---
doc_type: codex-ssot
title: Issue-Doc Lifecycle Discipline
summary:
  The closed 5-state machine for `plans/active/issues/` docs (UNACKED → ACKED-INTO-PLAN/-CODE/-OUT-OF-SCOPE/-AS-INVALID)
  — archive triggers, anti-patterns (no "stays until parent closes"), and the grep-based audit recipe for dual-tracking
  violations; referenced from CLAUDE.md Citadel standard item 9.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [issue-lifecycle, plan-hygiene, archival, audit]
related:
  [
    /codex/11-project-management/foundation-completion-gate-discipline.md,
    /codex/11-project-management/citadel-grade-planning-standards.md,
  ]
created: 2026-05-20
authoritative_for: [issue-doc lifecycle state machine, issue-doc archive triggers]
referenced_by:
  [
    /codex/11-project-management/audit-lifecycle.md,
    /codex/11-project-management/citadel-grade-planning-standards.md,
    /codex/11-project-management/epic-execution-with-sub-agents.md,
    /codex/11-project-management/foundation-completion-gate-discipline.md,
  ]
owner:
last_reviewed: 2026-07-25
code_refs: [scripts/plan-hygiene/check_terminal_status_archived.py]
---

# Issue-Doc Lifecycle Discipline

> **SSOT** for when issue docs in `plans/active/issues/` archive. Referenced from CLAUDE.md § "Citadel-Grade Planning
> Standards" item 9.

## The rule

**Issue docs exist to surface UNACKED work. Once acked — into a plan, into shipped code, or out-of-scope with a named
successor — they archive immediately. Banner-marked-in-`active/issues/` is a transitional convenience that should be
temporary, NOT a permanent state.**

`plans/active/issues/` should contain only items the workspace has not yet decided what to do about. Everything else
lives elsewhere.

## State machine (closed set)

| State                | Definition                                                                          | Location                                             |
| -------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `UNACKED`            | Surfaced, no operator/agent has decided how to address it yet                       | `plans/active/issues/`                               |
| `ACKED-INTO-PLAN`    | A named active plan absorbs the work (issue's findings are now in the plan's todos) | **`plans/archive/issues/`** (banner cites plan)      |
| `ACKED-INTO-CODE`    | The fix is shipped (commit SHA citable)                                             | **`plans/archive/issues/`** (banner cites SHA)       |
| `ACKED-OUT-OF-SCOPE` | Decision: not worth doing now; explicit successor named with date                   | **`plans/archive/issues/`** (banner cites successor) |
| `ACKED-AS-INVALID`   | False positive / not a real issue / superseded by better understanding              | **`plans/archive/issues/`** (banner cites why)       |

There are NO other states. Specifically:

- **NO** "ACKED-but-still-in-`active/issues/`-with-banner" state.
- **NO** "covered by plan, stays until parent closes" state.

If a banner says "stays in `active/issues/` until parent closes", the banner is wrong. The clean answer is: archive now;
the parent plan tracks the work; the banner becomes a one-line breadcrumb in the parent plan if needed for discovery.

## When to archive (specific triggers)

Archive an issue doc the moment ANY of these become true:

1. **A named successor plan exists in `plans/active/`** that absorbs the issue's findings. The issue is acked-into-plan;
   archive immediately.
2. **A commit SHA fixes the issue.** Add `resolved: <date>` frontmatter + resolution-citing-SHA banner; archive
   immediately.
3. **The work is subsumed by a meta-audit / cross-cutting plan** (mega-audit Phase A/B/C/D, codex SSOT, etc.).
   Acked-into-plan; archive.
4. **A clear out-of-scope decision lands** with a named successor (per CLAUDE.md "External Data Is Always Available" /
   "Temporary states must have a named successor"). Acked-out-of-scope; archive.
5. **The issue is determined invalid** (false positive, wrong root cause, superseded). Acked-as-invalid; archive with
   rationale.

## Anti-patterns (review-blocking)

- ❌ **Banner-marked + still in `active/issues/`** — dual-tracking. The banner says "see the parent"; the issue file
  itself is now redundant. Archive.
- ❌ **Pre-audit / diagnostic artefacts in `active/issues/`** — these are audit outputs, not unacked issues. They belong
  in `plans/audit/` (for forward-looking audits that downstream plans reference) or `plans/archive/issues/` (for closed
  one-shot triage).
- ❌ **Meta-audit / triage docs surviving past their action**: once acted on, archive. They served their one-shot
  purpose.
- ❌ **"Archived alongside parent" lifecycle policies** in issue frontmatter — these explicitly create dual-tracking.
  Archive the issue when ack-ed, not when parent closes.

## How to ack without losing the diagnostic data

When archiving an `ACKED-INTO-PLAN` issue, the parent plan typically **already references** the issue (it was the input
that drove the plan's phases). No code change needed; just archive the issue.

If the parent plan does NOT reference the issue, add ONE line to the parent:

```markdown
## Related diagnostic

- Pre-audit / issue trail: `plans/archive/issues/<issue-name>.md` (archived <date>)
```

Then archive. The `git log` history preserves the issue forever; the parent plan has a one-line discovery breadcrumb.

## Composition with other rules

- **Capture Discoveries As Plan Todos** (CLAUDE.md): the discovery still files as an issue todo at the moment it
  surfaces. This rule just says: once the todo lives in a plan, the issue archives.
- **Foundation-Completion-Gate Discipline** ([[foundation-completion-gate-discipline]]):
  banner-marked-in-`active/issues/` for layer-N work that's covered by a layer-N plan is still dual-tracking. Archive
  once acked into the plan.
- **Plans Run To Actual Completion** (CLAUDE.md): "shipped" for the issue's purposes is "the plan that absorbed it now
  owns the work". The issue doesn't wait for plan-shipped to archive.
- **Plan archival hard rule** (CLAUDE.md): when an archived issue's parent plan ALSO archives, no special action needed
  — the issue is already in archive.

## Reference incident

2026-05-20 cleanup pass: `plans/active/issues/` contained 14+ banner-marked items (9 mega-audit subsumed + 5
existing-plan covered) carrying explicit "stays until parent closes" lifecycle. Operator flagged the dual-tracking; this
SSOT codifies the cleaner pattern. Pattern observed across `ml_repo_consolidation_preaudit_2026_05_19.md`,
`strategy_repo_consolidation_preaudit_2026_05_19.md`, and the 14 banner-marked items.

## Audit recipe

**⚠️ Corrected 2026-07-25** — the previous version of this recipe checked for a `^resolved:` frontmatter key. That key
never existed in the live schema; the real terminal-status field is `status:` (values `resolved`/`false-positive`/
`superseded` per `docspec.py`'s `STATUS_BY_TYPE["issue"]`), with `resolved_by:` as the conditionally-required evidence
field. The stale recipe silently caught **zero** of the ~42 real violations found on re-audit — this is exactly why the
dual-tracking anti-pattern accumulated undetected for months. The corrected recipe:

```bash
# Files with COVERED BY / SUBSUMED BY banners (and similar acks)
grep -lE "(🟡|🟢) (COVERED BY|SUBSUMED BY MEGA AUDIT|RESOLVED|RE-RESOLVED|LAUNCHED)" \
  plans/active/issues/*.md

# Files with a terminal status still in active/issues/ (the real check)
for f in plans/active/issues/*.md; do
  st=$(grep -m1 "^status:" "$f" | sed 's/^status: *//')
  case "$st" in
    resolved|false-positive|superseded) echo "DUAL-TRACK: $f" ;;
  esac
done
```

Any output from these greps is review-blocking — archive the listed files. **This is now also machine-enforced** (not
just a manual recipe) by `scripts/plan-hygiene/check_terminal_status_archived.py`, wired into `run_hygiene_sweep.sh` — a
shrinking-ratchet gate covering pre-existing debt while blocking any NEW terminal-status doc from landing unarchived
(issue-side AND the plan-side parallel — see that script's docstring).
