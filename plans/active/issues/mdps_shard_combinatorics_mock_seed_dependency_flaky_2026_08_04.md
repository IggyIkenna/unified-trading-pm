---
doc_type: issue
title: >-
  market-data-processing-service's shard-combinatorics smoke tests (135 CLI dry-run cases) intermittently fail
  all-or-nothing on a missing slot-level mock-seed-data marker, plus 2 unrelated stale pre-existing assertions in the
  same test file
summary: >-
  Discovered while shipping an unrelated fix (registering PredictionBookSnapshotAdapter,
  `prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` todo 4). Running `bash scripts/quality-gates.sh`
  repeatedly on the exact same committed SHA produced non-deterministic results: sometimes 2347/2347 pytest tests pass,
  sometimes exactly 138 fail (135 of one parametrized test + 2 other pre-existing stale assertions), with byte-
  identical failure signatures each time it fails. Root-caused via traceback + direct filesystem inspection — three
  independent, unrelated causes bundled in one failing test file (`tests/smoke/test_shard_combinatorics.py`).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-data-processing-service, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [flaky-test, mock-seed-data, shard-combinatorics, qg, test-infra]
related: [/plans/active/issues/prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md]
created: "2026-08-04"
last_updated: "2026-08-04"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
source: >-
  Discovered live while shipping `prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` todo 4 (slot 5,
  backend_engineer, 2026-08-04) — repeated QG re-runs on an identical committed SHA produced inconsistent pytest
  results, forcing a byte-identical-failure verification pass per the CLAUDE.md repo-blocker protocol before it was safe
  to ship.
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    market-data-processing-service/tests/smoke/test_shard_combinatorics.py,
    market-data-processing-service/market_data_processing_service/engine/mock_data_provider.py,
    market-tick-data-service/scripts/seed_mock_data.py,
  ]
---

# MDPS shard-combinatorics smoke tests: 3 bundled unrelated issues, one causing non-deterministic QG (2026-08-04)

## What I found (all read-only investigation, no data mutation)

While shipping an unrelated 5-file diff (a new `PredictionBookSnapshotAdapter` registration, zero overlap with anything
below), `bash scripts/quality-gates.sh` on the exact same committed SHA (`market-data-processing-service@1c2db48`)
produced wildly different pytest results across 5 consecutive runs: 1 run passed 2347/2347, the other 4 runs each failed
the identical 138 tests (byte-identical test IDs and assertion messages every time). Verified via the standard "stash
the diff, run on the clean parent commit" recipe that the parent tree (`6003ac2`) is not inherently the cause either (it
also passed clean once) — the flakiness tracks a filesystem precondition, not either commit's content.

Root-caused via full (non-truncated) traceback capture — the 138 failures decompose into **3 independent, unrelated
causes**, all pre-existing (none touch PREDICTION/book_snapshot_5):

1. **135/138 — `test_cli_dry_run_all_category_venue_combos` (ALL CEFI/TRADFI/DEFI venue combos, all-or-nothing).**
   `market_data_processing_service/engine/mock_data_provider.py::generate_mock_candles` checks for a `.seed-complete`
   marker under `{slot_root}/.local-dev-cache/mock-seed/market-tick-data-service/` (`_get_seed_base()` resolves via
   `Path(__file__).resolve().parents[3]` — the SLOT root, shared across every repo in that slot, not per-repo). On this
   slot (`.tabs/5`), that marker **does not exist at all** (confirmed via direct `ls` both immediately after a failing
   run and independently) — nothing in `quality-gates.sh`, the shared `quality-gates-base/` scripts, or any
   `conftest.py` autouse fixture ever invokes `market-tick-data-service/scripts/seed_mock_data.py` (or
   `instruments-service`'s own upstream Layer-1 seed step) to create it. Whichever QG run happens to observe the marker
   present passes ALL 135 combos; whichever observes it absent fails ALL 135 identically
   (`AssertionError: Dry-run failed for {category}/{venue}` /
   `No upstream tick data at ... — run market-tick-data first`). This is consistent with the marker being created
   transiently by some OTHER concurrent process on the shared host (a different slot's own MTDS/instruments-service test
   run) and then cleaned up by that same run's teardown — i.e. a genuine cross-repo, cross-slot test-fixture race, not
   something either commit under test controls.
2. **1/138 — `test_total_shard_combinations`.** Hardcoded `assert total_combinations < 10000` — the real, current count
   is **27055** (`defi: 35 dt × 101 venues × 7 tf = 24745` dominates). This threshold is stale relative to the current
   DEFI venue/data-type registry size and would fail on ANY commit, unrelated to this session's diff.
3. **1/138 — `test_defi_specific_data_types`.** Asserts `"dex_swaps" in defi_types`, but the canonical name was
   operator-locked to `"dex_pool_swaps"` per `codex/02-data/defi-canonical-naming-ssot.md` (the sibling
   `test_adapter_registry_coverage.py` already carries a comment documenting this exact rename) — this assertion was
   never updated after the rename.
4. **1/138 — `test_instruments_domain_separation`** (integration test): raises
   `BucketNamingError: Unknown cloud provider 'local'; expected one of ('gcp', 'aws')` — an env/config value of `local`
   reaching `as_cloud()`, which only accepts `gcp`/`aws`. Also unrelated to this session's diff.

## Why this matters

QG-run non-determinism on an UNCHANGED committed SHA is exactly the failure mode the `quality-gates.sh` Pass-1 sentinel
mechanism assumes cannot happen (`RULES.md` § 2: "the sentinel Pass 1 writes is keyed to the exact HEAD SHA"). A worker
without this investigation would either (a) wrongly believe their unrelated change caused 138 failures and start
debugging/reverting correct code, or (b) get lucky on the first run and never notice the underlying fragility. Both are
bad outcomes for fleet throughput on a shared, heavily-loaded host (observed load average 13-18 with 7-13 concurrent
full `quality-gates.sh --no-fix` processes during this investigation).

## What I did NOT do (and why)

- **Did not build a cross-repo mock-seed orchestration fix** (seeding instruments-service → market-tick-data-service →
  market-data-processing-service in the correct dependency order) — that is real scope, out of bounds for the P1
  adapter-registration task this was discovered under. Todo 1 below owns it.
- **Did not fix the two stale assertions inline** — they are unrelated to the diff being shipped and belong to whichever
  recent DEFI-venue-expansion / dex_swaps-rename work should have updated them. Todos 2-3 below own them.

## Todos

- [ ] [INFRA] P2. **Make the slot-level mock-seed-data chain (instruments-service → market-tick-data-service →
      market-data-processing-service) deterministically available before
      `tests/smoke/test_shard_combinatorics.py::test_cli_dry_run_all_category_venue_combos` runs**, OR mark that
      parametrized test `@pytest.mark.skipif` when the upstream `.seed-complete` marker is absent (a live-verified
      precondition it currently trusts silently) instead of failing all 135 combos with a raw `assert result == 0`.
      Repo: market-data-processing-service (+ market-tick-data-service, instruments-service for the seed orchestration
      option). Done when: 5 consecutive `bash scripts/quality-gates.sh` runs on an unchanged tree produce identical
      pytest pass/fail counts (no more all-or-nothing flip).
- [ ] [SCRIPT] P3. **Fix the stale `test_total_shard_combinations` threshold**
      (`tests/smoke/test_shard_combinatorics.py:92`) — either raise the hardcoded `< 10000` bound to reflect the real
      current combinatorics (27055+ headroom) or make it a documented ratchet rather than a magic number. Repo:
      market-data-processing-service.
- [ ] [SCRIPT] P3. **Fix the stale `test_defi_specific_data_types` assertion**
      (`tests/smoke/test_shard_combinatorics.py:118`) — replace the retired `"dex_swaps"` expectation with the canonical
      `"dex_pool_swaps"` name per `codex/02-data/defi-canonical-naming-ssot.md`. Repo: market-data-processing-service.

## Progress Log

- **2026-08-04 (slot-5, backend_engineer)**: filed after root-causing a 4-of-5 non-deterministic QG run while shipping
  an unrelated diff; full evidence above.
