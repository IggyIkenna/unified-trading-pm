"""Fix bad start dates: phantom `captured` rows dated BEFORE the chain genesis.

Operator 2026-06-01 ("fix all these bad start dates"). Found: 8,477 index rows marked
`capture_status='captured'` for a (chain, date) that predates the chain's UAC genesis — the
chain did not exist, there are NO backing objects (verified: dex-pools day=2021-06-01 prefix
absent), so the captured status is false and inflates coverage. Fix = relabel to the honest
state `empty_confirmed` / `EXPECTED_PRE_GENESIS_CHAIN`. Provably safe: only touches rows where
date < chain genesis (impossible to have real data). Index-layer only, snapshot, retry.

NOTE: this fixes only the PROVABLE pre-genesis phantoms. Whether the *rest* of the dex `captured`
rows are object-backed (the uniform 2021-01-01 first-captured is suspicious) is a separate, bigger
audit — tracked as a plan todo, not done here.

Run:  .venv-workspace/bin/python <this>            # dry-run
      .venv-workspace/bin/python <this> --apply
"""

from __future__ import annotations

import sys
import time

import gcsfs
import pandas as pd

from unified_api_contracts.registry.chain_env import get_chain_genesis_date

PROJECT_ID = "central-element-323112"
BUCKETS = {
    "oracle-prices": f"oracle-prices-{PROJECT_ID}",
    "dex-pools": f"dex-pools-prd-{PROJECT_ID}",
    "dex-swaps": f"dex-swaps-prd-{PROJECT_ID}",
}
SNAP = "_index/snapshots/pre_phantom_captured_fix_2026_06_01.parquet"


def _read_retry(fs, path, tries=6):
    last = None
    for i in range(tries):
        try:
            return pd.read_parquet(fs.open(path))
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(1.5 * (i + 1))
    raise last  # type: ignore[misc]


def main() -> int:
    apply = "--apply" in sys.argv
    fs = gcsfs.GCSFileSystem()
    total = 0
    for name, bucket in BUCKETS.items():
        index = f"{bucket}/_index/availability_index.parquet"
        try:
            df = _read_retry(fs, index)
        except Exception as exc:  # noqa: BLE001
            print(f"{name}: SKIP after retries ({type(exc).__name__})")
            continue
        df = df[[c for c in df.columns if not c.startswith("__")]].copy()
        if not {"chain", "capture_status", "date"} <= set(df.columns):
            print(f"{name}: SKIP (missing cols)")
            continue
        ds = df["date"].astype(str).str.slice(0, 10)
        gen = df["chain"].astype(str).map(lambda c: get_chain_genesis_date(c) or "")
        mask = (df["capture_status"] == "captured") & (gen != "") & (ds < gen)
        n = int(mask.sum())
        total += n
        bd = df[mask].groupby("chain").size().to_dict() if n else {}
        print(f"{name}: {n} phantom captured-pre-genesis -> empty_confirmed/EXPECTED_PRE_GENESIS_CHAIN  {bd}")
        if apply and n:
            orig = _read_retry(fs, index)
            orig.to_parquet(fs.open(f"{bucket}/{SNAP}", "wb"), index=False)
            df.loc[mask, "capture_status"] = "empty_confirmed"
            df.loc[mask, "error_reason"] = "EXPECTED_PRE_GENESIS_CHAIN"
            if "available" in df.columns:
                df.loc[mask, "available"] = False
            if "row_count" in df.columns:
                df.loc[mask, "row_count"] = 0
            df.to_parquet(fs.open(index, "wb"), index=False)
            print(f"  -> snapshotted + wrote {index}")
    print(f"\nTOTAL phantom captured-pre-genesis fixed: {total}{'  (DRY-RUN)' if not apply else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
