# ShopSphere Security Architecture
## Phase 9: Application Security, Threat Defense & Defense-in-Depth

### 1. Security Design Principles
ShopSphere is engineered with security embedded directly into the application lifecycle:
1. **Never Trust the Client**: All prices, quantities, stock limits, and coupon discounts are calculated and verified exclusively on the server.
2. **Strict Principle of Least Privilege**: Customer accounts have zero access to administrative endpoints or other customers' orders.
3. **Defense-in-Depth HTTP Headers**: Applied to every HTTP response by `AppSecProtectionMiddleware`.
4. **Parameterized Data Access**: 100% of SQL queries across all services use parameterized `?` placeholders.

---

### 2. AppSec Protection Middleware & Threat Rules

All HTTP traffic to `/shop` and `/api/shop/*` passes through `AppSecProtectionMiddleware`:

| Rule ID | Threat Category | Inspection Criteria | Automated Action |
|---|---|---|---|
| **`SQLI-001`** | SQL Injection | Patterns matching `' OR '1'='1`, `UNION SELECT`, `DROP TABLE`, etc. in URI, headers, or body. | Quarantines IP, returns HTTP 403, triggers high-severity incident. |
| **`XSS-001`** | Cross-Site Scripting | `<script>`, `javascript:`, `onerror=`, `onload=` in query or request payload. | Quarantines IP, sanitizes input, logs event. |
| **`PATH-001`** | Path Traversal | `../`, `..\\`, `/etc/passwd`, `C:\Windows` in file or slug routes. | Returns HTTP 403, blocks source IP. |
| **`RATE-001`** | Request Rate Burst | In-memory sliding window exceeding 15 requests per 8-second window. | Returns HTTP 429 Too Many Requests with `Retry-After: 60`. |
| **`AUTH-001`** | Credential Stuffing | Repeated failed login attempts across multiple user accounts. | Throttles source IP, generates incident. |

---

### 3. Defense-in-Depth HTTP Response Headers

Every response emitted by the ShopSphere application includes:
```http
X-Correlation-ID: corr-XXXX
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

---

### 4. Commercial Integrity Protections
- **Negative / Zero Quantity Injection**: Pydantic models (`ge=1`) and service checks prevent negative or zero quantities from corrupting cart subtotals.
- **Client-Side Price Tampering**: Client requests pass only `product_id` and `quantity`. The unit price is fetched directly from the database at the time of order creation.
- **Coupon Abuse Prevention**: Minimum spend thresholds and per-coupon usage limits prevent coupon code reuse beyond authorized limits.
- **Double-Spend & Stock Race Conditions**: Prevented by SQLite atomic transactions and row locking.
