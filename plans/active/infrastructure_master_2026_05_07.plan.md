---
name: infrastructure-master
slug: infrastructure_master_2026_05_07
date: 2026-05-07
owner: claude-code
status: active
priority: P0
phase: pending_approval
domain: infrastructure
type: umbrella
locked_by: live-defi-rollout
locked_since: 2026-05-07
folds_in:
  - shard_granularity_ssot_propagation_2026_05_06
  - shard_granularity_ssot_propagation_2026_05_06.HANDOVER # paired handover doc
  - data_status_multi_axis_shard_propagation_2026_05_06
  - deployment_service_build_infrastructure_repair_2026_04_22
related_plans:
  - master_to_live_defi_2026_05_23
  - writegate_honest_coverage_endtoend_2026_05_06
  - venue_axis_asset_group_vocabulary_2026_04_25
---

# Infrastructure Master — shard / data-status / deployment-build umbrella

## Scope

Single source of truth for **shard-granularity propagation, data-status drilldown, and deployment-service build
infrastructure** — the cross-cutting plumbing that every asset_group umbrella depends on.

Covers:

- **Shard granularity SSOT propagation** — the canonical shard atom must match across (a) writer atomicity boundary, (b)
  manifest row key, (c) data-status display rollup, (d) downstream pre-flight gates, (e) deployment-UI drill-down. Per
  CLAUDE.md "Shard-granularity SSOT (CRITICAL)" rule.
- **Data-status multi-axis propagation** — per-(service, asset_group) shard-axis matrix;
  `breakdowns: dict[axis, dict[value, count]]`; deployment-ui BreakdownsAccordion. v6 → v7 manifest schema migration
  with `job_id` axis for ML/strategy/execution.
- **Deployment-service build infrastructure repair** — Cloud Build for the sports + features-sports services; UTL
  base-image rebuild; Cloud Run image refresh.
- **Shard granularity executor handover** — the in-flight per-service verify/fix/lift/build checklist for applying
  shard-atom alignment across MTDS / MDPS / features-\* / sports / instruments-service.

## Current state (2026-05-07)

- **Shard granularity propagation**: 20/11 = 65% done. Phase 0 audit findings shipped; Phase 1 raw-tables migration (14
  entries in `TABLE_TO_EXPORT`) pending; `_ensure_timestamp` shim deletion gated on raw-tables completion.
- **Data-status multi-axis**: 22/15 = 59% done. UTL @ed658e9b shipped (manifest v6→v7, additive); deployment-api
  @85053fe shipped (SSOT consumer, breakdowns, 6 filter params, `/api/config/shard-axis-matrix` endpoint); deployment-ui
  @8056995 shipped (BreakdownsAccordion). Per-service `feature_group` / `job_id` writer wiring + Playwright walk +
  cell-grid secondary-axis re-fetch pending.
- **Deployment service build infrastructure**: 4/5 = 80% done. Phases 1+2 shipped (UTL base-image rebuild commits);
  Phases 3-7 (local Docker smoke → Cloud Build smoke → Plan 3/6 unblock → workspace-wide validation) pending.

## Critical path

| Workstream                                                         | Status                        | Source                                                     |
| ------------------------------------------------------------------ | ----------------------------- | ---------------------------------------------------------- |
| Shard atom == manifest row key == data-status rollup == drill-down | partial                       | `shard_granularity_ssot_propagation`                       |
| `_ensure_timestamp` shim deletion (writegate Phase 2.C overlap)    | gated on raw-tables migration | `shard_granularity_ssot_propagation` + writegate Phase 2.C |
| Raw tables migration (14 entries in `TABLE_TO_EXPORT`)             | pending                       | `shard_granularity_ssot_propagation`                       |
| Per-service `feature_group` / `job_id` writer wiring               | pending                       | `data_status_multi_axis_shard_propagation`                 |
| Cell-grid secondary-axis re-fetch in deployment-ui                 | partial                       | `data_status_multi_axis_shard_propagation`                 |
| Playwright walk across 15 services × 5 asset_groups                | pending                       | `data_status_multi_axis_shard_propagation`                 |
| `feature_group` backfills (if writers never populated)             | conditional                   | `data_status_multi_axis_shard_propagation`                 |
| Cloud Build smoke (sports + features-sports)                       | pending                       | `deployment_service_build_infrastructure_repair`           |
| Plan 3 (sports_scheduler_cron_activation) unblock                  | gated on Cloud Build          | `deployment_service_build_infrastructure_repair`           |

## Consolidated todos (P0/P1 only)

**Cross-plan coordination**: this umbrella's raw-tables migration + `_ensure_timestamp` shim deletion are **Stage 4** of
the workspace-wide manifest migration. See
[`manifest_migration_master_2026_05_07.plan.md`](./manifest_migration_master_2026_05_07.plan.md) for sequencing DAG,
conflicts, VM impact (per-table mini-pauses for sports FWD on raw-tables migration), and operator gates. Constraints:
`_ensure_timestamp` shim DELETE is GATED on raw-tables migration completion; raw-tables migration runs AFTER Stage 3
reconcilers + `mtds-s4-10` rescan complete.

### Shard granularity propagation (`shard_granularity_ssot_propagation`)

- [ ] [HUMAN] P0. Phase 0 → Phase 1 handover sign-off; user converts findings into per-service fix todos in Phase 1.
- [ ] [AGENT] P0. **#1 MDPS 1440-NaN reproduction path** — the canonical per-shard test case for shard-atom alignment
      regressions.
- [ ] [AGENT] P0. **Raw tables migration** (next slice — needs design): 14 entries in `TABLE_TO_EXPORT`. Source-of-truth
      gap: pick canonical shape per table.
- [ ] [AGENT] P0. **Delete `_ensure_timestamp` shim** — once all 14 raw tables migrate, drop the midnight UTC fallback.
      Coordinated with writegate Phase 2.C.
- [ ] [AGENT] P0. All affected downstream consumers updated in this plan (no "fix later").
- [ ] [VERIFY] P0. Manifest reads + writes use same shard key for every (service, data_type).
- [ ] [VERIFY] P0. Data-status surfaces match writer granularity (audit report only — UI fix tracked separately).
- [ ] [VERIFY] P0. No fallback paths remain for migrated manifests.
- [ ] [VERIFY] P0. Tests cover write-gates: row=0 → fail loud, high NaN → fail loud, schema mismatch → fail loud.
- [ ] [VERIFY] P0. `available_at` end-to-end smoke: write feature at t-24, verify no input row consumed has
      `available_at > t-24-horizon`.

### Data-status multi-axis (`data_status_multi_axis_shard_propagation`)

- [ ] [features-onchain] P1. Each calculator writes `feature_group=` matching its upstream source (`lending_rates`,
      `lst_yields`, etc.).
- [ ] [features-calendar] P1. Each source writer (FRED, tradingeconomics, sec, holiday_calendar) populates
      `feature_group`.
- [ ] [features-cross-instrument / multi-timeframe] P1. Confirm `timeframe` populates correctly.
- [ ] [tests] P1. Per-service unit test: write under a `job_id`, assert manifest has populated `job_id`.
- [ ] [deployment-ui] P3. Visual regression smoke: Playwright walk across all 15 services × 5 asset_groups (where
      applicable).
- [ ] [feature_group backfills] P4. **If** Phase 1A audit finds a per-service writer that has never populated
      `feature_group`, backfill the manifest column for historical rows.
- [ ] [deployment-api / scripts/data_status_rollup_worker.py] P5. Update worker to emit `breakdowns` in the rollup blob.
- [ ] [deployment-service] P5. Push new image to Cloud Run; cron rebuilds 5 min after deploy.
- [ ] [deployment-ui] P5. Verify on Cloud Run URL.

### Deployment service build infrastructure (`deployment_service_build_infrastructure_repair`)

- [ ] [AGENT] P3. (`p3-local-smoke`) Phase 3 — Local Docker build smoke. Blocked on Phase 1 + Phase 2.
- [ ] [AGENT] P4. (`p4-cloud-build-smoke`) Phase 4 — Cloud Build smoke. Blocked on Phase 3 AND Phase 3b passing.
- [ ] [AGENT] P5. (`p5-plan3-unblock`) Phase 5 — Unblock Plan 3 (sports_scheduler_cron_activation). Blocked on Phase 4.
- [ ] [AGENT] P6. (`p6-plan6-check`) Phase 6 — Check whether Plan 6 (features-sports-service deployment) has the same
      build issue.
- [ ] [AGENT] P7. (`p7-success-criteria`) Phase 7 — Validate workspace-wide success criteria.

### Audit findings 2026-05-07 — folded from session wrapper

**Source**: `plans/ai/session_2026_05_07_data_status_audit_findings.plan.md` rows B.2 + C.13 (added 2026-05-07 from
operator screenshot). Operator surfaced two related drill-down issues during the deployment-ui walkthrough: (1) the
hierarchy depth doesn't match the codex shard-key matrix per asset_group, and (2) drill-down terminates at different
depths for different (service, venue, data_type) combinations — some land at per-day download icons + schema modal
(working correctly), others stop one level short (broken).

#### B.2 — Drill-down hierarchy must match codex shard-key matrix per asset_group

Plan in `plans/ai/data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md` (5 phases). Owner-side todos:

- [ ] [AGENT] P0. **Phase 1 audit** — walk the deployment-ui data-status panel for each (service, asset_group) and
      compare the rendered drill-down hierarchy against the codex shard-key matrix in CLAUDE.md
      `§ Per-asset-group shard-key matrix`. Expected matrix:
  - CeFi spot/perp: `venue → data_type → instrument_type → instrument_id → day`
  - CeFi options/futures: `venue → data_type → options_chain|futures_chain → root → day`
  - TradFi futures: `venue → data_type → instrument_type → root → day`
  - TradFi ETFs: `venue → data_type → instrument_type → instrument_id → day`
  - TradFi options: `venue → data_type → options_chain → root → day` (11-cluster ES.OPT taxonomy)
  - DeFi: `chain → venue|protocol → data_type → instrument_id|protocol_id → day`
  - Sports: `source → data_type → league_id → fixture_id|day_aggregate → day`
  - Prediction: `venue → data_type → canonical_question_group → market_id → day`
- [ ] [SCRIPT] P0. **Phase 2 deployment-api endpoint** — extend `/api/data-status/drilldown` to return the per-axis
      hierarchy keyed on the SSOT matrix (not per-service overrides). Source: UAC `data_status_axis_matrix.PRIMARY_AXIS`
      (already wired into `_select_coverage_group_axis` per data-status multi-axis Phase 0). Add nested-axis support so
      the response is `dict[axis, dict[value, dict[axis, ...]]]` to arbitrary depth (the matrix above tops out at 5
      levels per asset_group).
- [ ] [SCRIPT] P0. **Phase 3 deployment-ui component** — replace the current hardcoded 2-level drill-down
      (`venue → data_type`) with a recursive renderer that walks the per-asset_group axis chain from the
      `/api/config/shard-axis-matrix` endpoint (already shipped in deployment-api@`85053fe`). Each level is collapsible;
      the leaf level always shows per-day download icons + schema modal trigger.
- [ ] [SCRIPT] P0. **Phase 4 per-shard download + missing-day surfacing** — every leaf node renders one icon-per-day
      with hover tooltip showing `attempted_at` / `error_reason` / `probed_paths` for missing days. Backend
      `probed_paths` field shipped deployment-api@`4ca4bb7`; UI must surface it.
- [ ] [SCRIPT] P0. **Phase 5 MTDS CLI shard-targeting flags** — `market-tick-data-service` CLI gains `--shard-key`
      (compound key string per asset_group), `--instrument-type`, `--root`, `--instrument-id`, `--day`,
      `--canonical-question-group`. Operator clicking a missing-day download icon in the UI gets a copy-paste-ready CLI
      invocation that recovers exactly that shard atom (no broader collateral re-fetch).

#### C.13 — Drill-down DEPTH consistency audit (operator finding 2026-05-07 from MTDS TRADFI screenshot)

Per the operator's screenshot of the deployment-ui MTDS / TRADFI panel:

- **Working correctly** (CBOE `ohlcv_15m`): drill-down lands at per-day download icons (each day rendered as a green/red
  box with download arrow) + clicking a day opens the schema modal — `2,159 rows / 1493 days, 99.6% schema`.
- **Broken** (CME `combo` instrument_type → underlyings `12 / 13 / 23 / 3C / 3P / 3W / BO / BTC / BX / C12 / ...`): each
  underlying root is collapsible to per-data_type bars (`ohlcv_1m 1572/2318 68%`, `trades 1/2318 0%`) but does NOT go
  deeper to per-day download icons. Operator can see "BO has 68% ohlcv_1m and 0% trades" but cannot click into a
  specific missing day to download or to surface its `error_reason`.

This is a **B.2 sub-class**: same shard-atom-alignment work but scoped to a specific UI inconsistency where the
hierarchy renders correctly down to the second-to-last level but stops short of the per-day leaf. The B.2 plan above
covers the renderer change; this todo group adds the AUDIT step that catalogues every offending (service, asset_group,
venue, data_type) combination so Phase 3 can verify the fix is comprehensive (not just "works for CBOE ohlcv_15m").

- [ ] [AGENT] P0. Walk the deployment-ui data-status panel across all 5 asset_groups × all services × all venues × all
      data_types. For each combination, record:
  - Drill-down depth reached before the renderer stops adding levels.
  - Whether the leaf level renders per-day download icons.
  - Whether the schema modal triggers from the leaf.
  - Compare the actual depth to the codex shard-key matrix expected depth.
- [ ] [DOC] P0. Output a coverage matrix at `unified-trading-pm/codex/02-data/deployment-ui-drilldown-depth-audit.md`
      listing every (service, asset*group, venue, data_type) tuple as one of: `WORKING` /
      `STOPS_AT_INTERMEDIATE_LEVEL*<level>`/`MISSING_SCHEMA_MODAL`/    `MISSING_DOWNLOAD_ICON`. Reference incidents
      (CBOE ohlcv_15m = WORKING, CME combo/\* = STOPS_AT_DATA_TYPE) per the operator screenshot.
- [ ] [VERIFY] P0. After B.2 Phase 3 deployment-ui renderer ships: re-walk the same audit; every entry in the matrix
      flips to `WORKING`. Block Phase 5 (MTDS CLI shard-targeting) sign-off until the matrix is 100% green.
- [ ] [VERIFY] P0. Schema modal works at every leaf — confirm via Playwright walk (B.2 Phase 3's Playwright coverage
      extends here).

## Anti-patterns + workspace-rule cross-references

- **Shard-granularity SSOT (CRITICAL)** (CLAUDE.md): shard atom MUST match writer / manifest / data-status / pre-flight
  / drill-down. TradFi MVP partial-bundle, MDPS empty-placeholder, Databento per-schema drop are all instances of drift
  in this class.
- **Per-asset-group shard-key matrix** (CLAUDE.md): cefi spot/perp per-instrument; cefi options bundled by root; tradfi
  futures bundled; tradfi options 11-cluster ES.OPT taxonomy; defi `chain` first-class axis; sports
  `(source, data_type, league_id, day)`; prediction `canonical_question_group`.
- **No double SSOT** (CLAUDE.md): `_create_empty_output` AND `_handle_empty_tick_data` collapse; `_ensure_timestamp`
  shim AND per-source `stamp_available_at_*` collapse (writegate Phase 2.C); v3-shape `_write_manifest_records` AND v6
  canonical writer collapse.
- **Manifest migration NOT fallback** (CLAUDE.md): when manifest drifts from canonical shape, write a one-time migration
  script and **remove** the fallback reader.

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.plan.md`](./master_to_live_defi_2026_05_23.plan.md).
- Write-gate cluster:
  [`writegate_honest_coverage_endtoend_2026_05_06.plan.md`](./writegate_honest_coverage_endtoend_2026_05_06.plan.md).
- Asset_group vocabulary:
  [`venue_axis_asset_group_vocabulary_2026_04_25.plan.md`](./venue_axis_asset_group_vocabulary_2026_04_25.plan.md).
- Per-asset-group umbrellas: `cefi_master_2026_05_07`, `defi_master_2026_05_07`, `tradfi_master_2026_05_07`,
  `sports_master_2026_05_07`, `predictions_master_2026_05_07`.
- Manifest SSOT codex: `codex/02-data/availability-manifest-and-data-status.md`.

## Folded plans (archived 2026-05-07)

- `shard_granularity_ssot_propagation_2026_05_06.plan.md` — full per-service propagation spec; P0 todos lifted above.
- `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md` — paired executor handover (per-service verify / fix /
  lift / build checklist); referenced for execution detail.
- `data_status_multi_axis_shard_propagation_2026_05_06.plan.md` — multi-axis breakdowns + filter params + v7 manifest;
  P1+ todos lifted above.
- `deployment_service_build_infrastructure_repair_2026_04_22.plan.md` — Cloud Build + UTL base-image rebuild.
