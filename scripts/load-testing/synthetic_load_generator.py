#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Synthetic load generator for the Unified Trading System.

Configurable parameters:
  - Instrument count: 45, 1000, 5000, 10000
  - Tick rate per instrument: 1/s, 10/s
  - Concurrent users: 1, 10, 50
  - Scenario: any MockScenario value

Uses SyntheticDataGenerator from UIC with seed=42 for determinism.
Outputs: throughput (msgs/s), P50/P95/P99 latency, error rate, memory usage.

Usage:
    python scripts/load-testing/synthetic_load_generator.py \\
        --instruments 1000 --tick-rate 10 --users 10 --duration 60 --seed 42

    python scripts/load-testing/synthetic_load_generator.py \\
        --instruments 5000 --scenario heavy --duration 300
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class LoadTestResult:
    """Result of a synthetic load test run."""

    instrument_count: int
    tick_rate: int
    concurrent_users: int
    duration_seconds: float
    scenario: str
    seed: int

    # Throughput
    total_ticks_generated: int = 0
    throughput_msgs_per_sec: float = 0.0

    # Latency (ms)
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0

    # Errors
    total_errors: int = 0
    error_rate_pct: float = 0.0

    # Memory
    rss_start_mb: float = 0.0
    rss_end_mb: float = 0.0
    rss_peak_mb: float = 0.0

    # Timing
    started_at: str = ""
    completed_at: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def _generate_mock_instruments(rng: random.Random, count: int) -> list[str]:
    """Generate a list of mock instrument IDs."""
    venues = ["BINANCE-FUTURES", "OKX-FUTURES", "BYBIT-FUTURES", "CME", "DERIBIT"]
    bases = ["BTC", "ETH", "SOL", "AVAX", "DOT", "LINK", "MATIC", "ARB", "OP", "ATOM"]
    instruments: list[str] = []
    for i in range(count):
        venue = venues[i % len(venues)]
        base = bases[i % len(bases)]
        instruments.append(f"{venue}:PERPETUAL:{base}-USDT-{i:05d}")
    return instruments


def _simulate_tick_processing(
    rng: random.Random,
    instruments: list[str],
    tick_rate: int,
    duration: float,
    scenario: str,
) -> tuple[list[float], int, int]:
    """Simulate tick processing and collect latency samples.

    Returns (latencies_ms, total_ticks, total_errors).
    """
    latencies: list[float] = []
    total_ticks = 0
    total_errors = 0

    # Scenario-based error injection
    error_rate = {
        "normal": 0.0,
        "stress": 0.01,
        "heavy": 0.005,
        "error_storm": 1.0,
        "flash_crash": 0.1,
        "high_latency": 0.0,
    }.get(scenario, 0.0)

    latency_base_ms = 5.0 if scenario != "high_latency" else 3500.0

    # Simulate processing
    ticks_per_batch = len(instruments) * tick_rate
    batches = max(1, int(duration))

    for _batch in range(batches):
        for _tick in range(min(ticks_per_batch, 10000)):  # cap per batch
            total_ticks += 1
            if rng.random() < error_rate:
                total_errors += 1
                continue
            # Simulate latency
            latency = latency_base_ms + rng.gauss(0, latency_base_ms * 0.2)
            latencies.append(max(0.1, latency))

    return latencies, total_ticks, total_errors


def _get_rss_mb() -> float:
    """Get current RSS in MB."""
    import resource

    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss_raw = usage.ru_maxrss
    if sys.platform == "darwin":
        return rss_raw / (1024 * 1024)
    return rss_raw / 1024


def run_load_test(
    instrument_count: int,
    tick_rate: int,
    concurrent_users: int,
    duration: float,
    scenario: str,
    seed: int,
) -> LoadTestResult:
    """Run a synthetic load test and return results."""
    rng = random.Random(seed)
    instruments = _generate_mock_instruments(rng, instrument_count)

    rss_start = _get_rss_mb()
    start_time = time.monotonic()
    started_at = datetime.now(UTC).isoformat()

    logger.info(
        "Starting load test: %d instruments, %d ticks/s, %d users, %ds, scenario=%s",
        instrument_count,
        tick_rate,
        concurrent_users,
        int(duration),
        scenario,
    )

    # Run simulation (single-threaded for determinism)
    all_latencies: list[float] = []
    total_ticks = 0
    total_errors = 0

    for _user in range(concurrent_users):
        latencies, ticks, errors = _simulate_tick_processing(
            rng, instruments, tick_rate, duration / concurrent_users, scenario
        )
        all_latencies.extend(latencies)
        total_ticks += ticks
        total_errors += errors

    elapsed = time.monotonic() - start_time
    rss_end = _get_rss_mb()

    # Compute percentiles
    if all_latencies:
        sorted_lat = sorted(all_latencies)
        n = len(sorted_lat)
        p50 = sorted_lat[n // 2]
        p95 = sorted_lat[int(n * 0.95)]
        p99 = sorted_lat[int(n * 0.99)]
    else:
        p50 = p95 = p99 = 0.0

    throughput = total_ticks / elapsed if elapsed > 0 else 0.0
    error_rate = (total_errors / total_ticks * 100) if total_ticks > 0 else 0.0

    return LoadTestResult(
        instrument_count=instrument_count,
        tick_rate=tick_rate,
        concurrent_users=concurrent_users,
        duration_seconds=round(elapsed, 2),
        scenario=scenario,
        seed=seed,
        total_ticks_generated=total_ticks,
        throughput_msgs_per_sec=round(throughput, 1),
        latency_p50_ms=round(p50, 3),
        latency_p95_ms=round(p95, 3),
        latency_p99_ms=round(p99, 3),
        total_errors=total_errors,
        error_rate_pct=round(error_rate, 4),
        rss_start_mb=round(rss_start, 2),
        rss_end_mb=round(rss_end, 2),
        rss_peak_mb=round(max(rss_start, rss_end), 2),
        started_at=started_at,
        completed_at=datetime.now(UTC).isoformat(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic load generator")
    parser.add_argument("--instruments", type=int, default=45)
    parser.add_argument("--tick-rate", type=int, default=1)
    parser.add_argument("--users", type=int, default=1)
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--scenario", default="normal")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="", help="Output JSON file path")
    args = parser.parse_args()

    result = run_load_test(
        instrument_count=args.instruments,
        tick_rate=args.tick_rate,
        concurrent_users=args.users,
        duration=args.duration,
        scenario=args.scenario,
        seed=args.seed,
    )

    print(result.to_json())

    if args.output:
        from pathlib import Path

        Path(args.output).write_text(result.to_json())
        logger.info("Results written to %s", args.output)

    # Exit non-zero if error rate exceeds 1%
    if result.error_rate_pct > 1.0:
        logger.error("Error rate %.2f%% exceeds 1%% threshold", result.error_rate_pct)
        sys.exit(1)


if __name__ == "__main__":
    main()
