"""
AutoHeal Phase 8: 3D Threat Topology REST API & Live SSE Telemetry
Provides endpoints for spatial graph rendering, entity forensics,
attack sequence extraction, and live node state streaming.
"""

import json
import asyncio
from typing import Optional, List
from fastapi import APIRouter, Query, Path, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from src.appsec.threat_topology_models import (
    get_topology_graph, get_topology_entity_details, get_attack_sequence
)

router = APIRouter(prefix="/api/threat-topology", tags=["Threat Topology"])


@router.get("/graph", summary="Retrieve 3D Threat Topology Graph Snapshot")
def fetch_topology_graph(
    time_range: str = Query("24h", pattern="^(1h|6h|24h|7d|all)$", description="Temporal scope"),
    severity: str = Query("ALL", pattern="^(ALL|CRITICAL|HIGH|MEDIUM|LOW)$", description="Severity filter"),
    incident_id: Optional[str] = Query(None, description="Optional incident ID focus"),
    limit: int = Query(150, ge=10, le=300, description="Max graph nodes")
):
    """
    Returns a spatial graph payload of nodes and edges grounded in real database records.
    Differentiates confirmed relationships from inferred heuristic correlations.
    """
    try:
        graph = get_topology_graph(
            time_range=time_range,
            severity=severity,
            incident_id=incident_id,
            limit=limit
        )
        return JSONResponse(status_code=200, content=graph)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to build topology graph: {str(e)}"})


@router.get("/entities/{entity_type}/{entity_id}", summary="Retrieve Detailed Entity Forensics")
def fetch_entity_details(
    entity_type: str = Path(..., description="Entity category, e.g. SOURCE_IP, INCIDENT, DETECTION_RULE"),
    entity_id: str = Path(..., description="Identifier of the entity")
):
    """Returns deep forensic details, event history, threat intel, and related records for a node."""
    try:
        details = get_topology_entity_details(entity_type.upper(), entity_id)
        return JSONResponse(status_code=200, content=details)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to retrieve entity details: {str(e)}"})


@router.get("/attack-sequence", summary="Retrieve Chronological Attack Sequence")
def fetch_attack_sequence(
    incident_id: Optional[str] = Query(None, description="Optional incident focus"),
    limit: int = Query(50, ge=5, le=100, description="Max sequence steps")
):
    """Returns a chronological trace linking events, rules, incidents, responses, and verification probes."""
    try:
        seq = get_attack_sequence(incident_id=incident_id, limit=limit)
        return JSONResponse(status_code=200, content={"total": len(seq), "total_steps": len(seq), "sequence": seq})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to generate attack sequence: {str(e)}"})


@router.get("/summary", summary="Retrieve Topology Metric Summary")
def fetch_topology_summary():
    """Returns aggregate summary counts for nodes, edges, quarantined IPs, and monitored services."""
    try:
        graph = get_topology_graph(limit=100)
        return JSONResponse(status_code=200, content=graph.get("summary", {}))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to retrieve topology summary: {str(e)}"})


@router.get("/stream", summary="Live Server-Sent Events (SSE) for 3D Topology Updates")
async def stream_topology_updates():
    """
    Streams periodic topology delta events (node state changes, pulse triggers, and new edges)
    without forcing the frontend to rebuild the entire WebGL scene.
    """
    async def event_generator():
        while True:
            try:
                # Emit heartbeat and lightweight summary pulse
                graph = get_topology_graph(time_range="1h", limit=40)
                payload = {
                    "event": "topology_update",
                    "timestamp": graph["timestamp"],
                    "summary": graph["summary"],
                    "active_incidents": [n for n in graph["nodes"] if n["entity_type"] == "INCIDENT"][:5]
                }
                yield f"data: {json.dumps(payload)}\n\n"
            except Exception:
                yield f"data: {json.dumps({'event': 'ping'})}\n\n"

            await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
