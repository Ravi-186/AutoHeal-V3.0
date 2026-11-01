# AutoHeal & ShopSphere: Feature Inventory & Functional Audit

**Author:** Senior Quality & Architecture Engineering Group  
**Date:** 2026-11-01  
**Project:** AutoHeal Autonomous SOC Platform  
**Document Ref:** `FEAT-AUDIT-001`  

---

## 1. Audit Methodology & Feature Classification

Every identified capability in ShopSphere and AutoHeal has been evaluated against nine functional dimensions:
1. **UI Exists:** Is there a user interface or interactive template?
2. **Backend Exists:** Is the underlying python logic implemented?
3. **API Functional:** Does the REST endpoint execute without unhandled exceptions?
4. **Service Target:** Does it target the intended service component?
5. **Data Persisted:** Are entity state changes committed to SQLite?
6. **Validation:** Are inputs validated via Pydantic/Schemas?
7. **Authorization:** Is access restricted via role/token checks?
8. **Error & Loading Handled:** Are edge cases and failures presented cleanly?
9. **Covered by Tests:** Is there an automated unit/integration test?

### Classification Legend
- **WORKING:** Feature is complete, verified by tests, and operates end-to-end.
- **PARTIALLY WORKING:** Core logic runs but exhibits edge-case defects, UI mismatches, or fallback dependence.
- **BROKEN:** Endpoint or feature fails to execute, throws unhandled exceptions, or contains empty stubs.
- **MISSING:** Feature referenced in specifications/UI but lacks backend implementation.
- **INSECURE:** Feature works but violates core security principles (hardcoded backdoors, secret leaks).
- **NEEDS OPTIMIZATION:** Works correctly but contains synthetic sleep/delays, redundant queries, or hardcoded strings.

---

## 2. Feature-by-Feature Matrix

### 2.1 Application A: ShopSphere E-Commerce Workflows

| Feature ID | Feature Name | UI | Backend | API | Persisted | Validation | Auth | Tests | Status | Notes / Root Cause |
|---|---|---|---|---|---|---|---|---|---|---|
| **SHOP-01** | User Registration | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | PBKDF2-HMAC-SHA256 salted password hashing; persists to `users` table. |
| **SHOP-02** | Customer Login | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | Returns user profile with Bearer session token. |
| **SHOP-03** | Auth Profile (`/auth/me`) | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **WORKING** | Requires Bearer token; retrieves user record. |
| **SHOP-04** | Master Admin Backdoor | N/A | Yes | Yes | Yes | None | Bypass | No | **INSECURE** | Hardcoded token `token_admin_shopsphere_secret` grants admin bypass in `shopsphere/api.py:89`. |
| **SHOP-05** | Product Browsing & Filtering | Yes | Yes | Yes | Yes | Yes | Public | Yes | **WORKING** | Category, price range, stock, rating, and sorting filters functional. |
| **SHOP-06** | Product Search | Yes | Yes | Yes | Yes | Yes | Public | Yes | **WORKING** | Full text matching over title and description. |
| **SHOP-07** | Shopping Cart Add/Update/Remove | Yes | Yes | Yes | Yes | Yes | Session | Yes | **WORKING** | Session-bound and user-bound cart item operations. |
| **SHOP-08** | Cart Financial Invariant Logic | Yes | Yes | Yes | Yes | Yes | Session | Yes | **WORKING** | Subtotal, discounts, delivery fee (<₹500 = ₹40, >=₹500 = Free). |
| **SHOP-09** | Wishlist Management | Yes | Yes | Yes | Yes | Yes | Session | Yes | **WORKING** | Toggle item in wishlist, move-to-cart operations. |
| **SHOP-10** | Transactional Checkout | Yes | Yes | Yes | Yes | Yes | Session | Yes | **WORKING** | Atomic order creation, inventory stock decrement, generates `ORD-YYYY-XXXXXXXX`. |
| **SHOP-11** | Order History & Order Details | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **WORKING** | Lookup by order ID or customer email. |
| **SHOP-12** | Order Cancellation | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **WORKING** | Cancels order and atomically returns reserved stock to product catalog. |
| **SHOP-13** | Admin Dashboard Analytics | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **WORKING** | Aggregates revenue, order volume, catalog count, low stock warnings. |
| **SHOP-14** | Admin Stock Restock | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **WORKING** | Updates stock levels and appends to `admin_audit_logs`. |
| **SHOP-15** | Admin Order Fulfillment Status | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **WORKING** | Progresses status (PLACED -> SHIPPED -> DELIVERED). |

---

### 2.2 Application B: AutoHeal SOC Core & AppSec Workflows

| Feature ID | Feature Name | UI | Backend | API | Persisted | Validation | Auth | Tests | Status | Notes / Root Cause |
|---|---|---|---|---|---|---|---|---|---|---|
| **SOC-01** | ASGI AppSec Telemetry Interception | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | Intercepts HTTP requests, sanitizes passwords, writes to `security_events`. |
| **SOC-02** | Real-Time Dynamic WAF Quarantine | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | Blocks quarantined IPs in 0.4ms returning HTTP 403 Forbidden. |
| **SOC-03** | SQL Injection Detection (`INJ-001`) | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | Flags UNION SELECT, tautologies, stacked queries with 98% confidence. |
| **SOC-04** | XSS Detection (`XSS-001`) | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | Detects executable scripts and javascript URI schemes. |
| **SOC-05** | Credential Stuffing Detection (`AUTH-001`) | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | Sliding window threshold detector (4+ failed logins in 60s). |
| **SOC-06** | Admin Probing Detection (`AUTH-002`) | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | Flags unauthorized probes against `/api/shop/admin/*`. |
| **SOC-07** | Rate Anomaly Detection (`RATE-001`) | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | Intercepts request volume bursts (>25 req/10s). |
| **SOC-08** | Reliability Cascade Self-Healing (`HEALTH-001`) | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | Intercepts 500 error cascades and triggers database baseline restoration. |
| **SOC-09** | Closed-Loop Quarantine Verification | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | Dual-probe test (Perimeter probe 403 + Benign availability probe 200). |
| **SOC-10** | Bounded Escalation Engine | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | Escalates ISOLATE to BLOCK on verification failure; bounded retries. |
| **SOC-11** | Forensic Dossier Export (JSON) | Yes | Yes | Yes | Yes | Yes | None | Yes | **WORKING** | Exports complete incident dossier as JSON download. |
| **SOC-12** | Forensic Dossier Export (Markdown) | Yes | Yes | Yes | Yes | Yes | None | Yes | **WORKING** | Formatted markdown report with IoC table and timeline. |
| **SOC-13** | Forensic Dossier Export (PDF) | Yes | Yes | Yes | Yes | Yes | None | Yes | **WORKING** | Pure-python PDF 1.4 generation without third-party C binaries. |
| **SOC-14** | Duplicate Export Endpoint Definition | N/A | Yes | Conflict | N/A | N/A | None | No | **BROKEN** | Duplicate `@router.get("/incidents/{incident_id}/export")` in `src/appsec/api.py:90` & `:383`. |
| **SOC-15** | Attack Replay Endpoint | Yes | Stub | Yes | No | Yes | None | No | **BROKEN** | `replay_attack_comparison` in `src/appsec/api.py:375` has empty body returning None. |
| **SOC-16** | Security Posture Scoring | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | 0-100 deterministic scoring with deductions for open vulnerabilities. |
| **SOC-17** | AI Forensic Summary & Advisor | Yes | Yes | Yes | Yes | Yes | N/A | Yes | **WORKING** | Evidence-grounded local LLM summary generation & MITRE alignment. |
| **SOC-18** | Vulnerability Tracker & Patch Gate | Yes | Yes | Yes | Yes | Yes | None | Yes | **WORKING** | Lists vulnerabilities, approvals, applies surgical patches with regression test. |
| **SOC-19** | Live Attack Launcher SSE Stream | Yes | Yes | Yes | Yes | Yes | Localhost | Yes | **WORKING** | Real-time Server-Sent Events stream for attack execution progress. |
| **SOC-20** | Target Allowlisting Safety Guardrail | N/A | Yes | Yes | N/A | Yes | N/A | Yes | **WORKING** | Strict enforcement prohibiting non-localhost targets in `validate_target_safety`. |

---

### 2.3 Application B: Streamlit SOC Command Center & Telemetry

| Feature ID | Feature Name | UI | Backend | API | Persisted | Validation | Auth | Tests | Status | Notes / Root Cause |
|---|---|---|---|---|---|---|---|---|---|---|
| **DASH-01** | Streamlit Command Center Overview | Yes | Yes | Direct | Yes | N/A | None | Manual | **WORKING** | Real-time KPIs, active threats, contained incidents, system logs. |
| **DASH-02** | 3D WebGL Topology Background | Yes | Yes | JS/WebGL | No | N/A | None | Manual | **WORKING** | Three.js particle sphere reacting to network threat states. |
| **DASH-03** | 3D Lateral Movement Attack Path | Yes | Yes | HTML/JS | Yes | N/A | None | Manual | **WORKING** | Three.js attack graph visualizer showing multi-hop progression. |
| **DASH-04** | PostureScorer Import in Dashboard | Yes | Import | Direct | Yes | N/A | None | No | **BROKEN** | `dashboard/app.py:73` imports `PostureScorer` (class is `SecurityPostureScorer`); falls into fallback. |
| **DASH-05** | Total Monitored Devices Calculation | Yes | Yes | Direct | Yes | N/A | None | No | **NEEDS OPT** | `server.py:155` uses synthetic formula `len(devices) * 1152 + 14` instead of real count. |
| **DASH-06** | Hardcoded Remediation Timing | Yes | Yes | Direct | No | N/A | None | No | **NEEDS OPT** | `server.py:426` hardcodes `"remediation_time_ms": 842` and `responder.py:135` adds `+ 12`. |
| **DASH-07** | Manual Device Containment Controls | Yes | Yes | Yes | Yes | Yes | None | Yes | **WORKING** | Isolate, Block, and Restore actions on monitored endpoints. |
| **DASH-08** | Client IP Unblock Management | Yes | Yes | Yes | Yes | Yes | None | Yes | **WORKING** | Unblocks IP from `blocked_clients` table and restores access. |
