"""
World Bank Indicators API connector.

Handles:
- Cross-country economic indicators
- GDP, population, poverty metrics
- Development indicators

API Notes:
- No authentication required
- Add ?format=json for JSON responses
- Returns array: [metadata, data]
"""
from datetime import datetime
from typing import Any

import requests

from .base import BaseMetricConnector, ConnectorConfig, FetchResult
from ..storage.models import Observation


class WorldBankConnector(BaseMetricConnector):
    """Connector for World Bank Indicators API."""

    SOURCE_NAME = "worldbank"
    BASE_URL = "https://api.worldbank.org/v2"

    def fetch(self, config: ConnectorConfig) -> FetchResult:
        """
        Fetch indicator data from World Bank.

        Args:
            config: Must include indicator and country

        Returns:
            FetchResult with indicator observations
        """
        if not config.indicator:
            return FetchResult(
                success=False,
                data=[],
                error="indicator required for World Bank connector",
                source=self.SOURCE_NAME
            )

        country = config.country or "WLD"  # Default to World aggregate

        url = f"{self.BASE_URL}/country/{country}/indicator/{config.indicator}"
        params = {
            "format": "json",
            "per_page": 100,
            "mrv": 50,  # Most recent values
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # World Bank returns [metadata, data_array]
            if not isinstance(data, list) or len(data) < 2:
                return FetchResult(
                    success=False,
                    data=[],
                    error="Unexpected World Bank response format",
                    source=self.SOURCE_NAME
                )

            return FetchResult(
                success=True,
                data=data[1] or [],  # data[1] can be None
                source=self.SOURCE_NAME
            )

        except requests.RequestException as e:
            return FetchResult(
                success=False,
                data=[],
                error=str(e),
                source=self.SOURCE_NAME
            )

    def normalize(self, config: ConnectorConfig, raw_data: list[Any]) -> list[Observation]:
        """
        Convert World Bank data to observations.

        World Bank format:
        {
            "indicator": {"id": "...", "value": "..."},
            "country": {"id": "...", "value": "..."},
            "date": "2023",
            "value": 123.45
        }
        """
        observations = []

        for item in raw_data:
            if item is None:
                continue

            value = item.get("value")
            if value is None:
                continue

            # World Bank dates are usually just years
            date_str = item.get("date", "")
            if len(date_str) == 4:
                obs_date = f"{date_str}-01-01"
            else:
                obs_date = date_str

            obs = Observation(
                metric_id=config.metric_id,
                obs_date=obs_date,
                value=round(float(value) * config.multiplier, config.decimals),
                unit=config.unit,
                source=self.SOURCE_NAME,
                retrieved_at=datetime.now()
            )
            observations.append(obs)

        # Sort by date descending
        observations.sort(key=lambda x: x.obs_date, reverse=True)
        return observations

    def health_check(self) -> bool:
        """Check World Bank API availability."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/country/WLD/indicator/NY.GDP.MKTP.CD",
                params={"format": "json", "per_page": 1},
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
