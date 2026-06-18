---
title: Instruments ↔ MTDS subset + consistency remediation
created: 2026-06-17
parent_epic: instruments_master
assigned_vm: vm-operator-ops
status: active
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6.4
locked_by: live-defi-rollout
locked_since: 2026-06-17
source:
  - plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md (findings F1–F7, full-index walk)
  - operator 2026-06-17 (deep-dive audit dispatch)
---

# Instruments ↔ MTDS subset + consistency remediation

> **🔴 PRE-`--apply` BLOCKER GATE (2026-06-17).** The dry-run projections that `--apply` will materialise STILL carry
> these defects, and a reconcile `--apply` over uncovered path shapes flips real `captured`→`attempted_failed`
> (CLAUDE.md hard rule). **Do NOT `--apply` until these are fixed + the projection regenerated + re-eyeballed:**
> (1) **prefix_tpls coverage** — prove `ASSET_GROUP_CONFIG[ag]["prefix_tpls"]` covers ALL coexisting shapes
> (`category=`/`asset_group=`/bare/`pipeline_mode=`, see N7) per AG BEFORE apply; (2) **N6** normalize defi
> chain/venue/instrument_type pollution (apply migrates BY these values); (3) **N1** confirm dedup keeps the captured
> row, not the empty shadow; (4) **N3** recover sports league_id into the manifest first (else null-league is permanent);
> (5) **N5** verify the phantom-reconcile targets only true 0-row pre-launch vault cells. NON-blocking (fix after/parallel):
> F1, F3, N2, N4, F6, N8. **Apply order: pred → tradfi (clean) → cefi → sports → defi; never all-AG at once.**

Findings of record + method: `plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md`.

> **🟢 SCRIPT-COVERAGE MAP (2026-06-17) — every blocker is a GAP in the existing rebuild scripts, not unscripted.** The
> rebuild scripts ARE the migration: fix the gap → regenerate the dry-run projection → improved beta → `--apply`
> (path-schema) → backfills. Per finding: **prefix_tpls** ✅ `canonical_path_templates(ag)` covers all shapes (sports
> `[""]` — verify only); **N3** ⚠️ `rebuild_sports_manifest_v9` never extracts `league_id`/`league` from the MTDS object
> path into the row_key (canonicalizer `_canonicalize_row_key_league_id` then gets null); **N1** ⚠️ `rebuild_cefi`
> CF-11 dedup key mismatches (empty re-emit has blank `instrument_type` vs captured populated → both survive); **N5** ❌
> `rebuild_defi` emits `captured`/row_count=0 on file PRESENCE without opening (0-row/pre-launch → false captured) →
> route via `record_zero_rows`; **N6** ⚠️ `rebuild_defi._split_legacy_venue_chain` lacks instrument_type case-norm +
> lets pairs leak into `chain` + incomplete venue-dedup; **F3** ❌ `rebuild_cefi` passes legacy
> `attempted_failed` reasons through un-reclassified; **N2** ❌ instruments enumerator marks CME weekend carry-forward
> as `SOURCE_RETURNED_ZERO`. **Each Phase-A/B/D todo below = a scoped fix to the named script → regen that AG's
> dry-run projection → re-audit the fixed dimension.**
Phase-1 (manifest-level, full v9-projected-index walk) is DONE; Phase-2 (file-level cross-year manifest-vs-reality
sampling) is IN PROGRESS via per-AG sub-agents — findings fold back into the audit doc + new todos here.

## Execution sequence (end-to-end — the autonomous worker drives this in order)

Each script-fix step = fix → `quality-gates.sh`-green → `quickmerge --agent --files` → **regenerate that AG's dry-run
projection** (`rebuild_{ag}_manifest.py --dry-run --projection _index/audit/projected_index_{ag}.parquet`) → **re-audit
the fixed dimension** (the `/tmp/audit_subset.py` pattern or a per-AG file re-check) → flip the todo + journal before/after
numbers. Order:

1. **CeFi script** `rebuild_cefi_manifest.py` — **N1** dedup key (captured suppresses its blank-type empty shadow) + **F3**
   reclassify legacy `attempted_failed` recon-noise (~1.3M) vs keep genuine ~88k. Verify: no captured+empty double-rows;
   attempted_failed → ~88k.
2. **Sports script** `rebuild_sports_manifest_v9.py` — **N3** extract `league_id`/`league` from the MTDS object path +
   row column into the row_key (BEFORE `_canonicalize_row_key_league_id`); stamp `source` on `trades`; collapse
   API_FOOTBALL/`api_football`. Verify: captured cells carry league_id.
3. **DeFi script** `rebuild_defi_manifest.py` — **N6** normalize instrument_type case (pool/POOL), keep pool-pairs OUT of
   `chain` (only known chain tokens), collapse venue dups; **N5** route 0-row/pre-launch files through
   `DefiManifestRecorder.record_zero_rows` (venue-launch-date-aware) instead of presence⇒captured. Verify: no token-pairs
   in chain, single-case instrument_type, no pre-launch captured-0-row vault cells.
4. **Instruments enumerator** (instruments-service) — **N2** CME/TradFi weekend carry-forward = honest carry-forward (not
   `SOURCE_RETURNED_ZERO`); de-dup 2×-per-cell index rows.
5. **prefix_tpls VERIFY** (`reconcile_phantom_manifest_rows_all.py` `ASSET_GROUP_CONFIG`) — prove
   `canonical_path_templates(ag)` enumerates EVERY coexisting shape per AG (`category=`/`asset_group=`/bare/`pipeline_mode=`)
   against real GCS prefixes; replace the sports `[""]` with real templates. **APPLY FOOT-GUN — uncovered shape ⇒ apply
   flips real captured→attempted_failed.** Block apply for any AG whose coverage isn't proven.
6. **Regenerate ALL projections → re-audit** = the IMPROVED beta. Confirm F1–F7 + N1–N8 resolved/honestly-classified;
   record before/after in the audit-doc Progress Log.
7. **PRE-MIGRATION DRAIN GATE (HARD, CLAUDE.md)** — before ANY `--apply`: gracefully stop ALL running VMs (GCP+AWS) + run
   the manifest consolidator + snapshot `_index/snapshots/pre_migration_<date>.parquet`
   (`code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2.0 Stage 0).
8. **`--apply` AG-by-AG, safest first: pred → tradfi → cefi → sports → defi.** Per AG: prefix_tpls green + projection
   re-audited clean → run the real path-schema migration → verify the live `_index` matches the projection (NO mass
   captured→failed flip) → next AG. **Never all-AG at once.** Mass-flip ⇒ STOP + diagnose prefix_tpls, do not continue.
9. **Backfills** — F1 (Kraken+ instruments history), the ~88k genuine cefi `VENUE_FETCH_FAILED`, any real captured-absent
   cells. Run to completion (manifest-verified rows).

**Gates / hard-stops:** `--apply` is operator-DISPATCHED (authorized) but each AG is gated on (5)+(6)+(7) green; a red
gate ⇒ STOP+document, don't apply that AG. Genuine human hard-stops unchanged: live wallet keys, `1.0.0` graduation.

## Phase A — subset violations (MTDS data with no instrument backing)

- [ ] [DATA] P1. **F1 — backfill instruments-service for CEFI venues MTDS has but instruments lacks historically**:
      `KRAKEN-SPOT`/`KRAKEN-FUTURES` (added to instruments only at day=2026-06-17 — ~6yr gap), `LIGHTER-ZKSYNC`,
      `PACIFICA-SOLANA`, `EXTENDED-STARKNET`. Re-run the IS daily-listing CLI across the MTDS-covered date range per
      venue (never copy between dates). Verify the cefi (venue,date) subset closes. — instruments-service
- [ ] [DATA] P2. **F2 — backfill 5 missing BITGET-FUTURES + 5 BITGET-SPOT instrument-days** that MTDS captured but
      instruments is absent for. — instruments-service
- [ ] [DATA] P1. **F4 — SPORTS: 2,107 captured MTDS cells with NULL `league_id`** (odds_horizon_bucket/trades/ODDS).
      Diagnose whether the league mapping drops on write or we capture non-canonised leagues; stamp league_id or route
      to honest-absence. No sports market data may be captured for a non-canonised league. — market-tick-data-service
- [ ] [DATA] P3. **F7 — DEFI: 19 Ethereum MTDS cells pre-instruments-genesis (2020-01-01..19)**. Confirm instruments
      defi genesis should start earlier, or mark those MTDS cells spurious. — instruments-service

## Phase B — instruments internal consistency

- [ ] [DATA] P0. **F3 — CEFI: 1.40M `attempted_failed` MTDS cells (36%)**. Break down by venue×data_type; diagnose the
      failing adapters/venues; backfill. (Data-pipeline-correctness heartbeat — no deferral.) — market-tick-data-service
- [ ] [CODE] P2. **F6 — TRADFI: 182k blank `instrument_type` + thin options (`options_chain` 3,287 vs `futures_chain`
      15,875)**. Phase-2 sub-agent opens tradfi instruments files to confirm whether options ARE listed but not captured
      (the "we list options but have no options data" case); fix the instrument_type stamping + close the options
      capture gap if real. — market-tick-data-service / instruments-service
- [ ] [DATA] P2. **F5 — SPORTS INSTR index hygiene: 6,869 blank `capture_status` rows + a literal `date='all'`** in
      instruments-store-sports `_index`. Clean in the canonicalisation walk (classify the blanks; drop/repair the
      non-date row). — instruments-service

## Phase C — file-level verification (Phase-2 sub-agents)

- [x] ✅ [AUDIT] P1. **Cross-year file sampling per AG — DONE** (5 per-AG sub-agents opened real GCS parquets across
      2020/2023/2026). Reframes + new findings folded into the audit doc + Phase D below. Reframes: **F3** cefi
      attempted_failed is ~1.3M legacy-recon NOISE + only ~88k genuine fetch-failure (not 1.4M); **F6** options ARE
      captured (CME 8,602 opts/day, ES options_chain 20,956 rows) — the "thinness" is a typing artifact, REFUTED;
      **F5** `date='all'` (2 rows) is by-design reference entities. Discarded one false sub-agent claim (cefi≠tradfi).

## Phase D — file-level correctness findings (Phase-2 sub-agents, NEW)

- [ ] [DATA] P1. **N1 — CEFI phantom `empty_confirmed` shadow rows** (~61,300, 57% of real-shard empties): two manifest
      rows per cell (captured + bogus empty_confirmed w/ blank instrument_type) where the parquet exists with rows (e.g.
      AVAXUSDT 2021-01-01 BINANCE-FUTURES = 943,196 rows but flagged empty). De-dup the empty shadow in the
      canonicalisation walk; the captured row + GCS file are truth. — market-tick-data-service
- [ ] [DATA] P1. **N2 — TRADFI CME weekend dishonest-empty**: all 333 CME `SOURCE_RETURNED_ZERO`/empty dates are
      Saturdays, but instruments writes a weekend carry-forward snapshot to GCS (11,526 rows incl 7,364 options) → ~1,079
      dishonest-empty cells; INST index rows duplicated 2×/cell. Fix the weekend honest-absence classification +
      de-dup. — instruments-service
- [ ] [DATA] P0. **N3 — SPORTS league_id dropped by the consolidator (100% of captured)**: all 202,087 captured
      MTDS-sports cells have NULL `league_id` though the GCS path (`league_id=BUNDESLIGA`) + row-level column ARE
      populated. Propagate per-file league_id into the manifest row. ALSO stamp `source` on MTDS sports `trades` (73.7k
      NULL — violates source= rule) + collapse venue case-dup API_FOOTBALL/`api_football`. — market-tick-data-service
- [ ] [DATA] P2. **N4 — SPORTS instruments `instrument_count==0` on 194,356 captured rows** (per-league companion rows;
      global count lands on one row). Confirm against shard grain; fix count attribution. — instruments-service
- [ ] [DATA] P1. **N5 — DEFI temporally-impossible `vault_share_price` captured phantoms** (1,582 cells 2020–2023: MAKER
      pre-2023, ETHENA pre-Feb-2024-launch; 2020-01-01 VAULT opened 0-row). These are captured-but-empty pre-launch
      phantoms → reclassify to honest pre-launch absence (venue-launch-date-aware `record_zero_rows`). — market-tick-data-service
- [ ] [CODE] P1. **N6 — DEFI dimension pollution / normalization**: `chain` column contains token-pair symbols
      (`1INCH-ETH`/`ETH-USDC`/`WSTETH-ETH`); `instrument_type` case-dup `pool`(227,935)/`POOL`(158,431); `venue` dups
      (CURVE vs CURVE-ETHEREUM, MORPHOVAULTS vs MORPHO_VAULTS vs MORPHO-ETHEREUM). Normalize at write + in the
      canonicalisation walk so per-dimension grouping/denominators are correct. — market-tick-data-service
- [ ] [DATA] P0. **F3 (reframed) — CEFI: re-classify ~1.3M legacy-recon `attempted_failed` rows**
      (`LegacyBlankErrorReasonError` 763k + `LEGACY_THIRDKEY_DRIFT_RECON` 452k + `WITHIN_BOUNDS_EMPTY_RECLASSIFIED` 90k) in
      the canonicalisation walk, AND backfill the ~88k GENUINE `VENUE_FETCH_FAILED`+`HTTP_429` cells. — market-tick-data-service
- [ ] [CODE] P2. **F6 (reframed) — TRADFI option/instrument_type encoding**: unify the two options encodings
      (`instrument_type=options_chain` vs `data_type=options_chain` w/ blank type) + stamp instrument_type on the 182k
      blank-type cells (legacy path shapes). Not missing data — a typing fix. — market-tick-data-service
- [ ] [INFRA] P3. **N7 — pipeline_mode migration tail** (dual `asset_group=`+`category=` keys; missing
      `pipeline_mode=` partition; pred captured-max day only in bare shape). Cross-link to the pipeline_mode migration
      plan — do NOT re-open here; track that the v9 `--apply` closes it. — (pipeline_mode migration plan)
- [ ] [DATA] P3. **N8 — PRED index data_type label drift** (`prediction_canonical_question_group` vs GCS
      `prediction_trades`/`trades`) + 1 blank-reason attempted_failed cell. Confirm intentional rollup label vs drift;
      type the blank reason. — market-tick-data-service
- [ ] [DATA] P1. **N1b — CEFI: reconcile the ~698k `UNCLASSIFIED_ADAPTER_ERROR` (ex-`LegacyBlankErrorReasonError`,
      blank-itype) attempted_failed cells against the IS expected-universe (Step 4 enumerator) + reconcile (Step 8)**:
      cells the enumerator marks `expected_unattempted` (instrument not listed / pre-coverage) should drop the stale
      failed row; genuine in-coverage listed-instrument gaps stay attempted_failed → backfill (Step 9). DEPENDS on Step 4.
      (Provenance: Step-1 fix kept them visible rather than hide a gap; final fate is enumerator+reconcile-driven.) — market-tick-data-service
- [ ] [DATA] P2. **N3a — SPORTS: 32,707 captured cells genuinely NULL-league in the LIVE index** (schema_version=8;
      venue=bookmaker/ODDS_API, data_type=trades/ODDS/odds_horizon_bucket). The Step-2 fix recovered the 169,380 cells that
      HAD league; these 32,707 lost it at WRITE time. Recover league_id by joining each null-league captured (date,venue,
      data_type) to the GCS object paths (`league_id=<L>`) for that cell — needs a sports object scan (the rebuild is
      index-driven). No sports market data may be captured for an unattributed league. — market-tick-data-service
- [ ] [DATA] P3. **N3b — SPORTS: 6 captured cells still NULL source** (ARBITRAGE_OPPORTUNITY/ODDS_MOVEMENT/ODDS_SNAPSHOT,
      2 each) after the Step-2 `trades→odds_api` + case-insensitive bridge. Add these MDPS-derived data_types to the
      source bridge (or route to honest absence if not genuinely captured). — market-tick-data-service
