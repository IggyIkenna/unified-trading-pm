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

- [x] [FROM-T1] P1. **Re-check chain-scoped output for the four venues `KNOWN_CHAINS` silently dropped.**
      ✅ 2026-08-20 — **checked; no re-derivation needed for those four, and no data movement required.** Measured
      from the live 2026-08-19 coverage projection (derived from the manifest — no new GCS walk): none of
      `AAVE_V3-SCROLL`, `COMPOUND_V3-SCROLL`, `AAVE-PLASMA`, `FLUID-PLASMA` exists as a glued venue anywhere in the
      DeFi projection; there are ZERO `-SCROLL`/`-PLASMA`-suffixed venues at all. The bare protocols (`AAVE_V3`,
      `COMPOUND_V3`, `AAVE`, `FLUID`) are all present, and both chains are first-class values in `by_chain` with
      real volume (`SCROLL` 122,183 rows, `PLASMA` 198,424 rows incl. 36 captured). The venue/chain split landed
      correctly for these rows. **Scope of that claim**: it shows the chain column is populated and no glued form
      survived — it does not independently re-verify that each row is attached to the right protocol.
      **Both chains are ~99.9% `empty_confirmed`** (SCROLL 122,053/122,183 with 0 captured; PLASMA 198,388/198,424).
      That may be legitimate pre-genesis absence — not investigated here, and deliberately NOT claimed as a defect.
- [x] [FROM-T1-CONTEXT] P3. _(T1's original request text, kept so the todo total never shrinks — a checkbox flip
      must not delete a line.)_ **Re-check chain-scoped output for the four venues `KNOWN_CHAINS` silently
      dropped.** ✅ 2026-08-20 — answered in full by the `[FROM-T1] P1` item above; this entry is the same request,
      retained only for provenance.
- [x] [FROM-T1] P2. **instruments-service hand-rolls its own `KNOWN_CHAINS` literals instead of importing UAC's.**
      ✅ 2026-08-20 — all three now import the UAC set. T1's stated cause (missing SCROLL/PLASMA) did NOT hold on
      measurement; the real drift was a missing `ASTER` plus a phantom `STARKNET`. Evidence:
      `instruments-service@2b482a1247`; verified post-change that `_CATALOGUE_KNOWN_CHAINS is KNOWN_CHAINS`.
      Found while enumerating consumers: `scripts/audit_defi_zero_glued_2026_06_25.py` defines a local
      `KNOWN_CHAINS = {...}` set, `scripts/build_instrument_catalogue.py` defines `_CATALOGUE_KNOWN_CHAINS`
      ("mirrors the UAC `KNOWN_CHAINS` set"), and `scripts/collapse_defi_drift_to_canonical_2026_06_25.py` defines
      another. A mirrored copy does not receive the SCROLL/PLASMA fix and will drift again — these should import
      the UAC set. Not touched by T1: they are your repo.

## Todos

### W3 — granularity and the shard denominator

- [x] [BACKEND] P0. Reconcile the shipped 3,960-shard denominator against the operator's deepest-grain ruling. The
      shard space is NOT a Cartesian product — SSOT: `/plans/epics/system_readiness_master.md` § W3.
      ✅ 2026-08-20 — **ANSWERED: 3,960/3,962 is NOT the deepest-grain count. It is a projection that drops the
      chain axis for 99.1% of DeFi cells and drops leagues entirely.** The operator's expectation that a genuinely
      exhaustive count is LARGER is CONFIRMED. Measured against the live 2026-08-19 payload:
      - The payload carries exactly seven projections — `by_asset_group`, `by_venue`, `by_venue_data_type`,
        `by_venue_instrument_type`, `by_venue_instrument_type_data_type`, `by_day`, `by_chain`. **None joins chain
        to the shard atom.** `by_chain` is a MARGINAL `ag → chain → counts` view, never crossed with
        `(venue, instrument_type, data_type)`.
      - DeFi carries 23 distinct chains, but **2,778 of its 2,804 level-5 cells sit on a BARE venue** (no `-CHAIN`
        suffix), so one cell covers every chain that protocol runs on. Only 26 cells carry a glued
        `PROTOCOL-CHAIN` venue where the chain is folded in. The DeFi venue axis is therefore in a MIXED state and
        the count is neither cleanly chain-scoped nor cleanly chain-agnostic.
      - `cefi`, `tradfi`, `sports` and `prediction` each report exactly ONE chain and it is the empty string — the
        axis is inapplicable there, which is correct and not a defect.
      - **No league axis exists anywhere in the payload**, though the ruling names leagues as a real sports axis.
        Sports contributes 822 level-5 cells across 46 venues with leagues entirely uncollapsed into them.
      - Days are available (`by_day`: cefi 2,785 / defi 3,152 / tradfi 3,153 / sports 2,242 / prediction 3,152), so
        the ruling's "full denominator = shards x available days" is computable once the shard axis is right.
      **Not silently re-stated as a new headline number**: per the ruling, any denominator change lands as a dated
      supersession. The honest statement today is that 3,962 (3,876 after the 2026-08-20 dedup fix) is the
      `(asset_group, venue, instrument_type, data_type)` projection on 2026-08-19 — chain and league omitted — and
      that the exhaustive count cannot be produced until the next two todos land.
- [x] [BACKEND] P0. **Add a chain-joined shard-atom projection so the deepest grain is computable at all.**
      ✅ 2026-08-20 — shipped `instruments-service@551b25093c` (verified an ancestor of `origin/live-defi-rollout`;
      landed blob re-read to confirm it carries the projection). `by_venue_instrument_type_data_type_chain` emits
      `ag -> venue -> instrument_type -> data_type -> chain -> counts`, grouped on the SAME case-folded
      instrument_type/data_type keys and the SAME level-4 display label as level 5, so the two projections name one
      shard identically. Null chain spellings collapse to a single `""` via `_normalise_chain_series`, so an
      inapplicable axis (cefi/tradfi/sports/prediction) is one blank key rather than being omitted — a missing key
      and an inapplicable axis must not look alike to a reader. Registered in `_MERGEABLE_BY_AG_KEYS` so the
      per-asset_group streaming merge carries it (omitting that would have silently dropped it on every real run —
      the unit tests alone would not have caught that). 3 tests; full suite `5370 passed`; QG green (154s).
      **ADDITIVE: no published number changes.** Re-cutting the headline shard count against it is the separate,
      operator-gated supersession step, per W3. Today
      no projection crosses `chain` with `(venue, instrument_type, data_type)`, so the exhaustive DeFi shard count
      cannot be derived from the artefact by any consumer. `chain` is already read (`_READ_COLUMNS_WITH_CHAIN`) and
      already grouped marginally (`by_chain`), so this is an ADDITIVE projection, not a change to any published
      number — it can land without a supersession, and the reconciled denominator can then be quoted from it.
- [ ] [OPERATOR] P0. **Rule on the sports league axis before it is built.** The W3 ruling names leagues as a real
      sports axis and excludes FIXTURES from the shard COUNT while keeping them in the full denominator. Neither
      distinction is expressible today — no league axis exists in the manifest projections at all. Whether league
      belongs on the shard atom (multiplying 822 sports cells by league cardinality) or stays a drill-down is a
      denominator-defining decision, so it is the operator's, not this tranche's.
- [x] [BACKEND] P0. Add `instrument_type` and `data_type` columns to the coverage payload. **T5's coverage dump
      blocks on this** — it can only report at `(venue, data_type)` grain until these land. Tell T5 when shipped.
      ✅ 2026-08-20 — **already live before this tranche started; verified by execution, not by reading the writer.**
      Loaded `gs://central-element-323112-honest-coverage/2026-08-19/coverage.json` through T5's own
      `shard_universe.py`: `by_venue_instrument_type` (172 `(ag, venue)` pairs) and
      `by_venue_instrument_type_data_type` (184 pairs) populated for all 5 asset_groups, `detect_grain()` →
      `"instrument_type"`, 3,962 cells at `(ag, venue, instrument_type, data_type)`. T5 told, in their plan's
      `## Inbound requests`, with the two caveats that make the finer grain honest. Evidence:
      `unified-trading-pm@89fab080bd`. The axes needed no code; making them honest did — next item.
- [ ] [BACKEND] P0. Fix the mislabelled `grain` field. A wrong grain label silently misstates every denominator
      derived from it.
- [ ] [BACKEND] P0. Ensure the shard atom is IDENTICAL across writer, manifest, status, gate and UI. Any divergence
      makes two honest components disagree with no error. SSOT:
      `/codex/02-data/availability-manifest-and-data-status.md`.
      **PARTIAL 2026-08-20 — deliberately left open; the shipped fix covers the projections, not all five surfaces.**
      Fixed the level-4 ↔ level-5 divergence (3 defects, 86 duplicate cells, each measured on the live payload
      first and each pinned by a test proven to fail pre-fix): unstable level-5 display label (24 groups), `'nan'`
      leaking as a real instrument_type key (26 beside 85 blank), and `data_type` never case-folded (6 groups).
      Evidence: `instruments-service@2b482a1247`, verified an ancestor of `origin/live-defi-rollout`.
      **Still unmeasured, so still unchecked**: whether the manifest WRITER, the data-status gate and the UI agree
      with the projections' atom. Checking this box now would exceed what was measured.
- [ ] [BACKEND] P0. Make honest coverage measurable on EVERY axis and granularity, each figure carrying its
      denominator and date. This is the epic's own definition-of-done item. SSOT:
      `/codex/02-data/honest-coverage-model.md`.
- [ ] [OPERATOR] P0. **Rule on whether level 5 should drop fully-retired keys like level 4 does.** MEASURED
      2026-08-20: `by_venue_instrument_type` (level 4) passes through `_drop_fully_retired_nested`;
      `by_venue_instrument_type_data_type` (level 5) does not. After the 2026-08-20 naming fix the two levels
      agree on what each shard is CALLED but still disagree on which shards EXIST. Level 5 is the shard atom
      `iter_shard_cells()` reads, so aligning it changes the published denominator — which is exactly why this is
      operator-gated and was not folded into the naming fix. Blocked on the ruling, not on code.
- [ ] [BACKEND] P1. **Report coverage grain PER asset_group, or publish the hollow fraction beside the label.**
      MEASURED 2026-08-19: 1,973 of 3,962 cells (49.8%) carry a blank or `'nan'` instrument_type while
      `detect_grain()` reports `"instrument_type"` for the whole payload — `defi` 1,871/2,804 (66.7%), `tradfi`
      82/244 (33.6%), `prediction` 10/19 (52.6%), `sports` 10/822 (1.2%), `cefi` 0/73 (0%). A single payload-wide
      grain label overstates the breakdown available for half the corpus. Same failure mode as the mislabelled
      `grain` in the readiness dump (filed to T5, who owns that writer).
- [ ] [BACKEND] P1. **Trace the 9 blank-venue `sports` cells to the writer that emits them.** MEASURED
      2026-08-19: 9 cells in coverage.json carry `venue == ""` (all `sports`, data_types `odds_movement`,
      `odds_snapshot`, `ODDS_MOVEMENT`, `ODDS_SNAPSHOT`, `ARBITRAGE_OPPORTUNITY`, each `empty_confirmed: 1`).
      They propagate into T5's readiness dump as 9 rows with an empty `venue`. Read-only diagnosis of the manifest
      writer path first — any manifest row repair is data movement and stays operator-gated.

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
- [ ] [BACKEND] P0. **BLOCKED-UPSTREAM (T1/UAC)** — Lock and version the instruments schema — add
      `INSTRUMENTS_SCHEMA_VERSION`, a `schema_version` field on `SchemaContract`, make writers/readers actually
      consult the per-AG contracts, and add a golden/hash test so a silent column change cannot ship. Evidence:
      `/plans/active/issues/instruments_schema_not_locked_versioned_2026_08_18.md`.
      **Reason 2026-08-20 — the locked contract has NEVER matched the catalogue writer, so wiring it up as
      specified would have blocked production promotion for all five asset groups.** Parts 1-3 of that issue's
      4-part fix are UAC (T1's repo); part 4 is mine. I built part 4 — `validate_dataframe(df, CONTRACT_REGISTRY[...])`
      at `build_instrument_catalogue.py::promote_catalogue`, which already takes `asset_group`, blocking the way its
      neighbour `CATALOGUE_SHRINK_BLOCKED` does (CRITICAL event + exit 1, never a raise) — then MEASURED it before
      shipping and **reverted it**. The measurement:

      - The writer's `CATALOG_COLUMNS` emits **41** columns; the contract declares **85**.
      - **4 of the 6 `required=True` columns are never emitted, for ALL FIVE asset groups**:
        `instrument_key`, `symbol`, `available_from_datetime`, `timestamp`.
      - The writer's canonical identifier is **`instrument_id`** (`build_instrument_catalogue.py:279` — "`instrument_id`
        is written as the canonical column"); the contract requires `instrument_key`. Likewise the writer emits
        `available_from`/`available_to` where the contract wants `available_from_datetime`/`available_to_datetime`.
      - Wiring the gate turned 3 existing `promote_catalogue` tests red with 80 violations on a cefi frame — not
        because the fixtures are thin, but because the contract describes a different shape than the writer produces.

      So the contract is not a lock that drifted; it never fit. That also explains why "registered in
      `CONTRACT_REGISTRY` but consulted by nothing" survived unnoticed — the first consumer would have failed
      immediately. Part 4 is genuinely blocked on reconciling the contract with the writer, which lives in UAC.
      Filed to T1. The revert is verified: `git status` clean and the 12 `promote_catalogue` tests green again.
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
- [x] [BACKEND] P1. Resolve the DeFi golden/red capability drift — `test_expected_matches_golden[defi]` failing
      fleet-wide. Re-verify current red/green state first; the prior pass did not. Evidence:
      `/plans/active/issues/instruments_service_defi_golden_red_capability_drift_2026_08_14.md`.
      ✅ 2026-08-20 — **re-verified as instructed, and the todo's premise is stale: it is NOT red.** Ran the full
      instruments-service suite (`5367 passed, 6 skipped, 4 xfailed`): `test_expected_matches_golden[defi]` is
      **XFAIL** — a managed expected-failure carrying a written reason, not a failure. Nor is it defi-specific:
      `[defi]`, `[tradfi]`, `[sports]` and `[prediction]` are all xfailed; `[cefi]` is the only green one. The
      cited issue doc has ZERO open todos. Each xfail reason already names the reconciliation its own AG owner must
      do (e.g. the defi one flags that `defi_satellite_ao_dispatch_batch9_2026_08_06.md` claims to have REMOVED the
      AAVE_V3 rewards seed while the live universe still HAS it — so either the removal is incomplete or the golden
      was regenerated too early). Regenerating any fixture would silently pick a side of an unresolved question, so
      nothing was regenerated. **Correction to a claim I nearly made**: `AAVE`, `AAVEV3` and `AAVE_V3` appear as
      separate DeFi venues in coverage.json, but UAC's `canonicalize_defi_venue_combined()` maps all 105 DeFi
      venues to 105 distinct keys — zero collapse — so these are distinct venues, NOT spelling drift.
- [ ] [BACKEND] P1. Close the foundation-completeness and phase-0 cross-cutting CODE items. Evidence:
      `/plans/active/instruments_foundation_completeness_2026_06_24.md`,
      `/plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md`.
- [ ] [BACKEND] P2. Fix the AAVEV3 bare-alias enumerator CODE (already root-caused — duplicate dict key plus missing
      alias canonicalisation). The 46,300 bad `empty_confirmed` manifest rows stay operator-gated, not yours.

### MTDS and MDPS

- [ ] [BACKEND] P0. **BLOCKED-OPERATOR** — Fix the multi-instrument candle bundle write race — when 2+ underlyings
      land in the same shared `ticks.parquet` bundle each is written via an independent overwrite with no
      download-existing merge. Evidence:
      `/plans/active/issues/mdps_multi_instrument_bundle_write_race_hypothesis_2026_08_09.md`.
      **Reason 2026-08-20**: there is no write race to fix. The as-stated hypothesis was already REFUTED by code
      reading on 2026-08-10 and re-confirmed here — `_blob_matches_data_type_partition` admits only
      `underlying={U}/ticks.parquet` blobs and `_build_candle_output_path` emits a DISTINCT path per underlying, so
      BTC and ETH never share an object. The real defect is WITHIN-bundle truncation (7 raw contracts → 1 emitted,
      on both BYBIT and DERIBIT), and the issue's sole remaining todo is gated on a post-fix VM relaunch completing
      and being audited — data movement, out of scope per the standing rules. Read the current streaming path
      (`live_workers_streaming.py::_process_chain_bundle_streaming`): it accumulates every `_iter_chain_symbol_dfs`
      slice into `candles_by_tf`, and `_streaming_write_per_tf` streams every batch for a true chain
      (`groups = [(instrument_id, tf_candles)]`), so the current code appears correct and the stale 1-of-7 bundles
      predate it. The next item is the piece of this that IS code-shaped.
- [x] [BACKEND] P0. **Close the multi-symbol survival gap with a unit test so the relaunch stops being the only
      oracle.** ✅ 2026-08-20 — shipped `market-data-processing-service@8bffeb8dfe` (verified an ancestor of
      `origin/live-defi-rollout`; landed blob re-read to confirm the tests are in it). Three tests drive the real
      `_process_chain_bundle_streaming` with a 7-contract BYBIT futures_chain bundle — mirroring the exact GCS
      ground truth the issue measured — and assert every contract reaches `_streaming_write_one_group`, that a true
      chain writes ONE group per timeframe keyed on the chain root, and that the single-contract case still writes
      (so the multi-symbol assertions cannot pass vacuously). **RESULT: the current streaming code PRESERVES all 7
      contracts.** The issue doc's "current code appears correct ... unverifiable without the live post-fix
      relaunch" is now VERIFIED in code, so the stale 1-of-7 bundles are attributable to older code, not to what
      ships today. **Test teeth proven, not assumed**: injecting the exact 7→1 truncation into
      `_streaming_process_slice_timeframes` makes them fail with `6 of 7 contracts never reached the writer`; the
      source was restored and re-verified clean by `git diff` before shipping. Remaining risk on this symptom is
      DATA (already-written bundles), not code — and that stays operator-gated.
      **The gap that made this necessary**: `test_chain_streaming.py` already covered `_iter_chain_symbol_dfs`
      (the READER yields one slice per symbol), but a grep for a symbol-count/`nunique` assertion over WRITTEN
      output returned zero hits across the whole MDPS test tree — nothing checked that those slices survive to the
      writer. That absence, not the code, is why the issue stayed VM-gated for eleven days.
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

- 2026-08-20 — **T5 unblocked; the coverage-grain axes were already live.** Read the live artefact
  `gs://central-element-323112-honest-coverage/2026-08-19/coverage.json` (`schema_version: 2`) through T5's own
  engine (`cursor-configs/skills/honest-coverage-dump/scripts/shard_universe.py`) rather than inspecting the
  writer. MEASURED: both `by_venue_instrument_type` (172 `(ag, venue)` pairs) and
  `by_venue_instrument_type_data_type` (184 pairs) are populated for all 5 asset_groups; `detect_grain()` returns
  `"instrument_type"`; `iter_shard_cells()` yields **3,962** cells at `(asset_group, venue, instrument_type,
  data_type)` grain. The "add `instrument_type`/`data_type` columns to the coverage payload" todo was therefore
  already satisfied in production before this tranche started — the work left was not ADDING the axes but making
  them HONEST (below). Notified T5 in their plan's `## Inbound requests` with the two caveats they must carry into
  the re-run.

- 2026-08-20 — **Shard-atom defects in the coverage writer: found by measurement, fixed, regression-tested.**
  Three defects in `instruments-service/scripts/measure_honest_coverage.py`, each measured against the live
  2026-08-19 payload before any code was touched, each with a test PROVEN to fail on the pre-fix source and pass
  on the fixed one (ran the suite against `git show HEAD:` of the file to confirm, rather than assuming):

  1. **Level-5 display label was unstable across data_types — 24 groups.** `_representative_instrument_type()` was
     called inside each `(venue, itype_fold, data_type)` group, so the case-majority could differ per data_type
     and one logical shard grew TWO keys with its data_types split between them. `sports/LADBROKES` carried both
     `'ODDS'` (`data_types=['trades']`) and `'odds'` (`data_types=['odds']`). Level 4 was already clean (0 splits)
     — only level 5 leaked, so the two projections disagreed about what one shard is called. Fix: resolve the
     label ONCE per `(venue, case-folded instrument_type)` in the level-4 pass and have level 5 reuse it.
  2. **`'nan'` leaked as a real instrument_type key — 26 keys beside 85 blank ones.** `astype(str)` renders a
     missing value as the literal `"nan"`, and the grouping key never consulted
     `_BLANK_INSTRUMENT_TYPE_SENTINELS` (which already contained `"nan"` — defined, but unused for grouping).
     Fix: normalise every null spelling to `""` in `_casefold_instrument_type_series`, so one "never stamped an
     instrument_type" shard is one cell rather than up to five.
  3. **`data_type` was never case-folded — 6 split groups** (`sports` `ODDS_MOVEMENT`/`odds_movement` and
     `ODDS_SNAPSHOT`/`odds_snapshot`; `prediction` `MARKET_LIFECYCLE`/`market_lifecycle`). Fix: new
     `_casefold_data_type_series`, applied at level 5 ONLY. Deliberately NOT applied to level 3
     `by_venue_data_type`: that dict's KEYS feed deployment-api's `/distinct-values/{asset_group}` drift panel,
     which case-sensitively tracks the in-flight uppercase migration — merging there would blind the panel to the
     drift it exists to surface. A test pins both halves of that asymmetry.

  **Denominator impact, stated as a dated change per W3's "never a silent edit" rule:** these three collapse 86
  duplicate cells, so the true distinct-shard count at this grain is **3,876**, not the 3,962 the artefact
  currently reports (nor the 3,960 the headline quotes). Per-status ROW totals are unchanged — this re-partitions
  cells, it does not drop shards: captured 58,494,203 / attempted_failed 9,648,732 / expected_unattempted
  51,892,497 / empty_confirmed 93,065,443, reachable denominator 120,035,432 on 2026-08-19. The corrected count
  reaches the artefact on the next nightly `measure-honest-coverage` cron run; this tranche does not launch it.

  **Also measured, NOT fixed here** (needs an operator ruling on denominator semantics, so it is a tracked todo
  rather than a silent edit): level 4 drops fully-retired keys via `_drop_fully_retired_nested` and level 5 does
  not, so the two levels still disagree about which shards EXIST even though they now agree on naming.

- 2026-08-20 — **T1 inbound #2 worked; T1's stated cause was wrong, the underlying defect was real and worse.**
  T1 reported three hand-rolled `KNOWN_CHAINS` literals in `instruments-service` that "will not receive the
  SCROLL/PLASMA fix". MEASURED: all three already contained SCROLL and PLASMA, so that specific claim does not
  hold. The real drift ran in BOTH directions and predates it: each copy was missing `ASTER` (a venue that is its
  own L1 — `…-ASTER` venues therefore never split) and carried a phantom `STARKNET` that UAC deliberately
  excludes (`EXTENDED-STARKNET` is a CeFi on-chain perp CLOB that must NOT be DeFi-split, per
  `engine/orchestrator/writers.py`'s `VENUE_TO_ASSET_GROUP` guard). `build_instrument_catalogue.py`'s comment
  claimed it "Mirrors the UAC `KNOWN_CHAINS` set" — it did not; that comment is corrected in place rather than
  left to mislead the next reader. All three now import the UAC set
  (`unified_api_contracts.registry.capability_declarations._defi.KNOWN_CHAINS`, the path every already-correct
  consumer in the repo uses). Verified after the change by importing the module and asserting
  `_CATALOGUE_KNOWN_CHAINS is KNOWN_CHAINS` → True, `ASTER` present, `STARKNET` absent. This is a real behaviour
  change to the catalogue read-side venue split, in the correcting direction.
