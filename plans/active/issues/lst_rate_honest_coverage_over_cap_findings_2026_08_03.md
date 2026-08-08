---
doc_type: issue
title:
  lst_rate_honest_coverage_2026_07_21.md is over the 1000L plan hard-cap, blocking 3 ready-to-apply stale-checkbox
  closes; separately its DEX-fill VM `-3` failed 2026-07-27 and was never relaunched
summary:
  na-eligibility-audit (defi tranche, 2026-08-03) independently verified 3 of that doc's 6 open checkboxes are stale
  (work already shipped elsewhere, real shas confirmed) and one has a live, actionable finding (a backfill VM dead 6+
  days with no auto-recovery) — but the source doc is already over the 1000-line plan hard-cap
  (`scripts/plan-hygiene/check_line_caps.sh`), so a normal commit closing those checkboxes hard-fails the prek gate;
  only a small non-checkbox marker append is currently permitted there (operator ruling 2026-08-02, see that script's
  header comment). This doc carries the ready-to-apply evidence as real todos plus the VM finding, so neither is lost to
  prose. Do NOT re-derive the evidence below — it is already verified; the work is applying it once unblocked.
status: open
nature: issue
asset_group: [defi]
stage: [meta, data]
repos: [unified-trading-pm, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: [plan-hygiene, line-cap, stale-checkbox, vm-monitoring, billing-waste, na-eligibility-audit]
related:
  [
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    /plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md,
    /plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md,
  ]
created: "2026-08-03"
author: unknown
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.3
assigned_role: NA
drift_direction: correct-codex
resolved_by:
locked_by:
source:
  ["na-eligibility-audit defi tranche, 2026-08-03 — found while classifying lst_rate_honest_coverage_2026_07_21.md"]
depends_on: []
context_scope:
  [
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    scripts/plan-hygiene/check_line_caps.sh,
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    /plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md,
    /plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md,
  ]
---

# lst_rate_honest_coverage over-cap findings — ready-to-apply closes + a stalled backfill VM

## Why this doc exists instead of editing the source plan directly

`plans/active/lst_rate_honest_coverage_2026_07_21.md` is a `doc_type: plan` currently at ~1008 lines, over the 500L soft
/ 1000L hard cap enforced by `scripts/plan-hygiene/check_line_caps.sh`. That script's SCOPED mode (the prek pre-commit
hook) has a narrow, deliberate exception (operator ruling 2026-08-02) letting an already-over-cap doc take a small (≤10
added lines, 0 deleted, no `- [ ]`/`- [x]` pattern) marker-only append — specifically so na-eligibility-audit can still
write its incremental-skip verdict marker there. That exception explicitly EXCLUDES checkbox changes by design ("so this
can never be used to sneak in new tracked work on an over-cap doc"). This run used that exception to write the verdict
marker only; the actual checkbox closes below need either a real doc-split (bringing the file under 1000L first) or an
operator-approved wider edit.

## Todo 1 — split `lst_rate_honest_coverage_2026_07_21.md` under the 1000L cap

- [ ] [SCRIPT] P2. The doc's Progress Log carries a long, safe-to-extract chronological block of VM-monitoring check-in
      entries (roughly the `2026-07-21` through `2026-07-26` "VM re-check" entries — dozens of timestamped status
      updates for the now-largely-complete LST-rates and DEX-swaps backfill VMs). Extract that historical block into a
      companion doc (e.g. `plans/archive/issues/lst_rate_honest_coverage_vm_monitoring_history_2026_07_21.md` per the
      "extracted-history" pattern `check_line_caps.sh`'s own comments reference), leaving the live plan with its
      frontmatter, Phase sections/todos, and a condensed summary of the extracted history plus a pointer to the new doc.
      Verify no other doc references a specific timestamped entry inside the extracted range before moving it. Re-run
      `bash scripts/plan-hygiene/check_line_caps.sh plans/active/lst_rate_honest_coverage_2026_07_21.md` to confirm it's
      back under 1000L before applying todos 2-4 below.

## Todo 2 — close 3 stale checkboxes (evidence already verified, just apply)

- [ ] [SCRIPT] P3. Once todo 1 lands, flip these 3 open checkboxes in `lst_rate_honest_coverage_2026_07_21.md` to
      `[x] ✅` with the evidence below (verified 2026-08-03 — shas confirmed to exist on `live-defi-rollout` via
      `git log --oneline -1 <sha>`, do not re-verify): - **Phase 6 "A2 staking leg"** (`- [ ] [STRATEGY] P2`) — DONE,
      shipped `strategy-service@e93902d8` ("feat(strategy): wire carry_staked_basis STAKING leg to real lst_yields
      index-ratio accrual"), per `pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`'s "PROGRESS
      2026-07-23 — STAKING leg SHIPPED" entry. - **Phase 6 "Recursive-staking borrow leg"** (`- [ ] [STRATEGY] P3`) —
      DONE, shipped `strategy-service@23bd8b76` ("feat(strategy): wire CARRY_RECURSIVE_STAKED tick builder + Aave
      borrow-index leg"), per the same sibling doc's checked-off E3 todo, built as part of
      `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`'s Phase 2. - **Phase 3 "sample-download test on
      the -test- bucket"** (`- [ ] [MTDS] P3`) — superseded, not separately executed: Phase 5 #3 (AAVE oracle) proved
      the force-write leg via real climbing manifest counts to a clean `exit_code=0` completion; Phase 5 #2 (DEX)'s
      2026-07-23 01:26 UTC preemption-resume entry explicitly proved the skip-leg firing ("confirms the freshness-skip
      logic is genuinely working ... not re-fetching from scratch"). Both are stronger evidence than a
      `-test-`-bucket-only sample would add.

## Todo 3 — stalled DEX-swaps backfill VM needs a relaunch decision

- [x] ✅ [INFRA] P2. **RULED 2026-08-06 (operator): plain relaunch, same --start/--end, no --force** (the doc's own
      recipe, already proven 3x on sibling VMs). `[INFRA]` tag (was `[OPERATOR]`), AO-dispatchable — relies on the
      collector's freshness-skip to resume. `mtds-dex-swaps-backfill-3` (one of the 3-VM date-sharded fleet covering
      `2025-12-15 → 2026-07-21`) FAILED 2026-07-27 03:54 UTC with `exit_code=137` (`Killed` — OOM-shaped, same signature
      as the already-filed `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` P0, which as of 2026-08-03 is still
      open and itself blocked on vendor-credit exhaustion investigating the root cause) and has NOT been relaunched
      since — verified live via
      `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-dex-swaps-backfill-3/run.log | tail`
      (2026-08-03). It self-deleted (`VM_SHUTDOWN_ON_COMPLETION=true`), so it no longer shows in
      `gcloud compute instances list` as a red flag — a silent 6+ day stall on its shard. Sibling VMs: `-1` completed
      cleanly 2026-08-01 (`exit_code=0`); `-2` still healthily RUNNING as of 2026-08-03. This doc's own established
      recipe (proven 3× already, e.g. the 2026-07-23 01:26 UTC Progress Log entry) is a plain relaunch with the SAME
      `--start 2025-12-15 --end 2026-07-21` (no `--force`), relying on the collector's freshness-skip to resume — tagged
      `[OPERATOR]` because the underlying OOM root cause is still an open, unresolved P0 investigation (relaunching
      blind repeats the failure if the same OOM trigger fires again; the P0 issue's own resolution should inform whether
      a plain relaunch or a mitigated one — e.g. narrower shard, memory cap — is the right call now).

## Evidence

All shas, VM log tails, and doc cross-references above were verified directly (not inferred) during the 2026-08-03
na-eligibility-audit defi-tranche run. See `lst_rate_honest_coverage_2026_07_21.md`'s own 2026-08-03 Progress Log marker
for the compact pointer back to this doc.

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (5 entries) — added the two sibling evidence docs Todo 2 cites
  by name (`defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`,
  `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`) alongside the source plan, the line-cap script, and the
  STAKING-leg evidence doc.
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid — doc mixes two bounded
  SCRIPT-tagged todos with one explicitly `[OPERATOR]`-tagged genuine judgment call (whether/how to relaunch a stalled
  backfill VM pending an open OOM root-cause investigation); since not essentially all open work qualifies as bounded,
  the whole doc stays NA per the mixing rule. Doc stays `assigned_vm: NA`.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=defi, dispatch agt-e00d37): KEEP-NA valid — re-confirms the 2026-08-04
  verdict; the only change since was a context-scout metadata-only touch. Todo1/Todo2 [SCRIPT] remain bounded-in-
  isolation but sequentially gated on each other; Todo3 [OPERATOR] remains a genuine judgment call (VM relaunch approach
  pending the separate still-open P0 OOM issue). Doc stays `assigned_vm: NA` as a whole (per-doc field, one genuine
  judgment item is enough). Incidental: `mtds-dex-swaps-backfill-3` VM (Todo3's subject) was last independently verified
  stalled/OOM on 2026-08-03 — 3 days further elapsed with no fresh check in this doc; flagging for a
  `/vm-preemption-billing-waste-audit` pass, not re-verified live in this run.
- **2026-08-07 (slot 15, batch10 dispatch `defi_satellite_ao_dispatch_batch10-009`)**: Todo3 DONE — relaunched
  `mtds-dex-swaps-backfill-3` (SPOT, SHARD_INDEX=6, `--start 2025-12-15 --end 2026-07-21`, no `--force`) via
  `deployment-service/scripts/vm/launch-mtds-dex-swaps-backfill-vm.sh`. No sibling VMs running at launch time (both `-1`
  and `-2` had completed). T+10min health check: VM RUNNING (asia-northeast1-c, 35.190.235.80, e2-standard-4 SPOT);
  95,236 swap rows written to `market-data-tick-defi-prd-central-element-323112` in first shard (uniswap_v3_ETHEREUM) at
  T+5min; ManifestWriter per-VM shard updated at `_index/per_vm/mtds-dex-swaps-backfill-3.parquet`; RSS=840MiB (well
  within normal); PIPELINE_HEARTBEATs firing every 60s. ManifestConsolidatorStaleError in freshness-cache refresh
  (non-blocking; GCS is authoritative source; VM continues capturing). Firestore dual-write fails (best-effort, GCS
  authoritative, expected).
- **na-eligibility-audit 2026-08-08 (Phase 2, defi tranche)**: Todo1+Todo2 clear the whole-doc bar (both `[SCRIPT]`-
  tagged, bounded, sequential, done-when stated) — Todo3 above is already DONE. NOT reclassified: the conflict-check
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) found a near-verbatim duplicate
  already live — `plans/active/defi_satellite_ao_dispatch_batch10_2026_08_06.md` carries an OPEN `[DOC] P2` todo ("Bring
  lst_rate_honest_coverage_2026_07_21.md under the 1000L hard line cap...") that explicitly cites this doc's own
  Todo1+Todo2 verbatim as its source. `defi_satellite_ao_dispatch_batch9_2026_08_06.md` (line ~300) independently
  reached the same conclusion a day earlier ("already tracked elsewhere, no new park"). Flipping this doc to
  `assigned_vm: planning` would create a genuine duplicate-dispatch hazard (two AO-dispatchable surfaces claiming the
  same file edit). Left `assigned_vm: NA` — no action needed here; the work already has a live dispatch path via
  batch10's todo.
