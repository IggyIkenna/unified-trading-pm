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

- [ ] [FROM-T5] P2. **7 `not_consumed` values from the epic's "No orphans" DoD item — 5 data_types + 3
      instrument_types, all in your repos.** Measured 2026-08-20 via the `/shard-utilisation-sweep` skill
      (registry-backed consumption verdict, never a delete suggestion) against `coverage.json` date=2026-08-20:
      registry vocabulary coverage confirmed adequate for tradfi (9/13, 69%) and prediction (2/4, 50%) before
      calling these absences meaningful — this is not disjoint-vocabulary noise like the DeFi/sports findings in
      the same sweep (those are separately noted as `unverified`, not orphans).

      **data_type**, absent from the registry's declared vocabulary for their asset_group:
      `tradfi/macro_result` (14 cells), `tradfi/yield_curve` (9), `tradfi/ohlcv_1d` (9), `tradfi/futures_chain`
      (2), `prediction/prediction_canonical_question_group` (4), `prediction/market_lifecycle` (4) +
      `prediction/MARKET_LIFECYCLE` (2, its own uppercase duplicate — worth checking whether that's a casing
      drift of the same value before treating both as separate orphans).

      **instrument_type**: `tradfi/nan` (63 cells), `tradfi/UNKNOWN` (1), `prediction/nan` (1) — the `nan`/
      `UNKNOWN` values read like a writer emitting a missing-value sentinel into a real column rather than a
      genuine orphaned category; check the writer before assuming any of these are dead data.

      T5 does not have write access to instruments-service/market-tick-data-service to investigate further. Full
      sweep output (all axes, incl. the DeFi/sports vocabulary-coverage gaps that are NOT orphans):
      `/plans/active/code_readiness_t5_readiness_observability_presentations_2026_08_19.md`'s "No orphans" todo.

      **PARTIAL 2026-08-20 — instrument_type half resolved, data_type half still open.** Traced via a dedicated
      investigation, not guessed: `tradfi/nan` + `prediction/nan` were a genuine WRITE-TIME defect —
      `market-tick-data-service/market_tick_data_service/engine/orchestrator/partitioned_writer.py`'s
      `_resolve_instrument_type_column()` cast an already-present `instrument_type` column via `.astype(str)` with
      no null guard, so a NaN/None/`pd.NA` cell rendered as the literal string `"nan"` and became a real
      hive-partition segment + manifest row_key value — the write-side counterpart of a gap
      `measure_honest_coverage.py`'s own `_casefold_instrument_type_series` already defended against on the read
      side. Fixed with `.fillna("")` before the cast, 4 new regression tests (null/NaN/pd.NA/unaffected-real-value
      cases), 39/39 passing. Evidence: `market-tick-data-service@79ce0c89`.
      `tradfi/UNKNOWN` is **NOT a defect** — confirmed sanctioned, documented vendor pass-through
      (`unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py:1089-1095`: Databento's
      `stype_out=UNKNOWN` for continuous/calendar-spread futures contracts, already in `CONTRACT_REGISTRY`); the
      `not_consumed` verdict here is a vocabulary-registry mismatch in the sweep's checked source
      (`VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` doesn't mirror `CONTRACT_REGISTRY`'s sanctioned `UNKNOWN`
      entries), not a data problem — worth a follow-up to the sweep tool itself if it keeps false-flagging this,
      not tracked as a new todo here since it's a single already-understood cell.
      **Still open**: the 5 `data_type` findings (`tradfi/macro_result`, `tradfi/yield_curve`, `tradfi/ohlcv_1d`,
      `tradfi/futures_chain`, `prediction/prediction_canonical_question_group`) and the
      `market_lifecycle`/`MARKET_LIFECYCLE` casing-drift question — confirmed the lowercase `market_lifecycle` is
      the real writer value (`instruments-service/instruments_service/engine/orchestrator/writers.py`'s
      `_write_market_lifecycle`, GCS prefix `market_lifecycle/by_canonical_group`); the uppercase variant's source
      was not located.

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
- [x] [OPERATOR] P0. **Rule on the sports league axis before it is built.** ✅ 2026-08-20 — **operator ruling**
      (recorded here in `/plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md`'s own Progress Log —
      answered via an interactive `AskUserQuestion` exchange, no separate issue doc; this todo's own text is the
      traceable record): **fold league_id into the FULL primary shard atom** (venue, instrument_type, data_type, league_id), not the
      lighter (venue, data_type, league_id) drill-down first proposed. Shipped as level 5e,
      `by_venue_instrument_type_data_type_league` — a dated supersession, not a silent edit: the coarser
      `by_venue_instrument_type_data_type` (level 5) keeps its exact prior shape/meaning; the one real in-workspace
      consumer of its nested shape (`unified-trading-pm`'s `shard_universe.py` `iter_shard_cells`/`detect_grain`,
      confirmed via workspace-wide grep — zero other hits) is unaffected and separately extended to recognise the
      new `"league"` grain. FIXTURES-excluded-from-count is still unbuilt — out of scope for this ruling, tracked
      separately if needed. Evidence: `instruments-service@6056d46d5c` (level 5e + 6 regression tests, 70/70
      passing), `unified-trading-pm@25b428ee8f` (shard_universe.py grain extension + 6 regression tests, 12/12
      passing) — verified live via `git log --oneline -1` against `origin/live-defi-rollout`, not assumed from a
      queued push.
- [x] [BACKEND] P0. Add `instrument_type` and `data_type` columns to the coverage payload. **T5's coverage dump
      blocks on this** — it can only report at `(venue, data_type)` grain until these land. Tell T5 when shipped.
      ✅ 2026-08-20 — **already live before this tranche started; verified by execution, not by reading the writer.**
      Loaded `gs://central-element-323112-honest-coverage/2026-08-19/coverage.json` through T5's own
      `shard_universe.py`: `by_venue_instrument_type` (172 `(ag, venue)` pairs) and
      `by_venue_instrument_type_data_type` (184 pairs) populated for all 5 asset_groups, `detect_grain()` →
      `"instrument_type"`, 3,962 cells at `(ag, venue, instrument_type, data_type)`. T5 told, in their plan's
      `## Inbound requests`, with the two caveats that make the finer grain honest. Evidence:
      `unified-trading-pm@89fab080bd`. The axes needed no code; making them honest did — next item.
- [x] [BACKEND] P0. Fix the mislabelled `grain` field. A wrong grain label silently misstates every denominator
      derived from it. ✅ 2026-08-20 — **fixed by T5** (this todo's outbound request), not this tranche directly:
      `derive_readiness.py`'s single `grain` key conflated the COVERAGE-SOURCE grain (`detect_grain()`'s output)
      with the ROW grain (always `venue_asset_group_mode`, unconditionally) — split into `coverage_source_grain`/
      `row_grain`. Verified by reading the actual diff, not trusting the commit message alone:
      `unified-trading-pm@065067f345` (code) + `@e1051d80dd` (T5 plan flip, "FROM-T2 grain-mislabel fixed").
      Re-checked for conflict with this session's league-grain work before shipping — `detect_grain()`/
      `iter_shard_cells()` are called generically (no hardcoded grain-value list), so the new `"league"` grain
      value flows through with zero further changes needed there.
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
- [x] [OPERATOR] P0. **Rule on whether level 5 should drop fully-retired keys like level 4 does.** MEASURED
      2026-08-20: `by_venue_instrument_type` (level 4) passes through `_drop_fully_retired_nested`;
      `by_venue_instrument_type_data_type` (level 5) does not. After the 2026-08-20 naming fix the two levels
      agree on what each shard is CALLED but still disagree on which shards EXIST. Level 5 is the shard atom
      `iter_shard_cells()` reads, so aligning it changes the published denominator — which is exactly why this is
      operator-gated and was not folded into the naming fix. Blocked on the ruling, not on code.
      ✅ 2026-08-20 — **Operator ruling (interactive session, this tranche's plan
      `/plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md` + `/plans/epics/system_readiness_master.md`
      § W3): yes, apply the same drop.** Shipped
      `instruments-service@977f4b3a1a` (ancestor-verified against `origin/live-defi-rollout`, content re-read to
      confirm `_drop_fully_retired_shard_atom` landed): level 5 (`by_venue_instrument_type_data_type`, the actual
      shard atom `iter_shard_cells()` reads) now drops a fully-retired `(instrument_type, data_type)` leaf, then
      cascades to drop the `instrument_type` entry if that empties it, then the `venue` entry if that empties it
      — same policy `_drop_fully_retired_nested` already applied at level 4 since 2026-08-14. 3 new tests proving
      the cascade at all three depths, plus that a MIXED leaf (some captured/expected_unattempted alongside some
      attempted_failed) keeps its real counts rather than being dropped. Per W3's "any denominator change lands
      as a dated supersession, never a silent edit", this SHRINKS the reachable denominator — dated here,
      2026-08-20 — and reaches the live artefact on the next nightly `measure-honest-coverage` cron run.
- [x] [BACKEND] P1. **Report coverage grain PER asset_group, or publish the hollow fraction beside the label.**
      MEASURED 2026-08-19: 1,973 of 3,962 cells (49.8%) carry a blank or `'nan'` instrument_type while
      `detect_grain()` reports `"instrument_type"` for the whole payload — `defi` 1,871/2,804 (66.7%), `tradfi`
      82/244 (33.6%), `prediction` 10/19 (52.6%), `sports` 10/822 (1.2%), `cefi` 0/73 (0%). A single payload-wide
      grain label overstates the breakdown available for half the corpus. Same failure mode as the mislabelled
      `grain` in the readiness dump (filed to T5, who owns that writer).
      ✅ 2026-08-20 — **took the todo's own "or" branch**: published `hollow_instrument_type_fraction` as a new
      additive field on every `by_asset_group[ag]` cell (fraction of level-5 cells with a blank/`"nan"`
      instrument_type; `None` — not `0.0` — when an AG has zero level-5 cells, so "no data" and "fully
      populated" can't be confused). 4 regression tests (half-blank, all-real, no-column, `"nan"`-string cases).
      Also directly benefits from this same session's separate `nan`-string write-time fix
      (`market-tick-data-service@79ce0c89`) — future runs should show the fraction trending down as that fix's
      effect accumulates. Evidence: `instruments-service@540a3bd94d`.
- [x] [BACKEND] P1. **Trace the 9 blank-venue `sports` cells to the writer that emits them.** MEASURED
      2026-08-19: 9 cells in coverage.json carry `venue == ""` (all `sports`, data_types `odds_movement`,
      `odds_snapshot`, `ODDS_MOVEMENT`, `ODDS_SNAPSHOT`, `ARBITRAGE_OPPORTUNITY`, each `empty_confirmed: 1`).
      They propagate into T5's readiness dump as 9 rows with an empty `venue`. Read-only diagnosis of the manifest
      writer path first — any manifest row repair is data movement and stays operator-gated.
      ✅ 2026-08-20 — **traced via a dedicated investigation, not guessed, then the WRITER bug fixed (code only,
      the 9 existing rows are unrepaired data movement, correctly left alone).** Root cause:
      `market-data-processing-service/market_data_processing_service/app/core/canonical_writer_shaping.py`'s
      `_venue_token_from_canonical_id` returned `""` (not `"UNKNOWN"`, its own sibling fallback's convention) when
      a sports instrument_id's bookmaker token (position 1) was missing/blank — `_resolve_empty_failed_shard_tuple`
      falls through to this helper whenever `input_venue` is falsy, so a genuinely-unresolvable venue got stamped
      as a blank string onto `empty_confirmed` manifest rows rather than the documented "UNKNOWN" sentinel. The
      four venue-restamp/migration scripts checked (`manifest_swap_venue_restamp_2026_07_27.py`,
      `manifest_swap_venue_restamp_candles_2026_08_03.py`, `league_id_relocation/manifest_swap_2026_07_22.py`,
      `migrate_sports_canonical_v9.py`) all filter on a SPECIFIC old venue string, so `venue==""` was categorically
      out of scope for every sweep — not "left behind," never targeted. `ARBITRAGE_OPPORTUNITY`'s cell is
      additionally a pre-2026-08-09-retirement leftover (`SportsArbitrageAdapter` retired, arb detection moved to
      features-service) that can no longer be produced going forward regardless. Fixed
      `_venue_token_from_canonical_id` to return `"UNKNOWN"` on the blank-bookmaker fallback, matching the sibling
      no-colon-at-all convention already used elsewhere in the same function; 2 regression tests updated/added.
      Evidence: `market-data-processing-service@857085e316`.

### W2 — data pipeline integrity (code only, no runs)

- [ ] [BACKEND] P0. Land the manifest canonicalisation and skip-logic CODE. Do NOT run the migration.
- [x] [BACKEND] P0. Build consolidator-freshness gating so a stale index loud-fails rather than serving stale
      coverage. SSOT: `/codex/05-infrastructure/manifest-consolidator-ssot.md`.
      ✅ 2026-08-20 — **already shipped, and it loud-fails BY DEFAULT.** Verified in code, not from the codex prose:
      `unified-trading-library/manifest_writer/_read_index.py:357` —
      `if fail_fast_legacy or (shards_exist and not _resolve_allow_stale_fallback()):` → raise. Two distinct
      `ManifestConsolidatorStaleError` raise sites (`:406`, `:422`) deliberately separate "staleness budget too
      tight for this bucket's cadence" (age < 5x budget) from "consolidator appears DOWN" (blob missing or far past
      budget), each carrying its own remediation. The per-VM recovery merge is opt-IN only via
      `MANIFEST_ALLOW_STALE_FALLBACK` — refused by default precisely because it can be a 12+ GB pandas heap
      (cefi: 1700+ shards → SIGKILL at startup). Live default confirmed:
      `manifest_consolidated_staleness_sec = 120`. A genuinely-empty bucket is correctly NOT treated as an outage.
      **Ownership note**: this mechanism lives in `unified-trading-library` — T1's repo, not one of this tranche's
      three. The todo was mis-scoped to T2; nothing was needed in instruments-service / MTDS / MDPS.
- [x] [BACKEND] P0. Build the orphan-shard consumption check — no shard stored that nothing consumes. Epic
      definition-of-done item. SSOT: `/codex/02-data/orphan-object-detection.md`.
      ✅ 2026-08-20 — **built and shipped as the `shard-utilisation-sweep` skill.**
      Evidence: `unified-trading-pm@d9a53d1d01` (`--isolated` quickmerge, ancestry-verified against
      `origin/live-defi-rollout`, landed content re-read to confirm). Two earlier non-isolated attempts on this
      shared checkout hit real-but-external gates: a `PendleConnector` reachability flap (confirmed transient — a
      standalone re-run passed moments later) and an archive-safety-ratchet violation already committed to origin
      4 days earlier inside a DIFFERENT live session's file (`kimi_gemma_provider_onboarding_2026_08_16.md`, not
      touched by this tranche). `--isolated` mode — which builds the commit from a private index against origin
      rather than this contended working tree — sidestepped both without needing to touch either. Also fixed a
      real gap the first attempt surfaced: this skill's `tests/` dir was unreachable by `unified-trading-pm`'s
      `PYTEST_UNIT_DIR`, so `cursor-configs/skills/` was added to `scripts/quality-gates.sh`'s `PYTEST_UNIT_DIR=`
      list, verified against the fleet coverage baseline before shipping. The existing sweeps
      (`migration_orphan_sweep.py`, `candle_orphan_sweep.py`, MTDS's sports fork) all run GCS→manifest ("is this
      stored object manifested?"); nothing ran the other direction. This does: a CONSUMPTION verdict per declared
      venue / data_type / instrument_type / chain, resolved by IMPORTING the real registries
      (`VENUE_TO_ASSET_GROUP`, `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`, `KNOWN_CHAINS`) rather than inferring
      from grep counts, with `unverified` as a first-class verdict. Reuses `shard_universe.py` per the epic's
      consistency constraint, so it cannot disagree with the two shipped dumps about the denominator. Always exits
      0 — a gate that can legitimately answer `unverified` must not fail a build. 11 tests.
      **The safety constraint earned its place — the naive version cried wolf twice on live data, and both guards
      are regression-tested:**
      - **95 FALSE venue orphans**, including `AAVE_V3`, `LIDO`, `MORPHO`, `ETHERFI` at 50+ live cells each.
        Measured cause: `VENUE_TO_ASSET_GROUP` keys DeFi in the GLUED `PROTOCOL-CHAIN` form (135 of its 209
        entries, all glued) while the manifest carries the BARE protocol with chain in its own column — the two
        are on opposite sides of the venue/chain canonicalisation cutover. Now CONSUMED, with the cutover
        mismatch reported as its own finding. Venue axis went 85→158 consumed, 95→22 not_consumed.
      - **86 FALSE instrument_type orphans.** `defi` has ZERO entries in the registry; `sports` declares 5
        odds-SHAPE types against a manifest carrying ~84 MARKET types (`MATCH_ODDS`, `OVER_UNDER_2_5`,
        `SOCCER_EPL`) — one coincidental shared token (`odds`) was enough to condemn the other 83. Fixed with a
        proportional guard: the registry must cover a MAJORITY of what an asset_group actually carries before
        absence means anything (cefi 100% → meaningful; sports 1% → `unverified`). Went 86→**3** not_consumed.
      **What it found that is real** (verdicts, not delete suggestions): `AAVEV3` bare-alias ghost venue still
      carrying 25 cells; **`BARCHART` — a RETIRED vendor — still carrying 10 cells**; a literal `UNKNOWN` venue (3);
      `tradfi/nan` instrument_type at 63 cells (the same `'nan'` leak fixed upstream in the coverage writer this
      session); and the 10 chains outside `KNOWN_CHAINS`, correctly reported `unverified` rather than condemned.
      **Priority note**: the epic lists this as `[SKILL] P1`, not the `[BACKEND] P0` this todo carried.
- [ ] [BACKEND] P1. **BLOCKED-UPSTREAM (T1/UTL)** — Fix the manifest-writer per-VM shard flush that does a full
      read-merge-reserialize-upload on every debounced flush — past ~1M rows the flush outlasts the debounce
      interval and the VM stalls. CODE only. Evidence:
      `/plans/active/issues/manifest_writer_per_vm_shard_flush_scales_with_shard_size_2026_07_28.md`.
      **Reason 2026-08-20**: the manifest writer is
      `unified-trading-library/unified_trading_library/manifest_writer/` — T1's repo, not one of this tranche's
      three. The issue doc declares `repos: [unified-trading-library, market-tick-data-service]`, and every
      remaining todo is UTL-side: the append-only "delta shard" pattern (P2), a reworded P3, and a `[SCRIPT] P3`
      verification explicitly gated on "once either fix above ships". There is no instruments-service / MTDS / MDPS
      change available to make here. Filed to T1. The issue's own priority is P2, below this todo's P1 framing.
- [ ] [BACKEND] P1. Fix blocking GCS writes on the event loop, cross-asset-group. Evidence:
      `/plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md`.
      **PARTIAL 2026-08-20 — the headline fix is SHIPPED; what remains is a P3 residual tail.** Verified
      `market-tick-data-service@eeade63b0c` ("perf(defi): fan out evm_defi_collectors/liquidations/
      liquidation_events via ParallelPerSymbolRunner") is an ANCESTOR of MTDS HEAD via
      `git merge-base --is-ancestor` — 3 of 8 sites, landed 2026-08-15. The issue's remaining todos are all **P3**,
      not P1: async-ify the collection loops in `cli/handlers/dex_swaps_handler.py` (`_collect_all_protocols`),
      `gas_fee_handler.py` (`_collect_evm_chains`), `vault_share_price_handler.py` (`_collect_vault_rows`),
      re-assess `lst_rates_handler.py` for whether any per-shard fan-out axis exists at all, and fix 2 blocking
      writes in sync functions. All four handler files confirmed present here, so this residual IS T2-owned — kept
      OPEN, at its real P3 weight, behind this tranche's outstanding P0s.
- [x] [BACKEND] P1. Ensure `expected_unattempted` is materialised by the WRITER and never re-derived downstream.
      ✅ 2026-08-20 — **already satisfied.** `instruments_service/engine/orchestrator/process_write.py:604` calls
      `manifest.record_expected_unattempted(...)` at write/pre-flight time — the writer-side materialisation the
      todo asks for. Checked the downstream reader for the violation this guards against (re-deriving the status
      instead of trusting it): `scripts/measure_honest_coverage.py` has ZERO functions that recompute or infer
      `expected_unattempted` — it only reads the pre-stamped `capture_status` column via `_count_statuses` and the
      four-state groupby. Nothing to change in this tranche's three repos.

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
      **NOTE 2026-08-20 (T2, `/autonomous`) — do not duplicate, check status first next session.** Pulled origin
      mid-session and found the master plan (7 open / 3 done) has since been fanned out into 5 fresh
      `assigned_vm: planning` (AO-dispatched) per-asset-group batches: `cefi_venue_smoke_batch1_2026_08_20.md`,
      `defi_venue_smoke_batch1_2026_08_20.md`, `prediction_venue_smoke_batch1_2026_08_20.md`,
      `sports_venue_smoke_batch1_2026_08_20.md`, `tradfi_venue_smoke_batch1_2026_08_20.md` (each with a
      `_finalize` companion). Each batch's `repos:` spans beyond this tranche's 3 (also
      unified-api-contracts/features-service/execution-service) — genuinely cross-tranche, AO track, not
      something to grab mid-flight without first checking whether an AO worker already has it in progress. Not
      investigated further this session (discovered near session end) — next session: check each batch's
      current open/done state before doing any work here, to avoid racing an AO worker on the same files.
- [x] [BACKEND] P0. Close the CeFi and TradFi G1-G5 gate execution CODE paths. Evidence:
      `/plans/active/instruments_cefi_g1_g5_gate_execution_2026_07_24.md`,
      `/plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`.
      ✅ 2026-08-20 (T2, `/autonomous`) — **CeFi doc: fully closed, 0 open todos.** G2/G3/G3b/G4 were already
      SIGNED OFF by prior sessions; G1's own 4 named blocking defects (G1.1-G1.4) plus a follow-up finding were
      already done, and this session closed the last real G1-scope item — EXTENDED's CF-11 honest-absence
      violation (raise-on-fetch-failure fix, `instruments-service@c58802b9cc`) — then flipped the G1 rollup
      checkbox itself, which had never been flipped despite every child completing.
      **TradFi doc: CODE paths done; 2 residual items are DATA-MOVEMENT, correctly out of this tranche's "no
      backfills/manifest migrations" standing rule** — both already extracted into their own dedicated,
      currently-active AO-dispatch plan (`/plans/active/tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md`,
      2 open / 1 done), not duplicated here. Nothing further actionable in either doc from this tranche's 3
      repos.
- [x] [BACKEND] P1. Fix the CeFi `instrument_type` casing active-writer regression. Evidence:
      `/plans/archive/issues/cefi_instrument_type_casing_active_writer_regression_2026_08_17.md`.
      ✅ 2026-08-20 — **the writer-side CODE fix is shipped and live; everything left is data movement.**
      `market-tick-data-service@c07cc70e93` verified an ANCESTOR of MTDS HEAD (`git merge-base --is-ancestor`),
      not taken from the checkbox. Root cause it closed: `_tradfi_manifest_shard.py::_tradfi_manifest_itype`
      hardcoded `if VENUE_TO_ASSET_GROUP.get(venue) != "tradfi": return itype`, so every CeFi venue fell straight
      through and the lowercase `instrument_type` landed verbatim in the manifest row-key — even though UTL's
      shared `canonicalize_manifest_instrument_type` already shipped a `cefi` mapping table that was simply never
      reached. The fix calls that canon unconditionally and lets its own asset_group gating decide, including the
      bundle-grain exclusion set (`futures_chain`/`options_chain`/`combo`/`combo_chain`/`continuous_future` pass
      through unchanged). GCS path-building still uses the lowercase value verbatim — only the manifest column
      casing changed. **The 3 remaining todos on that issue are all `[DATA] P2` and out of scope here**: review the
      `canonical-migration-cefi-itype-casing-apply-*` dry-run, launch the full `--apply` VM, trigger the
      consolidator rebuild, then re-run the audit to confirm a 0 residual. That is exactly the "relaunch the VM /
      apply the delete" class this tranche leaves to the operator. Note the fix stops NEW lowercase rows being
      minted; it does not retroactively fix the ~39,286-row existing residual.
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
- [x] [BACKEND] P2. Fix the AAVEV3 bare-alias enumerator CODE (already root-caused — duplicate dict key plus missing
      alias canonicalisation). The 46,300 bad `empty_confirmed` manifest rows stay operator-gated, not yours.
      ✅ 2026-08-20 — **verified in place by reading the code, not by trusting the issue's checkbox.** Both halves of
      the root cause are closed in `instruments-service/scripts/enumerate_expected_universe.py`'s
      `_yield_v2_defi_pre_launch_rows` (line ~1457): (1) alias canonicalisation —
      `venue_label = VenueMapping._canonicalise_defi_protocol_spelling(protocol.upper())` maps `AAVEV3` → `AAVE_V3`,
      matching the per-instrument v2 path; (2) the duplicate-key guard — an `_emitted_chain_venues` set with
      `if (chain_upper, venue_label) in _emitted_chain_venues: continue`, so the legacy no-underscore alias key in
      `PROTOCOL_LAUNCH_DATES` can no longer re-emit every row its canonical twin already emitted. The inline comment
      cites this exact issue doc. The issue's two remaining todos are `[OPERATOR] P2` (purge the 46,300 rows via the
      human-gated `--apply` delete) and `[DESIGN] P3` (whether `chain_env.py` should keep alias dict-keys at all) —
      neither is this tranche's, exactly as this todo already stated.

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
- [x] [BACKEND] P1. Resolve the B21 distinct-values non-canonical live finding. Evidence:
      `/plans/active/issues/b21_distinct_values_noncanonical_live_2026_08_18.md`.
      ✅ 2026-08-20 — **nothing further actionable from this tranche's 3 repos.** The issue doc has been
      extensively worked by other sessions: 5 of 9 sub-todos done (defi venue/data_type root-causes, sports
      column-swap bug, sports FOOTBALL/ODDS_API/UNKNOWN venue-axis leakage — real MTDS/MDPS writer fixes,
      several already ancestor-verified on `live-defi-rollout`). The 4 remaining sub-todos are explicitly
      scoped to `unified-api-contracts` (registry extensions for confirmed-legitimate bookmaker/instrument_type/
      data_type spellings — T1's repo, not mine) or are manifest-row reconciliation (`venue=UNKNOWN` residual
      rows — data movement, operator-gated per this tranche's standing rules). Nothing in
      instruments-service/market-tick-data-service/market-data-processing-service remains open on this issue.
- [x] [BACKEND] P2. Decide and implement the MTDS WS venue-fallback removal for Polymarket.
      Evidence: `/plans/active/issues/mtds_ws_venue_fallback_removal_polymarket_decision_2026_08_17.md`.
      **Reason 2026-08-20**: the issue's sole todo is `[OPERATOR] P3` — a binary product/architecture call the doc
      itself says it "doesn't have the authority to make" (accept polymarket's two-connector dual-casing split as
      permanent, vs. keep a narrower documented fallback). Two independent `na-eligibility-audit` passes (08-17,
      08-19) both ruled KEEP-NA valid. Not this tranche's decision to make.
      **What I did add — the doc's factual premise is now VERIFIED, so the decision is de-risked**: both connectors
      register under their OWN canonical-cased key and each resolves via `resolve_ws_feed_venue_key`'s FIRST branch
      (`if venue in registered_keys: return venue`), so neither depends on the `.lower()`/`.upper()` fallback today.
      Evidence: `live/connectors/polymarket_ws.py:322-325` registers `venue="polymarket"` (auto-registers on import,
      line 331); `live/connectors/polymarket_clob_ws.py:537-540` registers UPPERCASE `"POLYMARKET"` with a docstring
      stating it is keyed that way "so it is distinct from" the Gamma-API one. Choosing (a) therefore requires zero
      registration changes and cannot break polymarket dispatch. Note `WS_FEED_CONNECTOR_FACTORIES` is EMPTY at
      import time (registration is lazy, on connector-module import), so a static probe of the dict proves nothing —
      the registration call sites are the evidence.
      ✅ 2026-08-20 — **Operator ruling (interactive session, source doc
      `mtds_ws_venue_fallback_removal_polymarket_decision_2026_08_17.md`): remove the fallback fleet-wide.**
      Shipped
      `market-tick-data-service@3c142f0d4a` (ancestor-verified, content re-read to confirm). `resolve_ws_feed_venue_key`
      is now EXACT-MATCH ONLY — the `.lower()`/`.upper()` fallback branches are gone; the function body is a
      single ternary. Confirmed safe for the venue the decision was actually about: both Polymarket connectors
      register under DIFFERENT canonical-cased keys (`polymarket_ws.py` registers lowercase `"polymarket"`,
      `polymarket_clob_ws.py` registers UPPERCASE `"POLYMARKET"`) and both resolve via exact match with zero
      registration changes. Updated the 2 pre-existing tests that asserted the OLD fallback behavior to assert
      the new exact-match-only contract instead of silently deleting them, and added 2 new tests specific to
      Polymarket: both connectors resolve post-removal, and a `"POLYMARKET"` lookup against only the lowercase
      key now correctly returns `None` instead of silently resolving to the wrong connector via `.upper()` — the
      exact class of mix-up removing the fallback closes. 39 tests passed.
- [x] [BACKEND] P2. Confirm the MDPS `--force` subprocess fix is live and that only a data relaunch remains — that
      relaunch is out of scope. Evidence:
      `/plans/active/issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md`.
      ✅ 2026-08-20 — **confirmed live in the shipped tree.** `market-data-processing-service@e9f9819f`
      ("fix(process_handler): forward --force to per-date subprocess spawns") is an ANCESTOR of current HEAD —
      verified with `git merge-base --is-ancestor`, not by reading a changelog. The forwarding is present at both
      spawn sites: `cli/handlers/process_handler.py:695-696` (`argv.append("--force")`) and `:776-777`
      (`cmd.append("--force")`). Its own commit message states the defect it closed: `_run_date_as_subprocess`
      built the child cmd from only `--operation/--mode/--start-date/--end-date`, silently dropping the parent's
      `--force`, so every multi-day `process --force` backfill ran with `force=False` on each child. Only the data
      relaunch remains, and that is operator-gated data movement, out of scope per this tranche's standing rules.
- [x] [BACKEND] P2. Ensure `source=` is threaded through every `record_captured()` call — it is crosscutting and
      required. SSOT: `/codex/02-data/pipeline-mode-partition.md`.
      ✅ 2026-08-20 — **already satisfied, and "every call" is the wrong bar.** Ran the shipped QG checker
      (`check_tradfi_source_explicit_at_record_captured.py`, STEP 5.64) against all three owned repos:
      **0 baselined occurrences and 0 new occurrences in each**, with `tradfi_source_explicit_baseline.yaml` at
      `entries: []` — the legacy backlog is fully cleared, not merely parked. **Scope of that claim, stated
      precisely**: the rule is registry-driven, not universal
      (`data_source_provenance_all_asset_groups_2026_06_01.md` Phase 6). The UTL writer AUTO-STAMPS the sole
      external source for single-source cells and only requires an explicit `source=` when
      `source_required(asset_group, data_type)` is True — verified live: `('cefi','trades')` and
      `('prediction','trades')` → True, `('tradfi','ohlcv')`, `('defi','lending_indices')`, `('sports','odds')` →
      False. Demanding `source=` at every callsite would false-fail the single-source ones that legitimately rely
      on auto-stamp. **What the static check does NOT cover** (so this is not claimed): it skips `scripts/` and
      `tests/`, and cannot resolve callsites whose category/data_type are runtime variables. The backstop for
      those is the runtime gate — `MissingSourceError`, verified importable from UTL and raised from
      `manifest_writer/_writer_captured.py` / `_writer_record.py`.

### Close-out

- [x] [DATA] P1. **Relaunch the CeFi itype-casing dry-run with reduced concurrency — the 2026-08-20 dry-run
      OOM-killed (exit 137) after ~19 min on a dedicated `e2-standard-16`, `--workers 16`.**
      ✅ 2026-08-20 — **DONE, full chain completed: dry-run → apply → re-audit, all clean.** Reduced concurrency
      alone (`--workers 4`) was NOT sufficient — a second attempt on the same `e2-standard-16` also OOM'd (see
      the issue doc's timing correction: it ran pre-fix code, so this doesn't cleanly indict worker-count
      alone). What actually worked: slot-18's memory-bound streaming fix
      (`market-tick-data-service@bccf8177ff`) + `MACHINE_TYPE=e2-highmem-16` (128GB) + `--workers 4`. Dry-run
      (`cefi-itype-casing-apply-rw-20260820-181447`) completed clean: `Grand total instrument_type values
      would be normalized: 39286 (collisions_dropped=8899)` — exact match to the independently re-measured
      baseline. `--apply` (`cefi-itype-casing-apply-rw-20260820-185429`) then completed clean on the same
      config: `rc=0`, backup written, manifest re-uploaded, `Grand total instrument_type values normalized:
      39286` — exact match. Live re-audit
      (`market-tick-data-service/scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`, run
      directly — a column-projected read, no VM needed) confirms **zero lowercase casing-variant rows remain**.
      Issue doc fully closed and archived:
      `/plans/archive/issues/cefi_instrument_type_casing_active_writer_regression_2026_08_17.md`. Evidence:
      `deployment-service@9ae1a78e9e` (the launcher), VM run.log content quoted above, full Progress Log in the
      archived issue doc.
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
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
