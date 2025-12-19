"""
Yahoo Finance API connector for market data.

Handles:
- Commodities (Brent Crude, Gold, etc.)
- Currency indices (DXY, etc.)
- Stock indices

API Notes:
- No authentication required
- Uses unofficial Yahoo Finance API endpoints
- Returns real-time and historical data
"""
from datetime import datetime
from typing import Any, Optional

import requests

from .base import BaseMetricConnector, ConnectorConfig, FetchResult
from ..storage.models import Observation


class YahooFinanceConnector(BaseMetricConnector):
    """Connector for Yahoo Finance market data."""

    SOURCE_NAME = "yahoo"
    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"

    # Map our metric IDs to Yahoo Finance symbols
    SYMBOL_MAP = {
        "global.brent": "BZ=F",      # Brent Crude Futures
        "global.dxy": "DX-Y.NYB",    # US Dollar Index
        "global.gold": "GC=F",       # Gold Futures
        "global.wti": "CL=F",        # WTI Crude Oil Futures
    }

    def fetch(self, config: ConnectorConfig) -> FetchResult:
        """
        Fetch market data from Yahoo Finance.

        Args:
            config: Must include metric_id that maps to a Yahoo symbol

        Returns:
            FetchResult with price data
        """
        symbol = self.SYMBOL_MAP.get(config.metric_id)
        if not symbol:
            symbol = config.series_id or config.metric_id

        url = f"{self.BASE_URL}/{symbol}"
        params = {
            "interval": "1d",
            "range": "1mo"  # Get 1 month of data for sparklines
        }

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            return FetchResult(
                success=True,
                data=data,
                source=self.SOURCE_NAME
            )

        except requests.RequestException as e:
            return FetchResult(
                success=False,
                data=[],
                error=str(e),
                source=self.SOURCE_NAME
            )

    def normalize(self, config: ConnectorConfig, raw_data: Any) -> list[Observation]:
        """
        Convert Yahoo Finance data to observations.

        Yahoo format:
        {
            "chart": {
                "result": [{
                    "timestamp": [1234567890, ...],
                    "indicators": {
                        "quote": [{
                            "close": [100.0, 101.0, ...]
                        }]
                    }
                }]
            }
        }
        """
        observations = []

        try:
            result = raw_data.get("chart", {}).get("result", [])
            if not result:
                return []

            result = result[0]
            timestamps = result.get("timestamp", [])
            quotes = result.get("indicators", {}).get("quote", [{}])[0]
            closes = quotes.get("close", [])

            for i, (ts, close) in enumerate(zip(timestamps, closes)):
                if close is None:
                    continue

                obs_date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

                obs = Observation(
                    metric_id=config.metric_id,
                    obs_date=obs_date,
                    value=round(float(close) * config.multiplier, config.decimals),
                    unit=config.unit,
                    source=self.SOURCE_NAME,
                    retrieved_at=datetime.now()
                )
                observations.append(obs)

        except (KeyError, ValueError, TypeError) as e:
            print(f"Yahoo Finance parse warning: {e}")

        # Sort by date descending
        observations.sort(key=lambda x: x.obs_date, reverse=True)
        return observations

    def health_check(self) -> bool:
        """Check Yahoo Finance API availability."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(
                f"{self.BASE_URL}/BZ=F",
                params={"interval": "1d", "range": "1d"},
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
