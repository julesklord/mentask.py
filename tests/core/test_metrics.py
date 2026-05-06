from unittest.mock import patch

import pytest

from mentask.core.metrics import TokenTracker


@pytest.fixture
def clean_tracker():
    return TokenTracker(model_name="gemini-2.0-flash")


def test_tracker_initialization(clean_tracker):
    assert clean_tracker.total_prompt_tokens == 0
    assert clean_tracker.total_candidate_tokens == 0


def test_add_usage(clean_tracker):
    clean_tracker.add_usage(100, 50)
    assert clean_tracker.total_prompt_tokens == 100
    assert clean_tracker.total_candidate_tokens == 50

    clean_tracker.add_usage(200, 100)
    assert clean_tracker.total_prompt_tokens == 300
    assert clean_tracker.total_candidate_tokens == 150


def test_metrics_summary(clean_tracker):
    clean_tracker.add_usage(100, 50)
    summary = clean_tracker.get_summary()

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


def test_total_tokens(clean_tracker):
    """Verifies that total_tokens returns the sum of prompt and candidate tokens."""
    tracker = clean_tracker
    assert tracker.total_tokens == 0

    tracker.add_usage(100, 50)
    assert tracker.total_tokens == 150

    tracker.add_usage(200, 100)
    assert tracker.total_tokens == 450
