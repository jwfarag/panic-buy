#!/usr/bin/env python3
"""
Fetch Test Data
===============
Pulls sample news and market data for testing and prototyping.

Usage:
    python scripts/fetch_test_data.py

Requires:
    - NEWSAPI_AI_KEY environment variable (or .env file)
    - pip install -r requirements.txt
"""

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()


def fetch_news_data(output_dir: Path, tickers: list[str], lookback_hours: int = 168):
    """Fetch news articles for sample tickers."""
    from src.ingestion.news.newsapi_source import NewsAPISource

    print("\n=== Fetching News Data ===")

    api_key = os.environ.get("NEWSAPI_AI_KEY")
    if not api_key:
        print("ERROR: NEWSAPI_AI_KEY not set. Add it to .env or environment.")
        return False

    output_dir.mkdir(parents=True, exist_ok=True)
    source = NewsAPISource(config={"max_items": 5})  # Limit to 5 per ticker

    all_articles = {}
    all_articles_flat = []  # For parquet (flat list)

    for ticker in tickers:
        print(f"  Fetching news for {ticker}...", end=" ")
        try:
            articles = source.fetch_for_ticker(ticker, lookback_hours=lookback_hours)
            all_articles[ticker] = [a.to_dict() for a in articles]
            all_articles_flat.extend([a.to_dict() for a in articles])
            print(f"found {len(articles)} articles")
        except Exception as e:
            print(f"ERROR: {e}")
            all_articles[ticker] = []

    # Save as JSON (human-readable)
    json_file = output_dir / "sample_articles.json"
    with open(json_file, "w") as f:
        json.dump(all_articles, f, indent=2, default=str)
    print(f"  Saved JSON to {json_file}")

    # Save as Parquet (pipeline-ready)
    if all_articles_flat:
        df = pd.DataFrame(all_articles_flat)
        parquet_file = output_dir / "sample_articles.parquet"
        df.to_parquet(parquet_file, index=False)
        print(f"  Saved Parquet to {parquet_file}")

    # Save single article for unit tests
    for ticker, articles in all_articles.items():
        if articles:
            single_file = output_dir / "single_article.json"
            with open(single_file, "w") as f:
                json.dump(articles[0], f, indent=2, default=str)
            print(f"  Saved single article to {single_file}")
            break

    total = sum(len(v) for v in all_articles.values())
    print(f"  Total: {total} articles")
    return True


def fetch_market_data(output_dir: Path, tickers: list[str], days: int = 30):
    """Fetch OHLCV market data for sample tickers."""
    from src.ingestion.market.yahoo_market import YahooMarketData

    print("\n=== Fetching Market Data ===")

    output_dir.mkdir(parents=True, exist_ok=True)
    market = YahooMarketData()

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    all_data = {}
    all_bars_flat = []  # For parquet (flat list with ticker column)

    for ticker in tickers:
        print(f"  Fetching {ticker}...", end=" ")
        try:
            data = market.fetch_ohlcv(ticker, start_date, end_date)
            bars_list = [
                {
                    "timestamp": bar.timestamp.isoformat(),
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                }
                for bar in data.bars
            ]
            all_data[ticker] = {
                "ticker": ticker,
                "bars": bars_list,
                "metadata": data.metadata,
            }
            # Add ticker column for flat parquet
            for bar in bars_list:
                bar["ticker"] = ticker
                all_bars_flat.append(bar)
            print(f"found {len(data.bars)} bars")
        except Exception as e:
            print(f"ERROR: {e}")
            all_data[ticker] = {"ticker": ticker, "bars": [], "metadata": {}}

    # Save as JSON (human-readable)
    json_file = output_dir / "sample_ohlcv.json"
    with open(json_file, "w") as f:
        json.dump(all_data, f, indent=2, default=str)
    print(f"  Saved JSON to {json_file}")

    # Save as Parquet (pipeline-ready)
    if all_bars_flat:
        df = pd.DataFrame(all_bars_flat)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        parquet_file = output_dir / "sample_ohlcv.parquet"
        df.to_parquet(parquet_file, index=False)
        print(f"  Saved Parquet to {parquet_file}")

    return True


def create_readme(fixtures_dir: Path):
    """Create README documenting the fixtures."""
    readme = fixtures_dir / "README.md"
    content = """# Test Fixtures

Sample data for testing and prototyping.

## Regenerating Data

Run the fetch script to pull fresh data:

```bash
python scripts/fetch_test_data.py
```

Requires `NEWSAPI_AI_KEY` in your environment or `.env` file.

## Contents

### News Data (`news/`)
- `sample_articles.json` - News articles grouped by ticker (human-readable)
- `sample_articles.parquet` - Flat article list (pipeline-ready)
- `single_article.json` - Single article for unit tests

### Market Data (`market/`)
- `sample_ohlcv.json` - OHLCV data grouped by ticker (human-readable)
- `sample_ohlcv.parquet` - Flat OHLCV bars with ticker column (pipeline-ready)

## Usage

```python
import pandas as pd

# Read parquet for analysis
articles_df = pd.read_parquet("tests/fixtures/news/sample_articles.parquet")
ohlcv_df = pd.read_parquet("tests/fixtures/market/sample_ohlcv.parquet")
```
"""
    with open(readme, "w") as f:
        f.write(content)
    print(f"\n  Created {readme}")


def main():
    print("Fetch Test Data")
    print("=" * 40)

    fixtures_dir = project_root / "tests" / "fixtures"

    # Sample tickers from universe (one per sector for diversity)
    # See config/tickers.yaml for full universe
    news_tickers = ["AAPL", "JNJ", "JPM", "PG", "CAT"]
    market_tickers = ["AAPL", "JNJ", "JPM", "PG", "CAT", "SPY", "QQQ"]

    # Fetch data
    fetch_news_data(fixtures_dir / "news", news_tickers, lookback_hours=168)
    fetch_market_data(fixtures_dir / "market", market_tickers, days=30)
    create_readme(fixtures_dir)

    print("\n" + "=" * 40)
    print("Done! Test fixtures saved to tests/fixtures/")


if __name__ == "__main__":
    main()
