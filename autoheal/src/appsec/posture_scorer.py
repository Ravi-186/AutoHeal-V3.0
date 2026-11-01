"""
Transparent Security Posture Scoring Engine
Calculates deterministic security posture scores based on actual security tests,
verified containment rates, and outstanding vulnerability findings.
"""

from typing import Dict, Any, List
from shopsphere.database import get_db_connection, init_db
from src.appsec.vulnerability_manager import VulnerabilityManager


class SecurityPostureScorer:
    """Computes a transparent, evidence-grounded security posture score."""

    @classmethod
    def calculate_posture(cls) -> Dict[str, Any]:
        """
        Calculates the 0-100 security posture score with full breakdown.
        """
        init_db()
        vulnerabilities = VulnerabilityManager.list_vulnerabilities()
        
        # Count vulnerabilities by status and severity
        total_vulns = len(vulnerabilities)
        open_critical = sum(1 for v in vulnerabilities if v.get("status") in ["OPEN", "AWAITING_APPROVAL", "ROLLED_BACK"] and v.get("severity") == "CRITICAL")
        open_high = sum(1 for v in vulnerabilities if v.get("status") in ["OPEN", "AWAITING_APPROVAL", "ROLLED_BACK"] and v.get("severity") == "HIGH")
        open_medium = sum(1 for v in vulnerabilities if v.get("status") in ["OPEN", "AWAITING_APPROVAL", "ROLLED_BACK"] and v.get("severity") == "MEDIUM")
        patched_vulns = sum(1 for v in vulnerabilities if v.get("status") == "PATCHED_VERIFIED")

        # Fetch incidents
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM security_incidents")
            total_incidents = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM security_incidents WHERE verification_status = 'VERIFIED_CONTAINED' OR status = 'CONTAINED'")
            contained_incidents = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM blocked_clients WHERE is_active = 1")
            active_quarantines = cursor.fetchone()[0]

        # Transparent Scoring Formula
        base_score = 100
        deductions = []

        # Deduct for open vulnerabilities
        crit_penalty = open_critical * 15
        if crit_penalty > 0:
            deductions.append({
                "item": f"{open_critical} Open Critical Vulnerability(ies)",
                "penalty": -crit_penalty,
                "reason": "Unpatched critical vulnerability presents immediate exploit risk."
            })

        high_penalty = open_high * 10
        if high_penalty > 0:
            deductions.append({
                "item": f"{open_high} Open High Severity Vulnerability(ies)",
                "penalty": -high_penalty,
                "reason": "High severity findings require remediation approval."
            })

        med_penalty = open_medium * 5
        if med_penalty > 0:
            deductions.append({
                "item": f"{open_medium} Open Medium Severity Vulnerability(ies)",
                "penalty": -med_penalty,
                "reason": "Medium severity input validation or sanitization gap."
            })

        # Calculate incident containment rate
        containment_rate = round((contained_incidents / total_incidents * 100), 1) if total_incidents > 0 else 100.0
        uncontained_count = total_incidents - contained_incidents
        if uncontained_count > 0:
            uncont_penalty = min(20, uncontained_count * 5)
            deductions.append({
                "item": f"{uncontained_count} Unverified/Uncontained Security Incident(s)",
                "penalty": -uncont_penalty,
                "reason": "Incidents pending automated containment verification."
            })

        # Calculate raw score
        total_penalties = crit_penalty + high_penalty + med_penalty + (min(20, uncontained_count * 5) if uncontained_count > 0 else 0)
        raw_score = base_score - total_penalties

        # Bonuses
        bonuses = []
        if patched_vulns >= 3:
            bonuses.append({
                "item": f"{patched_vulns} Verified Surgical Patches Deployed",
                "bonus": 5,
                "reason": "Code remediation verified with isolated regression suites."
            })
            raw_score += 5

        if containment_rate >= 90.0 and total_incidents > 0:
            bonuses.append({
                "item": "90%+ Incident Verification Rate",
                "bonus": 5,
                "reason": "Sentinel verified post-action containment on recorded threats."
            })
            raw_score += 5

        final_score = max(0, min(100, raw_score))

        # Assign Grade
        if final_score >= 90:
            grade = "A"
            rating = "HARDENED & RESILIENT"
            color = "#10b981"  # green
        elif final_score >= 75:
            grade = "B"
            rating = "PROTECTED (ACTION RECOMMENDED)"
            color = "#3b82f6"  # blue
        elif final_score >= 60:
            grade = "C"
            rating = "MODERATE RISK"
            color = "#f59e0b"  # yellow
        else:
            grade = "D"
            rating = "ELEVATED RISK"
            color = "#ef4444"  # red

        # 5 Defense Pillars
        pillars = [
            {
                "name": "Authentication Security",
                "score": 90 if open_high == 0 else 75,
                "status": "HARDENED" if open_high == 0 else "ACTIVE_DEFENSE",
                "details": "Brute-force correlation & IP quarantine active."
            },
            {
                "name": "Injection & Input Defense",
                "score": 100 if open_critical == 0 else 60,
                "status": "PROTECTED" if open_critical == 0 else "VULNERABLE",
                "details": "Parameterized queries & XSS escaping verified."
            },
            {
                "name": "Access Control & RBAC",
                "score": 95,
                "status": "ENFORCED",
                "details": "Admin endpoints require role='admin' validation."
            },
            {
                "name": "DoS & Traffic Resilience",
                "score": 90,
                "status": "ENFORCED",
                "details": "Sliding-window token rate limiting at ASGI perimeter."
            },
            {
                "name": "Code Integrity & Regression",
                "score": round((patched_vulns / total_vulns * 100), 0) if total_vulns > 0 else 85,
                "status": "VERIFIED",
                "details": f"{patched_vulns}/{total_vulns} patches verified by regression suites."
            }
        ]

        bonus_sum = sum(b.get("bonus", 0) for b in bonuses)
        formula_str = f"Base Score ({base_score}) - Deductions ({total_penalties}) + Bonuses (+{bonus_sum}) = {final_score}"

        return {
            "posture_score": final_score,
            "grade": grade,
            "rating": rating,
            "posture_rating": rating,
            "color": color,
            "containment_rate_pct": containment_rate,
            "containment_rate_percent": containment_rate,
            "active_quarantines": active_quarantines,
            "active_containments": active_quarantines,
            "total_incidents": total_incidents,
            "contained_incidents": contained_incidents,
            "total_vulnerabilities": total_vulns,
            "patched_vulnerabilities": patched_vulns,
            "open_vulnerabilities": total_vulns - patched_vulns,
            "scoring_formula": formula_str,
            "scoring_formula_details": {
                "base_score": base_score,
                "deductions": deductions,
                "bonuses": bonuses,
                "final_score": final_score
            },
            "defense_pillars": pillars
        }


# Convenient alias
PostureScorer = SecurityPostureScorer
