"""Pytest plugin that blocks all socket connections during test runs.

Provides a credential-free CI gate: proves that CI makes zero live network calls
when tests are run with ``--block-network``. Works regardless of HTTP library
(requests, httpx, aiohttp, websockets) because it patches at the socket level.

Usage:
    pytest --block-network                     # blocks all socket connections
    CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true pytest -m "not sandbox" --block-network

Registration:
    In any conftest.py that should enforce network blocking for all tests in that directory,
    add the following at the top (outside any function):

        pytest_plugins = ["unified_trading_pm.scripts.dev.network_block_plugin"]

    Or copy/import from network_block_conftest.py which shows the activation pattern.

Opt-out:
    Individual tests that legitimately make network calls (e.g. integration tests that
    require a running emulator) can be opted out using the marker:

        @pytest.mark.allow_network
        def test_connects_to_emulator() -> None:
            ...

    A WARNING is logged for each opted-out test so that the total exemption count
    is visible in CI logs.
"""

from __future__ import annotations

import logging
import socket
from collections.abc import Generator
from typing import Final
from unittest.mock import patch

import pytest

logger = logging.getLogger(__name__)

_MARKER_NAME: Final[str] = "allow_network"
_FLAG_NAME: Final[str] = "--block-network"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the --block-network CLI flag."""
    parser.addoption(
        _FLAG_NAME,
        action="store_true",
        default=False,
        help=(
            "Block all socket connections during the test run. "
            "Tests marked with @pytest.mark.allow_network are exempted. "
            "Usage: pytest --block-network"
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register the allow_network marker so it does not produce PytestUnknownMarkWarning."""
    config.addinivalue_line(
        "markers",
        f"{_MARKER_NAME}: exempt this test from --block-network socket blocking",
    )


@pytest.fixture(autouse=True)
def _enforce_network_block(request: pytest.FixtureRequest) -> Generator[None]:
    """Block all socket.socket connections when --block-network is active.

    Skips blocking for tests decorated with ``@pytest.mark.allow_network``.
    """
    if not request.config.getoption(_FLAG_NAME, default=False):
        # --block-network not active; passthrough
        yield
        return

    if request.node.get_closest_marker(_MARKER_NAME) is not None:
        logger.warning(
            "network_block_plugin: test %r is opted out via @%s -- socket connections allowed",
            request.node.nodeid,
            _MARKER_NAME,
        )
        yield
        return

    def _blocked_connect(self: socket.socket, address: tuple[str, int] | str) -> None:
        raise RuntimeError(
            f"network_block_plugin: test {request.node.nodeid!r} attempted a live socket "
            f"connection to {address!r}. "
            "Use a mock, VCR cassette, or local emulator instead. "
            f"To exempt this test, add @pytest.mark.{_MARKER_NAME}."
        )

    with patch.object(socket.socket, "connect", _blocked_connect):
        yield
