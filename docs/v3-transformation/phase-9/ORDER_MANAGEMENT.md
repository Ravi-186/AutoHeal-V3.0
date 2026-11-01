# Order Management & Fulfillment Architecture
## Phase 9: Order Lifecycle, Tracking & Inventory Replenishment

### 1. Order Data Architecture

Orders and line items are stored in relational tables with foreign keys and performance indexes:

```sql
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_ref TEXT UNIQUE NOT NULL,
    user_id INTEGER,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_phone TEXT NOT NULL,
    shipping_address TEXT NOT NULL,
    city TEXT NOT NULL,
    pincode TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    payment_status TEXT DEFAULT 'COMPLETED_SIMULATED',
    order_status TEXT DEFAULT 'PLACED',
    subtotal REAL NOT NULL,
    discount REAL DEFAULT 0.0,
    delivery_fee REAL DEFAULT 0.0,
    total_amount REAL NOT NULL,
    coupon_code TEXT,
    coupon_discount REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    unit_price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    total_price REAL NOT NULL,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(id)
);
```

---

### 2. Valid Order State Machine

```
      ┌──────────┐
      │  PLACED  │ ── Order created via transactional checkout; stock reserved.
      └────┬─────┘
           │
           ▼
    ┌──────────────┐
    │  PROCESSING  │ ── Picked and packaged in fulfillment center.
    └──────┬───────┘
           │
           ▼
     ┌───────────┐
     │  SHIPPED  │ ── Handed over to courier; tracking active.
     └─────┬─────┘
           │
           ▼
    ┌─────────────┐
    │  DELIVERED  │ ── Successfully delivered to recipient.
    └─────────────┘

    (Alternate Branch from PLACED or PROCESSING)
           │
           ▼
    ┌─────────────┐
    │  CANCELLED  │ ── Customer cancels order; stock immediately restored to inventory.
    └─────────────┘
```

---

### 3. Order Tracking & Customer Protection

1. **Order Reference Identifier (`order_ref`)**:
   - Format: `ORD-2026-XXXX` where `XXXX` is an 8-character uppercase cryptographic hexadecimal string (`secrets.token_hex(4).upper()`).
   - Prevents sequential ID guessing / enumeration attacks (e.g. IDOR).
2. **Ownership Verification (`cancel_order`)**:
   - `OrderService.cancel_order` enforces customer ownership. If `user_id` does not match the order record, a `PermissionError` is thrown, returning HTTP 403.
   - Orders in `DELIVERED` or `CANCELLED` status cannot be cancelled.
3. **Automated Stock Restoration**:
   - Upon cancellation, all quantities in `order_items` are atomically added back to `products.stock`.
   - Payment status transitions to `REFUNDED_SIMULATED`.
