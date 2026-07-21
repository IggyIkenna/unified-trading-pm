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
status: resolved
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
resolved_by: data_engineering slot-3, 2026-07-12T21:44Z — market-tick-data-service@8be30c8c + live VM verification
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

**Two UAC-declaration hypotheses CHECKED and RULED OUT this session** (both were the fastest, cheapest checks — the
exact class of gap that blocked DERIBIT-COMBO/OKX in the sibling issue doc, so worth eliminating first):

- `unified_api_contracts/registry/venue_constants.py:426` —
  `INSTRUMENT_TYPES_BY_VENUE["COINBASE-FUTURES"] = {"PERPETUAL", "SPOT_PAIR"}` — **SPOT_PAIR IS declared.** Not a
  missing-itype-declaration bug.
- `unified_api_contracts/registry/market_data_categories.py:1389` —
  `VENUE_DATA_TYPE_CAPABILITIES["COINBASE-FUTURES"] = {"trades": "2024-10-31", ...}` — **`trades` IS declared** (venue-
  level, not itype-scoped, so this check passes regardless of PERPETUAL vs SPOT_PAIR). Not a missing-capability bug.

**Symbol resolution itself CHECKED and RULED OUT this session too** — called `_catalogue_symbols_for_venue_date`
directly (no VM needed, same GCS catalogue read as Step 1 above, run locally):

```python
>>> _catalogue_symbols_for_venue_date("COINBASE-FUTURES", "2026-06-01")
# INFO catalogue-lifecycle universe for COINBASE-FUTURES on 2026-06-01 = 284 symbols
# includes: AAVE-USDC, ADA-USDC, AVAX-USDC, BTC-USDC, DOGE-USDC, ETH-USDC, HBAR-USDC,
#           HYPE-USDC, LINK-USDC, LTC-USDC, PAXG-USDC, SOL-USDC, SUI-USDC, TAO-USDC,
#           XLM-USDC, XRP-USDC  (all 16 mvp=True SPOT_PAIR symbols, present)
```

The function returns exactly the expected 284-symbol mixed PERPETUAL+SPOT_PAIR universe, correctly including every
mvp=True SPOT_PAIR symbol. **This is a strong, direct proof the symbol-resolution layer is NOT the bug** — do not
re-trace `_catalogue_symbols_for_venue_date`/`_resolve_symbols_from_by_date_snapshot`, they work correctly.

**Also checked: `force=True`'s scope.** `_run_preflight_availability_check(state, bucket, force)` is a full no-op when
`force=True` (confirmed by reading the function — `if force: return` is its first line), and `VM_FORCE=true` metadata
correctly threads to the CLI `--force` flag (`setup-data-pipeline-vm.sh:1204/1293/1510`). So the prior session's
`VM_FORCE=true` launch genuinely DID bypass the venue-level captured-atom skip-existing check — that mechanism is not
silently failing to apply.

**So the bug is narrowed to a specific, small window: AFTER symbol resolution correctly returns all 284 symbols
(including all 16 SPOT_PAIR), and AFTER the venue-level skip-existing check is confirmed bypassed by force=True, but
BEFORE any manifest row (of any capture_status) gets written for the 16 SPOT_PAIR symbols specifically.** That window is
inside `download_batch` → the actual per-symbol fetch dispatch / Tardis bulk-vs-per-symbol branching /
`_run_per_symbol_batch` → `_emit_per_symbol_manifest`. Two candidate hypotheses for THAT narrower window, neither
confirmed:

1. A per-`instrument_type` partition/filter inside `download_batch` itself (not `_resolve_symbols`) that splits the
   284-symbol list by itype for some OTHER reason (e.g. bulk-vs-per-symbol routing, or a Deribit-style
   option/future-stripping step generalized incorrectly to this venue) and silently drops the SPOT_PAIR partition.
2. A silent exception/early-return specific to symbols whose `raw_symbol` shape doesn't match what the per-symbol fetch
   loop expects (COINBASE-FUTURES's SPOT_PAIR symbols are `XXX-USDC`, distinct in shape from its PERPETUAL symbols) —
   worth checking whether `_run_per_symbol_batch` or its Tardis-request-URL construction has any symbol-shape assumption
   that would fail closed (no manifest write, no exception surfaced) specifically for `-USDC` suffixed symbols.

Whoever picks this up next should trace `download_batch`'s actual per-symbol dispatch loop directly (temporary logging
around the itype-partition point, or a live VM run.log inspection at the `_run_per_symbol_batch`/
`_emit_per_symbol_manifest` call sites) — NOT the resolution functions in isolation (`_resolve_symbols`,
`_catalogue_symbols_for_venue_date`) and NOT more UAC-declaration greps, both already eliminated with hard evidence this
session. This session's sibling issue doc (`cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md`) repeatedly found
that static code reading undersold the actual bug count; live verification surfaced bugs a code read alone missed — the
same discipline applies here.

## Why it matters

Blocks 1 of the 12 remaining Layer-1 tuples for cefi G4. Lower priority (P2, not P1) than the sibling
`cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md` docs because: (a) it's a single tuple, not two; (b) the
symbols ARE correctly catalogued (no cross-repo UAC wiring gap confirmed yet, unlike DERIBIT-COMBO's genuine missing
routing entry); (c) it may turn out to be a small, single-repo fix once traced, similar in shape to Bug C/D in the
sibling doc but not yet proven.

## Recommended decision

Route to `data_engineering` — all 3 easy-win hypotheses (2 UAC declarations + symbol resolution) are already ruled out
with hard evidence, so go straight to tracing `download_batch`'s per-symbol dispatch loop (temporary logging or a live
VM run.log inspection at the actual dispatch point — NOT more static reading of the already-eliminated resolution
functions). Once the code fix (if any) lands, launch a scoped `ONLY="COINBASE-FUTURES:2026:heavy" VM_FORCE=true` VM and
confirm real `SPOT_PAIR` rows land (any `capture_status`, matching this doc's own diagnostic method — a manifest
row-group-pushdown query, not a full 263MB download).

**Launcher note for whoever launches the diagnostic VM**: `launch-cefi-sharded-backfill.sh` refuses to launch while
other `cefi-*-heavy/light` VMs are running in the zone (a real singleton-lock safety check, not a bug) — use `FORCE=1`
(the harmless lock-bypass flag, distinct from `VM_FORCE`) alongside `VM_FORCE=true` when other cefi VMs are already
running, matching this session's and the prior session's launch commands.

## Todos

- [x] ✅ [SCRIPT] P2. Check `INSTRUMENT_TYPES_BY_VENUE["COINBASE-FUTURES"]` includes `"SPOT_PAIR"` and
      `VENUE_DATA_TYPE_CAPABILITIES["COINBASE-FUTURES"]` declares `"trades"` — both checked this session, both already
      correctly declared (see "What I found" above). Not the bug; do not re-check. (repo: unified-api-contracts)
- [x] ✅ [SCRIPT] P2. Check whether `_catalogue_symbols_for_venue_date`/`_resolve_symbols` actually surface the 16
      mvp=True SPOT_PAIR symbols — called directly this session (no VM needed), confirmed all 16 ARE returned correctly
      (284-symbol mixed universe for 2026-06-01). NOT the bug; do not re-trace the resolution layer. Also confirmed
      `force=True` genuinely no-ops the venue-level skip-existing preflight (read `_run_preflight_availability_check`
      directly) — the prior session's `VM_FORCE=true` wasn't silently failing to apply either. (repo:
      market-tick-data-service)
- [x] ✅ [SCRIPT] P2. Trace `download_batch`'s per-symbol dispatch loop (`_run_per_symbol_batch` →
      `_emit_per_symbol_manifest` in `tardis_batch_download.py`) directly — root cause found ONE LEVEL UP from the
      dispatch loop itself: `_classify_row_instrument_type` (`tardis_adapter.py:314`), called at task-construction time
      inside `_run_per_symbol_batch` to build each `PerSymbolTask.row_key["instrument_type"]`. Confirmed hypothesis 2
      (symbol-shape assumption) — its venue-level SPOT_PAIR whitelist only covered pure-spot venues
      (BINANCE-SPOT/BYBIT-SPOT/OKX-SPOT/COINBASE-SPOT/UPBIT/BITFINEX-SPOT/BITGET-SPOT/KRAKEN-SPOT); COINBASE-FUTURES is
      MIXED (401 PERPETUAL + 19 SPOT_PAIR per the live catalogue) so it couldn't join that blanket set, and every
      SPOT_PAIR symbol (`BTC-USDC` etc.) fell through to the venue-agnostic PERPETUAL default — misclassifying every
      COINBASE-FUTURES SPOT_PAIR manifest row as `instrument_type=PERPETUAL`, which exactly explains "zero rows of any
      capture_status" for the real (COINBASE-FUTURES, SPOT_PAIR) tuple (its captures were silently landing under the
      PERPETUAL bucket instead). Confirmed via live GCS catalogue query: PERPETUAL raw_symbols end `-PERP` (e.g.
      `BTC-PERP`), SPOT_PAIR raw_symbols end `-USDC` (e.g. `BTC-USDC`) — clean, unambiguous shape split. Fixed with a
      symbol-shape branch (`venue_u == "COINBASE-FUTURES" and s.endswith("-USDC")` → `SPOT_PAIR`) placed before the
      venue whitelist, verified NOT to regress the 401 real `-PERP` symbols (added a sibling regression test). 2
      regression tests added to `tests/unit/test_tardis_batch_download_failure_instrument_type.py`; full
      `quality-gates.sh` green (115s); shipped market-tick-data-service@8be30c8c. Hypothesis 1 (an itype-partition
      inside `download_batch` itself) was NOT the bug — no such partition exists for this venue; do not re-check it.
      (repo: market-tick-data-service) **Addendum (data_engineering slot-6, same session window):** independently traced
      the same root cause and landed an equivalent fix; on push, discovered slot-3's 8be30c8c already shipped the
      identical `_classify_row_instrument_type` change. Rebased onto it, dropped the now-redundant code change, and kept
      a complementary classifier-level regression test (direct `_classify_row_instrument_type` assertions, distinct test
      layer from slot-3's `_run_per_symbol_batch` row_key tests) — shipped market-tick-data-service@c7065850.
- [x] ✅ [VERIFY] P2. Once a fix lands, launch
      `ONLY="COINBASE-FUTURES:2026:heavy" VM_FORCE=true FORCE=1     TARDIS_KEY_CHECK=0 bash launch-cefi-sharded-backfill.sh`
      (see launcher note above) and confirm real SPOT_PAIR manifest rows land (query the manifest with a
      row-group-pushdown filter, not the full-download approach that timed out once in this session). (repo:
      deployment-service) — **Verified (data_engineering slot-3, 2026-07-12T21:13-21:44Z).** Launched
      `cefi-coinbase-futures-2026-heavy-20260712-212050` (SPOT, e2-highmem-16). **Real infra bug hit + fixed en route**:
      bare `gcloud` on this host resolves to a broken snap wrapper (`snap-confine: cap_dac_override` missing) that fails
      every call silently — the launcher's backgrounded `gcloud compute instances create ... &` never checks the child's
      exit code, so the first launch attempt reported "All 1 VMs launched" while creating ZERO real VMs (confirmed via
      `gcloud compute operations list` — no matching insert op). Fixed via the documented workaround
      (`PATH="/snap/google-cloud-cli/current/bin:$PATH"`, per `mvp_backfill_cefi_tick_v10_2026_06_27.md`'s prior
      2026-07-03/07-06 sightings of the same host bug). Second launch also caught + fixed a STALE code tarball (the mtds
      tarball manifest was pinned to the pre-fix commit `a0504bbe`) — deleted that VM before it could run pre-fix code,
      republished via `create-code-tarballs.sh --include market-tick-data-service` (manifest confirmed @ fix SHA
      `8be30c8c`), then relaunched clean. Monitored `run.log` (`gs://deployment-scripts-.../vm-logs/<vm>/run.log`) end
      to end — real Tardis captures for `BTC-USDC`/`ETH-USDC` landed under the CORRECT
      `instrument_type=spot_pair/data_type=trades/BTC-USDC.parquet` GCS path within seconds of day 2026-01-01 starting
      (structurally impossible pre-fix, since the classifier hardcoded every COINBASE-FUTURES symbol to
      `instrument_type=PERPETUAL`). Waited for day 2026-01-01's full per-symbol batch (~800 shards, all instrument
      types/data_types) to complete so the per-date manifest finalize (`_write_date_manifest`) ran — confirmed
      `Manifest updated: date=2026-01-01 venues=1 shards=346 total_records=48815321 complete=True` in the run.log, then
      queried the per-VM shard directly
      (`market-data-tick-cefi-prd-central-element-323112/_index/per_vm/<vm-name>.parquet`, row-group-pushdown filter,
      not a full-corpus walk) and got **4 real `capture_status=captured` rows** for (COINBASE-FUTURES, SPOT_PAIR):
      `BTC-USDC`/`ETH-USDC` × `{trades, book_snapshot_5}` — `BTC-USDC book_snapshot_5` 393,387 rows,
      `ETH-USDC     book_snapshot_5` 164,301 rows, `BTC-USDC trades` 192 rows, `ETH-USDC trades` 94 rows. Deleted the VM
      immediately after confirming (day 2026-01-01 complete; no need to run the full 2026-01-01→2026-05-22 range for
      this diagnostic). Bug fully closed: catalogue → resolution → dispatch → GCS write → manifest all now agree.
