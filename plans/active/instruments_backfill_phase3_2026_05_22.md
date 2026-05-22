---
name: instruments_backfill_phase3
title: "Instruments-service catalogue forward-fill — Phase 3 per-asset-group"
type: active
parent_epic: instruments_master
assigned_vm: vm-cefi
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
status: active
priority: P0
created: 2026-05-22
last_updated: 2026-05-22
gate: Phase 2 freeze lifted + instruments_master Phase A-E preflight GREEN
---

# Instruments-service catalogue forward-fill — Phase 3 per-asset-group

Unpacks `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 3.1 into per-asset-group items.
Instruments-service is the source-of-truth for reference data for ALL downstream pipelines (MTDS, features, strategy).
All 5 asset groups must be live before MTDS backfill VMs launch.

**Gate**: `instruments_master` Phase A-E preflight items GREEN before launching any live-activation VM. **Sequencing**:
instruments forward-fill → MTDS backfill (`mtds_backfill_phase3_2026_05_22.md`) → MDPS reprocessor → features compute.

---

## Phase 1 — CeFi instruments forward-fill

- [ ] [SCRIPT] P0. **IS-3.1.CeFi** — Launch instruments-service CeFi live-activation VM per `instruments_master` Phase
      F-CeFi. Venues: Bybit / Binance / OKX / Bitfinex / Bitget / Kraken / Deribit / Hyperliquid / Aster. Cloud
      Scheduler driver (15-min cadence). Per-VM shard isolation (`MANIFEST_PER_VM_SHARDS=true`). Watch event-stream
      T+10min per CLAUDE.md "No fire-and-forget".
- [ ] [VERIFY] P0. **IS-3.1.CeFi-V** — Post-launch: `instruments-store-cefi-prd` gains new rows; `available_at`
      populated; 0 `attempted_failed` after first poll cycle.

## Phase 2 — DeFi instruments forward-fill

- [ ] [SCRIPT] P0. **IS-3.1.DeFi** — Launch instruments-service DeFi live-activation VM per `instruments_master` Phase
      F-DeFi. Venues: Uniswap V3 / Curve / Aave / Compound / Lido / RocketPool / Chainlink / Pyth / on-chain contract
      discovery. 15-min cadence + event-driven trigger on new pool.
- [ ] [VERIFY] P0. **IS-3.1.DeFi-V** — `instruments-store-defi-prd` gains rows; 0 attempted_failed.

## Phase 3 — TradFi instruments forward-fill

- [ ] [SCRIPT] P0. **IS-3.1.TradFi** — Launch instruments-service TradFi live-activation VM per `instruments_master`
      Phase F-TradFi. Venues: Polygon.io (NASDAQ/NYSE equities + CME futures) + Yahoo (VIX / macro indices). 15-min
      Polygon + rolling 60d Yahoo per CLAUDE.md VIX-15m rule.
- [ ] [VERIFY] P0. **IS-3.1.TradFi-V** — `instruments-store-tradfi-prd` gains rows; VIX instrument present; honest-gap
      coverage for pre-Polygon dates.

## Phase 4 — Sports instruments forward-fill

**Gate**: `sports_master` Phase 3 rename (data_available_at → available_at) shipped.

- [ ] [SCRIPT] P0. **IS-3.1.Sports** — Launch instruments-service Sports live-activation VM per `instruments_master`
      Phase F-Sports. Trigger-driven: daily fixture re-poll + season-roll + transfer-window + weather. Sources: af / fs
      / sfi / us.
- [ ] [VERIFY] P0. **IS-3.1.Sports-V** — `instruments-store-sports-prd` gains rows; `fixture_id` field populated; sports
      rename confirmed absent (no `data_available_at` stragglers).

## Phase 5 — Predictions instruments forward-fill

- [ ] [SCRIPT] P0. **IS-3.1.Pred** — Launch instruments-service Predictions live-activation VM per `instruments_master`
      Phase F-Pred. 15-min market-discovery cadence. Sources: Polymarket + Kalshi. `canonical_question_group` rekey
      already shipped (Phase 2.2 of freeze plan).
- [ ] [VERIFY] P0. **IS-3.1.Pred-V** — `instruments-store-pred-prd` gains rows; question groups canonicalized; 0
      attempted_failed.

---

## P3 lint backlog (absorbed from unused_import_audit_2026_05_18)

- [ ] [AGENT] P3. Fix F401 unused imports in `instruments-service/tests/scripts/test_canonicalize_defi_manifest_data_types_2026_05_16.py` (`contextlib`, `os`, `tempfile`, `pytest`) and `instruments-service/tests/scripts/test_reconcile_lending_indices_phantom.py` (`pytest`). Run `ruff check --select F401 --fix <files>` after verifying git status is clean. Issue: `plans/archive/issues/unused_import_audit_2026_05_18.md`.

## Temporary states + their canonical follow-up plans

- Items gated on `sports_master` Phase 3: **BLOCKED-UPSTREAM** until rename shipped; track in `sports_master` epic
  directly.
