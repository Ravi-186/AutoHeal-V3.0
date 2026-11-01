import json
import secrets
import sqlite3
from datetime import datetime, timezone, timedelta
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


class CouponService:
    @staticmethod
    def validate_coupon(code: str, cart_subtotal: float) -> Dict[str, Any]:
        """Validates a promotional coupon code against order value and usage limits."""
        seed_data()
        if not code or not code.strip():
            return {"valid": False, "message": "Coupon code is empty.", "discount_amount": 0.0}

        clean_code = code.strip().upper()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM coupons WHERE code = ?", (clean_code,))
            coupon = cursor.fetchone()
            if not coupon:
                return {"valid": False, "message": f"Coupon code '{clean_code}' is invalid.", "discount_amount": 0.0}

            c_dict = dict(coupon)
            if not c_dict["is_active"]:
                return {"valid": False, "message": f"Coupon '{clean_code}' is currently inactive.", "discount_amount": 0.0}

            if c_dict["usage_count"] >= c_dict["usage_limit"]:
                return {"valid": False, "message": f"Coupon '{clean_code}' usage limit has been reached.", "discount_amount": 0.0}

            min_spend = float(c_dict["min_order_amount"] or 0.0)
            if cart_subtotal < min_spend:
                return {
                    "valid": False,
                    "message": f"Coupon '{clean_code}' requires a minimum order amount of ₹{min_spend:,.2f}.",
                    "discount_amount": 0.0
                }

            # Calculate discount
            val = float(c_dict["discount_value"])
            if c_dict["discount_type"] == "PERCENTAGE":
                discount = round(cart_subtotal * (val / 100.0), 2)
                max_disc = c_dict.get("max_discount_amount")
                if max_disc and discount > float(max_disc):
                    discount = float(max_disc)
            else:
                discount = round(min(val, cart_subtotal), 2)

            return {
                "valid": True,
                "code": clean_code,
                "discount_type": c_dict["discount_type"],
                "discount_value": val,
                "discount_amount": discount,
                "description": c_dict["description"],
                "message": f"Coupon '{clean_code}' applied: ₹{discount:,.2f} savings!",
                "coupon": c_dict
            }

    @staticmethod
    def record_coupon_usage(code: str):
        """Increments coupon usage counter."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE coupons SET usage_count = usage_count + 1 WHERE code = ?", (code.strip().upper(),))
            conn.commit()

    @staticmethod
    def list_coupons(active_only: bool = True) -> List[Dict[str, Any]]:
        """Retrieves list of promotional coupons."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute("SELECT * FROM coupons WHERE is_active = 1 ORDER BY min_order_amount ASC")
            else:
                cursor.execute("SELECT * FROM coupons ORDER BY id DESC")
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def create_or_update_coupon(
        code: str,
        discount_type: str,
        discount_value: float,
        min_order_amount: float = 0.0,
        max_discount_amount: Optional[float] = None,
        description: str = "",
        is_active: int = 1,
        usage_limit: int = 1000
    ) -> Dict[str, Any]:
        """Admin creates or updates a promotional coupon."""
        clean_code = code.strip().upper()
        if discount_type not in ["PERCENTAGE", "FIXED"]:
            raise ValueError("Discount type must be PERCENTAGE or FIXED.")
        if discount_value <= 0:
            raise ValueError("Discount value must be greater than zero.")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO coupons (
                code, discount_type, discount_value, min_order_amount,
                max_discount_amount, description, is_active, usage_limit
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                discount_type=excluded.discount_type,
                discount_value=excluded.discount_value,
                min_order_amount=excluded.min_order_amount,
                max_discount_amount=excluded.max_discount_amount,
                description=excluded.description,
                is_active=excluded.is_active,
                usage_limit=excluded.usage_limit
            """, (clean_code, discount_type, discount_value, min_order_amount, max_discount_amount, description, is_active, usage_limit))
            conn.commit()

            cursor.execute("SELECT * FROM coupons WHERE code = ?", (clean_code,))
            return dict(cursor.fetchone())


class ReviewService:
    @staticmethod
    def get_reviews_for_product(product_id: int) -> Dict[str, Any]:
        """Retrieves verified customer reviews and aggregate rating distribution for a product."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM product_reviews 
            WHERE product_id = ?
            ORDER BY id DESC
            """, (product_id,))
            reviews = [dict(r) for r in cursor.fetchall()]

            total_reviews = len(reviews)
            if total_reviews > 0:
                avg_rating = round(sum(r["rating"] for r in reviews) / total_reviews, 1)
            else:
                avg_rating = 5.0

            distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
            for r in reviews:
                distribution[r["rating"]] = distribution.get(r["rating"], 0) + 1

            return {
                "product_id": product_id,
                "total_reviews": total_reviews,
                "average_rating": avg_rating,
                "distribution": distribution,
                "reviews": reviews
            }

    @staticmethod
    def add_review(
        product_id: int,
        author_name: str,
        rating: int,
        headline: str,
        comment: str,
        user_id: Optional[int] = None,
        customer_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submits a customer review and recalculates product aggregate rating."""
        seed_data()
        if not author_name.strip():
            raise ValueError("Author name is required.")
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5 stars.")
        if not headline.strip():
            raise ValueError("Review headline is required.")
        if not comment.strip():
            raise ValueError("Review comment is required.")

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Check if product exists
            cursor.execute("SELECT id, title FROM products WHERE id = ?", (product_id,))
            prod = cursor.fetchone()
            if not prod:
                raise ValueError(f"Product #{product_id} not found.")

            # 2. Check if verified purchase (customer ordered this product before)
            is_verified = 0
            if user_id or customer_email:
                cursor.execute("""
                SELECT oi.id FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE oi.product_id = ? AND (o.user_id = ? OR o.customer_email = ?)
                LIMIT 1
                """, (product_id, user_id, customer_email.strip().lower() if customer_email else ""))
                if cursor.fetchone():
                    is_verified = 1

            # 3. Insert review
            cursor.execute("""
            INSERT INTO product_reviews (
                product_id, user_id, author_name, rating, headline, comment, is_verified_purchase
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (product_id, user_id, author_name.strip(), rating, headline.strip(), comment.strip(), is_verified))
            review_id = cursor.lastrowid

            # 4. Recalculate average rating on product
            cursor.execute("SELECT AVG(rating) as avg_r, COUNT(id) as cnt FROM product_reviews WHERE product_id = ?", (product_id,))
            stat = cursor.fetchone()
            new_avg = round(stat["avg_r"], 1) if stat["avg_r"] else rating
            new_cnt = stat["cnt"] or 1
            cursor.execute("UPDATE products SET rating = ?, review_count = ? WHERE id = ?", (new_avg, new_cnt, product_id))

            conn.commit()
            return {
                "id": review_id,
                "product_id": product_id,
                "author_name": author_name.strip(),
                "rating": rating,
                "headline": headline.strip(),
                "comment": comment.strip(),
                "is_verified_purchase": bool(is_verified),
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            }

    @staticmethod
    def delete_review(review_id: int, user_id: Optional[int] = None, is_admin: bool = False) -> bool:
        """Deletes a review if requested by author or admin."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT product_id, user_id FROM product_reviews WHERE id = ?", (review_id,))
            row = cursor.fetchone()
            if not row:
                return False

            if not is_admin and (not user_id or row["user_id"] != user_id):
                raise PermissionError("Unauthorized to delete this review.")

            product_id = row["product_id"]
            cursor.execute("DELETE FROM product_reviews WHERE id = ?", (review_id,))

            # Recalculate rating
            cursor.execute("SELECT AVG(rating) as avg_r, COUNT(id) as cnt FROM product_reviews WHERE product_id = ?", (product_id,))
            stat = cursor.fetchone()
            new_avg = round(stat["avg_r"], 1) if stat and stat["avg_r"] else 5.0
            new_cnt = stat["cnt"] if stat else 0
            cursor.execute("UPDATE products SET rating = ?, review_count = ? WHERE id = ?", (new_avg, new_cnt, product_id))

            conn.commit()
            return True


class NotificationService:
    @staticmethod
    def get_notifications(user_id: Optional[int] = None, email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves customer or admin notifications."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                SELECT * FROM customer_notifications
                WHERE user_id = ? OR customer_email = ?
                ORDER BY id DESC LIMIT 20
                """, (user_id, email or ""))
            elif email:
                cursor.execute("""
                SELECT * FROM customer_notifications
                WHERE customer_email = ?
                ORDER BY id DESC LIMIT 20
                """, (email.strip().lower(),))
            else:
                cursor.execute("SELECT * FROM customer_notifications ORDER BY id DESC LIMIT 20")
            return [dict(r) for r in cursor.fetchall()]

    @staticmethod
    def mark_as_read(notification_id: int) -> bool:
        """Marks a notification as read."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE customer_notifications SET is_read = 1 WHERE id = ?", (notification_id,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def mark_all_read(user_id: Optional[int] = None, email: Optional[str] = None):
        """Marks all notifications for user as read."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("UPDATE customer_notifications SET is_read = 1 WHERE user_id = ? OR customer_email = ?", (user_id, email or ""))
            elif email:
                cursor.execute("UPDATE customer_notifications SET is_read = 1 WHERE customer_email = ?", (email.strip().lower(),))
            else:
                cursor.execute("UPDATE customer_notifications SET is_read = 1")
            conn.commit()

    @staticmethod
    def create_notification(
        title: str,
        message: str,
        notification_type: str = "ORDER_UPDATE",
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        link_url: str = "/shop"
    ) -> Dict[str, Any]:
        """Creates a new in-app notification."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO customer_notifications (
                user_id, customer_email, title, message, notification_type, link_url
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, email.strip().lower() if email else None, title.strip(), message.strip(), notification_type, link_url))
            conn.commit()
            nid = cursor.lastrowid
            cursor.execute("SELECT * FROM customer_notifications WHERE id = ?", (nid,))
            return dict(cursor.fetchone())


class CartService:
    @staticmethod
    def calculate_cart_totals(items: List[Dict[str, Any]], coupon_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Pure business calculation of cart financial totals:
        - subtotal (sum of selling price * quantity)
        - original_subtotal (sum of MRP * quantity)
        - savings / discount
        - coupon_discount (if applicable coupon code provided)
        - delivery_fee (Free delivery on orders >= 500, else 40)
        - final_total (subtotal - coupon_discount + delivery_fee)
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

        # Delivery policy: Free above ₹500, else ₹40
        if subtotal == 0:
            delivery_fee = 0.0
        elif subtotal >= 500.0:
            delivery_fee = 0.0
        else:
            delivery_fee = 40.0

        # Optional Coupon Discount Calculation
        coupon_discount = 0.0
        coupon_info = None
        if coupon_code and coupon_code.strip() and subtotal > 0:
            c_val = CouponService.validate_coupon(coupon_code.strip(), subtotal)
            if c_val["valid"]:
                coupon_discount = c_val["discount_amount"]
                coupon_info = c_val

        final_total = max(0.0, round(subtotal - coupon_discount + delivery_fee, 2))

        return {
            "total_items": total_items,
            "subtotal": subtotal,
            "original_subtotal": original_subtotal,
            "discount": discount,
            "coupon_code": coupon_info["code"] if coupon_info else None,
            "coupon_discount": coupon_discount,
            "coupon_message": coupon_info["message"] if coupon_info else None,
            "delivery_fee": delivery_fee,
            "final_total": final_total,
            "free_delivery_qualified": subtotal >= 500.0 if subtotal > 0 else True
        }

    @staticmethod
    def get_cart(user_or_session_id: str, coupon_code: Optional[str] = None) -> Dict[str, Any]:
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

            totals = CartService.calculate_cart_totals(items, coupon_code=coupon_code)
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
        user_id: Optional[int] = None,
        coupon_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transactional Checkout:
        1. Validates cart has items.
        2. Applies optional promotional coupon.
        3. Validates and reserves inventory stock (atomic decrement).
        4. Generates unique order reference (e.g. ORD-2026-XXXX).
        5. Inserts into orders and order_items tables.
        6. Clears shopping cart and dispatches confirmation notification.
        """
        seed_data()
        cart = CartService.get_cart(user_or_session_id, coupon_code=coupon_code)
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

        applied_coupon = cart.get("coupon_code")
        coupon_discount = cart.get("coupon_discount") or 0.0
        if applied_coupon:
            CouponService.record_coupon_usage(applied_coupon)

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
                    order_status, subtotal, discount, delivery_fee, total_amount,
                    coupon_code, coupon_discount
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    cart["final_total"],
                    applied_coupon,
                    coupon_discount
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
                    UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?
                    """, (qty, pid, qty))
                    if cursor.rowcount == 0:
                        raise ValueError(f"Insufficient stock for '{item['title']}' due to concurrent checkout demand.")

                # Clear cart
                cursor.execute("DELETE FROM cart_items WHERE user_or_session_id = ?", (user_or_session_id,))

        try:
            NotificationService.create_notification(
                title=f"Order Confirmed: {order_ref}",
                message=f"Thank you, {customer_name}! Your order of {cart['total_items']} items totaling ₹{cart['final_total']:,.2f} has been placed.",
                notification_type="ORDER_UPDATE",
                user_id=user_id,
                email=customer_email,
                link_url="/shop"
            )
        except Exception:
            pass

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
            with conn:
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
        token_expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO users (name, email, password_hash, salt, role, phone, address, city, pincode, token, token_expires_at)
                VALUES (?, ?, ?, ?, 'customer', ?, ?, ?, ?, ?, ?)
                """, (name.strip(), email.strip().lower(), pw_hash, salt, phone.strip(), address.strip(), city.strip(), pincode.strip(), token, token_expires_at))
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
        """Authenticates user and returns active session token with 7-day expiration."""
        seed_data()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
            user = cursor.fetchone()

            if not user or not verify_password(password, user["password_hash"], user["salt"]):
                raise ValueError("Invalid email or password.")

            # Refresh token with role prefix and 7-day expiration
            prefix = "token_admin_" if user["role"] == "admin" else "token_"
            new_token = f"{prefix}{secrets.token_hex(24)}"
            token_expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE users SET token = ?, token_expires_at = ? WHERE id = ?", (new_token, token_expires_at, user["id"]))
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
        """Retrieves user by authorization token with expiration and timing-attack resistance."""
        if not token:
            return None
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, name, email, role, phone, address, city, pincode, token, token_expires_at 
            FROM users 
            WHERE token = ?
            """, (token,))
            row = cursor.fetchone()
            if not row:
                return None

            # Constant-time token verification
            if not secrets.compare_digest(row["token"], token):
                return None

            # Enforce server-side session expiration
            if "token_expires_at" in row.keys() and row["token_expires_at"]:
                if str(row["token_expires_at"]) < now_str:
                    return None  # Session expired

            return dict(row)

    @staticmethod
    def logout(token: str) -> bool:
        """Revokes an active session token server-side."""
        if not token:
            return False
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET token = NULL, token_expires_at = NULL WHERE token = ?", (token,))
            conn.commit()
            return cursor.rowcount > 0

    @staticmethod
    def update_profile(user_id: int, name: str, phone: str = "", address: str = "", city: str = "", pincode: str = "") -> Dict[str, Any]:
        """Updates customer contact and delivery address profile."""
        if not name.strip():
            raise ValueError("Full name cannot be empty.")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE users SET name = ?, phone = ?, address = ?, city = ?, pincode = ?
            WHERE id = ?
            """, (name.strip(), phone.strip(), address.strip(), city.strip(), pincode.strip(), user_id))
            conn.commit()
            cursor.execute("SELECT id, name, email, role, phone, address, city, pincode, token FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("User not found.")
            return dict(row)


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

            # Total reviews & customers
            cursor.execute("SELECT COUNT(id) as total_reviews FROM product_reviews")
            total_reviews = cursor.fetchone()["total_reviews"]

            cursor.execute("SELECT COUNT(id) as total_customers FROM users WHERE role = 'customer'")
            total_customers = cursor.fetchone()["total_customers"]

            cursor.execute("SELECT COUNT(id) as active_coupons FROM coupons WHERE is_active = 1")
            active_coupons = cursor.fetchone()["active_coupons"]

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
                "total_reviews": total_reviews,
                "total_customers": total_customers,
                "active_coupons": active_coupons,
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

    @staticmethod
    def list_all_orders(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Admin lists all store orders with optional status filtering."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if status_filter and status_filter.upper() != "ALL":
                cursor.execute("SELECT id FROM orders WHERE order_status = ? ORDER BY id DESC", (status_filter.upper(),))
            else:
                cursor.execute("SELECT id FROM orders ORDER BY id DESC")
            order_ids = [r["id"] for r in cursor.fetchall()]
            return [OrderService.get_order_by_id(oid) for oid in order_ids if oid]

    @staticmethod
    def list_all_customers() -> List[Dict[str, Any]]:
        """Admin lists all registered customers."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT u.id, u.name, u.email, u.phone, u.city, u.created_at, COUNT(o.id) as order_count, COALESCE(SUM(o.total_amount), 0) as total_spent
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id AND o.order_status != 'CANCELLED'
            WHERE u.role = 'customer'
            GROUP BY u.id
            ORDER BY u.id DESC
            """)
            return [dict(r) for r in cursor.fetchall()]
