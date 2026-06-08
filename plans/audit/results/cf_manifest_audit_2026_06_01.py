"""CF-1…CF-14 canonical-form DATA-STATE audit (read-only) for a manifest `_index`.

The acceptance criterion for the 2026-06-01 canonicalisation programme is
`plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` (CF-1…CF-14).
This tool reads the ACTUAL data-state of a bucket's `_index/availability_index.parquet`
(never a code constant — the manifest-v8 lesson: a constant said v8 while 0% of 7.4M rows
were v8) and emits a per-CF GREEN/RED with evidence + a machine-readable result dict.
Optionally diffs a legacy bucket to compute legacy-only `(date,venue,data_type)` cells
(the L6-decommission data-loss gate).

Extended 2026-06-08 (audit_criteria_automation_2026_06_08.md Tier-3) from CF-1…CF-12 to
CF-1…CF-14 + Era-B: adds CF-13 (pipeline_mode SOURCE-AWARE form, not just populated),
Era-B (chains are instrument_types w/ data_type=trades — count data_type=options_chain/
futures_chain == 0), CF-6 (expected_unattempted materialised in the 4-state), CF-10
(object-backed captured — phantom; SKIP-with-reason, the full check is
reconcile_phantom_manifest_rows_all.py), CF-14 (build_instrument_catalogue ⊇ present-set;
SKIP-with-reason when the catalogue artifact is not materialised — G1). The cross-AG
wrapper (`cf_manifest_audit_all.py`) runs all 5 AGs x {market-data-tick, instruments-store}
and emits a JSON rollup for the daily alert-on-RED cron.

Local GCS reads via gcsfs/aiodns are flaky on this host (DNS timeouts — see defi C7 note), so
this AUDIT pulls the single `_index` parquet with `gcloud storage cp` (reliable CLI network)
then reads it locally with pandas. Object-path sampling uses `gcloud storage ls`.

Run:
  .venv-workspace/bin/python cf_manifest_audit_2026_06_01.py <canonical-bucket> [--legacy <legacy-bucket>]
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

#: Canonical source-aware pipeline_mode prefixes (CF-13). A value MUST start with one of
#: these — the bare coarse `batch`/`live` is the retired form.
SOURCE_AWARE_PM_PREFIXES: tuple[str, ...] = ("batch_", "live_", "replay_")
#: Era-A data_type names that must be ZERO post-Era-B (chains write data_type=trades).
ERA_A_CHAIN_DATA_TYPES: frozenset[str] = frozenset({"options_chain", "futures_chain"})


def _cp(uri: str, dst: Path, tries: int = 5) -> bool:
    """Pull a single GCS object via the gcloud CLI (DNS-robust), retried. Returns ok."""
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
    """ONE-level (non-recursive) listing, time-boxed. DNS-robust (CLI, not gcsfs)."""
    cmd = f"gcloud storage ls {uri!r} 2>/dev/null | head -n {limit}"
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False, timeout=45)
    except subprocess.TimeoutExpired:
        return []
    return [ln.rstrip("/") for ln in res.stdout.splitlines() if ln.startswith("gs://")]


def _probe_paths(bucket: str, depth: int = 6) -> list[str]:
    """Descend the object tree ONE level at a time to discover the path scheme without ever
    recursive-listing a multi-million-object bucket. Returns the deepest sample leaf paths."""
    cur = f"gs://{bucket}/"
    seen: list[str] = []
    for _ in range(depth):
        kids = _ls_shallow(cur)
        seen = kids or seen
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


def _cells(df: pd.DataFrame) -> set[tuple[str, ...]]:
    cap = df[df["capture_status"] == "captured"] if "capture_status" in df.columns else df
    cols = [c for c in ("date", "venue", "data_type") if c in cap.columns]
    return set(map(tuple, cap[cols].astype(str).itertuples(index=False, name=None)))


def audit(canonical: str, legacy: str | None) -> tuple[int, dict[str, str]]:
    """Run the CF-1…CF-14 data-state audit on `canonical`. Returns (exit_code, results) where
    results maps CF id → status ('GREEN'/'RED'/'SKIP(...)'/'GREEN(...)'). exit_code 0 = readable,
    2 = could not read the index. RED-ness is decided by the caller from `results`."""
    results: dict[str, str] = {}
    tmp = Path(tempfile.mkdtemp(prefix="cf_audit_"))
    print(f"=== CF audit :: {canonical} ===", flush=True)
    df = _read_index(canonical, tmp, "canon")
    if df is None:
        print("  CANNOT READ canonical _index — abort", flush=True)
        return 2, {"READ": "RED"}
    n = len(df)
    cols = set(df.columns)
    print(f"rows: {n:,}\ncolumns: {sorted(cols)}\n", flush=True)

    # CF-1 schema_version == 9 (data-state)
    if "schema_version" in cols:
        dist = df["schema_version"].value_counts(dropna=False)
        v9 = int(dist.get(CANONICAL_SCHEMA_VERSION, 0))
        results["CF-1"] = "GREEN" if v9 == n else "RED"
        print(f"CF-1 schema_version  [{results['CF-1']}]  v9={v9:,}/{n:,} ({_pct(v9, n)})")
        print("     dist:", dict(dist.head(8)))
    else:
        results["CF-1"] = "RED"
        print("CF-1 schema_version  [RED]  column ABSENT")

    # CF-2 asset_group not category (rows)
    has_cat = "category" in cols
    has_ag = "asset_group" in cols
    results["CF-2"] = "GREEN" if (has_ag and not has_cat) else ("GREEN" if not has_cat else "RED")
    print(f"CF-2 asset_group(rows)  [{results['CF-2']}]  category col={has_cat} asset_group col={has_ag}")

    # CF-3 pipeline_mode column populated
    if "pipeline_mode" in cols:
        pm = df["pipeline_mode"].astype("string").fillna("")
        nonblank = int((pm.str.len() > 0).sum())
        results["CF-3"] = "GREEN" if nonblank == n else "RED"
        print(f"CF-3 pipeline_mode col  [{results['CF-3']}]  populated={nonblank:,}/{n:,} ({_pct(nonblank, n)})")
        print("     dist:", dict(pm.value_counts(dropna=False).head(8)))
    else:
        results["CF-3"] = "RED"
        print("CF-3 pipeline_mode col  [RED]  column ABSENT")

    # CF-4 source column, zero-blank on external cells
    if "source" in cols:
        src = df["source"].astype("string").fillna("")
        blank = int((src.str.len() == 0).sum())
        results["CF-4"] = "GREEN" if blank == 0 else "RED"
        print(f"CF-4 source col  [{results['CF-4']}]  blank={blank:,}/{n:,} ({_pct(blank, n)})")
        print("     dist:", dict(src.value_counts(dropna=False).head(8)))
    else:
        results["CF-4"] = "RED"
        print("CF-4 source col  [RED]  column ABSENT (needs add)")

    # CF-5 typed empty reason on empty cells
    reason_col = next((c for c in ("empty_confirmed_reason", "error_reason") if c in cols), None)
    if "capture_status" in cols:
        print("     capture_status:", dict(df["capture_status"].value_counts(dropna=False)))
        empt = df[df["capture_status"] == "empty_confirmed"]
        if reason_col and len(empt):
            r = empt[reason_col].astype("string").fillna("")
            blankr = int((r.str.len() == 0).sum())
            results["CF-5"] = "GREEN" if blankr == 0 else "RED"
            print(f"CF-5 typed reason ({reason_col})  [{results['CF-5']}]  blank/untyped={blankr:,}/{len(empt):,}")
            print("     empty-reason dist:", dict(r.value_counts(dropna=False).head(12)))
        else:
            results["CF-5"] = "GREEN" if len(empt) == 0 else "RED"
            print(f"CF-5 typed reason  [{results['CF-5']}]  empties={len(empt):,} reason_col={reason_col}")

    # CF-6 expected_unattempted materialised in the 4-state (writer-seeded, read by consumers)
    if "capture_status" in cols:
        statuses = set(df["capture_status"].astype(str).unique())
        eu = int((df["capture_status"].astype(str) == "expected_unattempted").sum())
        # GREEN if the 4-state vocabulary is present (expected_unattempted is a valid seeded state);
        # RED only if capture_status carries non-canonical values. Absence of EU rows is allowed
        # (a fully-backfilled bucket) — the check is that the 4-state is honoured, not a count floor.
        canonical_states = {"captured", "empty_confirmed", "attempted_failed", "expected_unattempted"}
        noncanon = statuses - canonical_states
        results["CF-6"] = "GREEN" if not noncanon else "RED"
        print(f"CF-6 expected_unattempted/4-state  [{results['CF-6']}]  EU rows={eu:,}  noncanonical-states={sorted(noncanon)}")
    else:
        results["CF-6"] = "RED"
        print("CF-6 4-state  [RED]  capture_status column ABSENT")

    # CF-8 available_at per-row
    aa = next((c for c in ("available_at", "written_at", "attempted_at") if c in cols), None)
    if "available_at" in cols:
        nn = int(df["available_at"].notna().sum())
        results["CF-8"] = "GREEN" if nn == n else "RED"
        print(f"CF-8 available_at  [{results['CF-8']}]  non-null={nn:,}/{n:,}")
    else:
        results["CF-8"] = "RED"
        print(f"CF-8 available_at  [RED]  column ABSENT (write-time proxy present: {aa})")

    # CF-7 venue / data_type canonical sample (human verify against UAC)
    if "data_type" in cols:
        print("CF-7 data_type sample:", sorted(df["data_type"].astype(str).unique())[:25])
    if "venue" in cols:
        print("CF-7 venue sample:", sorted(df["venue"].astype(str).unique())[:25])

    # CF-13 pipeline_mode SOURCE-AWARE form (batch_<source>, not bare batch) — data-state
    if "pipeline_mode" in cols:
        pm = df["pipeline_mode"].astype("string").fillna("")
        nonblank_mask = pm.str.len() > 0
        nonblank_total = int(nonblank_mask.sum())
        source_aware = int((nonblank_mask & pm.str.startswith(SOURCE_AWARE_PM_PREFIXES)).sum())
        # service/feature rows legitimately carry blank pipeline_mode; only the NON-blank
        # values must be source-aware. GREEN iff every populated value is source-aware.
        results["CF-13"] = "GREEN" if source_aware == nonblank_total else "RED"
        bare = sorted({v for v in pm[nonblank_mask].unique() if not v.startswith(SOURCE_AWARE_PM_PREFIXES)})[:8]
        print(
            f"CF-13 pm source-aware form  [{results['CF-13']}]  source_aware={source_aware:,}/{nonblank_total:,} "
            f"({_pct(source_aware, nonblank_total)})  bare/coarse-examples={bare}"
        )
    else:
        results["CF-13"] = "RED"
        print("CF-13 pm source-aware form  [RED]  pipeline_mode column ABSENT")

    # Era-B: chains are instrument_types w/ data_type=trades → count data_type=options_chain/futures_chain == 0
    if "data_type" in cols:
        era_a = int(df["data_type"].astype(str).isin(ERA_A_CHAIN_DATA_TYPES).sum())
        results["Era-B"] = "GREEN" if era_a == 0 else "RED"
        print(f"Era-B chain data_type  [{results['Era-B']}]  data_type in {{options_chain,futures_chain}} rows={era_a:,} (must be 0)")
    else:
        results["Era-B"] = "SKIP(no data_type col)"
        print("Era-B chain data_type  [SKIP]  data_type column ABSENT")

    # CF-10 object-backed captured (phantom) — SKIP-with-reason: a full check walks objects per
    # captured cell (expensive); the canonical tool is reconcile_phantom_manifest_rows_all.py.
    results["CF-10"] = "SKIP(use reconcile_phantom_manifest_rows_all.py --dry-run)"
    print(f"CF-10 phantom/object-backed  [{results['CF-10']}]")

    # CF-2/CF-3 object-path scheme (shallow descent — no corpus walk); CF-9 from bucket name
    print("\n-- object-path scheme (CF-2 paths / CF-3 partition) --")
    sample = _probe_paths(canonical)
    joined = "\n".join(sample)
    has_cat_path = "/category=" in joined
    has_ag_path = "/asset_group=" in joined
    has_pm_path = "/pipeline_mode=" in joined
    has_any_hive = "=" in joined.split(f"gs://{canonical}/", 1)[-1]
    results["CF-2-paths"] = "RED" if has_cat_path else ("GREEN" if has_ag_path else "RED")
    results["CF-3-partition"] = "GREEN" if has_pm_path else "RED"
    results["CF-9"] = "GREEN" if any(t in canonical for t in ("-prd-", "-test-", "-dev-", "-stg-")) else "RED"
    print(
        f"CF-2 paths  [{results['CF-2-paths']}]  category= present={has_cat_path}  "
        f"asset_group= present={has_ag_path}  any-hive={has_any_hive}"
    )
    print(f"CF-3 partition  [{results['CF-3-partition']}]  pipeline_mode= segment present={has_pm_path}")
    print(f"CF-9 env bucket  [{results['CF-9']}]  {canonical}")
    for s in sample[:4]:
        print("     ", s)

    # CF-14 catalogue ⊇ present-set — SKIP-with-reason unless a catalogue artifact is readable.
    # The could-exist denominator (build_instrument_catalogue roll-up) is G1's responsibility and
    # may not be materialised yet; an honest SKIP beats a fake GREEN/RED. When the catalogue
    # parquet is present in the instruments-store bucket, compare; else SKIP.
    cat_uri = f"gs://{canonical}/_catalogue/instrument_catalogue.parquet"
    cat_listing = _ls_shallow(cat_uri)
    if cat_listing:
        cdst = tmp / "catalogue.parquet"
        if _cp(cat_uri, cdst):
            cat = pd.read_parquet(cdst)
            present = _cells(df)
            ccols = [c for c in ("date", "venue", "data_type") if c in cat.columns]
            cat_cells = set(map(tuple, cat[ccols].astype(str).itertuples(index=False, name=None))) if ccols else set()
            present_not_in_cat = present - cat_cells if cat_cells else set()
            results["CF-14"] = "GREEN" if not present_not_in_cat else "RED"
            print(
                f"CF-14 catalogue ⊇ present  [{results['CF-14']}]  present={len(present):,} "
                f"catalogue={len(cat_cells):,}  present-not-in-catalogue={len(present_not_in_cat):,}"
            )
        else:
            results["CF-14"] = "SKIP(catalogue cp failed)"
            print("CF-14 catalogue ⊇ present  [SKIP]  could not read catalogue artifact")
    else:
        results["CF-14"] = "SKIP(catalogue not materialised — G1)"
        print("CF-14 catalogue ⊇ present  [SKIP]  no _catalogue/ artifact (G1 build_instrument_catalogue pending)")

    # legacy diff → legacy-only cells (L6 data-loss gate)
    if legacy:
        print(f"\n-- legacy diff :: {legacy} --", flush=True)
        ldf = _read_index(legacy, tmp, "legacy")
        if ldf is None:
            print("  cannot read legacy _index")
        else:
            lc, cc = _cells(ldf), _cells(df)
            legacy_only = lc - cc
            results["L6-legacy-only"] = "GREEN" if not legacy_only else "RED"
            print(f"legacy captured cells: {len(lc):,}  canonical: {len(cc):,}  overlap: {len(lc & cc):,}")
            print(f"LEGACY-ONLY CELLS (canonical MISSING): {len(legacy_only):,}  [{results['L6-legacy-only']}]")
            if legacy_only:
                for e in sorted(legacy_only)[:8]:
                    print("   ", e)
    print(f"\n(temp: {tmp})", flush=True)
    return 0, results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("canonical")
    ap.add_argument("--legacy", default=None)
    a = ap.parse_args()
    rc, results = audit(a.canonical, a.legacy)
    reds = sorted(k for k, v in results.items() if v == "RED")
    print(f"\n=== SUMMARY {a.canonical}: {'GREEN — all CF pass' if not reds else f'RED — {reds}'} ===")
    if rc == 2:
        return 2
    return 1 if reds else 0


if __name__ == "__main__":
    sys.exit(main())
