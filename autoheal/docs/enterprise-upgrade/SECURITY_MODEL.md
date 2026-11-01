# AutoHeal & ShopSphere: Security Model & RBAC Architecture

**Author:** Cybersecurity Architect & DevSecOps Lead  
**Document Ref:** `SEC-MODEL-001`  
**Date:** 2026-11-01  

---

## 1. Authentication Architecture

### 1.1 Password Cryptography
- **Algorithm:** PBKDF2 with HMAC-SHA256
- **Work Factor:** 100,000 iterations
- **Salt Generation:** Cryptographically random 16-byte hex string (`secrets.token_hex(16)`)
- **Verification:** Constant-time digest comparison (`secrets.compare_digest`) to prevent timing side-channel attacks.

### 1.2 Session & API Token Management
- **Token Generation:** 24-byte cryptographically secure random hexadecimal token (`secrets.token_hex(24)`).
- **Format:** `token_admin_<hex>` for administrative operators, `token_<hex>` for customer accounts.
- **Zero Static Tokens:** Legacy master token (`token_admin_shopsphere_secret`) has been eradicated from both codebase and database.
- **Storage:** Client-side `localStorage.getItem("shopsphere_auth_token")` passed in `Authorization: Bearer <token>` HTTP header.

---

## 2. Role-Based Access Control (RBAC) Matrix

| Operation / Resource | Public Shopper | Authenticated Customer | Security Analyst | Super Administrator |
|---|:---:|:---:|:---:|:---:|
| Browse Products (`GET /api/shop/products`) | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** |
| Manage Cart / Wishlist (`/api/shop/cart/*`) | Session-bound | Account-bound | Account-bound | Account-bound |
| Checkout & Place Orders (`POST /api/shop/checkout`) | Session-bound | Account-bound | Account-bound | Account-bound |
| View Customer Orders (`GET /api/shop/orders`) | **DENY (401)** | Own Orders Only | Own Orders Only | All Orders |
| Admin Analytics (`GET /api/shop/admin/stats`) | **DENY (401)** | **DENY (403)** | **DENY (403)** | **ALLOW (200)** |
| View SOC Telemetry (`GET /api/security/events`) | **DENY (401)** | **DENY (403)** | **ALLOW (200)** | **ALLOW (200)** |
| Trigger Defensive Quarantines (`POST /api/security/remediate`) | **DENY (401)** | **DENY (403)** | **ALLOW (200)** | **ALLOW (200)** |
| Unblock Quarantined IP (`POST /api/security/unblock`) | **DENY (401)** | **DENY (403)** | **ALLOW (200)** | **ALLOW (200)** |
| Apply Surgical Patch (`POST /api/security/vulnerabilities/{id}/apply`) | **DENY (401)** | **DENY (403)** | **DENY (403)** | **ALLOW (200)** |

---

## 3. Defense-in-Depth Layers

1. **Perimeter Filter (WAF Layer):** Intercepts SQL injection, cross-site scripting, and unauthorized path traversals before request dispatch.
2. **Dynamic Blocklist Layer:** Quarantined IPs are rejected at the edge with HTTP 403 Forbidden with sub-millisecond database lookup (`idx_blocked_clients_ip_active`).
3. **Application Layer Validation:** Strict Pydantic models validate all incoming payloads; SQL parameterized queries prevent injection.
4. **Data Layer Protection:** Write-Ahead Logging, Foreign Key enforcement, and atomic transaction contexts (`with conn:`).
5. **Auditing & Logging:** All security events and administrative actions append to immutable audit tables.
