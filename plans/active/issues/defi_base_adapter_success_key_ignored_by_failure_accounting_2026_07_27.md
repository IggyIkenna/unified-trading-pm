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
  ]
created: 2026-07-27
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
- [ ] [SERVICE] P3. **Audit the 12 named adapters for how often they actually hit their `success: False` path in
      production** (grep logs / manifest for the affected venues over a real window) to gauge whether this has been
      silently dropping real rows, before/alongside shipping the fix above — the fix changes behavior (failures start
      counting as failures), so knowing the current blast radius avoids a surprise jump in `failed` counts once wired.
      Repo: market-tick-data-service.
- [ ] [SERVICE] P3. **Audit the 12 named adapters for how often they actually hit their `success: False` path in
      production** (grep logs / manifest for the affected venues over a real window) to gauge whether this has been
      silently dropping real rows, before/alongside shipping the fix above — the fix changes behavior (failures start
      counting as failures), so knowing the current blast radius avoids a surprise jump in `failed` counts once wired.
      Repo: market-tick-data-service.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY -> assigned_vm: planning (conflict-check CLEAR against 231 active
  planning docs; no open todo elsewhere duplicates this claim) - primary fix shipped mtds@df3d55dd; residual is a
  bounded production blast-radius audit over 12 named adapters
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (3 entries).
