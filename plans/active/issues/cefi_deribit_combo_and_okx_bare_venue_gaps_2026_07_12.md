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

- [ ] [SCRIPT] P2. Add `("DERIBIT-COMBO", "OPTION"): "deribit"` (or correct itype key) to
      `venue_mapping.py::venue_instrument_type_to_tardis`, filtered to Tardis `type=='combo'` symbols only (not
      duplicating bare DERIBIT's option/future/perpetual/spot capture); verify `build_instrument_catalogue.py` tags
      catalogue rows `venue=DERIBIT-COMBO`; check whether an empty resolved symbol list (pre-catalogue-tracking dates)
      still writes a manifest row or needs `deribit_combo_adapter.py`'s `EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE`
      classification to fire instead; re-run the cefi backfill for `DERIBIT-COMBO`. (repo: unified-api-contracts,
      instruments-service, market-tick-data-service). **🚧 PARTIAL PROGRESS 2026-07-12 (slot-3)** —
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
- [ ] [SCRIPT] P2. Trace `get_tardis_exchange_for_venue`'s current return value for venue="OKX" (likely `okex` or
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
      `_route_tardis` for an `options_chain` `VM_DATA_TYPES` request specifically.

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
