---
doc_type: issue
title:
  market-tick-data-service quality-gates.sh RED — tradfi COMBO instrument_type casing mismatch (2 failing tests),
  pre-existing / unrelated to a concurrent in-flight fix
summary: >-
  While shipping an unrelated fix (pipeline_e2e_check.py's captured-days OOM fix,
  mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md), quality-gates.sh's pytest phase failed on 2 tests
  unrelated to the shipped change: test_build_casing_frame_upgrades_every_ known_residual_token (asserts
  changed_count==7, gets 6) and test_cme_combo_shard_itype_now_canonicalizes_uppercase (asserts shard_key[3]=="COMBO",
  gets "combo"). Confirmed pre-existing: byte-identical failure on HEAD~1 (before the shipped commit) and on a fresh git
  pull --rebase (multiple newer commits pulled in, same 2 failures persist). Several very recent commits on
  live-defi-rollout touch this exact area (65dc99a5, 6fa0dd9d, fbc9cc6f, b13e3a2b, 5f037099 -- all "fix(tradfi): ...
  combo ..." / "update ... itype casing tests"), strongly suggesting another slot's in-flight, multi-commit tradfi COMBO
  casing migration is mid-flight and the tree is transiently red between commits, not a settled bug -- but as of this
  doc's filing time the 2 tests are still red on the latest pulled tip.
status: open
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [ci-red, quality-gates, tradfi, combo, instrument-type-casing, repo-blocker]
related: [/plans/active/tradfi_consolidated_closeout_2026_07_18.md]
created: 2026-08-15
author: slot-29 (backend_engineer)
source: ["mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md, shipping the [CODE] P1 fix"]
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-15
parent_epic: infrastructure_master
priority: P1
---

# market-tick-data-service QG red: tradfi COMBO instrument_type casing mismatch

## What I found

Two tests fail on `live-defi-rollout` HEAD (verified across two separate pulls, several commits apart):

1. `tests/unit/scripts/test_migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py:: test_build_casing_frame_upgrades_every_known_residual_token`
   — expects `changed_count == 7`, gets `6`. The `('FX', 'spot')` row does not get upgraded to `SPOT_PAIR` alongside the
   `('FX', 'spot_pair')` row (both show up in `examples` with the SAME target `SPOT_PAIR`, but only one increments
   `changed_count`).
2. `tests/unit/test_venue_fetch_cefi_manifest_canonicalization.py:: TestTradfiRecordVenueShardCountsCanonicalization:: test_cme_combo_shard_itype_now_canonicalizes_uppercase`
   — expects `shard_key[3] == "COMBO"`, gets `"combo"` (lowercase passthrough, not canonicalized).

Confirmed NOT caused by my own concurrent change
(`fix(pipeline-e2e-check): route _captured_days_by_cell through the new streamed reader`, unrelated file):
byte-identical failure on the commit BEFORE mine, and still present after `git pull --rebase` pulled in several newer
commits.

Several very recent commits on this exact area suggest an in-flight migration:
`65dc99a5 fix(mtds): bridge CME/TradFi root-parent-symbol atom-format mismatch in preflight skip`,
`6fa0dd9d fix(tradfi): update stale combo lowercase-passthrough tests to match new UTL canon`,
`fbc9cc6f fix(tradfi): correct migration-script combo target-path remap + implement instrument_id-blank design for chain-bundle rows`,
`b13e3a2b fix(tradfi): combo_chain reader routing + split 2 files past the 900-line SRP cap`,
`5f037099 test(mtds): update tradfi manifest itype casing tests for 2026-08-10 revert`.

## Why it matters

`quality-gates.sh` is red on `live-defi-rollout` for `market-tick-data-service` — every agent trying to ship ANY change
through this repo (not just tradfi-related work) is blocked until this clears, per the green-tree-before-commit HARD
RULE.

## Recommended decision

Given the density of very recent same-area commits, this reads as an in-flight multi-commit migration transiently red
between steps rather than a settled regression — likely self-resolves once whoever is driving it lands their next
commit. If it's still red after a reasonable window, whoever picks this up should: (1) for test 1, check why the
`('FX', 'spot')` -> `SPOT_PAIR` row isn't counted in `changed_count` even though it appears in `examples` with the
correct target (look for an off-by-one in the counting vs the actual DataFrame mutation); (2) for test 2, find where the
CME combo shard's `instrument_type` should be uppercased before it's used to build `shard_key` (likely a
canonicalization call missing on one specific code path, given `6fa0dd9d`'s commit message says tests were already
updated to expect the new uppercase UTL canon — implying the PRODUCER side hasn't caught up yet).

## Open work (tracked todos)

- [ ] [BACKEND] P1. Root-cause + fix `test_build_casing_frame_upgrades_every_known_residual_token` (changed_count 6 vs
      expected 7 — the `('FX', 'spot')` row's casing upgrade isn't being counted) and
      `test_cme_combo_shard_itype_now_canonicalizes_uppercase` (CME combo shard's `instrument_type` stays lowercase
      `"combo"` instead of being canonicalized to `"COMBO"` before `shard_key` is built). Verify
      `bash scripts/quality-gates.sh` fully green afterward. (repo: market-tick-data-service)
