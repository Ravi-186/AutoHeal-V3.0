"""
Self-Healing Command Center REST API
Exposes endpoints for the 14-state remediation lifecycle, real-time KPI overview,
live activity explorer, real system protection status, root-cause analysis (facts vs hypotheses),
remediation planning, explainable risk assessment, autonomy policy configuration,
emergency stop safety controls, and transactional rollback.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, Request

from src.appsec.self_healing_models import (
    get_self_healing_overview, list_self_healing_executions,
    get_self_healing_execution, create_self_healing_execution,
    update_execution_stage, update_execution_record,
    get_autonomy_policy, update_autonomy_policy,
    trigger_emergency_stop, resume_from_emergency_stop,
    is_emergency_stop_active, get_system_protection_status,
    get_self_healing_audit_logs
)
from src.appsec.self_healing_engine import (
    RootCauseAnalyzer, RemediationPlanner, RiskImpactAssessor,
    SelfHealingEngine
)

router = APIRouter(prefix="/api/self-healing", tags=["Self-Healing Command Center"])


# --- Pydantic Request Models ---

class GeneratePlansRequest(BaseModel):
    incident_id: str = Field(..., description="Target security incident ID")


class CreateExecutionRequest(BaseModel):
    incident_id: str
    threat_category: Optional[str] = "SUSPICIOUS_TRAFFIC"
    severity: Optional[str] = "HIGH"
    affected_asset: Optional[str] = "ShopSphere Web App"
    root_cause: Optional[Dict[str, Any]] = None
    selected_plan: Optional[Dict[str, Any]] = None
    risk_level: Optional[str] = "MEDIUM"
    actor: Optional[str] = "admin@sentinel.sec"


class ApprovePlanRequest(BaseModel):
    execution_id: str
    actor: Optional[str] = "admin@sentinel.sec"
    notes: Optional[str] = "Approved by SOC Lead Analyst"


class ExecutePlanRequest(BaseModel):
    execution_id: str
    plan: Dict[str, Any]
    actor: Optional[str] = "admin@sentinel.sec"
    dry_run: Optional[bool] = False


class VerifyRemediationRequest(BaseModel):
    execution_id: str
    plan: Dict[str, Any]
    actor: Optional[str] = "admin@sentinel.sec"


class RollbackRequest(BaseModel):
    execution_id: str
    actor: Optional[str] = "admin@sentinel.sec"
    reason: Optional[str] = "Operator initiated safe rollback"


class PolicyUpdateRequest(BaseModel):
    autonomy_level: int = Field(..., ge=0, le=3, description="0=Monitor, 1=Recommend, 2=Approved Automation, 3=Controlled Autonomous")
    action_allowlist: Optional[List[str]] = None
    target_allowlist: Optional[List[str]] = None
    max_risk_level: Optional[str] = "HIGH"
    require_approval_above_risk: Optional[str] = "LOW"
    max_concurrent_operations: Optional[int] = 5
    max_execution_duration_sec: Optional[int] = 300
    actor: Optional[str] = "admin@sentinel.sec"


class EmergencyStopRequest(BaseModel):
    actor: str = Field(..., min_length=2, description="Authorized administrator identifier")
    reason: str = Field(..., min_length=5, description="Mandatory reason for activating Emergency Stop")


class AIAssistantRequest(BaseModel):
    query: str
    incident_id: Optional[str] = None
    execution_id: Optional[str] = None


# --- API Routes ---

@router.get("/overview", summary="Real-Time Remediation Overview Metrics")
def get_overview():
    """Returns actual backend-derived metrics calculated strictly from persisted records."""
    return get_self_healing_overview()


@router.get("/activity", summary="Live Remediation Activity Explorer")
def get_activity(
    stage: Optional[str] = Query(None, description="Filter by lifecycle stage"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    approval_state: Optional[str] = Query(None, description="Filter by approval state"),
    search: Optional[str] = Query(None, description="Search keyword"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Retrieves paginated, searchable live remediation executions from SQLite."""
    return list_self_healing_executions(
        stage=stage,
        severity=severity,
        approval_state=approval_state,
        search=search,
        limit=limit,
        offset=offset
    )


@router.get("/executions/{execution_id}", summary="Get Single Execution Session Detail")
def get_execution_detail(execution_id: str):
    """Retrieves complete details, lifecycle stages, and verification results for an execution session."""
    record = get_self_healing_execution(execution_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Execution session '{execution_id}' not found.")
    return record


@router.get("/protection-status", summary="Real Subsystem Protection Status")
def get_protection_status():
    """Executes live operational health checks across all 8 security subsystems."""
    return get_system_protection_status()


@router.get("/diagnose/{incident_id}", summary="Root-Cause Analysis (Facts vs Hypotheses)")
def diagnose_incident(incident_id: str):
    """
    Performs root-cause analysis on an incident, explicitly categorizing:
    1. Confirmed Facts (Evidence-proven)
    2. Probable Causes (Rule-supported)
    3. AI Hypotheses (Requiring analyst validation)
    """
    return RootCauseAnalyzer.analyze_incident(incident_id)


@router.post("/plans/generate", summary="Generate Remediation Plans & Risk Assessment")
def generate_plans(req: GeneratePlansRequest):
    """Recommends safe remediation plans with explainable risk scoring for an incident."""
    plans = RemediationPlanner.generate_plans(req.incident_id)
    return {
        "incident_id": req.incident_id,
        "total_plans": len(plans),
        "plans": plans
    }


@router.post("/executions/create", summary="Initialize Self-Healing Execution Session")
def create_execution(req: CreateExecutionRequest):
    """Creates a new self-healing execution tracking session."""
    return create_self_healing_execution(
        incident_id=req.incident_id,
        threat_category=req.threat_category or "SUSPICIOUS_TRAFFIC",
        severity=req.severity or "HIGH",
        affected_asset=req.affected_asset or "ShopSphere Web App",
        root_cause=req.root_cause,
        selected_plan=req.selected_plan,
        risk_level=req.risk_level or "MEDIUM",
        actor=req.actor or "admin@sentinel.sec"
    )


@router.post("/approve", summary="Human Operator Approval Gate")
def approve_plan(req: ApprovePlanRequest):
    """Approves a proposed remediation plan and transitions state to APPROVED."""
    execution = get_self_healing_execution(req.execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution '{req.execution_id}' not found.")

    # Update approval state
    update_execution_record(req.execution_id, {
        "approval_state": "APPROVED",
        "approved_by": req.actor,
        "approved_at": None  # Will be set by CURRENT_TIMESTAMP in DB
    }, actor=req.actor or "admin@sentinel.sec")

    # Transition lifecycle stage to APPROVED
    success, msg = update_execution_stage(
        req.execution_id,
        "APPROVED",
        actor=req.actor or "admin@sentinel.sec",
        reason=req.notes or "Human analyst formal approval"
    )

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "success": True,
        "execution_id": req.execution_id,
        "approval_state": "APPROVED",
        "approved_by": req.actor,
        "message": f"Remediation plan for {req.execution_id} approved successfully."
    }


@router.post("/execute", summary="Execute Remediation Action (Live or Dry-Run)")
def execute_remediation(req: ExecutePlanRequest):
    """
    Executes an approved remediation plan.
    Supports dry_run simulation, captures pre-change state, applies action,
    and runs independent verification.
    """
    is_stopped, reason, trigger_by = is_emergency_stop_active()
    if is_stopped:
        raise HTTPException(
            status_code=423,
            detail=f"EXECUTION BLOCKED: Emergency Stop is active (Triggered by {trigger_by}: {reason})"
        )

    res = SelfHealingEngine.execute_plan(
        execution_id=req.execution_id,
        plan=req.plan,
        actor=req.actor or "admin@sentinel.sec",
        is_dry_run=bool(req.dry_run)
    )

    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Remediation execution failed."))

    return res


@router.post("/verify", summary="Trigger Independent Verification Probe")
def verify_remediation(req: VerifyRemediationRequest):
    """Triggers dual-probe synthetic verification against the enforcement layer."""
    res = SelfHealingEngine.verify_remediation(
        execution_id=req.execution_id,
        plan=req.plan,
        actor=req.actor or "admin@sentinel.sec"
    )
    return res


@router.post("/rollback", summary="Execute Safe Rollback")
def rollback_remediation(req: RollbackRequest):
    """Rolls back an applied remediation using captured pre-change state."""
    res = SelfHealingEngine.execute_rollback(
        execution_id=req.execution_id,
        actor=req.actor or "admin@sentinel.sec",
        reason=req.reason or "Manual rollback requested"
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Rollback failed."))
    return res


@router.get("/policies", summary="Get Active Autonomy Policy")
def get_policy():
    """Retrieves active autonomy policy settings, allowlists, and emergency stop status."""
    return get_autonomy_policy()


@router.put("/policies", summary="Update Autonomy Policy")
def update_policy(req: PolicyUpdateRequest):
    """Updates autonomy policy configuration. Increments version and logs audit record."""
    try:
        updated = update_autonomy_policy(
            policy_data=req.model_dump(),
            actor=req.actor or "admin@sentinel.sec"
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency-stop", summary="Activate Immediate Emergency Stop")
def emergency_stop(req: EmergencyStopRequest):
    """
    Activates immediate emergency stop.
    Halts all autonomous remediation operations while leaving detection and ingestion active.
    """
    return trigger_emergency_stop(actor=req.actor, reason=req.reason)


@router.post("/emergency-resume", summary="Resume from Emergency Stop")
def emergency_resume(req: EmergencyStopRequest):
    """Controlled restoration from emergency stop requiring authorized credentials."""
    return resume_from_emergency_stop(actor=req.actor, reason=req.reason)


@router.get("/audit-logs", summary="List Self-Healing Immutable Audit Logs")
def get_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    execution_id: Optional[str] = Query(None)
):
    """Retrieves immutable audit logs for self-healing actions and emergency stop triggers."""
    return get_self_healing_audit_logs(limit=limit, execution_id=execution_id)


@router.post("/ai-assistant", summary="AI Self-Healing Assistant")
def ai_assistant(req: AIAssistantRequest):
    """
    Provides AI-assisted incident summaries, root-cause explanations, risk breakdowns,
    and draft remediation reports. Operates deterministically with verified facts.
    """
    query = req.query.lower()
    incident_id = req.incident_id
    execution_id = req.execution_id

    # Retrieve context
    rc_data = RootCauseAnalyzer.analyze_incident(incident_id) if incident_id else {}
    exec_data = get_self_healing_execution(execution_id) if execution_id else None

    # Deterministic intelligent reasoning
    summary = ""
    next_steps = []

    if "root cause" in query or "diagnose" in query:
        facts = rc_data.get("confirmed_facts", [])
        hypotheses = rc_data.get("ai_hypotheses", [])
        summary = (
            f"Root-cause analysis for incident {incident_id or 'selected'}:\n"
            f"• Confirmed Facts: {'; '.join(facts[:2]) if facts else 'Evidence captured in event stream.'}\n"
            f"• Hypothesized Intent: {hypotheses[0] if hypotheses else 'Standard threat reconnaissance.'}"
        )
        next_steps = [
            "Review supporting telemetry events",
            "Generate remediation plan with Risk Assessment",
            "Evaluate autonomy policy Level 1/2 requirements"
        ]

    elif "risk" in query or "impact" in query:
        summary = (
            "Risk Assessment Summary:\n"
            "• Remediation actions are classified as Low (IP Block/Rate Limit), Medium (Adaptive Throttling), "
            "High (Session Revocation / Code Repair), or Critical (System Isolation).\n"
            "• IP Blocking has near-zero benign user collateral risk and is fully reversible.\n"
            "• Session revocation requires customer re-authentication and is considered High Impact."
        )
        next_steps = [
            "Select reversible action first (e.g., BLOCK_IP)",
            "Run dry-run simulation before executing",
            "Require formal human approval for High/Critical risk actions"
        ]

    elif "verification" in query or "verify" in query:
        summary = (
            "Independent Verification Standard:\n"
            "• A remediation is never marked successful based solely on API success.\n"
            "• The system runs synthetic perimeter probes to assert the adversary receives HTTP 403/429.\n"
            "• Simultaneously, a benign availability probe asserts legitimate shopping workflows receive HTTP 200."
        )
        next_steps = [
            "Execute synthetic dual-probe test",
            "Inspect probe latency and HTTP response codes",
            "If probe fails, trigger automatic rollback pending"
        ]

    else:
        summary = (
            f"AutoHeal Autonomous Sentinel Remediation Assistant:\n"
            f"Currently monitoring incident {incident_id or 'active session'}. "
            f"Autonomous response is governed by Autonomy Policy Level {get_autonomy_policy().get('autonomy_level', 1)}. "
            f"All state transitions require dual-probe verification prior to incident closure."
        )
        next_steps = [
            "Review Root Cause Analysis workspace",
            "Generate remediation plan",
            "Validate system protection status across all 8 subsystems"
        ]

    return {
        "query": req.query,
        "incident_id": incident_id,
        "execution_id": execution_id,
        "ai_response": summary,
        "recommended_next_steps": next_steps,
        "distinction_note": "Facts are verified from database evidence; hypotheses are analytical interpretations."
    }
