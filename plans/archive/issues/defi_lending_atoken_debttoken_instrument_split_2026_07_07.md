---
doc_type: issue
title:
  "DeFi lending protocols need a real A_TOKEN/DEBT_TOKEN (supply/borrow) instrument split for correct P&L —
  AAVE_V3/SPARK already split but mislabeled, COMPOUND_V3 splits into invalid enum values (crash risk), MORPHO has no
  split at all"
summary:
  'Operator flagged (reviewing the drilldown mockup): AAVE-style lending protocols mint a supply-side interest-bearing
  token (a-token) and a borrow-side debt token per reserve — economically distinct instruments, same relationship as
  SPOT_ASSET vs SPOT_PAIR in CeFi, and essential for correct P&L attribution (supply position earns yield, borrow
  position accrues interest — collapsing them into one instrument makes correct PnL impossible). Investigated against
  the real production catalogue (7,223-row instruments-store-defi-prd catalog.parquet) and found three different real
  states: (1) AAVE_V3 (171 rows: 113 A_TOKEN + 58 DEBT_TOKEN) and SPARK (14 rows: 8+6) already emit two separate
  InstrumentRecords per reserve with correct instrument_id keys, but every row is mislabeled instrument_type=LENDING
  instead of A_TOKEN/DEBT_TOKEN (a documented, half-finished migration — low severity since downstream ledger resolution
  parses the key, not the field); (2) COMPOUND_V3 (26 rows: 13 SUPPLY + 13 BORROW) uses SUPPLY/BORROW as its
  instrument_type, which are not valid InstrumentType enum members at all — a real crash risk
  (UnknownInstrumentTypeError, by design "never mask with UNKNOWN") if this data ever reaches the ledger writer; (3)
  MORPHO (465 rows, all LENDING_MARKET) has NO supply/borrow split whatsoever — this is the real structural gap the
  operator described, and LENDING_MARKET is also not a valid InstrumentType (same crash-risk class as Compound).
  Confirmed the strategy/execution layer already ASSUMES the A_TOKEN/DEBT_TOKEN split exists (defi_position.py
  is_supply/is_borrow, PositionPortfolio.net_value = total_supply_value - total_borrow_value) — Compound V3 and Morpho
  currently violate that assumption in production. The lending_indices data_type schema itself is fine (already carries
  both supply+borrow rate/index fields per reserve on one row) — this is an instrument-identity gap, not a market-data
  schema gap.'
status: resolved
nature: notes
asset_group: [defi]
stage: [data, meta]
repos: [instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [lending, a-token, debt-token, aave, compound, morpho, instrument-identity, pnl-attribution, honest-coverage]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    /plans/active/issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P1
source:
  'Drilldown mockup review, 2026-07-07 — operator: "AAVE (and all borrowing and lending venues) have debt tokens and
  a-tokens... this is essential for accurate P&L... the mockup currently doesnt show lending and debt tokens for all of
  the lending and debt venues." Verified via direct read of the real production instrument catalogue + code trace across
  instruments-service/unified-api-contracts, not guessed.'
assigned_vm: NA
resolved_by: instruments-service@72e0113+5226818, unified-api-contracts@48bfadff5
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
last_updated: 2026-07-07
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding — P&L-correctness risk, cross-repo, one real crash path.** Compound V3 and Morpho
> lending positions currently have no valid, distinct instrument identity for supply-vs-borrow — the strategy layer
> already assumes this split exists (`PositionPortfolio.net_value = total_supply_value - total_borrow_value`) and will
> misbehave (Compound: raise `UnknownInstrumentTypeError`; Morpho: silently have nowhere to represent a borrow position
> distinct from a supply position in the same market) the moment either protocol's positions are read for real P&L.

## What was actually found (real production catalogue read, 2026-07-07)

Read `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet` (7,223 rows) directly and traced the
writer code in `instruments-service/instruments_service/reference_data/adapters/defi/`.

### 1. AAVE_V3 + SPARK — already split, mislabeled (cheap fix)

- AAVE_V3: 171 real rows = 113 `A_TOKEN` + 58 `DEBT_TOKEN` (e.g. `AAVE_V3-ARBITRUM:A_TOKEN:AWETH` vs
  `AAVE_V3-ARBITRUM:DEBT_TOKEN:DEBTWETH`) — `aave_v3.py:421-436` already emits two separate `InstrumentRecord`s per
  reserve, correctly keyed.
- SPARK: 14 real rows = 8 `A_TOKEN` + 6 `DEBT_TOKEN`, same pattern.
- **The bug**: every one of these rows is stamped `instrument_type=LENDING` (100%, verified), even though
  `InstrumentType.A_TOKEN`/`DEBT_TOKEN` already exist as real enum members
  (`unified_api_contracts/_instrument_enums.py:56-57`) and `aave_v3.py:400` hardcodes `LENDING` for both record types.
  This is a **known, documented, half-finished migration** —
  `unified_api_contracts/internal/schemas/contracts.py:522-524` literally says: "Handlers currently emit
  `instrument_type=LENDING` while the long-term canonical is `a_token` — both keys point to the same contract." **Low
  severity in practice**: `ledger_asset_resolution.py:172-197` (`derive_ledger_asset_fields`) parses the KEY's middle
  segment (`A_TOKEN`/`DEBT_TOKEN`), not the stored `instrument_type` field, so downstream ledger resolution already
  works correctly today despite the mislabel.

### 2. COMPOUND_V3 — split into invalid enum values (real crash risk)

- 26 real rows = 13 `SUPPLY` + 13 `BORROW` (`compound_v3.py:263,272`) as the `instrument_type` value.
- **`SUPPLY`/`BORROW` are not `InstrumentType` enum members at all.** `asset_class_for_instrument_type()`
  (`ledger_asset_resolution.py:161-165`) does `InstrumentType(instrument_type)` and raises `UnknownInstrumentTypeError`
  on anything unrecognized — by explicit design ("never mask with UNKNOWN"). Any real Compound V3 supply/borrow position
  reaching the determinism-spine ledger writer today would **fail loud**, not silently misattribute — which is the
  correct failure mode, but it means Compound V3 lending positions cannot currently be P&L-attributed in production at
  all.
- **Fix scope**: rename the instrument_type AND the key segment to `A_TOKEN`/`DEBT_TOKEN` (matching AAVE_V3/SPARK's
  pattern) — this changes the instrument_id key shape, so it needs a GCS partition migration, not just a field edit.

### 3. MORPHO — no split at all (the real structural gap)

- All 465 real rows are `LENDING_MARKET` (`morpho.py:191`), one row per (collateral, loan, marketId) triple — **zero
  supply/borrow distinction**. A strategy holding a Morpho supply position and a borrow position in the same market has
  nowhere to represent them as distinct instruments today.
- `LENDING_MARKET` is also not a valid `InstrumentType` — same `UnknownInstrumentTypeError` crash-risk class as
  Compound.
- **Fix scope**: an actual model change, not a relabel — two records per market
  (`MORPHO-{CHAIN}:A_TOKEN:{coll}-{loan}:{key8}` / `:DEBT_TOKEN:...`), following the AAVE_V3 pattern.

### 4. What's NOT broken

- `lending_indices`' schema already carries both supply-side (`liquidity_index`) and borrow-side
  (`variable_borrow_index`) fields on ONE row per reserve, regardless of protocol (`DEFI_AAVE_V3_LENDING_INDICES`;
  `lending_indices_handler.py:855`). The market-data rate/index time series was never the gap — this is purely an
  instrument-IDENTITY gap (can we name/track a supply position distinctly from a borrow position), not a market-data
  schema gap.
- The strategy/execution layer already codes to the A_TOKEN/DEBT_TOKEN split as the correct model —
  `unified_api_contracts/internal/domain/execution_service/defi_position.py:97-109` (`is_supply`/ `is_borrow`),
  `strategy_service/position.py:31-34` (cites `AAVE_V3_ETH:A_TOKEN:AUSDT@ETHEREUM` as the canonical example),
  `PositionPortfolio.net_value = total_supply_value - total_borrow_value`. This confirms the operator's framing is
  exactly right — the fix target already exists in the strategy layer, the reference-data layer just hasn't caught up
  for 2 of 3 protocols checked.

## Not yet checked — same verification needed

FLUID, VENUS, BENQI, RADIANT, EULER_V2 (lending protocols shown in the mockup) and MARGINFI/SOLEND/KAMINO (Solana
lending) have NOT been checked against this same A_TOKEN/DEBT_TOKEN pattern — do not assume they follow AAVE_V3's
pattern or MORPHO's gap; each needs the same real-catalogue read before conclusions.

## Todos

- [x] ✅ [FIX] P1. **AAVE_V3 + SPARK: fix the `instrument_type` mislabel** — `aave_v3.py`/`spark.py` now stamp
      `InstrumentType.A_TOKEN`/`DEBT_TOKEN` per record (key was already correct, field-only fix). Verified no consumer
      read the raw field directly beyond the two already-audited coupled dicts (below) — safe solo fix as predicted.
      instruments-service@72e0113. Live-verified against the real subgraph + production catalogue 2026-07-13: 167/171
      AAVE_V3 rows self-healed via the unchanged key (upsert), remaining 4 are pre-existing delisted rows migrated
      separately (see the 2026-07-13 Progress Log entry).
- [x] ✅ [FIX] P0. **COMPOUND_V3: fix the invalid-enum crash risk** — **correction to this todo's own diagnosis**: the
      `instrument_type` FIELD was actually always `LENDING` (a real, valid enum member) for both compound_v3.py records
      — verified via direct code read 2026-07-13, contradicting this doc's original "13 SUPPLY + 13 BORROW as the
      instrument_type value" claim. The REAL crash risk was the KEY segment (`:SUPPLY:`/`:BORROW:`, not a valid
      `InstrumentType`, would raise `UnknownInstrumentTypeError` the moment `InstrumentKey.from_string()` ever parsed
      it) — same crash-risk class, different exact mechanism. Fixed: key segment SUPPLY→A_TOKEN/BORROW→DEBT_TOKEN +
      field now matches. instruments-service@72e0113. The 26 pre-existing SUPPLY/BORROW-keyed rows were migrated (see
      below), not just left to age out.
- [x] ✅ [CODE] P1. **MORPHO: add the missing A_TOKEN/DEBT_TOKEN split** — **found already done** by an earlier,
      undocumented change (not tracked back to this issue) discovered while re-verifying against the real production
      catalogue 2026-07-13: `morpho.py::_market_to_records` already emits two records per market
      (`MORPHO-{CHAIN}:A_TOKEN:A{pair_key}` / `:DEBT_TOKEN:DEBT{pair_key}`, `build_canonical_instrument_id`-routed),
      with 435 real correct pairs already live in the catalogue. Only remaining gap: 898 pre-existing
      `LENDING_MARKET`-keyed rows from before that fix (the catalogue had grown to 1,768 Morpho rows by 2026-07-13, not
      the 465 this doc originally measured on 2026-07-07) — migrated, see below. Also fixed the one loose end:
      `morpho.py`'s `get_instruments(instrument_type=...)` guard still only accepted `(None, InstrumentType.LENDING)` —
      updated to accept `A_TOKEN`/`DEBT_TOKEN`, matching what it actually emits. instruments-service@72e0113.
- [x] [VERIFY] P1. **Checked FLUID/VENUS/BENQI/RADIANT/EULER_V2 (EVM) and MARGINFI/SOLEND (Solana)** against the real
      production catalogue via the full adapter smoke-test workflow, 2026-07-07 — see
      [[mtds_is_full_adapter_smoketest_findings_2026_07_07]] for the full report. **Result: none of the 7 has a real
      A_TOKEN/DEBT_TOKEN split — all 7 share MORPHO's gap exactly** (flat `LENDING_MARKET` single-record structure, also
      not a valid `InstrumentType` enum member on FLUID/VENUS/BENQI/ RADIANT/EULER_V2 specifically — same crash-risk
      class as COMPOUND_V3). Additional findings from the same pass: VENUS/BENQI/RADIANT/EULER_V2's adapters are
      functional when called directly but never invoked by the production orchestrator (0 real catalogue rows despite
      working code — a separate wiring bug, tracked in the smoketest doc); FLUID's own `lending_indices` MTDS fetch is
      100% broken (uncaught `ContractCustomError`); MARGINFI/SOLEND have NO reference-data adapter at all (worse than
      the other 5 — pipeline-only, IS-side coverage not even started). KAMINO was reclassified as a POOL/vault protocol
      in this session's earlier mockup work, not lending — not re-checked here under the lending lens.
- [x] [CODE] P2. **Updated the drilldown mockup's DeFi lending nodes** to show the real A_TOKEN/DEBT_TOKEN split (target
      end-state) per protocol, with each protocol's current implementation status (already correct / mislabeled /
      crash-risk / missing) as an explicit note. Evidence:
      https://claude.ai/code/artifact/e2824e52-3a51-43e0-b4b1-933bee469f9d (round-9).
- [x] ✅ [CODE] P1. **OPERATOR DECISION 2026-07-08: canonicalize ALL lending protocols to A_TOKEN/DEBT_TOKEN** — **found
      FLUID/VENUS/RADIANT/EULER_V2/BENQI's adapter code already canonical** (another undocumented earlier fix, same
      pattern as Morpho — all 5 already emit `A_TOKEN`/`DEBT_TOKEN` pairs via a `_build_market_records` helper mirroring
      `aave_v3.py`). The real remaining gap was DATA, not code: VENUS/RADIANT/EULER_V2/BENQI had 0 real catalogue rows
      despite `DEFI_VENUE_PHASE` already flipped to `"live"` on 2026-07-10 (per `defi_venues.py` comments citing
      `mtds_is_full_adapter_smoketest_findings_2026_07_07.md` P1) — the phase flip had landed but no backfill had run
      since. Fixed by actually running one: triggered a real
      `python -m instruments_service --operation instruments --mode batch --asset-group DEFI --force` against
      `ENVIRONMENT=prod` 2026-07-13 (the default `ENVIRONMENT=dev` silently targets a dev bucket — caught before wasting
      the run), which fetched real data for all 4 (VENUS 6, RADIANT 8, EULER_V2 6, BENQI 2 instrument rows, 100%
      correctly typed) plus refreshed AAVE_V3/SPARK/COMPOUND_V3/FLUID/MORPHO. Ran
      `build_instrument_catalogue.py --mode incremental` to roll the new by_date writes into `catalog.parquet`
      (9,298→9,456 rows, monotonic guard ACCEPT) — confirmed this correctly ages out every row the fixed writers stopped
      producing into `available_to`-capped history automatically (no manual deletion needed for the live/current view).
      MARGINFI/SOLEND still have no reference-data adapter at all — out of scope for a canonicalization pass (that's
      new-capability work, not a migration); left untouched, not silently dropped from scope.

## Progress Log

- **2026-07-14 (🟡 durability gap discovered — Stage 4 is NOT reproducible from a `--mode full` rebuild)** — Ran
  `build_instrument_catalogue.py --asset-group defi --mode full` for an unrelated reason (backfilling
  `canonical_instrument_id`, see `canonical_instrument_id_cefi_defi_backfill_2026_07_14.md`). It correctly rebuilt from
  `instrument_availability/by_date/` and produced **9,456 rows vs the live catalogue's 10,372** — the monotonic-shrink
  guard correctly REJECTED the promote (`CATALOGUE_SHRINK_BLOCKED`, nothing written, live catalogue untouched and still
  correct). Root-caused (real GCS reads + re-running the migration script locally against a real backup, exact match
  confirmed: `9456 + 904 = 10360`, +12 organic growth = `10372`): **Stage 4's migration
  (`canonicalize_defi_lending_atoken_debttoken_catalog_2026_07_13.py`) reads/writes `prod/catalog.parquet` directly and
  never touches the underlying `by_date` source parquets** — those still hold the pre-fix `LENDING`/`:SUPPLY:`/
  `:BORROW:`/`:LENDING_MARKET:`-shaped rows for the DELISTED history. Stage 3's aging-out (live rows correctly migrating
  to the new writer's shape) reproduces fine on a full rebuild since it's a real reflection of `by_date` history: **only
  Stage 4's relabel/split of already-DELISTED rows is a catalog-only patch**, so any future `--mode full` DeFi rebuild
  will silently re-derive those specific historical rows in their pre-Stage-4 shape (relabeling them back to
  `LENDING`/invalid-enum types and re-collapsing the 904 MORPHO/FLUID A_TOKEN/DEBT_TOKEN pairs into 452 flat
  `LENDING_MARKET` rows) — exactly what almost happened here, caught only because the guard fires on aggregate row
  count, not because anything currently checks for this specific regression. **Current live state is NOT affected** —
  this run's output was never promoted, `prod/catalog.parquet` is still the correct, fully-canonicalized 10,372-row
  catalogue. **Not reopening as unresolved** (the live/current claim in Stage 4 still holds), but flagging for whoever
  next needs a DeFi `--mode full` rebuild: **either re-run
  `canonicalize_defi_lending_atoken_debttoken_catalog_2026_07_13.py --apply` immediately after any full rebuild, or
  (real fix, not yet scoped) bake the relabel/split logic into `build_instrument_catalogue.py`'s own row-construction so
  it's reproduced from `by_date` directly** — do not treat `--mode full` as a safe, side-effect-free operation for DeFi
  until one of those lands. The canonical_instrument_id backfill that surfaced this is being redirected to a targeted
  in-place catalog patch instead of `--mode full`, specifically to avoid this landmine.

- **2026-07-13 (RESOLVED — canonicalized workspace-wide, code + real data + historical catalogue, all 9 protocols)** —
  Operator: "still should fix it migrating to the canonical A_TOKEN/DEBT_TOKEN across everything and update the allowed
  enums to avoid confusion" then "Trigger live re-fetch... Migrate/delete stale catalog rows... Check
  FLUID/VENUS/RADIANT/EULER_V2/BENQI... do these but not forward fix only also backfills and migrations." **Stage 1
  (code)**: fixed AAVE_V3/SPARK (field-only relabel) + COMPOUND_V3 (key+field, real crash-risk fix) writers, plus the
  two coupled UAC dicts that would otherwise have silently broken on the relabel:
  `instrument_validation.py::_SINGLE_ASSET_DEFI_TYPES` was missing `DEBT_TOKEN` (would have write-time-REJECTED every
  debt-token record — A_TOKEN was there, DEBT_TOKEN wasn't, an asymmetry that only mattered once the field stopped being
  the shared `LENDING` value) and `venue_constants.py::INSTRUMENT_TYPES_BY_VENUE`/`INSTRUCTION_VALID_INSTRUMENT_TYPES`
  hardcoded `{"LENDING"}` for AAVE_V3/AAVE_V3_ETH. Also updated the 4 adapters' `get_instruments(instrument_type=...)`
  guards (aave_v3/spark/compound_v3/morpho) to accept `A_TOKEN`/`DEBT_TOKEN` instead of the no-longer-real `LENDING` —
  confirmed via a full workspace grep that every real caller invokes `get_instruments()` bare (no type filter), so this
  was zero-risk, done for correctness/clarity per the operator's "avoid confusion" ask. 342 tests updated+passing across
  4 test files (including one regression-guard file whose "single-type adapter" assumption no longer held for these 4 —
  split into a dedicated dual-type test). Shipped unified-api-contracts@48bfadff5 + instruments-service@72e0113, both
  quality-gates green. **Stage 2 (real data, not forward-fix-only)**: triggered a real live instrument refresh
  (`python -m instruments_service --operation instruments --mode batch --asset-group DEFI --force`) — first attempt
  silently ran against `ENVIRONMENT=dev` (the framework's default when unset; caught before treating it as a real
  verification), re-ran with `ENVIRONMENT=prod` explicitly. Confirmed the code fix end-to-end against the real
  `instrument_availability/by_date/day=2026-07-13/` raw writes (AAVE_V3-ETHEREUM and COMPOUND_V3-ETHEREUM both correctly
  emitting `A_TOKEN`/`DEBT_TOKEN`). Discovered along the way that VENUS/RADIANT/EULER_V2/BENQI's adapter code was ALSO
  already canonical (another undocumented prior fix) and their `DEFI_VENUE_PHASE` had already been flipped
  `pipeline→live` on 2026-07-10 — but zero real catalogue rows existed because no backfill had actually run since. This
  one refresh run backfilled all 4 for the first time (real data, correctly typed, verified below) — this IS the
  "backfills, not just forward-fix" the operator asked for. **Stage 3 (catalogue rollup)**: `catalog.parquet` is a
  separate, `instrument_availability/by_date/` roll-up (`scripts/build_instrument_catalogue.py`), not written directly
  by the live refresh — ran `--mode incremental` for real (dry-run first), 9,298→9,456 rows, monotonic guard ACCEPT.
  Confirmed this is a lifecycle catalogue by design ("cumulative, all-instruments-ever... NOT a current snapshot" per
  the script's own docstring): every row the fixed writers stopped producing under its old key/type got correctly
  `available_to`-capped automatically — AAVE_V3 self-healed 167/171 rows via its unchanged key (pure upsert),
  COMPOUND_V3's 26 old `SUPPLY`/`BORROW`-keyed rows aged into delisted history the moment the new
  `A_TOKEN`/`DEBT_TOKEN`-keyed rows appeared, same for MORPHO/FLUID's old `LENDING_MARKET`-keyed rows. No LIVE row
  anywhere was left mislabeled after this step alone. **Stage 4 (historical migration — operator confirmed: "yeah but
  you can migrate to fix it right")**: the DELISTED rows still carried the legacy shape (crash-risk key/type for any
  historical/backtest consumer), so wrote `scripts/canonicalize_defi_lending_atoken_debttoken_catalog_2026_07_13.py` — a
  pure relabel/split of already-catalogued rows (no field guessed): AAVE_V3 (4 rows, key already
  `A_TOKEN`/`DEBT_TOKEN`-shaped, field-only fix), COMPOUND_V3 (26 rows, key+field rewrite, symbol segment verified
  byte-identical to what the live writer emits), MORPHO+FLUID (904 rows — 898 Morpho + 6 Fluid — 1:2 SPLIT into
  A_TOKEN+DEBT_TOKEN pairs per market, every other column verified identical between a market's two live rows before
  assuming that shape for the split). Dry-run verified exact predicted counts (9,456→10,360 rows) and sample transforms
  against known real rows before applying. Applied with an automatic timestamped backup
  (`prod/catalog.20260713-123709.atokendebttoken.bak.parquet`). **Final verified state: all 9 protocols (AAVE_V3 171,
  SPARK 14, COMPOUND_V3 52, MORPHO 2,666, FLUID 24, VENUS 6, RADIANT 8, EULER_V2 6, BENQI 2 — 2,949 rows total) are 100%
  A_TOKEN/DEBT_TOKEN, zero non-canonical rows anywhere, live or historical.** Shipped instruments-service@5226818,
  quality-gates green. **False-alarm caught and NOT filed**: mid-investigation, Morpho's `venue` column appeared to
  mismatch its `instrument_id`'s embedded chain-suffixed prefix (bare `"MORPHO"` vs `"MORPHO-BASE"`/`"MORPHO-ETHEREUM"`)
  across 100% of rows — checked before writing an issue doc, and confirmed this is deliberate catalogue-wide schema
  (verified the same bare-protocol-family-name pattern on UNISWAP_V3/BALANCER/CURVE, none of which are in scope here):
  `venue` = protocol family, `chain` = a separate column, full chain-specific identity lives in `instrument_id`. Not a
  bug, correctly not touched. **Deliberately out of scope**: MARGINFI/SOLEND (no reference-data adapter exists at all —
  building one is new-capability work, not a canonicalization migration).
- **2026-07-07 (verification closed)** — The full 17-cluster adapter smoke test confirmed all 7 not-yet-verified lending
  protocols (FLUID/VENUS/BENQI/RADIANT/EULER_V2/MARGINFI/SOLEND) share MORPHO's exact gap — no A_TOKEN/DEBT_TOKEN split
  anywhere, same invalid-`InstrumentType` crash-risk class on 5 of them. Full detail in
  [[mtds_is_full_adapter_smoketest_findings_2026_07_07]]. This closes the P1 verification todo; remaining scope is
  unchanged (fix AAVE_V3/SPARK mislabel, fix COMPOUND_V3's invalid enum, add MORPHO's missing split, and now by
  extension the same fix for FLUID/VENUS/BENQI/RADIANT/ EULER_V2 — MARGINFI/SOLEND need an IS adapter built from scratch
  first, they have none today).
- **2026-07-08 (canonicalization decision)** — Operator: "shall we canonicalize to A_TOKEN and DEBT_TOKEN like aave for
  compound and morpho and anything else please so that its canonical." Confirmed and generalized the target state to
  every lending protocol in scope, not just the ones already flagged. Mockup updated same-session to show
  FLUID/VENUS/RADIANT/EULER_V2/BENQI/MARGINFI/SOLEND all targeting A_TOKEN/DEBT_TOKEN, each with an explicit
  current-state bug note (crash-risk / no-split-today / no-adapter-at-all as applicable) so the target is visible right
  next to the real gap. Real code migration is staged, not done yet — fixing will happen in stages per protocol
  (operator: "fixing will be in stages ofc").
- **2026-07-07** — Filed after the operator flagged (reviewing the drilldown mockup) that lending protocols need a real
  a-token/debt-token instrument split for correct P&L, same relationship as SPOT_ASSET vs SPOT_PAIR. Verified against
  the real production catalogue + code trace: AAVE_V3/SPARK already split but mislabeled (cheap fix), COMPOUND_V3 splits
  into invalid enum values (real crash risk, P0), MORPHO has no split at all (the real structural gap, needs a model
  change). Confirmed the strategy/execution layer already assumes the split exists — this is a reference-data layer
  catch-up, not a new architectural decision. No code changed yet; this is the findings ledger.
