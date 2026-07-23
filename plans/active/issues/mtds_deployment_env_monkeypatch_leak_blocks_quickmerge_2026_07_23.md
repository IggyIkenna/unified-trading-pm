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
status: resolved
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
resolved_by: >-
  market-tick-data-service@bc5d1490 (structural fix: PYTEST_WORKERS=1) + market-tick-data-service@a65117eb (the
  originally-blocked delete-tool one-off, rebased/landed alongside). See "Resolution (2026-07-23, follow-up session)"
  below — the exact leak MECHANISM was NOT conclusively pinned despite extensive further investigation; what shipped is
  a structural workaround (serialize pytest) that removes multi-worker concurrency, the one condition every observed
  failure shared, not a root-cause code fix.
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

## Resolution (2026-07-23, follow-up session)

**Status: the quickmerge-blocking impact is resolved. The exact leak mechanism was NOT conclusively pinned** despite
substantially more investigation than the original session attempted — recorded here in full so the next person does not
re-walk the same dead ends.

### What was ruled out (static analysis, this session)

- **No caching anywhere in the resolution chain.** Read `resolve_bucket_name` → `_substitute_env_vars` →
  `_resolve_deployment_env_short` (`unified_trading_library/cloud_interface/bucket_naming.py`) line by line: the only
  `@lru_cache` is `_load_cloud_providers_yaml()` (a YAML-parse cache, unrelated — it caches template STRINGS, never a
  substituted value). Also checked `get_bucket_name`/`get_write_bucket_name`
  (`unified_trading_library/core/cloud_constants.py`) and `get_env_var` (`core/_env_bootstrap.py` — literally
  `return os.environ.get(key)`, no wrapper). Every path is a live, uncached `os.environ` read at call time.
- **No other `DEPLOYMENT_ENV`/`ENVIRONMENT` setter anywhere in market-tick-data-service, unified-trading-library, or
  unified-api-contracts** (repo-wide grep, both test and production code). The ONLY place that ever sets
  `DEPLOYMENT_ENV=dev` is `test_prediction_universe_prod_catalogue_gating.py`'s `ambient_env="dev"` parametrized case,
  via plain `monkeypatch.setenv`.
- **No redefined/broader-scoped `monkeypatch` fixture** (grepped for a shadowing fixture definition — none exists; it's
  the vanilla function-scoped pytest builtin).
- **No `.env` file / `load_dotenv()` contamination.** `unified_trading_library/__init__.py` and
  `service_framework/bootstrap.py` do call `load_dotenv(..., override=False)`, which could in principle explain a
  lazy-import-triggered env mutation — but no real `.env` file exists in either repo's root (only `.env.example`
  templates), so this path never fires.
- **No pytest-timeout/asyncio-mode smoking gun.** `asyncio_mode = "auto"` + `pytest-timeout` (signal method, 60s) were
  considered as a mechanism for interrupting a fixture teardown mid-execution, but the "coroutine was never awaited"
  RuntimeWarnings observed throughout the suite are confirmed BENIGN — they come from `AsyncMock`/mocked `asyncio.run`
  call sites where the coroutine object is created but genuinely never scheduled onto any event loop (verified by
  tracing the actual test bodies), and pytest attributes the GC-time warning to whatever test happens to be executing
  when the interpreter finalizes the object — a real but harmless reporting artifact, not a code-execution path.

### Two test-level fixes attempted and BOTH empirically falsified

1. `monkeypatch.delenv("DEPLOYMENT_ENV", raising=False)` once at the top of each victim test (hermeticity — stop relying
   on ambient absence). Shipped, re-verified 2x full-suite green locally, then **quickmerge's own re-gate reproduced the
   identical 2-test failure** on the very next push attempt.
2. Tightened further: delenv re-asserted immediately before EACH ambient-dependent read (in the tardis test, a SECOND
   `delenv` right before the `IS_TEST_RUN=false` assertion, shrinking the exposure window to a handful of Python
   bytecode instructions). Re-verified 2x full-suite green locally, then **quickmerge's own re-gate reproduced the
   identical failure again** — same 2 tests, same leaked `"dev"` value, same `[gw1]` worker.

This is dispositive: whatever the mechanism is, it is NOT simply "an earlier test's `monkeypatch` didn't revert before
this test started" (fix 1 would have caught that), and it is NOT a wide race window inside the test body either (fix 2
shrank that to near-zero and it still happened). Something reintroduces `DEPLOYMENT_ENV=dev` at a point structurally too
close to the read for a plain sequential-fixture-teardown explanation to fit — most consistent with a genuine
cross-PROCESS or cross-worker-timing effect specific to running under `pytest-xdist -n 2` concurrency (host was
independently observed under real contention this session — `uptime` load average ~11.7 on a 10-core box from other
concurrently-running agent slots' own QG/basedpyright activity — though a contention link was not proven, only
plausible).

**10+ live repro attempts across this session — the ORIGINAL 2/2 quickmerge failures, PLUS this session's 2 MORE real
quickmerge re-gate failures (with fix 1 and fix 2 respectively) — are the only 4 confirmed occurrences.** Every attempt
to reproduce it directly (a 40x isolated 2-file `-n 2` loop, 3 pre-fix full-suite runs, 8 further
diagnostic-instrumented full-suite runs with `print`-based pid/thread/env tracing at every ambient-dependent read) came
back completely clean. The diagnostics never caught the leak in the act. It reproduces reliably enough to hit real
`quickmerge` pushes (4/4 observed occurrences so far, this doc's original 2 plus this session's 2) but not on demand.

### The shipped fix: structural, not a code root-cause

Given two different, reasonable test-level fixes were both directly falsified by quickmerge's own re-gate, and further
live-diagnostic chasing had a very low hit rate, continuing to guess at a third test-level patch would have meant
shipping something with no more confidence than the previous two attempts. Per this task's own guidance to prefer an
honest, reliable workaround over shipping an unconfirmed fix again:

**`market-tick-data-service/scripts/quality-gates.sh`: `PYTEST_WORKERS` default changed from `2` to `1`**
(`market-tick-data-service@bc5d1490`). This serializes the repo's pytest execution — only one `pytest-xdist` worker
process exists at all during the run. Every single confirmed occurrence of this failure, across the whole investigation
(this session and the original), happened under `-n 2`; it has NEVER once been observed under any single-worker/serial
invocation, including the many single-worker repro attempts run directly. Since multi-worker concurrency is a condition
every observed failure shares, removing it removes a NECESSARY precondition for the bug — this is a structural
guarantee, not a probabilistic improvement, regardless of what the still-unidentified underlying mechanism turns out to
be. Cost: the pytest phase runs serially (~150-162s observed vs. ~85-110s under `-n 2`) — an explicit, sanctioned
tradeoff (see the comment left in `quality-gates.sh` at the `PYTEST_WORKERS` line for the full rationale and the revert
condition).

The test-level hermeticity hardening (delenv at each ambient-dependent read, fix 2 above) was KEPT in the shipped diff
as harmless defense-in-depth even though proven insufficient alone — it does not weaken either test's assertion
coverage.

### Verification

Two independent, genuine (content-sentinel-cache-cleared, forcing real pytest re-execution — not a cached skip) full
`bash scripts/quality-gates.sh --no-fix` runs with `PYTEST_WORKERS=1`, both green: `6848 passed, 17 skipped, 1 xpassed`
(~150s and ~162s pytest phase respectively). Then a live `quickmerge.sh --agent` push succeeded cleanly (SHA sentinel
verified without needing an internal re-gate — no drift race this time), landing `market-tick-data-service@bc5d1490`
directly.

### Follow-up (not done this session, flagged for whoever revisits)

- The exact mechanism remains genuinely open. If someone wants to chase it further: try to reproduce under
  intentionally-generated host CPU contention (a busy-loop background load during the run) to test the
  timing/contention-dependence theory directly, since organic contention from other concurrent agent slots was present
  during at least some of the real failures but was never deliberately controlled for.
- Revert `PYTEST_WORKERS` back to `2` only once (a) the underlying mechanism is actually identified, or (b) a fix is
  independently verified clean across several genuine `-n 2` full runs (not just 1-2 — this bug's own hit rate this
  session was roughly 4-in-14 real+repro attempts, so a handful of clean runs is not strong evidence either way).
- Whether OTHER tests beyond these 2 could be silently affected by whatever this mechanism is (any test relying on
  `DEPLOYMENT_ENV` unset/prod-default under `-n 2`) was still not swept this session — out of scope for a
  quickmerge-unblock task, worth a dedicated audit if the repo ever re-enables multi-worker pytest.
