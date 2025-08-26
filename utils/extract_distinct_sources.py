#!/usr/bin/env python3
"""
Script to extract distinct data sources from processed_urls.txt
"""

import re
from urllib.parse import urlparse
from collections import Counter

def extract_distinct_sources(file_path):
    """
    Extract distinct data sources from URLs in the file
    """
    sources = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    # Parse the URL
                    parsed_url = urlparse(line)
                    domain = parsed_url.netloc
                    
                    # Remove www. prefix if present
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    
                    sources.append(domain)
                    
                except Exception as e:
                    print(f"Error parsing URL at line {line_num}: {line}")
                    print(f"Error: {e}")
                    continue
    
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []
    
    return sources

def main():
    file_path = "output/joined/processed_urls.txt"
    
    print("Extracting distinct data sources from URLs...")
    print(f"Reading from: {file_path}")
    print("-" * 50)
    
    # Extract all sources
    all_sources = extract_distinct_sources(file_path)
    
    if not all_sources:
        print("No sources found or error occurred.")
        return
    
    # Count occurrences
    source_counts = Counter(all_sources)
    
    # Sort by count (descending)
    sorted_sources = source_counts.most_common()
    
    print(f"Total URLs processed: {len(all_sources)}")
    print(f"Distinct sources found: {len(source_counts)}")
    print("\nDistinct Data Sources (sorted by frequency):")
    print("-" * 50)
    
    for i, (source, count) in enumerate(sorted_sources, 1):
        percentage = (count / len(all_sources)) * 100
        print(f"{i:2d}. {source:<30} | Count: {count:6d} | {percentage:5.1f}%")
    
    # Save to file
    output_file = "distinct_sources.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Distinct Data Sources from processed_urls.txt\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total URLs processed: {len(all_sources)}\n")
        f.write(f"Distinct sources found: {len(source_counts)}\n\n")
        f.write("Sources (sorted by frequency):\n")
        f.write("-" * 30 + "\n")
        
        for i, (source, count) in enumerate(sorted_sources, 1):
            percentage = (count / len(all_sources)) * 100
            f.write(f"{i:2d}. {source:<30} | Count: {count:6d} | {percentage:5.1f}%\n")
    
    print(f"\nResults saved to: {output_file}")
    
    # Also save just the source names (one per line)
    sources_only_file = "distinct_sources_list.txt"
    with open(sources_only_file, 'w', encoding='utf-8') as f:
        for source, _ in sorted_sources:
            f.write(f"{source}\n")
    
    print(f"Source names only saved to: {sources_only_file}")

if __name__ == "__main__":
    main()
