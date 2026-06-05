#!/usr/bin/env python3
"""QG STEP 5.86 — fleet-wide ``SOURCE_RETURNED_ZERO`` routing ratchet (A10c-fleet).

Generalises the DeFi-MTDS-only A10c check (``scripts/qg/no_unrouted_source_returned_zero.sh``,
zero-tolerance, scoped to ``DefiManifestRecorder`` DeFi handlers) to EVERY service / asset_group.

**Why a baselined ratchet, not a bare grep-fail.** A10c (DeFi) could be zero-tolerance because the
DeFi handlers were already migrated to ``DefiManifestRecorder.record_zero_rows`` (A10d). Across the
rest of the fleet there are MANY existing raw ``record_empty(reason=SOURCE_RETURNED_ZERO)`` callsites
(tradfi / sports / prediction / features / instruments engine + adapter paths) that each AG-slot will
migrate to the generic UTL ``ManifestWriter.record_zero_rows(...)`` (plan §A10b) on its own schedule.
A flag-day grep-fail would break every repo's gate on day one. So this is a **grind-down ratchet**:

  * ``unrouted_source_returned_zero_baseline.yaml`` records the per-file count of raw, unrouted
    ``record_empty(...SOURCE_RETURNED_ZERO...)`` callsites at baseline time.
  * A file whose live count is ``<=`` its baseline PASSES (migration progress only lowers the count).
  * A file whose live count is ``>`` its baseline FAILS (a NEW unrouted callsite was added).
  * A file NOT in the baseline with ``>0`` unrouted callsites FAILS (route via ``record_zero_rows``,
    add an inline ``# QG-allow:`` waiver, or add it to the baseline via ``--regenerate-baseline``).

This makes the honest-absence routing backstop **un-bypassable fleet-wide** while letting each
asset_group grind its callsites down to zero without a coordinated flag-day. As AGs migrate, re-run
``--regenerate-baseline`` to LOWER the locked counts so a regression (re-adding a raw callsite) fails.

**What counts as an unrouted callsite.** An ``ast.Call`` to ``.record_empty(...)`` whose source span
mentions ``SOURCE_RETURNED_ZERO`` and does NOT carry an inline ``# QG-allow:`` marker anywhere in the
call span. The generic UTL ``record_zero_rows(was_expected=<per-AG oracle>, ...)`` is the sanctioned
replacement: it routes a genuinely-empty shard to ``empty_confirmed`` but a source that returned
nothing for a shard the per-AG "expected universe" oracle says SHOULD have had data to
``attempted_failed`` (the ``EmptyFromLiveInstrumentError`` backstop). The per-AG oracle is
``was_instrument_alive(venue, instrument_id, day)`` (cefi/defi/tradfi/prediction) or a fixture lookup
(sports). A genuinely-typed-reason callsite where ``record_zero_rows`` does not apply (e.g. a
service-output / computed-output manifest, ``pipeline-mode-not-applicable``) is exempt via an inline
``# QG-allow: <reason>`` marker on (any line of) the call.

``record_empty`` / ``record_zero_rows`` internal definitions in UTL ``manifest_writer.py`` and the
``DefiManifestRecorder`` wrapper ARE the sanctioned implementation, not adapter callsites — they carry
a ``# QG-allow: record-zero-rows-internal`` marker (or are simply baselined).

Usage::

    # per-repo (run by base-service.sh STEP 5.86):
    python check_unrouted_source_returned_zero.py --workspace-root <ws> --scope <repo-dir>

    # workspace-wide sweep (no --scope):
    python check_unrouted_source_returned_zero.py --workspace-root <ws>

    # regenerate baseline (after migration that intentionally lowers counts, or to seed):
    python check_unrouted_source_returned_zero.py --workspace-root <ws> --regenerate-baseline

SSOT: ``plans/active/defi_manifest_canonicalisation_2026_06_01.md`` §A10c-fleet (+ each AG's
``*_manifest_canonicalisation_2026_06_01.md``). Model: ``check_pipeline_mode_explicit_at_record_calls.py``
(AST per-repo scan) + ``check_adapter_contract_regression.py`` (per-file count baseline).
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

#: The manifest write method that, when passed a ``SOURCE_RETURNED_ZERO`` reason, must instead route
#: through ``record_zero_rows``. (Only ``record_empty`` — ``record_failed`` is already the
#: attempted_failed branch ``record_zero_rows`` itself calls.)
TARGET_METHOD: Final[str] = "record_empty"

#: The reason token whose presence in a ``record_empty`` call span marks it as a zero-rows write.
ZERO_TOKEN: Final[str] = "SOURCE_RETURNED_ZERO"

#: Inline marker (anywhere in the call span) that waives an audited, genuinely-typed-reason callsite.
WHITELIST_MARKER: Final[str] = "QG-allow:"

#: Top-level dir names to skip when walking. Mirrors check_pipeline_mode_explicit_at_record_calls.
#: ``scripts`` excludes one-shot migration tooling (rebuild_*_manifest.py, reset_*_manifest.py);
#: ``tests`` excludes test fixtures.
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
    return Path(__file__).resolve().parent / "unrouted_source_returned_zero_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    """Per-file maximum-allowed count of unrouted ``record_empty(SOURCE_RETURNED_ZERO)`` callsites."""

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
        "# Baseline for QG STEP 5.86 — fleet-wide SOURCE_RETURNED_ZERO routing ratchet (A10c-fleet).\n"
        "#\n"
        "# Each entry: `baseline[<workspace-relative-file>].count` = MAX allowed count of unrouted\n"
        "# `record_empty(...SOURCE_RETURNED_ZERO...)` callsites (no inline `# QG-allow:` waiver) in that\n"
        "# file. The gate FAILS (exit 1) for any file whose live count EXCEEDS its baseline (a NEW\n"
        "# unrouted callsite) OR any non-baselined file with >0 unrouted callsites.\n"
        "#\n"
        "# This is a GRIND-DOWN ratchet: migration to `record_zero_rows` only LOWERS counts (always\n"
        "# passes). After an AG migrates, re-run `--regenerate-baseline` to LOCK the lower count so a\n"
        "# re-added raw callsite fails. A genuinely-typed-reason callsite where `record_zero_rows` does\n"
        "# not apply (service-output / computed output / pipeline-mode-not-applicable) gets an inline\n"
        "# `# QG-allow: <reason>` marker instead of a baseline entry.\n"
        "#\n"
        "# DO NOT hand-edit; auto-generated by check_unrouted_source_returned_zero.py --regenerate-baseline.\n"
        "#\n"
        "# SSOT: plans/active/defi_manifest_canonicalisation_2026_06_01.md §A10c-fleet\n"
        "#       (+ each AG's *_manifest_canonicalisation_2026_06_01.md migration todo).\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note
            or "Seeded 2026-06-05 (slot-1) — A10c-fleet baseline of pre-migration unrouted callsites.",
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


def count_unrouted_in_file(path: Path) -> int:
    """Count ``record_empty(...SOURCE_RETURNED_ZERO...)`` call nodes lacking a ``# QG-allow:`` waiver.

    AST-bounded so docstring / comment / migration-narrative mentions of ``SOURCE_RETURNED_ZERO``
    elsewhere in the file do not match — only the source span of an actual ``.record_empty(...)`` call
    is inspected.
    """
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        print(f"[check_unrouted_source_returned_zero] skip unparseable {path}: {exc}", file=sys.stderr)
        return 0
    lines = src.splitlines()
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != TARGET_METHOD:
            continue
        start = node.lineno - 1
        end = node.end_lineno if node.end_lineno is not None else node.lineno
        span = "\n".join(lines[start:end])
        if ZERO_TOKEN not in span:
            continue
        if WHITELIST_MARKER in span:
            continue
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
            print(f"[check_unrouted_source_returned_zero] scope dir not found: {root}", file=sys.stderr)
            continue
        for py in _iter_py_files(root):
            count = count_unrouted_in_file(py)
            if count == 0:
                continue
            rel = py.relative_to(workspace_root).as_posix()
            results.append(FileScan(file_key=rel, count=count))
    return results


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fleet-wide SOURCE_RETURNED_ZERO routing ratchet (QG STEP 5.86 / A10c-fleet).",
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
        print(f"[check_unrouted_source_returned_zero] baseline rewritten at {_baseline_path()}")
        print(f"[check_unrouted_source_returned_zero] {len(observed)} file(s) with unrouted callsites recorded.")
        for file_key in sorted(observed):
            print(f"  {file_key}: {observed[file_key]}")
        return 0

    scans = _scan_scopes(workspace_root, args.scope)
    observed = {s.file_key: s.count for s in scans}

    # In --scope mode, only judge files under the scoped repo (a baselined file in another repo is
    # that repo's gate's concern). Identify the scoped baseline subset.
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
                f"[ERROR] {file_key}: {count} unrouted record_empty(SOURCE_RETURNED_ZERO) callsite(s), "
                f"file NOT in baseline. Route via ManifestWriter.record_zero_rows(was_expected=<oracle>, ...), "
                f"add an inline '# {WHITELIST_MARKER} <reason>' for a genuinely-typed-reason callsite, "
                f"or (if intentionally deferred) add to the baseline via --regenerate-baseline."
            )
        elif count > allowed:
            errors.append(
                f"[ERROR] {file_key}: {count} unrouted callsite(s) > baseline {allowed} — a NEW raw "
                f"record_empty(SOURCE_RETURNED_ZERO) was added. Use record_zero_rows(...) or '# {WHITELIST_MARKER}'."
            )
        elif count < allowed:
            progressed.append(
                f"[INFO] {file_key}: {count} < baseline {allowed} — migration progress; "
                f"re-run --regenerate-baseline to lock."
            )
        else:
            pending.append(f"[WARN] {file_key}: {count} baselined unrouted callsite(s) pending A10c-fleet migration.")

    # A baselined file that no longer appears in observed (count dropped to 0) is fully migrated.
    for file_key in sorted(baseline.counts):
        if in_scope(file_key) and file_key not in observed:
            progressed.append(
                f"[INFO] {file_key}: 0 < baseline {baseline.allowed(file_key)} — fully migrated; "
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
            f"\n[check_unrouted_source_returned_zero] FAIL — {len(errors)} file(s) with new/non-baselined "
            f"unrouted SOURCE_RETURNED_ZERO callsites ({len(pending)} baselined pending).\n"
            "→ Generic routing helper: unified_trading_library ManifestWriter.record_zero_rows(\n"
            "    row_key=..., reason='SOURCE_RETURNED_ZERO', was_expected=<per-AG oracle>, pipeline_mode=...).\n"
            "  Oracle: UAC was_instrument_alive(venue, instrument_id, day) (cefi/defi/tradfi/prediction)\n"
            "  or a sports fixture lookup. SSOT: defi_manifest_canonicalisation_2026_06_01.md §A10c-fleet.",
            file=sys.stderr,
        )
        return 1

    print(
        f"[check_unrouted_source_returned_zero] OK — {len(pending)} baselined pending, "
        f"{len(progressed)} migrated/in-progress; 0 new unrouted callsites"
        + (f" (scope={args.scope})." if args.scope else " (workspace-wide).")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
