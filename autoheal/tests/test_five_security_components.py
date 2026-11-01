"""
Comprehensive Test Suite for AutoHeal's Five Security Components:
1. Component 1: Detection Agent (Rules + ML Inference)
2. Component 2: Log Correlation Engine (Sliding Window + Deduplication)
3. Component 3: Response Agent (Policy Quarantine + Audit Logging)
4. Component 4: Verification Agent (Perimeter Probe + Benign Non-Regression)
5. Component 5: Escalation Mechanism (Bounded Retries + Cooldown + Terminal Escalation)
Plus Incident Reporting (PDF & JSON) and Attack Center Safety Guardrails.
"""

import unittest
import json
import time
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from server import app
from src.appsec.models import (
    record_security_event, get_security_events,
    create_security_incident, find_active_incident, upsert_security_incident,
    get_security_incident, update_incident_status, list_security_incidents,
    block_client_ip, is_client_blocked, unblock_client_ip,
    redact_sensitive_data
)
from src.appsec.detector import AppSecDetector, DetectionResult
from src.appsec.correlation_engine import AppSecCorrelationEngine
from src.appsec.responder import AppSecResponder
from src.appsec.verifier import AppSecVerifier
from src.appsec.reporter import AppSecReporter
from src.appsec.security_tester import validate_target_safety, ShopSphereSecurityTester, cancel_active_tests, reset_cancellation


class TestFiveSecurityComponents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        reset_cancellation()

    # =========================================================================
    # 1. COMPONENT 1: DETECTION AGENT TESTS
    # =========================================================================
    def test_01_detection_agent_sqli_inspection(self):
        """Detection Agent must inspect payloads and flag SQL injection tautology."""
        result = AppSecDetector.analyze_live_request(
            client_ip="198.51.100.101",
            method="GET",
            path="/api/shop/products",
            query_string="q=Laptop'+OR+'1'='1"
        )
        self.assertTrue(result.triggered)
        self.assertEqual(result.rule_id, "INJ-001")
        self.assertEqual(result.category, "Injection")
        self.assertEqual(result.severity, "CRITICAL")
        self.assertGreaterEqual(result.confidence, 0.95)
        self.assertEqual(result.recommended_action, "BLOCK_IP")

    def test_02_detection_agent_xss_inspection(self):
        """Detection Agent must flag executable script tags and DOM event handlers."""
        result = AppSecDetector.analyze_live_request(
            client_ip="198.51.100.102",
            method="GET",
            path="/api/shop/products",
            query_string="q=<script>alert('AutoHeal')</script>"
        )
        self.assertTrue(result.triggered)
        self.assertEqual(result.rule_id, "XSS-001")
        self.assertEqual(result.severity, "HIGH")
        self.assertIn("Cross-Site Scripting", result.category)

    def test_03_detection_agent_admin_probe_inspection(self):
        """Detection Agent must flag unauthenticated direct admin probes."""
        result = AppSecDetector.analyze_live_request(
            client_ip="198.51.100.103",
            method="GET",
            path="/api/shop/admin/orders",
            headers={}
        )
        self.assertTrue(result.triggered)
        self.assertEqual(result.rule_id, "AUTH-002")
        self.assertEqual(result.category, "Privilege Escalation")
        self.assertEqual(result.severity, "HIGH")

    def test_04_detection_agent_benign_request(self):
        """Detection Agent must not trigger on benign browsing queries."""
        result = AppSecDetector.analyze_live_request(
            client_ip="198.51.100.104",
            method="GET",
            path="/api/shop/products",
            query_string="q=macbook&category=electronics"
        )
        self.assertFalse(result.triggered)

    # =========================================================================
    # 2. COMPONENT 2: LOG CORRELATION ENGINE & DEDUPLICATION TESTS
    # =========================================================================
    def test_05_correlation_engine_auth_failure_burst(self):
        """Correlation Engine must group sliding-window auth failures into AUTH-001 incident."""
        test_ip = "198.51.100.105"
        unblock_client_ip(test_ip)

        # Inject 4 telemetry events directly
        for i in range(4):
            record_security_event(
                client_ip=test_ip,
                method="POST",
                path="/api/shop/auth/login",
                status_code=401,
                event_type="AUTH_FAILURE",
                severity="MEDIUM",
                user_id_or_session=f"user_{i}"
            )

        engine = AppSecCorrelationEngine(window_seconds=60, auth_failure_threshold=4)
        detections = engine.correlate_events(window_seconds=60)
        auth_dets = [d for d in detections if d.rule_id == "AUTH-001" and d.evidence.get("client_ip") == test_ip]

        self.assertGreaterEqual(len(auth_dets), 1)
        det = auth_dets[0]
        self.assertEqual(det.category, "Credential Stuffing / Brute Force")
        self.assertIn("linked_event_ids", det.evidence)
        self.assertGreaterEqual(len(det.evidence["linked_event_ids"]), 4)

    def test_06_correlation_engine_deduplication_idempotency(self):
        """Correlation Engine must not create duplicate incidents on repeated evaluations."""
        test_ip = "198.51.100.106"
        unblock_client_ip(test_ip)

        engine = AppSecCorrelationEngine(window_seconds=60, auth_failure_threshold=4)

        for i in range(5):
            record_security_event(
                client_ip=test_ip,
                method="POST",
                path="/api/shop/auth/login",
                status_code=401,
                event_type="AUTH_FAILURE",
                severity="MEDIUM"
            )

        # Run process_and_persist_incidents twice
        incidents_run1 = engine.process_and_persist_incidents(window_seconds=60)
        incidents_run2 = engine.process_and_persist_incidents(window_seconds=60)

        # There should be exactly ONE active incident ID for this IP and rule
        auth_inc1 = next((i for i in incidents_run1 if i.get("rule_id") == "AUTH-001" and i.get("source_ip") == test_ip), None)
        auth_inc2 = next((i for i in incidents_run2 if i.get("rule_id") == "AUTH-001" and i.get("source_ip") == test_ip), None)

        self.assertIsNotNone(auth_inc1)
        self.assertIsNotNone(auth_inc2)
        self.assertEqual(auth_inc1["incident_id"], auth_inc2["incident_id"])

    # =========================================================================
    # 3. COMPONENT 3: RESPONSE AGENT TESTS
    # =========================================================================
    def test_07_response_agent_quarantine_enforcement(self):
        """Response Agent must dynamically quarantine client IP with specified TTL."""
        test_ip = "198.51.100.107"
        unblock_client_ip(test_ip)

        detection = DetectionResult(
            triggered=True,
            rule_id="INJ-001",
            category="Injection",
            severity="CRITICAL",
            confidence=0.99,
            summary="SQL injection test mitigation",
            evidence={"client_ip": test_ip, "target_path": "/api/shop/products"},
            recommended_action="BLOCK_IP"
        )

        mitigation = AppSecResponder.execute_defensive_mitigation(detection)
        self.assertIn("incident_id", mitigation)
        self.assertEqual(mitigation["action_executed"], "BLOCK_IP")

        # Verify client is actively blocked
        blocked, record = is_client_blocked(test_ip)
        self.assertTrue(blocked)
        self.assertEqual(record["client_ip"], test_ip)
        self.assertEqual(record["rule_id"], "INJ-001")

        # Cleanup
        unblock_client_ip(test_ip)

    def test_08_temporary_quarantine_auto_expiry(self):
        """Expired client block records must automatically deactivate upon evaluation."""
        test_ip = "198.51.100.108"
        # Insert a block that expired 10 seconds ago
        block_client_ip(client_ip=test_ip, reason="Test TTL", rule_id="TEST-001", duration_seconds=-10)

        blocked, _ = is_client_blocked(test_ip)
        self.assertFalse(blocked, "Expired client IP block must automatically evaluate to unblocked.")

    # =========================================================================
    # 4. COMPONENT 4: VERIFICATION AGENT TESTS
    # =========================================================================
    def test_09_verification_agent_containment_and_availability(self):
        """Verification Agent must verify 403 on quarantined attacker and 200 on benign shopper."""
        test_ip = "198.51.100.109"
        unblock_client_ip(test_ip)

        # Trigger response via live testclient
        resp = self.client.get("/api/shop/products?q=Watch'+OR+'1'='1", headers={"X-Forwarded-For": test_ip})
        self.assertEqual(resp.status_code, 403)
        inc_id = resp.json().get("incident_id")
        self.assertIsNotNone(inc_id)

        # Run verification agent
        verif_res = AppSecVerifier.verify_incident_containment(inc_id, test_client=self.client)
        self.assertTrue(verif_res["verified"])
        self.assertIn(verif_res["status"], ["CONTAINED", "CONTAINMENT_VERIFIED"])
        self.assertEqual(verif_res["verification_status"], "VERIFIED_CONTAINED")
        self.assertEqual(verif_res["containment_status_code"], 403)
        self.assertEqual(verif_res["benign_status_code"], 200)

        # Cleanup
        unblock_client_ip(test_ip)

    # =========================================================================
    # 5. COMPONENT 5: ESCALATION MECHANISM TESTS
    # =========================================================================
    def test_10_escalation_mechanism_bounded_retries(self):
        """Escalation Mechanism must enforce bounded retries and transition to ESCALATION_REQUIRED."""
        test_ip = "198.51.100.110"
        inc_id = create_security_incident(
            rule_id="AUTH-001",
            title="Escalation Test Incident",
            category="Credential Access",
            severity="HIGH",
            summary="Simulated failed containment",
            source_ip=test_ip,
            evidence={"escalation_retries": 0, "escalation_history": []},
            affected_endpoints=["/api/shop/auth/login"],
            impact_actual="Simulated",
            impact_potential="Simulated",
            mitigation_actions=[]
        )

        # Simulate Retry 1
        res1 = AppSecVerifier.escalate_incident(inc_id, "Test bypass 1")
        self.assertFalse(res1["verified"])
        self.assertEqual(res1["retry_count"], 1)
        self.assertEqual(res1["status"], "RESPONSE_ATTEMPTED")

        # Simulate Retry 2
        res2 = AppSecVerifier.escalate_incident(inc_id, "Test bypass 2")
        self.assertEqual(res2["retry_count"], 2)

        # Simulate Retry 3
        res3 = AppSecVerifier.escalate_incident(inc_id, "Test bypass 3")
        self.assertEqual(res3["retry_count"], 3)

        # Simulate Retry 4 (Exceeds MAX_RETRIES)
        res4 = AppSecVerifier.escalate_incident(inc_id, "Test bypass 4")
        self.assertTrue(res4.get("terminal_escalation"))
        self.assertEqual(res4["status"], "ESCALATION_REQUIRED")
        self.assertEqual(res4["verification_status"], "VERIFICATION_FAILED")

        # Verify persisted state in database
        persisted = get_security_incident(inc_id)
        self.assertEqual(persisted["status"], "ESCALATION_REQUIRED")
        self.assertEqual(persisted["verification_status"], "VERIFICATION_FAILED")
        self.assertIn("Manual SOC operator investigation required", persisted["remediation_details"])

    # =========================================================================
    # 6. INCIDENT REPORTS & FORENSICS TESTS
    # =========================================================================
    def test_11_incident_json_dossier_and_redaction(self):
        """JSON dossier must include full timeline, verification probes, and redacted credentials."""
        test_ip = "198.51.100.111"
        inc_id = create_security_incident(
            rule_id="AUTH-001",
            title="Dossier Test Incident",
            category="Credential Access",
            severity="HIGH",
            summary="Dossier audit test",
            source_ip=test_ip,
            evidence={
                "password": "SuperSecretPassword123!",
                "token": "Bearer abcdef1234567890",
                "linked_event_ids": ["EVT-001", "EVT-002"]
            },
            affected_endpoints=["/api/shop/auth/login"],
            impact_actual="None",
            impact_potential="High",
            mitigation_actions=[{"action": "BLOCK_IP", "duration_seconds": 180}]
        )

        dossier = AppSecReporter.generate_json_dossier(inc_id)
        self.assertIn("incident", dossier)
        self.assertIn("mitre_attack_alignment", dossier)
        self.assertIn("ai_forensic_analysis", dossier)

        # Sensitive password and token must be redacted
        inc_data = dossier["incident"]
        evidence_text = json.dumps(inc_data.get("evidence", {}))
        self.assertNotIn("SuperSecretPassword123!", evidence_text)
        self.assertNotIn("abcdef1234567890", evidence_text)
        self.assertIn("[REDACTED]", evidence_text)

    def test_12_incident_pdf_generation(self):
        """PDF generator must compile valid PDF 1.4 byte stream."""
        test_ip = "198.51.100.112"
        inc_id = create_security_incident(
            rule_id="INJ-001",
            title="PDF Test Incident",
            category="Injection",
            severity="CRITICAL",
            summary="PDF generation test",
            source_ip=test_ip,
            evidence={"matched_pattern": "' OR '1'='1"},
            affected_endpoints=["/api/shop/products"],
            impact_actual="None",
            impact_potential="High",
            mitigation_actions=[{"action": "BLOCK_IP", "duration_seconds": 300}]
        )

        pdf_bytes = AppSecReporter.generate_pdf_report(inc_id)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
        self.assertIn(b"%%EOF", pdf_bytes)

    # =========================================================================
    # 7. ATTACK CENTER TARGET SAFETY & RESTRICTIONS TESTS
    # =========================================================================
    def test_13_attack_center_target_safety_and_cancellation(self):
        """Attack Center must strictly reject non-localhost URLs and support test cancellation."""
        # Non-localhost targets must be rejected
        with self.assertRaises(ValueError):
            validate_target_safety("https://flipkart.com")

        with self.assertRaises(ValueError):
            validate_target_safety("http://142.250.190.46:8000")

        # Cancellation support
        cancel_active_tests()
        from src.appsec.security_tester import is_test_cancelled
        self.assertTrue(is_test_cancelled())
        reset_cancellation()
        self.assertFalse(is_test_cancelled())


if __name__ == "__main__":
    unittest.main()
