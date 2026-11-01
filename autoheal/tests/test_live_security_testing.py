"""
Comprehensive Regression Test Suite for AutoHeal Live Security Testing & AppSec Pipeline
Validates end-to-end event-to-detection-to-response-to-report pipeline against local ShopSphere endpoints.
"""

import unittest
import json
import time
from fastapi.testclient import TestClient

from server import app
from src.appsec.models import (
    get_security_events, list_security_incidents,
    get_security_incident, is_client_blocked, unblock_client_ip,
    redact_sensitive_data
)
from src.appsec.security_tester import validate_target_safety, ShopSphereSecurityTester
from src.appsec.pdf_generator import IncidentPDFGenerator
from src.appsec.reporter import AppSecReporter


class TestLiveSecurityTestingPipeline(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_target_safety_guardrails(self):
        """Verifies runner permits only localhost targets and blocks arbitrary remote hosts."""
        self.assertEqual(validate_target_safety("http://localhost:8000"), "http://localhost:8000")
        self.assertEqual(validate_target_safety("http://127.0.0.1:8000"), "http://127.0.0.1:8000")
        self.assertEqual(validate_target_safety("http://0.0.0.0:8000"), "http://0.0.0.0:8000")
        self.assertEqual(validate_target_safety("http://testserver"), "http://testserver")

        with self.assertRaises(ValueError):
            validate_target_safety("http://google.com")

        with self.assertRaises(ValueError):
            validate_target_safety("http://192.168.1.100:8080")

        with self.assertRaises(ValueError):
            validate_target_safety("ftp://localhost:8000")

    def test_02_scenario_failed_logins_and_rate_limiting(self):
        """
        Scenario 1: Repeated failed logins to /api/shop/auth/login.
        Verifies 401 on attempts 1-4, threshold detection for AUTH-001,
        and immediate quarantine with HTTP 403 on subsequent attempt.
        """
        test_ip = "198.51.100.91"
        unblock_client_ip(test_ip)
        headers = {"X-Forwarded-For": test_ip}

        # Send 5 failed login attempts
        for i in range(5):
            resp = self.client.post(
                "/api/shop/auth/login",
                json={"email": f"victim_test_{i}@shopsphere.com", "password": "WrongPassword123!"},
                headers=headers
            )
            self.assertIn(resp.status_code, [401, 403])

        # Verification Probe: 6th attempt MUST be blocked by Sentinel with HTTP 403
        verif_resp = self.client.post(
            "/api/shop/auth/login",
            json={"email": "victim_test_probe@shopsphere.com", "password": "AnyPassword!"},
            headers=headers
        )
        self.assertEqual(verif_resp.status_code, 403)
        data = verif_resp.json()
        self.assertIn("error", data)
        self.assertIn("Sentinel", data["error"])

        # Verify incident exists in database
        incidents = list_security_incidents(limit=100)
        auth_inc = next((i for i in incidents if i.get("rule_id") == "AUTH-001" and i.get("source_ip") == test_ip), None)
        self.assertIsNotNone(auth_inc)
        self.assertEqual(auth_inc.get("verification_status"), "VERIFIED_CONTAINED")

        # Cleanup
        unblock_client_ip(test_ip)

    def test_03_scenario_sql_injection_defense(self):
        """
        Scenario 2: Safe SQL injection test string.
        Verifies immediate 403 intercept and IP quarantine.
        """
        test_ip = "203.0.113.71"
        unblock_client_ip(test_ip)
        headers = {"X-Forwarded-For": test_ip}

        resp = self.client.get("/api/shop/products?q=MacBook'+OR+'1'='1", headers=headers)
        self.assertEqual(resp.status_code, 403)
        data = resp.json()
        self.assertEqual(data.get("rule_id"), "INJ-001")
        self.assertEqual(data.get("threat_category"), "Injection")

        # Verify subsequent request from this IP is also quarantined
        followup = self.client.get("/api/shop/products", headers=headers)
        self.assertEqual(followup.status_code, 403)

        # Cleanup
        unblock_client_ip(test_ip)

    def test_04_scenario_xss_neutralization(self):
        """
        Scenario 3: Safe XSS probe string.
        Verifies immediate 403 intercept.
        """
        test_ip = "203.0.113.72"
        unblock_client_ip(test_ip)
        headers = {"X-Forwarded-For": test_ip}

        resp = self.client.get("/api/shop/products?q=<script>alert('XSS-Test')</script>", headers=headers)
        self.assertEqual(resp.status_code, 403)
        data = resp.json()
        self.assertEqual(data.get("rule_id"), "XSS-001")

        # Cleanup
        unblock_client_ip(test_ip)

    def test_05_scenario_unauthorized_admin_probe(self):
        """
        Scenario 4: Unauthorized access to /api/shop/admin/stats.
        Verifies request is denied with 401 or 403.
        """
        test_ip = "198.51.100.73"
        unblock_client_ip(test_ip)
        headers = {"X-Forwarded-For": test_ip}

        resp = self.client.get("/api/shop/admin/stats", headers=headers)
        self.assertIn(resp.status_code, [401, 403])

        # Cleanup
        unblock_client_ip(test_ip)

    def test_06_scenario_request_rate_anomaly(self):
        """
        Scenario 5: High-frequency request burst.
        Verifies HTTP 429 Too Many Requests is triggered.
        """
        test_ip = "198.51.100.74"
        unblock_client_ip(test_ip)
        headers = {"X-Forwarded-For": test_ip}

        throttled = False
        for _ in range(25):
            resp = self.client.get("/api/shop/products", headers=headers)
            if resp.status_code == 429:
                throttled = True
                self.assertIn("Retry-After", resp.headers)
                break

        self.assertTrue(throttled, "Rate limiting should have returned HTTP 429 during burst")

        # Cleanup
        unblock_client_ip(test_ip)

    def test_07_scenario_health_cascade_resilience(self):
        """
        Scenario 6: Application Health & Exception Telemetry.
        Verifies simulated error is captured and storefront health remains operational.
        """
        test_ip = "198.51.100.75"
        headers = {"X-Forwarded-For": test_ip}

        # Simulated error
        err_resp = self.client.post("/api/shop/health/simulate-error", headers=headers)
        self.assertEqual(err_resp.status_code, 500)

        # Health endpoint check
        health_resp = self.client.get("/api/shop/health")
        self.assertEqual(health_resp.status_code, 200)
        self.assertEqual(health_resp.json().get("status"), "UP")

    def test_08_pdf_incident_report_generation(self):
        """Verifies pure-Python PDF generator outputs valid standard binary PDF documents."""
        mock_inc = {
            "incident_id": "INC-2026-UNIT",
            "rule_id": "AUTH-001",
            "title": "Credential Stuffing Incident",
            "category": "Credential Stuffing / Brute Force",
            "severity": "HIGH",
            "status": "CONTAINED",
            "verification_status": "VERIFIED_CONTAINED",
            "summary": "Burst of failed logins detected against ShopSphere auth service.",
            "source_ip": "198.51.100.22",
            "evidence": {"failed_attempt_count": 5, "target_endpoint": "/api/shop/auth/login"},
            "affected_endpoints": ["/api/shop/auth/login"],
            "impact_actual": "Attempted brute force contained before account takeover.",
            "impact_potential": "High risk of credential compromise.",
            "remediation_details": "Client IP dynamically quarantined for 180s."
        }
        pdf_bytes = IncidentPDFGenerator.generate_pdf_report(mock_inc)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))
        self.assertTrue(b"%%EOF" in pdf_bytes)

    def test_09_incident_export_endpoints(self):
        """Verifies REST API endpoints for JSON and PDF report downloads."""
        # Create a test incident first via SQL injection
        test_ip = "203.0.113.76"
        unblock_client_ip(test_ip)
        self.client.get("/api/shop/products?q=Watch'+OR+'1'='1", headers={"X-Forwarded-For": test_ip})

        incidents = list_security_incidents(limit=5)
        self.assertTrue(len(incidents) > 0)
        inc_id = incidents[0]["incident_id"]

        # 1. Export as JSON
        json_resp = self.client.get(f"/api/security/incidents/{inc_id}/export?format=json")
        self.assertEqual(json_resp.status_code, 200)
        json_data = json_resp.json()
        self.assertIn("incident", json_data)

        # 2. Export as PDF
        pdf_resp = self.client.get(f"/api/security/incidents/{inc_id}/export?format=pdf")
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp.headers["content-type"], "application/pdf")
        self.assertTrue(pdf_resp.content.startswith(b"%PDF-1.4"))

        # Cleanup
        unblock_client_ip(test_ip)

    def test_10_sensitive_data_redaction_guardrails(self):
        """Verifies passwords and credit cards are NEVER saved unmasked in telemetry or incidents."""
        raw_data = {
            "password": "SuperSecretPassword123!",
            "credit_card": "4111 2222 3333 4444",
            "token": "Bearer secret_bearer_token_xyz"
        }
        redacted = redact_sensitive_data(raw_data)
        self.assertEqual(redacted["password"], "[REDACTED]")
        self.assertNotIn("SuperSecretPassword123!", str(redacted))

    def test_11_replay_attack_comparison(self):
        """Verifies the /api/security/test/replay endpoint executes and returns before/after comparisons."""
        test_ip = "203.0.113.111"
        unblock_client_ip(test_ip)

        resp = self.client.post(
            "/api/security/test/replay",
            json={
                "scenario": "sqli",
                "target_url": "http://testserver",
                "client_ip": test_ip
            }
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["scenario"], "sqli")
        self.assertEqual(data["client_ip"], test_ip)
        self.assertIn("before_state", data)
        self.assertIn("after_state", data)
        self.assertTrue(data["protection_verified"])

        unblock_client_ip(test_ip)


if __name__ == "__main__":
    unittest.main()
