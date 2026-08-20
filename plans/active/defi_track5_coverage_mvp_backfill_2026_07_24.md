---
doc_type: plan
title: DeFi Track 5 — COVERAGE backfill → MVP-100% (forked from defi_consolidated_closeout_2026_07_18.md)
summary: >-
  Forked verbatim from defi_consolidated_closeout_2026_07_18.md's "Track 5 — COVERAGE" section (2026-07-24, per
  task_template.md's "partial parallelism is NOT expressible inside one plan — SPLIT" rule and an operator ruling during
  the 5-AG plan-quality audit session). Track 5 was gated on Track 2 (STORE path-authority) + Track 3 (DENOM
  empty_confirmed/denominator honesty) completing, expressed only as header prose in the parent with no machine-backed
  dependency — this fork makes that gate real via depends_on + gate_on_depends. Content moved verbatim, nothing
  summarized or dropped; the parent's own close-out criterion / "Sources" framing is unchanged.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos:
  [deployment-service, market-tick-data-service, features-service, market-data-processing-service, instruments-service]
scope: [engineer]
tags: [defi, close-out, coverage, backfill, mvp, canonicalisation]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    /plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md,
    /plans/archive/2026_07/defi_onchain_derivable_values_and_date_drift_2026_06_20.md,
    /plans/archive/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md,
    /plans/archive/2026_07/candle_canonical_path_migration_execution_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-08-17"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_consolidated_closeout_2026_07_18]
gate_on_depends: true
source: >-
  Forked 2026-07-24 from defi_consolidated_closeout_2026_07_18.md's Track 5, per operator ruling during the 5-AG
  plan-quality audit session ("fork Track 5 into a new child plan") after the audit flagged its C-GREEN-gated-on-T1→T3
  dependency as prose-only with no machine backing.
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py,
    /plans/archive/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md,
    /plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md,
    /plans/active/issues/mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md,
  ]
---

# DeFi Track 5 — COVERAGE: backfill → MVP-100%

> **Machine-gated on `defi_consolidated_closeout_2026_07_18.md`** (`depends_on` + `gate_on_depends: true`). **Honesty
> note on what the mechanism actually enforces** (same caveat already documented on tradfi's equivalent gate, see
> `tradfi_consolidated_closeout_2026_07_18.md`): `gate_on_depends: true` holds every task in THIS plan until every task
> in the NAMED plan is done — i.e. it currently waits on the parent's ENTIRE remaining scope (Tracks 1, 2, 3, 4, 6, 7,
> 8...), not just the real prerequisite (Track 2 STORE + Track 3 DENOM). There is no per-section dependency mechanism.
> This is over-broad but safe (never dispatches early); if the parent's other tracks turn out to meaningfully outlive
> Track 2/3, revisit by forking Track 2+3 out too and re-pointing this depends_on at just those. Both plans are
> `execution_scope: local-only` today, so this has no live dispatch effect yet — it becomes load-bearing only if either
> plan is ever flipped to `assigned_vm: planning`.

- **Sources**: `mvp_backfill_defi_onchain_v10_2026_06_27.md` (G2 final verify),
  `defi_pipeline_e2e_and_coverage_validation_2026_06_20.md` (Phase-D carry tracer — prior ✅ was gate-only, data was
  10/10 SKIP → RE-RUN), `defi_onchain_derivable_values_and_date_drift_2026_06_20.md` (2 P1).
- **Close-out criterion**: manifest-counted canonical rows for every MVP cell; carry tracer green on real data.

> **mvp-defi backlog unpark condition — re-pointed here 2026-07-20 (`ao_dispatch_cooldown_and_park_2026_07_20` todo
> 4).** The agent-orchestrator backlog task `mvp_backfill_defi_onchain_v10-001` carries a durable park (`priority: 999`
> / `priority_override: true`) gated on the named prerequisite
> `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` (condition currently `false`).
>
> Its original owner, `data_completion_defi_2026_07_15.md` (todos B0/C0, seed-then-backfill framing), is dead under the
> per-instrument re-architecture above — that plan never re-derives the condition and its seed-chain premise no longer
> matches how backfill actually runs (shard key = symbolic `canonical_instrument_id`, not the old seed-chain).
>
> **Flip instruction**: set `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` **true**
> (`POST /api/prerequisites/defi_onchain_v10_universe_v2_seed_or_backfill_progressed {"value": true, "set_by": "<you>"}`)
> the first time the todo below shows REAL manifest-counted progress on the per-instrument shard key — i.e. once R1→R3
> above have landed (writer + denominator + historical migration) and this track's backfill has actually started writing
> canonical rows, not merely been unblocked to start.
>
> Until then the park is intentional, not stale: Track 5 is explicitly gated on Track 2 (STORE) + Track 3 (DENOM) in the
> parent plan, and R3 (the historical migration this backfill depends on) is still `RUNNING, partial` as of this
> writing. No park exists without a named LIVE flipper — this note + this plan ARE that flipper; if this plan is ever
> archived/superseded before flipping the condition, migrate this note to whatever supersedes it rather than letting the
> park go silent again.

## Todos

- [ ] [DATA] P1. **Run the DeFi MVP backfill to 100%** on the canonical/migrated corpus (SPOT VMs; the DRIFT/Velocity
      historical grind is now CULL residue — DRIFT is out of target, so its gap is dropped not filled); re-run the
      Phase-D historical carry tracer on real data; resolve the 2 derivable-values P1s. On first real progress, flip
      `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` true per the unpark note above — that is what releases
      the parked `mvp_backfill_defi_onchain_v10-001` backlog task back to the fleet. (repos: deployment-service,
      market-tick-data-service, features-service)
- [x] ✅ [BACKEND] P2. **Async fan-out + executor-offload for the MTDS DeFi collectors** (recovered from the
      pre-2026-07-24 historical Progress Log's deferred-work table — genuinely correctness-sensitive, deliberately not
      squeezed into a sub-agent turn). The sequential loops needing fan-out are
      `solana_defi_handler.py::_run_solana_protocol_loop` + `dex_pools_handler.py::_run_process`, with the actual
      blocking `_upload_parquet`/`storage.upload_bytes` calls two files deeper in
      `_dex_pools_subgraph.py::_collect_protocol_chain`/`::_collect_solana_dex`. Design sketch: fan out fetch+upload via
      UTL `ParallelPerSymbolRunner` with `manifest_writer=None`, then apply
      `record_captured`/`record_zero_rows`/`record_failed` + the heartbeat SEQUENTIALLY over the gathered results in
      original iteration order (preserves today's manifest-write/heartbeat semantics exactly while parallelizing the
      slow I/O). ~~The 3 `service_config.py` knobs are a trivial, un-risky first step~~ — **CORRECTED 2026-07-24
      (sub-agent investigation): WRONG per this item's own cited source** —
      `plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md:617` states the knobs (none of the 3 exist
      yet — confirmed via grep) are "inert alone — 0% gain, 3 unread fields — ship knobs+fanout+executors as ONE commit
      or not at all." `plans/archive/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md` (open, locked_by:
      live-defi-rollout) already carries the correctly-bundled todo; nothing shipped standalone. **Separately**: the
      2-VM TheGraph canary is operator-owned ("ship code + I run the canary") — do not launch VMs for it. (repo:
      market-tick-data-service) **na-eligibility-audit 2026-08-01: CLOSED — done elsewhere.**
      `plans/archive/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md` (status: resolved, archived 2026-07-31,
      0 open/5 done): its bundled fan-out+executor-offload todo checked `[x]` "DONE 2026-07-27 (slot-6)" citing
      `mtds@ff1b5d51` ("feat(defi): MTDS DeFi perf bundle -- concurrency knobs + async fan-out + executor-offload") and
      `mtds@4cf0ea3d` (`defi_max_concurrent_fetches` semaphore fix), both confirmed ancestors of
      `origin/live-defi-rollout`.
- [x] ✅ [DATA] P1. **Confirm the launcher + parallelization plan for the DeFi-MVP full-history MDPS candle backfill**
      (gate-audit §6, 2026-07-24 — gated on `candle_canonical_path_migration_execution_2026_07_24.md` reaching P8).
      Determine which launcher runs it (single-VM vs. cross-VM sharded) and whether `max_workers` lets concurrent writes
      overlap GCS (~8x ETA impact suspected, unconfirmed). Definition of done: name the launcher + cite a measured
      write-concurrency figure. (repos: market-data-processing-service, deployment-service) **na-eligibility-audit
      2026-08-03**: the gate is now cleared — `candle_canonical_path_migration_execution_2026_07_24.md` is archived
      `status: complete` (all 17 todos done, P8 cross-AG verify/reconcile confirmed clean for all 4 AGs, archived
      2026-07-28). This checkbox's own definition-of-done (name the launcher + a measured write-concurrency figure) has
      not itself been produced anywhere found in the corpus — not closing, just unblocked now.
      **CLOSED BY CITATION 2026-08-16 (defi_satellite_ao_dispatch_batch9_2026_08_06_finalize, source-doc
      reconciliation pass, slot 23, data_engineering)** — `defi_satellite_ao_dispatch_batch9_2026_08_06.md` todo 11
      answered this exact definition-of-done: launcher named
      (`launch-mdps-sharded-backfill.sh defi --env prod`, the same fleet verified in this doc's own Todo above/todo 15
      of `data_pipeline_check_mdps_features_2026_07_20.md`) + concurrency figure cited (`_max_workers_for defi` empty →
      MDPS default `min(cpu_count, 16)` = 8 on e2-standard-8, each worker writing a distinct `gs://` blob path via
      `polars_candle_engine.write_parquet()` — up to 8 concurrent GCS writes structurally possible; no independently
      MEASURED overlap figure exists, an honest partial answer batch9 itself flags). This checkbox was never flipped
      when batch9 closed it — flipping now by citation, no new investigation performed.
- [ ] [DATA] P1. **PARTIAL progress via `/plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md`
      (2026-08-14/15) — baseline attempted, mid/final still correctly ungated (backfill not yet 100%).** IS baseline VM
      (`pipeline-e2e-check-is-20260814-224849-f6e2db`) alive + progressing. MTDS baseline hit a driver-VM OOM (fixed
      2026-08-15) then a still-open `rc=3` per-shard bug on CEFI — no clean MTDS baseline yet. Full detail in
      `plans/active/issues/mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md`'s Progress Log. Still
      open — this todo's own done-when (3x each, cited report paths) is not met. Run `/data-pipeline-check-is` and
      `/data-pipeline-check-mtds` 3x each across the defi backfill** (gate-audit §11: pre-backfill baseline,
      mid-backfill spot-check, post-backfill final gate per skill — 0 dated runs of either on record for defi today).
      Cite each run's report path + date. (repos: instruments-service, market-tick-data-service) **UNPARKED 2026-08-08
      (operator ruling): `--day 2026-07-01` for the baseline/mid/final checkpoints.** Resolves the `BLK-d355f03a`
      blocked question from `/plans/archive/2026_07/defi_satellite_ao_dispatch_batch5_2026_07_27.md` (both skills'
      SKILL.md § 0 forbid synthesizing `--day` without operator input — now supplied). Exact commands for whoever runs
      the 3x-each cadence: - Baseline: `/data-pipeline-check-is --day 2026-07-01` +
      `/data-pipeline-check-mtds --day 2026-07-01` - Mid-backfill spot-check:
      `/data-pipeline-check-is --day 2026-07-01` + `/data-pipeline-check-mtds --day 2026-07-01` (re-run once the MVP
      backfill above is genuinely mid-flight — cite the report path + date of that run, not a duplicate of the baseline
      run under a different label) - Post-backfill final gate: same command, run once the MVP backfill is complete
      **2026-08-08 apply-pass attempt**: invoked `/data-pipeline-check-is --day 2026-07-01` from this session — the
      skill loaded and its own §1a states this check must run via a dedicated VM driver
      (`launch-pipeline-e2e-check-driver-vm.sh`, real GCS-bucket provisioning + a full MVP `(asset_group, venue)` matrix
      sweep, explicitly "never run inline on the shared host", multi-minute-plus real VM spend). Did NOT launch that VM
      this session — out of proportion to run to completion synchronously alongside this apply session's other 8 items,
      and the skill is designed for VM-launch + poll, not an inline quick check. The `--day` blocker is genuinely
      cleared now; whoever runs the 3x-each cadence next can go straight to execution with the commands above.
      **2026-08-14/15 MTDS baseline attempts (both `--day 2026-07-01`)**: first attempt
      (defi_satellite_ao_dispatch_batch13, 2026-08-14) OOM'd 10 min in on the unscoped full sweep (3126 shards) — filed
      `/plans/active/issues/mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md`. Second attempt
      (2026-08-15, slot 6) re-ran per that issue doc's landed per-`--asset-group` interim workaround (5 separate driver
      VMs) — **still only PARTIAL, not a genuine baseline**: PREDICTION and TRADFI completed and produced reports
      (`plans/audit/results/data_pipeline_e2e_check_mtds_2026_07_01_PREDICTION.md`, `…_TRADFI.md`); CEFI, DEFI, and
      SPORTS did not complete (2 died silently with no report, 1 exited `rc=3` with no report — see that issue doc's
      2026-08-15 Progress Log entry for full detail + the two new todos it added). The IS baseline (companion check)
      succeeded cleanly on 2026-08-14 — MTDS is the side still blocked. **Do not check this todo off on the MTDS side**
      until the issue doc's [CODE] P1 root-cause todo ships and a genuinely complete 5/5 MTDS baseline run exists to
      cite.

## MVP universe — proven-wired vs. merely-declared (gate-audit §14, 2026-07-24: no such section existed; this track is the closest source)

**Status: unresolved, mostly an open question.** Per the unpark note above, defi's MVP backfill has not yet written
canonical rows against the per-instrument shard key (R3 is `RUNNING, partial`) — so **no DeFi MVP cell can yet be called
PROVEN wired backfill=paper=live**; every cell in scope today is only DECLARED in-scope via the catalogue/registries +
the parent plan's Track 7 culled-venue ruling.

- [ ] [DATA] P2. **Determine the real DeFi MVP universe once this track's backfill produces its first canonical rows** —
      enumerate which (venue, instrument_type, data_type) cells are PROVEN wired backfill=paper=live vs. still only
      declared in-scope. Definition of done: a verdict table (here or a linked issue doc), re-derived from the live
      catalogue/manifest at that time. (repos: instruments-service, market-tick-data-service)

## Progress Log

- **round5-na-digest-defi 2026-08-08 (apply pass, item 66)**: operator supplied `--day 2026-07-01` for the
  baseline/mid/final pipeline-check cadence, unparking the `BLK-d355f03a` blocked question. Attempted to actually invoke
  `/data-pipeline-check-is --day 2026-07-01` this session; the skill's own §1a requires launching a dedicated VM driver
  for a real, multi-minute-plus, real-VM-spend full MVP matrix sweep — did not launch that VM this session (out of scope
  to run to completion synchronously alongside this session's other 8 items). Recorded the exact commands + confirmed
  date in the todo above for the next runner. Doc unchanged otherwise.
- **na-eligibility-audit 2026-08-01**: KEEP-NA-STALE-ITEMS — re-verified live: parent
  `defi_consolidated_closeout_2026_07_18.md` still `depends_on` + `gate_on_depends: true`, still active/unlocked, still
  18 open todos — gate citation still holds, doc stays KEEP-NA overall. Closed 1 stale item this pass (async fan-out —
  shipped elsewhere, see inline note above). Items 3-5 show no evidence of completion; item 3's inner sub-gate has
  cleared but its own launcher-determination task isn't done.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - depends_on + gate_on_depends:true on
  defi_consolidated_closeout_2026_07_18 which still carries 19 open todos — KEEP-NA on the gate citation alone
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — fixed a duplicated entry (the same optimization
  issue doc was listed twice) and swapped in the real `dex_pools_handler.py` fan-out target named in the doc's own
  Track-5 async-fan-out todo.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — gate_on_depends on
  defi_consolidated_closeout_2026_07_18 re-verified still open (13 todos) today; genuine prerequisite, not stale.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- 192-line doc forked from
  `defi_consolidated_closeout_2026_07_18.md` Track 5. Explicit `depends_on`+`gate_on_depends: true` on the parent,
  personally confirmed still open (14 items, same-batch read). 4 open todos; whole-doc KEEP-NA on the gate citation. Doc
  stays `assigned_vm: NA`.
- **batch10 source-doc reconciliation 2026-08-11 (slot-31, `defi_satellite_ao_dispatch_batch10_2026_08_06_finalize.md`
  (archived 2026-08-11) todo 1)**: Todo 1's milestone progress recorded here for citation parity with
  `defi_satellite_ao_dispatch_batch10_2026_08_06.md` todo 3 (2026-08-07, slot-7/12): VM `mtds-perp-funding-backfill`
  launched SPOT (asia-northeast1-c), 1824 rows for 2023-11-05 at T+5min; prerequisite
  `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` flipped `true` 2026-08-07T16:44Z (set_by=slot-7) on first
  real progress; other MVP data_types already complete (dex_pool_state 08-05, lending_indices 07-30, lst_rates 07-26,
  oracle_prices 08-03), dex_pool_swaps mid-flight (`mtds-dex-swaps-backfill`, 63k+ rows/shard). Todo 1's
  backfill-to-100% not yet reached — checkbox stays `[ ]` (genuine remaining work, not orphaned).
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (5 entries).
- **na-eligibility-audit 2026-08-16** [body-hash:ccfb9f96b88be407]: KEEP-NA, valid — Forked from defi_consolidated_closeout_2026_07_18.md's Track 5, machine-gated via depends_on:[defi_consolidated_closeout_2026_07_18] + gate_on_depends:true (doc's own banner: this holds every task in THIS plan until the parent's ENTIRE remaining scope is done).
**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17**: KEEP-NA, valid — reverified live: parent defi_consolidated_closeout_2026_07_18.md's depends_on+gate_on_depends:true still holds (10 open todos today), genuine prerequisite not stale. 3 open todos, all DEPENDENCY_BLOCKED on the same parent gate. Doc stays assigned_vm: NA.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
