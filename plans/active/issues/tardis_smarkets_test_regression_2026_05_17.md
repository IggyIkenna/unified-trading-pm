---
title: "MTDS QG: 5 pre-existing test failures in market_interface (Tardis network + smarkets UAC registry)"
created: 2026-05-17
author: slot-3
source:
  - market-tick-data-service QG Phase 15.1 sweep
locked_by: live-defi-rollout
---

## What I found

5 test failures remain after fixing 2 Databento-related regressions (MTDS@139e2e6):

### Group A — Tardis canonical output (3 tests, network-blocked)

- `tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_download_batch_never_invokes_legacy_writer`
- `tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_download_batch_writer_kwarg_is_ignored_without_canonical_bucket`
- `tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_download_batch_returns_empty_df_and_populates_partition_writer`

Root cause: These tests make real network calls to `datasets.tardis.dev:443`. The `tests/market_interface/conftest.py`
adds a `--block-network` socket blocker via pytest-socket. When all tests are collected together (full QG with
`PYTEST_UNIT_DIR="tests/"`), the socket blocker activates for the whole suite, including these tests. Fix: Either add
`@pytest.mark.allow_network` to these tests, or replace the live network call with an `aioresponses`/`respx` mock
returning a 404 response.

### Group B — Tardis stream client (1 test, isolation issue)

- `tests/market_interface/unit/test_tardis_stream_client.py::TestAsyncIterBytes::test_raises_tardis_http_error_on_404`

Root cause: Passes when run standalone (`1 passed in 8.25s`). Fails in full suite due to test isolation — likely the
pytest-socket block from another test's fixture leaks into this test. Fix: ensure the test resets socket state or uses
`@pytest.mark.allow_network` to opt out.

### Group C — smarkets UAC registry (1 test)

- `tests/market_interface/integration/test_uac_venue_registry_adoption.py::TestUACBettingSportsVenuesImport::test_smarkets_in_manifest`

Root cause: `assert 'smarkets' in BETTING_SPORTS_VENUES` fails — `smarkets` is not in the UAC registry. The test was
written expecting `smarkets` to be added, but the UAC venue registry does not include it. This is either a test written
ahead of an unshipped UAC commit, or a regression from a UAC cleanup that removed `smarkets`. Fix: Either add `smarkets`
to UAC `BETTING_SPORTS_VENUES` registry, or remove the test if `smarkets` was intentionally de-scoped.

## Why it matters

MTDS Phase 15.1 (workspace QG sweep) requires 0 failures. These 5 failures block Phase 15 completion. They are all in
`tests/market_interface/` (excluded from slot-3 scope per CLAUDE.md "foreign files" rule). Slot-3 owner cannot fix these
without risk of unrecoverable overwrite on foreign files.

## Recommended decision

1. **Tardis tests**: Owner of `tests/market_interface/adapters/cefi/test_tardis_canonical_output.py` should add
   `@pytest.mark.allow_network` markers to the 3 failing tests + investigate the `test_raises_tardis_http_error_on_404`
   isolation issue.
2. **smarkets test**: Owner of UAC sports venue registry should add `smarkets` to `BETTING_SPORTS_VENUES` or remove the
   test if `smarkets` is de-scoped.

Until resolved, MTDS QG reports 5/3746+5 failures — these are pre-existing and not caused by Phase 3 work. MTDS@5f8448b
(Phase 3) and MTDS@139e2e6 (Databento test fix) introduce 0 new failures.
