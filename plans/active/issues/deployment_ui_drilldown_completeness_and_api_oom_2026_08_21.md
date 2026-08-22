---
doc_type: issue
title: Deployment-UI data-status drill-down completeness + deployment-api OOM (panels intermittently failing)
summary: >-
  Two coupled operator asks (2026-08-21, with screenshot): (1) the data-status drill-downs are
  incomplete — each service view should drill to ITS OWN shard grain (instruments by instrument at the
  dumped shard level; MTDS by data_type → instrument_type/chain → venue; prediction by its TWO category
  axes: coarse category + canonical_question_group), with per-shard-per-day completion % (the
  manifest's whole point), a click-to-download CSV for EVERY shard (parquet→CSV server-side, not a
  sample), and a click-to-view per-shard schema (day-independent); (2) various panels error out — the
  screenshot's Prediction catalogue "Unknown error"/0-categories is root-cause-LED by
  uts-shared-deployment-api hitting its 16 GiB Cloud Run memory limit TWICE in the 90 min before
  investigation (10:50:36Z + 10:57:00Z, "16626 MiB used"), OOM-killing in-flight requests — 8
  deployment_api modules read availability indexes whole (the defi index is now 7.5GB/161.8M rows) and
  the prediction catalogue loads a 302MB parquet per 5-min cache miss; the whole-index pattern-debt
  census (sibling issue) swept only */scripts and MISSED the API package. Investigation complete;
  implementation handed to the next session with the code map + verification recipes below.
status: open
nature: issue
asset_group: [cefi, defi]
stage: [data]
repos: [deployment-ui, deployment-api]
scope: [engineer]
tags: [deployment-ui, deployment-api, data-status, drilldown, csv-export, schema, oom, cloud-run]
related:
  [
    /plans/active/issues/whole_index_script_pattern_debt_2026_08_21.md,
    /codex/06-coding-standards/ui-testing-layers.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: "2026-08-21"
author: interactive session (slot-2)
priority: P1
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["operator ask + screenshot 2026-08-21 (Prediction catalogue: Unknown error, All categories (0))"]
drift_direction: advance-code
context_scope:
  [
    deployment-ui/src/components/DataStatusTab.tsx,
    deployment-ui/src/components/DataStatusDrilldown.tsx,
    deployment-ui/src/components/PredictionCatalogue.tsx,
    deployment-api/deployment_api/routes/data_status/,
    deployment-api/deployment_api/services/data_status_drilldown/,
    deployment-api/deployment_api/services/prediction_catalogue.py,
  ]
---

## Part 1 — panels intermittently failing: deployment-api is OOMing (measured, today)

**Evidence** (all captured 2026-08-21 ~11:30Z):

- Cloud Run `uts-shared-deployment-api` (region asia-northeast1, memory limit **16Gi**, maxScale 20)
  logged `Memory limit of 16384 MiB exceeded with 16626 MiB used` at **10:50:36Z and 10:57:00Z** —
  the ONLY two occurrences in 24h, i.e. this started today. An OOM-killed instance aborts every
  in-flight request; the UI's fetch rejects and `PredictionCatalogue.tsx`'s catch renders the
  screenshot's "Unknown error" with category counts left at their empty default ("All categories
  (0)"). Any other panel whose request rides a dying instance fails the same way — this is the
  "various parts aren't loading" symptom class, NOT per-panel bugs.
- `prod/catalog.parquet` (bucket `instruments-store-pred-prd-…`) EXISTS, 301,972,070 bytes, updated
  01:08Z today — so the catalogue's 0-rows is NOT missing data. Its reader
  (`services/prediction_catalogue.py:180-183`) downloads all 302MB and `pd.read_parquet`s it behind a
  5-min TTL cache — a multi-GB RSS spike per cold read, per instance.
- **8 modules in the deployment_api package read `availability_index` directly**:
  `scripts/data_status_rollup_worker.py`, `routes/deployment_freshness.py`,
  `routes/data_status/{__init__,_catalogue,_axis_census,_live_coverage,_coverage_scope}.py`,
  `routes/health_consolidator/_reads.py`. The defi index is now **7.5GB compressed / 161,763,519
  rows** (doubled in 12 days — see the sibling pattern-debt issue for the measured decode blowup:
  54.5GB RSS for a whole-frame read). A couple of concurrent index-touching requests plausibly clears
  16GiB. **Census correction**: the sibling issue's fleet census swept only `*/scripts` — the
  deployment_api package (a 16GiB-capped SERVER, the worst place for whole-frame reads) was missed.
- The service already ships per-request memory instrumentation
  (`deployment_api/utils/request_memory_profiling.log_rss_delta`) — a first implementation step is
  reading its emission format from that file and querying Cloud Logging for the top per-request RSS
  deltas around 10:50Z (my quick `textPayload:"rss_delta"` probe returned nothing in 6h — check
  whether it logs under jsonPayload or a different marker before concluding it's off).
- Direct API probing needs auth (`X-API-Key` or Firebase Bearer — anonymous curl → 401), so reproduce
  through the UI or with the key.

**Fix shape** (implementer's choice of sequencing): (a) stopgap — raise the Cloud Run memory limit
(one flag) to stop the user-facing bleeding; (b) real fix — convert the API-package index/catalogue
readers to column-projected + row-group-streamed reads (the sibling issue's
`migration_common.stream_filter_parquet` pattern; those helpers live in deployment-service, so either
replicate the ~80-line pattern in deployment_api or do the sibling issue's [DESIGN] UTL-helper move
first); (c) verify by watching `textPayload:"Memory limit"` stay silent for 24h and the Prediction
catalogue panel loading. Note the catalogue reader is already column-projected but still loads all
row groups of 302MB into pandas per cache miss — cache the projected frame across requests
process-wide (it already does, 5-min TTL) AND consider longer TTL + pre-warm, or push the faceting
into row-group-filtered reads.

## Part 2 — drill-down completeness: what exists vs what the operator wants

**Current state (verified in code, 2026-08-21):**

- UI: `deployment-ui/src/components/DataStatusTab.tsx` (7,038 lines, per-service views) +
  `DataStatusDrilldown.tsx` (1,354). The drill-down's `ShardRow` type ALREADY carries the multi-axis
  optional fields — `chain`, `canonical_question_group`, `feature_group`, `timeframe` (from
  `data_status_multi_axis_shard_propagation_2026_05_06.md` Phase 3) — and there is ALREADY a
  SchemaContract panel fetching columns for (category, instrument_type, data_type, [venue]).
- Backend: `routes/data_status/_downloads.py` is a capture-status-aware CSV download route (captured →
  parquet→CSV 200; empty_confirmed / attempted_failed → explanatory CSV bodies — the branch table is
  in its header comment). `services/data_status_drilldown/` already has `_core.py`, `_csv_export.py`
  (with `build_csv_export`, `build_fixtures_csv_export`, `build_instruments_shard_csv_export`,
  `build_mtds_shard_csv_export`), `_instruments.py`, `_schema.py`, `_fixtures_pools.py`. Per-day
  per-shard completion already flows through the dual-scope rollup
  (`data_status_rollup_worker.py` → `{service}/full.json.gz`, read by `/api/data-status/manifest`).

**The ask, distilled from the operator (2026-08-21):**

1. **Instruments view**: drill down BY INSTRUMENT, at whatever shard grain instruments-service dumps
   (its manifest shard atom) — not stopping at venue/data_type.
2. **MTDS view**: breakdown by MTDS data_type → instrument_type/chain → venue.
3. **Prediction**: TWO category axes — the coarse 7-bucket `category` AND
   `canonical_question_group` — both already modeled in `services/prediction_catalogue.py` and the
   `ShardRow.canonical_question_group` field; the drill-down should use them.
4. **Axes are service-dependent**: fields that don't exist for a service simply don't render — drive
   each service's drill order from ONE config map (service → ordered axis list), derived from the
   fields actually present in that service's rollup shard atoms; do NOT hardcode per panel.
5. **Per-shard-per-day completion %** on every shard row ("the whole point of the manifest") — the
   rollup already carries this; the UI work is rendering it at every drill level, not inventing data.
6. **CSV download for EVERY shard** (operator explicit: not a sample — every shard, click →
   download; server converts parquet → CSV). Prior art exists (see builders above) — the work is
   coverage: audit which service views expose a download affordance at leaf rows, extend the builder
   set for services lacking one, and wire the button into `DataStatusDrilldown` leaves everywhere.
   HARD CONSTRAINT: the conversion endpoint must stay bounded-memory (per-day-per-shard parquets are
   small — `_csv_export.py`'s own comment says rarely >500k rows — but never read a consolidated
   index whole in the API process; that is Part 1's outage).
7. **Per-shard schema, day-independent** ("schema doesn't stay the same per day — it IS the same, so
   show it at shard level"): click a shard → its schema. Prior art: the SchemaContract UI panel
   (contract-side) + `_schema.py` service. Recommended completion: also read the ACTUAL parquet
   footer schema of one recent captured object (`pq.read_schema` on one blob — cheap, bounded) and
   render contract vs actual side by side, so contract drift ("the seam in the shards") is visible in
   the drill-down.

**Verification recipe per service** (gate any `- [x]` on this + the UI playwright rule —
`[UI]` tick needs `pw:L2 ✓` + a cited regression spec per `/codex/06-coding-standards/ui-testing-layers.md`):
drill instruments → an instrument-grain leaf; MTDS → data_type → instrument_type/chain → venue leaf;
prediction → category → cqg leaf; at each leaf: completion % visible per day, CSV downloads a real
captured shard, schema renders without picking a day.

## Todos

- [ ] [INFRA] P1. Stop the deployment-api OOM. STOPGAP DONE 2026-08-21 (~14:0xZ): live service bumped
      16Gi/4cpu -> 32Gi/8cpu (revision `uts-shared-deployment-api-00688-8jv`; Cloud Run needs 8 CPU
      above 24Gi), and deploy-shared.sh's literal landed as `deployment-service@6ef5ba27c2`.
      CORRECTION 2026-08-22: that pass mis-identified the sizing SSOT — the live 32Gi revision was
      reverted to 16Gi by the next promotion (00695, four hours later), because the deployment-api
      REPO's own `cloudbuild.yaml` deploy step (`gcloud run deploy --memory 16Gi --cpu 4`, run by the
      deployment-api-main-deploy trigger) re-sets resources on EVERY promotion; deployment-service's
      root cloudbuild.yaml belongs to deployment-dashboard and was a red herring. Live re-applied as
      revision `00699-cx7`; the real fix LANDED 2026-08-22 ~11:4x local as
      `deployment-api@7ed11bd12b` (cloudbuild.yaml deploy step -> 32Gi/8; verified on origin) +
      `deployment-service@ea7243f093` (deploy-shared.sh comment retracted to "must match
      deployment-api's cloudbuild.yaml") — every promotion now deploys 32Gi, the revert window is
      CLOSED. Landed via a load-gated auto-ship watcher after the parked window below. (Historical
      parked-state record, kept for the lessons:) the ship had been **SHIP PARKED
      2026-08-22 ~07:40 local**: the laptop sat at load average 300+ (peers' gates) — every
      deployment-service re-gate timed out its launcher-script tests at 300s (two identical runs), and
      deployment-api's quickmerge could not pass STAGE 1 because UAC/DS origins moved faster than the
      isolated-worktree setup. Both edits are NAMED STASHES in the slot-2 checkouts (+ scratchpad
      copies): deployment-service `slot2-deploy-shared-sizing-comment-fix-2026-08-22` (comment-only) and
      deployment-api `slot2-deployment-api-32gi-cloudbuild-2026-08-22` (the one that matters); the
      `qm-iso-evac-*` stash entries beside them are quickmerge's own leftovers of the same edits — drop
      after landing. RESUME when `uptime` load is sane (<~20): in each repo `git pull --ff-only origin
      live-defi-rollout` (CHECK `git status --porcelain` is empty FIRST — a pull over a peer's dirty tree
      autostashes their WIP; it happened to unified-api-contracts' stash@{0} this morning), then
      `git stash pop stash^{/slot2-deploy-shared}` -> quickmerge deployment-service
      `--files 'scripts/cloud-run/deploy-shared.sh'`; then `git stash pop stash^{/slot2-deployment-api-32gi}`
      -> quickmerge deployment-api `--files 'cloudbuild.yaml'` (deployment-service is its path-dep: DS
      FIRST, and clean). UNTIL the deployment-api change lands, every promotion re-sets the live service
      to 16Gi/4 — re-apply `gcloud run services update uts-shared-deployment-api --region asia-northeast1
      --memory=32Gi --cpu=8` if the UI starts erroring again.
      REMAINING (box stays open for it): confirm top per-request RSS offenders via the existing
      `log_rss_delta` instrumentation (read its emission format first) and land the real fix —
      column-projected / row-group-streamed reads for the 8 index-reading modules listed in Part 1 +
      the 302MB catalogue load. Verify: zero `Memory limit` log lines for 24h; Prediction catalogue
      loads.
- [ ] [CODE] P1. Census addendum on the sibling pattern-debt issue: extend the whole-index census to
      the `deployment_api` package (and any other SERVER packages — the original sweep was
      `*/scripts` only); fold the 8 files above into its remediation todos.
- [ ] [UI] P2. Per-service drill-down axis completeness per "The ask" items 1-5 (single axis-config
      map, service-dependent axes, completion % at every level). Playwright evidence per the recipe.
- [ ] [CODE] P2. CSV-download coverage for EVERY service's leaf shards (item 6): audit existing
      builder coverage (`build_{csv,fixtures_csv,instruments_shard_csv,mtds_shard_csv}_export`), add
      missing per-service builders, wire the affordance into every leaf row. Bounded-memory only.
- [ ] [CODE] P2. Day-independent per-shard schema affordance (item 7): contract + actual-footer
      schema (one-object `pq.read_schema`), rendered from the drill-down leaf.
- [ ] [UI] P3. Error UX: `PredictionCatalogue.tsx` (and siblings) collapse backend failures into
      "Unknown error" — surface the API error body/status so an OOM-class outage is distinguishable
      from an empty catalogue in one glance.

## Progress Log

- **2026-08-21 (interactive session, slot-2 — investigation only, per operator instruction to
  document before /pre-compact)**: all findings above verified directly (Cloud Run logs, live 401
  probe, blob existence/size, code map of both repos). No code changed under this issue. The OOM is
  the likely single cause of the screenshot error AND the "various parts aren't loading" class; the
  drill-down/CSV/schema asks are mostly WIRING over existing backend machinery, not greenfield.
