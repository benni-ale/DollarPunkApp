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
MAX_TICKERS_PER_RUN = int(os.getenv("MAX_TICKERS_PER_RUN", "3"))  # Process max 3 tickers per run
MAX_RETRIES = 3  # Maximum retries for failed API calls

def fetch_news(ticker, time_from=None, time_to=None):
    """Fetch news for a specific ticker with optional date filtering"""
    url = (
        "https://www.alphavantage.co/query?"
        f"function=NEWS_SENTIMENT&tickers={ticker}&apikey={API_KEY}"
    )
    
    # Add date filters if provided
    if time_from:
        url += f"&time_from={time_from}"
    if time_to:
        url += f"&time_to={time_to}"
    
    print(f"🔗 API URL: {url}")
    
    r = requests.get(url)
    if r.status_code != 200:
        print(f"❌ Error for {ticker}: HTTP {r.status_code}")
        return []
    
    response = r.json()
    print(f"📊 Response keys: {list(response.keys())}")
    
    # Check for API errors and rate limiting
    if "Information" in response:
        info_msg = response["Information"]
        print(f"⚠️  API Information: {info_msg}")
        
        if "API call frequency" in info_msg or "rate" in info_msg.lower():
            print("🚫 Rate limit exceeded! Waiting 2 minutes...")
            time.sleep(120)  # Wait 2 minutes
            return []
        elif "limit" in info_msg.lower():
            print("🚫 API limit reached! Waiting 1 minute...")
            time.sleep(60)  # Wait 1 minute
            return []
        else:
            print(f"ℹ️  API Info: {info_msg}")
            # Try fallback without date filters
            if time_from or time_to:
                print("🔄 Trying fallback without date filters...")
                return fetch_news(ticker)  # Recursive call without date filters
            return []
    
    if "Error Message" in response:
        print(f"❌ API Error: {response['Error Message']}")
        # Try fallback without date filters
        if time_from or time_to:
            print("🔄 Trying fallback without date filters...")
            return fetch_news(ticker)  # Recursive call without date filters
        return []
    
    if "Note" in response:
        print(f"⚠️  API Note: {response['Note']}")
        if "limit" in response['Note'].lower():
            print("🚫 API limit reached! Waiting 1 minute...")
            time.sleep(60)
            return []
        # Try fallback without date filters
        if time_from or time_to:
            print("🔄 Trying fallback without date filters...")
            return fetch_news(ticker)  # Recursive call without date filters
        return []
    
    feed = response.get("feed", [])
    print(f"📊 Feed length: {len(feed)}")
    
    return feed

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
    
    # Get date range for this batch
    if articles:
        first_article_date = articles[0].get("time_published", "N/A")
        last_article_date = articles[-1].get("time_published", "N/A")
        date_info = f" | 📅 {first_article_date} → {last_article_date}"
    else:
        date_info = ""
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Written batch {batch_number}: {len(articles)} articles -> {filename}{date_info}")
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

def test_api_connection():
    """Test API connection with a simple request"""
    print("🔍 Testing API connection...")
    
    # Test with a simple request (no date filters)
    test_url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=AAPL&apikey={API_KEY}"
    print(f"🔗 Test URL: {test_url}")
    
    try:
        r = requests.get(test_url)
        if r.status_code != 200:
            print(f"❌ API test failed: HTTP {r.status_code}")
            return False
        
        response = r.json()
        print(f"📊 Test response keys: {list(response.keys())}")
        
        if "Information" in response:
            print(f"⚠️  API test returned info: {response['Information']}")
            return False
        
        if "Error Message" in response:
            print(f"❌ API test error: {response['Error Message']}")
            return False
        
        feed = response.get("feed", [])
        print(f"✅ API test successful! Feed length: {len(feed)}")
        return True
        
    except Exception as e:
        print(f"❌ API test exception: {e}")
        return False

def fetch_historical_news_year():
    """Fetch news from the last year with intelligent batching - starting from oldest"""
    print("🚀 Starting historical news ingestion for the last year...")
    print("📅 Processing from OLDEST to NEWEST articles")
    
    # Test API connection first
    if not test_api_connection():
        print("❌ API connection test failed. Please check your API key and plan.")
        return
    
    print("✅ API connection test passed. Proceeding with ingestion...")
    
    # Calculate date range (last 365 days) - break into smaller chunks
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Break into 30-day chunks to avoid overwhelming the API
    chunk_days = 30
    total_chunks = (365 + chunk_days - 1) // chunk_days
    
    print(f"📅 Fetching news from: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"⏰ Total days: 365 (broken into {total_chunks} chunks of {chunk_days} days)")
    print(f"📦 Batch size: {BATCH_SIZE} articles per file")
    
    # Load existing articles
    existing_articles, existing_urls = load_existing_articles()
    
    # Initialize counters
    total_new_articles = 0
    total_duplicates = 0
    batch_articles = []
    batch_number = 1
    
    # Process each ticker (limited to avoid overwhelming the API)
    tickers_to_process = TICKERS[:MAX_TICKERS_PER_RUN]
    print(f"📊 Processing {len(tickers_to_process)} out of {len(TICKERS)} tickers (MAX_TICKERS_PER_RUN={MAX_TICKERS_PER_RUN})")
    
    for ticker_index, ticker in enumerate(tickers_to_process):
        print(f"\n{'='*60}")
        print(f"📈 Processing ticker {ticker_index + 1}/{len(tickers_to_process)}: {ticker}")
        print(f"{'='*60}")
        
        ticker_total_new = 0
        ticker_total_duplicates = 0
        
        # Process in smaller date chunks
        current_start = start_date
        chunk_number = 1
        
        while current_start < end_date:
            current_end = min(current_start + timedelta(days=chunk_days), end_date)
            
            print(f"📅 Processing chunk {chunk_number}/{total_chunks}: {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')}")
            
            # Format dates for API (YYYYMMDDTHHMMSS)
            time_from = current_start.strftime("%Y%m%dT000000")
            time_to = current_end.strftime("%Y%m%dT235959")
            
            print(f"📅 Using date range: {time_from} to {time_to}")
            
            # Retry logic for API calls
            news_list = []
            for retry in range(MAX_RETRIES):
                news_list = fetch_news(ticker, time_from=time_from, time_to=time_to)
                if news_list or retry == MAX_RETRIES - 1:
                    break
                print(f"🔄 Retry {retry + 1}/{MAX_RETRIES} for {ticker} chunk {chunk_number}")
                time.sleep(30)  # Wait before retry
            
            # Reverse the list to process from oldest to newest
            news_list.reverse()
            print(f"🔄 Reversed order: processing {len(news_list)} articles from oldest to newest")
            
            # Show date range of articles
            if news_list:
                first_article_date = news_list[0].get("time_published", "N/A")
                last_article_date = news_list[-1].get("time_published", "N/A")
                print(f"📅 Date range: {first_article_date} (oldest) → {last_article_date} (newest)")
            
            ticker_new = 0
            ticker_duplicates = 0
            
            for item in news_list:
                # Add metadata
                item["source_ticker"] = ticker
                item["ingestion_timestamp"] = datetime.now().isoformat()
                item["historical_fetch"] = True
                item["fetch_date_range"] = {
                    "start_date": current_start.strftime("%Y-%m-%d"),
                    "end_date": current_end.strftime("%Y-%m-%d"),
                    "days_back": 365
                }
                
                # Check for duplicates
                if item.get("url", "") in existing_urls:
                    ticker_duplicates += 1
                    ticker_total_duplicates += 1
                    total_duplicates += 1
                    continue
                
                # New article found
                ticker_new += 1
                ticker_total_new += 1
                total_new_articles += 1
                existing_urls.add(item.get("url", ""))
                batch_articles.append(item)
                
                # Write batch if full
                if len(batch_articles) >= BATCH_SIZE:
                    write_batch_file(batch_articles, batch_number)
                    batch_articles = []
                    batch_number += 1
            
            print(f"✅ Chunk {chunk_number} results: {ticker_new} new, {ticker_duplicates} duplicates")
            
            # Move to next chunk
            current_start = current_end
            chunk_number += 1
            
            # Wait between chunks to respect API limits
            if chunk_number <= total_chunks:
                print(f"⏳ Waiting 45 seconds before next chunk...")
                time.sleep(45)
        
        print(f"✅ {ticker} results:")
        print(f"   • New articles: {ticker_total_new}")
        print(f"   • Duplicates: {ticker_total_duplicates}")
        print(f"   • Total for this ticker: {ticker_total_new} new, {ticker_total_duplicates} duplicates")
        
        # Sleep between tickers to respect API limits
        if ticker_index < len(tickers_to_process) - 1:
            print(f"⏳ Waiting 90 seconds before next ticker...")
            time.sleep(90)  # Increased from 15 to 90 seconds
    
    # Write remaining articles
    if batch_articles:
        write_batch_file(batch_articles, batch_number)
        batch_number += 1
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"🎉 HISTORICAL YEAR INGESTION COMPLETED!")
    print(f"{'='*60}")
    print(f"📊 Final Summary:")
    print(f"   • Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"   • Processing order: OLDEST to NEWEST")
    print(f"   • Total new articles: {total_new_articles}")
    print(f"   • Total duplicates skipped: {total_duplicates}")
    print(f"   • Total batches written: {batch_number - 1}")
    print(f"   • Tickers processed: {len(tickers_to_process)} out of {len(TICKERS)}")
    
    if len(tickers_to_process) < len(TICKERS):
        remaining_tickers = TICKERS[len(tickers_to_process):]
        print(f"   • Remaining tickers for next run: {', '.join(remaining_tickers)}")
    
    if total_new_articles == 0:
        print("   ⚠️  No new articles found in the last year!")
    else:
        print(f"   📈 Average articles per ticker: {total_new_articles / len(tickers_to_process):.1f}")

def run_ingestion():
    """Legacy function for single run - now calls continuous"""
    run_continuous_ingestion()

if __name__ == "__main__":
    print("🚀 DollarPunk News Ingester")
    print("=" * 40)
    
    # Check if running in non-interactive mode (Docker)
    ingestion_mode = os.getenv("INGESTION_MODE")
    
    if ingestion_mode:
        # Non-interactive mode
        choice = ingestion_mode.strip()
        print(f"🔧 Non-interactive mode detected: {choice}")
    else:
        # Interactive mode
        print("Choose your ingestion mode:")
        print("1. Continuous ingestion (8 hours, real-time)")
        print("2. Historical year ingestion (last 365 days)")
        print("3. Exit")
        choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\n🔄 Starting continuous ingestion...")
        run_continuous_ingestion()
    elif choice == "2":
        print("\n📅 Starting historical year ingestion...")
        fetch_historical_news_year()
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice. Exiting.")
