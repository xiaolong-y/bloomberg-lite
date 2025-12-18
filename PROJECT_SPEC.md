# Bloomberg-Lite: Personal Macro & Tech Intelligence Dashboard

## Project Overview

Build a zero-cost, self-hosted information aggregator that pulls macroeconomic data from official sources and tech discussion from Hacker News into a single dense dashboard. The system runs entirely on GitHub Actions + GitHub Pages with no paid infrastructure.

**Design Philosophy:** Radical simplicity. Fewer sources, better curation, zero maintenance burden.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION LAYER                               │
│                     (GitHub Actions Scheduler)                           │
│                      Runs: Every 6 hours                                 │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION LAYER                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │    FRED     │  │     ECB     │  │ World Bank  │  │ Hacker News │    │
│  │  Connector  │  │  Connector  │  │  Connector  │  │  Connector  │    │
│  │  (US data)  │  │  (EU data)  │  │  (Global)   │  │  (Tech news)│    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         └────────────────┴────────────────┴────────────────┘            │
│                                   │                                      │
│                                   ▼                                      │
│                        ┌───────────────────┐                            │
│                        │    Normalizer     │                            │
│                        │  (unified schema) │                            │
│                        └─────────┬─────────┘                            │
└──────────────────────────────────┼──────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PERSISTENCE LAYER                                │
│                     ┌───────────────────────┐                           │
│                     │       SQLite          │                           │
│                     │  - observations       │                           │
│                     │  - stories            │                           │
│                     │  - metrics metadata   │                           │
│                     └───────────┬───────────┘                           │
└─────────────────────────────────┼───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                                │
│                    ┌────────────────────────┐                           │
│                    │   Static HTML Generator │                           │
│                    │   (Jinja2 templates)    │                           │
│                    └───────────┬────────────┘                           │
│                                │                                         │
│                                ▼                                         │
│                    ┌────────────────────────┐                           │
│                    │    GitHub Pages        │                           │
│                    │  (static hosting)      │                           │
│                    └────────────────────────┘                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
bloomberg-lite/
├── README.md                    # Project documentation
├── CONTRIBUTING.md              # Development guide
├── config/
│   ├── metrics.yaml             # Metric definitions & API mappings
│   └── feeds.yaml               # HN feed configurations
├── src/
│   ├── __init__.py
│   ├── main.py                  # Orchestrator entry point
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract connector interface
│   │   ├── fred.py              # FRED API connector
│   │   ├── ecb.py               # ECB SDMX connector
│   │   ├── worldbank.py         # World Bank API connector
│   │   └── hackernews.py        # HN Firebase + Algolia connector
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py          # SQLite operations
│   │   └── models.py            # Data models / schemas
│   ├── transforms/
│   │   ├── __init__.py
│   │   └── calculations.py      # YoY, QoQ, moving averages
│   └── generator/
│       ├── __init__.py
│       ├── html.py              # HTML generation logic
│       └── sparklines.py        # ASCII/SVG sparkline generator
├── templates/
│   ├── dashboard.html           # Main dashboard template
│   ├── partials/
│   │   ├── macro_panel.html     # Macro data section
│   │   ├── tech_panel.html      # Tech news section
│   │   └── metric_card.html     # Individual metric display
│   └── static/
│       └── style.css            # Dashboard styles
├── data/
│   └── bloomberg_lite.db        # SQLite database (gitignored)
├── docs/
│   └── index.html               # Generated dashboard (GitHub Pages)
├── tests/
│   ├── __init__.py
│   ├── test_connectors.py
│   ├── test_transforms.py
│   └── test_generator.py
├── .github/
│   └── workflows/
│       └── update.yaml          # Scheduled update workflow
├── .env.example                 # Environment variables template
├── .gitignore
├── pyproject.toml               # Project dependencies
└── requirements.txt             # Pip requirements (fallback)
```

---

## Agent Task Breakdown

This project is designed for parallel subagent execution. Each agent handles a discrete, well-defined component.

### Agent 1: Project Scaffolding

**Task:** Initialize project structure and configuration files.

**Deliverables:**
- [ ] Create directory structure as specified above
- [ ] Initialize `pyproject.toml` with dependencies:
  ```toml
  [project]
  name = "bloomberg-lite"
  version = "0.1.0"
  requires-python = ">=3.11"
  dependencies = [
      "requests>=2.31.0",
      "pyyaml>=6.0",
      "jinja2>=3.1.0",
      "python-dotenv>=1.0.0",
  ]

  [project.optional-dependencies]
  dev = ["pytest>=8.0", "ruff>=0.1.0"]
  ```
- [ ] Create `.gitignore` (Python defaults + `data/*.db`, `.env`)
- [ ] Create `.env.example` with required variables
- [ ] Create `requirements.txt` from pyproject.toml

**Acceptance Criteria:**
- `pip install -e .` succeeds
- All directories exist
- `.env.example` documents all required secrets

---

### Agent 2: Configuration Schema

**Task:** Define YAML configuration schemas for metrics and feeds.

**Deliverables:**

**config/metrics.yaml:**
```yaml
# Metric Configuration Schema
# Each metric defines: identifier, display name, data source, and optional transforms

defaults:
  cache_hours: 6
  history_points: 120  # ~10 years monthly data

metrics:
  # ============================================
  # UNITED STATES (via FRED)
  # ============================================
  - id: us.fed_funds
    name: "Fed Funds Rate"
    source: fred
    series_id: FEDFUNDS
    frequency: monthly
    unit: "%"
    decimals: 2

  - id: us.cpi_yoy
    name: "US CPI YoY"
    source: fred
    series_id: CPIAUCSL
    frequency: monthly
    unit: "%"
    decimals: 1
    transform: yoy_percent

  - id: us.core_cpi_yoy
    name: "US Core CPI YoY"
    source: fred
    series_id: CPILFESL
    frequency: monthly
    unit: "%"
    decimals: 1
    transform: yoy_percent

  - id: us.unemployment
    name: "US Unemployment"
    source: fred
    series_id: UNRATE
    frequency: monthly
    unit: "%"
    decimals: 1

  - id: us.gdp_qoq
    name: "US GDP QoQ"
    source: fred
    series_id: GDP
    frequency: quarterly
    unit: "%"
    decimals: 1
    transform: qoq_percent

  - id: us.yield_curve
    name: "10Y-2Y Spread"
    source: fred
    series_id: T10Y2Y
    frequency: daily
    unit: "bp"
    decimals: 0
    multiplier: 100  # Convert to basis points

  # ============================================
  # EUROZONE (via ECB SDMX)
  # ============================================
  - id: eu.deposit_rate
    name: "ECB Deposit Rate"
    source: ecb
    dataflow: FM
    series_key: M.U2.EUR.4F.KR.DFR.LEV
    frequency: monthly
    unit: "%"
    decimals: 2

  - id: eu.hicp_yoy
    name: "Eurozone HICP YoY"
    source: ecb
    dataflow: ICP
    series_key: M.U2.N.000000.4.ANR
    frequency: monthly
    unit: "%"
    decimals: 1

  - id: eu.unemployment
    name: "Eurozone Unemployment"
    source: ecb
    dataflow: STS
    series_key: M.I9.S.UNEH.RTT000.4.000
    frequency: monthly
    unit: "%"
    decimals: 1

  # ============================================
  # GLOBAL (via FRED mirrors)
  # ============================================
  - id: global.brent
    name: "Brent Crude"
    source: fred
    series_id: DCOILBRENTEU
    frequency: daily
    unit: "$/bbl"
    decimals: 2

  - id: global.gold
    name: "Gold (London PM)"
    source: fred
    series_id: GOLDPMGBD228NLBM
    frequency: daily
    unit: "$/oz"
    decimals: 0

  - id: global.dxy
    name: "USD Index (DXY)"
    source: fred
    series_id: DTWEXBGS
    frequency: daily
    unit: "index"
    decimals: 1

  # ============================================
  # WORLD (via World Bank)
  # ============================================
  - id: world.gdp_growth
    name: "World GDP Growth"
    source: worldbank
    indicator: NY.GDP.MKTP.KD.ZG
    country: WLD
    frequency: annual
    unit: "%"
    decimals: 1

# Display groupings for dashboard layout
groups:
  - name: "US Economy"
    metrics: [us.fed_funds, us.cpi_yoy, us.core_cpi_yoy, us.unemployment, us.gdp_qoq, us.yield_curve]

  - name: "Eurozone"
    metrics: [eu.deposit_rate, eu.hicp_yoy, eu.unemployment]

  - name: "Global Markets"
    metrics: [global.brent, global.gold, global.dxy]
```

**config/feeds.yaml:**
```yaml
# Tech Feed Configuration

feeds:
  - id: hn_top
    name: "Top Stories"
    source: hn_firebase
    endpoint: topstories
    limit: 20
    refresh_minutes: 30

  - id: hn_best
    name: "Best Stories"
    source: hn_firebase
    endpoint: beststories
    limit: 10
    refresh_minutes: 60

  - id: hn_ai
    name: "AI/ML"
    source: hn_algolia
    query: "LLM OR GPT OR Claude OR transformer OR \"machine learning\" OR \"neural network\""
    tags: story
    time_range: week
    limit: 15

  - id: hn_data
    name: "Databases & Data"
    source: hn_algolia
    query: "postgres OR sqlite OR duckdb OR \"data engineering\" OR ETL"
    tags: story
    time_range: week
    limit: 10

  - id: hn_fintech
    name: "Finance & Trading"
    source: hn_algolia
    query: "trading OR Bloomberg OR \"quantitative finance\" OR fintech"
    tags: story
    time_range: month
    limit: 10

display:
  primary_feed: hn_top
  sidebar_feeds: [hn_ai, hn_data]
```

**Acceptance Criteria:**
- YAML files parse without errors
- All metric IDs are unique
- All referenced sources have connector implementations
- Groups reference valid metric IDs

---

### Agent 3: Database Layer

**Task:** Implement SQLite storage with proper schema and CRUD operations.

**Deliverables:**

**src/storage/models.py:**
```python
"""
Data models for Bloomberg-Lite storage layer.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Observation:
    """A single data point for a metric."""
    metric_id: str
    obs_date: str  # ISO format YYYY-MM-DD
    value: float
    unit: Optional[str] = None
    source: str = ""
    retrieved_at: Optional[datetime] = None

@dataclass
class Story:
    """A Hacker News story."""
    id: int  # HN item ID
    title: str
    url: Optional[str]
    score: int
    comments: int
    author: str
    posted_at: datetime
    source: str  # hn_firebase or hn_algolia
    feed_id: str  # Which config feed found this
    retrieved_at: Optional[datetime] = None

@dataclass
class MetricMeta:
    """Metadata about a tracked metric."""
    id: str
    name: str
    source: str
    frequency: str
    unit: Optional[str]
    last_value: Optional[float]
    last_updated: Optional[datetime]
    previous_value: Optional[float]
    change: Optional[float]
    change_percent: Optional[float]
```

**src/storage/database.py:**
```python
"""
SQLite database operations for Bloomberg-Lite.

Design principles:
- Append-only for observations (full history)
- Rolling window for stories (7 days)
- Idempotent upserts (safe to re-run)
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator, Optional

from .models import Observation, Story, MetricMeta

DB_PATH = Path(__file__).parent.parent.parent / "data" / "bloomberg_lite.db"

SCHEMA = """
-- Macro observations (append-only, keeps full history)
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_id TEXT NOT NULL,
    obs_date TEXT NOT NULL,  -- YYYY-MM-DD
    value REAL NOT NULL,
    unit TEXT,
    source TEXT NOT NULL,
    retrieved_at TEXT DEFAULT (datetime('now')),
    UNIQUE(metric_id, obs_date, source)
);

CREATE INDEX IF NOT EXISTS idx_obs_metric ON observations(metric_id);
CREATE INDEX IF NOT EXISTS idx_obs_date ON observations(obs_date DESC);

-- Tech stories (rolling 7-day window)
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY,  -- HN item ID
    title TEXT NOT NULL,
    url TEXT,
    score INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    author TEXT,
    posted_at TEXT,
    source TEXT NOT NULL,
    feed_id TEXT NOT NULL,
    retrieved_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_stories_feed ON stories(feed_id);
CREATE INDEX IF NOT EXISTS idx_stories_score ON stories(score DESC);

-- Metric metadata cache
CREATE TABLE IF NOT EXISTS metrics (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source TEXT NOT NULL,
    frequency TEXT,
    unit TEXT,
    last_value REAL,
    last_updated TEXT,
    previous_value REAL,
    change REAL,
    change_percent REAL
);
"""

@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db() -> None:
    """Initialize database schema."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)

def upsert_observation(obs: Observation) -> None:
    """Insert or update an observation."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO observations (metric_id, obs_date, value, unit, source)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(metric_id, obs_date, source)
            DO UPDATE SET value = excluded.value, retrieved_at = datetime('now')
        """, (obs.metric_id, obs.obs_date, obs.value, obs.unit, obs.source))

def upsert_story(story: Story) -> None:
    """Insert or update a story."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO stories (id, title, url, score, comments, author, posted_at, source, feed_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                score = excluded.score,
                comments = excluded.comments,
                retrieved_at = datetime('now')
        """, (story.id, story.title, story.url, story.score, story.comments,
              story.author, story.posted_at.isoformat() if story.posted_at else None,
              story.source, story.feed_id))

def get_latest_observations(metric_id: str, limit: int = 120) -> list[dict]:
    """Get recent observations for a metric."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT obs_date, value, unit, source, retrieved_at
            FROM observations
            WHERE metric_id = ?
            ORDER BY obs_date DESC
            LIMIT ?
        """, (metric_id, limit)).fetchall()
        return [dict(row) for row in rows]

def get_stories_by_feed(feed_id: str, limit: int = 20) -> list[dict]:
    """Get stories for a specific feed."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, title, url, score, comments, author, posted_at, source
            FROM stories
            WHERE feed_id = ?
            ORDER BY score DESC
            LIMIT ?
        """, (feed_id, limit)).fetchall()
        return [dict(row) for row in rows]

def cleanup_old_stories(days: int = 7) -> int:
    """Remove stories older than N days. Returns count deleted."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM stories WHERE retrieved_at < ?", (cutoff,)
        )
        return cursor.rowcount

def update_metric_meta(meta: MetricMeta) -> None:
    """Update metric metadata cache."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO metrics (id, name, source, frequency, unit,
                                 last_value, last_updated, previous_value, change, change_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                last_value = excluded.last_value,
                last_updated = excluded.last_updated,
                previous_value = excluded.previous_value,
                change = excluded.change,
                change_percent = excluded.change_percent
        """, (meta.id, meta.name, meta.source, meta.frequency, meta.unit,
              meta.last_value, meta.last_updated.isoformat() if meta.last_updated else None,
              meta.previous_value, meta.change, meta.change_percent))

def get_all_metric_meta() -> list[dict]:
    """Get all metric metadata for dashboard display."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM metrics ORDER BY id").fetchall()
        return [dict(row) for row in rows]
```

**Acceptance Criteria:**
- `init_db()` creates all tables idempotently
- Upserts handle duplicates gracefully
- Queries return properly typed results
- Cleanup removes old stories correctly
- All operations are wrapped in transactions

---

### Agent 4: Base Connector Interface

**Task:** Define abstract connector interface that all data sources implement.

**Deliverables:**

**src/connectors/base.py:**
```python
"""
Abstract base class for all data connectors.

All connectors must implement:
1. fetch() - Retrieve raw data from source
2. normalize() - Convert to standard Observation/Story format
3. health_check() - Verify API connectivity
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from ..storage.models import Observation, Story

@dataclass
class ConnectorConfig:
    """Configuration passed to connectors."""
    metric_id: str
    name: str
    source: str
    frequency: str
    unit: Optional[str] = None
    decimals: int = 2
    transform: Optional[str] = None
    multiplier: float = 1.0
    # Source-specific fields
    series_id: Optional[str] = None  # FRED
    dataflow: Optional[str] = None   # ECB
    series_key: Optional[str] = None # ECB
    indicator: Optional[str] = None  # World Bank
    country: Optional[str] = None    # World Bank

@dataclass
class FeedConfig:
    """Configuration for tech feeds."""
    id: str
    name: str
    source: str
    limit: int = 20
    # Source-specific
    endpoint: Optional[str] = None   # HN Firebase
    query: Optional[str] = None      # HN Algolia
    tags: Optional[str] = None       # HN Algolia
    time_range: Optional[str] = None # HN Algolia

@dataclass
class FetchResult:
    """Result of a fetch operation."""
    success: bool
    data: list[Any]
    error: Optional[str] = None
    source: str = ""
    fetched_at: datetime = None

    def __post_init__(self):
        if self.fetched_at is None:
            self.fetched_at = datetime.now()

class BaseMetricConnector(ABC):
    """Abstract base for metric data connectors."""

    SOURCE_NAME: str = "base"

    @abstractmethod
    def fetch(self, config: ConnectorConfig) -> FetchResult:
        """
        Fetch raw data from the source API.

        Args:
            config: Metric configuration

        Returns:
            FetchResult with raw API response data
        """
        pass

    @abstractmethod
    def normalize(self, config: ConnectorConfig, raw_data: list[Any]) -> list[Observation]:
        """
        Convert raw API data to standard Observation format.

        Args:
            config: Metric configuration
            raw_data: Raw data from fetch()

        Returns:
            List of normalized Observation objects
        """
        pass

    def health_check(self) -> bool:
        """
        Verify API connectivity.

        Returns:
            True if API is reachable and responding
        """
        return True

    def fetch_and_normalize(self, config: ConnectorConfig) -> list[Observation]:
        """
        Convenience method: fetch + normalize in one call.
        """
        result = self.fetch(config)
        if not result.success:
            raise RuntimeError(f"Fetch failed: {result.error}")
        return self.normalize(config, result.data)

class BaseFeedConnector(ABC):
    """Abstract base for tech feed connectors."""

    SOURCE_NAME: str = "base"

    @abstractmethod
    def fetch(self, config: FeedConfig) -> FetchResult:
        """Fetch stories from the feed source."""
        pass

    @abstractmethod
    def normalize(self, config: FeedConfig, raw_data: list[Any]) -> list[Story]:
        """Convert raw data to Story objects."""
        pass

    def fetch_and_normalize(self, config: FeedConfig) -> list[Story]:
        """Convenience method: fetch + normalize."""
        result = self.fetch(config)
        if not result.success:
            raise RuntimeError(f"Fetch failed: {result.error}")
        return self.normalize(config, result.data)
```

**Acceptance Criteria:**
- Abstract methods cannot be instantiated
- Dataclasses are properly typed
- FetchResult captures both success and failure states
- Convenience method chains fetch → normalize

---

### Agent 5: FRED Connector

**Task:** Implement FRED API connector for US economic data.

**API Reference:**
- Base URL: `https://api.stlouisfed.org/fred/`
- Auth: API key required (free registration)
- Rate limit: 120 requests/minute
- Docs: https://fred.stlouisfed.org/docs/api/fred/

**Deliverables:**

**src/connectors/fred.py:**
```python
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
from typing import Any

import requests

from .base import BaseMetricConnector, ConnectorConfig, FetchResult
from ..storage.models import Observation

class FREDConnector(BaseMetricConnector):
    """Connector for FRED API."""

    SOURCE_NAME = "fred"
    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("FRED_API_KEY")
        if not self.api_key:
            raise ValueError("FRED_API_KEY required. Get one at https://fred.stlouisfed.org/docs/api/api_key.html")

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

    def normalize(self, config: ConnectorConfig, raw_data: list[Any]) -> list[Observation]:
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
```

**Acceptance Criteria:**
- Handles missing API key gracefully
- Skips FRED's "." missing value markers
- Applies multiplier for unit conversion (e.g., basis points)
- Health check uses a stable series
- Timeout prevents hanging on slow responses

---

### Agent 6: ECB Connector

**Task:** Implement ECB SDMX API connector for Eurozone data.

**API Reference:**
- Base URL: `https://data-api.ecb.europa.eu/service/`
- Auth: None required (public)
- Format: SDMX-JSON
- Docs: https://data.ecb.europa.eu/help/api/data

**Deliverables:**

**src/connectors/ecb.py:**
```python
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

    def normalize(self, config: ConnectorConfig, raw_data: Any) -> list[Observation]:
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
        - 2024-01 → 2024-01-01
        - 2024-Q1 → 2024-01-01
        - 2024 → 2024-01-01
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
```

**Acceptance Criteria:**
- Parses SDMX-JSON structure correctly
- Handles monthly, quarterly, and annual time periods
- No API key required
- Graceful handling of malformed responses

---

### Agent 7: World Bank Connector

**Task:** Implement World Bank API connector for global indicators.

**API Reference:**
- Base URL: `https://api.worldbank.org/v2/`
- Auth: None required
- Format: JSON (add `?format=json`)
- Docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392

**Deliverables:**

**src/connectors/worldbank.py:**
```python
"""
World Bank Indicators API connector.

Handles:
- Cross-country economic indicators
- GDP, population, poverty metrics
- Development indicators

API Notes:
- No authentication required
- Add ?format=json for JSON responses
- Returns array: [metadata, data]
"""
from datetime import datetime
from typing import Any

import requests

from .base import BaseMetricConnector, ConnectorConfig, FetchResult
from ..storage.models import Observation

class WorldBankConnector(BaseMetricConnector):
    """Connector for World Bank Indicators API."""

    SOURCE_NAME = "worldbank"
    BASE_URL = "https://api.worldbank.org/v2"

    def fetch(self, config: ConnectorConfig) -> FetchResult:
        """
        Fetch indicator data from World Bank.

        Args:
            config: Must include indicator and country

        Returns:
            FetchResult with indicator observations
        """
        if not config.indicator:
            return FetchResult(
                success=False,
                data=[],
                error="indicator required for World Bank connector",
                source=self.SOURCE_NAME
            )

        country = config.country or "WLD"  # Default to World aggregate

        url = f"{self.BASE_URL}/country/{country}/indicator/{config.indicator}"
        params = {
            "format": "json",
            "per_page": 100,
            "mrv": 50,  # Most recent values
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # World Bank returns [metadata, data_array]
            if not isinstance(data, list) or len(data) < 2:
                return FetchResult(
                    success=False,
                    data=[],
                    error="Unexpected World Bank response format",
                    source=self.SOURCE_NAME
                )

            return FetchResult(
                success=True,
                data=data[1] or [],  # data[1] can be None
                source=self.SOURCE_NAME
            )

        except requests.RequestException as e:
            return FetchResult(
                success=False,
                data=[],
                error=str(e),
                source=self.SOURCE_NAME
            )

    def normalize(self, config: ConnectorConfig, raw_data: list[Any]) -> list[Observation]:
        """
        Convert World Bank data to observations.

        World Bank format:
        {
            "indicator": {"id": "...", "value": "..."},
            "country": {"id": "...", "value": "..."},
            "date": "2023",
            "value": 123.45
        }
        """
        observations = []

        for item in raw_data:
            if item is None:
                continue

            value = item.get("value")
            if value is None:
                continue

            # World Bank dates are usually just years
            date_str = item.get("date", "")
            if len(date_str) == 4:
                obs_date = f"{date_str}-01-01"
            else:
                obs_date = date_str

            obs = Observation(
                metric_id=config.metric_id,
                obs_date=obs_date,
                value=round(float(value) * config.multiplier, config.decimals),
                unit=config.unit,
                source=self.SOURCE_NAME,
                retrieved_at=datetime.now()
            )
            observations.append(obs)

        # Sort by date descending
        observations.sort(key=lambda x: x.obs_date, reverse=True)
        return observations

    def health_check(self) -> bool:
        """Check World Bank API availability."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/country/WLD/indicator/NY.GDP.MKTP.CD",
                params={"format": "json", "per_page": 1},
                timeout=10
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
```

**Acceptance Criteria:**
- Handles `[metadata, data]` response structure
- Skips null values gracefully
- Supports country filtering
- Works with annual data (World Bank's primary frequency)

---

### Agent 8: Hacker News Connector

**Task:** Implement HN Firebase API and Algolia Search connectors.

**API References:**
- Firebase: `https://hacker-news.firebaseio.com/v0/`
- Algolia: `https://hn.algolia.com/api/v1/`
- No auth required for either

**Deliverables:**

**src/connectors/hackernews.py:**
```python
"""
Hacker News connectors (Firebase official API + Algolia search).

Firebase API:
- Official HN API
- Real-time item data
- Top/best/new story lists
- No rate limit (be polite)

Algolia API:
- Full-text search
- Filtering by date, tags
- Faster for bulk retrieval
"""
from datetime import datetime
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from .base import BaseFeedConnector, FeedConfig, FetchResult
from ..storage.models import Story

class HNFirebaseConnector(BaseFeedConnector):
    """Connector for official HN Firebase API."""

    SOURCE_NAME = "hn_firebase"
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def fetch(self, config: FeedConfig) -> FetchResult:
        """
        Fetch stories from HN Firebase.

        Args:
            config: Must include endpoint (topstories, beststories, newstories)

        Returns:
            FetchResult with story items
        """
        endpoint = config.endpoint or "topstories"
        limit = config.limit or 20

        try:
            # Get story IDs
            ids_url = f"{self.BASE_URL}/{endpoint}.json"
            response = requests.get(ids_url, timeout=15)
            response.raise_for_status()
            story_ids = response.json()[:limit]

            # Fetch individual stories in parallel
            stories = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {
                    executor.submit(self._fetch_item, sid): sid
                    for sid in story_ids
                }
                for future in as_completed(futures):
                    try:
                        item = future.result()
                        if item and item.get("type") == "story":
                            stories.append(item)
                    except Exception:
                        continue

            return FetchResult(
                success=True,
                data=stories,
                source=self.SOURCE_NAME
            )

        except requests.RequestException as e:
            return FetchResult(
                success=False,
                data=[],
                error=str(e),
                source=self.SOURCE_NAME
            )

    def _fetch_item(self, item_id: int) -> dict | None:
        """Fetch a single HN item."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/item/{item_id}.json",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def normalize(self, config: FeedConfig, raw_data: list[Any]) -> list[Story]:
        """Convert HN items to Story objects."""
        stories = []

        for item in raw_data:
            if not item:
                continue

            # Parse Unix timestamp
            posted_at = None
            if item.get("time"):
                posted_at = datetime.fromtimestamp(item["time"])

            story = Story(
                id=item["id"],
                title=item.get("title", ""),
                url=item.get("url"),
                score=item.get("score", 0),
                comments=item.get("descendants", 0),
                author=item.get("by", ""),
                posted_at=posted_at,
                source=self.SOURCE_NAME,
                feed_id=config.id,
                retrieved_at=datetime.now()
            )
            stories.append(story)

        return stories


class HNAlgoliaConnector(BaseFeedConnector):
    """Connector for HN Algolia Search API."""

    SOURCE_NAME = "hn_algolia"
    BASE_URL = "https://hn.algolia.com/api/v1"

    def fetch(self, config: FeedConfig) -> FetchResult:
        """
        Search HN via Algolia.

        Args:
            config: Should include query, optional tags, time_range

        Returns:
            FetchResult with search hits
        """
        if not config.query:
            return FetchResult(
                success=False,
                data=[],
                error="query required for Algolia search",
                source=self.SOURCE_NAME
            )

        params = {
            "query": config.query,
            "hitsPerPage": config.limit or 20,
        }

        # Add tags filter (story, comment, etc.)
        if config.tags:
            params["tags"] = config.tags

        # Add time filter
        if config.time_range:
            import time
            now = int(time.time())
            ranges = {
                "day": 86400,
                "week": 604800,
                "month": 2592000,
                "year": 31536000,
            }
            if config.time_range in ranges:
                params["numericFilters"] = f"created_at_i>{now - ranges[config.time_range]}"

        try:
            # Use search_by_date for recent content
            url = f"{self.BASE_URL}/search_by_date" if config.time_range else f"{self.BASE_URL}/search"
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            return FetchResult(
                success=True,
                data=data.get("hits", []),
                source=self.SOURCE_NAME
            )

        except requests.RequestException as e:
            return FetchResult(
                success=False,
                data=[],
                error=str(e),
                source=self.SOURCE_NAME
            )

    def normalize(self, config: FeedConfig, raw_data: list[Any]) -> list[Story]:
        """Convert Algolia hits to Story objects."""
        stories = []

        for hit in raw_data:
            # Parse ISO timestamp
            posted_at = None
            if hit.get("created_at"):
                try:
                    posted_at = datetime.fromisoformat(
                        hit["created_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            story = Story(
                id=int(hit.get("objectID", 0)),
                title=hit.get("title", ""),
                url=hit.get("url"),
                score=hit.get("points", 0),
                comments=hit.get("num_comments", 0),
                author=hit.get("author", ""),
                posted_at=posted_at,
                source=self.SOURCE_NAME,
                feed_id=config.id,
                retrieved_at=datetime.now()
            )
            stories.append(story)

        return stories
```

**Acceptance Criteria:**
- Firebase uses parallel fetching for speed
- Algolia supports query, tags, and time range filtering
- Both handle Unix and ISO timestamps
- Graceful handling of missing fields

---

### Agent 9: Transforms Module

**Task:** Implement data transformations (YoY, QoQ, moving averages).

**Deliverables:**

**src/transforms/calculations.py:**
```python
"""
Data transformations for time series observations.

Supports:
- Year-over-year (YoY) percent change
- Quarter-over-quarter (QoQ) percent change
- Period-over-period change
- Moving averages
- Sparkline data preparation
"""
from datetime import datetime
from typing import Optional

from ..storage.models import Observation

def calculate_yoy_percent(observations: list[Observation]) -> list[Observation]:
    """
    Calculate year-over-year percent change.

    For each observation, finds the value from ~12 months ago
    and computes: ((current - prior) / prior) * 100

    Args:
        observations: List sorted by date descending

    Returns:
        New list with YoY percent values
    """
    if len(observations) < 13:
        return []

    # Build date->value lookup
    date_values = {obs.obs_date: obs.value for obs in observations}

    yoy_obs = []
    for obs in observations:
        # Find observation from ~12 months ago
        try:
            current_date = datetime.strptime(obs.obs_date, "%Y-%m-%d")
            prior_date = current_date.replace(year=current_date.year - 1)
            prior_date_str = prior_date.strftime("%Y-%m-%d")

            if prior_date_str in date_values:
                prior_value = date_values[prior_date_str]
                if prior_value != 0:
                    yoy_value = ((obs.value - prior_value) / prior_value) * 100

                    yoy_obs.append(Observation(
                        metric_id=obs.metric_id,
                        obs_date=obs.obs_date,
                        value=round(yoy_value, 2),
                        unit="%",
                        source=obs.source,
                        retrieved_at=obs.retrieved_at
                    ))
        except (ValueError, AttributeError):
            continue

    return yoy_obs


def calculate_qoq_percent(observations: list[Observation]) -> list[Observation]:
    """
    Calculate quarter-over-quarter percent change.

    Args:
        observations: List sorted by date descending

    Returns:
        New list with QoQ percent values
    """
    if len(observations) < 5:
        return []

    date_values = {obs.obs_date: obs.value for obs in observations}

    qoq_obs = []
    for obs in observations:
        try:
            current_date = datetime.strptime(obs.obs_date, "%Y-%m-%d")
            # Go back 3 months
            month = current_date.month - 3
            year = current_date.year
            if month < 1:
                month += 12
                year -= 1
            prior_date = current_date.replace(year=year, month=month)
            prior_date_str = prior_date.strftime("%Y-%m-%d")

            if prior_date_str in date_values:
                prior_value = date_values[prior_date_str]
                if prior_value != 0:
                    qoq_value = ((obs.value - prior_value) / prior_value) * 100

                    qoq_obs.append(Observation(
                        metric_id=obs.metric_id,
                        obs_date=obs.obs_date,
                        value=round(qoq_value, 2),
                        unit="%",
                        source=obs.source,
                        retrieved_at=obs.retrieved_at
                    ))
        except (ValueError, AttributeError):
            continue

    return qoq_obs


def calculate_change(
    current: float,
    previous: float
) -> tuple[Optional[float], Optional[float]]:
    """
    Calculate absolute and percent change between two values.

    Returns:
        (absolute_change, percent_change) or (None, None) if invalid
    """
    if previous is None or previous == 0:
        return (current - previous if previous is not None else None, None)

    absolute = current - previous
    percent = (absolute / previous) * 100
    return (round(absolute, 4), round(percent, 2))


def prepare_sparkline_data(
    observations: list[Observation],
    points: int = 12
) -> list[float]:
    """
    Extract values for sparkline visualization.

    Args:
        observations: Sorted by date descending
        points: Number of data points for sparkline

    Returns:
        List of values in chronological order (oldest first)
    """
    # Take most recent N observations, reverse to chronological
    recent = observations[:points]
    return [obs.value for obs in reversed(recent)]


def generate_ascii_sparkline(values: list[float], width: int = 10) -> str:
    """
    Generate ASCII sparkline from values.

    Uses Unicode block characters: ▁▂▃▄▅▆▇█

    Args:
        values: List of numeric values
        width: Target character width

    Returns:
        String of block characters representing the trend
    """
    if not values:
        return ""

    blocks = " ▁▂▃▄▅▆▇█"

    # Normalize values to 0-8 range
    min_val = min(values)
    max_val = max(values)

    if max_val == min_val:
        return blocks[4] * min(len(values), width)

    # Sample if too many values
    if len(values) > width:
        step = len(values) / width
        values = [values[int(i * step)] for i in range(width)]

    sparkline = ""
    for v in values:
        normalized = (v - min_val) / (max_val - min_val)
        idx = int(normalized * 8)
        sparkline += blocks[idx]

    return sparkline
```

**Acceptance Criteria:**
- YoY handles monthly data (finds value 12 months prior)
- QoQ handles quarterly data (finds value 3 months prior)
- Sparkline generates valid Unicode block characters
- All functions handle edge cases (empty lists, division by zero)

---

### Agent 10: HTML Generator

**Task:** Implement static HTML dashboard generation with Jinja2.

**Deliverables:**

**src/generator/html.py:**
```python
"""
Static HTML dashboard generator.

Generates a single-page dense dashboard using Jinja2 templates.
Output is a self-contained HTML file suitable for GitHub Pages.
"""
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from ..storage.database import get_all_metric_meta, get_stories_by_feed, get_latest_observations
from ..transforms.calculations import prepare_sparkline_data, generate_ascii_sparkline

TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "docs"

def load_config() -> dict:
    """Load metric and feed configurations."""
    import yaml
    config_dir = Path(__file__).parent.parent.parent / "config"

    with open(config_dir / "metrics.yaml") as f:
        metrics_config = yaml.safe_load(f)

    with open(config_dir / "feeds.yaml") as f:
        feeds_config = yaml.safe_load(f)

    return {
        "metrics": metrics_config,
        "feeds": feeds_config
    }

def build_dashboard_context() -> dict[str, Any]:
    """
    Build template context from database.

    Returns:
        Dictionary with all data needed for dashboard template
    """
    config = load_config()

    # Get metric metadata with sparklines
    metrics = []
    for group in config["metrics"].get("groups", []):
        group_metrics = []
        for metric_id in group.get("metrics", []):
            # Get metadata
            all_meta = get_all_metric_meta()
            meta = next((m for m in all_meta if m["id"] == metric_id), None)

            if meta:
                # Generate sparkline
                observations = get_latest_observations(metric_id, limit=12)
                sparkline_values = prepare_sparkline_data(
                    [type('obj', (object,), o)() for o in observations],  # Convert dicts to objects
                    points=10
                )
                sparkline = generate_ascii_sparkline(sparkline_values)

                # Determine change direction
                change_class = ""
                if meta.get("change"):
                    change_class = "up" if meta["change"] > 0 else "down" if meta["change"] < 0 else ""

                group_metrics.append({
                    **meta,
                    "sparkline": sparkline,
                    "change_class": change_class,
                    "formatted_value": format_value(meta.get("last_value"), meta.get("unit")),
                    "formatted_change": format_change(meta.get("change"), meta.get("unit")),
                })

        metrics.append({
            "name": group["name"],
            "metrics": group_metrics
        })

    # Get stories by feed
    feeds = []
    for feed_config in config["feeds"].get("feeds", []):
        stories = get_stories_by_feed(feed_config["id"], limit=feed_config.get("limit", 20))
        feeds.append({
            "id": feed_config["id"],
            "name": feed_config["name"],
            "stories": stories
        })

    return {
        "title": "Bloomberg-Lite",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "metric_groups": metrics,
        "feeds": feeds,
        "primary_feed": config["feeds"].get("display", {}).get("primary_feed", "hn_top"),
    }

def format_value(value: float | None, unit: str | None) -> str:
    """Format a metric value with its unit."""
    if value is None:
        return "—"

    if unit == "%":
        return f"{value:.1f}%"
    elif unit == "bp":
        return f"{value:.0f}bp"
    elif unit and "$" in unit:
        return f"${value:,.2f}"
    elif unit == "index":
        return f"{value:.1f}"
    else:
        return f"{value:,.2f}"

def format_change(change: float | None, unit: str | None) -> str:
    """Format a change value with appropriate prefix."""
    if change is None:
        return ""

    prefix = "+" if change > 0 else ""

    if unit == "%":
        return f"{prefix}{change:.1f}pp"
    elif unit == "bp":
        return f"{prefix}{change:.0f}bp"
    else:
        return f"{prefix}{change:.2f}"

def generate_dashboard() -> Path:
    """
    Generate the static HTML dashboard.

    Returns:
        Path to generated index.html
    """
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=True
    )

    template = env.get_template("dashboard.html")
    context = build_dashboard_context()

    html = template.render(**context)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "index.html"
    output_path.write_text(html)

    return output_path

if __name__ == "__main__":
    path = generate_dashboard()
    print(f"Generated: {path}")
```

**templates/dashboard.html:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }} | {{ generated_at }}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&display=swap');

    *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

    :root {
      --bg: #0a0a0a;
      --panel: #111;
      --border: #222;
      --text: #e0e0e0;
      --muted: #666;
      --up: #22c55e;
      --down: #ef4444;
      --accent: #3b82f6;
    }

    body {
      font: 11px/1.4 'IBM Plex Mono', monospace;
      background: var(--bg);
      color: var(--text);
      padding: 8px;
    }

    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--border);
      margin-bottom: 8px;
    }

    h1 { font-size: 14px; font-weight: 500; color: var(--accent); }
    .timestamp { color: var(--muted); font-size: 10px; }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 8px;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--border);
      padding: 8px;
    }

    .panel-title {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--muted);
      border-bottom: 1px solid var(--border);
      padding-bottom: 4px;
      margin-bottom: 8px;
    }

    .metric {
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 8px;
      padding: 4px 0;
      border-bottom: 1px solid var(--border);
      align-items: center;
    }

    .metric:last-child { border-bottom: none; }

    .metric-name { color: var(--muted); font-size: 10px; }
    .metric-value { font-weight: 500; text-align: right; }
    .metric-change { font-size: 10px; text-align: right; min-width: 50px; }
    .metric-change.up { color: var(--up); }
    .metric-change.down { color: var(--down); }

    .sparkline {
      font-size: 10px;
      color: var(--accent);
      letter-spacing: -1px;
    }

    .stories { grid-column: 1 / -1; }

    .story {
      display: grid;
      grid-template-columns: 50px 1fr;
      gap: 8px;
      padding: 4px 0;
      border-bottom: 1px solid var(--border);
    }

    .story:last-child { border-bottom: none; }

    .story-score {
      color: var(--accent);
      font-weight: 500;
      text-align: right;
    }

    .story-title a {
      color: var(--text);
      text-decoration: none;
    }

    .story-title a:hover { color: var(--accent); }

    .story-meta {
      color: var(--muted);
      font-size: 10px;
    }

    @media (max-width: 600px) {
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>

<header>
  <h1>{{ title }}</h1>
  <span class="timestamp">{{ generated_at }}</span>
</header>

<div class="grid">
  {% for group in metric_groups %}
  <section class="panel">
    <div class="panel-title">{{ group.name }}</div>
    {% for m in group.metrics %}
    <div class="metric">
      <div>
        <div class="metric-name">{{ m.name }}</div>
        <div class="sparkline">{{ m.sparkline }}</div>
      </div>
      <div class="metric-value">{{ m.formatted_value }}</div>
      <div class="metric-change {{ m.change_class }}">{{ m.formatted_change }}</div>
    </div>
    {% endfor %}
  </section>
  {% endfor %}

  <section class="panel stories">
    <div class="panel-title">Tech Discussion</div>
    {% for feed in feeds %}
    {% if feed.id == primary_feed %}
    {% for story in feed.stories[:15] %}
    <div class="story">
      <div class="story-score">▲ {{ story.score }}</div>
      <div>
        <div class="story-title">
          <a href="{{ story.url or 'https://news.ycombinator.com/item?id=' ~ story.id }}" target="_blank">
            {{ story.title }}
          </a>
        </div>
        <div class="story-meta">{{ story.comments }} comments · {{ story.author }}</div>
      </div>
    </div>
    {% endfor %}
    {% endif %}
    {% endfor %}
  </section>
</div>

</body>
</html>
```

**Acceptance Criteria:**
- Generates valid HTML5
- Responsive grid layout
- Dark theme by default
- Sparklines display correctly
- Stories link to HN or original URL
- Self-contained (no external dependencies except fonts)

---

### Agent 11: Main Orchestrator

**Task:** Implement the main entry point that coordinates all components.

**Deliverables:**

**src/main.py:**
```python
"""
Bloomberg-Lite main orchestrator.

Coordinates:
1. Loading configuration
2. Fetching data from all sources
3. Storing observations
4. Generating dashboard

Usage:
    python -m src.main              # Full update
    python -m src.main --fetch-only # Fetch data only
    python -m src.main --gen-only   # Generate dashboard only
"""
import argparse
import logging
from datetime import datetime
from pathlib import Path

import yaml

from .connectors.fred import FREDConnector
from .connectors.ecb import ECBConnector
from .connectors.worldbank import WorldBankConnector
from .connectors.hackernews import HNFirebaseConnector, HNAlgoliaConnector
from .connectors.base import ConnectorConfig, FeedConfig
from .storage.database import (
    init_db,
    upsert_observation,
    upsert_story,
    update_metric_meta,
    cleanup_old_stories,
    get_latest_observations
)
from .storage.models import MetricMeta
from .transforms.calculations import calculate_change
from .generator.html import generate_dashboard

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent / "config"

def load_configs() -> tuple[dict, dict]:
    """Load metric and feed configurations."""
    with open(CONFIG_DIR / "metrics.yaml") as f:
        metrics = yaml.safe_load(f)
    with open(CONFIG_DIR / "feeds.yaml") as f:
        feeds = yaml.safe_load(f)
    return metrics, feeds

def fetch_metrics(metrics_config: dict) -> None:
    """Fetch all configured metrics."""
    # Initialize connectors
    connectors = {
        "fred": FREDConnector(),
        "ecb": ECBConnector(),
        "worldbank": WorldBankConnector(),
    }

    for metric in metrics_config.get("metrics", []):
        source = metric.get("source")
        if source not in connectors:
            logger.warning(f"Unknown source '{source}' for metric {metric['id']}")
            continue

        connector = connectors[source]
        config = ConnectorConfig(
            metric_id=metric["id"],
            name=metric["name"],
            source=source,
            frequency=metric.get("frequency", "monthly"),
            unit=metric.get("unit"),
            decimals=metric.get("decimals", 2),
            transform=metric.get("transform"),
            multiplier=metric.get("multiplier", 1.0),
            series_id=metric.get("series_id"),
            dataflow=metric.get("dataflow"),
            series_key=metric.get("series_key"),
            indicator=metric.get("indicator"),
            country=metric.get("country"),
        )

        logger.info(f"Fetching {config.metric_id}...")

        try:
            observations = connector.fetch_and_normalize(config)

            for obs in observations:
                upsert_observation(obs)

            # Update metric metadata
            if observations:
                latest = observations[0]
                previous = observations[1] if len(observations) > 1 else None

                change, change_pct = calculate_change(
                    latest.value,
                    previous.value if previous else None
                )

                meta = MetricMeta(
                    id=config.metric_id,
                    name=config.name,
                    source=config.source,
                    frequency=config.frequency,
                    unit=config.unit,
                    last_value=latest.value,
                    last_updated=datetime.now(),
                    previous_value=previous.value if previous else None,
                    change=change,
                    change_percent=change_pct,
                )
                update_metric_meta(meta)

            logger.info(f"  ✓ {len(observations)} observations")

        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")

def fetch_feeds(feeds_config: dict) -> None:
    """Fetch all configured feeds."""
    connectors = {
        "hn_firebase": HNFirebaseConnector(),
        "hn_algolia": HNAlgoliaConnector(),
    }

    for feed in feeds_config.get("feeds", []):
        source = feed.get("source")
        if source not in connectors:
            logger.warning(f"Unknown source '{source}' for feed {feed['id']}")
            continue

        connector = connectors[source]
        config = FeedConfig(
            id=feed["id"],
            name=feed["name"],
            source=source,
            limit=feed.get("limit", 20),
            endpoint=feed.get("endpoint"),
            query=feed.get("query"),
            tags=feed.get("tags"),
            time_range=feed.get("time_range"),
        )

        logger.info(f"Fetching feed {config.id}...")

        try:
            stories = connector.fetch_and_normalize(config)

            for story in stories:
                upsert_story(story)

            logger.info(f"  ✓ {len(stories)} stories")

        except Exception as e:
            logger.error(f"  ✗ Failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Bloomberg-Lite dashboard updater")
    parser.add_argument("--fetch-only", action="store_true", help="Only fetch data")
    parser.add_argument("--gen-only", action="store_true", help="Only generate dashboard")
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("Bloomberg-Lite Update")
    logger.info("=" * 50)

    # Initialize database
    init_db()

    # Load configs
    metrics_config, feeds_config = load_configs()

    if not args.gen_only:
        # Fetch metrics
        logger.info("\n📊 Fetching metrics...")
        fetch_metrics(metrics_config)

        # Fetch feeds
        logger.info("\n📰 Fetching feeds...")
        fetch_feeds(feeds_config)

        # Cleanup old stories
        deleted = cleanup_old_stories(days=7)
        if deleted:
            logger.info(f"\n🧹 Cleaned up {deleted} old stories")

    if not args.fetch_only:
        # Generate dashboard
        logger.info("\n🎨 Generating dashboard...")
        output = generate_dashboard()
        logger.info(f"  ✓ Generated: {output}")

    logger.info("\n✅ Done!")

if __name__ == "__main__":
    main()
```

**Acceptance Criteria:**
- Handles all CLI flags correctly
- Logs progress clearly
- Continues on individual source failures
- Updates metadata after fetching
- Cleans up old data

---

### Agent 12: GitHub Actions Workflow

**Task:** Create the scheduled workflow for automated updates.

**Deliverables:**

**.github/workflows/update.yaml:**
```yaml
name: Update Dashboard

on:
  # Run every 6 hours
  schedule:
    - cron: '0 */6 * * *'

  # Allow manual trigger
  workflow_dispatch:

  # Run on push to main (for testing)
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'config/**'
      - 'templates/**'

jobs:
  update:
    runs-on: ubuntu-latest

    permissions:
      contents: write
      pages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .

      - name: Restore database cache
        uses: actions/cache@v4
        with:
          path: data/bloomberg_lite.db
          key: db-${{ github.run_number }}
          restore-keys: |
            db-

      - name: Fetch data and generate dashboard
        env:
          FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
        run: python -m src.main

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
          force_orphan: true
          commit_message: 'Update dashboard'

  health-check:
    runs-on: ubuntu-latest
    needs: update

    steps:
      - name: Check dashboard is accessible
        run: |
          # Wait for pages deployment
          sleep 30

          # Get GitHub Pages URL
          PAGES_URL="https://${{ github.repository_owner }}.github.io/${{ github.event.repository.name }}/"

          # Check response
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$PAGES_URL")

          if [ "$STATUS" -eq 200 ]; then
            echo "✅ Dashboard accessible at $PAGES_URL"
          else
            echo "⚠️ Dashboard returned status $STATUS"
            exit 1
          fi
```

**Acceptance Criteria:**
- Runs on schedule (every 6 hours)
- Supports manual trigger
- Caches database between runs
- Deploys to GitHub Pages
- Health check verifies deployment

---

### Agent 13: Testing Suite

**Task:** Implement unit tests for all components.

**Deliverables:**

**tests/test_connectors.py:**
```python
"""Tests for data connectors."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.connectors.fred import FREDConnector
from src.connectors.ecb import ECBConnector
from src.connectors.hackernews import HNFirebaseConnector, HNAlgoliaConnector
from src.connectors.base import ConnectorConfig, FeedConfig

class TestFREDConnector:
    """Tests for FRED API connector."""

    @pytest.fixture
    def connector(self):
        return FREDConnector(api_key="test_key")

    @pytest.fixture
    def config(self):
        return ConnectorConfig(
            metric_id="test.metric",
            name="Test Metric",
            source="fred",
            frequency="monthly",
            series_id="TEST123",
            unit="%",
            decimals=2,
            multiplier=1.0
        )

    def test_fetch_success(self, connector, config):
        """Test successful FRED fetch."""
        mock_response = {
            "observations": [
                {"date": "2024-01-01", "value": "5.25"},
                {"date": "2023-12-01", "value": "5.33"},
            ]
        }

        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = MagicMock()

            result = connector.fetch(config)

            assert result.success
            assert len(result.data) == 2

    def test_normalize_skips_missing(self, connector, config):
        """Test that normalization skips missing values."""
        raw_data = [
            {"date": "2024-01-01", "value": "5.25"},
            {"date": "2023-12-01", "value": "."},  # Missing
            {"date": "2023-11-01", "value": "5.00"},
        ]

        observations = connector.normalize(config, raw_data)

        assert len(observations) == 2
        assert observations[0].value == 5.25
        assert observations[1].value == 5.00


class TestECBConnector:
    """Tests for ECB SDMX connector."""

    @pytest.fixture
    def connector(self):
        return ECBConnector()

    def test_parse_time_period_monthly(self, connector):
        """Test monthly time period parsing."""
        assert connector._parse_time_period("2024-01") == "2024-01-01"

    def test_parse_time_period_quarterly(self, connector):
        """Test quarterly time period parsing."""
        assert connector._parse_time_period("2024-Q1") == "2024-01-01"
        assert connector._parse_time_period("2024-Q2") == "2024-04-01"
        assert connector._parse_time_period("2024-Q3") == "2024-07-01"
        assert connector._parse_time_period("2024-Q4") == "2024-10-01"

    def test_parse_time_period_annual(self, connector):
        """Test annual time period parsing."""
        assert connector._parse_time_period("2024") == "2024-01-01"


class TestHNConnectors:
    """Tests for Hacker News connectors."""

    def test_firebase_normalize(self):
        """Test Firebase story normalization."""
        connector = HNFirebaseConnector()
        config = FeedConfig(id="test", name="Test", source="hn_firebase")

        raw_data = [{
            "id": 12345,
            "title": "Test Story",
            "url": "https://example.com",
            "score": 100,
            "descendants": 50,
            "by": "testuser",
            "time": 1704067200,  # 2024-01-01
            "type": "story"
        }]

        stories = connector.normalize(config, raw_data)

        assert len(stories) == 1
        assert stories[0].id == 12345
        assert stories[0].title == "Test Story"
        assert stories[0].score == 100
```

**tests/test_transforms.py:**
```python
"""Tests for data transformations."""
import pytest
from datetime import datetime

from src.transforms.calculations import (
    calculate_change,
    generate_ascii_sparkline,
    prepare_sparkline_data
)
from src.storage.models import Observation

class TestCalculateChange:
    """Tests for change calculations."""

    def test_positive_change(self):
        """Test positive change calculation."""
        abs_change, pct_change = calculate_change(110, 100)
        assert abs_change == 10
        assert pct_change == 10.0

    def test_negative_change(self):
        """Test negative change calculation."""
        abs_change, pct_change = calculate_change(90, 100)
        assert abs_change == -10
        assert pct_change == -10.0

    def test_zero_previous(self):
        """Test division by zero handling."""
        abs_change, pct_change = calculate_change(100, 0)
        assert abs_change == 100
        assert pct_change is None

    def test_none_previous(self):
        """Test None previous value."""
        abs_change, pct_change = calculate_change(100, None)
        assert abs_change is None
        assert pct_change is None


class TestSparklines:
    """Tests for sparkline generation."""

    def test_generate_sparkline(self):
        """Test ASCII sparkline generation."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        sparkline = generate_ascii_sparkline(values)

        assert len(sparkline) == 10
        assert sparkline[0] == '▁'  # Lowest
        assert sparkline[-1] == '█'  # Highest

    def test_sparkline_flat(self):
        """Test sparkline with constant values."""
        values = [5, 5, 5, 5, 5]
        sparkline = generate_ascii_sparkline(values)

        assert all(c == '▄' for c in sparkline)  # Middle block

    def test_sparkline_empty(self):
        """Test sparkline with empty input."""
        sparkline = generate_ascii_sparkline([])
        assert sparkline == ""
```

**Acceptance Criteria:**
- All connectors have fetch and normalize tests
- Transforms have edge case coverage
- Tests run without network access (mocked)
- `pytest` passes with no warnings

---

## Implementation Order

Execute agents in this dependency order:

```
Phase 1 (Parallel):
├── Agent 1: Project Scaffolding
├── Agent 2: Configuration Schema
└── Agent 4: Base Connector Interface

Phase 2 (Parallel, after Phase 1):
├── Agent 3: Database Layer
├── Agent 5: FRED Connector
├── Agent 6: ECB Connector
├── Agent 7: World Bank Connector
└── Agent 8: Hacker News Connector

Phase 3 (Sequential, after Phase 2):
├── Agent 9: Transforms Module
├── Agent 10: HTML Generator
└── Agent 11: Main Orchestrator

Phase 4 (Parallel, after Phase 3):
├── Agent 12: GitHub Actions
└── Agent 13: Testing Suite
```

---

## Environment Variables

```bash
# Required
FRED_API_KEY=your_fred_api_key_here

# Optional (for future expansion)
# BEA_API_KEY=...
# BLS_API_KEY=...
```

---

## Success Criteria

The project is complete when:

1. **Data Pipeline**
   - [ ] FRED connector fetches US data correctly
   - [ ] ECB connector fetches Eurozone data correctly
   - [ ] World Bank connector fetches global data correctly
   - [ ] HN connectors fetch stories correctly
   - [ ] All data stored in SQLite with proper deduplication

2. **Dashboard**
   - [ ] Static HTML generates successfully
   - [ ] All metric groups display with sparklines
   - [ ] Stories display with scores and metadata
   - [ ] Responsive on mobile devices

3. **Automation**
   - [ ] GitHub Actions runs on schedule
   - [ ] Database persists between runs
   - [ ] Dashboard deploys to GitHub Pages
   - [ ] Health check verifies deployment

4. **Quality**
   - [ ] All tests pass
   - [ ] No hardcoded secrets
   - [ ] Graceful error handling
   - [ ] Clear logging output

---

## Extension Points

Future enhancements (not in v1 scope):

- **Additional sources**: BLS, BEA, OECD, BIS, IMF
- **Alerts**: Email when metrics cross thresholds
- **Historical charts**: Interactive Plotly/Chart.js visualizations
- **Search**: Full-text search across stored data
- **Mobile app**: PWA wrapper for the static site
- **RSS feed**: Generate RSS from metric updates
