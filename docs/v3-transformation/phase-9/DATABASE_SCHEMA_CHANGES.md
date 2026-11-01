# Database Schema Changes & Migrations
## Phase 9: Table Additions, Column Migrations & Performance Indexes

### 1. Overview of SQLite Database Evolution
In Phase 9, `autoheal/data/shopsphere.db` was enhanced from 26 tables to **30 normalized relational tables** to support real-time product reviews, promotional coupons, customer in-app notifications, and advanced order fulfillment metadata.

---

### 2. New Database Tables (Phase 9)

#### Table 27: `product_reviews`
Stores customer ratings, review headlines, detailed feedback, and verified purchase flags.
```sql
CREATE TABLE IF NOT EXISTS product_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    user_id INTEGER,
    author_name TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    headline TEXT NOT NULL,
    comment TEXT NOT NULL,
    is_verified_purchase INTEGER DEFAULT 0,
    helpful_votes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);
```

#### Table 28: `coupons`
Defines active promotional campaigns, discount structures, minimum order thresholds, and usage limits.
```sql
CREATE TABLE IF NOT EXISTS coupons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    discount_type TEXT NOT NULL,            -- 'PERCENTAGE' or 'FIXED'
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

#### Table 29: `customer_notifications`
Provides persistent in-app notifications for order tracking, fulfillment status changes, and promotions.
```sql
CREATE TABLE IF NOT EXISTS customer_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    customer_email TEXT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT DEFAULT 'ORDER_UPDATE',
    is_read INTEGER DEFAULT 0,
    link_url TEXT DEFAULT '/shop',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

### 3. Column Alteration Migrations (Backwards Compatible)

The schema initialization migration safely alters existing tables if columns are missing:
1. **`orders` Table**:
   - `coupon_code TEXT` (Stores applied promotional code on completed order).
   - `coupon_discount REAL DEFAULT 0.0` (Stores calculated financial discount deducted from total).
2. **`products` Table**:
   - `brand TEXT DEFAULT 'ShopSphere'` (Allows brand-level grouping and filtering).
   - `gallery_images_json TEXT DEFAULT '[]'` (Stores serialized JSON array of auxiliary product images).

---

### 4. Performance Indexes Added

To maintain sub-15ms query execution under heavy catalog browsing and concurrent checkout demands:
```sql
CREATE INDEX IF NOT EXISTS idx_product_reviews_prod ON product_reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_coupons_code ON coupons(code);
CREATE INDEX IF NOT EXISTS idx_customer_notifs_user ON customer_notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_orders_customer_email ON orders(customer_email);
```
