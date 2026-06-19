---
title: "Alert Quality Overhaul — dedup, error-pointer messages, GHA↔server de-duplication"
created: 2026-06-18
status: active
parent_epic: infrastructure_master
assigned_vm: planning
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

- [ ] [SCRIPT] P0. Add read-back dedup to the shared carrier `unified-trading-pm/.github/workflows/notify-slack.yml`
      (`dedup_key` + `cooldown_min` inputs; read the already-written ledger JSONL `:196-228` before posting; skip a key
      seen within cooldown). Roll out via `rollout-workflow-templates.sh` if templated. Repo: unified-trading-pm.
- [ ] [ORCHESTRATOR] P0. Persist the server-side in-memory dedup state to disk (the `ci_reconcile.load_etag_cache`
      pattern, `ci_reconcile.py:208-242`, under `config.STATE_DIR`) for: `health.py`
      `_stale_alerted`/`_idle_failed_alerted`, `usage_poller` `_*_ALERTED`, `escalation.py` `_pool_exhaustion_alerted`,
      `gh_rate_monitor._level`, `worker_liveness_watchdog._burn_flagged`, `_git_alerts` throttle dicts — so a central-VM
      restart stops re-firing every still-true alert. Repo: agent-orchestrator.

## Phase 2 — Collapse duplicate detectors (P1)

- [ ] [SCRIPT] P1. Make `ci-failure-watcher` the SSOT for stuck/conflict promotion PRs; strip `_stuck_prs` +
      `_classify_stuck_pr` + `_lock_dangle` from `scripts/cicd/promotion_lag_monitor.py` (leave it a pure branch-pair
      lag monitor; `sit-starvation-detector.yml` owns dangling-lock). Repo: unified-trading-pm.
- [ ] [SCRIPT] P1. Gate `escalate-to-orchestrator.yml:267` `if: always()` notify so it does NOT re-page on every
      re-dispatch tick (page once "handed off"; let the server S4 page "resolved/abandoned"). Repo: unified-trading-pm.

## Phase 3 — Error-pointer message standard (P1)

- [ ] [SCRIPT] P1. Rewrite the cited low-info offenders to the standard (header=WHAT+number; exactly one correct
      deep-link; CLI hint secondary; no audit detail in body): promotion-lag (`promotion_lag_monitor.py:335-444`, demote
      to transition-only — page on 60m-CROSSING not every tick); stuck-PR Slack line (`ci_failure_watcher.py:719-726`).
      Repo: unified-trading-pm.
- [ ] [ORCHESTRATOR] P1. Same rewrite + add the missing UI deep-link to server alerts that dead-end in CLI hints:
      `notify_git_staleness_red` (#4, → `/fleet-git?slot=N`), `notify_escalation_unresolved` (#12, → GitHub PR/run),
      `notify_agent_stuck_escalation` (#8), `notify_autospawn_flap` (#13). Add RESOLVED bookends to slot-failed /
      git-staleness / auth-failed. Repo: agent-orchestrator.
- [ ] [ORCHESTRATOR] P1. ADD a missing alert: slot stuck in branch-state quarantine (moved from
      `orchestrator_agent_type_oversight_coverage_2026_06_17.md` Phase 7). Incident 2026-06-18: a slot quarantined on a
      dead-session dirty dep starved ALL escalation dispatch for hours (one wall hit 316 retries) — the only signal was
      the deduped `_alert_branch_quarantine` WARNING, which went unseen. A slot that stays quarantined > N min WHILE
      walls queue must page to the error-pointer standard with the SPECIFIC repo + cause (e.g. "slot-1:
      unified-api-contracts 88-behind+dirty, ff-only failed → dispatch starved") + a deep-link, not a generic warning.
      Pairs with the `_pick_free_slot` anti-starvation skip (already shipped agent-orchestrator@51bf0b6) + the Phase-7
      dead-session-dirty-dep self-heal. Repo: agent-orchestrator (`server/escalation.py` + `notifications/`).

## Phase 4 — Delete / consolidate / route (P2)

- [ ] [ORCHESTRATOR] P2. Delete `notify_all_accounts_exhausted` (#15, no live caller — confirm then remove; consolidate
      the 3 "no-capacity" alerts #9/#15/#21 to one). Repo: agent-orchestrator.
- [ ] [ORCHESTRATOR] P2. Remove `notify_work_picked_up` (#20) from Slack or default-off
      (`ORCHESTRATOR_NOTIFY_WORK_PICKED_UP=false`) — steady-state monitoring in the failure channel. Repo:
      agent-orchestrator.
- [ ] [ORCHESTRATOR] P2. Split the overloaded `notify_agent_stuck_respawned` (#7) into purpose-specific functions (real
      respawn vs plan-health dispatch vs escalation dispatch — kill the misleading "Auto-respawn" header). Repo:
      agent-orchestrator.
- [ ] [SCRIPT] P2. Route `cloud-build-failure-watcher.yml:232-246` through `notify-slack.yml` (gain dedup + ledger +
      truthful severity); make it transition-based. Repo: unified-trading-pm.
- [ ] [ORCHESTRATOR] P2. Drop the gh-rate 50% NOTICE tier; same-operator account-rotation → dashboard-only (alert only
      on cross-op). Repo: agent-orchestrator.

## Success criteria

- A standing condition pages ONCE (transition) + a RESOLVED bookend — never every tick; survives a central-VM restart.
- One event = one alert (no triple stuck-PR / double dangling-lock).
- Every alert carries WHAT + one correct deep-link to the authoritative surface (deployment-ui / AO / GitHub).
- Measured: the daily alert volume + repeat-ratio drop (sample `#ci-failures` before/after).

## Codex SSOT updates

- `codex/08-workflows/ci-cd-flow.md` — record the carrier-dedup contract + the stuck-PR SSOT consolidation.
- `codex/04-architecture/agent-orchestrator-overview.md` — record persisted-dedup + the error-pointer message standard.
