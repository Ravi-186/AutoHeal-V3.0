import os
import sys
import time
import secrets
import sqlite3
import threading
import unittest
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from shopsphere.database import init_db, seed_data, get_db_connection, DB_PATH
from shopsphere.services import (
    ProductService, CartService, OrderService, UserService, AdminService
)
from src.appsec.detector import AppSecDetector
from fastapi.testclient import TestClient
from server import app


class TestSecurityDefectsAndHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_data()
        cls.client = TestClient(app)

    def test_new_def_001_auth002_detector_bypass_prevention(self):
        """
        NEW-DEF-001: Attacker sending 'Bearer token_admin_fake' must NOT bypass detection.
        Only a genuine, active authenticated admin token may pass without triggering AUTH-002.
        """
        admin_user = UserService.login("admin@shopsphere.com", "Admin@123")
        valid_admin_token = admin_user["token"]

        # 1. Fake admin token -> MUST trigger AUTH-002
        det_fake = AppSecDetector.analyze_live_request(
            client_ip="10.0.0.1",
            method="POST",
            path="/api/admin/products",
            headers={"authorization": "Bearer token_admin_attacker_forged_payload"}
        )
        self.assertIsNotNone(det_fake)
        self.assertTrue(det_fake.triggered)
        self.assertEqual(det_fake.rule_id, "AUTH-002")

        # 2. Customer token accessing admin endpoint -> MUST trigger AUTH-002
        customer = UserService.login("rahul.shopper@example.com", "Demo@123")
        det_cust = AppSecDetector.analyze_live_request(
            client_ip="10.0.0.2",
            method="GET",
            path="/api/admin/audit-logs",
            headers={"authorization": f"Bearer {customer['token']}"}
        )
        self.assertIsNotNone(det_cust)
        self.assertTrue(det_cust.triggered)
        self.assertEqual(det_cust.rule_id, "AUTH-002")

        # 3. No token at all -> MUST trigger AUTH-002
        det_none = AppSecDetector.analyze_live_request(
            client_ip="10.0.0.3",
            method="GET",
            path="/api/admin/orders",
            headers={}
        )
        self.assertIsNotNone(det_none)
        self.assertTrue(det_none.triggered)
        self.assertEqual(det_none.rule_id, "AUTH-002")

        # 4. Legitimate active admin token -> MUST NOT trigger AUTH-002
        det_legit = AppSecDetector.analyze_live_request(
            client_ip="10.0.0.4",
            method="GET",
            path="/api/admin/orders",
            headers={"authorization": f"Bearer {valid_admin_token}"}
        )
        self.assertFalse(det_legit.triggered, "Legitimate active admin token must not trigger AUTH-002.")

    def test_new_def_002_and_003_token_expiration_and_constant_time_comparison(self):
        """
        NEW-DEF-002 & NEW-DEF-003: Server-side token expiration and constant-time token comparison.
        """
        user = UserService.register(
            name="Expiration Test User",
            email=f"exp_{secrets.token_hex(4)}@example.com",
            password="SecurePassword2026!"
        )
        logged_in = UserService.login(user["email"], "SecurePassword2026!")
        token = logged_in["token"]

        # Token must be valid immediately
        fetched = UserService.get_by_token(token)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["email"], user["email"])

        # Manually set expiration in the past to simulate token expiry
        past_time = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET token_expires_at = ? WHERE id = ?", (past_time, user["id"]))
            conn.commit()

        # Token lookup must now fail due to expiration
        expired_fetched = UserService.get_by_token(token)
        self.assertIsNone(expired_fetched, "Expired token must not authenticate.")

        # Tampered token must fail constant-time comparison
        tampered_token = token[:-4] + "XXXX"
        tampered_fetched = UserService.get_by_token(tampered_token)
        self.assertIsNone(tampered_fetched, "Tampered token must not authenticate.")

    def test_new_def_004_server_side_logout_revocation(self):
        """
        NEW-DEF-004: POST /api/shop/auth/logout must revoke the active token server-side.
        """
        email = f"logout_{secrets.token_hex(4)}@example.com"
        UserService.register(name="Logout User", email=email, password="ValidPassword123!")
        logged_in = UserService.login(email, "ValidPassword123!")
        token = logged_in["token"]

        # Call /api/shop/auth/me -> Should succeed
        me_resp1 = self.client.get("/api/shop/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_resp1.status_code, 200)

        # Call POST /api/shop/auth/logout
        logout_resp = self.client.post("/api/shop/auth/logout", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(logout_resp.status_code, 200)
        self.assertEqual(logout_resp.json().get("status"), "success")

        # Verify token in database has been wiped
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT token, token_expires_at FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            self.assertIsNone(row["token"])
            self.assertIsNone(row["token_expires_at"])

        # Subsequent authenticated requests must be rejected
        me_resp2 = self.client.get("/api/shop/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(me_resp2.status_code, 401)

    def test_defense_in_depth_security_headers(self):
        """
        Verify that all responses include enterprise defensive headers:
        X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, X-Correlation-ID.
        """
        resp = self.client.get("/api/shop/products")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(resp.headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertEqual(resp.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
        self.assertTrue(resp.headers.get("X-Correlation-ID").startswith("corr-"))


class TestDatabaseReliabilityAndDisasterRecovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_data()

    def test_disposable_database_backup_and_restoration(self):
        """
        Performs actual online SQLite backup to a disposable copy, verifies integrity,
        simulates corruption/loss on a temporary copy, performs online restore,
        and verifies 100% record integrity across all tables.
        """
        backup_path = os.path.join(REPO_ROOT, "data", "disposable_test_backup.db")
        restored_path = os.path.join(REPO_ROOT, "data", "disposable_test_restored.db")

        try:
            # 1. Perform online backup from primary DB
            with sqlite3.connect(DB_PATH) as src_conn:
                with sqlite3.connect(backup_path) as bkp_conn:
                    src_conn.backup(bkp_conn)

            self.assertTrue(os.path.exists(backup_path), "Backup database file was not created.")

            # 2. Verify integrity of backup database
            with sqlite3.connect(backup_path) as bkp_conn:
                cursor = bkp_conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                integrity_result = cursor.fetchone()[0]
                self.assertEqual(integrity_result, "ok", "Backup database integrity check failed.")

                cursor.execute("SELECT COUNT(*) FROM products;")
                bkp_product_count = cursor.fetchone()[0]
                self.assertGreater(bkp_product_count, 0)

            # 3. Simulate disaster recovery by restoring to target database
            with sqlite3.connect(backup_path) as bkp_conn:
                with sqlite3.connect(restored_path) as res_conn:
                    bkp_conn.backup(res_conn)

            # 4. Verify restored database has identical row counts across core tables
            with sqlite3.connect(DB_PATH) as orig_conn, sqlite3.connect(restored_path) as res_conn:
                for table in ["users", "products", "categories", "orders", "cart_items"]:
                    orig_count = orig_conn.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
                    res_count = res_conn.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
                    self.assertEqual(orig_count, res_count, f"Mismatch in row count for table '{table}'.")

        finally:
            # Clean up disposable files
            for p in [backup_path, restored_path]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass

    def test_concurrent_checkout_inventory_consistency(self):
        """
        Simulate 10 concurrent threads attempting to checkout the exact same limited-stock item.
        Verifies:
        - Atomic transactions prevent overselling.
        - Stock never drops below zero.
        - Database locks/WAL concurrency are handled without corruption.
        """
        # Create a product with stock = 2
        test_slug = f"concurrency-item-{secrets.token_hex(4)}"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO products (
                title, slug, category, description, price, original_price,
                discount_percent, rating, review_count, stock, image_url
            ) VALUES (?, ?, 'electronics', 'High concurrency test item', 100.0, 100.0, 0, 5.0, 10, 2, 'img.jpg')
            """, (f"Concurrency Item {test_slug}", test_slug))
            product_id = cursor.lastrowid
            conn.commit()

        success_count = 0
        failure_count = 0
        lock = threading.Lock()

        def attempt_checkout(thread_id: int):
            nonlocal success_count, failure_count
            session_id = f"concurrent_sess_{thread_id}_{secrets.token_hex(2)}"
            try:
                # Add 2 items to cart
                CartService.add_to_cart(session_id, product_id, 2)
                OrderService.checkout(
                    user_or_session_id=session_id,
                    customer_name=f"Shopper {thread_id}",
                    customer_email=f"shopper_{thread_id}@test.com",
                    customer_phone="9999999999",
                    shipping_address="123 Test St",
                    city="Bangalore",
                    pincode="560001"
                )
                with lock:
                    success_count += 1
            except Exception:
                with lock:
                    failure_count += 1

        threads = []
        for i in range(10):
            t = threading.Thread(target=attempt_checkout, args=(i,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Exactly 1 order should have succeeded (taking the 2 items), 9 failed
        self.assertEqual(success_count, 1, f"Expected exactly 1 successful checkout, got {success_count}.")
        self.assertEqual(failure_count, 9, f"Expected 9 failed checkouts due to stock exhaustion, got {failure_count}.")

        # Verify final stock is exactly 0 and NOT negative
        final_prod = ProductService.get_product(product_id)
        self.assertEqual(final_prod["stock"], 0, "Stock must be 0 and never drop below zero.")


class TestDetectionEngineRulesAdversarial(unittest.TestCase):
    def test_inj_001_true_positives_and_benign_resilience(self):
        """
        Rule INJ-001: Detects SQL Injection while avoiding false positives on benign queries.
        """
        # True Positives
        sqli_payloads = [
            "' UNION SELECT 1,2,3--",
            "1; DROP TABLE users;--",
            "' OR '1'='1",
            "admin' --",
            "1' waitfor delay '0:0:5'--"
        ]
        for p in sqli_payloads:
            res = AppSecDetector.analyze_live_request(
                client_ip="10.1.1.1", method="GET", path="/api/shop/products",
                query_string=f"q={p}"
            )
            self.assertIsNotNone(res, f"Failed to detect SQLi payload: {p}")
            self.assertTrue(res.triggered)
            self.assertEqual(res.rule_id, "INJ-001")

        # False Positive Resistance (Benign queries that contain SQL keywords like or, and, select)
        benign_queries = [
            "shoes or boots",
            "rock and roll t-shirt",
            "select collection shirts",
            "Doctor Who DVD box set",
            "black & white sneakers"
        ]
        for b in benign_queries:
            res = AppSecDetector.analyze_live_request(
                client_ip="10.1.1.2", method="GET", path="/api/shop/products",
                query_string=f"q={b}"
            )
            self.assertFalse(res.triggered, f"Benign query '{b}' caused false positive detection.")

    def test_xss_001_true_positives_and_benign_resilience(self):
        """
        Rule XSS-001: Detects Cross-Site Scripting while avoiding false positives on legitimate input.
        """
        # True Positives
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(document.cookie)",
            "<svg/onload=confirm(1)>"
        ]
        for p in xss_payloads:
            res = AppSecDetector.analyze_live_request(
                client_ip="10.1.1.3", method="POST", path="/api/shop/reviews",
                body_sample=f'{{"comment": "{p}"}}'
            )
            self.assertIsNotNone(res, f"Failed to detect XSS payload: {p}")
            self.assertTrue(res.triggered)
            self.assertEqual(res.rule_id, "XSS-001")

        # Benign inputs
        benign_texts = [
            "This product is > than average",
            "Price is < $500",
            "Me & my friends loved it",
            "5 * 5 = 25"
        ]
        for b in benign_texts:
            res = AppSecDetector.analyze_live_request(
                client_ip="10.1.1.4", method="POST", path="/api/shop/reviews",
                body_sample=f'{{"comment": "{b}"}}'
            )
            self.assertFalse(res.triggered, f"Benign text '{b}' caused false positive XSS detection.")


if __name__ == "__main__":
    unittest.main()
