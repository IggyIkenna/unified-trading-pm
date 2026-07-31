---
doc_type: issue
title: market-tick-data-service QG pytest red — pre-existing, unrelated to tradfi manifest-shard test-only commit
summary: >-
  quality-gates.sh Pass-1 pytest reported 5 failures on a clean tradfi-only test-file commit (2690f5be,
  test_tradfi_manifest_shard.py additions only). Isolated re-runs show 3 are full-suite-order-dependent flake (pass
  standalone) and 2 are a real, reproducible, CeFi-only pipeline_e2e_check sampler bug — none touch
  tradfi/manifest-shard code.
status: open
nature: record
asset_group: tradfi
created: 2026-07-31
tags: [mtds, qg, pytest, flaky, cefi, pipeline_e2e, repo-blocker]
related: [tradfi_manifest_writer_legacy_id_regression_2026_07_21]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
drift_direction: fix-code
depends_on: []
source: >-
  tradfi_satellite_ao_dispatch_batch5_2026_07_29 todo 4, slot 3 data_engineering, 2026-07-31 — discovered while shipping
  a test-only commit unrelated to any of the 5 failing tests.
locked_by:
resolved_by:
---

# mtds QG pytest red — pre-existing, unrelated to the tradfi manifest-shard commit

## What I found

Shipping `market-tick-data-service@2690f5be` (test-only: 6 new regression tests in
`tests/unit/engine/test_tradfi_manifest_shard.py`, zero source changes), Pass-1 `quality-gates.sh` reported 5 pytest
failures against a repo tree that was otherwise clean (fetch/ff-only confirmed HEAD == origin before committing):

- `tests/unit/scripts/test_rebuild_defi_manifest_chunking.py::test_run_chunked_forces_reemit_absence_false_per_chunk`
- `tests/unit/test_lst_rates_handler.py::test_process_writes_canonical_partition_per_protocol_chain`
- `tests/unit/test_lst_rates_handler.py::test_evm_errors_fan_out_record_failed_to_all_evm_venues`
- `tests/unit/test_pipeline_e2e_sampler_prefers_captured.py::test_sampler_prefers_captured_over_empty_confirmed`
- `tests/unit/test_pipeline_e2e_sampler_prefers_captured.py::test_sampler_falls_back_to_genuine_when_no_captured`

None of these files reference `tradfi`, `manifest_shard`, or `_resolve_tradfi` (grepped directly). Re-ran all 5
together, isolated from the full 9763-test suite:

- The `test_rebuild_defi_manifest_chunking` + both `test_lst_rates_handler` tests **PASS** in this isolated run —
  full-suite-order-dependent flake (shared module/global state polluted by some other test earlier in the full run), not
  a real defect on this tree.
- Both `test_pipeline_e2e_sampler_prefers_captured` tests **FAIL consistently**, isolated or not:
  `_sample_raw_symbol_from_prod_listing` (CeFi BINANCE-FUTURES pipeline_e2e sampler) picks
  `BINANCE-FUTURES:PERPETUAL:ADA-USDT@LIN` when the test expects it to prefer the `captured` instrument (`BTC-USDT`)
  over an `empty_confirmed` one, and separately expects a `prod_manifest` sample-source label but gets
  `prod_parquet_listing`. This is a real, reproducible bug in the CeFi pipeline_e2e sampler's
  listing-order/source-preference logic — structurally unrelated to TradFi or the manifest-shard resolver (different
  asset_group, different module, no shared code path).

## Why it matters

Blocks the QG sentinel for ANY commit on this tree right now (Pass-1 must exit 0 to write `.qg_last_passed_sha`), even a
pure test-file addition to an unrelated module. Per `unified-trading-pm/agents/RULES.md` § 4b this is a repo-blocker,
not a defect in the blocked commit — filing + declaring per that procedure rather than chasing a fix inline (out of
scope for a tradfi manifest-shard todo).

## Recommended next step

1. Root-cause the full-suite ordering dependency for the 3 flaky tests (likely shared module-level/global state — e.g. a
   cache, registry singleton, or fixture leak — polluted by an earlier test in the 9763-test run). Not investigated
   further here (out of scope for the tradfi todo that surfaced it).
2. Fix the CeFi `pipeline_e2e_check.py` sampler's listing-order/source-preference logic so
   `test_sampler_prefers_captured_over_empty_confirmed` / `test_sampler_falls_back_to_genuine_when_no_captured` pass
   deterministically.

## Todos

- [ ] [SCRIPT] P2. Root-cause + fix the full-suite test-order dependency behind
      `test_rebuild_defi_manifest_chunking.py::test_run_chunked_forces_reemit_absence_false_per_chunk` and
      `test_lst_rates_handler.py`'s 2 failing tests only failing inside the full suite (pass in isolation) — most likely
      a shared module-level/global state leak from an earlier test. Repo: market-tick-data-service.
- [ ] [DATA] P2. Fix the CeFi `pipeline_e2e_check.py::_sample_raw_symbol_from_prod_listing` sampler so it
      deterministically prefers a `captured` instrument over `empty_confirmed` and reports the correct
      `prod_manifest`/`prod_parquet_listing` sample-source label, per `test_pipeline_e2e_sampler_prefers_captured.py`'s
      2 failing assertions. Repo: market-tick-data-service.

## Progress Log

- 2026-07-31 (slot 3, data_engineering): filed while shipping `market-tick-data-service@2690f5be` (tradfi manifest-shard
  regression tests, source: `tradfi_satellite_ao_dispatch_batch5_2026_07_29` todo 4). Declaring repo-blocker via
  `/api/repo-blockers` next; my own commit's tests (`tests/unit/engine/test_tradfi_manifest_shard.py`, 14/14) pass
  cleanly and are unaffected.
- 2026-07-31 (slot 4, cicd escalation `agt-a1ecae`, RB-6f0ca058): re-verified against `origin/live-defi-rollout` HEAD
  `17204fca` (2690f5be is not an ancestor/reachable ref in this clone — was local-only in slot 3's worktree at the time
  of the report). Ran the real `bash scripts/quality-gates.sh` Pass-1 end-to-end: **ALL QUALITY GATES PASSED (263s)**,
  `.qg_last_passed_sha=17204fca...` sentinel written — zero pytest failures. Additionally tried to reproduce the 2 "FAIL
  consistently, isolated or not" `test_pipeline_e2e_sampler_prefers_captured.py` assertions directly: PASS in isolation
  (both tests), PASS when run together with their sibling `test_pipeline_e2e_raw_symbol_sampler.py` (the file whose
  fixture data — `BINANCE-FUTURES:PERPETUAL:ADA-USDT@LIN` — matches the leaked value originally reported), and PASS when
  re-run alongside the other 3 originally-failing tests. The gate is GREEN on `live-defi-rollout` right now; resolving
  repo-blocker `RB-6f0ca058` accordingly so waiters (slot 3) resume immediately. Did reproduce ONE of the 3 flaky tests
  in that last combo run
  (`test_rebuild_defi_manifest_chunking.py::test_run_chunked_forces_reemit_absence_false_per_chunk` →
  `ManifestConsolidatorStaleError`, `consolidated_age_sec: -1.0`), confirming genuine order/fixture-timing dependency
  for that group — but it did NOT reproduce in the full quality-gates.sh run, so it isn't currently gate-blocking
  either. Leaving both P2 todos open as-is (real backlog, not currently blocking); not chasing the root cause further
  here — out of scope for a one-shot gate-unblock escalation.

- **2026-07-31 (slot 3, data_engineering) — SELF-CORRECTION: my original "2 fail consistently, isolated or not" claim
  above was itself an artifact of my own shell, not a genuine repo-wide QG red.** After the repo-blocker resolved, I
  re-ran `quality-gates.sh` on the rebased tree (HEAD `41391cba`, my test commit on top of the fix) and reproduced the
  SAME 5 failures TWICE in a row — contradicting slot 4's clean re-run. Root-caused the discrepancy: my Pass-1
  invocations had explicitly prefixed `GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp` (carried over from an
  earlier scratch investigation script in this same session that needed live GCS access for the tradfi manifest
  re-measurement). Re-ran `quality-gates.sh` with a genuinely clean environment (no manual env prefix) —
  **`All checks passed!`, sentinel written matching HEAD, 0 pytest failures** — confirming these explicit env vars (not
  ambient shell leakage; each Bash invocation in this harness is a fresh process) change enough runtime behavior
  (config-reloader / cloud-provider detection defaults, plausibly touching exactly the bucket/manifest-source-selection
  code the failing `pipeline_e2e_sampler`/`defi_manifest_chunking`/`lst_rates_handler` tests exercise) to flip these 5
  tests from passing to failing. **Correcting the record**: the "2 fail consistently" finding earlier in this doc was
  reproduced under this same contaminated environment and should be read as UNCONFIRMED against a clean shell — slot 4's
  clean re-run (0 failures) and my own clean re-run (0 failures) are the two data points that actually reflect real
  CI/gate behavior. Not deleting the 2 P2 todos above (a kernel of genuine order/timing flake was independently
  reproduced by slot 4 in one specific multi-file combo, `ManifestConsolidatorStaleError`) but downgrading confidence
  that either represents a standing, always-reproducible gate blocker. Shipped `market-tick-data-service@41391cba` (the
  tradfi manifest-shard regression tests this doc's parent todo needed) immediately after the clean confirmation —
  verified on origin. `status` stays `open` for the 2 real (if intermittent) flaky-test todos; this entry exists so a
  future reader doesn't re-chase a false "always fails" signal caused by an explicit env-var override, not the repo.
