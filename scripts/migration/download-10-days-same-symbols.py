#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Download market data for the SAME 17 symbols across 10 days.

Uses identical symbols as download_all_providers_validate.py for downstream testing
(features, ML, strategy). SAME date range for all categories (aligned for features/ML):

- ALL: 2025-11-01 to 2025-11-10 (10 days)

Tracks per-day success/failure. Writes failed_days.json for retry.

Usage:
  python scripts/download_10_days_same_symbols.py [--dry-run] [--parallel N]
  python scripts/download_10_days_same_symbols.py --retry-from logs/.../failed_days.json

Examples:
  python scripts/download_10_days_same_symbols.py --no-dry-run --parallel 5
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add market-tick-data-service to path
REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
MARKET_TICK_HANDLER = WORKSPACE_ROOT / "market-tick-data-service"
if not MARKET_TICK_HANDLER.exists():
    MARKET_TICK_HANDLER = REPO_ROOT / "market-tick-data-service"
if not MARKET_TICK_HANDLER.exists():
    raise FileNotFoundError("market-tick-data-service not found")
sys.path.insert(0, str(MARKET_TICK_HANDLER))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@dataclass
class DownloadTask:
    """Single download task for (category, venue, symbol, data_type) over 10 days."""

    category: str
    venue: str
    symbol: str
    data_type: str
    start_date: str
    end_date: str
    dry_run: bool = True
    force: bool = False
    max_results: int | None = None  # None = no limit (all 10 days)

    def __post_init__(self):
        self.id = f"{self.category}:{self.venue}:{self.symbol}:{self.data_type}"

    def to_cmd(self) -> list[str]:
        cmd = [
            sys.executable,
            "-m",
            "market_data_tick_handler",
            "--mode",
            "download",
            "--start-date",
            self.start_date,
            "--end-date",
            self.end_date,
            "--venues",
            self.venue,
            "--symbols",
            self.symbol,
            "--data-types",
            self.data_type,
            "--skip-dependency-check",
        ]
        if self.category == "CEFI":
            cmd.extend(["--CEFI"])
        elif self.category == "TRADFI":
            cmd.extend(["--TRADFI"])
        elif self.category == "DEFI":
            cmd.extend(["--DEFI"])
        if self.dry_run:
            cmd.extend(["--dry-run"])
        if self.force:
            cmd.extend(["--force"])
        if self.max_results is not None:
            cmd.extend(["--max-results", str(self.max_results)])
        return cmd


# Same symbols as download_all_providers_validate.py - 10 days each
# ALL categories: 2025-11-01 to 2025-11-10 (aligned for features/ML)
TASKS_10_DAYS = [
    # CEFI
    ("CEFI", "BINANCE-FUTURES", "BTC-USDT@LIN", "trades", "2025-11-01", "2025-11-10"),
    ("CEFI", "BYBIT", "BTC-USDT@LIN", "trades", "2025-11-01", "2025-11-10"),
    ("CEFI", "DERIBIT", "BTC-USD@INV", "trades", "2025-11-01", "2025-11-10"),
    ("CEFI", "OKX", "BTC-USDT", "trades", "2025-11-01", "2025-11-10"),
    ("CEFI", "HYPERLIQUID", "BTC-USDC@LIN", "trades", "2025-11-01", "2025-11-10"),
    ("CEFI", "ASTER", "BTC-USDC@LIN", "trades", "2025-11-01", "2025-11-10"),
    # TRADFI
    ("TRADFI", "NASDAQ", "IBIT-USD", "ohlcv_1m", "2025-11-01", "2025-11-10"),
    ("TRADFI", "NYSE", "ABBV-USD", "ohlcv_1m", "2025-11-01", "2025-11-10"),
    ("TRADFI", "CBOE", "VIX-USD", "ohlcv_1m", "2025-11-01", "2025-11-10"),
    ("TRADFI", "CME", "AUD-USD-260116@LIN", "ohlcv_1m", "2025-11-01", "2025-11-10"),
    ("TRADFI", "FX", "KRW-USD", "ohlcv_24h", "2025-11-01", "2025-11-10"),
    # DEFI
    ("DEFI", "UNISWAP_V2-ETHEREUM", "WETH-USDC", "dex_swaps", "2025-11-01", "2025-11-10"),
    ("DEFI", "UNISWAP_V3-ETHEREUM", "WETH-USDC:500", "dex_swaps", "2025-11-01", "2025-11-10"),
    ("DEFI", "UNISWAP_V4-ETHEREUM", "ETH-USDC:500", "dex_swaps", "2025-11-01", "2025-11-10"),
    ("DEFI", "CURVE-ETHEREUM", "3pool", "dex_swaps", "2025-11-01", "2025-11-10"),
    ("DEFI", "AAVE_V3_ETHEREUM", "AWETH", "lending_indices", "2025-11-01", "2025-11-10"),
    ("DEFI", "LIDO-ETHEREUM", "STETH", "oracle_prices", "2025-11-01", "2025-11-10"),
]


# Regex to parse per-day results from log (JSON: "message": "Day YYYY-MM-DD completed: ...")
_DAY_FAILED_RE = re.compile(
    r"Day (\d{4}-\d{2}-\d{2}) completed: FAILED",
    re.IGNORECASE,
)
_DAY_SUCCESS_RE = re.compile(
    r"Day (\d{4}-\d{2}-\d{2}) completed:.*?(\d+)/(\d+) successful",
)


def _parse_per_day_from_log(log_path: str, task: DownloadTask) -> dict[str, str]:
    """Parse log file for per-day success/failure. Returns {date: 'ok'|'failed'|'unknown'}."""
    per_day: dict[str, str] = {}
    # Initialize all days in range as unknown
    start = datetime.strptime(task.start_date, "%Y-%m-%d").date()
    end = datetime.strptime(task.end_date, "%Y-%m-%d").date()
    d = start
    while d <= end:
        per_day[d.strftime("%Y-%m-%d")] = "unknown"
        d += timedelta(days=1)

    try:
        with open(log_path) as f:
            for line in f:
                # JSON format: {"message": "Day 2025-11-03 completed: FAILED ..."}
                m = _DAY_FAILED_RE.search(line)
                if m:
                    per_day[m.group(1)] = "failed"
                    continue
                m = _DAY_SUCCESS_RE.search(line)
                if m:
                    ok, total = int(m.group(2)), int(m.group(3))
                    per_day[m.group(1)] = "ok" if (total > 0 and ok > 0) else "failed"
    except (OSError, FileNotFoundError):
        pass
    return per_day


def run_task(task: DownloadTask, log_dir: Path, timeout: int = 600) -> tuple[DownloadTask, bool, str]:
    """Run a single download task."""
    # Per-day retry tasks use date in filename to avoid overwriting
    if task.start_date == task.end_date:
        log_file = log_dir / f"{task.category}_{task.venue}_{task.data_type}_{task.start_date}.log"
    else:
        log_file = log_dir / f"{task.category}_{task.venue}_{task.data_type}.log"
    cmd = task.to_cmd()
    try:
        with open(log_file, "w") as f:
            result = subprocess.run(
                cmd,
                cwd=str(MARKET_TICK_HANDLER),
                env={**os.environ},
                stdout=f,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                text=True,
            )
        return (task, result.returncode == 0, str(log_file))
    except subprocess.TimeoutExpired:
        with open(log_file, "a") as f:
            f.write(f"\n[TIMEOUT after {timeout}s]\n")
        return (task, False, str(log_file))
    except (OSError, PermissionError, ValueError) as e:
        with open(log_file, "w") as f:
            f.write(f"Error: {e}\n")
        return (task, False, str(log_file))


def _build_retry_tasks(failed_days_path: Path, dry_run: bool) -> list[DownloadTask]:
    """Build per-day tasks from failed_days.json for retry."""
    with open(failed_days_path) as f:
        data = json.load(f)
    tasks = []
    if "failed_days" not in data:
        raise KeyError("failed_days required in failed_days.json")
    for item in data["failed_days"]:
        task_id = item["task"]
        date = item["date"]
        # Parse task_id: CATEGORY:VENUE:SYMBOL:DATA_TYPE (symbol may contain colons)
        parts = task_id.split(":")
        if len(parts) < 4:
            continue
        category, venue = parts[0], parts[1]
        data_type = parts[-1]
        symbol = ":".join(parts[2:-1])
        # Find full task params from TASKS_10_DAYS
        for cat, ven, sym, dt, _, _ in TASKS_10_DAYS:
            if cat == category and ven == venue and sym == symbol and dt == data_type:
                tasks.append(DownloadTask(cat, ven, sym, dt, date, date, dry_run=dry_run))
                break
    return tasks


def main():
    parser = argparse.ArgumentParser(description="Download 10 days of data for same symbols (downstream testing)")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--no-dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Force re-download (skip GCS existence check)")
    parser.add_argument("--parallel", type=int, default=5)
    parser.add_argument("--log-dir", type=str, default=None)
    parser.add_argument("--timeout", type=int, default=600, help="Per-task timeout (seconds)")
    parser.add_argument(
        "--retry-from",
        type=str,
        default=None,
        help="Retry only failed (task, date) pairs from failed_days.json",
    )
    parser.add_argument(
        "--categories",
        type=str,
        nargs="+",
        default=None,
        help="Filter to specific categories only (e.g. --categories CEFI TRADFI). Default: all.",
    )
    args = parser.parse_args()

    dry_run = args.dry_run and not args.no_dry_run
    force = getattr(args, "force", False)
    log_dir = Path(args.log_dir or f"logs/download_10_days_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}")
    log_dir.mkdir(parents=True, exist_ok=True)

    if args.retry_from:
        retry_path = Path(args.retry_from)
        if not retry_path.exists():
            logger.error("Retry file not found: %s", retry_path)
            sys.exit(1)
        tasks = _build_retry_tasks(retry_path, dry_run)
        logger.info("Retry mode: %d per-day tasks from %s", len(tasks), retry_path)
        if not tasks:
            logger.info("No failed days to retry.")
            sys.exit(0)
        for t in tasks:
            t.force = force
    else:
        base_tasks = [
            DownloadTask(cat, ven, sym, dt, sd, ed, dry_run=dry_run, force=force)
            for (cat, ven, sym, dt, sd, ed) in TASKS_10_DAYS
        ]
        if args.categories:
            cats_upper = [c.upper() for c in args.categories]
            tasks = [t for t in base_tasks if t.category in cats_upper]
            logger.info("Category filter: %s -> %d tasks", cats_upper, len(tasks))
            if not tasks:
                logger.error("No tasks match categories %s", cats_upper)
                sys.exit(1)
        else:
            tasks = base_tasks

    logger.info("=" * 70)
    logger.info("DOWNLOAD 10 DAYS - SAME SYMBOLS (downstream testing)")
    logger.info("=" * 70)
    logger.info("Dry run: %s", dry_run)
    logger.info("Force: %s", force)
    logger.info("Parallel: %d", args.parallel)
    logger.info("Log dir: %s", log_dir.resolve())
    logger.info("Tasks: %d", len(tasks))
    logger.info("=" * 70)

    results: list[tuple[DownloadTask, bool, str]] = []
    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {executor.submit(run_task, t, log_dir, args.timeout): t for t in tasks}
        for future in as_completed(futures):
            task, success, log_path = future.result()
            results.append((task, success, log_path))
            status = "✅" if success else "❌"
            logger.info("%s %s (%s to %s)", status, task.id, task.start_date, task.end_date)

    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed
    logger.info("=" * 70)
    logger.info("SUMMARY: %d passed, %d failed", passed, failed)

    # Per-day tracking: parse logs and build failed_days
    failed_days: list[dict[str, str]] = []
    per_day_summary: dict[str, dict[str, str]] = {}

    for task, ok, log_path in results:
        per_day = _parse_per_day_from_log(log_path, task)
        key = f"{task.id}:{task.start_date}" if task.start_date == task.end_date else task.id
        per_day_summary[key] = per_day
        for date, status in per_day.items():
            if status == "failed" or (status == "unknown" and not ok):
                failed_days.append({"task": task.id, "date": date})

    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "dry_run": dry_run,
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "date_ranges": {
            "TRADFI": "2025-11-01 to 2025-11-10",
            "CEFI": "2026-01-21 to 2026-01-30",
            "DEFI": "2026-01-21 to 2026-01-30",
        },
        "results": [{"task": r[0].id, "success": r[1], "log": r[2]} for r in results],
        "per_day_summary": per_day_summary,
        "failed_days": failed_days,
    }
    report_path = log_dir / "report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info("Report: %s", report_path)

    failed_days_path = log_dir / "failed_days.json"
    abs_path = str(failed_days_path.resolve())
    with open(failed_days_path, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "log_dir": str(log_dir.resolve()),
                "failed_days": failed_days,
                "retry_command": (
                    f"python scripts/download_10_days_same_symbols.py --no-dry-run --retry-from {abs_path}"
                ),
            },
            f,
            indent=2,
        )
    logger.info("Failed days (for retry): %s", failed_days_path)
    if failed_days:
        logger.info("  %d (task, date) pairs to retry. Run: --retry-from %s", len(failed_days), failed_days_path)

    if failed > 0:
        for task, ok, log_path in results:
            if not ok:
                logger.warning("  - %s (log: %s)", task.id, log_path)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
