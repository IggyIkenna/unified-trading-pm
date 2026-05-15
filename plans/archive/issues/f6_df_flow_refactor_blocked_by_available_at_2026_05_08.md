---
title: "F6 deeper df-flow refactor BLOCKED — 7 of 8 features families don't stamp available_at"
created: 2026-05-08
resolved: 2026-05-10
author: wave8-f6-df-flow-agent
source:
  - unified-trading-pm/plans/active/issues/f6_record_captured_requires_df_features_consolidation_2026_05_08.md
  - unified-trading-pm/plans/active/features_repo_consolidation_2026_05_08.md (F6 deferred-work row)
  - features-service/features_service/{calendar,onchain,volatility,commodity,delta_one,cross_instrument,multi_timeframe}/
    (no `available_at` references)
  - unified-trading-library/unified_trading_library/manifest_writer.py:2153 (`assert_available_at_present(df)` mandatory
    — df-shape path only)
  - unified-trading-library/unified_trading_library/manifest_writer.py:2222 (record_captured_from_counts NEW shipped at
    UTL@ef47c81b)
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

> ## RESOLVED 2026-05-10 by record_captured_from_counts (UTL@ef47c81b)
>
> **Status**: ✅ RESOLVED. The "available_at prerequisite missing in 7 of 8 features families" blocker is closed by
> `ManifestWriter.record_captured_from_counts(...)` shipped at UTL@`ef47c81b` — the streaming-writer companion that
> accepts a single envelope timestamp instead of requiring per-row `available_at` stamping on the input DataFrame.
>
> **Why this resolves the blocker:**
>
> The original blocker analysis correctly identified that `record_captured(df, ...)` calls
> `assert_available_at_present(df)` at `manifest_writer.py:2153` unconditionally — and 7 of 8 features families
> (calendar / onchain / volatility / commodity / delta_one / cross_instrument / multi_timeframe) don't stamp
> `available_at` on their output dfs today. Migrating those families to `record_captured(df, ...)` would have raised
> `LookaheadBiasError` on every production write.
>
> The shipped helper sidesteps this by **moving the `available_at` presence assertion from per-row (df) to per-shard
> (envelope)**:
>
> | Aspect                           | `record_captured(df, ...)` (df-shape)         | `record_captured_from_counts(...)` (envelope-shape)              |
> | -------------------------------- | --------------------------------------------- | ---------------------------------------------------------------- |
> | `available_at` presence gate     | per-row via `assert_available_at_present(df)` | per-shard via `available_at_envelope` kwarg + tz-aware UTC check |
> | Source of validation             | DataFrame column                              | Caller-computed envelope timestamp                               |
> | Where it fires                   | Manifest finalize time (after parquet write)  | Manifest finalize time (same boundary)                           |
> | What raises `LookaheadBiasError` | Missing/null per-row `available_at`           | None/NaT envelope timestamp                                      |
> | Schema validation                | Per-row at manifest finalize                  | Per-chunk by streaming writer (already in place)                 |
> | Cluster coverage                 | Per-cluster from df groupby                   | Per-cluster from caller-supplied `observed_clusters` dict        |
>
> **The 7 features families compute `available_at_envelope` at finalize time** as
> `max(per-row available_at across all clusters) + UAC EMISSION_LATENCY_MS_BY_SOURCE for the primary source` — a single
> timestamp per shard, not per-row stamping. This collapses the multi-day per-family stamping refactor into a 3-line
> callsite migration.
>
> **What the predecessor analysis got right (still valid):**
>
> - The 3 other pillars (NaN ratio / schema / cluster coverage) for features rows still need independent UTL/UAC work —
>   those gaps are unrelated to F6 + remain tracked at:
>   - **Pillar 2 (NaN ratio)** — writegate Plan B Q#4 (lift inline gate to UTL helper).
>   - **Pillar 3 (schema)** — UAC contract registry needs entries for the 8 features data_types (`options_volatility`,
>     `fixture_features`, `time_features`, `carry_staked_basis`, `cross_pair_corr`, etc.).
>   - **Pillar 4 (cluster coverage)** — features data_types are not in
>     `unified_api_contracts.canonical.crosscutting.honest_coverage.BUNDLED_DATA_TYPES`; the per-cluster gate is a no-op
>     for non-bundled features (which is correct — only bundled shards have cluster semantics).
>
> Recommended Option α (preferred — keep F6 closed; track migration in features_repo_consolidation row) is now
> mechanical instead of multi-day. No need for Option β (new prerequisite plan) or Option γ (banned bypass flag).
>
> **Naming-successor parking note** (per CLAUDE.md "Temporary state must have a named successor plan"):
>
> The named successor for the per-family `record_captured_from_counts` migration is the F6 deferred-work row in
> `features_repo_consolidation_2026_05_08.md` — that row's body annotation now reads "Migrate to
> `record_captured_from_counts` per UTL@`ef47c81b`; mechanical 3-line per-callsite change."
>
> **No further action required on this issue doc.** It may be moved to `plans/archive/issues/` at the next archival
> sweep.

# F6 deeper df-flow refactor BLOCKED — `available_at` prerequisite missing in 7 of 8 features families

> **Severity**: P0 — multi-day blocker; prior issue doc's "Option B = 3-5 days" estimate was understated; the
> prerequisite work (stamping `available_at` across 7 families) is itself the multi-day item. **Blast radius**:
> features-service (8 families × per-family upstream df-pipeline refactor), would change Wave 8 work-split, would block
> Phase 12 batch-vs-live reconciler full-run criterion (depends on `available_at` per row). **Suggested owner**:
> features-service maintainer + Tab 2 LIVE-PIPELINE owner (composes with writegate Phase 2.D / writegate Phase 4 slice
> (b) Phase 5.x).

## What I found

Wave 8 F6-DF-Flow sub-agent was spawned to execute the "deeper df-flow refactor" that the existing F6 issue doc
(`f6_record_captured_requires_df_features_consolidation_2026_05_08.md`) deferred. Plan: take helper signatures from
`(df → parquet write → return row_count)` to `(df → parquet write → record_captured(df, ...) internally)` so the
4-pillar validation gates (row count / NaN ratio / schema / cluster coverage) fire at the writer atomicity boundary per
CLAUDE.md "Validation gates per `record_captured` — 4 pillars".

Pre-flight audit surfaced a hard blocker the F6 issue doc didn't enumerate: **`record_captured()` calls
`assert_available_at_present(df)` at manifest_writer.py:2153 unconditionally** — and 7 of 8 features families do NOT
stamp `available_at` on their output dfs today.

Audit (2026-05-08, Wave 8 sub-agent):

```bash
cd features-service && for fam in calendar onchain volatility commodity delta_one cross_instrument multi_timeframe; do
  echo "=== $fam ==="
  grep -l "available_at" features_service/$fam/ -r --include="*.py" 2>/dev/null | grep -v test_ | head -3
done
```

| Family             | Stamps `available_at`? | Notes                                                                              |
| ------------------ | ---------------------- | ---------------------------------------------------------------------------------- |
| `sports`           | ✅ YES                 | LIFT-3 shipped — `stamp_available_at_explicit/offset/post_match` per-source rules. |
| `calendar`         | ❌ NO                  | `_generate_time_features` returns df with `open/high/low/close` only.              |
| `onchain`          | ❌ NO                  | LST yields / gas fees / vault TVL — no `available_at` in output dfs.               |
| `volatility`       | ❌ NO                  | options_volatility / futures_term_structure — parallel-worker shape, no stamp.     |
| `commodity`        | ❌ NO                  | commodity carry / cross-pair correlation — no stamp.                               |
| `delta_one`        | ❌ NO                  | delta_one carry — no stamp.                                                        |
| `cross_instrument` | ❌ NO                  | cross-pair correlation / dispersion — no stamp.                                    |
| `multi_timeframe`  | ❌ NO                  | multi-tf alignment features — no stamp.                                            |

Migrating any of those 7 families' helpers to call `writer.record_captured(df, ...)` would raise `LookaheadBiasError` on
EVERY production write — taking out the entire features pipeline.

**Why the F6 issue doc didn't catch this**: it called out the `assert_available_at_present(df)` requirement (line 53)
but presumed Option B's "refactor df-flow per family" included stamping `available_at` along the way. In practice the
stamping is itself the multi-day item — sports' LIFT-3 work was a multi-week effort across exporters, derived-features,
fixture-features, and odds-features pipelines. Doing the same across 7 more families is the bulk of the work, not a
side-effect of plumbing the df.

Three pillars beyond `available_at` are also incomplete for features:

- **Schema validation (pillar 3)**: zero of the 8 features data_types are registered in the UAC contract registry today
  (verified:
  `grep -rn "options_volatility\|fixture_features\|time_features\|carry_staked_basis\|cross_pair_corr" unified-api-contracts/unified_api_contracts/registry/`
  returns no matches in the contract registry path). Without UAC contract registration,
  `_maybe_validate(df, category, instrument_type, data_type, venue, ...)` silently warns rather than fails — pillar 3 is
  a no-op for features rows regardless of which method writes them.
- **NaN ratio (pillar 2)**: not yet lifted to UTL — writegate plan B Q#4 still open per CLAUDE.md "No double SSOT".
- **Cluster coverage (pillar 4)**: zero of the 8 features data_types appear in
  `unified_api_contracts.canonical.crosscutting.honest_coverage.BUNDLED_DATA_TYPES` (closed set: `options_chain`,
  `futures_chain`, `prediction_canonical_question_group`, `sports_fixture_bundle`). The pillar-4 guard is a no-op for
  features.

So the meaningful pillar at the moment is just **row count > 0** (pillar 1) — which the existing `add()` path already
captures via the row_count kwarg. Migrating to `record_captured` therefore offers ~zero net validation benefit until the
prerequisite work for pillars 2/3/4 lands, while introducing the immediate breakage risk via pillar 0 (`available_at`
presence assertion).

## Why it matters

- **Code-shipped vs operationally-shipped (CLAUDE.md "Plan Archival HARD RULE")**: The F6 deferred-work row landed on
  the assumption that Option B is a "3-5 day refactor" that we'd schedule when ready. Wave 8's pre-flight shows the
  prerequisite (per-family `available_at` stamping) is itself the bulk of the 3-5 days. Closing F6 deeper-work as "done"
  without that prerequisite would be the kind of code-shipped-but-not-operationally-shipped silent failure that rule
  prohibits.
- **In-flight VM risk**: features-service VMs that pull from `live-defi-rollout` would IMMEDIATELY break on next launch
  if the migration shipped naively (every helper invocation raises `LookaheadBiasError`). Reference: CLAUDE.md
  "Cross-Plan Coordination Banners" — this is exactly why in-flight refactors of writer atomicity boundaries get a
  banner.
- **Composes with writegate Phase 2.D / Phase 4 slice (b) Phase 5.x**: `available_at` cross-family stamping IS a
  writegate-plan concern. The work belongs in writegate's per-family rollout, not in F6 isolation.
- **Sibling-agent collision risk**: 4 parallel sibling agents (ModeHandler-Lift / BaseFC-ValidationFlip /
  WatermarkFanin-LatentExcept / Downstream-Hookup) are touching features-service same cycle per the work-split. A
  multi-file 8-family refactor across writer atomicity boundaries during sibling-agent activity is high collision
  surface (per CLAUDE.md "Two teammates × multiple parallel agents — don't edit unfamiliar files").

## Recommended decision

Operator triage:

### Option α (preferred) — keep F6 closed, retitle the issue doc to make the prerequisite explicit

Per the existing F6 closeout (Option C), `add()` already accepts `feature_family` kwarg + the deployment-UI Phase 8B
drilldown column is populated. F6's user-visible benefit shipped. The "deeper" df-flow refactor is parked behind the
named successor work (per-family `available_at` stamping → migrate to `record_captured(df, ...)` once stamping is
complete).

This issue doc becomes the canonical pointer for the named successor: when writegate Phase 2.D (or a future
`features_available_at_stamping_2026_*.md` plan) ships per-family `available_at` stamping for calendar / onchain /
volatility / commodity / delta_one / cross_instrument / multi_timeframe, the migration to `record_captured` becomes
mechanical and unblocked.

**Pros**: matches Citadel-grade discipline (no double-SSOT, no half-shipped writes that erode workspace trust); avoids
multi-hour blast-radius edits during high sibling-agent activity; preserves the ratchet (4-pillar validation lands fully
when each prerequisite is met, never partially).

**Cons**: leaves `add()` legacy method alive longer; pillars 2/3/4 stay no-ops for features rows — but those are no-ops
regardless of which method writes (pillars 2-4 require independent UTL/UAC work).

### Option β — write the prerequisite plan now, defer this Wave 8 task

Spawn a new active plan `plans/active/features_available_at_stamping_2026_05_08.md` with per-family stamping todos
(calendar / onchain / volatility / commodity / delta_one / cross_instrument / multi_timeframe). Wave 8 transfers to that
plan; the F6 deeper-refactor rolls forward as a 1-day mechanical Wave behind the new prereq plan.

**Pros**: explicit successor work gets a plan-of-record; subsequent agents pick up cleanly; deferred-work registry stays
honest.

**Cons**: 1-day plan-drafting work where the existing issue doc + this issue doc already capture the shape; deferral
overhead.

### Option γ (NOT recommended) — naive migration anyway with `available_at` exemption flag

Add a `skip_available_at_check: bool = False` kwarg to `record_captured()` that bypasses `assert_available_at_present`
for features rows during the rollout window. Migrate the 18 callsites + flip the flag.

**Cons**: violates CLAUDE.md "available_at is per-row, write-time, equal to live-pipeline-arrival (workspace-wide)" —
explicitly forbids opt-out paths. Would create a double-SSOT (records claim available_at-validated when they aren't).
Future agents reading the manifest assume `available_at` is enforced; reading rows that bypassed the check produces
silent lookahead bias in features compute.

## What I did NOT do

I did **not** ship any of the 18 callsite migrations or any helper signature changes. Per the F6 issue doc and CLAUDE.md
"Findings Triage Discipline" Case 5, surfacing this BIG cross-cutting blocker before destructive multi-hour work is
mandatory.

## Suggested next move

Operator picks α / β / γ. Default: α (close-out unchanged; the F6 deferred-work row remains
`status: helper-shipped, deferred-after-features-available-at-stamping`).

If **β**, Wave 8 stays parked + a new active plan gets drafted with per-family stamping todos.

If **γ**, requires explicit operator override of CLAUDE.md "available_at workspace-wide" rule + must be documented as a
temporary state with a named successor plan per CLAUDE.md "Temporary state must have a named successor plan".

## Cross-reference

- Wave 8 work item / sub-agent prompt: `work_split_2026_05_08_ikenna.md` (Tab 2 LIVE-PIPELINE / F6-DF-Flow scope).
- Predecessor issue doc:
  [`f6_record_captured_requires_df_features_consolidation_2026_05_08.md`](f6_record_captured_requires_df_features_consolidation_2026_05_08.md).
- Plan deferred-work row: [`features_repo_consolidation_2026_05_08.md`](../features_repo_consolidation_2026_05_08.md) §
  F6 deferred-work row.
- Composes with: writegate Phase 2.D / Phase 4 slice (b) Phase 5.x available_at cross-family stamping.
