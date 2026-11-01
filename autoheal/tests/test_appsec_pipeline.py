import os
import sys
import unittest
import time
from datetime import datetime, timezone, timedelta

# Ensure repo root is on Python path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from shopsphere.database import init_db
from src.appsec.models import (
    redact_sensitive_data, record_security_event, get_security_events,
    create_security_incident, get_security_incident, list_security_incidents,
    update_incident_status, block_client_ip, is_client_blocked,
    unblock_client_ip, get_active_blocked_clients
)
from src.appsec.detector import AppSecDetector, DetectionResult
from src.appsec.responder import AppSecResponder
from src.appsec.reporter import AppSecReporter


class TestSensitiveDataRedaction(unittest.TestCase):
    def test_password_and_token_redaction(self):
        sample_payload = {
            "username": "attacker",
            "password": "MySuperSecretPassword@2026",
            "auth_token": "token_abc123456789",
            "profile": {
                "user_id": 42,
                "secret_key": "sk_live_999888777"
            }
        }
        redacted = redact_sensitive_data(sample_payload)
        self.assertEqual(redacted["password"], "[REDACTED]")
        self.assertEqual(redacted["auth_token"], "[REDACTED]")
        self.assertEqual(redacted["profile"]["secret_key"], "[REDACTED]")
        self.assertEqual(redacted["profile"]["user_id"], 42)

    def test_credit_card_and_bearer_token_string_redaction(self):
        raw_text = "Transaction payload with raw card 4111-2222-3333-4444 and Authorization=Bearer eyJhbGciOiJIUzI1NiJ9"
        cleaned = redact_sensitive_data(raw_text)
        self.assertNotIn("4111-2222-3333-4444", cleaned)
        self.assertNotIn("eyJhbGciOiJIUzI1NiJ9", cleaned)
        self.assertIn("[REDACTED_CREDIT_CARD]", cleaned)
        self.assertIn("[REDACTED_TOKEN]", cleaned)


class TestAppSecDetectionRules(unittest.TestCase):
    def test_sqli_detection_and_tautologies(self):
        malicious_queries = [
            "q=' OR '1'='1",
            "q=admin' UNION SELECT id, password FROM users--",
            "q=1; DROP TABLE products"
        ]
        for q in malicious_queries:
            det = AppSecDetector.analyze_live_request(
                client_ip="198.51.100.99",
                method="GET",
                path="/api/shop/products",
                query_string=q
            )
            self.assertTrue(det.triggered, f"Failed to detect SQLi in query: {q}")
            self.assertEqual(det.rule_id, "INJ-001")
            self.assertEqual(det.severity, "CRITICAL")
            self.assertGreaterEqual(det.confidence, 0.95)

    def test_xss_detection_patterns(self):
        xss_queries = [
            "search=<script>alert('xss')</script>",
            "name=<img src=x onerror=alert(1)>",
            "ref=javascript:stealTokens()"
        ]
        for q in xss_queries:
            det = AppSecDetector.analyze_live_request(
                client_ip="198.51.100.88",
                method="GET",
                path="/api/shop/products",
                query_string=q
            )
            self.assertTrue(det.triggered, f"Failed to detect XSS in query: {q}")
            self.assertEqual(det.rule_id, "XSS-001")
            self.assertEqual(det.severity, "HIGH")

    def test_unauthorized_admin_probing(self):
        det = AppSecDetector.analyze_live_request(
            client_ip="203.0.113.15",
            method="GET",
            path="/api/shop/admin/stats",
            headers={"Authorization": "Bearer invalid_customer_token"}
        )
        self.assertTrue(det.triggered)
        self.assertEqual(det.rule_id, "AUTH-002")
        self.assertEqual(det.category, "Privilege Escalation")

    def test_benign_traffic_no_false_positives(self):
        benign_queries = [
            "q=Apple iPhone 16 Pro",
            "q=Men's Running Shoes",
            "q=Sony WH-1000XM5",
            "category=electronics&min_price=10000"
        ]
        for q in benign_queries:
            det = AppSecDetector.analyze_live_request(
                client_ip="192.168.1.50",
                method="GET",
                path="/api/shop/products",
                query_string=q
            )
            self.assertFalse(det.triggered, f"False positive triggered for benign query: {q}")


class TestCorrelationAndSlidingWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_credential_stuffing_correlation(self):
        test_ip = "198.51.100.77"
        # Record 5 failed logins
        for i in range(5):
            record_security_event(
                client_ip=test_ip,
                method="POST",
                path="/api/shop/auth/login",
                status_code=401,
                event_type="AUTH_FAILURE",
                severity="MEDIUM",
                user_id_or_session=f"target_victim_{i}"
            )

        detections = AppSecDetector.correlate_telemetry_window(window_seconds=60)
        auth_dets = [d for d in detections if d.rule_id == "AUTH-001" and d.evidence.get("client_ip") == test_ip]
        self.assertGreaterEqual(len(auth_dets), 1)
        self.assertEqual(auth_dets[0].category, "Credential Stuffing / Brute Force")

    def test_health_degradation_correlation(self):
        for _ in range(4):
            record_security_event(
                client_ip="127.0.0.1",
                method="GET",
                path="/api/shop/checkout",
                status_code=500,
                event_type="SERVICE_HEALTH_ERROR",
                severity="HIGH"
            )

        detections = AppSecDetector.correlate_telemetry_window(window_seconds=60)
        health_dets = [d for d in detections if d.rule_id == "HEALTH-001"]
        self.assertGreaterEqual(len(health_dets), 1)
        self.assertEqual(health_dets[0].recommended_action, "RECOVER_SERVICE")


class TestDefensiveResponseAndMitigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_block_client_ip_and_expiry(self):
        test_ip = "203.0.113.44"
        # Block for 2 seconds
        block_client_ip(test_ip, reason="Automated test block", rule_id="TEST-001", duration_seconds=2)
        blocked, info = is_client_blocked(test_ip)
        self.assertTrue(blocked)
        self.assertEqual(info["rule_id"], "TEST-001")

        # Wait for expiry
        time.sleep(2.1)
        blocked_after, _ = is_client_blocked(test_ip)
        self.assertFalse(blocked_after)

    def test_responder_mitigation_execution_and_rollback(self):
        detection = DetectionResult(
            triggered=True,
            rule_id="INJ-001",
            category="Injection",
            severity="CRITICAL",
            confidence=0.99,
            summary="SQL injection test attempt",
            evidence={"client_ip": "198.51.100.55", "target_path": "/api/shop/products"},
            recommended_action="BLOCK_IP"
        )
        mitigation = AppSecResponder.execute_defensive_mitigation(detection)
        self.assertEqual(mitigation["status"], "CONTAINED")
        self.assertTrue(mitigation["verified"])

        inc_id = mitigation["incident_id"]
        inc = get_security_incident(inc_id)
        self.assertIsNotNone(inc)
        self.assertEqual(inc["status"], "CONTAINED")

        # Rollback mitigation
        rollback_res = AppSecResponder.rollback_mitigation("BLOCK_IP", "198.51.100.55", inc_id)
        self.assertEqual(rollback_res["status"], "success")

        # Verify client is no longer blocked
        blocked, _ = is_client_blocked("198.51.100.55")
        self.assertFalse(blocked)


class TestIncidentReporting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_markdown_and_json_report_generation(self):
        inc_id = create_security_incident(
            rule_id="INJ-001",
            title="AutoHeal AppSec: SQL injection detected",
            category="Injection",
            severity="CRITICAL",
            summary="Interception of SQL injection payload on /api/shop/products",
            source_ip="198.51.100.12",
            evidence={"matched_pattern": "UNION SELECT", "client_ip": "198.51.100.12"},
            affected_endpoints=["/api/shop/products"],
            impact_actual="Payload dropped at WAF layer.",
            impact_potential="Database unauthorized read/exfiltration.",
            mitigation_actions=[{"action": "BLOCK_IP", "duration_seconds": 300}],
            confidence=0.98,
            status="CONTAINED",
            verification_status="VERIFIED_CONTAINED"
        )

        # Markdown Report
        md = AppSecReporter.generate_markdown_report(inc_id)
        self.assertIn(inc_id, md)
        self.assertIn("AutoHeal Forensic Incident Report", md)
        self.assertIn("UNION SELECT", md)
        self.assertIn("VERIFIED_CONTAINED", md)

        # JSON Dossier
        dossier = AppSecReporter.generate_json_dossier(inc_id)
        self.assertEqual(dossier["incident"]["incident_id"], inc_id)
        self.assertEqual(dossier["incident"]["category"], "Injection")

        # CSV Events
        csv = AppSecReporter.generate_csv_events(limit=10)
        self.assertIn("event_id,correlation_id,timestamp", csv)


if __name__ == "__main__":
    unittest.main()
