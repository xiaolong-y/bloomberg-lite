"""
OECD SDMX API connector for economic indicators.

Handles:
- GDP growth rates
- Inflation (CPI)
- Unemployment rates
- Interest rates
- For US, EU, Japan, and other OECD countries

API Notes:
- No authentication required
- SDMX-JSON format
- Base URL: https://sdmx.oecd.org/public/rest
- Rate limit: Reasonable use expected
"""
from datetime import datetime
from typing import Any, Optional

import requests

from .base import BaseMetricConnector, ConnectorConfig, FetchResult
from ..storage.models import Observation


class OECDConnector(BaseMetricConnector):
    """Connector for OECD SDMX API."""

    SOURCE_NAME = "oecd"
    BASE_URL = "https://sdmx.oecd.org/public/rest/data"

    # OECD dataflow and key mappings
    # Format: metric_id -> (dataflow, key_parts)
    METRIC_MAP = {
        # US Economy
        "us.cpi_yoy": ("PRICES_CPI", "USA.CPALTT01.GY.M"),
        "us.core_cpi_yoy": ("PRICES_CPI", "USA.CPGRLE01.GY.M"),
        "us.unemployment": ("MEI", "USA.LRHUTTTT.STSA.M"),
        "us.gdp_qoq": ("QNA", "USA.B1_GE.GYSA.Q"),

        # Eurozone
        "eu.unemployment": ("MEI", "EA20.LRHUTTTT.STSA.M"),
        "eu.deposit_rate": ("MEI_FIN", "EA20.IR3TIB.ST.M"),

        # Japan
        "japan.policy_rate": ("MEI_FIN", "JPN.IR3TIB.ST.M"),
        "japan.cpi_yoy": ("PRICES_CPI", "JPN.CPALTT01.GY.M"),

        # Global
        "global.dxy": None,  # Not available from OECD
        "global.brent": ("MEI", "OECD.OILBRNT.STSA.M"),
    }

    def fetch(self, config: ConnectorConfig) -> FetchResult:
        """
        Fetch economic data from OECD SDMX API.

        Args:
            config: Metric configuration with OECD dataflow info

        Returns:
            FetchResult with SDMX data
        """
        mapping = self.METRIC_MAP.get(config.metric_id)

        # Use config overrides if provided
        dataflow = config.dataflow or (mapping[0] if mapping else None)
        series_key = config.series_key or (mapping[1] if mapping else None)

        if not dataflow or not series_key:
            return FetchResult(
                success=False,
                data=[],
                error=f"No OECD mapping for {config.metric_id}",
                source=self.SOURCE_NAME
            )

        url = f"{self.BASE_URL}/OECD.SDD.STES,DSD_{dataflow}@DF_{dataflow}/{series_key}"

        params = {
            "startPeriod": "2020-01",
            "dimensionAtObservation": "AllDimensions"
        }

        headers = {
            "Accept": "application/vnd.sdmx.data+json;charset=utf-8;version=1.0"
        }

        try:
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
        Convert OECD SDMX-JSON data to observations.
        """
        observations = []

        try:
            datasets = raw_data.get("data", {}).get("dataSets", [])
            if not datasets:
                return []

            # Get time periods from structure
            structure = raw_data.get("data", {}).get("structure", {})
            dimensions = structure.get("dimensions", {}).get("observation", [])

            time_dim = None
            for dim in dimensions:
                if dim.get("id") == "TIME_PERIOD":
                    time_dim = dim
                    break

            if not time_dim:
                return []

            time_values = {str(i): v["id"] for i, v in enumerate(time_dim.get("values", []))}

            # Parse observations
            series = datasets[0].get("series", {})
            for series_key, series_data in series.items():
                obs_data = series_data.get("observations", {})
                for time_idx, values in obs_data.items():
                    if not values:
                        continue

                    value = values[0]
                    if value is None:
                        continue

                    time_period = time_values.get(time_idx, "")
                    obs_date = self._parse_time_period(time_period)

                    if not obs_date:
                        continue

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
            print(f"OECD parse warning: {e}")

        # Sort by date descending
        observations.sort(key=lambda x: x.obs_date, reverse=True)
        return observations

    def _parse_time_period(self, period: str) -> str:
        """Convert OECD time period to YYYY-MM-DD format."""
        if not period:
            return ""

        try:
            # Monthly: 2024-01 -> 2024-01-01
            if len(period) == 7 and "-" in period:
                return f"{period}-01"

            # Quarterly: 2024-Q1 -> 2024-01-01
            if "Q" in period:
                year = period[:4]
                quarter = period[-1]
                month_map = {"1": "01", "2": "04", "3": "07", "4": "10"}
                month = month_map.get(quarter, "01")
                return f"{year}-{month}-01"

            # Annual: 2024 -> 2024-01-01
            if len(period) == 4 and period.isdigit():
                return f"{period}-01-01"

            return ""
        except Exception:
            return ""

    def health_check(self) -> bool:
        """Check OECD API availability."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/OECD.SDD.STES,DSD_PRICES_CPI@DF_PRICES_CPI/USA.CPALTT01.GY.M",
                params={"startPeriod": "2024-01"},
                headers={"Accept": "application/vnd.sdmx.data+json"},
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
