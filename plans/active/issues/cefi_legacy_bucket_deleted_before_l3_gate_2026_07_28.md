---
doc_type: issue
title:
  cefi legacy bucket (`market-data-tick-cefi-central-element-323112`) was DELETED 2026-07-14 — 10+ days before this
  plan's own L3 gate (false-phantom fix, gap-fill, E5 rebuild, E7 verify) was even attempted
summary: >-
  Re-ran the "bucket-state evidence" todo (line ~280) fresh: the `-prd` bucket has grown 5x since the 2026-06-02
  baseline (7,899,854 live objects, current through day=2026-07-27 — no longer 17-days-stale) and IS healthy. But the
  LEGACY bucket this todo compares it against, `market-data-tick-cefi-central-element-323112`, no longer exists —
  confirmed 404 via `gcloud storage buckets describe`. Cloud Audit Logs show `storage.buckets.delete` by
  ikenna@odum-research.com on 2026-07-14T11:02:29Z (asia-northeast1), i.e. ~14 days before today and, critically, ~10
  days BEFORE this very plan's sibling doc (`legacy_bucket_dual_write_decommission_2026_07_24.md`, dated 2026-07-24)
  still asserts "cefi ... stays open" / "Do NOT delete an AG's legacy bucket while its L3 plan is open" — a confirmed
  plan-vs-reality drift. This plan's own L3 gate (false-phantom itype/underlying-drift fix, `--also-legacy` gap-fill of
  5,233 legacy-only cells, E5 rebuild, E7 verify all C-GREEN) has NOT been met as of 2026-07-28 (see the 2026-07-28
  slot-8/10/12 Progress Log entries in this same plan) — meaning the legacy-bucket delete happened well before its own
  documented precondition. A pre-migration snapshot exists
  (`gs://central-element-323112-pre-migration-snapshot/market-data-tick-cefi-central-element-323112/`) but is dated
  ~2026-05-16 and only ~136MB (looks like a manifest `_index` snapshot, not the full raw-tick corpus), while legacy
  writes continued through day=2026-05-24 per this plan's own text — an ~8-day window of legacy-only writes that may not
  be covered by any backup.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [cefi, bucket-decommission, data-correctness, legacy-bucket, plan-drift, gcs]
related:
  [
    ../data_completion_cefi_2026_07_15.md,
    ../legacy_bucket_dual_write_decommission_2026_07_24.md,
    ../cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md,
  ]
created: "2026-07-28"
source: data_completion_cefi_2026_07_15.md "Orphan sweep + bucket-state evidence" todo re-run (slot-3, data_engineering)
resolved_by:
locked_by:
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

## What I found

Dispatched todo: `data_completion_cefi_2026_07_15.md` line ~280, "Orphan sweep + bucket-state evidence (slot/Harsh
bucket-state verification 2026-06-02)" — a diagnostic todo carrying a 2026-06-02 measurement (`-prd` 1,545,850 live
objects, ~65% of legacy's 2,377,168, `-prd` ~17 days stale). Re-verified live rather than trusting the ~2-month-old
number, per this plan's craft north-star (correctness is the heartbeat, no trusting stale baked-in evidence).

**Fresh `-prd` measurement (2026-07-28, GCP Cloud Monitoring `storage.googleapis.com/storage/v2/total_count`, single
targeted MQL query on `market-data-tick-cefi-prd-central-element-323112`, no corpus walk):**

```
live-object:        7,899,854   (was 1,545,850 on 2026-06-02 — 5.1x growth)
soft-deleted-object: 4,612,973
```

Delimited `raw_tick_data/by_date/` listing (single level, not recursive) shows the newest partition is `day=2026-07-27`
— **`-prd` is current, not stale.** The original todo's "~17 days STALE" characterization is itself now stale and should
not be trusted going forward without a fresh re-check each time.

**Critical finding — the legacy bucket this todo's whole comparison depends on is GONE:**

```
$ gcloud storage buckets describe gs://market-data-tick-cefi-central-element-323112
ERROR: (gcloud.storage.buckets.describe) gs://market-data-tick-cefi-central-element-323112 not found: 404.
```

Cloud Audit Logs (Admin Activity, default-on, no Data Access logging needed for a bucket-level op) confirm:

```
timestamp:     2026-07-14T11:02:29.017002502Z
methodName:    storage.buckets.delete
principal:     ikenna@odum-research.com
resourceName:  projects/_/buckets/market-data-tick-cefi-central-element-323112
location:      asia-northeast1
user-agent:    google-cloud-sdk gcloud/546.0.0 command/gcloud.storage.buckets.delete ... client-os/MACOSX ... interactive/False
```

No `storage.objects.delete` events precede it in the Admin Activity log (expected — object-level CRUD needs Data Access
audit logging, which is off by default; a prior bulk-purge of the bucket's ~2.3M live + 3.81M noncurrent objects would
not show up here even if it happened). One day earlier (2026-07-13), the SAME decommission pattern was executed for
**prediction** (`legacy_bucket_dual_write_decommission_2026_07_24.md` line 135-137: "prediction: DONE 2026-07-13 ...
confirmed 404"), which is the closest analog — it's plausible the operator ran the same playbook for cefi immediately
after, but this plan's own explicit gate says that must wait for cefi's L3 (this very plan) to reach C-GREEN first (line
134 of the sibling decommission plan: **"Do NOT delete an AG's legacy bucket while its L3 plan is open — prediction/cefi
hold legacy-only history"**, and line 138: **"cefi/defi/tradfi/sports unaffected, this item stays open for them"** —
written 2026-07-24, ten days AFTER the actual cefi deletion, i.e. the decommission plan's own text doesn't know the
deletion already happened).

**cefi's L3 gate (this plan) is still NOT met as of today (2026-07-28)** — see this plan's own Progress Log:

- 2026-07-28 (slot-12): multi-year phantom dry-run FAILED (`phantom_to_failed=490,639`, ~8.6% of the index) — the
  false-phantom itype/underlying-drift bug (`cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`) is
  unresolved.
- 2026-07-28 (slot-8): the post-walk CF audit re-run is STILL RED (v9=97.4%, source blank=24.0%, pipeline_mode
  blank=1.4%, Era-B chain rows=490,332 — none of the four GREEN criteria met).
- 2026-07-28 (slot-3, prior session): built the `--drop-stale` tool but explicitly did NOT run it against prod; the
  `--also-legacy` gap-fill (5,233 legacy-only cells) has never executed.

So the legacy bucket was deleted roughly **two weeks before** the plan's own required precondition chain (false- phantom
fix → gap-fill → E5 rebuild → E7 verify C-GREEN) was even attempted, let alone satisfied.

**Partial mitigation — a pre-migration snapshot exists, but is old and looks metadata-only:**

```
gs://central-element-323112-pre-migration-snapshot/market-data-tick-cefi-central-element-323112/raw-tick-2026-05-16/_index/
```

`gcloud storage du --summarize` on that prefix reports only **~136.5 MB** total — far too small to be the actual
raw-tick parquet corpus (the live legacy bucket held 2,377,168 live objects at ~910 objects/day-dir per this plan's own
per-year-distribution table); this looks like a manifest `_index` snapshot only, not a data backup. The snapshot is
dated `2026-05-16`, but this plan's own text says legacy's last write day was `2026-05-24` — **an ~8-day window
(2026-05-16 → 2026-05-24) of legacy writes is not obviously covered by any backup**, and the previously-identified 838
legacy-only cells (examples cited in the archived `cefi_manifest_canonicalisation_2026_06_01.md`: dates 2026-03-21,
2026-05-14, 2026-05-20 — some inside, some outside that window) were never confirmed migrated to canonical before the
bucket vanished.

## Why it matters

1. **Possible unrecoverable data loss.** If any of the (at-least-838, possibly more by 2026-06-01) legacy-only cells
   were never copied into the `-prd` canonical bucket before 2026-07-14, that data is very likely gone — GCS bucket
   deletion is not a soft/reversible operation in this gcloud SDK (`gcloud storage buckets list --soft-deleted` is not a
   recognized flag on the installed SDK, 569.0.0), and the only backup found is a small, ~2-month-old, probably
   metadata-only snapshot.
2. **Plan-corpus is now factually wrong.** Two active plans (`data_completion_cefi_2026_07_15.md`'s own "Orphan sweep
   - bucket-state evidence" / E4 gap-fill / E8 delete todos, and `legacy_bucket_dual_write_decommission_2026_07_24.md`
     line 123-154's "L6 decommission" + "version-aware delete" todos for cefi) all describe pending work — reading
     legacy for gap-fill, sweeping orphans against it, purging its versions, deleting it — against a bucket that **no
     longer exists**. Any worker picking up those todos as literally written would either fail confusingly against a 404
     or (worse) skip the now-impossible legacy-read step and falsely claim the todo done.
3. This is exactly the class of finding CLAUDE.md's "Governance + safety HARD RULES" calls a **big finding**
   (data-pipeline-correctness + cross-plan SSOT contradiction) requiring operator notification, not a quiet fix.

## Urgent — affects the just-landed consolidated plan

`plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` (slot-4, landed while this doc was being
written) still describes, as live executable work: **Phase C** ("E4b: legacy→canonical gap-fill", line 104-112 —
`MIGRATION_EXTRA_ARGS="--also-legacy" ... launch-canonical-migration-vm.sh` reading the legacy bucket for the 5,233-cell
gap-fill) and **Phase F** ("E8: legacy bucket delete", line 134-142 — "permanently delete the legacy
`market-data-tick-cefi` bucket"). **Both target a bucket that no longer exists** (confirmed 404 above, deleted
2026-07-14). Whoever picks up Phase C will get an immediate, confusing failure against a 404; Phase F is a no-op delete
of something already gone. This needs reconciling in that plan BEFORE either phase is dispatched — flagging here rather
than editing that plan directly (main has designated slot-4 as sole owner/consolidator of this plan to avoid a same-file
collision; this issue doc is the citable evidence for slot-4/main to fold in).

## Recommended decision

1. **[OPERATOR] Confirm intent.** Was the 2026-07-14 `market-data-tick-cefi-central-element-323112` deletion a
   deliberate, informed decision (e.g., the operator independently verified via some out-of-band check that the 838-cell
   gap was already closed, or accepted the loss), or was it an accidental extension of the 2026-07-13 prediction
   decommission run to cefi by mistake? This determines whether any recovery effort is warranted at all.
2. **[DATA] If recovery is warranted**, check whether any OTHER backup exists beyond the ~136MB snapshot found here
   (e.g. a fuller snapshot under a different prefix/bucket, a BigQuery external-table copy, or a downstream consumer
   that already ingested the legacy-only cells) before concluding data is lost.
3. **[DATA] Reconcile the now-moot todos** in both plans — do not attempt to execute the `--also-legacy` gap-fill,
   orphan sweep, version-aware delete, or "E8 legacy-bucket delete" steps as literally written; they all target a bucket
   that is already gone. Mark them superseded-by-fait-accompli (with a pointer to this issue doc) rather than leaving
   them looking like live, executable work.
4. **[DATA] Update `legacy_bucket_dual_write_decommission_2026_07_24.md`'s "L6 decommission" row** (line 123-139) and
   its "version-aware + orphan-aware delete" row (line 141-154) to note cefi is ALREADY bucket-deleted (not "stays
   open") — the current text is misleading to the next reader.

## Todos

- [ ] [OPERATOR] P0. Confirm whether the 2026-07-14 `market-data-tick-cefi-central-element-323112` deletion was
      intentional/informed or accidental, and whether any data-loss risk (the ~8-day 2026-05-16→05-24 window, plus any
      of the 838+ legacy-only cells never confirmed migrated) is accepted or needs recovery effort. (repo:
      unified-trading-pm — decision doc, no code)
- [ ] [DATA] P1. Once the operator's call above lands: reconcile `data_completion_cefi_2026_07_15.md`'s E4 orphan-
      sweep/gap-fill todo (line ~307) and the "NEXT SESSION — execute the migration" P0 todo (line ~227) — both
      currently describe reading/sweeping the legacy bucket, which no longer exists; mark them superseded or re-scope to
      "canonical-form fix only, no legacy read" as appropriate. (repo: unified-trading-pm)
- [ ] [DATA] P2. Update `legacy_bucket_dual_write_decommission_2026_07_24.md` lines 123-154 (the "L6 decommission" and
      "version-aware + orphan-aware delete" rows) to reflect cefi's legacy bucket is ALREADY deleted (2026-07-14), not
      "stays open" — the current text contradicts live GCP state. (repo: unified-trading-pm)
- [ ] [DATA] P2. Check for any additional cefi legacy backup beyond the ~136MB `_index`-only snapshot at
      `gs://central-element-323112-pre-migration-snapshot/market-data-tick-cefi-central-element-323112/` (e.g. a fuller
      raw-object copy under a different prefix, or a BigQuery external table) before concluding the 2026-05-16 to
      2026-05-24 window is unrecoverable. (repo: unified-trading-pm — investigation, cite findings back here)
