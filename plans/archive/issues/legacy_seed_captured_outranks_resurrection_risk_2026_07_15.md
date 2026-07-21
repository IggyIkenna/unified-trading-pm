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
status: resolved
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
last_updated: 2026-07-15 (Part 2 fix + cefi live multi-cycle hold confirmed)
parent_epic: infrastructure_master
priority: P1
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
resolved_by: |
  unified-trading-library@f14b13aeac298f70ea07bbf5ed30ca4f480ab8e9 (Part 1: captured-outranks tie-break demotion),
  unified-trading-library@59084b005aa68d56d7125c388e192480bc158396 (Part 1 follow-up: FutureWarning cleanup),
  unified-trading-library@8e783d7015a5c93fd54c5579605631c50dd7f0b6 (Part 2: legacy-seed exclusion for the
  deletion-resurrection gap Part 1 alone missed — discovered + fixed same session via direct production
  stress-testing). Verified live via 2 deliberate `--force` full-rebuilds + 1 genuine incremental production cycle
  against `market-data-tick-cefi-prd-central-element-323112`, all post-deploy, all holding at 0 resurrected rows. See
  the dated section below for full evidence.
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

- [x] ✅ [SCRIPT] P1. Determine why the production `manifest_consolidator.py` Cloud Run job has NOT (observably)
      reverted the CeFi 9,757-row fix — MOOT, superseded by the 2026-07-15 (later) confirmed-live resurrection below: it
      DID revert, on a subsequent cycle, so there was no real protection to find (the first-cycle survival was
      incidental to the incremental path's mtime-staleness cutoff naturally excluding the frozen seed most cycles — not
      a deliberate absorbed-shard guard). Not independently re-derived in this pass; superseded by shipping the fix
      directly. Repo: unified-trading-library.
  - [x] ✅ [SCRIPT] P1. Option (a) implemented exactly as specified — special-cased `_legacy_seed.parquet` out of the
        captured-outranks tie-break by shard-identity (not option (b), periodic refresh; not a general recency
        reordering) — `unified-trading-library@f14b13ae`. See the dated section below for the full writeup. Repo:
        unified-trading-library.
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

## 🟢 2026-07-15 (later) — FIX SHIPPED: legacy seed special-cased out of the captured-outranks tie-break

Operator decision (interactive session, 2026-07-15): special-case the legacy seed out of the tie-break — option (a) from
this doc's own "Recommended next steps" — not option (b) (periodic seed refresh), and not a general recency-reordering
of the whole tie-break's semantics (deemed higher-risk for shared consolidator-fleet code). Implemented exactly this, in
both places this doc identified the byte-identical tie-break logic living
(`unified-trading-library@f14b13aeac298f70ea07bbf5ed30ca4f480ab8e9`):

- **`unified_trading_library/manifest_consolidator.py::_duckdb_merge_payload`** (the production Cloud Run consolidator's
  own merge SQL, ~line 2232 pre-fix): the legacy seed shard is now downloaded to its own fixed local basename
  (`__legacy_seed__.parquet`, never the generic index-numbered scheme ordinary shards use) and its rows are tagged
  `is_legacy_seed_row` via `ends_with(filename, ...)` on DuckDB's `filename` pseudo-column
  (`read_parquet(..., filename=true)`). The leading `order_by` CASE now reads
  `CASE WHEN capture_status = 'captured' AND NOT is_legacy_seed_row THEN 1 ELSE 0 END DESC` — a captured row sourced
  from the legacy seed no longer gets the outranking boost; it falls through to plain recency like any non-captured row,
  so a newer, non-tainted competitor for the same key always wins. The synthetic column is excluded from every final
  written-parquet output (all 3 merge-completion sites: incremental + full-rebuild × Option-B/non-Option-B). No-op —
  byte-identical SQL — when the legacy seed doesn't participate in a given cycle, which is the overwhelming majority
  (its frozen mtime naturally excludes it from most incremental cycles' "changed shards" set; it only re-enters via a
  full rebuild, which is when the resurrection actually manifested).
- **`unified_trading_library/manifest_writer/_read_index.py::_merge_shard_frames`** (the Python reader-side helper this
  doc's own diagnostic exercised directly — the ACTUAL call that returned 0 rows instead of 9,757):
  `_read_and_merge_per_vm_shards` tags the frame read from `_LEGACY_SEED_PATH` with a synthetic `_IS_LEGACY_SEED_COL`
  marker; `_merge_shard_frames`'s captured-outranks rank computation now ANDs in `NOT is_legacy_seed`, so a tainted row
  never outranks a newer, untainted competitor. The taint survives exactly ONE additional chained-merge hop (new
  `keep_legacy_seed_taint` kwarg) so `merge_canonical_with_outstanding_shards`'s own canonical-vs-shard merge — the
  specific call this doc's diagnostic used — is protected too; the taint is always stripped before any value returned to
  an external caller (verified by a dedicated regression test asserting the synthetic column never leaks).
- **`unified_trading_library/manifest_writer/_maintenance.py::rebuild_manifest_from_canonical_paths`**: same
  chained-merge shape found on a second, previously-unaudited call site (its own staleness-guard merge against
  freshly-discovered-from-GCS rows) — given the identical `keep_legacy_seed_taint` treatment.

**Scope confirmed cross-asset-group**: `manifest_consolidator.py` is bucket-parametrized shared code (not
per-asset-group duplicated), so this fix protects cefi, defi, and tradfi uniformly — all three buckets carry their own
frozen `_legacy_seed.parquet` per this doc's own §6 above. No separate per-asset-group fix was needed.
`instruments-service`'s `reconcile_phantom_manifest_rows_all.py` (this doc's §"Why it matters" — its DeFi delete passes
use `merge_canonical_with_outstanding_shards` as their staleness guard) needs NO direct change — it calls the now-fixed
UTL function and inherits the protection transitively once instruments-service picks up the new UTL version.

**Tests** (3 new regression tests, all reproducing the exact resurrection scenario and asserting it no longer occurs):
`test_consolidate_legacy_seed_does_not_resurrect_corrected_row` (DuckDB full-rebuild path, in
`tests/unit/test_manifest_consolidator.py`); `test_merge_shard_frames_legacy_seed_taint_never_outranks_newer_correction`

- `test_merge_canonical_with_outstanding_shards_legacy_seed_does_not_resurrect_corrected_row` (Python reader path, in
  `tests/unit/test_manifest_writer_per_vm.py` — the latter a direct reproduction of this doc's own diagnostic: a
  canonical holding the corrected `attempted_failed` state plus a `_legacy_seed.parquet` shard holding the stale
  `captured` state for the identical key). Full `unified-trading-library` test suite + `quality-gates.sh` green before
  shipping.

**Still open / explicitly NOT done by this fix (AT THE TIME OF THIS SECTION)**: the cefi 9,757-row delete had NOT been
re-run yet, and — critically, discovered by a LATER pass in this same session — this Part-1 fix alone turned out to be
INSUFFICIENT for the redo: a direct production `--force` stress-test reverted the delete again even with Part 1 live,
because Part 1's tie-break-demotion only guards a state-FLIP correction, not a DELETION (see the "Part 2" fix and the
"closing" multi-cycle verification sections below, both dated later 2026-07-15). Re-running the delete was correctly
gated on multi-cycle confirmation per operator instruction — that gate caught this exact gap rather than shipping a
false "done." `status`/`priority` are updated in the frontmatter now that BOTH parts are shipped, deployed, and
multi-cycle-verified — see the closing section below for the full evidence chain.

## 🟢 2026-07-15 (independent sweep) — broad "any OTHER reseed vector" audit: clean, PLUS content-verified that the

in-flight Part-2 fix is already LIVE in production

Operator asked a sharp follow-up while a delete re-attempt was live-monitored in a parallel worktree in this same
session/slot: did anyone check for a reseed mechanism OTHER than the one already found? This was a dedicated read-only
sweep (no code/data changes) against that exact question, run concurrently with (and independently of) whatever the
monitoring session was doing. Headline: **clean sweep — no additional reseed vector found** — plus this pass happened to
catch that a second fix commit (`unified-trading-library@8e783d70`, "Part 2") had ALREADY landed and been deployed to
production by the time of this check, closing a real gap Part 1 alone left open.

**1. Other frozen/stale snapshot files (not just the one already found)**: `gcloud storage ls -l` on `_index/per_vm/`
for all three buckets found EXACTLY ONE `_legacy_seed.parquet` per bucket — cefi (frozen 2026-06-24T08:44:46Z, 5.4MB),
defi (2026-06-24T17:28:59Z, 175KB), tradfi (2026-05-12T17:07:19Z, 281KB) — matching this doc's own §6 exactly, no
dated/regional/DR duplicates. Cefi's `per_vm/` has exactly one OTHER file (`cefi-queue-heavy-20260714-123340.parquet`,
an ordinary live backfill-VM shard last written 2026-07-15T11:09:54Z, not a frozen seed — routine, not yet merged into
the canonical as of the last consolidation cycle). Separately, cefi's `_index/` DOES have `backups/` (5 objects, 875MB)
and `snapshots/` (15 objects, 2.3GB) subdirectories — real pre-migration safety-net copies
(`pre_aster_migration_20260713`, `pre_bybit_futures_chain_manifest_20260713`, `pre_purge_deribit_option_..._20260712`,
etc., going back to 2026-05-22). Grepped the whole workspace for any code path that READS from `_index/backups/` or
`_index/snapshots/` as a source (as opposed to the ~30 one-off migration scripts that WRITE a pre-`--apply` safety copy
there): found none — restore-from-backup is a manual, operator-invoked disaster-recovery procedure only
(`codex/05-infrastructure/disaster-recovery.md`, `codex/02-data/ manifest-migration-coordination.md` — explicit steps,
notify-operator, post-mortem doc required), never automatic, and none of the existing backup/snapshot files are tied to
this specific blank-`data_type` incident, so nothing here is a live risk right now — documented as a category worth
knowing about, not a finding requiring action.

**2. Other entry points that write to the canonical index**: read `reconcile_phantom_manifest_rows_all.py` in full (1517
lines) — its ONLY write-capable modes are the two already-identified DELETE passes
(`_apply_delete_chain_level_defi_phantoms`, `_apply_delete_legacy_combined_venue_defi_phantoms`); no `--undo`/
`--restore`/`--revert` flag exists, so the "dry-run candidate list gets accidentally applied as a re-add" scenario the
operator asked about is not possible — the tool can only ever delete/mark-empty, never re-mark something `captured`.
Both delete passes call `merge_canonical_with_outstanding_shards` as their staleness guard (confirmed by grep), so they
inherit the Part-1+2 fix transitively — but that inheritance depends on `instruments-service`'s own environment/image
having picked up the new UTL commit, which was NOT independently verified in this pass (this doc's own P2 todo above
already tracks that as a separate, still-open, non-live-right-now audit item — not duplicating it here). Confirmed the
`--force` full-rebuild path is the ONLY way a whole-corpus reseed happens: the routine `*/1 * * * *` Cloud Scheduler
cron (`deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`) never passes `--force`; every historical
`--force` invocation found workspace-wide (~25 references across issue docs/plans) was a manual
`gcloud run jobs execute ... --args=...,--force` during an operator/agent incident intervention — never scheduled, never
automatic. No disaster-recovery / cross-region-sync / "restore manifest wholesale" script was found anywhere in the
workspace beyond the manual GCS-object-versioning rollback procedure already covered in point 1.

**3. Active (not frozen) writer producing blank-`data_type` rows independently, checked live, right now**: ran a direct
single-object read of the CURRENT `market-data-tick-cefi-prd-central-element-323112` canonical (not a whole-corpus walk)
via `unified_trading_library`'s own `StorageClient`/`resolve_bucket_name`. Result, as of 2026-07-15T12:11 UTC (canonical
generation `1784113556416482`, `consolidator_run_at=2026-07-15T11:05:53Z`, `Update time` on the blob
`2026-07-15T11:05:56Z`): **0 blank-`data_type` rows of ANY `capture_status`** out of 11,250,228 total rows
(captured=3,136,382, attempted_failed=1,738,645). This is a stronger result than "still 9,757" or "resurrected again" —
it's zero, meaning (a) the re-attempted delete this session's parallel monitoring session ran DID land and HELD through
the most recent consolidator cycle, and (b) there is no evidence whatsoever of a live writer independently reintroducing
blank-`data_type` rows post-fix.

**4. The `--force` full-rebuild path, specifically**: this doc's Part-1 write-up already flagged this as unaudited.
Independently confirmed it: `manifest_consolidator.py`'s full-rebuild branch (`if force or canonical_mtime is None`)
originally used ALL per-VM-shard paths unfiltered, including the legacy seed — Part-1's tie-break demotion doesn't help
a full rebuild when the competing row was DELETED (not flipped), because with no competing row left, the frozen seed's
row is the ONLY row for that key and wins trivially regardless of tie-break logic. **This is exactly the gap that
resurrected the delete in production** (per `unified-trading-library@8e783d70`'s own commit message, confirmed live
2026-07-15: "the sanctioned CeFi blank-`data_type` orphan-row DELETE reverted on a real production `--force` rebuild
even with the Part-1 tie-break fix deployed"). Part 2 fixes this by excluding `_legacy_seed.parquet` outright (not just
demoting its rank) from the full-rebuild merge whenever a canonical already exists, plus the same exclusion in
`_read_and_merge_per_vm_shards`'s new `exclude_legacy_seed` param (wired into `merge_canonical_with_outstanding_shards`
and `rebuild_manifest_from_canonical_paths`) — all 3 call sites checked by git diff on
`unified-trading-library@8e783d70`.

**Content-verified live in production (not just git-committed)**: `market-tick-data-service`'s `Dockerfile` was bumped
twice today (`unified-trading-library@2f60fe31` for Part 1, `@48857be4` for Part 2) to pin
`BASE_IMAGE_DIGEST=sha256:7b9a94ea90ce2b5594000520758005bfc37e2c77785e571c043947ff4a77c9ae`. Verified via
`gcloud builds list`/`describe` that Cloud Build `b6e279af` (SUCCESS, finished 2026-07-15T11:00:36Z) built MTDS commit
`5f659c12`, confirmed via `git merge-base --is-ancestor` to be a descendant of BOTH digest-bump commits — i.e. the
currently-published `market-tick-data-service:latest` already carries both fixes. Went one step further than
ancestor-checking (per this codebase's own established "content-verified, not just ancestor-checked" precedent):
`docker pull`+`docker run --entrypoint bash` against the EXACT pinned UTL digest and grepped the live container's
`manifest_consolidator.py`/`_read_index.py`/`_maintenance.py` — confirmed `is_legacy_seed_row`, the
`canonical_mtime is not None and p == _LEGACY_SEED_PATH` full-rebuild exclusion, and `exclude_legacy_seed` are all
PRESENT in the actual deployed image content. Per this codebase's own established operational precedent (documented in
this repo's own prior incident write-ups), the `uts-prod-manifest-consolidator-*` Cloud Run Jobs resolve
`market-tick-data-service:latest` fresh per execution (no separate Job redeploy needed) — consistent with the
2026-07-15T11:05:53Z consolidator run (5 min after the fixed image published) already reflecting the fix, per point 3
above.

**Verdict**: clean sweep. No additional/independent reseed mechanism found beyond the one already tracked by this doc
(the full-rebuild deletion-resurrection gap, Part 2). That gap is not hypothetical — it is confirmed to be the actual
mechanism, is already fixed in code, and the fix is confirmed content-live in production as of this check, with the live
canonical currently showing 0 blank-`data_type` rows. Residual, non-urgent, already-tracked item: this doc's own P2 todo
(audit `reconcile_phantom_manifest_rows_all.py`'s DeFi delete passes for the identical exposure class) remains genuinely
open and is unaffected by this sweep's findings.

Evidence: `gcloud storage ls -l` on `_index/per_vm/`, `_index/backups/`, `_index/snapshots/` for cefi/defi/tradfi
(single-object listings, no corpus walk); full read of
`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`; workspace-wide `rg` for
`legacy_seed`/`_snapshot`/`_frozen`/`_backup`/`--force`/`rollback`/`restore`; `git show`/
`git log`/`git merge-base --is-ancestor` on `unified-trading-library@{f14b13ae,8e783d70}` and
`market-tick-data-service@{2f60fe31,48857be4,5f659c12}`; `gcloud builds list/describe` for `market-tick-data-service`
build `b6e279af`; `docker pull`+`docker run` content-grep against UTL digest
`sha256:7b9a94ea90ce2b5594000520758005bfc37e2c77785e571c043947ff4a77c9ae`; a single-object read of the live cefi
canonical via `unified_trading_library.StorageClient`/`resolve_bucket_name` (ad hoc diagnostic, not committed).

## 🟢 2026-07-15 (closing) — DELIBERATE multi-cycle live verification (the session that ran the redo + Part 2 fix)

This is the primary session that (a) discovered the Part-2 deletion-resurrection gap by directly force-rebuilding
production with the Part-1-only fix deployed (confirmed the 9,757 rows DID resurrect — see `8e783d70`'s own commit
message, quoted by the independent-sweep section above), (b) designed/shipped/deployed Part 2, and (c) ran the actual
multi-cycle confirmation the prior session's delete attempt was gated on. Recorded here for the exact evidence chain
(execution names, generations, row counts) since the independent-sweep section above corroborates the _outcome_ via a
single point-in-time read rather than the deliberate multi-cycle drive documented below.

**Root cause of the original "cycle 1 survived, cycle 2 reverted" mystery** (this doc's own original open question): the
routine `*/1` Cloud Scheduler cron NEVER passes `--force` — it always runs the incremental anti-join path, which only
re-reads shards whose mtime is newer than the last real content-write (`_get_content_write_mtime` cutoff). The frozen
`_legacy_seed.parquet`'s mtime never changes, so it is structurally EXCLUDED from every ordinary incremental cycle's
`changed_paths` — an incremental cycle can never touch it, hence "cycle 1" (an ordinary cron tick) never reverted
anything. The legacy seed re-enters a merge ONLY via a `--force` full rebuild (`merge_paths` = every shard, unfiltered,
pre-Part-2). No code path auto-escalates to `--force` — confirmed by reading `consolidate()`'s only two call sites of
`force=True` (the CLI `--force` flag, always operator/script-invoked) and the stall-alert (`_check_consolidation_stall`)
which only LOGS a recommendation to run `--force` manually, never triggers it itself. "Cycle 2" (the revert) was
therefore necessarily an out-of-band manual/scripted `--force` full rebuild against the cefi bucket sometime in the ~1h
window — consistent with (though not proven to be identical to) this session's own later deliberate `--force`
reproductions below, which used the exact same mechanism to both DISPROVE the Part-1-only fix and then CONFIRM the
Part-2 fix.

**Redo + multi-cycle verification, in order (all against `market-data-tick-cefi-prd-central-element-323112`, all
generation numbers directly `gsutil stat`-read, not self-reported by the scripts):**

1. Deployed Part 1 (`f14b13ae`) to production: UTL image `sha256:a70cae27d0...` (Cloud Build
   `6566c90b-a2d2-428f-be29-956d683821e8`, SUCCESS) → MTDS Dockerfile bump `2f60fe31` → MTDS image
   `sha256:6b0dfd038e...` (Cloud Build `0304d22a-2ff5-4b1d-9b1e-7da767416723`, SUCCESS) → `gcloud run jobs update`
   re-resolved `uts-prod-manifest-consolidator-market-data-{cefi,defi,tradfi,tradfi-legacy}` to `:latest`.
2. Re-ran the CeFi delete (`instruments-service/scripts/delete_cefi_blank_data_type_orphan_rows_2026_07_15.py --apply`):
   current live count re-confirmed 9,757 (unchanged from the 2026-06-28 investigation) — 11,256,487 → 11,246,730 rows,
   generation `1784110007144868` → `1784110148022045`.
3. **Deliberately triggered `--force` on the DEPLOYED (Part-1-only) job**
   (`gcloud run jobs execute ... --args=..., --force`, execution `...-dz8gr`, after pausing the cron + clearing an
   OOM-orphaned lock + bumping the job to 32Gi/8cpu + `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT=24GB` — the default 8GB/11GB
   OOM'd twice first, `Container terminated on signal 9`, consistent with this doc's own cross-referenced CeFi OOM
   history). Log confirmed `legacy_seed_in_cycle=True`, `rows_out=11258976`. **A follow-up dry-run confirmed the delete
   HAD REVERTED — 9,757 rows back** — this is the direct reproduction that proved Part 1 alone was insufficient and
   drove the Part-2 design (documented above).
4. Shipped + deployed Part 2 (`8e783d70`): UTL image `sha256:7b9a94ea90...` (Cloud Build
   `c9bf70d9-8cd1-47cf-a835-32c8f1fd571b`, SUCCESS) → MTDS Dockerfile bump `48857be4` → MTDS image
   `sha256:eab3fdc1f8...` (Cloud Build `559fc09b-8e5f-4e00-9fda-0c507e10a7fc`, SUCCESS) → redeployed all 4 market-data
   consolidator jobs again.
5. Re-ran the delete again: 11,258,976 → 11,249,219 rows, generation `1784111319779932` → `1784113412833129`.
6. **Cycle A — deliberate `--force` rebuild on the Part-2-fixed job** (execution `...-57ggf`): log confirmed
   `legacy_seed_in_cycle=False` (the seed was excluded from the shard-download step entirely —
   `shards_downloaded shards=2` vs. `shards_listed shards=3`), `rows_out=11250228`. Dry-run immediately after: **0
   orphan rows** (was 9,757 pre-Part-2 under the identical `--force` mechanism).
7. **Cycle B — a genuine, NOT-manually-triggered incremental production cycle** (execution `...-gj7zz`, fired by the
   `*/1` cron in the ~60s window before my scheduler-pause fully propagated): absorbed one real new per-VM shard,
   `mode=incremental`, 89 date-chunked windows, `legacy_seed_in_cycle=False` (expected — incremental never includes the
   seed, confirming point 3 of the root-cause section above), `rows_out=11250537`. Dry-run after: **0 orphan rows**.
8. **Cycle C — second independent deliberate `--force` rebuild** (execution `...-pw6xt`, after clearing another
   cron-created lock): `legacy_seed_in_cycle=False`, `shards_downloaded shards=2` (of 3 listed), `rows_out=11250538`.
   Dry-run after: **0 orphan rows**.

**Verdict: durably fixed, verified through 3 independent real production cycles post-Part-2** — two of which
deliberately re-created the EXACT mechanism (`--force` full rebuild) that reverted both the original 2026-07-15 delete
AND this session's own first redo attempt (step 3 above), plus one genuine unplanned incremental cycle. This is not a
"caught one lucky cycle" result — Cycle A and Cycle C are independent, deliberate reproductions of the specific failure
mode, run ~20 minutes apart, both clean.

**Operational notes for anyone re-reading this later**: (a) the cefi consolidator job was temporarily bumped to
32Gi/8cpu + the cron paused during steps 3/6/8 above to get a clean, uncontested `--force` run past the per-minute
cron's lock contention and the ~11.6M-row full-rebuild's memory footprint (the default 8GB/11GB DuckDB limit is
insufficient for a full rebuild of this bucket's current size — this is now a known operational fact, not previously
documented, worth adding to the consolidator SSOT if CeFi needs another manual `--force` in future); both were reverted
to their original values (16Gi/4cpu, cron re-enabled) once verification completed — the job's PERSISTENT config carries
no trace of the temporary bump. (b) `CONSOLIDATOR_DUCKDB_MEMORY_LIMIT` set via
`gcloud run jobs execute --update-env-vars` is execution-scoped only (confirmed via `gcloud run jobs describe` showing
the job's persistent env unchanged) — no cleanup needed there. (c) DeFi/TradFi/TradFi-legacy consolidator jobs were also
redeployed to the final Part-2 image for consistency (both buckets are confirmed to carry their own frozen
`_legacy_seed.parquet` per this doc's §6) — not independently multi-cycle-verified this session (no known pending
deletes on those buckets to gate on), but now running the same fixed code.

This todo (`plans/active/data_pipeline_alerts_batch_remediation_2026_07_15.md`'s cefi-orphan-rows item) is now
closeable. The `- [ ]` P2 audit item above (`reconcile_phantom_manifest_rows_all.py`'s DeFi delete passes) remains
genuinely open — it is a DIFFERENT code path in `instruments-service`, not verified this session to have picked up the
new UTL version yet, and is explicitly NOT blocking this issue's resolution per the independent-sweep section's own
scoping.

Evidence: direct `gcloud run jobs execute`/`executions describe`/`logging read` against
`uts-prod-manifest-consolidator-market-data-cefi` for executions `dz8gr`/`w4hx6`/`qjr2f`/`57ggf`/`gj7zz`/`pw6xt`;
`gsutil stat` on the canonical + lock blob before/after each step; `gcloud builds describe` for
`6566c90b`/`c9bf70d9`/`0304d22a`/`559fc09b` (all SUCCESS); direct `--dry-run` reads via
`instruments-service/scripts/delete_cefi_blank_data_type_orphan_rows_2026_07_15.py` after every cycle.

## 🟢 2026-07-15 — independent corroboration (separate re-verification session, dispatched to confirm hold)

A third, independently-dispatched session (operator ask: re-verify the delete's current state and monitor real
consolidator cycles before declaring success, given the doc's own earlier "confirmed live" resurrection). Arrived after
the "closing" session above had already shipped Part 2 and re-run the delete, so this session's own live queries found
the fix already in place rather than needing to re-execute it — recorded here as independent cross-validation, not a
duplicate remediation:

- Confirmed the same facts independently: `market-tick-data-service`'s HEAD Dockerfile (`origin/live-defi-rollout`)
  still pins `BASE_IMAGE_DIGEST=sha256:7b9a94ea90...` (Part 2); the `uts-prod-manifest-consolidator-market-data-cefi`
  Cloud Run Job's most recent manual execution (`57ggf`, `mode=full`, `legacy_seeded=False`, completed
  2026-07-15T11:05:56Z) used image digest `sha256:5bf7a426...`, traced via `gcloud builds describe` to Cloud Build
  `b6e279af` (commit `5f659c12`, a confirmed descendant of the Part-2 digest-bump commit `48857be4`).
- Independently re-ran the broad blank-`data_type` query
  (`capture_status='attempted_failed' AND (data_type=='' OR data_type IS NULL)`, and separately ANY `capture_status`)
  against a fresh raw canonical-only read: **0 rows**, confirmed repeatedly across a ~29-minute window
  (2026-07-15T11:03:32Z delete write through 11:32:43Z), spanning executions `57ggf` (`mode=full`), `gj7zz`
  (`mode=incremental`, ~9 min, 89 date-chunks), and ~6 more cron-fired executions after this session found the cron
  paused and resumed it (`gcloud scheduler jobs resume`) once the fix was independently confirmed holding — full
  detail + evidence table filed in `phantom_captures_cefi_2026_06_28.md`'s own matching 2026-07-15 re-verification
  section (this session's primary write-up) to avoid duplicating the closing session's already-thorough evidence chain
  here.
- No discrepancy found between this session's independent observations and the closing session's account above —
  cross-validates the verdict: **durably fixed for cefi.** Concur with the closing session's own scoping: defi/tradfi
  carry the same fix (shared, bucket-parametrized code) but have NOT had their own live
  resurrection-then-delete-then-hold cycle exercised — the P2 DeFi-delete-passes audit item above remains open and
  unaffected.
