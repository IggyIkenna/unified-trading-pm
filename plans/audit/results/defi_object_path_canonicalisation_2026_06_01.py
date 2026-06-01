"""C0/C2/C3/C9 object-level path canonicalisation for the dedicated DeFi buckets (DRY-RUN first).

Per the Sequencing gate: rewrite every legacy object path to the canonical layout so backfills
land correctly. Legacy:
  {kind}-{project}/day=YYYY-MM-DD/category=defi/venue=V/chain=C/instrument_type=T/data_type=D/file.parquet
Canonical (env-split + pipeline_mode + asset_group=):
  {kind}-prd-{project}/asset_group=defi/pipeline_mode=batch/day=YYYY-MM-DD/venue=V/chain=C/instrument_type=T/data_type=D'/file.parquet
  where D' = underscore-canonical data_type (lending-indices->lending_indices, dex-pools->dex_pools,
  dex-swaps->dex_swaps, staking_yields->lst_rates) and venue/chain are already flat in these buckets.

Copies are SERVER-SIDE (gcsfs `.copy`, GCS rewrite API) — data does not transit the local link, so a
flaky local DNS only affects the list/copy *call* (retried), not throughput. Dry-run prints the rewrite
plan + counts; --apply does the server-side copies (idempotent; originals left in place until a verified
cutover deletes them in a separate step). Snapshot/drain discipline applies before --apply at scale.

Run:  .venv-workspace/bin/python <this> <bucket-key>            # dry-run (default oracle-prices)
      .venv-workspace/bin/python <this> <bucket-key> --apply
"""

from __future__ import annotations

import sys
import time
from collections import Counter

import gcsfs

PROJECT_ID = "central-element-323112"
# bucket-key -> (legacy bucket, canonical -prd bucket, kind for asset_group derivation)
BUCKETS = {
    "oracle-prices": (f"oracle-prices-{PROJECT_ID}", f"oracle-prices-prd-{PROJECT_ID}"),
    "lst-rates": (f"lst-rates-{PROJECT_ID}", f"lst-rates-prd-{PROJECT_ID}"),
    "lending-indices": (f"lending-indices-{PROJECT_ID}", f"lending-indices-prd-{PROJECT_ID}"),
    "perp-funding": (f"perp-funding-{PROJECT_ID}", f"perp-funding-prd-{PROJECT_ID}"),
}
DATA_TYPE_CANON = {
    "lending-indices": "lending_indices",
    "dex-pools": "dex_pools",
    "dex-swaps": "dex_swaps",
    "staking_yields": "lst_rates",
}


def _retry(fn, *a, tries: int = 6):
    last: Exception | None = None
    for i in range(tries):
        try:
            return fn(*a)
        except Exception as exc:  # noqa: BLE001 — transient warmup
            last = exc
            time.sleep(1.5 * (i + 1))
    raise last  # type: ignore[misc]


def canonical_path(legacy_rel: str) -> str | None:
    """legacy_rel = path under the bucket. Return canonical rel path, or None if unparseable."""
    parts = [p for p in legacy_rel.split("/") if p]
    if not parts or not parts[-1].endswith(".parquet"):
        return None
    kv = {}
    for seg in parts[:-1]:
        if "=" in seg:
            k, v = seg.split("=", 1)
            kv[k] = v
    day = kv.get("day")
    if not day:
        return None
    ag = "defi"  # category=defi -> asset_group=defi
    dt = DATA_TYPE_CANON.get(kv.get("data_type", ""), kv.get("data_type", ""))
    venue = kv.get("venue", "")
    chain = kv.get("chain", "")
    itype = kv.get("instrument_type", "")
    fname = parts[-1]
    out = [f"asset_group={ag}", "pipeline_mode=batch", f"day={day}"]
    if venue:
        out.append(f"venue={venue}")
    if chain:
        out.append(f"chain={chain}")
    if itype:
        out.append(f"instrument_type={itype}")
    out.append(f"data_type={dt}")
    out.append(fname)
    return "/".join(out)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    key = args[0] if args else "oracle-prices"
    apply = "--apply" in sys.argv
    legacy_bucket, canon_bucket = BUCKETS[key]
    fs = gcsfs.GCSFileSystem()
    print(f"listing gs://{legacy_bucket}/ (server-side; data does not transit local) ...", flush=True)
    objs = _retry(lambda: fs.find(legacy_bucket))
    parquets = [o for o in objs if o.endswith(".parquet") and "/_index/" not in o and "/snapshots/" not in o]
    print(f"{len(parquets):,} data parquet objects (excl. _index/snapshots)")
    sample, rename_dt, unparseable = [], Counter(), 0
    for full in parquets:
        rel = full[len(legacy_bucket) + 1 :]
        canon = canonical_path(rel)
        if canon is None:
            unparseable += 1
            continue
        old_dt = rel.split("data_type=")[-1].split("/")[0] if "data_type=" in rel else "?"
        new_dt = canon.split("data_type=")[-1].split("/")[0]
        if old_dt != new_dt:
            rename_dt[f"{old_dt}->{new_dt}"] += 1
        if len(sample) < 4:
            sample.append((rel, canon))
        if apply:
            _retry(lambda c=canon, f=full: fs.copy(f, f"{canon_bucket}/{c}"))
    print(f"\nunparseable: {unparseable}")
    print(f"data_type renames: {dict(rename_dt)}")
    print("\nsample rewrites (legacy -> canonical):")
    for old, new in sample:
        print(f"  {old}\n    -> gs://{canon_bucket}/{new}")
    print(f"\n{'APPLIED server-side copies' if apply else 'DRY-RUN — re-run with --apply'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
