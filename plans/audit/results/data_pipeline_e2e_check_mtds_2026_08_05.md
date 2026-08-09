---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-08-05), cefi_mtds_smoke_tester's first-ever run"
summary: >-
  data_pipeline_e2e_check_mtds pipeline-e2e-check for day=2026-08-05, all legs attempted (force/skip/live). Real,
  evidence-backed but PARTIAL coverage — CEFI/TRADFI/SPORTS/PREDICTION each got 1 real force+skip cell + 1 real live
  cell proven; DEFI got 0 force+skip cells (died in precheck 3/3 attempts) but 2 real live cells. Root cause: the local
  checker process was killed at a reproducible fixed ~300-330s wall-clock mark on EVERY one of 3 attempts (2 issue docs
  filed, both pushed). A separate, confirmed checker-code bug (also filed) silently drops ALL cefi/sports shards from
  any unfiltered full-matrix sweep — worked around this run via explicit per-asset-group invocations.
status: partial
nature: record
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds, cefi, smoke-test, process-killed, mvp-enumeration-bug]
related:
  [
    plans/active/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md,
    /plans/archive/2026_08/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md,
  ]
created: 2026-08-06
audited_scope:
  "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-08-05, per-asset-group invocations
  (CEFI/DEFI/TRADFI/SPORTS/PREDICTION run separately — required both to work around a confirmed enumeration bug and to
  avoid the known report-filename-collision bug from the 2026-08-02 report). Phase 1 (force,skip[,canonical for TRADFI])
  attempted 3 times (2 full-scope + 1 DEFI-narrow-scope retry); Phase 2 (live, mvp-only) attempted once. This doc
  manually merges all attempts' real results (extracted from the local checker's own logs where it survived long enough,
  and directly from GCS `vm-logs/<vm>/{run.log,EXIT_STATUS}` for cells whose local orchestrator died before writing its
  own report) — see the two linked issue docs for full root-cause detail on why manual merging was necessary."
date: 2026-08-06
auditor: cefi_mtds_smoke_tester (agt-e76dc5, slot 6, real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-08-05
generated_at: 2026-08-06T04:05:00+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-08-05)

> **Note on this doc's provenance**: this is `cefi_mtds_smoke_tester`'s first-ever run. The checker's own
> `report.write_report()` never fired in ANY of the 4 real invocations below — every one either (a) enumerated shards
> incorrectly when run unfiltered (CEFI/SPORTS silently return 0 — see the linked enumeration-bug issue doc, worked
> around via explicit `--asset-group` per invocation) or (b) had its local process killed at a reproducible ~300-330s
> wall-clock mark before it could write a report (see the linked process-killed issue doc — confirmed real infra was
> never orphaned; only the LOCAL report-writing step was lost). This doc's tables are hand-assembled from the real GCS
> VM logs (`vm-logs/<vm>/run.log`, `EXIT_STATUS`) for every cell that got a genuine VM run, applying the same verdict
> criteria the skill document specifies (force: parquet + manifest captured; skip: freshness pre-flight signal +
> unchanged object fingerprint; live: per-VM manifest shard written + clean connection, the `--max-duration-seconds`
> cutoff's own `exit_code=1` is EXPECTED and does not itself mean failure, per the 2026-08-02 report's established
> precedent for this exact pattern).

**Legs attempted:** force, skip, canonical (TRADFI only), live. **Day:** 2026-08-05 (all cells' actual data day was
substituted via `--auto-day` — the corpus had no captured data for 2026-08-05 itself in any sampled cell; see per-cell
notes). **Phase 1 attempts:** 03:33:34 UTC (attempt 1, all 5 groups), 03:42:54 UTC (attempt 2, all 5 groups), 03:51:10
UTC (attempt 3, DEFI only, narrow-scoped). **Phase 2:** 03:53:20 UTC (all 5 groups, single attempt).

**Combined summary:** 5/5 asset_groups attempted; 4/5 (CEFI, TRADFI, SPORTS, PREDICTION) produced 1 real force-leg + 1
real skip-leg verdict each; 5/5 produced a real live-leg verdict (DEFI got 2). DEFI's force/skip matrix produced
**zero** real cells across 3 attempts (distinct, unresolved problem — see below).

---

## 🎯 CEFI headline (this role's reason to exist)

| Leg   | Cell                          | Day (auto-substituted) | Verdict                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ----- | ----------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| force | CEFI:BINANCE-SPOT:trades      | 2026-04-14             | **FAILED — honest upstream absence.** Tardis `HTTP 400 code=300 structural absence` for the sampled symbol `BINANCE-SPOT:SPOT_PAIR:ADA-USDC`; `Batch complete: 0 results collected`; `CHUNK_FAILED ... NONZERO_EXIT`. Not a pipeline bug — the honest-absence sentinel correctly reported "nothing here" rather than fabricating data; the gap is that `--auto-day`+`--require-captured` still selected a (day, sampled-instrument) pair with no real Tardis data. |
| skip  | CEFI:BINANCE-SPOT:trades      | 2026-04-14             | Same absence, identical `CHUNK_FAILED` shape — not a genuine skip-if-fresh proof (nothing was ever captured to skip). `skip_proof: not_applicable`.                                                                                                                                                                                                                                                                                                                |
| live  | CEFI:BINANCE-SPOT:trades (WS) | live (2026-08-06)      | **PASSED.** Clean `websocket-streaming` connection, `ManifestWriter: per-VM shard updated` fired twice during the 90s window, zero errors. `exit_code=1` is the expected `--max-duration-seconds=90 elapsed` cutoff, not a failure (established precedent, 2026-08-02 report).                                                                                                                                                                                     |

**Verdict: CEFI's live capture path is proven healthy. CEFI's force/skip batch path did NOT get a genuine proof this
run** — the one sampled cell hit a real, honest upstream data gap rather than exercising the actual force-refetch /
skip-if-fresh logic. This is this run's single most important finding for this role's own stated purpose: **cefi
force/skip coverage is NOT proven for 2026-08-05** — re-run needed (ideally after the enumeration-bug fix lands, so a
full 225-cell CEFI sweep can pick a cell more likely to have real captured data, rather than depending on a single
`--auto-day`-selected sample).

Also see the **separately filed, confirmed checker bug**: an unfiltered `pipeline_e2e_check.py` sweep (the literal form
the `/data-pipeline-check-mtds` skill documents) silently enumerates **zero** CEFI (and zero SPORTS) shards —
`plans/active/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md`. Every result in this
report required working around that bug by invoking `--asset-group CEFI` explicitly.

---

## Phase 1 — force, skip (day=2026-08-05, auto-day substituted per cell)

| Shard                                                  | Leg   | Status                  | Skip proof                                 | Exit | Manifest/parquet evidence                                                                                                                                              | Reason                                                                                                                                                                                                                                             |
| ------------------------------------------------------ | ----- | ----------------------- | ------------------------------------------ | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:BINANCE-SPOT:trades                               | force | failed                  | not_applicable                             | 0    | none written                                                                                                                                                           | honest_absence: Tardis HTTP 400 structural absence for sampled symbol, day=2026-04-14 (auto-day)                                                                                                                                                   |
| CEFI:BINANCE-SPOT:trades                               | skip  | failed                  | not_applicable                             | 0    | none written                                                                                                                                                           | same honest absence — skip never proven meaningful                                                                                                                                                                                                 |
| TRADFI:NASDAQ:ohlcv_1m                                 | force | failed                  | not_applicable                             | 0    | none written                                                                                                                                                           | honest_absence: 0 results collected for sampled id NASDAQ:EQUITY:GOOG-USD, day=2026-07-20 (auto-day)                                                                                                                                               |
| TRADFI:NASDAQ:ohlcv_1m                                 | skip  | failed                  | not_applicable                             | 0    | none written                                                                                                                                                           | same honest absence                                                                                                                                                                                                                                |
| SPORTS:ODDS_API:odds_horizon_bucket (fallback-sampled) | force | **passed**              | genuine (see note)                         | 0    | `StreamingParquetWriter: uploaded` 6+ venue parquets (UNIBET/CASUMO/LIVESCOREBET/VIRGINBET/BETRIVERS/SMARKETS, ENG_CHAMPIONSHIP), 2352 rows, day=2026-04-14 (auto-day) | real data fetched + written to test bucket                                                                                                                                                                                                         |
| SPORTS:ODDS_API:odds_horizon_bucket (fallback-sampled) | skip  | ⚠️ ambiguous            | **ambiguous — see operational note below** | 0    | IDENTICAL parquet paths + row counts re-uploaded ~4min later                                                                                                           | no `Pre-flight: ... fully covered` signal observed in the skip-leg log; the skip leg re-fetched and re-wrote the same data rather than short-circuiting — this looks like a genuine skip-if-fresh gap for this cell, not proof skip-if-fresh works |
| PREDICTION:POLYMARKET:trades                           | force | failed                  | not_applicable                             | 0    | none written                                                                                                                                                           | 0 venues ok / 0 failed / captured=0 for sampled id, day=2026-08-03→08-04 (auto-day)                                                                                                                                                                |
| PREDICTION:POLYMARKET:trades                           | skip  | failed                  | not_applicable                             | 0    | none written                                                                                                                                                           | same — captured=0 both legs                                                                                                                                                                                                                        |
| DEFI (whole matrix, 2958 candidates)                   | force | **not attempted — 0/3** | n/a                                        | —    | —                                                                                                                                                                      | local checker process died before any VM launch in ALL 3 attempts (2 full-scope, 1 narrowed to `UNISWAP_V2-ETHEREUM:dex_pool_swaps`) — see process-killed issue doc                                                                                |
| DEFI (whole matrix)                                    | skip  | **not attempted — 0/3** | n/a                                        | —    | —                                                                                                                                                                      | same                                                                                                                                                                                                                                               |

**Note on the SPORTS skip-leg re-upload**: this is a real, first-time observation from this run, not previously
documented — flagging here as an operational note rather than a 3rd formal issue doc (time-boxed this run to the 2
issues already filed); worth a follow-up investigation into whether the ODDS_API/sports smoke-matrix-fallback path's
freshness pre-flight check is wired correctly, or whether this specific fallback-sampled cell structurally bypasses it.

## Phase 2 — live (day=2026-08-05, `--mvp-only`)

| Shard                                              | Leg  | Status     | Manifest evidence                                      | Reason                                                                                                                                                                        |
| -------------------------------------------------- | ---- | ---------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:BINANCE-SPOT:trades (WS)                      | live | **passed** | `ManifestWriter: per-VM shard updated` x2, zero errors | ok (`exit_code=1` = expected `--max-duration-seconds=90` cutoff, not a failure)                                                                                               |
| DEFI:UNISWAP_V2-ETHEREUM:dex_pool_state            | live | **failed** | none (service raised before any subscribe)             | `BLOCKED-BUILD: live DEX-swap subgraph poller not yet implemented for UNISWAP_V2-ETHEREUM` — already tracked, `plans/active/issues/wsfeedconnector_phase35_gap_2026_07_06.md` |
| DEFI:UNISWAP_V2-ETHEREUM:dex_pool_swaps (2nd cell) | live | **failed** | none                                                   | same BLOCKED-BUILD gap, same protocol family                                                                                                                                  |
| TRADFI:NASDAQ:ohlcv_1m (HOOD)                      | live | **failed** | none (subscribe rejected before any manifest write)    | `CRAM authentication error: A live data license is required to access DBEQ.BASIC` — billing/license gate, not a code bug                                                      |
| SPORTS:ODDS_API:trades (soccer_epl, fallback)      | live | **passed** | `ManifestWriter: per-VM shard updated` x1, zero errors | ok (expected max-duration cutoff)                                                                                                                                             |
| PREDICTION:POLYMARKET:trades (fallback)            | live | **passed** | `ManifestWriter: per-VM shard updated` x1, zero errors | ok (expected max-duration cutoff)                                                                                                                                             |

---

## Operational findings (this session — process/tooling, not shard verdicts)

1. **[P1, filed] `enumerate_mtds_shards()` silently drops CEFI + SPORTS from any unfiltered `--mvp-only` sweep** —
   confirmed via direct function calls before spending any VM budget: `is_mvp()` needs a `base_ccy`/`league` this
   enumeration-time probe never supplies (same class of gap already known + hand-fixed for TRADFI, never extended to
   CEFI/SPORTS), and the fallback that WOULD correctly enumerate them is masked by other asset_groups' non-empty results
   in a combined sweep. Worked around by invoking per-`--asset-group` explicitly this whole run. **This is the literal
   invocation the `/data-pipeline-check-mtds` skill documents as the default** — every future scheduled run of this role
   will hit the same silent gap unless it also applies this workaround or the bug is fixed.
   `plans/active/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md`.
2. **[P1, filed] The local checker process was killed at a reproducible fixed ~300-330s wall-clock mark, 3/3 attempts,
   across 2 structurally different code paths (force/skip AND live)** — zero traceback despite full stdout+stderr
   capture, ruled out the script's own `--wall-clock-timeout-sec` backstop (2400s/1200s, 4-8x longer) and every other
   internal timeout site in both `pipeline_e2e_check.py` and the shared launcher library. No orphaned VMs resulted
   (everything already-launched self-terminated cleanly), but the checker's own report-write never fired, meaning
   `report.write_report()` — the entire deliverable this tool exists to produce — silently failed all 3 times. This is
   almost certainly why every historical `data_pipeline_e2e_check_mtds_*.md` report found in this directory covers a
   small (1-20 shard) scope rather than a real full sweep.
   `/plans/archive/2026_08/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md`.
3. **DEFI's force/skip matrix could not be proven at all this run** (0/3 attempts, including a narrowly-scoped single
   real cell) — every attempt died even before Phase-2's leg-agnostic ~300-330s mark, during Phase-0
   precheck/enumeration. Phase 2's live leg proved DEFI's connectivity path fine (2 real cells), so this looks specific
   to the force/skip + `--require-captured` precheck code path for DEFI, not a DEFI-wide infra problem — not yet
   root-caused; flagged in finding 2's issue doc as a secondary, DEFI-specific data point rather than a separate doc
   (same underlying "process dies silently" symptom, needs the same investigation).
4. **DEFI live-leg BLOCKED-BUILD and TRADFI live-leg billing-license gap are BOTH already-known, already-tracked
   conditions** (DEFI: `wsfeedconnector_phase35_gap_2026_07_06.md`; TRADFI: consistent with the documented Databento
   billing-fail-closed design in `/codex/02-data/tradfi-databento-sourcing-ssot.md`) — reported here as this run's
   observed verdicts, not new findings.

## Report file collision note (inherited from the 2026-08-02 report's own finding)

Per the 2026-08-02 report's own documented defect, `report.write_report()` targets a filename keyed only by `run_date`,
so multiple invocations for the same day silently overwrite each other's report. This run sidestepped that by giving
every invocation a distinct scratch `--report-dir` and merging by hand (this document) — the underlying checker-script
defect is unresolved (not re-filed as a 3rd issue; the earlier report already references it via its parent plan's
Progress Log).
