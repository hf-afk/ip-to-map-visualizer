import streamlit as st
import pandas as pd
import folium
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from io import BytesIO
import time
import random

# Function to initialize the driver
def initialize_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.70 Safari/537.36")
    options.add_argument("--headless=new")  # Use `new` headless mode
    driver = uc.Chrome(options=options)
    return driver

# Function to simulate random human-like activity
def simulate_human_activity(driver, delay=3):
    actions = ActionChains(driver)
    for _ in range(random.randint(2, 5)):  # Random number of interactions
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

# Function to handle cookies
def inject_cookies(driver, cookies):
    for cookie in cookies:
        driver.add_cookie(cookie)

# Function to get IP geolocation data
def get_ip_data(ip_address):
    driver = initialize_driver()

    # Define the target URL
    url = f"https://www.iplocation.net/search?ie=UTF-8&q={ip_address}&sa=Search"
    driver.get(url)

    # Simulate human activity to pass Cloudflare checks
    simulate_human_activity(driver)

    # Wait for Cloudflare check to complete
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.col_12_of_12")))
    except Exception as e:
        st.error(f"Cloudflare verification failed: {e}")
        driver.quit()
        return []

    # Extract geolocation data
    ip_data_list = []
    try:
        data_sections = driver.find_elements(By.CSS_SELECTOR, "div.col_12_of_12")

        for section in data_sections:
            source = section.find_element(By.CSS_SELECTOR, "h4.geo-service a").text if section.find_elements(By.CSS_SELECTOR, "h4.geo-service a") else "N/A"
            if source != "N/A":
                data = {
                    "Source": source,
                    "Country": section.find_element(By.CSS_SELECTOR, "span[class*='country']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='country']") else "N/A",
                    "Region": section.find_element(By.CSS_SELECTOR, "span[class*='region']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='region']") else "N/A",
                    "City": section.find_element(By.CSS_SELECTOR, "span[class*='city']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='city']") else "N/A",
                    "ISP": section.find_element(By.CSS_SELECTOR, "span[class*='isp']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='isp']") else "N/A",
                    "Organization": section.find_element(By.CSS_SELECTOR, "span[class*='org']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='org']") else "N/A",
                    "Latitude": section.find_element(By.CSS_SELECTOR, "span[class*='lat']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='lat']") else "N/A",
                    "Longitude": section.find_element(By.CSS_SELECTOR, "span[class*='long']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='long']") else "N/A",
                }
                ip_data_list.append(data)

    except Exception as e:
        st.error(f"Error retrieving data for IP {ip_address}: {e}")
    finally:
        driver.quit()

    return ip_data_list

# Function to generate table and map
def generate_table_and_map(ip_address):
    ip_data_list = get_ip_data(ip_address)
    df = pd.DataFrame(ip_data_list)

    if not df.empty:
        # Rename for CSV export
        df_csv = df.rename(columns={"Latitude": "Latitude (Decimal)", "Longitude": "Longitude (Decimal)"})
        df_csv.columns = [f"Geolocation Data for {ip_address}" if col == "Source" else col for col in df_csv.columns]

        # Display table
        st.subheader(f"Geolocation Data for {ip_address}")
        st.dataframe(df)

        # Export to CSV
        csv_data = df_csv.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Geolocation Data (CSV)",
            data=csv_data,
            file_name=f"{ip_address}_geolocation.csv",
            mime="text/csv",
        )

        # Generate Map
        df = df[df["Latitude"].apply(lambda x: x != "N/A") & df["Longitude"].apply(lambda x: x != "N/A")]
        df["Latitude"] = df["Latitude"].astype(float)
        df["Longitude"] = df["Longitude"].astype(float)

        map_center = [df["Latitude"].mean(), df["Longitude"].mean()]
        ip_map = folium.Map(location=map_center, zoom_start=11)

        for _, row in df.iterrows():
            folium.Marker(
                location=[row["Latitude"], row["Longitude"]],
                popup=(f"Source: {row['Source']}<br>Country: {row['Country']}<br>"
                       f"Region: {row['Region']}<br>City: {row['City']}<br>"
                       f"ISP: {row['ISP']}<br>Organization: {row['Organization']}"),
                tooltip=f"{row['Source']} - {row['Country']}",
            ).add_to(ip_map)

        map_buffer = BytesIO()
        ip_map.save(map_buffer, close_file=False)
        map_html = map_buffer.getvalue().decode()

        st.subheader("Geolocation Map")
        st.components.v1.html(map_html, height=500)
        st.download_button(
            label="Download Map (HTML)",
            data=map_html,
            file_name=f"{ip_address}_map.html",
            mime="text/html",
        )
    else:
        st.warning(f"No geolocation data found for {ip_address}.")

# Streamlit app
def main():
    st.title("🌍 IP Geolocation Tracker")
    st.markdown("Enter an IP address to fetch its geolocation data and visualize it on a map.")

    ip_address = st.text_input("Enter IP Address:")
    if st.button("Fetch Geolocation"):
        if ip_address:
            with st.spinner(f"Fetching geolocation data for {ip_address}..."):
                generate_table_and_map(ip_address)
        else:
            st.warning("Please enter a valid IP address.")

def add_footer():
    footer = """
    <style>
        .footer {
            position: fixed;
            bottom: 0;
            right: 0;
            width: 100%;
            text-align: left;
            font-size: 12px;
            padding: 10px;
            color: #777;
        }
    </style>
    <div class="footer">
        © 2024 Made with 💚 by AZIZ.
    </div>
    """
    st.markdown(footer, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    add_footer()
