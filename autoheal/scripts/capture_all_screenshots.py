"""
Capture Genuine Project Screenshots for AutoHeal Documentation
"""
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

OUTPUT_DIR = r"C:\Users\bobba\Documents\AD\autoheal\AutoHeal_Documentation\screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

options = Options()
options.add_argument('--headless=new')
options.add_argument('--window-size=1600,1050')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--hide-scrollbars')

driver = webdriver.Chrome(options=options)

try:
    # 1. ShopSphere E-Commerce Storefront
    print("Capturing 1: ShopSphere Storefront...")
    driver.get("http://localhost:8000/shop")
    time.sleep(2)
    driver.save_screenshot(os.path.join(OUTPUT_DIR, "screenshot_01_shopsphere_storefront.png"))

    # 2. AutoHeal SOC Dashboard Overview
    print("Capturing 2: AutoHeal SOC Overview...")
    driver.get("http://localhost:8000/")
    time.sleep(2)
    driver.save_screenshot(os.path.join(OUTPUT_DIR, "screenshot_02_autoheal_overview.png"))

    # 3. Attack Center Tab
    print("Capturing 3: Attack Center...")
    try:
        btn = driver.find_element(By.CSS_SELECTOR, "button[data-page='pageAttackCenter']")
        btn.click()
        time.sleep(1.5)
    except Exception as e:
        print("Tab switch error:", e)
    driver.save_screenshot(os.path.join(OUTPUT_DIR, "screenshot_03_attack_center.png"))

    # 4. Attack Execution Result in Attack Center
    print("Capturing 4: Attack Execution...")
    try:
        launch_btn = driver.find_element(By.ID, "btnLaunchAttack")
        launch_btn.click()
        time.sleep(4)  # Wait for attack requests to complete
    except Exception as e:
        print("Launch button error:", e)
    driver.save_screenshot(os.path.join(OUTPUT_DIR, "screenshot_04_attack_execution.png"))

    # 5. Live Security Events Stream
    print("Capturing 5: Live Security Events...")
    try:
        btn = driver.find_element(By.CSS_SELECTOR, "button[data-page='pageEvents']")
        btn.click()
        time.sleep(1.5)
    except Exception as e:
        print("Tab switch error:", e)
    driver.save_screenshot(os.path.join(OUTPUT_DIR, "screenshot_05_live_events.png"))

    # 6. Incident Details & Forensic Workspace
    print("Capturing 6: Incident Details & Forensics...")
    try:
        btn = driver.find_element(By.CSS_SELECTOR, "button[data-page='pageIncidents']")
        btn.click()
        time.sleep(1.5)
    except Exception as e:
        print("Tab switch error:", e)
    driver.save_screenshot(os.path.join(OUTPUT_DIR, "screenshot_06_incident_forensics.png"))

    # 7. Healing & Vulnerability Remediation Hub
    print("Capturing 7: Healing & Vulnerability Remediation...")
    try:
        btn = driver.find_element(By.CSS_SELECTOR, "button[data-page='pageHealing']")
        btn.click()
        time.sleep(1.5)
    except Exception as e:
        print("Tab switch error:", e)
    driver.save_screenshot(os.path.join(OUTPUT_DIR, "screenshot_07_vulnerability_remediation.png"))

    # 8. System Health Tab
    print("Capturing 8: System Health & Sentinel Status...")
    try:
        btn = driver.find_element(By.CSS_SELECTOR, "button[data-page='pageHealth']")
        btn.click()
        time.sleep(1.5)
    except Exception as e:
        print("Tab switch error:", e)
    driver.save_screenshot(os.path.join(OUTPUT_DIR, "screenshot_08_system_health.png"))

    # 9. Streamlit Multi-Agent & 3D Network Topology
    print("Capturing 9: Streamlit SOC Dashboard...")
    driver.get("http://localhost:8501/")
    time.sleep(4)  # Wait for Streamlit components to hydrate
    driver.save_screenshot(os.path.join(OUTPUT_DIR, "screenshot_09_streamlit_3d_soc.png"))

    print("ALL REAL SCREENSHOTS CAPTURED SUCCESSFULLY!")

finally:
    driver.quit()
