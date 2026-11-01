import os
import sys
import unittest
import sqlite3

# Ensure repository root is on Python path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from shopsphere.database import init_db, seed_data, get_db_connection, hash_password, verify_password
from shopsphere.services import (
    ProductService, CartService, WishlistService,
    OrderService, UserService, AdminService
)
from shopsphere.autoheal_engine import AutoHealDemoEngine, SIMULATE_CART_BUG


class TestShopSphereCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_data()

    def test_catalog_seed_and_list(self):
        result = ProductService.list_products()
        self.assertGreater(result["total"], 0)
        self.assertGreater(len(result["products"]), 0)

    def test_product_search_by_query(self):
        res = ProductService.list_products(q="iPhone")
        self.assertGreater(res["total"], 0)
        for p in res["products"]:
            self.assertIn("iphone", p["title"].lower())

    def test_product_filter_by_category(self):
        res = ProductService.list_products(category="audio")
        self.assertGreater(res["total"], 0)
        for p in res["products"]:
            self.assertEqual(p["category"], "audio")

    def test_product_filter_by_price_range(self):
        res = ProductService.list_products(min_price=20000.0, max_price=50000.0)
        for p in res["products"]:
            self.assertGreaterEqual(p["price"], 20000.0)
            self.assertLessEqual(p["price"], 50000.0)

    def test_product_sorting(self):
        res_asc = ProductService.list_products(sort_by="price_asc")
        prices = [p["price"] for p in res_asc["products"]]
        self.assertEqual(prices, sorted(prices))


class TestShopSphereCartAndFinancialInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_data()

    def setUp(self):
        self.session_id = "test_cart_session_123"
        CartService.clear_cart(self.session_id)

    def tearDown(self):
        CartService.clear_cart(self.session_id)

    def test_cart_totals_calculation_delivery_rules(self):
        # 1. Order below ₹500 should incur ₹40 delivery fee
        items_under_500 = [{"price": 300.0, "original_price": 400.0, "quantity": 1}]
        totals_small = CartService.calculate_cart_totals(items_under_500)
        self.assertEqual(totals_small["subtotal"], 300.0)
        self.assertEqual(totals_small["delivery_fee"], 40.0)
        self.assertEqual(totals_small["final_total"], 340.0)
        self.assertEqual(totals_small["discount"], 100.0)

        # 2. Order above ₹500 should qualify for FREE delivery
        items_over_500 = [{"price": 1200.0, "original_price": 1500.0, "quantity": 1}]
        totals_large = CartService.calculate_cart_totals(items_over_500)
        self.assertEqual(totals_large["subtotal"], 1200.0)
        self.assertEqual(totals_large["delivery_fee"], 0.0)
        self.assertEqual(totals_large["final_total"], 1200.0)

    def test_add_to_cart_and_quantity_controls(self):
        products = ProductService.list_products()["products"]
        prod = products[0]

        # Add 2 items
        cart = CartService.add_to_cart(self.session_id, prod["id"], 2)
        self.assertEqual(cart["total_items"], 2)
        self.assertEqual(len(cart["items"]), 1)

        # Update to 3 items
        cart = CartService.update_quantity(self.session_id, prod["id"], 3)
        self.assertEqual(cart["total_items"], 3)

        # Remove product
        cart = CartService.remove_from_cart(self.session_id, prod["id"])
        self.assertEqual(cart["total_items"], 0)
        self.assertEqual(len(cart["items"]), 0)

    def test_stock_limit_enforcement(self):
        products = ProductService.list_products()["products"]
        prod = products[0]
        stock = prod["stock"]

        # Requesting more than available stock should cap at stock
        cart = CartService.add_to_cart(self.session_id, prod["id"], stock + 100)
        self.assertLessEqual(cart["total_items"], stock)


class TestShopSphereOrdersAndInventory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_data()

    def setUp(self):
        self.session_id = "test_order_session_456"
        CartService.clear_cart(self.session_id)

    def tearDown(self):
        CartService.clear_cart(self.session_id)

    def test_checkout_decrements_inventory_and_generates_order_ref(self):
        products = ProductService.list_products()["products"]
        prod = products[0]
        initial_stock = prod["stock"]
        self.assertGreater(initial_stock, 2)

        # Add 2 items to cart
        CartService.add_to_cart(self.session_id, prod["id"], 2)

        # Place order
        order = OrderService.checkout(
            user_or_session_id=self.session_id,
            customer_name="Test Customer",
            customer_email="test.customer@example.com",
            customer_phone="+91 99999 88888",
            shipping_address="123 Tech Boulevard",
            city="Bengaluru",
            pincode="560100",
            payment_method="UPI / QR Code"
        )

        self.assertTrue(order["order_ref"].startswith("ORD-2026-"))
        self.assertEqual(order["order_status"], "PLACED")
        self.assertEqual(len(order["items"]), 1)
        self.assertEqual(order["items"][0]["quantity"], 2)

        # Verify inventory was decremented in database
        updated_prod = ProductService.get_product(prod["id"])
        self.assertEqual(updated_prod["stock"], initial_stock - 2)

        # Cancel order and verify stock was restored
        cancelled_order = OrderService.cancel_order(order["id"])
        self.assertEqual(cancelled_order["order_status"], "CANCELLED")

        restored_prod = ProductService.get_product(prod["id"])
        self.assertEqual(restored_prod["stock"], initial_stock)


class TestShopSphereSecurityAndAuth(unittest.TestCase):
    def test_password_hashing_and_verification(self):
        raw_pw = "SecretP@ssw0rd2026"
        h1, s1 = hash_password(raw_pw)
        self.assertTrue(verify_password(raw_pw, h1, s1))
        self.assertFalse(verify_password("WrongPassword", h1, s1))

    def test_user_registration_and_login(self):
        email = f"user_{os.urandom(4).hex()}@example.com"
        user = UserService.register(
            name="Alice Wonder",
            email=email,
            password="SecurePassword123"
        )
        self.assertEqual(user["email"], email)
        self.assertEqual(user["role"], "customer")

        # Login
        logged_in = UserService.login(email, "SecurePassword123")
        self.assertEqual(logged_in["id"], user["id"])
        self.assertTrue(logged_in["token"].startswith("token_"))

        # Rejection of invalid password
        with self.assertRaises(ValueError):
            UserService.login(email, "BadPassword")


class TestAutoHealDemonstrationEngine(unittest.TestCase):
    def test_autoheal_11_step_lifecycle(self):
        # 1. Baseline should pass
        base_test = AutoHealDemoEngine.run_regression_test()
        self.assertTrue(base_test["passed"])

        # 2. Bug Injection
        AutoHealDemoEngine.inject_controlled_bug()
        reg_fail = AutoHealDemoEngine.run_regression_test()
        self.assertFalse(reg_fail["passed"])
        self.assertIn("AssertionError", reg_fail["error"])

        # 3. Root Cause Diagnosis
        diagnosis = AutoHealDemoEngine.diagnose_root_cause()
        self.assertTrue(diagnosis["root_cause_found"])
        self.assertIn("CartService", diagnosis["file"])

        # 4. Surgical AutoHeal Patch
        patch = AutoHealDemoEngine.apply_autoheal_patch()
        self.assertEqual(patch["status"], "HEALED")

        # 5. Regression Re-verification
        reg_pass = AutoHealDemoEngine.run_regression_test()
        self.assertTrue(reg_pass["passed"])


class TestShopSphereAdminRBAC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_data()

    def test_admin_requires_authentication(self):
        from fastapi import HTTPException
        from shopsphere.api import require_admin_user

        # 1. No authorization header -> 401
        with self.assertRaises(HTTPException) as ctx:
            require_admin_user(authorization=None)
        self.assertEqual(ctx.exception.status_code, 401)

        # 2. Old backdoor token must be rejected -> 401
        with self.assertRaises(HTTPException) as ctx:
            require_admin_user(authorization="Bearer token_admin_shopsphere_secret")
        self.assertEqual(ctx.exception.status_code, 401)

        # 3. Customer token cannot access admin -> 403
        customer = UserService.login("rahul.shopper@example.com", "Demo@123")
        with self.assertRaises(HTTPException) as ctx:
            require_admin_user(authorization=f"Bearer {customer['token']}")
        self.assertEqual(ctx.exception.status_code, 403)

        # 4. Valid admin login token -> Allowed
        admin = UserService.login("admin@shopsphere.com", "Admin@123")
        user = require_admin_user(authorization=f"Bearer {admin['token']}")
        self.assertEqual(user["email"], "admin@shopsphere.com")
        self.assertEqual(user["role"], "admin")


if __name__ == "__main__":
    unittest.main()
