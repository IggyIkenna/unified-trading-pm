#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA — re-run whenever /ag-closeout-audit parked reports reach 0 open todos
"""Archive every ag-closeout parked report that has reached 0 open todos (15 as of 2026-08-10).

MUST RUN AFTER the dedupe commit has landed, never in the same commit as it:
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` forbids combining a
checkbox flip with the `git mv` archival (2026-07-30 incident). Six of these carry a
dedupe flip, so this is sequenced as its own step.

Does the 6-step ritual, mechanised:
  1. deferred items -> already migrated (batch1 owns them; operator residue consolidated separately)
  2. status: resolved + superseded_by + last_updated, then `git mv` into plans/archive/2026_08/issues/
  5. repoint every PATH-form referrer corpus-wide (bare slugs in superseded_by/depends_on stay bare,
     per /codex/11-project-management/cross-reference-path-convention.md)
  6. confirm the move; a locked doc is refused, not force-archived

Idempotent: a doc already under plans/archive/ is skipped. Exits non-zero if any doc still
has an open todo, so a regressed corpus cannot be silently archived.

TRAPS HIT BUILDING THIS (2026-08-10) — do not re-learn them:

1. **Run it AFTER the checkbox-flip commit has landed, never in the same commit.**
   /codex/12-agent-workflow/plan-completion-and-archival-discipline.md forbids combining a flip with the `git mv`.

2. **The referrer repoint must be scoped to docs that ACTUALLY moved** (`moved | skipped`), not to every slug in the
   successor table. Repointing a slug still living in plans/active/ manufactures the exact dangling refs step 5 exists
   to prevent. This was a live bug in the first version.

3. **Derive the target set at runtime, never hardcode it.** The eligible set grows as other plans clear todos; a frozen
   list goes stale the moment a batch lands.

5. **Promoting a scratchpad script is its first real quality gate — expect it to fail.** Scratchpad files are never
   linted; `scripts/` is. This file failed ruff E501 + `ruff format` the moment it moved, having run fine for hours.
   Promote tools EARLY, not at checkpoint time, so the gate fires while you still have context to fix it cheaply.

6. **Measure line length with ruff, not `awk 'length>120'`.** `awk` counts BYTES, ruff counts CHARACTERS, and every
   em-dash here is 3 bytes — so `awk` reports phantom over-long lines that ruff is perfectly happy with. Chasing one
   cost a wasted edit cycle. `ruff check <file>` is the only authority.

4. **`safe-doc-push` isolated mode used to DROP the deletions** this script creates, producing create-only archive
   commits with a live duplicate left at the old path (measured on 8ac88720e6: 17 A, zero D). Fixed
   2026-08-10 in unified-trading-pm@18ae9a4312. If you are on an older checkout, ship with `SDP_ISOLATED=0` and ALWAYS
   verify with `git show --name-status <sha>` that a `D`/`R` exists for every plans/active path — an exit code proves
   nothing. Issue: /plans/active/issues/safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md
"""

import pathlib
import re
import subprocess
import sys

PM = pathlib.Path(__file__).resolve().parents[2]  # <repo>/scripts/plan-hygiene/<this> -> <repo>
ACTIVE = PM / "plans/active/issues"
ARCHIVE = PM / "plans/archive/2026_08/issues"

# Successor lookup: slug -> next dated doc in the same tranche chain, or None if newest.
# The ACTUAL target set is derived at runtime (any parked doc with 0 open todos and no lock),
# so this grows correctly as batch1's todo 17 clears more docs — a hardcoded list would go
# stale the moment that lands.
SUCCESSORS = {
    "ag_closeout_audit_cefi_parked_2026_08_10": None,
    "ag_closeout_audit_ci_parked_2026_08_10": None,
    "ag_closeout_audit_cross_cutting_parked_2026_08_01": "ag_closeout_audit_cross_cutting_parked_2026_08_02",
    "ag_closeout_audit_cross_cutting_parked_2026_08_06": "ag_closeout_audit_cross_cutting_parked_2026_08_07",
    "ag_closeout_audit_cross_cutting_parked_2026_08_07": "ag_closeout_audit_cross_cutting_parked_2026_08_08",
    "ag_closeout_audit_cross_cutting_parked_2026_08_08": "ag_closeout_audit_cross_cutting_parked_2026_08_10",
    "ag_closeout_audit_cross_cutting_parked_2026_08_10": None,
    "ag_closeout_audit_ao_parked_2026_08_10": None,
    "ag_closeout_audit_defi_parked_2026_08_06": "ag_closeout_audit_defi_parked_2026_08_07",
    "ag_closeout_audit_defi_parked_2026_08_07": "ag_closeout_audit_defi_parked_2026_08_08",
    "ag_closeout_audit_infra_parked_2026_08_03": "ag_closeout_audit_infra_parked_2026_08_04",
    "ag_closeout_audit_tradfi_parked_2026_08_10": None,
    "ag_closeout_audit_ui_parked_2026_08_08": "ag_closeout_audit_ui_parked_2026_08_09",
    "ag_closeout_audit_ui_parked_2026_08_09": "ag_closeout_audit_ui_parked_2026_08_10",
    "ag_closeout_audit_defi_parked_2026_08_08": "ag_closeout_audit_defi_parked_2026_08_10",
    "ag_closeout_audit_defi_parked_2026_08_10": None,
    "ag_closeout_audit_infra_parked_2026_08_01": "ag_closeout_audit_infra_parked_2026_08_02",
    "ag_closeout_audit_infra_parked_2026_08_04": "ag_closeout_audit_infra_parked_2026_08_06",
    "ag_closeout_audit_infra_parked_2026_08_06": "ag_closeout_audit_infra_parked_2026_08_07",
    "ag_closeout_audit_infra_parked_2026_08_07": "ag_closeout_audit_infra_parked_2026_08_08",
    "ag_closeout_audit_infra_parked_2026_08_08": "ag_closeout_audit_infra_parked_2026_08_09",
    "ag_closeout_audit_infra_parked_2026_08_09": "ag_closeout_audit_infra_parked_2026_08_10",
    "ag_closeout_audit_infra_parked_2026_08_10": None,
    "ag_closeout_audit_prediction_parked_2026_07_31": "ag_closeout_audit_prediction_parked_2026_08_04",
    "ag_closeout_audit_prediction_parked_2026_08_09": "ag_closeout_audit_prediction_parked_2026_08_10",
    "ag_closeout_audit_sports_parked_2026_08_09": None,
    "ag_closeout_audit_ui_parked_2026_08_07": "ag_closeout_audit_ui_parked_2026_08_08",
    "ag_closeout_audit_ui_parked_2026_08_10": None,
}

BANNER = (
    "> **📦 ARCHIVED 2026-08-10 — this audit report is complete.** Every finding it raised has been\n"
    "> dispositioned: the\n"
    "> bounded, worker-determinable items were extracted into\n"
    "> `/plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md`, cross-day duplicates were collapsed\n"
    "> into their origin doc, and informational findings were converted to prose (all per\n"
    '> `cursor-configs/skills/ag-closeout-audit/SKILL.md` § "Three things that must NOT reach a parked doc",\n'
    "> `unified-trading-pm@bd812c57ad`). Zero open todos remained at archival. Archived as COMPLETE, not superseded —\n"
    "> `superseded_by` below points to the next dated report in this tranche's chain for navigation only; it does not\n"
    "> mean this report's content was replaced.\n\n"
)


def _dup_verdict(same: bool) -> str:
    """Identical duplicates are safe to drop; diverged ones need a human read-and-merge."""
    if same:
        return "identical — safe to delete the active copy"
    return "DIVERGED — reconcile by hand, do not delete"


def run(*args: str) -> str:
    return subprocess.run(args, cwd=PM, capture_output=True, text=True, check=True).stdout


def eligible() -> list[str]:
    """Every parked doc in plans/active/issues/ with zero open todos and no lock."""
    out = []
    for p in sorted(ACTIVE.glob("ag_closeout_audit_*_parked_*.md")):
        t = p.read_text()
        if re.search(r"^- \[ \]", t, flags=re.M):
            continue
        if re.search(r"^locked_by: \S", t, flags=re.M):
            continue
        out.append(p.stem)
    return out


def main() -> int:
    moved, skipped, errs = [], [], []
    targets = eligible()
    print(f"eligible (0 open, unlocked): {len(targets)}")

    for slug in targets:
        successor = SUCCESSORS.get(slug)
        src = ACTIVE / f"{slug}.md"
        dst = ARCHIVE / f"{slug}.md"
        if dst.exists() and not src.exists():
            skipped.append(slug)
            continue
        if not src.exists():
            errs.append(f"{slug}: not found in plans/active/issues/")
            continue
        if dst.exists() and src.exists():
            # A live duplicate pair — the create-only-archive failure mode
            # (safe_doc_push_isolation_drops_rename_deletions_2026_08_10). NEVER clobber:
            # the two copies may have diverged, and the archived one is not automatically
            # authoritative. Report for manual reconciliation and leave both untouched.
            same = src.read_bytes() == dst.read_bytes()
            errs.append(f"{slug}: DUPLICATE at both paths ({_dup_verdict(same)})")
            continue

        txt = src.read_text()

        txt = re.sub(r"^status: .*$", "status: resolved", txt, count=1, flags=re.M)
        txt = re.sub(r"^last_updated: .*$", 'last_updated: "2026-08-10"', txt, count=1, flags=re.M)
        if successor:
            txt = re.sub(r"^superseded_by:.*$", f"superseded_by: {successor}", txt, count=1, flags=re.M)
        # banner immediately after the closing frontmatter delimiter
        if "📦 ARCHIVED 2026-08-10" not in txt:
            head, _, body = txt.partition("---\n")[2].partition("---\n")
            txt = "---\n" + head + "---\n\n" + BANNER + body.lstrip("\n")

        src.write_text(txt)
        run("git", "mv", str(src.relative_to(PM)), str(dst.relative_to(PM)))
        moved.append(slug)

    # --- step 5: repoint every PATH-form referrer corpus-wide ---
    # ONLY for docs that actually now live under plans/archive/ — repointing a slug that is
    # still in plans/active/ would manufacture the dangling refs this step exists to prevent.
    relocated = set(moved) | set(skipped)
    repointed = 0
    for root in ("plans", "codex", "cursor-configs", "scripts", "audits"):
        base = PM / root
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix not in {".md", ".py", ".sh", ".yaml", ".yml"}:
                continue
            if ".venv" in p.parts:
                continue
            try:
                t = p.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            orig = t
            for slug in relocated:
                if p.name == f"{slug}.md":
                    continue
                t = t.replace(
                    f"plans/active/issues/{slug}.md",
                    f"plans/archive/2026_08/issues/{slug}.md",
                )
            if t != orig:
                p.write_text(t)
                repointed += 1

    print(f"archived={len(moved)} already-archived={len(skipped)} referrer-files-repointed={repointed}")
    for e in errs:
        print(f"  ERROR {e}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
