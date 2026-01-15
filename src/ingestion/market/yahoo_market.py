# Yahoo Finance Market Data
# =========================
# Fetches market data from Yahoo Finance using yfinance library.

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional

import yfinance as yf
import pandas as pd

from .base import MarketDataSource, OHLCV, TickerData

logger = logging.getLogger(__name__)


class YahooMarketData(MarketDataSource):
    """Yahoo Finance market data provider."""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize Yahoo Finance data provider.

        Args:
            config: Optional configuration dict with:
                - rate_limit_delay: Delay between requests in seconds
        """
        self.config = config or {}
        self._rate_limit_delay = self.config.get('rate_limit_delay', 0.1)

    def fetch_ohlcv(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> TickerData:
        """
        Fetch OHLCV data from Yahoo Finance.

        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            start_date: Start of date range
            end_date: End of date range
            interval: Bar interval ('1d', '1h', '5m', etc.)

        Returns:
            TickerData with OHLCV bars
        """
        logger.debug(f"Fetching {ticker} from {start_date} to {end_date}")

        try:
            yf_ticker = yf.Ticker(ticker)
            df = yf_ticker.history(
                start=start_date,
                end=end_date + timedelta(days=1),  # yfinance end is exclusive
                interval=interval,
                auto_adjust=False  # Keep raw OHLC + separate adj close
            )

            if df.empty:
                logger.warning(f"No data returned for {ticker}")
                return TickerData(ticker=ticker, bars=[], metadata={})

            bars = self._dataframe_to_bars(df)

            # Get metadata
            metadata = self._get_ticker_metadata(yf_ticker)

            return TickerData(ticker=ticker, bars=bars, metadata=metadata)

        except Exception as e:
            logger.error(f"Error fetching {ticker}: {e}")
            raise

    def fetch_batch(
        self,
        tickers: List[str],
        start_date: date,
        end_date: date,
        interval: str = "1d"
    ) -> Dict[str, TickerData]:
        """
        Fetch data for multiple tickers efficiently using yfinance batch download.

        Args:
            tickers: List of stock symbols
            start_date: Start of date range
            end_date: End of date range
            interval: Bar interval

        Returns:
            Dict mapping ticker to TickerData
        """
        logger.info(f"Batch fetching {len(tickers)} tickers")

        try:
            # yfinance batch download
            df = yf.download(
                tickers,
                start=start_date,
                end=end_date + timedelta(days=1),
                interval=interval,
                auto_adjust=False,
                group_by='ticker',
                progress=False
            )

            results = {}

            if len(tickers) == 1:
                # Single ticker returns flat DataFrame
                ticker = tickers[0]
                bars = self._dataframe_to_bars(df)
                results[ticker] = TickerData(ticker=ticker, bars=bars, metadata={})
            else:
                # Multiple tickers returns MultiIndex columns
                for ticker in tickers:
                    try:
                        ticker_df = df[ticker].dropna(how='all')
                        if ticker_df.empty:
                            logger.warning(f"No data for {ticker} in batch")
                            results[ticker] = TickerData(ticker=ticker, bars=[], metadata={})
                        else:
                            bars = self._dataframe_to_bars(ticker_df)
                            results[ticker] = TickerData(ticker=ticker, bars=bars, metadata={})
                    except KeyError:
                        logger.warning(f"Ticker {ticker} not found in batch results")
                        results[ticker] = TickerData(ticker=ticker, bars=[], metadata={})

            return results

        except Exception as e:
            logger.error(f"Error in batch fetch: {e}")
            raise

    def get_latest_price(self, ticker: str) -> float:
        """
        Get most recent price for a ticker.

        Args:
            ticker: Stock symbol

        Returns:
            Latest price
        """
        try:
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info
            return info.get('regularMarketPrice') or info.get('currentPrice', 0.0)
        except Exception as e:
            logger.error(f"Error getting latest price for {ticker}: {e}")
            raise

    def get_ticker_info(self, ticker: str) -> dict:
        """
        Get company metadata (sector, market cap, beta, etc.).

        Args:
            ticker: Stock symbol

        Returns:
            Dict with company info
        """
        try:
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info

            return {
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap'),
                'beta': info.get('beta'),
                'trailing_pe': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'dividend_yield': info.get('dividendYield'),
                'short_name': info.get('shortName'),
                'long_name': info.get('longName'),
            }
        except Exception as e:
            logger.error(f"Error getting info for {ticker}: {e}")
            raise

    @property
    def source_name(self) -> str:
        return "yahoo"

    def _dataframe_to_bars(self, df: pd.DataFrame) -> List[OHLCV]:
        """Convert yfinance DataFrame to list of OHLCV bars."""
        bars = []

        for idx, row in df.iterrows():
            # Handle timezone-aware timestamps
            if isinstance(idx, pd.Timestamp):
                timestamp = idx.to_pydatetime()
                if timestamp.tzinfo is not None:
                    timestamp = timestamp.replace(tzinfo=None)
            else:
                timestamp = idx

            bar = OHLCV(
                timestamp=timestamp,
                open=float(row['Open']) if pd.notna(row['Open']) else 0.0,
                high=float(row['High']) if pd.notna(row['High']) else 0.0,
                low=float(row['Low']) if pd.notna(row['Low']) else 0.0,
                close=float(row['Close']) if pd.notna(row['Close']) else 0.0,
                volume=int(row['Volume']) if pd.notna(row['Volume']) else 0,
                adjusted_close=float(row['Adj Close']) if 'Adj Close' in row and pd.notna(row['Adj Close']) else None,
            )
            bars.append(bar)

        return bars

    def _get_ticker_metadata(self, yf_ticker) -> dict:
        """Extract metadata from yfinance ticker object."""
        try:
            info = yf_ticker.info
            return {
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'short_name': info.get('shortName'),
            }
        except Exception:
            return {}
