# ShopSphere REST API Reference
## Phase 9: Comprehensive API Endpoint Inventory

All ShopSphere endpoints are exposed under the `/api/shop` router prefix.

---

### 1. Catalog & Discovery Endpoints

| Method | Endpoint | Description | Request / Query Parameters | Response |
|---|---|---|---|---|
| `GET` | `/products` | List & search products with filtering | `q`, `category`, `min_price`, `max_price`, `min_rating`, `in_stock_only`, `sort_by`, `page`, `page_size` | `{ products: [], total: int, page: int }` |
| `GET` | `/products/{id}` | Get product details & specs | `id: int` | `{ id, title, price, stock, specs, ... }` |
| `GET` | `/categories` | List product categories | None | `[ { id, name, slug, product_count }, ... ]` |
| `GET` | `/products/{id}/reviews` | Get customer reviews & rating breakdown | `id: int` | `{ product_id, total_reviews, average_rating, distribution, reviews: [] }` |
| `POST` | `/products/{id}/reviews` | Submit a verified customer review | `ReviewCreateRequest` (`rating`, `headline`, `comment`, `author_name`) | `{ id, product_id, rating, headline, ... }` |
| `DELETE`| `/reviews/{id}` | Delete a review (Author or Admin) | `id: int` | `{ status: "success", message: str }` |

---

### 2. Promotional Coupons Endpoints

| Method | Endpoint | Description | Request / Query Parameters | Response |
|---|---|---|---|---|
| `POST` | `/coupons/validate` | Validate promo code against order subtotal | `CouponValidateRequest` (`code`, `order_subtotal`) | `{ valid: bool, code, discount_amount, message }` |
| `GET` | `/coupons` | List all active public promotional coupons | None | `[ { code, discount_type, discount_value, min_order_amount, ... }, ... ]` |

---

### 3. Shopping Cart Endpoints

| Method | Endpoint | Description | Request / Query Parameters | Response |
|---|---|---|---|---|
| `GET` | `/cart` | Retrieve shopping cart and financial summary | `session_id`, `coupon_code` (optional) | `{ items: [], subtotal, discount, coupon_discount, delivery_fee, final_total }` |
| `POST` | `/cart/add` | Add product to cart (stock-capped) | `CartItemRequest` (`session_id`, `product_id`, `quantity`) | `{ status: "success", cart: CartData }` |
| `POST` | `/cart/update` | Update item quantity in cart | `CartUpdateRequest` (`session_id`, `product_id`, `quantity`) | `{ status: "success", cart: CartData }` |
| `POST` | `/cart/remove` | Remove product completely from cart | `CartRemoveRequest` (`session_id`, `product_id`) | `{ status: "success", cart: CartData }` |
| `POST` | `/cart/clear` | Clear all items from cart | `session_id: str` | `{ status: "success", message: str }` |
| `POST` | `/cart/apply-coupon` | Apply coupon code to active cart | `ApplyCouponRequest` (`session_id`, `coupon_code`) | `{ status: "success", cart: CartData }` |

---

### 4. Wishlist Endpoints

| Method | Endpoint | Description | Request / Query Parameters | Response |
|---|---|---|---|---|
| `GET` | `/wishlist` | Retrieve customer wishlist | `session_id: str` | `[ { product_id, title, price, ... }, ... ]` |
| `POST` | `/wishlist/toggle` | Toggle product in/out of wishlist | `WishlistToggleRequest` (`session_id`, `product_id`) | `{ in_wishlist: bool, wishlist: [] }` |
| `POST` | `/wishlist/move-to-cart`| Move item from wishlist into cart | `WishlistToggleRequest` (`session_id`, `product_id`) | `{ cart: CartData, wishlist: [] }` |

---

### 5. Checkout & Orders Endpoints

| Method | Endpoint | Description | Request / Query Parameters | Response |
|---|---|---|---|---|
| `POST` | `/checkout` | Complete transactional order checkout | `CheckoutRequest` (`session_id`, `customer_name`, `customer_email`, `customer_phone`, `shipping_address`, `city`, `pincode`, `payment_method`, `coupon_code`) | `{ status: "success", order: OrderData }` |
| `GET` | `/orders` | List customer orders | `email: str` or Authenticated User Token | `[ OrderData, ... ]` |
| `GET` | `/orders/{ref_or_id}` | Retrieve specific order details | `ref_or_id: str` | `OrderData` with items list |
| `POST` | `/orders/{id}/cancel` | Cancel order & restore inventory stock | `id: int` | `{ status: "success", order: OrderData }` |

---

### 6. Customer Authentication & Profile Endpoints

| Method | Endpoint | Description | Request / Query Parameters | Response |
|---|---|---|---|---|
| `POST` | `/auth/register` | Register customer account | `RegisterRequest` (`name`, `email`, `password`, `phone`, `address`, `city`, `pincode`) | `{ status: "success", user: UserData }` |
| `POST` | `/auth/login` | Authenticate customer/admin | `LoginRequest` (`email`, `password`) | `{ status: "success", user: UserData }` |
| `GET` | `/auth/me` | Get authenticated profile | `Authorization: Bearer <token>` | `UserData` |
| `PUT` | `/auth/profile` | Update contact & delivery address | `ProfileUpdateRequest` (`name`, `phone`, `address`, `city`, `pincode`) | `{ status: "success", user: UserData }` |
| `POST` | `/auth/logout` | Revoke active session token | `Authorization: Bearer <token>` | `{ status: "success", message: str }` |

---

### 7. Customer In-App Notifications Endpoints

| Method | Endpoint | Description | Request / Query Parameters | Response |
|---|---|---|---|---|
| `GET` | `/notifications` | List customer in-app notifications | `email` or Authenticated User Token | `[ NotificationData, ... ]` |
| `POST` | `/notifications/{id}/read` | Mark single notification as read | `id: int` | `{ status: "success", message: str }` |
| `POST` | `/notifications/read-all` | Mark all notifications as read | `email` or Authenticated User Token | `{ status: "success", message: str }` |

---

### 8. Admin Portal Endpoints (RBAC Enforced)

| Method | Endpoint | Description | Authorization | Response |
|---|---|---|---|---|
| `GET` | `/admin/stats` | Executive revenue & inventory KPIs | Admin Token Required | `{ total_revenue, total_orders, total_products, out_of_stock_count, ... }` |
| `GET` | `/admin/orders` | List all orders with status filter | Admin Token Required | `[ OrderData, ... ]` |
| `POST` | `/admin/orders/{id}/status`| Update order fulfillment status | Admin Token Required | `{ status: "success", order: OrderData }` |
| `POST` | `/admin/products/{id}/stock`| Update product inventory stock level | Admin Token Required | `{ status: "success", product: ProductData }` |
| `GET` | `/admin/coupons` | List all promotional coupons | Admin Token Required | `[ CouponData, ... ]` |
| `POST` | `/admin/coupons` | Create or update coupon | Admin Token Required | `CouponData` |
| `GET` | `/admin/customers` | List all registered shoppers | Admin Token Required | `[ CustomerData, ... ]` |

---

### 9. AutoHeal Demonstration & Health Endpoints

| Method | Endpoint | Description | Response |
|---|---|---|---|
| `GET` | `/autoheal/status` | Get AutoHeal demo engine status | `{ bug_injected: bool, baseline_status: str }` |
| `POST` | `/autoheal/inject-bug` | Inject controlled CartService math defect | `{ status: "BUG_INJECTED", description: str }` |
| `POST` | `/autoheal/regression-test` | Execute regression test suite | `{ passed: bool, error: Optional[str] }` |
| `POST` | `/autoheal/diagnose` | Run AI AST root-cause diagnostic | `{ root_cause_found: bool, finding: str, prescribed_patch: str }` |
| `POST` | `/autoheal/apply-fix` | Deploy surgical self-healing patch | `{ status: "PATCH_APPLIED", action: str, duration_ms: float }` |
| `POST` | `/autoheal/run-full-demo` | Run full 11-step autonomous cycle | `{ completed_successfully: bool, steps: [] }` |
| `GET` | `/health` | API operational and database health check | `{ status: "UP", database: "CONNECTED", ... }` |
