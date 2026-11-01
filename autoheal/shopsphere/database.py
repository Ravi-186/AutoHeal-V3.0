import os
import sqlite3
import hashlib
import secrets
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

# Database path in data/
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "shopsphere.db")


from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Yields a thread-safe connection to the ShopSphere SQLite database and automatically closes it."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Secure password hashing using PBKDF2-HMAC-SHA256 with cryptographically random salt."""
    if not salt:
        salt = secrets.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations=100000
    ).hex()
    return pw_hash, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verifies a plain password against the stored PBKDF2 hash."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)


def init_db():
    """Creates database tables and initializes schema if they do not exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer',
            phone TEXT,
            address TEXT,
            city TEXT,
            pincode TEXT,
            token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Categories Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            icon TEXT NOT NULL,
            description TEXT
        );
        """)

        # 3. Products Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            original_price REAL NOT NULL,
            discount_percent INTEGER NOT NULL,
            rating REAL NOT NULL DEFAULT 4.5,
            review_count INTEGER NOT NULL DEFAULT 120,
            stock INTEGER NOT NULL DEFAULT 20,
            image_url TEXT NOT NULL,
            badge TEXT,
            specs_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 4. Cart Items Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_or_session_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            UNIQUE(user_or_session_id, product_id)
        );
        """)

        # 5. Wishlist Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_or_session_id TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            UNIQUE(user_or_session_id, product_id)
        );
        """)

        # 6. Orders Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_ref TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            city TEXT NOT NULL,
            pincode TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'COMPLETED_SIMULATED',
            order_status TEXT NOT NULL DEFAULT 'PLACED',
            subtotal REAL NOT NULL,
            discount REAL NOT NULL,
            delivery_fee REAL NOT NULL,
            total_amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        """)

        # 7. Order Items Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            unit_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
        );
        """)

        # 8. Admin Audit Log Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_email TEXT NOT NULL,
            action TEXT NOT NULL,
            target_entity TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 9. AppSec Telemetry Events Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            correlation_id TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            client_ip TEXT NOT NULL,
            user_agent TEXT,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            latency_ms REAL NOT NULL DEFAULT 0.0,
            user_id_or_session TEXT,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL DEFAULT 'INFO',
            details_json TEXT,
            action_taken TEXT NOT NULL DEFAULT 'ALLOWED'
        );
        """)

        # 10. AppSec Security Incidents Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT UNIQUE NOT NULL,
            rule_id TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            confidence REAL NOT NULL DEFAULT 1.0,
            summary TEXT NOT NULL,
            evidence_json TEXT,
            affected_endpoints_json TEXT,
            source_ip TEXT,
            impact_actual TEXT,
            impact_potential TEXT,
            mitigation_actions_json TEXT,
            remediation_details TEXT,
            regression_tests_json TEXT,
            verification_status TEXT NOT NULL DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 11. Dynamic Client Blocklist Table (WAF / Rate-limiting)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS blocked_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_ip TEXT UNIQUE NOT NULL,
            reason TEXT NOT NULL,
            rule_id TEXT NOT NULL,
            incident_id TEXT,
            blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1
        );
        """)

        # 12. Vulnerabilities Tracker & Remediation Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vulnerabilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vuln_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            cwe_id TEXT NOT NULL,
            mitre_technique_id TEXT NOT NULL,
            mitre_tactic TEXT NOT NULL,
            component_path TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            description TEXT NOT NULL,
            remediation_proposal TEXT NOT NULL,
            patch_diff TEXT NOT NULL,
            regression_test_name TEXT NOT NULL,
            regression_test_status TEXT NOT NULL DEFAULT 'PENDING',
            approval_status TEXT NOT NULL DEFAULT 'PENDING',
            approved_by TEXT,
            applied_at TIMESTAMP,
            rolled_back_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Add optional MITRE and AI columns to security_incidents if not present
        extra_columns = [
            ("mitre_technique_id", "TEXT DEFAULT 'T1110.001'"),
            ("mitre_tactic", "TEXT DEFAULT 'Credential Access (TA0006)'"),
            ("mitre_name", "TEXT DEFAULT 'Brute Force: Password Guessing'"),
            ("ai_summary", "TEXT"),
            ("ai_recommendations_json", "TEXT"),
            ("recovery_status", "TEXT DEFAULT 'CONTAINED'")
        ]
        for col_name, col_type in extra_columns:
            try:
                cursor.execute(f"ALTER TABLE security_incidents ADD COLUMN {col_name} {col_type};")
            except Exception:
                pass  # column already exists

        conn.commit()


def seed_data():
    """Populates database with realistic categories, products, and default admin/customer accounts."""
    init_db()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Seed Default Admin & Customer Accounts
        admin_pw_hash, admin_salt = hash_password("Admin@123")
        cursor.execute("""
        INSERT OR IGNORE INTO users (name, email, password_hash, salt, role, phone, address, city, pincode, token)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "System Administrator",
            "admin@shopsphere.com",
            admin_pw_hash,
            admin_salt,
            "admin",
            "+91 98765 43210",
            "ShopSphere HQ, Cyber Tech Park",
            "Bengaluru",
            "560100",
            "token_admin_shopsphere_secret"
        ))

        demo_pw_hash, demo_salt = hash_password("Demo@123")
        cursor.execute("""
        INSERT OR IGNORE INTO users (name, email, password_hash, salt, role, phone, address, city, pincode, token)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Rahul Sharma",
            "rahul.shopper@example.com",
            demo_pw_hash,
            demo_salt,
            "customer",
            "+91 91234 56789",
            "Flat 402, Green Valley Apartments",
            "Bengaluru",
            "560034",
            "token_demo_customer_session"
        ))

        # Seed Categories matching the exact diagram categories
        categories = [
            ("Mobiles", "mobiles", "📱", "Latest smartphones, 5G devices, and tablets"),
            ("Laptops", "laptops", "💻", "High-performance ultrabooks, MacBooks, and gaming laptops"),
            ("Electronics", "electronics", "⚡", "TVs, smart gadgets, audio, and gaming gear"),
            ("Fashion", "fashion", "👟", "Apparel, sneakers, watches, and accessories"),
            ("Home & Furniture", "home", "🏠", "Home appliances, kitchenware, and furniture"),
            ("Beauty", "beauty", "✨", "Skincare, cosmetics, grooming, and wellness"),
            ("Sports", "sports", "⚽", "Fitness gear, activewear, and outdoor sports"),
            ("Books", "books", "📚", "Bestsellers, tech guides, fiction, and literature")
        ]
        for name, slug, icon, desc in categories:
            cursor.execute("""
            INSERT OR IGNORE INTO categories (name, slug, icon, description)
            VALUES (?, ?, ?, ?)
            """, (name, slug, icon, desc))

        # Ensure the 4 Featured Products shown in the target diagram are always present and up-to-date
        diagram_featured_products = [
            (
                1,
                "iPhone 15",
                "iphone-15",
                "mobiles",
                "Dynamic Island, 48MP Main camera, and USB-C in a durable color-infused glass and aluminum design.",
                79999.0, 89999.0, 11, 4.8, 5320, 25,
                "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=600&auto=format&fit=crop&q=80",
                "Featured",
                json.dumps({"Display": "6.1-inch Super Retina XDR", "Chip": "A16 Bionic", "Camera": "48MP Dual System", "Port": "USB-C"})
            ),
            (
                2,
                "MacBook Air",
                "macbook-air",
                "laptops",
                "Strikingly thin design with fast Apple Silicon, up to 18 hours of battery life, Liquid Retina display, and backlit Magic Keyboard.",
                109999.0, 119999.0, 8, 4.9, 3120, 15,
                "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop&q=80",
                "Featured",
                json.dumps({"Screen": "13.6-inch Liquid Retina", "Chip": "Apple M2 / M3", "RAM": "16 GB", "SSD": "512 GB"})
            ),
            (
                3,
                "Sony Headphones",
                "sony-headphones",
                "electronics",
                "Industry-leading noise canceling with dual noise sensor technology, high-res audio, and long battery life.",
                14999.0, 19999.0, 25, 4.7, 8920, 40,
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80",
                "Featured",
                json.dumps({"Battery Life": "30 Hours ANC on", "Driver": "30mm Precision", "Connectivity": "Bluetooth 5.2 / Multipoint"})
            ),
            (
                4,
                "Samsung TV",
                "samsung-tv",
                "electronics",
                "Crystal 4K Ultra HD Smart TV with Dynamic Crystal Color, HDR10+, and built-in voice assistants.",
                49999.0, 64999.0, 23, 4.6, 2150, 18,
                "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=600&auto=format&fit=crop&q=80",
                "Featured",
                json.dumps({"Display": "55-inch Crystal 4K UHD", "Resolution": "3840 x 2160", "HDR": "HDR10+", "Refresh Rate": "60Hz"})
            )
        ]

        for p in diagram_featured_products:
            cursor.execute("""
            INSERT INTO products (
                id, title, slug, category, description, price, original_price,
                discount_percent, rating, review_count, stock, image_url, badge, specs_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                slug=excluded.slug,
                category=excluded.category,
                price=excluded.price,
                original_price=excluded.original_price,
                image_url=excluded.image_url,
                badge=excluded.badge
            """, p)

        # Check if other products already exist
        cursor.execute("SELECT COUNT(*) as cnt FROM products")
        if cursor.fetchone()["cnt"] > 4:
            seed_vulnerabilities(conn=conn)
            conn.commit()
            return

        # Seed Comprehensive Product Catalog with Realistic Specs
        sample_products = [
            # Mobiles
            (
                "Apple iPhone 16 Pro (Desert Titanium, 256 GB)",
                "apple-iphone-16-pro-256gb",
                "mobiles",
                "Titanium design with larger 6.3-inch Super Retina XDR display, A18 Pro Bionic chip, Camera Control button, and 48MP Fusion camera with 5x telephoto optical zoom.",
                119900.0, 129900.0, 8, 4.8, 4210, 25,
                "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=600&auto=format&fit=crop&q=80",
                "Bestseller",
                json.dumps({"Display": "6.3-inch OLED 120Hz", "Processor": "A18 Pro", "Storage": "256 GB", "Camera": "48MP + 48MP + 12MP", "Battery": "3582 mAh"})
            ),
            (
                "Samsung Galaxy S24 Ultra 5G (Titanium Gray, 512 GB)",
                "samsung-galaxy-s24-ultra-512gb",
                "mobiles",
                "Galaxy AI powerhouse featuring titanium frame, built-in S Pen, Snapdragon 8 Gen 3 for Galaxy, 200MP Quad Telephoto camera with 100x Space Zoom.",
                129999.0, 144999.0, 10, 4.7, 3180, 18,
                "https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=600&auto=format&fit=crop&q=80",
                "Top Rated",
                json.dumps({"Display": "6.8-inch Dynamic AMOLED 2X", "Processor": "Snapdragon 8 Gen 3", "Storage": "512 GB", "Camera": "200MP + 50MP + 12MP + 10MP", "Battery": "5000 mAh"})
            ),
            (
                "OnePlus 12 5G (Flowy Emerald, 16GB RAM, 512GB)",
                "oneplus-12-5g-512gb",
                "mobiles",
                "Qualcomm Snapdragon 8 Gen 3, 4th Gen Hasselblad Camera for Mobile, 5400 mAh Battery with 100W SUPERVOOC fast charging and 50W AIRVOOC wireless.",
                64999.0, 69999.0, 7, 4.6, 2150, 30,
                "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=600&auto=format&fit=crop&q=80",
                "Hot Deal",
                json.dumps({"Display": "6.82-inch ProXDR 120Hz", "RAM": "16 GB", "Storage": "512 GB", "Battery": "5400 mAh", "Charging": "100W Fast Charge"})
            ),
            (
                "Google Pixel 9 Pro (Hazel, 128 GB)",
                "google-pixel-9-pro-128gb",
                "mobiles",
                "Engineered by Google with Gemini built-in, Tensor G4 processor, advanced 50MP triple rear camera system with 30x Super Res Zoom, and 24-hour battery life.",
                109999.0, 109999.0, 0, 4.7, 1420, 15,
                "https://images.unsplash.com/photo-1511707171634-5f897ff02560?w=600&auto=format&fit=crop&q=80",
                "Gemini AI",
                json.dumps({"Display": "6.3-inch Super Actua OLED", "Processor": "Google Tensor G4", "RAM": "16 GB", "Security": "Titan M2", "Camera": "50MP Triple System"})
            ),

            # Electronics & Laptops
            (
                "Apple MacBook Air M3 15-inch (Midnight, 16GB RAM, 512GB SSD)",
                "apple-macbook-air-m3-15-midnight",
                "electronics",
                "Strikingly thin design with fast M3 chip, up to 18 hours of battery life, Liquid Retina display, 1080p FaceTime HD camera, and six-speaker sound system.",
                134900.0, 144900.0, 7, 4.9, 1890, 14,
                "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop&q=80",
                "Editor's Choice",
                json.dumps({"Screen": "15.3-inch Liquid Retina", "Chip": "Apple M3 (8-core CPU / 10-core GPU)", "RAM": "16 GB Unified", "SSD": "512 GB", "Weight": "1.51 kg"})
            ),
            (
                "Dell XPS 15 OLED (Intel Core i9-13900H, 32GB RAM, 1TB SSD, RTX 4070)",
                "dell-xps-15-oled-rtx4070",
                "electronics",
                "Stunning 3.5K OLED InfinityEdge touch display, NVIDIA GeForce RTX 4070 graphics, CNC machined aluminum chassis with carbon fiber palm rest.",
                229990.0, 259990.0, 12, 4.6, 680, 8,
                "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=600&auto=format&fit=crop&q=80",
                "Pro Creator",
                json.dumps({"Display": "15.6-inch 3.5K OLED Touch", "CPU": "Intel Core i9 14-core", "GPU": "NVIDIA RTX 4070 8GB", "RAM": "32 GB DDR5", "SSD": "1 TB NVMe"})
            ),
            (
                "Sony PlayStation 5 Slim Console (1TB SSD, Digital Edition)",
                "sony-playstation-5-slim-digital",
                "electronics",
                "Ultra-high speed SSD with near instant load times, haptic feedback, adaptive triggers, 3D Audio, and incredible next-gen PlayStation gaming graphics.",
                44990.0, 49990.0, 10, 4.8, 5420, 22,
                "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=600&auto=format&fit=crop&q=80",
                "Trending",
                json.dumps({"Storage": "1 TB Custom NVMe", "Resolution": "Up to 4K 120Hz / 8K output", "Audio": "Tempest 3D AudioTech", "Ray Tracing": "Hardware Accelerated"})
            ),

            # Audio & Wearables
            (
                "Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
                "sony-wh-1000xm5-wireless-anc",
                "audio",
                "Industry-leading noise cancellation with two processors and 8 microphones, Auto NC Optimizer, crystal clear hands-free calling, up to 30-hour battery life.",
                26990.0, 34990.0, 23, 4.7, 8920, 40,
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80",
                "Best Seller",
                json.dumps({"Battery Life": "30 Hours ANC on", "Driver": "30mm precision engineered", "Connectivity": "Bluetooth 5.2 / Multipoint", "Codec": "LDAC, AAC, SBC"})
            ),
            (
                "Apple Watch Series 10 GPS (Jet Black Aluminum, 46mm)",
                "apple-watch-series-10-46mm-black",
                "audio",
                "Thinnest Apple Watch ever with the biggest wide-angle OLED display, sleep apnea notifications, faster charging, depth gauge, and water temperature sensor.",
                49900.0, 49900.0, 0, 4.8, 2140, 16,
                "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=600&auto=format&fit=crop&q=80",
                "New Release",
                json.dumps({"Case Size": "46 mm", "Display": "Wide-angle OLED Always-On", "Sensors": "ECG, SpO2, Temperature, Depth", "Water Resistance": "50m swimproof"})
            ),
            (
                "Apple AirPods Pro (2nd Generation with MagSafe Case USB-C)",
                "apple-airpods-pro-2nd-gen-usbc",
                "audio",
                "Up to 2x more Active Noise Cancellation, Adaptive Audio, Transparency mode, Personalized Spatial Audio with dynamic head tracking, and USB-C charging.",
                21990.0, 24900.0, 12, 4.8, 14200, 35,
                "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=600&auto=format&fit=crop&q=80",
                "Top Pick",
                json.dumps({"Chip": "Apple H2 headphone chip", "Battery": "Up to 6 hours (30 with case)", "Resistance": "IP54 dust, sweat, and water", "Charging": "USB-C & MagSafe"})
            ),

            # Fashion & Footwear
            (
                "Nike Air Jordan 1 Retro High OG (Chicago Lost & Found)",
                "nike-air-jordan-1-retro-high-og",
                "fashion",
                "Iconic vintage basketball silhouette crafted with premium aged leather, encapsulated Air cushioning, and authentic heritage color-blocking.",
                16995.0, 19995.0, 15, 4.9, 1240, 12,
                "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80",
                "Limited Drop",
                json.dumps({"Upper": "Full-grain genuine leather", "Midsole": "Encapsulated Air-Sole unit", "Outsole": "Solid rubber traction", "Origin": "Heritage Basketball"})
            ),
            (
                "Ray-Ban Classic Aviator Polarized Sunglasses (Gold Frame / Green Lens)",
                "ray-ban-classic-aviator-polarized",
                "fashion",
                "Originally designed for U.S. aviators in 1937, timeless gold metal frame with polarized G-15 crystal green lenses delivering 100% UV protection.",
                11590.0, 14290.0, 19, 4.6, 3100, 28,
                "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600&auto=format&fit=crop&q=80",
                "Timeless",
                json.dumps({"Frame Material": "Polished Metal Gold", "Lens Technology": "Polarized Classic G-15", "UV Protection": "100% UV400", "Size": "58-14-135"})
            ),

            # Home & Appliances
            (
                "Dyson V15 Detect Extra Cordless Vacuum Cleaner",
                "dyson-v15-detect-extra-cordless",
                "appliances",
                "Dyson's most powerful, intelligent cordless vacuum with laser illumination that reveals invisible dust, piezo sensor that sizes and counts particles, and up to 60 min runtime.",
                62900.0, 72900.0, 14, 4.7, 980, 15,
                "https://images.unsplash.com/photo-1558317374-067fb5f30001?w=600&auto=format&fit=crop&q=80",
                "Smart Clean",
                json.dumps({"Suction Power": "240 AW", "Filtration": "Whole-machine HEPA 99.99%", "Run Time": "Up to 60 minutes", "Weight": "3.0 kg"})
            ),
            (
                "Philips Digital Connected Airfryer XXL (7.2L Capacity, 16 Functions)",
                "philips-connected-airfryer-xxl-72l",
                "appliances",
                "Rapid CombiAir technology for juicy meats and crispy fries with up to 90% less fat. NutriU app integration with food probe and automated cooking programs.",
                17999.0, 22999.0, 22, 4.6, 4120, 20,
                "https://images.unsplash.com/photo-1585515320310-259814833e62?w=600&auto=format&fit=crop&q=80",
                "Deal of Day",
                json.dumps({"Capacity": "7.2 Liters (1.4 kg)", "Power": "2000 Watts", "Programs": "16 Preset Cooking Modes", "Connectivity": "Wi-Fi + NutriU App"})
            )
        ]

        for p in sample_products:
            cursor.execute("""
            INSERT OR IGNORE INTO products (
                title, slug, category, description, price, original_price,
                discount_percent, rating, review_count, stock, image_url, badge, specs_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, p)

        conn.commit()

    seed_vulnerabilities()


def seed_vulnerabilities(conn=None):
    """Seeds baseline vulnerabilities with patch proposals and regression test definitions."""
    should_close = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        should_close = True

    try:
        cursor = conn.cursor()
        vulnerabilities = [
            (
                "VULN-AUTH-001",
                "Lack of Application-Layer Rate Limiting on Login Endpoint",
                "Authentication Security",
                "HIGH",
                "CWE-307: Improper Restriction of Excessive Authentication Attempts",
                "T1110.001",
                "Credential Access (TA0006)",
                "shopsphere/api.py:/api/shop/auth/login",
                "AWAITING_APPROVAL",
                "Repeated failed authentication attempts against /api/shop/auth/login are not rate-limited natively in endpoint handler, allowing dictionary attacks unless mitigated by AutoHeal Sentinel sliding window.",
                "Enforce dynamic IP quarantine and sliding window threshold (max 5 failed logins / 60s) with 300s temporary quarantine.",
                """--- a/shopsphere/api.py\n+++ b/shopsphere/api.py\n@@ -102,6 +102,10 @@ def login(payload: LoginRequest, request: Request):\n+    # Enforce AutoHeal Sentinel rate limit gate\n+    if is_client_quarantined(client_ip):\n+        raise HTTPException(status_code=403, detail="IP address quarantined due to excessive failed attempts")""",
                "test_auth_burst_quarantine_enforcement",
                "PASSED",
                "PENDING"
            ),
            (
                "VULN-INJ-001",
                "Unescaped SQL Operators in Product Catalog Search Parameter",
                "Input Validation & Injection",
                "CRITICAL",
                "CWE-89: Improper Neutralization of Special Elements in SQL Command",
                "T1190",
                "Initial Access (TA0001)",
                "shopsphere/services.py:ProductService.list_products",
                "PATCHED_VERIFIED",
                "Search parameter 'q' accepts raw characters that can trigger syntax anomalies unless parameterized queries with parameterized placeholders are strictly enforced.",
                "Enforce parameterized SQL bindings (title LIKE ? OR description LIKE ?) across all catalog search queries.",
                """--- a/shopsphere/services.py\n+++ b/shopsphere/services.py\n@@ -140,7 +140,7 @@ class ProductService:\n-        query = f"SELECT * FROM products WHERE title LIKE '%{q}%'"\n+        query = "SELECT * FROM products WHERE title LIKE ? OR description LIKE ?"\n+        params.extend([f"%{q}%", f"%{q}%"])""",
                "test_sql_injection_tautology_sanitization",
                "PASSED",
                "APPROVED"
            ),
            (
                "VULN-FIN-001",
                "Unbounded Negative Delivery Arithmetic in Shopping Cart Logic",
                "Business Logic Integrity",
                "HIGH",
                "CWE-682: Incorrect Calculation",
                "T1499",
                "Impact (TA0040)",
                "shopsphere/services.py:CartService.calculate_cart_totals",
                "OPEN",
                "Cart calculation service allows negative delivery fee values (-999.0) if manipulated by injected logic, allowing checkout amounts below wholesale subtotal.",
                "Clamp delivery fee to minimum 0.0, apply ₹40 fee strictly for orders below ₹500, and assert final_total >= subtotal.",
                """--- a/shopsphere/services.py\n+++ b/shopsphere/services.py\n@@ -210,6 +210,7 @@ class CartService:\n+        delivery_fee = 0.0 if subtotal >= 500.0 else 40.0\n+        delivery_fee = max(0.0, delivery_fee)\n+        final_total = round(max(0.0, subtotal - discount + delivery_fee), 2)""",
                "test_cart_delivery_non_negative_invariant",
                "PENDING",
                "PENDING"
            ),
            (
                "VULN-RBAC-001",
                "Missing Role Verification on Internal Store Analytics Endpoint",
                "Access Control & Authorization",
                "HIGH",
                "CWE-862: Missing Authorization",
                "T1068",
                "Privilege Escalation (TA0004)",
                "shopsphere/api.py:/api/shop/admin/stats",
                "PATCHED_VERIFIED",
                "Administrative stats endpoint /api/shop/admin/stats relies on client role validation which could permit customer token access if role is unverified.",
                "Strict server-side JWT verification requiring role === 'admin' before returning sales/order metrics.",
                """--- a/shopsphere/api.py\n+++ b/shopsphere/api.py\n@@ -190,6 +190,8 @@ def get_admin_stats(user = Depends(get_current_user)):\n+    if not user or user.get("role") != "admin":\n+        raise HTTPException(status_code=403, detail="Admin role required")""",
                "test_unauthorized_admin_access_forbidden",
                "PASSED",
                "APPROVED"
            ),
            (
                "VULN-XSS-001",
                "Reflected Script Tags in Search Keyword Echo",
                "Input Validation & Sanitization",
                "MEDIUM",
                "CWE-79: Cross-Site Scripting",
                "T1059.007",
                "Execution (TA0002)",
                "shopsphere/services.py:ProductService",
                "PATCHED_VERIFIED",
                "Search query reflected in client response could trigger script execution in browsers if HTML escaping is bypassed.",
                "Sanitize search keywords with html.escape and enforce Content-Security-Policy header.",
                """--- a/shopsphere/services.py\n+++ b/shopsphere/services.py\n@@ -160,6 +160,7 @@ class ProductService:\n+    import html\n+    safe_q = html.escape(q)""",
                "test_xss_script_payload_neutralization",
                "PASSED",
                "APPROVED"
            )
        ]

        for v in vulnerabilities:
            cursor.execute("""
            INSERT OR IGNORE INTO vulnerabilities (
                vuln_id, title, category, severity, cwe_id, mitre_technique_id,
                mitre_tactic, component_path, status, description, remediation_proposal,
                patch_diff, regression_test_name, regression_test_status, approval_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, v)

        conn.commit()
    finally:
        if should_close:
            conn.close()
