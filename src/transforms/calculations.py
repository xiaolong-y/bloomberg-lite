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
    Generate ASCII sparkline from values using block characters.

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

    min_val = min(values)
    max_val = max(values)

    if max_val == min_val:
        return blocks[4] * min(len(values), width)

    if len(values) > width:
        step = len(values) / width
        values = [values[int(i * step)] for i in range(width)]

    sparkline = ""
    for v in values:
        normalized = (v - min_val) / (max_val - min_val)
        idx = int(normalized * 8)
        sparkline += blocks[idx]

    return sparkline


def generate_braille_sparkline(values: list[float], width: int = 8) -> str:
    """
    Generate high-resolution sparkline using braille patterns.

    Each braille character encodes TWO data points (left and right columns),
    giving 2x the resolution of block characters. Each column has 5 height
    levels (0-4 dots).

    Braille dot positions:
        1 4
        2 5
        3 6
        7 8

    Args:
        values: List of numeric values
        width: Target character width (actual data points = width * 2)

    Returns:
        String of braille characters representing the trend
    """
    if not values:
        return ""

    # Braille encoding: each column can show 5 heights (0-4 dots from bottom)
    # Left column (dots 7,3,2,1 from bottom to top): values 64, 4, 2, 1
    # Right column (dots 8,6,5,4 from bottom to top): values 128, 32, 16, 8
    LEFT_HEIGHTS = [0, 64, 64+4, 64+4+2, 64+4+2+1]  # 0-4 dots
    RIGHT_HEIGHTS = [0, 128, 128+32, 128+32+16, 128+32+16+8]  # 0-4 dots
    BRAILLE_BASE = 0x2800

    min_val = min(values)
    max_val = max(values)

    # Handle flat line
    if max_val == min_val:
        mid = LEFT_HEIGHTS[2] + RIGHT_HEIGHTS[2]
        return chr(BRAILLE_BASE + mid) * width

    # Resample to fit width * 2 data points (2 per braille char)
    target_points = width * 2
    if len(values) != target_points:
        if len(values) > target_points:
            step = len(values) / target_points
            values = [values[int(i * step)] for i in range(target_points)]
        else:
            # Pad with last value if not enough data
            values = values + [values[-1]] * (target_points - len(values))

    # Normalize values to 0-4 range
    def normalize(v):
        n = (v - min_val) / (max_val - min_val)
        return int(n * 4)

    # Build braille string, 2 values per character
    sparkline = ""
    for i in range(0, len(values), 2):
        left_height = normalize(values[i])
        right_height = normalize(values[i + 1]) if i + 1 < len(values) else normalize(values[i])
        char_code = BRAILLE_BASE + LEFT_HEIGHTS[left_height] + RIGHT_HEIGHTS[right_height]
        sparkline += chr(char_code)

    return sparkline
