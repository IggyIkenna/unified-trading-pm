---
doc_type: issue
title:
  "CRITICAL — the MDT legacy sports bucket (market-data-tick-sports-central-element-323112) was manually deleted by the
  operator on 2026-07-17, BEFORE the planned 5-step recovery (mdt_legacy_canonical_row_gap_2026_07_16.md) ever ran a
  single step — the ~550,062 legacy-only tick keys / ~2,081 objects it was tracking are now PERMANENTLY LOST (confirmed
  past the 7-day GCS soft-delete window, not present in the project's 39 currently-soft-deleted buckets)"
summary: >-
  Dispatched to execute STEP 1 (read-only) of `mdt_legacy_canonical_row_gap_2026_07_16.md`'s 5-step legacy→canonical
  recovery. Before writing the read-only script, live-verified the legacy bucket
  (`market-data-tick-sports-central-element-323112`) still existed — it does NOT: `gcloud storage buckets describe`
  returns 404, and the bucket is absent from `gs://` project listing entirely (only `-prd-`/`-test-` variants remain).
  Cloud Audit Logs confirm `storage.buckets.delete` fired 2026-07-17T17:05:17Z, principal `ikenna@odum-research.com`,
  via `gcloud storage rm` from a MacOS client — a MANUAL operator action, NOT via this AO plan's gated STEP 6 (which
  explicitly requires "CHECKPOINT WITH OPERATOR BEFORE STEP 6 (irreversible)" and was never reached — the source doc's
  own Progress Log confirms STEPS 1-5 were never executed, only planned). Checked GCS soft-delete recovery directly via
  the JSON API (`?softDeleted=true`): the bucket is NOT among the project's 39 currently soft-deleted buckets (sibling
  buckets deleted around the same window, e.g. `execution-store-sports-central-element-323112`, show `hardDeleteTime` ~7
  days after their `softDeleteTime` — by the same 604800s retention policy this bucket's `hardDeleteTime` would have
  been ~2026-07-24T17:05Z, already passed as of this session, 2026-07-25T02:41Z). **The data is gone, not merely hard to
  reach.**
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [sports, mdt, data-loss, gcs, bucket-delete, critical, operator-action]
related:
  [
    /plans/active/issues/mdt_legacy_canonical_row_gap_2026_07_16.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: 2026-07-25
priority: P0
parent_epic: sports_master
source: "[DATA] slot 7, sports_satellite_ao_dispatch_batch2-033, pre-implementation live verification"
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# MDT legacy sports bucket deleted before the planned recovery ran — data permanently lost (2026-07-25)

## What I found

Dispatched `sports_satellite_ao_dispatch_batch2-033` — STEP 1 (read-only) of the 5-step MDT legacy→canonical recovery in
`mdt_legacy_canonical_row_gap_2026_07_16.md`. Before writing the containment-check script, live-probed the legacy bucket
rather than assuming it still existed (the doc's most recent entries are 8 days old):

1. `uv run python` via `get_storage_client().list_blobs(...)` on `market-data-tick-sports-central-element-323112` →
   `google.api_core.exceptions.NotFound: 404 ... The specified bucket does not exist.`
2. `gcloud storage buckets describe gs://market-data-tick-sports-central-element-323112` → `404 not found`.
3. `gcloud storage buckets list --filter="name~market-data-tick-sports"` → only `-prd-` and `-test-` variants exist; the
   flat (no env-tier) legacy name is absent entirely.
4. **Root cause located via Cloud Audit Logs** (`protoPayload.methodName="storage.buckets.delete"`,
   `resourceName:"market-data-tick-sports-central-element-323112"`):
   ```
   timestamp: 2026-07-17T17:05:17Z
   principalEmail: ikenna@odum-research.com
   methodName: storage.buckets.delete
   callerSuppliedUserAgent: google-cloud-sdk gcloud/546.0.0 command/gcloud.storage.rm ... client-os: MACOSX
   ```
   A direct, manual `gcloud storage rm` from the operator's own machine — not this AO plan's STEP 6 (which the source
   doc gates behind an explicit operator checkpoint and which its own Progress Log confirms was never reached; STEPS 1-5
   show zero execution, only the 2026-07-17 planning entry).
5. **Checked soft-delete recoverability directly** (the CLI here has no `buckets restore`/`undelete` subcommand, so used
   the JSON API): `GET https://storage.googleapis.com/storage/v1/b?project=central-element-323112&softDeleted=true`
   returned 39 currently-soft-deleted project buckets — `market-data-tick-sports-central-element-323112` is **not among
   them**. Sibling buckets deleted in the same window (e.g. `execution-store-sports-central-element-323112`,
   `softDeleteTime=2026-07-18T21:49:09Z`) show a `hardDeleteTime` exactly 7 days (604800s) later. Applying the same
   retention to this bucket's 2026-07-17T17:05:17Z delete time puts its `hardDeleteTime` at ~2026-07-24T17:05Z —
   **already passed** as of this session (2026-07-25T02:41Z). The bucket has been hard-deleted, not merely soft-deleted;
   it is not recoverable via GCS's own restore mechanism.

## Why it matters

- The entire premise of `mdt_legacy_canonical_row_gap_2026_07_16.md`'s 5-step recovery plan — recovering ~550,062
  legacy-only tick keys (524,486 pre-match + 25,576 in-play) across ~32 gap days / ~2,081 objects into canonical — is
  now **categorically impossible**. There is nothing left to read. STEPS 1-5 as currently written cannot be executed by
  any future worker, ever, against this bucket.
- **The deletion happened BEFORE the 2026-07-17 planning session that authored the "MDT RECOVERY EXECUTION PLAN"** (or
  at best, same-day but the planning entry never re-verified the bucket post-delete) — meaning that plan was written
  against a premise that may already have been false at authoring time, and **no session since has actually touched the
  bucket to notice** (confirmed via this session's own Explore-agent research: zero execution activity logged for STEPS
  1-5 in the 8 days since). This session is the first to actually attempt contact with the bucket since the delete.
- This is a genuine, irreversible data-loss event on a production bucket, discovered mid-execution of an actively
  AO-dispatched recovery task — exactly the class of finding CLAUDE.md's HARD RULE requires operator notification for
  (data-correctness, cross-repo, contradicts an active plan's stated premise).
- **Open question for the operator** (genuine judgment call, not something a worker should decide unilaterally): was
  this bucket deletion intentional and informed (i.e., the operator had already independently decided the legacy data
  wasn't worth recovering, making this whole 5-step plan moot from their side), or was it an accidental/unrelated
  cleanup action that unknowingly destroyed data an active plan was still tracking as recoverable? The answer changes
  what "closing this out correctly" looks like — either archive the recovery plan as moot-by-operator-decision, or treat
  this as a genuine incident worth a retrospective on why an active AO plan's target data disappeared without the plan
  being updated.

## Recommended decision

1. **Confirm with the operator directly** whether the 2026-07-17T17:05:17Z deletion of
   `market-data-tick-sports-central-element-323112` was a deliberate, informed decision to abandon the legacy-recovery
   effort, or an unintended side effect of unrelated cleanup.
2. **Regardless of intent, the 5-step recovery in `mdt_legacy_canonical_row_gap_2026_07_16.md` can no longer be executed
   as written** — its STEPS 1-5 should be marked `BLOCKED` (data source gone) rather than left as pending
   AO-dispatchable work; a future worker should not be re-dispatched against this todo without first reading this doc.
3. **Re-assess T2.10 (seed purge) and T4.1 (object-layer proof) independently** — those two steps' preconditions
   (`_index/per_vm/_legacy_seed.parquet` phantom-row purge; legacy-bucket `unique==0` object-layer proof) may still be
   partially actionable even though the row-recovery itself cannot happen, since T2.10 operates on the INDEX (which
   still exists) not the deleted bucket's raw objects — a future session should check this specifically rather than
   assume the whole 5-step chain is dead.
4. **No further AO dispatch against `sports_satellite_ao_dispatch_batch2-033`'s original scope** until the operator
   responds — re-attempting STEP 1 will just re-discover the same 404 every time.

## Todos

- [x] ✅ [OPERATOR] P0. Confirm with the operator whether the 2026-07-17 legacy-bucket deletion was deliberate or
      accidental — **answered 2026-07-25 via `AskUserQuestion`: DELIBERATE, abandon recovery.** No retrospective needed;
      `mdt_legacy_canonical_row_gap_2026_07_16.md` archives its execution plan as moot.
- [x] ✅ [DATA] P1. Marked `mdt_legacy_canonical_row_gap_2026_07_16.md`'s STEP 1-6 execution plan permanently BLOCKED
      (banner + inline marker added, this doc cross-referenced) — `unified-trading-pm@bb527cbd6`. T2.10 re-assessed:
      genuinely independently actionable (operates on `_index/per_vm/_legacy_seed.parquet`, the still-live manifest
      index, never touches the deleted bucket's objects) but has **no existing tooling** — scoped as its own follow-up
      below rather than rushed.
- [ ] [DATA] P2. Build + run the T2.10 seed-purge: strip the 37,114 phantom `api_football × trades` rows (captured,
      nonzero `instrument_count`) from `_index/per_vm/_legacy_seed.parquet` with the NULL-safe COALESCE `source` filter
      (211,313 real `odds_api × trades` rows survive) — back up the index first, let the consolidator re-merge, verify
      by content. (repo: market-tick-data-service). **Done when**: the 37,114 phantom rows are gone from the live index,
      verified via a fresh count query, with 0 collateral loss to the 211,313 real rows. — **🟡 APPEARS MOOT, checked
      2026-07-25T04:56Z (slot 2)**: direct targeted read (single-object, not a corpus walk) of the CURRENT
      `gs://market-data-tick-sports-prd-central-element-323112/_index/per_vm/_legacy_seed.parquet` (362,753 rows,
      **frozen 2026-07-17T15:47:54Z — a day AFTER** the original T2.10 measurement that produced the "37,114 phantom"
      count, which lives in `mdt_legacy_canonical_row_gap_2026_07_16.md`, dated 2026-07-16) found: `trades` rows =
      232,098 total = **211,313 `source=odds_api` + 20,785 `source=polymarket_clob`, exactly** — zero rows with
      `source=api_football`, zero rows with `source` NULL. The described 37,114 phantom rows are not present under
      either interpretation of the "NULL-safe COALESCE" predicate. Most likely explanation: this seed file was
      re-frozen/regenerated at some point after the 2026-07-16 measurement (its freeze timestamp is newer), and whatever
      produced the phantom rows in the OLDER seed generation the original measurement read is not present in the current
      one. **Did not run a purge against rows that don't exist.** Before re-dispatching this todo, a future session
      should either (a) re-derive the phantom-row predicate from scratch against the CURRENT seed content (this check
      found none under the described predicate, but a different column/value combination might still hold the real
      phantom population — not exhaustively ruled out here), or (b) if genuinely clean, close this todo as moot with
      that evidence rather than re-attempting the original 2026-07-16 recipe verbatim.

## Codex SSOTs

None new — this is an incident report on an already-tracked recovery plan's premise, not a new durable contract.
