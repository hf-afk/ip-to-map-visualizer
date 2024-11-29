import pandas as pd
import folium
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64

# Function to get IP geolocation data
def get_ip_data(ip_address):
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
    finally:
        driver.quit()
    return ip_data_list

# Function to generate map
def generate_map(df):
    df = df[df["Latitude"].apply(lambda x: x != "N/A") & df["Longitude"].apply(lambda x: x != "N/A")]
    df["Latitude"] = df["Latitude"].astype(float)
    df["Longitude"] = df["Longitude"].astype(float)

    map_center = [df["Latitude"].mean(), df["Longitude"].mean()]
    ip_map = folium.Map(location=map_center, zoom_start=8)

    for _, row in df.iterrows():
        lat, lon = row["Latitude"], row["Longitude"]
        folium.Marker(
            [lat, lon],
            popup=(f"Source: {row['Source']}<br>Country: {row['Country']}<br>"
                   f"Region: {row['Region']}<br>City: {row['City']}<br>"
                   f"ISP: {row['ISP']}<br>Organization: {row['Organization']}"),
            tooltip=f"{row['Source']}",
            icon=folium.Icon(color="blue")
        ).add_to(ip_map)

    return ip_map

# Function to download HTML file
def download_html(map_object):
    html_data = map_object.get_root().render()
    b64 = base64.b64encode(html_data.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="ip_geolocation_map.html">Download Map as HTML</a>'

# Streamlit app
def main():
    st.title("🌍 IP Geolocation Data Viewer")
    st.markdown("Enter IP addresses separated by commas to fetch geolocation data.")
    
    ip_addresses = st.text_area("Enter IP addresses:", placeholder="E.g., 8.8.8.8, 1.1.1.1").split(",")
    ip_addresses = [ip.strip() for ip in ip_addresses if ip.strip()]

    if st.button("Fetch Geolocation Data"):
        if ip_addresses:
            with st.spinner("Fetching data..."):
                all_data = []
                for ip in ip_addresses:
                    all_data.extend(get_ip_data(ip))
                
                if all_data:
                    df = pd.DataFrame(all_data)
                    
                    # Display table with ISP and Organization columns
                    st.subheader("Geolocation Data Table")
                    st.dataframe(df)

                    # Prepare and download CSV
                    csv_header = f"Geolocation Data for {', '.join(ip_addresses)}\n"
                    csv_data = csv_header + df.to_csv(index=False)
                    st.download_button(
                        label="Download Data (CSV)",
                        data=csv_data.encode('utf-8'),
                        file_name="ip_geolocation_data.csv",
                        mime="text/csv"
                    )

                    # Generate map
                    st.subheader("Geolocation Map")
                    ip_map = generate_map(df)

                    # Render map in Streamlit
                    map_html = ip_map._repr_html_()
                    st.components.v1.html(map_html, height=500)

                    # Align download button below map
                    st.markdown(download_html(ip_map), unsafe_allow_html=True)
                else:
                    st.warning("No geolocation data found for the provided IP addresses.")
        else:
            st.error("Please enter at least one IP address.")

if __name__ == "__main__":
    main()
