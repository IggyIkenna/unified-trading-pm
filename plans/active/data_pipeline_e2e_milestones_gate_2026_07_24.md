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
  **Standing reference surface, not an archival candidate** (resolved
  `autonomous_session_operator_decisions_2026_07_25.md` entry #10, 2026-07-26, option A) — 0 open todos is expected here
  even when fully "done": this doc's own todos read `✅ DONE — target: <file>`, meaning distributed, not shipped, and it
  is the cited reference surface for `/plan-reconcile`'s hunter 6 ("for each AG closeout, confirm every todo tagged for
  it has actually landed there"), an ongoing duty. Keep `status: active` in `plans/active/`.
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
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
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
archive_exempt: true # standing reference surface by operator ruling — 0 open todos is expected here, re-confirmed by na-eligibility-audit 2026-08-02
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
context_scope:
  [
    /plans/archive/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /plans/active/task_template.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# Data-pipeline E2E milestones gate — 14 cross-AG correctness criteria

> **How to use this doc**: each of the 14 sections below states the milestone, the measured gap (not a guess — every
> claim below cites a real file/line), and a set of todos tagged `target: <file>`. **The actual fix is: open the target
> file and add/apply the todo there** (most targets are the 5 consolidated closeouts or a codex doc) — this gate doc is
> the index, not a duplicate execution surface. `[cross-cutting]`-tagged todos have no single AG target; they create/fix
> a shared codex doc, skill, or corpus-wide sweep.
>
> **Evidence note (2026-07-24 distribution pass)**: every `pm@<commit-pending>` citation below resolved on push to
> either `pm@4f81d0139` (the 8 direct-authorable items) or `pm@37e74aaf0` (the remaining 56, incl. all 5 AG-agent
> batches + new issue/codex docs) — both on `origin/live-defi-rollout`. Run `git log --oneline -- <target-file>` on the
> cited target for the exact commit if the distinction matters.

## 1. Full code E2E canonical — no dead code / fallbacks / duplicate SSOTs (all adapters)

**Gap**: no single codex SSOT bans adapter-level dead code / runtime fallback / duplicate implementations — only 3
partial, non-adapter-specific mechanisms exist (vulture is corpus-wide/advisory and blind to registered-but-never-
scheduled dead code; `check_no_fallback_imports.py` bans only import-time shims, not runtime fallback logic; the UTL/UAC
reuse audit targets service-vs-library duplication, not adapter-vs-adapter). Coverage across the 5 AGs is uneven and
incidental; cefi's own `execution-service` adapters have unaudited parallel `*_ccxt.py`/`*_native.py` pairs per venue
(binance/bybit/okx) whose live-routing status (both used vs. one dead) is unaddressed anywhere.

- [x] [BACKEND] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`. Added
      as a bounded dispatchable audit todo (Track A2), citing the new adapter-dead-code-and-fallback-ban SSOT.
      `pm@<commit-pending>`.
- [x] [BACKEND] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/defi_consolidated_closeout_2026_07_18.md`. Added as
      a bounded dispatchable audit todo. `pm@<commit-pending>`.
- [x] [BACKEND] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/cefi_consolidated_closeout_2026_07_18.md`. Added as
      a bounded dispatchable audit todo (Track 5), including the ccxt/native binance/bybit/okx question.
      `pm@<commit-pending>`.
- [x] [BACKEND] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/prediction_consolidated_closeout_2026_07_18.md`.
      Added as a bounded dispatchable audit todo. `pm@<commit-pending>`.
- [x] [BACKEND] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`. Added
      as a bounded dispatchable audit todo (Track X/CLEANUP). `pm@<commit-pending>`.
- [x] [DOC] P3. ✅ **DONE 2026-07-24** — target: `/codex/06-coding-standards/README.md`. Fixed the broken Document Map
      link (repointed to the new doc below) and authored
      `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md` (new codex-ssot) stating the no-dead-code /
      no-runtime-fallback / no-duplicate-adapter rule explicitly, cross-linked from `quality-gates.md`'s vulture
      section. `pm@<commit-pending>`.

## 2. Manifest/catalogue/registry canonicalization — Distinct Values census reads 0 everywhere

**Gap**: this is one of the most actively-worked items in the workspace already (live `_distinct_values.py` +
`_axis_census.py` endpoints, an 821-line active cross-cutting audit plan updated today) — the real gaps are narrower:
only sports states a durable "census reads 0" terminal checkpoint; tradfi's own plan doesn't know the census feature
already shipped (stale "re-add it" todo); prediction is silent despite measuring near-0 already; the cross-cutting
audit's ground-truth table is stale relative to today's state.

- [x] [DATA] P1. ✅ **DONE 2026-07-24** — target:
      `/plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md` (corrected path — it lives directly
      under `plans/active/`, not `plans/active/issues/`). Added a dispatchable todo to re-run the census and refresh the
      stale ground-truth table (the live measurement itself needs a real script run, not performed in this distribution
      pass). `pm@<commit-pending>`.
- [x] [REVIEW] P1. ✅ **DONE 2026-07-24** — target: `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`. Replaced
      the stale "re-add the dimensions enumeration view" todo with a real "run it, verify 0 non-canonical" checkpoint
      (Phase C). `pm@<commit-pending>`.
- [x] [REVIEW] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/prediction_consolidated_closeout_2026_07_18.md`.
      Added a Distinct Values/axis-value census section. `pm@<commit-pending>`.
- [x] [DATA] P1. ✅ **DONE 2026-07-24** — target: `/plans/active/cefi_consolidated_closeout_2026_07_18.md` Track 6.
      Added the terminal checkpoint todo gated on the Track-1 drain-gate + `--apply` run. `pm@<commit-pending>`.
- [x] [DATA] P1. ✅ **DONE 2026-07-24** — target: `/plans/active/defi_consolidated_closeout_2026_07_18.md` Track 6.
      Rewrote the close-out criterion in place to require a fresh census re-run returning 0, not just the view being
      live. `pm@<commit-pending>`.
- [x] [REVIEW] P2. ✅ **DONE 2026-07-24** — target: `/codex/02-data/reconciliation-finding-taxonomy.md`. Reconciled the
      C2a instrument_type-casing `migration_pending` suppression scope discrepancy: code-read
      `deployment-api/deployment_api/routes/data_status/_distinct_values.py::_comparison_set()` confirmed defi's
      instrument_type casing is a SEPARATE, permanent, already-settled rule (canonical LOWERCASE, folded always) — NOT
      part of the same migration_pending population as cefi/tradfi's D1 UPPERCASE-target ruling. Added a scope
      correction to taxonomy.md §5.1. `pm@<commit-pending>`. > **⚠️ 2026-07-25 correction**: the framing above
      (permanent, out-of-scope, folded-always LOWERCASE) was itself > superseded ~20 min after that same commit
      (`4f81d0139`, 19:11:01 UTC) by the operator's own directive commit > (`adb28421d`, 19:31:37 UTC), which put defi
      back in scope for a narrower **per-value least-migration-cost** > convergence rule — a different rule that happens
      to produce the same LOWERCASE outcome today. See >
      `/plans/archive/2026_08/cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md` (§ "Open todo", DONE >
      2026-07-24) for the authoritative framing and the correction banners already added to >
      `reconciliation-finding-taxonomy.md`, `canonical-cutover-register.md`, and `cross-asset-canonical-target-ssot.md`.
- [x] [REVIEW] P2. ✅ **DONE 2026-07-24** — target: new issue doc under `plans/active/issues/`. Created
      `catalogue_census_equivalents_inventory_2026_07_24.md` with the bounded inventory todo (the investigation itself
      is future dispatch work). `pm@<commit-pending>`.

## 3. GCS paths/filenames canonical — migrated non-canonical content ACTUALLY DELETED, not duplicated

**Gap**: the delete protocol (5-part proof, closed disposition vocabulary, human-only hard stops) is solid and followed
where applied — but only ONE AG-scale case (defi `dex_pools`/`lending_indices`) is fully closed
(fold→repoint→delete→re-probe 0). Estate-wide this milestone is genuinely NOT yet true for any other AG; cefi has two
contradictory numbers for the same population in the corpus (a stale "~1.2M orphan objects, delete the whole bucket"
todo vs. a fresh 2026-07-22 measurement of 6).

- [x] [REVIEW] P1. ✅ **DONE 2026-07-24** — target:
      `/plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`. Added a todo to verify/correct the
      "cefi + sports already done" claim, citing the 0-of-34,385 gap. `pm@<commit-pending>`.
- [x] [DATA] P2. ✅ **ALREADY SATISFIED (found 2026-07-24, no new todo needed)** — target:
      `/plans/active/issues/estate_orphan_assessment_2026_07_21.md`. A concurrent session's own extensive Progress Log
      updates (session 3-4) already carry the defi orphan-sweep VM far past this ask: sweep COMPLETED (15,865,384
      orphan_class_E, 2026-07-23), dry-run COMPLETED (real remaining population 637,738 rows after re-verify), and
      `--apply` LAUNCHED 2026-07-24 19:06 UTC. Per task_template.md finding C (don't duplicate a todo the doc's own
      later section already answers), no new checkbox added — the doc's own history is the record.
- [x] [DATA] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/issues/estate_orphan_assessment_2026_07_21.md`. Added
      todo 8: measure prediction's `B_legacy_duplicate` population from the already-durable sweep report (genuinely not
      yet measured anywhere in the corpus). `pm@<commit-pending>`.
- [x] [DATA] P1. ✅ **DONE 2026-07-24** — target:
      `/plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`. Added a dispatchable todo for the dry-run
      step (never `--apply` without explicit operator sign-off — hard stop per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3). `pm@<commit-pending>`.
- [x] [REVIEW] P1. ✅ **DONE 2026-07-24** — target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`. Added
      the K1/K2 re-verify todo in Track C, next to the existing casing-migration revert todo. `pm@<commit-pending>`.

## 4. VM preemption + attempted_failed billing-waste monitoring — new skill needed

**Gap**: no single codex doc, alert, or skill answers "is a VM currently burning billing on repeated non-retriable
failures?" `DP_RUN_MOSTLY_EMPTY`/`check_high_attempted_failed` is a real alert but is a static cumulative check, not a
"this run, right now" delta. There is no automated gate stopping a future backfill wave from re-attempting a
structurally non-retriable (FAIL-classified) shard — `record_failed()` retries it by default forever absent a human
manually marking it dead.

- [x] [DOC] P1. ✅ **ALREADY DONE (prior session, verified 2026-07-24)** — target:
      `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md`. Confirmed present with full codex-ssot
      frontmatter (`authoritative_for: [VM preemption + attempted_failed billing-waste monitoring contract]`) and all
      the specified content (PROGRESS-checkpoint summary, transient-vs-genuine classification via
      `classify_venue_error()`, monitoring cadence).
- [x] [SCRIPT] P1. ✅ **ALREADY DONE (prior session, verified 2026-07-24)** — target: new skill
      `cursor-configs/skills/vm-preemption-billing-waste-audit/`. Confirmed present (`SKILL.md`) with the full 4-part
      checklist matching this todo's spec.
- [x] [DOC] P2. ✅ **DONE 2026-07-24** — target: 5 existing infra docs. 4 of 5 already had the cross-reference
      (`spot-vms-for-backfill.md`, `deployment-observability.md`, `data-pipeline-alerts.md` via `related:` frontmatter;
      CLAUDE.md's VM-launcher section already names the skill). Added the missing 5th to `vm-launcher-runbook.md`'s
      References section. `pm@<commit-pending>`.
- [x] [SCRIPT] P1. ✅ **DONE 2026-07-24 (tracked, not yet run)** — target: run the new skill. Added a dispatchable todo
      in the new `plans/archive/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md` — the
      actual live run against both clouds' fleets is execution work for a future dispatch, not this distribution pass.
      `pm@<commit-pending>`.
- [x] [BACKEND] P2. ✅ **DONE 2026-07-24 (tracked, not yet designed)** — target: new cross-cutting design doc. Same new
      issue doc as above carries the pre-flight-gate design todo. `pm@<commit-pending>`.

## 5. MDPS canonicalization for ALL data types incl. candles, resolution-floor logic

**Gap**: the core mechanism already exists and is authoritative (UAC `NEEDS_CANDLE_PROCESSING` + MDPS
`ohlcv_passthrough.py` — already-canonical candles DO route through MDPS). Narrower real gaps: no cross-AG codex
statement of the "native resolution is the floor, never synthesize finer" invariant; cefi has no standalone
`NEEDS_CANDLE_PROCESSING` catalog doc (codex's own README already flags this); defi's catalog doc doesn't actually
enumerate it despite claiming to.

- [x] [DATA] P1. ✅ **DONE 2026-07-24** — target: `/codex/02-data/mdps-candle-canonical-reconciliation.md`. Added new
      "§1a Resolution-floor invariant" section stating the cross-AG rule + a per-AG native-floor table (tradfi:
      Databento-native tick/MBP; cefi: `book_snapshot_5`; defi: dex-swap/pool-snapshot cadence; prediction: native tick
      cadence; sports: `odds_snapshot` interval). `pm@<commit-pending>`.
- [x] [DATA] P2. ✅ **DONE 2026-07-24 (stub + todo, not the full audit)** — target: new
      `/codex/02-data/cefi-data-types-catalog.md`. Created following `tradfi-data-types-catalog.md`'s exact table
      structure, with a `_TBD_`-marked placeholder table + a bounded todo to fill in the real values against UAC's live
      dict (that live lookup needs tool access this distribution pass didn't have — genuine investigation, not
      formatting). `pm@<commit-pending>`.
- [x] [DATA] P2. ✅ **DONE 2026-07-24 (gap flagged + todo added, not the full audit)** — target:
      `/codex/02-data/defi-data-types-catalog.md`. Added a banner flagging the README's stale "comprehensive" claim
      (only 1 of ~24 DeFi data_types has a documented NEEDS_CANDLE_PROCESSING value) + a todo to audit the rest against
      UAC's live dict. `pm@<commit-pending>`.
- [x] [DATA] P1. ✅ **DONE 2026-07-24 (gap documented, not implemented)** — target: `/data-pipeline-check-mdps` skill.
      Added a "Known gap" note under §3a (Canonical-paths principle) describing the needed extension — a real code
      change to `pipeline_e2e_check.py`'s canonical-leg verifier, out of scope for this doc-distribution pass.
      `pm@<commit-pending>`.

## 6. Parallelization for long-running (multi-hour) VMs

**Gap**: no codex doc states a generic wall-clock threshold triggering a parallelization obligation (nearest analogues
are size-triggered or reactive-to-hangs, not proactive). tradfi/defi both have concrete, already-tracked,
measured-but-unapplied parallelization todos. Sports has zero tracked coverage of this concern at all despite having
both a serial (4-8h) and a parallel (1-2h) launcher available.

- [x] [DOC] P2. ✅ **DONE 2026-07-24** — target: `/codex/05-infrastructure/vm-launcher-runbook.md`. Added new "§
      Parallelization Threshold for Long-Running VMs" section stating the generic rule (any VM run expected/observed to
      exceed a few hours must be cross-machine-sharded and/or intra-machine-parallelized, unless I/O-bound against a
      single shared external resource — the Tardis exception generalized). `pm@<commit-pending>`.
- [x] [DATA] P1. ✅ **DONE 2026-07-24** — target: `/plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md` (Track
      5 was forked out of `defi_consolidated_closeout_2026_07_18.md` earlier 2026-07-24; this is where the content
      actually landed — see gate-audit §6 there). Added the launcher-confirmation todo, gated on
      `candle_canonical_path_migration_execution_2026_07_24.md` reaching P8. `pm@<commit-pending>`.
- [x] [DATA] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`. Added the
      launcher-determination todo naming both the serial and parallel launchers. `pm@<commit-pending>`.
- [x] [DATA] P3. ✅ **DONE 2026-07-24** — target: `/plans/active/cefi_consolidated_closeout_2026_07_18.md`. Added the
      non-Tardis multi-hour VM sweep todo, exempting Tardis VMs per the codex cap. `pm@<commit-pending>`.

## 7. Every issue doc has a clear, bounded todo — even research

**Gap**: sampled 10 issue docs referenced by the 5 closeouts — 8/10 PASS (several with explicit "Gate:"
definition-of-done clauses). 2/10 FAIL: `defi_legacy_precanonical_composite_venue_objects_2026_07-24.md` has NO todos
section at all, only a "Suggested next steps (not started)" list with an undecided judgment call ("Decide
fold-vs-migrate") presented as a step.

- [x] [DOCS] P2. ✅ **DONE 2026-07-24 (both known instances fixed; full corpus sweep tracked as a todo)** — target:
      corpus-wide sweep, `plans/active/issues/`. Created
      `plans/archive/issues/issue_docs_zero_checkbox_sweep_2026_07_24.md` tracking this; the remaining full-corpus sweep
      (beyond the original 10-doc sample) is its own dispatchable todo there. `pm@<commit-pending>`.
- [x] [DOCS] P2. ✅ **DONE 2026-07-24** — target: 3 named zero-checkbox issue docs. Both known instances converted:
      `pipeline_e2e_check_vm_name_collision_2026_07_12.md` (real `[CODE] P2` todo added) and
      `defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` (archived 2026-08-08, delete complete; 4 real
      todos, splitting the undecided fold-vs-migrate judgment call into fact-gathering + a separate `[OPERATOR]`
      decision todo). The gate doc's own citation had a typo (`2026_07-24` → corrected to `2026_07_24`).
      `pm@<commit-pending>`.

## 8. Features service catalogue completeness across all AGs, every adapter smoke-tested

**Gap**: real and current — catalogue completeness is full for exactly 1 of 9 features-service modules (`delta_one`, but
98% un-audited against a 2026-05-28 baseline), partial for 6 (no `status`/`formula_version` field on `BuilderEntry`),
and absent entirely for 3 (`commodity`, `performance_features`, `strategy_pnl_archetype` — no catalogue module at all,
confirmed by directory listing).

- [x] [DIAG] P2. ✅ **DONE 2026-07-24 (both tracked in one new doc)** — target: new issue doc. Created
      `plans/active/issues/features_service_catalogue_completeness_inventory_2026_07_24.md` with both the
      catalogue-completeness inventory and the smoke-check-masking test as bounded todos. `pm@<commit-pending>`.
- [x] [DIAG] P2. ✅ **DONE 2026-07-24** — same new doc as above (see previous item).
- [x] [SCRIPT] P3. ✅ **DONE 2026-07-24** — target: `/codex/04-architecture/artifact-versioning.md`. Fixed the stale
      registry-SSOT claim — the "Feature groups" row now states the registry is PER-FAMILY (delta_one's `registry.py`
      vs. onchain's own `BUILDER_REGISTRY`/`BuilderEntry` in `feature_builder_registry.py`), not a single shared file.
      `pm@<commit-pending>`.

## 9. CLI shard-level splits (day, chain, league, fixture, instrument_type) for all AGs/services

**Gap**: the codex 6-tuple + `--shard-key` convention is REAL in exactly one of 4 sampled services
(`market-tick-data-service`, the reference implementation — `decompose_shard_key` has zero hits in instruments-service,
MDPS, or features-service) and ASPIRATIONAL elsewhere. instruments-service's `--operation download` entrypoint has no
`--shard-key`/`--instrument-type`/`--day`/`--root` at all.

- [x] [BACKEND] P1. ✅ **DONE 2026-07-24 (both tracked in one new doc)** — target: new issue doc. Created
      `/plans/archive/issues/cli_shard_split_flag_coverage_audit_2026_07_24.md` (archived 2026-07-28, all 4 todos done)
      with both the 6-tuple audit and the chain-scoping-flag enumeration as bounded todos. `pm@<commit-pending>`.
- [x] [BACKEND] P2. ✅ **DONE 2026-07-24** — same new doc as above (see previous item).
- [x] [BACKEND] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`. Added
      the fixture-level-targeting-flag confirmation todo. `pm@<commit-pending>`.

## 10. Honest-coverage 100% backfill math — empty_confirmed symmetry, 0 attempted_failed after billing-exclusion

**Gap**: part (a) SATISFIED — `all_shards_coverage` already includes `empty_confirmed` in the high-level denominator.
Part (b) — the symmetric-inclusion invariant (numerator XOR denominator is never allowed) is never stated explicitly in
codex, though the 2 SSOT formulas happen to satisfy it by construction; a 3rd, undocumented formula site was found live
in deployment-api. Part (c) — CONFIRMED real gap: no mechanism excludes billing-gated Databento L2/L3 cells from
`attempted_failed`; the current design does the opposite (a billing 4xx propagates straight to failure).

- [x] [DOC] P2. ✅ **DONE 2026-07-24** — target: `/codex/02-data/honest-coverage-model.md`. Added the explicit
      symmetric-inclusion invariant statement to § "Coverage formula". `pm@<commit-pending>`.
- [x] [AUDIT] P2. ✅ **DONE 2026-07-24** — target: new issue doc. Created
      `plans/archive/issues/coverage_percent_symmetric_inclusion_audit_2026_07_24.md` with the bounded grep+classify
      todo. `pm@<commit-pending>`.
- [x] [VERIFY] P2. ✅ **CHECKED 2026-07-24 — already correctly homed, no distribution action needed.** target:
      `/plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`.
      The cited `- [ ] [VERIFY] P3.` todo (tracing how a `_DATABENTO_SUPPORTED_DATA_TYPES`-filtered-out data_type gets
      recorded — `attempted_failed` vs. `empty_confirmed`) already exists in that file, already correctly formatted per
      task_template.md (tagged, scoped, states what closing it requires). This gate-doc item asked to actually RESOLVE
      the trace, not just place a todo — that's a genuine code investigation across `market-tick-data-service`'s
      orchestrator/sentinel layer, out of scope for this mechanical-distribution pass; left open for a future dispatched
      worker with full tool access.
- [x] [CODE] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`. Added the
      billing-gated-classification todo to Phase C, next to the existing honest-coverage bullet. `pm@<commit-pending>`.

## 11. Checkpoint cadence — the 5 data-pipeline-check skills + reconciliation, 3x per AG plan

**Gap**: no codex/task_template.md rule requires the 3x pre/mid/post-backfill cadence — real and total documentation
gap. Execution reality varies sharply: `-is`/`-mtds` are checkpointed only for tradfi (2 real runs) and partially
prediction (1 open todo each); **defi has ZERO references to either skill anywhere in its corpus**; cefi has zero real
run-todos for either; sports has zero real run-todos for any of the 4 check skills despite all 4 already supporting
sports's shard atoms.

- [x] [PM] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/task_template.md`. Added finding K (new §3 bullet)
      stating the explicit checkpoint-cadence rule. `pm@<commit-pending>`.
- [x] [DATA] P1. ✅ **DONE 2026-07-24** — target: `/plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md` (Track
      5 was forked out of `defi_consolidated_closeout_2026_07_18.md` earlier 2026-07-24; this is where the content
      actually landed — see gate-audit §11 there). Added one combined `data-pipeline-check-is`/`-mtds`
      checkpoint-cadence todo. `pm@<commit-pending>`.
- [x] [DATA] P1. ✅ **DONE 2026-07-24** — target: `/plans/active/cefi_consolidated_closeout_2026_07_18.md`. Added a new
      "Checkpoint cadence" subsection with 6 genuine RUN todos (3x each for -is/-mtds). `pm@<commit-pending>`.
- [x] [DATA] P1. ✅ **DONE 2026-07-24** — target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`. Added one
      combined RUN-checkpoint todo naming all 4 check skills. `pm@<commit-pending>`.
- [x] [DATA] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/prediction_consolidated_closeout_2026_07_18.md`. Added
      3 topping-up checkpoint todos for -is/-mtds/reconciliation. `pm@<commit-pending>`.
- [x] [DATA] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md`. Added a
      post-full-backfill reconciliation RUN checkpoint todo (both raw-tick and candles layers) as the terminal gate's
      final verification step. `pm@<commit-pending>`.

## 12. Cross-linking — verify today's "Aggregated source docs" enrichment is actually complete

**Gap**: largely solid (cefi fully complete). Drift/misses found: tradfi missing 3 today-dated plans (23 open todos
invisible); **defi's biggest single gap** — `defi_track01_per_instrument_and_canon_id_2026_07-24.md` (18 open todos) is
referenced in prose 3 times ("tracked under X below") without X ever actually appearing as a linked entry; prediction's
4 Phase children are in the Split-notice table but not repeated in the Aggregated-source-docs section; sports has one
low-severity miss (a 0-open-todo doc).

- [x] [DOC] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`. Added a
      "Child plans" digest group under Aggregated source docs for the 3 missing today-dated plans.
      `pm@<commit-pending>`.
- [x] [DOC] P1. ✅ **DONE 2026-07-24 (digest bullet + a new fix-it todo added — the target's own 3 dangling refs are NOT
      yet fixed)** — target: `/plans/active/defi_consolidated_closeout_2026_07_18.md`. Added a digest bullet for
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md` under Aggregated source docs, plus a new
      `- [ ] [DOC] P1.` todo to actually apply it into `defi_consolidated_closeout_aggregated_sources_2026_07_24.md` and
      fix that file's 3 dangling "tracked under X below" references (verified 2026-07-24: still unresolved there as of
      this correction). `pm@<commit-pending>`.
- [x] [DOC] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/prediction_consolidated_closeout_2026_07_18.md`. Added
      the 4 Phase A-E children as digest bullets in the Aggregated-source-docs section. `pm@<commit-pending>`.
- [x] [DOC] P3. ✅ **DONE 2026-07-24** — target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`. Added
      `data_completion_sports_history_2026_07_24.md` as a bulleted entry (via a pointer, per the agent's report — the
      Aggregated-source-docs content lives in a separate extracted file). `pm@<commit-pending>`.

## 13. AO-dispatch-readiness — zero contradictions, no open-ended items, crystal-clear for a cold Sonnet-5 worker

**Gap**: NOT uniformly satisfied. Sports is the only one of the 5 with a full self-documented adversarial pass (Track Y,
findings A-G — since archived out of the live sports closeout doc into
`/plans/archive/2026_07/sports_consolidated_closeout_history_2026_07_24.md` as part of the same-day line-cap trim) — and
even it has one un-flagged prose-only ordering dependency. tradfi/defi/cefi got only the narrower 2026-07-24
AO-flip-safety audit (checkbox-digest safety + `depends_on` gating) — a real but smaller slice; defi has a stale/broken
cross-todo citation plus a self-contradiction about whether a fix already shipped; cefi has an open-ended judgment-call
todo with no bounded scope. Prediction has had no adversarial pass at all.

- [x] [DOC] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`. Added a
      machine-gate caveat to Track C's EXCHANGE_ODDS/FIXED_ODDS fork sequence. `pm@<commit-pending>`.
- [x] [DOC] P1. ✅ **DONE 2026-07-24** — target: `/plans/active/defi_consolidated_closeout_2026_07_18.md`. Fixed the
      broken citation + resolved the self-contradiction in "Resume the paused DeFi crons" (the fix has, in fact, shipped
      — the todo now says so). `pm@<commit-pending>`.
- [x] [BACKEND] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/cefi_consolidated_closeout_2026_07_18.md`. Resolved
      the open-ended judgment call by splitting it into a bounded audit todo + a separate `[OPERATOR]` decision todo.
      `pm@<commit-pending>`.
- [x] [REVIEW] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`. Added
      the adversarial-pass todo (mirroring sports Track Y); did a same-session spot-check that found no obvious instance
      of the 6 defect classes, recorded inline. `pm@<commit-pending>`.
- [x] [REVIEW] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/prediction_consolidated_closeout_2026_07_18.md`.
      Added the adversarial-pass todo; same-session spot-check found no obvious instance, recorded inline.
      `pm@<commit-pending>`.

## 14. MVP vs non-MVP data distinction + batch=live=paper wiring symmetry

**Gap**: the epsilon=0 paper=batch-rerun determinism guarantee is real, documented codex SSOT for the tick/candle
event-log tier. Three concrete gaps survive: (1) the "one unified space" claim is proven only for that tier — paper
ledger outputs write to a SEPARATE `runs/{run_id}/ledger/` namespace, not the canonical `by_date/` tree, and no codex
doc says this scoping out loud; (2) "daily block" translation isn't documented verbatim anywhere (the mechanism exists,
split across 2 docs under different names); (3) none of the 5 AG plans' own "MVP universe" sections state which MVP
cells have actually been proven wired through backfill=paper=live, vs. just declared in-scope.

- [x] [DOC] P1. ✅ **DONE 2026-07-24** — target: new cross-cutting investigation. Created
      `plans/active/issues/mvp_scope_resolver_code_read_2026_07_24.md` with the bounded code-read todo (the
      investigation itself is future dispatch work). `pm@<commit-pending>`.
- [x] [DATA] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`. Extended
      "## MVP universe" with a real per-cell proven-wired-vs-declared table + an honest gap finding.
      `pm@<commit-pending>`.
- [x] [DATA] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md` (Track
      5 was forked out of `defi_consolidated_closeout_2026_07_18.md` earlier 2026-07-24; this is where the content
      actually landed — see gate-audit §14 there). Added a new "## MVP universe" section stating no cell is yet proven
      wired backfill=paper=live. `pm@<commit-pending>`.
- [x] [DATA] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/cefi_consolidated_closeout_2026_07_18.md`. Added a new
      "## MVP universe" section referencing `/codex/02-data/mvp-scope-canonical.md`, consolidating the scattered
      per-venue list + a table. `pm@<commit-pending>`.
- [x] [DATA] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/prediction_consolidated_closeout_2026_07_18.md`.
      Extended "## MVP universe" with a Codex SSOTs bullet citing
      `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`. `pm@<commit-pending>`.
- [x] [DATA] P2. ✅ **DONE 2026-07-24** — target: `/plans/active/sports_consolidated_closeout_2026_07_19.md`. Added a
      new "## MVP universe" section referencing `/codex/02-data/mvp-scope-canonical.md` § Sports. `pm@<commit-pending>`.

## Codex SSOTs

`/codex/02-data/honest-coverage-model.md`, `/codex/02-data/four-surface-reconciliation-procedure.md`,
`/codex/02-data/mdps-candle-canonical-reconciliation.md`, `/codex/05-infrastructure/vm-launcher-runbook.md`,
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`,
`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`,
`/codex/02-data/live-data-persistence-and-event-log.md`, `/codex/06-coding-standards/cli-convention.md`.

## Deferred work after 2026-07-24

| Item                                                                                                                                         | State                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Blocked on                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| -------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| All 64 todos above distributed into their target files                                                                                       | **Done 2026-07-24**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | — (33 by 5 parallel Agent-tool workers on the 5 consolidated closeouts, 8 direct, 23 as new stub issue docs/dispatchable todos where the ask was a genuine investigation, not formatting)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Todo #4's new skill + codex doc actually authored                                                                                            | **Done** (confirmed pre-existing, prior session)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Todo #4's first live 30-day audit run                                                                                                        | Not started                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Tracked in `plans/archive/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Point 3's tradfi/defi/prediction orphan-sweep re-measurements                                                                                | Partially done (defi/prediction measured by a concurrent session; tradfi/cefi/sports already had numbers)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | **CORRECTED 2026-08-16 (plan_reconciler)**: none — prediction's `B_legacy_duplicate` count was resolved `= 0` on 2026-07-30 (**corrected 2026-08-18, plan_reconciler cross-cutting** — was a digit transposition of the source doc's real date), per `estate_orphan_assessment_2026_07_21.md` todo 8's own `[x]` DONE entry                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| The ~15 sub-investigations this session stubbed as new issue docs (not executed)                                                             | Not started                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Nobody — each is now a bounded, dispatchable todo in its own issue doc (see §2/§4/§5/§7/§8/§9/§10/§14 above)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Adversarial verification of the 64-todo distribution's actual content quality                                                                | **Done 2026-07-24 (later, separate session)**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | — a 7-lane parallel workflow (one lane per target-file group) cross-checked every claimed addition against `task_template.md`'s rules + basic factual accuracy; all 64 genuinely landed real content (no hollow checkboxes), but found and fixed 8 concrete defects: 2 stale/wrong cross-references + 1 undercounted digest in tradfi, 1 malformed heading in defi (+ 1 overstated completion claim in this gate doc, corrected), 1 flatly-false "doc doesn't exist" claim (2x) + 1 undercounted digest in prediction, 2 line-1-truncated todos in cefi, and 2 defects in codex docs (a stale backlink claim, a self-contradictory invariant statement) — `pm@d5dcd5120` |
| Findings L (structural well-formedness) + M (internal self-consistency) added to `task_template.md` §3, `/plan-reconcile`, `/docs-reconcile` | **Done 2026-07-24**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | — `pm@6c1d89fe8`, closing the 2 defect classes above that no existing hunter's checklist named                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Operator-requested broader audit pass, part 1: full-corpus `/plan-reconcile`                                                                 | **DONE 2026-07-25 (hunt+verify+apply, fully closed)** — 74 hunters, 290 raw candidates, 246 confirmed (41 refuted) after adversarial verification. Severity: 1 P0, 35 P1, 119 P2, 91 P3. The sole P0 (`sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s league_id-casing todo extending an already-reverted K1/K2 migration) handled as its own issue doc + queued operator-decision item. 234 of the remaining 245 were auto-fixable; APPLY phase completed via a 16-agent background Workflow (`wnk9sc47x`, run `wf_ada40e95-0bf`) -- every batch's report reviewed: 2 formal NEEDS-OPERATOR-JUDGMENT items + 1 live-but-tracked P1 bug folded into the decision queue below, all real fixes verified pushed (`git rev-list --count` = 0 per batch). 11 report-only findings (archival-candidate + near-complete) handled directly: 8 via frontmatter status flips, 1 via the epic-body regenerator, 1 confirmed no-action-needed, 1 deferred (live-locked). Follow-up sweeps also completed: an archival-ritual sweep (16/16 candidates archived, deferred items migrated, none dropped) and a line-cap split-and-apply pass (5/5 over-cap files split + their blocked findings applied). Bonus: found + fixed a genuine `.pre-commit-config.yaml` worktree path-resolution bug (4 independent agents hit it; fixed upstream `2283828a7`) and a real YAML-fold frontmatter corruption bug affecting 5 plans (`b7e5c5cff`) | Nothing -- fully closed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Operator-requested broader audit pass, part 3: `/data-pipeline-reconciliation` x5 (one per AG)                                               | **DONE 2026-08-22 (relay+triage verified)** — launched in parallel with part 1 rather than waiting (independent corpus, no dependency): background Workflow task `wtb0lnq1m`, run `wf_db7e7fab-127`, 5 parallel agents (tradfi/defi/cefi/prediction/sports), raw-tick layer only (candles layer out of scope for this dispatch). Phase-0 pre-verified before dispatch to remove the most common first-run failure points: venv `market-tick-data-service/.venv` (only one that imports both UTL+UAC), `GCP_PROJECT_ID=central-element-323112` required env, `resolve_bucket_name` is all-keyword-only, prediction uses a dedicated flat `kind='market-data-tick-prediction'` (NOT `asset_group='prediction'` on the `market-data` kind, which raises `BucketNamingError`), all 5 prod buckets confirmed reachable. Script persisted at `/home/ubuntu/.claude/projects/-home-ubuntu-unified-trading-system-repos-market-tick-data-service/bbf81a1c-a8d9-4bff-857f-6b9f1b0f0229/workflows/scripts/data-pipeline-reconciliation-x5-wf_db7e7fab-127.js`, resumable via `Workflow({scriptPath, resumeFromRunId: "wf_db7e7fab-127"})` if the launching session is gone. Each agent writes `plans/audit/results/data_pipeline_reconciliation_<ag>_2026_07_24.md` + JSON and commits/pushes its own report. **Relay + triage confirmed 2026-08-22** (cross_cutting_satellite_ao_dispatch_batch18 item 7): every finding surfaced by the 5 reports was filed as an issue doc, and every one of those docs is now `status: resolved` (archived) — `plans/archive/issues/cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md` (cefi BIG finding), `plans/archive/issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md` + `plans/archive/issues/defi_lst_empty_marker_hardcoded_venue_2026_07_27.md` (defi's 2 findings), `plans/archive/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md` (tradfi), `plans/archive/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md` (prediction headline finding), and the addendum to `plans/archive/issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md` (sports) — verified by direct frontmatter read, not assumed from filenames alone                                                                                                                                                           | Nothing — fully closed; relay + triage verified 2026-08-22 (see State column for the 6 archived, `status: resolved` issue docs)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |

## Follow-up todo (added to make the Deferred-work table's open items real checkboxes)

- [x] [DATA] P2. **Run the first live 30-day VM billing-waste audit** — the Deferred-work table above still shows "Todo
      #4's first live 30-day audit run | Not started"; tracked in
      `/plans/archive/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md`. —
      `unified-trading-pm@a5d0702de` + the tracking doc's own `[x] [SCRIPT] P1` at
      `/plans/archive/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md:57-63` records the run
      DONE 2026-07-25 with GCP exhaustive (all 18 launcher families across two runs, 197/197 preemption events accounted
      for, one confirmed `tradfi-bf-*` billing-waste finding + an alerting gap), backed by two dated Progress Log
      entries citing real `gcloud compute operations list` output. Flipped 2026-08-02 by the `/plan-reconcile`
      whole-corpus run after verifying `a5d0702de` is an ancestor of `origin/live-defi-rollout` — this checkbox and the
      Deferred-work table row were simply never updated. **Residual, deliberately not blocking this checkbox** (it is
      the tracking todo's own stated carve-out, not a gap this todo owns): the AWS half stays IAM-blocked on
      `ec2:DescribeSpotInstanceRequests` for `uts-orchestrator-epic-role`, re-confirmed 2026-07-25.

## Lesson (2026-07-24, not yet elsewhere in codex — worth carrying)

Dispatching 5 concurrent background Agent-tool workers (one per consolidated closeout) filled this session's host tmpfs
(`/tmp/claude-1000/.../tasks/`, where background-task output/transcripts land) and blocked the MAIN session's own `Bash`
tool for an extended stretch (every command failed `ENOSPC`, incl. `echo hi`) — and 3 of the 5 sub-agents independently
hit the identical Bash lockout partway through their own runs, confirmed via their own final reports. Read/Edit/Write
tools kept working throughout; both the main session and the affected sub-agents worked around it by switching to
Read-only investigation + Edit (no `grep`/`wc -l`/git ops) for the remainder. Not yet reflected in
`/codex/12-agent-workflow/async-wait-and-poll-discipline.md`'s parallel-agent guidance — worth a note there if this
recurs: **more than ~3-5 concurrent background agents in one session risk exhausting the shared tmpfs**, degrading Bash
for everyone until agents finish and free space, not just a risk for the dispatching session.

## Operator decisions queued (2026-07-25, `/autonomous` extended run — operator away up to 8h)

Per explicit operator instruction: genuine judgment/authority-only calls found during this run are **parked here**
(pointer + one-line question) rather than decided unilaterally or blocked-on synchronously. Everything else (mechanical
fixes, provable-from-evidence corrections, AG-plan todo additions) is applied directly without asking, per the
workspace's own ASK>PARK calibration now that the operator is away. Each row's issue doc carries the full
`BLOCKED-OPERATOR-DECISION` entry (options + recommendation, SUB_AGENT_MANDATORY_RULES escalation format) — this table
is the single place to scan them all in one pass.

| #   | Question (one line)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Issue doc                                                                                                                  | Status                                                                                                                                   |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Prediction's manifest `data_type=prediction_trades` (2,477 rows, still being written) — retroactively register it as a legitimate 3rd shard-grain variant, or migrate/purge it as a bug? Neither the documented pre-Plan-A legacy shape nor any current codex doc names this exact shape.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | `/plans/archive/issues/prediction_polymarket_legacy_dual_write_trees_metadata_loss_2026_07_24.md` (Q3)                     | RESOLVED — answered directly in-session, see resolved_by in the linked issue doc                                                         |
| 2   | Sports league_id-casing satellite-batch2 AO todo would extend the K1/K2 upper-case migration Track C already ruled must be reverted (FINAL 2026-07-23). Not urgent right now (blocked on an unrelated gsutil credential issue) but should be fixed or explicitly BLOCKED-OPERATOR before that clears. **Recommendation: mark the todo BLOCKED-OPERATOR pending the same go-ahead Track C's own revert todos require** [WORKER REC], rather than repointing it to lower-case unilaterally, since Track C's revert is itself gated on an explicit operator decision not yet given. Not yet applied even as the non-committal gating fix — target file has been live-locked by another concurrent session on every retry today.                                                                                                                        | `/plans/archive/issues/sports_satellite_batch2_casing_direction_contradicts_k1k2_revert_2026_07_25.md`                     | RESOLVED — mtds@fb51d86c + unified-trading-pm@816b83c74                                                                                  |
| 3   | `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (+ sibling `wsfeedconnector_phase35_gap_2026_07_06.md`) carry `assigned_vm: NA` + `execution_scope: orchestrator-agent` — neither of `task_template.md`'s two documented pairings. Functionally harmless today (`NA` alone blocks AO ingestion regardless of `execution_scope`) but genuine intent ambiguity: is this plan actually meant to be AO-dispatched or not? **Recommendation: flip `execution_scope` to `local-only`** [WORKER REC] — the content reads as genuinely NA/not-dispatched despite the elaborate `[TAG]`/P0-P3 todo format, rather than flipping `assigned_vm` to `planning`.                                                                                                                                                                              | `/plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (plan-reconcile apply batch 9, finding 9) | RESOLVED — flipped execution_scope to local-only on both docs                                                                            |
| 4   | `/codex/02-data/tradfi-databento-sourcing-ssot.md`'s "VIX — futures vs the cash index" section is the stale side of a contradiction (zero mention of the 2026-06-23 VIX cash-index deletion; 2+ other docs already say VX-futures-only via Databento XCBF.PITCH, Barchart retired) — but per this run's own routing rule, a codex SSOT edit needs wider-review, not a batch-apply drive-by, even when the batch-apply agent is confident which side is stale. **Recommendation: update the codex SSOT's VIX section now** [WORKER REC] — low-risk since the underlying ruling is already well-established elsewhere; the alternative is leaving codex stale and filing a dedicated follow-up instead.                                                                                                                                               | `/codex/02-data/tradfi-databento-sourcing-ssot.md` (plan-reconcile apply batch 14, finding 14)                             | RESOLVED — /codex/02-data/tradfi-databento-sourcing-ssot.md updated                                                                      |
| 5   | FYI, not a decision needed: `dp_catalog_not_running_sports_prediction_2026_07_15.md` (P1) tracks a genuinely live, unresolved production bug — `CATALOGUE_SHRINK_BLOCKED` monotonic-guard rejections across sports/cefi/defi's `lifecycle-catalogue-regen-*` jobs, still recurring as of the 2026-07-23 RE-TRIAGE. The apply-Workflow found and fixed a `status: resolved` vs actually-still-open contradiction on this doc (it's correctly `status: open` again now, with the still-outstanding cefi todo restored) — already well cross-referenced from the sports/cefi/defi/prediction consolidated closeouts, so it isn't going to be silently missed. Flagging only so the operator knows this P1 is real and still open, not because any authority call is needed here — the engineering next steps are already tracked as todos in that doc. | `/plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md`                                             | RESOLVED — cefi dedup-aware guard shipped instruments-service@5c1c3ccb (2026-07-30), doc reached genuinely 0 open todos and was archived |

## Progress Log

- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; re-read after intervening edits, verdict unchanged):
  KEEP-NA, valid — dated operator ruling (autonomous_session_operator_decisions_2026_07_25 entry #10, resolved
  2026-07-26 option A): standing reference surface, not an archival candidate; 0 open todos is expected here.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03 (full re-scout pass)**: re-verified context_scope (6 entries, corrects the prior marker's
  stale count) -- unchanged; this is a standing tracking/index surface (0 open todos by design), no source path applies
  -- real work lives in the cited target plans.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms 2026-08-02 (unchanged): `archive_exempt: true`,
  standing reference surface by operator ruling; 0 open todos is expected/by design, not an archival signal here.
- **context-scout 2026-08-07**: re-verified context_scope, no change needed (6 entries) -- still a standing
  tracking/index surface, no source path applies.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-06 (unchanged): standing reference surface,
  `archive_exempt: true` by operator ruling, 0 open todos by design.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- reaffirms 2026-08-07 (unchanged):
  `archive_exempt: true`, standing reference surface by operator ruling
  (`autonomous_session_operator_decisions_ 2026_07_25.md` entry #10); 0 open todos is expected/by design here, not a
  reclassification signal.
- **context-scout 2026-08-15**: refreshed context_scope (6 entries), no change needed -- still a standing tracking/index
  surface, no source path applies.
**context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:bf5ab4d74bda2f7b]: KEEP-NA, valid -- 0 open todos by design, not an archival signal -- explicit dated operator ruling (autonomous_session_operator_decisions_2026_07_25.md entry #10, resolved 2026-07-26 option A) plus archive_exempt: true frontmatter plus 4 prior na-eligibility-audit reaffirmations (2026-08-02, 08-06, 08-07, 08-08 round7 RECLASSIFY sweep) all confirm this is a standing tracking/index surface with an ongoing citation duty (cited reference surface for /plan-reconcile's hunter 6), not a completed plan awaiting archival. locked_by is empty in frontmatter -- not locked.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — Standing reference/index surface (archive_exempt: true), 0 open todos by design — all 64 distribution todos read '✅ DONE — target: <file>' meaning the work was distributed elsewhere, not shipped here. Explicit dated.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
