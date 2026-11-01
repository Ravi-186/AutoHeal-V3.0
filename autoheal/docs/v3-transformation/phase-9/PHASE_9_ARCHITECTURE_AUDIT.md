# AutoHeal Phase 9: Architecture & Pre-Redesign Audit

## 1. Executive Summary

This architecture audit evaluates the state of the **ShopSphere E-Commerce Platform** prior to the Phase 9 Premium Modern Redesign. 

ShopSphere serves two critical functions within the AutoHeal ecosystem:
1. **Target Application for AutoHeal AppSec**: It acts as the live, controlled security-testing environment. WAF rules, rate-limiting, SQL injection filters, brute-force detectors, and autonomous self-healing engines actively protect ShopSphere.
2. **Realistic E-Commerce Shopping Experience**: It provides customer shopping, product discovery, dynamic pricing, cart management, inventory controls, order tracking, and store administration.

This audit establishes the baseline architectural state, identifies gaps between the existing Flipkart-inspired single-page template and modern premium consumer marketplace standards, and outlines the implementation plan for Phase 9.

---

## 2. Existing Frontend Architecture

### 2.1 Component Structure (`web/templates/shopsphere.html`)
- **Template Engine**: Jinja2 single-file template served at `GET /shop`.
- **Styling Architecture**: Embedded CSS within `<style>` tags (~1,300 lines) modeled after Indian e-commerce marketplace conventions (blue primary `#2874f0`, yellow accents `#ffe500`, rupee symbol `₹`).
- **Interactive Logic**: Vanilla JavaScript with embedded DOM manipulation (~1,280 lines) managing client-side catalog rendering, cart mutations, modal visibility, and sandbox payment simulation.
- **Client State**:
  - `sessionId`: Ephemeral UUID generated in `localStorage` (`shop_session_id`).
  - `authToken`: JWT/session token stored in `localStorage` (`shopsphere_token`).
  - `cartData`: Cached shopping cart object loaded from `/api/shop/cart`.
  - `wishlistList`: Cached wishlist array loaded from `/api/shop/wishlist`.

### 2.2 Strengths
- Real backend API integration: Cart, wishlist, catalog, authentication, and order workflows make real HTTP calls to `/api/shop/*`.
- Built-in AutoHeal demonstration widget (`.autoheal-panel`) displaying real-time bug injection and autonomous patch status.
- Zero external frontend framework overhead (no React/Vue hydration mismatch; fast load times).

### 2.3 Identified Limitations & Gaps
- **Visual Identity**: The Flipkart-style blue-and-yellow scheme feels utilitarian rather than premium. Modern consumer expectations favor spacious luxury aesthetics: clean white and warm-neutral surfaces, refined typography, elegant brand accents, modern cards, and subtle transitions.
- **Product Detail**: Product details are presently confined to a basic quick-view modal rather than a full-featured product detail page with rich specs, image galleries, and customer reviews.
- **Reviews & Ratings**: Review counts and star ratings are static fields on product rows rather than interactive, user-submitted reviews with verified purchase badges.
- **Coupons & Promotions**: Lacks a coupon code redemption engine during cart or checkout.
- **Customer Account Center**: Profile details and order history are accessible only through disjointed modals rather than an integrated customer dashboard.
- **Admin Dashboard**: The admin experience is a basic modal rather than a structured portal for inventory control, order fulfillment, promotions, and sales analytics.

---

## 3. Existing Backend Architecture & Services

### 3.1 Backend Application (`shopsphere/`)
- **`shopsphere/api.py`** (431 lines): FastAPI APIRouter mounted at `/api/shop` providing 18 REST endpoints.
- **`shopsphere/services.py`** (744 lines): Core domain logic split across 6 classes:
  - `ProductService`: Multi-criteria catalog filtering, text search, price-range queries, and pagination.
  - `CartService`: Financial calculations (subtotal, original MRP, discount, delivery fee), item addition, stock caps, and removal.
  - `WishlistService`: Toggle items and move-to-cart operations.
  - `OrderService`: Transactional checkout with row-level stock locks, reference generation (`ORD-2026-XXXX`), order history, and cancellation stock restoration.
  - `UserService`: PBKDF2-HMAC-SHA256 salted password hashing, registration, login token generation with 7-day expiration, and session revocation.
  - `AdminService`: Dashboard sales analytics, inventory updates, and order fulfillment status transitions.
- **`shopsphere/database.py`** (1,407 lines): SQLite WAL database management and initial schema seeding.
- **`shopsphere/autoheal_engine.py`** (232 lines): 11-step AutoHeal bug injection and self-healing test engine.

---

## 4. Database Schema Audit

The existing SQLite database (`data/shopsphere.db`) manages 26 production tables. The e-commerce core utilizes 7 tables:

```
[users] ──────────< [orders] ──────────< [order_items] >────────── [products]
  │                    │                                                │
  │                    │                                                │
  ▼                    ▼                                                ▼
[cart_items]      [admin_audit_logs]                               [categories]
  │
  ▼
[wishlist]
```

### Existing Table Capabilities
1. `users`: Stores customer and administrator accounts with roles (`customer`, `admin`), addresses, and expiring tokens.
2. `categories`: 8 categories (`mobiles`, `laptops`, `electronics`, `fashion`, `home`, `beauty`, `sports`, `books`).
3. `products`: 14 catalog items with prices, MRP, discounts, stock levels, and JSON specs.
4. `cart_items`: User/session-scoped line items with stock limit checking.
5. `wishlist`: User/session-scoped favorite items.
6. `orders`: Order headers with financial totals, delivery addresses, and payment statuses (`COMPLETED_SIMULATED`).
7. `order_items`: Line-item snapshots with unit prices and quantities.

### Missing Tables for Phase 9
- **Table 27: `product_reviews`**: Required for persistent customer reviews, star ratings (1-5), verified purchase indicators, and helpfulness votes.
- **Table 28: `coupons`**: Required for promo codes (`WELCOME10`, `SAVE20`, `FESTIVE50`), percentage vs fixed discounts, minimum thresholds, and expiration dates.
- **Table 29: `customer_notifications`**: Required for order updates, delivery tracking alerts, and low-stock alerts.

---

## 5. Security Controls & AutoHeal Integration

### 5.1 AppSec Middleware Interception (`src/appsec/middleware.py`)
All requests to `/api/shop/*` and `/shop` pass through `AppSecProtectionMiddleware`:
- **Rate-Limiting (RATE-001)**: Max 15 requests per 8-second window per IP. Exceeding triggers HTTP 429 and incident logging.
- **Attack Payload Inspection**: Request bodies, query parameters, and headers are evaluated by `AppSecDetector`:
  - `SQLI-001`: SQL injection strings (e.g. `' OR 1=1--`, `UNION SELECT`) are blocked with HTTP 403.
  - `XSS-001`: Script injection tags (`<script>`, `javascript:`) are blocked with HTTP 403.
  - `PATH-001`: Directory traversal attempts (`../`, `/etc/passwd`) are blocked with HTTP 403.
  - `AUTH-001`: Failed login surges trigger credential stuffing alerts and temporary IP quarantine in `blocked_clients`.

### 5.2 Mandatory Compatibility Invariants
- The redesign must **NEVER** bypass, weaken, or whitelist `/api/shop/*` from `AppSecProtectionMiddleware`.
- Controlled attack simulation scenarios (`tests/test_attack_simulation_center.py` and `tests/test_live_security_testing.py`) must continue targeting `/api/shop/products`, `/api/shop/auth/login`, and `/api/shop/cart`.
- The dual-probe verification mechanism (Attacker Probe 403 vs Benign Shopper 200 OK) must remain completely functional.

---

## 6. Phase 9 Redesign & Upgrade Strategy

```
+-----------------------------------------------------------------------------------------+
|                         PHASE 9 SHOPSPHERE UPGRADE STRATEGY                             |
+-----------------------------------------------------------------------------------------+
|                                                                                         |
|   1. Visual Elevation (Premium Modern E-Commerce)                                       |
|      - Clean white surfaces (#FFFFFF), warm neutral slate (#F8FAFC, #F1F5F9)             |
|      - High-contrast charcoal typography (#0F172A, #1E293B, #475569)                    |
|      - Refined Sapphire brand accent (#2563EB) & Emerald conversion accents (#059669)   |
|      - Curated high-resolution Unsplash product photography with crisp shadows          |
|                                                                                         |
|   2. Full Feature Architecture                                                          |
|      - Multi-view architecture (Landing, Catalog, Detail, Cart, Multi-step Checkout)    |
|      - Customer Dashboard (Profile, Orders with Tracking Timeline, Saved Addresses)     |
|      - Interactive Customer Reviews & Ratings with Verified Purchase Badges             |
|      - Server-Side Promo & Coupon Code Engine with Live Cart Discount Calculation       |
|      - Dedicated ShopSphere Admin Portal with Live SQLite Analytics & Stock Controls    |
|      - In-App Notifications Drawer with Order Lifecycle & Security Alerts               |
|                                                                                         |
|   3. Robust Security & Zero Regression                                                  |
|      - 100% telemetry generation to AutoHeal security_events & security_incidents       |
|      - Atomic transactions on inventory mutations and order checkout                     |
|      - Full test suite: 199 baseline tests + dedicated Phase 9 test suite               |
|                                                                                         |
+-----------------------------------------------------------------------------------------+
```
