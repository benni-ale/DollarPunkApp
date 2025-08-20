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
from typing import Dict

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

def save_results(results: list, json_path: str):
    """Save results to JSON file in original format (just array of articles)"""
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def load_node_config(node_id: str, config_file: str = "output/node_configs.json") -> dict:
    """Load node configuration from the config file"""
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            configs = json.load(f)
            for config in configs:
                if config["node_id"] == node_id:
                    return config
        raise ValueError(f"Node {node_id} not found in configuration")
    except Exception as e:
        print(f"Error loading config for {node_id}: {e}")
        raise

def wait_for_config_file(config_file: str = "output/node_configs.json", max_wait: int = 300) -> bool:
    """Wait for the coordinator to create the config file"""
    print(f"Waiting for config file: {config_file}")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if os.path.exists(config_file):
            print(f"Found config file: {config_file}")
            return True
        
        print(f"Config file not found yet, waiting... ({int(time.time() - start_time)}s)")
        time.sleep(5)
    
    raise TimeoutError(f"Config file not found after {max_wait} seconds")

def load_urls_from_csv_range(csv_path: str, start_index: int, end_index: int) -> Dict[str, str]:
    """Load URLs from CSV within the specified range"""
    urls = {}
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i < start_index:
                continue
            if i >= end_index:
                break
                
            u = (row.get("url") or "").strip()
            if u and u not in urls:
                urls[u] = (row.get("summary") or "").strip()
    return urls

def main_from_config_file(node_id: str):
    """Main function that reads configuration from file"""
    # Wait for coordinator to create config file
    wait_for_config_file()
    
    # Load configuration for this node
    config = load_node_config(node_id)
    
    node_id = config["node_id"]
    run_id = config["run_id"]
    start_index = config["start_index"]
    end_index = config["end_index"]
    url_count = config["url_count"]
    output_file = config["output_file"]
    
    print(f"Node {node_id} (Run {run_id}): Processing URLs {start_index}-{end_index} ({url_count} URLs)")
    
    # Load URLs from CSV for this node's range
    urls_to_scrape = load_urls_from_csv_range("input/tickers.csv", start_index, end_index)
    print(f"Loaded {len(urls_to_scrape)} URLs from CSV range")
    
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
    
    for i, (url, summary) in enumerate(new_urls.items(), 1):
        print(f"[{node_id}] Scraping {i}/{len(new_urls)}: {url[:80]}...")
        item = {
            "url": url, 
            "summary": summary, 
            "article": ""
        }
        
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
            save_results(out, output_file)
        
        time.sleep(0.5)
    
    # Save final results
    print(f"💾 Saving final results to {output_file}...")
    save_results(out, output_file)
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
            save_results(out, out_json)
        
        time.sleep(0.5)
    
    # Save final results
    print(f"💾 Saving final results to {out_json}...")
    save_results(out, out_json)
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
    parser.add_argument("--node-id", required=True, help="Node identifier")
    parser.add_argument("--config-file", default="output/node_configs.json", help="Configuration file path")
    parser.add_argument("input_csv", default="input.csv", nargs="?", help="Input CSV file (legacy mode)")
    parser.add_argument("output_json", default="scraped_news.json", nargs="?", help="Output JSON file (legacy mode)")
    parser.add_argument("--start", type=int, default=0, help="Starting index for this node (legacy mode)")
    parser.add_argument("--end", type=int, default=None, help="Ending index for this node (legacy mode)")
    
    args = parser.parse_args()
    
    if args.node_id:
        # New distributed mode
        main_from_config_file(args.node_id)
    else:
        # Legacy mode
        main_legacy(args.input_csv, args.output_json, args.start, args.end, args.node_id)
