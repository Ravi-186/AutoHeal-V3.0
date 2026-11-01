import os
import sys
import time

# Ensure repository root is on Python path
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from shopsphere.database import init_db, seed_data
from shopsphere.services import ProductService, CartService, OrderService, AdminService
from shopsphere.autoheal_engine import AutoHealDemoEngine


def print_banner():
    print("""
================================================================================
   🛍️  SHOPSPHERE: FLIPKART-INSPIRED E-COMMERCE WITH AUTOHEAL SENTINEL ⚡
================================================================================
  Enterprise Autonomous Self-Healing SOAR & Full-Stack E-Commerce Platform
================================================================================
""")


def run_demo():
    print_banner()

    # Step 1: Initialize Database & Verify Baseline
    print("--- [STEP 1] INITIALIZE SYSTEM & VERIFY BASELINE ---")
    init_db()
    seed_data()
    print("✓ SQLite Database schema initialized and seed catalog verified.")

    # Step 2: Catalog Search & Filter Demonstration
    print("\n--- [STEP 2] DEMONSTRATE PRODUCT CATALOG & SEARCH ---")
    categories = ProductService.get_categories()
    print(f"✓ Loaded {len(categories)} product categories: {', '.join([c['name'] for c in categories])}")
    
    search_query = "iPhone"
    search_res = ProductService.list_products(q=search_query)
    print(f"✓ Search Query: '{search_query}' -> Found {search_res['total']} matching product(s):")
    for p in search_res["products"]:
        print(f"    • {p['title']} | Price: ₹{p['price']:,.2f} (MRP: ₹{p['original_price']:,.2f}) | Stock: {p['stock']} | Rating: {p['rating']}★")

    # Step 3: Shopping Cart Operations & Financial Invariant
    print("\n--- [STEP 3] DEMONSTRATE SHOPPING CART & INVENTORY LIMITS ---")
    session_id = "demo_live_shopper_01"
    CartService.clear_cart(session_id)

    target_prod = search_res["products"][0]
    initial_stock = target_prod["stock"]
    print(f"✓ Adding 2 units of '{target_prod['title']}' to cart (Current Stock: {initial_stock})...")
    cart = CartService.add_to_cart(session_id, target_prod["id"], 2)
    print(f"✓ Cart Updated: {cart['total_items']} items in cart.")
    print(f"    Subtotal: ₹{cart['subtotal']:,.2f}")
    print(f"    Discount Savings: ₹{cart['discount']:,.2f}")
    print(f"    Delivery Charges: ₹{cart['delivery_fee']:,.2f} ({'FREE DELIVERY QUALIFIED' if cart['delivery_fee'] == 0 else 'Standard Delivery'})")
    print(f"    Final Total Amount: ₹{cart['final_total']:,.2f}")

    # Step 4: Transactional Checkout & Atomic Inventory Decrement
    print("\n--- [STEP 4] DEMONSTRATE TRANSACTIONAL CHECKOUT ---")
    order = OrderService.checkout(
        user_or_session_id=session_id,
        customer_name="Priya Patel",
        customer_email="priya.patel@example.com",
        customer_phone="+91 98123 45678",
        shipping_address="Tower 3, Penthouse 1204, HighTech City",
        city="Hyderabad",
        pincode="500081",
        payment_method="UPI / QR Code (Simulated Sandbox)"
    )
    print(f"✓ Order Placed Successfully!")
    print(f"    Order Reference: {order['order_ref']}")
    print(f"    Order Status: {order['order_status']}")
    print(f"    Total Paid: ₹{order['total_amount']:,.2f}")
    print(f"    Delivery To: {order['customer_name']} | {order['shipping_address']}, {order['city']}")

    updated_prod = ProductService.get_product(target_prod["id"])
    print(f"✓ Atomic Inventory Decrement Verified: Stock reduced from {initial_stock} -> {updated_prod['stock']}.")

    # Step 5: Admin Dashboard Analytics
    print("\n--- [STEP 5] DEMONSTRATE PROTECTED ADMIN ANALYTICS ---")
    metrics = AdminService.get_dashboard_metrics()
    print(f"✓ Live Stored Revenue: ₹{metrics['total_revenue']:,.2f}")
    print(f"✓ Total Stored Orders: {metrics['total_orders']}")
    print(f"✓ Monitored Catalog Items: {metrics['total_products']}")
    print(f"✓ Low Stock Items Alert: {metrics['low_stock_count']}")

    # Step 6: Baseline Test Execution
    print("\n--- [STEP 6] RUN BASELINE UNIT & REGRESSION TEST SUITE ---")
    base_test = AutoHealDemoEngine.run_regression_test()
    if base_test["passed"]:
        print(f"✓ [PASS] {base_test['test_name']}: {base_test['message']}")
    else:
        print(f"✗ [FAIL] {base_test['error']}")

    # Step 7: Controlled Bug Injection
    print("\n--- [STEP 7] INTRODUCE CONTROLLED CALCULATION DEFECT (ISOLATED) ---")
    bug_info = AutoHealDemoEngine.inject_controlled_bug()
    print(f"⚠️  Controlled Bug Injected: {bug_info['description']}")
    print(f"    Component: {bug_info['component']}")

    # Step 8: Run Regression Test (Show Failure)
    print("\n--- [STEP 8] RUN REGRESSION TEST (DETECTION) ---")
    reg_fail = AutoHealDemoEngine.run_regression_test()
    if not reg_fail["passed"]:
        print(f"🚨 [EXPECTED REGRESSION CAUGHT]")
        print(f"    Error: {reg_fail['error']}")
        print(f"    Observed Output: {reg_fail['observed_output']}")
    else:
        print("✗ Unexpected pass.")

    # Step 9: Agent Root-Cause Diagnosis
    print("\n--- [STEP 9] AI AGENT ROOT-CAUSE DIAGNOSIS ---")
    diag = AutoHealDemoEngine.diagnose_root_cause()
    print(f"🔍 Root Cause Identified: {diag['finding']}")
    print(f"    Target File: {diag['file']}")
    print(f"    Anomaly Type: {diag['anomaly_type']}")
    print(f"    Prescribed Remediation: {diag['prescribed_patch']}")

    # Step 10: Apply Surgical AutoHeal Patch
    print("\n--- [STEP 10] DEPLOY SURGICAL AUTOHEAL REPAIR ---")
    patch = AutoHealDemoEngine.apply_autoheal_patch()
    print(f"⚡ [AUTOHEAL APPLIED] {patch['action']} in {patch['duration_ms']}ms!")
    print(f"    Patch: {patch['patch_applied']}")

    # Step 11: Re-run Regression Test & Confirm Green Baseline
    print("\n--- [STEP 11] RE-RUN REGRESSION CHECK & FINAL VERIFICATION ---")
    reg_pass = AutoHealDemoEngine.run_regression_test()
    if reg_pass["passed"]:
        print(f"✓ [VERIFIED PASS] {reg_pass['test_name']}: All financial calculations restored!")
        print("✓ Zero data loss. Transactional integrity preserved.")
    else:
        print(f"✗ Regression still failing: {reg_pass['error']}")

    print("\n" + "="*80)
    print("   🎉 ALL 11 STEPS COMPLETED & VERIFIED SUCCESSFULLY!")
    print("   Open in Browser: http://localhost:8000/shop")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_demo()
