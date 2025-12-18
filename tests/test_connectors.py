"""
Tests for data connectors with mocked API responses.

All tests run without network access using unittest.mock.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.connectors.fred import FREDConnector
from src.connectors.ecb import ECBConnector
from src.connectors.worldbank import WorldBankConnector
from src.connectors.hackernews import HNFirebaseConnector, HNAlgoliaConnector
from src.connectors.base import ConnectorConfig, FeedConfig


class TestFREDConnector:
    """Tests for FRED API connector."""

    @pytest.fixture
    def connector(self):
        """Create connector with test API key."""
        return FREDConnector(api_key="test_api_key")

    @pytest.fixture
    def config(self):
        """Create standard test config."""
        return ConnectorConfig(
            metric_id="us_gdp",
            name="US GDP",
            source="fred",
            frequency="quarterly",
            series_id="GDP",
            unit="$B",
            decimals=2,
            multiplier=1.0
        )

    def test_fred_connector_fetch_success(self, connector, config):
        """Test successful FRED API fetch."""
        mock_response = {
            "observations": [
                {"date": "2024-10-01", "value": "29000.5"},
                {"date": "2024-07-01", "value": "28500.2"},
                {"date": "2024-04-01", "value": "28100.0"},
            ]
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response
            )
            mock_get.return_value.raise_for_status = MagicMock()

            result = connector.fetch(config)

            assert result.success is True
            assert len(result.data) == 3
            assert result.source == "fred"
            assert result.error is None

    def test_fred_connector_fetch_missing_series_id(self, connector):
        """Test fetch fails without series_id."""
        config = ConnectorConfig(
            metric_id="test",
            name="Test",
            source="fred",
            frequency="monthly"
        )

        result = connector.fetch(config)

        assert result.success is False
        assert "series_id required" in result.error

    def test_fred_connector_fetch_api_error(self, connector, config):
        """Test handling of API errors."""
        import requests as req
        with patch("requests.get") as mock_get:
            mock_get.side_effect = req.RequestException("Connection timeout")

            result = connector.fetch(config)

            assert result.success is False
            assert "Connection timeout" in result.error

    def test_fred_connector_normalize(self, connector, config):
        """Test normalization of FRED data."""
        raw_data = [
            {"date": "2024-10-01", "value": "29000.5"},
            {"date": "2024-07-01", "value": "28500.2"},
            {"date": "2024-04-01", "value": "."},  # Missing value
        ]

        observations = connector.normalize(config, raw_data)

        assert len(observations) == 2  # Missing value skipped
        assert observations[0].metric_id == "us_gdp"
        assert observations[0].value == 29000.5
        assert observations[0].obs_date == "2024-10-01"
        assert observations[0].source == "fred"

    def test_fred_connector_init_requires_api_key(self):
        """Test connector requires API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                FREDConnector(api_key=None)
            assert "FRED_API_KEY required" in str(exc_info.value)


class TestECBConnector:
    """Tests for ECB SDMX API connector."""

    @pytest.fixture
    def connector(self):
        return ECBConnector()

    @pytest.fixture
    def config(self):
        return ConnectorConfig(
            metric_id="ecb_dfr",
            name="ECB Deposit Facility Rate",
            source="ecb",
            frequency="monthly",
            dataflow="FM",
            series_key="M.U2.EUR.4F.KR.DFR.LEV",
            unit="%",
            decimals=2
        )

    def test_ecb_connector_fetch_success(self, connector, config):
        """Test successful ECB SDMX fetch."""
        mock_response = {
            "dataSets": [{
                "series": {
                    "0:0:0:0:0:0:0": {
                        "observations": {
                            "0": [3.5],
                            "1": [3.25],
                            "2": [3.0]
                        }
                    }
                }
            }],
            "structure": {
                "dimensions": {
                    "observation": [{
                        "id": "TIME_PERIOD",
                        "values": [
                            {"id": "2024-10"},
                            {"id": "2024-09"},
                            {"id": "2024-08"}
                        ]
                    }]
                }
            }
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response
            )
            mock_get.return_value.raise_for_status = MagicMock()

            result = connector.fetch(config)

            assert result.success is True
            assert result.source == "ecb"

    def test_ecb_connector_fetch_missing_config(self, connector):
        """Test fetch fails without required fields."""
        config = ConnectorConfig(
            metric_id="test",
            name="Test",
            source="ecb",
            frequency="monthly"
        )

        result = connector.fetch(config)

        assert result.success is False
        assert "dataflow and series_key required" in result.error

    def test_ecb_connector_normalize(self, connector, config):
        """Test normalization of ECB SDMX data."""
        raw_data = {
            "dataSets": [{
                "series": {
                    "0:0:0": {
                        "observations": {
                            "0": [3.5],
                            "1": [3.25]
                        }
                    }
                }
            }],
            "structure": {
                "dimensions": {
                    "observation": [{
                        "id": "TIME_PERIOD",
                        "values": [
                            {"id": "2024-10"},
                            {"id": "2024-09"}
                        ]
                    }]
                }
            }
        }

        observations = connector.normalize(config, raw_data)

        assert len(observations) == 2
        assert observations[0].value == 3.5
        # ECB monthly dates get -01 appended
        assert observations[0].obs_date == "2024-10-01"

    def test_ecb_parse_time_period_quarterly(self, connector):
        """Test quarterly time period parsing."""
        assert connector._parse_time_period("2024-Q1") == "2024-01-01"
        assert connector._parse_time_period("2024-Q2") == "2024-04-01"
        assert connector._parse_time_period("2024-Q3") == "2024-07-01"
        assert connector._parse_time_period("2024-Q4") == "2024-10-01"

    def test_ecb_parse_time_period_annual(self, connector):
        """Test annual time period parsing."""
        assert connector._parse_time_period("2024") == "2024-01-01"


class TestWorldBankConnector:
    """Tests for World Bank API connector."""

    @pytest.fixture
    def connector(self):
        return WorldBankConnector()

    @pytest.fixture
    def config(self):
        return ConnectorConfig(
            metric_id="world_gdp",
            name="World GDP",
            source="worldbank",
            frequency="annual",
            indicator="NY.GDP.MKTP.CD",
            country="WLD",
            unit="$T",
            decimals=2,
            multiplier=1e-12
        )

    def test_worldbank_connector_fetch_success(self, connector, config):
        """Test successful World Bank fetch."""
        mock_response = [
            {"page": 1, "pages": 1, "total": 3},
            [
                {"date": "2023", "value": 105000000000000},
                {"date": "2022", "value": 100000000000000},
                {"date": "2021", "value": 96000000000000}
            ]
        ]

        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response
            )
            mock_get.return_value.raise_for_status = MagicMock()

            result = connector.fetch(config)

            assert result.success is True
            assert len(result.data) == 3
            assert result.source == "worldbank"

    def test_worldbank_connector_fetch_missing_indicator(self, connector):
        """Test fetch fails without indicator."""
        config = ConnectorConfig(
            metric_id="test",
            name="Test",
            source="worldbank",
            frequency="annual"
        )

        result = connector.fetch(config)

        assert result.success is False
        assert "indicator required" in result.error

    def test_worldbank_connector_normalize(self, connector, config):
        """Test normalization of World Bank data."""
        raw_data = [
            {"date": "2023", "value": 105000000000000},
            {"date": "2022", "value": 100000000000000},
            {"date": "2021", "value": None}  # Null value
        ]

        observations = connector.normalize(config, raw_data)

        assert len(observations) == 2  # Null skipped
        # Check multiplier applied (1e-12 converts to trillions)
        assert observations[0].value == 105.0  # 105T
        assert observations[0].obs_date == "2023-01-01"

    def test_worldbank_connector_default_country(self, connector):
        """Test default country is WLD (World)."""
        config = ConnectorConfig(
            metric_id="test",
            name="Test",
            source="worldbank",
            frequency="annual",
            indicator="NY.GDP.MKTP.CD"
        )

        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: [{}, []]
            )
            mock_get.return_value.raise_for_status = MagicMock()

            connector.fetch(config)

            call_url = mock_get.call_args[0][0]
            assert "/country/WLD/" in call_url


class TestHNFirebaseConnector:
    """Tests for HN Firebase API connector."""

    @pytest.fixture
    def connector(self):
        return HNFirebaseConnector()

    @pytest.fixture
    def config(self):
        return FeedConfig(
            id="hn_top",
            name="HN Top Stories",
            source="hn_firebase",
            endpoint="topstories",
            limit=5
        )

    def test_hn_firebase_connector_fetch_success(self, connector, config):
        """Test successful Firebase fetch."""
        story_ids = [12345, 12346, 12347, 12348, 12349]
        story_data = {
            "id": 12345,
            "type": "story",
            "title": "Test Story",
            "url": "https://example.com",
            "score": 100,
            "descendants": 50,
            "by": "testuser",
            "time": 1700000000
        }

        with patch("requests.get") as mock_get:
            def side_effect(url, **kwargs):
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()

                if "topstories" in url:
                    mock_response.json = lambda: story_ids
                else:
                    mock_response.json = lambda: story_data

                return mock_response

            mock_get.side_effect = side_effect

            result = connector.fetch(config)

            assert result.success is True
            assert result.source == "hn_firebase"
            assert len(result.data) <= 5

    def test_hn_firebase_connector_normalize(self, connector, config):
        """Test normalization of Firebase story data."""
        raw_data = [
            {
                "id": 12345,
                "type": "story",
                "title": "Test Story",
                "url": "https://example.com",
                "score": 100,
                "descendants": 50,
                "by": "testuser",
                "time": 1700000000
            }
        ]

        stories = connector.normalize(config, raw_data)

        assert len(stories) == 1
        assert stories[0].id == 12345
        assert stories[0].title == "Test Story"
        assert stories[0].score == 100
        assert stories[0].author == "testuser"
        assert stories[0].source == "hn_firebase"

    def test_hn_firebase_connector_handles_missing_fields(self, connector, config):
        """Test normalization handles missing optional fields."""
        raw_data = [
            {
                "id": 12345,
                "type": "story"
            }
        ]

        stories = connector.normalize(config, raw_data)

        assert len(stories) == 1
        assert stories[0].title == ""
        assert stories[0].url is None
        assert stories[0].score == 0


class TestHNAlgoliaConnector:
    """Tests for HN Algolia API connector."""

    @pytest.fixture
    def connector(self):
        return HNAlgoliaConnector()

    @pytest.fixture
    def config(self):
        return FeedConfig(
            id="hn_ai",
            name="HN AI News",
            source="hn_algolia",
            query="artificial intelligence",
            tags="story",
            limit=10
        )

    def test_hn_algolia_connector_fetch_success(self, connector, config):
        """Test successful Algolia search."""
        mock_response = {
            "hits": [
                {
                    "objectID": "12345",
                    "title": "AI Breakthrough",
                    "url": "https://example.com/ai",
                    "points": 200,
                    "num_comments": 100,
                    "author": "aiuser",
                    "created_at": "2024-01-15T10:30:00.000Z"
                }
            ],
            "nbHits": 1
        }

        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response
            )
            mock_get.return_value.raise_for_status = MagicMock()

            result = connector.fetch(config)

            assert result.success is True
            assert len(result.data) == 1
            assert result.source == "hn_algolia"

    def test_hn_algolia_connector_fetch_missing_query(self, connector):
        """Test fetch fails without query."""
        config = FeedConfig(
            id="test",
            name="Test",
            source="hn_algolia"
        )

        result = connector.fetch(config)

        assert result.success is False
        assert "query required" in result.error

    def test_hn_algolia_connector_normalize(self, connector, config):
        """Test normalization of Algolia hits."""
        raw_data = [
            {
                "objectID": "12345",
                "title": "AI Breakthrough",
                "url": "https://example.com/ai",
                "points": 200,
                "num_comments": 100,
                "author": "aiuser",
                "created_at": "2024-01-15T10:30:00Z"
            }
        ]

        stories = connector.normalize(config, raw_data)

        assert len(stories) == 1
        assert stories[0].id == 12345
        assert stories[0].title == "AI Breakthrough"
        assert stories[0].score == 200
        assert stories[0].comments == 100
        assert stories[0].source == "hn_algolia"

    def test_hn_algolia_connector_time_range(self, connector):
        """Test time range filter is applied."""
        config = FeedConfig(
            id="test",
            name="Test",
            source="hn_algolia",
            query="test",
            time_range="week"
        )

        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: {"hits": []}
            )
            mock_get.return_value.raise_for_status = MagicMock()

            connector.fetch(config)

            # Should use search_by_date endpoint for time range
            call_url = mock_get.call_args[0][0]
            assert "search_by_date" in call_url


class TestConnectorHealthChecks:
    """Tests for connector health check methods."""

    def test_fred_health_check_success(self):
        """Test FRED health check with successful response."""
        connector = FREDConnector(api_key="test_key")

        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)

            assert connector.health_check() is True

    def test_fred_health_check_failure(self):
        """Test FRED health check with failed response."""
        import requests as req
        connector = FREDConnector(api_key="test_key")

        with patch("requests.get") as mock_get:
            mock_get.side_effect = req.RequestException("Network error")

            assert connector.health_check() is False

    def test_ecb_health_check_success(self):
        """Test ECB health check with successful response."""
        connector = ECBConnector()

        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)

            assert connector.health_check() is True

    def test_worldbank_health_check_success(self):
        """Test World Bank health check with successful response."""
        connector = WorldBankConnector()

        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)

            assert connector.health_check() is True
