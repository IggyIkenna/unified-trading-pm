---
doc_type: issue
title:
  9-repo simultaneous QG cascade (21:07-21:17Z) — PM's `plans/active/*.md` corpus validator broke persistently for
  ~20-40min during concurrent /plan-reconcile archival sweeps; self-healed, but confirms the PM-corpus SPOF recurs in a
  NEW shape the morning's retry fix cannot span
summary: >-
  Second `/ci-reconcile` sweep of 2026-08-18. A fresh wave of Slack #ci-failures CRITICAL alerts (8:12PM-10:17PM)
  included a 9-repo simultaneous quality-gates-v2 FAILED cluster (alerting-service, trading-agent-service,
  market-tick-data-service, ml-service, instruments-service, strategy-service, unified-trading-library,
  unified-trading-pm, deployment-service — all live-defi-rollout push CI, 21:07-21:17Z) that superficially matched the
  SAME shape as the morning's 13-repo PM-manifest-race cascade (fixed via unified-trading-pm@176ff63dab, archived at
  /plans/archive/2026_08/issues/fleet_wide_qg_cascade_pm_manifest_race_plus_silent_webhook_gap_2026_08_18.md). It was
  NOT the same failure recurring — the morning's retry-after-repull hardening (base-service.sh/base-library.sh [6/6]
  PRODUCTION READINESS VALIDATORS) ran correctly on every one of the 9 failures, re-pulled PM, found "Already up to
  date", and STILL failed both passes — proving this was a genuinely persistent (not instant-race) break in PM's
  `plans/active/*.md` corpus (per `run_validators.py --scope all`'s dangling-link check) that outlasted the retry's
  ~5s window. Confirmed self-healed within ~30-40 minutes via PM's own high-velocity /plan-reconcile automation (no
  code fix needed) — verified live via `gh run rerun --failed` on alerting-service's unchanged sha (b0a10840) turning
  green, and a local `run_validators.py --scope all` pass. Separately, the same sweep's agent-orchestrator
  "QG slice CANCELLED/TIMED-OUT" alert (20:03-20:06Z) was root-caused to an UNRELATED, already-tracked P1
  (`codeload.github.com` 429 on `actions/checkout@v4`, self-hosted glue-runner pool) — see
  /plans/active/issues/glue_runner_pool_single_instance_fleet_wide_ci_queue_congestion_2026_08_15.md.
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    alerting-service,
    trading-agent-service,
    market-tick-data-service,
    ml-service,
    instruments-service,
    strategy-service,
    unified-trading-library,
    deployment-service,
  ]
scope: [engineer, admin]
tags: [ci-reconcile, pm-corpus-spof, plan-reconcile, dangling-link, self-healed, quality-gates-v2]
related:
  [glue_runner_pool_single_instance_fleet_wide_ci_queue_congestion_2026_08_15]
created: 2026-08-18
source: ci_reconcile-sweep-2026-08-18-evening
author: ci_reconciler
parent_epic: ci_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
resolved_by: >-
  Self-healed via PM's own /plan-reconcile automation between 21:17-21:41Z (no code fix needed — root cause was
  transient corpus content, not a defect). Confirmed with real evidence: gh run rerun 32185996475 (alerting-service,
  unchanged sha b0a10840) -> conclusion=success; local `python3 scripts/run_validators.py --scope all` -> clean
  (3/3 checks OK) as of this session. Morning's retry-after-repull fix (unified-trading-pm@176ff63dab) confirmed
  working exactly as designed — it correctly distinguished this from an instant race and did not falsely suppress a
  genuine (if transient) validator failure.
locked_by:
locked_since:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    scripts/quality-gates-base/base-service.sh,
    scripts/quality-gates-base/base-library.sh,
    scripts/run_validators.py,
  ]
drift_direction: advance-code
depends_on: []
---

> **🗄️ ARCHIVED 2026-08-18** — status: resolved (self-healed, verified with real evidence), no todos block archival
> beyond the tracked P3 follow-up below (threshold-triggered, not blocking). Filed and archived same-session per
> /codex/12-agent-workflow/plan-completion-and-archival-discipline.md.

# 9-repo QG cascade (21:07-21:17Z) — PM corpus broke persistently during an active /plan-reconcile sweep, self-healed

## What fired

Slack #ci-failures, 2026-08-18 evening (all times UTC unless noted):

- 19:12Z — Cloud Run Traffic Pin (signal-broadcast-smoke-receiver) — **unrelated**, self-resolved within 4 minutes by
  its own automation before this investigation even started; see Progress Log.
- 20:01Z — glue-runner-crash-loop-watchdog (`github-glue-runner-unified-api-contracts@glue-1.service`, 10.2h active)
  — **unrelated to this doc**, tracked under
  /plans/active/issues/glue_runner_pool_single_instance_fleet_wide_ci_queue_congestion_2026_08_15.md.
- 20:06Z — agent-orchestrator quality-gates-v2 "QG slice CANCELLED/TIMED-OUT" (sha 6bfd8eef) — root-caused to the
  SAME glue-runner P1 above (`codeload.github.com` 429 on `actions/checkout@v4` mid-"Set up job", 2 backoff retries
  then `A task was canceled.`), NOT this doc's cascade. See that doc's Progress Log for the newest recurrence entry.
- 20:55-20:56Z — deployment-service `main` branch quality-gates-v2 FAILED + CI REGRESSION (sha 7f509a00) —
  investigated separately this same sweep; see that thread's own resolution (folded into this sweep's final report,
  not this doc — different branch, different timing, needed its own root-cause pass).
- **21:07-21:17Z — THIS DOC**: 9 repos' quality-gates-v2 FAILED on live-defi-rollout push, in rapid succession:
  alerting-service (b0a10840), trading-agent-service (5cf8d509), market-tick-data-service (290b5458), ml-service
  (4a559d30), instruments-service (8a8edfa5), strategy-service (9d43d388), unified-trading-library (1bfd3e6a),
  unified-trading-pm (4c9549a1), deployment-service (b7fb1584).

## Why this looked like a repeat of the morning's cascade, and why it wasn't

The morning's incident (archived at
/plans/archive/2026_08/issues/fleet_wide_qg_cascade_pm_manifest_race_plus_silent_webhook_gap_2026_08_18.md) was a
`workspace-manifest.json` write race — an INSTANT window (two concurrent manifest-bump commits), caught by a single
retry-after-repull with a 5s gap. This evening's cascade LOOKED identical in symptom (many unrelated repos' QG
"checks" slice failing at once on `[6/6] PRODUCTION READINESS VALIDATORS`), but the actual failure logs
(`gh run view <id> --log-failed` for alerting-service run 32185996475 and unified-trading-pm run 32186076604) show
the retry ran correctly and did NOT save it:

```
── [6/6] PRODUCTION READINESS VALIDATORS ──
OK: workspace-manifest.json valid (schema + topological)
⚠️  Production readiness validators failed on first pass — re-pulling unified-trading-pm and retrying once...
From https://github.com/IggyIkenna/unified-trading-pm
 * branch            live-defi-rollout -> FETCH_HEAD
Already up to date.
OK: workspace-manifest.json valid (schema + topological)
❌ Production readiness validators FAILED (persisted after re-pull + retry) — fix unified-trading-pm/workspace-manifest.json and plans/active/*.md
##[error]QG selector 'lint-codex' FAILED (leg=checks, exit=1)
```

"Already up to date" on the re-pull, immediately followed by the SAME failure, is the tell: this was not a race the
retry could ever have caught, because there was nothing new to pull — the bad content was already the committed HEAD
of live-defi-rollout at the moment of each of these 9 repos' independent QG runs (21:07-21:17Z), and stayed bad for
long enough that every one of them hit it. `workspace-manifest.json` itself passed both times (`OK:`) — the actual
failure was the `plans/active/*.md` dangling-link check inside `run_validators.py --scope all`.

## Root cause

PM was under an unusually heavy concurrent load of automated `/plan-reconcile` sweeps this exact evening (visible in
`git log` around this window: `uac_master` @ 21:23:52+01, `plan_hygiene_master` @ 21:26:28+01, `ci_master` @
21:41:22+01 — each doing multi-file archivals, dangling-ref repoints, and closeout-linkage fixes across dozens of
docs in one commit). The archival ritual requires every referrer's path to be fixed in the SAME commit a doc moves
(CLAUDE.md, "Plans" §), but with several of these large sweeps landing on LDR within minutes of each other, it's
consistent with one sweep's commit briefly leaving a dangling `/plans/active/issues/...` reference that a moved
target doc's LATER, separate archival(from a concurrent sweep) hadn't yet repointed — a genuine, if narrow and
short-lived, corpus content break, not a code defect anywhere. The exact single commit/link responsible was not
pinned down this pass (multiple simultaneous sweeps make `git blame` ambiguous without a wider forensic pass); given
it demonstrably self-healed and no repo's own code needed a fix, further narrowing was not pursued — see "Not done"
below if it recurs and this becomes worth revisiting.

## Why the fix from this morning is not being extended further

This morning's retry-after-repull (unified-trading-pm@176ff63dab) is confirmed working exactly as designed here: it
correctly distinguished "instant race, retry catches it" (this morning) from "genuinely persistent this pass, must
fail loud" (tonight), and did NOT falsely suppress a real (if transient) content break. Widening the retry's backoff
or adding more attempts would need to span 20-40 minutes to have caught tonight's specific window — that is not a
viable trade for every one of the fleet's hundreds of daily QG runs (most of which hit this validator with nothing
wrong). The retry is correctly scoped for its actual job (absorbing sub-minute manifest-write races); a break that
outlasts an active multi-minute archival sweep is a fundamentally different class this workspace already has a
policy answer for (the archival ritual's same-commit-referrer-fix rule) rather than something a CI-side retry should
try to paper over. A more durable structural fix — validating repos' dependent-on-PM checks against a pinned
last-known-green PM sha rather than always live HEAD — would eliminate this whole failure class, but is a real
architecture change (affects every repo's QG clone-and-validate step) and is flagged here as a follow-up idea, not
attempted in this pass.

## What's NOT confirmed

- The exact commit/link that broke and the exact commit that fixed it (see above — not pinned down, self-heal
  confirmed by outcome, not by diff).
- Whether this specific concurrent-sweep-collision pattern (multiple `/plan-reconcile` epics landing large archival
  commits within the same few minutes) has a frequency trend — this is the second PM-corpus-SPOF-shaped incident in
  one day (this doc + the morning's manifest-race doc), which may warrant a standing watch if a third occurs.

## Progress Log

- 2026-08-18 (ci_reconciler, evening `/ci-reconcile` sweep): Filed after confirming self-heal via
  `gh run rerun 32185996475 --repo IggyIkenna/alerting-service --failed` -> success on unchanged sha, and a clean
  local `python3 scripts/run_validators.py --scope all` run (workspace-manifest.json valid, no broken links, all
  checklists OK). No code fix shipped — root cause was transient corpus content already resolved by PM's own
  automation between 21:17-21:41Z. Confirmed the morning's retry-after-repull fix (176ff63dab) behaved correctly
  (real persistent failure, not a race) rather than being buggy.

## Follow-ups (tracked work, not prose)

- [ ] [SCRIPT] P3. If a THIRD PM-corpus-SPOF-shaped cascade occurs within the next ~2 weeks, stop treating each as an
      independent one-off and open a scoped design task for pinning repos' `run-all-validators.sh` dependency against
      a last-known-green PM sha (or a short debounce on the validator itself) instead of always live HEAD — cite this
      doc and /plans/archive/2026_08/issues/fleet_wide_qg_cascade_pm_manifest_race_plus_silent_webhook_gap_2026_08_18
      as the first two data points.
