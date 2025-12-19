"""Data connectors for various sources."""
from .base import (
    BaseMetricConnector,
    BaseFeedConnector,
    ConnectorConfig,
    FeedConfig,
    FetchResult,
)
from .fred import FREDConnector
from .ecb import ECBConnector
from .worldbank import WorldBankConnector
from .imf import IMFConnector
from .estat_dashboard import EStatDashboardConnector
from .coingecko import CoinGeckoConnector
from .yahoo import YahooFinanceConnector
from .oecd import OECDConnector
from .hackernews import HNFirebaseConnector, HNAlgoliaConnector

__all__ = [
    "BaseMetricConnector",
    "BaseFeedConnector",
    "ConnectorConfig",
    "FeedConfig",
    "FetchResult",
    "FREDConnector",
    "ECBConnector",
    "WorldBankConnector",
    "IMFConnector",
    "EStatDashboardConnector",
    "CoinGeckoConnector",
    "YahooFinanceConnector",
    "OECDConnector",
    "HNFirebaseConnector",
    "HNAlgoliaConnector",
]
