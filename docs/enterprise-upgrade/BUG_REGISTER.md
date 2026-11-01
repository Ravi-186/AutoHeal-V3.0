# AutoHeal & ShopSphere: Enterprise Bug Register

**Author:** QA Automation & Software Reliability Engineering Group  
**Date:** 2026-11-01  
**Project:** AutoHeal Autonomous SOC Platform  
**Document Ref:** `BUG-REG-001`  

---

## 1. Summary of Discovered Software Defects

| Bug ID | Severity | Component | Summary | Status |
|---|---|---|---|---|
| **BUG-001** | **CRITICAL** | Dependencies | Missing `fastapi` and `plotly` dependencies preventing application startup and unit tests | **RESOLVED** |
| **BUG-002** | **HIGH** | Dashboard / AppSec | Streamlit dashboard imports `PostureScorer` instead of `SecurityPostureScorer`, breaking posture score calculation | **OPEN** |
| **BUG-003** | **HIGH** | AppSec API | Duplicate route definition for `@router.get("/incidents/{incident_id}/export")` in `src/appsec/api.py` | **OPEN** |
| **BUG-004** | **HIGH** | AppSec API | `replay_attack_comparison` endpoint has empty implementation body and returns `None` | **OPEN** |
| **BUG-005** | **CRITICAL** | ShopSphere Auth | Hardcoded backdoor admin token `token_admin_shopsphere_secret` bypasses authentication | **OPEN** |
| **BUG-006** | **MEDIUM** | AutoHeal Sentinel | Hardcoded calculation formula for `total_devices` (`len(devices) * 1152 + 14`) in `server.py:155` | **OPEN** |
| **BUG-007** | **MEDIUM** | AutoHeal Sentinel | Hardcoded remediation latency (`"remediation_time_ms": 842`) and synthetic `+ 12` ms addition | **OPEN** |
| **BUG-008** | **MEDIUM** | AppSec Metrics | Hardcoded `"average_remediation_ms": 38.5` in `/api/security/metrics` | **OPEN** |
| **BUG-009** | **MEDIUM** | AppSec Verifier | Synthetic loopback probe fails silently when external HTTP server is offline instead of using in-memory ASGI client | **OPEN** |
| **BUG-010** | **LOW** | Database / Schema | Missing temporal and IP composite indexes on `security_events` causing table scan lag | **OPEN** |

---

## 2. Defect Breakdown & Root Cause Analysis

### BUG-001: Missing `fastapi` and `plotly` in Active Virtual Environment
- **Severity:** CRITICAL
- **Location:** `AD/.venv` and `autoheal/requirements.txt`
- **Root Cause:** Dependencies declared in `requirements.txt` were not installed into the active `.venv`. When running `python -m unittest discover tests`, 3 test modules failed immediately with `ModuleNotFoundError: No module named 'fastapi'`.
- **Resolution:** Executed `.venv/Scripts/pip.exe install fastapi plotly pytest coverage`.
- **Verification:** All 68 tests across all test suites ran and passed in 99.0s.
- **Status:** **RESOLVED** (Regression test verified).

---

### BUG-002: Streamlit Dashboard Class Name Mismatch (`PostureScorer`)
- **Severity:** HIGH
- **Location:** `autoheal/dashboard/app.py:73, 81` and `autoheal/src/appsec/posture_scorer.py:12`
- **Root Cause:** `dashboard/app.py` attempts to import `PostureScorer`:
  ```python
  from src.appsec.posture_scorer import PostureScorer
  ```
  However, the class defined in `src/appsec/posture_scorer.py` is named `SecurityPostureScorer`. The import fails, gets caught in an empty `except Exception: pass`, leaving `PostureScorer = None`. As a result, the live posture calculation (`if PostureScorer:`) never executes and falls back to a simplified formula.
- **Remediation:** Update `dashboard/app.py` to import `SecurityPostureScorer as PostureScorer` or alias `PostureScorer = SecurityPostureScorer` in `src/appsec/posture_scorer.py`.
- **Status:** **OPEN**

---

### BUG-003: Duplicate Route Definition for `/incidents/{incident_id}/export`
- **Severity:** HIGH
- **Location:** `autoheal/src/appsec/api.py:90` and `autoheal/src/appsec/api.py:383`
- **Root Cause:** The endpoint `@router.get("/incidents/{incident_id}/export")` is defined twice in the same router. The first definition supports `json`, `md`, `markdown`, and `pdf` formats with download headers. The second definition duplicates the logic with slight variation in headers.
- **Remediation:** Remove the redundant duplicate definition at line 383 and consolidate parameters into a single canonical export endpoint.
- **Status:** **OPEN**

---

### BUG-004: Incomplete Implementation Body in `replay_attack_comparison`
- **Severity:** HIGH
- **Location:** `autoheal/src/appsec/api.py:368-382`
- **Root Cause:** The endpoint defines:
  ```python
  @router.post("/test/replay", summary="Execute Attack Replay with Before & After Comparison")
  def replay_attack_comparison(req: ReplayRequest):
      """Replays an authorized test scenario against local ShopSphere and returns Before vs After comparison."""
      from src.appsec.security_tester import ShopSphereSecurityTester
      try:
          tester = ShopSphereSecurityTester(base_url=req.target_url)
      except ValueError as e:
          raise HTTPException(status_code=400, detail=str(e))
  ```
  The function body terminates at line 382 without invoking the test or returning any response, resulting in a silent `HTTP 200` returning `null`.
- **Remediation:** Complete the implementation: invoke the test scenario, execute the replay probe, compare baseline vs post-mitigation state, and return the structured comparison object.
- **Status:** **OPEN**

---

### BUG-005: Hardcoded Master Admin Backdoor Token in ShopSphere API
- **Severity:** CRITICAL
- **Location:** `autoheal/shopsphere/api.py:89` and `autoheal/shopsphere/database.py:307`
- **Root Cause:** Bypasses authentication if `token_admin_shopsphere_secret` is present in headers.
- **Remediation:** Remove the backdoor bypass and require legitimate database-backed administrative authentication.
- **Status:** **OPEN**

---

### BUG-006: Hardcoded Monitored Device Formula
- **Severity:** MEDIUM
- **Location:** `autoheal/server.py:155`
- **Root Cause:** `total_devices` is computed as `"{:,}".format(len(devices) * 1152 + 14)`. This creates fabricated enterprise metrics violating Rule 6 ("Never hardcode security metrics, incident counts...").
- **Remediation:** Replace with actual device count from the network inventory.
- **Status:** **OPEN**

---

### BUG-007: Fabricated Remediation Latencies (`842ms` and `+12ms`)
- **Severity:** MEDIUM
- **Location:** `autoheal/server.py:426` and `autoheal/src/appsec/responder.py:135`
- **Root Cause:** `server.py` hardcodes `"remediation_time_ms": 842` and `responder.py` artificially adds `+ 12` ms to measured time.
- **Remediation:** Accurately measure and record true high-resolution elapsed time (`(t_end - t_start) * 1000`) without artificial offsets.
- **Status:** **OPEN**

---

### BUG-008: Hardcoded Average Remediation Metric
- **Severity:** MEDIUM
- **Location:** `autoheal/src/appsec/api.py:49`
- **Root Cause:** `get_security_metrics` returns `"average_remediation_ms": 38.5` as a hardcoded float.
- **Remediation:** Compute true mean remediation duration from historical rows in `security_incidents` table.
- **Status:** **OPEN**

---

### BUG-009: Verification Agent Socket Dependency in Standalone Runs
- **Severity:** MEDIUM
- **Location:** `autoheal/src/appsec/verifier.py:81`
- **Root Cause:** `verify_incident_containment` attempts an external HTTP socket connection to `http://localhost:8000`. If running in a background worker or CLI script where the HTTP server is not actively bound, it throws connection errors and falls back to database-only checks.
- **Remediation:** Accept an optional in-process ASGI application instance / `TestClient` so verification probes can execute in-memory when no external socket is bound.
- **Status:** **OPEN**

---

### BUG-010: Missing Composite Indexes on High-Traffic Telemetry Tables
- **Severity:** LOW
- **Location:** `autoheal/shopsphere/database.py`
- **Root Cause:** Lack of indexes on `security_events(client_ip, timestamp)` and `blocked_clients(client_ip, is_active)` causes linear table scans as event count grows.
- **Remediation:** Add declarative `CREATE INDEX IF NOT EXISTS` statements during schema initialization.
- **Status:** **OPEN**
