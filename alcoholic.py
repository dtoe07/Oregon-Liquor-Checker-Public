# A bot scraper to search for specific liquor in Oregon when they are avail in store
# Created by: Dinh dtoe07@gmail.com
# Date created: 1/7/2021

from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
from random import randint
import datetime


# Function to send txt from Gmail to phone#

def send_SMS(message, addr_list):
    if message != 'None':
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('YOUR_EMAIL_HERE', 'YOUR_PASSWORD_HERE')
        from_mail = 'YOUR_EMAIL_HERE'

        # Recipients list to send emails to

        addr_to = addr_list

        # Setup the MIME

        mail_content = message
        message = MIMEMultipart()
        message['From'] = 'YOUR_EMAIL_HERE'
        message['To'] = ', '.join(addr_to)
        message['Subject'] = 'Cheers with Toe! '  # The subject line

        # The body and the attachments for the mail

        message.attach(MIMEText(mail_content, 'plain'))
        text = message.as_string()

        server.sendmail(from_mail, addr_to, text)

        # Quit the server after job is done

        server.quit()  # End send_message function!


########################################################################################################################################

# List of user agents for header of the requests

user_agent_list = \
    ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15'
     ,
     'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0'
     ,
     'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
     ,
     'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0'
     ,
     'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
     ]

# Pick a random user agent

user_agent = random.choice(user_agent_list)

# Open new session and click the button for over 21

session = requests.Session()

# Update user agent to header

session.headers.update({'User-Agent': user_agent})

# Start connecting to the server, this will auto bypass the click if you are over 21 button as well

s = \
    session.post('http://www.oregonliquorsearch.com/servlet/WelcomeController'
                 )
time.sleep(randint(10, 30))


# Define a search function to take in an item number ======================================================================================

def search_liquor(itemNumber, itemName):
    NEWLINE = '\n'

    # Getting result list from the search with the Item number

    s = \
        session.get('http://www.oregonliquorsearch.com/servlet/FrontController?view=global&action=search&radiusSearchParam=30&productSearchParam='
                     + itemNumber
                    + '&locationSearchParam=97230&chkDefault=on&btnSearch=Search'
                    )

    # Loading page content to bs4 for parsing

    bsObj = BeautifulSoup(s.content, 'html.parser')

    # find the section that contains the list of the stores that has it avail

    result = bsObj.find('table', {'class': 'list'})

    # Check if there is only one store avail to buy for that item

    oneStore = bsObj.find('div', {'id': 'prod-loc-details'})

    # Continue if stock is found!!!!

    if result is not None and oneStore is None:
        message = '****** '

        # Append product name into the message to send SMS later

        message += str(bsObj.find('th', {'id': 'product-desc'
                       }).find('h2').text) + '\n'

        # Print out the product name for debugging purposes

        print '########## ' + bsObj.find('th', {'id': 'product-desc'
                }).find('h2').text + ' ##########' + '\n'

        # Loading up the stores to a list of stores

        resultList = result.find_all('tr')

        # Printing out each store info

        for tag in resultList:

            # Find store info

            aStore = tag.find_all('td')

            # Looping thru a specific range from the store info list to display

            for item in aStore[2:6]:
                print item.text

            # Check if the list is not empty then print the quantity of the avail product

            if len(aStore) > 7:
                quantity = 'Quantity: ' + aStore[6].text + '\n'
                print quantity
                message += str(aStore[2].text + NEWLINE)
                message += str(aStore[4].text + NEWLINE)
                message += str(quantity + NEWLINE)

        # append 2 extra spaces to the message because for some reason it will cut 2 pos when sending it out...

        message += '  '
        return message
    elif oneStore is not None:

    # If there is only one store has it

        message = '****** '
        message += str(bsObj.find('th', {'id': 'product-desc'
                       }).find('h2').text) + '\n'  # append bottle name into the message to send SMS
        print '########## ' + bsObj.find('th', {'id': 'product-desc'
                }).find('h2').text + ' ##########' + '\n'
        print 'only one store has it in stock: '
        store = oneStore.find('td', {'id': 'location-display'})
        storeInfo = store.find_all('p')
        for info in storeInfo:
            print info.text
        print '\n'
        address = str(storeInfo[0].text)
        new_address = ' '.join(address.split())
        message += new_address
        message += str(NEWLINE + storeInfo[1].text + NEWLINE)

        # Append 2 extra spaces again

        message += '  \n'
        return message
    else:

    # If there are none instock

        print '########## none in stock for item: ' + itemName \
            + ' ! ##########'
        message = 'None'
        return message


###################################################################################################################
################################ Start the search with each item codes ############################################
###################################################################################################################

addr_to = ['RECEIVER_EMAIL_HERE', 'TMOBILE_PHONE_HERE@tmomail.net']  # Recipients list to send SMS to

# List of the products with their search codes

item_list = [
    ('8722B', 'Red Weller'),
    ('8119B', 'SUNTORY HIBIKI 12YR'),
    ('8321B', 'SUNTORY YAMAZAKI 12 YR'),
    ('7634B', 'SUNTORY YAMAZAKI 18 YR'),
    ('8954B', 'Green Weller'),
    ('0191B', 'Stagg JR.'),
    ('1562B', 'W.L. WELLER 12YR KENTUCKY STRAIGHT BRBN'),
    ('2146B', 'WOODFORD RES. MC BOURBON'),
    ('3749B', 'BLOOD OATH PACT VII'),
    ('2893B', 'HIGH WEST MIDWINTER'),
    ('2344B', "MICHTER'S US1 SOUR MASH WHISKEY"),
    ('2657B ', "MICHTER'S TOASTED BARREL FINISH"),
    ('0793B ', 'E.H. TAYLOR SINGLE BARREL STRAIGHT BOURB'),
    ('1416B ', 'E.H. TAYLOR JR BARREL PROOF'),
    ('1418B ', 'E.H. TAYLOR STRAIGHT RYE WHISKEY'),
    ('6374B', 'WELLER FULL PROOF'),
    ]

# randomize the list to make the search look more humanlike

random.shuffle(item_list)
now = datetime.datetime.now()

# Write to logfile script has started

with open('/home/python/logfile.txt', 'a') as myfile:
    myfile.write('\n - Bot has started...   '
                 + str(now.strftime('%Y-%m-%d %H:%M:%S')))

# Initialize a string to start loading up the email body to send later

email_body = str(now.strftime('%Y-%m-%d %H:%M:%S')) + '''

 '''

# Start searching from the list of products after ramdomized

for (a, b) in item_list:

    # Append the search result to the email message

    message = search_liquor(a, b)
    if message != 'None':
        email_body += message
    time.sleep(randint(20, 40))

# Sending out SMS and email with all the results

send_SMS(email_body, addr_to)

# Write to logfile bot has run til the end

with open('/home/python/logfile.txt', 'a') as myfile:
    myfile.write(' ...Bot Succeeded!')
