---
doc_type: issue
title:
  DeFi bridge_events (ACROSS/STARGATE) historical backfill — the assumed CLI gap does NOT exist; real blocker is the
  already-tracked mode= threading todo
summary: >-
  Investigated the dispatched todo's premise ("bridge_events_handler.py has no --start-date/--end-date CLI support ...
  confirmed via grep, zero matches") before filing a blocked-on-unbuilt-tooling doc as instructed. The grep-zero-matches
  was a grep-then-conclude trap: --start-date/--end-date is generic ServiceBootstrap/UnifiedServiceHandler
  infrastructure (add_date_args defaults True), not something individual handlers implement — verified by reading
  bootstrap.py, the UnifiedServiceHandler adapter, and BatchIO/DateRangeInput end-to-end. BridgeEventsHandler.process()
  already correctly consumes the per-day BatchPayload.date the framework hands it. No new CLI flag work is needed. The
  actual blocker for a genesis-to-present backfill is that bridge_events_handler.py's _catalog_preflight() calls
  assert_defi_catalog_fresh() without mode=, defaulting to "live" freshness semantics that fail-closed on any date >24h
  old — the exact "historical-backfill block" bug _defi_catalog_freshness.py's own docstring already documents as fixed
  elsewhere, but NOT wired into this handler. That fix is ALREADY a P1 todo in the SAME dispatching plan (the "Thread
  mode= into assert_defi_catalog_fresh() for the 9 remaining DeFi handlers" todo, which explicitly names
  bridge_events_handler.py) — so no new fix todo is filed here, only a small follow-up verification todo once that fix
  ships.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [defi, bridge-events, backfill, cli-convention, catalog-freshness, correction]
related: [/plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md, /codex/02-data/pipeline-mode-partition.md]
created: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
source: >-
  Dispatched todo in plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md ("File a new tracked issue doc for the
  ACROSS/STARGATE bridge_events historical-backfill capability gap"), itself sourced from
  plans/archive/issues/defi_five_never_captured_venues_fix_2026_07_22.md. The todo's premise (no --start-date/--end-date
  CLI support) was verified FALSE before filing — see "What I found" below.
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
resolved_by:
---

# DeFi bridge_events historical backfill — corrected finding

## What I found

The dispatched todo claimed: "`bridge_events_handler.py` has no `--start-date`/`--end-date` CLI support (confirmed via
grep, zero matches), so the daily cron can't be reused for a historical backfill to genesis (ACROSS 2021-11-11, STARGATE
2022-03-17) without that flag first."

Grepping `bridge_events_handler.py` for `add_argument`/`start-date`/`start_date` does return zero matches — but that's
because date-range CLI plumbing is NOT something individual `UnifiedServiceHandler` subclasses implement. Read the
actual consumer chain (per CLAUDE.md's "Grep-then-READ, not grep-then-conclude" rule) instead of trusting the grep:

1. `market-tick-data-service/cli/main.py:541` calls
   `ServiceBootstrap(service_name=..., operations={"collect-bridge-events": BridgeEventsHandler, ...}, ...)` with no
   `add_date_args` override.
2. `unified-trading-library/unified_trading_library/service_framework/bootstrap.py` — `ServiceBootstrap.__init__`
   defaults `add_date_args: bool = True`. This applies service-wide, to every operation in the dict,
   `collect-bridge-events` included.
3. `bootstrap.py:_adapt_operations()` wraps every `UnifiedServiceHandler` subclass (including `BridgeEventsHandler`) in
   an auto-generated `_Adapter(BaseModeHandler)` via `service_framework/_adapter.py:make_handler_adapter()`.
4. `_adapter.py:_Adapter._build_io()` reads `args.start_date`/`args.end_date` off the parsed CLI args and constructs
   `BatchIO(start_date=..., end_date=..., ...)` — genuinely generic, no handler-specific code required.
5. `service_framework/io_batch.py`'s `DateRangeInput` iterates `get_date_range(start_date, end_date)` and yields one
   `BatchPayload(date=<day>)` per day in the range via `__anext__`.
6. `_adapter.py:_drive_serial()`/`_drive_concurrent()` call `handler.process(payload)` once per yielded `BatchPayload` —
   shard-level failure isolation preserved per date.
7. `bridge_events_handler.py:BridgeEventsHandler.process()` already correctly branches on
   `isinstance(payload, BatchPayload) and payload.date` to resolve `target_date` — it is NOT hardcoded to `date.today()`
   (unlike `deribit_options_chain_handler.py`, whose own comment in `main.py` honestly flags THAT handler as `process()`
   collecting `date.today()` only — a real instance of this class of bug, just not in bridge_events).

**Conclusion:
`--operation collect-bridge-events --mode batch --start-date 2021-11-11 --end-date <today> --asset-group defi` already
walks day-by-day from ACROSS's genesis to today, today, with zero code changes.** The "missing CLI flag" premise is
false. No CLI/handler code needs to be built for the flag itself.

### The real blocker (already tracked elsewhere in this same plan)

`bridge_events_handler.py:_catalog_preflight()` calls:

```python
if assert_defi_catalog_fresh(
    project_id=self.runtime.gcp_project_id or "",
    on_date=target_date,
    correlation_id=date_str,
):
```

— omitting `mode=`. `assert_defi_catalog_fresh()`'s signature defaults `mode: str = "live"`
(`market-tick-data-service/cli/handlers/_defi_catalog_freshness.py:174`). Per that function's own docstring ("MODE-AWARE
freshness (codified 2026-06-24 — the historical-backfill block fix)"), `live` mode requires the instruments-catalog
manifest row to be <24h fresh — correct for today's date, but WRONG for a historical `batch` date, where the correct
property is "does the catalogue cover `on_date`" (checked via `_batch_catalog_covers_date`, unused here because `mode=`
is never passed). Without `mode="batch"` threaded through on a batch-mode run, every date older than ~24h fails closed
at the preflight gate with `UPSTREAM_INSTRUMENTS_CATALOG_STALE` — reproducing the exact "durable defi-stuck root cause"
bug that same docstring says was already fixed for OTHER handlers.

This exact fix is **already**
todo #`[SCRIPT] P1. Thread mode= into assert_defi_catalog_fresh() for the 9 remaining DeFi handlers still omitting it`
in `plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md` — `bridge_events_handler.py` is explicitly named in
that todo's handler list. No new fix todo is filed here to avoid a duplicate.

## Why it matters

Filing a "blocked on unbuilt CLI tooling" issue doc as originally instructed would have introduced a false finding into
the tracked corpus — a future worker reading it would build unnecessary `--start-date`/`--end-date` argparse plumbing
that already exists generically, wasting effort and adding handler-specific code that fights the shared framework
convention (every other DeFi handler gets this for free from `ServiceBootstrap`). The actual, real blocker was already
correctly identified and tracked by a DIFFERENT todo in the same plan — this doc exists so that todo's fix is understood
to _also_ unblock the bridge_events historical backfill, and so nobody re-investigates the CLI-support question again.

## Recommended decision

- [ ] [DATA] P2. Once the "Thread mode= into assert_defi_catalog_fresh()" todo ships for `bridge_events_handler.py`
      (passing `mode=('batch' if runtime.mode is batch else 'live')`, mirroring the pattern already shipped for
      `dex_pools_handler.py`/`risk_params_handler.py`/`lst_rates_handler.py`), verify a real
      `--operation collect-bridge-events --mode batch --start-date 2021-11-11 --end-date <run-date> --asset-group defi`
      invocation actually captures ACROSS rows starting at or after 2021-11-11 (its real on-chain `FundsDeposited`-topic
      genesis) and STARGATE rows starting at or after 2022-03-17, with no `UPSTREAM_INSTRUMENTS_CATALOG_STALE` failures
      on historical dates. Repo: market-tick-data-service. Genesis dates per the source issue doc
      (`plans/archive/issues/defi_five_never_captured_venues_fix_2026_07_22.md`), not independently re-derived here.
      **PRECONDITION CONFIRMED SHIPPED 2026-07-29 (batch closeout pass)**: `bridge_events_handler.py:265` now calls
      `assert_defi_catalog_fresh(..., mode=("live" if _run_tag == "live" else "batch"))` —
      `market-tick-data-service@c38e1b3f` ("fix: thread mode= into assert_defi_catalog_fresh for 9 remaining DeFi
      handlers") already landed this exact fix, `bridge_events_handler.py` included. **Still open**: the actual
      verification run (`--start-date 2021-11-11 --end-date <today>`) is a real multi-year production capture backfill
      against live GCS/instruments-catalog — not attempted this session (out of a bounded doc-closeout pass's scope;
      genesis-to-present is a real data-capture operation, not a code check). Left `- [ ]` for whoever schedules the
      actual backfill run.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - locked_by set; residual is a genesis-to-present multi-year
  production capture backfill with no VM-launch gating stated on the todo
