import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Query, Response, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
import json

from src.appsec.models import (
    get_security_events, list_security_incidents,
    get_security_incident, update_incident_status,
    get_active_blocked_clients, unblock_client_ip
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
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    client_ip: Optional[str] = Query(None),
    limit: int = Query(50, le=200)
):
    """Retrieves immutable security request logs and telemetry events."""
    return get_security_events(limit=limit, event_type=event_type, severity=severity, client_ip=client_ip)


@router.get("/incidents", summary="List Security Incidents")
def list_incidents(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, le=200)
):
    """Lists security incidents with evidence and mitigation records."""
    return list_security_incidents(status=status, severity=severity, limit=limit)


@router.get("/incidents/{incident_id}", summary="Get Incident Dossier")
def get_incident_dossier(incident_id: str):
    """Retrieves complete forensic incident evidence dossier."""
    inc = get_security_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found.")
    return inc


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


@router.get("/attack-center/stream", summary="Stream Real-Time Attack Center Execution (SSE)")
def stream_attack_center(
    scenario: str = Query("failed_logins"),
    target_url: str = Query("http://localhost:8000"),
    client_ip: str = Query("198.51.100.22"),
    attempts: int = Query(5),
    payload: Optional[str] = Query(None)
):
    """Streams real-time HTTP attack test progress, detection, and mitigation via Server-Sent Events (SSE)."""
    from src.appsec.security_tester import ShopSphereSecurityTester
    try:
        tester = ShopSphereSecurityTester(base_url=target_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    def sse_event_stream():
        for item in tester.stream_test_execution(
            scenario=scenario,
            client_ip=client_ip,
            attempts=attempts,
            payload=payload
        ):
            yield f"data: {json.dumps(item)}\n\n"

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
