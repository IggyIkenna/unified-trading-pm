---
doc_type: plan
title: Data-Pipeline AG Residual Backfill Decisions — TradFi + DeFi (forked from the hardening/self-monitoring plan)
summary: |
  The residual per-asset-group data-backfill/scope decisions forked out of
  data_pipeline_hardening_self_monitoring_2026_06_22.md's "TradFi pending work" section + the DeFi/TradFi correctness
  items surfaced during per-AG hardening dispatch, during the 2026-07-24 line-cap remediation split. Covers retrying
  the tradfi attempted_failed cells, fixing the UAC image-packaging bug biting tradfi builds, fixing alerting-service
  app-log visibility (tradfi-adjacent), threading real HTTP-status evidence into DeFi's clean-path fetch-evidence
  calls, resolving the tradfi ohlcv_15s spurious-aggregation-tier bug, and the tracked defi DIVERGENT_EMPTY per-venue
  backfill-vs-scope campaign (name-drift reconciliation + never-collected/out-of-MVP triage — operator HARD RULE: no
  flat clip).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui]
scope: [engineer, admin]
tags: [data-pipeline, tradfi, defi, backfill, divergent-empty, plan-split, residual]
related:
  [
    /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    /plans/archive/2026_07/data_pipeline_alert_substrate_residual_2026_07_24.md,
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
  ]
created: "2026-07-24"
last_updated: "2026-08-20" # F-CROSSCUTTING-8 wave-launcher FOLDED-IN claim vs code verification
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only # was: orchestrator-agent — corrected 2026-08-19 (plan_reconciler, cross-cutting) — only valid NA-paired value
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
drift_direction: advance-code
supersedes:
superseded_by:
depends_on:
source:
  [
    "Forked 2026-07-24 from data_pipeline_hardening_self_monitoring_2026_06_22.md per the plan line-cap remediation
    triage (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 9, 'AG backfill decisions' fork) — operator
    approved unlock+split via interactive Q&A.",
  ]
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /plans/archive/2026_08/issues/defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    deployment-service/scripts/wave_launcher.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/governance_adapter.py,
  ]
---

# Data-Pipeline AG Residual Backfill Decisions — TradFi + DeFi

> **Forked 2026-07-24** from
> [`data_pipeline_hardening_self_monitoring_2026_06_22.md`](/plans/archive/2026_08/data_pipeline_hardening_self_monitoring_2026_06_22.md)
> as 1 of a 4-way split (+ 1 excise) approved by the operator via the plan line-cap remediation triage
> (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 9). Unlike the sibling forks (alert substrate,
> self-healing completion), everything here is a **per-asset-group data decision**, not systemic-guard code — moved
> **verbatim** from the parent's "TradFi pending work" section and its per-AG hardening dispatch. Sibling forks:
> `data_pipeline_alert_substrate_residual_2026_07_24.md`,
> `data_pipeline_self_healing_completion_residual_2026_07_24.md`. **Operator HARD RULE carried forward from the
> parent**: no flat clip on the defi DIVERGENT_EMPTY residual — every venue/data_type gets a per-pair backfill-vs-scope
> decision, not a blanket reclassification.

## TradFi pending work — NOT yet done (tracked 2026-06-22, slot-0·human-planning)

Status after the 3-deploy /autonomous run: alerting consumer LIVE (`dp-alerting-subscriber`, fix `8897e91`), daily-audit
jobs LIVE. tradfi = **84.1% cell-complete** (13 failed cells; 31% rows still `expected_unattempted`). Remaining tradfi
items:

> **✅ Tradfi EU universe-correction APPLIED 2026-06-23 (addresses caveat (a) below — the completion oracle now reads a
> real fetchable target).** The live tradfi `_index` over-seeded `expected_unattempted` with unfillable cells; the
> in-place row-preserving reclass (`instruments-service/scripts/correct_tradfi_universe_floor_clip_and_vix_index.py`,
> instruments-service@e9e5128) moved **EU 1,466,157 → 1,084,542** (−381,615: floor-clipped out-of-rolling-window L1
> trades/tbbo + L2 mbp_10 = 241,085 → `EXPECTED_OUT_OF_COVERAGE_WINDOW`; derived ohlcv_15m = 140,530 →
> `EXPECTED_OUTSIDE_PROCESSING_SCOPE`). captured 733,338 + attempted_failed 16,358 UNCHANGED (absolute gate). Honest
> coverage (captured/(captured+failed+EU)) 33.1% → 39.98%. Plan-of-record + full evidence:
> `/plans/archive/2026_08/tradfi_multisource_backfill_2026_06_22.md` § "VIX-index DELETE + Databento universe
> floor-clip" (see also `/codex/02-data/tradfi-databento-sourcing-ssot.md` § "VIX — futures vs the cash index"). The
> remaining EU is now the genuine fetchable backfill target (ohlcv_1s/1m within the 16y L0 floor + in-window
> trades/tbbo/mbp_10 + corporate_action/earnings refdata).

- [x] ✅ [INFRA] P0. **Autonomous wave-launcher → tradfi 100% — LIVE 2026-06-22** (`deployment-service@ebfe6e3`
      `scripts/wave_launcher.py`). Reads the tradfi index, builds per-`(venue,root,year)` dispatch atoms (NOT
      root×year×data_type — `data_type` is not part of the `Dispatch` grouping key; a launcher venue backfills
      whichever OHLCV data_types it owns) from cells whose status is `expected_unattempted` OR `attempted_failed`
      (`NEEDS_WORK`), caps at `WAVE_MAX_CONCURRENT=12` (hard ceiling 20, `budget=cap-running`), drops cells running VMs
      own, launches via the per-venue `launch-tradfi-bf-*-ohlcv-1m.sh`. **LIVE-PROVEN**: a controlled tick launched
      NYSE-2023/NASDAQ-2024/NYSE-2024 (fleet 8→11, cap-respected, 1 expected fail = CBOE-2025-no-shards). **Automated**
      via a `0 */3 * * *` cron on the planning host (gcloud+workspace+venv present; needs `WORKSPACE_ROOT` so the
      launchers resolve UAC). **Caveats / follow-ups**: (a) CBOE-2025 + ICE + YAHOO cells are permanently
      un-backfillable (no databento shards / out-of-subscription) → they stay `expected_unattempted` forever, so the
      completion target must EXCLUDE unfillable cells or it never reads 100% (refine the completion oracle). (b)
      host-cron is the immediate autonomy; the durable cloud-native form is a Cloud Scheduler → gcloud-equipped
      ephemeral runner (a Cloud Run Job can't launch VMs — no gcloud) — follow-up. (c) wave events emit mode='local'
      (DP_TRADFI_WAVE_LAUNCHED isn't registered in the alert registry, so wouldn't route anyway; the VMs it launches ARE
      covered by the exit_code/heartbeat monitors). The alerting is now live so launcher failures alert. **(was:
      trailing "— NOT DONE (the building agent hit the session limit at 22:10 UTC reset). Need
      `deployment-service/scripts/wave_launcher.py` (reads tradfi `expected_unattempted` gaps by root×year×data_type,
      launches `launch-tradfi-backfill-vm.sh` waves, HARD cap `MAX_CONCURRENT≤12` never >20, dry-run-first, completion
      at expected_unattempted=0) + a Cloud Scheduler firing every 2-3h. Without it the 8-VM manual wave stalls; tradfi
      never reaches 100% autonomously." — corrected 2026-07-14, doc-reconciliation verify-rerun-2 finding 178: this
      same-bullet tail was stale leftover text from a pre-build session that hit the limit before the launcher existed;
      it directly contradicted this bullet's own checked `[x]` + "LIVE-PROVEN" framing above, and later sections of this
      doc (§ "wave-launcher multi-source" + the auto-kill heartbeat-stalled-VM section) already treat the wave-launcher
      as live, functioning infrastructure with no correction of this tail.)** **(was: "BOTH `expected_unattempted` AND
      `attempted_failed` — the P1 retry is FOLDED IN" — corrected 2026-08-20, F-CROSSCUTTING-8 verification against the
      live `deployment-service/scripts/wave_launcher.py` code (this doc's own `context_scope` citation): `NEEDS_WORK`
      does include `attempted_failed`, but the wave-launcher is OHLCV-ONLY per its own docstring — a manifest row only
      enters the candidate pool if its `data_type` is in `OHLCV_DATA_TYPES` (`ohlcv_1m`/`ohlcv_1s`) AND its `venue` has
      an entry in `LAUNCHER_FOR_VENUE` (CME/CBOE/NASDAQ/NYSE only). Rows failing either filter land in `out_of_scope`
      and are explicitly "reported but never launched" (docstring's own words; code path: `compute_dispatch_candidates`'s
      `addressable_mask`). So "the P1 retry is FOLDED IN" only holds for `attempted_failed` cells that are
      `ohlcv_1m`/`ohlcv_1s` at one of those 4 venues — any cell outside that (a non-OHLCV data_type, or a venue like
      ICE/FX/KRX with no launcher) is NOT retried by this mechanism at all, contra the unqualified "FOLDED IN" framing.
      Separately, even for genuinely in-scope OHLCV cells, a wave-launcher dispatch does not guarantee resolution: the
      archived `plans/archive/issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md` found ohlcv_1s/ohlcv_1m
      `attempted_failed` at exactly these 4 venues still large and ACTIVE 4+ weeks after this bullet's "LIVE" date
      (224,204 / 81,220 rows, shrinking only 1.3%/11.3% over the prior 16 days) because most of that population is a
      real upstream Databento silent-zero-row gap (`WithinBoundsTradfiSourceZero`) that reproduces on a plain retry —
      the wave-launcher keeps re-attempting these cells forever, it doesn't root-cause or purge them. No doc in this
      corpus records the venue/data_type breakdown of the specific "13 cells / ~12.5k rows" the open P1 todo below
      names, so whether they are even in the wave-launcher's addressable set was never actually checked before this
      bullet claimed FOLDED IN — see that todo's own note.)** — deployment-service
- [x] ✅ [DATA] P1. **tradfi schema-drift — `DP_NOT_V9=13670` RESOLVED 2026-06-22**
      (`populate_v9_index_columns_inplace --asset-group tradfi --apply`: the 13,670 rows were `schema_version=4` legacy;
      derived pipeline_mode/source in-place + bumped to 9; ALSO filled 903k blank pipeline_mode + 1.4M blank source on
      already-v9 rows. Written index = 100% v9 / 6.81M rows, captures UNCHANGED (734102), GATE-passed, snapshot kept).
      **(was: unqualified "100% v9" — corrected 2026-07-14, doc-reconciliation verify-rerun-2 finding 180: a 2026-06-27
      audit — `/plans/archive/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md`,
      after fixing an unrelated string-vs-int display bug that had been masking the true count — found a genuine
      ~98,476-row (~4%) tradfi non-v9 residual (legacy `'4'` + empty `''` + instrument-key-contaminated `schema_version`
      values) still present 5 days after this "100% v9" claim. That audit's operator-decision item to clean the residual
      was still `- [ ]` open as of this correction; the "100% v9" completeness claim above does not hold as stated.)**
      **`DP_NOT_V9`** originally (13,670 tradfi rows NOT at canonical schema_version=9), surfaced by the now-live
      `manifest_hygiene_daily` audit. Re-walk/canonicalise those rows to v9. — market-tick-data-service
- [ ] [DATA] P1. **Retry the tradfi `attempted_failed`** (13 cells / ~12.5k rows) — surfaced by the digest. Re-run the
      backfill for the failed (venue,data_type,day) cells. **Left open 2026-08-20 (F-CROSSCUTTING-8 verification)**:
      the wave-launcher bullet above claims this is "FOLDED IN" — traced `wave_launcher.py`'s actual selection logic and
      that claim only holds conditionally (OHLCV `data_type` at a CME/CBOE/NASDAQ/NYSE launcher venue — everything else
      is reported-but-never-launched `out_of_scope`), and nobody had traced that logic before checking this box off. No
      surviving doc records which venue/data_type this specific 13-cell population is, so it's unverified whether it's
      even in the wave-launcher's addressable set; genuinely non-OHLCV or non-launcher-venue cells need a manual retry
      this todo still covers. Also note the 13-cell/~12.5k-row count is from 2026-06-22 and is very likely stale — the
      manifest showed `attempted_failed=342,211` by 2026-07-13 and the OHLCV subset alone was 305k+ rows by 2026-07-23
      (`plans/archive/issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md`) — a fresh manifest read is needed
      before this todo can be sized or closed. — market-tick-data-service
- [x] ✅ [INFRA] P2. **UAC image-packaging bug — already RESOLVED 2026-06-23** (see this doc's own "2026-06-23
      follow-ups RESOLVED" note above: clean alerting image bundles `registry/data/*.json`, `dp-alerting-subscriber`
      redeployed clean rev 00008-csc with NO datafix layer, UAC wheel 0.48.0 exports `build_fetch_evidence`).
      **RE-VERIFIED LIVE 2026-07-28 (slot-11)**: corpus-wide grep for `datafix`/`dp-subscriber-datafix` across
      alerting-service + deployment-service returns ZERO hits (no regression); `alerting-service/Dockerfile` confirms
      the standard UTL-base-image pattern (no local sibling-repo COPY, no thin datafix layer) — this checkbox was
      genuinely done but never flipped here. — unified-api-contracts, deployment-service
- [x] ✅ [INFRA] P3. **RESOLVED 2026-07-28** — not a handler/stdout config gap per se: root cause was the project's
      `_Default` Cloud Logging sink `debug-filter` exclusion
      (`severity <= "DEBUG" AND NOT resource.type="cloud_run_job"`) silently dropping every plain-text
      (severity-`DEFAULT`) stdout/stderr line from this Cloud Run **service** (jobs are exempted). Fixed by switching
      `api/main.py::_configure_stdout_logging()` to UTL's structured-JSON `setup_cloud_logging(json_format=True)` so
      Cloud Run tags real severities instead of defaulting everything to `DEFAULT`. alerting-service@62b850c;
      live-verified on redeployed revision `dp-alerting-subscriber-00015-lcn` (`gcloud logging read` now shows
      INFO/WARNING route + lifespan logs). Full diagnosis: `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md`'s
      "Diagnose the alerting-service Cloud Logging ingestion gap" item (flipped same-turn). — alerting-service

## Blank `asset_group` re-blank class (C3 sibling — stale-tarball producer) — FIXED 2026-06-22

- [x] ✅ [CODE] P0. **Consolidator self-heals blank/absent `asset_group` from the per-AG market-data bucket** —
      `unified-trading-library@7b2306c3` (QG green 110s, sentinel==HEAD; 3 new regression tests, 31/31 consolidator
      tests pass). **Root cause**: 73.9k defi (`onchain_subgraph`/`onchain_rpc` DEX swaps) + 2.3k cefi (`hyperliquid`)
      `captured` rows read BLANK `asset_group` in the consolidated index, re-blanked every consolidation tick. The
      `mdps-defi-2025-20260622-074035` VM launched **07:41 UTC** on a pre-v9 UTL tarball whose `record_captured`
      predates the `asset_group` ROW COLUMN (landed UTL `4bd9487e` **13:59 UTC** — ~6h after launch) → its per-VM shard
      has the column ABSENT → `union_by_name` fills NULL → canonical reads blank. `asset_group` is NOT a dedup key, so a
      one-shot canonical re-stamp is re-blanked by the still-column-less shard on the next cycle. **Fix (systemic,
      durable)**: `manifest_consolidator._asset_group_for_market_data_bucket(bucket)` derives the single AG a per-AG
      `market-data-tick-{cefi|defi|tradfi|sports|pred}-` bucket holds; the DuckDB merge now `COALESCE`s a
      blank/NULL/absent `asset_group` to that AG at merge time (both incremental + full-rebuild branches; `REPLACE` when
      the column is present-but-blank, projected-`AS` when absent) — heals ANY stale-producer shard every cycle, no
      per-VM coordination. The current `record_captured` already emits the column correctly (this is a
      stale-running-VM + missing-consolidator-guard class, not a writer bug). **Operational re-stamp (guarded)**:
      snapshotted both consolidated indexes to `_index/snapshots/pre_mdps_ag_restamp_2026_06_22.parquet`, re-stamped
      defi 79,689 + cefi 2,297 blank rows → bucket-AG (rowcount + captured-count preserved; `blank_after=0` both) AND
      the per-VM shards (mdps-defi-2025 + both `_legacy_seed`) so even the pre-deploy Cloud Run consolidator keeps the
      column. **Residual (bounded, self-healing)**: the still-running pre-v9 `mdps-defi-2025` VM appends NEW column-less
      rows until it finishes/self-deletes; the consolidator fix heals them every `*/1` cycle once the consolidator image
      rebuilds from `main` (the durable guarantee — no manual re-stamp needed thereafter). — unified-trading-library
  - **✅ RE-ACCRUAL VERIFIED + DURABLE SELF-HEAL PROVEN ON LIVE DATA (2026-06-22 ~23:08Z resume-run,
    slot·human-planning, Opus 4.8):** ran the prompt's "VERIFY no re-accrual after a consolidator tick" check.
    **Re-accrual IS occurring as predicted**: the consolidated defi `_index` had **30,236 blank/NULL `asset_group` rows
    among captured** (UNISWAP_V3/V4/V2 + BALANCER/CURVE/SUSHI swaps_ohlcv\_\*, source `onchain_subgraph`/`onchain_rpc`,
    `attempted_at` up to 23:05Z = minutes-fresh) because the pre-v9 `mdps-defi-2025-20260622-074035` VM is STILL RUNNING
    (`purpose=mdps-sharded-backfill`, year 2025, launched 07:41Z ~15.5h ago — a LEGITIMATE bounded backfill, NOT a
    zombie, so NOT stopped) and keeps appending column-less rows, AND the SCHEDULED Cloud Run consolidator
    (`uts-prod-manifest-consolidator-execution-defi`, last ran 23:07Z) is on the OLD image (the UTL@7b2306c3 self-heal
    is on LDR but the consolidator image rebuild is **gated by the same fleet-wide GitHub Actions outage** as items
    3/5).

    **Durable fix proven**: ran the FIXED consolidator from the workspace UTL (7b2306c3 IS ancestor of HEAD —
    `_asset_group_for_market_data_bucket` COALESCE at `manifest_consolidator.py:1289`) `--force` against live
    `market-data-tick-defi-prd-…` → success, 4,108,810 rows out, 6.3s → **BLANK now 0 / 100% `asset_group=defi` verified
    by re-read**. Also healed tradfi (12→0, 6.81M rows) for completeness; cefi/sports/prediction already 0. **All 5 AG
    consolidated indexes now 0 blank `asset_group`.** **Bounded residual (self-healing, no action owed):** between now
    and (a) the backfill VM finishing OR (b) the consolidator image rebuilding from `main` (Actions-gated — unblocks
    with items 3/5), the scheduled consolidator will re-blank defi each `*/1` cycle from the running VM's new shards;
    once the image carries 7b2306c3 it self-heals every cycle with no manual run. The manual `--force` run above keeps
    coverage honest in the interim. — unified-trading-library

- **2026-06-22 unfillable-cell reclassification (slot-0·human-planning, Opus 4.8)** — operator: "class unfillable or
  mass-enter as `empty_confirmed` with reason." Investigated the tradfi `expected_unattempted` by venue + the databento
  3-dataset allowlist (GLBX.MDP3/DBEQ.BASIC/XCBF.PITCH). **ICE (530,600 cells) is genuinely unfillable** (out of
  subscription — no databento dataset, not Barchart/Yahoo) → in-place re-classified to
  `empty_confirmed`/`error_reason=EXPECTED_NO_PROVIDER_COVERAGE` (snapshot `pre_ice_reclassify_2026_06_22.parquet`,
  GATE-passed: rows + captured unchanged). **Honest coverage 68.4%→76.2%** (cell-grain ~84%→higher). Deliberately LEFT:
  CME/NYSE/NASDAQ (databento-fillable gaps the wave-launcher works), **CBOE (1,930 = VIX/SPX _index_ cells, fillable by
  Barchart/Yahoo — a different source, not databento)**, **FX (3,228 spot pairs, already source-stamped
  massive/databento — ambiguous, marking would hide a real gap)**. **RESIDUAL**: the wave-launcher (databento-only)
  can't fill CBOE-index/FX (~5,158 cells), so its `expected_unattempted==0` completion check should SCOPE to
  databento-fillable venues (or those get their own Barchart/Yahoo backfill) — else it never reads 0. Follow-up. —
  market-tick-data-service

- **2026-06-22 multi-source backfill RESOLVED (slot-0·human-planning, Opus 4.8)** — agent built the
  venue→source→fillable matrix + wired it. **Massive does NOT have ICE** (probed S3:
  crypto/forex/us_futures-CME/indices/options/stocks prefixes, no ICE; `_MASSIVE_FUTURES_VENUES={CME}`) — so per
  operator ICE flipped → `empty_confirmed`/`EXPECTED_NO_PROVIDER_COVERAGE` (530,600; snapshot
  `pre_ice_final_reclass_2026_06_22.parquet`; credential-ask on file if ever wanted). **CBOE cash-index** (1,614
  VIX/SPX) → `empty_confirmed` (not in any databento dataset; VX futures via XCBF.PITCH ARE captured + preserved) —
  `market-tick-data-service@2c6425b`. **FX-spot** (USD/KRW) → yahoo daily `launch-tradfi-bf-fx-ohlcv-24h.sh` +
  **wave-launcher multi-source** (`LAUNCHER_FOR_VENUE`+FX, per-venue data_types, ICE excluded) —
  `deployment-service@eab5aeb`. NASDAQ/NYSE confirmed DBEQ.BASIC equities (correctly databento). **Net: honest coverage
  76.2%, remaining FILLABLE eu=1,607,003 (all databento/yahoo) = the wave-launcher's reachable 100% target.** Plan:
  `/plans/archive/2026_08/tradfi_multisource_backfill_2026_06_22.md`.

- **2026-06-23 follow-ups RESOLVED (slot-0·human-planning, Opus 4.8)** — (P1) UAC image-packaging: clean alerting image
  now bundles `registry/data/*.json`; `dp-alerting-subscriber` RE-DEPLOYED clean (rev 00008-csc, NO datafix layer);
  published UAC wheel 0.48.0 exports `build_fetch_evidence` (fleet ImportError gone). (P3) FX→yahoo FIXED (3 bugs:
  launcher var-order/databento-misroute, D+1/D+2 timestamp-bias zeroing rows, --source gate) + verified a live Yahoo FX
  row — `deployment-service@6dbce30` `mtds@bf19ab8/5272143`. (P4) CBOE-316 options_chain (SPX/VIX OPRA options, no
  provider) → `empty_confirmed/EXPECTED_NO_PROVIDER_COVERAGE` (`mtds@b3f67ac`, GATE-passed). (P2) alerting app-logs:
  code FIXED (stdout handler + consume/route/POST INFO logs, `alerting@9b6d429/8e511d4/9e52751`) verified LOCALLY, but
  the DEPLOYED instance still surfaces 0 app-logs in Cloud Logging (Cloud-Run stdout-ingestion quirk; webhook still
  fires — alerting works, only visibility impacted) → `[INFRA] P2`. **NEW FINDING**: an FX cell marked `captured` with
  NO backing parquet — possible pre-existing manifest/data mismatch → audit follow-up. **Backfill** running at cap=20,
  ~11k captured/day (~85% rate), consolidator current; multi-day grind on the 1.6M backlog, monitor `bvcaydjvf` armed.

## Residual from Phase 3 (defi DIVERGENT_EMPTY, closes C2/C3)

- [ ] [CODE] P1. **Residual defi DIVERGENT_EMPTY real-gaps (13,760, 2 classes) — backfill OR handler↔oracle data_type
      reconciliation (C2/C3)** — **RE-VERIFIED 2026-06-22 (post-coverage_start-fix re-run of
      `detect_manifest_divergence.py --asset-group defi` on the live prod `_index`): 22,140 → 13,760 confirmed (−8,380
      clip by UAC@bfe6736b), MAX DATE 2025-11-18, ZERO in the operational window (≥2025-11-19) — all historical, NOT
      blocking. The 13,760 are exactly the two classes: name-drift [AAVE_V3
      `position_data`/`liquidation_events`/`flash_loan_events` ×1063 each, MORPHO
      `risk_params`/`position_data`/`liquidation_events`/`lending_indices`, COMPOUND_V3] + never-collected/out-of-MVP
      [STAKEWISE/STADER `staking_yields`, STARGATE/ACROSS `bridge_events`, ALCHEMY `token_transfers`/`gas_fees`,
      ASTER/GMX `perp_funding` (GMX half MOOT — REMOVED 2026-07-25, see
      `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`; ASTER decision still open), FLASHBOTS `mev_events`,
      PYTH `oracle_prices`, AAVE `governance_events`]. Candidate CSV regenerated:
      `plans/audit/results/divergence_2026-06-22.csv` (filter classification=DIVERGENT_EMPTY). Stays a tracked campaign
      (per-venue backfill-vs-scope decision; operator HARD RULE = NO flat clip).**

      — the 2026-06-22 triage (divergence CSV + measured first-capture cross-ref) split the post-`coverage_start`
          residual into two REAL classes, all historical (≤2025-11-18, 0 in operational window): **(a) data_type
          NAME-DRIFT (~5–6k cells)** — AAVE_V3/MORPHO/COMPOUND_V3/FLUID lending: the oracle scope
          (`_DEFI_LENDING_*_PAIRS`) expects `liquidation_events`/`position_data`/`risk_params`/`flash_loan_events`/
          `lending_indices` but the manifest CAPTURED `liquidations`/`rate_indices`/`utilization` (legacy
          `liquidations_handler.py` still exists alongside `liquidation_events_handler.py`; MORPHO subgraph emits
          `rate_indices`/`utilization` not the AAVE-style names). The data EXISTS under a different data_type name →
          diagnose both sides + reconcile (either retire the legacy handler/data_type names → the canonical scope, or
          correct the oracle scope to the names the handlers actually emit). NOT a flat clip. **(b) NEVER-COLLECTED real
          gaps (~7k cells)** — venues with ZERO captured rows for ANY scoped data_type: STARGATE/ACROSS `bridge_events`,
          PYTH `oracle_prices`, FLASHBOTS `mev_events`, ASTER/GMX `perp_funding` (GMX half MOOT — REMOVED 2026-07-25,
          see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`; ASTER decision still open), FLUID lending, AAVE `governance_events`,
          ALCHEMY `token_transfers`, STAKEWISE/STADER/SWELL `staking_yields` — the adapter never ran a historical backfill,
          OR the data_type is out-of-MVP-archetype scope (bridge/mev/governance/flash-loan are NOT in the
          `carry_staked_basis`/`arbitrage_price_dispersion` data needs). Decision per venue: real-MVP-need → defi MTDS
          historical backfill (per-VM shards, canonical venue+chain, PER-CHAIN launch dates); out-of-MVP → move to
          `EMPTY_OR_DEPRECATED_DEFI_VENUES`/`DEFI_INSTRUMENTS_NOT_YET_COLLECTED` or trim the oracle scope. Candidate CSV:
          `plans/audit/results/divergence_2026-06-22.csv` (filter classification=DIVERGENT_EMPTY). —
          **unified-api-contracts, market-tick-data-service**

          **RE-VERIFIED AGAIN 2026-06-22 resume-run** (fresh `detect_manifest_divergence.py --asset-group defi` on live
          prod `_index`, 2,436,439 cells): **DIVERGENT_EMPTY = 13,760 EXACTLY (stable — auto-flip reclassifier holding it,
          not growing); max date 2025-11-18; ZERO in the operational window (≥2025-11-19) — all historical, NOT
          blocking.** Breakdown re-confirmed = the two classes (name-drift-suspect lending + never-collected/out-of-MVP).
          **Sub-finding (refines class-a):** the `dex_pool_swaps` DIVERGENT_EMPTY cells (UNISWAP_V3 350 / BALANCER 355 /
          CURVE 43) are NOT name-drift — `dex_pool_swaps` IS actively captured (4,392 OK_CAPTURED cells), so these are
          genuine date-specific historical swap gaps on those venues → resolve via per-venue historical DEX-swaps backfill
          (PER-CHAIN launch dates), not an oracle rename. Stays the tracked per-venue backfill-vs-scope campaign (operator
          HARD RULE: NO flat clip).

## Residual from per-AG hardening dispatch (DeFi agent)

- [ ] [CODE] P2. **DeFi evidence-fidelity (was folded into the DeFi P0)**: thread the ACTUAL subgraph/RPC HTTP status
      into the defi handlers' clean-path `record_zero_rows`/`record_empty(SOURCE_RETURNED_ZERO)` calls (vs the
      recorder's synthesized `clean_fetch_evidence`). Nicety — the danger-class is already closed (errors →
      `record_failed`). — market-tick-data-service. **SCOPED 2026-07-28 (slot-11) — NOT a bounded 1-hour change as
      written, stays unflipped here.** Live research found 25+ call sites across non-uniform fetch mechanisms (subgraph
      HTTP, Aave/Alchemy RPC multicall, on-chain Chainlink/Pyth calls, Solana RPC) where the real HTTP status is
      genuinely never in local scope at the manifest-recording call site — threading it through needs a per-fetch-family
      return-signature widen, not a find-and-replace. Also found the "danger-class already closed" framing does NOT hold
      for `governance_adapter.py` specifically: it swallows a real HTTP error into an empty list (a genuine C1
      correctness gap, higher priority than this fidelity nicety). Full scope + the recommended P1/P2 split:
      `/plans/archive/2026_08/issues/defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md`.

## Later-surfaced tradfi bug (2026-06-23 REAL OUTAGE triage)

- [x] ✅ [CODE] P1. **tradfi `ohlcv_15s` is a SPURIOUS aggregation tier — FIXED 2026-07-28
      (`market-data-processing-service@b2114d5`, slot-11).** `mdps-backfill-tradfi` spews CRITICAL
      `No SchemaContract registered for asset_group='tradfi' instrument_type='UNKNOWN' data_type='ohlcv_15s' venue='CME'`.
      Diagnosis (2026-06-23): tradfi OHLCV is `ohlcv_1s`/ `ohlcv_1m` (fetched) → aggregated to
      `ohlcv_15m`/`ohlcv_1h`/`ohlcv_24h`; a 15-**second** tradfi tier is NOT valid (`ohlcv_15s` appears only as a CeFi
      example). **Two-layer fix**: (1) `config.py`'s `_TIMEFRAME_CEILING_BY_ASSET_GROUP` already scoped tradfi to
      `{1m,5m,15m,1h,4h,1d}` (no 15s) as of `mdps@36e80cd` 2026-07-27, but (2) `orchestration_service.py` only called
      `resolve_timeframes()` when the caller's `timeframes` param was falsy
      (`timeframes or self.config.resolve_timeframes(category)`) — an EXPLICIT non-empty timeframes list (CLI
      `--timeframes` / the shared `MDPS_TIMEFRAMES` env-var bridge, which can inject the same 7-timeframe value
      uniformly across every asset_group launcher) bypassed the ceiling entirely, still emitting `ohlcv_15s` for tradfi.
      Fix: widened `resolve_timeframes(asset_group, requested=None)` to ALWAYS intersect its candidate list (explicit
      `requested` when given, else `default_timeframes`) against the ceiling — never bypassable — and updated all 3
      `orchestration_service.py` call sites to route through it unconditionally. No `ohlcv_15s` CONTRACT_REGISTRY entry
      added (would have masked the bug). 3 new regression tests (explicit-list-still-scoped, narrower-subset-honoured,
      no-ceiling-passthrough) + 1 test-fixture fix (a MagicMock config test that bypassed `resolve_timeframes()` before
      this fix, now exercises the real intersection path). QG green. (market-data-processing-service)

## Success criteria

- All open todos above ticked `- [x]` with evidence (commit sha / QG sentinel / deploy verification per PLAN_FORMAT.md §
  8b for any runtime-infra claim).
- The defi DIVERGENT_EMPTY campaign resolves per-venue (backfill OR documented out-of-MVP/name-drift reconciliation) —
  no flat clip, per the operator HARD RULE.
- `bash scripts/plan-hygiene/check_line_caps.sh` no longer flags this file, and
  `bash scripts/plan-hygiene/run_hygiene_sweep.sh` shows 0 hard failures across the 4-way split.

## Progress Log

- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; only change since = context-scout `context_scope`
  frontmatter, body byte-identical): KEEP-NA, valid — the defi DIVERGENT_EMPTY campaign carries an operator HARD RULE
  (no flat clip, per-venue decision) and the DeFi evidence-fidelity item was re-scoped 2026-07-28 as explicitly NOT
  bounded.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03 (full re-scout pass)**: refreshed context_scope (6 entries) -- added the
  honest-absence-downstream-handling SSOT + the two source files the tradfi-retry/defi-evidence-fidelity todos actually
  name (`wave_launcher.py`, `governance_adapter.py`).
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-02 (unchanged, 3 open todos): the tradfi
  attempted_failed retry (GENUINE_WORK, bounded) is real but small residual work; the defi DIVERGENT_EMPTY campaign
  still carries the operator HARD RULE (no flat clip, per-venue backfill-vs-scope decision — GENUINE_WORK, judgment-
  laden); the DeFi evidence-fidelity item's 2026-07-28 re-scoping (25+ non-uniform call sites, a per-fetch-family
  return-signature widen, NOT a bounded 1-hour change) still holds on a fresh read — no new evidence changes any of the
  three verdicts.
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (6 entries) -- intervening commits (archival
  of `data_pipeline_hardening_self_monitoring`, a P0 checkbox flip) already resolve correctly via this doc's existing
  archive-path entry; `wave_launcher.py` + `governance_adapter.py` remain the correct source targets for the 2
  still-open tradfi-retry/defi-evidence-fidelity todos.
- **na-eligibility-audit 2026-08-17** [body-hash:45aa0e33b58fdbda]: KEEP-NA, valid -- 3 open items, each already independently reaffirmed KEEP-NA by 2 prior audit passes (2026-08-02, 2026-08-07) with matching reasoning I independently confirm on a fresh read: (1) the tradfi attempted_failed retry is small but genuine data-engineering work; (2) the defi DIVERGENT_EMPTY campaign explicitly carries an operator HARD RULE ('no flat clip... every venue/data_type gets a per-pair backfill-vs-scope decision') spanning many venues with distinct name-drift vs never-collected classifications -- textbook per-item judgment, not a single bounded outcome; (3) the DeFi evidence-fidelity item's own 2026-07-28 re-scoping note explicitly states it is 'NOT a bounded 1-hour change as written' (25+ non-uniform call sites needing a per-fetch-family return-signature widen). No new evidence since the last audit changes any of the three verdicts.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **context-scout 2026-08-17**: re-verified context_scope, no change needed (6 entries).
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche): KEEP-NA, valid — reaffirms 2026-08-17 (unchanged, 3 open items, each independently reaffirmed KEEP-NA across 3 prior audit passes): tradfi attempted_failed retry (small genuine data-engineering work), the defi DIVERGENT_EMPTY campaign (explicit operator HARD RULE — no flat clip, per-venue decision), and the DeFi evidence-fidelity item (explicitly re-scoped 2026-07-28 as NOT a bounded change — 25+ non-uniform call sites needing a per-fetch-family return-signature widen).
