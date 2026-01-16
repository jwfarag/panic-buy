#!/usr/bin/env python3
"""
Fetch Test Data
===============
Pulls sample market data for testing and prototyping.

Usage:
    python scripts/fetch_test_data.py

Requires:
    pip install -r requirements.txt
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Output directory
OUTPUT_DIR = project_root / "data" / "raw" / "market"


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


def main():
    print("Fetch Test Data")
    print("=" * 40)

    # Sample tickers from universe (one per sector for diversity)
    # See config/tickers.yaml for full universe
    tickers = ["AAPL", "JNJ", "JPM", "PG", "CAT", "SPY", "QQQ"]

    # Fetch data
    fetch_market_data(OUTPUT_DIR, tickers, days=30)

    print("\n" + "=" * 40)
    print(f"Done! Market data saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
