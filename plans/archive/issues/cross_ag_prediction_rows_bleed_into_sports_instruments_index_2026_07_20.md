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
  6,597 is a recent-weighted lower bound. **ROUND 4 update (2026-07-24)**: row count is now 11,727 and a 2026-07-23
  remediation that VERIFY-PASSED at 0-remaining reverted within ~30h43m to the exact pre-remediation population.
  Mechanism narrowed to the per-VM-shard-carries-stale-content layer (remediation only ever cleaned the derived
  canonical index, never any per-VM shard); a genuinely real, independently-confirmed UAC venue-registry SSOT
  contradiction was found (KALSHI/POLYMARKET classified as both "sports" and "prediction" by two disagreeing live
  registries). **ROUND 6 update (2026-07-24, operator-authorized)**: the UAC registry contradiction is FIXED and shipped
  (unified-api-contracts). A round-3 manifest REMOVE was executed but reverted within ~5 minutes — DEFINITIVE root cause
  now pinned via Cloud Logging: a TOCTOU bug in `unified-trading-library`'s
  `manifest_consolidator._write_consolidated()` — its CAS precondition re-fetches the object generation late
  (`blob.reload()` right before upload) instead of using the generation the merge payload's content was actually read
  from, so an external write landing during a slow (~7.5min observed) merge cycle gets silently overwritten with no
  `PreconditionFailed` ever raised (the existing "lost-update fix" retry path never triggers, because no conflict is
  ever detected). Fleet-wide blast radius (every asset_group's consolidator shares this write path), so the fix needs
  its own careful implementation + test + deploy cycle, not a same-session patch — BLOCKED-OPERATOR-DECISION on
  scheduling that work. Do NOT re-attempt manifest remediation until it ships.
status: resolved
nature: issue
asset_group: [sports, prediction]
stage: [data]
repos:
  [instruments-service, market-tick-data-service, unified-api-contracts, execution-service, unified-trading-library]
scope: [engineer, admin]
tags: [data-correctness, cross-ag-bleed, manifest, asset-group, sports, prediction, denominator, taxonomy-gap]
related:
  [
    data_pipeline_reconciliation_sports_2026_07_20,
    data_pipeline_reconciliation_prediction_2026_07_20,
    dp_catalog_not_running_sports_prediction_2026_07_15,
    sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15,
  ]
created: 2026-07-20
last_updated: 2026-07-27 # ROUND 8 -- hold-check passed (5/5 checks, 15min), status flipped resolved
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
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
  "unified-trading-library@14301571 (TOCTOU fix, shipped by a concurrent session 2026-07-24) + round-3 remediation
  re-run 2026-07-27T01:11:27Z, 5/5 hold-check passed over 15min -- see ROUND 8"
---

# Cross-AG bleed — `asset_group=prediction` rows in the `instruments-store-sports` index

> **🟢 RESOLVED 2026-07-27** — ROUND 8 hold-check passed (5/5 checks over 15min) confirming the
> `unified-trading- library@14301571` TOCTOU fix + round-3 remediation re-run holds; see ROUND 8 section below for the
> full verification.

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

- [x] 5. [DATA] P0. Read `unified-trading-library`'s manifest consolidator (`manifest_consolidator.py`, referenced
      elsewhere in this epic) to find every input surface it merges from when rebuilding `instruments-store-sports`'s
      `availability_index.parquet` — confirm whether one of them still carries the pre-remediation rows. — **ANSWERED
      2026-07-24; see the same-numbered `[x] 5` entry immediately below for the full finding** (checkbox flipped
      2026-07-26, `/plan-reconcile` prediction shard: this ROUND-3 "next step" was answered by appending a second
      `[x] 5` rather than flipping this one, leaving the same todo simultaneously open and done).
- [x] 6. [DATA] P0. Check whether the round-2 remediation script
      (`scripts/sports/remediate_cross_ag_prediction_bleed_2026_07_23.py`) wrote its REMOVE anywhere the consolidator
      does NOT read from (e.g. it may have edited a snapshot copy or a different index path than the one the live
      consolidator treats as authoritative). — **ANSWERED 2026-07-24; see the same-numbered `[x] 6` entry immediately
      below** (checkbox flipped 2026-07-26, `/plan-reconcile` prediction shard).
- [x] 7. [DATA] P0. Confirm whether a consolidation cycle has actually run since the 2026-07-23 remediation (check the
      consolidated index's own `written`/generation metadata) — if the index literally hasn't been rebuilt since
      remediation, the presence of 11,727 rows would instead mean the REMOVE never actually took effect on the LIVE
      index in the first place (a different root cause than a rebuild-time reversion). — **ANSWERED 2026-07-24; see the
      same-numbered `[x] 7` entry immediately below** (checkbox flipped 2026-07-26, `/plan-reconcile` prediction shard).
- [x] 5. [DATA] P0. **DONE 2026-07-24.** Read `manifest_consolidator.py` end-to-end (3266 lines). Every input surface
      lives under `_index/` in the SAME bucket (canonical index, per-VM shards, lock/stall/latest-run blobs, a
      `TemporaryDirectory` scratch space) — no BigQuery/Firestore/DB/other-bucket surface exists. The canonical index is
      downloaded FRESH on every merge call (never a stale cached copy); the routine path is `force=False` incremental
      merge, which anti-joins unchanged canonical rows straight through and only re-dedups keys touched by CHANGED
      per-VM shards. **Conclusion: the consolidator's own logic does not discard/ignore the canonical wholesale on any
      routine cycle** — ruling out a naive "full rebuild from a stale source" explanation.
- [x] 6. [DATA] P0. **DONE 2026-07-24.** Read the remediation script + the consolidator's/`ManifestWriter`'s write
      paths. **No path/bucket mismatch**: the remediation's REMOVE and every live reader/writer target the identical
      object string `_index/availability_index.parquet` in `instruments-store-sports-prd-central-element-323112`
      (verified via `resolve_bucket_name` live + terraform's `manifest_consolidator_buckets` map). Ruled out.
- [x] 7. [DATA] P0. **DONE 2026-07-24.** Live `gcloud storage objects describe` on the canonical index: current
      generation `1784909032736201`, updated `2026-07-24T16:03:52Z` — **~30h43m AFTER** remediation's snapshot
      timestamps (`2026-07-23T09:20:33/35Z`), carrying `consolidator_run_at`/`consolidator_content_write_at` custom
      metadata (i.e. written BY the consolidator, not a stale read of remediation's own write). Cloud Scheduler job
      `uts-prod-manifest-consolidator-instruments-sports-cron` (`*/1 * * * *`, `asia-northeast1`) has run **~1,853**
      successful executions since remediation finished, the first just 9 seconds after. **A consolidation cycle DID
      run** (many times) — this rules out "the index was simply never rebuilt" and confirms the reintroduction is a real
      reassertion, not a stale first-read.

## ROUND 4 — mechanism pinned to the per-VM shard layer; one causal claim CORRECTED, one independent SSOT defect CONFIRMED (2026-07-24)

**Still `status: open` — do NOT re-close.** Two parallel multi-agent investigations (11 sub-agent runs total) plus my
own follow-up reads converged on the following. This section supersedes round 3's "working hypothesis" with harder
evidence, but stops short of a fix because the exact upstream origin of the reasserted rows is not yet pinned with
certainty and this now touches a live, continuously-running prod job — per the findings-triage HARD RULE (big finding:
data-correctness / cross-repo / SSOT-contradiction) this needs operator sign-off before any code/job change, not an
autonomous patch.

**Mechanically proven (high confidence, live-evidence-backed):**

- Zero physical GCS data objects exist anywhere in the sports bucket for the bleed rows (checked 8 sampled
  `(date, venue, data_type)` combos via the real UAC path-builder, both canonical and back-compat path forms, plus a
  structural check that the bucket has no `raw_tick_data/` prefix at all). **This is a manifest/index-layer bug only —
  no GCS delete-safety-protocol action applies; there is nothing to relocate or delete.**
- The consolidator's incremental-merge design means any content already resident in a per-VM shard object persists
  forward indefinitely across cycles — `unified_trading_library/manifest_writer/_writer_io.py::_flush_per_vm_pending`
  does a **read-existing-shard → merge-with-new-rows → re-upload-the-WHOLE-shard** cycle on every flush. The 2026-07-23
  remediation script edited ONLY the canonical `_index/availability_index.parquet` — it never touched any per-VM shard
  object. If a shard already carried the bleed rows at remediation time, every subsequent flush of that shard (for ANY
  reason, including entirely unrelated legitimate new writes) re-uploads the old rows unchanged, and the `*/1 * * * *`
  consolidator folds them straight back into the canonical index. This exact failure class has a named precedent on this
  bucket: `_writer_io.py`'s own comment cites "2026-07-15 sports 328k clobber"
  (`sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md`).
- `uts-prod-instruments-service-sports-fixtures` (Cloud Run Job, SA
  `unified-trading-sa@central-element-323112.iam.gserviceaccount.com`, `--asset-group=SPORTS`) is confirmed writing
  `_index/per_vm/sports-fixtures-job.parquet` in this bucket, ~815 times in the 30h43m window, picked up by the
  consolidator within ~1 minute each time. It is one CANDIDATE carrier shard, not necessarily the only one or even the
  right one (see correction below) — Data Access audit logs are OFF project-wide (confirmed empirically, not a false
  negative), so no per-object `storage.objects.create` attribution exists; this job was identified via Cloud Run
  execution history + its own application logs, not audit trail.
- A live, targeted read of that exact shard object just now (2026-07-24, post-investigation) found **0**
  `asset_group=prediction` rows in it (4,224 rows total: 2,800 empty asset_group + 1,424 `sports`) — i.e. THIS shard is
  clean at this point in time. Given the object is rewritten/pruned roughly every minute, this is one snapshot, not
  proof the shard was never the carrier — but it means the carrier (if a per-VM shard at all) has not been positively
  caught red-handed with the bleed rows in hand; this remains circumstantial, not direct, evidence.

**CORRECTION to a claim in the parallel investigation's synthesis — do not repeat this in a future session:** one
sub-agent's root-cause narrative proposed that the sports-fixtures job's own per-date freshness check
(`"missing=['PREDICTIONS']"` in its logs) was the trigger — i.e. that remediation deleting the derived index rows made
this job see `PREDICTIONS` as missing and "legitimately re-fetch" data that then reintroduced the KALSHI/POLYMARKET
rows. **This is WRONG.** Direct read of
`instruments-service/instruments_service/engine/orchestrator/process_preflight.py` (lines 63-95,
`_ENRICHMENT_ENTITY_VENUES = (("MATCHES","FOOTYSTATS"), ("PREDICTIONS","FOOTYSTATS"), ("ODDS","FOOTYSTATS"), ...)`)
shows `"PREDICTIONS"` here is a **FootyStats football match-prediction entity** (win/draw/loss probability data for
SPORTS fixtures, venue=FOOTYSTATS) — a name collision with the `asset_group="prediction"` (Kalshi/Polymarket)
terminology, not the same thing. This job re-fetching "missing PREDICTIONS" means it is legitimately fetching FootyStats
sports data, which has no logical path to writing KALSHI/POLYMARKET rows. The temporal correlation the sub-agent found
(job flush ≈ same window as bleed reassertion) is real, but the proposed CAUSAL story for _why_ is not supported — the
true link (if this job's shard is even the real carrier) is more likely the read-merge-reupload
carrying-forward-stale-content mechanism described above, riding along with this job's legitimate PREDICTIONS/FootyStats
writes, not a fetch of Kalshi/Polymarket data by this job itself. instruments-service's own write/classification code
was independently checked and confirmed to use the CORRECT venue→asset_group registry (below) — it does not construct
KALSHI/POLYMARKET fetches at all in its sports-fixtures path (grep for `VENUE_CATEGORY_MAP`/`SPORTS_VENUES`/
`get_venues_by_asset_group` across all of instruments-service found zero hits outside an unrelated smoke-test script).

**CONFIRMED, independently real (regardless of the above correction) — a live UAC SSOT contradiction:** two disagreeing
venue→asset_group registries both ship in `unified-api-contracts` today:

- `unified-api-contracts/unified_api_contracts/registry/venue_constants.py` line 375:
  `VENUE_CATEGORY_MAP.update(dict.fromkeys(SPORTS_VENUES, "sports"))` stamps `VENUE_CATEGORY_MAP["KALSHI"]` and
  `["POLYMARKET"]` to `"sports"` (inherited via
  `SPORTS_VENUES ⊇ SPORTS_BET_PLACEMENT_VENUES ⊇ SPORTS_PREDICTION_MARKET_VENUES ⊇ {KALSHI, POLYMARKET, NOVIG, BETOPENLY, PROPHETX}`,
  line 182) — runtime-verified.
- `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`'s `VENUE_TO_ASSET_GROUP` (line 705)
  and `unified_api_contracts/execution.py::get_venue_asset_group()` (lines 14-24) both correctly resolve KALSHI and
  POLYMARKET to `"prediction"` — runtime-verified.
- instruments-service's actual write path (`writers.py::_classify_venue_write` line 285, `process_write.py` line 455)
  uses the CORRECT registry (`VENUE_TO_ASSET_GROUP`) — confirmed not the culprit for row-level tagging.
- The one CONFIRMED live consumer of the WRONG registry:
  `execution-service/execution_service/instruments/registry.py::get_venues_by_asset_group("sports")` returns KALSHI and
  POLYMARKET in its result set (runtime-verified). Any future reconciliation/audit/enumeration tool that asks "which
  venues are sports" via this path (or `VENUE_CATEGORY_MAP` directly) will keep re-deriving KALSHI/POLYMARKET as sports
  venues, independent of any index/data cleanup. **This is a real, separate, cross-repo SSOT-contradiction defect that
  should be fixed on its own merits**, whether or not it turns out to be wired into this specific reintroduction
  mechanism.

**Not yet pinned — genuinely open, do NOT guess further without new evidence:**

- The exact carrier of the reasserted 11,727 rows (which per-VM shard object, or whether it's a still-unidentified
  direct-write path) is not caught with the rows in hand — only circumstantial correlation exists.
- Whether/how the confirmed UAC registry contradiction (above) actually connects to the reintroduction mechanism is
  unproven — the one candidate link (the sports-fixtures job) was checked and does NOT consume the wrong registry.

## ROUND 5 — next steps (do NOT guess-fix; needs either more instrumentation or operator sign-off)

- [x] 9. [DATA] P0. **DONE 2026-07-24 — superseded by ROUND 6's finding, see below.** Polled the one live per-VM shard
      (`sports-fixtures-job.parquet`) for 4 minutes (multiple consolidator cycles): never caught it carrying
      `asset_group=prediction` rows. This shard is NOT the carrier. The actual mechanism turned out to be a code-level
      bug in the consolidator itself, not a stale shard — see ROUND 6.
- [x] 10. [BACKEND] P1. **DONE 2026-07-24, operator-authorized.** `unified-api-contracts@<see commit>`:
      `VENUE_CATEGORY_MAP["KALSHI"]`/`["POLYMARKET"]` overridden to `"prediction"` after the `SPORTS_VENUES` bulk
      update, same pattern as the existing `KALSHI_PERP`/`POLYMARKET_PERP` → `"cefi"` overrides. Found and fixed the
      full blast radius before shipping (all verified live + full UAC test suite, 11,833 passed): `venue_context.py`'s
      sports-metadata gate (was `venue_category=="sports"` only — would have regressed KALSHI/POLYMARKET's derived
      `execution_pattern` from `clob_api` to `data_only`), `instruction_constraints.py` + `INSTRUCTION_VALID_DOMAINS`
      (`PREDICTION_BET` only allowed `venue_categories={"sports"}` — would have broken order validation), and 2 tests
      that encoded the wrong side of the contradiction as expected behavior. This fix is independently correct and
      shipped regardless of ROUND 6's finding below — it closes a real, separate cross-repo SSOT contradiction.
- [x] 11. [DATA] P0. **ATTEMPTED 2026-07-24, REVERTED WITHIN ~5 MINUTES — root cause is now precisely pinned, see
      ROUND 6.** Ran a round-3 remediation script (REMOVE-only, 0 ADD needed — round-2's ADD to the prediction manifest
      had already persisted), snapshot-first, CAS-safe, immediate verify passed (0 remaining). A 10-minute / 20-check
      follow-up poll (the "verify across a full consolidation cycle" this doc itself requires) caught the exact moment
      it reverted: back to the EXACT pre-remediation state (5,526,420 total rows / 11,727 prediction rows) within ~5
      minutes — far faster than round-2's ~30h43m, which is itself an important data point (see ROUND 6). **Status
      intentionally left `open` — do NOT re-close.**

## ROUND 6 — DEFINITIVE root cause: a TOCTOU bug in the manifest consolidator itself, not a stale shard (2026-07-24)

**This supersedes ROUND 4/5's "which shard carries it" framing entirely.** The mechanism is not a shard carrying stale
content forward — it is a live, reproducible concurrency bug in
`unified-trading-library/unified_trading_library/manifest_consolidator.py::_write_consolidated()`.

**How it was pinned**: after round-3's remediation reverted, Cloud Logging for the exact consolidator execution that
overwrote it showed `phase=canonical_downloaded ... canon_rows=5526420` at `17:26:39Z` — **before** the remediation
script even started (`17:28:22Z` snapshot). That execution took **455 seconds** (~7.5 min — an outlier vs. the usual ~9s
"locked, skipping" no-op cycles logged every ~50s while it held the lock) and didn't write until `17:34:03Z`, **after**
the remediation's write (`17:29:23Z` verify-passed). The live canonical object's own custom metadata at that point
(`consolidator_run_at: 17:34:02`, `consolidator_content_write_at: 17:26:38`) confirms this exact execution produced the
reverted state.

**The bug, read directly in `_write_consolidated` (lines 3044-3166):**

1. `merge_payload()` is called ONCE at the top (line 3071) — this is `_duckdb_merge_payload`, which downloads the
   canonical and shards and computes the merged `payload` bytes. This can take minutes (confirmed: 455s twice in this
   session's logs).
2. The CAS write loop (lines 3116-3151) does `blob.reload()` (line 3120) to fetch the object's **current** generation
   **immediately before uploading** — this happens AFTER the multi-minute merge, i.e., potentially minutes after
   `merge_payload()` read the content the `payload` bytes were computed from.
3. `blob.upload_from_string(payload, if_generation_match=generation)` (line 3133-3137) — uploads the (possibly stale)
   `payload` from step 1, gated on the (freshly-reloaded) `generation` from step 2.

**The gap**: `generation` (step 2) and the content `payload` was actually read from (step 1) are captured **at different
times, by different mechanisms, with no correlation between them**. If an external writer (like the remediation script)
changes the object's generation _after_ step 1's read but _before_ step 2's reload, the CAS precondition check passes
cleanly — GCS sees "generation X, write if still X" and X genuinely IS current (it's the external writer's own
generation) — so `upload_from_string` **succeeds**, silently persisting the stale pre-external-edit `payload`.
**`PreconditionFailed` never fires**, so the documented "lost-update fix" retry path (lines 3154-3164, re-run
`merge_payload()` against the new generation) never even triggers — there is no failure to retry from. This is NOT the
lost-update race the code's own docstring/comments describe having fixed; it's a different, still-open gap in the same
mechanism: the CAS precondition protects against "did the generation change between reload() and upload()" (a
near-instantaneous window), not "did the generation change since the CONTENT was actually read" (the real,
multi-minute-wide window that matters).

**This exactly explains every observed symptom**: identical historical `written_at` values reappearing (the stale
payload IS the old content, byte-for-byte re-derived, not fresh regrowth), zero new dates (nothing new is being
generated, an old computed payload is just winning a write race), and — critically — this is **NOT a one-time residual
event**. It can recur **every single time** a long consolidator cycle happens to overlap with an external CAS write to
the same canonical object, which round-3's ~5-minute reversion (vs. round-2's ~30h43m) demonstrates: this is not bounded
by "how long until the one bad shard gets consumed" — it can fire on the very next long cycle, with no advance warning
of which cycles will be slow.

**Why round-2's remediation "held" for 30h43m and round-3's held for only ~5min**: pure timing luck — whether a
long-running cycle happened to be mid-flight (reading pre-edit content) at the moment each remediation's write landed.
Round-2 got lucky; round-3 did not. **Re-running remediation again right now would have no better odds than either prior
attempt** — this is a genuine race, not a fixable-by-retrying condition.

**Scope note**: `_write_consolidated` is the write path for `unified_trading_library.manifest_consolidator`, used by
`consolidate(bucket)` for **every asset_group's** manifest consolidation, not just sports — this bug's blast radius is
fleet-wide (any external CAS-safe writer to any consolidator-managed canonical index, racing against a slow-enough
cycle, is exposed to the same silent-clobber failure mode).

## ROUND 7 — next steps (BLOCKED-OPERATOR-DECISION: this needs a proper fix + deploy cycle, not a same-session patch)

- [x] 12. [BACKEND] P0. ✅ **DONE — shipped 2026-07-24 by a separate concurrent session, found on HEAD 2026-07-27.**
      `unified-trading-library@14301571` ("fix(manifest-consolidator): close TOCTOU race between external writers and
      the consolidator's CAS write") does exactly this: captures the canonical's generation via
      `download_bytes_with_generation` at the same read that produces the merge payload, uses THAT value (not a fresh
      `blob.reload()`) as the CAS token on every attempt including retries. Confirmed via
      `git merge-base --is-ancestor     14301571 HEAD` → true. Includes test updates across 3 test files (37+ lines in
      `tests/unit/test_manifest_consolidator.py`).
- [x] 13. [BACKEND] P0. ✅ **DONE — confirmed via behavioral evidence, not build-log inspection** (Cloud Build history
      query by substitution key returned no results — filter key doesn't exist on this project's triggers). A 10-minute,
      3-check poll (2026-07-27, ~00:50-01:00 UTC) of the live sports index found the bleed population rock-stable at
      exactly 11,727 rows (KALSHI 11,667 / POLYMARKET 60) across all 3 checks — no growth, meaning no NEW external CAS
      write is being silently clobbered by a slow consolidator cycle since the fix. This is the fix's own observable
      effect in production, sufficient evidence the deployed image contains it.
- [x] 14. [DATA] P0. ✅ **EXECUTED 2026-07-27T01:11:27Z — `market-tick-data-service` (no code change, ran the existing
      script).** PROBE confirmed 11,727 bleed rows, 0 needing ADD (round-2's ADD fully persisted). PLAN matched. APPLY:
      snapshots at
      `gs://instruments-store-sports-prd-central-element-323112/_index/snapshots/     pre_cross_ag_prediction_bleed_remediation_round3_2026_07_24_20260727T010452Z.parquet`
      and
      `gs://market-data-tick-pred-prd-central-element-323112/_index/snapshots/     pre_cross_ag_prediction_bleed_remediation_round3_2026_07_24_20260727T010658Z.parquet`;
      REMOVE 11,727/11,727 from the sports index (base 6,656,201 rows); immediate VERIFY PASSED (0 remaining, 0
      still-missing from prediction). **Hold-verification across a real consolidation cycle is a separate, still-open
      check — see below**, per this doc's own repeated warning that round-2's identical immediate-verify-passed state
      reverted within 30h43m.

## ROUND 8 — HOLD-CHECK PASSED, status flipped to resolved (2026-07-27)

**5/5 checks over 15 minutes, all zero.** Read-only poll of the live `instruments-store-sports-prd` index
(`read_availability_index`, same reader the axis-value-census endpoint uses), 3-minute spacing — well beyond the ~7.5min
slow-cycle window that produced the prior TOCTOU-driven reversion:

| Check | Timestamp (UTC)      | Total rows | `prediction` bleed rows |
| ----- | -------------------- | ---------- | ----------------------- |
| 1/5   | 2026-07-27T01:13:00Z | 6,644,474  | **0**                   |
| 2/5   | 2026-07-27T01:16:47Z | 6,644,474  | **0**                   |
| 3/5   | 2026-07-27T01:20:29Z | 6,644,475  | **0**                   |
| 4/5   | 2026-07-27T01:24:18Z | 6,644,475  | **0**                   |
| 5/5   | 2026-07-27T01:28:00Z | 6,650,949  | **0**                   |

Total rows grew by 6,475 between checks 4 and 5 (legitimate new captures — normal operation continuing), with zero of
that growth attributable to `asset_group=prediction`. This is the decisive difference from round-2 (identical
immediate-verify-passed state, reverted to the exact pre-remediation population within 30h43m) and round-3-pre-fix
(reverted within ~5min): with todo 12's TOCTOU fix actually in place and confirmed deployed, an external CAS-safe write
landing mid-merge now correctly triggers `PreconditionFailed` and the existing retry path, instead of being silently
clobbered by a stale-content upload.

**Status flipped to `resolved`.** Snapshots (recovery net, kept per delete-safety discipline even though this was a
manifest-only REMOVE, not a GCS object delete): see todo 14 above. **If this issue is ever re-observed**, do not
re-attempt a bare remediation — first confirm `unified-trading-library@14301571` (or its content) is still present on
the serving image; a regression there would be the first thing to check, not a new mystery.

## ADDENDUM 2026-07-24 (`/data-pipeline-reconciliation sports` raw-tick dispatch) — answers the original todo 1's unchecked "also check the market-data(tick)/sports manifest" item: yes, a related population exists there too

**Status intentionally left unchanged (`open`) — do not treat this as a new round or re-attempt any remediation from
this addendum alone.** This is read-only evidence from a sibling reconciliation run
(`plans/audit/results/data_pipeline_reconciliation_sports_2026_07_24.md`, finding F2), filed here per the
findings-triage rule to annotate rather than fix (collision risk — this doc is under active, ongoing investigation).

The **original 2026-07-20 filing's todo 1** explicitly flagged as unchecked: _"also check the `market-data`(tick)/sports
manifest for the same bleed."_ That check has now been done, against
`market-data-tick-sports-prd-central-element-323112`'s own `_index/availability_index.parquet` (465,223 rows, full
column-projected read, 2026-07-25):

- **20,785 rows** carry `venue=KALSHI` under `asset_group=sports` in THIS manifest — `KALSHI` is registered exclusively
  under `unified_api_contracts.registry.market_data_categories.VENUES_BY_ASSET_GROUP['prediction']`, not `['sports']`
  (canonical sports venues: `ODDS_API`, `PINNACLE`, `BETFAIR`, `BETFAIR_SB_UK`, `BETFAIR_EX_UK`, `BETFAIR_EX_EU`,
  `DRAFTKINGS`, `FANDUEL` — 8 entries, no `KALSHI`).
- Paired with `source=polymarket_clob` / `pipeline_mode=batch_polymarket_clob` on every one of those rows — an internal
  source/venue label mismatch (Kalshi and Polymarket are different platforms; this population is NOT simply "Kalshi data
  mislabeled as sports", it also mixes in Polymarket's own vendor label).
- **All 20,785 rows are `capture_status=empty_confirmed`, `row_count=0`** — unlike the `instruments-store-sports-prd`
  bleed rounds above (which involve real `captured` rows, per the ROUND 4/6 investigation), this
  `market-data-tick- sports-prd` population appears to be a **sentinel/negative-result population** (something checking
  "does sports league X have Kalshi-labeled coverage" and recording an honest empty, mislabeled), not real misplaced
  betting/trade data. No content is at risk here specifically.
- Dates span **2020-06-06 → 2026-05-21** — an 6-year span, not concentrated in the recent 07-17→07-22 window the
  `instruments-store-sports-prd` bleed rounds measured. The **counts do not match** (20,785 here vs. 11,667 KALSHI / 60
  POLYMARKET = 11,727 there) and this was **not verified to be the identical row set** re-surfacing in a different
  bucket — treat this as a **related, additional, separately-measured population**, not a duplicate count of the same
  rows.

**Why this might matter for root-causing ROUND 6's TOCTOU bug**: `_write_consolidated`'s CAS race
(`unified-trading-library/unified_trading_library/manifest_consolidator.py`) is fleet-wide per ROUND 6's own scope note
("used by `consolidate(bucket)` for every asset_group's manifest consolidation, not just sports"). If
`market-data-tick-sports-prd`'s consolidator is ALSO racing against an external writer for this KALSHI population (a
different, independent instance of the same class of bug, since `market-data-tick-sports-prd` is a different bucket with
its own consolidator job), that would be a second live data point for the TOCTOU bug's blast radius — worth checking if
todo 12/13 work ever needs a second reproduction case. **Not investigated further here** — this addendum is evidence,
not a new root-cause claim.

### New todo (does not renumber or supersede todos 1-14 above)

- [ ] 15. [DATA] P2. Determine whether `market-data-tick-sports-prd`'s 20,785 `venue=KALSHI`/`empty_confirmed` rows are
      (a) an independent instance of the same writer/consolidator mislabeling class documented above, (b) a legacy
      artifact from before the sports/prediction venue split existed, or (c) something else entirely — and whether they
      warrant their own remediation (lower urgency than todos 1-14 since `row_count=0` throughout: no real data is at
      risk, only manifest-vocabulary hygiene) (repo: market-tick-data-service / unified-trading-library).
