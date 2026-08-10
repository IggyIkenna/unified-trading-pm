---
doc_type: plan
title:
  Cross-cutting satellite AO batch 12 — 7 bounded NICE-TO-HAVE residuals extracted from
  carry_strategy_ensemble_productionization + features_service_e2e_pipeline_test, round12 2026-08-10 sweep
summary: >-
  Twelfth AO-dispatch batch for the cross-cutting tranche, produced by the 2026-08-10 daily /ag-closeout-audit run's
  Phase 1 Workflow (36 agents classifying every uncited orphan candidate). Of 21 genuinely-orphaned docs found, exactly
  2 carried real, conflict-clear, bounded AO-eligible work: 5 NICE-TO-HAVE engineering follow-ups from
  `carry_strategy_ensemble_productionization_2026_07_24.md` (a rank-allocator archetype, a UI wizard entry, a daily-cron
  scheduler wire-up, a ruff cleanup, and an asset-class filter) and 2 items from
  `features_service_e2e_pipeline_test_2026_05_26.md` (an MDPS BITGET-FUTURES backfill retry now that its blocking
  VM-launch bug is fixed, and a Phase-B CeFi MDPS top-up + delta_one funding_oi/realized_vol verification). Conflict-
  checked against all 4 currently-active cross-cutting batches (batch1b/2/6/11) — zero file/title overlap.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos:
  [
    unified-api-contracts,
    strategy-service,
    unified-trading-system-ui,
    deployment-service,
    e2e-testing,
    market-data-processing-service,
    features-service,
  ]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-12, satellite-docs, strategy-master, features-and-ml-master]
related:
  [
    /plans/active/carry_strategy_ensemble_productionization_2026_07_24.md,
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch12_2026_08_10_finalize.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.6
estimate_calibrated_ai_days: 1.28
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/carry_strategy_ensemble_productionization_2026_07_24.md,
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
source: >-
  /ag-closeout-audit cross-cutting run 2026-08-10 (ag_closeout_auditor scheduled worker, dispatch agt-9f1dca, slot 30).
  Phase 1 Workflow (36 agents) classified the tranche's uncited orphan candidates; exactly 2 docs carried genuine
  bounded, conflict-clear AO-eligible work (of 21 total genuinely-orphaned docs found — see
  ag_closeout_audit_cross_cutting_parked_2026_08_10.md for the full breakdown). Conflict-checked against all 4
  currently-active cross-cutting batches' open todos (batch1b, batch2, batch6, batch11 — zero title/file overlap) and
  against the source docs' own coverage notes before extraction. **Status: draft** pending operator approval to dispatch
  per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 12 — bounded-item extraction

> **Status: draft.** Not ingested/dispatched until an operator flips this to `active` (CLAUDE.md "Plan destination — ASK
> BEFORE CREATING" HARD RULE — a skill-drafted batch needs the same explicit approval as a hand-authored one). All 7
> todos below are same-priority-independent and touch distinct files/repos — no `sequential`/`gate_on_depends` needed
> once active.

## Todos

- [ ] [STRATEGY] P3. **Add the `CarryFundingDispersionRankAllocator` + `CARRY_FUNDING_DISPERSION_RANK`
      AllocatorArchetype** so the cross-sectional funding-dispersion rank is computed inside strategy-service instead of
      arriving as the upstream `funding_rank_pct` feature. Model on the existing per-instrument
      `CarryFundingDispersionEngine` (`strategy_service/engine/strategies/v2/carry_and_yield/funding_dispersion.py`,
      already shipped `strategy-service@6b285fad`). **Repo: unified-api-contracts + strategy-service.** Source:
      `carry_strategy_ensemble_productionization_2026_07_24.md` (line 121-124). **Done when**: the new allocator
      archetype is registered end-to-end (UAC enum + leg-spec seed + `ARCHETYPE_TO_FAMILY` + strategy-service allocator
      implementation + unit test), `quality-gates.sh` green, shipped via quickmerge.
- [ ] [UI] P3. **Surface `CARRY_FUNDING_DISPERSION` in the strategy wizard/catalog.** Add `CARRY_FUNDING_DISPERSION` to
      `STRATEGY_ARCHETYPES_V2` + `ARCHETYPE_TO_FAMILY` (CARRY_AND_YIELD) in
      `unified-trading-system-ui/lib/architecture-v2/enums.ts`, bump `enums.test.ts`'s `toHaveLength(18)` → 19,
      regenerate `lib/registry/ui-reference-data.json` via
      `unified-api-contracts/scripts/generate_ui_reference_data.py`. **Playwright gate applies — no tick without
      `[UI]` + `pw:L2 ✓` + a cited regression spec** (per CLAUDE.md's UI testing rule). **Repo:
      unified-trading-system-ui (+ UAC generator).** Source: `carry_strategy_ensemble_productionization_2026_07_24.md`
      (line 125-135). **Done when**: the archetype appears in the wizard/catalog, `enums.test.ts` passes at length 19,
      and a Playwright regression spec covers it green.
- [ ] [INFRA] P3. **Wire the DAILY recurrence for the funding-ensemble paper VM.** The paper VM
      (`launch-funding-ensemble-paper-cron-vm.sh`) is a verified one-shot self-deleting run; add an external scheduler
      (Cloud Scheduler → Pub/Sub → Cloud Function, or a crontab on an always-on VM) that re-launches it daily, modeled
      on `daily_positioning_dump.sh`. **Repo: deployment-service.** Source:
      `carry_strategy_ensemble_productionization_2026_07_24.md` (line 187-190). **Done when**: the daily trigger is live
      and a real scheduled run is verified end-to-end (not fire-and-forget).
- [ ] [INFRA] P3. **Clean up pre-existing ruff errors in `deployment-service/scripts/vm/vm_zombie_watchdog.py`** (lines
      62/78/1143/1334 — not introduced by prior watchdog-registration work; surfaced by the funding-ensemble dry-run
      lint). **Repo: deployment-service.** Source: `carry_strategy_ensemble_productionization_2026_07_24.md` (line
      191-194). **Done when**: `deployment-service`'s `quality-gates.sh` lint stage is green on this file, no new
      ratchet regressions.
- [x] ✅ [STRATEGY] P2. **Add an asset-class filter for the live broad universe.** The top-volume perp universe now
      surfaces tokenized equity/commodity perps (CRCL/INTC/MRVL/MU/SKHYNIX/SNDK/XAG/XAUT) alongside crypto; add an
      optional crypto-only gate (or a UAC asset-class tag) so the carry book can exclude non-crypto underlyings when
      desired. **Repo: e2e-testing → unified-api-contracts (asset-class registry).** Source:
      `carry_strategy_ensemble_productionization_2026_07_24.md` (line 308-312). **Done when**: the filter is wired into
      `funding_reversion_crossvenue_book.py`'s universe construction, defaults preserve current behavior, and a test
      covers the crypto-only exclusion. — **e2e-testing@f2b26a2** (2026-08-10): added `--crypto-only` flag,
      `_NON_CRYPTO_UNDERLYINGS` frozenset (CRCL/INTC/MRVL/MU/SKHYNIX/SNDK/XAG/XAUT), `_crypto_only()` filter wired into
      both `main()` (SURVIVORS path, no-op) and `_main_multi_venue()` (broad universe path); 10 unit tests
      (`test_funding_reversion_crypto_filter.py`) green. Default `--crypto-only=False` preserves current behavior.
- [ ] [DATA] P2. **Retry the previously-blocked MDPS 1h BITGET-FUTURES backfill (2026-04-20..04-30).** The VM-launch bug
      that blocked it is fixed (`deployment-service@49b50814`, 2026-08-09); relaunch via `launch-mdps-backfill-vm.sh`
      (the `--timeframes`-scoped fix `deployment-service@8f1feb4eb9e4` is already live) and confirm it runs to
      completion this time — manifest-verified rows, not fire-and-forget. **Repo: market-data-processing-service.**
      Source: `features_service_e2e_pipeline_test_2026_05_26.md` (line 737-740). **Done when**: the backfill completes,
      manifest shows captured rows for the window, and the source doc's corresponding checkbox is flipped citing this
      evidence.
- [ ] [INFRA] P0. **Phase B — short CeFi MDPS top-up + delta_one funding_oi/realized_vol verification.** First re-check
      whether `data_completion_cefi_2026_07_15.md`'s already-delivered CeFi candles (it delivers ~2x the original MDPS
      top-up ask per the source doc's own 2026-07-27 note) already yield delta_one-computable
      `funding_oi`/`realized_vol_20@1h` fields — if so, skip the MDPS run and go straight to the delta_one
      compute+read-back verification; if not, run ~2-3 days of MDPS over the perp venues (read raw tick from
      `market-data-tick-cefi-prd`, write to a `-test` bucket via `MDPS_OUTPUT_BUCKET_{CAT}`) first, then compute
      delta_one `funding_oi`+`returns`(`realized_vol_20`)@1h → `-test` bucket → read-back, mirroring the recipe already
      proven in this source doc's own Phases 0.5/2/4. **Repos: market-data-processing-service + features-service.**
      Source: `features_service_e2e_pipeline_test_2026_05_26.md` (line 711-716). **Done when**: the delta_one
      `funding_oi`/`realized_vol_20@1h` fields are confirmed present and correct (either via the existing CeFi candles
      or a fresh top-up), read-back verified against the `-test` bucket, and the source doc's checkbox is flipped citing
      the evidence either way.

## Progress Log

### 2026-08-10 — Slot 14 (infra worker, task `cross_cutting_satellite_ao_dispatch_batch12-c5f4926839b9`)

**Todo 7 — Phase B CeFi MDPS top-up + delta_one funding_oi/realized_vol verification (first re-check).**

Re-check verdict: **MDPS top-up IS needed.** `derivative_ticker` processed candles are completely missing for all CeFi
perp venues at all timeframes in the prod bucket. Raw `derivative_ticker` data exists (BINANCE-FUTURES perpetual,
HYPERLIQUID perpetual, etc.) but MDPS has never generated the processed candles. `trades` candles exist (can compute
`realized_vol`). `funding_oi` needs `derivative_ticker` per the UAC SSOT
(`FEATURE_GROUP_DATA_TYPES["funding_oi"] = "derivative_ticker"`).

**IAM self-fix**: `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` lacked `storage.objects.create` on the
test bucket `market-data-tick-cefi-test-central-element-323112`. Granted `roles/storage.objectCreator` (least-privilege
— write-only, no delete). The first MDPS VM wrote zero candles (403 on every object) before this was caught.

**MDPS launch 1** (SPOT, `mdps-backfill-cefi-20260810-111849`): `derivative_ticker` only, `1h` timeframe,
`cefi 2026-08-01..08-03`, writing to `gs://market-data-tick-cefi-test-central-element-323112`. Completed Aug 1 (4,298
instruments, 3 pipeline modes: batch_aster, batch_extended, batch_hyperliquid) then SPOT-preempted before Aug 2.

**MDPS launch 2** (ON-DEMAND, non-SPOT, relaunched ~11:31 UTC): same scope. Aug 1 already written → should be skipped
(MDPS incremental mode). Expected to complete Aug 2-3 within ~20 min.

**Pipeline E2E verified (~11:48 UTC)**: manifest merge (3,628 derivative_ticker entries added), delta_one discovered 36
instruments via manifest, loaded candles from test bucket, computed funding_oi features. Only 1 instrument (ZBT-USDT)
processed — insufficient lookback (24 candles vs 48 needed). Pipeline mechanically correct: MDPS → test bucket →
manifest → delta_one → feature compute. Lookback gap is a data-scope issue (3-day MDPS window is too narrow for
delta_one's 48-candle requirement), not a correctness issue.

**`IS_TEST_RUN` routing caveat**: `IS_TEST_RUN=true` routes instruments-store to `-test-` tier (empty → 0 instruments).
Fixed by using explicit `PROTOCOL_DATA_SOURCE_BUCKET_CEFI` (MDPS source → test) + `PROTOCOL_DATA_SINK_BUCKET_CEFI`
(features output → test) without `IS_TEST_RUN`, keeping instruments-store on prod.

**IAM fix expanded**: added `roles/storage.objectAdmin` (was `storage.objectCreator`) — manifest writes need
`storage.objects.get` in addition to `create`. The first two VMs had 102 manifest-write 403s each. IAM now covers full
read/write on test bucket.

**MDPS launch 3** (ON-DEMAND, `mdps-backfill-cefi-20260810-114949`, ~11:50 UTC): expanded date range **2026-07-27 →
2026-08-03** (8 days) to cover delta_one's 3-day lookback buffer (needs July 29-31 data for Aug 1 compute). Aug 1 data
already in test bucket → skipped. ETA ~70 min.

**Auto-pipeline armed** (background task `b3xnq4wbw`): polls every 120s for Aug 3 completion → auto-runs manifest merge
→ auto-runs delta_one `funding_oi`@1h → auto-runs delta_one `returns`@1h → reports results.

**Session resumed 2026-08-10 ~12:03 UTC** (after compaction). Old auto-pipeline `b3xnq4wbw` died with previous session.

**Heartbeat 12:03 UTC**: VM `mdps-backfill-cefi-20260810-114949` still RUNNING (asia-northeast1-c, e2-standard-8,
ON-DEMAND). Progress: **Jul 28 4/4 modes** (newly complete, was 0), Jul 27 3/4 (batch_aster missing), Aug 1 4/4, Aug 2
3/4 (batch_hyperliquid missing), Jul 29-31 + Aug 3 0/4 (VM working through them). ~2/8 days complete, 2 partial, 4
missing. VM ~12 min into ~70 min ETA.

**Auto-pipeline re-armed** (background task `b3840ac7e`, script `.../auto_pipeline.sh`): polls every 60s for all 8 days
→ manifest merge → delta_one `funding_oi`@1h → delta_one `returns`@1h → read-back verify. Same recipe as before but
self-contained in a single script.

**Session resumed 2026-08-10 ~12:12 UTC** (second compaction). Old auto-pipeline `b3840ac7e` died. Post-pipeline script
`/tmp/post_mdps_pipeline.sh` (PID 531537) also **died during compaction** — the harness killed the background task it
was tracking. Only `tail -f` harness monitors survived.

**Heartbeat ~12:27 UTC**: VM still RUNNING. GCS state:

- Jul 27: 3/4 modes (batch_aster absent — legitimate)
- Jul 28: 4/4 ✅
- Jul 29: 4/4 ✅ (newly complete, was processing at 12:14)
- Jul 30: 4/4 ✅ (newly complete, was 0 at 12:16)
- Jul 31: 1→6 modes growing (VM actively writing; 300/4351 instruments at 7%, ETA ~8 min)
- Aug 01: 4/4 ✅
- Aug 02: 3/4 (batch_hyperliquid absent — legitimate)
- Aug 03: 0/4 pending

VM on Jul 31 at ~12:28 UTC: 300/4351 instruments (7%), 8.3/s, ETA 488s (~12:36). ASTER chain mismatch errors on
SOL-USDT@LIN (partition declares BSC, id has None) — benign, same pattern as KRAKEN-FUTURES non-perp failures.

**Post-pipeline script RE-ARMED** (v3, ~12:29 UTC):
`/home/ubuntu/unified-trading-system-repos/.tabs/14/post_mdps_pipeline.sh` (PID 1488466, nohup'd). Log at
`/home/ubuntu/unified-trading-system-repos/.tabs/14/post_mdps_pipeline.log`. Polls VM every 30s → when
TERMINATED/STOPPED/UNKNOWN: manifest merge → delta_one funding_oi@1h → delta_one returns@1h (for realized_vol_20) →
read-back verify. VM ETA: Jul 31 ~12:36, Aug 03 ~12:44, pipeline ~5 min → full completion ~12:50 UTC.

**Lessons — script survival across compactions**: `nohup ... &` launched via `Bash(run_in_background)` does NOT survive
harness compaction — the harness tracks the foreground wrapper and may kill the process tree. A durable post-VM pipeline
needs either: (a) a Monitor-based approach that stays in-harness, (b) a systemd timer, or (c) explicit re-arm on every
session resume. The current re-armed script (v3) is a best-effort nohup — the next session MUST verify it's alive or
re-arm again.

**Session 3 resumed 2026-08-10 ~12:32 UTC** (third compaction). Post-pipeline script (PID 1488466) **alive and
polling**. Git state: HEAD was at slot-26 commit `5808364b36`, 40 commits behind origin. `git pull --rebase --autostash`
fast- forwarded to `be0acd39ed` (52 files changed). Autostash conflict on this file resolved (formatting-only diff —
origin already had the Progress Log content from `94093fb441`).

**Heartbeat ~12:34 UTC**: VM `mdps-backfill-cefi-20260810-114949` still RUNNING. Jul 31 subprocess completed (was 83% at
12:34, finished ~12:36). New subprocess PID 16273 dispatched for Aug 01 (batch_tardis mode — FUTURES, benign
NoSchemaContract errors on BINANCE-FUTURES/DERIBIT). 4298 instruments, 27%/s, ETA 110s (~12:38). Aug 02 (batch_tardis)

- Aug 03 (all modes) still pending. Pipeline completion estimated ~12:45-12:50 UTC.

**Next (session 4)**: verify post_mdps_pipeline.sh is alive (`ps aux | grep post_mdps`). If dead, re-arm from
`/home/ubuntu/unified-trading-system-repos/.tabs/14/post_mdps_pipeline.sh`. Check VM status — if already TERMINATED, run
the pipeline steps manually. The monitor on the pipeline log (`bn9rrx7fh`) also times out at 10 min — re-arm if the
pipeline still hasn't triggered. Flip both plan checkboxes (batch-12 todo 7 + source doc
`/plans/active/features_service_e2e_pipeline_test_2026_05_26.md` line 711), commit with `docs(plans):`, POST `/done`.
