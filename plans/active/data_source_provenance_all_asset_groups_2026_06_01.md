---
title: Data-source provenance enforced across all asset groups (source column + SOURCE_PRIORITY)
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
priority: P0
status: active
estimate_class: infra
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 8
created: 2026-06-01
locked_by: live-defi-rollout
locked_since: 2026-06-01
completion_gates:
  code: C5
  deployment: D3
  business: B4
repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: features-service
    code: C0
    deployment: none
    business: none
related_plans:
  - plans/epics/mtds_mdps_master.md
  - plans/active/tradfi_massive_dual_source_2026_05_28.md
  - plans/epics/defi_master.md
  - plans/epics/sports_master.md
---

# Data-source provenance enforced across all asset groups

> **🟡 CROSS-PLAN COORDINATION — no third DeFi `_index` walk (2026-06-01)**: the `source`-column backfill onto existing
> DeFi manifest rows must NOT open its own whole-corpus walk on `market-data-tick-defi-prd-…`. Two plans already
> contend for that `_index`: `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` (`--manifest-only` seed)
> then `defi_manifest_canonicalisation_2026_06_01.md` (`C0` single-walk, runs second). Single-walk discipline (HARD
> RULE): this plan's DeFi `source` backfill **rides defi_manifest's C0 single-walk**, gated until C0 is GREEN. Code
> changes here (UAC `source` column + UTL `record_captured` + MTDS/features writers) are unblocked now; only the
> existing-row DeFi backfill is sequenced. Other asset_groups (tradfi/cefi/sports) are independent. Coordination owner:
> epic `mtds_mdps_master`. Banner-remove when defi_manifest C-GREEN + this plan's DeFi backfill folded into that walk.

## Overview

TradFi shipped a dual-source provenance model (`tradfi_massive_dual_source_2026_05_28.md`): a shard
(`data_type × venue × time`) may be populated by more than one vendor over time, **co-mingled on the same hive drop**
and disambiguated by a **row-level `source` column** + a per-source manifest row, resolved downstream via UAC
`SOURCE_PRIORITY`. Operator decision 2026-06-01: **`source` stays a column, not a hive path key** — better for
batch/live symmetry and single-walk discipline.

**This concern is crosscutting, not TradFi-only.** Every asset group except prediction realistically gets the same
logical metric from >1 source over time. The crosscutting audit (2026-06-01, see § Audit findings) found the root
cause: **`SOURCE_PRIORITY` already declares multi-source lists for cefi / defi / sports, but the `source` field is only
*enforced* and only *wired downstream* for `category=="tradfi"`.** Everyone else writes `source=""` with no gate and no
read-time reconciliation — so two sources for one cell silently collapse (last-write-wins) or double-count.

## Design decision (SSOT for this plan)

The enforcement gate must be **driven by `SOURCE_PRIORITY`, not by a hardcoded asset_group list**. Generalize the
existing TradFi gate (`manifest_writer.py` `if category == "tradfi" and not source`) to:

> **Raise `MissingSourceError` when `SOURCE_PRIORITY[(asset_group, data_type)]` has >1 entry and `source` is blank.**

This auto-covers tradfi + the multi-source cells of cefi/defi/sports, and auto-exempts single-source cells and
prediction (Polymarket/Kalshi are separate **venues**, not sources — multi-source is N/A there by design). No asset_group
list to maintain; the registry is the SSOT.

## Audit findings (2026-06-01 crosscutting sweep — the exposed gaps)

| Asset group | Multi-source reality | `source` recorded | Enforced | Downstream resolves | Status |
| ----------- | -------------------- | ----------------- | -------- | ------------------- | ------ |
| TradFi      | databento + massive (+ yahoo/barchart VIX) | ✅ v9 column | ✅ tradfi gate | ✅ SOURCE_PRIORITY | GREEN (verify-in-prod via audit items h–o) |
| DeFi        | **strongest**: oracle (pyth_hermes+chainlink), native_staking (solana_rpc+helius_rpc), APR/rates (DefiLlama vs subgraph vs on-chain) | ❌ writers route via `add()`, never pass source | ❌ | ❌ dead code | **RED** — last-write-wins collapses divergent values silently |
| CeFi        | Tardis archive vs per-venue live/REST for same (data_type, venue) | ❌ source="" | ❌ | ❌ | **RED** |
| Sports      | api_football + footystats (FIXTURES); multi-book odds | ❌ source="" | ❌ | ❌ | **RED** |
| Prediction  | Polymarket/Kalshi are separate venues; dispersion is cross-venue at feature level | n/a (correct) | n/a | n/a | GREEN — N/A by design |

## Phased execution

### Phase 1 — UAC + UTL: registry-driven source gate (P0, foundation)

- [ ] [UAC] P0. Generalise the source-enforcement rule to be SOURCE_PRIORITY-driven: expose a helper
      `source_required(asset_group, data_type) -> bool` returning True when `SOURCE_PRIORITY[(asset_group, data_type)]`
      has >1 entry. `unified-api-contracts/.../canonical/crosscutting/source_priority.py`.
- [ ] [UTL] P0. Replace the hardcoded `if category == "tradfi" and not source` gate with
      `if source_required(category, data_type) and not source: raise MissingSourceError(...)`.
      `unified-trading-library/.../manifest_writer.py:2426`. Keep single-source + prediction cells exempt.
- [ ] [TEST] P0. Extend `unified-trading-library/tests/unit/test_manifest_writer_source.py`: multi-source cefi/defi/sports
      cells without `source=` MUST raise; single-source + prediction cells MUST NOT raise; both sources on one cell
      produce two manifest rows.

### Phase 2 — DeFi writer rewiring (P0, biggest gap)

- [ ] [UTL] P0. `DefiManifestRecorder.record_captured()` must accept `source: str` and route through
      `ManifestWriter.record_captured()` (currently routes through legacy `add()` which drops source).
      `market-tick-data-service/.../cli/handlers/_defi_manifest.py`.
- [ ] [MTDS] P0. Thread `source=` through every DeFi handler call site (oracle_prices, native_staking_rates,
      lending_indices, dex_swaps, dex_pools, evm_defi, solana_defi, +others). Source string = the actual provider used
      for that fetch, from the SOURCE_PRIORITY closed set. `market-tick-data-service/.../cli/handlers/*.py`.
- [ ] [MTDS] P0. Oracle + staking handlers already resolve per-row pipeline_mode at the callsite — stamp the matching
      `source` (`pyth_hermes`/`chainlink`, `solana_rpc`/`helius_rpc`) on each row in the same place.
- [ ] [AUDIT] P1. Features-service DeFi onchain calculators — audit every emit that touches a DeFi data_type and confirm
      source is stamped. `features-service/.../onchain/`.

### Phase 3 — CeFi writer source (P1)

- [ ] [UAC] P1. Expand CeFi `SOURCE_PRIORITY` entries from sole `tardis` to ordered multi-source lists where a live
      per-venue path exists (e.g. `["<venue>_live", "tardis"]` for funding/marks/ticks). `source_priority.py:148`.
- [ ] [MTDS] P1. Thread `source=` (`tardis` vs `<venue>`) through CeFi adapter writes + extend
      `record_empty_for_shard`/`record_failed_for_shard` to accept + forward `source`.
      `market-data-processing-service/.../core/canonical_writer.py`.
- [ ] [TEST] P1. CeFi multi-source unit test: tardis + venue_live on the same cell → two manifest rows, resolved by
      priority at read time.

### Phase 4 — Sports writer source (P1)

- [ ] [MTDS] P1. Thread `source=` through Sports adapter writes (api_football / footystats / odds_api / understat).
      `market-tick-data-service/.../market_interface/adapters/sports/`.
- [ ] [TEST] P1. Sports multi-source unit test (same fixture from api_football + footystats → two rows, primary resolved).

### Phase 5 — Downstream reconciliation wired for all multi-source asset groups (P0 correctness)

- [ ] [TEST] P0. Prove the consumer read path resolves source priority for **cefi/defi/sports** (not just tradfi):
      2-source fixture (same instrument+ts from two providers, co-mingled in one folder) → consumer emits exactly ONE
      resolved row via `select_primary_available_source()`. No silent double-count. Cover features-service consumers.
- [ ] [UAC] P1. Confirm `detect_dual_source_conflicts()` is invoked at consolidation/audit time for every multi-source
      asset group; `DUAL_SOURCE_DUPLICATE`/`VALUE_DIVERGENCE`/`COVERAGE_DIVERGENCE` surfaced, never swallowed.

### Phase 6 — QG + audit instructions + codex (P1)

- [ ] [QG] P1. Generalise QG STEP 5.64 (currently tradfi-only `source` kwarg check) to fire for any multi-source
      `(asset_group, data_type)` per `source_required()`. Wire into MTDS + MDPS `quality-gates.sh`.
- [x] ✅ [AUDIT] P1. Add a **Dual-source provenance** section to ALL per-epic audit instruction files: `tradfi_master`
      (items h–o), `cefi_master` (i–l), `sports_master` (h–j, incl. path→column migration finding), `predictions_master`
      (h–j, N/A-by-design invariant), `defi_master` (n1–n4, strongest multi-source case), `mtds_mdps_master` (Mode 1 item
      j, write-time stamping), `manifest_master` (item i, the `source`-column schema home + registry-driven gate). The
      defi/mtds_mdps/manifest edits were layered on top of an in-flight "zero-rows = silent lie" sweep (operator-acked
      2026-06-01 as ready-to-ship → bundled).
- [ ] [CODEX] P1. Generalise `codex/02-data/contracts-scope-and-layout.md` § "TradFi canonical schema — dual-source
      source column" + `honest-absence-downstream-handling.md` multi-source consumer policy to all multi-source asset
      groups (currently scoped to tradfi).
- [ ] [PREDICTION] P2. Document in codex that prediction is multi-source-N/A by design (venue ≠ source); when Kalshi
      lands it is a **venue addition**, not a second source of a Polymarket shard. (From prediction audit — not a gap.)

### Phase 7 — Prod data-state verification (P1, post-enforcement)

- [ ] [AUDIT] P1. After enforcement lands, read ACTUAL `source` column distribution per (asset_group, venue, data_type)
      in prod manifests/parquets — confirm zero blank source on multi-source cells. Data-state, NOT constant (manifest-v8
      lesson: constant said 8 while 0% of rows were v8). Report per-cell source histogram.

## Out of scope (deferred — named successors required)

- Backfilling historical cefi/defi/sports parquets with retroactive `source` stamps (analogous to the TradFi
  `backfill_tradfi_source_column.py` Phase 5). File a `<asset_group>_source_backfill_<date>.md` successor if/when a
  multi-source second provider actually starts writing a previously single-source cell.

## Codex SSOTs

- `codex/02-data/contracts-scope-and-layout.md` — generalise dual-source `source` column section beyond tradfi
- `codex/02-data/honest-absence-downstream-handling.md` — generalise multi-source consumer policy
- `codex/02-data/availability-manifest-and-data-status.md` — `source` field semantics across asset groups

## Provenance

Crosscutting data-source provenance audit run 2026-06-01 (slot 1, operator-directed). Four parallel read-only audits
(cefi/defi/sports/prediction) + the prior tradfi exploration. Operator directive: provenance must be auditable across
**all** asset groups, gaps exposed, PM active todos created.

> **🟡 DRAINED-WRITER DEPENDENCY (2026-06-01)** — the legacy-bucket SSOT remediation drained writer VMs
> `mdps-backfill-defi` / `mdps-prediction-2025` / `sports-scheduler`. They must NOT be relaunched until the
> legacy→canonical migration + manifest work complete. SSOT + relaunch gate:
> `plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` Phase 4.
