#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Plan operator-ruling evidence gate — a checked todo or resolved_by: claiming completion via
an "operator ruling" must cite a traceable source within 300 chars of the ruling phrase.

Two incidents, 4 days apart, different roles:
  1. plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md
     (SHA fabrication — the sibling check_plan_commit_sha_evidence.py gate was shipped for that).
  2. plans/active/issues/tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md
     (slot-9 closed an [OPERATOR]-tagged decision citing "DECIDED 2026-08-03 (operator ruling)"
     with no traceable source; a corpus-wide grep for its subject returned zero other docs).

The SHA checker structurally cannot catch shape (2) — there is no SHA to resolve. A fabricated
ruling yields an authority bypass: an [OPERATOR]-gated decision, the one class this workspace
reserves for a human, silently closed by a worker.

The counter-example that passes: Finding I-2 in the same audit doc cites
"operator ruling on `plan_reconcile_parked_operator_decisions_2026_08_02.md`" — a real,
checkable pointer, exactly the standard E-1 conspicuously did not meet.

What counts as a "traceable source" (any ONE, within ±300 chars of the ruling phrase):
  - A /plans/… or /codex/… path substring, OR
  - Any .md filename reference (e.g., plan_reconcile_parked_operator_decisions_2026_08_02.md).

Detected "operator ruling" phrases (case-insensitive):
  - "operator ruling"       — direct form, e.g., "DECIDED 2026-08-03 (operator ruling)"
  - "operator, interactive" — interactive-session form, e.g., "(operator, interactive)"

Scope: checked `- [x]` todo blocks and resolved_by: frontmatter in plans/active/*.md and
plans/active/issues/*.md.

Baselined ratchet (same shape as check_plan_commit_sha_evidence.py): the corpus may already
carry pre-existing unsourced closures — those are grandfathered at first rollout; only new
regressions (fresh unsourced rulings that push the count above the baseline) fail. Re-baseline
with --baseline-write ONLY after confirming the flagged violation is pre-existing, non-fabricated
drift, not a new authority bypass.

Exit codes: 0 = at/below baseline; 1 = regression; 2 = arg/IO error.

``--only <paths>`` (2026-08-09, precommit migration — root-caused after this ratchet regressed
5x in one day, 58->76, entirely via the docs(plans) fast path / safe-doc-push.sh, which runs
run_hygiene_sweep.sh --precommit and NEVER invoked this script at all): the corpus-wide/baselined
mode above is precommit-unsafe for the same reason check_terminal_status_archived.py's is — a
huge pre-existing backlog (58+) would false-block every commit if run as a blocking gate. But an
unsourced 'operator ruling' citation in a file YOU are actively staging is unconditionally wrong
regardless of the rest of the corpus's backlog (same reasoning check_terminal_status_archived.py
--only already established) — no baseline needed for a single-file check. Wired into
run_hygiene_sweep.sh's STAGED_PLANS precommit block so the fast doc-commit path — the one that
was actually producing this drift all day, invisible to every code-commit-only quickmerge run
until hours later — now catches a NEW unsourced citation at commit time instead of letting it
land and surface as a corpus-wide QG failure someone has to firefight after the fact.

**Pre-existing-debt exemption (2026-08-09, plan_hygiene_ratchet_regressions_outpace_serial_ci_
fix_velocity_2026_08_09.md "New facet"):** `--only` originally flagged EVERY violation in a staged
file regardless of whether it already existed at HEAD — measured live: a routine, fully-unrelated
context_scope-maintenance sweep touching ~270 docs hit 39 files failing this check on
pre-existing, untouched citations, none introduced by that session, with no way to proceed short
of excluding all 39 from the commit. Same shape + fix as check_effort_signal_ratchet.py's
`_was_silent_default_at_head`: a violation is compared by identity (ruling phrase + context
snippet) against the violation set already present in the file's committed HEAD version — a
citation that was ALREADY unsourced at HEAD is pre-existing debt and is skipped; a citation that
is new (brand-new file, brand-new ruling phrase, or an edit that changes an existing citation's
context) still flags. This is the same "flag only what THIS COMMIT INTRODUCES" contract the
corpus-wide baselined-ratchet mode above already has — `--only` just didn't inherit it.
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml


def _pm_root_or_legacy(workspace_root):
    """PM checkout root resolved by CONTENT, not by directory NAME (F7, 2026-08-10).

    See scripts/quality_gates/_pm_root.py for why. Behaviour-preserving in a canonically
    named checkout; fixes resolution when running from a git worktree."""
    import pathlib as _pathlib
    import sys as _sys

    _d = str(_pathlib.Path(__file__).resolve().parent)
    if _d not in _sys.path:
        _sys.path.insert(0, _d)
    from _pm_root import pm_root_or_legacy as _impl

    return _impl(workspace_root)


DEFAULT_BASELINE_PATH = Path(__file__).parent / "plan_operator_ruling_evidence_baseline.yaml"

# unified-trading-pm repo root — baseline paths are stored relative to this so the file is
# byte-identical no matter which slot/host regenerates it.
_PM_ROOT = Path(__file__).resolve().parents[2]

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n", re.DOTALL)
_CHECKED_RE = re.compile(r"^\s*-\s*\[[xX]\]\s")
_UNCHECKED_OR_CHECKED_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s")

# Phrases that indicate an operator ruling is being CLAIMED as completion justification.
# Matches (case-insensitive):
#   "operator ruling"       — direct form, e.g., "DECIDED (operator ruling)"
#   "operator, interactive" — interactive-session form, e.g., "(operator, interactive)"
_OPERATOR_RULING_RE = re.compile(
    r"\boperator\s+ruling\b|\boperator,\s*interactive\b",
    re.IGNORECASE,
)

# A traceable source for the ruling: /plans/ or /codex/ path, or any .md filename reference.
# Requires at least 2 chars before ".md" to avoid degenerate matches.
_TRACEABLE_SOURCE_RE = re.compile(
    r"/plans/|/codex/|\b[\w][\w\-]+\.md\b",
)

# Characters after the ruling-phrase start to search for a traceable source.
# Small lookback (50) for rare cases where the source appears just before the phrase.
_RULING_WINDOW_AFTER = 300
_RULING_WINDOW_BEFORE = 50


@dataclass(frozen=True)
class RulingCitation:
    path: Path
    line_no: int
    phrase: str  # the matched operator-ruling phrase
    source: str  # "frontmatter:resolved_by" | "todo"
    context: str  # ~160-char snippet for the printed diagnostic


@dataclass(frozen=True)
class RulingViolation:
    citation: RulingCitation

    def __str__(self) -> str:
        return (
            f"{self.citation.path}:{self.citation.line_no}: "
            f"[{self.citation.source}] completion cites '{self.citation.phrase}' "
            f"with no traceable source (/plans/…, /codex/…, or .md doc) "
            f"within {_RULING_WINDOW_AFTER} chars — {self.citation.context}"
        )


def _has_traceable_source(text: str, match_start: int) -> bool:
    """True iff a /plans/, /codex/, or .md filename appears within the search window around
    the operator-ruling phrase start in `text`."""
    window = text[max(0, match_start - _RULING_WINDOW_BEFORE) : match_start + _RULING_WINDOW_AFTER]
    return bool(_TRACEABLE_SOURCE_RE.search(window))


def _iter_frontmatter_ruling_citations(text: str, path: Path) -> list[RulingCitation]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return []
    fm_text = m.group(1)
    try:
        fm = cast(object, yaml.safe_load(io.StringIO(fm_text)))
    except yaml.YAMLError:
        return []
    if not isinstance(fm, dict):
        return []
    fm_dict = cast(dict[str, object], fm)
    raw = fm_dict.get("resolved_by")
    if not raw:
        return []
    resolved_by_str = raw if isinstance(raw, str) else str(raw)

    line_no = 1
    for i, line in enumerate(text.splitlines(), start=1):
        if line.strip().startswith("resolved_by:"):
            line_no = i
            break

    out: list[RulingCitation] = []
    for rm in _OPERATOR_RULING_RE.finditer(resolved_by_str):
        if not _has_traceable_source(resolved_by_str, rm.start()):
            out.append(
                RulingCitation(
                    path=path,
                    line_no=line_no,
                    phrase=rm.group(0),
                    source="frontmatter:resolved_by",
                    context=resolved_by_str.strip()[:160],
                )
            )
    return out


def _iter_todo_ruling_citations(text: str, path: Path) -> list[RulingCitation]:
    out: list[RulingCitation] = []
    lines = text.splitlines()
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        if _CHECKED_RE.match(line):
            buf = [line]
            j = i + 1
            while j < n:
                nxt = lines[j]
                if _UNCHECKED_OR_CHECKED_RE.match(nxt) or not nxt.strip():
                    break
                buf.append(nxt)
                j += 1
            block_text = "\n".join(buf)
            for rm in _OPERATOR_RULING_RE.finditer(block_text):
                if not _has_traceable_source(block_text, rm.start()):
                    out.append(
                        RulingCitation(
                            path=path,
                            line_no=i + 1,
                            phrase=rm.group(0),
                            source="todo",
                            context=buf[0].strip()[:160],
                        )
                    )
                    # One violation per block is enough; stop on first unsourced match.
                    break
            i = j
        else:
            i += 1
    return out


def _load_baseline(baseline_path: Path) -> int:
    if not baseline_path.exists():
        return 0
    try:
        loaded = cast(object, yaml.safe_load(baseline_path.read_text(encoding="utf-8")))
    except yaml.YAMLError:
        return 0
    if isinstance(loaded, dict):
        count = cast(dict[str, object], loaded).get("unsourced_ruling_baseline")
        if isinstance(count, int):
            return count
    return 0


def _write_baseline(baseline_path: Path, violations: list[RulingViolation]) -> None:
    payload: dict[str, object] = {
        "unsourced_ruling_baseline": len(violations),
        "rule": "plan-operator-ruling-evidence (ratchet)",
        "source": "plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md",
        "baseline_violations": [
            {
                # Repo-root-relative, NOT absolute (2026-08-09). Storing resolved absolute paths
                # made this file specific to whichever clone last regenerated it -- a run from a
                # different slot/host rewrote all N entries, so a real ratchet-DOWN was
                # indistinguishable from path churn in review. That is precisely the noise that
                # invites the "just re-baseline it" reflex which took this ratchet 58 -> 76.
                # See plans/active/issues/operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md.
                # Only `unsourced_ruling_baseline` is ever read back; this list is a human record.
                "path": str(v.citation.path.resolve().relative_to(_PM_ROOT)),
                "line": v.citation.line_no,
                "phrase": v.citation.phrase,
                "context": v.citation.context[:80],
            }
            for v in violations
        ],
    }
    baseline_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _violations_for_text(text: str, p: Path) -> list[RulingViolation]:
    """Pure content-level scan, so the same rule can be applied to a working-tree file AND
    to a `git show HEAD:<path>` blob without a second implementation (mirrors
    check_effort_signal_ratchet.py's _is_silent_default_text split)."""
    out: list[RulingViolation] = []
    for citation in _iter_frontmatter_ruling_citations(text, p):
        out.append(RulingViolation(citation=citation))
    for citation in _iter_todo_ruling_citations(text, p):
        out.append(RulingViolation(citation=citation))
    return out


def _violations_for_file(p: Path) -> list[RulingViolation]:
    """Shared by the corpus-wide glob and the --only path so the two modes can never
    silently diverge on what counts as a violation."""
    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return _violations_for_text(text, p)


def _violations_at_head(p: Path) -> list[RulingViolation]:
    """Violations already present in the committed HEAD version of this file.

    A file absent from HEAD (brand-new) returns [] — a new file introducing an unsourced
    ruling citation IS the growth this check exists to stop, so it must still flag.
    """
    proc = subprocess.run(
        ["git", "-C", str(_PM_ROOT), "show", f"HEAD:{p.resolve().relative_to(_PM_ROOT)}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return _violations_for_text(proc.stdout, p)


def _violation_identity(v: RulingViolation) -> tuple[str, str]:
    """(phrase, context) — stable enough to match "the same citation" across an unrelated
    edit elsewhere in the file, but changes if the citation text itself is edited (which
    correctly re-earns scrutiny rather than silently staying grandfathered forever)."""
    return (v.citation.phrase, v.citation.context)


def _run_only(paths: list[str], quiet: bool) -> int:
    """Precommit-scoped mode: check exactly the given staged files.

    Flags only what THIS COMMIT INTRODUCES — a citation already unsourced at HEAD is
    pre-existing debt and is skipped (2026-08-09; see the module docstring's --only
    section). A pre-existing violation in a file you happen to be touching for an
    unrelated reason must not block that commit; a brand-new unsourced citation still
    does.
    """
    violations: list[RulingViolation] = []
    for raw in paths:
        p = Path(raw)
        if not p.is_absolute():
            p = Path.cwd() / p
        current = _violations_for_file(p)
        if not current:
            continue
        already_at_head = {_violation_identity(v) for v in _violations_at_head(p)}
        violations.extend(v for v in current if _violation_identity(v) not in already_at_head)

    if not quiet:
        for v in violations:
            print(f"  {v}")

    n = len(violations)
    print(f"{'✅' if n == 0 else '❌'} check_plan_operator_ruling_evidence (--only): {n} violation(s) in staged files")
    return 0 if n == 0 else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plan operator-ruling evidence check: checked todos claiming completion via "
            "an 'operator ruling' must cite a traceable source (/plans/…, /codex/…, or .md doc)."
        )
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(__file__).resolve().parents[2].parent,
    )
    parser.add_argument("--baseline-path", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--baseline-write", action="store_true")
    return parser.parse_args()


def main() -> int:
    quiet = "--quiet" in sys.argv
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        return _run_only(sys.argv[idx + 1 :], quiet)

    ns = _parse_args()
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)

    active_dir = (_pm_root_or_legacy(workspace_root)) / "plans" / "active"
    if not active_dir.is_dir():
        print(f"ERROR: plans/active not found at {active_dir}", file=sys.stderr)
        return 2

    plan_files = sorted(active_dir.glob("*.md"))
    issues_dir = active_dir / "issues"
    if issues_dir.is_dir():
        plan_files.extend(sorted(issues_dir.glob("*.md")))

    all_violations: list[RulingViolation] = []
    for p in plan_files:
        all_violations.extend(_violations_for_file(p))

    # De-dupe by (path, line_no) — a single block can generate at most one violation.
    seen: set[tuple[Path, int]] = set()
    deduped: list[RulingViolation] = []
    for v in all_violations:
        key = (v.citation.path, v.citation.line_no)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(v)
    violations = deduped

    print(
        f"Scanned {len(plan_files)} plan(s) — "
        f"{len(violations)} checked todo(s)/resolved_by: value(s) citing 'operator ruling' "
        f"without a traceable source (/plans/…, /codex/…, or .md doc within "
        f"{_RULING_WINDOW_AFTER} chars)."
    )

    if baseline_write:
        # A RAISE must be loud. This ratchet went 58 -> 76 in a single day through silent
        # --baseline-write calls, absorbing 18 real violations; nothing printed, so nothing was
        # defended in a commit message and the debt became invisible. Mirrors the warning
        # check_ao_dispatch_visibility_gate.py already emits on its own axes.
        # SSOT: plans/active/issues/operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md
        previous = _load_baseline(baseline_path)
        _write_baseline(baseline_path, violations)
        print(f"✅ Wrote baseline ({len(violations)}) to {baseline_path}")
        if len(violations) > previous:
            print(
                f"WARNING: unsourced_ruling_baseline RAISED {previous} -> {len(violations)} -- a shrinking ratchet\n"
                "  must only go DOWN. Verify this is a reviewed, justified raise and say why in the commit message;\n"
                "  the correct default is to fix or file the new violations instead.",
                file=sys.stderr,
            )
        return 0

    baseline = _load_baseline(baseline_path)
    regression = len(violations) > baseline
    if violations:
        print(f"\nUnsourced operator-ruling citations: {len(violations)} (baseline {baseline}).")
        for v in violations[:20]:
            try:
                rel = v.citation.path.relative_to(workspace_root)
            except ValueError:
                rel = v.citation.path
            print(f"  - {rel}:{v.citation.line_no}: [{v.citation.source}] {v.citation.phrase!r}")
        if len(violations) > 20:
            print(f"  ... + {len(violations) - 20} more")

    if regression:
        print(
            f"\n❌ Plan-operator-ruling-evidence regression: {len(violations)} > baseline {baseline}. "
            "A checked todo or resolved_by: field claims an 'operator ruling' with no traceable "
            f"source (/plans/…, /codex/…, or .md doc within {_RULING_WINDOW_AFTER} chars of the "
            "ruling phrase). Add a specific doc/path reference to the ruling citation — see "
            "plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md "
            "§ 'Done when' for the standard. Or re-baseline with --baseline-write after "
            "confirming the violation is pre-existing, non-fabricated drift."
        )
        return 1

    if violations and len(violations) < baseline:
        print(f"\n⚠️  Improvement: {len(violations)} < baseline {baseline}. Re-baseline to codify.")
    print("\n✅ Plan-operator-ruling-evidence: at/below baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
