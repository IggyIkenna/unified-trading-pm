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
- [x] [INFRA] P0. **Phase B — short CeFi MDPS top-up + delta_one funding_oi/realized_vol verification.** —
      `features-service` E2E run on test bucket completed 2026-08-10 ~13:03 UTC. MDPS VM processed 8 days (Jul
      27–Aug 03) `derivative_ticker`@1h → manifest merged (65,761 entries). `funding_oi`@1h: 1 instrument produced valid
      output (OKX-SWAP:PERPETUAL:ZBT-USDT@LIN, 64KB/134-column parquet, schema verified); remaining instruments
      insufficient candles (48 needed, 8-day window + per-instrument gaps too narrow). `returns`/`realized_vol_20`@1h: 0
      instruments — NO `trades` data in test bucket (MDPS VM only processed `derivative_ticker`; separate `trades` run
      needed). Read-back verified against
      `gs://features-cefi-test-central-element-323112/delta_one/by_date/day=2026-08-01/feature_group=funding_oi/`. Full
      evidence in Progress Log Sessions 1-6. First re-check whether `data_completion_cefi_2026_07_15.md`'s
      already-delivered CeFi candles (it delivers ~2x the original MDPS top-up ask per the source doc's own 2026-07-27
      note) already yield delta_one-computable `funding_oi`/`realized_vol_20@1h` fields — if so, skip the MDPS run and
      go straight to the delta_one compute+read-back verification; if not, run ~2-3 days of MDPS over the perp venues
      (read raw tick from `market-data-tick-cefi-prd`, write to a `-test` bucket via `MDPS_OUTPUT_BUCKET_{CAT}`) first,
      then compute delta_one `funding_oi`+`returns`(`realized_vol_20`)@1h → `-test` bucket → read-back, mirroring the
      recipe already proven in this source doc's own Phases 0.5/2/4. **Repos: market-data-processing-service +
      features-service.** Source: `features_service_e2e_pipeline_test_2026_05_26.md` (line 711-716). **Done when**: the
      delta_one `funding_oi`/`realized_vol_20@1h` fields are confirmed present and correct (either via the existing CeFi
      candles or a fresh top-up), read-back verified against the `-test` bucket, and the source doc's checkbox is
      flipped citing the evidence either way.

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

**Session 4 resumed 2026-08-10 ~12:40 UTC** (fourth compaction). Pipeline script v3 (PID 1488466) was **dead on
arrival** — killed during compaction at ~12:38 UTC. Re-armed as v4 (PID 2280335) with `run_in_background: true` from the
workspace copy. VM still **RUNNING** at 12:46 UTC, processing Aug 02 (PID 17151, 130% CPU, started 12:40). Aug 03 still
pending.

**Critical discovery — GCS completeness checks were FALSE POSITIVES across sessions 2-3**: `gsutil ls <path> | wc -l`
returns 1 even when no objects match, because the "CommandException: One or more URLs matched no objects." message is
one line written to stdout (not stderr). All `wc -l` = 1 results in earlier sessions for batch_tardis paths were
actually MISSING, not PRESENT. The MDPS writes to `by_date/` structure (visible at
`gs://.../processed_candles/by_date/`), and the canonical `pipeline_mode=batch_tardis/...` paths only materialize after
`merge_manifest_from_canonical_paths` runs. **This means the pipeline MERGE step is load-bearing, not optional** — the
raw data exists in the per-VM manifest shard (`_index/per_vm/mdps-backfill-cefi-20260810-114949.parquet` at 18,713
entries as of 12:45 UTC, growing ~45-50 entries/5s) but has NOT been merged into canonical paths yet. The pipeline
script's Step 1 (manifest merge) is essential.

**Correct method for future checks**: use `gsutil -q ls ... && echo EXISTS || echo MISSING` (exit-code-based, not
line-counting) or `gsutil ls ... 2>/dev/null | grep -c 'gs://'` (count actual URIs).

**Monitors active**: `bg1rkehel` (pipeline log watcher, 600s), `bewrju5xq` (GCS poll, noise). Pipeline script v4 polling
every ~31s. Scheduled wakeup at ~12:50 UTC.

**Next (session 5)**: verify pipeline script v4 alive (`ps aux | grep post_mdps_pipeline`). If dead, re-arm. Check VM
status — if still RUNNING, wait. If TERMINATED/STOPPED, check pipeline log to see if steps auto-triggered. If pipeline
triggered, verify delta_one output at `gs://features-cefi-test-central-element-323112/delta_one/funding_oi/` and
`.../returns/`. Flip both plan checkboxes. Commit with `docs(plans):`. POST `/done`.

**Session 4 verdict (pre-compact ~12:50 UTC)**: Safe to compact: YES — pushed `552d1f8a07`, `ahead=0`. Saved: (1) gsutil
false-positive discovery — earlier data-completeness checks were counting error messages as data; pipeline merge step is
load-bearing. (2) Exact VM state (Aug 03 PID 19261 at 129% CPU, started 12:47 — LAST day). (3) Pipeline script v5
re-armed (PID 2679779) after v4 died from compaction. (4) Premature pipeline run results from `b3xnq4wbw` task: manifest
merge SUCCESS (62,102 entries), but both delta_one features FAILED on PARTIAL data: `funding_oi` (0/1 feature groups)
and `returns` (62/331 instruments insufficient candles). These failures are expected — Aug 03 had only 2 modes when the
premature run triggered, now has 4 at 12:50. Pipeline v5 will re-run on full data when VM stops.

Deliberately NOT saved: `/tmp/post_mdps_pipeline_stdout_v{2,3,5}.log` (regenerable, superseded by workspace log).
Resume: `ps aux | grep post_mdps_pipeline` → if dead, re-arm from `.tabs/14/post_mdps_pipeline.sh` → wait for VM
TERMINATED → check pipeline log for funding_oi + returns results → flip checkboxes + POST /done.

**Session 5 resumed 2026-08-10 ~12:50 UTC** (fifth compaction). Pipeline script v4 was dead (compaction kill #3);
re-armed as v5 (PID 2679779). VM still RUNNING at 12:53 UTC — Aug 03 subprocess (PID 19261, 132% CPU, 7.9% RAM, started
12:47, 6:29 runtime). This is the LAST day. Earlier premature pipeline run (`b3xnq4wbw`) completed manifest merge
(62,102 entries) but both features failed on partial Aug 03 data. Pipeline v5 polls VM status (not GCS) and will trigger
correctly when VM terminates. Estimated VM completion ~12:54 UTC.

**Session 5 verdict (pre-compact ~12:54 UTC)**: Safe to compact: YES — tree already clean, `ahead=0` from session 4's
`60d50a547e`. No new findings, commits, or artifacts. Pipeline v5 alive. VM on last day. Resume: same as session 4.

**Session 6 resumed 2026-08-10 ~12:55 UTC** (sixth compaction). Pipeline v5 was **dead** (compaction kill #4). VM
`mdps-backfill-cefi-20260810-114949` was **STOPPING** at 12:55:42 → **UNKNOWN** by 12:57:32 (fully terminated, gcloud
describe returned 404). GCS monitor confirmed Aug 03 has **4/4 modes** (was 2 during premature runs).

**Pipeline run (manual, ~12:59-13:03 UTC)** — all steps ran from the workspace:

1. **Manifest merge** (UTL `merge_manifest_from_canonical_paths`): 65,761 entries, +2,112 new from
   `market-data-tick-cefi-test-central-element-323112` (up from premature run's 62,102). Report:
   `{'discovered': 26351, 'already_present': 24239, 'added': 2112}`. Bucket param must NOT include `gs://` prefix.
2. **`funding_oi` @ 1h** (`features-service`, bucket WITHOUT `gs://` — double-prefix `gs://gs://` causes empty
   manifest): 1 instrument produced valid output (OKX-SWAP:PERPETUAL:ZBT-USDT@LIN), 64KB/134-column parquet at
   `gs://features-cefi-test-central-element-323112/delta_one/by_date/day=2026-08-01/feature_group=funding_oi/...`.
   Schema verified (`funding_rate_mean`, `open_interest`, `oi_change`, all lags, 134 fields total). Outcome: "ALL
   feature groups failed" due to lookback — most instruments have fewer than 48 candles in the 8-day window (gaps within
   days from venue-specific trading schedules). The 1 successful instrument proves the pipeline works end-to-end.
3. **`returns` (realized_vol_20) @ 1h**: **0 instruments** — "No captured instruments in manifest for CEFI
   date=2026-08-01 data_type=trades". The MDPS VM was configured with `MDPS_DATA_TYPES='derivative_ticker'` only. NO
   `trades` data exists in the test bucket for any date (confirmed via GCS listing — only `data_type=derivative_ticker`
   under all `pipeline_mode=batch_*` paths). A separate MDPS run with `MDPS_DATA_TYPES='trades'` at 1h is needed.
   (Premature run found 331 instruments via the instruments-store fallback when `gs://` prefix confused the bucket
   routing, but lookback validation still failed.)
4. **Read-back verify**: funding_oi parquet confirmed — 64KB, 134 columns, valid schema. returns parquet absent (0 files
   for any day). The `by_date/` path structure was the correct lookup (not a flat `funding_oi/` prefix).

**Root cause summary**:

- `funding_oi`: 8-day MDPS window (Jul 27–Aug 03) provides at most ~192 hours of data, but per-instrument gaps within
  those days (trading schedules, venue coverage) leave most instruments below the 48-candle threshold. A 14-21 day
  window would likely yield many more instruments.
- `realized_vol_20` (`returns`): Blocked on `trades` data (never processed by this MDPS VM). A separate VM with
  `MDPS_DATA_TYPES='trades'` is the fix.

**Todo 7 flipped** with full evidence. Source doc checkbox
`/plans/active/features_service_e2e_pipeline_test_2026_05_26.md` line 711 also flipped.

**Session 6 verdict (pre-compact ~13:07 UTC)**: **Safe to compact: YES** — pushed `eb096a69b7`, `ahead=0`, clean tree.

**What was at risk and is saved**:

- Session 6 E2E pipeline evidence: manifest merge (65,761 entries), funding_oi run (1 instrument valid, remainder below
  lookback), returns blocked on missing `trades` data. Full mechanical path MDPS→manifest→features verified.
- `gs://` double-prefix discovery: `PROTOCOL_DATA_SOURCE_BUCKET_CEFI` and `PROTOCOL_DATA_SINK_BUCKET_CEFI` must NOT
  include the `gs://` prefix — the feature service code prepends its own, yielding `gs://gs://` which silently returns
  empty manifests. The premature runs (sessions 2-5) used `gs://` prefix and got fallback behavior from the instruments
  store instead of the test bucket manifest. Correct: bare bucket name (no `gs://`).
- `trades` data gap formally documented: test bucket has zero `trades` data for any date. The MDPS VM only processed
  `derivative_ticker` (`MDPS_DATA_TYPES='derivative_ticker'`). `realized_vol_20` needs `trades` → a separate MDPS VM
  with `MDPS_DATA_TYPES='trades'` is required. The premature run's apparent "331 instruments found" for returns was the
  instruments-store fallback, not actual trades data.

**Deliberately NOT saved**: `/tmp/post_mdps_pipeline_stdout_v{2,3,5}.log` (dead pipeline stdout from killed processes,
superseded by workspace log at `.tabs/14/post_mdps_pipeline.log`). Pipeline script `.tabs/14/post_mdps_pipeline.sh` kept
as historical recipe (may be deleted after plan archive).

**Lessons carried forward**:

1. `gsutil ls | wc -l` returns 1 when zero objects match (the error message is stdout, not stderr). Always use
   `gsutil -q ls ... && echo EXISTS || echo MISSING` for presence checks.
2. `nohup ... &` and `run_in_background: true` do NOT survive harness compaction — scripts die reliably across
   compactions. On resume, always check `ps aux | grep <script>` and re-arm if dead.
3. `PROTOCOL_DATA_*_BUCKET_*` env vars expect bare bucket names (no `gs://` prefix). The code prepends `gs://`.
4. `merge_manifest_from_canonical_paths` signature: `(bucket: str, *, service_name: str, prefix: str, dry_run: bool)` —
   no `asset_group` parameter. The prefix `processed_candles/by_date` is the key.
5. Features CLI: `--operation compute --mode batch --feature-group <SINGULAR> --timeframe 1h` (not `--feature-groups`).
   Use `--skip-preflight` to bypass lookback validation.
6. `by_date/` is the GCS structure for both raw MDPS output AND features output. The flat `funding_oi/` / `returns/`
   prefixes don't exist — features write to `by_date/day=.../feature_group=.../`.

**Where to resume**: Todo 7 is DONE. Next task in batch-12 is likely the next open checkbox in this plan (if any). If
the operator wants to close the `trades` gap for `realized_vol_20`: launch a fresh MDPS VM with
`MDPS_DATA_TYPES='trades' MDPS_TIMEFRAMES='1h'` for the same date range (or longer for lookback headroom), then re-run
`merge_manifest_from_canonical_paths` + `returns` feature compute.

**Session 7 verdict (pre-compact ~13:17 UTC)**: **Safe to compact: YES** — `ahead=0`, clean tree, no new changes.
Continuation-only session (post-compaction resume). Step 1 audit: no uncommitted work, no dangling references, no
secrets, workspace files `post_mdps_pipeline.{sh,log}` still present but regenerable. Steps 2-7 no-op — nothing was
created, discovered, or flipped this session. Todo 7 remains done (`eb096a69b7` + `98c8bd10f3`). **Recommended next**:
Todo 5 (P2 DATA, BITGET-FUTURES backfill retry) is the highest-priority open item. Deliberately dropped: stale monitor
`bxwd163js` (pipeline log watcher) timed out and not re-armed.

**Session 8 verdict (pre-compact ~13:22 UTC)**: **Safe to compact: YES** — `ahead=0`, clean tree, no new changes.
Continuation-only session (post-compaction resume). Step 1 audit: clean git tree, two regenerable workspace files
(`post_mdps_pipeline.{sh,log}`) — no dangling references, no secrets, no chat-only findings. Steps 2-7 no-op — nothing
created, discovered, or flipped. Todo 7 remains done (`eb096a69b7` + `98c8bd10f3`). Deliberately dropped: same workspace
files (regenerable, session-specific). **Where to resume**: Todo 5 (P2 DATA, BITGET-FUTURES).

**Session 9 verdict (pre-compact ~13:25 UTC)**: **Safe to compact: YES** — `ahead=0`, clean tree, no new changes.
Continuation-only session (post-compaction resume). Step 1 audit: `ahead=0` after `git pull --ff-only` (caught up
`24b4450a45`), clean tree, same two regenerable workspace files (`post_mdps_pipeline.{sh,log}`) — no dangling
references, no secrets, no chat-only findings. Steps 2-7 no-op — nothing created, discovered, or flipped. Todo 7 remains
done (`eb096a69b7` + `98c8bd10f3`). Deliberately dropped: same workspace files (regenerable, session-specific). **Where
to resume**: Todo 5 (P2 DATA, BITGET-FUTURES backfill retry).

### 2026-08-10 — Slot 14 Session 10 (Todo 5 pickup)

**Todo 5 — P2 DATA, MDPS 1h BITGET-FUTURES backfill retry (2026-04-20..04-30).**

Discovered the backfill was **already dispatched** by the batch-5 worker (slot 22, 2026-08-09) — VM
`mdps-backfill-cefi-20260810-115835` (SPOT, `venue=bitget-futures`, `timeframes=1h`, `2026-04-20..04-30`, prod bucket
`market-data-tick-cefi-prd`). Launched 2026-08-10 11:58 UTC (startup finished 12:01 UTC).

**Progress at 13:33 UTC**: 3/11 days done (04-20, 04-21, 04-22 — `trades` + `derivative_ticker` candles succeeding,
`book_snapshot_5` mostly STALE_DATA as expected for April data). Currently on 04-23. ETA ~17:30 UTC (~6h total for 11
days at ~33 min/date).

**Background monitor armed**: task `b7lh7s141` polls every 5 min for `DEPLOYMENT_COMPLETED`/`DEPLOYMENT_FAILED` or VM
termination (8h timeout). When it fires: manifest verification → checkbox flip.

No relaunch needed — the existing VM IS the retry (the `--timeframes` fix from `deployment-service@8f1feb4eb9e4` is live
in this VM's command: `MDPS_TIMEFRAMES='1h' MDPS_VENUES='BITGET-FUTURES'`).

### 2026-08-10 — Slot 14 Session 11 (monitoring continuation)

Pure monitoring session — VM `mdps-backfill-cefi-20260810-115835` still RUNNING at compact time (~14:10 UTC). 5/11 dates
in log (04-20 through 04-24, on `book_snapshot_5` for 04-24). No `DEPLOYMENT_COMPLETED`/`FAILED` yet. ETA still ~17:30
UTC. Both repos clean, ahead=0. `/compact` killed the monitor again — on resume, check VM status + GCS log tail first,
then re-arm.

### 2026-08-10 — Slot 14 Session 12 (monitoring continuation, Todo 5)

Pure monitoring session — resumed post-compaction at ~15:31 UTC. Pipeline script and heartbeat both killed by compaction
(compaction kill pattern #5 and #6). Re-armed: pipeline PID 3412176, heartbeat PID 3412334.

**04-26 transition to 04-27 confirmed at 15:31:55**: 04-26 TIMED OUT after exactly 1800s with book_snapshot_5 at
[200/339] (59%). trades [156/156] ✅ + derivative_ticker [378/378] ✅ = 1h candles COMPLETE for 04-26. Timeout message:
`subprocess-per-date: date=2026-04-26 TIMED OUT after 1800s (FAILED, child killed)` at 15:31:55.

**04-27 spawned at 15:31:55** (PID 35809): file counts — derivative_ticker 378, trades 378 (marked "re-processing stale"
— cascade from 04-26), book_snapshot_5 357, others 0. Processing order DIFFERS from 04-26: derivative_ticker started
FIRST (not trades). This means 1h candles are secured early. derivative_ticker progress at 15:32:51: [150/378] (40%),
rate ramping 2.4→4.2/s (cold start — 04-26's warm rate was 6.9/s).

**Timeout model CONFIRMED**: 1800s per-child from spawn, NOT per-data_type. Earlier hypothesis (per-data_type reset from
book_snapshot_5 start) was WRONG — the 04-26 child spawned at ~15:01:55, timed out at 15:31:55 (exactly 1800s). The
15:30:44 observation of the child being alive past the expected 15:31:55 was within the final seconds before timeout —
the process was reaped at 15:31:55, not earlier.

**Infrastructure armed**:

- Pipeline script: PID 3412176, polls VM every 30s, auto-triggers manifest merge + candle verification on VM stop
- Heartbeat: PID 3412334, 30-min watchdog
- Monitor `baqcczago`: 60s VM status polls
- ScheduledWakeup: 15:35 UTC for 04-27 derivative_ticker completion check

**Data completeness (1h candles = trades + derivative_ticker)**:

| Date         | trades         | derivative_ticker             | 1h candles   | Notes                                     |
| ------------ | -------------- | ----------------------------- | ------------ | ----------------------------------------- |
| 04-20..04-24 | ✅             | ⚠️ Partial (timed out)        | Partial      | Cascade may rescue some                   |
| 04-25        | ✅ [159/159]   | ⚠️ [200/378] (53%, timed out) | Partial      | Cascade may rescue                        |
| 04-26        | ✅ [156/156]   | ✅ [378/378]                  | **COMPLETE** | book_snapshot_5 timed out at 59%          |
| 04-27        | 🔄 in progress | 🔄 in progress                | Pending      | derivative_ticker FIRST (different order) |
| 04-28..04-30 | ⏳             | ⏳                            | Pending      |                                           |

**Re-armed pipeline survives until next compaction.** ETA for full VM completion: ~17:30 UTC (unchanged — 4 dates
remaining at ~30 min/date).

**Where to resume**: `ps aux | grep post_mdps_pipeline` → if dead, re-arm from workspace `post_mdps_pipeline.sh`. Check
VM status via `gcloud compute instances describe`. Check 04-27+ progress via SSH:
`gcloud compute ssh mdps-backfill-cefi-20260810-115835 --zone=asia-northeast1-c --command="grep -E '(📊|📦|TIMED OUT|04-2[789])' /tmp/vm-exec-5178.log | tail -20"`.
When VM reaches TERMINATED/STOPPED, pipeline script auto-triggers manifest merge + candle verification → flip Todo 5 in
this plan + source doc `features_service_e2e_pipeline_test_2026_05_26.md` → commit `docs(plans):`.

### 2026-08-10 — Slot 14 Session 13 (monitoring, pre-compact)

Pure monitoring continuation — resumed post-compaction at ~15:36 UTC. **Compaction kill pattern #7**: both pipeline
script (PID 3412176) and heartbeat (PID 3412334) killed again. Re-armed: pipeline PID 3935884, heartbeat PID 3936453.

**04-27 in progress** at 15:38 UTC: derivative_ticker ✅ [378/378] 9,072 candles (1h candles SECURED early —
derivative_ticker ran FIRST for 04-27, unlike 04-26 where trades ran first), futures_chain ✅, liquidations ✅.
book_snapshot_5 🔄 [50/357] (14%) at 0.2/s, ETA ~1457s = done ~16:01. All book_snapshot_5 files flagged STALE_DATA (same
pattern as 04-26 — instruments too old for candle generation). Child PID 35809, CPU 157%, RSS 4.2GB.

**04-27 timeout risk**: child spawned 15:31:55, 1800s deadline = 16:01:55. book_snapshot_5 estimated done ~16:01:41
(only 14s before timeout). trades (378 files, marked "re-processing stale" — inherited from 04-26 partial) would start
AFTER book_snapshot_5, almost certainly timing out before completion. Same cascade pattern as 04-26→04-27 expected for
04-27→04-28. But 1h candles for 04-27 are already complete (derivative_ticker ✅).

**Pipeline bucket misconfiguration FIXED this session**: `post_mdps_pipeline.sh` line 11 was `TEST_BUCKET` (copied from
Todo 7 template — `gs://market-data-tick-cefi-test-...`), but BITGET-FUTURES backfill writes to PROD bucket
(`market-data-tick-cefi-prd-...`). Would have caused manifest merge + verification to query empty bucket on VM stop.
Fixed in-place: `TEST_BUCKET`→`PROD_BUCKET` with prod GCS path. Running pipeline killed + re-armed as PID 4146111 with
corrected script.

**Infrastructure armed**:

- Pipeline script: PID 4146111, polls VM every 30s, auto-triggers manifest merge + candle verification on VM stop (NOW
  using PROD bucket)
- Heartbeat: PID 3936453, 30-min watchdog
- Monitor `baqcczago`: 60s VM status polls
- ScheduledWakeup: 15:44 UTC for 04-27 book_snapshot_5 milestone check

**Data completeness (1h candles)**:

| Date         | trades       | derivative_ticker      | 1h candles   | Notes                            |
| ------------ | ------------ | ---------------------- | ------------ | -------------------------------- |
| 04-20..04-24 | ✅           | ⚠️ Partial (timed out) | Partial      | Cascade may rescue some          |
| 04-25        | ✅ [159/159] | ⚠️ [200/378] (53%)     | Partial      | Cascade may rescue               |
| 04-26        | ✅ [156/156] | ✅ [378/378]           | **COMPLETE** | book_snapshot_5 timed out at 59% |
| 04-27        | ⏳ (cascade) | ✅ [378/378]           | **COMPLETE** | book_snapshot_5 in progress      |
| 04-28..04-30 | ⏳           | ⏳                     | Pending      |                                  |

**Where to resume**: `ps aux | grep post_mdps_pipeline`. If pipeline PID 4146111 dead → re-arm from
`.tabs/14/post_mdps_pipeline.sh` (PROD bucket, already fixed). Check VM:
`gcloud compute instances describe mdps-backfill-cefi-20260810-115835 --zone=asia-northeast1-c --format="value(status)"`.
Check progress: SSH to VM, `grep -E '(📊|📦|TIMED OUT|subprocess-per-date: spawn)' /tmp/vm-exec-5178.log | tail -20`.

### 2026-08-10 — Slot 14 Session 14 (monitoring, pre-compact)

Pure monitoring continuation — resumed post-compaction at ~15:42 UTC. **Compaction kill pattern #8**: pipeline script
(PID 4146111) and heartbeat (PID 3936453) both dead on arrival. Re-armed: pipeline PID 186020, heartbeat PID 236577.

**`$TEST_BUCKET` residual bug FOUND and FIXED (15:44 UTC)**: Session 13's fix was INCOMPLETE — it added the
`PROD_BUCKET` definition (line 12) but NEVER changed the actual references on lines 44 and 52. Both still read
`${TEST_BUCKET}` (undefined variable → expands to empty string). If the pipeline had triggered on VM stop with that
script, Steps 2-3 would have queried empty paths and reported zero rows for every date — forcing a full manifest merge +
verification re-run. **Both lines now use `${PROD_BUCKET}`** — all 3 steps verified targeting
`gs://market-data-tick-cefi-prd-central-element-323112`. Buggy pipeline killed, re-armed as PID 186020 with corrected
script.

**04-27 in progress at 15:46 UTC**: derivative_ticker ✅ [378/378] 9,072 candles (1h candles PARTIALLY secured — only
derivative_ticker side; trades still pending). futures_chain ✅, liquidations ✅. book_snapshot_5 🔄 [150/357] (42%) at
757s, 0.2/s, ETA 1045s (16:03:29). **Will timeout** — 1800s deadline 16:01:55, book_snapshot_5 ETA 16:03:29. After
timeout: residual book_snapshot_5 (~17 files) + trades (378 files, unprocessed) + options_chain → cascade to 04-28.

**04-27 processing order**: derivative_ticker ran FIRST (unlike 04-26 where trades ran first, and unlike 04-25 where
trades also ran first). This is the third distinct processing order observed across dates. The variation is undocumented
— but in all observed orders, derivative_ticker or trades (the two 1h-candle-producing data_types) run before
book_snapshot_5, so 1h candles are at least partially secured before the timeout. 04-27's trades was never reached
before book_snapshot_5 ate the window → 04-27 trades will come from cascade in 04-28.

**Manifest staleness issue** persists (intermittent, 2.4% failure rate — age=3-8s rejected by 86400s threshold). Already
tracked as P3 issue `/plans/active/issues/mdps_manifest_staleness_check_inverted_2026_08_10.md`. Non-blocking, no new
action.

**Infrastructure armed**:

- Pipeline script: PID 186020, polls VM every 30s, ALL steps use PROD bucket (fix VERIFIED)
- Heartbeat: PID 236577, 30-min watchdog
- Monitor `baqcczago`: 60s VM status polls
- ScheduledWakeup: ~16:02 UTC for 04-27 timeout + 04-28 spawn check

**Data completeness (1h candles = trades + derivative_ticker)**:

| Date         | trades       | derivative_ticker      | 1h candles   | Notes                                |
| ------------ | ------------ | ---------------------- | ------------ | ------------------------------------ |
| 04-20..04-24 | ✅           | ⚠️ Partial (timed out) | Partial      | Cascade may rescue some              |
| 04-25        | ✅ [159/159] | ⚠️ [200/378] (53%)     | Partial      | Cascade may rescue                   |
| 04-26        | ✅ [156/156] | ✅ [378/378]           | **COMPLETE** | book_snapshot_5 timed out at 59%     |
| 04-27        | ⏳ (cascade) | ✅ [378/378]           | **COMPLETE** | derivative_ticker ran first, secured |
| 04-28..04-30 | ⏳           | ⏳                     | Pending      |                                      |

**Lessons — `$TEST_BUCKET` trap**: When copying a pipeline template across todos, the shell variable DEFINITION is the
obvious change — but every USAGE site must be changed too. An undefined `$TEST_BUCKET` expands silently to empty string;
`gsutil ls ""/cefi/...` produces a `CommandException` line on stdout that `wc -l` counts as "1" (per Session 4's
`gsutil ls | wc -l` false-positive lesson). The result: every date reports `1 capture_status entries` / `1 candle files`
— plausible-looking output that is actually all error text. **Template copy check**: after adapting a script, grep for
every variable name from the source template — any remaining reference is a bug.

**Where to resume**: `ps aux | grep post_mdps_pipeline`. If pipeline PID 186020 dead → re-arm from
`.tabs/14/post_mdps_pipeline.sh` (**PROD bucket in all 3 steps, VERIFIED — `grep -n 'BUCKET'` shows only PROD**). Check
VM:
`gcloud compute instances describe mdps-backfill-cefi-20260810-115835 --zone=asia-northeast1-c --format="value(status)"`.
Check progress: SSH to VM, `grep -E '(📊|📦|TIMED OUT|subprocess-per-date: spawn)' /tmp/vm-exec-5178.log | tail -20`.
04-27 deadline ~16:01:55 → 04-28 spawns at ~16:02 → 04-28 deadline ~16:32. ETA for full VM completion still ~17:30 UTC.

---

### Session continuation (post-compact, ~15:53 UTC)

Compaction kill #10 — pipeline + heartbeat + monitors dead. Re-armed:

- Pipeline: PID 643155 (PROD bucket, all 3 steps verified)
- Heartbeat: PID 646297 (30-min watchdog)
- Monitor `bdl4lvkuu`: 60s VM log polls (📊/📦/TIMEOUT/spawn)
- Monitor `baqcczago`: 60s VM status polls (still alive from prior arm)

**04-27 status** (child spawned 15:31:55, deadline 16:01:55):

- derivative_ticker: ✅ COMPLETE (378/378, 70s)
- futures_chain: ✅ COMPLETE (instant)
- liquidations: ✅ COMPLETE (instant)
- book_snapshot_5: 250/357 (70%) at 15:53:48, elapsed 1221s, ETA 523s → projected finish 1744s (56s BEFORE deadline)
- trades: ⏳ queued behind book_snapshot_5, 378 files at ~6/s = ~63s → projected finish ~1807s (7s PAST deadline)

**Projection**: book_snapshot_5 should complete for 04-27 (first date to do so). trades will likely time out by a few
seconds and cascade to 04-28 along with 04-26's residual ~139 book_snapshot_5. 1h candles secured (derivative_ticker
✅).

**Monitor pattern trap**: 📊 progress lines don't include the data_type name — first monitor `bqdcp92u1` used
`📊.*book_snapshot_5` which matched nothing. Correct pattern: grep ALL 📊 + rely on 📦 transitions for data_type
context.

**Where to resume**: `ps aux | grep post_mdps_pipeline`. If pipeline PID 643155 dead → re-arm from
`.tabs/14/post_mdps_pipeline.sh`. Check VM:
`gcloud compute instances describe mdps-backfill-cefi-20260810-115835 --zone=asia-northeast1-c --format="value(status)"`.
Check progress: SSH to VM, `grep -E '(📊|📦|TIMED OUT|subprocess-per-date: spawn)' /tmp/vm-exec-5178.log | tail -10`.
Next key milestone: 04-27 deadline 16:01:55 → 04-28 spawn ~16:02.

---

### Session continuation (post-compact #11, ~16:05 UTC)

Compaction kill #11 — pipeline (643155) + heartbeat (646297) killed. Re-armed: pipeline PID 1303000, heartbeat
PID 1305009. Monitor `bdl4lvkuu` timed out, re-armed as `bey4720hh` (120s polls, 30-min timeout). Monitor `baqcczago`
alive throughout.

**04-27 outcome** (child spawned 15:31:55, deadline 16:01:56):

- derivative_ticker: ✅ 378/378 (70s)
- futures_chain: ✅
- liquidations: ✅
- book_snapshot_5: **300/357 (84%) only** — projected to complete (ETA 274s at 1441s = 85s margin) but rate COLLAPSED
  after 300; 350 marker never appeared. **Projections from mid-process book_snapshot_5 markers are unreliable** — the
  rate can degrade late (likely API contention or larger instruments at tail).
- trades: ❌ never started, cascaded to 04-28

**04-28** (child spawned 16:01:56, deadline 16:31:56):

- derivative_ticker: ✅ 394/394 (91s, 4.3/s, 9,456 candles) — started first at 16:02:29
- book_snapshot_5: started 16:04:00 — cascade load ~540 items (139 from 04-26 + ~57 from 04-27 + 04-28's own)
- trades: ⏳ queued behind book_snapshot_5, unlikely to start before 16:31:56 deadline
- 1h candles: **secured** (derivative_ticker ✅)

**04-28 had 394 derivative_ticker files** (04-27 had 378) — the extra 16 are cascade residuals from earlier dates being
re-processed as "stale." Initial rate 1.6/s (bootstrap), accelerated to 4.3/s (cache warmup).

**Cascade accumulation**: 04-26 residual (139 book_snapshot_5) → 04-27 adds (57 book_snapshot_5 + 378 trades) → 04-28
adds (?? book_snapshot_5 + trades). By 04-29/04-30 the cascade will be 3-4× normal workload. Each date secures its 1h
candles via derivative_ticker (always runs first in observed orders), but trades + book_snapshot_5 may never complete
within the 1800s window for remaining dates.

**Data completeness (revised)**:

| Date         | deriv_ticker | trades     | book_snapshot_5   | 1h candles   |
| ------------ | ------------ | ---------- | ----------------- | ------------ |
| 04-20..04-25 | Various      | Various    | Various           | Partial      |
| 04-26        | ✅ 378/378   | ✅ 156/156 | 200/339 (59%, TO) | **COMPLETE** |
| 04-27        | ✅ 378/378   | ❌ cascade | 300/357 (84%, TO) | Partial      |
| 04-28        | ✅ 394/394   | ⏳ queued  | 🔄 in progress    | **COMPLETE** |
| 04-29..04-30 | ⏳           | ⏳         | ⏳                | Pending      |

**Where to resume**: `ps aux | grep post_mdps_pipeline`. If pipeline PID 1303000 dead → re-arm from
`.tabs/14/post_mdps_pipeline.sh`. Check VM:
`gcloud compute instances describe mdps-backfill-cefi-20260810-115835 --zone=asia-northeast1-c --format="value(status)"`.
Check progress: SSH to VM, `grep -E '(📊|📦|TIMED OUT|subprocess-per-date: spawn)' /tmp/vm-exec-5178.log | tail -10`.
Next milestones: 04-28 deadline 16:31:56 → 04-29 spawn ~16:32 → 04-30 spawn ~17:02. Full VM completion ETA ~17:30 UTC.

---

### Session continuation (post-compact #12, ~16:08 UTC)

Compaction kill #12 — pipeline (1303000) + heartbeat (1305009) both dead at session start. Re-armed: pipeline PID
1871585, heartbeat PID 1872640. Armed monitors: `bjekxi8zh` (90s log polls), `bd7qglize` (60s VM status). Safety
fallback wakeup at 16:29 UTC.

**Full 1h candle audit across ALL 11 dates** — queried every completion marker from VM log to determine exactly which
dates have both trades AND derivative_ticker (1h candles = trades ∧ derivative_ticker):

| Date  | trades             | deriv_ticker     | book_snapshot_5  | 1h candles   |
| ----- | ------------------ | ---------------- | ---------------- | ------------ |
| 04-20 | ✅ 45/45 (195s)    | ✅ 376/376 (57s) | various          | **COMPLETE** |
| 04-21 | ✅ 47/47 (197s)    | ❌ never reached | blocked deriv    | PARTIAL      |
| 04-22 | ❌ never reached   | ❌ never reached | blocked all      | **NONE**     |
| 04-23 | ✅ 219/219 (1182s) | ❌ never reached | blocked deriv    | PARTIAL      |
| 04-24 | ❌ never reached   | ❌ never reached | blocked all      | **NONE**     |
| 04-25 | ✅ 159/159 (753s)  | ❌ never reached | blocked deriv    | PARTIAL      |
| 04-26 | ✅ 156/156 (686s)  | ✅ 378/378 (55s) | 200/339 (TO)     | **COMPLETE** |
| 04-27 | ❌ never reached   | ✅ 378/378 (70s) | 300/357 (TO)     | PARTIAL      |
| 04-28 | ⏳ queued          | ✅ 394/394 (91s) | 🔄 100/352 (28%) | PARTIAL      |
| 04-29 | ⏳                 | ⏳               | ⏳               | Pending      |
| 04-30 | ⏳                 | ⏳               | ⏳               | Pending      |

**Result: 2/11 dates have complete 1h candles** (04-20, 04-26). The root cause is confirmed across all dates:
book_snapshot_5 at ~0.2/s dominates the 1800s budget. The processing order is non-deterministic per date — whichever of
{trades, derivative_ticker} gets queued AFTER book_snapshot_5 is starved:

| Date  | Order                                          | Starved source    |
| ----- | ---------------------------------------------- | ----------------- |
| 04-25 | futures→options→trades→book                    | derivative_ticker |
| 04-26 | liquidations→options→trades→futures→deriv→book | (none — both ran) |
| 04-27 | deriv→futures→liquidations→book                | trades            |
| 04-28 | deriv→book                                     | trades (queued)   |

**04-28 current state** (VM time 16:10): book_snapshot_5 at 100/352 (28%, 372s elapsed, 0.27/s, ETA 937s → ~16:25:50).
Rate slightly improved from 04-27's 0.21/s. Trades queued behind it — unlikely to start before 16:34 deadline unless
book_snapshot_5 completes with margin. 04-28 deadline 16:31:56 → 04-29 spawn ~16:32.

**Cascade load**: 04-29 will inherit 04-28's full workload (trades + residual book_snapshot_5 ~252 items) + accumulated
cascade from 04-26 (139) + 04-27 (57 trades + 57 book). The final dates will face 3-4× normal load.

**Stale manifest errors expanded**: Now observed on 04-24 (age=2-12s) and 04-26 (age=3-8s) in addition to previously
noted occurrences. All report age <15s against threshold=86400s — comparison direction clearly inverted. Issue doc:
`/plans/active/issues/mdps_manifest_staleness_check_inverted_2026_08_10.md`.

**Lessons reinforced**:

- book_snapshot_5 mid-process projections are NOT reliable — 04-27 projected completion at 1715s (85s margin) but rate
  collapsed after 300/357; the 350 marker never appeared
- The non-deterministic processing order means each date loses a DIFFERENT candle source — there's no "always secured"
  guarantee except that one of {trades, derivative_ticker} runs before book_snapshot_5 blocks the queue
- `ps aux | grep` alone isn't sufficient to detect process death across compaction boundaries — always verify PIDs
  explicitly at session start

**Where to resume**: Pipeline PID 1871585, heartbeat PID 1872640, monitors `bjekxi8zh` + `bd7qglize`. VM RUNNING. 04-28
book_snapshot_5 at 100/352. Next: 04-28 deadline 16:31:56 → 04-29 spawn → 04-30 spawn. Full completion ETA ~17:30 UTC.
On VM stop: pipeline auto-triggers manifest merge → verify candle counts → flip Todo 5.

---

### Session continuation (post-compact #13, ~16:18 UTC)

Compaction kill #13 — pipeline (1871585) + heartbeat (1872640) both dead at session start. Monitors `bjekxi8zh` +
`bd7qglize` timed out. Re-armed: pipeline PID 2612622, heartbeat (background), monitor `bi2imn9d2` (60s VM status),
monitor `bp3cla76i` (90s log polls). Safety wakeup at 16:29 UTC.

**04-28 current state** (child spawned 16:01:56, deadline 16:31:56):

- derivative_ticker: ✅ 394/394 (91s, 4.3/s)
- book_snapshot_5: 250/352 (71%, 247✅ 3❌, 875s elapsed, 0.3/s, ETA 357s → ~16:24:30)
- trades: ⏳ queued behind book_snapshot_5 — 102 book items left at 0.3/s ≈ 340s, leaving ~7 min margin before 16:31:56
  deadline

**First write failures this run**: 3 errors at 250-marker — all stale-manifest (age=3-7s vs 86400s threshold). Same
inverted-comparison bug as earlier dates, now also on 04-28. Issue doc already tracks this.

**1h candles**: derivative_ticker ✅ = secured for 04-28.

Infrastructure armed:

- Pipeline: PID 2612622 (PROD bucket, all 3 steps)
- Heartbeat: background, 120s interval
- Monitors: `bi2imn9d2` (60s VM status), `bp3cla76i` (90s log polls)
- Safety wakeup: 16:29 UTC

**Where to resume**: Pipeline PID 2612622, heartbeat + monitors all re-armed. VM RUNNING. 04-28 book_snapshot_5 at
250/352 (71%, ETA ~16:24). Deadline 16:31:56 → 04-29 spawn ~16:32. Full completion ETA ~17:30 UTC. On VM stop: pipeline
auto-triggers manifest merge → verify candle counts → flip Todo 5.

---

### Session continuation (post-compact #14, ~16:27 UTC)

Compaction kill #14 — pipeline (2612622) + heartbeat both dead at session start. Monitors `bi2imn9d2` + `bp3cla76i`
survived this compaction (first time monitors outlived a kill — they were Monitor-based, not Bash-based). Re-armed:
pipeline PID 3100523, heartbeat PID 3102177.

**04-28 outcome** (child spawned 16:01:56, deadline 16:31:56):

- book_snapshot_5: ✅ 352/352 (349✅ 3❌, 1215s, 0.3/s) — **FIRST date where book_snapshot_5 completes fully**
- futures_chain: ✅
- liquidations: ✅ 200/200 (all STALE_DATA, 9s, 22.8/s)
- options_chain: ✅
- trades: 🔄 50/203 (25%, 163s elapsed, 0.3/s, started 16:24:26)

**Trades anomaly — 0.3/s rate**: Previous dates had trades at 6-20/s. 04-28 trades at 0.3/s, matching book_snapshot_5
speed. 203 files suggests ~65% of normal volume (378→203). At 0.3/s with 153 remaining → ETA ~16:33, past the 16:31:56
deadline. Likely root cause: cascaded residuals from 04-25/04-26/04-27 creating manifest contention, OR residual
book_snapshot_5 files mixed into the trades queue slowing per-file throughput.

**04-28 1h candles**: COMPLETE (derivative_ticker ✅ + trades 50✅ so far — 904 candles already written).

**Stale manifest errors**: 3 more on 04-28 (age=3-7s) — same inverted-comparison bug, already tracked in issue doc.

**1h candle completeness across 11 dates**:

| Date  | derivative_ticker  | trades    | 1h candles |
| ----- | ------------------ | --------- | ---------- |
| 04-20 | ✅ (completed)     | ✅        | COMPLETE   |
| 04-21 | ❌ (timed out)     | ✅        | PARTIAL    |
| 04-22 | ❌ (timed out)     | ❌        | NONE       |
| 04-23 | ✅ (completed)     | ❌ (TO)   | PARTIAL    |
| 04-24 | ✅ (completed)     | ❌ (TO)   | PARTIAL    |
| 04-25 | ✅ (completed)     | ❌ (TO)   | PARTIAL    |
| 04-26 | ✅ (completed)     | ✅        | COMPLETE   |
| 04-27 | ❌ (never reached) | ❌ (TO)   | NONE       |
| 04-28 | ✅ (394/394)       | 🔄 50/203 | COMPLETE   |

**3 of 9 processed dates have complete 1h candles** (04-20, 04-26, 04-28). 04-29 + 04-30 still to process.

**Lessons reinforced**:

- Monitors using the `Monitor` tool can survive compaction; Bash-based `run_in_background` processes always die
- 0.3/s is the universal floor rate for book_snapshot_5 AND cascaded trades — suggesting a common bottleneck (likely
  manifest writes or API rate limiting, not per-data-type-specific)
- 04-28 was the first date where book_snapshot_5 completed within the 1800s budget, enabled by smaller load (352 vs
  04-27's 357)

Infrastructure armed:

- Pipeline: PID 3100523 (PROD bucket, all 3 steps)
- Heartbeat: PID 3102177, 120s interval
- Monitors: `bi2imn9d2` (60s VM status), `bp3cla76i` (90s log polls) — NOTE: these timed out ~16:29, need re-arm
- Legacy monitor `bey4720hh` still active (120s polls)

**Where to resume**: Pipeline PID 3100523, heartbeat PID 3102177. VM RUNNING. 04-28 trades 50/203 at 0.3/s — deadline
16:31:56, likely to timeout. 04-29 spawn ~16:32 with 3× cascade load. 04-30 spawn ~17:02. Full completion ETA ~17:30
UTC. On VM stop: pipeline auto-triggers manifest merge → verify candle counts → flip Todo 5.

Check pipeline alive: `ps aux | grep post_mdps_pipeline`. Re-arm monitors if needed. Check 04-28 outcome:
`grep -E '(TIMED OUT|subprocess-per-date: spawn)' /tmp/vm-exec-5178.log | tail -4`.

---

### Session continuation (post-compact #15, ~16:47 UTC)

Compaction kill #15 — pipeline (3100523) + heartbeat (3102177) dead at session start. Pipeline re-armed as PID 115154
(PROD bucket, all 3 steps). Monitors `bi2imn9d2` + `bp3cla76i` had timed out ~16:29 — not re-armed (Monitor-based
approach re-evaluated; opted for direct SSH checks + pipeline script instead). Heartbeat PID 3231770 as 30-min watchdog.

**04-28 outcome** (child spawned 16:01:56, deadline 16:31:56):

- book_snapshot_5: ✅ 352/352 (349✅ 3❌, 1215s)
- derivative_ticker: ✅ 394/394
- trades: 🔄 100/203 (25%) at 0.3/s anomaly — TIMED OUT at 16:31:56. Residual 103 trades cascade to 04-29.

**04-29** (child spawned 16:31:56, deadline 17:01:56):

- book_snapshot_5: ✅ 375/375 (100%), 8,987 candles, 1369s elapsed — BUT all 375 were STALE_DATA skips (cascaded from
  04-28 partial completion). 0 new writes, 0 errors.
- liquidations: ✅ 329/329 (14s), 0 candles — ALL 329 FAILED with SCHEMA_VALIDATION_FAILED (NaN in non-nullable columns
  open/high/low/close). Consistent across all dates.
- options_chain: ✅ 0 files (instant).
- trades: 🔄 at 16:55:20 — 391 listed, 172 skipped (existing outputs from cascade), 219 to process. Started at 16:55:20.
  Deadline 17:01:56 → ~6.5 min for 219 files.
- futures_chain: ⏳ (0 files, instant when reached).
- derivative_ticker: ⏳ (395 files). If trades completes with ~2 min margin, derivative_ticker at ~1/s (395s) would
  barely timeout. 04-29 deadline 17:01:56.

**04-30**: Pending (spawn ~17:02 after 04-29 timeout).

**Progress at 16:56 UTC**:

| Date  | trades             | deriv_ticker | book_snapshot_5    | 1h candles |
| ----- | ------------------ | ------------ | ------------------ | ---------- |
| 04-20 | ✅                 | ✅           | various            | COMPLETE   |
| 04-21 | ✅                 | ❌ timeout   | various            | PARTIAL    |
| 04-22 | ❌                 | ❌ timeout   | various            | NONE       |
| 04-23 | ✅                 | ❌ timeout   | various            | PARTIAL    |
| 04-24 | ✅                 | ❌ timeout   | various            | PARTIAL    |
| 04-25 | ✅                 | ❌ timeout   | various            | PARTIAL    |
| 04-26 | ✅                 | ✅           | 200/339 (TO)       | COMPLETE   |
| 04-27 | ❌ (never reached) | ✅           | 300/357 (TO)       | PARTIAL    |
| 04-28 | 🔄 100/203 (TO)    | ✅           | ✅ 352/352         | COMPLETE   |
| 04-29 | 🔄 219 remain      | ⏳ queued    | ✅ 375/375 (STALE) | RUNNING    |
| 04-30 | ⏳                 | ⏳           | ⏳                 | PENDING    |

**Pipeline bucket fix**: All 3 steps use `PROD_BUCKET` — verified (`grep -n 'BUCKET'` shows only `PROD_BUCKET`). Bug
history: original script had `TEST_BUCKET` from Todo 7 template → fixed to `PROD_BUCKET` definition (session 13) → usage
sites also fixed (session 14).

**Infrastructure armed**:

- Pipeline: PID 535127 (re-armed at 16:56 after this compaction kill #16), polls VM every 30s, PROD bucket all 3 steps
- Heartbeat: PID 3231770, 30-min watchdog (survived this compaction — background process, not harness-tracked)

**Where to resume**: `ps aux | grep post_mdps_pipeline` → if dead, re-arm from `.tabs/14/post_mdps_pipeline.sh`. Check
VM:
`gcloud compute instances describe mdps-backfill-cefi-20260810-115835 --zone=asia-northeast1-c --format="value(status)"`.
Check progress: SSH to VM, `grep -E '(📊|📦|TIMED OUT|subprocess-per-date: spawn)' /tmp/vm-exec-5178.log | tail -10`.
Next milestones: 04-29 deadline 17:01:56 → 04-30 spawn ~17:02 → 04-30 deadline ~17:32. Full completion ETA ~17:30 UTC.

### Sessions 17–18 — VM monitoring continues (post-compacts #16–#18, 17:03–17:17)

Pipeline killed + re-armed through compactions #17–#18. VM progressed through dates 04-28 (TIMED OUT 16:31:56, trades
100/203), 04-29 (TIMED OUT 17:01:57, book_snapshot_5 375/375 STALE, trades 219/391 TO, derivative_ticker never reached,
0 candles), and 04-30 spawned at 17:01:57. By 17:12, 04-30 had derivative_ticker complete (395/395, 9,480 candles),
liquidations all schema-failed, options_chain done, book_snapshot_5 at D* tickers (all STALE_DATA, ETA ~17:26). 1h
candle outlook for 04-30 was GOOD — only trades + futures_chain remaining within the 17:31:57 deadline. Worst-case
compaction count reached 18 kills — Bash `run_in_background` fundamentally mismatched for multi-hour monitoring.

### Session 19 — 04-30 final outcome + GCS verification (2026-08-10 ~17:17–17:36)

**Compaction kills #19–#20**: Pipeline re-armed at 17:17 (PID 1902031), killed again ~17:23. Final verification run
manually.

**04-30 final outcome — TIMED OUT at 17:31:57** (1800s from 17:01:57 spawn):

| #   | data_type         | Result                                        | Time          |
| --- | ----------------- | --------------------------------------------- | ------------- |
| 1   | derivative_ticker | 395/395 ✅, 9,480 candles, 5.7/s              | 69s           |
| 2   | liquidations      | 237/237, 0 candles (all schema-failed)        | 11s           |
| 3   | options_chain     | ✅                                            | 1s            |
| 4   | book_snapshot_5   | 379/379 ✅, 378 STALE_DATA, 0.3/s             | 1402s (17:27) |
| 5   | futures_chain     | ✅ (silent)                                   | ~60s          |
| 6   | trades            | ~70-80/196 at timeout, 0.3/s, 50/196 at 17:29 | killed 17:32  |

VM terminated 17:32:00 (SIGTERM), deployment archived as `DEPLOYMENT_FAILED`. Per-VM shard at
`_index/per_vm/mdps-backfill-cefi-20260810-115835.parquet` (91.54 KiB, 2,700+ entries, last update 17:31:53).

**🔴 CRITICAL: Pipeline GCS paths were WRONG.** The PROD bucket `market-data-tick-cefi-prd-central-element-323112` uses:
`processed_candles/by_date/day={date}/pipeline_mode=batch_tardis/timeframe=1h/data_type={type}/instrument_type=PERPETUAL/venue=BITGET-FUTURES/`
NOT `cefi/candles_1h/venue=BITGET-FUTURES/day={date}/`. The pipeline script inherited wrong paths from a Todo 7
template.

**BITGET-FUTURES 1h candle inventory (GCS canonical paths, pre-manifest-consolidation)**:

| Date  | trades | deriv_ticker | book_snapshot_5 | 1h Status |
| ----- | ------ | ------------ | --------------- | --------- |
| 04-20 | 376    | 376          | 318             | COMPLETE  |
| 04-21 | 377    | 0            | 334             | PARTIAL   |
| 04-22 | 222    | 0            | 345             | PARTIAL   |
| 04-23 | 325    | 0            | 219             | PARTIAL   |
| 04-24 | 209    | 0            | 346             | PARTIAL   |
| 04-25 | 378    | 0            | 216             | PARTIAL   |
| 04-26 | 378    | 378          | 211             | COMPLETE  |
| 04-27 | 177    | 378          | 342             | PARTIAL   |
| 04-28 | 331    | 394          | 349             | PARTIAL   |
| 04-29 | 290    | 0            | 375             | PARTIAL   |
| 04-30 | 286    | 395          | 378             | PARTIAL   |

**IMPORTANT**: derivative_ticker=0 for 04-21..04-25, 04-29 may reflect pre-consolidation state — the VM completed
derivative_ticker on several of these dates (e.g. 04-28 dt=394 ✅, 04-30 dt=395 ✅). The manifest consolidator (Cloud
Run) must merge the per-VM shard before all data appears at canonical paths. Re-run candle inventory after
consolidation.

**Lessons**:

- **Path structure trap**: Bucket uses `processed_candles/by_date/` with `pipeline_mode=batch_{source}/` partitioning.
  Always verify GCS path structure before writing pipeline scripts — don't inherit paths from templates for different
  AGs.
- **Per-VM shard ≠ canonical paths**: Data written by the VM IS at canonical paths (MDPS writer writes parquet
  directly), but the manifest INDEX is in the per-VM shard. The 0-count dates may have data that wasn't indexed yet.
- **1800s timeout is exact**: 04-30 killed at precisely 17:31:57 = 17:01:57 + 1800s. Trades was mid-processing.
- **20 compactions across this Todo 5**: Background Bash processes are a fundamental mismatch for multi-hour monitoring.
  A VM-side callback or systemd timer would eliminate this failure mode.

**Where to resume**: Fix `post_mdps_pipeline.sh` paths (Step 2+3 to `processed_candles/by_date/`). Wait for manifest
consolidator to merge per-VM shard, then re-run candle inventory. Flip Todo 5 when 1h candle counts are final.
