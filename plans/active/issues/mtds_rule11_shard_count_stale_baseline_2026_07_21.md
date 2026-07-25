---
doc_type: issue
title: >-
  MTDS test_rule11_per_ag_shard_counts_byte_unchanged has a stale CEFI shard-count baseline (200), blocking the full
  quality-gates.sh for every MTDS change right now
summary: >-
  tests/unit/test_pipeline_e2e_prediction_canonical.py::test_rule11_per_ag_shard_counts_byte_unchanged asserts an exact
  CEFI shard count of 200 and now measures 208 — an 8-shard delta that exactly matches the already-known
  OKX-FUTURES/OKX-SWAP cefi venue registration landed earlier this session (previously documented as "8 live cells the
  matrix had never enumerated"). Reproduced against a clean HEAD (isolated from all other uncommitted peer WIP in the
  shared working tree), so this is a genuine, unrelated, pre-existing test-baseline drift — not caused by any in-flight
  change. It currently fails `bash scripts/quality-gates.sh` for EVERY MTDS change, blocking unrelated ships.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [test-baseline-drift, quality-gates-blocker, cefi, shard-count]
related: []
created: "2026-07-21"
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
    "hit while shipping an unrelated LST rate honest-coverage Phase 1 change 2026-07-21; blocked the full-tree
    quality-gates.sh for every MTDS commit",
  ]
resolved_by: market-tick-data-service@56d39325
locked_by:
---

# MTDS rule11 shard-count baseline is stale (200 → measured 208)

## Reproduction

```
.venv/bin/pytest tests/unit/test_pipeline_e2e_prediction_canonical.py::test_rule11_per_ag_shard_counts_byte_unchanged -v
```

`AssertionError: CEFI shard count drifted: 208 != 200`

**Verified NOT caused by any in-flight change**: reproduced against a clean HEAD with all uncommitted peer WIP in the
shared working tree isolated away via a scoped `git stash`. The failure is present on the committed tree as-is.

## Likely root cause

The +8 delta matches the OKX-FUTURES/OKX-SWAP CeFi venue registration already landed earlier this session (previously
documented in this session's history as "8 live cells the matrix had never enumerated" — `OKX-FUTURES`/`OKX-SWAP` absent
from `VENUES_BY_ASSET_GROUP['cefi']` until that fix). The MVP-scope enumeration this test snapshots now correctly
includes those venues; the test's hardcoded expected count (200) was never updated to match.

## Impact

This is a hard-gate blocker in `quality-gates.sh` for **every** MTDS commit right now, regardless of what the commit
actually touches — any unrelated change (e.g. an oracle feed-map addition) fails the full gate on this unrelated
assertion.

## Fix

Update the hardcoded expected count in `test_rule11_per_ag_shard_counts_byte_unchanged` from 200 to 208 (verify the 208
enumeration is itself correct — i.e. no OTHER accidental venue/data_type inflation beyond the known OKX-FUTURES/OKX-SWAP
add — before just bumping the number). If the test's intent is "byte-unchanged unless intentionally changed", consider
whether it should snapshot the enumerated set (not just a count) so future additions fail with a clear diff instead of a
bare count mismatch.

## RESOLVED (2026-07-25)

Frontmatter flipped per the cefi orphan-audit (2026-07-25). Verified directly in market-tick-data-service:
`test_pipeline_e2e_prediction_canonical.py` line 264 pins CEFI=208 (was 200); `git blame` shows commit `56d39325`
(2026-07-21) "re-pin RULE-11 CEFI shard count for uac@11adf279" exactly matching this doc's described root cause/fix;
re-ran the named test — PASSED. Also corroborated by other docs referencing this as already resolved.
