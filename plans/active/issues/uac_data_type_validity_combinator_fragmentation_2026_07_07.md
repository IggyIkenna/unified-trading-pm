---
doc_type: issue
title:
  "UAC data-type-validity combinator is fragmented across CEFI/DEFI/TRADFI -- no AG has a real (venue, instrument_type)
  -> data_types table, and one cell is live-wrong"
summary:
  "A 5-way audit (2026-07-07) found that no asset group has a genuine (venue, instrument_type) -> data_types combinator
  in UAC. CEFI has a flat per-venue map plus an asset-group-wide (not venue-wide) instrument-shape matrix, patched by
  three independently-bolted-on venue-specific overrides in two files. DeFi has a real (protocol, instrument_type) ->
  data_types object but it cannot narrow within a protocol and has drifted from its own actually-captured registry.
  TradFi has three orthogonal axes that are never joined, producing a live, provably-wrong cell: CME and ICE both get an
  identical futures_chain valid-data_types set despite ICE having no Databento coverage. Sports and Prediction are
  correctly excluded from this combinator entirely -- neither domain has a real per-instrument-type dimension (sports
  has no tradeable-instrument concept; a prediction market already encodes its full structure in one record) -- but
  Prediction has a separate, smaller problem: its flat venue map under-declares real data types, forcing a parallel
  deployment-api registry."
status: open
nature: notes
asset_group: [cefi, defi, tradfi]
stage: [data, meta]
repos: [unified-api-contracts, market-tick-data-service, instruments-service, deployment-api]
scope: [engineer, admin]
tags: [uac, ssot, data-type, instrument-type, combinator, cefi, defi, tradfi, honest-coverage]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P1
source:
  "ASTER/CEFI instrument-service audit follow-up, 2026-07-07 -- 5-way parallel audit (one per asset group + a cross-repo
  writer-duplication scan), operator-scoped to exclude Sports/Prediction from the combinator redesign"
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: opus-required
thinking_tier: high
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
last_updated:
  '2026-07-13 (was: 2026-07-07 — verify-rerun-2 finding 140, corrected 2026-07-14 — body''s debt_token finding (finding
  2) marked "SUPERSEDED 2026-07-13"; frontmatter never bumped)'
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: correct-codex
locked_since:
---

> **Scope note (operator-confirmed 2026-07-07):** this combinator applies to **CEFI, DEFI, TRADFI only**. Sports has no
> tradeable-instrument concept at all (a fixture/league/bookmaker isn't an instrument with a shape) — its one
> "instrument_type" value is a catalogue-grain label borrowed from an unrelated reference-data map, and UAC's own dead
> matrix rows for sports are already marked `UNCERTAIN`/unused. Prediction's instrument is always the same shape
> (`PREDICTION_MARKET`) because a prediction market's full structure — question, outcomes, resolution — is already
> encoded in one record; there is no spot-vs-perpetual-vs-option-style variation to combinate over. Forcing either
> domain into a `(venue, instrument_type) → data_types` table would manufacture a dimension neither domain has — the
> same mistake `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` already flagged for
> `market_metadata`. Both stay on the simpler flat venue-map shape; see the separate, smaller Prediction todo below.

## Findings, worst first

1. **Live, silently-wrong cell (TradFi).** `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`
   (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:611-735`) is keyed
   `(asset_group, instrument_type)` — not `(venue, instrument_type)`. Its accessor,
   `valid_data_types_for_venue_instrument_type` (`market_data_categories.py:995-1032`), accepts a `venue` parameter and
   then discards it for every asset group except DeFi (`:1019-1020`,
   `if asset_group.lower() != "defi" or not venue: return valid_data_types_for_instrument_type(...)`). Net effect: CME
   and ICE, both stamped `instrument_type="futures_chain"`, get the identical valid-data_types set (line 666's comment
   literally asserts "CME/ICE futures_chain cells with ohlcv_1s") — even though ICE has no Databento coverage at all
   (per the venue-list's own comment, `:273-285`) and `VENUE_DATA_TYPE_CAPABILITIES["ICE"]` doesn't declare `ohlcv_1s`
   (`:1276`). This directly contradicts the flat venue map with no reconciliation.
2. **DeFi's two registries have drifted from each other.** `PROTOCOL_CAPABILITIES` (the "should be valid" declaration,
   `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py:344-843`) and
   `DEFI_VENUE_DATA_TYPE_CAPABILITIES` (the "actually captured" registry,
   `unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py:17-232`) disagree on vocabulary for
   the same protocols, independent of chain: Aave/Radiant/Spark/Compound/Euler/Fluid all declare `liquidations`/
   `risk_params` as valid via the shared `_LENDING_DATA` shorthand (`_defi.py:338`), but zero instances of either are
   ever actually captured anywhere in `DEFI_VENUE_DATA_TYPE_CAPABILITIES`; conversely `oracle_prices` is captured on
   every Aave chain but never declared valid. Nothing enforces the two registries stay in sync, and unlike the module's
   own convention for aspirational entries (an inline comment, `_defi.py:322-324`), these carry none. **The same drift
   also shows up one level down, at `instrument_type` rather than `data_type`** (found 2026-07-07, later same day):
   `InstrumentType.DEBT_TOKEN` is a fully real, declared type — a schema contract exists for
   `("defi", "debt_token", "lending_indices")`
   (`unified-api-contracts/unified_api_contracts/internal/schemas/_defi_v2_contracts.py:99`) — but a live pull of
   `AAVE_V3-ETHEREUM`'s real `instrument_types` breakdown shows only `a_token` (the supply-side receipt token);
   `debt_token` (the borrow-side counterpart, i.e. what people owe) has zero captured rows anywhere. Aave lending
   positions are being tracked one-sided today: we see what people supplied, not what they borrowed. Same root pattern
   as the `liquidations`/`risk_params` drift above — declared, schema-ready, never wired to a capture path — just one
   axis deeper (a whole missing `instrument_type`, not a missing `data_type` within one). **SUPERSEDED 2026-07-13**:
   this one-sided-tracking claim is resolved — all 9 DeFi lending protocols (AAVE_V3, SPARK, COMPOUND_V3, MORPHO, FLUID,
   VENUS, RADIANT, EULER_V2, BENQI) now emit both `a_token` and `debt_token` with real captured rows (2,949 total), per
   the resolved `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md`'s 2026-07-13 entry.
3. **CEFI's per-instrument-type narrowing is three independently-bolted-on patches, not one mechanism**, in two files:
   `DERIBIT_MVP_INSTRUMENT_TYPE_DATA_TYPES` (`market_data_categories.py:549-553`, Deribit-only, `instrument_type`-keyed,
   consumed by MTDS fetch-scoping) · `CeFiMvpRule.instrument_type_data_types`/ `.venue_data_types`
   (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py:204-205, 465-467, 479-483`, a
   _different_ sparser mechanism narrowing Deribit OPTION and cutting Coinbase to trades-only) · `FUTURE_BUNDLE_VENUES`
   (`market_data_categories.py:809-812`, a grain-axis overlay affecting Deribit and OKX). Plus one confirmed-dead
   remnant, `MVP_VENUE_DATA_TYPES` (`market_data_categories.py:539-544`, zero consumers workspace-wide). Each was added
   independently for a different purpose (MVP cost-cutting vs. could-exist shape validity vs. capture-grain) with no
   shared shape.
4. **MTDS re-hardcodes facts UAC already declares, and one has already drifted.**
   `market-tick-data-service/market_tick_data_service/cli/handlers/book_microstructure_handler.py:73-83`'s `_L5_VENUES`
   tuple (meant to list every `book_snapshot_5`-capable CeFi venue) is missing 11 venues UAC's
   `VENUE_DATA_TYPE_CAPABILITIES` declares as capable (BYBIT-SPOT, COINBASE-FUTURES, BITFINEX-SPOT/FUTURES,
   BITGET-SPOT/FUTURES, KRAKEN-SPOT/FUTURES, HYPERLIQUID, ASTER, PACIFICA-SOLANA, EXTENDED-STARKNET, LIGHTER-ZKSYNC).
   Currently cosmetic (only feeds a `preflight()` log line), but a live example of the drift class. Two more confirmed
   duplicates: `onchain_perp_batch_handler.py:122-126`'s `_SOURCE_COVERAGE_START` (byte-identical to
   `VENUE_DATA_TYPE_CAPABILITIES["HYPERLIQUID"]`, and itself a copy of a _third_ hardcoded pair in
   `market_tick_data_service/adapters/hyperliquid_s3.py:51-52` — the same fact now lives in three unlinked places);
   `solana_defi_handler.py:246-257`'s `_PROTOCOL_TO_DATA_TYPE` (splits `"kamino"` into two protocol keys with no
   corresponding UAC entry for the split — a structural mismatch, not just a copy).
5. **Prediction's flat venue map under-declares real data types** (separate from the instrument_type question — see the
   scope note above): `VENUE_DATA_TYPE_CAPABILITIES["POLYMARKET"/"KALSHI"]` only declares `trades`, so
   `deployment-api/deployment_api/services/data_status/mtds.py:143-215` has to maintain a parallel
   `PREDICTION_DATA_TYPE_META` just to keep the honest-coverage denominator correct for `book_snapshot`/
   `market_metadata`/`fills` — a real UAC-completeness gap, patched outside UAC rather than fixed in it.
6. **A real modeling gap MTDS is already patching around**: `onchain_perp_batch_handler.py:136-148`'s
   `_LIVE_ONLY_DATA_TYPES`/`_DROPPED_DATA_TYPES` exist because UAC's `VENUE_DATA_TYPE_CAPABILITIES` has no batch-vs-live
   (`pipeline_mode`) axis — only a bare start-date per `(venue, data_type)`. When a venue's batch and live paths
   genuinely differ in what they can serve (ASTER: `book_snapshot_5`/`liquidations` are live-only), MTDS has nowhere in
   UAC to source that fact and invents its own local, unenforced mini-registry. This is direct evidence the eventual fix
   needs a `pipeline_mode` axis, not just an `instrument_type` one.

## The target shape — two layers, not one flat table

**Correction (2026-07-07, operator-caught):** an earlier draft of this section collapsed DeFi's chain into `venue` as an
opaque `"PROTOCOL-CHAIN"` string and claimed "no separate chain axis needed." That's wrong — chain is a real axis, it
just belongs on a different layer than instrument_type does, and conflating the two layers is exactly what let finding
2's drift go unnoticed. Two layers, explicitly joined:

1. **Theoretical validity** — `(asset_group, protocol, instrument_type) → frozenset[data_type]`, **chain-agnostic by
   design**. A protocol's conceptual shape (does a lending protocol produce `lending_indices`? does an option produce
   `options_chain`?) doesn't change based on which chain it's deployed on. This is what `PROTOCOL_CAPABILITIES` already
   correctly does for DeFi and what CEFI's `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` already correctly does
   chain-lessly (CEFI has no chain concept for its own venues, only for the 2 on-chain CLOB venues classified under it —
   those are DeFi-shaped for this purpose). Nothing about this layer needs to change shape; TradFi's version just needs
   `venue` to stop being silently discarded (see finding 1's fix).
2. **Actual availability / genesis** —
   `(asset_group, chain, venue, instrument_type, pipeline_mode) → {data_type: genesis_date}`, **chain IS a mandatory
   explicit key here** — not folded into an opaque venue string. Whether a specific chain's subgraph/RPC/exchange-API
   actually exposes a data type is an infrastructure fact that genuinely varies (Aave on Ethereum exposes 7 data_types;
   the same protocol on Scroll/zkSync exposes 2, per finding 2) — this is exactly the axis the current
   `DEFI_VENUE_DATA_TYPE_CAPABILITIES` already varies by (correctly), it just isn't a named, first-class key column
   today. For CEFI/TradFi, `chain` is simply absent/null (no chain concept), so the table degrades cleanly to today's
   flat venue map for those two asset groups.
3. **The join, not either layer alone, is the actual fix.** A single accessor should compose both layers and assert
   `actual ⊆ theoretical` per `(chain, venue, instrument_type)` — that check is what's missing today, and it's what
   would have caught finding 2's drift (Aave declaring `liquidations`/`risk_params` as theoretically valid while zero
   chains ever actually captured either) automatically instead of requiring a manual audit to surface it.

- `pipeline_mode` (batch vs. live) is a first-class axis on the availability layer only — finding 6 shows MTDS already
  needs this dimension in practice; it has no meaning on the theoretical-validity layer (a protocol either can
  conceptually produce a data type or it can't, independent of batch/live transport).

## Todos

- [x] [CODE] P1. **Fix the live CME/ICE cell** (finding 1) — shipped `unified-api-contracts@fa9cece5`
      (`origin/live-defi-rollout`, verified post-push): `valid_data_types_for_venue_instrument_type` now actually uses
      `venue` for TRADFI (a new `VALID_DATA_TYPES_VENUE_EXCLUSIONS` table, checked for every asset_group, not just
      DeFi). See Progress Log for live-verified evidence.
- [x] [DESIGN] P1. **Operator decision:** approved 2026-07-10 (`instruments_remaining_work_audit_2026_07_10.md` Progress
      Log, decision #4). Implemented as a JOIN inside the existing `valid_data_types_for_venue_instrument_type` accessor
      — see Progress Log for why an additive implementation was chosen over a literal key-shape migration of
      `VENUE_DATA_TYPE_CAPABILITIES`.
- [x] [CODE] P2. Reconcile DeFi's `PROTOCOL_CAPABILITIES` vs. `DEFI_VENUE_DATA_TYPE_CAPABILITIES` vocabulary drift
      (finding 2) — **partially shipped** (`unified-api-contracts@fa9cece5`): added
      `defi_actual_data_types_not_declared_valid()` (the `actual ⊆ theoretical` join/audit), ran it over live production
      data, fixed the one genuinely-evidenced violation (`aave_v3` + `oracle_prices`, 3,160 real captured rows), added
      the module's aspirational-entry convention to `radiant`/`euler_v2`'s dead `liquidations`/`risk_params`. **NOT
      fixed** — see Progress Log's 31-venue table (a different bug class: the actual/genesis layer over-claiming a start
      date with zero real captures, filed as a new P2 DESIGN todo below). **`debt_token`** intentionally OUT OF SCOPE —
      tracked in `defi_lending_atoken_debttoken_instrument_split_2026_07_07.md` (now RESOLVED — see that doc).
- [ ] [CODE] P2. ~~Fix `_L5_VENUES` (finding 4) to read from `VENUE_DATA_TYPE_CAPABILITIES`~~ **← `_L5_VENUES` part
      RESOLVED-BY-DELETION (2026-07-18):** it was added by `market-tick-data-service@0908bda7` (order_flow_imbalance L2
      feature) and removed entirely by `market-tick-data-service@a4fb3d13`, which retired that feature (zero consumers /
      zero prod rows / duplicated MDPS). `grep -rn _L5_VENUES market_tick_data_service/` = 0 hits. **STILL OPEN (onchain,
      not cefi):** audit `_SOURCE_COVERAGE_START` (`onchain_perp_batch_handler.py`, byte-copy of
      `VENUE_DATA_TYPE_CAPABILITIES["HYPERLIQUID"]`) and `_PROTOCOL_TO_DATA_TYPE` (`solana_defi_handler.py`, the
      `"kamino"`/`"kamino_lending"` split mismatch) for the same read-from-UAC fix. (repo: market-tick-data-service)
- [ ] [CODE] P2. Add the missing `book_snapshot`/`market_metadata`/`fills` declarations to
      `VENUE_DATA_TYPE_CAPABILITIES["POLYMARKET"/"KALSHI"]` (finding 5) and retire deployment-api's parallel
      `PREDICTION_DATA_TYPE_META` once UAC is complete. This is independent of the CEFI/DEFI/TRADFI combinator redesign
      — a plain completeness fix. **Not touched this pass** — the `deployment-api` half is out of scope.
- [ ] [SCRIPT] P3. Delete confirmed-dead code: `MVP_VENUE_DATA_TYPES` (zero consumers), DeFi's emptied
      `DEFI_VENUE_AXIS_OVERRIDES = {}` (`defi_venues.py:573`) plus the stale comment referencing it in
      `defi_venue_capabilities.py:133-134`, and Prediction's inert `(asset_group, instrument_type)` matrix row
      (`market_data_categories.py:732-734`, already documented as a no-op) once its scope exclusion (this doc's header
      note) is itself the authoritative record. **Not touched this pass** — `defi_venues.py` was live-being-edited by
      concurrent sibling agents for the duration of this dispatch.
- [ ] [DESIGN] P2. **New finding, 2026-07-10** (surfaced while live-verifying finding 2): 31 DeFi `(venue, data_type)`
      pairs across 8 protocols (COMPOUND_V3/MORPHO/FLUID/SPARK/RADIANT/GMX/DRIFT/KAMINO + AAVE_V3's `rewards` + all
      `ALCHEMY-*` `gas_fees`) declare a genesis start-date in `DEFI_VENUE_DATA_TYPE_CAPABILITIES` (Layer 2 — "actual")
      with **zero real captured rows** in the live manifest (100% `empty_confirmed`). This is the ACTUAL layer
      over-claiming, not the theoretical layer under-declaring (finding 2's original shape) — needs an
      operator/data-owner decision per (protocol, data_type) whether to wire the real capture path or roll back the
      aspirational genesis date. Full live-verified table in the Progress Log below.

## Progress Log

- **2026-07-10** — **Two-layer combinator redesign implemented and shipped, `unified-api-contracts@fa9cece5`**
  (`origin/live-defi-rollout`; content verified present post-push via `git show origin/live-defi-rollout:<path>`).
  Scope: finding 1 (live fix), the operator-approved design decision, and the real/evidence-backed subset of finding 2's
  DeFi reconciliation. Full detail:
  - **Finding 1 (CME/ICE), live-verified before fixing**: pulled fresh prod manifests
    (`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`, 2026-07-10) rather
    than trusting the doc's prior claim at face value. Real result: CME/futures_chain/ohlcv_1s has 151,153 real
    `captured` rows; ICE/futures_chain/ohlcv_1s (2,108 rows), ICE/combo/ohlcv_1s (360,270 rows), and bare-ICE/ohlcv_1s
    are ALL 100% `empty_confirmed` — ZERO `captured` anywhere — while ICE's `trades`/`ohlcv_1m`/`tbbo` genuinely DO have
    real captured rows at the same grains (ICE/futures_chain: 110 trades + 135 ohlcv_1m; ICE/combo: 83 trades + 95
    ohlcv_1m). Fix: a new
    `VALID_DATA_TYPES_VENUE_EXCLUSIONS: dict[tuple[asset_group, venue, instrument_type], frozenset[data_type]]` table in
    `market_data_categories.py`, checked inside `valid_data_types_for_venue_instrument_type` for every asset_group (not
    just DeFi). Only 2 entries (`("tradfi","ICE","futures_chain")`, `("tradfi","ICE","combo")` → `{"ohlcv_1s"}`) — a
    SUBTRACTION from the AG-level theoretical set, not a hand-authored replacement, so no other proven-real ICE
    data_type (e.g. `tbbo`, unverified at this exact grain) is silently dropped. Every other TradFi/CeFi/DeFi venue (CME
    included) is byte-identical to pre-fix behaviour — verified via `test_non_defi_delegates_unchanged`.
  - **Two-layer design, implementation choice**: rather than physically restructuring `VENUE_DATA_TYPE_CAPABILITIES`'s
    key shape to a literal `(asset_group, chain, venue, instrument_type, pipeline_mode)` tuple (the doc's originally
    drafted target shape), the redesign was implemented as an ADDITIVE JOIN inside the existing accessor. Reason,
    discovered while implementing: `VENUE_DATA_TYPE_CAPABILITIES` for CeFi/TradFi is a SPARSE start-date OVERRIDE table
    (an entry omits any data_type whose start date equals the venue's own default launch date — e.g. CME's dict has only
    `{ohlcv_1s, ohlcv_1m}` despite CME genuinely also capturing `trades`/`tbbo` at massive scale; DERIBIT's dict omits
    `ohlcv_1m` despite it being a real default-start data_type) — so treating "absent from the dict" as "not capable"
    (the naive literal-join interpretation) would have produced dozens of false exclusions across every CeFi/TradFi
    venue with an override entry. The additive exclusion-table approach avoids this entirely: it only ever subtracts an
    EXPLICITLY-PROVEN-WRONG cell, never infers absence-as-exclusion. DeFi's per-chain dict does NOT have this
    sparse-override convention (every declared data_type is a literal, real key), so the Layer-3 `actual ⊆ theoretical`
    join (below) IS safe to run directly against it.
  - **Finding 2 (DeFi drift), live-verified before fixing**: added `defi_actual_data_types_not_declared_valid()` to
    `market_data_categories.py` — for every `PROTOCOL-CHAIN` venue in `DEFI_VENUE_DATA_TYPE_CAPABILITIES`, flags any
    data_type NOT in that protocol's `PROTOCOL_CAPABILITIES.data_types` (the `actual ⊄ theoretical` direction). Run
    against the CURRENT (pre-fix) registries: **34 venues flagged**, dominated by `oracle_prices` (25 venues across
    every lending/staking/perp protocol) + `rewards` (8 AAVE_V3 chains) + `gas_fees` (5 ALCHEMY chain-level venues) +
    `dex_pool_swaps` (DRIFT-SOLANA). Cross-checked EVERY flagged venue against the live prod DeFi manifest
    (`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`) before deciding anything
    — this materially changed the fix from what the doc's original finding-2 text implied:
    - **Only `AAVE_V3-ETHEREUM`'s `oracle_prices`** has real `captured` rows (3,160) among all 34 flagged venues. Fixed:
      added `"oracle_prices"` (+ `"collect-oracle-prices"` mtds_operation) to `aave_v3`'s `PROTOCOL_CAPABILITIES` entry
      in `capability_declarations/_defi.py`. Verified: `defi_actual_data_types_not_declared_valid()` no longer flags any
      AAVE_V3-\* venue for `oracle_prices` (34→32 violations; the 2 dropped are AAVE_V3-SCROLL/ZKSYNC, whose ONLY
      violation was `oracle_prices`).
    - **The other 33 flagged (venue, data_type) pairs are ALL 100% `empty_confirmed` in prod — zero real captured rows
      anywhere** (spot-checked: GMX-ARBITRUM/AVALANCHE `oracle_prices`, DRIFT-SOLANA `dex_pool_swaps`, KAMINO-SOLANA
      `oracle_prices`, and the full AAVE_V3/COMPOUND_V3/RADIANT/SPARK/FLUID `oracle_prices`/`rewards` set). This means
      `DEFI_VENUE_DATA_TYPE_CAPABILITIES` over-claims a genesis date for these — the OPPOSITE direction from a
      theoretical under-declaration — filed as a new finding/todo above rather than "fixed" by unilaterally adding more
      theoretical declarations with zero supporting evidence.
    - **`liquidations`/`risk_params`** (the doc's original finding-2 claim: "declared valid via `_LENDING_DATA` but zero
      instances ever captured") is a MIXED picture on live re-verification, not a blanket true/false: real `captured`
      rows exist for `AAVE_V3` (`liquidations` 554, `risk_params` 20,302), `COMPOUND_V3` (`risk_params` 1,514), `FLUID`
      (`risk_params` 690) — the doc's blanket claim does not hold for these. Genuinely zero attempts/captures for
      `EULER_V2` (no `DEFI_VENUE_DATA_TYPE_CAPABILITIES` entry AT ALL) and `RADIANT` (declares
      `lending_indices`/`oracle_prices` only, no genesis date for `liquidations`/`risk_params` at all) — added the
      module's own aspirational-entry inline-comment convention to both, cross-referencing the separate
      VENUS/BENQI/RADIANT/EULER_V2 orchestrator-wiring item. **Note**: a companion commit
      (`unified-api-contracts@42ce2de3`, landed concurrently by a sibling agent during this same session) wired
      VENUS/BENQI/RADIANT/EULER_V2 into the IS production orchestrator + honest-coverage phase registry — this may
      partially supersede the "unwired" framing of this doc's aspirational comment for `lending_indices` specifically;
      the `liquidations`/`risk_params` subgraph-entity-support question the comment is really about was not re-verified
      against that companion change and may need a follow-up check. `COMPOUND_V3`/`FLUID`/`SPARK`'s `liquidations` and
      `SPARK`'s `risk_params` show real `attempted_failed` activity (genuine wired attempts, just failing/zero-yield) —
      left declared as-is (not aspirational — an active code-path issue, not a registry-drift one; not fixed here).
  - **Tests**: `tests/test_valid_data_types_by_instrument_type.py` — new `TestValidDataTypesVenueAxisExclusions` (7
    tests) + `TestDefiActualNotDeclaredValidJoin` (5 tests). Full suite green locally against the shipped SHA: 196/196
    across the touched-adjacent DeFi/validity-matrix/data-status test files; ruff + basedpyright clean on all 3 files.
  - **Multi-agent note (real, not hypothetical)**: this repo's working tree had MANY concurrent sibling agents
    live-editing/committing/pushing the SAME files for the rest of `instruments_remaining_work_audit_2026_07_10.md`'s
    8-workstream dispatch (COINBASE-SPOT/CDE, DERIBIT-COMBO, D10 defi capability entries, VENUS/BENQI/RADIANT/EULER_V2
    orchestrator wiring, a DP-CATALOG-002 alert rule — 6+ real commits landed on `live-defi-rollout` in the ~25 minutes
    this change was in flight). This caused the local branch to be reset away from an uncommitted/unpushed local commit
    **4 separate times** (verified via `git reflog` each time — always a clean, content-preserving loss: the commit
    object stayed reachable, recovered via `git cherry-pick`/`git apply` from the known-good SHA each time, verified
    byte-correct after each recovery before re-attempting). Root cause never conclusively identified
    (`slot-cron-ff-pull.sh` itself was checked and confirmed NOT the cause — it is `--ff-only` only, per its own "Never
    destructive" doc comment; a peer agent's own quickmerge Stage-0 cascade/pull-rebase cycle interacting with this
    change sitting uncommitted in the same physical clone is the more likely candidate). Final ship strategy: commit
    immediately after each re-apply (no gap for a QG run to sit exposed in), let the shared branch's own churn carry the
    commit forward (any agent's successful push with my commit as an ancestor ships it — confirmed this is exactly what
    happened), and verify against `origin/live-defi-rollout` directly rather than trusting a local quickmerge run's exit
    code. No other agent's work was reverted, dropped, or its stash touched — 2 unrelated stash entries were left
    completely alone throughout, per the workspace's "never `git stash drop` foreign WIP" rule. This doc itself (in
    `unified-trading-pm`) hit the identical pattern once (a concurrent `docs(plans): resolve autostash conflict...`
    commit landed and reverted this doc to pre-edit state) — redone once, same recovery approach.
- **2026-07-07 (later same day)** — Added the Aave `debt_token` finding to finding 2 and its todo — the same
  declared-vs-captured drift pattern, one axis deeper (a whole missing `instrument_type`, not a missing `data_type`
  within one). Surfaced during a conceptual walkthrough of DeFi instrument_type semantics
  (`a_token`/`debt_token`/`spot_asset`/`pool`), not a fresh audit pass.
- **2026-07-07** — Filed from a 5-way parallel audit (one agent per asset group + a cross-repo writer-duplication scan)
  following the ASTER/CEFI shard-dimension work. Operator confirmed the scope exclusion for Sports/Prediction before
  this doc was written — the combinator redesign targets CEFI/DEFI/TRADFI only; Prediction's separate
  venue-map-completeness gap (finding 5) is tracked as its own smaller, independent todo. No files edited.
