# Frontend Architecture Specification
## Phase 9: Modern Reactive Vanilla Architecture & State Lifecycle

### 1. Architectural Strategy
The ShopSphere storefront is architected using **Modern Vanilla Web Technologies** (ES6+ JavaScript, CSS Custom Properties, Semantic HTML5) without external UI frameworks (React, Vue, Angular) or heavy script bundles.

This design achieves:
1. **Sub-millisecond First Contentful Paint (FCP):** Zero framework hydration overhead; immediate initial paint upon HTML parsing.
2. **Minimal Bundle Footprint:** Total template footprint under 120 KB inclusive of all styles, layouts, modals, and client logic.
3. **Transparent Security Testing:** Directly inspectable by AutoHeal's AST security analyzers, with zero obfuscated virtual DOM wrappers.
4. **Resilient Browser Support:** Operates seamlessly across modern mobile, tablet, and desktop viewports.

---

### 2. State Management Architecture

```
                       ┌────────────────────────┐
                       │     localStorage       │
                       │  - session_id          │
                       │  - auth_token          │
                       └───────────┬────────────┘
                                   │ Hydration
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Global Client State                             │
│                                                                        │
│  - currentCategory: str ('all', 'electronics', 'audio', ...)           │
│  - currentSearchQuery: str                                             │
│  - currentMaxPrice: int (slider value)                                 │
│  - currentMinRating: float (0.0, 4.0, 4.5)                             │
│  - currentInStockOnly: bool                                            │
│  - currentSort: str ('popularity', 'price_low', 'price_high', ...)     │
│  - productsCatalog: List[Product]                                      │
│  - shoppingCart: CartData { items, subtotal, discount, final_total }   │
│  - userWishlist: List[WishlistItem]                                    │
│  - authenticatedUser: Optional[UserData]                               │
│  - appliedCouponCode: Optional[str]                                    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Dispatches DOM Re-renders
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                              │
│                                                                        │
│  - Announcement Bar & Header Badges (cart total, unread notifs)        │
│  - Category Ribbon & Hero Spotlight Card                               │
│  - Catalog Product Grid (cards with badges, stock indicators)          │
│  - Slide-Over Drawers (Cart with delivery meter, Wishlist, Notifs)     │
│  - Interactive Modals (Product Details, Checkout, Auth, Admin)         │
│  - Floating AutoHeal Testing Console & Pulse Sentinel                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 3. Client-Side Lifecycle & Event Pipeline

1. **`DOMContentLoaded` Initialization:**
   - Evaluates `localStorage.getItem('shopsphere_session_id')`; generates cryptographically safe random session ID if missing.
   - Dispatches parallel API fetches:
     - `loadCatalogProducts()` -> `GET /api/shop/products`
     - `loadShoppingCart()` -> `GET /api/shop/cart`
     - `loadWishlist()` -> `GET /api/shop/wishlist`
     - `checkCurrentUserAuth()` -> `GET /api/shop/auth/me`
     - `loadNotifications()` -> `GET /api/shop/notifications`
     - `checkAutohealEngineStatus()` -> `GET /api/shop/autoheal/status`
2. **Catalog Discovery Pipeline:**
   - Filters are bound to reactive handlers (`handlePriceSliderChange`, `handleRatingFilter`, `selectCategory`, `executeSearch`).
   - Query parameters are dynamically synthesized and sent to `/api/shop/products`.
   - Results populate `productCardsGrid` with accessible DOM elements and fallback image handling.
3. **Cart & Wishlist Synchronization:**
   - Quantity mutations (`updateCartItemQuantity`) enforce available stock limits client-side and server-side.
   - Coupon applications (`applyCartCouponCode`) execute server-side financial calculations via `POST /api/shop/cart/apply-coupon`.
4. **Modal & Drawer Orchestration:**
   - Drawers and modals use CSS class `.active` with backdrop blur and smooth transitions.
   - Keyboard events (e.g. `Escape` key, click outside modal body via `event.stopPropagation()`) safely close modals without memory leaks.
