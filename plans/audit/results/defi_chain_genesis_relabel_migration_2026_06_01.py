"""C7-partial: chain-genesis reason relabel across ALL dedicated DeFi bucket indexes.

Generalises the proven C1 oracle relabel: for each dedicated DeFi bucket, any
`empty_confirmed` row whose (chain, date) predates the chain's UAC genesis but is tagged
SOURCE_RETURNED_ZERO / blank → relabel to EXPECTED_PRE_GENESIS_CHAIN. Index-layer only,
snapshot before write, idempotent. Chain-genesis is the only input (in UAC) — the
venue/protocol-launch relabel (PACIFICA/ASTER/LST pre-launch) stays a separate item (A2a,
needs DEFI_VENUE_LAUNCH_DATES populated). oracle-prices already done by C1 — skipped here.

Run:  .venv-workspace/bin/python <this>            # dry-run all buckets
      .venv-workspace/bin/python <this> --apply    # snapshot + write
"""

from __future__ import annotations

import sys
import time

import gcsfs
import pandas as pd
from unified_api_contracts.registry.chain_env import get_chain_genesis_date


def _read_retry(fs: gcsfs.GCSFileSystem, path: str, tries: int = 6):
    """Retry reads — gcsfs's first GCS requests after init hit a cold DNS/connection
    that times out, then warms up; retry absorbs that warmup artifact."""
    last: Exception | None = None
    for attempt in range(tries):
        try:
            return pd.read_parquet(fs.open(path))
        except Exception as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise last  # type: ignore[misc]


PROJECT_ID = "central-element-323112"
# oracle-prices excluded — already migrated by C1.
BUCKETS = {
    "lst-rates": f"lst-rates-{PROJECT_ID}",
    "lending-indices": f"lending-indices-{PROJECT_ID}",
    "perp-funding": f"perp-funding-{PROJECT_ID}",
    "dex-pools": f"dex-pools-prd-{PROJECT_ID}",
    "dex-swaps": f"dex-swaps-prd-{PROJECT_ID}",
}
SNAP = "_index/snapshots/pre_chain_genesis_relabel_2026_06_01.parquet"


def main() -> int:
    apply = "--apply" in sys.argv
    fs = gcsfs.GCSFileSystem()
    total = 0
    for name, bucket in BUCKETS.items():
        index = f"{bucket}/_index/availability_index.parquet"
        try:
            df = _read_retry(fs, index)
        except Exception as exc:
            print(f"{name}: SKIP after retries ({type(exc).__name__})")
            continue
        df = df[[c for c in df.columns if not c.startswith("__")]].copy()
        if "chain" not in df.columns or "capture_status" not in df.columns:
            print(f"{name}: SKIP (no chain/capture_status)")
            continue
        date_str = df["date"].astype(str).str.slice(0, 10)
        genesis = df["chain"].astype(str).map(lambda c: get_chain_genesis_date(c) or "")
        pre = (genesis != "") & (date_str < genesis)
        mask = (
            (df["capture_status"] == "empty_confirmed")
            & pre
            & (df.get("error_reason", pd.Series([""] * len(df))).fillna("") != "EXPECTED_PRE_GENESIS_CHAIN")
        )
        n = int(mask.sum())
        total += n
        breakdown = (
            df[mask]
            .groupby([df["chain"], df.get("error_reason", pd.Series([""] * len(df))).fillna("<blank>")])
            .size()
            .to_dict()
            if n
            else {}
        )
        print(f"{name}: {n} pre-genesis relabels  {breakdown}")
        if apply and n:
            orig = pd.read_parquet(fs.open(index))
            orig.to_parquet(fs.open(f"{bucket}/{SNAP}", "wb"), index=False)
            df.loc[mask, "error_reason"] = "EXPECTED_PRE_GENESIS_CHAIN"
            df.to_parquet(fs.open(index, "wb"), index=False)
            print(f"  -> snapshotted + wrote {index}")
    print(f"\nTOTAL pre-genesis relabels: {total}{'  (DRY-RUN — re-run with --apply)' if not apply else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
