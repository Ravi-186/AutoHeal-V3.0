# AutoHeal: Incident Response Lifecycle & SOAR Playbooks

**Author:** Incident Response & SOAR Automation Engineer  
**Document Ref:** `IR-SOAR-001`  
**Date:** 2026-11-01  

---

## 1. Enterprise Incident Lifecycle

AutoHeal enforces a deterministic 7-stage incident response state machine:

```
[ NEW ] 
   │
   ▼
[ TRIAGED ] (Severity and Confidence Score Evaluated)
   │
   ▼
[ INVESTIGATING ] (Telemetry Correlation & IoC Extraction)
   │
   ▼
[ CONTAINMENT ] (SOAR Playbook Execution: e.g. BLOCK_IP, RATE_LIMIT)
   │
   ▼
[ REMEDIATION ] (Surgical Code Patching or Service Restoration)
   │
   ▼
[ VERIFICATION ] (Dual Synthetic Probing: Perimeter 403 + Availability 200)
   │
   ├─► Passed: [ RESOLVED ] / [ VERIFIED_CONTAINED ]
   └─► Failed: [ ESCALATION_REQUIRED ] (Max 3 retries, then alert human analyst)
```

---

## 2. Automated SOAR Playbooks

### Playbook 1: `PLAYBOOK-QUARANTINE-IP`
- **Trigger:** Rule `INJ-001`, `XSS-001`, `AUTH-001`, or `AUTH-002`
- **Preconditions:** Source IP is not in system allowlist (`127.0.0.1`, RFC 1918 internal gateway).
- **Execution:**
  1. Insert into `blocked_clients` with TTL (180s - 300s).
  2. Log action to `security_events` with `action_taken = 'QUARANTINED'`.
  3. Emit SSE alert to connected SOC operators.
- **Verification Requirement:** Execute synthetic loopback perimeter probe with `X-Forwarded-For: <target_ip>`. Must return HTTP 403 Forbidden.
- **Rollback:** `POST /api/security/unblock` removes IP from `blocked_clients`.

### Playbook 2: `PLAYBOOK-RATE-LIMIT-SURGE`
- **Trigger:** Rule `RATE-001`
- **Preconditions:** Request volume exceeds 20 requests/10s.
- **Execution:** Temporarily throttle client IP with HTTP 429 response status and 120s cooldown.
- **Verification Requirement:** Confirm subsequent requests receive HTTP 429 while benign traffic receives HTTP 200.

### Playbook 3: `PLAYBOOK-SERVICE-RECOVERY`
- **Trigger:** Rule `HEALTH-001`
- **Execution:** Re-initialize database connection pools, re-seed nominal baseline, and execute health readiness probe.
- **Verification Requirement:** Availability probe against `/api/shop/health` must return `HTTP 200 OK` with `status: HEALTHY`.

---

## 3. Closed-Loop Verification Guarantee (Rule 6 Strict Compliance)

In AutoHeal, a remediation action is NEVER marked successful simply because an API call succeeded or returned HTTP 200.
1. The **Verification Agent (`AppSecVerifier`)** dispatches a synthetic probe simulating the attacker to verify containment (expected HTTP 403).
2. The agent dispatches a second synthetic probe simulating a benign shopper (from `192.0.2.100`) to verify that the storefront remains available (expected HTTP 200).
3. Only when BOTH probes satisfy invariants is the incident status updated to `VERIFIED_CONTAINED`.
