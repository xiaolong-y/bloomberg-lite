"""
IMF DataMapper API connector.

Handles:
- Cross-country macroeconomic indicators
- GDP growth, inflation, unemployment
- Fiscal and monetary indicators

API Notes:
- No authentication required
- Simple JSON API format
- URL: https://www.imf.org/external/datamapper/api/v1/{INDICATOR}/{COUNTRY}
- Returns annual data
- Includes historical data and forecasts
"""
from datetime import datetime
from typing import Any

import requests

from .base import BaseMetricConnector, ConnectorConfig, FetchResult
from ..storage.models import Observation


class IMFConnector(BaseMetricConnector):
    """Connector for IMF DataMapper API."""

    SOURCE_NAME = "imf"
    BASE_URL = "https://www.imf.org/external/datamapper/api/v1"

    def fetch(self, config: ConnectorConfig) -> FetchResult:
        """
        Fetch indicator data from IMF DataMapper.

        Args:
            config: Must include indicator (IMF indicator code) and country (ISO 3-letter code)

        Returns:
            FetchResult with indicator data
        """
        if not config.indicator:
            return FetchResult(
                success=False,
                data=[],
                error="indicator required for IMF connector",
                source=self.SOURCE_NAME
            )

        country = config.country or "CHN"  # Default to China

        url = f"{self.BASE_URL}/{config.indicator}/{country}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "values" not in data:
                return FetchResult(
                    success=False,
                    data=[],
                    error=f"Unexpected response format: {list(data.keys())}",
                    source=self.SOURCE_NAME
                )

            return FetchResult(
                success=True,
                data=data["values"],
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
        Convert IMF DataMapper data to observations.

        IMF format:
        {
            "INDICATOR_CODE": {
                "COUNTRY_CODE": {
                    "2020": 5.4,
                    "2021": 6.1,
                    ...
                }
            }
        }
        """
        observations = []

        try:
            # Get the indicator data
            indicator_code = config.indicator
            country_code = config.country or "CHN"

            if indicator_code not in raw_data:
                return []

            country_data = raw_data[indicator_code].get(country_code, {})

            for year, value in country_data.items():
                if value is None:
                    continue

                # Convert year to date (use January 1st)
                obs_date = f"{year}-01-01"

                obs = Observation(
                    metric_id=config.metric_id,
                    obs_date=obs_date,
                    value=round(float(value) * config.multiplier, config.decimals),
                    unit=config.unit,
                    source=self.SOURCE_NAME,
                    retrieved_at=datetime.now()
                )
                observations.append(obs)

        except (KeyError, ValueError, TypeError) as e:
            print(f"IMF parse warning: {e}")

        # Sort by date descending
        observations.sort(key=lambda x: x.obs_date, reverse=True)
        return observations

    def health_check(self) -> bool:
        """Check IMF DataMapper API availability."""
        try:
            # Fetch a known stable indicator (World GDP growth)
            response = requests.get(
                f"{self.BASE_URL}/NGDP_RPCH/WLD",
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
