"""Fix ALL pre-existence bad labelling: `captured` rows dated before the venue/chain existed.

Operator 2026-06-01 ("fix this so we don't have bad labelling for pre genesis"). Comprehensive
complement to C10 (which did chain-genesis only): a `captured` row whose date predates EITHER
  - the chain's UAC genesis (`get_chain_genesis_date`)  -> EXPECTED_PRE_GENESIS_CHAIN, OR
  - the venue's UAC launch  (`DEFI_VENUE_LAUNCH_DATES[{venue}-{chain}]`) -> EXPECTED_PRE_VENUE_LAUNCH
is impossible (the data could not have existed) -> relabel `empty_confirmed` + typed reason.
Index-layer only, snapshot, retry, idempotent. Chain-genesis already cleared by C10 — this run
mainly catches captured-before-VENUE-launch. (Post-launch object-backing phantoms = C11/VM walk.)

Run:  .venv-workspace/bin/python <this>            # dry-run
      .venv-workspace/bin/python <this> --apply
"""

from __future__ import annotations

import sys
import time

import gcsfs
import pandas as pd
from unified_api_contracts.registry.chain_env import get_chain_genesis_date
from unified_api_contracts.registry.venue_launch_dates import DEFI_VENUE_LAUNCH_DATES

PROJECT_ID = "central-element-323112"
BUCKETS = {
    "lst-rates": f"lst-rates-{PROJECT_ID}",
    "lending-indices": f"lending-indices-{PROJECT_ID}",
    "oracle-prices": f"oracle-prices-{PROJECT_ID}",
    "perp-funding": f"perp-funding-{PROJECT_ID}",
    "dex-pools": f"dex-pools-prd-{PROJECT_ID}",
    "dex-swaps": f"dex-swaps-prd-{PROJECT_ID}",
}
SNAP = "_index/snapshots/pre_captured_pre_existence_fix_2026_06_01.parquet"


def _read_retry(fs, path, tries=6):
    last = None
    for i in range(tries):
        try:
            return pd.read_parquet(fs.open(path))
        except Exception as exc:
            last = exc
            time.sleep(1.5 * (i + 1))
    raise last  # type: ignore[misc]


def _launch(venue: str, chain: str) -> str | None:
    return DEFI_VENUE_LAUNCH_DATES.get(f"{venue}-{chain}") or DEFI_VENUE_LAUNCH_DATES.get(venue)


def main() -> int:
    apply = "--apply" in sys.argv
    fs = gcsfs.GCSFileSystem()
    total_gen = total_launch = 0
    for name, bucket in BUCKETS.items():
        index = f"{bucket}/_index/availability_index.parquet"
        try:
            df = _read_retry(fs, index)
        except Exception as exc:
            print(f"{name}: SKIP after retries ({type(exc).__name__})")
            continue
        df = df[[c for c in df.columns if not c.startswith("__")]].copy()
        if not {"venue", "chain", "capture_status", "date"} <= set(df.columns):
            print(f"{name}: SKIP (missing cols)")
            continue
        ds = df["date"].astype(str).str.slice(0, 10)
        cap = df["capture_status"] == "captured"
        gen = df["chain"].astype(str).map(lambda c: get_chain_genesis_date(c) or "")
        launch = pd.Series(
            [_launch(str(v), str(c)) for v, c in zip(df["venue"], df["chain"], strict=False)], index=df.index
        )
        pre_gen = cap & (gen != "") & (ds < gen)
        pre_launch = cap & ~pre_gen & launch.notna() & (ds < launch.fillna("9999"))
        ng, nl = int(pre_gen.sum()), int(pre_launch.sum())
        total_gen += ng
        total_launch += nl
        bd = df[pre_launch].groupby([df["venue"], df["chain"]]).size().to_dict() if nl else {}
        print(f"{name}: pre-genesis-captured={ng}  pre-venue-launch-captured={nl}  {bd}")
        if apply and (ng or nl):
            orig = _read_retry(fs, index)
            orig.to_parquet(fs.open(f"{bucket}/{SNAP}", "wb"), index=False)
            df.loc[pre_gen, ["capture_status", "error_reason"]] = ["empty_confirmed", "EXPECTED_PRE_GENESIS_CHAIN"]
            df.loc[pre_launch, ["capture_status", "error_reason"]] = ["empty_confirmed", "EXPECTED_PRE_VENUE_LAUNCH"]
            for col, val in (("available", False), ("row_count", 0)):
                if col in df.columns:
                    df.loc[pre_gen | pre_launch, col] = val
            df.to_parquet(fs.open(index, "wb"), index=False)
            print(f"  -> snapshotted + wrote {index}")
    print(
        f"\nTOTAL pre-genesis-captured={total_gen}  pre-venue-launch-captured={total_launch}{'  (DRY-RUN)' if not apply else ''}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
