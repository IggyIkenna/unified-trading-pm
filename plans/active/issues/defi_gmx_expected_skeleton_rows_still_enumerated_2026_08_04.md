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
last_updated: "2026-08-04"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
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

- [ ] [DIAG] P1. Locate the actual IS instrument-catalogue artifact (bucket + object path, or code path if it's not
      GCS-backed) that `enumerate_expected_universe.py`'s Layer-1 skeleton-builder reads for the DEFI asset group, and
      confirm whether it still lists a GMX pool instrument.
- [ ] [DATA] P1. (Gated on the above.) If confirmed, prune the stale GMX catalogue entry (or rebuild the catalogue from
      current source, whichever this workspace's established catalogue-maintenance convention is) and re-run the
      honest-coverage `--asset-group defi` measurement to confirm the 4 `expected_unattempted` rows stop reappearing.
- [ ] [DIAG] P2. Check whether DRIFT/PACIFICA (removed 2026-07-16, per
      `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`) have the same class of surviving catalogue
      residue — same root-cause family as this finding, not yet checked.

## Progress Log

- **interactive session 2026-08-04 (`/autonomous`)**: filed after the operator directly asked "did you purge the
  manifest" — this session's own GCS-object purge (4 orphan liquidations objects, unrelated cell) had been reported
  without a direct manifest-side check; a targeted follow-up check found these 4 DIFFERENT rows in the live manifest.
  Corrects the "zero remaining live gmx/gmx_v2 references found anywhere checked this pass" claim in
  `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`'s Progress Log — that claim was accurate for the
  generated-bundle + source-registry surfaces it was scoped to, but this manifest-skeleton surface was not checked at
  the time and is not clean. Not resolved this session — context budget exhausted; filed for a fresh follow-up.
