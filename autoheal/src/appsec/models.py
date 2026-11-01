import re
import json
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

from shopsphere.database import get_db_connection, init_db


# --- Sensitive Data Redaction ---
SENSITIVE_PATTERNS = [
    (r'(?i)(password|passwd|pwd|secret|token|api_key|auth_token|cvv|card_number)["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', r'\1=[REDACTED]'),
    (r'\b(?:\d{4}[ -]?){3}\d{4}\b', '[REDACTED_CREDIT_CARD]'),
    (r'\bBearer\s+[A-Za-z0-9_\-\.]+\b', 'Bearer [REDACTED_TOKEN]')
]


def redact_sensitive_data(data: Any) -> Any:
    """Recursively redacts passwords, tokens, API keys, and payment card numbers from dictionaries, lists, or strings."""
    if isinstance(data, dict):
        redacted = {}
        for k, v in data.items():
            if any(s in k.lower() for s in ['password', 'passwd', 'secret', 'token', 'auth', 'cvv', 'card_num']):
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = redact_sensitive_data(v)
        return redacted
    elif isinstance(data, list):
        return [redact_sensitive_data(it) for it in data]
    elif isinstance(data, str):
        text = data
        for pattern, replacement in SENSITIVE_PATTERNS:
            text = re.sub(pattern, replacement, text)
        return text
    return data


# --- Database Operations for Security Events ---
def record_security_event(
    client_ip: str,
    method: str,
    path: str,
    status_code: int,
    event_type: str,
    severity: str = "INFO",
    latency_ms: float = 0.0,
    correlation_id: Optional[str] = None,
    user_agent: Optional[str] = None,
    user_id_or_session: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    action_taken: str = "ALLOWED"
) -> str:
    """Inserts an immutable telemetry record into security_events."""
    init_db()
    event_id = f"EVT-{secrets.token_hex(6).upper()}"
    corr_id = correlation_id or f"corr-{secrets.token_hex(4)}"
    safe_details = redact_sensitive_data(details or {})
    details_str = json.dumps(safe_details)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO security_events (
            event_id, correlation_id, client_ip, user_agent, method, path,
            status_code, latency_ms, user_id_or_session, event_type,
            severity, details_json, action_taken
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, corr_id, client_ip, user_agent or "Unknown", method.upper(), path,
            status_code, round(latency_ms, 2), user_id_or_session, event_type,
            severity.upper(), details_str, action_taken
        ))
        conn.commit()
    return event_id


def get_security_events(
    limit: int = 100,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    client_ip: Optional[str] = None,
    since_seconds: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Retrieves security telemetry events with filtering."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM security_events WHERE 1=1"
        params = []
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if severity:
            query += " AND severity = ?"
            params.append(severity.upper())
        if client_ip:
            query += " AND client_ip = ?"
            params.append(client_ip)
        if since_seconds:
            cutoff = (datetime.now(timezone.utc) - timedelta(seconds=since_seconds)).strftime("%Y-%m-%d %H:%M:%S")
            query += " AND timestamp >= ?"
            params.append(cutoff)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        events = []
        for r in rows:
            ev = dict(r)
            if ev.get("details_json"):
                try:
                    ev["details"] = json.loads(ev["details_json"])
                except Exception:
                    ev["details"] = {}
            events.append(ev)
        return events


# --- Database Operations for Security Incidents ---
def create_security_incident(
    rule_id: str,
    title: str,
    category: str,
    severity: str,
    summary: str,
    source_ip: str,
    evidence: Dict[str, Any],
    affected_endpoints: List[str],
    impact_actual: str,
    impact_potential: str,
    mitigation_actions: List[Dict[str, Any]],
    confidence: float = 1.0,
    status: str = "OPEN",
    remediation_details: str = "",
    verification_status: str = "PENDING"
) -> str:
    """Inserts a structured incident record into security_incidents."""
    init_db()
    incident_id = f"INC-2026-{secrets.token_hex(4).upper()}"
    evidence_str = json.dumps(redact_sensitive_data(evidence))
    endpoints_str = json.dumps(affected_endpoints)
    actions_str = json.dumps(mitigation_actions)

    # MITRE ATT&CK alignment lookup
    mitre_tech = "T1110.001"
    mitre_tactic = "Credential Access (TA0006)"
    mitre_name = "Brute Force: Password Guessing"
    try:
        from src.appsec.ai_advisor import MITRE_CATALOG
        m = MITRE_CATALOG.get(rule_id)
        if m:
            mitre_tech = m.get("technique_id", mitre_tech)
            mitre_tactic = f"{m.get('tactic_name')} ({m.get('tactic_id')})"
            mitre_name = f"{m.get('technique_name')}: {m.get('subtechnique', '')}".rstrip(": ")
    except Exception:
        pass

    recovery_status = "NOMINAL_MONITORING"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO security_incidents (
            incident_id, rule_id, title, category, severity, status,
            confidence, summary, evidence_json, affected_endpoints_json,
            source_ip, impact_actual, impact_potential, mitigation_actions_json,
            remediation_details, verification_status,
            mitre_technique_id, mitre_tactic, mitre_name, recovery_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            incident_id, rule_id, title, category, severity.upper(), status.upper(),
            round(confidence, 2), summary, evidence_str, endpoints_str,
            source_ip, impact_actual, impact_potential, actions_str,
            remediation_details, verification_status,
            mitre_tech, mitre_tactic, mitre_name, recovery_status
        ))
        conn.commit()
    return incident_id


def find_active_incident(
    source_ip: str,
    rule_id: str,
    window_seconds: int = 300
) -> Optional[Dict[str, Any]]:
    """
    Finds an existing open/active incident for the given client IP and rule
    within the sliding window to prevent duplicate incident creation.
    """
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=window_seconds)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            SELECT incident_id FROM security_incidents
            WHERE source_ip = ? AND rule_id = ? 
              AND status NOT IN ('RESOLVED', 'CLOSED')
              AND (created_at >= ? OR updated_at >= ?)
            ORDER BY id DESC LIMIT 1
        """, (source_ip, rule_id, cutoff, cutoff))
        row = cursor.fetchone()
        if not row:
            return None
        return get_security_incident(row["incident_id"])


def upsert_security_incident(
    rule_id: str,
    title: str,
    category: str,
    severity: str,
    summary: str,
    source_ip: str,
    evidence: Dict[str, Any],
    affected_endpoints: List[str],
    impact_actual: str,
    impact_potential: str,
    mitigation_actions: List[Dict[str, Any]],
    confidence: float = 1.0,
    status: str = "OPEN",
    remediation_details: str = "",
    verification_status: str = "PENDING",
    window_seconds: int = 300
) -> str:
    """
    Idempotent incident creation. If an active incident for (source_ip, rule_id) exists
    within the correlation window, updates it with merged evidence and timestamps rather
    than creating an unnecessary duplicate incident record.
    """
    existing = find_active_incident(source_ip=source_ip, rule_id=rule_id, window_seconds=window_seconds)
    if existing:
        inc_id = existing["incident_id"]
        existing_evidence = existing.get("evidence", {}) or {}
        merged_evidence = dict(existing_evidence)
        merged_evidence.update(evidence)

        # Merge linked event IDs list
        existing_evts = set(existing_evidence.get("linked_event_ids", []))
        new_evts = set(evidence.get("linked_event_ids", []))
        if evidence.get("event_id"):
            new_evts.add(evidence["event_id"])
        combined_evts = list(existing_evts.union(new_evts))
        if combined_evts:
            merged_evidence["linked_event_ids"] = combined_evts

        # Merge mitigation actions
        existing_actions = existing.get("mitigation_actions", []) or []
        for action in mitigation_actions:
            if action not in existing_actions:
                existing_actions.append(action)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE security_incidents SET
                    evidence_json = ?,
                    mitigation_actions_json = ?,
                    confidence = MAX(confidence, ?),
                    updated_at = CURRENT_TIMESTAMP
                WHERE incident_id = ?
            """, (
                json.dumps(redact_sensitive_data(merged_evidence)),
                json.dumps(existing_actions),
                round(confidence, 2),
                inc_id
            ))
            conn.commit()
        return inc_id

    # Create new incident if none active
    return create_security_incident(
        rule_id=rule_id,
        title=title,
        category=category,
        severity=severity,
        summary=summary,
        source_ip=source_ip,
        evidence=evidence,
        affected_endpoints=affected_endpoints,
        impact_actual=impact_actual,
        impact_potential=impact_potential,
        mitigation_actions=mitigation_actions,
        confidence=confidence,
        status=status,
        remediation_details=remediation_details,
        verification_status=verification_status
    )


def get_security_incident(incident_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves full incident dossier by incident_id."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM security_incidents WHERE incident_id = ?", (incident_id,))
        row = cursor.fetchone()
        if not row:
            return None
        inc = dict(row)
        for field in ["evidence_json", "affected_endpoints_json", "mitigation_actions_json", "regression_tests_json"]:
            if inc.get(field):
                try:
                    inc[field.replace("_json", "")] = json.loads(inc[field])
                except Exception:
                    inc[field.replace("_json", "")] = {}
        if not inc.get("recovery_status"):
            inc["recovery_status"] = "NOMINAL_MONITORING"
        if not inc.get("mitre_technique_id") and inc.get("rule_id"):
            try:
                from src.appsec.ai_advisor import MITRE_CATALOG
                m = MITRE_CATALOG.get(inc.get("rule_id"))
                if m:
                    inc["mitre_technique_id"] = m.get("technique_id")
                    inc["mitre_tactic"] = f"{m.get('tactic_name')} ({m.get('tactic_id')})"
                    inc["mitre_name"] = f"{m.get('technique_name')}: {m.get('subtechnique', '')}".rstrip(": ")
            except Exception:
                pass
        return inc


def list_security_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Lists recent security incidents with filtering."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM security_incidents WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status.upper())
        if severity:
            query += " AND severity = ?"
            params.append(severity.upper())

        query += " ORDER BY updated_at DESC, id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        incidents = []
        for r in rows:
            inc = dict(r)
            for field in ["evidence_json", "affected_endpoints_json", "mitigation_actions_json"]:
                if inc.get(field):
                    try:
                        inc[field.replace("_json", "")] = json.loads(inc[field])
                    except Exception:
                        inc[field.replace("_json", "")] = {}
            incidents.append(inc)
        return incidents


def update_incident_status(
    incident_id: str,
    status: str,
    verification_status: Optional[str] = None,
    remediation_details: Optional[str] = None,
    evidence: Optional[Dict[str, Any]] = None,
    recovery_status: Optional[str] = None,
    regression_tests: Optional[List[Dict[str, Any]]] = None
) -> Optional[Dict[str, Any]]:
    """Updates the status and verification state of an incident."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
        params = [status.upper()]

        if verification_status:
            updates.append("verification_status = ?")
            params.append(verification_status.upper())
        if remediation_details:
            updates.append("remediation_details = ?")
            params.append(remediation_details)
        if evidence:
            updates.append("evidence_json = ?")
            params.append(json.dumps(redact_sensitive_data(evidence)))
        if recovery_status:
            updates.append("recovery_status = ?")
            params.append(recovery_status.upper())
        if regression_tests:
            updates.append("regression_tests_json = ?")
            params.append(json.dumps(regression_tests))

        params.append(incident_id)
        cursor.execute(f"UPDATE security_incidents SET {', '.join(updates)} WHERE incident_id = ?", params)
        conn.commit()
    return get_security_incident(incident_id)


# --- Database Operations for Dynamic Client IP Blocklist ---
def block_client_ip(
    client_ip: str,
    reason: str,
    rule_id: str,
    duration_seconds: int = 300,
    incident_id: Optional[str] = None
) -> Dict[str, Any]:
    """Dynamically blocks an abusive IP address for a configured TTL (e.g. 5 minutes)."""
    # Exclude loopback/localhost from quarantine to prevent locking out local demo operator
    if client_ip in ["127.0.0.1", "::1", "localhost"]:
        return {
            "client_ip": client_ip,
            "reason": f"Loopback exempted: {reason}",
            "rule_id": rule_id,
            "incident_id": incident_id,
            "expires_at": "",
            "duration_seconds": 0
        }

    init_db()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)
    expires_str = expires_at.isoformat()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO blocked_clients (client_ip, reason, rule_id, incident_id, expires_at, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
        ON CONFLICT(client_ip) DO UPDATE SET
            reason = excluded.reason,
            rule_id = excluded.rule_id,
            incident_id = excluded.incident_id,
            expires_at = excluded.expires_at,
            is_active = 1
        """, (client_ip, reason, rule_id, incident_id, expires_str))
        conn.commit()

    return {
        "client_ip": client_ip,
        "reason": reason,
        "rule_id": rule_id,
        "incident_id": incident_id,
        "expires_at": expires_str,
        "duration_seconds": duration_seconds
    }


def is_client_blocked(client_ip: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Checks whether an IP address is actively blocked, expiring stale blocks automatically."""
    if client_ip in ["127.0.0.1", "::1", "localhost"]:
        return False, None
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM blocked_clients 
        WHERE client_ip = ? AND is_active = 1
        """, (client_ip,))
        row = cursor.fetchone()
        if not row:
            return False, None

        block_data = dict(row)
        expires_str = block_data["expires_at"]
        try:
            # Handle ISO timestamp comparison
            expires_dt = datetime.fromisoformat(expires_str)
            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=timezone.utc)
            now_dt = datetime.now(timezone.utc)

            if now_dt > expires_dt:
                # Expired -> mark inactive
                cursor.execute("UPDATE blocked_clients SET is_active = 0 WHERE id = ?", (block_data["id"],))
                conn.commit()
                return False, None
        except Exception:
            pass

        return True, block_data


def unblock_client_ip(client_ip: str) -> bool:
    """Manually unblocks a client IP address."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE blocked_clients SET is_active = 0 WHERE client_ip = ?", (client_ip,))
        conn.commit()
        return cursor.rowcount > 0


def get_active_blocked_clients() -> List[Dict[str, Any]]:
    """Retrieves all currently active blocked client records."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blocked_clients WHERE is_active = 1 ORDER BY id DESC")
        rows = cursor.fetchall()
        active = []
        now_dt = datetime.now(timezone.utc)
        for r in rows:
            b = dict(r)
            try:
                exp = datetime.fromisoformat(b["expires_at"])
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if now_dt <= exp:
                    active.append(b)
                else:
                    cursor.execute("UPDATE blocked_clients SET is_active = 0 WHERE id = ?", (b["id"],))
            except Exception:
                active.append(b)
        conn.commit()
        return active
