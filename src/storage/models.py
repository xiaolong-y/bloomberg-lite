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
