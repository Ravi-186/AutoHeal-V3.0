import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, Query, Response, Request, status
from fastapi.responses import JSONResponse

from src.appsec.soar_models import (
    get_soar_stats, query_playbooks_paginated, get_playbook,
    create_playbook, update_playbook_metadata, duplicate_playbook,
    archive_playbook, save_playbook_draft, publish_playbook_version,
    get_playbook_versions_list, list_soar_executions, get_soar_execution,
    cancel_soar_execution, list_pending_approvals, get_approval,
    decide_approval, list_soar_audit_logs, seed_default_playbooks_if_empty
)
from src.appsec.soar_engine import SOARValidator, SOARExecutionEngine, NODE_REGISTRY


router = APIRouter(prefix="/api/soar", tags=["Visual SOAR Automation Builder"])


# --- Request & Response Schemas ---

class CreatePlaybookRequest(BaseModel):
    name: str = Field(..., min_length=2)
    description: str = Field(..., min_length=5)
    category: str = "INJECTION"
    trigger_type: str = "NEW_INCIDENT"
    trigger_config: Optional[Dict[str, Any]] = None
    owner: Optional[str] = "admin@sentinel.sec"
    required_permissions: Optional[List[str]] = None
    initial_nodes: Optional[List[Dict[str, Any]]] = None
    initial_edges: Optional[List[Dict[str, Any]]] = None


class UpdatePlaybookRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    owner: Optional[str] = None


class SaveDraftRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    viewport: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = ""
    author: Optional[str] = "admin@sentinel.sec"


class PublishRequest(BaseModel):
    version: Optional[int] = None
    validation_hash: Optional[str] = None
    author: Optional[str] = "admin@sentinel.sec"


class ValidateWorkflowRequest(BaseModel):
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    definition: Optional[Dict[str, Any]] = None
    playbook_id: Optional[str] = None


class ExecutePlaybookRequest(BaseModel):
    version: Optional[int] = None
    incident_id: Optional[str] = None
    trigger_payload: Optional[Dict[str, Any]] = None
    actor: Optional[str] = "admin@sentinel.sec"


class CancelExecutionRequest(BaseModel):
    reason: Optional[str] = ""
    actor: Optional[str] = "admin@sentinel.sec"


class ApprovalDecisionRequest(BaseModel):
    decision: str  # 'APPROVED' or 'REJECTED'
    reason: Optional[str] = ""
    decided_by: Optional[str] = "admin@sentinel.sec"


# --- Endpoints ---

@router.get("/stats", summary="Get Real-Time SOAR Operational Metrics")
def get_stats():
    """Returns aggregated SOAR metrics derived from SQLite tables."""
    try:
        return get_soar_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node-types", summary="Get Registered SOAR Node Specifications")
def get_node_types():
    """Returns the complete catalog of supported SOAR node types."""
    return {"node_types": NODE_REGISTRY, **NODE_REGISTRY}


@router.get("/playbooks", summary="List SOAR Playbooks with Pagination & Filtering")
def list_playbooks(
    search: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    sort_by: str = "updated_at",
    sort_order: str = "desc"
):
    """Retrieves paginated playbooks with execution statistics."""
    try:
        return query_playbooks_paginated(
            search=search,
            category=category,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playbooks", summary="Create New Playbook Draft")
def create_new_playbook(req: CreatePlaybookRequest):
    """Creates a new playbook with initial draft version."""
    try:
        return create_playbook(
            name=req.name,
            description=req.description,
            category=req.category,
            trigger_type=req.trigger_type,
            trigger_config=req.trigger_config,
            owner=req.owner or "admin@sentinel.sec",
            required_permissions=req.required_permissions,
            initial_nodes=req.initial_nodes,
            initial_edges=req.initial_edges
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/playbooks/{playbook_id}", summary="Get Playbook Details & Graph")
def get_playbook_details(playbook_id: str):
    """Retrieves a single playbook with its current version canvas graph."""
    pb = get_playbook(playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail=f"Playbook '{playbook_id}' not found.")
    return pb


@router.put("/playbooks/{playbook_id}", summary="Update Playbook Metadata")
def update_playbook(playbook_id: str, req: UpdatePlaybookRequest):
    """Updates high-level playbook metadata."""
    try:
        return update_playbook_metadata(
            playbook_id=playbook_id,
            name=req.name,
            description=req.description,
            category=req.category,
            trigger_type=req.trigger_type,
            trigger_config=req.trigger_config,
            status=req.status,
            owner=req.owner
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playbooks/{playbook_id}/duplicate", summary="Duplicate Playbook")
def duplicate_existing_playbook(playbook_id: str):
    """Duplicates an existing playbook with its canvas graph into a new draft."""
    try:
        return duplicate_playbook(playbook_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/playbooks/{playbook_id}", summary="Archive Playbook")
def archive_existing_playbook(playbook_id: str):
    """Safely archives a playbook, preventing active execution."""
    try:
        return archive_playbook(playbook_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/playbooks/{playbook_id}/versions", summary="List Playbook Version History")
def get_versions(playbook_id: str):
    """Lists historical versions of a playbook."""
    return get_playbook_versions_list(playbook_id)


@router.post("/playbooks/{playbook_id}/versions/draft", summary="Save Playbook Canvas Draft")
def save_draft(playbook_id: str, req: SaveDraftRequest):
    """Saves workflow graph changes to the current active draft version."""
    try:
        return save_playbook_draft(
            playbook_id=playbook_id,
            nodes=req.nodes,
            edges=req.edges,
            viewport=req.viewport,
            change_summary=req.change_summary or "",
            actor=req.author or "admin@sentinel.sec"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playbooks/{playbook_id}/publish", summary="Publish Playbook Version")
def publish_version(playbook_id: str, req: Optional[PublishRequest] = None):
    """Validates and publishes a playbook version for active execution."""
    req = req or PublishRequest()
    pb = get_playbook(playbook_id)
    if not pb:
        raise HTTPException(status_code=404, detail="Playbook not found.")

    v_data = pb.get("version_data", {})
    val_res = SOARValidator.validate_workflow(v_data.get("nodes", []), v_data.get("edges", []))
    if not val_res["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot publish invalid workflow: {'; '.join(val_res['errors'])}"
        )

    try:
        return publish_playbook_version(
            playbook_id=playbook_id,
            version=req.version,
            validation_hash=val_res.get("validation_hash"),
            actor=req.author or "admin@sentinel.sec"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playbooks/validate", summary="Validate Workflow Directed Acyclic Graph (DAG)")
def validate_workflow(req: ValidateWorkflowRequest):
    """Executes backend-authoritative validation over nodes and edges."""
    nodes = req.nodes
    edges = req.edges
    if nodes is None and req.definition:
        nodes = req.definition.get("nodes", [])
        edges = req.definition.get("edges", [])
    nodes = nodes or []
    edges = edges or []
    return SOARValidator.validate_workflow(nodes, edges)


@router.post("/playbooks/{playbook_id}/execute", summary="Execute Playbook (Live)")
def execute_playbook(playbook_id: str, req: ExecutePlaybookRequest):
    """Executes a playbook in LIVE mode against ShopSphere."""
    try:
        return SOARExecutionEngine.execute_playbook(
            playbook_id=playbook_id,
            version=req.version,
            trigger_payload=req.trigger_payload,
            execution_mode="LIVE",
            incident_id=req.incident_id,
            actor=req.actor or "admin@sentinel.sec"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/playbooks/{playbook_id}/dry-run", summary="Dry-Run Playbook Execution")
def dry_run_playbook(playbook_id: str, req: ExecutePlaybookRequest):
    """Executes a playbook in DRY_RUN mode (simulates actions without mutating security state)."""
    try:
        return SOARExecutionEngine.execute_playbook(
            playbook_id=playbook_id,
            version=req.version,
            trigger_payload=req.trigger_payload,
            execution_mode="DRY_RUN",
            incident_id=req.incident_id,
            actor=req.actor or "admin@sentinel.sec"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions", summary="List SOAR Workflow Executions")
def list_executions(
    playbook_id: Optional[str] = None,
    incident_id: Optional[str] = None,
    status: Optional[str] = None,
    execution_mode: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Retrieves paginated workflow execution history."""
    try:
        data = list_soar_executions(
            playbook_id=playbook_id,
            incident_id=incident_id,
            status=status,
            execution_mode=execution_mode,
            page=page,
            page_size=page_size
        )
        if isinstance(data, dict):
            data["executions"] = data.get("items", [])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}", summary="Get Execution Telemetry & Node Traces")
def get_execution_details(execution_id: str):
    """Retrieves detailed execution state along with per-node input/output traces."""
    exec_data = get_soar_execution(execution_id)
    if not exec_data:
        raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found.")
    return {
        "execution": exec_data,
        "nodes": exec_data.get("nodes", []),
        **exec_data
    }


@router.post("/executions/{execution_id}/cancel", summary="Cancel Running Execution")
def cancel_execution(execution_id: str, req: Optional[CancelExecutionRequest] = None):
    """Cancels an in-flight or waiting execution."""
    req = req or CancelExecutionRequest()
    try:
        return cancel_soar_execution(
            execution_id=execution_id,
            actor=req.actor or "admin@sentinel.sec",
            reason=req.reason or ""
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals", summary="List Pending Approval Gates")
@router.get("/approvals/pending", summary="List Pending Approval Gates (Alias)")
def get_approvals(execution_id: Optional[str] = None):
    """Lists pending human-in-the-loop approval gates."""
    return list_pending_approvals(execution_id)


@router.post("/approvals/{approval_id}/decide", summary="Approve or Reject Gate")
def decide_approval_gate(approval_id: str, req: ApprovalDecisionRequest):
    """Submits decision for an approval gate and resumes paused workflow."""
    try:
        res = decide_approval(
            approval_id=approval_id,
            decision=req.decision,
            decided_by=req.decided_by or "admin@sentinel.sec",
            reason=req.reason or ""
        )

        # Resume the execution whether approved or rejected
        if res.get("execution_id"):
            exec_row = get_soar_execution(res["execution_id"])
            if exec_row and exec_row["status"] == "WAITING_FOR_APPROVAL":
                resumed_exec = SOARExecutionEngine.execute_playbook(
                    playbook_id=exec_row["playbook_id"],
                    version=exec_row["playbook_version"],
                    trigger_payload=exec_row["context"].get("trigger_payload"),
                    execution_mode=exec_row["execution_mode"],
                    incident_id=exec_row["incident_id"],
                    actor=req.decided_by or "admin@sentinel.sec",
                    resume_from_approval_id=approval_id
                )
                if resumed_exec:
                    resumed_exec["approval_id"] = approval_id
                    resumed_exec["decision"] = req.decision
                    return resumed_exec

        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs", summary="List SOAR Security Audit Logs")
def get_audit_logs(
    playbook_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100)
):
    """Retrieves paginated SOAR audit logs."""
    data = list_soar_audit_logs(
        playbook_id=playbook_id,
        execution_id=execution_id,
        page=page,
        page_size=page_size
    )
    if isinstance(data, dict):
        data["audit_logs"] = data.get("items", [])
    return data
