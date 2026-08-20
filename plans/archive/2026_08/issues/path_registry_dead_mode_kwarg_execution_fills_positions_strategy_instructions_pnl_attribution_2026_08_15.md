---
doc_type: issue
title:
  "PATH_REGISTRY dead-`mode`-kwarg bug — execution_fills/positions/strategy_instructions/pnl_attribution all silently
  drop the `mode=` kwarg callers already pass, so batch/paper/live writes collide on the SAME object path"
summary:
  "unified-trading-library's `PATH_REGISTRY` path_templates for `execution_fills`, `positions`, `strategy_instructions`,
  and `pnl_attribution` have NO `{mode}` placeholder, but real production callers
  (`strategy-service/strategy_service/pnl/adapters/domain_adapter.py`, `execution-service/.../save_operations.py`)
  already pass a `mode=` kwarg on every call. `build_path()` uses bare `str.format(**partition_values)`, which silently
  discards unconsumed kwargs — so the `mode=` value is accepted, does nothing, and batch/paper/live rows for the same
  (date, category/strategy_id) write to the IDENTICAL GCS object path today, each overwriting the previous mode's data.
  Confirmed live via direct code read, not just the source design doc's research."
status: closed
nature: issue
asset_group: [cross-cutting]
stage: [execution, data]
repos: [unified-trading-library, strategy-service, execution-service, unified-trading-api]
scope: [engineer, admin]
tags: [data-correctness, path-registry, pnl, execution, positions, live-vs-paper, silent-bug]
related: [/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
created: 2026-08-15
author: slot-18-infra
last_updated: 2026-08-15
priority: P1
parent_epic: security_and_cross_cutting_master
source:
  "Surfaced by `/plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md` §2.1/§2.2/§2.4 research (2026-07-29);
  filed as its own issue doc per that doc's own P2 todo + the findings-triage rule, via
  `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md`'s corresponding todo. Re-verified live against current
  HEAD before filing (2026-08-15), not just carried forward from the source doc's prose."
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: brand-new
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    unified-trading-library/unified_trading_library/config_interface/paths/registry.py,
    strategy-service/strategy_service/pnl/adapters/domain_adapter.py,
    strategy-service/strategy_service/adapters/domain_adapter.py,
    execution-service/execution_service/results/save_operations.py,
    /plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md,
  ]
---

# PATH_REGISTRY dead-`mode`-kwarg bug — execution_fills/positions/strategy_instructions/pnl_attribution

## What I found

`unified-trading-library/unified_trading_library/config_interface/paths/registry.py` defines `build_path()` as:

```python
def build_path(name: str, **partition_values: str) -> str:
    spec = get_spec(name)
    return spec.path_template.format(**partition_values)
```

Python's `str.format(**kwargs)` silently ignores any kwarg that doesn't correspond to a `{placeholder}` in the format
string — it does not raise. Four `PATH_REGISTRY` entries have `path_template`s with **no `{mode}` placeholder**, yet
real production call sites pass `mode=` on every call:

| Dataset                 | `path_template` (registry.py)                                                       | Live caller passing `mode=`                                                                                                                                                        |
| ----------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `execution_fills`       | `{category}/execution/by_date/day={date}/`                                          | `execution-service/execution_service/results/save_operations.py:790` (`_mode = result.get("mode", "live")`); `strategy-service/strategy_service/pnl/adapters/domain_adapter.py:50` |
| `positions`             | `positions/by_date/day={date}/account={account_key}/snapshot_type={snapshot_type}/` | `strategy-service/strategy_service/pnl/adapters/domain_adapter.py:63` (`read_positions_path(..., mode=mode)`)                                                                      |
| `strategy_instructions` | `strategy_instructions/client_id={client_id}/strategy_id={strategy_id}/day={date}/` | `strategy-service/strategy_service/pnl/adapters/domain_adapter.py:76`                                                                                                              |
| `pnl_attribution`       | `pnl-attribution/by_date/day={date}/strategy_id={strategy_id}/`                     | `strategy-service/strategy_service/pnl/adapters/domain_adapter.py:84`, `execution-service`-side callers                                                                            |

Confirmed by direct read of current HEAD (2026-08-15), not just the source design doc's prose — the `mode=` kwarg is
genuinely wired through from real writers (`execution-service/.../save_operations.py`'s `_write_canonical_fills`, keyed
off `result.get("mode", "live")`) and real readers (`domain_adapter.py`'s `read_execution_fills_path` /
`read_positions_path` / `read_strategy_instructions_path` / `write_pnl_attribution_path`, each with a
`mode: str = "live"` parameter it forwards straight into `build_path()`).

**Net effect**: batch, paper, and live fills/instructions/pnl-attribution rows for the same `(date, category)` or
`(date, strategy_id)` key write to the **identical GCS object path** today — each write silently overwrites whatever the
previous mode wrote, with no error, no warning, and no schema signal that anything is wrong. `positions` has only one
confirmed real caller (the same `domain_adapter.py` reader) and no confirmed live writer in this survey — the bug's
blast radius there may be smaller in practice, but the template itself carries the identical defect.

**Not a hypothetical class either** — the very same registry file already carries a comment (`registry.py:18-25`)
documenting an earlier, structurally identical incident for `raw_tick_data` (a template missing BOTH `pipeline_mode=`
and `asset_group=`, silently accepting calls that omitted them and resolving to a prefix that never matched what MTDS
actually wrote) that was caught and fixed 2026-07-28. This is the second confirmed occurrence of the exact same failure
mode (documented as a general risk in that same comment) — this time live in the execution/PnL storage path rather than
raw tick data.

**Related, not the same bug**: `unified-trading-api/unified_trading_api/services/live_service.py:36,38` maintains its
OWN separate, parallel path-template map for `"positions"` and `"execution_fills"` that DOES include a `mode={mode}`
segment — i.e. a third, independent implementation that already assumed mode-partitioning was real. This wasn't
investigated further (out of scope for this filing pass) but is worth a look when scoping the fix: it may be evidence of
what the "correct" shape should look like, or it may itself be dead/inconsistent code.

## Why it matters

This is a live data-correctness bug in the storage layer for **execution fills, PnL attribution, and strategy
instructions** — three of the workspace's core financial-record datasets. Per CLAUDE.md's "Data pipeline correctness is
the heartbeat" hard rule and the batch=live determinism spine
(`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`, "paper(W) MUST equal batch-rerun(W)
trade-for-trade, ε=0 PROOF"), a mechanism that lets different trading modes silently clobber each other's persisted
fills/PnL/instructions at the same object path directly undermines that determinism guarantee — any downstream reader
(client-reporting-api's `compute_ledger_views`, a batch-vs-live reconciliation pass, a future trading-analyst job) that
expects mode-isolated data may instead be reading whichever mode wrote LAST, without any signal that a collision
occurred.

## Recommended decision

This needs an explicit design decision before a fix ships — a straight template edit is a **breaking path-shape change
for live production data** (existing objects at the old, mode-collapsed path may already hold commingled/ overwritten
data from multiple modes), not a bounded mechanical fix:

- [x] ✅ [RESOLVED-BY-OPERATOR 2026-08-19] P1. **Migration strategy DECIDED — Ruling 3.** _"Add `{mode}` to all four
      templates AND migrate existing data."_ / _"Ruling 3 — migrate, do not quarantine. The migration touches stored
      paths, so it is governed by [entity-rename-and-split-consumer-migration-rule](/codex/02-data/entity-rename-and-split-consumer-migration-rule.md):
      every consumer enumerated and migrated in the SAME change… Writer-only fixes are explicitly NOT what was
      chosen."_ Recorded in `/plans/audit/results/code_completion_scope_2026_08_19.md`. So option (a)/(b) below is
      settled as **(a) cut over, with the data migrated** — not a reader-fallback probe. Retagged from `[OPERATOR]`
      by T1 2026-08-19 on finding the gate answered but the tag stale.
      **Still operator-gated, separately**: the DATA movement itself (no backfills/migrations under the
      code-readiness tranche rules) — that is a launch decision, not a design one.
      **Superseded option list, kept for the record:** (a) add the `{mode}` segment
      and cut over fresh (old commingled objects become stale/orphaned, readers must know the cutover date), (b) add the
      segment with a reader fallback that probes the old flat path when the new mode-partitioned path is empty, (c)
      something else. Also decide the segment's value vocabulary (the narrower `batch`/`live`/`paper` string
      `domain_adapter.py`'s callers already use vs. the fuller `PipelineMode` enum) and whether `unified-trading-api`'s
      already-mode-partitioned `live_service.py` template should become the canonical shape instead of the
      `PATH_REGISTRY` one.
- [x] ✅ [CODE] P1. **Shipped — `unified-trading-library@783d98ec`.** Added the `{mode}` placeholder to all 6 live
      occurrences (`execution_fills`, `positions`, `strategy_instructions`, `pnl_attribution`, `strategy_orders`,
      plus one more `day={date}/mode={mode}/` template found during the pass), added `mode` to each
      `partition_keys` list, and removed `_MODE_KWARG_PENDING_MIGRATION` from `registry.py` entirely (confirmed
      absent via direct source inspection 2026-08-20). Byte-parity across writer/reader call sites verified as
      part of shipping, per `domain_adapter.py`'s own "BYTE-PARITY TWIN" convention.
- [x] ✅ [CODE] P1. **Harden `build_path()` itself** to fail loudly instead of silently dropping unconsumed kwargs —
      unified-trading-library@3313e3f441. `build_path()` now parses `path_template`'s actual placeholders (via
      `string.Formatter`) and raises `ValueError` on any passed kwarg the template doesn't consume, except two
      documented carve-outs: `category` (always harmlessly forwarded by `build_full_uri()`) and `mode` for the 5
      datasets above still pending the `{mode}` migration (todos 1/2) — hardening those 5 immediately would turn today's
      silent path collision into a hard crash on live writes/reads ahead of that migration landing, which is a worse
      regression than the bug this hardening targets. Added regression tests
      (`test_build_path_rejects_unconsumed_kwargs`,
      `test_build_path_mode_kwarg_carve_out_for_pending_migration_datasets`) in
      `tests/config_interface/unit/test_paths_registry_smoke.py`. QG green (316s), sentinel verified on origin.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
