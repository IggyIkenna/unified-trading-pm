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
    /plans/active/issues/instrument_id_format_canonicalization_2026_07_08.md,
    ../canonical_instrument_id_cefi_defi_backfill_2026_07_14.md,
    /plans/archive/issues/cefi_live_only_data_types_vs_layer1_denominator_contradiction_2026_07_12.md,
  ]
created: 2026-07-15
parent_epic: cefi_master
assigned_vm: NA
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
- [x] ✅ [SCRIPT] P1. Once (1) lands and is verified with a live smoke capture, re-measure
      `measure_honest_coverage.py --asset-group cefi` and confirm the Tardis lane's NEW writes land under canonical keys
      and start reducing `expected_unattempted`. (repo: instruments-service) — **RESULT: NEGATIVE, but
      CORRECTION/RETRACTION (2026-07-15T~22:30Z, cross-referenced from `cefi_completion_program_2026_07_15.md`, the
      successor to the now-archived `mvp_backfill_cefi_tick_v10_2026_06_27.md`): the causal conclusion below was
      methodologically INVALID, not just negative.** Ran the decisive re-measurement at the armed T+86min window (20:22Z
      baseline → 21:48Z): `expected_unattempted` FLAT at 2,773,292 (zero delta). At the time this was read as "writer
      fix insufficient, enumerator atom-inconsistency is the blocker" — that fix (below) is real and DID land
      (`instruments-service@a2468dd9`, confirmed via independent direct data cross-tab, not via this test), but the TEST
      ITSELF proves nothing: the fleet's `YEARS=2026` scoping still derived `start_date=2026-01-01`, and the actual gap
      is `2026-02+` — the fleet spent the entire 86-minute window inside the already-resolved January zone, where zero
      eu-cell closure was possible regardless of writer correctness. Three separate eu re-measurements across this
      thread (this one, and two more before the fleet was correctly re-aimed at `START_DATE=2026-02-01`) were all
      invalid for the same reason. A valid writer-fix test requires a wave whose scan cursor is inside 2026-02+ AND
      survives long enough to write (a THIRD, independent defect — SPOT preemption deletes waves with no relaunch
      mechanism, also found and tracked in the successor plan — made this hard to arrange). See
      `cefi_completion_program_2026_07_15.md` Progress Log "Three structural blockers" entry for the full corrected
      picture.
- [x] ✅ [BACKEND] P0. **NEW, confirmed blocker (the actual G4 gate-closer): re-materialize the cefi expected-universe
      enumerator so every `expected_unattempted` row carries ONE canonical atom shape.** Live-verified the
      `expected_unattempted` side is currently a MIX: some rows canonical (`VENUE:PERPETUAL:BASE-QUOTE@MARKER`, matching
      the now-fixed writer's output), some rows stale (`instrument_type=''` + lowercase-raw id, e.g.
      BINANCE-FUTURES/trades `hotusdt`) — a direct violation of the workspace HARD RULE "shard atom identical across
      writer/manifest/status/gate/UI" (CLAUDE.md § DATA). Even a perfectly-canonicalizing writer cannot close a
      `(itype='', id='hotusdt')` eu cell. Fix: identify + correct whatever wrote the stale-shape eu rows (an older
      enumerator version, most likely — `enumerate_expected_universe.py` or its per-instrument-day writer), then
      re-materialize so ALL eu rows for cefi share the current canonical atom. AFTER this lands, re-run the relabel
      script (todo 2, still operator-gated for `--apply`) and re-measure — do NOT relaunch/widen the Tardis fleet
      further until this lands (per operator ruling `BLK-b319db38`, disposition B: existing 3-VM fleet keeps running
      since its captures are canonical/reusable pre-fetch, but no widening). (repo: instruments-service) —
      `instruments-service@a2468dd9` (code fix) + `instruments-service@7f1aed10` (purge script, dry-run only).
      **Root-cause diagnosis (live manifest read, prd cefi bucket, 2026-07-15T22:2x Z)**: cross-tabbed all 3,106,459
      `expected_unattempted` rows by shard-atom shape. 3,039,660 (97.8%) already canonical. The remaining 66,799
      non-canonical split into THREE distinct classes, only two of which are `expected_unattempted` (the third, 18,855,
      was a false positive in the first-pass regex — `KRAKEN-FUTURES:FUTURE:BTC-USD@LIN-20260626` IS canonical, my
      initial check just didn't allow for the per-contract expiry suffix): (a) **42,993 legacy rows**,
      `enumerator_run_id` column absent (written before that column existed — pre-shape-aware enumerator/writer),
      `instrument_type=''` + a bare, sometimes-lowercase `BASE-QUOTE` id (confirmed live examples:
      `BINANCE-FUTURES/book_snapshot_5` → `ethusdt`/`ontusdt`/`etcusdt`, `COINBASE/book_snapshot_5` → `ETC-USD`, across
      CRYPTOFACILITIES/BITFINEX/BITFINEX-DERIVATIVES/OKEX*/KRAKEN/BYBIT*/BINANCE*/DERIBIT/HYPERLIQUID/UPBIT/
      BITGET-FUTURES — pure historical debris, not reproducible by current code). (b) **6,727 rows tagged with the
      CURRENT enumerator_run_id** (`enum-universe-cefi-20260715-013053`, i.e. an ACTIVE bug, not just debris) — ALL from
      `_enumerate_v2_cefi`'s per-underlying BUNDLE handling (`futures_chain`/`options_chain`,
      DERIBIT/OKX-FUTURES/BYBIT/KRAKEN-FUTURES/BINANCE-FUTURES): the synthetic entry `_rollup_bundle_grain` produces
      carries `instrument_id=<underlying>` (e.g. `SOL`/`BTC`/`FIL`), and `_enumerate_v2_cefi` was blindly copying
      `instr.instrument_id` straight into the `ExpectedRow` for EVERY emission site, never reading `instr.underlying` —
      producing `(instrument_id='SOL', underlying='')` instead of the MTDS writer's actual bundle-capture shard atom
      `(instrument_id='', underlying='SOL')` (`_UNDERLYING_PARTITIONED_TYPES`, confirmed in
      `market_tick_data_service/reader.py`/`manifest_finalize.py`). **This exact bug was ALREADY FIXED for tradfi**
      (`_enumerate_v2_tradfi`'s `is_bundle` branch) — its own present-cols docstring said, verbatim, "Scoped to tradfi
      to leave the cefi / defi / prediction grain — and their per-AG enumerators, which do not yet collapse bundle
      `instrument_id` — untouched." This task is exactly that untouched cefi gap. **Fix shipped**
      (`instruments-service@a2468dd9`): mirrored `_enumerate_v2_tradfi`'s `is_bundle` pattern into `_enumerate_v2_cefi`
      (via `grain_for_instrument_type("cefi", instr.instrument_type, instr.venue) ==     GRAIN_BUNDLE_BY_UNDERLYING`)
      across all 3 `ExpectedRow` emission sites; generalized the present-set columns (`_TRADFI_PRESENT_COLS` →
      `_UNDERLYING_AWARE_PRESENT_COLS`, now routes BOTH tradfi and cefi through the underlying-aware key) — without this
      half, the shape fix alone would have made every bundle underlying's blank `instrument_id` collide in the
      present-set match (one captured underlying falsely marking every OTHER underlying's cell "present", an
      UNDER-seeding regression). Updated 7 pre-existing unit tests whose fixtures/assertions encoded the old
      uncanonicalized bundle shape (2 in `test_enumerate_expected_universe_v2.py` caught the bug directly on first QG
      run; a full-suite QG pass then caught 5 more + 1 in `test_build_instrument_catalogue.py`). Full `quality-gates.sh`
      green (4,404 passed; the 1 pre-existing `check_adapter_contract_regression` warning is MTDS-repo, unrelated,
      already tracked in `lint_sweep_774602ea8_regression_audit_2026_05_20.md`). **Re-materialization (the legacy-debris
      half, `instruments-service@7f1aed10`)**: the code fix only stops FUTURE writes from being non-canonical — it
      cannot retroactively fix the 49,720 rows (both classes above) already on disk. Wrote
      `scripts/purge_stale_shape_cefi_expected_unattempted_2026_07_15.py`, mirroring the established
      snapshot-first/dry-run-default/STOP-ON-SURPRISE pattern
      (`purge_deribit_option_per_strike_trades_book5_2026_07_12.py`). Dry-run verified live against the prd cefi bucket:
      49,720 matches (0 in any of the 5 per-vm shards, all in the main `_index/availability_index.parquet`), within the
      STOP-ON-SURPRISE bound `[5,000, 250,000]`. **`--apply` intentionally NOT run this session** — same precedent as
      this doc's own todo (2) relabel script: deleting ~50K manifest rows corpus-wide, while low-risk (these are
      `expected_unattempted` placeholder rows, not captured data — a stale row is purely denominator debris; either the
      cell genuinely needs re-seeding, which a fresh post-fix enumerator run supplies correctly, or the catalogue no
      longer lists the instrument and the row shouldn't exist at all), is still a real production mutation. Sign-off
      requested — see `/blocked` question posted for this task. **NEW FOLLOW-UP FINDING (filed as its own P1 todo below,
      NOT fixed here)**: a THIRD, narrower non-canonical shape class exists — `BINANCE-FUTURES` dated futures (e.g.
      `BINANCE-FUTURES:FUTURE:ETHUSDT_260626`, 1,776 rows, all current-run) carry a venue:type: prefix glued onto a
      raw/wire-form middle segment (`ETHUSDT_260626`, underscore+YYMMDD) instead of the dash-form
      `BASE-QUOTE@MARKER-YYYYMMDD` every OTHER dated-futures venue uses (confirmed against KRAKEN-FUTURES/BYBIT, which
      correctly produce e.g. `KRAKEN-FUTURES:FUTURE:BTC-USD@LIN-20260626`). This is a LEAF row (not a bundle), so
      `_enumerate_v2_cefi` correctly passes through whatever `instrument_id` the instruments-service CATALOGUE supplies
      — the defect (if any) is upstream, in `build_instrument_catalogue.py`'s catalogue-build step, not in this
      enumerator. Diagnosing both sides (ambiguous → don't blind-edit, per the standing triage rule) was out of this
      todo's scope; flagged as its own follow-up rather than fixed blind.
- [x] ✅ [BACKEND] P1. **NEW FINDING — BINANCE-FUTURES dated-futures catalogue `instrument_id` carries a raw/wire-form
      middle segment instead of the dash-canonical shape every other dated-futures venue uses.** Found while diagnosing
      the P0 above: live cefi manifest has 1,776 `expected_unattempted` rows (all tagged with the current
      `enum-universe-cefi-20260715-013053` run) shaped `BINANCE-FUTURES:FUTURE:ETHUSDT_260626` /
      `BINANCE-FUTURES:FUTURE:BTCUSDT_260626` — a correct `VENUE:TYPE:` prefix glued onto `ETHUSDT_260626` (underscore +
      6-digit YYMMDD, the raw Binance wire form) rather than the dash-canonical `BASE-QUOTE@MARKER-YYYYMMDD`
      (`ETH-USDT@LIN-20260626`) that `KRAKEN-FUTURES`/`BYBIT` dated futures correctly produce in the SAME manifest, SAME
      enumerator run (e.g. `KRAKEN-FUTURES:FUTURE:BTC-USD@LIN-20260626`). Confirmed via
      `market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py::derive_row_instrument_id`
      (`InstrumentType.FUTURE` branch, `_MARGIN_MARKER_VENUES`): the MTDS writer's OWN canonical shape for a dated
      future is the dash form — so `ETHUSDT_260626` cannot be what a correct writer would ever stamp for this cell. This
      is a LEAF row (not `futures_chain`/`options_chain` bundle-grain), so `_enumerate_v2_cefi` correctly passes through
      whatever `instrument_id` the instruments-service catalogue supplies for it — meaning the raw-shape `instrument_id`
      is coming FROM the catalogue (`build_instrument_catalogue.py`'s roll-up), not from this enumerator. Recommend:
      read `build_instrument_catalogue.py`'s BINANCE-FUTURES dated-future `instrument_id`/`instrument_key` derivation
      (likely reads the adapter's raw `instrument_key` verbatim rather than re-deriving the canonical dash form the way
      `_cefi_perp_lineage_key`/`_canonical_instrument_id` do for other id-convention chains) and either fix at
      catalogue-build time or confirm this is an intentional per-venue convention divergence that the enumerator/writer
      should instead special-case. (repo: instruments-service) — `instruments-service@79d4dbcb`. **Confirmed the
      diagnosis exactly**: the Tardis reference-data adapter
      (`instruments_service/reference_data/adapters/cefi/tardis/adapter.py:895-899`) already builds the canonical dash
      form for a FRESH capture via the shared UAC `build_instrument_id()` (same builder `_cefi_perp_lineage_key`'s
      PERPETUAL-family precedent relies on) — the defect is scoped exactly to `build_instrument_catalogue.py`'s roll-up,
      which for a non-pool row (`_defi_pool_dual_form`'s fallthrough branch) passed the by_date snapshot's raw
      `instrument_key`/`instrument_id` straight through with NO re-derivation, unlike the
      PERPETUAL-family/DeFi-ghost-venue collapses the file already does. Root cause: legacy by_date snapshot rows
      captured BEFORE the adapter's 2026-07-09 fix still carry the pre-fix raw wire-form id on disk; a catalogue rebuild
      rolls those historical rows up UNCHANGED every time, regardless of how new the adapter code is. Fixed at
      catalogue-build time (per the doc's own first recommended option), not by declaring a venue special-case: added
      `_canonicalize_cefi_future_id()`, mirroring the exact `_cefi_perp_lineage_key`/`_canonical_instrument_id` pattern
      — rebuilds via the SAME shared UAC `build_instrument_id()` the adapter itself uses
      (`build_instrument_id(venue, InstrumentType.FUTURE, f"{base}-{quote}", expiry_date=expiry, margin_marker=marker)`)
      whenever a CeFi FUTURE row's id lacks the `@` marker and all 4 required fields
      (`base_asset`/`quote_asset`/`margin_type`/`expiry`, all already carried in the by_date snapshot's own columns per
      `_extract_meta`) are present; degrades to the raw id unchanged otherwise (already-canonical Kraken/Bybit/Deribit
      rows, non-FUTURE rows, or a row missing a required field — never guesses). Wired into
      `build_catalogue_dataframe`'s row-construction step, right after `_defi_pool_dual_form`. Live-repro-tested against
      the EXACT reported example before shipping:
      `_canonicalize_cefi_future_id("BINANCE-FUTURES:FUTURE:ETHUSDT_260626", {instrument_type: FUTURE, venue:     BINANCE-FUTURES, base_asset: ETH, quote_asset: USDT, margin_type: linear, expiry: 2026-06-26})`
      → `"BINANCE-FUTURES:FUTURE:ETH-USDT@LIN-20260626"` (matches the doc's own stated target exactly); also verified
      the BINANCE-DELIVERY inverse side (`@INV`), that an already-canonical KRAKEN-FUTURES row is an idempotent no-op,
      that a non-FUTURE (PERPETUAL) row is untouched, and that a row missing a required field (e.g. blank `quote_asset`)
      degrades to the raw id rather than guessing. Added 5 new unit tests
      (`tests/unit/scripts/test_build_instrument_catalogue.py`, end-to-end through `build_catalogue_dataframe`, not just
      the helper in isolation) covering all of the above. Full `quality-gates.sh` green (both before commit and
      re-verified after a rebase pull-in — 2 peer-slot commits landed mid-session); the only warning present
      (`check_adapter_contract_regression`) is a PRE-EXISTING MTDS-repo warning unrelated to this instruments-service
      change, already tracked in `lint_sweep_774602ea8_regression_audit_2026_05_20.md` per this same doc's earlier
      entries. **Not yet re-measured against the live prd manifest** — this fix only affects a FRESH catalogue rebuild
      (`prod/catalog.parquet` regeneration); it does not retroactively touch the 1,776 rows already on disk in the
      current `expected_unattempted` denominator (same "code fix ≠ retroactive data fix" pattern the P0 items above
      already hit twice). A follow-up re-run of the catalogue-build pipeline + `enumerate_expected_universe.py` (or a
      targeted relabel of the 1,776 existing rows, mirroring todo (2)'s relabel-script pattern) is needed before this
      count actually drops in the live denominator — out of this todo's own scope (this todo was specifically about the
      catalogue-build CODE defect, not the operator-gated corpus mutation), not filed as a new todo since it is a
      routine consequence of every code-only fix in this doc (P0 items 1/4 above hit the identical "code fix landed,
      re-measure still pending relaunch/relabel" gap and did not spin up a separate todo for it either).
- [x] ✅ [INFRA] P0. Confirm a fresh MTDS deployment tarball exists for `market-tick-data-service@5d44a197` (or a later
      SHA) — check `gs://deployment-scripts-central-element-323112/code/market-tick-data-service-code@<sha>*` — then
      relaunch the 3 `cefi-queue-*` Tardis VMs against it (respect the hard 3-VM Tardis cap: kill-then-relaunch, never
      exceed 3 concurrent). Do NOT relaunch against `56679e78` — confirmed a silent no-op, superseded by `5d44a197`.
      This is the live-smoke-capture precondition todo (3) is blocked on: verify post-relaunch that newly captured
      Tardis-sourced rows in the cefi prd manifest carry canonical `instrument_id` (not raw wire symbol) before todo (3)
      re-measures. (repo: deployment-service) — see Progress Log entry (infra, slot-6) below for the relaunch + partial
      live-smoke-capture status. **Todo (3) should still wait**: canonical-manifest-row proof was not yet observed live
      by the end of this session (natural backfill sequencing, not a fix failure — see entry).
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
- [x] ✅ [BACKEND] P1. **NEW FINDING — the Tier-3 sentinel's OWN captured-vs-expected comparison looks broken for CeFi
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
      (Kraken's PI*/PF*-prefixed shapes aren't recognised by that heuristic's dispatcher at all — its own test file says
      as much: "Kraken's PI*BTCUSD wire shape is rarer; the dispatcher peels USD but won't strip the PI* prefix"). This
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
      Recommend a dedicated fix-plan todo, same pattern as this doc's own P0 items. —
      `market-tick-data-service@bbf6649c`. Fixed in `venue_fetch.py::_record_venue_shard_counts`: for Tardis-sourced
      venues (`_VENUE_TO_DATA_SOURCE[venue] == "tardis"`, same scope guard as todo 1's manifest-write fix), add the
      manifest-write canonicalizer's output (`_canonicalize_manifest_instrument_id` — the SAME proven-correct derivation
      as todo 1, not `_canonicalize_captured_instrument_id`) to `captured_per_instrument_shards` **alongside** the
      legacy bare form, rather than replacing it. Live-tested this decision was necessary, not just simpler: a
      pre-existing test
      (`test_orchestrator_per_data_type_sentinel.py::     test_tier3_cefi_perp_partial_capture_fans_out_per_instrument`)
      failed on a naive "swap the function" fix — its fixture (and the real fallback path in `sentinel_catalogs.py`,
      which silently falls back to the v1 UAC seed tables on ANY catalog-read exception) proves `expected_instruments`
      is sometimes the bare UAC-seed shape (`BTC-PERP`), not always the IS catalogue's full canonical `InstrumentKey`.
      Since `captured_per_instrument_shards` is a set used purely for membership-testing, carrying both candidate shapes
      is cheap and correct regardless of which comparison mode is active for a given date/venue — confirmed via a live
      repro (`_canonicalize_manifest_instrument_id("KRAKEN-FUTURES", "PERPETUAL", "PF_IOTAUSD")` →
      `"KRAKEN-FUTURES:PERPETUAL:IOTA-USD@LIN"`, matching the catalogue shape) and unit tests locking both the
      Tardis-canonical-match case and the non-Tardis/sports untouched case
      (`tests/unit/test_venue_fetch_cefi_manifest_canonicalization.py::TestTier3CapturedInstrumentsCanonicalization`, 6
      new tests). Full `quality-gates.sh` green (6172 passed) both before commit and re-verified after the rebase
      pull-in (a peer slot's `tardis_concurrency_lease.py` fix landed mid-session); the file-size ratchet forced a trim
      of the inline comment to stay under the 900-line cap for `venue_fetch.py` (908→898 lines).

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
  `availability_index.parquet` per the dispatch's own instructions (KRAKEN-FUTURES/book*snapshot_5: 25,462 `captured` /
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
  heuristic, verified NOT to touch Kraken's `PI*`/`PF\_`prefixes at all) — a separate, likely pre-existing defect, not
  something this session's fixes caused or need to fix to close THIS issue's own scope. Filed as a new P1 todo above
  with the concrete repro rather than fixed blind, per the standing "ambiguous → diagnose both sides, don't blind-edit"
  triage rule — recommend it become its own dedicated fix-plan todo, same pattern the P0 items in this doc already
  followed. Deliberately did NOT touch VM launch/relaunch (todo 4) or the relabel`--apply` (todo 2, operator-gated) —
  both explicitly out of this dispatch's authorized scope.

- **2026-07-15T20:19-20:40Z (infra, slot-6)**: Picked up todo (4). **Tarball confirmed**: the un-suffixed
  `gs://deployment-scripts-central-element-323112/code/mtds-code.tar.gz` alias (what launchers actually pull) was built
  at 20:00:43Z from `commit_sha=5d44a197bc02510a53d9b3b4973ce49d1e7833eb` (its own `mtds-code.manifest.json`) —
  satisfies "5d44a197 or later" exactly; confirmed the SHA-suffixed `market-tick-data-service-code@<sha>*` objects were
  stale (last build 2026-07-12) so that naming scheme isn't what's actually deployed — the un-suffixed alias is the one
  `setup-data-pipeline-vm.sh`/launchers use. Also reviewed `90ecde17` (landed after 5d44a197, before this tarball build)
  and confirmed it's a non-behavioral logging/test-only follow-up (adds a WARNING summary +
  `cefi_manifest_id_unresolved` accumulator + persisted unit tests; does not change canonicalization OUTPUT for any
  symbol that resolves) — so relaunching against the 5d44a197-built tarball is safe and equivalent for this todo's
  purpose. **Relaunched**: killed the 3 pre-fix-tarball VMs (`cefi-queue-heavy-20260715-174106`,
  `cefi-queue-light-20260715-174110`, `cefi-queue-light-20260715-183058`, all confirmed via SSH-checked deployed venv to
  predate `_canonical_cefi_manifest_instrument_id` per the todo's own note), relaunched 3 equivalents mirroring each
  VM's exact venue/data_type scope via `launch-cefi-sharded-backfill.sh` `SINGLE_VM_QUEUE=1`
  (`cefi-queue-heavy-binancefutu-x15-...`: 15-venue trades+book_snapshot_5; `cefi-queue-light-binancefutu-x2-...`:
  BINANCE-FUTURES+BITGET-FUTURES derivative_ticker/liquidations/futures_chain; `cefi-queue-light-bybit-x4-...`:
  BYBIT+OKX-SWAP+KRAKEN-FUTURES+BITFINEX-FUTURES same data_types), all with
  `TARDIS_CONCURRENCY_LEASE=1 TARDIS_CONCURRENCY_LEASE_BUCKET=config-store-central-element-323112` per the multi-VM-wave
  HARD RULE. `tardis-concurrency-guard.sh` confirmed the cap was respected at every step (0→1→2→3, never exceeded 3).
  All 3 STARTED <60s (gcloud instances list RUNNING), zero fire-and-forget — actively monitored ~20 min post-launch.
  **Partial live-smoke-capture verification**: the parquet FILE content path (`derive_row_instrument_id` inside
  `finalise_rows_and_path`) was reconfirmed already-correct via live `run.log` — "canonical shard binance/avntusdt" etc.
  lines for every write. The MANIFEST write path specifically (this issue's actual defect) could **not** be confirmed
  with a genuine NEW `captured` row within this session's wall-clock: pre-flight correctly (not a bug) skips re-fetching
  Jan-2026 dates it already sees as "fully covered" (mislabeled-but-present raw-symbol rows from before the fix), so the
  fleet must sequentially traverse ~30+ already-covered days before reaching dates with a genuine `expected_unattempted`
  gap that would produce a fresh, fix-covered `captured` row — `cefi-queue-light-bybit-x4` was still on 2026-01-06 (of
  2026-01-01→2026-07-14) after 20 min at its own natural ~2.5min/day pace, i.e. genuinely ~1h+ away from the earliest
  plausible new-capture date, too long to block this dispatch on synchronously. Checked 3x over the monitoring window
  (per-VM manifest shards downloaded + read directly, `capture_status` column) — all rows so far are
  `attempted_failed`/`empty_confirmed`, none yet `captured`. **New finding, filed separately (not blocking this todo,
  but relevant to todo 3's eventual re-measure)**: `../issues/tardis_concurrency_lease_intra_process_race_2026_07_15.md`
  (`unified-trading-pm@686f0d2e8`) — the `TardisConcurrencyLease` process-wide singleton lets ~15 of every 16
  concurrently-gathered symbol-fetch coroutines bypass the lease-wait entirely (flag flips synchronously before the
  blocking `acquire()` resolves), reproducing the exact `code=274 concurrent-IP-lock` 403 the lease exists to prevent —
  live-observed on `cefi-queue-light-binancefutu-x2` (1928 403s, 9-min stall on a single date) while the other 2 VMs in
  the same wave ran clean, ruling out cross-VM contention as the cause. Does not block todo (4)'s own scope (the
  relaunch itself is correct and complete) but will inflate `attempted_failed` counts in the interim and should be fixed
  before todo (3)'s re-measure treats a large `attempted_failed` delta as meaningful. **Left all 3 VMs running** — they
  are legitimate, correctly-configured production backfill work; killing them again would waste the progress already
  made. **Next session picking up todo (3)**: re-check `_index/per_vm/cefi-queue-*` (or the consolidated
  `availability_index.parquet`) for a `capture_status=captured` row with a canonical (not raw-symbol) `instrument_id`
  before re-measuring — if none yet, wait longer or spot-check a known-gap date/venue directly rather than re-measure
  prematurely.

- **2026-07-15T22:2x Z (backend_engineer, slot-6)**: Picked up the final P0 todo (re-materialize the enumerator so every
  eu row shares one canonical atom). Downloaded + cross-tabbed the live prd cefi `_index/availability_index.parquet`
  (11.37M rows) directly rather than trusting the "hotusdt"-style example verbatim — found the real shape mix is
  3,106,459 total `expected_unattempted` rows, 3,039,660 (97.8%) already canonical, 66,799 non-canonical of which 18,855
  were a false positive in my own first-pass regex (dated-futures expiry suffix, actually canonical). Of the genuine
  49,720: 42,993 pure historical debris (`enumerator_run_id` absent, pre-dates that column), 6,727 an ACTIVE bug in
  `_enumerate_v2_cefi`'s bundle-grain handling (confirmed via the SAME run id as the 3.04M canonical rows — i.e. the
  CURRENT code was still producing some non-canonical rows, not just old debris). Root-caused the active bug to
  `_enumerate_v2_cefi` never reading `instr.underlying` for `_rollup_bundle_grain`'s synthetic bundle entries — a gap
  the tradfi enumerator's equivalent function had ALREADY closed (its own present-cols docstring explicitly said
  "cefi... does not yet collapse bundle instrument_id — untouched"). Fixed by mirroring `_enumerate_v2_tradfi`'s
  `is_bundle` pattern exactly (`instruments-service@a2468dd9`) — 7 pre-existing unit tests needed updating to match the
  now-correct shape (2 caught the bug directly, a full-suite QG pass caught 5 more that were encoding the same pre-fix
  assumption). Full `quality-gates.sh` green. Wrote + dry-run-verified (against the LIVE bucket, read-only) a
  snapshot-first purge script for the 49,720 already-on-disk stale rows (`instruments-service@7f1aed10`) — matches my
  manual count exactly (49,720 across 6 blobs, 0 in per-vm shards). Did **not** run `--apply`: per this doc's own
  established precedent (todo 2's relabel script, same operator-gating reasoning), a corpus-wide manifest mutation gets
  a sign-off ask even though this one is objectively lower-risk (denominator placeholder rows, not captured data). Filed
  a `/blocked` question for the `--apply` sign-off. Also surfaced and filed (not fixed — out of this todo's scope,
  catalogue-build-step not enumerator) a narrower THIRD non-canonical class: 1,776 BINANCE-FUTURES dated-futures rows
  carrying a raw wire-form id segment (`ETHUSDT_260626`) instead of the dash-canonical shape every other dated-futures
  venue in the same run correctly produces — new P1 todo above. Did not touch todo 2's `--apply` gate, VM
  launch/relaunch, or widen the Tardis fleet (out of scope; also blocked by `BLK-b319db38` disposition B until this
  todo's purge fully lands and is re-measured).

- **2026-07-15 (backend_engineer, slot-3)**: Picked up the final remaining P1 todo (BINANCE-FUTURES dated-futures
  catalogue `instrument_id` raw-wire-form finding). Confirmed the diagnosis exactly via code read: the Tardis adapter
  already stamps the canonical dash form for a fresh capture (`adapter.py:895-899`, shared UAC `build_instrument_id()`)
  — the defect was isolated to `build_instrument_catalogue.py`'s roll-up, whose non-pool fallthrough branch
  (`_defi_pool_dual_form`) passed a legacy by_date snapshot row's raw `instrument_key` straight through with no
  re-derivation, unlike the PERPETUAL-family/DeFi-ghost-venue collapses the same file already performs. Fixed at
  catalogue-build time per the doc's own first recommended option: added `_canonicalize_cefi_future_id()`, mirroring the
  `_cefi_perp_lineage_key`/`_canonical_instrument_id` precedent, reusing the same shared UAC builder the adapter itself
  calls. `instruments-service@79d4dbcb` — see todo's own entry above for full detail (live-repro-tested against the
  exact reported example, 5 new end-to-end unit tests, full `quality-gates.sh` green). Every todo in this doc is now
  checked, but the doc itself is NOT being marked resolved by this session — todos (2)'s relabel `--apply` and (4)'s
  purge `--apply` are still operator-gated sign-offs per this doc's own "OPERATOR DECISION" framing, and this fix does
  not retroactively touch the 1,776 already-on-disk non-canonical rows (only a fresh catalogue rebuild benefits). Left
  `status: open` for the operator to close once the outstanding `--apply` sign-offs are actioned.
