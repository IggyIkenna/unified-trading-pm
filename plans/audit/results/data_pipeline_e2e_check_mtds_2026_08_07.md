---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-08-07), cefi-headline (cefi_mtds_smoke_tester)"
summary: >-
  cefi_mtds_smoke_tester run for day=2026-08-07. Phase 0 (bucket provisioning) PASS all 5 asset groups. Phase 1
  (force+skip): 1 genuine cefi PASS (COINBASE-CDE trades); all ~30 Tardis-sourced cefi cells correctly guard-refused by
  a genuine concurrent production VM (not a bug); a separate unscoped attempt-1 OOM'd (rc=137) before reaching cefi at
  all. Phase 2 (live leg, cefi-scoped): 7/7 completed BINANCE-SPOT cells PASS (manifest-confirmed); driver continued
  async past this report. §3a DERIBIT futures_chain negative check: PASS. §3b content spot-checks: SKIPPED (no fresh
  force-leg parquet obtained this run, Tardis-contended). Two infra issue docs updated with new evidence.
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds, cefi, tardis-contention, oom]
related:
  [
    /plans/archive/2026_08/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md,
    /plans/archive/issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md,
  ]
created: 2026-08-08
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-08-07, cefi-headline"
date: 2026-08-08
auditor: cefi_mtds_smoke_tester (agt-9e871f, slot 8)
parent_epic: infrastructure_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-08-07
generated_at: 2026-08-08T04:30:00+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-08-07), cefi-headline

**Legs:** force, skip, live **Started:** 2026-08-08T01:41:10Z **Finished (this report):** 2026-08-08T04:30:00Z (Phase 2
driver continued running asynchronously past this report — see "Still in flight" below)

**Summary:** Phase 0 PASS (5/5 buckets). Phase 1 partial: 1 genuine cefi PASS, rest correctly guard-refused by real
Tardis contention, attempt-1 (unscoped) OOM'd before reaching cefi. Phase 2 (cefi-scoped live leg): 7/7 completed PASS.
§3a PASS. §3b SKIPPED.

## Phase 0 — provisioning gate

All 5 asset-group `-test-` buckets confirmed present via object-level probe (never `buckets describe`,
`storage.buckets.get` is unavailable to `unified-trading-sa`):

| Asset group | Bucket                                              | Result |
| ----------- | --------------------------------------------------- | ------ |
| cefi        | market-data-tick-cefi-test-central-element-323112   | OK     |
| defi        | market-data-tick-defi-test-central-element-323112   | OK     |
| tradfi      | market-data-tick-tradfi-test-central-element-323112 | OK     |
| sports      | market-data-tick-sports-test-central-element-323112 | OK     |
| prediction  | market-data-tick-pred-test-central-element-323112   | OK     |

## Phase 1 — force+skip matrix

**Attempt 1** (unscoped, all asset groups): driver VM `pipeline-e2e-check-mtds-20260808-014110-a016d8`. OOM-killed
(`rc=137`, explicit bash `Killed`) after 29 minutes, having only processed 8 TRADFI shards (NASDAQ, NYSE, CME×2, FX×2) —
**never reached cefi**. This is despite running on its own dedicated `e2-highmem-4` (32GB) VM, specifically sized
against the 2026-08-06 shared-host OOM incident's measured 21.9GB peak. New evidence recorded on
`/plans/archive/2026_08/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md`
(unified-trading-pm@bac60585e) — likely a distinct, real memory-growth bug in the driver's polling loop (circumstantial
suspect: the `firestore dual-write heartbeat ... failed` warning fires on every single heartbeat, never once succeeding,
for the whole 29min run — worth checking if that retry path leaks).

**Attempt 2** (retry, `--asset-group CEFI`): driver VM `pipeline-e2e-check-mtds-20260808-022238-ce5cd3`. Ran 63 minutes
(well past attempt-1's 29min OOM point — the CEFI-only scope avoided that failure mode) before aborting (`rc=3`) after
178 retries were refused by `tardis_concurrency_guard` (`TARDIS_MAX_CONCURRENT_VMS=1`). Root cause confirmed in source,
not log inference: a genuine, still-running production VM (`cefi-deribit-2019-light-20260807-194407`, running since
2026-08-07T19:45:41Z, confirmed via `gcloud compute instances list`, still RUNNING after my driver self-deleted) held
the sole Tardis slot the entire time. **This is the guard working correctly, not a bug** — confirmed against
`tardis-concurrency-guard.sh` source (`TARDIS_MAX_CONCURRENT_VMS=1`, defined at `:94`, refusal check at `:286`-`:297`;
the "5 streams (default 4)" text visible in `run.log` is a truncated fragment of the guard's own usage/help dump, not a
second cap being breached).

| Shard                                                                               | Leg        | Status                                          | Reason                                                                                    |
| ----------------------------------------------------------------------------------- | ---------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------- |
| CEFI:COINBASE-CDE:trades                                                            | force      | passed                                          | EXIT_STATUS=0 (`mtds-backfill-cefi-pipelinecheck-20260808-030832-fedea6`)                 |
| CEFI:COINBASE-CDE:trades                                                            | skip       | passed                                          | EXIT_STATUS=0 (`mtds-backfill-cefi-pipelinecheck-20260808-031122-fedea6`)                 |
| CEFI:{BINANCE-\*,BYBIT\*,BITFINEX-\*,BITGET-\*,DERIBIT,OKX-\*,UPBIT}:\* (~30 cells) | force+skip | skipped                                         | `tardis_guard_busy` — correctly refused, real concurrent production Tardis VM (see above) |
| TRADFI:{NASDAQ,NYSE}:ohlcv_1m                                                       | force+skip | passed (partial, from attempt-1 before its OOM) | real force-leg VM launched + polled successfully for both venues                          |
| TRADFI:CME:ohlcv_1m                                                                 | force      | in-flight at OOM                                | attempt-1 died mid-launch for this cell                                                   |
| TRADFI:FX:ohlcv_24h                                                                 | force      | in-flight at OOM                                | attempt-1 died mid-launch for this cell                                                   |

Verification of the guard's own CAP-EXEMPT-venue correctness (a standing gap flagged 2026-07-28) is now CLOSED using
this run's evidence: COINBASE-CDE (CAP-EXEMPT) passed cleanly with zero guard refusals despite the concurrent Tardis VM,
while every genuine Tardis venue was correctly refused — both halves of the 2026-07-28 fix confirmed live. Full
writeup + a new follow-up (checker aborts the whole run on exhausted guard-refusal retries instead of a per-cell skip)
on `/plans/archive/issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md`
(unified-trading-pm@476cbd294).

**No 3rd Phase-1 VM was launched** — the contending production VM was still running when attempt 2 aborted, so a retry
would very likely hit the identical wall; accepted this run's real, evidence-backed partial scope instead (consistent
with this issue doc's own 2026-08-06 precedent).

## Phase 2 — live leg (cefi-scoped)

Driver VM `pipeline-e2e-check-mtds-20260808-034610-5e1190` (`--asset-group CEFI --legs live --mvp-only`), launched
03:47:26Z. Live mode does NOT touch the guarded `datasets.tardis.dev` endpoint (confirmed per SKILL.md §4a and by this
run: zero guard refusals across all 8 launches, unlike Phase 1).

| Shard                               | Leg  | Status    | Manifest write confirmed       | Exit code | Note                                                                                                 |
| ----------------------------------- | ---- | --------- | ------------------------------ | --------- | ---------------------------------------------------------------------------------------------------- |
| CEFI:BINANCE-SPOT:trades            | live | passed    | yes (2 writes)                 | 1         | documented `--max-duration-seconds` artifact, not a real failure (`pipeline_e2e_check.py:2237-2243`) |
| CEFI:BINANCE-SPOT:book_snapshot_5   | live | passed    | yes                            | 1         | same                                                                                                 |
| CEFI:BINANCE-SPOT:derivative_ticker | live | passed    | yes (2 writes)                 | 1         | same                                                                                                 |
| CEFI:BINANCE-SPOT:liquidations      | live | passed    | yes                            | 1         | same                                                                                                 |
| CEFI:BINANCE-SPOT:ohlcv_1m          | live | passed    | yes (2 writes)                 | 1         | same                                                                                                 |
| CEFI:BINANCE-SPOT:perp_funding      | live | passed    | yes                            | 1         | same                                                                                                 |
| CEFI:BINANCE-SPOT:volatility_index  | live | passed    | yes                            | 1         | same                                                                                                 |
| CEFI:BINANCE-FUTURES:trades         | live | in-flight | not yet checked at report time | -         | 8th launch, still running when this report was compiled                                              |

**Still in flight**: the driver VM continues sweeping the remaining cefi MVP live cells asynchronously and will
self-delete + mirror its own authoritative report to
`gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/market_tick_data_service/2026-08-08/` on
completion (per SKILL.md §1a) — that report is the source of truth for the full live-leg matrix beyond the 8 cells
directly verified here. No sign of any genuine failure in the 7 completed cells' `run.log`s (real WS connection,
`ResourceProfiler` samples, `ManifestWriter` rows) — every raw `exit_code=1` is the known, already-documented
bounded-duration-stop artifact, confirmed by reading `pipeline_e2e_check.py`'s own handling (falls through to the
manifest check rather than treating it as an automatic fail).

## §3a — DERIBIT futures_chain negative check (structural-absence regression guard)

```
PASS: futures_chain not attempted
rows matched: 0
```

No `attempted_failed` (or any) row for `CEFI:DERIBIT:futures_chain` on 2026-08-07 — the 2026-07-15 retry-storm
regression (66,007→112,727 rows) is NOT recurring.

## §3b — Content spot-checks (DERIBIT options_chain greeks/IV, BINANCE-FUTURES funding/OI)

**SKIPPED this run.** Both required cells' fresh force-leg parquet were unavailable: `CEFI:DERIBIT:options_chain` and
`CEFI:BINANCE-FUTURES:derivative_ticker` are both Tardis-sourced and were among the ~30 cells correctly guard-refused in
Phase 1 (see above) — there is no freshly-written test-bucket parquet from THIS run to content-check. Rather than check
against stale/prior data (which would not prove anything about today's write path), this leg is recorded as untested
pending a Phase-1 retry outside the current Tardis-contention window.

## Infra findings this run (both documented + shipped)

1. **Driver OOM on unscoped sweep** — `unified-trading-pm@bac60585e`, appended to
   `/plans/archive/2026_08/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md`.
2. **Tardis-contention verification + new checker-resilience follow-up** — `unified-trading-pm@476cbd294`, closed the
   standing P3 verification gap on
   `/plans/archive/issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md` and added a new P1
   follow-up (checker aborts the whole run instead of skipping one contended cell).

## Bottom line for cefi (this role's headline)

Real force+skip proof obtained for 1 cefi cell (COINBASE-CDE trades); real live-mode proof obtained for 7 cefi cells
(all BINANCE-SPOT data types). Every other cefi Tardis-sourced MVP cell was correctly, not-a-bug, guard-refused due to a
genuine concurrent production backfill — not a data-pipeline correctness gap. The DERIBIT `futures_chain` structural
regression guard is holding (PASS). No genuine cefi write-path regression was observed anywhere in this run; the gaps in
today's coverage are fully explained by (a) an infra OOM needing further investigation and (b) legitimate,
correctly-guarded resource contention with a real production job, not by anything wrong with cefi's data pipeline
itself.
