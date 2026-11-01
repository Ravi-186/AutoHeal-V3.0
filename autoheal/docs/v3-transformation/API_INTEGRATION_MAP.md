# AutoHeal v3.0 — API Integration & Telemetry Binding Map
**Document ID:** AH-V3-API-001  
**Architecture:** RESTful JSON APIs + Server-Sent Events (SSE) Telemetry Stream  
**Target Baseline:** FastAPI 0.162.0 / Python 3.13.7  

---

## 1. Executive Telemetry Policy

**Strict Completion Rule Compliance:**  
1. **Zero Mock Telemetry:** Every KPI tile, chart curve, incident table row, quarantine entry, and AST diff binds directly to an active FastAPI backend route.
2. **Real Statuses:** Status indicators (`HEALTHY`, `DEGRADED`, `CRITICAL`, `CONTAINED`) reflect verified database records and background worker states.
3. **Graceful Fallbacks:** In the event of transient network interruption, explicit empty, loading, or retry states are rendered rather than fake numbers.

---

## 2. Telemetry Endpoints & Component Bindings

### 2.1 Executive Overview Dashboard (`pageOverview`)

| UI Component | Backend Endpoint | Method | Response Payload Mapping | Refresh Cadence |
| :--- | :--- | :--- | :--- | :--- |
| **KPI: Total Events** | `/api/security/metrics` | `GET` | `response.total_events` | Polling (3s) |
| **KPI: Active Incidents** | `/api/security/metrics` | `GET` | `response.active_incidents` | Polling (3s) |
| **KPI: Blocked Attackers** | `/api/security/metrics` | `GET` | `response.blocked_clients` | Polling (3s) |
| **KPI: Contained Threats** | `/api/security/metrics` | `GET` | `response.contained_threats` | Polling (3s) |
| **KPI: Posture Score** | `/api/security/posture` | `GET` | `response.posture_score` (0-100) | Polling (10s) |
| **KPI: MTTD / MTTR** | `/api/security/posture` | `GET` | `response.mttd_seconds`, `response.mttr_seconds` | Polling (10s) |
| **Chart: Event Trends** | `/api/security/events?limit=100` | `GET` | Aggregated timestamps & event counts per bucket | On Tab / Refresh |
| **Chart: Threat Severity** | `/api/security/incidents` | `GET` | Grouped count by `severity` (CRITICAL, HIGH, MEDIUM, LOW) | On Tab / Refresh |
| **Live Activity Feed** | `/api/security/events?limit=10` | `GET` | Top 10 recent events with icons, IPs, and tags | Polling (3s) |

---

### 2.2 Live Threat Center (`pageEvents`)

| UI Component | Backend Endpoint | Method | Parameters | Action / Result |
| :--- | :--- | :--- | :--- | :--- |
| **Live Telemetry Table** | `/api/security/events` | `GET` | `limit=100`, `category=...`, `severity=...` | Populates forensic table rows with IP, timestamp, type, severity |
| **Event Search Filter** | Client-side filter | N/A | Evaluates against retrieved `allFetchedEvents` | Real-time DOM filtering |
| **Event Detail Drawer** | Selected Event Object | N/A | Bound to clicked row data | Displays request headers, path, payload, and raw JSON |
| **Export Telemetry** | Client JSON/CSV generator | N/A | Exports current filtered view | Triggers browser file download (`autoheal-events-YYYYMMDD.csv`) |

---

### 2.3 Attack Simulation Center (`pageAttackCenter`)

| UI Component | Backend Endpoint | Method | Payload / Parameters | Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Scenario Cards** | Built-in scenario registry | N/A | 6 Scenarios: SQLi, XSS, Credential Stuffing, DoS, Admin Probe, Health Cascade | Renders scenario descriptions, risk levels, target endpoint |
| **Launch Test Button** | `/api/security/test/run` | `POST` | `{"scenario": "sqli_auth_bypass", "intensity": 3}` | Dispatches asynchronous attack simulation runner |
| **Stop Test Button** | `/api/security/test/stop` | `POST` | Empty | Cancels active scenario runner |
| **Live SSE Telemetry** | `/api/security/attack-center/stream` | `GET` | SSE EventSource connection | Streams live step execution, detections, mitigation, and verification results |
| **Attack Replay Test** | `/api/security/test/replay` | `POST` | `{"scenario": "sqli_auth_bypass"}` | Replays attack payload to verify defense barrier (403 expected) |

---

### 2.4 Incident Command Center (`pageIncidents`)

| UI Component | Backend Endpoint | Method | Parameters | Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Incident Triage Queue** | `/api/security/incidents` | `GET` | Status filters: `ALL`, `OPEN`, `MITIGATING`, `CONTAINED` | Renders cards with severity badge, time elapsed, attacker IP, vector |
| **Incident Forensics Dossier** | `/api/security/incidents/{id}` | `GET` | `incident_id` | Opens full investigative workspace with timeline and payload evidence |
| **AI Incident Summary** | `/api/security/incidents/{id}/ai-summary` | `GET` | `incident_id` | Returns LLM-generated forensic root-cause analysis and MITRE mapping |
| **Incident Formal Report** | `/api/security/incidents/{id}/report` | `GET` | `incident_id` | Returns complete forensic report JSON with export-ready markdown |

---

### 2.5 SOAR Automation Center (`pageSoar`)

| UI Component | Backend Endpoint | Method | Parameters | Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Playbook Catalog** | Active playbooks | `GET` | Core playbooks: Credential Lockdown, SQLi Containment, DoS Shaper | Renders visual playbook nodes and trigger conditions |
| **Active Quarantined IPs**| `/api/security/blocked-clients` | `GET` | None | Lists IP, reason, quarantined_at, expires_at, block_count |
| **Manual Unblock Action**| `/api/security/unblock` | `POST` | `{"client_id": ip_address}` | Removes client from quarantine, restores access, logs audit event |

---

### 2.6 Self-Healing Center (`pageHealing`)

| UI Component | Backend Endpoint | Method | Parameters | Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Vulnerabilities Inventory**| `/api/security/vulnerabilities` | `GET` | None | Lists detected vulnerabilities with AST patch status |
| **Inspect AST Diff** | `/api/security/vulnerabilities/{id}` | `GET` | `vuln_id` | Renders before/after code diff in syntax-highlighted editor |
| **Approve & Apply Patch** | `/api/security/vulnerabilities/{id}/apply` | `POST` | `vuln_id` | Applies verified AST patch directly to target code file |
| **Rollback Patch** | `/api/security/vulnerabilities/{id}/rollback` | `POST` | `vuln_id` | Reverts code patch back to clean state from backup snapshot |
| **Dual-Probe Verification** | `/api/security/vulnerabilities/{id}/test` | `POST` | `vuln_id` | Runs verification: Attacker Probe (expect 403) and Benign Probe (expect 200) |

---

### 2.7 Asset Management & Threat Topology (`pageTopology`)

| UI Component | Backend Endpoint | Method | Parameters | Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Asset Directory Table** | `/api/state` | `GET` | None | Renders monitored devices, network zones, role, IP, threat state, risk score |
| **3D / 2.5D Topology Canvas**| `/api/state` + Three.js | Canvas | Parsed devices & connections | Interactive WebGL network graph with node selection and threat pulse |
| **Accessible 2D Table Fallback**| Toggle button | DOM | Switches between WebGL canvas and structured tabular view | Complete WCAG 2.2 AA accessibility compliance |

---

### 2.8 Audit & System Health (`pageSettings`)

| UI Component | Backend Endpoint | Method | Parameters | Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **System Health Matrix** | `/api/health` | `GET` | None | Reports FastAPI status, model status, monitored assets, active threats |
| **Configuration Controls** | Backend settings | `GET`/`POST`| Rate limit limits, failed login counts | Updates runtime defense parameters in security middleware |
