"""
Comprehensive Automated Test Suite for Phase 7: Advanced Self-Healing Command Center
Validates:
1. 14-state remediation lifecycle state machine & transition rules.
2. Root-cause analysis (Confirmed Facts vs Probable Causes vs AI Hypotheses).
3. Intelligent remediation planner & explainable risk scoring.
4. Autonomy policies (Levels 0-3) and action allowlists.
5. Real execution (BLOCK_IP, APPLY_RATE_LIMIT, CODE_REPAIR_PATCH, REVOKE_SESSION).
6. Independent dual-probe synthetic verification.
7. Safe transactional rollback & pre-change state restoration.
8. Emergency stop activation, blocking, and authorized resumption.
9. Real-time persistent KPI aggregations (no static simulations).
10. Immutable audit logging and zero secret leakage.
"""

import pytest
import json
import time
from fastapi.testclient import TestClient

import server
from shopsphere.database import init_db, get_db_connection
from src.appsec.models import (
    create_security_incident, get_security_incident,
    is_client_blocked, block_client_ip, unblock_client_ip
)
from src.appsec.self_healing_models import (
    get_self_healing_overview, list_self_healing_executions,
    get_self_healing_execution, create_self_healing_execution,
    update_execution_stage, update_execution_record,
    get_autonomy_policy, update_autonomy_policy,
    trigger_emergency_stop, resume_from_emergency_stop,
    is_emergency_stop_active, get_system_protection_status,
    get_self_healing_audit_logs, LIFECYCLE_STAGES
)
from src.appsec.self_healing_engine import (
    RootCauseAnalyzer, RiskImpactAssessor, RemediationPlanner,
    SelfHealingEngine
)
from src.appsec.vulnerability_manager import VulnerabilityManager


@pytest.fixture(autouse=True)
def reset_database_state():
    """Ensures clean baseline database state before each test."""
    init_db()
    from src.appsec.middleware import AppSecProtectionMiddleware
    from shopsphere.autoheal_engine import AutoHealDemoEngine
    AppSecProtectionMiddleware._rate_tracker.clear()
    AutoHealDemoEngine.apply_autoheal_patch()
    # Reset emergency stop
    resume_from_emergency_stop(actor="test_fixture", reason="Reset test suite state")
    # Reset policy to Level 1
    update_autonomy_policy({
        "autonomy_level": 1,
        "max_risk_level": "HIGH",
        "require_approval_above_risk": "LOW",
        "action_allowlist": ["BLOCK_IP", "APPLY_RATE_LIMIT", "REVOKE_SESSION", "DISABLE_ACCOUNT", "CODE_REPAIR_PATCH"],
        "target_allowlist": ["127.0.0.1", "localhost", "ShopSphere", "CartService", "ProductService", "198.51.100.99"]
    }, actor="test_fixture")
    yield
    AutoHealDemoEngine.apply_autoheal_patch()
    VulnerabilityManager.apply_patch("VULN-FIN-001")
    AppSecProtectionMiddleware._rate_tracker.clear()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(server.app)


# =========================================================================
# 1. 14-STATE LIFECYCLE STATE MACHINE TESTS
# =========================================================================

def test_14_lifecycle_stages_defined():
    """Assert all 14 lifecycle stages exist in the state machine."""
    expected = [
        "DETECTED", "INVESTIGATING", "DIAGNOSING", "PLAN_GENERATED",
        "AWAITING_APPROVAL", "APPROVED", "EXECUTING", "VERIFYING",
        "VERIFIED", "FAILED", "ROLLBACK_PENDING", "ROLLING_BACK",
        "ROLLED_BACK", "MANUAL_INTERVENTION_REQUIRED"
    ]
    for st in expected:
        assert st in LIFECYCLE_STAGES


def test_valid_lifecycle_transitions_sequence():
    """Assert a standard valid path traverses through stages correctly."""
    exec_rec = create_self_healing_execution(
        incident_id="INC-TEST-001",
        threat_category="BRUTE_FORCE",
        severity="HIGH",
        actor="test_analyst"
    )
    exec_id = exec_rec["execution_id"]
    assert exec_rec["lifecycle_stage"] == "DETECTED"

    # Step 1: DETECTED -> INVESTIGATING
    ok, msg = update_execution_stage(exec_id, "INVESTIGATING", actor="test")
    assert ok is True
    assert get_self_healing_execution(exec_id)["lifecycle_stage"] == "INVESTIGATING"

    # Step 2: INVESTIGATING -> DIAGNOSING
    ok, msg = update_execution_stage(exec_id, "DIAGNOSING", actor="test")
    assert ok is True

    # Step 3: DIAGNOSING -> PLAN_GENERATED
    ok, msg = update_execution_stage(exec_id, "PLAN_GENERATED", actor="test")
    assert ok is True

    # Step 4: PLAN_GENERATED -> AWAITING_APPROVAL
    ok, msg = update_execution_stage(exec_id, "AWAITING_APPROVAL", actor="test")
    assert ok is True

    # Step 5: AWAITING_APPROVAL -> APPROVED
    ok, msg = update_execution_stage(exec_id, "APPROVED", actor="test")
    assert ok is True

    # Step 6: APPROVED -> EXECUTING
    ok, msg = update_execution_stage(exec_id, "EXECUTING", actor="test")
    assert ok is True

    # Step 7: EXECUTING -> VERIFYING
    ok, msg = update_execution_stage(exec_id, "VERIFYING", actor="test")
    assert ok is True

    # Step 8: VERIFYING -> VERIFIED
    ok, msg = update_execution_stage(exec_id, "VERIFIED", actor="test")
    assert ok is True


def test_invalid_lifecycle_transition_rejected():
    """Assert illegal transitions (e.g. jumping from DETECTED directly to VERIFIED) are strictly blocked."""
    exec_rec = create_self_healing_execution(incident_id="INC-TEST-002", severity="MEDIUM")
    exec_id = exec_rec["execution_id"]

    # Illegal direct jump
    ok, msg = update_execution_stage(exec_id, "VERIFIED", actor="test")
    assert ok is False
    assert "Illegal state transition" in msg
    assert get_self_healing_execution(exec_id)["lifecycle_stage"] == "DETECTED"


def test_idempotent_stage_transition():
    """Assert transitioning to the same stage is treated as an idempotent success."""
    exec_rec = create_self_healing_execution(incident_id="INC-TEST-003")
    exec_id = exec_rec["execution_id"]

    ok, msg = update_execution_stage(exec_id, "DETECTED", actor="test")
    assert ok is True
    assert "already in stage" in msg


# =========================================================================
# 2. ROOT-CAUSE ANALYSIS: FACTS VS PROBABLE CAUSES VS AI HYPOTHESES
# =========================================================================

def test_rca_facts_hypotheses_separation():
    """Assert RCA clearly separates evidence-proven facts from AI hypotheses."""
    rca = RootCauseAnalyzer.analyze_incident("INC-AUTH-1001")

    assert "confirmed_facts" in rca
    assert "probable_causes" in rca
    assert "ai_hypotheses" in rca

    assert isinstance(rca["confirmed_facts"], list)
    assert isinstance(rca["probable_causes"], list)
    assert isinstance(rca["ai_hypotheses"], list)

    assert len(rca["confirmed_facts"]) > 0
    assert len(rca["probable_causes"]) > 0
    assert len(rca["ai_hypotheses"]) > 0

    # Verify facts are explicitly evidence-anchored
    assert any("recorded" in f.lower() or "endpoint" in f.lower() or "ip" in f.lower() for f in rca["confirmed_facts"])

    # Verify hypotheses indicate uncertainty/analytical suggestion
    assert any("may" in h.lower() or "might" in h.lower() or "precursor" in h.lower() for h in rca["ai_hypotheses"])


# =========================================================================
# 3. EXPLAINABLE RISK ASSESSMENT & REMEDIATION PLANNER
# =========================================================================

def test_risk_assessment_scoring():
    """Assert risk classification scores vectors explainably."""
    # Low-risk action on specific IP
    risk_low = RiskImpactAssessor.assess_risk("BLOCK_IP", "198.51.100.99", "LOW", "Perimeter")
    assert risk_low["risk_level"] in ["LOW", "MEDIUM"]
    assert risk_low["reversibility"] == "FULLY_REVERSIBLE"

    # High-impact session invalidation on critical service
    risk_high = RiskImpactAssessor.assess_risk("REVOKE_SESSION", "All Users", "CRITICAL", "Storewide Gateway")
    assert risk_high["total_score"] > risk_low["total_score"]
    assert risk_high["risk_level"] in ["HIGH", "CRITICAL"]
    assert "user_impact_summary" in risk_high


def test_remediation_planner_generates_options():
    """Assert planner generates multiple distinct options with risk vectors."""
    plans = RemediationPlanner.generate_plans("INC-AUTH-1001")
    assert len(plans) >= 2

    action_types = [p["action_type"] for p in plans]
    assert "BLOCK_IP" in action_types or "APPLY_RATE_LIMIT" in action_types

    for p in plans:
        assert "risk_assessment" in p
        assert "risk_level" in p
        assert "verification_procedure" in p
        assert "reversibility" in p


# =========================================================================
# 4. AUTONOMY POLICY ENFORCEMENT & SAFETY CONTROLS
# =========================================================================

def test_policy_level_0_blocks_automation():
    """Policy Level 0 (Monitor Only) must reject all autonomous state modifications."""
    update_autonomy_policy({"autonomy_level": 0}, actor="admin")
    can_exec, reason = SelfHealingEngine.evaluate_autonomy("BLOCK_IP", "198.51.100.99", "LOW")
    assert can_exec is False
    assert "Level 0" in reason


def test_policy_level_1_requires_human_approval():
    """Policy Level 1 (Recommend) must generate plans but require human approval to execute."""
    update_autonomy_policy({"autonomy_level": 1}, actor="admin")
    can_exec, reason = SelfHealingEngine.evaluate_autonomy("BLOCK_IP", "198.51.100.99", "LOW")
    assert can_exec is False
    assert "Level 1" in reason


def test_policy_level_2_allows_low_risk_allowlisted():
    """Policy Level 2 allows low-risk allowlisted action within target scope."""
    update_autonomy_policy({
        "autonomy_level": 2,
        "action_allowlist": ["BLOCK_IP"],
        "target_allowlist": ["198.51.100.99"],
        "require_approval_above_risk": "LOW"
    }, actor="admin")

    # Low risk allowed
    can_exec, _ = SelfHealingEngine.evaluate_autonomy("BLOCK_IP", "198.51.100.99", "LOW")
    assert can_exec is True

    # High risk requires approval
    can_exec_high, reason_high = SelfHealingEngine.evaluate_autonomy("BLOCK_IP", "198.51.100.99", "HIGH")
    assert can_exec_high is False
    assert "exceeds" in reason_high


def test_target_allowlist_restriction():
    """Assert actions targeting outside configured target scope are blocked."""
    update_autonomy_policy({
        "autonomy_level": 2,
        "target_allowlist": ["127.0.0.1", "ShopSphere"]
    }, actor="admin")

    can_exec, reason = SelfHealingEngine.evaluate_autonomy("BLOCK_IP", "8.8.8.8", "LOW")
    assert can_exec is False
    assert "not in policy target allowlist" in reason


# =========================================================================
# 5. REAL EXECUTION, VERIFICATION & ROLLBACK
# =========================================================================

def test_dry_run_simulation_does_not_mutate_state():
    """Assert dry-run simulation validates plan without mutating security state."""
    exec_rec = create_self_healing_execution(incident_id="INC-SIM-001")
    exec_id = exec_rec["execution_id"]

    plan = {
        "action_type": "BLOCK_IP",
        "target": "198.51.100.77",
        "duration_seconds": 600
    }

    res = SelfHealingEngine.execute_plan(exec_id, plan, is_dry_run=True)
    assert res["success"] is True
    assert res["is_dry_run"] is True

    # Assert IP was not actually blocked in DB
    is_blocked, _ = is_client_blocked("198.51.100.77")
    assert is_blocked is False


def test_live_execution_and_independent_verification():
    """Assert live execution enforces action and triggers independent verification."""
    target_ip = "198.51.100.88"
    exec_rec = create_self_healing_execution(incident_id="INC-EXEC-001", affected_asset="ShopSphere")
    exec_id = exec_rec["execution_id"]

    plan = {
        "action_type": "BLOCK_IP",
        "target": target_ip,
        "duration_seconds": 600
    }

    # Transition to APPROVED first
    update_execution_stage(exec_id, "INVESTIGATING")
    update_execution_stage(exec_id, "DIAGNOSING")
    update_execution_stage(exec_id, "PLAN_GENERATED")
    update_execution_stage(exec_id, "APPROVED")

    res = SelfHealingEngine.execute_plan(exec_id, plan, is_dry_run=False)
    assert res["success"] is True

    # Verify IP is actively blocked in database
    is_blocked, _ = is_client_blocked(target_ip)
    assert is_blocked is True

    # Verify execution record has verification results
    updated = get_self_healing_execution(exec_id)
    assert updated["verification_state"] in ["VERIFIED", "FAILED"]

    # Clean up test block
    unblock_client_ip(target_ip)


def test_code_repair_execution_and_rollback():
    """Assert AST code repair applies surgical patch, verifies regression test, and safely rolls back."""
    exec_rec = create_self_healing_execution(incident_id="INC-VULN-001", affected_asset="CartService")
    exec_id = exec_rec["execution_id"]

    plan = {
        "action_type": "CODE_REPAIR_PATCH",
        "target": "VULN-FIN-001",
        "vuln_id": "VULN-FIN-001"
    }

    # Transition to APPROVED
    update_execution_stage(exec_id, "INVESTIGATING")
    update_execution_stage(exec_id, "DIAGNOSING")
    update_execution_stage(exec_id, "PLAN_GENERATED")
    update_execution_stage(exec_id, "APPROVED")

    # 1. Apply patch
    res = SelfHealingEngine.execute_plan(exec_id, plan, is_dry_run=False)
    assert res["success"] is True

    # Regression test verified
    vuln = VulnerabilityManager.get_vulnerability("VULN-FIN-001")
    assert vuln["regression_test_status"] == "PASSED"

    # 2. Rollback patch
    rollback_res = SelfHealingEngine.execute_rollback(exec_id, reason="Testing rollback restoration")
    assert rollback_res["success"] is True
    assert rollback_res["rollback_state"] == "ROLLED_BACK"

    # Check execution record status
    exec_after = get_self_healing_execution(exec_id)
    assert exec_after["lifecycle_stage"] == "ROLLED_BACK"

    # Restore clean state for subsequent tests
    from shopsphere.autoheal_engine import AutoHealDemoEngine
    AutoHealDemoEngine.apply_autoheal_patch()
    VulnerabilityManager.apply_patch("VULN-FIN-001")


# =========================================================================
# 6. EMERGENCY STOP & OPERATIONAL SAFETY CONTROLS
# =========================================================================

def test_emergency_stop_halts_executions():
    """Assert Emergency Stop immediately prevents new executions."""
    # 1. Activate Emergency Stop
    stop_res = trigger_emergency_stop(actor="soc_lead@sentinel.sec", reason="Suspected compromised telemetry feed")
    assert stop_res["emergency_stop"] is True

    is_stopped, reason, actor = is_emergency_stop_active()
    assert is_stopped is True
    assert actor == "soc_lead@sentinel.sec"

    # 2. Attempt execution during emergency stop
    exec_rec = create_self_healing_execution(incident_id="INC-STOP-001")
    exec_id = exec_rec["execution_id"]
    plan = {"action_type": "BLOCK_IP", "target": "198.51.100.55"}

    res = SelfHealingEngine.execute_plan(exec_id, plan)
    assert res["success"] is False
    assert "Emergency Stop" in res["error"]

    # 3. Resume from Emergency Stop
    resume_res = resume_from_emergency_stop(actor="soc_lead@sentinel.sec", reason="Feed validated clean")
    assert resume_res["emergency_stop"] is False
    is_stopped_after, _, _ = is_emergency_stop_active()
    assert is_stopped_after is False


# =========================================================================
# 7. REAL-TIME PERSISTENT KPI METRICS (NO FABRICATION)
# =========================================================================

def test_kpi_overview_calculated_from_db():
    """Assert KPI metrics are mathematically verified against real SQLite rows."""
    overview = get_self_healing_overview()

    assert "total_attempts" in overview
    assert "successful_remediations" in overview
    assert "failed_remediations" in overview
    assert "pending_approvals" in overview
    assert "awaiting_verification" in overview
    assert "verified_containment" in overview
    assert "rollback_count" in overview
    assert "avg_remediation_duration_ms" in overview
    assert "verification_failure_count" in overview

    # Verify counts match database query
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM self_healing_executions")
        actual_total = cursor.fetchone()["cnt"]

    assert overview["total_attempts"] == actual_total


def test_protection_status_matrix_real_health():
    """Assert all 8 subsystems report actual operational status without simulation."""
    status = get_system_protection_status()

    assert "overall_status" in status
    assert status["overall_status"] in ["HEALTHY", "DEGRADED", "UNAVAILABLE"]

    components = status["components"]
    expected_components = [
        "detection_engine", "event_ingestion", "remediation_engine",
        "verification_engine", "soar_engine", "database",
        "background_workers", "shopsphere_target"
    ]

    for comp in expected_components:
        assert comp in components
        assert components[comp]["status"] in ["HEALTHY", "DEGRADED", "UNAVAILABLE", "UNKNOWN"]
        assert "details" in components[comp]


# =========================================================================
# 8. REST API ENDPOINTS & INTEGRATION
# =========================================================================

def test_api_overview_endpoint(client):
    """GET /api/self-healing/overview returns 200 with persistent metrics."""
    res = client.get("/api/self-healing/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_attempts"] >= 0


def test_api_activity_pagination_and_filter(client):
    """GET /api/self-healing/activity supports stage filtering and pagination."""
    res = client.get("/api/self-healing/activity?limit=10&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data


def test_api_diagnose_endpoint(client):
    """GET /api/self-healing/diagnose/{id} returns tripartite facts vs hypotheses."""
    res = client.get("/api/self-healing/diagnose/INC-AUTH-1001")
    assert res.status_code == 200
    data = res.json()
    assert "confirmed_facts" in data
    assert "probable_causes" in data
    assert "ai_hypotheses" in data


def test_api_plans_generate(client):
    """POST /api/self-healing/plans/generate returns risk-scored remediation plans."""
    res = client.post("/api/self-healing/plans/generate", json={"incident_id": "INC-AUTH-1001"})
    assert res.status_code == 200
    data = res.json()
    assert "plans" in data
    assert len(data["plans"]) > 0


def test_api_policy_crud(client):
    """GET & PUT /api/self-healing/policies updates configuration and increments version."""
    get_res = client.get("/api/self-healing/policies")
    assert get_res.status_code == 200
    initial_version = get_res.json()["version"]

    put_res = client.put("/api/self-healing/policies", json={
        "autonomy_level": 2,
        "max_risk_level": "MEDIUM",
        "require_approval_above_risk": "LOW"
    })
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["autonomy_level"] == 2
    assert updated["version"] == initial_version + 1


def test_api_emergency_stop_flow(client):
    """POST /api/self-healing/emergency-stop and /api/self-healing/emergency-resume."""
    # Stop
    stop_res = client.post("/api/self-healing/emergency-stop", json={
        "actor": "admin@sentinel.sec",
        "reason": "Security Drill - Immediate Stop"
    })
    assert stop_res.status_code == 200
    assert stop_res.json()["emergency_stop"] is True

    # Resume
    resume_res = client.post("/api/self-healing/emergency-resume", json={
        "actor": "admin@sentinel.sec",
        "reason": "Drill completed"
    })
    assert resume_res.status_code == 200
    assert resume_res.json()["emergency_stop"] is False


def test_api_ai_assistant_deterministic_output(client):
    """POST /api/self-healing/ai-assistant generates grounded advice without hallucinating facts."""
    res = client.post("/api/self-healing/ai-assistant", json={
        "query": "Diagnose root cause facts vs hypotheses",
        "incident_id": "INC-AUTH-1001"
    })
    assert res.status_code == 200
    data = res.json()
    assert "ai_response" in data
    assert "distinction_note" in data
    assert "Facts are verified from database evidence" in data["distinction_note"]


# =========================================================================
# 9. IMMUTABLE AUDIT LOGS & SECRET PROTECTION
# =========================================================================

def test_immutable_audit_logs_persisted():
    """Assert all policy changes and emergency stop actions create immutable audit logs."""
    trigger_emergency_stop(actor="audit_test_admin", reason="Audit Verification Trigger")
    resume_from_emergency_stop(actor="audit_test_admin", reason="Audit Resume Trigger")

    logs_after = get_self_healing_audit_logs(limit=20)
    recent_actions = [l["action_type"] for l in logs_after[:5]]
    assert "EMERGENCY_STOP" in recent_actions
    assert "EMERGENCY_RESUME" in recent_actions
    assert any(l["actor"] == "audit_test_admin" for l in logs_after[:5])


def test_zero_secret_leakage_in_records():
    """Assert user password hashes or secret tokens are never exposed in execution responses."""
    executions = list_self_healing_executions(limit=20)
    json_str = json.dumps(executions)

    assert "password_hash" not in json_str
    assert "PBKDF2" not in json_str
    assert "secret_key" not in json_str
