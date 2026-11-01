import time
import secrets
import json
from collections import defaultdict
from typing import Callable, Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from src.appsec.models import (
    record_security_event, is_client_blocked, redact_sensitive_data,
    get_security_events
)
from src.appsec.detector import AppSecDetector, DetectionResult
from src.appsec.responder import AppSecResponder


class AppSecProtectionMiddleware(BaseHTTPMiddleware):
    """
    Real-time defensive middleware that inspects, throttles, and protects
    ShopSphere from injection, unauthorized probes, request-rate bursts, and credential stuffing.
    """

    # In-memory sliding-window request rate tracker: client_ip -> list of timestamps
    _rate_tracker: Dict[str, List[float]] = defaultdict(list)
    RATE_LIMIT_WINDOW = 8.0  # seconds
    RATE_LIMIT_MAX_REQUESTS = 15  # requests per window

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "127.0.0.1"

        # Allow test client IP override for authorized localhost test simulations
        forwarded = request.headers.get("X-Forwarded-For") or request.headers.get("X-Client-IP")
        if forwarded and client_ip in ["127.0.0.1", "::1", "localhost", "testclient"]:
            client_ip = forwarded.split(",")[0].strip()

        correlation_id = request.headers.get("X-Correlation-ID", f"corr-{secrets.token_hex(4)}")
        path = request.url.path
        method = request.method
        query_string = request.url.query

        # Exclude static assets and docs from heavy inspection
        if any(path.startswith(prefix) for prefix in ["/static", "/css", "/js", "/favicon.ico"]):
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response

        # 1. Check if Client IP is actively quarantined in blocklist
        blocked, block_info = is_client_blocked(client_ip)
        if blocked and not path.startswith("/api/security/unblock"):
            record_security_event(
                client_ip=client_ip,
                method=method,
                path=path,
                status_code=403,
                event_type="BLOCKED_IP_ACCESS",
                severity="HIGH",
                correlation_id=correlation_id,
                details=block_info,
                action_taken="QUARANTINED"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Access Blocked by AutoHeal AppSec Sentinel",
                    "reason": block_info.get("reason", "Malicious activity detected"),
                    "rule_id": block_info.get("rule_id", "POLICY-001"),
                    "incident_id": block_info.get("incident_id"),
                    "expires_at": block_info.get("expires_at"),
                    "correlation_id": correlation_id
                },
                headers={"X-Correlation-ID": correlation_id}
            )

        # 2. Check Sliding-Window Rate Limit (Rule RATE-001)
        now = time.time()
        timestamps = self._rate_tracker[client_ip]
        timestamps = [t for t in timestamps if now - t <= self.RATE_LIMIT_WINDOW]
        timestamps.append(now)
        self._rate_tracker[client_ip] = timestamps

        if len(timestamps) > self.RATE_LIMIT_MAX_REQUESTS and not path.startswith("/api/security"):
            detection = DetectionResult(
                triggered=True,
                rule_id="RATE-001",
                category="Denial of Service / Scraping",
                severity="MEDIUM",
                confidence=0.95,
                summary=f"High-frequency request surge ({len(timestamps)} requests in {self.RATE_LIMIT_WINDOW}s) from {client_ip}",
                evidence={
                    "client_ip": client_ip,
                    "request_count": len(timestamps),
                    "window_seconds": self.RATE_LIMIT_WINDOW,
                    "target_path": path
                },
                why_flagged="Request rate significantly exceeds normal human interactive velocity.",
                false_positive_considerations="Rapid client prefetching or shared NAT proxy.",
                recommended_action="RATE_LIMIT",
                status="ATTEMPTED_BLOCKED"
            )
            mitigation = AppSecResponder.execute_defensive_mitigation(detection)
            record_security_event(
                client_ip=client_ip,
                method=method,
                path=path,
                status_code=429,
                event_type="RATE_LIMIT_EXCEEDED",
                severity="MEDIUM",
                correlation_id=correlation_id,
                details={"rate": len(timestamps), "window": self.RATE_LIMIT_WINDOW},
                action_taken="RATE_LIMITED"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate Limit Exceeded by AutoHeal AppSec Sentinel",
                    "threat_category": "Denial of Service / Scraping",
                    "rule_id": "RATE-001",
                    "summary": detection.summary,
                    "incident_id": mitigation.get("incident_id"),
                    "mitigation_action": mitigation.get("action_executed"),
                    "retry_after_seconds": 60,
                    "correlation_id": correlation_id
                },
                headers={"X-Correlation-ID": correlation_id, "Retry-After": "60"}
            )

        # 3. Read request body safely if POST/PUT without consuming it
        body_sample = ""
        if method in ["POST", "PUT", "PATCH"]:
            try:
                body_bytes = await request.body()
                async def receive():
                    return {"type": "http.request", "body": body_bytes}
                request._receive = receive
                body_sample = body_bytes.decode("utf-8", errors="ignore")[:4096]
            except Exception:
                body_sample = ""

        # 4. Inspect query parameters, headers, and body for live attack payloads targeting application endpoints
        detection = None
        if not path.startswith("/api/security"):
            headers_dict = dict(request.headers)
            detection = AppSecDetector.analyze_live_request(
                client_ip=client_ip,
                method=method,
                path=path,
                query_string=query_string,
                headers=headers_dict,
                body_sample=body_sample
            )

        if detection and detection.triggered:
            mitigation = AppSecResponder.execute_defensive_mitigation(detection)
            record_security_event(
                client_ip=client_ip,
                method=method,
                path=path,
                status_code=403,
                event_type=f"{detection.rule_id}_DEFENSE_TRIGGERED",
                severity=detection.severity,
                correlation_id=correlation_id,
                details=detection.to_dict(),
                action_taken="BLOCKED"
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Request Blocked by AutoHeal Application Security Sentinel",
                    "threat_category": detection.category,
                    "rule_id": detection.rule_id,
                    "summary": detection.summary,
                    "incident_id": mitigation.get("incident_id"),
                    "mitigation_action": mitigation.get("action_executed"),
                    "confidence": detection.confidence,
                    "correlation_id": correlation_id
                },
                headers={"X-Correlation-ID": correlation_id}
            )

        # 5. Process Request
        try:
            response = await call_next(request)
            latency_ms = round((time.time() - start_time) * 1000, 2)
            response.headers["X-Correlation-ID"] = correlation_id

            status_code = response.status_code
            event_type = "NORMAL_REQUEST"
            severity = "INFO"

            if status_code in [401, 403]:
                event_type = "AUTHZ_FAILURE"
                severity = "LOW"
            elif status_code >= 500:
                event_type = "SERVICE_HEALTH_ERROR"
                severity = "HIGH"

            # Check for failed login on auth endpoints
            if path == "/api/shop/auth/login" and status_code >= 400:
                event_type = "AUTH_FAILURE"
                severity = "MEDIUM"

            # Record Telemetry Event
            record_security_event(
                client_ip=client_ip,
                method=method,
                path=path,
                status_code=status_code,
                latency_ms=latency_ms,
                correlation_id=correlation_id,
                event_type=event_type,
                severity=severity,
                details={"query_string": redact_sensitive_data(query_string)}
            )

            # Check if this failed login triggers AUTH-001 Brute Force / Credential Stuffing
            if event_type == "AUTH_FAILURE":
                recent_auth_failures = get_security_events(
                    limit=20,
                    client_ip=client_ip,
                    event_type="AUTH_FAILURE",
                    since_seconds=60
                )
                if len(recent_auth_failures) >= 4:
                    brute_det = DetectionResult(
                        triggered=True,
                        rule_id="AUTH-001",
                        category="Credential Stuffing / Brute Force",
                        severity="HIGH",
                        confidence=0.96,
                        summary=f"Burst of {len(recent_auth_failures)} failed logins detected from IP {client_ip}",
                        evidence={
                            "client_ip": client_ip,
                            "failed_attempt_count": len(recent_auth_failures),
                            "target_endpoint": path,
                            "linked_event_ids": [e.get("event_id") for e in recent_auth_failures if e.get("event_id")]
                        },
                        why_flagged=f"Exceeded threshold of 4 failed authentication attempts within sliding window from IP {client_ip}.",
                        false_positive_considerations="Single forgotten password; multiple attempts indicate automated brute force or credential stuffing.",
                        recommended_action="BLOCK_IP",
                        status="ATTEMPTED"
                    )
                    AppSecResponder.execute_defensive_mitigation(brute_det)

            return response

        except Exception as exc:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            record_security_event(
                client_ip=client_ip,
                method=method,
                path=path,
                status_code=500,
                latency_ms=latency_ms,
                correlation_id=correlation_id,
                event_type="UNHANDLED_EXCEPTION",
                severity="CRITICAL",
                details={"exception": str(exc)}
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "correlation_id": correlation_id,
                    "detail": str(exc)
                },
                headers={"X-Correlation-ID": correlation_id}
            )
