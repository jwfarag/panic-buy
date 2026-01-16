#!/usr/bin/env python3
"""
Fetch news articles using MassiveNewsSource.

Simple script to pull articles from the past N hours for a set of tickers.

Usage:
    python scripts/fetch_massive_news.py

Requires:
    POLYGON_API_KEY environment variable
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestion.news import MassiveNewsSource, NewsArticle


def main():
    # Configuration - same tickers as fetch_test_data.py
    # One per sector from config/tickers.yaml for diversity
    tickers = ["AAPL", "JNJ", "JPM", "PG", "CAT"]
    lookback_hours = 72

    print(f"Fetching news for {tickers} from the past {lookback_hours} hours...\n")

    # Initialize source
    try:
        source = MassiveNewsSource()
    except ValueError as e:
        print(f"Error: {e}")
        print("Set POLYGON_API_KEY environment variable and try again.")
        sys.exit(1)

    # Fetch articles
    articles = source.fetch_for_tickers(tickers, lookback_hours=lookback_hours)

    print(f"Found {len(articles)} articles\n")
    print("=" * 80)

    for i, article in enumerate(articles, 1):
        print(f"\n[{i}] {article.title}")
        print(f"    Source: {article.source}")
        print(f"    Published: {article.published_at}")
        print(f"    Tickers: {', '.join(article.tickers)}")
        print(f"    URL: {article.url}")

        if article.content:
            # Show first 200 chars of content
            preview = article.content[:200].replace("\n", " ")
            print(f"    Content preview: {preview}...")
        else:
            print("    Content: [extraction failed]")

        print("-" * 80)


if __name__ == "__main__":
    main()
