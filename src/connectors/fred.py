"""
FRED (Federal Reserve Economic Data) API connector.

Handles:
- US economic indicators (GDP, CPI, unemployment, etc.)
- Interest rates and yields
- Some international data mirrored by FRED

API Notes:
- Requires free API key from https://fred.stlouisfed.org/docs/api/api_key.html
- Returns observations in ascending date order by default
- Dates in YYYY-MM-DD format
"""
import os
from datetime import datetime
from typing import Any, Optional

import requests

from .base import BaseMetricConnector, ConnectorConfig, FetchResult
from ..storage.models import Observation


class FREDConnector(BaseMetricConnector):
    """Connector for FRED API."""

    SOURCE_NAME = "fred"
    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("FRED_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FRED_API_KEY required. Get one at "
                "https://fred.stlouisfed.org/docs/api/api_key.html"
            )

    def fetch(self, config: ConnectorConfig) -> FetchResult:
        """
        Fetch series observations from FRED.

        Args:
            config: Must include series_id

        Returns:
            FetchResult with observation data
        """
        if not config.series_id:
            return FetchResult(
                success=False,
                data=[],
                error="series_id required for FRED connector",
                source=self.SOURCE_NAME
            )

        url = f"{self.BASE_URL}/series/observations"
        params = {
            "series_id": config.series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 500,  # Get plenty of history
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "observations" not in data:
                return FetchResult(
                    success=False,
                    data=[],
                    error=f"Unexpected response format: {list(data.keys())}",
                    source=self.SOURCE_NAME
                )

            return FetchResult(
                success=True,
                data=data["observations"],
                source=self.SOURCE_NAME
            )

        except requests.RequestException as e:
            return FetchResult(
                success=False,
                data=[],
                error=str(e),
                source=self.SOURCE_NAME
            )

    def normalize(
        self, config: ConnectorConfig, raw_data: list[Any]
    ) -> list[Observation]:
        """
        Convert FRED observations to standard format.

        Handles:
        - Missing values (FRED uses "." for missing)
        - Unit multiplier application
        - Date parsing
        """
        observations = []

        for item in raw_data:
            # Skip missing values
            value_str = item.get("value", ".")
            if value_str == "." or not value_str:
                continue

            try:
                value = float(value_str) * config.multiplier
            except ValueError:
                continue

            obs = Observation(
                metric_id=config.metric_id,
                obs_date=item["date"],  # Already YYYY-MM-DD
                value=round(value, config.decimals),
                unit=config.unit,
                source=self.SOURCE_NAME,
                retrieved_at=datetime.now()
            )
            observations.append(obs)

        return observations

    def health_check(self) -> bool:
        """Check FRED API availability."""
        try:
            # Fetch a known stable series
            response = requests.get(
                f"{self.BASE_URL}/series",
                params={
                    "series_id": "GNPCA",  # Real GNP, very stable
                    "api_key": self.api_key,
                    "file_type": "json"
                },
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
