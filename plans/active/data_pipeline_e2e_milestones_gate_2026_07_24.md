---
doc_type: plan
title: Data-pipeline E2E milestones gate — 14 cross-AG correctness criteria for the 5 asset-group consolidated closeouts
summary: >-
  Operator-specified checklist (2026-07-24) of 14 milestones that must hold, symmetrically, across all 5 asset groups
  (tradfi/defi/cefi/prediction/sports) — across every data source, venue, chain, league, fixture, data_type,
  instrument_type, and derived-feature computation — for the data pipeline from instruments-service through
  features-service to be considered genuinely done, not just smoke-test green. A 14-agent parallel research pass
  (2026-07-24) checked each milestone against the live codex SSOTs, the 5 consolidated closeout plans, and (where
  feasible) actual code/CLI state, producing 64 precisely-scoped audit/fix todos below, each tagged with its target
  file. This doc is the tracking/index surface — the actual work happens by distributing each todo into its cited target
  plan (most already exist; a few are new codex docs or a new skill). Companion to
  plan_quality_four_line_defense_architecture_2026_07_23.md (that doc owns PLAN-FORMAT/AO-dispatch-readiness quality;
  this doc owns DATA-PIPELINE-CONTENT correctness) and plan_line_cap_remediation_2026_07_23.md (line-cap hygiene).
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    execution-service,
    unified-api-contracts,
    deployment-api,
    deployment-service,
    strategy-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    data-pipeline,
    e2e,
    milestones,
    canonicalization,
    honest-coverage,
    mvp,
    batch-live-paper,
    plan-quality,
    cross-cutting,
  ]
related:
  [
    /plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/task_template.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 9.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator request 2026-07-24: 14 cross-AG data-pipeline milestones, checked via a 14-agent parallel research workflow
  against codex + the 5 consolidated closeout plans + live code state where feasible.
assigned_role: data_engineering
drift_direction: correct-codex
---

# Data-pipeline E2E milestones gate — 14 cross-AG correctness criteria

> **How to use this doc**: each of the 14 sections below states the milestone, the measured gap (not a guess — every
> claim below cites a real file/line), and a set of todos tagged `target: <file>`. **The actual fix is: open the target
> file and add/apply the todo there** (most targets are the 5 consolidated closeouts or a codex doc) — this gate doc is
> the index, not a duplicate execution surface. `[cross-cutting]`-tagged todos have no single AG target; they create/fix
> a shared codex doc, skill, or corpus-wide sweep.

## 1. Full code E2E canonical — no dead code / fallbacks / duplicate SSOTs (all adapters)

**Gap**: no single codex SSOT bans adapter-level dead code / runtime fallback / duplicate implementations — only 3
partial, non-adapter-specific mechanisms exist (vulture is corpus-wide/advisory and blind to registered-but-never-
scheduled dead code; `check_no_fallback_imports.py` bans only import-time shims, not runtime fallback logic; the UTL/UAC
reuse audit targets service-vs-library duplication, not adapter-vs-adapter). Coverage across the 5 AGs is uneven and
incidental; cefi's own `execution-service` adapters have unaudited parallel `*_ccxt.py`/`*_native.py` pairs per venue
(binance/bybit/okx) whose live-routing status (both used vs. one dead) is unaddressed anywhere.

- [ ] [BACKEND] P2. **target: `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`** — Audit every adapter/handler
      module under `instruments-service/instruments_service/reference_data/adapters/tradfi/`,
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/`, and the tradfi venue files
      in `execution-service/execution_service/trade_execution/adapters/` for duplicate implementations, runtime fallback
      masking a real failure, and dead (referenced-but-never-scheduled) code. Definition-of-done: a filed finding (or a
      stated "clean") per adapter directory, cited with file paths.
- [ ] [BACKEND] P2. **target: `/plans/active/defi_consolidated_closeout_2026_07_18.md`** — Same audit scoped to
      `instruments-service/.../adapters/defi/`, MTDS
      `market_interface/adapters/{defi,defi_live,onchain,onchain_perps}/`, and
      `execution-service/.../adapters/defi_adapter.py`.
- [ ] [BACKEND] P2. **target: `/plans/active/cefi_consolidated_closeout_2026_07_18.md`** — Same audit scoped to
      `instruments-service/.../adapters/cefi/tardis/`, MTDS `.../adapters/cefi/`, and every cefi venue file in
      `execution-service/.../trade_execution/adapters/` — **specifically resolve the `*_ccxt.py`/`*_native.py`
      parallel-file question for binance/bybit/okx** (both live-routed by design, or one dead?).
- [ ] [BACKEND] P2. **target: `/plans/active/prediction_consolidated_closeout_2026_07_18.md`** — Same audit scoped to
      `instruments-service/.../adapters/prediction/` (`kalshi.py`, `polymarket/`) and MTDS `.../adapters/prediction/`.
- [ ] [BACKEND] P2. **target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`** — Same audit scoped to
      `instruments-service/.../adapters/sports/adapters/`, MTDS `.../adapters/sports/`, and
      `execution-service/.../sports_execution/adapters/`.
- [ ] [DOC] P3. **target: `/codex/06-coding-standards/README.md`** — Fix the broken Document Map link ("Forbidden code
      patterns" → `STANDARDS.md`, which does not exist) and author a new codex SSOT stating the no-dead-code /
      no-runtime-fallback / no-duplicate-adapter rule explicitly, cross-linked from `quality-gates.md`.

## 2. Manifest/catalogue/registry canonicalization — Distinct Values census reads 0 everywhere

**Gap**: this is one of the most actively-worked items in the workspace already (live `_distinct_values.py` +
`_axis_census.py` endpoints, an 821-line active cross-cutting audit plan updated today) — the real gaps are narrower:
only sports states a durable "census reads 0" terminal checkpoint; tradfi's own plan doesn't know the census feature
already shipped (stale "re-add it" todo); prediction is silent despite measuring near-0 already; the cross-cutting
audit's ground-truth table is stale relative to today's state.

- [ ] [DATA] P1. **target: `/plans/active/issues/distinct_values_noncanonical_audit_2026_07_20.md`** — Re-run the
      distinct-value census for all 5 asset_groups against the current nightly rollup + manifest, refresh the stale
      2026-07-20 ground-truth table.
- [ ] [REVIEW] P1. **target: `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`** — Replace the stale "re-add
      the dimensions enumeration view" todo — it already shipped live (`GET /distinct-values/{asset_group}`,
      `GET /axis-value-census`) — with a real "run it, verify 0 non-canonical" checkpoint.
- [ ] [REVIEW] P2. **target: `/plans/active/prediction_consolidated_closeout_2026_07_18.md`** — Add a Distinct Values /
      axis-value census section (prediction already measures cleanest of the 5 AGs — just undocumented here).
- [ ] [DATA] P1. **target: `/plans/active/cefi_consolidated_closeout_2026_07_18.md`** Track 6 — Add a terminal
      checkpoint todo: once the Track-1 cutover drain-gate lifts and
      `complete_cefi_manifest_canonical_dedup_2026_07_17.py     --apply` actually runs, re-run the census and require 0
      (or only explicitly-accepted exceptions).
- [ ] [DATA] P1. **target: `/plans/active/defi_consolidated_closeout_2026_07_18.md`** Track 6 — Its "Close-out
      criterion" only requires the distinct-values VIEW to be live (feature-shipped bar, not canonicalization-complete
      bar) — re-run the census against current state and require 0.
- [ ] [REVIEW] P2. **target: `/codex/02-data/reconciliation-finding-taxonomy.md`** — Reconcile the C2a
      instrument_type-casing `migration_pending` suppression scope discrepancy against
      `reconciliation-census-and-compute-tiers.md` §1.5.
- [ ] [REVIEW] P2. **target: new issue doc under `plans/active/issues/`** — Written inventory (no code changes): does an
      equivalent census exist for strategy catalogue, features catalogue, fixtures catalogue, and UAC registries beyond
      the 4 axes `_distinct_values.py`/`_axis_census.py` already cover?

## 3. GCS paths/filenames canonical — migrated non-canonical content ACTUALLY DELETED, not duplicated

**Gap**: the delete protocol (5-part proof, closed disposition vocabulary, human-only hard stops) is solid and followed
where applied — but only ONE AG-scale case (defi `dex_pools`/`lending_indices`) is fully closed
(fold→repoint→delete→re-probe 0). Estate-wide this milestone is genuinely NOT yet true for any other AG; cefi has two
contradictory numbers for the same population in the corpus (a stale "~1.2M orphan objects, delete the whole bucket"
todo vs. a fresh 2026-07-22 measurement of 6).

- [ ] [REVIEW] P1. **target: `/plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`** — Verify (or
      correct) the claim "cefi + sports already done" — sports's own measurement shows 0 of 34,385 `B_legacy_duplicate`
      rows pass the 5-part proof yet.
- [ ] [DATA] P2. **target: `/plans/active/issues/estate_orphan_assessment_2026_07_21.md`** — Check current state of the
      defi orphan-sweep VM (last known: 6th attempt, healthy, 11.75M+ objects swept, no ETA); if finished, record the
      final numbers.
- [ ] [DATA] P2. **target: `/plans/active/issues/estate_orphan_assessment_2026_07_21.md`** — Measure prediction's
      `B_legacy_duplicate` population (never reported anywhere in the corpus; only `E_orphan_real=3,137,183` exists).
- [ ] [DATA] P1. **target: `/plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`** — Run the
      already-named-but-unexecuted next step:
      `cleanup_legacy_twins.py --asset-group tradfi --report-uri     _index/audit/orphan_sweep_tradfi.parquet --dry-run`
      (never `--apply` without explicit operator sign-off — hard stop per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3).
- [ ] [REVIEW] P1. **target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`** — Re-verify the K1/K2
      delete-candidate object list is still the correct target given the casing migration (lowercase→UPPER-case) that
      landed since the list was built.

## 4. VM preemption + attempted_failed billing-waste monitoring — new skill needed

**Gap**: no single codex doc, alert, or skill answers "is a VM currently burning billing on repeated non-retriable
failures?" `DP_RUN_MOSTLY_EMPTY`/`check_high_attempted_failed` is a real alert but is a static cumulative check, not a
"this run, right now" delta. There is no automated gate stopping a future backfill wave from re-attempting a
structurally non-retriable (FAIL-classified) shard — `record_failed()` retries it by default forever absent a human
manually marking it dead.

- [ ] [DOC] P1. **target: new `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md`** — Full
      codex-ssot frontmatter
      (`authoritative_for: [VM preemption + attempted_failed billing-waste monitoring     contract]`). Content:
      summarize the existing PROGRESS-checkpoint preemption-resume contract (`spot-vms-for-backfill.md`), define
      "transient/should-retry" vs. "genuine/should-count-as-failed" via `classify_venue_error()`, state the monitoring
      cadence.
- [ ] [SCRIPT] P1. **target: new skill `cursor-configs/skills/vm-preemption-billing-waste-audit/`** — Trigger
      `/vm-preemption-billing-waste-audit`. Checklist: (1) regular preemption scan both clouds
      (`gcloud compute operations list --filter="operationType=compute.instances.preempted"` + AWS spot-interruption
      equivalent) cross-referenced against auto-recovery evidence; (2) investigate any non-auto-recovered preemption;
      (3) audit `attempted_failed` rows for non-retriable errors that should have been excluded from billing/denominator
      but weren't; (4) verify Slack/data-pipeline alerts actually catch both classes — harden if not.
- [ ] [DOC] P2. **target: 5 existing infra docs** — Cross-reference the new codex doc from `vm-launcher-runbook.md`,
      `spot-vms-for-backfill.md`, `deployment-observability.md`, `data-pipeline-alerts.md`, and CLAUDE.md's VM-launcher
      section (one-line pointer, per the size-budget rule).
- [ ] [SCRIPT] P1. **target: run the new skill** — First live run against both clouds' fleets, 30-day lookback. File
      findings for any launcher missing the preemption-signal contract or any confirmed billing-wasting
      `attempted_failed` cluster.
- [ ] [BACKEND] P2. **target: new cross-cutting design doc** — Design + wire a cross-run pre-flight gate: an
      `action=FAIL` verdict from `classify_venue_error()` (or N consecutive identical-`error_reason` failures across
      waves) routes the shard to a "known-dead, do not re-attempt" manifest-level marker instead of silent infinite
      retry.

## 5. MDPS canonicalization for ALL data types incl. candles, resolution-floor logic

**Gap**: the core mechanism already exists and is authoritative (UAC `NEEDS_CANDLE_PROCESSING` + MDPS
`ohlcv_passthrough.py` — already-canonical candles DO route through MDPS). Narrower real gaps: no cross-AG codex
statement of the "native resolution is the floor, never synthesize finer" invariant; cefi has no standalone
`NEEDS_CANDLE_PROCESSING` catalog doc (codex's own README already flags this); defi's catalog doc doesn't actually
enumerate it despite claiming to.

- [ ] [DATA] P1. **target: `/codex/02-data/mdps-candle-canonical-reconciliation.md`** — New "§ Resolution-floor
      invariant" section stating the cross-AG rule (input resolution is the floor, aggregate coarser only), grounded in
      the existing code-level guard + tradfi's Databento-specific precedent; name each AG's native floor (cefi:
      book_snapshot_5 interval; defi: dex-swap/pool-snapshot cadence; sports: odds_snapshot interval).
- [ ] [DATA] P2. **target: new `/codex/02-data/cefi-data-types-catalog.md`** — Create following the exact table
      structure of `tradfi-data-types-catalog.md`'s NEEDS_CANDLE_PROCESSING section, covering all 6 CeFi data types.
- [ ] [DATA] P2. **target: `/codex/02-data/defi-data-types-catalog.md`** — Audit against the ~24 DeFi entries in UAC's
      `market_data_categories.py` NEEDS_CANDLE_PROCESSING dict (currently mentioned once vs. README's "comprehensive"
      claim).
- [ ] [DATA] P1. **target: `/data-pipeline-check-mdps` skill** — Extend the canonical leg to verify, per MVP
      (asset_group, data_type) shard, that MDPS's actual write behavior matches the declared NEEDS_CANDLE_PROCESSING
      value.

## 6. Parallelization for long-running (multi-hour) VMs

**Gap**: no codex doc states a generic wall-clock threshold triggering a parallelization obligation (nearest analogues
are size-triggered or reactive-to-hangs, not proactive). tradfi/defi both have concrete, already-tracked,
measured-but-unapplied parallelization todos. Sports has zero tracked coverage of this concern at all despite having
both a serial (4-8h) and a parallel (1-2h) launcher available.

- [ ] [DOC] P2. **target: `/codex/05-infrastructure/vm-launcher-runbook.md`** — State the generic rule: any VM run
      expected/observed to exceed a few hours must be cross-machine-sharded and/or intra-machine-parallelized, unless
      I/O-bound against a single shared external resource (the Tardis exception generalized).
- [ ] [DATA] P1. **target: `/plans/active/defi_consolidated_closeout_2026_07_18.md`** — For the DeFi-MVP full-history
      MDPS candle backfill (gated on `candle_canonical_path_migration_execution_2026_07_24.md` reaching P8), confirm
      which launcher is planned: single-VM or the cross-VM sharded one — and whether `max_workers` actually overlaps GCS
      writes (up to ~8x ETA impact suspected, unconfirmed).
- [ ] [DATA] P2. **target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`** — Determine which launcher was
      used for the most recent sports features backfill (serial `launch-features-sports-backfill-vm.sh` vs. parallel
      `launch-features-sports-parallel-backfill-vm.sh`); add a todo requiring the parallel one going forward.
- [ ] [DATA] P3. **target: `/plans/active/cefi_consolidated_closeout_2026_07_18.md`** — Sweep for any non-Tardis cefi VM
      class with multi-hour+ single-VM runtime not already cross-machine-sharded.

## 7. Every issue doc has a clear, bounded todo — even research

**Gap**: sampled 10 issue docs referenced by the 5 closeouts — 8/10 PASS (several with explicit "Gate:"
definition-of-done clauses). 2/10 FAIL: `defi_legacy_precanonical_composite_venue_objects_2026_07-24.md` has NO todos
section at all, only a "Suggested next steps (not started)" list with an undecided judgment call ("Decide
fold-vs-migrate") presented as a step.

- [ ] [DOCS] P2. **target: corpus-wide sweep, `plans/active/issues/`** — Sweep every `status: open` issue doc referenced
      by the 5 closeouts for zero-checkbox docs; classify + fix each genuine gap.
- [ ] [DOCS] P2. **target: 3 named zero-checkbox issue docs** (`pipeline_e2e_check_vm_name_collision_2026_07_12.md` + 2
      others found by the sweep above) — Convert prose deferrals into real, bounded `- [ ] [TAG] Pn.` todos (text-only,
      no re-investigation, no implementation).

## 8. Features service catalogue completeness across all AGs, every adapter smoke-tested

**Gap**: real and current — catalogue completeness is full for exactly 1 of 9 features-service modules (`delta_one`, but
98% un-audited against a 2026-05-28 baseline), partial for 6 (no `status`/`formula_version` field on `BuilderEntry`),
and absent entirely for 3 (`commodity`, `performance_features`, `strategy_pnl_archetype` — no catalogue module at all,
confirmed by directory listing).

- [ ] [DIAG] P2. **target: new issue doc** — Inventory catalogue completeness across all 9 features-service modules:
      does a per-feature declarative registry exist, does it have status/formula_version, per module.
- [ ] [DIAG] P2. **target: new issue doc** — Empirically test whether the family-level smoke check can mask a broken
      individual external-data-source adapter (scope: the ~16 real vendor adapters across commodity/calendar families).
- [ ] [SCRIPT] P3. **target: `/codex/04-architecture/artifact-versioning.md`** — Fix the stale registry-SSOT claim (line
      ~76) that doesn't match onchain's actual `BuilderEntry`-based registry.

## 9. CLI shard-level splits (day, chain, league, fixture, instrument_type) for all AGs/services

**Gap**: the codex 6-tuple + `--shard-key` convention is REAL in exactly one of 4 sampled services
(`market-tick-data-service`, the reference implementation — `decompose_shard_key` has zero hits in instruments-service,
MDPS, or features-service) and ASPIRATIONAL elsewhere. instruments-service's `--operation download` entrypoint has no
`--shard-key`/`--instrument-type`/`--day`/`--root` at all.

- [ ] [BACKEND] P1. **target: new issue doc** — Audit CLI shard-split flag coverage across instruments-service, MDPS,
      and every features-service family CLI against the codex 6-tuple convention; file the gap list per service.
- [ ] [BACKEND] P2. **target: new issue doc** — Enumerate every chain-scoping CLI flag on instruments-service's download
      entrypoint (baseline found: `--gas-fee-chains`, `--evm-defi-chains`, `--lending-chains`, `--risk-params-chains`)
      and confirm features-service's onchain family CLI accepts the same set.
- [ ] [BACKEND] P2. **target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`** — Confirm whether any primary
      entrypoint (not a one-off script) exposes a genuine fixture-level targeting flag; if not, todo to add one.

## 10. Honest-coverage 100% backfill math — empty_confirmed symmetry, 0 attempted_failed after billing-exclusion

**Gap**: part (a) SATISFIED — `all_shards_coverage` already includes `empty_confirmed` in the high-level denominator.
Part (b) — the symmetric-inclusion invariant (numerator XOR denominator is never allowed) is never stated explicitly in
codex, though the 2 SSOT formulas happen to satisfy it by construction; a 3rd, undocumented formula site was found live
in deployment-api. Part (c) — CONFIRMED real gap: no mechanism excludes billing-gated Databento L2/L3 cells from
`attempted_failed`; the current design does the opposite (a billing 4xx propagates straight to failure).

- [ ] [DOC] P2. **target: `/codex/02-data/honest-coverage-model.md`** — Add the explicit symmetric-inclusion invariant
      statement to § "Coverage formula" (~line 216-240).
- [ ] [AUDIT] P2. **target: new issue doc** — Grep every repo (start deployment-api) for coverage-percent computations
      referencing `empty_confirmed`; classify each against the invariant; file any asymmetric violation.
- [ ] [VERIFY] P2. **target:
      `/plans/active/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`** —
      Resolve the open `[VERIFY] P3` todo tracing MTDS's classification path for a billing-guard-hit Databento request.
- [ ] [CODE] P2. **target: `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`** — Wire a durable "billing-gated,
      not a real failure" classification for Databento L2/L3 lookback/entitlement-guard hits so they never count as
      `attempted_failed`.

## 11. Checkpoint cadence — the 5 data-pipeline-check skills + reconciliation, 3x per AG plan

**Gap**: no codex/task_template.md rule requires the 3x pre/mid/post-backfill cadence — real and total documentation
gap. Execution reality varies sharply: `-is`/`-mtds` are checkpointed only for tradfi (2 real runs) and partially
prediction (1 open todo each); **defi has ZERO references to either skill anywhere in its corpus**; cefi has zero real
run-todos for either; sports has zero real run-todos for any of the 4 check skills despite all 4 already supporting
sports's shard atoms.

- [ ] [PM] P2. **target: `/plans/active/task_template.md`** — Add the explicit checkpoint-cadence rule: every AG
      consolidated-closeout plan carries 3 distinct dated RUN checkpoints per data-pipeline-check-{is,mtds,mdps,
      features} + reconciliation (pre-backfill baseline / mid-backfill spot-check / post-backfill final gate).
- [ ] [DATA] P1. **target: `/plans/active/defi_consolidated_closeout_2026_07_18.md`** — Add data-pipeline-check-is and
      -mtds RUN checkpoint todos (currently zero references to either skill anywhere in defi's corpus).
- [ ] [DATA] P1. **target: `/plans/active/cefi_consolidated_closeout_2026_07_18.md`** — Add genuine RUN checkpoint todos
      for -is and -mtds (the one existing -mtds reference is a skill-upgrade todo, not a run).
- [ ] [DATA] P1. **target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`** — Add RUN checkpoint todos for
      all 4 check skills (zero real ones exist today despite all 4 already supporting sports's shard atoms).
- [ ] [DATA] P2. **target: `/plans/active/prediction_consolidated_closeout_2026_07_18.md`** — Top up toward 3x for -is,
      -mtds, and reconciliation (currently 1 open todo each for -is/-mtds, 2 historical reconciliation runs).
- [ ] [DATA] P2. **target: `/plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md`** — Add a post-full-backfill
      reconciliation RUN checkpoint (both raw-tick and candles layers) as the terminal gate's final verification step.

## 12. Cross-linking — verify today's "Aggregated source docs" enrichment is actually complete

**Gap**: largely solid (cefi fully complete). Drift/misses found: tradfi missing 3 today-dated plans (23 open todos
invisible); **defi's biggest single gap** — `defi_track01_per_instrument_and_canon_id_2026_07-24.md` (18 open todos) is
referenced in prose 3 times ("tracked under X below") without X ever actually appearing as a linked entry; prediction's
4 Phase children are in the Split-notice table but not repeated in the Aggregated-source-docs section; sports has one
low-severity miss (a 0-open-todo doc).

- [ ] [DOC] P2. **target: `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`** — Add 3 missing digested entries
      for today-dated tradfi plans a fresh `grep -l '^asset_group:.*tradfi'` finds but the section doesn't link.
- [ ] [DOC] P1. **target: `/plans/active/defi_consolidated_closeout_2026_07_18.md`** — Add the real digested entry for
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md` (18 open todos) — currently a broken forward-reference.
- [ ] [DOC] P2. **target: `/plans/active/prediction_consolidated_closeout_2026_07_18.md`** — Add the 4 Phase A-E
      children to the Aggregated-source-docs section (currently only in the Split-notice table).
- [ ] [DOC] P3. **target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`** — Add
      `data_completion_sports_history_2026_07_24.md` (0 open todos) as a bulleted entry.

## 13. AO-dispatch-readiness — zero contradictions, no open-ended items, crystal-clear for a cold Sonnet-5 worker

**Gap**: NOT uniformly satisfied. Sports is the only one of the 5 with a full self-documented adversarial pass (Track Y,
findings A-G) — and even it has one un-flagged prose-only ordering dependency. tradfi/defi/cefi got only the narrower
2026-07-24 AO-flip-safety audit (checkbox-digest safety + `depends_on` gating) — a real but smaller slice; defi has a
stale/broken cross-todo citation plus a self-contradiction about whether a fix already shipped; cefi has an open-ended
judgment-call todo with no bounded scope. Prediction has had no adversarial pass at all.

- [ ] [DOC] P2. **target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`** — Add a machine-gate caveat to
      Track C's EXCHANGE_ODDS/FIXED_ODDS fork sequence — no machine gate enforces its stated ordering constraints.
- [ ] [DOC] P1. **target: `/plans/active/defi_consolidated_closeout_2026_07_18.md`** — Fix the broken citation in
      "Resume the paused DeFi crons" (lines 673-689) and resolve the self-contradiction about whether the fix shipped.
- [ ] [BACKEND] P2. **target: `/plans/active/cefi_consolidated_closeout_2026_07_18.md`** — Resolve the open-ended
      "decide + remove if..." judgment call at line 234 — violates task_template.md's bounded-outcome rule.
- [ ] [REVIEW] P2. **target: `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`** — Run the same adversarial
      AO-dispatch-readiness pass sports's Track Y ran (bare `§X`, ambiguous verbs, delete-tagging, definition-of-done,
      stale checkboxes, digest-checkbox safety).
- [ ] [REVIEW] P2. **target: `/plans/active/prediction_consolidated_closeout_2026_07_18.md`** — Same adversarial pass
      (prediction has had zero adversarial review to date).

## 14. MVP vs non-MVP data distinction + batch=live=paper wiring symmetry

**Gap**: the epsilon=0 paper=batch-rerun determinism guarantee is real, documented codex SSOT for the tick/candle
event-log tier. Three concrete gaps survive: (1) the "one unified space" claim is proven only for that tier — paper
ledger outputs write to a SEPARATE `runs/{run_id}/ledger/` namespace, not the canonical `by_date/` tree, and no codex
doc says this scoping out loud; (2) "daily block" translation isn't documented verbatim anywhere (the mechanism exists,
split across 2 docs under different names); (3) none of the 5 AG plans' own "MVP universe" sections state which MVP
cells have actually been proven wired through backfill=paper=live, vs. just declared in-scope.

- [ ] [DOC] P1. **target: new cross-cutting investigation** — Code-read (not assumption) whether the paper/live strategy
      universe resolver actually restricts itself to UAC's `MVP_SCOPE` canonical definition.
- [ ] [DATA] P2. **target: `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`** — Extend "## MVP universe" with
      which MVP cells have actually been proven through backfill=paper=live, not just declared in-scope.
- [ ] [DATA] P2. **target: `/plans/active/defi_consolidated_closeout_2026_07_18.md`** — Add an "## MVP universe" section
      (none exists — closest is Track 5) stating which DeFi MVP cells are proven wired.
- [ ] [DATA] P2. **target: `/plans/active/cefi_consolidated_closeout_2026_07_18.md`** — Add an "## MVP universe" section
      (none exists — MVP only in a scattered per-venue list) referencing `/codex/02-data/mvp-scope-canonical.md`.
- [ ] [DATA] P2. **target: `/plans/active/prediction_consolidated_closeout_2026_07_18.md`** — Extend "## MVP universe"
      to cite `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` in its Codex SSOTs list.
- [ ] [DATA] P2. **target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`** — Add an "## MVP universe"
      section (none exists) referencing `/codex/02-data/mvp-scope-canonical.md` § Sports.

## Codex SSOTs

`/codex/02-data/honest-coverage-model.md`, `/codex/02-data/four-surface-reconciliation-procedure.md`,
`/codex/02-data/mdps-candle-canonical-reconciliation.md`, `/codex/05-infrastructure/vm-launcher-runbook.md`,
`/codex/05-infrastructure/gcs-and-manifest-delete-safety-protocol.md`,
`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`,
`/codex/02-data/live-data-persistence-and-event-log.md`, `/codex/06-coding-standards/cli-convention.md`.

## Deferred work after 2026-07-24

| Item                                                          | State       | Blocked on                                                      |
| ------------------------------------------------------------- | ----------- | --------------------------------------------------------------- |
| All 64 todos above distributed into their target files        | Not started | Nobody — mechanical, next session's primary work                |
| Todo #4's new skill + codex doc actually authored             | Not started | Nobody — self-contained, no dependencies                        |
| Todo #4's first live 30-day audit run                         | Not started | The skill existing (prior row)                                  |
| Point 3's tradfi/defi/prediction orphan-sweep re-measurements | Not started | Nobody — some are already-running VMs, just need a status check |
