---
doc_type: issue
title:
  SIT-gate treadmill recurs under high LDR commit velocity — unified-api-contracts/market-tick-data-service stuck 8/6
  straight blocked ticks, Slack alert silently cooldown-suppressed while worsening
summary: >-
  Live, 2026-08-08 ~10:30Z onward. A genuine code regression (UAC sports-taxonomy commit 1f5879fc removed
  odds_snapshot/odds_movement from DATA_TYPES_BY_ASSET_GROUP without updating MTDS's venue_data_types.yaml consumer)
  turned SIT red at ~10:30Z; already fixed in both repos by ~11:28Z (unified-api-contracts self-corrected,
  market-tick-data-service@b505b5e8 + @0c71f0e6). SIT itself reached green once (run 31254578291, 11:15:44Z) but a fresh
  LDR commit landed before the promoter's next tick could bank that result, cancelling the in-flight re-validate and
  restarting the ~10-15min round trip — this is exactly the mechanism documented (and mitigated, not eliminated) in the
  RESOLVED /plans/archive/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md: SIT validates
  "whatever LDR is now" each round, so convergence needs LDR quiescent for one full round trip, and today's LDR commit
  velocity (multiple sessions actively shipping across UAC/MTDS/UTL/PM) is high enough that no round has gone
  uninterrupted since. Root code fix already shipped; the treadmill itself is unresolved and NOT something a code fix in
  either affected repo can address (the retarget-to-validated-ancestor fix was designed and REJECTED on two
  independently-verified fatal grounds in the 2026-07-20 doc — not re-attempted here). Live-measured via
  `scripts/cicd/sit_gate_stuck_detector.py` (no --slack): unified-api-contracts steady at 8 straight SIT-gate-blocked
  ticks (11:38Z through at least 11:47Z, not climbing), market-tick-data-service climbing 4→6 straight over the same
  window. SEPARATE finding: `sit-gate-stuck-detector.yml`'s own run at 11:42Z computed this exact verdict internally but
  did NOT post to Slack — `notify/send-notification` logged `Dedup decision: should_post=false (key 'sit_gate_stuck'
  last posted 56m ago < 60m cooldown — suppressed)`. The monitor is not silent because the condition cleared; it is
  silent because its dedup cooldown fired on a condition that is, by the monitor's own internal measurement, WORSENING
  (MTDS 4→6) not repeating unchanged. A fixed cooldown window is the wrong dedup key for a monotonically-worsening
  streak count — see Todos.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts, market-tick-data-service, system-integration-tests]
scope: [engineer, admin]
tags: [ci-cd, sit, promotion, ldr-main, race-condition, monitoring-gap, alert-dedup]
related:
  [
    /plans/archive/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md,
    /plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-08
author: claude (interactive session, /ci-reconcile)
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: cicd
drift_direction: advance-code
depends_on: []
source:
  [
    "surfaced 2026-08-08 investigating a user-reported wall of sit-unlock/sit-gate-stuck Slack alerts the /ci-reconcile
    skill's prior sweep had not independently caught; root-caused live via gh Actions API + sit_gate_stuck_detector.py
    direct invocation, not from the Slack alert text",
  ]
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md,
    scripts/cicd/sit_gate_stuck_detector.py,
    .github/workflows/sit-gate-stuck-detector.yml,
    .github/workflows/ldr-to-main-promote-fleet.yml,
  ]
---

# SIT-gate treadmill recurring under high commit velocity, and its own stuck-detector is cooldown-silenced

## What was measured (live, 2026-08-08)

- 10:30Z–11:10Z: `full-workspace-sit.yml` red on `test_yaml_data_types_in_uac[market-tick-data-service]` —
  `venue_data_types.yaml` still declared `odds_snapshot`/`odds_movement` for BETFAIR/PINNACLE/ODDS_API after UAC commit
  `1f5879fc` (09:57Z) retired them from `DATA_TYPES_BY_ASSET_GROUP["sports"]` as MDPS-derived processed types.
- 11:02Z (market-tick-data-service@b505b5e8) + 11:28Z (@0c71f0e6, an unrelated STEP-5.105 gcloud-subprocess fix on the
  same tree): both real regressions fixed.
- 11:15:44Z: SIT run 31254578291 → **success**.
- 11:26:00Z: SIT run 31254957764 → **cancelled** (superseded by a fresh LDR commit before completion).
- 11:30:43Z → 11:41:53Z → 11:45:47Z: three more SIT dispatches queued/cancelled/in-progress in succession — the round
  trip has not completed uninterrupted since the one 11:15:44Z success.
- `sit_gate_stuck_detector.py` direct run, 11:47Z: `unified-api-contracts` 8 straight blocked ticks (unchanged since
  ≥11:38Z), `market-tick-data-service` 6 straight (was 4 at 11:42Z, 5 at the user-reported 11:12Z-window alert).
- `sit-gate-stuck-detector.yml` run 31255563526 (11:42Z): computed the above verdict correctly, but
  `notify/send-notification` step logged
  `Dedup decision: should_post=false (key 'sit_gate_stuck' last posted 56m ago < 60m cooldown — suppressed)`. No Slack
  post went out despite MTDS's count increasing since the last post.

## Why this isn't a code bug to fix in UAC or MTDS

Both real regressions that ORIGINALLY turned SIT red are already fixed and confirmed on `live-defi-rollout`. The
treadmill itself is the `sit_validated_tree`-vs-moving-LDR-tip race documented in the 2026-07-20 doc, whose intuitive
fix (retarget promote to the last-validated ancestor) was deliberately rejected there on two independently-verified
fatal grounds — re-deriving and re-attempting that design is explicitly out of scope per that doc's own framing, and
this session does not re-attempt it. The practical mitigation that doc DID ship (2026-08-06) reduces exposure but cannot
eliminate the race under sustained high commit velocity — which is what today's window is.

## Todos

- [ ] [DEVOPS] P2. **Fix `sit-gate-stuck-detector.yml`'s dedup key** — the cooldown should not suppress a repost when
      the detector's own worst-repo streak count has INCREASED since the last post (i.e. include the streak count, or a
      monotonic-worsening check, in the dedup decision alongside the flat 60-min timer). Read
      `scripts/self-hosted-runners/hosted-baseline/notify-slack.yml`'s dedup_key/cooldown_min contract before changing
      call sites elsewhere in the fleet. SSOT: `/codex/04-architecture/ci-alerting.md`.
- [ ] [DEVOPS] P3. **Re-check after LDR goes quiet** — once commit velocity on `live-defi-rollout` drops (multiple
      sessions currently shipping concurrently), confirm SIT completes an uninterrupted round and both repos' streak
      resets to 0; if it does NOT reset even once LDR is quiet for one full round-trip window, that would indicate a
      DIFFERENT, currently-masked bug and warrants fresh investigation (not assumed to be this same treadmill).

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — this doc was filed hours before this
sweep and self-describes as a still-live, unresolved condition (todo 2 explicitly gates on "once LDR goes quiet,"
unconfirmed). Todo 1 (fix the dedup-key cooldown logic) reads bounded in isolation, but dispatching a change to the
alerting mechanism actively instrumenting a live, hours-old incident carries real risk of masking the ongoing diagnosis
— the same "too hot to batch while live" posture this tranche applies to comparable same-day continuation docs (e.g.
`pytest_timeout_60s_flaky_under_contention_continued2/3`, parked live-incident in batch6 D6-16/D6-17). Checked today's 9
precedents; none apply. Revisit once todo 2's "LDR quiet" precondition is confirmed. No `assigned_vm` change.

## Progress Log

- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:5bafab3bb0900fde]: KEEP-NA,
valid — confirms the 2026-08-08 round7 verdict. Todo 1 (dedup-key fix) stays too-hot-to-touch while live; todo 2
explicitly gates on "LDR goes quiet," unconfirmed. Independently re-confirmed by today's
`ag_closeout_audit_ci_parked_2026_08_09.md` ("too_large_or_risky / live-incident... re-confirmed unchanged a day
later"). No `assigned_vm` change.

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:decf447e0673ce26]: KEEP-NA,
valid — Full read confirms 2 open items on a doc documenting a LIVE incident from 2026-08-08 (SIT-gate treadmill under
high LDR commit velocity, plus a cooldown-suppressed stuck-detector alert). Two prior audit passes (2026-08-08 round7,
2026-08-09) both kept KEEP-NA on 'too hot to touch while live' grounds for item 1 (dedup-key fix to the alerting
mechanism actively instrumenting the ongoing diagnosis), and item 2 is explicitly self-gated in its own todo text on a
live precondition ('once LDR goes quiet... confirm SIT completes an uninterrupted round and both repos' streak resets to
0'). As a read-only text-classification pass with no cloud/network access, I cannot independently verify whether LDR has
since gone quiet or the streak has reset -- the doc's own remediation path requires exactly that live check before
either item can responsibly move.
