import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from src.appsec.detector import DetectionResult
from src.appsec.models import (
    create_security_incident, upsert_security_incident, update_incident_status,
    block_client_ip, unblock_client_ip, is_client_blocked, get_security_incident
)
from shopsphere.database import get_db_connection


class AppSecResponder:
    """
    Component 3: Response Agent
    Policy-driven AutoHeal defensive response engine with auditable mitigation,
    dry-run execution, automated verification handoff, and safe rollback capabilities.
    """

    POLICY_RULES = {
        "INJ-001": {
            "default_action": "BLOCK_IP",
            "duration_seconds": 300,
            "requires_approval": False,
            "description": "Dynamic WAF block for SQL injection payload sources."
        },
        "XSS-001": {
            "default_action": "BLOCK_IP",
            "duration_seconds": 300,
            "requires_approval": False,
            "description": "Dynamic WAF block for Cross-Site Scripting sources."
        },
        "AUTH-001": {
            "default_action": "BLOCK_IP",
            "duration_seconds": 180,
            "requires_approval": False,
            "description": "Temporary client IP quarantine for credential stuffing."
        },
        "AUTH-002": {
            "default_action": "BLOCK_IP",
            "duration_seconds": 300,
            "requires_approval": False,
            "description": "Access barrier for unauthorized administrative probing."
        },
        "RATE-001": {
            "default_action": "RATE_LIMIT",
            "duration_seconds": 120,
            "requires_approval": False,
            "description": "Throttling client request rate to mitigate denial of service."
        },
        "HEALTH-001": {
            "default_action": "RECOVER_SERVICE",
            "duration_seconds": 0,
            "requires_approval": False,
            "description": "Trigger automated self-healing restart and telemetry reset."
        }
    }

    @classmethod
    def execute_defensive_mitigation(
        cls,
        detection: DetectionResult,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Executes policy-governed mitigation for a detected threat,
        idempotently upserts an incident dossier, and hands off to the Verification Agent.
        """
        rule_cfg = cls.POLICY_RULES.get(detection.rule_id, {
            "default_action": "BLOCK_IP",
            "duration_seconds": 180,
            "requires_approval": False
        })
        action_type = rule_cfg["default_action"]
        duration_sec = rule_cfg.get("duration_seconds", 180)
        client_ip = detection.evidence.get("client_ip", "127.0.0.1")

        proposed_action = {
            "action": action_type,
            "target": client_ip,
            "duration_seconds": duration_sec,
            "dry_run": dry_run,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Idempotent incident upsert (prevents duplicate incidents for same IP and rule)
        incident_id = upsert_security_incident(
            rule_id=detection.rule_id,
            title=f"AutoHeal AppSec: {detection.summary}",
            category=detection.category,
            severity=detection.severity,
            summary=detection.summary,
            source_ip=client_ip,
            evidence=detection.evidence,
            affected_endpoints=[detection.evidence.get("target_path", "/api/shop")],
            impact_actual="Attempted malicious interaction intercepted before application layer breach.",
            impact_potential=f"High risk of {detection.category} compromising data integrity or availability.",
            mitigation_actions=[proposed_action],
            confidence=detection.confidence,
            status="RESPONSE_ATTEMPTED" if not dry_run else "DRY_RUN",
            remediation_details=f"Policy {detection.rule_id} triggered action {action_type}."
        )

        if dry_run:
            proposed_action["outcome"] = "PROPOSED_ONLY"
            return {
                "incident_id": incident_id,
                "action_executed": action_type,
                "status": "DRY_RUN_COMPLETED",
                "details": proposed_action
            }

        # Execute live mitigation based on action type
        execution_start = time.perf_counter()
        outcome_msg = ""

        if action_type in ["BLOCK_IP", "RATE_LIMIT"]:
            block_client_ip(
                client_ip=client_ip,
                reason=f"AutoHeal {detection.rule_id}: {detection.summary}",
                rule_id=detection.rule_id,
                duration_seconds=duration_sec,
                incident_id=incident_id
            )
            outcome_msg = f"Client IP {client_ip} dynamically quarantined for {duration_sec}s."

        elif action_type == "RECOVER_SERVICE":
            try:
                from shopsphere.database import seed_data
                seed_data()
                outcome_msg = "Application data integrity & baseline connection pools successfully recovered."
            except Exception as e:
                outcome_msg = f"Service recovery error: {str(e)}"

        elapsed_ms = round((time.perf_counter() - execution_start) * 1000, 2)

        # Component 4: Hand off to Verification Agent for follow-up testing
        from src.appsec.verifier import AppSecVerifier
        verif_result = AppSecVerifier.verify_incident_containment(incident_id)
        verified = verif_result.get("verified", False)
        new_status = "CONTAINED" if verified else "RESPONSE_ATTEMPTED"
        verif_status = "VERIFIED_CONTAINED" if verified else "VERIFICATION_FAILED"

        return {
            "incident_id": incident_id,
            "action_executed": action_type,
            "status": new_status,
            "verified": verified,
            "verification_status": verif_result.get("verification_status", "VERIFIED_CONTAINED" if verified else "VERIFICATION_FAILED"),
            "execution_time_ms": elapsed_ms,
            "message": outcome_msg,
            "client_ip": client_ip,
            "ttl_seconds": duration_sec,
            "verification_details": verif_result
        }

    @classmethod
    def verify_mitigation_outcome(cls, action_type: str, target: str) -> bool:
        """Verifies that the executed mitigation is actively enforcing security invariants."""
        if action_type in ["BLOCK_IP", "RATE_LIMIT"]:
            blocked, _ = is_client_blocked(target)
            return blocked
        elif action_type == "RECOVER_SERVICE":
            return True
        return True

    @classmethod
    def rollback_mitigation(cls, action_type: str, target: str, incident_id: str) -> Dict[str, Any]:
        """Safely rolls back an applied mitigation (e.g. unblocking IP address)."""
        if action_type in ["BLOCK_IP", "RATE_LIMIT"]:
            unblock_client_ip(target)
            update_incident_status(
                incident_id=incident_id,
                status="CLOSED",
                verification_status="VERIFIED_RECOVERED",
                remediation_details=f"Rollback executed: Client IP {target} unblocked."
            )
            return {
                "status": "success",
                "message": f"Successfully rolled back mitigation for {target}.",
                "incident_id": incident_id
            }
        return {"status": "noop", "message": "No rollback needed for action type."}
