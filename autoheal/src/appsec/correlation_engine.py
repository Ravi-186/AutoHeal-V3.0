"""
Component 2: Log Correlation Engine
Groups raw and flagged security telemetry into structured, evidence-backed security incidents
using configurable sliding time windows, multi-step pattern detection, and duplicate prevention.
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from src.appsec.models import (
    get_security_events, upsert_security_incident, find_active_incident,
    get_security_incident, redact_sensitive_data
)
from src.appsec.detector import DetectionResult, AppSecDetector


class AppSecCorrelationEngine:
    """
    Modular Log Correlation Engine that processes security events within a configurable
    sliding window, detects single-stage and multi-step attack patterns, preserves linked
    event IDs, and idempotently correlates incidents without duplication.
    """

    def __init__(self, window_seconds: int = 60, auth_failure_threshold: int = 4, rate_threshold: int = 25):
        self.window_seconds = window_seconds
        self.auth_failure_threshold = auth_failure_threshold
        self.rate_threshold = rate_threshold

    def correlate_events(self, window_seconds: Optional[int] = None) -> List[DetectionResult]:
        """
        Gathers recent security events within the sliding window and identifies:
        1. Rule AUTH-001: Burst of authentication failures (Credential stuffing / Brute force).
        2. Rule RATE-001: High-frequency request surges (Denial of Service / Scraping).
        3. Rule CORR-001: Multi-step attack sequences (Failed logins followed by injection or admin probes).
        4. Rule HEALTH-001: Clustered unhandled server exceptions (Reliability / Degradation).
        """
        win_sec = window_seconds or self.window_seconds
        recent_events = get_security_events(limit=250, since_seconds=win_sec)
        if not recent_events:
            return []

        # Group events by client IP
        events_by_ip: Dict[str, List[Dict[str, Any]]] = {}
        for ev in recent_events:
            ip = ev.get("client_ip") or "127.0.0.1"
            events_by_ip.setdefault(ip, []).append(ev)

        correlated_detections: List[DetectionResult] = []

        # ---------------------------------------------------------------------
        # 1. Rule AUTH-001: Credential Stuffing / Brute Force
        # ---------------------------------------------------------------------
        for ip, events in events_by_ip.items():
            auth_failures = [e for e in events if e.get("event_type") == "AUTH_FAILURE"]
            if len(auth_failures) >= self.auth_failure_threshold:
                target_users = list(set(e.get("user_id_or_session") or "unknown" for e in auth_failures))
                linked_ids = [e.get("event_id") for e in auth_failures if e.get("event_id")]
                
                # Check ML anomaly score if available
                ml_score, ml_threat = self._evaluate_ml_features(
                    failed_logins=len(auth_failures),
                    connections=len(events),
                    bytes_sent=sum(len(str(e.get("details", ""))) for e in events)
                )

                correlated_detections.append(DetectionResult(
                    triggered=True,
                    rule_id="AUTH-001",
                    category="Credential Stuffing / Brute Force",
                    severity="HIGH",
                    confidence=max(0.95, round(ml_score, 2)) if ml_threat else 0.95,
                    summary=f"Burst of {len(auth_failures)} failed logins detected from IP {ip}",
                    evidence={
                        "client_ip": ip,
                        "failed_attempt_count": len(auth_failures),
                        "targeted_accounts": target_users[:5],
                        "linked_event_ids": linked_ids,
                        "window_seconds": win_sec,
                        "ml_model_score": ml_score,
                        "ml_anomaly_detected": ml_threat
                    },
                    why_flagged=f"Exceeded threshold of {self.auth_failure_threshold} failed authentication attempts within {win_sec}s sliding correlation window.",
                    false_positive_considerations="Legitimate user forgetting password; multiple distinct usernames or high frequency indicates automated brute force.",
                    recommended_action="BLOCK_IP",
                    status="ATTEMPTED"
                ))

        # ---------------------------------------------------------------------
        # 2. Rule RATE-001: Request-Rate Anomaly / Scraping
        # ---------------------------------------------------------------------
        for ip, events in events_by_ip.items():
            if len(events) >= self.rate_threshold:
                linked_ids = [e.get("event_id") for e in events[:30] if e.get("event_id")]
                correlated_detections.append(DetectionResult(
                    triggered=True,
                    rule_id="RATE-001",
                    category="Denial of Service / Scraping",
                    severity="MEDIUM",
                    confidence=0.92,
                    summary=f"High-frequency request surge ({len(events)} requests in {win_sec}s) from IP {ip}",
                    evidence={
                        "client_ip": ip,
                        "request_count": len(events),
                        "window_seconds": win_sec,
                        "linked_event_ids": linked_ids
                    },
                    why_flagged=f"Exceeded request rate baseline of {self.rate_threshold} requests within {win_sec}s sliding correlation window.",
                    false_positive_considerations="Aggressive client-side prefetching or shared corporate NAT gateway.",
                    recommended_action="RATE_LIMIT",
                    status="ATTEMPTED"
                ))

        # ---------------------------------------------------------------------
        # 3. Rule CORR-001: Multi-Step Attack Sequence
        # (Failed logins followed by unauthorized admin probe or injection)
        # ---------------------------------------------------------------------
        for ip, events in events_by_ip.items():
            has_auth_fail = any(e.get("event_type") == "AUTH_FAILURE" for e in events)
            has_probe_or_inj = any(
                ("admin" in (e.get("path") or "").lower() and e.get("status_code") in [401, 403]) or
                "INJ" in (e.get("event_type") or "") or
                "XSS" in (e.get("event_type") or "")
                for e in events
            )
            if has_auth_fail and has_probe_or_inj:
                linked_ids = [e.get("event_id") for e in events if e.get("event_id")]
                correlated_detections.append(DetectionResult(
                    triggered=True,
                    rule_id="CORR-001",
                    category="Multi-Step Attack Sequence",
                    severity="CRITICAL",
                    confidence=0.98,
                    summary=f"Multi-step intrusion sequence: authentication probing followed by administrative/injection probes from IP {ip}",
                    evidence={
                        "client_ip": ip,
                        "event_count": len(events),
                        "attack_stages": ["Credential Access (TA0006)", "Privilege Escalation / Exploitation (TA0004)"],
                        "linked_event_ids": linked_ids,
                        "window_seconds": win_sec
                    },
                    why_flagged="Correlated progression of distinct attack stages (reconnaissance -> credential probing -> privilege escalation).",
                    false_positive_considerations="Extremely unlikely in benign user traffic.",
                    recommended_action="BLOCK_IP",
                    status="ATTEMPTED"
                ))

        # ---------------------------------------------------------------------
        # 4. Rule HEALTH-001: Service Degradation Cluster
        # ---------------------------------------------------------------------
        server_errors = [e for e in recent_events if (e.get("status_code") or 200) >= 500 or e.get("event_type") == "SERVICE_HEALTH_ERROR"]
        if len(server_errors) >= 3:
            affected_paths = list(set(e.get("path") or "-" for e in server_errors))
            linked_ids = [e.get("event_id") for e in server_errors if e.get("event_id")]
            correlated_detections.append(DetectionResult(
                triggered=True,
                rule_id="HEALTH-001",
                category="Reliability / Health Degradation",
                severity="HIGH",
                confidence=0.96,
                summary=f"Cluster of {len(server_errors)} unhandled backend exceptions detected",
                evidence={
                    "error_count": len(server_errors),
                    "affected_endpoints": affected_paths,
                    "linked_event_ids": linked_ids
                },
                why_flagged="Consecutive internal server errors indicate unexpected backend failure or unhandled crash.",
                false_positive_considerations="Transient database connection pool spike during cold start.",
                recommended_action="RECOVER_SERVICE",
                status="SERVICE_DEGRADED"
            ))

        return correlated_detections

    def process_and_persist_incidents(self, window_seconds: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Runs correlation, applies idempotent deduplication via upsert_security_incident,
        and returns the persisted incident dossiers with linked event IDs.
        """
        detections = self.correlate_events(window_seconds=window_seconds)
        incidents = []

        for d in detections:
            client_ip = d.evidence.get("client_ip") or "127.0.0.1"
            endpoints = d.evidence.get("affected_endpoints") or [d.evidence.get("target_path", "/api/shop")]

            incident_id = upsert_security_incident(
                rule_id=d.rule_id,
                title=f"AutoHeal AppSec: {d.summary}",
                category=d.category,
                severity=d.severity,
                summary=d.summary,
                source_ip=client_ip,
                evidence=d.evidence,
                affected_endpoints=endpoints,
                impact_actual="Intercepted and correlated by AutoHeal Log Correlation Engine.",
                impact_potential=f"High risk of {d.category} compromising application availability or data confidentiality.",
                mitigation_actions=[{
                    "action": d.recommended_action,
                    "target": client_ip,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }],
                confidence=d.confidence,
                status="UNDER_INVESTIGATION",
                remediation_details=f"Correlated via rule {d.rule_id} across sliding window.",
                verification_status="PENDING",
                window_seconds=window_seconds or self.window_seconds
            )
            inc = get_security_incident(incident_id)
            if inc:
                incidents.append(inc)

        return incidents

    @staticmethod
    def _evaluate_ml_features(failed_logins: int, connections: int, bytes_sent: int) -> tuple[float, bool]:
        """
        Queries the verified Random Forest DetectionModel if available.
        Returns (probability_score, is_anomaly_detected).
        """
        try:
            from src.detection.model import DetectionModel
            model = DetectionModel()
            features = {
                "failed_logins": failed_logins,
                "connections": connections,
                "bytes_sent": bytes_sent,
                "bytes_received": 1024,
                "dns_requests": 1,
                "cpu_usage": 15.0,
                "mem_usage": 25.0
            }
            is_threat, score = model.predict(features)
            return score, is_threat
        except Exception:
            # Fallback if model joblib is not accessible
            heuristic = failed_logins >= 4 or connections >= 25
            return (0.85 if heuristic else 0.15), heuristic
