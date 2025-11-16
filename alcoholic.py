# Liquor Availability Bot Scraper for Oregon Liquor Stores
# Purpose: Automates the search for specific liquor availability in Oregon liquor stores.
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
import datetime
import folium
from geopy.geocoders import Nominatim, ArcGIS
import argparse

# Load environment variables for email credentials
login_email = os.getenv("LOGIN_EMAIL")
access_token = os.getenv("ACCESS_TOKEN")

# Load recipient addresses from environment variables for zip 97015
addr_to_97015 = [
    e.strip().lower()
    for e in os.environ.get("ADDR_TO_97015", "").split(",")
    if e.strip()
]
# Load recipient addresses from environment variables for zip 97223
addr_to_97223 = [
    e.strip().lower()
    for e in os.environ.get("ADDR_TO_97223", "").split(",")
    if e.strip()
]
# Load test email addresses from environment variables for other zip codes
test_email = [
    e.strip().lower() for e in os.environ.get("TEST_EMAIL", "").split(",") if e.strip()
]

# List of url to the maps to be appended to the end of the email
map_urls = []

# List of the liquor to be searched
item_list = [
    ("8722B", "Red Weller"),
    ("8954B", "Green Weller"),
    ("1562B", "W.L. WELLER 12YR KENTUCKY STRAIGHT BRBN"),
    ("6374B", "WELLER FULL PROOF"),
    ("11941B", "WELLER FULL PROOF SINGLE BARREL SELECT"),
    ("8119B", "SUNTORY HIBIKI 12YR"),
    # ('7634B', 'SUNTORY YAMAZAKI 18 YR'),
    ("0191B", "Stagg JR."),
    ("2146B", "WOODFORD RES. MC BOURBON"),
    ("3749B", "BLOOD OATH PACT VII"),
    ("2893B", "HIGH WEST MIDWINTER"),
    ("2657B", "MICHTER'S TOASTED BARREL FINISH"),
    ("0793B", "E.H. TAYLOR SINGLE BARREL STRAIGHT BOURB"),
    ("1416B", "E.H. TAYLOR JR BARREL PROOF"),
    ("1418B", "E.H. TAYLOR STRAIGHT RYE WHISKEY"),
    ("5830B", "TEQUILA FORTALEZA BLANCO"),
    ("5831B", "TEQUILA FORTALEZA REPOSADO"),
    ("5829B", "TEQUILA FORTALEZA Anejo"),
    ("2160B", "EAGLE RARE S/B BOURBON"),
    ("1059B", "HAKUSHU 12 YR"),
    ("3560B", "HAKUSHU 18 YR"),
    ("12876B", "WILD TURKEY 8 YR 101 BRBN"),
    # Add more items here...
]

# Browser User Agents to randomize browser for the bot
user_agent_list = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
]


# ======================================================================================================================
# =========================== Main =====================================================================================
def main():
    # Get search parameters from command line arguments or use defaults
    zip_code, search_radius = get_search_params()
    print(f"Searching for ZIP Code: {zip_code}, Search Radius: {search_radius} miles")

    # Set up a session with a random user-agent
    user_agent = random.choice(user_agent_list)
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent})

    # Try to establish connection to www.oregonliquorsearch.com
    try:
        session.post(
            "http://www.oregonliquorsearch.com/servlet/WelcomeController", timeout=10
        )
    except requests.RequestException as e:
        print(f"Failed to establish session: {e}")
        return

    # Randomize the liquor list
    random.shuffle(item_list)
    now = datetime.datetime.now()

    # Add to log message bot has started
    log_message(f"Bot started at {now.strftime('%Y-%m-%d %H:%M:%S')}")

    # Start email/text body by appending the current time
    email_body = f"{now.strftime('%Y-%m-%d %H:%M:%S')}\n"
    # append zipcode and search radius to the email body
    email_body += (
        f"Search ZIP Code: {zip_code}, Search Radius: {search_radius} miles\n\n"
    )

    # Start searching thru the liquor list
    for item_number, item_name in item_list:
        message = search_liquor(
            session, item_number, item_name, zip_code, search_radius
        )  # Get message from searching each liquor
        if message != "None":
            email_body += message  # Appending the result if stock is found
            # also append the message to the log file
            log_message(message)
        else:
            log_message(f"No stock found for item: {item_name}")
        time.sleep(
            randint(15, 30)
        )  # Randomly pause the bot after every search to simulate human-like behavior

    # Append the map URLs to the message if any maps were created
    if map_urls:
        email_body += "\nMaps of Store Locations:\n"
        for item_name, url in map_urls:
            email_body += f"{item_name}: {url}\n"
            print(f"Appended map URL into email for {item_name}: {url}")
        map_urls.clear()

    # Sending the email/SMS to the recipients based on the zip code
    if zip_code == "97015":
        send_SMS(email_body, addr_to_97015, zip_code)
    elif zip_code == "97223":
        send_SMS(email_body, addr_to_97223, zip_code)
    else:
        send_SMS(email_body, test_email, zip_code)

    # Add to the log file that the bot ran successfully
    log_message("Bot completed successfully.")


# ======================================================================================================================
# =========================== Functions Definitions ====================================================================


# Search for liquor function ===========================================================================================
def search_liquor(
    session, item_number, item_name, zip_code="97015", search_radius="30"
):
    try:
        # Attempt to send a GET request to the Oregon Liquor Search website
        response = session.get(
            f"http://www.oregonliquorsearch.com/servlet/FrontController?"
            f"view=global&action=search&radiusSearchParam={search_radius}&productSearchParam={item_number}&"
            f"locationSearchParam={zip_code}&chkDefault=on&btnSearch=Search",
            timeout=10,  # Set a timeout for the request to avoid long delays
        )
        response.raise_for_status()  # Raise an exception if the HTTP response indicates an error
    except requests.RequestException as e:
        # Handle any errors that occur during the request
        print(f"Failed to fetch item {item_name}: {e}")
        return "None"  # Return 'None' to indicate the request failed.

    # Parse the HTML content of the response
    soup = BeautifulSoup(response.content, "html.parser")

    # Look for a table with class "list" that contains multiple store results
    result = soup.find("table", {"class": "list"})

    # Look for a div with id "prod-loc-details" that contains details for a single store
    one_store = soup.find("div", {"id": "prod-loc-details"})

    if result:
        # If multiple store results are found, parse them using the `parse_multiple_stores` function
        print(f"✅ Multiple stores found for item: {item_name}")
        return parse_multiple_stores(soup, result, item_number, item_name, zip_code)
    elif one_store:
        # If a single store result is found, parse it using the `parse_single_store` function
        print(f"✅ Single store found for item: {item_name}")
        return parse_single_store(soup, one_store)
    else:
        # If no results are found, print a message indicating no stock was located
        print(f"❌ No stock found for item: {item_name}")
        return "None"  # Return 'None' to indicate no stock was found.


# Parse details from multiple stores found in the search results =======================================================
def parse_multiple_stores(soup, result, item_number, item_name, zip_code="97015"):
    # Start building the message with a separator line for clarity
    message = "-------------------------\n"

    # Extract product description
    product_desc_tag = soup.find("th", {"id": "product-desc"}).find("h2")
    product_description = " ".join(product_desc_tag.text.split())

    # Extract bottle price
    price_th = soup.find("th", string="Bottle Price:")
    if price_th:
        bottle_price = price_th.find_next("td").get_text(strip=True)
    else:
        bottle_price = "N/A"

    # Add both to one line
    message += f"{product_description}: {bottle_price}\n"

    # List to hold store addresses with stock
    store_in_stock = []
    # Loop through each table row in the search result.
    for row in result.find_all("tr"):
        store_info = row.find_all("td")  # Extract table data cells for the current row

        if len(store_info) > 7:
            # If there are enough cells, extract and format store details
            quantity = f"Quantity: {store_info[6].text}"  # Get the quantity of the product available
            message += f"    - {store_info[2].text}\n"  # Add the store address
            store_in_stock.append(
                store_info[2].text
            )  # Append the store address to the list
            message += f"      {store_info[4].text}\n"  # Add the store phone number
            message += f"      {quantity}\n"  # Add the quantity

    # Create a map with the store addresses found
    if store_in_stock:
        # Use product code to name the map file
        print(f"📍 Creating map for item: {item_name}")
        create_map(store_in_stock, f"{item_number}_map.html")
        # Append the map URL to the global list for inclusion in the email
        map_urls.append(
            (
                item_name,
                f"https://your-git-user.github.io/map-hosting/{zip_code}/{item_number}_map.html",
            )
        )

    return message  # Return the all results message


# Parse details from a single store found in the search results ========================================================
def parse_single_store(soup, one_store):
    # Start building the message with a separator line for clarity
    message = "-------------------------\n"

    # Extract and format the product description
    product_desc_tag = soup.find("th", {"id": "product-desc"}).find("h2")
    product_description = " ".join(product_desc_tag.text.split())

    # Extract the bottle price
    price_th = soup.find("th", string="Bottle Price:")
    if price_th:
        bottle_price = price_th.find_next("td").get_text(strip=True)
    else:
        bottle_price = "N/A"

    # Add both to one line
    message += f"{product_description}: {bottle_price}\n"

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
        h2_tag = in_stock_div.find(
            "h2"
        )  # Extract the stock information from the stock section
        if h2_tag:
            stock_info = h2_tag.get_text(strip=True)  # Format the stock information
            message += f"      {stock_info}\n"  # Add stock info to message
        else:
            message += "      Stock information not available\n"
    else:
        # If the stock section is not found, log this issue
        message += "      Stock section not found\n"

    return message


# Send the message via email to the specified recipients ===============================================================
def send_SMS(message, recipients, zipcode="97015"):
    if message != "None":
        try:
            server = smtplib.SMTP(
                "smtp.gmail.com", 587
            )  # Connect to Gmail's SMTP server
            server.starttls()  # Start TLS encryption for the connection

            # Log in to the email account. Replace these with secure credentials
            server.login(login_email, access_token)

            # Create the email message
            msg = MIMEMultipart()
            msg["From"] = login_email  # Sender's email address
            msg["To"] = ", ".join(recipients)  # Recipient list
            msg["Subject"] = (
                "Blackpink in your area!!! Catch them all for zipcode: " + zipcode
            )  # Email subject
            msg.attach(MIMEText(message, "plain"))  # Attach the message as plain text

            # Send the email
            server.sendmail(msg["From"], recipients, msg.as_string())
            server.quit()  # Close the connection to the SMTP server
        except smtplib.SMTPException as e:
            # Handle any SMTP exceptions and print an error message.
            print(f"Failed to send email: {e}")


# Clean up and normalize address strings =============================================================================
def normalize_address(addr):
    addr = addr.title()  # Proper capitalization
    addr = addr.replace("Ste", "Suite")
    addr = addr.replace("Ave", "Avenue")
    addr = addr.replace("Blvd", "Boulevard")
    addr = addr.replace("Hwy", "Highway")
    return addr


# Create a map with given addresses and save as HTML. =================================================================
def create_map(
    addresses, output_file, map_center="Portland, OR", default_state="Oregon, USA"
):
    geolocator = Nominatim(user_agent="map_app", timeout=10)

    # Center the map on Portland
    center_location = geolocator.geocode(map_center)
    if center_location:
        m = folium.Map(
            location=[center_location.latitude, center_location.longitude],
            zoom_start=10,
        )
    else:
        # fallback roughly in Oregon
        m = folium.Map(location=[44.0, -120.5], zoom_start=7)

    for address in addresses:
        full_address = f"{normalize_address(address)}, {default_state}"
        try:
            location = geolocator.geocode(full_address)
            if not location:
                # Optional fallback to ArcGIS
                location = ArcGIS().geocode(full_address)

            if location:
                folium.Marker(
                    [location.latitude, location.longitude], popup=full_address
                ).add_to(m)
                print(f"\t++ Added: {address} → Geocoded as: {location.address}")
            else:
                print(f"Not found: {address}")
        except Exception as e:
            print(f"Error geocoding {address}: {e}")
        time.sleep(1)  # Respect Nominatim's rate limit

    # Make sure the 'maps' folder exists
    os.makedirs("maps", exist_ok=True)
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


# Get search parameters from command line arguments or use defaults ====================================================
def get_search_params():
    parser = argparse.ArgumentParser(
        description="Search Oregon Liquor stores by ZIP and radius."
    )
    parser.add_argument(
        "zip", nargs="?", default="97015", help="ZIP code to search from"
    )
    parser.add_argument(
        "radius", nargs="?", default="30", help="Search radius (2,5,10,30,60)"
    )
    args = parser.parse_args()

    default_zip = "97015"
    default_radius = "30"
    allowed_radii = {"2", "5", "10", "30", "60"}

    zip_code = args.zip if args.zip.isdigit() and len(args.zip) == 5 else default_zip
    search_radius = args.radius if args.radius in allowed_radii else default_radius

    return zip_code, search_radius


if __name__ == "__main__":
    # This block ensures that main() is called only when the script is executed directly,
    # not when it's imported as a module into another script.
    main()
