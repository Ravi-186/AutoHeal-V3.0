import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1600,1050")
options.add_argument("--enable-webgl")
options.add_argument("--ignore-gpu-blocklist")

driver = webdriver.Chrome(options=options)
try:
    driver.get("http://localhost:8501")
    time.sleep(8)
    print("Page title:", driver.title)
    elements = driver.find_elements("tag name", "h1")
    print("H1 elements:", [e.text for e in elements])
    driver.save_screenshot("AutoHeal_Documentation/screenshots/screenshot_10_streamlit_soc.png")
    print("Screenshot saved, size:", os.path.getsize("AutoHeal_Documentation/screenshots/screenshot_10_streamlit_soc.png"))
finally:
    driver.quit()
