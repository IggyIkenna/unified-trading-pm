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
last_updated: 2026-07-24
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
- [ ] 9. [DATA] P0. RUN + VALIDATE `/data-pipeline-check-features` e2e: multi-day input window per family, prove
      force+skip for every MVP feature shard (all families × valid AGs). Report written.
- [ ] 10. [DATA] P1. Steady-state benchmark VMs (250GB disk) per representative shard-type; measure amortized per-shard-
      day throughput (RX + rows/s + wall-clock); project full-history time (honest floor + flat 2019) + SPOT cost +
      parallelization/optimization headroom.
- [ ] 11. [DATA] P0. Cross-repo orphan/lineage audit (MTDS→MDPS→features→ml/strategy) + MIGRATE existing candle/feature
      data to zero orphans (MVP or not). Migrations run to real completion (data-correctness heartbeat).
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

## Deferred work after 2026-07-27

| #   | Item                                                                                                                                | Priority | Where tracked                                                             | Gating                     |
| --- | ----------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------- | -------------------------- |
| 1   | Root-cause / fix worker-session teardown killing long-running check-skill drivers                                                   | P1       | `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` | none                       |
| 2   | Add `--resume`/checkpoint to `pipeline_e2e_check` so a killed run doesn't restart the whole matrix                                  | P2       | same issue doc                                                            | depends on #1's root cause |
| 3   | ✅ DONE 2026-07-27 (slot-9) — Loosen/backoff `launch_vm_and_wait`'s launcher-script timeout under fleet contention (`utl@137e219c`) | P2       | same issue doc                                                            | none                       |
| 4   | Root-cause non-deterministic instrument_type path segment for identical force re-runs                                               | P3       | `mdps_candle_path_instrument_type_segment_nondeterministic_2026_07_27.md` | none                       |
| 5   | Complete todo 8's actual scope (skip-proof + defi/tradfi/sports/prediction reps) once #1/#2 land                                    | P0       | this plan, todo 8                                                         | #1                         |
| 6   | Complete todo 9 (`/data-pipeline-check-features`) — not yet attempted this session                                                  | P0       | this plan, todo 9                                                         | #1                         |

### 2026-07-20 — OPERATOR CONTRACT: "empty window" vs "not fetched yet" are TWO signals (durable rule)

Operator, verbatim: _"the key is knowing what is empty data because theres nothing to aggregate in the window vs not
fetched yet that's where the manifest needs to help and different consumers live and batch will have different ways of
handling depending on their needs"_

**The contract (durable — belongs in `/codex/02-data/honest-absence-downstream-handling.md` at the post-phase codex
audit; journaled here so it is not lost first):**

| Question a consumer asks                   | Which surface answers it        | Representation                                                                                    |
| ------------------------------------------ | ------------------------------- | ------------------------------------------------------------------------------------------------- |
| "Was this WINDOW active?"                  | the **parquet**, per bin        | row EXISTS on the session grid with **NaN price-like + 0 volume** = covered, nothing to aggregate |
| "Was this SHARD-DAY ever fetched/derived?" | the **manifest**, per shard-day | 4-state `capture_status`                                                                          |

- `captured` — derived, ≥1 bin had a real observation.
- `empty_confirmed` + a **typed** `EmptyConfirmedReason` — derived, but the WHOLE shard-day legitimately had nothing.
- `attempted_failed` + `error_reason` — we tried and it broke.
- `expected_unattempted` / no row — **never attempted**. There is no parquet to be NaN.

**Why it matters:** NaN alone cannot carry both meanings. A consumer must never infer "was this fetched?" from NaN in a
parquet, nor "was this window active?" from the manifest alone. Live and batch consumers handle each case differently
per their own needs, so the pipeline's job is to PRESERVE the distinction faithfully, never to paper over it. This is
exactly why LOCF (carry-forward) is wrong for `derivative_ticker`: it fabricates an observation in a window that had
none, destroying signal (1) and making the gap invisible.

**Two failure modes this rule makes checkable (NEW checks for both skills):**

1. manifest `captured` but NO parquet object = **phantom capture** (already checked — this is the MTDS-documented
   `PHANTOM_CAPTURED_NO_OBJECT`).
2. parquet present but **100% NaN bins** while the manifest says `captured` = should have been `empty_confirmed` with a
   typed reason. An all-NaN "capture" is the INVERSE phantom and is equally misleading. **Add this assertion to the MDPS
   driver's content check** (todo below).

**Applied immediately to the in-flight P0 fix** (`issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md`):
the fix must (a) leave empty bins NaN/0 rather than LOCF-filling them, (b) record `empty_confirmed` + typed reason when
the ENTIRE shard-day is empty rather than writing an all-NaN parquet as `captured`, and (c) document the two-signal
contract in-code so nobody "helpfully" re-adds carry-forward.

- [ ] NEW todo. [SCRIPT] P1. Add the all-NaN-parquet-vs-`captured` assertion to `/data-pipeline-check-mdps` (and the
      features twin where a family can emit an all-null feature frame) as a distinct `content_check=` verdict, so the
      inverse-phantom is caught the same way the phantom is.
- [ ] NEW todo. [DOC] P2. Promote the two-signal table above into `/codex/02-data/honest-absence-downstream-handling.md`
      at the post-phase codex audit (SSOT direction: codex, not this plan).

### 2026-07-20 — MEASURED throughput overturns the codex's compute-bound assumption (ETA input)

Authoritative VM summaries (e2-standard-8, pd-balanced 250GB, cefi DERIBIT, one day, 7 timeframes each):

| run                                 | per-instrument-day | writes        | evidence                                       |
| ----------------------------------- | ------------------ | ------------- | ---------------------------------------------- |
| `trades` (writes SUCCEEDED)         | **25,948 ms**      | ✅ 14 objects | `cefi 51.9s 2 success 0 failed 15,230 candles` |
| `derivative_ticker` (writes FAILED) | 2,105 ms           | ❌ 0 objects  | 12x "faster" ONLY because it never wrote       |

**The candle pipeline is WRITE/IO-BOUND, not compute-bound.** Of the ~25.9s per instrument-day, the polars aggregation
is only **~1.5s** (measured: the `POLARS AGGREGATED: 1440 1m … 1 24h` cascade spans 13:52:30.763→13:52:32.235). The
other ~94% is GCS write + manifest. Per instrument-day the writer emits **7 separate small parquet objects** (one per
timeframe) — small-object overhead dominates.

**This CONTRADICTS `/codex/06-coding-standards/performance-targets.md`**, which classifies `mdps_compute` as
"compute-bound, sublinear-70%" and recommends `c2-standard-16` for the <6h target. On this measurement a bigger CPU SKU
buys almost nothing. **Correct optimization levers, re-ranked by the measurement:**

1. **Write parallelism** — MDPS `max_workers` auto-resolves to `min(cpu_count,16)` = 8 on e2-standard-8, but the
   observed instrument cascade ran effectively serial (`25,948ms/instrument x 2 = 51.9s total`, i.e. sum == total). **If
   the 8 workers are not actually overlapping the writes, that is the single biggest win available** — verify and fix
   before sizing any fleet. (Explains why the codex's serial-day estimate is so large.)
2. **Disk throughput** — pd-balanced 250GB gives ~70 MB/s; `BOOT_DISK_TYPE=pd-ssd` (0.48 MB/s per GB vs 0.28) or a
   larger pd-balanced buys proportionally more write bandwidth. Directly attacks the dominant cost.
3. **Fewer/larger objects** — 7 small parquets per instrument-day is small-object-overhead-heavy. Batching timeframes
   (or instruments) per object would cut write count materially. NOTE: any such change interacts with the chain-bundle
   rule and the canonical path shape — do not change layout without the operator's A/B/C canonical ruling.
4. **Fleet width** — still the reliable multiplier (MDPS is NOT Tardis-capped), but it multiplies a write-bound unit, so
   per-VM disk/write-parallelism must be fixed first or you just buy N x the same bottleneck.
5. **Rust / faster libs** — LOWEST priority for candles on this evidence: the compute is already polars and is only ~6%
   of wall-clock. (The Python-loop hot spots B1 found — whale-detection O(n_intervals x n_ticks), `_carry_forward_ohlc`
   — matter for the `trades` HFT-feature path specifically, not the write-bound aggregate.)

**ETA caveat (honest):** a defensible DeFi-MVP ETA needs (a) the P0 derivative_ticker fix landed (that data_type
currently writes nothing), (b) confirmation of whether the 8 workers actually overlap writes (item 1 — it changes the
answer by up to ~8x), and (c) the DeFi MVP instrument x data_type shard count. Items (a) and (b) are in flight; the
per-instrument-day unit cost above (25.9s serial, write-bound) is the measured input to plug in. Quoting an ETA before
(b) is resolved would be guessing at the dominant term.

- [ ] NEW todo. [DATA] P0. Verify whether MDPS `max_workers` (8 on e2-standard-8) actually OVERLAPS the GCS writes.
      Measured `25,948ms/instrument x 2 == 51.9s total` implies SERIAL. If writes are not overlapped, fixing that is the
      single largest backfill speedup available and it changes the ETA by up to ~8x.
- [ ] NEW todo. [DOC] P2. Correct `/codex/06-coding-standards/performance-targets.md`: `mdps_compute` is WRITE/IO-bound
      (measured ~94% write, ~6% polars), not compute-bound; the c2-standard-16 recommendation does not follow.

> The "CORRECTION: the candle write bottleneck is NOT the MTDS 50GB-disk issue" entry (2026-07-20, no open todos) was
> extracted verbatim to `/plans/archive/2026_07/data_pipeline_check_mdps_features_history_2026_07_24.md`.

### 2026-07-20 — operator: manifest durability is a FALSE tradeoff + scope expansion

**(1) "must be a better way to do this right? without killing the data loss think hard"**

My earlier framing ("durability-vs-throughput tradeoff") was WRONG and I corrected it. The cost is not flush FREQUENCY —
it is that each flush does a **read-modify-write of a GROWING file** (`_index/per_vm/{vm}.parquet`), so total flush work
is **O(n^2) in shards-per-VM** while STILL only guaranteeing "SIGKILL loses <= 1 shard". **The current design is
strictly dominated: simultaneously slow AND lossy.** A better design is faster AND loses nothing. Dedicated design agent
dispatched to validate against the code and rank:

- **A. Per-shard immutable object** (`_index/per_vm/{vm}/shard-{seq}.parquet`) — O(1) per shard, O(n) total; durability
  IMPROVES to **zero shards lost**. Extends the EXISTING `_index/per_vm/` merge-on-read pattern one level down. Key
  check: does the consolidator/`read_availability_index` glob a PREFIX (nearly free) or expect exactly one file per VM?
- **B. Write-ahead receipt + single materialisation** — tiny O(1) receipt per shard; full parquet once; replay on crash.
- **C. Async flush off the critical path** — keeps per-shard durability, overlaps flush with the next shard's compute.
  ORTHOGONAL, combinable with A/B; changes the guarantee not at all.
- **D. Co-locate the manifest row with the candle write** (no extra round-trip) — biggest layout change, GATED on the
  pending canonical A/B/C ruling.
- **E. Batch per instrument** — FALLBACK only (this was my original, inferior suggestion); requires stating a new
  crash-loss bound.

HARD CONSTRAINT carried into the design: manifest COMPLETENESS is already a live problem (cefi day=2026-04-14 has 20,734
candle objects vs 6 MDPS manifest rows corpus-wide), so the design must cut flush COST without ever reducing row COUNT
or making rows easier to lose.

**(2) Scope expansion (operator):** _"keep going and improving mdps and dont forget to do all AG that are relevant (not
the ones already in candles) and do features service across all shards too"_

- MDPS must be exercised across **ALL relevant asset_groups**, prioritising the ones that do **NOT** already have
  candles (i.e. the REMAINING work) rather than re-proving the covered ones. Requires first enumerating the
  candle-coverage gap per (ag, venue, data_type, timeframe) from the manifest — that enumeration is also the ETA
  denominator, so it does double duty.
- features-service must be exercised across **ALL shards** (all 8 families x their valid asset_groups, ~29 viable cells
  per the launcher's `_is_viable_cell` matrix).
- Sequencing reality: the features sweep is partly gated on candles existing (candle-dependent families will honestly
  report `no_captured_input_for_window` until the candle backfill runs) — so MDPS coverage leads, features follows, and
  the honest-gap verdicts in between are themselves the signal, not a failure.

- [ ] NEW todo. [DATA] P0. Enumerate the candle-coverage GAP per (asset_group, venue, data_type, timeframe): which cells
      ALREADY have candles vs which do not. Drives both "which AGs to run" and the ETA denominator.
- [ ] NEW todo. [DATA] P0. Run `/data-pipeline-check-mdps` across all relevant AGs NOT already in candles.
- [ ] NEW todo. [DATA] P0. Run `/data-pipeline-check-features` across ALL shards (8 families x valid AGs).

### 2026-07-20 — ✅ SPOT preemption auto-recovery was NOT fleet-wide; now it is (`deployment-service@c79f984`)

Operator: _"vms are SPOT and need to recover themselves if they go down via auto recovery think we have that for some
vms already so propagate if not there."_ **They were right to doubt it — and the gap was much wider than "some".**

**MEASURED (I verified the headline myself, independently of the agent): 58 launchers pass `--provisioning-model=SPOT`;
only ~10 emitted the `vm-logs/{vm}/PREEMPTED` blob. ~48 SPOT launchers were preemption-BLIND.** The
`RelaunchPreemptedVm` machinery is well-built and correct — but its **trigger** was missing, so a preempted VM
classified as `EXIT_NONZERO`/`GONE_NO_CAPTURE` and **PAGED a human** instead of auto-recovering.
`/codex/05-infrastructure/spot-vms-for-backfill.md` asserts the signal is "wired fleet-wide via `launcher_common.sh`" —
**that claim is false and the codex is now stale** (todo below).

**The mechanism (verified end-to-end):** VM shutdown checks `instance/preempted` → writes `PREEMPTED` blob →
`_gcs.is_vm_preempted` + `read_launch_params` + `read_progress_checkpoint` → `classify_terminated_vm` checks `preempted`
BEFORE exit_code → `DP_VM_PREEMPTED` (AUTO_RECOVER, DP-VM-007) → `RelaunchPreemptedVm.relaunch()` replays
`LAUNCH_PARAMS.json`, re-resolves `*_TARBALL_SHA` pins, budget 48/day/prefix. Resume overrides `START_DATE` to
`last_completed_date` **only if `monotonic=true`**; a `--force` run with non-monotonic/absent checkpoint still **PAGEs**
`force_run_not_replayable` — never silent. `PROGRESS.json` emission was ALREADY fleet-wide (UTL `record_vm_progress` +
`vm-exec-with-gcs-tee.sh`), which is why only the trigger was missing.

**CORRECTION (2026-07-25):** "ALREADY fleet-wide" is not exceptionless —
`plans/active/lst_rate_honest_coverage_2026_07_21.md` (2026-07-21/22) documents a concrete production counter-example:
`launch-mtds-pyth-lst-backfill-vm.sh` does NOT write a `PROGRESS.json` checkpoint (that session's own correction:
"unlike the newer PROGRESS-checkpoint contract referenced in CLAUDE.md — that's a DIFFERENT, newer launcher family"),
and the VM preempted after ~10hrs requiring a manual manifest-derived resume rather than an auto-resume via checkpoint.
Root cause of why this specific launcher lacks coverage despite booting via the shared `setup-data-pipeline-vm.sh` seam
is not yet diagnosed anywhere in the corpus — flagged here rather than swept into
`issues/vm_fleet_preemption_autorecovery_gap_2026_07_23.md` (that doc tracks the separate early-shutdown-script
`PREEMPTED`-signal blind spot, not this checkpoint-emission gap).

**Fix:** `setup-data-pipeline-vm.sh` now installs `uts-preemption-signal.service`, a systemd unit mirroring Google's own
`google-shutdown-scripts.service`, writing the same blob with the same `preempted=true` gate. Chosen because gcloud
accepts only ONE metadata `shutdown-script`, so a unit **composes** with the ~10 launchers already emitting it inline
rather than colliding. Every blind launcher boots from this one seam — including **both launchers I extended for these
skills** (`launch-mdps-backfill-vm.sh`, `launch-features-vm.sh`) and `launch-mdps-sharded-backfill.sh`. Also registered
**`mdps-sports-`** in BOTH registries (previously emitted by the sharded launcher but registered in neither →
unmonitored AND unrecoverable; sports confirmed genuinely in scope via its dedicated `STALL_TIMEOUT_SEC` +
`STALL_PROGRESS_REGEX` against a live run.log). New guard test: **no SPOT launcher may be preemption-blind**. **Safety
is structural** — inert on live/forward/cron/paper VMs because they are on-demand and GCE never sets `preempted=true` on
them; no exclusion list needed. QG GREEN (339s, 2781 passed/5 skipped).

**Shipped by DIRECT PUSH under the closed dirty-deps carve-out** (UAC concurrently mid-edit by my own P0 agent, so
quickmerge's dep pre-flight could not pass). **Multi-agent hazard hit and handled**: a concurrent agent had staged 13
foreign files into the shared index (17 staged, 1,556 insertions); caught it via the mandatory no-path-arg
`git status`/`git diff --cached --stat`, `git reset`, re-staged ONLY my 4 by name. Foreign work never entered the
commit.

**RESIDUAL RISKS (carried forward, not swept):**

1. **Arg-required launchers still cannot actually recover** — `launch-features-vm.sh` exits 2 without
   `--feature-family`/`--asset-group`, and the relauncher passes ENV only. Result is a loud CRITICAL
   `DP_VM_PREEMPTED_NO_RELAUNCH`, not silence — but not recovery either. **This directly affects the features backfill**
   and is the next thing to close (needs `lc_write_launch_params` adoption or env-arg support).
2. **Manual delete ≈ preemption exposure now spans ~48 more launchers.** A prior incident (manual delete → relaunch →
   two VMs 469ms apart → Tardis 403 lockout, 1181 rejections) is the precedent. Mitigated by the `preempted=true`
   metadata gate (a manual delete does not set it), the Tardis guard, and the 48/day budget — but worth review before
   the next wide SPOT wave.
3. **Relaunch scope amplification**: `launch-mdps-sharded-backfill.sh` with no args defaults to all 5 AGs x all years —
   a preempted shard could relaunch dozens of VMs. Absorbed by presence-skip (cost, not corruption); real fix is the
   `lc_write_launch_params` rollout.
4. **Not runtime-proven**: `bash -n` clean + guard tests pass, but only a live SPOT reclaim proves the unit fires.
5. `launch-prediction-features-vm.sh` (broken: packages a deleted repo, no SPOT, 50GB disk) deliberately NOT touched —
   it is operator-gated A/B/C in `issues/mdps_features_deadcode_consolidation_2026_07_20.md`.

- [ ] NEW todo. [DOC] P1. Correct `/codex/05-infrastructure/spot-vms-for-backfill.md`: the preemption signal was NOT
      wired fleet-wide via `launcher_common.sh`; it is now installed by `setup-data-pipeline-vm.sh` as a systemd unit.
- [ ] NEW todo. [SCRIPT] P1. Close residual risk 1 — make arg-required launchers relaunchable (features especially).

### 2026-07-20 — my manifest-flush hypothesis was REFUTED by measurement; the real cost is 1000x bigger

**I was wrong, and the correction is more valuable than the original hypothesis.** I suspected the per-shard manifest
flush was doing an O(n^2) read-modify-write. **Measurement refuted it:**

- `ManifestWriter.flush()` deliberately does NOT force the per-VM rewrite — it DEBOUNCES (50 entries OR 5.0s,
  `_writer_io.py:291` -> `_state.py:706`); only `close()`/atexit force it. Shipped 2026-06-21 as `utl@6b6d53bd`.
- The live log line `(8 total entries, 7 new)` **proves the debounce worked** — 7 rows coalesced into ONE rewrite,
  not 7.
- Measured on the actual shard the profiled run produced: **14 rows / 23,438 bytes**, `to_parquet` = **0.010s**, ~2
  rewrites for the whole run, **~47 KB total rewritten**. The manifest WRITE is ~**0.02s** of a 51.9s run.
- => "Batch the flush" (my Option E) was ALREADY SHIPPED; per-shard-object / WAL / async-flush (A/B/C) would optimise
  **0.02s** while adding durability-relevant moving parts. **All rejected on evidence.** The operator's instinct that
  there must be a better way was right — but the better way is not on the write path at all.

**The REAL cost is a READ amplification** (filed `issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`):
`_publish_emission_check` -> `compute_completeness_fraction` -> `_build_capture_status_map(index)` builds a
**full-corpus python dict over EVERY manifest row x 25 key columns** to serve a lookup whose `upstream_window` is a
literal **1-element list** — **3x per instrument** (ohlcv_1m/1h/1d are policy-gated from `trades`), **unmemoized**, and
each flush calls `_invalidate_index_cache` forcing the next check to re-merge.

Measured scaling: 22,719 rows 0.11s -> 1,454,016 rows **13.14s** (super-linear, 9.04 us/row).

**I VERIFIED the prod index sizes myself** (`gcloud storage ls -l`): **defi 1,579.3 MB**, cefi 159.1 MB, tradfi 77.4 MB,
sports 46.1 MB — against the **0.44 MB TEST index every timing was measured on**.

**⚠️ THIS INVALIDATES MY OWN ETA INPUT.** The 25.9s/instrument-day was measured against a **0.44 MB** index; defi-prd is
**3,614x** larger. On cefi-prd the same path projects to ~75-100s per policy-gated timeframe ~= **4-5 minutes per
instrument**. **Any backfill ETA built on the 25.9s number is optimistic by roughly 10x until this is fixed or the
projection is disproved.** Do not quote the 25.9s-derived ETA to anyone without this caveat.

**Fix is read-path ONLY** (so durability/honest-absence/layout are untouched): F1 filter-then-build instead of
full-corpus map; F2 memoize by index identity; F3 thread the ALREADY-EXISTING `manifest_index=` kwarg so 3 timeframes
share one read. Crash-loss bound identical to today.

**SECOND STANDALONE P0: the defi-prd availability index is 1.58 GB.** Any `read_availability_index` caller on defi
without a column/filter projection is one cache-miss from an OOM. Independent of the above.

- [ ] NEW todo. [DATA] P0. VERIFY the prod projection on a real prod-bucket MDPS run before sizing the win (is the
      emission check actually firing in prod, or short-circuited?). It is INFERRED from a measured curve + measured
      sizes, not observed on a prod VM. **This is the single biggest unknown in the ETA.**
- [ ] NEW todo. [SCRIPT] P0. Implement F1+F2 (UTL `manifest_completeness.py`) + F3 (MDPS `_publish_emission_check`),
      with the 1.4M-row perf guard (<0.5s vs 13.14s today).
- [ ] NEW todo. [DATA] P0. Audit every `read_availability_index` caller on defi for a missing column/filter projection
      (1.58 GB index, OOM risk).

### 2026-07-20 — my SECOND hypothesis refuted, and a P0 concurrency bug that BLOCKS the speed lever

**Refuted (again, by measurement — recording plainly):** I claimed `25,948ms x 2 == 51.9s` was a "smoking gun" for
serial execution. **It is an arithmetic identity.** `processing_stats.py:468`:
`avg_time = stats.duration_seconds / stats.total_instruments * 1000` — the log line is `total/N` by construction, true
for ANY N. It proves nothing about serial-vs-parallel. **Verified by direct read.** Two of my hypotheses have now been
killed by measurement (the O(n^2) flush, and this) — both times the corrected answer was more valuable.

**What is ACTUALLY true (measured from code):**

- The `ThreadPoolExecutor` IS used (`batch_workers.py:370`) and was **UNDER-FED, not serialised** — 2 futures into 8
  slots, 6 workers idle.
- Parallel axis is the instrument FILE only. **Dates, asset_groups, data_types and TIMEFRAMES are all serial loops.**
- **The 7 timeframe writes per instrument ARE strictly sequential** (`live_workers_chain.py:314`) — each iteration does
  encode -> finalize -> read-back -> upload -> manifest -> flush before the next starts. **That is the 10.7s gap.**
- Serialisation points found: S1 timeframe loop (dominant) · S2 a process-global per-VM manifest shard LOCK (one path
  per VM, so every worker thread contends on ONE lock; critical section = download+read_parquet+merge+to_parquet+upload)
  · S3 a fresh ManifestWriter + flush per (instrument x timeframe) · S4 a full parquet READ-BACK per write (14x on this
  run) · S5 the GIL at the pandas adapter boundary · S6 a hard cap of 2 on venue-file listing regardless of MAX_WORKERS
  (`cloud_data_provider.py:277`) · S7 the emission-policy manifest lookup on 3 of 7 timeframes — **independently
  corroborating the other agent's `compute_completeness_fraction` finding**.

**🔴 P0 CONCURRENCY BUG — filed `issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`. I VERIFIED BOTH HALVES BY
DIRECT READ.** `candle_write_mixin.py:406-411` `_set_prior_seed_context` writes
`self._seed_category / _seed_date_str / _seed_input_venue / _seed_underlying / _seed_pipeline_mode / _seed_frame_cache`
onto the **SHARED** orchestrator instance, while `batch_workers.py:332-335` submits `self._process_instrument_file` to
the pool. With `max_workers>1` over a HETEROGENEOUS file list (multiple venues/underlyings/pipeline_modes in one
data_type — the NORMAL backfill shape) a thread reads another thread's context and resolves the prior-day carry seed
from the **WRONG GCS path**. **SILENT** — wrong leading-bin prices, no crash, no `attempted_failed`, no manifest signal.

**Why this matters more than a normal bug: it BLOCKS the primary speed lever.** The pool being under-fed means the
obvious fix is "raise concurrency" — and raising concurrency is EXACTLY what triggers this corruption. So the
correctness fix is a hard PREREQUISITE for the throughput work, not a parallel task. It was invisible in my own smoke
run only because both files were DERIBIT/same-day/same-mode, so the clobbered values were identical — any homogeneous
single-venue test passes. The adapter itself is safe (`base_adapter.py:802` returns a fresh adapter per call).

**Biggest lever (R1, from the probe):** run K **date-subprocesses** concurrently (`process_handler.py:783-807` is a
serial `while` over dates). ~K x wall-clock, and **LOW risk precisely because separate processes sidestep the shared-
`self` bug entirely** while keeping the C-arena reclaim `--subprocess-per-date` exists for. That is the months->weeks
lever, and it does NOT require raising in-process `max_workers` first.

- [ ] NEW todo. [SCRIPT] P0. Fix the shared seed context (per-call immutable value object + collision-proof frame-cache
      key) + a regression test that FAILS today (heterogeneous file list, assert each instrument resolves its OWN seed
      path). PREREQUISITE for raising in-process concurrency.
- [ ] NEW todo. [DATA] P1. Blast radius: did any PAST prod MDPS run use max_workers>1 over a heterogeneous list? If so
      those shards may carry wrong leading-bin seeds and need re-derivation.
- [ ] NEW todo. [SCRIPT] P0. Implement R1 (concurrent date-subprocesses) — the months->weeks lever that is SAFE today.

> The "✅ P0 derivative_ticker FIXED + shipped" entry (2026-07-20, no open todos) was extracted verbatim to
> `/plans/archive/2026_07/data_pipeline_check_mdps_features_history_2026_07_24.md`.

### 2026-07-20 — GIL question ANSWERED with measurement: yes it's the GIL; the throughput fix is MULTIPROCESSING (R1)

Operator: _"check if could be GIL in which case code needs refactor to use multi processes rather than concurrency
within a single python process."_ **Measured, decisive: YES.**

**The decisive benchmark** (real UTL `_build_capture_status_map` — VERIFIED a pure-Python `for` loop over
`_ROW_KEY_COLUMNS`, `manifest_completeness.py:169 — on ThreadPool vs ProcessPool, K=1..8):**

- Case A (the pure-Python map-build, GIL-HELD): **threads get WORSE with more workers — per-worker speed 0.67 → 0.11x
  (~1/K), wall EXPLODES 6.4s→41.5s** for the same work. Processes stay near full speed (0.86→0.52x); K=4 processes 12.3s
  vs threads 21.2s (**1.7x**). Textbook GIL. The thread-side degradation is the proof and needs no process-pool (the
  process side just confirms the alternative works; I independently confirmed the thread-side result is unambiguous).
- Case B (polars `group_by_dynamic`) + Case C (pandas numeric `.agg`): on the SAME thread pool, walls stay FLAT — they
  RELEASE the GIL. **So threads help the GIL-released fraction (I/O, polars, numeric agg) and do NOTHING for the held
  fraction.** Correction to a prior assumption: vectorized pandas numeric `.agg` RELEASES the GIL; the genuinely
  GIL-held pandas cost is the Python-callback/loop code (`_scatter_series`, `_carry_forward_ohlc`, HFT helpers) + the
  **3 redundant `.to_pandas()` per write** (`candle_write_mixin.py:519/571/618` — confirmed).

**Architecture (recommended):**

- **R1 (PRIMARY) — date-level multiprocessing:** the machinery ALREADY exists (`_run_date_as_subprocess`,
  `process_handler.py:675`) but the date loop dispatches SERIALLY (`:785`, blocking `subprocess.run`). Change serial →
  bounded-concurrent dispatch (Popen/ProcessPool of size K over dates). Separate processes → no cross-date GIL
  contention; C-arena reclaimed per child; **dates (~2400 multi-year) >> cores so it saturates any VM/fleet**; LOW risk
  (reuses tested subprocess code, only the dispatch loop changes). This is the "2 weeks" throughput lever.
- Keep the in-date `ThreadPoolExecutor(8)` — it profitably overlaps the GIL-RELEASED work within a date (Case B proves
  it).
- **R2 (secondary) — instrument-level ProcessPool** at `batch_workers.py:370`, only for single-DATE-heavy latency
  (one-day recompute), where date fan-out = 1.

**⚠️ NUANCE I must correct in the GIL agent's report:** it said R1 "fixes the shared-`self` seed bug for free." That is
only PARTLY true. R1 fixes CROSS-date races (different dates = different processes), but WITHIN one date the in-date
thread pool still runs over the shared `self`, so a date with heterogeneous files (multi-venue/underlying) still races.
**The seed-context fix (per-call value object) is REQUIRED independently of R1** — do not rely on R1 to cover it. (R2
WOULD cover it, since each instrument gets its own process, but R2 isn't the backfill recommendation.)

**The two operator targets are DIFFERENT problems — stated explicitly:**

- **"5s PER instrument-day" (LATENCY): multiprocessing buys 0% of this.** It needs per-unit Python-cost cuts: (1) the
  emission-check read-path fix (removes ~9-40s of GIL-held Python per PROD instrument — measured ~3-13s x ~3 calls),
  then (2) de-pandas the adapter (collapse the 3 redundant `.to_pandas()`, vectorize `_scatter_series`/
  `_carry_forward_ohlc`/HFT callbacks). 5s is a per-unit optimization program, reachable via those fixes.
- **"everything in 2 weeks" (THROUGHPUT): exactly what multiprocessing buys.** R1 at K workers x M VMs → per-unit /
  (K.M). Even at the un-optimized ~25.9s TEST residual, 16 workers ≈ 1.6s amortized; add VMs linearly. Reachable — BUT
  the emission-check read-path fix is a PREREQUISITE, because under a process pool each of K processes rebuilds its own
  1.45M-row dict → K copies in RAM → RAM caps K and stalls the fan-out. Multiprocessing AMPLIFIES the read-path bug.

**Sequencing that follows from the measurement:** (1) emission-check read-path fix [IN FLIGHT] — prerequisite for both
targets; (2) seed-context per-call fix — correctness prerequisite for in-date concurrency; (3) R1 concurrent
date-subprocess dispatch — the 2-week throughput lever; (4) de-pandas the adapter — the remaining per-unit latency to
hit 5s; (5) re-measure on a real VM against a PROD-sized index to PROVE the numbers.

- [ ] NEW todo. [SCRIPT] P1. Implement R1: bounded-concurrent `_run_date_as_subprocess` dispatch (the 2-week throughput
      lever). Gated on the seed-context fix for in-date safety.
- [ ] NEW todo. [SCRIPT] P2. De-pandas the per-write path: collapse the 3 redundant `.to_pandas()`
      (`candle_write_mixin.py:519/571/618`) + vectorize `_scatter_series`/`_carry_forward_ohlc`/HFT callbacks — the
      remaining per-unit latency cut toward 5s.

### 2026-07-20 — DeFi-MVP backfill ETA (MEASURED denominator) + the read-path-fix reframes the fleet size

**THE DELIVERABLE the operator asked for. Denominator MEASURED from UAC SSOT + PROD manifests; per-unit rate is the
measured input; caveats stated.**

**DeFi-MVP candle-backfill denominator ≈ 2.71M instrument-days** (unit = instrument × data_type × day; all 7 timeframes
in ONE pass, so NOT × timeframe). Of DeFi's 27 data_types only 3 produce candles (`needs_candle_processing`):

- `dex_pool_swaps` **2,703,497** (99.8% of the work; UNISWAP_V3 alone = 2.07M = **76%**, then PANCAKESWAP_V3 194k,
  BALANCER 132k, SUSHISWAP_V3 108k, CURVE 72k, AERODROME_V3 31k)
- `liquidations` **6,254**
- `derivative_ticker` **16** (P0-broken → excluded until the fix's tarball lands; only 16 for DeFi anyway)
- **Already-derived (MDPS manifest rows) = 0 → REMAINING = ALL.** (Physical candle objects exist under
  `processed_candles/` untracked by the manifest — the object↔manifest disconnect I filed; the in-flight
  canonical-migration-defi-rebuild may be reconciling it.)
- The naive "instruments × flat-days" (346M) OVERSTATES by ~128× — MDPS only derives days with captured raw ticks, so
  the measured captured-instrument-day count (2.71M) is the honest denominator. It is a GROWING lower bound (raw capture
  still in progress; measured off an immutable mid-migration snapshot, live index ~13% larger).

**CeFi reference ≈ 3.23M total / 2.06M workable** (excl. broken derivative_ticker's 1.17M), already-derived = **6**
(confirms my earlier figure).

**ETA (16 workers/VM = MDPS default; wall = N×rate/(16×fleet)):**

| rate/unit                                 | DeFi 1 VM×16w | DeFi 10 VMs | **DeFi: min VMs for 2 WEEKS** |
| ----------------------------------------- | ------------- | ----------- | ----------------------------- |
| 25.9s (test-measured)                     | 50.8 d        | 5.1 d       | **4 VMs**                     |
| ~260s (prod-projected, PRE read-path-fix) | 507 d         | 50.8 d      | **37 VMs**                    |
| 5s (operator target, needs de-pandas too) | 9.8 d         | ~1 d        | **1 VM**                      |

**🔑 CRITICAL REFRAME — the read-path fix I shipped today collapses this.** The ETA agent used ~260s as the "prod rate"
BECAUSE the `compute_completeness_fraction` full-corpus map-build added ~9-40s/instrument on the prod-sized index.
**That is exactly the term `utl@80d2497e` + `mdps@b4db0af` (16.7x, value-equivalent) removed.** So the realistic
post-fix prod rate is ~25.9s + prod-I/O residual, NOT ~260s → **the DeFi 2-week target now needs ~4-6 VMs, not 37.**
This MUST be confirmed by a real-VM re-measure against a prod-sized index (queued) before being quoted as final — the
16.7x was measured on the map-build in isolation, not yet end-to-end per-instrument on a prod VM.

**Practical backfill plan implied by the numbers:** shard by venue (UNISWAP_V3 is 76% → give it its own fleet lane);
DeFi is NOT Tardis-capped so scale fleet-wide freely; land the derivative_ticker tarball before counting its cefi 1.17M;
turn on R1 `MDPS_DATE_CONCURRENCY` per VM. At the post-fix ~25.9s rate, **all remaining DeFi MVP candles fit in ~2 weeks
on ~4-6 SPOT VMs**, or comfortably under 2 weeks with the de-pandas per-unit work toward 5s.

- [x] NEW todo. [DATA] P0. **DONE 2026-07-27 (slot-10)** — satisfied by
      `manifest_completeness_full_corpus_map_build-001`'s closure this session: a real `/data-pipeline-check-mdps` run
      against real prod raw ticks measured **19.4s** per-instrument-day end-to-end (cefi trades), confirming prod ≈
      19-26s, NOT 260s. See todo 13 above for the resulting fleet-size/ETA/cost delivery.

### 2026-07-20 — per-unit latency: safe wins + HFT vectorization SHIPPED; vol_clock + write-I/O floor characterized

De-pandas / HFT vectorization work, all BYTE-IDENTICAL (these feed the batch=live ε=0 spine, so allclose is not enough):

- `mdps@0ba3a72`: collapse redundant `to_pandas` 3->2 (schema+write share one conversion) + vectorize `_scatter_series`
  (170x, 9 edge cases proven). Honest note: safe plumbing alone = ~0.12% — it does not move the needle.
- `mdps@09da08c`: vectorize `_detect_whale_trades` (148x at 15s; **removes an O(n_intervals x n_ticks) throughput
  CLIFF** — a liquid instrument's whale loop measured 1791ms and scales with ticks, a real backfill hazard, not just
  latency) + `_calculate_tick_direction_momentum` (3.4x). 87/87 byte-identical each. **The agent caught + corrected its
  own spec: the prescribed `np.add.at` momentum vectorization is NOT bit-exact (few-ULP drift vs np.average on nearly
  every multi-tick group); only a per-interval numpy `.sum()` on the contiguous slice is 0-ULP.** ~2-2.5s saved per
  liquid instrument-day.

**Honest per-unit accounting (measured):** ~25.9s -> ~20-22s after the HFT vectorizations. **The 5s per-unit target is
NOT reachable without also attacking the ~20s per-write GCS/manifest I/O floor** (batch the 7 timeframe writes into
fewer objects) — which interacts with the canonical A/B/C ruling and is a bigger architectural change.
`_carry_forward_ohlc` (1.9ms, coupled honest-absence logic) and `_calculate_volume_clock_features` (biggest single
callback ~2.5s but the most intricate milestone-crossing logic) are left as REVIEWED follow-ups — deliberately not
gambling the just-fixed working adapters for the last seconds. **The 2-week THROUGHPUT target is already met by R1 + the
read-path fix (4-6 VMs); the 5s LATENCY target is a separate, fully-characterized optimization program (HFT done,
write-batching + vol_clock remaining).**

- [ ] NEW todo. [SCRIPT] P2 (reviewed follow-up). Vectorize `_calculate_volume_clock_features` (~2.5s, the largest
      single HFT callback) WITH a dedicated byte-identity test for the milestone-crossing edge cases (single-tick
      groups, zero total volume, <2 milestones). Prototype/plan in `de-pandas` agent output.
- [ ] NEW todo. [SCRIPT] P2. Write-batching: collapse the 7 per-timeframe parquet writes per instrument-day into fewer
      objects to attack the ~20s I/O floor (the remaining bulk of the 5s-target gap). GATED on the canonical A/B/C
      ruling (it changes the object layout).

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
