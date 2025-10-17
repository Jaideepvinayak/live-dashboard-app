# analysis_scraper.py
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import firebase_admin
from firebase_admin import credentials, firestore
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import re
from collections import Counter

# --- Part 1: Initialization ---
try:
    cred = credentials.Certificate("credentials.json")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Successfully connected to Firebase.")
except Exception as e:
    print(f"🔥 Error initializing Firebase: {e}")
    exit()

try:
    sia = SentimentIntensityAnalyzer()
    print("✅ Sentiment Analyzer ready.")
except Exception as e:
    print(f"🔥 Error initializing Sentiment Analyzer: {e}")
    exit()


# --- Part 2: Scrape News and Find Trend ---
def get_trending_topic_from_news():
    print("\n🔍 Scraping news to find a trending topic...")
    URL = "https://www.bbc.com/news"
    try:
        page = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
        page.raise_for_status()
        soup = BeautifulSoup(page.content, "html.parser")
        
        headlines = [h.text for h in soup.find_all("h2", {"data-testid": "card-headline"})]
        
        if not headlines:
            print("❌ Could not find headlines. Using a default topic.")
            return "Global"

        words = re.findall(r'\b[A-Z][a-z]{3,}\b', " ".join(headlines))
        if not words:
            return "World"
            
        most_common_word = Counter(words).most_common(1)[0][0]
        print(f"📈 Trending Topic Found: {most_common_word}")
        return most_common_word

    except Exception as e:
        print(f"❌ Error scraping news: {e}. Using a default topic.")
        return "Technology"


# --- Part 3: Scrape Reddit Opinions ---
def scrape_reddit_opinions(topic):
    print(f"\n🔍 Scraping Reddit for opinions on '{topic}'...")
    search_url = f"https://www.reddit.com/search/?q={topic}&type=link"
    
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Add a user-agent to mimic a real browser
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 20) # Wait up to 20 seconds
        
        driver.get(search_url)
        print("Waiting for Reddit search results...")
        
        # UPDATED: More robust selector for the first post's link
        post_link_selector = "a[data-testid='post-title']"
        
        # Wait until the element is present and clickable
        first_post_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, post_link_selector)))
        post_url = first_post_link.get_attribute('href')

        print(f"Navigating to top post: {post_url}")
        driver.get(post_url)
        print("Waiting for comments to load...")
        
        comment_selector = "div[data-testid='comment']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, comment_selector)))

        # Add a small extra sleep just in case
        time.sleep(2)

        comments = []
        comment_elements = driver.find_elements(By.CSS_SELECTOR, comment_selector)
        for el in comment_elements:
            comments.append(el.text.strip())
        
        print(f"✅ Scraped {len(comments)} comments.")
        return comments
    
    except Exception as e:
        print(f"❌ Error scraping Reddit: {e}")
        return []
    finally:
        if 'driver' in locals():
            driver.quit()


# --- Part 4: Analyze Sentiment and Store ---
def analyze_and_store(topic, opinions):
    if not opinions:
        print("No opinions to analyze. Halting.")
        return

    print("\n🔬 Analyzing sentiment of opinions...")
    results = []
    sentiment_summary = {"positive": 0, "negative": 0, "neutral": 0}

    for op in opinions:
        score = sia.polarity_scores(op)
        sentiment = "neutral"
        if score['compound'] > 0.05:
            sentiment = "positive"
            sentiment_summary["positive"] += 1
        elif score['compound'] < -0.05:
            sentiment = "negative"
            sentiment_summary["negative"] += 1
        else:
            sentiment_summary["neutral"] += 1
        
        results.append({"text": op, "sentiment": sentiment})

    doc_ref = db.collection("sentiments").document(topic.lower().replace(" ", "_"))
    doc_ref.set({
        "topic": topic,
        "summary": sentiment_summary,
        "opinions": results,
        "last_updated": firestore.SERVER_TIMESTAMP
    })
    print(f"✅ Success! Stored sentiment analysis for '{topic}' in Firestore.")


# --- Main Execution ---
if __name__ == "__main__":
    trending_topic = get_trending_topic_from_news()
    if trending_topic:
        reddit_opinions = scrape_reddit_opinions(trending_topic)
        analyze_and_store(trending_topic, reddit_opinions)