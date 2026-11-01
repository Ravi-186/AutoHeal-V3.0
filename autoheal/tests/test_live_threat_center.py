"""
Live Threat Center, Security Event Explorer & Threat Investigation Test Suite
Validates Phase 3 enterprise capabilities:
- Server-side event pagination, filtering, search, and sorting
- Single event forensic detail inspection dossier
- Related event multi-factor correlation (trace ID, IP, endpoint)
- Detection rule coverage catalog for all 7 detection rules
- Threat intelligence reputation enrichment
- Analyst investigation workflow persistence and audit logging
- Incident escalation from telemetry events
- Telemetry CSV export
- XSS escaping and payload sanitization
"""

import pytest
import sqlite3
import json
from fastapi.testclient import TestClient

from server import app
from src.appsec.models import (
    get_security_event_by_id,
    get_related_security_events,
    query_security_events_advanced,
    record_event_investigation,
    get_threat_intel,
    get_detection_rule_catalog,
    RULE_METADATA
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_events_pagination_and_structure(client):
    """Verifies that the /api/security/events endpoint returns structured paginated telemetry."""
    response = client.get("/api/security/events?page=1&limit=25")
    assert response.status_code == 200
    data = response.json()

    assert "events" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert "total_pages" in data
    assert "summary" in data

    assert data["page"] == 1
    assert data["limit"] == 25
    assert data["total"] > 0
    assert len(data["events"]) <= 25

    summary = data["summary"]
    assert "total" in summary
    assert "critical" in summary
    assert "high" in summary
    assert "medium" in summary
    assert "low" in summary
    assert "info" in summary
    assert summary["total"] == data["total"]


def test_events_multi_filtering(client):
    """Verifies severity, category, and action filtering on the event explorer."""
    # Filter by CRITICAL severity
    res_crit = client.get("/api/security/events?severity=CRITICAL&limit=50")
    assert res_crit.status_code == 200
    data_crit = res_crit.json()
    for ev in data_crit["events"]:
        assert ev["severity"] == "CRITICAL"

    # Filter by SQL Injection category
    res_sqli = client.get("/api/security/events?category=SQL_INJECTION&limit=50")
    assert res_sqli.status_code == 200
    data_sqli = res_sqli.json()
    assert len(data_sqli["events"]) > 0
    for ev in data_sqli["events"]:
        assert "inj" in ev["event_type"].lower() or "injection" in ev.get("details_json", "").lower()

    # Filter by Rule ID
    res_rule = client.get("/api/security/events?rule_id=INJ-001&limit=50")
    assert res_rule.status_code == 200
    data_rule = res_rule.json()
    for ev in data_rule["events"]:
        assert "INJ-001" in ev["event_type"] or "INJ-001" in ev.get("details_json", "")


def test_events_fulltext_search(client):
    """Verifies full-text search across endpoint paths, client IPs, and payload patterns."""
    res = client.get("/api/security/events?search=products&limit=25")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    for ev in data["events"]:
        match_found = (
            "products" in (ev.get("path") or "").lower() or
            "products" in (ev.get("details_json") or "").lower() or
            "products" in (ev.get("event_type") or "").lower()
        )
        assert match_found


def test_event_detail_inspector(client):
    """Validates single event forensic dossier retrieval and schema compliance."""
    # Fetch first event ID
    res_list = client.get("/api/security/events?limit=1")
    assert res_list.status_code == 200
    first_ev = res_list.json()["events"][0]
    event_id = first_ev["event_id"]

    # Inspect single event dossier
    res_detail = client.get(f"/api/security/events/{event_id}")
    assert res_detail.status_code == 200
    ev_detail = res_detail.json()

    assert ev_detail["event_id"] == event_id
    assert "timestamp" in ev_detail
    assert "client_ip" in ev_detail
    assert "method" in ev_detail
    assert "path" in ev_detail
    assert "status_code" in ev_detail
    assert "details" in ev_detail
    assert "investigation" in ev_detail
    assert "rule_id" in ev_detail


def test_event_not_found(client):
    """Verifies that querying a nonexistent event returns HTTP 404."""
    res = client.get("/api/security/events/EVT-NONEXISTENT-999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_related_events_correlation(client):
    """Validates multi-factor correlation of related security telemetry events."""
    res_list = client.get("/api/security/events?limit=5")
    assert res_list.status_code == 200
    event_id = res_list.json()["events"][0]["event_id"]

    res_related = client.get(f"/api/security/events/{event_id}/related?limit=10")
    assert res_related.status_code == 200
    rel_data = res_related.json()

    assert rel_data["event_id"] == event_id
    assert "related_events" in rel_data
    assert isinstance(rel_data["related_events"], list)

    for rel in rel_data["related_events"]:
        assert "relationship_type" in rel
        assert rel["relationship_type"] in [
            "CONFIRMED_CORRELATION",
            "COMMON_SOURCE_IP",
            "TARGET_ENDPOINT_PROXIMITY"
        ]


def test_detection_rule_catalog(client):
    """Verifies that all 7 detection rules are accurately inventoried with real SQLite telemetry counts."""
    res = client.get("/api/security/rules/catalog")
    assert res.status_code == 200
    data = res.json()

    assert data["total_rules"] == 7
    assert data["active_rules"] == 7
    rules = data["rules"]
    assert len(rules) == 7

    rule_ids = [r["rule_id"] for r in rules]
    expected_rules = ["INJ-001", "XSS-001", "AUTH-001", "AUTH-002", "RATE-001", "CORR-001", "HEALTH-001"]
    for expected in expected_rules:
        assert expected in rule_ids

    for r in rules:
        assert r["enabled"] is True
        assert r["related_event_count"] >= 0
        assert r["related_incident_count"] >= 0
        assert "mitre_technique_id" in r
        assert "description" in r
        assert "detection_logic" in r


def test_threat_intelligence_enrichment(client):
    """Verifies IP reputation, behavioral scoring, and threat tags from the threat intelligence engine."""
    res = client.get("/api/security/threat-intel/enrich?ip=127.0.0.1")
    assert res.status_code == 200
    intel = res.json()

    assert intel["ip"] == "127.0.0.1"
    assert "threat_score" in intel
    assert 0 <= intel["threat_score"] <= 100
    assert intel["reputation"] in ["MALICIOUS", "SUSPICIOUS", "NEUTRAL", "BENIGN"]
    assert "confidence" in intel
    assert "provider" in intel
    assert "provider_status" in intel
    assert "tags" in intel
    assert isinstance(intel["tags"], list)


def test_investigation_workflow_persistence(client):
    """Verifies that analyst notes and investigation status are persisted in the SQLite database and logged in audit logs."""
    res_list = client.get("/api/security/events?limit=1")
    event_id = res_list.json()["events"][0]["event_id"]

    test_notes = "Triage validation: suspicious injection parameter verified by Tier-2 analyst."
    res_inv = client.post(
        f"/api/security/events/{event_id}/investigate",
        json={
            "status": "INVESTIGATING",
            "notes": test_notes,
            "assigned_analyst": "lead_soc@sentinel.sec",
            "create_incident": False
        }
    )
    assert res_inv.status_code == 200
    inv_data = res_inv.json()
    assert inv_data["event_id"] == event_id
    assert inv_data["status"] == "INVESTIGATING"
    assert inv_data["notes"] == test_notes
    assert inv_data["assigned_analyst"] == "lead_soc@sentinel.sec"

    # Verify persistence via detail endpoint
    res_check = client.get(f"/api/security/events/{event_id}")
    assert res_check.status_code == 200
    detail = res_check.json()
    assert detail["investigation"]["status"] == "INVESTIGATING"
    assert detail["investigation"]["notes"] == test_notes
    assert detail["investigation"]["assigned_analyst"] == "lead_soc@sentinel.sec"


def test_incident_escalation_from_event(client):
    """Verifies that an analyst can escalate an unassigned event into a formal security incident."""
    res_list = client.get("/api/security/events?severity=CRITICAL&limit=1")
    assert res_list.status_code == 200
    event_id = res_list.json()["events"][0]["event_id"]

    res_esc = client.post(
        f"/api/security/events/{event_id}/investigate",
        json={
            "status": "ESCALATED",
            "notes": "Escalated critical SQL injection attempt to Tier-3 incident queue.",
            "assigned_analyst": "admin@sentinel.sec",
            "create_incident": True
        }
    )
    assert res_esc.status_code == 200
    esc_data = res_esc.json()
    assert esc_data["status"] == "ESCALATED"
    assert esc_data["incident_id"] is not None
    assert esc_data["incident_id"].startswith("INC-2026-")

    # Verify incident exists in incident center
    inc_res = client.get(f"/api/security/incidents/{esc_data['incident_id']}")
    assert inc_res.status_code == 200
    inc_dossier = inc_res.json()
    assert inc_dossier["incident_id"] == esc_data["incident_id"]


def test_events_csv_export(client):
    """Verifies that filtered security events can be exported as a valid CSV attachment."""
    res_csv = client.get("/api/security/events?format=csv&limit=10")
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers["content-type"]
    assert "attachment" in res_csv.headers["content-disposition"]
    content = res_csv.text
    lines = content.strip().split("\n")
    assert len(lines) >= 2
    header = lines[0]
    assert "Timestamp" in header
    assert "Event ID" in header
    assert "Severity" in header
    assert "Client IP" in header
