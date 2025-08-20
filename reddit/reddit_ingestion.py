# root/reddit/script.py
# Prereq: pip install praw python-dotenv
# .env (in root/.env): REDDIT_CLIENT_ID=... REDDIT_CLIENT_SECRET=... REDDIT_USER_AGENT=...

import os, json, argparse, sys, logging
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import praw

def iso(ts): 
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def load_processed_posts(tracking_file):
    """Load list of already processed post IDs from JSON file"""
    if tracking_file.exists():
        try:
            with open(tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('processed_posts', []))
        except Exception as e:
            print(f"Warning: Could not load tracking file: {e}")
    return set()

def save_processed_posts(tracking_file, processed_posts):
    """Save list of processed post IDs to JSON file"""
    data = {
        'processed_posts': list(processed_posts),
        'last_updated': datetime.now().isoformat()
    }
    with open(tracking_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def ser_comment(c, depth, max_depth, max_replies):
    if depth > max_depth: 
        return None
    item = {
        "id": getattr(c, "id", None),
        "parent_id": getattr(c, "parent_id", None),
        "author": str(getattr(c, "author", None)) if getattr(c, "author", None) else None,
        "body": getattr(c, "body", ""),
        "score": int(getattr(c, "score", 0)),
        "created_utc": iso(getattr(c, "created_utc", 0)),
        "depth": depth,
        "replies": []
    }
    for r in list(getattr(c, "replies", []))[:max_replies]:
        sc = ser_comment(r, depth + 1, max_depth, max_replies)
        if sc: 
            item["replies"].append(sc)
    return item

def load_config():
    """Load configuration from .conf file"""
    config = {}
    conf_path = Path(__file__).parent / ".conf"
    
    if conf_path.exists():
        with open(conf_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config

def main():
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Reddit ingestion process")
    
    # Load configuration
    config = load_config()
    default_subs = config.get('SUBREDDITS', 'investing+stocks+StockMarket+EuropeFIRE+PersonalFinanceEurope')
    default_query = config.get('QUERY', '(ECB OR FED OR inflation OR earnings OR ETF OR recession)')
    days_to_fetch = int(config.get('DAYS_TO_FETCH', '7'))
    
    # Calculate time filter based on days_to_fetch
    if days_to_fetch <= 1:
        time_filter = "day"
    elif days_to_fetch <= 7:
        time_filter = "week"
    elif days_to_fetch <= 30:
        time_filter = "month"
    elif days_to_fetch <= 365:
        time_filter = "year"
    else:
        time_filter = "all"
    
    ap = argparse.ArgumentParser(description="Reddit finance → JSONL con top commenti")
    ap.add_argument("--subs", default=default_subs)
    ap.add_argument("--q", default=default_query)
    ap.add_argument("--time", default=time_filter, choices=["hour","day","week","month","year","all"])
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--out", default="output/reddit/fin_reddit.jsonl")
    ap.add_argument("--top_n", type=int, default=4, help="# top commenti top-level per score")
    ap.add_argument("--max_depth", type=int, default=2, help="profondità reply")
    ap.add_argument("--max_replies", type=int, default=50, help="limite reply per livello")
    ap.add_argument("--replace_more", type=int, default=16, help="0=espandi tutti (lento)")
    ap.add_argument("--chunk_size", type=int, default=10, help="numero di post per chunk")
    args = ap.parse_args()

    logger.info(f"Configuration: subs={args.subs}, query={args.q}, limit={args.limit}, chunk_size={args.chunk_size}, days_to_fetch={days_to_fetch}, time_filter={args.time}")

    # Carica credenziali da .env (montato dal docker-compose)
    env_path = Path(".env")
    if not env_path.exists():
        # Fallback: prova a cercare nella root del progetto
        env_path = Path(__file__).resolve().parents[1] / ".env"
    
    load_dotenv(dotenv_path=env_path)

    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT"),
    )
    reddit.read_only = True

    # Ensure output directory exists
    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Setup tracking file for processed posts
    tracking_file = output_path.parent / "processed_posts.json"
    processed_posts = load_processed_posts(tracking_file)
    logger.info(f"Loaded {len(processed_posts)} already processed posts")

    sr = reddit.subreddit(args.subs)
    it = sr.search(query=args.q, sort="new", time_filter=args.time, syntax="lucene", limit=args.limit)

    written = 0
    skipped = 0
    
    # Process posts one by one for immediate writing
    posts = list(it)
    total_posts = len(posts)
    logger.info(f"Found {total_posts} posts to process")
    
    for i, s in enumerate(posts, 1):
        try:
            # Check if post already processed
            if s.id in processed_posts:
                logger.info(f"Skipping already processed post: {s.id} - {s.title[:50]}...")
                skipped += 1
                continue
            
            logger.info(f"Processing post {i}/{total_posts}: {s.id} - {s.title[:50]}...")
            
            s.comment_sort = "top"  # ordina per score
            s.comments.replace_more(limit=args.replace_more)

            # Solo top-level; prendi i migliori per score
            top_level = [c for c in list(s.comments) if hasattr(c, "score")]
            top_sorted = sorted(top_level, key=lambda c: getattr(c, "score", 0), reverse=True)[:args.top_n]

            comments = []
            for c in top_sorted:
                sc = ser_comment(c, depth=0, max_depth=args.max_depth, max_replies=args.max_replies)
                if sc: 
                    comments.append(sc)

            obj = {
                "id": s.id,
                "subreddit": s.subreddit.display_name,
                "title": s.title,
                "selftext": s.selftext or "",
                "url": s.url,
                "permalink": f"https://www.reddit.com{s.permalink}",
                "author": str(s.author) if s.author else None,
                "flair": getattr(s, "link_flair_text", None),
                "score": s.score,
                "num_comments": s.num_comments,
                "created_utc": iso(s.created_utc),
                "comments": comments
            }
            
            # Write immediately to file
            with open(args.out, "a", encoding="utf-8") as f:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            
            # Mark as processed immediately
            processed_posts.add(s.id)
            save_processed_posts(tracking_file, processed_posts)
            
            written += 1
            logger.info(f"Post {i} written and marked as processed")
            
        except Exception as e:
            logger.error(f"Error processing post {getattr(s, 'id', '?')}: {e}")
        
        # Small delay between posts to be respectful to Reddit API
        import time
        time.sleep(0.5)
    
    logger.info(f"Processing complete: {written} posts written, {skipped} posts skipped")
    print(f"OK → {args.out} | righe: {written} | saltati: {skipped}")

if __name__ == "__main__":
    main()
