# news_scraper.py
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore

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

def scrape_and_store_news():
    """Scrapes top 10 BBC News headlines and stores them in Firestore."""
    print("\n🔍 Scraping BBC News for top 10 headlines...")
    URL = "https://www.bbc.com/news"
    
    try:
        page = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
        page.raise_for_status()
        soup = BeautifulSoup(page.content, "html.parser")
        
        headlines_data = []
        headline_elements = soup.find_all("h2", {"data-testid": "card-headline"})

        if not headline_elements:
            print("❌ Could not find headlines. The website's HTML structure may have changed.")
            return

        for element in headline_elements[:10]:
            title = element.text.strip()
            link_tag = element.find_parent("a")
            
            if title and link_tag and link_tag.has_attr('href'):
                link = "https://www.bbc.com" + link_tag['href'] if not link_tag['href'].startswith("http") else link_tag['href']
                headlines_data.append({"title": title, "link": link})
        
        doc_ref = db.collection("news").document("latest_headlines")
        
        doc_ref.set({
            "headlines": headlines_data,
            "last_updated": firestore.SERVER_TIMESTAMP
        })
        
        print(f"✅ Success! Stored {len(headlines_data)} headlines in Firestore.")

    except Exception as e:
        print(f"❌ An error occurred during scraping: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    scrape_and_store_news()