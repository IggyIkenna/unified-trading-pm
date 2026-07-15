---
doc_type: plan
title: Data-pipeline alerts batch remediation — drive #data-pipeline-alerts to a clean/accurate state
summary:
  "Operator pasted a dense batch of data-pipeline-alerts Slack alerts (2026-07-14 23:50 to 2026-07-15 00:19 UTC) —
  DP_RUN_MOSTLY_EMPTY across sports/cefi/defi/tradfi and DP_VM_EXIT_NONZERO for features-sports VMs — and asked (a) why
  identical alert payloads re-fire ~15min apart with no dedup/RESOLVED-green signal, (b) to actually fix the underlying
  consolidator/data issues since they affect data counts, and (c) to run this autonomously/locally with sub-agents,
  looping, until the channel is clean. Local human-driven track (not AO-dispatched) per operator's explicit 'locally'
  instruction."
status: active
nature: process
asset_group: [meta]
stage: [data]
repos:
  [
    unified-trading-pm,
    alerting-service,
    unified-trading-library,
    features-service,
    deployment-service,
    market-tick-data-service,
    instruments-service,
  ]
scope: [engineer, admin]
tags: [data-pipeline, alerting, manifest-consolidator, dedup, autonomous, incident]
related:
  [
    codex/05-infrastructure/data-pipeline-alerts.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
    plans/active/issues/manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md,
    plans/active/issues/defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md,
    plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md,
  ]
created: 2026-07-15
last_updated: 2026-07-15
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: [operator Slack alert paste, 2026-07-15 conversation]
assigned_role: infra
drift_direction: advance-code
---

# Data-pipeline alerts batch remediation — 2026-07-15

## Why this plan exists

Operator pasted ~60 Slack alerts from `#data-pipeline-alerts` (window 2026-07-14 23:50Z → 2026-07-15 00:19Z) and asked
three things in the same turn: (1) diagnose+fix why alerts repeat byte-identical payloads every ~15min with no
dedup/RESOLVED signal, (2) actually fix the consolidator/data issues since they affect real data counts (not just
document them), (3) drive this to a clean channel state autonomously, locally, on a loop, with sub-agents, without
stopping to ask. `/autonomous` was explicitly invoked. This is a LOCAL plan (`assigned_vm: NA`) — operator said
"locally"; not routed through AO ingestion.

**Codex SSOTs**: `codex/05-infrastructure/data-pipeline-alerts.md` (failure-mode registry + emit/route/escalate model),
`codex/05-infrastructure/manifest-consolidator-ssot.md` (consolidator runtime + verification recipe).

## Ground truth established before this plan was written (do not re-derive)

- The alert batch maps to a DENSE pre-existing corpus of tracked issue docs — this is NOT a fresh discovery, it's an
  active, ongoing, heavily-documented incident class. Confirmed via cross-reference agent + direct reads:
  - `manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md` (P1, open) — explains the
    `DP_VM_EXIT_NONZERO` features-sports alerts exactly: `uts-prod-manifest-consolidator-instruments-sports` Cloud Run
    job occasionally takes 8-9min instead of ~40s, blowing the 120s freshness budget. 0/9 VM launches succeeded as of
    last entry. Doc's own "most promising near-term fix": bounded retry-with-backoff in the features-service compute
    VM's startup gate (repo: features-service).
  - `defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md` (P1, open) — defi consolidator scheduler-triggered
    executions SIGKILL every ~5-6min (down from ~2min after a partial TTL fix); canonical manifest stuck stale for days
    at a time; MTDS defi VMs self-delete via OOM-preflight guard before ever running. Multiple mitigation rounds (memory
    bump, lock TTL) tried; root cause still NOT found. Next documented step: fix the Cloud-Run-jobs app-log-shipping gap
    (stdout logging bootstrap) so the actual in-container kill point becomes visible — explicitly deferred pending a
    concurrent UTL edit that may have since landed.
  - Many other tracked issues cover individual asset_group/data_type gaps (cefi resolved 07-13; various sports/tradfi
    issues). Full list surfaced by the cross-reference agent — see Progress Log entry below.
- Live `gcloud` check (2026-07-14 ~23:34Z) confirmed: `market-data-sports` consolidator's THEN-latest execution had
  failed with `Image '...market-tick-data-service:latest' not found`, but the NEXT execution 4 min later resolved the
  image fine and proceeded normally — a transient image-tag-resolution race at Cloud-Run-job execution-creation time
  (consistent with the precedent noted in `mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md`), NOT a sustained
  breakage. Not pursued further as its own item unless it recurs.
- AO backlog check (`check-ao-backlog-status.sh consolidator`) returned 0 matching dispatched/queued tasks — nobody is
  currently working these via the AO fleet. Safe to work locally without AO collision, but per-slot git-safety rules
  still apply (fetch before push, scope commits by name).
- Alert-repeat root cause: under active investigation by a background agent as this plan was authored — see Progress Log
  for the finding once it lands.

## Todos

- [x] [INFRA] P0. Diagnose and fix the alert-repeat/no-dedup/no-RESOLVED-green bug — BOTH layers shipped:
      `alerting-service@fe76ded34a4` (cadence-aware cooldown, `DP_RUN_MOSTLY_EMPTY: 1800.0`) +
      `deployment-service@0aaab1a22` (source-side `RenagTracker`, defense-in-depth). 166 unit tests pass,
      `quality-gates.sh` green both repos. Issue doc fully resolved (all 3 todos done):
      `plans/active/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md`.
- [x] [CODE] P1. Bounded retry-with-backoff shipped — `features-service@5e1ffd2e`
      (`_assert_consolidator_healthy_with_retry`, 3 attempts/75s/150s total, fail-fast intent preserved).
- [x] [INFRA] P1. Root cause found: `instruments-sports` consolidator has the IDENTICAL lock-contention livelock class
      already fixed for defi (just triggered by ordinary shard-backlog growth, not date-range chunking) — live
      `"clearing stale lock ... age>TTL"` reclaim signature confirmed it, `market-data-sports` control group (same
      timeout tier) stayed fast the whole time. Fixed via `deployment-service@69136c2c`
      (`CONSOLIDATOR_LOCK_TTL_SECONDS=2400` Terraform override, live-applied). Post-fix: 2+ six-minute cycles with ZERO
      stale-lock reclaims (previously guaranteed). Issue doc flipped `open` → `resolved`:
      `unified-trading-pm@05942b2f0`.
- [x] [INFRA] P1 — SUPERSEDED, not needed. The stdout-logging-bootstrap plan for defi turned out unnecessary: the actual
      root cause (lock-TTL livelock, not an unobservable in-container crash) was found and fixed via Terraform alone
      (see Ground Truth — defi fix already verified live-working before this todo was ever picked up). Leaving unstruck
      rather than deleted, per plan-hygiene (documents why the originally-planned approach wasn't taken).
- [x] [DATA] P1. Swept every (asset_group, data_type) pair from the alert batch. cefi/tradfi partial-ratio cells:
      already tracked under existing per-venue docs. New:
      `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` (3 root causes; mbp_10
      mechanical fix dispatched separately). Big finding: cefi blank-data_type 9,757-row "RESOLVED" claim was incomplete
      — live re-query confirms real-but-static orphan rows (not actively growing), annotated
      `phantom_captures_cefi_2026_06_28.md`. Commits: `unified-trading-pm@{0378027e6,fe674d7a3}`.
- [ ] [INFRA] P2. Re-run the manifest-consolidator-ssot.md verification recipe across the full fleet (all ~26 Cloud Run
      jobs) after the above fixes land; confirm no job is stuck on a stale/failing image or lock; note any PAUSED legacy
      job that's still being polled by the liveness watchdog (false-positive class already flagged in the defi sigkill
      doc's "Aside" section) and fix the watchdog's `--buckets` exclusion if still live.
- [ ] [REVIEW] P2. After fixes ship, observe the `#data-pipeline-alerts` channel behavior for one full cycle (or the
      longest relevant cadence — cefi is 24h) to confirm: no more byte-identical repeats, RESOLVED/green alerts appear
      when a previously-CRITICAL condition clears. Document actual observed channel state honestly (a "0.x% of alerts
      require a real upstream/adapter fix beyond this plan's scope" is an acceptable non-100% outcome IF documented with
      evidence — see Rule 1 exception below).
- [ ] [REVIEW] P3. Final report in this plan's Progress Log: every issue doc touched/filed, every code fix shipped
      (repo@sha), every genuine-impossibility/deferred-with-reason item, and the verified end-state of the alert
      channel.

## Progress Log

- 2026-07-15: Plan created. Investigation to this point (issue-doc cross-reference, live gcloud consolidator health
  checks, AO backlog check) summarized in "Ground truth" above. Two background agents in flight: (1) cross-reference of
  the alert batch against tracked issue docs — DONE, findings folded into Ground Truth; (2) alert-repeat/dedup
  root-cause investigation — in flight, will fold in on completion.
- 2026-07-15 (later same session): Alert-dedup root cause DIAGNOSED (agent completed) — full code-level cause with
  file:line refs, filed as `plans/active/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md`
  (unified-trading-pm@1db306a86). Corrected the codex incident-gateway wiring claim in
  `codex/05-infrastructure/data-pipeline-alerts.md` (same commit) — DP_\* CRITICAL events were never actually wired
  through the incident gateway, contrary to the diagram; they rely on `AlertDeduplicator` + a per-event cooldown map.
  Live-verified the defi consolidator lock-TTL/livelock fix (shipped by another slot, `unified-trading-library@9358fb0b`
  - `deployment-service@fe67a53`, deployed with `CONSOLIDATOR_LOCK_TTL_SECONDS=4200`) is WORKING: a 24m28s execution
    completed successfully post-fix (no SIGKILL), canonical manifest fresh. Did NOT duplicate that work. Dispatched 4
    parallel sub-agents (SUB_AGENT_MANDATORY_RULES.md + AUTONOMOUS_AGENT_RULES.md injected):
  1. `alerting-service` — implement cadence-aware cooldown fix #1 for `DP_RUN_MOSTLY_EMPTY` (dedup issue doc todo 1).
  2. `deployment-service` — source-side re-nag interval fix #2, defense-in-depth (dedup issue doc todo 2).
  3. `unified-trading-library` + `features-service` — investigate whether the sports 8-9min intermittent slow-run issue
     shares the defi livelock root cause (and fix via Terraform lock-TTL override if so), plus ship bounded
     retry-with-backoff in the features-service startup gate regardless (Option 2 from
     `manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md`).
  4. Research/triage sweep of remaining cefi/tradfi (asset_group, data_type) pairs from the alert batch not yet
     explained — classify tracked-vs-new, file/annotate issue docs. All 4 in flight as this entry is written; will fold
     results in on completion (harness auto-notifies on each).
- 2026-07-15 (agent 1 DONE): alerting-service dedup fix shipped —
  `alerting-service@fe76ded34a46f0cfa880c563fe462c155d50809f`. `_RECURRING_WARN_EVENTS: frozenset[str]` →
  `_RECURRING_ALERT_COOLDOWNS: dict[str, float]`, `DP_RUN_MOSTLY_EMPTY: 1800.0` added. Regression tests added (router +
  data_pipeline_rules), `quality-gates.sh --no-fix` green. Issue doc todo 1 flipped (`unified-trading-pm@0b7654658`).
  Todos 2 (deployment-service) and 3 (docs) left untouched as instructed — todo 3 was already done by the parallel docs
  commit; agent correctly preserved it rather than overwriting.
- 2026-07-15 (agent 4 DONE — cefi/tradfi sweep): classified every remaining alert-batch (asset_group, data_type) pair.
  Most cefi/tradfi partial-ratio cells were already tracked under existing per-venue capture-gap docs. Two genuinely
  new/uncovered findings surfaced and require operator visibility (both flagged, see below) + one new issue doc filed:
  `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` (3 distinct root causes for tradfi
  mbp_10/ohlcv_15m/ohlcv_24h/corporate_action_confirmed/earnings_result stuck ~100% failed — one mechanical
  allowlist-gap fix dispatched separately below, two are architecture/policy decisions left for operator review).
  Commit: `unified-trading-pm@0378027e6`.
- 2026-07-15 (agent 6 DONE — cefi phantom re-query, dispatched after the sweep flagged it as a possible "big finding"):
  **CONFIRMED real, but NOT actively growing.** The 9,757 blank-`data_type` `attempted_failed` cefi rows the alert
  reports are BYTE-IDENTICAL to a 2026-06-28 issue this doc's sibling (`phantom_captures_cefi_2026_06_28.md`) claimed
  fully RESOLVED — live re-query proves that claim was incomplete, not false: all 9,757 rows share one `attempted_at`
  timestamp (2026-06-28T03:12:34Z, an undocumented `reconcile_phantom_manifest_rows_all.py --apply` run), no NEW
  blank-data_type rows have appeared since (rules out an active writer regression), and 99.0% of them have a separate,
  correctly-typed `captured` row for the same (date, venue) — i.e. these are stale orphan manifest rows from a past
  cleanup pass, not missing/at-risk data, and the phantom-audit tool has a real blind spot (any blank-`data_type` row is
  unconditionally flagged phantom). No code fix shipped — remediation needs design (delete orphans vs. harden the audit
  tool) so it was captured as 3 follow-up todos rather than rushed. Issue doc annotated (not overwritten):
  `unified-trading-pm@fe674d7a3`.
- 2026-07-15: dispatched 2 more follow-up agents in parallel: (5) mechanical fix for the tradfi mbp_10 allowlist gap
  (market-tick-data-service, same pattern as the already-fixed KRX/ICE precedents) — in flight; (agent 3 continued)
  resumed the sports/features-service+UTL agent twice after it stalled in a background-wait pattern that doesn't
  actually wake a sub-agent (corrected with explicit foreground-execution instructions) — in flight.
- 2026-07-15 (agent 3 DONE — sports consolidator, after 2 stalls + correction): confirmed the sports 8-9min slow-run
  issue shares the EXACT SAME lock-contention livelock class already fixed for defi. Fixed `deployment-service@69136c2c`
  (Terraform lock-TTL override, live-applied) + defense-in-depth `features-service@5e1ffd2e` (bounded retry). Post-fix
  live-verified: zero stale-lock reclaims across 2+ six-minute cycles (previously guaranteed under the old 300s TTL).
  Issue doc flipped to resolved. Note: this agent's commit (`05942b2f0`) landed interleaved with my own in-flight edit
  to THIS plan file (shared working directory across concurrent agents) — content was NOT lost, both sets of changes are
  present, just under one commit instead of two; noting for the record, not re-litigating (rewriting shared history is
  banned).
- 2026-07-15 (agent 2 DONE — deployment-service re-nag): shipped `deployment-service@0aaab1a22`, a new `RenagTracker`
  module (GCS-persisted `last_alerted_at` per cell, mirrors the existing `MissTracker` pattern) wired into
  `check_high_attempted_failed` + `reconcile_resolved`. 5 new tests, 166 total unit tests pass,
  `quality-gates.sh --no-fix` green (file-size ratchet: `meta_watchers.py` was already at 897/900 lines pre-change,
  lands at 925/900 post-change — consumes the repo's existing `CODEX_MAX_VIOLATIONS=1` tolerance rather than adding a
  NEW one; QG reports it non-blocking. Worth a follow-up extraction pass but not blocking this fix). Both dedup-issue
  layers (alerting-service + deployment-service) now shipped — issue doc fully resolved.
- 2026-07-15: **Big finding — needs operator chat notification** (queued for the next progress report, per the HARD
  RULE, rather than blind-fixed): (1) cefi blank-data_type 9,757-row stale "RESOLVED" claim (confirmed real-but-static
  via live re-query, see above), (2) tradfi cross-service data_type misclassification
  (corporate_action_confirmed/earnings_result expected in the MTDS tick manifest but only ever captured by
  features-service's calendar module — a bucket that structurally can never be satisfied). Both are architecture/policy
  items needing a real decision, not blind-fixed.
