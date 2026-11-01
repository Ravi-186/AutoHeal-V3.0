# Admin E-Commerce Portal Architecture
## Phase 9: Executive Metrics, RBAC, Catalog Controls & Fulfillment Management

### 1. Overview
The ShopSphere Admin Dashboard provides store managers and operations teams with real-time visibility into sales metrics, inventory levels, order fulfillment, and promotional campaigns.

Access is strictly protected by `require_admin_user`, enforcing server-side role verification (`role == 'admin'`).

---

### 2. Executive Sales & Operations KPIs
Metrics are computed dynamically from actual database records via `AdminService.get_dashboard_metrics()`:

1. **Total Revenue**: $\sum \text{total\_amount}$ for all orders where `order_status != 'CANCELLED'`.
2. **Total Orders**: Count of all customer orders in the system.
3. **Catalog Items**: Total active products in catalog.
4. **Out of Stock**: Count of products with $\text{stock} = 0$.
5. **Low Stock Count**: Count of products with $1 \le \text{stock} \le 5$.
6. **Active Coupons**: Count of promotional coupons currently active.
7. **Total Customers**: Count of registered shoppers.
8. **Total Reviews**: Count of verified customer reviews submitted.

---

### 3. Administrative Workflows

#### 3.1 Inventory Management
- **Endpoint**: `POST /api/shop/admin/products/{id}/stock`
- **Payload**: `{"stock": 42}`
- **Operation**: Updates available inventory and records an entry in `admin_audit_logs`.

#### 3.2 Order Fulfillment Pipeline
- **Endpoint**: `POST /api/shop/admin/orders/{id}/status`
- **Payload**: `{"status": "SHIPPED"}`
- **Permitted Transitions**: `PLACED` $\rightarrow$ `PROCESSING` $\rightarrow$ `SHIPPED` $\rightarrow$ `DELIVERED` or `CANCELLED`.
- **Audit**: Logs action to `admin_audit_logs`.

#### 3.3 Coupon Administration
- **Endpoints**: `GET /api/shop/admin/coupons`, `POST /api/shop/admin/coupons`
- **Payload**: `CouponCreateRequest` (code, discount type, value, minimum order threshold, maximum discount cap, usage limit).
- **Operation**: Upserts into `coupons` table.

#### 3.4 Customer Roster
- **Endpoint**: `GET /api/shop/admin/customers`
- **Aggregation**: Queries `users` joined with `orders` to display order counts and total customer lifetime value (CLV).
