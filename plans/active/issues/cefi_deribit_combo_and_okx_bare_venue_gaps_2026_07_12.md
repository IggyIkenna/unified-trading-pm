---
doc_type: issue
title:
  DERIBIT-COMBO trades capture is unwired (no Tardis routing entry); bare OKX/options_chain Layer-1 tuple needs a
  live-check
summary:
  'Found 2026-07-12 while investigating the mvp_backfill_cefi_tick_v10 G4 Layer-1 gate. Two of the 15 remaining missing
  Layer-1 tuples for cefi are (DERIBIT-COMBO, options_chain, trades) and (OKX, options_chain, trades). Neither is
  fixable by a plain backfill VM launch. DERIBIT-COMBO has ZERO manifest rows of any capture_status ever (confirmed via
  instruments-service/scripts/relabel_deribit_combo_historical_to_empty_2026_06_27.py --dry-run) because
  venue_mapping.py venue_instrument_type_to_tardis has no (DERIBIT-COMBO, *) entry at all — MTDS TardisAdapter cannot
  resolve a Tardis exchange slug for it, so a launch would either silently resolve zero symbols or error before ever
  attempting a fetch. Bare "OKX" is explicitly documented in venue_constants.py:327-335 as NOT a real capture venue
  (data lands under OKX-SPOT/OKX-SWAP/OKX-FUTURES) — this looks like the same phantom-denominator class already fixed
  today for BITFINEX-FUTURES/FUTURE (unified-api-contracts@5b57c2b2), but was not verified this session.'
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
author: data_engineering (slot-2)
parent_epic: cefi_master
priority: P2
source: mvp_backfill_cefi_tick_v10_2026_06_27.md G4 re-verification, 2026-07-12T07:20-08:05Z session
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
assigned_role: data_engineering
model_tier: sonnet-doable
thinking_tier: high
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

### 2. `(OKX, options_chain, trades)` — likely a phantom denominator tuple, needs the same live-check BITFINEX-FUTURES got

- `unified_api_contracts/registry/market_data_categories.py:327-335` (comment, verbatim): "OKX is captured under
  canonical SUB-VENUE names in the platform (OKX-SPOT / OKX-SWAP / OKX-FUTURES — like BINANCE-SPOT / BINANCE-FUTURES),
  NOT the bare `OKX` token. Declaring the sub-venues here makes `is_mvp("cefi", "OKX-SPOT", …)` etc. — the bare `OKX`
  caller still resolves (`mvp_instrument_universe_gap_audit` back-compat)."
- This is the exact same shape of bug just fixed for `BITFINEX-FUTURES` (a whole-venue/itype declared in the EXPECTED
  builder without checking whether real captured data can ever land under that exact venue string). Given bare `OKX` is
  explicitly NOT where captures land, `(OKX, options_chain, trades)` is very likely never closable by backfill — but has
  NOT been independently verified this session (time-boxed; the BITFINEX-FUTURES fix consumed the session's
  live-Tardis-check budget). Needs the same treatment: trace which UAC dict is actually emitting this EXPECTED tuple for
  bare `OKX` (grep `"OKX"` across `venue_constants.py` / `market_data_categories.py` / `_mvp_scope_rules.py` for an
  `options_chain`/OPTION-itype declaration under the bare token — NOT `OKX-SPOT`/ `OKX-SWAP`/`OKX-FUTURES`), confirm via
  live Tardis metadata whether `okex`/`okex-options` (if it exists as a Tardis exchange) actually serves options data,
  then either fix the denominator (drop the phantom tuple, mirroring the BITFINEX-FUTURES precedent) or wire the correct
  sub-venue routing if OKX DOES offer options via Tardis under a different canonical venue string than the current
  EXPECTED-builder emits.

## Why it matters

Both tuples block the `mvp_backfill_cefi_tick_v10` plan's G4 gate (`denominator_complete == True` required). Neither is
fixable by the "launch a VM" playbook the rest of the plan's remaining gaps use — (1) needs real cross-repo code wiring
before any capture attempt is even possible, and (2) is very likely a denominator bug masquerading as a capture gap
(same root-cause class as the BITFINEX-FUTURES fix shipped today, `unified-api-contracts@5b57c2b2`).

## Recommended decision

- Todo 1 (DERIBIT-COMBO wiring): route to `data_engineering` — needs the venue_mapping.py routing entry + a catalogue
  tagging check, both squarely pipeline-code work. Verify via `api.tardis.dev/v1/exchanges/deribit` first (dead-simple
  curl check, ~2 min) before writing any code, in case Tardis's `deribit` exchange doesn't distinguish combo instruments
  at all (in which case this becomes ANOTHER denominator-correction case, not a wiring fix).
- Todo 2 (bare-OKX verification): route to `data_engineering` — same live-check pattern as this session's
  BITFINEX-FUTURES fix (grep the EXPECTED-emitting dict, curl the Tardis exchange metadata, fix-or-confirm).

## Todos

- [ ] [SCRIPT] P2. Curl `api.tardis.dev/v1/exchanges/deribit` and confirm whether Tardis's `deribit` exchange exposes
      combo/multi-leg instrument IDs distinct from single-leg options. If yes: add the `venue_instrument_type_to_tardis`
      routing entry (`venue_mapping.py`) + verify `build_instrument_catalogue.py` tags combo rows with
      `venue=DERIBIT-COMBO`, then re-run the cefi backfill for `DERIBIT-COMBO`. If no: file a denominator-correction fix
      instead (mirror `unified-api-contracts@5b57c2b2`). (repo: unified-api-contracts, instruments-service,
      market-tick-data-service)
- [ ] [SCRIPT] P2. Trace which UAC dict emits the bare-`OKX`/`options_chain`/`trades` Layer-1 EXPECTED tuple (NOT
      OKX-SPOT/OKX-SWAP/OKX-FUTURES); confirm via live Tardis metadata whether it is real or phantom; fix the
      denominator (mirror the BITFINEX-FUTURES precedent, `unified-api-contracts@5b57c2b2`) if phantom. (repo:
      unified-api-contracts)
