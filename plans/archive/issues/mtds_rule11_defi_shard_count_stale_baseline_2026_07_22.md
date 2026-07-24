---
doc_type: issue
title: >-
  MTDS test_rule11_per_ag_shard_counts_byte_unchanged has a stale DEFI shard-count baseline (2673), measuring 2592,
  blocking quickmerge --agent's sentinel for every MTDS change right now
summary: >-
  tests/unit/test_pipeline_e2e_prediction_canonical.py::test_rule11_per_ag_shard_counts_byte_unchanged asserts an exact
  DEFI shard count of 2673 and now measures 2592 — a 81-shard delta, unrelated to any in-flight DERIBIT/CeFi change.
  Reproduced deterministically across two independent full `bash scripts/quality-gates.sh --no-fix` runs (~15 min apart)
  while attempting to ship an unrelated DERIBIT bare-venue combo classification fix (commit `dc2c92be`, files:
  `market_interface/adapters/tradfi/tardis_adapter.py`, `market_interface/adapters/cefi/tardis_shared.py`, a new test).
  Both an implementer agent and an independent verifier agent confirmed this failure is pre-existing and unrelated to
  that diff (docstring/scope says the test is "UAC-registry-driven only, never touches tardis_cefi_shards.py"). This is
  the SAME class of stale-baseline blocker already tracked for CEFI in
  `mtds_rule11_shard_count_stale_baseline_2026_07_21.md` (200→208) — a different asset_group/delta, so filed separately.
  Because `quickmerge.sh`'s Pass-1 SHA sentinel (`.qg_last_passed_sha`) and green content sentinel
  (`.qg_content_sentinel`) are ONLY written on a fully green `quality-gates.sh` run (see
  `unified-trading-pm/scripts/quality-gates-base/base-service.sh` ~line 3803), this failure blocks `quickmerge --agent`
  for ANY MTDS commit until fixed, not just the DERIBIT-combo fix that surfaced it.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [test-baseline-drift, quality-gates-blocker, defi, shard-count, quickmerge-sentinel]
related: [/plans/active/issues/mtds_rule11_shard_count_stale_baseline_2026_07_21.md]
created: "2026-07-22"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source:
  [
    "hit while shipping the deribit_combo_perpetual_partition_move_2026_07_21.md write-path classification fix (commit
    dc2c92be); blocked quickmerge --agent (no valid sentinel) for that unrelated ship",
  ]
resolved_by:
  unified-api-contracts@9a047a31 (root cause) + market-tick-data-service@0fcfa803 (the test-baseline fix itself)
locked_by:
---

# MTDS rule11 DEFI shard-count baseline is stale (2673 → measured 2592)

## Reproduction

```
.venv/bin/pytest tests/unit/test_pipeline_e2e_prediction_canonical.py::test_rule11_per_ag_shard_counts_byte_unchanged -v
```

`AssertionError: DEFI shard count drifted: 2592 != 2673`

Reproduced twice on `live-defi-rollout` HEAD (once at `dc2c92be`'s original parent, once again after quickmerge's
auto-pull rebased the same commit onto a newly-landed `feat(sports): K1` commit) — same 2592/2673 delta both times,
`1 failed, 6828 passed, 17 skipped, 1 xpassed` both runs. The one failure is isolated: `git diff --stat` on both
attempted-ship commits shows only `tardis_shared.py` / `tardis_adapter.py` / one new DERIBIT-combo test file touched —
nothing in the DEFI shard-enumeration path.

## Impact

Blocks `quickmerge.sh`'s STAGE 3 `--agent` fast-path for **every** MTDS commit right now: the SHA sentinel
(`.qg_last_passed_sha`) and content sentinel (`.qg_content_sentinel`) are written only on a run that prints "✅ ALL
QUALITY GATES PASSED" (no test failures at all), so a real-but-unrelated pytest failure prevents the sentinel from ever
refreshing, regardless of how many times `quality-gates.sh` is re-run. Non-`--agent` quickmerge would hit the same wall
at its own Phase 3 (`bash scripts/quality-gates.sh --no-fix --skip-lint ...` also exits 1 on any test failure).

## Fix

Likely a DEFI venue/data_type enumeration change (asset-group MVP-scope shrink, e.g. a venue deregistration or
consolidation) landed without updating this test's hardcoded expected DEFI count (2673 → 2592). Cross-check against
recent DEFI-scope commits (e.g. the `defi_lending_writer_retire_prerequisite_2026_07_20.md` / dex_pools+lending_indices
fold work referenced in CLAUDE.md as landing 2026-07-21) before just bumping the number — confirm 2592 is the _correct_
new count, not a further regression, then update the assertion (or better, snapshot the enumerated shard set so future
drift produces a diff instead of a bare count mismatch, per the same suggestion in the sibling CEFI issue).

## Status of the fix this was blocking

The DERIBIT bare-venue combo classification fix (`dc2c92be`) itself is fully implemented, independently verified
safe-to-ship, and committed locally on `live-defi-rollout` — it is NOT stuck for any reason related to its own code,
only blocked from `quickmerge --agent`'s sentinel gate by this unrelated pre-existing DEFI count drift.

## RESOLVED — 2026-07-22 ~19:50Z

Root cause confirmed: `unified-api-contracts@9a047a31` ("narrow METEORA/LIFINITY/PHOENIX-SOLANA back to phase=pipeline —
measured-dead upstreams, re-verified 2026-07-22") flipped 3 DEFI Solana DEX-pool venues from `phase="live"` to
`"pipeline"`, dropping `VENUES_BY_ASSET_GROUP["defi"]` from 99 to 96 entries; 3 venues × 27 data_types = 81 = exactly
the observed 2673→2592 delta. Confirmed a deliberate, twice-measured, documented consolidation (dead upstreams,
404/522/NXDOMAIN, re-verified against a Pyth-endpoint control to rule out sandbox egress issues) — not a regression. The
test-baseline fix itself landed independently via `market-tick-data-service@0fcfa803` (a concurrent sibling session
shipped the identical fix — same value, same root cause, same arithmetic — while this issue was still being
investigated; verified via `git merge-base --is-ancestor` and a direct diff comparison, not just trusting the sha). This
in turn unblocked the DERIBIT combo fix, which shipped separately at `market-tick-data-service@2ddc6d4a` after one more
follow-on round (a file/function-size-cap violation introduced by its own diff, fixed with a pure code-motion
extraction). No further action needed on this issue. </content>
