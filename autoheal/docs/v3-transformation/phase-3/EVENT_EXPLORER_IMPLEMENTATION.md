# AutoHeal v3.0 — Phase 3: Security Event Explorer Implementation

## Architectural Overview

The **Security Event Explorer** provides tier-1, tier-2, and tier-3 SOC analysts with a high-density, forensic-grade inspection table for raw application security telemetry. Backed by the SQLite WAL repository (`shopsphere.db`), the Event Explorer supports real-time multi-dimensional filtering, indexed search queries, server-side pagination, and non-blocking exports.

---

## Data Schema & Column Specification

The explorer renders 10 structured columns optimized for analyst readability and triage speed:

| Column Header | Field Source | Visual Treatment | Technical Purpose |
| :--- | :--- | :--- | :--- |
| **Timestamp** | `se.timestamp` | Monospace muted UTC | Temporal sorting and event timeline alignment. |
| **Event ID** | `se.event_id` | Monospace cyan code chip | Cryptographic unique event identifier (`EVT-XXXXXX`). |
| **Severity** | `se.severity` | Obsidian Sentinel badge | Visual threat ranking (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`). |
| **Category & Rule**| `se.event_type` + `rule_id`| Bold title + neutral rule chip | Identifies detection domain (e.g. `INJ-001`, `XSS-001`, `AUTH-002`). |
| **Method & Target** | `se.method` + `se.path` | Bold HTTP verb + code URI | Exact REST or GraphQL endpoint targeted by client. |
| **Status Code** | `se.status_code` | Green (<400) / Red (>=400) | Upstream HTTP response status code. |
| **Source IP** | `se.client_ip` | Monospace code with tooltip | Originator IP with instant threat intelligence lookup trigger. |
| **Action Taken** | `se.action_taken` | Status color text | Autonomous mitigation (`BLOCKED`, `THROTTLED`, `ALLOWED`). |
| **Investigation** | `ei.status` | State badge (`NEW`, `INVESTIGATING`)| Current forensic triage status in `event_investigations`. |
| **Inspect** | N/A | Secondary icon action button | Opens 5-tab Side-Over Forensic Dossier Drawer. |

---

## Server-Side Query Engine (`query_security_events_advanced`)

To efficiently handle over 7,800+ events without client-side memory bloat or DOM freezing, the backend provides `query_security_events_advanced` in `src/appsec/models.py`.

### Query Capabilities

```sql
SELECT se.*, ei.status as investigation_status, ei.assigned_analyst, ei.notes as investigation_notes
FROM security_events se
LEFT JOIN event_investigations ei ON se.event_id = ei.event_id
WHERE 1=1
  AND (se.event_id LIKE ? OR se.client_ip LIKE ? OR se.path LIKE ? OR se.details_json LIKE ?)
  AND se.severity = ?
  AND (se.event_type LIKE '%INJ%' OR se.details_json LIKE '%Injection%')
  AND se.timestamp >= ?
ORDER BY se.timestamp DESC
LIMIT ? OFFSET ?;
```

### Supported Parameters
- `page` (default 1) & `limit` (default 25, max 500)
- `search`: Debounced 300ms multi-column keyword matcher.
- `category`: Mapped categories (`SQL_INJECTION`, `XSS`, `CREDENTIAL_STUFFING`, `ADMIN_PATH_TRAVERSAL`, `RATE_LIMIT_EXCEEDED`, `SERVICE_HEALTH_ERROR`).
- `severity`: Standard threat levels (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`).
- `action_taken`: Filter by enforcement (`BLOCKED`, `THROTTLED`, `ALLOWED`).
- `client_ip`: Precise originator IP filtering.
- `rule_id`: Specific detection rule matcher (`INJ-001` through `HEALTH-001`).
- `time_range`: Quick temporal boundaries (`1h`, `24h`, `7d`, `30d`, `all`).
- `sort_by`: Indexed sorting by `timestamp`, `severity` (custom case weighting), `status_code`, `latency_ms`, `client_ip`, or `path`.

---

## Telemetry Export Capabilities

1. **CSV Export (`/api/security/events?format=csv`)**:
   - Streams an RFC 4180 compliant CSV attachment directly from the database cursor.
   - Includes standard header row (`Timestamp`, `Event ID`, `Severity`, `Event Type`, `Method`, `Path`, `Status Code`, `Client IP`, `Action Taken`, `Correlation ID`).
   - Supports active filter parameters to ensure exported dataset matches analyst view.
2. **JSON Export (`exportThreatCenterJSON()`)**:
   - Client-side downloadable structured JSON dossier formatted with 2-space indentation.
