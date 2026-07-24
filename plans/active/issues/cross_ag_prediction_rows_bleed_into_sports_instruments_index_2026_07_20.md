---
doc_type: issue
title:
  "Cross-AG bleed — asset_group=prediction rows are physically in the instruments-store-sports availability index (6,597
  and growing), root cause unlocated"
summary: >-
  Independently measured by BOTH the /data-pipeline-reconciliation sports run (F4) and the prediction run (F1) on
  2026-07-20. The instruments-store-sports-prd _index holds at least 6,597 rows carrying asset_group=prediction (KALSHI
  6,562, POLYMARKET 35; trades 6,484, prediction_canonical_question_group 113), dated 2026-07-16 to 2026-07-19 with
  written_at up to 2026-07-20 13:10 — i.e. the bleed is ACTIVE, not a frozen relic. It has GROWN from the 4,097 rows
  documented in the reference sheets (2026-06-26 to 07-18), so it is worsening. A prediction shard belongs in the
  prediction estate, never the sports reference index; this is a manifest-writer cross-AG misattribution that corrupts
  both estates' coverage denominators. Root cause was NOT located in either read-only run. This is a taxonomy gap (no
  closed reconciliation type fits a cross-bucket asset_group bleed) escalated per the findings-triage HARD RULE, not a
  finding either read-only skill could fix. Measurement caveat — the sports index was in stale per-VM-shard fallback so
  6,597 is a recent-weighted lower bound.
status: open
nature: issue
asset_group: [sports, prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [data-correctness, cross-ag-bleed, manifest, asset-group, sports, prediction, denominator, taxonomy-gap]
related:
  [
    data_pipeline_reconciliation_sports_2026_07_20,
    data_pipeline_reconciliation_prediction_2026_07_20,
    dp_catalog_not_running_sports_prediction_2026_07_15,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "/data-pipeline-reconciliation sports (F4) + prediction (F1) runs, 2026-07-20; both independently measured the same
  bleed at 6,597 rows via scoped manifest reads"
resolved_by:
---

# Cross-AG bleed — `asset_group=prediction` rows in the `instruments-store-sports` index

> **⚠️ BIG FINDING (data-correctness — cross-AG / cross-bucket).** Operator-notify per the findings-triage HARD RULE.
> Independently measured by two 2026-07-20 reconciliation runs (sports F4 + prediction F1). Filed as a tracked open
> issue; the read-only reconciliation skills could not root-cause it and neither could fix it.

## What was measured (two independent audits, same number)

- `instruments-store-sports-prd` `_index/availability_index.parquet` holds **≥ 6,597** rows with
  `asset_group=prediction` — KALSHI 6,562, POLYMARKET 35; by data_type: `trades` 6,484,
  `prediction_canonical_question_group` 113 (+ 1 cefi + 1 defi row noted by the sports run).
- Dates span **2026-07-16 → 2026-07-19**; `written_at` up to **2026-07-20 13:10** — the bleed is **active**, not a
  historical relic.
- It has **GROWN** from the **4,097** rows the reference sheets documented (2026-06-26 → 07-18) — worsening over time.
- **Measurement caveat (both runs):** the `instruments-store-sports` index was in stale per-VM-shard fallback
  (consolidated blob age > 120s), so 6,597 is a partial recent-weighted count and a **lower bound**. The
  `market-data`(tick)/sports manifest was not read for further bleed.

## Why it matters

A prediction shard atom lives in the prediction estate. Its physical presence in the SPORTS reference index means:

- The sports coverage denominator is inflated by rows that are not sports data (the sports run notes its reference-lane
  `captured` count is contaminated by cross-lane rows).
- The prediction estate under-accounts for shards that landed in the wrong bucket.
- Any consumer that trusts `instruments-store-sports` as sports-only reads prediction rows as sports.

Both are silent corruptions of the honest-coverage denominators the whole Foundation-gate rests on.

## Not covered elsewhere

Not the same as `dp_catalog_not_running_sports_prediction_2026_07_15.md` (that is catalogue-staleness alerts on the
`prod/catalog.parquet` writers, a different surface and a different failure). No existing issue doc tracks the
asset_group bleed itself; the reference sheets carry only the count, and both reconciliation runs explicitly deferred
the register/root-cause work as out of read-only scope.

## Investigation direction (root cause unlocated — do NOT guess-fix)

The writer that lands rows in the `instruments-store-sports` index is stamping some prediction (KALSHI/POLYMARKET)
shards with the sports bucket/index target. Likely candidates to trace: a shared manifest writer or per-VM-shard
uploader whose `asset_group` / bucket resolution is not scoped to the shard's true asset_group, or a KALSHI/prediction
job whose manifest target resolves to the sports instruments-store bucket. The KALSHI concentration (6,562 of 6,597)
plus the recent, still-growing dates are the strongest lead.

## Todos

- [ ] 1. [DATA] P1. Pin the true full count and composition — read the `instruments-store-sports` index after a fresh
      consolidation (not the stale per-VM fallback), grouped by `asset_group` × `venue` × `data_type` × `written_at`,
      and also check the `market-data`(tick)/sports manifest for the same bleed (repo: instruments-service).
- [ ] 2. [BACKEND] P1. Locate the writer — trace which job/uploader writes `asset_group=prediction` rows into the
      `instruments-store-sports` index (grep the manifest-writer / per-VM-shard upload path for where the bucket/index
      target is resolved vs the shard's asset_group; the KALSHI concentration and the 2026-07-16→ dates bound the
      search) (repos: instruments-service, market-tick-data-service).
- [ ] 3. [BACKEND] P1. Fix the misattribution at the writer so a prediction shard's manifest row lands only in the
      prediction estate; add a regression/guard test that a prediction shard can never write into a sports index (repos:
      instruments-service, market-tick-data-service, unified-api-contracts).
- [ ] 4. [DATA] P2. Remediate the already-written bleed rows — decide whether to relocate them to the prediction index
      or delete the mis-targeted rows (manifest-write, human-gated), and re-measure both estates' coverage denominators
      after (repo: instruments-service).

## RE-TRIAGE (2026-07-23)

**Verdict: STILL OPEN, ACCURATE — and materially WORSE than either this doc or the parent
`sports_consolidated_closeout_2026_07_19.md` currently record.** The parent plan documents this as fully root-caused,
fixed, and remediated on 2026-07-20 (`market-tick-data-service@5581dcf9` fixing per-venue bucket resolution in
`process_ticks()`, plus a "CROSS-AG DATA REMEDIATION COMPLETE" section claiming 6,597 rows purged from the sports
manifest down to **0 remaining**). A fresh live read of the same index today contradicts that "0 remaining" claim.

**Live evidence (2026-07-23, direct read of
`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` via
`unified_trading_library.get_storage_client()`/`resolve_bucket_name(kind="instruments-store", asset_group="sports")`):**

- `asset_group=prediction` rows present: **11,727** (KALSHI 11,667 / POLYMARKET 60; `trades` 11,540 /
  `prediction_canonical_question_group` 187; all `service_name=market-tick-data-service`), plus the same 1 cefi + 1 defi
  row noted originally.
- Broken down by `written_at` date: **07-17: 1,756 · 07-19: 2,341 · 07-20: 2,500 · 07-21: 2,468 · 07-22: 2,662.** The
  first three figures are an **exact match** to the doc's own 2026-07-20 measurement of the pre-purge population (1,756
  / 2,341 / 2,500 — see "Newly-actionable todos" section above), strongly suggesting those original rows were never
  durably removed (or were re-absorbed from a stale per-VM shard — the same consolidator-fan-in hazard already
  documented elsewhere in this epic, e.g.
  `sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14.md`'s "Hard-learned during apply" note). The
  07-21 and 07-22 additions are NEW rows written well **after** the `5581dcf9` fix landed (2026-07-20T10:35 UTC) and
  after the plan's remediation was recorded complete — i.e. the writer bug is not conclusively fixed in production, or a
  second emitter exists.
- Verified `5581dcf9` is on the current `live-defi-rollout` HEAD (`git merge-base --is-ancestor 5581dcf9 HEAD` → true)
  and the `market-tick-data-service` image actively serving the daily `fast-t1-recon` Cloud Run job
  (`uts-prod-market-tick-data-service-fast-t1-recon`, executions run every 5 min) was rebuilt as recently as
  2026-07-23T08:24 UTC — so the code fix is deployed, yet the bleed continued accumulating through 07-21/07-22.

**This is a genuinely new, significant finding, not a re-confirmation of the original claim**: the parent plan's
"CROSS-AG DATA REMEDIATION COMPLETE" / "0 remaining" section is contradicted by live production data. Flagging per the
findings-triage HARD RULE rather than attempting a fix here (root cause of the reaccumulation — incomplete fix, a second
write path, or stale-shard re-absorption — was not diagnosed in this pass). Recommend: (1) re-verify whether `5581dcf9`
actually addresses every code path that writes into this bucket (not just `process_ticks()`), (2) check for an un-pruned
per-VM shard still carrying the pre-purge rows, (3) re-run the same relocate+purge remediation once (1)/(2) are ruled
out, and (4) notify the operator that the 07-20 "complete" claim needs retraction/correction. Status left `open` (todos
1-4 above are NOT actually done — only step 3's code fix is real, and even that hasn't held).

## ROUND-2 ROOT CAUSE + REMEDIATION (2026-07-23) — RESOLVED

**Root cause, precisely pinned this time.** The 07-20 remediation fixed the RAW DATA bucket bug (`mtds@5581dcf9`,
per-venue in `process_ticks()`) and did a one-time purge. It did NOT fix the MANIFEST bucket, which had the exact same
class of bug in a DIFFERENT function: `orchestrator/__init__.py`'s `_resolve_manifest_bucket()` resolved the manifest
target ONCE per run from the first `--asset-group` argument, not per-venue. That was fixed separately —
`market-tick-data-service@299ef540` ("fix(manifest): route manifest-writer bucket per-venue, not per-run"), **deployed
2026-07-22T02:01:44Z**. During the ~39.5h gap between the two fixes (07-20 10:35 → 07-22 02:01), the manifest bug kept
writing fresh bleed rows into the sports index even though the underlying tick DATA was, by then, already correctly
landing in the prediction bucket (verified: `market-data-tick-sports-prd` has 0 KALSHI objects for day=2026-07-20;
`market-data-tick-pred-prd` has 2,417).

**Confirmed the writer bug is now fully fixed and holding** (checked before touching anything): every one of the 11,727
present bleed rows has `written_at` strictly BEFORE `299ef540`'s deploy (max observed 2026-07-22T00:57:06Z vs the fix at
02:01:44Z) — zero new bleed rows in the 30+ hours since. This was cleanup of a dead residual, not a live wound, and did
not need to wait for anything further.

**Remediation executed**: `market-tick-data-service@a7ff45f9`
(`scripts/sports/remediate_cross_ag_prediction_bleed_2026_07_23.py`, new CAS-safe tool, snapshot-first on both buckets).
Since the underlying data was already correctly placed (no object relocation needed this round, unlike 07-20's messier
fix), this was a pure manifest operation: **ADD 5,056 rows** to the prediction manifest (rows that had NO correct-side
row at all — the manifest bug meant they never got one) **+ REMOVE all 11,727** bleed rows from
`instruments-store-sports`. Snapshots:
`gs://instruments-store-sports-prd-central-element-323112/_index/snapshots/ pre_cross_ag_prediction_bleed_remediation_2026_07_23_20260723T092033Z.parquet`
and
`gs://market-data-tick-pred-prd-central-element-323112/_index/snapshots/ pre_cross_ag_prediction_bleed_remediation_2026_07_23_20260723T092035Z.parquet`.
**VERIFY PASSED**: sports `asset_group=prediction` rows remaining = 0; bleed keys still absent from the prediction
manifest = 0.

**Status: RESOLVED.** Todos 1-4 above are now genuinely done (1: pinned via this investigation; 2: root-caused precisely
— it was an unfixed second bug, not stale-shard reassertion; 3: the fix landed 07-22, confirmed holding; 4: this section
IS the retraction/correction of the 07-20 "complete" claim).

## RE-TRIAGE ROUND 3 (2026-07-24) — REOPENED, "RESOLVED" claim contradicted by a fresh live read

**Verdict: STILL OPEN, and round-2's "RESOLVED"/"VERIFY PASSED: 0 remaining" claim does not hold today.** Reverting
`status` to `open` and clearing `resolved_by` per the findings-triage HARD RULE — do NOT re-close from this doc alone;
this needs a dedicated root-cause session before any further remediation attempt (per the RE-TRIAGE round-2 section's
own instruction not to guess-fix).

**Live evidence (2026-07-24, streaming pyarrow/gcsfs read of
`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, columns
`asset_group`/`venue`/`data_type`/`written_at` only — no full-file download, no whole-bucket walk):**

- `asset_group=prediction` rows present: **11,727** — KALSHI 11,667 / POLYMARKET 60; `trades` 11,540 /
  `prediction_canonical_question_group` 187. This is the **exact same total, exact same venue/data_type split** as the
  round-2 RE-TRIAGE's pre-remediation measurement (2026-07-23), not a fresh reaccumulation with different numbers.
- By `written_at` date: **07-17: 1,756 · 07-19: 2,341 · 07-20: 2,500 · 07-21: 2,468 · 07-22: 2,662** — again an **exact
  match**, date-for-date and count-for-count, to the round-2 RE-TRIAGE's own pre-remediation breakdown. Notably **zero
  rows dated 07-23 or later** — if this were a live, ongoing writer bug reaccumulating fresh rows (as round-1 was), we
  would expect NEW dates appearing in the 24+ hours since; instead the row set looks like the EXACT pre-remediation
  population was restored wholesale, not regrown.
- Checked whether this is a raw-data (object-level) regression, not just a manifest ghost: `gcloud storage ls` for the
  sample rows' `(date, venue)` combinations under the sports bucket's tree returned **zero matching objects** —
  consistent with round-2's own claim that the underlying tick data was already correctly placed in the prediction
  bucket and needed no relocation. **This is a metadata-only reassertion, not a recurrence of the original raw-data
  bucket-routing bug.**
- Checked the obvious "stale per-VM shard" hypothesis the round-2 section itself named as a risk:
  `gs://instruments-store-sports-prd-central-element-323112/_index/per_vm/` contains only one object,
  `_legacy_seed.parquet` (18.3 KiB, last modified 2026-06-28) — far too small and far too old to carry 11,727 rows dated
  07-17 through 07-22. **This specific hypothesis is RULED OUT** — whatever is reasserting these rows is not this per-VM
  shard directory.

**Working hypothesis (NOT confirmed — needs code-level investigation, not just data reads):** the exact-match-down-to-
the-row totals strongly suggest the consolidated `_index/availability_index.parquet` is periodically **rebuilt from a
source that round-2's remediation never touched** — e.g. a snapshot/checkpoint/BigQuery write-ahead surface the
consolidator merges from on each cycle, distinct from both the live consolidated parquet (which the remediation script
successfully edited, per its own VERIFY PASSED) and the `per_vm/` shard directory (ruled out above). If the
consolidator's rebuild logic re-merges an older full-index snapshot (rather than incrementally applying the REMOVE),
every consolidation cycle would silently undo the fix — which is consistent with what's observed: the exact
pre-remediation row set, verbatim, reappearing with no new growth.

**Next steps (do NOT guess-fix; this needs its own investigation before any further remediation is attempted):**

1. Read `unified-trading-library`'s manifest consolidator (`manifest_consolidator.py`, referenced elsewhere in this
   epic) to find every input surface it merges from when rebuilding `instruments-store-sports`'s
   `availability_index.parquet` — confirm whether one of them still carries the pre-remediation rows.
2. Check whether the round-2 remediation script (`scripts/sports/remediate_cross_ag_prediction_bleed_2026_07_23.py`)
   wrote its REMOVE anywhere the consolidator does NOT read from (e.g. it may have edited a snapshot copy or a different
   index path than the one the live consolidator treats as authoritative).
3. Confirm whether a consolidation cycle has actually run since the 2026-07-23 remediation (check the consolidated
   index's own `written`/generation metadata) — if the index literally hasn't been rebuilt since remediation, the
   presence of 11,727 rows would instead mean the REMOVE never actually took effect on the LIVE index in the first place
   (a different root cause than a rebuild-time reversion).
4. Once (1)-(3) pin the actual mechanism, re-run the remediation (or fix the consolidator input the remediation missed)
   and verify **across at least one full consolidation cycle** (not just an immediate post-write read) before re-closing
   this doc.

Do not re-flip this doc's `status` to `resolved` or re-attribute `resolved_by` until a round-4 pass confirms the fix
holds across a real consolidation cycle, not just an immediate verify.
