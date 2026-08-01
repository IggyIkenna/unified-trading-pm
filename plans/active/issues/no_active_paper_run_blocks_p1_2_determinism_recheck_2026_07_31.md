---
doc_type: issue
title:
  "No active paper-trading VM/run exists trading BINANCE-FUTURES/ASTER/OKX-FUTURES — blocks the P1.2 daily-determinism
  recheck in the warm-sink-recovery plan from ever being satisfiable"
summary: >-
  While working `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`'s `[DATA] P1.2` todo (re-run the
  paper(W)==batch-rerun(W) determinism test for BINANCE-FUTURES/ASTER/OKX-FUTURES now that real warm+cold capture is
  confirmed flowing), confirmed live that `DailyDeterminismHandler.run()` needs `cfg.paper_ledger_root` /
  `cfg.batch_ledger_root` set, which in turn needs an ACTIVE paper strategy run trading instruments on these 3 venues.
  `gcloud compute instances list --filter="name~paper OR name~colocated"` returns ZERO results — confirmed independently
  by two workers (slot-14 earlier today, this worker at 2026-07-31T22:03Z) on the live project. Starting/confirming such
  a run is a strategy-desk decision, not a data-pipeline task, so it is out of scope for the warm-sink plan itself and
  needs its own home.
status: open
nature: issue
asset_group: [cefi]
stage: [strategy]
repos: [strategy-service, deployment-service, batch-live-reconciliation-service]
scope: [engineer, admin]
tags: [paper-trading, determinism, live-batch-symmetry, cefi, blocked-operator-decision]
related:
  [
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/active/issues/batch_live_recon_cloud_run_job_stage0_never_succeeded_2026_07_30.md,
  ]
created: "2026-07-31"
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
drift_direction: none
assigned_role: data_engineering
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Found 2026-07-31 while working live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md's [DATA] P1.2 todo
  (slot 8). `gcloud compute instances list --filter="name~paper OR name~colocated"` (read-only), cross-checked against
  the same finding already logged in that plan's Progress Log by slot-14 earlier the same day.
---

# No active paper-trading run for BINANCE-FUTURES/ASTER/OKX-FUTURES

## What I found

`live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`'s `[DATA] P1.2` todo requires re-running the
`paper(W)==batch-rerun(W)` determinism test (`daily-determinism` CLI / `DailyDeterminismHandler` in
`batch-live-reconciliation-service`, per `codex/09-strategy/operational/paper-batch-live-reconciliation.md` §5) for
BINANCE-FUTURES, ASTER, and OKX-FUTURES now that real warm+cold capture is confirmed flowing for these 3 venues (P1.1,
redeployed 2026-07-31T21:14-21:16Z).

`DailyDeterminismHandler.run()` is an honest no-op (`skipped: no_run_configured`) unless `cfg.paper_ledger_root` /
`cfg.batch_ledger_root` are set — which requires an ACTIVE paper strategy run actually trading instruments on these
venues so it produces a ledger to compare. `gcloud compute instances list --filter="name~paper OR name~colocated"`
returns **zero results** on the live project (`central-element-323112`) — checked twice independently the same day: by
slot-14 (per that plan's own Progress Log) and by this worker at `2026-07-31T22:03Z`.

The mechanism itself is proven: `citadel_paper_batch_live_reconciliation_2026_06_19.md` P7.1/P7.2 already ran a real
paper week (2026-06-19→26) and proved ε=0 determinism end-to-end. But that was a bounded historical soak run, not a
standing/continuous paper deployment — there is no evidence any paper run today is actively trading BINANCE-FUTURES,
ASTER, or OKX-FUTURES specifically, so P1.2 has no ledger to diff against no matter how much wall-clock time passes.

## Why it matters

Without either (a) a new paper run started that trades these 3 venues, or (b) confirmation that an existing/different
paper mechanism already covers them under a name this search didn't match, `[DATA] P1.2` is not just time-gated — it is
**permanently unsatisfiable** as currently scoped, regardless of how long the 24h data-accumulation window is allowed to
run. The time-gate and the paper-run gap are two independent blockers; closing this one is necessary before P1.2 can
ever produce a real epsilon=0 citation.

## Recommended decision

This is a strategy-desk judgment call (whether/when to stand up a paper run for these 3 venues, or whether an existing
run already covers them under different instrument routing), not a mechanical data-pipeline fix — hence
`assigned_vm: NA`. Two options, either resolves this:

1. Confirm an existing paper-trading mechanism already routes through BINANCE-FUTURES/ASTER/OKX-FUTURES (read
   strategy-service's instrument-universe config for whichever paper run(s) ARE active, if any exist under a
   non-`paper`/`colocated`-named VM or a non-VM deployment) — if so, P1.2 just needs the correct
   `paper_ledger_root`/`batch_ledger_root` pointed at it.
2. If no such run exists, decide whether to start one for these venues, and if so when — then P1.2's next attempt can
   proceed once both the 24h accumulation window and this run have been live long enough to produce a comparable ledger.

## Todos

- [ ] [DIAG] P2. Determine whether any currently-active paper/strategy deployment (VM-based or otherwise) already trades
      BINANCE-FUTURES, ASTER, or OKX-FUTURES instruments — read strategy-service's active instrument-universe config,
      not just VM naming conventions (a differently-named VM or an in-process/Cloud-Run paper deployment could still
      cover this). Repo: strategy-service.
- [ ] [DECISION] P2. If no such run exists: strategy-desk decision on whether/when to start a paper run trading these 3
      venues so `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`'s P1.2 todo becomes satisfiable.
      `[OPERATOR]` — genuinely outside a worker's mechanical authority.

## Progress Log

- **2026-07-31**: Filed while working the warm-sink-recovery plan's P1.2 todo (slot 8). Read-only investigation
  (`gcloud compute instances list`, no writes). Reconfirms slot-14's same-day finding from that plan's own Progress Log;
  escalated to its own issue doc per that todo's explicit instruction ("confirm a paper run trading these venues exists
  (or escalate that gap as its own finding if not)").

## Progress Log (na-eligibility-audit)

- **na-eligibility-audit 2026-08-01** (tranche=cefi, autonomous): KEEP-NA, valid. `[DECISION]` item is a genuine
  strategy-desk judgment call per the doc's own reasoning (two independent worker confirmations, zero active deployments
  touching these 3 venues). `[DIAG]` item could be split into its own AO-dispatchable audit in principle (flagged for a
  future authoring pass), but its answer only serves the gated DECISION — not splitting it this run. Cross-checked
  parent plan `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md` (lines 170-188): independently and
  currently parks P1.2 citing this exact doc. No reclassification.
