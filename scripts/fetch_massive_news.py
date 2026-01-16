#!/usr/bin/env python3
"""
Fetch news articles using MassiveNewsSource.

Simple script to pull articles from the past N hours for a set of tickers.
Outputs both JSON (human-readable) and Parquet (pipeline-ready) formats.

Usage:
    python scripts/fetch_massive_news.py

Requires:
    POLYGON_API_KEY environment variable
"""

import json
import sys
from pathlib import Path

import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ingestion.news import MassiveNewsSource, NewsArticle

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw" / "news"


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

    # Display articles
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

    # Save outputs
    if articles:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Convert to list of dicts
        articles_data = [a.to_dict() for a in articles]

        # Save as JSON (human-readable)
        json_file = OUTPUT_DIR / "massive_articles.json"
        with open(json_file, "w") as f:
            json.dump(articles_data, f, indent=2, default=str)
        print(f"\nSaved JSON to {json_file}")

        # Save as Parquet (pipeline-ready)
        df = pd.DataFrame(articles_data)
        parquet_file = OUTPUT_DIR / "massive_articles.parquet"
        df.to_parquet(parquet_file, index=False)
        print(f"Saved Parquet to {parquet_file}")


if __name__ == "__main__":
    main()
