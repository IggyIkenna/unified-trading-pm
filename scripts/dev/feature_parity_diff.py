#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Pre-merge vs post-merge feature-output parity diff.

SSOT: unified-trading-pm/plans/active/features_repo_consolidation_2026_05_08.md § Phase 6.

Phase 6 of the features-* repo consolidation proves the 8-to-1 merge produced
numerically-identical feature outputs. This is the reusable diff utility that
phase calls for: read the per-family parquet outputs from a *baseline* run (the
8 separate features-*-service repos checked out at their last-pre-consolidation
commit) and a *post-merge* run (``python -m features_service --feature-family
<f> ...``) and assert byte-for-byte equality within floating-point tolerance.

Layout expected (one sub-directory per family, parquets inside, any nesting):

    <baseline-dir>/calendar/.../*.parquet
    <baseline-dir>/onchain/.../*.parquet
    ...
    <postmerge-dir>/calendar/.../*.parquet
    ...

Per family the checks are (in order, first failure short-circuits that family):

  1. Same set of relative parquet paths under the family directory.
  2. Per parquet: schema match — identical column names + Arrow types.
  3. Per parquet: identical row count.
  4. Per parquet, per column:
       * numeric columns           → ``np.allclose(base, post, rtol, atol)``
                                      (cross-row aggregates can carry minute
                                      reorder noise; default rtol=1e-9, atol=0).
       * ``available_at`` column    → exact element-wise timestamp equality
                                      (the Phase 5 stamping lift must NOT change
                                      stamping semantics).
       * string / categorical / bool / other → exact element-wise equality.

Exit code 0 iff every family is parity-clean; 1 otherwise. A human-readable
report goes to stdout; ``--json`` emits a machine-readable summary instead.

Usage (from anywhere):

    python unified-trading-pm/scripts/dev/feature_parity_diff.py \
        --baseline-dir "${WORKSPACE_ROOT}/.feature_parity_diff/baseline" \
        --postmerge-dir "${WORKSPACE_ROOT}/.feature_parity_diff/postmerge"

    # restrict to a subset of families
    python .../feature_parity_diff.py --baseline-dir ... --postmerge-dir ... \
        --family onchain --family delta_one

    # loosen the float tolerance for a noisy family
    python .../feature_parity_diff.py ... --rtol 1e-6
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

# ── colours ───────────────────────────────────────────────────────────────────
_GREEN = "\033[0;32m"
_RED = "\033[0;31m"
_YELLOW = "\033[1;33m"
_BLUE = "\033[0;34m"
_NC = "\033[0m"

# The 8 canonical feature families (mirrors UAC ``FeatureFamily`` enum values).
_FAMILIES: tuple[str, ...] = (
    "calendar",
    "commodity",
    "cross_instrument",
    "delta_one",
    "multi_timeframe",
    "onchain",
    "sports",
    "volatility",
)

_AVAILABLE_AT_COL = "available_at"


# ── result containers ─────────────────────────────────────────────────────────
@dataclass
class FileDiff:
    """Diff outcome for one parquet file shared by baseline + post-merge."""

    rel_path: str
    ok: bool
    problems: list[str] = field(default_factory=list)


@dataclass
class FamilyDiff:
    """Aggregate diff outcome for one feature family."""

    family: str
    ok: bool
    baseline_present: bool
    postmerge_present: bool
    only_in_baseline: list[str] = field(default_factory=list)
    only_in_postmerge: list[str] = field(default_factory=list)
    file_diffs: list[FileDiff] = field(default_factory=list)
    note: str = ""

    def to_json(self) -> dict[str, object]:
        return {
            "family": self.family,
            "ok": self.ok,
            "baseline_present": self.baseline_present,
            "postmerge_present": self.postmerge_present,
            "only_in_baseline": self.only_in_baseline,
            "only_in_postmerge": self.only_in_postmerge,
            "files_compared": len(self.file_diffs),
            "files_failed": [fd.rel_path for fd in self.file_diffs if not fd.ok],
            "problems": [f"{fd.rel_path}: {p}" for fd in self.file_diffs for p in fd.problems],
            "note": self.note,
        }


# ── parquet helpers ───────────────────────────────────────────────────────────
def _relative_parquets(family_dir: Path) -> dict[str, Path]:
    """Map family-relative POSIX path → absolute Path for every ``*.parquet``."""

    out: dict[str, Path] = {}
    if not family_dir.is_dir():
        return out
    for p in sorted(family_dir.rglob("*.parquet")):
        out[p.relative_to(family_dir).as_posix()] = p
    return out


def _schema_signature(schema: pa.Schema) -> list[tuple[str, str]]:
    """Stable ``[(name, str(type)), ...]`` signature for schema comparison."""

    return [(name, str(schema.field(name).type)) for name in schema.names]


def _column_is_numeric(col_type: pa.DataType) -> bool:
    return bool(pa.types.is_integer(col_type) or pa.types.is_floating(col_type) or pa.types.is_decimal(col_type))


def _compare_column(
    name: str,
    base_arr: pa.ChunkedArray,
    post_arr: pa.ChunkedArray,
    rtol: float,
    atol: float,
) -> str | None:
    """Return ``None`` if the column matches, else a one-line problem string."""

    col_type = base_arr.type
    if name == _AVAILABLE_AT_COL or pa.types.is_temporal(col_type):
        base_list = base_arr.to_pylist()
        post_list = post_arr.to_pylist()
        if base_list != post_list:
            n_diff = sum(1 for a, b in zip(base_list, post_list, strict=True) if a != b)
            return f"column '{name}' (temporal): {n_diff} of {len(base_list)} timestamps differ"
        return None

    if _column_is_numeric(col_type):
        base_np = np.asarray(base_arr.to_numpy(zero_copy_only=False), dtype=np.float64)
        post_np = np.asarray(post_arr.to_numpy(zero_copy_only=False), dtype=np.float64)
        # ``equal_nan=True`` so a NaN in the same slot on both sides is a match —
        # honest-absence NaN is allowed downstream; the crime is masking absence,
        # not the NaN itself (per CLAUDE.md "Honest absence vs fake placeholders").
        if not np.allclose(base_np, post_np, rtol=rtol, atol=atol, equal_nan=True):
            close_mask = np.isclose(base_np, post_np, rtol=rtol, atol=atol, equal_nan=True)
            n_off = int(np.count_nonzero(~close_mask))
            # First few diverging row indices (cast: numpy's ``ndarray.tolist``
            # returns a loosely-typed list, so the cast is the sanctioned
            # narrowing to ``list[int]`` per workspace strict-typing rules).
            off_idx: list[int] = cast("list[int]", np.flatnonzero(~close_mask).tolist())[:5]
            sample = f"; first divergent rows: {off_idx}" if off_idx else ""
            return (
                f"column '{name}' (numeric): {n_off} of {base_np.size} values exceed "
                f"tolerance (rtol={rtol}, atol={atol}){sample}"
            )
        return None

    # string / categorical / bool / binary / list / struct — exact equality.
    base_list = base_arr.to_pylist()
    post_list = post_arr.to_pylist()
    if base_list != post_list:
        n_diff = sum(1 for a, b in zip(base_list, post_list, strict=True) if a != b)
        return f"column '{name}' ({col_type}): {n_diff} of {len(base_list)} values differ"
    return None


def _diff_parquet(rel_path: str, base_path: Path, post_path: Path, rtol: float, atol: float) -> FileDiff:
    problems: list[str] = []
    try:
        base_tbl = pq.read_table(base_path)
        post_tbl = pq.read_table(post_path)
    except (OSError, pa.ArrowInvalid) as exc:
        return FileDiff(rel_path=rel_path, ok=False, problems=[f"failed to read parquet: {exc}"])

    base_sig = _schema_signature(base_tbl.schema)
    post_sig = _schema_signature(post_tbl.schema)
    if base_sig != post_sig:
        base_set = dict(base_sig)
        post_set = dict(post_sig)
        added = [c for c in post_set if c not in base_set]
        removed = [c for c in base_set if c not in post_set]
        retyped = [
            f"{c}: {base_set[c]}→{post_set[c]}" for c in base_set if c in post_set and base_set[c] != post_set[c]
        ]
        bits: list[str] = []
        if removed:
            bits.append(f"columns only in baseline: {removed}")
        if added:
            bits.append(f"columns only in post-merge: {added}")
        if retyped:
            bits.append(f"retyped columns: {retyped}")
        problems.append("schema mismatch — " + "; ".join(bits))
        # Schema mismatch makes column-by-column comparison meaningless.
        return FileDiff(rel_path=rel_path, ok=False, problems=problems)

    if base_tbl.num_rows != post_tbl.num_rows:
        problems.append(f"row count mismatch: baseline={base_tbl.num_rows}, post-merge={post_tbl.num_rows}")
        return FileDiff(rel_path=rel_path, ok=False, problems=problems)

    for name in base_tbl.schema.names:
        prob = _compare_column(name, base_tbl.column(name), post_tbl.column(name), rtol, atol)
        if prob is not None:
            problems.append(prob)

    return FileDiff(rel_path=rel_path, ok=not problems, problems=problems)


# ── family-level diff ─────────────────────────────────────────────────────────
def diff_family(family: str, baseline_root: Path, postmerge_root: Path, rtol: float, atol: float) -> FamilyDiff:
    base_dir = baseline_root / family
    post_dir = postmerge_root / family
    base_present = base_dir.is_dir()
    post_present = post_dir.is_dir()

    if not base_present and not post_present:
        return FamilyDiff(
            family=family,
            ok=True,
            baseline_present=False,
            postmerge_present=False,
            note="neither baseline nor post-merge produced output for this family — skipped",
        )
    if base_present != post_present:
        missing = "post-merge" if base_present else "baseline"
        return FamilyDiff(
            family=family,
            ok=False,
            baseline_present=base_present,
            postmerge_present=post_present,
            note=f"output present on one side only — {missing} directory missing",
        )

    base_files = _relative_parquets(base_dir)
    post_files = _relative_parquets(post_dir)
    only_base = sorted(set(base_files) - set(post_files))
    only_post = sorted(set(post_files) - set(base_files))

    file_diffs: list[FileDiff] = []
    for rel in sorted(set(base_files) & set(post_files)):
        file_diffs.append(_diff_parquet(rel, base_files[rel], post_files[rel], rtol, atol))

    ok = not only_base and not only_post and all(fd.ok for fd in file_diffs)
    note = ""
    if not base_files and not post_files:
        note = "family directories present but contain no parquet files"
        ok = True  # nothing to compare — treat as a non-failure, but flag it.
    return FamilyDiff(
        family=family,
        ok=ok,
        baseline_present=True,
        postmerge_present=True,
        only_in_baseline=only_base,
        only_in_postmerge=only_post,
        file_diffs=file_diffs,
        note=note,
    )


# ── reporting ─────────────────────────────────────────────────────────────────
def _print_text_report(results: Sequence[FamilyDiff]) -> None:
    print(f"\n{_BLUE}── feature-output parity diff ──{_NC}")
    for r in results:
        if r.ok and (not r.baseline_present and not r.postmerge_present):
            print(f"{_YELLOW}  [skip] {r.family:<17} {r.note}{_NC}")
            continue
        if r.ok:
            n = len(r.file_diffs)
            extra = f" — {r.note}" if r.note else ""
            print(f"{_GREEN}  [ok]   {r.family:<17} {n} parquet(s) parity-clean{extra}{_NC}")
            continue
        print(f"{_RED}  [FAIL] {r.family:<17}{_NC}")
        if r.note:
            print(f"           {r.note}")
        if r.only_in_baseline:
            print(f"           parquets only in baseline:   {r.only_in_baseline}")
        if r.only_in_postmerge:
            print(f"           parquets only in post-merge: {r.only_in_postmerge}")
        for fd in r.file_diffs:
            if fd.ok:
                continue
            print(f"           {fd.rel_path}")
            for p in fd.problems:
                print(f"             - {p}")


def _exit_code(results: Sequence[FamilyDiff]) -> int:
    return 0 if all(r.ok for r in results) else 1


# ── cli ───────────────────────────────────────────────────────────────────────
class _Args(argparse.Namespace):
    """Typed view of the parsed CLI namespace (keeps basedpyright `reportAny` happy)."""

    baseline_dir: Path
    postmerge_dir: Path
    families: list[str] | None
    rtol: float
    atol: float
    json: bool


def _parse_args(argv: Sequence[str] | None = None) -> _Args:
    parser = argparse.ArgumentParser(
        prog="feature_parity_diff.py",
        description="Pre-merge vs post-merge feature-output parity diff (Phase 6 of features_repo_consolidation).",
    )
    _ = parser.add_argument(
        "--baseline-dir", required=True, type=Path, help="Root of the pre-consolidation per-family outputs."
    )
    _ = parser.add_argument(
        "--postmerge-dir",
        required=True,
        type=Path,
        help="Root of the consolidated features-service per-family outputs.",
    )
    _ = parser.add_argument(
        "--family",
        action="append",
        choices=_FAMILIES,
        dest="families",
        help="Restrict to one or more families (repeatable). Default: all 8.",
    )
    _ = parser.add_argument(
        "--rtol", type=float, default=1e-9, help="Relative tolerance for numeric columns (default 1e-9)."
    )
    _ = parser.add_argument(
        "--atol", type=float, default=0.0, help="Absolute tolerance for numeric columns (default 0.0)."
    )
    _ = parser.add_argument(
        "--json", action="store_true", help="Emit a machine-readable JSON summary instead of the text report."
    )
    return cast("_Args", parser.parse_args(argv, namespace=_Args()))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    baseline_dir: Path = args.baseline_dir
    postmerge_dir: Path = args.postmerge_dir
    families: list[str] = list(args.families) if args.families else list(_FAMILIES)
    rtol: float = float(args.rtol)
    atol: float = float(args.atol)
    as_json: bool = bool(args.json)

    if not baseline_dir.is_dir():
        print(f"{_RED}baseline-dir does not exist: {baseline_dir}{_NC}", file=sys.stderr)
        return 2
    if not postmerge_dir.is_dir():
        print(f"{_RED}postmerge-dir does not exist: {postmerge_dir}{_NC}", file=sys.stderr)
        return 2

    results = [diff_family(f, baseline_dir, postmerge_dir, rtol, atol) for f in families]

    if as_json:
        payload: dict[str, object] = {
            "ok": all(r.ok for r in results),
            "baseline_dir": str(baseline_dir),
            "postmerge_dir": str(postmerge_dir),
            "rtol": rtol,
            "atol": atol,
            "families": [r.to_json() for r in results],
        }
        print(json.dumps(payload, indent=2))
    else:
        _print_text_report(results)
        code = _exit_code(results)
        if code == 0:
            print(f"\n{_GREEN}PARITY CLEAN — all families match within tolerance.{_NC}")
        else:
            n_fail = sum(1 for r in results if not r.ok)
            print(f"\n{_RED}PARITY FAILED — {n_fail} of {len(results)} families have differences.{_NC}")

    return _exit_code(results)


if __name__ == "__main__":
    raise SystemExit(main())
