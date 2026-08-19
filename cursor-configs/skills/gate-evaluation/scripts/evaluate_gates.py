#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Gate-evaluation dump -- makes /plans/active/data_pipeline_completion_2026_08_21.md's
53-gate BATCH/PAPER/LIVE register RE-RUNNABLE instead of a point-in-time
snapshot, the same shape as readiness-state-dump / honest-coverage-dump
(both live in ../../{honest-coverage-dump,readiness-state-dump}/scripts/,
this skill's siblings under cursor-configs/skills/).

Readiness is DERIVED, never declared (the same operator ruling
readiness-state-dump already follows, 2026-08-16): a gate with no real
machine check reports "unverified", never a silent pass and never a
fabricated PASS/FAIL. Only 3 of the 53 gates have a genuine, already-existing
machine oracle wired here (B1, B8, B16 -- all three sourced from the SAME
already-computed coverage.json honest-coverage-dump reads, reused verbatim
via dump_coverage.build_report(), never recomputed). The other 50 report
"unverified" honestly, each carrying whether it has an owning doc (per the
register's own 2026-08-18 cross-link pass) so a reader can immediately see
which gap is "go read <doc>" vs "no tracked work exists for this at all".

This is deliberately NOT an attempt to wire all 53 gates to bespoke checks in
one pass -- most gates (B3 observability, B20 human sign-off, L9 DR-drill,
etc.) require either a human judgment call, a live drill, or deep
service-internal investigation well beyond what a single register-dump
script can honestly automate. Wiring a NEW gate here later is a natural
extension point: add a checker function + register its gate_id in CHECKERS.

REQUIRES a Python whose venv has unified-trading-library installed (GCS
reads go through UTL's cloud_interface only, via honest-coverage-dump's
shard_universe.py -- a subprocess gcloud/gsutil call is a hard workspace
ban). instruments-service's venv is the natural choice, same as its two
sibling skills:

    cd instruments-service && .venv/bin/python3 \\
        ../unified-trading-pm/cursor-configs/skills/gate-evaluation/scripts/evaluate_gates.py

Usage:
    python evaluate_gates.py                    # full register, summary view
    python evaluate_gates.py --verbose           # every gate's verdict + detail
    python evaluate_gates.py --category BATCH
    python evaluate_gates.py --json              # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

_HERE = Path(__file__).resolve()
_SKILLS_DIR = _HERE.parents[2]  # .../cursor-configs/skills

sys.path.insert(0, str(_SKILLS_DIR / "honest-coverage-dump" / "scripts"))

import dump_coverage
from gate_registry import AUTOMATED_GATE_IDS, CATEGORIES, GATES, Gate
from shard_universe import CoverageReadError, load_coverage

VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_UNVERIFIED = "UNVERIFIED"


@dataclass(frozen=True)
class GateResult:
    gate: Gate
    verdict: str
    detail: str


def _check_b1_availability(report: dict) -> GateResult:
    """B1 -- >0 honest coverage per shard, excluding empty_confirmed. A shard
    FAILS only when it has zero captured rows AND is not a confirmed-empty
    legitimate absence (i.e. attempted_failed-only or
    expected_unattempted-only shards genuinely have no reached coverage)."""
    failing = [
        row["shard"]
        for row in report["shards"]
        if row["capture_states"]["captured"] == 0 and row["capture_states"]["expected-absent"] == 0
    ]
    total = report["shard_count"]
    if total == 0:
        return GateResult(_GATE_BY_ID["B1"], VERDICT_UNVERIFIED, "no shards in scope for the loaded coverage.json")
    if failing:
        sample = ", ".join(failing[:5])
        more = f" (+{len(failing) - 5} more)" if len(failing) > 5 else ""
        return GateResult(
            _GATE_BY_ID["B1"],
            VERDICT_FAIL,
            f"{len(failing)}/{total} shards have ZERO honest coverage, not confirmed-empty: {sample}{more}",
        )
    return GateResult(
        _GATE_BY_ID["B1"], VERDICT_PASS, f"all {total} shards have >0 honest coverage or are confirmed-empty"
    )


def _check_b8_full_coverage(report: dict) -> GateResult:
    """B8 -- honest coverage 100% over the declared expected set. Reuses the
    exact reachable_coverage_pct dump_coverage.py already computes -- this is
    the same figure the Friday-target table (data_pipeline_completion_2026_08_21.md)
    was hand-recorded from on 2026-08-18; this check re-derives it live."""
    pct = report["totals"]["reachable_coverage_pct"]
    denom = report["totals"]["reachable_denominator"]
    if pct is None:
        return GateResult(_GATE_BY_ID["B8"], VERDICT_UNVERIFIED, "reachable_denominator is 0 for the loaded scope")
    if pct >= 100.0:
        return GateResult(_GATE_BY_ID["B8"], VERDICT_PASS, f"reachable_coverage_pct=100.0% (denom={denom})")
    return GateResult(_GATE_BY_ID["B8"], VERDICT_FAIL, f"reachable_coverage_pct={pct}% (denom={denom}, not yet 100%)")


def _check_b16_denominator_declared(report: dict) -> GateResult:
    """B16 -- every coverage % states its denominator, 4 states reported
    separately. Structural check on the SAME report dump_coverage.py already
    builds: confirms all 4 capture-state fields are present as distinct keys
    (this is a property of dump_coverage.py's own schema contract, not
    something that can silently regress without this check catching it) and
    that reachable_denominator is carried alongside every percentage."""
    expected_labels = {"captured", "expected-absent", "attempted-failed", "expected-unattempted"}
    totals_keys = set(report["totals"].keys())
    missing = expected_labels - totals_keys
    if missing:
        return GateResult(
            _GATE_BY_ID["B16"], VERDICT_FAIL, f"missing capture-state labels in totals: {sorted(missing)}"
        )
    if "reachable_denominator" not in report["totals"]:
        return GateResult(
            _GATE_BY_ID["B16"], VERDICT_FAIL, "reachable_denominator not carried alongside the percentage"
        )
    return GateResult(
        _GATE_BY_ID["B16"],
        VERDICT_PASS,
        f"all 4 states reported separately + denominator stated: {sorted(expected_labels)}",
    )


CHECKERS = {
    "B1": _check_b1_availability,
    "B8": _check_b8_full_coverage,
    "B16": _check_b16_denominator_declared,
}
assert set(CHECKERS) == AUTOMATED_GATE_IDS, "CHECKERS must wire exactly the gates gate_registry.py declares AUTOMATED"

_GATE_BY_ID: dict[str, Gate] = {g.gate_id: g for g in GATES}


def _unverified_result(gate: Gate) -> GateResult:
    if gate.owning_doc:
        detail = f"no machine check wired yet; tracked via {gate.owning_doc}"
    else:
        detail = "no machine check wired yet; no owning doc either (per the 2026-08-18 cross-link pass)"
    return GateResult(gate, VERDICT_UNVERIFIED, detail)


def evaluate(project: str, date: str | None, categories: set[str] | None) -> tuple[list[GateResult], dict]:
    coverage_report: dict | None = None
    coverage_error: str | None = None
    try:
        payload, resolved_date, gcs_path = load_coverage(project, date)
        coverage_report = dump_coverage.build_report(payload, asset_groups=None, venues=None)
        coverage_report["_resolved_date"] = resolved_date
        coverage_report["_gcs_path"] = gcs_path
    except CoverageReadError as exc:
        coverage_error = str(exc)

    results: list[GateResult] = []
    for gate in GATES:
        if categories and gate.category not in categories:
            continue
        if gate.gate_id in CHECKERS:
            if coverage_report is not None:
                results.append(CHECKERS[gate.gate_id](coverage_report))
            else:
                results.append(
                    GateResult(gate, VERDICT_UNVERIFIED, f"coverage.json unreadable, cannot evaluate: {coverage_error}")
                )
        else:
            results.append(_unverified_result(gate))

    meta = {"coverage_error": coverage_error}
    if coverage_report is not None:
        meta["coverage_source"] = coverage_report["_gcs_path"]
        meta["coverage_date"] = coverage_report["_resolved_date"]
    return results, meta


def _print_human(results: list[GateResult], meta: dict, verbose: bool) -> None:
    print("Gate-evaluation dump -- data_pipeline_completion_2026_08_21.md's 53-gate register")
    if meta.get("coverage_source"):
        print(f"Coverage source: {meta['coverage_source']} (date={meta['coverage_date']})")
    if meta.get("coverage_error"):
        print(f"WARNING -- coverage.json unreadable: {meta['coverage_error']}", file=sys.stderr)
        print("  (the 3 automated gates B1/B8/B16 report UNVERIFIED as a result; every other gate is unaffected)")
    print()

    by_category: dict[str, list[GateResult]] = {c: [] for c in CATEGORIES}
    for r in results:
        by_category[r.gate.category].append(r)

    grand_totals = {VERDICT_PASS: 0, VERDICT_FAIL: 0, VERDICT_UNVERIFIED: 0}
    for category in CATEGORIES:
        rows = by_category[category]
        if not rows:
            continue
        counts = {VERDICT_PASS: 0, VERDICT_FAIL: 0, VERDICT_UNVERIFIED: 0}
        for r in rows:
            counts[r.verdict] += 1
            grand_totals[r.verdict] += 1
        print(
            f"=== {category}: {len(rows)} gates -- PASS={counts[VERDICT_PASS]} "
            f"FAIL={counts[VERDICT_FAIL]} UNVERIFIED={counts[VERDICT_UNVERIFIED]} ==="
        )
        if verbose:
            for r in sorted(rows, key=lambda r: int(r.gate.gate_id[1:])):
                owning = r.gate.owning_doc or "(no owning doc)"
                print(f"  [{r.verdict:<10}] {r.gate.gate_id:<4} {r.gate.name}")
                print(f"               bar: {r.gate.bar}")
                print(f"               owning_doc: {owning}")
                print(f"               detail: {r.detail}")
        else:
            failing = [r for r in rows if r.verdict == VERDICT_FAIL]
            if failing:
                for r in failing:
                    print(f"  FAIL {r.gate.gate_id} {r.gate.name}: {r.detail}")
        print()

    total = sum(grand_totals.values())
    print(
        f"=== TOTAL: {total} gates -- PASS={grand_totals[VERDICT_PASS]} "
        f"FAIL={grand_totals[VERDICT_FAIL]} UNVERIFIED={grand_totals[VERDICT_UNVERIFIED]} ==="
    )
    no_owning = sum(1 for r in results if r.gate.owning_doc is None)
    print(f"Gates with no owning doc: {no_owning}/{total}")
    if not verbose:
        print("(pass --verbose for the full per-gate table, or --json for machine-readable output)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--project", default="central-element-323112", help="GCP project hosting the honest-coverage bucket"
    )
    parser.add_argument("--date", default=None, help="YYYY-MM-DD; defaults to the latest available coverage.json")
    parser.add_argument(
        "--category", action="append", choices=CATEGORIES, default=None, help="Filter to BATCH/PAPER/LIVE"
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of the human report")
    parser.add_argument("--verbose", action="store_true", help="Print every gate's verdict, bar, owning_doc and detail")
    args = parser.parse_args()

    categories = set(args.category) if args.category else None
    results, meta = evaluate(args.project, args.date, categories)

    if args.json:
        payload = {
            "meta": meta,
            "gates": [{**asdict(r.gate), "verdict": r.verdict, "detail": r.detail} for r in results],
        }
        json.dump(payload, sys.stdout, indent=2)
        print()
    else:
        _print_human(results, meta, args.verbose)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
