"""C11 — captured-vs-objects walk: find `captured` index rows with NO backing GCS object.

Operator 2026-06-01. The dex backfill's uniform 2021-01-01 first-captured suggested some `captured`
rows may be enumerated without object-backing. This walks the dedicated dex buckets: lists every
object, parses (venue, chain, day), builds the backed-set, and flags any `captured` index row whose
(venue, chain, date) has NO object = phantom. Dry-run reports counts + sample; --apply relabels
phantoms to `empty_confirmed/SOURCE_RETURNED_ZERO` (honest: claimed captured, no data present).
Snapshot, retry, idempotent. (Date-impossible phantoms already fixed by C10/C10b.)

Run:  .venv-workspace/bin/python <this> [bucket-key]            # dry-run (default dex-pools)
      .venv-workspace/bin/python <this> [bucket-key] --apply
"""

from __future__ import annotations

import sys
import time

import gcsfs
import pandas as pd

PROJECT_ID = "central-element-323112"
BUCKETS = {
    "dex-pools": f"dex-pools-prd-{PROJECT_ID}",
    "dex-swaps": f"dex-swaps-prd-{PROJECT_ID}",
}
SNAP = "_index/snapshots/pre_captured_vs_objects_2026_06_01.parquet"


def _retry(fn, tries=6):
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as exc:
            last = exc
            time.sleep(1.5 * (i + 1))
    raise last  # type: ignore[misc]


import re as _re


def _norm_venue(v: str) -> str:
    """Normalise venue for comparison: index uses `UNISWAPV3`, objects use `UNISWAP_V3`.
    Insert `_` before a trailing version token (V2/V3/V4) so both sides match."""
    return _re.sub(r"(?<=[A-Z])(V\d)$", r"_\1", str(v).upper())


def _parse(rel: str) -> tuple[str, str, str] | None:
    kv = {}
    for seg in rel.split("/"):
        if "=" in seg:
            k, v = seg.split("=", 1)
            kv[k] = v
    day, venue, chain = kv.get("day"), kv.get("venue"), kv.get("chain")
    if day and venue:
        return (_norm_venue(venue), chain or "", day)
    return None


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    key = args[0] if args else "dex-pools"
    apply = "--apply" in sys.argv
    bucket = BUCKETS[key]
    fs = gcsfs.GCSFileSystem()
    print(f"walking gs://{bucket}/ objects (server-side list, retry) ...", flush=True)
    objs = _retry(lambda: fs.find(bucket))
    parquets = [o for o in objs if o.endswith(".parquet") and "/_index/" not in o and "/snapshots/" not in o]
    backed = set()
    for o in parquets:
        p = _parse(o[len(bucket) + 1 :])
        if p:
            backed.add(p)
    print(f"  {len(parquets):,} objects -> {len(backed):,} distinct (venue,chain,day) backed cells")
    index = f"{bucket}/_index/availability_index.parquet"
    df = _retry(lambda: pd.read_parquet(fs.open(index)))
    df = df[[c for c in df.columns if not c.startswith("__")]].copy()
    ds = df["date"].astype(str).str.slice(0, 10)
    cap = df["capture_status"] == "captured"
    key_tuples = list(zip(df["venue"].map(_norm_venue), df["chain"].astype(str), ds, strict=False))
    has_obj = pd.Series([t in backed for t in key_tuples], index=df.index)
    phantom = cap & ~has_obj
    n = int(phantom.sum())
    print(f"\ncaptured rows: {int(cap.sum()):,}  | captured WITHOUT backing object (phantom): {n:,}")
    if n:
        print("  by venue/chain (top):")
        print(df[phantom].groupby([df["venue"], df["chain"]]).size().sort_values(ascending=False).head(12).to_string())
    if apply and n:
        orig = _retry(lambda: pd.read_parquet(fs.open(index)))
        orig.to_parquet(fs.open(f"{bucket}/{SNAP}", "wb"), index=False)
        df.loc[phantom, ["capture_status", "error_reason"]] = ["empty_confirmed", "SOURCE_RETURNED_ZERO"]
        for col, val in (("available", False), ("row_count", 0)):
            if col in df.columns:
                df.loc[phantom, col] = val
        df.to_parquet(fs.open(index, "wb"), index=False)
        print(f"  -> snapshotted + wrote {index}")
    elif n:
        print("\n  DRY-RUN — re-run with --apply to relabel phantoms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
