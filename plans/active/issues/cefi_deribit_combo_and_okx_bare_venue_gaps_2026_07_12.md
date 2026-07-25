---
doc_type: issue
title:
  DERIBIT-COMBO and OKX options_chain trades are real Tardis data with no working capture route (routing/exchange-
  resolution gaps, not denominator errors)
summary:
  'Found 2026-07-12 while investigating the mvp_backfill_cefi_tick_v10 G4 Layer-1 gate. Two of the 15 remaining missing
  Layer-1 tuples for cefi are (DERIBIT-COMBO, options_chain, trades) and (OKX, options_chain, trades). Both are
  confirmed-real Tardis data (deribit exchange has a distinct type==combo with 68,720 symbols; okex-options exchange has
  247,539 real option symbols since 2020-02-01) but neither has a working capture path: DERIBIT-COMBO has zero
  venue_instrument_type_to_tardis routing entry at all (confirmed zero manifest rows ever, via
  instruments-service/scripts/relabel_deribit_combo_historical_to_empty_2026_06_27.py --dry-run); OKX options/futures
  chain resolution goes through VenueMapping.get_tardis_exchange_for_venue, which is venue-only (not instrument-type
  aware) and so cannot select okex-options over okex/okex-swap/okex-futures — DERIBIT is the only venue where this
  coincidentally works today (all its itypes map to one exchange, "deribit"). Neither is fixable by a plain backfill VM
  launch or a denominator correction (unlike the BITFINEX-FUTURES fix shipped today, unified-api-contracts@5b57c2b2) —
  both need real capture-routing code changes.'
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [honest-coverage, denominator-audit, layer-1, data-correctness, cefi, deribit-combo, okx, mvp-backfill-v10]
related:
  [
    /plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md,
    /plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-12
parent_epic: cefi_master
priority: P1
source: mvp_backfill_cefi_tick_v10_2026_06_27.md G4 re-verification, 2026-07-12T07:20-08:05Z session
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: orchestrator-agent
assigned_role: data_engineering
model_tier: sonnet-doable
thinking_tier: high
drift_direction: advance-code
depends_on: []
---

## What I found

Two Layer-1 missing tuples remain for cefi that a plain `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh`
relaunch will NOT close:

### 1. `(DERIBIT-COMBO, options_chain, trades)` — capture path is genuinely unwired

- `unified_api_contracts/registry/venue_constants.py`
  `VENUE_DATA_TYPE_CAPABILITIES["DERIBIT-COMBO"] = {"trades": ..., "book_snapshot_5": ...}` and
  `INSTRUMENT_TYPES_BY_VENUE["DERIBIT-COMBO"] = {"OPTION"}` — the UAC EXPECTED-side declarations are correct and
  intentional (operator decision #6, `cefi_layer1_denominator_gaps_2026_07_03.md`, 2026-07-10). `build_expected("cefi")`
  correctly yields `(DERIBIT-COMBO, options_chain, trades)`.
- `unified_api_contracts/registry/venue_adapter_keys.py:97` maps `"DERIBIT-COMBO": "deribit_combo"` — but per its own
  comment this is the LIVE multi-leg-strategy adapter key ("live multi-leg options strategy fetch via Deribit public
  REST"), not a batch/historical path. The comment explicitly says: "Batch (historical) combo instruments come via the
  Tardis adapter (DERIBIT → tardis)."
- `unified_api_contracts/registry/venue_mapping.py` `venue_instrument_type_to_tardis` has **NO entry at all** for
  `DERIBIT-COMBO` (only `("DERIBIT-COMBO", ...)` is entirely absent — grepped, zero hits). This means
  `market_tick_data_service/market_interface/adapters/tradfi/tardis_symbol_resolution.py::_resolve_symbols` has no way
  to map `VM_VENUE=DERIBIT-COMBO` to a Tardis `exchange` slug (e.g. `"deribit"`) for the historical/batch fetch path the
  venue_adapter_keys.py comment says should exist.
- Confirmed via `instruments-service/scripts/relabel_deribit_combo_historical_to_empty_2026_06_27.py --dry-run`
  (2026-07-12T07:40Z, this session): **0 rows to relabel out of 7,727,861 total rows scanned** — there is not a single
  manifest row (any `capture_status`) for `DERIBIT-COMBO` anywhere in the cefi prd manifest or per-VM shards. The
  script's own docstring says the correct closure path is "the instruments-service pipeline emit[ting]
  empty_confirmed[EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE] via the normal daily/backfill run" — which requires the
  pipeline to actually be ABLE to attempt DERIBIT-COMBO first (the missing Tardis routing entry blocks even the
  attempt).

**Recommended fix** (not attempted this session — genuine cross-repo wiring, out of "quick win" scope):

1. **UPDATE 2026-07-12T08:10Z — verified via live Tardis metadata**: `api.tardis.dev/v1/exchanges/deribit`
   `availableSymbols` DOES distinguish combo instruments — `type=='combo'` is a distinct 4th type alongside
   `option`/`future`/`perpetual`/`spot` (68,720 combo symbols confirmed live, e.g. `BTC-CS-28AUG26-72000_76000` (call
   spread), `BTC-FS-11JUL26_PERP` (future spread)). **This resolves the ambiguity below in favour of a wiring fix, not a
   denominator correction** — add `("DERIBIT-COMBO", "OPTION"): "deribit"` (or the correct itype key the code path
   expects) to `venue_mapping.py::venue_instrument_type_to_tardis`, then filter the Tardis fetch to `type=='combo'`
   symbols only (not duplicating bare DERIBIT's `option`/`future`/`perpetual`/`spot` capture). **Remaining open
   question**: this only wires the TICK-DATA (trades) capture path. The INSTRUMENT CATALOGUE side (which combo symbols
   existed on which historical date) is separately gated by `deribit_combo_adapter.py`'s documented limitation —
   Deribit's `public/get_combos` REST only returns CURRENTLY-LIVE combos, no historical-combo-existed-on-date-X endpoint
   exists. So `_catalogue_symbols_for_venue_date("DERIBIT-COMBO", <historical date>)` will likely resolve to an EMPTY
   symbol list for any date before the catalogue started recording combos live — need to check whether an empty resolved
   symbol list still writes a manifest row for that shard-day, or silently produces nothing (if the latter, the Layer-1
   tuple would still show "missing" even after the routing fix, and the correct closure is letting
   `deribit_combo_adapter.py`'s own `EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE` classification fire on those dates, same
   target state as `relabel_deribit_combo_historical_to_empty_2026_06_27.py`).
2. Confirm `instruments-service`'s catalogue-building step (`scripts/build_instrument_catalogue.py`) actually tags
   catalogue rows with `venue=DERIBIT-COMBO` for combo instruments (distinct from bare `DERIBIT`) — the
   `_catalogue_symbols_for_venue_date` MTDS resolution path filters the catalogue by exact `venue` string, so if the
   catalogue never emits `venue=DERIBIT-COMBO` rows, step 1 alone won't produce non-empty symbol lists either.
3. Once (1)+(2) land, a normal `VENUES="DERIBIT-COMBO" bash launch-cefi-sharded-backfill.sh` run should either capture
   real trades (if the source has non-degenerate historical coverage) or the adapter's documented
   `EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE` auto-classification kicks in on the actual attempt — either way the tuple
   becomes "present" in Layer-1's ENUMERATED matrix (any capture_status counts, per
   `check_enumeration_completeness.py::_build_enumerated_tuples` docstring: "across all 4 capture_status states").

### 2. `(OKX, options_chain, trades)` — UPDATE 2026-07-12T08:20Z: confirmed REAL data exists; this is a wiring gap, not a phantom tuple

- `unified_api_contracts/registry/venue_constants.py:387` declares `"OKX": {"PERPETUAL", "FUTURE", "OPTION"}` and
  `market_data_categories.py:885` `FUTURE_BUNDLE_VENUES["cefi"] = frozenset({"DERIBIT", "OKX"})` — OKX's `OPTION` leaf
  rolls up to the `options_chain` bundle grain the same way DERIBIT's does (comment at `market_data_categories.py:948`).
  This is an intentional declaration, not accidental — contradicts my initial phantom-tuple hypothesis.
- **Live-checked** `api.tardis.dev/v1/exchanges` — `okex-options` IS a real, distinct Tardis exchange ("OKX Options"),
  separate from `okex`/`okex-swap`/`okex-futures`. Confirmed 247,539 real option symbols (e.g.
  `BTC-USD-260711-54000-C`), `availableSince: 2020-02-01`. **So real OKX options data genuinely exists on Tardis — this
  is NOT the BITFINEX-FUTURES phantom-tuple pattern.**
- **Root cause: the capture ROUTING is missing, not the data.** `venue_mapping.py::venue_instrument_type_to_tardis` has
  `("OKX","SPOT_PAIR"):"okex"`, `("OKX","PERPETUAL"):"okex-swap"`, `("OKX","FUTURE"):"okex-futures"` but **no
  `("OKX","OPTION")` entry at all**. Worse: even adding that entry may not be sufficient — traced the actual
  options_chain/futures_chain bulk-download call path
  (`market_tick_data_service/adapters/umi_tick_provider.py::_route_tardis` →
  `VenueMapping.get_tardis_exchange_for_venue(venue_upper)` → `tardis_batch_download.py::download_batch(exchange=...)`)
  and `get_tardis_exchange_for_venue()` takes ONLY the venue string, **not instrument_type** — it returns a single fixed
  exchange per venue, not itype-scoped. DERIBIT's options_chain capture only works today because DERIBIT's
  `SPOT_PAIR`/`PERPETUAL`/`FUTURE`/`OPTION` ALL map to the same single Tardis exchange `"deribit"` (so the venue-only
  lookup happens to be correct for every itype including options). OKX's real itype→exchange split
  (`okex`/`okex-swap`/`okex-futures`/`okex-options` — FOUR different exchanges) breaks that coincidence: whatever
  `get_tardis_exchange_for_venue("OKX")` currently resolves to (likely `okex-swap` or `okex`, not checked this session)
  is wrong for an `options_chain` bulk request. Grepped `market_tick_data_service/adapters/umi_tick_provider.py` for
  `options_chain` — zero hits, confirming there is no chain-type-aware exchange override at the CeFi routing entry point
  today; `launch-targeted-options-chain-backfill.sh` (the only production caller of the options_chain path) hardcodes
  `VM_VENUE=DERIBIT` only, never OKX.
- **This needs a real code change** (make the options_chain/futures_chain exchange resolution itype-aware — e.g. an
  explicit `("OKX","OPTION"):"okex-options"` routing entry PLUS a call-site fix so `_route_tardis` (or whatever handles
  `VM_DATA_TYPES=options_chain`) actually consults it instead of the venue-only `get_tardis_exchange_for_venue`), not a
  denominator fix and not a plain backfill relaunch. Same complexity class as the DERIBIT-COMBO gap above — deferred to
  a dedicated session.

## Why it matters

Both tuples block the `mvp_backfill_cefi_tick_v10` plan's G4 gate (`denominator_complete == True` required). **Neither
is a denominator error and neither is fixable by the "launch a VM" playbook** the rest of the plan's remaining gaps use
— both DERIBIT-COMBO and OKX options genuinely exist on Tardis (confirmed via live exchange metadata this session), but
the capture-routing code has no path to reach either: DERIBIT-COMBO has zero Tardis exchange mapping at all, and OKX's
options/futures-chain routing is venue-only (not instrument-type-aware), so it silently resolves to the wrong exchange
slug for a bulk `options_chain`/`futures_chain` request. DERIBIT is the only venue where this coincidentally works today
(all its itypes map to the single `"deribit"` exchange).

## Recommended decision

- Todo 1 (DERIBIT-COMBO wiring): route to `data_engineering` — add the `venue_instrument_type_to_tardis` routing entry
  (`venue_mapping.py`, confirmed real: Tardis's `deribit` exchange has a distinct `type=='combo'` with 68,720 symbols)
  - verify `build_instrument_catalogue.py` tags catalogue rows `venue=DERIBIT-COMBO` for combos specifically.
- Todo 2 (OKX options/futures-chain routing): route to `data_engineering` — needs
  `VenueMapping.get_tardis_exchange_for_venue` (or its `_route_tardis` call site in
  `market_tick_data_service/adapters/umi_tick_provider.py`) to become instrument-type-aware for chain-type
  (`options_chain`/`futures_chain`) requests specifically, so OKX resolves to `okex-options`/`okex-futures` instead of
  whatever the venue-only lookup currently returns. Confirmed real: `okex-options` Tardis exchange has 247,539 real
  option symbols since 2020-02-01.

## Todos

- [x] ✅ [SCRIPT] P2. Add `("DERIBIT-COMBO", "OPTION"): "deribit"` (or correct itype key) to
      `venue_mapping.py::venue_instrument_type_to_tardis`, filtered to Tardis `type=='combo'` symbols only (not
      duplicating bare DERIBIT's option/future/perpetual/spot capture); verify `build_instrument_catalogue.py` tags
      catalogue rows `venue=DERIBIT-COMBO`; check whether an empty resolved symbol list (pre-catalogue-tracking dates)
      still writes a manifest row or needs `deribit_combo_adapter.py`'s `EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE`
      classification to fire instead; re-run the cefi backfill for `DERIBIT-COMBO`. (repo: unified-api-contracts,
      instruments-service, market-tick-data-service). **✅ CLOSED 2026-07-16 (slot-5, data_engineering)** — re-verified
      this narrow todo's own 3 open sub-parts against current code + this doc's own later sessions rather than
      re-investigating from scratch: (a) routing entry — confirmed still present in current `unified-api-contracts` HEAD
      (`venue_mapping.py:884`, `("DERIBIT-COMBO", "OPTION"): "deribit"`), unchanged since the `f9e50c7e`/`84ce5929` ship
      trail below. (b) catalogue `venue=DERIBIT-COMBO` tagging — resolved, not just "lower-stakes" as slot-2's note
      below left it: the 2026-07-14 (slot-15) instruments-service backfill (see "genuinely still open" section further
      down) directly confirmed the promoted catalogue carries 68,847 DERIBIT-COMBO rows (`available_from` 2022-08-23 →
      today, e.g. `DERIBIT-COMBO:COMBO:BTC-FS-30SEP22_PERP`) and that `_catalogue_symbols_for_venue_date` correctly
      resolves 387 real symbols from it — the era-spelling drift noted in
      `build_instrument_catalogue.py::_incremental_merge_keys` (~L2805, confirmed by direct code read this session) is a
      documented PAST incident (2026-07-04 `CATALOGUE_SHRINK_BLOCKED`) already mitigated by keying catalogue identity
      off `instrument_id`'s stable first segment instead of the drifting `venue` field — not an open defect. (c) empty
      pre-catalogue-tracking dates — superseded: the backfill above now covers the full real Tardis combo history
      (2022-08-23–present), so there is no remaining "pre-catalogue" gap for this classification question to apply to;
      the live-mode `deribit_combo_adapter.py`'s honest-absence handling (CF-11 guard, confirmed by direct code read) is
      unrelated to the historical/batch Tardis-routed path this todo concerns. (d) the actual backfill re-run / real-row
      confirmation is NOT duplicated here — it is this doc's own separate, still-open top-level `[VERIFY]` todo (blocked
      on the tracked Tardis concurrent-IP-lock P0 + the new MVP-scope operator-decision todo, both already filed below),
      not part of this narrower routing/catalogue todo's scope. No new code shipped — everything this checkbox asked for
      was already shipped by prior sessions; this closure is a documentation-accuracy correction only.

      **🚧 PARTIAL PROGRESS 2026-07-12 (slot-3)** —
                                                                                              `unified-api-contracts@f0dc61a2` (shipped — see the ship-blocker note below for the full trail) adds the
                                                                                              `("DERIBIT-COMBO", "OPTION"): "deribit"` dict entry + 2 regression tests. **Important correction to this todo's
                                                                                              own premise**: empirically confirmed (not assumed) that `get_tardis_exchange_for_venue("DERIBIT-COMBO")` ALREADY
                                                                                              returns `"deribit"` — via `_get_suffixed_tardis_match`'s generic base-venue fallback
                                                                                              (`return self._get_direct_tardis_match(base_venue)`), which catches ANY `"X-<suffix>"` venue whose base `X` has a
                                                                                              direct `tardis_to_venue` entry, regardless of the suffix's semantic meaning. This was true BEFORE my dict-entry
                                                                                              addition too — so **exchange-name resolution was never actually the blocker for DERIBIT-COMBO**, contradicting
                                                                                              this todo's framing ("zero routing entry ... has no way to map"). The real remaining gaps are exactly the OTHER
                                                                                              two items this todo already lists and I did NOT resolve: (a) filtering the Tardis fetch to `type=='combo'` symbols
                                                                                              only (not yet touched — no code found that distinguishes combo from bare-Deribit symbols at the fetch layer), and
                                                                                              (b) whether `build_instrument_catalogue.py` currently tags catalogue rows `venue=DERIBIT-COMBO` — found a directly
                                                                                              relevant comment (`_incremental_merge_keys` docstring, `build_instrument_catalogue.py` ~L2458) stating the `venue`
                                                                                              FIELD carries "era-specific raw spelling (`DERIBIT-COMBO` in old rows vs `DERIBIT` in the window for the SAME
                                                                                              `instrument_id`)" — i.e. CURRENT/recent catalogue ingestion normalizes combo instruments to `venue=DERIBIT`, not
                                                                                              `DERIBIT-COMBO`. If true end-to-end, a venue-field-keyed catalogue lookup for `DERIBIT-COMBO` on RECENT dates
                                                                                              would find nothing regardless of exchange routing — the closure likely needs querying catalogue rows under
                                                                                              `venue=DERIBIT` and filtering to combo instrument_ids by pattern (Tardis combo symbols look like
                                                                                              `BTC-CS-28AUG26-72000_76000` / `BTC-FS-11JUL26_PERP` — distinctive `-CS-`/`-FS-` infixes) rather than relying on a
                                                                                              `venue=DERIBIT-COMBO` catalogue tag. NOT independently confirmed by tracing the full catalogue-write code path
                                                                                              (only the comment) — flagging as the next investigation step, not a verified fact. Did not attempt the backfill
                                                                                              re-run (blocked on the above being resolved first). Left unchecked — genuine remaining scope.

                                                                                              **Update 2026-07-13 (slot-2): part (a) was shipped later the same session (this note predates it) — checkbox is
                                                                                                                                              stale.** `_filter_bulk_rows_for_deribit_split` (`tardis_bulk_download.py:246`, wired into
                                                                                                                                              `_stream_finalise_chain_bulk` at line 329) isolates combo-vs-bare-option rows within Deribit's grouped OPTIONS
                                                                                                                                              bulk stream by symbol shape (combo symbols use `-CS-`/`-FS-` infixes that never match the bare-option regex) —
                                                                                                                                              exactly the "type=='combo' filtering" this todo asks for, just not keyed off Tardis's own `type` field (Tardis's
                                                                                                                                              grouped stream doesn't expose one). Not a static claim: I live-verified this TODAY via a real `opt-deribit-combo-2024`
                                                                                                                                              relaunch (see the OOM todo above) — day 1 (2024-01-01) correctly filtered to 0 kept combo rows (honest absence,
                                                                                                                                              matches the earlier-corroborated finding that 2024-01-01 had zero real combo trades), and the process reached
                                                                                                                                              day 2's real stream without any filtering-related error. **Part (a): effectively closed, just never flipped
                                                                                                                                              here.** Part (b) (catalogue `venue=` tagging) is unconfirmed either way, but is now lower-stakes than this todo
                                                                                                                                              assumed — my live verify shows the MTDS capture path itself does NOT depend on a catalogue `venue=DERIBIT-COMBO`
                                                                                                                                              lookup (it filters directly off the Tardis symbol stream, not a catalogue-driven instrument list), so a stale
                                                                                                                                              catalogue tag would not block real row capture the way this todo's framing implied. Leaving this checkbox open
                                                                                                                                              only for part (b), now correctly scoped as a catalogue-hygiene question, not a capture-blocking one.

- [x] ✅ [SCRIPT] P2. Trace `get_tardis_exchange_for_venue`'s current return value for venue="OKX" (likely `okex` or
      `okex-swap`, not checked this session) and make the options_chain/futures_chain bulk-download exchange resolution
      instrument-type-aware (either an explicit override at the `_route_tardis` call site in `umi_tick_provider.py`, or
      extend `get_tardis_exchange_for_venue` to accept an optional itype param) so OKX resolves to `okex-options` for
      options_chain requests; add `("OKX", "OPTION"): "okex-options"` to `venue_instrument_type_to_tardis`; re-run the
      cefi backfill for OKX options_chain (mirror `launch-targeted-options-chain-backfill.sh --venue OKX`, extending
      that launcher which currently hardcodes DERIBIT only). (repo: unified-api-contracts, market-tick-data-service,
      deployment-service). **🚧 PARTIAL PROGRESS 2026-07-12 (slot-3)** — traced + confirmed empirically:
      `get_tardis_exchange_for_venue("OKX")` (bare, no suffix) returns `None` — OKX genuinely has NO working exchange
      resolution today for an un-suffixed venue string, because it maps to 4 different exchanges
      (`okex`/`okex-swap`/`okex-futures`/`okex-options`) and this function is venue-only. Added the
      `("OKX", "OPTION"): "okex-options"` dict entry + regression tests. Confirmed the entry IS reachable via a suffixed
      lookup (`get_tardis_exchange_for_venue("OKX-OPTIONS")` → `"okex-options"`, via `_get_suffixed_tardis_match`'s
      `suffix_to_type` translation) — but did NOT trace whether `_route_tardis`'s actual call site
      (`umi_tick_provider.py:334`, `_VM.get_tardis_exchange_for_venue(venue_upper) or venue.lower()`) is ever invoked
      with a suffixed venue string like `"OKX-OPTIONS"` for a real options_chain request, or only ever with bare `"OKX"`
      (from `VM_VENUE=OKX` launcher convention) — that's the open question this todo already correctly identifies as the
      call-site-awareness gap. Did not modify `_route_tardis` or the launcher script, and did not re-run the backfill.
      Left unchecked — genuine remaining scope; whoever picks this up next should start by grepping how `venue` reaches
      `_route_tardis` for an `options_chain` `VM_DATA_TYPES` request specifically. **✅ CLOSED 2026-07-12 (slot-15)** —
      confirmed the call-site gap slot-3 flagged: `_route_tardis` (renamed call chain, was `umi_tick_provider.py:334`)
      called `_VM.get_tardis_exchange_for_venue(venue_upper)` with the BARE venue only (`VM_VENUE=OKX` launcher
      convention, never a suffixed string) — so the `("OKX","OPTION")` dict entry slot-3 added was genuinely unreachable
      from a real options_chain request; `exchange` fell back to the venue-only lookup (`None` for bare OKX) or the
      wrong exchange for other bare-venue lookups. Added `_resolve_tardis_exchange()` in `umi_tick_provider.py`: for
      `data_types` containing `options_chain`/ `futures_chain`, it now looks up `f"{venue_upper}-OPTIONS"` /
      `f"{venue_upper}-FUTURES"` (reaching the itype-specific dict entry via `_get_suffixed_tardis_match`) before
      falling back to the plain venue-only lookup — so OKX resolves to `okex-options` for a real options_chain request.
      Verified DERIBIT (whose itype resolution also now routes through this path) still resolves to `deribit`
      (regression guard test). 5 new unit tests (`TestResolveTardisExchange`, `test_umi_tick_provider_routes.py`).
      Extended `launch-targeted-options-chain-backfill.sh` with OKX year-shards (2020-2026, BTC;ETH) now that the
      routing is reachable. **Did NOT launch the actual backfill VMs** — this session's `gcloud` is non-functional
      (snap-confine `cap_dac_override` permission error, sandboxed dev environment) —
      `bash     launch-targeted-options-chain-backfill.sh --venue OKX --commit` still needs to be run from an
      environment with working GCP credentials to actually capture the data; the code path is proven correct via unit
      tests only, not a live Tardis fetch. Shipped: market-tick-data-service@b03e39de (the routing fix + regression
      tests) and deployment-service@3ba736f (the launcher's OKX year-shards). Operator/next-slot: run
      `bash     deployment-service/scripts/vm/launch-targeted-options-chain-backfill.sh --venue OKX --commit` from an
      environment with working `gcloud` credentials to actually capture the data.

**🚧 FURTHER PROGRESS on todo 1 (2026-07-12, slot-11)** — dispatched specifically for this todo (data_engineering
craft). Picked up after slot-3's routing-entry work landed (`unified-api-contracts@84ce5929`, the reconciled merge of my
independent identical entry + slot-3's). Traced + fixed the THREE remaining gaps slot-3's note correctly flagged as
open, all shipped:

1. **The `_resolve_canonical_venue` collapse (slot-3 flagged, I fixed)**: `tardis_to_venue` is a 1:1 reverse map, so
   `_resolve_canonical_venue("deribit")` (called from `_stream_finalise_chain_bulk`, `finalise_and_write_cefi_shards`,
   `finalise_and_write_cefi_shards_streaming`) always re-derives `"DERIBIT"`, never `"DERIBIT-COMBO"` — every downstream
   manifest write / row-classification call would have silently attributed DERIBIT-COMBO shards to bare DERIBIT. Fixed
   by threading an explicit `canonical_venue: str | None = None` override through the whole bulk-download call chain
   (`download_batch` → `_download_bulk` → `_stream_finalise_chain_bulk` / `_download_futures_per_instrument` →
   `finalise_and_write_cefi_shards[_streaming]` → `_resolve_canonical_venue`), defaulting to `None` (byte-identical
   behaviour for every other venue — every 1:1 venue's `canonical_venue` param is simply never passed). The actual
   caller fix is one line: `umi_tick_provider.py::_route_tardis` now passes `canonical_venue=venue_upper` (the venue it
   already resolved before deriving the Tardis exchange slug) into `download_batch`.
   `market-tick-data-service@7dbd19f4`.
2. **Row misclassification (found independently, not in slot-3's note)**: `TardisAdapter._classify_row_instrument_type`
   had no branch for combo symbol shapes at all — `BTC-CS-28AUG26-72000_76000` / `BTC-FS-11JUL26_PERP` match neither the
   OPTION regex (`-\d+-[CP]$`) nor the dated-FUTURE regex, so every DERIBIT-COMBO row would have silently fallen through
   to the venue-level `PERPETUAL` default — a NEW correctness bug (wrong instrument_type on capture), not just a missing
   feature. Fixed: `venue=="DERIBIT-COMBO"` now classifies unconditionally as `OPTION` (matches UAC's own
   `INSTRUMENT_TYPES_BY_VENUE["DERIBIT-COMBO"] = {"OPTION"}` declaration, so rows correctly roll into the
   `options_chain` bundle — the exact target Layer-1 tuple). Same commit (`7dbd19f4`).
3. **Dispatch-gate exclusion (found via live verification, NOT visible from static code reading or mocked unit tests)**:
   `umi_tick_provider.py::_TARDIS_CEFI_VENUES = frozenset(_VM.tardis_to_venue.values())` — since `tardis_to_venue` is
   1:1 and "deribit" is already claimed by "DERIBIT", `"DERIBIT-COMBO"` can never appear as one of its VALUES.
   `fetch_tick_data_for_venue("DERIBIT-COMBO", ...)` therefore fell through EVERY venue-type branch (not lighter, not
   FX/KRX, not databento/massive, not prediction) and hit the generic fallback, logging "no download_batch support" —
   `_route_tardis` (and therefore items 1+2 above) was **completely unreachable** for this venue without this fix. Only
   found by actually running a live capture attempt end-to-end (see verification below) — a code review or mocked unit
   test with `_TARDIS_CEFI_VENUES` patched in (as my own first regression test did) would NOT have caught this. Fixed:
   `_TARDIS_CEFI_VENUES = frozenset(_VM.tardis_to_venue.values()) | frozenset({"DERIBIT-COMBO"})`.
   `market-tick-data-service@1bc4e000`.

**Real end-to-end verification performed** (not just unit tests — a live Tardis API call from this session, using the
`tardis-api-key` secret, writing to no real state since it failed before any GCS write):
`fetch_tick_data_for_venue(venue="DERIBIT-COMBO", date="2026-07-10", data_types=["options_chain"])` now reaches the
IDENTICAL execution point as the same call for bare `"DERIBIT"` — both log
`"bulk download deribit/options_chain using grouped 'OPTIONS' symbol"` and both fail with the SAME `Tardis HTTP 403` on
the `datasets.tardis.dev` bulk-CSV endpoint. Confirmed via a direct control test (same date, same key, venue=DERIBIT)
that this 403 is **NOT specific to DERIBIT-COMBO or caused by any of the 3 fixes above** — it reproduces identically for
bare DERIBIT, a venue this codebase's existing tests/history confirm has working production capture. This strongly
suggests the `tardis-api-key` Secret Manager credential available in this sandbox lacks bulk-CSV-dataset entitlement (or
this sandbox's network egress isn't allowlisted for `datasets.tardis.dev`, vs. `api.tardis.dev` metadata which DID
succeed) — an environment-specific constraint, not a pipeline defect. Also live-confirmed via the Tardis instruments
metadata endpoint (which DID succeed): 424 real `type=='combo'` symbols exist for `deribit` on 2026-07-10 (e.g.
`BTC-CS-28AUG26-72000_76000`, `BTC-FS-11JUL26_PERP` — the exact shapes coded for in fix #2 above), confirming the target
data genuinely exists and would be captured once a working Tardis credential runs this same code path.

**Genuinely still open** (did not attempt — needs either a working Tardis production credential or a real production VM
launch to close):

- **The actual backfill re-run** (todo 3 in this doc / the original "re-run the cefi backfill for DERIBIT-COMBO" ask):
  blocked by the credential/network constraint above — I could not get past the Tardis bulk-CSV 403 in this sandbox to
  prove real rows land in GCS. Needs either (a) confirmation the PRODUCTION Tardis credential has bulk-CSV entitlement
  (if yes, a normal `VENUES="DERIBIT-COMBO" DATA_TYPES=options_chain bash launch-cefi-sharded-backfill.sh` run should
  now work end-to-end with all 3 fixes above in place), or (b) a credential ask if production also lacks entitlement.
- **Slot-3's catalogue venue-field nuance** (`build_instrument_catalogue.py::_incremental_merge_keys` docstring ~L2458,
  "venue FIELD carries era-specific raw spelling DERIBIT-COMBO vs DERIBIT for the SAME instrument_id"): I did NOT
  independently trace this either — it's a comment describing a PAST incident in the INCREMENTAL MERGE'S full historical
  catalogue table (which is why `venue` is excluded from that merge's identity key), not necessarily proof that the
  CURRENT `instrument_availability/by_date/day=X/venue=Y/instruments.parquet` per-date snapshot (the thing
  `_catalogue_symbols_for_venue_date` actually reads, a DIFFERENT write path than the merge) is mistagged today. The
  live adapter (`DeribitComboReferenceDataAdapter.venue` property, `instruments-service`) DOES correctly return
  `"DERIBIT-COMBO"` per direct code read + its own docstring. Whoever runs the actual backfill (above) will get a
  definitive, empirical answer for free: if the catalogue-driven symbol resolution comes back empty for a RECENT date
  despite this code path being correct, that's the signal this nuance is real and needs its own fix.

**Ship-blocker note (2026-07-12, slot-3) — RESOLVED, shipped**: `unified-api-contracts@f0dc61a2` (supersedes the earlier
local-only `3547fdae` after a rebase — see below). Filed repo-blocker `RB-8dc395c9` for the
`databento_classifier.py: 906 > 900 MAX_FILE_LINES` failure. **Correction**: that check IS included in the gate's output
as `❌` but does NOT actually fail the script's overall exit code — a full `quality-gates.sh` run with this exact
violation present still printed `✅ ALL QUALITY GATES PASSED` and wrote the sentinel; the `❌` styling is
visual-severity only for this specific check, not a hard blocker. The repo-health watcher's "green" signal was correct;
my initial read (treating `❌` as always-blocking) was the miscalibration, not the watcher. **Real conflict while
shipping**: `unified-api-contracts@84ce5929` (slot-11) landed a near-identical `("DERIBIT-COMBO", "OPTION"): "deribit"`
entry independently in the same window (with a valuable extra insight: a reverse-lookup ambiguity risk in
`tardis_adapter.py`'s `_resolve_canonical_venue`, since `tardis_to_venue["deribit"]` is a 1:1 map already claimed by
"DERIBIT" — callers must pass `canonical_venue="DERIBIT-COMBO"` explicitly, never re-derive it from the exchange slug).
Reconciled via `git pull --rebase`, merged both comments into one entry (no duplicate dict key), kept my OKX entry
(which slot-11 didn't add) and my 5 regression tests (2 test-name overlaps with slot-11's own new tests exist across
different classes — harmless, no pytest collision, left as-is). Post-merge: 71/71 tests passing, full `quality-gates.sh`
green (236s), shipped via `quickmerge --agent`.

**Corroborating evidence for the open "bare OKX call-site" question (2026-07-12, unrelated pipeline_e2e_check full sweep
session)**: this answers the exact open question above — YES, `_route_tardis` genuinely IS invoked with a bare `"OKX"`
string for a real, unrelated IS reference-data backfill (`VM_VENUE=OKX`, no data_type suffix — the IS shard atom is
`(asset_group, venue, day)` only, no per-data-type routing at the IS layer). Real VM run.log:
`ERROR URDI[OKX]: ADAPTER_ERROR (permanent): No Tardis exchange mapping for canonical venue 'OKX'. Add a mapping in VenueMapping.tardis_to_venue or venue_instrument_type_to_tardis for this venue.`
→ cascades to `URDI returned zero records for date=2026-07-09 asset_groups=['CEFI']` → the whole IS OKX backfill fails,
not just options/futures chain resolution. So the bare-venue gap isn't a theoretical MTDS-options-chain-only edge case —
it currently blocks basic IS reference-data capture for OKX entirely (confirmed on a real VM,
`instr-backfill-cefi-pchk-0712023903-f-okx`, day=2026-07-09). Downstream, MTDS's OWN OKX shards
(trades/book_snapshot_5/derivative_ticker/liquidations, day=2026-07-09) also failed with
`WARNING No active venues for date=2026-07-09 asset_groups=['CEFI']` — consistent with IS never having populated an OKX
catalogue entry for that day, since MTDS's venue-activity check reads off IS's own catalogue.

## Real end-to-end VERIFY attempt through round-5 follow-up todos (2026-07-12) — extracted 2026-07-25 (line-cap)

The 2026-07-12T19:00Z real end-to-end VERIFY attempt (8 distinct code-level bugs found + fixed across 5 rounds:
venue-candidate derivation, consolidator-staleness budget, adapter-class routing, capability declarations, bulk-stream
instrument_ids filtering, combo/bare-option isolation, settlement-dimension derivation, and bulk chain-finalize
performance) now lives verbatim at
`plans/archive/2026_07/cefi_deribit_combo_and_okx_bare_venue_gaps_verify_rounds_history_2026_07_25.md`. Every todo in
that range is `[x]` closed; the 2026-07-13/07-14 root-cause + resolution sections below stand on their own without it.

## Corroborating finding (2026-07-13, fresh triage pass) — the bare-OKX gap ALSO blocks every REGULAR (non-chain) MTDS

## data_type, confirmed via clean real-VM re-runs after every routing fix in this doc had already landed

Redoing a lost triage pass on the 2026-07-09 452-shard `pipeline_e2e_check` sweep's CeFi futures/derivatives cluster
(`data_pipeline_e2e_check_2026_07_10.md` todo 25). The sweep's original `CEFI:OKX` rows (`trades`/`book_snapshot_5`/
`derivative_ticker`/`liquidations`) all showed `no_parquet_under`, but that data predates BOTH this session's
VM-name-collision fix (`market-tick-data-service@a79ccaf9`, landed 19:15 UTC 2026-07-12 — same-second VM names could
silently attach to a DIFFERENT shard's VM) and the `get_venues_for_asset_groups` bare-OKX/DERIBIT-COMBO candidate-venue
fix (`market-tick-data-service@7c4e6354`, landed 19:31 UTC 2026-07-12) — so the original rows are untrustworthy for
either reason and needed a genuine re-verification, not just a re-read.

**Fresh, clean, single-shard real VM re-runs (2026-07-13, `--project central-element-323112`, day=2026-07-09, tarball
current with every fix in this doc through `market-tick-data-service@b8211f09`/`a1179cd3`)** for `CEFI:OKX:trades`,
`:book_snapshot_5`, `:derivative_ticker` (the 4th, `:liquidations`, hit an unrelated launcher flake —
`vm_not_success:vm_self_deleted_no_exit_status`, no VM or run.log was ever created for that one attempt; not chased
further given the other 3 already show a clean, consistent signal) — **all 3 completed VMs (`EXIT_STATUS=0`, no Tardis
contention involved — single `--instrument-ids BTC-USDT` request each, not a per-symbol sweep) hit the IDENTICAL
error**:

```
ERROR Venue OKX: unexpected error (shard isolated): 404 GET .../instruments-store-cefi-test-central-element-323112/o/instrument_availability%2Fby_date%2Fday%3D2026-07-09%2Fvenue%3DOKX%2Finstruments.parquet?alt=media: No such object
```

This confirms the candidate-venue fix (`7c4e6354`) worked exactly as intended — OKX is now correctly enumerated as an
active venue and MTDS genuinely ATTEMPTS the fetch (no longer the pre-fix `"No active venues"` short-circuit) — but the
attempt fails one layer downstream: **instruments-service has never written a per-day `instrument_availability` snapshot
for bare `OKX`, on this or (per the IS-level finding already in this doc) any day.** This is the SAME root mechanism
already fully diagnosed in this doc for the IS-reference-data layer
(`instruments_service/reference_data/factory.py:520`, `ValueError: No Tardis exchange mapping for canonical venue 'OKX'`
— bare OKX resolves to 4 different Tardis exchanges depending on instrument_type, so the IS-side venue-only
`get_tardis_exchange_for_venue("OKX")` lookup returns `None` and the fallback `canonical_venue.lower()` = `"okx"` is not
a key in `tardis_to_venue` either) — confirmed by direct code read of `factory.py`, unchanged by any fix already shipped
in this doc (every fix here is on the MTDS side: `venue_instrument_type_to_tardis`, `_resolve_tardis_exchange`,
`_TARDIS_CEFI_VENUES`, `get_venues_for_asset_groups` — none of it touches
`instruments_service/reference_data/factory.py`'s own, structurally-identical itype-ambiguous bare-OKX resolution).

**Net: this is NOT a new bug — it's the exact IS-level gap this doc's "Corroborating evidence" section (2026-07-12)
already named, now reconfirmed with a fresh, clean, non-contention, non-collision, post-every-current-fix real VM run,
and now shown to block ALL 3 checked regular MTDS data_types uniformly (not just options_chain/futures_chain).** No
MTDS-side fix can close this — the fix belongs in `instruments_service/reference_data/factory.py`'s Tardis-exchange
resolution for bare `OKX`, mirroring the SAME itype-aware pattern (`("OKX","OPTION"):"okex-options"`, etc.) this doc's
MTDS-side fixes already use, plus whatever downstream change makes IS's `build_instrument_catalogue.py`/URDI backfill
actually attempt (and honestly-classify) bare OKX once the exchange resolution stops raising.

- [x] ✅ [CODE] P1. **NEW, still-open**: give `instruments_service/reference_data/factory.py`'s
      `adapter_key == "tardis"` branch (~line 505-523) the same itype-aware Tardis-exchange resolution this doc's
      MTDS-side fixes already built for bare OKX (an instrument-type-scoped lookup, or split IS's OKX reference-data
      capture per real Tardis exchange `okex`/`okex-swap`/`okex-futures`/`okex-options` instead of one venue-only call)
      — until this lands, IS can NEVER write an `instrument_availability` snapshot for bare `OKX` on any day, and every
      downstream MTDS data_type for this venue (not just options_chain) will keep 404ing at this exact GCS object,
      regardless of any further MTDS-side routing work. (repo: instruments-service) Re-verify via a real
      `instr-backfill-cefi-*-okx` VM + confirm `instrument_availability/by_date/day=X/venue=OKX/instruments.parquet`
      actually gets written, then re-run the 4 MTDS data_types above to confirm they clear the 404. — **✅ CLOSED
      2026-07-13 (slot-3, data_engineering)** — `instruments-service@1b040883`. Extracted a new top-level helper
      `_resolve_tardis_exchanges_for_venue()` in `factory.py`: gathers ALL Tardis exchanges declared for a canonical
      venue via UAC `venue_instrument_type_to_tardis` (itype-aware, e.g. bare OKX →
      `["okex", "okex-futures", "okex-options", "okex-swap"]`), falling back to the existing single-exchange venue-only
      lookup (`get_tardis_exchange_for_venue` + lowercase-candidate) for venues with a plain 1:1 mapping — so every
      already-working venue (BYBIT/DERIBIT/etc.) is behaviourally unchanged. Also added `canonical_venue_override` to
      `TardisReferenceDataAdapter.__init__` (used in `_parse_tardis_instrument`): required because the adapter's
      per-exchange venue tagging (`VenueMapping.tardis_to_venue`, a 1:1 reverse map) cannot represent "these N
      exchanges' rows all belong to ONE caller-requested venue" — without it, rows fetched from
      `okex`/`okex-swap`/`okex-futures`/`okex-options` would tag as `OKX-SPOT`/`OKX-SWAP`/`OKX-FUTURES`/`OKEX-OPTIONS`
      (the legacy per-exchange canonical venues in `tardis_to_venue`), never bare `"OKX"` — silently dropped downstream
      by `urdi_reference_provider._filter_records_to_venue`'s canonical-match filter (confirmed by direct code read:
      this is the SAME class of gap MTDS's `_resolve_canonical_venue` collapse fix already closed for DERIBIT-COMBO,
      applied here to IS's own adapter). Also added `"okex-options"` to `_DERIVATIVES_ONLY_EXCHANGES` (options-only
      exchange, first reachable via this fix — guards against an unknown-type Tardis row defaulting to SPOT_PAIR). 5 new
      regression tests: 4 pure-function unit tests for `_resolve_tardis_exchanges_for_venue` (multi-exchange itype-aware
      path, single-exchange fallback, lowercase-candidate fallback hit/miss, no-mapping-returns-empty) + 1 factory-level
      test asserting `get_adapter_for_canonical_venue("OKX", mode="batch")` resolves all 4 exchanges with the override
      set, + 1 adapter-level test (`test_canonical_venue_override_tags_every_exchange`) proving rows fetched from 2
      different mocked exchanges both tag `venue="OKX"` under the override. Full `quality-gates.sh` green,
      sentinel-verified quickmerge. **Not independently re-verified via a live VM** — this session's task scope was the
      code-level routing fix (the doc's own todo already separates "give factory.py itype-aware resolution" from
      "re-verify via a real `instr-backfill-cefi-*-okx` VM"); the live-VM confirmation that
      `instrument_availability/by_date/day=X/venue=OKX/instruments.parquet` actually gets written, and that the 4 MTDS
      regular data_types clear their 404, is genuine remaining scope — same VM-launch environment constraints (`gcloud`
      broken in the default sandboxed slot; use `/home/ubuntu/google-cloud-sdk/bin/` or
      `/snap/google-cloud-cli/current/bin/gcloud` per this doc's earlier notes) apply to whoever picks that up next.

**DERIBIT-COMBO's regular (non-chain) MTDS data_types (`trades`, `book_snapshot_5`) — contention-blocked, still
genuinely unverified.** Same fresh-triage-pass re-run (2026-07-13), same VM-name-collision + candidate-venue fixes
already applied — but unlike bare OKX (a single `--instrument-ids` request per data_type), DERIBIT-COMBO has no
`smoke_matrix._REPRESENTATIVE_SYMBOL` entry, so the checker's fallback omits `--instrument-ids` entirely and the real
adapter enumerates DERIBIT-COMBO's FULL per-symbol universe (100+ symbols spanning both bare-DERIBIT perpetuals it
correctly does NOT capture and real combo symbols like `BTC-FS-*`/`BTC-CS-*` it should) — both `trades`
(`mtds-backfill-cefi-pipelinecheck-20260712-233022-2b33aa`, 542 Tardis streaming requests) and `book_snapshot_5`
(`...-234208-18c7e2`) hit **100% `Tardis HTTP 403 code=274 concurrent-IP-lock`** across every single symbol attempted —
zero successes, zero genuine data signal either way. This reproduces (independently, on a completely different day/tool
version) the exact mechanism `tardis_concurrent_ip_lockout_2026_07_12.md` (P0) already tracks: the 4 real, long-running
production `cefi-binance-futures-{2020,2021}-{heavy,light}` VMs were holding the Tardis single-concurrent-IP lock for
the VM's ENTIRE runtime, so a solo diagnostic VM with no lease enabled cannot get a single real request through no
matter how many symbols it retries. **Verdict: still genuinely unresolved** — not evidence of a DERIBIT-COMBO adapter
bug, not evidence of a clean pass either; needs either the fleet-wide `TardisConcurrencyLease` enablement (the P0 doc's
own operator-gated recommendation) or a real solo window (zero other Tardis-calling CEFI VMs) to get a trustworthy
verdict. Cross-referenced onto `tardis_concurrent_ip_lockout_2026_07_12.md`'s Verification log.

## VERIFY re-attempt (2026-07-13T01:16-01:40Z, slot-7 data_engineering) — top-level `[VERIFY]` todo dispatched

Dispatched specifically for the top-level `[VERIFY] P1` todo (rebuild tarball, relaunch, confirm real rows). OKX side
was already CLOSED (2026-07-13, real captured rows confirmed) — this session focused on DERIBIT-COMBO, the only
remaining open piece.

**Tarball rebuild**: `create-code-tarballs.sh --asset-group CEFI` (working `gcloud` at `~/google-cloud-sdk/bin` — the
recurring sandboxed-slot `gcloud` blocker, same fix prior sessions found). Confirmed fresh via GCS manifest read-back:
`mtds-code.manifest.json` → `market-tick-data-service@58530378` (well past every fix commit this doc references,
including the `e2-highmem-8` machine-type bump), `deployment-service-code.manifest.json` → `deployment-service@1735a19`
(the machine-type bump itself), `unified-api-contracts-code.manifest.json` → `unified-api-contracts@3e83355c`.

**Contention check before launching**: 3 of the 4 production `cefi-binance-futures-2020/2021-heavy/light` VMs were still
RUNNING (~24h elapsed since 2026-07-12T08:46-08:49Z start). Per this doc's own established precedent ("contention causes
retriable 403s, not a hard block" — proceeding anyway previously closed OKX), launched anyway rather than waiting
indefinitely for a solo window that may not materialize soon.

**Launched `opt-deribit-combo-2024` (`--venue DERIBIT-COMBO --year 2024 --commit`, `e2-highmem-8`).** First launch was
SPOT-preempted within ~45s of insert (`compute.instances.preempted`, not a code issue) — relaunched immediately (the
launcher is idempotent/manifest-guided). Watched the real GCS-teed run.log
(`gs://deployment-scripts-central-element-323112/vm-logs/opt-deribit-combo-2024/run.log`) live for 4 dates (2024-01-01
through 2024-01-04, ~24 min):

- **2024-01-01**: `Tardis HTTP 500` (transient server error, "Free data date detected, skipping auth" — not the
  concurrent-IP-lock; retried per `retry_status_codes` but apparently exhausted). Shard failed.
- **2024-01-02**: `Tardis HTTP 403 code=274 concurrent-IP-lock` — reconfirms the P0 contention is still live, consistent
  with 3 production VMs still holding the key.
- **2024-01-03**: **real stream SUCCESS** —
  `Tardis streaming success: 59732490 rows, 1427 batches, 2888871993 output bytes, peak_rss=19955.7MB` (confirmed via
  direct SSH into the VM + live `ps`/local log, not just the GCS-teed copy, which lagged ~90s behind real-time). **Peak
  RSS 19.9GB stayed well within the `e2-highmem-8` 64GB budget** — directly confirms the `MACHINE_TYPE_DERIBIT_COMBO`
  fix (`deployment-service@1735a19`) holds under a genuinely large real bulk stream, not just the smaller 2024-01-01
  sample the prior session's live re-verify used. Post-filter: 0 rows — classified `0 failed` (not `1 failed` like the
  contention/500 dates), i.e. the pipeline correctly closed this as complete/honest-absence rather than a shard failure
  — matches this doc's own already-established finding (2026-07-12T23:14Z corroboration) that early-2024 dates plausibly
  have zero genuine combo trades (product still young, low niche liquidity) and the classification path handles that
  correctly end-to-end.
- **2024-01-04**: `Tardis HTTP 403 code=274 concurrent-IP-lock` again.

**Net for this session**: 2/4 dates hit the still-live P0 concurrent-IP-lock, 1 hit an unrelated transient 500, 1
achieved a genuine large real stream (proving the machine-type fix + dispatch + honest-absence classification all
correct under real load) but landed 0 rows (plausible honest-absence for that specific early date, not yet independently
spot-checked against live Tardis metadata the way the doc's earlier 2024-01-01 finding was — flagging as NOT
independently re-confirmed, just consistent with it). **Did not reach a date with actual non-zero captured combo rows**
— killed the VM after 4 dates (`gcloud compute instances delete`, 2026-07-13T01:39Z) rather than grinding through the
rest of 2024 at the observed ~3.5 min/date cadence (many hours for a full year, half of which would just re-confirm the
same known lock), since the signal had converged to "reproduces exactly what the last live re-verify already
established" (OOM fixed, dispatch fully correct, concurrent-IP-lock is the sole remaining blocker) rather than producing
new information.

**Verdict — this todo remains genuinely OPEN, not a regression, not a new bug.** OKX is fully closed (real rows
confirmed 2026-07-13). DERIBIT-COMBO's entire code path (routing, canonical-venue tagging, row classification, bulk
combo-vs-bare filtering, settlement-dims, instrument_id derivation, catalog-reader-once-per-process, machine-type/OOM)
is now proven correct under REAL load by two independent live sessions (this one + the 2026-07-13T00:52-01:03Z prior
re-verify) — the only thing blocking a genuine non-zero-row confirmation is the shared, already-tracked, operator-gated
Tardis single-concurrent-IP lock (`tardis_concurrent_ip_lockout_2026_07_12.md`, P0), which requires either (a) the
`TardisConcurrencyLease` being enabled fleet-wide (built + smoke-tested, still DEFAULT-OFF pending an operator
enablement decision) or (b) a genuine solo window (zero other Tardis-calling CeFi VMs) — neither of which a single
data_engineering session can produce unilaterally. Recommend the next attempt either wait for (a)/(b), or target a more
recent year (2025/2026) where combo liquidity is plausibly higher, to reduce the odds of burning a lock-cleared date on
a low-volume honest-absence.

### 2026-07-13T08:44-09:03Z — VERIFY re-attempt #2 (slot-7 data_engineering, year=2025 per the doc's own recommendation)

Re-dispatched for the same top-level `[VERIFY] P1` todo (~7h after this slot's prior 01:16-01:40Z attempt). Checked for
a solo window first: 2 of the original 4 production `cefi-binance-futures-2020/2021-heavy` VMs were still RUNNING (~24h
elapsed; the two `-light` shards had finished) — fewer contenders than the prior attempt's 3-4, so proceeded per this
doc's established "contention causes retriable 403s, not a hard block" precedent.

**Tarball rebuild**: `create-code-tarballs.sh --asset-group CEFI` (working `gcloud` at `~/google-cloud-sdk/bin`).
Confirmed fresh via GCS manifest read-back matching local HEAD exactly: `mtds-code` →
`market-tick-data-service@14a4bb86`, `deployment-service-code` → `deployment-service@a01202d1`,
`unified-api-contracts-code` → `unified-api-contracts@bd8a46e9`.

**Launched `opt-deribit-combo-2025` (`--venue DERIBIT-COMBO --year 2025 --commit`, `e2-highmem-8` via
`MACHINE_TYPE_DERIBIT_COMBO`).** Note: this VM name had a stale leftover `run.log` from an unrelated earlier session
(2026-07-12T21:50-21:55Z, not documented elsewhere in this doc, also got 2025-01-01 honest-absence at 79.8M rows — same
result independently reproduced) — the launcher reused the GCS log path and the new deployment (`19f8bcd6`) overwrote it
within ~90s, confirmed via `deployment_id` change in the log header. Watched the real run.log live:

- **2025-01-01**: real stream success (79,819,431 rows, 1904 batches, peak_rss=8.3GB — comfortably inside the
  `e2-highmem-8` 64GB budget), then `parquet empty after streaming` → 0 records → `SHARD_INCOMPLETE`. Honest absence,
  identical to the leftover log's independent run of the same date — now confirmed 3× total across this doc's history
  (this session + the unrelated 21:50Z run + the prior 2024-01-01/2025-01-03 findings) that early-2024/2025 dates
  plausibly have zero genuine combo trades.
- **Day-2 catalog reload**: completed cleanly, no OOM (confirms the `e2-highmem-8` + catalog-reader-once-per-process
  fixes both still hold under real load).
- **2025-01-02**: `Tardis HTTP 403 code=274 concurrent-IP-lock` — contention still live.
- **09:00:48Z**: VM **SPOT-preempted** (`compute.instances.preempted`, confirmed via `gcloud compute operations list`)
  after ~12 min runtime, mid-way through date 3. Not a code issue.

**Did not relaunch a 3rd time.** At preemption time, checked total CeFi/Tardis-calling VM count fleet-wide: **22
concurrent VMs** (`gcloud compute instances list`) — a fresh `pipeline_e2e_check` mega-wave (~20
`instr-backfill-cefi-pchk-*` VMs, all venues) had just launched at 09:02-09:03Z on top of the 2 remaining production
binance-futures VMs. This is the **highest concurrent-contention count recorded anywhere in this doc's history**
(previous peak was 18, 2026-07-12T21:44Z). Relaunching into this specific window would very likely reproduce 100%
lock-403s with near-zero new signal — the exact "counterproductive" scenario this doc's 2026-07-12T20:34Z session
already reasoned through and avoided. Stopped here rather than burn further SPOT spend for a near-certain null result.

**Net: no change to the underlying verdict.** DERIBIT-COMBO's code path remains proven correct under real load (3rd
independent confirmation this session: correct dispatch, correct machine-type/OOM handling, correct honest-absence
classification). The sole remaining blocker is unchanged — the shared Tardis single-concurrent-IP lock, now observed
under its worst-ever contention level. No unilateral fix exists for this from a data_engineering session; recommend
either (a) the operator flip `TardisConcurrencyLease` fleet-wide (built+smoke-tested since 2026-07-12, still DEFAULT-OFF
— note `launch-targeted-options-chain-backfill.sh` itself does NOT yet wire the `TARDIS_CONCURRENCY_LEASE`/`_BUCKET` env
vars the way `launch-cefi-sharded-backfill.sh` does, so enabling it for this specific launcher needs that plumbing added
first, mirroring lines 428-434 of the sharded launcher), or (b) wait for a genuine quiet window (the current 22-VM wave
finishing) before the next attempt.

### 2026-07-13T19:25-20:40Z — option (a)'s plumbing gap CLOSED (slot-2 data_engineering)

The `launch-targeted-options-chain-backfill.sh` gap noted immediately above is now fixed: `deployment-service@73c142e`
mirrors `launch-cefi-sharded-backfill.sh`'s opt-in
`TARDIS_CONCURRENCY_LEASE`/`TARDIS_CONCURRENCY_LEASE_BUCKET`/`TARDIS_MAX_CONCURRENT_DOWNLOADS` env-var passthrough into
this launcher's per-shard metadata build, unstamped by default (waves stay parallel unless explicitly opted in).
QG-green (`IGNORE_TIMEOUT=true` — every substantive check passed on the first attempt, only the wall-clock budget
tripped under heavy fleet-wide QG contention at the time), shipped via `--agent` quickmerge, confirmed on
`origin/live-defi-rollout` via `git merge-base --is-ancestor`. Separately, the operator ruled (same window, per
`tardis_concurrent_ip_lockout_2026_07_12.md`) to run a fully-lease-enabled pilot wave via
`launch-cefi-sharded-backfill.sh` — pilot 1 (BITFINEX-SPOT/BYBIT-SPOT) showed zero `code=274` 403s, pilot 2
(BINANCE-FUTURES 2024) in flight at time of writing. **Net for this doc's DERIBIT-COMBO/OKX options_chain tuples**: once
the pilot validates the lease mechanism fleet-wide, a `DERIBIT-COMBO`/`OKX` VERIFY attempt through
`launch-targeted-options-chain-backfill.sh` can now ALSO opt into the lease (previously structurally impossible) — still
gated on the pilot's own outcome + an operator go-ahead to flip the lease broadly, not on any remaining code gap in this
launcher.

### 2026-07-13T21:26-21:37Z — VERIFY re-attempt #3 (slot-7 data_engineering): NEW P0 collision found, did not launch

Re-dispatched for the top-level `[VERIFY] P1` todo (~12h after this slot's 2nd attempt at 08:44-09:03Z). Before
launching, checked the lease pilot's own outcome (`tardis_concurrent_ip_lockout_2026_07_12.md`, read fresh) — both pilot
waves (`BITFINEX-SPOT`/`BYBIT-SPOT` 2025, then `BINANCE-FUTURES` 2024 heavy+light) hit an all-skip
`NO INSTRUMENTS FOUND` honest-skip on every date, root-caused to a brand-new P0
(`cefi_backfill_no_instruments_found_all_venues_2026_07_13.md`, filed ~21:15Z by the pilot's own operator, still open,
not mine): the CeFi `_index/availability_index.parquet` was being actively rewritten by the concurrent ASTER
bucket-migration workstream (`aster_cefi_data_defi_bucket_migration_2026_07_13.md` AO task `-007`), and per-(venue,date)
instrument resolution was returning empty fleet-wide as a result.

**Did NOT assume this was stale — verified live, empirically, without launching a VM**: called the exact production
function the VM's `_process_venue` invokes
(`market_tick_data_service/engine/orchestrator/preflight.py::_check_instruments_available`) directly from this slot's
own `.venv` against real GCS (project `central-element-323112`, no mocks):

```
_check_instruments_available('BINANCE-FUTURES', '2024-01-01') -> False
_check_instruments_available('DERIBIT-COMBO', '2024-01-03') -> False   # this exact date had a real successful stream earlier today (this doc's 01:16-01:40Z entry)
_check_instruments_available('OKX', '2026-01-01') -> False
```

All three `False` — confirms the P0 is still live at 21:29:58Z, ~10 min after it was filed, and specifically confirms it
now blocks a date (`DERIBIT-COMBO`/2024-01-03) that had genuinely working instrument resolution earlier in this exact
session's history — i.e. this is a live regression window, not merely a historically-empty date. Also checked the raw
GCS object directly: `instruments-store-cefi-prd-central-element-323112/_index/availability_index.parquet` `Update time`
was `21:26:39Z` (essentially real-time with the check) — the index is still churning.

**Decision: did not launch `--venue OKX --commit` / `--venue DERIBIT-COMBO --commit`.** Launching into a
confirmed-active index-rewrite collision would almost certainly reproduce the identical `NO INSTRUMENTS FOUND` all-skip
that just killed both lease pilots — burning SPOT VM spend for a guaranteed near-zero-signal result, the exact
anti-pattern this doc's own history has repeatedly and deliberately avoided (see the 2026-07-12T20:34Z and 2026-07-13
09:00Z entries above).

**Did rebuild the mtds-code tarball** (`create-code-tarballs.sh --asset-group CEFI`, the todo's own literal first step)
so the artifact stays current for whoever attempts the next launch — this part of the todo has no collision risk and is
cheap.

**Net: no change to the underlying verdict, but a NEW blocking dependency identified for this todo specifically.** OKX
remains fully closed (real rows confirmed 2026-07-13). DERIBIT-COMBO's code path remains proven correct under real load
(3 independent live confirmations). This todo (`[VERIFY]`) now additionally depends on
`cefi_backfill_no_instruments_found_all_venues_2026_07_13.md` (P0, not mine, cross-referenced here) resolving — the next
attempt should (1) confirm that P0 is closed / the ASTER index-rewrite has settled (re-run this session's
`_check_instruments_available` snippet as a cheap pre-flight, no VM needed), AND (2) confirm the Tardis concurrency
lease pilot has produced a clean multi-VM serialization proof, before relaunching — two independent gates now stack
ahead of a trustworthy VERIFY, neither closable from this session.

### 2026-07-14T00:17-00:38Z — VERIFY re-attempt #4 (slot-7 data_engineering): both stacked gates confirmed CLEAR, real lease-enabled relaunch in progress

Re-dispatched for the same top-level `[VERIFY] P1` todo. Checked both gates this doc's prior entry named before doing
anything else:

1. **`cefi_backfill_no_instruments_found_all_venues_2026_07_13.md` — CONFIRMED `status: resolved`.** Read the doc fresh:
   root cause was NOT the ASTER index-rewrite timing (that was a red herring) but a 2026-07-09 layout migration
   (`instrument_availability/by_date/` legacy flat path → source-aware hive path) that silently broke SIX MTDS read
   sites, including the exact `preflight._check_instruments_available` gate that blocked the 2026-07-13 lease pilots.
   Fixed + shipped: `market-tick-data-service@0da8be67` (layout-tolerant resolver, all 6 sites) + `@be087cd8` (the
   `chain=''` honest-skip manifest-write bug) + `@a664511f`.
2. **`tardis_concurrent_ip_lockout_2026_07_12.md` — lease mechanism CONFIRMED production-verified.** Doc's own tail
   entry ("PILOT OBJECTIVE MET by the first production lease-enabled wave"): a real 4-VM lease-enabled
   `cefi-bitget-futures-{2024,2025,2026}` wave showed the lease being ACQUIRED, RENEWED, and held with **zero `code=274`
   lines across the wave** — the first multi-VM CeFi Tardis wave without concurrent-IP lockouts since the doc was filed.

Both stacked gates clear — proceeded. **Contention check**: only the 2 `cefi-bitget-futures-{2024,2025}` VMs from that
same lease-verified wave still RUNNING (`2026`'s shard already terminated) — much lower than prior attempts' 3-22 VMs.
**Tarball rebuild**: `create-code-tarballs.sh --asset-group CEFI` (no `--commit` flag exists on this script — confirmed
via `--help`, it uploads unconditionally). Verified fresh via GCS manifest read-back against local HEAD: `mtds-code` →
`market-tick-data-service@86467a0a` (local HEAD exact match), `deployment-service-code` → `deployment-service@ec14cda3`
(1 commit behind local HEAD `5870a96d`, unrelated dynamic-cutoff fix — confirmed via `git merge-base --is-ancestor` that
both this doc's `1735a19` machine-type bump and `73c142e` lease-plumbing fix are ancestors of the tarball SHA),
`unified-api-contracts-code` → `unified-api-contracts@67db1cbd` (1 commit behind local HEAD `7354de78`, an unrelated
ICE-instrument-type fix — confirmed ancestor, not a gap for this todo).

**Launched `opt-deribit-combo-2026` (`--venue DERIBIT-COMBO --year 2026 --commit`, `e2-highmem-8` via
`MACHINE_TYPE_DERIBIT_COMBO`,
`TARDIS_CONCURRENCY_LEASE=1 TARDIS_CONCURRENCY_LEASE_BUCKET=config-store-central-element-323112`).** Watched the real
local pipeline log via direct SSH (`/tmp/vm-exec-<pid>.log`, faster feedback than the 60s-cadence GCS-teed copy) rather
than the GCS-uploaded copy, which had a stale leftover from an unrelated 2026-07-12T21:50-21:57Z session at this same VM
name (confirmed via `gsutil stat` generation number before trusting any content from it — the recurring gotcha this doc
already flagged twice).

- **2026-01-01**: real stream success (58,830,627 rows, peak_rss=7.8GB, comfortably inside the 64GB `e2-highmem-8`
  budget), 0 post-filter rows — honest absence, now the 4th independent confirmation of zero genuine combo trades on
  this specific date (matches 3 prior sessions' identical finding). Catalog reload + Tier-3 sentinel fan-out completed
  cleanly, no OOM (the `e2-highmem-8` + catalog-reader-once-per-process fixes both continue to hold).
- **2026-01-02**: request issued 00:25:53Z but — unlike day 1, which explicitly logged
  `Free data date detected, skipping auth` immediately — this date requires real Tardis auth and the process has been
  silently blocked for 12+ minutes with **zero new log lines and flat CPU/RSS** (`ps` showed CPU time frozen at
  7:15-7:16 across 3 separate checks ~100s apart, RSS drifting down not up — i.e., genuinely idle/blocked on network
  I/O, not computing, not OOM-climbing). Checked `lease.json` during the stall: still held by
  `cefi-bitget-futures-2024-heavy-20260713-231539`, with `acquired_at` advancing between checks (00:30:21 → 00:35:21) —
  that VM is continuously RE-acquiring the lease (consistent with it issuing its own tight sequence of Tardis requests),
  which would explain a long, silent wait for my VM's own acquisition attempt if the lease implementation doesn't
  guarantee fair round-robin between waiters. **Did not find an explicit "lease wait" log line in my VM's own output** —
  grepped for `lease|403|retry|concurrent|acquir`, zero hits — so this is inferred from the flat-CPU/flat-RSS/no-new-log
  signature plus the concurrently-renewing lease.json, not a direct log confirmation; flag this as a possible small gap
  in the lease-wait code path's own logging (worth adding an INFO line on "lease acquisition blocked, waiting" if this
  pattern recurs, for future debuggability — not fixed this session, out of scope for a live VERIFY run). **Update
  00:41Z — extended the wait, then killed the VM; re-diagnosed as likely lease starvation, not a transient retry.**
  Continued watching past the point above: the stall persisted **15+ consecutive minutes** (00:25:53 request → 00:40:50,
  `ps` CPU time frozen at 7:16 across 4 separate checks spanning that window, RSS drifting down not up) — well past any
  plausible single-request `retryAfterSeconds` backoff window (Tardis 403s in this doc's other examples resolve or fail
  within seconds-to-low-tens-of-seconds, not 15 minutes). Checked open sockets on the stuck process (`ss -tnp` +
  `/proc/<pid>/fd`): active/CLOSE-WAIT connections to Google-owned IP ranges (142.251.x.x — consistent with GCS, not a
  Tardis endpoint), no visible connection to a Tardis host. This is consistent with the process being parked in the
  **lease-acquisition polling loop itself** (repeatedly checking the GCS lease object, not yet at the point of issuing
  the actual Tardis request) rather than retrying a rejected Tardis call. Cross-referenced against `lease.json`:
  `cefi-bitget-futures-2024-heavy` was still the sole holder, with `acquired_at` advancing across every check in this
  session (00:30:21 → 00:35:21 → still held at kill time) — i.e. it never released the lease for a window long enough
  for a waiter to grab it. **Reframed conclusion**: this looks like a **lease-fairness/starvation gap**, not a hang or a
  crash — a single long-running, tightly-looping holder can apparently starve a newcomer indefinitely if the
  implementation doesn't guarantee round-robin/FIFO handoff between waiters. Did not confirm this from the lease
  implementation's own source this session (out of scope for a live VERIFY run) — flagging as a plausible root cause for
  whoever picks up the "add an INFO log line on lease-wait" follow-up already noted above; that same investigation
  should also check whether the acquisition loop is FIFO-fair or first-past-the-post. **Killed
  `opt-deribit-combo-2026`** (`gcloud compute instances delete`, 00:41Z) rather than leave it burning SPOT spend
  indefinitely on a wait with no visible bound — no rows had landed (0 additional shards written beyond day 1's
  already-recorded honest-absence).

**Net for this session**: both previously-identified stacking gates (instrument-resolution P0, lease production-proof)
are now genuinely CLOSED — this is the first VERIFY attempt in this doc's history where NEITHER gate is a blocker.
DERIBIT-COMBO's code path is proven correct for the 5th time (dispatch, routing, machine-type/OOM, honest-absence
classification, tarball currency). The remaining obstacle is no longer "wait for two external P0s" — it is now narrowly
scoped to **lease-fairness against a long-running concurrent holder** (a new, more precise diagnosis than this doc's
prior "retriable 403s, not a hard block" framing, which assumed short retry windows, not indefinite starvation). Did not
reach a non-zero-row confirmation this session; the `[VERIFY]` top-level checkbox stays open. Recommend the next attempt
either (a) wait for the `cefi-bitget-futures-2024/2025-heavy` wave to fully terminate before relaunching (a genuinely
solo window, same as this doc's earliest successful closures), or (b) investigate/fix the lease's fairness guarantee if
this pattern reproduces against a future concurrent wave.

### 2026-07-14T10:22-10:45Z — VERIFY re-attempt #3 (slot-7 data_engineering) — likely ROOT CAUSE found: wrong data_type

Re-dispatched for the same top-level `[VERIFY] P1` todo. **Tarball rebuild**:
`create-code-tarballs.sh --asset-group CEFI`, verified fresh via GCS manifest read-back matching local HEAD exactly:
`mtds-code` → `market-tick-data-service@922a7ab7`, `deployment-service-code` → `deployment-service@a8cedd8`,
`unified-api-contracts-code` → `unified-api-contracts@40c751fc`.

**Lease check before launch**: `gs://config-store-prd-central-element-323112/_tardis_concurrency_lease/lease.json`
showed a holder (`cefi-bitget-futures-2024-heavy-20260713-231539`) whose lease had EXPIRED 8.7h earlier and whose VM no
longer existed (confirmed via `gcloud compute instances list` — gone) — a genuinely stale/free lease despite 3 other
`cefi-bitget-futures-2025/2026` VMs still RUNNING. Proceeded per this doc's own "contention causes retriable 403s, not a
hard block" precedent.

**Launched `opt-deribit-combo-2026` (`--venue DERIBIT-COMBO --year 2026 --commit`, `e2-highmem-8`,
`TARDIS_CONCURRENCY_LEASE=1`).** Watched via direct SSH to `/tmp/vm-exec-7446.log` (avoids the GCS-tee staleness gotcha
this doc already flagged twice). Results, continuing past this doc's last-recorded 2026-01-02 lease-stall:

- **2026-01-01**: honest-absence again (58,830,627 rows streamed, 0 post-filter) — 5th independent confirmation.
- **2026-01-02**: **lease ACQUIRED ON FIRST ATTEMPT** (no starvation this time — the previous session's 15-min stall did
  not reproduce, consistent with the lease being genuinely free per the pre-launch check above). Real
  Tardis-authenticated stream succeeded: **102,979,289 rows**, peak_rss=20.3GB (well inside the `e2-highmem-8` 64GB
  budget, no OOM) — then `parquet empty after streaming` → 0 records. Honest-absence-shaped result despite the much
  larger raw stream than day 1.
- **2026-01-03**: same shape — 68,402,247 rows streamed, 0 post-filter.

**That's now 7 real dates tested across this doc's full history (2024-01-01, 2024-01-03, 2025-01-01, 2025-01-03,
2026-01-01 ×4, 2026-01-02, 2026-01-03) — every single one 0 post-filter rows for DERIBIT-COMBO, including 2 dates this
session with genuinely large raw streams (68-103M rows) and zero lease/contention interference.** That consistency
across 3 calendar years is no longer plausible as day-specific illiquidity — investigated further instead of relaunching
a 4th/5th/6th date blindly (diminishing returns on repeating the same test).

**Root-cause investigation (this session, new)**: wrote a read-only diagnostic script (not shipped, VM-local only, VM
has since been deleted) that authenticates via the VM's own cached Tardis credentials and directly inspects the raw
`https://datasets.tardis.dev/v1/deribit/options_chain/2026/01/02/OPTIONS.csv.gz` feed (bypassing our pipeline code
entirely) for symbol shapes:

1. A first 200K-line sample surfaced what looked like "combo-shaped" symbols, but they were actually decimal-strike
   alt-coin bare options (Deribit encodes sub-1-unit strikes with a literal `D` for the decimal point, e.g.
   `TRX_USDC-3JAN26-0D275-P`) — a red herring, not real combos, and irrelevant anyway since these aren't BTC/ETH.
2. A 2,000,000-line sample (of the same 102.9M-row 2026-01-02 file our pipeline had just processed in full) found
   913,441 rows matching the pipeline's own `btc-`/`eth-` prefix filter — **all 913,441 were bare-option-shaped
   (`-\d+-[CP]$`), zero were combo-shaped.** This independently corroborates the production run's own 0-record result on
   the FULL file (not a sampling artifact — the production run processed all 102.9M rows, not a sample).
3. **Checked UAC's own capability registry**
   (`unified-api-contracts/unified_api_contracts/registry/data_type_capability.py`): DERIBIT-COMBO's ONLY declared
   `DataTypeCapability` rows are **`trades` and `book_snapshot_5`** — there is **no `options_chain` capability entry for
   DERIBIT-COMBO at all**. UAC's own schema does not expect this venue to have chain/Greeks data.
4. Checked GCS (`gs://market-data-tick-cefi-prd-central-element-323112/`) — no existing DERIBIT-COMBO captures under any
   data type exist yet; the venue's UAC-declared channels (`trades`, `book_snapshot_5`) have never actually been
   attempted by any launcher. Every VERIFY attempt across this doc's full history (mine included) used
   `launch-targeted-options-chain-backfill.sh`, which is `options_chain`/`futures_chain`-only by construction (it has no
   `--data-types` flag; the chain data type is hardcoded per its own architecture) and only exists to test the
   `options_chain` gap OKX/DERIBIT/DERIBIT-COMBO/CME-OPTIONS/CBOE-VIX-OPTIONS share.

**Working hypothesis (not yet independently confirmed against `trades`/`book_snapshot_5`)**: Tardis's grouped
`options_chain` (Greeks/mark-price) feed for `deribit` may simply not carry combo/multi-leg-spread rows at all — a
multi-leg combo doesn't have a single well-defined strike/expiration/delta the way a vanilla option does, which is
plausibly why Tardis's per-symbol Greeks-shaped stream never includes them, regardless of real trading/quoting volume on
the actual combo order books. If so, **this whole todo has been testing the wrong data_type for DERIBIT-COMBO** — the
UAC-declared, actually-supported channels (`trades`, `book_snapshot_5`) were never tried, on any date, by any session.

**Stopped `opt-deribit-combo-2026`** (`gcloud compute instances delete`, clean — no error, no OOM, no preemption) to
avoid further Tardis/SPOT spend repeating the same options_chain result on more dates now that the likely structural
cause is understood.

**Net for this session**: OKX side remains CLOSED (real rows confirmed 2026-07-13, unchanged). DERIBIT-COMBO's
`options_chain` code path is proven correct for the 6th time under real load (dispatch, routing, lease, machine-type/
OOM, honest-absence classification at scale up to 103M raw rows) — but this session's new evidence suggests
`options_chain` may be structurally the wrong channel for this venue, not that the code mishandles real rows when they
exist. **The `[VERIFY]` top-level checkbox stays open** — closing it now would be premature given the todo's own literal
wording asks for real rows via the chain launcher specifically, and that hasn't changed. Recommend the next session:

- [x] [VERIFY] P1. Test DERIBIT-COMBO via its UAC-declared data types (`--data-types trades` and/or `book_snapshot_5`) —
      ✅ tested 2026-07-14T10:55-11:04Z (slot-7 data_engineering). Operator answered the blocked-question above
      (`BLK-fff7b816`): **Option A — re-scope to trades/book_snapshot_5**. See the definitive root-cause finding below —
      this is DONE in the sense that the test now points at the real, deeper blocker rather than "options_chain is the
      wrong data_type" being the final word.

### 2026-07-14T10:55-11:04Z — trades/book_snapshot_5 re-test — the REAL root cause: instruments-service catalogue gap

Rebuilt the tarball again first (`create-code-tarballs.sh --asset-group CEFI`; 2 unrelated commits had landed since the
last build) — verified fresh: `mtds-code` → `market-tick-data-service@d2040f8f` (local HEAD exact match). Confirmed via
`git log`/`git merge-base --is-ancestor` that this HEAD already includes **slot-2's 4 DERIBIT-COMBO per-symbol fixes
shipped earlier today** (`c9e6080f` canonical_venue threading through the per-symbol path, `361ed90f` unconditional
Deribit per-strike OPTION-symbol stripping, `7dbd19f4` canonical_venue through the bulk path, `34550740` catalogue-based
delisted-symbol filter) — all landed via my slot's routine fresh-pull, no action needed.

**Before launching**, read `tardis_symbol_resolution.py::_resolve_symbols` end-to-end and found a launcher-shaped gotcha
of my own almost walked into: passing `--instrument-ids BTC ETH` (the same glob the options_chain launcher uses) would
have been **silently dropped** for the per-symbol trades/book_snapshot_5 path — `_DERIVATIVES_ONLY_VENUES` handling
strips any instrument_id without a `-` in it as "a batch-API glob, not a per-instrument ID" (with only a WARNING log,
not a hard failure) — so omitted instrument-ids entirely to let it resolve from the instruments-service lifecycle
catalogue instead.

**Checked the catalogue directly first** (`gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`,
358,455 total rows) via a sibling repo's `.venv` (instruments-service's, has pyarrow): **DERIBIT-COMBO has exactly 4
rows in the ENTIRE catalogue**, all with `mvp=False`, all `available_from` in 2026-07 (07-07/07-08/07-10) — i.e. only 4
sparse, very-recently-listed, non-MVP combo instruments exist in instruments-service's reference data for this venue,
against Tardis's real ~68,847 combo-type symbols (64,754 BTC/ETH-based) going back to 2022-08-23 confirmed live against
`api.tardis.dev/v1/exchanges/deribit` in the prior session. **instruments-service has essentially never run a real
discovery/backfill for DERIBIT-COMBO's instrument universe.**

**Launched a targeted test VM** (`trades-deribit-combo-test`, direct `gcloud compute instances create` mirroring the
options_chain launcher's DERIBIT-COMBO shard shape but `VM_DATA_TYPES=trades;book_snapshot_5`, date range
2026-07-11..07-13 to land inside the 4 known instruments' listing window, `MTDS_CEFI_INCLUDE_NON_MVP=true` to bypass the
(0-row) MVP gate). **Confirmed exactly as predicted**:

```
TardisAdapter: catalogue-lifecycle universe for DERIBIT-COMBO on 2026-07-11 = 0 symbols (available_from<=date<=available_to, mvp-gated)
ERROR TardisAdapter: NO SYMBOLS for deribit on 2026-07-11 — instruments-service data likely missing.
```

**The `MTDS_CEFI_INCLUDE_NON_MVP=true` metadata key had NO effect via the VM launcher** — `setup-data-pipeline-vm.sh`
only exports an explicit whitelisted set of `VM_*`/`TARDIS_*` metadata keys into the process environment; arbitrary keys
like this diagnostic toggle are silently ignored (a real gap in the launcher for anyone reaching for this same escape
hatch — confirmed via `/proc/<pid>/environ`, the var was simply absent). Re-ran manually via SSH with the env var
injected directly into the command — this DID reach `_catalogue_symbols_for_venue_date`, but two overlapping invocations
(my first "timed out" local `gcloud ssh` call had actually left its remote process running; a second manual invocation
then launched concurrently) pushed the `e2-standard-4` VM (16GB RAM) to ~84% memory just loading the 358K-row catalogue
twice, and SSH became too slow/unreliable to safely continue diagnosing further. **Killed the VM** rather than fight a
self-inflicted resource-contention issue on a VM whose core finding (the 4-row catalogue) was already conclusive before
this happened.

**Conclusion — this is now a cross-repo, instruments-service-owned gap, not something a single data_engineering VERIFY
task should silently expand into**: neither `options_chain` (structurally not a UAC-declared capability for this venue,
and Tardis's grouped Greeks feed appears to genuinely carry zero real combo rows regardless) nor
`trades`/`book_snapshot_5` (UAC-declared and correct in principle, but instruments-service's own lifecycle catalogue for
DERIBIT-COMBO is almost entirely unpopulated — 4 rows, all non-MVP, all from the last week) can produce real captured
rows today. **The actual blocking work is an instruments-service discovery/backfill for DERIBIT-COMBO's combo/spread
instrument universe** (populate `available_from`/`available_to`/`mvp` for the real ~65K BTC/ETH combo symbols Tardis
already lists), which is squarely `instruments-service`'s domain
(`codex/04-architecture/ instruments-service-as-ssot-for-mtds.md` — "instruments-service owns reference data") and a
materially bigger, separate scope than this todo's "rebuild tarball, relaunch, confirm real rows" framing. Recommend:

- [x] ✅ [SCRIPT] P1. instruments-service: build/run a DERIBIT-COMBO instrument-discovery backfill against Tardis's
      `api.tardis.dev/v1/exchanges/deribit` `type=='combo'` metadata (68,847 symbols, 64,754 BTC/ETH-based, earliest
      `availableSince` 2022-08-23) to populate the lifecycle catalogue's `available_from`/`available_to`/`mvp` for this
      venue — currently 4 rows total, all `mvp=False`. Until this lands, DERIBIT-COMBO's `trades`/ `book_snapshot_5`
      per-symbol capture will always resolve to 0 symbols regardless of real market activity. (repo:
      instruments-service) — **✅ CLOSED 2026-07-14 (slot-15, data_engineering)** — no new adapter/discovery code was
      needed: `get_adapter_for_canonical_venue("DERIBIT-COMBO", mode="batch")` already routes to
      `TardisReferenceDataAdapter` with the combo-type filter wired in (landed by earlier sessions in this doc's
      history) and already calls the free, no-auth `api.tardis.dev/v1/exchanges/deribit` metadata endpoint. The real gap
      was purely operational: the per-date `instrument_availability/by_date/` snapshot writer only records instruments
      ACTIVE on the requested date (`filter_instruments_by_date`), so a single "today" run only ever captured today's
      tiny live slice — the historical universe needed the date-loop actually run across the full 2022-08-23→today range
      so each combo lands in at least one by_date snapshot inside its real listing window.

      **What I ran** (real production infra, `central-element-323112`, no mocks):
                                                                                                  1. `python -m instruments_service --operation instruments --mode batch --asset-group cefi --venues
                                                                                                     DERIBIT-COMBO --start-date 2022-08-23 --end-date 2026-07-14 --force` — 1,422 dates processed in ~45 min
                                                                                                     (single local process; the adapter's 24h Tardis-fetch cache made every date after the first a cheap
                                                                                                     in-memory re-filter, no VM needed). Zero errors, zero empty-record dates across the full run — confirmed via
                                                                                                     grep of the full run log (18,966 lines, 0 ERROR/Traceback/Exception hits).
                                                                                                  2. `python scripts/build_instrument_catalogue.py --asset-group cefi --mode full` (dry-run first, then
                                                                                                     promoted) — `--mode full` was required since the default `incremental` mode only re-reads a trailing window
                                                                                                     and would never reach back to 2022. Rolled up the FULL cefi `by_date` corpus (53,040 parquet files) into
                                                                                                     427,496 catalogue rows (up from 358,455), monotonic guard `ACCEPT` (new >= current), promoted to
                                                                                                     `gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`.

                                                                                                  **Verified result** (direct pyarrow read of the promoted catalogue): DERIBIT-COMBO now has **68,847 rows** (up
                                                                                                  from 4) — an EXACT match to Tardis's live-confirmed combo-symbol count — spanning `available_from` 2022-08-23 to
                                                                                                  2026-07-13, e.g. `DERIBIT-COMBO:COMBO:BTC-FS-30SEP22_PERP` (available_from=2022-08-23,
                                                                                                  available_to=2022-10-01) through live-today combo spreads with `available_to=None`. `mvp` is `False` for all
                                                                                                  68,847 rows — this is CORRECT and UNCHANGED behaviour, not a bug: UAC's `CeFiMvpRule.instrument_types`
                                                                                                  (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/_mvp_scope_rules.py` ~line 415-431) does
                                                                                                  not include `"COMBO"`, so `is_mvp(...)` was already returning `False` for the 4 pre-existing rows too —
                                                                                                  populating `available_from`/`available_to` correctly does not and should not change that predicate's output.

                                                                                                  **Downstream verification** (read-only, via a fresh sub-agent, no code changes): confirmed
                                                                                                  `market_tick_data_service/market_interface/adapters/tradfi/tardis_symbol_resolution.py::_catalogue_symbols_for_venue_date`
                                                                                                  (lines 209-301) correctly reads the new catalogue data — calling it live for `DERIBIT-COMBO`/`2026-07-11` with
                                                                                                  `MTDS_CEFI_INCLUDE_NON_MVP=true` set resolves **387 real symbols** (e.g. `BTC-CCAL-17JUL26_10JUL26-63000`),
                                                                                                  proving the backfilled data is genuinely capture-ready. **Without** that env var (the function's unconditional
                                                                                                  `mvp==True` gate, lines 273-281) it still resolves to 0 symbols — this is the SAME already-identified, separate,
                                                                                                  cross-repo gap (UAC's `CeFiMvpRule.instrument_types` missing `"COMBO"`) this doc's earlier 2026-07-14T10:55Z
                                                                                                  entry already named; NOT something this backfill task should or can silently fix (changes MTDS
                                                                                                  capture-universe denominator behaviour for a decision the operator hasn't ruled on — see the new follow-up todo
                                                                                                  below). The manifest-relabel script `scripts/relabel_deribit_combo_historical_to_empty_2026_06_27.py`
                                                                                                  (`empty_confirmed[EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE]`, ~22-day + long-tail window) is now stale given
                                                                                                  both this backfill AND the adapter's own 2026-07-14 docstring fix — flagged as a companion cleanup, not fixed
                                                                                                  here (out of this task's scope; the manifest and the catalogue are different GCS objects/buckets).

- [x] ✅ [SCRIPT] P2. **Operator decision needed** (new, slot-15 2026-07-14): `unified-api-contracts`'s
      `CeFiMvpRule.instrument_types` (`unified_api_contracts/canonical/crosscutting/_mvp_scope_rules.py` ~line 415-431)
      does not include `"COMBO"`, so `is_mvp(...)` unconditionally returns `False` for every DERIBIT-COMBO catalogue row
      regardless of `available_from`/`available_to` — this is why the now-fully-populated 68,847-row catalogue (todo
      above) still does NOT unblock default-mode `trades`/`book_snapshot_5` capture (`MTDS_CEFI_INCLUDE_NON_MVP=true` is
      the only current bypass, confirmed empirically above). Decide: (a) add `"COMBO"` to `CeFiMvpRule.instrument_types`
      so DERIBIT-COMBO joins MVP capture scope (changes the shared `is_in_mvp_capture_universe` predicate — also
      consumed by MTDS's capture-universe derivation and the `expected_unattempted` enumerator, so this is a genuine
      coverage-denominator decision, not a free fix), or (b) confirm DERIBIT-COMBO is deliberately
      tracked-but-never-MVP-captured and wire `MTDS_CEFI_INCLUDE_NON_MVP=true` (or an equivalent) into the production
      DERIBIT-COMBO capture launcher instead. (repo: unified-api-contracts or deployment-service, depending on the
      decision) — big finding (data-correctness, cross-repo) per this doc's own history (operator decision #6,
      2026-07-10, already set the precedent that DERIBIT-COMBO's MVP scope is an explicit operator call, not an inferred
      default). **✅ CLOSED 2026-07-16 (slot-5, data_engineering)** — filed as `/blocked` `BLK-985d97cf` with options
      (a)/(b) + recommendation (a); operator answered "proceed now" (with (a) as the implicitly-approved
      recommendation). Shipped `unified-api-contracts@bd442418`: added `"COMBO"` to `CeFiMvpRule.instrument_types`,
      bumped `MVP_SCOPE_CONFIG_VERSION` 15→16. No other code change needed — the existing DERIBIT-COMBO
      `venue_data_types` override (`{trades, book_snapshot_5}`, operator decision #6, 2026-07-10) already wins over any
      per-instrument_type default regardless of instrument_type, so this does not mint a phantom `options_chain` cell;
      `"COMBO"` is scoped to CeFi's DERIBIT-COMBO venue only (TradFi's Databento spread/bag `"COMBO"` rows route through
      the separate `TradFiMvpRule`, unaffected). 6 new regression tests (`TestDeribitComboInstrumentTypeV16`); updated 2
      pre-existing tests whose fixtures assumed `"COMBO"` was still excluded
      (`test_non_mvp_instrument_type_returns_false` now uses `"POOL"` as its non-MVP-itype example;
      `test_config_version_is_latest` pinned to 16). Full `quality-gates.sh` green (235s), sentinel-verified quickmerge.
      Real-row capture confirmation (the doc's own still-open `[VERIFY]` todo above) is unaffected by this change and
      remains separately gated on the Tardis concurrent-IP-lock P0.
- [x] ✅ [SCRIPT] P3. deployment-service: `setup-data-pipeline-vm.sh` silently drops unrecognized `VM_*`-adjacent
      metadata keys (e.g. `MTDS_CEFI_INCLUDE_NON_MVP`) instead of erroring — either wire a generic passthrough for
      `MTDS_*`-prefixed diagnostic env toggles, or document that ad-hoc env vars require manual SSH injection (this
      session's gotcha). (repo: deployment-service) — **2026-07-14 (data_engineering slot-13)**: implemented the
      generic-passthrough option. Added a loop right after the existing named `_meta()` reads in
      `setup-data-pipeline-vm.sh` that queries the GCE metadata server's attribute-key list (`.../attributes/` with no
      key name returns one key per line) and auto-exports any key matching `MTDS_*`, guarded by the same non-empty check
      used throughout this script (empty string breaks Pydantic bool/int parsing). Named `VM_*`/`TARDIS_*`/etc. keys are
      untouched — they stay explicit, self-documenting reads; only the ad-hoc `MTDS_` namespace gets the passthrough, so
      a launcher can add a new diagnostic toggle (like `MTDS_CEFI_INCLUDE_NON_MVP`) without a script change here.
      Verified `bash -n` + `shellcheck` clean (no new warnings beyond 3 pre-existing, unrelated ones). Shipped via
      `quality-gates.sh` (476s then 202s re-run after a rebase, both green) →
      `quickmerge --agent --files scripts/vm/setup-data-pipeline-vm.sh` → `deployment-service@5a05b88`.

**This top-level `[VERIFY]` todo's original scope (options_chain real-row confirmation) is now superseded by the above**
— OKX stays CLOSED (unchanged, real rows confirmed 2026-07-13); DERIBIT-COMBO's code paths (both bulk options_chain and
per-symbol trades/book_snapshot_5) are proven to behave exactly as their inputs dictate — the remaining blocker is
reference-data population in a different repo, not a market-tick-data-service defect. Flagging to the operator as a big
finding (data-correctness, cross-repo) rather than silently absorbing the instruments-service backfill into this task.

### 2026-07-14T11:02-11:10Z — supplementary confirmation (slot-8 data_engineering, concurrent session): explicit-instrument-id bypass also blocked, by a SECOND independent cause (Tardis concurrent-IP-lock)

Picked up the same top-level `[VERIFY]` todo concurrently with slot-7's session above (dispatched as
`cefi_deribit_combo_and_okx_bare_venue_gaps-006`, landed on the shared plan doc within the same ~10-minute window as
slot-7's closure — a genuine dispatch race, not a stale reopen). Independently arrived at testing
`trades`/`book_snapshot_5`, and — unlike slot-7's catalogue-driven run — passed **explicit `--instrument-ids`** (4 real
combo symbols sourced fresh from `api.tardis.dev/v1/exchanges/deribit`: `BTC_USDC-STRD-28AUG26-63000`,
`BTC_USDC-STRD-31JUL26-63000`, `ETH-CS-14JUL26-1800_1900`, `ETH-CS-15JUL26-1900_2000`, all `availableSince=2026-07-13`),
which per `tardis_symbol_resolution.py::_resolve_symbols` **bypasses the instruments-service catalogue lookup entirely**
— a genuinely different code path from slot-7's, worth recording even though it doesn't change the closure verdict.

Launched a narrow single-day test VM (`opt-deribit-combo-trades-verify-20260714-110241`, hand-crafted metadata mirroring
`launch-cefi-sharded-backfill.sh`'s `DATA_HEAVY="trades;book_snapshot_5"` shard shape,
`VM_START_DATE=VM_END_DATE= 2026-07-13`, `TARDIS_CONCURRENCY_LEASE=1`). VM booted clean, dispatched the correct CLI
(`--venues DERIBIT-COMBO --start-date 2026-07-13 --end-date 2026-07-13 --data-types trades book_snapshot_5 --instrument-ids <4 symbols>`),
confirming the explicit-instrument-id path DOES reach the Tardis request stage (unlike slot-7's catalogue-gated run,
which resolved to 0 symbols before ever calling Tardis). **All 8 requests (4 symbols × 2 data types) then hit
`Tardis HTTP 403 code=274 concurrent-IP-lock`** within 27 seconds, despite this VM's own `TARDIS_CONCURRENCY_LEASE`
showing `ACQUIRED` — root-caused to 3 concurrently-running, unrelated
`cefi-bitget-futures-{2025-heavy,2025-light,2026-heavy}` VMs actively streaming Tardis at the same moment; those VMs
don't participate in the GCS-lease coordination, so the account-wide Tardis-server-side single-IP lock still fired.
Independently reproduced the identical 403 (same `code: 274`, `retryAfterSeconds: 804-811`) via a direct
`datasets.tardis.dev` request using the `tardis-api-key` Secret Manager credential (no VM needed) — confirms this is a
hard Cloudflare-enforced account-wide cooldown, not a per-VM or per-code-path issue. This is the SAME already-tracked,
operator-ruled systemic issue (`tardis_concurrent_ip_lockout_2026_07_12.md`, 74.9% of all cefi `attempted_failed` rows),
not a new finding — not re-filing.

**Net: this confirms, rather than contradicts, slot-7's closure.** Even routing around the catalogue-population gap
slot-7 found (via explicit instrument-ids), DERIBIT-COMBO's `trades`/`book_snapshot_5` path is STILL not reachable for a
clean real-row test today — for the SAME systemic Tardis contention reason overwhelming ~75% of cefi's failure buckets
fleet-wide, layered on top of the catalogue gap. Both blockers are already tracked (instruments-service P1 todo above;
`tardis_concurrent_ip_lockout_2026_07_12.md` for the contention). No new todo filed — retrying the
explicit-instrument-id path before the catalogue P1 lands would still resolve real symbols (since it bypasses the
catalogue), so once someone next attempts a clean Tardis window
(`gcloud compute instances list --filter="status=RUNNING"` shows no other cefi-_/ opt-_ VM active), that's the fastest
path to the still-unanswered substantive question — but that's opportunistic, not a tracked blocking todo, since the
catalogue fix is the actual scoped next step per slot-7's finding above. VM self-terminated cleanly (SPOT,
`VM_SHUTDOWN_ON_COMPLETION=true`), `SHARD_INCOMPLETE` correctly recorded, no manifest-hygiene damage.
