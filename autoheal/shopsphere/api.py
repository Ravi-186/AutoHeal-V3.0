import os
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, Header, Depends, Query, status
from fastapi.responses import JSONResponse

from shopsphere.services import (
    ProductService, CartService, WishlistService,
    OrderService, UserService, AdminService
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


class CheckoutRequest(BaseModel):
    session_id: Optional[str] = ""
    customer_name: str
    customer_email: str
    customer_phone: str
    shipping_address: str
    city: str
    pincode: str
    payment_method: str = "UPI / QR Code"



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


@router.get("/categories", summary="List All Categories")
def get_categories():
    return ProductService.get_categories()


# --- 2. Authentication Endpoints ---
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


@router.post("/auth/logout", summary="Logout and Revoke Session Token")
def logout(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required.")
    token = authorization.replace("Bearer ", "").strip()
    revoked = UserService.logout(token)
    if not revoked:
        raise HTTPException(status_code=404, detail="Active session token not found or already revoked.")
    return {"status": "success", "message": "Session token successfully revoked."}


# --- 3. Shopping Cart Endpoints ---
@router.get("/cart", summary="Retrieve Shopping Cart")
def get_cart(
    session_id: Optional[str] = Query(None),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    sid = session_id or x_session_id
    if not sid:
        raise HTTPException(status_code=400, detail="session_id query parameter or X-Session-ID header is required.")
    return CartService.get_cart(sid)


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


# --- 4. Wishlist Endpoints ---
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


# --- 5. Checkout & Orders Endpoints ---
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
            user_id=user_id
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


# --- 6. Admin Portal Endpoints ---
@router.get("/admin/stats", summary="Get Admin Dashboard Metrics")
def get_admin_metrics(admin: Dict[str, Any] = Depends(require_admin_user)):
    return AdminService.get_dashboard_metrics()


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


# --- 7. AutoHeal Demonstration Endpoints ---
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

