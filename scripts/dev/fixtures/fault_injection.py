# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Fault injection fixtures for integration testing.

Provides FaultConfig, FaultInjectionTransport and preset scenario objects for
simulating network faults (timeouts, errors, rate-limits, latency) in tests.
"""
# SCHEMA_PROVENANCE_EXEMPT — PM-internal tooling model, not a domain schema

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass

import httpx


@dataclass
class FaultConfig:
    """Configuration for fault injection behaviour."""

    timeout_rate: float = 0.0
    error_rate: float = 0.0
    rate_limit_rate: float = 0.0
    latency_ms: int = 0
    enabled: bool = True

    def should_inject_timeout(self) -> bool:
        if not self.enabled:
            return False
        return random.random() < self.timeout_rate

    def should_inject_error(self) -> bool:
        if not self.enabled:
            return False
        return random.random() < self.error_rate

    def should_inject_rate_limit(self) -> bool:
        if not self.enabled:
            return False
        return random.random() < self.rate_limit_rate


class FaultInjectionTransport(httpx.AsyncBaseTransport):
    """httpx async transport that injects configurable faults."""

    def __init__(self, config: FaultConfig) -> None:
        self._config = config

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        if self._config.latency_ms > 0:
            await asyncio.sleep(self._config.latency_ms / 1000.0)

        if self._config.should_inject_timeout():
            raise httpx.TimeoutException("Injected timeout", request=request)

        if self._config.should_inject_rate_limit():
            return httpx.Response(429, text="Rate limited (injected)")

        if self._config.should_inject_error():
            return httpx.Response(500, text="Server error (injected)")

        return httpx.Response(200, text="OK")


def make_fault_transport(config: FaultConfig) -> FaultInjectionTransport:
    """Create a FaultInjectionTransport from the given FaultConfig."""
    return FaultInjectionTransport(config)


# ---------------------------------------------------------------------------
# Preset scenarios
# ---------------------------------------------------------------------------

TIMEOUT_SCENARIO = FaultConfig(timeout_rate=1.0, error_rate=0.0, rate_limit_rate=0.0)
RATE_LIMIT_SCENARIO = FaultConfig(timeout_rate=0.0, error_rate=0.0, rate_limit_rate=1.0)
CASCADE_SCENARIO = FaultConfig(timeout_rate=0.2, error_rate=0.8, rate_limit_rate=0.0)
HIGH_LATENCY_SCENARIO = FaultConfig(timeout_rate=0.0, error_rate=0.0, rate_limit_rate=0.0, latency_ms=2000)
FLAKY_SCENARIO = FaultConfig(timeout_rate=0.0, error_rate=0.5, rate_limit_rate=0.0, latency_ms=50)
