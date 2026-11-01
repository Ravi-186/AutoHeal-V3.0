# AutoHeal & ShopSphere: Comprehensive Security Audit & Threat Model

**Author:** Cybersecurity & DevSecOps Architecture Organization  
**Date:** 2026-11-01  
**Project:** AutoHeal Autonomous SOC Platform  
**Document Ref:** `SEC-AUDIT-001`  

---

## 1. Executive Summary

A comprehensive enterprise security audit was performed across ShopSphere (the e-commerce target) and AutoHeal (the autonomous SOC platform). While the architecture demonstrates exemplary defensive implementations—including real-time WAF telemetry interception, SQLi/XSS pattern matching, sliding-window brute-force detection, closed-loop verification, and strict target safety allowlisting—several critical and high-severity security weaknesses were identified in the existing codebase.

This document classifies every discovered finding with CVSS v3.1 scoring, root-cause analysis, and specific engineering remediation requirements.

---

## 2. Threat Model (STRIDE Methodology)

| Threat Category | Target Component | Threat Description | Existing Mitigation | Risk Level |
|---|---|---|---|---|
| **Spoofing** | ShopSphere Auth (`/api/shop/auth/*`) | Attacker sends forged credentials or spoofed `X-Forwarded-For` headers. | IP quarantine via `AUTH-001` rule; PBKDF2-HMAC password hashing. | **Medium** |
| **Tampering** | Cart & Checkout (`/api/shop/checkout`) | Attacker manipulates cart pricing or delivery fees. | Server-side financial invariant re-computation in `CartService`. | **Low** |
| **Repudiation** | Admin Actions (`/api/shop/admin/*`) | Administrator updates stock or order state without audit trace. | `admin_audit_logs` records email, timestamp, and entity diffs. | **Low** |
| **Information Disclosure** | Incident Export & Security Logs | Unauthenticated users access raw incident evidence containing IP addresses or queries. | Passwords redacted via `redact_sensitive_data`; needs RBAC on export endpoints. | **High** |
| **Denial of Service** | Storefront Catalog Probing | Scraping bots or volumetric HTTP floods degrade catalog availability. | Dynamic IP rate-limiting via `RATE-001` rule and `blocked_clients` table. | **Medium** |
| **Elevation of Privilege** | ShopSphere Admin API | Attacker passes hardcoded backdoor token `token_admin_shopsphere_secret` to obtain instant superuser admin rights. | None (Backdoor hardcoded in `shopsphere/api.py:89`). | **CRITICAL** |

---

## 3. Vulnerability Findings & Risk Register

### [SEC-01] CRITICAL: Hardcoded Master Admin Backdoor Token in ShopSphere API
- **CVSS v3.1 Score:** `9.8 (CRITICAL) - CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`
- **Location:** `autoheal/shopsphere/api.py:89-91` and `autoheal/shopsphere/database.py:307`
- **Vulnerability Description:** The helper dependency `require_admin_user` explicitly bypasses authentication and grants administrative privileges if the substring `"token_admin_shopsphere_secret"` is present in the `Authorization` header:
  ```python
  if authorization and "token_admin_shopsphere_secret" in authorization:
      return {"name": "Admin", "email": "admin@shopsphere.com", "role": "admin"}
  ```
- **Impact:** Any unauthenticated remote attacker can bypass access control to modify stock, view metrics, and alter order fulfillment without valid credentials.
- **Required Remediation:** Remove the hardcoded token check entirely. Enforce cryptographic validation of Bearer tokens against the database `users` table with expiration verification.

---

### [SEC-02] HIGH: Unauthenticated Access to SOC Management and Playbook Execution APIs
- **CVSS v3.1 Score:** `8.2 (HIGH) - CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:H/A:L`
- **Location:** `autoheal/src/appsec/api.py` and `autoheal/server.py`
- **Vulnerability Description:** Sensitive SOC endpoints such as `/api/security/unblock`, `/api/security/vulnerabilities/{id}/apply`, `/api/security/vulnerabilities/{id}/rollback`, and `/api/device/{id}/block` do not enforce role-based access control (RBAC). Any client on the network can trigger containment or unblock malicious IPs.
- **Impact:** An unauthorized party could unblock quarantined adversary nodes or trigger disruption by isolating legitimate services.
- **Required Remediation:** Implement FastAPI security dependencies (`Security(require_role("soc_admin"))` / `require_role("analyst")`) enforcing role-based permissions across all sensitive response and mutation endpoints.

---

### [SEC-03] HIGH: Missing Session Expiration and Token Revocation Mechanisms
- **CVSS v3.1 Score:** `7.5 (HIGH) - CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`
- **Location:** `autoheal/shopsphere/database.py` and `autoheal/shopsphere/services.py:UserService`
- **Vulnerability Description:** User tokens generated upon registration or login are static hex strings stored indefinitely in `users.token` without an `expires_at` column. Tokens remain valid perpetually and cannot be revoked without direct database modification.
- **Impact:** Compromised session tokens cannot be invalidated, allowing persistent session hijacking.
- **Required Remediation:** Introduce token TTLs, an explicit `sessions` table, and a `/auth/logout` endpoint that revokes the active token.

---

### [SEC-04] MEDIUM: Client IP Spoofing via Unverified `X-Forwarded-For` Header
- **CVSS v3.1 Score:** `5.3 (MEDIUM) - CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N`
- **Location:** `autoheal/src/appsec/middleware.py` and `autoheal/src/appsec/security_tester.py`
- **Vulnerability Description:** The application accepts any arbitrary IP passed in the `X-Forwarded-For` header without verifying if the request originated from a trusted reverse proxy.
- **Impact:** A malicious actor could spoof their IP address to evade rate limits or frame innocent IP addresses for malicious activity.
- **Required Remediation:** Only trust `X-Forwarded-For` headers when incoming requests originate from designated trusted proxies; otherwise, prioritize `request.client.host`.

---

### [SEC-05] LOW: Permissive CORS Configuration (`allow_origins=["*"]`)
- **CVSS v3.1 Score:** `3.7 (LOW) - CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N`
- **Location:** `autoheal/server.py:48-54`
- **Vulnerability Description:** FastAPI's `CORSMiddleware` is configured with `allow_origins=["*"]` while `allow_credentials=True`. Modern browsers disallow credentials with wildcard origins, but this configuration allows arbitrary domains to send cross-origin requests.
- **Required Remediation:** Restrict allowed CORS origins to explicit localhost ports (`http://localhost:8000`, `http://localhost:8501`, `http://127.0.0.1:8000`) and configurable enterprise domains via environment variables.

---

## 4. Assessment of Positive Security Controls

1. **Strict Target Safety Allowlisting (`validate_target_safety` in `security_tester.py`):**
   - The security test runner strictly enforces that only `localhost`, `127.0.0.1`, `0.0.0.0`, `::1`, and `testserver` can be targeted.
   - Any attempt to target an external domain or public IP throws an immediate `ValueError`, completely preventing uncontrolled external scanning.
2. **Deterministic Password Storage:**
   - PBKDF2-HMAC-SHA256 with 100,000 iterations and unique 16-byte cryptographically secure random salts. Plaintext passwords are never persisted.
3. **Sensitive Data Redaction:**
   - Password fields, tokens, and authorization headers are sanitized with `[REDACTED]` before writing to `security_events` and incident dossiers.
