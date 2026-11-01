# Authorized Adversarial Scenario Catalog (Phase 4)
## AutoHeal Sentinel v3.0 — Comprehensive Defensive Simulation Library

### 1. Catalog Overview & Selection Criteria

The AutoHeal Scenario Catalog provides a curated collection of **seven authorized, non-destructive defensive security tests**. Each scenario is designed to calibrate signature heuristics, test sliding-window correlation algorithms, and verify autonomous SOAR quarantine capabilities without risking database corruption or persistent denial of service.

Every scenario displayed in the user interface is backed by a concrete Python execution method in `ShopSphereSecurityTester`, a corresponding detection signature in `AppSecDetector`, and an automated verification routine.

---

### 2. Comprehensive Scenario Matrix

| Scenario ID | Name & Standard | MITRE ATT&CK | Risk Category | Severity | Target Endpoint | Expected Rule | Expected SOAR Action | Avg Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `sqli` | SQL Injection Attack Vector | T1190 (Exploit Public-Facing App) | Injection | **CRITICAL** | `GET /api/shop/products?q=` | `INJ-001` | BLOCK_IP (Quarantine) | ~0.8s |
| `xss` | Cross-Site Scripting Neutralization | T1059.007 (JavaScript Execution) | Injection | **HIGH** | `GET /api/shop/products?q=` | `XSS-001` | SANITIZE / BLOCK | ~0.6s |
| `failed_logins` | Credential Stuffing & Brute-Force | T1110.001 (Password Guessing) | Credential Access | **HIGH** | `POST /api/shop/auth/login` | `AUTH-001` | BLOCK_IP (300s TTL) | ~1.4s |
| `admin` | Unauthorized Admin Access | T1078 (Valid Accounts / RBAC) | Privilege Escalation | **HIGH** | `GET /api/shop/admin/stats` | `AUTH-002` | DROP_SESSION / 401 | ~0.5s |
| `rate` | API Endpoint Flooding / Burst | T1499.002 (Endpoint Exhaustion) | Denial of Service | **MEDIUM** | `GET /api/shop/products` | `RATE-001` | RATE_LIMIT / 429 | ~1.1s |
| `health` | Health & Error Cascade Resilience | T1499 (Service Degradation) | Availability & Reliability | **LOW** | `POST /api/shop/health/simulate-error` | `HEALTH-001` | CIRCUIT_BREAK / LOG | ~0.7s |
| `replay` | Multi-Vector Attack Replay | Multiple (Chained ATT&CK) | Complex Attack Chain | **CRITICAL** | `* /api/shop/*` | `CORR-001` | DYNAMIC_CONTAINMENT | ~1.8s |

---

### 3. Detailed Scenario Specifications

#### 3.1 Scenario 1: SQL Injection Attack Vector (`sqli`)
- **Objective**: Evaluates input parameter sanitization and tautological SQL injection pattern matching.
- **Payload Pattern**: `Laptop' OR '1'='1`
- **Method & Path**: `GET /api/shop/products?q=Laptop'%20OR%20'1'='1`
- **Detection Mechanism (`INJ-001`)**: Regular expression scanner intercepts SQL comment characters (`--`), tautology constructs (`OR '1'='1'`), and union selectors.
- **Expected Incident Behavior**: Generates high-confidence critical incident, tags MITRE T1190, records matched payload in forensic evidence.
- **Expected Remediation**: Dynamic IP quarantine applied; subsequent attacker requests to storefront return HTTP 403 Forbidden.

#### 3.2 Scenario 2: Cross-Site Scripting Neutralization (`xss`)
- **Objective**: Validates WAF reflection inspection and script context neutralization.
- **Payload Pattern**: `<script>alert('ShopSphere-XSS-Test')</script>`
- **Method & Path**: `GET /api/shop/products?q=%3Cscript%3Ealert(...)`
- **Detection Mechanism (`XSS-001`)**: HTML parser and heuristic regex scan for opening/closing script tags, inline event handlers (`onload=`, `onerror=`), and DOM javascript pseudoprotocols.
- **Expected Incident Behavior**: High-severity incident logged with reflected parameter context preserved for analyst triage.
- **Expected Remediation**: Request blocked with HTTP 403 or parameter stripped, client quarantined.

#### 3.3 Scenario 3: Credential Stuffing & Brute-Force Abuse (`failed_logins`)
- **Objective**: Calibrates sliding-window authentication failure correlation and brute-force mitigation.
- **Payload Pattern**: Repeated POST attempts with unique email strings and randomized passwords.
- **Method & Path**: `POST /api/shop/auth/login` (5 to 10 iterations within a 10-second window).
- **Detection Mechanism (`AUTH-001`)**: Threshold rule triggers when 5 or more authentication failures are recorded from the same IP address within a 60-second sliding window.
- **Expected Incident Behavior**: Incident created with severity HIGH, categorizing brute-force behavior and listing attempt count.
- **Expected Remediation**: Immediate insertion of client IP into `quarantined_clients` table with a 300-second TTL.

#### 3.4 Scenario 4: Unauthorized Administrative Access (`admin`)
- **Objective**: Probes administrative endpoints without session cookies or Bearer tokens to verify RBAC perimeter enforcement.
- **Payload Pattern**: Unauthenticated GET request to protected administrative telemetry routes.
- **Method & Path**: `GET /api/shop/admin/stats`
- **Detection Mechanism (`AUTH-002`)**: Detects unauthenticated or privilege-exceeding requests accessing administrative boundaries (`/api/shop/admin/*`).
- **Expected Incident Behavior**: Logs privilege abuse telemetry and audits attempted breach in `admin_audit_logs`.
- **Expected Remediation**: Rejection with HTTP 401 Unauthorized / 403 Forbidden.

#### 3.5 Scenario 5: API Endpoint Flooding & DoS Burst (`rate`)
- **Objective**: Verifies token-bucket rate limiting and high-concurrency request surge handling.
- **Payload Pattern**: High-velocity burst of 25 to 30 requests sent with minimal inter-request delay.
- **Method & Path**: `GET /api/shop/products`
- **Detection Mechanism (`RATE-001`)**: Triggers when requests from a single client exceed 120 requests/minute.
- **Expected Incident Behavior**: Incident logged with severity MEDIUM, documenting surge velocity.
- **Expected Remediation**: HTTP 429 Too Many Requests returned with `Retry-After: 60` response header.

#### 3.6 Scenario 6: Application Health & Error Cascade Resilience (`health`)
- **Objective**: Simulates downstream service errors to validate error containment, distributed tracing, and storefront availability.
- **Payload Pattern**: Synthetic 500 error generator probe.
- **Method & Path**: `POST /api/shop/health/simulate-error`
- **Detection Mechanism (`HEALTH-001`)**: Health observability monitor captures synthetic 500 status code, correlates with trace ID, and ensures error does not cascade.
- **Expected Incident Behavior**: Telemetry logged as LOW severity observability event.
- **Expected Remediation**: Storefront health probe confirms core catalog remains operational (HTTP 200 UP).

#### 3.7 Scenario 7: Multi-Vector Attack Replay & Baseline Comparison (`replay`)
- **Objective**: Executes a composite sequential attack chain to benchmark regression detection and measure Before vs After exposure delta.
- **Payload Pattern**: Multi-stage probe: baseline probe -> burst credential stuffing -> verification probe.
- **Method & Path**: Composite multi-endpoint execution.
- **Detection Mechanism (`CORR-001`)**: Multi-vector event correlation linking multiple distinct telemetry anomalies under unified correlation ID.
- **Expected Incident Behavior**: High-fidelity incident generated linking baseline probe to quarantined state.
- **Expected Remediation**: Validated containment with dual-probe confirmation.
