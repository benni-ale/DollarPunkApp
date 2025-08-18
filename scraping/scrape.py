# scrape_news_newspaper.py
import csv, json, time, sys
import httpx
import trafilatura
from readability import Document
from lxml import html as LH
from newspaper import Article, Config

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

def load_url_summary(csv_path: str):
    seen = {}
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            u = (row.get("url") or "").strip()
            if u and u not in seen:
                seen[u] = (row.get("summary") or "").strip()
    return seen

def load_existing_results(json_path: str):
    """Load existing results and return a dict of URL -> item"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
            return {item["url"]: item for item in existing}
    except FileNotFoundError:
        print(f"No existing results found at {json_path}")
        return {}
    except Exception as e:
        print(f"Error loading existing results: {e}")
        return {}

def save_results(results: list, json_path: str):
    """Save results to JSON file"""
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def main(in_csv: str, out_json: str):
    print(f"Loading URLs from {in_csv}...")
    url2sum = load_url_summary(in_csv)
    print(f"Found {len(url2sum)} unique URLs to scrape")
    
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
    chunk_size = 10
    
    for i, (url, summary) in enumerate(new_urls.items(), 1):
        print(f"Scraping {i}/{len(new_urls)}: {url[:80]}...")
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
        
        time.sleep(0.8)
    
    # Save final results
    print(f"💾 Saving final results to {out_json}...")
    save_results(out, out_json)
    print(f"Scraping completed! Total articles: {len(out)}")

if __name__ == "__main__":
    ic = sys.argv[1] if len(sys.argv) > 1 else "input.csv"
    oj = sys.argv[2] if len(sys.argv) > 2 else "scraped_news.json"
    main(ic, oj)
