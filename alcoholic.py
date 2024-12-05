# Liquor Availability Bot Scraper for Oregon Liquor Stores
# Purpose: Automates the search for specific liquor availability in Oregon liquor stores.
# Author: Dinh Nguyen (dtoe07@gmail.com)
# Date Created: January 7, 2021

import requests
from bs4 import BeautifulSoup
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
from random import randint
import datetime


def main():
    # Browser User Agents to randomize browswer for the bot
    user_agent_list = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    ]
    user_agent = random.choice(user_agent_list)
    session = requests.Session()
    session.headers.update({'User-Agent': user_agent})

    # Try to establish connection to www.oregonliquorsearch.com
    try:
        session.post("http://www.oregonliquorsearch.com/servlet/WelcomeController", timeout=10)
    except requests.RequestException as e:
        print(f"Failed to establish session: {e}")
        return

    # List of Recipients
    addr_to = ['RECIPIENTS-EMAILS-HERE']

    # List of the liquor to be searched
    item_list = [
        ('8722B', 'Red Weller'),
        ('8954B', 'Green Weller'),
        ('1562B', 'W.L. WELLER 12YR KENTUCKY STRAIGHT BRBN'),

        ('8119B', 'SUNTORY HIBIKI 12YR'),
        ('7634B', 'SUNTORY YAMAZAKI 18 YR'),

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

        ('2160B', 'EAGLE RARE S/B BOURBON')
        # Add more items here...
    ]

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
        time.sleep(randint(20, 40))                     # Randomly pause the bot after every search to simulate human-like behavior

    # Sending email/text with all the results
    send_SMS(email_body, addr_to)
    # Add to the log file that the bot ran successfully
    log_message("Bot completed successfully.")


# Search for liquor function ===========================================================================================
def search_liquor(session, item_number, item_name):
    try:
        # Attempt to send a GET request to the Oregon Liquor Search website
        response = session.get(
            f"http://www.oregonliquorsearch.com/servlet/FrontController?"
            f"view=global&action=search&radiusSearchParam=30&productSearchParam={item_number}&"
            f"locationSearchParam=97230&chkDefault=on&btnSearch=Search",
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

    # Loop through each table row in the search result.
    for row in result.find_all("tr"):
        store_info = row.find_all("td") # Extract table data cells for the current row
        if len(store_info) > 7:
            # If there are enough cells, extract and format store details
            quantity = f"Quantity: {store_info[6].text}\n"  # Get the quantity of the product available
            message += f"    - {store_info[2].text}\n"      # Add the store name
            message += f"      {store_info[4].text}\n"      # Add the store location
            message += f"      {quantity}\n"                # Add the quantity
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
            server.login('YOUR-EMAIL-HERE', 'PASSWORD-HERE')

            # Create the email message
            msg = MIMEMultipart()
            msg['From'] = 'YOUR-EMAIL-HERE'                            # Sender's email address
            msg['To'] = ", ".join(recipients)                           # Recipient list
            msg['Subject'] = 'dToe Liquor Availability Update'          # Email subject
            msg.attach(MIMEText(message, 'plain'))                      # Attach the message as plain text

            # Send the email
            server.sendmail(msg['From'], recipients, msg.as_string())
            server.quit()                                               # Close the connection to the SMTP server
        except smtplib.SMTPException as e:
            # Handle any SMTP exceptions and print an error message.
            print(f"Failed to send email: {e}")


# Append the given message to a log file ===============================================================================
def log_message(message):
    try:
        with open("/home/python/logfile.txt", "a") as log_file:
            log_file.write(f"{message}\n")                              # Write the message to the log file.
    except IOError as e:
        # Handle file input/output errors and print an error message
        print(f"Logging error: {e}")


if __name__ == "__main__":
    main()  # Entry point for the script. Calls the main function (not defined here).
            # Fuction can be used without having to define before the call
            # This helps pushing all functions to the end of the file for cleaner setup
