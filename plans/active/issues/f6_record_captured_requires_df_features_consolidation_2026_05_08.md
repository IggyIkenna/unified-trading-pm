---
title: "F6 migration blocker — record_captured() requires DataFrame, but writer.add() callsites don't have it in scope"
created: 2026-05-08
author: tab-c-f6-migration-agent
source:
  - unified-trading-pm/plans/active/features_repo_consolidation_2026_05_08.md (F6, lines 876-886)
  - features-service/features_service/sports/cli/handlers/batch_handler.py:797,805
  - features-service/features_service/calendar/engine/calendar_orchestrator.py:373
  - features-service/features_service/onchain/engine/orchestrator.py:182
  - features-service/features_service/volatility/engine/orchestrator.py:192,198,262,268,635,641
  - features-service/features_service/commodity/cli/handlers/batch_handler.py:269
  - features-service/features_service/delta_one/engine/orchestrator.py:316,322
  - features-service/features_service/cross_instrument/cli/handlers/batch_handler.py:472,479
  - features-service/features_service/multi_timeframe/engine/orchestrator.py:254,261
  - unified-trading-library/unified_trading_library/manifest_writer.py:1916 (record_captured signature)
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# F6 migration blocker — `record_captured()` requires DataFrame; legacy `add()` callsites don't have one

> **Severity**: P0 — F6 cannot ship as a mechanical migration; the work shape is materially different from what
> the plan body assumes.
> **Blast radius**: features-service repo (8 families, 18 callsites) + the F6 audit row of
> `features_repo_consolidation_2026_05_08.md`.
> **Suggested owner**: features-consolidation Tab 2 (Phase 4 sub-todo) — operator triage on path-forward shape.

## What I found

F6's plan-body action item (line 884-886 of `features_repo_consolidation_2026_05_08.md`) says:

> Phase 4 MUST migrate features-\* call sites from `writer.add(...)` to `writer.record_captured(...)` with
> `feature_family` passed.

But `record_captured()`'s contract is **not a drop-in replacement** for `add()`:

```python
def record_captured(
    self,
    *,
    row_key: Mapping[str, object],
    df: pd.DataFrame,                # MANDATORY — used for schema validation + assert_available_at_present
    category: str,                   # MANDATORY — contract registry key
    instrument_type: str,            # MANDATORY — contract registry key
    data_type: str,                  # MANDATORY — contract registry key
    venue: str | None = None,
    row_count: int | None = None,
    ...
```

The function:

1. Calls `assert_available_at_present(df)` (line 2101 of `manifest_writer.py`) — raises `LookaheadBiasError` if
   the df has no `available_at` column. **Mandatory; not opt-out-able.**
2. Calls `self._maybe_validate(df, category=..., instrument_type=..., data_type=..., venue=..., ...)` — schema
   validation against UAC contract registry.
3. Computes `effective_count = int(row_count) if row_count is not None else int(len(df))` — `df` is the SoT for
   row count too.

**Every one of the 18 features-service `writer.add(...)` callsites has the same shape**: the manifest write
happens AFTER the actual parquet write to GCS via a helper like `write_sports_table` / `_write_per_league` /
`save_features_to_gcs` — at manifest-flush time the DataFrame has been consumed by the GCS writer and is no longer
in scope. The callsite only has `row_count`, `feature_group`, optionally `timeframe` / `league_id`. Concretely:

```python
# features_service/sports/cli/handlers/batch_handler.py:797 (representative)
for tbl_name, row_count in table_row_counts.items():
    if "::" in tbl_name:
        base_table, manifest_league = tbl_name.split("::", 1)
        manifest.add(                       # ← only row_count, no df
            processing_date=target_date,
            row_count=row_count,
            feature_group=base_table,
            data_type=_manifest_data_type(base_table),
            league_id=manifest_league,
        )
    else:
        manifest.add(...)
```

Plumbing the df up through `_write_per_league` / `write_sports_table` and the analogous helpers in the other 7
families means refactoring `table_row_counts: dict[str, int]` into `table_dfs: dict[str, pd.DataFrame]` (or
parallel-dicts), which crosses MULTIPLE upstream functions per family. That's an 8-family upstream refactor, not
a per-callsite mechanical sed.

## Why it matters

- **F6 cannot ship as written.** The plan-body migration described as "Phase 4 MUST migrate features-\* call
  sites from `writer.add(...)` to `writer.record_captured(...)`" is not a 1-day mechanical Tab C scope. It's a
  multi-day cross-family refactor of the upstream df-flow.
- **Production-safety is preserved** as Phase 1B already verified — `add()` works today, just writes
  `feature_family=""` for features rows. The deployment-UI Phase 8B drilldown column rendering empty is the
  cosmetic consequence of NOT migrating; nothing breaks.
- **The plan's "Phase 1B production-safety verified" note (line 203-204) anticipated this**: "the 8 features-\*
  services use `writer.add(...)` not `record_captured(...)` — the new gate fires on the four record_\* methods
  only. `add()` unchanged. **No in-flight VMs break.**" But it didn't anticipate that the F6 migration to
  `record_captured()` would itself be non-trivial.

## Recommended decision

Three viable paths; operator triage to pick:

### Option A (minimum-viable, ~1 day Tab C) — extend `add()` to accept `feature_family` kwarg

Add `feature_family: str = ""` kwarg to `ManifestWriter.add()` in UTL. Stamp it on the
`AvailabilityRecord(feature_family=feature_family)`. Migrate all 18 callsites to pass `feature_family=` (lookup
from the family name OR from the existing `FEATURE_GROUP_TO_FAMILY` map already in UAC `features` per Phase 1A).
**Satisfies F6's ACCEPTANCE CRITERION** (deployment-UI Phase 8B drilldown column populated) without the deeper
contract migration. Leaves `record_captured()` migration for a future plan when the df-flow refactor is funded.

**Pros**: ships F6's user-visible benefit today; production-safe (`add()` semantics preserved); 18 callsites is
mechanical sed once UTL accepts the kwarg.

**Cons**: leaves the `add()` legacy method alive (workspace "no double SSOT" tension), but `add()` is already
preserved by design per Phase 1B. The double-SSOT here is acceptable until the df-plumbing refactor lands.

**Required UTL change**: `manifest_writer.py:add()` accepts `feature_family: str = ""`, stamps onto record.
Pre-launch guard already runs; no other behavior change. `feature_group ⇒ feature_family` sibling-presence gate
applies (raises `MissingFeatureFamilyError` if `feature_group` set without `feature_family`) — same shape as
`record_captured()` Phase 1B.

### Option B (correct-shape, ~3-5 days) — refactor df-flow + migrate to `record_captured()`

For each of the 8 families, refactor the `_write_per_league` / `write_sports_table` / equivalent helpers to
return the df (or accept a captured-df-collector dict). Then at manifest-flush time, pass the df to
`record_captured()`. Plumb `available_at` stamping verification, contract registry keys (`category` /
`instrument_type` / `data_type`), the `feature_family`, and the existing `feature_group`.

**Pros**: the architectural target. `record_captured()` is the "valid path" per CLAUDE.md "no double SSOT"; full
schema validation + `available_at` presence assertion at every features manifest write.

**Cons**: 3-5 day refactor across 8 families' upstream df-flow; each family has its own write-helper shape, no
universal pattern. Changes the failure mode (any feature with missing `available_at` column raises
`LookaheadBiasError` at manifest write — catches a real bug class but may surface latent gaps in features that
don't currently stamp `available_at`).

### Option C (hybrid) — Option A now (unblocks F6 closeout), Option B as a Phase 5 follow-up

Ship Option A in the next ~1 day to close F6 (drilldown column populated), AND queue Option B as a new sub-todo
in `features_repo_consolidation_2026_05_08.md` Phase 5 (or a new sub-plan) for the df-flow refactor. This treats
F6 as "make the deployment-UI happy now; the legitimacy-of-write contract can land at full strength after
Phase 6 parity test confirms feature outputs are identical pre- vs post-consolidation".

**Pros**: unblocks Tab C this cycle without scope creep; preserves the plan's intent (F6's user-visible benefit
ships); makes the df-flow refactor an explicit follow-up rather than silently deferred.

**Cons**: leaves a workspace "no double SSOT" tension open longer (`add()` continues to exist). Mitigation:
the Phase 5 follow-up is named in the plan, so it's not silent deferral.

## What I did NOT do

I did **not** ship any of the 18 callsite migrations because the trivial substitution
(`writer.add(...)` → `writer.record_captured(...)`) would break at runtime on every call (LookaheadBiasError
from `assert_available_at_present(df)` with no df, or TypeError on missing required `df` kwarg). Per CLAUDE.md
"Findings Triage Discipline" Case 5 (BIG — touches 2+ repos, contradicts plan assumption, ≥1 day work-shift),
I'm surfacing this to the operator before doing a destructive migration that cannot land cleanly.

## Suggested next move

Operator picks A / B / C. If **A** or **C**, Tab C re-spawns with the explicit Option-A scope (add UTL kwarg,
sed-migrate 18 callsites, ship per family). If **B**, the work transfers to a new Tab spec'd for the multi-day
df-flow refactor. Until the operator picks, no migrations land.

Plan annotation captured in `features_repo_consolidation_2026_05_08.md` § F6 audit row (next commit after this
issue doc).
