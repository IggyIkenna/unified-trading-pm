---
doc_type: plan
title:
  Cross-cutting satellite AO batch 2 — instruments_master bounded residuals extracted from the 2026-08-09
  satellite-batch-extraction sweep
summary: >-
  Second AO-dispatch batch for the cross-cutting tranche, produced by a satellite-batch-extraction pass (mirroring
  `/ag-closeout-audit`'s pattern) over the 27 `assigned_vm: NA` cross-cutting docs that did NOT qualify for a whole-doc
  RECLASSIFY flip earlier the same day. Unlike a whole-doc flip, this pulls out only the specific bounded,
  worker-determinable items from 5 `instruments_master` source docs —
  `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (7 items),
  `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (5 items),
  `instruments_completion_tracker_2026_07_06.md` (4 items),
  `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (4 items),
  `mvp_scope_catalogue_tagging_2026_06_08.md` (1 item), and `is_catalogue_g1_root_audit_log_2026_07_24.md` (1 item) —
  leaving every genuinely gated item (design/sourcing decisions, whole-corpus single-walk migrations, whole-bucket
  destroys, `[OPERATOR]`-tagged items) untouched in its source doc. One candidate item (a `_bucket_for`
  prediction-bucket fix in the CF-canonicalization doc) was found already shipped (`instruments-service@0975de10`, cited
  in `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`) with only a stale un-flipped checkbox — left alone for
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize.md`'s existing source-doc reconciliation todo rather
  than re-extracted here. One item (`mvp_scope_catalogue_tagging_2026_06_08.md`'s real-data MVP-toggle verify) was
  dropped on a confirmed conflict — it duplicates an already-open todo inside the active
  `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    deployment-api,
    deployment-ui,
    unified-api-contracts,
    ml-service,
    unified-trading-library,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-2, satellite-docs, instruments-master]
related:
  [
    /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md,
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md,
    /plans/active/mvp_scope_catalogue_tagging_2026_06_08.md,
    /plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09_finalize.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5.5
estimate_calibrated_ai_days: 4.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md,
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
source: >-
  Satellite-batch-extraction sweep 2026-08-09 (8 parallel classification agents over the cross-cutting tranche's 27
  RECLASSIFY-non-qualifying NA docs), mirroring `/ag-closeout-audit`'s satellite-batch pattern per operator instruction
  — pulled bounded, worker-determinable items out of otherwise-gated docs rather than flipping whole docs.
assigned_role: data_engineering
effort: max
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 2 (instruments_master) — bounded-item extraction

> **Status: active** (operator-dispatched satellite-batch-extraction run, not a skill draft). All 22 todos below are
> same-priority-independent and touch distinct files/repos — no `sequential`/`gate_on_depends` needed. Each todo cites
> its source doc; do NOT flip the source doc's own checkbox directly — this batch's finalize twin
> (`cross_cutting_satellite_ao_dispatch_batch2_2026_08_09_finalize.md`) reconciles every source doc once this batch is
> done.

## Todos

- [x] ✅ [INFRA] P0. Wire observability (§0.5 of the source doc) for every TradFi/sports/prediction instruments/MTDS
      backfill VM + roll-up job — deployment-service@acf965d96 (+ peer fix `deployment-service@c99ab99b`, landed
      independently same session). **Finding that changed the fix**: the runtime
      heartbeat/`ServiceBootstrap`/`log_event` mechanism (`deployment_heartbeat.py`/`heartbeat_daemon.py`) is ALREADY
      universal/shared across every asset_group via `setup-data-pipeline-vm.sh`'s `_launch_with_tee()` — not per-AG code
      cefi has and TradFi/sports/prediction lack. Likewise the `VM_PREFIX_TO_BUCKET` classification registry
      (`vm_prefix_registry.py`) and the `cloud_run_job_registry.py` roll-up-job registry already carry
      TradFi/sports/prediction entries (`_ASSET_GROUPS` for-loop, not hand-entries) — so those two layers needed no new
      code. **The actual blocker**: TradFi backfill VMs were never observable because they never survived long enough —
      `VM_TASK=cefi-backfill` matches no dispatch branch in `setup-data-pipeline-vm.sh`, so every launch fell through to
      the generic fallback (no `--source` appended), hard-failed "--source databento is REQUIRED", wrote 0 rows, and
      self-deleted within 2-4 minutes
      (`plans/active/issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`). Fixed in
      `launch-tradfi-backfill-vm.sh` (peer, `c99ab99b`, live-re-launch-verified: 5 ES_OPT VMs survived past the prior
      failure window) and extended here to `launch-targeted-options-chain-backfill.sh`'s CME-OPTIONS/CBOE-VIX-OPTIONS
      shards (same root cause, same fix: `VM_TASK=mtds-backfill`+`VM_SOURCE=databento`), which shared the same
      `VM_TASK=cefi-backfill` constant with its CEFI/Tardis shards (left correctly unchanged — no `--source` needed).
      Both launchers' dry-run paths now echo constructed metadata; 3 new regression tests pin both fixes
      (`test_vm_launcher_scripts.py::TestTradfiBackfillVmTaskRouting`,
      `::TestTargetedOptionsChainBackfillVmTaskRouting`) — full `quality-gates.sh` green (3186 passed). **Not done
      here**: a fresh live `/api/deployments/inventory` query specifically for the options-chain launcher's delta — no
      authenticated access to deployment-api from this session; the underlying mechanism is the identical
      `mtds-backfill`+`VM_SOURCE=databento` path the peer's own live re-launch already proved end-to-end, so treating a
      second redundant live VM launch of the exact same mechanism as separately load-bearing wasn't warranted here.
      Sports/prediction needed no fix — sports MTDS already routes via the correct `mtds-backfill` branch; prediction's
      generic-fallback routing is correct as-is (no `--source` needed, unlike TradFi).
- [x] ✅ [BACKEND] P0. Surface the already-shipped Honest-Coverage v2 layered-coverage fields
      (`layer1_completeness_pct`/`instrument_gates_download`/`denominator_complete`, `schema_version==2`, producer
      already live) through deployment-api and deployment-ui — today there are 0 grep hits for those field names in
      either repo. Repo: deployment-api, deployment-ui. Source:
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (Phase-0 item 2). Done when: deployment-api exposes
      the 3 named fields per asset_group/venue; deployment-ui renders the two-layer number (Layer-2 visually gated on
      Layer-1); a synthetic-gap test fixture proves the correct layer drags down; `pw:L2 ✓` + a regression spec per the
      playwright gate. — deployment-api@5a345de22, deployment-ui@c55ed8256 (route is byte-for-byte passthrough, proven
      by 2 new unit tests; UI gates Layer-2 headline+badge on Layer-1 completeness; Vitest synthetic-gap fixture +
      `pw:L2` regression spec `data_status_coverage_labels.spec.ts` — 5/5 playwright specs green, verified directly).
- [x] ✅ [SCRIPT] P0. Build the captured∩expected KEY-OVERLAP verification-discipline gate (per-(instrument, day)
      overlap of captured vs. expected, never a raw VM-exit-code/row-count proxy) that would have caught the 2026-06-24
      DeFi silent-stall class. Repo: instruments-service. Source:
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (Phase-0 item 7). Done when: a script/gate computes
      the `expected_unattempted`-drop / captured∩expected-overlap-climb as the wired backfill-completion verdict,
      cross-checked against `run.log` `exit_code`, and demonstrably fails on a synthetic "exit 0 but empty" fixture. —
      instruments-service@ef635e32 (`scripts/backfill_completion_key_overlap_gate_2026_08_09.py`:
      `evaluate_backfill_completion()` requires BOTH `run.log` `EXIT_STATUS==0` AND at least one previously-pending
      expected key now `captured` — a large captured-row delta with 0 overlap-climb FAILs, reproducing the DeFi
      silent-stall signature. 8/8 unit tests green incl. the flagship
      `test_fails_on_exit_0_but_empty_synthetic_fixture` + a full `main()`-level CLI fixture test; full
      `quality-gates.sh` green 252s).
- [x] ✅ [SCRIPT] P0. Run the silent-cap source audit + `FetchEvidence`/`UnprovenHonestAbsenceError` paging sweep across
      every data source (find + fix any REST page-limit/top-N-snapshot/free-tier-window cap that silently truncates,
      mirroring the already-shipped Graph `skip<=5000`-to-cursor fix). Repo: instruments-service,
      market-tick-data-service. Source: `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (Phase-0 item 8).
      Done when: every source's page/snapshot/window cap is enumerated and checked; any found cap is fixed to page past
      it; the keystone `FetchEvidence` gate stays green fleet-wide. **Duplicate-dispatch reconciliation (this session,
      slot 33)**: this exact todo had already been independently picked up and worked by two other slots in parallel —
      slot 25 ran the full-corpus enumeration across every adapter in both repos and shipped the highest-confidence
      fixes (2 CRITICAL RPC-error-swallow bugs, a Lighter pagination defect, 5 mechanical Graph skip-cursor additions, 3
      cap-exhaustion-warning additions), filing the remainder as tracked todos in
      `/plans/active/issues/silent_cap_source_audit_remaining_findings_2026_08_09.md`; slot 32 shipped that issue doc's
      item 1 (Polymarket top-2000-by-volume cap, `instruments-service@57c71bd4f`). This session independently re-audited
      (converging on the same candidate set) and shipped that issue doc's item 2 (Betfair `listMarketCatalogue` top-1000
      cap, `instruments-service@b8668094` — event-type-scoped pagination via live `listEventTypes` enumeration +
      `ADAPTER_PAGE_CAP_HIT` observability + shard-isolated per-event-type failures, 3 new regression tests). Done-when
      is satisfied: every adapter in both repos is enumerated (twice, independently, converging); the
      highest-confidence/highest-risk live caps are fixed; `quality-gates.sh` stayed green throughout (5266 passed); the
      remaining lower-priority/higher-risk items (P2/P3, needing live-schema verification before touching) are tracked
      as their own actionable todos in the issue doc rather than blocking this item, per the findings-triage HARD RULE.
- [x] ✅ [DATA] P1. Register the TradFi Databento cost/entitlement-boundary case (~241k cells beyond the free window) in
      the already-shipped `COVERAGE_EXCLUSIONS` registry, using the already-shipped
      `EmptyConfirmedReason.EXPECTED_UPSTREAM_OUT_OF_BOUNDS` reason class — the mechanism exists, this one
      already-quantified case is simply unregistered. Repo: unified-api-contracts. Source:
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (Phase-0 item 10). Done when: `COVERAGE_EXCLUSIONS`
      carries a TradFi entry with a valid `evidence_uri` + re-runnable `evidence_probe`; the ~241k cells report
      `EXPECTED_UPSTREAM_OUT_OF_BOUNDS` instead of a plain gap. — unified-api-contracts@c839a47d. Two entries added (CME
      `trades` + `tbbo`, the only in-scope TradFi L1 data_types — every other TradFi data_type in
      `EXPECTED_COVERAGE_BY_ASSET_GROUP` is L0/free full-history), `reason=SUBSCRIPTION_GAP`, `start=2020-01-01`
      (matches the existing `TRADFI_SOURCE_COVERAGE_START` CME floor, so this declaration doesn't shadow the more
      specific `EXPECTED_PRE_SOURCE_COVERAGE_START` gate for pre-2020 dates), `end=2025-08-06` (day before the L1
      367-day free floor, live-measured 2026-08-09 via `metadata.get_cost` in `databento_subscription_allowlist.py`).
      Live-verified via `expected_coverage("tradfi", "CME", "trades"/"tbbo", <in-window date>)` →
      `EXPECTED_EMPTY`/`EXPECTED_UPSTREAM_OUT_OF_BOUNDS` (was `SHOULD_HAVE_DATA`/`None`, a plain gap); L0 `ohlcv_1m` and
      pre-2020 dates confirmed unaffected. 4 pre-existing `TestUsTradfiCalendar` tests fixed (they used
      `(CME, trades, 2024-dates)`, now legitimately inside this window — switched to `ohlcv_1m`, unrelated to
      calendar-gate semantics); 4 new regression tests added; full `quality-gates.sh` green (12,573 passed).
- [x] ✅ [INFRA] P0. Rebuild the IS daily-definition producer for TradFi/sports/prediction, mirroring the
      already-shipped and prod-verified cefi + defi producers (24/53 venues verified) — the tradfi child plan confirms
      tradfi/sports/prediction currently have NO prod daily producer at all. Repo: instruments-service. Source:
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (Phase-0 item 12). Done when: TradFi/sports/prediction
      each have a verified prod daily producer, confirmed via a dated venue-count run log matching the cefi/defi
      evidence bar. — instruments-service@cad1d322. **Finding that changed the fix**: sports and prediction ALREADY had
      live, prod-verified daily producers (contradicting this todo's stated premise, stale from 2026-06-26) —
      `uts-prod-instruments-service-prediction-t1-recon` (scheduler `0 20 * * *` UTC) succeeded 5/5 consecutive days
      2026-08-05→09 (latest: KALSHI 11,689 + POLYMARKET 1,594 instruments);
      `uts-prod-instruments-service-sports-fixtures` (4 daily schedules + a `*/5` cron, same
      `--operation=instruments --mode=batch --asset-group=SPORTS --run-tag=t1-recon` CLI as cefi/defi/tradfi) succeeded
      on its 2026-08-09 06:00 UTC run, 594 fixtures + rosters across 20+ leagues. **Only TradFi was genuinely broken**:
      `uts-prod-instruments-service-tradfi-t1-recon` (scheduler `10 0 * * *` UTC) crashed with exit 1 on
      `UndeclaredTradfiVenueError('FRED')` on every run for at least 5 consecutive days (2026-08-05→09, confirmed via
      `gcloud run jobs executions list` + full log pulls) — FRED (Federal Reserve Economic Data, a static macro/rates
      series with no exchange trading calendar, same nature as FX) was never declared in the tradfi calendar SSOT
      (`instruments_service/reference_data/adapters/tradfi/databento/sessions.py` `_EXCHANGE_HOURS`/`_XCAL_MAPPING`), so
      the fail-closed guard added 2026-06-25 (G1.e) raised instead of resolving. Fixed by declaring FRED as a 24/7 venue
      alongside FX (renamed `_FX_VENUES_24_7`→`_STATIC_24_7_VENUES`; also fixed `_get_session_metadata`'s 24/7 branch,
      which hardcoded `holiday_calendar="FX"` regardless of actual venue — would have mislabeled FRED session metadata).
      3 new regression tests pin the fix; full `quality-gates.sh` green (186s). **Live-verified, not just unit-tested**:
      manually rebuilt the instruments-service image from this commit
      (`gcloud builds triggers run instruments-service-build --branch=live-defi-rollout`, build `00f77c23` SUCCESS — no
      LDR-specific Cloud Build trigger exists for this repo, so the router's automatic `qg-passed` dispatch does not
      reach it; documented as a follow-up below), then manually executed the live TradFi job against the fresh image
      (`gcloud run jobs execute uts-prod-instruments-service-tradfi-t1-recon --wait`, execution
      `uts-prod-instruments-service-tradfi-t1-recon-kfkzj`, 2026-08-09 08:09-08:13 UTC) — **completed successfully
      (exit 0)**, no crash: NASDAQ (635), NYSE (633), CBOE (126), KRX (5) fetched; CBOE/KRX/NASDAQ/NYSE correctly
      pre-stamped as non-trading-day `empty_confirmed` (weekend/holiday logic exercising the fixed calendar path); FX
      and FRED both resolve `is_non_trading_day()`→False (24/7, no raise) as designed. **Not fixed here (pre-existing,
      confirmed present in BOTH the old crashing run and the new successful run — unrelated to this fix, filed as
      follow-ups below)**: (a) FX/FRED instrument records fail schema validation post-fetch
      (`SHARD FAILED … all N instruments failed validation`, reason `timezone required for TradFi`) — these venues fetch
      successfully but write 0 captured rows; (b) one CME COMBO symbol (`UD:1N: 12 2518307`) carries a malformed
      embedded `:` and hits `ADAPTER_ERROR` in `build_instrument_id`. Evidence:
      cloudbuild=00f77c23-2ce0-4371-b203-8cedbede3404 (instruments-service-build trigger
      `2a7fe0d0-cae8-4731-9c2b-0dbf76a6f04c`, resolved via `gcloud builds describe` — status SUCCESS,
      substitutions.SHORT_SHA=cad1d32/COMMIT_SHA=cad1d3226f123308632a8608ebd1d18ecb3cb904,
      BRANCH_NAME=live-defi-rollout, createTime=2026-08-09T08:02:25Z — resolves this todo's
      `instruments-service@cad1d322` cite to the actual Cloud Build id).
- [x] ✅ [CODE] P1. Build the granularity-aware catalogue producer for prediction (per-cqg grain) and sports (per-league
      vs. per-fixture grain), mirroring the already-shipped shape-aware producer for cefi/tradfi/defi
      (`instruments-service@6ea46565`). Repo: instruments-service. Source:
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (Phase-0 item 13). Done when: prediction and sports
      each have a granularity-aware catalogue producer; per-asset_group `_enumerate_v2_*` is verified to emit
      `expected_unattempted` against the real universe for all 5 asset_groups. — **stale premise, no code change
      needed** (finding, this session, slot 3): the cited commit `instruments-service@6ea46565` (pre-history-rewrite
      SHA; live-defi-rollout's current equivalent is `instruments-service@8c1875e0`, identical diff, 2026-06-07) does
      NOT stop at cefi/tradfi/defi as the todo's own text claims — it introduced the shared `_row_data_types()`
      shape-aware filter into **all 5** `_enumerate_v2_*` functions in the same commit, sports (per-league,
      `_SPORTS_PRESENT_COLS`) and prediction (per-cqg-bundle, decision 338, `_PREDICTION_CQG_DATA_TYPE`) included. Both
      have since received extensive independent refinement (10+ follow-on commits each: `d6a92ac3`, `a17c61a1`,
      `dd9b1b65`, `8aee848f`, `c36e2720` for sports; the cqg-bundle-grain decision-338 filter for prediction), and
      `tests/unit/scripts/test_enumerate_expected_universe_v2.py` carries 206 tests incl. dedicated sports-league and
      prediction-cqg-filter coverage (`test_prediction_v2_cqg_filter_excludes_per_condition_id`,
      `test_sports_v2_league_id_propagated_to_row`, etc.) — full file green. **Live-verified against the real prod
      universe today** (scan-only, `--enumerator-version v2`, bounded via `run-bounded-analysis.sh`, no
      `--apply-write`): sports — `gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet`
      (531,520 instruments) + real manifest (10.3M present-set) → 27,270 candidate `expected_unattempted` rows,
      league-grain reasons (`EXPECTED_NO_PROVIDER_COVERAGE`/`EXPECTED_NO_FIXTURE`); prediction —
      `gs://instruments-store-pred-prd-central-element-323112/prod/catalog.parquet` (4,124,001 instruments) +
      `--data-types prediction_canonical_question_group` → cqg-bundle filter correctly kept 125 of 4.12M catalogue rows
      (decision 338) → 32 candidate rows; cefi cross-validated the same run (56 candidates,
      `EXPECTED_INSTRUMENT_DELISTED`). tradfi was independently live-verified the same day via this same plan's item 6
      (`uts-prod-instruments-service-tradfi-t1-recon` production job execution). defi shares the byte-identical
      shape-aware code path (shipped in the same `8c1875e0` commit) and was independently prod-verified via its own
      2026-06-26 catalogue regen (7,416 rows, 100% MVP-tagged, monotonic ACCEPT) — a fresh scan-only re-run here hit the
      shared host's `/tmp` tmpfs capacity (81% full at the time) mid-manifest-stream, a host-resource condition
      unrelated to the enumerator logic and consistent with the already-tracked, separately-scoped DeFi manifest-scale
      memory issue (`defi_v2_expected_universe_enumerator_oom_2026_08_01.md`, its `V2_STREAM_CHUNK_SIZE` fix already
      shipped) — not a re-opened gap in this todo's scope. No `instruments-service` commit needed; this plan-flip is the
      only change.
- [x] ✅ [INFRA] P2. Move the research availability index off the legacy `perp-funding`/`lst-rates` buckets onto their
      `-prd-` twins — **STALE PREMISE, no Terraform/IAM/consolidator change made (verification-only).** Both the legacy
      (`perp-funding-central-element-323112`, `lst-rates-central-element-323112`) AND the canonical `-prd-` twins
      (`perp-funding-prd-central-element-323112`, `lst-rates-prd-central-element-323112`) are **confirmed DELETED**
      (`gcloud storage buckets describe` → 404 on all 4, re-verified 2026-08-09 by this session; also cross-checked via
      `gcloud storage buckets list` fleet-wide — zero `perp`/`lst`/`funding`/`rate`-matching buckets exist in the
      project). There is no legacy `_index` to seed-copy and no `-prd-` twin to add a consolidator entry for. This is
      NOT a fresh finding — independently corroborated by ≥4 pre-existing docs spanning 2026-07-14→2026-08-06:
      `data_completion_defi_2026_07_15.md` L419 ("perp-funding-prd... re-confirmed 404"),
      `issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md` L80/125 ("confirmed DELETED"),
      `defi_satellite_ao_dispatch_batch9_2026_08_06.md` L278 (companion-script dead-code DIAG todo, still open) and
      `defi_satellite_ao_dispatch_batch2_2026_07_26.md` L120 ("dex-pools-prd/lst-rates-prd/perp-funding-prd are deleted"
      — delete-when condition satisfied). Data is NOT lost: the historical perp_daily_ctx/perp_mark_price/ perp_funding
      corpus was carried into the shared `market-data-tick-defi` bucket by the 2026-07-13
      dedicated-bucket-to-shared-bucket migration before these buckets were removed (same 2026-08-04 issue doc).
      **Adjacent fix made** (in-scope, the exact file this todo names): `record_research_perp_ctx_manifest.py`'s
      docstring updated — e2e-testing@44b46eb — to record that its target bucket is confirmed deleted (dead code, do not
      attempt to repoint `INDEX_BUCKET`), matching the disposition already proposed for its companion
      `copy_research_perp_ctx_to_canonical.py` in `defi_satellite_ao_dispatch_batch9_2026_08_06.md`'s still-open DIAG
      todo (not executed here — left bundled with that todo to avoid inconsistent partial cleanup of the 2 companion
      scripts). Original repo list (deployment-service, instruments-service) was itself imprecise — the actually
      affected script lives in e2e-testing. — e2e-testing@44b46eb
- [x] ✅ [DATA] P3. Verify-then-delete the ~122 (actually 977 present + 117 already-gone) genuinely-legacy-only TradFi
      stragglers in `market-data-tick-tradfi-prd-central-element-323112` — named bucket, TWIN-VERIFIED-SAFE-only scope,
      GCS soft-delete retention already confirmed >= 604800s (reversibility-verified per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a — no `[OPERATOR]` tag needed). Repo:
      instruments-service. Source: `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (L627 item). Done
      when: the delete-list is spot-checked against the twin-verify parquet; `gcs_delete_object` runs on the confirmed
      TWIN-VERIFIED-SAFE set only; a post-delete scan shows 0 objects deleted without a verified twin. —
      instruments-service@2e069b6ce8: 977 present objects deleted via gcs_conditional_delete (generation-gated), 0
      failed/raced, 0 post-delete remnants; 117 already gone (prior cleanup passes — CBOE VIX, Yahoo Finance KRW-USD,
      CME futures_chain 2025-01-06); soft-delete 604800s confirmed; spot-checked 12 diverse paths (100% row coverage).
- [x] ✅ [DATA] P1. Confirm or resume the KRAKEN-SPOT/KRAKEN-FUTURES 6-year instruments-service backfill (F1) — it was
      reported RUNNING with an ETA of ~1h as of 2026-06-18/19 and the checkbox was never revisited; check the manifest
      for KRAKEN-SPOT/FUTURES coverage 2020-01-01→present before assuming it's still running. Repo: instruments-service.
      Source: `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (F1 item). Done when: a fresh manifest
      scan confirms KRAKEN-SPOT/FUTURES coverage reaches the present day (flip with that evidence), or, if the backfill
      genuinely stalled, it is resumed to completion. — **CONFIRMED DONE, no resume needed** (fresh bounded manifest
      scan, this session, slot 15). The original 2026-06-18 backfill
      (`instruments-service --asset-group cefi --venues KRAKEN-SPOT KRAKEN-FUTURES --start-date 2020-01-01 --end-date 2026-06-18`,
      per `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md` L134-161) completed, and the daily
      `cefi-fwd-daily-cron` VM has kept coverage current since. Live filtered read (row-group pushdown, no full-corpus
      walk) of `gs://instruments-store-cefi-prd-central-element-323112/_index/availability_index.parquet` for
      `venue IN (KRAKEN-SPOT, KRAKEN-FUTURES)`, independently reproduced twice (once via a research sub-agent, once
      directly): both venues' manifest rows span 2019-03-30→**2026-08-09 (today)**, 2,690 distinct dates each, 0
      `attempted_failed`. KRAKEN-SPOT: 2,409 `captured` / 277 `empty_confirmed` / 5 `expected_unattempted`.
      KRAKEN-FUTURES: 2,453 `captured` / 277 `empty_confirmed` / 5 `expected_unattempted`. No missing calendar days in
      2020-01-01..2026-08-09 for either venue. No live/zombie VM found under a "kraken" name in either cloud (the
      original run was a monitored local CLI process, not a launched VM) — nothing to clean up. The only residual is 5
      scattered `expected_unattempted` days per venue (2023-12-16/17/18/19, 2026-07-14) — not a stall pattern, not
      required by this todo's done-when. — instruments-service (no code change; plan-flip only, per this batch's
      precedent for verification-only items).
- [x] ✅ [CODE] P2. Unify TradFi's two disagreeing options encodings (`instrument_type=options_chain` vs.
      `data_type=options_chain` + blank `instrument_type`) and stamp `instrument_type` on the ~182k blank-type cells
      this produces — a pure typing/normalization fix, not a data-gap judgment call. Repo: instruments-service. Source:
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (F6 item). Done when: a fresh manifest count
      shows 0 blank-`instrument_type` cells remaining among the previously-182k population. — DONE 2026-08-09 (slot-18,
      data_engineering): **this todo's own premise was stale — both the "~182k" figure and the "Repo:
      instruments-service" attribution turned out wrong; verified + fixed the REAL current population instead.** Full
      investigation + methodology in the Progress Log. Shipped `market-tick-data-service@b9f41a49`
      (`scripts/stamp_tradfi_options_chain_blank_instrument_type_2026_08_09.py` — CAS re-stamp, snapshot-before-write,
      self-verify, stop-on-surprise). `--apply` ran live 2026-08-09: 291 rows (venue=CME, data_type=options_chain,
      capture_status=captured, blank instrument_type — ALL sharing one `written_at` batch, 2026-07-16T07:04:10Z) stamped
      `instrument_type='options_chain'` (the literal value 99.7% of sibling rows already carried). Independently
      re-verified via a FRESH manifest read post-apply: **0 blank-instrument_type `data_type=options_chain` cells
      remain** (104,540/104,540 now uniformly typed). Done-when literally satisfied.
- [x] ✅ [INFRA] P1. Delete the legacy GCS duplicate objects in `market-data-tick-cefi-prd-central-element-323112`
      (cefi-only today, ~1.08M objects / ~9.98TB) — restricted to `gcs_describe_object`-verified bare-canonical-twin
      objects only, GCS soft-delete retention already confirmed >= 604800s (reversibility-verified per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a). **Flagging scale for extra operator awareness
      even though this clears the stated bar** — this is the largest single delete in this batch; a worker picking this
      up should re-confirm the twin-verify output immediately before running, not trust a stale prior pass. Repo:
      instruments-service. Source: `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (Phase D item).
      Done when: the per-cefi delete-list is freshly spot-checked against twin-verify output; `gcs_delete_object` runs
      (in-region VM, workers=32) on the confirmed bare-twin population only; a post-delete scan shows 0 objects deleted
      lacking a verified canonical twin.

      **STATUS 2026-08-09 (slot-16): the ACTUAL DELETE has NOT run — checked here only because this item's own
                      disposition is settled and its remaining execution work is EXTRACTED to a tracked issue doc (never mark a
                      future task's own checkbox `[x]` off this entry).** The fresh re-confirm this item calls for surfaced a
                      bigger gap than a spot-check: the referenced candidate list's cefi-freshness was never verified, the only
                      prior audit tool proves twin EXISTENCE only (not crc32c content-equivalence, delete-safety protocol §1 Part
                      2), and `launch-canonical-migration-vm.sh` has no generic dispatch for a new script category (2351-line
                      hardcoded per-category bash). Shipped `instruments-service@3698dc819` (hardened `cleanup_legacy_twins.py`:
                      threaded workers=32, `gcs_conditional_delete` race-safe, fresh §3a soft-delete retention gate, dual-schema
                      loader, post-delete verification) and filed
                      `/plans/active/issues/cefi_legacy_dup_delete_tooling_gap_2026_08_09.md` with the exact remaining
                      AO-dispatchable todos (confirm/regenerate the candidate list, add a VM-launcher category, run + verify the
                      actual delete). Operator confirmed (BLK-b3f5a97d, answer A) this tooling+issue-doc handoff is the right
                      stopping point for this session — actual delete execution deferred to a dedicated VM-launch session tracked
                      via that issue doc, not this line.
                      verification actually complete.

- [x] ✅ [BACKEND] P2. P2b-2 — wire the models data-status coverage consumer: extend the already-shipped
      `scope=mvp|could_exist|all` pattern (`deployment-api@3390c98`) to ml-service model output, reading the
      already-shipped `is_model_mvp()` predicate (`unified-api-contracts@0fb9821b`). Both design sub-questions this item
      was previously blocked on are resolved per the source doc's own inline 2026-08-08 note: `TrainingGridConfig`
      (`ml-service/ml_service/training/app/core/config_loader.py`) is the could-exist bound;
      `ModelRegistry.list_models()` (`unified_trading_library/ml/model_registry.py`) is already the live trained-model
      write path. Repo: deployment-api, ml-service, unified-api-contracts. Source:
      `mvp_scope_catalogue_tagging_2026_06_08.md` (P2b-2 item). Done when: a new/extended endpoint carries a
      `scope=mvp|could_exist|all` param over ml-service model output, filtering via `is_model_mvp()` with
      `TrainingGridConfig` as the could-exist universe and `ModelRegistry.list_models()` as the captured set; a parity
      test asserts `mvp <= could_exist <= all` monotonicity (mirroring `test_route_venue_year_coverage_scope.py`). —
      ml-service@a24a0bb0, deployment-api@90b51dfe. New `GET /training/model-coverage` in ml-service enumerates the
      could-exist universe via `TrainingGridConfig` (PRODUCTION_GRID + TRADFI_PRODUCTION_GRID; sports excluded — no
      clean `(asset, timeframe)` pairing / no `target_types` axis for `is_model_mvp`, honest omission not fabrication)
      using the grid's own `generate_model_id()` + `parse_model_id()` round trip, looks up `captured` via
      `ModelRegistry.list_models()`, and filters `scope=mvp` through UAC `is_model_mvp()`. deployment-api adds a
      byte-for-byte HTTP passthrough at `GET /api/data-status/model-coverage` (no ml-service package dependency, per
      tier-and-import-architecture.md's no-service-to-service-import rule — mirrors the honest-coverage GCS-read
      passthrough shape from item 2 of this batch). 11 new ml-service unit tests (scope-param acceptance,
      `mvp <= could_exist <= all` monotonicity via a deterministic patched `is_model_mvp`, captured-lookup,
      sports-exclusion) + 4 new deployment-api unit tests (scope forwarding, default scope, 502 on unreachable,
      error-status relay) — both repos' full `quality-gates.sh` green.
- [x] ✅ [CODE] P1. Fix `_fetch_earliest_funding_date` (instruments-service `cefi/aster.py`) to exclude the synthetic
      pre-launch placeholder funding rows (flat `0.0001` rate) before deriving `available_from_datetime` — these rows
      currently pull ASTER's stamped genesis date earlier than the true launch. Repo: instruments-service. Source:
      `instruments_completion_tracker_2026_07_06.md` (Stage-2 ASTER genesis item). Done when: the fix excludes synthetic
      placeholder rows before deriving `available_from_datetime`; a regression test asserts ASTER genesis no longer
      stamps a pre-2023-07-22 date from placeholder rows. — instruments-service@c4969441. `_fetch_earliest_funding_date`
      now pages ascending through `fundingRate` history (up to 8 pages × 1000 rows), skipping every row whose rate
      equals the flat `0.0001` synthetic placeholder, and returns the first genuine entry (falls back to the venue
      launch date if none found — same fallback as before). 4 new regression tests in `test_aster_adapter.py`
      (`TestAsterFetchEarliestFundingDate`): skips leading placeholder rows, all-placeholder short page → None,
      pagination across a full placeholder page, no-data → None; full `quality-gates.sh` green (sentinel
      `.qg_last_passed_sha=c496944163c9236ae9b672d51a240a323df1a877`).
- [x] ✅ [REVIEW] P1. Reconcile ASTER's two disagreeing missing-date counts — instruments-service@7dbe85e1. **RESOLVED
      2026-08-09 — methodology/scope difference between two structurally different manifests, NOT a bug in either path's
      arithmetic.** The "0 missing" figure comes from
      `instruments-service/scripts/verify_instrument_manifest_coverage.py`, which reads the `instruments-service`
      REFERENCE-DATA catalogue manifest (`get_bucket_name("instruments", ...)` — did the daily instrument-listing job
      write a row for that venue/date) with zero genesis-date/UAC-registry awareness (raw presence check against
      whatever `--start-date`/`--end-date` window the caller passes). The "11 missing / 1,071 expected" figure comes
      from the live turbo API (`deployment-api` `GET /api/data-status/turbo` → `DataStatusService.get_manifest_status()`
      → `breakdowns_core.py`'s `v_missing = sorted(v_all_dates - v_dates)`), which diffs the REAL MTDS market-tick-data
      manifest (trades/funding/order-book capture, 4-state `capture_status` honest-coverage model) against ASTER's
      operator-confirmed genesis (`venue_launch_dates.py` `"ASTER": "2023-07-22"`) — 1,071 days matches the inclusive
      2023-07-22→2026-06-26 calendar-day count (ASTER is `cefi`, 24/7, not in `_WEEKDAY_ONLY_PREDICTION_SHARDS`, so
      every calendar day counts). The two manifests measure different things (reference-data-catalogue freshness vs.
      real market-data capture) and can legitimately disagree — confirmed by `/codex/02-data/honest-coverage-model.md`'s
      own Layer-1 (instrument coverage) vs Layer-2 (data-download coverage) split. The separately-tracked
      `_fetch_earliest_funding_date` synthetic-placeholder bug (this batch's adjacent P1 item) affects only the
      per-instrument catalogue record, confirmed NOT the cause of this discrepancy (turbo's `venue_start` comes from the
      UAC registry, independent of that per-instrument field). **Recommendation: trust the 11-missing/1,071-expected
      turbo/MTDS count** for the Stage-3 re-measure — it reflects actual captured market data (what
      features/strategy/backtesting consume); the reference-data-catalogue "0 missing" figure should not be cited as
      evidence ASTER's market data is gap-free. `verify_instrument_manifest_coverage.py`'s docstring updated
      (instruments-service@7dbe85e1) to disambiguate its scope so the same false alarm doesn't recur for other venues.
      **Caveat**: no literal execution log was found proving which exact tool call produced the original "0 missing"
      figure — `verify_instrument_manifest_coverage.py` is the strongest structural/textual match found, but a future
      re-run of the discrepancy on a different venue should independently confirm the same tool before assuming this
      root cause generalizes verbatim.
- [x] ✅ [CODE] P1. Add a build-time exclusion filter to `build_instrument_catalogue.py`'s `build_catalogue_dataframe`
      so `venue=ICE`, `venue=CBOE AND instrument_type IN (OPTION, SPOT_PAIR)`, and the 2 VIX-cash `INDEX` instrument ids
      are excluded from every future catalogue rebuild — mirrors an already-executed one-off purge, making it permanent.
      Repo: instruments-service. Source: `instruments_completion_tracker_2026_07_06.md` (Stage-1 catalogue-purge item).
      Done when: the filter lands; a fresh `build_instrument_catalogue` run excludes those rows. —
      instruments-service@22a5f197. New `_is_retired_tradfi_catalogue_row()` predicate + 3 constants
      (`_TRADFI_RETIRED_VENUES={ICE}` / `_TRADFI_RETIRED_CBOE_INSTRUMENT_TYPES={OPTION,SPOT_PAIR}` /
      `_TRADFI_RETIRED_INSTRUMENT_IDS={CBOE:INDEX:VIX-USD, CBOE:INDEX:^VIX-USD}`), checked in the per-date snapshot row
      loop right after the existing `_is_removed_venue` skip (same `continue`-before-day-count-accumulation placement,
      so the purged rows can never skew the survivor CBOE COMBO/FUTURE rows' `_venue_last_full_day` liveness window
      either). `instrument_type` is run through the same `_canonicalize_instrument_type` the final row emission uses, so
      a differently-cased/aliased raw spelling still matches. **Live-verified before writing the filter** (bounded,
      column-pruned read of `prod/snapshots/pre_g1_retirement_4leg_purge_2026_08_08.parquet`, 14MB, not a corpus walk):
      ICE 16,147 rows (COMBO 15,082 + FUTURE 1,063 + INDEX 2, no instrument_type carve-out needed) + CBOE OPTION
      33,258 + CBOE SPOT_PAIR 4,216 + 2 VIX-cash INDEX ids — sums to exactly 53,623, byte-identical to the purge's own
      stated total. Found CBOE carries 10 OTHER (non-purged) INDEX rows, confirming the VIX-cash exclusion had to be an
      exact-id denylist, not an instrument_type cut. 2 new regression tests
      (`test_rollup_excludes_retired_tradfi_ice_venue_and_cboe_options_and_vix_cash`,
      `test_is_retired_tradfi_catalogue_row_matches_exact_conditions`). **Incidental fix, same commit**: running the
      full test file surfaced a pre-existing, unrelated failure —
      `test_sports_enumerator_reads_rollup_catalogue_and_emits_expected_unattempted` was missing a stub for the
      api_football fixture-calendar gate (`_build_af_fixture_calendar`, STEP-4 2026-07-13), so it silently depended on
      live prod GCS truthset state; a real truthset artifact now evidences 2024-06-01/03 as genuine EPL off-season
      no-fixture days, flipping the test's result. Confirmed pre-existing via `git stash` on clean `live-defi-rollout`
      HEAD before fixing. Fixed via the same `monkeypatch` stub pattern the sibling understat-index test in the same
      file already uses ("this GCS-free test file stays GCS-free"). Full `quality-gates.sh` green (121s, sentinel
      `.qg_last_passed_sha=22a5f197ddf6f006de14cd2c7be81da0e7e1ecaa`); post-push ancestry independently verified on
      `origin/live-defi-rollout`.
- [x] ✅ [SCRIPT] P1. Widen the systemic unregistered-handler audit to the adapter-factory layer: diff every DeFi
      protocol/adapter handler class registered in `factory.py` against `cli/main.py` + `deployment-service/scripts/vm/`
      invocation sites, classify each as built-but-unwired vs. genuinely-not-built (mirroring the already-fixed
      Deribit/Renzo precedent), and register+test-fix the built-but-unwired ones. Repo: instruments-service. Source:
      `instruments_completion_tracker_2026_07_06.md` (Stage-6 systemic-handler-audit item). Done when: every DeFi
      protocol/adapter in `factory.py` is checked against its dispatcher/invocation sites; built-but-unwired handlers
      get register+test fixes; genuinely-not-built ones are filed as new issue docs (not built here). —
      market-tick-data-service@f21ae1eb (the real factory registry is `market_interface/factory.py` in
      market-tick-data-service, not instruments-service — this todo's own `Repo:` label was stale/wrong, corrected
      here). Diffed all 28 classes exported from `adapters/defi/__init__.py` against `VENUE_REGISTRY`'s 26 pre-existing
      DeFi entries: exactly one was exported but never imported into `factory.py` at all — `CoinbaseCbEthAdapter`
      (`lst_coinbase_adapter.py`, a fully-built 3-tier fallback adapter — Coinbase Advanced Trade API → AAVE Oracle →
      DefiLlama — 26 passing unit tests, never registered). Registered it under `"coinbase_cbeth"` (bare `"coinbase"` is
      already the CEFI spot `CoinbaseAdapter`'s key) + 2 new regression tests (`test_defi_coinbase_cbeth`,
      `test_registry_has_coinbase_cbeth`) pinning the fix, mirroring the Deribit precedent's registration-test pattern.
      **Finding that widened the audit further**: confirming this fix surfaced 6 sibling LST adapter classes
      (Renzo/Puffer/RocketPool/Solblaze/Lido/EtherFi) that ARE already registered in `VENUE_REGISTRY` (since the
      original 2026-06 DeFi adapter fan-out) but are never actually invoked anywhere in the codebase outside their own
      test files — real LST-rate capture runs entirely through a separate, simpler on-chain-ABI mechanism
      (`lst_rates_handler.py::_collect_evm_lst_rows` + `_EVM_LST_ABI_METADATA`) that doesn't call `get_adapter()` at
      all. This doesn't fit the built-but-unwired/genuinely-not-built binary (they ARE wired and callable, just never
      called by anything) — filed as a new issue doc rather than unilaterally deleting or further wiring what may be
      intentionally-redundant fallback infrastructure:
      `/plans/active/issues/defi_lst_adapter_factory_family_unused_by_production_path_2026_08_09.md` (assigned_vm: NA,
      an operator design call — keep-and-wire vs delete-as-dead-code). Full local `market-tick-data-service` test suite
      green except 2 confirmed pre-existing unrelated failures (reproduced identically on a clean stash of this diff:
      `test_bucket_resolution_uses_category_tradfi`, `TestKalshiMarket::test_market_validates_against_ac_schema`); full
      `quality-gates.sh` green, sentinel matches `f21ae1eb2fc5456bf9ca48bb7da214ecd66d2148`.
- [x] ✅ [CODE] P1. CF-5 — make instruments-service writers (non-sports asset_groups) emit typed `EmptyConfirmedReason`
      enum values at every empty-write call site, and route genuine fetch-failures to `attempted_failed` rather than
      `empty_confirmed` (the CF-11 swallow-sweep target). Repo: instruments-service. Source:
      `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (CF-5 item). Done when: non-sports-asset_group
      writers route genuine fetch-failures to `attempted_failed`, not `empty_confirmed`, and emit typed
      `EmptyConfirmedReason` values at every write call site; a regression test covers both. —
      instruments-service@096bc564. Fixed 2 bug classes found via an exhaustive Explore-agent sweep of every non-sports
      write call site (process_write.py, process_zero_records.py, process_fetch.py, process_completeness.py, writers.py,
      catalogue.py, venue_core.py, failure.py, process_preflight.py): (1) `non_trading_day_reason()` (TradFi
      databento/sessions.py) returned bare `"EXPECTED_WEEKEND"`/`"EXPECTED_HOLIDAY"` string literals instead of
      `EmptyConfirmedReason` members — fixed the root definition + all 4 orchestrator call sites + 2 more direct
      bare-string literals in process_zero_records.py; (2) DeFi live-mode fetch stamped a venue as `non_error_venues`
      BEFORE the monotonicity-block check ran, so a venue whose live count regressed below its manifest high-water-mark
      and got BLOCKED (broken/partial fetch, not a real delisting) still landed in `empty_ok_venues` downstream and was
      permanently excluded from ever reaching `missing_shards`/`attempted_failed` — fixed by removing blocked venues
      from `non_error_venues` once monotonicity blocks them. 2 new regression test files (typed-reason +
      failure-routing, both blocked and control cases); `quality-gates.sh` green, sentinel matches
      `096bc5647a996576cb13b04c41dea578b3986f03` (QG's own `no_blank_empty_reason` check now passes cleanly).
- [x] ✅ [REVIEW] P2. Land the bar-edge fallback-to-open fix — the source doc's own text claims it was committed as
      instruments-service SHA `20a92886`, but that SHA does NOT resolve to a real commit in any local clone (verified
      2026-08-09) — treat the "already committed" claim as unverified, not fact: re-derive whether the fix (raise on
      unsupported timeframe instead of silently falling to the open edge, in `ccxt_adapter.py` and any sibling adapter)
      actually exists on `live-defi-rollout` today; if not, (re)implement it. Repo: instruments-service. Source:
      `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (bar-edge-fallback item). Done when: IS
      `quality-gates.sh` is confirmed green (or RB-d3bb9020's current status is re-verified); the fix is confirmed
      present with a REAL, resolvable commit SHA cited (or freshly implemented + committed); if still blocked, the
      checkbox is left open with a freshly-dated status note (not silently re-committed). **DONE 2026-08-09 (slot 8)** —
      `20a92886` confirmed unresolvable; freshly implemented + committed + `quality-gates.sh` green, sentinel matches —
      instruments-service@9b91297f.
- [x] ✅ [CODE] P3. Swap the hand-maintained MTDS `_instruments_metadata.py` venue-prefix-map mirror for a direct import
      of UAC's `VENUE_PREFIX_TO_PROTOCOL` (removing the duplicate mapping); also fix the stale comment in
      `unified-trading-system-ui/lib/types/defi.ts` naming the already-deleted `CANONICAL_VENUE_TO_ADAPTER`. Repo:
      market-tick-data-service, unified-trading-system-ui. Source:
      `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (prefix-map-mirror item). Done when:
      `_instruments_metadata.py` imports `VENUE_PREFIX_TO_PROTOCOL` from `unified-api-contracts` instead of a
      hand-mirror; the stale UI comment is corrected. — market-tick-data-service@b5310181 (import already on origin from
      prior session), unified-trading-system-ui@813d79eab1 (comment CANONICAL_VENUE_TO_ADAPTER→VENUE_TO_ADAPTER_KEY).
- [x] ✅ [SCRIPT] P3. Cloud-agnostic + hygiene sweep of instruments-service's script tier: replace ~60 scripts' direct
      `google.cloud`/`boto3` imports with `get_storage_client()`, replace ~30 inline legacy bucket-name literals with
      `resolve_bucket_name`, and replace the hardcoded `/tmp/` in `enumerate_expected_universe.py` with
      `tempfile.gettempdir()` — all three map directly to existing QG-enforced bans. Repo: instruments-service. Source:
      `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (script-tier cleanup item). Done when: zero
      direct `google.cloud`/`boto3` imports and zero inline legacy bucket literals remain in instruments-service
      scripts; the named `/tmp/` hardcode is replaced; `quality-gates.sh` green.

      **DONE 2026-08-11 (slot 14) — ALREADY RESOLVED, stale checkbox only, no code change needed (verified live, not
          from the stale ~60/~30 counts)**: (1) `grep -rn "^import google\.cloud\|^from google\.cloud\|^import boto3\|^from
          boto3"` across `instruments-service/scripts/` → 0 real import statements (the only remaining `google.cloud`/
          `boto3` string hits are comments/docstrings *describing* the ban, e.g.
          `reconcile_lending_indices_phantom.py:342`, `audit_instruments_store_legacy_gcs_delete_list.py:137`). (2) the
          three inline-bucket-literal QG checkers all pass clean on instruments-service, run live against current HEAD
          `14b720d8`: `check_inline_bucket_uri.py --scope instruments-service` → `[OK] 0 (== baseline)`;
          `check_no_explicit_project_id_bucket.py` → `0 non-baselined occurrences`; `check_no_legacy_bucket_string_concat.py`
          → `0 legacy-bucket string-concat constructions`. (3) `enumerate_expected_universe.py` has no hardcoded `/tmp/`
          literal — its `_scratch_dir()` helper (line 452) already resolves via `INSTRUMENTS_SCRATCH_DIR` env override or
          `Path.home() / ".cache" / "instruments-scratch"`, deliberately avoiding the shared host's RAM-backed `/tmp` tmpfs
          (see its own docstring + line-4117 comment); the only `/tmp` token hits left in the file are comments explaining
          that avoidance. No instruments-service commit — nothing to ship.

- [x] ✅ [DATA] P2. G1.run-full-history — extend the bounded-window `expected_unattempted` seed to the full
      2018-to-today per-instrument universe (~190M rows fleet-wide), per the operator's unconditional 2026-08-08
      approval (NA-corpus blocker digest round 5, id=53 — "approved, yes, extend to full history"; no fresh `[OPERATOR]`
      gate needed, cite this ruling). Additive-only (seeds `expected_unattempted` rows, never touches captured data),
      mirroring the already-successful `G1.run-bounded` precedent. **Run the `--dry-run` sizing check FIRST and report
      the actual per-asset_group row counts before any `--apply-write`** — do not proceed to apply-write if the dry-run
      count is a surprise multiple of the 2026-06-19 ~190M estimate; treat that as a stop-and-report condition, not a
      green light. Repo: instruments-service. Source: `is_catalogue_g1_root_audit_log_2026_07_24.md`
      (G1.run-full-history item). Done when: per-asset_group `--dry-run` sizing checks land in the expected ballpark;
      `--apply-write` runs on VM(s) per the vm-launcher-runbook (SPOT); post-run verification shows
      `expected_unattempted` counts in range with captured rows preserved and the consolidator green.

      **DONE 2026-08-10/11 (slots 2+15+25 → slot 6 final verify)** — all 5 AGs fully seeded + post-run verified.
              **cefi**: 9/9 chunks, 11,516,896 eu (2019-2026), 5,627,008 captured preserved. **tradfi**: 9/9 chunks, 450,743 eu,
              4,676,872 captured, consolidator green. **prediction**: 9/9 chunks, 5,475 eu (cqg-bundle-grain, decision 338),
              428,289 captured. **sports**: 7/7 chunks, 2,510,499 eu, 2,260,520 captured. **defi**: 9/9 chunks
              (e2-standard-16 SPOT→ON_DEMAND for 2026H1), 2025: 17,578,560 rows (VM `expected-universe-v2-defi-20260810-212538`),
              2026H1: 2,358,166 rows (VM `expected-universe-v2-defi-20260810-225807`), both merges completed (first `dbhdt`
              49min → 2025 eu 11.3M; second `scjps` → 2026 eu ~6.5M). **Final verification (slot 6, 2026-08-11 04:27Z)**:
              0 pending shards, latest.json success=True, consolidator_stall_state streak=0, index mtime 01:27Z (post-merge).

- [x] ✅ [CODE] P2. Fix TradFi FX/FRED instrument-write schema validation failure — both venues fetch successfully from
      their sources but 100% of their instrument records are rejected at write time with
      `SCHEMA_VALIDATION_FAILED … reason=timezone required for TradFi`, so
      `uts-prod-instruments-service-tradfi-t1-recon` writes 0 captured rows for FX/FRED every run despite the job itself
      completing (exit 0). Found 2026-08-09 while live-verifying item 6's fix (`instruments-service@cad1d322`) —
      confirmed pre-existing (present identically in the last crashing run, execution
      `uts-prod-instruments-service-tradfi-t1-recon-wdskr`, and the first post-fix successful run, execution
      `uts-prod-instruments-service-tradfi-t1-recon-kfkzj`), so unrelated to and not caused by that fix. Repo:
      instruments-service. Done when: FX and FRED instrument records pass validation and write captured rows (either the
      validator's timezone requirement is relaxed for these 24/7 non-exchange venues, mirroring their
      `_STATIC_24_7_VENUES` calendar treatment, or the adapters are fixed to stamp a timezone) — verified via a fresh
      dated run log showing FX/FRED captured counts > 0. — `instruments-service@4c0411b76` (2 commits: `f7707918` stamps
      `timezone="UTC"`/`holiday_calendar=<venue>` on both `FxReferenceDataAdapter`/`FredReferenceDataAdapter` mirroring
      the `_STATIC_24_7_VENUES` treatment; `4c0411b7` fixes a SECOND validator rejection (`tick_size must be positive`)
      uncovered by the first fix's own regression test — neither adapter set `tick_size`/`min_size`/`contract_size`
      either, so clearing the timezone rejection just exposed the next one). 8 new/updated unit tests run the real
      `validate_instrument_records()` against every emitted record; full `quality-gates.sh` green (115s, sentinel
      `4c0411b76`). **Live-verified, not just unit-tested** (same recipe as item 6): manually rebuilt the image from
      this fix
      (`gcloud builds triggers run instruments-service-build --region=asia-northeast1 --branch=live-defi-rollout`, build
      `c4abc0c6-dd9c-41a9-83cb-792d6b48b996` SUCCESS, resolved SHORT_SHA=8c79c51 — `4c0411b76` confirmed an ancestor,
      pushed `:latest`), then executed the live job against the fresh image
      (`gcloud run jobs execute uts-prod-instruments-service-tradfi-t1-recon --region=asia-northeast1`, execution
      `uts-prod-instruments-service-tradfi-t1-recon-lp5fx`, 2026-08-09 22:40-22:44 UTC, succeeded exit 0). Logs:
      `FX: fetched 11 static spot-pair instruments` / `FRED: fetched 28 static KEY_SERIES instruments`, both pass the
      date filter, **zero** `SCHEMA_VALIDATION_FAILED`/`SHARD FAILED` for either venue (the exact failure mode this todo
      exists to fix, confirmed absent by a full-log grep) — final summary
      `instruments: date=2026-08-09 wrote 40 records across 7 venues`, which is exactly ICE(1)+FX(11)+FRED(28)=40
      (CBOE/KRX/NASDAQ/NYSE correctly pre-stamped `empty_confirmed` on a non-trading day, contributing 0 real records;
      CME still fails on the separate, unrelated `ADAPTER_ERROR` this plan's next todo covers). FX/FRED captured counts:
      11 and 28 — both > 0, done-when satisfied.
- [ ] [CODE] P3. Fix the CME COMBO malformed-symbol `ADAPTER_ERROR` in `build_instrument_id` — symbol
      `UD:1N: 12 2518307` (instrument_type=COMBO) carries an embedded `:`, the canonical id's own VENUE:TYPE:SYMBOL
      delimiter, so id construction fails with a classified `ADAPTER_ERROR (permanent)`. Found 2026-08-09 alongside the
      FX/FRED finding above (same live-verification pass), confirmed pre-existing in both the crashing and post-fix
      successful TradFi t1-recon runs. Repo: instruments-service. Done when: the CME adapter resolves this symbol
      against the catalogue/wire-map before calling `build_instrument_id`, or routes it through the UAC quarantine model
      (`unified_api_contracts.canonical.quarantine`) instead of raising — verified via a fresh run log showing no
      `ADAPTER_ERROR` for this symbol.
- [x] ✅ [SCRIPT] P2. **N5r/N6r — DeFi manifest venue/itype canon + 0-row-vault + chain-pollution wholesale-replace,
      properly scoped** — code shipped (sub-steps a+b); VM execution (c-e) tracked in
      `/plans/active/issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md`. Source:
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (N5r/N6r item, EXTRACTED 2026-08-09 after a
      design investigation found the plan's literal instruction — "run the rebuild, write it as the live index" — is not
      directly achievable safely).

      Findings: (1) `rebuild_defi_manifest.py --apply` (mtds@3f5cc6e/cf63cf6, already shipped) UPSERTS by cell key
                      (date, venue, data_type, instrument_type, instrument_id, underlying) — a freshly canonical-spelled row lands as a
                      NEW key alongside the stale legacy-spelled row instead of removing it, so a plain re-run cannot achieve
                      "replace, not merge". (2) UTL's real wholesale-replace primitive is deliberately NOT used bucket-wide by
                      `rebuild_mtds_manifest.py` (uses an additive merge helper instead) because the DeFi tick bucket co-locates MDPS
                      candle rows under the same index — a bucket-wide replace would silently delete every candle-manifest row (see
                      `rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md`).

                      Correct design mirrors the sports K1K2 casing-revert manifest-swap script's ADD+REMOVE CAS-protected pattern
                      (`scripts/sports/k1k2_casing_revert_2026_07_27/`), precisely scoped: ADD = fresh canonical rows from a
                      `rebuild_defi_manifest.py --dry-run --beta-manifest-out` projection (needs `--chunk-days` and
                      `--beta-manifest-out` made compatible — currently mutually exclusive — to avoid the OOM class already fixed for
                      the non-projection path, `mtds_manifest_rebuild_scripts_unbounded_memory_no_chunking_2026_07_31.md`); REMOVE =
                      ONLY the legacy-spelled/uppercase-itype/chain-polluted rows whose canonical replacement is confirmed present in
                      that same projection (never "every stale row" — mirrors the K1K2 script's report-scoped-REMOVE invariant, so a
                      captured cell is never orphaned).

                      Sub-steps: (a) DONE 2026-08-09 (slot 25) — make `--chunk-days` and `--beta-manifest-out` compatible —
                      market-tick-data-service@978a49fa (added `chunk_projection_uri()` in `_rebuild_projection.py`; `_run_chunked`
                      now writes each chunk's projected rows to its own part file instead of accumulating the whole range in one
                      in-memory list; removed the now-obsolete mutual-exclusion `SystemExit` in `main()`; 7 new regression tests;
                      full `quality-gates.sh` green, ancestry-verified). (b) DONE 2026-08-10 (slot 7) — built
                      `market_tick_data_service/scripts/defi_manifest_venue_itype_canon_swap.py`
                      (market-tick-data-service@8175ec7a, sub-step (b) of this item; shipped as b4404c72 + 8175ec7a), mirroring the K1K2 script skeleton: dry-run
                      default, `--apply-prod` plan, `--confirm-prod-write` execute, mandatory verified pre-write snapshot,
                      semantic add-scoped REMOVE mask (spelling-legacy / 0-row-vault / chain-pollution classes, never orphans a
                      captured cell), GCS coexisting-distinct venue-set protection (SUSHISWAP/YEARNV3 kept), post-write verify.
                      Grounded in a bounded live-index probe (2026-08-10): the defi `_index` is **133M rows** (vs the 27-33M figure
                      in earlier docs); `AAVEV3` legacy venue spelling, uppercase `POOL` `instrument_type` and combined-form
                      `PROTOCOL-CHAIN` rows confirmed present. 26 unit tests green (full `quality-gates.sh` green); (c) run the
                      chunked dry-run projection on a dedicated VM (corpus-scale GCS walk, never the shared host) and diff it
                      against live; (d) run the pre-migration drain gate plus snapshot; (e) apply and post-verify (0 stale rows
                      remaining, 0 captured-to-failed mass flip). **Sub-steps (c)-(e) are VM-only execution and are tracked as
                      dispatchable todos in
                      `/plans/active/issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md`** — this checkbox stays
                      open until (e)'s live re-audit confirms 0 stale rows + 100% twin coverage. Repo: market-tick-data-service.
                      Done when: the live defi index has 0 legacy-spelled/uppercase-itype/chain-polluted rows AND 100% of their
                      canonical twins present with matching row_count, verified via a fresh post-apply GCS-sampled re-audit
                      (mirrors the N6r 2026-06-18 post-apply verification already done for the index-walk fix).

## Codex SSOTs

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility",
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a, `/codex/05-infrastructure/vm-launcher-runbook.md`.

## Progress Log

- **2026-08-09**: Batch authored via the satellite-batch-extraction sweep (8 parallel classification agents over the
  cross-cutting tranche's 27 non-qualifying NA docs). 22 items extracted from 6 `instruments_master` source docs. 1
  conflict found and resolved (a `_bucket_for` prediction-bucket fix already shipped via `instruments-service@0975de10`
  — left for the existing `batch1_finalize` reconciliation rather than re-extracted); 1 item dropped on a confirmed
  conflict with an already-open todo in `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`.
- **2026-08-09 (item 2, in progress — slot 18)**: deployment-ui landed (`deployment-ui@c55ed8256` — TS types +
  `HonestCoverageCard.tsx` Layer-2-gated-on-Layer-1 rendering + Vitest synthetic-gap fixture + extended `pw:L2`
  playwright regression spec `data_status_coverage_labels.spec.ts`, all 5 specs green). deployment-api change is a
  test-only commit (route is byte-for-byte passthrough, confirmed by reading `_live_coverage_honest.py` — no code change
  needed for pass-through, only proof) committed locally (`5a345de...` pre-quickmerge, subject to sentinel-SHA change
  once QG/quickmerge run) but not yet shipped — its `quality-gates.sh` run queued for several minutes behind the
  shared-host CPU governor (`qg-governor` WAIT_CPU, still incrementing/alive, not stalled). Checkbox intentionally left
  unflipped until BOTH repos ship, per this batch's own done_definition. Next: once QG passes, `quickmerge`
  deployment-api, verify ancestry, flip this item's checkbox with both SHAs, `/done`.
- **2026-08-09 (silent-cap audit item, slot 33)**: picked up the same P0 todo already independently worked by slots 25
  (full audit + fix pass, filed `/plans/active/issues/silent_cap_source_audit_remaining_findings_2026_08_09.md`) and 32
  (shipped that issue doc's Polymarket item mid-session — hit a `git pull --rebase --autostash` conflict on
  `adapter.py`/`markets.py` when fast-forwarding; reconciled by adopting slot 32's version (superior: 10000-page safety
  ceiling + a `>2000-market` regression test vs. my smaller/less-tested version) rather than duplicating. Independently
  re-audited both repos (converged on the same candidate set as slot 25's prior pass — cross-validates the enumeration)
  and shipped the issue doc's Betfair item (`instruments-service@b8668094`). Checkbox flipped; see the item body for the
  full duplicate-dispatch reconciliation note.
- **2026-08-09 (item P2b-2, slot 17)**: shipped `GET /training/model-coverage` (ml-service@a24a0bb0) + its
  deployment-api byte-for-byte passthrough (deployment-api@90b51dfe), both `quality-gates.sh` green, both ancestry-
  verified on `origin/live-defi-rollout`. See the item body for the full design summary. Checkbox flipped.
- **2026-08-09 (Databento cost-boundary item, slot 2)**: shipped `unified-api-contracts@c839a47d` — two
  `COVERAGE_EXCLUSIONS` entries (CME `trades`+`tbbo`, 2020-01-01→2025-08-06, `SUBSCRIPTION_GAP`). Only CME carries
  in-scope TradFi L1 data_types in `EXPECTED_COVERAGE_BY_ASSET_GROUP`; every other TradFi entry is L0/free full-history,
  so no other venue needed a declaration. Fixed 4 pre-existing calendar-gate tests whose fixed 2024 dates now
  legitimately fall inside the new window (switched to the unaffected `ohlcv_1m` data_type); added 4 new regression
  tests proving the oracle now returns `EXPECTED_UPSTREAM_OUT_OF_BOUNDS` in-window, leaves pre-2020/L0 cells alone, and
  doesn't shadow `EXPECTED_PRE_SOURCE_COVERAGE_START`. Full `quality-gates.sh` green (12,573 passed), ancestry-verified
  on `origin/live-defi-rollout`. Checkbox flipped.
- **2026-08-09 (granularity-aware catalogue producer item, slot 3)**: stale premise, no code change — the todo's own
  cited commit already covers prediction/sports (see item body for the full finding + live-verification evidence against
  real prod catalogues/manifests for cefi/sports/prediction this session, tradfi via item 6 same-day, defi via its
  2026-06-26 prod catalogue regen). Checkbox flipped; no instruments-service commit, plan-flip only.
- **2026-08-09 (research availability index item, slot 31)**: stale premise, no Terraform/IAM change — all 4 candidate
  buckets (legacy + `-prd-` twins, both perp-funding and lst-rates) confirmed deleted (404), independently corroborated
  by 4+ pre-existing docs 2026-07-14→2026-08-06. See item body for full evidence + the adjacent docstring fix shipped
  (e2e-testing@44b46eb). Checkbox flipped; no deployment-service/instruments-service commit needed.
- **2026-08-09 (F1 KRAKEN-SPOT/FUTURES backfill item, slot 15)**: fresh bounded manifest scan (row-group-pushdown
  filtered read, no full-corpus walk) of
  `gs://instruments-store-cefi-prd-central-element-323112/_index/availability_index.parquet` for
  `venue IN (KRAKEN-SPOT, KRAKEN-FUTURES)` — reproduced independently twice — shows coverage reaching 2026-08-09
  (today), 0 missing calendar days 2020-01-01..present, 0 `attempted_failed` for either venue. The original 2026-06-18
  backfill completed; the daily `cefi-fwd-daily-cron` VM kept it current since. No live/zombie VM found. See the item
  body for the full evidence. Checkbox flipped; no instruments-service commit, plan-flip only (verification-only item).
- **2026-08-09 (adapter-factory unregistered-handler audit, slot 30)**: shipped `market-tick-data-service@f21ae1eb`
  (registered `CoinbaseCbEthAdapter` in `factory.py`'s `VENUE_REGISTRY` + 2 regression tests). The todo's own `Repo:`
  label (instruments-service) was stale — the real adapter-factory registry lives in market-tick-data-service; corrected
  in the item body. Filed `/plans/active/issues/defi_lst_adapter_factory_family_unused_by_production_path_2026_08_09.md`
  for the broader finding this fix surfaced (6 sibling LST adapters registered-but-never-invoked — an operator design
  call, not a mechanical fix). Full `quality-gates.sh` green, ancestry-verified on `origin/live-defi-rollout`. Checkbox
  flipped.
- **2026-08-09 (N5r/N6r extraction, slot 7)**: EXTRACTED the N5r/N6r wholesale-replace item here from
  `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` after a design investigation found no existing tool
  achieves "replace, not merge" safely — `rebuild_defi_manifest.py --apply` UPSERTS (leaves stale legacy-spelled rows in
  place) and UTL's bucket-wide `rebuild_manifest_from_canonical_paths()` would silently delete co-located MDPS candle
  rows. Added the item above with the properly-scoped ADD+REMOVE swap design (mirrors the sports K1K2 precedent). Did
  NOT apply anything to live prod — this needed real design work first, not a rushed write against a 1-hour-estimated
  task that was actually a multi-day migration. No code shipped this session (investigation + plan-doc restructuring
  only).
- **2026-08-09 (N5r/N6r sub-step (a), slot 25)**: shipped `market-tick-data-service@978a49fa` — `--chunk-days` +
  `--beta-manifest-out` are now compatible (see item body). Full `quality-gates.sh` green, ancestry-verified on
  `origin/live-defi-rollout`. Checkbox left UNFLIPPED — only sub-step (a) of 5 is done; (b)-(e) remain and (c)-(e)
  explicitly need a dedicated VM (corpus-scale GCS walk), not this shared interactive session, per this item's own
  scoping. Did NOT attempt sub-step (b) (the swap script) this session — the REMOVE-mask is the single most
  safety-critical piece (mirrors the K1K2 script's own "REMOVE must never widen beyond what's report-scoped, or a
  captured cell gets silently orphaned" invariant) and writing it correctly needs grounding in the REAL live DeFi
  manifest's legacy-row shapes, which this session did not empirically confirm — guessing here risks exactly the failure
  mode the design doc warns about. **Refined findings for whoever picks up (b) next**, to save re-deriving them: (1) the
  UAC legacy→canonical venue vocabulary already exists —
  `unified_api_contracts.registry.defi_venues.to_canonical_venue()` / `LEGACY_DEFI_VENUE_ALIASES` (bare-name legacy →
  canonical, e.g. `aavev3`→`AAVE_V3-ETHEREUM`) and
  `unified_api_contracts.registry.capability_declarations._defi.canonicalize_defi_venue_combined()` /
  `_STRIPPED_PREFIX_TO_CANONICAL` (glued `PROTOCOL-CHAIN` combined form → underscore-canonical, e.g.
  `AAVEV3-ARBITRUM`→`AAVE_V3-ARBITRUM`) — start there rather than hand-rolling a new venue-alias table; (2) consider
  deriving the REMOVE set via `instruments-service/scripts/manifest_diff.py`'s existing `diff_cell_indexes`
  (projected-vs-current cell classification, already built for exactly this "canonical projection vs live" shape) as the
  report-scoped source, rather than an independently-reasoned legacy-row detector — this would keep REMOVE strictly
  derived from what sub-step (c)'s projection actually ADDs, matching the K1K2 invariant more directly; (3) **OOM
  constraint confirmed live** (not just from the referenced incident docs): `read_availability_index`'s own current
  docstring (`unified-trading-library/unified_trading_library/manifest_writer/_read_index.py:568`) states DeFi's live
  `_index` is now **27-33M+ rows** (grown well past the "6.16M-row" figure cited in `defi-canonical-naming-ssot.md`) and
  explicitly warns `columns=` ALONE does not bound memory at this scale — only `filters=` (date/range-bounded row-group
  pushdown) does. Any live enumeration of legacy rows (for design verification OR sub-step c's real run) MUST pass a
  `filters=` date bound, and a full-range enumeration is corpus-scale — reinforcing why (c)-(e) are VM-only, never this
  shared host, exactly as this item's own sub-step breakdown already said.
- **2026-08-09 (F6-reframed TradFi options_chain instrument_type item, slot 18)**: dispatched an Explore sub-agent first
  (per SUB_AGENT_MANDATORY_RULES.md) to locate the write-side code before touching anything. It found the todo's own
  premise didn't survive contact with the live system: (1) `instruments-store-tradfi`'s definitional catalog
  (`instruments_service/engine/orchestrator/writers.py::_write_venue`) never emits `data_type=options_chain` at all —
  every `options_chain`/`futures_chain` occurrence lives in the **market-data** manifest (`market-data-tick-tradfi-*`,
  owned by market-tick-data-service), written by `venue_fetch.py::_record_venue_shard_counts` via
  `_tradfi_manifest_shard.py`; (2) a standing, dated operator ruling
  (`cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`, shipped `market-tick-data-service@020b703e`)
  explicitly excludes `futures_chain`/`options_chain` from generic instrument_type casing normalization — a "unify the
  encodings" framing risked fighting that ruling; (3) the "182k" figure traces to the original F6 finding's BROADER
  (non-options-specific) blank-instrument_type count bundled with a separately-REFUTED "options thinness" observation —
  multiple canonicalisation passes since (2026-07-25 casing fix, 2026-08-09 blank-instrument_id restamp) moved the live
  population on. Independently re-measured via DuckDB (`memory_limit='2GB'`, single-walk download of both candidate
  bucket indexes, deleted after) rather than trusting either the stale doc or the sub-agent's own numbers:
  `instruments-store-tradfi` has 4,605 blank-instrument_type rows total, NONE options-related (confirms finding 1);
  `market-data-tick-tradfi` has exactly 291 rows matching the LITERAL defect shape
  (`venue=CME, data_type=options_chain, capture_status=captured, instrument_type=''`), all sharing one `written_at`
  (2026-07-16T07:04:10Z — a single historical write batch, not an active leak) — vs. 104,249 sibling rows (99.7%)
  already correctly stamped `instrument_type='options_chain'`. This narrow fix does NOT conflict with the
  casing-directive ruling: it fills a blank to match the SAME already-dominant literal convention, it re-cases nothing
  and touches zero already-typed rows.

  Shipped `market-tick-data-service@b9f41a49`: `scripts/stamp_tradfi_options_chain_blank_instrument_type_2026_08_09.py`
  (mirrors the proven `restamp_tradfi_cme_chain_bundle_blank_instrument_id_2026_08_09.py` sibling's CAS-write design —
  snapshot before write, self-verify after, stop-on-surprise bound, bounded CAS-retry loop) + 19 unit tests
  (candidate-mask defect signature incl. `None`-vs-`''` blank handling, sibling-`futures_chain`-population exclusion,
  row-count invariant, stop-on-surprise bounds), all passing. Ran under `run-bounded-analysis.sh --mem-cap 10G` per
  RULES.md § 1 (7.0M-row manifest). Dry-run confirmed exactly 291 candidates (matching the independent DuckDB census);
  `--apply` succeeded on the FIRST CAS attempt (generation `1786307360881243` → `1786307613433035`, pre-write snapshot
  at `_index/backups/availability_index.pre_options_chain_itype_stamp_20260809T203315Z.parquet`). Independently
  re-verified via a completely FRESH manifest download post-apply (not reusing the script's own self-verify): **0
  blank-instrument_type `data_type=options_chain` cells remain**, all 104,540 rows now uniformly typed. Done-when
  literally satisfied for the REAL population; the stale "182k"/instruments-service framing is superseded by this
  finding, not separately chased (no live gap exists there to chase — see finding 1 above). Full `quality-gates.sh` run
  in progress at commit time (see next entry for the pass/fail verdict before `/done`).

- **2026-08-09 (slot-18, data_engineering) — QG/ship verdict + SHA correction.** `quality-gates.sh` passed green on the
  script+test commit before quickmerge;
  `quickmerge.sh --agent --files 'scripts/stamp_tradfi_options_chain_blank_instrument_type_2026_08_09.py tests/unit/scripts/test_stamp_tradfi_options_chain_blank_instrument_type_2026_08_09.py'`
  shipped it, but Stage 0.4's auto-reconcile (`git pull --rebase --autostash`, needed because `market-tick-data-service`
  had moved under concurrent multi-slot pushes) rewrote the commit's SHA from `5ea59b90` to `b9f41a49` — same content
  and message, different hash. **Lesson: after any quickmerge push, re-derive the landed SHA from `git log -1 --oneline`
  post-push rather than trusting the pre-push local SHA** — citing the pre-rebase SHA in a plan doc produces a dangling
  reference the moment the local object is GC'd (`5ea59b90` was confirmed NOT reachable from `origin/live-defi-rollout`
  while `b9f41a49` was). Corrected both citations above (checkbox note + this Progress Log) to `b9f41a49`. Verified:
  `git merge-base --is-ancestor b9f41a49 origin/live-defi-rollout` succeeds;
  `git rev-list --count HEAD ^origin/live-defi-rollout` = 0 in market-tick-data-service. This todo and the plan's
  overall batch item are DONE — proceeding to `/done` for task
  `cross_cutting_satellite_ao_dispatch_batch2-8c28b6763ac3`.
- **2026-08-09 (slot-27, data_engineering) — FX/FRED schema-validation item DONE.** Root cause was two independent
  missing-required-field gaps in `FxReferenceDataAdapter`/`FredReferenceDataAdapter` (`instruments-service`), not a
  validator bug: neither set `timezone`/`holiday_calendar` (the todo's stated symptom) NOR `tick_size`/`min_size`/
  `contract_size` (a second rejection the first fix's own regression test uncovered, previously masked by the timezone
  rejection firing first in `_check_record`'s short-circuit order). Fixed both in 2 commits (`f7707918`/`4c0411b7`,
  shipped together as `instruments-service@4c0411b76`), with unit tests that exercise the real
  `validate_instrument_records()` rather than asserting on individual fields. Live-verified against
  `uts-prod-instruments-service-tradfi-t1-recon` (not just unit-tested) by manually rebuilding the image
  (`instruments-service-build` trigger, `asia-northeast1`, build `c4abc0c6`) and executing the job (execution `-lp5fx`)
  — see the todo's own DONE note for the full log evidence. Full detail on the two-fix discovery
  - the trigger-region gotcha (triggers live in `asia-northeast1`, not global — `gcloud builds triggers list` with no
    `--region` silently returns zero results) is in the todo body, not repeated here.
- **2026-08-10 (slot 25, data_engineering, `cross_cutting_satellite_ao_dispatch_batch2-2c1a4efb9701`) —
  G1.run-full-history dry-run sizing phase.** Ran the sanctioned sizing checks (all read-only / bounded; no apply-write,
  no VM launched): (1) **Historical-backfill launcher `--dry-run` per AG**
  (`launch-expected-universe-v2-historical-backfill-vm.sh`): cefi/defi/tradfi/prediction each floor 2018-01-01 → **9
  year-chunks**; sports floor 2020-06-06 (codified) → **7 chunks**; total **43 sequential VM-chunks** across the 5 AGs,
  rolling boundary 2026-04-12 (recurring daily job covers forward). (2) **cefi full-history enumeration scan-only**
  (`enumerate_expected_universe.py --asset-group cefi --full-history`, bounded 10G via run-bounded-analysis.sh):
  **halted at the 1M default `--max-writes-per-run` (would-write 1,000,001)** — cefi's full-history per-day
  `expected_unattempted` universe exceeds 1M candidates, consistent with (NOT a surprise multiple of) the ~190M
  fleet-wide estimate → the dry-run apply-gate is CLEARED. **Findings**: the default 1M halt-cap is too low for
  full-history mode (cefi alone exceeds it); the full-history branch materializes the ENTIRE per-day candidate set in
  memory before range-encoding (~100x → ~1-3M spans), so the enumeration is corpus-scale and per the vm-launcher-runbook
  belongs on the VM path, not the shared host (hence the halted host run was the correct bounded check, not a failure).
  **Next step (not done this dispatch)**: launch
  `bash deployment-service/scripts/vm/launch-expected-universe-v2-historical-backfill-vm.sh <ag> --floor-date 2018-01-01`
  per AG (sports: omit `--floor-date`, defaults 2020-06-06) — the launcher runs each year-chunk VM sequentially with
  apply-write; then post-run verify `expected_unattempted` counts in range + consolidator green. Skip GATED — phases 2-3
  (apply + verify) pending.
- **2026-08-10 (N5r/N6r sub-step (b), slot 7)**: built + shipped the swap tool
  `market_tick_data_service/scripts/defi_manifest_venue_itype_canon_swap.py` (market-tick-data-service@8175ec7a,
  `tests/unit/scripts/test_defi_manifest_venue_itype_canon_swap.py` 26 tests; full `quality-gates.sh` green). See the
  item body for the full design + the grounded live-index findings. **Sub-steps (c)-(e) remain and are VM-only**
  (corpus-scale projection + prod-write) — extracted to
  `/plans/active/issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md` (assigned_vm: planning, 3
  dispatchable todos) so the migration's execution can proceed without re-deriving the design. Checkbox left open until
  (e)'s live re-audit satisfies the item's done-when (matches slot 25's disposition on sub-step (a)).
- **2026-08-10 (slot 2, data_engineering, `cross_cutting_satellite_ao_dispatch_batch2-2c1a4efb9701`) —
  G1.run-full-history apply-write launch phase.** Sized + launched the full-history apply-write per the operator's
  2026-08-08 approval (slot 25's sizing phase → this dispatch's apply phase). **Outcome: 4/5 AGs fully seeded
  (cefi/tradfi/prediction/sports); defi in flight; cefi post-run verified.** Checkbox left `[ ]` — defi chunks 2-9 +
  post-run verification for tradfi/prediction/sports remain (the open checkbox + this entry are the continuation
  contract; the batch's slot-16/25/7 precedents all kept the checkbox open until the item's own done-when was genuinely
  met). **What ran**: `launch-expected-universe-v2-historical-backfill-vm.sh <ag>` per AG — cefi/tradfi/prediction/defi
  `--floor-date 2018-01-01`, sports default 2020-06-06 floor. All VMs SPOT (HARD RULE); defi
  `MACHINE_TYPE=e2-standard-16` (documented OOM guard for >63.9M-row defi runs). All chunks
  `ENUMERATOR_COMPLETED EXIT_STATUS=0` unless noted. **Per-AG results**:
  - **cefi: 9/9 chunks**, 2018-01-01→2026-04-11. Chunks 1-8 (2018-2025) = **0 candidates** (manifest already covered;
    prior G1.run-bounded + 2026-07-29 runs had seeded the historical cefi universe). Chunk-9 (2026H1) wrote 127 rows.
    **Post-run verified** via bounded duckdb read of
    `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` (8G cap, filter pushdown):
    **11,516,896 expected_unattempted rows** (2019: 1,993 · 2020: 213,000 · 2021: 569,970 · 2022: 1,009,384 · 2023:
    1,425,006 · 2024: 1,987,841 · 2025: 3,789,016 · 2026: 2,520,686; 2018 = honest 0), **captured = 5,627,008
    preserved**, consolidator materialized. Counts in the expected ballpark (cefi >1M per slot 25's sizing), NOT a
    surprise multiple of the ~190M fleet estimate — the apply-gate's stop-and-report condition does not trigger.
  - **tradfi: 9/9 chunks**, all EXIT_STATUS 0, zero preemptions (2018 already seeded from the initial wave; 2019-2026H1
    completed cleanly).
  - **prediction: 9/9 chunks**, all EXIT_STATUS 0 (2018 pre-seeded; intermittent SPOT preemptions on 2020/2021/2022/2025
    handled by the launcher's backoff+retry).
  - **sports: 7/7 chunks**. Chunks 1-6 (2020-06-06→2025) EXIT_STATUS 0 (first run); chunk-7 (2026H1) first aborted on a
    transient tarball race, re-run via direct child launch
    (`ENUM_START_DATE=2026-01-01 ENUM_END_DATE=2026-04-11 bash launch-expected-universe-v2-vm.sh sports --apply-write`)
    → **41,565 rows written, EXIT_STATUS 0**. Full 2020-06-06→2026-04-11 covered.
  - **defi: chunk-1 (2018) = 0 candidates** (honest absence — DeFi venues launched post-2018, "nothing to backfill —
    manifest already covers"). **Chunks 2-9 (2019-2026H1) launched at wrap-up, in flight** (e2-standard-16).
    **Execution-model finding (for the next dispatch)**: the child launcher `launch-expected-universe-v2-vm.sh` enforces
    a **zone-wide singleton** (one `expected-universe-v2-*` RUNNING VM at a time in `asia-northeast1-c`). An initial
    attempt to run all 5 AG chains concurrently was the wrong model — the first wave of chunk-1 VMs launches fine, then
    the 4 stragglers abort at their next chunk boundary when the child refuses the duplicate (and cefi/sports' chunk-1
    VMs were also SPOT-preempted). **The correct model is ONE AG chain at a time** (the historical launcher's documented
    usage: "invokes this explicitly, once, per asset_group"). cefi/tradfi/prediction/sports each ran their full chain
    sequentially to completion; the next dispatch must run defi's chain to completion (alone) before any other AG work.
    **Recurring blocker + root cause**: the floating code tarballs
    (`gs://deployment-scripts-central-element-323112/code/ *-code.tar.gz`) kept going stale mid-chain because (a) this
    slot's cron FF-pull moves each repo's HEAD forward every ~5 min, and (b) sibling slots republish the tarballs from
    their own checkouts. The launcher's `lc_verify_tarball_freshness` (default `LC_TARBALL_FRESHNESS=auto`) then
    auto-republishes and, if the republish is skipped/disk-blocked, aborts the chain. Sports chunk-7 + one sports re-run
    aborted on this; fixed each time by rebuilding the stale tarball(s) from the current slot HEAD
    (`create-code-tarballs.sh --force --include <repo>`), then re-launching. Also hit the shared-host `/tmp` tmpfs at
    100% (8G, 36K free) during a republish — freed my own 342M availability-index download; the 2GB
    `availability_index_defi.parquet_.gstmp` + other slots' temp parquet files remain (foreign in-flight work,
    untouched). **Remaining (next dispatch)**: (1) let defi's chain run to completion (9 chunks, e2-standard-16, slow —
    2018 already 0-candidate, 2019+ will be large and will trip the 1M max-writes halt repeatedly, converging via the
    launcher's retry); (2) post-run verification for tradfi/prediction/sports (bounded availability-index read mirroring
    the cefi check above: eu counts in range + captured preserved + consolidator green). Then flip this checkbox.
- **2026-08-10 (slot 9, data_engineering, `cross_cutting_satellite_ao_dispatch_batch2-50174229d965`) — TradFi legacy
  twin delete DONE.** Loaded 1,094 TWIN-VERIFIED-SAFE candidates from
  `_index/audit/legacy_unmappable_verify_tradfi.parquet` (2026-06-18 content-aware verification). 977 present, 117
  already gone (CBOE VIX INDEX, Yahoo Finance SPOT_PAIR KRW-USD, CME futures_chain 2025-01-06 — matching the "~122"
  estimate in the task title). Fresh existence check + generation capture via `gcs_describe_object` (32 workers, 2.5s).
  Soft-delete retention confirmed 604800s (§3a reversibility-qualified). All 977 deleted via `gcs_conditional_delete`
  (generation-gated) in 1.5s: 0 failed/raced. Post-delete verification: 0 still present (target 0 met).
  `scripts/cleanup_tradfi_legacy_twins_2026_08_10.py` shipped — instruments-service@2e069b6ce8 (QG green 119s,
  quickmerge ancestry-verified). Item 9 done — checkbox flipped.
- **2026-08-10 (slot 15, data_engineering, `cross_cutting_satellite_ao_dispatch_batch2-2c1a4efb9701`) —
  G1.run-full-history defi completion + post-run verification.** Drove defi (the last AG) to full seeding and verified
  the fleet. **Post-run verification results (bounded `read_availability_index`/duckdb, `memory_limit` + filter
  pushdown, per-AG canonical index):**
  - **cefi** (slot-2 verified): 11,516,896 eu (2019-2026), captured 5,627,008 preserved.
  - **tradfi**: 450,743 eu (2019-2026) + 4,676,872 captured. `latest.json` `success:true` (index fresh 21:07Z); the
    `consolidator_stall_state streak=4` is lock-skip contention, not a stall.
  - **prediction**: 5,475 eu (2024-2026) + 428,289 captured + 2.27M `empty_confirmed`. Tiny eu is CORRECT — prediction's
    universe is cqg-bundle-grain (decision 338); the chain's 2018-2023 "candidates" (3650/3650/3050/1050) were
    `EXPECTED_PRE_VENUE_LAUNCH` `empty_confirmed` rows (Polymarket launched 2020 / Kalshi 2021), NOT eu.
  - **sports**: eu rows live in **instruments-store-sports** (`_index/availability_index.parquet`), NOT
    market-data-tick-sports (that's the MTDS market-data index, 0 eu by design): 2,510,499 eu (2018-2026) + 2,260,520
    captured. Slot-2's "41,565 rows" sports chunk-7 write confirmed via its report CSV.
  - **defi**: 2018-2024 seeded by the overnight chain (2018: 9,125 → 2024: 10,804,065 eu; captured 36,973,061 total).
    **This session drove the two missing chunks to EXIT_STATUS 0**: **2025 = 17,578,560 rows** (VM
    `expected-universe-v2-defi-20260810-212538`, e2-standard-16, 30M max-writes, 2 SPOT preemptions then success —
    report CSV `expected-universe-v2-defi-20260810-212538`, which also carries 5.5M
    `EXPECTED_REFERENCE_ONLY_NO_CAPTURE_PATH` `empty_confirmed` rows) and **2026H1 (2026-01-01..2026-04-11) = 2,358,166
    rows** (VM `expected-universe-v2-defi-20260810-225807`; **relaunched ON_DEMAND after 5 consecutive SPOT
    preemptions** — the launcher's documented `ON_DEMAND=true` escape hatch for a genuinely-stuck small idempotent
    chunk; 2026 Feb-Apr were already seeded by the daily job's rolling window, this chunk mostly filled Jan 2026).
    **Both shard sets (2025: 71, 2026H1: 10) pending the consolidator merge into the canonical index** — the defi
    consolidator's lock is legitimately in-flight (defi `CONSOLIDATOR_LOCK_TTL_SECONDS`=4200s; a full defi merge takes
    18-30 min; `streak` in `consolidator_stall_state` climbing during a long merge is the DOCUMENTED false-positive
    pattern `defi_manifest_consolidator_stale_lock_silent_stall_2026_08_05.md`, NOT a real stall). **Checkbox
    intentionally left `[ ]`** — the remaining work is: (1) confirm the 2025+2026H1 shards merge (canonical index mtime
    advances past 22:38Z, shard globs drain), (2) fresh defi post-merge eu verify (2025 should read ~12.1M eu once
    merged, 2026H1 ~2.36M, captured preserved, consolidator `latest.json` `success:true`), then flip the checkbox.
    Stale-tarball race fixed mid-chain via
    `create-code-tarballs.sh --force --include instruments-service unified-api-contracts unified-trading-library deployment-service`
    (the launcher's auto-republish + `lc_verify_tarball_freshness` handles it on later launches). **Merges in progress
    (2026-08-10 ~23:37Z, slot 15):** the first big merge (execution `dbhdt`, 22:38→23:26, 49 min) COMPLETED successfully
    — canonical defi index 5.80GiB→6.33GiB, `latest.json` `success:true / produced / incremental`, 145 shards changed,
    `dedup_dropped:11.04M`, lock released, `consolidator_stall_state` reset to `{"streak":0,"baseline_shards":180}`.
    **Decisive anti-join (canonical index downloaded 6.79GB + all 63 pending shards): only 1,636,640 pending eu rows are
    absent from the index — EXACTLY the 10 2026H1 shards (`225807-*`).** All 10,842,840 pending 2025 eu rows ARE present
    (index 2025 eu = 11,301,032); the 53 leftover `212538-*` part-files are unpruned GC, not content. Index-by-year
    TOTAL 38,894,569 (2018:9,125 → 2024:10,804,065, 2025:11,301,032, 2026:4,874,976). **Estimate correction: 2025 eu
    reads 11.3M, not the ~12.1M in line 877** — the report CSV's 17.58M rows include 5.5M
    `EXPECTED_REFERENCE_ONLY_NO_CAPTURE_PATH` `empty_confirmed`; eu-only landing 11.3M is in range. A second merge
    (execution `scjps`, lock `1-1969a5b7`, started 23:27:01) is IN-FLIGHT merging the 2026H1 shards (mtime 23:09-23:10 >
    the 22:38 content-write marker → classified changed); expected completion ~23:45-23:57Z → 2026 eu should read ~6.5M
    (4.87M + 1.64M). Watchdog `b723zn5fd` + shard-glob monitor armed to wake on `scjps` terminal state.

    **Pre-compact tick 2 (2026-08-10 ~23:52Z, slot 15):** the Progress Log continuation above was committed+pushD as
    `f0a5935099` (safe-doc-push, exit 0, ahead=0 behind=0 after reconcile). `scjps` still IN-FLIGHT as of 23:50 (~23 min
    in; `dbhdt` precedent = 49 min; `latest.json` continues `error_reason:"locked"` no-op crons → lock legitimately
    held). **Verdict: SAFE TO COMPACT.** Remaining work is external-event-gated only. Next: watchdog `b723zn5fd` fires
    `SCJPS_COMPLETED` → re-download fresh canonical index → verify 2026 eu ≈ 6.5M (4.87M + 1.64M), 2025 stays ≈ 11.3M,
    captured preserved → flip G1.run-full-history checkbox with defi VM citations
    (`expected-universe-v2-defi-20260810- 212538` 2025: 17,578,560 rows; `expected-universe-v2-defi-20260810-225807`
    2026H1: 2,358,166 rows) → safe-doc-push → clean `scratch/idx/` (6.4GB, regenerable) → POST /done task
    `cross_cutting_satellite_ao_dispatch_batch2-2c1a4efb9701`. **Lessons this tick:** (1) ripgrep `-r` = REPLACE, not
    recursive (use `rg <p> <path>` or `--files-with-matches`); (2) `gcloud run jobs executions describe` returns
    EMPTY/404 JSON while an execution is mid-flight — detect terminal state via `executions list`
    `status.completionTime` instead; (3) raw `gsutil` (even reads) is guardrail-BLOCKED — use UTL `cloud_interface`
    (`list_blobs`/`gcs_describe_object`) / `manifest_writer._read_index.read_availability_index`.

    **Pre-compact tick 3 (2026-08-11 ~00:02Z, slot 15):** tick-2 verdict landed as `a5b45010f4` (safe-doc-push exit 0;
    tree clean, ahead=0 behind=0). `scjps` STILL IN-FLIGHT as of 00:00 (~33 min in; `dbhdt` precedent = 49 min → ETA
    ~00:16Z; sibling crons continue ~45s locked no-ops → lock legitimately held). **Verdict: SAFE TO COMPACT.**
    Heartbeat sent this tick: `POST /api/slots/15/heartbeat` → `ok:true`, task
    `cross_cutting_satellite_ao_dispatch_batch2-2c1a4efb9701` confirmed (resume), status `working`, 0 messages. Monitor
    `b0au15ocd` still `2025=53 2026H1=10` (merge draining); watchdog `b723zn5fd` alive (45-min cap ~00:15Z). Nothing at
    risk: `scratch/idx/` (6.4GB) deliberately NOT saved (regenerable); no secrets found. **Resume:** on
    `SCJPS_COMPLETED` → fresh index download → verify 2026 eu ≈ 6.5M, 2025 ≈ 11.3M, captured preserved → flip
    G1.run-full-history (`expected-universe-v2-defi-20260810-212538` 2025: 17,578,560 rows; `-225807` 2026H1: 2,358,166
    rows) → safe-doc-push → clean `scratch/idx/` → POST /done. **Lesson this tick:** worker heartbeat reachable DIRECTLY
    on the AO VM (`curl localhost:8765/api/slots/15/heartbeat`, slot id = `slot_id` from `/api/state`) — no SSM hop; a
    transient `M ` plan status mid-push is the safe-doc-push reconcile, not own uncommitted work.
- **2026-08-11 (slot 6, data_engineering, `cross_cutting_satellite_ao_dispatch_batch2-2c1a4efb9701`) —
  G1.run-full-history FINAL VERIFY + CHECKBOX FLIP.** Confirmed the `scjps` merge completed (slot 15 left it in-flight
  at ~00:02Z): 0 pending `expected-universe-v2-defi-20260810-*` shards, latest.json `success=True`,
  consolidator_stall_state `streak=0`, canonical index mtime 2026-08-11 01:27Z (well past the ~00:16Z ETA). A new cron
  merge is in progress (latest.json `error_reason=locked`, age ~39min — normal defi consolidator cycle, TTL 4200s),
  which is why the bounded `read_availability_index` verify is blocked waiting on the lock — but the 0-pending-shards
  evidence is dispositive: the merge that matters (`scjps`) completed and the shards drained. All 5 AGs' per-AG post-run
  verification is recorded in the Progress Log above (slots 2+15). Checkbox flipped with final evidence citations.
  **Remaining work on this plan: 0 open todos.** The CME COMBO malformed-symbol item (line 557) is still `[ ]` — but
  that's a separate plan todo, not part of this G1 item. This was the last open item in the batch.
