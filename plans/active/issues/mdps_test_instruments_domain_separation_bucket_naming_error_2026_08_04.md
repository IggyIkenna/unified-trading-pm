---
doc_type: issue
title: >-
  market-data-processing-service's test_instruments_domain_separation raises BucketNamingError on cloud provider "local"
summary: >-
  Deferred out of mdps_shard_combinatorics_mock_seed_dependency_flaky_2026_08_04.md (item 4 of "What I found", archived)
  — a genuinely separate, unrelated bug spotted while root-causing that doc's non-deterministic QG failures, never given
  its own todo. tests/integration/test_instrument_retrieval.py::test_instruments_domain_separation raises
  BucketNamingError: Unknown cloud provider 'local'; expected one of ('gcp', 'aws') — an env/config value of "local" is
  reaching as_cloud(), which only accepts gcp/aws.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [flaky-test, cloud-config, bucket-naming, test-infra]
related: [/plans/archive/issues/mdps_shard_combinatorics_mock_seed_dependency_flaky_2026_08_04.md]
created: "2026-08-04"
last_updated: "2026-08-04"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
source: >-
  Deferred from mdps_shard_combinatorics_mock_seed_dependency_flaky_2026_08_04.md's "What I found" item 4 (slot-5,
  backend_engineer, 2026-08-04) — migrated to its own tracked todo per the plan-completion-and-archival-discipline
  ritual's step 1 (never let a deferral evaporate with the archived plan) when that doc was archived (slot 6,
  2026-08-04).
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
    market-data-processing-service/tests/integration/test_instrument_retrieval.py,
    market-data-processing-service/market_data_processing_service/app/providers/cloud_data_provider.py,
  ]
---

# MDPS test_instruments_domain_separation: BucketNamingError on cloud provider "local" (2026-08-04)

## What I found

`tests/integration/test_instrument_retrieval.py::TestInstrumentRetrieval::test_instruments_domain_separation` raises:

```
BucketNamingError: Unknown cloud provider 'local'; expected one of ('gcp', 'aws')
```

`CloudDataProvider._get_instruments_bucket(category)` (called for each of CEFI/TRADFI/DEFI) resolves the bucket name via
`resolve_bucket_name(...)` → `as_cloud(...)`, which only accepts `gcp`/`aws`. Some env/config value of `"local"` is
reaching this call in the integration-test environment. Unrelated to the shard-combinatorics mock-seed marker fix or the
two stale-assertion fixes in the sibling doc — this is its own bug, deferred there without a todo.

## Why it matters

An integration test that cannot run at all (hard error, not a skip) is invisible signal loss — any real regression in
domain-separated bucket resolution for CEFI/TRADFI/DEFI instruments would not be caught until this is fixed.

## Recommended decision

Trace where the `"local"` provider value originates for this test's environment (a config default, an unset env var
`UnifiedCloudConfig` falls back to, or a test-fixture override) and either fix the env resolution so `gcp`/`aws` reaches
`as_cloud()` in this test context, or mark the test `skipif` with a clear reason if `"local"` is a genuinely
unsupported-in-this-context provider value that should never reach production code.

## Todos

- [ ] [SCRIPT] P3. Root-cause why cloud provider `"local"` reaches `as_cloud()` in
      `test_instruments_domain_separation`'s environment and fix the env resolution (or mark the test `skipif` with a
      stated reason if `"local"` is out of scope for this test context) (repo: market-data-processing-service).

## Progress Log

- **2026-08-04 (slot 6)** — Filed while archiving `mdps_shard_combinatorics_mock_seed_dependency_flaky_2026_08_04.md`
  (all 3 of its own todos done) per the archival ritual's step 1 — this finding was described in that doc's "What I
  found" item 4 but never given its own todo, a prose-deferral gap. Migrated here untouched (not investigated further
  this session).
