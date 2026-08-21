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
    /plans/archive/2026_08/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md,
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
      `plans/archive/2026_08/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
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
      `plans/archive/2026_08/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
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
      `plans/archive/2026_08/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
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
      `plans/archive/2026_08/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [x] ✅ [CODE] P2. Fix the gate's stale SCHEMA_CONTRACTS_AUDIT.md pointer message (and grep the fleet for the same
      template) — unified-trading-pm@144a18fed5 (2026-08-14). Repointed `plans/active/SCHEMA_CONTRACTS_AUDIT.md` →
      `plans/archive/SCHEMA_CONTRACTS_AUDIT.md` in the shared gate template (`base-service.sh`, `base-library.sh` —
      strategy-service and every other service source these, so the fix propagates fleet-wide with no per-repo
      duplication) plus 4 `.cursor/rules/*.mdc` and 2 `codex/*` docs carrying the same stale pointer. Fleet grep found
      no other verbatim copy of the gate check outside this repo (the UI repo's separate `context/` doc mirror was left
      untouched — out of this plan's repo scope). Source:
      `plans/archive/2026_08/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
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

## Additional entries extracted 2026-08-21 (line-cap condensation)

- [x] ✅ [CODE] P3. **DONE 2026-08-15 (slot-24·infra) — unified-trading-pm@a0689afd34.** `scripts/quickmerge.sh`'s STAGE
      3 re-gate guard (`_qm_other_fail`, ~L2482) now anchors on the re-gate log's own verdict lines instead of
      raw-grepping every ❌: if the log contains a hard `❌ Codex compliance FAILED` line, the script already `exit 1`'d
      right there (base-service.sh ~L2440-2442) and it IS a real failure; if instead it contains the WARN-tolerated
      `Codex compliance: N violations (within tolerance of M)` rollup, everything before that line is per-STEP
      `log_fail()` noise from checks that ran but did not fail the STEP (fires unconditionally per violation category,
      regardless of eventual tolerance — `qg-common.sh`), so the "other real failure" scan is now scoped to content
      AFTER that verdict line, where only STEPS that can still fail the run live (post-codex ratchets + the duration
      hard-gate). Verified against 3 mock re-gate logs before shipping (tolerated-codex + duration-only-fail →
      `other_fail=0`/host-contention as intended; tolerated-codex + a real typecheck `E ` line →
      `other_fail=1`/real-failure; hard codex-FAILED → `other_fail=2`/real-failure) — all 3 behaved as the fix intends.
      `bash scripts/quality-gates.sh` green (sentinel-verified at commit HEAD before the push-race rebase); quickmerge
      landed on LDR — note the shipped SHA `a0689afd34` differs from the original commit SHA `9f60b2e42b` because
      quickmerge's push retry rebased onto a moving remote tip mid-ship (high branch churn); post-push ancestry
      independently verified (`git merge-base --is-ancestor a0689afd34 origin/live-defi-rollout`) and the landed
      commit's content/message confirmed via `git show --stat`. No existing bats/unit test covers this inline guard
      (same as the original 2026-08-10 fix it extends — no dedicated test seam exists for logic embedded in the
      sentinel-retry loop); correctness was verified via the 3 standalone mock-log scenarios above instead. Repo:
      unified-trading-pm. Source:
      `plans/archive/2026_08/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md` (new
      finding, 2026-08-14 diagnosis)
- [x] ✅ [CODE] P2. **Diagnosed: mis-scoped for single-task AO dispatch, NOT attempted — corrected classification
      instead.** (2026-08-15, slot-31·infra) Concrete file-by-file scope survey of all 18
      `market_data_processing_service/app/adapters/*` files implementing `process_to_candles`, their 4 production caller
      sites, and `base_adapter.py`'s shared pandas helpers confirmed this is an atomic, single-PR migration (the
      ABC/Protocol boundary can't be half-converted across 18 polymorphic adapters) with 5 of 18 files
      (cefi/trades_adapter.py, cefi/book_snapshot_adapter.py, cefi/liquidations_adapter.py,
      sports/bucket_assignment_adapter.py, tradfi/ohlcv_passthrough.py) needing genuine groupby-based
      feature-engineering rewrites on live candle-production code — the same scope already operator-deferred twice under
      two archived predecessor plans, with a prior combined estimate of 2.0 calibrated AI-days, never a 1-hour task. Per
      CLAUDE.md's "AO-eligible = outcome DETERMINABLE by the worker alone" rule, did not attempt the migration; filed
      the full survey + recommended a dedicated design/execution effort (mirroring the sibling engine-internal
      conversion's benchmarked-verification pattern) as a new todo in `mtds_file_size_refactor_2026_06_08.md` (the
      item's designated SSOT owner) instead. Source issue:
      `plans/active/issues/mdps_adapter_protocol_polars_seam_mis_scoped_ao_dispatch_2026_08_15.md`
      (market-data-processing-service). Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [x] ✅ [CODE] P2. **PARTIAL — ui-reference-data.json untracked; capability-manifest.json intentionally LEFT TRACKED
      (real consumer dependency, not done).** unified-api-contracts@f70f29c8 (2026-08-15, slot-14·infra). Verified both
      files' actual consumers before untracking either: `openapi/ui-reference-data.json` is safe — its only real reader,
      `unified-trading-system-ui`'s `.github/workflows/uac-registry-sync.yml`, regenerates it by running
      `scripts/generate_ui_reference_data.py` from source (`pip install -e .` then invoke the generator), never reads
      this repo's committed copy — gitignored + `git rm --cached`, QG green (369s), quickmerge landed (post-push
      ancestry verified `f70f29c8f` on origin; quickmerge's own diff-check false-flagged "push landed but change did
      not" for this now-gitignored path — a known false-positive class since a deleted+gitignored file has no
      before/after diff to compare; confirmed the real land via
      `git cat-file -e origin/live-defi-rollout:openapi/ui-reference-data.json` → absent, as intended).
      `openapi/capability-manifest.json` is NOT safe to untrack as-is:
      `agent-orchestrator/server/mcp/manifest_loader.py` hard-requires it be a **committed** file in this repo's sibling
      clone (`_MANIFEST_REL`, `manifest_path()`; raises `ManifestUnavailableError` with no regen fallback if absent) —
      untracking it would break AO's capability MCP server on any fresh clone. Filed as a new followup todo below rather
      than silently skipped. Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [x] ✅ [CODE] P3. **WON'T-DO — regen-on-demand fallback deliberately not wired; documented in-code instead.**
      agent-orchestrator@16f8c4f66a (2026-08-15, slot-6·infra). The generator
      (`unified-trading-pm/scripts/openapi/generate_capability_manifest.py`) imports UAC-internal domain registries
      fleet-wide (`_capability_extract`/`_capability_gaps`/`_capability_orphan`/`_capability_readiness`,
      `unified_api_contracts.internal.architecture_v2.capability_manifest`) and sets up a mock-service env
      (`CLOUD_PROVIDER`/`CLOUD_MOCK_MODE`/`STORAGE_EMULATOR_HOST`/etc.) — wiring it as a live subprocess/import fallback
      inside AO's `manifest_loader.py` would contradict that module's own documented design (read-only,
      credential-free, minimal). The sibling todo above already resolved to keep `capability-manifest.json`
      permanently committed (not untracking it), so the forcing premise for a regen fallback ("the file might not
      exist") no longer applies — absence should only happen on a broken/partial checkout, and
      `ManifestUnavailableError` is the correct loud failure for that. Confirmed every MCP caller already handles it
      gracefully: `query_manifest()` in `server/mcp/tools.py` catches `ManifestUnavailableError` and returns an honest
      `ok: false` typed verdict, never a raw exception. Added a doc comment to `manifest_loader.py` recording this
      decision so a future reader doesn't re-raise the same question. `bash scripts/quality-gates.sh` green (3976
      passed, 2 skipped; dashboard tsc + vitest green); quickmerge landed on LDR, post-push ancestry verified
      (`16f8c4f66a` on `origin/live-defi-rollout`). Repo: agent-orchestrator. Source: this doc, todo above.
- [x] ✅ [CODE] P2. **STALE PREMISE — the "13 cells/~12.5k rows" digest figure is ~3 weeks stale; the actual retry
      mechanism is already live, but has a real coverage gap.** (2026-08-15, slot-27·infra). Live re-verification:
      `deployment-service/scripts/wave_launcher.py` (Cloud Run Job, host-cron `0 */3 * * *`) IS running — its own
      last-run sentinel `gs://deployment-scripts-central-element-323112/vm-census/wave-launcher-last-run.json` reads
      `{"ts": "2026-08-15T03:00:06Z"}`, i.e. it ticked ~90min before this check (the standalone Cloud Scheduler job
      `uts-prod-tradfi-wave-launcher-cron` in `asia-northeast1` shows `PAUSED` since 2026-06-24, but that's a dormant
      duplicate of the real host-cron path per the module's own code comment — not evidence the mechanism is off). A
      fresh, bounded (single manifest object, column-projected duckdb query, no new corpus walk) read of
      `market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` (371MB, 14.3M rows,
      last_modified 2026-08-15T04:29Z) found **798,028 attempted_failed rows / 16,171 distinct (venue,data_type,date)
      cells** — not 13/12.5k. Most of this is genuinely NOT a retry gap: `attempted_at` timestamps for the
      NYSE/NASDAQ/CME `NO_RAW_TICK_DATA_FOR_SHARD` + CME `SCHEMA_VALIDATION_FAILED` buckets (the bulk of recent
      activity) run through TODAY (2026-08-15), confirming the wave-launcher's docstring claim ("attempted_failed — the
      P1 retry is FOLDED IN") is true and live for those cells — they keep re-failing for a real reason (no source data
      / schema issue), not because nobody retried them. **Real finding, filed as a new todo below**: the single LARGEST
      bucket — CME ohlcv_1s/1m `WithinBoundsTradfiSourceZero`, 110,074 rows — was attempted exactly ONCE, on 2026-07-07
      (06:39-07:29 UTC), and never since, because every one of these rows has a blank `underlying` field:
      `_derive_cme_root()` (`wave_launcher.py:265-271`) returns `None` on a blank/empty `underlying`, so
      `compute_dispatch_candidates()` (`wave_launcher.py:318-332`) buckets them into `out_of_scope["CME:unmapped_root"]`
      and PERMANENTLY excludes them from every dispatch tick — a genuine, silent gap in the "P1 retry FOLDED IN" claim,
      distinct from the source-absence reasons above. (Minor aside, not worth its own todo: 6 rows across KRX/ICE/FX
      `ohlcv_24h` fail with `No module named 'yfinance'` — FX ohlcv_24h is explicitly DESCOPED 2026-06-30 per the
      wave-launcher's own comments, and this legacy Yahoo-daily surface is otherwise dead scope; too small/ likely-moot
      to action.) Source: `plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md`
- [x] ✅ [INFRA] P3. Wired an automated `/usr/local/sbin/*` sync — unified-trading-pm@d6bc752b3d (2026-08-15,
      slot-27·infra). Confirmed live via the repo (no host access from this role): no workflow, cron, or install
      script previously deployed `glue-runner-crash-loop-watchdog.sh` (or its 3 siblings —
      `docker-disk-cleanup.sh`, `tmpfs-disk-cleanup.sh`, `ci-vm-resource-watchdog.sh` — same
      systemd-`ExecStart=/usr/local/sbin/*` layout, same gap) to `/usr/local/sbin/`; every prior fix needed a
      manual SSM copy that evidently didn't happen consistently (per this doc's own 2026-08-06 Progress Log
      entry, the live watchdog copy had already drifted). Added `deploy-sbin-scripts.sh` (diffs the already
      10-min-refreshed slot mirror `${RUNNER_BASE}/repo` against each script's live `/usr/local/sbin/` copy,
      `install`s only the ones that changed) + `github-glue-deploy-sync.{service,timer}` (10-min cadence,
      `Wants=`/`After=github-glue-slot-refresh.service` so every activation pulls the mirror fresh first
      regardless of timer offset; runs as root since `/usr/local/sbin` is root:root 0755, unlike the
      unprivileged slot-refresh service). Wired into `setup-glue-runners.sh`'s `cmd_install` (guarded to the
      base/untagged pool only — these 4 scripts are host-wide singletons, not per-pool); documented in the
      README's Files table + Verify section. `shellcheck`/`bash -n` clean on the new + modified scripts;
      `bash scripts/quality-gates.sh` green (sentinel-verified at HEAD `fd9fcd858b`); quickmerge landed on LDR
      as `d6bc752b3d` (post-push ancestry independently verified). Live host deploy of the two new systemd
      units (`github-glue-deploy-sync.{service,timer}`) is a separate operational step for whoever next runs
      `setup-glue-runners.sh install`/has host access — this todo's scope was the code that makes future fixes
      self-propagate, matching this doc's own P1 pattern (the crash-loop-watchdog fix itself) of code-lands
      first, host-deploy follows. Source:
      `plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`
- [x] ✅ [BACKEND] P2. **Fleet swept — zero unfixed instances of the trap; only hit is the already-fixed source site.**
      (2026-08-15, slot-15·backend) Ran the cited command
      (`rg -n 'set -uo pipefail' -A 4 .github/workflows/ | rg -B1 'RC=\$\?'`) against every repo's `.github/workflows/`
      in the fleet checkout (28 repos incl. unified-trading-pm; excluded only the `*.stale-pre-history-rewrite-*`
      snapshot dirs and `scratch/`, neither of which carries live workflows). Single hit:
      `unified-trading-pm/.github/workflows/ldr-docs-gate.yml` lines 104-105 — these are the comment lines of the
      `set +e` fix this same issue doc's todo 1 already shipped 2026-08-10, not a live occurrence (the actual capture on
      line 115-116 already has `set +e` before it). Broadened the check beyond the literal 4-line window to catch
      variant spacing/ordering: grepped every repo's workflows for any `RC=$?`-shaped capture
      (`rg -n 'RC=\$\?' .github/workflows/`) and manually inspected the preceding shell state for each of the 7
      additional PM hits found this way (`promote-fleet-startup-failure-monitor.yml`, `sit-gate-stuck-detector.yml`,
      `glue-pool-starvation-monitor.yml`, `stale-build-watcher.yml`, `glue-runner-health-monitor.yml`,
      `branch-health.yml`, `reconcile-release-tags.yml`) — every one already has an explicit `set +e` immediately before
      its output-capturing `$(...)` call, so none carries the inherited-`-e` trap. No repo outside `unified-trading-pm`
      has any `.github/workflows/` file matching either pattern at all. No code change needed. Source:
      `plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md`
- [x] ✅ [CODE] P2. **CONFIRMED: NO — never cited in any actual promotion/sizing decision; nothing to flag.**
      (2026-08-15, slot-29·infra) Four independent, converging lines of evidence: (1) **The promote workflow's frozen
      decision artifact structurally cannot carry these figures** — `MinimalCandidateManifest.score_vector`
      (`unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/candidate_manifest.py:39-50`,
      `GroupBMetrics`) has exactly 6 fields (`sharpe_ratio`, `calmar_ratio`, `max_drawdown_pct`, `win_rate`,
      `backtest_days`, `total_return_pct`) — no `fill_rate`/`slippage` field exists anywhere in the schema the promote
      endpoint freezes at decision time. (2) **The 5 pre-flight promote gates are purely operational**
      (`/codex/04-architecture/promote-workflow-architecture.md`: Copper sandbox, venue API keys, alerting config,
      kill-switch YAML, recon green) — none are performance metrics. (3) **The capital-sizing mechanism (portfolio
      allocator) reads NAV/returns from PBMS**, not fill-rate/slippage (`/codex/03-services/portfolio-allocator.md` —
      zero `fill_rate`/`slippage` mentions in the whole doc); the one sizing mechanism that DOES exist for these
      strategies today, `/plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md`'s ADV-cap
      (`--adv-cap-pct`), sizes off Average Daily Volume, unrelated to fill-rate/slippage. (4) **No actual completed
      promote event exists for either strategy** — grepped the whole corpus for `STRATEGY_PROMOTED_TO_PAPER`/
      `STRATEGY_PROMOTED_TO_LIVE` co-occurring with `carry_staked_basis`/`carry_basis_perp`: zero hits (only references
      to the May-23 promote-workflow PLAN, never a completed promotion RECORD); separately grepped for
      operator-decided/capital-allocation language co-occurring with either strategy name: zero hits. Corroborated by
      the source finding itself (`/plans/archive/issues/multi_leg_paper_batch_live_parity_gap_2026_08_10.md`): as of
      2026-08-10, live execution didn't exist yet for these `AtomicInstruction`-based strategies at all ("a strategy
      promoted from paper today would have nothing to execute"), and the todo-6 paper-run analysis in
      `/plans/archive/2026_08/multi_leg_execution_systems_execution_2026_08_10.md` explicitly found **no prior paper
      equity data was even accessible** for comparison — i.e. no capital decision had meaningfully consumed a full paper
      run's economics at all, let alone its fill-rate/slippage sub-figures specifically. **Verdict: nothing to flag for
      re-check** — the pre-2026-08-10 fill-model overstatement is a real, already-fixed data-quality gap in the
      paper-run RECORDS themselves, but it never propagated into a promotion or sizing DECISION because neither decision
      mechanism ever consumed those fields. Source:
      `plans/active/cross_cutting_strategy_execution_determinism_2026_07_26.md`
- [x] ✅ [CODE] P2. **Diagnosed: naive per-repo scoping carries a live regression risk, NOT attempted — re-sequenced
      instead.** (2026-08-15, slot-20·infra) Empirically confirmed the obvious source for a per-repo `source_dir`
      (`workspace-manifest.json`'s `breaking_scan_dir`) is INCOMPLETE for at least e2e-testing (`"tests"` misses
      `scripts/`'s 144 `.py` files, several with landed `fix(...)` commits) — the same repo
      `detect_breaking_change.py`'s own docstring already cites as the reason full source-dir scoping was reverted after
      a 2026-08-09 false-negative incident (a real change going invisible to a scoped check silently clears a stall that
      should have stayed open, violating `_source_touched`'s own "fail toward alerting" design bias). Also confirmed
      live (not just docstring claim) that `detect_breaking_change.py`'s own `_source_touched` — not just
      reconcile_release_tags.py's copy — IS the actual semver-agent bump signal
      (`unified-trading-ci/.github/workflows/semver-agent.yml:612-626` reads its `source_touched` field to default-bump
      PATCH), so scoping only reconcile_release_tags.py's copy risks exactly the cross-script divergence the shared
      docstring warns against ("if you change one, change both"). Per CLAUDE.md's "AO-eligible = outcome determinable by
      the worker alone" rule, did not implement; re-sequenced the source issue doc's todo to gate on its sibling
      `[OPERATOR]` `breaking_scan_dir`-completeness audit landing first. Source:
      `plans/active/issues/ibkr_gateway_infra_release_tag_stall_2026_08_11.md` (updated with full diagnosis + Progress
      Log entry, same commit).
- [x] ✅ [CODE] P2. **MOOT — already captured live; the todo's own premise (a hand-curated `--instrument-ids` filter to
      edit) no longer exists.** (2026-08-15, slot-29·infra)
      `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh` carries its own 2026-08-14 stale-description
      correction (found + fixed by a peer session, re-verified live today): since 2026-06-23 the launcher is
      catalogue-mvp-driven with NO `--instrument-ids` — CeFi shards launch with `VM_INSTRUMENT_IDS` unset and MTDS
      resolves the per-venue capture universe from the IS catalogue via the shared `is_in_mvp_capture_universe`
      predicate (perp-gated). There is no hand-curated coin list left to edit. A bounded, column-projected read of the
      live IS catalogue (`instruments-store-cefi-prd-…/prod/catalog.parquet`) confirms all 10 named coins already have
      `mvp=True` PERPETUAL rows on 7-11 CeFi venues each (BINANCE-FUTURES/BYBIT/OKX-SWAP/
      KRAKEN-FUTURES/BITGET-FUTURES/COINBASE-FUTURES/… — all venues this launcher already iterates). A second bounded
      read of the live MTDS manifest (`market-data-tick-cefi-prd-…`, `derivative_ticker` rows only) confirms funding
      data is **already substantially captured** for every one of the 10 coins, not zero: WIF 16,857 captured rows
      (2023-01-01→2026-08-15, 10 venues), BONK 11,475, JUP 14,785, JTO 14,463, RENDER 10,758, FET 13,519, TAO 13,573,
      ORDI 18,963, STX 19,936 (back to 2021-01-01), LDO 21,175 (back to 2022-01-01) — each also carries a residual mix
      of `expected_unattempted`/`empty_confirmed`/`attempted_failed` rows, the normal honest-absence bookkeeping, not
      evidence of a gap. The 2026-06-17 "10 dataless coins" diagnosis was accurate **at the time** (pre-2026-06-23
      mechanism); the catalogue-mvp cutover + subsequent periodic backfill runs already closed it — no VM launch needed,
      nothing left to do here. Source: `plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md`
- [x] ✅ [CODE] P2. **STALE PREMISE — the "only ~9 coins" figure is ~2 months stale; the current OKX-SWAP
      derivative_ticker backfill universe + capture are healthy, no code bug found.** (2026-08-15, slot-20·infra) Two
      independent, bounded (single-object, column-projected) live checks against prod `central-element-323112`: (1)
      **Universe-resolution code** (`tardis_symbol_resolution._catalogue_symbols_for_venue_date`, the actual
      per-(venue,date) backfill-universe resolver `TardisAdapter._resolve_symbols` calls) reads the rolled-up CeFi
      lifecycle catalogue (`instruments-store-cefi-prd-…/prod/catalog.parquet`) with NO per-venue base-currency
      restriction — the MVP base universe (`CEFI_BASE_ASSET_UNIVERSE`, ~490 assets) is shared across every cefi venue,
      gated only by the generic mvp+perp-gate predicate. Live read: OKX-SWAP carries 667 catalogue PERPETUAL rows / 417
      distinct mvp base assets vs BINANCE-FUTURES' 929 rows / 592 distinct mvp bases — same order of magnitude, no
      OKX-specific universe cap in the resolver. (2) **Actual captured data** — a bounded, streamed (column-projected,
      `iter_batches`, no full-corpus load; wrapped under `run-bounded-analysis.sh`), read of
      `market-data-tick-cefi-prd-…/_index/availability_index.parquet` (29.4M rows) filtered to
      `data_type=derivative_ticker` + `date>=2026-01-01` found OKX-SWAP has **379 distinct base assets with
      `capture_status=captured` AND `row_count>0` in 2026** — vs BINANCE-FUTURES 603 and BYBIT 555 (same read). This
      directly contradicts the "~9 coins" premise (a >40x gap vs the actual current count) — the June observation was
      accurate at the time (the source doc's own coverage-window note: "funding to 2026-05-24") but the ongoing
      pipeline/backfill work since then closed the gap; no separate fix landed here, this is a fresh verification.
      **Content spot-check** (3 real captured OKX-SWAP + 1 BINANCE-FUTURES shard, read via the production
      `CanonicalParquetReader.read_shard(..., pipeline_mode="batch_tardis")`, same code path a live caller uses):
      `funding_rate` column present and >99.9% non-null in every sample (NEIRO-USDT 41172/41178, MOODENG-USDT
      90260/90269, ACE-USDT 43693/43693) — no captured-but-empty-funding defect either. **Verdict**: nothing to fix in
      MTDS's OKX-SWAP derivative_ticker backfill universe or capture path; closing as verified rather than filing a new
      finding. (Not touching the source doc per this batch's own convention — checkbox reconciliation back into source
      docs happens in the paired finalize plan.) Source:
      `plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md`
- [x] ✅ [CODE] P2. **NOT ATTEMPTED — premise unmet: the superseding job doesn't exist yet.** (2026-08-15,
      slot-21·infra) Confirmed live: `_write_agent_report()` is still present and called from `run_stage4()` in
      `batch_live_reconciliation_service/stages/stage4_agent_analysis.py` (writes `agent_report_{date}.md` to GCS, still
      read by nothing downstream — module docstring's dispatch/Slack claims remain stale, per this same source doc's
      §0). The source design doc's own §4 explicit decision gates this removal on "once the new [trading-analyst] job
      ships" — confirmed the job has NOT been built: no `agents/trading_analyst.md` role file, no `trading_analyst` mode
      in `plan_health.py`, no `install-trading-analyst-timer.sh`, zero fleet-wide matches for
      `trading_analyst`/`trading-analyst` outside this design doc itself. The source doc's own sibling todos ("Build the
      `trading-analyst` skill", "Wire the scheduling mechanics from §1") are still unchecked, confirming this directly.
      Per CLAUDE.md's "AO-eligible = outcome DETERMINABLE by the worker alone" rule + the doc's own explicit build-order
      (§4: this removal is a §5 follow-up gated on the new job shipping, NOT bundled into the job's own build), did not
      remove the write path — doing so now would delete Stage 4's only output before any replacement exists,
      contradicting the documented decision. No new issue doc filed: the gating work is already tracked as open todos in
      the same source doc; this removal should be re-picked-up once those ship. Source:
      `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md`
- [x] ✅ [INFRA] P3. Fixed `launch-cefi-onchain-forward-poll.sh`'s per-venue `VENUE_INSTRUMENTS`/`VENUE_DATA_TYPES`
      tables — deployment-service@02808f21c6 (2026-08-15, slot-29·infra). Re-pointed `VM_TASK` from
      `cefi-onchain-forward-poll` (no dedicated branch in `setup-data-pipeline-vm.sh` — fell through to the generic
      `--operation download` fallback, which does not thread `--data-types`/catalogue-driven `ALL` symbols for
      onchain-perp venues) to `mtds-backfill`, the only branch that detects membership in
      `umi_tick_provider.ONCHAIN_PERP_VENUE_CHAIN` + `VM_DATA_TYPES` set and routes to `collect-onchain-perp-batch`.
      Audited all 4 venues (not just EXTENDED-STARKNET): confirmed the SAME narrow-instrument-list gap on
      LIGHTER-ZKSYNC/HYPERLIQUID/ASTER too (each hardcoded to 2-5 coins vs. the live IS catalogue's ~200 mvp
      perpetuals) — set `VENUE_INSTRUMENTS=ALL` (the catalogue-driven sentinel, `_CATALOGUE_UNIVERSE_SENTINEL` in
      `_onchain_perp_batch_symbols.py`) for all 4. Corrected `VENUE_DATA_TYPES` to each venue's actual
      `onchain_perp_batch_handler.py`-documented capability set: dropped the dead `perp_funding` token everywhere
      (not a real `--onchain-perp-data-types` value for any of these venues — funding is embedded in
      `derivative_ticker`); LIGHTER-ZKSYNC is `derivative_ticker`-ONLY (trades/book are snapshot-only, excluded);
      EXTENDED-STARKNET/ASTER exclude `book_snapshot_5` (current-snapshot-only REST endpoint, no historical range);
      HYPERLIQUID keeps all 3 (`trades;book_snapshot_5;derivative_ticker`). Verified with `bash -n` +
      `--dry-run 2026-08-14 2026-08-14` (correct per-venue metadata assembly, singleton lock still works against
      live GCP state). `bash scripts/quality-gates.sh` green (311s, sentinel-verified at HEAD); quickmerge landed on
      LDR (first attempt's local timeout mid-push left the commit unpushed but intact; retried — post-push ancestry
      independently verified `02808f21c6` on `origin/live-defi-rollout`). Repo: deployment-service. Source: this
      doc's own 2026-08-15 diagnosis, folded in per the EXTENDED-STARKNET todo above.
- [ ] [CODE] P2. Step 3 cross-data_type completeness capture per venue_data_types.yaml Source:
      `plans/active/data_completion_to_100_all_ag_2026_06_21.md`

      **NOT ACTIONABLE 2026-08-15 (slot-5, infra craft) — mis-scoped for a single AO dispatch, re-scoping filed separately.**
      Investigated both halves: (1) the venue-specific completeness MEASUREMENT mechanism (`load_venue_data_types()` →
      `get_data_status_turbo_impl`, `service="market-tick-data-handler"`) already exists and is live — no code change needed
      — but a real corpus-wide query (`include_sub_dimensions=True`, all 5 asset groups, 30-day window) did not complete
      within a 120s budget, the same unbounded-read class `axis_value_census_mdps_scope_unbounded_read_hang_2026_08_15.md`
      already filed today for a sibling MDPS call. (2) The actual "capture" ask — backfilling every non-`trades` data_type
      per venue across all 5 asset groups — is an unbounded, multi-VM, multi-day operation, not a worker-determinable
      outcome for one ~1h dispatch. Filed `plans/active/issues/cross_cutting_data_type_completeness_capture_mis_scoped_ao_dispatch_2026_08_15.md`
      (P2, `assigned_vm: NA`) with the full investigation + a recommended sequencing (fix the unbounded-read class → run
      one real measurement pass → carve genuine gaps into properly-sized per-AG/per-venue bounded backfill todos) rather
      than re-attempting this umbrella-scoped todo as-is or absorbing an open-ended multi-AG backfill into this dispatch.

- [x] ✅ [CODE] P2. **STALE PREMISE — verified: no TVL-qualifying filter exists ANYWHERE by design, per an
      operator-directed decision already canonical elsewhere; no code change needed.** (2026-08-15, slot-17·infra) Full
      pipeline trace confirms: (1) MTDS's `DefiCatalogReader.list_instruments()`
      (`market_tick_data_service/engine/defi_catalog_reader.py`) reads the IS DeFi catalogue only for sentinel
      expected-universe enumeration (freshness/audit), filtering solely on venue + active-on-date window — it never
      reads the catalogue's `mvp` column. (2) MTDS's actual capture handlers
      (`cli/handlers/evm_defi_handler.py`/`solana_defi_handler.py`) drive their instrument universe from static
      per-adapter curated lists (e.g. `aave_lending.py:_filter_mvp_reserves()`'s hardcoded `mvp_tokens` set,
      `fluid_adapter.py:_get_mvp_markets()`), with only a catalogue-FRESHNESS preflight (`assert_defi_catalog_fresh`) —
      no per-instrument catalogue-driven filter. (3) IS's own `mvp` column for DeFi rows is a hardcoded `True` for every
      row (`instruments-service/scripts/build_instrument_catalogue.py` `_add_mvp_column()`, `asset_group == "defi"`
      branch) — **this is not a bug, it's the documented `defi_mvp_tag_all_2026_06_26` operator decision**, canonical
      SSOT `/codex/02-data/mvp-scope-canonical.md` § DeFi: "MVP-tag-all today... the production catalogue is wider [than
      UAC's `is_mvp` predicate], so `_add_mvp_column` short-circuits DeFi to all-MVP until a real per-instrument DeFi
      screen lands" — i.e. TVL-qualifying filtering for DeFi is EXPLICITLY DEFERRED future work, not a gap this
      1h-scoped todo should silently implement (would require designing + landing a new UAC `is_mvp` predicate for DeFi,
      the same class of judgment call CLAUDE.md's "AO-eligible = worker-determinable outcome" rule excludes). Nothing to
      verify-and-close as broken; the current tag-all design is intentional and already the SSOT of record. Source:
      `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [x] ✅ [CODE] P2. **All 3 sub-items verified: 2 already shipped by prior work, 1 residual gap closed here.**
      (2026-08-15, slot-16·infra) Live code verification of each named sub-item: (1) **record genuine zeros
      post-capture** — already comprehensively wired: `_dex_pools_subgraph.py`/`_dex_swaps_queries.py` call
      `DefiManifestRecorder.record_zero_rows` (launch-date-aware `SOURCE_RETURNED_ZERO`-with-`FetchEvidence`) and
      `record_catalogue_residual_empty` (`EXPECTED_NOT_ENOUGH_TVL`) in both dex handlers — the "FOUNDATION SHIPPED"
      state the source doc records. (2) **add missing subgraphs for TRADER_JOE_V2/UNISWAP_V4/ORCA/KAMINO/
      VELODROME_V2/RAYDIUM** — confirmed live in `dex_pools_handler.py`'s `_DEFAULT_PROTOCOLS` +
      `_dex_pools_subgraph.py`'s `fallbacks` cascade: `velodrome_v2`/`trader_joe_v2` both route via the shared
      `messari_basic` entry (`mtds_defi_dex_zero_capture_protocols_2026_07_14`), `uniswap_v4` has its own adapter +
      cascade entry, `kamino`/`orca`/`raydium` are live Solana AMM collectors in `solana_defi_amm.py` — all 6 named
      venues already covered, nothing to add. (3) **catalogue monotonicity check** — the monotonic->=-prev ASSERTION was
      already answered per this doc's own 2026-07-03 cross-ref (`evaluate_monotonic_guard` gates every daily promote);
      the residual CSV-distribution-report half was genuinely missing — added `instruments-service@0c057aad`
      (`scripts/report_defi_catalogue_distribution_2026_08_15.py`, read-only single- object bounded read, no corpus
      walk), run live against the prod DeFi catalogue: 78,447 rows / 134 distinct (venue,chain,data_type) groups,
      `available_from` 1970-01-01→2026-08-14, `available_to` 2021-01-01→2026-08-13 (11,758 still-active), monthly
      growth-over-time confirmed monotonically cumulative. **Also fixed a genuine pre-existing QG-red found while
      shipping** (unrelated to this todo, blocked the commit under the green-tree rule): 4 tests in
      `tests/unit/scripts/test_enumerate_expected_universe_v2.py` still asserted the pre-
      `tradfi_combo_casing_direction_ssot_contradiction_2026_08_03.md`-fix lowercase `"combo"` instrument_type where the
      shipped fix (`_canonical_writer_instrument_type`, "Fixed 2026-08-03" docstring) now correctly canonicalizes to
      uppercase `"COMBO"` — updated the 4 stale assertions (+docstrings) to match, fixed inline as a hotfix —
      `instruments-service@80d357bb`; `test_enumerate_expected_universe_v2.py` 240/240 pass; full `quality-gates.sh`
      green, sentinel-verified at HEAD `80d357bb`; both commits quickmerge-landed on LDR (post- push ancestry verified).
      Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [x] ✅ [CODE] P2. **PARTIAL — 11 of 53 verbose entries flipped to `active` on confirmed production wiring; the
      remainder genuinely require a broader per-repo investigation, not attempted here.** (2026-08-15, slot-5·infra)
      unified-trading-pm@(pending). Wiring criterion applied: (a) the failure mode's event has a REAL production call
      site constructing/routing a finding for it (not just a registry definition) AND (b) its DECLARED `escalation:`
      tier is the one that's actually operative — not a documented fallthrough. Confirmed via `PipelineFinding(event=…)`
      call sites in `deployment-service/deployment_service/data_pipeline_monitors/*.py` (the escalation hub) cross-
      referenced against `escalation.py`'s own docstring (only `CONSOLIDATOR_DOWN`/`DP_VM_EXIT_NONZERO`(oom)/
      `DP_VM_STALL`/`DP_VM_PREEMPTED` have wired `auto_recover` actuators; every other `auto_recover` tag falls through
      to `file_issue`) and the router's exact-match registration
      (`alerting-service/alerting_service/rules/ data_pipeline_rules.py`, built generically from the whole registry,
      so `file_issue`/`page_operator` tiers are structurally wired for any registered event — the real gate is whether a
      detector actually emits it in prod). Flipped (registry.yaml + the human-SSOT table in data-pipeline-alerts.md,
      kept in sync): DP-FETCH-007, DP-FETCH-009, DP-VM-001, DP-VM-002, DP-VM-003, DP-VM-004, DP-VM-007, DP-CATALOG-001,
      DP-WATCHER-001, DP-WATCHER-002, DP-WATCHER-004 — each has a confirmed `deployment-service` production call site
      AND its declared tier is genuinely operative (DP-VM-003's `auto_recover` → `relaunch_stalled_vm`, confirmed
      wired). Deliberately NOT flipped despite firing in prod: DP-RATE-001 (`DP_SOURCE_RATE_LIMITED`) —
      `escalation.py`'s own docstring names this the canonical example of an `auto_recover` tag with **no** wired
      actuator (falls through to `file_issue`), so flipping it would mischaracterize the declared tier as operative when
      it isn't. The other ~42 verbose entries (DP-FETCH-001..006/008, DP-COVERAGE-_, DP-PATH-_, DP-RATE-002/003,
      DP-ENV-_, DP-ORDER-_, DP-MANIFEST-002..005, DP-CATALOG-002, DP-WATCHER-003, DP-DIGEST-*) are mostly writer-side
      gates living in MTDS/instruments-service/ features-service/other repos this pass did not search, or LLM-judgment
      detectors — confirming each needs a per-repo call-site search beyond this single dispatch's scope; re-picking this
      up per-repo (not a single cross-cutting AO dispatch) is the natural next tranche. Source:
      `plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md`
- [x] ✅ [CODE] P2. **VERIFIED — both checkboxes already correctly flipped in their live successor doc; nothing stale to
      flip.** (2026-08-15, slot-4·infra) The archived `instruments_mtds_subset_consistency_remediation_2026_06_17.md` is
      a pure provenance-redirect table (its own body confirms every N-numbered finding's content migrated to
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`, L124-131) — so "instruments_mtds_subset"'s
      real current home for these items is that residuals doc, not the archived file. There: **N9c** is `[x]` ✅
      RESOLVED 2026-06-18 (verified `mtds@6b9f4b5` v9-column-population applied to all 5 AGs, independently re-confirmed
      for sports 2026-06-19) — matches current code, no contradiction. **N5r/N6r** is `[x]` ✅ EXTRACTED 2026-08-09 →
      `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`, where it is itself `[x]` ✅ (code sub-steps a+b
      shipped `market-tick-data-service@978a49fa`+`@8175ec7a`; remaining VM-only execution sub-steps c-e tracked
      separately in `plans/active/issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md`) — a legitimate
      extraction-closure, not a stale/self-contradictory state. Both checkboxes already match current code; no flip
      needed. (The sibling "migrate-first 4 AGs" / `instruments_catalogue_incremental_rollup` clauses of the source
      ADMIN todo are outside this batch todo's named scope — not checked here.) Source:
      `plans/active/instruments_completion_tracker_2026_07_06.md`
- [x] ✅ [CODE] P2. **Every other new-venue-add step was already wired; the one real gap was the
      `DEFI_VENUE_DATA_TYPE_CAPABILITIES` capability declaration — plus an interaction bug that surfaced fixing it.**
      unified-api-contracts@a0be68f9 + @4c95a3f2 (2026-08-15, slot-11·infra). Verified live: `COINBASE-ETHEREUM` was
      already in `ALL_DEFI_VENUES` + `DEFI_VENUE_PHASE` (both "live") + `DEFI_VENUE_LAUNCH_DATES` +
      `LST_VENUE_TO_TOKENS`/`LST_TOKEN_GENESIS["cbETH"]="2022-08-26"`, with a working MTDS adapter
      (`lst_coinbase_adapter.py`, emits the fully chain-qualified `venue="COINBASE-ETHEREUM"` directly — no
      `LEGACY_DEFI_VENUE_ALIASES` entry needed, and a bare `"COINBASE"` alias is deliberately NOT added per the todo's
      own caution: it would collide with the CeFi `COINBASE-SPOT` exchange) and an instruments-service reference-data
      adapter (`cbeth.py`). Added the missing `defi_venue_capabilities.py` entry —
      `"COINBASE-ETHEREUM": {"oracle_prices": "2022-08-26"}` (oracle_prices only: the adapter's `_default_data_types()`
      returns `["oracle_prices"]` only, `lst_rates_handler.py` has zero COINBASE wiring, so declaring `lst_rates` there
      would have inflated the could-exist denominator with a cell the code can't produce — DATA-001 precedent). That
      addition then surfaced a real, pre-existing interaction bug: `market_data_categories.py` already carries a
      2026-08-14-migration P1 override that REASSIGNS `VENUE_DATA_TYPE_CAPABILITIES["COINBASE-ETHEREUM"]` wholesale with
      a real MEASURED `lst_rates` capability (start `2022-02-05`, from actual captured manifest rows) — a bare
      reassignment there silently dropped my new `oracle_prices` record (caught by
      `test_batch_start_date_recoverable_one_for_one`, not a false-positive: pytest 1 failed / 13201 passed on the first
      full QG run). Fixed by merging the base-derived record's `data_types` into the override first, matching the
      sports-bookmaker-loop merge pattern already used a few lines above it in the same file. Full `quality-gates.sh`
      green (458s, sentinel-verified at HEAD `4c95a3f28e`); quickmerge landed on LDR (post-push ancestry verified
      `4c95a3f28` on `origin/live-defi-rollout`). Source:
      `plans/active/instruments_foundation_completeness_2026_06_24.md` (not touched — checkbox reconciliation happens in
      the paired finalize plan per this batch's own convention).
- [x] ✅ [CODE] P2. **Verified — catalogue leg CLEAN, cefi "equity-perp singles" CONFIRMED non-issue, but the manifest
      leg is NOT clean and re-opened a bigger finding than the June baseline.** (2026-08-15, slot-11·infra) Bounded live
      reads of `instruments-store-tradfi-prd-.../prod/catalog.parquet` (13MB) confirm zero `venue='ICE'` rows and zero
      `CBOE:INDEX:VIX*` rows — the original 91 SPOT_PAIR + 5 INDEX pollutants ARE gone from the catalogue. Cefi
      `is_equity_perp` (114-144 rows/venue across 15 venues) is a legitimate designed feature tag, not stray "singles" —
      confirmed no orphaned-single instances. But a bounded read of the MTDS tick-data manifest
      (`market-data-tick-tradfi-prd-.../_index/availability_index.parquet`, 367MB) found `source=databento`
      `capture_status=captured` rows for `venue=ICE` `futures_chain`/`ohlcv_1m` written **today** (2026-08-15
      06:17-06:25 UTC) by the live `market-tick-data-service` — despite every code comment (symbology.py,
      wave_launcher.py, expected_coverage.py) asserting ICE-via-databento is fully purged/"INTENTIONALLY ABSENT". Could
      not determine from the manifest alone whether this is a live re-fetch bug or a stale re-registration of pre-purge
      GCS objects — no live ICE dispatch code path found in `databento_adapter.py`/`venue_fetch.py` (grepped clean), so
      filed rather than guessed. Also found dormant (non-growing) manifest stragglers: 17 CBOE VIX-cash INDEX rows
      (existing purge scripts never fully cleared them) + 9,119 BARCHART rows (stale since 2026-07-07). Surfaces leg
      (catalogue/data-status/UI) not audited — out of this task's time budget. Full evidence + a concrete DIAG/OPERATOR
      follow-up todo list filed at
      `plans/active/issues/retirement_completeness_pollutant_reverify_ice_still_live_2026_08_15.md`. Source:
      `plans/active/instruments_foundation_completeness_2026_06_24.md`
- [x] ✅ [CODE] P2. **PARTIAL — defi+cefi consolidated into ONE parametrized script; tradfi/sports/prediction NOT
      mechanically generalisable, diagnosed + new follow-up todo filed below.** instruments-service@139fbfffba
      (2026-08-15, slot-9·infra). Replaced `scripts/defi_cumulative_drawdown_guard_2026_06_25.py` +
      `scripts/cefi_cumulative_drawdown_guard_2026_06_27.py` with a single
      `scripts/cumulative_drawdown_guard_2026_08_15.py` taking `--asset-group {defi,cefi}` (positional), preserving both
      scripts' day-over-day drop detection + cumulative-ever-seen (cummax) reporting, and additionally extending cefi's
      thin-day-collapse check (`--thin-frac`, default 0.5 of trailing 14-day median) to defi too (same formula,
      previously only implemented in the cefi copy). Updated the 2 live comment references (`venue_core.py`'s
      thin-day-collapse-convention comment, `canonicalize_defi_data_type_instrument_catalog_2026_07_16.py`'s
      read-side-filter citation) to point at the new script; grepped clean for any other reference to either deleted
      filename. **Did NOT extend to tradfi/sports/prediction — confirmed this is a design call, not a mechanical
      parametrization**: (1) tradfi has NO per-venue instruments-store bucket at all
      (`(AssetGroup.TRADFI, BucketKind.INSTRUMENTS): None` in
      `unified-api-contracts/unified_api_contracts/canonical/gcs_paths.py` — nothing to read); (2) sports/prediction's
      own orchestrators (`sports.py`/`prediction.py`) never write an `instrument_count`-shaped per-day series into their
      availability_index — sports' own catalogue read keys on `(date, service_name, data_type, league_id)`
      (fixtures/leagues), confirmed via a live grep of both files (0 hits for `instrument_count`/`cummax`/`monotonic`)
      and of `process_completeness.py`'s own thin-day helper, which explicitly skips any venue with no CeFi history.
      What the analogous per-day completeness series for a fixture/market catalogue even IS requires an operator/design
      decision this todo cannot resolve alone (per CLAUDE.md's "AO-eligible = outcome determinable by the worker alone"
      rule). Source: `plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md`
- [x] ✅ [CODE] P2. **Built the §2.3 ε=0 reconciliation guard (the narrower "QG step + watchdog" slice of the source
      doc's full 3-part item — UI-renders-SSOT and per-cell click-traceability are NOT in this batch todo's scope).**
      (2026-08-15, slot-16·infra) New audit script — e2e-testing@94fdeb0f60
      (`scripts/audit/drilldown_reconciliation_guard.py` + `tests/unit/test_drilldown_reconciliation_guard.py`):
      independently recomputes a BOUNDED, date-stratified sample of raw shard row_counts (never a whole-corpus walk) and
      asserts equality (ε=0) against the manifest's own recorded row_count for the SAME unambiguous (asset_group,
      data_type, date) captured cell — an ambiguous (e.g. multi-venue) or absent match is skipped, never guessed. Emits
      `DP_PHANTOM_ROWS` on drift, reusing the existing event per the DP-FETCH-009 precedent (a new
      `registry_id: DP-MANIFEST-006` in the alert details disambiguates from a true existence-phantom). 4 unit tests
      cover matching/no-finding, the DoD's own "a seeded manifest/raw divergence trips the guard" case, and the
      ambiguous-skip case — all green. **QG step**: wired into the existing lint+`--smoke` sweep at MTDS QG STEP 5.90
      (alongside the other 3 daily data-pipeline audits) — market-tick-data-service@3a24ab8e5d. **Watchdog**: scheduled
      daily 09:30 UTC via a new Cloud Run Job + Cloud Scheduler cron (Job 5, mirroring the existing 4) —
      deployment-service@3749eb6042. Registered `DP-MANIFEST-006` in the registry doc + `.registry.yaml`:
      unified-trading-pm (this commit). Full `bash scripts/quality-gates.sh` green on all 3 code repos (e2e-testing
      103s, deployment-service 363s, market-tick-data-service 427s), each sentinel-verified at its shipped HEAD; every
      commit's post-push ancestry verified on `origin/live-defi-rollout`. Source:
      `plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md`
- [x] ✅ [CODE] P2. **NOT (RE-)ATTEMPTED — premise stale, real remaining scope already tracked + gated in the correct
      issue doc.** (2026-08-15, slot-14·infra) This exact backfill was already dispatched + worked at length earlier
      today (data_engineering slot-2, 8+ checkpoints): a 500-row small-scale test on both surfaces looked correct, but
      scaling to the full run surfaced a real correctness bug (`_write_captured_rows()` dropped `timeframe=`,
      collapsing distinct `odds_horizon_bucket` rows into ~14,330 phantom blank-timeframe duplicates instead of
      superseding them) — the attempt was stopped immediately, both maintenance windows released, both crons resumed,
      no data destroyed. Full evidence + remaining-scope todos:
      `plans/active/issues/sports_cf8_captured_backfill_timeframe_dropped_2026_08_15.md`. The write-path fix is landed
      (`market-tick-data-service@e0b34e77fd`); the phantom-row cleanup + IS-surface check are still open; the
      re-attempt of THIS todo's own backfill is that doc's own todo #4, explicitly gated "once the fix + cleanup above
      are done" — cleanup is not done. Re-running now, before that gate clears, would repeat the exact
      premature-execution risk the prior session's own doc stopped to avoid on a surface with 2 prior real production
      regressions (`sports_cf8_available_at_backfill_regression_2026_07_13.md`) plus this 3rd near-miss. Per
      CLAUDE.md's "AO-eligible = outcome DETERMINABLE by the worker alone" + this craft's "never launch blind"
      north-star, did not execute; tracking stays on the issue doc's own todos rather than duplicated here. Source:
      `plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`
- [x] ✅ [CODE] P2. **Shutdown-wedge reaper watchdog shipped** — deployment-service@34bca6e6 (2026-08-15,
      slot-27·infra). `deployment_service/data_pipeline_monitors/shutdown_wedge.py`: detects a RUNNING VM whose last
      non-blank serial-console line is the systemd `Stopping <unit>...` job-start message with nothing logged after it
      (the exact signature the 2026-08-11 incident used to hand-classify 398 wedged VMs), tracks how long it has held
      that state via a GCS-persisted watch-state map, and reaps (tombstone + delete, reusing `reap_vms.py`'s
      tombstone-before-delete ordering so `exit_code_fleet_monitor` never misreads it as a preemption) once past a
      configurable grace period (default 30 min) — closing the "GCE still reports RUNNING with no automatic path to
      DELETE" gap this todo names. Pure detection/grace-period core is fully unit-tested (16 tests, DI'd GCE/GCS I/O,
      no live credentials needed);  `scripts/vm/reap_shutdown_wedged_vms.py` wires the real fleet (defaults to
      dry-run, `--apply` to actually reap). Uses subprocess `gcloud` for compute-instance list/serial-read (mirrors
      `reap_vms.py`'s existing convention in this script directory — no cloud-agnostic compute-instance wrapper
      exists yet, and the TID251 ratchet only bans NEW `google.cloud`/`boto3` SDK imports, not compute subprocess
      calls). `bash scripts/quality-gates.sh` green (0 basedpyright errors, TID251/empty-string-fallback ratchets
      held at baseline). Not yet wired into a live Cloud Scheduler cron — the exit-code monitor is deliberately PAUSED
      per this same source doc's standing operator hold, so a NEW auto-delete cron was deliberately left as an
      operator-invoked script rather than autonomous infra, consistent with the doc's own gating. Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [x] ✅ [CODE] P2. **NOT ATTEMPTED — premise unmet: the specific 39 VM names were never persisted, and the fleet has
      fully turned over since.** (2026-08-15, slot-22·infra) The source doc's remediation sessions saved name lists for
      every VM it acted ON (`reaped_vms_2026_08_11.txt`, `reaped_duplicate_year_shards_2026_08_11.txt`), but the 39
      "probe inconclusive" VMs were classified and left alone — no list of which 39 they were was ever written anywhere
      (checked `plans/active/issues/vm_reap_lists/`: only the two reap lists exist, no third file). Without that name
      list there is nothing to re-probe. Live fleet check confirms re-deriving it isn't viable either: the project now
      runs 88 instances total (`gcloud compute instances list --project=central-element-323112`), all but 2 launched
      2026-08-13 or later — only `mdps-cefi-2025-20260811-212851` and `betfair-egress-proxy-20260811-211046` survive
      from the 2026-08-11 wedge window, and neither can be confirmed as a member of the original 39 (that membership was
      never recorded). Per CLAUDE.md's "AO-eligible = outcome DETERMINABLE by the worker alone" rule, did not
      fabricate a probe target list. No code change; the tool
      (`deployment-service/scripts/vm/probe_vm_serial_liveness.sh`) is still in place for a future incident with a
      preserved name list. Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
