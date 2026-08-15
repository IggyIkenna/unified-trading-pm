---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 13 — 2026-08-13
summary: >-
  Extraction batch from the cross-cutting tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep —
  89 conflict-cleared, bounded/deterministic items pulled directly from 39 source docs (RECLASSIFY_SPLIT bounded items
  from the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each
  todo cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation
  back into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related: [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/alert_driven_dependency_revocation_2026_08_12.md,
    /plans/active/bucket_estate_consolidation_closeout_2026_07_24.md,
    /plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/active/cross_cutting_strategy_execution_determinism_2026_07_26.md,
    /plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md,
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /plans/active/data_source_provenance_enforcement_2026_07_24.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md,
    /plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md,
    /plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md,
    # + 24 more source docs cited per-todo below
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 13.3
estimate_calibrated_ai_days: 10.7
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# cross-cutting satellite AO dispatch batch 13 — 2026-08-13

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] ✅ [INFRA] P2. enumerate every live Cloud Run service's actual runtime SA + role set into the registry (bounded
      audit) — deployment-service@f5ad937bee (2026-08-13 full read-only audit: 25 live Cloud Run rows / 23 distinct
      services across 9 runtime SAs enumerated into `live_runtime_bindings` + `live_runtime_sa_roles` sections; YAML
      validated; QG green; quickmerge landed on LDR) Source:
      `plans/active/issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`
- [ ] [INFRA] P3. document which live services rely on the default-compute-SA and what secrets/buckets they can
      therefore reach (bounded documentation task) Source:
      `plans/active/issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`
- [x] ✅ [DIAG] P2. verify the exact CME instrument_id string format for FUTURE contracts against the live catalogue
      before implementing tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md's already-ruled fix —
      unified-trading-pm@db37be4e4b (2026-08-14: confirmed `CME:FUTURE:<PRODUCT_ROOT>-USD@LIN-YYYYMMDD` via 3 convergent
      code sites + a bounded live read of `prod/catalog.parquet`; recorded in both the source issue doc and
      `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`'s todo 1) Source:
      `plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md`
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
- [ ] [CODE] P3. Make `quickmerge.sh`'s STAGE 3 re-gate contention-vs-content guard (`_qm_other_fail`, ~L2463-2464) also
      exclude ❌ lines produced by `CODEX_MAX_VIOLATIONS`-tolerated checks — currently it only excludes the
      duration-budget line, so a run that warns-but-passes the codex-compliance tolerance check (prints its per-STEP
      `log_fail()` ❌ lines regardless) but fails purely on the independent duration hard-gate still gets misclassified
      as "a REAL failure" instead of "HOST CONTENTION, not your change" (repro case: strategy-service 2026-08-10, see
      the diagnosis todo above). Fix: additionally check the re-gate log's own final verdict line
      (`✅ ALL QUALITY GATES PASSED` / `⚠️ Codex compliance: N violations (within tolerance...)` vs
      `Codex compliance FAILED` / `Quality gates FAILED: N hard gate...`) rather than raw-grepping intermediate ❌ lines
      alone. Repo: unified-trading-pm. Source:
      `plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md` (new
      finding, 2026-08-14 diagnosis)
- [x] ✅ [CODE] P2. Split the remaining MTDS >900L files + extract oversized fns/methods —
      market-tick-data-service@21b2f7193a (2026-08-15, slot-30·infra). 0 files >900L already (prior wave); the real
      remaining scope was the 10 `FUNCTION_SIZE_EXTRA_EXCLUDES` files each carrying 1-2 methods 51-101L — extracted 15
      methods into private helper methods (all ≤50L, mechanical/behaviour-preserving) across bridge/flash_loan/
      governance/liquidation/mev/staking_yields/token_transfers handlers + databento_batch_jobs/
      alchemy_transfers_client/thegraph_base_client, then deleted the now-empty exclude list. Full `quality-gates.sh`
      exit 0 (sentinel-verified at HEAD). Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [x] ✅ [CODE] P2. Re-add 17 connector reconnect tests using terminating mocks (market-tick-data-service) —
      market-tick-data-service@26eef1999f (2026-08-15, slot-21·infra). No git-history evidence of a literal "def
      test_...reconnect..." deletion survived (full non-shallow history search, zero hits) — instead cross-referenced
      the 25 connectors that got the zero-delay-reconnect tight-loop fix (`cec16b74`) against which test files already
      exercise the reconnect loop with a TERMINATING mock (`reconnect_base_delay_s`/ `_ws_connect_side_effect` markers):
      9 already covered (incl. `deribit_book_ticker_ws` — the doc's own reference pattern), 16 gaps found — reconciles
      to the doc's "17" (the deribit reference + these 16). Added one `test_stream_connect_failure_retries` per gap
      (aster liquidations, binance-futures, bitfinex-spot, bitget-spot, bybit-futures, coinbase-cde, coinbase-spot,
      deribit-trades, hyperliquid l2book/ticker/trades, kraken futures/spot, okx-swap, tardis-machine, upbit-book) —
      each injects a mock `_http_session` whose `ws_connect` raises `aiohttp.ClientError` and flips `conn._closed` on
      the 3rd attempt, mirroring `test_deribit_book_ticker_ws_coverage.py`'s existing terminating-mock pattern rather
      than a never-closing one. QG green (`✅ ALL QUALITY GATES PASSED`, 489s, sentinel-verified); quickmerge landed on
      LDR (post-push ancestry verified). Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
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
      `git cat-file -e     origin/live-defi-rollout:openapi/ui-reference-data.json` → absent, as intended).
      `openapi/capability-manifest.json` is NOT safe to untrack as-is:
      `agent-orchestrator/server/mcp/manifest_loader.py` hard-requires it be a **committed** file in this repo's sibling
      clone (`_MANIFEST_REL`, `manifest_path()`; raises `ManifestUnavailableError` with no regen fallback if absent) —
      untracking it would break AO's capability MCP server on any fresh clone. Filed as a new followup todo below rather
      than silently skipped. Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [ ] [CODE] P3. **New finding, 2026-08-15**: before `openapi/capability-manifest.json` can be untracked per the
      generated-artifact-churn cleanup above, fix `agent-orchestrator/server/mcp/manifest_loader.py`'s hard dependency
      on it being a committed file (`_MANIFEST_REL = "unified-api-contracts/openapi/capability-manifest.json"`,
      `ManifestUnavailableError` on missing, no regen path) — either wire a regen-on-demand fallback (invoke
      `unified-trading-pm/scripts/openapi/generate_capability_manifest.py` when the committed copy is absent) or accept
      the file staying committed permanently and close this out as won't-do. Repo: agent-orchestrator +
      unified-api-contracts. Source: this doc, todo above.
- [x] ✅ [CODE] P2. **Ran PM `bash scripts/quality-gates.sh` — initially FAILED, root-caused + fixed, now confirmed
      green.** (2026-08-15, slot-12·infra) First run surfaced a real regression, not a stale/pre-existing red:
      `test_f47_unbuildable_venue_cells_are_not_available` failed with 18 unbuildable cells, all tracing to one venue
      (`pacifica_solana`). Root cause: the same-day 2026-08-15 "containment fix" to `archetype_leg_spec_seeds.py` added
      `"pacifica_solana"` to 3 `eligible_venue_ids` lists, reasoning from a hyphen→underscore fold of
      `catalog_carry.py`'s `full_venue="PACIFICA-SOLANA"` string — but the slot-label parser's alnum-fold
      (`_slot_venue_token`, full alnum-strip) turns that into `"pacificasolana"`, which never matches
      `KNOWN_VENUE_TOKENS`'s existing `"pacifica"` entry. The bundle's actual slot-label token (per
      `_CARRY_BASIS_PERP_VENUE_BUNDLES`'s own `("pacifica", "PACIFICA-SOLANA", ...)` row and `test_target_universe.py`'s
      live slot-label assertions) is `"pacifica"` — corrected all 3 sites to match. Fixed + shipped
      `unified-api-contracts@826763229f`; UAC's own `quality-gates.sh` green (429s, sentinel-verified); re-ran PM's full
      `quality-gates.sh` after the fix landed — `✅ ALL QUALITY GATES PASSED`, sentinel `.qg_last_passed_sha` verified
      == HEAD `8b7e53a624`. Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
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
- [x] ✅ [CODE] P2. **Fixed via the live instrument_id format, not the guessed `CME:FUTURE:ESM5` shape.**
      deployment-service@8e22704756 (2026-08-15, slot-30·infra). A bounded, column-projected read of the live
      `market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` manifest against the exact
      110,074-row bucket (venue=CME, data_type in {ohlcv_1s,ohlcv_1m}, error_reason=WithinBoundsTradfiSourceZero, blank
      `underlying`) confirmed every row's `instrument_id` is actually `<ROOT>.FUT` / `<ROOT>.OPT` (e.g. `CT.FUT`,
      `MNQ.OPT`) — not the contract-symbol form (`CME:FUTURE:ESM5`) the function's old docstring guessed at. Rewrote
      `_derive_cme_root()` to fall back to parsing that suffix when `underlying` is blank, so these rows now resolve a
      real root and re-enter `compute_dispatch_candidates()`'s gap computation instead of permanently bucketing into
      `out_of_scope["CME:unmapped_root"]`. Added `tests/unit/test_wave_launcher_cme_root_fallback.py` (6 cases:
      populated-underlying precedence, COMBO→None, FUT/OPT suffix fallback, unparseable-instrument_id→None, both-blank→
      None). `bash scripts/quality-gates.sh` green (799s, sentinel-verified at HEAD); quickmerge landed on LDR
      (post-push ancestry verified `8e22704756` on `origin/live-defi-rollout`). Source: this doc's own 2026-08-15
      diagnosis, folded in per the tradfi attempted_failed retry todo above.
- [ ] [INFRA] P3. disambiguate 'the planning VM' in monitoring/docs; always name the instance ID or a stable label
      Source: `plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`
- [ ] [INFRA] P3. wire an automated deploy/sync for glue-runner-crash-loop-watchdog.sh so a repo fix reaches the host
      Source: `plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`
- [ ] [BACKEND] P2. document the circular-dependency gap (scheduled workflow runs from default branch) in ci-cd-flow.md
      Source: `plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md`
- [ ] [BACKEND] P2. sweep the fleet for the same 'set -uo pipefail' + RC=$? -e trap via the given rg command Source:
      `plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md`
- [ ] [BACKEND] P2. add a meta-assertion that any job publishing a notify-consumed verdict output emits it on the
      failure path too Source:
      `plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md`
- [x] ✅ [CODE] P2. Pass --build-arg
      SETUPTOOLS_SCM_PRETEND_VERSION=$$VERSION in strategy-service and greeks-service
      cloudbuild.yaml once each repo's own blocking issue clears — strategy-service@b569635c28 +
      greeks-service@d4b796dfd5 (2026-08-15, slot-12·infra). Both prior blockers were already clear: strategy-service's
      own QG is not red at LDR tip (confirmed by an earlier todo in this same batch); greeks-service's git status is
      clean (no peer WIP conflict). Added `--build-arg SETUPTOOLS_SCM_PRETEND_VERSION=$$VERSION`to the`build`step's    `docker
      build`in both`cloudbuild.yaml`files, matching the fleet pattern already used in     agent-orchestrator/deployment-service/alerting-service/features-service. QG green + sentinel-verified on both     repos; both quickmerge-landed on LDR (post-push ancestry verified). Source:    `plans/active/issues/mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md`
- [x] ✅ [CODE] P2. Re-run hosted-baseline.sh to resync the derived cloud-build-router.yml snapshot with the live
      workflow — unified-trading-pm@f7fb62f580 (2026-08-15: `hosted-baseline.sh snapshot` re-run; the `derived`
      `cloud-build-router.yml` baseline now reflects the 2026-08-10 `build_error_detail` credential-scrub fix landed in
      the live workflow — MANIFEST row re-stamped at current HEAD. The script resyncs the whole fleet by design, so 25
      other drifted baselines were refreshed as a byproduct; residual `verify` warnings for
      `glue-pool-starvation-monitor.yml` (grep false-positive matching a historical-context comment, not a real
      `runs-on:`), `ldr-docs-gate.yml` (born self-hosted, no rehost overlay), and 3 pre-existing `history-logic-stale`
      baselines (`ldr-to-main-promote.yml`, `staging-to-main.yml`, `reconcile-staging-versions.yml`) are unrelated
      pre-existing conditions, unchanged by this run — out of scope for this bounded todo.) Source:
      `plans/active/issues/mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md`
- [x] ✅ [DATA] P1. **MOOT — already deleted, confirmed live (2026-08-13, slot 29).** This todo's premise (run a fresh
      retention check, then delete) was stale: the source doc's own 2026-08-12 docs-drift note records that
      `ml-models-store` was already deleted 2026-08-08 (operator-authorized) via the sibling plan
      `bucket_fold_ml_2026_07_17.md`'s "Delete sources" todo — this batch's extraction just hadn't picked that up. Fresh
      live re-verification this session (not just trusting the note):
      `gcloud asset search-all-resources     --scope=projects/central-element-323112 --query="name:ml-" --asset-types="storage.googleapis.com/Bucket"`
      returns only `ml-store-test-central-element-323112` and `ml-store-prd-central-element-323112` (the folded
      canonical buckets) — zero hits for `ml-models-store`, confirming the flat legacy bucket is gone. Dead
      TF/yaml-reference half also re-confirmed clean: fresh
      `grep -rn "ml-models-store\b" deployment-service/terraform deployment-service/configs deployment-api     unified-api-contracts`
      across all 4 repos returns only comments/docstrings describing the already-executed fold (`outputs.tf`,
      `_core.py`, a test docstring, `_ml_training_contract.py`) — no live resource declarations or resolver calls. No
      retention check or delete action was needed or taken. Source:
      `plans/active/bucket_estate_consolidation_closeout_2026_07_24.md`
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
- [x] ✅ [CODE] P2. Make claim/heartbeat behaviour under test injectable so the common cases can be covered without a
      real tmux server, per the doc's own P2 [SCRIPT] todo — unified-trading-pm@ef78ddc842 (2026-08-15, slot-12·infra).
      Factored `refresh_agent_claim_heartbeat()`'s inline `tmux has-session` check in
      `scripts/dev/slot-git-status-report.sh` into its own `_claim_heartbeat_session_alive()` function; the bats suite
      now redefines that function after sourcing to cover the "alive"/"dead" cases with NO real tmux server spawned.
      Only the exact-match-collision test still uses a real tmux session (it exists specifically to prove tmux's own
      `-t "="` exact-match semantics) — tagged `# bats test_tags=integration,tmux` so it's selectable via
      `bats --filter-tags` even though the fleet's current bats invocation doesn't filter. All 5 tests green locally.
      Source: `plans/active/issues/pm_bats_tmux_fixture_leak_wedges_shared_host_2026_08_10.md`
- [ ] [CODE] P2. Implement the schema/NaN contract in e2e-testing/scripts/validation/validate_shards_4pillar.py per the
      operator-ruled spec (wire _TICK_REQUIRED, add tick to _NAN_SCAN_COLUMNS, wire _DEFI_REQUIRED/_SPORTS_REQUIRED
      narrowly) Source: `plans/active/issues/silent_wrong_answer_audit_untracked_followups_2026_07_28.md`
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
- [ ] [CODE] P2. OKX-SWAP perp funding sparse (only ~9 coins captured in 2026 vs expected ~19+) -- verify the OKX
      derivative_ticker backfill universe in MTDS. Source:
      `plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md`
- [x] ✅ [CODE] P2. **STALE PREMISE, CONFIRMED — duplicate of an already-resolved source-doc item, no fix needed.**
      (2026-08-15, slot-10·infra) The source doc's own item (`citadel_paper_batch_live_reconciliation_2026_06_19.md`
      P9.2) was already re-verified + closed on 2026-08-14: the cited UAC `0.26.0`/`0.27.0` blocking pairing no longer
      exists. Fresh live re-run this session of
      `bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh` (check-only, PM already fresh-pulled to
      `origin/live-defi-rollout`) confirms the same result: **"OK: All dependencies aligned with manifest and canonical
      constraints." / "Alignment OK."** — strategy-service's QG-preflight version-alignment gate is not blocked. `--fix`
      was not run: the two currently-open conditions the check surfaces (fleet-wide `uv.lock` drift across ~18 repos, PM
      self-version drift `pyproject=1.2.596` vs `manifest=1.2.741`, and a 21-repo local-vs-`origin/main`
      `staging_versions` lag) are the SAME pre-existing, separately-tracked, out-of-scope conditions the source doc's
      2026-08-14 re-verification already identified — none is the strategy-service-blocking pairing this todo cites, and
      `--fix` would touch ~20 unrelated repos outside this todo's scope. Source:
      `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md`
- [x] ✅ [CODE] P2. Phase 1c: wire the drain registry into MTDS/MDPS/instruments-service/features-service backfill
      entrypoints. **STALE DUPLICATE, closed 2026-08-14** — this specific Phase-1 item shipped; Phase 1 landed
      `unified-trading-library@2aacde1359` (structural fix, not a 4-repo edit — see the plan's Phase 1 todo 9).
      **CORRECTION 2026-08-14 (cicd/plan_health):** the source plan was un-archived the same day (13 other todos remain
      open incl. 4 P0s — mechanism never actually fires in prod) — this Phase-1 item itself is still shipped and
      correctly closed here, only the "archived" framing was stale. Source:
      `plans/active/alert_driven_dependency_revocation_2026_08_12.md`.
- [x] ✅ [CODE] P2. Phase 1: add the flush-contract doc to spot-vms-for-backfill.md. **STALE DUPLICATE, closed
      2026-08-14** — landed same commit as above. Source:
      `plans/active/alert_driven_dependency_revocation_2026_08_12.md`.
- [x] ✅ [CODE] P2. Phase 2: add DependentAction StrEnum + evaluate_revocation() + alert-action map to UAC. **STALE
      DUPLICATE, closed 2026-08-14** — landed `unified-api-contracts@c206f910` (all 7 todos). Source:
      `plans/active/alert_driven_dependency_revocation_2026_08_12.md`.
- [x] ✅ [CODE] P2. Phase 3: add RetryBudget/RETRY_BUDGETS registry to UAC with the documented default ladder. **STALE
      DUPLICATE, closed 2026-08-14** — landed `unified-api-contracts@c206f910` + `instruments-service@1ae4b7d0` +
      `market-tick-data-service@554adf49` (all 8 todos). Source:
      `plans/active/alert_driven_dependency_revocation_2026_08_12.md`.
- [x] ✅ [CODE] P2. Phase 4: add the push actuator in deployment-service that consults evaluate_revocation() with no
      policy branch of its own. **STALE DUPLICATE, closed 2026-08-14** — landed `deployment-service@e38b2a0e` +
      `@67e3b36c` (all 9 todos). Source: `plans/active/alert_driven_dependency_revocation_2026_08_12.md`.
- [x] ✅ [CODE] P2. Phase 5: add the VM-side drain-marker poll hook and Cloud Run admission-check skip gate. **STALE
      DUPLICATE, closed 2026-08-14** — landed `deployment-service@67e3b36c` + `deployment-api@0d3f1cc` +
      `unified-trading-library@ad29bd9f` (all 8 todos). Source:
      `plans/active/alert_driven_dependency_revocation_2026_08_12.md`.
- [ ] [CODE] P2. Remove BLRS Stage 4's _write_agent_report() write path once superseded Source:
      `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md`
- [ ] [CODE] P2. File the dead-mode-kwarg bug (execution_fills/positions/strategy_instructions/pnl_attribution all
      silently drop a mode= path placeholder) as its own issue doc Source:
      `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md`
- [ ] [CODE] P2. Fix the stale scheduled-jobs table in agent-orchestrator-single-vm-architecture.md
      (opus/01:00-UTC-daily -> sonnet/hourly-retry) Source:
      `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md`
- [ ] [CODE] P2. Launch the now-unblocked EXTENDED-STARKNET instrument-catalogue + perp backfill
      (candles/funding/orderbook/trades) Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. Step 2 IS-store backfill for Kraken/LIGHTER/PACIFICA/EXTENDED/BITGET gap-days so MTDS<->IS subsets
      close both ways Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. Step 3 cross-data_type completeness capture per venue_data_types.yaml Source:
      `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. Verify/implement the DeFi catalogue MVP filter (MTDS reading IS catalogue as TVL-qualifying filter)
      Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. DeFi honest-absence residual-tail fixes: record genuine zeros post-capture, add missing subgraphs,
      catalogue monotonicity check Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. DeFi swallow-fixes (CF-11 class) in DefiManifestRecorder pass-through, liquidations_handler.py,
      polymarket_adapter Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. Restore the dex_swaps_handler.py adapter-contract QG-5.70 baseline Source:
      `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. Flip data-pipeline-alerts.registry.yaml modes verbose->active as each escalation tier is confirmed
      wired Source: `plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md`
- [ ] [CODE] P2. (stretch) Persist full launch-spec CLI args into DeploymentRegistryEntry for exact-replay relaunch
      Source: `plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md`
- [ ] [CODE] P2. Wire the generalised extra='forbid'-style source-required checker into MTDS + MDPS quality-gates.sh
      Source: `plans/active/data_source_provenance_enforcement_2026_07_24.md`
- [ ] [CODE] P2. Run scripts/quality_gates/audit_source_column_distribution.py against prod post-backfill and report the
      per-cell source histogram Source: `plans/active/data_source_provenance_enforcement_2026_07_24.md`
- [ ] [CODE] P2. Update codex + audit instructions to the universal source-provenance rule Source:
      `plans/active/data_source_provenance_enforcement_2026_07_24.md`
- [ ] [CODE] P2. Flip the named stale/self-contradictory checkboxes (instruments_mtds_subset: N9c, N5r/N6r) once
      verified against current code Source: `plans/active/instruments_completion_tracker_2026_07_06.md`
- [ ] [CODE] P2. Add cbETH as COINBASE-ETHEREUM to the DeFi LST universe (full new-venue registration) Source:
      `plans/active/instruments_foundation_completeness_2026_06_24.md`
- [ ] [CODE] P2. Retirement completeness (§8) sweep -- verify every named pollutant (tradfi ICE/CBOE/VIX-cash,
      cefi-domain equity-perp singles) is absent on all 4 legs Source:
      `plans/active/instruments_foundation_completeness_2026_06_24.md`
- [ ] [CODE] P2. Generalise the cumulative-drawdown health metric from the 2 existing per-AG scripts (defi, cefi) to a
      single cross-AG metric covering tradfi/sports/prediction Source:
      `plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md`
- [ ] [CODE] P2. Build the consolidation-reconcile script (actual shards vs materialised expected-universe, scoped
      --force after backfill) Source: `plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md`
- [ ] [CODE] P2. Build the drilldown-correctness ep=0 reconciliation guard as a QG step + watchdog Source:
      `plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md`
- [ ] [CODE] P2. Fix canonicalize_instruments_store_index.py's _bucket_for to resolve the prediction instruments-store
      bucket (currently a dead --asset-group prediction path) Source:
      `plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md`
- [ ] [CODE] P2. Investigate the systemic schema-drift dup (16% of shards with >1 manifest row) and fix writer-side
      row-key idempotency Source: `plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md`
- [ ] [CODE] P2. G1.run-prediction: run enumerate_expected_universe.py v2 at the cqg-bundle grain now that the IS
      catalogue-rollup loader wiring has landed (prediction_cqg_residual_2026_07_24.md is archived complete) Source:
      `plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md`
- [ ] [CODE] P2. add a git fetch+rebase step to each plan_health-family scheduled skill's STEP 0 (fixes the PM-checkout
      staleness gap the 2026-08-03 audit re-confirmed live) Source:
      `plans/active/issues/ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md`
- [ ] [CODE] P2. re-run /plan-reconcile whole-corpus SOLO to record a clean, unconfounded benchmark number Source:
      `plans/active/issues/ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md`
- [ ] [CODE] P2. apply the established ParallelPerSymbolRunner asyncio.gather+Semaphore pattern to the 8 remaining
      serial DeFi CLI handlers (dex_swaps_handler.py, evm_defi_collectors.py, gas_fee_handler.py, lst_rates_handler.py,
      liquidations_handler.py, liquidation_events_handler.py, vault_share_price_handler.py,
      eigenlayer_rewards_handler.py), verifying async-caller/ordering/line-cap per site Source:
      `plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md`
- [ ] [CODE] P2. fix the 2 blocking-write sites in sync functions (websocket_runner.py::_record_empty_window,
      live_aggregator.py::_handle_zero_tick_window) by dispatching the write via a dedicated executor, per the same
      pattern already shipped for the async sites Source:
      `plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md`
- [ ] [CODE] P2. confirm via migration_orphan_sweep.py/cefi-dedup-apply/cefi-content-apply run history or manifest
      history whether the cefi legacy-duplicate corpus is genuinely already gone, then flip the original checkbox in
      cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md citing this doc's todo-3 evidence Source:
      `plans/active/issues/cefi_legacy_dup_delete_tooling_gap_2026_08_09.md`
- [ ] [CODE] P2. execute the operator-approved sports CF-8 targeted backfill
      (market-tick-data-service/scripts/sports_captured_available_at_targeted_backfill_2026_07_14.py) plus the bundled
      CF-3/CF-4 legacy-row cleanup on instruments-store-sports-prd/market-data-tick-sports-prd, per the doc's own
      lease/snapshot/small-scale-first/verify/scale execution notes Source:
      `plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`
- [ ] [CODE] P2. add --no-renames to the 4 git show call sites in agent-orchestrator/server/verify.py (~lines 890, 936,
      976, 1028) per the operator-decided option-B fix, plus a regression test pinning bundled-rename+flip detection
      (per task_template.md finding U, a named-file content-level fix, no further design call needed) Source:
      `plans/active/issues/checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md`
- [ ] [CODE] P2. author the implementation plan for the 2026-08-12-ruled local-ratchet-gate-breach escalation detector
      (new wall type in agent-orchestrator/server/escalation.py, 15-minute delayed LDR re-check before dispatch,
      AO-driven remediation that restores the breached ratchet/baseline) after confirming AO-dispatched-vs-human-plan
      routing with the operator Source:
      `plans/active/issues/ci_escalation_no_coverage_for_local_ratchet_gate_breaches_2026_08_10.md`
- [ ] [CODE] P2. Add AO wall_type for Cloud Build failures (agent-orchestrator/server/escalation.py WALL_TYPES, mirror
      main_ci_red routing) Source: `plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md`
- [ ] [CODE] P2. Add AO wall_type for main-backmerge-to-ldr sync failures (same escalation.py mechanism) Source:
      `plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md`
- [ ] [CODE] P2. Fix the 7 failing github-glue-slot-refresh-* systemd units on host i-042a6332509482556 (git-credential
      error on mirror-refresh side-timer) Source: `plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md`
- [x] [CODE] P2. ✅ Live-verify (or synthetically force) the cloud-build-failure-watcher's coverage-gap self-check
      actually pages CRITICAL when a pool's oldest fetched build is newer than the lookback cutoff Source:
      `plans/archive/2026_08/issues/cloud_build_failure_watcher_limit_30_coverage_gap_silently_drops_failures_under_load_2026_08_10.md`
      — already done directly against the source issue (unified-trading-pm, this commit): synthetic/forced test of the
      extracted self-check logic against fabricated gap/no-gap Cloud Build JSON fixtures confirmed `alert=true` + the
      `COVERAGE GAP` message fires on a genuine gap and stays silent when coverage is adequate. Duplicate of this
      batch's copy; no separate dispatch needed.
- [x] [CODE] P2. ✅ Add duration floor (N consecutive failed probes AND outage >= expected_recovery_time_seconds) to
      evaluate_dependency_health's no-fallback branch before any producer is wired Source:
      `plans/archive/2026_08/issues/dependency_health_alerting_never_wired_2026_08_12.md` — already shipped directly
      against the source issue: `alerting-service@324ffa5`. Duplicate of this batch's copy; no separate dispatch needed.
- [x] [CODE] P2. ✅ Build the probe-driven producer + wire the *_event_handler.py subscriber into alerting-service's
      subscribers/alert_subscriber.py Source:
      `plans/archive/2026_08/issues/dependency_health_alerting_never_wired_2026_08_12.md` — already shipped directly
      against the source issue: `alerting-service@42347de`. Duplicate of this batch's copy.
- [x] [CODE] P2. ✅ Add an integration test that drives a simulated outage from the producer's entry point and asserts a
      routed alert Source: `plans/archive/2026_08/issues/dependency_health_alerting_never_wired_2026_08_12.md` — already
      shipped directly against the source issue: `alerting-service@7291bee`. Duplicate of this batch's copy.
- [x] [CODE] P2. ✅ Add a status line to /codex/04-architecture/dependency-health-policy.md stating the feature is
      contract-and-config only until wired Source:
      `plans/archive/2026_08/issues/dependency_health_alerting_never_wired_2026_08_12.md` — superseded: by the time this
      landed the feature was actually wired (2026-08-13), so the doc was brought CURRENT instead (added a "Status —
      WIRED end-to-end" section citing the real shipped commits) rather than caveated as not-live — same
      `unified-trading-pm` commit as this checkbox flip. Duplicate of this batch's copy.
- [ ] [CODE] P2. Bisect test_dp_recovery_actuators.py's full-suite contamination against predecessor test files
      (candidates: _\_relaunch_/fleet-monitor/dp-alerts suites; regression window b501a5e5, b34e85a2, 4ca051ea,
      dd7b62e1), find the shared-state leak, add cleanup Source:
      `plans/active/issues/deployment_service_qg_red_11_actuator_tests_suite_order_regression_2026_08_10.md`
- [ ] [CODE] P2. Confirm via Cloud Logging how far back the exit-code-monitor OOM recurrence goes (single blip vs
      sustained) Source: `plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md`
- [ ] [CODE] P2. Bump cpu/memory on data_pipeline_exit_code_monitor_job in
      terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf (mirror heartbeat-watcher precedent) -- may already be done
      live per the sibling sweep-overlap-storm doc, unconfirmed here Source:
      `plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md`
- [ ] [CODE] P2. Live-verify vm-census/exit-code-last-run.json advances on schedule for 3+ consecutive cycles post-fix
      with no further signal-9 entries Source: `plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md`
- [ ] [CODE] P2. Cross-check #data-pipeline-alerts for DP_CRON_DID_NOT_FIRE::vm-census/exit-code-last-run.json during
      the stale window Source: `plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md`
- [ ] [CODE] P2. Parallelize per-VM GCS reads in sweep() (exit_code_fleet_monitor.py + heartbeat_stall_watcher.py) via
      ThreadPoolExecutor, target <5min sweep, keep classify/route/emit sequential; fallback to reduced cron cadence if
      not shippable Source: `plans/active/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md`
- [ ] [DIAG] P2. run launch-measure-honest-coverage-vm.sh --oom-monitor for a fresh right-sizing verification Source:
      `plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md`
- [ ] [CODE] P2. UNPAUSE uts-prod-dp-exit-code-monitor-cron in the documented order (verify deploy image carries
      ecd6d2bd90, tombstone-backfill the 393 names, then unpause) Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [ ] [CODE] P2. Make exit_code_fleet_monitor complete a full fleet sweep inside its task timeout or loudly report
      incomplete coverage Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [ ] [CODE] P2. Set the exit-code-monitor Cloud Run job's concurrency to 1 to stop */5 executions overlapping Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [ ] [CODE] P2. Investigate the shared trigger behind ~398 VMs hanging mid-shutdown in the same hour window Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [ ] [CODE] P2. Make a VM stuck mid-shutdown actually terminate (shutdown-path DELETE or a reaper watchdog) Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [ ] [CODE] P2. Verify whether the GCS-backed relaunch budget fix is actually present in the deployed
      deployment-api:latest image Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [ ] [CODE] P2. Re-probe the 39 VMs whose serial-console read returned no parseable timestamp Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
