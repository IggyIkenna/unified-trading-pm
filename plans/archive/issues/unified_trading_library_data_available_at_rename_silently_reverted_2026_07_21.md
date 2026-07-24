---
doc_type: issue
title:
  UTL instruments_write_gate.py / point_in_time.py — data_available_at → available_at rename silently reverted,
  no-lookahead scan on sports data is a no-op
summary: >-
  While triaging archived-plan debt for `sports_data_available_at_rename_2026_05_07.md`, found that the Phase-3 4-repo
  atomic rename (`data_available_at` → `available_at`) shipped clean at `unified-trading-library@94e43e8c` (2026-05-22)
  but was silently reverted the next day by `988ab287` ("fix(cloud-agnostic): add noqa gs-uri markers to URI composer
  sites missing them", 2026-05-23) — an unrelated commit whose diff includes a 1-line accidental revert of
  `instruments_write_gate.py`'s `DEFAULT_AS_OF_COLUMNS` tuple back to the legacy name (likely a bad rebase/merge
  carrying stale local state). `unified-trading-library/unified_trading_library/instruments_write_gate.py:58` and
  `point_in_time.py`'s default `timestamp_col` still read `data_available_at` today, live-verified via `git log -p` and
  direct file read. Since sports adapters + every other service write the canonical `available_at` column (per
  `plans/epics/sports_master.md` line 635, "HIGH-2 FULLY SHIPPED 2026-05-24"), the write-gate's default column-name scan
  no longer matches any real column on sports rows — `InstrumentsWriteGate`'s lookahead-bias/timestamp-alignment check
  silently stops firing on sports data, with no error raised anywhere (a column-name mismatch, not an exception).
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-library]
scope: [engineer]
tags:
  [
    lookahead-bias,
    data-available-at,
    available-at,
    instruments-write-gate,
    point-in-time,
    silent-revert,
    data-correctness,
  ]
related:
  [
    plans/archive/sports_data_available_at_rename_2026_05_07.plan.md,
    plans/active/issues/pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md,
  ]
created: "2026-07-21"
parent_epic: sports_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [pm_qg_plan_discipline_and_frontmatter_regression-004]
resolved_by: slot-3, review, 2026-07-21
locked_by:
depends_on: []
---

# What I found

`unified-trading-library@94e43e8c` (2026-05-22, "refactor(sports): rename data_available_at → available_at in UTL (Phase
3 atomic rename)") correctly renamed the column in `DEFAULT_AS_OF_COLUMNS` (`instruments_write_gate.py:58`) and
`point_in_time.py`'s default `timestamp_col`, as part of the coordinated 4-repo rename tracked by
`plans/archive/sports_data_available_at_rename_2026_05_07.plan.md` (all 4 phases shipped and archived complete).

The very next day, `988ab287` (2026-05-23, "fix(cloud-agnostic): add noqa gs-uri markers to URI composer sites missing
them" — a large, mostly-unrelated commit touching workflow files, docs, and ~15 other files) includes this hunk in its
diff:

```diff
--- a/unified_trading_library/instruments_write_gate.py
+++ b/unified_trading_library/instruments_write_gate.py
@@ -60,7 +60,7 @@ logger = logging.getLogger(__name__)
 DEFAULT_AS_OF_COLUMNS: tuple[str, ...] = (
     "as_of_date",
     "valuation_date",
-    "available_at",
+    "data_available_at",
     "kickoff_utc",
     "event_time",
     "computed_at",
```

Nothing in that commit's message or the surrounding diff explains this revert — it reads like stale local state
(possibly an un-rebased branch, or a conflict resolution that picked the wrong side) that happened to land in an
otherwise-unrelated fix commit. Verified live on `unified-trading-library` HEAD today: `instruments_write_gate.py:58`
and `point_in_time.py`'s default `timestamp_col` + docstring still read `data_available_at`.

# Why it matters

`InstrumentsWriteGate` / `validate_pit_safety` scan a configurable list of "as-of" columns to detect timestamp-alignment
violations (batch-date vs row-timestamp mismatches — the lookahead-bias guard). Since sports rows are written with
`available_at`, not `data_available_at`, the default scan silently finds nothing to check on that column for every
sports write — no exception, no log warning, just a column that never matches. Any caller relying on the DEFAULT column
list (not passing an explicit `check_columns=` override) gets a false sense of protection: the gate still runs and still
"passes," but it is not actually inspecting the column that carries the real timestamp. This is exactly the kind of
silent no-op CLAUDE.md's "honest absence vs fake results" principle warns against — a check that looks green but isn't
checking the right thing.

# Recommended decision

Re-apply the `94e43e8c` rename to `instruments_write_gate.py` (`DEFAULT_AS_OF_COLUMNS`) and `point_in_time.py` (default
`timestamp_col` + docstrings), verify no other UTL/consumer files reference the legacy `data_available_at` name in a way
that would break if it's removed (grep first), and add a regression test asserting `DEFAULT_AS_OF_COLUMNS` contains
`available_at`, not `data_available_at`, so a future stale-merge can't silently reintroduce this.

## Todos

- [x] ✅ [CODE] P1. Re-fix `unified_trading_library/instruments_write_gate.py::DEFAULT_AS_OF_COLUMNS` —
      `data_available_at` → `available_at` (re-apply the `94e43e8c` change reverted by `988ab287`). (repo:
      unified-trading-library) — `unified-trading-library@9064dd2a`: `DEFAULT_AS_OF_COLUMNS` renamed back to
      `available_at`; existing tests updated (`test_instruments_write_gate.py`).
- [x] ✅ [CODE] P1. Re-fix `unified_trading_library/point_in_time.py` — default `timestamp_col` + docstrings, same
      rename. (repo: unified-trading-library) — shipped in the SAME commit `unified-trading-library@9064dd2a` (bundled
      with todo 1 above): `validate_pit_safety`'s default `timestamp_col` + both docstring references renamed to
      `available_at`; existing `TestValidatePitSafety` tests updated to construct DataFrames with the new default column
      name. That commit also fixed the QG red this rename surfaces on any commit to this repo (verified pre-existing,
      unrelated to the rename): registered `cicd-events` in `_KNOWN_YAML_ASYMMETRIES`
      (`tests/cloud_interface/unit/test_bucket_naming.py`) for the intentional GCP-only asymmetry from
      `deployment_alerts_ingestion_completeness_2026_07_20.md` todo 5. **Follow-up gap found + closed**: that fix didn't
      cover the THIRD `cloud-providers.yaml` mirror — `unified-trading-pm@a97a2728e`'s sibling,
      `unified-trading-pm/configs/cloud-providers.yaml`, was still missing the `cicd-events` entry, which
      `unified-trading-library`'s `test_sibling_copy_matches_packaged_uac_copy[unified-trading-pm]` regression pin
      catches (reads the PM sibling copy live off disk, not a committed snapshot) — added it here,
      `unified-trading-pm@b3ab78b00` (same entry + comment as the other two copies). `quality-gates.sh` green in
      unified-trading-library (6638 tests) with this PM-repo fix present.
- [x] ✅ [CODE] P2. Add a regression test asserting `DEFAULT_AS_OF_COLUMNS` / the default `timestamp_col` use the
      canonical `available_at` name, not the legacy `data_available_at`, so a future stale-merge/rebase can't silently
      reintroduce this class of bug. (repo: unified-trading-library) — `unified-trading-library@af3dc715`:
      `test_default_timestamp_col_is_canonical_available_at` inspects `validate_pit_safety`'s signature default directly
      (`inspect.signature(...).parameters["timestamp_col"].default == "available_at"`); the existing
      `test_default_columns_match_adapter_families` (test_instruments_write_gate.py) already pins the
      `DEFAULT_AS_OF_COLUMNS` set to include `available_at`, so that half was already covered. Both P2 todos in this
      issue doc are now closed — all 4 todos done.
- [x] ✅ [DIAG] P2. Grep every UTL consumer for an explicit `check_columns=`/`timestamp_col=` override naming
      `data_available_at` — if any exist, they were written to compensate for this exact bug and should be reverted back
      to relying on the (now-fixed) default once the rename lands. (repo: unified-trading-library) — **none found**.
      Workspace-wide `grep -rln "data_available_at"` (all file types, all repos) surfaced zero
      `check_columns=`/`timestamp_col=` call-site overrides anywhere. Every hit is one of: (1) the two
      instruments-service one-off migration scripts whose whole purpose is naming the legacy column
      (`migrate_available_at_column.py`, `migrate_sports_available_at_column.py`); (2) a test asserting the legacy
      column is ABSENT post-migration
      (`instruments-service/tests/unit/triggers/test_sports_fixtures_daily_repoll.py:241`); (3) UTL's own
      `test_custom_available_at_col` (`unified-trading-library/tests/unit/test_point_in_time.py:378-384`), which
      exercises the generic `available_at_col=` pass-through using the legacy name as an arbitrary example value — not a
      compensating override, and not a "consumer" (it's UTL's own test suite); (4) a naming coincidence in an unrelated
      MDPS test function name (`test_sparse_data_available_at_stamped_for_all_rows` — "sparse data" + "available_at
      stamped", no actual column reference); (5) plan/codex prose documenting the historical rename. No code changes
      needed for this todo — nothing to revert.

      **Adjacent finding, fixed in the same commit**: 2 codex docs still documented the STALE (bugged) column list —
                                                                              `/codex/06-coding-standards/validation-and-errors.md`'s `DEFAULT_AS_OF_COLUMNS` example showed both
                                                                              `data_available_at` AND `available_at` together (a state the real tuple never had), and
                                                                              `/codex/02-data/sports-scheduling-and-sharding.md` §5.1 prose still named `data_available_at` instead of the live
                                                                              `available_at`. Both corrected to match the current `unified-trading-library@9064dd2a` tuple
                                                                              (`as_of_date, valuation_date, available_at, kickoff_utc, event_time, computed_at`).

## Codex SSOTs

`/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`, `/codex/02-data/pipeline-mode-partition.md` (for
`available_at` semantics generally).
