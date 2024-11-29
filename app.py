import streamlit as st
import pandas as pd
import folium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from streamlit_folium import st_folium
from io import BytesIO

# Function to get IP geolocation data
def get_ip_data(ip_address):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    url = f"https://www.iplocation.net/search?cx=partner-pub-1026064395378929%3A2796854705&cof=FORID%3A10&ie=UTF-8&q={ip_address}&sa=Search"
    ip_data_list = []

    try:
        driver.get(url)
        data_sections = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.col_12_of_12"))
        )
        for section in data_sections:
            source = section.find_element(By.CSS_SELECTOR, "h4.geo-service a").text if section.find_elements(By.CSS_SELECTOR, "h4.geo-service a") else "N/A"
            if source != 'N/A':
                data = {
                    f"Geolocation Data for {ip_address}": ip_address,
                    "Source": source,
                    "Country": section.find_element(By.CSS_SELECTOR, "span[class*='country']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='country']") else "N/A",
                    "Region": section.find_element(By.CSS_SELECTOR, "span[class*='region']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='region']") else "N/A",
                    "City": section.find_element(By.CSS_SELECTOR, "span[class*='city']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='city']") else "N/A",
                    "ISP": section.find_element(By.CSS_SELECTOR, "span[class*='isp']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='isp']") else "N/A",
                    "Organization": section.find_element(By.CSS_SELECTOR, "span[class*='org']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='org']") else "N/A",
                    "Latitude": section.find_element(By.CSS_SELECTOR, "span[class*='lat']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='lat']") else "N/A",
                    "Longitude": section.find_element(By.CSS_SELECTOR, "span[class*='long']").text if section.find_elements(By.CSS_SELECTOR, "span[class*='long']") else "N/A"
                }
                ip_data_list.append(data)
    except Exception as e:
        st.error(f"Error retrieving data for IP {ip_address}: {e}")
    finally:
        driver.quit()
    return ip_data_list

# Streamlit App
def main():
    st.title("IP Geolocation Tracker")
    st.markdown("Enter a list of IP addresses to fetch their geolocation data and visualize it on a map.")
    ip_addresses = st.text_input("Enter IP addresses (comma-separated):")
    if st.button("Fetch Data"):
        if ip_addresses:
            with st.spinner("Fetching geolocation data..."):
                ip_list = [ip.strip() for ip in ip_addresses.split(",")]
                all_ip_data = []
                for ip in ip_list:
                    ip_data_list = get_ip_data(ip)
                    all_ip_data.extend(ip_data_list)
                
                df = pd.DataFrame(all_ip_data)
                if not df.empty:
                    st.subheader("Geolocation Data Table")
                    st.dataframe(df, use_container_width=True)

                    # CSV Download
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Geolocation Data (CSV)",
                        data=csv,
                        file_name="geolocation_data.csv",
                        mime="text/csv"
                    )

                    # Generate Map
                    df = df[df["Latitude"].apply(lambda x: x != "N/A") & df["Longitude"].apply(lambda x: x != "N/A")]
                    df["Latitude"] = df["Latitude"].astype(float)
                    df["Longitude"] = df["Longitude"].astype(float)
                    map_center = [df["Latitude"].mean(), df["Longitude"].mean()]
                    ip_map = folium.Map(location=map_center, zoom_start=8)

                    for _, row in df.iterrows():
                        folium.Marker(
                            [row["Latitude"], row["Longitude"]],
                            popup=(f"IP: {row[f'Geolocation Data for {row[f'Geolocation Data for {ip_list[0]}']}']}<br>"
                                   f"Source: {row['Source']}<br>Country: {row['Country']}<br>"
                                   f"Region: {row['Region']}<br>City: {row['City']}<br>"
                                   f"ISP: {row['ISP']}<br>Organization: {row['Organization']}"),
                            tooltip=f"{row['Source']} - {row[f'Geolocation Data for {ip_list[0]}']}"
                        ).add_to(ip_map)
                    
                    # Display Map
                    st.subheader("Geolocation Map")
                    map_html = ip_map._repr_html_()
                    st_folium(ip_map, width=800, height=400)

                    # HTML Download
                    map_buffer = BytesIO()
                    ip_map.save(map_buffer, close_file=False)
                    st.download_button(
                        label="Download Map (HTML)",
                        data=map_buffer.getvalue(),
                        file_name="ip_geolocation_map.html",
                        mime="text/html"
                    )
                else:
                    st.warning("No data available. Please check the IP addresses and try again.")
        else:
            st.warning("Please enter at least one IP address.")

if __name__ == "__main__":
    main()
