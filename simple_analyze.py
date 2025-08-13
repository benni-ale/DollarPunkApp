#!/usr/bin/env python3
"""
Simple DollarPunk Data Analyzer
Just run: python simple_analyze.py
"""

import json
import glob
from collections import Counter, defaultdict
from datetime import datetime

def simple_analyze():
    print("🔍 DollarPunk Simple Analysis")
    print("=" * 50)
    
    # Find all JSON files
    files = glob.glob("output/news_data_*.json")
    if not files:
        print("❌ No data files found in output/")
        return
    
    print(f"📁 Found {len(files)} files")
    
    # Collect all data
    all_articles = []
    all_urls = set()
    
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                articles = json.load(f)
                all_articles.extend(articles)
                all_urls.update(article.get('url', '') for article in articles)
        except Exception as e:
            print(f"⚠️  Error reading {file}: {e}")
    
    # Basic stats
    total_articles = len(all_articles)
    unique_urls = len([url for url in all_urls if url])
    duplicate_rate = ((total_articles - unique_urls) / total_articles * 100) if total_articles > 0 else 0
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total articles: {total_articles}")
    print(f"   Unique URLs: {unique_urls}")
    print(f"   Duplicate rate: {duplicate_rate:.1f}%")
    
    # By source ticker
    source_ticker_counts = Counter(article.get('source_ticker', 'Unknown') for article in all_articles)
    print(f"\n📈 BY SOURCE TICKER:")
    for ticker, count in source_ticker_counts.most_common():
        print(f"   {ticker}: {count}")
    

    
    # Date ranges by source ticker
    source_ticker_dates = defaultdict(list)
    for article in all_articles:
        ticker = article.get('source_ticker', 'Unknown')
        date_str = article.get('time_published', '')
        if date_str:
            try:
                # Parse the time_published format: YYYYMMDDTHHMMSS
                date_obj = datetime.strptime(date_str, '%Y%m%dT%H%M%S')
                source_ticker_dates[ticker].append(date_obj)
            except Exception:
                continue
    
    print(f"\n📅 DATE RANGES BY SOURCE TICKER:")
    for ticker in sorted(source_ticker_counts.keys()):
        dates = source_ticker_dates[ticker]
        if dates:
            min_date = min(dates)
            max_date = max(dates)
            print(f"   {ticker}: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')} ({len(dates)} articles)")
        else:
            print(f"   {ticker}: No valid dates found")
    

    
    # Overall sentiment
    sentiment_counts = Counter(article.get('overall_sentiment_label', 'Unknown') for article in all_articles)
    print(f"\n😊 OVERALL SENTIMENT (by article):")
    for sentiment, count in sentiment_counts.most_common():
        print(f"   {sentiment}: {count}")
    
    # By source
    source_counts = Counter(article.get('source', 'Unknown') for article in all_articles)
    print(f"\n📰 TOP SOURCES:")
    for source, count in source_counts.most_common(5):
        print(f"   {source}: {count}")
    
    # Sample articles
    print(f"\n📰 SAMPLE ARTICLES:")
    for i, article in enumerate(all_articles[:3]):
        print(f"   {i+1}. {article.get('title', 'No title')[:60]}...")
        print(f"      Source Ticker: {article.get('source_ticker')} | Sentiment: {article.get('overall_sentiment_label')}")
        print()

if __name__ == "__main__":
    simple_analyze() 