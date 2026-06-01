"""C7 venue-launch portion: relabel genuinely-pre-venue-launch empties → EXPECTED_PRE_VENUE_LAUNCH.

Operator 2026-06-01: "pre venue launch needs to be captured in UAC if genuinely pre venue and
migrated in manifest to use right naming." For each dedicated DeFi bucket index, an
`empty_confirmed` row tagged `SOURCE_RETURNED_ZERO`/blank whose date predates the venue's UAC
launch date (`DEFI_VENUE_LAUNCH_DATES[{venue}-{chain}]`) is genuinely pre-venue → relabel
`EXPECTED_PRE_VENUE_LAUNCH`. Uses EXISTING UAC data (no guessing). Venues with pre-launch-looking
empties but NO UAC launch date are REPORTED (need adding to UAC — e.g. perp PACIFICA/ASTER/LIGHTER).
Index-layer only, snapshot-protected, idempotent, warmup-retry. Chain-genesis already done (C1/C7).

Run:  .venv-workspace/bin/python <this>            # dry-run all buckets
      .venv-workspace/bin/python <this> --apply
"""

from __future__ import annotations

import sys
import time
from collections import Counter

import gcsfs
import pandas as pd

from unified_api_contracts.registry.venue_launch_dates import DEFI_VENUE_LAUNCH_DATES

PROJECT_ID = "central-element-323112"
BUCKETS = {
    "lst-rates": f"lst-rates-{PROJECT_ID}",
    "lending-indices": f"lending-indices-{PROJECT_ID}",
    "perp-funding": f"perp-funding-{PROJECT_ID}",
    "dex-pools": f"dex-pools-prd-{PROJECT_ID}",
    "dex-swaps": f"dex-swaps-prd-{PROJECT_ID}",
}
SNAP = "_index/snapshots/pre_venue_launch_relabel_2026_06_01.parquet"
_RELABEL_FROM = {"SOURCE_RETURNED_ZERO", "", None}


def _read_retry(fs, path, tries=6):
    last = None
    for i in range(tries):
        try:
            return pd.read_parquet(fs.open(path))
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5 * (i + 1))
    raise last  # type: ignore[misc]


def _launch(venue: str, chain: str) -> str | None:
    return DEFI_VENUE_LAUNCH_DATES.get(f"{venue}-{chain}") or DEFI_VENUE_LAUNCH_DATES.get(venue)


def main() -> int:
    apply = "--apply" in sys.argv
    fs = gcsfs.GCSFileSystem()
    total = 0
    missing_uac: Counter = Counter()
    for name, bucket in BUCKETS.items():
        index = f"{bucket}/_index/availability_index.parquet"
        try:
            df = _read_retry(fs, index)
        except Exception as exc:  # noqa: BLE001
            print(f"{name}: SKIP after retries ({type(exc).__name__})")
            continue
        df = df[[c for c in df.columns if not c.startswith("__")]].copy()
        if not {"venue", "chain", "capture_status", "date"} <= set(df.columns):
            print(f"{name}: SKIP (missing cols)")
            continue
        date_str = df["date"].astype(str).str.slice(0, 10)
        reason = df.get("error_reason", pd.Series([""] * len(df))).fillna("")
        launch = [_launch(str(v), str(c)) for v, c in zip(df["venue"], df["chain"], strict=False)]
        launch_s = pd.Series(launch, index=df.index)
        mask = (
            (df["capture_status"] == "empty_confirmed")
            & reason.isin(_RELABEL_FROM)
            & launch_s.notna()
            & (date_str < launch_s.fillna("9999"))
        )
        # report venues with pre-launch-looking empties but NO UAC launch date
        no_uac = (
            (df["capture_status"] == "empty_confirmed") & reason.isin(_RELABEL_FROM) & launch_s.isna()
        )
        for v, c in zip(df.loc[no_uac, "venue"], df.loc[no_uac, "chain"], strict=False):
            missing_uac[f"{v}-{c}"] += 1
        n = int(mask.sum())
        total += n
        bd = df[mask].groupby([df["venue"], df["chain"]]).size().to_dict() if n else {}
        print(f"{name}: {n} venue-launch relabels  {bd}")
        if apply and n:
            orig = _read_retry(fs, index)
            orig.to_parquet(fs.open(f"{bucket}/{SNAP}", "wb"), index=False)
            df.loc[mask, "error_reason"] = "EXPECTED_PRE_VENUE_LAUNCH"
            df.to_parquet(fs.open(index, "wb"), index=False)
            print(f"  -> snapshotted + wrote {index}")
    print(f"\nTOTAL venue-launch relabels: {total}{'  (DRY-RUN)' if not apply else ''}")
    print(f"\nVenues with pre-launch empties but NO UAC launch date (ADD to DEFI_VENUE_LAUNCH_DATES):")
    for k, v in missing_uac.most_common():
        print(f"  {k}: {v} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
