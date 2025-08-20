#!/usr/bin/env python3
import csv
import json
import os
import glob
import time
import argparse
from datetime import datetime
from typing import Dict, List, Set

def load_all_urls_from_csv(csv_path: str) -> Dict[str, str]:
    """Load all URLs from CSV file"""
    print(f"Loading all URLs from {csv_path}...")
    url2sum = {}
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            u = (row.get("url") or "").strip()
            if u and u not in url2sum:
                url2sum[u] = (row.get("summary") or "").strip()
    print(f"Found {len(url2sum)} unique URLs in CSV")
    return url2sum

def load_all_existing_results(output_folder: str) -> Dict[str, dict]:
    """Load all existing results from all JSON files in the folder"""
    print(f"Scanning for existing results in {output_folder}...")
    existing_results = {}
    
    # Find all JSON files in the output folder
    json_pattern = os.path.join(output_folder, "scraped_articles_*.json")
    json_files = glob.glob(json_pattern)
    
    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Handle both old format (list) and new format (with metadata)
                if isinstance(data, dict) and "articles" in data:
                    articles = data["articles"]
                else:
                    articles = data
                for item in articles:
                    if "url" in item:
                        existing_results[item["url"]] = item
            print(f"  Loaded {len(articles)} articles from {os.path.basename(json_file)}")
        except Exception as e:
            print(f"  Error loading {json_file}: {e}")
    
    print(f"Total existing articles found: {len(existing_results)}")
    return existing_results

def distribute_workload(urls_to_scrape: Dict[str, str], num_nodes: int) -> List[Dict[str, str]]:
    """Distribute URLs across nodes"""
    url_items = list(urls_to_scrape.items())
    chunk_size = len(url_items) // num_nodes
    
    distribution = []
    for i in range(num_nodes):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size if i < num_nodes - 1 else len(url_items)
        node_urls = dict(url_items[start_idx:end_idx])
        distribution.append(node_urls)
    
    return distribution

def create_node_configs(distribution: List[Dict[str, str]], output_folder: str, run_id: str) -> List[dict]:
    """Create configuration for each node"""
    configs = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create metadata directory
    metadata_dir = os.path.join(output_folder, "metadata")
    os.makedirs(metadata_dir, exist_ok=True)
    
    for i, node_urls in enumerate(distribution, 1):
        if not node_urls:  # Skip empty nodes
            continue
            
        config = {
            "node_id": f"node{i}",
            "run_id": run_id,
            "timestamp": timestamp,
            "urls": node_urls,
            "output_file": os.path.join(output_folder, f"scraped_articles_{run_id}_node{i}.json"),
            "start_index": 0,  # Will be calculated
            "end_index": len(node_urls)
        }
        configs.append(config)
    
    return configs

def save_node_configs(configs: List[dict], output_folder: str):
    """Save node configurations to files"""
    metadata_dir = os.path.join(output_folder, "metadata")
    os.makedirs(metadata_dir, exist_ok=True)
    
    for config in configs:
        config_file = os.path.join(metadata_dir, f"config_{config['run_id']}_{config['node_id']}.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"Saved config for {config['node_id']}: {len(config['urls'])} URLs -> {config['output_file']}")

def main():
    parser = argparse.ArgumentParser(description="Coordinate distributed scraping")
    parser.add_argument("input_csv", help="Input CSV file with URLs")
    parser.add_argument("output_folder", help="Output folder for results")
    parser.add_argument("--nodes", type=int, default=5, help="Number of nodes")
    parser.add_argument("--run-id", default=None, help="Run ID (auto-generated if not provided)")
    
    args = parser.parse_args()
    
    # Generate run ID if not provided
    if not args.run_id:
        args.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"🚀 Starting scraping coordination - Run ID: {args.run_id}")
    print(f"📁 Input: {args.input_csv}")
    print(f"📁 Output: {args.output_folder}")
    print(f"🖥️  Nodes: {args.nodes}")
    
    # Step 1: Load all URLs from CSV
    all_urls = load_all_urls_from_csv(args.input_csv)
    
    # Step 2: Load all existing results
    existing_results = load_all_existing_results(args.output_folder)
    
    # Step 3: Find URLs to scrape
    urls_to_scrape = {url: summary for url, summary in all_urls.items() if url not in existing_results}
    print(f"🎯 URLs to scrape: {len(urls_to_scrape)}")
    
    if not urls_to_scrape:
        print("✅ All URLs already processed!")
        return
    
    # Step 4: Distribute workload
    print(f"📊 Distributing {len(urls_to_scrape)} URLs across {args.nodes} nodes...")
    distribution = distribute_workload(urls_to_scrape, args.nodes)
    
    # Step 5: Create node configurations
    configs = create_node_configs(distribution, args.output_folder, args.run_id)
    
    # Step 6: Save configurations
    save_node_configs(configs, args.output_folder)
    
    # Step 7: Save summary
    summary = {
        "run_id": args.run_id,
        "timestamp": datetime.now().isoformat(),
        "total_urls": len(all_urls),
        "existing_urls": len(existing_results),
        "urls_to_scrape": len(urls_to_scrape),
        "nodes": len(configs),
        "configs": [{"node_id": c["node_id"], "urls_count": len(c["urls"]), "output_file": c["output_file"]} for c in configs]
    }
    
    summary_file = os.path.join(args.output_folder, "metadata", f"scraping_summary_{args.run_id}.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Coordination complete!")
    print(f"📋 Summary saved to: {summary_file}")
    print(f"🎯 Ready to launch {len(configs)} nodes")
    
    # Print launch commands
    print(f"\n🚀 Launch commands:")
    for config in configs:
        print(f"docker-compose up scraper-{config['node_id']}")

if __name__ == "__main__":
    main()
