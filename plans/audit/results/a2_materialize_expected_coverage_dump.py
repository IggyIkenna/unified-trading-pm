"""A2 — Materialize the expected_coverage() dump as parquet.

Mega-audit Phase A2 deliverable. Walks every in-scope (asset_group, source,
data_type) tuple from `EXPECTED_COVERAGE_BY_ASSET_GROUP` and calls the new
`expected_coverage()` oracle for every date from 2020-01-01 to today.

No symbol axis in this v1 — per operator decision 2026-05-20 ("Filter by
EXPECTED_COVERAGE_BY_ASSET_GROUP scope") since the per-symbol dimension is
captured downstream in A3 via the manifest comparison (each manifest row
already carries the symbol axis). Adding symbols here would balloon the
dump to tens of millions of rows for no diagnostic gain.

Output:
    plans/audit/results/expected_coverage_dump_2026_05_20.parquet
    plans/audit/results/expected_coverage_dump_2026_05_20_summary.md

Schema:
    asset_group: str
    source: str
    data_type: str
    date: date32
    expected_state: str  (SHOULD_HAVE_DATA | EXPECTED_EMPTY | NOT_YET_LIVE | NOT_IN_SCOPE)
    reason: str | None   (EmptyConfirmedReason value)
    diagnostic: str
"""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
UAC_ROOT = WORKSPACE_ROOT / "unified-api-contracts"
sys.path.insert(0, str(UAC_ROOT))

import pyarrow as pa  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

from unified_api_contracts.registry.expected_coverage import (  # noqa: E402
    EXPECTED_COVERAGE_BY_ASSET_GROUP,
    expected_coverage,
)

START_DATE = date(2020, 1, 1)
END_DATE = date(2026, 5, 20)


def daterange(start: date, end_inclusive: date):
    cur = start
    one = timedelta(days=1)
    while cur <= end_inclusive:
        yield cur
        cur += one


def main() -> int:
    asset_groups: list[str] = []
    sources: list[str] = []
    data_types: list[str] = []
    dates: list[date] = []
    states: list[str] = []
    reasons: list[str | None] = []
    diagnostics: list[str] = []

    per_state_count: dict[str, int] = defaultdict(int)
    per_reason_count: dict[str, int] = defaultdict(int)
    per_asset_group_count: dict[str, int] = defaultdict(int)
    per_asset_group_should_have: dict[str, int] = defaultdict(int)
    per_asset_group_expected_empty: dict[str, int] = defaultdict(int)

    for ag, venues in EXPECTED_COVERAGE_BY_ASSET_GROUP.items():
        for source, dts in venues.items():
            for dt in dts:
                for d in daterange(START_DATE, END_DATE):
                    result = expected_coverage(ag, source, dt, d)
                    asset_groups.append(ag)
                    sources.append(source)
                    data_types.append(dt)
                    dates.append(d)
                    states.append(result.state.value)
                    reasons.append(result.reason)
                    diagnostics.append(result.diagnostic)

                    per_state_count[result.state.value] += 1
                    per_asset_group_count[ag] += 1
                    if result.reason is not None:
                        per_reason_count[result.reason] += 1
                    if result.state.value == "SHOULD_HAVE_DATA":
                        per_asset_group_should_have[ag] += 1
                    elif result.state.value == "EXPECTED_EMPTY":
                        per_asset_group_expected_empty[ag] += 1

    print(f"Materialized {len(states):,} rows", flush=True)

    table = pa.table(
        {
            "asset_group": asset_groups,
            "source": sources,
            "data_type": data_types,
            "date": pa.array(dates, type=pa.date32()),
            "expected_state": states,
            "reason": reasons,
            "diagnostic": diagnostics,
        }
    )
    out_dir = WORKSPACE_ROOT / "unified-trading-pm" / "plans" / "audit" / "results"
    parquet_path = out_dir / "expected_coverage_dump_2026_05_20.parquet"
    pq.write_table(table, parquet_path, compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1024 / 1024:.2f} MiB)", flush=True)

    summary_path = out_dir / "expected_coverage_dump_2026_05_20_summary.md"
    with summary_path.open("w", encoding="utf-8") as fh:
        fh.write("# A2 — expected_coverage() dump summary\n\n")
        fh.write(f"_Generated: {datetime.now(UTC).isoformat()}_\n\n")
        fh.write(f"Window: {START_DATE.isoformat()} → {END_DATE.isoformat()}\n\n")
        fh.write(f"Total rows: {len(states):,}\n\n")
        fh.write(f"Output: `plans/audit/results/expected_coverage_dump_2026_05_20.parquet` ")
        fh.write(f"({parquet_path.stat().st_size / 1024 / 1024:.2f} MiB)\n\n")

        fh.write("## State breakdown\n\n")
        fh.write("| State | Rows | % |\n|---|---:|---:|\n")
        for state, count in sorted(per_state_count.items(), key=lambda kv: -kv[1]):
            pct = 100.0 * count / len(states) if states else 0.0
            fh.write(f"| `{state}` | {count:,} | {pct:.2f}% |\n")

        fh.write("\n## Reason breakdown (EXPECTED_EMPTY + NOT_YET_LIVE cells)\n\n")
        fh.write("| Reason | Rows |\n|---|---:|\n")
        for reason, count in sorted(per_reason_count.items(), key=lambda kv: -kv[1]):
            fh.write(f"| `{reason}` | {count:,} |\n")

        fh.write("\n## Per-asset-group breakdown\n\n")
        fh.write("| asset_group | total cells | SHOULD_HAVE_DATA | EXPECTED_EMPTY |\n")
        fh.write("|---|---:|---:|---:|\n")
        for ag in sorted(per_asset_group_count, key=lambda k: -per_asset_group_count[k]):
            fh.write(
                f"| {ag} | {per_asset_group_count[ag]:,} | "
                f"{per_asset_group_should_have.get(ag, 0):,} | "
                f"{per_asset_group_expected_empty.get(ag, 0):,} |\n"
            )

        fh.write("\n## Notes\n\n")
        fh.write("- No per-symbol axis in v1 (operator decision 2026-05-20). A3 introduces per-symbol comparison by reading manifest rows directly.\n")
        fh.write("- Sports off-season calendars are not yet encoded in UAC; in-scope sports cells default to `SHOULD_HAVE_DATA`. Tracked in `expected_coverage_calendar_decisions_2026_05_20.md`.\n")
        fh.write("- DeFi protocol pause windows are not yet encoded; in-scope DeFi cells default to `SHOULD_HAVE_DATA` once chain genesis + venue launch pass.\n")
        fh.write("- `SourceCapability.coverage_start` (per-data_type) was promoted by slot-3 plan `uac_source_capability_metadata_promotion_2026_05_20.md` but a lookup index integration is pending (slot-3 Phase 4).\n")

    print(f"Wrote {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
