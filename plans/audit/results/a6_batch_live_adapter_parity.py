"""A6 — Batch-live adapter parity audit.

Mega-audit Phase A6 (operator directive 2026-05-20). Per CLAUDE.md
"Batch = Live (CRITICAL)" — live + batch are operational modes of the
same pipeline. For every venue × data_type with a batch adapter, there
MUST be a live adapter (potentially from a different upstream source,
but same schema + same manifest emission contract).

Approach:

1. Enumerate adapter files across MTDS + instruments-service.
2. Classify each as batch / live / shared.
3. Extract venue + data_type signals from path + module-level constants.
4. Build matrix per (asset_group, venue, data_type) of (has_batch, has_live).
5. Pair against EXPECTED_COVERAGE_BY_ASSET_GROUP to flag missing-live cells
   (batch-only) and missing-batch cells (live-only).

Output:
    plans/audit/results/batch_live_adapter_parity_2026_05_20.csv
    plans/audit/results/batch_live_adapter_parity_2026_05_20_summary.md
"""

from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(WORKSPACE_ROOT / "unified-api-contracts"))

from unified_api_contracts.registry.expected_coverage import (  # noqa: E402
    EXPECTED_COVERAGE_BY_ASSET_GROUP,
)

ADAPTER_REPOS: list[str] = [
    "market-tick-data-service",
    "instruments-service",
    "market-data-processing-service",
]

SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {".venv", ".venv-workspace", "build", "dist", "node_modules", "__pycache__", ".git", ".tox", ".pytest_cache", "tests"},
)

# Path patterns to classify a file as batch vs live.
BATCH_PATH_PATTERN = re.compile(r"/(?:handlers?|batch|backfill|archive|historical)/")
LIVE_PATH_PATTERN = re.compile(r"/(?:live|stream|streaming|websocket|ws|realtime|rt_)/|_live\.py|_stream\.py|_ws\.py")
ADAPTER_PATH_PATTERN = re.compile(r"/(?:adapters?|handlers?|clients?)/|_adapter\.py|_client\.py|_handler\.py")

# Heuristic: venue token detection from path or module constants.
VENUE_FROM_PATH = re.compile(
    r"/(binance|bybit|okx|deribit|upbit|coinbase|hyperliquid|aster|kraken|bitfinex|bitget|"
    r"polymarket|kalshi|"
    r"odds_?api|pinnacle|betfair|draftkings|fanduel|bet365|"
    r"cme|ice|cboe|nyse|nasdaq|fx|yahoo_?finance|databento|barchart|"
    r"uniswap|sushiswap|curve|balancer|pancakeswap|aave|compound|morpho|fluid|"
    r"lido|etherfi|ethena|jito|rocketpool|"
    r"phoenix|orca|raydium|drift|gmx|extended|lighter|pacifica|"
    r"chainlink|pyth|"
    r"reuters|polygon_io|alpha_vantage|fred)",
    re.IGNORECASE,
)

DATA_TYPE_FROM_PATH = re.compile(
    r"(trades|book_snapshot_5|book_snapshot|orderbook|derivative_ticker|liquidations|"
    r"futures_chain|options_chain|funding|funding_rates|"
    r"ohlcv_1m|ohlcv_15m|ohlcv_24h|tbbo|ohlcv|candles|"
    r"odds|odds_snapshot|odds_movement|"
    r"dex_pools|dex_swaps|lending_indices|liquidation_events|position_data|risk_params|flash_loan_events|"
    r"lst_rates|staking_yields|eigenlayer_rewards|"
    r"oracle_prices|gas_fees|bridge_events|token_transfers)",
    re.IGNORECASE,
)


def walk_repos() -> list[Path]:
    paths: list[Path] = []
    for repo in ADAPTER_REPOS:
        repo_root = WORKSPACE_ROOT / repo
        if not repo_root.exists():
            continue
        for root, dirs, files in repo_root.walk():  # type: ignore[attr-defined]
            dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES and not d.startswith(".")]
            for fname in files:
                if fname.endswith(".py"):
                    paths.append(root / fname)
    return paths


def classify_path(rel_path: str) -> tuple[bool, bool]:
    """Return (is_batch, is_live) per path heuristics."""
    is_batch = bool(BATCH_PATH_PATTERN.search(rel_path)) or "/handlers" in rel_path
    is_live = bool(LIVE_PATH_PATTERN.search(rel_path))
    return is_batch, is_live


def extract_venue_data_type(path_str: str) -> tuple[set[str], set[str]]:
    venues: set[str] = set()
    data_types: set[str] = set()
    for m in VENUE_FROM_PATH.finditer(path_str):
        venues.add(m.group(1).lower().replace("_", ""))
    for m in DATA_TYPE_FROM_PATH.finditer(path_str):
        data_types.add(m.group(1).lower())
    return venues, data_types


def main() -> int:
    paths = walk_repos()
    print(f"Walking {len(paths):,} files across {len(ADAPTER_REPOS)} adapter repos ...", flush=True)

    # Per (venue_token, data_type_token) → (batch_files, live_files).
    matrix: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(
        lambda: {"batch": set(), "live": set()},
    )

    for path in paths:
        rel = str(path.relative_to(WORKSPACE_ROOT))
        if not ADAPTER_PATH_PATTERN.search(rel):
            continue
        is_batch, is_live = classify_path(rel)
        venues, data_types = extract_venue_data_type(rel)
        if not venues or not data_types:
            # Try reading file head to extract tokens from module constants.
            try:
                head = path.read_text(encoding="utf-8", errors="replace")[:4000]
            except OSError:
                continue
            if not venues:
                for m in VENUE_FROM_PATH.finditer(head):
                    venues.add(m.group(1).lower().replace("_", ""))
            if not data_types:
                for m in DATA_TYPE_FROM_PATH.finditer(head):
                    data_types.add(m.group(1).lower())
        if not venues or not data_types:
            continue
        for v in venues:
            for dt in data_types:
                if is_batch:
                    matrix[(v, dt)]["batch"].add(rel)
                if is_live:
                    matrix[(v, dt)]["live"].add(rel)
                if not is_batch and not is_live:
                    # Shared/ambiguous — count as batch by default (most adapters are batch first).
                    matrix[(v, dt)]["batch"].add(rel)

    # Cross-reference against scope policy.
    in_scope_pairs: set[tuple[str, str, str]] = set()  # (asset_group, venue_token, data_type)
    for ag, venues_dict in EXPECTED_COVERAGE_BY_ASSET_GROUP.items():
        for source, dts in venues_dict.items():
            for venue_word in re.findall(r"[A-Za-z0-9]+", source):
                token = venue_word.lower()
                for dt in dts:
                    in_scope_pairs.add((ag, token, dt.lower()))

    # Build rows: per (asset_group, venue_token, data_type) in scope, lookup batch/live presence.
    rows: list[dict[str, object]] = []
    for ag, venue_token, dt in sorted(in_scope_pairs):
        entry = matrix.get((venue_token, dt), {"batch": set(), "live": set()})
        rows.append(
            {
                "asset_group": ag,
                "venue_token": venue_token,
                "data_type": dt,
                "batch_files": len(entry["batch"]),
                "live_files": len(entry["live"]),
                "has_batch": len(entry["batch"]) > 0,
                "has_live": len(entry["live"]) > 0,
                "parity_status": (
                    "GREEN" if entry["batch"] and entry["live"]
                    else "BATCH_ONLY" if entry["batch"]
                    else "LIVE_ONLY" if entry["live"]
                    else "MISSING_BOTH"
                ),
                "sample_batch_path": next(iter(entry["batch"]), ""),
                "sample_live_path": next(iter(entry["live"]), ""),
            }
        )

    out_dir = WORKSPACE_ROOT / "unified-trading-pm" / "plans" / "audit" / "results"
    csv_path = out_dir / "batch_live_adapter_parity_2026_05_20.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "asset_group",
                "venue_token",
                "data_type",
                "batch_files",
                "live_files",
                "has_batch",
                "has_live",
                "parity_status",
                "sample_batch_path",
                "sample_live_path",
            ],
        )
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (r["parity_status"], r["asset_group"], r["venue_token"], r["data_type"])):
            writer.writerow(row)

    # Per-asset-group parity breakdown.
    per_ag_status: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        per_ag_status[str(r["asset_group"])][str(r["parity_status"])] += 1

    summary_path = out_dir / "batch_live_adapter_parity_2026_05_20_summary.md"
    with summary_path.open("w", encoding="utf-8") as fh:
        fh.write("# A6 — Batch-live adapter parity summary\n\n")
        fh.write(f"_Generated: {datetime.now(UTC).isoformat()}_\n\n")
        fh.write(f"Adapter files scanned: {len(paths):,} across {len(ADAPTER_REPOS)} repos.\n")
        fh.write(f"In-scope (asset_group, venue_token, data_type) tuples checked: {len(rows):,}.\n\n")

        fh.write("## Parity status per asset_group\n\n")
        fh.write("| asset_group | GREEN | BATCH_ONLY | LIVE_ONLY | MISSING_BOTH |\n|---|---:|---:|---:|---:|\n")
        all_statuses = ["GREEN", "BATCH_ONLY", "LIVE_ONLY", "MISSING_BOTH"]
        for ag in sorted(per_ag_status):
            counts = per_ag_status[ag]
            row = f"| {ag} | "
            for s in all_statuses:
                row += f"{counts.get(s, 0)} | "
            fh.write(row.rstrip(" |") + " |\n")

        fh.write("\n## BATCH_ONLY cells (live equivalent MUST be built per CLAUDE.md Batch = Live)\n\n")
        batch_only = [r for r in rows if r["parity_status"] == "BATCH_ONLY"]
        fh.write(f"Total BATCH_ONLY cells: **{len(batch_only)}** (review-blocking — every batch adapter MUST have a live equivalent)\n\n")
        if batch_only:
            fh.write("| asset_group | venue | data_type | batch file count | sample |\n|---|---|---|---:|---|\n")
            for r in sorted(batch_only, key=lambda x: (x["asset_group"], x["venue_token"], x["data_type"]))[:40]:
                fh.write(
                    f"| {r['asset_group']} | {r['venue_token']} | {r['data_type']} | {r['batch_files']} | `{r['sample_batch_path']}` |\n",
                )
            if len(batch_only) > 40:
                fh.write(f"\n_(showing first 40 of {len(batch_only)} BATCH_ONLY cells — see CSV for full list)_\n")

        fh.write("\n## MISSING_BOTH cells (no adapter detected — silent gap)\n\n")
        missing_both = [r for r in rows if r["parity_status"] == "MISSING_BOTH"]
        fh.write(f"Total MISSING_BOTH cells: **{len(missing_both)}**\n\n")
        if missing_both:
            fh.write("| asset_group | venue | data_type |\n|---|---|---|\n")
            for r in sorted(missing_both, key=lambda x: (x["asset_group"], x["venue_token"], x["data_type"]))[:40]:
                fh.write(f"| {r['asset_group']} | {r['venue_token']} | {r['data_type']} |\n")
            if len(missing_both) > 40:
                fh.write(f"\n_(showing first 40 of {len(missing_both)} MISSING_BOTH cells)_\n")

        fh.write("\n## LIVE_ONLY cells (suspicious — usually intentional only for derived/streaming-only data_types)\n\n")
        live_only = [r for r in rows if r["parity_status"] == "LIVE_ONLY"]
        fh.write(f"Total LIVE_ONLY cells: **{len(live_only)}**\n\n")
        if live_only:
            fh.write("| asset_group | venue | data_type |\n|---|---|---|\n")
            for r in sorted(live_only, key=lambda x: (x["asset_group"], x["venue_token"], x["data_type"]))[:20]:
                fh.write(f"| {r['asset_group']} | {r['venue_token']} | {r['data_type']} |\n")

        fh.write("\n## Caveats (sampling transparency)\n\n")
        fh.write("- Venue + data_type extraction is **regex-based on file paths + first 4000 chars**. Adapters that don't put venue/data_type in their path or module header are missed.\n")
        fh.write("- Path classification `is_batch` / `is_live` based on path tokens (`/handlers/`, `/live/`, `/stream/`, etc.). Ambiguous files default to batch.\n")
        fh.write("- An adapter may exist in code but not be wired into the orchestrator scope — A6 only checks *adapter file existence*, not whether it's enumerated.\n")
        fh.write("- A6 does not check schema parity between batch + live adapters (would require running them). Operator may want to follow up with a runtime parity test (cross-checking manifest rows from each mode).\n")
        fh.write("- Tokens collapsed (e.g. `OKX` and `okx` and `binance-futures` → split into `binance` + `futures`). Per-token false positives possible — see CSV `venue_token` column for exact match.\n")

    print(f"A6 scan complete:")
    print(f"  CSV:     {csv_path}")
    print(f"  Summary: {summary_path}")
    print(f"  In-scope tuples checked: {len(rows):,}")
    print(f"  GREEN: {sum(1 for r in rows if r['parity_status']=='GREEN')}")
    print(f"  BATCH_ONLY (review-blocking): {sum(1 for r in rows if r['parity_status']=='BATCH_ONLY')}")
    print(f"  LIVE_ONLY: {sum(1 for r in rows if r['parity_status']=='LIVE_ONLY')}")
    print(f"  MISSING_BOTH: {sum(1 for r in rows if r['parity_status']=='MISSING_BOTH')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
