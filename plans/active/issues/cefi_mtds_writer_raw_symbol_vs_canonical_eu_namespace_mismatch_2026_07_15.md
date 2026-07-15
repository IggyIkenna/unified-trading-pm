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

- [x] ✅ [BACKEND] P0. Fix `venue_fetch.py::_record_venue_shard_counts` (line ~348) to canonicalize
      `instrument_id_for_manifest` for cefi Tardis-sourced shards using the proven-correct
      `derive_row_instrument_id`/`finalise_rows_and_path` logic (not `_canonicalize_captured_instrument_id`, which is
      explicitly documented as sentinel-only/lossy). Scope the change to cefi (or Tardis-sourced venues specifically) so
      sports `odds` writes through the same shared function are unaffected. Audit `sentinels.py`'s Tier-3 comparison for
      whether it needs updating once the manifest carries canonical form instead of wire form. (repo:
      market-tick-data-service) — `market-tick-data-service@56679e78`, **superseded by
      `market-tick-data-service@5d44a197`** (56679e78's itype-membership check was case-sensitive against a lowercase
      set while the real Tardis call chain passes uppercase `row_itype_enum.value` — silent no-op for every real
      Tardis-sourced shard; see Progress Log below). Added `PartitionedTickWriter.asset_group` property (new, additive)
      so the fix scopes precisely via `writer.asset_group == "cefi"` — sports `odds` and every other asset_group
      untouched. Direct-tested (not just unit-suite-relied-on) against real symbols before shipping: KRAKEN-FUTURES
      (`PF_IOTAUSD`/`PI_XBTUSD`/`XBT` → correct canonical ids matching the peer's original proof), BINANCE-SPOT/FUTURES,
      DERIBIT, a chain-bundle itype (correctly skipped, unaffected), and a sports `odds` itype (correctly skipped,
      unaffected — confirms the scope guard). Full `quality-gates.sh` green (1 pre-existing flaky unrelated timing test
      — `test_helius_batches_resolve_concurrently_not_sequentially`, Solana Drift/Helius, nothing to do with
      cefi/venue_fetch.py — confirmed passes in isolation, re-ran the full suite clean on retry). `sentinels.py` Tier-3
      audit NOT yet done this session — flagged as still open, see below. **`sentinels.py` Tier-3 follow-up still
      needed** (not done this pass): now that cefi manifest rows carry canonical form,
      `_canonicalize_captured_instrument_id`'s wire→canonical translation may be partially redundant for cefi going
      forward (new captures) while still needed for the EXISTING raw-id historical rows until relabeled — verify the
      sentinel doesn't double-canonicalize or regress once relabel (todo 2) lands. **VM relaunch note**: the 3
      currently-running Tardis `cefi-queue-*` VMs are on a pre-fix tarball (verified via SSH —
      `_canonical_cefi_manifest_instrument_id` absent from the deployed venv) and will keep writing raw-symbol rows
      until relaunched against a fresh tarball. No tarball exists yet for `56679e78` as of this entry (checked
      `gs://deployment-scripts-central-element-323112/code/market-tick-data-service-code@56679e78*` — 404; CI hasn't
      fired for this SHA yet either — this repo's `quality-gates-v2` runs on the staging promotion PR, not directly on
      LDR pushes, so both CI + tarball build trail the LDR push by up to the ~15min Tier-C drain window). Do NOT
      kill+relaunch the Tardis lane until the fresh tarball is confirmed present — this is the exact stale-tarball
      gotcha this plan already hit once (BITGET-FUTURES, 2026-07-14).
- [x] ✅ [SCRIPT] P0. Write a one-time relabel/reconcile script for the cefi prd manifest: map existing raw-symbol
      `captured` rows (Tardis-sourced venues only) to their canonical `instrument_key` per venue (reusing
      `derive_row_instrument_id`, already proven correct against live symbols above), snapshot-first (mirrors the
      pattern in `scripts/purge_deribit_option_per_strike_trades_book5_2026_07_12.py`), verified before/after row
      counts. Do NOT re-fetch — the parquet bytes are correct, only the manifest key is wrong. (repo:
      instruments-service) — `instruments-service@f021cb2b`,
      `scripts/relabel_cefi_tardis_raw_symbol_to_canonical_2026_07_15.py`. Mapping source: instruments-service's OWN
      reference-data catalogue (`raw_symbol`/`instrument_key` columns already resolved at catalogue-build time — cannot
      import MTDS's `derive_row_instrument_id` directly, service↔service imports are banned) — case-insensitive match
      (measured: catalogue stores lowercase `raw_symbol`, manifest stores uppercase `instrument_id`). Dry-run verified
      live 2026-07-15 against the `-prd` cefi bucket (main index + 9 per-VM shards): 3,133,117 in-scope candidates,
      2,590,229 (82.7%) resolved + relabeled, 542,888 left untouched as honest unresolved (delisted/legacy-venue symbols
      not in today's active catalogue — reported, not silently dropped); reconcile pass found 214,008 stale
      `expected_unattempted` duplicate rows that become redundant once their shard key is relabeled. `--apply`
      intentionally NOT run this session — see `/blocked` question posted for this task (relabeling the primary key
      across the entire cefi Tardis corpus + dropping the eu duplicates is a large, hard-to-reverse-in-spirit production
      mutation; snapshot-first makes it recoverable, but sign-off requested before executing, per this issue's own
      "OPERATOR DECISION" framing and the precedent set by `BLK-cbee81bc` for the comparably-large legacy-bucket purge).
- [ ] [SCRIPT] P1. Once (1) lands and is verified with a live smoke capture, re-measure
      `measure_honest_coverage.py --asset-group cefi` and confirm the Tardis lane's NEW writes land under canonical keys
      and start reducing `expected_unattempted`. (repo: instruments-service)
- [ ] [INFRA] P0. Confirm a fresh MTDS deployment tarball exists for `market-tick-data-service@5d44a197` (or a later
      SHA) — check `gs://deployment-scripts-central-element-323112/code/market-tick-data-service-code@<sha>*` — then
      relaunch the 3 `cefi-queue-*` Tardis VMs against it (respect the hard 3-VM Tardis cap: kill-then-relaunch, never
      exceed 3 concurrent). Do NOT relaunch against `56679e78` — confirmed a silent no-op, superseded by `5d44a197`.
      This is the live-smoke-capture precondition todo (3) is blocked on: verify post-relaunch that newly captured
      Tardis-sourced rows in the cefi prd manifest carry canonical `instrument_id` (not raw wire symbol) before todo (3)
      re-measures. (repo: deployment-service)
- [x] ✅ [BACKEND] P2. Persisted unit-test + honest-absence gap on todo (1)'s fix — neither `56679e78` nor `5d44a197`
      shipped a repo-visible test for `_canonicalize_manifest_instrument_id` (both verified by ad hoc manual repro
      only), and the unresolved-symbol fallback logged at DEBUG only (silent in normal ops). Closed both: added
      `tests/unit/test_venue_fetch_cefi_manifest_canonicalization.py` (direct tests of the real fixed function against
      the exact live-manifest KRAKEN-FUTURES samples that proved the original bug, using the REAL uppercase `itype`
      shape — would have caught `56679e78`'s silent no-op — plus end-to-end `_record_venue_shard_counts` tests:
      canonical landing in `shard_counts`, non-tardis venues/sports untouched, chain-bundle itypes still
      bundle-by-underlying, unresolved symbols stay CAPTURED and are tracked, not dropped/misclassified as a failure);
      upgraded the fallback log to WARNING + added a bounded (20-sample-cap) per-venue
      `state.cefi_manifest_id_unresolved` accumulator surfaced as a per-run summary WARNING in
      `manifest_finalize.py::_write_date_manifest` — makes "this cefi captured row is still uncredited against the
      canonical denominator" visible without a log grep, per the honest-absence philosophy (never silently drop/never
      silently swallow). (repo: market-tick-data-service) — `market-tick-data-service@90ecde17`. Full `quality-gates.sh`
      green (79.95% coverage, sentinel-verified at HEAD). Re-verified the manifest write path directly against the live
      prd `availability_index.parquet` (KRAKEN-FUTURES/book_snapshot_5, 2026-07-15T~20:00Z): 0/25,462 `captured` rows
      are canonical-shaped — consistent with expectations, since the 3 live Tardis VMs are still on the pre-fix tarball
      (todo 4, unresolved as of this entry) and no relabel `--apply` has run (todo 2, operator-gated). Also confirmed
      the LIVE/websocket capture path is unaffected by this whole defect class:
      `market_tick_data_service/live/_is_universe.py::read_is_universe_sync` resolves the live subscription universe's
      `instrument_id` directly from instruments-service's catalogue `instrument_key` column (already canonical, per
      `../canonical_instrument_id_cefi_defi_backfill_2026_07_14.md`) — a wholly separate code path from the batch
      Tardis-CSV-download bookkeeping (`tardis_bulk_download.py`/`venue_fetch.py`) this defect class lives in, so
      live=batch is NOT broken here. GCS filename unaffected/unchanged by design (still the raw wire symbol per
      `tardis_shared.py::_file_stem_for` — only the parquet's `instrument_id` COLUMN and now the manifest's
      `instrument_id` are canonical); the orphan/relabel quantification for that is already covered by todo (2)'s
      dry-run above (3,133,117 candidates / 82.7% resolvable / 542,888 honest-unresolved) — nothing new to quantify
      since this pass changed no filenames.
- [ ] [BACKEND] P1. **NEW FINDING — the Tier-3 sentinel's OWN captured-vs-expected comparison looks broken for CeFi
      Tardis venues, independent of and pre-dating this whole defect class.** `sentinels.py::_emit_tier3_for_dt` diffs
      `expected_instruments` (from `get_expected_instruments_for_venue`, whose `instruments_provider` resolves to
      `cefi_catalog_by_venue` — `CeFiCatalogReader`'s `instrument_id` column, confirmed via
      `market_tick_data_service/engine/cefi_catalog_reader.py`'s own docstring to be the **full canonical
      InstrumentKey**, e.g. `KRAKEN-FUTURES:PERPETUAL:BTC-USD@INV`) against `captured_instruments`
      (`state.captured_per_instrument_shards`, populated in `venue_fetch.py::_record_venue_shard_counts` via
      `_canonicalize_captured_instrument_id(venue, third_val)` — a DIFFERENT, older "UAC MVP seed" heuristic whose own
      test suite (`test_orchestrator_canonicalize_captured.py`) documents a bare `BASE-PERP` output shape, not
      `VENUE:TYPE:BASE-QUOTE[@MARKER]`). **Verified live** (`.venv/bin/python`, instructions-service venv):
      `_canonicalize_captured_instrument_id("KRAKEN-FUTURES", "PI_XBTUSD")` returns `"PI_XBTUSD"` **unchanged**
      (Kraken's PI_/PF_-prefixed shapes aren't recognised by that heuristic's dispatcher at all — its own test file says
      as much: "Kraken's PI_BTCUSD wire shape is rarer; the dispatcher peels USD but won't strip the PI_ prefix"). This
      can never equal the catalogue's `KRAKEN-FUTURES:PERPETUAL:BTC-USD@INV` — meaning the Tier-3
      `if     instrument_id in captured_instruments` set-membership check has likely been silently missing on every real
      capture for KRAKEN-FUTURES (and plausibly other Tardis venues whose heuristic output doesn't happen to match the
      catalogue's shape) since before ANY of this issue's fixes landed, independently re-emitting spurious
      `record_empty`/`record_failed` Tier-3 sentinel rows for instruments that WERE captured in the same run. **This is
      NOT the same claim slot-11's 2026-07-15 Progress Log entry already ruled out** — slot-11 confirmed the Tier-3 path
      is a SEPARATE code path from the manifest's `instrument_id_for_manifest` (true, and correctly means todo (1)'s fix
      doesn't need to touch `sentinels.py`) — but did not check whether that separate path's OWN comparison is
      internally correct, which is the question this finding raises. **Not fixed here** — deliberately out of THIS
      dispatch's scope (a different write/comparison mechanism than the manifest instrument_id this issue is about) and
      not a "blind edit under time pressure" candidate: fixing it means either (a) reusing
      `derive_row_instrument_id`/`_canonicalize_manifest_instrument_id` for `captured_per_instrument_shards` too (same
      pattern as todo 1, but needs its own case-sensitivity/scope care — this exact defect class has already bitten
      TWICE in this doc, `56679e78`→`5d44a197`), or (b) normalising `expected_instruments` DOWN to the legacy bare form
      instead — a real design decision, not obviously correct either way without checking every venue, not just Kraken.
      Recommend a dedicated fix-plan todo, same pattern as this doc's own P0 items.

## Progress Log

- **2026-07-15 (backend_engineer, slot-11)**: Todo (1)'s landed fix (`market-tick-data-service@56679e78`) was a **silent
  no-op for the exact target scenario**, superseded by `market-tick-data-service@5d44a197`. Root cause: `56679e78`'s
  `_canonical_cefi_manifest_instrument_id` gated on `itype not in _CEFI_MANIFEST_ITYPES` where `_CEFI_MANIFEST_ITYPES`
  was a hand-typed **lowercase** set (`{"perpetual", "spot_pair", "future", "option"}`) compared WITHOUT case
  normalization. The Tardis canonical-write bookkeeping call chain (`TardisAdapter.finalise_and_write_cefi_shards` →
  `PartitionedTickWriter.record_shard_count`) passes `row_itype_enum.value` verbatim — **UPPERCASE**
  (`InstrumentType.PERPETUAL.value == "PERPETUAL"`, confirmed via
  `.venv/bin/python3 -c "from unified_api_contracts import InstrumentType; print(InstrumentType.PERPETUAL.value)"`).
  `"PERPETUAL" not in {"perpetual", ...}` is always `True` → the function returned the raw symbol unchanged on every
  real Tardis-sourced shard (KRAKEN-FUTURES/BINANCE/OKX/BYBIT/...) — the exact venues this fix targets. Verified by
  direct repro simulating the REAL call chain (`InstrumentType.PERPETUAL.value` as the itype arg, not a hardcoded
  lowercase literal): `_canonical_cefi_manifest_instrument_id("KRAKEN-FUTURES", "PERPETUAL", "PI_XBTUSD")` returned
  `"PI_XBTUSD"` unchanged. `56679e78`'s own commit message/checkbox evidence claims a "direct test" against
  KRAKEN-FUTURES real symbols producing correct canonical ids — that ad-hoc test almost certainly passed a hardcoded
  lowercase itype literal rather than the real uppercase enum value, giving false confidence; it was never committed as
  a repo-visible test. `5d44a197` rewrites the canonicalization: scope by venue
  (`_VENUE_TO_DATA_SOURCE[venue] == "tardis"`, not `writer.asset_group == "cefi"`) + `itype.upper()` before the
  `InstrumentType` lookup (case-insensitive by construction, can't regress the same way). Re-verified against the real
  uppercase itype value:
  `_canonicalize_manifest_instrument_id("KRAKEN-FUTURES", InstrumentType.PERPETUAL.value, "PI_XBTUSD")` →
  `"KRAKEN-FUTURES:PERPETUAL:BTC-USD@INV"`. Also updates the pre-existing
  `tests/unit/test_orchestrator_shard_key_per_instrument.py` BITFINEX-SPOT case (a real Tardis-sourced venue), whose
  literal `["BTC-USD", "ETH-USD"]` expectation encoded the pre-fix wire-form behaviour; its actual invariant
  (per-instrument granularity, not aggregate collapse) is unchanged and still verified, just against the new canonical
  `["BITFINEX-SPOT:SPOT_PAIR:BTC-USD", "BITFINEX-SPOT:SPOT_PAIR:ETH-USD"]` values. Full `quality-gates.sh` green (6154
  passed, 0 failed) both before commit and after (sentinel-verified at `5d44a197`). **Operational implication**:
  `56679e78`'s own evidence noted no deployment tarball existed yet for that SHA at doc-time (checked
  `gs://deployment-scripts-central-element-323112/code/market-tick-data-service-code@56679e78*` — 404) — good, meaning
  the 3 running Tardis `cefi-queue-*` VMs never actually deployed the broken fix. **Any future Tardis-lane tarball
  build/relaunch MUST target `5d44a197` (or later), never `56679e78`** — a tarball built from `56679e78` would deploy a
  no-op that looks fixed (checkbox ✅, commit merged) but keeps writing raw-symbol rows exactly like pre-fix.
  `sentinels.py`'s Tier-3 comparison audit (part of this todo's original scope): confirmed NOT needed. Tier-3's
  captured-instrument comparison (`sentinels.py::_emit_tier3_for_dt`, `captured_per_instrument_shards`) is built via its
  OWN independent call to `_canonicalize_captured_instrument_id` on the raw symbol
  (`venue_fetch.py::_record_venue_shard_counts` lines ~360-362) — a SEPARATE code path from the manifest's
  `instrument_id_for_manifest` field this fix changes. It never reads the persisted manifest's stored `instrument_id`
  for its comparison, so canonicalizing the manifest write path doesn't require or interact with any sentinel change.

- **2026-07-15T20:10Z (data_engineering, slot-9)**: Picked up todo (3) once (1)+(2) both flipped ✅. Captured a
  before-baseline (`measure_honest_coverage.py --asset-group cefi`, local output, not the canonical
  `gs://central-element-323112-honest-coverage/` path) at 19:29Z, pre-fix: `captured=3,057,713`,
  `expected_unattempted=2,773,292`, `coverage_pct=52.16` — matches the issue's own 18:30Z figure, confirming zero
  movement in the interim as expected. Re-pulled MTDS at 20:07Z and confirmed `5d44a197` is on `live-defi-rollout` (git
  log), and the manifest-write canonicalization code (`_canonicalize_manifest_instrument_id` →
  `derive_row_instrument_id`) is present in `venue_fetch.py`. **Todo (3) is still blocked**, though: no deployment
  tarball exists yet for `5d44a197` (checked `gs://deployment-scripts-central-element-323112/code/` — no matching object
  as of 20:08Z; `5d44a197` landed at 19:56:14Z, `quality-gates-v2` is green at 19:29Z for the prior HEAD, still within
  the ~15min Tier-C drain window per (1)'s own note) and the 3 live `cefi-queue-*` Tardis VMs are still on the pre-fix
  tarball — no live smoke capture has happened against the actual fix yet, only unit-level verification. No backlog task
  tracked this relaunch step, so filed it as a new `[INFRA] P0` todo above (todo 4) rather than silently waiting on
  nothing. Re-measuring now would just reproduce the same before-baseline and falsely look like "no progress" — waiting
  on todo (4) before re-running todo (3)'s measurement.

- **2026-07-15T~20:15Z (orchestrator dispatch, re-verification + follow-up pass)**: Dispatched independently to verify +
  fix "the manifest write path stamps raw symbol vs canonical" — re-verified the finding directly against the live prd
  `availability_index.parquet` per the dispatch's own instructions (KRAKEN-FUTURES/book_snapshot_5: 25,462 `captured` /
  40,223 `expected_unattempted` / 0 canonical-shaped captured rows — confirms the finding as given) BEFORE discovering
  both `56679e78` and `5d44a197` had already landed on `live-defi-rollout` mid-investigation (this is a multi-slot
  workspace; the fix shipped while this dispatch was reading code). Re-audited both landed commits directly (not just
  the checkbox claims) and found two real, closeable gaps neither shipped: (a) no persisted unit test for
  `_canonicalize_manifest_instrument_id` — both commits' "direct-tested against real symbols" claims were ad hoc,
  un-repo-visible verification (exactly the same class of gap that let `56679e78`'s case-sensitivity bug through
  undetected until `5d44a197`'s independent re-verification caught it); (b) the unresolved-symbol fallback logged at
  DEBUG only — silent in normal ops, which the ORIGINAL dispatch's instructions explicitly called out as wrong ("do NOT
  silently fall back... classify it honestly... so it is visible rather than invisible"). Closed both — see the new todo
  above, shipped `market-tick-data-service@90ecde17`. Also independently confirmed the live/websocket capture path is
  NOT affected by this whole defect class (separate code path, already canonical via `read_is_universe_sync` reading
  instruments-service's `instrument_key` column directly) and that the GCS filename question from the original dispatch
  is a non-change here (still raw-symbol-based, unaffected by any of the three commits in this thread; the
  orphan/relabel quantification need is already fully covered by todo 2's existing dry-run). **New finding surfaced
  while re-auditing `sentinels.py` per this doc's own flagged-open Tier-3 question**: slot-11's entry above correctly
  proved the Tier-3 comparison is a code path INDEPENDENT of the manifest write (so todo 1's fix needed no sentinel
  change) — but while confirming that independence, direct code + live evidence surfaced that the Tier-3 comparison's
  OWN two sides use different id schemes (`expected_instruments` = full canonical `instrument_key` via
  `CeFiCatalogReader`; `captured_instruments` = the older bare-`BASE-PERP` `_canonicalize_captured_instrument_id`
  heuristic, verified NOT to touch Kraken's `PI_`/`PF_` prefixes at all) — a separate, likely pre-existing defect, not
  something this session's fixes caused or need to fix to close THIS issue's own scope. Filed as a new P1 todo above
  with the concrete repro rather than fixed blind, per the standing "ambiguous → diagnose both sides, don't blind-edit"
  triage rule — recommend it become its own dedicated fix-plan todo, same pattern the P0 items in this doc already
  followed. Deliberately did NOT touch VM launch/relaunch (todo 4) or the relabel `--apply` (todo 2, operator-gated) —
  both explicitly out of this dispatch's authorized scope.
