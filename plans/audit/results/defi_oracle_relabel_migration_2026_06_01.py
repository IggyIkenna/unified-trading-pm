"""Oracle-prices manifest-index remediation (defi_master_audit_2026_06_01).

Two targeted, idempotent fixes to gs://oracle-prices-<pid>/_index/availability_index.parquet:

  M1 — Pre-genesis relabel: empty_confirmed rows whose (chain, date) predates the chain's
       UAC genesis but are tagged SOURCE_RETURNED_ZERO / blank -> EXPECTED_PRE_GENESIS_CHAIN.
       (The writer is now fixed @mtds 840d85f1; this corrects the legacy back-data.)
  M2 — Pyth chain dedup: captured Pyth rows recorded under chain='' (legacy) -> chain='SOLANA'
       (object ground-truth is venue=PYTH/chain=SOLANA); then drop the now-duplicate
       (PYTH, SOLANA, date) empty_confirmed phantom rows where a captured row exists.

Snapshots the original index to _index/snapshots/ before writing. Dry-run by default.
Run:  .venv-workspace/bin/python <this>            # dry-run
      .venv-workspace/bin/python <this> --apply    # write back (after snapshot)
"""

from __future__ import annotations

import sys

import gcsfs
import pandas as pd
from unified_api_contracts.registry.chain_env import get_chain_genesis_date

PROJECT_ID = "central-element-323112"
BUCKET = f"oracle-prices-{PROJECT_ID}"
INDEX = f"{BUCKET}/_index/availability_index.parquet"
SNAPSHOT = f"{BUCKET}/_index/snapshots/pre_relabel_2026_06_01.parquet"


def main() -> int:
    apply = "--apply" in sys.argv
    fs = gcsfs.GCSFileSystem()
    df = pd.read_parquet(fs.open(INDEX))
    df = df[[c for c in df.columns if not c.startswith("__")]].copy()
    n0 = len(df)
    date_str = df["date"].astype(str).str.slice(0, 10)

    # ── M1: pre-genesis relabel ────────────────────────────────────────────
    genesis = df["chain"].astype(str).map(lambda c: get_chain_genesis_date(c) or "")
    pre_genesis = (genesis != "") & (date_str < genesis)
    m1 = (
        (df["capture_status"] == "empty_confirmed")
        & pre_genesis
        & (df["error_reason"].fillna("") != "EXPECTED_PRE_GENESIS_CHAIN")
    )
    print(f"M1 pre-genesis relabel: {int(m1.sum())} rows")
    print(df[m1].groupby(["venue", "chain", df["error_reason"].fillna("<blank>")]).size().to_string())
    df.loc[m1, "error_reason"] = "EXPECTED_PRE_GENESIS_CHAIN"

    # ── M2: Pyth chain='' captured -> SOLANA, then drop duplicate empties ──
    pyth_blank_cap = (df["venue"] == "PYTH") & (df["chain"].astype(str) == "") & (df["capture_status"] == "captured")
    relabel_dates = set(date_str[pyth_blank_cap])
    print(f"\nM2a Pyth chain ''->SOLANA on captured rows: {int(pyth_blank_cap.sum())}")
    df.loc[pyth_blank_cap, "chain"] = "SOLANA"

    # after relabel, drop (PYTH, SOLANA, date) empty rows that now duplicate a captured row
    date_str2 = df["date"].astype(str).str.slice(0, 10)
    dup_empty = (
        (df["venue"] == "PYTH")
        & (df["chain"] == "SOLANA")
        & (df["capture_status"] == "empty_confirmed")
        & date_str2.isin(relabel_dates)
    )
    print(f"M2b drop duplicate PYTH/SOLANA empty rows (captured now exists same date): {int(dup_empty.sum())}")
    df = df[~dup_empty].reset_index(drop=True)

    print(f"\nrows: {n0} -> {len(df)}  (net {len(df) - n0})")
    print("PYTH chain dist after:", df[df.venue == "PYTH"].chain.value_counts(dropna=False).to_dict())

    if not apply:
        print("\nDRY-RUN — no write. Re-run with --apply to snapshot + write back.")
        return 0

    # snapshot original, then write corrected index
    orig = pd.read_parquet(fs.open(INDEX))
    orig.to_parquet(fs.open(SNAPSHOT, "wb"), index=False)
    print(f"\nSnapshotted original -> gs://{SNAPSHOT}")
    df.to_parquet(fs.open(INDEX, "wb"), index=False)
    print(f"Wrote corrected index -> gs://{INDEX}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
