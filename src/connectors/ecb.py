"""
ECB (European Central Bank) SDMX API connector.

Handles:
- Eurozone monetary policy rates
- HICP inflation data
- Exchange rates
- Banking statistics

API Notes:
- No authentication required
- Uses SDMX-JSON format
- Dataflow format: DATABASE/SERIES_KEY (e.g., FM/M.U2.EUR.4F.KR.DFR.LEV)
"""
from datetime import datetime
from typing import Any

import requests

from .base import BaseMetricConnector, ConnectorConfig, FetchResult
from ..storage.models import Observation


class ECBConnector(BaseMetricConnector):
    """Connector for ECB SDMX API."""

    SOURCE_NAME = "ecb"
    BASE_URL = "https://data-api.ecb.europa.eu/service/data"

    def fetch(self, config: ConnectorConfig) -> FetchResult:
        """
        Fetch data from ECB SDMX API.

        Args:
            config: Must include dataflow and series_key

        Returns:
            FetchResult with SDMX-JSON data
        """
        if not config.dataflow or not config.series_key:
            return FetchResult(
                success=False,
                data=[],
                error="dataflow and series_key required for ECB connector",
                source=self.SOURCE_NAME
            )

        # ECB URL format: /data/{dataflow}/{series_key}
        url = f"{self.BASE_URL}/{config.dataflow}/{config.series_key}"
        params = {
            "format": "jsondata",
            "lastNObservations": 500,
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return FetchResult(
                success=True,
                data=response.json(),
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
        Parse SDMX-JSON structure into observations.

        SDMX-JSON structure:
        {
            "dataSets": [{
                "series": {
                    "0:0:0:...": {
                        "observations": {
                            "0": [value],
                            "1": [value],
                            ...
                        }
                    }
                }
            }],
            "structure": {
                "dimensions": {
                    "observation": [{
                        "values": [{"id": "2024-01"}, ...]
                    }]
                }
            }
        }
        """
        observations = []

        try:
            # Extract time dimension values
            structure = raw_data.get("structure", {})
            obs_dims = structure.get("dimensions", {}).get("observation", [])

            # Find the TIME_PERIOD dimension
            time_values = []
            for dim in obs_dims:
                if dim.get("id") == "TIME_PERIOD":
                    time_values = [v.get("id") for v in dim.get("values", [])]
                    break

            if not time_values:
                return []

            # Extract observations from first dataset, first series
            datasets = raw_data.get("dataSets", [])
            if not datasets:
                return []

            series = datasets[0].get("series", {})
            if not series:
                return []

            # Get first series (usually only one for specific series_key)
            first_series = list(series.values())[0]
            obs_data = first_series.get("observations", {})

            for idx_str, values in obs_data.items():
                idx = int(idx_str)
                if idx >= len(time_values):
                    continue

                time_period = time_values[idx]
                value = values[0] if values else None

                if value is None:
                    continue

                # Convert time period to date (handle YYYY-MM, YYYY-QN, YYYY)
                obs_date = self._parse_time_period(time_period)

                obs = Observation(
                    metric_id=config.metric_id,
                    obs_date=obs_date,
                    value=round(float(value) * config.multiplier, config.decimals),
                    unit=config.unit,
                    source=self.SOURCE_NAME,
                    retrieved_at=datetime.now()
                )
                observations.append(obs)

        except (KeyError, IndexError, TypeError) as e:
            # Log error but return what we have
            print(f"ECB parse warning: {e}")

        # Sort by date descending
        observations.sort(key=lambda x: x.obs_date, reverse=True)
        return observations

    def _parse_time_period(self, period: str) -> str:
        """
        Convert ECB time period formats to YYYY-MM-DD.

        Formats:
        - 2024-01 -> 2024-01-01
        - 2024-Q1 -> 2024-01-01
        - 2024 -> 2024-01-01
        """
        if "-Q" in period:
            # Quarterly: 2024-Q1 -> 2024-01-01
            year, quarter = period.split("-Q")
            month = {"1": "01", "2": "04", "3": "07", "4": "10"}[quarter]
            return f"{year}-{month}-01"
        elif len(period) == 7:
            # Monthly: 2024-01 -> 2024-01-01
            return f"{period}-01"
        elif len(period) == 4:
            # Annual: 2024 -> 2024-01-01
            return f"{period}-01-01"
        else:
            # Already full date or unknown format
            return period

    def health_check(self) -> bool:
        """Check ECB API availability."""
        try:
            # Fetch a known stable series (ECB main refinancing rate)
            response = requests.get(
                f"{self.BASE_URL}/FM/M.U2.EUR.4F.KR.MRR_FR.LEV",
                params={"format": "jsondata", "lastNObservations": 1},
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
