# Test Fixtures

Sample data for testing and prototyping.

## News Data (`news/`)

- **sample_articles.json** - Sample news articles for AAPL, MSFT, GOOGL (3 articles each)
- **single_article.json** - Single article for unit tests

Articles include realistic headlines, full content, and metadata matching NewsAPI.ai format.

## Market Data (`market/`)

- **sample_ohlcv.json** - 10 days of OHLCV data for AAPL, MSFT, and SPY

### Test Scenarios

The AAPL data contains a **5% price drop** on 2024-01-15:
- Jan 12 close: $188.50
- Jan 15 close: $179.00 (-5.04%)
- High volume: 125M shares (vs ~50M normal)

SPY dropped only ~0.6% on the same day, making this an **idiosyncratic drop** useful for testing the market correlation filter.

MSFT shows steady growth throughout the period for comparison.

## Usage

```python
import json

# Load news fixtures
with open('tests/fixtures/news/sample_articles.json') as f:
    articles = json.load(f)

# Load market fixtures
with open('tests/fixtures/market/sample_ohlcv.json') as f:
    market_data = json.load(f)
```
