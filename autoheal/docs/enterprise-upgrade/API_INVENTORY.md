# AutoHeal & ShopSphere: API Inventory & Contract Specification

**Author:** Senior Full-Stack & Backend Engineering Group  
**Date:** 2026-11-01  
**Project:** AutoHeal Autonomous SOC Platform  
**Document Ref:** `API-INV-001`  

---

## 1. Overview of Exposed API Surfaces

The unified application server (`server.py`) exposes three primary API routers under FastAPI:
1. **AutoHeal Sentinel & System API:** Mounts directly on `/` and `/api/*`.
2. **ShopSphere E-Commerce API:** Mounted under `/api/shop/*`.
3. **AppSec Defense & SOC Operations API:** Mounted under `/api/security/*`.

All endpoints are protected by `AppSecProtectionMiddleware` (which captures telemetry and enforces the dynamic WAF blocklist) and `CORSMiddleware`.

---

## 2. AutoHeal Core Sentinel Endpoints (`server.py`)

| Method | Route | Description | Auth Required | Request Body / Params | Response Model |
|---|---|---|---|---|---|
| `GET` | `/` | Serves main AutoHeal SOC Dashboard HTML | Public | None | `HTMLResponse` |
| `GET` | `/shop` | Serves ShopSphere live e-commerce UI | Public | None | `HTMLResponse` |
| `GET` | `/flipkart` | Serves Flipkart Big Billion Days demo page | Public | None | `HTMLResponse` |
| `GET` | `/api/health` | Production service health check | Public | None | `HealthResponse` |
| `GET` | `/api/state` | Real-time network state & incident logs | Public | None | `NetworkStateResponse` |
| `POST` | `/api/attack/{attack_type}` | Injects adversary scenario (A, B, C, D) | Public | Path: `attack_type` | `AttackResponse` |
| `POST` | `/api/detect` | Triggers LangGraph multi-agent loop | Public | None | `DetectionResponse` |
| `POST` | `/api/device/{id}/restore` | Restores isolated endpoint to Normal | Public | Path: `id` | `DeviceActionResponse` |
| `POST` | `/api/device/{id}/isolate` | Quarantines endpoint onto isolation VLAN | Public | Path: `id` | `DeviceActionResponse` |
| `POST` | `/api/device/{id}/block` | Blocks endpoint at 802.1X switchport | Public | Path: `id` | `DeviceActionResponse` |
| `POST` | `/api/reset` | Resets sandbox devices & history | Public | None | `{"status": "success"}` |
| `GET` | `/api/incidents` | Retrieves all incident dossiers | Public | None | `List[Dict]` |
| `GET` | `/api/flipkart/status` | Microservices shield status | Public | None | `Dict[str, Any]` |
| `POST` | `/api/flipkart/attack/{scenario}` | Triggers Flipkart microservice attack | Public | Path: `scenario` | `Dict[str, Any]` |
| `POST` | `/api/flipkart/restore` | Restores Flipkart microservices | Public | None | `Dict[str, Any]` |

---

## 3. ShopSphere E-Commerce Endpoints (`shopsphere/api.py`)

| Method | Route | Description | Auth Required | Request Model / Params | Response |
|---|---|---|---|---|---|
| `GET` | `/api/shop/products` | Search & filter product catalog | Public | `q`, `category`, `min_price`, `max_price`, `sort_by`, `page` | `ProductListResponse` |
| `GET` | `/api/shop/products/{id}` | Retrieve product details | Public | Path: `id` | `ProductDict` |
| `GET` | `/api/shop/categories` | List all 10 product categories | Public | None | `List[CategoryDict]` |
| `POST` | `/api/shop/auth/register` | Register customer account | Public | `RegisterRequest` (JSON) | `{"status": "success", "user": ...}` |
| `POST` | `/api/shop/auth/login` | Authenticate customer/admin | Public | `LoginRequest` (JSON) | `{"status": "success", "user": ...}` |
| `GET` | `/api/shop/auth/me` | Current user profile | Bearer Token | Header: `Authorization` | `UserDict` |
| `GET` | `/api/shop/cart` | Retrieve active cart | Session / Token | `session_id` or `X-Session-ID` | `CartDict` |
| `POST` | `/api/shop/cart/add` | Add product to cart | Session / Token | `CartItemRequest` (JSON) | `{"status": "success", "cart": ...}` |
| `POST` | `/api/shop/cart/update` | Update cart item quantity | Session / Token | `CartUpdateRequest` (JSON) | `{"status": "success", "cart": ...}` |
| `POST` | `/api/shop/cart/remove` | Remove item from cart | Session / Token | `CartRemoveRequest` (JSON) | `{"status": "success", "cart": ...}` |
| `POST` | `/api/shop/cart/clear` | Clear entire cart | Session / Token | `session_id` or `X-Session-ID` | `{"status": "success"}` |
| `GET` | `/api/shop/wishlist` | Retrieve customer wishlist | Session / Token | `session_id` or `X-Session-ID` | `List[WishlistDict]` |
| `POST` | `/api/shop/wishlist/toggle` | Add/remove from wishlist | Session / Token | `WishlistToggleRequest` (JSON) | `{"status": "success"}` |
| `POST` | `/api/shop/wishlist/move-to-cart`| Move wishlist item to cart | Session / Token | `WishlistToggleRequest` (JSON) | `{"status": "success"}` |
| `POST` | `/api/shop/checkout` | Process order checkout | Session / Token | `CheckoutRequest` (JSON) | `{"status": "success", "order": ...}` |
| `POST` | `/api/shop/cart/checkout` | Alias to checkout | Session / Token | `CheckoutRequest` (JSON) | `{"status": "success", "order": ...}` |
| `GET` | `/api/shop/orders` | Customer order history | Session / Token | `email` or Bearer Token | `List[OrderDict]` |
| `GET` | `/api/shop/orders/{ref_or_id}` | Order details | Session / Token | Path: `order_ref_or_id` | `OrderDict` |
| `POST` | `/api/shop/orders/{id}/cancel` | Cancel order & return stock | Session / Token | Path: `id` | `{"status": "success"}` |
| `GET` | `/api/shop/admin/stats` | Admin metrics & revenue | Admin Role | Header: `Authorization` | `AdminMetricsDict` |
| `POST` | `/api/shop/admin/products/{id}/stock` | Update inventory stock | Admin Role | Path: `id`, `AdminStockUpdateRequest` | `{"status": "success"}` |
| `POST` | `/api/shop/admin/orders/{id}/status` | Update fulfillment state | Admin Role | Path: `id`, `AdminOrderStatusRequest` | `{"status": "success"}` |
| `GET` | `/api/shop/health` | Storefront health probe | Public | None | `{"status": "UP"}` |
| `POST` | `/api/shop/health/simulate-error` | Simulates 500 crash for SOC | Public | None | Throws `RuntimeError` |

---

## 4. AppSec Defense & SOC Operations Endpoints (`src/appsec/api.py`)

| Method | Route | Description | Auth Required | Request / Params | Response |
|---|---|---|---|---|---|
| `GET` | `/api/security/metrics` | Real-time AppSec KPIs | Public | None | `KPIsDict` |
| `GET` | `/api/security/events` | Immutable security log entries | Public | `event_type`, `severity`, `client_ip`, `limit` | `List[EventDict]` |
| `GET` | `/api/security/incidents` | Active & historical incidents | Public | `status`, `severity`, `limit` | `List[IncidentDict]` |
| `GET` | `/api/security/incidents/{id}` | Complete incident dossier | Public | Path: `id` | `IncidentDossierDict` |
| `GET` | `/api/security/incidents/{id}/report` | Markdown incident report | Public | Path: `id` | `PlainTextResponse (text/markdown)` |
| `GET` | `/api/security/incidents/{id}/export` | Export dossier (JSON, MD, PDF) | Public | Path: `id`, Query: `format` | File Attachment Download |
| `POST` | `/api/security/incidents/{id}/remediate` | Manually approve/record fix | Public | Path: `id`, `RemediateRequest` | `{"status": "success"}` |
| `POST` | `/api/security/incidents/{id}/verify` | Trigger verification agent probe | Public | Path: `id` | `VerificationResultDict` |
| `GET` | `/api/security/blocked-clients` | Active WAF IP blocklist entries | Public | None | `List[BlockedClientDict]` |
| `POST` | `/api/security/unblock` | Unblock quarantined IP | Public | `UnblockRequest` (JSON) | `{"status": "success"}` |
| `POST` | `/api/security/scan-telemetry` | Run sliding-window correlation | Public | None | `{"detections_count": ...}` |
| `POST` | `/api/security/test/run` | Launch controlled security test | Localhost | `SecurityTestRunRequest` | `TestExecutionResultDict` |
| `POST` | `/api/security/test/stop` | Immediate test cancellation | Public | None | `{"status": "cancelled"}` |
| `GET` | `/api/security/attack-center/stream` | Stream attack execution via SSE | Localhost | `scenario`, `target_url`, `attempts` | `StreamingResponse (text/event-stream)` |
| `GET` | `/api/security/vulnerabilities` | List tracked code vulnerabilities | Public | Query: `status` | `List[VulnerabilityDict]` |
| `GET` | `/api/security/vulnerabilities/{id}` | Vulnerability & patch diff | Public | Path: `id` | `VulnerabilityDict` |
| `POST` | `/api/security/vulnerabilities/{id}/test` | Run isolated regression test | Public | Path: `id` | `TestResultDict` |
| `POST` | `/api/security/vulnerabilities/{id}/approve` | Formally approve proposed patch | Operator | Path: `id`, `operator_name` | `{"success": true}` |
| `POST` | `/api/security/vulnerabilities/{id}/apply` | Apply patch with verification | Operator | Path: `id`, `operator_name` | `{"success": true}` |
| `POST` | `/api/security/vulnerabilities/{id}/rollback` | Rollback applied patch | Operator | Path: `id`, `operator_name` | `{"success": true}` |
| `GET` | `/api/security/posture` | 0-100 Security Posture Score | Public | None | `PostureScoreBreakdownDict` |
| `GET` | `/api/security/incidents/{id}/ai-summary` | AI forensic summary & MITRE | Public | Path: `id` | `AISummaryDict` |
| `POST` | `/api/security/test/replay` | Attack replay comparison | Localhost | `ReplayRequest` | **BROKEN (returns None)** |

---

## 5. Identified API Issues to Remediate in Architecture Modernization

1. **Duplicate Route Definition:** Line 90 and line 383 of `src/appsec/api.py` both define `@router.get("/incidents/{incident_id}/export")`. Consolidate into a single robust endpoint.
2. **Missing Implementation in Replay Route:** `src/appsec/api.py:374` defines `replay_attack_comparison` with no execution code. Complete the comparison execution logic.
3. **Hardcoded Response Values:**
   - `/api/security/metrics`: Line 49 hardcodes `"average_remediation_ms": 38.5`. Must be dynamically computed from `security_incidents` execution timestamps.
   - `/api/state`: Line 155 hardcodes `total_devices` as `len(devices) * 1152 + 14`. Must return actual monitored asset counts.
   - `/api/flipkart/attack/{scenario}`: Line 426 hardcodes `"remediation_time_ms": 842`. Must record actual elapsed execution duration.
4. **Administrative Backdoor Removal:** Remove `token_admin_shopsphere_secret` from `shopsphere/api.py:89` and require cryptographically valid JWT / Bearer tokens for all administrative endpoints.
