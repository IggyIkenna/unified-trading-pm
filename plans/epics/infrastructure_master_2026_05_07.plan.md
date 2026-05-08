---
name: infrastructure-master
slug: infrastructure_master_2026_05_07
date: 2026-05-07
deadline: 2026-05-23
last_updated: 2026-05-08
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
  - venue_axis_asset_group_vocabulary_2026_04_25 # 2 absorbed SSOT-cleanup items: venue_start_dates deletion + dashboard SSOT verify
related_plans:
  - master_to_live_defi_2026_05_23
  - writegate_honest_coverage_endtoend_2026_05_06
---

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 30 of 30 unchecked todos
- **Mis-marked DONE → flipped**: 0 — 2 todos classified as STALE (verified by audit-followups Tab 8 2026-05-08: Phase
  0→1 handover at line 126 + MDPS-1440-NaN reproduction-test at line 130, both superseded by writegate Phase 2.A
  - reconciler MDPS@`d3be0ef`); 9 verified actionable; 17 routed to other plans (mostly BLOCKED-ON
    data_status_drilldown_shard_atom_alignment_2026_05_07)
- **In-flight (running VMs)**: 24 cefi + 5 tradfi MDPS + 4 sports backfill VMs are LIVE TESTS of
  deployment-service@`456acb9` multi-axis correction shipped 2026-05-06; vm-zombie-watchdog always running. Plan does
  not gate these directly — they validate the shipped infrastructure.
- **Blocked by**: writegate `writegate_honest_coverage_endtoend_2026_05_06` Phase 2.A (legacy `_create_empty_output`
  deletion gates `_ensure_timestamp` shim deletion since the per-source `stamp_available_at_*` helpers in UTL@`cf312f66`
  are the migration target); `manifest_migration_master_2026_05_07` Stage 4 (raw-tables migration ordering)
- **Blocks**: `master_to_live_defi_2026_05_23` operator-facing data-status drilldown UX (B.2 + C.13 audit findings);
  `cefi_master` / `defi_master` / `tradfi_master` / `sports_master` / `predictions_master` umbrellas (each consumes the
  shard-axis matrix endpoint shipped here)
- **Last meaningful commits** (chronological, last shipped):
  - deployment-api@`176c599` (Tier 3D.2 reader-side classify_legacy_empty_row UTL helper wiring) — 2026-05-07
  - deployment-api@`0384eab` (DEFI pool drilldown probes asset_group= + chain= partition) — 2026-05-07
  - deployment-api@`14bbff9` (per-chain pre-launch date clipping for DEFI panel)
  - deployment-api@`64d2be9` / `cfb5096` / `8056995` / `7309b56` / `85053fe` (multi-axis breakdowns shipped)
  - deployment-ui@`ebfbc5d` (default startDate 2018-01-01 fix)
  - deployment-ui@`537d468` / `0fbd28b` / `7309b56` (BreakdownsAccordion + SchemaModal)
  - deployment-service@`456acb9` (multi-axis correction in docs)
  - UTL@`bf41175c` (split \_INDEX_CACHE into canonical+merged) + UTL@`75d16f28` (lift StreamingShardFinalizer)
  - UTL@`ed658e9b` (manifest v6→v7 with fixture_id + job_id columns)
- **Recommendation**: **NOT YET ARCHIVE-READY** — 9 actionable items remain (raw-tables migration, `_ensure_timestamp`
  shim deletion gated on it, drilldown depth audit + per-day icons, MTDS CLI shard-targeting flags, Cloud Build smoke
  for sports + features-sports). The deployment-ui drilldown depth-audit (B.2 / C.13) is the most operator-visible
  blocker and should be promoted to top-priority. The shard-granularity MDPS-1440-NaN reproduction-test todo is STALE —
  superseded by writegate Phase 2.A + MDPS@`d3be0ef` (`mdps_reconcile_1440_nan_placeholders.py` retrospective cleanup
  script). Per-service `feature_group`/`job_id` writer wiring is largely COMPLETE (onchain + calendar +
  multi-timeframe + ml-training@training_orchestrator + execution@save_operations + strategy@cloud_strategy_storage all
  confirmed) — those todos can be flipped after a final 1-day verification pass.
- **Anomalies**:
  - "MDPS 1440-NaN reproduction path" todo is STALE (superseded by writegate Phase 2.A and reconciler `d3be0ef`) —
    should be flipped to STALE marker not pursued.
  - The B.2 drilldown plan is in `plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md` (its own
    active plan), NOT in `plans/ai/` as the prose says — it was promoted on 2026-05-07 per PM commit `d968b5d3`.
    Reference text in plan body is now outdated.
  - "Schema modal works at every leaf" todo is verified live in deployment-ui — `SchemaModal` is wired
    (deployment-ui@`7309b56`/`537d468`), but the per-leaf coverage matrix audit is the real gating step.
  - Cloud Build status (Phases 3-7) — recent commits `e10a6ce` (deployment-api: "unbreak Cloud Build (red since 04-29)")
    and `6b05dd6` (UTL-base-image migration) suggest Phases 1+2 already shipped; Phase 3+4 (local Docker + Cloud Build
    smoke) likely still pending per the plan text.

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
      [AUDIT 2026-05-07: STALE — handover folded into umbrella; Phase 0 audit findings (multi-axis correction `456acb9`
      + B.2/C.13) were converted by sub-agent into the per-service todos already in this plan; no separate human
      sign-off remaining]
- [ ] [AGENT] P0. **#1 MDPS 1440-NaN reproduction path** — the canonical per-shard test case for shard-atom alignment
      regressions. [AUDIT 2026-05-07: STALE — superseded by writegate Phase 2.A (`_create_empty_output` deletion across
      all asset_groups, MDPS@`5b52d0b`/`b9f9328`/`80cf141`/`e9520a0`) AND retrospective cleanup script MDPS@`d3be0ef`
      `mdps_reconcile_1440_nan_placeholders.py`. Reproduction-test value moot — the bug is fixed at write-time AND
      backfill-cleaned]
- [ ] [AGENT] P0. **Raw tables migration** (next slice — needs design): 14 entries in `TABLE_TO_EXPORT`. Source-of-truth
      gap: pick canonical shape per table. [AUDIT 2026-05-07: FRESH — actionable; `TABLE_TO_EXPORT` confirmed at
      `features-sports-service/features_sports_service/cli/batch_write.py:20` with 8+ test mock sites; Stage 4 of
      `manifest_migration_master_2026_05_07` per plan body]
- [ ] [AGENT] P0. **Delete `_ensure_timestamp` shim** — once all 14 raw tables migrate, drop the midnight UTC fallback.
      Coordinated with writegate Phase 2.C. [AUDIT 2026-05-07: BLOCKED-ON infrastructure_master:raw-tables-migration;
      verified `_ensure_timestamp` still defined at
      `features-sports-service/features_sports_service/cli/batch_write.py:38` + `cli/handlers/batch_handler.py:148`
      (called at lines 544/628/695/766) + referenced by reconciler `scripts/features_sports_reconcile_available_at.py` —
      9 sites; cannot delete until raw-tables migration ships]
- [ ] [AGENT] P0. All affected downstream consumers updated in this plan (no "fix later"). [AUDIT 2026-05-07: BLOCKED-ON
      infrastructure_master:raw-tables-migration]
- [ ] [VERIFY] P0. Manifest reads + writes use same shard key for every (service, data_type). [AUDIT 2026-05-07: FRESH —
      verification gate; depends on raw-tables migration completion]
- [ ] [VERIFY] P0. Data-status surfaces match writer granularity (audit report only — UI fix tracked separately). [AUDIT
      2026-05-07: BLOCKED-ON infrastructure_master:Audit-findings-B.2-drilldown-depth-audit; UI fix lives in
      `data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md`]
- [ ] [VERIFY] P0. No fallback paths remain for migrated manifests. [AUDIT 2026-05-07: FRESH — verification gate;
      deployment-api@`64d2be9` dropped DEFI legacy-venue read-time canonicalisation fallback (one slice complete);
      raw-tables migration completion will retire remaining `_ensure_timestamp` fallback]
- [ ] [VERIFY] P0. Tests cover write-gates: row=0 → fail loud, high NaN → fail loud, schema mismatch → fail loud. [AUDIT
      2026-05-07: FRESH — verification gate; `record_empty(reason=...)` + `record_failed` shipped via UTL@`958634f9`;
      per-test-fixture verification across services pending]
- [ ] [VERIFY] P0. `available_at` end-to-end smoke: write feature at t-24, verify no input row consumed has
      `available_at > t-24-horizon`. [AUDIT 2026-05-07: FRESH — verification gate; UTL@`cf312f66`
      `availability_stamping` shipped + `LookaheadBiasError` raised in features-onchain `lst_yields`; smoke gate across
      all features-* pending]

### Data-status multi-axis (`data_status_multi_axis_shard_propagation`)

- [ ] [features-onchain] P1. Each calculator writes `feature_group=` matching its upstream source (`lending_rates`,
      `lst_yields`, etc.). [AUDIT 2026-05-07: VERIFIED-LIKELY-DONE —
      `features-onchain-service/features_onchain_service/adapters/onchain_writer.py:23` documents the path layout
      `by_date/day={date}/feature_group={group}/{protocol}.parquet` and `engine/orchestrator.py` has 13+
      `feature_group=` write sites (lines 134/164/192/200/208/257/575/584/1155/1187/1220 covering `lst_yields` /
      `lending_rates` / `macro_sentiment` / `rate_impact` / per-feature-group); flip after spot-check of writer fixture
      tests]
- [ ] [features-calendar] P1. Each source writer (FRED, tradingeconomics, sec, holiday_calendar) populates
      `feature_group`. [AUDIT 2026-05-07: VERIFIED-LIKELY-DONE —
      `features_calendar_service/engine/calendar_orchestrator.py:167-390` has 8+ `feature_group=` plumb-through sites;
      `engine/calculators/economic_events.py:56` declares `self.feature_group = "economic_events"`; flip after
      writer-test spot-check]
- [x] [features-cross-instrument / multi-timeframe] P1. Confirm `timeframe` populates correctly. (verified 2026-05-07:
      features-multi-timeframe-service/features_multi_timeframe_service/engine/orchestrator.py:127/258 has timeframe=
      write plumb) [AUDIT 2026-05-07: VERIFIED —
      `features-multi-timeframe-service/features_multi_timeframe_service/engine/orchestrator.py:127/258` has
      `timeframe=` write plumb; ready to flip]
- [ ] [tests] P1. Per-service unit test: write under a `job_id`, assert manifest has populated `job_id`. **DEFERRED**:
      tests pending — writer wiring shipped via ml-training@f7369f2 / ml-inference@69d6313 / strategy@90e00bb /
      execution@0b664d99 [AUDIT 2026-05-07: VERIFIED — ml-training@`f7369f2` / ml-inference@`69d6313` /
      strategy@`90e00bb` / execution@`0b664d99` shipped Phase 1B job_id writers (per master-plan-audit memory);
      ml-training `training_orchestrator.py:192-193/843` + `final_training_handler.py:207` + `model_registry.py:270`
      plumb job_id; execution `save_operations.py:802` plumbs job_id=run_id; strategy `cloud_strategy_storage.py:79-201`
      plumbs service_run_id; per-service unit-test verification pending but writer code is in place]
- [ ] [deployment-ui] P3. Visual regression smoke: Playwright walk across all 15 services × 5 asset_groups (where
      applicable). [AUDIT 2026-05-07: FRESH — actionable; deferred per CLAUDE.md DEFI canonicalisation closeout
      2026-05-07 ("B.2 Playwright walk across 15 services × 5 asset_groups deferred — needs full local stack + manual
      visual"); P3 deferral acceptable for May-23 deadline]
- [ ] [feature_group backfills] P4. **If** Phase 1A audit finds a per-service writer that has never populated
      `feature_group`, backfill the manifest column for historical rows. [AUDIT 2026-05-07: BLOCKED-ON
      infrastructure_master:Phase-1A-audit-feature_group; conditional on audit finding]
- [ ] [deployment-api / scripts/data_status_rollup_worker.py] P5. Update worker to emit `breakdowns` in the rollup blob.
      [AUDIT 2026-05-07: VERIFIED-LIKELY-DONE —
      `deployment-api/deployment_api/services/data_status_service.py:3126-3288` has `_build_breakdowns` method +
      per-(service, asset_group) breakdowns wired at line 3284-3288; deployment-api@`8056995` shipped per-asset-group
      breakdowns accordion + UAC SSOT axis matrix; rollup-worker @`44b4a98` shipped coverage-summary fast-path; flip
      after rollup blob inspection]
- [ ] [deployment-service] P5. Push new image to Cloud Run; cron rebuilds 5 min after deploy. [AUDIT 2026-05-07:
      BLOCKED-ON infrastructure_master:Cloud-Build-smoke; deployment-api@`e10a6ce` "unbreak Cloud Build (red since
      04-29)" suggests Cloud Build is now green; verify before flipping]
- [ ] [deployment-ui] P5. Verify on Cloud Run URL. [AUDIT 2026-05-07: BLOCKED-ON
      infrastructure_master:deployment-service-Cloud-Run-push]

### Deployment service build infrastructure (`deployment_service_build_infrastructure_repair`)

- [ ] [AGENT] P3. (`p3-local-smoke`) Phase 3 — Local Docker build smoke. Blocked on Phase 1 + Phase 2. [AUDIT
      2026-05-07: FRESH — actionable; UTL-base-image migration committed @`6b05dd6` suggests Phase 1+2 done; Phase 3
      local-Docker smoke remains]
- [ ] [AGENT] P4. (`p4-cloud-build-smoke`) Phase 4 — Cloud Build smoke. Blocked on Phase 3 AND Phase 3b passing. [AUDIT
      2026-05-07: FRESH — likely close to done; deployment-api@`e10a6ce` (2026-05-06) "unbreak Cloud Build (red since
      04-29) + tier-3 fast-path" suggests Cloud Build is now green; needs explicit smoke verification]
- [ ] [AGENT] P5. (`p5-plan3-unblock`) Phase 5 — Unblock Plan 3 (sports_scheduler_cron_activation). Blocked on Phase 4.
      [AUDIT 2026-05-07: BLOCKED-ON infrastructure_master:Phase-4-Cloud-Build-smoke]
- [ ] [AGENT] P6. (`p6-plan6-check`) Phase 6 — Check whether Plan 6 (features-sports-service deployment) has the same
      build issue. [AUDIT 2026-05-07: BLOCKED-ON infrastructure_master:Phase-4-Cloud-Build-smoke]
- [ ] [AGENT] P7. (`p7-success-criteria`) Phase 7 — Validate workspace-wide success criteria. [AUDIT 2026-05-07:
      BLOCKED-ON infrastructure_master:Phase-6-plan6-check]

### VenueMapping `venue_start_dates` cleanup (folded-in 2026-05-07 from `venue_axis_asset_group_vocabulary_2026_04_25`)

The asset-group vocabulary plan absorbed two SSOT-cleanup items from the archived `venue_availability_ssot_2026_03_25`
plan that ride on shard-axis infrastructure (venue start-date semantics + dashboard consumption). Both belong here since
they touch the manifest / data-status SSOT chain, not the asset_group rename itself.

- [ ] [AGENT] P0. Delete `venue_start_dates` from `VenueMapping` (old format) — replace with the canonical venue+date
      shape (per the source plan's design doc). [AUDIT 2026-05-07: FRESH — actionable; 8+ deployment-service test sites
      still reference `venue_start_dates` (`tests/conftest.py:392`,
      `tests/unit/test_shard_calculator.py:486/513/543/577/623`, `test_shard_optimization.py:80/107/137/171`); deletion
      is a real ~10-file change] (folded from venue_axis_asset_group_vocabulary_2026_04_25)
- [ ] [AGENT] P2. Data-status dashboard checks against same SSOT — confirm dashboard reads venue start dates from the
      canonical source post-cleanup. [AUDIT 2026-05-07: BLOCKED-ON
      infrastructure_master:VenueMapping-venue_start_dates-deletion; cannot verify dashboard SSOT consumption until
      `venue_start_dates` is deleted from VenueMapping] (folded from venue_axis_asset_group_vocabulary_2026_04_25)

### Streaming-finalize follow-ups (folded-in 2026-05-07 from `streaming_finalize_lift_and_downsize_2026_05_06`)

The streaming-finalize work-stream (UTL@`75d16f28` lift, MTDS@`b12ecb5` kraken slash→hyphen + UTL refactor,
deployment-service launcher downsize) shipped Items 1/3/5; Item 4 (DEX historical replay) has its own active plan at
`dex_historical_replay_lighter_extended_pacifica_2026_05_07.plan.md`. **Two follow-ups carry over and live here.**

- [ ] [HUMAN] P2. **Block-size tuning bench** for `TARDIS_STREAM_BLOCK_SIZE_MB` env var. Run sweep across {1, 2, 4, 8,
      16} MiB on Coinbase BTC-USD heavy day; plot peak RSS vs row count vs output parquet size. Pick the workspace
      default (likely 2 MiB → ~2 GB peak with ~5-10% larger output). Currently shipped knob defaults to 8 MiB clamped
      [1, 64]; exposed as VM-launch metadata via `setup-data-pipeline-vm.sh` per MTDS@`dae9bc4`. **Why HUMAN:** needs an
      operator on a 16 GB / 32 GB / 64 GB VM matrix to gather the empirical curve before tuning the default. The knob
      surfacing was the prerequisite; this bench is the calibration follow-up. [AUDIT 2026-05-07: FRESH — non-blocking
      for May 23 cutover; cost-saving and reliability optimization]
- [ ] [AGENT] P3. **Reuse `StreamingShardFinalizer` UTL helper** when adding the next bulk-CSV-style adapter (Databento
      bulk endpoints, future Tardis-style providers). Import path:
      `from unified_trading_library.io import StreamingShardFinalizer`. Pass an adapter-specific `shard_router` callback
      that takes a row-group DataFrame and yields `(shard_key, shard_path, shard_df, metadata)` tuples; the finalizer
      handles writer-pool lifecycle + bounded peak memory + FD-leak guarantees. **Do NOT copy-paste**
      `tardis_adapter._tardis_cefi_shard_router` per the workspace rule "[UTL] = cross-service runtime utilities; do not
      duplicate per-service." Reference: UTL@`75d16f28` shipped + MTDS Tardis adapter migrated. [AUDIT 2026-05-07:
      DEFERRED — fires only when next adapter is added]

### Audit findings 2026-05-07 — folded from session wrapper

**Source**: `plans/ai/session_2026_05_07_data_status_audit_findings.plan.md` rows B.2 + C.13 (added 2026-05-07 from
operator screenshot). Operator surfaced two related drill-down issues during the deployment-ui walkthrough: (1) the
hierarchy depth doesn't match the codex shard-key matrix per asset_group, and (2) drill-down terminates at different
depths for different (service, venue, data_type) combinations — some land at per-day download icons + schema modal
(working correctly), others stop one level short (broken).

#### B.2 — Drill-down hierarchy must match codex shard-key matrix per asset_group

Plan in `plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.plan.md` (5 phases — promoted from
`plans/ai/` to `plans/active/` on 2026-05-07 per PM commit `d968b5d3`). Owner-side todos:

- [ ] [AGENT] P0. **Phase 1 audit** — walk the deployment-ui data-status panel for each (service, asset_group) and
      compare the rendered drill-down hierarchy against the codex shard-key matrix in CLAUDE.md
      `§ Per-asset-group shard-key matrix`. Expected matrix: [AUDIT 2026-05-07: BLOCKED-ON
      data_status_drilldown_shard_atom_alignment_2026_05_07:Phase-1-audit; tracked in own active plan]
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
      levels per asset_group). [AUDIT 2026-05-07: BLOCKED-ON
      data_status_drilldown_shard_atom_alignment_2026_05_07:Phase-2-endpoint]
- [ ] [SCRIPT] P0. **Phase 3 deployment-ui component** — replace the current hardcoded 2-level drill-down
      (`venue → data_type`) with a recursive renderer that walks the per-asset_group axis chain from the
      `/api/config/shard-axis-matrix` endpoint (already shipped in deployment-api@`85053fe`). Each level is collapsible;
      the leaf level always shows per-day download icons + schema modal trigger. [AUDIT 2026-05-07: BLOCKED-ON
      data_status_drilldown_shard_atom_alignment_2026_05_07:Phase-3-renderer]
- [ ] [SCRIPT] P0. **Phase 4 per-shard download + missing-day surfacing** — every leaf node renders one icon-per-day
      with hover tooltip showing `attempted_at` / `error_reason` / `probed_paths` for missing days. Backend
      `probed_paths` field shipped deployment-api@`4ca4bb7`; UI must surface it. [AUDIT 2026-05-07: BLOCKED-ON
      data_status_drilldown_shard_atom_alignment_2026_05_07:Phase-4-leaf-icons; backend probed_paths confirmed shipped
      deployment-api@`4ca4bb7`]
- [ ] [SCRIPT] P0. **Phase 5 MTDS CLI shard-targeting flags** — `market-tick-data-service` CLI gains `--shard-key`
      (compound key string per asset_group), `--instrument-type`, `--root`, `--instrument-id`, `--day`,
      `--canonical-question-group`. Operator clicking a missing-day download icon in the UI gets a copy-paste-ready CLI
      invocation that recovers exactly that shard atom (no broader collateral re-fetch). [AUDIT 2026-05-07: FRESH —
      actionable; verified MTDS CLI does NOT have `--shard-key` / `--root` / `--day` / `--canonical-question-group`
      flags (`grep` in `cli/main.py` returns 0 hits — only existing `--venues` / `--data-types` / `--instrument-ids`);
      critical-path for operator UX after Phase 4 lands]

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
  - Compare the actual depth to the codex shard-key matrix expected depth. [AUDIT 2026-05-07: FRESH — actionable; gating
    audit step for Phase 3 verification]
- [ ] [DOC] P0. Output a coverage matrix at `unified-trading-pm/codex/02-data/deployment-ui-drilldown-depth-audit.md`
      listing every (service, asset*group, venue, data_type) tuple as one of: `WORKING` /
      `STOPS_AT_INTERMEDIATE_LEVEL*<level>`/`MISSING_SCHEMA_MODAL`/    `MISSING_DOWNLOAD_ICON`. Reference incidents     (CBOE ohlcv_15m = WORKING, CME combo/\* = STOPS_AT_DATA_TYPE) per the operator screenshot. [AUDIT 2026-05-07: FRESH — actionable; verified `unified-trading-pm/codex/02-data/deployment-ui-drilldown-depth-audit.md`does NOT exist (only`data-status-drilldown.md`+`shard-granularity-cefi.md`);
      doc creation is greenfield]
- [ ] [VERIFY] P0. After B.2 Phase 3 deployment-ui renderer ships: re-walk the same audit; every entry in the matrix
      flips to `WORKING`. Block Phase 5 (MTDS CLI shard-targeting) sign-off until the matrix is 100% green. [AUDIT
      2026-05-07: BLOCKED-ON data_status_drilldown_shard_atom_alignment_2026_05_07:Phase-3-renderer]
- [ ] [VERIFY] P0. Schema modal works at every leaf — confirm via Playwright walk (B.2 Phase 3's Playwright coverage
      extends here). [AUDIT 2026-05-07: BLOCKED-ON infrastructure_master:deployment-ui-Playwright-walk; SchemaModal
      wired in deployment-ui@`7309b56`/`537d468`; per-leaf coverage pending]

### Manifest cleanup HARD RULE (migrated from `manifest_cleanup_on_entity_add_remove_2026_05_08`)

Source issue archived. Today's manifest reconciliation tool (`reconcile_phantom_manifest_rows_all.py`) runs REACTIVELY
as periodic audit, not PREVENTIVELY at feature-add time. 2026-04-29 + 2026-05-04 incidents (167k + 130k phantom rows
discovered weeks/days after the change shipped) show drift goes undetected. No workspace rule mandates manifest cleanup
as acceptance criterion when entities are added/removed.

**Cross-plan effect (CRITICAL — banner added per plan)**: every active 2026-05-08 issue migration that adds/removes
entities (sports_master fixtures-split + cross-source-status + per-fixture iteration; defi_master chain-coverage CLOB
venues + governance-params; tradfi_master futures-expiry + session-type + CME backfill; predictions_master
canonical-groups backfill) MUST include explicit manifest cleanup acceptance criteria after this rule lands. Reviewers
reject migration commits that touch `DATA_TYPES_BY_ASSET_GROUP` / `VENUES_BY_ASSET_GROUP` / canonical entity registries
without the cleanup-script output attached.

**Cross-plan dependency**: Phase 1 below depends on writegate Phase 3.D.5 Wave 3 v2 enumerator existing to re-populate
`expected_unattempted` rows on `--add` (per archived issue's "Phase coordination required" callout).

- [ ] [HUMAN+AGENT] P1. **CLAUDE.md NEW workspace rule "Manifest cleanup on entity add/remove (HARD RULE)"** — mandatory
      checkbox section in any commit that touches an entity registry. Symlinks propagate to all repo-mirrors. Body:
      "When you add or remove a venue / data_type / canonical-group / chain / instrument-type from any UAC
      `*_BY_ASSET_GROUP` registry or canonical lifecycle SSOT, you MUST: (a) run
      `instruments-service/scripts/reconcile_manifest_after_entity_change.py --add|--remove --asset-group=X     --entity-type=Y --entity-key=Z`
      (NEW script — Phase 3 below); (b) attach the script's audit-CSV output to the PR description; (c) the audit must
      show ZERO orphan rows (rows whose entity is no longer in the registry but the manifest still has captured/empty
      rows for it). Reviewers reject PRs that don't include this output."
- [ ] [SCRIPT] P1. **`entity-lifecycle-cleanup.sh` workflow script** under
      `unified-trading-pm/scripts/lifecycle/entity-lifecycle-cleanup.sh`. Wraps the per-asset-group reconciler runs
      (instruments-service script Phase 3 below) into a single command. Output goes to a deterministic CSV path under
      `unified-trading-pm/audits/entity_lifecycle/by_date/day=<YYYY-MM-DD>/...csv`.
- [ ] [SCRIPT] P1. **`reconcile_manifest_after_entity_change.py`** under `instruments-service/scripts/`. `--add` mode:
      walks UAC entity registry post-change; for each entity-day-row that's now newly-expected (per writegate Phase
      3.D.5 v2 enumerator), writes `record_expected_unattempted` rows into the per-VM shard. `--remove` mode: walks the
      manifest for the removed entity; flips orphan rows to a tombstone status
      (`record_failed(REMOVED_ENTITY_TOMBSTONE)`) and emits the audit CSV. Idempotent + dry-run-by-default. **DEPENDS ON
      writegate Phase 3.D.5 Wave 3 v2 enumerator** for the `--add` path.
- [ ] [HUMAN+AGENT] P1. **Retroactive audit of 90-day commit history.** Walk
      `git log origin/live-defi-rollout --since='90 days' -p -- unified-api-contracts/.../canonical/crosscutting/     unified-api-contracts/.../canonical/domain/`;
      for every commit that adds/removes an entity, run the Phase 3 script in audit-only mode; collect every orphan row.
      Output: a single audit report under `unified-trading-pm/audits/entity_lifecycle/retroactive_90d_2026_05_08.csv`.
- [ ] [HUMAN+AGENT] P1. **Retroactive bulk reconciler run for stragglers** identified by the audit above. Operator
      decision per orphan: tombstone (most common) vs re-fetch (when the entity was removed by accident and the data is
      still useful) vs delete (when both removal + manifest were wrong).
- [ ] [SCRIPT] P1. **PM `quality-gates.sh` STEP 5.65 — entity-registry CI gate.** AST-walk: any commit that touches
      `DATA_TYPES_BY_ASSET_GROUP` / `VENUES_BY_ASSET_GROUP` / `PROTOCOL_LAUNCH_DATES` / `LST_TOKEN_GENESIS` /
      `PREDICTION_GROUPS` / `*_LAUNCH_DATES` registries MUST also include a CSV path under
      `unified-trading-pm/audits/entity_lifecycle/` referenced in the commit body OR an `[entity-skip-cleanup]` tag with
      operator-explained reason. Fails CI otherwise.

### Hard schema enforcement at write boundary (NEW sub-plan reference)

NEW sub-plan: `hard_schema_enforcement_2026_05_08.plan.md` (sibling to this master) — workspace-wide hard schema
enforcement at the write boundary. Operator decision 2026-05-08: SEQUENCE rather than bundle with futures-expiry work —
futures-expiry (tradfi_master Batch D) ships first, then this workspace-wide enforcement second. Detail lives in the
sub-plan; this section is a pointer.

- [ ] [POINTER] P0. **See `hard_schema_enforcement_2026_05_08.plan.md`** for the full per-asset-group UAC schema audit +
      per-row record_failed(SCHEMA_VALIDATION_FAILED) gate refactor + sports adapter full-column capture audit +
      manifest row_key shape validation + QG STEP 5.66 static assertion. Sub-plan referenced from this
      infrastructure_master umbrella; coordinate completion gates on both.

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

- Master plan: [`master_to_live_defi_2026_05_23.plan.md`](../active/master_to_live_defi_2026_05_23.plan.md).
- Write-gate cluster:
  [`writegate_honest_coverage_endtoend_2026_05_06.plan.md`](../active/writegate_honest_coverage_endtoend_2026_05_06.plan.md).
- Asset_group vocabulary:
  [`venue_axis_asset_group_vocabulary_2026_04_25.plan.md`](../archive/venue_axis_asset_group_vocabulary_2026_04_25.plan.md).
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
- `venue_axis_asset_group_vocabulary_2026_04_25.plan.md` — 2 absorbed SSOT-cleanup items (`venue_start_dates` deletion
  - dashboard SSOT verify) lifted above; `poolGetSnapshots` historical-TVL item folded into `defi_master_2026_05_07`;
    Waves A/B/C/D/E vocabulary migration shipped per CLAUDE.md "Asset-group vocabulary" section.
