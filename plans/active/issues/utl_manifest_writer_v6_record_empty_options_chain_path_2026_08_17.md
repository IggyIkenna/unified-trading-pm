---
doc_type: issue
title: UTL manifest_writer record_empty() drops underlying/quote/margin segments for cefi options_chain — pre-existing QG red
summary: >-
  `ManifestWriter.record_empty()` for a `(cefi, options_chain)` row raises `NonCanonicalWritePathError` because the
  candidate write path it resolves omits the `underlying=/quote=/margin=` v6 tail segments even though the caller's
  `row_key` carries them (`underlying`, `quote_asset`, `margin_type` all present). Confirmed pre-existing and unrelated
  to the `defi_satellite_ao_dispatch_batch16` Solana source-label fix in flight on slot-6 — reproduced byte-identical
  with that diff stashed out.
status: open
nature: issue
asset_group: [meta]
stage: [data]
repos: [unified-trading-library]
scope: [engineer]
tags: [qg-red, manifest-writer, v6, options-chain, pre-existing]
related: []
created: "2026-08-17"
author: slot-6 (data_engineering)
source:
  - defi_satellite_ao_dispatch_batch16_2026_08_17.md (todo 1 — discovered while running Pass-1 QG for an unrelated fix)
assigned_vm: planning
parent_epic: cefi_master
resolved_by:
locked_by:
priority: P1
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# UTL manifest_writer record_empty() drops underlying/quote/margin segments for cefi options_chain

## What I found

`tests/unit/test_manifest_writer_v6.py::TestManifestWriterRecordEmptyV6::test_record_empty_with_v6_key` FAILS on a
clean `unified-trading-library` tree (verified via `git stash` of an unrelated in-flight diff + re-run — byte-identical
failure with and without that diff, so this is genuinely pre-existing, not caused by any in-flight change):

```
unified_trading_library.manifest_writer._schema.NonCanonicalWritePathError: Non-canonical GCS write path for
service='market-tick-data-service' row_key={'date': '2026-04-23', 'venue': 'DERIBIT', 'instrument_type': 'option',
'data_type': 'options_chain', 'underlying': 'BTC', 'quote_asset': 'USD', 'margin_type': 'inverse'}: 'raw_tick_data/
by_date/day=2026-04-23/pipeline_mode=batch_databento/asset_group=cefi/venue=DERIBIT/instrument_type=option/
data_type=options_chain/_.parquet' :: cefi options_chain shard must end '.../underlying=<BASE>/quote=<Q>/margin=<M>/
ticks.parquet' (got tail ['venue=DERIBIT', 'instrument_type=option', 'data_type=options_chain', '_.parquet']) — v5 bare
chain tail is a lossy USD-vs-USDT / linear-vs-inverse collision, RULED v6-only everywhere (operator 2026-07-21)
```

The test's `row_key` DOES carry `underlying`/`quote_asset`/`margin_type` — so this is not a stale-test-fixture gap. The
candidate path `_resolve_candidate_write_path` (`unified_trading_library/manifest_writer/_rows.py`) builds for
`record_empty()` on this row_key omits those three segments from the tail entirely (`.../data_type=options_chain/
_.parquet` instead of `.../data_type=options_chain/underlying=BTC/quote=USD/margin=inverse/_.parquet`), then the v6
canonical-path check (correctly) rejects its own under-specified output. Looks like `record_empty()`'s path-building
leg doesn't thread the row_key's `underlying`/`quote_asset`/`margin_type` fields through the same way `record_captured`
presumably does — not investigated further (out of scope for the fix I was mid-task on).

## Why it matters

`quality-gates.sh` on a clean `unified-trading-library` tree is RED on this one test (`1 failed, 7120 passed` as of
2026-08-17). Any worker needing a green Pass-1 QG on this repo hits this — including this session, which had an
unrelated, verified-clean Solana pipeline_mode fix ready to ship and had to pause on it.

## Recommended decision

Fix `_resolve_candidate_write_path` (or wherever `record_empty()` diverges from `record_captured()`'s options_chain
path-building) to thread `underlying`/`quote_asset`/`margin_type` from `row_key` into the v6 tail for the empty-write
candidate path, the same way the captured-write path already does. Re-run
`tests/unit/test_manifest_writer_v6.py::TestManifestWriterRecordEmptyV6::test_record_empty_with_v6_key` to confirm
green, then full `quality-gates.sh`.

## Todos

- [ ] [BACKEND] P1. Fix `record_empty()`'s candidate write-path builder in
      `unified-trading-library/unified_trading_library/manifest_writer/_rows.py` (`_resolve_candidate_write_path` or its
      caller) so a `(cefi, options_chain)` empty-row write threads `underlying`/`quote_asset`/`margin_type` from
      `row_key` into the v6 tail exactly as `record_captured()` does. Repo: unified-trading-library. Done when:
      `tests/unit/test_manifest_writer_v6.py::TestManifestWriterRecordEmptyV6::test_record_empty_with_v6_key` passes and
      full `quality-gates.sh` is green on a clean tree.

## Progress Log

_Filed 2026-08-17 by slot-6 (data_engineering), discovered running Pass-1 QG for
`defi_satellite_ao_dispatch_batch16_2026_08_17.md` todo 1 (unrelated Solana pipeline_mode fix)._

### Root cause narrowed + false-positive repo-blocker resolution — 2026-08-17 (slot-6)

Narrowed the root cause: `_resolve_candidate_write_path` (`unified_trading_library/manifest_writer/_rows.py:55`) takes
NO `underlying`/`quote_asset`/`margin_type` parameters at all — its only per-instrument lever is `instrument_id`
(used solely to build `file_name`). The failing test's write is an EMPTY-cell record (no instrument captured), so
whatever `record_empty()`'s caller passes as `instrument_id` is empty/`"_"`, and `candidate_parquet_paths()` has no
other channel to emit the v6 `underlying=/quote=/margin=` tail — the check then correctly rejects the under-specified
path it was itself given no way to build correctly. This is a genuine signature gap, not a simple field-threading typo,
and touches shared core `manifest_writer` write-path logic used fleet-wide — did NOT attempt a fix given the blast
radius and that it's fully out of scope for my dispatched todo.

Declared repo-blocker `RB-1484c950` (`kind=qg_red`) and got a `watcher_green` resolution message ~15 min later. Before
resuming, re-ran the exact failing test locally against the fresh-pulled `origin/live-defi-rollout` HEAD
(`df3703ab`, confirmed via `git log`) — **still fails, byte-identical to the original repro**. This is a FALSE-POSITIVE
resolution: the watcher's CI-green read did not reflect this repo's actual local-QG state at the HEAD it claims to
cover. Re-declaring the blocker below since the repo is not actually fixed. Flagging for whoever owns
`RepoHealthWatcher`/`ci_status()` staleness handling — this is the same failure CLASS as
`repo_blocker_resolution_signal_false_positive_2026_07_28` (supposedly fixed 2026-07-30), recurring here on
2026-08-17 for a different underlying defect.

### Re-confirmed still blocking — 2026-08-17 (interactive slot 27)

`quickmerge.sh`'s own re-gate hit the identical failure while shipping an unrelated `pipeline_e2e_check` fix
(`consolidate_bucket` param on `launch_vm_and_wait`, for `dp_vm_001_mdps_pipelinecheck_test_bucket_no_consolidator_coverage_2026_08_17.md`)
— confirmed pre-existing by stashing that diff and re-running just this test in isolation (fails byte-identical with
and without). Still `origin/live-defi-rollout@df3703ab` at time of this confirmation. Operator direction (asked
directly, interactive session): wait for AO to clear this rather than attempt the core `manifest_writer` fix myself —
the shipment stays parked locally (uncommitted, nothing lost) until this clears.
