"""
AutoHeal Phase 8: AI SOC Copilot REST API Router
Exposes endpoints for interactive grounded chat, incident investigation,
report generation, conversation session management, and provider status.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Query, Path, HTTPException
from fastapi.responses import JSONResponse

from shopsphere.database import get_db_connection, init_db
from src.appsec.copilot_engine import (
    AIProviderManager, EvidenceRetriever, CopilotInvestigationPipeline,
    IncidentReportGenerator, get_or_create_conversation, append_conversation_message
)

router = APIRouter(prefix="/api/copilot", tags=["AI SOC Copilot"])


class CopilotChatRequest(BaseModel):
    question: Optional[str] = Field(None, max_length=2000, description="Analyst question or investigation query")
    message: Optional[str] = Field(None, max_length=2000, description="Analyst message alias")
    session_id: Optional[str] = Field(None, description="Optional conversation session ID")
    incident_id: Optional[str] = Field(None, description="Optional incident ID focus")
    analyst_id: Optional[str] = Field("SOC-ANALYST-1", description="Author identifier")


class ReportGenerateRequest(BaseModel):
    incident_id: Optional[str] = Field(None, description="Target incident ID to generate report for")
    author: Optional[str] = Field("AutoHeal AI SOC Copilot", description="Report author / analyst sign-off")


@router.get("/provider-status", summary="Check Active AI Provider Configuration & Health")
def fetch_provider_status():
    """Returns whether a real LLM is configured or platform is running in deterministic local mode."""
    try:
        status = AIProviderManager.get_provider_status()
        return JSONResponse(status_code=200, content=status)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to check provider: {str(e)}"})


@router.post("/chat", summary="Interact with AI SOC Copilot")
def chat_with_copilot(req: CopilotChatRequest):
    """
    Submits an analyst investigation query. Grounds response strictly in SQLite telemetry,
    redacts sensitive secrets, separates confirmed facts from hypotheses, and persists conversation.
    """
    try:
        query_text = req.question or req.message or "Investigate incident"
        # 1. Retrieve or start conversation session
        session = get_or_create_conversation(req.session_id, req.incident_id, req.analyst_id or "SOC-ANALYST-1")
        session_id = session["session_id"]

        # 2. Append analyst question
        analyst_msg = {
            "sender": "analyst",
            "role": "analyst",
            "timestamp": session.get("timestamp") or "",
            "content": query_text
        }
        append_conversation_message(session_id, analyst_msg)

        # 3. Execute investigation pipeline
        investigation = CopilotInvestigationPipeline.investigate(
            question=query_text,
            incident_id=req.incident_id
        )

        # 4. Append Copilot response
        copilot_msg = {
            "sender": "copilot",
            "role": "copilot",
            "timestamp": investigation["timestamp"],
            "content": investigation["answer"],
            "confirmed_facts": investigation.get("confirmed_facts", []),
            "confirmed_findings": investigation.get("confirmed_findings", []),
            "probable_causes": investigation.get("probable_causes", []),
            "unverified_hypotheses": investigation.get("unverified_hypotheses", []),
            "hypotheses": investigation.get("hypotheses", []),
            "evidence_references": investigation.get("evidence_references", []),
            "citations": investigation.get("citations", []),
            "recommended_steps": investigation.get("recommended_steps", []),
            "recommended_playbooks": investigation.get("recommended_playbooks", []),
            "confidence_score": investigation.get("confidence_score", 0.9),
            "confidence_basis": investigation.get("confidence_basis", ""),
            "provider_info": investigation.get("provider_info", {})
        }
        append_conversation_message(session_id, copilot_msg)

        return JSONResponse(status_code=200, content={
            "session_id": session_id,
            "response": copilot_msg,
            "reply": copilot_msg["content"],
            "citations": copilot_msg["citations"],
            "structured_findings": investigation,
            "incident_id": investigation["incident_id"]
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Copilot investigation failed: {str(e)}"})


@router.get("/investigate/{incident_id}", summary="Generate Grounded Investigation Dossier")
def get_investigation_dossier(incident_id: str = Path(..., description="Target Incident ID")):
    """Retrieves an instant, structured investigation dossier for an incident."""
    try:
        dossier = CopilotInvestigationPipeline.investigate(
            question=f"Provide full forensic analysis for {incident_id}",
            incident_id=incident_id
        )
        return JSONResponse(status_code=200, content=dossier)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to investigate incident: {str(e)}"})


@router.get("/evidence", summary="Retrieve Normalized Evidence for Incident")
def get_incident_evidence(incident_id: str = Query(..., description="Target Incident ID")):
    """Retrieves normalized, secret-redacted evidence tokens, events, and telemetry."""
    try:
        evidence = EvidenceRetriever.get_incident_evidence(incident_id)
        if not evidence.get("found"):
            return JSONResponse(status_code=404, content=evidence)
        return JSONResponse(status_code=200, content=evidence)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to retrieve evidence: {str(e)}"})


@router.post("/reports/generate", summary="Generate Formal Incident Report")
def generate_incident_report(
    req: Optional[ReportGenerateRequest] = None,
    incident_id: Optional[str] = Query(None, description="Optional incident ID query parameter")
):
    """Compiles a complete audit-ready incident report and persists it to the database."""
    target_id = (req.incident_id if req and req.incident_id else None) or incident_id or "INC-1004"
    author = (req.author if req and req.author else None) or "AutoHeal AI SOC Copilot"
    try:
        report = IncidentReportGenerator.generate_report(target_id, author)
        return JSONResponse(status_code=200, content={"report": report, **report})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to generate report: {str(e)}"})


@router.get("/reports", summary="List Historical Incident Reports")
def list_incident_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Returns paginated list of generated incident reports."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM incident_reports")
        total = cursor.fetchone()[0]

        cursor.execute("""
        SELECT report_id, incident_id, title, status, author, version, created_at 
        FROM incident_reports 
        ORDER BY created_at DESC LIMIT ? OFFSET ?
        """, (limit, offset))
        reports = [dict(r) for r in cursor.fetchall()]

        return JSONResponse(status_code=200, content={
            "total": total,
            "limit": limit,
            "offset": offset,
            "reports": reports
        })


@router.get("/reports/{report_id}", summary="Retrieve Full Incident Report Details")
def get_single_report(report_id: str = Path(..., description="Target Report ID")):
    """Returns full JSON content and sections of a single incident report."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incident_reports WHERE report_id = ?", (report_id,))
        row = cursor.fetchone()
        if not row:
            return JSONResponse(status_code=404, content={"error": f"Report {report_id} not found"})

        data = dict(row)
        try:
            data["full_report"] = json.loads(data["full_report_json"])
        except Exception:
            data["full_report"] = {}

        return JSONResponse(status_code=200, content=data)


@router.get("/suggested-prompts", summary="Retrieve Contextual Investigation Prompts")
def get_suggested_prompts(incident_id: Optional[str] = Query(None)):
    """Returns suggested investigative prompts based on the selected incident."""
    inc_label = incident_id or "INC-INJ-1004"
    prompts = [
        f"What happened in incident {inc_label}?",
        "Why was this event detected, and which rule triggered?",
        "What evidence supports the severity classification?",
        "What is the likely root cause versus unverified hypotheses?",
        "Which remediation actions and SOAR playbooks are available?",
        f"Generate formal incident report for {inc_label}."
    ]
    return JSONResponse(status_code=200, content={"incident_id": incident_id, "prompts": prompts})
