---
title:
  Frontmatter SCHEMA gate bypassed by docs-only commits → non-compliant plan/issue docs land on LDR and block fleet-wide
  full QG
status: active
priority: P2
locked_by: live-defi-rollout
created: 2026-06-16
source:
  - slot-3 setup-tab-worktrees ship 2026-06-16 — full QG blocked twice by a foreign issue doc missing status/priority
  - plans/active/issues/deployment_ui_test_env_esm_breakage_2026_06_16.md (the doc that demonstrated the bypass)
---

# Frontmatter schema gate bypassed by docs-only commits

> **✅ Primary fix SHIPPED in this change** (see "Fix" below). This doc stays open only for the **residual follow-up**
> (audit the same swallow pattern in the other local prek hooks). Archive once that is decided.

## What I found

`scripts/plan-hygiene/check_frontmatter_schema.py` enforces required-NON-EMPTY frontmatter fields
(`status`/`priority`/`locked_by`/… per doc type) and is run by the full `quality-gates.sh`. But it was **NOT** enforced
at commit time, for two compounding reasons:

1. **The prek hook ran the WEAK check.** `run_hygiene_sweep.sh --precommit` (the `plan-hygiene` prek hook) validated
   staged plans with `check_frontmatter.sh` (presence-only — "first line is `---`" + deprecated-field), **not** the
   value-level `check_frontmatter_schema.py`. A doc with `---` but missing `status`/`priority` passed prek.
2. **The hook entry swallowed failures.** The hook entry was `[ -f "$SWEEP" ] && bash "$SWEEP" --precommit || exit 0`.
   In `A && B || C`, `C` runs when **B fails** — so even a real sweep failure exited 0. The hook could never block.

Because `docs(plans):` commits take the prek hook only (NOT full QG — a deliberate docs/markdown carve-out), a
plan/issue doc with missing required frontmatter **commits cleanly, reaches `live-defi-rollout`, and then blocks EVERY
subsequent full `quality-gates.sh` run, fleet-wide**, for any agent — until someone backfills the missing field. This
happened twice in one session with `deployment_ui_test_env_esm_breakage_2026_06_16.md` (missing `status`, then
`priority`).

## Why it matters

A single non-compliant doc on the integration branch is a **fleet-wide soft-DoS on the local commit gate**: every
agent's `quality-gates.sh` (the local commit prerequisite) fails until the foreign doc is fixed, even though the agent's
own change is clean. The schema check existed but enforced nothing at the point the bad doc was created.

## Fix (shipped this change)

- `run_hygiene_sweep.sh --precommit` now ALSO runs `check_frontmatter_schema.py --quiet` on the staged plans (the
  value-level gate), alongside the existing presence-only check.
- The `plan-hygiene` hook entry is restructured to `[ -f "$SWEEP" ] || exit 0; bash "$SWEEP" --precommit` — tolerates a
  missing script (original intent) but **propagates a real failure** (no more swallow).
- Fixed in BOTH PM's live `.pre-commit-config.yaml` and the SSOT template
  `scripts/pre-commit-templates/docs.pre-commit-config.yaml` (the two were already drifted on the plan-hygiene block;
  re-synced so a future rollout won't regress).
- Verified end-to-end: a staged issue doc missing `priority` now fails the sweep (`exit 1`) → commit blocked.

## Recommended decision / follow-up

- **P2 — audit the other local prek hooks for the same `&& … || exit 0` swallow**: `fix-commit-identity`,
  `check-branch-drift`, and `prettier-autostage` use the identical pattern. Decide per-hook whether it should be
  fail-closed (block on real failure) or stay fail-open (advisory). `check-branch-drift` in particular is commented
  "behind-origin → STOP" but currently cannot block. Do this as a deliberate, separately-reviewed pass — not blindly.
- **P2 — the prek hook validates frontmatter but NOT todo-FORMAT, so `check_todo_format` violations slip onto LDR the
  same way (surfaced 2026-06-16).** `run_hygiene_sweep.sh --precommit` runs `check_frontmatter_schema.py` (the fix
  above) but still does NOT run `check_todo_format` / `check_todo_regression` — those live only in the _advisory_
  `plan-health-agent.yml` gate (red + dispatches the escalate fixer, never blocks merge). So a `docs(plans):` edit that
  adds a `- [ ]` without `[TAG] P<n>.` commits cleanly, reaches LDR, then fails the advisory sweep on EVERY subsequent
  LDR PR → dispatches escalate-to-orchestrator each time (the 2026-06-16 escalate storm; 3 such todos in 2 plans were
  the live cause, fixed PM@e8cb2bbd8). Decide whether `--precommit` should ALSO run `check_todo_format` fail-closed on
  staged plans (same fail-closed-vs-advisory call as the hooks above). </content> </invoke>
