---
doc_type: issue
title: DeFi-MVP backfill optimization + correctness defects — implementation-ready (T3), gated on auth + 2-VM canary
summary:
  The T3 study + refined workflow produced a validated optimized-backfill design, a provisional ETA band, and found 3
  live correctness defects. The fixes are designed against proven in-repo patterns and ready to implement, but every one
  changes the live capture path and its validation needs a 2-VM TheGraph canary + a re-backfill — both blocked by the
  expired gcloud CLI auth. This doc is the dispatchable unit.
status: open
nature: issue
asset_group: defi
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer]
tags: [defi, backfill, optimization, thegraph, pagination, spot, preemption, eta]
related: [defi_consolidated_closeout_2026_07_18, defi_available_at_clobbered_by_wallclock_2026_07_20]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
drift_direction: stable
depends_on: []
source: ["filed 2026-07-20 during DeFi MVP backfill work; frontmatter completed 2026-07-21 to pass the schema gate"]
resolved_by:
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# DeFi-MVP backfill optimization + correctness defects — READY

Consolidates the T3 study (`wzrlkakb0`) + the refined optimization workflow (`wf_c3e50e71-248`, 12 agents). All fixes
are designed against a **proven in-repo pattern**; none is implemented yet because each changes the LIVE capture path
and its validation needs the auth-blocked 2-VM canary + re-backfill (see § Auth block).

## The one structural fact

DeFi is **NOT single-IP-capped** (unlike cefi/Tardis) — its sources are keyed/gateway-pooled (The Graph key pool, RPC
providers, Pyth Hermes). So it scales horizontally across N VMs, which cefi never could — the linear ETA divisor.
**BUT** the real ceiling is likely the **shared TheGraph key pool**: every fat venue
(uniswapv3/morpho/balancer/curve/aave) draws the same pooled keys, and **429s classify as `attempted_failed`, so an
over-scaled wave CORRUPTS THE MANIFEST** — the Tardis-N>1 failure shape through a different door. **Canary at 2 VMs and
watch the 429 rate before any wide wave.**

## Correctness defects (fix these FIRST — they are bugs, not optimizations)

- [x] [SCRIPT] P0. **evm_defi history queries are UNPAGINATED (`first: 1000`)** — SHIPPED `mtds@6e2677b9` (QG green,
      6544 passed; +2 tests prove 1500 rows across 2 pages vs single-shot 1000). `_paginate_history` mirrors
      `lending_indices_subgraph._paginate`. — `_AAVE_V3_HISTORY_QUERY`, `_COMPOUND_V3_MESSARI_HISTORY_QUERY`,
      `_COMPOUND_V3_CUSTOM_HISTORY_QUERY` in `market-tick-data-service/.../cli/handlers/evm_defi_handler.py`
      (`:333/:354/:374`) query `reserveParamsHistoryItems`/`marketDailySnapshots` with `first: 1000` and no
      `skip:`/cursor. The Graph caps `first` at 1000, so a busy AAVE/Compound day (>1000 items) is **silently
      truncated**. FIX: route them through a timestamp-cursor paginator — **mirror the proven `_paginate` in
      `lending_indices_subgraph.py:95`** (cursor on `timestamp_gte`, dedup by `record_id`, stop at `len<page_size`,
      `max_pages=50` safety cap, `LENDING_INDICES_PAGINATED`- style event). Add a unit test: mock the subgraph
      returning >1000 items across 2 pages → assert all captured, no dup. Captured counts will go UP on busy shards —
      that is the fix landing, not a regression.
- [x] ✅ [SCRIPT] P0. **Both DeFi launchers MISS the SPOT preemption contract** — SHIPPED `deployment-service@684813a`
      (already on `origin/live-defi-rollout`). Both `launch-mtds-solana-defi-backfill-vm.sh` (`:175-194`) and
      `launch-defi-backfill-vm.sh` (`:153-173`) now call `lc_write_preemption_signal_file` + `lc_write_launch_params`
      (persisting START_DATE/END_DATE/protocols/force), set
      `--metadata-from-file="shutdown-script=${PREEMPTION_SIGNAL_FILE}"`, and carry
      `--instance-termination-action=DELETE --no-restart-on-failure` on the SPOT provisioning flags — mirrors
      `launch-cefi-sharded-backfill.sh:568-589` exactly. `launch-defi-backfill-vm.sh`'s START_DATE/END_DATE were also
      fixed to read from an inherited env so a PROGRESS-checkpoint-resumed relaunch round-trips instead of being
      clobbered by the hardcoded default. Verified by reading both launchers' current HEAD; checkbox was outstanding
      only because the code-ship commit never flipped it.
- [x] ✅ [DATA] P0. **`available_at` clobbered by wall-clock `now()`** — filed separately as
      `defi_available_at_clobbered_by_wallclock_2026_07_20.md`, now RESOLVED + ARCHIVED. Operator ruled 'keep the
      on-chain tick' (Option A): `mtds@f7af6ece` removed the 3 verified clobbers, `mtds@51ec9af2` extended the fix to
      the broader 17-handler follow-up (9 handlers left on wall-clock as the honest fallback, no on-chain timestamp
      exists). Both SHAs verified ancestors of `origin/live-defi-rollout`. Checkbox was outstanding only because the
      resolving commits never flipped it here.

## Optimization — the perf bundle (ship as ONE commit or not at all; canary-gated)

- [x] ✅ [SCRIPT] P1. **knobs + async fan-out + executor-offload, together.** The workflow proved the 3 concurrency
      knobs are **INERT alone** (0% gain, 3 unread config fields) unless shipped WITH the fan-out + dedicated executors,
      so bundle: (a) `service_config.py` — add `defi_max_concurrent_fetches` (32), `defi_max_inflight_tasks` (128),
      `defi_max_concurrent_uploads` (64), mirroring the Tardis 3-knob block; (b) replace the sequential
      `for protocol in protocols` / `for shard: _upload_parquet(...)` loops in `solana_defi_handler.py` +
      `dex_pools_handler.py` with a bounded `asyncio.Semaphore` fan-out — **reuse UTL's `ParallelPerSymbolRunner`**
      (already has per-atom failure isolation + in-flight-never-cancelled, so the shard-isolation contract is
      preserved); (c) run the blocking `_upload_parquet` via `loop.run_in_executor` on a **dedicated**
      `ThreadPoolExecutor` (NEVER the default — cefi's DNS-starvation wedge), concurrent per-instrument uploads. Verify:
      shard isolation preserved, no `raise` in per-shard loops, `record_captured` grain unchanged, no upload
      reorder/drop. **CANARY at 2 VMs, watch 429, before any wide wave.**

      **DONE 2026-07-27 (slot-6).** (a)/(b)/(c) as originally scoped were ALREADY SHIPPED — `mtds@ff1b5d51`
          "feat(defi): MTDS DeFi perf bundle -- concurrency knobs + async fan-out + executor-offload", ancestor of
          `origin/live-defi-rollout`. `defi_max_inflight_tasks`/`defi_max_concurrent_uploads` are live-consumed
          (`ParallelPerSymbolRunner` fan-out in `solana_defi_handler.py`/`dex_pools_handler.py`; dedicated
          `_defi_upload_executor.py` mirroring `tardis_csv_transport._get_parse_executor`). This dispatch closed the ONE
          real gap found: `defi_max_concurrent_fetches` was declared but never read (grep confirmed zero non-definition
          references), contradicting its own docstring's decoupled-from-defi_max_inflight_tasks promise. Fixed in
          `mtds@4cf0ea3d` — new `_defi_fetch_semaphore.py` (lazy-singleton `asyncio.Semaphore`, mirrors
          `_defi_upload_executor.py`'s shape) applied at the 3 fetch call sites in this todo's scope: `solana_defi_handler.py`'s
          `collector(session)` dispatch, and `_dex_pools_subgraph.py`'s Solana-native `fetch_*` dispatch + the shared
          EVM/TheGraph `_execute_subgraph_query`'s `session.post(...)` (the doc's own "structural fact" — the shared key
          pool is the real ceiling — held only for the request, released before the retry backoff). New
          `tests/unit/test_defi_fetch_semaphore.py` (4 tests) + 132 pre-existing solana_defi/dex_pools handler tests + the
          full `quality-gates.sh` suite (7101 items) all green. Deliberately did NOT touch
          `evm_defi_handler.py`/`lending_indices_handler.py`/`risk_params_handler.py` — each has its own separate
          `_execute_subgraph_query` copy, out of this todo's named scope. **CANARY at 2 VMs still required before any wide
          wave** — unchanged, still gated on the Auth block (§ below); this todo covers the CODE only, per the doc's own
          "safe to implement + unit-test without it; only their live validation is blocked."

## Descoped / do-NOT-implement-as-specced (workflow demolished these)

- Multi-day batched subgraph "~300× fewer round-trips" — **WRONG**: pools are already batched 500-at-a-time, real
  request-axis ceiling is **~2×**; descoped to two cheap carve-outs, not the headline lever.
- The streaming-finalizer `write_defi_rows` rewrite — **SOUND_WITH_FIXES but must NOT be built as specced**: its
  `rows_by_instrument_id` derivation is underivable (router keys on `shard_path`; the design's own symbol-merge makes it
  N-ids-one-rowcount-unsplittable) → would corrupt `record_captured` grain. Redesign before touching.

## ETA (PROVISIONAL — do not quote the optimized row until calibrated)

- W = **11.65M** defi-MVP `expected_unattempted` atoms (measured from the `_index`, after stripping ~43k cefi-misfiled
  EXTENDED/LIGHTER). Upper-bound band to **63.9M** (the v2-enumerator's measured-but-unapplied seed) — **report as a
  band**.
- ETA_wall = W / (N × R_vm × η), η≈0.7. Baseline R_vm≈6.5 atoms/s/VM → **~29.6d (N=1) / ~3.7d (N=8)**. Aspirational
  post-optimization R_vm≈25 → **~7.7d / ~1.0d**. The optimized row is unquotable until the calibration protocol runs.
- **Calibration protocol:** land the perf bundle, run ONE representative dense-2025 venue-day, measure R_vm = TARGET
  artifacts by `time_created` (entity-scoped to the exact venue/chain/instrument_type/data_type) cross-checked against
  manifest atoms — NEVER log activity, NEVER a first-of-month day. Recompute ETA_remaining hourly.

## Auth block (why none of this is shipped yet)

The gcloud CLI account expired mid-session (`Reauthentication failed. cannot prompt during non-interactive execution`;
likely from the account reset). ADC still works (GCS read/write via Python) but `gcloud compute` (VMs), `gcloud run`
(consolidator/jobs), and `gcloud storage` are blocked. So the 2-VM canary, the re-backfill that validates the pagination
fix, and `/data-pipeline-check-mtds` all need an interactive `gcloud auth login` first. The CODE fixes above are safe to
implement + unit-test without it; only their live validation is blocked.
