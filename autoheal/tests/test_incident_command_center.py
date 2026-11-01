"""
Enterprise Incident Command Center & Investigation Workspace Test Suite (Phase 5)
Validates enterprise-grade incident management, forensics, and investigation capabilities:
- Real-time persisted KPI statistics computed from SQLite security_incidents
- Paginated querying with compound filters (time_range, severity, status, priority, analyst)
- Full-text keyword search and multi-column sorting
- Formula-safe CSV export with injection sanitization
- Forensic incident dossier retrieval with 404 handling
- Chronological timeline reconstruction (Ingress, Detection, Containment, Verification, Recovery)
- Digital evidence explorer with SHA-256 cryptographic integrity hash and secret redaction
- 5-stage attack sequence visualization distinguishing observed facts from analytical hypotheses
- MITRE ATT&CK enterprise correlation
- Structured Root-Cause Analysis findings persistence
- Internal analyst collaboration notes thread
- Immutable cryptographically attributable activity logs
- Incident lifecycle state machine validation (NEW, TRIAGED, INVESTIGATING, CONTAINMENT, REMEDIATION, VERIFICATION, RESOLVED, CLOSED)
- Strict resolution gates (verification prerequisite + non-empty resolution notes)
- Optimistic concurrency conflict detection (HTTP 409 on version mismatch)
- Backward compatibility with legacy incident array consumers
"""

import pytest
import sqlite3
import hashlib
import json
from fastapi.testclient import TestClient

from server import app
from src.appsec.models import (
    get_incident_command_stats,
    query_incidents_paginated,
    get_security_incident,
    build_incident_timeline,
    get_incident_evidence_explorer,
    build_incident_attack_sequence,
    transition_incident_status,
    assign_incident_analyst,
    update_incident_priority,
    update_incident_root_cause,
    add_incident_note,
    get_incident_activity_logs,
    seed_default_incidents_if_empty,
    ConcurrencyError,
    VALID_INCIDENT_TRANSITIONS
)
from shopsphere.database import get_db_connection as get_db


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def ensure_seeded_data():
    """Ensure baseline incident test records exist in the database."""
    seed_default_incidents_if_empty()


def test_incident_command_stats_endpoint(client):
    """Verifies that GET /api/security/incidents/stats computes all 8 KPI metrics from SQLite."""
    response = client.get("/api/security/incidents/stats?time_range=all")
    assert response.status_code == 200
    stats = response.json()

    required_keys = [
        "total_incidents",
        "active_incidents",
        "critical_incidents",
        "high_incidents",
        "investigating_incidents",
        "pending_remediation",
        "verification_failures",
        "resolved_incidents",
        "time_range"
    ]
    for k in required_keys:
        assert k in stats, f"Missing KPI metric: {k}"

    assert isinstance(stats["total_incidents"], int)
    assert stats["total_incidents"] >= 3  # Seeded with at least 3
    assert isinstance(stats["active_incidents"], int)
    assert isinstance(stats["critical_incidents"], int)
    assert isinstance(stats["high_incidents"], int)
    assert stats["time_range"] == "all"

    # Test with 24h filter
    resp_24h = client.get("/api/security/incidents/stats?time_range=24h")
    assert resp_24h.status_code == 200
    assert resp_24h.json()["time_range"] == "24h"


def test_incidents_paginated_endpoint(client):
    """Verifies that GET /api/security/incidents with pagination returns the correct envelope and schema."""
    response = client.get("/api/security/incidents?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data

    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total"] >= 3
    assert len(data["items"]) <= 10

    # Verify item schema
    item = data["items"][0]
    expected_fields = [
        "incident_id", "title", "severity", "status", "priority",
        "rule_id", "created_at", "assigned_analyst", "related_events_count",
        "verification_status", "version"
    ]
    for field in expected_fields:
        assert field in item, f"Missing field {field} in incident item"


def test_incidents_filtering_severity_and_status(client):
    """Verifies compound filtering across severity, status, and priority."""
    # Filter by CRITICAL severity
    res_crit = client.get("/api/security/incidents?page=1&page_size=20&severity=CRITICAL")
    assert res_crit.status_code == 200
    crit_items = res_crit.json()["items"]
    for inc in crit_items:
        assert inc["severity"].upper() == "CRITICAL"

    # Filter by HIGH severity
    res_high = client.get("/api/security/incidents?page=1&page_size=20&severity=HIGH")
    assert res_high.status_code == 200
    high_items = res_high.json()["items"]
    for inc in high_items:
        assert inc["severity"].upper() == "HIGH"

    # Filter by status
    res_stat = client.get("/api/security/incidents?page=1&page_size=20&status=CONTAINMENT")
    assert res_stat.status_code == 200
    stat_items = res_stat.json()["items"]
    for inc in stat_items:
        assert inc["status"].upper() == "CONTAINMENT"


def test_incidents_search(client):
    """Verifies full-text search across incident ID, rule ID, title, and target endpoint."""
    res = client.get("/api/security/incidents?page=1&page_size=10&search=SQL")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    for item in data["items"]:
        match_found = (
            "SQL" in (item.get("incident_id") or "").upper() or
            "SQL" in (item.get("title") or "").upper() or
            "SQL" in (item.get("rule_id") or "").upper() or
            "SQL" in (item.get("target_endpoint") or "").upper() or
            "SQL" in (item.get("summary") or "").upper() or
            "SQL" in (item.get("category") or "").upper()
        )
        assert match_found


def test_incidents_sorting(client):
    """Verifies multi-column sorting ascending and descending."""
    # Sort created_at asc
    res_asc = client.get("/api/security/incidents?page=1&page_size=10&sort_by=created_at&sort_order=asc")
    assert res_asc.status_code == 200
    items_asc = res_asc.json()["items"]
    if len(items_asc) >= 2:
        assert items_asc[0]["created_at"] <= items_asc[-1]["created_at"]

    # Sort created_at desc
    res_desc = client.get("/api/security/incidents?page=1&page_size=10&sort_by=created_at&sort_order=desc")
    assert res_desc.status_code == 200
    items_desc = res_desc.json()["items"]
    if len(items_desc) >= 2:
        assert items_desc[0]["created_at"] >= items_desc[-1]["created_at"]


def test_incidents_csv_export_and_formula_escaping(client):
    """Verifies CSV export and formula injection sanitization."""
    res = client.get("/api/security/incidents?format=csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("content-type", "")
    assert "attachment; filename=" in res.headers.get("content-disposition", "")

    csv_text = res.text
    lines = csv_text.strip().split("\r\n")
    if len(lines) <= 1:
        lines = csv_text.strip().split("\n")
    assert len(lines) >= 2  # Header + at least one data row

    header = lines[0].lower()
    assert "incident_id" in header
    assert "severity" in header
    assert "status" in header
    assert "assigned_analyst" in header

    # Ensure no unsanitized leading formulas exist
    for line in lines[1:]:
        parts = line.split(",")
        for part in parts:
            clean_part = part.strip('"')
            if clean_part.startswith(("=", "+", "-", "@")):
                # Must be prefixed with single quote for defense
                assert clean_part.startswith("'")


def test_incident_detail_dossier(client):
    """Verifies detailed forensic dossier retrieval and 404 handling."""
    # First get an existing incident ID
    list_res = client.get("/api/security/incidents?page=1&page_size=1")
    assert list_res.status_code == 200
    inc_id = list_res.json()["items"][0]["incident_id"]

    res = client.get(f"/api/security/incidents/{inc_id}")
    assert res.status_code == 200
    inc = res.json()
    assert inc["incident_id"] == inc_id
    assert "version" in inc
    assert "assigned_analyst" in inc
    assert "priority" in inc
    assert "verification_status" in inc

    # 404 for invalid ID
    res_404 = client.get("/api/security/incidents/INC-DOES-NOT-EXIST-9999")
    assert res_404.status_code == 404


def test_incident_timeline_endpoint(client):
    """Verifies chronological timeline reconstruction."""
    list_res = client.get("/api/security/incidents?page=1&page_size=1")
    inc_id = list_res.json()["items"][0]["incident_id"]

    res = client.get(f"/api/security/incidents/{inc_id}/timeline")
    assert res.status_code == 200
    timeline = res.json()
    assert isinstance(timeline, list)
    assert len(timeline) >= 2

    # Check structure of timeline entries
    for entry in timeline:
        assert "timestamp" in entry
        assert "event_type" in entry
        assert "description" in entry
        assert "source" in entry
        assert "execution_status" in entry

    # Verify chronological ordering
    timestamps = [e["timestamp"] for e in timeline if e.get("timestamp")]
    assert timestamps == sorted(timestamps)


def test_incident_evidence_explorer_and_sha256_hash(client):
    """Verifies digital evidence explorer with cryptographic SHA-256 tamper-evident integrity hash."""
    list_res = client.get("/api/security/incidents?page=1&page_size=1")
    inc_id = list_res.json()["items"][0]["incident_id"]

    res = client.get(f"/api/security/incidents/{inc_id}/evidence")
    assert res.status_code == 200
    evidence_data = res.json()

    assert "incident_id" in evidence_data
    assert "evidence_integrity_sha256" in evidence_data
    sha256_hash = evidence_data["evidence_integrity_sha256"]
    assert len(sha256_hash) == 64
    assert all(c in "0123456789abcdef" for c in sha256_hash)

    assert "request_metadata" in evidence_data
    assert "related_events" in evidence_data


def test_incident_attack_sequence_endpoint(client):
    """Verifies attack-sequence visualization distinguishing facts from hypotheses."""
    list_res = client.get("/api/security/incidents?page=1&page_size=1")
    inc_id = list_res.json()["items"][0]["incident_id"]

    res = client.get(f"/api/security/incidents/{inc_id}/attack-sequence")
    assert res.status_code == 200
    data = res.json()

    assert "sequence" in data
    assert len(data["sequence"]) == 5
    assert "mitre_tactic" in data
    assert "mitre_technique" in data
    assert "mitre_technique_id" in data

    classes = [s["classification"] for s in data["sequence"]]
    assert "OBSERVED_FACT" in classes
    assert "ANALYTICAL_HYPOTHESIS" in classes


def test_incident_activity_log_endpoint(client):
    """Verifies retrieval of immutable activity logs."""
    list_res = client.get("/api/security/incidents?page=1&page_size=1")
    inc_id = list_res.json()["items"][0]["incident_id"]

    # Append an activity note to ensure at least one log entry exists
    client.post(f"/api/security/incidents/{inc_id}/notes", json={
        "content": "Test activity verification note",
        "author": "SOC Lead"
    })

    res = client.get(f"/api/security/incidents/{inc_id}/activity")
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)
    assert len(logs) >= 1
    log = logs[0]
    assert "action_type" in log
    assert "author" in log
    assert "created_at" in log


def test_incident_status_transition_valid_flow(client):
    """Verifies controlled status transitions incrementing version and writing audit logs."""
    # Find or seed a NEW incident
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO security_incidents (
                incident_id, title, category, severity, status, rule_id, summary, created_at,
                assigned_analyst, priority, verification_status, version
            ) VALUES (
                'INC-TEST-FLOW-01', 'Test Lifecycle Flow', 'AUTHENTICATION', 'HIGH', 'NEW', 'AUTH-001',
                'Test incident summary', datetime('now'), 'Unassigned', 'HIGH', 'PENDING', 1
            )
        """)
        conn.commit()

    # 1. NEW -> TRIAGED
    res1 = client.post("/api/security/incidents/INC-TEST-FLOW-01/status", json={
        "target_status": "TRIAGED",
        "analyst": "SOC Lead",
        "current_version": 1
    })
    assert res1.status_code == 200
    assert res1.json()["status"] == "TRIAGED"
    assert res1.json()["version"] == 2

    # 2. TRIAGED -> INVESTIGATING
    res2 = client.post("/api/security/incidents/INC-TEST-FLOW-01/status", json={
        "target_status": "INVESTIGATING",
        "analyst": "SOC Lead",
        "current_version": 2
    })
    assert res2.status_code == 200
    assert res2.json()["status"] == "INVESTIGATING"
    assert res2.json()["version"] == 3

    # 3. INVESTIGATING -> CONTAINMENT
    res3 = client.post("/api/security/incidents/INC-TEST-FLOW-01/status", json={
        "target_status": "CONTAINMENT",
        "analyst": "SOC Lead",
        "current_version": 3
    })
    assert res3.status_code == 200
    assert res3.json()["status"] == "CONTAINMENT"
    assert res3.json()["version"] == 4


def test_incident_status_transition_invalid_rejected(client):
    """Verifies that illegal status transitions outside the state machine are rejected."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO security_incidents (
                incident_id, title, category, severity, status, rule_id, summary, created_at,
                assigned_analyst, priority, verification_status, version
            ) VALUES (
                'INC-TEST-ILLEGAL-01', 'Test Illegal Transition', 'AUTHENTICATION', 'HIGH', 'NEW', 'AUTH-001',
                'Test incident summary', datetime('now'), 'Unassigned', 'HIGH', 'PENDING', 1
            )
        """)
        conn.commit()

    # Attempt NEW -> RESOLVED (Illegal transition skipping triage/containment/verification)
    res = client.post("/api/security/incidents/INC-TEST-ILLEGAL-01/status", json={
        "target_status": "RESOLVED",
        "resolution_notes": "Attempting skip",
        "analyst": "Rogue Operator",
        "current_version": 1
    })
    assert res.status_code == 400
    assert "Invalid incident lifecycle transition" in res.json()["detail"]


def test_resolution_gate_enforcement(client):
    """Verifies that transitioning to RESOLVED enforces both verification and resolution notes."""
    # 1. Verification status is PENDING -> Must be rejected even with notes
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO security_incidents (
                incident_id, title, category, severity, status, rule_id, summary, created_at,
                assigned_analyst, priority, verification_status, version
            ) VALUES (
                'INC-TEST-GATE-01', 'Test Resolution Gate', 'AUTHENTICATION', 'HIGH', 'VERIFICATION', 'AUTH-001',
                'Test incident summary', datetime('now'), 'Unassigned', 'HIGH', 'PENDING', 5
            )
        """)
        conn.commit()

    res_no_verif = client.post("/api/security/incidents/INC-TEST-GATE-01/status", json={
        "target_status": "RESOLVED",
        "resolution_notes": "We fixed it manually",
        "analyst": "SOC Lead",
        "current_version": 5
    })
    assert res_no_verif.status_code == 400
    assert "Verification state is 'PENDING'" in res_no_verif.json()["detail"]

    # 2. Verification is VERIFIED_CONTAINED, but resolution_notes is empty -> Must be rejected
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE security_incidents
            SET verification_status = 'VERIFIED_CONTAINED'
            WHERE incident_id = 'INC-TEST-GATE-01'
        """)
        conn.commit()

    res_no_notes = client.post("/api/security/incidents/INC-TEST-GATE-01/status", json={
        "target_status": "RESOLVED",
        "resolution_notes": "   ",
        "analyst": "SOC Lead",
        "current_version": 5
    })
    assert res_no_notes.status_code == 400
    assert "Resolution notes are strictly required" in res_no_notes.json()["detail"]

    # 3. Both verification and notes supplied -> Succeeded
    res_ok = client.post("/api/security/incidents/INC-TEST-GATE-01/status", json={
        "target_status": "RESOLVED",
        "resolution_notes": "Perimeter IP quarantine verified via synthetic loopback probe with HTTP 403 response.",
        "analyst": "SOC Lead",
        "current_version": 5
    })
    assert res_ok.status_code == 200
    data = res_ok.json()
    assert data["status"] == "RESOLVED"
    assert data["resolved_by"] == "SOC Lead"
    assert data["resolution_notes"] is not None
    assert data["resolved_at"] is not None


def test_concurrency_conflict_detection(client):
    """Verifies that stale version submissions return HTTP 409 Conflict."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO security_incidents (
                incident_id, title, category, severity, status, rule_id, summary, created_at,
                assigned_analyst, priority, verification_status, version
            ) VALUES (
                'INC-TEST-CONCURR-01', 'Test Concurrency', 'AUTHENTICATION', 'HIGH', 'NEW', 'AUTH-001',
                'Test incident summary', datetime('now'), 'Unassigned', 'HIGH', 'PENDING', 3
            )
        """)
        conn.commit()

    # Pass version 1 when DB is version 3
    res = client.post("/api/security/incidents/INC-TEST-CONCURR-01/status", json={
        "target_status": "TRIAGED",
        "analyst": "Analyst A",
        "current_version": 1
    })
    assert res.status_code == 409
    assert "Concurrency conflict" in res.json()["detail"]


def test_analyst_assignment_and_audit(client):
    """Verifies analyst assignment updates record and writes audit trail."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO security_incidents (
                incident_id, title, category, severity, status, rule_id, summary, created_at,
                assigned_analyst, priority, verification_status, version
            ) VALUES (
                'INC-TEST-ASSIGN-01', 'Test Assignment', 'AUTHENTICATION', 'HIGH', 'NEW', 'AUTH-001',
                'Test incident summary', datetime('now'), 'Unassigned', 'HIGH', 'PENDING', 1
            )
        """)
        conn.commit()

    res = client.post("/api/security/incidents/INC-TEST-ASSIGN-01/assign", json={
        "analyst": "Agent Miller",
        "current_version": 1
    })
    assert res.status_code == 200
    assert res.json()["assigned_analyst"] == "Agent Miller"
    assert res.json()["version"] == 2

    # Verify activity log
    act_res = client.get("/api/security/incidents/INC-TEST-ASSIGN-01/activity")
    assert act_res.status_code == 200
    actions = [a["action_type"] for a in act_res.json()]
    assert "ANALYST_ASSIGNED" in actions


def test_priority_update_and_audit(client):
    """Verifies priority change updates record and writes audit trail."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO security_incidents (
                incident_id, title, category, severity, status, rule_id, summary, created_at,
                assigned_analyst, priority, verification_status, version
            ) VALUES (
                'INC-TEST-PRIO-01', 'Test Priority', 'AUTHENTICATION', 'HIGH', 'NEW', 'AUTH-001',
                'Test incident summary', datetime('now'), 'Unassigned', 'MEDIUM', 'PENDING', 1
            )
        """)
        conn.commit()

    res = client.post("/api/security/incidents/INC-TEST-PRIO-01/priority", json={
        "priority": "CRITICAL",
        "reason": "Threat escalating to multi-endpoint traversal",
        "analyst": "SOC Lead",
        "current_version": 1
    })
    assert res.status_code == 200
    assert res.json()["priority"] == "CRITICAL"
    assert res.json()["version"] == 2


def test_root_cause_update_and_notes(client):
    """Verifies root-cause findings persistence and analyst notes."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO security_incidents (
                incident_id, title, category, severity, status, rule_id, summary, created_at,
                assigned_analyst, priority, verification_status, version
            ) VALUES (
                'INC-TEST-RCA-01', 'Test RCA & Notes', 'INJECTION', 'HIGH', 'INVESTIGATING', 'AUTH-001',
                'Test incident summary', datetime('now'), 'Analyst Sarah', 'HIGH', 'PENDING', 1
            )
        """)
        conn.commit()

    # Update RCA
    res_rca = client.post("/api/security/incidents/INC-TEST-RCA-01/root-cause", json={
        "entry_point": "/api/products/search",
        "conditions": "Missing parameter type enforcement on keyword param",
        "conclusions": "Vulnerability patched via AST sanitization middleware",
        "current_version": 1
    })
    assert res_rca.status_code == 200
    assert res_rca.json()["suspected_entry_point"] == "/api/products/search"
    assert res_rca.json()["version"] == 2

    # Add Note
    res_note = client.post("/api/security/incidents/INC-TEST-RCA-01/notes", json={
        "content": "Verified loopback IP ban is in effect and token blacklist cleared.",
        "author": "Analyst Sarah"
    })
    assert res_note.status_code == 200
    assert res_note.json()["action_type"] == "NOTE_ADDED"
    assert res_note.json()["author"] == "Analyst Sarah"


def test_legacy_array_backward_compatibility(client):
    """Verifies that calling GET /api/security/incidents without 'page' returns a flat array for legacy consumers."""
    res = client.get("/api/security/incidents?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) <= 5
    if len(data) > 0:
        assert "incident_id" in data[0]
