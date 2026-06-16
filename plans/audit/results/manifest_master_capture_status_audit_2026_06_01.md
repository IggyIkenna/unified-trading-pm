---
type: audit-result
title: manifest_master — per-service capture_status write-path audit — 2026-06-01
epic: manifest_master
auditor: harsh-claude-opus (4 parallel sonnet sub-agents)
date: "2026-06-01"
status: in-progress
instructions_ref:
  plans/audit/instructions/manifest_master_audit_instructions.md § "Per-Service capture_status Write-Path Calibration"
assigned_vm: vm-defi
tier: L1
instructions:
  plans/audit/instructions/manifest_master_audit_instructions.md § "Per-Service capture_status Write-Path Calibration"
locked_by: live-defi-rollout
---

# Per-Service `capture_status` Write-Path Audit — 2026-06-01

**Scope (operator-directed):** the 4 producer services backfilling now — instruments-service (IS),
market-tick-data-service (MTDS), market-data-processing-service (MDPS), features-service. READ-ONLY code audit of every
manifest emission path against the decision rule (empty_confirmed = LAST resort; owed-data ≠ absence; error ≠ empty; no
silent no-row skips). Run **before** further backfill so the code writes rule-correct statuses as the corpus fills.

> **Why now (operator, 2026-06-01):** auditing the _code_ now means the ongoing/remaining backfill produces a correct
> manifest. Deferring bakes any status-writing bug across millions of rows, then forces a reconcile + a search for the
> real bugs inside a pile of wrong statuses.

## Summary

| Service             | Callsites audited | Violations | P0    | P1     | P2    |
| ------------------- | ----------------- | ---------- | ----- | ------ | ----- |
| instruments-service | ~95               | 5          | 0     | 3      | 2     |
| MTDS                | ~65               | 6          | 0     | 4      | 2     |
| MDPS                | 14                | 5          | 0     | 4      | 2     |
| features-service    | ~55               | 7          | **3** | 2      | 2     |
| **Total**           | **~230**          | **23**     | **3** | **13** | **7** |

**Headline:** the 3 P0s are all in **features-service** (silent no-row skips + a dependency-gap that goes silent instead
of propagating upstream status). The dominant cross-cutting pattern across ALL four services is **silent no-row skips**
(a shard processed/attempted but no manifest row written — indistinguishable from a crash) and **error/missing → empty**
(config/credential/HTTP/dependency failures routed to `empty_confirmed`/`SOURCE_RETURNED_ZERO` instead of
`attempted_failed`/dependency-gate).

---

## Adversarial verification pass (2026-06-01) — second-pass refutation of every finding

The 23 first-pass findings were each independently re-checked by a separate agent instructed to **refute** it (read the
exact cited code + trace the call chain UP/DOWN, looking for a manifest write the first pass missed or a by-design
rationale). Result: **18 of 23 hold (16 at severity + 2 downgraded), 5 are false-positives.** The 3 features-service P0s
are **double-confirmed** (verifier found `cefi` is not in the CLI `_FAMILIES` tuple and `run_batch` has zero callers —
so no dispatcher can ever write the promised `record_empty`).

| Finding                                         | Verdict           | Note                                                                                                     |
| ----------------------------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------- |
| features cefi perp_funding:175-196 (P0)         | ✅ CONFIRMED      | no dispatcher exists; empty date → no row                                                                |
| features cefi perp_funding:160-166 (P0)         | ✅ CONFIRMED      | MTDS-unavailable → no `expected_unattempted`                                                             |
| features volatility:157-165 (P0)                | ✅ CONFIRMED      | partial batch (total_success>0, is_complete=False) → no row                                              |
| features volatility:499 (P1)                    | ✅ CONFIRMED      | spot/future conflation (P2 defensible)                                                                   |
| features onchain orchestrator:228-229 (P1)      | ✅ CONFIRMED      | `result=False` → no `record_empty`                                                                       |
| features onchain dependency_checker:21,210 (P2) | ✅ CONFIRMED      | contract "caller emits record_empty" unfulfilled                                                         |
| features multi_timeframe:318-335 (P2)           | ✅ CONFIRMED      | phantom `captured` 0-row when all instruments fail                                                       |
| MDPS live_workers:376-391 (P1)                  | ✅ CONFIRMED      | caller only debug-logs `success=False`; no row                                                           |
| MDPS live_workers:410-423 (P1)                  | ✅ CONFIRMED      | no-adapter → no row                                                                                      |
| MDPS live_workers:876-879 (P1)                  | ✅ CONFIRMED      | broad-except per-timeframe → no row                                                                      |
| MDPS batch_workers:167-189 (P1)                 | 🔻 RECLASSIFY→P2  | row IS written (wrong status); known DEFERRED — and **no active wave-3 plan exists** (successor missing) |
| MDPS orchestration_service:288-299 (P2)         | ❌ FALSE-POSITIVE | zero upstream files = MTDS's shard to report, not MDPS — by-design                                       |
| MDPS orchestration_service:625-634 (P2)         | ❌ FALSE-POSITIVE | bypass types / no-adapter = intentional scope exclusion                                                  |
| MTDS dex_swaps:491-495 (P1)                     | ✅ CONFIRMED      | missing subgraph_id → wrong reason SOURCE_RETURNED_ZERO                                                  |
| MTDS dex_swaps:492-495 (P1)                     | ✅ CONFIRMED      | missing API key → empty instead of failed                                                                |
| MTDS dex_swaps:606/633 (P1)                     | ❌ FALSE-POSITIVE | HTTP 404 = deprecated subgraph = genuine absence; documented rationale, row IS written                   |
| MTDS perp_funding:395-420 (P1)                  | ✅ CONFIRMED      | unknown protocol → empty instead of failed/raise                                                         |
| MTDS backfill_runner:223-224 (P2)               | ❌ FALSE-POSITIVE | live-aux gap-backfill, optional recorder; per-instrument empty is routine                                |
| MTDS lst_rates:506-515 (P2)                     | ✅ CONFIRMED      | only LIDO gets `record_failed`; ETHERFI/ETHENA no row                                                    |
| IS orchestrator:6240-6245 (P1)                  | ✅ CONFIRMED      | unmapped league → wrong `EXPECTED_NO_FIXTURE`                                                            |
| IS orchestrator:7034,7228 (P1)                  | ✅ CONFIRMED      | blank reason → **LegacyBlankErrorReasonError at runtime** (crash)                                        |
| IS orchestrator:6630-6637 (P1)                  | 🔻 RECLASSIFY→P2  | row IS written (wrong reason); in-progress-match latency                                                 |
| IS orchestrator:2880-2883 (P2)                  | ✅ CONFIRMED      | 50-99% completeness venues → no `attempted_failed` row                                                   |
| IS orchestrator:4280-4289 (P2)                  | ❌ FALSE-POSITIVE | recovery-mode filter — early return avoids phantom rows; by-design                                       |

**Net real violations: 18** (features 7 · MDPS 4 → 3+1-downgraded · MTDS 4 · IS 4 → 3+1-downgraded).
**False-positives: 5.** **Revised severity: P0×3 (all features), P1×9, P2×6.** The 5 false-positives were all "by-design
scope boundary / documented-genuine-absence" paths the first pass over-flagged. The single highest-confidence real bug
that is also a _crash_ (not just a misclassification) is **IS weather blank-reason → `LegacyBlankErrorReasonError`**.

---

## features-service (3×P0, 2×P1, 2×P2) — highest priority

| Module          | File:line                                            | Sev    | Pattern                                                                                                                                                                                                                                    |
| --------------- | ---------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| cefi            | `cefi/cli/handlers/perp_funding_handler.py:175-196`  | **P0** | `continue` on `df.is_empty()` — comment says dispatcher emits, but `run_batch` IS the terminal caller; manifest write never happens → silent no-row                                                                                        |
| cefi            | `cefi/cli/handlers/perp_funding_handler.py:160-166`  | **P0** | `_mtds_cefi_available()==False` → `continue`, no row on output bucket. Upstream `attempted_failed` must propagate; upstream "no row" → `expected_unattempted`, NOT silence                                                                 |
| volatility      | `volatility/engine/feature_group_service.py:157-165` | **P0** | `validate_batch_completeness` partial (`is_complete=False`) → logs + returns, no row. Partial success needs `record_captured` (partial), not silence. Affects futures_basis / futures_term_structure / options_iv / options_term_structure |
| volatility      | `volatility/engine/feature_group_service.py:499`     | P1     | `_calculate_futures_basis` collapses "futures empty" and "spot absent" into one silent `return pl.DataFrame()` — spot+future corollary untyped                                                                                             |
| onchain         | `onchain/engine/orchestrator.py:228-229`             | P1     | `result=False` (calculator returned empty) → `if result:` not entered → no `record_empty` → silent no-row                                                                                                                                  |
| onchain         | `onchain/app/core/dependency_checker.py:21,210`      | P2     | MTDS `empty_confirmed` → `available=True`; comment says "caller emits record_empty" but no caller does (unimplemented contract)                                                                                                            |
| multi_timeframe | `multi_timeframe/engine/orchestrator.py:318-335`     | P2     | `writer.add(row_count=0)` when all instruments failed → phantom `captured` 0-row instead of `record_empty(SOURCE_RETURNED_ZERO)`                                                                                                           |

**Clean:** delta_one, cross_instrument, calendar, sports, commodity, strategy_pnl_archetype (typed reasons;
`record_failed` on exception; `record_empty(SOURCE_RETURNED_ZERO)` on zero-row).

## MDPS (4×P1, 2×P2)

| File:line                          | Sev | Pattern                                                                                                                                                                                                                                                                                          |
| ---------------------------------- | --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `live_workers.py:376-391`          | P1  | broad-except on processing error returns failed result but writes NO manifest row → add `record_failed_for_shard(type(e).__name__)`                                                                                                                                                              |
| `live_workers.py:410-423`          | P1  | "No adapter for ..." returns failure, no row → `record_failed_for_shard("NO_ADAPTER_REGISTERED")`                                                                                                                                                                                                |
| `live_workers.py:876-879`          | P1  | broad adapter/write except appends to errors, no row → `record_failed_for_shard(str(e))` (mirror the UpstreamTimestampBiasError branch at 862)                                                                                                                                                   |
| `batch_workers.py:167-189`         | P1  | `_handle_empty_tick_data` unconditionally `record_empty_for_shard(SOURCE_RETURNED_ZERO)` for any empty tick file — **known tracked** (DEFERRED-AFTER-writegate_phase_3.D.5_wave3): catalog-alive instrument-day with source-zero MUST flip to `attempted_failed`. Verify Wave 3 plan isn't stale |
| `orchestration_service.py:288-299` | P2  | `skipped_data_types` (adapter exists, dep-check passed, zero upstream files) → no row → `expected_unattempted`/`attempted_failed`                                                                                                                                                                |
| `orchestration_service.py:625-634` | P2  | bypass types (`needs_candle_processing==False` / no adapter) return `[]` silently — ambiguous "intentional skip" vs "never ran"                                                                                                                                                                  |

**Clean:** dependency-skip → `expected_unattempted` (143-155); live-gap → `record_failed_for_shard(UPSTREAM_LIVE_GAP)`;
zero-trade-market-open → `record_empty_for_shard(SOURCE_RETURNED_ZERO)` (correctly distinguished from empty-tick-file);
typed UTL errors → `record_failed_for_shard`; VIX gap → `EXPECTED_KNOWN_SOURCE_GAP`.

## MTDS (4×P1, 2×P2)

| File:line                                         | Sev | Pattern                                                                                                                                                                                    |
| ------------------------------------------------- | --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `dex_swaps_handler.py:491-495`                    | P1  | missing `subgraph_id` → count 0 → `record_empty(SOURCE_RETURNED_ZERO)`. Source never queried → should be `EXPECTED_INSTRUMENT_NOT_LISTED` or raise→`attempted_failed`                      |
| `dex_swaps_handler.py:492-495`                    | P1  | missing API key → 0 → empty. Credential failure ≠ honest empty → `record_failed(MISSING_API_KEY)`                                                                                          |
| `dex_swaps_handler.py:606 / _query_and_parse:633` | P1  | HTTP 404 (`_SubgraphNotFoundError`) → `pd.DataFrame()` → `SOURCE_RETURNED_ZERO`. Unexpected-deprecation should be `record_failed`; only never-deployed is `EXPECTED_INSTRUMENT_NOT_LISTED` |
| `perp_funding_handler.py:395-420`                 | P1  | unknown protocol → `written=0` → `SOURCE_RETURNED_ZERO`. Config error, source never fetched → raise or `record_failed`                                                                     |
| `backfill_runner.py:223-224`                      | P2  | gap-backfill `rows.empty` → `continue`, no row → `record_failed("UPSTREAM_LIVE_GAP")` (mirror websocket_runner:730)                                                                        |
| `lst_rates_handler.py:506-515`                    | P2  | `evm_errors` non-empty → only LIDO/ETHEREUM gets `record_failed`; ETHERFI/ETHENA get no row → fan out all 3                                                                                |

**Clean:** tardis_adapter §6A (Empty-CSV→`SOURCE_RETURNED_ZERO`, else `record_failed`); `EXPECTED_INSTRUMENT_NOT_LISTED`
pre-listing; orchestrator Tier-2/3 sentinel fan-out; lending_indices oracle preflight; perp_funding
`EXPECTED_PRE_VENUE_LAUNCH`; websocket_runner gap→`record_failed(UPSTREAM_LIVE_GAP)`.

## instruments-service (3×P1, 2×P2)

| File:line                    | Sev | Pattern                                                                                                                                                                                                                            |
| ---------------------------- | --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `orchestrator.py:6240-6245`  | P1  | Transfermarkt unmapped league → `record_empty(EXPECTED_NO_FIXTURE)`. Wrong reason — not-attempted-due-to-missing-mapping, data OWED → `EXPECTED_NO_MAPPING` (or `attempted_failed`)                                                |
| `orchestrator.py:7034, 7228` | P1  | `_record_weather_empty()` called with no `reason=` → defaults to `""` → `LegacyBlankErrorReasonError`. Pass typed reason                                                                                                           |
| `orchestrator.py:6630-6637`  | P1  | SFI: match IDs present, all per-match fetches returned 0 → `EXPECTED_NO_FIXTURE`. Conflates "no games" with "games exist, stats not yet published" (data owed for in-progress match) → `attempted_failed` unless all matches final |
| `orchestrator.py:2880-2883`  | P2  | retry loop: venues 50-99% completeness exit with no `attempted_failed` row for the permanently-failed venues                                                                                                                       |
| `orchestrator.py:4280-4289`  | P2  | recovery-mode fixture filter → empty → `return counts`, no rows for FIXTURE\_\* entities → `expected_unattempted`                                                                                                                  |

---

## Cross-cutting patterns (fix these as classes, not one-offs)

1. **Silent no-row skip** (every service): a shard is processed/attempted but a `return`/`continue`/broad-except exits
   without any manifest row. Worst in MDPS `live_workers` broad-excepts (any adapter/IO crash → invisible shard) and
   features cefi/volatility/onchain. → every in-scope shard exit MUST write a typed status.
2. **Error / missing-config / missing-credential / missing-dependency → `empty_confirmed`** (MTDS dex_swaps + perp;
   features cefi MTDS-gap). The source was never successfully queried → `attempted_failed` / dependency-gate, never
   `SOURCE_RETURNED_ZERO`.
3. **Blank/untyped reason** (IS weather) → `LegacyBlankErrorReasonError` waiting to fire.
4. **Phantom `captured` 0-row** (multi_timeframe) instead of `record_empty`.
5. **Spot+future corollary untyped** (volatility futures_basis): "spot absent, future present" not distinguished from
   "future not listed".

## Recommended fix order

1. **features-service P0×3** — silent no-row in cefi perp_funding (×2) + volatility partial-batch. These drop real
   shards silently on the live backfill path.
2. **MDPS live_workers broad-except P1×3** — any adapter/IO crash currently → invisible shard; add
   `record_failed_for_shard`.
3. **MTDS error→empty P1×4** (dex_swaps + perp unknown-protocol) — reclassify config/credential/404/unknown → failed.
4. **IS P1×3** — fix the blank weather reason (crash risk) + the 2 wrong `EXPECTED_NO_FIXTURE` reasons.
5. **P2×7** — silent skips on partial-completeness / bypass / recovery paths; fan-out per-venue failed rows.
6. **MDPS `batch_workers` empty-tick** — confirm the Wave 3 plan (writegate_phase_3.D.5) is live, not stale.

Each fix lands in the owning service repo (changes the code that writes status) **before** that service backfills
further, so the manifest fills correctly. Re-run this audit per the instruction whenever a producer's emission paths
change.

## Status

Audit complete (READ-ONLY). No code changed. Fixes to be dispatched per the order above — operator/Harsh to assign.
