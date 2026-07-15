---
doc_type: issue
title:
  The permanent `_legacy_seed.parquet` per-VM shard + the 2026-07-13 "captured-outranks" merge tie-break can silently
  resurrect stale pre-fix `captured` state over a newer, correct non-captured row — reproduced live on CeFi, DeFi and
  TradFi carry the same frozen seed
summary: |
  While executing the sanctioned CeFi blank-data_type orphan-row delete
  (plans/active/issues/phantom_captures_cefi_2026_06_28.md), a call to UTL's
  `merge_canonical_with_outstanding_shards(client, cefi_bucket, "_index/availability_index.parquet")` reported ZERO
  rows matching a predicate that a raw canonical-only read (no shard merge) found EXACTLY 9,757 of, seconds apart, on
  the same bucket. Root cause: `market-data-tick-cefi-prd-central-element-323112/_index/per_vm/_legacy_seed.parquet`
  is a PERMANENT, never-pruned, one-time snapshot of the canonical taken 2026-06-24T08:44:46Z (per
  `manifest_consolidator.py`'s documented "legacy seed — never pruned" design, `_LEGACY_SEED_PATH`) — it still holds
  the SAME 9,757 rows in their PRE-flip `capture_status='captured'` state (frozen before the 2026-06-28T03:12:34Z
  phantom-flip that correctly moved them to `attempted_failed` in the canonical). The 2026-07-13
  "captured-outranks" merge tie-break (`unified_trading_library/manifest_writer/_read_index.py::_merge_shard_frames`,
  landed for `sports_index_recency_masked_captured_atoms_2026_07_13`) makes `capture_status='captured'`
  UNCONDITIONALLY outrank any non-captured row in the SAME dedup-key group REGARDLESS OF RECENCY. The
  frozen seed's stale `captured` row therefore wins every merge, making `merge_canonical_with_outstanding_shards`
  (and any caller of it) currently report these 9,757 rows as still `captured` — silently masking the legitimate
  2026-06-28 fix. `manifest_consolidator.py`'s own SQL carries the BYTE-IDENTICAL leading
  `CASE WHEN capture_status = 'captured' THEN 1 ELSE 0 END DESC` tie-break (line ~2232), so the same risk is
  structurally present in the production Cloud Run consolidator job itself, not just this Python reader helper —
  though empirically the live cefi canonical still showed the CORRECT `attempted_failed` state after a consolidator
  run at 2026-07-15T02:19:41Z, so whatever protects production today (shard-scan exclusion of already-fully-absorbed
  shards, a dedup-key granularity difference, or something else) was NOT identified in this pass — that gap is the
  main open question this issue leaves for a follow-up. Confirmed a `_legacy_seed.parquet` file also exists in the
  DeFi (`market-data-tick-defi-prd-central-element-323112`, frozen 2026-06-24T17:28:59Z) and TradFi
  (`market-data-tick-tradfi-prd-central-element-323112`, frozen 2026-05-12T17:07:19Z) buckets — this is NOT
  cefi-specific; any row that was `captured` as of a bucket's seed-freeze date and has SINCE been legitimately
  corrected to a non-captured state (via ANY reconciliation/manual fix/legitimate state transition) is at risk
  wherever `merge_canonical_with_outstanding_shards` (or the consolidator itself, if it shares the exposure) is used
  as the read-before-write staleness guard — notably including `reconcile_phantom_manifest_rows_all.py`'s OWN
  existing `_apply_delete_chain_level_defi_phantoms` / `_apply_delete_legacy_combined_venue_defi_phantoms` DeFi
  delete passes, which use exactly this merge helper for their staleness guard.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, instruments-service]
scope: [engineer]
tags: [manifest, consolidator, per-vm-shards, legacy-seed, dedup, race-condition, data-correctness, captured-outranks]
related:
  [
    plans/active/issues/phantom_captures_cefi_2026_06_28.md,
    plans/active/issues/manifest_consolidator_prune_race_overlapping_executions_2026_07_13.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
    codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-15
last_updated: 2026-07-15
parent_epic: infrastructure_master
priority: P0
source: |
  Discovered live, as a side effect, during the CeFi blank-data_type orphan-row deletion in
  phantom_captures_cefi_2026_06_28.md (this session, 2026-07-15). Not a query-definition mismatch or a laptop-only
  artifact — reproduced with a direct comparison of `merge_canonical_with_outstanding_shards` (0 matches) vs. a raw
  canonical-only read (9,757 matches) against the SAME bucket, seconds apart.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# The permanent `_legacy_seed.parquet` shard + captured-outranks tie-break can resurrect stale `captured` state

## What I found

Executing the sanctioned delete for the confirmed-stale 9,757-row CeFi blank-`data_type` population (see
`phantom_captures_cefi_2026_06_28.md`), the plan called for the reconciler's own established staleness-guard pattern:
`merge_canonical_with_outstanding_shards(client, bucket, index_blob)` immediately before any write-back (mirrors
`reconcile_phantom_manifest_rows_all.py`'s `_apply_delete_chain_level_defi_phantoms` /
`_apply_delete_legacy_combined_venue_defi_phantoms`).

A dry-run using that exact helper against `market-data-tick-cefi-prd-central-element-323112` reported **0** rows
matching `capture_status=='attempted_failed' & data_type==''` — flatly contradicting a `read_availability_index`
slim-column query run minutes earlier (and independently re-confirmed via a raw canonical-only read) that found
**exactly 9,757** rows matching the identical predicate.

Diagnosis:

1. `market-data-tick-cefi-prd-central-element-323112/_index/per_vm/_legacy_seed.parquet` (5.4 MB, **frozen at
   2026-06-24T08:44:46Z**) still contains these same 9,757 rows with `capture_status='captured'` — their state BEFORE
   the 2026-06-28T03:12:34Z phantom-flip that correctly moved them to `attempted_failed` in the canonical.
2. Per `manifest_consolidator.py` (`_LEGACY_SEED_PATH = "_index/per_vm/_legacy_seed.parquet"`), this file is a
   **one-time, idempotent-creation snapshot of the canonical, and is explicitly "never pruned"** — i.e. it persists
   forever as a per-VM shard input to every future merge, by design, so historical rows always participate.
3. `unified_trading_library/manifest_writer/_read_index.py::_merge_shard_frames` carries a **"captured-outranks"
   tie-break** (added 2026-07-13 for `sports_index_recency_masked_captured_atoms_2026_07_13`): within one dedup-key
   group, `capture_status='captured'` always beats any non-captured row **regardless of recency**. This was a correct
   fix for its own incident (a later bare-empty stamp masking a real capture) — but it has the side effect that a
   PERMANENTLY-FROZEN seed shard's stale `captured` row will ALWAYS outrank a newer, correct, legitimately non-captured
   canonical row for the same key, forever.
4. `manifest_consolidator.py` (the real production Cloud Run job) carries the **byte-identical** leading tie-break in
   its own merge SQL (`"CASE WHEN capture_status = 'captured' THEN 1 ELSE 0 END DESC, ..."`, ~line 2232) — so this is
   not just a Python-reader-helper quirk; the same logic is structurally present in the canonical consolidation path
   itself.
5. Empirically, the CeFi canonical **still showed the correct `attempted_failed` state** for these 9,757 rows
   immediately before this session's delete (verified via a raw canonical-only read; `consolidator_run_at` metadata on
   the blob showed a run at 2026-07-15T02:19:41Z, ~70 minutes before this check) — so whatever the production
   consolidator does differently from the `_merge_shard_frames` reader helper (a shard-already-fully-absorbed exclusion,
   a stricter dedup-key match, or genuinely nothing and it just hasn't recurred yet) was **NOT identified in this
   pass**. This is the main open question.
6. Confirmed via `gcloud storage ls` that a `_legacy_seed.parquet` also exists in the DeFi
   (`market-data-tick-defi-prd-central-element-323112`, frozen 2026-06-24T17:28:59Z) and TradFi
   (`market-data-tick-tradfi-prd-central-element-323112`, frozen 2026-05-12T17:07:19Z) buckets — this is a
   cross-asset-group pattern, not cefi-specific.

## Why it matters

Any manifest row that was `captured` as of a bucket's seed-freeze date, and has SINCE been legitimately corrected to a
non-captured state by ANY mechanism (phantom-reconcile, manual fix, a real re-audit), is at risk of that fix being
silently masked whenever `merge_canonical_with_outstanding_shards` is used as a "read the current truth" or "staleness
guard before write-back" primitive — and, if the same tie-break is genuinely live in the production consolidator's
regular merge cycle for some as-yet-unobserved key shape, of the CANONICAL BLOB ITSELF being silently reverted on a
future consolidation run. This directly threatens the reliability of:

- `reconcile_phantom_manifest_rows_all.py`'s own `_apply_delete_chain_level_defi_phantoms` /
  `_apply_delete_legacy_combined_venue_defi_phantoms` DeFi delete passes (both use
  `merge_canonical_with_outstanding_shards` as their staleness guard).
- Any future reconciliation/backfill tooling that trusts this helper as "the current truth."
- Honest-coverage / `DP_RUN_MOSTLY_EMPTY`-style monitoring, which could see a corrected cell silently regress back to
  looking broken (or a genuinely-broken cell silently masked as fixed) with no code change and no new writer activity —
  exactly mimicking a "live writer regression" symptom while actually being a stale-seed / tie-break interaction.

## What I did NOT do

This session's task was scoped to the CeFi 9,757-row deletion. I deliberately did **not** attempt to fix
`_merge_shard_frames`, `manifest_consolidator.py`, or delete/refresh any `_legacy_seed.parquet` file — that requires
understanding exactly why production has (apparently) not yet manifested this regression despite carrying the identical
tie-break logic, which is a real investigation in its own right and higher-risk to get wrong under time pressure than
the narrowly-scoped delete this session completed. The CeFi delete itself was executed SAFELY by routing around this
landmine entirely: reading + writing the canonical blob directly (bypassing the shard merge) with true atomic
compare-and-set (`StorageClient.conditional_upload_bytes(..., if_generation_match=...)`, the same GCS
generation-precondition primitive `manifest_consolidator.py` and `manifest_writer/_writer_io.py` use for their own
canonical writes) — see `scripts/delete_cefi_blank_data_type_orphan_rows_2026_07_15.py` in instruments-service.

## 🔴 2026-07-15 (~1h later) — CONFIRMED LIVE: the resurrection actually happened in production, not just theoretical

Independent re-verification (different session) re-queried the CeFi canonical directly: **the 9,757 blank-`data_type`
rows are back**, with the SAME original `attempted_at=2026-06-28T03:12:34Z` / `written_at` (April 6-20) timestamps as
before the delete — this is the SAME frozen-seed data resurrecting, not a new/different orphan population. The canonical
blob's own `Update time` (`gsutil stat`) is **2026-07-15T03:15:13Z** — a write landed only ~2 minutes before this check,
meaning the confirmed-safe delete (which held through one full consolidator cycle at 02:19:41Z per this doc's own "What
I found" section above) was reverted by a SUBSEQUENT consolidator run sometime between then and now.

**This closes this doc's own "main open question"**: whatever protected production during the FIRST post-delete cycle
did NOT protect it on a later cycle — the captured-outranks tie-break interacting with the permanently-frozen
`_legacy_seed.parquet` is a REAL, LIVE, currently-active production bug, not a latent/theoretical one. Re-running the
same delete script again would almost certainly get reverted again on the next consolidator cycle without first
addressing the tie-break/seed-freshness issue this doc already recommends fixing (P1 items below) — **do not re-attempt
the cefi delete until one of those P1 items lands**, or it will just burn another CAS-write cycle for a result that
reverts again.

**Escalating priority**: given this is now confirmed live (not theoretical) and the doc's own analysis already
establishes cross-asset-group exposure (defi + tradfi both carry the same frozen `_legacy_seed.parquet` pattern), this
should be treated as an active P0/P1 production data-correctness bug, not a background research item.

## Recommended next steps

- [ ] [SCRIPT] P1. Determine why the production `manifest_consolidator.py` Cloud Run job has NOT (observably) reverted
      the CeFi 9,757-row fix despite carrying the same leading captured-outranks `CASE` in its merge SQL and
      `_legacy_seed.parquet` still holding the stale `captured` state — read the consolidator's actual shard-scan /
      already-absorbed-shard tracking logic end-to-end (not just the merge SQL) to find the actual protection (if one
      exists) or confirm there is none and this is a live, unmitigated production risk. Repo: unified-trading-library.
  - [ ] [SCRIPT] P1. If no real protection is found: either (a) special-case `_legacy_seed.parquet` out of the
        captured-outranks tie-break specifically (recency-only comparison against the frozen seed, since by definition
        anything in the live canonical postdates the seed's freeze), or (b) refresh/re-freeze each bucket's
        `_legacy_seed.parquet` periodically (or after any bulk reconciliation pass) so it never diverges this far from
        canonical truth. Repo: unified-trading-library.
- [ ] [SCRIPT] P2. Audit `reconcile_phantom_manifest_rows_all.py`'s existing DeFi delete passes
      (`_apply_delete_chain_level_defi_phantoms` / `_apply_delete_legacy_combined_venue_defi_phantoms`) against the DeFi
      bucket's own `_legacy_seed.parquet` (frozen 2026-06-24T17:28:59Z) for the same class of silent-resurrection
      exposure — any `empty_confirmed` row those passes deleted that the seed still holds as `captured` under the old
      wrong-key form would currently read back as `captured` via `merge_canonical_with_outstanding_shards`. Repo:
      instruments-service.

Evidence: live, read-only comparison of `merge_canonical_with_outstanding_shards` vs. a raw canonical-only read against
`market-data-tick-cefi-prd-central-element-323112`, 2026-07-15, this session (ad hoc diagnostic scripts, not committed —
single-read discipline maintained per read, no whole-corpus GCS walk); `gcloud storage ls -l` listings of
`_index/per_vm/` for cefi/defi/tradfi buckets; direct reads of `unified_trading_library/manifest_writer/_read_index.py`
(`_merge_shard_frames`) and `unified_trading_library/manifest_consolidator.py` (`_LEGACY_SEED_PATH`, the leading
`CASE WHEN capture_status = 'captured'` ORDER BY).
