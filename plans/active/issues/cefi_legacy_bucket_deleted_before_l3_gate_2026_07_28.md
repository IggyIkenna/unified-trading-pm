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

## Attempted read-only migration-before-delete verification — INCONCLUSIVE, do not trust either number

Main asked whether the legacy-only cells were migrated to canonical `-prd` before the 2026-07-14 delete. Attempted a
read-only check using the pre-migration snapshot's manifest index (no corpus walk — two single-file parquet reads):

- `gs://central-element-323112-pre-migration-snapshot/market-data-tick-cefi-central-element-323112/raw-tick-2026-05-16/_index/availability_index.parquet`
  (2,632,931 rows, 1,300,463 `captured`, dated 2026-05-16)
- `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` (current, 9,212,011 rows,
  3,436,611 `captured`, through day=2026-07-27)

A naive `(date, venue, data_type)` cell-coverage diff (legacy `captured` cells not present in `-prd` `captured` cells)
returns **52,499 legacy-only cells** — an order of magnitude above the previously-cited 838 (2026-06-01) or 5,233
figures. Even after excluding the two obvious naming-drift causes visible in the raw venue/data_type vocabularies
(legacy carries bare pre-split venue names `OKX`/`COINBASE`/`BYBIT` that `-prd` has since split into
`OKX-{SPOT,FUTURES,SWAP}`/`COINBASE-{SPOT,FUTURES,CDE}`/`BYBIT-SPOT`; legacy carries `options_chain`/`futures_chain`
data_types that don't exist at all in `-prd`'s vocabulary — the already-tracked Era-B legacy-chain-form issue), a
**residual 39,651 cells** remain mismatched, spread across every major venue (KRAKEN-FUTURES 4,680, DERIBIT 4,395,
BITFINEX-FUTURES 4,017, ... down to LIGHTER-ZKSYNC 18) and every date from 2019-03-31 through 2026-05-07 — including
venue/data_type combinations that exist verbatim in both vocabularies (e.g. `KRAKEN-FUTURES`/`trades`), which rules out
simple naming drift as the sole explanation.

**This does NOT mean 39,651+ cells of real data are missing/lost.** This plan's OWN prior finding
(`cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`) proves that a naive exact-tuple manifest comparison
for this exact corpus produces false-mismatch rates in the tens-of-percent range (490,639/5.68M, ~8.6%) purely from
schema/normalization drift the naive compare doesn't account for (case, synonym, column-vs-path disagreement) — my quick
ad-hoc script almost certainly has the same class of blind spot (e.g. it does not account for any
`instrument_type`/`underlying` normalization, and treats `date` as a bare string). **I am NOT reporting a gap count
here** — neither "0" nor "39,651" nor "52,499" is trustworthy from this read-only pass. A reliable answer needs the
actual audit tooling's covered-keys normalization logic (the same one `rebuild_cefi_manifest.py`/CF-11 uses), run
properly, not a spreadsheet-style tuple diff. **Recording this as an OPEN verification item**: before anyone concludes
the legacy-only gap was (or wasn't) migrated before the 2026-07-14 delete, re-run a normalization-aware comparison
(ideally reusing the CF-11 covered-keys code path once its false-phantom bug is fixed) against this same pre-migration
snapshot file, since it's the only surviving copy of legacy's manifest state.

## Recommended decision

1. **[OPERATOR] Confirm intent. — ✅ ANSWERED 2026-07-28: "Yes, confirmed — it was a legacy bucket. Intent confirmed."**
   Was the 2026-07-14 `market-data-tick-cefi-central-element-323112` deletion a deliberate, informed decision (e.g., the
   operator independently verified via some out-of-band check that the 838-cell gap was already closed, or accepted the
   loss), or was it an accidental extension of the 2026-07-13 prediction decommission run to cefi by mistake? This
   determines whether any recovery effort is warranted at all. **Resolved**: deliberate legacy-bucket decommission, not
   accidental. Whether the specific ~8-day window / 838+ cells' loss is accepted vs. worth recovering was not separately
   addressed by this answer — proceed via the recovery-investigation todos below (check other backups; run the proper
   normalization-aware comparison) before treating it as settled either way.
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

- [x] ✅ [REVIEW] P0. **ANSWERED 2026-07-28 — OPERATOR DIRECT ANSWER: "Yes, confirmed — it was a legacy bucket. Intent
      confirmed."** The 2026-07-14 `market-data-tick-cefi-central-element-323112` deletion was a deliberate, informed
      decommission of a known legacy bucket, NOT an accidental extension of the prior day's `prediction` decommission
      run. This resolves the "deliberate vs accidental" half of this todo directly (business-fact-confirm — applied
      verbatim, not inferred). The operator's answer did not separately state "accept the loss" or "pursue recovery" for
      the ~8-day (2026-05-16→05-24) window / the 838+ legacy-only cells — that is a distinct question this doc cannot
      answer by guessing a fact, so it is NOT closed here by inference from "intent confirmed" alone. Per the operator's
      standing general ruling on full-completion (no accepting an open data-loss question on a shortcut, no
      half-measures on data-pipeline correctness): the correct next step is to EXHAUST the recovery-investigation
      avenues already scoped as their own todos below (check for any additional backup beyond the ~136MB snapshot; run
      the proper CF-11 normalization-aware legacy-vs-canonical comparison) before anyone concludes data is actually lost
      or accepts it as such — do not skip straight to "accept the loss" without that investigation completing first.
      Retagged away from `[OPERATOR]`/BLOCKED since the intent question itself is now answered; the remaining work is
      normal `[DATA]` investigation, already tracked below, not a second operator-only gate.
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
- [ ] [DATA] P1. Run a PROPER normalization-aware comparison (reusing the CF-11 covered-keys logic — the bug is now
      FIXED, see `plans/archive/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`) between the
      pre-migration snapshot's manifest index
      (`gs://central-element-323112-pre-migration-snapshot/market-data-tick-cefi-central-element-323112/raw-tick-2026-05-16/_index/availability_index.parquet`)
      and the current `-prd` manifest index — a naive `(date, venue, data_type)` tuple diff attempted here is
      INCONCLUSIVE (52,499 raw mismatches, 39,651 residual after excluding known naming-drift causes; see "Attempted
      read-only migration-before-delete verification" above) and must not be treated as a real gap count either way.
      (repo: market-tick-data-service)

## Progress Log

- **2026-07-28 (gated-decision retag sweep)** — Applied the operator's direct answer to the P0 confirm-intent todo:
  "Yes, confirmed — it was a legacy bucket. Intent confirmed." Retagged that todo from `[OPERATOR]` to `[x]` done
  (business-fact-confirm, applied verbatim, not inferred). The narrower "accept the loss vs. pursue recovery" question
  was not separately answered by the operator's response, so it is NOT closed by inference — the existing `[DATA]`
  recovery-investigation todos (additional-backup check, proper CF-11 normalization-aware comparison) remain open and
  are the correct next step before anyone concludes data is actually lost. Docs-only, no GCS/manifest action taken.
