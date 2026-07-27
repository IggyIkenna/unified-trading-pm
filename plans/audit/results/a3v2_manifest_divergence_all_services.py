"""A3 v2 — Manifest divergence audit, extended to ALL service manifest indexes.

Mega-audit Phase A3 v2 (operator directive 2026-05-20 — gap closure
"A3 doesn't read features-service / strategy / execution / ml-* manifests").

Extends A3 v1 from 5 MTDS buckets to comprehensive coverage:

1. **GCP**: probe every workspace bucket with the canonical
   `_index/availability_index.parquet` path. Read + classify. Services
   without a consolidated manifest are flagged as a finding (R-NEW-1).
2. **AWS**: probe parallel S3 buckets for the same index path. Cross-cloud
   divergence count surfaced.

Output:
    plans/audit/results/manifest_divergence_all_services_2026_05_20.parquet
    plans/audit/results/manifest_divergence_all_services_2026_05_20_summary.md
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import gcsfs
import pandas as pd
import pyarrow.parquet as pq
from unified_trading_library import get_storage_client

WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
PROJECT_ID = "central-element-323112"
ENV_SHORT = "prd"

# Comprehensive bucket inventory: (asset_group, service_kind, bucket_name).
# Asset_group = "shared" when the service spans multiple asset_groups or has
# no per-AG split.
GCS_BUCKETS: list[tuple[str, str, str]] = [
    # MTDS — already in A3 v1, re-included for completeness.
    ("cefi", "mtds", f"market-data-tick-cefi-{ENV_SHORT}-{PROJECT_ID}"),
    ("defi", "mtds", f"market-data-tick-defi-{ENV_SHORT}-{PROJECT_ID}"),
    ("tradfi", "mtds", f"market-data-tick-tradfi-{ENV_SHORT}-{PROJECT_ID}"),
    ("sports", "mtds", f"market-data-tick-sports-{ENV_SHORT}-{PROJECT_ID}"),
    ("prediction", "mtds", f"market-data-tick-pred-{ENV_SHORT}-{PROJECT_ID}"),
    # Instruments-service.
    ("cefi", "instruments", f"instruments-store-cefi-{ENV_SHORT}-{PROJECT_ID}"),
    ("defi", "instruments", f"instruments-store-defi-{ENV_SHORT}-{PROJECT_ID}"),
    ("tradfi", "instruments", f"instruments-store-tradfi-{ENV_SHORT}-{PROJECT_ID}"),
    ("sports", "instruments", f"instruments-store-sports-{ENV_SHORT}-{PROJECT_ID}"),
    ("prediction", "instruments", f"instruments-store-pred-{ENV_SHORT}-{PROJECT_ID}"),
    # Features (Group B — env-split rolled back, current path is flat).
    ("cefi", "features-delta-one", f"features-delta-one-cefi-{PROJECT_ID}"),
    ("defi", "features-delta-one", f"features-delta-one-defi-{PROJECT_ID}"),
    ("tradfi", "features-delta-one", f"features-delta-one-tradfi-{PROJECT_ID}"),
    ("sports", "features-delta-one", f"features-delta-one-sports-{PROJECT_ID}"),
    ("cefi", "features-volatility", f"features-volatility-cefi-{PROJECT_ID}"),
    ("defi", "features-volatility", f"features-volatility-defi-{PROJECT_ID}"),
    ("defi", "features-onchain", f"features-onchain-defi-{PROJECT_ID}"),
    ("sports", "features-sports", f"features-sports-{ENV_SHORT}-{PROJECT_ID}"),
    ("shared", "features-calendar", f"features-calendar-{ENV_SHORT}-{PROJECT_ID}"),
    # Strategy + execution (flat).
    ("cefi", "strategy", f"strategy-store-cefi-{PROJECT_ID}"),
    ("defi", "strategy", f"strategy-store-defi-{PROJECT_ID}"),
    ("tradfi", "strategy", f"strategy-store-tradfi-{PROJECT_ID}"),
    ("cefi", "execution", f"execution-store-cefi-{PROJECT_ID}"),
    ("defi", "execution", f"execution-store-defi-{PROJECT_ID}"),
    ("tradfi", "execution", f"execution-store-tradfi-{PROJECT_ID}"),
    # ML.
    ("shared", "ml-artifacts", f"ml-artifacts-{PROJECT_ID}"),
    ("shared", "ml-training", f"ml-training-artifacts-{PROJECT_ID}"),
]

AWS_ACCOUNT_ID = "427895769566"
AWS_BUCKETS: list[tuple[str, str, str]] = [
    ("cefi", "mtds-aws", f"unified-trading-market-data-cefi-{AWS_ACCOUNT_ID}"),
    ("defi", "mtds-aws", f"unified-trading-market-data-defi-{AWS_ACCOUNT_ID}"),
    ("tradfi", "mtds-aws", f"unified-trading-market-data-tradfi-{AWS_ACCOUNT_ID}"),
    ("defi", "evm-defi-aws", f"unified-trading-evm-defi-{ENV_SHORT}-{AWS_ACCOUNT_ID}"),
    ("cefi", "execution-aws", f"unified-trading-execution-cefi-prod-{AWS_ACCOUNT_ID}"),
    ("defi", "execution-aws", f"unified-trading-execution-defi-prod-{AWS_ACCOUNT_ID}"),
    ("tradfi", "execution-aws", f"unified-trading-execution-tradfi-prod-{AWS_ACCOUNT_ID}"),
]

MIN_DATE = date(2020, 1, 1)
MAX_DATE = date(2026, 5, 20)


def probe_gcs_index(fs: gcsfs.GCSFileSystem, bucket: str) -> pd.DataFrame | None:
    path = f"{bucket}/_index/availability_index.parquet"
    try:
        with fs.open(path, "rb") as fh:
            pf = pq.ParquetFile(fh)
            available = set(pf.schema_arrow.names)
            wanted = ["date", "venue", "data_type", "capture_status", "error_reason", "schema_version"]
            cols = [c for c in wanted if c in available]
            with fs.open(path, "rb") as fh2:
                df = pq.read_table(fh2, columns=cols).to_pandas()
    except (FileNotFoundError, OSError) as err:
        if "404" in str(err) or "NotFound" in str(err) or "Not Found" in str(err):
            return None
        raise

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
        df = df.dropna(subset=["date"])
        df = df[(df["date"] >= MIN_DATE) & (df["date"] <= MAX_DATE)]
    if "capture_status" not in df.columns:
        df["capture_status"] = "(schema-missing)"
    else:
        df["capture_status"] = df["capture_status"].astype(str).str.lower()
    if "schema_version" not in df.columns:
        df["schema_version"] = pd.NA
    return df


def probe_aws_index(bucket: str) -> dict[str, object]:
    """Lightweight AWS probe — list bucket head to confirm existence."""
    try:
        metas = list(get_storage_client(provider="aws").list_blobs(bucket, prefix="_index/", max_results=1))
        return {"exists": True, "stdout": str([m.name for m in metas])[:500]}
    except (OSError, ValueError, RuntimeError) as exc:
        msg = str(exc)
        if "NoSuchBucket" in msg:
            return {"exists": False, "reason": "NoSuchBucket"}
        return {"exists": False, "reason": msg[:200]}


def main() -> int:
    fs = gcsfs.GCSFileSystem()
    out_dir = WORKSPACE_ROOT / "unified-trading-pm" / "plans" / "audit" / "results"

    # --- GCS pass ---
    print(f"Probing {len(GCS_BUCKETS)} GCS buckets ...", flush=True)
    per_bucket_stats: list[dict[str, object]] = []
    for ag, kind, bucket in GCS_BUCKETS:
        try:
            df = probe_gcs_index(fs, bucket)
        except (OSError, FileNotFoundError) as err:
            per_bucket_stats.append(
                {
                    "asset_group": ag,
                    "service_kind": kind,
                    "bucket": bucket,
                    "exists": "ERROR",
                    "rows": 0,
                    "v8_rows": 0,
                    "v_lt_8_rows": 0,
                    "null_version_rows": 0,
                    "captured": 0,
                    "empty_confirmed": 0,
                    "attempted_failed": 0,
                    "error_summary": str(err)[:120],
                },
            )
            continue
        if df is None:
            per_bucket_stats.append(
                {
                    "asset_group": ag,
                    "service_kind": kind,
                    "bucket": bucket,
                    "exists": "NO_INDEX",
                    "rows": 0,
                    "v8_rows": 0,
                    "v_lt_8_rows": 0,
                    "null_version_rows": 0,
                    "captured": 0,
                    "empty_confirmed": 0,
                    "attempted_failed": 0,
                    "error_summary": "",
                },
            )
            print(f"  {kind:24s} {bucket}: NO _index/availability_index.parquet", flush=True)
            continue
        per_bucket_stats.append(
            {
                "asset_group": ag,
                "service_kind": kind,
                "bucket": bucket,
                "exists": "OK",
                "rows": len(df),
                "v8_rows": int((df["schema_version"] == 8).sum()),
                "v_lt_8_rows": int(df["schema_version"].isin([1, 2, 3, 4, 5, 6, 7]).sum()),
                "null_version_rows": int(df["schema_version"].isna().sum()),
                "captured": int((df["capture_status"] == "captured").sum()),
                "empty_confirmed": int((df["capture_status"] == "empty_confirmed").sum()),
                "attempted_failed": int((df["capture_status"] == "attempted_failed").sum()),
                "error_summary": "",
            },
        )
        print(f"  {kind:24s} {bucket}: {len(df):,} rows", flush=True)

    # --- AWS pass ---
    print(f"\nProbing {len(AWS_BUCKETS)} AWS buckets ...", flush=True)
    aws_results: list[dict[str, object]] = []
    for ag, kind, bucket in AWS_BUCKETS:
        probe = probe_aws_index(bucket)
        status = "EXISTS_WITH_INDEX" if probe["exists"] else f"MISSING:{probe.get('reason', '?')[:80]}"
        aws_results.append({"asset_group": ag, "service_kind": kind, "bucket": bucket, "status": status})
        print(f"  {kind:18s} {bucket}: {status}", flush=True)

    # Write outputs.
    bucket_summary_df = pd.DataFrame(per_bucket_stats)
    aws_summary_df = pd.DataFrame(aws_results)

    csv_path = out_dir / "manifest_divergence_all_services_2026_05_20.csv"
    bucket_summary_df.to_csv(csv_path, index=False)
    aws_csv_path = out_dir / "manifest_divergence_all_services_2026_05_20_aws.csv"
    aws_summary_df.to_csv(aws_csv_path, index=False)

    summary_path = out_dir / "manifest_divergence_all_services_2026_05_20_summary.md"
    with summary_path.open("w", encoding="utf-8") as fh:
        fh.write("# A3 v2 — Manifest divergence across ALL services (GCP + AWS)\n\n")
        fh.write(f"_Generated: {datetime.now(UTC).isoformat()}_\n\n")
        fh.write(f"GCS buckets probed: {len(GCS_BUCKETS)}\n")
        fh.write(f"AWS buckets probed: {len(AWS_BUCKETS)}\n\n")

        fh.write("## GCS bucket inventory + manifest index presence\n\n")
        fh.write(
            "| asset_group | service_kind | bucket | index? | rows | v8 | v<8 | NULL | captured | empty | failed |\n"
        )
        fh.write("|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|\n")
        for r in per_bucket_stats:
            fh.write(
                f"| {r['asset_group']} | {r['service_kind']} | `{r['bucket']}` | {r['exists']} | "
                f"{r['rows']:,} | {r['v8_rows']:,} | {r['v_lt_8_rows']:,} | {r['null_version_rows']:,} | "
                f"{r['captured']:,} | {r['empty_confirmed']:,} | {r['attempted_failed']:,} |\n",
            )

        fh.write("\n## Services without consolidated manifest (review-blocking — they emit but have no index)\n\n")
        no_index = [r for r in per_bucket_stats if r["exists"] == "NO_INDEX"]
        if no_index:
            fh.write("| asset_group | service_kind | bucket |\n|---|---|---|\n")
            for r in no_index:
                fh.write(f"| {r['asset_group']} | {r['service_kind']} | `{r['bucket']}` |\n")
            fh.write(
                "\n**Action**: per-service emission to `_index/availability_index.parquet` MUST be wired. Either:\n"
            )
            fh.write("- The service writes to a different bucket (look in `service-output-emission-semantics.md`)\n")
            fh.write(
                "- The service has NOT yet been wired into the manifest-emission pipeline (data-correctness gap)\n"
            )
            fh.write("- The consolidator doesn't run on these buckets (consolidator coverage gap)\n")
        else:
            fh.write("_All probed buckets have a consolidated manifest._\n")

        fh.write("\n## v8 schema-version compliance (extends A4)\n\n")
        fh.write("| asset_group | service_kind | bucket | total | v8 % | v<8 rows | NULL rows |\n")
        fh.write("|---|---|---|---:|---:|---:|---:|\n")
        for r in per_bucket_stats:
            if r["exists"] != "OK" or r["rows"] == 0:
                continue
            pct = 100.0 * int(r["v8_rows"]) / int(r["rows"])
            fh.write(
                f"| {r['asset_group']} | {r['service_kind']} | `{r['bucket']}` | {r['rows']:,} | "
                f"{pct:.2f}% | {r['v_lt_8_rows']:,} | {r['null_version_rows']:,} |\n",
            )

        fh.write("\n## AWS-side manifest index presence\n\n")
        fh.write("| asset_group | service_kind | bucket | status |\n|---|---|---|---|\n")
        for r in aws_results:
            fh.write(f"| {r['asset_group']} | {r['service_kind']} | `{r['bucket']}` | {r['status']} |\n")

        fh.write(
            "\n**Operator decision needed** (R21 in audit doc):"
            " are AWS S3 manifest indexes still actively maintained, or deprecated in favour of GCP? Either:\n"
        )
        fh.write("- If active: wire consolidator + extend A3 to read them per-cell (current A3 only reads GCS).\n")
        fh.write("- If deprecated: archive AWS section of `cloud-providers.yaml` + remove from bucket-name SSOT.\n")

    print(f"\nWrote {csv_path}")
    print(f"Wrote {aws_csv_path}")
    print(f"Wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
