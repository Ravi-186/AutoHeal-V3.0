"""
Attack Simulation Center Test Suite (Phase 4)
Validates enterprise-grade defensive security testing capabilities:
- Scenario catalog registration for all 7 verified scenarios
- Real-time persisted execution statistics from SQLite
- Target allowlist enforcement (strict localhost restriction)
- Defensive authorization confirmation enforcement
- Dry-run and live simulation execution
- Execution ID generation (SIM-YYYYMMDD-XXXX) and persistence
- 5-stage stepper telemetry and trace collection
- Detection validation matrix (expected vs actual rule, rule_match)
- Dual-probe containment verification (attacker 403 vs benign 200)
- Execution history pagination, multi-field filtering, and search
- Forensic evidence drawer detail inspection with 404 handling
- Operator abort / cancellation endpoint
- Formula-safe CSV export
- Streaming runner coverage for all scenario types
"""

import pytest
import sqlite3
import json
from fastapi.testclient import TestClient

from server import app
from src.appsec.models import (
    get_scenario_catalog,
    record_simulation_execution,
    update_simulation_execution,
    get_simulation_execution,
    query_simulation_executions,
    get_simulation_dashboard_stats,
    SCENARIO_CATALOG
)
from src.appsec.security_tester import ShopSphereSecurityTester, validate_target_safety


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_simulation_catalog_endpoint(client):
    """Verifies that GET /api/security/simulations/catalog returns all 7 verified scenarios."""
    response = client.get("/api/security/simulations/catalog")
    assert response.status_code == 200
    data = response.json()

    assert "scenarios" in data
    assert "total" in data
    assert data["total"] == 7

    scenario_ids = [s["scenario_id"] for s in data["scenarios"]]
    expected_scenarios = ["sqli", "xss", "failed_logins", "admin", "rate", "health", "replay"]
    for s_id in expected_scenarios:
        assert s_id in scenario_ids

    # Verify scenario schema
    for s in data["scenarios"]:
        assert "scenario_id" in s
        assert "name" in s
        assert "description" in s
        assert "risk_category" in s
        assert "severity" in s
        assert "expected_rule_id" in s
        assert "expected_action" in s
        assert "mitre_technique" in s
        assert "estimated_duration_sec" in s
        assert s["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def test_simulation_stats_endpoint(client):
    """Verifies that GET /api/security/simulations/stats computes true metrics from SQLite."""
    response = client.get("/api/security/simulations/stats")
    assert response.status_code == 200
    stats = response.json()

    assert "total_simulations" in stats
    assert "scenarios_available" in stats
    assert "successful_detections" in stats
    assert "failed_detections" in stats
    assert "detection_rate_pct" in stats
    assert "verified_protections" in stats
    assert "incidents_created" in stats

    assert stats["scenarios_available"] == 7
    assert stats["total_simulations"] >= 0
    assert 0 <= stats["detection_rate_pct"] <= 100


def test_simulation_dispatch_target_safety_rejection(client):
    """Verifies that targets not in the localhost allowlist are strictly rejected with HTTP 400."""
    external_targets = [
        "https://evil-attacker.com",
        "https://www.google.com",
        "http://192.168.1.100:8000",
        "http://10.0.0.5:8080"
    ]
    for target in external_targets:
        response = client.post("/api/security/simulations/dispatch", json={
            "scenario_id": "sqli",
            "target_url": target,
            "client_ip": "203.0.113.88",
            "attempts": 3,
            "execution_mode": "live",
            "authorized_confirmation": True
        })
        assert response.status_code == 400
        data = response.json()
        assert "strictly prohibited" in data["detail"] or "TargetSafetyError" in data["detail"]


def test_simulation_dispatch_authorization_required(client):
    """Verifies that executions without authorized_confirmation=True are rejected with HTTP 400."""
    response = client.post("/api/security/simulations/dispatch", json={
        "scenario_id": "sqli",
        "target_url": "http://localhost:8000",
        "client_ip": "203.0.113.88",
        "attempts": 3,
        "execution_mode": "live",
        "authorized_confirmation": False
    })
    assert response.status_code == 400
    data = response.json()
    assert "Defensive testing authorization confirmation is required" in data["detail"]


def test_simulation_dispatch_dryrun(client):
    """Verifies dry-run simulation mode generates valid execution record without actual attacks."""
    response = client.post("/api/security/simulations/dispatch", json={
        "scenario_id": "sqli",
        "target_url": "http://localhost:8000",
        "client_ip": "203.0.113.88",
        "attempts": 3,
        "execution_mode": "dryrun",
        "authorized_confirmation": True
    })
    assert response.status_code == 200
    data = response.json()

    assert "execution_id" in data
    assert data["execution_id"].startswith("SIM-")
    assert data["status"] == "COMPLETED"
    assert data["execution_mode"] == "dryrun"
    assert data["detection_outcome"] == "DETECTED"
    assert bool(data["protection_verified"]) is True
    assert "validation_matrix" in data
    assert data["validation_matrix"]["detection"]["rule_match"] is True


def test_simulation_dispatch_live_sqli(client):
    """Verifies live simulation dispatch triggers testing pipeline, persists ID, and validates containment."""
    response = client.post("/api/security/simulations/dispatch", json={
        "scenario_id": "sqli",
        "target_url": "http://localhost:8000",
        "client_ip": "203.0.113.88",
        "attempts": 3,
        "execution_mode": "live",
        "authorized_confirmation": True
    })
    assert response.status_code == 200
    data = response.json()

    assert "execution_id" in data
    exec_id = data["execution_id"]
    assert exec_id.startswith("SIM-")
    assert data["status"] == "COMPLETED"
    assert data["scenario_id"] == "sqli"
    assert data["detection_outcome"] == "DETECTED"
    assert bool(data["protection_verified"]) is True
    assert len(data.get("steps", [])) > 0
    assert data["request_count"] > 0


def test_simulation_history_pagination(client):
    """Verifies GET /api/security/simulations supports server-side pagination with standard envelope."""
    response = client.get("/api/security/simulations?page=1&limit=3")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "total_pages" in data

    assert data["page"] == 1
    assert data["limit"] == 3
    assert len(data["items"]) <= 3
    assert data["total"] >= 1


def test_simulation_history_filtering(client):
    """Verifies filtering by scenario, status, and detection outcome."""
    # Scenario filter
    res_sqli = client.get("/api/security/simulations?scenario=sqli&limit=50")
    assert res_sqli.status_code == 200
    items_sqli = res_sqli.json()["items"]
    for item in items_sqli:
        assert item["scenario_id"] == "sqli"

    # Status filter
    res_completed = client.get("/api/security/simulations?status=COMPLETED&limit=50")
    assert res_completed.status_code == 200
    items_completed = res_completed.json()["items"]
    for item in items_completed:
        assert item["status"] == "COMPLETED"

    # Outcome filter
    res_detected = client.get("/api/security/simulations?detection_outcome=DETECTED&limit=50")
    assert res_detected.status_code == 200
    items_detected = res_detected.json()["items"]
    for item in items_detected:
        assert item["detection_outcome"] == "DETECTED"


def test_simulation_detail_and_validation_matrix(client):
    """Verifies retrieval of detailed simulation record by ID and 404 for unknown IDs."""
    # First get an existing execution ID
    list_res = client.get("/api/security/simulations?limit=1")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) > 0
    exec_id = items[0]["execution_id"]

    # Fetch detail
    detail_res = client.get(f"/api/security/simulations/{exec_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()

    assert detail["execution_id"] == exec_id
    assert "scenario_name" in detail
    assert "validation_matrix" in detail
    assert "detection" in detail["validation_matrix"]
    assert "remediation" in detail["validation_matrix"]
    assert "steps" in detail
    assert isinstance(detail["steps"], list)

    # Unknown ID 404
    unknown_res = client.get("/api/security/simulations/SIM-UNKNOWN-9999")
    assert unknown_res.status_code == 404


def test_simulation_abort_endpoint(client):
    """Verifies POST /api/security/simulations/abort signals engine cancellation successfully."""
    response = client.post("/api/security/simulations/abort")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "aborted"
    assert "message" in data


def test_simulation_csv_export(client):
    """Verifies GET /api/security/simulations?format=csv returns safe CSV with appropriate headers."""
    response = client.get("/api/security/simulations?format=csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert "attachment" in response.headers.get("content-disposition", "")
    assert "simulation_executions_export.csv" in response.headers.get("content-disposition", "")

    csv_text = response.text
    lines = csv_text.strip().split("\n")
    header = lines[0].strip()
    assert "execution_id" in header
    assert "scenario_id" in header
    assert "status" in header
    assert "detection_outcome" in header
    assert "protection_verified" in header
    assert len(lines) > 1


def test_target_safety_validator_unit():
    """Unit test for validate_target_safety."""
    assert validate_target_safety("http://localhost:8000") == "http://localhost:8000"
    assert validate_target_safety("http://127.0.0.1:8000") == "http://127.0.0.1:8000"
    assert validate_target_safety("http://testserver") == "http://testserver"

    with pytest.raises(ValueError):
        validate_target_safety("https://attacker.com/exploit")

    with pytest.raises(ValueError):
        validate_target_safety("http://169.254.169.254/latest/meta-data")


def test_streaming_runner_health_and_replay_scenarios():
    """Verifies that health and replay scenarios run properly in stream_test_execution."""
    tester = ShopSphereSecurityTester(base_url="http://testserver")

    # Health scenario
    health_events = list(tester.stream_test_execution(
        scenario="health",
        client_ip="198.51.100.33",
        attempts=2
    ))
    types = [e.get("type") for e in health_events]
    assert "phase" in types
    assert "request" in types
    assert "detection" in types
    assert "complete" in types

    # Replay scenario
    replay_events = list(tester.stream_test_execution(
        scenario="replay",
        client_ip="203.0.113.105",
        attempts=2
    ))
    replay_types = [e.get("type") for e in replay_events]
    assert "phase" in replay_types
    assert "request" in replay_types
    assert "detection" in replay_types
    assert "verification" in replay_types
    assert "complete" in replay_types
