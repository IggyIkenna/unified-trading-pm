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
Phase-1 (manifest-level, full v9-projected-index walk) is DONE; Phase-2 (file-level cross-year manifest-vs-reality
sampling) is IN PROGRESS via per-AG sub-agents — findings fold back into the audit doc + new todos here.

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
