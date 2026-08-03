---
doc_type: plan
title: DVOL-Backtestable VOL Engines — VOL_CARRY + VOL_ARB_RV_IV register-or-honest-absent
summary:
  Build the missing DVOL-index historical capture path (free Deribit public REST, no credentials) and use it to actually
  backtest VOL_CARRY + VOL_ARB_RV_IV — the only 2 of 17 VOL_* engines that don't need Tardis — then register only if the
  backtest genuinely passes.
status: complete # (was: active) 2026-08-03 -- all 5 todos done, finalized + archived
nature: process
asset_group:
  [cefi] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag:
  # exclusively Deribit DVOL-index CeFi vol trading, explicitly tagged ("cefi","volatility_index") in the registry

stage: [data, backtest]
repos: [unified-api-contracts, market-tick-data-service, strategy-service]
scope: [engineer]
tags: [strategy, v2-engine, vol-trading, backtest, deribit]
related: [/plans/active/v2_engine_venue_buildout_2026_06_15.md]
created: 2026-07-13
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 5.0
assigned_role: backend_engineer
drift_direction: advance-code
last_updated: 2026-08-03
locked_by:
locked_since:
depends_on:
supersedes:
superseded_by:
source: [v2_engine_venue_buildout_2026_06_15.md follow-up, operator decision 2026-07-13]
sequential: true
context_scope:
  [
    /plans/active/v2_engine_venue_buildout_2026_06_15.md,
    /plans/archive/2026_08/vol_dvol_backtestable_engines_2026_07_13_finalize_2026_07_30.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/epics/strategy_master.md,
  ]
---

# DVOL-Backtestable VOL Engines

> **✅ ARCHIVED 2026-08-03 — all 5 todos DONE.** Full DVOL history pulled + manifest-verified (2021-03-24→2026-07-30,
> 1955 distinct dates × {BTC, ETH}, 100% `captured`, re-measured independently by the finalize twin
> `vol_dvol_backtestable_engines_2026_07_13_finalize_2026_07_30.md`). Both VOL_CARRY and VOL_ARB_RV_IV got real
> `GroupBRunner` backtests over the full honest-intersection window (2021-03-24→2026-05-22) and both came back
> non-passing (indistinguishable-from-noise Sharpe, flat-to-negative PnL) — BLOCKED-INSUFFICIENT-EDGE, neither
> registered in `ARCHETYPE_ENGINE_REGISTRY`, both stay `not_available`. `capability-verdict-matrix.json` regenerated
> (unified-api-contracts@`14dbb6d1`) confirming 0/2 flipped. Archived alongside its finalize twin in the same commit.
> Re-open only if a concrete alternative param-sweep candidate is proposed for either engine.

> **Split out 2026-07-13** from [`v2_engine_venue_buildout_2026_06_15.md`](v2_engine_venue_buildout_2026_06_15.md) Phase
> E2. Of the 17 VOL\_\* engines, 15 are `BLOCKED-CREDENTIALS` on Tardis (stays in the parent plan, do not touch here).
> VOL_CARRY (`engine/strategies/v2/vol_trading/carry.py`) and VOL_ARB_RV_IV (`vol_trading/arb_rv_iv.py`) are the
> exception — both trade `iv_atm - rv`, which needs only the DVOL implied-vol index + the underlying's realised-vol
> close series, NOT a per-strike surface. Deribit's public `/public/get_volatility_index_data` gives BTC DVOL OHLC back
> to **2021-03-24**, no auth, confirmed live in the parent plan's 2026-06-15 probe.

## HARD CONTRACT — copied verbatim from the parent plan, applies to every todo here

**An archetype is DONE only when the engine is REAL**: genuine strategy logic, a **passing backtest artifact** via
`GroupBRunner` (`strategy-service/.../engine/strategies/v2/batch_harness.py`), unit tests, registered in
`ARCHETYPE_ENGINE_REGISTRY`, and the verdict matrix regenerated to `available`. **NEVER register a hollow/stub engine or
one whose backtest didn't actually pass** — a registered engine with no real edge makes the matrix LIE, which is worse
than honest `not_available`. If the backtest doesn't clear a real bar (not just "it ran without crashing" — a defensible
signal, non-degenerate PnL/Sharpe), leave the engine `not_available` and file a new `BLOCKED-*` todo naming exactly
what's missing.

## Ground truth (2026-07-13 gap check — do not re-derive)

- `unified-api-contracts/unified_api_contracts/registry/endpoints.py:205` already maps
  `("deribit", "volatility_index"): "DeribitVolatilityIndex"` — an endpoint reference exists, but there is **no**
  `data_type_capability.py` capability row for `volatility_index` (checked: zero hits) and **zero** MTDS handler files
  reference `volatility_index`/`dvol` — the ingestion path is genuinely unbuilt, this is real net-new work, not a
  registry-only fix like the sibling `uac_venue_registry_completion_2026_07_13.md` plan.
- `strategy_service/.../vol_trading/carry.py` and `arb_rv_iv.py` already have code comments acknowledging
  DVOL-backtestability but nothing upstream feeds them yet.
- **Canonical form (mandatory)**: register `volatility_index` as a real `data_type` in
  `unified-api-contracts/unified_api_contracts/registry/data_type_capability.py` (do not invent a different name —
  `volatility_index` is the name already used in `endpoints.py`); any captured/written parquet MUST carry the
  `pipeline_mode = {mode}_{source}[_{transport}]` hive-partition key (e.g. `batch_deribit`) LEFT of `asset_group=`, per
  `/codex/02-data/pipeline-mode-partition.md`; every bucket lookup goes through
  `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)` — **never** an inline `gs://` path or
  a hardcoded bucket string.

## Todos

- [x] ✅ [DATA] P1. Register `volatility_index` data_type capability: `data_type_capability.py` entry for
      `(cefi,     volatility_index)`, venue `DERIBIT`, `live_capable=True, batch_capable=True` (it's a REST history
      endpoint, no streaming needed). `SOURCE_PRIORITY[("cefi","volatility_index")] = ["deribit"]`. Repo:
      unified-api-contracts. — **DONE, slot 9, unified-api-contracts@`a02ce954`.** Added the `DataTypeCapability` entry
      (no `streaming_protocol`, mirroring the `prediction_canonical_question_group` REST-derived pattern — it's a
      REST-polled index, not a WS stream) + `SOURCE_PRIORITY[("cefi","volatility_index")] = ["deribit"]` exactly as
      specified. Discovered the literal one-line `SOURCE_PRIORITY` entry needed a broader closed-set cascade to actually
      round-trip (verified via the repo's own test suite, not assumed): added `PipelineMode.BATCH_DERIBIT`, widened
      `SOURCE_MODE_CAPABILITY["deribit"]` + `BATCH_CAPABLE_CEFI_VENUES` to carry the same "self-archiving vendor"
      exception already used for aster/extended/pacifica (deribit stays live/replay-only for every OTHER cefi data_type
      — tardis remains those data_types' batch archive — but is now ALSO the genuine batch source for `volatility_index`
      specifically), added an `EMISSION_LATENCY_MS_BY_SOURCE` entry (1h, matching the REST-history-endpoint cadence
      class) and an `AVAILABILITY_AT_SEMANTICS` entry (`tick_timestamp`), and updated 2 tests that hard-coded deribit's
      prior live/replay-only mode set. Verified via 718 targeted tests green (`test_source_mode_capability.py` /
      `test_source_priority.py` / `test_source_priority_pipeline_mode.py` / `test_pipeline_mode.py` /
      `test_availability_semantics.py` / `test_validity_matrix_completeness.py` + broader keyword sweep) + full
      `quality-gates.sh` green (`ALL QUALITY GATES PASSED`, sentinel matches HEAD). Hit + resolved an unrelated
      repo-wide QG-red blocker along the way (databento_classifier.py file-size + cryptography GHSA-537c-gmf6-5ccf,
      pre-existing, verified via clean `git diff --stat HEAD` on both — filed
      [`plans/active/issues/uac_qg_red_databento_classifier_filesize_and_cryptography_ghsa_2026_07_13.md`](issues/uac_qg_red_databento_classifier_filesize_and_cryptography_ghsa_2026_07_13.md),
      declared repo-blocker RB-e4b7bd5c, resolved once another slot shipped the cryptography bump). No MTDS handler
      built here — that is the next todo below, separate scope.
- [x] ✅ [DATA] P1. Build the MTDS handler consuming the existing `DeribitVolatilityIndex` endpoint mapping: capture
      DVOL OHLC (`/public/get_volatility_index_data`, resolutions incl. `86400`/`3600`, paged via `continuation`) into
      the canonical schema, `pipeline_mode=batch_deribit`, `source="deribit"`, bucket via `resolve_bucket_name(...)`,
      `classify_venue_error()` + shard isolation per the established Deribit-adapter pattern in this codebase.
      **Connectivity-test with a SMALL bounded pull only (e.g. trailing 30-90 days) to prove the pipeline** — do **NOT**
      run the full 2021→now historical pull as part of this todo. Repo: market-tick-data-service. — **DONE, slot 4,
      market-tick-data-service@`77ff475a`** (initial handler shipped at `3511ab3b`, then a real-connectivity-test bug
      found+fixed at `77ff475a`). Built `DeribitVolatilityIndexHandler` (new `collect-deribit-volatility-index`
      operation, registered in `cli/main.py`), per-day `BatchPayload` dispatch, `fetch_dvol_day()` doing
      `continuation`-cursor pagination against `/public/get_volatility_index_data` for BTC/ETH, honest-absence for
      pre-2021-03-24 (DVOL launch) days, per-currency shard isolation + `classify_venue_error`. 14 unit tests
      (pagination, CF-11 failure signalling, capture/empty/failed routing). **Runtime-verified against real production
      Deribit REST + GCS (not just unit tests)**: a real connectivity-test run caught a genuine bug unit-mocks couldn't
      — the `row_key` dict used `"day"`/`"asset_group"`, but `ManifestWriter`'s real schema uses `"date"` and has no
      `"asset_group"` column, so every manifest write raised an uncaught `KeyError` that also aborted the OTHER
      currency's turn in the shard loop (a real shard-isolation gap). Fixed both (corrected row_key shape + wrapped the
      manifest-write call in its own try/except) and re-verified: a 1-day pull (`2026-07-13`, `--venues DERIBIT`) now
      shows real captured manifest rows for BOTH currencies —
      `venue=DERIBIT data_type=volatility_index underlying=BTC/ETH day=2026-07-13 capture_status=captured     instrument_count=23 pipeline_mode=batch_deribit source=deribit`
      — with real parquet at
      `gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2026-07-13/pipeline_mode=batch_deribit/asset_group=cefi/venue=DERIBIT/instrument_type=index/data_type=volatility_index/underlying={BTC,ETH}/dvol.parquet`.
      **Note for the operator-go todo below**: the shared `availability_index.parquet` (~7.5M rows) is under heavy write
      contention from the rest of the fleet right now — a genuine manifest flush took ~9 retry attempts / ~9 min
      wall-clock to land under this session's load. Not a defect in this handler, but worth knowing before scheduling
      the full 2021→now historical pull (many more shards writing to the same contended index).
- [x] ✅ [DATA] P1. **DONE 2026-07-30 (slot-2, `data_engineering`).** RULED 2026-07-28 (operator general-theme ruling —
      no longer operator-gated, now AO-dispatchable): pulled the FULL DVOL historical series, 2021-03-24 → now, for both
      BTC and ETH, via the `collect-deribit-volatility-index` handler built in the todo above. **Ruling: full history,
      not a shorter window — go-ahead granted.** **Reasoning (operator's standing 2026-07-28 theme, applied here)**: (1)
      "full backfills/full migrations — as long as an item isn't superseded by more recent work, do it": this plan is
      confirmed still active and not superseded (checked 2026-07-28 — `v2_engine_venue_buildout_2026_06_15.md`,
      `cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`, and
      `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` all still list this plan as the live open item for
      VOL_CARRY/VOL_ARB_RV_IV); (2) DVOL is free/credential-free (Deribit public REST, no auth) so "cost under
      $100 is
      not a concern" doesn't even need invoking — this pull is $0; (3) "opt for full completions, no
      shortcuts... no cheap implementations" — a shorter recent-only window risks covering too few volatility regimes
      for a defensible backtest verdict under the HARD CONTRACT above (a false `not_available` from under-coverage is
      exactly the partial/cheap outcome the theme rules against). **This resolves `BLK-011c84cb`** (the standing
      operator-decision escalation raised 2026-07-14, still open as of the 2026-07-25 Progress Log entry below).
      **Execution**: a same-repo-family connectivity smoke-test (small 3-day range) run inline first hit a REAL memory
      spike (~17GB RSS, ignored a 120s `timeout` SIGTERM) — root-caused to `ManifestWriter.flush()`'s per-day full
      read-merge-write of the shared cefi `availability_index.parquet` (~7.5M rows), the SAME class already root-caused
      for other cefi MTDS backfills (`mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`, fixed there via
      e2-highmem-4). Killed the runaway process (exact PID, SIGTERM) per the runaway-process HARD RULE, then built +
      shipped a dedicated one-off VM launcher rather than running the full historical pull on the shared orchestrator
      host: `deployment-service@42b80f65f9f3` — new `dvol-deribit-` VM prefix (registry + launcher-registry parity,
      `test_launcher_registry.py`/`test_validate_vm_prefix_mapping.py` green) + `launch-deribit-dvol-backfill-vm.sh`
      (e2-highmem-4/250GB pd-balanced, SPOT, `VM_TASK=deribit-dvol-backfill` routed through the generic
      `VM_OPERATION`-driven dispatch branch in `setup-data-pipeline-vm.sh`, which was also extended to forward
      `VM_BATCH_DATE_CONCURRENCY` — previously only the `mtds-backfill` branch read it). Full quality-gates.sh green
      before commit (incl. the backfill-VM-disk-provisioning gate, which caught the initial 100GB disk as under the
      250GB minimum for this workload class). **Real VM run** (`dvol-deribit-backfill`, launched 2026-07-30T14:00:09Z,
      self-shutdown+self-deleted 2026-07-30T14:10:41Z on exit_code=0, ~10.5min wall-clock — no contention/slowdown
      observed running unopposed on its own VM, unlike the shared-host smoke test): manifest verification (not just
      GCS-object existence) via a direct read of the per-VM shard
      `market-data-tick-cefi-prd-central-element-323112/_index/per_vm/dvol-deribit-backfill.parquet` shows **3910/3910
      rows `capture_status=captured`** (0 `attempted_failed`, 0 `empty`) — 1955 distinct dates × {BTC, ETH}, date range
      exactly `2021-03-24` → `2026-07-30`, matching the expected 1955 calendar-day count for that inclusive window
      (`(date(2026,7,30)-date(2021,3,24)).days+1 == 1955`, verified programmatically). Both boundaries (`day=2021-03-24`
      DVOL-launch day and `day=2026-07-30` today) independently spot-checked in raw GCS before the full-distribution
      manifest check. **No partial runs, no gaps, no re-run needed.**
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-30 (slot-7, `backend_engineer`).** Wired the DVOL implied-vol index + the
      underlying's realised-vol close series as `GroupBRunner` backtest input for **VOL_CARRY** and ran the backtest —
      strategy-service@`18d7e775`. See Progress Log below for the full methodology + real results (both underlyings'
      backtests came back NON-passing — near-zero/slightly-negative Sharpe — so the next todo should leave VOL_CARRY
      `not_available` and file the `BLOCKED-*` naming this, not register it).
- [x] ✅ [SCRIPT] P1. If VOL_CARRY's backtest passes the HARD CONTRACT bar above, register it in
      `ARCHETYPE_ENGINE_REGISTRY`. If it does not pass, leave `not_available` and file a new `BLOCKED-*` todo naming the
      specific failure (e.g. degenerate PnL, insufficient sample). Repo: strategy-service. — **DONE 2026-07-30 (slot-14,
      `backend_engineer`).** Confirmed the recorded 2026-07-30 (slot-7) backtest result stands (no new methodology
      challenge, no re-run per the plan's own instruction): BTC `sharpe_ratio=-0.0063`, ETH `sharpe_ratio=+0.0461`, both
      PnL flat-to-negative (-119.76 / -191.40), win rate 22.8%/24.75% — an order of magnitude below any defensible-edge
      threshold. **Verified VOL_CARRY is NOT in `ARCHETYPE_ENGINE_REGISTRY`**
      (`strategy_service/engine/strategies/v2/factory.py` — zero hits for `VOL_CARRY`), so `not_available` is already
      the live state; no registry code change needed (nothing to revert). Filed the `BLOCKED-*` todo below naming the
      specific failure + citing the exact metrics. No code shipped this todo (a leave-as-is decision, not a
      registration) — plan-only commit.
- [x] ✅ [SCRIPT] P3. **BLOCKED-INSUFFICIENT-EDGE — VOL_CARRY fails the HARD CONTRACT bar, no further work planned
      unless a concrete param-sweep candidate is proposed.** The 2026-07-30 (slot-7) real backtest — `iv_atm` from the
      captured DVOL series, realised vol from the captured BINANCE-FUTURES `derivative_ticker` `index_price` series,
      full honest intersection window 2021-03-24→2026-05-22, `entry_vrp=0.04`/`exit_vrp=0.01` (carry.py defaults,
      untested) — came back non-passing for both underlyings: BTC `sharpe_ratio=-0.0063`, `sortino_ratio=-0.0052`,
      `total_pnl=-119.76`, `win_rate=22.8%` (29 cycles/58 fills); ETH `sharpe_ratio=+0.0461`, `sortino_ratio=+0.0360`,
      `total_pnl=-191.40`, `win_rate=24.75%` (51 cycles/102 fills). Both Sharpes are indistinguishable-from-noise, PnL
      is flat-to-negative, and win rate ~23-25% has no compensating asymmetric payoff — this is a genuine "no edge at
      the default thresholds" result, not a methodology gap (real captured data both legs, real `GroupBRunner` wiring,
      full available window). **Not scheduling a param sweep here** — `entry_vrp`/`exit_vrp` were left at defaults and a
      different threshold pair MIGHT clear the bar, but that is a fresh trading-judgment hypothesis the
      operator/quant_dev should decide to pursue, not a mechanical follow-up. VOL_CARRY stays `not_available`; re-open
      only if a specific alternative parameterization is proposed with a stated rationale. Repo: strategy-service (no
      code — decision record). — **DONE 2026-08-03 (slot-13, `data_engineering`).** This todo IS the decision record
      (filed 2026-07-30 by slot-14); no code task exists to ship. Re-verified live: `VOL_CARRY` still has zero hits in
      `strategy_service/engine/strategies/v2/factory.py` (`ARCHETYPE_ENGINE_REGISTRY`), so `not_available` still holds
      and nothing has drifted since the decision was recorded. No concrete alternative param-sweep candidate has been
      proposed since filing, so per the todo's own instruction there is no further mechanical action — flipping closed.
- [x] ✅ [SCRIPT] P1. **DONE 2026-08-03 (slot-2, `backend_engineer`).** Same backtest-then-conditionally-register
      sequence for **VOL_ARB_RV_IV** (`vol_trading/arb_rv_iv.py`) — strategy-service@`8996e3c2` (script wiring
      `8c9198da`, a scripts-package import-collision fix `8996e3c2`). Real production-data backtest run: both
      underlyings came back NON-passing (near-zero Sharpe, strongly negative PnL) — see Progress Log below for the full
      methodology + results. Verified `VOL_ARB_RV_IV` is NOT in `ARCHETYPE_ENGINE_REGISTRY`
      (`strategy_service/engine/strategies/v2/factory.py` — zero hits), so `not_available` is already the correct live
      state; no registry code change made. Filed the `BLOCKED-INSUFFICIENT-EDGE` decision-record todo below citing the
      exact metrics.
- [x] ✅ [SCRIPT] P3. **DONE 2026-08-03 (slot-12, `data_engineering`).** This todo IS the decision record (filed
      2026-08-03 by slot-2); no code task exists to ship. Re-verified live:
      `strategy_service/engine/strategies/v2/factory.py`'s `ARCHETYPE_ENGINE_REGISTRY` still has zero hits for
      `VOL_ARB_RV_IV`, confirming `not_available` hasn't drifted since the decision was recorded. No concrete
      alternative param-sweep candidate has been proposed since filing (the only stated condition for re-opening), so
      per the todo's own instruction there is no further mechanical action — flipping closed.
      **BLOCKED-INSUFFICIENT-EDGE — VOL_ARB_RV_IV fails the HARD CONTRACT bar, no further work planned unless a concrete
      param-sweep candidate is proposed.** The 2026-08-03 (slot-2) real backtest — `iv_atm` from the captured DVOL
      series, realised vol from the captured BINANCE-FUTURES `derivative_ticker` `index_price` series, full honest
      intersection window 2021-03-24→2026-05-22 (1866/1886 candidate days, same window VOL_CARRY used), `entry_gap=0.03`
      (arb_rv_iv.py default, untested), `vega_budget_per_leg=10` — came back non-passing for both underlyings: BTC
      `sharpe_ratio=0.0099`, `sortino_ratio=0.0082`, `total_pnl=-9826.53`, `win_rate=24.1%` (1786 instructions/3572
      fills); ETH `sharpe_ratio=0.0095`, `sortino_ratio=0.0080`, `total_pnl=-9612.40`, `win_rate=23.7%` (1784
      instructions/3568 fills). Both Sharpes are indistinguishable-from-noise (same bar VOL_CARRY was held to), PnL is
      strongly negative for both assets (this engine has no exit/flatten state machine — unlike VOL_CARRY, it re-enters
      a fresh straddle on EVERY day `|iv_atm - rv| >= entry_gap`, which is why trade count is ~70x VOL_CARRY's at this
      same threshold), and win rate ~24% has no compensating asymmetric payoff — this is a genuine "no edge at the
      default threshold" result, not a methodology gap (real captured data both legs, real `GroupBRunner` wiring, full
      available window, unmodified engine code — the script does not add position-tracking logic the engine itself
      doesn't have). **Not scheduling a param sweep here** — `entry_gap` was left at its default and a different
      threshold MIGHT clear the bar (a wider gap would fire far less often, closer to VOL_CARRY's trade cadence), but
      that is a fresh trading-judgment hypothesis the operator/quant_dev should decide to pursue, not a mechanical
      follow-up. VOL_ARB_RV_IV stays `not_available`; re-open only if a specific alternative parameterization is
      proposed with a stated rationale. Repo: strategy-service (no code — decision record).
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-03 (slot-15, `backend_engineer`).** Regenerated + committed
      `capability-verdict-matrix.json` — unified-api-contracts@`14dbb6d1`. **0 of the 2 engines flipped to `available`**
      (both VOL_CARRY and VOL_ARB_RV_IV failed their backtests per the two todos above and remain unregistered —
      confirmed via a live re-probe of `strategy_service.engine.strategies.v2.factory.ARCHETYPE_ENGINE_REGISTRY` in a
      fresh `strategy-service/.venv`: neither key present, 32 engines registered total). Ran
      `unified-trading-pm/scripts/openapi/generate_capability_verdict_matrix.py` against current HEAD (`bda8bfc7`); diff
      vs. the prior committed matrix (2026-07-26, `431cb79a`) is JSON-formatting normalization + the
      `generated_from_commit` bump + the missing verdict-summary block restored in `capability-orphan-report.txt` —
      summary totals are byte-identical (31168 total cells: 22517 available / 8203 blocked / 448 not_registered) and the
      VOL_CARRY/VOL_ARB_RV_IV archetype blocks are unchanged (still `not_registered(no_v2_engine)`), confirming no
      semantic drift. Full `quality-gates.sh` green before commit (sentinel matched HEAD); shipped via quickmerge,
      verified on origin (`git merge-base --is-ancestor 14dbb6d1 origin/live-defi-rollout`).

## Progress Log

(loop handoff lands here)

- 2026-07-13 (slot-13): Dispatched the `[SCRIPT] P1. Once the historical DVOL series is available (post-operator-go)...`
  todo, but its predecessor `[OPERATOR] P1. BLOCKED-OPERATOR-DECISION` todo is still unchecked and explicitly "Not
  dispatchable — stays visible, never auto-ingested." No historical DVOL series has been pulled yet, and I can't grant
  the operator-go myself. Skipping for this slot rather than working around the missing decision. Note for whoever
  authors the next backlog-affecting plan edit: this todo has no `depends_on`/`conditions` gate tying it to the OPERATOR
  todo above it, so `sequential: true` alone didn't stop it from being dispatched independently — worth adding a
  `prereqs.conditions` gate (e.g. `dvol-historical-pull-approved`, flipped true once the operator go lands) if this
  recurs.
- 2026-07-14 (slot-14): Same task dispatched again, same wall — the OPERATOR P1 BLOCKED-OPERATOR-DECISION todo is still
  unchecked a day later. Rather than silently re-skip, filed `/blocked` question `BLK-011c84cb` putting the actual
  decision (full 2021-03-24→now vs. a shorter window) in front of the operator/main via the dashboard, then
  `/skip-current-task`. Confirmed via the live backlog API (`GET /api/backlog`, task
  `vol_dvol_backtestable_engines-003`) that the entry still carries no `prereqs`/`conditions` field — slot-13's
  suggested fix was never applied. This is now a 2-slot repeat; whoever resolves `BLK-011c84cb` should also add the
  `prereqs.conditions` gate at the same time so a 3rd slot doesn't burn a dispatch on this.
- 2026-07-17 (slot-7): **3rd repeat-dispatch** — `vol_dvol_backtestable_engines-001` dispatched to slot-7, still no
  operator-go (OPERATOR P1 todo remains `[ ]`; last plan edit is slot-14's note above, no DVOL history pulled), and
  `GET /api/backlog` still shows `-001..-004` with `prereqs: null` — the gate slots 13 & 14 both asked for was never
  added. `BLK-011c84cb` remains the standing operator decision, so I did not file a duplicate. Instead, escalated the
  **gate-add** to main as a separate, immediately-actionable fix (independent of the operator's timing) so a 4th slot
  doesn't burn on this. **Gate-add recipe for main** (per `agents/RULES.md` §4.3, yaml-only — regen does NOT derive
  per-task prereqs from plan todos, and `sequential: true` alone provably does not gate independent dispatch): (1)
  `POST /api/prerequisites/dvol-historical-pull-approved {value:false, set_by:"main"}`; (2) add
  `prereqs.prerequisites: [dvol-historical-pull-approved]` to `-001`, `-002`, `-003`, `-004` in
  `data/config/backlog.yaml`, then `POST /api/backlog/reload`; (3) re-verify it survives a `PlanRegenLoop` tick (the
  `backlog_regen_drops_handtuned_prereqs` bug class); (4) when the operator answers `BLK-011c84cb`, flip the condition
  true. Then `/skip-current-task` (blocked-operator + ungated — not doable from a worker slot; worker cannot hand-edit
  `backlog.yaml` per the HARD RULE, so the gate is main's to add).
- 2026-07-25 (/plan-reconcile apply pass): confirmed via a direct code read
  (`agent-orchestrator/server/regen_backlog_from_plan.py::_wire_sequential_prereqs` + `_wire_gate_on_depends_prereqs`)
  that **no plan-authoring-level fix exists for this specific shape** — not `sequential: true` (already set; confirmed
  the doc's own prior finding that a non-ingested `[OPERATOR]`/`BLOCKED-*` predecessor is skipped when computing
  "immediate predecessor," so the SCRIPT todo's real wired predecessor is the already-DONE todo two positions up), and
  NOT a `depends_on`+`gate_on_depends: true` plan-split either — that mechanism's `_parse_open_todos` fallback (which
  WOULD correctly gate on the still-open OPERATOR todo) only engages when the upstream plan has ZERO current backlog
  task ids; this plan already has 2 DONE ingested task ids, so a split's downstream gate would wire to those (already
  satisfied) and dispatch immediately — reproducing the exact same bug in a new form. **The only real fix is main's
  backlog.yaml `prereqs.conditions` recipe above (still not applied) or a `dispatch.py`/regen code fix to also gate on
  non-ingested predecessors** — flagging this as a cross-cutting AO limitation (not vol-specific) rather than
  re-attempting a doc-only workaround. Added an inline `BLOCKED-OPERATOR-DECISION` self-skip warning to the SCRIPT todo
  above so a dispatched worker can bail in one read without re-deriving this.
- 2026-07-28 (gate-clearing pass, operator general-theme ruling applied — corpus-wide 87-mentions/73-decisions
  gated-item review): the standing `[OPERATOR] BLOCKED-OPERATOR-DECISION` todo (full-history-vs-shorter-window +
  go-ahead) is now **RULED**: full 2021-03-24→now history, go-ahead granted, per the operator's 2026-07-28 general theme
  covering every gated design-choice without a specific per-item answer (not superseded → do it; free source → cost
  floor moot; full-completion-over-shortcuts → full window, not a sample). This resolves `BLK-011c84cb`. Retagged that
  todo `[OPERATOR]` → `[DATA]` and wrote the ruling + full-completion mandate directly into its text. Also updated the
  immediately-following `[SCRIPT]` todo's stale "BLOCKED-OPERATOR-DECISION" wording (that phrase described the
  now-resolved gate, not a separate blocker) to instead describe the real remaining prerequisite — the historical pull
  must actually land in the manifest before the backtest-wiring todo can start. Side note for whoever dispatches next:
  the predecessor todo is no longer `[OPERATOR]`-tagged, so it should now count as a normal ingestable backlog task id —
  the AO gating gap diagnosed in the 2026-07-25 entry above (a non-ingested `[OPERATOR]`/`BLOCKED-*` predecessor skipped
  when `sequential: true` computes the "immediate predecessor") should no longer apply to this specific pair, since the
  predecessor is now a normal `[DATA]` todo; this was NOT independently re-verified against a live
  `regen_backlog_from_plan.py` run, so still confirm the `[SCRIPT]` todo isn't dispatched before the `[DATA]` todo's
  manifest rows actually exist. **No production action taken in this pass** (no GCS writes, no VM launches, no `--apply`
  runs) — this was a docs/backlog-unblocking edit only; the actual full historical pull is the next AO-dispatchable
  step.

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY -> `assigned_vm: planning` (in place, name
  unchanged). the operator gate was RULED 2026-07-28 and the doc itself states "no longer operator-gated, now
  AO-dispatchable"; all 5 todos are bounded (DVOL pull -> backtest -> conditional register -> matrix regen).
  Conflict-check clear: `cross_cutting_satellite_ao_dispatch_batch2` and the cefi digest both name THIS doc as the live
  owner. Shared conflict-check protocol: `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`
  sect.3 - CLEARED.

- 2026-07-30 (slot-2, `data_engineering`): Dispatched the `[DATA] P1` full-history DVOL pull todo. An inline 3-day
  connectivity smoke-test on the shared orchestrator host hit a real ~17GB RSS memory spike (ManifestWriter.flush()'s
  per-day full read-merge-write of the shared cefi `availability_index.parquet`, ~7.5M rows) — killed the runaway
  process (exact PID) and built a dedicated one-off VM launcher instead (`deployment-service@42b80f65f9f3`:
  `dvol-deribit-` prefix + `launch-deribit-dvol-backfill-vm.sh`, e2-highmem-4/250GB SPOT). Real VM run completed clean
  in ~10.5min (no contention running unopposed): manifest-verified 3910/3910 `capture_status=captured` rows (1955 dates
  × {BTC,ETH}, exactly 2021-03-24→2026-07-30, 0 failures/empties). Todo flipped `[x]`. Next: the `[SCRIPT]`
  backtest-wiring todo below is now genuinely dispatchable (its manifest prerequisite is fully satisfied).

- 2026-07-30 (slot-7, `backend_engineer`): Wired + ran the VOL_CARRY DVOL backtest — strategy-service@`18d7e775`
  (`scripts/vol_carry_dvol_backtest.py` + `tests/unit/scripts/test_vol_carry_dvol_backtest.py`, full `quality-gates.sh`
  green before ship, 6 new unit tests). **Methodology**: `iv_atm` from the already-captured DVOL parquet
  (`data_type=volatility_index`, last hourly bar/day, vol-points→fraction); realised vol from a SECOND already-captured
  real series — BINANCE-FUTURES perpetual `derivative_ticker` `index_price` (Tardis batch capture; confirmed via direct
  GCS probe this codebase already holds this data 2021-03-24→2026-05-22, i.e. it predates the current Tardis-credentials
  block — no new external calls made), 20-day rolling annualised close-to-close log-return vol (same formula as
  features-service's `realized_vol_calculator.py`, reimplemented locally per the no-service-to-service-imports rule
  rather than importing it). **Honest window**: backtest run over 2021-03-24→2026-05-22 — the real, GCS-probe-confirmed
  INTERSECTION of both series' coverage (not the full DVOL range, which runs 45 days further to 2026-07-30 with no
  matching underlying-close data yet) — 1866/1886 candidate days had both series (the 20-day gap is the RV lookback
  warmup, not a data hole). **GroupBRunner wiring**: VOL_CARRY is not yet in `ARCHETYPE_ENGINE_REGISTRY` (that is the
  NEXT todo's decision), so the script injects a process-local registry entry before constructing the runner (never
  touches the committed `factory.py`) — the backtest genuinely runs through the real v2 orchestrator + benchmark-fill
  engine, not a bypass. Each ATM CALL/PUT leg's `MarketStateSnapshot.mid_price` is set to the DVOL level itself (no
  per-strike premium series exists — that's precisely what the other 15 VOL_* engines are `BLOCKED-CREDENTIALS` on), so
  the runner's benchmark P&L measures vega P&L (IV-level moves between entry/exit), the economically meaningful quantity
  here. **Real results (both underlyings, full window, no synthetic data)**:
  - BTC: 29 open+flatten cycles (58 fills), `total_pnl=-119.76`, `sharpe_ratio=-0.0063`, `sortino_ratio=-0.0052`,
    `win_rate=22.8%`.
  - ETH: 51 cycles (102 fills), `total_pnl=-191.40`, `sharpe_ratio=+0.0461`, `sortino_ratio=+0.0360`, `win_rate=24.75%`.
    Full JSON in the commit's script output (re-runnable:
    `python scripts/vol_carry_dvol_backtest.py --underlyings BTC,ETH`). **Verdict against the HARD CONTRACT bar**: this
    does NOT clear it — both Sharpes are indistinguishable-from-noise (an order of magnitude below any defensible-edge
    threshold), PnL is flat-to-negative for both assets, and win rate ~23-25% with no compensating asymmetric payoff.
    Flipped this todo `[x]`; annotated the next `[SCRIPT]` (register-or-not) todo above so it does NOT re-run the
    backtest — it should go straight to `not_available` + file the `BLOCKED-*` finding citing these numbers, unless a
    worker has a concrete, stated reason to try a different param sweep (entry_vrp/exit_vrp were left at carry.py's
    defaults 0.04/0.01 — untested whether a different threshold pair would clear the bar; that would be a legitimate
    reason to re-run, not a silent do-over).

- 2026-07-30 (slot-14, `backend_engineer`): Closed the register-or-not todo per the plan's own instruction (no re-run,
  no new methodology challenge). Verified live: `VOL_CARRY` has zero hits in
  `strategy_service/engine/strategies/v2/factory.py` (`ARCHETYPE_ENGINE_REGISTRY`'s wiring point), confirming
  `not_available` is already the actual state — nothing to revert, nothing to register. Filed the
  `BLOCKED-INSUFFICIENT-EDGE` todo (new, P3) directly above citing the exact slot-7 metrics, scoped as a decision record
  (not a code task) so it doesn't silently vanish from the plan. Next: the VOL_ARB_RV_IV todo below runs the same
  backtest-then-conditionally-register sequence independently (separate engine, separate verdict expected).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).

- 2026-08-03 (slot-13, `data_engineering`): Flipped the `BLOCKED-INSUFFICIENT-EDGE` P3 todo above. It was already a
  complete decision record (filed 2026-07-30 by slot-14) — no code task attached to it, so there was nothing to ship.
  Re-verified live that `VOL_CARRY` still has zero hits in `strategy_service/engine/strategies/v2/factory.py`
  (`ARCHETYPE_ENGINE_REGISTRY`), confirming `not_available` hasn't drifted since the decision was recorded, and that no
  alternative param-sweep candidate has since been proposed (the only stated condition for re-opening). Next open todo
  is the `[SCRIPT] P1` VOL_ARB_RV_IV backtest-then-conditionally-register todo below — separate engine, independent
  verdict, genuinely dispatchable next.

- 2026-08-03 (slot-2, `backend_engineer`): Wired + ran the VOL_ARB_RV_IV DVOL backtest — strategy-service@`8996e3c2`
  (`scripts/vol_arb_rv_iv_dvol_backtest.py` + `tests/unit/scripts/test_dvol_backtest_data.py`, full `quality-gates.sh`
  green before ship). **Refactor note**: extracted the DVOL/underlying-close fetch + tick-assembly helpers VOL_CARRY's
  script already had (identical logic — neither archetype needs anything archetype-specific in the data layer) into a
  new shared `scripts/_dvol_backtest_data.py` module, and updated `vol_carry_dvol_backtest.py` to import from it instead
  of duplicating ~150 lines; its superseded `tests/unit/scripts/test_vol_carry_dvol_backtest.py` was folded into the new
  shared test file (same test bodies, now covering the shared module directly rather than via the carry script's
  re-exports). **Import-path pitfall found
  - fixed along the way**: the first commit (`8c9198da`) wired the shared module via
    `from scripts import _dvol_backtest_data`, which passed a direct-python smoke check but hit a real pytest collection
    `ImportError` under the full `quality-gates.sh` run — `unified-api-contracts` installs its OWN `scripts/__init__.py`
    package (a real, non-namespace package), which wins the ambiguous `scripts` name over this repo's plain `scripts/`
    directory whenever its site-packages entry is resolved first on `sys.path`. Fixed (`8996e3c2`) by having both
    scripts insert their own directory onto `sys.path` and import the sibling module by its bare (unqualified) name
    instead, and having the test module load it via `importlib.util.spec_from_file_location` by explicit file path — the
    same technique the superseded test file already used for exactly this class of problem. Full `quality-gates.sh`
    re-run green after the fix (sentinel matched HEAD); shipped via quickmerge, verified on `origin/live-defi-rollout`.

  **Real backtest run** (production GCS data, same honest-intersection window VOL_CARRY used: `2021-03-24`→`2026-05-22`,
  1866/1886 candidate days — the 20-day gap is the RV lookback warmup): ran the UNMODIFIED `VolArbRvIvEngine` (no
  position-tracking added — the engine itself has no in-position/flatten state machine; it emits a fresh straddle
  instruction every day `|iv_atm - rv| >= entry_gap`, unlike VOL_CARRY's open/hold/flatten cycle) via the real
  `GroupBRunner`, `entry_gap=0.03` (arb_rv_iv.py default, untested) + `vega_budget_per_leg=10` (matching VOL_CARRY's
  convention). **Results (both underlyings, full window, no synthetic data)**:
  - BTC: 1786 atomic instructions / 3572 fills, `total_pnl=-9826.53`, `sharpe_ratio=0.0099`, `sortino_ratio=0.0082`,
    `win_rate=24.1%`.
  - ETH: 1784 atomic instructions / 3568 fills, `total_pnl=-9612.40`, `sharpe_ratio=0.0095`, `sortino_ratio=0.0080`,
    `win_rate=23.7%`. Full JSON re-runnable:
    `GCP_PROJECT_ID=central-element-323112 python scripts/vol_arb_rv_iv_dvol_backtest.py --underlyings BTC,ETH` (this
    script's `resolve_bucket_name(...)` call needs `GCP_PROJECT_ID` set in the shell env — not exported by default on
    this host; `gcloud config get-value project` gives the right value). **Verdict against the HARD CONTRACT bar**: does
    NOT clear it — both Sharpes are indistinguishable-from-noise (same bar VOL_CARRY failed on), PnL is strongly
    negative for both assets, and win rate ~24% has no compensating asymmetric payoff. Trade count is ~70x VOL_CARRY's
    at this window (the no-flatten re-entry-every-threshold-day behavior described above), which also explains the much
    larger absolute PnL loss at the same per-leg size. Flipped the register-or-not todo `[x]` directly (folded the two
    steps VOL_CARRY split across separate todos, since this plan only carries one combined todo for VOL_ARB_RV_IV) and
    filed the `BLOCKED-INSUFFICIENT-EDGE` decision record above citing these numbers. Next: the `[SCRIPT] P2`
    matrix-regen todo below is a separate task (not dispatched to this slot) — since 0 of 2 engines flipped to
    `available`, whoever picks it up should confirm the regenerated matrix is unchanged rather than assume no regen is
    needed.

- 2026-08-03 (slot-12, `data_engineering`): Flipped the `BLOCKED-INSUFFICIENT-EDGE` VOL_ARB_RV_IV P3 todo above. Same
  pattern as VOL_CARRY's twin todo — it was already a complete decision record (filed 2026-08-03 by slot-2); no code
  task exists to ship. Re-verified live: `strategy_service/engine/strategies/v2/factory.py`'s
  `ARCHETYPE_ENGINE_REGISTRY` still has zero hits for `VOL_ARB_RV_IV`, and no alternative param-sweep candidate has been
  proposed since filing. **All 5 of this plan's todos are now `[x]` and `locked_by:` is empty** — but this plan has a
  machine-gated finalize twin (`vol_dvol_backtestable_engines_2026_07_13_finalize_2026_07_30.md`,
  `depends_on: [vol_dvol_backtestable_engines_2026_07_13]` + `gate_on_depends: true`) whose own todo is specifically the
  re-verification + archival-eligibility check (measured DVOL date range, fresh backtest re-run for any flipped engine,
  matrix-regen confirmation, then the standard 6-step archival ritual). Not doing that work here — it's out of scope for
  this todo and the twin now becomes dispatchable to do it properly. Next: the finalize twin's `[SCRIPT] P2` todo.

- 2026-08-03 (slot-13, `backend_engineer`) — **finalize twin's re-verification, run here since the parent and its twin
  archive together**: **(1) Measured, not trusted**, the CONSOLIDATED availability manifest directly
  (`unified_trading_ library.read_availability_index_safe` against
  `resolve_bucket_name(cloud="gcp", kind="tick-data", asset_group="cefi")`, filtered
  `data_type=volatility_index`/`venue=DERIBIT`) — confirms **1955 distinct captured dates for BOTH BTC and ETH, span
  exactly 2021-03-24→2026-07-30** (matches `(date(2026,7,30)-date(2021,3,24)).days+1 == 1955` exactly), 100%
  `capture_status=captured` (0 failed/empty). Found 5 BTC + 4 ETH duplicate rows on 3 specific dates (2026-07-08/09/13)
  — harmless overlap between the earlier small connectivity-test days and the later full backfill VM's own write of the
  same dates, not a gap (distinct-date count is what matters and it's exact). The backfill's own claimed range stands,
  independently re-derived from the real consolidated index, not just re-quoted. (2) **Zero engines flipped to
  `available`** — re-confirmed live, zero hits for `VOL_CARRY`/`VOL_ARB_RV_IV` in
  `strategy_service/engine/strategies/v2/factory.py`'s `ARCHETYPE_ENGINE_REGISTRY` — so per the finalize twin's own
  instruction, no fresh backtest re-run was owed (that step only applies to an engine that WAS flipped to available;
  neither was). (3) Confirmed `capability-verdict-matrix.json` commit `14dbb6d1` (unified-api-contracts) genuinely
  reflects 0/2 flipped — both archetypes still `not_registered(no_v2_engine)`, summary totals byte-identical to the
  prior regen. (4) All 5 todos `[x]`, `locked_by:` empty → archival candidate confirmed. Ran the 6-step archival ritual:
  fixed every corpus referrer (`cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`,
  `v2_engine_venue_buildout_2026_06_15.md` ×5, `plans/epics/strategy_master.md` ×2,
  `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` — bare-slug prose fact corrected), no new codex contract to
  stub (the memory-bounding + one-off-backfill-VM patterns this plan used were both pre-existing established patterns,
  not new ones this plan introduced), archiving this plan + its finalize twin together into `plans/archive/2026_08/` in
  the same commit. See the finalize twin's own Progress Log for its todo's full closure.
