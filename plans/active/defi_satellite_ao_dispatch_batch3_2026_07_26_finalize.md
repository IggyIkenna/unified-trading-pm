---
doc_type: plan
title: DeFi satellite AO batch 3 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch3_2026_07_26.md — machine-held via depends_on + gate_on_depends:
  true until all 12 of that plan's todos are done. Mirrors batch1/batch2-finalize's pattern (reconcile each distinct
  source doc's checkboxes independently once its batch-3 todo lands, then re-check the Deferred
  operator-gated/conflict-gated/non-batchable items for any that have since cleared), then archives batch3 via the
  standard 6-step ritual. Also carries the follow-up for batch3's non-actioned findings (2 archivable_now docs to
  archive + 1 exclude_cross_cutting mistag to confirm retagged). **CORRECTED 2026-08-12 (/plan-reconcile)**: this
  summary previously said "status: draft — activated only after its parent batch3 is operator-approved and dispatched" —
  stale boilerplate contradicting the frontmatter `status: active` below; the parent batch3 was dispatched and is now
  archived (`plans/archive/2026_07/defi_satellite_ao_dispatch_batch3_2026_07_26.md`), so `active` is correct and
  current.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-3, satellite-docs, archival]
related:
  [
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-08-06"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_satellite_ao_dispatch_batch3_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26 (autonomous, scheduled ag_closeout_auditor), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan, mirroring the defi
  batch1 + batch2 + cefi + sports precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# DeFi satellite AO batch 3 — finalize

> **🟡 status: draft** — inert until its parent `defi_satellite_ao_dispatch_batch3_2026_07_26.md` is operator-approved
> (flipped to `active`) and dispatched. **Machine-gated on that plan** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 12 of its tasks are `done`. `sequential: true` because todo 2
> (deferred re-check) needs todo 1's reconciliation first, and todo 4 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all distinct source docs' checkboxes.** For each of
      `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s now-done todos: flip the corresponding checkbox/section in its
      named source doc (each todo ends with "Source: `<doc>.md`"), citing the batch-3 commit(s) that shipped it — verify
      the actual shipped commit exists before citing it. After flipping, re-check whether that source doc now has 0 open
      todos (checkbox AND prose-form — do not trust checkbox count alone); only flip its `status` to `resolved` if it
      genuinely reaches 0. **Done when**: all source-doc checkboxes/sections are flipped with verified evidence, and any
      doc that genuinely reaches 0 open todos is flipped to `status: resolved`.
- [x] ✅ [REVIEW] P1. **Re-check batch3's Deferred items** (the operator-gated, conflict/sequence-gated, and 9
      non-batchable-orphan items), now that batch3's own todos have landed. For each: re-read the specific gating ground
      to check if it has cleared — if so, extract it as a new tracked todo in a follow-up `batch4` (do not draft it
      directly here — this finalize plan's scope is reconciliation, not fresh drafting); if still genuinely unresolved,
      leave it explicitly deferred and note the re-check happened (do not re-ask an already-open operator question).
      Specifically re-check: the E3 borrow leg (should clear once todo 4 A2-staking-leg lands), and the 5
      `defi_migration_audit_log` stale-premise items (need an operator reconciliation against the shipped shared-bucket
      architecture — confirm the premise is still stale, don't silently drop them). **Done when**: each Deferred item
      has either (a) a note it's ready for `batch4` extraction, or (b) an explicit re-verified confirmation the gate is
      still open.
- [x] ✅ [DOC] P2. **Action batch3's non-batched findings.** (1) Archive the 2 archivable_now docs
      (`e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md`, `mtds_perp_funding_backfill_hang_2026_07_14.md`)
      via the standard 6-step ritual — but FIRST confirm each still reaches 0 open todos on a fresh read (they were
      classified archivable_now 2026-07-26; re-verify nothing re-opened). **PARTIALLY DONE 2026-07-27**:
      `e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md` was already archived by the separate
      `june_2026_vintage_audit_findings_2026_07_27.md` §2 execution pass — verify it landed at
      `/plans/archive/issues/e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md` with a clean banner (don't
      re-archive); `mtds_perp_funding_backfill_hang_2026_07_14.md` still needs its own archival pass here. (2) Confirm
      `mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` got retagged off `[defi]` (batch2's finalize
      owns the retag; this is just a cross-check that it happened — if not, file/hand off, do not duplicate the retag
      todo). **Done when**: item (1)'s 2 docs are in `plans/archive/2026_07/` with every corpus referrer fixed (or
      explicitly re-deferred if a fresh read finds new open work); item (2) is confirmed done or handed off. **DONE
      2026-08-06 (slot-11)**: (1) Both docs confirmed archived at `plans/archive/issues/` with `status: resolved` and
      proper banners — e2e doc at `/plans/archive/issues/e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md`
      (clean banner, `status: resolved`); mtds_perp doc at
      `/plans/archive/issues/mtds_perp_funding_backfill_hang_2026_07_14.md` (archived per commit bec54efeb, banner "🟢
      RESOLVED 2026-07-14"). Formal `related:` corpus referrers fixed:
      `../archive/2026_08/mtds_retry_safe_default_audit_2026_07_14.md` and `defi_consolidated_closeout_2026_07_18.md`
      both updated from `issues/...` to `/plans/archive/issues/mtds_perp_funding_backfill_hang_2026_07_14.md`. e2e doc
      already correctly referenced in `e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` as
      `/plans/archive/issues/...`. (2) Retag NOT done — batch2 finalize's `[DOC] P2` todo still `- [ ]`
      (`defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md`); handed off — batch2 finalize owns it, no duplicate
      todo authored here.
- [x] ✅ [DOC] P1. **Archive `defi_satellite_ao_dispatch_batch3_2026_07_26.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have resolved or re-confirmed all of them — verify none silently vanish) → add the archive banner → run the
      codex-alignment check (no new durable contract from this batch, confirm still true) → grep the corpus for every
      referrer of `defi_satellite_ao_dispatch_batch3_2026_07_26` and fix each path to point at the archived location →
      clear `locked_by` (already empty, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit. **DONE 2026-08-06 (slot-4)**: all 6 ritual steps complete — (1) deferred items re-verified by Todo 2 (none
      silently vanished); (2) archive banner added + `status: complete`; (3) codex-alignment: no new durable contracts;
      (4) CLAUDE.md: nothing new; (5) all 34 path referrers updated from `plans/active/` → `plans/archive/2026_07/`; (6)
      `locked_by` was empty, confirmed; `git mv` to
      `plans/archive/2026_07/defi_satellite_ao_dispatch_batch3_2026_07_26.md`. Note: finalize doc itself not archived
      alongside (Todo 1 still open).

## Progress Log

- **2026-08-06 (slot-8, review role) — Todo 2 deferred re-check COMPLETE** (every Deferred item in the parent
  `defi_satellite_ao_dispatch_batch3_2026_07_26.md` re-read against its gating ground; per-item verdicts below).
  Independent verification done this pass: `strategy-service@e93902d8` (the A2 staking leg that gates E3) confirmed an
  ancestor of `origin/live-defi-rollout` (`git merge-base --is-ancestor`);
  `defi_consolidated_closeout_2026_07_18.md:200` re-read and still states all kinds resolve `kind="tick-data"` on the
  single `market-data-tick-defi-prd` — the dedicated→shared consolidation remains shipped. Cross-checked against the
  later re-checks already performed by batch5-finalize (2026-08-05) and batch6 (2026-07-30) so no already-open operator
  question is re-asked. Note: the "follow-up `batch4`" named in the todo text has since run and been archived (defi
  batch4 2026-07-26 + batch5 2026-07-27); defi batch6 is the current active batch and already carries forward the
  cleared-gate item below — so the extraction target is batch6/batch7's Deferred, not a new batch4. **GATE CLEARED →
  ready for extraction (option (a)):**
  - **E3 recursive-staking borrow leg** (`lst_rate_honest_coverage_2026_07_21.md` Phase 6 `[STRATEGY] P3`) —
    sequence-gate CLEARED: the A2 staking leg (batch3 todo 4) landed (`strategy-service@e93902d8`, verified ancestor of
    LDR). Standing scoping step still applies per the doc (money-path 3-lens review; Aave-oracle unblock alone
    insufficient) — batch6 (2026-07-30) re-categorized it operator-gated (money-path) and carries it in its own Deferred
    for batch7. Ready to draft as a batch7 todo with that scoping pre-condition. E3 checkbox stays `- [ ]` in the source
    doc (its own flip is source-doc reconciliation, not this todo).
  - `defi_expected_unattempted_seeder_design_2026_07_26.md` — CLEARED: archived 2026-08, `status: complete` (superseded
    by batch6's fresh triage).
  - `defi_five_never_captured_venues_fix_2026_07_22.md` — CLEARED: archived, `status: superseded` (superseded_by
    `five_broken_defi_capture_paths_shipped_2026_07_22.md`, resolved, same date — all 5 handled).
  - `onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md` — CLEARED: archived, `status: resolved` (its one
    todo shipped 2026-07-30 `features-service@d8a643a0`; recompute scope tracked in
    `features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`). **STILL GATED → re-verified, left
    explicitly deferred (option (b)):**
  - `defi_turbo_api_hides_real_captured_data_2026_07_07.md` (HYPERLIQUID/ASTER into UAC `ALL_DEFI_VENUES`) —
    `status: open`; the UAC-registry-level CEFI+DEFI double-counting ruling is still open (batch5-finalize: STILL
    BLOCKED; batch6: operator-gated). No re-ask.
  - `defi_migration_audit_log_2026_07_24.md` items 3/5/7/8/10 (dedicated-bucket premise) — premise RE-VERIFIED STALE:
    the dedicated→shared consolidation is still shipped (`defi_consolidated_closeout_2026_07_18.md:200`); doc
    `status: active`, `assigned_vm: NA`. Drafting these as dedicated-bucket migrate todos would re-introduce the
    divergence the consolidation removed — operator reconciliation of item text vs the shipped shared-bucket
    architecture is still needed (batch6: 10 of 11 remaining items are design/operator-sign-off calls).
  - `defi_migration_audit_log` item 2 (SOURCE_PRIORITY Solana source) + item 9 (delete legacy buckets) + item 1 (Era-B
    legacy retirement) — item 2's "which Solana source is canonical" operator ruling still open; item 9's destructive
    legacy-bucket delete still needs operator sign-off per the GCS delete-safety HARD RULE; item 1 still warrants its
    own dedicated plan (large cascade-coupled UAC+MTDS registry+test drop).
  - `data_completion_defi_2026_07_15.md` G6 Jupiter historical reconstruction — G1 (Orca+Raydium pool-state backfill)
    still operator-launched/not scheduled by a covering plan, and the simulation-vs-pool-states approach is still an
    undecided research/design call (batch6: "G6 explicitly parked by batch3"). G6 checkbox still `- [ ]` in the source
    doc.
  - `defi_venue_lst_rates_residual_2026_07_24.md` — `status: active`; bare-`SUSHISWAP` classic-vs-V3 alias
    data-semantics ruling still open.
  - `architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` — `status: open`; CARRY_STAKED_BASIS
    delete-vs-re-leg strategy-domain ruling still unruled (batch5-finalize: STILL BLOCKED).
  - `defi_morpho_lending_indices_never_wired_2026_07_12.md` — `status: open`; time-gated on
    `defi_onchain_v10_universe_v2_seed_or_backfill_progressed`, still not confirmed complete.
  - `/plans/archive/issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md` — `status: resolved` + archived
    2026-08-11; both open items resolved (todo 4 DECISION via `unified-api-contracts@8c506575`, todo 5 register-append
    via batch10 item 7).
  - `defi_upstream_instruments_catalog_stale_2026_07_15.md` — `status: open`; `[DESIGN] P3` retry-sweep-signal mechanism
    ownership still unruled (batch5-finalize: STILL BLOCKED).
  - `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` — `status: open`; generator-vs-committed
    prospectus reconciliation design decision still needed (batch6: operator-gated).
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: re-verified context_scope (5 entries) -- unchanged, already minimal.
- **context-scout 2026-08-07**: re-verified context_scope (5 entries) -- all 5 entries still resolve and remain the
  correct minimal reading list after the 2026-08-06 Todo 3/Todo 4 completions; unchanged.
- **2026-08-06 (slot-4, data_engineering) — Todo 4 [DOC] P1 archive DONE**: 6-step ritual complete for
  `defi_satellite_ao_dispatch_batch3_2026_07_26.md`. All 13 todos verified `[x]`, locked_by empty. Deferred items
  confirmed by Todo 2 (none silently vanished). Codex-alignment: no new durable contracts. 34 path referrers updated
  from `plans/active/` → `plans/archive/2026_07/` across 20 files. INDEX.md batch3 entry removed. File moved via
  `git mv` to `plans/archive/2026_07/`. Note: finalize plan NOT archived alongside — Todo 1 (source-doc reconciliation)
  still open; finalize will archive once Todo 1 ships.
