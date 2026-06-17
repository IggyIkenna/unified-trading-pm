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

- [ ] [AUDIT] P1. **Complete cross-year file sampling per AG** (operator's explicit ask): open sampled instruments +
      MTDS parquets across venue×data_type×instrument_type×chain×league and ≥3 far-apart years; verify captured⇒rows,
      empty⇒no-file, and instruments-file types match MTDS capture. Fold findings into the audit doc; add todos for new
      gaps. — e2e-testing / data audit
