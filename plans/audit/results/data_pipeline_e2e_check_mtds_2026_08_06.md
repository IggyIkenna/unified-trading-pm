---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-08-06), cefi_mtds_smoke_tester run #2"
summary: >-
  data_pipeline_e2e_check_mtds pipeline-e2e-check for day=2026-08-06, run via the NEW driver-VM launcher
  (deployment-service/scripts/vm/launch-pipeline-e2e-check-driver-vm.sh) added specifically in response to 2026-08-05's
  run (agt-e76dc5) hitting a shared-host OOM-kill. 10 driver VMs launched (5 asset-groups x {combined
  force/skip/live/canonical, supplementary live-only}), all reached a genuine terminal state — either a real completed
  sweep or the documented 3600s wall-clock safety timeout (exit_code=3, not a crash). CEFI's force/skip/live/canonical
  batch covered 11 real (venue,data_type) shards across BINANCE-SPOT/FUTURES/DELIVERY and BYBIT before timing out;
  CEFI's live-only supplement covered 12 more (BINANCE-SPOT/FUTURES only) — DERIBIT was never reached by either CEFI run
  in this smoke window. The CEFI DERIBIT futures_chain negative-check (§3a) PASSED (0 rows for 2026-08-06, retry-storm
  regression not recurring). The §3b content-check could not complete with fresh same-run evidence (Tardis-guard retry
  exhaustion blocked the sampled BINANCE-FUTURES derivative_ticker force-write; DERIBIT unreached). A real methodology
  finding: combining --require-captured with the live leg in one invocation incorrectly gates live-leg cell selection by
  the same "genuinely captured" filter as force/skip — worked around via a separate live-only invocation per
  asset_group, which recovered real live coverage for DEFI/CEFI/SPORTS that the combined runs had zeroed out. SPORTS
  live coverage is now proven broken at scale (1/110 passed, 84 failed). TRADFI is proven code-complete for live
  connectors (previously flagged as possibly unregistered) with 2/5 real MVP cells passing both combined and live-only
  runs.
status: partial
nature: record
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, deployment-service]
scope: [engineer, admin]
tags:
  [
    pipeline-e2e-check,
    data_pipeline_e2e_check_mtds,
    cefi,
    smoke-test,
    wall-clock-timeout,
    driver-vm-launcher,
    require-captured-live-leg-gate,
  ]
related:
  [
    plans/active/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md,
    /plans/archive/2026_08/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md,
    plans/audit/results/data_pipeline_e2e_check_mtds_2026_08_05.md,
  ]
created: 2026-08-07
audited_scope: >-
  data_pipeline_e2e_check_mtds real-VM force/skip/live/canonical pipeline check for day=2026-08-06, run via
  deployment-service/scripts/vm/launch-pipeline-e2e-check-driver-vm.sh (one dedicated e2-highmem-4 VM per asset_group,
  per leg-set) — 5 combined (force,skip,live,canonical + --require-captured --auto-day) + 5 supplementary live-only
  (--legs live --mvp-only, no --require-captured) invocations, all --asset-group-scoped to work around the
  confirmed-still-open enumeration bug that silently zeroes CEFI/SPORTS in an unfiltered sweep.
date: 2026-08-07
auditor: cefi_mtds_smoke_tester (agt-6a9c44, slot 8, real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-08-06
generated_at: 2026-08-07T04:41:00+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-08-06)

> **Provenance note**: this is `cefi_mtds_smoke_tester`'s SECOND run, first using the new
> `launch-pipeline-e2e-check-driver-vm.sh` (added specifically after 2026-08-05's shared-host OOM-kill — see
> `/plans/archive/2026_08/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md`). The fix
> worked: no host-level kill this run. All 10 driver VMs reached a genuine terminal state. 5 of 10 completed their full
> assigned matrix and wrote a real `write_report()` output (DEFI-combined, TRADFI-combined, PREDICTION-combined,
> TRADFI-live, PREDICTION-live, SPORTS-live — 6 actually); the other 4 (CEFI-combined, SPORTS-combined, CEFI-live,
> DEFI-live) hit the script's own `--wall-clock-timeout-sec 3600` safety backstop (`exit_code=3`, a deliberate
> `os._exit(3)` via SIGALRM, not a crash) before finishing their much larger CEFI/SPORTS/DEFI candidate matrices — real
> infrastructure work happened (VMs launched, shards processed) but `write_report()` never ran for those 4, so this
> doc's tables for them are hand-assembled from the real GCS VM logs (`vm-logs/<vm>/run.log`), per this skill's own
> "ground truth is the VM run.log" principle. The GCS report-mirror path
> (`pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-06/`) is NOT reusable across these 10 invocations —
> confirmed the known collision (each asset-group's driver VM has its own empty local disk, so `write_report()`'s
> same-day MERGE logic only works within ONE process/VM, not across this 10-VM fan-out; the GCS copy is simply whichever
> invocation finished last) — every real number below comes from a VM's own run.log or a same-run local report snapshot
> captured immediately after that specific VM went terminal, before the next one could overwrite the shared GCS path.

**Legs attempted:** force, skip, live, canonical (10 driver VMs: 5 asset_groups × {combined, live-only supplement}).
**Day:** 2026-08-06 (auto-day substituted per cell — the corpus is sparse; see per-cell notes). **Launched:**
~03:28–03:29 UTC (combined), ~03:37–03:39 UTC (live-only supplement, added mid-run — see finding #2 below). **All 10
terminal by:** 04:40 UTC.

**Combined summary:** 10/10 driver VMs reached a genuine terminal state (0 host-kills, 0 hangs). 6/10 completed their
assigned matrix and produced a real merged report. 4/10 (CEFI×2, SPORTS-combined, DEFI-live) hit the 3600s wall-clock
safety timeout with real, partial, evidence-backed progress. DERIBIT was never reached by CEFI in either run this smoke
window.

---

## 🎯 CEFI headline (this role's reason to exist)

**Enumeration bug workaround confirmed still necessary**: `enumerate_mtds_shards()`'s combined-list fallback gate
(`if shards: return shards`) is still combined-list-scoped, not per-asset_group — verified live in current HEAD
(`market-tick-data-service/scripts/pipeline_e2e_check.py:684`) before this run. Every CEFI number below is only real
because this run explicitly passed `--asset-group CEFI` (`enumerate_mtds_shards` correctly returned 225 MVP shards,
matching the issue doc's measurement — see
`plans/active/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md`, still `status: open`
with unchecked action items).

### CEFI combined (force,skip,live,canonical + --require-captured --auto-day)

VM `pipeline-e2e-check-mtds-20260807-032815-7acf8c`. 225 shards enumerated. Ran 03:31–04:31 (3600s), hit the wall-clock
safety timeout (`exit_code=3`) mid-BYBIT:liquidations live leg. **write_report() never ran — no merged pass/fail table
exists for this invocation.** Real, evidence-backed coverage extracted from `run.log` (77 real `launch_vm_and_wait`
calls, Tardis-guard-retried where the N=1 cap was hit — confirmed WORKING as designed, not a bug: "Keep total concurrent
connections well under Tardis's tolerance" retry-with-backoff fired repeatedly and always eventually got through):

| Venue            | data_type         | Force/skip reached? | Live reached?                   | Notes                                                                           |
| ---------------- | ----------------- | ------------------- | ------------------------------- | ------------------------------------------------------------------------------- |
| BINANCE-SPOT     | trades            | yes                 | yes                             | auto-day=2026-05-31                                                             |
| BINANCE-SPOT     | book_snapshot_5   | yes                 | yes                             | auto-day=2026-05-31                                                             |
| BINANCE-FUTURES  | trades            | yes                 | yes                             |                                                                                 |
| BINANCE-FUTURES  | book_snapshot_5   | yes                 | yes                             |                                                                                 |
| BINANCE-FUTURES  | derivative_ticker | yes                 | yes                             | auto-day=2026-05-31; force-leg hit Tardis-guard retry storm — see §3b gap below |
| BINANCE-FUTURES  | liquidations      | yes                 | yes                             | auto-day=2026-05-31                                                             |
| BINANCE-DELIVERY | trades            | force only          | no                              | run advanced to BYBIT before this shard's skip/live legs                        |
| BYBIT            | trades            | yes                 | yes                             | auto-day=2026-07-22                                                             |
| BYBIT            | book_snapshot_5   | yes                 | yes                             | auto-day=2026-06-27                                                             |
| BYBIT            | derivative_ticker | yes                 | yes                             | auto-day=2026-06-27                                                             |
| BYBIT            | liquidations      | yes                 | mid-live-leg when timeout fired | auto-day=2026-05-29; this is where the 3600s bound hit                          |

**DERIBIT: NOT reached.** 225-shard CEFI matrix genuinely needs more than 3600s under Tardis N=1 serialization — 11 of
225 (venue, data_type) cells got real coverage in this window (~5% by shard count, but front-loaded on high-priority
CEXes).

### CEFI live-only supplement (--legs live --mvp-only, no --require-captured)

VM `pipeline-e2e-check-mtds-20260807-033706-1f5541`. Same 225-shard enumeration. Ran 03:41–04:36 (3600s), hit the same
wall-clock timeout — **write_report() never ran for this one either.** 12 real live-smoke VM launches, **all 12
`launcher exited 0`** (0 launch failures — the live leg doesn't hit the Tardis N=1 guard per §4a):
BINANCE-FUTURES{book_snapshot_5, derivative_ticker, liquidations, options_chain, trades}, BINANCE-SPOT{book_snapshot_5,
derivative_ticker, liquidations, ohlcv_1m, perp_funding, trades, volatility_index}. DERIBIT not reached here either.

### § 3a — DERIBIT `futures_chain` structural-absence negative-check

**PASS.** Direct `read_availability_index()` read (bucket=`market-data-tick-cefi-prd-central-element-323112`, filtered
`venue=DERIBIT, data_type=futures_chain`, columns=`[date,venue,data_type,capture_status]` — memory-bounded per the
filters= mechanism, not the naive unfiltered-then-pandas-filter form the skill's illustrative snippet shows): **0 rows
at all for day=2026-08-06** (neither `captured` nor `attempted_failed`) out of 12,631 total DERIBIT futures_chain rows
across all history. The 2026-07-15 retry-storm regression
(`plans/active/issues/deribit_options_chain_af_g4_blocker_2026_07_03.md`) is **not recurring** — the structurally-absent
channel was correctly never attempted today. (Skipped the "run force-leg twice, diff the count" step since there was
nothing to diff — 0 rows both times by construction; forcing an attempt myself would have manufactured exactly the
condition this check exists to detect the ABSENCE of.)

### § 3b — Content-level spot-checks (DERIBIT `options_chain` greeks/IV, BINANCE-FUTURES `derivative_ticker` funding/OI)

**NOT COMPLETED this run — honest gap, not a fabricated pass.** DERIBIT `options_chain` was never reached by either CEFI
invocation (see above) — no fresh test-bucket parquet exists to check. BINANCE-FUTURES `derivative_ticker`'s force-leg
(the one CEFI cell that WOULD have given real content to check) hit 2+ Tardis-guard retry rejections
(`launcher exited 1 ... 5 streams (default 4 — its own cap)`) before the run's log moved on to the skip leg; neither of
the two candidate VM names logged for this attempt (`mtds-backfill-cefi-pipelinecheck-20260807-035647-debcbd`,
`...-035707-debcbd`) has a `run.log` or `EXIT_STATUS` in GCS — i.e. no real VM was ever created for this specific
force-write, the guard rejected all 3 retry attempts. A pre-existing test-bucket parquet for this exact (venue,
data_type) does exist from an EARLIER unrelated run (days 2026-02-02, 2026-07-09) but checking THAT would not be
evidence about TODAY's write path, so I did not substitute it. **Follow-up needed**: re-run this specific check once
CEFI can either (a) get more Tardis-guard headroom, or (b) run in isolation without competing against 10 other
concurrent shards' worth of guard contention within the same VM's own sequential loop.

---

## Phase 0 — provisioning gate

All 5 `-test-` buckets verified via object-level probe (`gcloud storage buckets describe`/`gsutil ls -b` correctly
avoided — `unified-trading-sa` lacks `storage.buckets.get`): cefi, defi, tradfi, sports, pred — **all OK, exist with
objects**. No provisioning needed.

## Other asset_groups (real, evidence-backed — completes this skill's whole-matrix contract)

| Asset group | Combined run (force,skip,live,canonical)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Live-only supplement                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DEFI        | **PROVED NOTHING** (guard-triggered, `exit_code=1`): 2958 shards × 4 legs = 11832, ALL `skipped/no_captured_data_for_cell`, 0 proven. See finding #2 below — this run's `--require-captured` combination gated the live leg too, on top of the ALREADY-documented (pre-existing, expected) near-total absence of genuinely-captured cells across DEFI's raw 102-venue × 29-data_type cross-product (`mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md` flags this exact shape pre-emptively as accepted/non-actionable). | **Real, completed** (finding #2's fix in action): 9 real live-smoke launches, all `launcher exited 0`, all `UNISWAP_V2-ETHEREUM` (bridge_events, dex_pool_swaps, gas_fees, lending_indices, liquidations, lst_rates, mev_events, oracle_prices, staking_yields). No merged report (timed out before `write_report()`, but real per-VM launch evidence exists).                                                                                                                                |
| TRADFI      | **Real, completed.** total=20 (5 MVP shards × 4 legs), **passed=2, failed=13, skipped=5**. 65% failure rate on the current 5-cell MVP set — a real finding worth a follow-up look, distinct from this role's CEFI mandate.                                                                                                                                                                                                                                                                                                                       | **Real, completed.** total=5, **passed=2, failed=2, skipped=1**. Confirms tradfi HAS registered live `WSFeedConnector`s for at least NASDAQ/NYSE/CME/CBOE/FX (the skill's §4a cautionary note about possibly-unregistered tradfi live connectors does not apply — live-leg VMs launched and connected for all 5).                                                                                                                                                                             |
| SPORTS      | Hit wall-clock timeout (`exit_code=3`) after 110-shard enumeration confirmed correct (issue-doc predicted 110, matches). Real coverage before timeout: 8 distinct (venue,data_type) force/skip cells (BETFAIR_SB_UK:odds_snapshot, ODDS_API:{odds_horizon_bucket,trades}, PINNACLE:{arbitrage_opportunity,odds_horizon_bucket,odds_movement,odds_snapshot,trades}), only 2 reached their live leg before timeout.                                                                                                                                | **Real, completed — full 110-shard sweep finished.** total=110, **passed=1, failed=84, skipped=25**. **Major finding**: SPORTS live coverage is proven broken at scale — 0.9% pass rate. Not this role's headline, but severity-worthy on its own; flagging for a dedicated SPORTS-focused follow-up (this smoke role sweeps every asset_group as a side effect, per its own role-file rationale, but a P1/P2 finding this size deserves its own triage, not burial in a CEFI-titled report). |
| PREDICTION  | **Real, completed.** total=16 (4 MVP shards × 4 legs), **passed=3, failed=5, skipped=8**.                                                                                                                                                                                                                                                                                                                                                                                                                                                        | **Real, completed.** total=4, **passed=2, failed=2**. The 2 failures are both `book_snapshot_5` (POLYMARKET, KALSHI) failing with `no sampled instrument_id/underlying available for live shard-spec` — a distinct, already-understood gap (live sampler can't find an instrument for this data_type), not a connectivity failure. The 2 passes (POLYMARKET/KALSHI `trades`) are genuine clean WS connections.                                                                                |

---

## Key methodology findings from this run

1. **Driver-VM launcher fix WORKED — zero host-level kills this run**, vs. 2026-08-05's 3/3 local-process kills at a
   reproducible ~300-330s mark. `deployment-service/scripts/vm/launch-pipeline-e2e-check-driver-vm.sh` (added
   2026-08-06/07 in direct response to that incident) gives the driver its own dedicated `e2-highmem-4` VM instead of
   competing for the shared AO host's memory pool — confirms the root-cause diagnosis in
   `/plans/archive/2026_08/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md` was correct
   (RSS pressure / resource contention, not a code bug in the checker itself).

2. **NEW finding — combining `--require-captured` with the `live` leg in ONE invocation incorrectly gates live-leg cell
   selection by the same "genuinely captured on some day" filter as force/skip.** The skill's own §4 documents the live
   leg as a SEPARATE invocation without `--require-captured`/`--auto-day` — I initially combined all 4 legs into one
   call per asset_group to halve the VM count, which silently zeroed DEFI's live coverage (0 real live cells in the
   combined run, vs. 9 real live cells once run separately without `--require-captured`). Root cause, confirmed in
   `pipeline_e2e_check.py:_resolve_shard_day()`/the per-shard loop (~line 2582): when `shard_day is None` (no
   genuinely-captured day found under `require_captured=True`), the code marks **every** leg in `shard_legs` — including
   `live`, which doesn't need historical capture, just a working connection right now — as
   `skipped/no_captured_data_for_cell`. **Fix applied this run**: launched a SEPARATE live-only driver VM per
   asset_group (`--legs live --mvp-only`, no `--require-captured`/`--auto-day`), exactly matching the skill's documented
   §4 shape. This recovered real live coverage for DEFI (0→9 cells), CEFI (0→12 cells, though still timeout-bound before
   DERIBIT), and confirmed genuine SPORTS/TRADFI/PREDICTION live health at scale. **Suggested follow-up**: the skill doc
   (`cursor-configs/skills/data-pipeline-check-mtds/SKILL.md` §1a) currently shows a combined
   `--legs force,skip,live,canonical --require-captured` example as if it's a safe default — it should either warn
   against combining `live` with `--require-captured`, or the underlying script should special-case `live` to bypass
   `require_captured` gating (matching how it already conceptually "always forces" per the existing §4 prose). Filed as
   follow-up action item below.

3. **The wall-clock safety timeout (`exit_code=3`, SIGALRM → `os._exit(3)`) skips `write_report()` entirely** — a real,
   large sweep (CEFI's 225-shard Tardis-serialized matrix, SPORTS-combined's 110-shard matrix) that makes genuine
   progress but doesn't finish within the 3600s default loses ALL of that progress from the OFFICIAL report artifact;
   it's only recoverable via manual `run.log` archaeology (which this doc did, for CEFI and DEFI-live specifically).
   This is a distinct, less severe cousin of the 2026-08-06 "process killed silently" finding — the difference is this
   timeout is INTENTIONAL and clearly signposted (`exit_code=3`, a specific log line), so it's diagnosable, just not
   self-reporting. **Suggested follow-up**: either raise `--wall-clock-timeout-sec` for known large/Tardis-serialized
   asset_groups (CEFI, SPORTS), or add incremental/checkpointed report writes (flush partial results periodically, not
   only at the very end) so a timeout doesn't discard already-proven cells.

4. **GCS report-mirror collision reconfirmed** (same shape as the 2026-08-02/08-05 "separately-known" bug, now observed
   across a 10-VM fan-out rather than same-host sequential invocations): every driver VM's `write_report()` uploads to
   the identical `pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-06/` GCS path regardless of which
   asset_group or leg-set it ran — since each VM has its own empty local disk, the same-day MERGE logic in
   `write_report()`/`_merge_with_existing()` never actually merges across VMs, it just repeatedly overwrites. This doc
   worked around it the same way the 2026-08-05 report did: read each VM's OWN `run.log` directly rather than trusting
   the shared GCS path's final state.

## Action items

- [ ] [DATA] P1. Fix `enumerate_mtds_shards()` so a combined `--mvp-only` sweep no longer silently drops CEFI/SPORTS —
      already tracked, still open:
      `plans/active/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md` (repo:
      market-tick-data-service).
- [ ] [DATA] P2. Fix `--require-captured` incorrectly gating the `live` leg's cell selection (finding #2 above) — either
      special-case `live` in the per-shard loop to bypass `_resolve_shard_day`'s `require_captured` gate (it should
      always use the literal `--day`, matching "live already always forces" from §4), or update `SKILL.md` §1a to
      explicitly warn against combining `--legs ...,live` with `--require-captured` in one invocation (repo:
      market-tick-data-service, ref: this doc's finding #2).
- [ ] [DATA] P2. Investigate SPORTS live-leg's 84/110 (76%) failure rate — proven broken at scale this run, not
      previously measured at this coverage depth (repo: market-tick-data-service, market data pipeline).
- [ ] [DATA] P3. Investigate TRADFI combined run's 13/20 (65%) failure rate on the 5-cell MVP set (repo:
      market-tick-data-service).
- [ ] [INFRA] P3. Consider raising `--wall-clock-timeout-sec` for CEFI/SPORTS specifically (Tardis N=1 serialization
      makes their real matrices structurally slower than the 3600s default), or add incremental report checkpointing so
      a timeout doesn't discard already-proven cells (repo: market-tick-data-service, unified-trading-library).
- [ ] [DATA] P3. Re-run the CEFI §3b content-check (DERIBIT options_chain greeks/IV, BINANCE-FUTURES derivative_ticker
      funding/open_interest) once a run can reach DERIBIT and get real Tardis-guard headroom for derivative_ticker's
      force-write — this run's evidence was inconclusive, not failing (repo: market-tick-data-service).
