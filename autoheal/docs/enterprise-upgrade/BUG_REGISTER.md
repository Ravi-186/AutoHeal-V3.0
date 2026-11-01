# AutoHeal & ShopSphere: Enterprise Bug Register

**Author:** QA Automation & Software Reliability Engineering Group  
**Date:** 2026-11-01  
**Project:** AutoHeal Autonomous SOC Platform  
**Document Ref:** `BUG-REG-001`  

---

## 1. Summary of Discovered Software Defects & Resolution Status

| Bug ID | Severity | Component | Summary | Status | Verification Test / Evidence |
|---|---|---|---|---|---|
| **BUG-001** | **CRITICAL** | Dependencies | Missing `fastapi` and `plotly` dependencies preventing application startup and unit tests | **RESOLVED** | Installed in `.venv`; 72/72 tests pass |
| **BUG-002** | **HIGH** | Dashboard / AppSec | Streamlit dashboard imports `PostureScorer` instead of `SecurityPostureScorer`, breaking posture score calculation | **RESOLVED** | Aliased in `posture_scorer.py` and dual-imported in `dashboard/app.py` |
| **BUG-003** | **HIGH** | AppSec API | Duplicate route definition for `@router.get("/incidents/{incident_id}/export")` in `src/appsec/api.py` | **RESOLVED** | Redundant duplicate route removed; single canonical endpoint |
| **BUG-004** | **HIGH** | AppSec API | `replay_attack_comparison` endpoint has empty implementation body and returns `None` | **RESOLVED** | Full implementation + `test_11_replay_attack_comparison` passed |
| **BUG-005** | **CRITICAL** | ShopSphere Auth | Hardcoded backdoor admin token `token_admin_shopsphere_secret` bypasses authentication | **RESOLVED** | Cryptographic token generation + `TestShopSphereAdminRBAC` passed (13/13 tests) |
| **BUG-006** | **MEDIUM** | AutoHeal Sentinel | Hardcoded calculation formula for `total_devices` (`len(devices) * 1152 + 14`) in `server.py:155` | **RESOLVED** | Replaced with true count `str(len(devices))`; zero fabrication |
| **BUG-007** | **MEDIUM** | AutoHeal Sentinel | Hardcoded remediation latency (`"remediation_time_ms": 842`) and synthetic `+ 12` ms addition | **RESOLVED** | High-resolution `time.perf_counter()` timer measurement implemented; `test_flipkart_heal_measured_latency` passed |
| **BUG-008** | **MEDIUM** | AppSec Metrics | Hardcoded `"average_remediation_ms": 38.5` in `/api/security/metrics` | **RESOLVED** | Dynamic calculation from real persisted incident verification probe telemetry; `test_security_metrics_dynamic` passed |
| **BUG-009** | **MEDIUM** | AppSec Verifier | Synthetic loopback probe fails silently when external HTTP server is offline instead of using in-memory ASGI client | **RESOLVED** | Integrated `TestClient(server_app)` in `security_tester.py` for in-process testing |
| **BUG-010** | **LOW** | Database / Schema | Missing temporal and IP composite indexes on `security_events` causing table scan lag | **RESOLVED** | Added 7 composite performance indexes to `init_db()` in `shopsphere/database.py` |

---

## 2. Defect Breakdown & Root Cause Analysis

### BUG-001: Missing `fastapi` and `plotly` in Active Virtual Environment
- **Severity:** CRITICAL
- **Location:** `AD/.venv` and `autoheal/requirements.txt`
- **Root Cause:** Dependencies declared in `requirements.txt` were not installed into the active `.venv`. When running `python -m unittest discover tests`, 3 test modules failed immediately with `ModuleNotFoundError: No module named 'fastapi'`.
- **Resolution:** Executed `.venv/Scripts/pip.exe install fastapi plotly pytest coverage`.
- **Verification:** All 72 tests across all test suites ran and passed.
- **Status:** **RESOLVED**

---

### BUG-002: Streamlit Dashboard Class Name Mismatch (`PostureScorer`)
- **Severity:** HIGH
- **Location:** `autoheal/dashboard/app.py:73, 81` and `autoheal/src/appsec/posture_scorer.py:188`
- **Root Cause:** `dashboard/app.py` attempts to import `PostureScorer`:
  ```python
  from src.appsec.posture_scorer import PostureScorer
  ```
  However, the class defined in `src/appsec/posture_scorer.py` was named `SecurityPostureScorer`.
- **Resolution:** Added `PostureScorer = SecurityPostureScorer` alias in `posture_scorer.py` and dual-imported both in `dashboard/app.py`.
- **Verification:** `SecurityPostureScorer().calculate_posture()` imports cleanly and calculates dynamic posture score (65/100).
- **Status:** **RESOLVED**

---

### BUG-003: Duplicate Route Definition for `/incidents/{incident_id}/export`
- **Severity:** HIGH
- **Location:** `autoheal/src/appsec/api.py:90` and `autoheal/src/appsec/api.py:383`
- **Root Cause:** The endpoint `@router.get("/incidents/{incident_id}/export")` was defined twice in the same router. The second definition was a partial duplicate that could shadow the primary JSON/PDF/Markdown export handler.
- **Resolution:** Removed the redundant second definition at line 383, leaving the complete, canonical export implementation.
- **Verification:** `TestLiveSecurityTestingPipeline.test_10_incident_export_formats` verified both JSON and PDF export routes return HTTP 200 with appropriate mime types.
- **Status:** **RESOLVED**

---

### BUG-004: Empty Implementation of `replay_attack_comparison`
- **Severity:** HIGH
- **Location:** `autoheal/src/appsec/api.py:380`
- **Root Cause:** The endpoint was declared as an empty stub:
  ```python
  @router.post("/test/replay")
  def replay_attack_comparison(...):
      pass
  ```
- **Resolution:** Implemented full execution logic: executes specified security test scenario against target, measures baseline before state, executes perimeter containment verification, and returns structured comparison (`before_state`, `after_state`, `protection_verified`, `incident_id`).
- **Verification:** `test_11_replay_attack_comparison` passed with HTTP 200 and verified protection state.
- **Status:** **RESOLVED**

---

### BUG-005: Hardcoded Static Backdoor Admin Token in ShopSphere Auth
- **Severity:** CRITICAL
- **Location:** `autoheal/shopsphere/api.py:37` and `autoheal/shopsphere/database.py:293`
- **Root Cause:** ShopSphere API accepted a static hardcoded token `token_admin_shopsphere_secret` with zero expiration or signature verification, completely bypassing RBAC.
- **Resolution:** Removed master backdoor token. Seeded admin and customer accounts now generate cryptographically random tokens (`secrets.token_hex(24)`). Database migration updates any existing legacy backdoor tokens. Updated web template to use active session token from localStorage.
- **Verification:** Added `TestShopSphereAdminRBAC` in `test_shopsphere.py` testing 401 on missing/backdoor tokens, 403 on customer role, and 200 on authenticated admin. (Passed 13/13 tests).
- **Status:** **RESOLVED**

---

### BUG-006: Hardcoded `total_devices` Metric Formula in `server.py`
- **Severity:** MEDIUM
- **Location:** `autoheal/server.py:155`
- **Root Cause:** Line 155 fabricated the monitored device count using an artificial multiplier:
  ```python
  total_devices="{:,}".format(len(devices) * 1152 + 14)
  ```
- **Resolution:** Replaced with the exact, unadulterated length of active devices: `total_devices=str(len(devices))`.
- **Verification:** `TestFastAPIEndpoints.test_get_state` verified accurate, deterministic state reporting.
- **Status:** **RESOLVED**

---

### BUG-007: Hardcoded Remediation Latency & Artificial Offset
- **Severity:** MEDIUM
- **Location:** `autoheal/server.py:426` and `autoheal/src/appsec/responder.py:135`
- **Root Cause:** `server.py` hardcoded `remediation_time_ms: 842`, and `responder.py` artificially added `+ 12` ms to measured duration.
- **Resolution:** Replaced hardcoded values with high-resolution `time.perf_counter()` duration measurements across LangGraph stream and responder execution.
- **Verification:** `test_flipkart_heal_measured_latency` verifies real, measured latency > 0.0ms.
- **Status:** **RESOLVED**

---

### BUG-008: Hardcoded `average_remediation_ms = 38.5` in AppSec Metrics
- **Severity:** MEDIUM
- **Location:** `autoheal/src/appsec/api.py:49`
- **Root Cause:** Metric API returned `38.5` as a hardcoded constant without computing real database telemetry.
- **Resolution:** Implemented dynamic calculation averaging real verification probe latencies and mitigation action execution times recorded in `security_incidents`.
- **Verification:** `test_security_metrics_dynamic` verified that `average_remediation_ms` is computed dynamically from persisted incident records.
- **Status:** **RESOLVED**

---

### BUG-009: Inability of SecurityTester to Execute In-Process Against Test Server
- **Severity:** MEDIUM
- **Location:** `autoheal/src/appsec/security_tester.py:57`
- **Root Cause:** When `testserver` URL was passed in automated test suites, `httpx.Client` attempted socket DNS lookup against `testserver`, failing with `[Errno 11001] getaddrinfo failed`.
- **Resolution:** Integrated `TestClient(server_app)` in `_get_client` for seamless in-process ASGI testing when `testserver` is in the target URL.
- **Verification:** All 11 live security testing pipeline tests pass in-process without network socket dependency.
- **Status:** **RESOLVED**

---

### BUG-010: Missing Database Indexes on Security Telemetry Tables
- **Severity:** LOW
- **Location:** `autoheal/shopsphere/database.py:270`
- **Root Cause:** Telemetry tables `security_events`, `blocked_clients`, and `security_incidents` lacked composite indexes for temporal and IP-filtered queries, leading to full table scans.
- **Resolution:** Added 7 composite indexes to `init_db()`:
  - `idx_blocked_clients_ip_active ON blocked_clients (client_ip, is_active, expires_at)`
  - `idx_security_events_temporal ON security_events (client_ip, timestamp)`
  - `idx_security_events_type_time ON security_events (event_type, timestamp)`
  - `idx_security_incidents_status ON security_incidents (status, severity, created_at DESC)`
  - `idx_orders_customer_email ON orders (customer_email, created_at DESC)`
  - `idx_cart_items_user ON cart_items (user_or_session_id)`
  - `idx_wishlist_user ON wishlist (user_or_session_id)`
- **Verification:** Query plans verified via SQLite `EXPLAIN QUERY PLAN` confirming index scans.
- **Status:** **RESOLVED**
