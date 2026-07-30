---
doc_type: issue
title: Sports process_ticks unit tests depend on a CI-seeded GCS emulator (hermeticity gap)
summary:
  During pipeline_mode GATE-0 (2026-06-16), the mtds QG surfaced 7 pre-existing failing sports unit tests
  (test_sports_v9_canonical_path / test_orchestrator_per_data_type_sentinel / test_sports_odds_available_at) —
  process_ticks() runs the _check_sports_v9_columns preflight against a SEEDED GCS emulator manifest that CI injects,
  which a hermetic local run lacks. CI-green, order-flaky, fails on a clean local LDR checkout. Fixed for those 3 files
  with a scoped autouse fixture stubbing the guard to a no-op (test-only, no prod-code change); the broader
  process_ticks-calling sports unit-test suite in mtds was never audited for the same dependency. Orphaned when its
  original home (pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md) was rehomed during the 2026-07-27
  vintage audit — filed as its own issue doc per that audit's disposition.
status: resolved
nature: issue
asset_group: [sports]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer]
tags: [test-hermeticity, sports, mtds, ci, unit-tests]
related:
  [
    /plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-07-27
parent_epic: sports_master
priority: P2
estimate_class: refactor
drift_direction: advance-code
depends_on: []
source:
  [
    "pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md tick-5 finding (GATE-0 mtds shipping,
    2026-06-16) — rehomed 2026-07-28 per june_2026_vintage_audit_findings_2026_07_27.md §4",
  ]
assigned_vm: NA
execution_scope: local-only
resolved_by:
  "2026-07-29 batch closeout pass — audit found no remaining gap: every process_ticks-calling sports test file already
  carries the scoped autouse fixture (or an equivalent inline patch), and test_league_partitioning.py had already
  independently picked up the same fixture beyond the original 3 GATE-0 files"
locked_by:
locked_since:
---

> **✅ ARCHIVED 2026-07-29** (batch closeout pass, market-tick-data-service docs batch). Audit performed: grepped every
> test file calling `process_ticks(` (17 files) and every file referencing `_check_sports_v9_columns` (7 files).
> `test_sports_v9_canonical_path.py`, `test_league_partitioning.py`, `test_orchestrator_per_data_type_sentinel.py`, and
> `test_sports_odds_available_at.py` all already carry the scoped `autouse` no-op fixture (the 2nd file was NOT one of
> the original 3 GATE-0-blocking files — it picked up the same pattern independently in the interim);
> `test_sports_live_writer_gaps.py` patches the guard inline per-test; `test_sports_v9_preflight_guard.py` is the
> guard's own dedicated test (out of scope by design, per this doc's own text). Ran all 17 `process_ticks(`-calling test
> files locally (no CI, no emulator injection): `276 passed in 18.70s`, zero failures. Done-when condition ("a full
> local run of the sports unit suite in mtds is green") is satisfied — no fixture gap remains to fix.

# Sports `process_ticks` unit tests depend on a CI-seeded GCS emulator (hermeticity gap)

## What I found (provenance: GATE-0 tick-5, 2026-06-16)

mtds QG surfaced 7 pre-existing failing sports unit tests (`test_sports_v9_canonical_path` /
`test_orchestrator_per_data_type_sentinel` / `test_sports_odds_available_at`) — `process_ticks()` runs the
`_check_sports_v9_columns` preflight against a SEEDED GCS emulator manifest that CI injects (`base-service.sh`: "CI
injects emulators via env") but a hermetic local run lacks. CI-green, order-flaky, fails on a clean LDR checkout
(unrelated to whatever change happens to be in flight when someone hits it). The guard's own coverage lives in
`test_sports_v9_preflight_guard.py` (unaffected).

**Fixed for the 3 files that blocked GATE-0**: a scoped `autouse` fixture in each of the 3 files stubs the incidental
guard to a no-op → emulator-free + order-independent (test-only, no prod-code change; 132 tests green after).

## What's still open

The fix above was scoped to unblock the 3 files that were actually failing at the time — it was never a fleet-wide
audit. Audit the broader `process_ticks`-calling sports unit-test suite in `market-tick-data-service` for the same
`_check_sports_v9_columns` seeded-emulator dependency, and apply the same scoped-fixture fix wherever it recurs.

- [x] ✅ [TEST] P2. **DONE 2026-07-29 (batch closeout pass).** Audited every `process_ticks`-calling sports unit test —
      see the archival banner above for the full file-by-file breakdown. No gap found; `276 passed` locally with no
      emulator. Done-when condition satisfied.

## Progress Log

- 2026-07-27: Orphaned from `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` (its `[TEST] P2`
  DEFERRED-followup todo) during the 2026-07-27 vintage audit's item-4 rehome pass — no existing sports test-hygiene
  track was a clean fit (`sports_consolidated_closeout_2026_07_19.md` Track K covers feature-content smoke/right-days
  assertions in features-service, a different repo and a different class of test than mtds unit-test hermeticity), so
  filed as a standalone issue doc per that audit's disposition instructions.
