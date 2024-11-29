import pandas as pd
import folium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import streamlit as st
from io import BytesIO

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

    except Exception as e:
        st.error(f"Error retrieving data for IP {ip_address}: {e}")
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
        try:
            lat, lon = float(row["Latitude"]), float(row["Longitude"])
            folium.Marker(
                [lat, lon],
                popup=(f"Source: {row['Source']}<br>"
                       f"Country: {row['Country']}<br>Region: {row['Region']}<br>"
                       f"City: {row['City']}<br>ISP: {row['ISP']}<br>Organization: {row['Organization']}"),
                tooltip=f"{row['Source']}",
                icon=folium.Icon(color="blue")
            ).add_to(ip_map)
        except ValueError:
            pass

    return ip_map

# Streamlit App
def main():
    st.title("🌍 IP Geolocation Tracker")
    st.markdown("Enter IP addresses to fetch and visualize geolocation data.")

    ip_addresses = st.text_area("Enter IP addresses (comma-separated):", "").split(",")
    if st.button("Fetch Geolocation Data"):
        ip_addresses = [ip.strip() for ip in ip_addresses if ip.strip()]
        if ip_addresses:
            with st.spinner("Fetching data..."):
                all_ip_data = []
                for ip in ip_addresses:
                    ip_data_list = get_ip_data(ip)
                    all_ip_data.extend(ip_data_list)

                if all_ip_data:
                    df = pd.DataFrame(all_ip_data)

                    # Display table
                    st.subheader("Geolocation Data")
                    st.dataframe(df)

                    # Prepare CSV for download
                    df_csv = df.drop(columns=["Latitude", "Longitude"])
                    csv_content = df_csv.to_csv(index=False, header=[f"Geolocation Data for {ip_addresses[0]}"]).encode('utf-8')
                    st.download_button(
                        label="Download Data (CSV)",
                        data=csv_content,
                        file_name="geolocation_data.csv",
                        mime="text/csv"
                    )

                    # Generate and display map
                    st.subheader("Geolocation Map")
                    ip_map = generate_map(df)
                    map_file = BytesIO()
                    ip_map.save(map_file, close_file=False)
                    map_html = map_file.getvalue().decode()
                    st.components.v1.html(map_html, height=500)

                    # Download map as HTML
                    st.download_button(
                        label="Download Map (HTML)",
                        data=map_file.getvalue(),
                        file_name="ip_geolocation_map.html",
                        mime="text/html"
                    )
                else:
                    st.warning("No data found for the entered IP addresses.")
        else:
            st.warning("Please enter at least one IP address.")

if __name__ == "__main__":
    main()
