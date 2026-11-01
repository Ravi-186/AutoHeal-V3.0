"""
ShopSphere Premium E-Commerce Test Suite (Phase 9)
Validates complete full-stack consumer e-commerce functionality,
database models, transactional checkout, coupon promotions, verified reviews,
customer profiles, notifications, admin RBAC controls, and AutoHeal security integration.
"""

import pytest
import sqlite3
from fastapi.testclient import TestClient
from server import app
from shopsphere.services import (
    ProductService, CartService, WishlistService,
    OrderService, UserService, AdminService,
    CouponService, ReviewService, NotificationService
)
from shopsphere.database import get_db_connection, seed_data

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    seed_data()
    from src.appsec.middleware import AppSecProtectionMiddleware
    AppSecProtectionMiddleware._rate_tracker.clear()
    with get_db_connection() as conn:
        conn.cursor().execute("DELETE FROM blocked_clients WHERE client_ip IN ('testclient', '127.0.0.1')")
        conn.commit()
    yield
    AppSecProtectionMiddleware._rate_tracker.clear()
    with get_db_connection() as conn:
        conn.cursor().execute("DELETE FROM blocked_clients WHERE client_ip IN ('testclient', '127.0.0.1')")
        conn.commit()


# =====================================================================
# 1. CATALOG DISCOVERY & FILTERING TESTS
# =====================================================================
def test_catalog_listing_and_filtering():
    """Tests product listing with category, pricing, and sorting."""
    # List all
    res = client.get("/api/shop/products")
    assert res.status_code == 200
    data = res.json()
    assert "products" in data
    assert data["total"] >= 14
    assert len(data["products"]) > 0

    # Filter by category
    res_cat = client.get("/api/shop/products?category=electronics")
    assert res_cat.status_code == 200
    data_cat = res_cat.json()
    for p in data_cat["products"]:
        assert p["category"].lower() == "electronics"

    # Search by keyword
    res_search = client.get("/api/shop/products?q=MacBook")
    assert res_search.status_code == 200
    data_search = res_search.json()
    assert len(data_search["products"]) >= 1
    assert "MacBook" in data_search["products"][0]["title"]


def test_product_detail_retrieval():
    """Tests retrieving full product details and specifications."""
    res = client.get("/api/shop/products/1")
    assert res.status_code == 200
    p = res.json()
    assert p["id"] == 1
    assert "title" in p and len(p["title"]) > 0
    assert p["price"] > 0
    assert p["stock"] > 0
    assert "specs" in p
    assert isinstance(p["specs"], dict)

    # 404 for non-existent product
    res_non = client.get("/api/shop/products/99999")
    assert res_non.status_code == 404


# =====================================================================
# 2. VERIFIED REVIEWS & RATINGS TESTS
# =====================================================================
def test_product_reviews_workflow():
    """Tests retrieving reviews, adding a review, and recalculating product aggregate rating."""
    product_id = 2  # iPhone 15 Pro
    # 1. Get initial reviews
    res_init = client.get(f"/api/shop/products/{product_id}/reviews")
    assert res_init.status_code == 200
    init_data = res_init.json()
    initial_count = init_data["total_reviews"]

    # 2. Add review
    review_payload = {
        "rating": 5,
        "headline": "Superb Build Quality & Camera",
        "comment": "The titanium finish feels incredible and the 5x telephoto camera is top tier.",
        "author_name": "Arjun Singhania"
    }
    res_add = client.post(f"/api/shop/products/{product_id}/reviews", json=review_payload)
    assert res_add.status_code == 200
    added = res_add.json()
    assert added["rating"] == 5
    assert added["headline"] == review_payload["headline"]

    # 3. Verify updated aggregate rating
    res_after = client.get(f"/api/shop/products/{product_id}/reviews")
    assert res_after.status_code == 200
    after_data = res_after.json()
    assert after_data["total_reviews"] == initial_count + 1
    assert after_data["distribution"]["5"] >= 1

    # 4. Verify product model updated review_count
    prod = client.get(f"/api/shop/products/{product_id}").json()
    assert prod["review_count"] == initial_count + 1


def test_review_input_validation():
    """Tests validation of ratings (1 to 5) and required review fields."""
    res_invalid_rating = client.post("/api/shop/products/1/reviews", json={
        "rating": 6,  # Invalid: > 5
        "headline": "Too high",
        "comment": "Great product"
    })
    assert res_invalid_rating.status_code == 422


# =====================================================================
# 3. PROMOTIONAL COUPONS TESTS
# =====================================================================
def test_coupon_validation_and_discounts():
    """Tests validating coupons, minimum order limits, and discount calculation."""
    # WELCOME10: 10% off
    res_w10 = client.post("/api/shop/coupons/validate", json={"code": "WELCOME10", "order_subtotal": 1000.0})
    assert res_w10.status_code == 200
    d_w10 = res_w10.json()
    assert d_w10["valid"] is True
    assert d_w10["discount_amount"] == 100.0

    # SAVE20: requires min ₹2000
    res_s20_fail = client.post("/api/shop/coupons/validate", json={"code": "SAVE20", "order_subtotal": 1500.0})
    assert res_s20_fail.status_code == 400
    assert "minimum order" in res_s20_fail.json()["detail"].lower()

    res_s20_pass = client.post("/api/shop/coupons/validate", json={"code": "SAVE20", "order_subtotal": 3000.0})
    assert res_s20_pass.status_code == 200
    assert res_s20_pass.json()["discount_amount"] == 600.0

    # Non-existent coupon
    res_invalid = client.post("/api/shop/coupons/validate", json={"code": "FAKECODE99", "order_subtotal": 5000.0})
    assert res_invalid.status_code == 400


# =====================================================================
# 4. SHOPPING CART & COUPON APPLICATION TESTS
# =====================================================================
def test_shopping_cart_workflow_and_coupon_application():
    """Tests adding items to cart, applying a promo coupon, and checking totals."""
    session_id = "test_cart_sess_9001"
    # 1. Clear cart
    client.post(f"/api/shop/cart/clear?session_id={session_id}")

    # Fetch product #5 details dynamically
    prod5 = client.get("/api/shop/products/5").json()
    p5_price = prod5["price"]

    # 2. Add product #5
    res_add = client.post("/api/shop/cart/add", json={
        "session_id": session_id,
        "product_id": 5,
        "quantity": 1
    })
    assert res_add.status_code == 200
    cart = res_add.json()["cart"]
    assert cart["total_items"] == 1
    assert cart["subtotal"] == p5_price
    assert cart["delivery_fee"] == 0.0  # Free delivery above ₹500

    # 3. Apply coupon SAVE20 (capped at max discount ₹1500)
    res_cp = client.post("/api/shop/cart/apply-coupon", json={
        "session_id": session_id,
        "coupon_code": "SAVE20"
    })
    assert res_cp.status_code == 200
    c_cart = res_cp.json()["cart"]
    assert c_cart["coupon_code"] == "SAVE20"
    expected_discount = min(3000.0, round(p5_price * 0.20, 2))
    assert c_cart["coupon_discount"] == expected_discount
    assert c_cart["final_total"] == round(p5_price - expected_discount, 2)

    # 4. Update quantity
    res_up = client.post("/api/shop/cart/update", json={
        "session_id": session_id,
        "product_id": 5,
        "quantity": 2
    })
    assert res_up.status_code == 200
    assert res_up.json()["cart"]["total_items"] == 2

    # 5. Remove item
    res_rm = client.post("/api/shop/cart/remove", json={
        "session_id": session_id,
        "product_id": 5
    })
    assert res_rm.status_code == 200
    assert res_rm.json()["cart"]["total_items"] == 0


def test_cart_stock_limit_enforcement():
    """Tests that a customer cannot add more items than physically available in stock."""
    prod = client.get("/api/shop/products/4").json()  # Dell XPS 15
    available_stock = prod["stock"]

    session_id = "test_stock_cap_sess"
    client.post(f"/api/shop/cart/clear?session_id={session_id}")

    # Attempt to add available_stock + 10 items
    res = client.post("/api/shop/cart/add", json={
        "session_id": session_id,
        "product_id": 4,
        "quantity": available_stock + 10
    })
    assert res.status_code == 200
    cart = res.json()["cart"]
    # Cart item quantity is automatically capped at available stock
    assert cart["items"][0]["quantity"] == available_stock


# =====================================================================
# 5. WISHLIST OPERATIONS TESTS
# =====================================================================
def test_wishlist_workflow():
    """Tests adding, toggling, listing, and moving items to cart."""
    session_id = "test_wishlist_sess_100"
    product_id = 6  # Bose QuietComfort Ultra

    # Toggle in
    res_in = client.post("/api/shop/wishlist/toggle", json={"session_id": session_id, "product_id": product_id})
    assert res_in.status_code == 200
    assert res_in.json()["in_wishlist"] is True

    # Move to cart
    res_move = client.post("/api/shop/wishlist/move-to-cart", json={"session_id": session_id, "product_id": product_id})
    assert res_move.status_code == 200
    d_move = res_move.json()
    assert any(it["product_id"] == product_id for it in d_move["cart"]["items"])
    assert not any(w["product_id"] == product_id for w in d_move["wishlist"])


# =====================================================================
# 6. TRANSACTIONAL CHECKOUT & INVENTORY ATOMICITY
# =====================================================================
def test_transactional_checkout_with_coupon_and_stock_decrement():
    """Tests end-to-end checkout, coupon recording, stock decrement, and notification creation."""
    session_id = "test_checkout_sess_2026"
    client.post(f"/api/shop/cart/clear?session_id={session_id}")

    # Check initial stock of Product #8 (Espresso Machine, stock=12)
    prod_before = client.get("/api/shop/products/8").json()
    stock_before = prod_before["stock"]

    # Add 2 units to cart
    client.post("/api/shop/cart/add", json={"session_id": session_id, "product_id": 8, "quantity": 2})

    # Checkout with coupon WELCOME10
    checkout_payload = {
        "session_id": session_id,
        "customer_name": "Deepika Padukone",
        "customer_email": "deepika.shopper@example.com",
        "customer_phone": "+91 99887 76655",
        "shipping_address": "Penthouse 12, Highline Towers",
        "city": "Mumbai",
        "pincode": "400001",
        "payment_method": "UPI / QR Code",
        "coupon_code": "WELCOME10"
    }

    res_chk = client.post("/api/shop/checkout", json=checkout_payload)
    assert res_chk.status_code == 200
    chk_data = res_chk.json()
    assert chk_data["status"] == "success"
    order = chk_data["order"]
    assert order["order_ref"].startswith("ORD-2026-")
    assert order["coupon_code"] == "WELCOME10"
    assert order["coupon_discount"] > 0
    assert order["payment_status"] == "COMPLETED_SIMULATED"
    assert order["order_status"] == "PLACED"

    # Verify inventory was atomically decremented by 2
    prod_after = client.get("/api/shop/products/8").json()
    assert prod_after["stock"] == stock_before - 2

    # Verify cart is now empty
    cart_after = client.get(f"/api/shop/cart?session_id={session_id}").json()
    assert cart_after["total_items"] == 0

    # Verify notification created
    res_notif = client.get(f"/api/shop/notifications?email={checkout_payload['customer_email']}")
    assert res_notif.status_code == 200
    notifs = res_notif.json()
    assert len(notifs) >= 1
    assert order["order_ref"] in notifs[0]["title"]


def test_order_cancellation_and_automatic_stock_restoration():
    """Tests cancelling an order and verifying that reserved stock is restored."""
    session_id = "test_cancel_sess_404"
    client.post(f"/api/shop/cart/clear?session_id={session_id}")

    # Add 1 unit of product #9
    prod_init = client.get("/api/shop/products/9").json()
    init_stock = prod_init["stock"]

    client.post("/api/shop/cart/add", json={"session_id": session_id, "product_id": 9, "quantity": 1})

    res_chk = client.post("/api/shop/checkout", json={
        "session_id": session_id,
        "customer_name": "Test User",
        "customer_email": "cancel.test@example.com",
        "customer_phone": "9999999999",
        "shipping_address": "Test St",
        "city": "Bengaluru",
        "pincode": "560001",
        "payment_method": "Cash on Delivery"
    })
    order_id = res_chk.json()["order"]["id"]

    # Verify stock decremented
    assert client.get("/api/shop/products/9").json()["stock"] == init_stock - 1

    # Cancel order
    res_cancel = client.post(f"/api/shop/orders/{order_id}/cancel")
    assert res_cancel.status_code == 200
    cancelled_order = res_cancel.json()["order"]
    assert cancelled_order["order_status"] == "CANCELLED"
    assert cancelled_order["payment_status"] == "REFUNDED_SIMULATED"

    # Verify stock restored!
    assert client.get("/api/shop/products/9").json()["stock"] == init_stock


# =====================================================================
# 7. CUSTOMER PROFILE & IN-APP NOTIFICATIONS
# =====================================================================
def test_customer_profile_update():
    """Tests updating a customer contact and delivery address profile."""
    # Login customer
    res_login = client.post("/api/shop/auth/login", json={
        "email": "rahul.shopper@example.com",
        "password": "Demo@123"
    })
    token = res_login.json()["user"]["token"]

    # Update profile
    res_update = client.put("/api/shop/auth/profile", headers={"Authorization": f"Bearer {token}"}, json={
        "name": "Rahul Sharma (Updated)",
        "phone": "+91 91234 56789",
        "address": "Villa 108, Palm Meadows",
        "city": "Bengaluru",
        "pincode": "560066"
    })
    assert res_update.status_code == 200
    updated_user = res_update.json()["user"]
    assert updated_user["name"] == "Rahul Sharma (Updated)"
    assert updated_user["phone"] == "+91 91234 56789"
    assert updated_user["address"] == "Villa 108, Palm Meadows"


def test_customer_notifications_flow():
    """Tests retrieving and marking in-app notifications as read."""
    # Create notification
    notif = NotificationService.create_notification(
        title="Delivery Dispatched",
        message="Your package has left the Bengaluru fulfillment warehouse.",
        notification_type="ORDER_UPDATE",
        email="rahul.shopper@example.com"
    )
    notif_id = notif["id"]

    # Mark as read
    res_read = client.post(f"/api/shop/notifications/{notif_id}/read")
    assert res_read.status_code == 200
    assert res_read.json()["status"] == "success"

    # Mark all read
    res_all = client.post("/api/shop/notifications/read-all?email=rahul.shopper@example.com")
    assert res_all.status_code == 200


# =====================================================================
# 8. ADMIN RBAC & E-COMMERCE MANAGEMENT CONTROLS
# =====================================================================
def test_admin_rbac_and_management_endpoints():
    """Tests that unauthenticated and customer accounts cannot access admin endpoints, while admin can."""
    # 1. Unauthenticated request to admin stats
    res_unauth = client.get("/api/shop/admin/stats")
    assert res_unauth.status_code in [401, 403]

    # 2. Customer user attempting admin access
    res_cust = client.post("/api/shop/auth/login", json={"email": "rahul.shopper@example.com", "password": "Demo@123"})
    cust_token = res_cust.json()["user"]["token"]
    res_forbidden = client.get("/api/shop/admin/stats", headers={"Authorization": f"Bearer {cust_token}"})
    assert res_forbidden.status_code in [401, 403]

    # 3. Valid Admin access
    res_admin = client.post("/api/shop/auth/login", json={"email": "admin@shopsphere.com", "password": "Admin@123"})
    admin_token = res_admin.json()["user"]["token"]

    res_stats = client.get("/api/shop/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert "total_revenue" in stats
    assert "total_orders" in stats
    assert "total_products" in stats

    # 4. Admin updates inventory stock
    res_stock = client.post("/api/shop/admin/products/1/stock", headers={"Authorization": f"Bearer {admin_token}"}, json={"stock": 42})
    assert res_stock.status_code == 200
    assert res_stock.json()["product"]["stock"] == 42

    # 5. Admin lists orders
    res_orders = client.get("/api/shop/admin/orders", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_orders.status_code == 200
    assert isinstance(res_orders.json(), list)

    # 6. Admin creates a new promo coupon
    res_cp = client.post("/api/shop/admin/coupons", headers={"Authorization": f"Bearer {admin_token}"}, json={
        "code": "SUPERVIP30",
        "discount_type": "PERCENTAGE",
        "discount_value": 30.0,
        "min_order_amount": 5000.0,
        "max_discount_amount": 2500.0,
        "description": "30% off for executive members on orders above ₹5,000",
        "is_active": 1,
        "usage_limit": 500
    })
    assert res_cp.status_code == 200
    assert res_cp.json()["code"] == "SUPERVIP30"


# =====================================================================
# 9. AUTOHEAL ENGINE & SECURITY INTEGRATION
# =====================================================================
def test_shopsphere_html_route():
    """Validates that the main /shop storefront route serves the premium template."""
    res = client.get("/shop")
    assert res.status_code == 200
    assert "ShopSphere | Premium Modern Marketplace" in res.text
    assert "AutoHeal Sentinel" in res.text
    assert "Multi-Step Checkout" in res.text


def test_autoheal_demonstration_endpoints():
    """Validates that AutoHeal autonomous diagnostic and repair endpoints respond correctly."""
    # Status
    res_st = client.get("/api/shop/autoheal/status")
    assert res_st.status_code == 200
    assert "bug_injected" in res_st.json()

    # Regression test
    res_reg = client.post("/api/shop/autoheal/regression-test")
    assert res_reg.status_code == 200
    assert res_reg.json()["passed"] is True

    # Full demo
    res_demo = client.post("/api/shop/autoheal/run-full-demo")
    assert res_demo.status_code == 200
    demo_d = res_demo.json()
    assert demo_d.get("completed_successfully") is True or demo_d.get("status") == "SUCCESS"
    assert len(demo_d["steps"]) == 11
