---
doc_type: issue
title: >-
  CI-wall escalation watchdog: single-shot re-escalation cap, page-on-first-miss, and no path back from
  `unresolved`/`still_red_past_deadline` to `resolved` — retuned + a new passive reconcile pass added
summary: >-
  Operator was reading the AO dashboard's escalations widget and found two `unified-trading-pm` rows (`main_ci_red`,
  `ldr_qg_failure`) both sitting `unresolved — still_red_past_deadline` for 15-17h. Live `gh run list` showed `main`'s
  quality-gates-v2 had actually gone green ~11h AFTER the row went terminal — the escalation just never found out.
  Traced to a structural gap, not a bug: `verify_dispatched_escalations` (server/escalation.py) only ever re-polls rows
  with `status=="dispatched"`; once `_mark_unresolved_and_maybe_reescalate` flips a row to terminal `unresolved`
  (re-escalation cap hit), nothing ever looks at it again — a wall fixed by a human, a different agent, or an unrelated
  later push/promotion stays a permanent "still_red_past_deadline" ghost in the dashboard forever, and the dashboard's
  own `active_within_hours=24` window (dashboard/src/api.ts) only hides it from view once it ages out, it never gets
  corrected. Separately, `MAX_REESCALATIONS=1` (2 total dispatch attempts) + paging on the very FIRST 90-minute deadline
  miss meant a wall that would clear on its 3rd try got both an unnecessary page AND gave up too early. Operator ruling
  (2026-08-07): the LDR→main promote flow is ~25min end-to-end and a cicd worker should clear most walls in ~15min, so
  retune the per-attempt deadline down (90→45min) while raising the retry budget way up (1→10 re-escalations) — try
  harder before giving up, but don't page on every miss; delay the first page to the 2nd failed retry (~135min, close to
  the old single-shot bar) instead of the 1st (~90min); and add a new passive (no new dispatch, same read-only `gh`-CLI
  probe as the live watchdog) reconcile pass that keeps checking a TERMINAL `unresolved` row for 24h after it gave up
  and flips it back to `resolved` (tagged `_reconciled`) if the wall cleared some other way. Also revisits
  `/plans/active/issues/ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md`'s "CI-wall re-escalation cap
  (defensible judgment bar) — no action" finding from the day before: that judgment was made without the live evidence
  this session surfaced (rows that visibly never self-correct), so it is superseded here rather than left standing as a
  contradicting "no action needed" claim.
status: resolved
resolved_by: interactive session, 2026-08-07 — agent-orchestrator@d9e59db6
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao, escalation, watchdog, ci-cd, tuning, reconcile, still-red-past-deadline, big-finding]
related:
  [
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/issues/ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md,
    /plans/archive/issues/escalation_watchdog_stale_merged_pr_false_unresolved_2026_08_06.md,
  ]
created: 2026-08-07
author: interactive session (operator noticed via the AO dashboard's escalations widget)
last_updated: 2026-08-07
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: devops_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    "operator reading the AO dashboard escalations widget, 2026-08-07 — two unified-trading-pm rows (main_ci_red,
    ldr_qg_failure) both 'unresolved — still_red_past_deadline' 15-17h after creation, cross-checked against live `gh
    run list` which showed main had already gone green",
  ]
context_scope:
  [
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/tests/test_escalation.py,
    agent-orchestrator/dashboard/src/api.ts,
    agent-orchestrator/scripts/ao-self-pull.sh,
  ]
---

# Escalation watchdog retune: try harder before giving up, page later, and stop leaving `unresolved` rows stuck forever

## What I found

Walked the operator through the two live escalations first (`main_ci_red` / `ldr_qg_failure` on `unified-trading-pm`),
then verified against live GitHub state (`gh run list --branch main|live-defi-rollout --workflow quality-gates-v2.yml`):
`main`'s latest run had succeeded ~11h after the escalation row already gave up. The operator's question — "if so, why
not raise MAX_REESCALATIONS and reconcile the historical `still_red_past_deadline` rows?" — is exactly right, because
the mechanism to check is already fully scripted and agent-free (`_poll_wall_resolution`, a read-only `gh` probe); it
just was never invoked again after a row went terminal.

Three separate, compounding issues in `server/escalation.py`:

1. **No path back from `unresolved` to `resolved`.** `verify_dispatched_escalations` queries only
   `EscalationQueueRow.status == "dispatched"`. `_mark_unresolved_and_maybe_reescalate`'s terminal branch sets
   `status="unresolved"` and nothing ever re-queries it. The dashboard's `list_active_escalations` (called with
   `active_within_hours=24`) treats `unresolved` as still "active," so the row sits visible — and permanently wrong —
   until it simply ages out of the 24h window, never because it was actually corrected.
2. **`MAX_REESCALATIONS=1`** gave a wall only 2 total dispatch attempts (original + 1 retry) at a 90-minute deadline
   each before permanently giving up (~3h). Given the operator's own estimate — LDR→main promote is ~25min, a cicd
   worker should clear most walls in ~15min — 90min per attempt was generous but the retry BUDGET was thin.
3. **Paging fired on the very first deadline miss** (`_mark_unresolved_and_maybe_reescalate` unconditionally tried
   `notify_escalation_unresolved` on every `will_reescalate` path, gated only by a 3h cooldown, not by how many attempts
   had actually failed) — so a wall that would clear on retry #2 or #3 still generated a CRITICAL page on attempt #1.

This also revisits `/plans/active/issues/ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md`, filed one day
earlier, which classified "CI-wall re-escalation cap" as **"defensible judgment bar — no action."** That audit did not
have the live dashboard evidence this session did (two rows that visibly never self-corrected); superseded in that doc
via a strikethrough + pointer here so a future reader doesn't take the earlier "no action" line as still current.

## Fix

`agent-orchestrator/server/escalation.py`:

- `RESOLUTION_DEADLINE_MINUTES`: 90 → **45** (per-attempt deadline; CI promote ~25min + agent fix ~15min + buffer).
- `MAX_REESCALATIONS`: 1 → **10** (try harder before giving up; still bounded to ~8h worst case, well inside
  `WATCH_TTL_HOURS`/the new reconcile window).
- New `PAGE_AFTER_REESCALATIONS = 2`: `_mark_unresolved_and_maybe_reescalate` now only pages once this many
  re-escalations have ALREADY failed (or unconditionally on the final cap-hit give-up) — the first 2 misses re-escalate
  silently.
- New `RECONCILE_UNRESOLVED_WINDOW_HOURS = 24` + new function `reconcile_stale_unresolved_escalations()`: a passive (no
  new dispatch) sweep of terminal `unresolved` rows within 24h of giving up, using the SAME `_poll_wall_resolution`
  probe. A cleared wall flips to `resolved` via a broadened `_mark_resolved(..., from_status="unresolved")`, tagged
  `<resolution>_reconciled` so the history stays honest about being found green late, not caught live. Wired into
  `AutoSpawnLoop._drain_escalations` (`server/autospawn.py`) right after `verify_dispatched_escalations`.
- No dashboard change needed: `list_active_escalations`'s existing `active_within_hours=24` /
  `include_resolved_within_hours=24` (dashboard/src/api.ts) already caps what the widget shows to a rolling 24h — a row
  the reconcile pass flips to `resolved` naturally reappears there as a fresh "closed the loop" entry for 24h, then ages
  out same as any other resolution.

**Live rows**: the two `unified-trading-pm` escalations that prompted this are both well within the new 24h reconcile
window (15-17h old at time of writing) — `ao-self-pull.sh`'s ~15min cron auto-deploys this once merged to
`live-defi-rollout`, so no separate manual backfill was needed for them. Historical `unresolved` rows already older than
24h at deploy time are intentionally left as permanent record — they've already aged out of the dashboard's own display
window, so reconciling them has no visible effect and isn't worth an ad-hoc production DB mutation.

`agent-orchestrator/tests/test_escalation.py`: replaced `test_verify_red_past_deadline_reescalates_once` (which asserted
a page on the very first miss — now wrong) with `test_verify_red_past_deadline_first_miss_reescalates_silently` (no
page) and `test_verify_red_past_deadline_reaches_page_threshold` (pages once `PAGE_AFTER_REESCALATIONS` misses have
failed); added 4 new tests for `reconcile_stale_unresolved_escalations` (disabled-by-flag,
flips-to-resolved-within-window, still-red-left-alone, past-window-skipped). All existing cap-hit tests
(`test_verify_reescalation_capped_marks_unresolved`, the dedup/cooldown/cross-incident tests) reference
`escalation.MAX_REESCALATIONS` symbolically, so they hold under the new value unchanged.

## Todos

- [x] ✅ [DEVOPS] P1. Fix shipped: `agent-orchestrator@d9e59db6`.
- [x] ✅ [DEVOPS] P1. Regression tests added/updated in `tests/test_escalation.py`; full `quality-gates.sh --no-fix`
      green before shipping (ruff, basedpyright, pytest).
- [x] ✅ [DOCS] P2. Cross-referenced the superseded judgment in
      `/plans/active/issues/ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md`.

## Progress Log

- **2026-08-07 (interactive session)**: operator noticed the two stuck escalations via the AO dashboard, asked why
  they'd never resolve, then proposed the retune+reconcile design after confirming (via live `gh run list`) that `main`
  had in fact already gone green. Implemented, tested, `quality-gates.sh --no-fix` green, shipped via
  `quickmerge.sh --agent --files`. Auto-deploys to the live `planning` VM within ~15min via `ao-self-pull.sh`'s cron.
