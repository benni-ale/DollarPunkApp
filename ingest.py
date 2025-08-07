import requests
import json
import time
import os
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
TICKERS = os.getenv("TICKERS", "").split(",")
OUTPUT_FILE = "output/news_data.json"

def fetch_news(ticker):
    url = (
        "https://www.alphavantage.co/query?"
        f"function=NEWS_SENTIMENT&tickers={ticker}&apikey={API_KEY}"
    )
    r = requests.get(url)
    if r.status_code != 200:
        print(f"Errore per {ticker}: {r.status_code}")
        return []
    return r.json().get("feed", [])

def run_ingestion():
    all_news = []
    
    for i, ticker in enumerate(tqdm(TICKERS)):
        news_list = fetch_news(ticker)
        for item in news_list:
            item["source_ticker"] = ticker  # aggiungi info utile
            all_news.append(item)
        time.sleep(12)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2)
    
    print(f"Ingestion completed: {len(all_news)} articles collected")

if __name__ == "__main__":
    run_ingestion()
