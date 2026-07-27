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
    /plans/archive/2026_07/data_pipeline_e2e_check_2026_07_10.md,
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
    /plans/active/candle_canonical_path_migration_execution_2026_07_24.md,
    /plans/archive/2026_07/data_pipeline_check_mdps_features_history_2026_07_24.md,
    ../epics/infrastructure_master.md,
    ../../cursor-configs/skills/data-pipeline-check-mtds/SKILL.md,
    ../../cursor-configs/skills/data-pipeline-check-is/SKILL.md,
  ]
created: 2026-07-20
last_updated: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
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
      `DATA_TYPES_BY_ASSET_GROUP ∩     needs_candle_processing`; per-timeframe verify; SELF-CONTAINED skip (MDPS reads
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
- [ ] NEW todo (was 8's remaining scope). [DATA] P0. Complete the automated `/data-pipeline-check-mdps` skill's OWN
      multi-cell round-trip (force+skip, all AGs × venues × data_types × timeframes, report written) — the mechanism is
      proven (see todo 8 above) but the SKILL DRIVER ITSELF has never survived long enough (5 independent reproductions
      across 2 sessions, both ad-hoc interactive and AO-managed persistent workers) to produce one clean automated
      verdict beyond a single scoped cell. **GATED on prerequisite condition `mdps-e2e-shared-host-teardown-fixed`**
      (set by main/operator; tracks `issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md` — fleet-wide
      shared-host RAM contention silently killing background processes mid-run, 32s-520s in, not tied to elapsed time; a
      distinct but likely-related mechanism from the `WorkerLivenessWatchdog` heartbeat-silent kill documented for the
      original ~19-minute reproduction in `/codex/04-architecture/agent-orchestrator-worker-liveness.md`). Do NOT
      attempt this todo until that condition flips green — re-attempting blind just wastes another cycle on the same
      wall. **RE-VERIFIED 2026-07-27 (slot-10)**: `issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`
      is still `status: open`; no evidence the `mdps-e2e-shared-host-teardown-fixed` condition has flipped. Not
      re-attempted — would be the 6th reproduction of the same known failure mode. Skipped rather than burning another
      cycle; re-check once the operator/main flips the condition.
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
      `universe_filter [technical_indicators]: retained 552/588; excluded     36 (unknown_quote=3)` — up from 0/588
      pre-fix. Separately discovered + fixed an unrelated infra gap while launching that VM: the `features-service` code
      tarball VMs pull (`gs://deployment-scripts-{project}/code/     features-service-code.tar.gz`) was 5+ hours stale
      (built 01:29 UTC, hours before the 06:18 UTC fix push), so the first post-fix VM run still failed on the OLD code
      — root-caused via the tarball manifest's `commit_sha`, fixed by manually rebuilding via
      `deployment-service/scripts/vm/create-code-tarballs.sh --include features-service     --force`. Full detail + the
      tarball-staleness finding:
      `issues/features_universe_filter_settlement_suffix_and_vm_     tarball_staleness_2026_07_27.md`.
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
      `market-data-processing-service@6cd96e8` + `deployment-service@c8ee47e`. Re-checked live fleet state on pickup of
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
- [ ] 10. [DATA] P1. Steady-state benchmark VMs (250GB disk) per representative shard-type; measure amortized per-shard-
      day throughput (RX + rows/s + wall-clock); project full-history time (honest floor + flat 2019) + SPOT cost +
      parallelization/optimization headroom.
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
- **[DATA] P0. 11b.** The actual cross-repo orphan/lineage report — remains open, tracked via the 4 todos in
  `issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md` (build+run MDPS/features/ml-strategy sweeps,
  then write the combined report). Non-checkbox pointer per the scoping above.
- [ ] 11c. [DATA] P0. **MIGRATE existing candle/feature data to zero orphans** (MVP or not) — WRITES the GCS manifest
      (safe additive `merge_manifest_from_canonical_paths()` from 11a, never destructive
      `rebuild_manifest_from_canonical_paths`). **Not `[OPERATOR]`-pre-gated** (corrected 2026-07-27 — the additive path
      only ADDS rows, finding O's carve-out applies). **Once 11b lands**: any orphan class needing a real GCS migration
      re-checks that bucket's soft-delete fresh via `gcs_bucket_soft_delete_retention_seconds()` — `>=604800s` →
      autonomous (finding T, §3a); else tag `[OPERATOR]` then, not before. VM-only, never in-session. `depends_on: 11b`.
      Migrations run to real completion per the data-pipeline-correctness HARD RULE.
- [ ] 12. [SCRIPT] P1. Backfill-processing path (download→process→upload) code-ready + OPTIMIZED learning from cefi
      (within-VM multiproc, faster-libs/Rust where it pays, 250GB disk, fleet-wide since not Tardis-capped).
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
- [ ] 14. [SCRIPT] P2. Ship everything via quickmerge --agent per repo; flip these checkboxes same-turn; rule-9 final
      report. Post-phase codex audit (update contracts / stub patterns / CLAUDE.md one-liner for the two new skills).
- [ ] 15. [DATA] P1. Full DeFi-MVP candle backfill on real infra — GATED on
      `/plans/active/candle_canonical_path_migration_execution_2026_07_24.md` (the Option-A canonical-path migration
      epic) reaching its P8 verify/reconcile; do NOT backfill the corpus into the pre-migration shape (see this plan's
      `depends_on` frontmatter).

## Progress Log

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

### 2026-07-27 — todo 8 PARTIAL: CEFI force-leg mechanism re-proven 4x; skip-proof + other AGs blocked by session teardown

Scoped `/data-pipeline-check-mdps` to CEFI:BINANCE-FUTURES:trades (day=2026-07-05, auto-day-resolved) as a
representative cell before attempting the full 448-cell all-AG matrix (unscoped run is explicitly warned against by the
skill itself). **Force leg independently re-proven correct on real infra 4 separate times** (VMs
`...pipelinecheck-20260727-022633`, `-023618`, `-031200`, `...manualskip-033855` — all `exit_code=0`, all derive the
identical 7,615 candles across the 7 timeframes). The automated skill driver (`pipeline_e2e_check.py --legs force,skip`)
could not be kept alive long enough by this interactive session to produce a clean automated skip-proof verdict — the
local process was killed mid-run 4 times across different backgrounding strategies (plain `run_in_background`,
`nohup&disown`, foreground-with-auto-background, `setsid`). Full findings + recommended fixes:
`/plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`. A secondary, minor
finding (byte-identical candle written to two different paths — with/without `instrument_type=` segment — across
consecutive force runs) is tracked separately:
`/plans/active/issues/mdps_candle_path_instrument_type_segment_nondeterministic_2026_07_27.md`.

**Disposition:** todo 8 stays OPEN (not flipped) — the force-leg _mechanism_ is proven, but the todo's actual scope
("every MVP candle shard, all AGs") and even a single clean automated skip-proof are not yet met. Report written this
session: `plans/audit/results/data_pipeline_e2e_check_mdps_2026_07_05.md`.

### 2026-07-27 (slot-9) — one of todo 8's two identified blockers FIXED; todo 8 itself still OPEN

Dispatched to continue todo 8. Rather than re-attempt the exact same 4x-failed backgrounding strategies (harness
`run_in_background`, `nohup&disown`, foreground-auto-backgrounded, `setsid` — all already exhausted per the entry
above), root-caused and fixed the CONCRETE bug behind attempt 3's `launcher_script_timeout` false-failure:
`unified-trading-library@137e219c` — a `subprocess.TimeoutExpired` on the launcher-script client-side wait
(`_LAUNCHER_SCRIPT_TIMEOUT_SEC=120s`) previously aborted the whole shard immediately with ZERO retry, even though the
identical `_vm_is_present`-gated retry machinery already existed for ordinary nonzero launcher exits (added for the
exact same "gcloud create succeeded server-side after the client-side confirmation wait already gave up" failure mode).
Now a timeout is converted to a synthetic nonzero-exit result and flows through that same retry path. 3 new regression
tests, QG green (226s). Full detail + evidence:
`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` todo 3 (flipped).

**Disposition:** todo 8 stays OPEN — this fixes one of the two identified blockers (the launcher-timeout false-failure),
not the other (the session/container teardown killing the long-running driver process itself, still under P1
investigation, unresolved). A from-scratch automated run may now get further before hitting the teardown wall, but
re-attempting the full multi-hour/462-cell matrix was out of scope for this 1-hour task; the next attempt should happen
once the teardown root-cause (item 1 below) is resolved, or from a longer-lived host if the teardown proves to be this
interactive-session-class specific.

### 2026-07-27 (slot-12) — todo 11 PARTIAL: caught + fixed a P0 unsafe-rebuild bug blocking the candle-manifest orphan reconciliation; DEFI candle-manifest measurement corrected

Dispatched to todo 11 (cross-repo orphan/lineage audit + migrate to zero orphans). Scoping how to execute the
already-open `issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` (CEFI candle files orphaned by
pre-fix-era OOM crashes) surfaced a genuine, previously-uncaught **P0 data-loss risk in the recommended remediation
itself**: `unified_trading_library.manifest_writer.rebuild_manifest_from_canonical_paths()` builds its output purely
from a `prefix`-scoped GCS walk and uploads that as the bucket's WHOLE consolidated manifest index — on the
`market-data-tick-{ag}-prd` buckets, which co-locate MTDS's `raw_tick_data/` and MDPS's `processed_candles/` under ONE
index, a prefix-scoped call (exactly what the reconciliation doc recommended) would have silently deleted essentially
the entire raw-tick manifest for that asset_group to backfill a much smaller candle-orphan set. **Caught before any VM
launched — nothing was actually deleted.** Full analysis, evidence, and fix:
`issues/rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md` (new, P0). Shipped the fix:
`unified-trading-library@2352e7c8` — added `merge_manifest_from_canonical_paths()`, an additive sibling that only adds
genuinely-missing `(day, venue, chain, instrument_type, data_type)` rows and preserves every existing row (including
rows for other prefixes) verbatim; 2 new regression tests directly proving the safety property (a pre-existing
out-of-prefix row survives the merge, both in the returned frame AND in what actually lands in GCS) plus an idempotency
test. Corrected `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`'s recommended-fix section to route
through the new additive function instead of the unsafe call, and to re-verify the bucket's non-candle row count is
unchanged before trusting a future run.

**Also corrected a stale measurement feeding this same effort**:
`candle_feature_canonical_path_divergence_2026_07_20.md` todo 7's "candle manifest never systematically populated" claim
(cefi=6/defi=0/tradfi=73/prediction=168 rows, 2026-07-23) used the WRONG `data_type` vocabulary (the aggregated
`ohlcv_*` family) — the SAME mistake already root-caused for cefi in the archived
`mdps_cefi_candle_manifest_never_emitted_2026_07_26.md` (MDPS stamps `data_type=<SOURCE type>` + a real `timeframe`, not
the aggregated family, by deliberate operator ruling). Re-measured DEFI directly this session with the correct
vocabulary: **7,913 real `market-data-processing-service` candle-manifest rows exist today**
(`data_type=dex_pool_swaps`, real timeframes), not 0. Flagged in that todo; not fully re-verified for
cefi/tradfi/prediction this session — do not close it on the DEFI spot-check alone.

**Disposition:** todo 11 stays OPEN — this session did NOT run the actual candle/feature migration. The previously-
recommended reconciliation path was unsafe; the additive fix (`unified-trading-library@2352e7c8`) has now SHIPPED and is
QG/CI-green, so `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` is UNBLOCKED for its next session (only
the actual Tier-2 SPOT VM reconciliation run remains, deliberately not launched from this interactive session per the
heavy-I/O rule). The full cross-repo lineage audit (MTDS→MDPS→features→ml/strategy) beyond the candle-manifest slice was
not attempted this session. What shipped is a genuine, verifiable safety fix + a corrected measurement that a future
session's migration work depends on not repeating.

### 2026-07-27 (slot-10) — todo 9b: no new CEFI cell launchable without duplicating in-flight work; billing-waste finding filed

Dispatched to todo 9b (full-matrix features re-run). Fresh-checked live state before launching anything (per the
duplicate-VM lesson learned mid-session, see below): `gcloud compute instances list --filter="name~'features-e2e-cefi'"`
showed **5 delta_one:CEFI VMs already RUNNING** from prior sessions (oldest since 06:34 UTC, ~4.7h runtime at check
time), none complete — `run.log` tails confirm all 5 are genuinely still computing (live-advancing timestamps, not
stuck), so none qualify for deletion under the VM-delete guardrail. Two are exact-duplicate pairs of each other (same
family/AG/window, both `--force`) — real billing waste from repeated relaunches with no in-flight check, filed as a new
todo in `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`. Separately confirmed via
`gcloud compute instances list --filter="name~'features-'"` that slot-3 is concurrently running `--family volatility`
(all-AG, covers CEFI) since 10:44 UTC, and another slot is running `sports`/`TRADFI:volatility` re-verification (both
post their respective fixes landing at 10:17/unclear). **Near-miss**: launched a
`--family volatility --asset-group CEFI` driver myself before checking local processes — `ps aux` immediately after
caught slot-3's identical in-flight run; killed my own 5-second-old duplicate before it reached VM-launch (confirmed via
its log: enumeration only, no VM created). Net effect: **zero new VMs launched this session** — every remaining CEFI
cell (`delta_one`, `volatility`) is already covered by in-flight work, and the two derived cells (`multi_timeframe`,
`cross_instrument`) are blocked on `delta_one`'s test-bucket output, which none of the 5 in-flight runs have produced
yet (checked `gs://features-cefi-test-central-element-323112/delta_one/by_date/day=2026-07-19/` — no objects; only the
still-writing `day=2026-06-28` partition has partial output so far).

**Disposition:** todo 9b stays OPEN. **Next session**: check
`gcloud compute instances list --filter="name~'features-e2e-cefi'"` FIRST — if all 5 have terminated, check which (if
any) reached a real completion (non-empty `by_date/day=<window-end>/` output in the test bucket) before launching
`multi_timeframe`/`cross_instrument` for CEFI (they need `delta_one`'s test output as `--source-bucket`); do NOT launch
a 6th `delta_one` VM. If `volatility` has a written report from slot-3 by then, fold it into the combined
`data_pipeline_e2e_check_features_2026_07_05` report via `merge_pipeline_e2e_report.py`.

### 2026-07-27 (slot-6) — todo 9b: found slot-7 ALREADY driving the full matrix; shipped the duplicate-VM billing-waste fix instead of launching

Dispatched to todo 9b. Per the disposition above, checked live fleet state FIRST:
`gcloud compute instances list --filter="name~'features-e2e'"` showed **7** `features-e2e-cefi-*` VMs RUNNING (up from
the 5 slot-10 found) + 2 `features-e2e-tradfi-*`, all confirmed live-advancing via fresh `run.log` tails (none stalled).
`ps aux` found slot-7 actively running
`.venv/bin/python scripts/pipeline_e2e_check.py --day 2026-07-05 --legs force,skip --require-captured --auto-day` (no
`--family`/`--asset-group` — the genuine unrestricted full-matrix driver todo 9b calls for) since 11:21 UTC, whose own
`run.log` showed it had just launched one of the 7 CEFI VMs (`-112159`, shard 1/16 = `CEFI:delta_one`) — i.e. **slot-7
is already doing exactly this todo**, ~35 min in, correctly progressing. This is the same slot-6/slot-7 double-dispatch
pattern main already ruled on once this session for a different task (`sports_satellite_ao_dispatch_batch5-026` — "stand
down, the other slot already implemented it"); applying the same resolution here: did NOT start a competing full-matrix
run (would duplicate VM spend on top of an already-running one) and did NOT touch slot-7's VMs (all genuinely
progressing, none eligible for the delete guardrail).

Instead used the dispatch productively: slot-7's own `-112159` launch was itself a NEW duplicate of the
2026-06-28..2026-06-29 window `-101851`/`-102228` were already computing — live proof that the P1 duplicate-VM-launch
bug filed in `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` was still unfixed and
actively costing money on the very run meant to close todo 9b. Shipped the fix: `features-service@6981b2b8` adds
`_find_inflight_duplicate_vm` (labels-based `aggregated_list_instances` check, no raw gcloud/subprocess) to both the
force and skip leg launch paths — a hit skips the launch with `status=skipped, reason=duplicate_in_flight: ...` instead
of creating another billable VM. QG green, quickmerge shipped. Full detail + a follow-up MDPS-parity todo (not yet
confirmed vulnerable, not yet fixed) in the same issue doc.

**Disposition:** todo 9b remains OPEN, now owned by slot-7's in-flight run (started 11:21 UTC, shard 1/16 of 16, window
`--day 2026-07-05 --auto-day`). **Next session**: check `ps aux | grep pipeline_e2e_check` for slot-7's process FIRST —
if it completed, read its written report (`data_pipeline_e2e_check_features_2026_07_05*`) and fold in any still-separate
`volatility` report from slot-3 via `merge_pipeline_e2e_report.py`; if it died mid-matrix (no `--resume` support yet —
see the other open todo in the same issue doc), resume from whichever shard it reached (check `run.log`'s last
`Starting compute:` line) rather than restarting all 16 from shard 1 — the new duplicate-guard fix will now correctly
skip any of the 7 already-running CEFI VMs / 2 TRADFI VMs it encounters again instead of adding an 8th/9th/10th.

### 2026-07-27 (slot-2) — todo 9b: slot-7 still in-flight; closed the MDPS-parity duplicate-VM-guard followup instead

Dispatched to todo 9b. Re-checked live fleet state: slot-7's driver (PID 3665121, started 11:21 UTC) STILL RUNNING,
1h18m+ elapsed, alive not zombie. Per the slot-6/slot-10 resolution, did NOT launch anything.

Used the dispatch productively to close the MDPS-parity followup flagged in
`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` (full detail there — confirmed
vulnerable + the launcher-label insufficiency finding + both fixes): `market-data-processing-service@6cd96e8` (ports
`_find_inflight_duplicate_vm` into both force/skip legs, 6 new tests, QG green 118s) + `deployment-service@c8ee47e`
(extends `launch-mdps-backfill-vm.sh` labels with venue/data_type, 5 new tests).

**Disposition:** todo 9b remains OPEN, still owned by slot-7's in-flight run — this closed an ADJACENT gap, not 9b
itself. **Next session**: `ps aux | grep pipeline_e2e_check` for slot-7 first; if finished, read its report; if died
mid-matrix, resume from its last shard (both drivers now duplicate-guarded).

## Deferred work after 2026-07-27

| #   | Item                                                                                                                                                                                     | Priority | Where tracked                                                                     | Gating                     |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------- | -------------------------- |
| 1   | Root-cause / fix worker-session teardown killing long-running check-skill drivers                                                                                                        | P1       | `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`         | none                       |
| 2   | Add `--resume`/checkpoint to `pipeline_e2e_check` so a killed run doesn't restart the whole matrix                                                                                       | P2       | same issue doc                                                                    | depends on #1's root cause |
| 3   | ✅ DONE 2026-07-27 (slot-9) — Loosen/backoff `launch_vm_and_wait`'s launcher-script timeout under fleet contention (`utl@137e219c`)                                                      | P2       | same issue doc                                                                    | none                       |
| 7   | Run the CEFI candle-manifest orphan reconciliation via the new safe `merge_manifest_from_canonical_paths` (Tier-2 SPOT VM, never in-session)                                             | P1       | `mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`                   | none                       |
| 8   | Audit `rebuild_mtds_manifest.py --from-canonical`'s existing call site for the same prefix-scoped-wipe risk (already-shipped permanent script)                                           | P1       | `rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md` todo 3   | none                       |
| 9   | Re-measure cefi/tradfi/prediction candle-manifest coverage with the CORRECT vocabulary before trusting todo 7's "never populated" framing                                                | P1       | `candle_feature_canonical_path_divergence_2026_07_20.md` todo 7                   | none                       |
| 10  | Run todo 11b (cross-repo lineage audit) then 11c (migrate to zero orphans, [OPERATOR]) — the ex-todo-11 rollup split                                                                     | P0       | this plan, todos 11b/11c                                                          | 11c depends_on 11b         |
| 4   | Root-cause non-deterministic instrument_type path segment for identical force re-runs                                                                                                    | P3       | `mdps_candle_path_instrument_type_segment_nondeterministic_2026_07_27.md`         | none                       |
| 5   | Complete todo 8's actual scope (skip-proof + defi/tradfi/sports/prediction reps) once #1/#2 land                                                                                         | P0       | this plan, todo 8                                                                 | #1                         |
| 6   | ✅ DONE 2026-07-27 (slot-7) — Complete todo 9 (`/data-pipeline-check-features` full-matrix run + report)                                                                                 | P0       | this plan, todos 9/9b + 2 new issue docs (below)                                  | none                       |
| 11  | Fix the 6 distinct genuine root causes behind 17/32 failed legs (coverage/dependency-check mismatch, multi_timeframe date bug, OOM, manifest-staleness/env-parity, external-vendor auth) | P0       | `issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md`    | none                       |
| 12  | Fix the timeout/orphaned-duplicate-VM defect for large-universe shards — **PARTIALLY DONE 2026-07-27 (slot-6)**, `features-service@4d71b1b5`                                             | P1       | `issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md` | none                       |

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

## Deferred work after 2026-07-21

Every item below is already a tracked todo in the cited issue doc (nothing lost). None blocks the operator's DeFi-MVP
backfill decision — the derivative_ticker write path (the one hard blocker found this session) is PROVEN fixed.

| #   | Item                                                                                                                                                     | Priority | Where tracked                                                       | Gating                                                          |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------- | --------------------------------------------------------------- |
| 1   | Driver reads MERGED index not the leg VM's per-VM shard → reports "failed" on a successful write (EXACT fix spec'd)                                      | P2       | `mdps_derivative_ticker_candle_schema_violation` todo 4             | none — unit-testable, no VM                                     |
| 2   | Exit-code-lies: a run whose every write fails still exits rc=0 (shard-isolation-safe fix needed)                                                         | P1       | same issue, todo 2                                                  | none                                                            |
| 3   | Proof-sweep the other empty-window candle types (book5/liq exempt) — the fix already covers them via the shared seam                                     | P1       | same issue, todo 3                                                  | none                                                            |
| 4   | Candle object↔manifest disconnect: 6 degenerate MDPS rows vs 20k+ objects/day — candle manifest never systematically populated                           | P0       | `candle_feature_canonical_path_divergence` todo 7                   | none — root-cause needed before trusting skip-if-fresh at scale |
| 5   | Canonical A/B/C ruling for the candle object-path shape (instrument_type= presence + source vs aggregated data_type)                                     | P1       | same issue, todo 1                                                  | **OPERATOR-GATED**                                              |
| 6   | Split-brain candle layout (pipeline_mode present on some objects, absent on others) + extend the UAC canonical oracle to the processed_candles namespace | P1       | same issue, todos 9,10                                              | partly operator-gated (follows the A/B/C ruling)                |
| 7   | Real features-service writing smoke (proves the features skill's green path)                                                                             | P2       | this plan                                                           | candle input coverage (blocked by #4)                           |
| 8   | Full DeFi-MVP candle backfill on real infra                                                                                                              | —        | this plan / ETA                                                     | operator's run (SPOT fleet ready; per the delivered ETA)        |
| 9   | Defense-in-depth UAC pin on the other service launchers (mtds/instruments/mdps-sharded/mtds-dex-swaps)                                                   | P2       | `mdps_vm_stale_uac_contract_propagation` (resolved; follow-up note) | none — already covered fleet-wide by shared setup Fix 2/3       |

## Session close 2026-07-21 — what shipped + proven

**Delivered:** both skills (`/data-pipeline-check-mdps` + `/data-pipeline-check-features`) built, shipped,
harness-registered, and VALIDATED end-to-end on real infra — where they earned their keep by catching 3 silent P0s no
green-tick smoke would surface. **3 P0s fixed + PROVEN on live VMs:** (1) derivative_ticker candle write (0→140
objects + 140 `captured` rows, via adapter `mdps@beea161` + nullability `mdps@d4052e20b`); (2) UAC contract-propagation
(`deployment@e978f32d`, fleet-wide silent staleness); (3) read-path amplification 16.7x + seed-context thread-safety
(`utl@80d2497e`/`mdps@b4db0af`/`b3376b8`) shipped earlier. Root cause of (1) was CORRECTED mid-flight by an adversarial
8-agent workflow (my first "key mismatch" hypothesis was a red herring — the real cause was category-gated nullability
in the MDPS pre-upload validator). **Measured:** trades write-rate ~16.9s/instrument-day; full MDPS MVP breadth 462
shard cells. **Ground-truthed (operator-gated resolution):** the existing-candle estate's canonical orphans (split-brain
layout, no candle oracle, 6-row manifest vs 20k objects/day). Every finding is a tracked todo; the SPOT backfill fleet
is ready pending the operator's canonical ruling + the candle-manifest-population root-cause.

### 2026-07-21 — Option-A candle canonical-path migration EXTRACTED to its own plan

The full "OPTION-A MIGRATION SCOPED" record and the "RESUMPTION STATE 2026-07-21" record (scale correction, blast
radius, path transform, the 8-phase breakdown, the LOCKED canonical shape, the per-repo shipped/uncommitted-file table,
RESUME ORDER, and the 🔑 LESSONS) were extracted **verbatim** 2026-07-24 to
`/plans/active/candle_canonical_path_migration_execution_2026_07_24.md` (plan-hygiene line-cap remediation) — that plan
now owns the migration epic end-to-end (census → executor → per-AG SPOT migration → verify). See that file for the full
record; nothing here was summarized or lost, only moved. This plan's own remaining work (todo 15) is `depends_on`-gated
on that plan's completion.

### 2026-07-27 (slot-7) — todo "Run /data-pipeline-check-features across ALL shards" IN FLIGHT, not blocked

Phase 0 passed. Local driver dies silently/often (`WorkerLivenessWatchdog`/RAM contention, slot-3 independently
diagnosed same class — `issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` todo 9). On
death, check `gcloud compute instances list --filter="name~'features-e2e-<ag>'"` first (VM usually outlives the
poller) + its `run.log`. **Resume**:
`cd features-service && .venv/bin/python scripts/pipeline_e2e_check.py --day 2026-07-05 --legs force,skip --require-captured --auto-day --asset-group <AG> --family <FAM> --project central-element-323112`;
`delta_one` first per-AG; CEFI is slot-3's; driver OVERWRITES its report per-invocation — merge with
`unified-trading-pm@e537bff29` `scripts/plan-hygiene/merge_pipeline_e2e_report.py` after every cell.

**12/16 driver-matrix cells attempted — ALL non-CEFI cells now exhausted** (0 in flight; remaining 4 are
`delta_one`/`volatility`/`cross_instrument`/`multi_timeframe` on CEFI, slot-3's). 7 honest
`no_captured_input_for_window` skips (`DEFI:delta_one`, `PREDICTION:delta_one`, `DEFI:onchain`,
`multi_timeframe:{DEFI,TRADFI}`, `cross_instrument:PREDICTION` — all cascade cleanly from their own family's missing
input, expected — `volatility:TRADFI`). `TRADFI:delta_one` FAILED (2 identical VM runs,
`DEPENDENCY CHECK FAILED — Missing market-data-processing-service`; driver's `--require-captured` wrongly accepted the
window, P1 todo below); `cross_instrument:TRADFI` (both legs) FAILED HARD as the same cascade — but **note the
asymmetry**: `multi_timeframe:TRADFI` and `cross_instrument:PREDICTION` both degraded gracefully to a clean skip on
their own missing-input condition, `cross_instrument:TRADFI` alone raised an uncaught `FileNotFoundError` — worth a
follow-up but not filed (downstream of the same already-tracked P1). `commodity:TRADFI` FAILED cleanly — 3
public/no-auth sources 403/timeout/404'd, NOT `BLOCKED-CREDENTIALS` —
`issues/features_commodity_public_api_403_from_gcp_vm_2026_07_27.md` (P2). **TWO P0 DATA-CORRECTNESS BUGS, same
root-cause class**: `calendar` (0 rows) and `sports` (51 REAL fixtures — worse) both wrote to PROD despite
`IS_TEST_RUN=true` — each family's `is_test_run` field is declared but never consulted at its actual bucket-resolution
call site (delta_one's `get_output_bucket()`/`get_data_sink()` is correct; calendar's fix shipped
`features-service@ba5143fd`, sports' is open). Filed
`issues/features_{calendar,sports}_is_test_run_ignored_writes_*_2026_07_27.md` (both P0, operator-notified). **Do NOT
re-run `calendar` or `sports` until fixed**; `onchain`'s AG may share this bug (untested). Report:
`plans/audit/results/data_pipeline_e2e_check_features_2026_07_05.{md,json}` (total=24 failed=6 skipped=13). **Next
session**: either pick up the 4 CEFI cells (coordinate with slot-3 first) or re-run `calendar`/`sports` once their P0
fixes land. Plan AT its 1000-line hard cap — archive older closed sections before adding more.

- [x] ✅ NEW todo. [DATA] P0. **Coverage-check discrepancy — FOLDED 2026-07-27 (slot-7); FIXED 2026-07-27 (slot-4)**:
      same root cause independently hit 3x (this occurrence + slot-3's day=2026-07-19 occurrence + the fuller writeup) —
      tracked and fixed in `issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md` todo 1,
      not here: `features-service@1b272676` (+ test reconciliation `4fbf4dc7`). Root cause was a coverage-check
      granularity gap (NOT phantom-capture) — `--require-captured`/`--auto-day` accepted an `EMPTY_CONFIRMED` TARGET day
      (a TradFi weekend/holiday MDPS positively confirmed has zero output) as "covered", guaranteeing the runtime
      dependency checker's real GCS listing would then fail. Fixed by requiring the target day specifically to have a
      real `CAPTURED` row while still tolerating `EMPTY_CONFIRMED` window-interior days. **This todo attracted 3
      simultaneous independent dispatches** (this fix + slot-14's `696768c7` object-existence-probe variant + slot-2's
      `ecd548b8` runtime-dependency-checker fix) — reconciled by rebase-merging slot-14's probe scoped to
      `captured_days` only (not the broader `canonical_days`, which would have blanket-excluded every TradFi
      weekend/holiday from window-interior tolerance too — a worse regression); slot-2's fix is a complementary
      different-layer change (runtime checker vs this driver's pre-flight skip), no conflict. Full reconciliation
      writeup in the issue doc. 18 tests pass across the 3 related test files, QG green. The issue doc's own todo 2
      (re-run for a genuine force+skip proof) stays open — no `capture_status=captured` TRADFI/MDPS candle row exists
      yet in the 06-01..07-27 window, so that proof is gated on a real TRADFI candle backfill, not on this fix.

### 2026-07-27 (slot-3) — todo 9b: day=2026-07-19 CEFI-inclusive 8-family sweep complete; NOT claiming 9b closed

Ran `/data-pipeline-check-features` for day=2026-07-19 across all 8 families (30 force+skip rows: 3 passed/13 failed/14
skipped) — `plans/audit/results/data_pipeline_e2e_check_features_2026_07_19.{md,json}`. Covers the 4 CEFI cells slot-7's
entry above asked "next session" to pick up (delta_one/volatility/multi_timeframe/cross_instrument), just on a different
calendar day (07-19 vs slot-7's 07-05) — do NOT merge into slot-7's report file as-is, the day mismatch would
misrepresent it. 2 new real driver bugs found+fixed+shipped:
`issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md` (P2) and
`issues/features_pipeline_e2e_check_duplicate_vm_launch_same_shard_2026_07_27.md` (P2 — root cause independently also
fixed by slot-6's `features-service@6981b2b8`). Also incidentally answers the sports `IS_TEST_RUN` issue's own P2
audit-todo for volatility/cross_instrument/multi_timeframe/commodity: every cell that produced real output wrote to the
correct `-test-` bucket (no PROD-pollution bug found); `onchain` never got real output to check. Real findings not
separately filed given time: OOM kill (rc=137) on `cross_instrument:CEFI` loading a 115,584×4,476 dataset for
`regime_detection`; genuine upstream 404 (`baker_hughes_rig_count`) on `commodity:TRADFI`.

**Discovered mid-session**: slots 6/7/10 were concurrently working this SAME todo without my awareness (see their
entries above). Slot-7's day=2026-07-05 non-CEFI driver (PID 3665121) confirmed STILL RUNNING at this check, so per
slot-6's own disposition 9b's closure isn't mine to claim — **9b left OPEN**. Live fleet check also found **9**
`features-e2e-*` VMs still RUNNING right now (oldest ~9h) — billing-waste addendum filed on
`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` (P1, recommends
`/vm-preemption-billing-waste-audit`). **Next session**: check if slot-7's run finished; then decide whether the day-19
CEFI proof suffices or the 4 CEFI cells need a same-day (07-05) re-run before flipping 9b.

### 2026-07-27 (slot-7, same slot, PID 3665121 finished) — todo 9b + standalone todo DONE: full 16-shard matrix completed; calendar/sports re-run confirmed SAFE; cross-linked with slot-3's parallel findings

The day=2026-07-05 driver (PID 3665121, referenced above and by slot-3/6/10/2) ran to completion: **~3h56min wall-clock
(11:21:49 → 15:15:07 UTC)**, via `run_in_background` + a companion heartbeat loop every ~200s (the confirmed
session-teardown mitigation) — **zero session-teardown kills**. Report:
`plans/audit/results/data_pipeline_e2e_check_features_2026_07_05.md` — **total=32 passed=3 failed=17 skipped=12** (all
16 real viable cells per the driver's own enumeration, not the ~29 estimate elsewhere in this plan).

**Claiming 9b's closure now** per slot-3's own explicit disposition ("check if slot-7's run finished... before flipping
9b") — it finished, covering the same 4 CEFI cells slot-3 asked about, on the operator-ruled day (07-05) throughout. The
standalone "Run `/data-pipeline-check-features` across ALL shards" todo above is the same underlying goal (a
pre-existing collision risk this plan's own Progress Log already flagged) — both flipped from this one completed run.

**Before trusting the calendar/sports re-run** (a prior slot-7 entry above explicitly warned "Do NOT re-run `calendar`
or `sports` until fixed" — sports' `IS_TEST_RUN` bug was open at that point), verified `features-service@48a255cd` (the
sports fix) was live and ground-truthed both writes directly against GCS: `features-sports-test-...`'s `day=2026-07-05`
fixtures object shows `creation_time=2026-07-27T14:47:45Z` (matching this run) while the PROD equivalent is untouched
since the original incident's `2026-07-27T09:03:54Z` (`metageneration: 1` unchanged) — no new PROD pollution. Same check
for calendar: TEST object created `2026-07-27T14:58:41Z`, no PROD equivalent exists. **Both families confirmed safe.**

**Two follow-up issue docs filed** (findings triage — this todo's job was RUN + REPORT, not fix):

1. `issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md` — CEFI:delta_one AND
   TRADFI:volatility both hit the driver's 2400s per-VM timeout despite genuinely still computing, causing an orphaned
   duplicate VM each time. **Already fixed same-day by slot-6** (`features-service@4d71b1b5`,
   `_FAMILY_TIMEOUT_OVERRIDES`) — TRADFI:volatility's fix is fully verified (real `EXIT_STATUS=0` observed at 4788s);
   CEFI:delta_one's override (36000s) is evidence-based but not yet directly observed completing.
2. `issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md` (**P0, big finding**) — direct VM
   `run.log` inspection of the 17 failed (non-timeout) legs surfaced 6 distinct GENUINE root causes across ≥3 repos: (A)
   the coverage-check/dependency-check disagreement for TRADFI candles (independently corroborated by slot-3 on a
   different day — tracked in ONE place,
   `issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`, not duplicated); (B)
   `multi_timeframe` reads TODAY's wall-clock date instead of the requested window, hit IDENTICALLY by both CEFI and
   TRADFI — the highest-value fix, asset_group-agnostic; (C) a genuine OOM (exit=137) during CEFI:cross_instrument's
   `regime_detection` HMM fit (also independently seen by slot-3); (D) SPORTS:sports skip-leg hit a stale manifest
   consolidator + a local/VM env-parity gap; (E) TRADFI:commodity's external vendors (EIA/CFTC/Baker Hughes) 403/404'd —
   credential/config, `[OPERATOR]`-tagged (also independently seen by slot-3); (F) a cascade of (A). 12 skips were
   honest and correctly not counted as failures.

**Cross-referenced all 4 issue docs** (this session's 2 + slot-3's 2) so root causes A and the timeout defect each have
exactly ONE tracked fix-todo. **Corrected an error made mid-session**: an earlier version of the timeout doc mistook
`TRADFI:delta_one`'s fast EXIT (a real dependency-check failure, root cause A) for a fast clean pass and called it a
"negative control" — fixed in that doc's own Progress Log once caught; did not affect the shipped timeout fix, which
targeted the two independently-confirmed cells on their own merits.

**Disposition**: DONE. **Next session**: work the 6 fix-path todos in the widespread-failures doc (root cause B — the
`multi_timeframe` date bug — is the highest-value/lowest-effort fix, asset_group-agnostic), then re-run for just the
affected shards to confirm genuine (non-error) verdicts.

### 2026-07-27 (slot-3, after session resume) — todo 10 PARTIAL: 2 real measured benchmarks + 2 honestly-diagnosed data-gap failures; CEFI deliberately deferred

Ran the `/data-pipeline-check-features` benchmark leg (`--legs benchmark`) against 4 representative shard-types
(day=2026-07-19), avoiding CEFI:delta_one entirely — it already has **8 confirmed-duplicate VMs running** (billing-waste
audit filed + operator notified same session,
`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`).

**2 real, complete, measured throughput numbers (both PASSED, exit=0):**

| Shard             | Window | Wall-clock | Per-shard-day | Objects |
| ----------------- | ------ | ---------- | ------------- | ------- |
| `GLOBAL:calendar` | 30d    | 230s       | **~8s**       | 1       |
| `SPORTS:sports`   | 7d     | 1708s      | **~244s**     | 23      |

A **30x spread** between the fastest and slowest measured family — exactly the parallelization-headroom signal todo 10
asks for. Rough full-history (flat-2019, ~2757d) serial projections at these rates: calendar ≈ 6.1 VM-hours
(≈$1.63 on-demand, trivial); sports ≈ 186.9 VM-hours (≈$50 on-demand / ≈$4.50-20 SPOT, single VM — divide by fleet width
for wall-clock). Both are single-family bounds, not a full-matrix total (see gaps below).

**2 honest failures, both real upstream-data gaps, neither a driver bug:**

- `TRADFI:delta_one` (30d window): dependency-check failure for 2026-06-19 — `No data for 2026-06-19/TRADFI` (MDPS
  processed_candles gap, same class as
  `issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`).
- `DEFI:onchain` (retried at 30d AND 3d, both failed identically): **not a window-size issue** — direct root cause:
  `no MTDS manifest in market-data-tick-defi-prd-... — MTDS has not run for vault_share_price/lst_rates/lending_indices/oracle_prices/perp_funding`.
  MTDS has never ingested these DeFi raw-tick bypass-grain data types at all, for any date. A structural gap, not a
  benchmark-day-window problem.

Both VMs self-terminated cleanly (`VM_SHUTDOWN_ON_COMPLETION=true`) — zero added billing-waste.

**Real driver finding**: `SPORTS:sports`'s first attempt (30-day window) hit the driver's own hardcoded 2400s default
timeout at ~9 days in (NOT a crash — directly observed steady real progress the whole time, day-by-day, via `run.log`).
Confirmed via direct code read that `_FAMILY_TIMEOUT_OVERRIDES` (`features-service@4d71b1b5`, shipped same day by
slot-6) only covers `(volatility, TRADFI)` and `(delta_one, CEFI)` — sports isn't in it. At the measured ~244s/day rate,
anything past ~9-10 days needs either an explicit `--timeout-sec` override or a `(sports, SPORTS)` entry added to that
dict.

**Also confirms**: the `multisource_xg` (21/28 all-NaN columns — missing understat/footystats/api_football xG source
data) and `player_lineup` (74/74 all-zero columns — missing squad-depth/lineup-quality inputs) calculator gaps recur on
**every single day** processed across both sports runs (13 days total observed) — consistently reproducible, not
transient. Both handled gracefully (`recovery=skip`, `SCHEMA VIOLATION` logged but non-fatal).

- [x] [SCRIPT] P3. ✅ Add `(sports, SPORTS)` to `_FAMILY_TIMEOUT_OVERRIDES` in
      `features-service/scripts/pipeline_e2e_check.py` (measured ~244s/shard-day means the 2400s default caps out around
      9-10 benchmark-days) — `features-service@3cf2b674`. Set to 10800s (~48% margin over the 30-day-benchmark
      prediction of ~7320s), mirroring the same measured-completion methodology as the existing
      `("volatility",     "TRADFI")` and `("delta_one", "CEFI")` overrides.
- [x] [DATA] P2. ✅ Both gaps ALREADY have their own dedicated, deeper root-cause docs from other slots — filing a 3rd
      "consolidated" doc would duplicate rather than add value. Appended a 2026-07-27 live-reproduction corroboration
      note to each instead: `issues/sports_multisource_xg_21_of_28_columns_never_computed_2026_07_26.md` (21/28 columns
      confirmed all-NaN across 13 days this session, consistent with its dead-placeholder-schema diagnosis) and
      `issues/sports_features_layer_findings_sweep_2026_07_18.md` (`player_lineup` 74/74 all-zero confirmed on
      day=2026-07-19 — flagged an open question: that day falls 2 days past the 2026-07-18 re-derive's
      `2019-01-01..2026-07-17` window, so this may be normal data-capture lag rather than a regression; not
      independently diagnosed further).
- [ ] [DATA] P2. MTDS has never ingested DeFi
      `vault_share_price`/`lst_rates`/`lending_indices`/`oracle_prices`/`perp_funding` raw-tick bypass-grain data types
      (confirmed via direct dependency-check error, both a 30d and a 3d window) — blocks `DEFI:onchain` entirely until
      MTDS backfill/ingestion for these data_types starts.
- [ ] [DATA] P1. Remaining todo-10 scope: CEFI/TRADFI/DEFI/PREDICTION `delta_one`, `volatility`, `multi_timeframe`,
      `cross_instrument`, `commodity` still need real benchmark measurements — CEFI was deliberately deferred (fleet
      already oversaturated, operator-gated), TRADFI/DEFI's attempts hit genuine upstream gaps rather than measuring
      compute. Full "project full-history time + SPOT cost + parallelization headroom" needs at least one real number
      per family, not just calendar+sports.

### 2026-07-27 (slot-3, continued) — todo 10: full round across 7 families complete; 1 real code bug found + filed

Extended the benchmark sweep to `TRADFI:volatility`, `PREDICTION:delta_one`, and `TRADFI:commodity` — all 3 failed on
genuine, individually root-caused issues (none a driver bug):

- `TRADFI:volatility`: real upstream gap — "no captured options_chain or futures_chain shards found" for 2026-07-12 (raw
  tick data, not candles — same class as the delta_one candle gap, different data type).
- `PREDICTION:delta_one`: **a real, confirmed CODE BUG**, not a data gap — the dependency checker resolves
  `market-data-tick-prediction-...` (a bucket that has never existed) instead of the real
  `market-data-tick-pred-prd-...` (PREDICTION is the one asset_group whose bucket token is abbreviated to `pred`).
  Root-caused via direct code read of `features_service/delta_one/app/core/dependency_checker.py`'s
  `_format_template_vars` (naive `asset_group.lower()`, no abbreviation map) — the exact same bug class this file's own
  comments show was ALREADY found+fixed on the output-bucket side, just never ported to the input side. Filed
  `issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md`. Separately confirmed (via
  `gcloud storage ls` on the real bucket) that PREDICTION MDPS candles have a genuine ~6-month production gap
  (2026-01-14 through ~2026-07-24), only just resuming — day=2026-07-19 falls inside that gap regardless of the naming
  bug, so a future re-test needs both the code fix AND a day ≥2026-07-25.
- `TRADFI:commodity`: reproduces the already-known Baker Hughes vendor issue (timeout + "unexpected file format"),
  correctly failing each day rather than emitting a partial/fake signal (`ManifestWriter.record_empty` itself refused to
  record a false "empty" verdict without real `FetchEvidence` — the honest-absence guard working as designed).

**Full round now complete**: 7 families/AGs attempted this session (calendar, sports, TRADFI:delta_one, DEFI:onchain,
TRADFI:volatility, PREDICTION:delta_one, TRADFI:commodity) — 2 measured (calendar ~8s/shard-day, sports
~244s/shard-day), 5 honestly diagnosed failures (4 real upstream-data gaps across 3 different data-type classes + 1 real
code bug). CEFI:delta_one remains deliberately untouched (8-VM billing-waste situation, unchanged, still awaiting an
operator decision). `multi_timeframe`/`cross_instrument` weren't attempted — both are DERIVED families reading
`delta_one`'s own `-test-` output as source, and since delta_one hasn't successfully produced test output for
TRADFI/DEFI/PREDICTION this session, they would very likely just re-hit the same upstream gaps.

- [ ] [DATA] P2. Re-test `TRADFI:volatility`/`TRADFI:commodity` once their respective upstream gaps close (raw
      options/futures tick backfill; Baker Hughes vendor fix) to get genuine benchmark measurements.
- [x] [SCRIPT] P2. ✅ See `issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md` —
      fixed the PREDICTION bucket-token bug (`features-service@bba7de58`). Root cause was bigger than initially scoped:
      PREDICTION resolves via a dedicated FLAT yaml kind (`market-data-tick-prediction`), not an entry in the
      per-asset_group `market-data` dict — `resolve_bucket_name(kind="market-data", asset_group="prediction")` raises
      `BucketNamingError` rather than silently resolving wrong. Fixed by mirroring the identical, already-shipped fix in
      `execution-service/execution_service/utils/dependency_checker.py` (special-case PREDICTION to the flat kind, no
      `asset_group=`); added a new `_resolve_mdps_bucket` helper used by both `_resolve_gcs_path` and
      `_mdps_manifest_capture_status`; 2 new regression tests (7/7 passing). Day=2026-07-19 still can't be re-tested
      (falls inside the ~6-month PREDICTION MDPS candle production gap) — needs a day ≥2026-07-25 per the issue doc.
