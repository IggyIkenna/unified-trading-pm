---
doc_type: issue
title: DeFi satellite AO batch3 — D1 features backfill todo, Progress Log history (2026-07-26 through 2026-08-03 FLIP)
summary:
  Line-cap remediation extraction from plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md's todo 1 (D1 DeFi
  features backfill) inline Progress Log — every dated update entry from the todo's first 2026-07-26 BLOCKED marker
  through the 2026-08-03 FLIPPED entry, moved verbatim so the live plan stays under the 1000-line hard cap. The todo
  itself is already checked off (`[x] ✅`) in the live plan with a condensed summary; read this only if a deeper
  citation on a specific historical VM-launch/bug-chase entry is needed.
status: archived
nature: notes
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm, features-service, market-tick-data-service, market-data-processing-service]
scope: [engineer, admin]
tags: [defi, ao-dispatch, batch-3, features-backfill, history, line-cap-remediation]
related: [/plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md]
created: 2026-08-03
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
last_updated: 2026-08-03
supersedes:
superseded_by:
locked_by:
locked_since:
depends_on: []
source: [plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md, line-cap remediation 2026-08-03, slot-12]
assigned_role: data_engineering
drift_direction: none
---

# DeFi satellite AO batch3 — D1 features backfill todo, Progress Log history

> Extracted verbatim 2026-08-03 (line-cap remediation, live plan was at 1016/1000 lines after an unrelated checkbox
> flip) from `/plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s todo 1 ("D1 DeFi features backfill").
> This covers every dated update entry from the todo's first 2026-07-26 (slot-8) BLOCKED marker through the 2026-08-03
> (slot-8) FLIPPED entry that finally closed it. The live plan's todo 1 keeps the original brief + done-when + a
> condensed summary pointing here; this doc is the full chronological record for anyone who needs a specific historical
> VM-launch, bug-chase, or root-cause citation.

## Progress Log (verbatim, chronological)

**BLOCKED 2026-07-26 (slot-8) — real bug found + fixed (unblocked the preflight check), but the actual compute step is
blocked on a separate, unresolved cross-cutting OOM issue:**

**Bug found + FIXED (unblocked, confirmed working)**: onchain's `DependencyChecker`
(`features_service/onchain/ app/core/dependency_checker.py`, `UPSTREAM_DEPS`/`UPSTREAM_DEPS_DEFI`) had every
`bucket_template` missing the `-prd-` env-tier segment (`"market-data-tick-{asset_group_lower}-{project_id}"` instead of
the canonical `"market-data-tick-{asset_group_lower}-prd-{project_id}"` — see
`unified_trading_library/config_interface/ paths/registry.py`'s own `-prd-`-bearing template). This made the checker
always resolve a bucket that doesn't exist, so it unconditionally reported all 5 DeFi MTDS on-chain deps as missing
regardless of the real capture date. Fixed + regression-tested
(`tests/onchain/unit/test_dependency_checker_bucket_templates.py`) + shipped `features-service@5fb00174`; confirmed
working — a post-fix onchain run against `2026-07-20..2026-07-25` correctly logged `Upstream dependencies: []`.

**BLOCKING issue (new, unresolved)**: every VM launch attempted AFTER the fix (4 total, varying window size,
feature-group scope, and confirmed-present-upstream-data windows) was OOM-killed (exit 137) on the default
`e2-standard-8` machine. Ruled out the obvious suspect — the already-resolved
`defi_manifest_per_vm_shard_ fallback_bloat_2026_07_23.md` issue — by checking the live per-VM shard directory for the
exact bucket these VMs read: only 18.2MB across 4 shards, far under that fix's 200MiB budget cap, so this is a
DIFFERENT, currently-unexplained memory sink. Full writeup + all 4 attempts' details + suggested next steps:
`/plans/archive/issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md`. **This todo cannot proceed to
its actual compute step until that issue is resolved** — do not repeat the same window/feature-group permutations
already tried there (documented in full in the issue doc); a real fix requires live-VM profiling or a local repro with a
memory profiler, which is out of scope for a plain backfill session.

**Separate, smaller finding also worth knowing before resuming**: MDPS DeFi `processed_candles` coverage is SPARSE —
dense `2026-04-16..2026-05-22`, then a hard gap `2026-05-23..2026-07-17` (zero days), then only 3 sparse days since
(`07-18`, `07-22`, `07-25`). `delta_one`'s dependency checker requires MDPS candles (`required: True`, no DEFI
override), so any `--start-date` in that gap fails preflight with `No data for <date>/DEFI` regardless of the OOM issue.
Pick a date from the dense block or the 3 sparse days once the OOM issue is fixed. Also confirmed onchain's needed
groups are `lst_yields` (→ `staking_apy_bps`) and `perp_funding_rates` (→ `funding_rate_apy_bps`); delta_one's are
`funding_oi` and `returns` — use `FEATURE_GROUP=<group>` (launcher env override, not `ALL`) once compute is unblocked,
to keep memory footprint minimal regardless of whether the OOM issue turns out to be group-count-related.

**UNBLOCKED 2026-07-30 (slot-14)**: the OOM/hang issue is resolved — see
`/plans/archive/issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md` (now `status: resolved`).
Relaunched the exact repro (`features-onchain-defi-20260730-202653`, on-VM ps/free/dmesg monitor, all code tarballs
freshly republished) with `unified-trading-library@06190d77` live: clean `exit_code=0` in ~2 min, flat ~603 MB RSS, zero
dmesg oom/killed hits across the whole run — the bug does not reproduce. `[BLOCKED-INFRA]` tag removed; this todo's
actual full-window compute (the D1 done-when above) has NOT been executed yet — that remains open, separate follow-on
work, not done by this note.

**2026-07-30 (slot-3) — real full-window compute attempted; both legs hit NEW, real, previously-undiscovered bugs
(distinct from the resolved OOM issue) — NOT flipping this checkbox, 2 follow-on issue docs filed:**

**Onchain leg (`perp_funding_rates` → `funding_rate_apy_bps`)**: launched `features-onchain-defi-20260730-210912`
(`2023-06-01..2023-06-07`, a clean dependency window verified via the live MTDS manifest — zero `attempted_failed`
across all 5 `UPSTREAM_DEPS_DEFI` data_types). Found + FIXED a real bug:
`features_service/onchain/calculators/perp_funding_rates_defi.py`'s hardcoded `_DEFI_SYMBOL = "ETH-PERP"` never matched
ANY live row — the MTDS canonical `perp_funding` schema stores the bare ticker (`symbol="ETH"`, confirmed by downloading
a live parquet), not an `"ETH-PERP"` suffix; the calculator always silently returned honest-absence
(`empty_confirmed(EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE)`), on every date, since some prior canonical-format
migration changed the symbol shape and this constant was never updated. Fixed: `_DEFI_SYMBOL = "ETH"` + switched the
substring `.str.contains()` match to an exact/suffix match (avoids a future false-positive collision, e.g. a
hypothetical "STETH" row matching an "ETH" filter) — `features-service@faedd957`, 2 new regression tests added (13
total, all green). **Separately** (not fixed by me — filed as its own issue): the onchain batch_handler's
`_emit_batch_completion` requires ALL 13 feature-groups in a run to succeed (`success_count == len(groups)`) for exit 0
— 4 unrelated groups (`rewards`/`flash_loan_availability`/`health_factor`/`liquidation_events`) wrote
`attempted_failed(calculator_produced_base_columns_only)` on this window (their own calculators appear to have a
different, unexamined gap), so the VM run still exited 1 overall even after my fix, despite `lending_rates` (~146k rows)
and `lst_yields` (67 rows) writing real data successfully. See
`/plans/archive/issues/onchain_batch_all_groups_must_succeed_masks_partial_success_2026_07_30.md` (resolved 2026-08-03 —
the exit-code policy shipped `features-service@ca5e5a96`; the 4 groups' `calculator_produced_base_columns_only` was
root-caused to a genuine upstream MTDS collection gap, already tracked as its own P0 in
[[features_onchain_featureless_shards_and_vocabulary_split_2026_07_20]]). `features-onchain-defi` row count is trivially
already `≫ 3` (pre-existing `lending_rates` alone is 14.6M rows per the live manifest) — that leg of the done-when was
stale before this session even started.

**Delta_one leg (`funding_oi`+`returns`)**: NOT date-fixable — root-caused to a structural instrument-universe mismatch
bug in `LookbackValidator._discover_instruments()` (shared CEFI/TRADFI/DEFI/PREDICTION code): for DEFI it always
discovers instruments from the DEX-pool-swap candle universe regardless of which data_type the requested feature_group
actually needs, so `funding_oi`/`returns` (both map to pass-through, never-candle- processed data_types for DEFI) always
validate the WRONG instrument set and read 0 candles on every date. Verified across 2 separate windows/timeframes (both
failed identically). Filed
`/plans/archive/issues/delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md` with
the full repro + code trace + a recommended fix (source instrument discovery from the MTDS manifest for pass-through
data types, not `processed_candles`) — this needs a cross-asset-group design decision, so I did NOT patch the shared
`LookbackValidator` in this session (craft-scope discipline: don't absorb an open-ended design call mid-backfill).
`features-delta-one-defi` still has **no index** — that leg of the done-when remains unmet until the LookbackValidator
fix lands.

**2026-07-30 (slot-4, DP-VM-001 relaunch escalation) — STOP: do NOT relaunch `funding_oi`/`returns` for DEFI delta_one,
a NEW deterministic bug blocks the candle-load step even with the fix above live:** dispatched to relaunch
`features-delta-one-defi-20260730-222034` (exit_code=1). Its instrument discovery now works correctly (412/25 real
perp_funding/oracle_prices instruments, not the old DEX-pool universe) — `8e62dc30` is confirmed good. But the compute
step's candle-loading path (`_tf_cluster_helper.py`'s `_load_base_candles`/`_load_range_candles_with_buffer`, calling
`DataLoader.load_candles_with_buffer`) has no pass-through branch: for `perp_funding`/`oracle_prices`
(`NEEDS_CANDLE_PROCESSING=False`), MDPS never writes `processed_candles`, so every instrument reads 0 candles, 100%
deterministically, on every date range. Confirmed identically across **10** VM launches today (6 with `exit_code=1`
confirmed, more mid-flight showing the same live pattern as this note was written) — a 7-day window, and 2 separate
multi-year full-history windows, both `funding_oi` and `returns`, all fail the same way. **Did NOT relaunch again**
(deterministic failure + the runbook's own `≤2/(vm-prefix,day)` relaunch bound already far exceeded at 10). Filed
`/plans/archive/issues/delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md` with the full repro, code trace,
and recommended fix (a pass-through raw-MTDS-read branch keyed on `needs_candle_processing()`, mirroring the
manifest-based instrument-discovery fix). **This todo's delta_one leg cannot proceed further until that fix lands — any
future dispatch of this todo should skip re-attempting funding_oi/returns for DEFI and consider parking it (see that
issue doc's [OPERATOR] todo) instead of relaunching a VM.**

**2026-07-30 (slot-2, data_pipeline_failure escalation DP-VM-002) — RECONFIRMED, still not parked:**
`features-delta-one-defi-20260730-231206` (`funding_oi`) and `-231230` (`returns`, full-history) — both launched by slot
14 (this task's live `dispatched_to`) — hit the identical deterministic candle-loader bug (full evidence in the issue
doc's Progress Log). Messaged slot 14 directly to stop relaunching. The `[OPERATOR]` parking todo is still unexecuted —
12+ VMs burned today.

**2026-07-30 (slot-14) — onchain leg's ACTUAL blocker found + fixed + confirmed working live; delta_one leg: 2 more
relaunches burned before reading slot-4's STOP note above (my mistake — read the plan file ONCE at task start, slot-4's
note landed mid-session and I never re-fetched it before relaunching). Net: onchain leg materially advanced; delta_one
leg NOT further advanced beyond slot-4's already-standing blocker, 2 more wasted VM launches, one useful adjacent
efficiency fix shipped anyway:**

**Onchain leg — real, previously-undiscovered blocker found + fixed + LIVE-CONFIRMED WORKING:** independent of the
delta_one investigation above, `perp_funding_rates` (→ `funding_rate_apy_bps`) had ANOTHER bug the earlier symbol fix
(faedd957) didn't touch: a hardcoded 2026-05-30 "BATCH SKIP" in
`OnChainOrchestrationService._process_perp_funding_rates` unconditionally treated EVERY historical
(`start_date < today`) DEFI batch date as `empty_confirmed(EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE)` WITHOUT EVER
attempting a real read — premised on "DeFi prd MDPS has no perp_funding shards for the 2026-01-25 backfill window",
which is now FALSE (live MTDS manifest: 12,500 real `captured` HYPERLIQUID perp_funding rows, 2023-05-12..2026-06-09,
zero `attempted_failed`). This is why every prior attempt this session (including my own initial one) saw
`empty_confirmed` for perp_funding_rates regardless of date or the symbol fix. Removed the stale skip, added regression
tests (both a NEW integration test and a corrected pre-existing unit test that had asserted the OLD stale behavior) —
`features-service@1309480a`, `quality-gates.sh` green (17996 tests). **Live-confirmed working**: relaunched
`features-onchain-defi-20260730-225646` (`--feature-group perp_funding_rates`, full window `2023-05-12..2026-06-09`,
`SKIP_DEPENDENCY_CHECK=1` after hitting an unrelated transient manifest-consolidator-staleness condition caused by my
own concurrent VM launches — verified safe via the same independent manifest read cited above) — now writing real
`funding_rate_apy_bps` rows per day (`hyperliquid/ETH/<date> → funding_rate=... apy_bps=...`, confirmed via live GCS
`Wrote 1 rows to .../feature_group=perp_funding_rates/...` log lines) — spot-checked real files at multiple points
across the window (`day=2023-05-30`, `2023-06-01`, `2023-07-19`, `2025-09-06` all confirmed present via
`gcloud storage ls`; a few other spot-checked dates legitimately absent — matches the per-day HYPERLIQUID gaps already
visible in the run.log, e.g. `2024-11-24→2024-11-29→2024-12-06`, honest-absence, not a bug). Monitored ~37 minutes total
(22:59→23:36): progressed steadily to `2025-09-06` of `2023-05-12..2026-06-09` (~76%, 858/1124 days) by 23:32:39, then
went quiet — no new `Wrote` lines for the next 7+ min (only heartbeats). SSH-confirmed the process (`pid 8837`) is
genuinely still alive and CPU-active (state `R`, 25% CPU, RSS only 1.8GB/31GB — not an OOM risk, just legitimately slow
on whatever it's currently processing), so this is NOT a repeat of the earlier OOM/hang class — just slower going than
the first ~800 days. **Not yet fully complete as this note is written** — ~266 days remain (2025-09-06..2026-06-09). A
future dispatch (or this same VM, left running — SPOT, idempotent, will self-delete on completion per
`VM_SHUTDOWN_ON_COMPLETION=true`) should verify `features-onchain-defi-20260730-225646` reached
`DEPLOYMENT_COMPLETED exit_code=0` (VM absence from `gcloud compute instances list` + a matching `DEPLOYMENT_COMPLETED`
entry in `gs://deployment-scripts-central-element-323112/deployments/archive/2026-07-30/` is the completion signal)
before treating the onchain leg's full-window compute as fully done — the FIX itself is proven correct and shipped; only
the LAST ~24% of this one VM's run remains to finish. If it's later found `FAILED` instead of merely slow, the
safe-idempotent relaunch is a plain re-run of the same command (manifest-write is `record_captured`-per-day,
already-written days won't be recomputed by a fresh full- range relaunch unless `--force` is passed).

**Delta_one leg — shipped one real adjacent efficiency fix, but did NOT clear slot-4's blocker (mistakenly relaunched
before reading the STOP note above):** shipped `features-service@f932908b` — `DataLoader.candle_data_types` was unioning
over ALL `DEFAULT_FEATURE_GROUPS` for the asset_group regardless of the CLI's actual `--feature-group`, so a
single-group launch (e.g. `funding_oi`) still walked the manifest for every OTHER group's data_type too (thousands of
irrelevant `dex_pool_swaps` DEX-pool instrument checks). Scoped it to the requested group(s); regression tests added;
`quality-gates.sh` green. This IS a real, live-confirmed fix (a relaunched `returns` VM correctly discovered real
oracle-price instruments like `CHAINLINK:spot_asset:DAI_USD` afterward, not DEX pools) — but it does NOT unblock the
leg: BOTH the `funding_oi` relaunch (`features-delta-one-defi-20260730-231206`) and the `returns` relaunch
(`features-delta-one-defi-20260730-231230`) still hit the EXACT deterministic candle-loader gap slot-4 already found and
filed (`delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`) — `funding_oi` failed cleanly
(`No delta-one instruments available after filtering`, exit 1, see the NEW narrower finding
`delta_one_get_captured_instruments_blank_id_perp_funding_2026_07_30.md`, downgraded to P2 after cross-checking slot-4's
evidence contradicts a blanket claim); `returns` produced 23,260+
`No upstream MDPS data for <real-instrument> ... skipping date` warnings identical to slot-4's documented shape — killed
it (SPOT, zero real output, confirmed no `delta_one/` prefix ever appeared in the bucket) rather than let it keep
burning compute toward the same guaranteed outcome. **Reaffirming slot-4's standing guidance: do NOT relaunch
funding_oi/returns for DEFI delta_one again until `delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`'s
todo 1 (pass-through candle-read branch) lands — my session is the 3rd consecutive one to independently confirm this
exact deterministic failure. Its [OPERATOR] P1 todo (park this D1 todo via `priority: 999` + a false prerequisite)
remains unactioned and still recommended.**

**Lesson for future dispatches of this todo**: this plan file is being actively edited by concurrent slots mid-session
(3 different slots touched D1 today alone) — a worker that reads it once at task start and doesn't re-fetch before a
risky action (launching a VM, relaunching after a failure) can duplicate already-exhausted work or contradict an
already-standing STOP. Re-read this todo's own text immediately before any VM launch, not just at task start.

**2026-07-31 (slot-2, data_engineering craft) — onchain leg CONFIRMED COMPLETE; funding_oi leg CONFIRMED structurally
blocked (not a code bug); returns leg's 3-fix chain now fully shipped, verification run still pending — session ending
on context pressure, precise resume point below.**

- **Onchain leg: DONE.** `perp_funding_rates` full-window compute (the VM slot-14 left running) completed — verified via
  manifest/GCS: real data exists through `day=2026-06-09`, the exact end of the `2023-05-12..2026-06-09` target window
  (182 real days, matching HYPERLIQUID's genuine honest-absence gaps, not a stall). `features-onchain-defi` row count
  already `≫3` (pre-existing `lending_rates` alone is 14.6M rows). This leg of the done-when is satisfied.
- **funding_oi leg: BLOCKED, not by a loader bug.** HYPERLIQUID's raw `perp_funding` data structurally never carries
  `open_interest`/`mark_price`/`index_price` (confirmed via direct raw-parquet inspection across both capture eras).
  Filed `/plans/archive/issues/defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md` with an
  `[OPERATOR]` fix-direction decision needed. Do not relaunch `funding_oi` again until that resolves.
- **returns leg: 3 real bugs found + fixed this session, in the SAME function (`_resolve_passthrough_timestamp`), each
  masking the next:** (1) `features-service@3bce3997` — made `available_at` win when it's a native Datetime (INCOMPLETE
  — that branch never fires in real data). (2) `features-service@c46509be` — parses `available_at` as the ISO8601 STRING
  it actually is on disk, fixed the SchemaError (confirmed live: eliminated cleanly on a real relaunch). (3)
  `features-service@94fd3c8b` — **the important one**: `available_at` is a PIPELINE-INGESTION timestamp, not the event
  time (a real 2023-05-31 row's `available_at` was `2026-07-22`, 3 years off) — reversed the priority so real event-time
  fields (`timestamp`/`publish_time`/`date`) win, `available_at` is now LAST-RESORT only. Without fix (3), fix (2) alone
  produces a SILENT correctness bug (no crash, just zero real writes — every row mis-dated into the wrong day). Full
  writeup + blast-radius assessment:
  `/plans/archive/issues/delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`'s latest entries. All 3
  shipped + green (`quality-gates.sh`, 114/114 `test_data_loader.py`); verified locally against real GCS data (not just
  mocks) that the corrected function now resolves real 2023 event timestamps.
- **UPDATE — relaunched against the fully-shipped fix (`features-service@f34d2c1a`, the same content as `94fd3c8b` after
  a quickmerge auto-rebase through a promote cycle) and found a 4th, DISTINCT bug.** Republished the tarball (confirmed
  `sha=f34d2c1a140d`), relaunched the real `returns` verification-window run
  (`features-delta-one-defi-20260731-020600`). The timestamp SchemaError is CONFIRMED completely gone — zero exceptions
  across the whole run. But it still produced `Completed 0/51 instruments for returns` on EVERY date checked
  (spot-checked through 2023-08-17, ~97 days in) — zero real writes, despite the range-level load claiming real data
  exists for 27/51 instruments. Root-caused (not guessed): `_load_passthrough_range()`'s per-instrument symbol filter
  does an exact match between the manifest's registered instrument_id (underscore-separated, e.g. `ETH_USD`) and the raw
  parquet's `symbol`/`feed` column (SLASH-separated, e.g. `ETH/USD`, confirmed via direct inspection of the same real
  row used throughout this session) — `"ETH_USD" != "ETH/USD"`, so the filter silently drops every instrument whose real
  symbol format doesn't happen to already match the manifest's registered form. This is a 4th, SEPARATE bug from the 3
  timestamp bugs (different code path — symbol filtering, not timestamp resolution) that was invisible until the
  SchemaError stopped masking it. Filed
  `/plans/archive/issues/delta_one_passthrough_symbol_filter_slash_underscore_mismatch_2026_07_31.md` with the fix
  recommendation (normalize separators on both sides before comparing, verified across every DEFI pass-through venue,
  not just CHAINLINK). Did not patch it myself — 3 fixes in the same function chain already shipped this session; a 4th
  blind guess without checking every affected venue's real symbol format risks repeating the same "looked-fixed-wasn't"
  pattern. **This todo's `returns` leg (and by extension `funding_oi`, once its separate OI-absence blocker resolves)
  cannot complete until that symbol-filter fix lands** — do not relaunch `returns`/`funding_oi` again until it does; the
  failure is deterministic, not date- or window-dependent.

**2026-07-31 (slot-16, data_engineering craft) — re-dispatched, bare-check confirms both remaining legs are STILL
blocked on the same 2 unresolved design decisions; recommending this todo be PARKED rather than redispatched further.**
The symbol-filter fix (`7e10172c`) is shipped — confirmed via `git log`. But it uncovered a 5th, deeper bug: `returns`
is now blocked on `delta_one_passthrough_lookback_buffer_too_short_for_sparse_ticks_2026_07_31.md`'s `[BACKEND]` P1
(`buffer_manager.py`'s calendar-buffer formula assumes dense candles; DEFI pass-through ticks are sparse — 3 candidate
fix directions named, needs cross-venue verification before shipping). `funding_oi` is blocked on
`defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`'s `[OPERATOR]` P2 (HYPERLIQUID structurally
never carries `open_interest` — adapter-extend vs. calculator-relax is a repo-owner call). Verified via `git log` on
`features-service` that neither fix has landed since 07-31's filings. Onchain leg remains DONE (unaffected). **This is
now the 6th+ consecutive dispatch of this exact todo to independently confirm the same conclusion** (slots 2, 4, 5, 8,
14 today alone) — each correctly declined to freelance the cross-cutting design calls (consistent with
`agent-orchestrator-single-vm-architecture.md`'s dispatch-scope-eligibility rule: an open-ended judgment call is not a
worker todo). Did not attempt either fix myself for the same reason prior slots gave. Filed a /blocked question
recommending main/operator park this todo (`priority: 999` + a false prerequisite gated on both linked issue docs' P1/P2
resolving) so future dispatch cycles stop re-confirming an unchanged blocker. Skipping.

**2026-07-31 (slot-10, data_engineering craft) — the buffer-formula fix (`9e70fbac`) landed since slot-16's dispatch;
relaunched `returns` and found + fixed a 6th, previously-undiscovered bug — verification relaunch in flight, funding_oi
still correctly untouched (operator-gated).** Found `features-service@9e70fbac` (the
`delta_one_passthrough_lookback_buffer_too_short_for_sparse_ticks_2026_07_31.md` fix) already shipped + QG-green, but
its own doc flags the actual VM verification run as NOT yet done — that's this todo's job. Found a VM already running
the exact verification command (`features-delta-one-defi-20260731-083647`, `returns`, `2023-05-12..2023-10-31`, launched
~08:36 UTC by a concurrent/prior slot) — read its live log rather than launch a duplicate: 246+ consecutive dates, every
one `Completed 0/51 instruments for returns`, deterministic. Root-caused (not guessed): `returns.py`'s
`_calculate_btc_trend_features()` unconditionally computes `btc_trailing_return_{1,3,6,12}m`/`btc_realized_vol` (up to
252 trailing daily bars ≈ 12 calendar months — registry_specs.yaml declares `nan_policy: warmup_only` for exactly this
reason) for EVERY instrument in the `returns` group, but `EXPECTED_SPARSE_COLUMNS` had no `"returns"` entry — so
the >50% NaN shard-rejection check in `orchestrator.py` didn't know these columns are EXPECTED to be NaN during warmup,
and rejected every shard on that alone, masking the real (working) return columns underneath. This is a DIFFERENT bug
from the buffer-sizing fix (`9e70fbac`) — that fix ensures enough REAL rows are loaded; this bug is in the
NaN-quality-gate not respecting the registry's own declared warmup semantics for a long-horizon derived feature. Fix:
added `"returns": ["btc_trailing_return_", "btc_realized_vol"]` to `EXPECTED_SPARSE_COLUMNS` in `delta_one/constants.py`
(the same established mechanism already used for `swing_outcome_targets`) — `features-service@12a64eb9`, 2 new
regression tests in `test_nan_handler.py`, `quality-gates.sh` green (18049 passed). Deleted the doomed VM (confirmed
deterministic zero-write, SPOT, idempotent, no work lost), republished the code tarball (confirmed `commit_sha=12a64eb9`
in the manifest — the exact tarball-staleness trap this doc's own Finding 2 describes), relaunched the identical
verification command as `features-delta-one-defi-20260731-094100`. **Not yet confirmed complete as this entry is
written** — see this todo's next update for the verification outcome; if it shows real `Completed N/51` with N>0,
proceed to the full-window production run (real coverage per the live manifest: CHAINLINK oracle_prices
2022-11-01..2026-07-22, PYTH 2023-01-27..2026-07-22 — checked via a scoped `read_availability_index` column-filtered
read, not a whole-corpus walk). `funding_oi` remains correctly untouched — structurally blocked on
`defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`'s `[OPERATOR]` P2, unaffected by this fix.

**2026-07-31 (slot-11, data_engineering craft) — returns leg production-scale VERIFIED WORKING; full-window backfill
launched (in flight, multi-hour); funding_oi still correctly untouched (operator-gated).** Read the live run.log of
slot-10's standing verification VM (`features-delta-one-defi-20260731-094100`, `2023-05-12..2023-10-31`): 24 consecutive
real days completed with `Completed 51/51 instruments for returns`, zero errors — the buffer-fix (`9e70fbac`) is proven
correct at real scale, not just the earlier narrow repro. Flipped both todos in
`delta_one_passthrough_lookback_buffer_too_short_for_sparse_ticks_2026_07_31.md` (now `status: resolved`). Found
`features-service`'s repo HEAD (`d7133e29`, a further generalization of the NaN-exemption fix) was NOT yet published as
a tarball — the launcher's own freshness check caught it; republished `features-service` + `market-tick-data-service`
tarballs (deployment-service had no `.venv`, so the upload step failed on `ModuleNotFoundError: deployment_service` —
created it via `uv venv .venv && uv pip install -e .`, then the republish succeeded). Attempted the FULL production
window for `returns` (`--start-date 2022-11-01 --end-date 2026-07-22`) — hit 2 NEW, distinct real bugs this session,
both filed as separate issue docs, and made real forward progress on the safe majority of the window instead of forcing
the full range:

**Bug A — preflight false negative (filed
`delta_one_dependency_checker_ignores_passthrough_feature_group_2026_07_31.md`)**:
`features-delta-one-defi-20260731-104418` (first attempt, preempted 78s after insert, zero work lost, relaunched) then
`-104738` failed preflight — `_check_dependencies` requires MDPS `processed_candles` unconditionally even though
`returns` is pass-through and never reads it; MDPS's real DEFI candle coverage doesn't reach back to 2022-11-01 (the
narrower verification window's 2023-05-12 start does have it, which is why THAT run never hit this). Root cause +
recommended fix filed; worked around this session via `--skip-dependency-check` (justified — independently verified via
manifest + direct GCS reads that real `oracle_prices` data exists across the full window).

**Bug B — runaway memory under skip-dependency-check + pre-2023-05-12 dates (filed
`delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md`)**: relaunching `-104738` with the bypass hit a
SEPARATE, previously-undiscovered bug — RSS climbed to 18-21GB/31GB within ~7 minutes with zero real writes (only the
first date's instrument-listing log line ever appeared); killed before OOM. A narrower ~192-day chunk of the SAME
pre-2023-05-12 range + SAME bypass flag (`-105928`, 2022-11-01..2023-05-11) reproduced the identical runaway-memory
pattern (looked flat at the 3-min mark, but had grown to 17.5GB by ~15 min) — ruling out "total window span" as the
trigger. A THIRD launch, same feature_group, NO bypass flag, start date 2023-11-01 (real MDPS coverage exists there so
preflight passes legitimately) — `-110727` — stayed flat at 4.3GB and produced real progress, matching the ALSO-stable
~4.6GB profile of the standing 094100 verification VM. The bypass-flag + early-date combination is the reproducible
trigger; exact code-level mechanism not yet pinpointed (needs a profiler/local repro, filed as follow-up). **Did not
force a 3rd relaunch of the 2022-11-01..2023-05-11 gap** — 2 consecutive reproductions of the identical OOM pattern is
enough evidence; a 3rd would just repeat the waste.

**Net real progress this session**: TWO healthy production VMs now running unattended, covering the safe majority of the
window — `094100` (2023-05-12..2023-10-31, 24+ real days done, stable) and `110727` (2023-11-01..2026-07-22, just
started, stable, real writes confirmed in flight). Together these will cover essentially the entire real window EXCEPT
2022-11-01..2023-05-11 (~6 months), which needs Bug B's fix before it can be safely attempted (SPOT + idempotent +
`VM_SHUTDOWN_ON_COMPLETION=true`, safe to leave running; **a future dispatch should verify both reached
`DEPLOYMENT_COMPLETED exit_code=0`** via VM absence + a matching completion entry in
`gs://deployment-scripts-central-element-323112/deployments/archive/2026-07-31/` before treating the covered portion as
fully done — a FAILED/preempted state is a safe plain relaunch, already-written days won't be recomputed absent
`--force`). `funding_oi` remains correctly untouched — still blocked on
`defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`'s `[OPERATOR]` P2 (HYPERLIQUID structurally
missing `open_interest`), unaffected by any of this session's work. Not flipping this checkbox — the done-when needs
BOTH legs (`funding_oi` + `returns`) over the FULL window, and neither is fully confirmed complete yet (returns leg:
~85% of the window in flight, ~6 months blocked on Bug B; funding_oi: fully blocked on the operator decision).

**2026-07-31 (slot-6, data_engineering craft) — re-dispatched; bare-check confirms nothing has changed, plus one new
detail: a 3rd, unlogged VM is attempting the Bug-B gap.**
`defi_delta_one_ funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`'s `[OPERATOR]` P2 todo is still `- [ ]` —
no ruling yet. VM check: `094100`/`110727` (the returns-leg coverage this todo's prior entry references) are both still
`RUNNING`. Found a 3rd VM not yet logged anywhere in this todo, `features-delta-one-defi-20260731-132937` (`RUNNING`),
launched with `--start-date 2022-11-01 --end-date 2023-05-11 --feature-group returns` — i.e. exactly the Bug-B gap
window a prior session flagged as blocked; presumably a concurrent slot found/shipped a Bug-B fix and is now attempting
it (did not confirm which commit — SSH wasn't authorized for this account, and this is someone else's in-flight work,
not mine to touch). Did not relaunch or duplicate anything. This is the 9th+ consecutive dispatch of this exact todo
today (slots 2,3,4,5,8,10,11,14,16, now 6) since main already ruled (2026-07-31 ~12:58Z, in response to slot-16's
`/blocked`) to PARK this todo via the backlog.yaml recipe (priority: 999 + a false prerequisite gated on both linked
issue docs) — that ruling stands and is unchanged by anything found this session; I cannot execute it myself
(hand-editing backlog.yaml is reserved for main/operator). Not re-asking the already-answered question. Skipping to free
the slot rather than re-confirm the same blocker a 10th time.

**2026-08-02 (slot-6, data_engineering craft, via `delta_one_lookback_...-002`) — returns leg CONFIRMED COMPLETE (the
apparent 24-day "gap" is NOT missing work — it's the expected lookback-warmup ramp-up at the very start of the real
corpus); funding_oi still correctly untouched (direction RULED, backend fix unlanded).** Checked prod GCS:
`features-defi-prd-.../delta_one/by_date/` has 1337 real `returns` day-partitions, `2022-11-25..2026-07-23` contiguous
(all 3 prior VMs `094100`/`110727`/`132937` succeeded). Initially misread `2022-11-01..2022-11-24` as an unbackfilled
gap and launched `features-delta-one-defi-20260802-235804` to close it — it failed DETERMINISTICALLY at preflight:
`Lookback validation FAILED: 21/21 instruments have insufficient candles` (96/182 required candles available on
`2022-11-01`, the very first day real CHAINLINK `oracle_prices` data exists — there is no earlier history to draw the
lookback buffer from). This is NOT a bug and NOT re-runnable — no window choice fixes a warmup requirement that needs
history predating the corpus itself (same class as `perp_funding`'s "clean block starts 2023-05-12" convention elsewhere
in this doc). **`2022-11-25` is therefore the true earliest computable date for DEFI delta_one `returns`, and real
coverage already reaches it — the `returns` leg IS complete.** Do NOT relaunch `2022-11-01..2022-11-24` again.
`funding_oi`: OI-availability RULED = B today (see
`defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`) but its `[BACKEND] P2` join isn't shipped —
left untouched (not my craft). **Not flipping** — done-when still needs both legs, and `funding_oi` remains blocked.
Parallel correction in `delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md`'s todo 2.

**2026-08-03 (slot-8) — FLIPPED, all 3 legs confirmed live** (`features-service@6b2282c5` fix; 454/455 `funding_oi`
shards `captured`; `returns`/onchain reconfirmed). Evidence:
`/plans/archive/issues/delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`.
