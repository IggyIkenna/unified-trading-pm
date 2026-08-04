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
priority: P1
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

> **🔴 REPO-WIDE BLOCKER (bumped P3→P1 by main agt-1756f6, 2026-08-04, from slot-5 BLK-4c3b8444)**: this deterministic
> (100%-reproducible) failure now blocks a green `quality-gates.sh` Pass-1 for the ENTIRE market-data-processing-service
> tree — NO MDPS commit can ship until it lands (confirmed: slot-5's verified-correct adapter-registration commit is
> stuck on it, and its task is parked pending this fix). Prioritised urgent; land it to unblock all MDPS shipping.

- [x] ✅ [SCRIPT] P1. Root-cause why cloud provider `"local"` reaches `as_cloud()` in
      `test_instruments_domain_separation`'s environment and fix the env resolution —
      market-data-processing-service@3a69c6d. **Real root cause (neither of the two candidates guessed above):
      `tests/unit/test_unified_deps_functional.py` had a MODULE-LEVEL `os.environ.setdefault("CLOUD_PROVIDER", "local")`
      (line 28, executed at pytest collection time, before any test runs). MDPS's `get_service_config()` is a
      process-wide singleton — whichever test first calls it locks in `cloud_provider` for the rest of the pytest
      session. Every actual config-instantiation site in that file already scoped its own env correctly via a per-test
      `@patch.dict(os.environ, {...})` decorator, so the module-level `setdefault` was dead weight that did nothing for
      that file's own tests and only leaked `CLOUD_PROVIDER=local` process-wide for whichever test ran later —
      reproduced 1:1 by running that file + the integration test together (fails), vs the integration test alone
      (passes). Fix: deleted the module-level `setdefault` lines. Confirmed deterministic-repro before,
      deterministic-pass after (37 passed/1 skipped together, unrelated pre-existing GCS skip). Also applied fix
      candidate (a) from this todo as defense-in-depth: widened `tests/conftest.py`'s autouse
      `_skip_integration_without_creds` fixture to additionally check `config.cloud_provider in ('gcp','aws')`, not just
      credential-presence — verified live with `CLOUD_PROVIDER=local` env override: test now SKIPS (not fails) instead
      of hard-erroring. Both acceptance-criteria halves verified: real `gcp` config → PASSES; mock/local config → SKIPS.
      Evidence: `bash scripts/quality-gates.sh` green (sentinel
      `.qg_last_passed_sha=3a69c6d3dda7f2484a56d3e85eece33623ac0df1` == HEAD), shipped via quickmerge, verified on
      `origin/live-defi-rollout`.

## Progress Log

- **2026-08-04 (slot 6)** — Filed while archiving `mdps_shard_combinatorics_mock_seed_dependency_flaky_2026_08_04.md`
  (all 3 of its own todos done) per the archival ritual's step 1 — this finding was described in that doc's "What I
  found" item 4 but never given its own todo, a prose-deferral gap. Migrated here untouched (not investigated further
  this session).
- **2026-08-04 (slot-5, backend_engineer)** — hit this same failure live while trying to land a green Pass-1 for an
  unrelated diff (still blocked on it — `prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` todo 4).
  Tried the obvious same-pattern fix (skip on `BucketNamingError`, mirroring the sibling
  `test_get_instruments_from_gcs`'s `None`-tolerance) — reverted after it tripped the zero-test-silent-pass guard (both
  tests in the file skip on this host). Recorded the rejected approach + real root cause (autouse fixture checks
  creds-presence, not cloud-provider-shape) above so the next attempt doesn't re-walk the same dead end.
- **2026-08-04 (slot 3, data_engineering)** — Root-caused for real: not a fixture-narrowness problem at all, but a
  `tests/unit/test_unified_deps_functional.py` module-level `os.environ.setdefault("CLOUD_PROVIDER", "local")`
  (collection-time, unscoped) leaking into MDPS's process-wide `get_service_config()` singleton for the rest of the
  pytest session — reproduced the exact failure by running that file + the integration test together, confirmed clean
  pass running the integration test alone. Removed the dead module-level `setdefault` (every real usage in that file
  already scopes its own env via `@patch.dict`) and, as defense-in-depth on top of the removed leak, also widened
  `tests/conftest.py`'s autouse `_skip_integration_without_creds` fixture per this todo's candidate (a) to check
  `config.cloud_provider in ('gcp','aws')`. Both acceptance-criteria halves verified live (real gcp config → passes;
  `CLOUD_PROVIDER=local` override → skips, not fails). Shipped market-data-processing-service@3a69c6d,
  `quality-gates.sh` green, verified on origin. Todo done — repo-wide MDPS shipping blocker cleared.
