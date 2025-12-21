"""
HuggingFace Datasets connector for LLM benchmarks.

Handles:
- Open LLM Leaderboard scores
- Model benchmark tracking

API Notes:
- Uses HuggingFace Datasets Server API for structured data access
- No authentication required for public datasets
- Leaderboard data: open-llm-leaderboard/contents
"""
import re
from datetime import datetime
from typing import Any

import requests

from .base import BaseMetricConnector, ConnectorConfig, FetchResult
from ..storage.models import Observation


class HuggingFaceConnector(BaseMetricConnector):
    """Connector for HuggingFace Open LLM Leaderboard."""

    SOURCE_NAME = "huggingface"
    BASE_URL = "https://huggingface.co"

    # Datasets Server API - provides structured access to HuggingFace datasets
    DATASETS_SERVER = "https://datasets-server.huggingface.co"

    # Sample offsets to scan the leaderboard (dataset is sorted alphabetically)
    SAMPLE_OFFSETS = [0, 1000, 2000, 3000, 4000]
    BATCH_SIZE = 100

    def fetch(self, config: ConnectorConfig) -> FetchResult:
        """
        Fetch LLM leaderboard data from HuggingFace Datasets Server.

        Samples from multiple offsets in the dataset to find the top-scoring
        models since the dataset is sorted alphabetically, not by score.

        Args:
            config: Configuration for the metric

        Returns:
            FetchResult with leaderboard data including top model and score
        """
        all_models = []

        try:
            # Fetch from multiple offsets to sample the full dataset
            for offset in self.SAMPLE_OFFSETS:
                url = (
                    f"{self.DATASETS_SERVER}/rows"
                    f"?dataset=open-llm-leaderboard/contents"
                    f"&config=default&split=train"
                    f"&offset={offset}&length={self.BATCH_SIZE}"
                )

                response = requests.get(url, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    for row_data in data.get("rows", []):
                        row = row_data.get("row", {})
                        model_html = row.get("Model", "")

                        # Extract model name from HTML anchor tag
                        match = re.search(r">([^<]+)</a>", model_html)
                        name = match.group(1) if match else model_html

                        avg_score = row.get("Average ⬆️", 0)
                        if avg_score and name:
                            all_models.append({
                                "name": name,
                                "score": float(avg_score)
                            })

            if all_models:
                # Sort by score descending
                all_models.sort(key=lambda x: x["score"], reverse=True)

                return FetchResult(
                    success=True,
                    data={
                        "top_models": all_models[:10],
                        "top_score": all_models[0]["score"],
                        "top_model": all_models[0]["name"],
                        "sample_size": len(all_models)
                    },
                    source=self.SOURCE_NAME
                )

            # No data found
            return FetchResult(
                success=False,
                data=[],
                error="No leaderboard data found in HuggingFace dataset",
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
        Convert HuggingFace leaderboard data to observations.

        For LLM benchmarks, we track:
        - Top model score (average across benchmarks)

        Returns a single observation with the top score from the leaderboard.
        """
        observations = []
        today = datetime.now().strftime("%Y-%m-%d")

        if isinstance(raw_data, dict) and "top_score" in raw_data:
            top_score = raw_data["top_score"]
            top_model = raw_data.get("top_model", "unknown")

            obs = Observation(
                metric_id=config.metric_id,
                obs_date=today,
                value=round(top_score * config.multiplier, config.decimals),
                unit=config.unit,
                source=self.SOURCE_NAME,
                retrieved_at=datetime.now()
            )
            observations.append(obs)

        return observations

    def health_check(self) -> bool:
        """Check HuggingFace Datasets Server availability."""
        try:
            # Test the datasets-server API with a minimal request
            url = (
                f"{self.DATASETS_SERVER}/rows"
                f"?dataset=open-llm-leaderboard/contents"
                f"&config=default&split=train&offset=0&length=1"
            )
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False
