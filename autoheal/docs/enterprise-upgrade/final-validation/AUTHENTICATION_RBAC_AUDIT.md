# AutoHeal & ShopSphere v2.5.0: Authentication and RBAC Security Audit

**Auditor:** Principal Security Architect & IAM Specialist  
**Target:** Authentication Subsystem, Session Lifecycle, and RBAC Enforcement  
**Baseline Commit:** `bf47d7a` | **Audit Branch:** `enterprise-validation`  
**Classification:** **ENTERPRISE SECURITY EVALUATION**

---

## 1. Scope of Review

This audit provides an independent evaluation of the authentication and role-based access control (RBAC) mechanisms across:
- `shopsphere/api.py` (Authentication endpoints and route dependencies)
- `shopsphere/database.py` (Database schema, hashing, salt generation, and migrations)
- `shopsphere/services.py` (UserService, AdminService, and token management)
- `src/appsec/detector.py` (AUTH-001 credential stuffing and AUTH-002 admin probe detection)
- `web/templates/shopsphere.html` (Client-side token storage and session state handling)

---

## 2. Key Audit Findings & Remediations

### 2.1 Complete Elimination of Administrative Backdoor
* **Prior Issue:** Previous versions included a static backdoor token (`token_admin_shopsphere_secret`) allowing hardcoded administrative access.
* **Independent Verification:** Tested in `tests/test_shopsphere.py` and `tests/test_audit_validation.py`. Sending `Authorization: Bearer token_admin_shopsphere_secret` results in `HTTP 401 Unauthorized`. All admin tokens must exist as valid rows in the `users` table with `role = 'admin'`.
* **Finding:** The legacy backdoor is completely eliminated.

### 2.2 Token Generation Entropy
* **Implementation:** `new_token = f"{prefix}{secrets.token_hex(24)}"`
* **Cryptographic Strength:** `secrets.token_hex(24)` utilizes Python's CSPRNG (`os.urandom`), producing 48 hexadecimal characters (192 bits of entropy).
* **Finding:** Resistant to brute-force prediction and collision attacks.

### 2.3 Timing-Attack Resistance (NEW-DEF-003)
* **Remediation:** In `shopsphere/services.py`:
  - Password hash verification uses `secrets.compare_digest(computed_hash, stored_hash)`.
  - Token lookups in `UserService.get_by_token(token)` enforce `secrets.compare_digest(row["token"], token)`.
* **Finding:** Comparisons execute in constant time, preventing side-channel timing analysis.

### 2.4 Server-Side Token Expiration (NEW-DEF-002)
* **Prior Issue:** Session tokens previously possessed indefinite validity, persisting until overwritten by a subsequent login.
* **Remediation:** Added `token_expires_at TIMESTAMP` column in `users` table and schema migration in `init_db()`.
* **Policy:** Tokens are issued with a 7-day TTL (`datetime.now(timezone.utc) + timedelta(days=7)`).
* **Verification:** `UserService.get_by_token()` checks `token_expires_at < now_str`. Expired tokens return `None` and receive HTTP 401.

### 2.5 Server-Side Token Revocation & Logout (NEW-DEF-004)
* **Implementation:** Added `UserService.logout(token)` and route `POST /api/shop/auth/logout`.
* **Database Action:**
  ```sql
  UPDATE users SET token = NULL, token_expires_at = NULL WHERE token = ?
  ```
* **Verification:** Tested in `tests/test_audit_validation.py`. Upon logout, the active token is immediately revoked from database storage; subsequent requests using the token are rejected with HTTP 401.

### 2.6 Server-Side Role Enforcement (RBAC)
* **Implementation:** FastAPI dependency `require_admin_user`:
  ```python
  def require_admin_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
      user = get_current_user(authorization)
      if not user:
          raise HTTPException(status_code=401, detail="Authentication required.")
      if user.get("role") != "admin":
          raise HTTPException(status_code=403, detail="Forbidden. Administrative privileges required.")
      return user
  ```
* **Customer Isolation:** Customers attempting to access `/api/admin/orders` or `/api/admin/audit-logs` receive `HTTP 403 Forbidden`. Unauthenticated requests receive `HTTP 401 Unauthorized`.

---

## 3. Cryptographic Evaluation: Password Hashing

### Current Implementation
```python
def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations=100000
    ).hex()
    return pw_hash, salt
```

### Guidance Alignment
* **Current Posture:** 100,000 iterations of PBKDF2-HMAC-SHA256 with 16 bytes (128 bits) of unique random salt per user.
* **OWASP / NIST SP 800-63B Recommendation:**
  - NIST SP 800-63B and OWASP Password Storage Cheat Sheet recommend a minimum of **600,000 iterations** for PBKDF2-HMAC-SHA256, or migrating to modern memory-hard functions such as **Argon2id** (`m=65536, t=3, p=4`).
* **Production Recommendation:** For high-throughput cloud environments, upgrade iterations to 600,000 or implement transparent upgrade to Argon2id upon subsequent successful logins.

---

## 4. Browser Token Storage: localStorage vs HttpOnly Cookies

### Current Frontend Implementation
In `web/templates/shopsphere.html`:
```javascript
localStorage.setItem('shopsphere_auth_token', data.user.token);
localStorage.setItem('shopsphere_user', JSON.stringify(data.user));
```

### Risk Analysis
* **Threat Model:** If an attacker succeeds in executing Cross-Site Scripting (XSS), JavaScript running in the browser origin can access `localStorage.getItem('shopsphere_auth_token')` and exfiltrate the session token.
* **Mitigating Factors in Place:**
  1. Server-side XSS detection (Rule XSS-001) in `AppSecDetector` blocks executable tags and event handlers with HTTP 403.
  2. Jinja2 template auto-escaping.
  3. Defensive security headers: `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`.
  4. Server-side token expiration (7-day TTL) limits exfiltration window.
* **Production Hardening Recommendation:**
  Migrate from localStorage to `HttpOnly`, `Secure`, `SameSite=Strict` cookies issued by `/api/shop/auth/login`. HttpOnly cookies cannot be accessed or read by client-side JavaScript, rendering session tokens immune to XSS exfiltration.

---

## 5. Verification Test Matrix

| Test Identifier | Description | Expected Result | Actual Result |
| :--- | :--- | :--- | :--- |
| `test_password_hashing_and_verification` | PBKDF2 hashing & salt verification | Match on correct PW, reject on invalid | **PASSED** |
| `test_user_registration_and_login` | Registration, login, and token issuance | Valid token issued, role='customer' | **PASSED** |
| `test_admin_requires_authentication` | Admin endpoint security & RBAC | Reject unauth (401), reject customer (403) | **PASSED** |
| `test_new_def_001_auth002_detector_bypass` | Fake admin token detection | Intercepted & quarantined by AUTH-002 | **PASSED** |
| `test_new_def_002_and_003_token_expiration` | Expired token rejection & constant-time check | Expired token returns None; tampered rejected | **PASSED** |
| `test_new_def_004_server_side_logout_revocation`| Token revocation via `/auth/logout` | Token wiped from DB; subsequent calls 401 | **PASSED** |

---

## 6. Audit Conclusion
The authentication and RBAC controls meet enterprise security baselines. Critical bypass vectors have been successfully remediated. Recommendations for Argon2id and HttpOnly cookies are documented for roadmap implementation.
