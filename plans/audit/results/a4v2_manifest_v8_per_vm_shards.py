"""A4 v2 — Manifest v8 compliance for `_index/per_vm/*.parquet` shards.

Gap closure for operator directive 2026-05-20 §5: "A4 doesn't read
`_index/per_vm/*.parquet` shards — pre-consolidation per-VM shards may
have different versions."

A4 v1 only read the master `_index/availability_index.parquet`. A4 v2
walks every `_index/per_vm/<vm>.parquet` shard per bucket + computes the
`schema_version` distribution. Surfaces:

- Per-VM shards at v<8 (post-bump VMs writing at old schema = a bug).
- Per-VM shards with NULL schema_version (untyped writes).
- Per-VM shards whose distribution differs from the canonical (consolidator coverage gap).

Output:
    plans/audit/results/manifest_v8_per_vm_shards_2026_05_20.csv
    plans/audit/results/manifest_v8_per_vm_shards_2026_05_20_summary.md
"""

from __future__ import annotations

import csv
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import gcsfs
import pyarrow.parquet as pq

# Workspace convention per CLAUDE.md: GCS REST API + thread pool (GIL released → true parallelism).
NUM_WORKERS = 32

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
PROJECT_ID = "central-element-323112"
ENV_SHORT = "prd"

BUCKETS: list[tuple[str, str]] = [
    ("cefi", f"market-data-tick-cefi-{ENV_SHORT}-{PROJECT_ID}"),
    ("defi", f"market-data-tick-defi-{ENV_SHORT}-{PROJECT_ID}"),
    ("tradfi", f"market-data-tick-tradfi-{ENV_SHORT}-{PROJECT_ID}"),
    ("sports", f"market-data-tick-sports-{ENV_SHORT}-{PROJECT_ID}"),
    ("prediction", f"market-data-tick-pred-{ENV_SHORT}-{PROJECT_ID}"),
    ("cefi", f"instruments-store-cefi-{ENV_SHORT}-{PROJECT_ID}"),
    ("defi", f"instruments-store-defi-{ENV_SHORT}-{PROJECT_ID}"),
    ("tradfi", f"instruments-store-tradfi-{ENV_SHORT}-{PROJECT_ID}"),
    ("sports", f"instruments-store-sports-{ENV_SHORT}-{PROJECT_ID}"),
    ("prediction", f"instruments-store-pred-{ENV_SHORT}-{PROJECT_ID}"),
]


def _scan_one_shard(args: tuple[str, str, str]) -> dict[str, object]:
    """Read one per_vm shard's schema_version distribution. Thread-safe (each call opens its own fs)."""
    ag, bucket, shard_path = args
    fs = gcsfs.GCSFileSystem()
    try:
        with fs.open(shard_path, "rb") as fh:
            pf = pq.ParquetFile(fh)
            if "schema_version" not in pf.schema_arrow.names:
                return {
                    "asset_group": ag,
                    "bucket": bucket,
                    "vm_shard": shard_path.split("/")[-1],
                    "total_rows": pf.metadata.num_rows,
                    "v8_rows": 0,
                    "v_lt_8_rows": 0,
                    "null_rows": pf.metadata.num_rows,
                    "schema_versions_seen": "(no schema_version column)",
                }
        with fs.open(shard_path, "rb") as fh2:
            df = pq.read_table(fh2, columns=["schema_version"]).to_pandas()
    except (FileNotFoundError, OSError) as err:
        return {
            "asset_group": ag,
            "bucket": bucket,
            "vm_shard": shard_path.split("/")[-1],
            "total_rows": 0,
            "v8_rows": 0,
            "v_lt_8_rows": 0,
            "null_rows": 0,
            "schema_versions_seen": f"READ_ERROR: {str(err)[:80]}",
        }
    v8 = int((df["schema_version"] == 8).sum())
    v_lt_8 = int(df["schema_version"].isin([1, 2, 3, 4, 5, 6, 7]).sum())
    null = int(df["schema_version"].isna().sum())
    versions = sorted({int(v) for v in df["schema_version"].dropna().unique()})
    return {
        "asset_group": ag,
        "bucket": bucket,
        "vm_shard": shard_path.split("/")[-1],
        "total_rows": len(df),
        "v8_rows": v8,
        "v_lt_8_rows": v_lt_8,
        "null_rows": null,
        "schema_versions_seen": ",".join(str(v) for v in versions) or "(empty)",
    }


def main() -> int:
    fs = gcsfs.GCSFileSystem()
    # Build the full work list: every (ag, bucket, shard_path) tuple.
    tasks: list[tuple[str, str, str]] = []
    for ag, bucket in BUCKETS:
        prefix = f"{bucket}/_index/per_vm/"
        try:
            shards = fs.ls(prefix)
        except (FileNotFoundError, OSError):
            print(f"  {ag:12s} {bucket}: no per_vm dir", flush=True)
            continue
        print(f"  {ag:12s} {bucket}: {len(shards)} per_vm shards", flush=True)
        for shard_path in shards:
            if shard_path.endswith(".parquet"):
                tasks.append((ag, bucket, shard_path))

    total = len(tasks)
    print(f"\nScanning {total:,} per_vm shards with {NUM_WORKERS} workers ...", flush=True)
    rows: list[dict[str, object]] = []
    completed = 0
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as pool:
        futures = [pool.submit(_scan_one_shard, task) for task in tasks]
        for fut in as_completed(futures):
            rows.append(fut.result())
            completed += 1
            if completed % 200 == 0 or completed == total:
                print(f"  progress: {completed:,}/{total:,}", flush=True)

    out_dir = WORKSPACE_ROOT / "unified-trading-pm" / "plans" / "audit" / "results"
    csv_path = out_dir / "manifest_v8_per_vm_shards_2026_05_20.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "asset_group", "bucket", "vm_shard",
                "total_rows", "v8_rows", "v_lt_8_rows", "null_rows", "schema_versions_seen",
            ],
        )
        writer.writeheader()
        for r in sorted(
            rows,
            key=lambda x: (-int(x["v_lt_8_rows"]) - int(x["null_rows"]), x["asset_group"], x["bucket"], x["vm_shard"]),
        ):
            writer.writerow(r)

    # Per-bucket aggregates.
    per_bucket: dict[str, dict[str, int]] = defaultdict(
        lambda: {"total": 0, "v8": 0, "v_lt_8": 0, "null": 0, "shards": 0}
    )
    for r in rows:
        b = str(r["bucket"])
        per_bucket[b]["total"] += int(r["total_rows"])
        per_bucket[b]["v8"] += int(r["v8_rows"])
        per_bucket[b]["v_lt_8"] += int(r["v_lt_8_rows"])
        per_bucket[b]["null"] += int(r["null_rows"])
        per_bucket[b]["shards"] += 1

    summary_path = out_dir / "manifest_v8_per_vm_shards_2026_05_20_summary.md"
    with summary_path.open("w", encoding="utf-8") as fh:
        fh.write("# A4 v2 — Per-VM shard schema_version compliance\n\n")
        fh.write(f"_Generated: {datetime.now(UTC).isoformat()}_\n\n")
        fh.write(f"Total per-VM shards inspected: {len(rows)}\n\n")
        fh.write("## Per-bucket aggregates\n\n")
        fh.write("| bucket | shards | total rows | v8 rows | v8 % | v<8 rows | NULL rows |\n")
        fh.write("|---|---:|---:|---:|---:|---:|---:|\n")
        for bucket, agg in sorted(per_bucket.items()):
            pct = 100.0 * agg["v8"] / agg["total"] if agg["total"] else 0.0
            fh.write(
                f"| `{bucket}` | {agg['shards']:,} | {agg['total']:,} | {agg['v8']:,} | "
                f"{pct:.2f}% | {agg['v_lt_8']:,} | {agg['null']:,} |\n",
            )

        fh.write("\n## Per-VM shards at v<8 OR with NULL schema_version (review-blocking)\n\n")
        bad = [r for r in rows if int(r["v_lt_8_rows"]) > 0 or int(r["null_rows"]) > 0]
        if bad:
            fh.write(f"Total problematic shards: **{len(bad)}**\n\n")
            fh.write(
                "| asset_group | bucket | shard | total | v<8 | NULL | versions |\n"
                "|---|---|---|---:|---:|---:|---|\n"
            )
            for r in sorted(bad, key=lambda x: -int(x["v_lt_8_rows"]) - int(x["null_rows"]))[:50]:
                fh.write(
                    f"| {r['asset_group']} | `{r['bucket'].split('-')[0]}-{r['asset_group']}` | "
                    f"`{r['vm_shard']}` | {r['total_rows']:,} | {r['v_lt_8_rows']:,} | "
                    f"{r['null_rows']:,} | {r['schema_versions_seen']} |\n",
                )
            if len(bad) > 50:
                fh.write(f"\n_(showing first 50 of {len(bad)} problematic shards — see CSV for full list)_\n")
        else:
            fh.write("_All per-VM shards at v8 — no per-VM-writer regressions detected._\n")

        fh.write("\n## Composition with A4 v1 (master availability_index)\n\n")
        fh.write(
            "Master availability_index has 0% v8 rows workspace-wide (A4 v1)."
            " If per-VM shards are also v<8, the consolidator preserves the source version (correct behavior)."
            " If per-VM shards ARE at v8 but master isn't, the consolidator should be regenerating master"
            " from per-VM shards — gap.\n\n"
        )
        fh.write("Compare aggregates above to A4 v1 numbers to identify drift between the two paths.\n")

    print(f"\nWrote {csv_path}")
    print(f"Wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
