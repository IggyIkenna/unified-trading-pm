---
doc_type: issue
title: GMX still enumerated into today's honest-coverage expected_unattempted skeleton, despite full 2026-07-25 removal
summary: >-
  Live-verified via a targeted (bounded, predicate-pushdown) read of
  `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` filtered to `venue=GMX`: 4
  rows remain, all `date=2026-08-04` (today), `chain=ARBITRUM`, `instrument_type=pool`, `data_type` in `{dex_pool_state,
  dex_pool_swaps, governance_events, position_data}`, `capture_status=expected_unattempted`, `row_count=0`. These are
  NOT the 4 orphan pre-purge liquidations objects deleted earlier this session (those were `day=2020-12-01`, `chain in
  {ARBITRUM,AVALANCHE}`, `instrument_type=lending`, `data_type=liquidations` — a fully separate cell). These are
  freshly-dated skeleton rows, meaning some enumerator (the Layer-1 `enumerate_expected_universe.py` v2
  skeleton-builder, per `/codex/02-data/honest-coverage-model.md`) is STILL treating GMX as a valid in-scope venue as of
  today — almost certainly triggered by this same session's own `--asset-group all` honest-coverage measurement run (see
  `/plans/active/issues/honest_coverage_cron_run_job_sa_missing_actas_uts_prd_sa_2026_08_03.md`, resolved same session).
  Checked instruments-service's own source (`reference_data/factory.py`, `reference_data/adapters/defi/morpho.py`,
  `engine/orchestrator/defi.py`, the dex-pool-glued-pair-id script) — all clean, only dated 2026-07-25 removal comments
  + one unrelated legitimate exception (a GMX-issued token accepted as Morpho vault collateral, a different namespace,
  same class as the UAC `defi_reserve_params.py` collateral entry). Did NOT locate the actual source before this session
  ran out of context budget — most likely the IS instrument/venue CATALOGUE itself (a data artifact, not code — e.g.
  `build_instrument_catalogue.py`'s output, or a similar reference-data store) still has a GMX pool instrument entry
  that was never pruned when the 2026-07-25 removal touched only Python source registries.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [defi, gmx, venue-removal, honest-coverage, manifest, instrument-catalogue, data-correctness]
related:
  [
    /plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md,
    /plans/active/issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md,
    /plans/active/issues/honest_coverage_cron_run_job_sa_missing_actas_uts_prd_sa_2026_08_03.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: "2026-08-04"
author: unknown
last_updated: "2026-08-04"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
source: >-
  Operator directly asked "did you purge the manifest" after this session's GMX-removal-follow-up work claimed (in
  deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md's Progress Log) "zero remaining live gmx/gmx_v2
  references found anywhere checked this pass" -- that claim is CORRECTED by this doc: the generated-bundle +
  source-registry sweep was genuinely clean, but a live manifest-skeleton surface was not checked and is not clean.
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    instruments-service/scripts/enumerate_expected_universe.py,
    instruments-service/instruments_service/reference_data/factory.py,
    /plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md,
  ]
---

# GMX still enumerated into today's honest-coverage expected skeleton

## What's confirmed

- 4 `venue=GMX` manifest rows exist as of this doc's filing, all dated `2026-08-04`, all
  `capture_status=expected_unattempted` (`row_count=0` — no actual data captured or claimed, just an "expect this cell
  to exist" skeleton entry).
- These are cleanly distinguishable from (and unrelated to) the 4 orphan pre-purge liquidations objects this session
  found and deleted from GCS (`day=2020-12-01`, `instrument_type=lending`, `data_type=liquidations` — see
  `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`'s "Fifth pass" entry). Those were dead historical
  artifacts; these are a LIVE re-derivation happening today.
- instruments-service's own Python source (the 4 files a repo-wide case-insensitive `gmx` grep matched) is clean — dated
  removal comments only, plus one legitimate unrelated exception (GMX token as Morpho collateral, not a venue).
- The row shape (`instrument_type=pool`, `data_type` axis spanning `dex_pool_state`/`dex_pool_swaps`/
  `governance_events`/`position_data`) matches a generic DEX-pool-protocol enumeration pattern, not anything
  GMX-perp-specific — consistent with the theory that a CATALOGUE data artifact (not source code) still lists a GMX pool
  instrument that the source-code-only 2026-07-25 removal never touched.

## What's NOT yet confirmed (the actual gap)

- The exact artifact/table/file that still declares GMX as an enumerable venue. Candidates, not yet checked:
  - The IS instrument catalogue's own committed/cached output (wherever `build_instrument_catalogue.py` or an equivalent
    writes its result — GCS bucket name not yet located this session; a guessed bucket name 404'd).
  - A stale row in the catalogue's underlying data store that a code-only removal pass never re-derives without an
    explicit catalogue rebuild.
- Whether this is a ONE-TIME artifact of this session's own `--asset-group all` honest-coverage trigger re-reading a
  stale catalogue snapshot (i.e., it would self-heal once the catalogue itself is fixed and the next nightly run reads
  it), or a standing daily recurrence that will keep re-appearing every day until fixed.
- Whether any OTHER dead venue (DRIFT, PACIFICA) has the same class of catalogue-level residue that a source-code-only
  removal similarly missed — not checked, out of this doc's scope, but the same root-cause class as this finding
  suggests it's worth a targeted check.

## Why not resolved this session

This finding surfaced at the very end of an already-long `/autonomous` session (honest-coverage IAM fix + a full GMX
generated-bundle sweep across 4 repos, prompted directly by the operator asking "did you purge the manifest" after this
session's own Progress Log entry claimed a completeness it hadn't actually verified on this specific surface). Finding
the actual catalogue artifact requires locating the right GCS bucket/build script (attempted once, wrong bucket name
guessed, 404) and is exactly the kind of thing that deserves a fresh, unhurried investigation rather than a rushed guess
under critical context pressure.

## Todos

- [x] [DIAG] P1. Locate the actual IS instrument-catalogue artifact (bucket + object path, or code path if it's not
      GCS-backed) that `enumerate_expected_universe.py`'s Layer-1 skeleton-builder reads for the DEFI asset group, and
      confirm whether it still lists a GMX pool instrument. ✅ **Artifact**:
      `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet` — written by
      `build_instrument_catalogue.py` (scheduled via `lifecycle_catalogue_scheduler.tf`, 01:00 UTC daily, using
      `instruments-service:latest`). Current catalog has **0 rows with venue=GMX** (79,002 rows total, updated
      2026-08-04T08:22:59Z). Pre-rebuild backup (`catalog.parquet.pre_cefi_reclassified_venue_purge_2026_08_04.bak`,
      08:22:49 UTC, 79,035 rows) also has 0 GMX rows — confirming the catalog was already clean when the daily 01:30 UTC
      enumerator ran today. July-22 backup (`catalog.20260722-025355.restakinglrt.bak.parquet`) confirms GMX was present
      before 2026-07-25 removal (1 row: venue=GMX, chain=ARBITRUM, instrument_type=POOL,
      instrument_id=0x489ee077994b6658eafa855c308275ead8097c4a, available_to=None). **Catalog does NOT still list GMX.**
      The 4 manifest rows are stale residue from a pre-cleanup enumerator run; the incremental manifest consolidator
      preserves old rows that no shard explicitly overwrites — they will persist until pruned.
- [x] [DATA] P1. ✅ (Gated on [DIAG] P1 above, now resolved.) Prune the 4 stale `venue=GMX` manifest rows from
      `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` and re-run
      `measure_honest_coverage.py --asset-group defi` to confirm they stop appearing. **Tag demoted [OPERATOR]→[DATA]
      per inline note:** (i) `gcs_bucket_soft_delete_retention_seconds()` for the manifest bucket = 604800s (≥604800s,
      effectiveTime 2026-05-12) — reversibility-verified per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`
      §3a. **Mutation scope**: NOT catalogue pruning (catalog is already clean). Needed: targeted removal of exactly 4
      rows
      `(venue=GMX, chain=ARBITRUM, instrument_type=pool, date=2026-08-04, instrument_id=0x489ee077994b6658eafa855c308275ead8097c4a,     data_type∈{dex_pool_state,dex_pool_swaps,governance_events,position_data})`
      from the consolidated manifest. Use `manifest_reprocess.py` (UTL) or a bounded pruning script (run via
      `run-bounded-analysis.sh`; manifest is 1.75GB so I/O is heavy — run on AO VM not local host per heavy-I/O rule).
      **Self-healing note**: the daily 01:30 UTC enumerator (clean catalog) will NOT re-seed these rows; once pruned
      they will not reappear. **DONE**: bounded DuckDB pruning script (ANALYSIS_MEM_CAP=12G, file-based I/O); rows
      42,192,496→42,192,492 (4 removed); captured count preserved at 26,448,553; targeted verification confirms 0
      venue=GMX rows remain in gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet.
- [x] ✅ [DIAG] P2. **DONE 2026-08-04.** Checked DRIFT/PACIFICA (removed 2026-07-16, per
      `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`) for surviving catalogue residue — **CLEAN:**
      (a) DeFi availability manifest
      (`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, bounded
      column-projected read via UTL `read_availability_index`): 0 rows with `venue=DRIFT` or `venue=PACIFICA`. (b)
      Instrument catalogue (`gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet`, full read via
      UTL `get_storage_client`, 79,002 rows): 0 rows with `venue=DRIFT` or `venue=PACIFICA`. Unlike GMX (whose
      2026-07-25 source-code-only removal left a catalogue entry → stale manifest skeleton), the 2026-07-16
      DRIFT/PACIFICA removal was more thorough (11 repos) and no residue survived. No further action needed.

## Progress Log

- **interactive session 2026-08-04 (`/autonomous`)**: filed after the operator directly asked "did you purge the
  manifest" — this session's own GCS-object purge (4 orphan liquidations objects, unrelated cell) had been reported
  without a direct manifest-side check; a targeted follow-up check found these 4 DIFFERENT rows in the live manifest.
  Corrects the "zero remaining live gmx/gmx_v2 references found anywhere checked this pass" claim in
  `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`'s Progress Log — that claim was accurate for the
  generated-bundle + source-registry surfaces it was scoped to, but this manifest-skeleton surface was not checked at
  the time and is not clean. Not resolved this session — context budget exhausted; filed for a fresh follow-up.
- **AO slot-16 backend_engineer 2026-08-04** (dispatch defi_gmx_expected_skeleton_rows_still_enumerated-001): **[DIAG]
  P1 COMPLETE.** Artifact located: `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet`
  (GCS-backed, built by `lifecycle-catalogue-regen-defi` Cloud Run Job at 01:00 UTC via `build_instrument_catalogue.py`,
  read by `expected-universe-v2-defi` enumerator at 01:30 UTC via `--catalog-path`). **Catalog is CLEAN**: 0 GMX rows in
  both current (79,002 rows) and pre-08:22 backup (79,035 rows). Root-cause of the 4 stale manifest rows: an older
  enumerator run (before the catalog was cleaned on 2026-07-25) seeded `expected_unattempted` rows for the GMX pool
  instrument; the incremental manifest consolidator preserves those rows because no shard has since written an override
  for those keys. Self-healing from daily enumerator alone is NOT sufficient — the enumerator adds rows from the clean
  catalog but never removes old rows not in its output. Manifest bucket soft-delete retention = 604800s (≥604800s) →
  [OPERATOR] P1 tag demoted to [DATA] P1 per §3a reversibility check. Mutation scope: targeted row pruning of 4 rows
  from `availability_index.parquet`, NOT catalog rebuild. Recommended: bounded pruning script on AO VM + re-verify.
- **AO slot-14 data_engineering 2026-08-04** (dispatch defi_gmx_expected_skeleton_rows_still_enumerated-004): **[DATA]
  P1 COMPLETE.** Pruned 4 stale `venue=GMX` rows from the DEFI availability manifest using a bounded DuckDB pruning
  script (`ANALYSIS_MEM_CAP=12G`, file-based GCS download/upload via UTL `get_storage_client()`). Rows confirmed:
  `chain=ARBITRUM, instrument_type=pool, date=2026-08-04, data_type∈{dex_pool_state,dex_pool_swaps, governance_events,position_data}`,
  all `capture_status=expected_unattempted, row_count=0`. Safety gates passed: (1) 0 captured rows in prune set, (2)
  `MANIFEST_PER_VM_SHARDS=true + VM_NAME=ao-slot-14` declared, (3) captured count preserved at 26,448,553
  (before=after). Total rows: 42,192,496→42,192,492. Targeted follow-up verification confirmed 0 venue=GMX rows in the
  uploaded manifest. Daily enumerator (clean catalog) confirmed will not re-seed. [DIAG] P2 (DRIFT/PACIFICA residue
  check) remains open.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): **RECLASSIFY, conflict-check CLEAR.** All 3
  open todos are bounded locate/confirm/fix/re-verify tasks over the IS instrument-catalogue + honest-coverage manifest
  with objectively checkable done-states, never previously assessed for AO eligibility (simply defaulted to NA at filing
  time). Conflict-check against all 16 active `defi_master` `assigned_vm:planning` docs (+finalize twins) and
  `defi_consolidated_closeout_2026_07_18.md` found zero verbatim/near-verbatim duplicate claim —
  `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s catalogue-expansion todo is a different, additive-only direction
  (widens the catalogue, never prunes) and structurally cannot have already fixed this. Flipped
  `assigned_vm: NA -> planning`, `execution_scope: local-only -> orchestrator-agent`. Retagged the `[DATA] P1`
  prune/rebuild todo to `[OPERATOR] P1` per finding O path (b) — the exact mutation mechanism is unknown until the
  `[DIAG] P1` todo locates the artifact, so no safe-idempotent/reversibility-verified justification (path (a)/(c)) can
  be stated yet; the executing worker resolves the tag once `[DIAG] P1` lands (see inline note on that todo). No
  companion finalize plan authored — `doc_type: issue`, structurally exempt from the finalize-plan-coverage rule per
  `cursor-configs/skills/na-eligibility-audit/SKILL.md` Phase 3 (`check_finalize_plan_coverage.py` only globs
  `plans/active/*.md`, not `plans/active/issues/*.md`); ordinary archival applies once this doc's own todos close.
- **slot-12 data_engineering 2026-08-04** (dispatch `defi_gmx_expected_skeleton_rows_still_enumerated-003`): **[DIAG] P2
  COMPLETE.** Checked both surfaces (bounded live reads, not corpus walks) — (a) DeFi availability manifest via UTL
  `read_availability_index` with column projection: 0 rows `venue∈{DRIFT,PACIFICA}`; (b) instrument catalogue
  (`gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet`, 79,002 rows, full read via UTL
  `get_storage_client`): 0 rows `venue∈{DRIFT,PACIFICA}`. Verdict: CLEAN — unlike GMX (whose 2026-07-25 source-code-only
  removal left catalogue residue → stale manifest skeleton), the 2026-07-16 DRIFT/PACIFICA removal was more thorough (11
  repos) and no residue survived. No further action needed. All todos in this doc are now done; doc is archival-eligible
  (no `locked_by`, all checkboxes flipped).
- **context-scout 2026-08-05**: re-scouted; all todos now closed; context_scope re-verified (4 entries), unchanged.
