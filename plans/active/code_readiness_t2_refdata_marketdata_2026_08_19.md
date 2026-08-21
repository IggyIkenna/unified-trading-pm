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

### Walkthrough feedback 2026-08-21 — refdata/coverage cluster (operator feedback on platform-external-api-walkthrough.html)

- [ ] [BACKEND] P1. **Kalshi perp — DATA-ONLY repoint, PROCEED (operator ruling 2026-08-21, final).** Wire
      RSA-PSS auth from existing GSM secrets (kalshi-api-key-id + kalshi-private-key-pem — MEASURED 2026-08-21:
      HTTP 200 with real perp market data on `external-api.kalshi.com/trade-api/v2/margin/markets`), repoint
      `kalshi_perp.py` enumeration to the margin host, flip `_REPOINT_PENDING`, keep the write-guard, discover
      the real funding-rates subpath (the docstring's literal path 404s), update the stale BLOCKED-CREDENTIALS
      docstring claim. Never re-enable against the events host. An EARLIER same-day hold ("auth probe ≠ perps
      trading rights, do not repoint") applied before the operator distinguished the data path — it is
      SUPERSEDED for data capture and remains in force ONLY for TRADING integration, which stays gated on the
      member-by-member perps rights signup.
- [x] ✅ [AGENT] P1. Classify the sports bookmaker roster for the operator (NOT for the artefact): for each of the
      27 kept books, is it (a) an odds-api bookmaker, (b) covered by the Unity central-wallet integration, or (c)
      neither — legacy arbitrage-research leftovers. Deliver the (c) list as a removal proposal; removal itself is
      operator-gated. Artefact side (T5): sports data types are odds, arbitrage_opportunity,
      odds_horizon_bucket, trades, trades_inplay; execution = Unity integration central-wallet, "coming soon —
      available faster on demand".
      **2026-08-21 — built the missing clean list, classified all currently-kept venues.** Full table + evidence:
      `/plans/active/issues/sports_bookmaker_roster_classification_2026_08_21.md`. The "27" is a stale 2026-08-08
      snapshot; the CURRENT kept roster is 39 (27 original + 4 Betfair-family/Pinnacle + 8 Unity child books added
      2026-08-17, after the count was taken) — all 39 classified. 25 actively odds_api-fetched, 9 Unity-covered (1
      dual-covered), 4 **HIGH-confidence removal candidates** (BETOPENLY, NOVIG, ONEXBET, PROPHETX — canonical
      token + odds_api key exist but were never wired into the live fetch scope, zero manifest presence of any
      kind in the 2026-08-20 coverage.json, no Unity coverage — arbitrage-research vintage), 2 LOW-MEDIUM
      confidence flags (BETMGM, BETWAY — same unwired pattern but some real captured rows, an operator judgment
      call rather than a clean removal). 2 Unity-roster contradictions surfaced, not resolved (code SSOT vs
      `sports_master.md`'s historical vision doc disagree on PINNACLE/CROWN). Operator + follow-up todos filed in
      the issue doc, not here.
- [ ] [BACKEND] P2. Unattributed manifest tokens (24 in the 2026-08-19 manifest, incl. 76 pre-canonical
      bare-protocol DeFi tokens in the wider decomposition): land the manifest-side attribution/canonicalisation
      CODE so the "Unattributed" bucket disappears from client-facing surfaces (migration run itself stays out
      of tranche scope). Chains without data (e.g. bitcoin mother-chain): get the connectors in and prove data
      acquisition so the chain appears canonically, per operator feedback.
      **BLOCKED 2026-08-21 — plan-conflict found, not shipped as code.** `/plans/active/state_fabric_artefacts_2026_08_20.md`
      § "T2 — the 24 unattributed tokens (investigation complete)" already investigated this exact 24-token set
      same-week and reached a **contrary verdict**: all 24 are real, well-formed `PROTOCOL-CHAIN` DeFi venues in
      genuine `DEFI_VENUE_PHASE == "pipeline"` status (none malformed/duplicate/manifest-artifact);
      `VENUES_BY_ASSET_GROUP["defi"]` is deliberately live-phase-only by design. That doc's own prescribed fix is
      explicit and DOC-only: relabel the bucket "DeFi — pipeline phase, not yet live" and **do NOT add these 24 to
      `VENUES_BY_ASSET_GROUP["defi"]`** — new attribution/canonicalisation CODE here would directly produce the
      "misrepresent pipeline venues as backfilled" outcome that doc warns against. Not force-shipped without
      reconciling the two docs first (findings-triage HARD RULE: outside-plan ambiguous → diagnose both sides,
      don't silently pick one). Bitcoin mother-chain connector sub-item is a genuine net-new adapter build,
      untouched this pass — split out below.
      - [ ] [BACKEND] P2. Reconcile this todo against `state_fabric_artefacts_2026_08_20.md`'s T2 finding before
            either doc's box flips again — either the DOC-relabel there supersedes this CODE ask, or an operator
            ruling says client-facing surfaces additionally need a resolver-side fallback into the phase-aware
            DeFi venue registry (not a manifest rewrite).
      - [ ] [BACKEND] P2. Bitcoin mother-chain connector: build the connector(s) and prove real data acquisition
            so `bitcoin` appears canonically on the chain axis (currently a chain-without-data gap per operator
            feedback) — instruments-service and/or market-tick-data-service, whichever owns chain-connector
            registration for BTC.

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
      **MEASURED 2026-08-21 (T2, general-purpose sub-agent investigation, evidence-cited)** — the remaining 3
      surfaces, one at a time:
      - **Writer vs projection: CONSISTENT.** `unified-trading-library`'s real dedup/shard key
        (`manifest_consolidator.py:571-585` `_BASE_DEDUP_COLS`+`_OPTIONAL_DEDUP_COLS`, mirrored
        `manifest_writer/_read_index.py:38-50`) and the MTDS sports-odds writer
        (`market-tick-data-service/.../manifest_finalize.py:400-497`) both agree with the projection: `league_id`
        is a real splitting key, `instrument_type` is a uniform non-splitting `"odds"` constant for sports (matches
        the codex's own "not a shard axis" ruling), `fixture_id` is display-only everywhere, never in the dedup key.
        No fix needed.
      - **Gate vs projection: DIVERGENT, real, still open — NOT closing this session.** The Layer-1
        enumeration-completeness gate (`scripts/check_enumeration_completeness.py::_build_enumerated_tuples`,
        `scripts/expected_universe.py::_expected_sports`) still computes EXPECTED/ENUMERATED at the coarser
        `(venue, instrument_type, data_type)` 3-tuple grain — never extended when level 5e folded `league_id` in.
        A venue with one league fully captured and every other league untouched still reads
        `instrument_gates_download: false` (falsely "complete enough to trust") for that venue. Root cause is
        NOT a quick code fix: closing it needs a new authoritative "expected leagues per bookmaker venue"
        source, which does not exist anywhere today (checked `unified_api_contracts.registry.sports_per_source_rules`
        — a different surface, reference-data sources not MTDS odds venues; checked
        `market-tick-data-service/.../adapters/sports/_league_request_resolution.py` — per-adapter fetch-time
        scoping, e.g. `odds_api_adapter.py`'s own `_candidate_leagues`, not a shared cross-venue registry).
        Fabricating one from observed data would risk manufacturing FALSE holes for leagues a venue never actually
        offers — exactly the dishonesty this system exists to prevent. Split out as its own todo below rather than
        forced through half-measured. Also fixed the stale codex banner that still called this "STILL OPEN" for the
        projection half after it shipped: `/codex/02-data/honest-coverage-model.md`.
      - **UI vs projection: minor, non-fabricating gap, cross-tranche.** `deployment-ui/src/components/HonestCoverageCard.tsx:135`
        faithfully passes through the gate's flag (inherits its blind spot, introduces no NEW disagreement).
        `ShardDetailModal.tsx`'s coordinate type has no `league_id` field, so it can't express a league-scoped
        single-shard drilldown — but `deployment-api/deployment_api/services/data_status_drilldown/_core.py:201-361`
        already carries `league_id` end-to-end, just not wired into `ShardDetailModal`'s own route/type. Split out
        below as a cross-tranche note (deployment-api + deployment-ui are T5-adjacent, not T2-owned).
      Leaving this box unchecked — genuinely partial, not closeable this session (2/3 remaining surfaces are either
      real-but-blocked-on-missing-authority or outside T2's ownership).
- [ ] [BACKEND] P1. **BLOCKED — missing authority, not missing code.** Extend the Layer-1 enumeration-completeness
      gate (`instruments-service/scripts/check_enumeration_completeness.py`, `scripts/expected_universe.py::_expected_sports`)
      to a `(venue, instrument_type, data_type, league_id)` grain for sports, split out of the shard-atom-identity
      todo above (2026-08-21 investigation). Needs a new authoritative "expected leagues per bookmaker venue"
      source first — none exists (`unified_api_contracts.registry.sports_per_source_rules` is a different surface;
      each MTDS odds adapter, e.g. `odds_api_adapter.py`, resolves its own league scope ad hoc). Either: (a) an
      operator/design decision on what defines "expected" per venue (e.g. formalize each adapter's own
      unscoped-fetch league set — `odds_api_adapter`'s is `LeagueClassificationRegistry.get_prediction_leagues()`
      — into a shared per-venue registry), or (b) explicitly rule the gate stays coarser-grained by design and
      close this as WON'T-FIX with that reasoning recorded. Do not fabricate an expected-leagues list from observed
      data — that risks manufacturing false holes for leagues a venue never offers.
- [ ] [FROM-T2, for T5/deployment-api] P2. Wire `league_id` through `ShardDetailModal.tsx`'s coordinate type
      (`deployment-ui/src/components/ShardDetailModal.tsx`) and its backing route
      (`deployment-api/deployment_api/types/shard_detail.py`), split out of the shard-atom-identity todo above
      (2026-08-21 investigation). The plumbing already exists one layer up
      (`deployment-api/.../services/data_status_drilldown/_core.py:201-361` carries `league_id` end-to-end) — this
      is wiring it into the single-shard drilldown modal, not new design. Low severity: the modal doesn't assert
      anything false today, it just can't express a league-scoped drilldown yet. Cross-tranche — deployment-api/
      deployment-ui are outside T2's owned repos (instruments-service, market-tick-data-service,
      market-data-processing-service, + the documented deployment-service carve-out).
- [x] ✅ [BACKEND] P0. Make honest coverage measurable on EVERY axis and granularity, each figure carrying its
      denominator and date. This is the epic's own definition-of-done item. SSOT:
      `/codex/02-data/honest-coverage-model.md`.
      **FINDING 2026-08-20 (T2, `/autonomous`) — today's daily rollup OOM'd, so coverage is currently
      UNMEASURED, not just incomplete on some axis.** Ran `launch-measure-honest-coverage-vm.sh` (the
      SSOT owner per the script's own docstring) to pick up this session's shipped code (league fold-in,
      hollow-fraction). Result: `measure-honest-coverage-20260820-205216` (default `e2-highmem-8`, 64GB)
      OOM-killed (`exit_code=137`) ~4.5min into loading DeFi's manifest (161,691,460 rows — this script's own
      header comments document a LONG history of exactly this class of OOM as defi's manifest has grown,
      already forcing 2 prior machine-type escalations: `e2-standard-4` → `e2-highmem-4` → `e2-highmem-8`,
      the last one specifically because defi crossed ~158M rows on 2026-08-12). cefi's own Layer-1/projection
      pass completed cleanly first (30.8M rows) — the kill landed specifically on defi's larger load. Cannot
      yet rule out this session's own level-5c/5d/5e chain/league joins (3 new O(n) groupby projections, each
      producing a result set roughly proportional to defi's higher cardinality) as a contributing factor on
      top of the pre-existing growth-driven pressure, vs. this being purely the SAME recurring class already
      documented — relaunched at `e2-highmem-16` (128GB).
      **RESOLVED 2026-08-20 — succeeded, and it was never actually stuck.** Two launcher-side false starts
      first (both this session's own known stale-tarball freshness-check false-negative, self-resolving on
      retry — `unified-api-contracts`/`market-tick-data-service` pattern recurring for `deployment-service`
      this time). The real run (`measure-honest-coverage-20260820-212202`) then appeared to stall after
      loading defi's manifest — 12+ minutes of only `PIPELINE_HEARTBEAT` lines, past the launcher's own 20min
      poll-and-give-up window (which correctly reported FAILURE rather than a blind success, per its own
      design). Watched it directly rather than assuming either outcome: `gcloud compute instances describe`
      confirmed the VM itself was still `RUNNING` (not OOM-killed, no `exit_code=137`), and a longer watchdog
      confirmed it was making real, if slow, progress — cefi finished ~20:33, defi's heavier computation (5
      projection levels including this session's 3 new joins, over 162M rows / 82M reachable) simply took
      until sometime before 20:55, then sports+prediction finished quickly after. **`rc=0`,
      `DEPLOYMENT_COMPLETED`, `gs://central-element-323112-honest-coverage/2026-08-20/coverage.json` written
      — a genuine success, not a stall or an OOM.** Live reachable-coverage: cefi 47.40%, defi 36.61%,
      tradfi 86.95%, sports 99.26%, prediction 92.86%. This IS visible on deployment-api's
      `/data-status/honest-coverage` route (deployment-ui's data-status tab) now — the operator's original ask
      for this session. Real signal for a future pass, not urgent: the `--asset-group all` run now takes
      ~35-40 minutes end-to-end (vs whatever it was before this session's 3 new projection levels landed) —
      worth profiling if it keeps growing, but not a bug today.
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

- [x] ✅ [BACKEND] P0. Land the manifest canonicalisation and skip-logic CODE. Do NOT run the migration.
      **2026-08-21 — investigated (general-purpose sub-agent, exhaustive), no open referent found; closing rather
      than carrying an un-scopeable placeholder forward.** This todo carried no SSOT link, asset_group, or
      issue-doc reference; T2's own frontmatter (`depends_on`/`supersedes`/`related`) has no link to any of the 5
      per-AG canonicalisation closeout plans either — it reads as a generic placeholder for the canonical-migration
      *program* (`/codex/02-data/cross-asset-canonical-target-ssot.md` §12), typed without checking what remained
      open. Grepped all 5 (`cefi`/`tradfi`/`defi`/`prediction`/`sports`) `*_consolidated_closeout_2026_07_18/19.md`
      plans plus the cross-cutting closeout for open canonical/migration/skip-logic todos landing in T2's 3 repos:
      - cefi, tradfi, prediction: zero open hits.
      - defi: the one open item is `delete_migrated_defi_markers_2026_07_23.py --apply` — the CODE already shipped
        (`market-tick-data-service@a65117eb`); only the gated **run** remains, and T2 does not run migrations.
      - sports: the referenced §11c issue doc
        (`plans/archive/2026_08/issues/instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03.md`)
        is `status: resolved`, all 13 todos `[x]` — the writer fix + `league=`-aware migration-tool shape
        extension shipped as `instruments-service@ba87cc32`, re-verified live on `main`.
        `sports_taxonomy_p2_migration_2026_08_08.md` (the actual sports manifest-canonicalisation migration) is
        also fully `[x]`. The closest real "skip-logic" match — `check_shard_freshness`'s ODDS_API-sentinel-collision
        bug — is fixed (`market-tick-data-service@362e64e3`), though the underlying function lives in
        `unified_trading_library/manifest_writer/_queries.py` (T1's repo, mirroring the sibling consolidator-freshness
        todo above that was already found mis-scoped to T2 for the same reason).
      Nothing left to build in T2's 3 repos under this heading. If the operator meant a SPECIFIC migration not
      captured by any of the above, re-open with a named asset_group/SSOT so it can actually be scoped.
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
      **PARTIAL 2026-08-21 — `lst_rates_handler.py` re-assessed and fixed; 3 sub-items remain open.** Found a
      real, worth-it fan-out axis the prior pass's "re-assess" correctly left undecided: `_collect_evm_lst_rows`
      (11 EVM LST tokens, each a blocking `web3.eth.call` via `_query_rate_with_retry`) and its sibling
      `_collect_evm_extended_rows` in `_lst_extended_rates.py` (multi-chain, similar count) were both plain
      synchronous `for` loops inside the async `process()` path — the exact class this issue tracks. Converted
      both to `async def`, fanning out per-token queries via `asyncio.to_thread` + `asyncio.gather` under a
      `Semaphore(8)` bound (conservative cap for a third-party RPC provider, not a headroom limit). Preserves
      exact row/error semantics (per-token failures still isolate via `evm_errors`/per-item skip, never abort the
      batch). New regression test proves the fix, not just non-regression:
      `test_evm_lst_rows_queries_concurrently_not_sequentially` stubs `_query_rate` with a real `time.sleep(0.05)`
      and asserts wall-clock stays near ONE sleep rather than N — fails against the pre-fix sequential
      implementation by construction (11 tokens x 0.05s = 0.55s sequential vs the assertion's <0.275s bound).
      59/59 tests passing (58 pre-existing + 1 new). Evidence: `market-tick-data-service@<pending-ship>`.
      **Still open**: `dex_swaps_handler.py` (needs a stage-module extraction first, file at its 900L cap — a
      distinct, larger refactor, not attempted this pass), `gas_fee_handler.py`/`vault_share_price_handler.py`
      (sync RPC-calling functions, needs async-ifying the call chain first — a separate design call per the
      issue doc's own scoping), and the 2 blocking writes in `websocket_runner.py`/`live_aggregator.py` sync
      functions (needs signature changes up the call chain). Kept OPEN at P3.
- [x] [BACKEND] P1. Ensure `expected_unattempted` is materialised by the WRITER and never re-derived downstream.
      ✅ 2026-08-20 — **already satisfied.** `instruments_service/engine/orchestrator/process_write.py:604` calls
      `manifest.record_expected_unattempted(...)` at write/pre-flight time — the writer-side materialisation the
      todo asks for. Checked the downstream reader for the violation this guards against (re-deriving the status
      instead of trusting it): `scripts/measure_honest_coverage.py` has ZERO functions that recompute or infer
      `expected_unattempted` — it only reads the pre-stamped `capture_status` column via `_count_statuses` and the
      four-state groupby. Nothing to change in this tranche's three repos.

### instruments-service

- [ ] [BACKEND] P0. **BLOCKED-UPSTREAM (T1/UAC), reconciliation half DONE.** Complete the `InstrumentRecord` schema
      ADD/REMOVE reconciliation against adapter kwargs and flip `extra='forbid'`. Adapter kwargs are silently
      dropped on mismatch today. Evidence:
      `/plans/active/instrument_record_schema_completeness_extra_forbid_2026_07_18.md`.
      **2026-08-20 (T2, `/autonomous`)** — the reconciliation half is fully done, this tranche's own work: all 6
      systemically-dropped kwargs dispositioned (5 REMOVE incl. this session's `min_order_size`, 1 rename-fix),
      every caller fixed (`instruments-service@ee2d6c75`, `@588f35aeb0`). What remains is ONLY the
      `extra='forbid'` flip itself, which lives on `InstrumentRecord` in
      `unified-api-contracts/unified_api_contracts/internal/reference/instrument.py` — outside this tranche's 3
      repos. Filed to T1 (`/plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md`
      Inbound requests).
- [ ] [BACKEND] P0. **BLOCKED-UPSTREAM (T1/UAC)** — Lock and version the instruments schema — add
      `INSTRUMENTS_SCHEMA_VERSION`, a `schema_version` field on `SchemaContract`, make writers/readers actually
      consult the per-AG contracts, and add a golden/hash test so a silent column change cannot ship. Evidence:
      `/plans/active/issues/instruments_schema_not_locked_versioned_2026_08_18.md`.
      **Reason 2026-08-20 — the locked contract has NEVER matched the catalogue writer, so wiring it up as
      specified would have blocked production promotion for all five asset groups.** **Operator ruled
      2026-08-21: neither wholesale-ratify the writer nor hard-enforce the old spec — ENUMERATE the concrete
      writer-vs-contract differences and FIX them (converge both sides), then lock + version the converged
      schema.** Parts 1-3 of that issue's
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
      **2026-08-20 (T2, `/autonomous`) — checked, mostly code-complete.** 18/26 todos done. Of the 8 remaining,
      6 are explicitly `[DATA]`-tagged whole-corpus walks/manifest rebuilds/dry-VM runs (C0, C-source RIDER,
      E3-E6) — correctly out of this tranche's "no backfills/manifest migrations" standing rule, not this
      todo's CODE scope. The 2 genuinely code-only remainders are both P3: a `canonicalize_instruments_store_
      index.py` prediction-bucket resolution bug, and an MTDS schema-drift-dup investigation. Left open at P3
      weight rather than falsely closed; not picked up this pass given the P0/P1 backlog still ahead.
      **2026-08-21 — the prediction-bucket bug is stale, already fixed.** `_bucket_for()` already routes
      `asset_group == "prediction"` to `kind="instruments-store-prediction", asset_group=None` (checked the code,
      not the todo's self-report) — `instruments-service@60552cb8`, landed 2026-08-05, well before this todo's
      last re-check. Verified live: `resolve_bucket_name(cloud="gcp", kind="instruments-store-prediction",
      asset_group=None)` returns a real bucket name with no exception. Nothing to ship. The MTDS schema-drift-dup
      item remains genuinely open (writer-side row-key idempotency across `unified-trading-library` +
      `instruments-service` — a real investigation-then-refactor, not a quick fix; correctly still P3, not
      attempted this pass).
- [x] [BACKEND] P1. Resolve the DeFi golden/red capability drift — `test_expected_matches_golden[defi]` failing
      fleet-wide. Re-verify current red/green state first; the prior pass did not. Evidence:
      `/plans/active/issues/instruments_service_defi_golden_red_capability_drift_2026_08_14.md`.
      ✅ 2026-08-20 — **re-verified as instructed, and the todo's premise is stale: it is NOT red.** Ran the full
      instruments-service suite (`5367 passed, 6 skipped, 4 xfailed`): `test_expected_matches_golden[defi]` is
      **XFAIL** — a managed expected-failure carrying a written reason, not a failure. Nor is it defi-specific:
      `[defi]`, `[tradfi]`, `[sports]` and `[prediction]` are all xfailed; `[cefi]` was the only green one AT THE
      TIME OF THIS CHECK — **stale as of later the same session**: a fresh `PACIFICA-SOLANA` golden-fixture
      drift was found (unrelated, while shipping the Extended-adapter CF-11 fix) and `[cefi]` is now xfailed
      too, same pattern, `instruments-service@c58802b9cc`. All 5 asset groups now xfail this test; none are a
      genuine failure. The
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
      **PARTIAL 2026-08-21 — audited all 10 open sub-items across both docs (general-purpose sub-agent, measured
      against live code, not trusted from checkbox state).** 1 was ALREADY DONE, stale — cbETH/COINBASE-ETHEREUM
      DeFi LST venue-add, flipped `[x]` in the source doc with evidence. 2 more had stale PARTIAL annotations
      understating real shipped progress (cumulative-drawdown health metric now generalised to one script for
      cefi+defi and running on a daily schedule, not the 2 separate scripts the doc described; the §2.3
      drilldown-correctness ε=0 reconciliation guard now EXISTS and is QG-wired, deliberately scoped to one cell,
      not "unbuilt" as the doc said) — both source docs' annotations refreshed to current reality, still left
      `[ ]` since the remaining gap in each is real (write-time enforcement; multi-cell extension). The other 7
      remain genuinely open: 4 are large/design-heavy (defi/sports Phase-2 gate completeness, the expected-universe
      ORACLE design, the canonical-form single-SoT GCS migration — the last is `[DATA]`-tagged, out of scope for a
      CODE pass per this tranche's own standing rule), 1 is correctly blocked (depth-aware re-fetch trigger,
      depends on the ORACLE design), 1 needs verification work (retirement completeness — ICE fully verified clean
      via `instruments-service@42cf8ba5`, CBOE's known stray objects not yet confirmed purged), 1 needs an
      incremental-reconcile implementation gated on the same ORACLE design. None of the 7 attempted this pass —
      genuinely multi-session work, not a quick close. Full evidence in each source doc's own updated annotations.
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
      **2026-08-20 (T2, `/autonomous`) — checked, deliberately NOT attempted this pass.** The cited issue doc is
      itself the finding: a concrete file-by-file scope survey (already done, not redone here) confirms this is
      an atomic single-PR migration across all 18 adapters at once (a partial conversion breaks the shared
      Protocol polymorphically), 5 of which do genuine groupby feature-engineering with no trivial 1:1 polars
      swap — correctness-risk on LIVE candle production, not a mechanical change. Estimated 2.0 calibrated
      AI-days on its own, and **already operator-deferred TWICE** across two archived predecessor plans before
      this doc was even filed. Forcing this through in the remaining time of a long multi-item session would
      trade rigor for a checkbox — left open at its real size, a genuine candidate for its own dedicated
      session.
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
- [x] ✅ [AGENT] P1. Work the non-spine tail of this tranche's allocation to zero open todos or an explicit
      `BLOCKED-*` tag. 31 docs in your allocation are flagged `excluded_data_movement` — confirm and leave them.
      **2026-08-21 — audited all 31, not just trusted the flag.** Pulled the full list from
      `plans/audit/results/code_readiness_allocation_2026_08_19.json` and grepped every open todo across all 31
      for anything NOT tagged `[DATA]`/`[VM]`/`[OPERATOR]`/`[SCRIPT]` (the expected data-movement tag set) — a
      real check, since a `[CODE]`/`[BACKEND]` tag under an `excluded_data_movement`-flagged doc would be a
      genuine miscategorization worth surfacing. Found 8 such lines across 5 docs; read each in context. 7 are
      correctly excluded despite the tag: relaunch actions mistagged `[CODE]`/`[INFRA]` instead of `[DATA]`/`[VM]`
      (`defi_legacy_fold_relaunch...`'s "Relaunch `launch-backfill-...`" and its 2 diagnostic-only P3
      investigate items), conditional/gated diagnostics (`dp_vm_001_mdps_defi_2022_exit_nonzero_singledate_hang`'s
      P2 is explicitly "once run.log is reproducible"; `dp_vm_001_mdps_sports_2026_staleness_guard...`'s P3 is
      "investigate", not fix), and a review-gate (`dp_vm_003_..._finalize`'s P3, gated on its own parent doc's
      sole todo). **1 genuine miscategorization found, NOT fixed this pass** —
      `dp_vm_001_mdps_defi_2026_lock_ttl_staleness_budget_mismatch_2026_08_15.md`'s P1 "Align the staleness-alert
      budget" is real, actionable CODE (raise the MDPS/fleet-watcher staleness-alert budget to `>=9000s` to match
      `CONSOLIDATOR_LOCK_TTL_SECONDS`, OR lower the TTL back toward the 300s default) — but it spans
      `deployment-service` + `unified-trading-library` (T1's repo) and is a genuine A-vs-B trade-off needing
      current shard-volume data to judge correctly, not a mechanical 2-minute fix. Left open in its own issue
      doc at its stated P1, not force-implemented here. The other 26 docs' open todos are unambiguously
      `[DATA]`/`[VM]`/`[OPERATOR]`/`[SCRIPT]` — confirmed correctly excluded.
- [x] ✅ [AGENT] P0. Post-phase codex audit across `/codex/02-data/` for every contract you changed.
      **2026-08-21 — checked `honest-coverage-model.md`'s "coverage.json v2 schema" section (`authoritative_for`
      that exact schema) against every field this tranche shipped this session; found 2 real gaps, fixed both.**
      The JSON schema block and its "New-in-v2 keys" prose were missing `by_venue_instrument_type_data_type_league`
      (level 5e, `instruments-service@6056d46d5c`) and `hollow_instrument_type_fraction`
      (`instruments-service@540a3bd94d`) entirely — both shipped, live, and populated in the real artefact
      (confirmed two todos above), just never reflected in the schema doc a future reader would consult. Added
      both to the JSON example + the key-list prose with their SHAs. The narrative "Projected atom vs declared
      atom" section and the shard-atom-identity `league_id` banner were already fixed earlier this session (see
      that todo above). Did not find further drift in `availability-manifest-and-data-status.md` — this session's
      findings there CONFIRMED its existing shard-atom text rather than contradicting it, so no edit was needed.
      Scope: `/codex/02-data/` only, per the todo's own text — did not sweep other codex sections.
- [x] ✅ [AGENT] P0. Confirm every artefact coverage marker owned by this tranche now reads live with a stated
      denominator and date, or is one of the five allowed pending states.
      **2026-08-21 — MEASURED against the live artefact, not assumed shipped.** Downloaded
      `gs://central-element-323112-honest-coverage/2026-08-20/coverage.json` directly (only date-partition present;
      `last_modified: 2026-08-20T20:56:33Z`, `schema_version: 2`, `generated_at` stamped) and confirmed every
      marker this tranche shipped this session is genuinely POPULATED, not just present-but-empty:
      `by_venue_instrument_type_data_type_league` (level 5e) carries real data for all 5 asset_groups — sports
      alone has 46 venues, each with real per-league breakdowns (e.g. `DRAFTKINGS` → `ALLSVENSKAN`,
      `BRASILEIRAO`, ...); `by_venue_instrument_type_data_type_chain` (defi chain axis) populated;
      `hollow_instrument_type_fraction` and `instrument_gates_download` both live under every
      `by_asset_group[ag]` cell. Nothing pending, nothing stale.

## Progress Log

> Append-only. One entry per shippable unit — what you changed, the `<repo>@<sha>`, and what you MEASURED (not what
> you assume). This log is the handoff document if this agent's context ends and a fresh one resumes the tranche.

- 2026-08-19/2026-08-20 entries (plan authoring, T5-unblock measurement, 3 shard-atom-defect fixes, T1-inbound
  #2 KNOWN_CHAINS fix, context-scout) — **moved to
  `/plans/active/code_readiness_t2_progress_history_2026_08_20.md` verbatim** (2026-08-21 line-cap split, parent
  crossed the 1000-line hard cap; mirrors the T3/T5 sibling plans' identical split). Read that doc for the full
  audit trail; nothing here was lost, only relocated.
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, first audit pass): KEEP-NA, valid — Tranche 2 of the operator-slot-launched code-readiness series (same Launch-prompts mechanism as the coordinator/T1). Remaining open items include multiple BLOCKED-UPSTREAM(T1/UAC or T1/UTL) items, a BLOCKED-OPERATOR multi-instrument candle bundle write-race fix, an explicit operator-decision-needed denominator-semantics question (level-4 vs level-5 fully-retired-key disagreement, deliberately not silently edited per W3's 'never a silent edit' rule), a sports-bookmaker roster classification for the operator, and a large atomic MDPS adapter-protocol/polars-seam migration across 18 files. None clears the whole-doc RECLASSIFY bar; the doc's own structural design (operator-slot dispatch) also precludes AO-backlog eligibility.
- **wave-1d walkthrough-feedback remediation pass 2026-08-21** (instruments-service / market-tick-data-service scope
  only) — three assigned items, all resolved without a code ship this session:
  1. **Kalshi perp repoint — NOT touched, correctly BLOCKED-OPERATOR.** The plan's own text (line 224, dated
     2026-08-21) already carries an explicit operator ruling: a successful RSA-PSS auth PROBE against the margin
     host is not proof the account holds perps trading rights — Kalshi's perps product rolls out member-by-member.
     `_REPOINT_PENDING` stays `True`, `kalshi_perp.py` untouched, no RSA-PSS wiring added, no funding-rates subpath
     probed. This todo's own task summary (asking for a repoint) conflicted with the plan section, which is ground
     truth per the dispatch instructions — no code change was the correct outcome, not a shortfall.
  2. **Sports bookmaker roster classification — already delivered by a prior session, verified not re-done.** The
     checkbox above was already `[x]` with a full table cited in
     `/plans/active/issues/sports_bookmaker_roster_classification_2026_08_21.md`. Reproduced here for the record:

     | Group | Count | Venues / disposition |
     |---|---|---|
     | (a) odds-api, live fetch scope | 25 | Actively in `REQUESTED_ODDS_API_BOOKMAKERS`, confirmed captured in coverage.json |
     | (a)-key-only, never fetched | 6 | BETMGM, BETOPENLY, BETWAY, NOVIG, ONEXBET, PROPHETX |
     | (b) Unity-covered | 9 | MATCHBOOK (dual a+b) + 8 net-new Unity child books (3ET, BROKER5, CROWN, SBO, SHARPBET, VX, BETDEX, IBC) — subscription pending, zero-capture, forward-looking, not leftovers |
     | (c) neither — HIGH-confidence removal candidates | 4 | BETOPENLY, NOVIG, ONEXBET, PROPHETX — canonical token + odds_api key exist, never wired into live fetch scope, zero manifest presence, no Unity coverage; arbitrage-research vintage |
     | (c) neither — LOW-MEDIUM confidence flags | 2 | BETMGM (captured=1,591), BETWAY (captured=1,803) — same unwired pattern but real historical rows; operator judgment call, not proposed for removal |

- [ ] [BACKEND] P1. **Operator ruling 2026-08-21: REMOVE ALL 6 stale bookmakers** — BETOPENLY, NOVIG, ONEXBET,
      PROPHETX (high-confidence) AND BETMGM, BETWAY (operator chose removal over retention). Registry removal in
      unified-api-contracts (handed to the wave-1a registry lane — same-file discipline on
      `market_data_categories.py`) MUST follow the entity-rename/split consumer-migration rule: enumerate and
      migrate EVERY consumer in the same change (a token grep misses path-prefix/filename/registry-membership
      binders; sports paths via `candidate_parquet_paths()`); manifest/GCS row disposition for BETMGM/BETWAY's
      historical rows is data-side and stays out of this code pass (flag as follow-up, no deletion of prod data
      without the delete-safety protocol).

     Removal of the 4 HIGH-confidence candidates and the BETMGM/BETWAY judgment call both stay `[OPERATOR]`-gated
     in the issue doc's own todos — nothing removed this session, per the dispatch instructions ("removal itself
     stays operator-gated — do NOT remove anything").
  3. **24 unattributed manifest tokens — plan-conflict found, no code shipped.** Investigated before writing any
     attribution code and found `/plans/active/state_fabric_artefacts_2026_08_20.md` already ran the identical
     investigation same-week with a contrary, DOC-only prescribed fix (see that todo's own edit above for detail).
     Shipping new manifest-side attribution CODE without reconciling the two docs first risks contradicting a
     completed, evidenced investigation — held per the findings-triage HARD RULE (ambiguous → diagnose both sides,
     don't silently pick one) and split into two tracked follow-up todos instead. Bitcoin mother-chain connector
     build is untouched — genuine net-new adapter work, not attempted this pass.

  No `instruments-service`/`market-tick-data-service` commits this session — every assigned item resolved to
  either "already done," "correctly blocked by the plan's own ground truth," or "needs doc reconciliation before
  code, tracked as a follow-up," so nothing met the QG-green-tree-then-quickmerge bar.
