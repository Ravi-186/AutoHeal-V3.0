# AutoHeal: Multi-Vector Threat Detection Engine Specification

**Author:** SOC & SIEM Engineering Lead  
**Document Ref:** `DET-ENG-001`  
**Date:** 2026-11-01  

---

## 1. Detection Engine Architecture

The AutoHeal Detection Engine operates two complementary detection pipelines:
1. **Per-Request Perimeter Inspection (Real-Time In-Line):** Evaluates requests at the HTTP gateway before routing to the application layer.
2. **Sliding-Window Correlation Engine (Temporal Correlation):** Ingests normalized telemetry events and evaluates sliding-window statistical rules (e.g. 60-second sliding timeframes) to detect distributed or slow-and-low attack patterns.

---

## 2. Rule Catalog & MITRE ATT&CK Mapping

### Rule 1: `INJ-001` (SQL Injection)
- **Category:** Injection
- **Severity:** `CRITICAL` | **Confidence:** `0.98`
- **MITRE Technique:** `T1190 - Exploit Public-Facing Application: SQL Injection`
- **Detection Logic:** Regex pattern matching for tautologies (`' OR '1'='1`), stacked queries (`; DROP TABLE`), union operators (`UNION SELECT`), comment evasion (`--`, `/*`), and sleep commands (`WAITFOR DELAY`, `pg_sleep`).
- **Defensive Action:** Immediate HTTP 403 Forbidden intercept + Dynamic IP block for 300 seconds.

### Rule 2: `XSS-001` (Cross-Site Scripting)
- **Category:** Cross-Site Scripting (XSS)
- **Severity:** `HIGH` | **Confidence:** `0.95`
- **MITRE Technique:** `T1059.007 - Command and Scripting Interpreter: JavaScript`
- **Detection Logic:** Inspection of URI parameters and request bodies for `<script>`, `javascript:`, DOM event attributes (`onload=`, `onerror=`), and `document.cookie` exfiltration patterns.
- **Defensive Action:** Immediate HTTP 403 Forbidden intercept + Dynamic IP block for 300 seconds.

### Rule 3: `AUTH-001` (Repeated Failed Logins)
- **Category:** Credential Stuffing / Brute Force
- **Severity:** `HIGH` | **Confidence:** `0.95`
- **MITRE Technique:** `T1110.001 - Brute Force: Password Guessing`
- **Detection Logic:** Sliding-window aggregation of `AUTH_FAILURE` events. Triggers when failed login attempts from a single `client_ip` exceed `threshold = 4` within a `window_seconds = 60` window.
- **Defensive Action:** Dynamic IP quarantine for 180 seconds.

### Rule 4: `AUTH-002` (Unauthorized Administrative Access)
- **Category:** Privilege Escalation / Unauthorized Access
- **Severity:** `HIGH` | **Confidence:** `0.95`
- **MITRE Technique:** `T1078 - Valid Accounts`
- **Detection Logic:** Intercepts requests targeting `/api/shop/admin/*` lacking valid bearer tokens or authenticated as customer role.
- **Defensive Action:** Immediate HTTP 403 Forbidden intercept + Dynamic IP quarantine for 300 seconds.

### Rule 5: `RATE-001` (Abnormal Request Rate / Scraping)
- **Category:** Denial of Service / Scraping
- **Severity:** `MEDIUM` | **Confidence:** `0.90`
- **MITRE Technique:** `T1498 - Network Denial of Service`
- **Detection Logic:** Count of requests from a single client IP exceeds `threshold = 20` requests within `window_seconds = 10`.
- **Defensive Action:** HTTP 429 Too Many Requests + Dynamic rate-limit quarantine for 120 seconds.

### Rule 6: `HEALTH-001` (Application Health Degradation)
- **Category:** Reliability / Service Degradation
- **Severity:** `HIGH` | **Confidence:** `0.92`
- **Detection Logic:** Ingestion of consecutive HTTP 500 error events (> 3) on critical services within 30 seconds.
- **Defensive Action:** Triggers autonomous service recovery playbook, database connection pool reset, and baseline validation.
