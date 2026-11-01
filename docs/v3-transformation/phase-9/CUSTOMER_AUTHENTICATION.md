# Customer Authentication & Session Management
## Phase 9: Secure Customer Onboarding, Role Separation & Profile Security

### 1. Authentication Security Model
ShopSphere implements consumer authentication designed according to NIST Special Publication 800-63B guidelines and OWASP Top 10 Application Security verification standards.

```
┌────────────────────────────────────────────────────────┐
│                   Customer Credentials                 │
│                 Email + Plaintext Password             │
└───────────────────────────┬────────────────────────────┘
                            │ SHA-256 / PBKDF2 + Salt (32-byte)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   Database Verification                │
│       Salted Password Hash + Constant-time Check       │
└───────────────────────────┬────────────────────────────┘
                            │ Match Confirmed
                            ▼
┌────────────────────────────────────────────────────────┐
│               Session Token Generation                 │
│      token_XXXX / token_admin_XXXX (Crypto 48-char)    │
│            Server-side Expiration: 7 Days              │
└────────────────────────────────────────────────────────┘
```

---

### 2. User Data Architecture

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    role TEXT DEFAULT 'customer',
    phone TEXT,
    address TEXT,
    city TEXT,
    pincode TEXT,
    token TEXT,
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Default Seeded Profiles
- **Consumer Shopper**: `rahul.shopper@example.com` / `Demo@123` (Role: `customer`)
- **Store Administrator**: `admin@shopsphere.com` / `Admin@123` (Role: `admin`)

---

### 3. Key Defensive Controls

1. **Salted Password Hashing (`hash_password`, `verify_password`)**:
   - Every password hash is generated with a unique 32-byte cryptographic salt (`secrets.token_hex(32)`).
   - Rainbow tables and precomputed hash dictionaries are completely ineffective.
2. **Timing-Attack Resistance**:
   - Token lookup employs `secrets.compare_digest(row["token"], token)` to prevent side-channel timing analysis attacks.
3. **Server-Side Session Expiration**:
   - `token_expires_at` is enforced in `UserService.get_by_token`. Expired tokens return `None`, compelling re-authentication.
4. **Instant Server-Side Token Revocation (`POST /api/shop/auth/logout`)**:
   - Sets `token = NULL` and `token_expires_at = NULL` in SQLite, invalidating the session immediately across all devices.
5. **Strict Role-Based Access Control (RBAC)**:
   - FastAPI dependency `require_admin_user` checks `user.get("role") == "admin"`.
   - Customer tokens attempting administrative calls receive HTTP 403 Forbidden.
