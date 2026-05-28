---
name: mdps_filter_pushdown_memory_audit_and_fix
title: "MDPS filter-pushdown + memory pathology — audit, fix, verify (2026-05-28)"
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
status: active
priority: P1
created: 2026-05-28
author: harsh (claude opus 4.7)
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
related:
  - features_calc_efficiency_and_correctness_2026_05_27.md   # the 4h/24h unblock waiting on MDPS sample data
  - features_service_e2e_pipeline_test_2026_05_26.md          # the original 4h/24h non-landing trail
---

# MDPS filter-pushdown + memory pathology — audit, fix, verify

## Goal

Diagnose + fix the MDPS memory-pathology that makes narrow-scope backfills consume 70 GB+ of RAM
regardless of the `--instrument-ids` / `--venues` / `--data-types` filters. Land the smallest
viable fix so a small-sample CeFi 1h-candle backfill (16 days × 2 venues × ~4 instruments,
trades-only) runs on a modest VM in under an hour.

## Provenance (what happened — DO NOT RECREATE)

This plan exists because **two MDPS runs blew up on memory in the same day** (2026-05-28):

1. **VM `mdps-backfill-cefi-20260528-112956`** (`e2-standard-8`, 32 GB, `MDPS_MAX_WORKERS=4` default).
   Full-scope CeFi backfill for 2026-04-15 → 04-30. Hung after processing **only 2 instruments**
   in 40 minutes (per-VM shard had 2 entries; run.log frozen). SSH unreachable. VM auto-deleted
   by operator after diagnosis.

2. **Local laptop smoke** (`mdps@cef7263`, `MDPS_MAX_WORKERS=2`, narrow scope: 4 instruments ×
   1 data_type × 1 day). `MDPS_DATA_TYPES=trades MDPS_VENUES="BINANCE-FUTURES BYBIT"
   MDPS_INSTRUMENT_IDS="BINANCE-FUTURES:PERPETUAL:BTCUSDT BINANCE-FUTURES:PERPETUAL:ETHUSDT
   BYBIT:PERPETUAL:BTCUSDT BYBIT:PERPETUAL:ETHUSDT"`. **Successfully aggregated all 7 timeframes
   for the first instrument in ~43 seconds**, then memory grew to **75.2 % of 93 GB ≈ 70 GB**
   in the next ~2 minutes, with the MDPS log saying `BatchOrchestrationMixin: memory backpressure
   engaged at 75.2 % — gating new submissions`. Operator killed before the OOM-killer fired.

**Pre-existing workspace signal we missed**:
`deployment-service/scripts/vm/launch-mdps-sharded-backfill.sh` already contains:
> "TradFi gets e2-highmem-8 (64 GB) + max-workers=2 (halves concurrent peak footprint vs default 4)
> until the MDPS [memory issue is fixed]."
> "single python process hit 79 GB RSS (basedpyright/pytest)" — incident log 2026-05-15.

The memory pathology is **already documented** workspace-wide as an unfixed MDPS issue; this plan
is the focused fix.

### Smoke log fingerprint (so the next agent recognises the symptom WITHOUT recreating)

```text
ManifestWriter: per-VM shard updated (1 total entries, 1 new)    ← first TF lands
POLARS AGGREGATED: 1440 1m candles
ManifestWriter: per-VM shard updated (2 total entries, 1 new)    ← second TF
…
POLARS AGGREGATED: 1 24h candles                                  ← all 7 TFs done for 1 instrument
BatchOrchestrationMixin: memory backpressure engaged at 75.2 %    ← memory bloat starts HERE
   …                                                              ← no further progress before kill
```

If you see the backpressure line, **stop the process** — do not let it climb. The memory grows
between instruments, not during aggregation.

## Hypothesis (most likely root cause — needs Phase 1 to confirm)

`--instrument-ids` / `--venues` / `--data-types` filters apply at **write-time**, not **read-time**.
MDPS loads the entire `raw_tick_data/by_date/day=…/asset_group=…/venue=…/instrument_type=…/data_type=…/*.parquet`
corpus for the date into memory, then filters at the per-instrument-write step. Narrow scope
shrinks GCS writes (the visible "4 instruments × 7 TFs" output), not RAM reads.

**Evidence supporting this**:
- 4-instrument scope hit 70 GB — way more than 4 instruments of trades data should occupy.
- First instrument's outputs all wrote successfully (read + aggregate + write works); memory bloat
  appeared **between** instruments (and the launcher VM hung at exactly the same boundary, after
  2 instruments).
- The workspace's own mitigation pattern (`e2-highmem-8 + max-workers=2`) treats the symptom by
  capping concurrent in-memory blocks, not by narrowing reads — consistent with reads being
  unfiltered.

## Phase 1 — AUDIT (read-only; no execution risk)

Goal: confirm filter-pushdown is the root cause and pinpoint the exact line(s) where the filter
should attach to the read path. Deliverable: short audit doc at
`plans/active/issues/mdps_filter_pushdown_audit_2026_05_28.md` (frontmatter:
`title` / `created: 2026-05-28` / `author: <slot>` / `source: [mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md]` /
`locked_by: live-defi-rollout`). No code edits in this phase.

- [x] [AUDIT][P1] **1.1 Trace the read path.** ✅ Done. See audit doc § 1 — full CLI→worker call-stack with file:line at each hop. Memory-backpressure log line confirmed at `batch_workers.py:236` inside `BatchOrchestrationMixin._on_memory_warning()`.
- [x] [AUDIT][P1] **1.2 Map where the filter args land.** ✅ Done. See audit doc § 2 — 12-row table classifying every `instrument_ids` / `venues` / `data_types` callsite.
- [x] [AUDIT][P1] **1.3 Identify the bloat owner.** ✅ Done. See audit doc § 3 — bloat is **not** per-instrument DataFrame retention. The scanner returns the wrong file list (`instrument_ids` silently dropped on venue-prefix match at `orchestration_scanner.py:441-449`); workers faithfully download whatever the scanner queued. Memory grows linearly with the over-queued blob count.
- [~] [AUDIT][P1] **1.4 Sanity-check on a contained, instrumented canary.** SKIPPED — static-trace evidence in § 3 is unambiguous. A canary would burn ~1h to confirm `len(files_to_process)` is much larger than the operator-requested scope; the code already shows it. Audit § 6 recommends going straight to Phase 2 + Phase 3.1 (which IS the canary, but against the fix instead of against the bug).
- [x] [AUDIT][P1] **1.5 Update the hypothesis + name the fix.** ✅ Done. See audit doc § 4 (verdict: CONFIRMED with refinement — plumbing exists, gating logic short-circuits) and § 5 (3-line fix in `_collect_matching_parquet_blobs` + parallel fallback). Sibling-correct shape exists at `orchestration_scheduling.py:243` as proof of intent.

> **Phase 1 deliverable:** [`plans/active/issues/mdps_filter_pushdown_audit_2026_05_28.md`](issues/mdps_filter_pushdown_audit_2026_05_28.md). Audit recommends skipping Phase 2.2 (`del` between iterations) and Phase 2.3 (streaming orchestrator) — both target a non-existent leak. The scanner fix alone should resolve the pathology; if Phase 3.1 fails the RSS cap, revisit.

## Phase 2 — FIX (only after Phase 1 names the cause)

Principle: **minimum-viable change**. Don't refactor more than needed. If the audit confirms
filter-pushdown:

- [ ] [P1] **2.1 Push the 3 filters down to the read layer.** Before issuing the `raw_tick_data/`
  list/read, filter the candidate set by `instrument_ids` / `venues` / `data_types`. Result: a
  narrow scope reads only what it will write. Keep the write-time filter as defence-in-depth, but
  it should now match zero rows because the read was already filtered.
- [ ] [P1] **2.2 Free per-instrument memory between iterations.** After writing all 7 TFs for one
  instrument, `del raw_df` (or polars equivalent) + clear any orchestrator-level caches keyed by
  the just-processed instrument. **Do NOT add `gc.collect()` in a hot loop unprovoked** — measure
  first; only add it if 2.1 alone doesn't return RSS to baseline between instruments.
- [ ] [P2] **2.3 Optional: streaming-per-instrument orchestrator mode.** If the orchestrator
  currently fans out reads for all instruments upfront and only the writes are serial, restructure
  to streaming: for each instrument → load → aggregate (all 7 TFs) → write → release → next. This
  is the architectural fix, larger scope — only do it if 2.1 + 2.2 don't get RSS under 4 GB on the
  canary VM. (Performance principle: streaming may run slightly slower per-instrument than the
  fan-out, but it's the right shape for a 4128-instrument corpus on a 32-GB box.)

If Phase 1 names a different cause: apply that fix with the same minimum-viable principle and
keep this plan's other phases.

## Phase 3 — VERIFY (no re-OOMing the dev machine)

Critical: verification runs on a VM, never locally. The fix must be confirmed on **a deliberately
modest VM** so the bug returns audibly if the fix is incomplete — not silently absorbed by capacity.

- [ ] [VERIFY][P1] **3.1 Canary run on `e2-standard-4` (16 GB)** — single day, the exact narrow
  scope used in the 2026-05-28 smoke (4 instruments × trades × all 7 TFs). Monitor RSS every 5 s.
  **Pass criterion: RSS stays under 2 GB for the full run; all 7 TFs land in `processed_candles/`
  for all 4 instruments; VM auto-shuts down on completion.** If RSS climbs past 4 GB, the fix is
  incomplete — return to Phase 2.
- [ ] [VERIFY][P1] **3.2 7-day scope** — same instruments + venues + data_type, 2026-04-15 → 04-21.
  Still on `e2-standard-4`. Pass criterion: same memory cap; 7 days × 4 instruments × 7 TFs land;
  wall-clock recorded.
- [ ] [VERIFY][P1] **3.3 The actual unblock — 16-day narrow scope** 2026-04-15 → 04-30 (the gap
  filling 04-14 + 04-15..04-30 + 05-01..05-04 into 21 contiguous days for features-service 4h/24h).
  Same 4 instruments + 2 venues + trades. Still `e2-standard-4`. Pass criterion: memory cap holds;
  features-service re-runs delta_one all-TFs for 2026-05-03 and **4h + 24h finally land in `-test`**
  — that's the feature-side proof.

## Phase 4 — Codex SSOT updates (HARD RULE)

- [ ] [P2] **4.1 Update `codex/04-architecture/` or `codex/06-coding-standards/` with the read-time
  filter discipline** — every batch service whose pipeline matches MDPS's shape (list raw → filter
  → load → process → write) MUST apply scope filters at the LIST stage, not the WRITE stage.
  Reference this plan + the 2026-05-28 incident. (If no codex doc fits, write a stub.)
- [ ] [P2] **4.2 Remove the now-stale workspace mitigations** in the sharded launcher
  (`e2-highmem-8` + `max-workers=2` for TradFi) — once the fix lands, `e2-standard-8` +
  `max-workers=4` should be back on the table. Land that revert in `launch-mdps-sharded-backfill.sh`
  with a comment pointing at this plan as the fix-source.

## DO NOT (anti-patterns the next agent should avoid)

- **Do not run MDPS locally on the dev machine.** It's not configured for MDPS's memory profile;
  the 2026-05-28 incident proved this. Even "narrow scope" hits 70 GB before the fix.
- **Do not "make the VM bigger" as the fix.** `e2-highmem-16` (128 GB) would mask the bug, not
  solve it. The pathology scales with corpus size; today's 4128 instruments is tomorrow's 8000.
- **Do not set `MDPS_MAX_WORKERS > 2` until Phase 3 passes.** Even if the fix lands, validating
  with workers=1 first isolates whether the bloat is per-worker or shared.
- **Do not skip the canary VM** in Phase 3.1. Going straight to 16 days hides whether the fix
  actually drops RSS or just spreads the bloat over more time.
- **Do not add `gc.collect()` blindly** to "fix memory". Measure first; collect targets specific
  refs the audit identified. Unprovoked `gc.collect()` in a hot loop just wastes CPU.

## Performance / time balance (operator-stated principle)

- VM has good capacity → use it sensibly. **Don't pessimize to e2-micro to "save resources"** —
  that wastes dev-cycle time.
- But **don't oversize** either. e2-standard-4 (16 GB) for the canary is the right starting point;
  scale up only if Phase 3.3 needs it for the 16-day window and the fix is sound.
- Time budget: **1.6 calibrated AI-days** (infra class, 0.8× of 2-day baseline). If Phase 1 audit
  takes > half a day, ping operator with the partial findings rather than going dark.
- The unblock is the goal — not making MDPS perfect. Phase 4 cleanup is P2 specifically so the 4h/24h
  features-side work isn't gated on it.

## Success criterion

- 4h + 24h delta_one features land for CeFi 2026-05-03 in `features-delta-one-cefi-test-...`.
- MDPS runs the 16-day narrow-scope CeFi backfill on `e2-standard-4` (16 GB) without backpressure
  warnings; RSS stays < 4 GB throughout.
- Workspace mitigation comments in the sharded launcher updated.
