#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""QG STEP 5.99 — ``SOURCE_RETURNED_ZERO`` reachable from an error/except branch MUST carry ``fetch_evidence=``.

Companion to STEP 5.86 (``check_unrouted_source_returned_zero.py``). Where 5.86 ratchets raw
``record_empty(SOURCE_RETURNED_ZERO)`` toward ``record_zero_rows`` routing, THIS check closes the
**proof-of-honest-absence** gap (failure-class C1, the operator's #1): a ``record_empty(...)`` /
``record_zero_rows(...)`` call that stamps ``SOURCE_RETURNED_ZERO`` **from inside an ``except`` /
error-classification branch** is exactly the bug shape — an adapter hit a 401/403/429/5xx/timeout/
exception, then fell through to honest-absence and marked the shard ``empty_confirmed`` when the data
could have been fetched with a code fix.

**Why this exists as a commit-time ratchet.** The keystone runtime gate (utl@39f8ec85) now
HARD-RAISES ``UnprovenHonestAbsenceError`` on a ``record_empty/record_zero_rows(reason=
SOURCE_RETURNED_ZERO)`` that lacks a ``FetchEvidence`` proving ``http_status in 2xx AND
response_received AND rows_in_response == 0 AND error_signal == ""`` (operator decision 2026-06-22).
This static check catches the same pattern at COMMIT time with a precise ``file:line`` so an adapter
never re-regresses to a runtime crash on a VM. It is the static twin of that runtime raise.

**What counts as a violation.** An ``ast.Call`` to ``.record_empty(...)`` or ``.record_zero_rows(...)``
whose call span mentions ``SOURCE_RETURNED_ZERO``, that is lexically reachable from an ``except``
handler (the call is nested inside an ``ast.ExceptHandler`` body), and that does NOT pass a
``fetch_evidence=`` keyword argument anywhere in the call. The ``except``-reachability scoping is what
distinguishes a genuine honest-absence write on the happy 2xx-empty path (which has its
``FetchEvidence`` built from a real response) from an error-branch fall-through that masks a fetch
failure as absence.

``EXPECTED_*`` calendar reasons are EXEMPT (no fetch was attempted — a delisted/not-yet-listed shard
needs no evidence). A call that carries an inline ``# QG-allow: <reason>`` marker is exempt (e.g. a
re-raise path that records the empty AFTER threading evidence on a separate line, or a genuinely-typed
service-output reason).

Baselined GRIND-DOWN ratchet (same mechanism + baseline file shape as STEP 5.86): the per-file count
of unproven except-reachable ``SOURCE_RETURNED_ZERO`` callsites is locked at baseline time; the count
only goes DOWN as the per-AG agents thread ``fetch_evidence`` (a 401/429/timeout/exception path then
routes to ``record_failed`` / ``attempted_failed``, NOT empty). A NEW such callsite (or a non-baselined
file with one) FAILS.

Usage::

    # per-repo (run by base-service.sh STEP 5.99):
    python check_source_returned_zero_needs_fetch_evidence.py --workspace-root <ws> --scope <repo-dir>

    # workspace-wide sweep:
    python check_source_returned_zero_needs_fetch_evidence.py --workspace-root <ws>

    # regenerate baseline (seed, or LOWER after an AG threads fetch_evidence):
    python check_source_returned_zero_needs_fetch_evidence.py --workspace-root <ws> --regenerate-baseline

SSOT: ``plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md`` Phase 1 (keystone) +
``codex/02-data/availability-manifest-and-data-status.md`` § "Proof-of-honest-absence contract".
Model: ``check_unrouted_source_returned_zero.py`` (AST per-repo scan + per-file count baseline).
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

#: Manifest write methods that, when passed ``SOURCE_RETURNED_ZERO`` from an error branch, must also
#: pass ``fetch_evidence=`` (proving the source was genuinely reached and returned 2xx + 0 rows).
TARGET_METHODS: Final[frozenset[str]] = frozenset({"record_empty", "record_zero_rows"})

#: The reason token whose presence in the call span marks it as a honest-absence (zero-rows) write.
ZERO_TOKEN: Final[str] = "SOURCE_RETURNED_ZERO"

#: The keyword argument that proves honest absence. Its presence (any value) satisfies the gate —
#: the RUNTIME ``UnprovenHonestAbsenceError`` then validates ``.proves_honest_absence()`` content.
EVIDENCE_KW: Final[str] = "fetch_evidence"

#: Inline marker (anywhere in the call span) that waives an audited callsite.
WHITELIST_MARKER: Final[str] = "QG-allow:"

#: ``EXPECTED_*`` calendar reasons are exempt — no fetch attempted, so no evidence is owed.
EXEMPT_REASON_PREFIX: Final[str] = "EXPECTED_"

#: Top-level dir names to skip when walking (mirrors check_unrouted_source_returned_zero.py).
EXCLUDE_DIR_NAMES: Final[frozenset[str]] = frozenset(
    {
        ".venv",
        ".venv-workspace",
        "venv",
        "node_modules",
        "build",
        "dist",
        "__pycache__",
        ".git",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "htmlcov",
        ".tox",
        "site-packages",
        "scripts",
        "tests",
        # Nested per-agent git worktrees (.claude/worktrees/<id>/) can carry an
        # older/different snapshot of the same repo's source — scanning one
        # produces false violations for code that doesn't exist in the actual
        # checked-out tree (found live 2026-08-06, same class as the
        # check_manifest_import_alignment.py / test_event_logging.py fixes).
        ".claude",
    }
)

#: Path-fragment patterns that indicate archived / generated trees.
EXCLUDE_PATH_FRAGMENTS: Final[tuple[str, ...]] = (
    "/archive/",
    "/.archive/",
    "/_archived/",
    ".egg-info",
)


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "source_returned_zero_needs_fetch_evidence_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    """Per-file maximum-allowed count of except-reachable SOURCE_RETURNED_ZERO writes lacking evidence."""

    counts: dict[str, int]
    note: str = ""

    def allowed(self, file_key: str) -> int:
        return int(self.counts.get(file_key, 0))

    def has(self, file_key: str) -> bool:
        return file_key in self.counts


def load_baseline() -> Baseline:
    path = _baseline_path()
    if not path.exists():
        return Baseline(counts={})
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    files_raw = raw.get("baseline") or {}
    counts: dict[str, int] = {}
    for file_key, val in files_raw.items():
        if isinstance(val, dict):
            counts[str(file_key)] = int(val.get("count", 0))
        else:
            counts[str(file_key)] = int(val)
    return Baseline(counts=counts, note=str(raw.get("note") or ""))


def write_baseline(counts: dict[str, int], existing: Baseline) -> None:
    path = _baseline_path()
    merged: dict[str, dict[str, int]] = {}
    for file_key in sorted(counts):
        observed = int(counts[file_key])
        if observed > 0:
            merged[file_key] = {"count": observed}
    header = (
        "# Baseline for QG STEP 5.99 — proof-of-honest-absence ratchet (Phase-1 keystone twin).\n"
        "#\n"
        "# Each entry: `baseline[<workspace-relative-file>].count` = MAX allowed count of\n"
        "# `record_empty/record_zero_rows(...SOURCE_RETURNED_ZERO...)` callsites that are reachable\n"
        "# from an `except`/error branch and do NOT pass `fetch_evidence=` (no inline `# QG-allow:`).\n"
        "# The gate FAILS (exit 1) for any file whose live count EXCEEDS its baseline (a NEW unproven\n"
        "# except-reachable callsite) OR any non-baselined file with >0 such callsites.\n"
        "#\n"
        "# GRIND-DOWN ratchet: threading `fetch_evidence` (so a 401/429/timeout/exception path routes\n"
        "# to record_failed instead of empty) only LOWERS counts (always passes). After an AG threads\n"
        "# its adapters, re-run `--regenerate-baseline` to LOCK the lower count so a regression fails.\n"
        "#\n"
        "# DO NOT hand-edit; auto-generated by\n"
        "#   check_source_returned_zero_needs_fetch_evidence.py --regenerate-baseline.\n"
        "#\n"
        "# Runtime twin: UTL ManifestWriter HARD-RAISES UnprovenHonestAbsenceError on the same pattern\n"
        "# (utl@39f8ec85, operator decision 2026-06-22). This static check catches it at commit time.\n"
        "#\n"
        "# SSOT: plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 1 +\n"
        "#       codex/02-data/availability-manifest-and-data-status.md "
        '"Proof-of-honest-absence contract".\n'
    )
    body = yaml.safe_dump(
        {
            "note": existing.note
            or "Seeded 2026-06-22 — Phase-1 keystone baseline of pre-threading unproven SOURCE_RETURNED_ZERO sites.",
            "baseline": merged,
        },
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
    )
    _ = path.write_text(header + body, encoding="utf-8")


def _iter_py_files(root: Path) -> Iterator[Path]:
    if root.is_file() and root.suffix == ".py":
        if not (set(root.parts) & EXCLUDE_DIR_NAMES):
            yield root
        return
    for path in root.rglob("*.py"):
        if set(path.parts) & EXCLUDE_DIR_NAMES:
            continue
        s = str(path).replace("\\", "/")
        if any(frag in s for frag in EXCLUDE_PATH_FRAGMENTS):
            continue
        yield path


def _call_has_evidence_kw(node: ast.Call) -> bool:
    """True if the call passes ``fetch_evidence=`` (keyword) or ``**kwargs`` forwarding it."""
    for kw in node.keywords:
        if kw.arg == EVIDENCE_KW:
            return True
        # A ``**evidence_kwargs`` splat could carry it — be conservative (treat as proven) so the
        # gate never false-fails a deliberate forwarding pattern; the runtime gate is the backstop.
        if kw.arg is None:
            return True
    return False


def _span_is_exempt(span: str) -> bool:
    """True if the call span carries a QG-allow waiver or only EXPECTED_* (calendar) reasons."""
    if WHITELIST_MARKER in span:
        return True
    # If the only honest-absence-ish token is EXPECTED_* and SOURCE_RETURNED_ZERO is absent, the
    # outer ZERO_TOKEN check already excluded it; this guards the rare both-present narrative line.
    return EXEMPT_REASON_PREFIX in span and ZERO_TOKEN not in span


def count_violations_in_file(path: Path) -> int:
    """Count except-reachable record_empty/record_zero_rows(SOURCE_RETURNED_ZERO) calls lacking evidence.

    A call is "except-reachable" when it lexically appears inside an ``ast.ExceptHandler`` body. We
    walk each handler's subtree so a call buried in a nested ``if``/``for``/helper-block inside the
    ``except`` still counts (the fall-through-to-empty bug nests the write under post-classification
    branching).
    """
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(
            f"[check_source_returned_zero_needs_fetch_evidence] skip unparseable {path}: {exc}",
            file=sys.stderr,
        )
        return 0
    lines = src.splitlines()
    seen: set[tuple[int, int]] = set()
    count = 0
    for handler in ast.walk(tree):
        if not isinstance(handler, ast.ExceptHandler):
            continue
        for node in ast.walk(handler):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute) or func.attr not in TARGET_METHODS:
                continue
            key = (node.lineno, node.col_offset)
            if key in seen:
                continue
            start = node.lineno - 1
            end = node.end_lineno if node.end_lineno is not None else node.lineno
            span = "\n".join(lines[start:end])
            if ZERO_TOKEN not in span:
                continue
            if _span_is_exempt(span):
                seen.add(key)
                continue
            if _call_has_evidence_kw(node):
                seen.add(key)
                continue
            seen.add(key)
            count += 1
    return count


@dataclass(frozen=True)
class FileScan:
    file_key: str  # workspace-relative POSIX path
    count: int


def _scan_scopes(workspace_root: Path, scope: str | None) -> list[FileScan]:
    if scope:
        roots = [workspace_root / scope]
    else:
        roots = [
            child
            for child in sorted(workspace_root.iterdir())
            if child.is_dir()
            and child.name not in EXCLUDE_DIR_NAMES
            and not child.name.startswith(".")
            and (child / "pyproject.toml").exists()
        ]
    results: list[FileScan] = []
    for root in roots:
        if not root.is_dir():
            print(
                f"[check_source_returned_zero_needs_fetch_evidence] scope dir not found: {root}",
                file=sys.stderr,
            )
            continue
        for py in _iter_py_files(root):
            count = count_violations_in_file(py)
            if count == 0:
                continue
            rel = py.relative_to(workspace_root).as_posix()
            results.append(FileScan(file_key=rel, count=count))
    return results


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Proof-of-honest-absence ratchet — except-reachable SOURCE_RETURNED_ZERO needs "
        "fetch_evidence (QG STEP 5.99 / Phase-1 keystone twin).",
    )
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--scope", default=None, help="Single repo dir name to scope to (per-repo QG mode).")
    parser.add_argument(
        "--regenerate-baseline",
        action="store_true",
        help="Rewrite the baseline with observed counts workspace-wide (RAISES or LOWERS as needed).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    workspace_root: Path = args.workspace_root.resolve()
    baseline = load_baseline()

    if args.regenerate_baseline:
        scans = _scan_scopes(workspace_root, scope=None)
        observed = {s.file_key: s.count for s in scans}
        write_baseline(observed, baseline)
        print(f"[check_source_returned_zero_needs_fetch_evidence] baseline rewritten at {_baseline_path()}")
        print(
            f"[check_source_returned_zero_needs_fetch_evidence] {len(observed)} file(s) with unproven "
            "except-reachable callsites recorded."
        )
        for file_key in sorted(observed):
            print(f"  {file_key}: {observed[file_key]}")
        return 0

    scans = _scan_scopes(workspace_root, args.scope)
    observed = {s.file_key: s.count for s in scans}

    def in_scope(file_key: str) -> bool:
        if not args.scope:
            return True
        return file_key.split("/", 1)[0] == args.scope

    errors: list[str] = []
    pending: list[str] = []
    progressed: list[str] = []

    for file_key, count in sorted(observed.items()):
        allowed = baseline.allowed(file_key)
        if not baseline.has(file_key):
            errors.append(
                f"[ERROR] {file_key}: {count} except-reachable record_empty/record_zero_rows"
                f"(SOURCE_RETURNED_ZERO) callsite(s) WITHOUT fetch_evidence=, file NOT in baseline. "
                f"Build a FetchEvidence at the adapter HTTP site (the classify_venue_error() call) and "
                f"pass fetch_evidence= — a 401/403/429/5xx/timeout/exception path then routes to "
                f"record_failed (attempted_failed), NOT empty. Add an inline '# {WHITELIST_MARKER} <reason>' "
                f"for an audited callsite, or add to the baseline via --regenerate-baseline."
            )
        elif count > allowed:
            errors.append(
                f"[ERROR] {file_key}: {count} unproven except-reachable callsite(s) > baseline {allowed} "
                f"— a NEW record_empty/record_zero_rows(SOURCE_RETURNED_ZERO) without fetch_evidence= was "
                f"added on an error branch. Thread fetch_evidence= or '# {WHITELIST_MARKER}'."
            )
        elif count < allowed:
            progressed.append(
                f"[INFO] {file_key}: {count} < baseline {allowed} — fetch_evidence threading progress; "
                f"re-run --regenerate-baseline to lock."
            )
        else:
            pending.append(
                f"[WARN] {file_key}: {count} baselined unproven SOURCE_RETURNED_ZERO callsite(s) pending "
                f"fetch_evidence threading (Phase-1)."
            )

    for file_key in sorted(baseline.counts):
        if in_scope(file_key) and file_key not in observed:
            progressed.append(
                f"[INFO] {file_key}: 0 < baseline {baseline.allowed(file_key)} — fully threaded; "
                f"re-run --regenerate-baseline to drop from baseline."
            )

    for line in pending:
        print(line)
    for line in progressed:
        print(line)
    for line in errors:
        print(line, file=sys.stderr)

    if errors:
        print(
            f"\n[check_source_returned_zero_needs_fetch_evidence] FAIL — {len(errors)} file(s) with "
            f"new/non-baselined except-reachable SOURCE_RETURNED_ZERO callsites lacking fetch_evidence "
            f"({len(pending)} baselined pending).\n"
            "→ Proof-of-honest-absence contract: a SOURCE_RETURNED_ZERO write reachable from an except\n"
            "  branch MUST carry a FetchEvidence proving http 2xx + response_received + 0 rows + no\n"
            "  error_signal (UTL ManifestWriter raises UnprovenHonestAbsenceError otherwise). An error\n"
            "  path (401/429/5xx/timeout/exception) is NOT honest absence → record_failed.\n"
            "  SSOT: codex/02-data/availability-manifest-and-data-status.md "
            '"Proof-of-honest-absence contract".',
            file=sys.stderr,
        )
        return 1

    print(
        f"[check_source_returned_zero_needs_fetch_evidence] OK — {len(pending)} baselined pending, "
        f"{len(progressed)} threaded/in-progress; 0 new unproven callsites"
        + (f" (scope={args.scope})." if args.scope else " (workspace-wide).")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
