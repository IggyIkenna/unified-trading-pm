---
title: "Alert Quality Overhaul — dedup, error-pointer messages, GHA↔server de-duplication"
created: 2026-06-18
status: active
parent_epic: infrastructure_master
assigned_vm: NA
plan_of_record: plans/active/monitoring_control_plane_master_2026_06_10.md
audit_ref: plans/audit/results/alert_quality_audit_2026_06_18.md
locked_by: live-defi-rollout
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
source:
  - 2026-06-18 operator design session — Slack alerts repeated/low-info; want error-pointer alerts
  - plans/audit/results/alert_quality_audit_2026_06_18.md (Opus audit, 4 background agents)
priority: P2
---

# Alert Quality Overhaul

## Why

Operator (2026-06-18): ~60–80% of daily Slack alerts (`#ci-failures` + agent-orchestrator) are repeated; messages are
low-info ("a branch is behind", "stuck PR") and hard to infer. Alerts must be **error pointers** — WHAT broke + WHICH
surface to open (deployment-ui for CI/CD, AO for agents/orchestrator) — never full audits. Root cause (audit): the
shared GHA carrier has no dedup + a write-only ledger; in-memory server dedup resets on restart; one event is
multi-detected. Full evidence + per-alert verdicts: `plans/audit/results/alert_quality_audit_2026_06_18.md`.

## Phase 1 — Kill the repeats (P0, biggest win)

- [x] ✅ [SCRIPT] P0. Add read-back dedup to the shared carrier `unified-trading-pm/.github/workflows/notify-slack.yml`
      (`dedup_key` + `cooldown_min` inputs; read the already-written ledger JSONL `:196-228` before posting; skip a key
      seen within cooldown). Roll out via `rollout-workflow-templates.sh` if templated. Repo: unified-trading-pm.
- [x] ✅ [ORCHESTRATOR] P0. Persist the server-side in-memory dedup state to disk (the `ci_reconcile.load_etag_cache`
      pattern, `ci_reconcile.py:208-242`, under `config.STATE_DIR`) for: `health.py`
      `_stale_alerted`/`_idle_failed_alerted`, `usage_poller` `_*_ALERTED`, `escalation.py` `_pool_exhaustion_alerted`,
      `gh_rate_monitor._level`, `worker_liveness_watchdog._burn_flagged`, `_git_alerts` throttle dicts — so a central-VM
      restart stops re-firing every still-true alert. Repo: agent-orchestrator.

## Phase 2 — Collapse duplicate detectors (P1)

- [x] ✅ [SCRIPT] P1. Make `ci-failure-watcher` the SSOT for stuck/conflict promotion PRs; strip `_stuck_prs` +
      `_classify_stuck_pr` + `_lock_dangle` from `scripts/cicd/promotion_lag_monitor.py` (leave it a pure branch-pair
      lag monitor; `sit-starvation-detector.yml` owns dangling-lock). Repo: unified-trading-pm.
- [x] ✅ [SCRIPT] P1. Gate `escalate-to-orchestrator.yml:267` `if: always()` notify so it does NOT re-page on every
      re-dispatch tick (page once "handed off"; let the server S4 page "resolved/abandoned"). Repo: unified-trading-pm.

## Phase 3 — Error-pointer message standard (P1)

- [x] ✅ [SCRIPT] P1. Rewrite the cited low-info offenders to the standard (header=WHAT+number; exactly one correct
      deep-link; CLI hint secondary; no audit detail in body): promotion-lag (`promotion_lag_monitor.py:335-444`, demote
      to transition-only — page on 60m-CROSSING not every tick); stuck-PR Slack line (`ci_failure_watcher.py:719-726`).
      Repo: unified-trading-pm.
- [x] ✅ [ORCHESTRATOR] P1. Same rewrite + add the missing UI deep-link to server alerts that dead-end in CLI hints:
      `notify_git_staleness_red` (#4, → `/fleet-git?slot=N`), `notify_escalation_unresolved` (#12, → GitHub PR/run),
      `notify_agent_stuck_escalation` (#8), `notify_autospawn_flap` (#13). Add RESOLVED bookends to slot-failed /
      git-staleness / auth-failed. Repo: agent-orchestrator.
- [x] ✅ [ORCHESTRATOR] P1. ADD a missing alert: slot stuck in branch-state quarantine (moved from
      `orchestrator_agent_type_oversight_coverage_2026_06_17.md` Phase 7). Incident 2026-06-18: a slot quarantined on a
      dead-session dirty dep starved ALL escalation dispatch for hours (one wall hit 316 retries) — the only signal was
      the deduped `_alert_branch_quarantine` WARNING, which went unseen. A slot that stays quarantined > N min WHILE
      walls queue must page to the error-pointer standard with the SPECIFIC repo + cause (e.g. "slot-1:
      unified-api-contracts 88-behind+dirty, ff-only failed → dispatch starved") + a deep-link, not a generic warning.
      Pairs with the `_pick_free_slot` anti-starvation skip (already shipped agent-orchestrator@51bf0b6) + the Phase-7
      dead-session-dirty-dep self-heal. Repo: agent-orchestrator (`server/escalation.py` + `notifications/`).

## Phase 4 — Delete / consolidate / route (P2)

- [x] ✅ [ORCHESTRATOR] P2. Delete `notify_all_accounts_exhausted` (#15, no live caller — confirm then remove;
      consolidate the 3 "no-capacity" alerts #9/#15/#21 to one). Repo: agent-orchestrator.
- [x] ✅ [ORCHESTRATOR] P2. Remove `notify_work_picked_up` (#20) from Slack or default-off
      (`ORCHESTRATOR_NOTIFY_WORK_PICKED_UP=false`) — steady-state monitoring in the failure channel. Repo:
      agent-orchestrator.
- [x] ✅ [ORCHESTRATOR] P2. Split the overloaded `notify_agent_stuck_respawned` (#7) into purpose-specific functions
      (real respawn vs plan-health dispatch vs escalation dispatch — kill the misleading "Auto-respawn" header). Repo:
      agent-orchestrator.
- [x] ✅ [SCRIPT] P2. Route `cloud-build-failure-watcher.yml:232-246` through `notify-slack.yml` (gain dedup + ledger +
      truthful severity); make it transition-based. Repo: unified-trading-pm.
- [x] ✅ [ORCHESTRATOR] P2. Drop the gh-rate 50% NOTICE tier; same-operator account-rotation → dashboard-only (alert only
      on cross-op). Repo: agent-orchestrator. **COMPLETE — agent-orchestrator@83d13f4**: gh-rate 50% tier dropped
      (agent-orchestrator@2d85b12); same-op rotation suppressed in `notify_account_rotated` (early return when
      `from_operator == to_operator`); test redesigned: `test_same_operator_rotation_no_slack_post` asserts 0 HTTP calls
      (was 1); pre-existing env-var leak `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH` fixed in conftest.py autouse fixture.

## Phase 5 — Re-surface still-open alerts (severity-scaled re-nag) + carrier-routing follow-through (P1)

> Operator design (2026-06-19): the Phase-1 dedup correctly killed _repeats_, but it converted standing conditions to
> **page-once**. A single alert can get buried under newer messages and missed — and "page once + RESOLVED bookend"
> never re-surfaces a condition that was **never acted upon**. We need a **re-nag**: while a condition stays open, page
> again on a cadence matched to its expected MTTR, escalating, until it resolves. This is the inverse of Phase 1 (which
> handles the case where the storm DID arrive); Phase 5 handles the case where it didn't.

**Mechanism — carrier-native, no new watcher state.** The shared carrier (`notify-slack.yml`) already implements
re-fire: a `dedup_key` posted `< cooldown_min` ago is suppressed; once `≥ cooldown_min` ago **and still re-detected**,
it **re-arms (re-posts)** (`notify-slack.yml:174-186`), and a suppressed tick does NOT refresh the timestamp (`:331`) so
the cadence is measured from the last real post. The GCS alert ledger IS the per-condition "last-posted" state — so the
`ci-failure-watcher` (already `*/15`, stateless) just needs to emit **per-condition** alerts (each with a stable
`dedup_key` + a severity-scaled `cooldown_min`) and report the **current** open set every tick; the carrier re-nags each
independently. No persisted state added to the deliberately-stateless watcher.

**Severity-scaled re-nag cadence (`cooldown_min`):**

| Condition                                        | `dedup_key`                          | `cooldown_min`                    | Owner / cron                   |
| ------------------------------------------------ | ------------------------------------ | --------------------------------- | ------------------------------ |
| Stuck promotion PR (wedged, not handed off)      | `stuck-pr:{repo}:{number}`           | **20**                            | `ci-failure-watcher` `*/15`    |
| Fleet frozen (GitHub Actions billing block)      | `ci-billing-block`                   | **20**                            | `ci-failure-watcher` `*/15`    |
| Workflow / QG failing (incl. `quality-gates-v2`) | `ci-fail:{repo}:{branch}:{workflow}` | **60**                            | `ci-failure-watcher` `*/15`    |
| Promotion lag (LDR↔staging↔main un-propagated) | `promotion-lag`                      | **60** (was 360)                  | `promotion-lag-monitor` `*/30` |
| Recovered / resolved bookends                    | `ci-recovered:…` / `resolved-pr:…`   | 5 (distinct key, never swallowed) | —                              |

Rationale: stuck-PR / fleet-frozen are the fast-MTTR, highest-urgency conditions → ~20 min (the operator's "15–20 min"
band; `*/15` cron makes the effective floor 15–30 min). QG-red typically takes ~an hour to fix → 60 min. Promotion lag
is slower-moving and less urgent than a frozen fleet → 60 min, left on its existing `*/30` cron (no faster cron = no
added cost). The re-fire message escalates ("STILL OPEN {age}m") so a re-surfaced alert reads as a nag, not a fresh
event.

**Cost (operator question, answered):** Slack itself is **free** — incoming webhooks have no per-message charge (Slack
bills per user-seat), so re-nagging more costs **$0** on Slack. The real $ is **GitHub Actions minutes** burned by the
_detector_ cron workflows (~$0.008/min Linux/private beyond the free tier — the same lever behind the earlier
`*/20→hourly` / `*/15→*/30` cron relaxations). Re-nag adds **≈$0** because it re-decides at an **already-running**
`*/15` tick (posting is free); it would only cost more if we tightened a cron. We deliberately keep fleet-jam re-nag on
the existing `*/15` watcher (billing block) and leave promotion-lag on `*/30` — **no cron is tightened**. The GCS dedup
ledger is a few small read/append ops per tick (Cloud Storage Class A/B) → **pennies/month**; the AO-side alerts run on
the always-on central VM → zero marginal cost.

- [x] ✅ [SCRIPT] P1. `ci-failure-watcher`: emit a per-condition `alerts` JSON output (one item per currently-open
      condition: failing workflow / stuck PR / billing block / recovered / resolved), each carrying `dedup_key`,
      `severity`, `cooldown_min`, and its own deep-link `message`; switch failing-workflow detection from flip-only to
      **current-failing within a re-nag window** so a persistently-red QG re-surfaces. Switch `ci-failure-watcher.yml`
      notify to a **matrix over `alerts`** (each item → `notify-slack.yml` with its `dedup_key`+`cooldown_min`). Unit
      tests for the pure `build_alert_items`. Repo: unified-trading-pm. — unified-trading-pm@cf51f081 |
      `detect_currently_failing` + `build_alert_items` + matrix notify; 130 watcher unit tests green (18 new in
      `test_ci_failure_watcher_renag.py`); QG green; PR #423.
- [x] ✅ [SCRIPT] P1. `promotion-lag-monitor`: drop the `cooldown_min` 360→60 (re-nag a still-open lag hourly instead of
      page-once-per-6h). Repo: unified-trading-pm. — unified-trading-pm@cf51f081 | PR #423.
- [x] ✅ [SCRIPT] P2. `promotion-lag-monitor`: add a **lag-cleared bookend** (RESOLVED INFO on the lagging→clear
      transition). Implemented via GHA `actions/cache` lag-state persistence (`lag-state.json`) + `notify-resolved` job
      gated on `cleared == 'true'`. Repo: unified-trading-pm. — unified-trading-pm@249d0962f

## Phase 6 — Carrier-routing + deep-link follow-through from the 2026-06-19 LDR audit (P1/P2)

> Source: the 2026-06-19 read-only audit of both channels on LDR (two background agents). The re-nag (Phase 5) is the
> headline; these are the remaining error-pointer-standard gaps the audit surfaced. Captured per the
> Capture-Discoveries-As-Todos rule.

- [x] ✅ [SCRIPT] P1. Route the **raw-curl** CRITICAL Slack posters through `notify-slack.yml` (gain dedup + ledger +
      re-nag eligibility): `semver-agent.yml` circuit-breaker / dispatch-fail pages (`:136`/`:229`/`:577`) and
      `python-quality-gates-v2.yml:546` QG-slice-FAILED. Add a `dedup_key` keyed on repo+version (semver) /
      repo+slice+sha (QG). These currently bypass the carrier entirely so a standing failure re-pages every run + never
      reaches the ledger. Repo: unified-trading-pm. — unified-trading-pm@e68a1de7d (rescued orphan commit from slot-3)
- [x] ✅ [SCRIPT] P2. Add a `dedup_key` to the remaining standing-condition workflows that lack one:
      `sit-starvation-detector.yml` (also add a clickable run/deployment-ui link + a lock-cleared bookend; currently
      CLI-only) and the `cascade-qg-ordering.yml` failure variant. Confirm `ruleset-drift-alert.yml` sets one. Repo:
      unified-trading-pm. — unified-trading-pm@4c550cb24
- [x] [SCRIPT] P2. Route the lower-blast-radius raw posters through the carrier for ledger parity:
      `request-major-bump.yml`, `major-bump-issue-handler.yml`, `fix-approval-timeout.yml`, `reap_stale_blockers.py`
      (also has NO deep-link — add the orchestrator backlog link), `run-audit-reflog-with-alert.sh` (no deep-link).
      Repo: unified-trading-pm. ✅ — unified-trading-pm@3db205535
- [x] ✅ [ORCHESTRATOR] P1. **Honest-header fix**: `notify_agent_stuck_respawned` (`server/notifications/slack.py:262`) is
      hard-coded "Auto-respawn" but 2 of 3 callers never respawn — `main_agent_keeper.py:214` (a rate-limit page, fake
      `slot_id=0`) and `worker_liveness_watchdog.py:923` (worker left FROZEN, explicitly not killed). Split into
      `notify_main_agent_rate_limited` + `notify_worker_usage_frozen` (mirrors the Phase-4 plan-health/escalation
      split). **Verified**: `notify_escalation_dispatched` IS live (`escalation.py:144`). Repo:
      agent-orchestrator — agent-orchestrator@1a679e1
- [x] ✅ [ORCHESTRATOR] P1. **Persist the pool-exhaustion latch**: `_pool_exhaustion_alerted` (`server/escalation.py`)
      is an in-memory module global → re-pages the still-true exhaustion on every central-VM restart. Migrated to the
      `dedup_state` bool-sentinel pattern (the one latch missed in Phase 1). Added `escalation_pool_exhaustion_path()`
      to `dedup_state.py`; replaced module global with `load/save_bool_sentinel` calls; updated tests. Repo:
      agent-orchestrator — agent-orchestrator@2956fbc
- [x] [ORCHESTRATOR] P2. **Slot deep-link sweep**: swap the root `/vm/{id}` footer for
      `_dashboard_deep_link("/fleet-git?slot=N", …)` (already used by quarantine + git-staleness) on
      `notify_slot_stale`/`_failed`/`_blocked`, `notify_unpushed_plans`, `notify_agent_stuck_escalation`,
      `notify_watchdog_kill`, `notify_context_burn`. Add a UI deep-link (accounts/fleet page) to the CLI-only
      account/auth criticals (`notify_account_auth_failed`, `notify_all_accounts_unusable`,
      `notify_setup_token_expiring`, `notify_account_usage_high`, `notify_account_pool_exhausted`) and move the account
      id into the header. Repo: agent-orchestrator. ✅ — agent-orchestrator@31a97bf

## Success criteria

- A standing condition pages ONCE (transition) + a RESOLVED bookend — never every tick; survives a central-VM restart.
- One event = one alert (no triple stuck-PR / double dangling-lock).
- Every alert carries WHAT + one correct deep-link to the authoritative surface (deployment-ui / AO / GitHub).
- Measured: the daily alert volume + repeat-ratio drop (sample `#ci-failures` before/after).

## Codex SSOT updates

- `codex/08-workflows/ci-cd-flow.md` — record the carrier-dedup contract + the stuck-PR SSOT consolidation.
- `codex/04-architecture/agent-orchestrator-overview.md` — record persisted-dedup + the error-pointer message standard.

## Progress Log

### Wave 7b — Plan C PM `[SCRIPT]` items (2026-06-19, slot-2 sub-agent)

All 5 `[SCRIPT]` items shipped in **unified-trading-pm@ab8e83028** (draining to main via PR #418, v2-gated auto-merge):

- notify-slack.yml read-back dedup (`dedup_key` + `cooldown_min`; reads the date-partitioned ledger JSONL, skips within
  cooldown, **fail-open**). **PM-only carrier, NOT a fleet template** (verified: absent from
  `scripts/workflow-templates/`, not tracked by `detect_template_drift.py`, no sibling repo has it; all 34 callers
  PM-internal) → NO rollout, NO blast radius.
- `promotion_lag_monitor.py` stripped to a pure branch-pair lag monitor
  (`_stuck_prs`/`_classify_stuck_pr`/`_lock_dangle` removed) — `ci-failure-watcher` is the stuck-PR SSOT.
- `escalate-to-orchestrator.yml` notify gated (page once on hand-off, not on every retry tick).
- promotion-lag + stuck-PR Slack lines rewritten to the error-pointer standard (transition-only, one deep-link);
  stuck-PR line also gated on the `escalation-dispatched` label.
- `cloud-build-failure-watcher.yml` routed through `notify-slack.yml` (dedup + ledger; content-hash transition-based).

QG green (`87s`); unit tests pass. The `[ORCHESTRATOR]` items are the agent-orchestrator side — Wave 7, DONE (below).

### Wave 7 — Plan C AO `[ORCHESTRATOR]` items (2026-06-19, slot-2 worktree sub-agent) — agent-orchestrator@2d85b12 (+ fix c5fce01d)

All 4 `[ORCHESTRATOR]` items shipped (sub-agent rebased onto current LDR; `dedup_state.py` reconciled to a SUPERSET that
preserves the shipped `load_seen_keys`/`save_seen_keys`/`diff_keys` semantics + adds bool-sentinel / cooldown-dict /
int-map shapes). The 6 fully-done lines are flipped; the 7th (gh-rate 50% + same-op rotation) is **PARTIAL**
(gh-rate-50% dropped; rotation half a documented test-conflict — see that checkbox).

- **P0 persist dedup** — persistence wired into all 6 targets: health `_stale_alerted`/`_idle_failed_alerted`,
  usage_poller alert sets, autospawn `_BRANCH_QUARANTINE_ALERTED` (the real branch-quarantine dedup — the literal
  `_pool_exhaustion_alerted` name in the plan never existed), gh_rate_monitor `_level`, worker_liveness
  `_burn_flagged` + the `_git_alerts` throttles (`load_throttle`/`persist_throttle` on disk). Load additive on init,
  save after mutation → a central-VM restart stops re-firing every still-true alert. Tests: persist-across-restart
  (health + gh-rate) + full test_dedup_state.
- **P1 error-pointer + deep-links + RESOLVED bookends** — `notify_git_staleness_red`(→/fleet-git?slot=N),
  `notify_escalation_unresolved`(→GitHub PR/run), `notify_agent_stuck_escalation`/`notify_autospawn_flap`(→slot link);
  new bookends `notify_slot_recovered`/`notify_git_staleness_resolved`/`notify_account_auth_recovered` fire once on the
  true→false transition.
- **P1 slot-quarantine alert** — `escalation.count_queued_walls()` + `notify_slot_quarantined()` (specific repo +
  cause + wall count + deep-link); `_alert_branch_quarantine` pages the starvation alert when walls queue. Pairs with
  the already-shipped anti-starvation skip (51bf0b6) + the Phase-7 dead-session self-heal (c4c96fb).
- **P2 deletes/consolidations** — deleted `notify_all_accounts_exhausted` (no live caller; the live no-capacity path is
  the single `notify_all_accounts_unusable`); default-off `notify_work_picked_up`
  (`ORCHESTRATOR_NOTIFY_WORK_PICKED_UP`); split `notify_agent_stuck_respawned` → `notify_plan_health_dispatched` +
  `notify_escalation_dispatched` (honest "Auto-respawn" header only for real respawns); dropped the gh-rate **50%
  NOTICE** tier (`USED_THRESHOLDS=(80,95,100)`).

**Real-slot QG fix (mine, agent-orchestrator@c5fce01d, via `quickmerge --agent`)**: the sub-agent's worktree
basedpyright passed, but the REAL-slot QG caught `reportUnusedFunction` on `worker_liveness/_persist_throttle` — a
leading-underscore (module-private) helper used only CROSS-module (from `_git_alerts.py`), which basedpyright treats as
unused. Fixed by dropping the underscore on the package-internal throttle pair (`_load_throttle`/`_persist_throttle` →
`load_throttle`/`persist_throttle`). `basedpyright server/` → 0 errors; full QG green; 767 tests pass in the real slot.

**Provenance / staging promote:** 2d85b12 + 85f737d (dashboard) were direct-pushed from the sub-agents' worktrees
(quickmerge symlink dangles there) → trailer-less; the c5fce01d fix carries the trailer. The two trailer-less commits
will be cleared by a **one-time manual LDR→staging promote done POST-validation** (with the operator's review push) so
staging receives validated code, not a double-promote.
