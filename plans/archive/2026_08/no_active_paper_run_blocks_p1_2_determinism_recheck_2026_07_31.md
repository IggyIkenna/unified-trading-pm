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
status: resolved
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
    /plans/archive/issues/batch_live_recon_cloud_run_job_stage0_never_succeeded_2026_07_30.md,
  ]
created: "2026-07-31"
author: unknown
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
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
context_scope:
  [
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    batch-live-reconciliation-service/batch_live_reconciliation_service/cli/handlers/daily_determinism_handler.py,
  ]
---

# No active paper-trading run for BINANCE-FUTURES/ASTER/OKX-FUTURES

> **🟢 ARCHIVED 2026-08-09** — all 3 todos complete (DIAG finding: NO active paper deployment covers these venues;
> DECISION: operator ruled "start it, conditionally"; DIAG P1: venue-scoped completeness check ran, verdict NOT CLEAN).
> The still-open follow-on work (backfill/IS completeness gap for BINANCE-FUTURES/ASTER/OKX-FUTURES that blocks the
> paper-run start) is tracked in its own doc, not here:
> `/plans/active/issues/cefi_binance_futures_aster_okx_futures_paper_gate_backfill_incomplete_2026_08_08.md`. Moved to
> `plans/archive/2026_08/` alongside its finalize plan
> (`no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31_finalize_2026_08_08.md`) in the same commit.

## What I found

`live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`'s `[DATA] P1.2` todo requires re-running the
`paper(W)==batch-rerun(W)` determinism test (`daily-determinism` CLI / `DailyDeterminismHandler` in
`batch-live-reconciliation-service`, per `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` §5) for
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

- [x] ✅ [DIAG] P2. Determine whether any currently-active paper/strategy deployment (VM-based or otherwise) already
      trades BINANCE-FUTURES, ASTER, or OKX-FUTURES instruments — read strategy-service's active instrument-universe
      config, not just VM naming conventions (a differently-named VM or an in-process/Cloud-Run paper deployment could
      still cover this). Repo: strategy-service. **Finding (slot 15, 2026-08-07): NO.** The catalog DOES wire all 3
      venues — `catalog_carry.py` `_CARRY_BASIS_PERP_VENUE_BUNDLES` (lines 212-235) and `_FUNDING_DISPERSION_VENUES`
      (lines 395-409) both include BINANCE-FUTURES/OKX-FUTURES/ASTER, and both archetypes are in
      `E2E_UNIVERSE_ARCHETYPES`. However, the only active paper-related Cloud Run job is `paper-signal-engine` (4660
      executions, last ran 2026-08-07T05:15Z) — a signal-processing engine that does NOT call `run_paper()` and does NOT
      write to `client_ledger_root()` (`gs://{client-reports}/ledger/client_id=.../run_id=.../` per
      `unified_trading_library/ledger/run_writer.py:210`). The `paper-trading-engine` (the job that calls `run_paper()`
      and writes the ledger) last ran 2026-06-21 and is currently inactive. Zero GCE paper/colocated VMs (confirmed
      2026-07-31 by two independent workers). `DailyDeterminismHandler` therefore remains `skipped: no_run_configured`.
      P1.2 is permanently unsatisfiable until an active `paper-trading-engine` run is configured. The `[DECISION] P2`
      `[OPERATOR]` item below remains open and correctly `[OPERATOR]`-gated.
- [x] ✅ [DECISION] P2. If no such run exists: strategy-desk decision on whether/when to start a paper run trading these
      3 venues so `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md`'s P1.2 todo becomes satisfiable.
      **RULED (operator, 2026-08-08)**: "Start it to ensure pipes work, but gate on backfill/IS data being complete
      through the strategy layer for these venues first (else missing-data risk). Spin the VM up and down deliberately —
      do not leave it running for days, cost creeps." **Investigated 2026-08-08 (na-corpus-digest-closeout, grep-based
      against manifest/honest-coverage state — no new full-corpus GCS walk)**: backfill/IS completeness is **NOT
      confirmed** for BINANCE-FUTURES/ASTER/OKX-FUTURES — do not start the run yet.
  > - All 3 venues are inside the SAME still-open CeFi coverage gap as
  >   `cefi_ml_directional_continuous_live_2026_06_20.md` item 26 investigated the same day: the only honest-coverage
  >   number on record is a full-history aggregate (44.96% pre-backfill baseline,
  >   `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`), and the backfill meant to close it has
  >   failed/preempted 7 times across 12 days, currently only ~10.7% through its remaining chronological scope
  >   (`last_completed_date=2019-10-21` of `2019-01-01..2026-08-01`) — no fresh, confirmed number exists for any of the
  >   3 venues specifically.
  > - **ASTER specifically** has its own documented completeness history
  >   (`plans/archive/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md`, `status: resolved` for the
  >   specific bugs found there — genesis-clip + provenance — but not a blanket completeness clearance) and **zero MDPS
  >   derived-candle coverage** as of the most recent check (`aster_and_cefi_rolling_adv_feature_2026_07_21.md`: "zero
  >   coverage for the on-chain-perp CeFi venues (ASTER/HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET)... confirmed via a
  >   direct GCS listing"). This is a downstream/derived data type (not raw MTDS ticks, which the strategy layer reads
  >   more directly for funding/carry archetypes), but it is corroborating evidence that ASTER's pipeline has open,
  >   unresolved completeness gaps, not a clean bill of health.
  > - **What IS confirmed**: the `[DIAG]` item above shows the strategy catalog is correctly WIRED for all 3 venues
  >   (`catalog_carry.py`), and CeFi's raw-tick capture Cloud Run Job is currently flowing (Track 1b,
  >   `cefi_consolidated_closeout_2026_07_18.md`, resolved 2026-07-25) — the pipes exist and current ingestion is
  >   healthy. What is NOT confirmed is whether historical backfill/IS completeness for these 3 specific venues is
  >   sufficient to avoid missing-data risk once a paper run starts consuming them through the strategy layer.
  > - **Conclusion**: per the operator's own gating condition, **the paper run stays NOT startable yet.** Filed the
  >   specific blocking prerequisite as a new todo below (a venue-scoped completeness check, narrower and faster than
  >   the stalled full-history backfill). The operator's cost-control instruction (spin the VM up/down deliberately, no
  >   multi-day idle runs) is captured in that same todo for whenever the gate clears.
- [x] ✅ [DIAG] P1. **Blocking prerequisite for the paper-run start decision above**: run a venue-scoped completeness
      check (`instruments-service/scripts/measure_honest_coverage.py --asset-group cefi`, or a targeted IS/MTDS
      spot-check) restricted to **BINANCE-FUTURES, ASTER, OKX-FUTURES** specifically — covering both IS reference-data
      completeness (instrument universe present + non-stale) and recent MTDS tick-capture health (no silent gaps in the
      trailing window a paper run would actually trade against). Repo: instruments-service. **Done when**: a
      venue-scoped completeness verdict for exactly these 3 venues is cited in this doc's Progress Log. If clean: start
      the paper run per the operator's authorization above, launching the VM deliberately (not left running for days —
      spin down once P1.2's ledger comparison has what it needs, per the operator's explicit cost-control instruction).
      If gaps are found: file them as the specific blocking data-completeness issue before starting. — **DONE 2026-08-08
      (slot 33)**: verdict is **NOT CLEAN** — gaps found. Targeted
      `read_availability_index(columns=,     filters=[("venue","in",[...])])` spot-check (live prod cefi manifest,
      3,174,368 rows across the 3 venues, NOT a full-corpus walk) measured reachable-coverage of **53.54%
      (BINANCE-FUTURES)**, **83.60% (ASTER)**, **89.66% (OKX-FUTURES)** — none clear a reasonable bar for a paper run to
      safely consume. Per this todo's own pre-specified branch, filed the blocking data-completeness issue:
      `/plans/active/issues/cefi_binance_futures_aster_okx_futures_paper_gate_backfill_incomplete_2026_08_08.md`. The
      paper VM was **NOT** started — the gate stays closed pending an operator/data-pipeline decision on backfill
      priority for these 3 venues (tracked in that new issue doc, not duplicated here).

## Progress Log

- **2026-07-31**: Filed while working the warm-sink-recovery plan's P1.2 todo (slot 8). Read-only investigation
  (`gcloud compute instances list`, no writes). Reconfirms slot-14's same-day finding from that plan's own Progress Log;
  escalated to its own issue doc per that todo's explicit instruction ("confirm a paper run trading these venues exists
  (or escalate that gap as its own finding if not)").
- **2026-08-08 (slot 33, `no_active_paper_run_blocks_p1_2_determinism_recheck-001`)**: Ran the `[DIAG] P1` venue-scoped
  completeness check. Verdict: **NOT CLEAN**. Reachable-coverage — BINANCE-FUTURES 53.54%, ASTER 83.60%, OKX-FUTURES
  89.66% (targeted `read_availability_index(columns=, filters=[("venue","in",[...])])` read against the live prod cefi
  manifest — 3,174,368 rows, not a full-corpus walk; the unfiltered `measure_honest_coverage.py --asset-group cefi`
  full-manifest read was attempted first but was externally killed on the shared host, so switched to the lighter
  targeted alternative the todo itself offered). Filed the blocking data-completeness issue per the todo's own
  pre-specified branch:
  `/plans/active/issues/cefi_binance_futures_aster_okx_futures_paper_gate_backfill_incomplete_2026_08_08.md`. Paper VM
  NOT started — gate stays closed.

## Progress Log (na-eligibility-audit)

- **na-eligibility-audit 2026-08-01** (tranche=cefi, autonomous): KEEP-NA, valid. `[DECISION]` item is a genuine
  strategy-desk judgment call per the doc's own reasoning (two independent worker confirmations, zero active deployments
  touching these 3 venues). `[DIAG]` item could be split into its own AO-dispatchable audit in principle (flagged for a
  future authoring pass), but its answer only serves the gated DECISION — not splitting it this run. Cross-checked
  parent plan `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md` (lines 170-188): independently and
  currently parks P1.2 citing this exact doc. No reclassification.
- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-08-01 verdict; the
  gating strategy-desk judgment call (whether/when to start a paper run) still holds, so the companion bounded [DIAG]
  audit item stays whole-doc-NA (it only serves the gated decision).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-08-01 verdict; the
  gating `[OPERATOR]` strategy-desk call (whether/when to start a paper run) still holds, so the companion `[DIAG]` item
  stays whole-doc-NA (it only serves the gated decision). The `[DIAG]` item was independently drafted into
  `cefi_satellite_ao_dispatch_batch7_2026_08_03.md` (still draft).
- **2026-08-07** (slot 15 · `cefi_satellite_ao_dispatch_batch7-002`): `[DIAG] P2` CLOSED — **finding: NO.** Strategy
  catalog includes all 3 venues in `CARRY_BASIS_PERP` + `CARRY_FUNDING_DISPERSION` (both E2E archetypes,
  `catalog_carry.py` lines 212-235 / 395-409), but the only active Cloud Run paper job is `paper-signal-engine`
  (signal-only, no `run_paper()`/ledger write; 4660 executions, last ran 2026-08-07T05:15Z). `paper-trading-engine`
  (ledger writer) inactive since 2026-06-21; zero GCE paper VMs. P1.2 ledger-pointer update NOT triggered (NO finding).
  `[DECISION] P2` `[OPERATOR]` item unchanged and remains open.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — the [DIAG] item was closed today by a concurrent session; the
  sole remaining [DECISION] P2 [OPERATOR] item stays open, unchanged.
- **na-corpus-digest-closeout 2026-08-08**: operator ruled "start it, gated on backfill/IS completeness for these 3
  venues, and spin the VM up/down deliberately (cost control)." Investigated: no venue-scoped completeness measurement
  exists for BINANCE-FUTURES/ASTER/OKX-FUTURES — only the same full-history CeFi aggregate (44.96%, stalled backfill)
  already found incomplete while investigating a sibling item (`cefi_ml_directional_continuous_live_2026_06_20.md`'s
  item 26, same session) plus ASTER's own documented completeness history. Completeness is therefore **not confirmed** —
  the paper run stays NOT startable yet. Closed the `[DECISION]` todo (the decision itself — start it, conditionally —
  is now made) and filed a new `[DIAG] P1` blocking-prerequisite todo for the venue-scoped check that would actually
  clear the gate, carrying the operator's cost-control instruction forward for whenever it does.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: RECLASSIFY → `assigned_vm: planning`. The doc's own
  `[OPERATOR]`-gated `[DECISION]` judgment call is CLOSED (na-corpus-digest-closeout 2026-08-08, ruled "start it,
  conditionally" — the direction is decided, only the mechanical gate remains). The sole remaining open item
  (`[DIAG] P1`) is bounded and worker-determinable: run `measure_honest_coverage.py --asset-group cefi` (or a targeted
  IS/MTDS spot-check) scoped to exactly 3 named venues, cite the verdict, then branch on a pre-specified rule — clean →
  launch the paper VM (self-terminating, deliberately spun down per the operator's own explicit cost-control
  instruction, the same idempotent smoke-test-class VM launch already routinely AO-dispatched — satisfies the
  safe-idempotent justification without an `[OPERATOR]` tag); gaps found → file them as a new blocking data-completeness
  issue (a determinable, not a judgment, branch). Conflict-check: no `assigned_vm: planning` doc under
  `parent_epic: batch_live_symmetry_master` exists; `cefi_consolidated_closeout_2026_07_18.md` does not reference this
  doc or BINANCE-FUTURES/ASTER/OKX-FUTURES paper-run completeness. `cefi_satellite_ao_dispatch_batch10_2026_08_08.md`'s
  "Deferred — operator-gated" listing for this doc predates the same-day na-corpus-digest-closeout entries that closed
  the `[DECISION]` item and filed the new bounded `[DIAG]` item — superseded, not a live conflict. Estimate re-tiered
  `research`→`infra` (a completeness measurement + a conditionally-launched, self-terminating VM). Companion finalize
  plan: `/plans/active/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31_finalize_2026_08_08.md`.
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
