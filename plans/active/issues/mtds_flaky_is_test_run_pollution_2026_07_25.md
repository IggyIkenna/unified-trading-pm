---
doc_type: issue
title:
  "market-tick-data-service — 2 tests flaky in full-suite/xdist run (pass in isolation), non-deterministic across
  identical trees"
summary: >-
  While shipping an unrelated comment-only cloudbuild.yaml fix
  (cloudbuild_yaml_unescaped_substitution_comments_fleet_wide_2026_07_25.md item -006), quickmerge's Pass-2 re-gate
  failed 3 consecutive times on
  `tests/unit/test_websocket_streaming_handler.py::TestResolveLiveBucketPrediction::test_prediction_stays_prod_without_is_test_run`
  and
  `tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware`.
  Both tests PASS in isolation (`pytest <both> -x` → 2 passed). A control run of the FULL quality-gates.sh suite on the
  byte-identical tree WITHOUT the cloudbuild.yaml diff (stashed) PASSED cleanly (6901 passed, 0 failed). The
  cloudbuild.yaml change is a YAML comment-only edit with zero Python surface, so it cannot be the cause either way —
  this is non-deterministic test-order pollution in the full xdist-parallel suite, most likely a shared/global
  `IS_TEST_RUN`-style flag leaking between tests depending on xdist worker assignment order.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [flaky-test, test-isolation, xdist, qg, market-tick-data-service]
related: [/plans/active/issues/cloudbuild_yaml_unescaped_substitution_comments_fleet_wide_2026_07_25.md]
created: 2026-07-25
parent_epic: infrastructure_master
priority: P2
source:
  "Found 2026-07-25 (slot 2, infra) while shipping cloudbuild_yaml_unescaped_substitution_comments_fleet_wide-006."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# market-tick-data-service — flaky IS_TEST_RUN-adjacent test pollution

## What I found

Shipping `market-tick-data-service/cloudbuild.yaml`'s comment-only fix (escaping bare `$BASE_IMAGE_DIGEST`/`$VERSION` at
lines 108, 309 — identical mechanical pattern to the other 14 repos in the parent fleet-wide issue doc), quickmerge's
Pass-2 re-gate ran `bash scripts/quality-gates.sh --no-fix` 3 times in a row and failed identically each time on:

- `tests/unit/test_websocket_streaming_handler.py::TestResolveLiveBucketPrediction::test_prediction_stays_prod_without_is_test_run`
- `tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware`

Both tests pass individually (`pytest <both files>::<both tests> -x` → `2 passed in 0.39s`). To rule out my own diff as
the cause, I stashed the cloudbuild.yaml change (reverting to `a1de76ac`, the tip I based on) and ran the FULL
`quality-gates.sh --no-fix` suite on that byte-identical clean tree: it PASSED cleanly
(`6901 passed, 17 skipped, 1 xpassed, 0 failed`). My change is a YAML comment edit inside `cloudbuild.yaml` with no
Python import surface, so it cannot cause or fix a Python test failure either way — the failure is **non-deterministic
across identical invocations of the same command on the same tree** (green once, red three times), which rules out both
"pre-existing red baseline" and "my change caused it" and points at real test-order/global-state pollution in the
xdist-parallel run.

Both failing tests' names strongly suggest a shared `is_test_run`/`IS_TEST_RUN`-style flag or bucket-resolution cache
that a different (unrelated) test sets and does not tear down, and whether that leaked state is visible to these two
tests depends on which xdist worker draws which test — i.e. it is an **assignment-order-dependent test isolation bug**,
not a logic bug in either test itself.

## Why this wasn't fixed inline

Root-causing a test-isolation/xdist-ordering bug (finding the exact global/module-level state that leaks, e.g. a
monkeypatched env var, singleton cache, or class attribute not reset in a fixture teardown) requires a focused bisection
across the ~6900-test suite and is out of scope for a P1 comment-escaping mechanical fix — different task, different
owner.

## Recommended fix

1. Bisect: run the full suite repeatedly with `-p no:randomly` / fixed `-n` worker count and capture which specific
   OTHER test(s), when run before the two failing ones on the same xdist worker, cause them to fail. `pytest --dist=no`
   (serial) forcing a specific ordering, or `pytest-randomly`'s seed replay, will surface the offending test faster than
   manual bisection.
2. Once the leaking global/state is identified, fix at the source: reset it in a fixture `finally`/teardown (autouse
   fixture scoped to the leaking state's owner module), not in the two victim tests.
3. Consider adding `pytest-randomly` (if not already active) with a FIXED seed in CI so a recurrence is reproducible
   instead of silently flaky.

## Todos

- [ ] [BACKEND] P2. Bisect and fix the test-order-dependent global-state leak causing
      `test_prediction_stays_prod_without_is_test_run` and
      `test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware` to fail non-deterministically in the full xdist
      suite while passing in isolation. Add/verify test-isolation (autouse teardown fixture) at the leaking state's
      source, not in the two victim tests. (repo: market-tick-data-service)

## Codex SSOTs

No existing SSOT covers xdist test-order-pollution debugging for this repo specifically — out of scope to author one
here; flagging as a possible follow-up if this recurs.
