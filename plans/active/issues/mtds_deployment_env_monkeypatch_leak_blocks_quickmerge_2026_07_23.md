---
doc_type: issue
title:
  "market-tick-data-service full quality-gates.sh (pytest -n 2) fails 2 unrelated bucket-resolution tests
  deterministically -- a DEPLOYMENT_ENV=dev monkeypatch from test_prediction_universe_prod_catalogue_gating.py's
  parametrized case appears to leak across tests within an xdist worker, blocking quickmerge for ANY unrelated change"
summary: >-
  While shipping an unrelated new one-off script (scripts/one_offs/delete_migrated_defi_markers_2026_07_23.py, zero
  overlap with the failing tests' code paths), `quickmerge.sh`'s quality-gates.sh --no-fix re-gate failed TWICE IN A ROW
  (consecutive, independent invocations) with the identical 2 failures:
  tests/unit/test_websocket_streaming_handler.py::TestResolveLiveBucketPrediction::test_prediction_stays_prod_without_is_test_run
  and
  tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware.
  Both PASS cleanly when run in isolation (a fresh, 2-test-only pytest invocation). The actual assertion failure
  (captured from the full-suite run's traceback) is `AssertionError: market-data-tick-pred-dev-test-project` where
  `market-data-tick-pred-prd-test-project` was expected -- i.e. `resolve_bucket_name`'s
  `os.environ.get("DEPLOYMENT_ENV")` fallback (bucket_naming.py:173, a live env read, not cached) resolved to `"dev"`
  instead of the expected unset/prod default. `tests/unit/test_prediction_universe_prod_catalogue_gating.py` is
  parametrized with `ambient_env=["test", "dev", None]` and uses `monkeypatch.setenv("DEPLOYMENT_ENV", ambient_env)`
  (line 69) for the `"dev"` case -- monkeypatch SHOULD auto-revert this at test teardown, but the observed symptom is
  consistent with that revert not happening (or a different in-process leak of the identical value) before
  `test_prediction_stays_prod_without_is_test_run` runs in the same xdist worker. Not root-caused to the exact mechanism
  (pytest-xdist worker-teardown edge case vs an async/asyncio-mode interaction -- this test file's surrounding warnings
  included multiple "coroutine was never awaited" RuntimeWarnings, which is at least circumstantially suggestive of
  async-fixture-teardown fragility, but this was NOT confirmed as the mechanism).
status: open
nature: issue
asset_group: [meta]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [ci, testing, pytest-xdist, flake, quickmerge-blocker, test-isolation, monkeypatch]
related:
  - plans/active/defi_consolidated_closeout_2026_07_18.md
created: 2026-07-23
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data-engineer
drift_direction: none
depends_on: []
locked_by:
locked_since:
source: >-
  Discovered 2026-07-23 attempting to quickmerge scripts/one_offs/delete_migrated_defi_markers_2026_07_23.py (an
  unrelated, isolated new file with zero import/call overlap with either failing test's code path) — see
  plans/active/defi_consolidated_closeout_2026_07_18.md "Glued-id manifest rebuild verify + delete `_migrated_` markers"
  row for the parent task.
resolved_by:
---

## What was observed (measured, not inferred)

Two consecutive, independent
`bash scripts/quickmerge.sh ... --files scripts/one_offs/delete_migrated_defi_markers_2026_07_23.py` invocations
(separated by several minutes, each running the FULL `pytest tests/unit/ ... -n 2 --cov=market_tick_data_service` suite
from a fresh process) both failed with the IDENTICAL 2 tests, at the identical ~94-95% position in the run:

```
FAILED tests/unit/test_websocket_streaming_handler.py::TestResolveLiveBucketPrediction::test_prediction_stays_prod_without_is_test_run
FAILED tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware
= 2 failed, 6833-6837 passed, 17 skipped, 1 xpassed, 7 warnings in ~97-132s =
```

Run #1 (2/2 failing) and Run #2 (2/2 failing, same 2 tests) both hit this — `quickmerge.sh` correctly identified this as
"❌ Re-gate FAILED against the current tree — this is a REAL failure, not a lost race" both times and refused to push.

Both failing tests pass cleanly in isolation:

```
$ .venv/bin/python -m pytest tests/unit/test_websocket_streaming_handler.py::TestResolveLiveBucketPrediction::test_prediction_stays_prod_without_is_test_run \
    tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware -q
2 passed in 0.33s
```

The actual assertion failure captured from the full-suite run:

```
tests/unit/test_websocket_streaming_handler.py:435: in test_prediction_stays_prod_without_is_test_run
    assert bucket == "market-data-tick-pred-prd-test-project", bucket
AssertionError: market-data-tick-pred-dev-test-project
```

`"prd"` (the expected default tier when `DEPLOYMENT_ENV` is unset) became `"dev"`.

## Root cause (partially traced, not fully confirmed)

`WebsocketStreamingHandler._resolve_live_bucket("prediction")` (websocket_streaming_handler.py:194) calls
`resolve_bucket_name(cloud="gcp", kind="market-data-tick-prediction", deployment_env=None)`.
`unified_trading_library.cloud_interface.bucket_naming._resolve_deployment_env_short` (bucket_naming.py:155-177)
resolves the tier via `deployment_env or os.environ.get("DEPLOYMENT_ENV") or ...` — this is a LIVE `os.environ` read
every call, NOT behind any `lru_cache` (verified directly in source; the only `@lru_cache` in that module is on
`_load_cloud_providers_yaml()`, an unrelated YAML-parse cache). So the test's failure requires the REAL process
`DEPLOYMENT_ENV` env var to actually be `"dev"` at the moment this specific test runs.

The only test found (repo-wide grep) that sets `DEPLOYMENT_ENV=dev` anywhere is
`tests/unit/test_prediction_universe_prod_catalogue_gating.py:69`
(`@pytest.mark.parametrize("ambient_env", ["test", "dev", None])`, `monkeypatch.setenv("DEPLOYMENT_ENV", ambient_env)`
for the `"dev"` case). `monkeypatch.setenv` is documented to auto-revert at test teardown, so under normal pytest
semantics this should NOT leak into a later test — but the observed symptom (the failing test seeing exactly `"dev"`,
the exact value that parametrized case sets) is circumstantially consistent with that revert not completing before the
next test in the same xdist worker runs. NOT confirmed further this session — a `bash -x`/pytest `--forked` or
`-p no:cacheprovider --dist=no` (single-process) A/B comparison would be the next diagnostic step, not attempted here
(out of scope for the session that found it).

## What is NOT claimed

- The EXACT mechanism (xdist worker-teardown ordering vs. an unrelated real env leak vs. something else) is not
  confirmed — only that (a) the failure is deterministic across 2 independent full-suite runs, (b) both tests are
  hermetic in isolation, and (c) the specific wrong value ("dev") matches a real parametrized case elsewhere in the
  suite that sets exactly that value via `monkeypatch.setenv`.
- Whether this affects OTHER tests beyond these 2 (any test relying on `DEPLOYMENT_ENV` being unset/prod-default under
  the full `-n 2` suite could plausibly be silently affected depending on xdist's dynamic test distribution across runs)
  was not swept.
- No fix was attempted this session — this is a test-infrastructure issue orthogonal to the DeFi migration/manifest work
  that surfaced it; fixing it belongs to whoever next needs a clean quickmerge in this repo, or a dedicated pass.

## Impact

Blocks `quickmerge.sh` for ANY change in market-tick-data-service whenever this ordering/leak triggers (non-obviously
timing/distribution-dependent under `pytest-xdist`'s default `--dist=load`). Confirmed to have blocked
`market-tick-data-service@952618d1` (the `_migrated_*` delete-tool one-off, itself unrelated and independently
ruff-clean + smoke-tested) from shipping via the sanctioned quickmerge path this session — that commit sits local,
unpushed, pending this issue's resolution or a lucky xdist re-distribution on a future retry.
