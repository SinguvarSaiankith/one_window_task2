import requests
import time
import json
from bs4 import BeautifulSoup
from selenium import webdriver

# Configure Selenium WebDriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)
driver = webdriver.Chrome(options=chrome_options)

# Base URL for the site
base_url = 'https://www.4icu.org'

# Step 1: Scrape university names, locations, and URLs
driver.get(base_url + "/de/universities/")
time.sleep(3)

# Use Requests to get the page content for the main state page
html = requests.get(base_url + '/de/universities/')
soup = BeautifulSoup(html.content, 'html.parser')

# Extract all <a> tags within the table (state links)
state_links = soup.select('table a')

# Collect state URLs and state names
state_data = []
for link in state_links:
    state_name = link.get_text(strip=True)
    state_url = link['href']
    full_state_url = base_url + state_url  # Construct the full URL
    state_data.append({
        'state_name': state_name,
        'state_url': full_state_url
    })

# List to collect all university details
all_universities = []

# Step 2: Loop over each state URL and extract university links and towns
for state in state_data:
    state_name = state['state_name']
    state_url = state['state_url']

    # Fetch state page
    html = requests.get(state_url)
    soup = BeautifulSoup(html.content, 'html.parser')

    # Extract university rows containing town and university links
    university_rows = soup.select('table.table-hover tbody tr')

    universities_in_state = []
    for row in university_rows:
        # Extract university name and link
        university_link_tag = row.select_one('td a')
        if university_link_tag:
            university_name = university_link_tag.get_text(strip=True)  # University name
            university_url = university_link_tag['href']  # Relative URL
            full_university_url = base_url + university_url  # Full university URL

            # Step 3: Visit the university page to scrape more data (town name, logo, social media, etc.)
            html_university = requests.get(full_university_url)
            soup_university = BeautifulSoup(html_university.content, 'html.parser')

            # Extract town name from the university page
            town_name = soup_university.find('span', itemprop='addressLocality').get_text() if soup_university.find('span', itemprop='addressLocality') else None

            phone_icon_tag = soup_university.find('img', {'alt': lambda alt: alt and 'Phone Number' in alt})
            phone_number = phone_icon_tag.find_next('td').get_text(strip=True) if phone_icon_tag else None

            # Extract logo URL
            logo_tag = soup_university.find('img', {'itemprop': 'logo'})
            logo_src = logo_tag['src'] if logo_tag else None

            # Extract the official website URL
            anchor_tag = soup_university.find('a', {'itemprop': 'url'})
            website_url = anchor_tag['href'] if anchor_tag else None

            # Extract whether the university is public or private
            control_tag = soup_university.find('p', class_='lead')
            control_type = control_tag.find('strong').string.lower() if control_tag else None

            # Extract the founding year
            founded_year = soup_university.find('span', {'itemprop': 'foundingDate'})
            establish_year = founded_year.text if founded_year else None

            # Extract social media links
            facebook_link = soup_university.find('strong', string='Facebook').find_next('a', {'itemprop': 'sameAs'})['href'] if soup_university.find('strong', string='Facebook') else None
            twitter_link = soup_university.find('strong', string='X (Twitter)').find_next('a', {'itemprop': 'sameAs'})['href'] if soup_university.find('strong', string='X (Twitter)') else None
            instagram_link = soup_university.find('strong', string='Instagram').find_next('a', {'itemprop': 'sameAs'})['href'] if soup_university.find('strong', string='Instagram') else None
            linkedin_link = soup_university.find('strong', string='LinkedIn').find_next('a', {'itemprop': 'sameAs'})['href'] if soup_university.find('strong', string='LinkedIn') else None
            youtube_link = soup_university.find('strong', string='YouTube').find_next('a', {'itemprop': 'sameAs'})['href'] if soup_university.find('strong', string='YouTube') else None

            # Append all data for this university in the required format
            universities_in_state.append({
                'name': university_name,
                'location': {
                    'country': 'Germany',
                    'state': state_name,
                    'city': town_name
                },
                'phone': phone_number,
                'logoSrc': logo_src,
                'type': control_type,
                'establishedYear': establish_year,
                'contact': {
                    'facebook': facebook_link,
                    'twitter': twitter_link,
                    'instagram': instagram_link,
                    'officialWebsite': website_url,
                    'linkedin': linkedin_link,
                    'youtube': youtube_link
                }
            })

    # Append universities of the current state to the main list
    all_universities.append({
        'state_name': state_name,
        'universities': universities_in_state
    })

    time.sleep(1)  # Adding a delay to avoid overloading the server

# Step 4: Save the scraped data to a JSON file
with open('universities_data.json', 'w', encoding='utf-8') as f:
    json.dump(all_universities, f, ensure_ascii=False, indent=4)

# Optional: Print confirmation
print("University data successfully written to 'universities_data.json'")
