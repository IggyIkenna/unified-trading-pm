---
doc_type: issue
title: Full-corpus /plan-reconcile sweep 2026-08-20 -- 892 docs read in full, 301 findings, triage in progress
summary: >-
  Coordinator record for a full-coverage /plan-reconcile pass across the entire active corpus (892 unique docs, all
  10 tranches), dispatched as 36 read-only ~22-doc-group hunters (max 5 parallel) rather than tranche-level, after an
  early tranche-level pass measured only 18-45 of ~140-199 docs read per tranche. Zero repo writes during the hunt
  phase; every fix applied afterward through normal interactive triage. This doc is the durable record of the sweep
  and the tracked home for the P2/P3 long tail -- the raw per-group report transcripts lived in an ephemeral session
  scratchpad and are not preserved verbatim; the counts and class-level dispositions below are.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-reconcile, full-sweep, corpus-hygiene, triage]
related:
  [
    /plans/active/issues/plan_reconciler_findings_all_2026_08_12.md,
    /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md,
  ]
created: 2026-08-20
author: interactive session, slot-6
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
assigned_role: plan_health
drift_direction: advance-code
depends_on: []
source: >-
  Operator directive 2026-08-20 -- run /plan-reconcile with sub-agents per shard, report-only, then triage
  interactively so plans become accurate and complete.
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md,
  ]
---

# Full-corpus /plan-reconcile sweep 2026-08-20

## Method

892 unique active docs (388 plans + 505 issues at sweep start) partitioned into 36 groups of ~22 docs each
(~600KB/group), read in full by independent read-only hunters, 5 parallel at a time (CLAUDE.md's max). Two hunters
died mid-run on transient API/network errors and were resumed from their own transcripts via `SendMessage`, not
restarted cold -- their partial reports (written incrementally per-finding, not buffered) survived. Zero repo writes
during the hunt phase; every hunter was explicitly report-only.

**Measured totals**: 301 findings across 46 report files (36 corpus groups + 10 earlier tranche-level runs whose
scope the 36-group sweep superseded for coverage but whose findings are folded in here) -- 3 P0, 33 P1, 91 P2, 153
P3. By class: 104 NEAR-COMPLETE, 96 MECHANICAL, 25 CONTRADICTION, 16 ARCHIVE, 13 FALSE-UNCHECKED, 12 PRIOR-FINDING, 7
ZERO-CHECKBOX, 5 STILL-OPEN, 1 STALLED-CAMPAIGN.

## Disposition

**P0 (3) -- all resolved.**

1. A design doc's security justification ("PM repo is private") was factually false, risking reopening a
   fork-PR exposure a 2026-08-07 fleet-wide revert fixed -- corrected, `unified-trading-pm@724bdd3d26`.
2. A checkbox cited a fabricated commit sha (`agent-orchestrator@be120911`, does not exist in repo history) --
   verified the real fix landed under a different, correct sha (`agent-orchestrator@4bff9c15`) between the finding
   and triage; no doc edit needed, already self-resolved.
3. A "1 open todo" near-complete finding turned out to be a correct, already-re-verified-5x standing item -- no
   action needed, informational only.

**P1 (33) -- all actioned** via a mix of direct edits (18 docs, `unified-trading-pm@129def7cc5`) and 6 dispatched
follow-ups (wave-launcher verification `@7343cc865f`, PnL spec split `@69313eabd0`, plus Grok/Kimi removal,
dead-lock clearing, pipeline_mode live GCS check, and terraform Phase-1 re-plan -- see `## Dispatched follow-ups`
below for live status). Two required an operator ruling before proceeding, both answered:

- Terraform drift (F-G20-4): already-approved backlog, blocked only on a stale diff -- operator asked for a live
  re-plan before any apply; dispatched as a READ-ONLY Phase 1 (re-plan + classify only, no `tofu apply`), Phase 2
  gated on reviewing that output.
- PnL native-staking-return metric (F-G20-6): genuine unbuilt money-path work under a standing OPERATOR GATE --
  operator asked for a build-ready spec, not code; delivered as
  `plans/active/issues/pnl_true_native_staking_return_spec_2026_08_20.md`.

**P2/P3 long tail (244) -- disposed by CLASS, not individually.** Per-finding transcripts are not preserved (they
lived in the ephemeral hunt scratchpad); the actionable classes and their resolutions are tracked as todos below.
Re-running the sweep (or a topic-scoped `/plan-reconcile <tranche>`) will re-surface any individual finding that
still needs attention once a class-level fix lands.

## Todos

- [ ] [SCRIPT] P2. **`locked_by: live-defi-rollout` boilerplate corpus-wide.** Confirmed across 9+ docs this sweep
      (independently found by at least 4 different hunters) -- a branch name landing in the lock-holder field,
      not a real lock, blocking otherwise-ready archivals. Operator ruling: treat any doc where this is the ONLY
      blocker as unlocked and archive-eligible. A standing tracker already exists at
      `/plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md` (cited "2 files" as
      of its own last count; this sweep found 9+, confirming it's an active, growing tooling bug, not historical
      residue) -- update that doc's count and root-cause it (find what's stamping the branch name into this field)
      rather than re-litigating per-doc here.
- [ ] [SCRIPT] P2. **`context-scout` append-corruption -- 17+ confirmed instances, dated mostly 2026-08-18.** A
      batch process died mid-write on that date: a `na-eligibility-audit 2026-08-18` Progress Log entry gets
      truncated mid-sentence, then a later `context-scout` append (often 2026-08-20) lands out of order right
      after the truncation point. Confirmed docs include (non-exhaustive, first 8 of 17+):
      `qg_host_adaptive_resource_governor_2026_07_14.md`,
      `test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md`,
      `glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`,
      `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md`,
      `ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md`,
      `dp_vm_001_mdps_cefi_2019_exit_nonzero_relaunch_bound_page_2026_08_14.md`,
      `dp_vm_001_tradfi_2026_exit_nonzero_relaunch_bound_page_2026_08_14.md`, plus a milder split-H2-section variant
      seen in several sports satellite-batch docs. Operator ruling: (a) file this as its own tooling-fix issue doc
      naming every instance, (b) dispatch a cleanup pass to repair the truncated text in each. File the issue doc
      first (a dedicated `context_scout_append_corruption_2026_08_20.md`), enumerate the full instance list via a
      corpus grep for the exact truncation signature, THEN dispatch the repair pass -- don't repair blind without
      the full list captured durably first.
- [ ] [AGENT] P2. **Near-complete auto-fold (104 candidates, exactly 1 open todo each).** Operator-approved
      carve-out: auto-fold ONLY where the remaining tag is `[REVIEW]` or `[DOC]` AND exactly one active sibling
      exists under the same `parent_epic` (the only case where the fold destination isn't a real choice).
      Everything else needs a per-epic batch ruling (2+ siblings, or a different tag). Run the narrow auto-fold
      pass first, then group the remainder by `parent_epic` and bring back as batched questions -- do not ask
      per-doc, the epic groupings already did most of this sorting during the hunt.
- [ ] [SCRIPT] P2. **Non-standard checkbox markers (`[~]`) and bare status lines with no `[ ]`/`[x]` marker at
      all** -- confirmed in 6+ docs (`bucket_fold_ml_2026_07_17.md`, `bucket_fold_features_2026_07_17.md`,
      `data_completion_defi_2026_07_15.md`, `sports_cf8_available_at_backfill_regression_2026_07_13.md`'s
      "CANCELLED" line, `mtds_qg_red_morpho_url_and_sports_contract_regression_2026_08_15.md`, and one more from
      the defi cluster). Both are invisible to the standard checkbox-grep every audit/backlog tool in this corpus
      uses, silently undercounting open-todo totals. Operator-approved: normalize to standard `[ ]`/`[x]` syntax
      corpus-wide, mechanical, no judgment call -- a single grep-and-fix pass.
- [ ] [AGENT] P2. **Archive candidates (16 confirmed this sweep, 0 open todos / unlocked / no real blocker).**
      Includes several `archive_exempt: true` docs where the exemption was set >1 week ago deferring to a named
      follow-on pass (`/archive-candidates-audit`) that never ran. Operator-approved: batch through the standard
      6-step archival ritual rather than spot-checking individually -- this was the highest-confidence, lowest-risk
      class in the whole sweep.
- [ ] [AGENT] P3. **153 P3 findings** (mostly MECHANICAL: stale banners, dangling refs already resolvable to
      archive/codex, minor duplicate-todo/duplicate-`context_scope`-entry cleanups, a handful of stale
      `last_updated`/`summary:` vs Progress-Log-tail mismatches). Lower priority than the classes above; work
      through opportunistically during the next scheduled `/plan-reconcile` cadence rather than a dedicated pass --
      most will self-resolve as docs get touched for other reasons, and re-running the sweep will re-surface
      anything that doesn't.

## Dispatched follow-ups -- live status as of this checkpoint (2026-08-20)

- **Grok removal / Kimi routing-block** (agent-orchestrator, unified-api-contracts, unified-trading-system-ui,
  unified-trading-pm codex) -- IN PROGRESS, mid-quality-gate at checkpoint time. Uncommitted working-tree changes
  present in `agent-orchestrator` (`dashboard/src/KimiWalletPanel.tsx`, `TaskUsageWindows.tsx`, `layout.tsx`,
  `server/model_pricing.py`, `tests/test_deepseek_provider_routing.py`, and others) -- DO NOT TOUCH, this is a live
  agent's in-progress work, not abandoned WIP. Resume by messaging agent `a05af12f32ba65381` (or re-dispatch fresh
  with the same brief if that session is gone) if it hasn't self-completed and reported.
- **Dead reconciler-lock clearing** (`plan_reconciler_findings_ui_2026_08_19.md`,
  `plan_reconciler_findings_sports_2026_08_19.md`) -- dispatched, status unknown at checkpoint time. Check both
  docs' `locked_by:` field; if still set and the dispatch confirmed reaped-stale, the fix wasn't shipped yet.
- **pipeline_mode partition live GCS check + requirements-drift check**
  (`pipeline_mode_partition_migration_2026_06_01.md`) -- dispatched, status unknown at checkpoint time. Check the
  doc's Progress Log for a dated 2026-08-20 entry with live evidence; if absent, the dispatch didn't complete.
- **Terraform drift Phase 1 re-plan** (`prod_terraform_drift_backlog_reconcile_2026_07_24.md`) -- dispatched,
  READ-ONLY (no apply authorized), status unknown at checkpoint time. Check the doc for a fresh dated
  classification section. **Phase 2 (the actual `tofu apply`) is explicitly NOT authorized until a human reviews
  Phase 1's output** -- do not let a resumed session skip straight to applying.

## Progress Log

- **2026-08-20 (interactive, slot-6)**: Sweep run, 892 docs / 301 findings measured. P0s (3/3) and P1s (33/33)
  actioned via direct triage + 6 dispatched follow-ups. This doc created as the durable record ahead of a
  context-checkpoint compaction; P2/P3 long tail converted to class-level tracked todos above rather than left as
  ephemeral scratchpad-only findings.
