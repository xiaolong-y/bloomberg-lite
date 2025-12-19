"""
CoinGecko API connector for cryptocurrency data.

Handles:
- Bitcoin (BTC) price and market data
- Ethereum (ETH) price and market data
- Other major cryptocurrencies

API Notes:
- No authentication required (free tier)
- Rate limit: 10-30 calls/minute
- Returns USD prices by default
- Includes 24h change data
"""
from datetime import datetime
from typing import Any, Optional

import requests

from .base import BaseMetricConnector, ConnectorConfig, FetchResult
from ..storage.models import Observation


class CoinGeckoConnector(BaseMetricConnector):
    """Connector for CoinGecko cryptocurrency API."""

    SOURCE_NAME = "coingecko"
    BASE_URL = "https://api.coingecko.com/api/v3"

    # Map our metric IDs to CoinGecko IDs
    COIN_MAP = {
        "crypto.bitcoin": "bitcoin",
        "crypto.ethereum": "ethereum",
    }

    def fetch(self, config: ConnectorConfig) -> FetchResult:
        """
        Fetch cryptocurrency price data from CoinGecko.

        Args:
            config: Must include metric_id that maps to a CoinGecko coin ID

        Returns:
            FetchResult with price and market data
        """
        coin_id = self.COIN_MAP.get(config.metric_id)
        if not coin_id:
            # Try using series_id as coin_id
            coin_id = config.series_id or config.metric_id.split(".")[-1]

        url = f"{self.BASE_URL}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false"
        }

        try:
            response = requests.get(url, params=params, timeout=30)
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
        Convert CoinGecko data to observations.

        CoinGecko format:
        {
            "market_data": {
                "current_price": {"usd": 42000},
                "price_change_percentage_24h": -2.5,
                ...
            }
        }
        """
        observations = []

        try:
            market_data = raw_data.get("market_data", {})
            current_price = market_data.get("current_price", {}).get("usd")

            if current_price is None:
                return []

            obs = Observation(
                metric_id=config.metric_id,
                obs_date=datetime.now().strftime("%Y-%m-%d"),
                value=round(float(current_price) * config.multiplier, config.decimals),
                unit=config.unit or "$",
                source=self.SOURCE_NAME,
                retrieved_at=datetime.now()
            )
            observations.append(obs)

        except (KeyError, ValueError, TypeError) as e:
            print(f"CoinGecko parse warning: {e}")

        return observations

    def health_check(self) -> bool:
        """Check CoinGecko API availability."""
        try:
            response = requests.get(f"{self.BASE_URL}/ping", timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False
