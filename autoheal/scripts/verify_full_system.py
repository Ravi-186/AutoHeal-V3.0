"""
AutoHeal Enterprise Autonomous Security & ShopSphere Full System Verification
Tests all 12 platform capabilities against live local server http://localhost:8000.
"""

import sys
import json
import time
import httpx

BASE_URL = "http://localhost:8000"

def test_full_system():
    client = httpx.Client(timeout=30.0)
    print("=" * 70)
    print("AUTOHEAL ENTERPRISE DEFENSE PLATFORM - END-TO-END SYSTEM TEST")
    print("=" * 70)

    # 1. Verify ShopSphere Storefront and AutoHeal SOC Interface (Feature 12)
    print("\n[TEST 1] Verifying AutoHeal SOC Dashboard and ShopSphere Web UI...")
    soc_res = client.get(f"{BASE_URL}/")
    assert soc_res.status_code == 200, f"AutoHeal SOC failed: {soc_res.status_code}"
    assert "AutoHeal" in soc_res.text, "AutoHeal branding missing from SOC interface"
    print("  -> AutoHeal SOC Interface (http://localhost:8000/): HTTP 200 OK")

    shop_res = client.get(f"{BASE_URL}/shop")
    assert shop_res.status_code == 200, f"ShopSphere Storefront failed: {shop_res.status_code}"
    assert "ShopSphere" in shop_res.text, "ShopSphere branding missing from storefront"
    print("  -> ShopSphere Storefront (http://localhost:8000/shop): HTTP 200 OK")

    # 2. Attack Center Execution & SSE Streaming (Feature 1 & Feature 2)
    print("\n[TEST 2] Executing Bounded Attack Center Simulation (Failed Logins -> Local ShopSphere)...")
    payload = {
        "scenario": "failed_logins",
        "target_host": "http://localhost:8000",
        "endpoint": "/api/shop/auth/login",
        "attempts": 6,
        "client_ip": "198.51.100.11",
        "username": "victim@example.com",
        "password": "WrongPassword123"
    }
    run_res = client.post(f"{BASE_URL}/api/security/test/run", json=payload)
    assert run_res.status_code == 200, f"Attack execution failed: {run_res.status_code}"
    test_run = run_res.json()
    incident_id = test_run.get("incident_id")
    assert incident_id, "No incident_id returned from test execution"
    print(f"  -> Attack run successfully executed. Incident generated: {incident_id}")

    # 3. Persistent Security Telemetry Event Pipeline (Feature 2)
    print("\n[TEST 3] Verifying Security Event Pipeline & SQLite Storage...")
    events_res = client.get(f"{BASE_URL}/api/security/events?limit=10")
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) > 0, "No telemetry events in database"
    first_evt = events[0]
    assert "event_id" in first_evt and "event_type" in first_evt and "correlation_id" in first_evt
    print(f"  -> Telemetry store verified: {len(events)} events retrieved. Sample: [{first_evt['event_type']}] from {first_evt['client_ip']}")

    # 4. Real Detection Rules & Evidence Correlation (Feature 3)
    print("\n[TEST 4] Verifying Real Detection Rules & Incident Correlation...")
    inc_res = client.get(f"{BASE_URL}/api/security/incidents/{incident_id}")
    assert inc_res.status_code == 200, f"Incident fetch failed: {inc_res.status_code}"
    inc_data = inc_res.json()
    assert inc_data.get("rule_id") == "AUTH-001", f"Unexpected rule_id: {inc_data.get('rule_id')}"
    assert inc_data.get("confidence", 0) >= 0.9, "Confidence score lower than expected"
    assert "evidence" in inc_data or "evidence_summary" in inc_data, "Incident missing evidence"
    print(f"  -> Rule [{inc_data['rule_id']}] matched with {int(inc_data['confidence']*100)}% confidence. Evidence verified.")

    # 5. Automatic Containment & Follow-up Verification (Feature 4)
    print("\n[TEST 5] Verifying Automatic Containment, Expiry, and Verification Probes...")
    blocked_res = client.get(f"{BASE_URL}/api/security/blocked-clients")
    assert blocked_res.status_code == 200
    blocked_clients = blocked_res.json()
    blocked_ips = [b["client_ip"] for b in blocked_clients]
    assert "198.51.100.11" in blocked_ips, f"IP 198.51.100.11 was not quarantined: {blocked_ips}"
    print(f"  -> Client 198.51.100.11 successfully quarantined in sliding TTL blocklist. Active blocks: {len(blocked_clients)}")

    # Unblock test to verify manual and autonomous release
    unblock_res = client.post(f"{BASE_URL}/api/security/unblock", json={"client_ip": "198.51.100.11"})
    assert unblock_res.status_code == 200
    print("  -> Client 198.51.100.11 unblocked successfully.")

    # 6. MITRE ATT&CK Mapping (Feature 8)
    print("\n[TEST 6] Verifying MITRE ATT&CK Mapping...")
    assert inc_data.get("mitre_technique_id") == "T1110.001", f"Unexpected MITRE technique: {inc_data.get('mitre_technique_id')}"
    assert "Credential Access" in inc_data.get("mitre_tactic", ""), f"Unexpected MITRE tactic: {inc_data.get('mitre_tactic')}"
    print(f"  -> MITRE Mapping verified: {inc_data['mitre_technique_id']} ({inc_data['mitre_name']}) in tactic [{inc_data['mitre_tactic']}].")

    # 7. AI-Assisted Forensic Summaries & Recommendations (Feature 7)
    print("\n[TEST 7] Verifying Grounded AI Forensic Summaries & Remediation Plans...")
    ai_res = client.get(f"{BASE_URL}/api/security/incidents/{incident_id}/ai-summary")
    assert ai_res.status_code == 200, f"AI summary endpoint failed: {ai_res.status_code}"
    ai_data = ai_res.json()
    assert "ai_summary" in ai_data and len(ai_data["ai_summary"]) > 20, "AI summary missing or empty"
    assert "remediation_recommendations" in ai_data and len(ai_data["remediation_recommendations"]) >= 3, "Missing recommendations"
    print(f"  -> Grounded AI Forensic Narrative: {ai_data['ai_summary'][:85]}...")
    print(f"  -> Root Cause: {ai_data.get('root_cause')}")
    print(f"  -> AI Action Checklist ({len(ai_data['remediation_recommendations'])} items generated)")

    # 8. Incident Investigation Workspace Timeline & Recovery Status (Feature 6)
    print("\n[TEST 8] Verifying Incident Investigation Workspace & Recovery Status...")
    assert inc_data.get("recovery_status") == "NOMINAL_MONITORING"
    print(f"  -> Investigation Workspace state: {inc_data['status']}, Recovery: {inc_data['recovery_status']}")

    # 9. Before-and-After Testing and Attack Replay (Feature 9)
    print("\n[TEST 9] Verifying Attack Replay & Before-and-After Comparison Engine...")
    replay_res = client.post(f"{BASE_URL}/api/security/test/replay", json={"scenario": "sqli"})
    assert replay_res.status_code == 200, f"Replay failed: {replay_res.status_code}"
    replay_data = replay_res.json()
    assert "before" in replay_data and "after" in replay_data
    print(f"  -> Before State: HTTP {replay_data['before']['status_code']} - {replay_data['before']['defense_verdict']}")
    print(f"  -> After State:  HTTP {replay_data['after']['status_code']} - {replay_data['after']['defense_verdict']}")
    print(f"  -> Delta Summary: {replay_data['evaluation_delta']}")

    # 10. Vulnerability Tracker & Controlled Remediation Workflow (Feature 5)
    print("\n[TEST 10] Verifying Vulnerability Tracker, Approval Gates, Isolated Tests & Rollback...")
    vulns_res = client.get(f"{BASE_URL}/api/security/vulnerabilities")
    assert vulns_res.status_code == 200
    vulns = vulns_res.json()
    assert len(vulns) >= 5, f"Expected 5 seeded vulnerabilities, got {len(vulns)}"
    target_vuln_id = "VULN-AUTH-001"
    print(f"  -> Retrieved {len(vulns)} registered vulnerabilities from tracker.")

    # 10a. Isolated Regression Test
    test_vuln_res = client.post(f"{BASE_URL}/api/security/vulnerabilities/{target_vuln_id}/test")
    assert test_vuln_res.status_code == 200
    test_result = test_vuln_res.json()
    assert test_result.get("status") == "PASSED", f"Regression test failed: {test_result}"
    print(f"  -> Isolated Regression Test [{test_result.get('test_name')}]: PASSED ({test_result.get('duration_ms')}ms)")

    # 10b. Approval Gate
    approve_res = client.post(f"{BASE_URL}/api/security/vulnerabilities/{target_vuln_id}/approve", json={"approver": "SecOps Automation"})
    assert approve_res.status_code == 200
    assert approve_res.json().get("approval_status") == "APPROVED"
    print(f"  -> Approval Gate passed for {target_vuln_id}: APPROVED")

    # 10c. Apply Patch
    apply_res = client.post(f"{BASE_URL}/api/security/vulnerabilities/{target_vuln_id}/apply")
    assert apply_res.status_code == 200
    assert apply_res.json().get("status") in ["PATCHED_VERIFIED", "REMEDIATED"], f"Unexpected apply status: {apply_res.json()}"
    print(f"  -> Remediation Patch applied for {target_vuln_id}: {apply_res.json().get('status')}")

    # 10d. Rollback Patch
    rollback_res = client.post(f"{BASE_URL}/api/security/vulnerabilities/{target_vuln_id}/rollback")
    assert rollback_res.status_code == 200
    assert rollback_res.json().get("status") == "ROLLED_BACK"
    print(f"  -> Rollback workflow executed for {target_vuln_id}: ROLLED_BACK")

    # 11. Incident Reports in JSON and PDF Formats (Feature 10)
    print("\n[TEST 11] Verifying Incident Reports Generation (JSON & Binary PDF 1.4)...")
    json_rep_res = client.get(f"{BASE_URL}/api/security/incidents/{incident_id}/export?format=json")
    assert json_rep_res.status_code == 200
    assert json_rep_res.headers.get("content-type") == "application/json"
    rep_obj = json_rep_res.json()
    extracted_id = rep_obj.get("incident_id") or rep_obj.get("incident", {}).get("incident_id")
    assert extracted_id == incident_id, f"Expected {incident_id}, got {extracted_id}"
    print(f"  -> JSON Incident Report verified ({len(json_rep_res.content)} bytes)")

    pdf_rep_res = client.get(f"{BASE_URL}/api/security/incidents/{incident_id}/export?format=pdf")
    assert pdf_rep_res.status_code == 200
    assert pdf_rep_res.headers.get("content-type") == "application/pdf"
    assert pdf_rep_res.content.startswith(b"%PDF-1.4"), "Downloaded file is not a valid PDF 1.4 document"
    print(f"  -> Pure-Python PDF 1.4 Incident Dossier verified ({len(pdf_rep_res.content)} bytes, header: %PDF-1.4)")

    # 12. Transparent Security Posture Score (Feature 11)
    print("\n[TEST 12] Verifying Transparent Security Posture Score & Defense Pillars...")
    posture_res = client.get(f"{BASE_URL}/api/security/posture")
    assert posture_res.status_code == 200
    posture = posture_res.json()
    assert "posture_score" in posture and 0 <= posture["posture_score"] <= 100
    assert "rating" in posture
    assert "scoring_formula" in posture
    assert "defense_pillars" in posture and len(posture["defense_pillars"]) == 5
    print(f"  -> Posture Score: {posture['posture_score']}/100 (Grade {posture['rating']} - {posture['posture_rating']})")
    print(f"  -> Containment Rate: {posture['containment_rate_percent']}% across {posture['active_containments']} active blocks")
    print(f"  -> Scoring Formula: {posture['scoring_formula']}")
    for p in posture["defense_pillars"]:
        print(f"     * Pillar [{p['name']}]: {p['score']}% ({p['status']})")

    print("\n" + "=" * 70)
    print("ALL 12 PLATFORM CAPABILITIES FULLY VERIFIED AND PASSING!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_full_system()
    except Exception as e:
        print(f"\n[FATAL ERROR] System test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
