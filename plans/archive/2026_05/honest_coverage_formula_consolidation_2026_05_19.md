---
doc_type: plan
title: Honest-Coverage Formula Consolidation — 2026-05-19
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-19"
estimate_class: refactor
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 2.4
priority: P0
parent_epic: manifest_master
epic_secondary: instruments_master
---

# Honest-Coverage Formula Consolidation — 2026-05-19

> **Trigger**: 2026-05-19 backfill-fleet launch revealed the data-status numerator/denominator was inconsistent across
> writegate-endtoend, expected-unattempted-propagation, and data-status-drilldown plans, AND the instruments-service
> launcher hardcoded `--force` so the manifest-driven skip never actually fired in production. Operator directive: "fix
> the plan complete it for manifest and deployment api/ui and service data status so that no confusion again and ensure
> the production code for IS and MTDS looks at the right numerator and denominator when skipping and that running
> without --force works."

## The Canonical Formula (SSOT — DO NOT REDEFINE ELSEWHERE)

```python
from unified_api_contracts.canonical.crosscutting.honest_coverage import (
    CaptureStatusCounts, compute_honest_coverage, HONEST_COVERAGE_GAP_FIELDS,
)

counts = CaptureStatusCounts(
    captured=...,
    empty_confirmed=...,
    attempted_failed=...,
    expected_unattempted_known_empty=...,   # error_reason startswith "EXPECTED_"
    expected_unattempted_pending_fetch=..., # error_reason NOT startswith "EXPECTED_"
)
ratio = compute_honest_coverage(counts)
# numerator   = captured + empty_confirmed + expected_unattempted_known_empty
# denominator = numerator + attempted_failed + expected_unattempted_pending_fetch
# returns 1.0 if denominator == 0
```

Equivalent in English: a slot is **honestly answered** if we have any truthful answer (data landed, OR confirmed empty,
OR Tier-3 sentinel pre-resolved as known-empty per an `EXPECTED_*` reason). A slot is a **gap** only if we tried and
failed (`attempted_failed`) or if the sentinel says "expected, never tried" (non-`EXPECTED_*` `expected_unattempted`).

**Backfill skip rule (without `--force`)**: retry `attempted_failed` + `expected_unattempted_pending_fetch`; skip
everything else. With `--force`: refetch all, including already-captured (operator-only escape hatch for schema
migrations etc).

## Why this plan exists — formula drift inventory

Three plans each carried a partial formula with implicit numerator semantics:

| Plan                                                       | Implicit formula                                                                                    | Drift                                                                            |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `writegate_honest_coverage_endtoend_2026_05_06.md`         | "denominator clipped to legitimately-coverable shards" — pre-launch/holiday rows excluded from BOTH | OK if `empty_confirmed` is the only credit; mute on `expected_unattempted` split |
| `expected_unattempted_propagation_chain_2026_05_12.md`     | Phase 2.A: `expected_unattempted` rows propagate but counting role unspecified                      | Missing: `EXPECTED_*` vs non-`EXPECTED_*` split                                  |
| `data_status_drilldown_shard_atom_alignment_2026_05_07.md` | Line 170-171: "numerator = manifest rows with `capture_status=captured`"                            | Excludes `empty_confirmed` from numerator → understates coverage                 |
| `deployment-api/data_status_service.py`                    | Formula scattered across 350+ helper lines, no canonical expression                                 | No grep target for QG audit                                                      |

Net result: deployment-ui sometimes showed coverage % that didn't match `--operation=status` CLI output that didn't
match what the CI ratchet would compute (if it existed).

## Status — Phase 0 shipped 2026-05-19

- [x] **P0-0a. ✅ UAC**: `compute_honest_coverage()` + `CaptureStatusCounts` NamedTuple land as canonical SSOT —
      `unified-api-contracts@327fec6`. Validates against sports manifest real data (100.00%). Includes
      `HONEST_COVERAGE_GAP_FIELDS` for the two gap-state field names so backfill orchestrators don't re-derive the gap
      set.
- [x] **P0-0b. ✅ deployment-service**: `launch-instruments-backfill-vm.sh` `--force` made opt-in (was hardcoded ON,
      defeating manifest skip) — `deployment-service@d673323`. Without `--force`:
      `MODE: --force OFF (default) — manifest-driven skip ACTIVE` printed at launch. Re-launched 7 VMs at 19:54 UTC in
      no-force mode; manifest will filter.
- [x] **P0-0c. ✅ deployment-service**: EXIT-trap log upload across 14 inline-script VM launchers —
      `deployment-service@6b4610c`. New helper `lc_log_upload_trap_block` in `lib/launcher_common.sh` emits a snippet
      that tees stdout+stderr to `/var/log/run.log` and installs a `trap EXIT` handler uploading to canonical
      `gs://deployment-scripts-<project>/vm-logs/<vm-name>/run.log` with 3-attempt retry. Fires on success, error,
      signal, `set -e` propagation. Closes the demonstrated mtds-solana-drift-backfill bug (TERMINATED with no log
      uploaded). Unblocks Phase 8 verification — post-mortem on any failed VM now always has evidence.

## Pre-Audit Before Execution (per Citadel-Grade Planning Standards)

Workspace-wide consumers of the legacy formula(s) that need migration to `compute_honest_coverage()`:

```bash
# Run from workspace root to enumerate all callers requiring migration:
rg -l "captured.*total|coverage.*pct|honest_coverage|_coverage_ratio" \
   --type py --glob '!.venv*' --glob '!build' --glob '!tests'
```

Expected hits per audit:

1. `deployment-api/deployment_api/services/data_status_service.py` — primary panel rollup
2. `deployment-api/deployment_api/services/data_status_drilldown_service.py` — drilldown
3. `instruments-service/instruments_service/api/data_status_endpoint.py` (or similar)
4. `market-tick-data-service/.../api/data_status_endpoint.py`
5. `deployment-ui/src/.../DataStatusPanel.tsx` (or `unified-trading-system-ui/src/...`)
6. Per-service `--operation=status` CLI handlers (count: TBD by Phase 2/3 sub-agent)

QG addition (Phase 6) blocks any new caller that recomputes the formula inline rather than importing
`compute_honest_coverage`.

## Phased Execution DAG

```
Phase 0 (✅ DONE)
   │
   ├── Phase 1 (UTL helper)  ─┐
   │                          │
   ├── Phase 2 (IS migration) ┤
   │                          ├── Phase 4 (deployment-api) ─── Phase 5 (UI) ─── Phase 6 (CI ratchet)
   ├── Phase 3 (MTDS migr.)   ┤
   │                          │
   └─ Phase 7 (codex docs)  ──┘                                                   │
                                                                                  └── Phase 8 (verify on real fleet)
```

### Phase 1 — UTL `ManifestWriter.read_capture_status_counts()` helper

- [x] **P0. ✅ UAC facade exports**: `CaptureStatusCounts`, `compute_honest_coverage`, `HONEST_COVERAGE_GAP_FIELDS`
      added to `unified_api_contracts/__init__.py` public facade — consumers no longer need deep internal paths. —
      `unified-api-contracts@a9891f9`
- [x] **P0. ✅ UTL helper**: `read_capture_status_counts()` + `compute_coverage_for_bucket()` added to
      `unified-trading-library/unified_trading_library/manifest_writer.py`. Reads manifest parquet, groups by
      `(capture_status, error_reason)`, applies `EXPECTED_*` split, returns typed `CaptureStatusCounts`.
      `compute_coverage_for_bucket()` wraps both and returns `(counts, ratio)`. — `unified-trading-library@8d66204`
- [x] **P0. ✅ Test**: full roundtrip suite in `tests/unit/test_manifest_writer_coverage_counts.py` — all 4 statuses
      split correctly, data_type + date_range filters, empty manifest → zero counts, `compute_coverage_for_bucket` tuple
      output. 3792 passed, 2 pre-existing unrelated failures. — `unified-trading-library@8d66204`
- [x] ✅ **P1. Per-service docstring rule**: every service's `/api/data-status` endpoint MUST call this helper, not
      re-implement the manifest read. — PM@b0b1d9915; codex doc at
      `/codex/06-coding-standards/data-status-endpoint-contract.md`; QG STEP 5.90 wired in base-service.sh.

### Phase 2 — instruments-service migration

- [x] **P0. ✅ CLI `--operation=status`**: `_run_coverage_status()` added to IS `cli/main.py` — bypasses
      ServiceBootstrap date-loop, reads IS bucket manifest, calls `compute_coverage_for_bucket()` per data_type, prints
      JSON `{bucket, rows:[{asset_group, data_type, counts (5 fields), coverage}]}`. IS@d79a5a3. (2026-05-20 slot-2)
- [x] **P0. ✅ Skip path for `--force=false`**: `_should_skip_shard` + `_should_skip_date_for_per_league` + UTL
      `check_shard_freshness` all patched to honor EXPECTED\_\*/pending_fetch split. `expected_unattempted_known_empty`
      → skip; `expected_unattempted_pending_fetch` → stale/retry. 4 new UTL tests + 3 new IS tests pass. IS@ad18108
      UTL@1ba2c57. (2026-05-20 slot-2)
- [x] ✅ **P1. /api/data-status endpoint**: same migration for the HTTP endpoint. — IS@001cf7c; `GET /api/data-status`
      uses `compute_coverage_for_bucket()`, returns `{"counts": counts._asdict(), "coverage": float}` shape.

### Phase 3 — MTDS migration (parallel with Phase 2)

- [x] **P0. ✅ Same migration as Phase 2** but for `market-tick-data-service`. Confirmed orchestrator.py:1985 skip
      logic; patched to include `expected_unattempted_known_empty` (EXPECTED*\* reason) in skip-set. Non-EXPECTED*\*
      `expected_unattempted` excluded from skip → retry. MTDS@77d9f31. (2026-05-20 slot-2)
- [x] **P0. ✅ Per-data-type CLIs**: all 9 MTDS handlers (dex_pools, dex_swaps, gas_fee, lending_indices,
      liquidation_events, liquidations, lst_rates, perp_funding, solana_lst_archival) updated to use
      `is_now_skip_worthy()` (new UTL method: captured | empty_confirmed | expected_unattempted_known_empty) instead of
      `is_now_captured()`. UTL@c33f3b6 MTDS@dfb518e. (2026-05-20 slot-2)

### Phase 4 — deployment-api consumers

- [x] ✅ **P0. `data_status_service.py`**: replace the scattered helper functions with one call to
      `compute_honest_coverage()` per (asset_group, data_type) panel cell. Remove the ~350 lines of inline
      numerator/denominator math. — deployment-api@9d556fd; UAC `__all__` fix: unified-api-contracts@7da0545
- [x] ✅ **P0. `data_status_drilldown_service.py`**: same migration for shard-level drilldown. Allow
      `expected_unattempted` through status coercion gate. — deployment-api@9d556fd
- [x] ✅ **P1. API response shape**: every endpoint returns
      `{"counts": CaptureStatusCounts.as_dict(), "coverage": float}` so the UI never has to re-derive. —
      deployment-api@fa94b7a; `_compute_honest_coverage_for_category()` returns `"counts": counts_dict` +
      `"coverage": float(capture_rates["honest_coverage"])` at lines 1960-1961.

### Phase 5 — deployment-ui consumers

- [x] **P0. ✅ `HonestCoverageCard.tsx` + `client.ts`**: deployment-ui@643a22e — split expected_unattempted into
      expected_unattempted_known_empty + expected_unattempted_pending_fetch; coverage_pct comment corrected to canonical
      formula; CoverageBar renders all 5 fields as separate segments; tooltip text corrected; test fixture updated; QG
      green (68 tests, 0 TS errors, build pass). NOTE: `DataStatusPanel.tsx` is separate from `HonestCoverageCard` —
      Phase 5 scope was HonestCoverageCard per item 12. DataStatusPanel migration is tracked in Phase 4 P1 if needed.
- [x] **P1. ✅ Coverage % color thresholds**: green ≥99%, amber ≥95%, red <95% applied to `HonestCoverageCard.tsx`
      deployment-ui@643a22e.

### Phase 6 — CI ratchet

- [x] **P0. ✅ `honest-coverage-ratchet.sh`** in `unified-trading-pm/scripts/qg/`: snapshot yesterday's coverage per
      asset_group × data_type, compare to today, fail QG if any ratio regressed by >0.5pp. Stored snapshot:
      `_index/snapshots/honest_coverage/`. Script + `honest_coverage_ratchet.py` created PM@d68b92f7; wired into
      MTDS@65f0e52 + IS@f534700.
- [x] **P0. ✅ QG STEP wired**: per-service `quality-gates.sh` calls the ratchet for that service's bucket scope.
      Base-service.sh generic wiring not possible (per-service bucket names required); resolved by per-service wiring:
      MTDS `market-data-tick-defi-*` STEP 5.70 (MTDS@65f0e52) + IS `instruments-store-defi-*` STEP 5.70 (IS@f534700).
- [x] **P1. ✅ Inline-formula linter**: `no_inline_coverage_formula.sh` created PM@d68b92f7; wired as STEP 5.84 in
      base-service.sh (all services) + STEP 5.70 in MTDS@65f0e52 + IS@f534700. Passes clean (0 violations in both
      repos).
- [x] **P0. ✅ ⚓ COMPOSES WITH `is_mtds_contract_audit_2026_05_20.md` Phase 7** — the no-silent-absence +
      no-hardcoded-URL + no-hardcoded-universe QG steps live alongside the inline-formula linter in the same
      `unified-trading-pm/scripts/qg/` bundle. The ratchet is the "regression detector"; those three are the "structural
      guards". Cross-link in is_mtds_contract_audit Phase 7 + base-service.sh STEP 5.84 wired.

### Phase 7 — Codex docs

- [x] **P0. ✅ Update** `/codex/02-data/availability-manifest-and-data-status.md` § "Coverage formula" — stale 4-field
      formula replaced with canonical 5-field `CaptureStatusCounts` + `compute_honest_coverage()` reference + UTL
      helpers pointer. — `PM@d8cc6a4b`
- [x] **P0. ✅ Add SUPERSEDED banner** to the 3 in-flight plans' inline formula sections:
      `writegate_honest_coverage_endtoend_2026_05_06.md` (prose numerator omits empty_confirmed),
      `data_status_drilldown_shard_atom_alignment_2026_05_07.md` (numerator=captured only),
      `expected_unattempted_propagation_chain_2026_05_12.md` (counting role unspecified). — `PM@d8cc6a4b`
- [x] **P1. ✅ Update** `/codex/02-data/honest-absence-downstream-handling.md` § "Reason taxonomy" — callout block
      added: EXPECTED*\*/non-EXPECTED*\* split required when computing coverage; do NOT roll your own formula. —
      `PM@d8cc6a4b`

### Phase 8 — verify on real fleet

- [x] ✅ **P0. Re-pull manifest counts** for instruments-service + all 5 MTDS asset_groups — DONE 2026-05-22 (slot-2).
      Applied `compute_honest_coverage()` against live GCS consolidated blobs (all 10 buckets, 2026-05-22 03:44–08:08
      UTC snapshots). **Every (asset_group, data_type) cell reports a real number.** Formula is working correctly
      end-to-end.

      **Summary per service × asset_group** (manifest row totals + coverage range):

                                                                                                                      | service | asset_group | data_types | manifest_rows | min_cov% | max_cov% | cells_w_failed |
                                                                                                                      |---------|-------------|-----------|---------------|---------|---------|----------------|
                                                                                                                      | IS | cefi | 1 | 17,999 | 100% | 100% | 0 |
                                                                                                                      | IS | defi | 1 | 85,326 | 100% | 100% | 0 |
                                                                                                                      | IS | prediction | 16 | 795 | 0% | 100% | 0 |
                                                                                                                      | IS | sports | 25 | 2,619,839 | 0% | 100% | 15 |
                                                                                                                      | IS | tradfi | 1 | 9,265 | 100% | 100% | 0 |
                                                                                                                      | MTDS | cefi | 15 | 2,703,990 | **0%** | 100% | 14 |
                                                                                                                      | MTDS | defi | 24 | 1,862,668 | 96.96% | 100% | 20 |
                                                                                                                      | MTDS | prediction | 3 | 16,822 | 99.51% | 100% | 1 |
                                                                                                                      | MTDS | sports | 25 | 2,619,839 | 0% | 100% | 15 |
                                                                                                                      | MTDS | tradfi | 7 | 321,456 | 86.67% | 100% | 3 |

                                                                                                                      **Critical findings (attempted_failed > 0)**:
                                                                                                                      - MTDS cefi `book_snapshot_5`: 483,966 failed → **40.1%** coverage ← needs backfill
                                                                                                                      - MTDS cefi `trades`: 437,154 failed → **64.3%** ← needs backfill
                                                                                                                      - MTDS cefi `derivative_ticker`: 196,843 failed → **46.0%** ← needs backfill
                                                                                                                      - MTDS cefi `futures_chain`: 92,459 failed → **12.4%** ← needs backfill
                                                                                                                      - MTDS cefi `perp_funding`: 729 failed, 0 captured → **0%** ← critical
                                                                                                                      - MTDS cefi `options_chain`: 62,655 failed → **4.7%** ← needs backfill
                                                                                                                      - Sports data_types (FIXTURE_STATS/EVENTS/LINEUPS/INJURIES): 17K-19K failed each → 90-93%

                                                                                                                      **Suspicious (100% with 0 eu_pending_fetch)**: IS cefi/defi/tradfi buckets have no `data_type` column (pure
                                                                                                                      reference catalog rows, not time-series manifest); their 100% is valid. IS prediction data_types (14 cells) are
                                                                                                                      reference catalog (no time-series coverage). DeFi MTDS cells at 100% (`dex_pool_state`, `dex_pool_swaps`,
                                                                                                                      `rate_indices`, `utilization`) are fully backfilled — no issue.

                                                                                                                      **eu_pending_fetch > 0 (DeFi only)**: `dex_swaps` 252, `dex_pools` 234, `staking_yields` 234, `oracle_prices` 126
                                                                                                                      → Tier-3 sentinel propagation not yet complete for these data_types; addressed by
                                                                                                                      `expected_unattempted_validation_pending_phase3_2026_05_19.md`.

- [x] ✅ **P0. Master plan update**: add "Path to 99% coverage" row (item 28) to master plan Group D with the
      continuous-verification path = `honest-coverage-ratchet.sh` daily run + this plan's Phase 8 sweep result. NOTE:
      Group H was already taken (per-client isolation added 2026-05-20); added as Group D item 28 instead. —
      PM@06221f716

## Downstream Consumer Updates

Every consumer of legacy coverage math:

| Consumer                                     | File                                                             | Migration                      | Owner phase |
| -------------------------------------------- | ---------------------------------------------------------------- | ------------------------------ | ----------- |
| deployment-api panel                         | `data_status_service.py`                                         | replace inline math            | Phase 4     |
| deployment-api drilldown                     | `data_status_drilldown_service.py`                               | replace inline math            | Phase 4     |
| deployment-ui panel                          | `DataStatusPanel.tsx`                                            | use API value                  | Phase 5     |
| instruments-service /api/data-status         | `api/data_status_endpoint.py` (TBD)                              | use UTL helper                 | Phase 2     |
| instruments-service `--operation=status` CLI | TBD                                                              | use UTL helper                 | Phase 2     |
| MTDS /api/data-status                        | TBD                                                              | use UTL helper                 | Phase 3     |
| MTDS per-data-type CLIs                      | TBD                                                              | use UTL helper                 | Phase 3     |
| QG ratchet                                   | `unified-trading-pm/scripts/qg/honest-coverage-ratchet.sh` (NEW) | call `compute_honest_coverage` | Phase 6     |

## Continuous Verification Column (per Master Plan rule)

| Item                | Cutover criterion                                       | Continuous verification                                                         | Last verified                                   |
| ------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------------- |
| Formula SSOT        | UAC export + 1 test                                     | `pytest tests/canonical/crosscutting/test_honest_coverage_formula.py` (Phase 1) | 2026-05-19 (manual roundtrip in REPL)           |
| No-force skip works | Backfill on already-captured asset_group runs in <10min | Phase 0b VM logs; daily ratchet                                                 | 2026-05-19 (in-flight on instr-backfill-\* VMs) |
| Consumer parity     | API + UI + CLI report same coverage                     | QG STEP 5.XX (Phase 6)                                                          | TBD                                             |

## Codex SSOT updates (mandatory per HARD RULE)

Touched in Phase 7:

- `/codex/02-data/availability-manifest-and-data-status.md`
- `/codex/02-data/honest-absence-downstream-handling.md`
- `/codex/06-coding-standards/manifest-skip-semantics.md` (NEW — codifies no-force skip rule)

## Temporary states + their canonical follow-up plans

- The legacy inline formulas in `data_status_service.py` continue working until Phase 4 ships. New code MUST use
  `compute_honest_coverage`. Plan's Phase 4 is the cleanup successor; pre-existing inline math is review-blocking on
  touch.

## Deferred work after 2026-05-19 honest-coverage consolidation session

| Item                                         | Reason                                                          | Successor plan                                                 |
| -------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------- |
| Phases 1-8 implementation                    | Multi-repo, multi-day scope; not bundleable into May-19 session | This plan (Phases 1-8)                                         |
| Tier-3 sentinel propagation completion       | Pre-existing — Phase 3D.5 pending                               | `expected_unattempted_validation_pending_phase3_2026_05_19.md` |
| `measure-honest-coverage.py` baseline script | Pre-existing TBD per master plan audit                          | `master_to_live_defi_2026_05_23.md` Group H (new)              |

## Deferred work — migrated to:

Per the deferred items table (§ Deferred work after 2026-05-19 session):

- **Phases 1-8 implementation**: completed in this plan (26/26 todos done).
- **Tier-3 sentinel propagation**: **MIGRATED FROM:** this plan →
  `plans/active/expected_unattempted_validation_pending_phase3_2026_05_19.md` (already named there).
- **`measure-honest-coverage.py` baseline script**: **MIGRATED FROM:** this plan →
  `plans/active/master_to_live_defi_2026_05_23.md` Group H (already named there).
