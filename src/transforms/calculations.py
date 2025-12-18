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
    observations: list[dict],
    points: int = 12
) -> list[float]:
    """
    Extract values for sparkline visualization.

    Args:
        observations: List of observation dicts sorted by date descending
        points: Number of data points for sparkline

    Returns:
        List of values in chronological order (oldest first)
    """
    # Take most recent N observations, reverse to chronological
    recent = observations[:points]
    return [obs["value"] for obs in reversed(recent)]


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
