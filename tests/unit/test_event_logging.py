"""Unit tests for event logging — PM is a devops repo; event logging is for batch/live services."""

import pytest


def test_event_logging_pm_exempt() -> None:
    """PM is a devops repo; event logging (log_event, setup_events) is for batch/live services only."""
    # reason: unified-trading-pm does not use log_event or setup_events
    pytest.skip("unified-trading-pm does not use event logging")
