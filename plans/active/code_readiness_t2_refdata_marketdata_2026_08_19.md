---
doc_type: plan
title: Code readiness T2 — reference data and market data
summary: >-
  Tranche 2 of the five-agent code-readiness push — makes instruments-service, market-tick-data-service and market-data-processing-service code-complete. Owns the coverage story the artefacts lead with, including the shard denominator, the four-state capture ledger and the instrument_type plus data_type grain T5's dump needs.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, market-tick-data-service, market-data-processing-service]
scope: [engineer]
tags: [code-readiness, instruments, mtds, mdps, honest-coverage, tranche-2]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/audit/results/code_completion_scope_2026_08_19.md,
    /plans/audit/results/code_readiness_allocation_2026_08_19.json,
    /codex/14-customer-journeys/commercial-model/platform-architecture.html,
  ]
created: 2026-08-19
last_updated: 2026-08-19
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 45
estimate_calibrated_ai_days: 18
locked_by:
locked_since:
context_scope:
  [
    /plans/epics/system_readiness_master.md,
    /plans/audit/results/code_completion_scope_2026_08_19.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
supersedes:
superseded_by:
depends_on:
source: >-
  Operator directive 2026-08-19 — allocate every active plan and issue across five parallel agents and drive the four
  client artefacts to code-ready, excluding manifest migration and data backfills.
assigned_role: data_engineering
effort: max # multi-day autonomous tranche — 30-40 todos spanning several repos, cross-tranche contract edges
drift_direction: advance-code
---

# Code readiness T2 — reference data and market data

> **Tranche 2 of 5.** Owned repos — **instruments-service, market-tick-data-service, market-data-processing-service**. Allocated corpus —
> **293 docs** (28 spine, 31 excluded as data-movement), **753 open todos**
> at authoring. You are one of five agents running in parallel on disjoint repos.

**This tranche owns the number the artefacts lead with.** The coverage denominator, the shard atom and the
four-state capture ledger are all yours. It is also the largest tranche by doc count (293) — but 31 of the 31 spine
docs are what matter; the tail is mostly data-movement you are explicitly told not to run.

## The goalpost — what "done" means (operator ruling 2026-08-19)

Everything in this tranche is **complete in code**. The ONLY things that may still be pending when this plan closes:

1. **Backfills still running** — batch data landing.
2. **Venue connectivity** — private feed and public feed, orders and trades.
3. **Market data live.**
4. **Testnets, where they exist.**
5. **Strategy archetypes code-ready for batch / paper / live — pending testing with real data.**

Anything outside those five that is not code-complete is REMAINING WORK. SSOT for the goalpost:
`/plans/epics/system_readiness_master.md` § "Definition of done".

**The acceptance test is the artefacts.** These four client-sendable documents must stop carrying `pending`,
`planned`, `partial`, `not built` or `unverified` on any claim that is not one of the five above:

- `/codex/14-customer-journeys/commercial-model/platform-architecture.html`
- `/codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html`
- `/codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html`
- `/codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html`

Their status markers carry `owner: W1`…`W22` tags binding each claim to a workstream in
`/plans/epics/system_readiness_master.md`. Closing a W-item is what clears its marker. **Never clear a marker by
editing the HTML** — the marker is derived from real state; change the state, then re-derive.

## Standing rules for this tranche — HARD

- **Do NOT run backfills, manifest migrations, corpus sweeps or GCS deletes** (operator ruling 2026-08-19). Fixing
  the manifest-writer / path-registry / capture-status **code** is IN scope; launching the data movement is NOT.
  A todo whose only remaining step is "relaunch the VM" or "apply the delete" is marked `BLOCKED-OPERATOR` and left.
- **Do NOT request or wait on API keys / credentials.** Where a real credential is missing, build the adapter and
  the full code path anyway and mark the item `BLOCKED-CREDENTIALS` — never descope it. SSOT:
  `/codex/02-data/external-data-always-available-rule.md`.
- **Edit ONLY the repos this tranche owns** (listed above). Another tranche owns every other repo, and a same-file
  edit across two agents is the one thing the workspace concurrency model forbids. Need a change in someone else's
  repo? File it via the handoff protocol below — never reach across.
- **Every claim ≤ its measurement.** A proxy (line count, exit 0, a green test, a cached `origin/`) is not the
  property. Measure it or say you did not. SSOT: `/codex/12-agent-workflow/measurement-claims-discipline.md`.
- **Commit + push + flip the checkbox in the SAME turn**, with `<repo>@<sha>` evidence. SSOT:
  `/codex/12-agent-workflow/commit-push-flip-rule.md`.
- **Ship code only via** `bash scripts/quickmerge.sh "msg" --agent --files '<paths>'` from a `quality-gates.sh`-green
  tree. Doc/plan-only changes go via `bash scripts/dev/safe-doc-push.sh`.

## Cross-tranche handoff protocol

Five agents run in parallel on disjoint repos. When your work needs a change in a repo you do not own:

1. Append a `- [ ]` todo to the OWNING tranche's plan under its `## Inbound requests` section, tagged
   `[FROM-<your-tranche>]`, naming the exact symbol/file and what shape you need.
2. Commit that plan edit via `safe-doc-push.sh` (doc-only, no code).
3. Keep working — build your side against the contract you asked for, behind a feature flag or an adapter seam if
   it does not exist yet. Do not block, and do not edit their repo yourself.

**Known blocking edges at authoring time** (T1 is upstream of everyone — it runs first and fastest by design):

- T4 delta-proxy repricer generalization → needs T1 to extend UAC `QuoteInstruction` with
  `delta` / `gamma` / `underlying_instrument_id`.
- T3 + T4 strategy→execution reference triple → needs T1 to add `reference_position` and `credit` to
  `StrategyInstructionEnvelope`.
- T5 readiness dump's execution-instruction leg (the structural reason all 864 rows read `unverified`) → needs T4
  to expose a real per-venue instruction-path check.
- T5 coverage dump at `instrument_type` / `data_type` grain → needs T2 to land those axes in `coverage.json`.

## Your allocated corpus

The full, reproducible allocation lives in `/plans/audit/results/code_readiness_allocation_2026_08_19.json`,
regenerated by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`. Every one of the 892 active plan/issue
docs is assigned to exactly one tranche, so nothing is orphaned and nothing is worked twice.

```bash
python3 -c "
import json
d=json.load(open('plans/audit/results/code_readiness_allocation_2026_08_19.json'))
for x in d['tranches']['T2-refdata-marketdata']['docs']:
    if not x['excluded_data_movement']:
        print(('SPINE ' if x['spine'] else '      '), x['priority'], x['open_todos'], x['path'])
"
```

**Work order**: `spine: true` docs FIRST, in priority order — those are the docs that back a presentation claim.
Then the tail. A doc flagged `excluded_data_movement: true` is skipped per the standing rules above; open its
todos only to confirm they are data-movement, then leave it.


## Inbound requests

> Other tranches append `- [ ] [FROM-Tn]` items here when they need a change in a repo you own. Work them at the
> priority they state — another agent is blocked on each one.

_None at authoring time._

## Todos

### W3 — granularity and the shard denominator

- [ ] [BACKEND] P0. Reconcile the shipped 3,960-shard denominator against the operator's deepest-grain ruling. The
      shard space is NOT a Cartesian product — SSOT: `/plans/epics/system_readiness_master.md` § W3.
- [ ] [BACKEND] P0. Add `instrument_type` and `data_type` columns to the coverage payload. **T5's coverage dump
      blocks on this** — it can only report at `(venue, data_type)` grain until these land. Tell T5 when shipped.
- [ ] [BACKEND] P0. Fix the mislabelled `grain` field. A wrong grain label silently misstates every denominator
      derived from it.
- [ ] [BACKEND] P0. Ensure the shard atom is IDENTICAL across writer, manifest, status, gate and UI. Any divergence
      makes two honest components disagree with no error. SSOT:
      `/codex/02-data/availability-manifest-and-data-status.md`.
- [ ] [BACKEND] P0. Make honest coverage measurable on EVERY axis and granularity, each figure carrying its
      denominator and date. This is the epic's own definition-of-done item. SSOT:
      `/codex/02-data/honest-coverage-model.md`.

### W2 — data pipeline integrity (code only, no runs)

- [ ] [BACKEND] P0. Land the manifest canonicalisation and skip-logic CODE. Do NOT run the migration.
- [ ] [BACKEND] P0. Build consolidator-freshness gating so a stale index loud-fails rather than serving stale
      coverage. SSOT: `/codex/05-infrastructure/manifest-consolidator-ssot.md`.
- [ ] [BACKEND] P0. Build the orphan-shard consumption check — no shard stored that nothing consumes. Epic
      definition-of-done item. SSOT: `/codex/02-data/orphan-object-detection.md`.
- [ ] [BACKEND] P1. Fix the manifest-writer per-VM shard flush that does a full read-merge-reserialize-upload on
      every debounced flush — past ~1M rows the flush outlasts the debounce interval and the VM stalls. CODE only.
      Evidence: `/plans/active/issues/manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md`.
- [ ] [BACKEND] P1. Fix blocking GCS writes on the event loop, cross-asset-group. Evidence:
      `/plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md`.
- [ ] [BACKEND] P1. Ensure `expected_unattempted` is materialised by the WRITER and never re-derived downstream.

### instruments-service

- [ ] [BACKEND] P0. Complete the `InstrumentRecord` schema ADD/REMOVE reconciliation against adapter kwargs and flip
      `extra='forbid'`. Adapter kwargs are silently dropped on mismatch today. Evidence:
      `/plans/active/instrument_record_schema_completeness_extra_forbid_2026_07_18.md`.
- [ ] [BACKEND] P0. Lock and version the instruments schema — add `INSTRUMENTS_SCHEMA_VERSION`, a `schema_version`
      field on `SchemaContract`, make writers/readers actually consult the per-AG contracts, and add a golden/hash
      test so a silent column change cannot ship. Evidence:
      `/plans/active/issues/instruments_schema_not_locked_versioned_2026_08_18.md`.
- [ ] [BACKEND] P0. Build the instruments catalogue definitions aggregation and field-change history — monthly-grain
      aggregation, mutable-field declaration, field-change log, point-in-time-equivalence proof. **The design
      ratification todo is `[OPERATOR]`-gated** — build everything downstream of it against the documented design
      and flag the gate. Evidence:
      `/plans/active/instruments_catalogue_definitions_and_field_history_2026_08_17.md`.
- [ ] [BACKEND] P0. Land the venue smoke-test bar and the venue E2E wiring. Evidence:
      `/plans/active/venue_smoke_test_bar_2026_08_16.md`, `/plans/active/venue_e2e_wiring_2026_08_16.md`.
- [ ] [BACKEND] P0. Close the CeFi and TradFi G1-G5 gate execution CODE paths. Evidence:
      `/plans/active/instruments_cefi_g1_g5_gate_execution_2026_07_24.md`,
      `/plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`.
- [ ] [BACKEND] P1. Fix the CeFi `instrument_type` casing active-writer regression. Evidence:
      `/plans/active/issues/cefi_instrument_type_casing_active_writer_regression_2026_08_17.md`.
- [ ] [BACKEND] P1. Land the CF-canonicalization single-walk CODE. Any NEW whole-corpus GCS walk is
      review-blocking — reuse the existing walk. Evidence:
      `/plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md`.
- [ ] [BACKEND] P1. Resolve the DeFi golden/red capability drift — `test_expected_matches_golden[defi]` failing
      fleet-wide. Re-verify current red/green state first; the prior pass did not. Evidence:
      `/plans/active/issues/instruments_service_defi_golden_red_capability_drift_2026_08_14.md`.
- [ ] [BACKEND] P1. Close the foundation-completeness and phase-0 cross-cutting CODE items. Evidence:
      `/plans/active/instruments_foundation_completeness_2026_06_24.md`,
      `/plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md`.
- [ ] [BACKEND] P2. Fix the AAVEV3 bare-alias enumerator CODE (already root-caused — duplicate dict key plus missing
      alias canonicalisation). The 46,300 bad `empty_confirmed` manifest rows stay operator-gated, not yours.

### MTDS and MDPS

- [ ] [BACKEND] P0. Fix the multi-instrument candle bundle write race — when 2+ underlyings land in the same shared
      `ticks.parquet` bundle each is written via an independent overwrite with no download-existing merge. Evidence:
      `/plans/active/issues/mdps_multi_instrument_bundle_write_race_hypothesis_2026_08_09.md`.
- [ ] [BACKEND] P1. Land the MDPS adapter-protocol / polars-seam migration as ONE atomic change across the 18
      adapter files sharing the ABC/Protocol boundary. Evidence:
      `/plans/active/issues/mdps_adapter_protocol_polars_seam_mis_scoped_ao_dispatch_2026_08_15.md`.
- [ ] [BACKEND] P1. Resolve the B21 distinct-values non-canonical live finding. Evidence:
      `/plans/active/issues/b21_distinct_values_noncanonical_live_2026_08_18.md`.
- [ ] [BACKEND] P2. Decide and implement the MTDS WS venue-fallback removal for Polymarket. Evidence:
      `/plans/active/issues/mtds_ws_venue_fallback_removal_polymarket_decision_2026_08_17.md`.
- [ ] [BACKEND] P2. Confirm the MDPS `--force` subprocess fix is live and that only a data relaunch remains — that
      relaunch is out of scope. Evidence:
      `/plans/active/issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md`.
- [ ] [BACKEND] P2. Ensure `source=` is threaded through every `record_captured()` call — it is crosscutting and
      required. SSOT: `/codex/02-data/pipeline-mode-partition.md`.

### Close-out

- [ ] [AGENT] P1. Work the non-spine tail of this tranche's allocation to zero open todos or an explicit
      `BLOCKED-*` tag. 31 docs in your allocation are flagged `excluded_data_movement` — confirm and leave them.
- [ ] [AGENT] P0. Post-phase codex audit across `/codex/02-data/` for every contract you changed.
- [ ] [AGENT] P0. Confirm every artefact coverage marker owned by this tranche now reads live with a stated
      denominator and date, or is one of the five allowed pending states.

## Progress Log

> Append-only. One entry per shippable unit — what you changed, the `<repo>@<sha>`, and what you MEASURED (not what
> you assume). This log is the handoff document if this agent's context ends and a fresh one resumes the tranche.

- 2026-08-19 — Plan authored. Allocation derived by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`
  against the 892-doc active corpus. No code work started yet.
