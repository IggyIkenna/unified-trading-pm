---
doc_type: issue
title:
  COINBASE-FUTURES SPOT_PAIR has valid MVP-tagged catalogue symbols but ZERO manifest rows of any capture_status — not a
  catalogue-population gap, a deeper resolution/dispatch bug
summary:
  "Prior session (2026-07-12T13:15-13:35Z) diagnosed the missing (COINBASE-FUTURES, spot_pair, trades) Layer-1 tuple as
  a likely instruments-service catalogue gap (SPOT_PAIR symbols never populated) and left it unconfirmed. This session
  directly queried both the IS catalogue and the cefi tick manifest and DISPROVED that hypothesis: the catalogue has 19
  real SPOT_PAIR rows for COINBASE-FUTURES (16 with mvp=True, matching Tardis coinbase-international's live 19-symbol
  metadata), yet the cefi prd manifest has LITERALLY ZERO rows of ANY capture_status (captured/attempted_failed/
  empty_confirmed) for (venue=COINBASE-FUTURES, instrument_type=SPOT_PAIR) — not a fetch failure, a complete absence of
  any attempt, despite a VM_FORCE=true VM having run to completion the prior session with confirmed real PERPETUAL
  activity for the same venue. The real bug is upstream of symbol resolution (something scopes the batch request to
  PERPETUAL-only before _resolve_symbols/_catalogue_symbols_for_venue_date is ever reached, or those functions ARE
  reached but silently drop SPOT_PAIR) — needs a dedicated code trace, not attempted this session (time-boxed after the
  cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md thread)."
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags:
  [honest-coverage, denominator-audit, layer-1, data-correctness, cefi, coinbase-futures, spot-pair, mvp-backfill-v10]
related:
  [
    mvp_backfill_cefi_tick_v10_2026_06_27.md,
    cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md,
    ../../../codex/02-data/honest-coverage-model.md,
    ../../../codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-12
parent_epic: cefi_master
priority: P2
source:
  mvp_backfill_cefi_tick_v10_2026_06_27.md G4 re-verification, 2026-07-12T20:15-20:45Z session (data_engineering slot-2)
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

The prior session (2026-07-12T13:15-13:35Z entry in `mvp_backfill_cefi_tick_v10_2026_06_27.md`) flagged this as an
untested hypothesis: "Sub-agent traced it to a likely instruments-service catalogue gap ... Needs a direct IS catalogue
query to confirm — not attempted this session (time-boxed)." This session ran that query and two follow-ups.

**Step 1 — the catalogue query (disproves the hypothesis):**

```python
# instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet
table = pq.read_table(..., filters=[('venue','=','COINBASE-FUTURES')])
# total COINBASE-FUTURES rows: 420 — Counter({'PERPETUAL': 401, 'SPOT_PAIR': 19})
```

19 real SPOT_PAIR rows exist. Full detail
(`venue,instrument_type,raw_symbol,base_asset,mvp,available_from, available_to`):

| raw_symbol                                                       | mvp   | available_from                  |
| ---------------------------------------------------------------- | ----- | ------------------------------- |
| BTC-USDC                                                         | True  | 2024-10-31                      |
| ETH-USDC                                                         | True  | 2024-10-31                      |
| SOL-USDC                                                         | True  | 2025-11-14                      |
| XRP-USDC                                                         | True  | 2026-02-03                      |
| AAVE/ADA/AVAX/DOGE/HBAR/HYPE/LINK/LTC/PAXG/SUI/TAO/XLM-USDC (12) | True  | 2026-05-22                      |
| COSMOSDYDX-USDC                                                  | False | 2024-10-31 (expired 2026-02-04) |
| PEPE-USDC                                                        | False | 2026-05-22                      |
| USDT-USDC                                                        | False | 2026-05-22                      |

16/19 are `mvp=True` — matches Tardis's live `coinbase-international` metadata (19 real spot symbols,
`availableSince: 2026-05-22`, confirmed by the prior session). So the catalogue-population hypothesis is FALSE: the
symbols exist, are correctly typed `SPOT_PAIR`, and most are tagged `mvp=True` with real availability windows.

**Step 2 — the manifest query (the actual, more specific gap):**

```python
# market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet, row-group pushdown filter
dataset.to_table(filter=(venue=='COINBASE-FUTURES') & (instrument_type=='SPOT_PAIR'))
# rows: 0
```

**Zero rows of ANY `capture_status`** — not `captured`, not `attempted_failed`, not `empty_confirmed`. This is a
stronger, more specific finding than "missing from Layer-1": it means COINBASE-FUTURES's SPOT_PAIR symbols were never
even ATTEMPTED, despite:

- The catalogue having valid, correctly-typed, mostly-MVP-tagged symbols since this session confirmed.
- A `VM_FORCE=true` VM (`cefi-coinbase-futures-2026-heavy-20260712-121158`) having run to completion in the prior
  session with confirmed genuine Tardis activity for the SAME venue (PERPETUAL symbols, per that session's own run.log
  spot-check).
- COINBASE-FUTURES having exactly ONE Tardis exchange (`coinbase-international`) covering BOTH instrument types, so
  there is no itype-vs-exchange routing split to lose (ruling out the exact bug class that hit OKX/DERIBIT-COMBO in the
  sibling issue doc).

**Not yet traced (genuine remaining scope, not attempted this session — time-boxed):** WHY the symbol resolution path
(`market_tick_data_service/market_interface/adapters/tradfi/tardis_symbol_resolution.py::_catalogue_symbols_for_venue_date`
/ `_resolve_symbols_from_by_date_snapshot` / `_resolve_symbols`) never surfaces these 16 mvp=True SPOT_PAIR symbols for
ANY date in 2026 for a `VENUES="COINBASE-FUTURES"` batch request.

**Two UAC-declaration hypotheses CHECKED and RULED OUT this session** (both were the fastest, cheapest checks — the
exact class of gap that blocked DERIBIT-COMBO/OKX in the sibling issue doc, so worth eliminating first):

- `unified_api_contracts/registry/venue_constants.py:426` —
  `INSTRUMENT_TYPES_BY_VENUE["COINBASE-FUTURES"] = {"PERPETUAL", "SPOT_PAIR"}` — **SPOT_PAIR IS declared.** Not a
  missing-itype-declaration bug.
- `unified_api_contracts/registry/market_data_categories.py:1389` —
  `VENUE_DATA_TYPE_CAPABILITIES["COINBASE-FUTURES"] = {"trades": "2024-10-31", ...}` — **`trades` IS declared** (venue-
  level, not itype-scoped, so this check passes regardless of PERPETUAL vs SPOT_PAIR). Not a missing-capability bug.

So the bug is genuinely in the RUNTIME resolution/dispatch path, not a UAC declaration gap — both easy wins are
eliminated. Remaining candidate hypotheses, neither confirmed:

1. Something upstream of symbol resolution scopes the requested `instrument_type`(s) for a
   `VENUES="COINBASE-FUTURES" DATA_TYPES=trades` batch call to PERPETUAL only, so `_resolve_symbols` (or its callers)
   never even reach the SPOT_PAIR rows in the (correctly-populated, correctly-declared) catalogue — check whether the
   launcher/handler passes an implicit `instrument_type` filter, or whether `download_batch`'s dispatch keys off
   `_VENUE_SOURCE`/similar mappings that are PERPETUAL-specific for this venue.
2. `_resolve_symbols` IS reached with the full symbol set (401 PERPETUAL + 16-19 SPOT_PAIR) but something downstream
   partitions/filters by `instrument_type` per data_type request (e.g. a `data_type` → `instrument_type` compatibility
   check that silently excludes SPOT_PAIR for `trades` on this venue specifically) before any fetch/manifest-write
   happens.

Whoever picks this up next should trace the actual runtime call path for a `VENUES="COINBASE-FUTURES"` launch (not just
read the resolution functions in isolation, and not more UAC-declaration greps — both are now eliminated) — this
session's sibling issue doc (`cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md`) repeatedly found that static
code reading undersold the actual bug count; live VM verification (with run.log inspection at the actual dispatch point,
e.g. temporary logging around `_resolve_symbols`'s call sites) surfaced bugs a code read alone missed.

## Why it matters

Blocks 1 of the 12 remaining Layer-1 tuples for cefi G4. Lower priority (P2, not P1) than the sibling
`cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md` docs because: (a) it's a single tuple, not two; (b) the
symbols ARE correctly catalogued (no cross-repo UAC wiring gap confirmed yet, unlike DERIBIT-COMBO's genuine missing
routing entry); (c) it may turn out to be a small, single-repo fix once traced, similar in shape to Bug C/D in the
sibling doc but not yet proven.

## Recommended decision

Route to `data_engineering` — both UAC-declaration hypotheses are already ruled out (see above), so go straight to a
live VM launch + run.log inspection at the actual dispatch point (NOT static code reading alone — see the "why it
matters" note above). Once the code fix (if any) lands, launch a scoped
`ONLY="COINBASE-FUTURES:2026:heavy" VM_FORCE=true` VM and confirm real `SPOT_PAIR` rows land (any `capture_status`,
matching this doc's own diagnostic method — a manifest row-group-pushdown query, not a full 263MB download).

## Todos

- [x] ✅ [SCRIPT] P2. Check `INSTRUMENT_TYPES_BY_VENUE["COINBASE-FUTURES"]` includes `"SPOT_PAIR"` and
      `VENUE_DATA_TYPE_CAPABILITIES["COINBASE-FUTURES"]` declares `"trades"` — both checked this session, both already
      correctly declared (see "What I found" above). Not the bug; do not re-check. (repo: unified-api-contracts)
- [ ] [SCRIPT] P2. Trace why `_resolve_symbols`'s catalogue-lifecycle path never surfaces COINBASE-FUTURES's 16 mvp=True
      SPOT_PAIR symbols for a `VENUES="COINBASE-FUTURES" DATA_TYPES=trades` batch request — via a live VM launch +
      run.log inspection, not static reading alone (hypotheses 1/2 above). (repo: market-tick-data-service)
- [ ] [VERIFY] P2. Once a fix lands, launch
      `ONLY="COINBASE-FUTURES:2026:heavy" VM_FORCE=true     bash launch-cefi-sharded-backfill.sh` and confirm real
      SPOT_PAIR manifest rows land (query the manifest with a row-group-pushdown filter, not the full-download approach
      that timed out once in this session). (repo: deployment-service)
