---
doc_type: plan
title: DeFi satellite AO batch 3 — residual-orphan triage after batch2
summary: >-
  Third AO-dispatch batch for defi, produced by the `/ag-closeout-audit` skill's Phase-1 (per-doc classify) + Phase-3
  (conflict-check + draft) triage over all 59 defi AG-primary docs, run AFTER batch2 landed (2026-07-26). With batch1,
  batch2, the consolidated closeout, the aggregated-sources index and the forked children (track01, track5,
  lending-writer-retire, dex-pool-symbol-fix+finalize, native-ao-extract+finalize) all counted as covering, only 17 docs
  came back orphaned (15 partial-coverage, 2 never-touched); 39 are archivable-after-planned-work (already covered), 2
  archivable-now (archive candidates), 1 a cross-cutting/infra mistag (excluded). Phase-3's conflict-check took the 8
  AO-eligible orphan docs and cleared 13 candidate todos → merged 2 read-only report todos on the same source doc into 1
  (avoids a same-file Progress-Log race) → **12 todos ship here**. It left 8 items conflict/operator-gated (notably 5
  `defi_migration_audit_log` items whose "fold into dedicated buckets" premise is STALE — the dedicated→shared
  consolidation already shipped, so drafting them would regress the architecture), 4 skip_covered (already covered, not
  re-drafted), and 9 non-batchable orphans in the Deferred sections for the next iteration or an operator ruling.
  **status: draft — NOT dispatched. Flipping to active is an operator decision (per CLAUDE.md "Plan destination" HARD
  RULE); this batch was drafted autonomously by the scheduled ag_closeout_auditor and awaits operator approval.**
status: active
nature: process
asset_group: [defi]
stage: [data]
repos:
  [
    unified-trading-pm,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    strategy-service,
    unified-api-contracts,
    agent-orchestrator,
    execution-service,
    unified-trading-library,
  ]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-3, satellite-docs, fresh-triage]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/defi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.4
estimate_calibrated_ai_days: 1.9
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (autonomous, scheduled ag_closeout_auditor, tranche=defi) — Phase 1 classified
  all 59 defi AG-primary docs via a Workflow fan-out (59 agents, sonnet), Phase 3 ran a conflict-check + candidate-todo
  draft over the 8 AO-eligible orphan docs via a second Workflow fan-out (8 agents, opus), per the skill's documented
  methodology. batch2 (also 2026-07-26) is counted as covering here — this batch is the residual after batch2.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 3 — residual-orphan triage after batch2

> **🟡 status: draft — NOT INGESTED / NOT DISPATCHED.** A draft plan is inert (`plans/PLAN_FORMAT.md`); the dispatcher
> ignores it until an operator flips `status: draft` → `active`. This batch was drafted autonomously by the scheduled
> `ag_closeout_auditor` (tranche=defi, 2026-07-26). Flipping it to active is an operator decision per CLAUDE.md's "Plan
> destination — ASK BEFORE CREATING" HARD RULE. Do a fresh re-read of each todo before activating (some source docs move
> fast).
>
> **Cross-plan sequencing note (todo 5):** the LIQUIDATION_CAPTURE tick-builder edits `paper_universe.py`, which
> `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s MEV-DOCS todo (batch2 line ~197) also edits. The edits are
> non-contradictory, but todo 5 should be **sequenced after** that batch2 todo lands to avoid a same-file race. If
> batch2 is still in flight when this batch activates, hold todo 5 until batch2's paper_universe.py change is in.

## Context (read before dispatching any todo)

Every todo below is a conflict-checked extraction from ONE orphaned defi source doc (each ends with `Source:`). The
conflict-check (Phase 3, one opus agent per orphan doc) grepped the whole covering set for each item's target
file/mechanism before drafting — items that a covering plan already claims were skipped (see "Already covered" note),
and items needing an operator/design ruling were parked (see Deferred). Same-priority todos run CONCURRENTLY across
workers by default; the 12 below were checked for cross-todo file collisions (the two read-only report checks on
`defi_manifest_no_expected_unattempted_seeder_2026_07_26.md` were merged into todo 9 to avoid a same-file Progress-Log
race). Two todos touch code beyond defi and are flagged inline: todo 2 (cefi/tradfi/sports strategy catalogs) and todo
10 (agent-orchestrator).

## Todos

- [ ] [DATA] P1. D1 DeFi features backfill — run the features-service compute over the captured DeFi raw window
      (features read canonical raw; C0 done) to populate `features-onchain-defi` (currently ~3 rows) and
      `features-delta-one-defi` (currently no index), materialising `staking_apy_bps`/`funding_rate_apy_bps` (onchain)
      and `basis_bps`/`realized_vol_*` (delta_one, via the `funding_oi` and `returns` feature-groups respectively) for
      the in-scope DeFi instruments. **`features-volatility-defi` DROPPED from this todo's scope 2026-07-26** (slot-8
      finding, main-ruling-confirmed): the volatility feature family's `--asset-group DEFI` choice was REMOVED
      2026-07-17 (operator ruling — no DeFi options products exist, so implied-vol/skew/term-structure surfaces cannot
      be computed for DeFi; `features_service/volatility/cli/parser.py` now hard-rejects it, the corresponding bucket
      was deleted, and a unit test (`test_asset_group_choices`) enforces `ASSET_GROUP_CHOICES == ["CEFI", "TRADFI"]`).
      The original done-when's "features-volatility-defi... present and populated" leg predates that ruling and is
      structurally unsatisfiable by design — NOT a gap to chase. Safe-idempotent justification: idempotent feature
      compute, no GCS delete. Repo: features-service. Done when: `features-onchain-defi` row count ≫ 3 AND
      `features-delta-one-defi` has a populated index, both over the full captured window (2 legs, not 3). Source:
      `data_completion_defi_2026_07_15.md`

      **BLOCKED 2026-07-26 (slot-8) — real bug found + fixed (unblocked the preflight check), but the actual
                                                                                                                                                                                                                                                          compute step is blocked on a separate, unresolved cross-cutting OOM issue:**

                                                                                                                                                                                                                                                          **Bug found + FIXED (unblocked, confirmed working)**: onchain's `DependencyChecker` (`features_service/onchain/
                                                                                                                                                                                                                                                          app/core/dependency_checker.py`, `UPSTREAM_DEPS`/`UPSTREAM_DEPS_DEFI`) had every `bucket_template` missing the
                                                                                                                                                                                                                                                          `-prd-` env-tier segment (`"market-data-tick-{asset_group_lower}-{project_id}"` instead of the canonical
                                                                                                                                                                                                                                                          `"market-data-tick-{asset_group_lower}-prd-{project_id}"` — see `unified_trading_library/config_interface/
                                                                                                                                                                                                                                                          paths/registry.py`'s own `-prd-`-bearing template). This made the checker always resolve a bucket that doesn't
                                                                                                                                                                                                                                                          exist, so it unconditionally reported all 5 DeFi MTDS on-chain deps as missing regardless of the real capture
                                                                                                                                                                                                                                                          date. Fixed + regression-tested (`tests/onchain/unit/test_dependency_checker_bucket_templates.py`) + shipped
                                                                                                                                                                                                                                                          `features-service@5fb00174`; confirmed working — a post-fix onchain run against `2026-07-20..2026-07-25`
                                                                                                                                                                                                                                                          correctly logged `Upstream dependencies: []`.

                                                                                                                                                                                                                                                          **BLOCKING issue (new, unresolved)**: every VM launch attempted AFTER the fix (4 total, varying window size,
                                                                                                                                                                                                                                                          feature-group scope, and confirmed-present-upstream-data windows) was OOM-killed (exit 137) on the default
                                                                                                                                                                                                                                                          `e2-standard-8` machine. Ruled out the obvious suspect — the already-resolved `defi_manifest_per_vm_shard_
                                                                                                                                                                                                                                                          fallback_bloat_2026_07_23.md` issue — by checking the live per-VM shard directory for the exact bucket these
                                                                                                                                                                                                                                                          VMs read: only 18.2MB across 4 shards, far under that fix's 200MiB budget cap, so this is a DIFFERENT,
                                                                                                                                                                                                                                                          currently-unexplained memory sink. Full writeup + all 4 attempts' details + suggested next steps:
                                                                                                                                                                                                                                                          `/plans/active/issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md`. **This todo cannot
                                                                                                                                                                                                                                                          proceed to its actual compute step until that issue is resolved** — do not repeat the same window/feature-group
                                                                                                                                                                                                                                                          permutations already tried there (documented in full in the issue doc); a real fix requires live-VM profiling
                                                                                                                                                                                                                                                          or a local repro with a memory profiler, which is out of scope for a plain backfill session.

                                                                                                                                                                                                                                                          **Separate, smaller finding also worth knowing before resuming**: MDPS DeFi `processed_candles` coverage is
                                                                                                                                                                                                                                                          SPARSE — dense `2026-04-16..2026-05-22`, then a hard gap `2026-05-23..2026-07-17` (zero days), then only 3
                                                                                                                                                                                                                                                          sparse days since (`07-18`, `07-22`, `07-25`). `delta_one`'s dependency checker requires MDPS candles
                                                                                                                                                                                                                                                          (`required: True`, no DEFI override), so any `--start-date` in that gap fails preflight with `No data for
                                                                                                                                                                                                                                                          <date>/DEFI` regardless of the OOM issue. Pick a date from the dense block or the 3 sparse days once the OOM
                                                                                                                                                                                                                                                          issue is fixed. Also confirmed onchain's needed groups are `lst_yields` (→ `staking_apy_bps`) and
                                                                                                                                                                                                                                                          `perp_funding_rates` (→ `funding_rate_apy_bps`); delta_one's are `funding_oi` and `returns` — use
                                                                                                                                                                                                                                                          `FEATURE_GROUP=<group>` (launcher env override, not `ALL`) once compute is unblocked, to keep memory footprint
                                                                                                                                                                                                                                                          minimal regardless of whether the OOM issue turns out to be group-count-related.

                                                                          **UNBLOCKED 2026-07-30 (slot-14)**: the OOM/hang issue is resolved — see
                                                                          `/plans/active/issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md` (now `status: resolved`).
                                                                          Relaunched the exact repro (`features-onchain-defi-20260730-202653`, on-VM ps/free/dmesg monitor, all code
                                                                          tarballs freshly republished) with `unified-trading-library@06190d77` live: clean `exit_code=0` in ~2 min, flat
                                                                          ~603 MB RSS, zero dmesg oom/killed hits across the whole run — the bug does not reproduce. `[BLOCKED-INFRA]` tag
                                                                          removed; this todo's actual full-window compute (the D1 done-when above) has NOT been executed yet — that
                                                                          remains open, separate follow-on work, not done by this note.

                                                                          **2026-07-30 (slot-3) — real full-window compute attempted; both legs hit NEW, real, previously-undiscovered
                                                                          bugs (distinct from the resolved OOM issue) — NOT flipping this checkbox, 2 follow-on issue docs filed:**

                                                                          **Onchain leg (`perp_funding_rates` → `funding_rate_apy_bps`)**: launched
                                                                          `features-onchain-defi-20260730-210912` (`2023-06-01..2023-06-07`, a clean dependency window verified via the
                                                                          live MTDS manifest — zero `attempted_failed` across all 5 `UPSTREAM_DEPS_DEFI` data_types). Found + FIXED a
                                                                          real bug: `features_service/onchain/calculators/perp_funding_rates_defi.py`'s hardcoded `_DEFI_SYMBOL =
                                                                          "ETH-PERP"` never matched ANY live row — the MTDS canonical `perp_funding` schema stores the bare ticker
                                                                          (`symbol="ETH"`, confirmed by downloading a live parquet), not an `"ETH-PERP"` suffix; the calculator always
                                                                          silently returned honest-absence (`empty_confirmed(EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE)`), on every date,
                                                                          since some prior canonical-format migration changed the symbol shape and this constant was never updated.
                                                                          Fixed: `_DEFI_SYMBOL = "ETH"` + switched the substring `.str.contains()` match to an exact/suffix match (avoids
                                                                          a future false-positive collision, e.g. a hypothetical "STETH" row matching an "ETH" filter) —
                                                                          `features-service@faedd957`, 2 new regression tests added (13 total, all green).
                                                                          **Separately** (not fixed by me — filed as its own issue): the onchain batch_handler's
                                                                          `_emit_batch_completion` requires ALL 13 feature-groups in a run to succeed (`success_count == len(groups)`)
                                                                          for exit 0 — 4 unrelated groups (`rewards`/`flash_loan_availability`/`health_factor`/`liquidation_events`)
                                                                          wrote `attempted_failed(calculator_produced_base_columns_only)` on this window (their own calculators appear
                                                                          to have a different, unexamined gap), so the VM run still exited 1 overall even after my fix, despite
                                                                          `lending_rates` (~146k rows) and `lst_yields` (67 rows) writing real data successfully. See
                                                                          `/plans/active/issues/onchain_batch_all_groups_must_succeed_masks_partial_success_2026_07_30.md`.
                                                                          `features-onchain-defi` row count is trivially already `≫ 3` (pre-existing `lending_rates` alone is 14.6M rows
                                                                          per the live manifest) — that leg of the done-when was stale before this session even started.

                                                                          **Delta_one leg (`funding_oi`+`returns`)**: NOT date-fixable — root-caused to a structural instrument-universe
                                                                          mismatch bug in `LookbackValidator._discover_instruments()` (shared CEFI/TRADFI/DEFI/PREDICTION code): for
                                                                          DEFI it always discovers instruments from the DEX-pool-swap candle universe regardless of which data_type the
                                                                          requested feature_group actually needs, so `funding_oi`/`returns` (both map to pass-through, never-candle-
                                                                          processed data_types for DEFI) always validate the WRONG instrument set and read 0 candles on every date.
                                                                          Verified across 2 separate windows/timeframes (both failed identically). Filed
                                                                          `/plans/active/issues/delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md`
                                                                          with the full repro + code trace + a recommended fix (source instrument discovery from the MTDS manifest for
                                                                          pass-through data types, not `processed_candles`) — this needs a cross-asset-group design decision, so I did
                                                                          NOT patch the shared `LookbackValidator` in this session (craft-scope discipline: don't absorb an
                                                                          open-ended design call mid-backfill). `features-delta-one-defi` still has **no index** — that leg of the
                                                                          done-when remains unmet until the LookbackValidator fix lands.

                                                                          **2026-07-30 (slot-4, DP-VM-001 relaunch escalation) — STOP: do NOT relaunch `funding_oi`/`returns`
                                                                          for DEFI delta_one, a NEW deterministic bug blocks the candle-load step even with the fix above
                                                                          live:** dispatched to relaunch `features-delta-one-defi-20260730-222034` (exit_code=1). Its
                                                                          instrument discovery now works correctly (412/25 real perp_funding/oracle_prices instruments, not the
                                                                          old DEX-pool universe) — `8e62dc30` is confirmed good. But the compute step's candle-loading path
                                                                          (`_tf_cluster_helper.py`'s `_load_base_candles`/`_load_range_candles_with_buffer`, calling
                                                                          `DataLoader.load_candles_with_buffer`) has no pass-through branch: for `perp_funding`/`oracle_prices`
                                                                          (`NEEDS_CANDLE_PROCESSING=False`), MDPS never writes `processed_candles`, so every instrument reads 0
                                                                          candles, 100% deterministically, on every date range. Confirmed identically across **10** VM launches
                                                                          today (6 with `exit_code=1` confirmed, more mid-flight showing the same live pattern as this note was
                                                                          written) — a 7-day window, and 2 separate multi-year full-history windows, both `funding_oi` and
                                                                          `returns`, all fail the same way. **Did NOT relaunch again** (deterministic failure + the runbook's
                                                                          own `≤2/(vm-prefix,day)` relaunch bound already far exceeded at 10). Filed
                                                                          `/plans/active/issues/delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md` with the full
                                                                          repro, code trace, and recommended fix (a pass-through raw-MTDS-read branch keyed on
                                                                          `needs_candle_processing()`, mirroring the manifest-based instrument-discovery fix). **This todo's
                                                                          delta_one leg cannot proceed further until that fix lands — any future dispatch of this todo should
                                                                          skip re-attempting funding_oi/returns for DEFI and consider parking it (see that issue doc's
                                                                          [OPERATOR] todo) instead of relaunching a VM.**

                                                                          **2026-07-30 (slot-2, data_pipeline_failure escalation DP-VM-002) — RECONFIRMED, still not parked:**
                                                                          `features-delta-one-defi-20260730-231206` (`funding_oi`) and `-231230` (`returns`, full-history) —
                                                                          both launched by slot 14 (this task's live `dispatched_to`) — hit the identical deterministic
                                                                          candle-loader bug (full evidence in the issue doc's Progress Log). Messaged slot 14 directly to stop
                                                                          relaunching. The `[OPERATOR]` parking todo is still unexecuted — 12+ VMs burned today.

                                                                          **2026-07-30 (slot-14) — onchain leg's ACTUAL blocker found + fixed + confirmed working
                                                                          live; delta_one leg: 2 more relaunches burned before reading slot-4's STOP note above
                                                                          (my mistake — read the plan file ONCE at task start, slot-4's note landed mid-session
                                                                          and I never re-fetched it before relaunching). Net: onchain leg materially advanced;
                                                                          delta_one leg NOT further advanced beyond slot-4's already-standing blocker, 2 more
                                                                          wasted VM launches, one useful adjacent efficiency fix shipped anyway:**

                                                                      **Onchain leg — real, previously-undiscovered blocker found + fixed + LIVE-CONFIRMED
                                                                      WORKING:** independent of the delta_one investigation above, `perp_funding_rates`
                                                                      (→ `funding_rate_apy_bps`) had ANOTHER bug the earlier symbol fix (faedd957) didn't
                                                                      touch: a hardcoded 2026-05-30 "BATCH SKIP" in
                                                                      `OnChainOrchestrationService._process_perp_funding_rates` unconditionally treated
                                                                      EVERY historical (`start_date < today`) DEFI batch date as
                                                                      `empty_confirmed(EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE)` WITHOUT EVER attempting a
                                                                      real read — premised on "DeFi prd MDPS has no perp_funding shards for the 2026-01-25
                                                                      backfill window", which is now FALSE (live MTDS manifest: 12,500 real `captured`
                                                                      HYPERLIQUID perp_funding rows, 2023-05-12..2026-06-09, zero `attempted_failed`). This
                                                                      is why every prior attempt this session (including my own initial one) saw
                                                                      `empty_confirmed` for perp_funding_rates regardless of date or the symbol fix.
                                                                      Removed the stale skip, added regression tests (both a NEW integration test and a
                                                                      corrected pre-existing unit test that had asserted the OLD stale behavior) —
                                                                      `features-service@1309480a`, `quality-gates.sh` green (17996 tests). **Live-confirmed
                                                                      working**: relaunched `features-onchain-defi-20260730-225646` (`--feature-group
                                                                      perp_funding_rates`, full window `2023-05-12..2026-06-09`, `SKIP_DEPENDENCY_CHECK=1`
                                                                      after hitting an unrelated transient manifest-consolidator-staleness condition caused
                                                                      by my own concurrent VM launches — verified safe via the same independent manifest
                                                                      read cited above) — now writing real `funding_rate_apy_bps` rows per day
                                                                      (`hyperliquid/ETH/<date> → funding_rate=... apy_bps=...`, confirmed via live GCS
                                                                      `Wrote 1 rows to .../feature_group=perp_funding_rates/...` log lines) — spot-checked
                                                                      real files at multiple points across the window (`day=2023-05-30`, `2023-06-01`,
                                                                      `2023-07-19`, `2025-09-06` all confirmed present via `gcloud storage ls`; a few other
                                                                      spot-checked dates legitimately absent — matches the per-day HYPERLIQUID gaps already
                                                                      visible in the run.log, e.g. `2024-11-24→2024-11-29→2024-12-06`, honest-absence, not a
                                                                      bug). Monitored ~37 minutes total (22:59→23:36): progressed steadily to `2025-09-06`
                                                                      of `2023-05-12..2026-06-09` (~76%, 858/1124 days) by 23:32:39, then went quiet — no
                                                                      new `Wrote` lines for the next 7+ min (only heartbeats). SSH-confirmed the process
                                                                      (`pid 8837`) is genuinely still alive and CPU-active (state `R`, 25% CPU, RSS only
                                                                      1.8GB/31GB — not an OOM risk, just legitimately slow on whatever it's currently
                                                                      processing), so this is NOT a repeat of the earlier OOM/hang class — just slower
                                                                      going than the first ~800 days. **Not yet fully complete as this note is written** —
                                                                      ~266 days remain (2025-09-06..2026-06-09). A future dispatch (or this same VM, left
                                                                      running — SPOT, idempotent, will self-delete on completion per
                                                                      `VM_SHUTDOWN_ON_COMPLETION=true`) should verify `features-onchain-defi-20260730-225646`
                                                                      reached `DEPLOYMENT_COMPLETED exit_code=0` (VM absence from
                                                                      `gcloud compute instances list` + a matching `DEPLOYMENT_COMPLETED` entry in
                                                                      `gs://deployment-scripts-central-element-323112/deployments/archive/2026-07-30/` is
                                                                      the completion signal) before treating the onchain leg's full-window compute as
                                                                      fully done — the FIX itself is proven correct and shipped; only the LAST ~24% of this
                                                                      one VM's run remains to finish. If it's later found `FAILED` instead of merely slow,
                                                                      the safe-idempotent relaunch is a plain re-run of the same command (manifest-write is
                                                                      `record_captured`-per-day, already-written days won't be recomputed by a fresh full-
                                                                      range relaunch unless `--force` is passed).

                                                                          **Delta_one leg — shipped one real adjacent efficiency fix, but did NOT clear slot-4's
                                                                          blocker (mistakenly relaunched before reading the STOP note above):** shipped
                                                                          `features-service@f932908b` — `DataLoader.candle_data_types` was unioning over ALL
                                                                          `DEFAULT_FEATURE_GROUPS` for the asset_group regardless of the CLI's actual
                                                                          `--feature-group`, so a single-group launch (e.g. `funding_oi`) still walked the
                                                                          manifest for every OTHER group's data_type too (thousands of irrelevant `dex_pool_swaps`
                                                                          DEX-pool instrument checks). Scoped it to the requested group(s); regression tests
                                                                          added; `quality-gates.sh` green. This IS a real, live-confirmed fix (a relaunched
                                                                          `returns` VM correctly discovered real oracle-price instruments like
                                                                          `CHAINLINK:spot_asset:DAI_USD` afterward, not DEX pools) — but it does NOT unblock the
                                                                          leg: BOTH the `funding_oi` relaunch (`features-delta-one-defi-20260730-231206`) and the
                                                                          `returns` relaunch (`features-delta-one-defi-20260730-231230`) still hit the EXACT
                                                                          deterministic candle-loader gap slot-4 already found and filed
                                                                          (`delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`) — `funding_oi`
                                                                          failed cleanly (`No delta-one instruments available after filtering`, exit 1, see the
                                                                          NEW narrower finding `delta_one_get_captured_instruments_blank_id_perp_funding_2026_07_30.md`,
                                                                          downgraded to P2 after cross-checking slot-4's evidence contradicts a blanket claim);
                                                                          `returns` produced 23,260+ `No upstream MDPS data for <real-instrument> ... skipping
                                                                          date` warnings identical to slot-4's documented shape — killed it (SPOT, zero real
                                                                          output, confirmed no `delta_one/` prefix ever appeared in the bucket) rather than let
                                                                          it keep burning compute toward the same guaranteed outcome. **Reaffirming slot-4's
                                                                          standing guidance: do NOT relaunch funding_oi/returns for DEFI delta_one again until
                                                                          `delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`'s todo 1 (pass-through
                                                                          candle-read branch) lands — my session is the 3rd consecutive one to independently
                                                                          confirm this exact deterministic failure. Its [OPERATOR] P1 todo (park this D1 todo via
                                                                          `priority: 999` + a false prerequisite) remains unactioned and still recommended.**

                                                                          **Lesson for future dispatches of this todo**: this plan file is being actively
                                                                          edited by concurrent slots mid-session (3 different slots touched D1 today alone) — a
                                                                          worker that reads it once at task start and doesn't re-fetch before a risky action
                                                                          (launching a VM, relaunching after a failure) can duplicate already-exhausted work or
                                                                          contradict an already-standing STOP. Re-read this todo's own text immediately before
                                                                          any VM launch, not just at task start.

                                                                          **2026-07-31 (slot-2, data_engineering craft) — onchain leg CONFIRMED COMPLETE;
                                                                          funding_oi leg CONFIRMED structurally blocked (not a code bug); returns leg's
                                                                          3-fix chain now fully shipped, verification run still pending — session ending on
                                                                          context pressure, precise resume point below.**
                                                                          - **Onchain leg: DONE.** `perp_funding_rates` full-window compute (the VM slot-14 left
                                                                            running) completed — verified via manifest/GCS: real data exists through
                                                                            `day=2026-06-09`, the exact end of the `2023-05-12..2026-06-09` target window (182
                                                                            real days, matching HYPERLIQUID's genuine honest-absence gaps, not a stall).
                                                                            `features-onchain-defi` row count already `≫3` (pre-existing `lending_rates` alone
                                                                            is 14.6M rows). This leg of the done-when is satisfied.
                                                                          - **funding_oi leg: BLOCKED, not by a loader bug.** HYPERLIQUID's raw `perp_funding`
                                                                            data structurally never carries `open_interest`/`mark_price`/`index_price` (confirmed
                                                                            via direct raw-parquet inspection across both capture eras). Filed
                                                                            `/plans/active/issues/defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`
                                                                            with an `[OPERATOR]` fix-direction decision needed. Do not relaunch `funding_oi` again
                                                                            until that resolves.
                                                                          - **returns leg: 3 real bugs found + fixed this session, in the SAME function
                                                                            (`_resolve_passthrough_timestamp`), each masking the next:** (1)
                                                                            `features-service@3bce3997` — made `available_at` win when it's a native Datetime
                                                                            (INCOMPLETE — that branch never fires in real data). (2) `features-service@c46509be`
                                                                            — parses `available_at` as the ISO8601 STRING it actually is on disk, fixed the
                                                                            SchemaError (confirmed live: eliminated cleanly on a real relaunch). (3)
                                                                            `features-service@94fd3c8b` — **the important one**: `available_at` is a
                                                                            PIPELINE-INGESTION timestamp, not the event time (a real 2023-05-31 row's
                                                                            `available_at` was `2026-07-22`, 3 years off) — reversed the priority so real
                                                                            event-time fields (`timestamp`/`publish_time`/`date`) win, `available_at` is now
                                                                            LAST-RESORT only. Without fix (3), fix (2) alone produces a SILENT correctness bug
                                                                            (no crash, just zero real writes — every row mis-dated into the wrong day). Full
                                                                            writeup + blast-radius assessment:
                                                                            `/plans/active/issues/delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`'s
                                                                            latest entries. All 3 shipped + green (`quality-gates.sh`, 114/114
                                                                            `test_data_loader.py`); verified locally against real GCS data (not just mocks) that
                                                                            the corrected function now resolves real 2023 event timestamps.
                                                                          - **UPDATE — relaunched against the fully-shipped fix (`features-service@f34d2c1a`,
                                                                            the same content as `94fd3c8b` after a quickmerge auto-rebase through a
                                                                            promote cycle) and found a 4th, DISTINCT bug.** Republished the tarball
                                                                            (confirmed `sha=f34d2c1a140d`), relaunched the real `returns`
                                                                            verification-window run
                                                                            (`features-delta-one-defi-20260731-020600`). The timestamp SchemaError is
                                                                            CONFIRMED completely gone — zero exceptions across the whole run. But it
                                                                            still produced `Completed 0/51 instruments for returns` on EVERY date
                                                                            checked (spot-checked through 2023-08-17, ~97 days in) — zero real writes,
                                                                            despite the range-level load claiming real data exists for 27/51
                                                                            instruments. Root-caused (not guessed): `_load_passthrough_range()`'s
                                                                            per-instrument symbol filter does an exact match between the manifest's
                                                                            registered instrument_id (underscore-separated, e.g. `ETH_USD`) and the raw
                                                                            parquet's `symbol`/`feed` column (SLASH-separated, e.g. `ETH/USD`, confirmed
                                                                            via direct inspection of the same real row used throughout this session) —
                                                                            `"ETH_USD" != "ETH/USD"`, so the filter silently drops every instrument
                                                                            whose real symbol format doesn't happen to already match the manifest's
                                                                            registered form. This is a 4th, SEPARATE bug from the 3 timestamp bugs
                                                                            (different code path — symbol filtering, not timestamp resolution) that was
                                                                            invisible until the SchemaError stopped masking it. Filed
                                                                            `/plans/active/issues/delta_one_passthrough_symbol_filter_slash_underscore_mismatch_2026_07_31.md`
                                                                            with the fix recommendation (normalize separators on both sides before
                                                                            comparing, verified across every DEFI pass-through venue, not just
                                                                            CHAINLINK). Did not patch it myself — 3 fixes in the same function chain
                                                                            already shipped this session; a 4th blind guess without checking every
                                                                            affected venue's real symbol format risks repeating the same
                                                                            "looked-fixed-wasn't" pattern. **This todo's `returns` leg (and by
                                                                            extension `funding_oi`, once its separate OI-absence blocker resolves)
                                                                            cannot complete until that symbol-filter fix lands** — do not relaunch
                                                                            `returns`/`funding_oi` again until it does; the failure is deterministic,
                                                                            not date- or window-dependent.

                                                                          **2026-07-31 (slot-16, data_engineering craft) — re-dispatched, bare-check
                                                                          confirms both remaining legs are STILL blocked on the same 2 unresolved
                                                                          design decisions; recommending this todo be PARKED rather than redispatched
                                                                          further.** The symbol-filter fix (`7e10172c`) is shipped — confirmed via
                                                                          `git log`. But it uncovered a 5th, deeper bug: `returns` is now blocked on
                                                                          `delta_one_passthrough_lookback_buffer_too_short_for_sparse_ticks_2026_07_31.md`'s
                                                                          `[BACKEND]` P1 (`buffer_manager.py`'s calendar-buffer formula assumes dense
                                                                          candles; DEFI pass-through ticks are sparse — 3 candidate fix directions
                                                                          named, needs cross-venue verification before shipping). `funding_oi` is
                                                                          blocked on `defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`'s
                                                                          `[OPERATOR]` P2 (HYPERLIQUID structurally never carries `open_interest` —
                                                                          adapter-extend vs. calculator-relax is a repo-owner call). Verified via
                                                                          `git log` on `features-service` that neither fix has landed since 07-31's
                                                                          filings. Onchain leg remains DONE (unaffected). **This is now the 6th+
                                                                          consecutive dispatch of this exact todo to independently confirm the same
                                                                          conclusion** (slots 2, 4, 5, 8, 14 today alone) — each correctly declined to
                                                                          freelance the cross-cutting design calls (consistent with
                                                                          `agent-orchestrator-single-vm-architecture.md`'s dispatch-scope-eligibility
                                                                          rule: an open-ended judgment call is not a worker todo). Did not attempt
                                                                          either fix myself for the same reason prior slots gave. Filed a /blocked
                                                                          question recommending main/operator park this todo (`priority: 999` + a
                                                                          false prerequisite gated on both linked issue docs' P1/P2 resolving) so
                                                                          future dispatch cycles stop re-confirming an unchanged blocker. Skipping.

                                                                          **2026-07-31 (slot-10, data_engineering craft) — the buffer-formula
                                                                          fix (`9e70fbac`) landed since slot-16's dispatch; relaunched `returns`
                                                                          and found + fixed a 6th, previously-undiscovered bug — verification
                                                                          relaunch in flight, funding_oi still correctly untouched
                                                                          (operator-gated).** Found `features-service@9e70fbac` (the
                                                                          `delta_one_passthrough_lookback_buffer_too_short_for_sparse_ticks_2026_07_31.md`
                                                                          fix) already shipped + QG-green, but its own doc flags the actual VM
                                                                          verification run as NOT yet done — that's this todo's job. Found a VM
                                                                          already running the exact verification command
                                                                          (`features-delta-one-defi-20260731-083647`, `returns`,
                                                                          `2023-05-12..2023-10-31`, launched ~08:36 UTC by a concurrent/prior
                                                                          slot) — read its live log rather than launch a duplicate: 246+
                                                                          consecutive dates, every one `Completed 0/51 instruments for
                                                                          returns`, deterministic. Root-caused (not guessed): `returns.py`'s
                                                                          `_calculate_btc_trend_features()` unconditionally computes
                                                                          `btc_trailing_return_{1,3,6,12}m`/`btc_realized_vol` (up to 252
                                                                          trailing daily bars ≈ 12 calendar months — registry_specs.yaml
                                                                          declares `nan_policy: warmup_only` for exactly this reason) for
                                                                          EVERY instrument in the `returns` group, but `EXPECTED_SPARSE_COLUMNS`
                                                                          had no `"returns"` entry — so the >50% NaN shard-rejection check in
                                                                          `orchestrator.py` didn't know these columns are EXPECTED to be NaN
                                                                          during warmup, and rejected every shard on that alone, masking the
                                                                          real (working) return columns underneath. This is a DIFFERENT bug
                                                                          from the buffer-sizing fix (`9e70fbac`) — that fix ensures enough
                                                                          REAL rows are loaded; this bug is in the NaN-quality-gate not
                                                                          respecting the registry's own declared warmup semantics for a
                                                                          long-horizon derived feature. Fix: added `"returns":
                                                                          ["btc_trailing_return_", "btc_realized_vol"]` to
                                                                          `EXPECTED_SPARSE_COLUMNS` in `delta_one/constants.py` (the same
                                                                          established mechanism already used for `swing_outcome_targets`) —
                                                                          `features-service@12a64eb9`, 2 new regression tests in
                                                                          `test_nan_handler.py`, `quality-gates.sh` green (18049 passed).
                                                                          Deleted the doomed VM (confirmed deterministic zero-write, SPOT,
                                                                          idempotent, no work lost), republished the code tarball (confirmed
                                                                          `commit_sha=12a64eb9` in the manifest — the exact tarball-staleness
                                                                          trap this doc's own Finding 2 describes), relaunched the identical
                                                                          verification command as `features-delta-one-defi-20260731-094100`.
                                                                          **Not yet confirmed complete as this entry is written** — see this
                                                                          todo's next update for the verification outcome; if it shows real
                                                                          `Completed N/51` with N>0, proceed to the full-window production run
                                                                          (real coverage per the live manifest: CHAINLINK oracle_prices
                                                                          2022-11-01..2026-07-22, PYTH 2023-01-27..2026-07-22 — checked via a
                                                                          scoped `read_availability_index` column-filtered read, not a
                                                                          whole-corpus walk). `funding_oi` remains correctly untouched —
                                                                          structurally blocked on
                                                                          `defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`'s
                                                                          `[OPERATOR]` P2, unaffected by this fix.

                                                                          **2026-07-31 (slot-11, data_engineering craft) — returns leg
                                                                          production-scale VERIFIED WORKING; full-window backfill launched
                                                                          (in flight, multi-hour); funding_oi still correctly untouched
                                                                          (operator-gated).** Read the live run.log of slot-10's standing
                                                                          verification VM (`features-delta-one-defi-20260731-094100`,
                                                                          `2023-05-12..2023-10-31`): 24 consecutive real days completed
                                                                          with `Completed 51/51 instruments for returns`, zero errors —
                                                                          the buffer-fix (`9e70fbac`) is proven correct at real scale, not
                                                                          just the earlier narrow repro. Flipped both todos in
                                                                          `delta_one_passthrough_lookback_buffer_too_short_for_sparse_ticks_2026_07_31.md`
                                                                          (now `status: resolved`). Found `features-service`'s repo HEAD
                                                                          (`d7133e29`, a further generalization of the NaN-exemption fix)
                                                                          was NOT yet published as a tarball — the launcher's own
                                                                          freshness check caught it; republished `features-service` +
                                                                          `market-tick-data-service` tarballs (deployment-service had no
                                                                          `.venv`, so the upload step failed on
                                                                          `ModuleNotFoundError: deployment_service` — created it via
                                                                          `uv venv .venv && uv pip install -e .`, then the republish
                                                                          succeeded). Attempted the FULL production window for `returns`
                                                                          (`--start-date 2022-11-01 --end-date 2026-07-22`) — hit 2
                                                                          NEW, distinct real bugs this session, both filed as separate
                                                                          issue docs, and made real forward progress on the safe
                                                                          majority of the window instead of forcing the full range:

                                                                          **Bug A — preflight false negative (filed
                                                                          `delta_one_dependency_checker_ignores_passthrough_feature_group_2026_07_31.md`)**:
                                                                          `features-delta-one-defi-20260731-104418` (first attempt,
                                                                          preempted 78s after insert, zero work lost, relaunched) then
                                                                          `-104738` failed preflight — `_check_dependencies` requires
                                                                          MDPS `processed_candles` unconditionally even though
                                                                          `returns` is pass-through and never reads it; MDPS's real
                                                                          DEFI candle coverage doesn't reach back to 2022-11-01 (the
                                                                          narrower verification window's 2023-05-12 start does have
                                                                          it, which is why THAT run never hit this). Root cause +
                                                                          recommended fix filed; worked around this session via
                                                                          `--skip-dependency-check` (justified — independently verified
                                                                          via manifest + direct GCS reads that real `oracle_prices`
                                                                          data exists across the full window).

                                                                          **Bug B — runaway memory under skip-dependency-check +
                                                                          pre-2023-05-12 dates (filed
                                                                          `delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md`)**:
                                                                          relaunching `-104738` with the bypass hit a SEPARATE,
                                                                          previously-undiscovered bug — RSS climbed to 18-21GB/31GB
                                                                          within ~7 minutes with zero real writes (only the first
                                                                          date's instrument-listing log line ever appeared); killed
                                                                          before OOM. A narrower ~192-day chunk of the SAME
                                                                          pre-2023-05-12 range + SAME bypass flag
                                                                          (`-105928`, 2022-11-01..2023-05-11) reproduced the identical
                                                                          runaway-memory pattern (looked flat at the 3-min mark, but
                                                                          had grown to 17.5GB by ~15 min) — ruling out "total window
                                                                          span" as the trigger. A THIRD launch, same feature_group,
                                                                          NO bypass flag, start date 2023-11-01 (real MDPS coverage
                                                                          exists there so preflight passes legitimately) —
                                                                          `-110727` — stayed flat at 4.3GB and produced real progress,
                                                                          matching the ALSO-stable ~4.6GB profile of the standing
                                                                          094100 verification VM. The bypass-flag + early-date
                                                                          combination is the reproducible trigger; exact code-level
                                                                          mechanism not yet pinpointed (needs a profiler/local repro,
                                                                          filed as follow-up). **Did not force a 3rd relaunch of the
                                                                          2022-11-01..2023-05-11 gap** — 2 consecutive reproductions
                                                                          of the identical OOM pattern is enough evidence; a 3rd
                                                                          would just repeat the waste.

                                                                          **Net real progress this session**: TWO healthy production
                                                                          VMs now running unattended, covering the safe majority of
                                                                          the window — `094100` (2023-05-12..2023-10-31, 24+ real
                                                                          days done, stable) and `110727` (2023-11-01..2026-07-22,
                                                                          just started, stable, real writes confirmed in flight).
                                                                          Together these will cover essentially the entire real
                                                                          window EXCEPT 2022-11-01..2023-05-11 (~6 months), which
                                                                          needs Bug B's fix before it can be safely attempted (SPOT +
                                                                          idempotent + `VM_SHUTDOWN_ON_COMPLETION=true`, safe to leave
                                                                          running; **a future dispatch should verify both reached
                                                                          `DEPLOYMENT_COMPLETED exit_code=0`** via VM absence +
                                                                          a matching completion entry in
                                                                          `gs://deployment-scripts-central-element-323112/deployments/archive/2026-07-31/`
                                                                          before treating the covered portion as fully done — a
                                                                          FAILED/preempted state is a safe plain relaunch,
                                                                          already-written days won't be recomputed absent `--force`).
                                                                          `funding_oi` remains correctly untouched — still blocked on
                                                                          `defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`'s
                                                                          `[OPERATOR]` P2 (HYPERLIQUID structurally missing
                                                                          `open_interest`), unaffected by any of this session's work.
                                                                          Not flipping this checkbox — the done-when needs BOTH legs
                                                                          (`funding_oi` + `returns`) over the FULL window, and neither
                                                                          is fully confirmed complete yet (returns leg: ~85% of the
                                                                          window in flight, ~6 months blocked on Bug B; funding_oi:
                                                                          fully blocked on the operator decision).

- [x] ✅ [STRATEGY] P1. **[CROSS-AG: touches cefi/tradfi/sports strategy code]** Sweep `archetype_slots_cefi.py`
      (CEFI_SLOTS), `archetype_slots_tradfi.py` (TRADFI_SLOTS), and `archetype_slots_sports.py` (SPORTS_SLOTS) — the v5
      slot-table construction surfaces parallel to the already-swept `archetype_slots_defi.py` DEFI_SLOTS (where 7/28
      rows were broken) — for catalog-emitted-config-key vs engine-param-read drift, using this doc's proven technique:
      construct the real registered engine (`get_archetype_engine_class` / factory.py ARCHETYPE_ENGINE_REGISTRY) from
      each slot's `initial_config`, call `on_tick` with realistic per-row features, and confirm a non-`[]` instruction.
      Fix unambiguous mechanical key rename/add drift in place (ADD the engine's real keys alongside — do not drop keys
      a real second consumer reads); for design-gated archetypes (RULES_DIRECTIONAL_CONTINUOUS /
      RULES_DIRECTIONAL_EVENT_SETTLED / ML_DIRECTIONAL_EVENT_SETTLED / MARKET_MAKING_EVENT_SETTLED / VOL_TRADING_OPTIONS
      — already xfail'd) leave them `xfail(strict=True)` with a one-line reason, do NOT force-fix. Extend
      `tests/unit/engine/strategies/v2/test_all_catalogued_archetypes_construct_and_fire.py` to parametrize
      CEFI_SLOTS/TRADFI_SLOTS/SPORTS_SLOTS (mirroring its DEFI_SLOTS coverage). Repo: strategy-service. Done when: every
      CEFI/TRADFI/SPORTS slot row either fires a real non-empty instruction or is explicitly
      xfail(strict=True)/allow-listed with a reason, the extended guardrail is green under
      `bash scripts/quality-gates.sh --no-fix` (0 unexpected failures, 0 XPASS), mechanical fixes shipped via quickmerge
      scoped to touched files. Source: `defi_catalog_engine_config_key_contract_drift_2026_07_23.md` —
      **strategy-service@bc441642**. Swept all 31 CEFI + 12 TRADFI + 5 SPORTS slot rows: found + fixed the same
      catalog/engine config-key drift bug class in 2 CEFI rows (`STAT_ARB_BTC_ETH`, `REL_VOL_BTC_ETH` — catalog set
      `leg_a`/`leg_b`/`entry_zscore`/`exit_zscore`; `StatArbPairsFixedEngine` reads
      `long_instrument`/`short_instrument`/`long_venue`/`entry_z_score`/`exit_z_score`; added the real keys alongside,
      kept the originals as documentation per the same-catalog-surface `catalog_trading.py` precedent). All other rows
      already fired correctly or were on the existing design-gated xfail allow-list (RULES_DIRECTIONAL_CONTINUOUS /
      ML_DIRECTIONAL_EVENT_SETTLED / MARKET_MAKING_EVENT_SETTLED / VOL_TRADING_OPTIONS) — none force-fixed. Extended
      `test_all_catalogued_archetypes_construct_and_fire.py` to parametrize CEFI/TRADFI/SPORTS_SLOTS via a shared
      `_slot_test_params`/`_assert_slot_constructs_and_fires` helper (refactored the existing DEFI_SLOTS test onto the
      same helper, behavior-preserving). Verified: `bash scripts/quality-gates.sh --no-fix` green (real exit code
      confirmed via unpiped re-run, not a `| tail` artifact); systemic test 92 passed, 22 xfailed, 0 unexpected
      failures, 0 XPASS.

- [x] 2026-07-27 (slot-2) ✅ [DATA] P1. D2 MDPS `swaps_ohlcv` reprocess of the stale chain-column
      `attempted_failed`/`SCHEMA_VALIDATION_FAILED` rows — **VERIFIED STALE PREMISE, no reprocess needed.** Read the
      LIVE consolidated manifest directly (`market-data-tick-defi-prd-central-element-323112` —
      `resolve_bucket_name(kind="market-data", asset_group="defi")`; confirmed the legacy non-`-prd`
      `market-data-tick-defi-central-element-323112` bucket this todo's own text cites no longer exists, 404): **zero**
      `attempted_failed` rows exist for UNISWAP_V3-ETHEREUM or any of the 10 companion venues
      (UNISWAP_V2-ETHEREUM/AAVEV3-OPTIMISM/EIGENLAYER/CURVE-ETHEREUM/MAKER/FRAX/DRIFT-SOLANA/KAMINO/JITO/MARGINFI, or
      their current canonical forms AAVE_V3-OPTIMISM/EIGENLAYER-ETHEREUM/MAKER-ETHEREUM/FRAX-ETHEREUM/KAMINO-SOLANA/
      JITO-SOLANA/MARGINFI-SOLANA) under the `swaps_ohlcv`/`dex_pool_swaps` data_type. The `chain` column is 100%
      populated fleet-wide for the current `dex_pool_swaps` rows (0/795 null) — the chain-propagation bug this todo
      describes is confirmed fixed, and the C0 full-hive migration (C0d, `canonical-migration-defi-20260618-180603`)
      evidently already re-derived/rewrote this data with the fixed code, superseding the specific 28,634+companion row
      count this todo cited from 2026-05-28. Both the venue naming (now flat, e.g. `UNISWAP_V3` not
      `UNISWAP_V3-ETHEREUM`) and the manifest's `data_type` field (now the raw ingest type `dex_pool_swaps`, not
      per-timeframe `swaps_ohlcv_{tf}`) have changed since this todo was written, consistent with the C2/C3
      canonicalisation todos in `instrument_availability_hive_canonicalisation_2026_07_21.md`-style migrations. Done
      when: post-reprocess `attempted_failed` for all listed venues → 0, verified against the live `_index` — **this is
      independently true today with no reprocess run**, so there is nothing left to execute against this todo's
      described scope. **New finding, filed separately** (not part of this todo — a different, currently-ACTIVE failure
      mode, not the old chain-column bug): 795 `dex_pool_swaps` `attempted_failed` rows exist TODAY across
      UNISWAP_V3/OPTIMISM (342), CURVE/OPTIMISM (338), TRADER_JOE_V2/AVALANCHE (73, already tracked),
      PANCAKESWAP_V3/BSC+ETHEREUM (17), UNISWAP_V4/ETHEREUM+POLYGON (12), UNISWAP_V2/ETHEREUM (5), VELODROME_V2/OPTIMISM
      (5), AERODROME_V3/BASE (1) — all
      `error_reason="All N cascade schemas     drifted/returned GraphQL errors for {venue}/{chain} (subgraph=...)"`,
      growing daily through 2026-07-27 (not a stale artifact). Same TheGraph subgraph-schema-cascade failure class as
      the already-tracked TRADER_JOE_V2 finding in `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md` —
      extended that doc's scope with a new todo rather than filing a duplicate issue. Source:
      `data_completion_defi_2026_07_15.md`

- [ ] [STRATEGY] P2. Build the interest-PnL A2 staking leg in strategy-service: wire the `carry_staked_basis`
      `STAKING_REWARD`/`CARRY` accrual leg to the `lst_yields` `exchange_rate`/`prev_rate` index ratio keyed off
      `cfg['lst_asset']`, mirroring the already-shipped E1 FUNDING-leg pattern (additive new param defaulting to None so
      all other callers stay byte-for-byte; quote-only existing path, no schema change). Explicit-zero the Aave-lending
      mismodel, keep honest-absence visible, add a real passive-parity test, run the 3-lens money-path review and
      hold-not-force-ship if anything is uncertain. Repo: strategy-service. Done when: the STAKING leg computes accrual
      from real `lst_yields` exchange-rate rows, the passive-parity test passes, all pre-existing callers are preserved
      byte-for-byte, `bash scripts/quality-gates.sh` is green, and the change ships to LDR via scoped
      `quickmerge.sh --agent --files` (prod-NAV recompute stays operator-gated, out of scope). Source:
      `lst_rate_honest_coverage_2026_07_21.md`

- [x] ✅ [BACKEND] P2. Phase 5 — wire the LIQUIDATION_CAPTURE archetype's paper-replay tick builder in strategy-service,
      mirroring the already-shipped Phase 3/4a/4b pattern. FIRST run the mechanical catalog-key-vs-engine pre-check
      (catalog `initial_config` keys emitted for LIQUIDATION_CAPTURE vs
      `LiquidationCaptureEngine.on_tick`/`REQUIRED_PARAMS`, per
      `defi_catalog_engine_config_key_contract_drift_2026_07_23.md`) and confirm the engine `on_tick` actually emits
      instructions (not a stub). IF buildable: add `_load_liquidation_capture_ticks()` in
      `strategy_service/cli/handlers/paper_run_handler.py` reading real per-day on-chain
      `liquidation_events`/`health_factor` feature data (`health_factor_trigger` threshold sourced from catalog config,
      not invented), add LIQUIDATION_CAPTURE to `_ENGINE_DRIVABLE_ARCHETYPES` behind a new satisfiability gate in
      `paper_universe.py` with a typed honest-skip reason on data absence, add unit tests (satisfiability gate,
      honest-absence, determinism). Repo: strategy-service. Done when: EITHER LIQUIDATION_CAPTURE is in
      `_ENGINE_DRIVABLE_ARCHETYPES`, its tick loader reads real liquidation_events/health_factor GCS features with
      per-row honest-skip, and `quality-gates.sh --no-fix` is green with new tests; OR, if the pre-check finds the
      engine is a stub/no-op or requires an undecided health-factor-trigger design decision, the todo lands a documented
      held-finding in the issue doc naming the exact blocker with zero fabricated wiring. **Sequence after batch2's
      paper_universe.py MEV-DOCS todo (same file).** Source:
      `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md` — **HELD-FINDING, 2026-07-31 (slot 11,
      backend_engineer).** Pre-check run: confirmed `on_tick` (`liquidation_capture.py:68`) is real logic, not a stub —
      but it structurally can NEVER fire from a paper-replay tick because BOTH catalog sources
      (`catalog_yield_defi.py::build_liquidation_capture()`, `archetype_slots_defi.py`'s `DEFI_SLOTS`) deliberately
      leave `debt_asset`/`underwater_address` empty on every row (genuinely per-event runtime facts, no static catalog
      row can encode them), and fresh-verified `orchestrator.py` still has no params-mutation API to inject them
      per-tick — unchanged from the source doc's 2026-07-23 finding. This is the todo's own "stub/no-op" honest-finding
      branch, not the buildable one. Zero fabricated wiring — did NOT add LIQUIDATION_CAPTURE to
      `_ENGINE_DRIVABLE_ARCHETYPES` or build a tick loader. Full evidence chain landed in the source doc's own Phase 5
      todo (now also flipped). No code shipped, batch2's `paper_universe.py` MEV-DOCS prerequisite confirmed already
      landed (`strategy-service@8d7c6549`).

- [ ] [DATA] P2. C6 Pyth `oracle_prices` historical backfill — launch a SPOT backfill VM running MTDS Pyth Hermes-API
      collection for the 2026-04-15→present gap window, writing ONLY into the canonical
      env-split/`pipeline_mode=`/`asset_group=defi` layout (never the legacy layout; C0 canonical structure is live).
      Safe-idempotent justification: SPOT + idempotent re-fetch, no GCS delete. Repo: market-tick-data-service. Done
      when: the consolidated `market-data-tick-defi` `_index` shows Pyth `oracle_prices` rows `captured` (or legit
      `empty_confirmed`) across the full 2026-04-15→present window with zero remaining gap days. Source:
      `data_completion_defi_2026_07_15.md`

- [ ] [VERIFY] P2. Grep-then-READ whether DeFi arb/carry net-of-gas cost (gas_price × gas_units — execution
      `estimate_gas` gas_units × the captured per-chain `gas_fees` price) is actually wired in any consumer: search
      strategy-service, execution-service, features-service and unified-trading-library for a gas_price × gas_units
      net-cost computation and READ each candidate consumer to confirm (0-hit ≠ absent). Repo: strategy-service
      (cross-repo audit — do NOT build the consumer inline). Done when: a written verdict with file:line evidence states
      definitively whether net-of-gas is wired; if absent, a `plans/active/issues/` findings-triage doc is filed for the
      strategy/PnL axis naming the missing gas_price × gas_units computation. Source:
      `defi_migration_audit_log_2026_07_24.md`

- [ ] [SCRIPT] P3. Regenerate the stale `adapter_contract_baseline.yaml` entries for the 2026-07-26 MTDS DeFi
      code-motion splits, two independently-verified sub-parts committed together: (a) `dex_pools_handler.py` (9→5) +
      new `_dex_pools_subgraph.py` (2→6) from the perf-bundle facade extraction — already grep-confirmed pure
      code-motion, zero calls lost (5+6=11=pre-split total), safe to regen; (b) `_defi_manifest.py` (43→42) + new
      `_defi_catalog_freshness.py` (6 calls, no prior baseline entry) from the merged sibling-slot
      `assert_defi_catalog_fresh` extraction (commit `08439787`) — FIRST verify via `git show 08439787` that the 6 calls
      moved out of `_defi_manifest.py` rather than being silently lost/duplicated (reconcile the −1 net drop against the
      6 in the new file before blessing); if any sub-part shows real lost calls, do NOT regen it — file a P1/P2
      regression issue and leave that WARN in place. Then run `check_adapter_contract_regression --regenerate-baseline`
      (quality-gates.sh 5.70/6 flow) scoped to `market-tick-data-service`, keeping the regen limited to these four
      confirmed-safe defi files (do NOT blanket-bless unrelated cefi/tradfi/solana_defi_drift entries in the shared YAML
      — coordinate/sequence with `defi_satellite_ao_dispatch_batch2_2026_07_26.md` line ~495's sibling solana_defi_drift
      regen since both rewrite the same file). Repo: unified-trading-pm (baseline YAML edit + commit) +
      market-tick-data-service (verification reads). Done when: `bash scripts/quality-gates.sh --no-fix` on
      `market-tick-data-service` no longer prints the ⚠️ "Adapter contract-call regression" for `dex_pools_handler.py`
      or `_defi_manifest.py`, the YAML diff is committed, and this issue doc's `status:` is flipped to `resolved` (or a
      regression issue filed for any unconfirmed sub-part). Source:
      `mtds_dex_pools_adapter_contract_baseline_stale_2026_07_26.md`

- [ ] [DATA] P3. Two read-only reconciliation checks for `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`,
      combined into ONE todo (both append findings to that doc's Progress Log — must not race): (a) reconcile the three
      independent `_DEFAULT_PROTOCOLS` lists in market-tick-data-service (`lending_indices_handler.py:176`,
      `risk_params_handler.py:107`, `liquidations_handler.py:149`) against each other and against `SUBGRAPH_IDS`
      (`unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py:62-217`) — produce a
      written mismatch report (which protocol appears in which list vs SUBGRAPH_IDS); (b) confirm whether
      `vault_share_price_handler.py` has actually run/been scheduled for FRAX-ETHEREUM (`_VAULTS["sFRAX"]`) by reading
      the live defi manifest (scoped read, no new whole-corpus walk) for FRAX-ETHEREUM under
      `data_type=vault_share_price` — genuine absence = a scheduling gap, not an enumeration gap. READ-ONLY: do NOT add
      `fluid` or any protocol to a handler without also wiring a real collector (would write dishonest zero-row manifest
      stamps). Repo: market-tick-data-service. Done when: both findings (the cross-list mismatch inventory + the
      FRAX-ETHEREUM vault_share_price row-count/`attempted_at` classification) are appended to the source doc's Progress
      Log with no handler code changed. Source: `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`

- [ ] [INFRA] P3. **[CROSS-AG: targets agent-orchestrator, not defi code]** Add an M3 `/done` verification exception in
      agent-orchestrator: when a cross-repo plan commit converts a referenced `- [ ]` todo into a non-checkbox
      `CANCELLED`/`SUPERSEDED` marker (per `task_template.md`'s remove-a-todo convention) within the verification
      window, accept `/done` (or an equivalent explicit-cancellation close) instead of hard-rejecting with
      `cross_repo_pm_file_touched_no_checkbox_flip` — which today forces a `/skip-current-task` with no way to record
      disposition. Repo: agent-orchestrator. Done when: the M3 check accepts a commit converting the referenced todo
      `- [ ]` → non-checkbox CANCELLED/SUPERSEDED marker without a `[x]` flip, with a regression test covering both the
      accepted-cancellation case and the still-rejected plain-no-flip case; `quality-gates.sh` green. Source:
      `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`

- [ ] [REGISTRY] P3. Tighten the defi POOL data-type validity grain from union-across-protocols to per-protocol in UAC
      `registry/capability_declarations/_defi.py` PROTOCOL_CAPABILITIES, so
      `valid_data_types_for_instrument_type("defi","POOL")` no longer seeds expected_unattempted
      `perp_funding`/`lending_indices`/`liquidations` for a pure-DEX pool (e.g. UNISWAP_V3) while still granting those
      data_types to perp-capable pools that legitimately produce them. Repo: unified-api-contracts. Done when:
      `valid_data_types_for_instrument_type("defi","POOL")` is protocol-scoped (a UNISWAP_V3 POOL yields only
      `dex_pool_state`/`dex_pool_swaps`; a perp-capable POOL still yields `perp_funding`), a new unit test proves the
      tightened per-protocol set, no impossible-combo regression, quality-gates.sh green. Source:
      `defi_migration_audit_log_2026_07_24.md`

- [ ] [SCRIPT] P3. Gate the `migrate_defi_full_v9_canonical.py:570` L1 `_safe_find(fs, {base}/{dir_name})` on a cheap
      prefix-existence probe (or drop it) so the migrator stops issuing a whole-bucket enumeration per
      `day=`-partitioned source bucket that has no top-level L1/raw_tick_data tree — but KEEP a fallback so a bucket
      that genuinely has an L1 tree is never silently skipped (data-loss guard). Repo: market-tick-data-service. Done
      when: the L1 find is guarded by an existence probe; a unit test proves both (a) a `day=`-only bucket skips the
      expensive scan and (b) a bucket with a real L1 tree still enumerates it; a date-scoped dry-run still completes
      0-errors; quality-gates.sh green. Source: `defi_migration_audit_log_2026_07_24.md`

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION, not batchable)

- **`issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`**: Declare HYPERLIQUID/ASTER in UAC
  `ALL_DEFI_VENUES` + `DEFI_VENUE_DATA_TYPE_CAPABILITIES`. batch2 (line ~341) dispatched this doc's OTHER todos
  (EULER_V2/Plasma) and explicitly excluded this one. The `honest_coverage_shard_dimension_model` confirmation only
  resolves the CLASSIFICATION intent (dual CEFI+DEFI listing is intentional), NOT whether declaring into UAC
  `ALL_DEFI_VENUES` double-counts the same on-chain rows across system-wide CEFI+DEFI denominators — an open
  UAC-registry-level axis ruling the operator must make. The doc's own last word (2026-07-21) still flags it as "a real
  follow-up."
- **`defi_migration_audit_log_2026_07_24.md` items 3, 5, 7, 8, 10 (STALE/INVERTED PREMISE)**: all five prescribe giving
  orphan data_types / handler writes DEDICATED buckets, but the dedicated→**shared** consolidation already SHIPPED
  (`defi_consolidated_closeout_2026_07_18.md`:194-195 — all kinds resolve `kind="tick-data"` on the single
  `market-data-tick-defi-prd`; the foundational v9 migration ran 2026-06-18). Drafting these as-is would RE-INTRODUCE
  the divergence the consolidation removed. They need an operator reconciliation of the item text against the shipped
  shared-bucket architecture, not a fresh migrate todo. (item 5's "gas in the could-exist denominator" sub-part is also
  an open design call — gas is chain-grain, not the instrument-universe grain of Track-3's 63.9M seed; item 10 folds the
  already-EXCLUDED item-2 Solana-source ruling, and DefiLlama's status as a canonical on-chain source is itself
  contested — batch2:143 migrated AaveRateImpact OFF the DefiLlama borrow field.)
- **`defi_migration_audit_log_2026_07_24.md` item 2 (SOURCE_PRIORITY Solana source) + item 9 (delete legacy buckets)**:
  item 2 is an operator "which Solana source is canonical" ruling (solana_rpc/helius/defillama); item 9 is a destructive
  legacy-bucket delete requiring operator sign-off per the GCS delete-safety HARD RULE. Item 1 (Era-B legacy retirement)
  is a large cascade-coupled UAC+MTDS registry+test drop — technically AO-eligible now its cefi+tradfi G4-apply gate
  cleared, but sizeable enough it warrants its OWN dedicated plan, not a batch todo.

## Deferred — conflict-gated / sequence-gated (re-check next iteration)

- **`lst_rate_honest_coverage_2026_07_21.md` E3 recursive-staking borrow leg**: builds ON TOP of todo 4 (A2 staking leg)
  in the SAME strategy-service `carry_staked_basis` accrual mechanism — drafting it as a sibling would race on the same
  file. Also still needs its own scoping step (Aave-oracle unblock alone is insufficient per the doc). Re-extract as a
  batch4 todo once todo 4 lands.
- **`data_completion_defi_2026_07_15.md` G6 Jupiter historical reconstruction**: GATED on G1 (Orca+Raydium pool-state
  backfill), which is operator-launched long-wall-clock and not scheduled by any covering plan; and the reconstruction
  approach itself (simulate Jupiter routing vs pool states, "algorithmically nontrivial") is an undecided
  research/design call. Unblock once G1 lands and the approach is ruled.

## Deferred — non-batchable orphans from Phase 1 (report only; need direct human action, not another batch)

These 9 orphaned docs carry ONLY non-batchable-taxonomy remaining work (per the per-doc Phase-1 classification) —
re-running the audit against them will keep reporting the same until a human acts:

- **`defi_venue_lst_rates_residual_2026_07_24.md`** — operator-gated: bare-`SUSHISWAP` classic-vs-V3 alias is a
  data-semantics ruling (same class as the already-made SUSHISWAP/UNISWAP factory-version call).
- **`defi_expected_unattempted_seeder_design_2026_07_26.md`** — operator-gated: IS the standing human plan (assigned_vm:
  NA) batch2 designated as successor to cancelled C8; P0 is an [OPERATOR] capability-vs-collectibility reconciliation,
  P1-P3 BLOCKED-OPERATOR. Becomes AO-eligible only after the operator resolves P0.
- **`issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`** — human-only/too-large:
  CARRY_STAKED_BASIS delete-vs-re-leg is a strategy-domain judgment; the generator/UI structural-skew item "needs its
  own plan"; the UI resync is blocked on both.
- **`issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`** — time-gated: sole remaining item (re-run G2 gate)
  is blocked on `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` (owned by
  `data_completion_defi_2026_07_15.md`); 13 dispatches already bounced on it. Already in batch2's time-gated Deferred.
- **`issues/defi_five_never_captured_venues_fix_2026_07_22.md`** — human-only: correcting/deleting MORPHOVAULTS
  `GTUSDCP.parquet` garbage share_price row is a prod-bucket data mutation, operator-gated per the GCS
  delete/mutate-safety protocol.
- **`issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md`** — human-only: Todo 4 is a `[DECISION]`
  remediation ruling (accept legacy artifact vs targeted manifest correction), conditionally gated on todo 1's
  now-covered outcome.
- **`issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`** — human-only: `[DESIGN] P3`
  IS-catalogue-completion-signal retry-sweep is a design call (pub/sub vs sentinel-file vs other; which service owns
  it). Needs a design session first, then a scoped todo.
- **`issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`** — human-only: regenerating/reconciling
  the 57 `unified-api-contracts/openapi/prospectus/*.md` generator outputs spans many axes unrelated to DRIFT removal —
  needs a human design decision on how to reconcile generator vs committed copies before any worker todo is
  determinable.
- **`archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md`** — human-only: steps 2-4 (new MTDS
  chain-field collectors for ltv/liquidation_threshold/reward_rate/health-factor inputs + recompute) are "genuinely new
  scope (upstream collection)... size them as their own work" per the doc author (now tracked in
  `features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`; the doc's own one todo — delete + register —
  shipped 2026-07-30, features-service@d8a643a0, doc archived). Already in batch2's human-only Deferred.

## Note — items already covered (skip_covered, NOT re-drafted)

Phase-3 conflict-check confirmed these 4 items are already claimed by a covering plan (would be duplicates):

- `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md` item 4 (MORPHO absence intentional-check) → owned by
  `defi_expected_unattempted_seeder_design_2026_07_26.md`'s [OPERATOR] P0.
- `data_completion_defi_2026_07_15.md` C5 phantom-grid delete → subsumed by the C0/track01 canon walk + data-status
  dedicated-index repoint.
- `data_completion_defi_2026_07_15.md` instruments-store-defi canonical-form walk → owned by the active cross-cutting
  `instruments_manifest_canonicalisation` plan.
- `data_completion_defi_2026_07_15.md` FLAG2 `_BUCKET_CATEGORY_OVERRIDES` → already RESOLVED at
  `defi_dedicated_bucket_shared_migration_2026_07_13.md`:257-268 ([x] ✅ deployment-api).

## Note — archival candidates (archivable_now — a separate archival todo, not a batch candidate)

- `issues/e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md` — Final report (2026-06-17) declares done state;
  all 6 BUGs fixed; sole open item self-migrated to `perp_funding_data_semantics_and_cadence_2026_06_16.md`. Archive.
- `issues/mtds_perp_funding_backfill_hang_2026_07_14.md` — all 6 todos [x] with evidence; residual spun to
  `mtds_retry_safe_default_audit_2026_07_14.md`. Archive (batch2 already flagged this one archivable_now).

## Note — 1 mistag (exclude_cross_cutting)

- `archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` — tagged `asset_group: [defi]`
  but real content is a fleet-wide QG STEP 5.101 infra/CI issue, not defi-specific. Should be retagged `cross-cutting`
  or `infra` (batch2 already flagged this as a mistag Note).

## Deferred work — migrated to: N/A (this plan itself is not deferred/migrated)

This plan's own `## Deferred — ...` sections each cite their source issue doc directly as the successor reference; no
part of this plan was migrated elsewhere.

## Progress Log

- **2026-07-26** — Drafted autonomously by the scheduled `ag_closeout_auditor` (slot 15, tranche=defi) via the
  `/ag-closeout-audit` skill. Phase 1: 59 defi AG-primary docs classified by a 59-agent Workflow (sonnet) → 39
  archivable-after-planned-work, 15 orphaned_partial, 2 orphaned_never_touched, 2 archivable_now, 1 exclude. Phase 3: 8
  AO-eligible orphan docs conflict-checked by an 8-agent Workflow (opus) → 13 draft / 4 skip_covered / 8 conflict_park;
  merged 2 same-source read-only report todos into todo 9 → **12 todos**. `status: draft` — awaits operator approval to
  flip to `active`.
- **2026-07-27 (slot-11)** — Worked D1's blocking issue
  (`features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md`). Shipped a candidate fix for finding 1 —
  `unified-trading-library@06190d77` bounds `read_manifest_rows()` to the slim, filtered manifest-read path — plus
  regression coverage. **D1's checkbox stays UNFLIPPED**: the fix is not yet end-to-end validated (needs the UTL wheel
  release to reach features-service before the repro VM can confirm it resolves the hang/OOM). Operator-confirmed
  (BLK-adabd51f, option B) this session's deliverable is the shipped candidate fix + the issue doc's handoff section
  (repro command + pending gate + next steps) — do not idle-hold a slot on the wheel release; a future dispatch resumes
  the validation.
- **2026-07-31 (slot-5, data_engineering craft)** — Resumed D1's `returns` leg from slot-2's handoff (3 timestamp bugs +
  a found-but-unfixed 4th symbol-separator bug). Shipped the 4th fix (`features-service@7e10172c`, verified against real
  CHAINLINK+PYTH raw data, 6 new regression tests, full QG green) —
  `delta_one_passthrough_symbol_filter_slash_underscore_mismatch_2026_07_31.md`'s P1 recommended-decision item is now
  flipped (slot-8 independently confirmed the same fix via a concurrent `git pull --rebase` reconciliation, no duplicate
  shipped). Relaunched the real verification run (`features-delta-one-defi-20260731-025149`,
  `FEATURE_GROUP=returns FORCE=1`, same clean window `2023-05-12..2023-10-31`) to confirm end-to-end — caught and fixed
  a stale-tarball launch first (deleted the mis-launched VM within seconds, republished, relaunched clean; full recipe
  in the symbol-filter issue doc's Progress Log). **The symbol-fix is confirmed working**: range-load went from the
  pre-fix `27/51` to `51/51` real instruments matched. But the run still produced
  `Completed 0/51 instruments for returns` — a **5th, distinct, downstream bug**:
  `BufferManager.calculate_buffer_days()` computes only a 1-2 calendar-day lookback window from
  `FEATURE_GROUP_LOOKBACK["returns"]=100` periods (correct for CEFI's dense 15s candles, wrong for DEFI's sparse
  pass-through event ticks — confirmed via direct repro: 945 real rows genuinely exist across the full window, but the
  per-date window only admits ~4-12 of them, never reaching the 100-row sufficiency threshold, deterministically on
  every date). Filed `delta_one_passthrough_lookback_buffer_too_short_for_sparse_ticks_2026_07_31.md` with full repro
  evidence + 3 candidate fix directions (did not patch `buffer_manager.py` myself — it's shared CEFI/TRADFI/DEFI code
  where the current formula is correct for real candle data; a blind fix risks regressing that). **D1's checkbox stays
  UNFLIPPED** — the `returns` leg still cannot complete until this new buffer-sufficiency bug is fixed, and `funding_oi`
  remains separately blocked on the HYPERLIQUID OI-absence operator decision
  (`defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`). Real forward progress this session: 2
  of what is now a confirmed 5-bug chain are fixed and verified; the remaining blocker is precisely scoped with
  reproducible evidence for the next dispatch.
- **2026-07-31 (slot-10, data_engineering craft, re-dispatch) — status-only check, no new bugs, no relaunch: confirmed
  both of slot-11's healthy production VMs are still alive and making real measured progress; both standing blockers are
  unchanged.** Re-read this todo's own text fully before touching anything (per the "lesson for future dispatches" note
  above). Live-verified (not just log-tail) both VMs via `gcloud compute instances list` + GCS `run.log` reads:
  `features-delta-one-defi-20260731-094100` (`2023-05-12..2023-10-31`) has produced 368 real
  `Completed N/51 instruments for returns` lines with zero errors/tracebacks, steady ~20-25s cadence with no gaps
  through 11:21 UTC; `features-delta-one-defi-20260731-110727` (`2023-11-01..2026-07-22`) passed lookback validation
  (51/51 instruments) and is mid-candle-load for its buffered range, heartbeating cleanly with no errors through 11:21
  UTC. Neither shows any sign of the resolved OOM/hang class or the fixed timestamp/symbol/buffer bugs recurring.
  Checked both blocking issue docs fresh (not from memory):
  `delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md` (blocks the remaining `2022-11-01..2023-05-11`
  ~6-month gap in the `returns` leg) is still `status: open`, `assigned_role: backend_engineer` — needs a profiler/local
  repro, correctly out of data_engineering craft scope for a backfill session.
  `defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md` (blocks the entire `funding_oi` leg) is
  still `status: open`, `[OPERATOR]`-gated — HYPERLIQUID structurally never carries `open_interest`, needs a repo-owner
  adapter-extend-vs-calculator-relax ruling. Did not relaunch or touch either blocked leg (deterministic, already
  exhaustively reproduced by 6+ prior dispatches). **D1's checkbox stays UNFLIPPED** — did not duplicate any
  already-exhausted work this dispatch; the two production VMs are the only forward motion in flight, self-shutting-
  down on completion (SPOT, idempotent). **For the next dispatch**: before relaunching anything, verify these two VMs
  reached `DEPLOYMENT_COMPLETED exit_code=0` (VM absence from `gcloud compute instances list` + a matching completion
  entry under `gs://deployment-scripts-central-element-323112/deployments/archive/2026-07-31/`) — if both completed
  cleanly, the `returns` leg's real coverage is then `2023-05-12..2026-07-22` (the vast majority of the true
  `2022-11-01..2026-07-22` window), with only the ~6-month gap left blocked on Bug B. The checkbox still cannot flip
  until BOTH the 6-month gap (needs Bug B's fix) and `funding_oi` (needs the operator ruling) clear — this todo remains
  a strong candidate for parking (`priority: 999` + a false prerequisite gated on both linked issue docs resolving, per
  slot-16's still-unactioned recommendation above) until either external blocker moves.
- **2026-07-31 (slot-4, data_engineering craft, re-dispatch) — Bug B's fix landed since slot-10's check; launched the
  previously-blocked 6-month gap; the other 2 production VMs remain healthy; `funding_oi` still correctly untouched
  (operator-gated).** Re-read this todo's own text + both linked issue docs fresh before touching anything (per the
  standing "lesson for future dispatches" note). Found
  `delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md`'s `[BACKEND]` P1 is now `[x]` DONE
  (`features-service@f8e21361`+`b1652b59`, shipped by slot-14 since slot-10's dispatch — root-caused to
  `_build_captured_index()` decoding the whole 27.4M-row DEFI manifest with no `filters=`, fixed with a bounded
  row-group pushdown) — this unblocks todo 2 (the actual gap backfill), and separately confirmed
  `delta_one_dependency_checker_ignores_passthrough_feature_group_2026_07_31.md`'s `[BACKEND]` P2 (Bug A, the preflight
  false-negative for pass-through feature groups) is ALSO now `resolved` (`features-service@f57d11ae`, slot-7) — so the
  gap backfill no longer needs `--skip-dependency-check` at all. Live-verified (not from memory) the 2 standing
  production VMs (`094100`, `110727`) are both still `RUNNING` with clean, error-free logs (094100 processing its
  window's final days `2023-10-23..2023-10-31`; 110727 mid-window through `2026-07-22`) — did not touch either. Launched
  the gap backfill
  (`--feature-family delta_one --asset-group DEFI --feature-group returns --start-date 2022-11-01 --end-date 2023-05-11 --launch-mode full`,
  no skip-flag needed): first attempt (`features-delta-one-defi-20260731-132319`) flagged 4 STALE tarballs
  (features-service/UAC/UTL/deployment-service) by the launcher's own freshness check — deleted it within seconds
  (confirmed mine, zero real writes, genuinely stale per the check's own SHA diff) rather than let it run pre-fix code.
  Republish hit the known `deployment-service` missing `.venv` trap (`ModuleNotFoundError: deployment_service`) —
  recreated it (`uv venv .venv && uv pip install -e .`) per the established recipe. Relaunched (`-132653`); the
  freshness check then flagged `unified-trading-library` alone as stale — a _different_ slot (14) had landed
  `unified-trading-library@6c0ca59b` (the sibling UTL-side `get_captured_instruments()` unfiltered-manifest-read fix,
  same OOM class, same call path this exact backfill exercises) in the few minutes between my two launch attempts.
  Deleted + republished + relaunched a 3rd time (`features-delta-one-defi-20260731-132937`) —
  `lc_verify_tarball_freshness: all 5 tarball(s) current.` Live-confirmed healthy at the 60s mark: VM `RUNNING`, no
  crash. **Not yet confirmed complete as this entry is written** — a future check (or this same dispatch, later) should
  verify real `Completed N/51 instruments for returns` lines with no errors/runaway-RSS pattern, then confirm
  `DEPLOYMENT_COMPLETED exit_code=0` before treating the gap as filled. **Checkbox still cannot flip**: even if this gap
  backfill completes cleanly, `funding_oi` remains fully blocked on
  `defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`'s `[OPERATOR]` P2 (HYPERLIQUID
  structurally missing `open_interest` — a repo-owner design call, correctly not attempted here). Flipped
  `delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md`'s todo 2 to in-progress-not-done (VM launched,
  not yet verified).
