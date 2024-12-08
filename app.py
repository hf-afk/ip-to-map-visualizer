import time
import random
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Initialize WebDriver with proper configurations
def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Safari/537.36")
    chrome_options.add_argument("--start-maximized")  # Show full browser window
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Uncomment to run in headless mode
    # chrome_options.add_argument("--headless=new")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    return driver

# Simulate human-like activity
def simulate_human_activity(driver, delay=3):
    actions = ActionChains(driver)
    for _ in range(random.randint(3, 6)):  # Random number of interactions
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1, 2))
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(random.uniform(1, 2))
        if random.choice([True, False]):
            links = driver.find_elements(By.TAG_NAME, "a")
            if links:
                random.choice(links).click()
                time.sleep(delay)
                driver.back()

# Fetch data from Cloudflare-protected website
def fetch_data_from_cloudflare(ip_address):
    driver = initialize_driver()
    url = f"https://www.iplocation.net/search?ie=UTF-8&q={ip_address}&sa=Search"

    try:
        driver.get(url)

        # Simulate human activity to bypass Cloudflare checks
        simulate_human_activity(driver)

        # Wait for Cloudflare verification to complete
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "some_identifier_after_cloudflare_check")))

        # Extract required data
        data_sections = driver.find_elements(By.CSS_SELECTOR, "div.col_12_of_12")
        data = []
        for section in data_sections:
            source = section.find_element(By.CSS_SELECTOR, "h4.geo-service a").text if section.find_elements(By.CSS_SELECTOR, "h4.geo-service a") else "N/A"
            country = section.find_element(By.CSS_SELECTOR, "span[class*='country']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='country']") else "N/A"
            region = section.find_element(By.CSS_SELECTOR, "span[class*='region']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='region']") else "N/A"
            city = section.find_element(By.CSS_SELECTOR, "span[class*='city']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='city']") else "N/A"
            data.append({"Source": source, "Country": country, "Region": region, "City": city})

        return data

    except Exception as e:
        st.error(f"Failed to bypass Cloudflare: {e}")
        return []
    finally:
        driver.quit()

# Streamlit app
def main():
    st.title("🌍 Cloudflare Bypass Test with Selenium")
    ip_address = st.text_input("Enter IP Address:")
    if st.button("Fetch Data"):
        if ip_address:
            with st.spinner("Fetching data..."):
                data = fetch_data_from_cloudflare(ip_address)
                if data:
                    st.write(data)
                else:
                    st.warning("No data retrieved!")
        else:
            st.warning("Please enter a valid IP address.")

if __name__ == "__main__":
    main()
