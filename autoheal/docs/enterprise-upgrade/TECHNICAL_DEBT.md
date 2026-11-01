# AutoHeal & ShopSphere: Technical Debt & Architectural Debt Audit

**Author:** Principal Software Architect & Site Reliability Engineering Group  
**Date:** 2026-11-01  
**Project:** AutoHeal Autonomous SOC Platform  
**Document Ref:** `TECH-DEBT-001`  

---

## 1. Executive Summary

This document registers accumulated technical debt across code quality, type safety, component coupling, error handling, and runtime telemetry. Resolving this debt is essential to elevate AutoHeal from a functional prototype to an enterprise-grade production-ready Autonomous SOC platform.

---

## 2. Technical Debt Register

### 2.1 Type Safety & Static Analysis Suppression
- **Location:** `autoheal/dashboard/app.py:1-6`
- **Issue:** The Streamlit dashboard begins with six blanket type-checking suppressions:
  ```python
  # pyright: reportMissingImports=false
  # pyright: reportOptionalCall=false
  # pyright: reportOptionalMemberAccess=false
  # pyright: reportAttributeAccessIssue=false
  # pyright: reportGeneralTypeIssues=false
  # type: ignore
  ```
- **Consequence:** These suppressions masked the `PostureScorer` import mismatch (BUG-002), allowing broken references to pass static type checking silently.
- **Remediation:** Remove blanket `# type: ignore`, properly type all session state variables, and fix underlying type signatures so `pyright` passes cleanly.

---

### 2.2 Fabricated Telemetry & Metric Hardcoding
- **Locations:**
  - `server.py:155`: `"total_devices": "{:,}".format(len(devices) * 1152 + 14)`
  - `server.py:426`: `"remediation_time_ms": 842`
  - `server.py:428-433`: Hardcoded fallback audit trail strings
  - `src/appsec/api.py:49`: `"average_remediation_ms": 38.5`
  - `src/appsec/responder.py:135`: `round((time.time() - execution_start) * 1000 + 12, 2)`
- **Consequence:** Violates Rule 6 ("Never hardcode security metrics, incident counts, detection results, or remediation outcomes"). Destroys audit credibility in a production SOC.
- **Remediation:** Replace all fabricated formulas with dynamic queries against SQLite persisted data and true monotonic clock measurements (`time.perf_counter()`).

---

### 2.3 Monolithic Route Handlers & Redundant Code
- **Location:** `autoheal/server.py` (448 lines) and `autoheal/dashboard/app.py` (1,375 lines)
- **Issue:** `server.py` mixes legacy simulation endpoints (`/api/attack/A`), modern AppSec routes (`/api/security/*`), and Flipkart storefront endpoints (`/flipkart`) in a single file with global in-memory state objects (`workflow_history: List[Dict]`).
- **Consequence:** Global mutable in-memory lists (`workflow_history`) lose state when workers restart and cannot scale across multiple Uvicorn worker processes.
- **Remediation:** Transition state to the SQLite database. Modularize routes into cleanly separated APIRouters.

---

### 2.4 Broad Exception Handling & Silent Fallbacks
- **Location:** `autoheal/src/appsec/verifier.py:101`, `autoheal/dashboard/app.py:84`, `autoheal/src/appsec/security_tester.py:60`
- **Issue:** Use of `except Exception: pass` swallows root errors (such as network connection refused, missing table, or missing module).
- **Consequence:** Violates Rule 9 ("Never silently swallow exceptions"). Makes debugging intermittent failures in production environments extraordinarily difficult.
- **Remediation:** Catch explicit exception types (`sqlite3.OperationalError`, `httpx.ConnectError`), log with structured stack traces at `WARNING` or `ERROR` level, and provide auditable fallback metadata.

---

### 2.5 Inconsistent API Versioning & URL Prefixing
- **Issue:** AutoHeal APIs use inconsistent prefixes:
  - System APIs: `/api/state`, `/api/health`, `/api/detect`
  - ShopSphere APIs: `/api/shop/products`, `/api/shop/cart`
  - AppSec Defense APIs: `/api/security/incidents`, `/api/security/metrics`
  - Flipkart Microservice APIs: `/api/flipkart/status`
- **Remediation:** Standardize under structured, versioned routes (`/api/v1/soc/*`, `/api/v1/shop/*`, `/api/v1/appsec/*`) while maintaining backward-compatible aliases for legacy routes.

---

### 2.6 Database Transaction Isolation
- **Issue:** Some multi-step operations (e.g., checkout + order creation + inventory decrement) execute multiple independent SQL statements across separate cursor operations without an explicit wrapping `BEGIN TRANSACTION ... COMMIT`.
- **Consequence:** If a crash occurs midway, order items may be created without inventory decrement, violating transactional atomicity.
- **Remediation:** Wrap multi-step mutations in explicit context-managed transactions (`with conn:`).
