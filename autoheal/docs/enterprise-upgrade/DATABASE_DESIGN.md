# AutoHeal & ShopSphere: Enterprise Database Design Specification

**Author:** Database Architect & Site Reliability Engineer  
**Document Ref:** `DB-DESIGN-001`  
**Database Engine:** SQLite 3 with Write-Ahead Logging (WAL) Mode  
**Database File:** `autoheal/data/shopsphere.db`  
**Date:** 2026-11-01  

---

## 1. Engine Configuration & Pragmas

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 30000;
```

---

## 2. Table Schemas & Foreign Key Relationships

### 2.1 E-Commerce Core Domain
1. **`users`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `name TEXT NOT NULL`, `email TEXT UNIQUE NOT NULL`, `password_hash TEXT NOT NULL`, `salt TEXT NOT NULL`
   - `role TEXT NOT NULL DEFAULT 'customer'` (values: 'admin', 'customer', 'analyst')
   - `phone TEXT`, `address TEXT`, `city TEXT`, `pincode TEXT`
   - `token TEXT UNIQUE`, `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

2. **`categories`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `slug TEXT UNIQUE NOT NULL`, `name TEXT NOT NULL`, `icon TEXT`, `display_order INTEGER`

3. **`products`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `category_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT`
   - `title TEXT NOT NULL`, `description TEXT`, `price REAL NOT NULL`, `original_price REAL`
   - `discount_percent INTEGER DEFAULT 0`, `rating REAL DEFAULT 4.5`, `rating_count INTEGER DEFAULT 120`
   - `stock INTEGER NOT NULL DEFAULT 50`, `image_url TEXT`, `badge TEXT`, `created_at TIMESTAMP`

4. **`cart_items`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `user_or_session_id TEXT NOT NULL`, `product_id INTEGER REFERENCES products(id) ON DELETE CASCADE`
   - `quantity INTEGER NOT NULL DEFAULT 1`, `added_at TIMESTAMP`
   - `UNIQUE(user_or_session_id, product_id)`

5. **`wishlist`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `user_or_session_id TEXT NOT NULL`, `product_id INTEGER REFERENCES products(id) ON DELETE CASCADE`
   - `added_at TIMESTAMP`, `UNIQUE(user_or_session_id, product_id)`

6. **`orders`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `order_ref TEXT UNIQUE NOT NULL`, `user_id INTEGER REFERENCES users(id) ON DELETE SET NULL`
   - `customer_name TEXT NOT NULL`, `customer_email TEXT NOT NULL`, `customer_phone TEXT NOT NULL`
   - `shipping_address TEXT NOT NULL`, `city TEXT NOT NULL`, `pincode TEXT NOT NULL`
   - `payment_method TEXT NOT NULL`, `payment_status TEXT NOT NULL DEFAULT 'COMPLETED_SIMULATED'`
   - `order_status TEXT NOT NULL DEFAULT 'PLACED'`, `subtotal REAL NOT NULL`, `discount REAL NOT NULL`
   - `delivery_fee REAL NOT NULL`, `total_amount REAL NOT NULL`, `created_at TIMESTAMP`

7. **`order_items`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE`
   - `product_id INTEGER REFERENCES products(id) ON DELETE RESTRICT`
   - `title TEXT NOT NULL`, `unit_price REAL NOT NULL`, `quantity INTEGER NOT NULL`, `total_price REAL`

8. **`admin_audit_logs`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `admin_email TEXT NOT NULL`, `action TEXT NOT NULL`, `target_entity TEXT NOT NULL`
   - `details TEXT`, `timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

---

### 2.2 AutoHeal SOC Telemetry & Defense Domain
9. **`security_events`**:
   - `id INTEGER PRIMARY KEY AUTOINCREMENT`
   - `event_id TEXT UNIQUE NOT NULL`, `correlation_id TEXT NOT NULL`, `timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
   - `client_ip TEXT NOT NULL`, `user_agent TEXT`, `method TEXT NOT NULL`, `path TEXT NOT NULL`
   - `status_code INTEGER NOT NULL`, `latency_ms REAL NOT NULL DEFAULT 0.0`
   - `user_id_or_session TEXT`, `event_type TEXT NOT NULL`, `severity TEXT NOT NULL DEFAULT 'INFO'`
   - `details_json TEXT`, `action_taken TEXT NOT NULL DEFAULT 'ALLOWED'`

10. **`security_incidents`**:
    - `id INTEGER PRIMARY KEY AUTOINCREMENT`
    - `incident_id TEXT UNIQUE NOT NULL`, `rule_id TEXT NOT NULL`, `title TEXT NOT NULL`
    - `category TEXT NOT NULL`, `severity TEXT NOT NULL`, `status TEXT NOT NULL DEFAULT 'OPEN'`
    - `confidence REAL NOT NULL DEFAULT 1.0`, `summary TEXT NOT NULL`, `evidence_json TEXT`
    - `affected_endpoints_json TEXT`, `source_ip TEXT`, `impact_actual TEXT`, `impact_potential TEXT`
    - `mitigation_actions_json TEXT`, `remediation_details TEXT`, `regression_tests_json TEXT`
    - `verification_status TEXT NOT NULL DEFAULT 'PENDING'`
    - `mitre_technique_id TEXT`, `mitre_tactic TEXT`, `mitre_name TEXT`, `ai_summary TEXT`
    - `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`, `updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

11. **`blocked_clients`**:
    - `id INTEGER PRIMARY KEY AUTOINCREMENT`
    - `client_ip TEXT UNIQUE NOT NULL`, `reason TEXT NOT NULL`, `rule_id TEXT NOT NULL`
    - `incident_id TEXT`, `blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
    - `expires_at TIMESTAMP NOT NULL`, `is_active INTEGER NOT NULL DEFAULT 1`

12. **`vulnerabilities`**:
    - `id INTEGER PRIMARY KEY AUTOINCREMENT`
    - `vuln_id TEXT UNIQUE NOT NULL`, `title TEXT NOT NULL`, `category TEXT NOT NULL`, `severity TEXT NOT NULL`
    - `cwe_id TEXT NOT NULL`, `mitre_technique_id TEXT NOT NULL`, `component_path TEXT NOT NULL`
    - `status TEXT NOT NULL DEFAULT 'OPEN'`, `remediation_proposal TEXT NOT NULL`, `patch_diff TEXT NOT NULL`
    - `regression_test_name TEXT NOT NULL`, `regression_test_status TEXT NOT NULL DEFAULT 'PENDING'`
    - `approval_status TEXT NOT NULL DEFAULT 'PENDING'`, `approved_by TEXT`, `applied_at TIMESTAMP`

---

## 3. Composite Performance Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_blocked_clients_ip_active ON blocked_clients (client_ip, is_active, expires_at);
CREATE INDEX IF NOT EXISTS idx_security_events_temporal ON security_events (client_ip, timestamp);
CREATE INDEX IF NOT EXISTS idx_security_events_type_time ON security_events (event_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_security_incidents_status ON security_incidents (status, severity, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_customer_email ON orders (customer_email, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cart_items_user ON cart_items (user_or_session_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_user ON wishlist (user_or_session_id);
```

---

## 4. Transaction Atomicity & Concurrency Model

All multi-row business mutations (such as `OrderService.checkout`) are enclosed within an atomic transaction context:
```python
with get_db_connection() as conn:
    with conn:  # Enforces IMMEDIATE/DEFERRED transaction; automatic rollback on error
        ...
```
This guarantees that inventory is decremented, order items are stored, and the cart is emptied atomically. If an exception occurs at any point, all changes are rolled back automatically, preventing orphaned order rows or inventory leakage.
