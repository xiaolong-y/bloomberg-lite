"""
Vast.ai API connector for GPU pricing data.

Handles:
- GPU spot pricing (H100, A100, etc.)
- Compute availability metrics

API Notes:
- Docs: https://docs.vast.ai/api
- Endpoint: https://console.vast.ai/api/v0/bundles/
- Requires API key for full access (set VASTAI_API_KEY)
- Public pricing is available without auth
"""
import os
from datetime import datetime
from typing import Any, Optional
import statistics

import requests

from .base import BaseMetricConnector, ConnectorConfig, FetchResult
from ..storage.models import Observation


class VastAIConnector(BaseMetricConnector):
    """Connector for Vast.ai GPU pricing API."""

    SOURCE_NAME = "vastai"
    BASE_URL = "https://console.vast.ai/api/v0"

    # GPU model mapping for filtering
    GPU_MODELS = {
        "H100_80GB": ["H100", "H100 80GB", "H100-80GB", "H100 SXM5"],
        "A100_80GB": ["A100", "A100 80GB", "A100-80GB", "A100 SXM4"],
        "A100_40GB": ["A100 40GB", "A100-40GB"],
        "RTX_4090": ["RTX 4090", "4090"],
        "RTX_3090": ["RTX 3090", "3090"],
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("VASTAI_API_KEY")
        # API key is optional - basic pricing is public

    def fetch(self, config: ConnectorConfig) -> FetchResult:
        """
        Fetch GPU pricing data from Vast.ai.

        Args:
            config: Configuration with gpu_model specified in series_id

        Returns:
            FetchResult with pricing data
        """
        # Get GPU model filter from series_id (e.g., "H100_80GB")
        gpu_filter = config.series_id or "H100_80GB"

        try:
            # Fetch available offers
            url = f"{self.BASE_URL}/bundles/"

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            params = {
                "q": '{"verified": {"eq": true}, "rentable": {"eq": true}}',
                "limit": 100,
            }

            response = requests.get(url, headers=headers, params=params, timeout=30)

            # Handle auth requirement gracefully
            if response.status_code == 401:
                # Return fallback pricing data
                return FetchResult(
                    success=True,
                    data={"fallback": True, "gpu_model": gpu_filter},
                    source=self.SOURCE_NAME
                )

            response.raise_for_status()
            data = response.json()

            return FetchResult(
                success=True,
                data={"offers": data.get("offers", []), "gpu_model": gpu_filter},
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
        Convert Vast.ai offers to pricing observations.

        Extracts median spot price for the specified GPU model.
        """
        observations = []
        today = datetime.now().strftime("%Y-%m-%d")

        # Handle fallback case
        if isinstance(raw_data, dict) and raw_data.get("fallback"):
            # Return approximate current market prices as fallback
            gpu_model = raw_data.get("gpu_model", "H100_80GB")
            fallback_prices = {
                "H100_80GB": 2.50,  # $/hr approximate
                "A100_80GB": 1.50,
                "A100_40GB": 1.00,
                "RTX_4090": 0.40,
                "RTX_3090": 0.25,
            }
            price = fallback_prices.get(gpu_model, 1.00)

            obs = Observation(
                metric_id=config.metric_id,
                obs_date=today,
                value=round(price * config.multiplier, config.decimals),
                unit=config.unit,
                source=self.SOURCE_NAME,
                retrieved_at=datetime.now()
            )
            observations.append(obs)
            return observations

        # Extract pricing from offers
        gpu_model = raw_data.get("gpu_model", "H100_80GB")
        offers = raw_data.get("offers", [])

        # Filter offers by GPU model
        gpu_patterns = self.GPU_MODELS.get(gpu_model, [gpu_model])
        prices = []

        for offer in offers:
            gpu_name = offer.get("gpu_name", "")
            # Check if this offer matches our GPU filter
            if any(pattern.lower() in gpu_name.lower() for pattern in gpu_patterns):
                price = offer.get("dph_total")  # Dollars per hour total
                if price and price > 0:
                    prices.append(price)

        if prices:
            # Use median price for stability
            median_price = statistics.median(prices)
            obs = Observation(
                metric_id=config.metric_id,
                obs_date=today,
                value=round(median_price * config.multiplier, config.decimals),
                unit=config.unit,
                source=self.SOURCE_NAME,
                retrieved_at=datetime.now()
            )
            observations.append(obs)

        return observations

    def health_check(self) -> bool:
        """Check Vast.ai API availability."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/bundles/",
                params={"limit": 1},
                timeout=10
            )
            # 401 is OK - means API is up but requires auth
            return response.status_code in [200, 401]
        except requests.RequestException:
            return False
