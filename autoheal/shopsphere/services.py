import json
import secrets
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from shopsphere.database import (
    get_db_connection, hash_password, verify_password, seed_data
)


class ProductService:
    @staticmethod
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
    ) -> Dict[str, Any]:
        """Queries products with comprehensive multi-criteria filtering, search, and sorting."""
        seed_data()
        with get_db_connection() as conn:
            query = "SELECT * FROM products WHERE 1=1"
            params: List[Any] = []

            if q and q.strip():
                clean_q = f"%{q.strip()}%"
                query += " AND (title LIKE ? OR description LIKE ? OR category LIKE ?)"
                params.extend([clean_q, clean_q, clean_q])

            if category and category.strip() and category.lower() != "all":
                query += " AND category = ?"
                params.append(category.strip().lower())

            if min_price is not None and min_price > 0:
                query += " AND price >= ?"
                params.append(min_price)

            if max_price is not None and max_price > 0:
                query += " AND price <= ?"
                params.append(max_price)

            if min_rating is not None and min_rating > 0:
                query += " AND rating >= ?"
                params.append(min_rating)

            if in_stock_only:
                query += " AND stock > 0"

            # Sorting logic
            sort_map = {
                "price_asc": "price ASC",
                "price_desc": "price DESC",
                "rating": "rating DESC",
                "newest": "id DESC",
                "discount": "discount_percent DESC",
                "popularity": "review_count DESC, rating DESC"
            }
            order_clause = sort_map.get(sort_by, "review_count DESC")
            query += f" ORDER BY {order_clause}"

            # Total count for pagination
            cursor = conn.cursor()
            count_query = f"SELECT COUNT(*) as total FROM ({query})"
            cursor.execute(count_query, params)
            total = cursor.fetchone()["total"]

            # Pagination slice
            offset = max(0, (page - 1) * page_size)
            query += " LIMIT ? OFFSET ?"
            params.extend([page_size, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            products = []
            for r in rows:
                p = dict(r)
                if p.get("specs_json"):
                    try:
                        p["specs"] = json.loads(p["specs_json"])
                    except Exception:
                        p["specs"] = {}
                else:
                    p["specs"] = {}
                products.append(p)

            return {
                "products": products,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
            }

    @staticmethod
    def get_product(product_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single product by ID."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            if not row:
                return None
            p = dict(row)
            if p.get("specs_json"):
                try:
                    p["specs"] = json.loads(p["specs_json"])
                except Exception:
                    p["specs"] = {}
            else:
                p["specs"] = {}
            return p

    @staticmethod
    def get_categories() -> List[Dict[str, Any]]:
        """Retrieves all product categories with product counts."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT c.*, COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON p.category = c.slug
            GROUP BY c.id
            ORDER BY c.id ASC
            """)
            return [dict(r) for r in cursor.fetchall()]


class CartService:
    @staticmethod
    def calculate_cart_totals(items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Pure business calculation of cart financial totals:
        - subtotal (sum of selling price * quantity)
        - original_subtotal (sum of MRP * quantity)
        - savings / discount
        - delivery_fee (Free delivery on orders >= 500, else 40)
        - final_total (subtotal + delivery_fee)
        """
        subtotal = 0.0
        original_subtotal = 0.0
        total_items = 0

        for item in items:
            qty = max(1, int(item.get("quantity", 1)))
            price = float(item.get("price", 0.0))
            orig_price = float(item.get("original_price", price))

            subtotal += price * qty
            original_subtotal += orig_price * qty
            total_items += qty

        subtotal = round(subtotal, 2)
        original_subtotal = round(original_subtotal, 2)
        discount = round(max(0.0, original_subtotal - subtotal), 2)

        # Flipkart-style delivery policy: Free above ₹500, else ₹40
        if subtotal == 0:
            delivery_fee = 0.0
        elif subtotal >= 500.0:
            delivery_fee = 0.0
        else:
            delivery_fee = 40.0

        final_total = round(subtotal + delivery_fee, 2)

        return {
            "total_items": total_items,
            "subtotal": subtotal,
            "original_subtotal": original_subtotal,
            "discount": discount,
            "delivery_fee": delivery_fee,
            "final_total": final_total,
            "free_delivery_qualified": subtotal >= 500.0 if subtotal > 0 else True
        }

    @staticmethod
    def get_cart(user_or_session_id: str) -> Dict[str, Any]:
        """Retrieves cart items with complete product details and financial summary."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT c.id as cart_item_id, c.quantity, c.added_at,
                   p.id as product_id, p.title, p.price, p.original_price,
                   p.discount_percent, p.stock, p.image_url, p.category, p.badge
            FROM cart_items c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_or_session_id = ?
            ORDER BY c.id DESC
            """, (user_or_session_id,))
            rows = cursor.fetchall()
            items = [dict(r) for r in rows]

            totals = CartService.calculate_cart_totals(items)
            return {
                "user_or_session_id": user_or_session_id,
                "items": items,
                **totals
            }

    @staticmethod
    def add_to_cart(user_or_session_id: str, product_id: int, quantity: int = 1) -> Dict[str, Any]:
        """Adds a product to the cart with inventory stock limit enforcement."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # 1. Check product stock
            cursor.execute("SELECT stock, title FROM products WHERE id = ?", (product_id,))
            prod = cursor.fetchone()
            if not prod:
                raise ValueError(f"Product ID {product_id} not found.")

            stock = prod["stock"]
            if stock <= 0:
                raise ValueError(f"'{prod['title']}' is currently out of stock.")

            # 2. Check existing cart quantity
            cursor.execute("""
            SELECT quantity FROM cart_items 
            WHERE user_or_session_id = ? AND product_id = ?
            """, (user_or_session_id, product_id))
            existing = cursor.fetchone()

            if existing:
                new_qty = existing["quantity"] + quantity
                if new_qty > stock:
                    new_qty = stock  # Cap at available stock
                cursor.execute("""
                UPDATE cart_items SET quantity = ? 
                WHERE user_or_session_id = ? AND product_id = ?
                """, (new_qty, user_or_session_id, product_id))
            else:
                qty_to_add = min(quantity, stock)
                cursor.execute("""
                INSERT INTO cart_items (user_or_session_id, product_id, quantity)
                VALUES (?, ?, ?)
                """, (user_or_session_id, product_id, qty_to_add))

            conn.commit()
            return CartService.get_cart(user_or_session_id)

    @staticmethod
    def update_quantity(user_or_session_id: str, product_id: int, quantity: int) -> Dict[str, Any]:
        """Updates item quantity in cart or removes if quantity <= 0."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if quantity <= 0:
                cursor.execute("""
                DELETE FROM cart_items 
                WHERE user_or_session_id = ? AND product_id = ?
                """, (user_or_session_id, product_id))
            else:
                # Check available inventory
                cursor.execute("SELECT stock, title FROM products WHERE id = ?", (product_id,))
                prod = cursor.fetchone()
                if not prod:
                    raise ValueError(f"Product ID {product_id} not found.")
                stock = prod["stock"]
                capped_qty = min(quantity, stock)
                cursor.execute("""
                UPDATE cart_items SET quantity = ?
                WHERE user_or_session_id = ? AND product_id = ?
                """, (capped_qty, user_or_session_id, product_id))

            conn.commit()
            return CartService.get_cart(user_or_session_id)

    @staticmethod
    def remove_from_cart(user_or_session_id: str, product_id: int) -> Dict[str, Any]:
        """Removes a product completely from cart."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            DELETE FROM cart_items 
            WHERE user_or_session_id = ? AND product_id = ?
            """, (user_or_session_id, product_id))
            conn.commit()
            return CartService.get_cart(user_or_session_id)

    @staticmethod
    def clear_cart(user_or_session_id: str):
        """Clears all cart items for user or session."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cart_items WHERE user_or_session_id = ?", (user_or_session_id,))
            conn.commit()


class WishlistService:
    @staticmethod
    def get_wishlist(user_or_session_id: str) -> List[Dict[str, Any]]:
        """Retrieves all wishlist items for user."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT w.id as wishlist_id, w.added_at,
                   p.id as product_id, p.title, p.price, p.original_price,
                   p.discount_percent, p.rating, p.stock, p.image_url, p.category
            FROM wishlist w
            JOIN products p ON w.product_id = p.id
            WHERE w.user_or_session_id = ?
            ORDER BY w.id DESC
            """, (user_or_session_id,))
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def toggle_wishlist(user_or_session_id: str, product_id: int) -> Dict[str, Any]:
        """Adds or removes item from wishlist."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id FROM wishlist 
            WHERE user_or_session_id = ? AND product_id = ?
            """, (user_or_session_id, product_id))
            row = cursor.fetchone()

            if row:
                cursor.execute("DELETE FROM wishlist WHERE id = ?", (row["id"],))
                in_wishlist = False
            else:
                cursor.execute("""
                INSERT INTO wishlist (user_or_session_id, product_id)
                VALUES (?, ?)
                """, (user_or_session_id, product_id))
                in_wishlist = True

            conn.commit()
            return {
                "product_id": product_id,
                "in_wishlist": in_wishlist,
                "wishlist": WishlistService.get_wishlist(user_or_session_id)
            }

    @staticmethod
    def move_to_cart(user_or_session_id: str, product_id: int) -> Dict[str, Any]:
        """Moves an item from wishlist into the cart."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            DELETE FROM wishlist 
            WHERE user_or_session_id = ? AND product_id = ?
            """, (user_or_session_id, product_id))
            conn.commit()

        CartService.add_to_cart(user_or_session_id, product_id, 1)
        return {
            "cart": CartService.get_cart(user_or_session_id),
            "wishlist": WishlistService.get_wishlist(user_or_session_id)
        }


class OrderService:
    @staticmethod
    def checkout(
        user_or_session_id: str,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        shipping_address: str,
        city: str,
        pincode: str,
        payment_method: str = "UPI / QR Code",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Transactional Checkout:
        1. Validates cart has items.
        2. Validates and reserves inventory stock (atomic decrement).
        3. Generates unique order reference (e.g. ORD-2026-XXXX).
        4. Inserts into orders and order_items tables.
        5. Clears shopping cart.
        """
        seed_data()
        cart = CartService.get_cart(user_or_session_id)
        if not cart["items"]:
            raise ValueError("Cannot checkout with an empty cart.")

        # Input validation
        if not customer_name.strip():
            raise ValueError("Customer name is required.")
        if not customer_email.strip() or "@" not in customer_email:
            raise ValueError("A valid email address is required.")
        if not shipping_address.strip() or not city.strip() or not pincode.strip():
            raise ValueError("Complete delivery address, city, and pincode are required.")

        order_ref = f"ORD-2026-{secrets.token_hex(4).upper()}"

        with get_db_connection() as conn:
            with conn:  # Atomic transaction boundary; automatic rollback on any exception
                cursor = conn.cursor()

                # Verify stock and lock rows
                for item in cart["items"]:
                    pid = item["product_id"]
                    qty = item["quantity"]
                    cursor.execute("SELECT stock, title FROM products WHERE id = ?", (pid,))
                    prod = cursor.fetchone()
                    if not prod or prod["stock"] < qty:
                        raise ValueError(f"Insufficient stock for '{item['title']}'. Requested: {qty}, Available: {prod['stock'] if prod else 0}")

                # Insert Order
                cursor.execute("""
                INSERT INTO orders (
                    order_ref, user_id, customer_name, customer_email, customer_phone,
                    shipping_address, city, pincode, payment_method, payment_status,
                    order_status, subtotal, discount, delivery_fee, total_amount
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_ref,
                    user_id,
                    customer_name.strip(),
                    customer_email.strip(),
                    customer_phone.strip(),
                    shipping_address.strip(),
                    city.strip(),
                    pincode.strip(),
                    payment_method,
                    "COMPLETED_SIMULATED",
                    "PLACED",
                    cart["subtotal"],
                    cart["discount"],
                    cart["delivery_fee"],
                    cart["final_total"]
                ))
                order_id = cursor.lastrowid

                # Insert Order Items and Decrement Stock atomically
                for item in cart["items"]:
                    pid = item["product_id"]
                    qty = item["quantity"]
                    unit_price = item["price"]
                    item_total = round(unit_price * qty, 2)

                    cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, title, unit_price, quantity, total_price)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (order_id, pid, item["title"], unit_price, qty, item_total))

                    cursor.execute("""
                    UPDATE products SET stock = stock - ? WHERE id = ?
                    """, (qty, pid))

                # Clear cart
                cursor.execute("DELETE FROM cart_items WHERE user_or_session_id = ?", (user_or_session_id,))

            return OrderService.get_order_by_id(order_id)

    @staticmethod
    def get_order_by_id(order_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves full order with order items."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            order_row = cursor.fetchone()
            if not order_row:
                return None

            order = dict(order_row)
            cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
            order["items"] = [dict(r) for r in cursor.fetchall()]
            return order

    @staticmethod
    def get_order_by_ref(order_ref: str) -> Optional[Dict[str, Any]]:
        """Retrieves order by order reference string."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE order_ref = ?", (order_ref,))
            order_row = cursor.fetchone()
            if not order_row:
                return None
            return OrderService.get_order_by_id(order_row["id"])

    @staticmethod
    def get_orders_by_email_or_user(email: Optional[str] = None, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieves order history for a customer."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT id FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,))
            elif email:
                cursor.execute("SELECT id FROM orders WHERE customer_email = ? ORDER BY id DESC", (email.strip(),))
            else:
                return []
            order_ids = [r["id"] for r in cursor.fetchall()]
            return [OrderService.get_order_by_id(oid) for oid in order_ids if oid]

    @staticmethod
    def cancel_order(order_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Cancels an order and automatically restores reserved product stock to inventory."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            order = cursor.fetchone()
            if not order:
                raise ValueError("Order not found.")

            if user_id and order["user_id"] and order["user_id"] != user_id:
                raise PermissionError("Unauthorized to cancel this order.")

            if order["order_status"] in ["CANCELLED", "DELIVERED"]:
                raise ValueError(f"Cannot cancel order in status '{order['order_status']}'.")

            # Restore stock
            cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,))
            items = cursor.fetchall()
            for it in items:
                cursor.execute("""
                UPDATE products SET stock = stock + ? WHERE id = ?
                """, (it["quantity"], it["product_id"]))

            cursor.execute("""
            UPDATE orders SET order_status = 'CANCELLED', payment_status = 'REFUNDED_SIMULATED'
            WHERE id = ?
            """, (order_id,))
            conn.commit()

            return OrderService.get_order_by_id(order_id)


class UserService:
    @staticmethod
    def register(name: str, email: str, password: str, phone: str = "", address: str = "", city: str = "", pincode: str = "") -> Dict[str, Any]:
        """Registers a new customer account with secure salted password hashing."""
        seed_data()
        if not name.strip():
            raise ValueError("Full name is required.")
        if not email.strip() or "@" not in email:
            raise ValueError("Valid email is required.")
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")

        pw_hash, salt = hash_password(password)
        token = f"token_{secrets.token_hex(24)}"

        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO users (name, email, password_hash, salt, role, phone, address, city, pincode, token)
                VALUES (?, ?, ?, ?, 'customer', ?, ?, ?, ?, ?)
                """, (name.strip(), email.strip().lower(), pw_hash, salt, phone.strip(), address.strip(), city.strip(), pincode.strip(), token))
                conn.commit()
                user_id = cursor.lastrowid
                return {
                    "id": user_id,
                    "name": name.strip(),
                    "email": email.strip().lower(),
                    "role": "customer",
                    "phone": phone.strip(),
                    "address": address.strip(),
                    "city": city.strip(),
                    "pincode": pincode.strip(),
                    "token": token
                }
            except sqlite3.IntegrityError:
                raise ValueError("An account with this email address already exists.")

    @staticmethod
    def login(email: str, password: str) -> Dict[str, Any]:
        """Authenticates user and returns active session token."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
            user = cursor.fetchone()

            if not user or not verify_password(password, user["password_hash"], user["salt"]):
                raise ValueError("Invalid email or password.")

            # Refresh token with role prefix
            prefix = "token_admin_" if user["role"] == "admin" else "token_"
            new_token = f"{prefix}{secrets.token_hex(24)}"
            cursor.execute("UPDATE users SET token = ? WHERE id = ?", (new_token, user["id"]))
            conn.commit()

            return {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "phone": user["phone"] or "",
                "address": user["address"] or "",
                "city": user["city"] or "",
                "pincode": user["pincode"] or "",
                "token": new_token
            }

    @staticmethod
    def get_by_token(token: str) -> Optional[Dict[str, Any]]:
        """Retrieves user by authorization token."""
        if not token:
            return None
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, email, role, phone, address, city, pincode, token FROM users WHERE token = ?", (token,))
            row = cursor.fetchone()
            return dict(row) if row else None


class AdminService:
    @staticmethod
    def get_dashboard_metrics() -> Dict[str, Any]:
        """Calculates executive sales and inventory metrics from actual SQLite database."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Total revenue (excluding cancelled)
            cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as total_revenue,
                   COUNT(id) as total_orders
            FROM orders
            WHERE order_status != 'CANCELLED'
            """)
            rev_row = cursor.fetchone()
            total_revenue = round(rev_row["total_revenue"], 2)
            total_orders = rev_row["total_orders"]

            # Orders by status
            cursor.execute("""
            SELECT order_status, COUNT(id) as count
            FROM orders
            GROUP BY order_status
            """)
            status_counts = {r["order_status"]: r["count"] for r in cursor.fetchall()}

            # Product & Stock Counts
            cursor.execute("""
            SELECT COUNT(id) as total_products,
                   SUM(CASE WHEN stock <= 5 THEN 1 ELSE 0 END) as low_stock_count,
                   SUM(CASE WHEN stock = 0 THEN 1 ELSE 0 END) as out_of_stock_count
            FROM products
            """)
            prod_row = cursor.fetchone()

            # Top selling products
            cursor.execute("""
            SELECT p.id, p.title, p.price, p.stock, COALESCE(SUM(oi.quantity), 0) as units_sold
            FROM products p
            LEFT JOIN order_items oi ON p.id = oi.product_id
            GROUP BY p.id
            ORDER BY units_sold DESC, p.id ASC
            LIMIT 5
            """)
            top_products = [dict(r) for r in cursor.fetchall()]

            # Recent orders
            cursor.execute("""
            SELECT id, order_ref, customer_name, customer_email, total_amount, order_status, created_at
            FROM orders
            ORDER BY id DESC
            LIMIT 8
            """)
            recent_orders = [dict(r) for r in cursor.fetchall()]

            return {
                "total_revenue": total_revenue,
                "total_orders": total_orders,
                "orders_by_status": status_counts,
                "total_products": prod_row["total_products"],
                "low_stock_count": prod_row["low_stock_count"] or 0,
                "out_of_stock_count": prod_row["out_of_stock_count"] or 0,
                "top_products": top_products,
                "recent_orders": recent_orders
            }

    @staticmethod
    def update_product_inventory(product_id: int, new_stock: int, admin_email: str = "admin@shopsphere.com") -> Dict[str, Any]:
        """Admin updates product stock level."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
            cursor.execute("""
            INSERT INTO admin_audit_logs (admin_email, action, target_entity, details)
            VALUES (?, 'UPDATE_STOCK', ?, ?)
            """, (admin_email, f"Product #{product_id}", f"Updated stock to {new_stock}"))
            conn.commit()
            return ProductService.get_product(product_id)

    @staticmethod
    def update_order_status(order_id: int, new_status: str, admin_email: str = "admin@shopsphere.com") -> Dict[str, Any]:
        """Admin advances or updates an order status (PLACED -> PROCESSING -> SHIPPED -> DELIVERED)."""
        valid_statuses = ["PLACED", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status '{new_status}'. Supported: {', '.join(valid_statuses)}")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE orders SET order_status = ? WHERE id = ?", (new_status, order_id))
            cursor.execute("""
            INSERT INTO admin_audit_logs (admin_email, action, target_entity, details)
            VALUES (?, 'UPDATE_ORDER_STATUS', ?, ?)
            """, (admin_email, f"Order #{order_id}", f"Changed status to {new_status}"))
            conn.commit()
            return OrderService.get_order_by_id(order_id)
