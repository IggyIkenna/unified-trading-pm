---
doc_type: issue
title:
  "OPERATOR DECISION: MTDS's TardisAdapter cefi manifest WRITE path stamps raw exchange symbols as instrument_id; the
  honest-coverage denominator expects canonical instrument_key. Zero canonical-id rows have ever reached captured for
  Tardis-sourced venues — the 3-VM Tardis fleet is fetching real data into a namespace the G4 gate cannot credit.
  SCOPE-CORRECTED: the separate OnchainPerpBatchHandler lane (HL/ASTER/LIGHTER/PACIFICA/EXTENDED) is NOT affected —
  verified already writing canonical ids"
summary:
  "data_engineering (slot-12, 2026-07-15), continuing mvp_backfill_cefi_tick_v10_2026_06_27.md G4. A peer slot's 18:50Z
  Progress Log entry (unified-trading-pm@23d0b8161) found: reading the live prd
  market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet for KRAKEN-FUTURES/book_snapshot_5
  shows two disjoint id namespaces — captured rows keyed by RAW exchange symbol (XBT, PI_ETHUSD, BTCUSDH26) vs
  expected_unattempted rows keyed by CANONICAL instrument_key (KRAKEN-FUTURES:PERPETUAL:ETH-USD@LIN). Cross-tab by month
  across the ENTIRE corpus (2023-02→2026-03): every captured row is canon=False — ZERO canonical-id rows have EVER
  reached captured. Measured proof the live fleet fetching closes nothing: between the 17:18Z and 18:30Z coverage runs,
  expected_unattempted moved 2,969,412→2,773,292, a delta of exactly -196,120 — 100% attributable to the unrelated UAC
  no-batch-source code fix, not the 3 Tardis VMs that fetched throughout that window (they closed ZERO eu cells;
  captured rose +1,018, all into the uncredited raw namespace). This session (slot-12) independently verified the 'gap
  is the last 6 months' pattern holds per-venue for HYPERLIQUID/LIGHTER-ZKSYNC/PACIFICA-SOLANA/ EXTENDED-STARKNET
  (by_day cross-tab, eu=0 for every month before 2026-02), fixed a launcher scoping gap (deployment-service@ab59b01,
  YEARS= override on launch-cefi-hl-aster-historical-backfill.sh), and launched 4 new 2026-only VMs
  (cefi-hyperliquid/lighter-zksync/pacifica-solana/extended-starknet-2026-20260715-190049) targeting the ~172,759-cell
  non-Tardis derivative_ticker eu gap — BEFORE seeing this finding (it landed in the plan file between this session's
  read and its next pull). While filing this doc, code-read + live-manifest-verified that the defect is SCOPED TO
  TardisAdapter ONLY: the non-Tardis OnchainPerpBatchHandler lane (which the 4 new VMs use) already stamps canonical ids
  via native_symbol_to_instrument_id (canonicalized 2026-07-09) — confirmed against live ASTER/HYPERLIQUID captured rows
  (ASTER:PERPETUAL:BNB-USDT@LIN, HYPERLIQUID:PERPETUAL:TRB-USD@LIN), so the 4 new VMs are NOT affected and were left
  running with no caveat. NOT the same defect as ../instrument_id_format_canonicalization_2026_07_08.md (that one is the
  CATALOGUE's InstrumentRecord.canonical_instrument_id, already fixed per instruments-service@f90d0e0) — this is MTDS's
  TardisAdapter manifest WRITE path specifically."
status: open
priority: P0
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags:
  [
    cefi,
    instrument-id,
    canonicalization,
    manifest-writer,
    honest-coverage,
    namespace-mismatch,
    data-correctness,
    g4-gate,
  ]
related:
  [
    ../mvp_backfill_cefi_tick_v10_2026_06_27.md,
    instrument_id_format_canonicalization_2026_07_08.md,
    ../canonical_instrument_id_cefi_defi_backfill_2026_07_14.md,
    cefi_live_only_data_types_vs_layer1_denominator_contradiction_2026_07_12.md,
  ]
created: 2026-07-15
parent_epic: cefi_master
assigned_vm: planning
source:
  "Root cause found by a peer data_engineering slot, 2026-07-15T18:50Z, direct filtered read of
  market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet (KRAKEN-FUTURES/book_snapshot_5,
  207MB index) cross-tabbed by month against capture_status + canon flag; corroborated by measure_honest_coverage.py
  before/after deltas across the 17:18Z/18:23Z/18:30Z session runs. This doc filed by data_engineering slot-12 per the
  findings-triage HARD RULE (data-correctness + gate-status finding = NOTIFY OPERATOR + issue doc), since the peer's
  plan Progress Log entry had not yet been closed with a tracked issue doc."
locked_by:
locked_since:
resolved_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# CeFi MTDS writer: raw exchange symbol vs canonical instrument_key — eu namespace mismatch

## What I found

The `mvp_backfill_cefi_tick_v10_2026_06_27.md` G4 gate requires `expected_unattempted=0` for the cefi MVP universe. The
remaining ~2.77M eu cells were assumed to be a genuine backfill gap (the "last 6 months" finding). They are not — or not
entirely. Direct manifest inspection shows:

```
capture_status         rows     sample instrument_id
captured               25,282   XBT, PI_ETHUSD, ETH, BCH                    <- RAW exchange symbol
expected_unattempted   40,223   KRAKEN-FUTURES:PERPETUAL:PIXEL-USD@LIN      <- CANONICAL instrument_key
```

Every `captured` row across the entire corpus history is keyed by the vendor's raw symbol; every `expected_unattempted`
row (materialized by the Layer-1-complete enumerator) is keyed by the canonical `instrument_key`. Nothing joins them.
Zero canonical-id rows have ever reached `captured`, for any venue, in this manifest's history.

**Live proof the current fleet is actively reproducing this**: `cefi-queue-heavy-174106`'s `run.log` shows it writing
`.../venue=KRAKEN-FUTURES/instrument_type=perpetual/data_type=book_snapshot_5/PF_IOTAUSD.parquet` (raw symbol) in real
time.

**SCOPE CORRECTION (verified, not the fleet-wide defect this doc's title originally implied): the non-Tardis
`OnchainPerpBatchHandler` lane (HYPERLIQUID/ASTER/LIGHTER-ZKSYNC/PACIFICA-SOLANA/EXTENDED-STARKNET) does NOT share this
defect.** Code read:
`market_tick_data_service/cli/handlers/_onchain_perp_batch_symbols.py::native_symbol_to_instrument_id` was explicitly
canonicalized 2026-07-09 ("reconstructs the real settlement currency … rather than emitting a
quote-less/undash-joined/unmarked id") and IS the id stamped at write time
(`onchain_perp_batch_handler.py:446,551,575,585`). Empirically confirmed against the live prd manifest: existing
`captured` rows for both venues are already canonical — `ASTER:PERPETUAL:BNB-USDT@LIN`,
`HYPERLIQUID:PERPETUAL:TRB-USD@LIN` (pandas filtered read, `capture_status=captured`, both venues, 2026-07-15). The
defect is confirmed ONLY for the **Tardis-sourced venues** (`TardisAdapter`, the 3-VM `cefi-queue-*` lane) — this is
where the KRAKEN-FUTURES raw-symbol proof lives. The 4 non-Tardis VMs this session (slot-12) launched
(`cefi-hyperliquid/lighter-zksync/pacifica-solana/extended-starknet-2026-20260715-190049`) are writing canonical ids and
SHOULD correctly close their target eu cells — left running with no caveat.

**Measured, not inferred**: `expected_unattempted` moved 2,969,412 → 2,773,292 between the 17:18Z and 18:30Z coverage
runs — a delta of exactly −196,120, which is 100% attributable to the unrelated `VENUE_DATA_TYPE_NO_BATCH_SOURCE` UAC
fix shipped in that same window. The three Tardis VMs fetching throughout that window closed **zero** eu cells despite
`captured` rising +1,018 (all landing in the uncredited raw-symbol namespace).

## Why it matters

- **G4 cannot close via the Tardis lane this way.** Every VM-hour the 3-VM `cefi-queue-*` Tardis fleet spends right now
  writes real, correctly-fetched data that the honest-coverage gate cannot credit — that lane is accruing "relabel debt"
  at fleet speed instead of closing the gate, not merely working slowly.
- **Scoped to `TardisAdapter` only** (confirmed by code read + live manifest check, see above) — the separate
  `OnchainPerpBatchHandler` lane (HL/ASTER/LIGHTER-ZKSYNC/PACIFICA-SOLANA/EXTENDED-STARKNET, non-Tardis REST) already
  writes canonical ids and is NOT affected. The bulk of the ~2.77M eu gap is behind the majors (BINANCE/OKX/BYBIT/etc,
  all Tardis-sourced), so this still blocks most of G4 — but it is not a total fleet-wide freeze.
- Distinct from the already-fixed catalogue defect (`instruments-service@f90d0e0`,
  `../instrument_id_format_canonicalization_2026_07_08.md`) — that fixed `InstrumentRecord.canonical_instrument_id` in
  the reference-data catalogue. This defect is in MTDS's `TardisAdapter` manifest **write** path specifically, which
  still stamps the raw vendor symbol at capture time regardless of what the catalogue now carries.
- The bytes fetched so far by the Tardis lane are NOT wasted — they are real market data, reusable via a
  relabel/reconcile pass once the writer is fixed. This is why that lane was left running rather than killed — but every
  additional Tardis VM-hour without a plan to relabel is deferred work, not progress on G4.

## Root cause, code-traced end-to-end (2026-07-15T19:xx, data_engineering slot-12)

This is NOT a simple oversight — it is a **documented, intentional design decision** that now conflicts with the newer
Layer-1 honest-coverage gate's requirement that captured rows key on canonical `instrument_id`.

**The parquet FILE content is already correct.** `finalise_rows_and_path()`
(`market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py:717`) calls `derive_row_instrument_id()` per
row, which correctly canonicalizes every tested raw KRAKEN-FUTURES symbol (live tested against the running fleet's
actual symbols): `PI_ETHUSD → KRAKEN-FUTURES:PERPETUAL:ETH-USD@INV`,
`PF_IOTAUSD → KRAKEN-FUTURES:PERPETUAL:IOTA-USD@LIN`, `PI_XBTUSD → KRAKEN-FUTURES:PERPETUAL:BTC-USD@INV`. This is the
SAME canonicalization mechanism `OnchainPerpBatchHandler` uses successfully (confirmed above) — it is NOT missing, it
works.

**The MANIFEST write is a completely separate, parallel path that never calls this function.** Traced end-to-end:

1. `tardis_batch_download.py::_run_per_symbol_batch` (line ~146) builds each fetch task's `row_key` with
   `"instrument_id": sym` — the RAW wire symbol, set at task-creation time, before any canonicalization.
2. Per-shard bookkeeping (`tardis_cefi_shards.py::_tardis_cefi_shard_router` line ~433, `partitioned_writer.py`'s
   `record_shard_count`) groups by the raw `symbol` column (`third_key`) — also never canonicalized.
3. `venue_fetch.py::_record_venue_shard_counts` (line 348) sets
   `instrument_id_for_manifest = "" if is_derivative else third_val` — `third_val` is that same raw wire symbol, flowing
   straight into `state.shard_counts`.
4. `manifest_finalize.py::_write_shard_counts_to_manifest` (line ~292) unpacks `instrument_id_key` from `shard_counts`
   and passes it to the actual `record_captured()` call — still the raw wire symbol. **This function is shared across
   asset groups** (sports `odds` shards go through the same code, line ~329) — not cefi-specific.
5. A canonicalization function DOES exist and IS called somewhere in this vicinity —
   `preflight.py::_canonicalize_captured_instrument_id` (line 464) — but its own docstring says explicitly: _"Used by
   the Tier-3 sentinel comparison so captured shards correctly suppress false attempted_failed rows. **Never used for
   path or manifest writes — those keep wire form.**"_ This is the smoking gun: whoever wrote this knew the manifest
   stores wire-form and documented it as intentional, presumably before Layer-1 completeness became a hard gate
   requirement.

**Why this is NOT a quick solo fix**: `_write_shard_counts_to_manifest` and `_record_venue_shard_counts` are shared
plumbing, not cefi-only — a naive "just canonicalize `third_val`" edit risks regressing sports `odds` manifest writes
(same code path) and the Tier-3 sentinel's OWN dedup logic, which currently RE-canonicalizes wire-form on read
specifically BECAUSE the manifest stores wire form (`_canonicalize_captured_instrument_id`'s whole reason to exist).
Changing the manifest's stored form without also revisiting the sentinel comparison could silently break the sentinel
(double-canonicalizing an already-canonical id, or losing the wire-form fallback for unrecognised shapes it currently
relies on). This needs a scoped design decision, not a blind edit under time pressure.

## Recommended decision

Three options, not mutually exclusive, in dependency order — scoped to the Tardis lane only:

1. **Fix the manifest write path** — thread a cefi/Tardis-specific canonicalization call (reusing the already-correct
   `derive_row_instrument_id`/`finalise_rows_and_path` logic, NOT `_canonicalize_captured_instrument_id` which is
   intentionally lossy/best-effort) into `venue_fetch.py::_record_venue_shard_counts` line 348, gated to cefi
   Tardis-sourced shards specifically so sports `odds` writes (same shared function) are untouched. Requires also
   auditing whether the Tier-3 sentinel (`sentinels.py`) needs a matching update once the manifest itself carries
   canonical form (it may become simpler — no more wire↔canonical translation needed for cefi — but that must be
   verified, not assumed).
2. **Relabel/reconcile the existing raw-id Tardis captures** in place (one pass over the manifest, mapping raw symbol →
   canonical instrument_key per venue using `derive_row_instrument_id`, which the parquet FILE content already proves
   correct) rather than re-fetching — the underlying parquet bytes are correct, only the manifest's `instrument_id` key
   is wrong.
3. **Do NOT widen the Tardis lane (relaunch chronological waves, add venues) before (1) lands** — doing so burns more of
   the hard-capped 3-VM Tardis quota into the same uncredited namespace. The non-Tardis `OnchainPerpBatchHandler` lane
   is unaffected and may continue/widen normally.

- [ ] [BACKEND] P0. Fix `venue_fetch.py::_record_venue_shard_counts` (line ~348) to canonicalize
      `instrument_id_for_manifest` for cefi Tardis-sourced shards using the proven-correct
      `derive_row_instrument_id`/`finalise_rows_and_path` logic (not `_canonicalize_captured_instrument_id`, which is
      explicitly documented as sentinel-only/lossy). Scope the change to cefi (or Tardis-sourced venues specifically) so
      sports `odds` writes through the same shared function are unaffected. Audit `sentinels.py`'s Tier-3 comparison for
      whether it needs updating once the manifest carries canonical form instead of wire form. (repo:
      market-tick-data-service)
- [ ] [SCRIPT] P0. Write a one-time relabel/reconcile script for the cefi prd manifest: map existing raw-symbol
      `captured` rows (Tardis-sourced venues only) to their canonical `instrument_key` per venue (reusing
      `derive_row_instrument_id`, already proven correct against live symbols above), snapshot-first (mirrors the
      pattern in `scripts/purge_deribit_option_per_strike_trades_book5_2026_07_12.py`), verified before/after row
      counts. Do NOT re-fetch — the parquet bytes are correct, only the manifest key is wrong. (repo:
      instruments-service)
- [ ] [SCRIPT] P1. Once (1) lands and is verified with a live smoke capture, re-measure
      `measure_honest_coverage.py --asset-group cefi` and confirm the Tardis lane's NEW writes land under canonical keys
      and start reducing `expected_unattempted`. (repo: instruments-service)
