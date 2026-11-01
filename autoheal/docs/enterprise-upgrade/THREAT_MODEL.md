# AutoHeal & ShopSphere: STRIDE Threat Model

**Author:** Cybersecurity Architecture & Threat Intelligence Group  
**Document Ref:** `THREAT-MODEL-001`  
**Date:** 2026-11-01  

---

## 1. STRIDE Threat Analysis Matrix

| Threat Category | Target Asset / Flow | Potential Threat & Vector | Mitigation Mechanism | Verification Test |
|---|---|---|---|---|
| **Spoofing** | Customer Authentication & Admin APIs | Credential stuffing, brute-force password guessing | Rate limiting (Rule AUTH-001) + Dynamic IP quarantine for 180s | `test_01_repeated_failed_logins_triggers_quarantine` |
| **Tampering** | Product Catalog & Inventory | SQL injection in product search query (`q=...`) | AutoHeal Sentinel SQLi filter (Rule INJ-001) + parameterized queries | `test_02_sql_injection_attempt_intercepted` |
| **Repudiation** | Checkout & Administrative Actions | Denying fraudulent transactions or admin mutations | Immutable `admin_audit_logs` & `security_events` with correlation IDs | `test_05_admin_audit_trail_recorded` |
| **Information Disclosure** | Customer Profiles & Database Credentials | Exfiltration via SQLi, error stacks, or XSS | Output sanitization, Pydantic DTOs, credential hashing with salt | `test_03_xss_payload_intercepted` |
| **Denial of Service** | Storefront & Checkout Availability | Scraping botnet, HTTP flood, inventory lockup | Adaptive rate limiting (Rule RATE-001) + atomic inventory locks | `test_06_abnormal_request_rate_triggers_defense` |
| **Elevation of Privilege** | Administrative Endpoints (`/admin/*`) | Unauthenticated access or customer privilege escalation | Strict token validation, role comparison, removal of master backdoor | `TestShopSphereAdminRBAC` (13 tests) |

---

## 2. MITRE ATT&CK Mapping of Handled Vectors

- **T1110.001 - Brute Force: Password Guessing:** Mitigated by AUTH-001 sliding-window detection.
- **T1190 - Exploit Public-Facing Application (SQLi):** Mitigated by INJ-001 perimeter inspection.
- **T1059.007 - Command and Scripting Interpreter: JavaScript (XSS):** Mitigated by XSS-001 tag neutralizing filter.
- **T1078 - Valid Accounts / Privilege Escalation:** Mitigated by AUTH-002 token verification.
- **T1498 - Network Denial of Service / Scraping:** Mitigated by RATE-001 surge detection.
- **T1486 - Data Encrypted for Impact (Ransomware):** Mitigated by HEALTH-001 automated replica restoration.
