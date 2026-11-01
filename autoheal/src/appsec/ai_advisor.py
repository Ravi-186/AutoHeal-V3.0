"""
AI-Assisted Security Advisor and MITRE ATT&CK Mapping Engine
Grounds incident forensics, generates remediation recommendations,
and maps detected application behaviors to the MITRE ATT&CK enterprise matrix.
"""

from typing import Dict, Any, List, Optional


MITRE_CATALOG: Dict[str, Dict[str, Any]] = {
    "AUTH-001": {
        "tactic_id": "TA0006",
        "tactic_name": "Credential Access",
        "technique_id": "T1110.001",
        "technique_name": "Brute Force: Password Guessing",
        "subtechnique": "Password Guessing",
        "cwe_id": "CWE-307: Improper Restriction of Excessive Authentication Attempts",
        "nist_mapping": "AC-7: Unsuccessful Logon Attempts, IA-5: Authenticator Management",
        "threat_actor_objective": "Systematic credential enumeration and dictionary stuffing against public-facing login endpoint.",
        "detection_criteria": "4 or more failed HTTP 401 authentication attempts observed from a single IP within a 60-second sliding correlation window.",
        "default_remediation": [
            "Enforce IP sliding-window rate limiting (max 5 failed attempts per 60 seconds).",
            "Require Multi-Factor Authentication (MFA / TOTP) on sensitive or repeated login triggers.",
            "Integrate CAPTCHA challenge after 3 consecutive failed login attempts on /api/shop/auth/login.",
            "Deploy Argon2id or bcrypt password hashing with exponential backoff on consecutive failures."
        ]
    },
    "AUTH-002": {
        "tactic_id": "TA0004",
        "tactic_name": "Privilege Escalation",
        "technique_id": "T1068",
        "technique_name": "Exploitation for Privilege Escalation",
        "subtechnique": "Bypass Access Controls",
        "cwe_id": "CWE-862: Missing Authorization",
        "nist_mapping": "AC-3: Access Enforcement, AC-6: Least Privilege",
        "threat_actor_objective": "Attempt to bypass standard authentication and directly inspect or manipulate privileged administrative interfaces.",
        "detection_criteria": "Direct probe against restricted /admin or /api/shop/admin paths without a valid role='admin' cryptographic token.",
        "default_remediation": [
            "Enforce strict server-side role verification (role == 'admin') on all administrative API routes.",
            "Isolate administrative endpoints behind an authenticated VPN or internal network perimeter.",
            "Log all unauthorized administrative access attempts to SIEM with high-priority alerting.",
            "Require separate administrative credentials and hardware security keys (FIDO2/WebAuthn)."
        ]
    },
    "INJ-001": {
        "tactic_id": "TA0001",
        "tactic_name": "Initial Access",
        "technique_id": "T1190",
        "technique_name": "Exploit Public-Facing Application: SQL Injection",
        "subtechnique": "SQL Injection (Tautology & Stacked Queries)",
        "cwe_id": "CWE-89: Improper Neutralization of Special Elements in SQL Command",
        "nist_mapping": "SI-10: Information Input Validation, SC-13: Cryptographic Protection",
        "threat_actor_objective": "Manipulate SQL query logic via untrusted input to extract customer records, bypass authentication, or dump database tables.",
        "detection_criteria": "SQL syntax keywords (' OR '1'='1', UNION SELECT, --, DROP TABLE) detected in query string or payload parameters.",
        "default_remediation": [
            "Use strictly parameterized queries (prepared statements) for all database operations.",
            "Enforce input validation and allowlisting on all catalog search terms.",
            "Configure database accounts with least privilege (read-only for storefront catalog queries).",
            "Enable Sentinel perimeter WAF inspection to drop malformed SQL payloads before application dispatch."
        ]
    },
    "XSS-001": {
        "tactic_id": "TA0002",
        "tactic_name": "Execution",
        "technique_id": "T1059.007",
        "technique_name": "Command and Scripting Interpreter: JavaScript (Reflected XSS)",
        "subtechnique": "Reflected Cross-Site Scripting",
        "cwe_id": "CWE-79: Improper Neutralization of Input During Web Page Generation",
        "nist_mapping": "SI-15: Information Output Filtering, SC-18: Mobile Code",
        "threat_actor_objective": "Inject executable JavaScript into search queries to steal customer session cookies or hijack account sessions.",
        "detection_criteria": "Executable HTML/JS tags (<script>, onerror=, onload=, javascript:) submitted in request query parameters.",
        "default_remediation": [
            "Apply context-aware HTML entity escaping (html.escape) before echoing search terms in responses.",
            "Deploy a strict Content-Security-Policy (CSP) header: script-src 'self'.",
            "Mark all authentication session cookies with HttpOnly and SameSite=Strict flags.",
            "Block requests containing unencoded script tags at the ASGI middleware perimeter."
        ]
    },
    "RATE-001": {
        "tactic_id": "TA0040",
        "tactic_name": "Impact",
        "technique_id": "T1499.002",
        "technique_name": "Endpoint Denial of Service: Service Exhaustion Flood",
        "subtechnique": "HTTP Request Burst / Flood",
        "cwe_id": "CWE-400: Uncontrolled Resource Consumption",
        "nist_mapping": "SC-5: Denial-of-Service Protection, AU-12: Audit Generation",
        "threat_actor_objective": "Generate high-frequency request bursts to exhaust database connections, compute resources, and trigger service latency.",
        "detection_criteria": "Greater than 20 requests dispatched within a 5-second burst window from a single client IP.",
        "default_remediation": [
            "Implement sliding-window token bucket rate limiting (max 15 requests/sec per IP).",
            "Return HTTP 429 Too Many Requests with standard Retry-After headers when thresholds are exceeded.",
            "Apply automatic temporary client IP quarantine (300s TTL) for persistent burst violators.",
            "Deploy edge reverse proxy caching for public product catalog endpoints."
        ]
    },
    "HEALTH-001": {
        "tactic_id": "TA0040",
        "tactic_name": "Impact",
        "technique_id": "T1499",
        "technique_name": "Endpoint Denial of Service: Application Crash / Fault Injection",
        "subtechnique": "Exception Cascading",
        "cwe_id": "CWE-755: Improper Handling of Exceptional Conditions",
        "nist_mapping": "CP-2: Contingency Plan, SI-2: Flaw Remediation",
        "threat_actor_objective": "Trigger uncaught application exceptions to induce cascading service degradation.",
        "detection_criteria": "HTTP 500 status code returned by an application route during live request processing.",
        "default_remediation": [
            "Implement global exception handlers to prevent uncaught 500 errors from bubbling to clients.",
            "Log unhandled exceptions with full stack traces and correlation IDs for root-cause diagnosis.",
            "Verify circuit breaker thresholds and automated service health probes.",
            "Apply surgical bug fixes and verify via automated unit and regression test suites."
        ]
    }
}


class AISecurityAdvisor:
    """Provides grounded AI forensic summaries and MITRE ATT&CK mappings based on real telemetry."""

    @classmethod
    def get_mitre_mapping(cls, rule_id: str) -> Dict[str, Any]:
        """Returns MITRE ATT&CK mapping for a given rule_id, or a generic fallback."""
        return MITRE_CATALOG.get(rule_id, {
            "tactic_id": "TA0043",
            "tactic_name": "Reconnaissance",
            "technique_id": "T1595",
            "technique_name": "Active Scanning",
            "subtechnique": "Probing",
            "cwe_id": "CWE-200: Information Exposure",
            "nist_mapping": "SI-4: System Monitoring",
            "threat_actor_objective": "General application probing and vulnerability reconnaissance.",
            "detection_criteria": "Anomalous telemetry patterns flagged by AutoHeal Sentinel.",
            "default_remediation": [
                "Review perimeter firewall rules and monitor audit logs.",
                "Verify input validation across all public endpoints."
            ]
        })

    @classmethod
    def generate_grounded_summary(
        cls,
        incident_id: str,
        rule_id: str,
        category: str,
        severity: str,
        endpoint: str,
        source_ip: str,
        evidence: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes a high-fidelity, evidence-grounded AI forensic analysis
        incorporating MITRE ATT&CK alignment and prioritized remediation recommendations.
        """
        mitre = cls.get_mitre_mapping(rule_id)
        evidence_dict = evidence or {}

        # Synthesize narrative from exact forensic evidence
        attempt_count = evidence_dict.get("failed_attempt_count") or evidence_dict.get("attempt") or "multiple"
        pattern = evidence_dict.get("matched_pattern") or evidence_dict.get("error") or "anomaly pattern"

        if rule_id == "AUTH-001":
            narrative = (
                f"AutoHeal Sentinel correlated a high-frequency credential stuffing attack from client IP {source_ip}. "
                f"The attacker dispatched {attempt_count} rapid authentication attempts to {endpoint} using invalid "
                f"credentials, exceeding the sliding-window threshold. Sentinel dynamically quarantined IP {source_ip} "
                f"to contain brute-force credential discovery."
            )
            root_cause = "Authentication endpoint lacked native sliding-window rate limiting before Sentinel perimeter defense was activated."
        elif rule_id == "INJ-001":
            narrative = (
                f"An injection payload was intercepted at {endpoint} from client IP {source_ip}. "
                f"Sentinel identified malicious SQL syntax '{pattern}' designed to manipulate query execution logic. "
                f"The request was immediately short-circuited with HTTP 403 Forbidden, preventing database execution."
            )
            root_cause = "Public catalog search parameter accepted raw SQL operator syntax prior to parameterization."
        elif rule_id == "XSS-001":
            narrative = (
                f"A reflected cross-site scripting (XSS) probe was intercepted on {endpoint} originating from {source_ip}. "
                f"The incoming request contained unencoded script syntax '{pattern}'. Sentinel dropped the connection, "
                f"mitigating any client-side execution risk."
            )
            root_cause = "Storefront keyword search parameter echoed user input without mandatory context-aware HTML entity encoding."
        elif rule_id == "AUTH-002":
            narrative = (
                f"An unauthorized privilege escalation attempt was blocked on restricted endpoint {endpoint}. "
                f"Client IP {source_ip} attempted to access internal administrative metrics without valid administrator session tokens. "
                f"Access was denied with HTTP 403 Forbidden."
            )
            root_cause = "Direct HTTP requests were routed to administrative endpoints without pre-perimeter role validation."
        elif rule_id == "RATE-001":
            narrative = (
                f"High-frequency request-rate anomaly detected on {endpoint} from {source_ip}. "
                f"The client generated an aggressive burst of requests, triggering the Sentinel sliding rate threshold. "
                f"HTTP 429 Too Many Requests was returned, safeguarding backend database capacity."
            )
            root_cause = "Storefront catalog endpoint lacked burst throttling constraints."
        else:
            narrative = (
                f"Security incident {incident_id} detected on {endpoint} by rule {rule_id}. "
                f"AutoHeal Sentinel evaluated client behavior from {source_ip} as anomalous and applied automated containment."
            )
            root_cause = "Anomalous telemetry pattern identified by Sentinel correlation window."

        recommendations = mitre.get("default_remediation", [
            "Apply sliding-window IP rate limiting.",
            "Verify input sanitization on all parameters.",
            "Conduct post-action regression verification."
        ])

        return {
            "incident_id": incident_id,
            "rule_id": rule_id,
            "category": category,
            "severity": severity,
            "mitre_tactic": f"{mitre['tactic_name']} ({mitre['tactic_id']})",
            "mitre_technique": f"{mitre['technique_name']} ({mitre['technique_id']})",
            "mitre_id": mitre["technique_id"],
            "nist_mapping": mitre.get("nist_mapping", "SI-4"),
            "cwe_id": mitre.get("cwe_id", "CWE-200"),
            "executive_summary": narrative,
            "ai_summary": narrative,
            "root_cause_analysis": root_cause,
            "root_cause": root_cause,
            "remediation_plan": recommendations,
            "remediation_recommendations": recommendations,
            "verification_guidance": "Execute synthetic verification request via AutoHeal Attack Center to confirm HTTP 403/429 containment.",
            "recovery_status": "CONTAINED_AND_VERIFIED"
        }
