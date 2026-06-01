"""CF-1…CF-12 canonical-form DATA-STATE audit (read-only) for a manifest `_index`.

The acceptance criterion for the 2026-06-01 canonicalisation programme is
`plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` (CF-1…CF-12).
This tool reads the ACTUAL data-state of a bucket's `_index/availability_index.parquet`
(never a code constant — the manifest-v8 lesson: a constant said v8 while 0% of 7.4M rows
were v8) and emits a per-CF GREEN/RED with evidence. Optionally diffs a legacy bucket to
compute legacy-only `(date,venue,data_type)` cells (the L6-decommission data-loss gate).

Local GCS reads via gcsfs/aiodns are flaky on this host (DNS timeouts — see defi C7 note), so
this AUDIT pulls the single `_index` parquet with `gcloud storage cp` (reliable CLI network)
then reads it locally with pandas. Object-path sampling (CF-2 paths / CF-3 partition / CF-9
env) uses `gcloud storage ls`. (Whole-corpus MIGRATION walks still run on a VM via the UTL
gcs helpers per the § Migration-script performance contract — this is a one-shot read-only
audit of a handful of index files, where the CLI is the robust choice.)

Run:
  .venv-workspace/bin/python cf_manifest_audit_2026_06_01.py <canonical-bucket> [--legacy <legacy-bucket>]
  .venv-workspace/bin/python cf_manifest_audit_2026_06_01.py market-data-tick-cefi-prd-central-element-323112 \
      --legacy market-data-tick-cefi-central-element-323112
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

INDEX_REL = "_index/availability_index.parquet"
CANONICAL_SCHEMA_VERSION = 9


def _cp(uri: str, dst: Path, tries: int = 5) -> bool:
    """Pull a single GCS object via the gcloud CLI (DNS-robust), retried — the local network is
    flaky on larger index parquets (defi C7 note). Returns ok."""
    for i in range(tries):
        res = subprocess.run(
            ["gcloud", "storage", "cp", uri, str(dst)],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and dst.exists():
            return True
        print(f"  cp attempt {i + 1}/{tries} failed {uri}: {res.stderr.strip()[-120:]}", flush=True)
    return False


def _ls_shallow(uri: str, limit: int = 60) -> list[str]:
    """ONE-level (non-recursive) listing, time-boxed. Cheap on any bucket size (lists a single
    'directory' prefix, not the corpus). DNS-robust (CLI, not gcsfs)."""
    cmd = f"gcloud storage ls {uri!r} 2>/dev/null | head -n {limit}"
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False, timeout=45)
    except subprocess.TimeoutExpired:
        return []
    return [ln.rstrip("/") for ln in res.stdout.splitlines() if ln.startswith("gs://")]


def _probe_paths(bucket: str, depth: int = 6) -> list[str]:
    """Descend the object tree ONE level at a time (shallow, fast) to discover the path scheme —
    detects `category=` / `asset_group=` / `pipeline_mode=` / `day=` segments without ever
    recursive-listing a multi-million-object bucket. Returns the deepest sample leaf paths seen."""
    cur = f"gs://{bucket}/"
    seen: list[str] = []
    for _ in range(depth):
        kids = _ls_shallow(cur)
        seen = kids or seen
        # skip the manifest/admin prefixes; follow the first data-bearing child
        data_kids = [
            k for k in kids if not k.rstrip("/").endswith(("_index", "_vm_staging", "backfill-logs", "snapshots"))
        ]
        if not data_kids:
            break
        nxt = data_kids[0]
        if nxt.endswith(".parquet"):
            break
        cur = nxt + "/"
    return seen


def _read_index(bucket: str, tmp: Path, tag: str) -> pd.DataFrame | None:
    dst = tmp / f"{tag}_index.parquet"
    if not _cp(f"gs://{bucket}/{INDEX_REL}", dst):
        return None
    return pd.read_parquet(dst)


def _pct(n: int, d: int) -> str:
    return f"{(100.0 * n / d):.1f}%" if d else "n/a"


def _cells(df: pd.DataFrame) -> set[tuple]:
    cap = df[df["capture_status"] == "captured"] if "capture_status" in df.columns else df
    cols = [c for c in ("date", "venue", "data_type") if c in cap.columns]
    return set(map(tuple, cap[cols].astype(str).itertuples(index=False, name=None)))


def audit(canonical: str, legacy: str | None) -> int:
    tmp = Path(tempfile.mkdtemp(prefix="cf_audit_"))
    print(f"=== CF audit :: {canonical} ===", flush=True)
    df = _read_index(canonical, tmp, "canon")
    if df is None:
        print("  CANNOT READ canonical _index — abort", flush=True)
        return 2
    n = len(df)
    cols = set(df.columns)
    print(f"rows: {n:,}\ncolumns: {sorted(cols)}\n", flush=True)

    # CF-1 schema_version == 9 (data-state)
    if "schema_version" in cols:
        dist = df["schema_version"].value_counts(dropna=False)
        v9 = int(dist.get(CANONICAL_SCHEMA_VERSION, 0))
        green = v9 == n
        print(f"CF-1 schema_version  [{'GREEN' if green else 'RED'}]  v9={v9:,}/{n:,} ({_pct(v9, n)})")
        print("     dist:", dict(dist.head(8)))
    else:
        print("CF-1 schema_version  [RED]  column ABSENT")

    # CF-2 asset_group not category (rows). Bucket name implies AG; row column may be absent.
    has_cat = "category" in cols
    has_ag = "asset_group" in cols
    cf2 = "GREEN" if (has_ag and not has_cat) else ("GREEN(vacuous-no-AG-col)" if not has_cat and not has_ag else "RED")
    print(f"CF-2 asset_group(rows)  [{cf2}]  category col={has_cat} asset_group col={has_ag}")

    # CF-3 pipeline_mode column populated (partition = path check below)
    if "pipeline_mode" in cols:
        pm = df["pipeline_mode"].astype("string").fillna("")
        nonblank = int((pm.str.len() > 0).sum())
        print(
            f"CF-3 pipeline_mode col  [{'GREEN' if nonblank == n else 'RED'}]  populated={nonblank:,}/{n:,} ({_pct(nonblank, n)})"
        )
        print("     dist:", dict(pm.value_counts(dropna=False).head(8)))
    else:
        print("CF-3 pipeline_mode col  [RED]  column ABSENT")

    # CF-4 source column, zero-blank on external cells
    if "source" in cols:
        src = df["source"].astype("string").fillna("")
        blank = int((src.str.len() == 0).sum())
        print(f"CF-4 source col  [{'GREEN' if blank == 0 else 'RED'}]  blank={blank:,}/{n:,} ({_pct(blank, n)})")
        print("     dist:", dict(src.value_counts(dropna=False).head(8)))
    else:
        print("CF-4 source col  [RED]  column ABSENT (needs add)")

    # CF-5 typed empty reason on empty cells (reason column varies: empty_confirmed_reason / error_reason)
    reason_col = next((c for c in ("empty_confirmed_reason", "error_reason") if c in cols), None)
    if "capture_status" in cols:
        print("     capture_status:", dict(df["capture_status"].value_counts(dropna=False)))
        empt = df[df["capture_status"] == "empty_confirmed"]
        if reason_col and len(empt):
            r = empt[reason_col].astype("string").fillna("")
            blankr = int((r.str.len() == 0).sum())
            print(
                f"CF-5 typed reason ({reason_col})  [{'GREEN' if blankr == 0 else 'RED'}]  blank/untyped empties={blankr:,}/{len(empt):,}"
            )
            print("     empty-reason dist:", dict(r.value_counts(dropna=False).head(12)))
        else:
            print(
                f"CF-5 typed reason  [{'GREEN' if len(empt) == 0 else 'RED'}]  empties={len(empt):,} reason_col={reason_col}"
            )

    # CF-8 available_at per-row
    aa = next((c for c in ("available_at", "written_at", "attempted_at") if c in cols), None)
    if "available_at" in cols:
        nn = int(df["available_at"].notna().sum())
        print(f"CF-8 available_at  [{'GREEN' if nn == n else 'RED'}]  non-null={nn:,}/{n:,}")
    else:
        print(f"CF-8 available_at  [RED]  column ABSENT (write-time proxy present: {aa})")

    # CF-7 venue / data_type canonical sample (human verify against UAC)
    if "data_type" in cols:
        print("CF-7 data_type sample:", sorted(df["data_type"].astype(str).unique())[:25])
    if "venue" in cols:
        print("CF-7 venue sample:", sorted(df["venue"].astype(str).unique())[:25])

    # CF-2/CF-3 object-path scheme (shallow descent — no corpus walk); CF-9 from bucket name
    print("\n-- object-path scheme (CF-2 paths / CF-3 partition) --")
    sample = _probe_paths(canonical)
    joined = "\n".join(sample)
    has_cat_path = "/category=" in joined
    has_ag_path = "/asset_group=" in joined
    has_pm_path = "/pipeline_mode=" in joined
    has_any_hive = "=" in joined.split(f"gs://{canonical}/", 1)[-1]
    print(
        f"CF-2 paths  [{'RED' if has_cat_path else ('GREEN' if has_ag_path else 'RED(no-hive/flat)')}]  "
        f"category= present={has_cat_path}  asset_group= present={has_ag_path}  any-hive={has_any_hive}"
    )
    print(f"CF-3 partition  [{'GREEN' if has_pm_path else 'RED'}]  pipeline_mode= segment present={has_pm_path}")
    print(
        f"CF-9 env bucket  [{'GREEN' if any(t in canonical for t in ('-prd-', '-test-', '-dev-', '-stg-')) else 'RED'}]  {canonical}"
    )
    for s in sample[:4]:
        print("     ", s)

    # legacy diff → legacy-only cells (L6 data-loss gate)
    if legacy:
        print(f"\n-- legacy diff :: {legacy} --", flush=True)
        ldf = _read_index(legacy, tmp, "legacy")
        if ldf is None:
            print("  cannot read legacy _index")
        else:
            lc, cc = _cells(ldf), _cells(df)
            legacy_only = lc - cc
            print(f"legacy captured cells: {len(lc):,}  canonical: {len(cc):,}  overlap: {len(lc & cc):,}")
            print(
                f"LEGACY-ONLY CELLS (canonical MISSING): {len(legacy_only):,}  [{'GREEN' if not legacy_only else 'RED — data-loss risk on delete'}]"
            )
            if legacy_only:
                ex = sorted(legacy_only)[:8]
                for e in ex:
                    print("   ", e)
    print(f"\n(temp: {tmp})", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("canonical")
    ap.add_argument("--legacy", default=None)
    a = ap.parse_args()
    return audit(a.canonical, a.legacy)


if __name__ == "__main__":
    sys.exit(main())
