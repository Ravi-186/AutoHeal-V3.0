import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "AutoHeal_Documentation", "screenshots")

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1600,1050")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)

try:
    # 1. Incident Reports Page
    print("Capturing Incident Reports page...")
    driver.get("http://localhost:8000")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "pageOverview")))
    time.sleep(2)
    # click pageReports tab
    reports_tab = driver.find_element(By.CSS_SELECTOR, "button[data-page='pageReports']")
    driver.execute_script("arguments[0].click();", reports_tab)
    time.sleep(2)
    driver.save_screenshot(os.path.join(SCREENSHOTS_DIR, "screenshot_09_incident_reports.png"))

    # 2. Healing & Remediation with Active Demo Log
    print("Capturing Active Code Remediation Demo...")
    driver.get("http://localhost:8000")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "pageOverview")))
    time.sleep(1)
    healing_tab = driver.find_element(By.CSS_SELECTOR, "button[data-page='pageHealing']")
    driver.execute_script("arguments[0].click();", healing_tab)
    time.sleep(1)
    # Trigger AI Diagnosis or Full Autonomous Demo
    demo_btn = driver.find_elements(By.XPATH, "//button[contains(text(), 'Full Autonomous Demo') or contains(text(), 'AI Diagnosis')]")
    if demo_btn:
        driver.execute_script("arguments[0].click();", demo_btn[0])
        time.sleep(3)
    driver.save_screenshot(os.path.join(SCREENSHOTS_DIR, "screenshot_10_remediation_active.png"))

    # 3. Streamlit 3D SOC Dashboard with adequate wait
    print("Capturing Streamlit 3D SOC Dashboard...")
    driver.get("http://localhost:8501")
    # Streamlit can take 6-10 seconds to compile and render
    time.sleep(12)
    driver.save_screenshot(os.path.join(SCREENSHOTS_DIR, "screenshot_11_streamlit_dashboard.png"))

    print("Additional real screenshots captured successfully!")

finally:
    driver.quit()
