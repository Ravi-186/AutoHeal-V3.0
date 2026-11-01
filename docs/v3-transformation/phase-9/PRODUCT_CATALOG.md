# Product Catalog Architecture & Discovery Engine
## Phase 9: Real-Time Catalog Discovery, Filtering & Product Details

### 1. Catalog Data Architecture
The ShopSphere catalog is built upon a normalized relational model in SQLite (`products`, `categories`, `product_reviews` tables). Every product displays real data persisted in the database; no mock placeholders or simulated attributes exist.

```sql
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT UNIQUE,
    category TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    original_price REAL NOT NULL,
    discount_percent INTEGER DEFAULT 0,
    rating REAL DEFAULT 5.0,
    review_count INTEGER DEFAULT 0,
    stock INTEGER NOT NULL DEFAULT 10,
    image_url TEXT,
    badge TEXT,
    specs_json TEXT,
    brand TEXT DEFAULT 'ShopSphere',
    gallery_images_json TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 2. Supported Categories & Product Inventory
The catalog is partitioned across 8 consumer retail categories:

| Category Slug | Category Title | Sample Products in Catalog | Typical Price Range |
|---|---|---|---|
| `mobiles` / `electronics` | Electronics & Mobile | iPhone 15 Pro, Dell XPS 15, MacBook Pro M3 | ₹49,999 – ₹1,34,900 |
| `audio` | Personal Audio | Sony WH-1000XM5, Bose QuietComfort Ultra | ₹19,990 – ₹29,999 |
| `wearables` | Smart Wearables | Apple Watch Ultra, Garmin Fenix 7 | ₹44,999 – ₹64,999 |
| `home` | Home & Living | Espresso Coffee Machine, Smart Air Purifier | ₹12,999 – ₹24,999 |
| `fashion` | Footwear & Apparel | Nike Air Max 270, Leather Oxford Shoes | ₹4,999 – ₹11,999 |
| `accessories` | Travel & Lifestyle | Premium Leather Backpack, RFID Travel Wallet | ₹2,499 – ₹7,999 |

---

### 3. Filter & Search Query Mechanics
The backend endpoint `GET /api/shop/products` supports multi-dimensional parameterized querying:

- **Full-Text Search (`q`)**: Performs case-insensitive matching against product title, description, category, and brand using parameterized SQL queries (`title LIKE ? OR description LIKE ?`).
- **Category Filter (`category`)**: Exact slug filtering (`category = ?`).
- **Price Bounds (`min_price`, `max_price`)**: Range filtering (`price >= ? AND price <= ?`).
- **Rating Threshold (`min_rating`)**: Filters products having average customer ratings at or above the threshold (`rating >= ?`).
- **Stock Availability (`in_stock_only`)**: Excludes out-of-stock items (`stock > 0`).
- **Sort Strategies (`sort_by`)**:
  - `popularity`: Orders by review count and rating (`review_count DESC, rating DESC`).
  - `price_low`: Ascending price (`price ASC`).
  - `price_high`: Descending price (`price DESC`).
  - `rating`: Descending rating (`rating DESC`).
  - `newest`: Reverse chronological creation (`id DESC`).

---

### 4. Product Details Modal & Verified Reviews
Clicking any product card loads the interactive product modal:
- **Visual Presentation**: High-resolution image preview, discount tags, live inventory alerts (`⚡ Only X units remaining!`).
- **Structured Specifications**: Technical specifications dynamically parsed from `specs_json` (Display, Processor, Battery, RAM, Connectivity).
- **Verified Customer Reviews**:
  - Summary score with star rating distribution (5★ to 1★ progress bars).
  - List of reviews featuring headline, author, review date, and verified buyer badges.
  - Interactive "Write a Review" form allowing customers to rate (1–5) and submit written feedback.
  - Automatic dynamic recalculation of average rating and total review counts in SQLite.
