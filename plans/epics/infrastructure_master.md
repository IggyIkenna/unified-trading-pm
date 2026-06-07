---
name: infrastructure_master
title: "Infrastructure Master — shard / data-status / deployment-build umbrella"
type: epic
tier: L4
status: active
priority: P0
assigned_vm: vm-cross-cutting
parent: master_to_live_defi_2026_05_23
created: 2026-05-07
last_updated: 2026-05-22
locked_by: live-defi-rollout
locked_since: 2026-05-07
related_plans:
  - ../archive/2026_05/workspace_qg_sweep_2026_05_23.md
  - ../archive/2026_05/aws_migration_defi_first_2026_05_07.md
  - ../archive/2026_05/audit03_deployment_cron_provisioning_2026_05_22.md
  - ../archive/2026_05/vm_launcher_startup_url_migration_2026_05_21.md
  - ../archive/2026_05/aws_cloud_toggle_and_backfill_parity_2026_05_22.md
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
  are the migration target); `manifest_migration_SUPERSEDED_2026_05_21` Stage 4 (raw-tables migration ordering)
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
  - The B.2 drilldown plan is in `plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.md` (its own active
    plan), NOT in `plans/ai/` as the prose says — it was promoted on 2026-05-07 per PM commit `d968b5d3`. Reference text
    in plan body is now outdated.
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
[`manifest_migration_SUPERSEDED_2026_05_21.md`](./manifest_migration_SUPERSEDED_2026_05_21.md) for sequencing DAG,
conflicts, VM impact (per-table mini-pauses for sports FWD on raw-tables migration), and operator gates. Constraints:
`_ensure_timestamp` shim DELETE is GATED on raw-tables migration completion; raw-tables migration runs AFTER Stage 3
reconcilers + `mtds-s4-10` rescan complete.

### Shard granularity propagation (`shard_granularity_ssot_propagation`)

- [x] [HUMAN] P0. Phase 0 → Phase 1 handover sign-off; user converts findings into per-service fix todos in Phase 1.
      [AUDIT 2026-05-07: STALE — handover folded into umbrella; Phase 0 audit findings (multi-axis correction `456acb9`
      + B.2/C.13) were converted by sub-agent into the per-service todos already in this plan; no separate human
      sign-off remaining] **CLOSED-AS-STALE 2026-05-08** — handover already folded; no separate sign-off needed.
- [x] [AGENT] P0. **#1 MDPS 1440-NaN reproduction path** — the canonical per-shard test case for shard-atom alignment
      regressions. [AUDIT 2026-05-07: STALE — superseded by writegate Phase 2.A (`_create_empty_output` deletion across
      all asset_groups, MDPS@`5b52d0b`/`b9f9328`/`80cf141`/`e9520a0`) AND retrospective cleanup script MDPS@`d3be0ef`
      `mdps_reconcile_1440_nan_placeholders.py`. Reproduction-test value moot — the bug is fixed at write-time AND
      backfill-cleaned] **CLOSED-AS-STALE 2026-05-08** — write-side bug fixed + on-disk cleanup ran; reproduction
      regression test no longer load-bearing.
- [ ] [AGENT] P0. **Raw tables migration** (next slice — BLOCKED-UPSTREAM): 14 entries in `TABLE_TO_EXPORT` at
      `features-service/features_service/sports/cli/batch_write.py:22` (features-sports-service consolidated into
      features-service; old path in 2026-05-07 audit is stale). Reference tables already have manifest tracking in
      `batch_handler.py:_run_reference_tables` with `row_key={"date":..., "feature_group":...}`. Design question: pick
      canonical shard granularity per table (static tables like leagues/teams/venues should be per-season not daily;
      C.1 + C.11 audit findings). [AUDIT 2026-05-22 slot-11: BLOCKED-UPSTREAM — gated on (1) sports rename Stage 1
      (operator-gated, not done), (2) UAC `SchemaContract.cadence` field (not in contracts.py:92 yet), (3) new
      `EXPECTED_DEPRECATED_DATA_TYPE` + `EXPECTED_REFDATA_CADENCE_CHANGE` reason codes in UAC `honest_coverage.py`.
      Stage 4 of `manifest_master` epic (vm-defi). No slot-11 action until prerequisites clear.]
- [x] [AGENT] P0. **Delete `_ensure_timestamp` shim** — once all 14 raw tables migrate, drop the midnight UTC fallback.
      Coordinated with writegate Phase 2.C. [AUDIT 2026-05-22 slot-11: STALE/RESOLVED — `_ensure_timestamp` is NOT in
      active code in features-service (the consolidated repo). It appears ONLY in comments: `data/writer.py:120`
      (comment: "Phase 2.C writegate: _ensure_timestamp shim removed") + `exporters/odds_features_exporter.py:332`
      (comment). The shim was removed as part of Phase 2.C writegate when features-sports-service was consolidated into
      features-service. The old path `features-sports-service/...` no longer exists. **CLOSED-AS-RESOLVED 2026-05-22** —
      shim already gone.]
- [ ] [AGENT] P0. All affected downstream consumers updated in this plan (no "fix later"). [AUDIT 2026-05-07: BLOCKED-ON
      infrastructure_master:raw-tables-migration]
- [ ] [VERIFY] P0. Manifest reads + writes use same shard key for every (service, data_type). [AUDIT 2026-05-07: FRESH —
      verification gate; depends on raw-tables migration completion]
- [ ] [VERIFY] P0. Data-status surfaces match writer granularity (audit report only — UI fix tracked separately). [AUDIT
      2026-05-07: BLOCKED-ON infrastructure_master:Audit-findings-B.2-drilldown-depth-audit; UI fix lives in
      `data_status_drilldown_shard_atom_alignment_2026_05_07.md`]
- [ ] [VERIFY] P0. No fallback paths remain for migrated manifests. [AUDIT 2026-05-22 slot-11: PARTIAL —
      `_ensure_timestamp` fallback already gone (Phase 2.C writegate + consolidation); deployment-api@`64d2be9` dropped
      DEFI legacy-venue fallback; remaining open scope is raw-tables canonical-shape design (BLOCKED-UPSTREAM per item
      above)]
- [ ] [VERIFY] P0. Tests cover write-gates: row=0 → fail loud, high NaN → fail loud, schema mismatch → fail loud. [AUDIT
      2026-05-07: FRESH — verification gate; `record_empty(reason=...)` + `record_failed` shipped via UTL@`958634f9`;
      per-test-fixture verification across services pending]
- [ ] [VERIFY] P0. `available_at` end-to-end smoke: write feature at t-24, verify no input row consumed has
      `available_at > t-24-horizon`. [AUDIT 2026-05-07: FRESH — verification gate; UTL@`cf312f66`
      `availability_stamping` shipped + `LookaheadBiasError` raised in features-onchain `lst_yields`; smoke gate across
      all features-* pending]

### Data-status multi-axis (`data_status_multi_axis_shard_propagation`)

- [x] [features-onchain] P1. Each calculator writes `feature_group=` matching its upstream source (`lending_rates`,
      `lst_yields`, etc.). [AUDIT 2026-05-07: VERIFIED-LIKELY-DONE —
      `features-onchain-service/features_onchain_service/adapters/onchain_writer.py:23` documents the path layout
      `by_date/day={date}/feature_group={group}/{protocol}.parquet` and `engine/orchestrator.py` has 13+
      `feature_group=` write sites (lines 134/164/192/200/208/257/575/584/1155/1187/1220 covering `lst_yields` /
      `lending_rates` / `macro_sentiment` / `rate_impact` / per-feature-group); flip after spot-check of writer fixture
      tests] **VERIFIED 2026-05-08 (cluster-1 audit)** — 11 `feature_group=` write sites in `engine/orchestrator.py`
      confirmed via grep; writer documentation at `adapters/onchain_writer.py:23` confirmed.
- [x] [features-calendar] P1. Each source writer (FRED, tradingeconomics, sec, holiday_calendar) populates
      `feature_group`. [AUDIT 2026-05-07: VERIFIED-LIKELY-DONE —
      `features_calendar_service/engine/calendar_orchestrator.py:167-390` has 8+ `feature_group=` plumb-through sites;
      `engine/calculators/economic_events.py:56` declares `self.feature_group = "economic_events"`; flip after
      writer-test spot-check] **VERIFIED 2026-05-08 (cluster-1 audit)** — 37 `feature_group` references in
      `engine/calendar_orchestrator.py` confirmed via grep.
- [x] [features-cross-instrument / multi-timeframe] P1. Confirm `timeframe` populates correctly. (verified 2026-05-07:
      features-multi-timeframe-service/features_multi_timeframe_service/engine/orchestrator.py:127/258 has timeframe=
      write plumb) [AUDIT 2026-05-07: VERIFIED —
      `features-multi-timeframe-service/features_multi_timeframe_service/engine/orchestrator.py:127/258` has
      `timeframe=` write plumb; ready to flip]
- [x] ✅ [tests] P1. Per-service unit test: write under a `job_id`, assert manifest has populated `job_id`. —
      strategy@`2545b0be` / execution@`f821db863` (tests pushed to LDR 2026-05-27); ml-training@`78ab138` / ml-inference
      (tests committed locally — repos archived on GitHub, cannot push). Writer wiring confirmed: ml-training@`f7369f2`
      / ml-inference@`69d6313` / strategy@`90e00bb` / execution@`0b664d99` Phase 1B job_id writers; 3 tests per service
      pass (12 total). [ARCHIVED-REPO NOTE: ml-training-service + ml-inference-service are GitHub-archived (read-only).
      Tests exist in slot-7 worktree but remote push blocked. Tests for active repos fully verified.]
- [ ] [deployment-ui] P3. Visual regression smoke: Playwright walk across all 15 services × 5 asset_groups (where
      applicable). [AUDIT 2026-05-07: FRESH — actionable; deferred per CLAUDE.md DEFI canonicalisation closeout
      2026-05-07 ("B.2 Playwright walk across 15 services × 5 asset_groups deferred — needs full local stack + manual
      visual"); P3 deferral acceptable for May-23 deadline]
- [ ] [feature_group backfills] P4. **If** Phase 1A audit finds a per-service writer that has never populated
      `feature_group`, backfill the manifest column for historical rows. [AUDIT 2026-05-07: BLOCKED-ON
      infrastructure_master:Phase-1A-audit-feature_group; conditional on audit finding]
- [x] [deployment-api / scripts/data_status_rollup_worker.py] P5. Update worker to emit `breakdowns` in the rollup blob.
      [AUDIT 2026-05-07: VERIFIED-LIKELY-DONE —
      `deployment-api/deployment_api/services/data_status_service.py:3126-3288` has `_build_breakdowns` method +
      per-(service, asset_group) breakdowns wired at line 3284-3288; deployment-api@`8056995` shipped per-asset-group
      breakdowns accordion + UAC SSOT axis matrix; rollup-worker @`44b4a98` shipped coverage-summary fast-path; flip
      after rollup blob inspection] **VERIFIED 2026-05-08 (cluster-1 audit)** — `_build_breakdowns` confirmed at
      `data_status_service.py:3299` + caller wired at `:3461`.
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
`dex_historical_replay_lighter_extended_pacifica_2026_05_07.md`. **Two follow-ups carry over and live here.**

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

**Source**: `plans/ai/session_2026_05_07_data_status_audit_findings.md` rows B.2 + C.13 (added 2026-05-07 from operator
screenshot). Operator surfaced two related drill-down issues during the deployment-ui walkthrough: (1) the hierarchy
depth doesn't match the codex shard-key matrix per asset_group, and (2) drill-down terminates at different depths for
different (service, venue, data_type) combinations — some land at per-day download icons + schema modal (working
correctly), others stop one level short (broken).

#### B.2 — Drill-down hierarchy must match codex shard-key matrix per asset_group

Plan in `plans/active/data_status_drilldown_shard_atom_alignment_2026_05_07.md` (5 phases — promoted from `plans/ai/` to
`plans/active/` on 2026-05-07 per PM commit `d968b5d3`). Owner-side todos:

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
- [x] ✅ [SCRIPT] P1. **`entity-lifecycle-cleanup.sh` workflow script** under
      `unified-trading-pm/scripts/lifecycle/entity-lifecycle-cleanup.sh`. Wraps the per-asset-group reconciler runs
      (instruments-service script Phase 3 below) into a single command. Output goes to a deterministic CSV path under
      `unified-trading-pm/audits/entity_lifecycle/by_date/day=<YYYY-MM-DD>/...csv`. — PM@fb7205eff 2026-05-27 slot-7.
- [x] ✅ [SCRIPT] P1. **`reconcile_manifest_after_entity_change.py`** under `instruments-service/scripts/`. `--add`
      mode: walks UAC entity registry post-change; for each entity-day-row that's now newly-expected (per writegate
      Phase 3.D.5 v2 enumerator), writes `record_expected_unattempted` rows into the per-VM shard. `--remove` mode:
      walks the manifest for the removed entity; flips orphan rows to a tombstone status
      (`record_failed(REMOVED_ENTITY_TOMBSTONE)`) and emits the audit CSV. Idempotent + dry-run-by-default. **DEPENDS ON
      writegate Phase 3.D.5 Wave 3 v2 enumerator** for the `--add` path. — IS@af302bcb QG green. --remove path fully
      implemented; --add stubs NotImplementedError (BLOCKED-ON writegate Phase 3.D.5). 2026-05-27 slot-7.
- [ ] [HUMAN+AGENT] P1. **Retroactive audit of 90-day commit history.** Walk
      `git log origin/live-defi-rollout --since='90 days' -p -- unified-api-contracts/.../canonical/crosscutting/     unified-api-contracts/.../canonical/domain/`;
      for every commit that adds/removes an entity, run the Phase 3 script in audit-only mode; collect every orphan row.
      Output: a single audit report under `unified-trading-pm/audits/entity_lifecycle/retroactive_90d_2026_05_08.csv`.
- [ ] [HUMAN+AGENT] P1. **Retroactive bulk reconciler run for stragglers** identified by the audit above. Operator
      decision per orphan: tombstone (most common) vs re-fetch (when the entity was removed by accident and the data is
      still useful) vs delete (when both removal + manifest were wrong).
- [x] ✅ [SCRIPT] P1. **PM `quality-gates.sh` STEP 5.91 — entity-registry CI gate.** Any commit that touches
      `DATA_TYPES_BY_ASSET_GROUP` / `VENUES_BY_ASSET_GROUP` / `PROTOCOL_LAUNCH_DATES` / `LST_TOKEN_GENESIS` /
      `PREDICTION_GROUPS` / `*_LAUNCH_DATES` / `*_GENESIS_DATES` registries MUST also include a CSV path under
      `unified-trading-pm/audits/entity_lifecycle/` referenced in the commit body OR an `[entity-skip-cleanup]` tag with
      operator-explained reason. Fails CI otherwise. Note: shipped as STEP 5.91 (STEP 5.65 is already taken by
      removed-symbol AST-walk). — PM@4cc92ac20 + check_entity_registry_cleanup.py + base-service.sh. QG green.
      2026-05-27 slot-7.

### Hard schema enforcement at write boundary (NEW sub-plan reference)

NEW sub-plan: `hard_schema_enforcement_2026_05_08.md` (sibling to this master) — workspace-wide hard schema enforcement
at the write boundary. Operator decision 2026-05-08: SEQUENCE rather than bundle with futures-expiry work —
futures-expiry (tradfi_master Batch D) ships first, then this workspace-wide enforcement second. Detail lives in the
sub-plan; this section is a pointer.

- [ ] [POINTER] P0. **See `hard_schema_enforcement_2026_05_08.md`** for the full per-asset-group UAC schema audit +
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

## Assigned active plans

_1 active plans declare `parent_epic: infrastructure_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`workspace_qg_sweep_2026_05_23`](../archive/2026_05/workspace_qg_sweep_2026_05_23.md)

**status**: ✅ ARCHIVED 2026-05-26 — All items completed. Workspace-wide QG green sweep. All 20 Python repos to
`bash scripts/quality-gates.sh` exit 0. Dep-chain: UAC → UTL → IS/deployment-service → MTDS/features/strategy/execution
→ ML/misc. Fan-out across vm-cross-cutting (root + misc), vm-cefi (instruments-service), vm-ml (data pipeline),
vm-trading-core (trading machinery), vm-operator-ops (deployment-service/api). Pre-flight ruff counts recorded in plan
body. · **estimate**: 1.2 cal AI-days (class: refactor, 0.4× multiplier)

### [`audit03_deployment_cron_provisioning_2026_05_22`](../archive/2026_05/audit03_deployment_cron_provisioning_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — All 11 todos done. F-39/40/41/42 Cloud Run Jobs + Cloud Scheduler crons provisioned
on GCP; F-43 Solana devnet paper path; F-44 ManualTradeGateDialog Playwright e2e. BLRS dry-run succeeded;
strategy-service CRJ provisioned. · **estimate**: 2.0 cal AI-days (class: infra)

### [`defi_coverage_capability_alignment_2026_05_22`](../archive/issues/defi_coverage_capability_alignment_2026_05_22.md) — Bug 5 DeFi venue GCS re-key chain

**status**: 🟢 MIGRATION CHAIN DONE (B5.1-B5.9) — residual B5.9b + Bug 4 post-cutover. Root-cause code shipped (B5.1 IS
writer parquet-path canonicalisation UAC@fdc9206b + IS@a57ae01c; B5.2 no-op). Migration chain (HARD-ORDERED,
single-walk-discipline gate) **COMPLETE 2026-05-27**: **B5.3** GCS re-key glued→underscore (35,011 objects, 0 errors) →
**B5.4** manifest reconcile (audited GREEN, no corrector needed) → **B5.5** delete old glued keys (0 glued remain both
buckets) → **B5.6 [UI]** deployment-api pool-breakdown resolves canonical (no code change) → **B5.7 (VERIFY)** re-drill
done. **B5.8 (P3)** stale-comment cleanup. **B5.9 — ZKSYNC re-key (operator approved 2026-05-27) DONE**:
unified-api-contracts@ac5d2340 added `ZKSYNC` to `KNOWN_CHAINS` (chain-token recognition set, no expected-coverage
expansion, consumer pre-audit clean) + re-keyed **446 `PANCAKESWAPV3-ZKSYNC` → `PANCAKESWAP_V3-ZKSYNC`**
(instruments-service@445756d3, 0 errors); `LIGHTER-ZKSYNC` correct no-op (654 untouched); MTDS 0 glued ZKSYNC. **⚠️
Superseded the 2026-05-06 `purge_pancakeswapv3_zksync.py` "do not add ZKSYNC" decision** (purge never ran on the IS
partitions). Also Bug 2 residual (`liquidation_events_handler` venue casing) fixed MTDS@c60eb053. **Open residuals
(NICE-TO-HAVE, P3)**: **B5.9b** stale purge-script comment + MTDS combined-vs-protocol-only venue duality +
`EXTENDED-STARKNET`/`PACIFICA-SOLANA` universe confirm; **B5.10** pool-breakdown can't read migrated
`pipeline_mode`/flat parquets. **Bug 4 (POST-CUTOVER)**: add a `data_source_type` taxonomy enum so LST venue `ANKR`
(ankrETH) vs RPC-provider `ANKR` (and `ALCHEMY`/`CHAINLINK`/`GAS_FEES` grid contaminants, DQ-04) are distinguishable —
fold the `oracle_prices_handler` `COINBASE-SPOT`-into-defi-grid filter fix in here. Full phased todos in the (now
archived) issue doc.

## P1 — important; post-current-gate

### [`vm_launcher_startup_url_migration_2026_05_21`](../archive/2026_05/vm_launcher_startup_url_migration_2026_05_21.md)

**status**: ✅ ARCHIVED 2026-05-23 — All 17 todos done. 22 data-pipeline launchers converted to Pattern A
(startup-script-url); 11 Pattern B exceptions documented in codex. Codex `vm-tarball-deployment.md` updated ✅
2026-05-21. · **estimate**: 2.4 cal AI-days (class: infra)

### [`aws_migration_defi_first_2026_05_07`](../archive/2026_05/aws_migration_defi_first_2026_05_07.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-5b complete (DeFi-first: 10 S3 buckets, 346k objects / 36.83 GB migrated,
Glue DB + Athena configured). Phase 5 cross-cloud rsync + Phase 6 ECS Fargate + Phase 9 full-workspace
DEFERRED-POST-CUTOVER. · **estimate**: 32 cal AI-days (class: infra)

## P2 — useful; opportunistic

_(no plans currently assigned at this priority)_

## Archived plans

### [`aws_migration_defi_first_2026_05_07`](../archive/2026_05/aws_migration_defi_first_2026_05_07.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-5b complete (DeFi-first).

**Deferred (migrated):**

- **Phase 5 — Cross-cloud data rsync**: DEFERRED-POST-CUTOVER. Gated on GCP manifest + data-quality green (master plan
  Gate 4).
- **Phase 6 — ECS Fargate deployment (OPERATOR ACTION)**: BLOCKED-OPERATOR. Full service deployment to AWS ECS using ECR
  images.
- **Phase 9 — Full-workspace rollout**: Extend AWS dual-cloud from DeFi-first to all asset groups post-cutover.

### [`aws_cloud_toggle_and_backfill_parity_2026_05_22`](../archive/2026_05/aws_cloud_toggle_and_backfill_parity_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-4 done: AWS cloud toggle wired end-to-end (service+route+UI layers),
GCP|AWS toggle button live, 8 AWS backfill launcher scripts created + QG green. 3 items DEFERRED-OPERATOR-DECISION
(BLOCKED-GCP-BACKFILL-COMPLETE). · **estimate**: 3.0 cal AI-days (class: brand-new)

**Deferred (MIGRATED FROM archived plan)** — BLOCKED-GCP-BACKFILL-COMPLETE backlog:

- **SMOKE-1 — AWS 1-day smoke test (P0, BLOCKED-GCP-BACKFILL-COMPLETE)**: For each asset_group × service (MTDS × 5 +
  MDPS × 3 + IS × 5), fetch 1 day via deployment-api `?cloud=aws` and verify non-zero captured rows.
- **SMOKE-2 — Data-status UI AWS toggle verify (P0, BLOCKED-GCP-BACKFILL-COMPLETE)**: Toggle to AWS; verify cells
  render.
- **SMOKE-3 — Document smoke result (P0, BLOCKED-GCP-BACKFILL-COMPLETE)**: Per-cell result table at
  `plans/audit/results/aws_smoke_1day_<date>.md`. Gate for full AWS backfill execution.

## P3 — backlog; revisit quarterly

- [ ] [INFRA] P3. **uv-pin drift-guard** (**MIGRATED FROM:** `uv_lockfile_determinism_2026_06_02.md`, archived
      2026-06-07). Build a PM `quality_gates/` check that greps the 4 uv-pin sites (`setup.sh`, `base-service.sh` +
      `base-library.sh`, `python-quality-gates-v2.yml`, `../unified-trading-library/Dockerfile`) and fails if their
      pinned `uv` versions disagree. No active drift today (all `0.10.8`) → low priority. ⚠️ **COORDINATION:** touches
      `base-service.sh` — a shared QG surface also edited by `cicd_contract_hardening` (H5 sentinel + QG-debt steps);
      coordinate edits to avoid a collision.
- [ ] [INFRA] P2. **Fleet per-repo local-QG debt sweep** (**MIGRATED FROM:** `uv_lockfile_determinism_2026_06_02.md`,
      archived 2026-06-07). The bash-3.2 governor fix unmasked each repo's accumulated stage-5+ local-QG debt (codex /
      cloudbuild-schema / size-import baselines) that the crash had been hiding. Walk every repo's
      `quality-gates.sh     --no-fix` locally and clear the surfaced debt. **Overlaps `utl_full_quality_gates_green`**
      (the T0 QG-green effort) — coordinate the per-repo greening there; most repos already proved green on LDR
      (2026-06-07 fleet drain), so this is the residual local-only tail.
- [ ] [INFRA] P3. **VM-side QG-memory baseline** (**MIGRATED FROM:**
      `quality_gates_resource_contention_speedup_2026_06_02.md`, archived 2026-06-07). The per-repo QG resource
      baseline + 2× deviation guard is DONE for the 20-repo LOCAL baseline (`scripts/dev/qg_resource_baseline.json`,
      guard in `base-service.sh:2518-2529`); the VM-side baseline is deferred — blocked on `qg-cw-memory-agent` (the
      CloudWatch memory agent is not yet installed on fleet VMs; the `vm` key is absent from the baseline JSON until
      that lands). Install the CW agent on the fleet, then capture the VM baseline.
- [ ] [INFRA] P3. **QG aggregate-storm validation (K∈{4,8} on a shared host)** (**MIGRATED FROM:**
      `quality_gates_resource_contention_speedup_2026_06_02.md`, archived 2026-06-07). `benchmark-qg-under-load.sh` is
      BUILT + smoke-clean; the actual K∈{4,8} concurrent-QG storm on a shared host is deferred to a coordinated window
      (it deliberately induces the thrash the plan fixes — must not run during active fleet work). Run it in a quiet
      window to confirm the host-governor serialization holds under real oversubscription.
- [x] [AGENT] P3. **UTL `STANDARD_CATEGORIES` lowercase** (**MIGRATED FROM:**
      `audit03_deployment_cron_provisioning_2026_05_22.md` Phase 4) — UTL `service_cli.py` STANDARD_CATEGORIES should
      include lowercase asset-group choices (`cefi`/`defi`/`tradfi`/`sports`/`prediction`) to match canonical vocabulary
      per CLAUDE.md. Small UTL change; no urgency for May-23. — ✅ **DONE 2026-05-26 slot-7** | UTL@c7294847 | Added
      lowercase + uppercase variants; uppercase kept for backward compat with launcher scripts.
- [ ] [AGENT] P3. **`launch-gcs-migration-bundle-vm.sh` GCS script staging** (**MIGRATED FROM:**
      `vm_launcher_startup_url_migration_2026_05_21.md` Pattern B note) — Consider moving the per-run migration script
      from unified-trading-pm to `CODE_BUCKET/scripts/` to enable a future Pattern A conversion. Low priority; Pattern B
      is correct for now.
- [ ] [SCRIPT] P3. **VM startup `gsutil -m cp` wheel-cache step deadlocks → boot-hang (make non-blocking / drop `-m`).**
      **MIGRATED FROM:** `plans/active/issues/running_vm_fleet_status_2026_05_27.md` § C (archived 2026-06-07). The VM
      startup script's final "Caching compiled wheels to GCS" step runs
      `gsutil -m -q cp /tmp/wheel-cache/*.whl     gs://…/wheels/…`; the snap-bundled `gsutil -m` (multiprocessing)
      deadlocked (parent gsutil alive, defunct `[python3]` zombie workers) and the **startup script blocks on it** →
      `market_tick_data_service` never launches (observed on bybit-2024 / hyperliquid-2025 / kraken-2024 — never
      self-recovers). Also violates the workspace rule that per-object GCS ops use `gcs_copy_object` (REST), not
      subprocess `gsutil` (codex `gcs-object-operations.md`). Fix: make the wheel-cache step non-blocking /
      timeout-guarded / drop `-m` (or use the `gcs_copy_object` helper). Repo: `deployment-service` (VM launcher /
      startup script).

> **MIGRATED FROM:** `aws_migration_defi_first_2026_05_07.md` (archived 2026-05-23) — DeFi S3/Athena/Glue migration
> complete; remaining items are AWS parity extensions + post-cutover cross-asset-group work.

- [x] [AGENT] P2. **GCP Pub/Sub topic inventory** — inventory all Pub/Sub topics + subscriptions; document UCI
      `MessageBus` abstraction gap (deploy-service currently GCP-only; AWS SNS equivalent not wired). Gate: confirm
      whether AWS SNS mirroring is needed before post-cutover backfill VMs launch. — **DONE 2026-05-26 slot-7** |
      PM@b32702f60 | Findings: 23 TF-managed event-bus topics + 38 legacy/unmanaged. AWS SNS NOT required before
      backfill VMs launch (AWS VMs write S3 only; event bus is GCP-services only). MessageBus abstraction needed only
      when services migrate to AWS ECS (post-cutover). Cleanup: 2 duplicate hyperliquid topics + 1 typo topic. Full
      inventory: `codex/05-infrastructure/pubsub-topic-inventory.md`.
- [ ] [AGENT] P2. **UCI `MessageBus` abstraction** — once inventory done (✅), create `MessageBus` interface in UTL that
      wraps GCP Pub/Sub + AWS SNS behind a single emit API driven by `CLOUD_PROVIDER` env. Required for service repos to
      push events to both clouds in dual-cloud mode. **DEFERRED — gated on services migrating to AWS ECS
      (post-cutover)**. Implementation path documented in `codex/05-infrastructure/pubsub-topic-inventory.md`.
- [x] [AGENT] P2. **`defi-validation` key in `cloud-providers.yaml`** — GCP has `defi-validation` bucket in
      `configs/cloud-providers.yaml`; AWS does not. Add corresponding S3 bucket key so `resolve_bucket_name()` works on
      AWS. — **ALREADY DONE**: `deployment-service/configs/cloud-providers.yaml` line 332-333 already has
      `defi-validation: "unified-trading-defi-validation-${AWS_ACCOUNT_ID}"` (verified 2026-05-26 slot-7).
- [ ] [OPERATOR] P2. **Per-service `buildspec.aws.yaml` parity test** — run CodeBuild parity test for all services that
      have `buildspec.aws.yaml`. BLOCKED-OPERATOR: requires AWS IAM perms for CodeBuild + ECR in account `427895769566`.
      Ping operator for creds.
- [x] ✅ [AGENT] P2. **Reconciler scripts `--cloud` flag** — audit + reconciler scripts in
      `instruments-service/scripts/`, `mtds/scripts/`, `features-service/scripts/` must accept `--cloud aws|gcp` and
      route to S3 vs GCS appropriately. All 3 repos done: MTDS@04dea99b (already had it), IS@d6b8f42e (coverage boosted
      to 77.03% first, then `reconcile_phantom_manifest_rows_all.py` `--cloud` committed), features-service@e47ca213
      (`features_sports_reconcile_available_at.py` UTL storage client + resolve_bucket_name + --cloud flag). QG green
      all 3. - [x] ✅ [AGENT] P2-sub. **Fix IS coverage to ≥77%** — boosted from 74.47% to 77.03% via 39 new tests
      (understat ×19, sports_fixtures_daily_repoll ×11, urdi_reference_provider ×9) — IS@d6b8f42e.
- [ ] [OPERATOR] P2. **Operator sign-off on dual-cloud parity** — after parity tests pass: operator signs off in
      handover doc confirming GCS + S3 are byte-equivalent for DeFi asset_group.
- [ ] [AGENT] P3. **Repeat Phase 2-7 for sports/predictions/tradfi/cefi** — extend AWS migration to remaining
      asset_groups using the same playbook as DeFi. Post-cutover scope.
- [ ] [AGENT] P3. **CI/CD cutover to AWS-only** — once workspace fully bilateral, cut CI/CD to build + push to AWS ECR;
      decommission GCP Cloud Build triggers. Post-cutover scope.
- [ ] [AGENT] P3. **GCP bucket decommission** — after AWS parity confirmed + TTL expired, decommission GCP buckets per
      data-retention policy. Post-cutover scope.

## Codex SSOTs

> **[DONE 2026-05-22]** Group D audit: all referenced docs verified to exist and reflect shipped state.

| Doc                                                                     | Owns                                                                                                                                                                                                                                                                                  |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `codex/05-infrastructure/vm-tarball-deployment.md`                      | VM tarball deployment; `lifecycle_class` requirements (EPHEMERAL_BATCH / EPHEMERAL_EXPERIMENT / SCHEDULED_RECURRING / LONG_LIVED_LIVE); Pattern A vs B startup; T+10min post-launch verification; singleton-lock pattern                                                              |
| `codex/05-infrastructure/manifest-consolidator-ssot.md`                 | Manifest consolidator runtime — GCP: 20 Phase A Cloud Run jobs (10 env-tiered + 10 legacy flat) + 14 Phase D Group B pending `tofu apply`; AWS: 10 Phase C Batch Fargate EventBridge Rules + 16 Phase D pending; DuckDB merge engine (shipped 2026-05-26). GCE VM DELETED 2026-05-20. |
| `codex/05-infrastructure/gcs-object-operations.md`                      | GCS object ops canonical pattern (`unified_trading_library.cloud_interface.gcs_copy_object`; 250× faster than gsutil)                                                                                                                                                                 |
| `codex/05-infrastructure/launcher-script-ssot.md`                       | VM launcher conventions; prefix→bucket registry; `VM_PREFIX_TO_BUCKET` + `VmPrefixSpec` shape                                                                                                                                                                                         |
| `codex/02-data/availability-manifest-and-data-status.md`                | Manifest schema v8 + 4-state `capture_status` + per-asset-group bucket layout                                                                                                                                                                                                         |
| `plans/archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md` | Bucket naming SSOT (`resolve_bucket_name()` only; never inline `gs://` f-strings; QG STEP 5.69) — ARCHIVED 2026-05-23                                                                                                                                                                 |

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.md`](../active/master_to_live_defi_2026_05_23.md).
- Write-gate cluster:
  [`writegate_honest_coverage_endtoend_2026_05_06.md`](../active/writegate_honest_coverage_endtoend_2026_05_06.md).
- Asset_group vocabulary:
  [`venue_axis_asset_group_vocabulary_2026_04_25.md`](../archive/venue_axis_asset_group_vocabulary_2026_04_25.plan.md).
- Per-asset-group umbrellas: `cefi_master`, `defi_master`, `tradfi_master`, `sports_master`, `predictions_master`.
- Manifest SSOT codex: `codex/02-data/availability-manifest-and-data-status.md`.

## Referenced sub-plans (active, added 2026-05-14)

Active sub-plans owned by or closely coordinated with this epic:

| Plan                                                                                                                                             | Role                                                                                                                                                                                     | Status                 |
| ------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| [`active/per_agent_worktrees_2026_05_10`](../active/per_agent_worktrees_2026_05_10.md)                                                           | Per-agent worktree setup + tab isolation — 3-tier parallel-agent infrastructure for workspace                                                                                            | Active                 |
| [`active/ruff_workspace_cleanup_2026_05_12`](../active/ruff_workspace_cleanup_2026_05_12.md)                                                     | Ruff workspace cleanup — lint sweep + unsafe-fixes across workspace repos with foreign-file safety protocol                                                                              | Active                 |
| [`active/features_service_qg_cleanup_2026_05_11`](../active/features_service_qg_cleanup_2026_05_11.md)                                           | Features service QG cleanup — quality-gate repair for features-\* service family                                                                                                         | Active                 |
| [`active/compute_optimization_mock_data_2026_05_13`](../active/compute_optimization_mock_data_2026_05_13.md)                                     | Compute optimization + mock data — backtest compute sizing + mock-data pipeline benchmarking                                                                                             | Active                 |
| [`active/context_fill_optimization_2026_05_14`](../active/context_fill_optimization_2026_05_14.md)                                               | Context fill optimization — agent context efficiency + prompt-fill compression for long-running slots                                                                                    | Active                 |
| [`active/gate_3_phantom_audit_runbook_2026_05_13`](../active/gate_3_phantom_audit_runbook_2026_05_13.md)                                         | Gate 3 phantom-audit execution runbook — one-shot phantom reconciliation pre-2026-05-15 freeze gate                                                                                      | Active                 |
| [`archive/2026_05/agent_orchestrator_cloud_run_deployment_2026_05_19`](../archive/2026_05/agent_orchestrator_cloud_run_deployment_2026_05_19.md) | agent-orchestrator: laptop nginx → Cloud Run + Firebase Hosting + Squarespace DNS + strict-auth + CI. P0–P4 + P6 done; P5 + Firebase first-deploy DEFERRED-HUMAN-GATE.                   | ✅ ARCHIVED 2026-05-21 |
| [`active/agent_orchestrator_workers_on_vms_2026_05_19`](../active/agent_orchestrator_workers_on_vms_2026_05_19.md)                               | agent-orchestrator: asymmetric worker topology (Ikenna VM-primary + laptop-backup; Harsh PC-primary + VM-backup; both → GCS state sync). Successor to Cloud Run plan; gates parent's P5. | Active                 |
| [`active/agent_orchestrator_slack_notifications_2026_05_19`](../active/agent_orchestrator_slack_notifications_2026_05_19.md)                     | agent-orchestrator: Slack push notifications for slot_blocked / slot_stale / slot_failed via incoming webhook (#agent-orchestrator-alerts). All 6 secrets in Secret Manager. Successor.  | Active                 |

## Folded plans (archived 2026-05-07)

- `shard_granularity_ssot_propagation_2026_05_06.md` — full per-service propagation spec; P0 todos lifted above.
- `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md` — paired executor handover (per-service verify / fix /
  lift / build checklist); referenced for execution detail.
- `data_status_multi_axis_shard_propagation_2026_05_06.md` — multi-axis breakdowns + filter params + v7 manifest; P1+
  todos lifted above.
- `deployment_service_build_infrastructure_repair_2026_04_22.md` — Cloud Build + UTL base-image rebuild.
- `venue_axis_asset_group_vocabulary_2026_04_25.md` — 2 absorbed SSOT-cleanup items (`venue_start_dates` deletion
  - dashboard SSOT verify) lifted above; `poolGetSnapshots` historical-TVL item folded into `defi_master`; Waves
    A/B/C/D/E vocabulary migration shipped per CLAUDE.md "Asset-group vocabulary" section.
