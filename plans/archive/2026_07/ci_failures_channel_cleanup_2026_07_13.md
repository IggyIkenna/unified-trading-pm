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
status: complete # (was: active) 2026-07-15 plan-reconcile §6: remnant folded out to its target (operator ruling); zero open todos
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [alerts, slack, ci-cd, ci-failures, dedup, observability, notifications]
related: [/plans/active/agent_orchestrator_alert_channel_cleanup_2026_07_13.md, /plans/epics/observability_master.md]
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

## Timing basis (promotion cadence — MEASURED, operator's re-remind question)

Declared crons: `ldr-to-main-promote.yml` = `*/15`; `branch-health.yml` lag monitor = `*/30`; `ldr-ci-monitor.yml` =
hourly. **But the declared crons are NOT the real cadence.** Measured over the last 60 promote runs (2026-07-11 17:08 →
07-13 09:55 UTC, all `schedule`-triggered):

| metric          | value                       |
| --------------- | --------------------------- |
| **average gap** | **41.5 min**                |
| **median gap**  | **33.0 min**                |
| fastest         | 21.9 min (never reaches 15) |
| **slowest**     | **93.1 min** (~1.5 h)       |

So GitHub's hosted scheduler fires the promote at **~37% of the declared `*/15` rate** (~one run every 40 min, gaps up
to 93 min) — GitHub deprioritizes `schedule:` workflows on high-Actions-usage accounts. **Two consequences:**

1. **The 60-min lag threshold is now suspect.** With promote gaps up to 93 min, a lag of 60–90 min can simply mean _the
   next promote hasn't fired yet_, not a stuck promotion. Options (D4): raise the lag threshold to ~120 min (≥3 real
   cycles) so only genuinely-stuck lags alert; or make the threshold a small multiple of the observed p95 promote gap.
2. **Re-remind must be age-based, not tick-based.** Anchor the cooldown to how long the pair has been un-propagated, not
   to cron ticks (which slip). With a real ~40-min cadence, a 120-min cooldown ≈ 3 actual promote cycles.

A possible structural fix (considered, then **dropped by operator 2026-07-13 — not pursuing**): **trigger the promote
(and the lag check) from our own scheduler** (the AO backend, reliable 15-min tick) instead of GitHub's throttled
`schedule:` — then `*/15` would be real and both the threshold and re-remind become meaningful. The noise-cleanup (WS-1
cooldown → 2 h) is sufficient on its own; the measured cadence above is why the 2 h cooldown ≈ 3 real promote cycles.

## Design

- **WS-1 — Promotion-lag dedup.** Bump `branch-health.yml` `lag-notify` `cooldown_min` 60 → **120** (2 h; matches "1–2 h
  is fine" and ~3 REAL promote cycles at the measured ~40-min cadence), keeping the existing `promotion-lag` dedup key +
  the RESOLVED bookend (`lag-notify-resolved`, already present). Optionally raise the lag THRESHOLD 60 → 120 min per D4
  so a lag that is merely waiting for a throttled promote does not alert at all. Effect: a standing lag pages once on
  the threshold crossing, then ~every 2 h, and clears with a RESOLVED — ~24/day → ~12/day (fewer if the threshold
  rises), and a self-resolving lag makes far less noise. Cooldown is the one knob for cadence; 240 is the notify-slack
  default if 2 h still feels noisy for a multi-day stuck lag.
- **WS-2 — Drop/digest CI-RECOVERED.** Stop paging the red→green recovery from `ci-status-update.yml` (keep the
  REGRESSION →red page + the GCS ledger write). Simplest: gate the recovery branch so it persists + logs but does not
  call `notify-slack.yml` (mirror the AO WS-A "success is silent"); optionally surface a count in a periodic digest.
- **WS-3 — Deduplicate the per-run QG alert.** Change `python-quality-gates-v2.yml` `notify-qg-fail` `dedup_key` from
  `qg-fail:<repo>:<sha>` → **`qg-fail:<repo>:<ref_name>`** (branch, not SHA), and raise `cooldown_min` 45 → 120. Effect:
  a still-red branch pages once per red-period, not once per failing push — ~105 collapses toward the transition count,
  while a genuinely new failure after the cooldown still re-alerts. ci-status-update stays the authoritative
  went-red/recovered SSOT.

**Where these workflows live (verified — NOT fleet-rolled-out templates).** All three are PM-local and edited directly
in `unified-trading-pm/.github/workflows/` — no `rollout-workflow-templates.sh`:

- `branch-health.yml` — PM-local cron (scans all repos' lag from one place). Change takes effect from the DEFAULT branch
  (main) → must reach `main` via the LDR→main promote.
- `ci-status-update.yml` — PM-local; receives `repository_dispatch` from all repos' QG. Also fires from `main`.
- `python-quality-gates-v2.yml` — a **reusable workflow** every repo calls via
  `uses: IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates-v2.yml@live-defi-rollout`. One edit in PM
  applies fleet-wide the moment it is on `live-defi-rollout` (the pinned ref) — no rollout.

`notify-slack.yml` (the shared dedup carrier) + `promotion_lag_monitor.py` also live in PM. `.github/**` edits take the
sanctioned direct-push carve-out. (The rolled-out template is the separate `quality-gates-v2.yml.tmpl`, which only
dispatches to PM — it does NOT emit these alerts, so it is untouched.)

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` (promotion flow, `*/15` LDR→main, ci_status Firestore-SSOT). Post-implementation,
  add the dedup/cooldown contract for the CI alert carrier there (or a new `/codex/04-architecture/ci-alerting.md`
  sibling to the AO one) — WS-4.
- `notify-slack.yml` is the shared dedup carrier (`dedup_key` + `cooldown_min` + the green/INFO suppression gate).

## Decisions

- **D1 — WS-1 re-remind cooldown → RESOLVED: 120 min (2 h).** Operator (2026-07-13): "2 hour re-reminding if it's not
  solved." So `lag-notify` `cooldown_min` 60 → 120.
- **D2 — WS-3 aggressiveness → RESOLVED: dedup-by-branch.** Operator (2026-07-13): "your recommendation." Keep the
  per-run QG alert but key it `qg-fail:<repo>:<ref_name>` (branch) + `cooldown_min` 45 → 120, so a still-red branch
  pages once per red-period, not per failing push. ci-status-update stays the went-red/recovered SSOT.
- **D3 — CI-RECOVERED → RESOLVED: drop from Slack (+ digest count later).** Operator: "your recommendation." Stop paging
  the red→green recovery (keep the GCS ledger write); a count in a periodic digest is a P3 follow-up — the drop is the
  volume win.
- **D4 — WS-1 lag threshold → RESOLVED: keep 60 min (no change).** Operator: "let it run at its pace, don't worry about
  the lag threshold right now." WS-1 is the cooldown bump only; the threshold stays 60.

## Todos

- [x] [OPERATOR] P1. ✅ All decisions resolved (2026-07-13): D1=2h cooldown, D2=dedup-by-branch, D3=drop CI-RECOVERED
      (+digest later), D4=keep 60-min threshold. Plan unblocked for implementation.
- [x] 1. ✅ [INFRA] P2. WS-1: bumped `branch-health.yml` `lag-notify` `cooldown_min` 60 → 120 (D1); `promotion-lag`
      dedup_key + `lag-notify-resolved` bookend intact. PM-local cron (no rollout) — takes effect from `main`. —
      unified-trading-pm@e4b494356; YAML parses.
- [x] 2. ✅ [INFRA] P2. WS-3: `python-quality-gates-v2.yml` `notify-qg-fail` `dedup_key` `qg-fail:<repo>:<sha>` →
      `qg-fail:<repo>:<ref_name>` + `cooldown_min` 45 → 120 (D2). Reusable workflow — applies fleet-wide via the
      `@live-defi-rollout` ref (no rollout). — unified-trading-pm@e4b494356.
- [x] 3. ✅ [INFRA] P2. WS-2: gated `ci-status-update.yml` `notify` on `status == 'FAILING'` so only regressions page;
      the green CI-RECOVERED / SIT-pass all-clears drop from Slack (Firestore + GCS ledger writes unchanged) per D3.
      PM-local (fires from `main`). — unified-trading-pm@e4b494356.
- [x] 4. ✅ [REVIEW] P3. WS-4 (doc): wrote the CI-alert dedup/cooldown SSOT `/codex/04-architecture/ci-alerting.md` —
      the `notify-slack.yml` carrier contract (read-back dedup, `dedup_key`+`cooldown_min`, `recovery`-gating,
      fail-open), the per-reporter key/cooldown table (branch-health lag/AR, `notify-qg-fail`, `ci-status-update`), the
      3-way-count explainer (per-run vs per-transition vs hourly), and the "cooldown tracks MEASURED cadence not
      declared cron" rule. Cross-linked from `ci-cd-flow.md` § CI-health + the CLAUDE.md Slack-notifications bullet.
      Also fixed a stale SHA-based dedup comment in `python-quality-gates-v2.yml` left by WS-3 (actionlint clean).
      Frontmatter + size-cap + prettier green. — unified-trading-pm (this commit).
- [x] [REVIEW] P3. WS-4 (verify): re-pull a 24–48 h `#ci-failures` window post-rollout and confirm the volume drop
      (promotion-lag re-reminds ~2 h not hourly, no green all-clears, QG failures dedup per-branch); drop the evidence
      jsonl in `alerts_audit/`. (Pure observation window — same 24–48 h wait as AO WS-E.) — **FOLDED OUT** to
      plans/epics/observability_master.md (2026-07-15, plan-reconcile §6 operator ruling); tracked there, not here.

## Progress Log

- **2026-07-13** — Audit complete. 384 msgs / 7 days → 11 shapes. Root causes + exact touch-points verified: WS-1
  promotion-lag cooldown=60m too short (`branch-health.yml` lag-notify); WS-2 CI-RECOVERED green bookends
  (`ci-status-update.yml`); WS-3 per-run QG alert keyed by SHA (`python-quality-gates-v2.yml` notify-qg-fail). Answered
  the 3-way-count question (per-run vs per-transition vs hourly granularities). Plan authored (human/LOCAL).
- **2026-07-13 (implemented)** — WS-1/2/3 shipped in `unified-trading-pm@e4b494356` (3 PM-local workflow edits, all YAML
  valid). Corrected the plan's rollout assumption: these are NOT fleet-rolled-out templates —
  `python-quality-gates-v2.yml` is a reusable workflow applied via the `@live-defi-rollout` ref (fleet-wide, no
  rollout); `branch-health.yml` + `ci-status-update.yml` are PM-local and take effect from `main`. All operator
  decisions resolved. **Remaining:** WS-3 is live on LDR immediately; WS-1/WS-2 activate once `e4b494356` promotes
  LDR→main; then the WS-4 verification re-pull (24–48 h) confirms the volume drop. WS-1-stretch (self-triggered
  scheduler) + WS-4 (codex doc + digest count) stay open.
- **2026-07-13 (cadence measured)** — Operator flagged the promote is not really `*/15`. MEASURED last 60 promote runs:
  avg gap **41.5 min**, median **33 min**, max **93 min** — GitHub throttles the `schedule:` cron to ~37% of declared
  rate. Consequences folded in: (a) the 60-min lag threshold can fire on a lag merely waiting for a throttled promote →
  new **D4** (raise threshold 60→120); (b) re-remind must be age-based; (c) the self-triggered-scheduler stretch item is
  now evidence-backed. **D1 resolved: 2 h re-remind cooldown** (operator). D2/D3/D4 open.
- **2026-07-13 (WS-4 doc + stretch dropped)** — Operator: do WS-4, drop the WS-1 stretch. Wrote the CI-alert SSOT
  `/codex/04-architecture/ci-alerting.md` (carrier dedup/cooldown contract + per-reporter table + 3-way-count
  explainer + measured-cadence rule), cross-linked from `ci-cd-flow.md` § CI-health and the CLAUDE.md
  Slack-notifications bullet, and fixed a stale SHA-based dedup comment WS-3 left in `python-quality-gates-v2.yml` (the
  key is `ref_name` now; actionlint clean). **Deleted the WS-1-stretch todo** (self-triggered AO scheduler) per operator
  — not pursuing. Only the WS-4 verification re-pull (24–48 h observation) remains open, matching the AO-plan WS-E wait.
- **2026-07-13 (WS-5: sit-unlock icon contradiction)** — Operator flagged a `#ci-failures` alert showing
  `:white_check_mark: CRITICAL — sit-unlock | result: OK (success)` with body "SIT Failed — staging unlocked." Root
  cause: `sit-unlock.yml`'s notify passed `conclusion: needs.unlock-staging.result` — the UNLOCK job's mechanical result
  (`success`, because unlocking staging works fine) — which drives the carrier's icon, so a SIT-failure alert rendered a
  green ✅. Fixed the notify `conclusion` to reflect the alert SUBJECT: `failure` for both the unlock-failed and
  SIT-failed cases, `success` only on the genuine sit-passed green path. Now the SIT-failed alert renders `:x:` CRITICAL
  result FAILED. The `persist` job keeps `unlock-staging.result` (the ledger records the JOB outcome). actionlint clean,
  all 3 branches verified. — **unified-trading-pm@86e335607**.
- **2026-07-14 (WS-6: the dedup was silently BROKEN — anonymous gsutil)** — Operator: "non-stop duplicate QG-failed
  alerts for the same PR, I thought we deduped." Pulled the channel: PR#1008 fired **67** QG-failed pages in ~3h, one
  per commit. WS-3's key was CORRECT + stable (`gh` run log: `dedup_key: qg-fail:unified-trading-pm:1008/merge`), but
  the dedup gate logged `should_post=true (key not seen)` + a
  **`ServiceException: 401 Anonymous caller … storage.objects .list denied on unified-trading-cicd-events`**. Root
  cause: `notify-slack.yml` reads/writes the ledger with `gsutil`, but `auth@v3` only exports ADC — **gsutil ran
  anonymous**, so the read 401'd, the ledger looked empty, and the gate fail-opened on EVERY run. This silently broke
  dedup for **every** `dedup_key` alert (promotion-lag over-fired the same way — explains the 92 branch-health
  alerts/3d). Fix: added `setup-gcloud@v2` after `auth@v3` so gsutil authenticates (read + write); declared `GCP_SA_KEY`
  in the reusable `secrets:` block. — **unified-trading-pm@91ce0524c** (actionlint clean). codex `ci-alerting.md` gains
  the gotcha. **Verify:** next QG-failed run after this promotes should log `should_post=false (suppressed)` and the
  channel should collapse to one page per red-period per branch.
