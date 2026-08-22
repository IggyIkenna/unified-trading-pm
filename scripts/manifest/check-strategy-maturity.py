#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Check strategy maturity report card.

Reads strategy-manifest.json and prints a maturity report for each strategy.
Exit 0 on success, exit 1 if manifest cannot be loaded.

Usage:
    python3 scripts/manifest/check-strategy-maturity.py
    python3 scripts/manifest/check-strategy-maturity.py --asset-group CEFI
    python3 scripts/manifest/check-strategy-maturity.py --summary
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MANIFEST_PATH = Path(__file__).resolve().parent.parent.parent / "strategy-manifest.json"


def _checkbox(value: bool) -> str:
    return "[x]" if value else "[ ]"


def print_strategy_report(strategy: dict[str, object]) -> None:
    """Print maturity report card for a single strategy."""
    sid = strategy["strategy_id"]
    maturity = strategy["maturity"]  # type: ignore[index]
    code = maturity["code"]  # type: ignore[index]
    deploy = maturity["deployment"]  # type: ignore[index]
    biz = maturity["business"]  # type: ignore[index]

    print(f"{sid}:")
    print(
        f"  Code:       {code['status']}"  # type: ignore[index]
        f" {_checkbox(code['class_exists'])} class"  # type: ignore[index]
        f" {_checkbox(code['unit_tests'])} tests"  # type: ignore[index]
        f" {_checkbox(code['qg_pass'])} QG"  # type: ignore[index]
        f" {_checkbox(code['merged'])} merged"  # type: ignore[index]
    )
    print(
        f"  Deployment: {deploy['status']}"  # type: ignore[index]
        f" {_checkbox(deploy['batch_analytics'])} batch"  # type: ignore[index]
        f" {_checkbox(deploy['mock_smoke'])} smoke"  # type: ignore[index]
        f" {_checkbox(deploy['batch_live_recon'])} recon"  # type: ignore[index]
    )
    print(
        f"  Business:   {biz['status']}"  # type: ignore[index]
        f" {_checkbox(biz['backtest_profitable'])} backtest"  # type: ignore[index]
        f" {_checkbox(biz['live_1d_match'])} live_1d"  # type: ignore[index]
        f" {_checkbox(biz['live_1w_match'])} live_1w"  # type: ignore[index]
        f" {_checkbox(biz['strategy_deck'])} deck"  # type: ignore[index]
    )


def print_summary(strategies: list[dict[str, object]]) -> None:
    """Print summary statistics across all strategies."""
    total = len(strategies)
    asset_group_counts: dict[str, int] = {}
    code_merged = 0
    deploy_smoke = 0
    biz_backtest = 0

    for s in strategies:
        ag = str(s["asset_group"])
        asset_group_counts[ag] = asset_group_counts.get(ag, 0) + 1
        maturity = s["maturity"]  # type: ignore[index]
        if maturity["code"]["merged"]:  # type: ignore[index]
            code_merged += 1
        if maturity["deployment"]["mock_smoke"]:  # type: ignore[index]
            deploy_smoke += 1
        if maturity["business"]["backtest_profitable"]:  # type: ignore[index]
            biz_backtest += 1

    print(f"\n{'=' * 60}")
    print("STRATEGY MANIFEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total strategies: {total}")
    print("By asset group:")
    for ag, count in sorted(asset_group_counts.items()):
        print(f"  {ag}: {count}")
    print("\nMaturity gates passed:")
    print(f"  Code merged:          {code_merged}/{total}")
    print(f"  Deployment smoke:     {deploy_smoke}/{total}")
    print(f"  Business backtest:    {biz_backtest}/{total}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Strategy maturity report card")
    parser.add_argument(
        "--asset-group",
        type=str,
        default=None,
        dest="asset_group",
        help="Filter by venue asset group (CEFI, TRADFI, DEFI, SPORTS, QUANT, OPTIONS)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary statistics only",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="Path to strategy-manifest.json (default: auto-detect)",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest) if args.manifest else MANIFEST_PATH

    if not manifest_path.exists():
        print(f"ERROR: Manifest not found at {manifest_path}", file=sys.stderr)
        return 1

    with open(manifest_path) as f:
        manifest = json.load(f)

    strategies: list[dict[str, object]] = manifest["strategies"]

    if args.asset_group:
        want = str(args.asset_group).upper()
        strategies = [s for s in strategies if str(s["asset_group"]).upper() == want]

    if not strategies:
        print("No strategies found matching filter.", file=sys.stderr)
        return 1

    if args.summary:
        print_summary(strategies)
        return 0

    for i, strategy in enumerate(strategies):
        if i > 0:
            print()
        print_strategy_report(strategy)

    print_summary(strategies)
    return 0


if __name__ == "__main__":
    sys.exit(main())
