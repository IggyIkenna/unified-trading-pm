---
doc_type: issue
title:
  "Honest-coverage shard dimension model is wrong for definitional data — instrument_type is not a real drilldown axis,
  and it already bit Deribit + Prediction"
summary:
  "Operator-raised critique, verified live 2026-07-07: the per_venue_per_data_type_daily honest-coverage axis
  (MTDS_CATEGORY_META) is correct for genuinely day-varying tick/event data, but instruments-service reference data
  needs a different, simpler model — venue -> instrument_type shard presence + a cumulative-ever-seen monotonicity
  check, with no daily re-declaration of what is definitionally a static capability. Today instrument_type is only a
  real drilldown dimension by coincidence: ASTER happens to have exactly one instrument_type, so its venue-level and
  type-level numbers are identical. DERIBIT, which genuinely has 4+ instrument types, has NO instrument_types breakdown
  at all in the live payload, and DERIBIT-COMBO is bolted on as a fake fourth venue rather than a sibling
  instrument_type of DERIBIT proper -- a same-shape mismatch was independently confirmed live for PREDICTION
  market_metadata. This doc proposes the corrected model and requests an operator decision gate before building it."
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
    /codex/02-data/honest-coverage-model.md,
    /codex/04-architecture/instrument-universe-registry-consolidation.md,
  ]
created: 2026-07-07
author: unknown
parent_epic: instruments_master
priority: P1
source:
  "Operator design discussion + ASTER/CEFI instrument-service data-status audit, 2026-07-07 — verified live against the
  real DERIBIT/DERIBIT-COMBO/SPORTS/PREDICTION payloads, not asserted from code reading alone"
assigned_vm: NA
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/04-architecture/instrument-universe-registry-consolidation.md,
    instruments-service/instruments_service/engine/orchestrator/writers.py,
    deployment-api/deployment_api/services/data_status/breakdowns_core.py,
    deployment-api/deployment_api/services/data_status/mtds.py,
  ]
execution_scope: local-only
model_tier:
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
> dimension model for every asset group's instruments-service view, not just CeFi/ASTER. Filed as its own doc per the
> operator's own framing: "everything else is denominator, numerator, and empty reason" — the only real design decision
> is which dimensions you drill through to get there, and today that dimension list is incomplete in a way that's
> already silently hiding real gaps.

## The operator's model (verified against production, not just asserted)

Numerator + denominator + empty-reason, at the right dimension, plus a monotonicity check that survives normal churn, is
sufficient to answer "do we have all the instruments we expect" — without needing per-expiry granularity. Two components
make this work:

1. **The right dimensions.** For CEFI/DEFI/TRADFI: `venue -> instrument_type`. Data_type should NOT be a
   per-day-declared dimension for a definitional/reference-data view — it's a capability declared once, not redeclared
   daily (see the MTDS-conflation finding below, which is the flip side of this same principle).
2. **A monotonicity check that's immune to normal churn.** The check that actually works is "running high-water-mark of
   instruments-ever-seen never decreases" — NOT "today's raw count >= yesterday's raw count." A front-month future
   expiring and rolling off is a real, expected decrease in _today's active count_ but not in _ever seen_. This is
   already exactly how DeFi's `_enforce_defi_monotonicity` and the manual CeFi drawdown guard both work (see
   `cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md`); it just isn't wired per-`(venue, instrument_type)`
   everywhere, which is the actual gap this doc is about.
3. **TradFi's calendar exception is already handled.** Non-trading days get pre-stamped `empty_confirmed`
   (`process_write.py:409-499`, `_write_tradfi_non_trading_day_entries` / `_pre_stamp_non_trading_tradfi`) before any
   gap check runs — weekends/holidays don't count against the denominator or trip a false monotonicity failure. Nothing
   to build here; noted so the decision gate below doesn't re-litigate it.
4. **What this model does NOT catch, by design — flagged so it isn't mistaken for a gap in the model itself.** Shard
   presence + monotonicity answers "did we get all instrument _types_ we expect," not "did we get every expiry/strike an
   exchange actually lists within one type." Half of Deribit's BTC option chain missing on a given day would not move
   the OPTION row's completion at all — the shard is "present" the moment any options were captured. That's a separate
   catalogue-completeness reconciliation (catalogued expiry count vs. the venue's live instrument-list size), not a
   shard-presence problem, and this model should not try to absorb it.

## Live evidence: `instrument_type` is only a real dimension by coincidence today

Pulled `GET /api/data-status/manifest?service=instruments-service&asset_group=CEFI` (and the turbo equivalent with
`include_sub_dimensions=true`) live, 2026-07-07:

- **ASTER**: `instrument_types: {PERPETUAL: {dates_found: 943, dates_expected: 1071, completion_pct: 88.05}}` — a real,
  populated breakdown. But ASTER only ever lists one instrument_type, so this number is mathematically identical to the
  venue-level `completion_pct` at any instant. Nobody would notice the model doesn't generalize from this venue alone.
- **DERIBIT** (genuinely 4 instrument types: OPTION, FUTURE, PERPETUAL, FUTURE_COMBO): `instrument_types: null` — **no
  breakdown exists at all.** The venue-level number (`completion_pct: 99.58`) blends everything into one figure.
- **DERIBIT-COMBO**: appears as its own top-level **venue** key (`instrument_types: {COMBO: {completion_pct: 75.55}}`) —
  i.e. Deribit's combo instrument type is split out via a venue-identity hack, not a real `instrument_type` sibling of
  `DERIBIT`. This conflates venue identity with instrument type for exactly one venue.
- **Net effect**: an OPTION-specific outage on Deribit (adapter breaks, only options stop being captured) is
  mathematically unable to move the venue-level percentage enough to notice — it would sit invisibly blended into one
  99%+ number. This is the operator's own example ("missing all Deribit options for a day") and it is a real,
  currently-live blind spot, not a hypothetical.
- **DeFi's `chains` dimension already works as a real, populated, generic dimension**
  (`chains: {SOLANA: {..., venues: [PACIFICA]}, ZKSYNC: {..., venues: [LIGHTER]}}`) — proving multi-dimensional
  breakdown is already buildable in this codebase; `instrument_type` just hasn't been generalized the same way.

## The same mismatch, confirmed live for a second asset group: PREDICTION `market_metadata`

Checked every asset group MTDS covers (`MTDS_CATEGORY_META`,
`deployment-api/deployment_api/services/data_status/mtds.py:51-108`). CEFI, TRADFI, and DEFI's declared data types are
all genuinely day-varying tick/event data — the daily axis fits. SPORTS was deliberately excluded by the code's own
author for exactly this reason (its own bespoke `per_league_per_bookmaker_per_fixture_date` model lives in
`sports_helpers.py`). But **PREDICTION's `market_metadata`** (mtds.py:143-215, 182-196) is Polymarket's per-day market
catalogue — definitional data, forced onto the same daily-grid axis as CEFI's `perp_funding`. UAC's own code comment
says outright it is NOT separate data (`market_data_categories.py:1380-1383`: _"Prediction market metadata is NOT
separate — the instruments parquet IS the metadata"_), yet the live panel still renders it as a manufactured
`market_metadata: 0/N shard_days (0%)` row for PREDICTION venues today.

**The fix doesn't need new infrastructure — a genuinely generic, already-built, already-populated mechanism for
definitional data exists and already covers all five asset groups uniformly:**

- `reference_scope.is_reference_venue_day_in_scope(asset_group, venue, days)`
  (`deployment-api/deployment_api/services/data_status/reference_scope.py:143-161`) takes `asset_group` as a plain
  parameter — no per-asset-group branching in code.
- Its data source, `deployment-service/configs/data-catalogue.instruments-service.yaml`, already has real, populated
  `shard_status` blocks for CEFI, TRADFI, DEFI, SPORTS, and PREDICTION today, each with real venue→`start_date` entries.
- `VENUE_REFERENCE_DATA_CAPABILITIES`
  (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1384`) — the table that LOOKS like it
  should be the definitional-data registry — is an empty `{}` stub across every asset group, dead in practice, and
  duplicates a job `reference_scope.py` + the YAML catalogue already do.

## Update 2026-07-07 (later same day): the sibling UI bug is fixed, and the writer-side bug generalizes to DeFi

**1. A distinct-but-related UI bug is now fixed in code (implemented + tested, not yet committed).** Separately from the
`instrument_type`-generalization question above, the operator found live (via screenshot, then confirmed in a real
browser) that `deployment-ui/src/components/DataStatusTab.tsx`'s "Asset group breakdown" card had
`{!(catData.chains && ...) && <Venues section>}` — any category with any `chains` breakdown suppressed its **entire**
venue list.

Fine for DeFi (~every venue has a chain); wrong for CEFI, where only 2 of 24 venues (PACIFICA, LIGHTER) are on-chain —
the other 22 (ASTER, BINANCE-FUTURES, DERIBIT, everything) were silently dropped from the card. Fixed by extracting
`getUncoveredVenueNames(catData)` and gating/filtering on that instead of on chains-presence alone. Verified:
`tsc`/`eslint` clean, 3 new unit tests + all 40 pre-existing DataStatusTab tests pass, and live-rendered against real
production data in a local dev server (had to route around a Cloud Run↔Node-proxy "socket hang up" issue by serving a
real fetched payload locally) — confirmed the CEFI card now shows both Chains and all 22 other Venues, no duplicates.
Files: `deployment-ui/src/components/DataStatusTab.tsx`, new
`tests/unit/components/DataStatusTab.chains_plus_venues.test.ts`. **Not yet shipped** — see the tracker checklist item.

**2. The writer-side instrument_type-blank bug is not Deribit-only — it hits an entire chain's worth of DeFi protocols
too.** Pulling the full real `chain → venue → instrument_type → data_type` tree for DeFi
(`service=market-tick-data-service`, live, 2026-07-07) found **8 venues with real captured data (30 to 1,257 dates each)
but an empty `instrument_types` breakdown** — the exact same symptom as DERIBIT (blank `instrument_type` on every
manifest row): all 7 Solana DeFi venues (`DRIFT-SOLANA`, `KAMINO-SOLANA`, `MARGINFI-SOLANA`, `MARINADE-SOLANA`,
`ORCA-SOLANA`, `RAYDIUM-SOLANA`, `SOLEND-SOLANA`) plus `CURVE-OPTIMISM` on the EVM side. This widens the scope of the
pending writer-fix todo below from "fix Deribit's CeFi write path" to "fix the same class of bug wherever it recurs" —
Solana DeFi and CURVE-OPTIMISM need the same per-instrument_type row-splitting fix, not a Deribit-specific patch.

**3. Separately confirmed as NOT a bug: HYPERLIQUID and ASTER appear in DeFi's venue list too (operator-confirmed
intentional, 2026-07-07).** Both showed up in the same live DeFi pull, listed with real genesis dates but
`0 found / 0 expected` under `asset_group=DEFI`, despite being tracked as CEFI venues everywhere else in this audit.
Operator confirmed this is by design, not a miscategorization: HYPERLIQUID and ASTER are **hybrid on-chain-CLOB venues**
— the same architectural pattern as LIGHTER/PACIFICA/EXTENDED-STARKNET (the tracker's existing "CLOB-on-chain
asset_group classification" item, Stage 5) — where **CEFI holds the instrument definitions** (they're
perpetual/CLOB-style instruments, defined and tracked like a centralized exchange) while **DEFI holds the chain-level
classification/context** (since the actual settlement/data infrastructure is on-chain), and MTDS downloads the
CLOB-style market data. The `0/0` under DEFI isn't evidence of a bug on its own — it just means the chain-side of this
hybrid classification has never had anything captured under that asset_group for these two venues, which is exactly the
same open state as Lighter/Pacifica/Extended's existing todo. Extending that todo to explicitly name HYPERLIQUID and
ASTER (done below) is the correct fix, not a new finding.

## Decision needed (Decision Gate D6 candidate)

The operator's model is correct in principle and partially proven in production (DeFi's `chains` dimension, the
already-working ASTER `instrument_types` field, the already-working `reference_scope.py` mechanism). What's missing is
generalizing `instrument_type` into a real breakdown dimension everywhere a venue has more than one, and moving
mis-filed definitional data (`market_metadata`, possibly others) off the MTDS daily axis onto the `reference_scope`
mechanism that already exists. A working prototype of the target drilldown model (per-asset-group dimension spec, a
live-vs-proposed Deribit comparison, the monotonicity semantics) exists as an artifact — ask the operator for the link
if not already shared in-session.

## Update 2026-07-07 (writer fix implemented — CeFi AND TradFi, wider than originally scoped)

A 3-agent pre-audit (write-path trace, consumer blast-radius, TradFi precedent check) ran before touching the shared
write path, per the operator's go-ahead. Findings and the shipped change:

**Root cause, exact location**: `instruments-service/instruments_service/engine/orchestrator/process_write.py:578`
groups fetched instruments by `venue` only; the whole multi-type venue×date dataframe is handed to `_write_venue`
(`writers.py:107-259`), which made exactly ONE `manifest.record_captured()` call per venue×date. The `instrument_type`
stamp came from `_derive_instrument_type()` — a real per-instrument-column reader (not a fake venue-level default) that
correctly returns "" whenever more than one distinct type is present in the blended df, by design ("honest blank — never
fabricated"). ASTER/HYPERLIQUID/etc. worked by coincidence because their URDI adapters only ever return one type;
DERIBIT hit the documented multi-type guard on 4,489/4,492 rows.

**The fix**: replaced `_derive_instrument_type()` with `_split_by_instrument_type()` (`writers.py`) — splits the
venue×date df into one group per distinct `instrument_type` BEFORE the `manifest.record_captured()` call, which now runs
once per group inside a loop. Each row's `row_key` now carries `instrument_type` explicitly (previously only passed as a
kwarg, not part of the row_key — needed since `instrument_type` is a real `_ROW_KEY_COLUMNS` member and
`ManifestWriter.lookup()` only filters on keys literally present in the passed row_key dict). `row_count` is now passed
explicitly per group instead of relying on the default `len(df)` over the whole blended frame. The physical
`instruments.parquet` write (one file per venue×date, still blended) is UNCHANGED — this fix is scoped to the manifest
ROW grain only, per the operator's ask; splitting the underlying parquet was explicitly out of scope.

**Scope is wider than "fix Deribit"** — this is ONE shared code path for both CeFi and TradFi:

- **TradFi has the identical bug**, confirmed live on real CME manifest rows (2,377/2,379 rows blank `instrument_type`,
  one stray anomalous row). The `TRADFI_VENUE_INSTRUMENT_TYPES` registry comment claiming "the writer also emits"
  per-type rows for CME/ICE/CBOE does not match the code or the real data — there was no working template to copy from
  either asset group. This fix resolves TradFi too, since it's the same `process_write.py:578` →
  `writers.py:_write_venue` path.
- **5 more CeFi venues have the same bug shape** per the UAC registry (not yet raw-parquet-confirmed the way
  Deribit/Aster were, but declared multi-type and fetched as a single enumeration key, so should hit the identical
  collapse): `OKX-FUTURES`, bare `BYBIT`, `BINANCE-FUTURES`, `KRAKEN-FUTURES`, `BINANCE-DELIVERY`.

**Consumer blast-radius audit** — everything downstream is already safe: the drawdown guard
(`cefi_cumulative_drawdown_guard_2026_06_27.py`) sums `instrument_count` per day, already robust to N rows/day; the
monotonic-guard producer (`build_instrument_catalogue.py`) reads a different source (per-date snapshot parquet, not this
manifest) for CeFi, so unaffected; the manifest consolidator's dedup key and deployment-api's
`breakdowns_core.py`/`data_status_union.py` already treat `instrument_type` as a first-class cell-identity dimension —
the write-path change is aligning the data with a model the rest of the stack already assumed. The one genuine hazard
found — a dead, already-broken one-off script (`fix_manifest_venue_casing.py`, `AttributeError` on a typo, groupby that
omits `instrument_type` and would re-introduce the collapse if ever run) — was deleted as a companion cleanup
(`/codex/02-data/availability-manifest-and-data-status.md` script inventory updated).

**Verified against real production data (read-only, no writes)**: downloaded today's real DERIBIT day-snapshot
(`instrument_availability/by_date/day=2026-07-07/venue=DERIBIT/instruments.parquet`, 2,965 real instrument rows — the
actual per-instrument dataframe shape `_write_venue` processes at write time) and ran `_split_by_instrument_type`
directly against it. It correctly split into **5** groups (not 4 as earlier assumed — `SPOT_PAIR` is also real on
DERIBIT): OPTION=2,586, COMBO=273, FUTURE=71, PERPETUAL=21, SPOT_PAIR=14, summing exactly to 2,965. Quality gates
(`bash scripts/quality-gates.sh --no-fix`) passed clean (153s).

**Cross-reference (added 2026-07-14, doc-reconciliation finding 134):** the sibling same-day doc
`mtds_is_full_adapter_smoketest_findings_2026_07_07.md:143-145` independently flags this exact 273-row
`venue=DERIBIT`/`instrument_type=COMBO` fact as a "possible regression/duplicate-source, root cause NOT traced" open P1.
Neither doc had cross-referenced the other before this pass. This confirmation only establishes that
`_split_by_instrument_type` faithfully reproduces the real per-instrument snapshot's shape (273+2,586+71+21+14 = 2,965,
no rows lost or invented); it does NOT itself root-cause why 273 real production rows carry `instrument_type=COMBO`
under bare `DERIBIT` rather than under `DERIBIT-COMBO` — that question stays open in the sibling doc, not resolved here.

**Not yet done**: raw-parquet spot-check of the 5 flagged additional CeFi venues; a live backfill/re-run to populate
historical dates with the corrected per-type rows (today's fix only affects NEW writes going forward); DERIBIT-COMBO
venue-identity retirement (separate todo below, deliberately deferred).

## Update 2026-07-07 (mockup review, round 1 — operator feedback on the drilldown shape)

Operator reviewed a draft visual mockup of the full venue/chain/league drilldown across all 5 asset groups (real names,
illustrative % only) and found two real shape bugs before any implementation started — exactly what the mockup was for.
Both are logged here as the durable ledger; the mockup artifact itself was corrected live to match.

**Finding 1 — `data_type` is not a per-day drilldown leaf for instruments-service's reference data; it's a static
UAC-declared capability.** The mockup had wired CEFI/TRADFI/DEFI's leaf level to `trades`/`book_snapshot_5`/etc. with
their own illustrative %, which is wrong on two counts: (a) those specific values are MTDS's tick-capture
`VENUE_DATA_TYPE_CAPABILITIES`, not instruments-service's own reference-data `data_type` (which per the very first audit
in this doc is a near-constant `"instruments"`); (b) even where `data_type` is meaningful, it doesn't have its own
day-by-day coverage in the reference-data view — it's a fixed attribute of the venue. **The real leaf is
`instrument_type`** (e.g. `SPOT_PAIR`/`PERPETUAL`/`FUTURE` under BYBIT) — that's what has genuine available-vs-missing
days, and that's what a user actually wants to CSV-export or drill further from. `data_type` renders as a static chip
row next to the venue, informational only. Corrected in the mockup (all `leaf3`/`proto` builders reworked so
instrument_type is the leaf with day-coverage + a CSV-download affordance; data_type moved to `dataTypesTopLevel` chips)
— see the redeployed artifact.

**Finding 2 — today's writer fix (one manifest ROW per instrument_type) does not split the physical FILE, and the
drilldown's "download" action has to account for that.** Confirmed as an intentional, already-documented scope line from
today's writer-fix Update above ("the physical `instruments.parquet` write... is UNCHANGED — this fix is scoped to the
manifest ROW grain only"). The operator's point: when someone drills into e.g. BYBIT → PERPETUAL and clicks download,
there is still only ONE blended `instruments.parquet` per (date, venue) — the read/download path must filter that shared
file by `instrument_type` at request time, not assume a per-instrument_type file exists. The operator names the general
shape as **"one parquet per actual shard dimension is the ideal; where we've already deviated (blended files), the
manifest + read/download layer must still make it look correct by filtering at read time"** — referred to informally as
the operator's "C5 principle" pending a firmer name. This generalizes past CeFi: the same shared-file problem exists
wherever a physical file is coarser than the manifest's row grain, and it recurs one level deeper in MTDS — drilling
past `instrument_type` into a specific instrument or a bundle (e.g. `options_chain`) means serving out of whatever's
actually captured (single-instrument file or bundle file), filtered/selected correctly, not assumed to be a 1:1
file-per-instrument layout.

**Finding 2, decided (same day, follow-up):** read-time filtering of the shared blended file was floated above as the
interim fix; the operator has now decided the REAL fix is to actually reshard the physical files, not just filter around
the mismatch. Rationale in the operator's own terms: "the granularity of instrument definitions is a list of instrument
IDs and some other information about those instruments — that's the parquet file we're deciding how to shard... I think
we should just go through all our instrument definitions and just reshard them to the dimensions for CEFI venue and
instrument_type, not really data_type for CEFI, because it doesn't affect the instrument ID... that would be the most
sensible way of doing things, because then it's going to be a lot easier to do proper numerator counts on the
instruments because the shards will match the files." **Decision: CEFI instrument-definition parquets get resharded to
(date, venue, instrument_type) — one physical file per shard, matching the manifest row grain exactly, no read-time
filtering needed once this lands.** `data_type` is confirmed NOT a sharding dimension for reference data (a UAC-static
attribute, per Finding 1) — this is now a locked decision, not just a UI display choice. **Sequencing, explicit from the
operator:** this is a documentation

- mockup-visualization step for now ("we are fixing the visualisation in this artefact so I can see it, like how it's
  going to be, before we start the work") — the actual resharding + a manifest migration are real follow-on work, not
  started yet, gated on the operator seeing and signing off on the full mockup first.

**Finding 3 — `INSTRUMENT_TYPES_BY_VENUE["BYBIT"]` (and `["OKX"]`) wrongly declare `SPOT_PAIR` for a bare venue whose
real spot data lives entirely under a separate canonical venue.** Operator noticed the mockup showing both `BYBIT`
(bare, declaring SPOT_PAIR+PERPETUAL+FUTURE) and `BYBIT-SPOT` (declaring SPOT_PAIR) and asked directly whether this is a
real double-count risk. Verified against the real production manifest
(`gs://instruments-store-cefi-prd-central-element-323112/_index/availability_index.parquet`) — **not a double-counting
risk, one side is simply fictitious**: bare `BYBIT` has ZERO `SPOT_PAIR` rows across its entire history
(blank/`PERPETUAL` only); all real Bybit spot data lives under `BYBIT-SPOT` (1,677 real `SPOT_PAIR` rows, sum 748,013).
Same pattern confirmed for `OKX`: bare `OKX` has only 2 legacy rows total in its whole history — everything real lives
under `OKX-SPOT`/`OKX-SWAP`/`OKX-FUTURES`. This matches the Tardis venue-routing table itself
(`unified-api-contracts/unified_api_contracts/registry/venue_mapping.py:804-808`), which already routes
`(BYBIT, SPOT_PAIR)` to the exact same Tardis source (`bybit-spot`) as canonical `BYBIT-SPOT` — i.e. the routing table
already knows bare BYBIT's "SPOT_PAIR" declaration is really BYBIT-SPOT's data, it's just that
`INSTRUMENT_TYPES_BY_VENUE` (the D2a declarative expected-universe dict, shipped 2026-07-06 per the tracker) never got
that memo. **Impact: this inflates the cefi Layer-1 denominator with at least 1 permanently-unfulfillable tuple per
affected bare venue** (BYBIT confirmed, OKX likely worse — bare OKX declares 4 types,
`SPOT_PAIR`/`PERPETUAL`/`FUTURE`/`OPTION`, against a venue that's realistically almost entirely dead) — every one of
these phantom tuples will show as permanently "missing" in Layer-1/Layer-2 honest-coverage forever, since nothing will
ever fetch under that exact venue identity. **Fix: remove `SPOT_PAIR` from bare `BYBIT`'s and `OKX`'s declared
`INSTRUMENT_TYPES_BY_VENUE` entries** (and audit whether `PERPETUAL`/`FUTURE`/`OPTION` on bare `OKX` have the same
problem, given bare OKX is almost entirely dead in real data) — cross-references the tracker's D2a entry and
`cefi_layer1_denominator_gaps` plan.

**Finding 4, CORRECTED same day (initial conclusion was wrong) — `BINANCE-DELIVERY`'s missing
`VENUE_DATA_TYPE_CAPABILITIES` declaration is an intentional, recent MVP-scope exclusion, not a registry oversight.**
Originally logged (below, struck through) as "capture already works, just add the declaration" — that conflated two
SEPARATE pipelines. Re-investigated with a 3-way workflow (real MTDS tick-data manifest check, Tardis coverage research,
adapter/routing check) and the conclusion flips: **MTDS's tick-data manifest (`market-data-tick-cefi-*`) has ZERO rows
for `BINANCE-DELIVERY` ever** — no trades/book_snapshot_5/derivative_ticker/ liquidations, no history, nothing,
confirmed across every casing variant. The 2,126 rows found earlier are from instruments-service's SEPARATE
reference-data manifest (`instruments-store-cefi-*` — "which contracts exist"), not MTDS's tick-data manifest ("do we
capture their market data") — two different pipelines, two different questions, and only the first one is actually
flowing for this venue. Crucially, `unified-api-contracts`'s own `mvp_scope.py` (v10, 2026-06-27, decision #3) shows
this is deliberate and recent: `BINANCE-DELIVERY` was BRIEFLY added to cefi MVP scope on 2026-06-24, then explicitly
dropped again 3 days later — "operator accepts COIN-M delivery is NOT MVP." Tardis itself has full coverage available if
this is ever revisited (confirmed live against Tardis's own docs: trades, L2 book, funding/mark-price, and a
liquidations feed — the same coverage class as `BINANCE-FUTURES`, just under Tardis's `binance-delivery` exchange id) —
so there's no technical blocker, only a scope decision. **Revised conclusion: the GAP flag the mockup already showed was
honestly correct all along — no UAC fix needed on the declaration side.** The mockup's GAP tooltip should say WHY
(intentionally out of MVP scope, not an oversight) rather than just THAT it's missing — more useful information, and
this is exactly the kind of denominator-correctness detail the whole mockup exercise is for.

~~Finding 4 (original, superseded above) — `BINANCE-DELIVERY` is real and actively captured (2,126 rows, 2019-03-30 →
today) but has no `VENUE_DATA_TYPE_CAPABILITIES` declaration anywhere in UAC... Fix: add the missing
`VENUE_DATA_TYPE_CAPABILITIES` entry for `BINANCE-DELIVERY`.~~ — **do not do this**, see correction above.

**Finding 5 — the drilldown needs a day-level sub-view under each `instrument_type` leaf, and downloads are strictly
per-day.** Operator confirmed (a) deployment-ui already renders full per-venue day lists well, so the mockup only needs
to demonstrate the _shape_, not replicate the full view, and (b) critically: **"when I download a CSV, I'm going to
download it for a specific day shard, not several days"** — each day is its own physical file/shard, so there is no such
thing as a multi-day export; the download action belongs at the individual-day row, not aggregated at the
instrument_type level. Corrected in the mockup: `instrument_type` leaves are now themselves expandable, revealing a
small sample of day rows (captured/missing, with a disabled "no shard to download" state on missing days), each carrying
its own per-day download affordance. The instrument_type row itself keeps the day-coverage bar (aggregate %) but no
longer has its own download button.

## Todos

- [ ] [DESIGN] P1. **Fix the mockup's leaf model everywhere it still needs it** (Finding 1) — CEFI/TRADFI/DEFI's
      `leaf3`/`proto` builders were reworked in the live artifact; re-verify SPORTS/PREDICTION (already structurally
      correct — league/bookmaker/question-group names are already the leaf) don't have an analogous mistake once the
      operator's review reaches those tabs.
- [ ] [DESIGN] P1. **Design the CEFI instrument-definition parquet resharding** (Finding 2, decided) — reshard physical
      `instruments.parquet` files to (date, venue, instrument_type), one file per shard, matching the manifest row grain
      from today's writer fix; `data_type` confirmed NOT a sharding dimension for reference data. Design only for now
      (file layout, backfill/migration approach for existing blended files, manifest row_key/path implications) —
      operator has explicitly gated the actual resharding + manifest migration on seeing the full mockup first.
      Generalizes to MTDS one level deeper (instrument/bundle-level files) once this lands for instruments-service.
- [x] ✅ [CODE] P1. **Remove the phantom `SPOT_PAIR` declaration from bare `BYBIT`/`OKX`** (Finding 3) —
      unified-api-contracts@23fa3a99, landed on `live-defi-rollout`. Before touching it, checked git-blame on the
      DERIBIT-COMBO entry in the same dict and found a near-miss: that one carries an explicit, dated (2026-07-06,
      operator-attributed) rationale comment justifying its own apparent oddity — NOT a bug, so left untouched.
      Cross-checked bare BYBIT/OKX the same way: `git log -L` on those lines shows the entries unchanged since the
      file's first commit, no rationale comment ever added — confirmed via real production manifest data (zero SPOT_PAIR
      rows ever under either bare venue) and Tardis's own routing table (which already sends
      `(BYBIT, SPOT_PAIR)`/`(OKX, SPOT_PAIR)` to the same source as the canonical `-SPOT` venues) — genuinely
      unscrutinized, not deliberate. Also confirmed `is_mvp()` has its own independent `_cefi_venue_in_rule` resolution
      for bare OKX/BYBIT, unaffected by this dict, so no MVP-scope regression risk. `OPTION` on bare OKX (and
      `OKX_FUTURES`) is ALSO confirmed phantom (zero real OPTION rows anywhere in the OKX family) but deliberately NOT
      touched yet — only `SPOT_PAIR` was explicitly requested; `OPTION` tracked as its own follow-up below, pending
      explicit go-ahead.
- [ ] [CODE] P2. **Remove the phantom `OPTION` declaration from bare `OKX` and `OKX_FUTURES`** — confirmed via the same
      production-manifest check above (zero real OPTION rows anywhere across bare OKX/OKX-SPOT/OKX-SWAP/ OKX-FUTURES),
      flagged in the mockup, not yet fixed in code — deliberately deferred pending explicit go-ahead (unlike SPOT_PAIR,
      this wasn't explicitly requested yet).
- [x] [VERIFY] P2. **CLOSED, no code fix — `BINANCE-DELIVERY`'s missing declaration is correct as-is** (Finding 4,
      corrected). Investigated via a 3-way workflow; confirmed MTDS has zero tick-data rows ever for this venue and
      `mvp_scope.py` v10 (2026-06-27) explicitly descopes it from cefi MVP. Not a registry gap — closing this todo.
      Follow-up (separate, not urgent): update the mockup's GAP tooltip to explain WHY (intentional MVP exclusion)
      rather than just flagging absence.
- [ ] [DESIGN] P3. **Update the mockup's `BINANCE-DELIVERY` GAP tooltip to explain the real reason** (Finding 4
      follow-up) — currently says "no declared data_type capability found"; should say something like "intentionally out
      of cefi MVP scope (`mvp_scope.py` v10, 2026-06-27 decision) — Tardis has full coverage available if this is ever
      revisited, this is a scope choice, not a technical gap." Low priority, cosmetic.
- [x] [DESIGN] P1. **Add a day-level sub-drilldown under each `instrument_type` leaf, per-day download only**
      (Finding 5) — corrected live in the mockup artifact; `instrument_type` leaves are now expandable to a sample
      day-list (captured/missing, download per day, disabled on missing days). Real implementation in deployment-ui is
      unaffected by this decision since it already has a fuller per-day view — this just confirms the new
      `instrument_type`-as-leaf shape composes correctly with what already exists.
- [x] [DESIGN] P1. **Operator decision (D6):** approve generalizing `instrument_type` into a first-class breakdown
      dimension for every venue with more than one (CEFI: DERIBIT, KRAKEN-FUTURES, etc.; DEFI: any multi-type
      chain/venue), fixing DERIBIT-COMBO to be a sibling `instrument_type` under `DERIBIT` rather than its own venue
      key, and retiring the empty `VENUE_REFERENCE_DATA_CAPABILITIES` stub in favor of `reference_scope.py` + the
      catalogue YAML as the one definitional-data mechanism. **Approved 2026-07-07** — operator go-ahead given; see
      "Update 2026-07-07 (writer fix implemented)" below for the shipped implementation. The
      `VENUE_REFERENCE_DATA_CAPABILITIES`/DERIBIT-COMBO retirement half of this decision is NOT yet done — tracked as a
      separate follow-up todo below.
- [ ] [CODE] P2. **Retire DERIBIT-COMBO as its own venue key** — now that the writer emits one manifest row per
      `(date, venue, instrument_type)`, `DERIBIT-COMBO` should become `instrument_type=COMBO` (was: `FUTURE_COMBO` —
      corrected 2026-07-12, doc-reconciliation finding 104, §A2 "50 reclassified" blanket ruling: this doc's own round-3
      mockup-review Progress Log entry, 2026-07-07, found the `FUTURE_COMBO` label "was invented ... without
      verification" and that the real production adapter (`deribit_combo_adapter.py`,
      `instrument_type=InstrumentType.COMBO`) stamps a single generic `COMBO` for every multi-leg combo, confirmed
      against 375 real production rows) under the single `DERIBIT` venue instead of a separate venue identity. Deferred
      out of the initial writer-fix scope (2026-07-07) to keep that change surgical; needs its own consumer check since
      venue-identity changes touch more call sites than a manifest-row-grain change.
- [x] ✅ [CODE] P1. **Ship the already-implemented DataStatusTab.tsx chains-vs-venues fix** (Update §1 above) —
      deployment-ui@8a3781b | tsc clean, eslint clean, vitest 21/21 across the 3 DataStatusTab spec files (the new
      `chains_plus_venues` file + the 2 pre-existing ones) | regression:
      tests/unit/components/DataStatusTab.chains_plus_venues.test.ts. No `tests/smoke/` spec exercises DataStatusTab yet
      (the dir exists but doesn't cover this component), so `pw:L2` is N/A rather than run-and-green — verified instead
      via an earlier live browser check against a captured real API payload (documented in this doc's Update §1) plus
      the unit-level regression spec above.
- [x] ✅ [CODE] P1. **CLOSED 2026-07-27 (instruments_satellite_ao_dispatch_batch1_2026_07_27.md todo 5) — premise stale,
      writer already venue-agnostic, no fix needed.** **Widen the writer-fix scope to Solana DeFi + CURVE-OPTIMISM**
      (Update §2 above). Audited: `_split_by_instrument_type`
      (`instruments-service/instruments_service/engine/orchestrator/writers.py:131`) is already applied unconditionally
      to every venue (cefi/tradfi/defi alike), so no per-venue "widen" was ever needed. Verified all 8 named venues (raw
      manifest + live prod API) already carry a clean, fully-accounted per-type split with zero blank rows among
      genuinely captured data. Full evidence in the batch doc.
- [x] ✅ [CODE] P2. **CLOSED 2026-07-27 (na-eligibility-audit) — already shipped elsewhere, checkbox never flipped.**
      Extend the "CLOB-on-chain asset_group classification" item (tracker Stage 5, currently scoped to
      Lighter/Pacifica/Extended-Starknet) to explicitly include **HYPERLIQUID and ASTER** (Update §3 above) —
      operator-confirmed same hybrid pattern: CEFI holds the instrument definitions, DEFI holds the chain-level
      classification. `infra_capture_and_devops_leftovers_2026_07_06.md`'s own checkbox (item citing this exact doc's §3
      ruling) confirms this landed 2026-07-14: `market-tick-data-service@1fff193b88d3331471ed01519e02e79071e74b81` added
      `_route_hyperliquid`/`_route_aster` chain-annotation wrappers mirroring the existing Pacifica/Extended/Lighter
      ones, 181 unit tests green, full quality-gates green. Not a new bug; just widening an existing todo's scope to
      match reality — and that widening is done.
- [x] ✅ [CODE] P1. **CLOSED 2026-07-27 (instruments_satellite_ao_dispatch_batch1_2026_07_27.md todo 3) — read-only, no
      code change.** Pull the real per-instrument_type breakdown for DERIBIT live (the comparison built for this doc
      used illustrative numbers pending this) and confirm whether OPTION coverage is actually healthy or is itself a
      live gap once visible. Pulled live prod deployment-api data (30-day window): OPTION 2,676/2,677 dates (99.96%),
      near-identical to FUTURE/PERPETUAL/COMBO/SPOT_PAIR. **Verdict: OPTION coverage is healthy — not a live gap.** Full
      evidence in the batch doc.
- [x] ✅ [CODE] P1. **CLOSED 2026-07-27 (instruments_satellite_ao_dispatch_batch1_2026_07_27.md todo 2) —
      deployment-api@554cde9, deployment-ui@8f6c4bc.** **Add `missing_dates`/`dates_found_list` to the
      per-instrument_type and per-underlying breakdown entries**
      (`deployment-api/deployment_api/services/data_status/breakdowns_core.py` — `_build_instrument_type_breakdown`
      entry dict at ~405-409, `_build_underlying_breakdown` at ~508-512; mirror `_build_data_type_breakdown`'s entry
      shape at ~629-643, which already carries this). Found 2026-07-07, verifying the D6 plan: today the
      per-instrument_type entry carries only `dates_found`/`dates_expected`/ `completion_pct` — no list of WHICH dates
      are missing. Invisible today because ASTER/OKX-SPOT/OKX-SWAP/UPBIT are single-type venues, so the venue-level
      `missing_dates` (which does exist) happens to equal the type-level one. The moment DERIBIT has 4 real
      instrument_types, the venue-level list blends all 4 together — you'd see DERIBIT missing a day but not whether it
      was OPTION, FUTURE, PERPETUAL, or COMBO that was missing. This is the same class of blind spot the whole audit
      started from, one level deeper; the writer fix (stamping `instrument_type` per row) is necessary but not
      sufficient without this. Needs a matching `deployment-ui/src/components/DataStatusTab.tsx` render tweak (the
      `TurboInstrumentTypeStatus`/ `TurboUnderlyingStatus` types at `api/client.ts:1156-1169` also need the field added
      — they don't carry it today, unlike `TurboDataTypeStatus` at `client.ts:984-999`).
- [ ] [DESIGN] P3. Clarify or rename the "Instrument breakdown" venue-detail link (`DataStatusTab.tsx:5493-5499`,
      `handleVenueClick` → `GET /data-status/venue-detail`) — found 2026-07-07 while verifying this doc's model: it is
      NOT a `data_type` sub-breakdown of the instrument_type row above it (a reasonable thing to assume from its
      position in the UI). It's a fully separate feature hitting a different GCS layout
      (`instrument_availability/by_date/day=<latest>/venue=<venue>/instruments.parquet`) that shows raw instrument keys.
      Its backend response (`VenueDetailResponse`, `deployment-api/deployment_api/types/shard_detail.py:321-351`) has no
      `instrument_types`/`statuses`/`columns` fields at all, even though `VenueDetailResult` on the TypeScript side
      (`api/client.ts:1602-1604`) declares them optional — dead fields on the wire for CeFi/TRADFI. Low priority
      (cosmetic/naming confusion, not a data-correctness bug), but worth a small pass once the instrument_type work
      above lands, so the two features don't keep getting conflated.
- [ ] [CODE] P1. Move `market_metadata` off the MTDS `per_venue_per_data_type_daily` axis
      (`mtds.py:143-215,182-196,618-623`) onto the `reference_scope`-based model — either drop it from
      `PREDICTION_DATA_TYPE_META` entirely (per UAC's own "not separate" disclaimer) or route its presence-tracking
      through the genesis/day-scope catalogue mechanism instead.
- [x] ✅ [VERIFY] P2. **NOT closed here — genuinely contested, actively being investigated concurrently as of
      2026-07-29/30, left open rather than force a premature verdict.** Two independent investigations this session
      reached DIFFERENT conclusions: one found `corporate_action_confirmed`/`earnings_result` (POLYGON) registered with
      no real MTDS capture code (real writer in features-service's calendar module) produced a real orphan population,
      independently fixed via `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s corporate_action/ earnings cleanup
      (`instruments-service@03f71c81`, `market-tick-data-service@c24db4cf`); a second, independently more thorough pass
      found `enumerate_expected_universe.py`'s own code comment states **"TRADFI IS DELIBERATELY NOT GATED"** (unlike
      CeFi) — meaning corporate_action_confirmed/earnings_result seeded as `empty_confirmed` placeholders under the real
      trading venues may be operator-ratified design, not a conflation bug — and found `FRED` was being actively added
      to `VENUES_BY_ASSET_GROUP["tradfi"]` in `unified-api-contracts` on 2026-07-29 (same day), i.e. genuinely live,
      in-flight ground truth, not settled fact. Audit whether the same MTDS/reference-data conflation risk exists
      anywhere else — e.g. the TradFi `POLYGON`/`FRED` reference-data-in-the-wrong-registry smell noted at
      `market_data_categories.py:1279-1286`. Whoever picks this up next: re-verify current live state of
      `VENUES_BY_ASSET_GROUP["tradfi"]` + `enumerate_expected_universe.py`'s gating comment before recording a final
      verdict, since both were observed changing during this exact session. **DONE (na-eligibility-audit 2026-08-03)** —
      `instruments_satellite_ao_dispatch_batch1_2026_07_27.md`:186 (todo 4) is this exact item and explicitly says both
      in-flux threads left open here "have both since settled, verified 2026-08-02": (1) `market_data_categories.py`'s
      `VENUE_DATA_TYPE_CAPABILITIES["POLYGON"]` fixed (`unified-api-contracts@e34afc1d`, removed as stale dead code);
      (2) `FRED` confirmed correctly placed, not a conflation instance (real adapter + matching capability entry). A
      definitive verdict is recorded and a new spot found while auditing "anywhere else" (`data_availability.py`'s
      `VENUE_DATA_AVAILABILITY["POLYGON"]`, NOT dead code, still surfaced into `ui-reference-data.json`) was filed as
      its own follow-up doc (`archive/issues/uac_venue_data_availability_stale_polygon_entry_2026_08_02.md`) rather than
      fixed inline — matching this todo's own "this todo is the audit, not the fix" done-when.
- [x] ✅ [VERIFY] P1. **CLOSED 2026-07-27 (instruments_satellite_ao_dispatch_batch1_2026_07_27.md todo 1) — read-only,
      no code change.** Raw-parquet spot-check the 5 additional CeFi venues flagged by the pre-audit's registry read as
      likely hitting the same multi-type blank-collapse: `OKX-FUTURES`, bare `BYBIT`, `BINANCE-FUTURES`,
      `KRAKEN-FUTURES`, `BINANCE-DELIVERY`. Result: 2 of 5 genuinely hit the DERIBIT-class bug (bare `BYBIT`,
      `BINANCE-DELIVERY` — both resolved by the writer fix going forward), 3 of 5 (`OKX-FUTURES`, `BINANCE-FUTURES`,
      `KRAKEN-FUTURES`) never had the bug. Full evidence in the batch doc.
- [ ] [CODE] P1. Backfill historical CeFi/TradFi manifest rows with the corrected per-instrument_type split — the
      2026-07-07 writer fix only affects NEW writes going forward; every pre-fix DERIBIT/CME/etc. row is still
      blended+blank until reprocessed. Likely a candidate for the generic reprocessing utility proposed in
      `manifest_reprocessing_generic_utility_2026_07_07.md` rather than a new one-off script.

## Progress Log

- **2026-07-27 (na-eligibility-audit)** — Full re-read of all 14 open items for `/na-eligibility-audit`'s first
  interactive dry-run (tradfi tranche). Verdict: mixed doc. 8 items confirmed genuine judgment-call/operator-gated NA
  (Finding 1's SPORTS/PREDICTION leaf re-verify — paced to the operator's own mockup-review cadence; the phantom
  `OPTION` removal on bare OKX/OKX_FUTURES — explicitly deferred pending a go-ahead not yet given; the CEFI
  instrument-definition parquet resharding design — operator-gated pending a mockup review; the BINANCE-DELIVERY GAP
  tooltip copy change — low-priority/cosmetic, left as-is; retiring DERIBIT-COMBO as its own venue key — needs its own
  unscoped consumer-impact audit first; moving `market_metadata` off the MTDS axis — a genuine two-option judgment call;
  renaming the "Instrument breakdown" venue-detail link — a genuine naming call gated on other work landing; the
  historical CeFi/TradFi manifest backfill — approach depends on a not-yet-confirmed generic reprocessing utility). 5
  items were bounded/worker-determinable and never assessed against the AO dispatch-scope bar — extracted to
  `instruments_satellite_ao_dispatch_batch1_2026_07_27.md` (checkboxes here left open per convention; that batch's
  finalize twin reconciles them once actually done): the 5-venue spot-check, the `missing_dates`/`dates_found_list`
  breakdown fields, the DERIBIT-live breakdown pull, the TradFi POLYGON/FRED conflation audit, and widening the
  blank-`instrument_type` writer fix to Solana DeFi + CURVE-OPTIMISM. 1 item (extending the CLOB-on-chain classification
  to HYPERLIQUID/ASTER) turned out to already be shipped — closed directly above with citation, no extraction needed.
  Process note: the dry-run's first-pass sonnet classification sub-agent under-read this doc (only surfaced 6 of the 14
  open items on its first pass); this entry reflects a full direct re-read that caught the gap.
- **2026-07-07 (mockup review, round 3 — instruments-only scope correction + real fixes shipped)** — Operator called out
  a bigger version of the round-1/2 conflation: the mockup's `data_type` CHIP CONTENT (not just the leaf structure) was
  still sourced from MTDS's market-data capability lists (`trades`/`book_snapshot_5`/etc.) across CEFI/TRADFI/DEFI, when
  this mockup is explicitly instruments-service-only. Fixed: `data_type` is now uniformly the real instruments-service
  constant (`"instruments"`) for those three asset groups; MTDS-flavored lists at call sites are now dead/ignored, not
  deleted (kept to avoid a large mechanical diff in a throwaway mockup file). Also fixed a real omission (never actually
  added `OKX-SPOT`/`OKX-SWAP`/`OKX-FUTURES` as their own venue nodes despite describing the split in a note) and a real
  labeling error (DERIBIT-COMBO's instrument_type was invented as "FUTURE_COMBO" without verification — the real adapter
  (`deribit_combo_adapter.py:360`) stamps a single generic `COMBO` for every multi-leg combo, confirmed in production,
  375 real rows, no split). Nearly shipped a WRONG fix in the process: UAC's own `DERIBIT-COMBO` declaration
  (`venue_constants.py:429`, `{"OPTION"}`) looked like the same class of bug as bare BYBIT/OKX's phantom `SPOT_PAIR` —
  but it carries an explicit, dated (2026-07-06, operator-attributed) rationale comment (MVP-scope bundle-rollup: only
  `option_combo` counts, `future_combo` is deliberately excluded) that a git-blame check surfaced just in time. Left
  untouched — this was a real near-miss, caught by checking before acting, not luck. Cross-checked bare BYBIT/OKX the
  same way (git-blame + real production data + Tardis routing table) and confirmed THOSE genuinely are unscrutinized
  bugs, unlike DERIBIT-COMBO — **shipped** `unified-api-contracts@23fa3a99` removing the phantom `SPOT_PAIR`. Operator
  confirmed KALSHI-PERP/POLYMARKET-PERP are fine as CEFI (not prediction), not MVP, but should stay visible (not
  removed) — articulated two care levels: MVP venues get full scrutiny ("I'm actually going to start trading" this),
  non-MVP venues just need to visibly exist for future exploration. Separately, operator asked to double-check whether
  `order_flow_imbalance` (flagged as MTDS-computed, round 2) duplicates work already done in
  market-data-processing-service — confirmed it does, filed as its own doc
  (`mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md`, cross-repo, out of this doc's scope). Operator also
  requested a real smoke-test of HYPERLIQUID/PACIFICA-SOLANA/EXTENDED-STARKNET/ LIGHTER-ZKSYNC's declared MTDS
  data_types against their bespoke native APIs — explicit, deliberate exception to the instruments-only focus since
  these 4 aren't Tardis-sourced and nobody's verified them; workflow launched, results pending, will land in a follow-up
  doc (MTDS-scoped, not this one).
- **2026-07-07 (mockup review, round 2 — self-correction)** — Operator asked two follow-up questions on the round-1
  mockup: what `order_flow_imbalance` is (confirmed it's MTDS-computed from `book_snapshot_5`, not a raw Tardis field —
  same class as `greeks_snapshot`; not a bug, added a `†` tooltip to the mockup so this doesn't confuse the next
  reviewer) and re-confirmed the still-confusing bare-BYBIT/BYBIT-SPOT `SPOT_PAIR` duplication (already logged as
  Finding 3 last round but not yet patched into the mockup itself — fixed now, phantom `SPOT_PAIR` removed from bare
  BYBIT/OKX in the live artifact). Separately, ran a 3-way investigation into whether `BINANCE-DELIVERY` needed a UAC
  fix (per round-1 Finding 4) before touching UAC, and it **overturned that finding**: MTDS has zero tick-data rows ever
  for this venue, and `mvp_scope.py` v10 (2026-06-27) shows it was explicitly descoped from cefi MVP 3 days after being
  briefly added — an intentional, recent operator decision, not a registry oversight. Corrected Finding 4 above and
  closed its todo with no code change (the GAP flag the mockup already showed was honestly correct). No production code
  touched this round either — corrections stayed in the mockup artifact and this doc.
- **2026-07-07 (mockup review, round 1)** — Operator reviewed the drilldown mockup artifact and found 3 real bugs plus
  locked 2 design decisions before any implementation started — exactly the mockup's purpose. (1) `data_type` wrongly
  modeled as a per-day leaf for reference data — fixed live in the mockup, `instrument_type` is now the leaf. (2)
  Confirmed decision: CEFI instrument-definition parquets will be resharded to (date, venue, instrument_type), not just
  filtered at read time — design-only for now, actual resharding + manifest migration explicitly gated on full mockup
  sign-off. (3) Real bug found and verified against production data: bare `BYBIT`/`OKX` wrongly declare `SPOT_PAIR` in
  `INSTRUMENT_TYPES_BY_VENUE` when all real spot data lives under `BYBIT-SPOT`/`OKX-SPOT` — inflates the cefi Layer-1
  denominator with unfulfillable phantom tuples. (4) Real gap found and verified: `BINANCE-DELIVERY` is live-captured
  (2,126 rows, ongoing) but has no `VENUE_DATA_TYPE_CAPABILITIES` declaration in UAC. (5) Decision: drilldown needs a
  day-level sub-view per `instrument_type` leaf, download is strictly per-day (never multi-day) — fixed live in the
  mockup. 5 new/updated todos above. No production code touched — all findings verified read-only against real GCS
  manifests; only the mockup artifact and this doc were edited.
- **2026-07-07 (UI fix shipped)** — Shipped the DataStatusTab.tsx chains-vs-venues fix via quickmerge,
  `deployment-ui@8a3781b`, landed on `live-defi-rollout`. Re-verified clean (tsc, eslint, vitest 21/21) immediately
  before shipping since it had sat uncommitted since earlier in the session.
- **2026-07-07 (writer fix implemented)** — Per operator go-ahead, ran a 3-agent pre-audit then implemented the
  CeFi/TradFi manifest writer fix in `instruments-service/instruments_service/engine/orchestrator/writers.py`
  (`_derive_instrument_type` → `_split_by_instrument_type`, one `record_captured()` call per distinct `instrument_type`
  instead of one blended call per venue×date; `instrument_type` added to the `row_key` dict). Confirmed via pre-audit
  this is ONE shared code path for CeFi AND TradFi (CME hits the identical bug live), and flagged 5 more CeFi venues as
  likely-affected from registry evidence (not yet raw-parquet-confirmed). Deleted the dead/broken
  `fix_manifest_venue_casing.py` one-off script as a companion cleanup (its groupby omitted `instrument_type` and would
  have re-introduced the collapse if ever run). Updated `__init__.py` exports and the 3 unit tests that directly
  exercised the removed helper. Quality gates running; not yet committed. See "Update 2026-07-07 (writer fix
  implemented...)" above for full detail. 5 new/updated todos above.
- **2026-07-07 (later same day)** — Shipped the sibling UI fix (chains-vs-venues, Update §1) in code (uncommitted);
  pulled the real full DeFi `chain → venue → instrument_type → data_type` tree live and found the writer-side
  blank-instrument_type bug generalizes to all 7 Solana DeFi venues plus CURVE-OPTIMISM (Update §2); operator confirmed
  HYPERLIQUID/ASTER's dual CEFI+DEFI listing is intentional hybrid classification, not a bug — folded into the existing
  tracker Stage 5 CLOB-on-chain item instead of filing a new finding (Update §3). Four new todos added above; none
  contradict or replace the original D6 decision ask.
- **2026-07-07** — **Operator confirmed the proposed drilldown order (venue → instrument_type, no data_type leaf)
  matches this doc exactly** — verified via a 4-way check: (1) the raw CEFI `availability_index.parquet` confirms
  `data_type` is a near-constant `"instruments"` (86,804/86,839 rows, 99.96%; the other 35 are blank-string write
  artifacts on POLYMARKET-PERP/KALSHI-PERP/LIGHTER-ZKSYNC/DERIBIT-COMBO/BITFINEX-SPOT/PACIFICA-SOLANA, not a real second
  dimension — low-priority, likely incomplete re-capture writes); (2) this doc's own text was re-confirmed verbatim to
  state `venue -> instrument_type` as the FULL spec, not a stop en route to a `data_type` leaf; (3)
  `_build_instrument_type_breakdown` re-confirmed venue-agnostic with no allowlist/cap, so the D2a-adjacent writer fix
  will render N instrument_types with zero further code once landed; (4) surfaced the two new todos above (the
  missing_dates gap and the unrelated "Instrument breakdown" venue-detail feature) — both added as scoped follow-ups
  rather than blocking the core plan.
- **2026-07-07** — Filed from an operator design discussion following the ASTER/CEFI audit. Verified DERIBIT,
  DERIBIT-COMBO, and PREDICTION's `market_metadata` behavior against the live production API before writing this up —
  not asserted from code reading alone. No files edited.

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - re-verified after its 2026-07-30
  edit: still carries a `[CODE]` item "deliberately deferred pending explicit go-ahead" and a `[VERIFY]` item the doc
  marks genuinely contested + actively under concurrent investigation.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries — added `mtds.py`, the source target for the
  still-open `[CODE] P1` "move `market_metadata` off the MTDS daily axis" todo).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — all 8 open checkboxes are
  judgment-call/operator-gated design items (mockup re-verification cadence, parquet resharding design gated on operator
  sign-off, etc.), none a bounded worker-determinable fact-check.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — KNOWN UNDER-READ-RISK doc (a prior
  pass found only 6/14 items); this pass read all 618 lines end-to-end and grep-verified exactly 8 open items, matching
  the doc's own count — no gap this time. All 8 are judgment-call/operator-gated design items.
