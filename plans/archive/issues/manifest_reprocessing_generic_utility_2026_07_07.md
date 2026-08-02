---
doc_type: issue
title:
  "No generic manifest-reprocessing mechanism -- 13 near-identical one-off reclassify scripts written across 3 repos in
  8 weeks (was: 11 -- see 2026-07-12 correction)"
summary:
  "When an adapter/writer bug gets fixed, nothing in the codebase automatically finds and re-attempts the
  attempted_failed or unclassified-empty shards it caused. Every incident, ASTER included, has gotten its own
  hand-written load-manifest-filter-flip-write-back script. Found 13 near-identical such scripts (was: 11 -- see
  2026-07-12 correction) across instruments-service and market-tick-data-service since 2026-05-04. The codebase own
  script-homes.md standard says a recurring need like this should graduate to a permanent tool -- it has not. One
  existing script (retry_transient_cefi_failures_2026_06_28.py) is already ~90% of the generic shape."
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [data, meta]
repos: [instruments-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [reprocessing, reclassify, honest-coverage, hygiene, script-homes, cefi, defi, sports]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    /plans/archive/issues/cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md,
    /codex/06-coding-standards/script-homes.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P2
source:
  "ASTER/CEFI instrument-service data-status audit, 2026-07-07 -- prompted by the question of whether the ASTER 05-14
  base-URL fix needed a follow-up reprocessing run"
assigned_vm: planning
resolved_by:
  "Generic reprocessing utility fully shipped + CLI-wired (unified-trading-library@abeebede/4b6a13cf,
  instruments-service@e9eac282). Retirement of the 13 legacy one-offs closed 2026-07-30: verified all 13 still exist,
  each carries a proper Lifecycle:oneoff + Delete-when: marker (script-homes.md convention), none is imported by other
  code (only docstring cross-references), and per this todo's own stated alternative ('leave as historical record — they
  don't need deletion if inert') no deletion was executed. /codex/06-coding-standards/script-homes.md updated with a
  worked-example note pointing future incidents at the new CLI subcommand instead of a fresh one-off."
locked_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
last_updated: "2026-07-30"
supersedes:
superseded_by:
depends_on:
assigned_role: infra
drift_direction: advance-code
locked_since:
---

## What I found

13 near-identical (was: 11 -- see 2026-07-12 correction below) "load manifest → filter by predicate → flip status/reason
field → snapshot → write back" scripts, independently reinvented across 3 repos and ~2 months:

| Script                                                                   | Repo                     | Date          | Scope                                          |
| ------------------------------------------------------------------------ | ------------------------ | ------------- | ---------------------------------------------- |
| `scripts/reclassify_404_failures_to_empty.py`                            | instruments-service      | 2026-05-04    | 404s → empty (hardcoded Tardis venue prefixes) |
| `scripts/reconcile_expected_absence_reasons.py`                          | instruments-service      | 2026-05-07    | null-reason `empty_confirmed` → typed reason   |
| `scripts/reclassify_defi_orphan_eu_notlisted_2026_06_24.py`              | instruments-service      | 2026-06-24    | DeFi orphan EU rows                            |
| `scripts/reclassify_defi_postdelist_eu_2026_06_24.py`                    | instruments-service      | 2026-06-24    | DeFi post-delist EU rows                       |
| `scripts/reclassify_golden_window_fixtures_no_match_2026_06_24.py`       | instruments-service      | 2026-06-24    | Sports FIXTURES golden-window                  |
| `scripts/reclassify_oos_sports_expected_unattempted_2026_06_24.py`       | instruments-service      | 2026-06-24    | out-of-scope sports sources                    |
| `scripts/reclassify_xg_blank_league_phantoms.py`                         | instruments-service      | 2026-06-23    | XG blank-league rows                           |
| `scripts/reclassify_cefi_manifest_mvp_universe_2026_06_23.py`            | market-tick-data-service | 2026-06-23    | CeFi MVP universe                              |
| `scripts/retry_transient_cefi_failures_2026_06_28.py`                    | instruments-service      | 2026-06-28    | Tardis 500/503/timeout transients              |
| `scripts/reclassify_xg_shots_false_failed_2026_06_29.py`                 | instruments-service      | 2026-06-29    | XG_SHOTS 401-vs-404 misclassification          |
| `scripts/delete_aster_overseeded_capability_rows.py`                     | instruments-service      | 2026-06-29/30 | ASTER over-seeded book/liq rows                |
| `scripts/backfill_cefi_blank_instruments_data_type_2026_07_06.py`        | instruments-service      | 2026-07-06    | CeFi blank `data_type` → `instruments`         |
| `scripts/backfill_defi_tradfi_blank_instruments_data_type_2026_07_06.py` | instruments-service      | 2026-07-06    | DeFi/TradFi blank `data_type` → `instruments`  |

> **(2026-07-12, finding 122, §A2 B-queue ruling)**: count corrected 11 → 13 (was: 11) — this audit's own filing date
> (2026-07-07) postdates two more scripts matching this exact recurring shape, shipped one day earlier at
> `instruments-service@40bdfe1d` and `instruments-service@523d427`
> (`plans/active/issues/is_cefi_manifest_blank_data_type_since_2026_06_29_2026_07_06.md`), which were absent from the
> original enumeration. The "Recommendation" and "Todos" sections below are unaffected — a 13th/14th instance only
> strengthens the case for the generic utility, it doesn't change the proposed shape.

None import a shared "reclassify" or "retry-window" library primitive — grepped `unified-trading-library`,
`unified-api-contracts`, and both service repos for `def.*reclassify`, `def.*replay_failed`, `def.*retry_attempted`,
`ShardReplay`: zero hits outside these one-offs. The closest thing to a generic mechanism is `check_shard_freshness()`
(`unified-trading-library/unified_trading_library/manifest_writer/_queries.py:63`), whose `retry_failed=True` default
means a plain backfill VM re-run over a date range _will_ naturally re-attempt `attempted_failed` shards it touches —
but only by date range, not by error reason, and only if a human remembers to relaunch a backfill covering the right
venue and window. It does nothing on its own when a fix lands.

**Codex already flags this as the recurring-need pattern it's supposed to prevent:**
`/codex/06-coding-standards/script-homes.md:62-66`: _"If the script encodes a recurring need, it has a named successor
(a service CLI subcommand / deployment-service job) and is retired the moment that lands — never left as a parallel
path."_ 11 scripts in 8 weeks is exactly that recurring need, and it hasn't graduated.

**ASTER itself is the proof, not a one-off exception**: per `cefi_hl_aster_batch_data_gaps_2026_06_22.md`, ASTER
accumulated three _more_ distinct attempted*failed-causing bugs after the 2026-05-14 base-URL fix (book_snapshot_5
misclassification, a catalog-reader small-universe cap, NOT_LISTED over-seeding), each needing its own diagnosis and its
own bespoke remediation. That doc's own line 173-176 is a smoking gun: the launcher that \_did* exist for ASTER's re-run
deliberately excludes `liquidations` from its `DATA_TYPES`, so even an existing recovery mechanism silently skipped part
of its own backlog — undetected until someone happened to notice.

## Recommendation

Build one generic utility rather than continuing to write one-off scripts per incident — the risk isn't hypothetical,
it's 11 independently-implemented (and independently-audited) safety gates: per-VM shard isolation, dry-run defaults,
snapshot-before-write, captured-count invariants, each re-solved from scratch.

**Concrete shape:** a function
`select_shards_for_reprocess(df, *, asset_group=None, venue=None, capture_status=ATTEMPTED_FAILED, date_start=None, date_end=None, error_reason_predicate)` +
a generalized flip-and-write helper, living in
`unified-trading-library/unified_trading_library/manifest_writer/_queries.py` (sibling to `check_shard_freshness`, which
already has half the needed logic) or a new `manifest_reprocess.py` module next to `manifest_migrations/`. Best existing
template to generalize from: `instruments-service/scripts/retry_transient_cefi_failures_2026_06_28.py` — its
`_is_transient`, `_identify_transient_rows`, and `_flip_to_expected_unattempted` functions are already ~90% of the
generic shape; they just need the hardcoded pattern list and hardcoded bucket resolver replaced with CLI args.

**Where it should surface:** per `/codex/06-coding-standards/script-homes.md`'s decision rule ("production verb →
service CLI subcommand"), as a permanent instruments-service CLI subcommand — e.g.
`instruments-service --operation reprocess-shards --asset-group cefi --venue ASTER --capture-status attempted_failed --error-reason-contains "404" --date-start 2024-10-01 --date-end 2026-05-14 [--apply]`
— backed by the UTL library function so market-tick-data-service and any future consumer get it for free.

## Todos

- [x] ✅ [DESIGN] P2. Design `select_shards_for_reprocess()` + the flip-and-write helper signature; confirm placement
      (`unified-trading-library/manifest_writer/_queries.py` vs. a new `manifest_reprocess.py`). —
      `unified-trading-library@abeebede`. Placement: new top-level `unified_trading_library/manifest_reprocess.py`
      (sibling to `manifest_completeness.py`/`manifest_consolidator.py`/`manifest_freshness.py` — the established
      convention for a standalone manifest concern, not a fragment of the split monolith), re-exported via the top-level
      package `__init__.py`. Rejected `_queries.py` (read-side-only by its own docstring; the flip-and-write half is a
      real mutation) and `_maintenance.py` (already 891 lines against the 900-line file-size ratchet) and
      `manifest_migrations/` (schema-migration-specific, a different axis). `select_shards_for_reprocess()` is fully
      implemented (pure/stateless filter: capture_status + optional asset_group/venue-or-data_type/date_range/
      error_reason_predicate) with 13 unit tests. `reprocess_shards()`'s signature + the 3-gate safety contract (per-VM
      shard isolation, idx-only mutation, captured-count invariant) are pinned in its docstring; the body is a
      documented `NotImplementedError` stub — implementing it is the separate `[CODE] P2` todo below, unchanged.
- [x] ✅ [CODE] P2. Implement it, generalizing `retry_transient_cefi_failures_2026_06_28.py` as the template; port its
      existing safety gates (dry-run default, snapshot-before-write, captured-count invariant checks). —
      `unified-trading-library@4b6a13cf`.
- [x] ✅ [CODE] P2. Wire it as an instruments-service CLI subcommand (`--operation reprocess-shards`) per
      `script-homes.md`'s production-verb rule. — `instruments-service@e9eac282`.
- [x] ✅ [SCRIPT] P3. Retire the 13 one-off scripts above (was: 11 — verify-rerun-2 finding 151, 2026-07-14:
      title/summary were corrected 2026-07-12 to 13, but this todo's count was never updated) once the generic tool
      covers their use cases (or leave the already-run ones as historical record — they don't need deletion if inert,
      just no new ones going forward). **DONE 2026-07-30 — took the "leave as historical record" branch, no deletion
      executed.** Verified all 13 scripts still exist in their original repos (instruments-service ×12,
      market-tick-data-service ×1), each still carries a valid 3-line
      `# Epic: / # Lifecycle: oneoff / # Delete-when: <condition>` header per `script-homes.md`'s lifecycle-marker
      convention, and none is imported by other code — a corpus grep found only docstring cross-references ("sister
      script to…", "companion to…") from a handful of sibling one-offs, never a `from scripts.X import`. Each script's
      own `Delete-when:` condition is a per-incident production verification (e.g. "manifest attempted_failed count
      reduced", "GCS orphan-sweep = 0") that was out of this pass's bounded scope to re-verify live for all 13 — the
      todo's own stated alternative explicitly permits this ("they don't need deletion if inert, just no new ones going
      forward"), which the shipped CLI (items 1-3 above) already satisfies. Added a worked-example note to
      `/codex/06-coding-standards/script-homes.md` § "Repo `scripts/` sub-rules" pointing future incidents at
      `instruments-service --operation reprocess-shards` instead of a fresh hand-written one-off.

> **🟢 ARCHIVED 2026-07-30** — status=resolved, all 4 todos done/covered, 0 open todos, moved to
> `/plans/archive/issues/manifest_reprocessing_generic_utility_2026_07_07.md`. Archived per
> `/codex/11-project-management/issue-doc-lifecycle.md`'s archive-on-resolve rule.

## Progress Log

- **2026-07-30 (slot 7, infra)** — Dispatched `manifest_reprocessing_generic_utility-003` (the third `[CODE] P2` todo,
  wiring the CLI). Added `--operation reprocess-shards` to `instruments-service/instruments_service/cli/main.py`,
  following the existing `--operation=status` / `--operation=refresh-league-entity-coverage` pattern: it bypasses
  `ServiceBootstrap`'s date-loop (a maintenance verb, not a date-fetch) and dispatches from `main_service_cli()` before
  the daily-recon date-default logic. New `_run_reprocess_shards()` parses `--asset-group`, `--bucket` (resolves via
  `get_write_bucket_name("instruments", asset_group)` when omitted — one of the two is required, fails loud otherwise),
  `--venue`, `--capture-status` (default `attempted_failed`, validated against the `CaptureStatus` enum — an unknown
  value fails loud rather than silently matching zero rows), `--error-reason-contains` (case-insensitive substring,
  wired to `select_shards_for_reprocess`'s `error_reason_predicate`), `--date-start`/`--date-end`, `--target-status`
  (default `expected_unattempted`, also enum-validated), `--target-error-reason`, and `--apply` (dry-run by default).
  Calls `read_availability_index` → `select_shards_for_reprocess` → `reprocess_shards` (all three imported from
  `unified_trading_library`'s top-level re-export) and prints one JSON object to stdout with the match/flip counts +
  captured-count invariant values — matches the plan's own worked example:
  `instruments-service --operation reprocess-shards --asset-group cefi --venue ASTER --capture-status attempted_failed --error-reason-contains "404" --date-start 2024-10-01 --date-end 2026-05-14 [--apply]`.
  6 new unit tests in `tests/unit/cli/test_reprocess_shards_cli.py` covering: unknown capture-status rejection, missing
  bucket/asset-group rejection, dry-run default with venue + error-reason-contains filtering (case-insensitive), the
  `--apply` abort when `MANIFEST_PER_VM_SHARDS`/`VM_NAME` are unset (surfaces `reprocess_shards`'s own
  `MissingReprocessShardIsolationError`), and bucket resolution from `--asset-group` when `--bucket` is omitted. All 27
  tests in `tests/unit/cli/` pass; `bash scripts/quality-gates.sh` green. Shipped `instruments-service@e9eac282` via
  quickmerge.

- **2026-07-30 (slot 6, infra)** — Dispatched `manifest_reprocessing_generic_utility-002` (the second `[CODE] P2` todo).
  Implemented `reprocess_shards()`'s body in `unified_trading_library/manifest_reprocess.py`, replacing the
  `NotImplementedError` stub, porting all three pinned safety gates verbatim from
  `retry_transient_cefi_failures_2026_06_28.py`: (1) per-VM shard isolation — `dry_run=False` requires
  `MANIFEST_PER_VM_SHARDS=true` + non-empty `VM_NAME` in the environment, checked via a new
  `_has_reprocess_shard_isolation()` (raw env reads mirroring the template's `_validate_apply_env` and the identical
  `manifest_migrations.v7_to_v8` pattern — deliberately NOT `UnifiedCloudConfig`, since this asks "did the operator
  declare isolation for THIS run", not "what's the shared default"), aborting via a new
  `MissingReprocessShardIsolationError` before any mutation; (2) idx-only mutation — `df.loc[idx, ...]` never re-derives
  a selection; (3) captured-count invariant — computed before/after via a new `_captured_row_count()` helper, raising
  `RuntimeError` (no partial write) on mismatch. The write path re-uses the established `ManifestWriter._INDEX_PATH`
  canonical-index constant (matching how `_maintenance.py`/`_read_index.py`/existing tests already reference it
  cross-module) and resolves its storage client lazily via
  `unified_trading_library.cloud_interface.get_storage_client()` with no explicit provider (matching
  `read_availability_index`'s own resolution pattern, rather than hardcoding `provider="gcp"` like the CeFi-specific
  template did). Dry-run (the default) and the zero-matched-rows case both short-circuit before any env-gate check or
  write — mirrors the template's own early-return. Replaced the prior stub-only test
  (`test_reprocess_shards_not_yet_implemented`) with 5 real tests covering: zero-matched no-op, dry-run (no mutation/no
  write, isolation env not required), missing-isolation abort (row untouched), a full apply that flips only the matched
  row and writes the parquet back (verified via a `_StubStorageClient` patched onto
  `unified_trading_library.cloud_interface.get_storage_client`), and the captured-count-invariant abort (no write
  attempted). All 17 tests in `tests/unit/test_manifest_reprocess.py` pass; `bash scripts/quality-gates.sh` green (one
  iteration caught a real false-positive: a docstring line containing the literal substring `os.environ` with no `noqa`
  tripped the codex-compliance grep check even though the actual code lines already carried the correct
  `qg-os-environ`/`config-bootstrap` markers — reworded the prose to avoid the banned literal, no logic change). Shipped
  `unified-trading-library@4b6a13cf` via quickmerge.

- **2026-07-30 (slot 6, infra)** — Dispatched `manifest_reprocessing_generic_utility-001` (the `[DESIGN] P2` todo).
  Resolved the placement question and shipped `unified_trading_library/manifest_reprocess.py`: `CaptureStatus` +
  `pd.Index`-shaped
  `select_shards_for_reprocess(df, *, asset_group=None, venue=None, capture_status=CaptureStatus.ATTEMPTED_FAILED.value, date_start=None, date_end=None, error_reason_predicate=None)`
  fully implemented (pure filter, no I/O — mirrors the template script's `_identify_transient_rows`, generalized with
  asset_group/venue-or-data_type/date-range/reason-predicate filters);
  `reprocess_shards(bucket, df, idx, *, target_status=..., target_error_reason="", dry_run=True) -> ReprocessResult`
  signature + its 3-gate safety contract (per-VM shard isolation before any write, mutate ONLY the given `idx`,
  captured-count invariant) pinned in the docstring, body a documented `NotImplementedError` — implementing it is the
  next `[CODE] P2` todo, deliberately left untouched. Re-exported through the top-level `unified_trading_library`
  `__init__.py` (`ReprocessResult`, `reprocess_shards`, `select_shards_for_reprocess`) so market-tick-data-service and
  instruments-service can import it once the CLI-wiring todo lands. 13 new unit tests in
  `tests/unit/test_manifest_reprocess.py` covering every filter dimension + combinations, plus one asserting the
  `reprocess_shards` stub still raises (so a future partial implementation can't silently skip the documented safety
  gates without a test failure). `bash scripts/quality-gates.sh` run before shipping.

- **2026-07-07** — Filed from the ASTER/CEFI instrument-service data-status audit, prompted by the operator asking
  whether the 2026-05-14 ASTER base-URL fix needed a follow-up reprocessing run. No files edited.

- **2026-07-30 (plans-corpus reduction marathon, wave 3)** — Closed the final `[SCRIPT] P3` retirement todo (see above)
  by taking the doc's own "leave as historical record" branch — verified all 13 one-offs, no deletions. Added the
  worked-example note to `/codex/06-coding-standards/script-homes.md`. All 4 todos now done/covered — archiving this
  session per the 6-step ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): referrer paths
  corpus-wide grep + fix pending in the same commit that moves this file.
