import pytest

from askgem.cli.dashboard import AskGemDashboard


def test_dashboard_stub_raises_clear_deprecation_error():
    with pytest.raises(RuntimeError, match="has been removed"):
        AskGemDashboard()
