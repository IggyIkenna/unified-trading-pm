---
doc_type: issue
title:
  "P1 (RESOLVED): MTDS quality gate RED — rebuild_defi_manifest dry-run tests fail from a STALE per-VM shard left in the
  SHARED local-storage temp dir, not from an unguarded index read"
summary:
  CORRECTED root cause. The 3 test_rebuild_defi_manifest_dry_run.py failures were NOT an unguarded index read. UTL
  read_availability_index fail-closes with ManifestConsolidatorStaleError whenever per-VM shards exist without a fresh
  consolidated _index; a stray shard from an unrelated 2026-07-14 SPORTS backfill test, left in the SHARED
  /tmp/local-storage bucket, made _per_vm_shards_exist() true so the guard fired correctly. Production code was right
  all along. Cleared by removing the stale artifact; slot-4 separately shipped mtds@2c88b269 (CF-11 row_key + PROJECTed
  _index read) fixing the related rebuild-VM OOM. Tests now 0 failed / 6529 passed.
status: resolved
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
resolved_by: mtds@2c88b269 + stale-local-storage-artifact removal
---

> **⚠️ ROOT CAUSE CORRECTED 2026-07-20 — read this before the original analysis below, which was WRONG.**
>
> The original diagnosis ("`reemit_defi_honest_absence_rows` reads the index unguarded → `FileNotFoundError`") was only
> the FIRST frame of the traceback. The `FileNotFoundError` **is** already caught (`:411`); what actually escaped was
> raised by the FALLBACK `read_availability_index(bucket_name)` at `:413`:
>
> ```
> ManifestConsolidatorStaleError: Consolidated availability_index for bucket=... is stale or missing
> (older than MANIFEST_CONSOLIDATED_STALENESS_SEC=120s) while per-VM shards exist — the manifest
> consolidator is behind or DOWN. Refusing to fall back to the per-VM shard merge (can OOM on large buckets).
> ```
>
> **That raise is CORRECT, deliberate fail-closed behaviour** (`_read_index.py:229-254`; codex: the manifest
> consolidator "loud-fails on stale index"). It fires when `shards_exist and not MANIFEST_ALLOW_STALE_FALLBACK`.
> `MANIFEST_FAIL_ON_STALE_FALLBACK` was unset, so the trigger was **`_per_vm_shards_exist() == True`**.
>
> **Why shards "existed" on a supposedly fresh test bucket**: the local-storage provider backs `-test-` buckets with a
> **SHARED, non-per-test** temp dir. It contained one stray leftover:
>
> ```
> /…/T/local-storage/market-data-tick-defi-prd-test-project/_index/per_vm/
>     sports-cf8-captured-available-at-backfill-2026-07-14.parquet
> ```
>
> — a 6-day-old artifact from an unrelated **SPORTS** backfill test, with **no** consolidated blob beside it
> (`consolidated_age_sec = -1.0`). So UTL saw "shards present + consolidated missing ⇒ consolidator DOWN" and correctly
> refused. **No production code was broken**; this never reproduces on a clean machine or in CI.
>
> **Do NOT "fix" this by catching `ManifestConsolidatorStaleError` in `rebuild_defi_manifest.py`** — that would defeat a
> deliberate loud-fail AND re-introduce the exact CF-11 bug this function exists to prevent (silently dropping the
> absence corpus, 2026-06-11). A guard was drafted, proven ineffective against the real exception, and **reverted**;
> slot-4's file is untouched.
>
> **Resolution**: stale artifact removed (quarantined, not deleted) → the 3 tests pass; slot-4 independently shipped
> `mtds@2c88b269` (CF-11 honest-absence `row_key` + PROJECTed `_index` read, fixing the OOM that wedged 3 rebuild VMs).
> Measured after: **0 failed / 6529 passed**.
>
> **Residual worth tracking (P3, not re-opened here)**: the local-storage test provider using a **shared** temp dir
> rather than a per-test path lets any test leak state that later fails an unrelated suite. That is the real, durable
> weakness this episode exposed.

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
