---
title: "Batch+Live Shard Smoke Matrix — prove live=batch for every (asset_group × venue × data_type)"
parent_epic: batch_live_symmetry_master
assigned_vm: vm-cross-cutting
status: active
priority: P1
created: 2026-06-19
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3
locked_by: live-defi-rollout
locked_since: 2026-06-19
related_plans:
  - plans/epics/batch_live_symmetry_master.md
  - plans/active/cross_ag_shard_4pillar_validation_harness_2026_06_19.md
Codex SSOTs:
  - codex/04-architecture/shard-level-failure-isolation.md
  - codex/02-data/pipeline-mode-and-batch-live-reconciliation.md
---

# Batch+Live Shard Smoke Matrix

**Owns**: the FIRST comprehensive, repeatable batch+LIVE smoke across every `(asset_group × venue × data_type)` shard
combination — the live counterpart to the batch-only 4-pillar harness (`validate_shards_4pillar.py`). Proves the **Batch
= Live** HARD RULE per cell: BOTH the batch adapter AND the live WSFeedConnector are wired and target the SAME canonical
schema contract (`find_schema(ag, data_type)`).

**Provenance**: operator-flagged gap (2026-06-19) — only batch-shard 4-pillar had run so far; the live dimension (live
adapter/connector exercised + asserted live=batch schema) was missing.

## What the harness does

`e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py` (wired into MTDS `quality-gates.sh` STEP 5.88b as
ruff-lint + warn-only L1 smoke; comprehensive run is operator/scheduled). Per cell, two dimensions + a symmetry verdict:

- **BATCH**: batch handler present for the AG + (network) sample a stored shard → 4-pillar schema check (reuses
  `validate_shards_4pillar.check_shard`). `pass` / `no-data` / `fail`.
- **LIVE L1** (always; credential-free, network-free): a `WSFeedConnector` is registered for the venue → its factory
  instantiates a protocol-satisfying connector → a canonical `find_schema(ag, data_type)` exists. `schema-only` (wired)
  / `blocked-not-registered` / `blocked-credentials` (Databento/Odds-API) / `fail`.
- **LIVE L2** (network + credential-free public venue): `connect()` + drive `stream()` a short window → ≥1 real
  `ReceivedTick` → frame schema-symmetric with batch contract → `live=pass`.
- **SYMMETRY**: `symmetric` (both target the same canonical schema) / `divergent` / `n/a`.

Honest taxonomy — credential / market-hours / no-network cells are reported blocked, NEVER faked. L2 venue egress runs
only on a network-enabled host (the central VM / scheduled job).

## First comprehensive run (2026-06-19, central VM, GCS network on)

3401 cells across all 5 AGs. **BATCH**: 754 pass, 0 fail, 2647 no-data (handler wired, no sampled stored shard for that
exact data_type). **LIVE**: 339 L1-wired, 50 blocked-credentials (TradFi Databento + Sports Odds-API), 3012
blocked-not-registered (cross-product venues with no live stream), **0 live-fail**. **SYMMETRY**: 135 symmetric, **0
divergent**. L2 verified end-to-end with a real Binance-spot trades tick (`live=pass`, columns
`price/side/size/symbol/trade_id/ts_ms/venue`, symmetric). Per-AG: cefi 76 batch-pass / 56 live-wired; defi 620 / 275;
prediction 2 / 8; sports 16 / 0 (10 blocked-cred); tradfi 40 / 0 (40 blocked-cred Databento).

## Todos

- [x] ✅ [SCRIPT] P0. Build the batch+live smoke matrix harness
      `e2e-testing/scripts/validation/validate_batch_live_smoke_matrix.py` — enumerate UAC
      `VENUES_BY_ASSET_GROUP × DATA_TYPES_BY_ASSET_GROUP`, per-cell batch (4-pillar reuse) + live (L1
      registry/protocol/canonical-schema + L2 short live window) + symmetry verdict; honest blocked taxonomy, never a
      fake live pass. — e2e-testing@c92d50f | ruff clean | QG-green
- [x] ✅ [SCRIPT] P0. RUN the matrix across all 5 AGs on the central VM (GCS network on) → 754 batch-pass / 0
      batch-fail, 339 live-wired / 50 blocked-cred / 0 live-fail, 135 symmetric / 0 divergent; L2 real Binance-spot tick
      proven. — e2e-testing@c92d50f
- [ ] [SCRIPT] P0. **BLOCKED-DEP** Wire as a repeatable smoke — MTDS `quality-gates.sh` STEP 5.88b (ruff-lint + warn-only
      L1 `--smoke`), mirroring STEP 5.88's 4-pillar wiring. **DONE in the working tree + MTDS QG-green (sentinel == HEAD
      `b9a8d79`, the 5.88b block ran clean inside the gate); ship via quickmerge is BLOCKED on a FOREIGN dirty dep** —
      `unified-trading-library` carries 3 uncommitted source edits (test_honest_coverage_ratchet / core/asset_group /
      honest_coverage_ratchet) from another agent's in-flight work on the shared central VM, and quickmerge's pre-flight
      refuses to build against a dirty dep (correct — never quickmerge with dirty deps). Lands the moment UTL is clean:
      `cd market-tick-data-service && bash scripts/quickmerge.sh "ci(quality-gates): wire     batch+live smoke matrix STEP 5.88b" --agent --files 'scripts/quality-gates.sh'`.
      The block is purely the shared-host foreign-dep state, not my change. — market-tick-data-service (working tree
      ready, QG-green)
- [ ] [SCRIPT] P2. **NICE-TO-HAVE** Add catalog-aware live-instrument discovery to L2 so the network-enabled scheduled
      run gets a real tick for prediction/DeFi-polling venues (not only Binance) — today L2 uses a best-effort
      `_representative_instrument` map; a real `clob_token_id`/condition_id discovery would upgrade more cells from
      `schema-only` → `pass`. Provenance: 2026-06-19 build; L2 needs the per-venue rollout's instrument enumeration.
      Target repo: market-tick-data-service (connector) + e2e-testing (harness).
- [ ] [SCRIPT] P2. **NICE-TO-HAVE** Schedule the comprehensive run (`--live-window 8` + GCS sampling) as a recurring job
      on the central VM (network-enabled) so the L2 runtime-tick dimension runs continuously, not only L1 in QG.
      Provenance: 2026-06-19; QG is network- free so only L1 runs there. Target repo: deployment-service (scheduler) +
      e2e-testing.

## Temporary states + their canonical follow-up plans

- L2 runtime-tick coverage is L1-only in QG (network-free) + Binance-proven on the central VM; full
  L2-across-credential-free-venues is the two P2 NICE-TO-HAVE todos above (named successor = this plan). Credential
  venues (Databento/Odds-API) stay `blocked-credentials` until the keys land — tracked by the existing credential asks,
  not re-deferred here.
