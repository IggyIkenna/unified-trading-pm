"""C3 venue-canonicalisation: migrate the manifest INDEX venue strings to the canonical form.

Operator 2026-06-01: "normalising venue names in code is a fallback and causes issues downstream"
— so MIGRATE the data, don't transform at read time. The index uses non-canonical venue strings
(`UNISWAPV3`) while the GCS objects + UAC `ALL_DEFI_VENUES` use the canonical `UNISWAP_V3`. This
one-time migration rewrites the index `venue` column to the canonical value, sourced AUTHORITATIVELY
from the actual object venue strings (ground truth), so index↔object joins work and nothing has to
normalise at runtime. Snapshot, retry, idempotent.

Run:  .venv-workspace/bin/python <this> [bucket-key]            # dry-run (default dex-pools)
      .venv-workspace/bin/python <this> [bucket-key] --apply
"""

from __future__ import annotations

import re
import sys
import time

import gcsfs
import pandas as pd

PROJECT_ID = "central-element-323112"
BUCKETS = {
    "dex-pools": f"dex-pools-prd-{PROJECT_ID}",
    "dex-swaps": f"dex-swaps-prd-{PROJECT_ID}",
}
SNAP = "_index/snapshots/pre_index_venue_canonicalise_2026_06_01.parquet"


def _retry(fn, tries=6):
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as exc:
            last = exc
            time.sleep(1.5 * (i + 1))
    raise last  # type: ignore[misc]


def _key(v: str) -> str:
    """Comparison key to MATCH an index venue to an object venue (build the map only —
    the migration writes the explicit object string, not this key)."""
    return re.sub(r"[^A-Z0-9]", "", str(v).upper())


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    key = args[0] if args else "dex-pools"
    apply = "--apply" in sys.argv
    bucket = BUCKETS[key]
    fs = gcsfs.GCSFileSystem()

    # 1. canonical object venues (ground truth) — sample a spread of days
    print(f"sampling object venues in gs://{bucket}/ ...", flush=True)
    days = [d for d in _retry(lambda: fs.ls(bucket, detail=False)) if "/day=" in d]
    obj_venues: set[str] = set()
    for d in days[:: max(1, len(days) // 30)]:  # ~30 sampled days
        for o in _retry(lambda dd=d: fs.find(dd)):
            m = re.search(r"venue=([^/]+)", o)
            if m:
                obj_venues.add(m.group(1))
    obj_by_key = {_key(v): v for v in obj_venues}
    print(f"  canonical object venues: {sorted(obj_venues)}")

    # 2. index venues + build explicit map index_venue -> canonical object venue
    index = f"{bucket}/_index/availability_index.parquet"
    df = _retry(lambda: pd.read_parquet(fs.open(index)))
    df = df[[c for c in df.columns if not c.startswith("__")]].copy()
    vmap = {}
    for iv in sorted(df["venue"].astype(str).unique()):
        canon = obj_by_key.get(_key(iv))
        if canon and canon != iv:
            vmap[iv] = canon
    print(f"\n  index venues needing migration ({len(vmap)}):")
    for k, v in vmap.items():
        print(f"    {k} -> {v}  ({int((df['venue'].astype(str) == k).sum()):,} rows)")
    unmatched = [iv for iv in df["venue"].astype(str).unique() if _key(iv) not in obj_by_key]
    if unmatched:
        print(f"  WARNING unmatched index venues (no object venue — investigate): {unmatched}")

    if not vmap:
        print("\n  nothing to migrate")
        return 0
    if not apply:
        print("\n  DRY-RUN — re-run with --apply")
        return 0
    orig = _retry(lambda: pd.read_parquet(fs.open(index)))
    orig.to_parquet(fs.open(f"{bucket}/{SNAP}", "wb"), index=False)
    df["venue"] = df["venue"].astype(str).map(lambda v: vmap.get(v, v))
    df.to_parquet(fs.open(index, "wb"), index=False)
    print(f"\n  APPLIED — snapshotted + wrote {index}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
