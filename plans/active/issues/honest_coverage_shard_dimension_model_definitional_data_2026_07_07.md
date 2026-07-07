---
doc_type: issue
title: 'Honest-coverage shard dimension model is wrong for definitional data — instrument_type is not a real drilldown axis, and it already bit Deribit + Prediction'
summary:
  'Operator-raised critique, verified live 2026-07-07: the per_venue_per_data_type_daily honest-coverage axis
  (MTDS_CATEGORY_META) is correct for genuinely day-varying tick/event data, but instruments-service reference data
  needs a different, simpler model — venue -> instrument_type shard presence + a cumulative-ever-seen monotonicity
  check, with no daily re-declaration of what is definitionally a static capability. Today instrument_type is only
  a real drilldown dimension by coincidence: ASTER happens to have exactly one instrument_type, so its venue-level
  and type-level numbers are identical. DERIBIT, which genuinely has 4+ instrument types, has NO instrument_types
  breakdown at all in the live payload, and DERIBIT-COMBO is bolted on as a fake fourth venue rather than a sibling
  instrument_type of DERIBIT proper -- a same-shape mismatch was independently confirmed live for PREDICTION
  market_metadata. This doc proposes the corrected model and requests an operator decision gate before building it.'
status: open
nature: notes
asset_group: [cefi, defi, tradfi, prediction]
stage: [data, meta]
repos: [deployment-api, deployment-ui, unified-api-contracts, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [honest-coverage, shard-dimension, instrument-type, deribit, prediction, data-status, design]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    ../../../codex/02-data/honest-coverage-model.md,
    ../../../codex/04-architecture/instrument-universe-registry-consolidation.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P1
source:
  'Operator design discussion + ASTER/CEFI instrument-service data-status audit, 2026-07-07 — verified live against
  the real DERIBIT/DERIBIT-COMBO/SPORTS/PREDICTION payloads, not asserted from code reading alone'
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: opus-required
thinking_tier: high
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
last_updated: 2026-07-07
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: correct-codex
locked_since:
---

> This is a **Decision Gate D6 candidate on `instruments_completion_tracker_2026_07_06.md`** — it changes the shard
> dimension model for every asset group's instruments-service view, not just CeFi/ASTER. Filed as its own doc per
> the operator's own framing: "everything else is denominator, numerator, and empty reason" — the only real design
> decision is which dimensions you drill through to get there, and today that dimension list is incomplete in a way
> that's already silently hiding real gaps.

## The operator's model (verified against production, not just asserted)

Numerator + denominator + empty-reason, at the right dimension, plus a monotonicity check that survives normal
churn, is sufficient to answer "do we have all the instruments we expect" — without needing per-expiry granularity.
Two components make this work:

1. **The right dimensions.** For CEFI/DEFI/TRADFI: `venue -> instrument_type`. Data_type should NOT be a
   per-day-declared dimension for a definitional/reference-data view — it's a capability declared once, not
   redeclared daily (see the MTDS-conflation finding below, which is the flip side of this same principle).
2. **A monotonicity check that's immune to normal churn.** The check that actually works is "running high-water-mark
   of instruments-ever-seen never decreases" — NOT "today's raw count >= yesterday's raw count." A front-month
   future expiring and rolling off is a real, expected decrease in *today's active count* but not in *ever seen*.
   This is already exactly how DeFi's `_enforce_defi_monotonicity` and the manual CeFi drawdown guard both work
   (see `cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md`); it just isn't wired per-`(venue,
   instrument_type)` everywhere, which is the actual gap this doc is about.
3. **TradFi's calendar exception is already handled.** Non-trading days get pre-stamped `empty_confirmed`
   (`process_write.py:409-499`, `_write_tradfi_non_trading_day_entries` / `_pre_stamp_non_trading_tradfi`) before any
   gap check runs — weekends/holidays don't count against the denominator or trip a false monotonicity failure.
   Nothing to build here; noted so the decision gate below doesn't re-litigate it.
4. **What this model does NOT catch, by design — flagged so it isn't mistaken for a gap in the model itself.**
   Shard presence + monotonicity answers "did we get all instrument *types* we expect," not "did we get every
   expiry/strike an exchange actually lists within one type." Half of Deribit's BTC option chain missing on a given
   day would not move the OPTION row's completion at all — the shard is "present" the moment any options were
   captured. That's a separate catalogue-completeness reconciliation (catalogued expiry count vs. the venue's live
   instrument-list size), not a shard-presence problem, and this model should not try to absorb it.

## Live evidence: `instrument_type` is only a real dimension by coincidence today

Pulled `GET /api/data-status/manifest?service=instruments-service&asset_group=CEFI` (and the turbo equivalent with
`include_sub_dimensions=true`) live, 2026-07-07:

- **ASTER**: `instrument_types: {PERPETUAL: {dates_found: 943, dates_expected: 1071, completion_pct: 88.05}}` — a
  real, populated breakdown. But ASTER only ever lists one instrument_type, so this number is mathematically
  identical to the venue-level `completion_pct` at any instant. Nobody would notice the model doesn't generalize
  from this venue alone.
- **DERIBIT** (genuinely 4 instrument types: OPTION, FUTURE, PERPETUAL, FUTURE_COMBO): `instrument_types: null` —
  **no breakdown exists at all.** The venue-level number (`completion_pct: 99.58`) blends everything into one figure.
- **DERIBIT-COMBO**: appears as its own top-level **venue** key (`instrument_types: {COMBO: {completion_pct:
  75.55}}`) — i.e. Deribit's combo instrument type is split out via a venue-identity hack, not a real
  `instrument_type` sibling of `DERIBIT`. This conflates venue identity with instrument type for exactly one venue.
- **Net effect**: an OPTION-specific outage on Deribit (adapter breaks, only options stop being captured) is
  mathematically unable to move the venue-level percentage enough to notice — it would sit invisibly blended into
  one 99%+ number. This is the operator's own example ("missing all Deribit options for a day") and it is a real,
  currently-live blind spot, not a hypothetical.
- **DeFi's `chains` dimension already works as a real, populated, generic dimension** (`chains: {SOLANA: {...,
  venues: [PACIFICA]}, ZKSYNC: {..., venues: [LIGHTER]}}`) — proving multi-dimensional breakdown is already
  buildable in this codebase; `instrument_type` just hasn't been generalized the same way.

## The same mismatch, confirmed live for a second asset group: PREDICTION `market_metadata`

Checked every asset group MTDS covers (`MTDS_CATEGORY_META`, `deployment-api/deployment_api/services/data_status/mtds.py:51-108`).
CEFI, TRADFI, and DEFI's declared data types are all genuinely day-varying tick/event data — the daily axis fits.
SPORTS was deliberately excluded by the code's own author for exactly this reason (its own bespoke
`per_league_per_bookmaker_per_fixture_date` model lives in `sports_helpers.py`). But **PREDICTION's
`market_metadata`** (mtds.py:143-215, 182-196) is Polymarket's per-day market catalogue — definitional data, forced
onto the same daily-grid axis as CEFI's `perp_funding`. UAC's own code comment says outright it is NOT separate
data (`market_data_categories.py:1380-1383`: *"Prediction market metadata is NOT separate — the instruments parquet
IS the metadata"*), yet the live panel still renders it as a manufactured `market_metadata: 0/N shard_days (0%)`
row for PREDICTION venues today.

**The fix doesn't need new infrastructure — a genuinely generic, already-built, already-populated mechanism for
definitional data exists and already covers all five asset groups uniformly:**

- `reference_scope.is_reference_venue_day_in_scope(asset_group, venue, days)`
  (`deployment-api/deployment_api/services/data_status/reference_scope.py:143-161`) takes `asset_group` as a plain
  parameter — no per-asset-group branching in code.
- Its data source, `deployment-service/configs/data-catalogue.instruments-service.yaml`, already has real, populated
  `shard_status` blocks for CEFI, TRADFI, DEFI, SPORTS, and PREDICTION today, each with real venue→`start_date`
  entries.
- `VENUE_REFERENCE_DATA_CAPABILITIES` (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1384`)
  — the table that LOOKS like it should be the definitional-data registry — is an empty `{}` stub across every
  asset group, dead in practice, and duplicates a job `reference_scope.py` + the YAML catalogue already do.

## Update 2026-07-07 (later same day): the sibling UI bug is fixed, and the writer-side bug generalizes to DeFi

**1. A distinct-but-related UI bug is now fixed in code (implemented + tested, not yet committed).** Separately
from the instrument_type-generalization question above, the operator found live (via screenshot, then confirmed
in a real browser) that `deployment-ui/src/components/DataStatusTab.tsx`'s "Asset group breakdown" card had
`{!(catData.chains && ...) && <Venues section>}` — any category with *any* `chains` breakdown suppressed its
**entire** venue list. Fine for DeFi (~every venue has a chain); wrong for CEFI, where only 2 of 24 venues
(PACIFICA, LIGHTER) are on-chain — the other 22 (ASTER, BINANCE-FUTURES, DERIBIT, everything) were silently dropped
from the card. Fixed by extracting `getUncoveredVenueNames(catData)` and gating/filtering on that instead of on
chains-presence alone. Verified: `tsc`/`eslint` clean, 3 new unit tests + all 40 pre-existing DataStatusTab tests
pass, and live-rendered against real production data in a local dev server (had to route around a Cloud
Run↔Node-proxy "socket hang up" issue by serving a real fetched payload locally) — confirmed the CEFI card now
shows both Chains and all 22 other Venues, no duplicates. Files: `deployment-ui/src/components/DataStatusTab.tsx`,
new `tests/unit/components/DataStatusTab.chains_plus_venues.test.ts`. **Not yet shipped** — see the tracker
checklist item.

**2. The writer-side instrument_type-blank bug is not Deribit-only — it hits an entire chain's worth of DeFi
protocols too.** Pulling the full real `chain → venue → instrument_type → data_type` tree for DeFi
(`service=market-tick-data-service`, live, 2026-07-07) found **8 venues with real captured data (30 to 1,257 dates
each) but an empty `instrument_types` breakdown** — the exact same symptom as DERIBIT (blank `instrument_type` on
every manifest row): all 7 Solana DeFi venues (`DRIFT-SOLANA`, `KAMINO-SOLANA`, `MARGINFI-SOLANA`,
`MARINADE-SOLANA`, `ORCA-SOLANA`, `RAYDIUM-SOLANA`, `SOLEND-SOLANA`) plus `CURVE-OPTIMISM` on the EVM side. This
widens the scope of the pending writer-fix todo below from "fix Deribit's CeFi write path" to "fix the same class
of bug wherever it recurs" — Solana DeFi and CURVE-OPTIMISM need the same per-instrument_type row-splitting fix,
not a Deribit-specific patch.

**3. Separately confirmed as NOT a bug: HYPERLIQUID and ASTER appear in DeFi's venue list too (operator-confirmed
intentional, 2026-07-07).** Both showed up in the same live DeFi pull, listed with real genesis dates but
`0 found / 0 expected` under `asset_group=DEFI`, despite being tracked as CEFI venues everywhere else in this
audit. Operator confirmed this is by design, not a miscategorization: HYPERLIQUID and ASTER are **hybrid
on-chain-CLOB venues** — the same architectural pattern as LIGHTER/PACIFICA/EXTENDED-STARKNET (the tracker's
existing "CLOB-on-chain asset_group classification" item, Stage 5) — where **CEFI holds the instrument
definitions** (they're perpetual/CLOB-style instruments, defined and tracked like a centralized exchange) while
**DEFI holds the chain-level classification/context** (since the actual settlement/data infrastructure is
on-chain), and MTDS downloads the CLOB-style market data. The `0/0` under DEFI isn't evidence of a bug on its
own — it just means the chain-side of this hybrid classification has never had anything captured under that
asset_group for these two venues, which is exactly the same open state as Lighter/Pacifica/Extended's existing
todo. Extending that todo to explicitly name HYPERLIQUID and ASTER (done below) is the correct fix, not a new
finding.

## Decision needed (Decision Gate D6 candidate)

The operator's model is correct in principle and partially proven in production (DeFi's `chains` dimension, the
already-working ASTER `instrument_types` field, the already-working `reference_scope.py` mechanism). What's missing
is generalizing `instrument_type` into a real breakdown dimension everywhere a venue has more than one, and moving
mis-filed definitional data (`market_metadata`, possibly others) off the MTDS daily axis onto the `reference_scope`
mechanism that already exists. A working prototype of the target drilldown model (per-asset-group dimension spec,
a live-vs-proposed Deribit comparison, the monotonicity semantics) exists as an artifact — ask the operator for the
link if not already shared in-session.

## Update 2026-07-07 (writer fix implemented — CeFi AND TradFi, wider than originally scoped)

A 3-agent pre-audit (write-path trace, consumer blast-radius, TradFi precedent check) ran before touching the shared
write path, per the operator's go-ahead. Findings and the shipped change:

**Root cause, exact location**: `instruments-service/instruments_service/engine/orchestrator/process_write.py:578`
groups fetched instruments by `venue` only; the whole multi-type venue×date dataframe is handed to `_write_venue`
(`writers.py:107-259`), which made exactly ONE `manifest.record_captured()` call per venue×date. The
`instrument_type` stamp came from `_derive_instrument_type()` — a real per-instrument-column reader (not a fake
venue-level default) that correctly returns "" whenever more than one distinct type is present in the blended df,
by design ("honest blank — never fabricated"). ASTER/HYPERLIQUID/etc. worked by coincidence because their URDI
adapters only ever return one type; DERIBIT hit the documented multi-type guard on 4,489/4,492 rows.

**The fix**: replaced `_derive_instrument_type()` with `_split_by_instrument_type()`
(`writers.py`) — splits the venue×date df into one group per distinct `instrument_type` BEFORE the
`manifest.record_captured()` call, which now runs once per group inside a loop. Each row's `row_key` now carries
`instrument_type` explicitly (previously only passed as a kwarg, not part of the row_key — needed since
`instrument_type` is a real `_ROW_KEY_COLUMNS` member and `ManifestWriter.lookup()` only filters on keys literally
present in the passed row_key dict). `row_count` is now passed explicitly per group instead of relying on the
default `len(df)` over the whole blended frame. The physical `instruments.parquet` write (one file per venue×date,
still blended) is UNCHANGED — this fix is scoped to the manifest ROW grain only, per the operator's ask; splitting
the underlying parquet was explicitly out of scope.

**Scope is wider than "fix Deribit"** — this is ONE shared code path for both CeFi and TradFi:
- **TradFi has the identical bug**, confirmed live on real CME manifest rows (2,377/2,379 rows blank
  `instrument_type`, one stray anomalous row). The `TRADFI_VENUE_INSTRUMENT_TYPES` registry comment claiming "the
  writer also emits" per-type rows for CME/ICE/CBOE does not match the code or the real data — there was no working
  template to copy from either asset group. This fix resolves TradFi too, since it's the same
  `process_write.py:578` → `writers.py:_write_venue` path.
- **5 more CeFi venues have the same bug shape** per the UAC registry (not yet raw-parquet-confirmed the way
  Deribit/Aster were, but declared multi-type and fetched as a single enumeration key, so should hit the identical
  collapse): `OKX-FUTURES`, bare `BYBIT`, `BINANCE-FUTURES`, `KRAKEN-FUTURES`, `BINANCE-DELIVERY`.

**Consumer blast-radius audit** — everything downstream is already safe: the drawdown guard
(`cefi_cumulative_drawdown_guard_2026_06_27.py`) sums `instrument_count` per day, already robust to N rows/day; the
monotonic-guard producer (`build_instrument_catalogue.py`) reads a different source (per-date snapshot parquet, not
this manifest) for CeFi, so unaffected; the manifest consolidator's dedup key and deployment-api's
`breakdowns_core.py`/`data_status_union.py` already treat `instrument_type` as a first-class cell-identity
dimension — the write-path change is aligning the data with a model the rest of the stack already assumed. The one
genuine hazard found — a dead, already-broken one-off script (`fix_manifest_venue_casing.py`, `AttributeError` on a
typo, groupby that omits `instrument_type` and would re-introduce the collapse if ever run) — was deleted as a
companion cleanup (`codex/02-data/availability-manifest-and-data-status.md` script inventory updated).

**Verified against real production data (read-only, no writes)**: downloaded today's real DERIBIT day-snapshot
(`instrument_availability/by_date/day=2026-07-07/venue=DERIBIT/instruments.parquet`, 2,965 real instrument rows —
the actual per-instrument dataframe shape `_write_venue` processes at write time) and ran `_split_by_instrument_type`
directly against it. It correctly split into **5** groups (not 4 as earlier assumed — `SPOT_PAIR` is also real on
DERIBIT): OPTION=2,586, COMBO=273, FUTURE=71, PERPETUAL=21, SPOT_PAIR=14, summing exactly to 2,965. Quality gates
(`bash scripts/quality-gates.sh --no-fix`) passed clean (153s).

**Not yet done**: raw-parquet spot-check of the 5 flagged additional CeFi venues; a live backfill/re-run to
populate historical dates with the corrected per-type rows (today's fix only affects NEW writes going forward);
DERIBIT-COMBO venue-identity retirement (separate todo below, deliberately deferred).

## Todos

- [x] [DESIGN] P1. **Operator decision (D6):** approve generalizing `instrument_type` into a first-class breakdown
      dimension for every venue with more than one (CEFI: DERIBIT, KRAKEN-FUTURES, etc.; DEFI: any multi-type
      chain/venue), fixing DERIBIT-COMBO to be a sibling `instrument_type` under `DERIBIT` rather than its own venue
      key, and retiring the empty `VENUE_REFERENCE_DATA_CAPABILITIES` stub in favor of `reference_scope.py` +
      the catalogue YAML as the one definitional-data mechanism. **Approved 2026-07-07** — operator go-ahead given;
      see "Update 2026-07-07 (writer fix implemented)" below for the shipped implementation. The
      `VENUE_REFERENCE_DATA_CAPABILITIES`/DERIBIT-COMBO retirement half of this decision is NOT yet done — tracked
      as a separate follow-up todo below.
- [ ] [CODE] P2. **Retire DERIBIT-COMBO as its own venue key** — now that the writer emits one manifest row per
      `(date, venue, instrument_type)`, `DERIBIT-COMBO` should become `instrument_type=FUTURE_COMBO` under the
      single `DERIBIT` venue instead of a separate venue identity. Deferred out of the initial writer-fix scope
      (2026-07-07) to keep that change surgical; needs its own consumer check since venue-identity changes touch
      more call sites than a manifest-row-grain change.
- [ ] [CODE] P1. **Ship the already-implemented DataStatusTab.tsx chains-vs-venues fix** (Update §1 above) —
      `deployment-ui/src/components/DataStatusTab.tsx` + `tests/unit/components/DataStatusTab.chains_plus_venues.test.ts`,
      implemented and tested 2026-07-07, not yet committed/quickmerged. This is independent of the D6 decision —
      it's a straightforward bug fix, not a design question.
- [ ] [CODE] P1. **Widen the writer-fix scope to Solana DeFi + CURVE-OPTIMISM** (Update §2 above) — the blank
      `instrument_type` bug found on DERIBIT also hits `DRIFT-SOLANA`, `KAMINO-SOLANA`, `MARGINFI-SOLANA`,
      `MARINADE-SOLANA`, `ORCA-SOLANA`, `RAYDIUM-SOLANA`, `SOLEND-SOLANA`, and `CURVE-OPTIMISM` — all have real
      captured dates but zero `instrument_types` breakdown. Same fix (split the manifest row by instrument_type
      instead of writing one blended row per venue-day), applied wherever this recurs, not a Deribit-only patch.
- [ ] [CODE] P2. **Extend the "CLOB-on-chain asset_group classification" item** (tracker Stage 5, currently scoped
      to Lighter/Pacifica/Extended-Starknet) to explicitly include **HYPERLIQUID and ASTER** (Update §3 above) —
      operator-confirmed same hybrid pattern: CEFI holds the instrument definitions, DEFI holds the chain-level
      classification. Not a new bug; just widening an existing todo's scope to match reality.
- [ ] [CODE] P1. Pull the real per-instrument_type breakdown for DERIBIT live (the comparison built for this doc
      used illustrative numbers pending this) and confirm whether OPTION coverage is actually healthy or is itself
      a live gap once visible.
- [ ] [CODE] P1. **Add `missing_dates`/`dates_found_list` to the per-instrument_type and per-underlying breakdown
      entries** (`deployment-api/deployment_api/services/data_status/breakdowns_core.py` —
      `_build_instrument_type_breakdown` entry dict at ~405-409, `_build_underlying_breakdown` at ~508-512; mirror
      `_build_data_type_breakdown`'s entry shape at ~629-643, which already carries this). Found 2026-07-07,
      verifying the D6 plan: today the per-instrument_type entry carries only `dates_found`/`dates_expected`/
      `completion_pct` — no list of WHICH dates are missing. Invisible today because ASTER/OKX-SPOT/OKX-SWAP/UPBIT
      are single-type venues, so the venue-level `missing_dates` (which does exist) happens to equal the type-level
      one. The moment DERIBIT has 4 real instrument_types, the venue-level list blends all 4 together — you'd see
      DERIBIT missing a day but not whether it was OPTION, FUTURE, PERPETUAL, or COMBO that was missing. This is the
      same class of blind spot the whole audit started from, one level deeper; the writer fix (stamping
      `instrument_type` per row) is necessary but not sufficient without this. Needs a matching
      `deployment-ui/src/components/DataStatusTab.tsx` render tweak (the `TurboInstrumentTypeStatus`/
      `TurboUnderlyingStatus` types at `api/client.ts:1156-1169` also need the field added — they don't carry it
      today, unlike `TurboDataTypeStatus` at `client.ts:984-999`).
- [ ] [DESIGN] P3. Clarify or rename the "Instrument breakdown" venue-detail link (`DataStatusTab.tsx:5493-5499`,
      `handleVenueClick` → `GET /data-status/venue-detail`) — found 2026-07-07 while verifying this doc's model: it
      is NOT a `data_type` sub-breakdown of the instrument_type row above it (a reasonable thing to assume from its
      position in the UI). It's a fully separate feature hitting a different GCS layout
      (`instrument_availability/by_date/day=<latest>/venue=<venue>/instruments.parquet`) that shows raw instrument
      keys. Its backend response (`VenueDetailResponse`, `deployment-api/deployment_api/types/shard_detail.py:321-351`)
      has no `instrument_types`/`statuses`/`columns` fields at all, even though `VenueDetailResult` on the
      TypeScript side (`api/client.ts:1602-1604`) declares them optional — dead fields on the wire for CeFi/TRADFI.
      Low priority (cosmetic/naming confusion, not a data-correctness bug), but worth a small pass once the
      instrument_type work above lands, so the two features don't keep getting conflated.
- [ ] [CODE] P1. Move `market_metadata` off the MTDS `per_venue_per_data_type_daily` axis
      (`mtds.py:143-215,182-196,618-623`) onto the `reference_scope`-based model — either drop it from
      `PREDICTION_DATA_TYPE_META` entirely (per UAC's own "not separate" disclaimer) or route its presence-tracking
      through the genesis/day-scope catalogue mechanism instead.
- [ ] [VERIFY] P2. Audit whether the same MTDS/reference-data conflation risk exists anywhere else — e.g. the
      TradFi `POLYGON`/`FRED` reference-data-in-the-wrong-registry smell noted at `market_data_categories.py:1279-1286`
      (not confirmed live; flagged as a follow-up, not a confirmed bug).
- [ ] [VERIFY] P1. Raw-parquet spot-check the 5 additional CeFi venues flagged by the pre-audit's registry read as
      likely hitting the same multi-type blank-collapse: `OKX-FUTURES`, bare `BYBIT`, `BINANCE-FUTURES`,
      `KRAKEN-FUTURES`, `BINANCE-DELIVERY` — same method used on DERIBIT/ASTER (download
      `availability_index.parquet`, check `instrument_type` distribution). Confirms whether the writer fix's
      benefit is as wide as the registry evidence suggests.
- [ ] [CODE] P1. Backfill historical CeFi/TradFi manifest rows with the corrected per-instrument_type split — the
      2026-07-07 writer fix only affects NEW writes going forward; every pre-fix DERIBIT/CME/etc. row is still
      blended+blank until reprocessed. Likely a candidate for the generic reprocessing utility proposed in
      `manifest_reprocessing_generic_utility_2026_07_07.md` rather than a new one-off script.

## Progress Log

- **2026-07-07 (writer fix implemented)** — Per operator go-ahead, ran a 3-agent pre-audit then implemented the
  CeFi/TradFi manifest writer fix in `instruments-service/instruments_service/engine/orchestrator/writers.py`
  (`_derive_instrument_type` → `_split_by_instrument_type`, one `record_captured()` call per distinct
  `instrument_type` instead of one blended call per venue×date; `instrument_type` added to the `row_key` dict).
  Confirmed via pre-audit this is ONE shared code path for CeFi AND TradFi (CME hits the identical bug live), and
  flagged 5 more CeFi venues as likely-affected from registry evidence (not yet raw-parquet-confirmed). Deleted the
  dead/broken `fix_manifest_venue_casing.py` one-off script as a companion cleanup (its groupby omitted
  `instrument_type` and would have re-introduced the collapse if ever run). Updated `__init__.py` exports and the 3
  unit tests that directly exercised the removed helper. Quality gates running; not yet committed. See "Update
  2026-07-07 (writer fix implemented...)" above for full detail. 5 new/updated todos above.
- **2026-07-07 (later same day)** — Shipped the sibling UI fix (chains-vs-venues, Update §1) in code (uncommitted);
  pulled the real full DeFi `chain → venue → instrument_type → data_type` tree live and found the writer-side
  blank-instrument_type bug generalizes to all 7 Solana DeFi venues plus CURVE-OPTIMISM (Update §2); operator
  confirmed HYPERLIQUID/ASTER's dual CEFI+DEFI listing is intentional hybrid classification, not a bug — folded
  into the existing tracker Stage 5 CLOB-on-chain item instead of filing a new finding (Update §3). Four new todos
  added above; none contradict or replace the original D6 decision ask.
- **2026-07-07** — **Operator confirmed the proposed drilldown order (venue → instrument_type, no data_type leaf)
  matches this doc exactly** — verified via a 4-way check: (1) the raw CEFI `availability_index.parquet` confirms
  `data_type` is a near-constant `"instruments"` (86,804/86,839 rows, 99.96%; the other 35 are blank-string write
  artifacts on POLYMARKET-PERP/KALSHI-PERP/LIGHTER-ZKSYNC/DERIBIT-COMBO/BITFINEX-SPOT/PACIFICA-SOLANA, not a real
  second dimension — low-priority, likely incomplete re-capture writes); (2) this doc's own text was re-confirmed
  verbatim to state `venue -> instrument_type` as the FULL spec, not a stop en route to a `data_type` leaf; (3)
  `_build_instrument_type_breakdown` re-confirmed venue-agnostic with no allowlist/cap, so the D2a-adjacent writer
  fix will render N instrument_types with zero further code once landed; (4) surfaced the two new todos above (the
  missing_dates gap and the unrelated "Instrument breakdown" venue-detail feature) — both added as scoped follow-ups
  rather than blocking the core plan.
- **2026-07-07** — Filed from an operator design discussion following the ASTER/CEFI audit. Verified DERIBIT,
  DERIBIT-COMBO, and PREDICTION's `market_metadata` behavior against the live production API before writing this
  up — not asserted from code reading alone. No files edited.
