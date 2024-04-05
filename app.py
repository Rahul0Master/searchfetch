from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from flask import Flask, render_template

app = Flask(__name__)

# The scope for the Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# Load credentials from the service account key JSON file
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

def perform_search(search_query, country_code, num):
    #-----------changes Made-------------------#
    service = Service(ChromeDriverManager().install())

    # Set up the Chrome options for headless mode
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')

    # Initialize the Chrome WebDriver with service and options
    driver = webdriver.Chrome(service=service, options=options)
    
    # Open Google search with the country code and num parameters
    google_url_with_params = f'https://www.google.com/search?q={search_query}&gl={country_code}&num={num}'
    driver.get(google_url_with_params)

    # Create a dictionary to store unique URLs and their headings
    unique_urls_and_headings = {}

    # Find all search result headings and URLs on the current page
    search_results = driver.find_elements(By.CSS_SELECTOR, 'div.g')

    result_count = 0
    # Extract the URLs and headings, and filter out duplicates
    for result in search_results:
        try:
            heading = result.find_element(By.CSS_SELECTOR, 'h3').text
            link = result.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
            if heading and link:  # Check for non-empty
                # Only add the URL and heading if the URL is not already in the dictionary
                # if link not in unique_urls_and_headings:
                unique_urls_and_headings[link] = heading
                result_count = result_count + 1
                
        except Exception as e:
            print(f"Error extracting result: {e}")

    # Close the WebDriver
    driver.quit()

    # Convert the dictionary to a list of tuples
    urls_and_headings = [(heading, link) for link, heading in unique_urls_and_headings.items()]

    return urls_and_headings

def upload_sheets():
    # The ID of your Google Sheet
    SPREADSHEET_ID = '1k6_zvyVHiVk0sZkzLkIDvNhrd3Pb9RQ2O-49EggablI'
    # The range in the Google Sheet where the queries will be read from
    QUERY_RANGE_NAME = 'Sheet1!A1:B'
    # The range in the Google Sheet where the results will be written
    RESULT_RANGE_NAME = 'Sheet2!A1:B'
    # The service that communicates with the Google Sheets API
    sheet = service.spreadsheets()

    # Clear existing data in the result range
    clear_result = sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range=RESULT_RANGE_NAME).execute()

    # Read the search queries from the query tab
    query_result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=QUERY_RANGE_NAME).execute()
    query_values = query_result.get('values', [])

    # Perform searches for each query
    all_search_results = []
    for query_row in query_values:

        # Ignore empty cells
        if query_row:
            search_query = query_row[0]
            country_code = query_row[1] if len(query_row) > 1 else 'us'
            # Perform the search and get results
            search_results = perform_search(search_query, country_code, 150)  #Country code 'us' and number of results 150
            all_search_results.extend(search_results[:100])

    # Write the search results to the result tab
    values = [["Title", "URL"]] + all_search_results
    body = {'values': values}

    result = sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=RESULT_RANGE_NAME, valueInputOption='RAW', body=body).execute()

    print('Search results written to Google Sheet')

@app.route('/')
def index():
    upload_sheets()
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
    # upload_sheets()
