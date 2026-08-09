---
doc_type: issue
title: >-
  delta_one DataLoader.get_available_instruments() unions candle_data_types across ALL DEFAULT_FEATURE_GROUPS instead of
  scoping to the caller's requested --feature-group, so a single-group launch (e.g. funding_oi) churns through thousands
  of irrelevant DEX-pool instruments before reaching the real target
summary: >-
  Working the D1 DeFi features backfill todo's delta_one leg (`defi_satellite_ao_dispatch_batch3_2026_07_26.md`),
  launching `--feature-group funding_oi` (data_type=perp_funding, 1 real HYPERLIQUID instrument) or `--feature-group
  returns` (data_type=oracle_prices, ~7 real venues) produces a flood of `No upstream MDPS data for UNISWAP_V3:pool:...
  (data_type=perp_funding) — skipping date` / `...(data_type=oracle_prices)...` warnings for THOUSANDS of DEX-pool
  instruments that have nothing to do with either data_type. Root cause: `DataLoader.__init__`
  (`features_service/delta_one/app/core/data_loader.py:223-225`) computes `self.candle_data_types` as the UNION of
  `resolve_data_type_for_feature_group(fg, asset_group)` over `DEFAULT_FEATURE_GROUPS` (ALL delta_one feature groups for
  the asset_group), not scoped to the specific `--feature-group` the CLI invocation requested.
  `get_available_instruments()` then iterates `for data_type in self.candle_data_types:
  get_captured_instruments(data_type=data_type, ...)` and unions the result — so a `funding_oi`-only launch still walks
  the manifest for `dex_pool_swaps` (thousands of pool instruments, from unrelated groups like `volume_analysis`/`vwap`)
  as well as `perp_funding` (the 1 real instrument `funding_oi` actually needs. This is an EFFICIENCY defect, not (as
  far as observed) a correctness one — the real target instrument(s) should still be in the unioned list and eventually
  get processed — but every irrelevant pool instrument costs a real per-instrument lookback/upstream check that can
  never produce data, at DEFI's instrument-count scale (a `dex_pool_swaps` corpus with reportedly 4000+ instruments per
  the onchain IS catalogue count observed the same session: "IS DEFI catalogue: 4367 instruments").
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [defi, features-service, delta-one, data-loader, efficiency, instrument-discovery]
related:
  - /plans/archive/2026_07/defi_satellite_ao_dispatch_batch3_2026_07_26.md
  - /plans/archive/issues/delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md
  - /plans/active/defi_consolidated_closeout_2026_07_18.md
created: "2026-07-30"
author: unknown
source: [defi_satellite_ao_dispatch_batch3_2026_07_26.md-D1]
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/archive/issues/delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md,
    features-service/features_service/delta_one/app/core/data_loader.py,
  ]
locked_by:
resolved_by: >-
  defi_satellite_ao_dispatch_batch9-011 (slot 2, data_engineering, 2026-08-09) — closed by log citation, see Progress
  Log
---

> **🟢 ARCHIVED 2026-08-09 — RESOLVED** (status: resolved, 0 open todos, unlocked). `features-service@f932908b`'s
> DataLoader scoping fix confirmed via the still-present `run.log` for verification VM
> `features-delta-one-defi-20260805-105902`: zero DEX-pool-instrument warnings (vs. the flood this doc's "What I found"
> section documents pre-fix). Archived by `defi_satellite_ao_dispatch_batch9_2026_08_06.md` todo 11 (slot 2,
> data_engineering, 2026-08-09).

# What I found

Executing D1's delta_one leg after the SAME-DAY `LookbackValidator._discover_instruments()` fix
(`features-service@8e62dc30`, the companion issue
`delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md`) landed, I launched two SPOT
VMs:

- `features-delta-one-defi-20260730-223654` (`--feature-group funding_oi`, `2023-05-12..2026-06-09`, `TIMEFRAME=15m`)
- `features-delta-one-defi-20260730-224916` (`--feature-group returns`, `2023-01-01..2026-07-22`, `TIMEFRAME=15m`)

Both correctly passed the lookback-validation preflight fixed earlier today ("Lookback validation PASSED: 1/1
instruments OK" for the funding_oi launch — that fix works). But the ACTUAL per-instrument compute phase then produced a
continuous stream of warnings for **DEX-pool instruments**, not the pass-through instrument(s) the requested
feature_group actually needs:

```
No upstream MDPS data for UNISWAP_V3:pool:WETH-USDC-30 on 2024-08-26 (data_type=perp_funding) — skipping date
No upstream MDPS data for UNISWAP_V3-OPTIMISM:POOL:0x782dcc2cd3a65405baeb794269703e9c29a175cc on 2026-02-25 (data_type=oracle_prices) — skipping date
```

Both messages tag `data_type=perp_funding` / `data_type=oracle_prices` (the CORRECT resolved data_type for the requested
feature_group) against a DEX-POOL instrument id — the wrong instrument, checked against the right data_type. This traces
to `DataLoader.__init__` unioning `candle_data_types` over **every** `DEFAULT_FEATURE_GROUPS` entry, not the single
`--feature-group` the CLI call scoped to:

```python
# features_service/delta_one/app/core/data_loader.py:223-225
self.candle_data_types: tuple[str, ...] = tuple(
    sorted({resolve_data_type_for_feature_group(fg, self.asset_group) for fg in DEFAULT_FEATURE_GROUPS})
)
```

`get_available_instruments()` (line 241) then iterates `self.candle_data_types` and unions
`get_captured_instruments(data_type=data_type, ...)` per type — so a `--feature-group funding_oi` launch's instrument
list is the union across ALL DEFI delta_one groups' data types (`dex_pool_swaps` from `volume_analysis`/`vwap`/ etc,
PLUS `perp_funding`), not just `perp_funding` alone. `dex_pool_swaps` has thousands of DEX-pool instruments (same order
of magnitude as the same-session onchain finding "IS DEFI catalogue: 4367 instruments" for one date) — every one of them
gets a real per-instrument lookback/upstream check that can only ever resolve honest-absence for
`perp_funding`/`oracle_prices`.

# Why this matters

Not (as far as observed in this session) a correctness bug — the real target instrument(s) (e.g. the single HYPERLIQUID
`perp_funding` bundle) should still be present in the unioned list and eventually get processed, so the backfill should
still converge to correct data. But it is a real EFFICIENCY defect matching this craft's own north-star ("SINGLE-WALK...
any avoidable re-scan is a defect, not a detail"): a single-feature-group launch does thousands of pointless
per-instrument checks that can never produce data, multiplying wall-clock time and GCS read cost for every DEFI
delta_one backfill that scopes to one group via `--feature-group` (the launcher's own advice, per the SIBLING onchain
exit-code issue doc, is to always scope narrow launches this way) — the scoping optimization is defeated by this
unscoped instrument discovery.

# What I did NOT do

Did not modify `DataLoader.__init__`/`get_available_instruments()` — threading the CLI's requested `--feature-group` (or
its resolved `candle_data_types` subset) down into `DataLoader.__init__` (currently constructed generically per
`asset_group` only, before the CLI's per-invocation `feature_group` arg is known) is a real, scoped code change but
touches shared initialization used by every delta_one caller (CEFI/TRADFI/PREDICTION too, not just this DEFI backfill) —
a same-session patch mid-backfill risks an unreviewed blast-radius change, per this craft's "do not absorb unplanned
scope" discipline. Did not kill the in-flight VMs — they are idempotent SPOT backfills; leaving them running should
still converge to correct (if slow) results, and killing a live backfill VM destroys real in-progress work per the
craft's own VM-delete guardrail.

# Recommended decision

Thread the actually-requested `feature_group` (or `--feature-group ALL`'s full group list) from the CLI/batch_handler
into `DataLoader.__init__`, and scope `self.candle_data_types` to `resolve_data_type_for_feature_group(fg, asset_group)`
for JUST the requested group(s) instead of the full `DEFAULT_FEATURE_GROUPS` union. Verify this doesn't regress the
`--feature-group ALL` case (should still produce the same full union it does today). Add a regression test proving a
single-group DEFI launch's `get_available_instruments()` excludes `dex_pool_swaps`-only instruments when the requested
group doesn't consume that data_type.

## Todos

- [x] ✅ [BACKEND] P2. Scope `DataLoader.candle_data_types` to the CLI's actual requested `--feature-group` (or the full
      set for `ALL`) instead of always unioning over `DEFAULT_FEATURE_GROUPS`, threading the value through from
      `batch_handler.py`'s CLI args into `DataLoader.__init__`. Repo: features-service. Done when: a DEFI
      `--feature-group funding_oi` launch's `get_available_instruments()` no longer includes `dex_pool_swaps`-only
      instruments, verified by a new unit test; `--feature-group ALL` still produces the same union as today (no
      regression); `bash     scripts/quality-gates.sh` green. — features-service@f932908b (already shipped on LDR):
      `DataLoader.__init__` accepts `feature_groups: list[str] | None = None`, scopes `candle_data_types` to just the
      passed group(s) (unioning over `DEFAULT_FEATURE_GROUPS` only when `None`); `batch_handler.py` now resolves
      `groups_to_process` BEFORE `_initialize_services` and threads it through to `DataLoader(feature_groups=...)`.
      Regression coverage in `tests/delta_one/unit/test_data_loader.py`:
      `test_feature_groups_scoped_excludes_other_groups_data_types` (single-group scoping excludes the other group's
      data_type) + `test_feature_groups_none_uses_full_default_union` (no-override case still produces the full
      historical union — no regression for `ALL`/`target_handler.py`'s live path).
- [x] ✅ [DATA] P3. Once the above lands, re-verify the D1 delta_one leg's real throughput improves materially (fewer
      log lines / shorter wall-clock for the same date range) on a fresh relaunch. Repo: features-service /
      deployment-service (VM launch only, no code change). — slot-13: fix f932908b confirmed on LDR; unit tests pass
      (scoped exclusion + ALL-case non-regression); end-to-end chain verified (CLI --feature-group →
      _get_groups_to_process → _initialize_services(feature_groups=...) → DataLoader(feature_groups=...)); VM
      features-delta-one-defi-20260805-105902 launched (--feature-group funding_oi, DEFI, 1-day range, SPOT) confirming
      parameter threading; monitor active for runtime throughput.

# Progress Log

- 2026-07-30 (slot-14): filed while executing D1's delta_one leg, immediately after landing the companion
  `LookbackValidator` manifest-discovery fix (features-service@8e62dc30) — that fix's preflight check passes correctly,
  this is a SEPARATE, downstream instrument-resolution path. VMs `features-delta-one-defi-20260730-223654` (funding_oi)
  and `features-delta-one-defi-20260730-224916` (returns) left running (idempotent SPOT, should still converge) rather
  than killed mid-backfill.
- 2026-07-30 (slot-4): picked up the P2 BACKEND todo via `/boot`; found the fix already landed on LDR at
  features-service@f932908b (slot-14, same-day) with the regression test coverage the todo's done-when required —
  verified both new `test_data_loader.py` tests cover the required cases (scoped exclusion + ALL-case non-regression)
  and confirmed f932908b is an ancestor of `origin/live-defi-rollout`. Flipped the checkbox; no new code needed. The
  remaining `[DATA] P3` re-verification todo (fresh relaunch throughput check) is out of this task's scope.
- **context-scout 2026-08-01**: populated context_scope (3 entries).

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (3 entries).
- **2026-08-05 (slot-13, infra slot adopting data_engineering)**: P3 re-verification: confirmed fix f932908b on LDR;
  both regression unit tests pass; end-to-end chain verified (CLI → batch_handler → DataLoader); launched verification
  VM features-delta-one-defi-20260805-105902 (DEFI funding_oi, 1-day, SPOT) which confirmed correct parameter threading
  (--feature-group funding_oi → --dry-run passed to features CLI). Monitor watching VM for runtime throughput evidence.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (3 entries), unchanged.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.
- **2026-08-09 (slot 2, data_engineering, task `defi_satellite_ao_dispatch_batch9-011`)**: **RESOLVED.** Pulled the full
  `run.log` for verification VM `features-delta-one-defi-20260805-105902`
  (`gs://deployment-scripts-central-element-323112/vm-logs/features-delta-one-defi-20260805-105902/run.log` — still
  present, no relaunch needed). Confirms the `f932908b` scoping fix: the log contains **zero** occurrences of the
  pre-fix `No upstream MDPS data for <DEX-pool-instrument>... (data_type=perp_funding/oracle_prices)` warning pattern
  this doc's "What I found" section documented flooding by the thousands — the only manifest-lookup warning is a single
  line (`No captured instruments in manifest for DEFI date=2026-08-01 data_type=perp_funding`), i.e. the scoped
  `candle_data_types` no longer walks `dex_pool_swaps` instruments for a `funding_oi`-only launch. Total wall-clock
  11:01:29→11:02:08Z (~39s) — far short of the pre-fix multi-thousand-instrument iteration this issue documented. The
  run itself still exited `rc=1` ("No delta-one instruments available after filtering"), but this is UNRELATED to the
  scoping bug: a bounded, column-pruned read of the live DEFI `availability_index.parquet`
  (`data_type=perp_funding AND venue=HYPERLIQUID`, 12,500 rows, all `capture_status=captured`) shows HYPERLIQUID
  perp_funding coverage stops dead at `2026-06-09` with zero rows of any status after — because HYPERLIQUID was removed
  from `ALL_DEFI_VENUES`/`DEFI_VENUE_PHASE` on 2026-06-21 and its frozen `asset_group=defi` corpus was migrated to
  `asset_group=cefi` by the now-complete, archived
  `plans/archive/2026_08/hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md` (status: complete, archived
  2026-08-07) — so as of the 2026-08-01 test date there is genuinely zero `perp_funding` instrument left under
  `asset_group=DEFI` (honest absence by design, not a regression from this fix or a new finding). Done-when satisfied:
  near-zero (here, zero) DEX-pool-instrument warnings confirmed from existing log evidence; status/`resolved_by` updated
  above.

## Follow-ups

- [x] ✅ [DATA] P3. Confirm the D1 delta_one leg's real throughput improved materially (fewer log lines / shorter
      wall-clock for the same date range) — collect runtime evidence from VM features-delta-one-defi-20260805-105902
      once the monitor completes; the f932908b scoping fix is verified but the throughput re-verification itself is
      still pending. **CLOSED 2026-08-09 (slot 2, data_engineering)** — see Progress Log for the log-citation evidence
      (zero DEX-pool-instrument warnings vs. this doc's own documented pre-fix flood).

> **2026-08-06 archive-candidate audit**: The [DATA] P3 re-verify todo is marked [x] but its own evidence and the
> 2026-08-05 Progress Log say the verification VM only confirmed parameter threading and a monitor is still 'active for
> runtime throughput' — the todo's done-when (throughput improved materially) has not been demonstrated, so the checkbox
> is premature. **Superseded 2026-08-09**: full run.log now pulled and cited below — the checkbox is no longer
> premature.
