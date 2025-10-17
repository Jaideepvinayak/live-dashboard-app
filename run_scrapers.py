# run_scrapers.py
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore

# We need to import Selenium for the gold scraper
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- Firebase Initialization ---
try:
    cred = credentials.Certificate("credentials.json")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Successfully connected to Firebase.")
except Exception as e:
    print(f"🔥 Error initializing Firebase: {e}")
    exit()

def scrape_news():
    """Scrapes top 10 BBC News headlines and stores them."""
    print("\n🔍 Scraping BBC News...")
    URL = "https://www.bbc.com/news"
    try:
        page = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
        page.raise_for_status()
        soup = BeautifulSoup(page.content, "html.parser")
        
        headlines_data = []
        headline_elements = soup.find_all("h2", {"data-testid": "card-headline"})

        if not headline_elements:
            print("❌ Could not find news headlines.")
            return

        for element in headline_elements[:10]:
            title = element.text.strip()
            link_tag = element.find_parent("a")
            if title and link_tag and link_tag.has_attr('href'):
                link = "https://www.bbc.com" + link_tag['href'] if not link_tag['href'].startswith("http") else link_tag['href']
                headlines_data.append({"title": title, "link": link})
        
        doc_ref = db.collection("dashboard_data").document("latest_news")
        doc_ref.set({"headlines": headlines_data, "last_updated": firestore.SERVER_TIMESTAMP})
        print(f"✅ Stored {len(headlines_data)} news headlines.")

    except Exception as e:
        print(f"❌ An error occurred during news scraping: {e}")

def scrape_gold_rates():
    """Scrapes live gold rates for Hyderabad using Selenium to avoid being blocked."""
    print("\n🔍 Scraping Gold Rates...")
    URL = "https://www.goodreturns.in/gold-rates/hyderabad.html"
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # Run browser in the background
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(URL)
        
        # Get the page HTML after it has been loaded by the browser
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit() # Close the browser
        
        rates_data = []
        table = soup.find('div', class_='gold_silver_table').find('table')
        rows = table.find_all('tr')

        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) >= 2:
                carat = cols[0].text.strip()
                price = cols[1].text.strip()
                rates_data.append({"carat": carat, "price": price})

        if not rates_data:
            print("❌ Could not find gold rates.")
            return

        doc_ref = db.collection("dashboard_data").document("latest_gold_rates")
        doc_ref.set({"rates": rates_data, "last_updated": firestore.SERVER_TIMESTAMP})
        print(f"✅ Stored {len(rates_data)} gold rate entries.")

    except Exception as e:
        print(f"❌ An error occurred during gold scraping: {e}")
        if 'driver' in locals():
            driver.quit()

# --- Main Execution ---
if __name__ == "__main__":
    scrape_news()
    scrape_gold_rates()