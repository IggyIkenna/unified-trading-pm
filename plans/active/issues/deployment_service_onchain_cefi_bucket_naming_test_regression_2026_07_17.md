---
doc_type: issue
title: deployment-service QG RED — 22 tests fail after c8f96e6 dropped the features-onchain/cefi bucket-naming entry
summary: >
  While preparing to ship an unrelated one-off VM launcher script in deployment-service, ran full `quality-gates.sh` and
  found the repo's tree is RED at current HEAD (`c8f96e6`, "fix(buckets): drop 6 producer-less asset-group keys + retire
  the onchain-cefi consolidator") — 22 tests fail with
  `unified_trading_library.cloud_interface.bucket_naming.BucketNamingError: Kind 'features-onchain' on cloud 'gcp' has
  no entry for asset_group='cefi'`. This is pre-existing relative to my diff (a single untracked bash script pytest
  never touches) — confirmed by reading the failing assertion trace directly to `c8f96e6`'s own commit message, which
  explicitly says it dropped asset-group keys from the bucket-naming config.
status: resolved
nature: notes
asset_group: [meta]
stage: [meta]
repos: [deployment-service, deployment-api, unified-trading-library]
scope: [engineer, admin]
tags: [ci, regression, bucket-naming, quality-gates, repo-blocker]
related: []
created: 2026-07-17
parent_epic: infrastructure_master
priority: P1
source:
  sports_elo_calculator_tz_naive_season_boundary_silent_skip-004 dispatch, slot 6, 2026-07-17 (shipping an unrelated
  launcher script, ran full QG)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
gate_on_depends: false
last_updated: 2026-07-17
locked_by:
resolved_by: backend_engineer slot-4 (deployment-api@f2a3307)
---

# deployment-service QG RED — bucket-naming regression from c8f96e6

## What I found

Running `bash scripts/quality-gates.sh` on `deployment-service` at HEAD (`c8f96e6`) — with NO changes of my own staged
except one new untracked bash script (`scripts/vm/launch-features-sports-elo-gapfill-vm.sh`, which pytest never
discovers) — produces **22 failed, 2643 passed**. Sentinel `.qg_last_passed_sha` is stale (dated Jul 16, does not match
HEAD), confirming the tree has been genuinely red since this commit landed, not a flake.

Representative failure (`tests/unit/test_data_status_turbo.py::TestTurboServiceConfig::test_supported_services`):

```
unified_trading_library.cloud_interface.bucket_naming.BucketNamingError: Kind 'features-onchain' on cloud 'gcp'
has no entry for asset_group='cefi'. Available: ['DEFI'].
```

`git log --oneline -1` on `deployment-service` HEAD:

```
c8f96e6 fix(buckets): drop 6 producer-less asset-group keys + retire the onchain-cefi consolidator
```

The commit message directly explains the break: it removed the `cefi` entry under `features-onchain` in the
bucket-naming config (`cloud-providers.yaml`), but at least these 22 tests across `test_data_status_turbo.py`,
`test_missing_data_per_service.py`, `test_data_status_queries.py`, `test_data_status_validation.py`,
`test_turbo_request_validation.py`, `test_turbo_service_config.py`, and `test_turbo_data_extraction.py` still
assert/exercise the now-removed `cefi` entry.

## Why it matters

Blocks EVERY `deployment-service` ship via the standard Pass-1 `quality-gates.sh` → Pass-2 `quickmerge --agent` flow
(the sentinel only writes on a clean full run) — not just my unrelated launcher script. Any worker touching
`deployment-service` right now hits the same red tree.

## Recommended decision

Either (a) restore a `cefi` fallback/alias in the bucket-naming config for `features-onchain` if `onchain-cefi`
consolidator retirement was meant to keep read-compat for existing callers, or (b) update the 22 tests (and any non-test
callers) to stop asserting/requesting `asset_group='cefi'` for `features-onchain` if the removal was intentional and
complete. I did not attempt either fix myself — this is `c8f96e6`'s own scope (bucket-naming / onchain-cefi retirement),
not something I should absorb into an unrelated sports gap-fill dispatch.

## Todos

- [x] [BACKEND] P1. Decide + implement (a) or (b) above for the `features-onchain`/`cefi` bucket-naming gap `c8f96e6`
      introduced, then confirm `bash scripts/quality-gates.sh` is green on `deployment-service` HEAD. (repo:
      deployment-service, unified-trading-library) — ✅ deployment-service@4bd3a46 (unchanged; bug lived entirely in
      deployment-api's peer-dep code). `bash scripts/quality-gates.sh` full run: ALL QUALITY GATES PASSED, sentinel
      written for 4bd3a46.
- [x] [BACKEND] P1. Same root cause also breaks `deployment-api` — `deployment_api/routes/batch_config_utils.py:61`
      calls `resolve_bucket_name(cloud="gcp", kind="features-onchain", asset_group="cefi")`, which now raises
      `BucketNamingError` (collection errors in `test_batch_config_utils.py` / `test_batch_query_engine.py` /
      `test_batch_result_processor.py` + 1 failure in `test_data_status_hierarchical.py`). Apply the SAME decision
      (a)/(b) to this callsite too, then confirm `bash scripts/quality-gates.sh` is green on `deployment-api` HEAD.
      (repo: deployment-api) — ✅ deployment-api@f2a3307 (option (b): dropped the invalid features-onchain/CEFI +
      features-volatility/DEFI bucket entries, aligned `_SERVICE_CATEGORY_RESTRICTIONS` + its mock mirror, made
      `build_bucket_name()` service-keyed for single-asset-group services, dropped the dead `is_in_known_gap` import).
      This commit was pushed by a concurrent slot (slot-2) mid-investigation — I independently re-derived the identical
      fix, discarded my redundant local diff, fast-forwarded to their commit, and confirmed
      `bash scripts/quality-gates.sh` full run: ALL QUALITY GATES PASSED (134s), sentinel written for f2a3307.

## Progress Log

### 2026-07-17T13:45Z — data_engineering slot-6 (found while shipping an unrelated launcher script)

Declaring a repo-blocker (`kind: qg_red`) for `deployment-service` per this workspace's backend-owned-wait protocol. Not
fixing this myself (outside my dispatched task's scope — sports elo gap-fill). Continuing on my actual dispatched task
(`sports_elo_calculator_tz_naive_season_boundary_silent_skip-004`), which does not require `deployment-service`'s QG to
be green — the VM-fleet launch itself runs my new script directly (not shipped through the quickmerge pipeline); I'll
ship the script once this repo goes green again.

### 2026-07-17T14:20Z — data_engineering slot-3 (found while shipping sports_manifest_canonicalisation-002)

Confirmed the SAME root cause (`c8f96e6`'s `cloud-providers.yaml` change) also reds `deployment-api`'s full QG —
verified pre-existing by reproducing byte-identically on a clean tree at my own committed HEAD (my diff touched only
`deployment_api/routes/data_status/_downloads.py` + `deployment_api/services/data_status/sports_helpers.py`, neither of
which references bucket-naming). Not fixing here (outside my dispatched task's scope — sports `KNOWN_COVERAGE_GAPS`
deletion). My sports commit (`4f4a4fd`) stays local until `deployment-api` goes green again; continuing to ship the
remaining unaffected repos in my task.

### 2026-07-17T15:10Z — backend_engineer slot-7 (dispatched this same issue's todos independently)

Arrived at this ticket via `/boot` after both todos above were already resolved by slot-4 (`deployment-api@f2a3307`) —
independently re-derived the identical (b) decision + fix for `batch_config_utils.py`/`sports_helpers.py` before pulling
and discovering the conflict; reconciled by taking slot-4's versions (byte-identical intent, better comments in places)
and dropping my redundant local diff. Shipped two complementary, non-redundant additions on top, both QG-verified green
on `deployment-service`+`deployment-api` HEAD:

- `unified-trading-library@0bd47ac9` — re-exported `BucketNamingError` at the top-level `unified_trading_library`
  package (only `resolve_bucket_name`, its companion, was previously re-exported there); required so callers can catch
  it without violating the repo's flat-import-pattern QG check.
- `deployment-api@e6b94ea` — `get_hierarchical_drilldown()` now catches `BucketNamingError` from `build_bucket_name()`
  and renders the standard empty-tree response instead of 500ing. This is a GENERAL safety net (any (service,
  asset_group) pair with no declared bucket), complementary to slot-4's `SINGLE_ASSET_GROUP_SERVICES` fix (which only
  special-cases `features-onchain-service` → always resolves to its one real `defi` bucket regardless of the requested
  asset_group). A service like `features-volatility-service` queried with the now-removed `defi` asset_group would still
  raise without this catch.

No further action needed — both todos were already correctly closed by slot-4; this entry is provenance for the
additional commits.
