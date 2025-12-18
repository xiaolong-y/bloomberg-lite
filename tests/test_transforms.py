"""
Tests for data transformation calculations.

Tests cover:
- Year-over-year percent change
- Quarter-over-quarter percent change
- Absolute and percent change calculations
- ASCII sparkline generation
- Edge cases (empty lists, division by zero, etc.)
"""
import pytest
from datetime import datetime

from src.transforms.calculations import (
    calculate_yoy_percent,
    calculate_qoq_percent,
    calculate_change,
    prepare_sparkline_data,
    generate_ascii_sparkline,
)
from src.storage.models import Observation


def make_observation(metric_id: str, date: str, value: float) -> Observation:
    """Helper to create Observation objects for testing."""
    return Observation(
        metric_id=metric_id,
        obs_date=date,
        value=value,
        unit="%",
        source="test",
        retrieved_at=datetime.now()
    )


class TestCalculateYoYPercent:
    """Tests for year-over-year percent change calculation."""

    def test_calculate_yoy_percent_basic(self):
        """Test basic YoY calculation with matching dates."""
        observations = [
            make_observation("test", "2024-06-01", 110.0),
            make_observation("test", "2024-05-01", 108.0),
            make_observation("test", "2024-04-01", 105.0),
            make_observation("test", "2024-03-01", 103.0),
            make_observation("test", "2024-02-01", 102.0),
            make_observation("test", "2024-01-01", 101.0),
            make_observation("test", "2023-12-01", 100.0),
            make_observation("test", "2023-11-01", 99.0),
            make_observation("test", "2023-10-01", 98.0),
            make_observation("test", "2023-09-01", 97.0),
            make_observation("test", "2023-08-01", 96.0),
            make_observation("test", "2023-07-01", 95.0),
            make_observation("test", "2023-06-01", 100.0),  # 12 months prior
        ]

        yoy = calculate_yoy_percent(observations)

        assert len(yoy) >= 1
        # 2024-06-01 vs 2023-06-01: (110 - 100) / 100 * 100 = 10%
        assert yoy[0].value == 10.0
        assert yoy[0].unit == "%"

    def test_calculate_yoy_percent_insufficient_data(self):
        """Test YoY returns empty when insufficient observations."""
        observations = [
            make_observation("test", "2024-06-01", 110.0),
            make_observation("test", "2024-05-01", 108.0),
        ]

        yoy = calculate_yoy_percent(observations)

        assert yoy == []

    def test_calculate_yoy_percent_empty_list(self):
        """Test YoY handles empty input."""
        assert calculate_yoy_percent([]) == []

    def test_calculate_yoy_percent_no_matching_dates(self):
        """Test YoY when no dates match 12 months apart."""
        # All dates in same year, no matching prior year dates
        observations = [make_observation("test", f"2024-{i:02d}-01", 100.0 + i) for i in range(1, 14)]

        yoy = calculate_yoy_percent(observations)

        assert yoy == []

    def test_calculate_yoy_percent_preserves_metric_id(self):
        """Test YoY observations retain original metric_id."""
        observations = [
            make_observation("gdp_growth", f"2024-{i:02d}-01", 100.0 + i)
            for i in range(1, 13)
        ] + [
            make_observation("gdp_growth", f"2023-{i:02d}-01", 100.0)
            for i in range(1, 13)
        ]

        yoy = calculate_yoy_percent(observations)

        for obs in yoy:
            assert obs.metric_id == "gdp_growth"


class TestCalculateQoQPercent:
    """Tests for quarter-over-quarter percent change calculation."""

    def test_calculate_qoq_percent_basic(self):
        """Test basic QoQ calculation."""
        observations = [
            make_observation("test", "2024-07-01", 110.0),
            make_observation("test", "2024-04-01", 100.0),  # 3 months prior
            make_observation("test", "2024-01-01", 95.0),
            make_observation("test", "2023-10-01", 90.0),
            make_observation("test", "2023-07-01", 85.0),
        ]

        qoq = calculate_qoq_percent(observations)

        # 2024-07-01 vs 2024-04-01: (110 - 100) / 100 * 100 = 10%
        assert len(qoq) >= 1
        assert qoq[0].value == 10.0

    def test_calculate_qoq_percent_insufficient_data(self):
        """Test QoQ returns empty with insufficient data."""
        observations = [
            make_observation("test", "2024-07-01", 110.0),
            make_observation("test", "2024-04-01", 100.0),
        ]

        qoq = calculate_qoq_percent(observations)

        assert qoq == []

    def test_calculate_qoq_percent_empty_list(self):
        """Test QoQ handles empty input."""
        assert calculate_qoq_percent([]) == []

    def test_calculate_qoq_percent_cross_year_boundary(self):
        """Test QoQ calculation across year boundary."""
        observations = [
            make_observation("test", "2024-03-01", 110.0),
            make_observation("test", "2023-12-01", 100.0),  # 3 months prior, different year
            make_observation("test", "2023-09-01", 95.0),
            make_observation("test", "2023-06-01", 90.0),
            make_observation("test", "2023-03-01", 85.0),
        ]

        qoq = calculate_qoq_percent(observations)

        assert len(qoq) >= 1
        # 2024-03-01 vs 2023-12-01: (110 - 100) / 100 * 100 = 10%
        assert qoq[0].value == 10.0


class TestCalculateChange:
    """Tests for absolute and percent change calculation."""

    def test_calculate_change_positive(self):
        """Test positive change calculation."""
        absolute, percent = calculate_change(110.0, 100.0)

        assert absolute == 10.0
        assert percent == 10.0

    def test_calculate_change_negative(self):
        """Test negative change calculation."""
        absolute, percent = calculate_change(90.0, 100.0)

        assert absolute == -10.0
        assert percent == -10.0

    def test_calculate_change_zero_previous(self):
        """Test division by zero is handled."""
        absolute, percent = calculate_change(100.0, 0.0)

        assert absolute == 100.0
        assert percent is None

    def test_calculate_change_none_previous(self):
        """Test None previous value."""
        absolute, percent = calculate_change(100.0, None)

        assert absolute is None
        assert percent is None

    def test_calculate_change_no_change(self):
        """Test when values are equal."""
        absolute, percent = calculate_change(100.0, 100.0)

        assert absolute == 0.0
        assert percent == 0.0

    def test_calculate_change_rounding(self):
        """Test rounding behavior."""
        absolute, percent = calculate_change(1.0, 3.0)

        # absolute: -2.0, percent: -66.67%
        assert absolute == -2.0
        assert percent == -66.67

    def test_calculate_change_small_values(self):
        """Test with small decimal values."""
        absolute, percent = calculate_change(0.055, 0.050)

        assert absolute == pytest.approx(0.005, rel=1e-3)
        assert percent == 10.0


class TestGenerateAsciiSparkline:
    """Tests for ASCII sparkline generation."""

    def test_generate_ascii_sparkline_basic(self):
        """Test basic sparkline generation."""
        values = [1, 2, 3, 4, 5, 6, 7, 8]

        sparkline = generate_ascii_sparkline(values)

        assert len(sparkline) == 8
        # blocks = " ▁▂▃▄▅▆▇█", index 0 is space (lowest), index 8 is █ (highest)
        assert sparkline[0] == " "  # Lowest (normalized to 0 -> space)
        assert sparkline[-1] == "█"  # Highest

    def test_generate_ascii_sparkline_empty_list(self):
        """Test sparkline with empty input."""
        assert generate_ascii_sparkline([]) == ""

    def test_generate_ascii_sparkline_single_value(self):
        """Test sparkline with single value."""
        sparkline = generate_ascii_sparkline([50])

        assert len(sparkline) == 1
        assert sparkline == "▄"  # Middle block for constant

    def test_generate_ascii_sparkline_constant_values(self):
        """Test sparkline when all values are equal."""
        values = [100, 100, 100, 100]

        sparkline = generate_ascii_sparkline(values)

        # All same value should produce middle blocks
        assert sparkline == "▄▄▄▄"

    def test_generate_ascii_sparkline_with_width_limit(self):
        """Test sparkline respects width limit."""
        values = list(range(100))

        sparkline = generate_ascii_sparkline(values, width=10)

        assert len(sparkline) == 10

    def test_generate_ascii_sparkline_negative_values(self):
        """Test sparkline handles negative values."""
        values = [-10, -5, 0, 5, 10]

        sparkline = generate_ascii_sparkline(values)

        assert len(sparkline) == 5
        # blocks = " ▁▂▃▄▅▆▇█", index 0 is space (lowest), index 8 is █ (highest)
        assert sparkline[0] == " "  # -10 (lowest normalized to 0 -> space)
        assert sparkline[-1] == "█"  # 10 (highest)

    def test_generate_ascii_sparkline_float_values(self):
        """Test sparkline with float values."""
        values = [1.5, 2.7, 3.2, 4.8, 5.1]

        sparkline = generate_ascii_sparkline(values)

        assert len(sparkline) == 5
        assert all(c in " ▁▂▃▄▅▆▇█" for c in sparkline)


class TestPrepareSparklineData:
    """Tests for sparkline data preparation."""

    def test_prepare_sparkline_data_basic(self):
        """Test basic sparkline data preparation."""
        observations = [
            {"value": 10},
            {"value": 20},
            {"value": 30},
        ]

        data = prepare_sparkline_data(observations, points=3)

        # Should reverse to chronological order
        assert data == [30, 20, 10]

    def test_prepare_sparkline_data_limit_points(self):
        """Test sparkline limits to specified points."""
        observations = [{"value": i} for i in range(20)]

        data = prepare_sparkline_data(observations, points=5)

        assert len(data) == 5

    def test_prepare_sparkline_data_empty_list(self):
        """Test sparkline data with empty input."""
        assert prepare_sparkline_data([]) == []

    def test_prepare_sparkline_data_fewer_than_points(self):
        """Test when observations fewer than requested points."""
        observations = [{"value": 1}, {"value": 2}]

        data = prepare_sparkline_data(observations, points=10)

        assert len(data) == 2


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_yoy_with_invalid_date_format(self):
        """Test YoY handles invalid date formats gracefully."""
        observations = [
            Observation(
                metric_id="test",
                obs_date="invalid-date",
                value=100.0,
                source="test"
            )
        ] * 15

        # Should not raise, returns empty or skips invalid
        result = calculate_yoy_percent(observations)
        assert isinstance(result, list)

    def test_qoq_with_invalid_date_format(self):
        """Test QoQ handles invalid date formats gracefully."""
        observations = [
            Observation(
                metric_id="test",
                obs_date="2024/01/01",  # Wrong format
                value=100.0,
                source="test"
            )
        ] * 10

        result = calculate_qoq_percent(observations)
        assert isinstance(result, list)

    def test_sparkline_with_inf_values(self):
        """Test sparkline raises on infinity values."""
        values = [1, 2, float("inf"), 4, 5]

        # Function doesn't handle inf - raises ValueError
        with pytest.raises(ValueError):
            generate_ascii_sparkline(values)

    def test_sparkline_with_nan_values(self):
        """Test sparkline raises on NaN values."""
        values = [1, 2, float("nan"), 4, 5]

        # Function doesn't handle NaN - raises ValueError
        with pytest.raises(ValueError):
            generate_ascii_sparkline(values)

    def test_change_with_very_large_numbers(self):
        """Test change calculation with large numbers."""
        absolute, percent = calculate_change(1e15, 1e14)

        assert absolute == 9e14
        assert percent == 900.0

    def test_change_with_very_small_numbers(self):
        """Test change calculation with very small numbers."""
        absolute, percent = calculate_change(1e-10, 1e-11)

        assert absolute is not None
        assert percent == 900.0


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_yoy_workflow(self):
        """Test complete YoY calculation workflow."""
        # Create 24 months of data
        observations = []
        for year in [2023, 2024]:
            for month in range(1, 13):
                value = 100 + (year - 2023) * 12 + month
                obs = make_observation(
                    "gdp",
                    f"{year}-{month:02d}-01",
                    value
                )
                observations.append(obs)

        yoy = calculate_yoy_percent(observations)

        # Should have YoY values for 2024 months
        assert len(yoy) > 0
        # All YoY values should be positive (values increased)
        assert all(obs.value > 0 for obs in yoy)

    def test_sparkline_from_observations(self):
        """Test generating sparkline from observation data."""
        # Simulate observations sorted by date descending (most recent first)
        # Values go: [125, 120, 115, ...] representing newest to oldest
        raw_values = [125, 120, 115, 110, 105, 100, 98, 95, 92, 90]
        obs_dicts = [{"value": v} for v in raw_values]

        # prepare_sparkline_data takes first N and reverses to chronological
        # So [125, 120, 115, 110, 105, 100, 98, 95, 92, 90] -> [90, 92, 95, 98, 100, 105, 110, 115, 120, 125]
        sparkline_data = prepare_sparkline_data(obs_dicts, points=10)

        # Generate sparkline
        sparkline = generate_ascii_sparkline(sparkline_data, width=10)

        assert len(sparkline) == 10
        # After reversal, data is in ascending order (upward trend)
        # First value (90) is lowest -> space, last value (125) is highest -> █
        assert sparkline[-1] == "█"
