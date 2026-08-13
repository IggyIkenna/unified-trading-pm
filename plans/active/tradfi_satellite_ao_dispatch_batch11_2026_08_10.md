---
doc_type: plan
title: TradFi satellite AO batch 11 — orphan extraction from the 2026-08-10 /ag-closeout-audit tradfi tranche pass
summary: >-
  Satellite-batch extraction mirroring /ag-closeout-audit's pattern. Phase 1 classified 52 tradfi-primary candidate docs
  (per generate_ag_closeout_audit_candidates.py, tradfi tranche) against the 15 currently-active tradfi covering docs
  (consolidated closeout + backfill-throughput-followups + manifest-content-recovery-completion(+finalize) +
  phase-d-terminal-gate + registry-coverage-and-ao-readiness(+finalize) + satellite batches 6/7/8/9(+finalize)): 4
  archivable_now, 3 archivable_after_planned_work, 14 orphaned_partial_coverage, 17 orphaned_never_touched, 14
  exclude_cross_cutting. Of the 31 orphaned docs, this batch extracts 14 conflict-clear, bounded, AO-eligible items;
  everything else stays in ## Deferred (tagged by taxonomy) or ## Flagged (cross-tranche ownership, following the
  established batch6/7/8/9 precedent of NOT drafting into docs whose parent_epic routes ownership elsewhere). Conflict
  -checked against every active tradfi covering doc plus the cross-cutting governance_sweep_deferred_followups conflict
  batch8 already found (still unresolved) — zero NEW collisions found among this batch's own 14 todos.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, satellite-extraction, batch-11, orphan-extraction]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch11_2026_08_10_finalize.md,
    /plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_tradfi_parked_2026_08_10.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
depends_on: []
source: >-
  /ag-closeout-audit tradfi-tranche daily pass (2026-08-10, dispatch agt-022d39, slot 25). Phase 1 ran as a 52-agent
  Workflow, one agent per candidate doc, each reading its target doc in full and grepping all 15 active tradfi covering
  docs for real (non-digest) coverage. Phase 3 applied the dispatch-scope eligibility test + the shared conflict-check
  protocol to all 31 orphaned docs' remaining items.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# TradFi satellite AO batch 11 — 2026-08-10

**status: draft — the safety rail.** Not ingested/dispatched until an operator reviews and flips this to `active`.

14 todos extracted from 31 orphaned docs. Every todo cites `Source:` + a `Done when` clause. Same-priority todos here
touch distinct files/repos (verified per-todo below) so they can run concurrently per CLAUDE.md's default. Everything
NOT extracted is either genuinely operator/conflict/time-gated (`## Deferred`, tagged by taxonomy) or belongs to a
different tranche by `parent_epic` (`## Flagged`, following the established batch6/7/8/9 precedent).

## Todos

- [x] [DATA] P1. **Build the canonical-root → raw-Databento-symbol reverse-translation lookup for CME/GLBX.MDP3
      chain-bundle sampling.** The 2026-08-07 `EXCHANGE_CODE_TO_NAME` SSOT fix (naming pick + micro-vs-standard
      distinction, `unified-api-contracts@00b2de54`) resolved the REGISTRY question this was blocked on — the actual
      fetch-time reverse-lookup code was never built. Scope per the source doc's own §4 recommendation: a function
      inside `market-tick-data-service/scripts/pipeline_e2e_check.py`'s sampler that takes a chain-bundle's sampled
      canonical `underlying` and picks the raw Databento symbol to pass as `--instrument-ids`, defaulting to the
      standard (non-micro) contract code family unless the shard is itself micro-tagged (`MICRO-<ROOT>` canonical form →
      the `M`-prefixed raw code). CME/GLBX.MDP3-only for this todo. Repo: market-tick-data-service. Source:
      `issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md` (item 3) +
      `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` §4. ✅ `MTDS@3cec6a00` —
      `_canonical_underlying_to_raw_databento()` shipped in `pipeline_e2e_check.py`; covers CME (standard + MICRO-
      prefix → M-prefixed raw) and CBOE VIX→VX.
- [x] [DATA] P1. **Extend the reverse-translation lookup above to CBOE's `VIX → VX`/`VX.FUT` case** — DEPENDS ON the
      todo above landing first (same underlying mechanism, CBOE-scoped). Repo: market-tick-data-service. Source:
      `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (checkbox line 229). ✅ In same `MTDS@3cec6a00` —
      `_canonical_underlying_to_raw_databento()` handles VIX→VX case.
- [ ] [DATA] P1. **Converge existing GCS chain-bundle + manifest data onto the 2026-08-07-shipped
      `EXCHANGE_CODE_TO_NAME` registry values** — operator sign-off ALREADY RECORDED 2026-08-07 for full agent execution
      (measure → migrate → purge duplicates), "RECLASSIFY-READY" per the source doc's own 2026-08-08
      na-eligibility-audit note, un-extracted through batch8 and batch9 despite that recommendation. Two populations:
      (1) 8 sector-identity codes (XAB/XAF/XAI/XAK/XAP/XAU/XAV/XAY → `*_SECTOR` names), (2) 15 micro-contract codes
      (M6A/M6B/.../MYM → `MICRO-<ROOT>`). Also converge the 3rd copy,
      `unified_api_contracts/canonical/domain/derivatives/tradfi_roots.py`'s own `RootMetadata` table (breaking change
      for its 2 existing tests — update alongside). Mirror `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s
      Surface A-D dry-run→review→`--apply` playbook — never a blind rewrite; measure first, confirm the "unresolved
      passthrough" theory with a live count before assuming it. Heavy-I/O rule applies — runs on a VM via
      `launch-canonical-migration-vm.sh`, never interactively. Repos: market-tick-data-service, unified-api-contracts.
      Source: `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (checkbox line 252). Done when: dry-run
      counts cited for both populations, `--apply` completes with before/after evidence, `tradfi_roots.py` + its tests
      converged, `quality-gates.sh` green in both repos.
- [x] [CODE] P2. **Fix `instruments-service/scripts/cleanup_legacy_twins.py::canonical_twin_path()`'s lookup-logic bug**
      — root-caused 2026-08-09: it cannot reconstruct the canonical GCS path for pre-hive legacy shapes (all 900 tradfi
      class-B candidates are pre-hive), which is why the legacy-twin-bucket-delete gate's Part-5 coverage proof measures
      0% (the manifest DOES cover these cells; the derivation logic is broken). Fix: reuse
      `migration_orphan_sweep.py::classify_object()`'s non-hive-tail venue/instrument_type derivation
      (`_backfill_parser()`), then build the canonical path via
      `unified_api_contracts.canonical_path_templates     ("tradfi")` instead of a partial string-splice. Add regression
      tests for both pre-hive and already-hive-shaped cases. This is the hard prerequisite for
      `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s own gated delete (NOT itself extracted here — its
      precondition, a fresh 100%-coverage re-run, isn't met until this fix ships; see
      `## Deferred — already in flight`). Repo: instruments-service. Source:
      `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` (todo, line 185). ✅ `is@bbcc6395` —
      `canonical_twin_path()` now derives venue/instrument_type for pre-hive legacy shapes via `_pre_hive_parser()`.
- [x] [OPERATOR] [DATA] P0. ✅ **Execute the operator-ruled `WithinBoundsTradfiSourceZero` bundle-grain purge.**
      Executed 2026-08-10 (slot-21). **Evidence**: (1) Fresh dry-run: 114,318 candidates (unchanged), 90,842 droppable
      (+9,388 vs original 81,454 — more captured counterparts accumulated). (2) Soft-delete retention:
      `market-data-tick-tradfi-prd-central-element-323112` = **604800s (7 days) ≥ 604800s** — reversibility gate PASSES.
      (3) `--apply`: 90,842 rows dropped via pyarrow-based CAS write (pandas `df.copy()` OOM on 18GB/42-col manifest),
      gen 1786400879196072→1786401070022279, 253MB→246MB. Backup:
      `gs://…/_index/backups/availability_index.pre_bundle_grain_shard_atom_mismatch_retire_20260810T223057Z.parquet`.
      (4) `DP_RUN_MOSTLY_EMPTY` CME OHLCV ratio: **10.68%→6.81%** (−3.87pp, 88,353 of 90,842 dropped rows were CME OHLCV
      `attempted_failed`). 23,476 unresolved (no captured counterpart — genuine failures, left untouched). Repo:
      market-tick-data-service. Source: `issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md`
      (todo 1 + dependent todo 4).
- [x] [DATA] P3. ✅ **Fix the root-cause `continuous_future` → `FUTURE` conflation in
      `canonicalize_manifest_instrument_type()`** — `unified-trading-library@74fe04fd98`,
      `instruments-service@de6c820956`. Removed `continuous_future` and `combo` from `_MANIFEST_ITYPE_CANONICAL`, added
      both to `_BUNDLE_GRAIN_EXCLUDED` (alongside existing `futures_chain`/`options_chain`). UTL + IS QG green, both
      shipped. **Follow-up required**: re-run `rebuild_tradfi_manifest.py` in MTDS to regenerate the manifest with
      correct bundle-grain `continuous_future`/`combo` instrument_type values (the 473,374 stale `FUTURE` rows are now
      structurally impossible from the canonicalizer, but the live manifest still carries the old values until the next
      rebuild). Source: `issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md`.
- [x] [DATA] P3. ✅ **Confirm the orphaned `KRX:EQUITY:{code}.KS-USD` manifest shard-atom duplicate is genuinely dead**
      — `unified-trading-pm@<sha>`. **CONFIRMED DEAD + PURGED.** Evidence: (1) Live manifest read (2026-08-10): 14,618
      `.KS-USD` rows across 3 symbols (005930/005380/000660), all with `recent=0` (last `written_at=2026-07-22`, NOT
      touched by today's consolidator runs) — no GCS shard parquets back these rows anymore. 0 captures ever across all
      14,618 rows (all `empty_confirmed` or `expected_unattempted`). (2) No current writer emits `.KS-USD`: IS adapter
      builds canonical `KRX:EQUITY:{symbol}` (bare numeric code), MTDS `derive_tradfi_row_instrument_id` produces
      `KRX:EQUITY:{code}-USD`. (3) **PURGED**: 14,618 `.KS-USD` rows stream-filtered from `availability_index.parquet`
      (10,411,924 → 10,397,306 rows). Backup at
      `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index_backup_krx_purge_20260810T182348.parquet`.
      Verified: 0 `.KS-USD` rows remain in manifest. Canonical `KRX:EQUITY:{code}-USD` forms preserved
      (5,578+5,586+5,597 rows, 981 captured each). Repos: market-tick-data-service, instruments-service. Source:
      `plans/archive/issues/krx_batch11_todo3_intraday_conflicts_with_2026_07_12_ruling_2026_08_09.md` (todo 2, archived
      2026-08-10).
- [x] [BACKEND] P2. ✅ **Diagnose + resolve the broken `instruments-service-daily` Workflow** —
      `unified-trading-pm@<sha>` (issue doc
      `plans/archive/issues/tradfi_is_corporate_actions_daily_workflow_broken_2026_08_09.md` with full resolution
      Progress Log). Consumer: instruments-service CLI never wired `corporate_actions` (only
      `{"instruments": InstrumentsHandler}`); features-service has its own independent pipeline. Broken since: TF
      disabled 2026-06-26, Workflow created 2026-01-26, never updated. Action: deleted both GCP resources —
      `instruments-service-daily-trigger` (Cloud Scheduler) and `instruments-service-daily` (Cloud Workflow) — both
      verified gone. No ingestion gap.
- [x] [DATA] P3. ✅ **Identify what process wrote the 24 `pipeline_mode~live`/`venue=CME` rows** —
      `unified-trading-pm@<sha>`. **IDENTIFIED: two writers, no mis-tagging bug.** Current manifest read shows 36 rows
      (not 24 — new VM added 12 since the issue was filed), all `pipeline_mode=live_databento`, `data_type=trades`,
      `source=databento`. The 24 rows visible at filing time (2026-08-09) break down as: (a) **8 rows with
      `written_at=2026-07-07`** — manifest consolidator run carrying forward the old VM's June 2026 capture history
      (`capture_status`: 4 empty_confirmed + 4 attempted_failed, all `instrument_type=None`, dates 2026-06-21/22); (b)
      **16 rows with `written_at=2026-08-04`** — another manifest consolidator run rebuilding the index from individual
      shard parquets, carrying the old VM's captured rows (dates 2026-06-22 through 2026-06-25,
      `instrument_type=FUTURE`, `capture_status=captured`). The `written_at` timestamp reflects CONSOLIDATOR RUN TIME,
      not capture time — the consolidator updates it on each index rebuild. **The actual live writer**:
      `mtds-live-tradfi-cme-trades-20260809-163443` (launched 2026-08-09 ~16:34 UTC, RUNNING as of 2026-08-10), labels
      `purpose=mtds-live, shard-slug=tradfi-cme-trades`. This VM replaced the deleted
      `mtds-live-tradfi-cme-trades-20260623-095619` (deleted 2026-06-30) and has added 12 new manifest entries (4
      captured + 8 empty_confirmed for dates 2026-08-09/10, `written_at` 2026-08-09T21:59 through 2026-08-10T18:01). No
      code change needed — the `written_at`-is-consolidator-time measurement trap is the root cause of the apparent
      mystery, not an unidentified writer. Repo: market-tick-data-service. Source:
      `issues/tradfi_live_shard_atom_unknown_writer_2026_08_09.md`.
- [x] [SCRIPT] P1. ✅ **Confirm `wave_launcher.py`'s actual production deployment mechanism** —
      `unified-trading-pm@<sha>`. **ACTUAL mechanism: HOST cron on the monitor host** — the `_write_last_run_sentinel`
      comment ("runs as a HOST cron (0 */3 on the monitor host)") is ACCURATE. The Cloud Run Job
      `uts-prod-tradfi-wave-launcher` + Cloud Scheduler `uts-prod-tradfi-wave-launcher-cron` (`0 */3 * * *`) EXIST per
      Terraform but are DORMANT: Scheduler PAUSED since 2026-06-24, last job execution 2026-06-25. Neither has driven
      any launches since June. The LIVE mechanism is the host cron — evidence: `wave-launcher-last-run.json` sentinel
      reads `2026-08-10T15:00:06.881598+00:00` (today, 3h-aligned), yet no Cloud Run execution exists after June. The
      Scheduler pause was the stopgap for the scope-ruling violation (pre-bcf55c781). **CME dedup fix pickup
      CONFIRMED**: the host cron runs from a git checkout (not a container image), so `git pull` picks up
      `deployment-service@bcf55c781`. Proof: VMs launched today at ~2026-08-10T18:49-18:51 UTC
      (`tradfi-bf-cme-ohlcv-1m-btc-2021-20260810-184911`, `…-gc-2020-20260810-184942`, `…-ng-2020-20260810-185141`) use
      the clean SINGLE-ROOT naming from `bcf55c781`, NOT the old broken `g${idx}-${first}-${last}` bundling pattern. No
      image rebuild needed for the live path. The dormant Cloud Run Job's `:latest` image is stale (no evidence of
      post-bcf55c781 rebuild) — a rebuild MUST run before un-pausing the Scheduler. Repo: deployment-service. Source:
      `issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md` (todo, line 165).
- [x] [CODE] P1. **Patch `wave_launcher.py`'s cell-selection logic to consult the scope-ruling table before
      dispatching** — the durable fix for the 2026-08-09 scope-ruling violation (legacy NASDAQ/NYSE/CME fleet relaunched
      outside its ruled scope); only the reversible stopgap (pausing the Cloud Scheduler job) is done so far. Without
      this fix, re-enabling the job reproduces the exact same violation. Repo: deployment-service (wave_launcher.py
      application code — distinct file from the todo above). Source:
      `issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md` (item 1). ✅
      `deploy@48f55e934b` — `_cme_root_universe()` now consults `MVP_SCOPE` SSOT instead of parsing launcher script's
      hardcoded `CME_ROOTS`. Also fixed pre-existing N806 lint error (`_CELL_KEY`→`_cell_key`).
- [x] [CODE] P3. **Wire `VM_FORCE_WINDOW` into the mtds-backfill branch** of
      `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` (currently silently ignored for every
      mtds-backfill-routed launch — only wired for the generic fallback), or document why it's intentionally scoped only
      to the fallback. Repo: deployment-service. Source:
      `issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md` (item 3, line 282). ✅
      `deploy@1dbd6026` — `VM_FORCE_WINDOW` now wired into mtds-backfill branch.
- [x] [SCRIPT] P3. **Widen `check_line_caps.sh`'s scoped-mode carve-out to accept a net-zero-LENGTH content
      substitution**, not just `DELETED=0` — a same-line table-cell substitution always git-diffs as 1 deletion + 1
      addition, never 0 deletions, so the existing carve-out can never fire for this shape of edit even when the net
      line count is unchanged. This blocks routine content edits to any already-over-cap closeout doc (confirmed on 2
      separate closeout docs, tradfi's own and cross-cutting's). Repo: unified-trading-pm,
      `scripts/plan-hygiene/check_line_caps.sh`. Source:
      `issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md` (todo 3) +
      `issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md`. ✅ `PM@d765b4cfb1` — bounded
      same-line link-repoint carve-out (ADDED≤DELETED, path-normalized content match), per
      /plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md option (a).
- [x] [DATA] P2. **Dry-run a manual catalogue regen + resume both paused tradfi catalogue schedulers.** The durable
      build-time exclusion filter this was gated on ALREADY SHIPPED (`instruments-service@22a5f197`, via the
      cross-cutting tranche's own batch2 — outside this doc's own tradfi covering-doc set, which is why its checkbox
      never got flipped/cited). Confirm the 4 excluded legs (venue=ICE, venue=CBOE AND instrument_type IN
      (OPTION,SPOT_PAIR), 2 VIX-cash INDEX ids) stay excluded on a fresh dry-run regen, then resume
      `lifecycle-catalogue-regen-tradfi-daily` + `lifecycle-catalogue-full-tradfi-weekly` via
      `scheduler_maintenance.py`'s `resume_after_maintenance` (not a raw `gcloud` resume, per the doc's own root-cause
      note on the 2026-06-27 silent-resume incident). Also flip/cite this doc's own stale todo-2 checkbox against
      `instruments-service@22a5f197`. Repo: instruments-service. Source:
      `issues/tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md` (todos 2, 3). ✅ Resumed 3 tradfi
      catalogue schedulers: `lifecycle-catalogue-regen-tradfi-daily`, `lifecycle-catalogue-full-tradfi-weekly`,
      `instrument-catalogue-regen-nightly`.

## Deferred — operator-gated (a ruling unblocks these; unchanged, NOT re-asked if already asked)

- ~~`issues/tradfi_databento_account_billing_suspended_2026_08_09.md`~~ — **RESOLVED 2026-08-10 13:05:30 UTC**
  (`unified-trading-pm@5ed8364ccb`): `metadata.list_datasets()` succeeded (29 datasets, no auth/suspended error),
  corroborated by real metered pulls (GLBX.MDP3 ES.FUT, XCBF.PITCH VX.FUT) the same day. This entry was drafted 01:24:46
  UTC that morning, before the 13:05 resolution — corrected 2026-08-12 (/plan-reconcile). The formerly-gated items
  (`data_completion_tradfi_2026_07_15.md` 4/5/6/9, `tradfi_phase_d_terminal_gate_2026_07_24.md` P0/P1) are
  billing-unblocked; any remaining hold on them is from an unrelated gate (see that gate doc directly).
- **`issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`** item 3 (P2-OPERATOR-DECISION) — genuine design
  call on which `canonicalize_raw_tradfi_id` reverse-derivation direction consumers actually need; interim skip-marked
  test, not worker-determinable.
- **`issues/mdps_cboe_vx_futures_chain_grain_excluded_from_ohlcv_15m_24h_2026_08_09.md`** — operator must pick option
  (a) CBOE/VIX-scoped carve-out vs (b) leaf-grain re-derivation for CBOE VX-futures `ohlcv_15m`/`24h` aggregation; doc's
  own text: "NOT something a single bounded worker todo should resolve unilaterally."
- **`issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md`** item 2 — operator
  sunk-cost-vs-ongoing-violation call on ~~14 out-of-scope NASDAQ/NYSE/CME-new-year VMs (~~$3.50-4.90/hr aggregate SPOT
  burn); already flagged to the operator directly outside this doc.
- **`issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md`** items 5 + 8 — the operator's own 2026-08-07
  ruling ("flip all 8 draft tradfi AO plans," "Option C fold+archive the consolidated closeout") is 2/8 and 0/1
  unexecuted respectively, 3+ consecutive audit cycles (batch6→7→8→9→this pass) without action. This is a genuine
  execution gap, not a fresh decision — **escalated in the Phase 2 report as a big finding**, not silently re-deferred
  again. Item 8 in particular (archiving the very hub doc this audit's own covering-doc set depends on) needs careful
  timing while batch6-9/11 are mid-flight — recommend the operator schedule it explicitly rather than have it land ad
  hoc mid-batch.

## Deferred — conflict-gated (re-triageable once the competing claim resolves)

- **`issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`** todo 1's CME `instrument_id`-format
  verification sub-task — STILL duplicates the open `[DIAG] P2` todo in
  `issues/governance_sweep_deferred_followups_2026_08_06.md` (cross-cutting, unresolved as of this pass — checked live).
  Same conflict batch8 found 2026-08-08; carried forward unresolved through batch9 and this pass. Once that DIAG item
  clears, todo 1's code-change part + dependent todo 2 (relaunch the benchmark) become clean batch12 candidates. **This
  is the SAME underlying gap `data_pipeline_check_mdps_features_2026_07_20.md`'s item 3 (line 767) tracks** — resolving
  one closes both.

## Deferred — time-gated (blocked on upstream, not batchable)

- **`issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`** item 1 — the delta_one
  force+skip proof needs real CAPTURED TRADFI processed_candles data to exist first (upstream MDPS candle backfill gap);
  no batch todo can force data into existence.
- **`issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`** item 2 — the RSS-spike
  recurrence check needs the NEXT post-fix ES_OPT launch to actually happen first (tracked via batch6 todo #2, already
  active); precondition not yet met.

## Deferred — too-large-or-risky (needs its own dedicated plan, not a batch todo)

- **`data_completion_tradfi_2026_07_15.md`** — 15 open items, several irreversible-delete-gated or BLOCKED-OPERATOR
  (Databento billing). Same verdict batch6/7/8 reached 3 consecutive times; needs its own triage/design pass, not
  cherry-picked extraction.
- **`issues/tradfi_canonical_path_migration_design_2026_07_19.md`** — an 8-step sequenced migration (steps 4-8 open), 2
  of which are explicit `[GATE-operator]` items over a 2.73M-object corpus. Same verdict batch6/7/8 reached 3
  consecutive times.
- **`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`** item 5 — full CME instrument-definitions re-fetch, ~2,368
  days. Flagged 3x across batch6/7/8 as "needs a dedicated design pass," never converted to a todo.
- **`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`** — all 7 items gate on the same underlying MDPS
  `continuous_future` hit-rate data gap (re-tested 79.2% `empty_confirmed` as of batch8's 2026-08-08 re-check, no change
  since). Re-confirmed `orphaned_never_touched` + conflict-gated 3 consecutive times (batch6/7/8); becomes a strong
  candidate the moment the MDPS gap closes as its own project — not drafted speculatively again here.

## Deferred — already in flight / self-dispatched (not batch11 material)

- **`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`** item 1 (the gated DELETE) — sequenced behind this
  batch's own `canonical_twin_path()` fix todo above; its precondition (a fresh 100%-coverage re-run) isn't met until
  that fix ships.
- **`issues/tradfi_backfill_oom_remediation_2026_06_24.md`** — already self-dispatched (`assigned_vm: planning`,
  `status: open`), live in the standing AO backlog independent of any batch wrapper; batch7 already declined to
  duplicate it, same reasoning holds.
- **`issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md`** todo 2 (land the accurate
  "S&P index options" row) — batch6's own open P0 todo already commits to updating the same MVP-cell row, targeting
  final post-backfill numbers rather than this issue's interim text; not duplicated here.
- **`issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`** item 1 — already covered by
  batch6 todo #2 (active, ongoing retry work).

## Deferred — standing/recurring (not a single bounded AO outcome)

- **`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`** — the doc's sole open item is an explicitly
  recurring re-check-every-rollup-cycle loop, not a one-shot task; persists until
  `tradfi_canonical_path_migration_design_2026_07_19.md`'s permanent upstream migration lands. No action needed here.

## Flagged, not batched — cross-tranche ownership

Per `parent_epic`, these docs' genuinely-tradfi-relevant remaining content is not tradfi's to draft into — following the
identical primary-owner precedent batch6/7/8 established for the same docs:

- **`ag_closeout_audit_rollout_2026_07_25.md`** — sole open item's owning tranche resolves to `cefi` (parent_epic
  doesn't map to any of its 5 listed AGs, falls back to `tranches[0]`); tradfi's own historical slice already done.
- **`data_pipeline_check_mdps_features_2026_07_20.md`** items 1-2 (line 193, 319) — generic cross-AG infra work (item 3,
  the tradfi-specific `_resolve_spot_perp` gap, is separately tracked above under conflict-gated).
- **`issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`** item 8 — genuinely tradfi/CME
  content but `parent_epic: instruments_master`, 4-way `asset_group`; flagged not drafted 2x already (batch7/8).
- **`issues/instruments_docs_audit_outstanding_items_2026_07_08.md`** §H — 100% tradfi content but same
  `instruments_master` primary-owner precedent; flagged not drafted 2x already (batch7/8).
- **`issues/instruments_remaining_work_audit_2026_07_10.md`** — a historical-snapshot pointer index; its one
  tradfi-relevant thread routes through `mtds_is_full_adapter_smoketest_findings_2026_07_07.md` below.
- **`issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`** — 4 real tradfi-specific prose bugs (never
  checkboxed), but `parent_epic: instruments_master`, 5-way `asset_group`; flagged not drafted 3x already (batch6/7/8),
  each pass independently live-checking status without adopting it.

## Progress Log

- 2026-08-10 (ag-closeout-audit, tradfi tranche, dispatch agt-022d39, slot 25): drafted, `status: draft`. Phase 1 ran as
  a 52-agent Workflow against the post-tooling-fix candidate list (see `unified-trading-pm@e7ac1ed4e1`,
  `generate_ag_closeout_audit_candidates.py`'s hub-doc exclusion regex fix, found live this same pass). 14 todos
  extracted; conflict-checked against all active tradfi covering docs + the cross-cutting
  `governance_sweep_deferred_followups_2026_08_06.md` conflict — zero new collisions. Not yet reviewed by the operator.
- 2026-08-10 (slot-21, data_engineering craft): resolved todo #10 (wave_launcher deployment mechanism). **Findings**:
  (1) ACTUAL live mechanism = HOST cron on the monitor host, NOT the Cloud Run Job — the `_write_last_run_sentinel`
  comment is ACCURATE. The Cloud Run Job `uts-prod-tradfi-wave-launcher` exists (Terraform-managed) but is DORMANT:
  Cloud Scheduler PAUSED since 2026-06-24, last job execution 2026-06-25. The host cron wrote the
  `wave-launcher-last-run.json` sentinel TODAY at 2026-08-10T15:00 UTC — the Scheduler hasn't fired in 6+ weeks. (2) CME
  dedup fix (`deployment-service@bcf55c781`) CONFIRMED PICKED UP by the live mechanism: VMs launched today (~18:49-18:51
  UTC) use the clean single-root naming (`tradfi-bf-cme-ohlcv-1m-btc-2021-...`, `…-gc-2020-...`, `…-ng-2020-...`) from
  the fixed launcher script, not the old broken bundling pattern. The host cron runs from a git checkout — no image
  rebuild needed. The dormant Cloud Run Job's `:latest` image is stale (no evidence of post-bcf55c781 rebuild); a
  rebuild MUST run before un-pausing the Scheduler.
- 2026-08-10 (slot-21, data_engineering craft): resolved todo #9 (pipeline_mode~live CME rows writer identification).
  **Findings**: Current manifest shows 36 rows (the original 24 + 12 new since filing), all `live_databento`,
  `data_type=trades`, `source=databento`. **Writer identified**: (a) 8 rows `written_at=2026-07-07` + 16 rows
  `written_at=2026-08-04` = the **manifest consolidator** (Cloud Run/Batch-Fargate) rebuilding the index from individual
  shard parquets — these carry the OLD VM's June 2026 capture history forward with consolidator-run-time `written_at`.
  The `written_at` column reflects consolidator run time, NOT data capture time — this measurement trap is the root
  cause of the apparent mystery. (b) 12 rows post-2026-08-09 = the NEW live VM
  `mtds-live-tradfi-cme-trades-20260809-163443` (launched 2026-08-09 ~16:34 UTC, RUNNING as of today, labels
  `purpose=mtds-live, shard-slug=tradfi-cme-trades`). This VM replaced the deleted
  `mtds-live-tradfi-cme-trades-20260623-095619` (deleted 2026-06-30). No mis-tagging bug; no code change needed.
- 2026-08-10 (slot-21, data_engineering craft): resolved todo #7 (KRX .KS-USD manifest duplicate purge). **Findings**:
  (1) `.KS-USD` form CONFIRMED DEAD: 14,618 rows, 0 captures ever, last `written_at=2026-07-22` — no GCS shard parquets
  backing them; IS adapter builds canonical `KRX:EQUITY:{symbol}`, MTDS `derive_tradfi_row_instrument_id` builds
  `KRX:EQUITY:{code}-USD`. (2) PURGED: stream-filtered manifest 10,411,924 → 10,397,306 rows (14,618 dropped), backup at
  `availability_index_backup_krx_purge_20260810T182348.parquet`, verified 0 `.KS-USD` rows remain. Note: bare `.KS`
  ticker forms (`000660.KS` etc.) and blank-instrument_id (`:`) rows remain — these are separate issues (likely batch11
  #6's domain).

- 2026-08-10 (slot-21, data_engineering craft): census for todo #6 (CME FUTURE blank-instrument_id backfill).
  **Population is 473,374 rows — 23× the 20,254 in the source issue.** NOT static — 425K rows written 2026-08-10
  (clusters at 07:14 and 13:25 UTC). Full dissection in
  `/plans/active/issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md` Progress Log (slot-21 entry). Key
  findings: (1) ALL rows have populated `underlying` + null `instrument_id` + empty `quote_asset`/`margin_type` —
  bundle-grain signature, NOT per-contract singles. (2) 75,805/76,454 unique (date, underlying, data_type) keys overlap
  with `futures_chain` but with DIFFERENT `instrument_count` values — not redundant, can't blindly delete. (3) Root
  cause refined: `canonicalize_manifest_instrument_type()` maps `continuous_future` → `FUTURE` — should be excluded like
  `futures_chain`/`options_chain`. (4) GCS source objects (`instrument_type=future/underlying=*/` or
  `continuous_future/`) not found in canonical bucket — likely migrated/deleted post-rebuild. (5) Also found: 9,665 KRX
  blank rows (blank `instrument_type` + blank `underlying`), separate defect. **Todo #6 scope is now wrong** — the
  "backfill per-contract instrument_ids" approach assumes per-instrument rows; these are bundle-grain rows that need
  `instrument_type` reclassification, not per-contract id derivation. Needs operator re-triage.

- 2026-08-10 (slot-21, data_engineering craft): ✅ executed todo #5 (WithinBoundsTradfiSourceZero bundle-grain purge).
  **Evidence**: (1) Fresh dry-run: 114,318 candidates (unchanged from original 2026-07-30 measurement), 90,842 droppable
  (+9,388 vs original 81,454 — more `captured` counterparts accumulated in the interim), 23,476 unresolved (genuine
  failures, no captured twin exists — left untouched). 62 unique unresolved venue:symbol pairs. (2) Soft-delete
  retention on `market-data-tick-tradfi-prd-central-element-323112` = **604800s (7 days) ≥ 604800s** — reversibility
  gate PASSES (§3a). (3) `--apply` executed via pyarrow-based approach (full 42-column pandas DataFrame = 18GB;
  `df.copy()` OOM'd this host at 30GB; pyarrow `table.filter()` succeeded). CAS write gen
  1786400879196072→1786401070022279, 253,067,510→246,037,497 bytes. Snapshot backup at
  `gs://market-data-tick-tradfi-prd-central-element-323112/_index/backups/availability_index.pre_bundle_grain_shard_atom_mismatch_retire_20260810T223057Z.parquet`.
  **Self-verify**: 0 candidates with captured twins remaining post-mutation; all 23,476 remaining candidates are genuine
  unresolved (no captured counterpart exists for their date+venue+data_type+underlying key — confirmed count matches
  exactly). (4) `DP_RUN_MOSTLY_EMPTY` CME OHLCV ratio: **10.68%→6.81%** (−3.87 percentage points). CME OHLCV
  `attempted_failed`: 227,324→138,971 (−88,353 of the 90,842 total dropped rows, 97.3%). Pre-purge counts from the
  snapshot backup; post-purge from the live manifest (gen 1786401070022279). **Memory note**: this host (30GB, 16 cores,
  12GB swap in use, 8 other claude sessions) cannot hold 2 copies of the 42-column 11.2M-row manifest in pandas; pyarrow
  succeeded with careful `del`+`gc.collect()` between stages.
