# AutoHeal v2.5.0: Independent Audit New Defect Register

**Auditor:** Independent Lead Security & Reliability Engineer  
**Audit Target:** Baseline Commit `bf47d7a` on Branch `enterprise-upgrade`  
**Remediation Branch:** `enterprise-validation`  
**Classification:** **ENGINEERING DEFECT LOG & REMEDIATION MATRIX**

---

## 1. Defect Summary Table

| Defect ID | Severity | Component | Summary | Status |
| :--- | :--- | :--- | :--- | :--- |
| **NEW-DEF-001** | **HIGH** | `src/appsec/detector.py` | AUTH-002 Detector Bypass via Unchecked Token Substring | **RESOLVED & VERIFIED** |
| **NEW-DEF-002** | **MEDIUM** | `shopsphere/database.py` | Missing Server-Side Session Token Expiration (Indefinite TTL) | **RESOLVED & VERIFIED** |
| **NEW-DEF-003** | **MEDIUM** | `shopsphere/services.py` | Timing-Attack Susceptibility in Token Lookup | **RESOLVED & VERIFIED** |
| **NEW-DEF-004** | **MEDIUM** | `shopsphere/api.py` | Missing Logout / Server-Side Token Revocation Endpoint | **RESOLVED & VERIFIED** |
| **NEW-DEF-005** | **LOW** | `shopsphere/autoheal_engine.py` | Artificial Latency Inflation Offset (`+ 42` ms) in Demo Engine | **RESOLVED & VERIFIED** |
| **NEW-DEF-006** | **MEDIUM** | `src/appsec/middleware.py` | Missing Defense-in-Depth HTTP Security Headers | **RESOLVED & VERIFIED** |
| **NEW-DEF-007** | **HIGH** | `shopsphere/services.py` | Non-Atomic Concurrency Race in Checkout Stock Decrement | **RESOLVED & VERIFIED** |

---

## 2. Detailed Defect Dossiers

### NEW-DEF-001: AUTH-002 Detector Bypass via Unchecked Token Substring
* **Severity:** **HIGH** (CWE-287 / CWE-697)
* **Affected Component:** `autoheal/src/appsec/detector.py:179`
* **Root Cause Analysis:**
  The detector evaluated admin endpoint authorization via:
  `if not auth_header or "token_admin" not in auth_header:`
  An adversary sending an arbitrary fake header such as `Authorization: Bearer token_admin_attacker_forged` caused the substring check to pass, bypassing detection Rule AUTH-002.
* **Remediation:**
  Updated `detector.py` to extract the bearer token, verify that it begins with `token_admin_`, and query `UserService.get_by_token(token)` to ensure the token corresponds to an active, authenticated user with `role == 'admin'`.
* **Regression Test:** `tests/test_audit_validation.py::TestSecurityDefectsAndHardening::test_new_def_001_auth002_detector_bypass_prevention`
* **Status:** **RESOLVED & VERIFIED**

---

### NEW-DEF-002: Missing Server-Side Session Token Expiration
* **Severity:** **MEDIUM** (CWE-613: Insufficient Session Expiration)
* **Affected Component:** `autoheal/shopsphere/database.py`, `autoheal/shopsphere/services.py`
* **Root Cause Analysis:**
  The `users` table only contained a `token TEXT` column without an expiration timestamp. Issued tokens remained valid indefinitely until overwritten by a subsequent login from the same user account.
* **Remediation:**
  1. Added `token_expires_at TIMESTAMP` column to `users` table and migration in `init_db()`.
  2. Set a 7-day TTL (`datetime.now(timezone.utc) + timedelta(days=7)`) on login.
  3. Enforced expiration check in `UserService.get_by_token()`.
* **Regression Test:** `tests/test_audit_validation.py::TestSecurityDefectsAndHardening::test_new_def_002_and_003_token_expiration_and_constant_time_comparison`
* **Status:** **RESOLVED & VERIFIED**

---

### NEW-DEF-003: Timing-Attack Susceptibility in Token Lookup
* **Severity:** **MEDIUM** (CWE-208: Observable Timing Discrepancy)
* **Affected Component:** `autoheal/shopsphere/services.py:625`
* **Root Cause Analysis:**
  Token validation previously relied solely on SQL equality (`WHERE token = ?`). In high-precision side-channel analysis, variable-length byte comparisons can leak token characteristics.
* **Remediation:**
  Added in-memory constant-time digest verification using `secrets.compare_digest(row["token"], token)` within `UserService.get_by_token()`.
* **Regression Test:** `tests/test_audit_validation.py::TestSecurityDefectsAndHardening::test_new_def_002_and_003_token_expiration_and_constant_time_comparison`
* **Status:** **RESOLVED & VERIFIED**

---

### NEW-DEF-004: Missing Logout / Server-Side Token Revocation Endpoint
* **Severity:** **MEDIUM** (CWE-613 / CWE-384)
* **Affected Component:** `autoheal/shopsphere/api.py`, `autoheal/shopsphere/services.py`
* **Root Cause Analysis:**
  The application lacked a logout route. When a user clicked "Logout" on the client, the token was deleted only from browser `localStorage`, leaving the token fully active on the server.
* **Remediation:**
  Implemented `UserService.logout(token)` to clear token fields in SQLite and exposed `POST /api/shop/auth/logout`.
* **Regression Test:** `tests/test_audit_validation.py::TestSecurityDefectsAndHardening::test_new_def_004_server_side_logout_revocation`
* **Status:** **RESOLVED & VERIFIED**

---

### NEW-DEF-005: Artificial Metric Offset (+42 ms) in Demo Engine
* **Severity:** **LOW / CODE INTEGRITY**
* **Affected Component:** `autoheal/shopsphere/autoheal_engine.py:112`
* **Root Cause Analysis:**
  In `run_regression_test()`, execution time was calculated as:
  `elapsed_ms = round((time.time() - start_time) * 1000 + 42, 2)`
  This added an artificial 42 millisecond latency to all diagnostic runs, violating Rule 6 (zero metric fabrication).
* **Remediation:**
  Removed the static `+ 42` offset and upgraded to high-resolution `time.perf_counter()`.
* **Regression Test:** `tests/test_engine.py` and `tests/test_shopsphere.py`
* **Status:** **RESOLVED & VERIFIED**

---

### NEW-DEF-006: Missing Defense-in-Depth HTTP Security Headers
* **Severity:** **MEDIUM** (CWE-693: Protection Mechanism Failure)
* **Affected Component:** `autoheal/src/appsec/middleware.py`
* **Root Cause Analysis:**
  HTTP responses returned by `AppSecProtectionMiddleware` (including normal and blocked responses) lacked standard browser defense headers.
* **Remediation:**
  Added `_apply_security_headers()` to set `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin` on all responses.
* **Regression Test:** `tests/test_audit_validation.py::TestSecurityDefectsAndHardening::test_defense_in_depth_security_headers`
* **Status:** **RESOLVED & VERIFIED**

---

### NEW-DEF-007: Non-Atomic Concurrency Race in Checkout Stock Decrement
* **Severity:** **HIGH** (CWE-362: Race Condition / Concurrent Execution)
* **Affected Component:** `autoheal/shopsphere/services.py:454`
* **Root Cause Analysis:**
  Stock decrements were executed via `UPDATE products SET stock = stock - ? WHERE id = ?`. Under simultaneous checkouts across concurrent threads, stock could drop below zero before the application detected inventory depletion.
* **Remediation:**
  Replaced with atomic conditional update:
  `UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?`
  If `cursor.rowcount == 0`, a `ValueError` is raised, causing the transaction to rollback automatically.
* **Regression Test:** `tests/test_audit_validation.py::TestDatabaseReliabilityAndDisasterRecovery::test_concurrent_checkout_inventory_consistency`
* **Status:** **RESOLVED & VERIFIED**

---

## 3. Conclusion
All 7 newly discovered defects have been isolated, reproduced, remediated with surgical patches, and verified with automated regression tests. No regressions were introduced across the existing 72-test baseline suite.
