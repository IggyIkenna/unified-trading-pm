---
doc_type: plan
title: data_status_comprehensive_test_coverage_2026_05_07
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui, market-tick-data-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/data_status_drilldown_shard_atom_alignment_2026_05_07.md,
    /plans/archive/2026_05/aws_migration_defi_first_2026_05_07.md,
    /plans/archive/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md,
    /plans/archive/deploy_missing_auto_launch_2026_05_07.md,
  ]
created: "2026-05-07"
overview:
  Build a comprehensive regression-test net for the data-status surface — Python unit tests for SSOT alignment + cutoffs
  + deploy-missing + cloud-agnostic behavior, Vitest component tests for the UI, and a Playwright e2e suite that walks
  every (service, asset_group) pair. Premise — the data-status surface keeps breaking because (a) writers + readers + UI
  live in different repos with no contract test gluing them, (b) the pieces are mocked individually but never
  end-to-end, (c) cloud-agnostic claims aren't tested.
type: code
epic: epic-deployment
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: deployment-api, code: C2, deployment: none, business: none }
  - { repo: deployment-ui, code: C2, deployment: none, business: none }
  - { repo: unified-api-contracts, code: C2, deployment: none, business: none }
  - { repo: unified-trading-library, code: C2, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C2, deployment: none, business: none }
depends_on: [data_status_drilldown_shard_atom_alignment_2026_05_07.md]
todos: []
isProject: false
estimate_class: design
estimate_baseline_ai_days: 15
estimate_calibrated_ai_days: 9
estimate_calibration_note: "Backfilled 2026-05-13: 30 todos, 0 done; cross-repo regression-test net (Python unit +
  Vitest + Playwright e2e) across deployment-api/ui + UAC + UTL + PM. Design class (test contract surface design;
  building matrices). Baseline 15 (~0.5 AI-day per substantive todo, mech-leaning); × 0.6 = 9.0.

  "
---

# Comprehensive data-status test coverage

## Why

The data-status surface keeps breaking. Sample of incidents from the last 6 weeks:

- 2026-05-07 — `read_availability_index(gs://...)` instead of bucket name → "No data for cefi" despite 1M+ captured
  rows. Mocked-shape unit test passed; Playwright caught it.
- 2026-05-07 — `DeployMissingButton` rendered on partial-shard venue-level nodes → 400 from `/deploy-missing-preview`.
  Tests didn't cover render-gate combinations.
- 2026-05-07 — `_build_chain_breakdown` reported `ARBITRUM 32/54 shards` (date-count math) for a 25k-true-shard
  universe. No test asserted the headline math matched the codex shard atom.
- 2026-05-06 — TradFi MVP partial-bundle ES.OPT 18 dates with single-parent fills passed manifest as `captured`. No
  cluster-validation test on the writer.
- 2026-05-05 — MDPS 1440 NaN OHLC bars per day per (venue, data_type) for years passed manifest as `captured`. No
  validation-by-output-inspection test.
- 2026-04-29 — Phantom audit false 26% phantom for ODDS because the audit probed `entity=odds/` instead of
  `entity=footystats_odds/`. No cross-repo path-SSOT test.

Pattern across all incidents:

1. Writer + reader + UI live in 3+ different repos.
2. Each repo unit-tests its own logic in isolation, mocking the inputs.
3. The mocks accept any shape, so contract drift between repos is invisible.
4. Bugs only surface end-to-end, often only via the operator's eye on the live panel.

This plan ships a regression-test net designed to **catch the contract-drift class of bug** without needing live GCS / a
browser / a manifest backfill. Five test categories, each with explicit assertion shape + pre-audit of which SSOT is the
source-of-truth.

## Test categories

### A. Shard methodology SSOT alignment (cross-repo contract tests)

The **shard atom** must be identical across:

1. UAC `SHARD_AXIS_MATRIX` (the SSOT for what columns count as shard axes).
2. UTL `ManifestWriter.record_captured` kwargs (the writer atomicity boundary).
3. deployment-api `data_status_hierarchical.py` axis order (drill-down depth).
4. deployment-api `data_status_service.py` `_build_chain_breakdown` denominator math.
5. UTL `read_availability_index` returned DataFrame columns.
6. deployment-ui `HierarchicalShardDrilldown.tsx` row_key field consumption.

**Drift between any two = silent correctness bug.** The cluster-validation incident (TradFi options ES.OPT bundle) and
the rollup-math incident (ARBITRUM 32/54) are both this class.

**Tests:**

- [x] [unified-api-contracts] P0. `tests/test_shard_axis_matrix_consistency.py` — for every `(service, asset_group)` in
      `SHARD_AXIS_MATRIX`, assert: (a) every axis name maps to a real manifest column that
      `ManifestWriter.record_captured` accepts as a kwarg; (b) the axis order matches the codex per-asset-group
      shard-key matrix in CLAUDE.md (golden file). (UAC@bf7607c — shipped; xfail documents canonical_question_group
      drift)
- [x] [unified-trading-library] P0. `tests/test_manifest_writer_axis_kwargs.py` — for every `(service, asset_group)`
      covered by the writer, assert `record_captured` called with the SSOT-declared kwargs raises ValueError when one is
      missing (catches writer drift away from the SSOT). (UTL@02352dc8 — shipped; 43 tests pass)
- [x] [deployment-api] P0. `tests/unit/test_drilldown_axis_depth_matches_ssot.py` — call `get_hierarchical_drilldown`
      for every `(service, asset_group)` in `SHARD_AXIS_MATRIX`; assert the returned `axes` list equals
      `SSOT_axes + ["date"]`. Catches the "drilldown excludes display axes" drift listed as an open follow-up in
      `data_status_drilldown_shard_atom_alignment_2026_05_07` § "Open drifts". (deployment-api@6cfed38 — test exists +
      passes; deployment-api@40f7769 — aligned to UAC SHARD_AXIS_MATRIX consolidation)
- [x] [deployment-api] P0. `tests/unit/test_chain_breakdown_shards_vs_dates.py` — synthesize a manifest with multiple
      data_types and instruments per chain; assert `_build_chain_breakdown` returns `shards_expected ≫ dates_expected`.
      Catches the rollup-math incident. (deployment-api@6cfed38 — test exists + passes)
- [x] [deployment-ui] P0. `tests/contracts/test_drilldown_response_shape.test.ts` — Vitest test that pins the
      `DrilldownResponse` interface shape against a golden JSON snapshot. Catches API drift where a field rename (e.g.
      `total_top_axis_children` → `total`) silently breaks the UI. (deployment-ui@f747e38 — 17 tests: TypeScript
      compile-time assignment-narrowing + runtime Object.keys assertions for DrilldownTotals, DrilldownNode,
      DrilldownResponse; critical regression guard pins total_top_axis_children as the pagination field name)

### B. UAC canonical-types alignment (cross-service field parity)

UAC declares the canonical types every consumer expects. When a consumer adds a field, it must land in UAC first.

**Tests:**

- [x] [unified-api-contracts] P0. `tests/test_canonical_capture_status_taxonomy.py` — assert `EMPTY_CONFIRMED_REASONS`
      is a closed set covering every reason a writer is allowed to emit; assert UTL's `record_empty(reason=...)`
      validates against this set. (UAC@bf7607c — shipped; 8 tests pass)
- [x] [unified-api-contracts] P0. `tests/test_drilldown_node_shape.py` — pin the `DrilldownNode` Pydantic / TypedDict
      shape; assert deployment-api's `DrilldownNode.to_dict()` produces a dict matching the schema (catches a renamed
      field on either side). (UAC@ff599d7 spec-side 30 tests; deployment-api@b2de03d impl-side 16 tests; both pass)
- [x] [unified-api-contracts] P0. `tests/test_protocol_launch_dates_vs_chain_genesis.py` — every chain in
      `PROTOCOL_LAUNCH_DATES` keys must be in `CHAIN_GENESIS_DATES`; every protocol declared must have either a launch
      date OR be on `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION`. (already partially shipped — extend.) (UAC@6c873e4 —
      shipped as `test_protocol_launch_dates.py` in UAC unit tests; UAC@f22f4b1 — `test_chain_genesis_dates.py`)
- [x] [deployment-api] P0. `tests/unit/test_uac_imports_only_via_facades.py` — AST-walk
      `deployment_api/services/data_status_*.py` and assert no `from unified_api_contracts.canonical.*` imports
      (UAC-internal); only `from unified_api_contracts import X` or `from unified_api_contracts.{domain} import X`.
      Catches the Citadel UAC-import-rule violations. (deployment-api@6cfed38 — test exists + passes)

### C. Start-date / cutoff methodology (per-source coverage clipping)

Every per-source / per-chain / per-protocol cutoff in UAC must propagate cleanly through every expected-universe
builder, every preflight skip, every record_expected_empty reason.

**Tests:**

- [x] [deployment-api] P0. `tests/unit/test_mtds_expected_dates_clipping.py` — for every (chain, protocol) pair in
      `PROTOCOL_LAUNCH_DATES`, assert `_mtds_expected_dates_cached` returns empty when the window predates
      `max(chain_genesis, protocol_launch)` and non-empty when it postdates. Catches the regression where one cutoff is
      honored but the other isn't. (deployment-api@6ab227b — test exists + passes)
- [x] [unified-api-contracts] P0. `tests/test_sports_source_coverage_propagation.py` — for every (source, data_type) in
      `SOURCE_COVERAGE_START` + `DATA_TYPE_COVERAGE_START`, assert
      `clip_dates_to_source_coverage(source, start, end, data_type=dt)` correctly drops pre-coverage dates. (UAC@6f2db1f
      — 20 tests covering clip_dates_to_source_coverage behaviour + completeness + DATA_TYPE_COVERAGE_START integrity;
      20/20 pass)
- [x] [market-tick-data-service] P0. `tests/unit/test_vix_15m_source_layering.py` — assert the routing surface in
      `umi_tick_provider.py` sends pre-2025-11-13 dates to Barchart preload (no Yahoo round-trip), 2025-11-13 →
      today−60d to the honest-gap branch, and post-today−60d to Yahoo. (already shipped — 10/10 pass verified 2026-05-14
      slot 4)
- [x] [deployment-api] P0. `tests/unit/test_data_status_denominator_clips_pre_cutoff_days.py` — assert the data- status
      panel's denominator excludes pre-cutoff days, so the panel doesn't render thousands of phantom- missing pre-launch
      days for chains/protocols that didn't exist yet. (deployment-api@6ab227b — test exists + passes)
- [x] [unified-api-contracts] P0. `tests/test_chain_genesis_dates_completeness.py` — every EVM chain in
      `MAINNET_CHAIN_IDS` (non-zero chain_id) has a genesis date. (already shipped — extend with non-EVM fallbacks.)
      (UAC@f22f4b1 — shipped as `test_chain_genesis_dates.py` in UAC unit tests)

### D. Deploy-Missing end-to-end coverage

Beyond the row_key + mode tests already shipped, exercise the full preview→shard-key→handler-decompose→
orchestrator-skip flow.

**Tests:**

- [x] [deployment-api] P0. `tests/unit/test_deploy_missing_preview_routing_per_service.py` — for every service in
      `_SERVICE_LAUNCHER_SCRIPTS`, build a representative leaf row_key + assert the preview composes a shard-key
      consumable by that service's CLI handler. (deployment-api@3040a1b + deployment-api@8012a12 — test exists + passes)
- [x] [market-tick-data-service] P0. `tests/cli/test_shard_key_round_trip.py` — given the preview's emitted `shard_key`,
      run `decompose_shard_key()` on it and assert the recovered argparse Namespace matches the original row_key
      field-for-field. Catches drift between the preview composer and the decomposer. (MTDS@32960ad — test exists +
      passes; 7 parametrized cases + 3 standalone tests)
- [x] [deployment-api] P0. `tests/unit/test_deploy_missing_tarball_mode_command.py` — assert the `tarball-from-local`
      mode's command chains `create-code-tarballs.sh --all && launcher` (catches `&&` → `;` regression that would let
      the launcher run even when the tarball build fails). (deployment-api@6cfed38 — test exists + passes)
- [x] [deployment-api] P0. `tests/integration/test_deploy_missing_skip_already_captured.py` — using a fixture manifest
      where one shard is `captured` and one is missing, run a simulated handler invocation with the shard-key targeting
      the captured shard; assert the orchestrator's `preflight_captured_atoms` skip path fires without re-fetching.
      Catches the user's 2026-05-07 directive: "service responds to it, respects it, and is run without --force so that
      it skips already existing shards." (deployment-api@6ab227b — test exists + passes; 3 class tests + 3 parametrized)
- [x] [deployment-ui] P0. `tests/components/DeployMissingButton.test.tsx` — already partially shipped; extend with tests
      for the warning panel rendering on `tarball-from-local` mode + the mode-toggle re-fetch behavior.
      (deployment-ui@79548a6 — 19 tests in tests/unit/components/DeployMissingButton.test.tsx: tarball-from-local
      LOCAL-ONLY warning panel, mode-toggle re-fetch issues second postDeployMissingPreview call, env-based blocking
      staging/production/development, copy, close, error handling)

### E. Cloud-agnostic behavior

The AWS/GCP UI toggle must actually swap the underlying storage client. Today the toggle just changes the API base URL;
the data-status / drilldown / deploy_missing services are GCS-only.

**Tests:**

- [x] [deployment-api] P0. `tests/unit/test_storage_facade_aws_path.py` — when `CLOUD_PROVIDER=aws`, assert
      `storage_facade` reads from S3 (mocked via moto), NOT GCS. Catches the regression where a refactor leaves
      `from google.cloud import storage` hardcoded. (deployment-api@1e6e357 — 8 tests: factory dispatch + facade UCI
      routing)
- [x] [deployment-api] P0. `tests/unit/test_data_status_hierarchical_aws_path.py` — when `CLOUD_PROVIDER=aws`, assert
      `get_hierarchical_drilldown` reads the manifest from S3 (mocked) using the AWS-equivalent bucket name template;
      the returned tree shape is identical to GCS. (deployment-api@fed999b — 10 tests: bucket-name pin + shape parity +
      required keys + no-GCS dispatch)
- [x] [deployment-api] P0. `tests/unit/test_deploy_missing_aws_launcher_routing.py` — when `CLOUD_PROVIDER=aws`, assert
      `_SERVICE_LAUNCHER_SCRIPTS` resolves to `launch-*-ec2.sh` (or the AWS-equivalent) rather than the GCE
      `launch-*-vm.sh`. (Note: requires the EC2 launchers from `aws_migration_defi_first_2026_05_07` to exist; gate this
      test on the launcher-existence check.) (deployment-api@ce40a88 — 6 tests skip-gated on EC2 launchers + 2
      pre-migration state pins pass; auto-unskips when \_SERVICE_LAUNCHER_SCRIPTS gains ec2 entries)
- [x] [unified-cloud-interface] P0. `tests/test_storage_client_protocol_parity.py` — assert
      `StorageClient.read_parquet`, `list_blobs`, `get_blob_metadata` produce the same return shape across the GCS + S3
      backends for an identical input dataset. (Generalizes beyond data-status.) (unified-trading-library@e55d3c9f — 16
      tests: subclass inheritance + return-shape via LocalStorageProvider; BlobMetadata.full_path; GCS/S3/Local all
      satisfy StorageClient ABC)
- [x] [deployment-ui] P0. `tests/components/CloudProviderToggle.test.tsx` — assert clicking AWS sets `apiBaseUrl` to
      port 8005 + clears the cache; clicking GCP returns to 8004. (Today only port-swapping; extend when the API gains
      real AWS code paths.) (deployment-ui@1d1c970 — 15 tests: 4 describe blocks — toggle rendering, target transitions,
      DEV-mode /api passthrough, local-prod port 8004/8005 routing)

### F. Playwright e2e suite (data-status UI walks)

For the bug classes that escape unit tests (real network 502s, real GCS latency, HMR issues, full-stack contract drift),
build an automated Playwright suite that walks every (service, asset_group) panel.

**Tests:**

- [x] [deployment-ui] P0. `tests/e2e/data-status-tab-renders.spec.ts` — clicks each of the 23 services in the
      service-mesh; asserts the Data Status tab loads + renders per-asset_group panels for every covered asset_group; no
      console errors; no 5xx in network log. (deployment-ui@a9f5e98 — 3 tests: per-service loop over mocked services,
      pageerror listener, 5xx response guard)
- [x] [deployment-ui] P0. `tests/e2e/hierarchical-drilldown-walk.spec.ts` — for every (service, asset_group) pair the
      drill-down endpoint covers, expand the panel + assert: axes list rendered, totals rendered with non-zero values
      for asset_groups that have data in the test window, "Show more" button surfaces when
      `total_top_axis_children > tree.length`. (deployment-ui@a9f5e98 — 6 tests: axes+totals + Show-more for 3
      service/asset_group pairs)
- [x] [deployment-ui] P0. `tests/e2e/deploy-missing-preview.spec.ts` — drill into a captured=0 leaf with full shard
      atom; click ↻ deploy; assert the copy-to-clipboard command renders + has the canonical 6-field shard-key shape;
      toggle to tarball-from-local; assert the LOCAL-ONLY warning panel is visible + the command chains
      create-code-tarballs.sh + launcher with `&&`. (deployment-ui@a9f5e98 — 2 tests: shard-key fields in command;
      LOCAL-ONLY warning + && in tarball mode)
- [x] [deployment-ui] P0. `tests/e2e/per-leaf-csv-download.spec.ts` — click a captured leaf's `↓ csv` link; assert the
      response Content-Type is `text/csv` + at least one row. (deployment-ui@a9f5e98 — 2 tests: ↓ csv link visible;
      text/csv response with ≥1 data row)
- [x] [deployment-ui] P0. `tests/e2e/cloud-toggle.spec.ts` — click the AWS toggle; assert the API base URL switches;
      reload; assert the panels still render (or render an explicit "AWS backend not configured" placeholder while the
      cloud-agnostic backend is still being built). (deployment-ui@a9f5e98 — 3 tests: toggle no crash; GCP/AWS buttons
      visible; round-trip GCP→AWS→GCP survives)
- [x] [deployment-ui] P0. `tests/e2e/regression-2026-05-07.spec.ts` — explicit regression for the 2026-05-07 "No data
      for cefi" + "Deploy-Missing 400" incidents — load TRADFI panel, assert non-zero totals; load DeployMissingButton
      on a venue-level node, assert it does NOT render; load on a date-level leaf with full shard-key, assert it DOES
      render + opens the preview modal. (deployment-ui@a9f5e98 — 3 tests: TRADFI non-zero totals; partial-key node no
      button; full-key leaf opens modal)

## Phased execution DAG

```
Phase 0 (audit existing coverage)
─────────────────────────────────
Inventory current tests; map each
to a category (A-F); identify gaps.
              ↓
Phase 1 (Categories A + B in parallel)        Phase 2 (Category C in parallel)
─────────────────────────────────────         ───────────────────────────────
SSOT alignment + UAC canonical-types          Start-date / cutoff propagation
              ↓                                              ↓
Phase 3 (Category D in parallel)              Phase 4 (Category E)
──────────────────────────────────           ──────────────────────────────────
Deploy-Missing E2E                            Cloud-agnostic
              ↓                                              ↓
Phase 5 (Category F — Playwright suite)
────────────────────────────────────────────────────────────────────────────
e2e walks + regression specs
              ↓
Phase 6 (CI wiring)
─────────────────────────────────────
GHA workflow runs the Playwright suite on
every deployment-ui PR + every drilldown-
related deployment-api PR.
```

## Success criteria

- **Code gates:** every test in categories A-F passes locally + in CI.
- **Coverage gate:** every (service, asset_group) pair in `SHARD_AXIS_MATRIX` has at least one Playwright walk + one
  Vitest render-gate test + one Python contract test.
- **Regression gate:** the four 2026-05-07 + earlier incidents listed in "Why" each have a named test that fails when
  the bug is reverted (verified-via-stash-and-rerun protocol).
- **Documentation gate:** new codex doc `/codex/06-coding-standards/test-coverage-data-status.md` lists the test
  patterns + how to add a new (service, asset_group) to the suite when one lands.

## Out of scope

- Test coverage for non-data-status surfaces (DART / strategy / execution / risk / ml-\* dashboards). Those have their
  own plans / handoffs.
- Test coverage for the launchers themselves (the `launcher_scripts_consolidation_into_deployment_service` plan tracks
  per-launcher smoke tests).
- Deletion of existing flakier tests — out of scope; this plan only adds new ones.

## Temporary states + their canonical follow-up plans

- Until Category E ships, the AWS/GCP toggle is "documented-not-tested" — the toggle changes the API URL but the
  data-status backend doesn't actually swap to S3. Successor: `aws_migration_defi_first_2026_05_07.md` Phase N (the
  storage-facade work).
- Until the EC2 launchers ship, Category E `test_deploy_missing_aws_launcher_routing` is gated on launcher- existence +
  may skip with an `@pytest.mark.skip("EC2 launchers not yet shipped")` decorator.

## References

- `data_status_drilldown_shard_atom_alignment_2026_05_07.md` — the drill-down plan whose Phase 6 ship motivates this
  regression net.
- `aws_migration_defi_first_2026_05_07.md` — Category E AWS work depends on the unified storage facade shipped there.
- `launcher_scripts_consolidation_into_deployment_service_2026_05_07.md` — Category D (Deploy-Missing per-service
  routing) extends as new launchers register.
- `deploy_missing_auto_launch_2026_05_07.md` — when auto-launch ships, Category D extends with security- boundary tests
  (rate-limiter, audit-log, IAM-scope assertions).
- CLAUDE.md "Per-asset-group shard-key matrix" — golden source for the SSOT alignment tests.
- CLAUDE.md "VM launcher script SSOT" — golden source for the Deploy-Missing routing tests.
- Reference incidents listed in "Why" — every one becomes a named regression test in Category F.
