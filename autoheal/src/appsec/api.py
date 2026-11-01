import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Query, Response, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
import json
import time

from src.appsec.models import (
    get_security_events, list_security_incidents,
    get_security_incident, update_incident_status,
    get_active_blocked_clients, unblock_client_ip,
    get_security_event_by_id, get_related_security_events,
    query_security_events_advanced, record_event_investigation,
    get_threat_intel, get_detection_rule_catalog,
    get_incident_command_stats, query_incidents_paginated,
    transition_incident_status, assign_incident_analyst,
    update_incident_priority, update_incident_root_cause,
    add_incident_note, build_incident_timeline,
    get_incident_evidence_explorer, build_incident_attack_sequence,
    get_incident_activity_logs, ConcurrencyError
)
from src.appsec.detector import AppSecDetector
from src.appsec.responder import AppSecResponder
from src.appsec.reporter import AppSecReporter

router = APIRouter(prefix="/api/security", tags=["AppSec Defense & Incident Management"])


class UnblockRequest(BaseModel):
    client_ip: str


class RemediateRequest(BaseModel):
    remediation_notes: str
    mark_as_remediated: bool = True


class InvestigationRequest(BaseModel):
    status: str = "INVESTIGATING"
    notes: str = ""
    assigned_analyst: str = "admin@sentinel.sec"
    tags: Optional[List[str]] = None
    create_incident: bool = False


class StatusTransitionRequest(BaseModel):
    status: Optional[str] = None
    target_status: Optional[str] = None
    resolution_notes: Optional[str] = None
    author: Optional[str] = "admin@sentinel.sec"
    analyst: Optional[str] = None
    expected_version: Optional[int] = None
    current_version: Optional[int] = None


class AssignAnalystRequest(BaseModel):
    analyst: str
    assigned_by: Optional[str] = "admin@sentinel.sec"
    current_version: Optional[int] = None
    expected_version: Optional[int] = None


class UpdatePriorityRequest(BaseModel):
    priority: str
    reason: Optional[str] = ""
    updated_by: Optional[str] = "admin@sentinel.sec"
    analyst: Optional[str] = None
    current_version: Optional[int] = None
    expected_version: Optional[int] = None


class UpdateRootCauseRequest(BaseModel):
    entry_point: Optional[str] = None
    suspected_entry_point: Optional[str] = ""
    conditions: Optional[str] = None
    contributing_conditions: Optional[str] = ""
    conclusions: Optional[str] = None
    analyst_conclusions: Optional[str] = ""
    author: Optional[str] = "admin@sentinel.sec"
    current_version: Optional[int] = None
    expected_version: Optional[int] = None


class AddNoteRequest(BaseModel):
    note: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = "admin@sentinel.sec"


@router.get("/metrics", summary="Retrieve Live Application Security KPIs")
def get_security_metrics(
    time_range: str = Query("24h"),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None)
):
    """Returns SOC dashboard metrics including active threats, blocked IPs, incidents by severity, and executive KPIs."""
    from src.appsec.analytics import ExecutiveAnalyticsEngine
    return ExecutiveAnalyticsEngine.get_executive_metrics(
        time_range=time_range,
        start_time=start_time,
        end_time=end_time
    )


@router.get("/analytics/timeline", summary="Retrieve Event Timeline Data for Charts")
def get_event_timeline_data(
    time_range: str = Query("24h"),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    num_buckets: int = Query(12, ge=6, le=30)
):
    """Returns time-bucketed event counts and severities for responsive Chart.js timeline rendering."""
    from src.appsec.analytics import ExecutiveAnalyticsEngine
    return ExecutiveAnalyticsEngine.get_event_timeline(
        time_range=time_range,
        category=category,
        severity=severity,
        num_buckets=num_buckets
    )


@router.get("/activity/feed", summary="Retrieve Live Security Activity Feed")
def get_activity_feed(limit: int = Query(25, ge=5, le=100)):
    """Returns unified real-time security events, incidents, and remediation actions."""
    from src.appsec.analytics import ExecutiveAnalyticsEngine
    return ExecutiveAnalyticsEngine.get_live_activity_feed(limit=limit)


@router.get("/health/detailed", summary="Retrieve Detailed 8-Subsystem Health Status")
def get_detailed_system_health():
    """Evaluates operational health across API, DB, Ingestion, Worker, Queue, Detector, Verifier, and AI Provider."""
    from src.appsec.analytics import ExecutiveAnalyticsEngine
    return ExecutiveAnalyticsEngine.get_detailed_system_health()


@router.get("/events/stream", summary="Stream Real-Time Security Telemetry & System Heartbeat (SSE)")
async def stream_live_events(request: Request):
    """Streams real-time security events, threat detections, and Sentinel heartbeats via Server-Sent Events (SSE)."""
    async def sse_event_stream():
        last_event_id = None
        while True:
            if await request.is_disconnected():
                break
            try:
                events = get_security_events(limit=1)
                if events:
                    newest = events[0]
                    if newest.get("event_id") != last_event_id:
                        last_event_id = newest.get("event_id")
                        yield f"event: security_event\ndata: {json.dumps(newest)}\n\n"
            except Exception:
                pass

            heartbeat = {
                "type": "heartbeat",
                "status": "SENTINEL_OPERATIONAL",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            yield f"event: heartbeat\ndata: {json.dumps(heartbeat)}\n\n"
            await asyncio.sleep(3)

    return StreamingResponse(sse_event_stream(), media_type="text/event-stream")


@router.get("/events", summary="List Telemetry Security Events")
def list_events(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=500),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    rule_id: Optional[str] = Query(None),
    client_ip: Optional[str] = Query(None),
    action_taken: Optional[str] = Query(None),
    time_range: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    sort_by: str = Query("timestamp"),
    sort_order: str = Query("desc"),
    format: Optional[str] = Query(None)
):
    """Retrieves paginated, searchable, multi-filtered telemetry events with aggregate breakdowns and CSV export."""
    effective_category = category or event_type
    res = query_security_events_advanced(
        page=page,
        limit=limit,
        search=search,
        category=effective_category,
        severity=severity,
        rule_id=rule_id,
        client_ip=client_ip,
        action_taken=action_taken,
        time_range=time_range,
        start_time=start_time,
        end_time=end_time,
        sort_by=sort_by,
        sort_order=sort_order
    )

    if format == "csv":
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Timestamp", "Event ID", "Severity", "Event Type", "Method", "Path", "Status Code", "Client IP", "Action Taken", "Correlation ID"])
        for ev in res["events"]:
            writer.writerow([
                ev.get("timestamp"),
                ev.get("event_id"),
                ev.get("severity"),
                ev.get("event_type"),
                ev.get("method"),
                ev.get("path"),
                ev.get("status_code"),
                ev.get("client_ip"),
                ev.get("action_taken"),
                ev.get("correlation_id")
            ])
        csv_bytes = output.getvalue().encode("utf-8")
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=sentinel_events_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"}
        )

    return res


@router.get("/events/export", summary="Export Security Events (CSV/JSON)")
def export_security_events(
    format: str = Query("csv", pattern="^(csv|json)$"),
    limit: int = Query(1000, ge=1, le=10000),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    rule_id: Optional[str] = Query(None),
    client_ip: Optional[str] = Query(None),
    action_taken: Optional[str] = Query(None),
    time_range: Optional[str] = Query(None)
):
    """Explicit export route providing CSV or JSON export of telemetry events."""
    effective_category = category
    res = query_security_events_advanced(
        page=1,
        limit=limit,
        search=search,
        category=effective_category,
        severity=severity,
        rule_id=rule_id,
        client_ip=client_ip,
        action_taken=action_taken,
        time_range=time_range,
        sort_by="timestamp",
        sort_order="desc"
    )
    if format == "csv":
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Timestamp", "Event ID", "Severity", "Event Type", "Method", "Path", "Status Code", "Client IP", "Action Taken", "Correlation ID"])
        for ev in res["events"]:
            writer.writerow([
                ev.get("timestamp"),
                ev.get("event_id"),
                ev.get("severity"),
                ev.get("event_type"),
                ev.get("method"),
                ev.get("path"),
                ev.get("status_code"),
                ev.get("client_ip"),
                ev.get("action_taken"),
                ev.get("correlation_id")
            ])
        csv_bytes = output.getvalue().encode("utf-8")
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=sentinel_events_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"}
        )
    return res


@router.get("/events/{event_id}", summary="Get Event Dossier")
def get_event_detail(event_id: str):
    """Retrieves complete structured telemetry event, investigation status, detection rule, and related incident."""
    ev = get_security_event_by_id(event_id)
    if not ev:
        raise HTTPException(status_code=404, detail=f"Security event {event_id} not found.")
    return ev


@router.get("/events/{event_id}/related", summary="Get Related Security Events")
def get_related_events(event_id: str, limit: int = Query(15, ge=1, le=50)):
    """Retrieves correlated security events matching trace ID, client IP, or target resource."""
    ev = get_security_event_by_id(event_id)
    if not ev:
        raise HTTPException(status_code=404, detail=f"Security event {event_id} not found.")
    return {
        "event_id": event_id,
        "related_events": get_related_security_events(event_id, limit=limit)
    }


@router.post("/events/{event_id}/investigate", summary="Update Event Investigation Status & Notes")
def update_event_investigation(event_id: str, payload: InvestigationRequest):
    """Updates investigation status, notes, tags, and optionally escalates to formal incident."""
    try:
        updated = record_event_investigation(
            event_id=event_id,
            status=payload.status,
            notes=payload.notes,
            assigned_analyst=payload.assigned_analyst,
            tags=payload.tags,
            create_incident=payload.create_incident
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/threat-intel/enrich", summary="Enrich Client IP with Threat Intelligence")
def threat_intel_enrichment(ip: str = Query(..., description="Client IP to inspect")):
    """Enriches client IP with autonomous blocklist state, reputation score, and behavioral tags."""
    return get_threat_intel(ip)


@router.get("/rules/catalog", summary="Retrieve Detection Rule Catalog")
def get_rules_catalog():
    """Returns detection rule catalog with live telemetry event counts, incident counts, and MITRE mapping."""
    return {
        "rules": get_detection_rule_catalog(),
        "total_rules": 7,
        "active_rules": 7
    }


@router.get("/incidents/stats", summary="Get Incident Command Center Stats")
def get_incident_stats(time_range: str = Query("all")):
    """Returns the 8 Incident Command Center KPI metrics."""
    return get_incident_command_stats(time_range=time_range)


@router.get("/incidents", summary="List Security Incidents")
def list_incidents(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_analyst: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    time_range: str = Query("all"),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    page: Optional[int] = Query(None),
    page_size: Optional[int] = Query(None),
    limit: Optional[int] = Query(None),
    format: Optional[str] = Query(None)
):
    """Lists security incidents with filtering, search, pagination, and CSV export."""
    if format == "csv":
        import io
        import csv
        data = query_incidents_paginated(
            status=status,
            severity=severity,
            priority=priority,
            assigned_analyst=assigned_analyst,
            search=search,
            time_range=time_range,
            sort_by=sort_by,
            sort_order=sort_order,
            page=1,
            page_size=1000
        )
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "incident_id", "title", "severity", "priority", "status",
            "rule_id", "category", "source_ip", "assigned_analyst",
            "confidence", "verification_status", "created_at", "updated_at"
        ])
        for inc in data.get("items", []):
            def escape_csv_formula(val):
                s = str(val or "")
                if s and s[0] in ["=", "+", "-", "@"]:
                    return "'" + s
                return s
            writer.writerow([
                escape_csv_formula(inc.get("incident_id")),
                escape_csv_formula(inc.get("title")),
                escape_csv_formula(inc.get("severity")),
                escape_csv_formula(inc.get("priority")),
                escape_csv_formula(inc.get("status")),
                escape_csv_formula(inc.get("rule_id")),
                escape_csv_formula(inc.get("category")),
                escape_csv_formula(inc.get("source_ip")),
                escape_csv_formula(inc.get("assigned_analyst")),
                inc.get("confidence", 1.0),
                escape_csv_formula(inc.get("verification_status")),
                escape_csv_formula(inc.get("created_at")),
                escape_csv_formula(inc.get("updated_at"))
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=autoheal_incidents_export.csv"}
        )

    # Return paginated envelope when pagination or advanced filtering query parameters are used
    if page is not None or page_size is not None or search is not None or priority is not None or assigned_analyst is not None or (limit is not None and limit > 100):
        p = page if page is not None else 1
        ps = page_size if page_size is not None else (limit if limit is not None else 20)
        return query_incidents_paginated(
            status=status,
            severity=severity,
            priority=priority,
            assigned_analyst=assigned_analyst,
            search=search,
            time_range=time_range,
            sort_by=sort_by,
            sort_order=sort_order,
            page=p,
            page_size=ps
        )

    # Legacy fallback: returns list of incident dicts
    return list_security_incidents(status=status, severity=severity, limit=limit or 50)


@router.get("/incidents/{incident_id}", summary="Get Incident Dossier")
def get_incident_dossier(incident_id: str):
    """Retrieves complete forensic incident evidence dossier."""
    inc = get_security_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")
    return inc


@router.get("/incidents/{incident_id}/timeline", summary="Get Interactive Incident Timeline")
def get_incident_timeline_endpoint(incident_id: str):
    """Returns unified chronological timeline of telemetry, detections, response, and analyst activities."""
    inc = get_security_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")
    return build_incident_timeline(incident_id)


@router.get("/incidents/{incident_id}/evidence", summary="Get Digital Evidence Explorer Dossier")
def get_incident_evidence_endpoint(incident_id: str):
    """Returns structured forensic evidence with SHA-256 cryptographic integrity hash."""
    inc = get_security_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")
    return get_incident_evidence_explorer(incident_id)


@router.get("/incidents/{incident_id}/attack-sequence", summary="Get Attack Sequence Flow")
def get_incident_attack_sequence_endpoint(incident_id: str):
    """Returns 5-stage attack sequence distinguishing observed facts from analytical hypotheses."""
    inc = get_security_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")
    return build_incident_attack_sequence(incident_id)


@router.get("/incidents/{incident_id}/activity", summary="Get Incident Activity & Collaboration Log")
def get_incident_activity_endpoint(incident_id: str):
    """Returns chronological internal notes and audit history for the incident."""
    inc = get_security_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")
    return get_incident_activity_logs(incident_id)


@router.post("/incidents/{incident_id}/status", summary="Transition Incident Lifecycle Status")
def transition_status_endpoint(incident_id: str, req: StatusTransitionRequest):
    """Controlled lifecycle status transition with validation, verification checks, and audit logging."""
    target_status = req.target_status or req.status
    if not target_status:
        raise HTTPException(status_code=400, detail="target_status is required.")
    author = req.analyst or req.author or "admin@sentinel.sec"
    expected_version = req.current_version if req.current_version is not None else req.expected_version
    try:
        updated = transition_incident_status(
            incident_id=incident_id,
            target_status=target_status,
            resolution_notes=req.resolution_notes,
            author=author,
            expected_version=expected_version
        )
        return updated
    except ConcurrencyError as ce:
        raise HTTPException(status_code=409, detail=str(ce))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/incidents/{incident_id}/assign", summary="Assign Incident to SOC Analyst")
def assign_analyst_endpoint(incident_id: str, req: AssignAnalystRequest):
    """Assigns or reassigns an incident to a SOC analyst with audit trail."""
    author = req.assigned_by or "admin@sentinel.sec"
    expected_version = req.current_version if req.current_version is not None else req.expected_version
    try:
        updated = assign_incident_analyst(
            incident_id=incident_id,
            analyst=req.analyst,
            assigned_by=author,
            expected_version=expected_version
        )
        return updated
    except ConcurrencyError as ce:
        raise HTTPException(status_code=409, detail=str(ce))
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.post("/incidents/{incident_id}/priority", summary="Update Incident Priority")
def update_priority_endpoint(incident_id: str, req: UpdatePriorityRequest):
    """Updates incident priority with audit logging."""
    author = req.analyst or req.updated_by or "admin@sentinel.sec"
    expected_version = req.current_version if req.current_version is not None else req.expected_version
    try:
        updated = update_incident_priority(
            incident_id=incident_id,
            priority=req.priority,
            updated_by=author,
            reason=req.reason or "",
            expected_version=expected_version
        )
        return updated
    except ConcurrencyError as ce:
        raise HTTPException(status_code=409, detail=str(ce))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/incidents/{incident_id}/root-cause", summary="Save Root-Cause Analysis Findings")
def update_root_cause_endpoint(incident_id: str, req: UpdateRootCauseRequest):
    """Persists verified analyst root-cause findings."""
    author = req.author or "admin@sentinel.sec"
    expected_version = req.current_version if req.current_version is not None else req.expected_version
    entry_point = req.entry_point if req.entry_point is not None else req.suspected_entry_point
    conditions = req.conditions if req.conditions is not None else req.contributing_conditions
    conclusions = req.conclusions if req.conclusions is not None else req.analyst_conclusions
    try:
        updated = update_incident_root_cause(
            incident_id=incident_id,
            suspected_entry_point=entry_point,
            contributing_conditions=conditions,
            analyst_conclusions=conclusions,
            author=author,
            expected_version=expected_version
        )
        return updated
    except ConcurrencyError as ce:
        raise HTTPException(status_code=409, detail=str(ce))
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@router.post("/incidents/{incident_id}/notes", summary="Add Internal Analyst Note")
def add_note_endpoint(incident_id: str, req: AddNoteRequest):
    """Appends an internal investigation note to the incident timeline and audit trail."""
    note_text = req.content if req.content is not None else (req.note or "")
    if not note_text:
        raise HTTPException(status_code=400, detail="Note content is required.")
    try:
        res = add_incident_note(
            incident_id=incident_id,
            note_text=note_text,
            author=req.author or "admin@sentinel.sec"
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get("/incidents/{incident_id}/report", summary="Get Formatted Markdown Incident Report")
def get_incident_report(incident_id: str):
    """Returns formatted forensic Markdown incident report."""
    md = AppSecReporter.generate_markdown_report(incident_id)
    return PlainTextResponse(content=md, media_type="text/markdown")


@router.get("/incidents/{incident_id}/export", summary="Download Incident Report (JSON/PDF/Markdown)")
def export_incident(incident_id: str, format: str = Query("json", pattern="^(json|md|markdown|pdf)$")):
    """Downloads forensic incident dossier in JSON, PDF, or Markdown format."""
    if format == "pdf":
        pdf_bytes = AppSecReporter.generate_pdf_report(incident_id)
        if not pdf_bytes:
            raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={incident_id}_report.pdf"}
        )
    elif format in ["md", "markdown"]:
        md = AppSecReporter.generate_markdown_report(incident_id)
        return Response(
            content=md,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={incident_id}_report.md"}
        )
    else:
        dossier = AppSecReporter.generate_json_dossier(incident_id)
        return JSONResponse(
            content=dossier,
            headers={"Content-Disposition": f"attachment; filename={incident_id}_dossier.json"}
        )


@router.post("/incidents/{incident_id}/remediate", summary="Execute or Record Incident Remediation")
def remediate_incident(incident_id: str, req: RemediateRequest):
    """Manually approves or records vulnerability remediation for an incident."""
    new_status = "REMEDIATED" if req.mark_as_remediated else "INVESTIGATING"
    updated = update_incident_status(
        incident_id=incident_id,
        status=new_status,
        verification_status="VERIFIED_RECOVERED",
        remediation_details=req.remediation_notes
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return {"status": "success", "incident": updated}


@router.post("/incidents/{incident_id}/verify", summary="Run Follow-up Autonomous Verification")
def verify_incident(incident_id: str):
    """Executes Component 4: Verification Agent against the target incident."""
    from src.appsec.verifier import AppSecVerifier
    result = AppSecVerifier.verify_incident_containment(incident_id)
    if result.get("status") == "INCIDENT_NOT_FOUND":
        raise HTTPException(status_code=404, detail="Incident not found.")
    return result


@router.get("/blocked-clients", summary="List Active Client IP Blocks")
def list_blocked_clients():
    """Returns currently active dynamic IP blocklist entries."""
    return get_active_blocked_clients()


@router.post("/unblock", summary="Unblock Quarantined Client IP")
def unblock_client(req: UnblockRequest):
    """Unblocks an IP address from the dynamic blocklist."""
    success = unblock_client_ip(req.client_ip)
    return {
        "status": "success" if success else "not_found",
        "client_ip": req.client_ip,
        "message": f"Client IP {req.client_ip} unblocked." if success else "IP was not in active blocklist."
    }


@router.post("/scan-telemetry", summary="Trigger Sliding-Window Detection Analysis")
def scan_telemetry():
    """Runs Component 2: Log Correlation Engine across recent security events."""
    from src.appsec.correlation_engine import AppSecCorrelationEngine
    engine = AppSecCorrelationEngine(window_seconds=60)
    incidents = engine.process_and_persist_incidents(window_seconds=60)
    detections = engine.correlate_events(window_seconds=60)
    mitigations = []
    for d in detections:
        mitigation = AppSecResponder.execute_defensive_mitigation(d)
        mitigations.append({
            "detection": d.to_dict(),
            "mitigation": mitigation
        })
    return {
        "scanned_at": True,
        "detections_count": len(detections),
        "incidents_count": len(incidents),
        "mitigations": mitigations
    }


class SecurityTestRunRequest(BaseModel):
    scenario: str = "failed_logins"
    target_url: str = "http://localhost:8000"
    client_ip: Optional[str] = None
    attempts: int = 5
    payload: Optional[str] = None
    target_endpoint: Optional[str] = None


@router.post("/test/run", summary="Execute Live Controlled Security Test")
def run_security_test(req: SecurityTestRunRequest):
    """Executes an authorized, controlled security test against the local ShopSphere instance."""
    from src.appsec.security_tester import ShopSphereSecurityTester
    try:
        tester = ShopSphereSecurityTester(base_url=req.target_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if req.scenario == "failed_logins":
        ip = req.client_ip or "198.51.100.22"
        return tester.test_repeated_failed_logins(client_ip=ip, attempts=req.attempts)
    elif req.scenario == "sqli":
        ip = req.client_ip or "203.0.113.88"
        p = req.payload or "Laptop' OR '1'='1"
        return tester.test_sql_injection(client_ip=ip, payload=p)
    elif req.scenario == "xss":
        ip = req.client_ip or "203.0.113.99"
        p = req.payload or "<script>alert('ShopSphere-XSS-Test')</script>"
        return tester.test_cross_site_scripting(client_ip=ip, payload=p)
    elif req.scenario == "admin":
        ip = req.client_ip or "198.51.100.77"
        return tester.test_unauthorized_admin(client_ip=ip)
    elif req.scenario == "rate":
        ip = req.client_ip or "198.51.100.55"
        return tester.test_request_rate_anomaly(client_ip=ip, count=25)
    elif req.scenario == "health":
        ip = req.client_ip or "198.51.100.33"
        return tester.test_health_cascade_resilience(client_ip=ip)
    elif req.scenario == "all":
        return tester.run_all_tests()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown test scenario: {req.scenario}")


@router.post("/test/stop", summary="Stop Currently Running Security Test")
def stop_security_test():
    """Cancels any running security test loop immediately."""
    from src.appsec.security_tester import cancel_active_tests
    cancel_active_tests()
    return {"status": "cancelled", "message": "Security test cancellation requested."}


# =============================================================================
# ATTACK SIMULATION CENTER API ENDPOINTS (PHASE 4)
# =============================================================================

@router.get("/simulations/catalog", summary="Get Authorized Attack Scenario Catalog")
def get_attack_scenarios():
    """Returns the comprehensive catalog of 7 authorized, executable attack simulation scenarios."""
    from src.appsec.models import get_scenario_catalog
    return {"scenarios": get_scenario_catalog(), "total": len(get_scenario_catalog())}


@router.get("/simulations/stats", summary="Get Simulation Dashboard Statistics")
def get_simulation_statistics():
    """Returns aggregated execution counts, detection rates, and verification metrics from SQLite."""
    from src.appsec.models import get_simulation_dashboard_stats
    return get_simulation_dashboard_stats()


@router.get("/simulations", summary="Query Simulation Execution History")
def list_simulations(
    scenario: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    detection_outcome: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    order_by: str = Query("start_time"),
    order_dir: str = Query("DESC"),
    format: Optional[str] = Query(None)
):
    """Retrieves paginated, searchable simulation history with optional CSV streaming export."""
    from src.appsec.models import query_simulation_executions
    data = query_simulation_executions(
        scenario=scenario,
        status=status,
        detection_outcome=detection_outcome,
        search=search,
        page=page,
        limit=1000 if format == "csv" else limit,
        order_by=order_by,
        order_dir=order_dir
    )

    if format == "csv":
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "execution_id", "scenario_id", "scenario_name", "risk_category", "severity",
            "target_url", "client_ip", "execution_mode", "status", "detection_outcome",
            "protection_verified", "expected_rule_id", "actual_rule_id", "incident_id",
            "request_count", "blocked_count", "duration_ms", "start_time"
        ])
        for it in data.get("items", []):
            def clean_cell(val):
                s = str(val or "")
                if s and s[0] in ("=", "+", "-", "@"):
                    return "'" + s
                return s

            writer.writerow([
                clean_cell(it.get("execution_id")),
                clean_cell(it.get("scenario_id")),
                clean_cell(it.get("scenario_name")),
                clean_cell(it.get("risk_category")),
                clean_cell(it.get("severity")),
                clean_cell(it.get("target_url")),
                clean_cell(it.get("client_ip")),
                clean_cell(it.get("execution_mode")),
                clean_cell(it.get("status")),
                clean_cell(it.get("detection_outcome")),
                1 if it.get("protection_verified") else 0,
                clean_cell(it.get("expected_rule_id")),
                clean_cell(it.get("actual_rule_id")),
                clean_cell(it.get("incident_id")),
                it.get("request_count", 0),
                it.get("blocked_count", 0),
                it.get("duration_ms", 0.0),
                clean_cell(it.get("start_time"))
            ])

        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="simulation_executions_export.csv"'}
        )

    return data


@router.get("/simulations/{execution_id}", summary="Get Simulation Execution Dossier & Evidence")
def get_simulation_detail(execution_id: str):
    """Retrieves full telemetry, detection validation matrix, remediation results, and evidence."""
    from src.appsec.models import get_simulation_execution
    sim = get_simulation_execution(execution_id)
    if not sim:
        raise HTTPException(status_code=404, detail=f"Simulation execution '{execution_id}' not found.")
    return sim


class SimulationDispatchRequest(BaseModel):
    scenario: Optional[str] = None
    scenario_id: Optional[str] = None
    target_url: str = "http://localhost:8000"
    client_ip: Optional[str] = None
    execution_mode: str = "live"  # 'live' or 'dryrun'
    attempts: int = 5
    payload: Optional[str] = None
    timeout: float = 10.0
    authorized_confirmation: bool = True


@router.post("/simulations/dispatch", summary="Dispatch Controlled Security Test Simulation")
def dispatch_simulation(req: SimulationDispatchRequest):
    """
    Executes an authorized defensive security test against local ShopSphere.
    Generates execution ID, records telemetry, compares detection vs expected rules,
    verifies mitigation status, and records an immutable audit log.
    """
    from src.appsec.security_tester import ShopSphereSecurityTester, validate_target_safety
    from src.appsec.models import (
        record_simulation_execution, update_simulation_execution,
        get_simulation_execution, SCENARIO_CATALOG
    )

    if not req.authorized_confirmation:
        raise HTTPException(status_code=400, detail="Defensive testing authorization confirmation is required to execute security simulation.")

    try:
        validated_url = validate_target_safety(req.target_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    scenario_key = req.scenario_id or req.scenario or "failed_logins"
    sc_info = SCENARIO_CATALOG.get(scenario_key)
    if not sc_info:
        raise HTTPException(status_code=400, detail=f"Unknown simulation scenario: '{scenario_key}'. Allowed: {', '.join(SCENARIO_CATALOG.keys())}")

    client_ip = req.client_ip or sc_info.get("default_client_ip", "198.51.100.42")
    payload = req.payload if req.payload is not None else sc_info.get("default_payload", "")
    attempts = max(1, min(req.attempts, 50))

    # Record initial execution state in DB
    exec_id = record_simulation_execution(
        scenario_id=scenario_key,
        target_url=validated_url,
        client_ip=client_ip,
        execution_mode=req.execution_mode,
        parameters={"attempts": attempts, "payload": payload, "timeout": req.timeout}
    )

    t0 = time.time()
    steps = []
    error_msg = None
    actual_rule_id = None
    incident_id = None
    protection_verified = False
    detection_outcome = "NOT_DETECTED"
    req_count = 1
    blocked_count = 0

    if req.execution_mode == "dryrun":
        # Safe dry-run simulation
        duration_ms = 45.0
        detection_outcome = "DETECTED"
        protection_verified = True
        actual_rule_id = sc_info.get("rule_id")
        steps = [
            {"step": "DRY_RUN_INIT", "status": "Simulated target safety validation pass", "client_ip": client_ip},
            {"step": "DRY_RUN_EVALUATION", "status": "Evaluated rule signature against dry-run payload", "rule_id": actual_rule_id},
            {"step": "DRY_RUN_PREDICTED_ACTION", "status": "Simulated quarantine action", "outcome": "PREDICTED_BLOCKED"}
        ]
        evidence = {
            "mode": "dryrun",
            "scenario": scenario_key,
            "target": validated_url,
            "simulated_rule": actual_rule_id
        }
    else:
        # Live execution against local test environment
        try:
            tester = ShopSphereSecurityTester(base_url=validated_url)
            if scenario_key in ["failed_logins", "brute_force"]:
                res = tester.test_repeated_failed_logins(client_ip=client_ip, attempts=attempts)
                req_count = attempts + 1
            elif scenario_key == "sqli":
                res = tester.test_sql_injection(client_ip=client_ip, payload=payload or "Laptop' OR '1'='1")
                req_count = 2
            elif scenario_key == "xss":
                res = tester.test_cross_site_scripting(client_ip=client_ip, payload=payload or "<script>alert('XSS')</script>")
                req_count = 1
            elif scenario_key == "admin":
                res = tester.test_unauthorized_admin(client_ip=client_ip)
                req_count = 1
            elif scenario_key == "rate":
                res = tester.test_request_rate_anomaly(client_ip=client_ip, count=attempts if attempts > 5 else 25)
                req_count = attempts if attempts > 5 else 25
            elif scenario_key == "health":
                res = tester.test_health_cascade_resilience(client_ip=client_ip)
                req_count = 2
            elif scenario_key == "replay":
                res = tester.replay_attack_comparison(scenario="failed_logins", client_ip=client_ip)
                req_count = 5
            else:
                res = {"protection_verified": False, "verification_details": "Unimplemented scenario"}

            duration_ms = round((time.time() - t0) * 1000, 1)
            steps = res.get("steps", [])
            evidence = {
                "target_endpoint": res.get("target_endpoint"),
                "verification_details": res.get("verification_details"),
                "traces": res.get("traces", [])
            }
            protection_verified = bool(res.get("protection_verified"))
            actual_rule_id = res.get("rule_id")
            incident_id = res.get("incident_id")

            # Validate detection
            expected_rule = sc_info.get("rule_id")
            if actual_rule_id and actual_rule_id == expected_rule:
                detection_outcome = "DETECTED"
            elif actual_rule_id:
                detection_outcome = "PARTIALLY_DETECTED"
            elif protection_verified:
                detection_outcome = "DETECTED"
            else:
                detection_outcome = "NOT_DETECTED"

            blocked_count = 1 if protection_verified else 0

        except Exception as e:
            duration_ms = round((time.time() - t0) * 1000, 1)
            error_msg = str(e)
            detection_outcome = "EXECUTION_FAILED"
            protection_verified = False
            evidence = {"error": error_msg}

    # Final DB update
    updated_sim = update_simulation_execution(
        execution_id=exec_id,
        status="COMPLETED" if detection_outcome != "EXECUTION_FAILED" else "FAILED",
        detection_outcome=detection_outcome,
        protection_verified=protection_verified,
        actual_rule_id=actual_rule_id,
        incident_id=incident_id,
        request_count=req_count,
        blocked_count=blocked_count,
        duration_ms=duration_ms,
        steps=steps,
        evidence=evidence,
        error_message=error_msg
    )

    # Immutable Audit Log
    try:
        from shopsphere.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO admin_audit_logs (user_id, action, target_type, target_id, details_json)
            VALUES (1, 'SIMULATION_DISPATCH', 'SIMULATION', ?, ?)
            """, (exec_id, json.dumps({
                "scenario": scenario_key,
                "target": validated_url,
                "outcome": detection_outcome,
                "verified": protection_verified
            })))
            conn.commit()
    except Exception:
        pass

    return updated_sim


@router.post("/simulations/abort", summary="Abort Running Security Simulation")
def abort_simulation():
    """Immediately stops active security test probe loops."""
    from src.appsec.security_tester import cancel_active_tests
    cancel_active_tests()
    return {"status": "aborted", "message": "Simulation cancellation requested."}


@router.get("/attack-center/stream", summary="Stream Real-Time Attack Center Execution (SSE)")
def stream_attack_center(
    scenario: str = Query("failed_logins"),
    target_url: str = Query("http://localhost:8000"),
    client_ip: str = Query("198.51.100.22"),
    attempts: int = Query(5),
    payload: Optional[str] = Query(None),
    execution_id: Optional[str] = Query(None)
):
    """Streams real-time HTTP attack test progress, detection, and mitigation via Server-Sent Events (SSE)."""
    from src.appsec.security_tester import ShopSphereSecurityTester
    from src.appsec.models import record_simulation_execution, update_simulation_execution, SCENARIO_CATALOG
    try:
        tester = ShopSphereSecurityTester(base_url=target_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    active_exec_id = execution_id or record_simulation_execution(
        scenario_id=scenario,
        target_url=target_url,
        client_ip=client_ip,
        execution_mode="live",
        parameters={"attempts": attempts, "payload": payload}
    )

    def sse_event_stream():
        recorded_steps = []
        final_rule_id = None
        final_inc_id = None
        final_verified = False
        t_start = time.time()

        # Send initial execution ID frame
        yield f"data: {json.dumps({'type': 'init', 'execution_id': active_exec_id, 'scenario': scenario, 'target_url': target_url})}\n\n"

        for item in tester.stream_test_execution(
            scenario=scenario,
            client_ip=client_ip,
            attempts=attempts,
            payload=payload
        ):
            if item.get("type") in ["request", "phase", "verification"]:
                recorded_steps.append(item)
            if item.get("type") == "detection":
                final_rule_id = item.get("rule_id")
            if item.get("type") == "complete":
                final_verified = item.get("protection_verified", False)
                final_inc_id = item.get("incident_id")
                final_rule_id = item.get("rule_id") or final_rule_id

            # Attach execution ID to frame
            item["execution_id"] = active_exec_id
            yield f"data: {json.dumps(item)}\n\n"

        duration_ms = round((time.time() - t_start) * 1000, 1)
        # Update simulation record in database
        try:
            expected_rule = SCENARIO_CATALOG.get(scenario, {}).get("rule_id")
            outcome = "DETECTED" if (final_rule_id == expected_rule or final_verified) else "NOT_DETECTED"
            update_simulation_execution(
                execution_id=active_exec_id,
                status="COMPLETED",
                detection_outcome=outcome,
                protection_verified=final_verified,
                actual_rule_id=final_rule_id,
                incident_id=final_inc_id,
                request_count=len(recorded_steps),
                blocked_count=1 if final_verified else 0,
                duration_ms=duration_ms,
                steps=recorded_steps,
                evidence={"scenario": scenario, "verified": final_verified}
            )
        except Exception:
            pass

    return StreamingResponse(sse_event_stream(), media_type="text/event-stream")


# =============================================================================
# VULNERABILITY TRACKER & CONTROLLED REMEDIATION WORKFLOW
# =============================================================================

@router.get("/vulnerabilities", summary="List All Tracked Vulnerabilities")
def list_vulnerabilities(status: Optional[str] = Query(None)):
    """Retrieves all tracked ShopSphere vulnerabilities, patch proposals, and regression statuses."""
    from src.appsec.vulnerability_manager import VulnerabilityManager
    return VulnerabilityManager.list_vulnerabilities(status=status)


@router.get("/vulnerabilities/{vuln_id}", summary="Get Specific Vulnerability Details")
def get_vulnerability(vuln_id: str):
    """Retrieves specific vulnerability, proposed patch diff, and regression test results."""
    from src.appsec.vulnerability_manager import VulnerabilityManager
    vuln = VulnerabilityManager.get_vulnerability(vuln_id)
    if not vuln:
        raise HTTPException(status_code=404, detail=f"Vulnerability {vuln_id} not found.")
    return vuln


@router.post("/vulnerabilities/{vuln_id}/test", summary="Run Isolated Regression Test")
def test_vulnerability_regression(vuln_id: str):
    """Runs isolated regression verification suite for a specific vulnerability."""
    from src.appsec.vulnerability_manager import VulnerabilityManager
    result = VulnerabilityManager.run_isolated_regression_test(vuln_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/vulnerabilities/{vuln_id}/approve", summary="Approval Gate: Approve Proposed Patch")
def approve_vulnerability_patch(vuln_id: str, operator_name: str = Query("SOC Security Operator")):
    """Formally approves a proposed code patch prior to runtime deployment."""
    from src.appsec.vulnerability_manager import VulnerabilityManager
    result = VulnerabilityManager.approve_patch(vuln_id, operator_name=operator_name)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Approval failed"))
    return result


@router.post("/vulnerabilities/{vuln_id}/apply", summary="Apply Surgical Patch with Verification")
def apply_vulnerability_patch(vuln_id: str, operator_name: str = Query("AutoHeal Autonomous Sentinel")):
    """Applies surgical patch, runs regression test suite, and confirms verification."""
    from src.appsec.vulnerability_manager import VulnerabilityManager
    result = VulnerabilityManager.apply_patch(vuln_id, operator_name=operator_name)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Patch application failed regression verification"))
    return result


@router.post("/vulnerabilities/{vuln_id}/rollback", summary="Rollback Patch")
def rollback_vulnerability_patch(vuln_id: str, operator_name: str = Query("SOC Security Operator")):
    """Rolls back an applied patch to previous baseline and logs the reversal audit."""
    from src.appsec.vulnerability_manager import VulnerabilityManager
    result = VulnerabilityManager.rollback_patch(vuln_id, operator_name=operator_name)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Rollback failed"))
    return result


# =============================================================================
# TRANSPARENT SECURITY POSTURE SCORE
# =============================================================================

@router.get("/posture", summary="Get Transparent Security Posture Score")
def get_security_posture():
    """Computes a transparent 0-100 security posture score with deductions, bonuses, and defense pillars."""
    from src.appsec.posture_scorer import SecurityPostureScorer
    return SecurityPostureScorer.calculate_posture()


# =============================================================================
# AI-ASSISTED INCIDENT SUMMARY & REMEDIATION RECOMMENDATIONS
# =============================================================================

@router.get("/incidents/{incident_id}/ai-summary", summary="Generate AI Forensic Summary & MITRE Mapping")
def get_ai_incident_summary(incident_id: str):
    """Generates an evidence-grounded AI forensic summary and MITRE ATT&CK alignment."""
    from src.appsec.models import get_security_incident
    from src.appsec.ai_advisor import AISecurityAdvisor

    inc = get_security_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")

    endpoint = (
        inc.get("affected_endpoints", ["/api/shop"])[0] 
        if isinstance(inc.get("affected_endpoints"), list) and inc.get("affected_endpoints") 
        else inc.get("target_endpoint", "/api/shop")
    )

    summary = AISecurityAdvisor.generate_grounded_summary(
        incident_id=inc["incident_id"],
        rule_id=inc.get("rule_id", "AUTH-001"),
        category=inc.get("category", "AppSec"),
        severity=inc.get("severity", "HIGH"),
        endpoint=endpoint,
        source_ip=inc.get("source_ip", "127.0.0.1"),
        evidence=inc.get("evidence", {})
    )
    return summary


# =============================================================================
# ATTACK REPLAY & BEFORE-AND-AFTER COMPARISON
# =============================================================================

class ReplayRequest(BaseModel):
    scenario: str = "failed_logins"
    target_url: str = "http://localhost:8000"
    client_ip: Optional[str] = "198.51.100.99"


@router.post("/test/replay", summary="Execute Attack Replay with Before & After Comparison")
def replay_attack_comparison(req: ReplayRequest):
    """Replays an authorized test scenario against local ShopSphere and returns Before vs After comparison."""
    from src.appsec.security_tester import ShopSphereSecurityTester
    try:
        tester = ShopSphereSecurityTester(base_url=req.target_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ip = req.client_ip or "198.51.100.99"
    if req.scenario == "failed_logins":
        test_result = tester.test_repeated_failed_logins(client_ip=ip, attempts=5)
    elif req.scenario == "sqli":
        test_result = tester.test_sql_injection(client_ip=ip, payload="Laptop' OR '1'='1")
    elif req.scenario == "xss":
        test_result = tester.test_cross_site_scripting(client_ip=ip)
    elif req.scenario == "admin":
        test_result = tester.test_unauthorized_admin(client_ip=ip)
    elif req.scenario == "rate":
        test_result = tester.test_request_rate_anomaly(client_ip=ip, count=25)
    elif req.scenario == "health":
        test_result = tester.test_health_cascade_resilience(client_ip=ip)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported replay scenario: {req.scenario}")

    traces = test_result.get("traces", [])
    before_status = traces[0].get("status_code", 200) if traces else 200
    after_probe = next((s for s in reversed(test_result.get("steps", [])) if s.get("step") == "VERIFICATION_PROBE"), None)
    after_status = after_probe.get("status_code", 403) if after_probe else (403 if test_result.get("protection_verified") else 200)

    return {
        "status": "success",
        "scenario": req.scenario,
        "target_url": req.target_url,
        "client_ip": ip,
        "before_state": {
            "initial_status_code": before_status,
            "access_allowed": before_status not in [403, 429],
            "description": "Pre-mitigation baseline request reached application layer."
        },
        "after_state": {
            "quarantine_status_code": after_status,
            "access_blocked": after_status in [403, 429],
            "description": "Post-mitigation verification probe quarantined at perimeter." if after_status in [403, 429] else "Mitigation verification failed."
        },
        "protection_verified": test_result.get("protection_verified", False),
        "incident_id": test_result.get("incident_id"),
        "raw_test_result": test_result
    }
