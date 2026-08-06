---
doc_type: issue
title:
  "base_defi_adapter.py's per-instrument failure accounting never inspects the `success` key ~12 DeFi adapters already
  return — a real failure reads as `succeeded` with zero rows, same shape as a genuine empty day"
summary: >-
  Discovered while tracing curve_adapter.py::_download_liquidity's broad-except masking
  (defi_adapter_dead_code_audit_2026_07_24.md §2.3, todo done 2026-07-27).
  base_defi_adapter.py::_download_all_instruments gates its succeeded/failed accounting on a single check, `if not
  result: continue` — whether the per-instrument download_market_data() dict is empty/falsy. ~12 DeFi adapters
  (lst_puffer_adapter.py, lst_lido_adapter.py, lst_renzo_adapter.py, lst_rocket_pool_adapter.py,
  lst_solblaze_adapter.py, restaking_jito_adapter.py, restaking_karak_adapter.py, vault_pendle_adapter.py,
  lst_coinbase_adapter.py, lst_etherfi_adapter.py, lst_kelpdao_adapter.py, aave_positions.py) already return a
  `{"success": bool, ...}` shape on failure (`{"success": False, "error": "..."}`), but `_flatten_instrument_result`'s
  only use of that key is to SKIP it during row-flattening (base_defi_adapter.py:50) — the boolean value is never read
  to route the outcome into the `failed` counter. A `{"success": False, "error": "..."}` result is a non-empty dict, so
  `if not result: continue` never fires; execution falls through to `_flatten_instrument_result` (contributes 0 rows,
  since neither "success" nor "error" is a list), then `succeeded += 1` fires anyway — the exact same shape as a genuine
  zero-result day, with the failure signal those 12 adapters already went to the trouble of producing silently discarded
  at the one place it could matter.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, adapters, failure-accounting, honest-absence, masking, shard-isolation, data-correctness]
related:
  [
    /plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-27
author: unknown
parent_epic: infrastructure_master
priority: P2
source:
  "Dispatched todo defi_satellite_ao_dispatch_batch1-012 (trace curve_adapter.py::_download_liquidity masking,
  plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md) — tracing the shared caller
  (base_defi_adapter.py::_download_all_instruments) for the Curve-specific verdict surfaced this broader, cross-adapter
  version of the same failure-accounting gap."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
last_reviewed:
assigned_role: data_engineering
context_scope:
  [
    /plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/base_defi_adapter.py,
  ]
---

# `base_defi_adapter.py`'s failure accounting never reads the `success` key it already receives

## What I found

`base_defi_adapter.py::_download_all_instruments` (the SHARED per-instrument loop every `BaseDefiAdapter` subclass uses
— confirmed via repo-wide grep, no subclass overrides `_download_all_instruments` or `download_batch`):

```python
for instrument in instruments:
    try:
        result = await self.download_market_data(instrument, date_dt, data_types)
        if not result:
            continue
        _flatten_instrument_result(result, instrument, date, all_rows)
        succeeded += 1
    except (OSError, ConnectionError, TimeoutError, ValueError) as exc:
        ...
        failed += 1
    except Exception as exc:
        ...
        failed += 1
```

The ONLY failure signal this loop understands is (a) an exception escaping `download_market_data`, or (b) `result` being
empty/falsy. It never inspects `result.get("success")`.

But ~12 adapters already return a `{"success": bool, ...}` shape specifically to signal failure without raising:

```python
# lst_puffer_adapter.py:235, lst_lido_adapter.py:225, lst_renzo_adapter.py:235,
# lst_rocket_pool_adapter.py:236, lst_solblaze_adapter.py:127, lst_coinbase_adapter.py:298,
# lst_etherfi_adapter.py:231, lst_kelpdao_adapter.py:235, aave_positions.py:137/144 (same shape):
return {"success": False, "error": "Invalid instrument"}
# restaking_jito_adapter.py:97, restaking_karak_adapter.py:89, vault_pendle_adapter.py:96 (same shape):
return {"success": False, "error": "invalid instrument: missing venue"}
```

`_flatten_instrument_result` (base_defi_adapter.py:23-53) DOES reference the `"success"` key — but only to skip it
during row-flattening, never to read its value:

```python
for data_type, records in data.items():
    if data_type == "success":
        continue
    if not isinstance(records, list):
        continue
    ...
```

Walking a `{"success": False, "error": "Invalid instrument"}` result through the full chain: `result` is a non-empty
dict → `if not result: continue` does NOT fire → `_flatten_instrument_result` runs → `"success"` is skipped, `"error"`
is a string not a list so it's also skipped → zero rows appended → back in the loop, `succeeded += 1` fires
unconditionally. **A `success: False` result is counted as succeeded, with the failure reason silently discarded.**

This is the SAME shape as `defi_adapter_dead_code_audit_2026_07_24.md` §2.3's confirmed Curve finding
(`curve_adapter.py::_download_liquidity`'s broad-except `return []`) — that investigation is what surfaced this one —
but it's broader: Curve's masking is a single adapter's own broad-except; this one is the SHARED caller silently
ignoring a failure signal that a dozen OTHER adapters already deliberately produce.

## Why it matters

- **Cross-adapter, not one file.** Any of the 12 adapters listed above hitting their `{"success": False, ...}` path (an
  invalid/malformed instrument, a missing venue, a fetch error the adapter chose to report this way instead of raising)
  reads as a normal success with zero data — indistinguishable from a genuine empty result, exactly the
  `honest-absence-downstream-handling` class this workspace treats as a data-pipeline-correctness HARD RULE concern.
- **The signal already exists — this isn't "add new instrumentation," it's "read what's already being produced."**
  Twelve adapters independently arrived at the same `{"success": bool, ...}` convention, which strongly suggests it was
  DESIGNED to be read by the caller at some point; `_flatten_instrument_result`'s explicit
  `if data_type == "success": continue` skip-line is itself evidence the caller author was AWARE of the key's existence,
  just wired the skip instead of the read.
- **Silent, not loud.** No exception, no `failed` counter increment, no line in the `if failed > 0` shard-summary log
  (base_defi_adapter.py:305-313) — a real failure vanishes with no trace beyond whatever the adapter itself logged
  internally (if anything) before returning `{"success": False, ...}`.

## Not traced further (scope)

Same as the parent audit doc's own convention: whether/how a zero-row-but-`succeeded` DataFrame from this path
propagates into GCS manifest `capture_status` is downstream of `download_batch`'s return value and wasn't traced here —
that would need its own pass against whichever CLI operation ultimately calls `download_batch` for each of these 12
adapters' venues.

## Recommended decision

- [x] ✅ [SERVICE] P2. **DONE 2026-07-29** — Wired `_download_all_instruments`'s failure accounting to read the
      `success` key. `download_market_data()` returning `{"success": False, "error": ...}` now routes into the `failed`
      counter (not `succeeded`) and surfaces the error in the per-instrument warning log, instead of being silently
      discarded via `_flatten_instrument_result`'s skip. New unit test
      (`test_download_all_instruments_routes_success_false_to_failed_not_succeeded`) asserts the routing + log content;
      `quality-gates.sh` green. — market-tick-data-service@df3d55dd.
- [x] ✅ [SERVICE] P3. **Audit complete 2026-08-05 (batch-6 todo 1) — blast radius: ZERO.** All 12 adapters gate
      `success:False` on `_validate_instrument` failures (missing venue / all-identifier-fields-null). Production
      instrument catalog (`prd/catalog.parquet`, 7,223 instruments, 31 venues) has ZERO malformed records. Instrument
      availability parquets for all 12 venues on 2026-08-05 (191 instruments) + historical spot-check
      2026-07-30/08-01/08-03 all CLEAN (no null venue, no null identifiers). The `success:False` path is a defensive
      guard that has never fired in production — no rows were silently dropped. The fix (mtds@df3d55dd) is correct but
      the blast radius is zero. See Progress Log § "P3 audit findings" for full adapter→venue mapping + validation
      methodology. Repo: market-tick-data-service.
- [x] ✅ [SERVICE] P3. **DUPLICATE of above — resolved by same audit.** Identical todo (same description, same repos);
      the audit above covers both. This duplicate should be removed in the next plan hygiene sweep.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - primary fix shipped mtds@df3d55dd; residual is a
  bounded production blast-radius audit over 12 named adapters
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (3 entries).
- **P3 audit findings 2026-08-05** (slot 6, data_engineering worker): blast radius = ZERO.

  **Methodology**: (1) Code analysis of all 12 adapters' `success: False` trigger conditions; (2) production catalog
  validation (`prd/catalog.parquet`, 7,223 instruments); (3) instrument_availability parquet validation for all 12
  venues on 2026-08-05 + spot-check 2026-07-30/08-01/08-03; (4) attempted VM log search for post-fix "failed for"
  warnings (no DeFi MTDS VMs running at audit time).

  **Adapter → venue mapping + validation method**:

  | Adapter                 | `self.venue`         | Validation check                          | Catalog entries |
  | ----------------------- | -------------------- | ----------------------------------------- | --------------- |
  | lst_puffer_adapter      | PUFFER-ETHEREUM      | venue + (contract_addr\|symbol\|inst_key) | 1, CLEAN        |
  | lst_lido_adapter        | LIDO-ETHEREUM        | venue + (contract_addr\|symbol\|inst_key) | 2, CLEAN        |
  | lst_renzo_adapter       | RENZO-ETHEREUM       | venue + (contract_addr\|symbol\|inst_key) | 1, CLEAN        |
  | lst_rocket_pool_adapter | ROCKETPOOL-ETHEREUM  | venue + (contract_addr\|symbol\|inst_key) | 1, CLEAN        |
  | lst_solblaze_adapter    | SOLBLAZE-SOLANA      | venue only                                | 1, CLEAN        |
  | restaking_jito_adapter  | JITORESTAKING-SOLANA | venue only                                | 3, CLEAN        |
  | restaking_karak_adapter | KARAK-ETHEREUM       | venue only                                | 2, CLEAN        |
  | vault_pendle_adapter    | PENDLE-ETHEREUM      | venue only                                | 8, CLEAN        |
  | lst_coinbase_adapter    | COINBASE-ETHEREUM    | venue + (contract_addr\|symbol\|inst_key) | 1, CLEAN        |
  | lst_etherfi_adapter     | ETHERFI-ETHEREUM     | venue + (contract_addr\|symbol\|inst_key) | 1, CLEAN        |
  | lst_kelpdao_adapter     | KELPDAO-ETHEREUM     | venue + (contract_addr\|symbol\|inst_key) | 1, CLEAN        |
  | aave_positions          | AAVE_V3-* (8 chains) | venue + (token_addr\|base_asset)          | 169, CLEAN      |

  **Root cause**: The `success: False` path fires ONLY when `_validate_instrument` rejects a malformed instrument record
  from instruments-service. No malformed records exist in the production catalog or in any recent
  instrument_availability snapshot. The 12 adapters independently arrived at the `{"success": False, ...}` convention as
  a defensive pattern — the validation failures it guards against have never materialized in production.

  **Impact of shipped fix (mtds@df3d55dd)**: The fix correctly reads `result.get("success")` and routes to `failed`
  counter. Since no instruments trigger validation failure, the fix produces zero behavioral change in current
  production — no surprise `failed` count jump. The fix remains valuable as defense-in-depth against future instrument
  definition corruption.

- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (3 entries), unchanged.
