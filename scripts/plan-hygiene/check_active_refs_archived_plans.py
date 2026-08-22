#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Archive-safety ratchet: an active-corpus doc must never cite a `/plans/archive/...`
path directly — it should cite the CODEX doc that now holds that archived plan's durable
content instead (operator ruling 2026-08-17).

WHY: `check_reference_paths.py` only catches a reference that fails to RESOLVE — a
`/plans/archive/issues/foo.md` citation resolves fine (the file is really there), so it
sails through that gate clean even though, per the archival ritual
(`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` step 5), it
shouldn't exist: archiving a plan is supposed to migrate its durable/reusable content into
a codex SSOT and repoint every referrer at THAT, not at the archived plan itself. Left
unenforced, this repeatedly produced two live failure modes the same night this checker
was built: (1) a referrer's `related:` entry silently rotting the moment its target moves
from `plans/active/` to `plans/archive/` (caught only by check_reference_paths when the
archival ALSO happens to break existence — not when it doesn't), and (2) durable facts
living only inside an archived plan with no codex home, so the fact effectively
disappears from the corpus's live, discoverable knowledge the moment the plan archives.

SHAPE: a standard SHRINKING ratchet, same pattern as check_reference_paths.py /
check_defi_address_citations.py — NOT zero-tolerance from day 1 (archival has predated
this rule for months, so the corpus-wide baseline is real pre-existing debt, not a bug
this checker introduced), but it must never grow. `--only <files>` is the precommit-time
mode (wired into quality-gates.sh's already-scoped doc-tree check, § "per-doc-type
frontmatter schema check" neighbour) — checks ONLY the given staged files' OWN content
for a `/plans/archive/...` citation, no baseline math, so a commit that adds a fresh
archive-plan citation is unconditionally wrong regardless of the rest of the corpus's
pre-existing debt. This adds ~zero runtime to an unrelated push: it only re-parses the
files already being scanned by the neighbouring frontmatter check, no corpus walk.

Usage:
  python3 scripts/plan-hygiene/check_active_refs_archived_plans.py [--quiet] [--update-baseline]
  python3 scripts/plan-hygiene/check_active_refs_archived_plans.py --only <path> [<path> ...]

Exit 0 if the corpus-wide count is <= baseline (or, in --only mode, if none of the given
files cite a `/plans/archive/...` path). NEVER hand-raise the baseline — if the count needs
to go up, something regressed; fix the citation (repoint at codex) instead. Ratchet DOWN as
the pre-existing debt gets cleaned up: fix real violations, then re-run --update-baseline.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

PM_DIR = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).resolve().parent / "active_refs_archived_plans_baseline.yaml"

# A leading-slash reference into plans/archive/ — the exact shape check_reference_paths.py's
# GOOD_REF_RE already validates as a well-formed, resolving path; this checker flags it for a
# DIFFERENT reason (it points at the wrong destination class, not a broken one).
ARCHIVE_REF_RE = re.compile(r"/plans/archive/[A-Za-z0-9_./-]+\.md")


@dataclass(frozen=True)
class Baseline:
    count: int = 0
    note: str = ""


def load_baseline() -> Baseline:
    if not BASELINE_PATH.exists():
        return Baseline()
    raw = yaml.safe_load(BASELINE_PATH.read_text(encoding="utf-8")) or {}
    return Baseline(count=int(raw.get("count", 0)), note=str(raw.get("note") or ""))


def write_baseline(count: int, existing: Baseline) -> None:
    """Persist a new baseline. Clamped DOWN only — never raised above the existing
    baseline (a higher live count means a NEW violation landed; fix it, don't bake it in)."""
    new_count = min(count, existing.count) if existing.count else count
    BASELINE_PATH.write_text(
        "# Baseline for check_active_refs_archived_plans.py -- active-corpus docs must cite\n"
        "# codex, never a /plans/archive/... path directly (operator ruling 2026-08-17).\n"
        "#\n"
        "# SHRINKING ratchet. `count` is the number of pre-existing archive-plan citations\n"
        "# this gate tolerates (predates the rule -- real corpus debt, not new breakage). A\n"
        "# live count EXCEEDING this fails the check. NEVER hand-raise it -- lower it\n"
        "# (--update-baseline) the moment a citation is fixed by repointing at codex.\n"
        "#\n"
        "# SSOT: /codex/12-agent-workflow/plan-completion-and-archival-discipline.md step 5.\n"
        "note: Seeded 2026-08-17 -- corpus-wide baseline, dispatched for bulk cleanup.\n"
        f"count: {new_count}\n",
        encoding="utf-8",
    )


def target_files() -> list[Path]:
    """The active-corpus population this ratchet audits -- plans/active + plans/epics
    ONLY. codex is deliberately OUT of scope: a codex doc citing `/plans/archive/...` as
    its EVIDENCE for a historical incident is exactly the CORRECT end-state this rule
    exists to produce (durable fact migrated to codex, citing the archived plan as its
    source record) -- flagging that would punish compliance, not violations. The problem
    this ratchet targets is an ACTIVE PLAN treating an archived plan as its live reference
    instead of codex. plans/archive itself is excluded too -- an archived doc's own
    references are frozen historical record, matching check_reference_paths.py's
    identical exclusion and for the identical reason."""
    files: list[Path] = []
    active = PM_DIR / "plans" / "active"
    if active.exists():
        files.extend(active.rglob("*.md"))
    epics = PM_DIR / "plans" / "epics"
    if epics.exists():
        files.extend(epics.glob("*.md"))
    return files


def extract_related_text(text: str) -> str:
    """Same extraction as check_reference_paths.py -- the `related:` frontmatter block
    only. A prose citation of an archived doc as historical evidence ("root-caused in
    /plans/archive/issues/foo.md") is NOT what this rule targets -- that is the same
    legitimate pattern codex docs use, and flagging it would bury the real signal (a
    STRUCTURAL related: pointer routing a reader at a now-dead plan instead of codex)
    under thousands of benign citations."""
    fm_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not fm_match:
        return ""
    fm_text = fm_match.group(1)
    rel_match = re.search(r"^related:\s*(\[.*?\]|(?:\n(?:[ \t]+.*\n?)*))", fm_text, re.MULTILINE)
    return rel_match.group(1) if rel_match else ""


def violations_in_text(text: str, relpath: str) -> list[str]:
    related_text = extract_related_text(text)
    if not related_text:
        return []
    base_line = text[: text.index(related_text)].count("\n") + 1 if related_text in text else 1
    return [
        f"{relpath}:{base_line + related_text[: m.start()].count(chr(10))}: related: entry cites archived plan "
        f"{m.group(0)!r} directly -- migrate the durable fact/pointer into a codex doc and repoint here, per the "
        "archival ritual step 5"
        for m in ARCHIVE_REF_RE.finditer(related_text)
    ]


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    quiet = "--quiet" in args
    update_baseline = "--update-baseline" in args
    only_idx = args.index("--only") if "--only" in args else -1
    only_files = [Path(p) for p in args[only_idx + 1 :]] if only_idx >= 0 else None

    if only_files is not None:
        # Precommit-time mode: no baseline math, just "does YOUR OWN staged content cite
        # an archived plan." A commit that doesn't touch this class of file is a no-op.
        all_violations: list[str] = []
        for p in only_files:
            full = p if p.is_absolute() else PM_DIR / p
            if not full.is_file() or full.suffix != ".md":
                continue
            try:
                text = full.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            all_violations.extend(violations_in_text(text, p.as_posix()))
        if all_violations:
            print("Active-corpus refs to archived plans (--only):")
            for v in all_violations:
                print(f"  {v}")
            print(
                "\n❌ check_active_refs_archived_plans (--only): "
                f"{len(all_violations)} violation(s) in staged files -- "
                "repoint at a codex doc (see the archival ritual, step 5)."
            )
            return 1
        if not quiet:
            print("✅ check_active_refs_archived_plans (--only): clean.")
        return 0

    # Corpus-wide baseline mode.
    all_violations = []
    for p in target_files():
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        all_violations.extend(violations_in_text(text, p.relative_to(PM_DIR).as_posix()))
    live_count = len(all_violations)
    baseline = load_baseline()

    if update_baseline:
        write_baseline(live_count, baseline)
        print(f"active_refs_archived_plans_baseline.yaml regenerated: {live_count} known-debt citation(s).")
        return 0

    if not quiet:
        for v in all_violations:
            print(f"  {v}")
    status = "✅" if live_count <= baseline.count else "❌"
    print(
        f"{status} check_active_refs_archived_plans: {live_count} archived-plan citation(s) (baseline {baseline.count})"
    )
    return 0 if live_count <= baseline.count else 1


if __name__ == "__main__":
    raise SystemExit(main())
