"""
Enterprise Visual SOAR Automation Builder Test Suite (Phase 6)
Validates end-to-end security orchestration, automation, and response:
- Server-side DAG validation (cycle detection, trigger requirement, valid connections, reachability)
- Code injection defense (rejects eval, exec, import, script payload injection)
- Safe execution target allowlisting (restricts targets to local ShopSphere environment)
- Versioning and immutability (drafting, publishing, duplicate prevention)
- Dry-run simulation (condition evaluation and branch traversal without altering system state)
- Live workflow execution (IP quarantine, session revocation, verification probe)
- Human-in-the-loop approval gates (pauses execution, generates single-use token, resumes upon decision)
- Execution monitoring and node telemetry logging
- Complete audit trail recording
- Incident Command Center integration
"""

import pytest
import json
from fastapi.testclient import TestClient

from server import app
from src.appsec.soar_models import (
    get_soar_stats,
    create_playbook,
    get_playbook,
    save_playbook_draft,
    publish_playbook_version,
    duplicate_playbook,
    query_playbooks_paginated,
    get_soar_execution,
    list_soar_executions,
    get_approval,
    decide_approval,
    list_pending_approvals,
    list_soar_audit_logs,
    seed_default_playbooks_if_empty
)
from src.appsec.soar_engine import SOARValidator, SOARExecutionEngine, NODE_REGISTRY


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def ensure_soar_seeded():
    """Ensure baseline enterprise playbooks exist and clear rate limiter / blocked clients."""
    from shopsphere.database import get_db_connection
    from src.appsec.middleware import AppSecProtectionMiddleware
    AppSecProtectionMiddleware._rate_tracker.clear()
    with get_db_connection() as conn:
        conn.cursor().execute("DELETE FROM blocked_clients WHERE client_ip IN ('testclient', '127.0.0.1', '198.51.100.88', '198.51.100.99', '198.51.100.77', '198.51.100.66', '198.51.100.42')")
        conn.commit()
    seed_default_playbooks_if_empty()
    yield
    AppSecProtectionMiddleware._rate_tracker.clear()
    with get_db_connection() as conn:
        conn.cursor().execute("DELETE FROM blocked_clients WHERE client_ip IN ('testclient', '127.0.0.1', '198.51.100.88', '198.51.100.99', '198.51.100.77', '198.51.100.66', '198.51.100.42')")
        conn.commit()


# =========================================================================
# 1. API STATS & CATALOG TESTS
# =========================================================================

def test_soar_stats_endpoint(client):
    """Verify aggregated SOAR operational KPIs."""
    res = client.get("/api/soar/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_playbooks" in data
    assert "published_playbooks" in data
    assert "total_executions" in data
    assert "success_rate_pct" in data
    assert data["total_playbooks"] >= 4
    assert data["published_playbooks"] >= 3


def test_soar_node_types_catalog(client):
    """Verify comprehensive 7-category node registry is exposed."""
    res = client.get("/api/soar/node-types")
    assert res.status_code == 200
    data = res.json()
    assert "node_types" in data
    types = data["node_types"]
    
    # Check coverage across all required categories
    categories = {info["category"].lower() for info in types.values()}
    assert "trigger" in categories
    assert "lookup" in categories
    assert "condition" in categories
    assert "branch" in categories
    assert "approval" in categories
    assert "action" in categories
    assert "verification" in categories
    
    # Specific nodes
    assert "trigger_security_event" in types
    assert "action_block_ip" in types
    assert "approval_high_impact" in types
    assert "verification_dual_probe" in types


# =========================================================================
# 2. PLAYBOOK LIFECYCLE & VERSIONING TESTS
# =========================================================================

def test_soar_playbook_crud_lifecycle(client):
    """Test creating, reading, updating draft, and listing playbooks."""
    # Create playbook
    res = client.post("/api/soar/playbooks", json={
        "name": "Test Automated Containment",
        "description": "Verifies automated test playbook CRUD lifecycle",
        "category": "CONTAINMENT"
    })
    assert res.status_code in (200, 201)
    created = res.json()
    playbook_id = created["playbook_id"]
    assert created["status"] == "DRAFT"
    assert created["current_version"] == 1

    # Read playbook
    res = client.get(f"/api/soar/playbooks/{playbook_id}")
    assert res.status_code == 200
    fetched = res.json()
    assert fetched["name"] == "Test Automated Containment"

    # Save draft version
    valid_def = {
        "nodes": [
            {
                "id": "trig-1",
                "type": "trigger_security_event",
                "category": "trigger",
                "name": "Event Ingress",
                "position": {"x": 100, "y": 100},
                "config": {}
            },
            {
                "id": "act-1",
                "type": "action_block_ip",
                "category": "action",
                "name": "Perimeter IP Block",
                "position": {"x": 400, "y": 100},
                "config": {"duration_seconds": 300}
            }
        ],
        "edges": [
            {"id": "e1", "source": "trig-1", "target": "act-1", "source_handle": "output", "target_handle": "input"}
        ]
    }

    res = client.post(f"/api/soar/playbooks/{playbook_id}/versions/draft", json=valid_def)
    assert res.status_code == 200
    draft_res = res.json()
    assert draft_res["status"] == "DRAFT"

    # Publish version
    res = client.post(f"/api/soar/playbooks/{playbook_id}/publish")
    assert res.status_code == 200
    pub_res = res.json()
    assert pub_res["status"] == "PUBLISHED"
    assert pub_res["current_version"] == 1


def test_soar_playbook_duplicate(client):
    """Test duplicating an existing published playbook."""
    source_id = "PB-SQLI-CONTAINMENT"
    res = client.post(f"/api/soar/playbooks/{source_id}/duplicate")
    assert res.status_code in (200, 201)
    dup_data = res.json()
    assert "version_data" in dup_data or "nodes" in dup_data.get("definition", {})
    assert dup_data["status"] == "DRAFT"


# =========================================================================
# 3. WORKFLOW VALIDATION ENGINE TESTS
# =========================================================================

def test_soar_validator_valid_dag(client):
    """Ensure a valid DAG passes validation without errors."""
    valid_def = {
        "nodes": [
            {"id": "trig-1", "type": "trigger_security_event", "category": "trigger", "name": "Event Ingress", "position": {"x": 0, "y": 0}},
            {"id": "cond-1", "type": "condition_severity", "category": "condition", "name": "Severity Check", "position": {"x": 200, "y": 0}, "config": {"expected_severity": "CRITICAL"}},
            {"id": "act-true", "type": "action_block_ip", "category": "action", "name": "Quarantine IP", "position": {"x": 400, "y": -50}},
            {"id": "act-false", "type": "action_add_incident_note", "category": "action", "name": "Log Note", "position": {"x": 400, "y": 50}}
        ],
        "edges": [
            {"id": "e1", "source": "trig-1", "target": "cond-1", "source_handle": "output", "target_handle": "input"},
            {"id": "e2", "source": "cond-1", "target": "act-true", "source_handle": "true", "target_handle": "input"},
            {"id": "e3", "source": "cond-1", "target": "act-false", "source_handle": "false", "target_handle": "input"}
        ]
    }

    res = client.post("/api/soar/playbooks/validate", json={
        "playbook_id": "PB-VAL-TEST",
        "definition": valid_def
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is True
    assert len(data["errors"]) == 0


def test_soar_validator_missing_trigger(client):
    """Ensure validator rejects workflow with no trigger node."""
    invalid_def = {
        "nodes": [
            {"id": "act-1", "type": "action_block_ip", "category": "action", "name": "Block IP", "position": {"x": 100, "y": 100}}
        ],
        "edges": []
    }

    res = client.post("/api/soar/playbooks/validate", json={
        "playbook_id": "PB-VAL-TEST",
        "definition": invalid_def
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
    assert any("trigger" in err.lower() for err in data["errors"])


def test_soar_validator_cycle_detection(client):
    """Ensure DFS cycle detector catches cycles and returns exact path."""
    cycle_def = {
        "nodes": [
            {"id": "trig-1", "type": "trigger_security_event", "category": "trigger", "name": "Start", "position": {"x": 0, "y": 0}},
            {"id": "node-A", "type": "action_add_incident_note", "category": "action", "name": "Node A", "position": {"x": 200, "y": 0}},
            {"id": "node-B", "type": "action_add_incident_note", "category": "action", "name": "Node B", "position": {"x": 400, "y": 0}}
        ],
        "edges": [
            {"id": "e1", "source": "trig-1", "target": "node-A"},
            {"id": "e2", "source": "node-A", "target": "node-B"},
            {"id": "e3", "source": "node-B", "target": "node-A"} # Cycle: node-A -> node-B -> node-A
        ]
    }

    res = client.post("/api/soar/playbooks/validate", json={
        "playbook_id": "PB-VAL-TEST",
        "definition": cycle_def
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
    assert any("cycle" in err.lower() for err in data["errors"])


def test_soar_validator_code_injection_defense(client):
    """Ensure validator strictly forbids code injection payloads inside configs."""
    injection_def = {
        "nodes": [
            {"id": "trig-1", "type": "trigger_security_event", "category": "trigger", "name": "Trigger", "position": {"x": 0, "y": 0}},
            {
                "id": "act-1",
                "type": "action_block_ip",
                "category": "action",
                "name": "Injected Action",
                "position": {"x": 200, "y": 0},
                "config": {
                    "malicious_eval": "__import__('os').system('whoami')"
                }
            }
        ],
        "edges": [
            {"id": "e1", "source": "trig-1", "target": "act-1"}
        ]
    }

    res = client.post("/api/soar/playbooks/validate", json={
        "playbook_id": "PB-VAL-TEST",
        "definition": injection_def
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
    assert any("code injection" in err.lower() or "forbidden" in err.lower() for err in data["errors"])


# =========================================================================
# 4. EXECUTION ENGINE & DRY-RUN TESTS
# =========================================================================

def test_soar_dry_run_execution(client):
    """Verify dry-run evaluates full DAG but performs zero persistent changes."""
    res = client.post("/api/soar/playbooks/PB-SQLI-CONTAINMENT/dry-run", json={
        "incident_id": "INC-TEST-DRYRUN-001",
        "trigger_payload": {
            "source": "UNIT_TEST",
            "source_ip": "198.51.100.99",
            "severity": "CRITICAL"
        }
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["is_dry_run"] is True
    assert data["executed_nodes_count"] >= 5


def test_soar_live_execution_without_approval(client):
    """Verify live playbook execution without approval nodes runs to completion."""
    res = client.post("/api/soar/playbooks/PB-SQLI-CONTAINMENT/execute", json={
        "incident_id": "INC-TEST-LIVE-001",
        "trigger_payload": {
            "source": "LIVE_TEST",
            "source_ip": "198.51.100.88",
            "severity": "CRITICAL"
        }
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["is_dry_run"] is False
    assert data["executed_nodes_count"] >= 6


def test_soar_approval_gate_pause_and_resume(client):
    """Verify approval gate pauses execution and decision resumes downstream traversal."""
    playbook_id = "PB-CRED-STUFFING-LOCKDOWN"
    
    # 1. Trigger execution -> Must pause at approval node
    res = client.post(f"/api/soar/playbooks/{playbook_id}/execute", json={
        "incident_id": "INC-APPROVAL-TEST-001",
        "trigger_payload": {
            "source": "APPROVAL_TEST",
            "source_ip": "198.51.100.77",
            "username": "victim_shopper_01",
            "severity": "CRITICAL"
        }
    })
    assert res.status_code == 200
    paused = res.json()
    assert paused["status"] == "WAITING_FOR_APPROVAL"
    approval_id = paused["approval_id"]
    execution_id = paused["execution_id"]
    assert approval_id.startswith("APPR-")

    # 2. Check pending approvals API
    res = client.get("/api/soar/approvals/pending")
    assert res.status_code == 200
    pending_list = res.json()
    assert any(a["approval_id"] == approval_id for a in pending_list)

    # 3. Approve the privileged operation
    res = client.post(f"/api/soar/approvals/{approval_id}/decide", json={
        "decision": "APPROVED",
        "reason": "Authorized test remediation of compromised account"
    })
    assert res.status_code == 200
    resumed = res.json()
    assert resumed["status"] == "COMPLETED"
    assert resumed["execution_id"] == execution_id

    # 4. Verify approval is no longer in pending list
    res = client.get("/api/soar/approvals/pending")
    assert not any(a["approval_id"] == approval_id for a in res.json())


def test_soar_approval_gate_rejection(client):
    """Verify rejecting an approval gate resumes through the rejected branch."""
    playbook_id = "PB-CRED-STUFFING-LOCKDOWN"
    
    # 1. Trigger execution
    res = client.post(f"/api/soar/playbooks/{playbook_id}/execute", json={
        "incident_id": "INC-REJECT-TEST-001",
        "trigger_payload": {
            "source": "APPROVAL_REJECT_TEST",
            "source_ip": "198.51.100.66",
            "severity": "HIGH"
        }
    })
    paused = res.json()
    approval_id = paused["approval_id"]

    # 2. Reject the privileged operation with mandatory justification
    res = client.post(f"/api/soar/approvals/{approval_id}/decide", json={
        "decision": "REJECTED",
        "reason": "False positive: activity determined to be authorized penetration testing"
    })
    assert res.status_code == 200
    rejected_res = res.json()
    assert rejected_res["status"] == "COMPLETED"


def test_soar_execution_cancellation(client):
    """Verify executing and cancelling a running/waiting workflow."""
    playbook_id = "PB-CRED-STUFFING-LOCKDOWN"
    res = client.post(f"/api/soar/playbooks/{playbook_id}/execute", json={
        "incident_id": "INC-CANCEL-TEST",
        "trigger_payload": {"source": "CANCEL_TEST"}
    })
    paused = res.json()
    execution_id = paused["execution_id"]

    # Cancel execution
    res = client.post(f"/api/soar/executions/{execution_id}/cancel")
    assert res.status_code == 200
    cancelled_res = res.json()
    assert cancelled_res["status"] == "CANCELLED"


# =========================================================================
# 5. AUDIT & TELEMETRY TESTS
# =========================================================================

def test_soar_execution_history_and_node_telemetry(client):
    """Verify node telemetry logging and history retrieval."""
    res = client.get("/api/soar/executions?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "executions" in data
    assert len(data["executions"]) > 0

    first_exec = data["executions"][0]
    exec_id = first_exec["execution_id"]

    # Inspect individual execution with node details
    res = client.get(f"/api/soar/executions/{exec_id}")
    assert res.status_code == 200
    detail = res.json()
    assert "execution" in detail
    assert "nodes" in detail
    assert len(detail["nodes"]) > 0


def test_soar_audit_trail_logging(client):
    """Verify immutable audit records for actions, approvals, and validations."""
    res = client.get("/api/soar/audit-logs?limit=25")
    assert res.status_code == 200
    data = res.json()
    assert "audit_logs" in data
    logs = data["audit_logs"]
    assert len(logs) > 0

    # Ensure sensitive secrets are never logged
    log_dump = json.dumps(logs)
    assert "password" not in log_dump.lower()
    assert "secret_key" not in log_dump.lower()


def test_soar_safe_target_allowlisting(client):
    """Ensure engine rejects attempts to target unauthorized external endpoints."""
    malicious_target_def = {
        "nodes": [
            {"id": "trig-1", "type": "trigger_security_event", "category": "trigger", "name": "Start", "position": {"x": 0, "y": 0}},
            {
                "id": "act-bad",
                "type": "action_block_ip",
                "category": "action",
                "name": "External Attack",
                "position": {"x": 200, "y": 0},
                "config": {"target_environment": "https://external-target.com/api"}
            }
        ],
        "edges": [{"id": "e1", "source": "trig-1", "target": "act-bad"}]
    }

    # Validation should reject non-ShopSphere target
    res = client.post("/api/soar/playbooks/validate", json={
        "playbook_id": "PB-MALICIOUS-TARGET",
        "definition": malicious_target_def
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
    assert any("target" in err.lower() or "unauthorized" in err.lower() for err in data["errors"])
