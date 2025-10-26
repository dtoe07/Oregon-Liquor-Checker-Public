# Liquor Availability Bot Scraper for Oregon Liquor Stores
# Purpose: Automates the search for specific liquor availability in Oregon liquor stores.
# Author: Dinh Nguyen (dtoe07@gmail.com)
# Date Created: January 7, 2021

import os
import requests
from bs4 import BeautifulSoup
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
from random import randint
import re
import datetime
import folium
from geopy.geocoders import Nominatim

# Load environment variables for email credentials
login_email = os.getenv("LOGIN_EMAIL")
access_token = os.getenv("ACCESS_TOKEN")

# List of Recipients
addr_to = ['recipient-email-here', 'recipient-email-here'] # Add more emails or phone numbers here

# List of url to the maps to be appended to the end of the email
map_urls = []

# List of the liquor to be searched
item_list = [
    ('8722B', 'Red Weller'),
    ('8954B', 'Green Weller'),
    ('1562B', 'W.L. WELLER 12YR KENTUCKY STRAIGHT BRBN'),
    ('6374B', 'WELLER FULL PROOF'),
    ('11941B', 'WELLER FULL PROOF SINGLE BARREL SELECT'),

    ('8119B', 'SUNTORY HIBIKI 12YR'),
    # ('7634B', 'SUNTORY YAMAZAKI 18 YR'),

    ('0191B', 'Stagg JR.'),
    ('2146B', "WOODFORD RES. MC BOURBON"),
    ('3749B', "BLOOD OATH PACT VII"),
    ('2893B', "HIGH WEST MIDWINTER"),
    ('2657B ', "MICHTER'S TOASTED BARREL FINISH"),

    ('0793B ', "E.H. TAYLOR SINGLE BARREL STRAIGHT BOURB"),
    ('1416B ', "E.H. TAYLOR JR BARREL PROOF"),
    ('1418B ', "E.H. TAYLOR STRAIGHT RYE WHISKEY"),

    ('5830B', 'TEQUILA FORTALEZA BLANCO'),
    ('5831B', 'TEQUILA FORTALEZA REPOSADO'),
    ('5829B', 'TEQUILA FORTALEZA Anejo'),

    ('2160B', 'EAGLE RARE S/B BOURBON')
    # Add more items here...
]

# Browser User Agents to randomize browser for the bot
user_agent_list = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
]
    
def main():
    # Set up a session with a random user-agent
    user_agent = random.choice(user_agent_list)
    session = requests.Session()
    session.headers.update({'User-Agent': user_agent})

    # Try to establish connection to www.oregonliquorsearch.com
    try:
        session.post("http://www.oregonliquorsearch.com/servlet/WelcomeController", timeout=10)
    except requests.RequestException as e:
        print(f"Failed to establish session: {e}")
        return

    # Randomize the liquor list
    random.shuffle(item_list)
    now = datetime.datetime.now()

    # Add to log message bot has started
    log_message(f"Bot started at {now.strftime('%Y-%m-%d %H:%M:%S')}")

    # Start email/text body by appending the current time
    email_body = f"{now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    # Start searching thru the liquor list
    for code, name in item_list:
        message = search_liquor(session, code, name)    # Get message from searching each liquor
        if message != 'None':
            email_body += message                       # Appending the result if stock is found
            # also append the message to the log file
            log_message(message)
        else:
            log_message(f"No stock found for item: {name}")
        time.sleep(randint(15, 30))                     # Randomly pause the bot after every search to simulate human-like behavior

    # Append the map URLs to the message if any maps were created
    if map_urls:
        email_body += "\nMaps of Store Locations:\n"
        for product_name, url in map_urls:
            print(f"Appending map URL for {product_name}: {url}")
            email_body += f"{product_name}: {url}\n"
        map_urls.clear()

    # Sending email/text with all the results
    send_SMS(email_body, addr_to)
    # Add to the log file that the bot ran successfully
    log_message("Bot completed successfully.")

# ======================================================================================================================
# =========================== Functions Definitions ====================================================================

# Search for liquor function ===========================================================================================
def search_liquor(session, item_number, item_name):
    try:
        # Attempt to send a GET request to the Oregon Liquor Search website
        response = session.get(
            f"http://www.oregonliquorsearch.com/servlet/FrontController?"
            f"view=global&action=search&radiusSearchParam=30&productSearchParam={item_number}&"
            f"locationSearchParam=97015&chkDefault=on&btnSearch=Search",
            timeout=10  # Set a timeout for the request to avoid long delays
        )
        response.raise_for_status() # Raise an exception if the HTTP response indicates an error
    except requests.RequestException as e:
        # Handle any errors that occur during the request
        print(f"Failed to fetch item {item_name}: {e}")
        return 'None'   # Return 'None' to indicate the request failed.

    # Parse the HTML content of the response
    soup = BeautifulSoup(response.content, "html.parser")

    # Look for a table with class "list" that contains multiple store results
    result = soup.find("table", {"class": "list"})

    # Look for a div with id "prod-loc-details" that contains details for a single store
    one_store = soup.find("div", {"id": "prod-loc-details"})

    if result:
        # If multiple store results are found, parse them using the `parse_multiple_stores` function
        return parse_multiple_stores(soup, result)
    elif one_store:
        # If a single store result is found, parse it using the `parse_single_store` function
        return parse_single_store(soup, one_store)
    else:
        # If no results are found, print a message indicating no stock was located
        print(f"No stock found for item: {item_name}")
        return 'None'   # Return 'None' to indicate no stock was found.


# Parse details from multiple stores found in the search results =======================================================
def parse_multiple_stores(soup, result):
    # Start building the message with a separator line for clarity
    message = '-------------------------\n'

    # Extract the product description and format it.
    message += " ".join(soup.find("th", {"id": "product-desc"}).find("h2").text.split()) + '\n'
    # Save this product description
    product_description = soup.find("th", {"id": "product-desc"}).find("h2").text.strip()
    # Search for code inside parentheses and store it separately
    match = re.search(r'\(([^)]+)\)', product_description)
    product_code = match.group(1) if match else "N/A"
    # Variable to store all the addresses found
    store_in_stock = []
    # Look up product name from the item_list using the product code
    for code, name in item_list:
        if code == product_code:
            product_name = name
            break

    # Loop through each table row in the search result.
    for row in result.find_all("tr"):
        store_info = row.find_all("td") # Extract table data cells for the current row
        
        if len(store_info) > 7:
            # If there are enough cells, extract and format store details
            quantity = f"Quantity: {store_info[6].text}\n"  # Get the quantity of the product available
            message += f"    - {store_info[2].text}\n"      # Add the store address
            store_in_stock.append(store_info[2].text)        # Append the store address to the list
            message += f"      {store_info[4].text}\n"      # Add the store phone number
            message += f"      {quantity}\n"                # Add the quantity
            
    # Create a map with the store addresses found
    if store_in_stock:
        # Use product code to name the map file
        create_map(store_in_stock, f"{product_code}_map.html")
        # Append the new map URL to the global list with the url pattern: https://git-user-name.github.io/map-hosting/2160B_map.html with product name
        map_urls.append((product_name, f"https://git-user-name.github.io/map-hosting/{product_code}_map.html"))
    return message      # Return the all results message


# Parse details from a single store found in the search results ========================================================
def parse_single_store(soup, one_store):
    # Start building the message with a separator line for clarity
    message = '-------------------------\n'

    # Extract and format the product description
    message += " ".join(soup.find("th", {"id": "product-desc"}).find("h2").text.split()) + '\n'

    # Extract the store address and other information
    store_info = one_store.find("td", {"id": "location-display"}).find_all("p")

    if len(store_info) > 1:
        # Extract and format the store address
        address = str(store_info[0].text).strip()
        new_address = " ".join(address.split())
        message += f"    - {new_address}\n"

        # Extract and add additional store details
        store_details = str(store_info[1].text).strip()
        message += f"      {store_details}\n"
    else:
        # If address or details are unavailable, log the issue in the message
        message += "Store address or information not available\n"

    # Add stock information if available.
    in_stock_div = soup.find("div", {"id": "in-stock"})
    if in_stock_div:
        h2_tag = in_stock_div.find("h2")                # Extract the stock information from the stock section
        if h2_tag:
            stock_info = h2_tag.get_text(strip=True)    # Format the stock information
            message += f"      {stock_info}\n"          # Add stock info to message
        else:

            message += "      Stock information not available\n"
    else:
        # If the stock section is not found, log this issue
        message += "      Stock section not found\n"

    return message + "  \n" # Add new line to the message.


# Send the message via email to the specified recipients ===============================================================
def send_SMS(message, recipients):
    if message != 'None':
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)                # Connect to Gmail's SMTP server
            server.starttls()                                           # Start TLS encryption for the connection

            # Log in to the email account. Replace these with secure credentials
            server.login(login_email, access_token)

            # Create the email message
            msg = MIMEMultipart()
            msg['From'] = login_email                            # Sender's email address
            msg['To'] = ", ".join(recipients)                           # Recipient list
            msg['Subject'] = 'dToe Liquor Availability Update'          # Email subject
            msg.attach(MIMEText(message, 'plain'))                      # Attach the message as plain text

            # Send the email
            server.sendmail(msg['From'], recipients, msg.as_string())
            server.quit()                                               # Close the connection to the SMTP server
        except smtplib.SMTPException as e:
            # Handle any SMTP exceptions and print an error message.
            print(f"Failed to send email: {e}")

# Create a map with given addresses and save as HTML ================================================================
def create_map(addresses, output_file):
    """Create a map with given addresses and save as HTML."""
    
    # Specify the city you want to center on
    city_name = "Portland, OR"

    geolocator = Nominatim(user_agent="map_app", timeout=10)
    location = geolocator.geocode(city_name)

    if location:
        # Center the map on the city
        m = folium.Map(location=[location.latitude, location.longitude], zoom_start=12)
    else:
        # Fallback to default coordinates if city not found
        m = folium.Map(location=[37.7749, -122.4194], zoom_start=5)

    for address in addresses:
        try:
            location = geolocator.geocode(address)
            if location:
                folium.Marker(
                    [location.latitude, location.longitude],
                    popup=address
                ).add_to(m)
                print(f"Added: {address}")
            else:
                print(f"Not found: {address}")
        except Exception as e:
            print(f"Error geocoding {address}: {e}")

    # Make sure the 'maps' folder exists
    os.makedirs("maps", exist_ok=True)
    # Prepend the folder path
    output_path = os.path.join("maps", output_file)
    m.save(output_path)
    print(f"Map saved as '{output_path}'")
    
    return output_path

# Append the given message to a log file ===============================================================================
def log_message(message):
    try:
        with open("logfile.txt", "a") as log_file:
            log_file.write(f"{message}\n")
    except IOError as e:
        # Handle file input/output errors and print an error message
        print(f"Logging error: {e}")


if __name__ == "__main__":
    main()  # Entry point for the script. Calls the main function (not defined here).
            # Methods can be used without having to define before the call
            # This helps pushing all functions to the end of the file for cleaner setup
