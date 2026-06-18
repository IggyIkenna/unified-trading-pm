---
title:
  Frontmatter SCHEMA gate bypassed by docs-only commits → non-compliant plan/issue docs land on LDR and block fleet-wide
  full QG
status: resolved
resolved: 2026-06-18
priority: P2
created: 2026-06-16
source:
  - slot-3 setup-tab-worktrees ship 2026-06-16 — full QG blocked twice by a foreign issue doc missing status/priority
  - plans/active/issues/deployment_ui_test_env_esm_breakage_2026_06_16.md (the doc that demonstrated the bypass)
---

# Frontmatter schema gate bypassed by docs-only commits

> **✅ RESOLVED + ARCHIVED 2026-06-18** — primary fix (frontmatter-schema gate enforced at commit) + both follow-ups
> done: all 3 prek hooks made fail-closed (PM@81d74c9a7 + rolled out to all 24 other repos), and `check_todo_format` was
> already fail-closed in `--precommit`. Details in "Recommended decision / follow-up" below.

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

Both follow-ups are now **RESOLVED** (2026-06-18):

- **P2.a — audit the other 3 local prek hooks for the `&& … || exit 0` swallow: ✅ DONE → all three made fail-closed.**
  `fix-commit-identity`, `check-branch-drift`, and `prettier-autostage` all wrapped their script as
  `[ -f "$HOOK" ] && bash "$HOOK" … || exit 0`, where the `|| exit 0` runs when the script FAILS — so a real failure was
  swallowed to exit 0. The audit confirmed each script is robustly fail-OPEN on environment errors (CI / no-network /
  missing tool / detached HEAD) and exits non-zero ONLY on its genuine block condition, and each carries a documented
  fail-closed intent the swallow defeated (identity header says "FAIL-CLOSED"; drift says "behind-origin → STOP";
  prettier says "parse error → commit aborts"). **Operator decision (Harsh, 2026-06-18): fix all three.** Rationale for
  `check-branch-drift` specifically (an initial draft proposed leaving it advisory): the `*/5` slot-cron-ff-pull +
  dirty-work Slack alert cover the common case, so the gate is the **backstop** for when they don't — catching drift at
  COMMIT time forces a local reconcile so conflicts never surface on staging. **Design evidence backs this**:
  `prettier-autostage` already self-skips when behind origin _because_ `check-branch-drift` was built to abort the
  commit (its own comment), so the swallow had silently broken an existing contract. Restructured to
  `[ -f "$HOOK" ] || exit 0; bash "$HOOK"` (tolerate a missing script, propagate a real failure). Shipped to PM's live
  config + all 4 templates (PM@81d74c9a7, dogfooded) and **rolled out + committed to all 24 other repos**
  (`ci(prek): make 3 hooks fail-closed`). `fail_fast: true` on identity + drift preserved.
- **P2.b — `--precommit` should also run `check_todo_format` fail-closed: ✅ ALREADY SHIPPED.** `run_hygiene_sweep.sh`
  `--precommit` already runs `check_todo_format.sh --quiet` on staged plans (line 45), increments the hard-failure
  counter, and `PF > 0 → exit 1` (lines 50–52) — fail-closed, with the (already-fixed) plan-hygiene wrapper propagating
  it. So a malformed `- [ ]` is now blocked at commit time, closing the escalate-storm path. No change required.
