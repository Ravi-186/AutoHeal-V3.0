# AutoHeal & ShopSphere: Database Architecture & Integrity Audit

**Author:** Principal Database Architect & Data Integrity Group  
**Date:** 2026-11-01  
**Project:** AutoHeal Autonomous SOC Platform  
**Document Ref:** `DB-AUDIT-001`  

---

## 1. Database Overview

The project uses a unified relational SQLite3 database located at `autoheal/data/shopsphere.db`. It serves as the single source of truth for both ShopSphere e-commerce operations and AutoHeal autonomous SOC telemetry.

### 1.1 Connection Management & Pragmas
Database connections are managed via a Python context manager (`shopsphere.database.get_db_connection()`):
- **WAL Mode (`PRAGMA journal_mode = WAL;`):** Write-Ahead Logging allows multiple concurrent readers to access tables simultaneously without locking out background writers (such as the telemetry middleware or verification agent).
- **Foreign Keys (`PRAGMA foreign_keys = ON;`):** Enforces referential integrity at the database engine level.
- **Connection Timeout:** Explicit 30.0-second timeout to handle peak contention gracefully.

---

## 2. Table-by-Table Schema Analysis

### 2.1 E-Commerce Core Tables

#### `users`
- **Columns:** `id`, `name`, `email` (UNIQUE), `password_hash`, `salt`, `role`, `phone`, `address`, `city`, `pincode`, `token`, `created_at`.
- **Integrity:** `email` is strictly unique. Passwords use PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte random salts.
- **Finding:** Default admin account seeded with hardcoded token `"token_admin_shopsphere_secret"`.

#### `categories`
- **Columns:** `id`, `name` (UNIQUE), `slug` (UNIQUE), `icon`, `description`.
- **Integrity:** Seeded with 10 primary Flipkart-style departments.

#### `products`
- **Columns:** `id`, `title`, `slug` (UNIQUE), `category`, `description`, `price`, `original_price`, `discount_percent`, `rating`, `review_count`, `stock`, `image_url`, `badge`, `specs_json`, `created_at`.
- **Integrity:** Check constraint missing on `stock >= 0`. (Currently enforced in Python application code).

#### `cart_items`
- **Columns:** `id`, `user_or_session_id`, `product_id`, `quantity`, `added_at`.
- **Integrity:** `UNIQUE(user_or_session_id, product_id)`.
- **Foreign Key:** `product_id REFERENCES products(id) ON DELETE CASCADE`.

#### `wishlist`
- **Columns:** `id`, `user_or_session_id`, `product_id`, `added_at`.
- **Integrity:** `UNIQUE(user_or_session_id, product_id)`.
- **Foreign Key:** `product_id REFERENCES products(id) ON DELETE CASCADE`.

#### `orders`
- **Columns:** `id`, `order_ref` (UNIQUE), `user_id`, `customer_name`, `customer_email`, `customer_phone`, `shipping_address`, `city`, `pincode`, `payment_method`, `payment_status`, `order_status`, `subtotal`, `discount`, `delivery_fee`, `total_amount`, `created_at`.
- **Foreign Key:** `user_id REFERENCES users(id) ON DELETE SET NULL`.
- **Integrity:** High. Guaranteed unique order references (`ORD-YYYY-XXXXXXXX`).

#### `order_items`
- **Columns:** `id`, `order_id`, `product_id`, `title`, `unit_price`, `quantity`, `total_price`.
- **Foreign Keys:** `order_id REFERENCES orders(id) ON DELETE CASCADE`, `product_id REFERENCES products(id) ON DELETE RESTRICT`.

#### `admin_audit_logs`
- **Columns:** `id`, `admin_email`, `action`, `target_entity`, `details`, `timestamp`.
- **Purpose:** Append-only ledger for all administrative interventions.

---

### 2.2 AutoHeal SOC & Telemetry Tables

#### `security_events`
- **Columns:** `id`, `event_id` (UNIQUE), `correlation_id`, `timestamp`, `client_ip`, `user_agent`, `method`, `path`, `status_code`, `latency_ms`, `user_id_or_session`, `event_type`, `severity`, `details_json`, `action_taken`.
- **Volume:** Continuously appended by `AppSecProtectionMiddleware`.
- **Finding:** Missing composite index on `(client_ip, timestamp)` and `(event_type, timestamp)`, which causes full table scans during sliding-window detection queries (`WHERE timestamp >= datetime('now', '-60 seconds')`).

#### `security_incidents`
- **Columns:** `id`, `incident_id` (UNIQUE), `rule_id`, `title`, `category`, `severity`, `status`, `confidence`, `summary`, `evidence_json`, `affected_endpoints_json`, `source_ip`, `impact_actual`, `impact_potential`, `mitigation_actions_json`, `remediation_details`, `regression_tests_json`, `verification_status`, `mitre_technique_id`, `mitre_tactic`, `mitre_name`, `ai_summary`, `ai_recommendations_json`, `recovery_status`, `created_at`, `updated_at`.
- **Integrity:** Idempotently upserted via `upsert_security_incident` keyed on `incident_id`.
- **Finding:** Needs an index on `(status, severity)` for dashboard filtering.

#### `blocked_clients`
- **Columns:** `id`, `client_ip` (UNIQUE), `reason`, `rule_id`, `incident_id`, `blocked_at`, `expires_at`, `is_active`.
- **Integrity:** Active quarantine records checked on every incoming HTTP request by middleware (`SELECT is_active, expires_at FROM blocked_clients WHERE client_ip = ?`).

#### `vulnerabilities`
- **Columns:** `id`, `vuln_id` (UNIQUE), `title`, `category`, `severity`, `cwe_id`, `mitre_technique_id`, `mitre_tactic`, `component_path`, `status`, `description`, `remediation_proposal`, `patch_diff`, `regression_test_name`, `regression_test_status`, `approval_status`, `approved_by`, `applied_at`, `rolled_back_at`, `created_at`.
- **Purpose:** Governs the formal vulnerability tracking, patch approval, and automated surgical code repair workflows.

---

## 3. Missing Indexes & Optimization Recommendations

To ensure sub-millisecond query latency under enterprise SOC event volumes, the following indexes are recommended for deployment in Phase Five:

```sql
-- 1. Accelerate Real-Time WAF Lookups
CREATE INDEX IF NOT EXISTS idx_blocked_clients_ip_active 
ON blocked_clients (client_ip, is_active, expires_at);

-- 2. Accelerate Sliding-Window Telemetry Queries
CREATE INDEX IF NOT EXISTS idx_security_events_temporal 
ON security_events (client_ip, timestamp);

CREATE INDEX IF NOT EXISTS idx_security_events_type_time 
ON security_events (event_type, timestamp);

-- 3. Accelerate Incident Dashboard Queries
CREATE INDEX IF NOT EXISTS idx_security_incidents_status 
ON security_incidents (status, severity, created_at DESC);

-- 4. Accelerate Order History & Admin Lookup
CREATE INDEX IF NOT EXISTS idx_orders_customer_email 
ON orders (customer_email, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_orders_user_id 
ON orders (user_id, created_at DESC);
```

---

## 4. Data Retention & Archival Strategy

1. **Telemetry Pruning:** Maintain 30-day retention for `security_events` table in production, archiving cold events to parquet/CSV monthly.
2. **Incident Permanence:** `security_incidents` and `admin_audit_logs` must remain permanent immutable historical records.
3. **Database Backup:** Snapshot `shopsphere.db` using SQLite's online backup API (`sqlite3_backup`) prior to applying migrations or patches.
