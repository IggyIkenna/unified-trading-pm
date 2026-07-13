---
doc_type: plan
title:
  ci-failures Channel Cleanup — dedup promotion-lag, drop/digest CI-RECOVERED, deduplicate the 3-way failure reporting
summary:
  The ci-failures Slack channel carries 384 messages in 7 days (~54/day) across only 11 shapes. It is far healthier than
  agent-orchestrator-alerts, but three cleanups remove most of the noise while keeping the genuine CI-regression signal
  loud. Promotion-lag (42%) re-fires hourly for a standing lag because its notify-slack cooldown is only 60 min — bump
  it toward the promotion cadence. CI-RECOVERED green bookends (13%) are all-clears — drop/digest. The three failure
  reporters (python-quality-gates-v2 per-run 105, ci-status-update-transition 39, ldr-ci-monitor hourly 11) differ
  because they run at different granularities; the per-run QG alert dedups by SHA so it never suppresses across commits
  — key it by branch instead so a still-red repo pages once, not per failing push.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [alerts, slack, ci-cd, ci-failures, dedup, observability, notifications]
related: [agent_orchestrator_alert_channel_cleanup_2026_07_13.md, observability_master.md]
created: "2026-07-13"
last_updated: 2026-07-13
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: infra
drift_direction: advance-code
---

# ci-failures Channel Cleanup

> **Human / LOCAL plan** (`assigned_vm: NA`, default track) — operator-driven, not auto-dispatched. Follow-on to the
> agent-orchestrator-alerts cleanup, same playbook. If you'd rather this be AO-dispatched, say so and I'll refront it.

## Context — the 7-day audit (evidence)

Pulled every message from `#ci-failures` (channel `C0B6KLNR9BR`) for 2026-07-06 → 2026-07-13 via the
`SLACK_ALERTS_READER_BOT_TOKEN` reader bot. Artifacts in the workspace `alerts_audit/` dir:

- `alerts_audit/ci-failures_7d_2026-07-13.jsonl` — 384 raw messages
- `alerts_audit/ci-failures_grouped_7d_2026-07-13.json` — dedup groups (count + first/last-seen + example)

**Headline:** 384 messages / 7 days (~54/day) → **11 distinct shapes**. Healthy channel; the genuine CI-regression
signal (~40/wk) is worth keeping loud. Three targeted cleanups remove the bulk of the noise.

|    # | Count |   % | Shape                                                                           | Disposition                                   |
| ---: | ----: | --: | ------------------------------------------------------------------------------- | --------------------------------------------- |
|    1 |   160 | 42% | ⚠️ branch-health — **PROMOTION LAG >60m**                                       | **WS-1** dedup: cooldown too short (60m)      |
|    2 |   105 | 27% | 🚨 python-quality-gates-v2 — QG slice FAILED                                    | **WS-3** dedup by branch (currently by SHA)   |
|    3 |    49 | 13% | ✅ ci-status-update — **CI RECOVERED** (→green)                                 | **WS-2** drop/digest the green all-clears     |
|    4 |    39 | 10% | ❌ ci-status-update — **CI REGRESSION** (→red)                                  | **KEEP** — the actionable SSOT for "went red" |
|    5 |    11 |  3% | 🚨 ldr-ci-monitor — LDR went RED                                                | KEEP — hourly LDR-only sweep (no remote CI)   |
| 6–11 |   ~20 |  5% | ldr-ci-monitor INFO, branch-health INFO, freeze, cloud-build, major-bump, probe | KEEP (low volume)                             |

## Why the three failure reporters differ (operator question)

They are **not** duplicates — they run at different granularities, so their counts differ:

- **python-quality-gates-v2 (105)** — the `notify-qg-fail` job fires from INSIDE the QG workflow on failure, **per
  failed RUN** (any repo, any push/PR). Its `dedup_key` is `qg-fail:<repo>:<sha>` — the **SHA** makes every failing
  commit a fresh key, so it never suppresses across commits. Noisiest.
- **ci-status-update (39 red / 49 green)** — a `repository_dispatch` state machine (`FEATURE_GREEN`/`MAIN_GREEN`/
  `FAILING`). It fires only on a **state TRANSITION** (green↔red), so an already-red repo failing again does NOT
  re-fire. Already deduped → far fewer. This is the SSOT for "repo went red".
- **ldr-ci-monitor (11)** — an **hourly** cron that catches `live-defi-rollout` red transitions (LDR has no remote CI,
  so push-triggered QG can't see it). Hourly + LDR-only → fewest.

**Overlap:** a red event yields both a per-run QG alert AND a transition alert; every _subsequent_ failing push on the
still-red repo re-fires only the per-run one. So the redundant/noisy path is python-quality-gates-v2's per-run alert
(WS-3), while ci-status-update is the deduped SSOT to keep.

## Root causes + touch-points (all verified)

1. **Promotion-lag re-fires hourly (WS-1).** The dedup IS wired — `branch-health.yml` `lag-notify` → `notify-slack.yml`
   with `dedup_key: promotion-lag` — but **`cooldown_min: 60`** means a standing lag re-posts every 60 min.
   branch-health runs `*/30`, so a persistent lag pages ~once/hour (~24/day). The instruments-service LDR→main lag (was
   107 commits / ~9.7 days; now ~17 ahead) lagged nearly the whole week → ~160 hourly re-reminders. The alert is genuine
   — it was just buried in its own repeats (same failure mode as the AO git-health guard).
2. **CI-RECOVERED green bookends (WS-2).** `ci-status-update.yml` posts the red→green recovery
   (`🟢 CI RECOVERED: <repo> → GREEN`) through `notify-slack.yml`. These are all-clears — not operator-actionable.
3. **Per-run QG alert keyed by SHA (WS-3).** `python-quality-gates-v2.yml` `notify-qg-fail` uses
   `dedup_key: "qg-fail:<repo>:<sha>"` + `cooldown_min: 45` — the SHA defeats cross-commit dedup, so a still-red repo
   pages on every failing push.

## Timing basis (promotion cadence — operator's re-remind question)

Verified cadences: `ldr-to-main-promote.yml` = **`*/15`** (every 15 min, ~30-min LDR→main SLA); `branch-health.yml` lag
monitor = `*/30`; `ldr-ci-monitor.yml` = hourly. A promotion lag > 60 min = >4 missed promote cycles → genuinely stuck
(not normal in-flight churn). Operator: a 1–2 h re-remind is acceptable ("we keep shipping; when promotion runs it
merges"). **Caveat (operator):** GitHub-hosted `schedule:` crons deviate under load, so the `*/15`/`*/30` timings are
best-effort — the re-remind must be **age-based** (how long the pair has been un-propagated), not tick-based, to stay
correct when a cron slips. A future option is to trigger the lag check from our own scheduler (the AO backend) for
reliable timing — captured as a stretch item, not required for this cleanup.

## Design

- **WS-1 — Promotion-lag dedup.** Bump `branch-health.yml` `lag-notify` `cooldown_min` 60 → **120** (2 h; matches "1–2 h
  is fine" and ~8 promote cycles), keeping the existing `promotion-lag` dedup*key + the RESOLVED bookend
  (`lag-notify-resolved`, already present). Effect: a standing lag pages once on the 60-min crossing, then ~every 2 h,
  and clears with a RESOLVED — ~24/day → ~12/day, and a self-resolving lag makes far less noise. *(Cooldown is the one
  knob; if 2 h still feels noisy for a multi-day stuck lag, 240 is the notify-slack default.)\_
- **WS-2 — Drop/digest CI-RECOVERED.** Stop paging the red→green recovery from `ci-status-update.yml` (keep the
  REGRESSION →red page + the GCS ledger write). Simplest: gate the recovery branch so it persists + logs but does not
  call `notify-slack.yml` (mirror the AO WS-A "success is silent"); optionally surface a count in a periodic digest.
- **WS-3 — Deduplicate the per-run QG alert.** Change `python-quality-gates-v2.yml` `notify-qg-fail` `dedup_key` from
  `qg-fail:<repo>:<sha>` → **`qg-fail:<repo>:<ref_name>`** (branch, not SHA), and raise `cooldown_min` 45 → 120. Effect:
  a still-red branch pages once per red-period, not once per failing push — ~105 collapses toward the transition count,
  while a genuinely new failure after the cooldown still re-alerts. ci-status-update stays the authoritative
  went-red/recovered SSOT.

**Fleet-wide-template rule (HARD).** `branch-health.yml`, `python-quality-gates-v2.yml`, `ci-status-update.yml`,
`notify-slack.yml` are ROLLED-OUT templates — never hand-edit a per-repo copy. Edit the template source +
`rollout-workflow-templates.sh`; rollout is complete only when every repo copy is committed + pushed (CLAUDE.md "CI
verification after every push"). `promotion_lag_monitor.py` lives in PM `scripts/cicd/`.

## Codex SSOTs

- `codex/08-workflows/ci-cd-flow.md` (promotion flow, `*/15` LDR→main, ci_status Firestore-SSOT). Post-implementation,
  add the dedup/cooldown contract for the CI alert carrier there (or a new `codex/04-architecture/ci-alerting.md`
  sibling to the AO one) — WS-4.
- `notify-slack.yml` is the shared dedup carrier (`dedup_key` + `cooldown_min` + the green/INFO suppression gate).

## Open decisions (operator)

- **D1 — WS-1 cooldown value.** Propose **120 min** (2 h). Confirm, or prefer 240 (4 h) for a quieter multi-day stuck
  lag.
- **D2 — WS-3 aggressiveness.** Propose the safe **dedup-by-branch** (keeps per-run alert, deduped). Alternative: DROP
  the per-run QG Slack alert entirely and rely solely on ci-status-update transitions (collapses 105→0 but loses "new
  failure while already red" visibility). Confirm branch-dedup vs drop.
- **D3 — CI-RECOVERED.** Drop from Slack entirely, or keep a once-daily digest count? Propose drop + digest count.

## Todos

- [ ] [OPERATOR] P1. Resolve D1 (cooldown), D2 (branch-dedup vs drop per-run QG alert), D3 (recovered drop vs digest).
- [ ] [INFRA] P2. WS-1: in the `branch-health.yml` TEMPLATE, bump `lag-notify` `cooldown_min` 60 → 120 (D1); verify the
      `promotion-lag` dedup_key + `lag-notify-resolved` bookend are intact; roll out via
      `rollout-workflow-templates.sh`.
- [ ] [INFRA] P2. WS-3: in the `python-quality-gates-v2.yml` TEMPLATE, change `notify-qg-fail` `dedup_key`
      `qg-fail:<repo>:<sha>` → `qg-fail:<repo>:<ref_name>` + `cooldown_min` 45 → 120 (D2 = branch-dedup); roll out.
- [ ] [INFRA] P2. WS-2: in the `ci-status-update.yml` TEMPLATE, stop routing the red→green RECOVERED transition to
      `notify-slack.yml` (keep the REGRESSION page + the ledger write) per D3; roll out.
- [ ] [INFRA] P3. WS-1 (stretch): evaluate moving the promotion-lag check to a self-triggered path (AO backend) for
      cron-deviation-proof timing — age-based re-remind independent of GitHub's hosted scheduler.
- [ ] [REVIEW] P3. WS-4: document the CI-alert dedup/cooldown contract in `codex/08-workflows/ci-cd-flow.md` (or a new
      `codex/04-architecture/ci-alerting.md`); re-pull a 24–48 h window post-rollout and confirm the volume drop
      (evidence jsonl in `alerts_audit/`).

## Progress Log

- **2026-07-13** — Audit complete. 384 msgs / 7 days → 11 shapes. Root causes + exact touch-points verified: WS-1
  promotion-lag cooldown=60m too short (`branch-health.yml` lag-notify); WS-2 CI-RECOVERED green bookends
  (`ci-status-update.yml`); WS-3 per-run QG alert keyed by SHA (`python-quality-gates-v2.yml` notify-qg-fail). Answered
  the 3-way-count question (per-run vs per-transition vs hourly granularities). Promotion cadence confirmed `*/15`. Plan
  authored (human/LOCAL). Awaiting D1–D3 before code.
