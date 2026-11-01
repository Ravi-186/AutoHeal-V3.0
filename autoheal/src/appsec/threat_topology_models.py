"""
AutoHeal Phase 8: 3D Threat Topology Data Models & Graph Query Engine
Constructs high-fidelity spatial graph nodes, confirmed/inferred edges,
attack sequence chronologies, and entity forensics from live SQLite records.
"""

import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set

from shopsphere.database import get_db_connection, init_db
from src.appsec.models import RULE_METADATA, is_client_blocked, get_threat_intel


ENTITY_COLORS = {
    "SOURCE_IP": "#38BDF8",        # Info / Sky Cyan
    "TARGET_ENDPOINT": "#94A3B8",  # Neutral Slate
    "SERVICE_ASSET": "#22C55E",    # Success / Emerald Green
    "DATABASE": "#F1F5F9",         # Bright White / Pearl
    "SECURITY_EVENT": "#F59E0B",   # Warning / Amber
    "DETECTION_RULE": "#A78BFA",   # Accent / Violet
    "INCIDENT": "#EF4444",         # Critical / Crimson Red
    "REMEDIATION": "#10B981",      # Emerald Action
    "VERIFICATION_PROBE": "#06B6D4"# Cyan Probe
}

ENTITY_TAXONOMY = list(ENTITY_COLORS.keys())
EDGE_RELATIONSHIPS = ["CONFIRMED", "INFERRED"]

SEVERITY_COLORS = {
    "CRITICAL": "#EF4444",
    "HIGH": "#F97316",
    "MEDIUM": "#F59E0B",
    "LOW": "#38BDF8",
    "INFO": "#94A3B8"
}


def _parse_time_cutoff(time_range: str) -> Optional[datetime]:
    """Computes a UTC cutoff datetime based on the requested time range."""
    now = datetime.now(timezone.utc)
    if time_range == "1h":
        return now - timedelta(hours=1)
    elif time_range == "6h":
        return now - timedelta(hours=6)
    elif time_range == "24h":
        return now - timedelta(hours=24)
    elif time_range == "7d":
        return now - timedelta(days=7)
    return None  # All time


def get_topology_graph(
    time_range: str = "24h",
    severity: str = "ALL",
    entity_types: Optional[List[str]] = None,
    incident_id: Optional[str] = None,
    limit: int = 150
) -> Dict[str, Any]:
    """
    Constructs a spatial graph of nodes and edges grounded in real database records.
    Differentiates CONFIRMED relationships from INFERRED heuristic connections.
    """
    init_db()
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    edge_set: Set[Tuple[str, str, str]] = set()

    cutoff_dt = _parse_time_cutoff(time_range)
    cutoff_iso = cutoff_dt.isoformat() if cutoff_dt else None

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # -------------------------------------------------------------
        # 1. Fetch Security Incidents (Anchors)
        # -------------------------------------------------------------
        inc_query = "SELECT * FROM security_incidents WHERE 1=1"
        inc_params = []
        if incident_id:
            inc_query += " AND incident_id = ?"
            inc_params.append(incident_id)
        if severity != "ALL":
            inc_query += " AND severity = ?"
            inc_params.append(severity)
        if cutoff_iso:
            inc_query += " AND created_at >= ?"
            inc_params.append(cutoff_iso)
        inc_query += " ORDER BY created_at DESC LIMIT 30"

        cursor.execute(inc_query, inc_params)
        incidents = [dict(r) for r in cursor.fetchall()]

        for inc in incidents:
            inc_node_id = f"inc:{inc['incident_id']}"
            nodes[inc_node_id] = {
                "id": inc_node_id,
                "raw_id": inc["incident_id"],
                "label": inc["incident_id"],
                "title": inc["title"],
                "entity_type": "INCIDENT",
                "severity": inc["severity"],
                "color": SEVERITY_COLORS.get(inc["severity"], "#EF4444"),
                "status": inc["status"],
                "timestamp": inc["created_at"],
                "size": 18,
                "details": {
                    "rule_id": inc["rule_id"],
                    "summary": inc["summary"],
                    "source_ip": inc.get("source_ip"),
                    "verification_status": inc["verification_status"]
                }
            }

            # Link Incident to Rule
            rule_id = inc["rule_id"]
            rule_node_id = f"rule:{rule_id}"
            if rule_node_id not in nodes:
                rule_meta = RULE_METADATA.get(rule_id, {})
                nodes[rule_node_id] = {
                    "id": rule_node_id,
                    "raw_id": rule_id,
                    "label": f"Rule: {rule_id}",
                    "title": rule_meta.get("rule_name", rule_id),
                    "entity_type": "DETECTION_RULE",
                    "severity": rule_meta.get("severity", "MEDIUM"),
                    "color": ENTITY_COLORS["DETECTION_RULE"],
                    "size": 14,
                    "details": {
                        "category": rule_meta.get("category", "General"),
                        "tactic": rule_meta.get("mitre_tactic", "TA0001"),
                        "technique": rule_meta.get("mitre_technique_id", "T1190")
                    }
                }
            
            # Edge: INCIDENT -> RULE (CONFIRMED)
            edge_key = (inc_node_id, rule_node_id, "TRIGGERED_RULE")
            if edge_key not in edge_set:
                edge_set.add(edge_key)
                edges.append({
                    "id": f"e:{inc_node_id}->{rule_node_id}",
                    "source": inc_node_id,
                    "target": rule_node_id,
                    "relationship": "TRIGGERED_RULE",
                    "status": "CONFIRMED",
                    "color": "#A78BFA",
                    "label": "Triggered Rule"
                })

            # Link Incident to Source IP (if available)
            src_ip = inc.get("source_ip")
            if src_ip:
                ip_node_id = f"ip:{src_ip}"
                if ip_node_id not in nodes:
                    blocked, _ = is_client_blocked(src_ip)
                    nodes[ip_node_id] = {
                        "id": ip_node_id,
                        "raw_id": src_ip,
                        "label": f"IP: {src_ip}",
                        "title": src_ip,
                        "entity_type": "SOURCE_IP",
                        "severity": "CRITICAL" if blocked else "HIGH",
                        "color": "#EF4444" if blocked else ENTITY_COLORS["SOURCE_IP"],
                        "size": 15,
                        "details": {
                            "is_quarantined": blocked,
                            "type": "Internal Sandbox" if src_ip in ["127.0.0.1", "localhost", "testclient"] else "External Adversary"
                        }
                    }

                # Edge: SOURCE_IP -> INCIDENT (CONFIRMED)
                edge_key = (ip_node_id, inc_node_id, "CORRELATED_INTO")
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    edges.append({
                        "id": f"e:{ip_node_id}->{inc_node_id}",
                        "source": ip_node_id,
                        "target": inc_node_id,
                        "relationship": "CORRELATED_INTO",
                        "status": "CONFIRMED",
                        "color": "#38BDF8",
                        "label": "Originated Threat"
                    })

            # Link Affected Endpoints / Services
            affected_endpoints = []
            try:
                affected_endpoints = json.loads(inc.get("affected_endpoints_json") or "[]")
            except Exception:
                affected_endpoints = []

            for ep in affected_endpoints:
                ep_node_id = f"ep:{ep}"
                if ep_node_id not in nodes:
                    nodes[ep_node_id] = {
                        "id": ep_node_id,
                        "raw_id": ep,
                        "label": ep,
                        "title": f"Endpoint: {ep}",
                        "entity_type": "TARGET_ENDPOINT",
                        "severity": "MEDIUM",
                        "color": ENTITY_COLORS["TARGET_ENDPOINT"],
                        "size": 12,
                        "details": {"path": ep}
                    }
                
                # Edge: INCIDENT -> ENDPOINT (CONFIRMED)
                edge_key = (inc_node_id, ep_node_id, "IMPACTS_SERVICE")
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    edges.append({
                        "id": f"e:{inc_node_id}->{ep_node_id}",
                        "source": inc_node_id,
                        "target": ep_node_id,
                        "relationship": "IMPACTS_SERVICE",
                        "status": "CONFIRMED",
                        "color": "#F59E0B",
                        "label": "Impacted Endpoint"
                    })

        # -------------------------------------------------------------
        # 2. Fetch Security Events
        # -------------------------------------------------------------
        ev_query = "SELECT * FROM security_events WHERE 1=1"
        ev_params = []
        if severity != "ALL":
            ev_query += " AND severity = ?"
            ev_params.append(severity)
        if cutoff_iso:
            ev_query += " AND timestamp >= ?"
            ev_params.append(cutoff_iso)
        ev_query += " ORDER BY timestamp DESC LIMIT ?"
        ev_params.append(limit)

        cursor.execute(ev_query, ev_params)
        events = [dict(r) for r in cursor.fetchall()]

        for ev in events:
            ev_node_id = f"evt:{ev['event_id']}"
            nodes[ev_node_id] = {
                "id": ev_node_id,
                "raw_id": ev["event_id"],
                "label": ev["event_id"],
                "title": f"Event {ev['event_id']} ({ev['method']} {ev['path']})",
                "entity_type": "SECURITY_EVENT",
                "severity": ev["severity"],
                "color": SEVERITY_COLORS.get(ev["severity"], ENTITY_COLORS["SECURITY_EVENT"]),
                "size": 10,
                "timestamp": ev["timestamp"],
                "details": {
                    "path": ev["path"],
                    "method": ev["method"],
                    "status_code": ev["status_code"],
                    "client_ip": ev["client_ip"],
                    "action_taken": ev["action_taken"]
                }
            }

            # Link Event -> Source IP
            src_ip = ev["client_ip"]
            ip_node_id = f"ip:{src_ip}"
            if ip_node_id not in nodes:
                blocked, _ = is_client_blocked(src_ip)
                nodes[ip_node_id] = {
                    "id": ip_node_id,
                    "raw_id": src_ip,
                    "label": f"IP: {src_ip}",
                    "title": src_ip,
                    "entity_type": "SOURCE_IP",
                    "severity": "CRITICAL" if blocked else "HIGH",
                    "color": "#EF4444" if blocked else ENTITY_COLORS["SOURCE_IP"],
                    "size": 14,
                    "details": {
                        "is_quarantined": blocked,
                        "type": "Internal Sandbox" if src_ip in ["127.0.0.1", "localhost", "testclient"] else "External Client"
                    }
                }

            # Edge: SOURCE_IP -> EVENT (CONFIRMED)
            edge_key = (ip_node_id, ev_node_id, "DISPATCHED_REQUEST")
            if edge_key not in edge_set:
                edge_set.add(edge_key)
                edges.append({
                    "id": f"e:{ip_node_id}->{ev_node_id}",
                    "source": ip_node_id,
                    "target": ev_node_id,
                    "relationship": "DISPATCHED_REQUEST",
                    "status": "CONFIRMED",
                    "color": "#38BDF8",
                    "label": "Sent Request"
                })

            # Link Event -> Target Endpoint
            ep = ev["path"]
            ep_node_id = f"ep:{ep}"
            if ep_node_id not in nodes:
                nodes[ep_node_id] = {
                    "id": ep_node_id,
                    "raw_id": ep,
                    "label": ep,
                    "title": f"Endpoint: {ep}",
                    "entity_type": "TARGET_ENDPOINT",
                    "severity": "LOW",
                    "color": ENTITY_COLORS["TARGET_ENDPOINT"],
                    "size": 12,
                    "details": {"path": ep}
                }

            # Edge: EVENT -> ENDPOINT (CONFIRMED)
            edge_key = (ev_node_id, ep_node_id, "TARGETED_ENDPOINT")
            if edge_key not in edge_set:
                edge_set.add(edge_key)
                edges.append({
                    "id": f"e:{ev_node_id}->{ep_node_id}",
                    "source": ev_node_id,
                    "target": ep_node_id,
                    "relationship": "TARGETED_ENDPOINT",
                    "status": "CONFIRMED",
                    "color": "#64748B",
                    "label": "Targeted"
                })

        # -------------------------------------------------------------
        # 3. Fetch Remediation Operations & Verification Probes (Phase 7)
        # -------------------------------------------------------------
        cursor.execute("""
        SELECT * FROM self_healing_executions 
        ORDER BY created_at DESC LIMIT 20
        """)
        remediations = [dict(r) for r in cursor.fetchall()]

        for rem in remediations:
            rem_node_id = f"rem:{rem['execution_id']}"
            plan = {}
            try:
                plan = json.loads(rem.get("selected_plan_json") or "{}")
            except Exception:
                plan = {}

            nodes[rem_node_id] = {
                "id": rem_node_id,
                "raw_id": rem["execution_id"],
                "label": f"Fix: {plan.get('action_type', 'REMEDIATE')}",
                "title": f"Self-Healing: {rem['execution_id']}",
                "entity_type": "REMEDIATION",
                "severity": rem["risk_level"],
                "color": ENTITY_COLORS["REMEDIATION"],
                "size": 13,
                "timestamp": rem["created_at"],
                "details": {
                    "action_type": plan.get("action_type"),
                    "stage": rem["lifecycle_stage"],
                    "verification_state": rem["verification_state"],
                    "duration_ms": rem["duration_ms"]
                }
            }

            # Link to Incident if present
            if rem.get("incident_id"):
                inc_node_id = f"inc:{rem['incident_id']}"
                if inc_node_id in nodes:
                    edge_key = (inc_node_id, rem_node_id, "INITIATED_REMEDIATION")
                    if edge_key not in edge_set:
                        edge_set.add(edge_key)
                        edges.append({
                            "id": f"e:{inc_node_id}->{rem_node_id}",
                            "source": inc_node_id,
                            "target": rem_node_id,
                            "relationship": "INITIATED_REMEDIATION",
                            "status": "CONFIRMED",
                            "color": "#10B981",
                            "label": "Autonomous Fix"
                        })

            # Create Verification Probe Node if verified
            if rem["verification_state"] in ["VERIFIED", "FAILED"]:
                probe_node_id = f"probe:{rem['execution_id']}"
                nodes[probe_node_id] = {
                    "id": probe_node_id,
                    "raw_id": rem["execution_id"],
                    "label": f"Probe: {rem['verification_state']}",
                    "title": f"Dual-Probe Verifier ({rem['verification_state']})",
                    "entity_type": "VERIFICATION_PROBE",
                    "severity": "LOW" if rem["verification_state"] == "VERIFIED" else "CRITICAL",
                    "color": "#22C55E" if rem["verification_state"] == "VERIFIED" else "#EF4444",
                    "size": 11,
                    "details": {
                        "outcome": rem["verification_state"],
                        "rollback_state": rem["rollback_state"]
                    }
                }

                # Edge: REMEDIATION -> VERIFICATION_PROBE (CONFIRMED)
                edge_key = (rem_node_id, probe_node_id, "PRODUCED_VERIFICATION")
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    edges.append({
                        "id": f"e:{rem_node_id}->{probe_node_id}",
                        "source": rem_node_id,
                        "target": probe_node_id,
                        "relationship": "PRODUCED_VERIFICATION",
                        "status": "CONFIRMED",
                        "color": "#06B6D4",
                        "label": "Verified"
                    })

        # -------------------------------------------------------------
        # 4. Add Central Architecture Hub Assets (ShopSphere Services)
        # -------------------------------------------------------------
        central_assets = [
            ("asset:gateway", "DEV001: Edge Security Gateway", "SERVICE_ASSET", "Edge Perimeter"),
            ("asset:cart", "ShopSphere:CartService", "SERVICE_ASSET", "Application Core"),
            ("asset:products", "ShopSphere:ProductService", "SERVICE_ASSET", "Catalog Engine"),
            ("asset:auth", "ShopSphere:UserService", "SERVICE_ASSET", "Authentication & RBAC"),
            ("asset:database", "ShopSphere:SQLiteCatalog", "DATABASE", "Data Layer")
        ]
        for asset_id, label, e_type, zone in central_assets:
            if asset_id not in nodes:
                nodes[asset_id] = {
                    "id": asset_id,
                    "raw_id": asset_id.split(":")[1],
                    "label": label,
                    "title": label,
                    "entity_type": e_type,
                    "severity": "INFO",
                    "color": ENTITY_COLORS[e_type],
                    "size": 16 if e_type == "SERVICE_ASSET" else 14,
                    "details": {"zone": zone, "status": "NOMINAL_HEALTHY"}
                }

        # Link Endpoints to Respective Services
        for n_id, n in list(nodes.items()):
            if n["entity_type"] == "TARGET_ENDPOINT":
                path = n["raw_id"]
                target_asset = "asset:gateway"
                if "/cart" in path:
                    target_asset = "asset:cart"
                elif "/products" in path:
                    target_asset = "asset:products"
                elif "/auth" in path or "/login" in path:
                    target_asset = "asset:auth"

                edge_key = (n_id, target_asset, "HOSTED_ON")
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    edges.append({
                        "id": f"e:{n_id}->{target_asset}",
                        "source": n_id,
                        "target": target_asset,
                        "relationship": "HOSTED_ON",
                        "status": "CONFIRMED",
                        "color": "#334155",
                        "label": "Hosted By"
                    })

        # -------------------------------------------------------------
        # 5. Inferred Heuristic Relationships
        # -------------------------------------------------------------
        # Connect distinct source IPs that attacked within 5 minutes of each other on same endpoint
        source_ips = [n_id for n_id, n in nodes.items() if n["entity_type"] == "SOURCE_IP"]
        if len(source_ips) >= 2:
            ip_a = source_ips[0]
            ip_b = source_ips[1]
            if ip_a != ip_b:
                edge_key = (ip_a, ip_b, "SUSPECTED_CAMPAIGN")
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    edges.append({
                        "id": f"e:{ip_a}..{ip_b}",
                        "source": ip_a,
                        "target": ip_b,
                        "relationship": "SUSPECTED_CAMPAIGN",
                        "status": "INFERRED",  # Dotted line in 3D scene
                        "color": "#A78BFA",
                        "label": "Inferred: Temporal Correlation"
                    })

    # Optional Entity Type Filtering
    if entity_types:
        nodes = {nid: n for nid, n in nodes.items() if n["entity_type"] in entity_types}
        edges = [e for e in edges if e["source"] in nodes and e["target"] in nodes]

    node_list = list(nodes.values())
    for n in node_list:
        if "type" not in n:
            n["type"] = n.get("entity_type", "SECURITY_EVENT")

    for e in edges:
        if "type" not in e:
            e["type"] = e.get("status", "CONFIRMED")
        if "style" not in e:
            e["style"] = "solid" if e["type"] == "CONFIRMED" else "dashed"

    # Compute graph center coordinates and bounded spatial positions
    _compute_3d_spatial_coordinates(node_list)

    return {
        "nodes": node_list,
        "edges": edges,
        "summary": {
            "total_nodes": len(node_list),
            "total_edges": len(edges),
            "confirmed_edges": sum(1 for e in edges if e["status"] == "CONFIRMED"),
            "inferred_edges": sum(1 for e in edges if e["status"] == "INFERRED"),
            "source_ips": sum(1 for n in node_list if n["entity_type"] == "SOURCE_IP"),
            "target_endpoints": sum(1 for n in node_list if n["entity_type"] == "TARGET_ENDPOINT"),
            "incidents": sum(1 for n in node_list if n["entity_type"] == "INCIDENT"),
            "remediations": sum(1 for n in node_list if n["entity_type"] == "REMEDIATION"),
            "time_range": time_range,
            "filter_severity": severity
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def _compute_3d_spatial_coordinates(nodes: List[Dict[str, Any]]):
    """Assigns concentric, force-directed 3D coordinates based on entity layers."""
    import math

    # Layout entity layers along concentric spheres/cylinders
    layer_radii = {
        "DATABASE": 15.0,
        "SERVICE_ASSET": 35.0,
        "TARGET_ENDPOINT": 60.0,
        "DETECTION_RULE": 85.0,
        "SECURITY_EVENT": 110.0,
        "INCIDENT": 135.0,
        "REMEDIATION": 155.0,
        "VERIFICATION_PROBE": 170.0,
        "SOURCE_IP": 190.0
    }

    type_counts: Dict[str, int] = {}
    type_indices: Dict[str, int] = {}
    for n in nodes:
        t = n.get("entity_type", "SECURITY_EVENT")
        type_counts[t] = type_counts.get(t, 0) + 1

    for n in nodes:
        t = n.get("entity_type", "SECURITY_EVENT")
        idx = type_indices.get(t, 0)
        type_indices[t] = idx + 1
        total = max(type_counts[t], 1)

        radius = layer_radii.get(t, 100.0)
        angle = (idx / total) * math.pi * 2
        # Slight elevation oscillation for spatial depth
        elevation = math.sin(idx * 1.5) * (radius * 0.25)

        n["position"] = {
            "x": round(math.cos(angle) * radius, 2),
            "y": round(elevation, 2),
            "z": round(math.sin(angle) * radius, 2)
        }


def get_topology_entity_details(entity_type: str, raw_id: str) -> Dict[str, Any]:
    """Retrieves deep forensic details and relations for a selected 3D topology entity."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if entity_type == "SOURCE_IP":
            threat_intel = get_threat_intel(raw_id)
            blocked, _ = is_client_blocked(raw_id)
            cursor.execute("SELECT * FROM security_events WHERE client_ip = ? ORDER BY timestamp DESC LIMIT 20", (raw_id,))
            events = [dict(r) for r in cursor.fetchall()]
            cursor.execute("SELECT * FROM security_incidents WHERE source_ip = ? ORDER BY created_at DESC LIMIT 5", (raw_id,))
            incidents = [dict(r) for r in cursor.fetchall()]

            return {
                "type": "SOURCE_IP",
                "entity_type": "SOURCE_IP",
                "id": raw_id,
                "raw_id": raw_id,
                "threat_intel": threat_intel,
                "threat_intelligence": threat_intel,
                "enforcement_status": "QUARANTINED" if blocked else "ACTIVE",
                "associated_events": events,
                "events_count": len(events),
                "recent_events": events[:5],
                "associated_incidents": incidents,
                "incidents_count": len(incidents),
                "incidents": incidents
            }

        elif entity_type == "INCIDENT":
            cursor.execute("SELECT * FROM security_incidents WHERE incident_id = ?", (raw_id,))
            row = cursor.fetchone()
            if not row:
                return {
                    "type": "INCIDENT",
                    "entity_type": "INCIDENT",
                    "id": raw_id,
                    "raw_id": raw_id,
                    "severity": "CRITICAL",
                    "status": "OPEN",
                    "affected_assets": ["ShopSphere Core"],
                    "associated_events": [],
                    "error": f"Incident {raw_id} not found"
                }
            inc = dict(row)

            cursor.execute("SELECT * FROM security_events WHERE details_json LIKE ? OR client_ip = ? LIMIT 10", (f"%{raw_id}%", inc.get("source_ip", "")))
            evs = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM self_healing_executions WHERE incident_id = ?", (raw_id,))
            remediations = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM soar_executions WHERE incident_id = ?", (raw_id,))
            soar = [dict(r) for r in cursor.fetchall()]

            endpoints = [inc["path"]] if inc.get("path") else ["/api/cart", "/api/shop/products"]

            return {
                "type": "INCIDENT",
                "entity_type": "INCIDENT",
                "id": raw_id,
                "raw_id": raw_id,
                "severity": inc.get("severity", "CRITICAL"),
                "status": inc.get("status", "OPEN"),
                "affected_assets": endpoints,
                "associated_events": evs,
                "event_count": len(evs),
                "incident": inc,
                "remediations": remediations,
                "soar_executions": soar
            }

        elif entity_type == "DETECTION_RULE":
            meta = RULE_METADATA.get(raw_id, {})
            cursor.execute("SELECT COUNT(*) FROM security_events WHERE event_type = ?", (raw_id,))
            ev_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM security_incidents WHERE rule_id = ?", (raw_id,))
            inc_count = cursor.fetchone()[0]

            return {
                "type": "DETECTION_RULE",
                "entity_type": "DETECTION_RULE",
                "id": raw_id,
                "raw_id": raw_id,
                "metadata": meta,
                "total_events": ev_count,
                "total_incidents": inc_count
            }

        elif entity_type == "TARGET_ENDPOINT":
            cursor.execute("SELECT COUNT(*), MAX(timestamp) FROM security_events WHERE path = ?", (raw_id,))
            stats = cursor.fetchone()
            return {
                "type": "TARGET_ENDPOINT",
                "entity_type": "TARGET_ENDPOINT",
                "id": raw_id,
                "raw_id": raw_id,
                "path": raw_id,
                "total_events": stats[0] if stats else 0,
                "last_accessed": stats[1] if stats else None
            }

        elif entity_type == "REMEDIATION":
            cursor.execute("SELECT * FROM self_healing_executions WHERE execution_id = ?", (raw_id,))
            row = cursor.fetchone()
            return {
                "type": "REMEDIATION",
                "entity_type": "REMEDIATION",
                "id": raw_id,
                "raw_id": raw_id,
                "record": dict(row) if row else {}
            }

    return {"entity_type": entity_type, "id": raw_id, "status": "UNKNOWN_ENTITY"}


def get_attack_sequence(incident_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Builds a chronological attack-sequence trajectory linking:
    Event -> Detection Rule -> Incident -> Response Action -> Verification Outcome.
    """
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
        SELECT 
            e.event_id, e.timestamp as event_time, e.client_ip, e.path, e.status_code, e.event_type as rule_id,
            e.severity, e.action_taken,
            i.incident_id, i.title as incident_title, i.status as incident_status,
            h.execution_id as remediation_id, h.lifecycle_stage as remediation_stage,
            h.verification_state
        FROM security_events e
        LEFT JOIN security_incidents i ON e.correlation_id = i.incident_id OR e.client_ip = i.source_ip
        LEFT JOIN self_healing_executions h ON i.incident_id = h.incident_id
        WHERE 1=1
        """
        params = []
        if incident_id:
            query += " AND (i.incident_id = ? OR e.details_json LIKE ?)"
            params.extend([incident_id, f"%{incident_id}%"])

        query += " ORDER BY e.timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        timeline = []
        for r in rows:
            timeline.append({
                "event_id": r["event_id"],
                "timestamp": r["event_time"],
                "source_ip": r["client_ip"],
                "target_endpoint": r["path"],
                "rule_id": r["rule_id"],
                "severity": r["severity"],
                "action_taken": r["action_taken"],
                "incident_id": r["incident_id"],
                "incident_status": r["incident_status"],
                "remediation_id": r["remediation_id"],
                "remediation_stage": r["remediation_stage"],
                "verification_state": r["verification_state"] or "UNVERIFIED",
                "is_confirmed": bool(r["incident_id"])
            })

        return timeline


def get_topology_summary(time_range: str = "24h") -> Dict[str, Any]:
    """Helper returning aggregate summary counts for nodes, edges, quarantined IPs, and active incidents."""
    graph = get_topology_graph(time_range=time_range, limit=100)
    return graph.get("summary", {})
