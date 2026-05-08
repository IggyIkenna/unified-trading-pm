---
title: "UTL QG broken on live-defi-rollout post Tab 2 pipeline_mode + streaming commits"
created: 2026-05-08
author: tab4-aws-migration
source:
  - unified-trading-library@52f123d6 feat(manifest-reader): pipeline_mode-aware reader with legacy fallback chain
  - unified-trading-library@8c67df5d feat(utl): Phase 2B UTC-aligned timeframe scheduler + BoundaryTick
  - unified-trading-library@87134364 feat(manifest-writer): pipeline_mode kwarg on record_* methods
  - unified-trading-library@f24e651b feat(utl): Phase 2A+2C streaming — Redis Streams client + replay-cascade helpers
  - unified-trading-library@68b3804a feat(manifest-writer): EXPECTED_UNATTEMPTED capture_status + reject blank reason on record_empty
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# UTL QG broken on `live-defi-rollout` after Tab 2 pipeline_mode + streaming commits

> **Severity**: P0 — `bash scripts/quality-gates.sh` failed in `unified-trading-library` with 25 failed tests + 2 errors as of 2026-05-08 (Tab 4 ran QG pre-push of `cloud_interface/bucket_naming.py`). Failures predate Tab 4's changes — verified via `git blame`/`git log` against the failing test paths. Tab 4 work is isolated to `cloud_interface/` + `core/seed_writer.py`, all 35 new tests pass, no shared modules with the failing surface.
>
> **Blast radius**: every UTL consumer that imports `manifest_writer`, `streaming.redis_stream`, `streaming.replay`, `streaming.utc_aligned_scheduler`, or `legacy_reason_classifier`. Live-pipeline plan Phase 2 + writegate Phase 3.D.5 + manifest v6→v7 all depend on green UTL CI.
>
> **Suggested owner**: Tab 2 (live-pipeline + writegate Phase 3.D.5) — these are their commits.

## What I found

`cd unified-trading-library && bash scripts/quality-gates.sh` (2026-05-08T~14:05Z) reports:

```
25 failed, 2504 passed, 7 skipped, 1 warning, 2 errors in 71.80s
```

Failure clusters (all on tests EXISTING before Tab 4 work):

1. **`LegacyBlankErrorReasonError` raises in 16 manifest_writer tests** — `test_manifest_writer_capture_status.py` (8), `test_manifest_writer_defi_canonicalisation.py` (10), `test_manifest_writer_flush_cadence.py` (1), `test_manifest_writer_normalising.py` (1), `test_manifest_writer_record_empty_reason.py` (1), `test_manifest_writer_v6.py` (1), `test_manifest_writer_v7.py` (1). Root cause: UTL@`68b3804a` (commit message: "reject blank reason on record_empty") tightened `record_empty()` to require a typed `EMPTY_CONFIRMED_REASONS` value but the existing tests still pass blank reason. Either the new strict mode should be backward-compatible for tests, or every test should be migrated to pass a typed reason.

2. **`test_legacy_reason_classifier::test_cefi_always_returns_source_returned_zero`** — 1 fail. Likely related to the same blank-reason rejection.

3. **`test_redis_stream` + `test_replay`: ImportError** — 2 errors. Tab 2's `feat(utl): Phase 2A+2C streaming — Redis Streams client + replay-cascade helpers` (UTL@`f24e651b`) shipped streaming modules but the test imports point at modules that don't exist or have different shapes. Need the test fixtures wired.

4. **`test_utc_aligned_scheduler::test_first_callback_fires_at_aligned_boundary_plus_grace`** — 1 timeout (5.0s `asyncio.wait_for` exceeded). Tab 2's `feat(utl): Phase 2B UTC-aligned timeframe scheduler + BoundaryTick` (UTL@`8c67df5d`) ships the scheduler. Test wait-for timeout vs scheduler grace-period misalignment.

Coverage gate: 77.52% ≥ 65% MIN_COVERAGE — passes.

## Why it matters

- `live-defi-rollout` is the working branch; VMs pull from it and CI runs against it. **Red CI on `live-defi-rollout` blocks the workspace.** Per CLAUDE.md "CI Verification After Every Push (HARD RULE)": "A red CI on `live-defi-rollout` blocks the workspace; fix immediately."
- Multiple downstream services (MTDS, MDPS, features-onchain, instruments-service) install UTL via `uv pip install -e .` editable. If UTL test surface is red, every service's QG is also red — entire workspace cascade-blocked.
- Tab 4's bucket_naming.py work IS pushed despite this red CI per CLAUDE.md "QG failure attribution": *"if QG fails on code another agent wrote (verify via `git blame` / `git log`), continue staging + committing + pushing your work anyway — they fix their breakage on their own commits."* Verified via `git log` that all failing tests trace to commits 87134364 / f24e651b / 8c67df5d / 68b3804a — Tab 4 commits do not touch `manifest_writer.py`, `streaming/`, or `legacy_reason_classifier.py`.

## Recommended decision

Tab 2 owns the fix. Two parallel restoration paths (pick one or both):

- **(a) Backward-compat path** — `record_empty()` accepts blank reason in test mode (e.g. via a `_legacy_blank_ok=True` constructor param) until the test migration sub-task lands. Lowest blast radius. Preferred for May-23 critical path.
- **(b) Test migration path** — sweep every `test_manifest_writer_*.py` test that calls `record_empty()` with blank reason, pass a typed reason (default `SOURCE_RETURNED_ZERO`). Highest correctness but ~16 test files to migrate.

Streaming + scheduler failures (clusters 3 + 4) are independent: fix the test fixtures or relax the asyncio timeout, ship as separate commits.

## Tab 4's stance

- bucket_naming.py + 35 new tests + seed_writer.py refactor pushed as a separate commit per CLAUDE.md attribution rule.
- This issue surfaces the foreign QG breakage so Tab 2's owners can fix it without Tab 4's commit being mistaken for the source.
- **Do NOT include** Tab 4's commit in any rollback that targets the streaming / pipeline_mode commits — they're independent.

## Cross-references

- CLAUDE.md § "CI Verification After Every Push (HARD RULE)"
- CLAUDE.md § "QG failure attribution" (workspace push-vs-quickmerge rule, 2026-05-06)
- `plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md` (Tab 2 plan-of-record)
- `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` Phase 3.D.5 (typed-reason taxonomy)
