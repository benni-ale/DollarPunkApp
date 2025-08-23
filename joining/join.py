import pandas as pd, json
from pathlib import Path
import sys
import hashlib
import os
import pickle
import time
import glob
from datetime import datetime
from tqdm import tqdm

# ---- file di input/output ----
ARTICLES_PATTERN = "output/scraped/scraped_*.json"  # All scraped files (original + distributed)
METRICS_CSV   = "output/processed/tickers.csv"   # url, overall_*, ticker, relevance_*, ticker_sentiment_*
OUT_JSONL     = "output/joined/train.jsonl"
PROCESSED_URLS_FILE = "output/joined/processed_urls.txt"
CHECKPOINT_FILE = "output/joined/checkpoint.pkl"
LOG_FILE = "output/joined/join_process.log"

# ---- logging setup ----
def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    
    # Ensure log directory exists
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry + "\n")

def get_article_files():
    """Get all scraped article files matching the pattern"""
    files = glob.glob(ARTICLES_PATTERN)
    files.sort()  # Sort for consistent processing order
    return files

def load_all_articles_deduplicated():
    """Load all articles from all files and deduplicate by URL"""
    log_message("Loading all articles from all scraped files...")
    
    all_articles = {}  # url -> article_data (will deduplicate)
    total_files = 0
    total_articles = 0
    duplicates_found = 0
    duplicate_files = set()
    
    article_files = get_article_files()
    if not article_files:
        log_message(f"Error: No article files found matching pattern: {ARTICLES_PATTERN}")
        sys.exit(1)
    
    log_message(f"Found {len(article_files)} article files to process")
    
    for file_path in tqdm(article_files, desc="Loading files"):
        file_name = os.path.basename(file_path)
        file_articles = 0
        file_duplicates = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                articles = json.load(f)
                
                for article in articles:
                    url = article.get("url")
                    article_text = article.get("article", "").strip()
                    
                    if url and article_text:
                        if url in all_articles:
                            file_duplicates += 1
                            duplicates_found += 1
                            duplicate_files.add(file_name)
                        
                        # Keep the latest version if URL already exists
                        all_articles[url] = {
                            "url": url,
                            "article": article_text,
                            "summary": article.get("summary", ""),
                            "source_file": file_name
                        }
                        file_articles += 1
                        
        except Exception as e:
            log_message(f"Error reading file {file_name}: {e}")
            continue
            
        total_files += 1
        total_articles += file_articles
    
    log_message(f"=== DEDUPLICATION SUMMARY ===")
    log_message(f"Total files processed: {total_files}")
    log_message(f"Total articles loaded: {total_articles}")
    log_message(f"Found {duplicates_found} duplicates in files: {', '.join(sorted(duplicate_files))}")
    log_message(f"Unique articles after deduplication: {len(all_articles)}")
    
    return list(all_articles.values())

def process_chunk(chunk_articles, output_file, processed_urls_file, processed_urls, 
                 overall_map, tickers_map, processed_count, skipped_count, checkpoint_mgr):
    """Process a chunk of articles"""
    chunk_processed = 0
    chunk_skipped = 0
    
    for article_data in chunk_articles:
        url = article_data.get("url")
        article = (article_data.get("article") or "").strip()
        
        if not article: 
            continue
            
        # Check if already processed
        if url in processed_urls:
            chunk_skipped += 1
            if chunk_skipped % 100 == 0:
                progress = checkpoint_mgr.get_progress_percentage()
                log_message(f"Skipped {chunk_skipped} already processed articles... ({progress:.1f}% complete)")
            continue
        
        # Get data for this URL
        overall = {k:v for k,v in (overall_map.get(url, {}) or {}).items() if pd.notna(v)}
        tickers = tickers_map.get(url, [])
        
        # Create output (without url_hash - that's for internal tracking only)
        output = {
            **overall, 
            "tickers": tickers
        }
        
        row = {
            "input": f"<ARTICLE>\n{article}\n</ARTICLE>",
            "output": output
        }
        
        # Write to file
        output_file.write(json.dumps(row, ensure_ascii=False) + "\n")
        output_file.flush()  # Force write to disk immediately
        
        # Mark as processed
        processed_urls.add(url)
        processed_urls_file.write(url + "\n")
        processed_urls_file.flush()
        
        chunk_processed += 1
        
        # Checkpoint periodically
        if checkpoint_mgr.should_checkpoint(processed_count + chunk_processed):
            checkpoint_mgr.save_checkpoint(processed_count + chunk_processed, skipped_count + chunk_skipped)
            progress = checkpoint_mgr.get_progress_percentage()
            elapsed = time.time() - checkpoint_mgr.state['start_time']
            rate = (processed_count + chunk_processed) / elapsed if elapsed > 0 else 0
            log_message(f"Checkpoint saved: {processed_count + chunk_processed} processed, {skipped_count + chunk_skipped} skipped "
                      f"({progress:.1f}% complete, {rate:.1f} articles/sec)")
    
    return processed_count + chunk_processed, skipped_count + chunk_skipped

# ---- checkpoint management ----
class CheckpointManager:
    def __init__(self, checkpoint_file):
        self.checkpoint_file = checkpoint_file
        self.state = {
            'processed_count': 0,
            'skipped_count': 0,
            'start_time': None,
            'last_checkpoint_time': None,
            'total_articles': 0,
            'checkpoint_interval': 50  # Checkpoint every 50 articles
        }
    
    def load_checkpoint(self):
        """Load checkpoint if exists"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'rb') as f:
                    self.state = pickle.load(f)
                log_message(f"Loaded checkpoint: processed {self.state['processed_count']} articles, "
                          f"skipped {self.state['skipped_count']} articles")
                return True
            except Exception as e:
                log_message(f"Error loading checkpoint: {e}")
        return False
    
    def save_checkpoint(self, processed_count, skipped_count):
        """Save current state to checkpoint"""
        self.state.update({
            'processed_count': processed_count,
            'skipped_count': skipped_count,
            'last_checkpoint_time': time.time()
        })
        
        try:
            Path(self.checkpoint_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.checkpoint_file, 'wb') as f:
                pickle.dump(self.state, f)
        except Exception as e:
            log_message(f"Error saving checkpoint: {e}")
    
    def should_checkpoint(self, current_count):
        """Check if we should save a checkpoint"""
        return current_count % self.state['checkpoint_interval'] == 0
    
    def get_progress_percentage(self):
        """Get progress percentage"""
        if self.state['total_articles'] == 0:
            return 0
        return min(99.9, (self.state['processed_count'] / self.state['total_articles']) * 100)

# ---- load ----
try:
    # Load all articles and deduplicate by URL
    all_articles = load_all_articles_deduplicated()
    
    # Load metrics first (we need this for all articles)
    log_message(f"Loading metrics from: {METRICS_CSV}")
    met = pd.read_csv(METRICS_CSV, engine="python")
    log_message(f"Loaded {len(met)} metric records")
    
except FileNotFoundError as e:
    log_message(f"Error: File not found - {e}")
    sys.exit(1)
except Exception as e:
    log_message(f"Error loading data: {e}")
    sys.exit(1)

# colonne attese (crea vuote se mancano)
need = ["url","overall_sentiment_score","overall_sentiment_label",
        "ticker","relevance_score","ticker_sentiment_score","ticker_sentiment_label"]
for c in need:
    if c not in met.columns: met[c] = None

# tickers per URL (dedup per ticker, tiene la riga con relevance_score più alta)
def tickers_for(g):
    g = g.dropna(subset=["ticker"]).sort_values("relevance_score", ascending=False)
    g = g.drop_duplicates("ticker", keep="first")
    out = []
    for _, r in g.iterrows():
        d = {
            "ticker": r["ticker"],
            "relevance_score": float(r["relevance_score"]) if pd.notna(r["relevance_score"]) else None,
            "ticker_sentiment_score": float(r["ticker_sentiment_score"]) if pd.notna(r["ticker_sentiment_score"]) else None,
            "ticker_sentiment_label": r["ticker_sentiment_label"],
        }
        out.append({k:v for k,v in d.items() if v is not None})
    return out

log_message("Processing tickers...")
# Add progress bar for ticker processing
tickers_map = {}
url_groups = met.groupby("url", dropna=True)
total_groups = len(url_groups)

log_message(f"Found {total_groups} unique URLs in metrics data")

urls_with_tickers = 0
urls_without_tickers = 0

for url, group in tqdm(url_groups, total=total_groups, desc="Processing tickers"):
    tickers = tickers_for(group)
    tickers_map[url] = tickers
    
    if tickers:
        urls_with_tickers += 1
    else:
        urls_without_tickers += 1

log_message(f"Ticker processing complete: {urls_with_tickers} URLs with tickers, {urls_without_tickers} without")

# overall per URL (prima occorrenza)
log_message("Processing overall sentiment...")
overall_data = met.dropna(subset=["url"]).drop_duplicates("url")
overall_map = {}

urls_with_sentiment = 0
urls_without_sentiment = 0

for _, row in tqdm(overall_data.iterrows(), total=len(overall_data), desc="Processing sentiment"):
    url = row["url"]
    sentiment_score = row["overall_sentiment_score"]
    sentiment_label = row["overall_sentiment_label"]
    
    overall_map[url] = {
        "overall_sentiment_score": sentiment_score,
        "overall_sentiment_label": sentiment_label
    }
    
    if pd.notna(sentiment_score) or pd.notna(sentiment_label):
        urls_with_sentiment += 1
    else:
        urls_without_sentiment += 1

log_message(f"Sentiment processing complete: {urls_with_sentiment} URLs with sentiment, {urls_without_sentiment} without")

# ---- setup output and checkpointing ----
log_message(f"Setting up output directory: {OUT_JSONL}")
Path(OUT_JSONL).parent.mkdir(parents=True, exist_ok=True)

# Initialize checkpoint manager
checkpoint_mgr = CheckpointManager(CHECKPOINT_FILE)
checkpoint_mgr.state['start_time'] = time.time()
checkpoint_mgr.state['total_articles'] = len(all_articles)

# Load checkpoint if exists
if checkpoint_mgr.load_checkpoint():
    log_message(f"Resuming from checkpoint: {checkpoint_mgr.state['processed_count']} already processed")

# Load already processed URLs (for incremental processing)
processed_urls = set()
if os.path.exists(PROCESSED_URLS_FILE):
    with open(PROCESSED_URLS_FILE, 'r', encoding='utf-8') as f:
        processed_urls = set(line.strip() for line in f if line.strip())
    log_message(f"Found {len(processed_urls)} already processed URLs")

# ---- process articles in chunks ----
CHUNK_SIZE = 100  # Process 100 articles at a time
log_message(f"Starting chunked processing with chunk size: {CHUNK_SIZE}")

processed_count = checkpoint_mgr.state['processed_count']
skipped_count = checkpoint_mgr.state['skipped_count']

# Open file in append mode if resuming, write mode if new
mode = 'a' if os.path.exists(OUT_JSONL) else 'w'
processed_urls_file = open(PROCESSED_URLS_FILE, 'a', encoding='utf-8')

try:
    with open(OUT_JSONL, mode, encoding="utf-8") as f:
        # Process articles in chunks
        for i in range(0, len(all_articles), CHUNK_SIZE):
            chunk = all_articles[i:i+CHUNK_SIZE]
            
            log_message(f"Processing chunk {i//CHUNK_SIZE + 1}/{(len(all_articles) + CHUNK_SIZE - 1)//CHUNK_SIZE} "
                      f"({len(chunk)} articles)...")
            
            processed_count, skipped_count = process_chunk(
                chunk, f, processed_urls_file, 
                processed_urls, overall_map, tickers_map, 
                processed_count, skipped_count, checkpoint_mgr
            )

except KeyboardInterrupt:
    log_message("Process interrupted by user. Saving checkpoint...")
    checkpoint_mgr.save_checkpoint(processed_count, skipped_count)
    raise
except Exception as e:
    log_message(f"Error during processing: {e}")
    checkpoint_mgr.save_checkpoint(processed_count, skipped_count)
    raise
finally:
    processed_urls_file.close()

# Final checkpoint
checkpoint_mgr.save_checkpoint(processed_count, skipped_count)

# Calculate final statistics
total_time = time.time() - checkpoint_mgr.state['start_time']
avg_rate = processed_count / total_time if total_time > 0 else 0

# Calculate join statistics
total_with_tickers = 0
total_with_sentiment = 0
total_with_both = 0
total_with_neither = 0

# Read the output file to get final statistics
if os.path.exists(OUT_JSONL):
    with open(OUT_JSONL, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                output = data.get('output', {})
                tickers = output.get('tickers', [])
                has_sentiment = any(k.startswith('overall_sentiment') for k in output.keys())
                
                has_tickers = len(tickers) > 0
                
                if has_tickers and has_sentiment:
                    total_with_both += 1
                elif has_tickers:
                    total_with_tickers += 1
                elif has_sentiment:
                    total_with_sentiment += 1
                else:
                    total_with_neither += 1
            except:
                continue

log_message(f"=== PROCESSING COMPLETE ===")
log_message(f"Total articles loaded: {len(all_articles)}")
log_message(f"Successfully processed: {processed_count} new articles")
log_message(f"Skipped: {skipped_count} already processed articles")
log_message(f"Total processed: {len(processed_urls)}")
log_message(f"Total time: {total_time:.1f} seconds")
log_message(f"Average rate: {avg_rate:.1f} articles/second")

log_message(f"=== JOIN STATISTICS ===")
log_message(f"Articles with both tickers and sentiment: {total_with_both}")
log_message(f"Articles with tickers only: {total_with_tickers}")
log_message(f"Articles with sentiment only: {total_with_sentiment}")
log_message(f"Articles with neither: {total_with_neither}")

if processed_count > 0:
    log_message(f"Join coverage:")
    log_message(f"  - Tickers coverage: {((total_with_both + total_with_tickers) / processed_count * 100):.1f}%")
    log_message(f"  - Sentiment coverage: {((total_with_both + total_with_sentiment) / processed_count * 100):.1f}%")
    log_message(f"  - Full coverage: {(total_with_both / processed_count * 100):.1f}%")

log_message(f"Output file: {Path(OUT_JSONL).resolve()}")
log_message(f"Checkpoint file: {Path(CHECKPOINT_FILE).resolve()}")
log_message(f"Log file: {Path(LOG_FILE).resolve()}")
