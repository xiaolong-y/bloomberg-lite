"""
e-Stat Statistics Dashboard API connector.

Handles:
- Japanese economic indicators (GDP, unemployment, inflation, etc.)
- Industrial production indices
- Trade and price indices
- No authentication required

API Notes:
- Open API with ~6000 indicators
- No registration or API key needed
- Uses indicator codes (19-digit base + cycle/region/seasonal modifiers)
- Time periods in format: YYYYMM00 (monthly), YYYYNQ00 (quarterly), YYYYCY00 (annual)
- Official source: https://dashboard.e-stat.go.jp/en/static/api
"""
from datetime import datetime
from typing import Any

import requests

from .base import BaseMetricConnector, ConnectorConfig, FetchResult
from ..storage.models import Observation


class EStatDashboardConnector(BaseMetricConnector):
    """Connector for Japan e-Stat Statistics Dashboard API."""

    SOURCE_NAME = "estat_dashboard"
    BASE_URL = "https://dashboard.e-stat.go.jp/api/1.0"

    def __init__(self):
        """Initialize e-Stat connector (no API key required)."""
        pass

    def fetch(self, config: ConnectorConfig) -> FetchResult:
        """
        Fetch data from e-Stat Dashboard API.

        Args:
            config: Must include indicator_code (e-Stat specific field)

        Returns:
            FetchResult with observation data
        """
        # Check for indicator_code in config
        indicator_code = getattr(config, 'indicator_code', None)
        if not indicator_code:
            return FetchResult(
                success=False,
                data=[],
                error="indicator_code required for e-Stat Dashboard connector",
                source=self.SOURCE_NAME
            )

        url = f"{self.BASE_URL}/Json/getData"
        params = {
            "IndicatorCode": indicator_code,
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            result = data.get('GET_STATS', {}).get('RESULT', {})
            if result.get('status') != '0':
                return FetchResult(
                    success=False,
                    data=[],
                    error=f"e-Stat API error: {result.get('errorMsg', 'Unknown error')}",
                    source=self.SOURCE_NAME
                )

            # Extract data objects
            data_objs = (
                data.get('GET_STATS', {})
                .get('STATISTICAL_DATA', {})
                .get('DATA_INF', {})
                .get('DATA_OBJ', [])
            )

            if not data_objs:
                return FetchResult(
                    success=False,
                    data=[],
                    error="No data returned from e-Stat API",
                    source=self.SOURCE_NAME
                )

            return FetchResult(
                success=True,
                data=data_objs,
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
        Convert e-Stat data to standard observation format.

        e-Stat structure:
        {
            "VALUE": {
                "@indicator": "0301010000020020010",
                "@time": "202411M00",  # Format: YYYYMM00 or YYYYNQ00 or YYYYCY00
                "@cycle": "1",  # 1=monthly, 2=quarterly, 3=annual
                "$": "2.5"  # The actual value
            }
        }
        """
        observations = []

        for item in raw_data:
            if not isinstance(item, dict) or 'VALUE' not in item:
                continue

            value_obj = item['VALUE']
            value_str = value_obj.get('$', '')

            # Skip missing or invalid values
            if not value_str or value_str == '':
                continue

            try:
                value = float(value_str) * config.multiplier
            except (ValueError, TypeError):
                continue

            # Parse time period
            time_period = value_obj.get('@time', '')
            obs_date = self._parse_time_period(time_period)

            if not obs_date:
                continue

            obs = Observation(
                metric_id=config.metric_id,
                obs_date=obs_date,
                value=round(value, config.decimals),
                unit=config.unit,
                source=self.SOURCE_NAME,
                retrieved_at=datetime.now()
            )
            observations.append(obs)

        # Sort by date descending
        observations.sort(key=lambda x: x.obs_date, reverse=True)
        return observations

    def _parse_time_period(self, period: str) -> str:
        """
        Convert e-Stat time period formats to YYYY-MM-DD.

        Formats:
        - 202411M00 -> 2024-11-01 (monthly)
        - 20243Q00 -> 2024-07-01 (quarterly, Q3 = July)
        - 2024CY00 -> 2024-01-01 (calendar year)
        - 2024FY00 -> 2024-04-01 (fiscal year, starts April in Japan)
        """
        if not period or len(period) < 6:
            return ""

        try:
            if 'M' in period:
                # Monthly: 202411M00 -> 2024-11-01
                year = period[:4]
                month = period[4:6]
                return f"{year}-{month}-01"

            elif 'Q' in period:
                # Quarterly: 20243Q00 -> 2024-07-01
                year = period[:4]
                quarter = period[4]
                month_map = {'1': '01', '2': '04', '3': '07', '4': '10'}
                month = month_map.get(quarter, '01')
                return f"{year}-{month}-01"

            elif 'CY' in period:
                # Calendar year: 2024CY00 -> 2024-01-01
                year = period[:4]
                return f"{year}-01-01"

            elif 'FY' in period:
                # Fiscal year: 2024FY00 -> 2024-04-01 (Japan FY starts April)
                year = period[:4]
                return f"{year}-04-01"

            else:
                # Unknown format, try to extract year
                year = period[:4]
                return f"{year}-01-01"

        except (IndexError, ValueError):
            return ""

    def health_check(self) -> bool:
        """Check e-Stat Dashboard API availability."""
        try:
            # Test with a known stable indicator (unemployment rate)
            response = requests.get(
                f"{self.BASE_URL}/Json/getData",
                params={"IndicatorCode": "0301010000020020010"},
                timeout=10
            )
            if response.status_code != 200:
                return False

            data = response.json()
            result = data.get('GET_STATS', {}).get('RESULT', {})
            return result.get('status') == '0'

        except requests.RequestException:
            return False
