import requests
import json
import time
import os
import glob
from datetime import datetime, timedelta
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
TICKERS = os.getenv("TICKERS", "").split(",")
BATCH_SIZE = 100  # Articles per file
MAX_RUNTIME_HOURS = 8  # Run for 8 hours
SLEEP_BETWEEN_RUNS = 300  # 5 minutes between ingestion cycles

def fetch_news(ticker):
    """Fetch news for a specific ticker"""
    url = (
        "https://www.alphavantage.co/query?"
        f"function=NEWS_SENTIMENT&tickers={ticker}&apikey={API_KEY}"
    )
    r = requests.get(url)
    if r.status_code != 200:
        print(f"Errore per {ticker}: {r.status_code}")
        return []
    return r.json().get("feed", [])

def load_existing_articles():
    """Load all existing articles from all previous files"""
    existing_articles = []
    existing_urls = set()
    
    # Find all existing news data files
    pattern = "output/news_data_*.json"
    files = glob.glob(pattern)
    
    if not files:
        print("No existing files found, starting fresh")
        return existing_articles, existing_urls
    
    print(f"Loading existing articles from {len(files)} files...")
    
    for file in sorted(files):
        try:
            with open(file, "r", encoding="utf-8") as f:
                articles = json.load(f)
                for article in articles:
                    url = article.get("url", "")
                    if url and url not in existing_urls:
                        existing_articles.append(article)
                        existing_urls.add(url)
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    print(f"Loaded {len(existing_articles)} unique articles from existing files")
    return existing_articles, existing_urls

def write_batch_file(articles, batch_number):
    """Write a batch of articles to a separate file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"output/news_data_batch_{batch_number:04d}_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Written batch {batch_number}: {len(articles)} articles -> {filename}")
    return filename

def run_continuous_ingestion():
    """Run continuous ingestion for historical data collection"""
    print("🚀 Starting continuous historical data ingestion...")
    print(f"⏰ Will run for {MAX_RUNTIME_HOURS} hours")
    print(f"📦 Batch size: {BATCH_SIZE} articles per file")
    print(f"🔄 Sleep between runs: {SLEEP_BETWEEN_RUNS} seconds")
    
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=MAX_RUNTIME_HOURS)
    
    # Load existing articles
    existing_articles, existing_urls = load_existing_articles()
    
    # Initialize counters
    total_new_articles = 0
    total_duplicates = 0
    batch_articles = []
    batch_number = 1
    run_number = 1
    
    print(f"\n🕐 Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🕐 Will end at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    while datetime.now() < end_time:
        print(f"\n{'='*60}")
        print(f"🔄 RUN #{run_number} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"⏰ Time remaining: {end_time - datetime.now()}")
        print(f"{'='*60}")
        
        run_new_articles = 0
        run_duplicates = 0
        
        # Process each ticker
        for i, ticker in enumerate(tqdm(TICKERS, desc=f"Run #{run_number}")):
            print(f"\n📈 Fetching news for {ticker}...")
            news_list = fetch_news(ticker)
            
            ticker_new = 0
            ticker_duplicates = 0
            
            for item in news_list:
                # Add source ticker info
                item["source_ticker"] = ticker
                item["ingestion_timestamp"] = datetime.now().isoformat()
                
                # Check for duplicates
                if item.get("url", "") in existing_urls:
                    ticker_duplicates += 1
                    run_duplicates += 1
                    total_duplicates += 1
                    continue
                
                # New article found
                ticker_new += 1
                run_new_articles += 1
                total_new_articles += 1
                existing_urls.add(item.get("url", ""))
                batch_articles.append(item)
                
                # Write batch if full
                if len(batch_articles) >= BATCH_SIZE:
                    write_batch_file(batch_articles, batch_number)
                    batch_articles = []
                    batch_number += 1
            
            print(f"  ✅ {ticker}: {ticker_new} new, {ticker_duplicates} duplicates")
            
            # Sleep between API calls
            if i < len(TICKERS) - 1:
                print(f"  ⏳ Waiting 12 seconds...")
                time.sleep(12)
        
        # Write remaining articles in final batch of this run
        if batch_articles:
            write_batch_file(batch_articles, batch_number)
            batch_articles = []
            batch_number += 1
        
        # Print run summary
        print(f"\n📊 Run #{run_number} Summary:")
        print(f"   • New articles: {run_new_articles}")
        print(f"   • Duplicates: {run_duplicates}")
        print(f"   • Total new so far: {total_new_articles}")
        print(f"   • Total duplicates so far: {total_duplicates}")
        print(f"   • Batches written: {batch_number - 1}")
        
        # Check if we should continue
        if datetime.now() >= end_time:
            print(f"\n⏰ Time limit reached! Stopping ingestion.")
            break
        
        # Sleep before next run
        print(f"\n😴 Sleeping {SLEEP_BETWEEN_RUNS} seconds before next run...")
        time.sleep(SLEEP_BETWEEN_RUNS)
        run_number += 1
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"🎉 CONTINUOUS INGESTION COMPLETED!")
    print(f"{'='*60}")
    print(f"📊 Final Summary:")
    print(f"   • Total runs: {run_number - 1}")
    print(f"   • Total new articles: {total_new_articles}")
    print(f"   • Total duplicates skipped: {total_duplicates}")
    print(f"   • Total batches written: {batch_number - 1}")
    print(f"   • Runtime: {datetime.now() - start_time}")
    print(f"   • Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   • Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if total_new_articles == 0:
        print("   ⚠️  No new articles found during the entire run!")

def run_ingestion():
    """Legacy function for single run - now calls continuous"""
    run_continuous_ingestion()

if __name__ == "__main__":
    run_continuous_ingestion()
