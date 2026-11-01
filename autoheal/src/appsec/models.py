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


# --- Live Threat Center & Event Forensics Engine (Phase 3) ---

RULE_METADATA: Dict[str, Dict[str, Any]] = {
    "INJ-001": {
        "rule_id": "INJ-001",
        "rule_name": "SQL Injection Attack",
        "description": "Inspects query strings, parameters, and bodies for union-based, boolean-based, or stacked SQL injection patterns.",
        "category": "Injection",
        "severity": "CRITICAL",
        "mitre_technique_id": "T1190",
        "mitre_tactic": "Initial Access (TA0001)",
        "mitre_name": "Exploit Public-Facing Application: SQL Injection",
        "detection_logic": "Regex inspection for SQL syntax fragments like UNION SELECT, OR 1=1, stacked query delimiters, and hex comments."
    },
    "AUTH-001": {
        "rule_id": "AUTH-001",
        "rule_name": "Credential Stuffing / Brute Force",
        "description": "Detects rapid sequential failed login attempts from a common client IP or against targeted user identities.",
        "category": "Credential Access",
        "severity": "HIGH",
        "mitre_technique_id": "T1110.001",
        "mitre_tactic": "Credential Access (TA0006)",
        "mitre_name": "Brute Force: Password Guessing",
        "detection_logic": "Sliding-window threshold of >3 consecutive failed login events within a 60-second window."
    },
    "XSS-001": {
        "rule_id": "XSS-001",
        "rule_name": "Cross-Site Scripting (XSS)",
        "description": "Identifies reflected or stored cross-site scripting vectors containing script tags, event handlers, or JavaScript pseudo-protocols.",
        "category": "Client-Side Execution",
        "severity": "HIGH",
        "mitre_technique_id": "T1059.007",
        "mitre_tactic": "Execution (TA0002)",
        "mitre_name": "Command and Scripting Interpreter: JavaScript",
        "detection_logic": "Pattern matching on HTML tags (<script>, <img>, <iframe>) with executable attributes (onload, onerror) or javascript: URIs."
    },
    "AUTH-002": {
        "rule_id": "AUTH-002",
        "rule_name": "Unauthorized Admin Access Probe",
        "description": "Flags requests directed towards privileged administrative management paths without valid cryptographic session tokens.",
        "category": "Privilege Escalation",
        "severity": "HIGH",
        "mitre_technique_id": "T1078",
        "mitre_tactic": "Defense Evasion (TA0005)",
        "mitre_name": "Valid Accounts: Default Accounts",
        "detection_logic": "Path inspection for /admin endpoints combined with token validation checking for admin role authorization."
    },
    "RATE-001": {
        "rule_id": "RATE-001",
        "rule_name": "Request-Rate Anomaly / Scraping",
        "description": "Monitors high-frequency volumetric request bursts exceeding standard shopping workflow rate limits.",
        "category": "Denial of Service",
        "severity": "MEDIUM",
        "mitre_technique_id": "T1499",
        "mitre_tactic": "Impact (TA0040)",
        "mitre_name": "Endpoint Denial of Service",
        "detection_logic": "Sliding-window request velocity tracking triggering when a single client IP exceeds 15 requests per 5-second interval."
    },
    "CORR-001": {
        "rule_id": "CORR-001",
        "rule_name": "Multi-Step Attack Correlation",
        "description": "Correlates multi-phase adversarial kill-chains combining reconnaissance, injection, and privilege escalation.",
        "category": "Advanced Persistent Threat",
        "severity": "CRITICAL",
        "mitre_technique_id": "T1190/T1078",
        "mitre_tactic": "Multiple Tactics",
        "mitre_name": "Combined Multi-Step Kill-Chain",
        "detection_logic": "Complex correlation heuristic linking diverse attack categories from identical source IP or correlation context."
    },
    "HEALTH-001": {
        "rule_id": "HEALTH-001",
        "rule_name": "Clustered Service Exception Degradation",
        "description": "Detects clustered application error bursts (HTTP 500) indicating potential zero-day exploitation or system failure.",
        "category": "System Reliability",
        "severity": "HIGH",
        "mitre_technique_id": "T1499.004",
        "mitre_tactic": "Impact (TA0040)",
        "mitre_name": "Application Exploitation Degradation",
        "detection_logic": "Threshold evaluation on unhandled 5xx server exceptions exceeding 5 errors within a 60-second window."
    }
}


def map_event_to_rule_id(event_type: str, details: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Resolves event type or details payload to its detection rule identifier."""
    if details and details.get("rule_id"):
        return details["rule_id"]
    t = (event_type or "").upper()
    if "INJ-001" in t or "SQL" in t:
        return "INJ-001"
    if "XSS-001" in t or "XSS" in t:
        return "XSS-001"
    if "AUTH-002" in t or "ADMIN" in t:
        return "AUTH-002"
    if "AUTH_FAILURE" in t or "AUTH-001" in t or "CREDENTIAL" in t or "LOGIN" in t:
        return "AUTH-001"
    if "RATE_LIMIT" in t or "RATE-001" in t or "SURGE" in t:
        return "RATE-001"
    if "HEALTH" in t or "EXCEPTION" in t:
        return "HEALTH-001"
    if "CORR" in t:
        return "CORR-001"
    return None


def get_security_event_by_id(event_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves full structured telemetry event, investigation status, detection rule, and related incident."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM security_events WHERE event_id = ? OR id = ?", (event_id, event_id))
        row = cursor.fetchone()
        if not row:
            return None
        ev = dict(row)
        details = {}
        if ev.get("details_json"):
            try:
                details = json.loads(ev["details_json"])
            except Exception:
                details = {}
        ev["details"] = details

        # Investigation state
        cursor.execute("SELECT * FROM event_investigations WHERE event_id = ?", (ev["event_id"],))
        inv_row = cursor.fetchone()
        if inv_row:
            inv = dict(inv_row)
            ev["investigation"] = {
                "status": inv.get("status", "NEW"),
                "assigned_analyst": inv.get("assigned_analyst", "admin@sentinel.sec"),
                "notes": inv.get("notes", ""),
                "incident_id": inv.get("incident_id"),
                "tags": json.loads(inv.get("tags_json") or "[]"),
                "updated_at": inv.get("updated_at")
            }
        else:
            ev["investigation"] = {
                "status": "NEW",
                "assigned_analyst": "admin@sentinel.sec",
                "notes": "",
                "incident_id": None,
                "tags": [],
                "updated_at": ev.get("timestamp")
            }

        # Rule resolution
        rule_id = map_event_to_rule_id(ev.get("event_type", ""), details)
        ev["rule_id"] = rule_id
        if rule_id and rule_id in RULE_METADATA:
            ev["detection_rule"] = RULE_METADATA[rule_id]
        else:
            ev["detection_rule"] = None

        # Related incident resolution
        incident_id = ev["investigation"]["incident_id"]
        if not incident_id and ev.get("client_ip"):
            cursor.execute(
                "SELECT incident_id, title, status, severity, created_at FROM security_incidents WHERE source_ip = ? ORDER BY id DESC LIMIT 1",
                (ev["client_ip"],)
            )
            inc_match = cursor.fetchone()
            ev["related_incident"] = dict(inc_match) if inc_match else None
        elif incident_id:
            cursor.execute(
                "SELECT incident_id, title, status, severity, created_at FROM security_incidents WHERE incident_id = ?",
                (incident_id,)
            )
            inc_match = cursor.fetchone()
            ev["related_incident"] = dict(inc_match) if inc_match else None
        else:
            ev["related_incident"] = None

        return ev


def get_related_security_events(event_id: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Correlates related security events by cryptographic correlation ID, identical source IP, and target resource proximity."""
    init_db()
    ev = get_security_event_by_id(event_id)
    if not ev:
        return []

    client_ip = ev.get("client_ip")
    corr_id = ev.get("correlation_id")
    target_path = ev.get("path")

    related = []
    seen_ids = {ev.get("event_id")}

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Confirmed relationship: Identical correlation_id
        if corr_id and corr_id != "corr-none":
            cursor.execute(
                "SELECT * FROM security_events WHERE correlation_id = ? AND event_id != ? ORDER BY id DESC LIMIT ?",
                (corr_id, ev.get("event_id"), limit)
            )
            for r in cursor.fetchall():
                item = dict(r)
                if item["event_id"] not in seen_ids:
                    seen_ids.add(item["event_id"])
                    item["relationship_type"] = "CONFIRMED_CORRELATION"
                    item["relationship_detail"] = f"Shares cryptographic correlation trace ID '{corr_id}'"
                    related.append(item)

        # 2. Heuristic relationship: Same client IP
        if client_ip and len(related) < limit:
            remaining = limit - len(related)
            cursor.execute(
                "SELECT * FROM security_events WHERE client_ip = ? AND event_id != ? ORDER BY id DESC LIMIT ?",
                (client_ip, ev.get("event_id"), remaining)
            )
            for r in cursor.fetchall():
                item = dict(r)
                if item["event_id"] not in seen_ids:
                    seen_ids.add(item["event_id"])
                    item["relationship_type"] = "COMMON_SOURCE_IP"
                    item["relationship_detail"] = f"Originated from identical client IP ({client_ip})"
                    related.append(item)

        # 3. Target resource proximity: Same target path with security triggers
        if target_path and len(related) < limit:
            remaining = limit - len(related)
            cursor.execute(
                "SELECT * FROM security_events WHERE path = ? AND event_id != ? AND severity IN ('CRITICAL', 'HIGH', 'MEDIUM') ORDER BY id DESC LIMIT ?",
                (target_path, ev.get("event_id"), remaining)
            )
            for r in cursor.fetchall():
                item = dict(r)
                if item["event_id"] not in seen_ids:
                    seen_ids.add(item["event_id"])
                    item["relationship_type"] = "TARGET_ENDPOINT_PROXIMITY"
                    item["relationship_detail"] = f"Concurrent attack probe directed at {target_path}"
                    related.append(item)

    for item in related:
        if item.get("details_json"):
            try:
                item["details"] = json.loads(item["details_json"])
            except Exception:
                item["details"] = {}
        item["rule_id"] = map_event_to_rule_id(item.get("event_type", ""), item.get("details"))

    return related


def query_security_events_advanced(
    page: int = 1,
    limit: int = 25,
    search: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    rule_id: Optional[str] = None,
    client_ip: Optional[str] = None,
    action_taken: Optional[str] = None,
    time_range: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc"
) -> Dict[str, Any]:
    """Advanced server-side query with full-text search, multi-field filtering, pagination, and aggregate breakdown."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()

        where_clauses = ["1=1"]
        params: List[Any] = []

        if search:
            s = f"%{search.strip()}%"
            where_clauses.append("(se.event_id LIKE ? OR se.correlation_id LIKE ? OR se.client_ip LIKE ? OR se.path LIKE ? OR se.method LIKE ? OR se.event_type LIKE ? OR se.details_json LIKE ?)")
            params.extend([s, s, s, s, s, s, s])

        if severity and severity.upper() != "ALL":
            where_clauses.append("se.severity = ?")
            params.append(severity.upper())

        if category and category.upper() != "ALL":
            cat = category.upper()
            if cat in ("SQL_INJECTION", "INJECTION"):
                where_clauses.append("(se.event_type LIKE '%INJ%' OR se.details_json LIKE '%Injection%' OR se.details_json LIKE '%injection%')")
            elif cat in ("XSS", "CROSS_SITE_SCRIPTING"):
                where_clauses.append("(se.event_type LIKE '%XSS%' OR se.details_json LIKE '%Cross-Site Scripting%' OR se.details_json LIKE '%xss%')")
            elif cat in ("CREDENTIAL_STUFFING", "AUTH_FAILURE", "CREDENTIAL_ACCESS"):
                where_clauses.append("(se.event_type LIKE '%AUTH_FAILURE%' OR se.event_type LIKE '%AUTH-001%')")
            elif cat in ("ADMIN_PATH_TRAVERSAL", "PRIVILEGE_ESCALATION", "AUTH-002"):
                where_clauses.append("(se.event_type LIKE '%AUTH-002%' OR se.event_type LIKE '%AUTHZ%')")
            elif cat in ("RATE_LIMIT_EXCEEDED", "DOS"):
                where_clauses.append("(se.event_type LIKE '%RATE%' OR se.status_code = 429)")
            elif cat in ("SERVICE_HEALTH_ERROR", "SYSTEM_RELIABILITY"):
                where_clauses.append("(se.event_type LIKE '%HEALTH%' OR se.event_type LIKE '%EXCEPTION%' OR se.status_code >= 500)")
            else:
                where_clauses.append("se.event_type = ?")
                params.append(category)

        if rule_id and rule_id.upper() != "ALL":
            r_id = rule_id.upper()
            where_clauses.append("(se.event_type LIKE ? OR se.details_json LIKE ?)")
            params.extend([f"%{r_id}%", f"%{r_id}%"])

        if client_ip:
            where_clauses.append("se.client_ip = ?")
            params.append(client_ip.strip())

        if action_taken and action_taken.upper() != "ALL":
            act = action_taken.upper()
            if "BLOCK" in act or "QUARANTINE" in act:
                where_clauses.append("(se.action_taken LIKE '%BLOCK%' OR se.action_taken LIKE '%QUARANTINE%' OR se.status_code = 403)")
            elif "THROTTLE" in act:
                where_clauses.append("(se.action_taken LIKE '%THROTTLE%' OR se.status_code = 429)")
            elif "ALLOW" in act:
                where_clauses.append("(se.action_taken LIKE '%ALLOW%' OR se.status_code = 200)")
            else:
                where_clauses.append("se.action_taken = ?")
                params.append(action_taken)

        # Time range filtering
        if time_range and time_range.lower() != "all":
            tr = time_range.lower()
            hours = 24
            if tr == "1h":
                hours = 1
            elif tr == "24h":
                hours = 24
            elif tr == "7d":
                hours = 24 * 7
            elif tr == "30d":
                hours = 24 * 30
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
            where_clauses.append("se.timestamp >= ?")
            params.append(cutoff)
        elif start_time and end_time:
            where_clauses.append("se.timestamp >= ? AND se.timestamp <= ?")
            params.extend([start_time, end_time])

        where_sql = " AND ".join(where_clauses)

        # Calculate counts per severity for filtered scope
        summary_query = f"""
        SELECT 
            COUNT(*) as total_count,
            SUM(CASE WHEN se.severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
            SUM(CASE WHEN se.severity = 'HIGH' THEN 1 ELSE 0 END) as high_count,
            SUM(CASE WHEN se.severity = 'MEDIUM' THEN 1 ELSE 0 END) as medium_count,
            SUM(CASE WHEN se.severity = 'LOW' THEN 1 ELSE 0 END) as low_count,
            SUM(CASE WHEN se.severity = 'INFO' THEN 1 ELSE 0 END) as info_count,
            MAX(se.timestamp) as last_event_timestamp
        FROM security_events se WHERE {where_sql}
        """
        cursor.execute(summary_query, params)
        sum_row = cursor.fetchone()
        total_records = sum_row[0] if sum_row else 0
        summary = {
            "total": total_records or 0,
            "critical": (sum_row[1] or 0) if sum_row else 0,
            "high": (sum_row[2] or 0) if sum_row else 0,
            "medium": (sum_row[3] or 0) if sum_row else 0,
            "low": (sum_row[4] or 0) if sum_row else 0,
            "info": (sum_row[5] or 0) if sum_row else 0,
            "last_event_timestamp": sum_row[6] if sum_row and sum_row[6] else None
        }

        # Sorting
        valid_sort_cols = {
            "timestamp": "se.timestamp",
            "severity": "CASE se.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 WHEN 'LOW' THEN 4 ELSE 5 END",
            "status_code": "se.status_code",
            "latency_ms": "se.latency_ms",
            "client_ip": "se.client_ip",
            "path": "se.path"
        }
        order_col = valid_sort_cols.get(sort_by, "se.id")
        direction = "ASC" if sort_order.lower() == "asc" else "DESC"

        # Pagination
        limit = max(1, min(limit, 500))
        offset = max(0, (page - 1) * limit)

        # Main query
        data_query = f"""
        SELECT se.*, ei.status as investigation_status, ei.assigned_analyst, ei.notes as investigation_notes
        FROM security_events se
        LEFT JOIN event_investigations ei ON se.event_id = ei.event_id
        WHERE {where_sql}
        ORDER BY {order_col} {direction}
        LIMIT ? OFFSET ?
        """
        data_params = list(params) + [limit, offset]
        cursor.execute(data_query, data_params)
        rows = cursor.fetchall()

        events = []
        for r in rows:
            ev = dict(r)
            if ev.get("details_json"):
                try:
                    ev["details"] = json.loads(ev["details_json"])
                except Exception:
                    ev["details"] = {}
            else:
                ev["details"] = {}

            ev["rule_id"] = map_event_to_rule_id(ev.get("event_type", ""), ev.get("details"))
            events.append(ev)

        total_pages = max(1, (total_records + limit - 1) // limit) if total_records > 0 else 1

        return {
            "events": events,
            "total": total_records,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "summary": summary
        }


def record_event_investigation(
    event_id: str,
    status: str = "INVESTIGATING",
    notes: str = "",
    assigned_analyst: str = "admin@sentinel.sec",
    tags: Optional[List[str]] = None,
    create_incident: bool = False,
    admin_email: str = "admin@sentinel.sec"
) -> Dict[str, Any]:
    """Persists investigation updates, analyst notes, and optional incident escalation with complete audit trail."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM security_events WHERE event_id = ?", (event_id,))
        ev_row = cursor.fetchone()
        if not ev_row:
            raise ValueError(f"Event {event_id} not found")
        ev = dict(ev_row)

        incident_id = None
        if create_incident:
            cursor.execute("SELECT incident_id FROM event_investigations WHERE event_id = ?", (event_id,))
            existing_inv = cursor.fetchone()
            if existing_inv and existing_inv[0]:
                incident_id = existing_inv[0]
            else:
                details = json.loads(ev.get("details_json") or "{}")
                rule_id = map_event_to_rule_id(ev.get("event_type"), details) or "INJ-001"
                rule_meta = RULE_METADATA.get(rule_id, RULE_METADATA["INJ-001"])
                incident_id = create_security_incident(
                    rule_id=rule_id,
                    title=f"Escalated from Event {event_id}: {ev.get('event_type')}",
                    category=rule_meta["category"],
                    severity=ev.get("severity", "HIGH"),
                    summary=f"Analyst escalated telemetry event {event_id} ({ev.get('method')} {ev.get('path')}) to formal security incident. Investigation notes: {notes}",
                    source_ip=ev.get("client_ip", "127.0.0.1"),
                    evidence={"event_id": event_id, "method": ev.get("method"), "path": ev.get("path"), "details": details},
                    affected_endpoints=[ev.get("path", "/")],
                    impact_actual=f"Active HTTP probe detected on {ev.get('path')}",
                    impact_potential="Potential privilege violation or data exposure",
                    mitigation_actions=[{"action": "ANALYST_ESCALATION", "timestamp": datetime.now(timezone.utc).isoformat(), "details": notes}],
                    confidence=0.95,
                    status="OPEN"
                )

        tags_str = json.dumps(tags or [])
        now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT INTO event_investigations (event_id, status, assigned_analyst, notes, incident_id, tags_json, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(event_id) DO UPDATE SET
            status = excluded.status,
            assigned_analyst = excluded.assigned_analyst,
            notes = excluded.notes,
            incident_id = COALESCE(excluded.incident_id, event_investigations.incident_id),
            tags_json = excluded.tags_json,
            updated_at = excluded.updated_at
        """, (event_id, status.upper(), assigned_analyst, notes, incident_id, tags_str, now_ts))

        cursor.execute("""
        INSERT INTO admin_audit_logs (admin_email, action, target_entity, details, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """, (
            admin_email,
            f"EVENT_INVESTIGATION_{status.upper()}",
            f"security_event:{event_id}",
            json.dumps({"notes": notes, "assigned_analyst": assigned_analyst, "incident_id": incident_id}),
            now_ts
        ))

        conn.commit()

        return {
            "event_id": event_id,
            "status": status.upper(),
            "assigned_analyst": assigned_analyst,
            "notes": notes,
            "incident_id": incident_id,
            "tags": tags or [],
            "updated_at": now_ts
        }


def get_threat_intel(ip: str) -> Dict[str, Any]:
    """Inspects IP reputation, autonomous blocklist state, hostile activity history, and threat actor tags."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM blocked_clients WHERE client_ip = ? AND is_active = 1", (ip,))
        blocked_row = cursor.fetchone()
        is_blocked = bool(blocked_row)

        cursor.execute("""
        SELECT 
            COUNT(*) as total_events,
            SUM(CASE WHEN severity IN ('CRITICAL', 'HIGH') THEN 1 ELSE 0 END) as hostile_events,
            MAX(timestamp) as last_seen
        FROM security_events WHERE client_ip = ?
        """, (ip,))
        ev_stats = cursor.fetchone()
        total_ev = ev_stats[0] if ev_stats else 0
        hostile_ev = ev_stats[1] if ev_stats else 0
        last_seen = ev_stats[2] if ev_stats else None

        if is_blocked:
            score = 98
            reputation = "MALICIOUS"
        elif hostile_ev > 10:
            score = 88
            reputation = "MALICIOUS"
        elif hostile_ev > 0:
            score = 65
            reputation = "SUSPICIOUS"
        elif total_ev > 50:
            score = 35
            reputation = "NEUTRAL"
        else:
            score = 12
            reputation = "BENIGN"

        tags = []
        if is_blocked:
            tags.append("WAF_ACTIVE_QUARANTINE")
        if hostile_ev > 0:
            tags.append("ATTACK_ORIGINATOR")
        if "127.0.0.1" in ip or "testclient" in ip:
            tags.append("INTERNAL_SANDBOX")
        elif ip.startswith("203.0.113.") or ip.startswith("198.51.100."):
            tags.append("DOCUMENTED_ADVERSARY_RANGE")
            tags.append("AUTOMATED_SCANNER")
        else:
            tags.append("EXTERNAL_CLIENT")

        return {
            "ip": ip,
            "reputation": reputation,
            "threat_score": score,
            "confidence": 0.94 if (hostile_ev > 0 or is_blocked) else 0.85,
            "is_blocked": is_blocked,
            "block_reason": blocked_row["reason"] if blocked_row else None,
            "total_events_observed": total_ev,
            "hostile_events_observed": hostile_ev,
            "last_seen": last_seen,
            "provider": "AutoHeal Sentinel Threat Intelligence Hub",
            "provider_status": "ONLINE (Local Cache & Behavioral Engine)",
            "geo": {
                "country": "Simulated Threat Origin" if hostile_ev > 0 else "Internal/Enterprise",
                "city": "Autonomous SOC Lab",
                "asn": "AS64496 AutoHeal Defense Grid"
            },
            "tags": tags,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }


def get_detection_rule_catalog() -> List[Dict[str, Any]]:
    """Calculates live telemetry event counts and linked security incident counts for all 7 detection rules."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()

        catalog = []
        for rule_id, meta in RULE_METADATA.items():
            cursor.execute("""
            SELECT COUNT(*), MAX(timestamp) 
            FROM security_events 
            WHERE event_type LIKE ? OR details_json LIKE ?
            """, (f"%{rule_id}%", f"%{rule_id}%"))
            ev_row = cursor.fetchone()
            ev_count = ev_row[0] if ev_row else 0
            last_triggered = ev_row[1] if ev_row and ev_row[1] else None

            cursor.execute("SELECT COUNT(*) FROM security_incidents WHERE rule_id = ?", (rule_id,))
            inc_row = cursor.fetchone()
            inc_count = inc_row[0] if inc_row else 0

            catalog.append({
                "rule_id": rule_id,
                "rule_name": meta["rule_name"],
                "description": meta["description"],
                "category": meta["category"],
                "severity": meta["severity"],
                "enabled": True,
                "mitre_technique_id": meta["mitre_technique_id"],
                "mitre_tactic": meta["mitre_tactic"],
                "mitre_name": meta["mitre_name"],
                "detection_logic": meta["detection_logic"],
                "related_event_count": ev_count,
                "related_incident_count": inc_count,
                "last_triggered": last_triggered
            })

        return catalog


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
