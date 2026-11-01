# AutoHeal Phase 8: REST API Reference Manual

## 1. Overview

Phase 8 exposes two primary API sub-routers mounted directly into the AutoHeal FastAPI application:
- **Threat Topology Router**: `/api/threat-topology`
- **AI SOC Copilot Router**: `/api/copilot`

Both routers are classified as control plane services and are whitelisted from automated perimeter rate limiting.

---

## 2. Threat Topology Endpoints (`/api/threat-topology`)

### 2.1 Get Full Topology Graph
- **Method**: `GET`
- **Path**: `/api/threat-topology/graph`
- **Query Parameters**:
  - `time_range` (`string`, optional): Time window (`1h`, `24h`, `7d`, `all`). Default: `all`.
  - `severity` (`string`, optional): Severity filter (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `ALL`). Default: `ALL`.
  - `limit` (`integer`, optional): Max nodes to return (1-500). Default: `100`.
- **Response**: `200 OK`
```json
{
  "nodes": [
    {
      "id": "IP-198.51.100.99",
      "label": "198.51.100.99",
      "type": "SOURCE_IP",
      "severity": "CRITICAL",
      "status": "BLOCKED",
      "position": {"x": 128.45, "y": -12.30, "z": 30.0},
      "color": "#EF4444",
      "degree": 8,
      "metadata": {}
    }
  ],
  "edges": [
    {
      "id": "EDGE-IP-198.51.100.99->EP-/api/cart",
      "source": "IP-198.51.100.99",
      "target": "EP-/api/cart",
      "type": "TARGETS",
      "status": "CONFIRMED",
      "style": "solid",
      "color": "#38BDF8"
    }
  ],
  "total_nodes": 1,
  "total_edges": 1
}
```

### 2.2 Get Entity Details
- **Method**: `GET`
- **Path**: `/api/threat-topology/entities/{type}/{id}`
- **Path Parameters**:
  - `type`: Entity taxonomy string (`SOURCE_IP`, `TARGET_ENDPOINT`, `SECURITY_INCIDENT`, etc.).
  - `id`: Raw entity identifier.
- **Response**: `200 OK` or `404 Not Found`.

### 2.3 Get Attack Sequence
- **Method**: `GET`
- **Path**: `/api/threat-topology/attack-sequence`
- **Query Parameters**:
  - `incident_id` (`string`, required): Target incident identifier.
- **Response**: `200 OK` with ordered `steps` array and `total_steps`.

### 2.4 Get Topology Summary Metrics
- **Method**: `GET`
- **Path**: `/api/threat-topology/summary`
- **Response**: `200 OK` containing node counts, active threat clusters, and blocked entity totals.

### 2.5 Real-Time Telemetry Stream
- **Method**: `GET`
- **Path**: `/api/threat-topology/stream`
- **Headers**: `Accept: text/event-stream`
- **Response**: `200 OK` (Server-Sent Events connection).

---

## 3. AI SOC Copilot Endpoints (`/api/copilot`)

### 3.1 Get AI Provider Status
- **Method**: `GET`
- **Path**: `/api/copilot/provider-status`
- **Response**: `200 OK`
```json
{
  "provider": "DETERMINISTIC_GROUNDED",
  "provider_display_name": "Deterministic Grounded Analyst Engine (Local SQLite Grounded)",
  "model": "rule-correlation-v3.0",
  "online": true,
  "mode": "deterministic_grounded",
  "external_llm_configured": false,
  "telemetry_sources_active": 7
}
```

### 3.2 Get Suggested Prompts
- **Method**: `GET`
- **Path**: `/api/copilot/suggested-prompts`
- **Response**: `200 OK` returning context-aware prompt templates for the active incident.

### 3.3 Retrieve Grounded Evidence
- **Method**: `GET`
- **Path**: `/api/copilot/evidence`
- **Query Parameters**:
  - `incident_id` (`string`, required): Incident ID to assemble evidence for.
- **Response**: `200 OK` with sanitized incident, events, remediations, SOAR executions, rule metadata, and citations.

### 3.4 Deep Incident Investigation
- **Method**: `GET`
- **Path**: `/api/copilot/investigate/{incident_id}`
- **Response**: `200 OK` containing calibrated confidence, confirmed facts, root cause analysis, hypotheses, and recommended playbooks.

### 3.5 Copilot Conversational Chat
- **Method**: `POST`
- **Path**: `/api/copilot/chat`
- **Request Body**:
```json
{
  "message": "Explain what detection rule triggered in this incident.",
  "incident_id": "INC-1004",
  "analyst_id": "SOC-ANALYST-1",
  "session_id": "SESS-20261101-01"
}
```
- **Response**: `200 OK`
```json
{
  "session_id": "SESS-20261101-01",
  "reply": "Investigation of incident INC-1004 reveals that Detection Rule SQLI-001 (SQL Injection Probe) triggered on /api/cart...",
  "facts": ["Payload ' OR 1=1-- detected", "HTTP 403 returned"],
  "hypotheses": ["Potential automated vulnerability scan"],
  "citations": [{"id": "INC-1004", "type": "INCIDENT", "claim": "SQL Injection on /api/cart"}],
  "confidence_score": 0.95,
  "provider": "DETERMINISTIC_GROUNDED"
}
```

### 3.6 Generate Formal Incident Report
- **Method**: `POST`
- **Path**: `/api/copilot/reports/generate`
- **Query / Body Parameters**:
  - `incident_id` (`string`, required): Incident to report on.
  - `author` (`string`, optional): Analyst name or role.
- **Response**: `200 OK` with 12-section report object and cryptographic audit hash.

### 3.7 List Historical Reports
- **Method**: `GET`
- **Path**: `/api/copilot/reports`
- **Query Parameters**:
  - `incident_id` (`string`, optional): Filter reports by incident.
  - `limit` (`integer`, optional): Max reports to return.
- **Response**: `200 OK` returning array of persisted report records.

### 3.8 Get Report by ID
- **Method**: `GET`
- **Path**: `/api/copilot/reports/{report_id}`
- **Response**: `200 OK` or `404 Not Found`.
