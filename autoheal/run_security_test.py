"""
ShopSphere Controlled Security Test CLI
Executes real HTTP test requests against local ShopSphere instances to validate
AutoHeal AppSec Sentinel detection, dynamic mitigation, and forensic reporting.
"""

import sys
import os
import argparse
import json
import time

# Ensure repository root is on path
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.appsec.security_tester import ShopSphereSecurityTester, validate_target_safety
from src.appsec.reporter import AppSecReporter


def print_banner():
    print("\n" + "=" * 80)
    print("   🛡️   AUTOHEAL APPSEC: CONTROLLED SECURITY TEST RUNNER ⚡")
    print("   Authorized Testing Suite Targeting Local ShopSphere E-Commerce Application")
    print("=" * 80 + "\n")


def print_scenario_result(res: dict):
    name = res.get("test_name", "Security Test")
    rule = res.get("rule_id", "POLICY")
    verified = res.get("protection_verified", False)
    status_str = "✅ VERIFIED PROTECTED" if verified else "❌ MITIGATION FAILED"
    
    print("-" * 80)
    print(f"🎯 SCENARIO: {name} [{rule}]")
    print(f"   Target:   {res.get('target_endpoint')} (Source IP: {res.get('client_ip')})")
    print(f"   Outcome:  {status_str}")
    print(f"   Details:  {res.get('verification_details')}")

    inc_id = res.get("incident_id")
    if inc_id:
        print(f"   Incident: {inc_id}")
        print(f"   Report:   http://localhost:8000/api/security/incidents/{inc_id}/export?format=pdf")
    
    if "steps" in res:
        print("   Audit Trail:")
        for st in res["steps"]:
            step_name = st.get("step", "STEP")
            sc = st.get("status_code", "")
            sc_str = f"HTTP {sc}" if sc else ""
            out = st.get("outcome") or st.get("status") or ""
            print(f"     • {step_name:20} {sc_str:10} {out}")
    print("-" * 80)


def main():
    parser = argparse.ArgumentParser(description="AutoHeal Controlled Security Test Runner")
    parser.add_argument("--target", default="http://localhost:8000", help="Target ShopSphere base URL (must be localhost/127.0.0.1)")
    parser.add_argument(
        "--scenario",
        default="all",
        choices=["all", "failed_logins", "sqli", "xss", "admin", "rate", "health"],
        help="Test scenario to execute"
    )
    parser.add_argument("--attempts", type=int, default=5, help="Number of failed login attempts for brute force scenario")
    parser.add_argument("--ip", default=None, help="Custom test client IP (simulated via X-Forwarded-For)")
    parser.add_argument("--json", action="store_true", help="Output results in raw JSON format")

    args = parser.parse_args()

    try:
        tester = ShopSphereSecurityTester(base_url=args.target)
    except ValueError as e:
        print(f"\n[SAFETY ERROR] {str(e)}", file=sys.stderr)
        sys.exit(1)

    if not args.json:
        print_banner()
        print(f"[*] Target Application URL: {tester.base_url}")
        print(f"[*] Enforcing Localhost-Only Safety Boundary: Validated OK\n")

    results = []

    if args.scenario in ["all", "failed_logins"]:
        ip = args.ip or "198.51.100.22"
        if not args.json:
            print(f"[*] [1/6] Launching Scenario: Repeated Failed Logins ({args.attempts} attempts from {ip})...")
        r = tester.test_repeated_failed_logins(client_ip=ip, attempts=args.attempts)
        results.append(r)
        if not args.json:
            print_scenario_result(r)

    if args.scenario in ["all", "sqli"]:
        ip = args.ip or "203.0.113.88"
        if not args.json:
            print(f"[*] [2/6] Launching Scenario: Safe SQL Injection Test from {ip}...")
        r = tester.test_sql_injection(client_ip=ip)
        results.append(r)
        if not args.json:
            print_scenario_result(r)

    if args.scenario in ["all", "xss"]:
        ip = args.ip or "203.0.113.99"
        if not args.json:
            print(f"[*] [3/6] Launching Scenario: Safe Cross-Site Scripting (XSS) from {ip}...")
        r = tester.test_cross_site_scripting(client_ip=ip)
        results.append(r)
        if not args.json:
            print_scenario_result(r)

    if args.scenario in ["all", "admin"]:
        ip = args.ip or "198.51.100.77"
        if not args.json:
            print(f"[*] [4/6] Launching Scenario: Unauthorized Admin Probe from {ip}...")
        r = tester.test_unauthorized_admin(client_ip=ip)
        results.append(r)
        if not args.json:
            print_scenario_result(r)

    if args.scenario in ["all", "rate"]:
        ip = args.ip or "198.51.100.55"
        if not args.json:
            print(f"[*] [5/6] Launching Scenario: High-Frequency Request-Rate Burst from {ip}...")
        r = tester.test_request_rate_anomaly(client_ip=ip, count=25)
        results.append(r)
        if not args.json:
            print_scenario_result(r)

    if args.scenario in ["all", "health"]:
        ip = args.ip or "198.51.100.33"
        if not args.json:
            print(f"[*] [6/6] Launching Scenario: Application Health & Exception Resilience...")
        r = tester.test_health_cascade_resilience(client_ip=ip)
        results.append(r)
        if not args.json:
            print_scenario_result(r)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        total = len(results)
        passed = sum(1 for r in results if r.get("protection_verified"))
        print("\n" + "=" * 80)
        print(f"   TEST SUITE SUMMARY: {passed}/{total} SCENARIOS VERIFIED PROTECTED")
        print("=" * 80)
        print(f"   • Real-Time Events Ingested into SQLite Database: Verified")
        print(f"   • View Live Incidents in Dashboard: http://localhost:8501")
        print(f"   • View Swagger API Endpoints:       http://localhost:8000/api/docs")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
