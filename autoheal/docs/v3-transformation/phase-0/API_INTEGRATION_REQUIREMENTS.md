# AutoHeal v3.0 — Phase 0: API Integration Requirements & Data Contracts
**Document ID:** AH-V3-P0-AIR-001  
**Project Baseline:** AutoHeal v2.5.0-PROD  
**Target Architecture:** FastAPI REST & Server-Sent Events (SSE) Protocol  
**Status:** Certified Engineering Specification  

---

## 1. Executive Policy: Zero Fabricated Data

All data consumed by the AutoHeal v3.0 SOC Sentinel Console and ShopSphere Storefront must originate from verified backend endpoints:
1. **No Client-Side Synthetic Mock Arrays:** All counts, charts, tables, and status pills must reflect actual database records in SQLite or real-time daemon state.
2. **Graceful Handling of Empty States:** When no incidents or events exist, the UI must render an informative empty state rather than populating placeholder records.
3. **Explicit Error Boundaries:** If an API endpoint fails or returns a non-200 HTTP code, the frontend must display an explicit error alert with retry capabilities.

---

## 2. API Contract & Payload Specifications

### 2.1 Security Metrics Endpoint
- **URL:** `GET /api/security/metrics`
- **Headers:** `Accept: application/json`
- **Response Schema:**
```json
{
  "total_events_recorded": 124,
  "active_threats": 0,
  "active_blocked_ips": 0,
  "contained_threats": 3,
  "total_incidents": 3,
  "critical_incidents": 1,
  "high_incidents": 2
}
```
- **Frontend Consumer:** `loadDashboardMetrics()` updating `#statTotalEvents`, `#statActiveIncidents`, `#statQuarantinedIps`, `#statVerifiedContained`, and `#navIncidentCount`.
- **Polling Cadence:** Every 3,000 ms (3 seconds).

---

### 2.2 Security Posture Endpoint
- **URL:** `GET /api/security/posture`
- **Response Schema:**
```json
{
  "posture_score": 92,
  "rating": "GRADE A • HARDENED & RESILIENT",
  "pillars": [
    { "name": "Runtime Protection", "score": 95, "status": "EXCELLENT" },
    { "name": "Autonomous Containment", "score": 90, "status": "HARDENED" },
    { "name": "Surgical AST Healing", "score": 92, "status": "VERIFIED" },
    { "name": "Telemetry Verification", "score": 94, "status": "OPTIMAL" },
    { "name": "Zero-Trust Segmentation", "score": 88, "status": "RESILIENT" }
  ],
  "mttd_seconds": 0.42,
  "mttr_seconds": 1.15,
  "active_bans_count": 0,
  "verification_rate_percent": 100
}
```
- **Frontend Consumer:** `loadSecurityPosture()` updating circular gauge `#postureScoreVal`, `#postureRatingBadge`, and progress bars in `#defensePillarsContainer`.

---

### 2.3 Live Telemetry Events Endpoint
- **URL:** `GET /api/security/events`
- **Query Parameters:** `limit` (default: 100), `event_type` (optional filter), `severity` (optional filter).
- **Response Schema:** Array of Event objects:
```json
[
  {
    "event_id": "EVT-20261101-0012",
    "timestamp": "2026-11-01T10:30:15.120Z",
    "event_type": "SQL_INJECTION_PROBE",
    "severity": "CRITICAL",
    "client_ip": "198.51.100.42",
    "method": "POST",
    "path": "/api/shop/auth/login",
    "status_code": 403,
    "action_taken": "Quarantined (403)",
    "correlation_id": "CORR-8921A",
    "headers": {
      "user-agent": "AutoHeal-Adversary-Tester/2.5",
      "accept": "application/json"
    },
    "payload": {
      "username": "admin' OR '1'='1' --",
      "password": "WrongPassword123"
    }
  }
]
```
- **Frontend Consumer:** `loadSecurityEvents()` and `renderEventsTable()`.

---

### 2.4 Server-Sent Events (SSE) Attack Center Telemetry
- **URL:** `GET /api/security/attack-center/stream`
- **Protocol:** `text/event-stream` (SSE EventSource)
- **Query Parameters:** `scenario`, `target_url`, `client_ip`, `attempts`, `payload`.
- **Event Stream Formats:**
  1. *Phase Notification:* `{"type": "phase", "phase": "DISPATCH_START", "message": "Fired attack probe..."}`
  2. *HTTP Request Result:* `{"type": "request", "method": "POST", "endpoint": "/api/shop/auth/login", "status_code": 403, "duration_ms": 14}`
  3. *Detection Event:* `{"type": "detection", "rule_id": "RULE-SQLI-001", "category": "SQL Injection", "confidence": 0.98, "mitigation_action": "Dynamic Quarantine"}`
  4. *Verification Result:* `{"type": "verification", "endpoint": "/api/shop/auth/login", "status_code": 403, "is_blocked": true}`
  5. *Execution Complete:* `{"type": "complete", "incident_id": "INC-8921", "duration_sec": 1.8}`
- **Frontend Consumer:** `launchAttackTest()` listening via `new EventSource(sseUrl)`.

---

### 2.5 Self-Healing AST Patch Management Endpoints
- **List Patches:** `GET /api/security/vulnerabilities`
- **Get Patch Diff:** `GET /api/security/vulnerabilities/{id}`
- **Execute Regression Test:** `POST /api/security/vulnerabilities/{id}/test`
- **Operator Approval Gate:** `POST /api/security/vulnerabilities/{id}/approve` (Body: `{"approver": "Lead SecOps Engineer"}`)
- **Apply Live Patch:** `POST /api/security/vulnerabilities/{id}/apply`
- **Rollback Patch:** `POST /api/security/vulnerabilities/{id}/rollback`

---

### 2.6 Dynamic IP Quarantine Endpoints
- **List Quarantined IPs:** `GET /api/security/blocked-clients`
- **Unblock Single IP:** `POST /api/security/unblock` (Body: `{"client_ip": "..."}`)

---

### 2.7 Network Assets State Endpoint
- **URL:** `GET /api/state`
- **Response Schema:**
```json
{
  "devices": [
    { "id": "DEV001", "role": "ShopSphere API Gateway", "ip": "10.0.1.10", "state": "Normal", "zone": "DMZ", "risk_score": 10 },
    { "id": "DEV002", "role": "ShopSphere SQLite DB", "ip": "10.0.2.20", "state": "Normal", "zone": "Database LAN", "risk_score": 5 },
    { "id": "DEV003", "role": "Edge Security Sentinel", "ip": "10.0.0.1", "state": "Normal", "zone": "Perimeter", "risk_score": 12 },
    { "id": "DEV004", "role": "Corporate LAN Workstation", "ip": "192.168.1.105", "state": "Normal", "zone": "Internal LAN", "risk_score": 15 }
  ],
  "active_threats": 0,
  "logs": []
}
```
- **Frontend Consumer:** `initTopology3D()` (Three.js WebGL canvas) and `loadTopologyAssets()` (accessible 2D table).
