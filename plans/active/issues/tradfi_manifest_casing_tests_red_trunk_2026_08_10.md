---
doc_type: issue
title:
  market-tick-data-service QG red on trunk — 3 pre-existing TradFi instrument_type-casing tests fail at LDR HEAD
  (2026-08-10)
summary: >-
  A full `quality-gates.sh` run for a LIGHTER-ZKSYNC migration fix (slot 20, 2026-08-10) found 3 unit tests FAILING on a
  clean tree at `origin/live-defi-rollout` HEAD (48df1fd7) — verified byte-identical on a detached worktree with the
  in-flight change absent. All three are in the TradFi `instrument_type` casing-migration domain
  (`_tradfi_manifest_itype` / COMBO casing / casing-frame `changed_count`), NOT the cefi migration being shipped. The
  cefi change itself is green (10508 passed; its own 12 regression tests pass). This doc tracks the pre-existing trunk
  red so a fix-worker can clear it and unblock quickmerge on this repo.
status: open
nature: issue
asset_group: [tradfi, cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tradfi, casing, instrument-type, manifest, qg-red, pre-existing, repo-blocker]
related:
  [
    /plans/active/issues/cefi_lighter_zksync_systemic_collision_2026_08_08.md,
    /plans/archive/2026_08/tradfi_casing_100pct_redrift_2026_07_27.md,
    /plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md,
  ]
created: 2026-08-10
author: slot-20
priority: P1
parent_epic: tradfi_master
source:
  - "slot 20 quality-gates.sh run for cefi_lighter_zksync_systemic_collision, 2026-08-10; verified pre-existing at LDR
    HEAD 48df1fd7 on a clean worktree"
assigned_vm: planning
assigned_role: data_engineering
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# market-tick-data-service QG red on trunk — 3 pre-existing TradFi casing tests

## What I found

`bash scripts/quality-gates.sh` (full, Pass-1, no skip flags) on `market-tick-data-service` HEAD `13ac6245` (the cefi
wire-superset migration fix, slot 20) reported **3 failed / 10508 passed / 28 skipped / 1 xpassed**. The 3 failures are:

1. `tests/unit/engine/test_tradfi_manifest_shard.py::test_tradfi_manifest_itype_continuous_future_now_upgrades_to_future`
   — `assert _tradfi_manifest_itype("CME", "continuous_future") == "FUTURE"` → got `'continuous_future'` (unconverted).
2. `tests/unit/scripts/test_migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py::test_build_casing_frame_upgrades_every_known_residual_token`
   — `assert outcome.changed_count == 7` → got `6` (one of 7 known residual tokens not upgraded).
3. `tests/unit/test_venue_fetch_cefi_manifest_canonicalization.py::TestTradfiRecordVenueShardCountsCanonicalization::test_cme_combo_shard_itype_upgrades_but_id_stays_empty`
   — `assert shard_key[3] == "COMBO"` → got `'combo'` (lowercase).

**Pre-existing verification (per RULES.md § 4b):** created a detached worktree at `origin/live-defi-rollout` HEAD
`48df1fd7` (the exact LDR tip, WITHOUT the in-flight cefi commit), and ran the same 3 tests there with the repo venv:
**byte-identical failures** (same assertions, same got-values). The red is NOT introduced by the cefi change; it lives
on the shared trunk.

**Not the shipped change:** the in-flight commit `13ac6245` only touches
`scripts/migrate_cefi_tardis_filename_canonical_2026_07_17.py` + its regression test
(`test_migrate_cefi_tardis_broad_dup_compare_2026_08_10.py`, 12/12 pass). None of the 3 failing test files imports that
module (`grep` confirms). This is a repo-blocker: unrelated staged work cannot ship under the green-tree rule.

**Context:** the failing tests live in the TradFi `instrument_type` casing-migration domain — the same area of the
archived `tradfi_casing_100pct_redrift_2026_07_27.md` (resolved 2026-08-04 via `4cae1cb0` ceiling-raise + real apply)
and `tradfi_manifest_content_recovery_completion_2026_07_24.md`. The `_tradfi_manifest_itype` canonical emitter is
expected to UPPERCASE `continuous_future`→`FUTURE` and COMBO→`COMBO`; recent commits (`4e631a3d`, `4122df13`,
`41391cba`, `65beaeaf`, `4cae1cb0`) last touched these test files / the resolver. Root cause of the current red is NOT
diagnosed here (out of the cefi task's scope) — this doc exists to route the fix.

## Why it matters

- A red `quality-gates.sh` on `market-tick-data-service` blocks EVERY agent's quickmerge ship on that repo (Pass-2
  `--agent` verifies the `.qg_last_passed_sha` sentinel == HEAD; no sentinel is written on a failing run). It is
  currently blocking the cefi LIGHTER-ZKSYNC wire-superset migration fix (tracked in
  `cefi_lighter_zksync_systemic_collision_2026_08_08.md`).
- The failures are all in the TradFi casing domain — a data-correctness surface (manifest `instrument_type` casing
  drives shard atoms / reader paths / the 4-surface reconciliation).

## Recommended decision

Fix the 3 tests / the underlying casing emitter on `market-tick-data-service` and get a clean full `quality-gates.sh`
run. Do NOT `--skip-*` to dodge; do NOT modify the cefi migration to work around a trunk red. Once green, the
repo-blocker auto-resolves and pending quickmerge ships proceed.

## Todos

- [ ] [DATA] P1. **Fix the 3 STALE mtds tests to match the UTL canon reversal (`74fe04fd`, 2026-08-10) — NOT by
      restoring the `continuous_future→FUTURE`/`combo→COMBO` mapping** — repo: market-tick-data-service. **CORRECTED
      ROOT CAUSE (2026-08-10, slot 20 — supersedes this todo's original hypothesis below):** the 3 failures are STALE
      TEST EXPECTATIONS, not a production bug. UTL canon `unified-trading-library@74fe04fd` (2026-08-10 21:10Z)
      **deliberately reversed** the prior `continuous_future→FUTURE`/`combo→COMBO` manifest-column mapping, after a live
      census showed **473,374 manifest rows with bundle-grain signature (populated `underlying`, null `instrument_id`)
      incorrectly classified as per-contract FUTURE rows** — `combo`/`continuous_future` are id-less bundle aggregates,
      permanently excluded from casing-upgrade like `futures_chain`/`options_chain`. That commit updated the UTL +
      instruments-service tests but NOT these 3 mtds tests. The production code (`_tradfi_manifest_itype` in
      `_tradfi_manifest_shard.py`, `build_casing_frame` in the casing migration script, `_record_venue_shard_counts` in
      `venue_fetch.py:391`) all route through the shared UTL canon and are CORRECT. **The fix is to update the 3 tests
      to expect lowercase pass-through** (`continuous_future` stays `'continuous_future'`, `combo` stays `'combo'`),
      matching `74fe04fd`'s canonical list. Do NOT restore the mapping — that re-introduces the misclassification bug
      the reversal fixed. 1.
      `tests/unit/engine/test_tradfi_manifest_shard.py::test_tradfi_manifest_itype_continuous_future_now_upgrades_to_future`
      → expect `_tradfi_manifest_itype("CME", "continuous_future") == "continuous_future"` (rename test). 2.
      `tests/unit/scripts/test_migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py::test_build_casing_frame_upgrades_every_known_residual_token`
      → the 7-token frame's `combo` row now stays lowercase: `changed_count == 6`, full_df set drops `"COMBO"`, keeps
      `"combo"` (combo is bundle-grain excluded, not a known residual token anymore). 3.
      `tests/unit/test_venue_fetch_cefi_manifest_canonicalization.py::TestTradfiRecordVenueShardCountsCanonicalization::test_cme_combo_shard_itype_upgrades_but_id_stays_empty`
      → `shard_key[3] == "combo"` (was `"COMBO"`); the test name + docstring change too (combo no longer upgrades). Done
      when: full `bash scripts/quality-gates.sh` green on market-tick-data-service (which also unblocks the cefi ship
      waiting on repo-blocker RB-90251f57).

## Progress Log

- **2026-08-10 (slot 20, dispatched on the fix todo, root-caused + CORRECTED the hypothesis)** — Investigated the 3
  failures fully and found the original todo hypothesis was WRONG. Verified: (a) the mtds venv resolves UTL from the
  sibling source clone (`.tabs/20/unified-trading-library`), which carries `74fe04fd` (2026-08-10 21:10Z, on origin);
  (b) `74fe04fd` deliberately removed `continuous_future`/`combo` from `_MANIFEST_ITYPE_CANONICAL` and added both to
  `_BUNDLE_GRAIN_EXCLUDED` (census: 473,374 bundle-grain rows misclassified as per-contract FUTURE); (c) all 3 mtds
  tests assert the pre-reversal behavior and are STALE — the production code paths
  (`_tradfi_manifest_itype`/`build_casing_frame`/`_record_venue_shard_counts`) route through the shared UTL canon and
  are correct. **This todo's fix is to update the 3 stale tests, NOT restore the mapping** (restoring would re-introduce
  the misclassification bug). Test edits are fully specified in the todo body above; each is a one-line assertion/name
  change. Compaction interrupted mid-task (context gate) — the edits are NOT yet applied; resume by making the 3 test
  edits, running `bash scripts/quality-gates.sh`, then quickmerge + flip.

## Deferred work after 2026-08-10

| Item                                                                                                           | State / why deferred                                                                                  | Blocked on                                    |
| -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| Update the 3 stale mtds tests to expect lowercase `continuous_future`/`combo` (UTL canon `74fe04fd`)           | Not done — root-caused + fully specified, edits not yet applied (compact interruption)                | Nobody — pick up here                         |
| Re-run `bash scripts/quality-gates.sh` on market-tick-data-service green, then quickmerge + flip this checkbox | Not done — depends on the test edits above                                                            | The test edits above                          |
| Ship cefi wire-superset fix `market-tick-data-service@13ac6245` (already committed + plan flip pushed)         | Not done — push blocked on this same trunk red (repo-blocker RB-90251f57); fixing the tests clears it | This todo's test fix + the repo turning green |

**Recommended next item**: make the 3 test edits specified in the todo body above (they are precise one-liners), run QG,
quickmerge, flip this checkbox — this simultaneously unblocks the cefi ship waiting on RB-90251f57.
