"""C0 FULL-v9 canonicalisation for the dedicated DeFi buckets — VM single-walk tool (DRY-RUN first).

Spec aligned with the 4 governing plans (operator 2026-06-01):
  * `pipeline_mode_implementation_2026_05_28.md` — the on-disk `pipeline_mode=` PARTITION was deferred
    to "the next whole-corpus migration window"; THIS migration is that window → it lands the partition.
    Value = the row's `pipeline_mode` (UAC `PipelineMode`, 27 batch + 1 live), joined from the manifest;
    historical batch objects default to their handler's batch mode.
  * `pipeline_mode_audit_2026_05_28.md` — `pipeline_mode` is a typed StrEnum, already a column.
  * `data_source_provenance_all_asset_groups_2026_06_01.md` — `source` stays a COLUMN (NOT a path key),
    populated for multi-source cells where UAC `SOURCE_PRIORITY[(asset_group, data_type)]` has >1 entry
    (defi included); single-source cells exempt. Enforced via `MissingSourceError` on write.
  * `manifest_consolidator_liveness_health_2026_06_01.md` — after the walk, the consolidator re-runs to
    rebuild `_index/availability_index.parquet`; the liveness watchdog monitors the heartbeat.

Legacy (current dedicated-bucket layout, Phase-1.8 output):
  {kind}-{project}/day=YYYY-MM-DD/category=defi/venue=V/chain=C/instrument_type=T/data_type=D/file.parquet
Canonical (FULL v9 target):
  {kind}-prd-{project}/asset_group=defi/pipeline_mode={MODE}/day=YYYY-MM-DD/venue=V/chain=C/instrument_type=T/data_type=D'/file.parquet
  PATH:    category=defi -> asset_group=defi; + pipeline_mode={MODE} partition; venue already flat `_V{N}`
           (migrate_defi_canonical Phase-1.8); D' = underscore-canonical data_type.
  CONTENT (requires read+rewrite, NOT server-side copy): stamp schema_version=9; populate `source` column
           per SOURCE_PRIORITY; carry `pipeline_mode` column. Server-side copy only suffices for path-only
           moves; v9 + source need a parquet read+rewrite → run on a VM (in-region I/O at scale).

Execution: extend + run on a `vm-defi` (asia-northeast1) via `launch-canonical-migration-vm.sh` after the
pre-migration drain (stop GCP+AWS fleet + snapshot) — HARD RULE. Dry-run first (logs the plan); review;
then full; then consolidator re-run + verify; then delete legacy originals.

Run:  .venv-workspace/bin/python <this> <bucket-key>            # dry-run (path plan)
      .venv-workspace/bin/python <this> <bucket-key> --apply    # path-only server-side (v9/source = VM read+rewrite)
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
        except Exception as exc:
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
