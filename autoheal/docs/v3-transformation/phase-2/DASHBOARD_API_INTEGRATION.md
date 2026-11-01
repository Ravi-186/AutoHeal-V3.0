# AutoHeal v3.0 — Phase 2: Dashboard API Integration Specification

**Document Version:** 3.0.0  
**Status:** Certified & Implemented  
**Author:** Backend Integration Engineer & Senior Frontend Architect  
**Subsystem:** FastAPI AppSec Core Daemon & Executive Analytics Engine

---

## 1. Overview & Architectural Principles

The Executive SOC Command Center integrates directly with the existing AutoHeal FastAPI service layer. All data is retrieved from production database tables in `shopsphere.db` (`security_events`, `security_incidents`, `blocked_clients`, and `vulnerabilities`).

### Core Integration Principles:
1. **Zero Fabrication:** No random numbers or decorative simulated charts.
2. **Backward Compatibility:** All existing endpoints (`/api/security/metrics`, `/api/security/incidents`) preserve 100% of their legacy JSON response keys.
3. **Optimized Aggregations:** Complex groupings and time-window slices are computed within `ExecutiveAnalyticsEngine` using indexed SQLite queries with sub-15ms response times.
4. **SSE Telemetry Streaming:** Real-time push telemetry via `/api/security/events/stream` with automated client reconnect and graceful polling fallback.

---

## 2. API Endpoints Catalog

### Endpoint 1: `/api/security/metrics`

- **Method:** `GET`
- **Purpose:** Primary telemetry aggregation endpoint providing all 8 KPI metrics, trend percentages, severity distributions, lifecycle pipeline counts, detection rule summaries, and self-healing verification status.
- **Query Parameters:**
  - `time_range` (`str`, optional, default: `"24h"`): Window identifier (`"1h"`, `"24h"`, `"7d"`, `"30d"`, `"all"`, `"custom"`).
  - `start_time` (`str`, optional): ISO-8601 start timestamp for custom ranges.
  - `end_time` (`str`, optional): ISO-8601 end timestamp for custom ranges.

#### Response Schema (JSON):
```json
{
  "status": "OPERATIONAL",
  "total_events_recorded": 7741,
  "total_incidents": 452,
  "active_blocked_ips": 3,
  "incidents_by_severity": { "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0 },
  "active_threats": 0,
  "average_remediation_ms": 1200.0,
  "time_range": "24h",
  "total_security_events": 7741,
  "active_incidents": 0,
  "critical_incidents": 0,
  "resolved_incidents": 0,
  "verified_remediations": 0,
  "mean_time_to_detect_ms": 1800.0,
  "mean_time_to_respond_ms": 1200.0,
  "system_availability_percent": 100.0,
  "kpis": [
    {
      "id": "statTotalEvents",
      "label": "Total Security Events",
      "value": 7741,
      "formatted": "7,741",
      "icon": "fa-solid fa-database",
      "trend_pct": 12.4,
      "trend_label": "vs prior period",
      "tooltip": "Total raw and correlated HTTP security telemetry events processed in selected window",
      "severity": "info"
    }
  ],
  "kpi_trends": {
    "events_delta_percent": 12.4,
    "incidents_delta_percent": -5.2,
    "critical_delta_percent": -10.0
  },
  "threat_severity_distribution": {
    "events": { "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 7741 },
    "incidents": { "CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0 }
  },
  "incident_lifecycle": {
    "new": 120,
    "triaged": 0,
    "investigating": 32,
    "containment": 240,
    "remediation": 25,
    "verification": 0,
    "resolved": 23
  },
  "detection_rules": [
    {
      "rule_id": "INJ-001",
      "name": "SQL Injection Attack",
      "category": "Injection",
      "severity": "CRITICAL",
      "mitre_technique": "T1190 - Exploit Public-Facing Application",
      "incident_count": 234,
      "detection_count": 468
    }
  ],
  "remediation_analytics": {
    "successful": 3,
    "failed": 0,
    "verification_failures": 37,
    "rolled_back": 1,
    "pending_approvals": 1,
    "success_rate_percent": 75.0
  },
  "self_healing_status": {
    "active_jobs": 0,
    "completed_jobs": 0,
    "failed_jobs": 0,
    "verification_failures": 37,
    "pending_approvals": 1,
    "attacker_verification": true,
    "benign_user_verification": true,
    "dual_probe_confirmed": true,
    "attacker_probe_status": "QUARANTINED (403 Forbidden)",
    "benign_probe_status": "UNIMPAIRED (200 OK)",
    "last_incident_id": "INC-2026-0F493FFE",
    "last_action_summary": "Perimeter IP Block & Rate Throttling verified via dual loopback probe."
  }
}
```

---

### Endpoint 2: `/api/security/analytics/timeline`

- **Method:** `GET`
- **Purpose:** Retrieves time-bucketed event counts and severities for responsive Chart.js line timeline rendering.
- **Query Parameters:**
  - `time_range` (`str`, optional, default: `"24h"`): Time range identifier.
  - `category` (`str`, optional): Attack category filter (`"ALL"`, `"INJ"`, `"AUTH"`, `"XSS"`, `"RATE"`).
  - `severity` (`str`, optional): Severity filter (`"ALL"`, `"CRITICAL"`, `"HIGH"`, `"MEDIUM"`, `"INFO"`).
  - `num_buckets` (`int`, optional, default: `12`): Number of uniform time slices (`6` to `30`).

#### Response Schema (JSON):
```json
{
  "status": "success",
  "time_range": "24h",
  "labels": ["10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00", "00:00", "02:00", "04:00", "06:00", "08:00"],
  "counts": [45, 120, 85, 340, 210, 95, 410, 620, 310, 180, 240, 95],
  "critical": [5, 12, 8, 40, 25, 10, 45, 80, 35, 20, 30, 10],
  "high": [10, 30, 20, 85, 50, 25, 105, 155, 75, 45, 60, 25],
  "medium": [10, 25, 20, 70, 45, 20, 80, 125, 65, 35, 50, 20],
  "info": [20, 53, 37, 145, 90, 40, 180, 260, 135, 80, 100, 40],
  "bucket_duration": "Uniform 12-Slice",
  "total_events": 2750
}
```

---

### Endpoint 3: `/api/security/activity/feed`

- **Method:** `GET`
- **Purpose:** Returns a chronological real-time activity feed combining raw HTTP security events, correlated incidents, and defense remediation actions.
- **Query Parameters:**
  - `limit` (`int`, optional, default: `25`, max: `100`): Maximum items returned.

#### Response Schema (JSON):
```json
[
  {
    "id": "INC-2026-0F493FFE",
    "type": "incident",
    "timestamp": "2026-11-01 04:59:59",
    "severity": "CRITICAL",
    "title": "SQL Injection Attack",
    "description": "Target Category: Injection • Verification: VERIFIED_CONTAINED",
    "source": "198.51.100.88",
    "source_ip": "198.51.100.88",
    "endpoint": "/api/shop/search",
    "status": "CONTAINED",
    "link_id": "INC-2026-0F493FFE",
    "link_target": "pageInvestigation"
  },
  {
    "id": "EVT-007741",
    "type": "event",
    "timestamp": "2026-11-01 04:59:58",
    "severity": "CRITICAL",
    "title": "SQL INJECTION DETECTED",
    "description": "GET /api/shop/search returned HTTP 403",
    "source": "198.51.100.88",
    "source_ip": "198.51.100.88",
    "endpoint": "/api/shop/search",
    "status": "Quarantined (403)",
    "link_id": "EVT-007741",
    "link_target": "pageEvents"
  }
]
```

---

### Endpoint 4: `/api/security/health/detailed`

- **Method:** `GET`
- **Purpose:** Diagnostic health evaluation across all 8 security subsystems measuring live execution latency and operational status.

#### Response Schema (JSON):
```json
{
  "status": "HEALTHY",
  "overall_status": "healthy",
  "total_subsystems": 8,
  "healthy_subsystems": 8,
  "timestamp": "2026-11-01T06:34:42.123456+00:00",
  "evaluation_duration_ms": 2.45,
  "subsystems": [
    {
      "id": "api",
      "name": "FastAPI Core Daemon",
      "status": "healthy",
      "status_upper": "HEALTHY",
      "latency_ms": 0.4,
      "details": "Responding on HTTP/1.1 with Uvicorn ASGI async broker"
    },
    {
      "id": "database",
      "name": "SQLite WAL Telemetry Store",
      "status": "healthy",
      "status_upper": "HEALTHY",
      "latency_ms": 0.85,
      "details": "Journal mode: WAL • Total events: 7,741"
    },
    {
      "id": "ingestion",
      "name": "AppSec Telemetry Ingestion",
      "status": "healthy",
      "status_upper": "HEALTHY",
      "latency_ms": 1.1,
      "details": "Active stream ingestion with automated credential redaction"
    },
    {
      "id": "worker",
      "name": "Autonomous Correlation Worker",
      "status": "healthy",
      "status_upper": "HEALTHY",
      "latency_ms": 2.4,
      "details": "60s sliding correlation window active with multi-step attack detection"
    },
    {
      "id": "queue",
      "name": "Perimeter Quarantine Queue",
      "status": "healthy",
      "status_upper": "HEALTHY",
      "latency_ms": 0.8,
      "details": "3 active IP blocks in perimeter quarantine"
    },
    {
      "id": "detection_engine",
      "name": "Rule-Based Detection Engine",
      "status": "healthy",
      "status_upper": "HEALTHY",
      "latency_ms": 0.6,
      "details": "7/7 detection rules operational (SQLi, XSS, Brute Force, Admin, Rate, Corr, Health)"
    },
    {
      "id": "verification_agent",
      "name": "Dual-Probe Verification Agent",
      "status": "healthy",
      "status_upper": "HEALTHY",
      "latency_ms": 1.5,
      "details": "Synthetic perimeter (403) and availability (200) loopback verification active"
    },
    {
      "id": "ai_provider",
      "name": "AI Threat Classifier / Ollama",
      "status": "healthy",
      "status_upper": "HEALTHY",
      "latency_ms": 3.2,
      "details": "Evidence-grounded heuristic advisor & MITRE ATT&CK mapping active"
    }
  ]
}
```

---

### Endpoint 5: `/api/security/events/stream`

- **Method:** `GET`
- **Content-Type:** `text/event-stream`
- **Purpose:** Server-Sent Events (SSE) telemetry transport pushing real-time events as they occur in ASGI middleware with periodic 15-second heartbeat keepalives.

---

*Certified integrated and tested across all endpoints with HTTP 200 responses.*
