"""Phase-0 LAYOUT audit (read-only) — enumerate ALL object layouts in a bucket before any walk.

Mandated blocking Phase 0 per the slot-2 DeFi lesson (2026-06-01): a source bucket can hold MULTIPLE
overlapping legacy layouts (near-canonical `raw_tick_data/by_date/day=/asset_group=/…`, older
`{venue}/{chain}/date=`, flat `day=/category=`), and a naive day-prefix walk silently under-migrates
— leaving a partial canonical set + data loss on legacy delete. This tool discovers every distinct
layout so the migrator covers them ALL (or consciously dedups overlap to the freshest schema).

For each top-level data tree it descends shallowly (one prefix level at a time — never a corpus walk)
to a sample leaf `.parquet`, records the **layout signature** = the ordered list of hive path-keys
(or `FLAT` / bare segments), and samples that leaf's columns + a date hint. Classifies whether the
layout already carries `asset_group=` / `pipeline_mode=` / `data_source=` path segments (the canonical
target markers). DNS-robust (gcloud CLI, not gcsfs), bounded (no recursive corpus listing).

Run:
  .venv-workspace/bin/python cf_layout_audit_2026_06_01.py <bucket> [<bucket> ...]
  .venv-workspace/bin/python cf_layout_audit_2026_06_01.py market-data-tick-cefi-prd-central-element-323112
"""

from __future__ import annotations

import contextlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from unified_trading_library import get_storage_client

ADMIN_PREFIXES = ("_index", "_deploy", "_vm_staging", "backfill-logs", "snapshots", "configs")


def _ls(uri: str, limit: int = 80) -> list[str]:
    """One-level (non-recursive) listing, time-boxed. Cheap on any bucket size."""
    cmd = f"gcloud storage ls {uri!r} 2>/dev/null | head -n {limit}"
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False, timeout=60)
    except subprocess.TimeoutExpired:
        return []
    return [ln.rstrip("/") for ln in res.stdout.splitlines() if ln.startswith("gs://")]


def _signature(rel_path: str) -> str:
    """Layout signature = ordered hive keys, or BARE segments, to the leaf file."""
    segs = rel_path.split("/")[:-1]  # drop filename
    parts: list[str] = []
    for s in segs:
        if "=" in s:
            parts.append(s.split("=", 1)[0] + "=")
        else:
            parts.append(f"<{s}>")  # bare (non-hive) segment
    return "/".join(parts) if parts else "FLAT"


def _descend_to_leaf(bucket: str, start: str, max_depth: int = 9) -> str | None:
    """Follow the first data-bearing child down to a `.parquet` leaf (shallow, fast)."""
    cur = start
    for _ in range(max_depth):
        kids = _ls(cur + "/")
        data = [k for k in kids if not k.rstrip("/").split("/")[-1].startswith("_")]
        if not data:
            return None
        leaf = next((k for k in data if k.endswith(".parquet")), None)
        if leaf:
            return leaf
        cur = data[0]
    return None


def _sample_schema(uri: str, tmp: Path) -> str:
    dst = tmp / "leaf.parquet"
    bucket, path = uri.removeprefix("gs://").split("/", 1)
    with contextlib.suppress(OSError, ValueError, RuntimeError):
        get_storage_client(provider="gcp").bucket(bucket).blob(path).download_to_filename(str(dst))
    if not dst.exists():
        return "  (could not read leaf)"
    try:
        import pandas as pd

        df = pd.read_parquet(dst)
        cols = list(df.columns)
        date_hint = ""
        for c in ("date", "day", "timestamp", "available_at"):
            if c in df.columns and len(df):
                date_hint = f" | {c}~{str(df[c].iloc[0])[:19]} (nuniq {df[c].nunique()})"
                break
        return f"  nrows={len(df)} cols={cols[:18]}{date_hint}"
    except Exception as exc:  # noqa: broad-except — best-effort schema sample, any read failure is reported inline
        return f"  (read error: {exc})"


def audit_bucket(bucket: str) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="cf_layout_"))
    print(f"\n=== LAYOUT audit :: {bucket} ===", flush=True)
    tops = _ls(f"gs://{bucket}/")
    data_tops = [t for t in tops if t.rstrip("/").split("/")[-1] not in ADMIN_PREFIXES]
    admin = [t.rstrip("/").split("/")[-1] for t in tops if t.rstrip("/").split("/")[-1] in ADMIN_PREFIXES]
    print(f"top-level prefixes: {len(tops)} (admin: {admin})", flush=True)
    seen_sigs: dict[str, str] = {}
    # Group top-level day=YYYY-... into one representative to avoid descending hundreds of day dirs.
    day_tops = [t for t in data_tops if re.search(r"/day=\d{4}", t)]
    other_tops = [t for t in data_tops if not re.search(r"/day=\d{4}", t)]
    reps = ([day_tops[0]] if day_tops else []) + other_tops
    if day_tops:
        print(f"  ({len(day_tops)} top-level day= dirs → sampling 1 as representative)", flush=True)
    for top in reps[:12]:
        leaf = _descend_to_leaf(bucket, top)
        if not leaf:
            print(f"  tree {top.split('/')[-1] or top!r}: (no parquet leaf found shallowly)", flush=True)
            continue
        rel = leaf[len(f"gs://{bucket}/") :]
        sig = _signature(rel)
        markers = []
        for m in ("asset_group=", "pipeline_mode=", "category=", "data_source=", "date=", "day="):
            if m in rel:
                markers.append(m)
        print(f"\n  TREE: {top[len(f'gs://{bucket}/') :] or '<root>'}", flush=True)
        print(f"    layout-sig: {sig}")
        print(f"    markers: {markers}")
        print(f"    sample: {rel}")
        if sig not in seen_sigs:
            seen_sigs[sig] = rel
            print(_sample_schema(leaf, tmp))
    print(f"\n  >> {len(seen_sigs)} DISTINCT layout signature(s) in {bucket}:", flush=True)
    for sig in seen_sigs:
        canon = "asset_group=" in sig and "pipeline_mode=" in sig
        near = "asset_group=" in sig
        tag = "CANONICAL" if canon else ("near-canonical (no pipeline_mode=)" if near else "LEGACY")
        print(f"     [{tag}] {sig}")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    for b in sys.argv[1:]:
        audit_bucket(b)
    return 0


if __name__ == "__main__":
    sys.exit(main())
