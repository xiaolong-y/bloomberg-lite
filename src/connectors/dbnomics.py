"""
DBnomics API connector.

Handles:
- ISM PMI data (US manufacturing)
- Other economic series available on DBnomics

API Notes:
- No authentication required
- Base URL: https://api.db.nomics.world/v22/
- Returns series data with period and value arrays
"""
from datetime import datetime
from typing import Any

import requests

from .base import BaseMetricConnector, ConnectorConfig, FetchResult
from ..storage.models import Observation


class DBnomicsConnector(BaseMetricConnector):
    """Connector for DBnomics API."""

    SOURCE_NAME = "dbnomics"
    BASE_URL = "https://api.db.nomics.world/v22"

    def fetch(self, config: ConnectorConfig) -> FetchResult:
        """
        Fetch series data from DBnomics.

        Args:
            config: Must include provider, dataset, and series fields
                   (stored in series_id as "provider/dataset/series")

        Returns:
            FetchResult with observation data
        """
        # Parse series_id format: "provider/dataset/series" or use separate fields
        series_path = config.series_id
        if not series_path:
            # Try to construct from individual fields if available
            provider = getattr(config, 'provider', None)
            dataset = getattr(config, 'dataset', None)
            series = getattr(config, 'series', None)
            if provider and dataset and series:
                series_path = f"{provider}/{dataset}/{series}"

        if not series_path:
            return FetchResult(
                success=False,
                data=[],
                error="series_id (format: provider/dataset/series) required for DBnomics connector",
                source=self.SOURCE_NAME
            )

        url = f"{self.BASE_URL}/series/{series_path}"
        params = {
            "observations": 1,  # Include observation data
            "format": "json",
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # DBnomics returns series info with observations
            if "series" not in data or not data["series"].get("docs"):
                return FetchResult(
                    success=False,
                    data=[],
                    error="No series data in response",
                    source=self.SOURCE_NAME
                )

            # Get the first (and usually only) series document
            series_doc = data["series"]["docs"][0]

            return FetchResult(
                success=True,
                data=series_doc,
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
        self, config: ConnectorConfig, raw_data: Any
    ) -> list[Observation]:
        """
        Convert DBnomics series data to standard format.

        DBnomics format:
        {
            "period": ["2024-01", "2024-02", ...],
            "value": [50.3, 49.1, ...],
            ...
        }
        """
        observations = []

        periods = raw_data.get("period", [])
        values = raw_data.get("value", [])

        if len(periods) != len(values):
            return []

        for period, value in zip(periods, values):
            # Skip null/missing values
            if value is None:
                continue

            try:
                val = float(value) * config.multiplier
            except (ValueError, TypeError):
                continue

            # Convert period to YYYY-MM-DD format
            obs_date = self._parse_period(period)

            obs = Observation(
                metric_id=config.metric_id,
                obs_date=obs_date,
                value=round(val, config.decimals),
                unit=config.unit,
                source=self.SOURCE_NAME,
                retrieved_at=datetime.now()
            )
            observations.append(obs)

        # Sort by date descending (most recent first)
        observations.sort(key=lambda x: x.obs_date, reverse=True)
        return observations

    def _parse_period(self, period: str) -> str:
        """
        Convert DBnomics period format to YYYY-MM-DD.

        Formats:
        - 2024-01 → 2024-01-01 (monthly)
        - 2024-Q1 → 2024-01-01 (quarterly)
        - 2024 → 2024-01-01 (annual)
        """
        if "-Q" in period:
            # Quarterly: 2024-Q1 → 2024-01-01
            year, quarter = period.split("-Q")
            month = {"1": "01", "2": "04", "3": "07", "4": "10"}[quarter]
            return f"{year}-{month}-01"
        elif len(period) == 7:
            # Monthly: 2024-01 → 2024-01-01
            return f"{period}-01"
        elif len(period) == 4:
            # Annual: 2024 → 2024-01-01
            return f"{period}-01-01"
        else:
            # Already full date or unknown format
            return period

    def health_check(self) -> bool:
        """Check DBnomics API availability."""
        try:
            # Check API status endpoint
            response = requests.get(
                f"{self.BASE_URL}/providers",
                params={"limit": 1},
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
