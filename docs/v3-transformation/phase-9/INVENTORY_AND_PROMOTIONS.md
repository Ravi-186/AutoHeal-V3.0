# Inventory Management & Promotions Architecture
## Phase 9: Stock Allocation, Low-Stock Alerts & Coupon Promotions

### 1. Inventory Management Architecture
ShopSphere enforces inventory controls to prevent overselling, race conditions, and phantom stock allocation.

#### 1.1 Real-Time Stock Status
Stock counts in the `products` table determine the commercial presentation:
- **`In Stock`**: $\text{stock} > 5$ units. Customer can purchase up to available quantity.
- **`Low Stock`**: $1 \le \text{stock} \le 5$ units. Visual alert badge displayed: `⚡ Only X units remaining!`.
- **`Out of Stock`**: $\text{stock} = 0$ units. "Add to Cart" and "Buy Now" controls are disabled client-side and rejected with HTTP 400 server-side.

#### 1.2 Concurrency & Atomic Decrements
Checkout utilizes strict atomic decrements:
```sql
UPDATE products 
SET stock = stock - ? 
WHERE id = ? AND stock >= ?
```
If concurrent checkouts reduce the available stock below the requested quantity, the query affects 0 rows, prompting an immediate transaction rollback with:
`Insufficient stock for '{title}' due to concurrent checkout demand.`

---

### 2. Promotions & Coupon Rules Engine

Promotional discounts are validated via `CouponService.validate_coupon(code, cart_subtotal)`:

1. **Existence & Case-Insensitive Matching**: Coupon code is trimmed and capitalized (`WELCOME10`).
2. **Active Status**: Confirms `is_active == 1`.
3. **Usage Limit**: Verifies `usage_count < usage_limit`.
4. **Minimum Order Spend**: Enforces `cart_subtotal >= min_order_amount`. If not met, returns clear user message (e.g. `Coupon 'SAVE20' requires a minimum order amount of ₹2,000.00.`).
5. **Discount Calculation**:
   - `PERCENTAGE`: Calculates `cart_subtotal * (discount_value / 100.0)`. Caps at `max_discount_amount` if configured.
   - `FIXED`: Flat discount deducted, up to `cart_subtotal`.
6. **Usage Counter Recording**: Incremented during transactional checkout via `CouponService.record_coupon_usage(code)`.

---

### 3. Administrator Inventory Controls
Store administrators can update stock levels at any time via `POST /api/shop/admin/products/{id}/stock`:
- Enforces non-negative values (`stock >= 0`).
- Inserts structured audit records into `admin_audit_logs`:
  `admin_email='admin@shopsphere.com', action='UPDATE_STOCK', target_entity='Product #X', details='Updated stock to Y'`.
