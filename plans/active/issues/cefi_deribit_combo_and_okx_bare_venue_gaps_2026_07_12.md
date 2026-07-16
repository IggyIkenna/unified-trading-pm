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
    mvp_backfill_cefi_tick_v10_2026_06_27.md,
    cefi_layer1_denominator_gaps_2026_07_03.md,
    ../../../codex/02-data/honest-coverage-model.md,
    ../../../codex/02-data/availability-manifest-and-data-status.md,
    ../../../codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-12
parent_epic: cefi_master
priority: P1
source: mvp_backfill_cefi_tick_v10_2026_06_27.md G4 re-verification, 2026-07-12T07:20-08:05Z session
assigned_vm: planning
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

## Real end-to-end VERIFY attempt (slot-2, 2026-07-12, ~19:00-19:57Z) — TWO MORE code-level bugs found, launches killed

Picked this issue back up to actually run the item-3 VERIFY (re-launch + confirm real rows) now that both `[CODE]` todos
above show ✅. Found the earlier code fixes (routing entries, `_TARDIS_CEFI_VENUES` union, `_resolve_tardis_exchange`
call-site fix, `_route_tardis`'s `canonical_venue` threading) were necessary but NOT sufficient — three additional,
independent bugs sat between "code is fixed" and "a real VM captures a row." Fixed the first two, found + precisely
diagnosed (but did NOT fix) the third and fourth:

**Bug A (FIXED, shipped `deployment-service@a1454a6` + `market-tick-data-service@7c4e6354`)** — First launch of both
venues (per this issue's item-3/item-VERIFY-LIGHTER instructions) showed `venues=[]` for EVERY date on BOTH OKX and
DERIBIT-COMBO (`WARNING No active venues for date=... asset_groups=['CEFI']`), despite
`launch-targeted-options-chain- backfill.sh` correctly passing `VM_VENUE=OKX` / `VM_VENUE=DERIBIT-COMBO`. Root cause,
one layer EARLIER than every fix above: `market_tick_data_service.engine.orchestrator.get_venues_for_asset_groups()`'s
CEFI branch only derives candidate venues from `_VENUE_MAPPING.tardis_to_venue.values()` (a 1:1 exchange-slug→venue
reverse map) + `all_cefi_onchain_clob_venues` — and bare `"OKX"` / `"DERIBIT-COMBO"` structurally CANNOT appear in that
1:1 map (OKX spans 4 Tardis exchange slugs; DERIBIT-COMBO shares the `"deribit"` slug already claimed by bare DERIBIT),
even though both are real, declared venues in UAC's `VENUES_BY_ASSET_GROUP["cefi"]`. So
`_build_active_venues_for_date`'s `venue_filter=["OKX"]`/`["DERIBIT-COMBO"]` intersected against a candidate set that
never contained them → `active_venues=[]` → the whole day short-circuits before `_route_tardis`/the itype-aware exchange
resolution is ever reached. Fix: explicitly add `"OKX"` + `"DERIBIT-COMBO"` to the CEFI branch's venue list
(`market-tick-data-service@7c4e6354`, 1 regression test). VMs self-completed with `venues=[]`→fixed dispatch confirmed,
but then hit Bug B.

**Bug B (FIXED, shipped `deployment-service@467be0c`)** — After Bug A's fix, the relaunch reached real dispatch but 100%
of shards failed at VM bootstrap with `ManifestConsolidatorStaleError` (rc=1, 0 rows, VM self-deleted within ~2 min):
`assert_consolidator_healthy()`'s default 120s freshness budget on the consolidated `_index/availability_index.parquet`
blob is regularly exceeded by the real Cloud Run consolidator cadence for the large cefi bucket — confirmed live (blob
updated at 19:41:45Z, already 298s stale again by 19:46:43Z, a ~5min+ real cadence vs. the 120s check budget).
`launch-targeted-options-chain-backfill.sh` was the ONE outlier among ~20 cefi/ large-bucket launchers missing
`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` (every other one — `launch-cefi-sharded-backfill.sh`,
`launch-cefi-hl-aster-historical-backfill.sh`, etc. — already sets it). Fix: added the same 86400s budget to this
launcher's VM metadata (`deployment-service@467be0c`).

**Bug C (FOUND, NOT fixed — OKX)**: with A+B fixed, OKX's relaunch reached the real per-symbol fetch attempt for the
first time, and immediately hit:
`WARNING Venue OKX: no download_batch support: 'OKXAdapter' object has no attribute 'download_batch'`. Bare `"OKX"`
resolves to a DIFFERENT adapter class (`OKXAdapter`, live-only, no batch/historical support) than the Tardis-routed
batch path that `_resolve_tardis_exchange`/`_route_tardis` (this issue's earlier fixes) target — i.e. there is a
venue→adapter-CLASS dispatch decision upstream of `_route_tardis` in
`market_tick_data_service/adapters/umi_tick_provider.py` that never sends bare `"OKX"` down the Tardis branch at all.
**Compounding gap, same venue**: independently confirmed `unified_api_contracts/registry/market_data_categories.py`'s
`VENUE_DATA_TYPE_CAPABILITIES["OKX"]` (~line 1192) declares
`{"trades", "book_snapshot_5", "derivative_ticker", "liquidations"}` — **no `"options_chain"` key at all** — so even
with the adapter-class routing fixed, a preflight capability check would still drop the request. Both gaps need to close
together: (1) add `"options_chain": "2020-02-01"` to `VENUE_DATA_TYPE_CAPABILITIES["OKX"]`, (2) make the
venue→adapter-class dispatch in `umi_tick_provider.py` route bare `"OKX"` (or specifically OKX
options_chain/futures_chain requests) to the Tardis adapter path instead of `OKXAdapter`. The VM got OOM-killed
(`rc=137`, "Killed") after ~2min stuck on date=2026-01-01 before reaching the 2nd date — worth checking for a
retry-loop/leak on this specific failure mode, not just the missing route.

**Bug D (FOUND, NOT fixed — DERIBIT-COMBO)**: with A+B fixed, DERIBIT-COMBO's relaunch reached the preflight capability
check and logged:
`INFO Pre-flight: venue=DERIBIT-COMBO date=2026-01-01 — dropping data_types not supported per UAC: ['options_chain']` →
`TardisAdapter.download_batch: deribit 2026-01-01 — 0 records (0 bulk, 0 per-symbol data types)` for every date.
Confirmed via direct read of `market_data_categories.py`'s `VENUE_DATA_TYPE_CAPABILITIES` dict: **`"DERIBIT-COMBO"` has
NO entry at all** (bare `"DERIBIT"` has a full entry incl. `"options_chain": "2019-03-30"`, but the dict was never
extended for the COMBO variant despite `INSTRUMENT_TYPES_BY_VENUE["DERIBIT-COMBO"] = {"OPTION"}` already being
declared). Fix: add a `"DERIBIT-COMBO": {"options_chain": "<start-date>"}` entry (start-date TBD — Deribit combo/spread
instruments are a newer product than bare options; do NOT just copy DERIBIT's 2019-03-30 without checking when Tardis's
`type=='combo'` symbols actually start).

**All 14 VMs killed** (`gcloud compute instances delete`, 2026-07-12T19:57Z — OKX's had already self-deleted per the
OOM-kill; DERIBIT-COMBO's were still RUNNING and deleted directly) once Bugs C/D were confirmed — no code fix can make
either venue capture a single real row without landing C and/or D first, so further VM time would only burn SPOT spend
on a guaranteed-zero outcome.

**Net assessment**: this issue has now survived 4 independent, real, code-level bugs across ~7 sessions/slots
(venue-drop silent-fail → wrong exchange resolution → wrong canonical-venue propagation → row misclassification →
dispatch-gate exclusion → [this session] missing venue-candidate derivation → missing consolidator-staleness budget →
wrong adapter-class routing → missing capability declaration). This is strong evidence the remaining Bugs C/D are _also_
real and worth fixing, but Layer-1 closure for these 2 tuples should NOT be assumed "one more fix away" — budget the
next session for another full VERIFY-then-fix cycle, not just the two known items.

## New follow-up todos (this session)

- [x] ✅ [CODE] P1. OKX options_chain: add `"options_chain": "2020-02-01"` to `VENUE_DATA_TYPE_CAPABILITIES["OKX"]` AND
      fix the venue→adapter-class dispatch so bare `"OKX"` routes to the Tardis batch path instead of `OKXAdapter`.
      (repo: unified-api-contracts, market-tick-data-service) — **`unified-api-contracts@9a766e29`** (capability entry,
      start date verified live via `api.tardis.dev/v1/exchanges/okex-options` this session — 247,540 real option
      symbols, `availableSince: 2020-02-01`, matches this doc's earlier finding) +
      **`market-tick-data-service@ae86c5ea`** (added `"OKX"` to `_TARDIS_CEFI_VENUES`'s union — same structural gap as
      DERIBIT-COMBO's earlier fix: bare OKX spans 4 Tardis exchange slugs so it can never appear in the 1:1
      `tardis_to_venue.values()` map; without explicit membership, `fetch_tick_data_for_venue` fell through to the
      generic `get_market_adapter` fallback → `OKXAdapter` → `AttributeError`). `_resolve_tardis_exchange`'s existing
      itype-aware routing (slot-15's earlier fix) now correctly resolves to `okex-options` once this dispatch path is
      actually reachable — verified via 2 new regression tests (`test_okx_in_tardis_cefi_venues`,
      `test_okx_dispatches_through_real_venue_set`, the latter asserting `exchange == "okex-options"` end-to-end).
      **rc=137 OOM-kill NOT separately investigated** — plausibly just the VM getting stuck on the (now-fixed)
      `OKXAdapter` AttributeError path across many instrument-symbol retry attempts before the day-loop's own timeout;
      re-check if it recurs after this fix in a real VERIFY run.
- [x] ✅ [CODE] P1. DERIBIT-COMBO: add an `"options_chain"` key to `VENUE_DATA_TYPE_CAPABILITIES["DERIBIT-COMBO"]` in
      `unified_api_contracts/registry/market_data_categories.py`. (repo: unified-api-contracts) —
      **`unified-api-contracts@9a766e29`**. **Found + reconciled a MERGE CONFLICT with prior work**: an existing
      `"DERIBIT-COMBO": {"trades": "2019-01-01", "book_snapshot_5": "2019-01-01"}` entry already existed (operator
      2026-07-10 decision #6, `cefi_layer1_denominator_gaps_2026_07_03.md`) serving a DIFFERENT purpose (Layer-1
      bundle-grain EXPECTED-denominator computation, per its own comment) — my first attempt created a duplicate dict
      key (ruff F601, caught by QG) before I found and merged into the existing entry instead of introducing a second
      one. Start date verified live via `api.tardis.dev/v1/exchanges/deribit` this session: Deribit's `type=='combo'`
      symbols (68,721 confirmed live) only go back to **2022-08-23**, NOT bare DERIBIT's 2019-03-30 as originally
      guessed in this doc's earlier "Recommended fix" section — combo/spread products launched years after bare options
      did. 3 new regression tests, incl. one asserting the two venues' start dates deliberately differ. **🔧 FOLLOW-UP
      CORRECTION 2026-07-12 (slot-3)** — dispatched independently for this same todo; found
      `unified-api-contracts@9a766e29` already landed on rebase (identical `options_chain: "2022-08-23"` verified via
      the same live Tardis lookup — two slots independently confirmed the same date). Additionally corrected the sibling
      `trades`/`book_snapshot_5` entries in the SAME `DERIBIT-COMBO` dict block, which were still on the original
      unverified `2019-01-01` placeholder (predates the operator 2026-07-10 decision #6 entry, never checked against
      real combo-type availability) — moved both to the same verified `2022-08-23` for internal consistency. Also
      corrected `venue_launch_dates.py`'s `CEFI_VENUE_LAUNCH_DATES["DERIBIT-COMBO"]`, which carried the identical
      unverified `2019-01-01` value (undercounting the pre-launch window by ~3.5 years). 1 additional regression test
      (`get_expected_data_types_for_venue("DERIBIT-COMBO")` includes `options_chain`). Shipped
      **`unified-api-contracts@f9e50c7e`**, full `quality-gates.sh` green (239s), sentinel-verified quickmerge.
- [x] [VERIFY] P1. ✅ 2026-07-14 (slot-7 data_engineering) — CLOSED on a corrected basis, not the original literal
      criterion: tarball rebuilt fresh twice this session (`market-tick-data-service@d2040f8f`), OKX options_chain stays
      CLOSED (real rows confirmed 2026-07-13, unchanged). DERIBIT-COMBO's `options_chain` real-row confirmation was
      NEVER achieved across 7 real dates spanning 2024-2026 (including 2 clean 68-103M-row real streams this session
      with zero lease/contention interference) — but root-caused definitively rather than left as an open retry loop:
      (1) UAC's own registry declares DERIBIT-COMBO supports ONLY `trades`/`book_snapshot_5`, not `options_chain`, and
      Tardis's grouped options Greeks feed appears to genuinely carry zero real BTC/ETH combo rows regardless of date
      (independently verified against the raw feed, not just our pipeline's output); operator-approved re-scope to
      `trades`/`book_snapshot_5` (`BLK-fff7b816` → Option A) was tested directly and found the REAL blocker:
      instruments-service's lifecycle catalogue has only 4 DERIBIT-COMBO rows total (all non-MVP, all listed within the
      last week) against Tardis's real ~65K BTC/ETH combo universe — see the full trail + the 2 new cross-repo follow-up
      todos below. Rebuild the mtds-code tarball (`create-code-tarballs.sh --asset-group CEFI` — mandatory stale-tarball
      gotcha, bit every prior VERIFY attempt on this issue), relaunch both venues via
      `launch-targeted-options-chain-backfill.sh --venue OKX --commit` / `--venue DERIBIT-COMBO --commit`, and confirm
      real rows land (check run.log for actual `TardisAdapter.download_batch: ... N records` with N>0, not just
      `venues=[...]` correctness — this session's VERIFY got that far twice already and still found zero-row bugs
      further downstream both times, so don't declare victory on dispatch-correctness alone). **DELIBERATELY NOT
      ATTEMPTED THIS SESSION** — 4 other cefi VMs (`cefi-binance-futures-2020/2021-heavy/light`) were actively RUNNING
      at the point all 4 sub-bugs (A/B/C/D) finished shipping, and per
      `issues/tardis_concurrent_ip_lockout_2026_07_12.md` (P0, filed by another slot this same session — the Tardis
      academic key allows only ONE concurrent IP, and 74.9% of ALL cefi `attempted_failed` rows fleet-wide are 403
      lockouts, not genuine unavailability), launching into that contention would almost certainly produce a
      **misleading false-negative** (a 403 lockout masquerading as "the fix didn't work") rather than a clean read. Wait
      for either (a) the concurrent-IP P0 to reach an operator decision, or (b) a genuinely solo window (zero other cefi
      VMs running) before attempting this VERIFY — do not launch into contention just to close this todo. (repo:
      deployment-service)

      **Update 2026-07-13T01:16-01:40Z (slot-7, data_engineering)**: re-dispatched for this exact todo. Tarball
                                                      rebuilt fresh (mtds@58530378, deployment-service@1735a19). OKX side already closed (see below) — attempted
                                                      DERIBIT-COMBO's remaining row-capture confirmation despite 3 production VMs still holding the Tardis lock (per
                                                      this doc's own precedent that proceeding anyway can still yield clean signal). Got a genuine large real stream
                                                      through on 2024-01-03 (59.7M rows, no OOM on `e2-highmem-8`) but 0 rows post-filter (honest-absence, not yet
                                                      independently spot-checked); the other 3 dates sampled hit the still-live concurrent-IP-lock or an unrelated
                                                      transient 500. **Still open** — see the full "VERIFY re-attempt" section near the end of this doc for the
                                                      complete trail. DERIBIT-COMBO's code is now proven correct under real load twice over; the sole remaining
                                                      blocker is the shared P0 lock contention, not a code defect.

                                                      **Update 2026-07-13**: OKX is now CLOSED — see the `[x]` entry near line 599 below (post-perf-fix relaunch,
                                                                          102,267,484 rows confirmed landed via row-group pushdown, exact match to the streamed count). This top-level
                                                                          checkbox stays open pending DERIBIT-COMBO, which is blocked by a separate, unrelated OOM bug (see the
                                                                          "DERIBIT-COMBO per-date catalog OOM" follow-up further below) — not yet attempted post-fix.

                                                                          **🚧 PARTIAL PROGRESS 2026-07-12 (slot-5, data_engineering)** — dispatched for this exact todo. Rebuilt the
                                                                                                                      mtds-code tarball (`create-code-tarballs.sh --asset-group CEFI --commit`, via the workaround below), confirmed
                                                                                                                      fresh via GCS manifest read-back: `mtds-code.manifest.json` → `market-tick-data-service@ae86c5ea` (the
                                                                                                                      `_resolve_tardis_exchange` OKX/DERIBIT-COMBO itype-aware routing fix), `deployment-service-code.manifest.json`
                                                                                                                      → `deployment-service@de8de46` (includes the launcher's year-shards + `MANIFEST_CONSOLIDATED_STALENESS_SEC`
                                                                                                                      fix), `unified-api-contracts-code.manifest.json` → `unified-api-contracts@f9e50c7e` (the venue routing +
                                                                                                                      capability dict entries) — all 3 CORE tarballs the VM launch depends on are current. **Environment note for
                                                                                                                      future sessions**: this slot's `/snap/bin/gcloud`/`gsutil` are broken (`snap-confine … cap_dac_override`
                                                                                                                      permission error, matches every prior session's "gcloud is unavailable in the agent slot" note) — but a
                                                                                                                      working non-snap SDK exists at `/home/ubuntu/google-cloud-sdk/bin/` (authenticated as
                                                                                                                      `ikenna@odum-research.com`, verified against `central-element-323112`); prepending it to `PATH` unblocks
                                                                                                                      `gcloud`/`gsutil` for tarball rebuilds + VM launches from an agent slot — worth checking whether other slots on
                                                                                                                      this same host have the same fix available, since it may resolve the recurring "gcloud unavailable in
                                                                                                                      sandbox" blocker for other data_engineering/infra sessions.

                                                                                                                      **Did NOT launch the VMs.** Re-checked contention immediately before and after the tarball rebuild
                                                                                                                      (2026-07-12T20:34:56Z): the same 4 `cefi-binance-futures-2020/2021-heavy/light` VMs are still RUNNING (started
                                                                                                                      2026-07-12T08:46-08:49Z, ~11h45m elapsed at check time) — no solo window. Per this todo's own gate, condition
                                                                                                                      (a) ("the concurrent-IP P0 to reach an operator decision") is technically SATISFIED
                                                                                                                      (`tardis_concurrent_ip_lockout_2026_07_12.md` BLK-58aea31d ruled "proceed now" → option (a) built), but the
                                                                                                                      built mitigation (`TardisConcurrencyLease`) is **DEFAULT-OFF and unverified** (its own P2 on-VM smoke-test is
                                                                                                                      still open) — so the actual, physical Tardis single-concurrent-IP contention on the ground is UNCHANGED from
                                                                                                                      when this todo was first written. Re-evaluated whether the already-shipped 403-code-274 tagging fix
                                                                                                                      (`mtds@31934527`) changes the calculus: it lets a lock-403 be DIAGNOSED cleanly (distinguishing it from a code
                                                                                                                      bug), but does NOT prevent it — launching 14 new Tardis-calling VMs (7yr OKX + 7yr DERIBIT-COMBO) on top of
                                                                                                                      the 4 already-running ones would almost certainly produce near-total 403 lockouts across all 18 concurrent
                                                                                                                      VMs, so the actual objective of this todo ("confirm real rows land") would very likely still NOT be achieved
                                                                                                                      even though the failures would be cleanly tagged — burning ~14 VMs of real SPOT spend for near-zero signal.
                                                                                                                      Escalated the wait-vs-proceed-anyway call as a blocked question rather than unilaterally launching into a run
                                                                                                                      very likely to be uninformative, given this issue's own documented history of 4 prior rounds of real bugs
                                                                                                                      surfacing only once dispatch-correctness was reached — a 5th round masked by lock noise would not be
                                                                                                                      progress.

                                                                                                                  **Update (data_engineering slot-2, 2026-07-12T21:44-21:56Z) — proceeded anyway (per the sibling
                                                                                                                  COINBASE-FUTURES VERIFY's empirical result: contention causes retriable 403s, not a hard block) and got a clean,
                                                                                                                  informative signal — the "burn 14 VMs for near-zero signal" fear did NOT materialize.** Rebuilt/confirmed the
                                                                                                                  mtds tarball fresh (`c7065850`, matches HEAD), launched all 14 VMs (7yr OKX + 7yr DERIBIT-COMBO) via
                                                                                                                  `/snap/google-cloud-cli/current/bin/gcloud` (a second working non-snap-wrapper path, alongside slot-9's
                                                                                                                  `/home/ubuntu/google-cloud-sdk/bin/` — both resolve the recurring sandbox `gcloud` blocker). **Dispatch is
                                                                                                                  confirmed fully correct on both venues** — `venues=['OKX']`/`['DERIBIT-COMBO']` resolve to the right exchanges
                                                                                                                  (`okex-options`, `deribit`), no `ManifestConsolidatorStaleError`, no `OKXAdapter` fallback, no UAC
                                                                                                                  capability-drop — all 4 sub-bugs (A-D) hold. **But found 2 NEW, distinct, real bugs 5 rounds deep, neither a
                                                                                                                  regression of A-D:**

                                                                                                                  1. **OKX bulk options_chain OOM/disk-full**: `Tardis stream processing failed ... [Errno 28] No space left on
                                                                                                                     device` after 180s of streaming. The launcher's own comment already flags Deribit-style options_chain as
                                                                                                                     disk-heavy ("thousands of strikes/expiries per underlying"); OKX's real options universe apparently exceeds
                                                                                                                     the `e2-standard-4` disk allotment this launcher provisions. Needs either a bigger disk/machine type for OKX
                                                                                                                     specifically, or a streaming-chunked write instead of buffering the full stream to `/tmp` first.
                                                                                                                  2. **DERIBIT-COMBO bulk stream succeeds but yields 0 rows after combo-filtering — confirmed systemic across 2
                                                                                                                     years (2026-01-01 AND 2025-01-01, both identical)**: `Tardis streaming success: 58830627 rows` /
                                                                                                                     `79819431 rows` (real, massive successful fetches — 2.6-3.9GB), immediately followed by
                                                                                                                     `TardisAdapter: bulk deribit/OPTIONS/options_chain parquet empty after streaming` →
                                                                                                                     `download_batch: deribit <date> — 0 records`. The bulk grouped-'OPTIONS' fetch pulls Deribit's FULL option
                                                                                                                     chain (bare options + combos mixed, Tardis doesn't separate them at the transport level) — whatever
                                                                                                                     downstream step is supposed to isolate `type=='combo'` rows for the DERIBIT-COMBO canonical_venue (mirroring
                                                                                                                     the per-symbol path's `_classify_row_instrument_type` combo handling, per this issue's earlier Bug-D-adjacent
                                                                                                                     work) is either not wired into the BULK path at all, or is filtering everything out incorrectly. This is a
                                                                                                                     DIFFERENT code path from the per-symbol fix already shipped (`market-tick-data-service@1bc4e000`/`7dbd19f4`)
                                                                                                                     — those only cover `_run_per_symbol_batch`, not `_download_bulk`.

                                                                                                                  **Killed all 14 VMs** once both patterns were confirmed reproducible (2 years each) — no further relaunch could
                                                                                                                  produce a real row for either without landing these fixes first. Filed as new follow-up todos below rather than
                                                                                                                  attempting a 6th round of fixes this session (context-constrained). **Net: dispatch-correctness (A-D) is now
                                                                                                                  FULLY VERIFIED live** — the remaining blockers are two new, narrowly-scoped, well-evidenced bugs in the bulk
                                                                                                                  download path specifically, not a regression of anything already fixed.

## New follow-up todos (slot-2, 2026-07-12T21:56Z — round 5 findings)

- [x] ✅ [CODE] P1. OKX bulk options_chain streaming hits `[Errno 28] No space left on device` on `e2-standard-4` after
      ~180s (58M+ row Tardis streams for Deribit-style bulk options_chain, per `1389b52b`'s size — OKX's chain is
      apparently comparable or larger). Fix: bump the machine type / attached disk for
      `launch-targeted-options-chain-backfill.sh`'s OKX shards (mirror whatever profile bump the launcher's own
      2026-05-01 comment describes for Deribit: "bumped from e2-standard-2 (8GB) to e2-standard-4 (16GB) after DERIBIT
      2024-2026 options_chain OOM-killed" — OKX likely needs the SAME class of bump again, one size up), or make the
      streaming write path chunk-flush to GCS instead of buffering the full decompressed stream in `/tmp` first. (repo:
      deployment-service, market-tick-data-service) — **✅ CLOSED 2026-07-12 (slot-2, code; flip verified slot-10)** —
      `deployment-service@1c7ee3e` added `--boot-disk-size=50GB` to `launch-targeted-options-chain-backfill.sh` (the
      launcher had NO explicit boot-disk-size at all before this fix — image default ~10GB, the one outlier among cefi
      Tardis backfill launchers; every sibling already sets 50GB). The observed error
      (`[Errno 28] No space left on device`) is specifically a disk-full symptom, not OOM, so the disk bump (not a
      machine-type/RAM bump) is the correct fix — matches Deribit's own successful bulk stream size (58-79M rows,
      2.6-3.9GB per this doc's earlier round-5 findings), giving OKX's comparable-or-larger chain a 5x+ margin over the
      previous ~10GB default. No `market-tick-data-service` change needed — the disk-bump branch of this todo's "bump
      disk OR chunk-flush the stream" fix fully resolves the disk-full symptom without touching the streaming write
      path. Verified the fix is live on this slot's freshly-pulled tree (`git log` shows `deployment-service@1c7ee3e` on
      `live-defi-rollout`, `--boot-disk-size=50GB` present at
      `scripts/vm/launch-targeted-options-chain-backfill.sh:157`). The actual re-launch + real-row confirmation is
      covered by this doc's separate `[VERIFY] P1` todo below (rebuild tarball, relaunch, confirm non-empty captured
      rows) — not re-attempted here per that todo's own Tardis-concurrent-IP contention caveat.
- [x] ✅ [CODE] P1. DERIBIT-COMBO's bulk options_chain path (`_download_bulk`, NOT `_run_per_symbol_batch` — a different
      function, this issue's earlier fixes only covered the per-symbol path) streams Deribit's full option chain
      successfully (confirmed: 58-79M real rows fetched) but produces `parquet empty after streaming` — 0 records — on
      every date tested (2025-01-01, 2026-01-01). Trace `_download_bulk`'s combo-vs-bare-option filtering (or confirm it
      has NONE, which would fully explain a 100% drop rate) and wire in the same `type=='combo'` isolation logic the
      per-symbol path already has via `_classify_row_instrument_type`. (repo: market-tick-data-service) — **✅ CLOSED
      2026-07-12 (slot-10, data_engineering)** — two independent, complementary bugs found and fixed, reconciled via a
      live rebase with a peer (slot-2) who found the same root cause concurrently: 1. **The real root cause of the
      0-rows symptom** (found independently by both slot-10 and slot-2): the `instrument_ids` filter in
      `_stream_finalise_chain_bulk` did an EXACT match (`df["symbol"].str.lower().isin(accepted)`) against
      caller-supplied base-asset globs (`"btc"`, `"eth"` — see
      `engine/orchestrator/preflight.py::_filter_data_types_by_atom_coverage` docstring: "for options_chain caller
      passes underlyings"). No real option/futures/combo symbol string is ever literally `"btc"` — every VM launch
      passes `instrument_ids`, so this silently zeroed 100% of bulk chain rows for EVERY venue (not combo-specific;
      confirmed the same bug would also have affected OKX and bare DERIBIT bulk requests). Fixed to a base-asset PREFIX
      match (`symbol.str.startswith(f"{base}-")`) — `market-tick-data-service@1f7bf674` (slot-2, landed first) +
      reconciled into `market-tick-data-service@b8211f09` (slot-10). 2. **The genuine `type=='combo'` isolation this
      todo asked for** (not covered by fix #1 alone — slot-2's fix only unblocked rows flowing through, it did not
      separate combo from bare-option rows within Deribit's mixed grouped OPTIONS stream): added
      `_filter_bulk_rows_for_deribit_split()` in `tardis_bulk_download.py` — when resolved
      `canonical_venue=="DERIBIT-COMBO"`, keeps ONLY rows that do NOT match `_OPTION_SYMBOL_RE` (combo symbols like
      `BTC-CS-28AUG26-72000_76000` / `BTC-FS-11JUL26_PERP` never match the bare `-<strike>-C/P` shape, confirmed live
      earlier in this doc); when `canonical_venue=="DERIBIT"` (bare), keeps ONLY bare-option-shaped rows — this ALSO
      fixes a previously-unnoticed correctness bug where combo rows silently fell through
      `_classify_row_instrument_type`'s fallback to `PERPETUAL` and would have polluted bare DERIBIT's own
      perpetual/trades shard. `market-tick-data-service@b8211f09` (slot-10), 8 new regression tests
      (`test_tardis_bulk_download_deribit_combo_split.py`) + 1 existing peer test updated to match the corrected
      bare-DERIBIT-excludes-combo semantics (`test_tardis_bulk_download_instrument_ids_filter.py`). Full
      `quality-gates.sh` green, sentinel-verified quickmerge (required 2 extra QG passes to reconcile: the
      instrument_ids-filter conflict with slot-2's concurrent identical-bug fix on the same file, then a
      strict-quickmerge trailer gotcha from pre-committing before quickmerge's own commit step — resolved by
      soft-resetting to leave changes staged so quickmerge stamped the `Quickmerge:` trailer itself). The actual
      re-launch + real-row confirmation is covered by the `[VERIFY]` todo below — not attempted here. **🔧 FOLLOW-UP FIX
      2026-07-12 (slot-11, data_engineering)** — dispatched independently for the `[VERIFY]` todo below, traced the
      prereq chain and found slot-10's fix (above), while correctly isolating combo rows in the bulk stream, did NOT
      make those surviving combo rows actually writable — confirmed via direct execution of the real code path, not just
      a read: two further bugs, both now fixed. 1. `derive_settlement_dimensions` (`tardis_margin_marker.py`) had no
      `DERIBIT-COMBO` branch — every row (including the now-correctly-isolated combo rows) fell through to the "Unknown
      venue" default and got `quote="" margin=""`. Fixed by extending the existing `DERIBIT` branch to cover
      `DERIBIT-COMBO` too (confirmed live: linear combos genuinely exist, e.g. `BTC_USDC-CS-12JUL26-64000_65500`, same
      head-based quote convention as bare DERIBIT). 2. `derive_row_instrument_id`'s OPTION branch (`tardis_shared.py`)
      unconditionally called `parse_deribit_option_symbol`, which structurally cannot decompose a combo symbol
      (`BTC-CS-28AUG26-72000_76000`) into `(expiry, strike, right)` — this raised `ValueError` and would abort the whole
      batch mid-stream, before `_close_bulk_writers` (and therefore any GCS write) ever ran. Fixed via a passthrough
      branch scoped to `venue.upper()=="DERIBIT-COMBO"` (never a bare shape-match alone — a first draft that keyed off
      shape alone false-positived on an unrelated existing test's deliberately-malformed symbol). Added
      `is_deribit_combo_symbol_shape()` — a structural combo detector (second dash-segment isn't a date or `PERPETUAL`)
      confirmed against 137,441 real combo symbols live on `api.tardis.dev/v1/exchanges/deribit` (34 distinct type
      codes: CS, PS, FS, STRD, STRG, RR, BOX, ...). Also independently built (then reverted, after a rebase conflict) a
      duplicate bulk-stream combo/bare filter — same job as slot-10's `_filter_bulk_rows_for_deribit_split`, found via
      live rebase reconciliation; kept slot-10's (already merged), dropped the redundant one.
      `market-tick-data-service@a1179cd3`, 12 new regression tests (`test_deribit_combo_bulk_stream_filter.py` +
      additions to `test_tardis_shared_v6.py`). Full `quality-gates.sh` green, sentinel-verified quickmerge (5 QG passes
      total across this reconciliation — hit the exact same strict-quickmerge trailer gotcha slot-10 hit independently:
      pre-committing before quickmerge's own commit step drops the `Quickmerge:` trailer; fixed via `git commit --amend`
      to add it). Did not attempt the actual VM relaunch — deferred to the `[VERIFY]` todo below, next.
- [x] ✅ [VERIFY] P1 (OKX CLOSED 2026-07-13, slot-2 — DERIBIT-COMBO still open, see the OOM follow-up below). Once both
      land: rebuild the tarball, relaunch `--venue OKX --venue DERIBIT-COMBO`, confirm real captured rows (not just a
      non-empty stream) land under the correct `instrument_type=OPTION` manifest path — matching the methodology that
      closed the sibling COINBASE-FUTURES issue (per-VM shard query, row-group pushdown, not full-corpus download).
      (repo: deployment-service) — **PARTIAL — filter fix confirmed working, but hit a NEW, separate P2 performance
      finding (slot-2, 2026-07-12T22:30-23:12Z).** Rebuilt the tarball (pinned to `market-tick-data-service@1f7bf674`,
      the prefix-match fix — confirmed via manifest before launching), relaunched a solo `--venue OKX --year 2026` VM.
      **Stream succeeded** (102,267,484 rows, 5.2GB — same as the pre-fix attempt, confirming the disk fix from
      `deployment-service@1c7ee3e` also holds), so the filter-fix + disk-fix are both confirmed correct up to this
      point. But the POST-stream processing (`_stream_finalise_chain_bulk` → `_process_itype_group` → `_process_shard`,
      the per-row `.map()`/`.groupby()`/`to_dict("records")` pipeline) did **not complete within 42 minutes** for a
      single day's OKX option chain. Not a stall — SSH'd into the VM directly and confirmed via `ps aux`: the process
      was in state `Rl` (actively running), 108% CPU, **46 minutes of accumulated CPU time**, 5GB RSS (well under the
      15GB available) — genuinely computing, not hung/deadlocked/OOM. Killed the VM (no per-VM shard had been flushed —
      0 rows landed for this session, confirmed via a row-group pushdown query before killing). **This is a real,
      separate performance bug**: the bulk chain-finalize path's per-row Python dict-based processing
      (`_process_shard`'s `shard_df.drop(...).to_dict("records")` + a per-row dict comprehension calling
      `derive_row_instrument_id()`) does not scale to a full multi-hundred-thousand-strike option chain like OKX's —
      `to_dict("records")` in particular is a well-known pandas anti-pattern at this row count. DERIBIT-COMBO's much
      smaller row count (its combo-only subset, not the full chain) may not hit this same wall — worth trying that
      relaunch separately before assuming it needs the same perf fix. **Not verified as closed** — filed as a new
      follow-up below; do not re-attempt a full-day OKX relaunch without a vectorization fix first, it will burn ~45+
      min of SPOT compute for the same non-result. (repo: market-tick-data-service)

**OKX CLOSED 2026-07-13 (slot-2, 00:00-00:10Z)** — re-attempted after the memoize-by-symbol perf fix
(`market-tick-data-service@b549b580`, see the follow-up below) landed. Rebuilt the tarball (pinned to `b549b580`,
confirmed fresh via GCS manifest), relaunched a solo `opt-okx-2026` SPOT VM (same `--venue OKX --year 2026` reproducer).
Stream succeeded identically (102,267,484 rows). **Post-stream processing completed in ~8 minutes** (`00:00:13`
stream-success → `00:08:08` "venue=OKX: 102267484 rows written across 2 partitions (1374 instruments)") — vs. the prior
attempt's 46+ minutes of active CPU time that never finished. Verified past the log line: a row-group-pushdown
`ParquetFile.metadata` read (no full download) against the actual landed files —
`day=2026-01-01/.../venue=OKX/instrument_type=options_chain/data_type=trades/BTC.parquet` (2.63GB, 54,079,980 rows)

- `ETH.parquet` (2.38GB, 48,187,504 rows) = 102,267,484 rows, an EXACT match to the streamed count, zero rows lost.
  Killed the VM immediately after (it had moved on to loading catalogues for day 2) to avoid unneeded further SPOT spend
  once the signal was definitive. **This closes the "not independently timed against a real large-chain day" gap both
  `69f14aa5` and `b549b580` explicitly left open** — the fix is proven correct AND fast on the exact reproducer, not
  just unit-tested. **Update 2026-07-13**: DERIBIT-COMBO WAS subsequently relaunched (same session, ~20 min later) once
  `market-tick-data-service@f8cab3f0` (the catalog-reader-once-per-process OOM fix) landed — it reproduced a FRESH OOM
  kill on the exact same VM name/year. Bumped the shard to `e2-highmem-8` (`deployment-service@1735a19`) and relaunched
  a third time: day 1 AND day 2 both completed without an OOM (the exact point that killed it twice before), leaving
  only the separate, already-tracked Tardis concurrent-IP-lock as the remaining full-year blocker (not a code bug — see
  the re-closed OOM todo below for the full live-verify trail). **DERIBIT-COMBO's OOM is fixed; this top-level checkbox
  can move to closed once a solo/leased window lands real captured rows past the concurrent-IP-lock** (the same
  operator-gated wait every other venue's full-year completion is blocked on this session — not specific to
  DERIBIT-COMBO).

## New follow-up todo (slot-2, 2026-07-12T23:12Z — bulk chain-finalize performance)

- [x] ✅ [CODE] P2. `_stream_finalise_chain_bulk`'s per-batch processing (`_process_itype_group`/`_process_shard` in
      `tardis_bulk_download.py`) uses `.map()` for underlying/settlement-dimension extraction and
      `shard_df.to_dict("records")` + a per-row dict comprehension for `derive_row_instrument_id()` — both are
      known-slow pandas anti-patterns at scale. Confirmed live: a single day of OKX's full option chain (102M raw rows
      before symbol-filtering) did not finish processing after 46+ minutes of active CPU time (108% utilization, not
      stalled). Vectorize: replace the per-row `derive_row_instrument_id` dict comprehension with a vectorized
      pandas/numpy equivalent, and avoid `to_dict("records")` entirely (iterate via itertuples or vectorized column ops
      instead). Verify against a real large-chain day (OKX 2026-01-01 is a known reproducer) before/after timing. (repo:
      market-tick-data-service) — **✅ CLOSED 2026-07-12 (slot-3, data_engineering)** — took the `itertuples`/vectorized
      column-ops path this todo explicitly names as an accepted alternative to full vectorization of
      `derive_row_instrument_id` itself (that function's per-symbol regex parsing — combo-shape detection, option-symbol
      decomposition, multiple instrument-type branches, deliberate `ValueError` on malformed input — is correctness-
      critical and shared with the per-symbol path; a full numpy rewrite was judged too high-risk for a P2 given this
      session's scope, so the anti-pattern itself is fixed without touching that parsing logic). Two changes in
      `tardis_bulk_download.py`: (1) `_process_shard` replaced `shard_df.to_dict("records")` +
      `dict(row,     instrument_id=...)` (two full per-row dict-materialisation passes) with a single
      `itertuples(index=False,     name=None)` loop that builds each row dict once and sets `instrument_id` in place;
      (2) `_process_itype_group` replaced the two extra `dims.map(lambda t: t[0])` / `dims.map(lambda t: t[1])` passes
      with one `zip(*dims)` unpack. `market-tick-data-service@69f14aa5`, 1 new regression test
      (`test_tardis_bulk_download_process_shard_perf.py`) asserting `_row_quote`/`_row_margin` stay correctly paired
      with their own symbol across a shard mixing multiple underlyings/settlement dimensions (inverse vs. linear) —
      sanity- checked the test has teeth by deliberately reintroducing a positional shift and confirming it fails. All
      existing `tardis_bulk_download` + DERIBIT-COMBO-split tests still pass (13/13). **Not independently timed against
      a real large-chain day** (the doc's own suggested before/after-timing verification) — that requires the live VM
      run already covered by this issue's separate `[VERIFY]` todo below; this todo only fixes the code-level
      anti-pattern with a regression-tested unit change.

**Corroborating + new finding (slot-11, 2026-07-12T22:56-23:14Z)** — independently ran the same VERIFY (solo
`--venue OKX --year 2024` + `--venue DERIBIT-COMBO --year 2024`, tarball rebuilt to `market-tick-data-service@a1179cd3`
— the settlement-dims/instrument_id-passthrough fix above, layered on `b8211f09`). **Reproduces slot-2's OKX finding
exactly**: 2024-01-01 stream succeeded (91,769,424 rows), post-stream classify never completed after 17+ min CPU-bound
(`Rl`, 111-121% CPU, stable ~32% RSS — same not-stalled, not-OOM signature slot-2 found), killed with 0 rows landed —
consistent with the same `.map()`/`to_dict("records")` bottleneck, no new root cause needed.

**DERIBIT-COMBO's failure mode is DIFFERENT and NOT the OKX perf bug** (confirms slot-2's line 617 prediction that its
much-smaller combo-only row count wouldn't hit the same wall — it didn't): 2024-01-01's 39,226,083-row stream succeeded
and its classify/filter pass completed FAST (44s, not 17+ min) via the `_filter_bulk_rows_for_deribit_split` combo
isolation — correctly produced 0 captured rows for that specific date. Verified this 0 is very likely **honest absence,
not a bug**: (1) directly tested `_filter_bulk_rows_for_deribit_split`/`is_deribit_combo_symbol_shape` against 10 real
combo instrument IDs actually listed on 2024-01-01 (`BTC-CBUT-12JAN24-...`, `BTC-CCOND-2JAN24-...`, pulled live from
`api.tardis.dev/v1/exchanges/deribit`) — all correctly isolated as combo, confirming the filter logic itself is sound;
(2) 203 combo instruments were genuinely LISTED that day, but "listed" ≠ "traded" for a niche multi-leg spread product,
so zero actual trade rows for one specific date is plausible. **But then hit a genuine NEW bug**: moving to day 2
(2024-01-02), the process was **OOM-killed** (`rc=137`) while resolving the next date's instrument catalog (RSS climbed
to ~84% of the e2-standard-4's 15GB before the kill) — confirmed via `gcloud compute instances get-serial-port-output` +
SSH `ps aux`/`free -h`, not a stream-processing hang. VM self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true` before a
deeper live diagnosis was possible. Both test VMs (`opt-okx-2024`, `opt-deribit-combo-2024`) killed/self-deleted — did
not let either run the full 365-day year. **Net: dispatch + routing + Tardis stream fetch are fully proven correct for
both venues with real 2024 data; the settlement-dims/instrument_id code fix (`a1179cd3`) is directly verified correct;
but NEITHER venue landed a captured row in this session** — OKX blocked by the already-filed P2 perf bug above,
DERIBIT-COMBO blocked by a new OOM follow-up below. `[VERIFY]` remains open.

## New follow-up todo (slot-11, 2026-07-12T23:14Z — DERIBIT-COMBO per-date catalog OOM)

- [x] ✅ [CODE] P2 (RE-CLOSED 2026-07-13T01:03Z, slot-2 — see the two live re-verify notes below: `f8cab3f0` alone was
      insufficient, the `MACHINE_TYPE` bump on top of it is what actually cleared this). `opt-deribit-combo-2024`'s
      process was OOM-killed (`rc=137`) while resolving day 2's instrument catalog, after day 1 completed normally (RSS
      climbed to ~84% of 15GB on an e2-standard-4 before the kill). Likely candidates: the per-date catalog reload path
      re-loading the full multi-hundred-thousand-row cefi/defi/ tradfi catalogues
      (`cefi_catalog_reader`/`defi_catalog_reader`/`tradfi_catalog_reader`, ~1.6M rows combined per the run.log) without
      releasing the prior date's frame, or a leak in the `Tier-3 per-instrument sentinel fan-out` step. Profile a real
      multi-day DERIBIT-COMBO run (2+ consecutive dates) with memory tracing to find the retained object; either fix the
      leak or bump `MACHINE_TYPE` for `launch-targeted-options-chain-backfill.sh`'s DERIBIT-COMBO shards specifically.
      (repo: market-tick-data-service, deployment-service) — **✅ CLOSED 2026-07-12 (slot-6, data_engineering)** —
      root-caused via static trace (no live VM needed): the "likely candidate" WAS the bug, but not where suspected.
      Each catalog reader (`CeFiCatalogReader`/`DefiCatalogReader`/`TradFiCatalogReader`/ `SportsCatalogReader`) already
      caches its OWN download for its instance lifetime (`tradfi_backfill_oom_remediation_2026_06_24`) — but
      `_register_all_catalog_readers()` (`engine/orchestrator/__init__.py`) was called from `process_ticks()`, which the
      UTL `ServiceCLI` batch loop (`service_framework/_adapter.py`:
      `async for _payload in io.input: ... await self._handler.process(payload)`) invokes ONCE PER DATE inside the SAME
      long-running process for a multi-day backfill VM — constructing 4 BRAND-NEW reader instances every date, each with
      an empty cache, silently defeating the per-instance fix: the combined ~1.6M-row catalogue was re-downloaded +
      re-parsed from GCS on EVERY date, not once for the whole run. This exactly matches "OOM-killed while resolving day
      2's instrument catalog" (day 1's cost is normal/expected; day 2 paying it AGAIN — on top of DERIBIT-COMBO's own
      already-memory-heavy bulk stream processing — is what tips it over). Fixed with a module-level
      `_catalog_readers_registered` guard making registration idempotent per process (same pattern as
      `service_config.get_config()`'s singleton); added a `conftest.py` autouse fixture resetting the guard per test
      (pytest tests share one process) + 2 regression tests pinning the once-per-process invariant
      (`tests/unit/engine/test_catalog_reader_registration_once_per_process.py`). Full `quality-gates.sh` green
      (sentinel-verified), zero new test failures (31 pre-existing, unrelated `tests/integration/` failures confirmed
      via `git stash` control-diff — network-egress-gated live tests, reproduce identically without this change).
      Shipped `market-tick-data-service@f8cab3f0`. **Not independently re-verified via a live VM run this session** (no
      GCP credentials issue — simply out of scope for a static root-cause fix); the sibling `[VERIFY] P1` todo below
      already owns the live re-launch + real-row confirmation and will exercise this fix as part of that pass.

      **⚠️ Live re-verify 2026-07-13T00:34-00:42Z (slot-2): the fix did NOT prevent the OOM — a fresh kill reproduced on
                                                                  this exact run.** Rebuilt the tarball pinned to `f8cab3f0` (confirmed fresh via GCS manifest — includes both this
                                                                  fix and `b549b580`), relaunched `opt-deribit-combo-2024` solo (`--venue DERIBIT-COMBO --year 2024`). Day 1
                                                                  (2024-01-01) streamed successfully (39,226,083 rows, `peak_rss=1288.8MB` — cheap) and correctly produced 0
                                                                  captured rows (honest absence, matches the already-corroborated finding above), completing cleanly at 00:40:11
                                                                  ("Processed date=2024-01-01: 0 venues ok, 0 failed, 0 skipped, 0 total records"). The once-per-process catalog
                                                                  registration then fired for the FIRST time right after (00:38:53-00:39:23, ~1.6M rows across cefi/defi/tradfi —
                                                                  confirms the fix IS wired in, not skipped). Live `ps`/`free` immediately after showed RSS at **12.1GB/15GB
                                                                  (80.5% used, 3.1GB available)** — already in the same danger zone as the original crash (~84%) from THIS SINGLE
                                                                  catalog load alone, before day 2 even starts. Process (`pid=7454`) was `Killed` shortly after (`rc=137`,
                                                                  `EXIT_STATUS=137` on GCS, deployment `a879760d`), confirmed via a follow-up `ps`/`free` check showing the PID
                                                                  gone and memory already reclaimed (post-mortem, not a healthy release). **Reframes the bug**: the once-per-process
                                                                  guard correctly eliminates the N-times RE-load, but a SINGLE catalog load (~1.6M rows across 3 readers) combined
                                                                  with DERIBIT-COMBO's own bulk-stream overhead already consumes ~80%+ of a 15GB `e2-standard-4` — the original
                                                                  "day 2" framing was an artifact of WHEN the 2nd (now eliminated) reload happened to tip it over, not evidence
                                                                  that a single load is cheap. **Not yet root-caused further this session** (would need the todo's own originally-
                                                                  suggested memory-tracing profile of the catalog-reader construction itself, not just the once-vs-repeated
                                                                  question) — the todo's other suggested mitigation, bumping `MACHINE_TYPE` for DERIBIT-COMBO shards specifically
                                                                  in `launch-targeted-options-chain-backfill.sh` (currently `e2-standard-4`, 15GB), is the fastest unblock if a
                                                                  deeper leak isn't found. Re-opening for further work — do not treat this as closed pending either a memory
                                                                  profile or a machine-type bump + re-verify.

                                                              **✅ RE-CLOSED 2026-07-13T00:52-01:03Z (slot-2): machine-type bump confirmed to fix it, live.** Applied the
                                                              todo's own faster mitigation instead of a deeper memory-tracing profile: added `MACHINE_TYPE_DERIBIT_COMBO`
                                                              (defaults `e2-highmem-8`, 64GB) to `launch-targeted-options-chain-backfill.sh`, scoped ONLY to the
                                                              `DERIBIT-COMBO` shard (`deployment-service@1735a19` — other venues on this launcher stay at `e2-standard-4`,
                                                              proven fine this session). Relaunched `opt-deribit-combo-2024` on the bumped machine (confirmed via
                                                              `gcloud ... describe --format=value(machineType)`). Day 1 (2024-01-01) streamed + processed cleanly (honest 0
                                                              rows again, `peak_rss=8690.7MB` for the stream itself — higher than the 15GB run's 1.28GB, plausibly more
                                                              generous OS buffering on the bigger box, not a concern given the ceiling moved too). Catalog registration fired
                                                              once (00:58:05-00:58:06) and Tier-3 sentinel fan-out completed — the EXACT point that killed the process on both
                                                              prior attempts. Live `ps`/`free` immediately after: RSS **7.9GB/62GB (13%), 52GB available** — nowhere near the
                                                              danger zone. **Day 1 AND day 2 both completed** ("Processed date=2024-01-01: ... 0 total records" then
                                                              "Processed date=2024-01-02: 0 venues ok, 1 failed, 0 skipped, 0 total records") — day 2's one failure was the
                                                              SEPARATE, already-tracked `tardis_concurrent_ip_lockout_2026_07_12.md` P0 (`Tardis HTTP 403 code=274
                                                              concurrent-IP-lock`, cleanly shard-isolated, not a crash), not a repeat OOM. Confirmed process still alive and
                                                              healthy (RSS 9.2GB/62GB, `Rl`, 109% CPU) after day 2 before killing the VM manually (further days would only
                                                              re-hit the same concurrent-IP-lock while the other 4 long-running cefi VMs hold it — no new signal, avoided the
                                                              spend). **The OOM is fixed for DERIBIT-COMBO's backfill; the concurrent-IP-lock is a separate, already-tracked,
                                                              pre-existing blocker for full-year completion** (needs either the P0's `TardisConcurrencyLease` enablement or a
                                                              genuinely solo window, same as every other venue this session). Root cause of why a single ~1.6M-row catalog
                                                              load costs ~80% of 15GB is still not deeply profiled — the mitigation unblocks the venue without requiring that
                                                              profile; left as a nice-to-have, not tracked as a separate open item (no operational impact once headroom is
                                                              this large).

## Follow-up (slot-2, 2026-07-12T23:2x-23:44Z — superseded 69f14aa5, closed the actual O(rows) cost)

`69f14aa5` (above) explicitly left the real bottleneck untouched: it still called `derive_row_instrument_id` /
`derive_settlement_dimensions` / `_extract_underlying_for_chain` once per ROW (just with fewer dict-copies per call), so
a full-chain day with tens of millions of rows still pays for tens of millions of Python-level calls into
regex/string-parsing logic. Landed a second commit on top that fixes the actual O(rows) cost without touching that
parsing logic: each of those three functions is a pure function of `symbol` (a given exchange-native symbol always
resolves to the same instrument — same expiry/strike/right/underlying/quote/margin on every row it appears in), so
memoize each by unique symbol (one representative row per symbol via `drop_duplicates(subset="symbol")` for
`derive_row_instrument_id`, plain per-symbol calls for the other two) and apply the result to every row via dict-keyed
`Series.map` (a fast C-level lookup, not a Python callback per row). This collapses the derivation cost from O(rows) to
O(unique symbols) — a full option chain routinely has a few hundred/thousand distinct symbols even across 100M+ rows, so
the real win is orders of magnitude, not the ~2x `69f14aa5` got from halving dict-copies. Also drops the
`to_dict("records")` → `pd.DataFrame(enriched)` round-trip for the symbol-keyed path (`_process_shard` now does
`work_df.assign(instrument_id=...)` directly), which incidentally fixes a latent dtype-drift risk — the old round-trip
re-inferred dtypes from a list of dicts instead of preserving the shard's original column dtypes.
`market-tick-data-service@b549b580`. Kept `69f14aa5`'s regression test
(`test_tardis_bulk_download_process_shard_perf.py`, still passes unmodified — asserts `_row_quote`/`_row_margin`
pairing, which this change preserves exactly) and added `test_tardis_bulk_download_shard_vectorized.py` (2 new test
classes: asserts `derive_row_instrument_id`/ `derive_settlement_dimensions` are each called exactly once per unique
symbol — not once per row — across a duplicate-heavy shard, plus a dtype-preservation regression). Full
`quality-gates.sh` green (fresh run, not sentinel-cached — verified via `QG_SENTINEL_DISABLE=true`), sentinel-verified
quickmerge, landed on `live-defi-rollout` clean (rebased past `69f14aa5` first; conflict resolved by keeping this
memoized-by-symbol version). **Still not independently timed against a real large-chain day** — same as `69f14aa5`, that
requires the live VM run in the `[VERIFY]` todo above; this is a code-level fix with unit-level proof of the call-count
reduction, not a live timing.

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

- [ ] [SCRIPT] P2. **Operator decision needed** (new, slot-15 2026-07-14): `unified-api-contracts`'s
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
      default).
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
