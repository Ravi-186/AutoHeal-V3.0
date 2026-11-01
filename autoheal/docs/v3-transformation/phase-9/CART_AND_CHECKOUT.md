# Shopping Cart & Transactional Checkout Architecture
## Phase 9: Financial Precision, Coupon Discounts & Multi-Step Checkout

### 1. Overview
The ShopSphere shopping cart and checkout pipeline is engineered with banking-grade financial precision and strict server-side transaction boundaries. Prices, discounts, coupon deductions, delivery fees, and inventory locks are computed exclusively on the backend to prevent client-side tampering.

---

### 2. Shopping Cart Data Model & Lifecycle

Cart items are tracked per session or customer in the `cart_items` table:
```sql
CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_or_session_id TEXT NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
);
```

#### 2.1 Pure Business Math Calculations
`CartService.calculate_cart_totals` computes cart totals deterministically:
- **`subtotal`**: $\sum (\text{selling\_price} \times \text{quantity})$
- **`original_subtotal`**: $\sum (\text{MRP} \times \text{quantity})$
- **`discount`**: $\max(0, \text{original\_subtotal} - \text{subtotal})$
- **`coupon_discount`**: Computed via `CouponService.validate_coupon` based on active coupon rules and maximum discount caps.
- **`delivery_fee`**: Free delivery on orders $\ge ₹500$, otherwise ₹40.
- **`final_total`**: $\max(0, \text{subtotal} - \text{coupon\_discount} + \text{delivery\_fee})$.

All floating point values are rounded to 2 decimal places using server-side standard rounding.

---

### 3. Promotional Coupon Integration

Coupons are managed in the `coupons` table:
```sql
CREATE TABLE IF NOT EXISTS coupons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    discount_type TEXT NOT NULL,          -- 'PERCENTAGE' or 'FIXED'
    discount_value REAL NOT NULL,
    min_order_amount REAL DEFAULT 0.0,
    max_discount_amount REAL,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    usage_count INTEGER DEFAULT 0,
    usage_limit INTEGER DEFAULT 1000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Seeded Promotional Codes
1. **`WELCOME10`**: 10% discount on any order value.
2. **`SAVE20`**: 20% discount on orders $\ge ₹2,000$ (capped at ₹3,000).
3. **`FESTIVE50`**: Flat ₹500 discount on orders $\ge ₹3,000$.

---

### 4. Transactional Multi-Step Checkout

The checkout process (`POST /api/shop/checkout`) executes inside an explicit SQLite atomic transaction boundary (`with conn:`):

```
[Customer Submits Checkout Form]
                │
                ▼
      [Backend Input Validation]
      - Customer Name, Email, Address, City, PIN
                │
                ▼
      [Recalculate Cart & Validate Stock]
      - Verify each item quantity <= available product stock
                │
                ▼
      [Begin Atomic Database Transaction]
      ├── 1. Generate Order Ref (ORD-2026-XXXX)
      ├── 2. Record Coupon Usage (increment usage_count)
      ├── 3. Insert into orders table
      ├── 4. Insert items into order_items table
      ├── 5. Atomically decrement stock:
      │      UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?
      └── 6. Clear shopping cart for user/session
                │
                ▼
      [Transaction Committed Successfully]
                │
                ▼
      [Dispatch In-App Confirmation Notification]
                │
                ▼
      [Return 200 OK with Order Object to Client]
```

#### Concurrency & Tamper Resistance
- **Race Condition Prevention**: If concurrent buyers purchase the last stock unit simultaneously, the atomic query `WHERE stock >= ?` fails with `rowcount == 0`, immediately raising a `ValueError` and rolling back the entire transaction.
- **Zero Raw Card Data**: Payment methods (`UPI / QR Code`, `Credit/Debit Card (PCI Vault)`, `Cash on Delivery`) are executed in a simulated sandbox testing mode. No raw cardholder numbers or CVVs are accepted or stored.
- **Stock Restoration on Cancel**: When an order is cancelled via `POST /api/shop/orders/{id}/cancel`, stock is immediately and atomically credited back to the catalog inventory.
