"""A4 — Manifest v8 deep compliance audit (data + code paths).

Mega-audit Phase A4 (expanded scope, operator directive 2026-05-20). Two
dimensions:

1. **Data side**: read each MTDS + IS manifest index from prod GCS, group
   rows by `schema_version`, count distribution. Any row at v < 8 is
   unmigrated data — flagged for the cross-cutting QG ratchet plan.

2. **Code-path side**: scan every consumer of manifest rows for code that
   either (a) hardcodes a v<8 schema_version, (b) doesn't reference v8 enhanced
   columns, or (c) has fallback branches for legacy schemas without a sunset
   date. Output per-file readiness flags.

Output:
    plans/audit/results/manifest_v8_compliance_2026_05_20.csv
    plans/audit/results/manifest_v8_compliance_2026_05_20_summary.md
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import gcsfs
import pyarrow.parquet as pq

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
PROJECT_ID = "central-element-323112"
ENV_SHORT = "prd"

# Manifest buckets to audit (data side).
MANIFEST_BUCKETS: dict[str, list[str]] = {
    "cefi": [
        f"market-data-tick-cefi-{ENV_SHORT}-{PROJECT_ID}",
        f"instruments-store-cefi-{ENV_SHORT}-{PROJECT_ID}",
    ],
    "defi": [
        f"market-data-tick-defi-{ENV_SHORT}-{PROJECT_ID}",
        f"instruments-store-defi-{ENV_SHORT}-{PROJECT_ID}",
    ],
    "tradfi": [
        f"market-data-tick-tradfi-{ENV_SHORT}-{PROJECT_ID}",
        f"instruments-store-tradfi-{ENV_SHORT}-{PROJECT_ID}",
    ],
    "sports": [
        f"market-data-tick-sports-{ENV_SHORT}-{PROJECT_ID}",
        f"instruments-store-sports-{ENV_SHORT}-{PROJECT_ID}",
    ],
    "prediction": [
        f"market-data-tick-pred-{ENV_SHORT}-{PROJECT_ID}",
        "instruments-store-pred-prd-central-element-323112",
    ],
}

# Repos that consume manifest rows (code-path side).
CONSUMER_REPOS: list[str] = [
    "alerting-service",
    "batch-live-reconciliation-service",
    "deployment-api",
    "deployment-service",
    "execution-service",
    "features-service",
    "instruments-service",
    "market-data-processing-service",
    "market-tick-data-service",
    "ml-inference-service",
    "ml-service",
    "ml-training-service",
    "pnl-attribution-service",
    "position-balance-monitor-service",
    "risk-and-exposure-service",
    "strategy-service",
    "trading-agent-service",
    "unified-api-contracts",
    "unified-trading-library",
]

SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {".venv", ".venv-workspace", "build", "dist", "node_modules", "__pycache__", ".git", ".tox", ".pytest_cache"},
)

# Regex patterns.
HARDCODED_VERSION_LT_8 = re.compile(r"schema_version\s*[=:]\s*[1-7]\b|MANIFEST_SCHEMA_VERSION\s*=\s*[1-7]\b")
V8_CONSUMER_INDICATOR = re.compile(r"schema_version\s*[><=]+\s*8|MANIFEST_SCHEMA_VERSION\s*[=]\s*8|capture_status\s*==")
LEGACY_FALLBACK_PATTERN = re.compile(
    r"(?:legacy|v[1-7])(?:.{0,30})(?:fallback|coerce|to_v8|migrate|backfill)", re.IGNORECASE
)
MANIFEST_READ_PATTERN = re.compile(r"read.*manifest|manifest.*read|availability_index|read.*_index/")


def audit_data_side(fs: gcsfs.GCSFileSystem) -> list[dict[str, object]]:
    """Read each manifest's schema_version distribution.

    Returns one row per (asset_group, bucket, schema_version) with count.
    """
    rows: list[dict[str, object]] = []
    for ag, buckets in MANIFEST_BUCKETS.items():
        for bucket in buckets:
            path = f"{bucket}/_index/availability_index.parquet"
            try:
                with fs.open(path, "rb") as fh:
                    df = pq.read_table(fh, columns=["schema_version"]).to_pandas()
            except (FileNotFoundError, OSError) as err:
                rows.append(
                    {
                        "asset_group": ag,
                        "bucket": bucket,
                        "schema_version": "READ_ERROR",
                        "row_count": 0,
                        "error": str(err)[:120],
                    },
                )
                continue
            vc = df["schema_version"].value_counts(dropna=False).to_dict()
            for sv, count in vc.items():
                sv_key = (
                    "NULL" if (sv is None or (isinstance(sv, float) and sv != sv))
                    else str(int(sv) if isinstance(sv, (int, float)) else sv)
                )
                rows.append(
                    {
                        "asset_group": ag,
                        "bucket": bucket,
                        "schema_version": sv_key,
                        "row_count": int(count),
                        "error": "",
                    },
                )
    return rows


def audit_code_paths() -> list[dict[str, object]]:
    """Scan every Python file in consumer repos for v8-readiness."""
    rows: list[dict[str, object]] = []
    for repo in CONSUMER_REPOS:
        repo_root = WORKSPACE_ROOT / repo
        if not repo_root.exists():
            continue
        for root, dirs, files in repo_root.walk():  # type: ignore[attr-defined]
            dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES and not d.startswith(".")]
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                path = root / fname
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                # Only files that touch manifest reading.
                is_consumer = bool(MANIFEST_READ_PATTERN.search(content)) or "availability_index" in content
                if not is_consumer:
                    continue
                v_lt_8 = len(HARDCODED_VERSION_LT_8.findall(content))
                v8_indicator = bool(V8_CONSUMER_INDICATOR.search(content))
                legacy_fallback = len(LEGACY_FALLBACK_PATTERN.findall(content))
                rows.append(
                    {
                        "repo": repo,
                        "rel_path": str(path.relative_to(repo_root)),
                        "v_lt_8_count": v_lt_8,
                        "v8_indicator": v8_indicator,
                        "legacy_fallback_count": legacy_fallback,
                    },
                )
    return rows


def main() -> int:
    fs = gcsfs.GCSFileSystem()

    print("Reading manifest data-side schema_version distribution ...", flush=True)
    data_rows = audit_data_side(fs)
    print(f"  data-side rows: {len(data_rows)}", flush=True)

    print("Scanning code-path consumers ...", flush=True)
    code_rows = audit_code_paths()
    print(f"  code-path files: {len(code_rows)}", flush=True)

    out_dir = WORKSPACE_ROOT / "unified-trading-pm" / "plans" / "audit" / "results"

    # Write CSVs.
    data_csv = out_dir / "manifest_v8_compliance_2026_05_20_data.csv"
    with data_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["asset_group", "bucket", "schema_version", "row_count", "error"])
        writer.writeheader()
        for row in sorted(data_rows, key=lambda r: (r["asset_group"], r["bucket"], r["schema_version"])):
            writer.writerow(row)

    code_csv = out_dir / "manifest_v8_compliance_2026_05_20_code.csv"
    with code_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["repo", "rel_path", "v_lt_8_count", "v8_indicator", "legacy_fallback_count"]
        )
        writer.writeheader()
        for row in sorted(
            code_rows,
            key=lambda r: (-int(r["v_lt_8_count"]) - int(r["legacy_fallback_count"]), r["repo"], r["rel_path"]),
        ):
            writer.writerow(row)

    # Summary.
    summary_path = out_dir / "manifest_v8_compliance_2026_05_20_summary.md"
    # Aggregate data-side: per asset_group, per schema_version.
    per_ag_v: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    bucket_total: dict[str, int] = defaultdict(int)
    for r in data_rows:
        per_ag_v[r["asset_group"]][str(r["schema_version"])] += int(r["row_count"])
        bucket_total[str(r["bucket"])] += int(r["row_count"])

    # Aggregate code-side.
    v_lt_8_files = [r for r in code_rows if int(r["v_lt_8_count"]) > 0]
    v8_aware_files = [r for r in code_rows if bool(r["v8_indicator"])]
    legacy_fallback_files = [r for r in code_rows if int(r["legacy_fallback_count"]) > 0]

    with summary_path.open("w", encoding="utf-8") as fh:
        fh.write("# A4 — Manifest v8 deep compliance summary\n\n")
        fh.write(f"_Generated: {datetime.now(UTC).isoformat()}_\n\n")
        fh.write("## Data side — `_index/availability_index.parquet` `schema_version` distribution per bucket\n\n")
        fh.write("| asset_group | bucket | schema_version | rows |\n|---|---|---:|---:|\n")
        for row in sorted(data_rows, key=lambda r: (r["asset_group"], r["bucket"], r["schema_version"])):
            fh.write(
                f"| {row['asset_group']} | {row['bucket']} | "
                f"{row['schema_version']} | {row['row_count']:,} |\n",
            )

        fh.write("\n## Data side — per-asset-group v<8 row counts (review-blocking)\n\n")
        fh.write("| asset_group | total rows | v8 rows | v<8 rows | NULL rows | v8 % |\n")
        fh.write("|---|---:|---:|---:|---:|---:|\n")
        for ag, versions in per_ag_v.items():
            total = sum(versions.values())
            v8_count = versions.get("8", 0)
            v_lt_8 = sum(versions.get(str(v), 0) for v in (1, 2, 3, 4, 5, 6, 7))
            null_count = versions.get("NULL", 0)
            pct = 100.0 * v8_count / total if total else 0.0
            fh.write(f"| {ag} | {total:,} | {v8_count:,} | {v_lt_8:,} | {null_count:,} | {pct:.2f}% |\n")

        fh.write("\n## Code side — files consuming manifest rows\n\n")
        fh.write(f"- Total consumer files: {len(code_rows)}\n")
        fh.write(f"- Files with hardcoded `schema_version` < 8: **{len(v_lt_8_files)}** (review-blocking)\n")
        fh.write(f"- Files with explicit v8 indicator: {len(v8_aware_files)}\n")
        fh.write(f"- Files with legacy-fallback pattern: {len(legacy_fallback_files)}\n\n")

        if v_lt_8_files:
            fh.write("### Files with hardcoded v<8 schema_version (REVIEW-BLOCKING)\n\n")
            fh.write("| Repo | File | v<8 count | legacy_fallback count |\n|---|---|---:|---:|\n")
            for r in v_lt_8_files[:30]:
                fh.write(f"| {r['repo']} | `{r['rel_path']}` | {r['v_lt_8_count']} | {r['legacy_fallback_count']} |\n")

        if legacy_fallback_files:
            fh.write("\n### Files with legacy-fallback patterns (review per-file for sunset date)\n\n")
            fh.write("| Repo | File | legacy_fallback count |\n|---|---|---:|\n")
            for r in legacy_fallback_files[:30]:
                fh.write(f"| {r['repo']} | `{r['rel_path']}` | {r['legacy_fallback_count']} |\n")

        fh.write("\n## Next actions\n\n")
        fh.write(
            "- Any v<8 row at the data side requires backfill/migration before next bucket cutover"
            " (per single-walk discipline, must bundle into Phase 2 migration).\n"
        )
        fh.write("- Any v<8 hardcoded constant in code requires update + a QG check that raises on resurgence.\n")
        fh.write(
            "- Legacy-fallback patterns should be reviewed for sunset dates"
            " — temporary state per CLAUDE.md must have a named successor plan.\n"
        )
        fh.write(
            "- Recommend new QG step: `scripts/quality_gates/check_manifest_schema_version_constants.py`"
            " that scans the workspace for any non-v8 manifest-schema constant.\n"
        )

    print(f"Wrote {data_csv}", flush=True)
    print(f"Wrote {code_csv}", flush=True)
    print(f"Wrote {summary_path}", flush=True)
    print(f"\nData side: {len(data_rows)} rows across {len(MANIFEST_BUCKETS) * 2} buckets")
    print(f"Code side: {len(code_rows)} consumer files; {len(v_lt_8_files)} with v<8 constants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
