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
    /plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    /plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md,
    /plans/active/defi_onchain_derivable_values_and_date_drift_2026_06_20.md,
    /plans/active/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md,
    /plans/active/candle_canonical_path_migration_execution_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
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
- [ ] [BACKEND] P2. **Async fan-out + executor-offload for the MTDS DeFi collectors** (recovered from the pre-2026-07-24
      historical Progress Log's deferred-work table — genuinely correctness-sensitive, deliberately not squeezed into a
      sub-agent turn). The sequential loops needing fan-out are `solana_defi_handler.py::_run_solana_protocol_loop` +
      `dex_pools_handler.py::_run_process`, with the actual blocking `_upload_parquet`/`storage.upload_bytes` calls two
      files deeper in `_dex_pools_subgraph.py::_collect_protocol_chain`/`::_collect_solana_dex`. Design sketch: fan out
      fetch+upload via UTL `ParallelPerSymbolRunner` with `manifest_writer=None`, then apply
      `record_captured`/`record_zero_rows`/`record_failed` + the heartbeat SEQUENTIALLY over the gathered results in
      original iteration order (preserves today's manifest-write/heartbeat semantics exactly while parallelizing the
      slow I/O). ~~The 3 `service_config.py` knobs are a trivial, un-risky first step~~ — **CORRECTED 2026-07-24
      (sub-agent investigation): WRONG per this item's own cited source** —
      `plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md:617` states the knobs (none of the 3 exist
      yet — confirmed via grep) are "inert alone — 0% gain, 3 unread fields — ship knobs+fanout+executors as ONE commit
      or not at all." `plans/active/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md` (open, locked_by:
      live-defi-rollout) already carries the correctly-bundled todo; nothing shipped standalone. **Separately**: the
      2-VM TheGraph canary is operator-owned ("ship code + I run the canary") — do not launch VMs for it. (repo:
      market-tick-data-service)
- [ ] [DATA] P1. **Confirm the launcher + parallelization plan for the DeFi-MVP full-history MDPS candle backfill**
      (gate-audit §6, 2026-07-24 — gated on `candle_canonical_path_migration_execution_2026_07_24.md` reaching P8).
      Determine which launcher runs it (single-VM vs. cross-VM sharded) and whether `max_workers` lets concurrent writes
      overlap GCS (~8x ETA impact suspected, unconfirmed). Definition of done: name the launcher + cite a measured
      write-concurrency figure. (repos: market-data-processing-service, deployment-service)
- [ ] [DATA] P1. **Run `/data-pipeline-check-is` and `/data-pipeline-check-mtds` 3x each across the defi backfill**
      (gate-audit §11: pre-backfill baseline, mid-backfill spot-check, post-backfill final gate per skill — 0 dated runs
      of either on record for defi today). Cite each run's report path + date. (repos: instruments-service,
      market-tick-data-service)

## MVP universe — proven-wired vs. merely-declared (gate-audit §14, 2026-07-24: no such section existed; this track is the closest source)

**Status: unresolved, mostly an open question.** Per the unpark note above, defi's MVP backfill has not yet written
canonical rows against the per-instrument shard key (R3 is `RUNNING, partial`) — so **no DeFi MVP cell can yet be called
PROVEN wired backfill=paper=live**; every cell in scope today is only DECLARED in-scope via the catalogue/registries +
the parent plan's Track 7 culled-venue ruling.

- [ ] [DATA] P2. **Determine the real DeFi MVP universe once this track's backfill produces its first canonical rows** —
      enumerate which (venue, instrument_type, data_type) cells are PROVEN wired backfill=paper=live vs. still only
      declared in-scope. Definition of done: a verdict table (here or a linked issue doc), re-derived from the live
      catalogue/manifest at that time. (repos: instruments-service, market-tick-data-service)
