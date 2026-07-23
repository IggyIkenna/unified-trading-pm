---
doc_type: issue
title:
  Consolidator silently reaps unmerged per-VM shards when an out-of-band index write strips the content-write marker
summary:
  An out-of-band rewrite of _index/availability_index.parquet that does not preserve the custom metadata destroys
  consolidator_content_write_at. _get_content_write_mtime then falls back to blob.updated — the out-of-band write's OWN
  mtime — which advances the prune cutoff PAST pending per-VM shards. The next consolidator run deletes those shards
  without merging them and reports success=True / exit(0) / rows_in=0. Fired for real on 2026-07-17 and destroyed 7,185
  sports manifest rows (recovered in-band from a pre-merge download). Affects EVERY asset_group, not just sports.
# RESOLVED 2026-07-17 04:30Z: rollout steps 3-7 complete. GCP = LIVE + PROVEN (24/24 consolidator jobs on
# sha256:57fc72e1; the fixed _get_content_write_mtime verified by running python inside that exact image).
# instruments-store-cefi-prd DISARMED 03:54Z (marker re-stamp, 3 cycles pruned=0, rows delta 0); all 10 GCP prd
# buckets carry a marker, 0 armed. AWS: the same verified image is pushed to ECR (:latest == sha256:57fc72e1);
# Batch-Fargate pickup is structurally certain (job defs reference :latest by TAG) but UNOBSERVED from this host
# (uts-orchestrator-epic-role lacks batch:* / events:* / s3:GetObject) — see § Rollout residual.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest, consolidator, data-correctness, silent-data-loss, per-vm-shards, gcs]
related:
  [
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: >-
  code fix unified-trading-library@1e995f75 (regression tests measured failing-before/passing-after) + FULL PROD ROLLOUT
  2026-07-17 — UTL base image sha256:61445152 (cloudbuild=74a5e3df, from 61bf7444 contains 1e995f75) → MTDS pin bump
  market-tick-data-service@22cb4d5f → MTDS image sha256:57fc72e1 (cloudbuild=f54235dc) → promote PR #598 merged
  04:27:08Z → 24/24 GCP consolidator jobs verified running sha256:57fc72e1, with the fixed code proven by executing
  python INSIDE that image → ECR latest mirrored to the identical sha256:57fc72e1 (04:29:43Z). Live exposure closed
  earlier at 03:54:34Z by the option-A marker re-stamp on instruments-store-cefi-prd (corrected stamp
  2026-07-14T04:00:00Z — the doc's original 2026-05-12T18:00Z value was measurably wrong). Residual — AWS Batch
  execution pickup unobserved from this host (IAM), not unverified-by-choice.
source:
  [
    sports legacy bucket cutover Phase 6 / T6.1 execution 2026-07-17,
    consolidator exec uts-prod-manifest-consolidator-instruments-sports-4rfp4,
  ]
---

# Consolidator silently reaps unmerged per-VM shards after an out-of-band index write

> **Severity: P0 / silent data loss.** The failure mode is a **successful-looking run**: `success=True`, `exit(0)`,
> `rows_in=0`, shards gone. Nothing alerts. It is caught only by someone who counted the rows BEFORE and AFTER.

## What happened (measured, 2026-07-17)

Executing T6.1 of the sports legacy bucket cutover — merging two pending per-VM shards into the canonical instruments
index — the first consolidator run (`uts-prod-manifest-consolidator-instruments-sports-4rfp4`, 01:34:31Z) logged:

```
manifest-consolidator bucket=instruments-store-sports-prd-central-element-323112
  success=True shards=3 rows_in=0 rows_out=0 dedup_dropped=0 pruned_shards=2 latency_ms=9449.3 error=-
ManifestConsolidator: pruned 2 consolidated per-VM shard(s)
  (cutoff=2026-07-16T18:45:21.846000+00:00, 2 eligible)
```

Both pending shards (`cutover-move-20260716.parquet` 7,183 rows; `or9-recover-20260716.parquet` 2 rows) were **deleted
without being merged**. The index was byte-identical afterwards (5,342,265 rows, delta 0). GCS retained **no**
noncurrent versions (`gcloud storage ls -a` on `_index/per_vm/` → only `_legacy_seed.parquet`). **7,185 manifest rows
describing 92,722+ real moved objects were destroyed by a run that reported success.**

Recovery was possible ONLY because the executing agent had downloaded both shards minutes earlier to measure the
expected deltas. Had it trusted the plan's expected numbers instead of deriving its own, the loss would have been
permanent and silent.

## Root cause

`unified_trading_library/manifest_consolidator.py`:

1. **`_prune_consolidated_shards` (`:1751-1782`)** deletes a shard iff `mtime <= cutoff`, where
   `cutoff = content_write_marker − _INCREMENTAL_SKEW_SECONDS (5s)`. Its stated invariant:

   > the marker carries the last real merge's SHARD-LISTING start time … so mtime `<= cutoff` proves the shard was
   > visible to that merge's listing — either merged as "changed" or already settled from an earlier cycle. Its data is
   > therefore provably in the canonical and the shard is redundant.

   This is sound — **but only if the marker was written by an actual merge.**

2. **`_get_content_write_mtime` (`:1617-1666`)** resolves the marker with a fallback chain:

   ```
   consolidator_content_write_at  →  consolidator_run_at  →  blob.updated
   ```

   documented as safe:

   > The fallback is SAFE: it can only make the cutoff OLDER (or equal), never newer, so it over-includes shards
   > (re-merge) rather than under-includes (silent drop) — fail toward correctness.

3. **That safety argument does not hold.** It assumes `blob.updated` is a proxy for "when a merge last wrote content" —
   true for a legacy canonical never touched by anything else. But **any out-of-band writer** that rewrites
   `_index/availability_index.parquet` without preserving custom metadata does two things at once:
   - **strips** `consolidator_content_write_at` (custom metadata is not carried by a plain rewrite), and
   - **bumps** `blob.updated` to now.

   The fallback then reads the out-of-band write's OWN mtime as if it were a merge's shard-listing time. The cutoff
   jumps **forward**, past shards no merge ever saw ⇒ **silent drop** — precisely the outcome the docstring claims is
   impossible. It fails toward DATA LOSS, not correctness.

### Forensic proof of the strip

Backups made by the cutover (`gcloud storage cp` preserves custom metadata) bracket the event:

| object                                              | as of                                   | `consolidator_content_write_at` |
| --------------------------------------------------- | --------------------------------------- | ------------------------------- |
| `availability_index.20260716-080453.precutover.bak` | 08:05Z (pre-purge)                      | `2026-07-16T06:36:46Z` (real)   |
| `availability_index.20260717-012712.pre_t6_1.bak`   | 01:27Z (post-purge, post-18:45 rewrite) | **`metadata: None`**            |

The T3.1 purge (13:09Z) and the 18:45:26Z byte-equivalent rewrite each rewrote the index out-of-band; the marker did not
survive. Fallback → `blob.updated` = 18:45:26.846Z → cutoff = **18:45:21.846Z** (exactly the logged value) → both shards
(12:46:09Z, 17:30:42Z) eligible → reaped.

**The poisoning agent was the "frozen-generation witness" itself** (`generation=1784227526828259`, the 18:45:26Z
rewrite). It was recorded as proof the index was quiet and unchanged — and it was, at the ROW layer. At the METADATA
layer it had armed a shard reaper.

## Blast radius

**Not sports-specific.** `_get_content_write_mtime` / `_prune_consolidated_shards` are asset-group-agnostic UTL code
used by every `uts-prod-manifest-consolidator-*` job. The trap arms whenever BOTH hold:

1. something rewrites a bucket's `_index/availability_index.parquet` out-of-band (a purge, a repair one-off, a manual
   `cp`/restore, a backfill patch script — the workspace has many), **and**
2. a per-VM shard written BEFORE that rewrite is still unmerged when the consolidator next runs.

Condition (2) is most likely exactly when (1) happens, because out-of-band index surgery is normally done with the
consolidators PAUSED — which is precisely when shards pile up unmerged. **The freeze/repair/resume runbook shape makes
this MORE likely, not less.**

Sports MDT was spared only by luck of ordering: its canonical still held a genuine marker (`2026-07-15T22:51:06Z`) and
was never rewritten out-of-band, so its shard (07-16 12:54:13Z) sat NEWER than the cutoff.

## ✅ FIX SHIPPED — `unified-trading-library@1e995f75` (2026-07-17)

**Reproduced FIRST, then fixed** (the report was CONFIRMED, not falsified). Option (1) below implemented, hardened by a
second hole found while fixing.

- **Reproduction**:
  `tests/unit/test_manifest_consolidator.py::test_out_of_band_index_rewrite_stripping_marker_does_not_reap_pending_shard`
  — end-to-end `consolidate()` with the REAL `_get_content_write_mtime` + `_list_per_vm_shards_with_mtime` +
  `_prune_consolidated_shards` (nothing about the bug stubbed). A new `_MarkerStrip*` stub family models the two GCS
  properties the bug turns on: custom metadata is REPLACED by each write (a plain rewrite strips it) and `updated` is
  bumped. **Measured FAILING on pre-fix code** with the incident's exact signature —
  `pruned 1 consolidated per-VM shard(s) (cutoff=<rewrite − 5s>, 1 eligible)`, shard deleted unmerged, `success=True` —
  and passing after. Verified by materialising the pre-fix module from git and re-running (both new tests fail before /
  pass after); all 98 tests green.
- **SECOND HOLE FOUND (not in the original report)**: `consolidator_run_at` is _also_ a fatal fallback. It is the
  FRESHNESS marker that the idle `_touch_canonical_mtime` re-stamps to `now()` **every cycle** (`:1499`), so once a
  strip removes both markers the very next idle touch re-creates `run_at` at now and **re-arms the identical reap
  through the second fallback**. Fixing only `blob.updated` would have left the trap live. Pinned by
  `::test_get_content_write_mtime_never_falls_back_to_run_at_or_blob_updated`.
- **The fix (fail CLOSED)**: `_get_content_write_mtime` reads `consolidator_content_write_at` and **nothing else** — no
  fallback chain. `None` now means **"the cutoff is UNPROVABLE"**, not "everything is settled"; `consolidate()` responds
  by treating every shard as changed (**merge** — idempotent) and pruning **NOTHING** (both prune sites are already
  gated on `content_write_mtime is not None`). The merge re-stamps a genuine marker → normal incremental+prune resumes
  next cycle: **self-healing, one merge of cost, never a silent drop.** The recovery merge EXCLUDES the legacy seed, or
  it would resurrect rows the out-of-band purge legitimately deleted (the 2026-07-15 deletion-resurrection gap — and a
  purge is exactly the writer that strips the marker).
- **The 2026-07-13 prune-race fix is PRESERVED** (marker = the merge's shard-LISTING time): its regression test
  `::test_shard_written_between_listing_and_canonical_write_survives_next_cycle` still passes, and case (d) of the new
  fallback test asserts a genuine marker still drives the cutoff.
- **Why NOT fix the ~15 out-of-band writers instead**: measured —
  `backfill_remove_unknown_league_phantom_2026_07_09.py:168`, `flip_b1_thin_payload_to_reattempt.py:288`,
  `dedup_defi_manifest_status_priority_2026_06_24.py:113`, `delete_aster_overseeded_capability_rows.py:130`,
  `populate_is_index_v9_2026_06_19.py:172`, `reconcile_defi_lending_manifest_canonical_2026_06_24.py:172`,
  `dedup_phantom_after_recovery.py:249`, `backfill_cefi_blank_instruments_data_type_2026_07_06.py:141`,
  `rebuild_sports_manifest.py:260`, +others all rewrite the canonical via a plain metadata-less `upload_bytes`. One
  consolidator fix covers all of them **plus every future one-off nobody remembers** — the class of assumption that
  produced this incident. (Grep-then-READ correction: of the four scripts named in the dispatch, only
  `backfill_remove_unknown_league_phantom` actually rewrites the canonical; `gw_false_empty_repair` +
  `recency_masked_adjudication` only read/snapshot, and `fixtures_eu_truthset_flip` writes a sanctioned per-VM shard.) A
  marker strip is now **COST** (one full merge), never **LOSS**.

## Original recommended fix (as filed)

Ordered by strength; (1) is the minimum — (1) is what shipped.

1. **Never prune on a fallback marker.** If `consolidator_content_write_at` (and `consolidator_run_at`) are absent,
   `_get_content_write_mtime` should signal "unknown" for PRUNE purposes and `_prune_consolidated_shards` must **prune
   nothing** — keep every shard, let the next real merge stamp the marker and prune on a later cycle. Pruning is an
   optimisation; merging is the contract. Never trade a durability invariant for a cleanup. (The `blob.updated` fallback
   may still be acceptable for _changed-shard detection_, which fails toward re-merge, not toward drop.)
2. **Make the prune positively-proven, not inferred.** Prune a shard only when its rows are demonstrably in the
   canonical — e.g. stamp each merged shard's generation/mtime into the canonical's metadata (a "merged through" set),
   and prune only members of that set. mtime-vs-cutoff is a proxy that any out-of-band write can falsify.
3. **Make out-of-band index writes preserve the marker.** Any tool rewriting `availability_index.parquet` must carry the
   existing custom metadata forward (or re-stamp it). This is necessary but NOT sufficient — it relies on every future
   one-off remembering, which is the class of assumption that produced this incident.
4. **Loud-fail the tell.** `rows_in=0 … pruned_shards=N>0` is contradictory: shards existed and were listed, yet nothing
   was read from them, and they were deleted anyway. That combination should log an ERROR / alert, never `success=True`.

## Repro

1. Bucket with a canonical index + ≥1 unmerged shard under `_index/per_vm/`.
2. Rewrite `_index/availability_index.parquet` out-of-band without preserving custom metadata (any plain `cp`/write),
   ensuring the rewrite's mtime is NEWER than the shard's.
3. Run the consolidator.
4. Observe: `rows_in=0 rows_out=0 pruned_shards=N`, `success=True`, `exit(0)`; the shard is gone; its rows never landed.

## Blast-radius sweep — MEASURED 2026-07-17 (read-only)

### What IS checkable: the ARMING condition (an index with no marker)

Probe (note **`custom_fields`**, not `metadata`, in current gcloud — the first attempt at this sweep used `metadata` and
returned a false "all 10 MISSING"; always sanity-check against a raw `describe`):

```bash
gcloud storage objects describe gs://<bucket>/_index/availability_index.parquet \
  --format="value(custom_fields.consolidator_content_write_at,update_time)"
```

**Result across all 10 GCP prd consolidator buckets: 9 carry a genuine marker; 1 does NOT.**

| bucket                                              | `consolidator_content_write_at` | state                                                   |
| --------------------------------------------------- | ------------------------------- | ------------------------------------------------------- |
| **instruments-store-cefi-prd**                      | **ABSENT (no custom_fields)**   | 🔴 **REAPER ARMED** → ✅ **DISARMED 03:54:34Z** (below) |
| instruments-store-{tradfi,defi,sports,pred}-prd     | present (genuine)               | healthy (re-checked 04:30Z — still genuine)             |
| market-data-tick-{cefi,tradfi,defi,sports,pred}-prd | present (genuine)               | healthy (re-checked 04:30Z — still genuine)             |

**🔴 `instruments-store-cefi-prd-central-element-323112` is armed RIGHT NOW** (on the pre-fix image still deployed). Its
canonical has **no custom metadata at all** — neither marker — while the `*/1` cron's idle `_touch` bumps `update_time`
every minute. So the fabricated cutoff (`blob.updated − 5s`) **tracks ~now permanently**: this is not a one-shot trap
but a **continuously re-armed** one. It has not destroyed anything yet only because its `_index/per_vm/` currently holds
**nothing but `_legacy_seed.parquet`** (`shards=1`, prune-exempt) — there is simply nothing to reap. The moment a cefi
instruments shard lands and is not merged before the next cycle's cutoff overtakes it (the ~9-14s cycle-latency window
each minute, or **any** freeze/repair/resume where shards pile up), it is deleted unmerged. Sports was spared the same
fate in June only by ordering luck.

### What is NOT checkable: past firings

**The `rows_in=0 … pruned_shards=N>0` tell proposed above does NOT work — measured false-positive.** It fires on normal
steady state, because the design merges at cycle N and prunes at cycle N+1. Live instruments-cefi, 2026-07-16:

```
13:33:39  shards=2 rows_in=93995 rows_out=93958 pruned_shards=0   ← real merge; rows LANDED
13:34:43  shards=2 rows_in=0     rows_out=0     pruned_shards=1   ← no-op + prune  ← the "tell", but CORRECT
13:35:49  shards=2 rows_in=93995 rows_out=93958 pruned_shards=0   ← writer re-wrote it; merged again
13:36:42  shards=2 rows_in=0     rows_out=0     pruned_shards=1   ← pruned again, again correctly
```

Proving a firing requires knowing the pruned shard's rows **never merged** — but the shard is gone and **GCS retained no
noncurrent versions of per_vm objects** (verified on sports during the incident). So:

- **Past firings are generally UNPROVABLE after the fact.** No claim is made here that there were none — the mechanism
  is asset-group-agnostic, has been live since the prune was introduced, and the freeze→repair→resume runbook shape
  (which the workspace prescribes) is exactly when it fires. It has very plausibly fired before, silently.
- **Equally, no specific past loss is claimed** beyond the one directly observed and recovered (sports T6.1, 7,185
  rows).
- The one surviving forensic handle is a **pre-event copy** of a shard (a backup, a local download) — which is why the
  sports rows were recoverable at all.

### Not checkable from this host: the AWS mirrors

`aws s3api head-object` on the AWS mirror buckets returns **403 Forbidden** under `uts-orchestrator-epic-role` (the same
IAM gap documented in the prune-race issue doc's rollout note — the role lacks `s3:ListBucket`/GetObject there). The 26
Batch-Fargate consolidators' marker state is therefore **UNVERIFIED from here**; confirm from an S3-read-capable role.
The code fix reaches them via the same ECR `:latest` image sync.

## Verification / recovery recipe (if this already fired somewhere)

- Detect: consolidator log line with `rows_in=0` and `pruned_shards>0`; or an index whose row count did not move across
  a run that pruned shards.
- Check for a stripped marker: read the canonical blob's `.metadata` — `None`/missing on a bucket that has been
  consolidating is the tell.
- Recover: restore the shard (from a pre-event copy — GCS versioning did NOT retain it in the observed case) into
  `_index/per_vm/` so its mtime is NEWER than the canonical's `updated`, then run the consolidator immediately (with the
  writer schedulers paused, so nothing re-advances the cutoff). Verify `rows_in > 0` and re-read the index BY CONTENT.
- **Never** re-upload a shard while its bucket's canonical is still being rewritten out-of-band — the race re-arms.

## Rollout — ⚠️ the fix is NOT LIVE in prod yet (code-shipped ≠ operationally-shipped)

The deployed consolidators are Cloud Run Jobs (`uts-prod-manifest-consolidator-*`, ~20) + 26 AWS Batch-Fargate mirrors,
all running the **`market-tick-data-service:latest` image with UTL installed as a dep**. Per the image deploy-hygiene
rule (`/codex/08-workflows/ci-cd-flow.md`), **a UTL fix does NOT reach them until the MTDS `BASE_IMAGE_DIGEST` is bumped
and MTDS is rebuilt.** Exact chain (mirrors the 2026-07-13 prune-race rollout precedent: UTL@97212d3b → MTDS@b11199cb):

| #   | Step                                                                                 | State (2026-07-17 04:30Z — ROLLOUT COMPLETE)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| --- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | UTL fix on LDR                                                                       | ✅ `unified-trading-library@1e995f75`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 2   | UTL promote PR LDR→main, v2-gated auto-merge                                         | ✅ **DONE — PR #586 MERGED 2026-07-17T03:40:09Z** (fleet promoter manually triggered, run 29552660105). **Verified by CONTENT** — not squash-inflated `ahead_by`: `gh api …/compare/main...live-defi-rollout` → **`files: 0`**, and `manifest_consolidator.py@main` carries the `UNPROVABLE` contract (4 hits). Only these 2 files rode along.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 3   | UTL base image republished from a build whose commit contains the fix → new digest   | ✅ **DONE — and it WAS automatic; the earlier "NOT automatic" finding was a FALSE PROBE (wrong region).** Cloud Build here is **REGIONAL (`asia-northeast1`)**; `gcloud builds list` / `triggers list` **without `--region` query the GLOBAL scope and return a misleading empty/stale list**. Trigger **`unified-trading-library-live-defi-rollout` (493290ef)** fires on **LDR** (not main). `Evidence: cloudbuild=74a5e3df-a137-4c66-a69f-e2400fd564dc` SUCCESS (03:40:29→03:46:56Z) from commit **61bf7444** → published base digest **`sha256:61445152e3587bd9c65279d076f24cfc4a5880136811d0e70e27b50f38f455f9`** (tag `0.55.0,latest`). Ancestry+CONTENT verified: `git merge-base --is-ancestor 1e995f75 61bf7444` = YES; `manifest_consolidator.py@61bf7444` has 4 `UNPROVABLE` hits + 0 fallback-loop hits. (Build `a8cf56e4` at 03:31Z had already built the fix commit `1e995f7` directly.) |
| 4   | MTDS `Dockerfile` `ARG BASE_IMAGE_DIGEST` bump → quickmerge to LDR → promote to main | ✅ **DONE — `market-tick-data-service@22cb4d5f`** (`Dockerfile:115` `sha256:d15fb29b…` → **`sha256:61445152…`**). QG `--no-fix` green (sentinel == HEAD), quickmerge `--agent --files 'Dockerfile'`. **The bump is REQUIRED**: MTDS `cloudbuild.yaml`'s `docker build` does NOT pass `--build-arg BASE_IMAGE_DIGEST` (the pre-pull step only _reads_ the pin), so the Dockerfile ARG default governs the base.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| 5   | MTDS image rebuilt; `:latest` → new digest + promote to main                         | ✅ **DONE.** MTDS LDR trigger (`46d60bf7`) auto-fired: `Evidence: cloudbuild=f54235dc-941b-47c5-9814-343a019001a3` **SUCCESS** (04:06:37→04:15:30Z), `source.gitSource.revision = 22cb4d5ff0088722ce355f8395fbc33ca8b56ec7` (exact bump commit — ancestry by CONTENT, not tag inference). `:latest` **CHANGED `sha256:5f056140` → `sha256:57fc72e1…`**. **Layer proof**: all 16 layers of UTL base `61445152` are the exact ordered prefix of MTDS `57fc72e1`; control — old MTDS `5f056140` had old base `d15fb29b` as prefix. Promote PR **#598 MERGED 04:27:08Z** (auto-merge fired on its own once v2 passed — no gate bypassed); `compare/main...LDR` → **`files: 0`**.                                                                                                                                                                                                                           |
| 6   | GCP Cloud Run jobs re-resolve `:latest`                                              | ✅ **DONE — VERIFIED LIVE.** Cloud Run resolves the tag to a digest at **execution-creation** time (job spec still says `:latest`; execution `…-instruments-cefi-swrnl` created 04:17:01Z shows `image: …market-tick-data-service@sha256:57fc72e1…`). **Fleet sweep: 24/24 `uts-prod-manifest-consolidator-*` jobs' latest execution runs `sha256:57fc72e1` — 0 on the old digest.** No repin needed. **DIRECT CODE PROOF inside the running image**: `docker run --entrypoint python …@sha256:57fc72e1 -c "inspect.getsource(m._get_content_write_mtime)"` → 2 `UNPROVABLE` mentions, **no** `run_at`/`blob.updated` fallback, reads the marker key.                                                                                                                                                                                                                                                  |
| 7   | AWS ECR `market-tick-data-service:latest` rebuilt + pushed                           | ✅ **PUSHED** — ECR `:latest` was **stale at `sha256:4e60180c` (2026-07-13T21:03:35Z)**, i.e. the 26 Batch-Fargate consolidators were still on pre-marker-strip-fix code. **Mirrored the VERIFIED GCP image rather than rebuilding** (pull GAR `@sha256:57fc72e1` → retag → push), so **ECR digest == GCP digest == `sha256:57fc72e1`** (byte-identical to the image proven live on GCP; strictly better than the 2026-07-13 rebuild which diverged). Pushed **04:29:43Z**; old `4e60180c` now untagged. **Batch pickup NOT OBSERVED from here** — see the residual note below.                                                                                                                                                                                                                                                                                                                        |

**Steps 3-7 executed 2026-07-17 04:00-04:30Z — the pre-fix reaper is NO LONGER deployed on GCP** (24/24 jobs on
`sha256:57fc72e1`, code-proven inside the image). The interim mitigation below was ALSO applied first, before the image
shipped, and is retained because it is what closed the live exposure window.

### ✅ Option (A) APPLIED 2026-07-17 03:54:34Z — cefi disarmed (with a CORRECTED stamp value)

`instruments-store-cefi-prd`'s canonical had **no custom metadata at all** — neither marker. Metadata-only
`blob.patch()` via the sanctioned client (`get_storage_client()` + the same `._client` native access the consolidator
itself uses); **deliberately NOT a content rewrite**, since a content rewrite is the very act that strips the marker.
Verified: `generation` UNCHANGED (`1784260426780854` before and after ⇒ rows untouched), `metageneration` 1→2.

> **⚠️ The stamp value named in option A as originally filed (`2026-05-12T18:00:00Z`) was WRONG and would have caused
> the exact deletion-resurrection it claims to avoid.** The doc took the legacy seed's mtime from
> `gcloud storage ls -l`, which prints **`creation_time`** (`2026-05-12T17:06:19Z`). The consolidator reads
> **`blob.updated`** (`_list_per_vm_shards_with_mtime` + `_prune_consolidated_shards`), which for cefi's seed is
> **`2026-07-14T03:17:52Z`** — a **COLDLINE lifecycle storage-class transition** bumped it (`storage_class: COLDLINE`,
> `storage_class_update_time: 2026-07-14T03:17:52`, `metageneration: 2`) with **no content rewrite and no metadata
> strip**. Stamping `2026-05-12T18:00Z` would have left the seed **ABOVE** the cutoff → classified CHANGED → **re-merged
> → resurrection of rows a purge legitimately deleted**. A pre-flight guard caught this before `--apply`.
>
> **Applied value: `2026-07-14T04:00:00+00:00`** — just after the seed's REAL effective mtime, honouring option A's
> stated INTENT (cutoff moves backward; seed stays "unchanged"; future shards merge; `pruned=0`) rather than its literal
> number.

**Why this disarms the still-deployed PRE-FIX image**: pre-fix `_get_content_write_mtime` reads
`consolidator_content_write_at` **FIRST** (`git 1e995f75^`:
`for key in (_CONSOLIDATOR_CONTENT_WRITE_AT_KEY, _CONSOLIDATOR_RUN_AT_KEY)`), so a present marker short-circuits the
`blob.updated` fallback — the fabricated cutoff becomes structurally unreachable.

**Measured proof (3 post-stamp cycles, 03:55:44 / 03:56:32 / 03:57:39Z)**: every cycle
`success=True shards=1 rows_in=0 pruned_shards=0`; the **marker SURVIVED all 3 cycles** (re-read
`2026-07-14T04:00:00+00:00` at every tick — the idle touch's tier-1 `copy_blob`-to-self preserves custom metadata);
index rows **80,578 → 80,578 (delta 0)**.

**Why cefi had NEITHER marker (mechanism now fully explained)**: `_touch_canonical_mtime` tier-1 is a server-side
`copy_blob`-to-self, which **copies the source's metadata verbatim** — so it faithfully propagated the stripped (empty)
metadata forward every minute while bumping `update_time` (`creation_time == update_time`, `metageneration: 1` on each
new generation). Tier-2 (the only path that stamps `consolidator_run_at`) never ran because tier-1 succeeded. Hence the
fabricated cutoff tracked ~now permanently, exactly as the sweep described.

**Post-rollout marker re-check (04:30Z) — all 10 GCP prd buckets carry a marker, 0 armed**: the 9 others are genuine and
actively advancing (e.g. `market-data-tick-defi` `02:40:45Z → 03:15:48Z` across the session = a real merge re-stamping;
`instruments-store-sports` `2026-07-17T03:15:45Z`, genuine post-restore). Note the prediction buckets are named
`*-pred-prd-*`, **not** `*-prediction-prd-*` (a `*-prediction-*` probe returns a misleading 404).

**Do NOT rewrite any bucket's `_index/availability_index.parquet` out-of-band without carrying the custom metadata
forward.** With the fix live this is now COST (one full merge) rather than LOSS — but it is still the polite contract.

## Rollout residual — AWS Batch pickup is UNOBSERVED (not unverified-by-choice)

The ECR push is confirmed by `aws ecr describe-images` (`:latest` = `sha256:57fc72e1`, pushed 04:29:43Z; the stale
`sha256:4e60180c` from 2026-07-13 is now untagged). **What could NOT be checked from this host**: every AWS control
surface needed to watch a Batch task is denied under `uts-orchestrator-epic-role` — measured 2026-07-17:

| probe                                | result                                                      |
| ------------------------------------ | ----------------------------------------------------------- |
| `aws ecr describe-images`            | ✅ OK (used for the push + verification)                    |
| `aws batch describe-job-definitions` | ❌ `AccessDeniedException` (`batch:DescribeJobDefinitions`) |
| `aws batch list-jobs`                | ❌ `AccessDeniedException` (`batch:ListJobs`)               |
| `aws events list-rules`              | ❌ `AccessDeniedException` (`events:ListRules`)             |
| `aws s3api head-object` (manifest)   | ❌ `403 Forbidden`                                          |

**Structural (code-level, NOT live) basis for expecting automatic pickup**:
`deployment-service/terraform/aws/manifest_consolidator_scheduler.tf:47` sets
`mtds_ecr_image = "…/market-tick-data-service:latest"` — referenced **by TAG** at `:253` + `:316` (both job-definition
modules), so Fargate re-resolves the tag at each per-minute task start. This mirrors the 2026-07-13 precedent, which
accepted the identical caveat ("pickup is structurally certain but unobserved from here"). **No claim is made that an
AWS Batch execution has been observed running `sha256:57fc72e1`.** Confirm from a Batch-read-capable role/console, or
grant `uts-orchestrator-epic-role` `batch:ListJobs` + `batch:DescribeJobDefinitions` + `s3:GetObject`/`ListBucket` on
the manifest buckets to close this observability gap permanently (tracked in
`aws_consolidator_batch_logstream_iam_gap_2026_07_16.md`).

## Measured lessons — two FALSE PROBES corrupted this doc's own findings

Both were "the tool answered a different question than the one asked", and both produced confident, wrong conclusions
that a later measurement overturned. Worth generalising:

1. **`metadata` vs `custom_fields`** (already recorded above) —
   `gcloud storage objects describe --format="value(metadata…)"` returned a false "all 10 buckets MISSING the marker".
2. **GLOBAL vs REGIONAL Cloud Build** (new, 2026-07-17) — `gcloud builds list` / `gcloud builds triggers list` **without
   `--region`** query the GLOBAL scope: the trigger list came back **EMPTY** and the newest build looked like `01:13Z`.
   That produced the (wrong) conclusion "the UTL base-image republish is NOT automatic; `image-build-gate.yml` is only a
   PR validator". **Measured with `--region asia-northeast1`: 30+ triggers exist**, including
   `unified-trading-library-live-defi-rollout` (`493290ef`) which fires on **LDR pushes**, and it had **already
   republished the base image at 03:46:56Z** (build `74a5e3df`) — before anyone asked it to. **Always pass
   `--region asia-northeast1` to `gcloud builds *` in this project.** The republish trigger is on **LDR, not main** — so
   a UTL fix reaches the base image on the quickmerge, not on the promote.
3. **`gcloud storage ls -l` prints `creation_time`, NOT `blob.updated`** (new, 2026-07-17) — the consolidator's
   changed-shard + prune logic reads `blob.updated`. These differ whenever anything touches an object without rewriting
   it; here a **COLDLINE lifecycle transition** moved cefi's legacy seed's effective mtime forward by **2 months**
   (`2026-05-12T17:06:19Z` creation vs `2026-07-14T03:17:52Z` updated). This is what made option A's literal stamp value
   wrong. **A GCS lifecycle storage-class transition silently advances `blob.updated` with no write, no content change,
   and no metadata strip.**
   - **Latent trap this implies** (no bucket is currently in this state — all 10 markers are ≥ their seed's `updated`):
     if a bucket's last real merge predates a seed's storage-class transition, the seed sorts **above** the cutoff → is
     classified CHANGED → **re-merged → resurrection of purged rows**. The `None`-marker (UNPROVABLE) branch is already
     immune (it explicitly excludes `_LEGACY_SEED_PATH`, `manifest_consolidator.py:783`), and the prune is immune
     (`:1856` skips the seed unconditionally) — the exposure is only the _incremental changed-shard_ path on a long-idle
     bucket. Flagged here rather than fixed: it is speculative, unobserved, and out of this issue's scope.

## Provenance

Found and recovered during `plans/active/sports_legacy_bucket_cutover_2026_07_16.md` T6.1 (2026-07-17). Full measured
narrative, before/after tables and evidence paths: that plan's Progress Log, entry **"✅ T6.1 MERGE COMPLETE"**.
