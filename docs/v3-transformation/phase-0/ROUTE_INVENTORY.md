# AutoHeal v3.0 — Phase 0: Complete Route Inventory
**Document ID:** AH-V3-P0-RTE-001  
**Project Baseline:** AutoHeal v2.5.0-PROD  
**Target Architecture:** FastAPI Web Routes & SPA View State Registry  
**Status:** Certified Audit  

---

## 1. Executive Summary

This document establishes the exhaustive routing inventory for the AutoHeal v3.0 ecosystem. It catalogs:
1. **Top-Level HTTP Web Page Endpoints** (HTML delivery).
2. **SPA Client-Side View State Routes** (DOM workspaces and drawers).
3. **AppSec & Cybersecurity Telemetry APIs** (`/api/security/*`).
4. **Network & System Telemetry APIs** (`/api/state`, `/api/health`).
5. **ShopSphere E-Commerce APIs** (`/api/shop/*`).
6. **Real-time SSE Streaming Endpoints**.

---

## 2. HTTP Web Page Endpoints (HTML Templates)

| HTTP Route | Method | Handler in `server.py` | Template Rendered | Role & Purpose | RBAC / Auth |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET /` | `GET` | `serve_dashboard` | `index.html` | Serves the primary AutoHeal SOC Sentinel Command Center SPA. | Public / Operator Session |
| `GET /shop` | `GET` | `serve_shopsphere` | `shopsphere.html` | Serves the full-stack ShopSphere e-commerce target storefront. | Public / Consumer Session |
| `GET /api/docs` | `GET` | FastAPI OpenAPI UI | Swagger UI | Interactive OpenAPI documentation. | Public (Dev/Audit) |
| `GET /api/redoc`| `GET` | FastAPI ReDoc UI | ReDoc UI | Structural API reference documentation. | Public (Dev/Audit) |

---

## 3. Client-Side SPA View State Inventory (`index.html`)

| View Identifier | DOM Container ID | Navigation Trigger | View Scope & Capabilities | Data Source Endpoints |
| :--- | :--- | :--- | :--- | :--- |
| `nav:overview` | `#pageOverview` | Sidebar Button `1` | Executive KPI ribbon, Security Posture Integrity gauge, recent events, velocity chart | `GET /api/security/metrics`<br>`GET /api/security/posture`<br>`GET /api/security/incidents` |
| `nav:events` | `#pageEvents` | Sidebar Button `2` | High-throughput telemetry log table, category/severity multi-filter, search, pagination | `GET /api/security/events` |
| `nav:attack` | `#pageAttackCenter`| Sidebar Button `3` | Scenario selection (6 tests), intensity slider, dry-run mode, 5-stage SSE stepper, terminal logs | `POST /api/security/test/run`<br>`POST /api/security/test/stop`<br>`GET /api/security/attack-center/stream` |
| `nav:incidents`| `#pageIncidents` | Sidebar Button `4` | Incident queue, forensic dossier workspace, attack timeline, evidence payload inspector, AI summary | `GET /api/security/incidents`<br>`GET /api/security/incidents/{id}` |
| `nav:soar` | `#pageSoar` | Sidebar Button `5` | Visual 5-node playbook flowchart, dynamic IP quarantine registry, instant unblock trigger | `GET /api/security/blocked-clients`<br>`POST /api/security/unblock` |
| `nav:healing` | `#pageHealing` | Sidebar Button `6` | Verified AST patch inventory, code diff viewer, dual-probe verification, atomic rollback | `GET /api/security/vulnerabilities`<br>`POST /api/security/vulnerabilities/{id}/*` |
| `nav:threat-intel`| `#pageThreatIntel`| Sidebar Button `7` | IOC reputation search (IP, domain, hash), adversary vector profiles | `GET /api/security/blocked-clients`<br>`GET /api/security/events` |
| `nav:mitre` | `#pageMitre` | Sidebar Button `8` | 5-tactic matrix grid mapping verified detection rules (T1190, T1059.007, T1110, T1078, T1499) | Detection rule registry |
| `nav:topology` | `#pageTopology` | Sidebar Button `9` | Interactive Three.js WebGL network topology canvas with node pulsing; accessible 2D table fallback | `GET /api/state` |
| `nav:reports` | `#pageReports` | Sidebar Button `10` | Export-ready incident reports list with timestamp, vector, severity, and download triggers | `GET /api/security/incidents` |
| `nav:settings` | `#pageSettings` | Sidebar Button `11` | Security threshold configuration, system diagnostics health matrix, target boundary status | `GET /api/health` |

---

## 4. Backend RESTful API Route Inventory

### 4.1 AppSec & Cybersecurity Endpoints (`src/appsec/api.py`)

| API Route | Method | Description | Request Parameters / Body | Response Payload Format |
| :--- | :--- | :--- | :--- | :--- |
| `/api/security/metrics` | `GET` | Returns aggregated operational KPIs | None | JSON: `{ total_events_recorded, active_threats, active_blocked_ips, total_incidents, ... }` |
| `/api/security/events` | `GET` | Returns paginated telemetry events | `limit` (int), `event_type` (str), `severity` (str) | JSON Array of Event objects with IP, timestamp, method, path, status_code |
| `/api/security/incidents` | `GET` | Returns correlated security incidents | `limit` (int), `status` (str) | JSON Array of Incident objects with vector, severity, affected_endpoints |
| `/api/security/incidents/{id}` | `GET` | Returns full forensic incident dossier | `id` (str) in path | JSON: Incident dossier, timeline, evidence payload |
| `/api/security/incidents/{id}/ai-summary` | `GET` | Generates grounded LLM forensic summary | `id` (str) in path | JSON: `{ summary, root_cause, mitre_technique, recommendation }` |
| `/api/security/incidents/{id}/report` | `GET` | Generates structured formal incident report | `id` (str) in path | JSON: Formatted incident report with exportable markdown |
| `/api/security/posture` | `GET` | Calculates transparent defense score (0-100)| None | JSON: `{ posture_score, rating, pillars, mttd_seconds, mttr_seconds }` |
| `/api/security/blocked-clients` | `GET` | Returns active dynamic IP quarantines | None | JSON Array: `[{ client_ip, reason, blocked_at, expires_at, block_count }]` |
| `/api/security/unblock` | `POST` | Manually removes an IP from quarantine | Body: `{"client_ip": "..."}` | JSON: `{ status: "success", unblocked_ip: "..." }` |
| `/api/security/test/run` | `POST` | Dispatches controlled attack test | Body: `{"scenario": "...", "client_ip": "...", "attempts": 5}` | JSON: `{ status: "started", test_id: "..." }` |
| `/api/security/test/stop` | `POST` | Aborts currently running attack test | None | JSON: `{ status: "stopped" }` |
| `/api/security/test/replay` | `POST` | Replays attack payload to verify defense | Body: `{"scenario": "..."}` | JSON: `{ status: "success", blocked: true, status_code: 403 }` |
| `/api/security/attack-center/stream` | `GET` | Real-time SSE execution telemetry stream | Query: `scenario`, `target_url`, `client_ip`, `attempts` | Text EventStream (`text/event-stream`) streaming JSON messages |
| `/api/security/vulnerabilities` | `GET` | Lists all discovered code vulnerabilities | None | JSON Array: `[{ vuln_id, title, component_path, status, patch_diff }]` |
| `/api/security/vulnerabilities/{id}` | `GET` | Retrieves detailed AST code patch diff | `id` (str) in path | JSON: Vulnerability record with `patch_diff`, before/after lines |
| `/api/security/vulnerabilities/{id}/test` | `POST` | Runs isolated regression test on patch | `id` (str) in path | JSON: `{ test_name, status: "PASSED", duration_ms }` |
| `/api/security/vulnerabilities/{id}/approve` | `POST` | Submits operator approval gate | Body: `{"approver": "Lead SecOps Engineer"}` | JSON: `{ status: "APPROVED", approved_by }` |
| `/api/security/vulnerabilities/{id}/apply` | `POST` | Applies AST surgical patch live | `id` (str) in path | JSON: `{ status: "APPLIED", test_result }` |
| `/api/security/vulnerabilities/{id}/rollback`| `POST` | Rolls back AST patch from snapshot | `id` (str) in path | JSON: `{ status: "ROLLED_BACK" }` |

### 4.2 Network & Health Telemetry APIs (`server.py`)

| API Route | Method | Description | Parameters | Response Payload Format |
| :--- | :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | Returns runtime health & model status | None | JSON: `{ status: "HEALTHY", version: "3.0.0-enterprise", active_threats: 0, ... }` |
| `/api/state` | `GET` | Returns monitored network devices & logs | None | JSON: `{ devices: [{ id, role, ip, state, zone, risk_score }], active_threats, logs }` |

### 4.3 ShopSphere E-Commerce Endpoints (`shopsphere/api.py`)

| API Route | Method | Description | Parameters / Body | Response Payload Format |
| :--- | :--- | :--- | :--- | :--- |
| `/api/shop/products` | `GET` | Returns product catalogue with filters | `category`, `q`, `min_price`, `max_price` | JSON Array: Product records with price, stock, ratings, image SVG |
| `/api/shop/products/{id}` | `GET` | Retrieves single product details | `id` (int) in path | JSON: Single Product object with specifications |
| `/api/shop/auth/login` | `POST` | Authenticates consumer / admin user | Body: `{"email": "...", "password": "..."}` | JSON: `{ success: true, user: { id, email, role } }` |
| `/api/shop/orders` | `POST` | Creates verified order & decrements stock | Body: `{"items": [...], "shipping_address": {...}, "payment_method": "..."}` | JSON: `{ order_id, status: "CONFIRMED", total_amount }` |
| `/api/shop/orders/{id}` | `GET` | Retrieves customer order details | `id` (str) in path | JSON: Order details with item list and tracking status |
| `/api/shop/orders/{id}/cancel` | `POST` | Cancels order & restores stock to SQLite | `id` (str) in path | JSON: `{ status: "CANCELLED", restored_items: [...] }` |
| `/api/shop/admin/stats` | `GET` | Retrieves store revenue & inventory stats | None (Admin RBAC required) | JSON: `{ total_revenue, total_orders, low_stock_items }` |
| `/api/shop/admin/stock` | `POST` | Updates product inventory stock level | Body: `{"product_id": 1, "stock": 50}` | JSON: `{ status: "updated", product_id: 1, new_stock: 50 }` |
| `/api/shop/health/simulate-error` | `GET` | Simulates localized service error for testing | None | JSON / HTTP 500: Cascading failure test |
