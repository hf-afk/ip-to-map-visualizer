import streamlit as st
import pandas as pd
import folium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from io import BytesIO
import base64
from tabulate import tabulate

# Function to get IP geolocation data from all sections on the page
def get_ip_data(ip_address):
    # Set up Chrome options for Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    url = f"https://www.iplocation.net/search?cx=partner-pub-1026064395378929%3A2796854705&cof=FORID%3A10&ie=UTF-8&q={ip_address}&sa=Search"
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    ip_data_list = []
    try:
        data_sections = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.col_12_of_12"))
        )

        for section in data_sections:
            source = section.find_element(By.CSS_SELECTOR, "h4.geo-service a").text if section.find_elements(By.CSS_SELECTOR, "h4.geo-service a") else "N/A"
            if source != 'N/A':
                data = {
                    "IP Address": ip_address,
                    "Source": source,
                    "Country": section.find_element(By.CSS_SELECTOR, "span[class*='country']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='country']") else "N/A",
                    "Region": section.find_element(By.CSS_SELECTOR, "span[class*='region']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='region']") else "N/A",
                    "City": section.find_element(By.CSS_SELECTOR, "span[class*='city']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='city']") else "N/A",
                    "Latitude": section.find_element(By.CSS_SELECTOR, "span[class*='lat']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='lat']") else "N/A",
                    "Longitude": section.find_element(By.CSS_SELECTOR, "span[class*='long']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='long']") else "N/A"
                }
                ip_data_list.append(data)
    except Exception as e:
        st.error(f"Error retrieving data for IP {ip_address}: {e}")
    finally:
        driver.quit()

    return ip_data_list

# Function to generate a map from geolocation data
def generate_map(df):
    df = df[df["Latitude"] != "N/A"]
    df["Latitude"] = df["Latitude"].astype(float)
    df["Longitude"] = df["Longitude"].astype(float)

    map_center = [df["Latitude"].mean(), df["Longitude"].mean()]
    ip_map = folium.Map(location=map_center, zoom_start=5)

    for _, row in df.iterrows():
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=(f"IP: {row['IP Address']}<br>Source: {row['Source']}<br>"
                   f"Country: {row['Country']}<br>Region: {row['Region']}<br>"
                   f"City: {row['City']}"),
            tooltip=row['IP Address'],
        ).add_to(ip_map)

    return ip_map

# Streamlit App
def main():
    st.title("🌍 IP Geolocation Tracker")
    st.markdown("Enter IP addresses to fetch their geolocation data and view it on a map.")
    
    ip_addresses = st.text_area("Enter IP addresses (comma-separated):")
    if st.button("Fetch Geolocation"):
        if ip_addresses:
            with st.spinner("Fetching data..."):
                ip_list = [ip.strip() for ip in ip_addresses.split(",")]
                all_ip_data = []

                for ip in ip_list:
                    ip_data_list = get_ip_data(ip)
                    all_ip_data.extend(ip_data_list)

                if all_ip_data:
                    df = pd.DataFrame(all_ip_data)
                    st.success("Geolocation data fetched successfully!")

                    # Display data table
                    st.subheader("Geolocation Data")
                    st.dataframe(df)

                    # Downloadable CSV
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="Download Data as CSV",
                        data=csv,
                        file_name="ip_geolocation_data.csv",
                        mime="text/csv",
                    )

                    # Generate and display the map
                    ip_map = generate_map(df)
                    map_html = ip_map._repr_html_()
                    st.components.v1.html(map_html, height=600)

                    # Downloadable HTML map
                    map_buffer = BytesIO()
                    ip_map.save(map_buffer, close_file=False)
                    map_buffer.seek(0)
                    st.download_button(
                        label="Download Map as HTML",
                        data=map_buffer,
                        file_name="ip_geolocation_map.html",
                        mime="text/html",
                    )
                else:
                    st.error("No data retrieved. Please check the IP addresses.")
        else:
            st.warning("Please enter at least one IP address.")

if __name__ == "__main__":
    main()
