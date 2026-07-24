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
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    plans/active/issues/manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md,
    plans/active/issues/defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md,
    plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    plans/active/issues/tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md,
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

**Codex SSOTs**: `/codex/05-infrastructure/data-pipeline-alerts.md` (failure-mode registry + emit/route/escalate model),
`/codex/05-infrastructure/manifest-consolidator-ssot.md` (consolidator runtime + verification recipe).

> **2026-07-24 — plan line-cap remediation**: the full historical narrative (ground-truth detail, the complete original
> todo list, every Progress Log entry, and every operator-reconciliation / adversarial-verification round through the
> 2026-07-16 close) was extracted verbatim to
> `plans/active/data_pipeline_alerts_batch_remediation_closeout_2026_07_24.md` — see it for the full record. This parent
> now carries only the condensed ground truth, the genuinely-still-open todos, and 2 todos this history shows were
> closed later but never had their checkbox flipped here.

## Ground truth (condensed — see the closeout child for the full version)

- The alert batch mapped to a dense, pre-existing corpus of tracked issue docs (sports/defi consolidator livelocks,
  cefi/tradfi capture gaps) — not a fresh discovery.
- Sports (`manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md`) and defi
  (`defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`) consolidator livelocks were both root-caused + fixed
  this session (Terraform lock-TTL override + a UTL liveness/lock-awareness fix); full chain in the child.
- AO backlog check returned 0 matching dispatched/queued tasks — safe to work locally without AO collision.

## Todos

- [ ] [REVIEW] P2 — PARTIALLY DONE, time-bound limit. A full observation cycle (up to 24h for cefi's cadence) cannot
      complete inside this session — genuinely requires real wall-clock time to pass, not more agent effort. What COULD
      be verified now: the alerting-service + deployment-service dedup fixes are unit-tested to the exact claimed
      behavior (900s-apart collapses, 1801s-apart re-delivers) and both were independently re-derived by the adversarial
      verifier, not just self-reported — high confidence the literal duplicate-spam pattern the operator showed us is
      fixed, even without waiting out a live 24h cefi cycle to watch it directly. Genuinely unverified until real time
      passes: whether a RESOLVED/green bookend actually posts when the sports/tradfi/cefi conditions clear (that
      requires the underlying condition to actually clear first, which is a data-fix problem, not an alerting one).
- [ ] [DOCS] P2. Tradfi mbp_10: correct
      `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` to reflect that the UAC
      registry restriction is a confirmed-still-intentional operator scope decision, not an open gap — and check whether
      the `DP_RUN_MOSTLY_EMPTY` detector/alert for this specific cell should be suppressed/reclassified as expected
      rather than continuing to page as if it's an active problem.
- [x] [DATA] P1. Cefi blank-`data_type` phantom-audit hardening + 9,757-row orphan delete — CLOSED. Tool hardened
      (`instruments-service@dd6b4e826`); the delete survived 2 resurrection reversions before a durable legacy-seed
      exclusion fix (`unified-trading-library@{f14b13ae,8e783d70}`) made it hold across 3 independent production cycles.
      Full evidence: `plans/archive/issues/legacy_seed_captured_outranks_resurrection_risk_2026_07_15.md` (resolved) +
      closeout child § "Fourth round".
- [x] [DATA] P0. Cross-cutting `EXPECTED_*`-prefixed/`attempted_failed` misclassification bug — CLOSED. Data fix
      `market-tick-data-service@92d4fb18b` (34,260 rows reclassified, live-verified 0 remaining) + code fix
      `unified-trading-library@c08a8d61b` (`ManifestWriter.record_failed()` now rejects `EXPECTED_*`-prefixed reasons).
      Full evidence: `plans/archive/issues/tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md`
      (resolved) + closeout child § "🔴 2026-07-15 (later) — independent re-verification pass".
