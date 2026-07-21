---
doc_type: issue
title:
  "P3: LocalStorageProvider defaults to ONE shared {gettempdir()}/local-storage root — any test can leak persistent
  state that later fails an unrelated suite"
summary:
  local.py:91 defaults every LocalStorageProvider to the fixed path {gettempdir()}/local-storage, shared by every test
  in every suite and never torn down, so writes persist across runs and across families. A stray 6-day-old SPORTS per-VM
  manifest shard left in that root made _per_vm_shards_exist() true for a DeFi -test- bucket and fail-closed the whole
  MTDS quality gate (3 rebuild_defi_manifest dry-run tests), blocking every MTDS agent from committing. Production code
  was correct; the failure was purely leaked machine-local test state. Fix is per-test isolation (tmp_path) so a suite
  cannot observe another suite's objects.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, market-tick-data-service]
scope: [engineer]
tags: [test-isolation, quality-gates, flaky, local-storage, manifest, blocked-shipping]
related:
  [
    mtds_qg_red_rebuild_defi_manifest_missing_index_2026_07_20,
    manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14,
  ]
created: 2026-07-20
priority: P3
parent_epic: infrastructure_master
source: "Root-caused while landing the tradfi CME shard-atom + durability-guard work (slot-1, 2026-07-20)"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by:
---

# P3 — `LocalStorageProvider` shares ONE temp root across every test, so state leaks between unrelated suites

## The defect

`unified-trading-library/unified_trading_library/cloud_interface/providers/local.py:91`:

```python
self._base = Path(base_dir or f"{tempfile.gettempdir()}/local-storage")
```

The default root is a **single fixed path**, so it is:

- **shared** — every test, in every family and every repo, that constructs a provider without an explicit `base_dir`
  reads and writes the same tree;
- **persistent** — nothing tears it down between tests, between suites, or between runs, so artifacts survive for days;
- **invisible** — a test that never touches DeFi can leave a file that only ever fails a DeFi test, much later.

This makes cross-suite state leakage the default behaviour rather than an opt-in hazard.

## What it actually cost (measured 2026-07-20)

The MTDS quality gate was RED, blocking **every** market-tick-data-service agent from committing (the commit is the
per-repo quality boundary, and a red gate writes no `.qg_last_passed_sha`, so `quickmerge` refuses). Three tests in
`tests/unit/scripts/test_rebuild_defi_manifest_dry_run.py` failed.

The cause was one stray file in the shared root:

```
{gettempdir()}/local-storage/market-data-tick-defi-prd-test-project/
    _index/per_vm/sports-cf8-captured-available-at-backfill-2026-07-14.parquet
```

A **6-day-old artifact from an unrelated SPORTS backfill test**, sitting in a **DeFi** bucket, with no consolidated blob
beside it (`consolidated_age_sec = -1.0`). UTL's `read_availability_index` therefore saw "per-VM shards exist +
consolidated index missing" and **correctly** fail-closed with `ManifestConsolidatorStaleError`
(`_read_index.py:229-254` — the documented "loud-fails on stale index" contract).

**No production code was broken.** Removing the stray file turned the suite green (0 failed / 6529 passed).

## Why this is worth fixing rather than tolerating

The failure mode is maximally expensive to diagnose and maximally misleading:

1. It presents as a **code** bug in whichever suite happens to fail, not as leaked state.
2. The traceback's first frame (`FileNotFoundError`) points at an **already-handled** line; the real exception comes
   from the fallback underneath it. The obvious "fix" — catching the error in `rebuild_defi_manifest.py` — would have
   defeated a deliberate fail-closed AND re-introduced the CF-11 silent absence-corpus-drop bug (2026-06-11). That wrong
   fix was drafted, disproved against the real exception, and reverted.
3. It **does not reproduce** on a clean machine or in CI, so it reads as flake.
4. It blocks an entire repo's agents, not just the team that owns the leaking test.

It will recur: nothing prevents the next suite from leaving the next artifact.

## Suggested fix (owner's call)

Give each test its own root so cross-suite observation is impossible:

- **Preferred** — bind the provider to pytest's `tmp_path` per test (a fixture supplying `base_dir=tmp_path`), so
  isolation is structural rather than dependent on cleanup discipline.
- **Alternative** — an autouse fixture that points the default root at a per-test directory (e.g. via the existing
  `base_dir` parameter), keeping call sites unchanged.
- **Minimum** — a session-scoped fixture that clears `{gettempdir()}/local-storage` before the run. Weaker: it fixes
  cross-_run_ leakage but not cross-_test_ leakage within a run.

Regression: a test asserting that two providers built in different tests cannot see each other's objects.

## Non-goals

Do **not** address this by loosening `ManifestConsolidatorStaleError` or setting `MANIFEST_ALLOW_STALE_FALLBACK=true` in
the test env. The fail-closed is correct and load-bearing (it prevents an OOM-prone per-VM shard merge and the CF-11
corpus drop); the bug is that tests fabricate the condition that trips it.
