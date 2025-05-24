from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_argument("--headless")
options.add_argument("--window-size=1920,1080")  # Increase window size for better quality
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Use Chrome by default on Windows
driver = webdriver.Chrome(options=options)

try:
    # Open OKX WIF/USDC trading page
    driver.get("https://www.okx.com/trade-spot/wif-usdc")
    
    # Wait for the page to load
    time.sleep(7)  # Let the page fully load
    
    # Find all iframes on the page
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"Found iframes: {len(iframes)}")
    if len(iframes) == 0:
        raise Exception("No iframes found on the page!")

    # Switch to the first iframe (most likely the chart)
    driver.switch_to.frame(iframes[0])
    time.sleep(2)  # Ждем подгрузки содержимого iframe

    # Делаем скриншот всего содержимого iframe
    driver.save_screenshot("okx_chart_iframe.png")
    print("Скриншот графика (iframe) сохранен в okx_chart_iframe.png")
    
except Exception as e:
    print(f"Произошла ошибка: {e}")
    
finally:
    driver.quit() 