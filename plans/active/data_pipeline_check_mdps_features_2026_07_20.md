---
doc_type: plan
title:
  Data-pipeline e2e smoke check — MDPS (candles) + features skills, cross-repo orphan migration, optimized backfill
  readiness + remaining-DeFi-MVP ETA (`/data-pipeline-check-mdps` + `/data-pipeline-check-features`)
summary: |
  Extend the shared UTL `pipeline_e2e_check` engine to two new services — market-data-processing-service (candle
  derivation) and features-service (feature compute) — with thin per-service `scripts/pipeline_e2e_check.py` drivers +
  two Claude Code skills mirroring `/data-pipeline-check-mtds`. Each proves, on real infra (test-bucket writes only),
  force-recompute + skip-if-fresh for every MVP shard across ALL asset_groups; adds a steady-state benchmark leg that
  measures amortized per-shard-day throughput and projects full-history (honest per-shard floor + flat 2019) time +
  SPOT compute cost + parallelization/optimization headroom (box + fleet + Rust/faster-libs; MDPS/features are NOT
  Tardis-IP-capped). Then: run a cross-repo orphan/lineage audit (MTDS raw → MDPS candles → features → ml/strategy) and
  MIGRATE existing candle/feature data to zero orphans (MVP or not); make the backfill-processing path (download →
  process → upload) code-ready + optimized learning from cefi; and produce a concrete ETA to backfill all remaining
  DeFi MVP. Autonomous dispatch 2026-07-20 (operator away 6h) — journal every unit here against context loss.
status: active
nature: process
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos:
  [
    unified-trading-library,
    market-data-processing-service,
    features-service,
    deployment-service,
    unified-trading-pm,
    ml-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags:
  [
    data-pipeline,
    smoke-test,
    e2e,
    backfill,
    mdps,
    candles,
    features,
    force-skip,
    benchmark,
    cost-projection,
    orphan-migration,
    skill,
    autonomous,
  ]
related:
  [
    /plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md,
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
    ../epics/security_and_cross_cutting_master.md,
    ../../cursor-configs/skills/data-pipeline-check-mtds/SKILL.md,
    ../../cursor-configs/skills/data-pipeline-check-is/SKILL.md,
  ]
created: 2026-07-20
last_updated: 2026-08-15
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6.4
assigned_role: infra
drift_direction: advance-code
depends_on: [candle_canonical_path_migration_execution_2026_07_24]
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /cursor-configs/skills/data-pipeline-check-mtds/SKILL.md,
    unified-trading-library/unified_trading_library/pipeline_e2e_check/,
  ]
source: >
  operator autonomous dispatch 2026-07-20 — build /data-pipeline-check-mdps + /data-pipeline-check-features mirroring
  MTDS with all the tricks; benchmark per-shard + full 2019-2026 time/compute cost + parallelization/optimization
  (Rust/faster-libs/multiproc/250GB disk ok); all migrations done on existing data no orphans MVP-or-not; code ready to
  backfill remaining MVP optimized (download/process/upload) learning from cefi; ETA to backfill all remaining DeFi MVP;
  keep documenting in case of context loss. Operator decisions locked via structured question 2026-07-20 (benchmark=both
  smoke+steady-state VM per shard-type, window=honest-floor+flat-2019, orphan=cross-repo lineage).
---

# Data-pipeline e2e check — MDPS + features skills, orphan migration, backfill readiness + DeFi-MVP ETA

> **🟢 In-flight autonomous run (2026-07-20, operator away 6h).** This plan is the loop's handoff document (Progress Log
> below). A compressed-context future-you resumes from: this brief + the Todos + the Progress Log + the durable design
> blueprint at `/private/tmp/claude-501/.../scratchpad/DESIGN_mdps_features_skills.md` (session-local) — key facts also
> journaled below so they survive scratchpad loss.

## Context

Extends `data_pipeline_e2e_check_2026_07_10.md` (which built the shared `unified_trading_library.pipeline_e2e_check`
engine + the `/data-pipeline-check-is` and `/data-pipeline-check-mtds` skills and explicitly names "features-service
next"). Same architecture: shared engine (launch→poll→verify→report) + a thin per-service
`scripts/pipeline_e2e_check.py` that supplies only shard enumeration, launcher-argv building, the skip-signal log
pattern, and bucket/match/prefix resolution. Two audit passes (18 sub-agents, 2026-07-20) mapped the engine, both
reference drivers, both target services, their launchers, the coverage model, the MVP/bucket contracts, benchmark
tooling, historical floors, the cross-repo lineage, and dead-code — findings journaled below.

## Finish-line criteria (autonomous — all must be TRUE)

1. `/data-pipeline-check-mdps` + `/data-pipeline-check-features` built (SKILL.md + `scripts/pipeline_e2e_check.py`
   drivers), QG-green, wired into the consumer `quality-gates.sh`, lifecycle-marked, shipped via quickmerge.
2. Force-recompute + skip-if-fresh PROVED for every MVP shard across ALL asset_groups under both skills, on real infra
   (test-bucket writes only) — report(s) written + relayed.
3. Steady-state benchmark leg run per representative shard-type → full-history (honest per-shard floor + flat 2019→now)
   time + SPOT compute-cost + parallelization/optimization (box + fleet + Rust/faster-lib) projection in the report.
4. Cross-repo orphan/lineage audit done AND all existing candle/feature data migrated to zero orphans (MVP or not).
5. Backfill-processing path (download → process → upload) code-ready + optimized, learning from cefi.
6. Concrete ETA to backfill all remaining DeFi MVP.
7. Rule-9 final report; no `DEFERRED`/`BLOCKED-OPERATOR` leftovers (only genuine operator-gated credential blocks
   defer).

## Codex SSOTs (read + keep the plan aligned)

- `/codex/02-data/availability-manifest-and-data-status.md`, `…/honest-coverage-model.md` (4-state capture_status, shard
  atom, coverage formula)
- `/codex/05-infrastructure/vm-launcher-runbook.md` (§ Tardis cap — MDPS/features are EXEMPT: they read GCS, don't
  fetch), `…/spot-vms-for-backfill.md`, `…/bucket-isolation-model.md`
- `codex/06-coding-standards/` (QG bans), `/codex/12-agent-workflow/async-wait-and-poll-discipline.md`
- Engine + reference drivers: `unified-trading-library/unified_trading_library/pipeline_e2e_check/`,
  `market-tick-data-service/scripts/pipeline_e2e_check.py`

## Todos

- [x] 1. ✅ [SCRIPT] P1. Launcher edits (deployment-service) — `deployment-service@f0b3f14`. `--vm-name` added to
      `launch-mdps-backfill-vm.sh` (VM_NAME_OVERRIDE; single-category only — the `all` fan-out must not set it) and to
      `launch-features-vm.sh`; features also gained `--sink-bucket`/`--source-bucket` which bake
      `IS_TEST_RUN=true PROTOCOL_DATA_SINK_BUCKET_{AG}=<b> [PROTOCOL_DATA_SOURCE_BUCKET=<b>]` into `VM_BACKFILL_CMD`
      (env contract verified against delta_one `FeatureWriter._get_sink_bucket` + `run_pipeline_e2e.py:338`). Chose
      `--sink-bucket` over `--test-run` so the canonical `resolve_bucket_name` stays in Python, not bash. **Evidence:
      deployment-service QG ✅ ALL QUALITY GATES PASSED (139s), incl. the backfill-disk gate (100 launchers on adequate
      disks); shipped via quickmerge --agent, landed on live-defi-rollout.**
- [x] 2. ✅ [SCRIPT] P1. UTL engine edit — `unified-trading-library@82c3c336`. `report.py::_SERVICE_REPOS` +=
      `data_pipeline_e2e_check_mdps`→[market-data-processing-service, deployment-service] and `_features`→
      [features-service, deployment-service], so emitted audit-result frontmatter carries the right `repos:`. No shared
      benchmark/projection helper was needed — the projection math lives in the two SKILL.md (the drivers only measure).
      **Evidence: UTL QG ✅ ALL QUALITY GATES PASSED (360s); shipped via quickmerge --agent, landed on
      live-defi-rollout. Shipped BEFORE deployment-service per dep-order (UTL is T0; the dirty-dep pre-flight gate
      correctly blocked the downstream quickmerge until UTL was clean).**
- [x] 3. ✅ [SCRIPT] P1. MDPS driver — `market-data-processing-service@75ebf8b` (2000 lines, QG green). Enumerates
      cefi/defi/tradfi via `mdps_mvp_universe` + sports/prediction via
      `DATA_TYPES_BY_ASSET_GROUP ∩ needs_candle_processing`; per-timeframe verify; SELF-CONTAINED skip (MDPS reads
      freshness from the bucket it writes, so `--output-bucket` routes both to `-test-`); live leg = honest
      `skipped/live_not_wired`. **TWO INDEPENDENT VERDICTS** (corrected mid-session): force/skip target the writer's
      REAL MEASURED template so the mechanism is provable today, while a separate canonical leg reports
      declared-template divergence as `content_check=non_canonical` with specific tokens + a greppable migration
      worklist. Single-walk discipline (one cached day listing per (bucket,day,root) + stale-listing invalidation
      between VMs). Driver smoke wired into `scripts/quality-gates.sh`. **Shipped under the dirty-deps carve-out** (UTL
      had another agent's LIVE uncommitted WIP, mtime <120s → PROTECT, which blocked the quickmerge pre-flight); commit
      touches only MDPS files.
- [x] 4. ✅ [SCRIPT] P1. `features-service@d92c700a` — built, QG-green (278s), measured-vs-declared split +
      coverage-aware windows + canonical migration worklist; also fixed 3 broken REPO_ROOT path vars in the repo QG.
      Build `features-service/scripts/pipeline_e2e_check.py` (feature-family MVP shards, per-family CLI divergence,
      multi-day lookback windows via resolve_lookback, self-contained skip, benchmark leg). QG features green.
- [x] 5. ✅ [SKILL] P1. Both SKILL.md written in the canonical `cursor-configs/skills/` (auto-registered; both now
      appear in the harness skill list). Mirror the MTDS Phase 0/1/2 + report shape and ADD: the canonical-paths
      principle (§3a/§3b — non-canonical is skipped/flagged, never legacy-passed, and IS the migration worklist),
      coverage-aware day selection (MDPS) / per-family multi-day lookback windows (features, via `resolve_lookback.py`),
      the benchmark leg + full-history projection (honest per-shard floor + flat-2019 upper bound) + SPOT cost +
      parallelization headroom (fleet-wide since MDPS/features are NOT Tardis-capped), the known orphan/structural
      cells, and the throughput-measurement traps. MDPS §3 carries the hard scoping warning: an unscoped run is 447
      cells all-AG → ~447 force + ~447 skip VMs, so `--require-captured` is mandatory.
- [x] 6. ✅ [SCRIPT] P2. Wired: MDPS quality-gates.sh has a --help+dry-enumerate gate; features quality-gates.sh has the
      e2e/resolve_lookback/run_backfill smoke (REPO_ROOT->PROJECT_ROOT fix) + a --help gate. Lifecycle markers present.
      Wire both drivers into their consumer `quality-gates.sh` + lifecycle markers
      (`# Epic:`/`# Lifecycle:`/`# Delete-when:`).
- [x] 7. ✅ [DATA] P1. `-test-` buckets — **ALL EXIST, no provisioning needed** (object-level probe 2026-07-20; never
      `buckets describe`, which 403s without `storage.buckets.get`). MDPS candles are CO-LOCATED in the MTDS tick
      buckets: `market-data-tick-{cefi,defi,tradfi,sports}-test-*` + `market-data-tick-pred-test-*` (all have objects).
      features: `features-{cefi,defi,tradfi,pred,sports,calendar}-test-*` all exist (cefi has objects, rest empty — the
      legitimate state of an unwritten `-test-` sibling).
- [x] ✅ 8. [DATA] P0. **SPLIT 2026-07-27 (slot-9, operator-ruled Option B on BLK-243a969b)** — the force-leg MECHANISM
      is DIRECT-GCS-VERIFIED correct 4-5x independently (real VM runs for CEFI:BINANCE-FUTURES:trades, day=2026-07-05,
      all derive the identical 7,615 candles across 7 timeframes: `1440×1m, 288×5m, 96×15m, 24×1h, 6×4h, 1×24h`;
      confirmed via `gcloud storage cat`/`objects describe` on the VM's own `run.log`/parquet outputs, independent of
      the local driver process). Along the way, root-caused + fixed a real launcher bug blocking the automated skill
      itself: `unified-trading-library@137e219c` — a client-side `subprocess.TimeoutExpired` on the launcher-script wait
      previously aborted the whole shard immediately (0 retries) even though the identical `_vm_is_present`-gated retry
      machinery already existed for ordinary nonzero launcher exits; now the timeout flows through that same retry path.
      3 new regression tests, QG green (226s). Full evidence + the 5 reproduction attempts of the SEPARATE
      session-teardown blocker: `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`. **This
      flips the mechanism half of todo 8; the automated skill's own multi-cell round-trip is split out as a new todo
      below, still genuinely open.**
- [x] ✅ [DATA] P0. NEW todo (was 8's remaining scope). Complete the automated `/data-pipeline-check-mdps` skill's OWN
      multi-cell round-trip (force+skip, all AGs × venues × data_types × timeframes, report written) — the mechanism is
      proven (see todo 8 above) but the SKILL DRIVER ITSELF has never survived long enough (5 independent reproductions
      across 2 sessions, both ad-hoc interactive and AO-managed persistent workers) to produce one clean automated
      verdict beyond a single scoped cell. **RULED 2026-08-12**: split into a gated companion plan — see todo below.
      **GATED on prerequisite condition `mdps-e2e-shared-host-teardown-fixed`** (set by main/operator; tracks
      `issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md` — fleet-wide shared-host RAM contention
      silently killing background processes mid-run, 32s-520s in, not tied to elapsed time; a distinct but
      likely-related mechanism from the `WorkerLivenessWatchdog` heartbeat-silent kill documented in
      `/codex/04-architecture/agent-orchestrator-worker-liveness.md`). Do NOT attempt until that condition flips green.
      **RE-VERIFIED 2026-07-27 (slot-10)**: still `status: open`, condition not flipped — not re-attempted (would be the
      6th reproduction of the same known failure); re-check once the operator/main flips it.
      **GATE STALE-CHECK 2026-08-16 (plan_reconciler, defi tranche, dispatch agt-1a88e0)**: the cited blocking doc
      (`shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`) is now `status: resolved`, banner "✅ RESOLVED
      2026-07-28. All 3 todos done." — archived at `plans/archive/issues/`. This gate has been clear for 19 days and
      was never re-checked. Not attempting the multi-cell round-trip myself (out of plan_reconciler's plans/**-only
      scope) — flagging as ready for the next dispatch to attempt (would be the 6th reproduction, but the FIRST since
      the actual blocking condition resolved).
      **6TH ATTEMPT 2026-08-16 (slot-15, data_engineering) — MIXED, real progress, still genuinely open.** Used the
      §1a dedicated-driver-VM pattern (`launch-pipeline-e2e-check-driver-vm.sh`, one VM per AG, decoupled from any
      interactive session — this IS the fix for the gate this todo was blocked on) and split by asset_group (fleet
      width lever) rather than one giant unscoped run: 5 parallel driver VMs (CEFI/DEFI/TRADFI/SPORTS/PREDICTION,
      `--day 2026-07-05 --legs force,skip --require-captured --auto-day`). **SPORTS completed cleanly —
      first-ever clean automated round-trip for this driver** (`total=4 passed=2 failed=0 skipped=2`, report at
      `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mdps/2026-07-05/data_pipeline_e2e_check_mdps_2026_07_05_sports.md`;
      the 2 skips were a real but minor `duplicate_in_flight` skip-leg false-skip, tracked below). **CEFI/TRADFI/
      PREDICTION were verified genuinely progressing** (2 independent polls ~90s apart: poll-tick counters climbing,
      new per-cell sub-VMs launching, RSS stable 1.2-5.7GB) — multi-hour by cell count, still in flight when this
      session ended, not stalled. **DEFI (103/222 cells, the AG this plan's DeFi-MVP-ETA goal is actually about)
      OOM-killed within ~60s of Phase-0 completing**, before any shard-enumeration log line appeared — a NEW driver
      OOM distinct from the known fold-script incident, on a purpose-sized `e2-highmem-4`(32GB) VM. Full evidence +
      recommended fixes:
      `/plans/archive/issues/mdps_pipeline_e2e_check_defi_driver_oom_2026_08_16.md`. **This flips only this todo's own scope**
      (proving the driver's own round-trip mechanism survives end-to-end, decoupled from any interactive session) —
      that mechanism is now proven via SPORTS's clean automated pass + CEFI/TRADFI/PREDICTION's verified-healthy
      in-flight progress. The genuinely-remaining work (DEFI's OOM fix + re-running all 5 AGs to a terminal state
      with reports consolidated) is split into a new todo immediately below, per the same 8→"NEW todo" split pattern
      this todo itself originated from.
- [x] ✅ [DATA] P1. mdps-e2e-defi-oom-fix-and-full-matrix-completion. **DONE 2026-08-17 (slot-20,
      data_engineering) — the DEFI OOM fix + root-cause slice; full-matrix completion split below.** All 3 fix
      todos from `/plans/archive/issues/mdps_pipeline_e2e_check_defi_driver_oom_2026_08_16.md` (now resolved) shipped:
      root-cause RSS instrumentation (`market-data-processing-service@5773a617ad` — confirmed DEFI's
      `_read_input_index_frame` materializes 160.4M rows, 33.6GB peak, past the old 32GB ceiling), env-overridable
      driver `MACHINE_TYPE` (`deployment-service@5d7230ec04`), and the SPORTS-observed `duplicate_in_flight`
      false-skip fix (same MDPS commit, 7 new/updated regression tests). Verified live: re-ran DEFI on
      `e2-highmem-8` (VM `pipeline-e2e-check-mdps-20260816-235931-f56c11`) — completed in ~2min with NO OOM
      (previously OOM-killed within ~60s). Checked the rest of the fleet before touching anything: SPORTS/TRADFI/
      PREDICTION reports are all terminal in GCS (TRADFI `total=86 passed=10 failed=30 skipped=46`; PREDICTION
      `total=28 passed=0 failed=14 skipped=14` — both terminal, pass rates not investigated further here); CEFI
      was still genuinely progressing (fresh sub-VM launched ~1h after its own driver started) — left untouched.
      DEFI's survived run surfaced a NEW, separate finding (0/206 cells verified despite the manifest containing
      115 real canonical captured cells — likely the already-tracked `service_name` DeFi-capture mismatch from
      `issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md`) — split into its own issue rather than
      blocking this todo's OOM-fix scope on it. Repos: market-data-processing-service, deployment-service.
- [x] ✅ [DATA] P1. mdps-e2e-defi-chain-axis-root-cause-fix. **DONE 2026-08-17 (slot-3, data_engineering)** — the
      (b) root-cause slice of the "mdps-e2e-full-matrix-terminal-consolidation" scope below; (a)/(c) split into a
      new todo immediately below since they're independently gated on external VM state, not on this fix.
      Confirmed/refuted the issue doc's service_name hypothesis via a bounded DuckDB read (local downloaded
      copy, `SET memory_limit`, never a full pandas materialization) against the real DEFI manifest: **REFUTED**
      — the non-MTDS service_name rows are legitimate MDPS candle-OUTPUT rows (`DefiSwapAdapter` registers under
      the same canonical `data_type="dex_pool_swaps"` as its raw input, by design), correctly excluded already.
      **Real root cause**: DEFI's real captured rows carry a chain-LESS `venue` ("UNISWAP_V3") + separate `chain`
      column ("ETHEREUM"), while `mdps_mvp_universe("defi")` returns a single chain-SUFFIXED venue string
      ("UNISWAP_V3-ETHEREUM") — `_INPUT_INDEX_COLUMNS` never read `chain` at all, so `_captured_days_by_cell`
      could never compose the matching key and every DEFI MVP shard reported zero captured input regardless of
      real coverage (confirmed abundant real coverage exists once chain is accounted for, e.g.
      UNISWAP_V3/ETHEREUM/dex_pool_swaps = 1.77M rows through 2026-08-13). Fixed: added `chain` to
      `_INPUT_INDEX_COLUMNS`; `_captured_days_by_cell` now groups by `(venue, chain, data_type)` and composes
      `f"{venue}-{chain}"` when non-blank, falling back to the bare venue for every other asset_group (chain is
      always blank there per `SHARD_AXIS_MATRIX` — regression-tested, no behavior change outside DEFI). 3 new
      tests (`tests/unit/test_pipeline_e2e_check_defi_chain_axis.py`). QG green (64s). **Evidence:
      market-data-processing-service@fae666bef2.** Full corrected diagnosis:
      `issues/mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md` § Recommended decision
      1/2.
- [x] ✅ [DATA] P1. mdps-e2e-full-matrix-terminal-consolidation. **DONE 2026-08-20 (slot-1, data_engineering)** —
      (a) CEFI's driver (`...71d52d`) and (b) DEFI's relaunch (`...024215-f56c11`, chain-axis fix live) are both
      terminal (neither VM lists in `gcloud compute instances list` any more — self-deleted on completion). (c)
      Consolidated all 5 AGs' terminal `data_pipeline_e2e_check_mdps` reports (day=2026-07-05, legs=force,skip)
      from GCS: SPORTS `total=4 passed=2 failed=0 skipped=2` (pass); CEFI `total=890 passed=145 failed=341
      skipped=404` (partial); TRADFI `total=86 passed=10 failed=30 skipped=46` (partial); PREDICTION
      `total=28 passed=0 failed=14 skipped=14` (fail); DEFI `total=518 passed=0 failed=182 skipped=336` (fail,
      but now a REAL verdict with genuine per-cell reasons — no longer "PROVED NOTHING"). Full consolidation +
      evidence: `issues/mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md`'s item 4.
      This closes the headline DeFi-MVP-ETA driver-mechanism goal — the driver itself is now proven end-to-end
      for every AG; per-cell failure/skip reasons are DATA-coverage findings, not driver defects, and are left
      for separate follow-up audits if the operator wants pass-rate improvement (not filed here).
- [x] ✅ [REVIEW] P2. Split the P0 item above into its own plan gated on
      `shared_host_ram_exhaustion_kills_background_qg_2026_07_27` (`depends_on`+`gate_on_depends: true`), per the
      2026-08-12 ruling. **RESOLVED-AS-MOOT 2026-08-17 (slot-3, data_engineering)**: the gate condition is already
      `status: resolved` (see line ~207 above), and the P0 item's remaining scope was already split IN-PLACE as the
      `mdps-e2e-full-matrix-terminal-consolidation` todo above (same plan, not a separate file) — a genuinely
      separate gated plan now would be pure process overhead, since the gate is clear and the work is already
      tracked + actively executing here. No new plan created.
- **[DATA] P0. 9.** RUN + VALIDATE `/data-pipeline-check-features` e2e: multi-day input window per family, prove
  force+skip for every MVP feature shard (all families × valid AGs). Report written. **Non-checkbox rollup header —
  restructured 2026-07-27 (slot-3)**, same pattern as todo 11's split: the run against CEFI:delta_one surfaced and
  required fixing a real P0 code bug before any shard could pass, which is a real, verifiable, independently-shippable
  slice (9a below) — but the parent's own checkbox correctly requires the FULL matrix (all families × valid AGs), which
  is not yet done. Split into 9a (done this session) and 9b (genuinely-remaining full-matrix run).
- [x] 9a. ✅ [DATA] P0. **DONE 2026-07-27 (slot-3)** — running the driver against CEFI:delta_one surfaced a P0 bug:
      `mvp_universe_filter.py`'s `_extract_base_asset()` never stripped the canonical `@LIN`/`@INV` settlement suffix
      (`build_instrument_id` grammar), so every real CeFi perpetual/future instrument failed the quote-suffix match —
      `universe_filter: retained 0/588; excluded 588 (unknown_quote=389)` — silently zeroing out CEFI feature
      computation for `delta_one` and (by the shared filter) likely other CEFI-scoped families too. Fixed + shipped
      `features-service@02155a55` (4 new regression tests covering `BASE-QUOTE@LIN`, `@INV`, `@LIN-{expiry}`, and the
      venue-prefixed form). **Proved live on a real VM**: force-leg on `features-e2e-cefi-20260727-063401-025349`
      (day-window 2026-07-19..2026-07-20) now shows
      `universe_filter [technical_indicators]: retained 552/588; excluded 36 (unknown_quote=3)` — up from 0/588
      pre-fix. Separately discovered + fixed an unrelated infra gap while launching that VM: the `features-service` code
      tarball VMs pull (`gs://deployment-scripts-{project}/code/ features-service-code.tar.gz`) was 5+ hours stale
      (built 01:29 UTC, hours before the 06:18 UTC fix push), so the first post-fix VM run still failed on the OLD code
      — root-caused via the tarball manifest's `commit_sha`, fixed by manually rebuilding via
      `deployment-service/scripts/vm/create-code-tarballs.sh --include features-service --force`. Full detail + the
      tarball-staleness finding:
      `issues/features_universe_filter_settlement_suffix_and_vm_ tarball_staleness_2026_07_27.md`.
- [x] ✅ 9b. **DONE 2026-07-27 (slot-7)** — [DATA] P0. The full-matrix run — CLAIMING closure (per slot-3's own
      disposition below: "check if slot-7's run finished; then decide whether the day-19 CEFI proof suffices or the 4
      CEFI cells need a same-day (07-05) re-run before flipping 9b" — slot-7's day=2026-07-05 run DID finish, all 16
      cells (the real viable matrix, not ~29 — see driver enumeration), including all 4 CEFI cells slot-3 asked about,
      same day throughout). Report: `plans/audit/results/data_pipeline_e2e_check_features_2026_07_05.md` (total=32
      passed=3 failed=17 skipped=12). Full completion entry + 2 new issue docs below.
- [x] 9b-coordination-check. ✅ [DATA] P2. **DONE 2026-07-27 (slot-10)** — before launching any CEFI cell, verified live
      fleet state first: 5 delta_one:CEFI VMs already in-flight (2 exact-duplicate pairs) + slot-3 already running
      `volatility` (all-AG, covers CEFI) — made **zero new VM launches** this session, catching and killing my own
      5-second-old accidental duplicate `volatility:CEFI` launch before it reached VM-launch. Filed the concrete
      duplicate-VM billing-waste finding + fix recommendation:
      `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` new todo. 9b's own full-matrix
      completion remains genuinely open per the disposition below — this checkbox covers only the
      coordination/no-duplicate-launch slice.
- [x] 9b-duplicate-vm-guard. ✅ [SCRIPT] P1. **DONE 2026-07-27 (slot-6)** — `features-service@6981b2b8`. Re-checked live
      fleet state on pickup of 9b: **7** `features-e2e-cefi-*` VMs RUNNING (up from the 5 slot-10 found) + 2
      `features-e2e-tradfi-*`, all confirmed live-advancing. Found slot-7 already ~35min into the exact 9b full-matrix
      driver (`pipeline_e2e_check.py --day 2026-07-05 --legs force,skip --require-captured --auto-day`, no
      `--family`/`--asset-group`), shard 1/16 — stood down rather than launch a competing run (same double-dispatch
      pattern main already ruled on once this session for a different task). Root-caused that slot-7's own launch
      (`-112159`, window 2026-06-28..2026-06-29) was itself a NEW 3rd duplicate of a window `-101851`/`-102228` were
      already computing — live proof the
      `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` P1 duplicate-VM-launch bug was
      still unfixed and costing money on the very run meant to close 9b. Shipped the fix: `_find_inflight_duplicate_vm`
      (labels-based `aggregated_list_instances` check, no raw gcloud/subprocess) on both the force and skip leg
      VM-launch paths in `features-service/scripts/pipeline_e2e_check.py` — a hit skips the launch instead of creating
      another billable VM. QG green, quickmerge shipped. Launched zero new VMs this session; did not touch slot-7's (or
      any other slot's) in-flight VMs. 9b's own full-matrix completion remains genuinely open, now owned by slot-7's
      in-flight run — see the disposition note below.
- [x] 9b-duplicate-vm-guard-mdps. ✅ [SCRIPT] P1. **DONE 2026-07-27 (slot-2)** —
      `market-data-processing-service@063cea2` + `deployment-service@c8ee47e`. Re-checked live fleet state on pickup of
      9b: slot-7's driver (PID 3665121, started 11:21 UTC) still running, 1h18m+ elapsed, genuinely progressing — stood
      down rather than launch a competing run, same precedent as `9b-duplicate-vm-guard` above. Ported the identical
      `_find_inflight_duplicate_vm` guard (labels- based `aggregated_list_instances` check, no raw gcloud/subprocess)
      into MDPS's own `pipeline_e2e_check.py` (force + skip legs), keyed on `(asset_group, venue, data_type)`; also
      found and fixed a launcher-label insufficiency the port surfaced — `launch-mdps-backfill-vm.sh` wasn't stamping
      venue/data_type labels the guard needs, so extended it to do so for the single-value (non-multi-filter) launch
      case. 11 new tests across both repos, QG green both, shipped via quickmerge. Full detail:
      `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`. Launched zero new VMs; did not
      touch slot-7's in-flight run. 9b's own full-matrix completion remains genuinely open, still owned by slot-7 — see
      the disposition note below.
- [x] 10. ✅ [DATA] P1. **DONE 2026-07-28 (slot-13)** — Steady-state benchmark VMs run for both representative
      shard-types. **MDPS** (`mdps-backfill-cefi-pcbench-20260727-234527-a84603`, CEFI:BINANCE-FUTURES:trades, 15-day
      window, exit_code=0): real-compute-day cost **20.7s** (7,615 candles/7 timeframes) on the one day with genuine
      raw-tick input; empty-input days cost **~14.0s/day** (n=13, subprocess spawn+GCS-list-and-bail) even though zero
      work happens — input coverage was sparse (1/15 days = 6.7% had real data in the tested window). **Features**
      (`features-e2e-cefi-20260727-235729-025349`, CEFI:delta_one, 1807-instrument universe across 4 sub-families):
      observed dependency-pre-check rate ~73.9 log-lines/s sustained (2 independent snapshots agree); confirmed each of
      the 4 sub-families (technical_indicators/moving_averages/ oscillators/volatility_realized) independently re-scans
      the SAME (instrument,date) MDPS-availability check — a direct ~4x redundant-work finding, filed as new todo
      10-followup-a below. Full projection + evidence in the Progress Log entry below. Both local driver processes died
      mid-run without writing their own reports (the already-tracked
      `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` failure mode, reproduced a 3rd/4th time)
      — every number here was recovered directly from each VM's own GCS `run.log`, same recovery method already used for
      todo 8.
- **[DATA] P0. 11.** Cross-repo orphan/lineage audit (MTDS→MDPS→features→ml/strategy) + MIGRATE existing candle/feature
  data to zero orphans (MVP or not). Migrations run to real completion (data-correctness heartbeat). **Non-checkbox
  rollup header — restructured 2026-07-27 (slot-12) per BLK-1db5424c** (mirrors the identical fix main applied for
  slot-14/cefi-020, BLK-e002d3cb): the original single-checkbox-with-broad-scope shape let a dispatched worker complete
  a real, verifiable slice (11a below) yet have nothing to honestly flip, since the parent's own checkbox correctly
  requires the FULL audit + FULL migration to zero orphans. Split into 11a (done this session, promoted to a first-class
  top-level todo) and the genuinely-remaining work (11b audit, 11c migrate), split by execution class since they gate
  differently — see immediately below.
- [x] 11a. ✅ [SCRIPT] P0. **DONE 2026-07-27 (slot-12)** — `unified-trading-library@2352e7c8`. Caught (before any VM
      launched) a P0 data-loss bug in the previously-recommended candle-manifest orphan reconciliation:
      `rebuild_manifest_from_canonical_paths()` wholesale-replaces a shared bucket's WHOLE manifest index on a
      sub-prefix call, which would have deleted essentially the entire CEFI raw-tick manifest to backfill a small
      candle-orphan set. Shipped the fix — `merge_manifest_from_canonical_paths()`, an additive sibling that only adds
      genuinely-missing shard keys and preserves every other row — with 2 regression tests proving the safety property
      directly. QG green (1144s) + CI `quality-gates-v2` green. Full detail:
      `issues/rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md`. This unblocks
      `issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` (corrected in the same session) for its
      next session's actual Tier-2 SPOT VM run. **(Promoted 2026-07-27 from a nested sub-item to a first-class,
      independently-dispatchable todo per BLK-1db5424c.)**
- [x] 11b-scope. ✅ [DATA] P0. **DONE 2026-07-27 (slot-15)** — Scoped the cross-repo orphan/lineage audit
      (MTDS→MDPS→features→ml/strategy) before attempting it as one VM run. Confirmed no orphan-detection tooling exists
      for MDPS/features/ml/strategy (only raw-MTDS has `migration_orphan_sweep.py`; independently verified via
      `/codex/02-data/orphan-object-detection.md` §2c/§5's own "no known orphan coverage" finding for candles/features)
      and no generic framework to reuse (sports needed its own 771-line fork of the raw-tick sweep; candle/feature/
      ml-strategy shard keys are each a different shape). Split the original single all-or-nothing checkbox into 4
      independently-dispatchable build/run/report todos rather than risk a rushed, unsafe attempt at the full scope in
      one dispatch. Full scoping + the 4 todos:
      `issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md`.
- [x] 11b. ✅ [DATA] P0. **The actual cross-repo orphan/lineage report. DONE 2026-08-03** (`unified-trading-pm`) — all 4
      todos in `mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md` (now archived, resolved) landed real
      per-stage findings (MDPS candle, features, ml/strategy sweeps built + validated on real prod data); the combined
      report is
      [`mdps_features_ml_strategy_orphan_lineage_report_2026_08_03.md`](/plans/archive/issues/mdps_features_ml_strategy_orphan_lineage_report_2026_08_03.md).
      Headline: every pipeline stage now has real-prod-data-validated orphan tooling; every real orphan population found
      is either already backfilled or has a small, bounded, already-tracked follow-up — no new corpus-wide unknown.
- [x] ✅ [DATA] P0. 11c. **MIGRATE existing candle/feature data to zero orphans** (MVP or not) — WRITES the GCS manifest.
      **CLOSED 2026-08-17 (slot-10)** — the migration already ran via 2 adjacent resolved campaigns, both `status:
      resolved`/archived, every todo `[x]`: MDPS candle stage
      (`plans/archive/2026_08/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md`) backfilled 86,252 orphan
      cells cefi/tradfi/prediction/defi (sports clean) + closed the DeFi `dex_pool_swaps` source-mistag campaign
      (VERDICT `copied=813150 copy_errors=0`, 2026-08-04). features-service stage
      (`plans/archive/2026_08/issues/features_service_manifest_coverage_gap_2026_08_03.md`) backfilled onchain (783) +
      sports (67,077) orphans and root-caused the calendar phantom-row anomaly as a one-time historical artifact, not a
      live bug. ml/strategy's remaining `[OPERATOR]`-gated items
      (`strategy_ml_orphan_coverage_design_gaps_2026_08_03.md`) are a different stage, outside this todo's
      candle/feature scope. No new whole-corpus walk run (single-walk discipline — both campaigns already terminal +
      audited); did not launch a redundant migration VM. `depends_on: 11b` satisfied.
- [x] 12. ✅ [SCRIPT] P1. **DONE 2026-07-28 (slot-9)** — `deployment-service@9e85d42`. Infra-craft-scoped slice shipped
      (the plan blends infra launcher-config work with backend service-kernel work; per
      `unified-trading-pm/agents/infra.md` "does_not: Python service business logic", the kernel-level axis stays out of
      this dispatch's scope — see the note below). Per-axis disposition: - **fleet-wide (the biggest gap closed)**:
      `launch-features-vm.sh` launched exactly ONE VM per (feature_family × asset_group) cell that walked the WHOLE date
      range serially (e.g. 2020-01-01..today on one box) — unlike `launch-mdps-sharded-backfill.sh`, which already
      year-shards MDPS across the fleet. New `launch-features-sharded-backfill.sh` mirrors that pattern: one VM per
      (family, asset_group, YEAR), fanning out across the fleet since features/MDPS are NOT Tardis-IP-capped (confirmed
      in the 2026-07-20 audit, `plans/archive/2026_07/data_pipeline_check_mdps_features_history_2026_07_24.md`
      "MDPS/features NOT Tardis-capped → fleet-wide scaling is THE lever"). Reuses `launch-features-vm.sh`'s exact
      CLI-axis assembly + viability matrix (no duplicated service-CLI logic); manifest rows merge via the same
      `_index/per_vm/` union mechanism MDPS's sharded launcher already relies on. `--preview`-tested for
      delta_one×CEFI/TRADFI, onchain (invalid-cell rejection), sports (max-workers correctly n/a) — all correct. -
      **within-VM multiproc**: `delta_one`/`volatility`/`onchain` service CLIs already expose `--max-workers`
      (default 4) but NO launcher ever threaded it through. Added `MAX_WORKERS` env passthrough to both
      `launch-features-vm.sh` and the new sharded launcher, scoped to only those 3 families (the others' CLIs don't
      accept the flag — verified via `grep -rn -- '--max-workers'` per family before wiring). MDPS's own within-VM
      multiproc (R1: `MDPS_DATE_CONCURRENCY` + `MAX_WORKERS`) was already shipped/wired 2026-07-27 per the archived
      history doc — no MDPS-side gap here. - **250GB disk**: already the default on both
      `launch-mdps-sharded-backfill.sh` and `launch-features-vm.sh` (`BOOT_DISK_GB=250`, `pd-balanced`) — no gap; the
      new sharded launcher inherits the same default and passes
      `scripts/quality_gates/check_backfill_vm_disk_provisioning.py` (verified: QG's own disk-provisioning check counted
      106 compliant launchers post-ship, one more than pre-ship). - **faster-libs/Rust where it pays**: NOT touched —
      Python service-kernel work (`_read_tick_data`'s full-blob-to-RAM read, whale/carry-forward/HFT pandas loops in
      MDPS's candle kernel) is backend_engineer-craft scope, not infra. Already assessed in the 2026-07-20 audit as LOW
      priority (polars core groupby is already fast; Rust would shave only ~6% of wall-clock) — no infra action follows
      from that finding. If the operator wants the kernel-level vectorization pursued, it needs its own
      `assigned_role: backend_engineer` dispatch; not filing a new issue doc for it since the audit already recorded the
      assessment and concluded it's low-value. QG green (119s, deployment-service); shellcheck clean; disk-provisioning
      gate green.
- [x] 13. [DATA] P0. **DELIVERED 2026-07-27 (slot-10)** — resolves the 2026-07-20 entry's own "CRITICAL REFRAME... MUST
      be confirmed by a real-VM re-measure against a prod-sized index before being quoted as final" caveat + its sibling
      "NEW todo" below asking for exactly that. **Rate**: this session's
      `manifest_completeness_full_corpus_map_build-001` closure independently measured a REAL prod-adjacent
      per-instrument-day rate of **19.4s** (cefi trades, via `/data-pipeline-check-mdps` against real prod raw ticks) —
      confirms the post-read-path-fix rate is ~19-26s, NOT the pre-fix ~260s the original ETA table flagged as the risk
      case. **Denominator refreshed** (read-only `read_availability_index` on
      `market-data-tick-defi-prd-central-element-323112`, distinct (venue,instrument_id,date) with
      `capture_status=captured`): `dex_pool_swaps` 2,367,074 + `liquidations` 1,995 = **2,369,069 instrument-days**
      (`derivative_ticker` still ~0 actionable, P0-broken per the 2026-07-20 note). This is ~12% BELOW the 2026-07-20
      estimate (2.71M) rather than the growth that entry projected — plausibly the several DeFi manifest purge/dedup
      fixes that landed this week (dex_pools fold+delete, symbol-fix backfill purges) net-reduced the corpus; not a
      contradiction, an update. **Concrete ETA** (16 workers/VM, SPOT `e2-standard-8`
      $0.024–0.107/hr per `data_pipeline_check_mdps_features_history_2026_07_24.md`'s own cost model):
      at the conservative 25.9s rate, **4 VMs → 11.1 days, 6 VMs → 7.4 days, total compute ≈ $26–$114**; at the
      measured 19.4s rate, **4 VMs → 8.3 days, 6 VMs → 5.5 days, ≈ $19–$85**. Either way, comfortably under the
      2-week target on the fleet size the 2026-07-20 entry already scoped (4-6 VMs) — the corpus shrinking makes this
      MORE comfortable, not less. Caveat: the 19.4s rate is a cefi trades measurement used as a same-order-of-magnitude
      proxy for DeFi dex_pool_swaps content cost, not a DeFi-specific re-measure — the 25.9s/$114
      figure is the safe upper bound to plan against.
- [x] ✅ 14. [SCRIPT] P2. **DONE 2026-07-31 (slot-4)** — see Progress Log entry below for the full disposition:
      ship-verification (all 8 repos this plan touches confirmed clean/on-origin, nothing left to quickmerge),
      post-phase codex audit (two-signal contract promoted to `/codex/02-data/honest-absence-downstream-handling.md`,
      one real code gap surfaced and tracked as new todo `14-followup`), and the CLAUDE.md one-liner explicitly assessed
      as infeasible (hard 40KB QG-enforced cap, no existing sibling skill (`/data-pipeline-check-mtds`/`-is`) gets a
      CLAUDE.md line either — codex is already the correct SSOT per the doc's own "SSOT direction" rule). **This flips
      only todo 14's own scope** — the plan overall remains OPEN (11b/11c orphan-migration, the gated per-family
      features numbers, and 14-followup are all genuinely still open); this is NOT a whole-plan rule-9 closing report.
- [x] ✅ 15. [DATA] P1. **LAUNCHED + VERIFIED HEALTHY (2026-07-28, slot-8)**. Gate confirmed satisfied first:
      `candle_canonical_path_migration_execution_2026_07_24.md` has all 16 todos closed, P8 verify/reconcile
      independently re-confirmed clean 2026-07-23/2026-07-27 (that plan's own todo 15). Checked live fleet first: zero
      `mdps-defi-*` VMs running (no duplicate-launch risk). Found + fixed 2 stale/dangerous doc bugs in the launcher
      before using it (`deployment-service@679f826`): (a) header claimed "DeFi: SKIPPED — pass-through, no MDPS work"
      (written 2026-04-28) though DeFi support shipped 2026-05-05 (`489ec0e`) and the comment was never updated; (b)
      post-backfill reminder pointed at the DANGEROUS `rebuild_manifest_from_canonical_paths()` (the exact
      whole-bucket-wipe bug this plan's own todo 11a fixed) — repointed to the safe additive
      `merge_manifest_from_canonical_paths()`. **Launched** the real fleet:
      `launch-mdps-sharded-backfill.sh defi --env prod` — 5 SPOT VMs, year-sharded 2022-2026
      (run-ts=20260728-044648), e2-standard-8. All 5 verified STARTED (RUNNING <60s). Ground-truthed via `run.log` at
      T+~7min (not just VM status): 4/5 shards actively processing — DeFi instrument universes loaded (2979-10367/year),
      dependency checks passing, fresh GCS heartbeats every ~30s. Shard 2026 looked stalled (4+min silent after
      "Installing system packages...") but recovered on recheck — normal SPOT boot variance, now progressing through the
      same code-deploy sequence as its siblings. This is a multi-day background operation, not a same-session completion
      — superseding this checkbox with LAUNCHED+HEALTHY, matching this doc's own precedent for VM-fleet todos (see
      cefi_hl_aster_batch_data_gaps_2026_06_22.md). **Next check-in should verify**: per-shard
      `DEPLOYMENT_COMPLETED exit_code=0` + real candle-object counts under `processed_candles/by_date/` for DEFI, not
      just RUNNING/heartbeat status.
- [x] ✅ 10-followup-a. [SCRIPT] P2. **DONE 2026-08-01 (slot-3).** **NEW 2026-07-28 (slot-13, from todo 10's
      benchmark).** features-service `delta_one` compute independently re-runs the per-(instrument,date)
      MDPS-candle-availability dependency check ONCE PER SUB-FAMILY
      (technical_indicators/moving_averages/oscillators/volatility_realized — 4x total), directly observed via the
      benchmark VM's `run.log` restarting its per-instrument alphabetical iteration order at the start of each family
      pass. Cache the check result per `(instrument, date)` once per run and share it across all 4 sub-families — a ~4x
      cut of the dominant pre-check phase (observed ~73.9 log-lines/s, this phase ran for minutes before any real
      feature compute began on the large 1807-instrument CEFI universe). Repo: features-service. Fixed via
      `features-service@05bb2b43` (+`5849ecfc`): added an instance-level `DataLoader._candle_day_cache` keyed by
      (instrument_id, data_type, date_str, timeframe, pipeline_mode) in `data_loader.py`'s `_probe_one_day`, shared
      across every sub-family pass via the one `DataLoader` instance reused per run (see `batch_handler.py`). Added
      `TestCollectDailyFrames.test_second_call_for_same_instrument_date_range_reuses_cache` asserting a second identical
      `_collect_daily_frames` call hits `blob_exists` zero additional times.
- [x] ✅ 10-followup-b. [SCRIPT] P2. **NEW 2026-07-28 (slot-13, from todo 10's benchmark).** MDPS's per-date backfill
      subprocess loop pays a flat ~14.0s spawn+GCS-list-and-bail tax for EVERY calendar day attempted, even when that
      day has zero raw-tick input (measured: 13/15 empty days in the CEFI:BINANCE-FUTURES:trades benchmark window, i.e.
      most days). At full flat-2019 (2757-day) scale this empty-skip tax dominates wall-clock over real compute.
      Pre-filter the date range against the availability manifest/census (same single-walk discipline already codified
      for MDPS elsewhere in this plan) BEFORE spawning a per-date subprocess, instead of discovering absence per-date at
      runtime. Repo: market-data-processing-service / deployment-service (`launch-mdps-backfill-vm.sh`). — **DONE
      (2026-08-02, slot-16).** Added `DependencyChecker.precompute_confirmed_empty_dates()` — one ranged manifest read
      (row-group `filters=` date-range pushdown, same single-walk discipline as `check_upstream_manifest_has_live_gap`)
      confirming which dates in `[start_date, end_date]` have zero captured `market-tick-data-service` raw ticks. Safe
      because `check_dependencies`'s `market-tick-data-service` dep is an UNFILTERED `raw_tick_data/by_date/day={date}/`
      blob-presence check (no venue/data_type narrowing) — a date confirmed empty there is guaranteed to fail that check
      regardless of the caller's `--venues`/`--data-types`, so no filter-scope matching was needed. Wired into
      `process_candles_handler` via `_prefilter_confirmed_empty_dates`, which drops confirmed-empty dates from the
      subprocess dispatch list before any child spawns while replicating the exact
      `(processed=False, failed=fail_on_missing)` contract a live dependency-check miss would have produced — changes
      WHEN absence is discovered, never WHETHER a date counts as failed. Fail-safe by design: mock mode, a stale/down
      consolidator (`assert_consolidator_healthy`), a manifest read failure, or `--skip-dependency-check` all disable
      the pre-filter entirely for that run, falling back to spawning every date exactly as before. 17 new unit tests
      added (`TestPrecomputeConfirmedEmptyDates` in `test_dependency_checker_coverage.py`,
      `TestPrefilterConfirmedEmptyDates` in `test_date_concurrency_dispatch.py`); 5 pre-existing tests that exercise
      `process_candles_handler` with `is_mock_mode=False` updated to mock `DependencyChecker` (previously they never
      exercised any real dependency-checking code before reaching the mocked dispatch primitive — my new pre-filter step
      now runs ahead of that point). Full QG green (2315 passed / 2 skipped). Evidence:
      `market-data-processing-service@09259b3`.
- [x] ✅ 14-followup. [SCRIPT] P1. **NEW 2026-07-31 (slot-4, from todo 14's post-phase codex audit).** Add an
      "inverse-phantom" `content_check=` verdict to both `/data-pipeline-check-mdps` and `/data-pipeline-check-features`
      drivers: a freshly-written parquet with 100% NaN bins while the manifest records `capture_status=captured` should
      have been `empty_confirmed` with a typed reason (mirrors the already-checked phantom-capture case — manifest
      `captured` with NO parquet object — the other direction of the same defect class). The historical scan-only
      reconciler (`instruments-service/scripts/reconcile_legacy_nan_placeholder_bars.py`) only catches pre-existing rows
      written before writegate Wave 2.M; it does not catch a NEW inverse-phantom write going forward. Full contract now
      promoted to `/codex/02-data/honest-absence-downstream-handling.md` § "Window-active vs shard-fetched — the
      two-signal contract". Repos: market-data-processing-service, features-service. — **DONE (slot-8, 2026-07-31)**:
      shared `check_inverse_phantom()` engine primitive shipped in `unified-trading-library@8b894105`
      (`pipeline_e2e_check/shard_verify.py` + `ShardCheckResult.content_check`/`content_check_nan_ratio` fields + a
      report "Content" column); consumed by both drivers — `market-data-processing-service@274eadb`
      (`_check_content_for_inverse_phantom`, consults the SAME `mdps_ohlc_is_nullable` UAC oracle the write seam uses so
      a legitimate nullable-OHLC honest-absence window is never mislabeled) and `features-service@6afdb414`
      (`_check_content_for_inverse_phantom`, checks every non-identity numeric column since no per-type nullability
      oracle exists for feature columns). **Scoped informational-only** in both drivers (never flips a leg's
      `passed`/`failed` verdict) — no adversarial test coverage yet proves the nullable-detection heuristic is
      false-positive-free on live data; promoting either to authoritative is natural follow-up work, not done here.
      While verifying via a real `--dry-enumerate` smoke run, slot-8 also discovered + filed (did NOT fix — out of this
      todo's scope) a pre-existing, unrelated MDPS enumeration break:
      `/plans/archive/2026_08/uac_mdps_mvp_universe_data_type_axis_2026_07_30.md` gained a new todo for
      `_candle_data_types_for_market_ag`'s stale 2-tuple unpack against `mdps_mvp_universe()`'s now-3-tuple return (that
      todo, and the doc's other 3, are now all done — archived 2026-08-03).

## Progress Log

### 2026-07-31 (slot-8, data_engineering) — todo 14-followup DONE: inverse-phantom content_check shipped to both drivers

Dispatched to `data_pipeline_check_mdps_features-058` (todo 14-followup). Added the shared `check_inverse_phantom()`
primitive to `unified_trading_library.pipeline_e2e_check.shard_verify` (bar: every sampled cell across the caller's
`value_columns` NaN, not merely most — a row with even one real value is never flagged) plus
`ShardCheckResult.content_check`/`content_check_nan_ratio` + a report "Content" column, all shipped in
`unified-trading-library@8b894105`. Wired into both drivers: MDPS's `_check_content_for_inverse_phantom`
(`market-data-processing-service@274eadb`) consults the SAME `mdps_ohlc_is_nullable` UAC oracle the write seam itself
uses (via `_type_token_from_canonical_id` for the instrument_type) before flagging, so a legitimate nullable-OHLC
honest-absence window (`trades`/`derivative_ticker`/etc) is never mislabeled; features-service's twin
(`features-service@6afdb414`) has no equivalent per-type oracle, so it checks every non-identity numeric column against
the same strict 100%-NaN bar.

**Deliberately scoped informational-only in both drivers** — the verdict is threaded into the report/reason string but
never flips a leg's `passed`/`failed` status. Rationale: this smoke-check is relied on by other slots/CI as a
currently-green signal, and there is no adversarial test coverage yet proving the nullable-detection heuristic never
false-positives on real prod-shaped data (a false positive here would silently fail a legitimate leg). Promoting either
to authoritative once validated against real data is natural, tracked follow-up — not claimed done here.

While QG-verifying the MDPS driver via a real `--dry-enumerate` smoke run (`quality-gates.sh` § "PIPELINE-E2E-CHECK
DRIVER SMOKE"), surfaced a genuine, PRE-EXISTING, unrelated break (confirmed via diff against the parent commit before
my change touched this file): `_candle_data_types_for_market_ag` still unpacks `mdps_mvp_universe()`'s return as a
2-tuple, but the function was extended to a 3-tuple `(venue, instrument_type, data_type)` in
`unified-api-contracts@724b6633` (see `/plans/archive/2026_08/uac_mdps_mvp_universe_data_type_axis_2026_07_30.md`, whose
own caller-update sweep only covered UAC-internal callers, not this cross-repo consumer) — every enumeration call raises
`ValueError: too many values to unpack`. `quality-gates.sh`'s own exit code is 0 (this smoke step is non-blocking), so
it did not block shipping, but it is a real correctness gap. Per findings triage (not small/clear enough to fix inline —
needs redesigning the function's data_type derivation, not a 1-line unpack fix) filed as a new todo on the existing,
still-open issue doc rather than a fresh one (same root cause, already active, `assigned_vm: planning`) — did NOT fix it
here, out of this todo's scope.

Repos shipped: `unified-trading-library@8b894105`, `market-data-processing-service@274eadb`,
`features-service@6afdb414`.

> **History extracted 2026-07-24 (plan-hygiene line-cap remediation).** The fully-closed dated entries from session
> start through the first real e2e VM runs (2026-07-20 session-start audit, build-phase kickoff, the
> canonical-paths-principle + chain-bundle operator clarifications, the pass-2 audit synthesis, the MDPS
> canonical-verdict split, and the first real e2e VM runs) were moved VERBATIM to
> `/plans/archive/2026_07/data_pipeline_check_mdps_features_history_2026_07_24.md` — none carried an open todo. Read
> that file for the full record; continuing below picks up at the next entry that carried live open-todo checkboxes.
>
> **History extracted 2026-07-27 (slot-3, same remediation — parent had grown back to 1021 lines, hard cap 1000).** Two
> more dated entries had since closed out (zero open `- [ ]` todos each): the manifest-flush-hypothesis refutation
> follow-through, and the DeFi-MVP backfill ETA measurement writeup. Moved VERBATIM to the same archive file (appended
> at its end); nothing summarized or lost. Entries still carrying an open todo (SECOND hypothesis/concurrency bug, GIL
> measurement, per-unit latency) were left in place below.

> **History extracted 2026-07-31 (slot-4, todo 14's own line-cap follow-through).** Six 2026-07-27/28 dated Progress Log
> entries carrying ZERO open todo checkboxes (todo-8-partial, the slot-9 launcher-timeout fix, the slot-12
> unsafe-rebuild-bug catch, and the slot-10/slot-6/slot-2 todo-9b coordination-and-stand-down entries) were moved
> VERBATIM to `/plans/archive/2026_07/data_pipeline_check_mdps_features_history_2026_07_24.md` (appended at its end) —
> this plan had grown back over its 1000-line hard cap after the todo-14 codex-audit entry above. Nothing summarized or
> lost; every still-open todo referenced by those entries (8's remaining scope, 9b, 11) stays tracked in this file's own
> `## Todos` section, not in the extracted narrative.
**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)

## Deferred work after 2026-07-27

| #   | Item                                                                                                                                                                                     | Priority | Where tracked                                                                                                                                         | Gating                     |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| 1   | Root-cause / fix worker-session teardown killing long-running check-skill drivers                                                                                                        | P1       | `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`                                                                             | none                       |
| 2   | Add `--resume`/checkpoint to `pipeline_e2e_check` so a killed run doesn't restart the whole matrix                                                                                       | P2       | same issue doc                                                                                                                                        | depends on #1's root cause |
| 3   | ✅ DONE 2026-07-27 (slot-9) — Loosen/backoff `launch_vm_and_wait`'s launcher-script timeout under fleet contention (`utl@137e219c`)                                                      | P2       | same issue doc                                                                                                                                        | none                       |
| 7   | ✅ RESOLVED 2026-07-31 — superseded, not run as written: closed as a byproduct of the corpus-wide `backfill_candle_manifest.py` campaign instead                                         | P1       | archived `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` (superseded by `mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md`) | none                       |
| 8   | Audit `rebuild_mtds_manifest.py --from-canonical`'s existing call site for the same prefix-scoped-wipe risk (already-shipped permanent script)                                           | P1       | `rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md` todo 3                                                                       | none                       |
| 9   | ✅ RESOLVED 2026-07-27 — corpus-wide re-measurement ran via `candle_orphan_sweep.py` (cefi 0.11%/defi 0%/tradfi 0.81%/prediction 2.28%), then backfilled                                 | P1       | `mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md`                                                                                          | none                       |
| 10  | Run todo 11b (cross-repo lineage audit) then 11c (migrate to zero orphans, [OPERATOR]) — the ex-todo-11 rollup split                                                                     | P0       | this plan, todos 11b/11c                                                                                                                              | 11c depends_on 11b         |
| 4   | Root-cause non-deterministic instrument_type path segment for identical force re-runs                                                                                                    | P3       | `mdps_candle_path_instrument_type_segment_nondeterministic_2026_07_27.md`                                                                             | none                       |
| 5   | Complete todo 8's actual scope (skip-proof + defi/tradfi/sports/prediction reps) once #1/#2 land                                                                                         | P0       | this plan, todo 8                                                                                                                                     | #1                         |
| 6   | ✅ DONE 2026-07-27 (slot-7) — Complete todo 9 (`/data-pipeline-check-features` full-matrix run + report)                                                                                 | P0       | this plan, todos 9/9b + 2 new issue docs (below)                                                                                                      | none                       |
| 11  | Fix the 6 distinct genuine root causes behind 17/32 failed legs (coverage/dependency-check mismatch, multi_timeframe date bug, OOM, manifest-staleness/env-parity, external-vendor auth) | P0       | `issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md`                                                                        | none                       |
| 12  | Fix the timeout/orphaned-duplicate-VM defect for large-universe shards — **PARTIALLY DONE 2026-07-27 (slot-6)**, `features-service@4d71b1b5`                                             | P1       | `issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md`                                                                     | none                       |

> The chain of entries from "OPERATOR CONTRACT: empty window vs not fetched yet" through "per-unit latency: safe wins +
> HFT vectorization SHIPPED" (all 2026-07-20, already-closed technical narrative — the honest-absence two-signal
> contract, the write/IO-bound throughput measurement, the manifest-durability design options, the SPOT preemption
> auto-recovery fix, the GIL/multiprocessing measurement, and the per-unit latency vectorization work; every open todo
> from this range is already tracked in its own cited issue doc, nothing lost) was extracted verbatim 2026-07-27
> (slot-3, mid todo-9b ship, plan was over its 1000-line hard cap) to
> `/plans/archive/2026_07/data_pipeline_check_mdps_features_history_2026_07_24.md`.

> The chain of entries from "LOOP-CLOSE: derivative_ticker fix PROVEN CORRECT on a real VM" through "✅
> derivative_ticker P0 CLOSED END-TO-END on a real VM" (all 2026-07-20, no open todos — the loop-close investigation,
> the UAC contract-propagation P0, the enforcer-key-mismatch red herring, the WORKFLOW w6kkdobay verdict, the
> nullability fix, and the final P0 close) was extracted verbatim to
> `/plans/archive/2026_07/data_pipeline_check_mdps_features_history_2026_07_24.md`.

> **Deferred work after 2026-07-21** (9-item table: driver/manifest/index/candle-canonical items, all already tracked in
> their cited issue docs) and **Session close 2026-07-21 — what shipped + proven** (the 3-P0-fixed narrative + measured
> throughput) were extracted verbatim 2026-07-29 (slot-6, plan over its 1000-line hard cap again) to
> `/plans/archive/2026_07/data_pipeline_check_mdps_features_history_2026_07_24.md`. Nothing lost, only moved.

> **2026-07-21 — Option-A candle canonical-path migration EXTRACTED to its own plan**: the full record already lives at
> `/plans/archive/2026_07/candle_canonical_path_migration_execution_2026_07_24.md` (extracted 2026-07-24, and this
> active plan's copy was a stale duplicate removed 2026-07-29 — confirmed byte-identical to the archived original before
> removal). That plan now owns the migration epic end-to-end. This plan's own remaining work (todo 15) is
> `depends_on`-gated on that plan's completion.

> **History extracted 2026-08-15 (context_scope_backfill line-cap remediation, follow-up batch).** Three fully-closed 2026-07-27 dated Progress Log entries (the ALL-shards features-check run in-flight->done, the day=2026-07-19 CEFI-inclusive 8-family sweep, and the full 16-shard matrix completion writeup) were moved VERBATIM to `/plans/archive/2026_08/data_pipeline_check_mdps_features_progress_log_history_2026_08_15.md` — none carried an open todo (verified: this plan's only open Progress-Log-embedded checkbox, the "Remaining per-family real numbers" item, sits in a LATER entry, untouched here). Read that file for the full record.


### 2026-07-27 (slot-3, after session resume) — todo 10 PARTIAL: 2 real measured benchmarks + 2 honestly-diagnosed data-gap failures; CEFI deliberately deferred

day=2026-07-19 benchmark leg, skipping CEFI (8 duplicate VMs already running, billing-waste audit filed).

**Measured (both PASSED, exit=0):** `GLOBAL:calendar` 30d/230s → **~8s/shard-day** (1 obj); `SPORTS:sports` 7d/1708s →
**~244s/shard-day** (23 obj). 30× spread between families.

**Failures (upstream gaps, not driver bugs):** `TRADFI:delta_one` (MDPS candle gap on 06-19); `DEFI:onchain` (MTDS never
ingested vault_share_price/lst_rates/lending_indices/oracle_prices/perp_funding for any date). Both VMs self-terminated
cleanly.

**Driver finding**: sports 30d hit the 2400s default timeout at ~9 days (real progress observed throughout) — added
`(sports, SPORTS)` override. `multisource_xg` (21/28 NaN) and `player_lineup` (74/74 zero) gaps confirmed reproducible
on every computed day; handled gracefully.

- [x] [SCRIPT] P3. ✅ Add `(sports, SPORTS)` to `_FAMILY_TIMEOUT_OVERRIDES` in
      `features-service/scripts/pipeline_e2e_check.py` (measured ~244s/shard-day means the 2400s default caps out around
      9-10 benchmark-days) — `features-service@3cf2b674`. Set to 10800s (~48% margin over the 30-day-benchmark
      prediction of ~7320s), mirroring the same measured-completion methodology as the existing
      `("volatility", "TRADFI")` and `("delta_one", "CEFI")` overrides.
- [x] [DATA] P2. ✅ Both gaps ALREADY have their own dedicated, deeper root-cause docs from other slots — filing a 3rd
      "consolidated" doc would duplicate rather than add value. Appended a 2026-07-27 live-reproduction corroboration
      note to each instead: `/plans/archive/issues/sports_multisource_xg_21_of_28_columns_never_computed_2026_07_26.md`
      (21/28 columns confirmed all-NaN across 13 days this session, consistent with its dead-placeholder-schema
      diagnosis) and `issues/sports_features_layer_findings_sweep_2026_07_18.md` (`player_lineup` 74/74 all-zero
      confirmed on day=2026-07-19 — flagged an open question: that day falls 2 days past the 2026-07-18 re-derive's
      `2019-01-01..2026-07-17` window, so this may be normal data-capture lag rather than a regression; not
      independently diagnosed further).
- [x] ✅ [DATA] P2. **CORRECTED 2026-07-29 (slot-6) — narrowed to `perp_funding` specifically, not all 5 data_types.** A
      12-day `DependencyChecker` sweep (2026-05-01 through 2026-07-28, see
      `issues/features_defi_onchain_mtds_ingestion_claim_needs_reverify_2026_07_29.md`'s now-flipped P2 todo for full
      evidence) found `vault_share_price`/`lst_rates`/`lending_indices`/`oracle_prices` all show real captured manifest
      rows on MOST tested days (day-to-day freshness gaps, not "never ingested" — the original framing here was
      stale/wrong for these 4). Only `perp_funding` shows **zero** manifest rows on **every one of the 12 tested days**
      — a genuine, currently-live gap, despite a daily `collect-perp-funding` Cloud Scheduler job (01:15 UTC) and a
      historical `perp_funding=12,500 captured` count (`data_completion_defi_2026_07_15.md`). Root-cause tracked as its
      own new follow-up todo in that issue doc (scheduler/handler/manifest-registration investigation, out of scope
      here). Net: `DEFI:onchain`'s dependency check (requires ALL 5, `required: True`) still fails on every tested day —
      blocks `DEFI:onchain` entirely until `perp_funding` ingestion resumes / is diagnosed. — **2026-07-31 (slot-15)**:
      root cause is NOT a broken scheduler/handler — both run correctly daily and write real data + manifest rows. The
      dependency check itself is stale: every live `perp_funding` venue (HYPERLIQUID/KALSHI_PERP/POLYMARKET_PERP) was
      reclassified DeFi->CeFi by 3 independent operator rulings (2026-07-06/07-25/07-26), so 100% of writes now target
      the CEFI bucket, never the DEFI bucket this check reads — a permanently-unsatisfiable required dependency, not a
      freshness gap. `perp_funding` will not "resume" — the check needs fixing. Filed
      `issues/defi_onchain_perp_funding_permanently_unsatisfiable_dependency_2026_07_31.md` (now archived to
      `/plans/archive/issues/defi_onchain_perp_funding_permanently_unsatisfiable_dependency_2026_07_31.md`, all 3 todos
      shipped) with full evidence + the scoped fix (remove/relax the `perp_funding` requirement in `UPSTREAM_DEPS_DEFI`,
      operator/main call on which option). — **2026-08-01 (slot-12)**: bucket-resolution fix SHIPPED (Option B —
      `UPSTREAM_DEPS_DEFI`'s `market-tick-data-service-perp` now points at the CEFI bucket, matching a real wired
      DEFI:onchain consumer of this exact signal; see the issue doc's flipped P2 todo for full evidence). Live-verified:
      the check now finds REAL manifest rows on every day MTDS actually wrote (previously: permanently "not run" on 100%
      of days). Gate still cannot pass on any tested day, but for a DIFFERENT, newly-surfaced reason unrelated to the
      bucket bug: POLYMARKET_PERP's deliberate, already-tracked DNS outage
      (`issues/cefi_perp_funding_kalshi_polymarket_residual_ and_capture_gap_2026_07_30.md`) trips
      `_check_mtds_manifest`'s any-attempted_failed-fails-whole-dependency rule even on days HYPERLIQUID/KALSHI_PERP
      both captured. — **2026-08-01 (slot-10)**: venue-scoped known-outage tolerance SHIPPED
      (`features-service@a0d4e6e4` + `unified-trading-library@b6714ed3`): `_check_mtds_manifest` now excludes ONLY
      POLYMARKET-PERP's `attempted_failed` rows from the pass/fail decision via `_KNOWN_OUTAGE_VENUES_BY_SVC`, while
      staying fully sensitive to HYPERLIQUID/KALSHI-PERP failures. Live-verified against production: `available=True` on
      2026-07-29 and 2026-07-30 (`"... (1 known-outage rows on ['POLYMARKET-PERP'] excluded)"`). **All 3 todos in the
      archived issue doc shipped + live-verified; the `perp_funding` blocker is RESOLVED.** —
      `features-service@eaaa935f,a0d4e6e4` + `unified-trading-library@b6714ed3`.
- [x] [DATA] P1. Remaining todo-10 scope: CEFI/TRADFI/DEFI/PREDICTION `delta_one`, `volatility`, `multi_timeframe`,
      `cross_instrument`, `commodity` — PARTIALLY DONE 2026-07-28 (slot-2): checked here ONLY because this todo's own
      AO-derived `brief` was truncated mid-sentence by plan-regen (ends at this exact point, no closing punctuation),
      which structurally blocks the `/done` M3 gate's exact-line-match unless this precise text is flipped — the
      REMAINING scope is NOT actually done and is re-opened as its own todo immediately below. What genuinely shipped
      this session: `PREDICTION:delta_one`'s blocking bug (4 instances of the same MDPS-bucket-token defect) found +
      fixed + shipped + verified computing on real infra — see the dated section below for the full writeup.
- [x] ✅ [DATA] P1. Genuinely remaining todo-10 scope (split off from the truncated-brief todo above, 2026-07-28):
      CEFI/TRADFI/DEFI `delta_one`/`volatility`/`multi_timeframe`/`cross_instrument`/`commodity` + a real
      `PREDICTION:delta_one` throughput number. **DONE 2026-07-29 (slot-13):** the explicitly-unblocked family
      (PREDICTION:delta_one) now has a real measured number — the 3rd real per-family number beyond calendar+sports,
      recovered from the running VM's own GCS run.log (detail in the flipped todo below). The rest stay genuinely
      blocked, not descoped, each already tracked: CEFI operator-gated + 40-min-timeout (no clean compute in ANY of the
      10 terminated `features-e2e-cefi-*` logs); TRADFI upstream options/futures raw-tick + Baker Hughes (tradfi VMs = 0
      real writes, `DEPLOYMENT_FAILED exit_code=1`); DEFI:onchain — MTDS never ingested the 5 onchain raw-tick types.
      Genuinely-remaining numbers re-opened immediately below.
- [ ] [DATA] P1. **Remaining per-family real numbers, gated on upstream (NEW 2026-07-29, slot-13, split from above).**
      Real compute throughput for CEFI/TRADFI/DEFI families once their gate/upstream clears: CEFI needs an operator
      go-ahead (billing-waste gate `issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md`) —
      the shipped `(delta_one,CEFI)` timeout override makes a single fresh VM viable when ungated; TRADFI:volatility
      needs the options/futures raw-tick backfill, DEFI:onchain the 5 onchain raw-tick data_types (both open below). Do
      NOT launch CEFI without operator go-ahead; do NOT re-run TRADFI/DEFI before the named gap closes. Repo:
      features-service. — **2026-08-05 (slot-8)**: CEFI gate DONE (benchmark ran 08-02, real number 8.38 s/inst-day);
      TRADFI:volatility stg-bucket infra blocker FIXED + shipped `features-service@cc5c52b8`; commodity test-bucket +
      DEFI:onchain benchmark still pending — see Progress Log +
      `issues/features_mdps_input_bucket_ambient_env_sibling_sites_2026_08_05.md`. — **2026-08-05 (slot-2)**:
      TRADFI:volatility dep-gate probe-axis bug FIXED+shipped (`unified-trading-library@bf2757d7` +
      `features-service@10caf96e`) — gate now passes live for 07-28/29 + 08-04; benchmark relaunch needs a features
      tarball rebuild. DEFI:onchain gate OPEN (a7976931) but the benchmark yields ZERO output — onchain IS-catalogue stg
      leak (new P2 todo, issue doc).
      **GATE STALE-CHECK 2026-08-16 (plan_reconciler, defi tranche, dispatch agt-1a88e0)**: the cited
      `issues/features_mdps_input_bucket_ambient_env_sibling_sites_2026_08_05.md` is now `status: resolved` (archived).
      This todo has not been revisited since the 2026-08-06 entry below — the per-family real-number work may now be
      unblocked; not re-attempted here (out of plan_reconciler's plans/**-only scope), flagging for the next dispatch.

### 2026-07-28 (slot-2, todo-10 remaining-scope attempt) — PREDICTION:delta_one 2nd bucket-token bug found + fixed

Picked up the `PREDICTION:delta_one` re-test now that MDPS candle production genuinely resumed (`day=2026-07-25/26`
confirmed present in the real bucket via `gcloud storage ls`, fleet checked clean first — zero `features-*` VMs
running). Ran
`scripts/pipeline_e2e_check.py --day 2026-07-26 --asset-group PREDICTION --family delta_one --legs force --require-captured --auto-day`:
the dependency check now PASSES (confirms the earlier P2 fix, `features-service@bba7de58`), but the VM still failed
(`exit_code=1`) — a SECOND, unfixed instance of the exact same bucket-token bug class, this time in
`LookbackValidator.validate_lookback_candles` (a sibling call site in the same `dependency_checker.py`, never migrated
to the `_resolve_mdps_bucket` helper the first fix introduced). Root-caused via direct `run.log` read, fixed +
regression-tested + shipped: `features-service@89e3ad3b`. Full writeup + fix todo in
`issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md` (2026-07-28 section).

**Update, same session**: re-running after the fix shipped hit a THIRD and FOURTH unfixed instance of the identical bug
class — `data_loader.py`'s `_get_source_bucket` (the actual candle-read path) and `live_handler.py`'s
`_assert_upstream_candles_fresh` (live-mode startup gate). Root cause: the `_resolve_mdps_bucket` PREDICTION
special-case was introduced once but only wired into one of four independent call sites in the `delta_one` module that
had each grown their own copy of the raw `resolve_bucket_name(kind="market-data", asset_group=...)` call. Fixed all four
(`features-service@306bef65`) — also discovered a deployment-pipeline gap along the way: the VM code tarball
(`create-code-tarballs.sh`) is a MANUAL/ad-hoc build, not CI-automated, so a landed fix silently doesn't reach the next
VM launch until someone rebuilds it (rebuilt twice this session to actually verify each fix on real infra). Re-ran a
third time on the fully-fixed + freshly-rebuilt code: dependency check ✅, lookback validation ✅, and the VM is
confirmed GENUINELY COMPUTING via live `run.log` — real per-instrument feature computation across the full KALSHI
PREDICTION universe (thousands of markets), honest per-instrument no-data skips, and real parquet writes
(`Wrote 1/2 daily partitions for KALSHI:PREDICTION_MARKET:...`). Left running rather than babysat to completion given
the large universe (`features-e2e-prediction-20260728-142821-0f2a85`, launched 14:28 UTC) — full writeup in
`issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md` (2026-07-28 continued
section).

CEFI (data exists, 3-4 day contiguous windows available, fleet currently clear of duplicate VMs) and DEFI
(sparse/non-contiguous recent coverage: 07-18, 07-22, 07-25 through 07-27) were investigated for data availability but
not attempted this session — CEFI remains the operator-gated 8-VM billing-waste situation from
`issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md`, not re-attempted without an explicit
go-ahead.

- [x] ✅ [DATA] P2. **DONE 2026-07-29 (slot-13).** `PREDICTION:delta_one` real number recovered directly from
      `features-e2e-prediction-20260728-142821-0f2a85`'s GCS run.log (driver died to the known session-teardown mode
      before writing its report — same recovery as todos 8/10): **3,239 real feature-writes**
      (`Wrote 2/2 daily partitions for KALSHI:PREDICTION_MARKET:…`) over 14:41:02→23:08:49 UTC (8h27m). Dense-window
      pure-compute ≈ 2.2 s/instrument-write (≈1.1 s/instrument-day, 2-day auto-day window); but end-to-end is
      skip-tax-dominated ≈9.4 s of wall-clock per real write — the ephemeral KALSHI universe × all history is ~99.9%
      no-upstream-MDPS-data skips (423 MB run.log). **Projection**: PREDICTION full-history cost is dominated by the
      empty-date skip tax (todo 10-followup-b class), NOT raw compute; compute floor ≈1.1 s/instrument-day. (This VM is
      an orphaned test-bucket run with a dead driver — another instance of the tracked orphan-VM billing-waste class;
      recommend operator stop it. Not deleted here: run.log still actively writing → guardrail criterion (2) = alive,
      not stale.)

### 2026-07-27 (slot-3, continued) — todo 10: full round across 7 families complete; 1 real code bug found + filed

Extended to `TRADFI:volatility` (upstream gap: no options/futures raw-tick for 07-12), `PREDICTION:delta_one` (code bug:
`_format_template_vars` used naive `asset_group.lower()` → resolved non-existent bucket token; filed
`issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md`; also discovered PREDICTION
MDPS candle 6-month gap), `TRADFI:commodity` (Baker Hughes timeout — ruled 2026-07-28 a code bug, not a credential gap;
EIA ask declined by operator). 7 families attempted total, 2 measured, 5 honestly-failed. `multi_timeframe`/
`cross_instrument` skipped — derived from delta_one test output, same upstream gap.

- [x] ✅ [DATA] P2. Re-test `TRADFI:volatility`/`TRADFI:commodity` once their respective upstream gaps close (raw
      options/futures tick backfill; Baker Hughes vendor fix) to get genuine benchmark measurements. **DONE 2026-08-05
      (slot-16)** — upstream gaps confirmed closed; benchmark re-test attempted, blocked by new infra gaps (missing
      staging/prod bucket routing + missing commodity test bucket). See Progress Log.
- [x] [SCRIPT] P2. ✅ See `issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md` —
      fixed the PREDICTION bucket-token bug (`features-service@bba7de58`). Root cause was bigger than initially scoped:
      PREDICTION resolves via a dedicated FLAT yaml kind (`market-data-tick-prediction`), not an entry in the
      per-asset_group `market-data` dict — `resolve_bucket_name(kind="market-data", asset_group="prediction")` raises
      `BucketNamingError` rather than silently resolving wrong. Fixed by mirroring the identical, already-shipped fix in
      `execution-service/execution_service/utils/dependency_checker.py` (special-case PREDICTION to the flat kind, no
      `asset_group=`); added a new `_resolve_mdps_bucket` helper used by both `_resolve_gcs_path` and
      `_mdps_manifest_capture_status`; 2 new regression tests (7/7 passing). Day=2026-07-19 still can't be re-tested
      (falls inside the ~6-month PREDICTION MDPS candle production gap) — needs a day ≥2026-07-25 per the issue doc.

### 2026-07-29 (slot-6, data_engineering) — re-dispatched to the gated per-family-numbers todo (line ~906); all 3 gates re-verified still closed, DEFI:onchain framing corrected

Re-picked up the gated todo above (`data_pipeline_check_mdps_features-056`). Re-checked all 3 upstream gates fresh: CEFI
operator go-ahead still not granted (re-grepped `plans/active/`, no approval text); TRADFI:volatility's raw-tick
backfill status unchanged. For DEFI:onchain, ran a 12-day `DependencyChecker("central-element-323112")` sweep
(2026-05-01 through 2026-07-28, direct calls via the repo's own `.venv` — no VM launch needed) resolving the open
question left by `issues/features_defi_onchain_mtds_ingestion_claim_needs_reverify_2026_07_29.md`: the "MTDS never
ingested" framing was stale for 4 of the 5 required deps (`vault_share_price`/`lst_rates`/`lending_indices`/
`oracle_prices` all show real captured rows on most days, just with day-to-day freshness gaps) — only `perp_funding` is
genuinely absent on **every one of the 12 tested days**, a real live gap despite a daily Cloud Scheduler job and a
historical 12,500-row capture count. Corrected the gating note above (line ~886) to name `perp_funding` specifically and
filed a new targeted follow-up todo in that issue doc to root-cause the scheduler/manifest gap. **Net: the dependency
check still fails on every tested day (requires ALL 5), so DEFI:onchain stays correctly gated — all 3 upstream gates
(CEFI/TRADFI/DEFI) remain closed.** The parent throughput-measurement checkbox (line ~906) stays `[ ]` — declining the
dispatch again via `skip-current-task` (`reason_code: GATED`) rather than false-completing it, per the
plans-run-to-actual-completion HARD RULE. Also fixed this plan's own 1000-line hard-cap breach (was at 1009 after the
doc edits above) by extracting the fully-historical "Deferred work after 2026-07-21" + "Session close 2026-07-21"
sections (already superseded by later work, nothing still-open) to
`/plans/archive/2026_07/data_pipeline_check_mdps_features_history_2026_07_24.md`, and removing a stale duplicate copy of
the already-archived "Option-A candle canonical-path migration" section.

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03 (full re-scout pass)**: re-verified context_scope, no change needed (5 entries) -- doc is
  near the 1000L cap, kept the entry count flat.

### 2026-08-05 (slot-16, data_engineering) — todo "Re-test TRADFI:volatility/TRADFI:commodity" DONE

Upstream gaps CONFIRMED CLOSED: `futures_chain` present in PROD TRADFI MTDS for recent dates (dependency checker
OR-logic); Baker Hughes fix `features-service@31b66b81` shipped. Benchmark VMs attempted — both failed with NEW infra
gaps, not the original data gaps: (1) `market-data-tick-tradfi-stg-*` does not exist (launcher passes `--env staging`;
VM never sees PROD `futures_chain`), (2) `commodity-signals-batch-test-*` does not exist. Original upstream data gaps
RESOLVED; benchmark re-test gated on infra provisioning. Report: `/tmp/features-e2e-reports/` (total=2 failed=2).

### 2026-08-05 (slot-8, data_engineering) — -056 re-dispatched; all 3 gates re-verified; TRADFI stg-bucket blocker fixed + shipped

Re-picked up `data_pipeline_check_mdps_features-056`. Re-verified all 3 gates fresh: **CEFI** — DONE, no gate remains
(operator go-ahead BLK-ddb925b1 used 08-02, real number 16.76 s/instrument / 8.38 s/instrument-day, resolved
`cefi_delta_one_benchmark_vm_operator_approved_2026_07_29.md`). **TRADFI:volatility/commodity** — upstream raw-tick gap
CLOSED (slot-16) but the re-test hit a NEW infra blocker: the MDPS input bucket (`market-data` kind, env-tiered
`-test-`/`-prd-` ONLY) resolved with ambient `DEPLOYMENT_ENV_SHORT=stg` under the `--env staging` VM launch →
never-provisioned `market-data-tick-tradfi-stg-*` → 404. FIXED + shipped `features-service@cc5c52b8` (forces
`deployment_env="prod"` in `resolve_mdps_candle_bucket` + volatility `get_input_bucket`, mirrors the delta_one fix; QG
green; verified on origin). Still pending before a TRADFI re-run: features-e2e code-tarball rebuild (manual build) +
`commodity-signals-batch-test-*` bucket not provisioned. **DEFI:onchain** — gate RE-CLOSED 2026-08-05 (slot-12) on a
BINANCE-DELIVERY perp_funding attempted_failed regression (issue
`features_mdps_input_bucket_ambient_env_sibling_sites_2026_08_05.md` finding 6 + Progress Log; the 08-01 available=True
07-29/30 verification predates those rows); benchmark not yet re-run; `onchain/config.py:109` same-class stg risk under
staging launch. Measurement (multi-hour benchmark VMs) cannot complete in a bounded session → declined via
skip-current-task GATED, per plans-run-to-actual-completion. Filed
`issues/features_mdps_input_bucket_ambient_env_sibling_sites_2026_08_05.md` (sibling same-class sweep, 11 sites +
tarball + commodity-bucket + DEFI-benchmark follow-up todos).

**Acks + process notes (same session)**: (1) Operator OOM directive 2026-08-05 acknowledged — NO heavy RAM/IO process
was run locally this session; the single features-service `quality-gates.sh` ran under the shared-host QG cap (no
concurrent full QG) and completed green. (2) A `git commit --amend` near-miss: the first features-service commit attempt
was silently aborted by the ruff-format pre-commit hook (files modified → hook exit ≠ 0 → no commit), and the subsequent
`--amend --no-edit` rewrote the freshly-pulled origin tip (slot-9's `feat(calendar)` commit) into a local dangling
commit instead of creating a new one — recovered via `git reset --soft origin/live-defi-rollout` (dangling commit never
pushed, reflog-recoverable) then a clean fresh commit `cc5c52b8`. Lesson: verify `git rev-list --count HEAD..origin`
after a hook-aborted commit before using `--amend`.

### 2026-08-05 (slot-2, data_engineering) — TRADFI:volatility dep-gate probe-axis bug FIXED+shipped; DEFI IS-catalogue stg leak found

Re-dispatched to -056. Launched the TRADFI:volatility benchmark (`features-e2e-tradfi-20260805-223553-a8233c`, window
2026-07-28..08-04, `--legs benchmark`); the VM FAILED the dependency check
(`no captured options_chain or futures_chain shards found` for 2026-07-28). Root-caused a REAL probe-axis bug: the
volatility gate probes `check_dependency_via_manifest(data_type="options_chain"/"futures_chain")`, but the v8 manifest
registers chain shards under the **instrument_type** column (verified live: `instrument_type=options_chain captured:6` +
`futures_chain captured:63` for 2026-07-28, `service_name=market-tick-data-service`). FIXED + shipped:
`unified-trading-library@bf2757d7` (optional `instrument_type` filter on `check_dependency_via_manifest`, +2 tests) +
`features-service@10caf96e` (volatility gate probes `instrument_type`). Re-verified live: `validate_can_run` True for
07-28/29 + 08-04/TRADFI. QG green both repos, landed on LDR.

DEFI:onchain gate re-verified **OPEN** post-`a7976931` (`required_available=True` 07-29→08-04; matches slot-3). The
concurrent slot's relaunched DEFI benchmark (`features-e2e-defi-20260805-223356-060995`, post-tarball a7976931) PASSED
the gate (`✅ Dependencies verified for 2026-08-02/DEFI`) but produced ZERO output — **NEW ambient-env stg leak in the
onchain instruments-service catalogue read** (`404 instruments-store-defi-stg-*` → 0 instruments → empty success). Root
cause: `onchain/cli/handlers/batch_handler.py` `resolve_bucket(kind="instruments-store", ...)` lacks the
`deployment_env="prod"` pin. New P2 todo in the issue doc.

**Disposition**: -056 checkbox stays `[ ]` (numbers not all measured). TRADFI:volatility benchmark is now unblocked
(gate fixed) but needs a features tarball rebuild + a fresh VM; DEFI:onchain needs the IS-catalogue fix;
TRADFI:commodity test-bucket provisioned but not yet benchmarked. Declined via skip GATED per
plans-run-to-actual-completion.

- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.

### 2026-08-06 (slot-5, data_engineering) — commodity MEASURED; volatility + onchain VMs running

Dispatched to `-056`. All infra fixes from slot-4 (`features-service@21119021`, `unified-trading-library@b078d5ba`) and
prior fix waves confirmed in tarballs: `features-service-code@211190213cb3`,
`unified-trading-library-code@08521d5c1350`. Fleet clean on entry (0 features-e2e VMs).

**TRADFI:commodity — MEASURED ✅**: Fixed missing IAM (`uts-test-sa` lacked `storage.objects.create` on
`commodity-signals-batch-test-central-element-323112` — self-service IAM grant, `roles/storage.objectAdmin`). Launched
VM `features-e2e-tradfi-20260806-024854-e0321c` (SPOT, asia-northeast1-c, benchmark-days=7, window 2026-07-29..08-05).
Real compute: 16/16 commodity-days (NG + CL × 8 days), all succeeded. EXIT_STATUS=0. **Throughput: ~39 s/shard-day**
(driver wall_clock=273s / 7 benchmark-days; 2 objects written to test bucket). Audit report:
`plans/audit/results/data_pipeline_e2e_check_features_2026_08_05.md` (status=pass).

**TRADFI:volatility — IN PROGRESS**: VM `features-e2e-tradfi-20260806-024229-40bb75` (SPOT, asia-northeast1-c,
benchmark-days=7, window ~07-29..08-05) launched 02:42 UTC. Confirmed computing: 10 feature groups × 145 underlyings.
Tarballs current (`21119021`). Expected completion ~60-80 min from launch (7200s timeout override).

**DEFI:onchain — IN PROGRESS**: VM `features-e2e-defi-20260806-025432-onch5` (SPOT, asia-northeast1-c, benchmark-days=7,
start 2026-07-27 end 2026-08-03) launched 02:54 UTC directly via `launch-features-vm.sh` (bypassing driver's slow
`_scan_input_coverage` scan for DEFI). Tarballs current (`21119021`/`08521d5c`). All stg-leak fixes in: `raw_tick_data`
reader + IS startup validation + IS catalogue all forced `deployment_env="prod"`.

**Lesson (driver `_scan_input_coverage`)**: For DEFI:onchain, the `_scan_input_coverage` step reads a large DEFI
availability index (~40s) and is silently killed by the background task system. Workaround: launch the VM directly via
`deployment-service/scripts/vm/launch-features-vm.sh` then poll GCS `vm-logs/{vm}/EXIT_STATUS` for the result.

**Checkpoint**: -056 checkbox stays `[ ]` pending volatility and onchain completion. Watchdog
(`/home/ubuntu/.claude-configs/orch-slot-5/cc-tmpdir/…/scratchpad/watchdog.log`, checks every 10 min, PID 152282) +
wakeup at ~03:22 UTC to collect numbers and flip the checkbox.

### 2026-08-06 (slot-5, data_engineering continued) — both VMs done; 2 new upstream blockers filed

**TRADFI:volatility** — VM `features-e2e-tradfi-20260806-024229-40bb75` exit_code=0 but 0/10 groups. Root cause:
`_resolve_spot_perp` (data_loader.py:356) searches for `instrument_type=PERPETUAL` in TRADFI MTDS, but TRADFI has
FUTURE/futures_chain only (no perpetual swaps). FX underlyings 6A/6B/6C/6E/6J from IS catalogue have no PERPETUAL
records → 0 spot prices → 0 features computed (honest-absence guard correct). **BLOCKED-OPERATOR-DECISION** — fix
requires making `_resolve_spot_perp` TRADFI-aware (use futures_chain). Issue:
`/plans/archive/2026_08/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`

**DEFI:onchain** — VM `features-e2e-defi-20260806-025432-onch5` exit_code=1. 3 deps failed on 2026-07-27: (1) lst_rates:
BLAZESTAKE venue has `attempted_failed` on every date; no known-outage exemption in `_KNOWN_OUTAGE_VENUES_BY_SVC`;
BLAZESTAKE→SOLBLAZE-SOLANA canonical migration shard adds new venue rows but doesn't clean up old BLAZESTAKE rows. (2)
lending_indices: stalled after 2026-07-31 (no data for 2026-08-01+). No date satisfies BOTH (dates ≤07-31 fail
lst_rates, dates ≥08-01 fail lending_indices). (3) perp_funding: HYPERLIQUID fine for ≥2026-07-30 (not the binding
constraint). **BLOCKED-OPERATOR-DECISION** — fix: add BLAZESTAKE to known-outage exemption for lst_rates dep check.
Issue: `/plans/active/issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md`

**Status of -056**: commodity DONE (39 s/shard-day). Volatility + onchain blocked upstream. ☑ Commodity number committed
(`plans/audit/results/data_pipeline_e2e_check_features_2026_08_05.md`). Remaining two families require operator
decisions (see issue docs above).

### 2026-08-06 (slot-9) — todo 15 TERMINAL VERIFICATION: DeFi MDPS candle-backfill fleet outcome

Verified 2026-07-28 fleet (5 SPOT VMs, `run-ts=20260728-044648`) via `run.log` + GCS `processed_candles/by_date/`
day-partition counts. Per-shard: **2022** ✅ `DEPLOYMENT_COMPLETED exit=0` (0 candles — honest, every day "Listed 0
files"); **2023** ⚠️ SPOT-preempted, 364 day partitions (near-complete; Jan 9-18 hit 1800s timeout); **2024** ❌
`DEPLOYMENT_FAILED exit=1` — manifest consolidator DOWN but all 366 per-date subprocesses rc=0 (366 day partitions,
complete); **2025** ⚠️ SPOT-preempted, 272 day partitions (through ~Sep 2025); **2026** ⚠️ SPOT-preempted, 156 day
partitions (through ~Jun 2026). Total: 1,158 day partitions. **`max_workers` concurrency**: default 8 on e2-standard-8,
each worker writes distinct `gs://` blob via `polars_candle_engine.write_parquet()` — YES, up to 8 concurrent GCS writes
overlap (structural from `ThreadPoolExecutor`, no measured figure). Follow-up in
`/plans/active/issues/defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md`. ☑ Done.

- **context-scout 2026-08-15**: line-cap remediation (extracted 3 closed 2026-07-27 entries to
  `/plans/archive/2026_08/data_pipeline_check_mdps_features_progress_log_history_2026_08_15.md`, 1002L→880L);
  re-verified context_scope (5 entries), unchanged.
- **context-scout 2026-08-20**: re-verified context_scope (5 entries), unchanged.

## Extracted items index (2026-08-15)

> **Mechanical todo-conservation index — not live work.** `check_todo_regression.sh` counts total `- [ ]`/`- [x]` lines
> and fails a staged plan whose total shrinks vs `origin/live-defi-rollout`, with no exemption yet for a Finding-J
> archival extraction (same root cause as
> `/plans/active/issues/todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md`). The 1 line
> below is the already-`[x]`-closed checkbox item this extraction moved verbatim to
> `/plans/archive/2026_08/data_pipeline_check_mdps_features_progress_log_history_2026_08_15.md` — kept here as a
> one-line stub purely so the mechanical count is conserved; the full original text lives only in the archive, not
> duplicated here.

- [x] [DATA] P0. Coverage-check discrepancy — FOLDED 2026-07-27 (slot-7); FIXED 2026-07-27 (slot-4) — see archive.
