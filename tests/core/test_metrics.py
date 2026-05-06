from unittest.mock import patch

import pytest

from mentask.core.metrics import TokenTracker


@pytest.fixture
def clean_tracker(tmp_path):
    # Mock the log path to use a temp file
    log_file = tmp_path / "test_usage.json"
    with patch("mentask.core.metrics.get_config_path", return_value=str(log_file)):
        yield TokenTracker(model_name="gemini-2.0-flash")


def test_metrics_accumulation(clean_tracker):
    """Verifies that tokens and costs accumulate correctly."""
    tracker = clean_tracker
    tracker.add_usage(100, 50)

    assert tracker.total_prompt_tokens == 100
    assert tracker.total_candidate_tokens == 50
    # calculate_cost now requires arguments
    assert tracker.calculate_cost(100, 50) > 0

    tracker.add_usage(200, 100)
    assert tracker.total_prompt_tokens == 300
    assert tracker.total_candidate_tokens == 150


def test_metrics_pricing_difference(tmp_path):
    """Verifies that different models result in different costs."""
    log_file = tmp_path / "test_usage_pricing.json"
    with patch("mentask.core.metrics.get_config_path", return_value=str(log_file)):
        tracker_flash = TokenTracker(model_name="gemini-1.5-flash")
        tracker_pro = TokenTracker(model_name="gemini-1.5-pro")

        # Pro should be more expensive than Flash for the same usage
        cost_flash = tracker_flash.calculate_cost(1000, 1000)
        cost_pro = tracker_pro.calculate_cost(1000, 1000)
        assert cost_pro > cost_flash


def test_metrics_reset(clean_tracker):
    """Verifies that metrics can be reset to zero."""
    tracker = clean_tracker
    tracker.add_usage(100, 50)
    tracker.reset()

    assert tracker.total_prompt_tokens == 0
    assert tracker.calculate_cost(tracker.total_prompt_tokens, tracker.total_candidate_tokens) == 0.0


def test_metrics_summary(clean_tracker):
    """Verifies the formatted summary string."""
    tracker = clean_tracker
    tracker.add_usage(1000, 500)
    summary = tracker.get_summary()

    assert "Tokens:" in summary
    assert "Cost:" in summary


@patch("mentask.core.models_hub.hub.get_pricing")
def test_calculate_cost(mock_get_pricing, clean_tracker):
    """Verifies that calculate_cost works with hub pricing and falls back correctly."""
    tracker = clean_tracker

    # Scenario 1: Standard hub pricing
    mock_get_pricing.return_value = {"input": 1.0, "output": 2.0}

    # 1 million input tokens = $1.0
    # 2 million output tokens = $4.0
    # Total = $5.0
    cost = tracker.calculate_cost(1_000_000, 2_000_000)
    assert cost == 5.0
    mock_get_pricing.assert_called_with(tracker.model_name)

    # Scenario 2: Fallback to static PRICING_MAP when hub returns 0.0
    mock_get_pricing.return_value = {"input": 0.0, "output": 0.0}

    # "gemini-2.0-flash" is in PRICING_MAP with input_1m=0.10, output_1m=0.40
    # 1 million input tokens = $0.10
    # 2 million output tokens = $0.80
    # Total = $0.90
    cost = tracker.calculate_cost(1_000_000, 2_000_000)
    assert cost == 0.90

    # Scenario 3: Fallback to default when model is unknown and hub returns 0.0
    tracker_unknown = TokenTracker(model_name="unknown-model")

    # The default fallback in PRICING_MAP is "gemini-2.0-flash"
    # input_1m=0.10, output_1m=0.40
    cost_unknown = tracker_unknown.calculate_cost(1_000_000, 2_000_000)
    assert cost_unknown == 0.90
