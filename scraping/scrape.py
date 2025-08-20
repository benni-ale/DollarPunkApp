# scrape_news_newspaper.py
import csv, json, time, sys
import httpx
import trafilatura
from readability import Document
from lxml import html as LH
from newspaper import Article, Config
from datetime import datetime
import os
import glob

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsScraper/1.0)"}
NP_CFG = Config()
NP_CFG.browser_user_agent = HEADERS["User-Agent"]
NP_CFG.request_timeout = 25

def fetch(url: str, timeout=25) -> str:
    with httpx.Client(follow_redirects=True, headers=HEADERS, timeout=timeout) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text

def try_trafilatura(html: str) -> str:
    return trafilatura.extract(html, include_comments=False, include_links=False) or ""

def try_newspaper(url: str, html: str) -> str:
    try:
        art = Article(url, config=NP_CFG)
        art.set_html(html)            # evita doppio download
        art.parse()
        return (art.text or "").strip()
    except Exception:
        return ""

def try_readability(html: str) -> str:
    try:
        summ = Document(html).summary(html_partial=True)
        return LH.fromstring(summ).text_content().strip()
    except Exception:
        return ""

def extract_best(url: str, html: str) -> str:
    cand = []
    for fn in (try_trafilatura, lambda h: try_newspaper(url, h), try_readability):
        txt = fn(html)
        cand.append(txt)
    # scegli il testo più lungo credibile
    cand = [t for t in cand if t]
    best = max(cand, key=len) if cand else ""
    return " ".join(best.split())

def find_config_file(node_id: str, output_folder: str = "output") -> str:
    """Find the latest config file for a specific node"""
    metadata_dir = os.path.join(output_folder, "metadata")
    pattern = os.path.join(metadata_dir, f"config_*_{node_id}.json")
    config_files = glob.glob(pattern)
    
    if not config_files:
        return None
    
    # Return the most recent config file
    return max(config_files, key=os.path.getctime)

def wait_for_config(node_id: str, output_folder: str = "output", max_wait: int = 300) -> dict:
    """Wait for coordinator to generate config file"""
    print(f"Waiting for config file for {node_id}...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        config_file = find_config_file(node_id, output_folder)
        if config_file:
            print(f"Found config file: {config_file}")
            return load_config(config_file)
        
        print(f"Config file not found yet, waiting... ({int(time.time() - start_time)}s)")
        time.sleep(5)
    
    raise TimeoutError(f"Config file for {node_id} not found after {max_wait} seconds")

def load_config(config_file: str) -> dict:
    """Load node configuration from file"""
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)

def load_existing_results(json_path: str):
    """Load existing results and return a dict of URL -> item"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Handle both old format (list) and new format (with metadata)
            if isinstance(data, dict) and "articles" in data:
                articles = data["articles"]
            else:
                articles = data
            return {item["url"]: item for item in articles}
    except FileNotFoundError:
        print(f"No existing results found at {json_path}")
        return {}
    except Exception as e:
        print(f"Error loading existing results: {e}")
        return {}

def save_results(results: list, json_path: str, metadata: dict):
    """Save results to JSON file with metadata"""
    output_data = {
        "metadata": metadata,
        "articles": results
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

def main_from_config(config_file: str):
    """Main function that works with coordinator config"""
    print(f"Loading configuration from {config_file}...")
    config = load_config(config_file)
    
    node_id = config["node_id"]
    run_id = config["run_id"]
    urls_to_scrape = config["urls"]
    output_file = config["output_file"]
    
    print(f"Node {node_id} (Run {run_id}): Processing {len(urls_to_scrape)} URLs")
    
    # Load existing results for this specific output file
    existing_results = load_existing_results(output_file)
    print(f"Found {len(existing_results)} existing articles in {os.path.basename(output_file)}")
    
    # Filter out already processed URLs
    new_urls = {url: summary for url, summary in urls_to_scrape.items() if url not in existing_results}
    print(f"Need to scrape {len(new_urls)} new URLs")
    
    if not new_urls:
        print("All URLs already processed!")
        return
    
    # Start with existing results
    out = list(existing_results.values())
    chunk_size = 50
    
    # Prepare metadata
    metadata = {
        "node_id": node_id,
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "total_urls_assigned": len(urls_to_scrape),
        "urls_to_scrape": len(new_urls),
        "scraped_count": 0,
        "error_count": 0
    }
    
    for i, (url, summary) in enumerate(new_urls.items(), 1):
        print(f"[{node_id}] Scraping {i}/{len(new_urls)}: {url[:80]}...")
        item = {
            "url": url, 
            "summary": summary, 
            "article": "",
            "node_id": node_id,
            "run_id": run_id,
            "scraped_at": datetime.now().isoformat()
        }
        
        try:
            html = fetch(url)
            item["article"] = extract_best(url, html)
            print(f"  ✓ Success - Article length: {len(item['article'])} chars")
            metadata["scraped_count"] += 1
        except Exception as e:
            item["error"] = f"{type(e).__name__}: {e}"
            print(f"  ✗ Error: {type(e).__name__}: {e}")
            metadata["error_count"] += 1
            
        out.append(item)
        
        # Save incrementally every chunk_size items
        if i % chunk_size == 0:
            print(f"💾 Saving chunk {i//chunk_size} ({len(out)} total articles)...")
            save_results(out, output_file, metadata)
        
        time.sleep(0.5)
    
    # Save final results
    print(f"💾 Saving final results to {output_file}...")
    save_results(out, output_file, metadata)
    print(f"Scraping completed! Total articles: {len(out)}")

def main_wait_for_config(node_id: str):
    """Main function that waits for coordinator to generate config"""
    try:
        config = wait_for_config(node_id)
        main_from_config_dict(config)
    except Exception as e:
        print(f"Error waiting for config: {e}")
        sys.exit(1)

def main_from_config_dict(config: dict):
    """Main function that works with config dictionary"""
    node_id = config["node_id"]
    run_id = config["run_id"]
    urls_to_scrape = config["urls"]
    output_file = config["output_file"]
    
    print(f"Node {node_id} (Run {run_id}): Processing {len(urls_to_scrape)} URLs")
    
    # Load existing results for this specific output file
    existing_results = load_existing_results(output_file)
    print(f"Found {len(existing_results)} existing articles in {os.path.basename(output_file)}")
    
    # Filter out already processed URLs
    new_urls = {url: summary for url, summary in urls_to_scrape.items() if url not in existing_results}
    print(f"Need to scrape {len(new_urls)} new URLs")
    
    if not new_urls:
        print("All URLs already processed!")
        return
    
    # Start with existing results
    out = list(existing_results.values())
    chunk_size = 50
    
    # Prepare metadata
    metadata = {
        "node_id": node_id,
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "total_urls_assigned": len(urls_to_scrape),
        "urls_to_scrape": len(new_urls),
        "scraped_count": 0,
        "error_count": 0
    }
    
    for i, (url, summary) in enumerate(new_urls.items(), 1):
        print(f"[{node_id}] Scraping {i}/{len(new_urls)}: {url[:80]}...")
        item = {
            "url": url, 
            "summary": summary, 
            "article": "",
            "node_id": node_id,
            "run_id": run_id,
            "scraped_at": datetime.now().isoformat()
        }
        
        try:
            html = fetch(url)
            item["article"] = extract_best(url, html)
            print(f"  ✓ Success - Article length: {len(item['article'])} chars")
            metadata["scraped_count"] += 1
        except Exception as e:
            item["error"] = f"{type(e).__name__}: {e}"
            print(f"  ✗ Error: {type(e).__name__}: {e}")
            metadata["error_count"] += 1
            
        out.append(item)
        
        # Save incrementally every chunk_size items
        if i % chunk_size == 0:
            print(f"💾 Saving chunk {i//chunk_size} ({len(out)} total articles)...")
            save_results(out, output_file, metadata)
        
        time.sleep(0.5)
    
    # Save final results
    print(f"💾 Saving final results to {output_file}...")
    save_results(out, output_file, metadata)
    print(f"Scraping completed! Total articles: {len(out)}")

def main_legacy(in_csv: str, out_json: str, start_index: int = 0, end_index: int = None, node_id: str = "node1"):
    """Legacy main function for backward compatibility"""
    print(f"Loading URLs from {in_csv} (range: {start_index}-{end_index or 'end'})...")
    url2sum = load_url_summary(in_csv, start_index, end_index)
    print(f"Node {node_id}: Found {len(url2sum)} unique URLs to scrape")
    
    # Load existing results
    existing_results = load_existing_results(out_json)
    print(f"Found {len(existing_results)} existing scraped articles")
    
    # Filter out already processed URLs
    new_urls = {url: summary for url, summary in url2sum.items() if url not in existing_results}
    print(f"Need to scrape {len(new_urls)} new URLs")
    
    if not new_urls:
        print("All URLs already processed!")
        return
    
    # Start with existing results
    out = list(existing_results.values())
    chunk_size = 50
    
    for i, (url, summary) in enumerate(new_urls.items(), 1):
        print(f"[{node_id}] Scraping {i}/{len(new_urls)}: {url[:80]}...")
        item = {"url": url, "summary": summary, "article": ""}
        try:
            html = fetch(url)
            item["article"] = extract_best(url, html)
            print(f"  ✓ Success - Article length: {len(item['article'])} chars")
        except Exception as e:
            item["error"] = f"{type(e).__name__}: {e}"
            print(f"  ✗ Error: {type(e).__name__}: {e}")
        out.append(item)
        
        # Save incrementally every chunk_size items
        if i % chunk_size == 0:
            print(f"💾 Saving chunk {i//chunk_size} ({len(out)} total articles)...")
            save_results(out, out_json, {"legacy": True})
        
        time.sleep(0.5)
    
    # Save final results
    print(f"💾 Saving final results to {out_json}...")
    save_results(out, out_json, {"legacy": True})
    print(f"Scraping completed! Total articles: {len(out)}")

def load_url_summary(csv_path: str, start_index: int = 0, end_index: int = None):
    """Load URLs from CSV with optional slicing for parallel processing"""
    seen = {}
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # Skip if before start_index
            if i < start_index:
                continue
            # Stop if after end_index
            if end_index is not None and i >= end_index:
                break
                
            u = (row.get("url") or "").strip()
            if u and u not in seen:
                seen[u] = (row.get("summary") or "").strip()
    return seen

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Configuration file from coordinator")
    parser.add_argument("--wait-for-config", help="Wait for coordinator to generate config for this node")
    parser.add_argument("input_csv", default="input.csv", nargs="?", help="Input CSV file (legacy mode)")
    parser.add_argument("output_json", default="scraped_news.json", nargs="?", help="Output JSON file (legacy mode)")
    parser.add_argument("--start", type=int, default=0, help="Starting index for this node (legacy mode)")
    parser.add_argument("--end", type=int, default=None, help="Ending index for this node (legacy mode)")
    parser.add_argument("--node-id", default="node1", help="Node identifier (legacy mode)")
    
    args = parser.parse_args()
    
    if args.wait_for_config:
        # New wait-for-config mode
        main_wait_for_config(args.wait_for_config)
    elif args.config:
        # New coordinator mode
        main_from_config(args.config)
    else:
        # Legacy mode
        main_legacy(args.input_csv, args.output_json, args.start, args.end, args.node_id)
