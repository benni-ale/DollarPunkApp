import pandas as pd, json
from pathlib import Path
import sys
import hashlib
import os
import pickle
import time
import glob
from datetime import datetime

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

def process_chunk(chunk_articles, output_file, processed_urls_file, processed_urls, 
                 overall_map, tickers_map, processed_count, skipped_count, checkpoint_mgr):
    """Process a chunk of articles"""
    for article_data in chunk_articles:
        url = article_data.get("url")
        article = (article_data.get("article") or "").strip()
        
        if not article: 
            continue
            
        # Check if already processed
        if url in processed_urls:
            skipped_count += 1
            if skipped_count % 100 == 0:
                progress = checkpoint_mgr.get_progress_percentage()
                log_message(f"Skipped {skipped_count} already processed articles... ({progress:.1f}% complete)")
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
        
        processed_count += 1
        
        # Checkpoint periodically
        if checkpoint_mgr.should_checkpoint(processed_count):
            checkpoint_mgr.save_checkpoint(current_file, current_index, processed_count, skipped_count)
            progress = checkpoint_mgr.get_progress_percentage()
            elapsed = time.time() - checkpoint_mgr.state['start_time']
            rate = processed_count / elapsed if elapsed > 0 else 0
            log_message(f"Checkpoint saved: {processed_count} processed, {skipped_count} skipped "
                      f"({progress:.1f}% complete, {rate:.1f} articles/sec)")
    
    return processed_count, skipped_count

# ---- checkpoint management ----
class CheckpointManager:
    def __init__(self, checkpoint_file):
        self.checkpoint_file = checkpoint_file
        self.state = {
            'last_processed_file': '',
            'last_processed_index': 0,
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
                          f"skipped {self.state['skipped_count']} articles, "
                          f"last file: {self.state['last_processed_file']}, "
                          f"last index: {self.state['last_processed_index']}")
                return True
            except Exception as e:
                log_message(f"Error loading checkpoint: {e}")
        return False
    
    def save_checkpoint(self, current_file, current_index, processed_count, skipped_count):
        """Save current state to checkpoint"""
        self.state.update({
            'last_processed_file': current_file,
            'last_processed_index': current_index,
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
        # Since we're processing in chunks, we can't know total articles
        # Just return a simple progress based on processed articles
        if self.state['processed_count'] == 0:
            return 0
        return min(99.9, (self.state['processed_count'] / 1000) * 10)  # Rough estimate

# ---- load ----
try:
    # Get all article files
    article_files = get_article_files()
    if not article_files:
        log_message(f"Error: No article files found matching pattern: {ARTICLES_PATTERN}")
        sys.exit(1)
    
    log_message(f"Found {len(article_files)} article files:")
    total_size = 0
    for file in article_files:
        file_size = os.path.getsize(file)
        total_size += file_size
        log_message(f"  {os.path.basename(file)}: {file_size / (1024*1024):.1f} MB")
    
    log_message(f"Total size: {total_size / (1024*1024):.1f} MB")
    
    # Load metrics first (we need this for all articles)
    log_message(f"Loading metrics from: {METRICS_CSV}")
    met = pd.read_csv(METRICS_CSV, engine="python")
    log_message(f"Loaded {len(met)} metric records")
    
    # Process articles in chunks instead of loading all at once
    log_message("Processing articles in chunks...")
    
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
tickers_map = met.groupby("url", dropna=True).apply(tickers_for).to_dict()

# overall per URL (prima occorrenza)
log_message("Processing overall sentiment...")
overall_map = (met.dropna(subset=["url"])
                 .drop_duplicates("url")
                 .set_index("url")[["overall_sentiment_score","overall_sentiment_label"]]
                 .to_dict(orient="index"))

# ---- setup output and checkpointing ----
log_message(f"Setting up output directory: {OUT_JSONL}")
Path(OUT_JSONL).parent.mkdir(parents=True, exist_ok=True)

# Initialize checkpoint manager
checkpoint_mgr = CheckpointManager(CHECKPOINT_FILE)
checkpoint_mgr.state['start_time'] = time.time()

# Load checkpoint if exists
resume_from_file = ''
resume_from_index = 0
if checkpoint_mgr.load_checkpoint():
    resume_from_file = checkpoint_mgr.state['last_processed_file']
    resume_from_index = checkpoint_mgr.state['last_processed_index']
    log_message(f"Resuming from file: {resume_from_file}, index: {resume_from_index}")

# Load already processed URLs (for incremental processing)
processed_urls = set()
if os.path.exists(PROCESSED_URLS_FILE):
    with open(PROCESSED_URLS_FILE, 'r', encoding='utf-8') as f:
        processed_urls = set(line.strip() for line in f if line.strip())
    log_message(f"Found {len(processed_urls)} already processed URLs")

# Create URL hash function
def get_url_hash(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()

# ---- process JSON files in chunks ----
CHUNK_SIZE = 100  # Process 100 articles at a time
log_message(f"Starting chunked processing with chunk size: {CHUNK_SIZE}")

processed_count = checkpoint_mgr.state['processed_count']
skipped_count = checkpoint_mgr.state['skipped_count']
current_file = resume_from_file
current_index = resume_from_index

# Open file in append mode if resuming, write mode if new
mode = 'a' if resume_from_file and os.path.exists(OUT_JSONL) else 'w'
processed_urls_file = open(PROCESSED_URLS_FILE, 'a', encoding='utf-8')

try:
    with open(OUT_JSONL, mode, encoding="utf-8") as f:
        # Process each article file
        for file_path in article_files:
            file_name = os.path.basename(file_path)
            
            # Skip files we've already processed (for resuming)
            if resume_from_file and file_path < resume_from_file:
                log_message(f"Skipping already processed file: {file_name}")
                continue
            
            log_message(f"Processing file: {file_name}")
            
            # Process JSON in chunks using ijson
            import ijson
            
            chunk_articles = []
            chunk_count = 0
            
            with open(file_path, 'rb') as json_file:
                parser = ijson.parse(json_file)
                current_article = {}
                in_article = False
                
                for prefix, event, value in parser:
                    if prefix == 'item' and event == 'start_map':
                        current_article = {}
                        in_article = True
                    elif prefix == 'item' and event == 'end_map':
                        if current_article.get('url') and current_article.get('article'):
                            # Skip if we're resuming and this index was already processed
                            if file_path == resume_from_file and current_index < resume_from_index:
                                current_index += 1
                                continue
                                
                            chunk_articles.append(current_article)
                            chunk_count += 1
                            
                            # Process chunk when it reaches the size limit
                            if chunk_count >= CHUNK_SIZE:
                                log_message(f"Processing chunk {len(chunk_articles)} articles from {file_name}...")
                                processed_count, skipped_count = process_chunk(
                                    chunk_articles, f, processed_urls_file, 
                                    processed_urls, overall_map, tickers_map, 
                                    processed_count, skipped_count, checkpoint_mgr
                                )
                                chunk_articles = []
                                chunk_count = 0
                                
                        current_index += 1
                        in_article = False
                    elif in_article and prefix.startswith('item.'):
                        field = prefix.split('.', 1)[1]
                        current_article[field] = value
                
                # Process remaining articles in the last chunk
                if chunk_articles:
                    log_message(f"Processing final chunk with {len(chunk_articles)} articles from {file_name}...")
                    processed_count, skipped_count = process_chunk(
                        chunk_articles, f, processed_urls_file, 
                        processed_urls, overall_map, tickers_map, 
                        processed_count, skipped_count, checkpoint_mgr
                    )
            
            # Save checkpoint after each file
            checkpoint_mgr.save_checkpoint(file_path, current_index, processed_count, skipped_count)
            log_message(f"Completed file: {file_name}")

except KeyboardInterrupt:
    log_message("Process interrupted by user. Saving checkpoint...")
    checkpoint_mgr.save_checkpoint(current_file, current_index, processed_count, skipped_count)
    raise
except Exception as e:
    log_message(f"Error during processing: {e}")
    checkpoint_mgr.save_checkpoint(current_file, current_index, processed_count, skipped_count)
    raise
finally:
    processed_urls_file.close()

# Final checkpoint
checkpoint_mgr.save_checkpoint(current_file, current_index, processed_count, skipped_count)

# Calculate final statistics
total_time = time.time() - checkpoint_mgr.state['start_time']
avg_rate = processed_count / total_time if total_time > 0 else 0

log_message(f"=== PROCESSING COMPLETE ===")
log_message(f"Successfully processed: {processed_count} new articles")
log_message(f"Skipped: {skipped_count} already processed articles")
log_message(f"Total processed: {len(processed_urls)}")
log_message(f"Total time: {total_time:.1f} seconds")
log_message(f"Average rate: {avg_rate:.1f} articles/second")
log_message(f"Output file: {Path(OUT_JSONL).resolve()}")
log_message(f"Checkpoint file: {Path(CHECKPOINT_FILE).resolve()}")
log_message(f"Log file: {Path(LOG_FILE).resolve()}")
