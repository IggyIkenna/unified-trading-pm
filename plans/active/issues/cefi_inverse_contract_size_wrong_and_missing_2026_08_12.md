---
doc_type: issue
title: "CeFi inverse contract_size silently wrong (OKX/Deribit) and unresolvable (30/64 instruments) — 2026-08-12"
summary: >-
  Third root cause found while verifying the liquidations inverse-notional re-derive (see
  data_pipeline_alert_storm_root_cause_batch_2026_08_10.md P0): MDPS was silently defaulting every inverse contract's
  face value to 1 (correct by coincidence for Bybit/Kraken, wrong for OKX non-BTC alts and Deribit BTC — understated
  10x/100x) because Tardis's free instrument-enumeration endpoint never carries contractMultiplier and the paid tier
  that does isn't in this workspace's current subscription. Fixed via a reverse-engineered, sourced UAC registry
  (unified-api-contracts@<pending>). A SEPARATE finding — 30/64 target instruments got ZERO successful writes the entire
  re-derive run, not intermittent — splits into a BYBIT stale-id-format bug (caller-side, MDPS threads a pre-migration
  id shape) and an OKX-SWAP delisted-instrument capture/rollup gap (not yet resolved).
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [unified-api-contracts, market-data-processing-service, instruments-service, unified-trading-library]
scope: [engineer, admin]
tags: [contract_size, liquidations, tardis, instruments-service, cefi-inverse]
related: [data_pipeline_alert_storm_root_cause_batch_2026_08_10, cefi_consolidated_closeout_2026_07_18]
created: 2026-08-12
author: claude-agent
source: "2026-08-12 continuation session, verifying the liquidations re-derive's manifest outcome"
priority: P0
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# CeFi inverse contract_size silently wrong and missing — 2026-08-12

## Background

After the two 2026-08-12 MDPS fixes (1d-scheduling spelling mismatch + OHLC-nullable schema fallback — see the P0 todo
in `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`), the liquidations re-derive VM
(`mdps-backfill-cefi-20260812-135814`) ran the full 2020-01-01..2026-01-31 range (2223 dates) to a clean exit. Full
verification found two DISTINCT further problems, neither caused by either of that day's two fixes.

## Finding 1 — 30/64 target instruments got ZERO successful writes the entire run (not intermittent)

Re-measured post-run: 56,238 shard-rows freshly captured in the run's wall-clock window (13:00-19:00 UTC), across only
34 of the 64 target instruments. The other 30 have NO manifest trace for this run at all. Two separate causes:

**1a. BYBIT stale-id-format — caller-side bug, not instruments-service's.** `BYBIT:PERPETUAL:BTCUSD` /
`BYBIT:PERPETUAL:ETHUSD` (no hyphen, no `@INV`) cannot be produced by any current Tardis-adapter code path — the
adapter's `_build_canonical_perpetual_key`
(`instruments-service/instruments_service/reference_data/adapters/cefi/ tardis/parsing.py:871-874`) always emits
`BYBIT:PERPETUAL:BTC-USD@INV`. Live-verified:
`read_instruments_catalog_contract_size("cefi", "BYBIT", "BYBIT:PERPETUAL:BTC-USD@INV")` resolves fine; the bare
no-hyphen form does not (misses all 3 of `instruments_catalog_reader.py`'s match strategies). **MDPS is somewhere
threading the pre-2026-07 legacy id shape into the liquidations calc instead of the canonical one — not yet traced to
the exact call site.** Fix: find where MDPS resolves `instrument_id_str` for BYBIT liquidations and correct it to the
canonical `@INV` form (or add the legacy shape as a 4th match strategy in `instruments_catalog_reader.py` — the
canonical-fix is preferred, don't paper over a real upstream id-hygiene gap).

**1b. OKX-SWAP delisted instruments — capture-vs-rollup gap, NOT resolved, needs a live GCS check.** Tardis's own
`/v1/exchanges/okex-swap` metadata confirms `AVAX-USD-SWAP` (availableSince 2021-11-25, availableTo 2026-07-08) and
`XLM-USD-SWAP` (availableSince 2020-05-11, availableTo 2025-08-16) are REAL, historically-active, now-delisted
instruments — not fabricated/malformed ids. `instruments-service`'s per-date capture
(`instrument_availability/by_date/day=.../venue=OKX-SWAP/instruments.parquet`) is point-in-time filtered
(`process_fetch.py:343-361`), so only days captured DURING the active window would ever carry them. **Whether IS ever
actually captured OKX-SWAP inside those windows, and whether `build_instrument_catalogue.py`'s rollup walked that far
back, is unconfirmed** — the decisive check (not yet run): scan a handful of days in each delisted window for
`raw_symbol` = `AVAX-USD-SWAP`/`XLM-USD-SWAP` in the per-date parquet; presence = rollup bug, absence = genuine capture
gap needing a backfill.

## Finding 2 — contract_size silently WRONG for OKX (non-BTC) and Deribit BTC — FIXED

Root cause, fully traced and verified against live code (not the sub-agent's word alone):

1. `liquidations_adapter.py:266-283` reads `contract_size` via
   `read_instruments_catalog_contract_size("cefi", venue, instrument_id_str)` — a static, non-date-aware lookup against
   `instruments-service`'s `catalog.parquet`. When it misses, the code FAIL-CLOSES (raises `MalformedTickFieldError`) —
   this is correct, deliberate design (2026-08-11 operator ruling: a wrong notional is worse than a failed shard).
2. **But the catalogue itself was never wrong-by-omission for Bybit/Kraken and silently wrong-by-substitution for
   OKX/Deribit.** `instruments-service`'s Tardis CeFi adapter (`adapter.py:649-661`) deliberately calls ONLY the free,
   no-auth `/v1/exchanges/{exchange}` endpoint (2026-06-23 operator decision, to avoid burning API limits before Tardis
   was paid) — that endpoint never returns `contractMultiplier` at all. `adapter.py:872-876` therefore ALWAYS falls
   through to a hardcoded `Decimal("1")` default for every Tardis-sourced CeFi instrument.
3. `1` happens to be Bybit's and Kraken Futures' genuine real face value (confirmed live: Bybit help center + Kraken
   Futures' own API, `contractSize` field value of 1 for `PI_XBTUSD`/`PI_ETHUSD`/`PI_LTCUSD`/`PI_XRPUSD`) — so those
   venues were accidentally correct. **OKX and Deribit were NOT**: live-verified against each venue's own public API
   (2026-08-12) — OKX `BTC-USD-SWAP` ctVal=100, every other `-USD-SWAP` alt ctVal=10 (14 distinct alts confirmed,
   corroborated by OKX's own help-center docs); Deribit `BTC-PERPETUAL` contract_size=10, `ETH-PERPETUAL`=1. **Deribit
   BTC was silently understated 10x and OKX non-BTC alts silently understated 10x — for every liquidation shard ever
   written by this pipeline, not just today's re-derive**, since nothing about this bug is new to today.
4. **Since Tardis is now paid, the obvious next step (switch to the authenticated `/v1/instruments/{exchange}` endpoint,
   which DOES carry `contractMultiplier`) was tested LIVE and does NOT work**: 401,
   `"Instruments metadata API is available only for active 'pro' and 'business' subscriptions."` — the current
   subscription tier doesn't include it. (The GSM secret `tardis-api-key` genuinely resolves and authenticates — this is
   a tier gap, not a missing/broken key. `DATA_SOURCE_TO_SECRET["tardis"] = "tardis-api-key"` in UAC's
   `canonical_mappings.py` is correct and the `ApiKeyReloader`/`factory.py` wiring already threads a real key into every
   OTHER Tardis adapter method — `instruments-service/instruments_service/reference_data/factory.py`'s Tardis
   construction branch just deliberately omits `api_key=api_key`, a one-line, easy, but INSUFFICIENT fix on its own
   given the tier gap.)

**Fix shipped** (operator direction: "reverse engineer it, stick it in UAC, resolve from that, use web to find patterns"
— not depend on the unavailable paid tier): new registry
`unified-api-contracts/unified_api_contracts/registry/cefi_inverse_contract_multipliers.py` —
`resolve_cefi_inverse_contract_multiplier(venue, base_asset)`, sourced + cited against each venue's live public API
(URLs + fetch date in the file's own comments), 34 new tests (`tests/unit/test_cefi_inverse_contract_multipliers.py`).
Gate green for the new code (34/34 passed); the FULL-repo gate has one UNRELATED pre-existing failure
(`test_priority_source_resolves_to_capability[fluid]` — a DeFi "Fluid" protocol capability-declaration gap that landed
via the same `main`→LDR backmerge that hit this checkout mid-session, nothing to do with CeFi/liquidations) — noted here
so it isn't confused with this fix; not this doc's scope to fix.

## Still open — NOT done yet

- [ ] [SCRIPT] P0. Wire the new UAC resolver into `liquidations_adapter.py`'s inverse-margin branch (check
      `resolve_cefi_inverse_contract_multiplier(venue, base_asset)` FIRST; fall back to the existing
      `read_instruments_catalog_contract_size` catalogue lookup only for venues the static registry doesn't cover). Was
      in progress when this session hit a context-limit checkpoint — not started.
- [ ] [SCRIPT] P1. Trace exactly where MDPS threads the stale `BYBIT:PERPETUAL:BTCUSD`/`ETHUSD` id shape into the
      liquidations calc (Finding 1a) and fix at the source (canonicalize before the catalogue-lookup call site).
- [ ] [DATA] P1. Run the decisive per-date GCS check for Finding 1b (OKX AVAX/XLM delisted-instrument capture vs rollup
      gap) — scan `instrument_availability/by_date/day=<in-window-date>/.../venue=OKX-SWAP/instruments.parquet` for
      `raw_symbol` = `AVAX-USD-SWAP`/`XLM-USD-SWAP`; presence=rollup bug, absence=capture gap.
- [ ] [OPERATOR] P2. Decide whether to upgrade the Tardis subscription to "pro"/"business" tier — would let
      instruments-service source `contractMultiplier` directly instead of depending on a hand-maintained UAC registry
      that needs manual re-verification if a venue's face values ever change. Not urgent — the UAC registry is a
      complete, correct, cited fix for the CURRENT known instrument set.
- [ ] [SCRIPT] P0. Re-run the liquidations re-derive (a 4th attempt) once the above are fixed, same 3-way verification
      rigor as every prior attempt in this batch (log counters + manifest `written_at` + GCS `last_modified` — a clean
      exit code alone has already proven insufficient twice this batch).

## Lesson

**A live, executable verification beats a plausible design decision every time — the free-vs-paid Tardis endpoint choice
READ as reasonable (a real operator decision with a real date and a real reason) right up until it was tested live and
found to not solve the actual problem (401, wrong tier).** Don't stop at "there's a documented reason this is the way it
is" — test whether the reason still holds NOW. Separately: mid-session, an automated `main`→LDR backmerge + this
checkout's own liveness-gated cleanup silently reverted an in-progress, uncommitted UAC edit (tracked file `__init__.py`
reverted, untracked new files deleted) — recovered only because the full file content was still in the live conversation
context. Reinforces the standing lesson even harder: ship at every green-gated unit, don't let genuinely-done work sit
uncommitted across a checkpoint boundary, even mid-task.
