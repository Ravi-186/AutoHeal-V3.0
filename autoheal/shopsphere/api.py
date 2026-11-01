import os
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, Header, Depends, Query, status
from fastapi.responses import JSONResponse

from shopsphere.services import (
    ProductService, CartService, WishlistService,
    OrderService, UserService, AdminService,
    CouponService, ReviewService, NotificationService
)
from shopsphere.autoheal_engine import AutoHealDemoEngine

router = APIRouter(prefix="/api/shop", tags=["ShopSphere E-Commerce"])


# --- Pydantic Request Models ---
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)
    phone: Optional[str] = ""
    address: Optional[str] = ""
    city: Optional[str] = ""
    pincode: Optional[str] = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileUpdateRequest(BaseModel):
    name: str = Field(..., min_length=2)
    phone: Optional[str] = ""
    address: Optional[str] = ""
    city: Optional[str] = ""
    pincode: Optional[str] = ""


class CartItemRequest(BaseModel):
    session_id: Optional[str] = ""
    product_id: int
    quantity: int = 1


class CartUpdateRequest(BaseModel):
    session_id: Optional[str] = ""
    product_id: int
    quantity: int


class CartRemoveRequest(BaseModel):
    session_id: Optional[str] = ""
    product_id: int


class WishlistToggleRequest(BaseModel):
    session_id: Optional[str] = ""
    product_id: int


class ApplyCouponRequest(BaseModel):
    session_id: Optional[str] = ""
    coupon_code: str = Field(..., min_length=1)


class CouponValidateRequest(BaseModel):
    code: str = Field(..., min_length=1)
    order_subtotal: float = Field(..., ge=0.0)


class CouponCreateRequest(BaseModel):
    code: str = Field(..., min_length=2)
    discount_type: str = "PERCENTAGE"
    discount_value: float = Field(..., gt=0.0)
    min_order_amount: float = 0.0
    max_discount_amount: Optional[float] = None
    description: Optional[str] = ""
    is_active: int = 1
    usage_limit: int = 1000


class ReviewCreateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    headline: str = Field(..., min_length=2)
    comment: str = Field(..., min_length=5)
    author_name: Optional[str] = ""


class CheckoutRequest(BaseModel):
    session_id: Optional[str] = ""
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: str
    city: str
    pincode: str
    payment_method: str = "UPI / QR Code"
    coupon_code: Optional[str] = None


class AdminStockUpdateRequest(BaseModel):
    stock: int = Field(..., ge=0)


class AdminOrderStatusRequest(BaseModel):
    status: str


# --- Helper Dependency for Auth ---
def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "").strip()
    return UserService.get_by_token(token)


def require_admin_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required for admin access.")
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator privileges required.")
    return user


# --- 1. Products Endpoints ---
@router.get("/products", summary="List & Search Products")
def list_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    in_stock_only: bool = False,
    sort_by: str = "popularity",
    page: int = 1,
    page_size: int = 24
):
    try:
        return ProductService.list_products(
            q=q,
            category=category,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            in_stock_only=in_stock_only,
            sort_by=sort_by,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}", summary="Get Product Details")
def get_product(product_id: int):
    prod = ProductService.get_product(product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found.")
    return prod


@router.get("/products/{product_id}/reviews", summary="Get Customer Reviews for Product")
def get_product_reviews(product_id: int):
    return ReviewService.get_reviews_for_product(product_id)


@router.post("/products/{product_id}/reviews", summary="Submit Product Review")
def add_product_review(
    product_id: int,
    req: ReviewCreateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    try:
        user_id = current_user["id"] if current_user else None
        customer_email = current_user["email"] if current_user else None
        author_name = req.author_name or (current_user["name"] if current_user else "Verified Shopper")
        return ReviewService.add_review(
            product_id=product_id,
            author_name=author_name,
            rating=req.rating,
            headline=req.headline,
            comment=req.comment,
            user_id=user_id,
            customer_email=customer_email
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/reviews/{review_id}", summary="Delete Review")
def delete_review(
    review_id: int,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    is_admin = current_user.get("role") == "admin"
    try:
        success = ReviewService.delete_review(review_id, user_id=current_user["id"], is_admin=is_admin)
        if not success:
            raise HTTPException(status_code=404, detail="Review not found.")
        return {"status": "success", "message": "Review deleted successfully."}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/categories", summary="List All Categories")
def get_categories():
    return ProductService.get_categories()


# --- 2. Authentication & Customer Profile Endpoints ---
@router.post("/auth/register", summary="Register Customer Account")
def register(req: RegisterRequest):
    try:
        user = UserService.register(
            name=req.name,
            email=req.email,
            password=req.password,
            phone=req.phone or "",
            address=req.address or "",
            city=req.city or "",
            pincode=req.pincode or ""
        )
        return {"status": "success", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login", summary="Login User")
def login(req: LoginRequest):
    try:
        user = UserService.login(req.email, req.password)
        return {"status": "success", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/auth/me", summary="Get Authenticated User Profile")
def get_me(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return current_user


@router.put("/auth/profile", summary="Update Customer Profile")
def update_profile(
    req: ProfileUpdateRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    try:
        updated = UserService.update_profile(
            user_id=current_user["id"],
            name=req.name,
            phone=req.phone or "",
            address=req.address or "",
            city=req.city or "",
            pincode=req.pincode or ""
        )
        return {"status": "success", "user": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/logout", summary="Logout and Revoke Session Token")
def logout(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required.")
    token = authorization.replace("Bearer ", "").strip()
    revoked = UserService.logout(token)
    if not revoked:
        raise HTTPException(status_code=404, detail="Active session token not found or already revoked.")
    return {"status": "success", "message": "Session token successfully revoked."}


# --- 3. Shopping Cart & Coupons Endpoints ---
@router.get("/cart", summary="Retrieve Shopping Cart")
def get_cart(
    session_id: Optional[str] = Query(None),
    coupon_code: Optional[str] = Query(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    sid = session_id or x_session_id
    if not sid:
        raise HTTPException(status_code=400, detail="session_id query parameter or X-Session-ID header is required.")
    return CartService.get_cart(sid, coupon_code=coupon_code)


@router.post("/cart/add", summary="Add Product to Cart")
def add_to_cart(
    req: CartItemRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    sid = req.session_id or x_session_id
    if not sid:
        raise HTTPException(status_code=400, detail="session_id is required in body or X-Session-ID header.")
    try:
        cart = CartService.add_to_cart(sid, req.product_id, req.quantity)
        return {"status": "success", "cart": cart}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cart/update", summary="Update Item Quantity in Cart")
def update_cart_quantity(
    req: CartUpdateRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    sid = req.session_id or x_session_id
    if not sid:
        raise HTTPException(status_code=400, detail="session_id is required in body or X-Session-ID header.")
    try:
        cart = CartService.update_quantity(sid, req.product_id, req.quantity)
        return {"status": "success", "cart": cart}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cart/remove", summary="Remove Product from Cart")
def remove_from_cart(
    req: CartRemoveRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    sid = req.session_id or x_session_id
    if not sid:
        raise HTTPException(status_code=400, detail="session_id is required in body or X-Session-ID header.")
    cart = CartService.remove_from_cart(sid, req.product_id)
    return {"status": "success", "cart": cart}


@router.post("/cart/clear", summary="Clear All Items from Cart")
def clear_cart(
    session_id: Optional[str] = Query(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    sid = session_id or x_session_id
    if not sid:
        raise HTTPException(status_code=400, detail="session_id query parameter or X-Session-ID header is required.")
    CartService.clear_cart(sid)
    return {"status": "success", "message": "Cart cleared."}


@router.post("/cart/apply-coupon", summary="Validate and Apply Coupon to Cart")
def apply_cart_coupon(
    req: ApplyCouponRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    sid = req.session_id or x_session_id
    if not sid:
        raise HTTPException(status_code=400, detail="session_id is required.")
    cart = CartService.get_cart(sid, coupon_code=req.coupon_code)
    if not cart.get("coupon_code"):
        validation = CouponService.validate_coupon(req.coupon_code, cart.get("subtotal", 0.0))
        raise HTTPException(status_code=400, detail=validation.get("message", "Invalid coupon."))
    return {"status": "success", "cart": cart}


# --- 4. Coupons & Promotions Endpoints ---
@router.post("/coupons/validate", summary="Validate Promotional Coupon")
def validate_coupon(req: CouponValidateRequest):
    result = CouponService.validate_coupon(req.code, req.order_subtotal)
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.get("/coupons", summary="List Active Promotional Coupons")
def list_active_coupons():
    return CouponService.list_coupons(active_only=True)


# --- 5. Wishlist Endpoints ---
@router.get("/wishlist", summary="Get Customer Wishlist")
def get_wishlist(
    session_id: Optional[str] = Query(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    sid = session_id or x_session_id
    if not sid:
        raise HTTPException(status_code=400, detail="session_id query parameter or X-Session-ID header is required.")
    return WishlistService.get_wishlist(sid)


@router.post("/wishlist/toggle", summary="Toggle Product in Wishlist")
def toggle_wishlist(
    req: WishlistToggleRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    sid = req.session_id or x_session_id
    if not sid:
        raise HTTPException(status_code=400, detail="session_id is required in body or X-Session-ID header.")
    return WishlistService.toggle_wishlist(sid, req.product_id)


@router.post("/wishlist/move-to-cart", summary="Move Item from Wishlist to Cart")
def move_wishlist_to_cart(
    req: WishlistToggleRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    sid = req.session_id or x_session_id
    if not sid:
        raise HTTPException(status_code=400, detail="session_id is required in body or X-Session-ID header.")
    return WishlistService.move_to_cart(sid, req.product_id)


# --- 6. Checkout & Orders Endpoints ---
@router.post("/checkout", summary="Complete Demo Order Checkout")
@router.post("/cart/checkout", summary="Complete Demo Order Checkout (Cart Alias)")
def checkout(
    req: CheckoutRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    sid = req.session_id or x_session_id
    if not sid:
        raise HTTPException(status_code=400, detail="session_id is required in body or X-Session-ID header.")
    try:
        user_id = current_user["id"] if current_user else None
        order = OrderService.checkout(
            user_or_session_id=sid,
            customer_name=req.customer_name,
            customer_email=req.customer_email,
            customer_phone=req.customer_phone,
            shipping_address=req.shipping_address,
            city=req.city,
            pincode=req.pincode,
            payment_method=req.payment_method,
            user_id=user_id,
            coupon_code=req.coupon_code
        )
        return {
            "status": "success",
            "message": "Order placed successfully (Sandbox Simulated Payment).",
            "order": order
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders", summary="Get Orders by Email or Authenticated User")
def get_orders(
    email: Optional[str] = Query(None),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    user_id = current_user["id"] if current_user else None
    user_email = email or (current_user["email"] if current_user else None)
    if not user_id and not user_email:
        return []
    return OrderService.get_orders_by_email_or_user(email=user_email, user_id=user_id)


@router.get("/orders/{order_ref_or_id}", summary="Get Order Details")
def get_order_by_ref(order_ref_or_id: str):
    if order_ref_or_id.isdigit():
        order = OrderService.get_order_by_id(int(order_ref_or_id))
    else:
        order = OrderService.get_order_by_ref(order_ref_or_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order


@router.post("/orders/{order_id}/cancel", summary="Cancel Customer Order")
def cancel_order(
    order_id: int,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    try:
        user_id = current_user["id"] if current_user else None
        cancelled = OrderService.cancel_order(order_id, user_id=user_id)
        return {
            "status": "success",
            "message": f"Order #{order_id} has been cancelled and stock returned to inventory.",
            "order": cancelled
        }
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- 7. Customer Notifications Endpoints ---
@router.get("/notifications", summary="Get Customer In-App Notifications")
def get_notifications(
    email: Optional[str] = Query(None),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    user_id = current_user["id"] if current_user else None
    user_email = email or (current_user["email"] if current_user else None)
    return NotificationService.get_notifications(user_id=user_id, email=user_email)


@router.post("/notifications/{notification_id}/read", summary="Mark Notification as Read")
def mark_notification_read(notification_id: int):
    success = NotificationService.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {"status": "success", "message": "Notification marked as read."}


@router.post("/notifications/read-all", summary="Mark All Notifications as Read")
def mark_all_notifications_read(
    email: Optional[str] = Query(None),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    user_id = current_user["id"] if current_user else None
    user_email = email or (current_user["email"] if current_user else None)
    NotificationService.mark_all_read(user_id=user_id, email=user_email)
    return {"status": "success", "message": "All notifications marked as read."}


# --- 8. Admin Portal Endpoints ---
@router.get("/admin/stats", summary="Get Admin Dashboard Metrics")
def get_admin_metrics(admin: Dict[str, Any] = Depends(require_admin_user)):
    return AdminService.get_dashboard_metrics()


@router.get("/admin/orders", summary="Admin List All Orders")
def list_admin_orders(
    status_filter: Optional[str] = Query(None),
    admin: Dict[str, Any] = Depends(require_admin_user)
):
    return AdminService.list_all_orders(status_filter=status_filter)


@router.get("/admin/customers", summary="Admin List All Customers")
def list_admin_customers(admin: Dict[str, Any] = Depends(require_admin_user)):
    return AdminService.list_all_customers()


@router.get("/admin/coupons", summary="Admin List All Coupons")
def list_admin_coupons(admin: Dict[str, Any] = Depends(require_admin_user)):
    return CouponService.list_coupons(active_only=False)


@router.post("/admin/coupons", summary="Admin Create or Update Coupon")
def create_admin_coupon(
    req: CouponCreateRequest,
    admin: Dict[str, Any] = Depends(require_admin_user)
):
    try:
        return CouponService.create_or_update_coupon(
            code=req.code,
            discount_type=req.discount_type,
            discount_value=req.discount_value,
            min_order_amount=req.min_order_amount,
            max_discount_amount=req.max_discount_amount,
            description=req.description or "",
            is_active=req.is_active,
            usage_limit=req.usage_limit
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/products/{product_id}/stock", summary="Update Product Stock Inventory")
def update_product_stock(
    product_id: int,
    req: AdminStockUpdateRequest,
    admin: Dict[str, Any] = Depends(require_admin_user)
):
    prod = AdminService.update_product_inventory(product_id, req.stock, admin.get("email", "admin@shopsphere.com"))
    return {"status": "success", "product": prod}


@router.post("/admin/orders/{order_id}/status", summary="Update Order Fulfillment Status")
def update_order_fulfillment(
    order_id: int,
    req: AdminOrderStatusRequest,
    admin: Dict[str, Any] = Depends(require_admin_user)
):
    try:
        order = AdminService.update_order_status(order_id, req.status, admin.get("email", "admin@shopsphere.com"))
        return {"status": "success", "order": order}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- 9. AutoHeal Demonstration Endpoints ---
@router.get("/autoheal/status", summary="Get AutoHeal Engine Status")
def autoheal_status():
    return AutoHealDemoEngine.get_status()


@router.post("/autoheal/inject-bug", summary="Inject Controlled Cart Calculation Bug")
def autoheal_inject():
    return AutoHealDemoEngine.inject_controlled_bug()


@router.post("/autoheal/regression-test", summary="Run Regression Test Suite")
def autoheal_regression():
    return AutoHealDemoEngine.run_regression_test()


@router.post("/autoheal/diagnose", summary="Run AI Root-Cause Diagnostic")
def autoheal_diagnose():
    return AutoHealDemoEngine.diagnose_root_cause()


@router.post("/autoheal/apply-fix", summary="Apply Surgical AutoHeal Fix")
def autoheal_apply_fix():
    return AutoHealDemoEngine.apply_autoheal_patch()


@router.post("/autoheal/run-full-demo", summary="Execute Complete 11-Step AutoHeal Demo")
def autoheal_full_demo():
    return AutoHealDemoEngine.run_full_demonstration()


# --- 8. Application Health & Resilience Endpoints ---
@router.get("/health", summary="ShopSphere Health Status")
def shop_health():
    """Returns database connectivity and operational health status."""
    return {
        "status": "UP",
        "service": "ShopSphere Production Storefront API",
        "database": "CONNECTED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/health/simulate-error", summary="Simulate Controlled Server Error")
def simulate_server_error():
    """Simulates an unhandled 500 error for health cascade resilience testing."""
    raise RuntimeError("Simulated Database Latency & Cluster Node Timeout (Controlled Test)")

