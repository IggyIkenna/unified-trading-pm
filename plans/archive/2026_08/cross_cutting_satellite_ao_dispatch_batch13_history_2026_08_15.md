---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 13 — extracted history (strategy-service LDR gate-red cluster)
summary: >-
  Verbatim extraction of 5 fully-closed todos from cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md (all citing
  strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md), moved out per task_template.md
  finding J to bring the parent plan back under its 1000-line hard cap. Pure record — 0 open todos, nothing dispatches
  from this file.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, satellite-batch, history-extract]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class:
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Extracted verbatim from cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md lines 91-173 (2026-08-15,
  slot-7·infra) per task_template.md §3 finding J — the parent plan crossed its 1000-line hard cap and these 5 todos
  (all already `[x]`-closed, all citing the same source issue) were the oldest self-contained, non-open-todo-adjacent
  block available for extraction.
---

# cross-cutting satellite AO dispatch batch 13 — extracted history

> Extracted verbatim from `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` (2026-08-15) — see that plan for
> the one-line pointer left in its place. All 5 items below were already `[x]`-closed at extraction time; nothing here
> is dispatchable.

- [x] ✅ [CODE] P2. **Diagnose how strategy-service's LDR HEAD went gate-red — NOT actually gate-red today; root cause
      isolated to a mis-triaged host-contention timing trip.** (2026-08-14, slot-27·infra) Clean-checkout re-run: fresh
      `git fetch`+`ff-only` to `origin/live-defi-rollout` (HEAD==origin, zero working-tree diff), then
      `bash scripts/quality-gates.sh --no-fix` in strategy-service → **`✅ ALL QUALITY GATES PASSED (112s)`, sentinel
      written at current HEAD `8f1aefc07c17`** — the reported failure does NOT reproduce. `git log -S`/`git blame` on
      the 4 flagged checks + their introducing code: strategy-service sets `CODEX_MAX_VIOLATIONS=4` (stable since
      2026-06-11, unchanged since) in its own `scripts/quality-gates.sh`; `base-service.sh`'s shared `$V` counter
      (`_max_v=${CODEX_MAX_VIOLATIONS:-0}`, ~L2416-2426) treats a violation count `<= _max_v` as `log_warn` ("within
      tolerance"), NOT a failure — but the underlying `log_fail()` calls for each individual STEP still print in ❌-red
      regardless of whether the run ultimately warns or fails. All 4 flagged checks (BaseModel: registry_router.py
      2026-04-21, operational_mode_router.py 2026-05-10 — check itself dates to 2026-03-09; STEP 5.37:
      analog_execution_gate.py kelly_boost 2026-05-30 — check dates to 2026-05-01; asyncio.run()-in-loop:
      live_routing.py 2026-08-10 — check dates to 2026-03-09; imports-inside-function: catalog_engine_coverage.py
      2026-08-14 — AST check dates to 2026-05-11) landed AFTER their respective checks already existed, but land at
      exactly the tolerance ceiling (V=4, `CODEX_MAX_VIOLATIONS=4`) — i.e. sanctioned ratchet headroom, not silent drift
      or a check that tightened afterward. One flagged STEP 5.37 site (`catalog_carry.py`'s
      `_, liquidation_threshold = resolve_ltv_mode(...)`) is a check REGEX false-positive: it matches the
      `liquidation_threshold\s*=` alternation on the tuple-unpack VARIABLE NAME, not an inline literal — the line is
      actually a call to the canonical resolver, the opposite of a violation (flagged for whoever picks up todo below).
      The actual 2026-08-10 exit-1 that blocked the one-line `cloudbuild.yaml` commit was almost certainly the
      independent, tolerance-exempt `<300s` duration hard-gate alone (`base-service.sh` ~L4471-4474, unconditional
      `exit 1`, outside the `$V`/`CODEX_MAX_VIOLATIONS` system) tripping under host contention (12s measured governor
      queue-wait that day) — `quickmerge.sh` itself documents this exact incident by date (STAGE 3 re-gate, ~L2445-2470:
      "measured 2026-08-10, 602s billable against a 600s cap under 11 concurrent quickmerges, with every content check
      passing... Telling an agent to go fix content that was never broken") and shipped a same-day CPU-vs-wall billing
      rework specifically to stop this false-failure class. **New finding not covered by an existing todo**:
      `quickmerge.sh`'s own contention-vs-content disambiguation guard (`_qm_other_fail`, ~L2463-2464) that exists
      BECAUSE of the 2026-08-10 incident is itself incomplete — it greps the re-gate log for any ❌/FAILED/ERROR line
      other than the duration message to decide "genuine content failure", but doesn't know some of those ❌ lines come
      from `CODEX_MAX_VIOLATIONS`-tolerated checks that the underlying script only WARNs on — so a run that is, in
      substance, ALSO just a duration-budget trip can still get misclassified as "a REAL failure" (exactly what the
      source issue doc's quoted evidence shows). Filed as a new todo below rather than fixed inline (out of this
      diagnosis todo's scope). Net: the 4 other todos below (move BaseModel/resolve STEP 5.37/fix or re-baseline the
      duration budget/fix the stale pointer) are still legitimate cleanup, but the BLOCKING premise — "every commit is
      blocked, HEAD is red" — is not currently true; a same-day re-run before attempting a real commit will very likely
      land it. Source:
      `plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [x] ✅ [CODE] P2. **Recorded justified exemptions (not a move) — 9 real classes, not 11.** The gate's own filtered
      check (excluding `# CORRECT-LOCAL`-annotated lines, which the raw `git grep -l` count in the source issue didn't
      account for) currently flags exactly 9 classes across 4 files: `api/registry_router.py` (4),
      `api/operational_mode_router.py` (2), `api/restriction_profile_router.py` (1), `signal_broadcast/transport.py`
      (2). All 9 are FastAPI request/response wire-shape DTOs bound to specific endpoints (admin registry envelopes,
      operational-mode transition body/reply, a restriction-profile HTTP envelope wrapping a UAC `RestrictionProfile`,
      and signal-broadcast ack/emission wire shapes) — not domain data contracts other services consume; two of the four
      files already self-documented this as a deliberate follow-up in their own module docstrings. Annotated each class
      with the repo's established `# CORRECT-LOCAL` exemption convention (already used in 8 other strategy-service
      files: `client_config.py`, `config_loader.py`, `reconciliation_routes.py`, `sports_position_tracker.py`,
      `position/models.py`, `position_interface/routing.py`, `risk/api/main.py`, `risk/models.py` — none of those needed
      touching, already exempt). Verified: QG-equivalent regex clean post-fix; full `quality-gates.sh --no-fix` green
      (`✅ ALL QUALITY GATES PASSED`, 31s) — strategy-service@621858344d (2026-08-14, slot-10·infra). Source:
      `plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [x] ✅ [CODE] P2. Resolved the STEP 5.37 inline HF/LTV/margin thresholds — unified-api-contracts@31b4ad958e +
      strategy-service@ac5cab7edb (2026-08-14, slot-29·infra). Added `MarginModel.REG_T` +
      `reg_t_initial_margin_long_pct`/`short_pct` fields to UAC `LIQUIDATION_PARAMS_REGISTRY` (50%/150%);
      `greek_model.py._reg_t` now reads those instead of inlining `Decimal("0.5")`/`Decimal("1.5")`. **Correction to the
      2026-08-14 diagnosis note**: `analog_execution_gate.py`'s `kelly_boost=Decimal("1.2")` hit was NOT genuine —
      re-verified live: it's a Kelly-criterion position-sizing multiplier on the analog execution gate, unrelated to
      margin/liquidation (confirmed via its own docstring: "Multiplier applied when all analogs were clean"), not a
      threshold sourced from any venue's margin model — same regex-false-positive class as `catalog_carry.py`'s
      `liquidation_threshold` var-name hits. Both false positives annotated `# CORRECT-LOCAL` (not migrated to UAC,
      which would be semantically wrong for a strategy-tuning constant). `strategy-service/scripts/quality-gates.sh`
      `CODEX_MAX_VIOLATIONS` ratcheted 4 -> 3 (STEP 5.37 class cleared); full QG green on both repos
      (unified-api-contracts 352s, strategy-service 141s, sentinel-verified). Source:
      `plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [x] ✅ [CODE] P2. **RESOLVED — already fixed by the 2026-08-10 CPU-vs-wall billing rework, no code change needed.**
      strategy-service@ac5cab7edb (2026-08-14, slot-27·infra). Re-verified under genuine contention (not just the 112s
      clean-host figure from the diagnosis todo above): 2 fresh `bash scripts/quality-gates.sh --no-fix` runs on the
      current LDR-tip HEAD, both under real host load — run 1: 134s wall (`time` real 2m14.415s), exit 0; run 2: 44s
      governor queue-wait (excluded from billable per base-service.sh's CPU-vs-wall rework) +
      `✅ ALL QUALITY GATES PASSED (152s)` billable work. Both comfortably under the 300s `MAX_DURATION` cap, including
      one run with real governor contention (30-44s queue-wait) — the exact contention scenario that produced the
      original 326s+12s=338s failure on 2026-08-10. Confirms the diagnosis todo's hypothesis: the billing rework already
      resolved this before this todo was ever picked up; no `MAX_DURATION` re-baseline or suite optimization is
      warranted. Source:
      `plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [x] ✅ [CODE] P2. Fix the gate's stale SCHEMA_CONTRACTS_AUDIT.md pointer message (and grep the fleet for the same
      template) — unified-trading-pm@144a18fed5 (2026-08-14). Repointed `plans/active/SCHEMA_CONTRACTS_AUDIT.md` →
      `plans/archive/SCHEMA_CONTRACTS_AUDIT.md` in the shared gate template (`base-service.sh`, `base-library.sh` —
      strategy-service and every other service source these, so the fix propagates fleet-wide with no per-repo
      duplication) plus 4 `.cursor/rules/*.mdc` and 2 `codex/*` docs carrying the same stale pointer. Fleet grep found
      no other verbatim copy of the gate check outside this repo (the UI repo's separate `context/` doc mirror was left
      untouched — out of this plan's repo scope). Source:
      `plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [x] ✅ [CODE] P2. **Launched — real 62,645-cell gap confirmed + closing; candles/orderbook already 100% (no action
      needed).** (2026-08-15, slot-4·infra) Live manifest read (bounded, column-projected
      `read_availability_index(columns=[...])`) found `ohlcv_1m` (candles) and `book_snapshot_5` (orderbook) already
      have ZERO `expected_unattempted` cells — the original todo's premise that all 4 sub-types needed a backfill was
      stale; only `derivative_ticker` (funding/ticker, 37,961 cells) and `trades` (24,684 cells) had a real gap,
      spanning 2024-10-01→2026-08-15 across 267 instruments, including 5,147+5,179 cells in the last 30 days alone
      (still actively growing). Root cause: the daily forward-poll launcher
      (`deployment-service/scripts/vm/launch-cefi-onchain-forward-poll.sh`) hardcodes EXTENDED-STARKNET's instrument
      list to `BTC;ETH;SOL` — but the live IS catalogue (`instruments-store-cefi-prd/prod/catalog.parquet`) has **200
      mvp=True perpetuals** for this venue, so only 3/200 were ever attempted daily; `derivative_ticker` was also
      missing from that launcher's per-venue data_types list entirely. **Fix path traced + verified live before
      shipping** (an initial launcher edit using the `--onchain-perp-symbols ALL` catalogue-driven sentinel was REVERTED
      after confirming `VM_TASK=cefi-onchain-forward-poll` has no dedicated branch in `setup-data-pipeline-vm.sh` and
      falls through to the generic `--operation download` path, which does NOT route onchain-perp venues through
      `OnchainPerpBatchHandler`/the `ALL` sentinel at all — shipping that edit would have been a silent no-op or
      regression). Instead launched the historical backfill via the ALREADY-CORRECT `launch-mtds-backfill-vm.sh`
      (`VM_TASK=mtds-backfill`, which DOES auto-detect onchain-perp venues via `ONCHAIN_PERP_VENUE_CHAIN` and route to
      `collect-onchain-perp-batch --onchain-perp-symbols ALL`):
      `bash scripts/vm/launch-mtds-backfill-vm.sh --asset-group CEFI --venues EXTENDED-STARKNET --data-types 'trades;derivative_ticker' --instrument-ids ALL --start 2024-10-01 --end 2026-08-14 --vm-name mtds-backfill-cefi-extended-starknet-fullhist-1`.
      VM `mtds-backfill-cefi-extended-starknet-fullhist-1` (asia-northeast1-c, e2-highmem-4, SPOT) confirmed RUNNING at
      T+3min (heartbeat blob live) and T+~4min run.log showed REAL progress:
      `OnchainPerpBatch: catalogue-driven universe for EXTENDED-STARKNET on 2024-10-02 = 76 symbols` (catalogue-driven,
      not the old 3-symbol hardcode) + `ManifestWriter: per-VM shard updated (202 total entries, 151 new...)` —
      day-chunked (5-day chunks, auto-selected for the recent-history tail), SPOT-preemption resumable, self-healing per
      the standard launcher contract; no further manual monitoring required this session. **Follow-up filed** (NOT fixed
      here — shared daily-cron script, 4-venue blast radius, needs its own verification): new todo in the parent batch
      plan + in the source doc's banner for fixing `launch-cefi-onchain-forward-poll.sh`'s EXTENDED-STARKNET (and likely
      LIGHTER-ZKSYNC/HYPERLIQUID/ASTER, same hardcoded-list pattern) instrument scoping so the gap doesn't re-accumulate
      once this one-time backfill converges. Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
