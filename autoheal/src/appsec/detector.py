import re
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

from src.appsec.models import (
    record_security_event, create_security_incident,
    get_security_events, redact_sensitive_data
)

# --- Signatures for Web Attack Detection ---
SQLI_PATTERNS = [
    r"(?i)(\bUNION\s+(?:ALL\s+)?SELECT\b)",
    r"(?i)(\bOR\s+['\"0-9a-z]+\s*=\s*['\"0-9a-z]+)",
    r"(?i)(['\"]\s*OR\s*['\"]?[0-9a-z]+['\"]?\s*=\s*['\"]?[0-9a-z]+)",
    r"(?i)(--\s*$|\bDROP\s+TABLE\b|\bINSERT\s+INTO\b|\bDELETE\s+FROM\b)",
    r"(?i)(\bEXEC\s*\(|\bWAITFOR\s+DELAY\b|\bSLEEP\s*\(\d+\))",
    r"(?i)(\bBENCHMARK\s*\(\d+,\s*SHA1\()"
]

XSS_PATTERNS = [
    r"(?i)(<script[\s\S]*?>[\s\S]*?<\/script>)",
    r"(?i)(<script[\s\S]*?>)",
    r"(?i)(javascript\s*:)",
    r"(?i)(\bonerror\s*=)",
    r"(?i)(\bonload\s*=)",
    r"(?i)(\bonclick\s*=)",
    r"(?i)(<iframe[\s\S]*?>)",
    r"(?i)(<img\s+[^>]*?onerror\s*=)",
    r"(?i)(<svg\s+[^>]*?onload\s*=)"
]


class DetectionResult:
    def __init__(
        self,
        triggered: bool,
        rule_id: str = "",
        category: str = "",
        severity: str = "INFO",
        confidence: float = 0.0,
        summary: str = "",
        evidence: Optional[Dict[str, Any]] = None,
        why_flagged: str = "",
        false_positive_considerations: str = "",
        recommended_action: str = "ALLOW",
        status: str = "ATTEMPTED",
        event_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        model_score: Optional[float] = None,
        ml_anomaly_detected: bool = False,
        linked_event_ids: Optional[List[str]] = None
    ):
        self.triggered = triggered
        self.rule_id = rule_id
        self.category = category
        self.severity = severity
        self.confidence = confidence
        self.summary = summary
        self.evidence = evidence or {}
        self.why_flagged = why_flagged
        self.false_positive_considerations = false_positive_considerations
        self.recommended_action = recommended_action
        self.status = status
        self.event_id = event_id
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.model_score = model_score
        self.ml_anomaly_detected = ml_anomaly_detected
        self.linked_event_ids = linked_event_ids or []
        if self.linked_event_ids and "linked_event_ids" not in self.evidence:
            self.evidence["linked_event_ids"] = self.linked_event_ids

    def to_dict(self) -> Dict[str, Any]:
        return {
            "triggered": self.triggered,
            "rule_id": self.rule_id,
            "category": self.category,
            "severity": self.severity,
            "confidence": self.confidence,
            "summary": self.summary,
            "evidence": self.evidence,
            "why_flagged": self.why_flagged,
            "false_positive_considerations": self.false_positive_considerations,
            "recommended_action": self.recommended_action,
            "status": self.status,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "model_score": self.model_score,
            "ml_anomaly_detected": self.ml_anomaly_detected,
            "linked_event_ids": self.linked_event_ids
        }


class AppSecDetector:
    """Modular application security detection engine with explicit rules and telemetry correlation."""

    @staticmethod
    def inspect_payload_for_sqli(payload: str) -> Optional[str]:
        """Detects SQL injection signatures in a given string."""
        decoded = urllib.parse.unquote_plus(urllib.parse.unquote(payload))
        for pat in SQLI_PATTERNS:
            match = re.search(pat, decoded)
            if match:
                return match.group(0)
        return None

    @staticmethod
    def inspect_payload_for_xss(payload: str) -> Optional[str]:
        """Detects Cross-Site Scripting signatures in a given string."""
        decoded = urllib.parse.unquote_plus(urllib.parse.unquote(payload))
        for pat in XSS_PATTERNS:
            match = re.search(pat, decoded)
            if match:
                return match.group(0)
        return None

    @classmethod
    def analyze_live_request(
        cls,
        client_ip: str,
        method: str,
        path: str,
        query_string: str = "",
        headers: Optional[Dict[str, str]] = None,
        body_sample: str = ""
    ) -> DetectionResult:
        """
        Inspects an incoming HTTP request in real time for injection attacks,
        malicious query strings, or unauthorized admin probes.
        """
        combined_payload = f"{path}?{query_string} {body_sample}"

        # 1. Check for SQL Injection (Rule INJ-001)
        sqli_match = cls.inspect_payload_for_sqli(combined_payload)
        if sqli_match:
            return DetectionResult(
                triggered=True,
                rule_id="INJ-001",
                category="Injection",
                severity="CRITICAL",
                confidence=0.98,
                summary=f"SQL injection attempt detected on {method} {path}",
                evidence={
                    "client_ip": client_ip,
                    "matched_pattern": sqli_match,
                    "target_path": path,
                    "query_string": redact_sensitive_data(query_string)
                },
                why_flagged=f"Request contains SQL syntax fragment '{sqli_match}' violating parameter validation.",
                false_positive_considerations="Uncommon in standard shopping queries; legitimate names with apostrophes are safely handled unless containing SQL operators.",
                recommended_action="BLOCK_IP",
                status="ATTEMPTED_BLOCKED"
            )

        # 2. Check for Cross-Site Scripting (Rule XSS-001)
        xss_match = cls.inspect_payload_for_xss(combined_payload)
        if xss_match:
            return DetectionResult(
                triggered=True,
                rule_id="XSS-001",
                category="Cross-Site Scripting (XSS)",
                severity="HIGH",
                confidence=0.94,
                summary=f"Cross-site scripting (XSS) payload detected on {method} {path}",
                evidence={
                    "client_ip": client_ip,
                    "matched_pattern": xss_match,
                    "target_path": path
                },
                why_flagged=f"Request contains executable script or event handler payload '{xss_match}'.",
                false_positive_considerations="Code-related forum submissions or technical blog posts might contain tags, but shopping search terms never require executable tags.",
                recommended_action="BLOCK_IP",
                status="ATTEMPTED_BLOCKED"
            )

        # 3. Check for Unauthorized Admin Probing (Rule AUTH-002)
        if "/admin" in path.lower() and not path.startswith("/api/docs"):
            auth_header = (headers or {}).get("authorization", "")
            token = auth_header.replace("Bearer ", "").strip() if auth_header else ""
            is_valid_admin = False
            if token and token.startswith("token_admin_"):
                try:
                    from shopsphere.services import UserService
                    user = UserService.get_by_token(token)
                    if user and user.get("role") == "admin":
                        is_valid_admin = True
                except Exception:
                    pass
            if not is_valid_admin:
                return DetectionResult(
                    triggered=True,
                    rule_id="AUTH-002",
                    category="Privilege Escalation",
                    severity="HIGH",
                    confidence=0.99,
                    summary=f"Unauthorized access probe against administrative endpoint {path}",
                    evidence={
                        "client_ip": client_ip,
                        "target_endpoint": path,
                        "method": method,
                        "has_auth_header": bool(auth_header)
                    },
                    why_flagged="Unauthenticated or unprivileged request made directly to internal administrative API.",
                    false_positive_considerations="Legitimate administrators whose sessions recently expired.",
                    recommended_action="BLOCK_IP",
                    status="UNAUTHORIZED_ACCESS"
                )

        return DetectionResult(triggered=False)

    @classmethod
    def correlate_telemetry_window(cls, window_seconds: int = 60) -> List[DetectionResult]:
        """
        Sliding-window correlation across recent security events.
        Delegates to Component 2: AppSecCorrelationEngine.
        """
        from src.appsec.correlation_engine import AppSecCorrelationEngine
        engine = AppSecCorrelationEngine(window_seconds=window_seconds)
        return engine.correlate_events(window_seconds=window_seconds)
