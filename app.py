import streamlit as st
import pandas as pd
import folium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from io import BytesIO

# Function to get IP geolocation data from all sections on the page
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
        ip_map = folium.Map(location=map_center, zoom_start=8)
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
    st.title("🌍📍 IP Geolocation Tracker")
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
        /* Position the footer */
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
