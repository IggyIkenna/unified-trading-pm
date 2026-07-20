---
doc_type: issue
title:
  "P1: MTDS quality gate is RED on LDR — rebuild_defi_manifest's honest-absence re-emit crashes FileNotFoundError on a
  missing availability_index (blocks every MTDS agent's commit/quickmerge)"
summary:
  reemit_defi_honest_absence_rows reads _index/availability_index.parquet unguarded, so it raises FileNotFoundError
  instead of treating a missing index as honest absence. The 3 tests in test_rebuild_defi_manifest_dry_run.py fail on a
  clean LDR checkout, so scripts/quality-gates.sh exits 1, never writes the .qg_last_passed_sha sentinel, and
  quickmerge's agent fast-path refuses — no agent can ship market-tick-data-service until this is green.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, blocked-shipping, honest-absence, manifest, defi-rebuild]
related: [defi_consolidated_closeout_2026_07_18, mtds_sentinels_qg_red_2026_07_13]
created: 2026-07-20
priority: P1
parent_epic: infrastructure_master
source: "Measured during the tradfi CME shard-atom / durability-guard work (slot-1, 2026-07-20)"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by:
---

# P1 — MTDS quality gate RED on LDR: `rebuild_defi_manifest` crashes on a missing availability index

## Discovery

Measured 2026-07-20 (slot-1) while gating unrelated TradFi test-only changes. Reproduced on a **clean LDR checkout with
zero local modifications** (changes stashed, verified apples-to-apples), so this is NOT caused by the work that found
it.

| tree                      | gate result               |
| ------------------------- | ------------------------- |
| clean LDR HEAD (baseline) | **4 failed**, 6516 passed |
| LDR HEAD after `e639c71f` | **3 failed**, 6523 passed |

`e639c71f` (another agent) fixed the 4th (`test_rule11_per_ag_shard_counts_byte_unchanged`, a stale 2403→2646 DeFi
shard-count baseline after `uac@3f79489f` added 9 DeFi venues). The remaining **3 are all one root cause**.

## Root cause

`market_tick_data_service/scripts/rebuild_defi_manifest.py:408` (`reemit_defi_honest_absence_rows`):

```python
raw_index = storage_client.download_bytes(bucket_name, "_index/availability_index.parquet")
```

The read is **unguarded**. When the index object does not exist the local-storage provider
(`unified_trading_library/cloud_interface/providers/local.py:146` → `Path.read_bytes()`) raises:

```
FileNotFoundError: [Errno 2] No such file or directory:
  .../local-storage/market-data-tick-defi-prd-test-project/_index/availability_index.parquet
```

This is a genuine robustness defect, not merely a test-fixture gap: **a missing availability index is honest absence**
(nothing captured yet) and must degrade to "no rows to re-emit", never crash the rebuild. A first-ever rebuild against a
fresh bucket hits exactly this path.

## Failing tests (all in `tests/unit/scripts/test_rebuild_defi_manifest_dry_run.py`)

- `test_dry_run_scans_credential_free_and_writes_nothing`
- `test_non_dry_run_instantiates_writer_and_adds`
- `test_migrated_marker_leaf_is_skipped_not_manifested`

## Impact — shipping is BLOCKED repo-wide

`scripts/quality-gates.sh` exits 1 → `base-service.sh` never writes `.qg_last_passed_sha` → `quickmerge.sh`'s agent
fast-path rejects with "Pass 1 quality-gates.sh sentinel invalid for current state". Because the commit is the per-repo
quality boundary (**commit only from a green tree**), _every_ agent with market-tick-data-service work is blocked,
regardless of whether their change touches DeFi. At least one such change is currently parked uncommitted on slot-1
(TradFi durability-guard tests, verified green in isolation).

## Ownership + fix direction

`rebuild_defi_manifest.py` is owned by **slot-4** (`35c87d66` 2026-07-19 "R3 rebuild skips `_migrated_*` markers",
`d3e38bfe` 2026-07-19), under `defi_consolidated_closeout_2026_07_18.md`. Filed rather than fixed here to avoid a
cross-agent collision on an actively-edited file.

Suggested fix (owner's call): guard the index read so a missing/absent object yields an empty frame — honest absence —
instead of propagating `FileNotFoundError`, and keep the 3 dry-run tests as the regression. The
`unified-trading-library` `read_availability_index` reader already models the absent-index case and is the natural shape
to mirror.
