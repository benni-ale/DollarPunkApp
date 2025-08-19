import pandas as pd, json
from pathlib import Path
import sys
import hashlib
import os
import pickle
import time
from datetime import datetime

# ---- file di input/output ----
ARTICLES_JSON = "output/scraped/scraped_articles.json"      # [{"url","article",...}, ...]
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

# ---- checkpoint management ----
class CheckpointManager:
    def __init__(self, checkpoint_file):
        self.checkpoint_file = checkpoint_file
        self.state = {
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
                          f"last index: {self.state['last_processed_index']}")
                return True
            except Exception as e:
                log_message(f"Error loading checkpoint: {e}")
        return False
    
    def save_checkpoint(self, current_index, processed_count, skipped_count):
        """Save current state to checkpoint"""
        self.state.update({
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
        if self.state['total_articles'] == 0:
            return 0
        return (self.state['processed_count'] + self.state['skipped_count']) / self.state['total_articles'] * 100

# ---- load ----
try:
    log_message(f"Loading articles from: {ARTICLES_JSON}")
    art = pd.read_json(ARTICLES_JSON)              # deve avere almeno: url, article
    log_message(f"Loaded {len(art)} articles")
    
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
checkpoint_mgr.state['total_articles'] = len(art)
checkpoint_mgr.state['start_time'] = time.time()

# Load checkpoint if exists
resume_from_index = 0
if checkpoint_mgr.load_checkpoint():
    resume_from_index = checkpoint_mgr.state['last_processed_index']
    log_message(f"Resuming from index {resume_from_index}")

# Load already processed URLs (for incremental processing)
processed_urls = set()
if os.path.exists(PROCESSED_URLS_FILE):
    with open(PROCESSED_URLS_FILE, 'r', encoding='utf-8') as f:
        processed_urls = set(line.strip() for line in f if line.strip())
    log_message(f"Found {len(processed_urls)} already processed URLs")

# Create URL hash function
def get_url_hash(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()

# ---- write JSONL incrementally with checkpointing ----
log_message(f"Starting incremental write to: {OUT_JSONL}")
processed_count = checkpoint_mgr.state['processed_count']
skipped_count = checkpoint_mgr.state['skipped_count']

# Open file in append mode if resuming, write mode if new
mode = 'a' if resume_from_index > 0 and os.path.exists(OUT_JSONL) else 'w'
processed_urls_file = open(PROCESSED_URLS_FILE, 'a', encoding='utf-8')

try:
    with open(OUT_JSONL, mode, encoding="utf-8") as f:
        for idx, r in art.iterrows():
            # Skip if we're resuming and this index was already processed
            if idx < resume_from_index:
                continue
                
            url = r.get("url")
            article = (r.get("article") or "").strip()
            
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
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()  # Force write to disk immediately
            
            # Mark as processed
            processed_urls.add(url)
            processed_urls_file.write(url + "\n")
            processed_urls_file.flush()
            
            processed_count += 1
            
            # Checkpoint periodically
            if checkpoint_mgr.should_checkpoint(processed_count):
                checkpoint_mgr.save_checkpoint(idx, processed_count, skipped_count)
                progress = checkpoint_mgr.get_progress_percentage()
                elapsed = time.time() - checkpoint_mgr.state['start_time']
                rate = processed_count / elapsed if elapsed > 0 else 0
                log_message(f"Checkpoint saved: {processed_count} processed, {skipped_count} skipped "
                          f"({progress:.1f}% complete, {rate:.1f} articles/sec)")

except KeyboardInterrupt:
    log_message("Process interrupted by user. Saving checkpoint...")
    checkpoint_mgr.save_checkpoint(idx, processed_count, skipped_count)
    raise
except Exception as e:
    log_message(f"Error during processing: {e}")
    checkpoint_mgr.save_checkpoint(idx, processed_count, skipped_count)
    raise
finally:
    processed_urls_file.close()

# Final checkpoint
checkpoint_mgr.save_checkpoint(len(art), processed_count, skipped_count)

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
