---
doc_type: audit-result
title: Alert Quality Audit — Slack
summary:
status: in-progress
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, deployment-ui]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-18
audited_scope:
date: 2026-06-18
auditor: ikennaigboaka
parent_epic:
severity:
resulting_plan:
lib_version:
doc_versions_checked:
type: audit-result
epic: infrastructure_master
instructions_ref: plans/audit/instructions/infrastructure_master_audit_instructions.md
plan_of_record: plans/active/monitoring_control_plane_master_2026_06_10.md
author: ikenna [autonomous audit — Opus background agents]
assigned_vm: planning
source:
  [
    agent-orchestrator/server/notifications/slack.py,
    "agent-orchestrator/server/{health,autospawn,worker_liveness_watchdog,main_agent_keeper,plan_health,escalation,ci_reconcile,usage_poller,gh_rate_monitor,server}.py",
    "unified-trading-pm/.github/workflows/{ci-failure-watcher,promotion-lag-monitor,escalate-to-orchestrator,semver-agent,main-backmerge-to-ldr}.yml",
    scripts/repo-management/ci_failure_watcher.py,
    scripts/cicd/promotion_lag_monitor.py,
    codex/08-workflows/ci-cd-flow.md,
  ]
---

# Alert Quality Audit (Class 1 of 2)

> **Status: IN PROGRESS** — skeleton captures the operator's full requirement set (2026-06-18); the per-alert findings
> are being filled from two background Opus audit agents (server-side `notify_*` + CI/CD-GHA side). Update this doc as
> findings land, then derive the wrapper sub-plan.

## Operator requirements (2026-06-18 design session — verbatim intent, do NOT drop any)

The alerts the operator receives on Slack (`#ci-failures` + agent-orchestrator alerts) are the problem. Decisions:

1. **Alerts are ERROR POINTERS, not audits.** An alert must say WHAT broke + WHICH surface to open (agent-orchestrator
   UI for agent/orchestrator issues; deployment-ui monitoring for CI/CD/codebase/fleet/image issues). The full detail
   lives in the UI — the alert routes you there. (Matches the master's "Slack = alerting only, actionable transitions,
   no steady-state monitoring.")
2. **~60–80% of daily alerts are REPEATED / useless.** → tune firing frequency + add deduplication so the same standing
   condition does not re-fire every tick.
3. **Messages are not meaningful / too low-detail to infer.** Cited bad examples: "a branch is behind", "there's a stuck
   PR" — almost no actionable info. → rewrite alert messages to the error-pointer standard.
4. The recurring/duplicate firing + low-info messages together make the channel hard to use → the goal is a channel
   where each line is a distinct, actionable, click-through-able error.

## Findings — server-side alerts (agent-orchestrator `notify_*`) — COMPLETE (Opus agent, 2026-06-18)

Audited all 24 `notify_*` in `server/notifications/slack.py` + every caller. Held against the master's Alert-parity
(L72-78), Division-of-surfaces (L80-86: "Slack = alerting only, no steady-state monitoring"), Click-through (L56-69), N1
(L100).

**Headline conclusions (the operator's complaints, root-caused):**

1. **The 60–80%-repeat is NOT systemic missing dedup — the fast loops are already correctly deduped** (Health 60s, Usage
   30m, gh-rate 120s all use state-transition/state-set guards). The real repeat source is that **every dedup set/flag
   is per-process IN-MEMORY and resets on every central-VM restart** → on restart it re-fires the alert for every
   still-true condition. Offenders: `health.py:77-78`, the `usage_poller` `_*_ALERTED` sets, `escalation.py:674`
   `_pool_exhaustion_alerted`, `gh_rate_monitor.py:296`, `worker_liveness_watchdog.py:702` `_burn_flagged`,
   `_git_alerts.py` throttle dicts. **FIX (biggest single win): persist dedup state to disk** using the proven
   `ci_reconcile.load_etag_cache/save_etag_cache` pattern (ci_reconcile.py:208-242) under `config.STATE_DIR`.
2. **Three alerts describe ONE condition ("no capacity to dispatch"):** `notify_account_pool_exhausted` (#9),
   `notify_all_accounts_exhausted` (#15), `notify_all_accounts_unusable` (#21). **#15 has no live caller (likely
   dead/duplicate) → delete after confirming**; consolidate to one critical page.
3. **`notify_work_picked_up` (#20, slack.py:690) is steady-state monitoring in the FAILURE channel** — fires on every
   task dispatch (slots_worker.py:187, escalation.py:422); directly violates the Division-of-surfaces "no steady-state"
   rule. **Remove from Slack or default-off** (`ORCHESTRATOR_NOTIFY_WORK_PICKED_UP=false`).
4. **`notify_agent_stuck_respawned` (#7) is semantically overloaded** across real watchdog respawn
   (worker_liveness_watchdog.py:896), plan-health dispatch heads-up (plan_health.py:78), AND escalation dispatch
   heads-up (escalation.py:144) — all render a misleading ":arrows_counterclockwise: Auto-respawn slot N" header (same
   bug-class the slot-0 abandon fix already corrected). **Split into purpose-specific functions.**
5. **The cited low-info offenders lack the mandated UI click-through** — they dead-end in CLI hints, not deep-links:
   - **#4 `notify_git_staleness_red` = the operator's "a branch is behind" example** (slack.py:117): header "git
     staleness" with no repo/why (dirty vs behind vs dead-cron conflated into one `max()` number, \_git_alerts.py:198);
     only action is a `journalctl` CLI line — **no `/fleet-git` deep-link** (violates click-through HARD RULE L64-66).
   - **#12 `notify_escalation_unresolved` = the "stuck PR" class** (slack.py:425): says "inspect the wall's
     quality-gates-v2 / PR state" but renders **no PR/run link**.
   - Also #8 `notify_agent_stuck_escalation`, #13 `notify_autospawn_flap` — CLI hints (`ssh`, `tmux attach`), no UI
     link.

**Per-alert verdicts (24):** keep-as-is (well-designed, only add deep-link): #9 pool-exhausted, #10
escalation-abandoned, #10b escalation-resolved, #18 token-expiring, #19 auth-failed, #21 all-unusable, #22 usage-high
(consider severity downgrade), #23 gh-rate (drop the 50% NOTICE tier). · **re-message** (error-pointer + deep-link): #1
slot-blocked, #2 slot-stale, #3 slot-failed, #4 git-staleness, #5 unpushed-plans, #8 stuck-escalation, #11
plan-health-findings (no standing dashboard surface — mild alert-parity gap), #12 escalation-unresolved, #13
autospawn-flap, #16 watchdog-kill, #17 context-burn. · **dedup** (add throttle on autospawn path): #6 spawn-failure. ·
**split**: #7. · **delete/consolidate**: #15 (dead), #20 (steady-state). · **reduce-frequency/downgrade**: #14
account-rotated (same-op → dashboard-only, alert only on cross-op).

**Proposed dedup/frequency strategy:** loop intervals are FINE — fix is at the EMIT layer (edge-trigger off PERSISTED
state, never level-emit each tick). Canonical dedup keys: slot health `(type,slot_id)`; git/fleet `(type,slot_id,repo)`

- raise throttle 30m→"until recover, max 4h"; account `(type,account_id,window)`; escalation per-row-terminal; gh-rate
  graduated. Add a RESOLVED bookend to high-sev transitions lacking one (slot-failed, git-staleness, auth-failed).

**Proposed error-pointer message standard:**

```
{sev} {SUBJECT} — {one-line WHAT + key number(s)}
{≤2 lines load-bearing facts: repo / slot / count / age}
→ {ONE deep-link to the authoritative surface}   (CLI hint secondary, never the primary action)
{dedup note: "(once per episode; RESOLVED bookend follows)"}
```

Rules: WHAT in the header not a bare label; exactly one correct WHERE-TO-CLICK (fleet/slot→AO `/fleet-git?slot=N`;
PR/run/sha→GitHub; account/CI→deployment-ui); no audit/review detail in the body (e.g. #11 should be "N drift / M
contradictions → open {surface}", not an 8-item dump); reserve 🚨/⛔/🆘 for "fleet/trading can't proceed".

## Findings — CI/CD + GitHub-Actions alerts + cross-channel overlap — COMPLETE (Opus agent, 2026-06-18)

Audited 50 PM workflows + 10 AO workflows + `ci_failure_watcher.py` + `promotion_lag_monitor.py`, cross-checked vs the
server `notify_*`.

**THE STRUCTURAL ROOT CAUSE (single highest-leverage fix):** `notify-slack.yml` — the reusable workflow ~34 GHA alert
callers route through — **has ZERO dedup** (`notify-slack.yml:45-182` posts unconditionally), and the central alert
ledger it writes (`:196-228`) is **WRITE-ONLY (never read back to suppress repeats)**. Emitters that DON'T repeat each
invented their own per-emitter state file (manifest `locked_alert_sent`, `ldr_ci_status`, Firestore `repo_state`) —
proving dedup belongs in the shared carrier. **Fix: add `dedup_key` + `cooldown_min` inputs to `notify-slack.yml`; read
the existing ledger JSONL before posting; skip a key seen within cooldown.** This converts the whole fleet from "re-page
while true" → "page on transition" in ONE place — directly killing the 60–80% repeat without per-emitter rewrites.

**Cross-channel duplication (one event → up to 4 pages):** a stuck/conflict promotion PR is **triple-detected** —
`ci-failure-watcher.py:detect_stuck_prs` (`*/15`, 30m) + `promotion_lag_monitor.py:_stuck_prs/_classify_stuck_pr`
(`*/30`, 120m) + server-side escalation (#9 dispatch + S4 resolved/unresolved/abandoned). The two scripts even share
near-identical `_PROMOTION_HEADS`/`mergeStateStatus` logic. **Dangling staging lock is double-detected**:
`promotion_lag_monitor.py:_lock_dangle` (no dedup → re-pages every 30m) + `sit-starvation-detector.yml` (has dedup).

**Repeat sources (NOT cron-frequency — most already relaxed to `*/15`–`*/30`; it's no per-condition cooldown):**

- `promotion-lag` (#6, `promotion_lag_monitor.py:335-444`, `*/30`, no dedup) = **the operator's cited "branch behind"
  near-useless alert** — body `"{repo} {label}: {n} commit(s), oldest {m}m old"`, no run link, no surface pointer,
  re-pages for hours.
- stuck-PR Slack line (`ci_failure_watcher.py:719-726`, `*/15`, no Slack cooldown) — re-pages a wedged PR every 15m.
- cloud-build-failure-watcher (`cloud-build-failure-watcher.yml:232-246`, `*/30`) — **bypasses the carrier with an
  inline `curl`** → no dedup, no ledger entry, no truthful-severity classifier.

**Exemplars to copy (already match the operator's error-pointer ask):** `ci_failure_watcher.py:691-699` BILLING-BLOCK
(states what broke + exact fix location), `:700-713` STARTED-FAILING (failed job→step + log excerpt + run link),
`escalate-to-orchestrator.yml:264-292` (3-way truthful outcome + AO dashboard deep-link). The fix is making the noisy
emitters look like these.

**Surface routing (Division-of-surfaces L80-86 + Alert-parity L71-78):** CI/CD pipeline conditions (promotion-lag,
stuck-PR, SIT lock/starvation, cloud-build, per-repo CI, billing) → page the TRANSITION, deep-link the **deployment-ui
repo row**; the steady state lives there. Escalation/slot/git-health → **AO dashboard**. Any SHA/check/run/PR →
**GitHub** directly.

**Consolidated proposal:** (1) centralize read-back dedup in `notify-slack.yml`; (2) route cloud-build-watcher through
the carrier; (3) collapse the triple stuck-PR detector → `ci-failure-watcher` is SSOT (it also auto-recovers+escalates),
strip `_stuck_prs`/`_classify_stuck_pr` + `_lock_dangle` from `promotion_lag_monitor.py` (leave it a pure branch-pair
lag monitor; sit-starvation owns dangling-lock); (4) demote promotion-lag to transition-only (page on 60m-CROSSING, not
every tick); (5) cross-channel contract — `escalate-to-orchestrator.yml:267` `if: always()` notify re-pages on every
re-dispatch tick → gate it so #9 pages once "handed off" and S4 pages "resolved/abandoned".

**Remediation files:** `notify-slack.yml` (dedup), `scripts/cicd/promotion_lag_monitor.py` (strip stuck/lock, demote
lag), `scripts/repo-management/ci_failure_watcher.py` (gate stuck Slack line on the `escalation-dispatched` label),
`cloud-build-failure-watcher.yml` (route via carrier), `escalate-to-orchestrator.yml:267` (suppress per-tick re-page).

## Recommended decisions / proposed standard — audit DONE 2026-06-18

**Prioritized remediation (→ wrapper plan `plans/active/alert_quality_overhaul_2026_06_18.md`):**

1. **P0 — read-back dedup in the shared carrier `notify-slack.yml`** (`dedup_key`+`cooldown_min`; read the
   already-written ledger before posting) → whole GHA fleet flips "re-page while true" → "page on transition" in ONE
   place. Pair: **persist the server-side in-memory dedup state to disk** (ci_reconcile ETag pattern) so a central-VM
   restart stops re-firing every still-true alert. Together = the bulk of the 60–80% repeats gone.
2. **P1 — collapse duplicate detectors** (stuck/conflict-PR triple-detected; dangling-lock double-detected): make
   `ci-failure-watcher` the SSOT, strip `_stuck_prs`/`_classify_stuck_pr`/`_lock_dangle` from
   `promotion_lag_monitor.py`, gate the escalate `if: always()` per-tick re-page.
3. **P1 — message rewrite to the error-pointer standard** (header=WHAT+number; one correct deep-link; no audit detail in
   body) for the cited offenders: promotion-lag #6, git-staleness #4, escalation-unresolved #12, stuck-PR #3; demote
   promotion-lag to transition-only.
4. **P2 — delete/consolidate:** `notify_all_accounts_exhausted` #15 (dead); `notify_work_picked_up` #20 (steady-state →
   remove/default-off); split overloaded #7; route cloud-build-watcher via the carrier; drop gh-rate 50% tier; same-op
   rotation → dashboard-only.
5. **Surface-routing contract** (feeds Audit-2): CI/CD → deployment-ui repo row · escalation/slot/git-health → AO
   dashboard · SHA/check/PR → GitHub.
