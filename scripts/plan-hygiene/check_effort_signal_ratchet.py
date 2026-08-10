#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Shrinking-ratchet gate on the "silent-default effort" population — living plans
(status draft/active) that declare `assigned_role` but neither `effort:` nor
`thinking_tier:`.

Why this population specifically: per agent-orchestrator's regen_backlog_from_plan.py,
a plan with NO tier signal at all (no effort/thinking_tier/assigned_role) is fine —
it gets a deliberate todo-count-derived tier (xhigh/max, operator ruling 2026-07-22,
NEVER a silent "medium"). But a plan that sets `assigned_role` and stops there routes
through the role's OWN thinking tier (role_registry.RoleSpec.effort), which returns
None unless the role is itself max/high — and None falls through to
server/model_tier.py's `_DEFAULT_EFFORT = "medium"` at spawn time. That's a real,
silent default this checker makes visible without re-litigating whether it's WRONG
(often it's fine — plenty of role-tagged work genuinely is medium effort) — it just
stops the population of "nobody looked at this" plans from growing unnoticed.
Declaring `effort:` or `thinking_tier:` explicitly is the fix; both are now schema-known
elective fields (docspec.py PER_TYPE["plan"], PLAN_FORMAT.md), and both are now VISIBLE
downstream in agent-orchestrator's dashboard (Fleet + Backlog-detail tables) once
resolved, so a plan author has somewhere to look before deciding whether to override.

Same shrinking-ratchet shape as check_na_corpus_ratchet.py / check_line_caps.sh: hard-
fails (as a SOFT-registered hygiene-sweep check) only when the CURRENT count exceeds the
baseline — never on pre-existing debt. The goal is not "every plan must declare
effort/thinking_tier" (todo-count-derivation without a role is already a deliberate,
non-silent default; forcing an explicit tier onto genuinely role-generic work is
busywork) — the goal is that the silent-default population does not grow unattended.

Usage: check_effort_signal_ratchet.py [--quiet] [--update-baseline]
  check_effort_signal_ratchet.py --only <path> [<path> ...]
  check_effort_signal_ratchet.py --diff-base <ref> [--quiet]
  --update-baseline   regenerate effort_signal_baseline.yaml from the CURRENT corpus
                       state. Run this ONLY after actually reviewing the new plans this
                       run flagged (declare effort:/thinking_tier: on the ones that need
                       it) — never to silence a run that just found new silent-default
                       plans. A genuine raise still writes (with a loud warning), so a
                       real spike stays visible in the commit history.
Exit 0 = current count <= baseline. Exit 1 = grew beyond baseline.

``--diff-base <ref>`` (2026-08-09, plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_
velocity_2026_08_09.md): diff-scoped mode, same shape + rationale as
check_reference_paths.py's own `--diff-base` (which itself mirrors check_archive_
candidates.sh's, operator ruling 2026-08-06). The corpus-wide baseline mode attributes ANY
concurrent agent's newly-authored silent-default plan, landing anywhere in the corpus
between a worker's fix-push and the next CI re-run, to whoever happens to be re-triggering
— on a high-churn branch this makes the check un-convergeable serially. Diff-scoped mode
compares the silent-default-effort plan SET at HEAD vs the set at <ref> (e.g. origin/main)
and fails only on plans new to that set at HEAD — pre-existing corpus debt at <ref> is
tolerated exactly like baseline mode tolerates it, but the comparison point no longer races
the corpus's live tip. Falls back safely to "no violations at base" (i.e. every current
violation counts as new) if <ref> cannot be resolved locally — callers MUST verify the ref
is fetched/resolvable before passing --diff-base (see run_hygiene_sweep.sh's DIFF_BASE_REF
guard).

``--only <paths>`` (2026-08-09, precommit migration): checks ONLY the given staged files,
no baseline math — same shape as check_terminal_status_archived.py --only. This ratchet
previously had NO precommit-time presence (only the full corpus-wide baseline mode), so a
docs(plans) commit authoring a new living plan with assigned_role but no effort/
thinking_tier had zero enforcement at commit time — root-caused after the baseline grew
217->228 in under a day via commits that never ran this check. --only flags what the commit
INTRODUCES: a staged plan that is a silent-default now but was ALREADY one at HEAD is
pre-existing debt and is skipped (corrected 2026-08-09 — the original "unconditionally
flagged regardless of pre-existing population" reading contradicted this module's own
never-on-pre-existing-debt / not-busywork contract above, and blocked an 18-doc
citation-sourcing commit on 18 gaps it neither created nor could correctly decide). A brand-new
plan, or an edit that STRIPS an existing effort signal, still flags — that is the growth this
ratchet exists to stop. Declaring effort/thinking_tier explicitly, or accepting the role
default deliberately, remains the author's call.
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]
ACTIVE_DIR = PM / "plans" / "active"
BASELINE = Path(__file__).resolve().parent / "effort_signal_baseline.yaml"

_LIVING_STATUSES = frozenset({"draft", "active"})
_EXCLUDE_NAMES = frozenset({"INDEX.md", "task_template.md"})

_BASELINE_HEADER = """\
# Shrinking-ratchet baseline for the "silent-default effort" population
# (check_effort_signal_ratchet.py) — living plans (status draft/active) that declare
# assigned_role but neither effort: nor thinking_tier:, so their reasoning-effort tier
# resolves to whatever the role's generic default is (often server/model_tier.py's
# _DEFAULT_EFFORT = "medium") without anyone having deliberately chosen that for THIS
# plan's actual complexity.
#
# This is a SHRINKING ratchet, same convention as na_corpus_baseline.yaml /
# line_caps_baseline.yaml: a run that finds the CURRENT count bigger than this baseline
# fails. The goal is not "drive this to zero" — role-generic default effort is often the
# right call — the goal is that the population cannot grow unattended: review each
# newly-flagged plan and either declare effort:/thinking_tier: explicitly, or accept the
# role default deliberately (nothing to do — it just should not silently accumulate).
#
# NEVER hand-raise this number to silence a run that just found new silent-default
# plans — only --update-baseline after actually reviewing them.
"""


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    out: dict[str, str] = {}
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            value = re.sub(r"\s+#.*$", "", m.group(2))
            out[m.group(1)] = value.strip().strip("'\"")
    return out


def _is_silent_default_text(name: str, text: str) -> bool:
    """Content-level predicate, so the same rule can be applied to a working-tree file AND to
    a `git show HEAD:<path>` blob without a second implementation."""
    if name in _EXCLUDE_NAMES or name.startswith("_") or name.endswith(".HANDOVER.md"):
        return False
    fm = _frontmatter(text)
    if fm.get("doc_type") != "plan":
        return False
    if fm.get("status") not in _LIVING_STATUSES:
        return False
    if not fm.get("assigned_role"):
        return False
    return not (fm.get("effort") or fm.get("thinking_tier"))


def _is_silent_default(fp: Path) -> bool:
    """True iff this plan is a living (draft/active) plan that declares assigned_role but
    neither effort: nor thinking_tier:. Shared by the corpus-wide scan and --only so the
    two modes can never silently diverge on what counts as a violation."""
    return _is_silent_default_text(fp.name, fp.read_text(encoding="utf-8", errors="replace"))


def _was_silent_default_at_head(fp: Path) -> bool:
    """True iff this plan was ALREADY a silent-default in the committed (HEAD) version.

    A file absent from HEAD (brand-new plan) returns False — a new plan authored without an
    effort signal IS the growth this ratchet exists to stop, so it must still be flagged.
    """
    proc = subprocess.run(
        ["git", "-C", str(PM), "show", f"HEAD:{fp.resolve().relative_to(PM)}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return False
    return _is_silent_default_text(fp.name, proc.stdout)


def _silent_default_plans() -> list[str]:
    return [fp.name for fp in sorted(ACTIVE_DIR.glob("*.md")) if _is_silent_default(fp)]


def _tree_entries_active_md(ref: str) -> list[tuple[str, str]]:
    """[(basename, blob_sha), ...] for immediate *.md children of plans/active/ at `ref`
    (non-recursive — mirrors ACTIVE_DIR.glob("*.md")). One subprocess call regardless of
    corpus size (same shape as check_reference_paths.py's _tree_entries_md)."""
    result = subprocess.run(
        # Trailing slash is load-bearing: `git ls-tree <ref> -- plans/active` (no slash)
        # returns the SINGLE `tree` entry for the directory itself, not its children —
        # confirmed live (0 entries returned, silently wrong) while validating this mode.
        ["git", "-C", str(PM), "ls-tree", ref, "--", "plans/active/"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    entries: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) != 3 or parts[1] != "blob":
            continue
        if path.endswith(".md"):
            entries.append((Path(path).name, parts[2]))
    return entries


def _batch_read_blobs(shas: list[str]) -> dict[str, str]:
    """sha -> decoded text content, via ONE `git cat-file --batch` call for the whole
    list (vs. one `git show` subprocess per file — mirrors check_reference_paths.py's
    identical helper, added there after a per-file `git show` implementation measured
    60s+ per run on this corpus)."""
    if not shas:
        return {}
    proc = subprocess.run(
        ["git", "-C", str(PM), "cat-file", "--batch"],
        input=("\n".join(shas) + "\n").encode("utf-8"),
        capture_output=True,
        check=False,
    )
    out = proc.stdout
    result: dict[str, str] = {}
    pos = 0
    while pos < len(out):
        nl = out.index(b"\n", pos)
        header = out[pos:nl].decode("utf-8", "replace").split()
        if len(header) != 3:
            break
        sha, _obj_type, size_s = header
        size = int(size_s)
        start = nl + 1
        result[sha] = out[start : start + size].decode("utf-8", "replace")
        pos = start + size + 1  # +1 skips the trailing newline after object data
    return result


def _silent_default_plans_at(ref: str) -> set[str]:
    """The full silent-default-effort plan-basename SET at `ref` — batched git reads,
    same shape as check_reference_paths.py's _violations_at."""
    entries = _tree_entries_active_md(ref)
    blobs = _batch_read_blobs([sha for _, sha in entries])
    out: set[str] = set()
    for basename, sha in entries:
        text = blobs.get(sha)
        if text is None:
            continue
        if _is_silent_default_text(basename, text):
            out.add(basename)
    return out


def _run_diff_base(base_ref: str, quiet: bool) -> int:
    """Diff-scoped mode: fail only on plans that are silent-default at HEAD but were NOT
    silent-default at `base_ref` — see the module docstring's --diff-base section for the
    race this closes."""
    head_set = set(_silent_default_plans())
    base_set = _silent_default_plans_at(base_ref)
    new_ones = sorted(head_set - base_set)

    if not quiet:
        for name in new_ones:
            print(f"  SILENT-DEFAULT-EFFORT  {name}")

    n = len(new_ones)
    print(
        f"{'✅' if n == 0 else '❌'} check_effort_signal_ratchet (--diff-base {base_ref}): "
        f"{n} NEW violation(s) vs {base_ref}"
    )
    return 0 if n == 0 else 1


def _run_only(paths: list[str], quiet: bool) -> int:
    """Precommit-scoped mode: check exactly the given staged files, no baseline math.

    Flags only what THIS COMMIT INTRODUCES — a plan that was already a silent-default at HEAD is
    pre-existing debt and is skipped (2026-08-09). Without that, editing one prose line of any
    legacy plan demanded an `effort:` declaration for a plan you may not own, which contradicts
    this module's own contract twice over: "hard-fails ... never on pre-existing debt", and "the
    goal is not 'every plan must declare effort/thinking_tier' ... forcing an explicit tier onto
    genuinely role-generic work is busywork". Measured: an 18-doc citation-sourcing commit was
    blocked on 18 pre-existing gaps it did not create and could not correctly decide. The growth
    signal the ratchet actually wants — a NEW plan, or an edit that REMOVES an existing effort
    signal — is still caught, because a file absent from HEAD (or clean at HEAD) still flags.
    """
    flagged: list[str] = []
    for raw in paths:
        p = Path(raw)
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.is_file():
            continue
        if _is_silent_default(p) and not _was_silent_default_at_head(p):
            flagged.append(str(p))

    if not quiet:
        for name in flagged:
            print(f"  SILENT-DEFAULT-EFFORT  {name}")

    n = len(flagged)
    print(f"{'✅' if n == 0 else '❌'} check_effort_signal_ratchet (--only): {n} violation(s) in staged files")
    return 0 if n == 0 else 1


def _load_baseline() -> dict[str, object]:
    if not BASELINE.is_file():
        return {}
    return yaml.safe_load(BASELINE.read_text()) or {}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    update_baseline = "--update-baseline" in args
    quiet = "--quiet" in args

    if "--only" in args:
        idx = args.index("--only")
        return _run_only(args[idx + 1 :], quiet)

    if "--diff-base" in args:
        idx = args.index("--diff-base")
        return _run_diff_base(args[idx + 1], quiet)

    flagged = _silent_default_plans()
    count = len(flagged)
    baseline = _load_baseline()
    max_count = baseline.get("max_silent_default_plans")

    if update_baseline:
        warning = ""
        if isinstance(max_count, int) and count > max_count:
            warning = f"max_silent_default_plans RAISED {max_count} -> {count}"
        BASELINE.write_text(
            _BASELINE_HEADER
            + f"max_silent_default_plans: {count}\n"
            + f'last_updated: "{datetime.now(UTC).date().isoformat()}"\n'
        )
        print(f"effort_signal_baseline.yaml regenerated: max_silent_default_plans={count}")
        if warning:
            print(f"⚠️  {warning} — verify this is a reviewed set, not a silenced failure", file=sys.stderr)
        return 0

    if isinstance(max_count, int) and count > max_count:
        new_ones = flagged[-(count - max_count) :] if count > max_count else []
        print(
            f"❌ check_effort_signal_ratchet: silent-default-effort plan count grew: {count} > baseline {max_count}",
            file=sys.stderr,
        )
        print("  Sample of currently-flagged plans (assigned_role set, no effort:/thinking_tier:):", file=sys.stderr)
        for name in (new_ones or flagged)[:10]:
            print(f"    - {name}", file=sys.stderr)
        print(
            "  Remedy: review the newly-flagged plan(s) and either declare effort: / thinking_tier:\n"
            "  explicitly, or confirm the role's default effort is genuinely right for this plan's\n"
            "  complexity, then re-run with --update-baseline. Never hand-edit the YAML.",
            file=sys.stderr,
        )
        return 1

    if not quiet:
        print(f"✅ check_effort_signal_ratchet: {count} silent-default-effort plans (baseline: {max_count})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
