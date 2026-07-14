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

- [ ] [INFRA] P0. Diagnose (via background agent, in flight) and fix the alert-repeat/no-dedup/no-RESOLVED-green bug so
      `DP_RUN_MOSTLY_EMPTY` (and other CRITICAL DP-\* alerts) stop re-posting byte-identical payloads on every detector
      tick and instead follow fire-on-change / dedup-while-unchanged / explicit RESOLVED-on-fix, mirroring the
      `codex/04-architecture/ci-alerting.md` dedup_key+cooldown model. Repo: alerting-service (+ whichever detector cron
      owns the DP-FETCH-007 post-run manifest scan). File/update the issue doc either way.
- [ ] [CODE] P1. Implement bounded retry-with-backoff in the features-service compute VM startup gate (Option 2 from
      `manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md`) so a transient consolidator-stale
      reading doesn't burn a full SPOT VM launch. Ship + update that issue doc with the fix commit.
- [ ] [INFRA] P1. Investigate root cause of `uts-prod-manifest-consolidator-instruments-sports`'s occasional 8-9min
      executions (Option 1 in the same issue doc) — check for concurrent-execution lock contention given the every-1min
      trigger cadence. Fix if tractable; document if not.
- [ ] [INFRA] P1. Ship the consolidator entrypoint stdout-logging-bootstrap fix (unified-trading-library) so a killed
      defi consolidator execution's actual in-container failure point becomes visible in Cloud Logging, per
      `defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`'s own next-step. Re-observe kill pattern after
      deploy and update that issue doc with whatever the logs reveal.
- [ ] [DATA] P1. For every (asset_group, data_type) pair named in the operator's pasted alert batch, verify: already
      covered by an open/tracked issue doc (annotate with this incident's timestamp as corroborating evidence) vs
      genuinely new (file a fresh `plans/active/issues/<slug>_2026_07_15.md`). Cover: sports (odds_horizon_bucket_\*,
      trades), cefi (trades, derivative_ticker, book_snapshot_5, options_chain, futures_chain, liquidations, blank
      data_type), defi (swaps_ohlcv_\*, dex_pool_state, dex_pool_swaps, gas_fees, oracle_prices, lending_indices,
      lst_rates, risk_params, rewards, blank data_type), tradfi (ohlcv_\*, trades, mbp_10, tbbo,
      corporate_action_confirmed, earnings_result).
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
