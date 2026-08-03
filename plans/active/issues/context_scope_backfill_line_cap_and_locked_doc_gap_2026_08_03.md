---
doc_type: issue
title:
  context_scope corpus-wide backfill blocked on 9 line-cap docs + 2 locked docs — pre-computed entries ready to apply
summary: >-
  During the 2026-08-03 `/context-scout` NEVER_SCOUTED backfill session (8 parallel scouting agents, 78 docs), 9 docs
  could not receive their `context_scope` frontmatter because the addition (context_scope YAML block + Progress Log
  marker, 6-12 lines) would push them past the workspace's 1000-line hard plan cap (`check_line_caps.sh`), and 2 docs
  were correctly skipped by the scouting agents because they carry `locked_by:` and editing a locked doc's frontmatter
  needs operator sign-off. All 11 docs already have their `context_scope` entries computed and verified-to-resolve below
  — this is a re-apply task, not a re-scout.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [unified-trading-pm, context-scout, line-cap, locked-plan, plan-hygiene, docspec]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-08-03"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: script
priority: P2
drift_direction: advance-code
source: [context-scout-session-2026-08-03]
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /cursor-configs/skills/context-scout/SKILL.md,
    scripts/plan-hygiene/check_line_caps.sh,
    scripts/plan-hygiene/generate_context_scope_inventory.py,
  ]
---

# What

The 2026-08-03 corpus-wide `/context-scout` backfill session dispatched 8 parallel sub-agents over the 78
`NEVER_SCOUTED` docs (per `generate_context_scope_inventory.py --json`, run fresh that session: 646 in-scope docs, 276
`UP_TO_DATE`, 292 `STALE`, 78 `NEVER_SCOUTED`). 77/78 docs were successfully scouted and written; 1 batch's docs split
into two problem classes documented here:

**Class A — line-cap collision (9 docs).** Each scouting agent correctly followed its mandate (populate
`context_scope:` + append a dated `context-scout` Progress Log marker) and correctly did NOT attempt any trimming —
that's out of scope for a mechanical scouting pass. But the addition itself (a `context_scope:` YAML flow-list, 4-8
lines, plus one Progress Log bullet) is enough to push a doc that was already sitting at or near the workspace's
1000-line hard cap (`scripts/plan-hygiene/check_line_caps.sh`) over the line. `check_line_caps.sh` in SCOPED mode (the
mode `quickmerge`'s prek hook runs in, using the exact staged file list) has **zero baseline tolerance**: a file the
commit touches must not cross 1000L, full stop, unless it qualifies for the narrow small-marker-append exception
(operator ruling 2026-08-02: file already >1000L **before** this commit, diff has 0 deletions, adds ≤10 lines, adds no
checkbox lines). Of the 9 affected docs, only 6 were sitting at **exactly** 1000L pre-commit (not `>1000`, so the
exception's condition (a) does not fire — a doc newly crossing the cap in this commit is treated as a real regression,
by design), 2 were just under 1000L, and 1 (`fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`) was measured
by its scouting agent as "already at 1007L" but a direct `git show HEAD:<path> | wc -l` check during this session's
audit found it was actually **999L** pre-commit — the agent's own line-count claim was wrong (possibly counted after its
own edit, or used a different tool than `wc -l`); flagging this as a secondary, minor finding: don't trust a sub-agent's
self-reported pre-edit line count without an independent `git show HEAD:<path>` check, same category of lesson as the
async-wait-discipline "measured, not activity" rule elsewhere in this workspace.

All 9 docs' computed `context_scope` was reverted from the working tree before shipping (to keep the 2026-08-03 ship
clean — see `/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md` Progress Log for that session's full ship
record), but the sub-agents' analysis work is **not lost** — every entry below was independently verified to resolve on
disk by the scouting agent that computed it, during the same session this issue was filed.

**Class B — locked docs (2 docs).** The scouting agent covering these correctly refused to write `context_scope` (a
frontmatter field) into a doc carrying `locked_by:`, since a locked doc's frontmatter needs operator sign-off before any
edit, matching the precedent independently hit in the same batch by `docs_reconcile_operator_decisions_2026_08_02.md`
which parked an identical case. These 2 docs will sit at `NEVER_SCOUTED` in every future
`generate_context_scope_inventory.py` run until either the lock is released or an operator explicitly authorizes a
locked-doc scouting carve-out.

# Why this matters

`plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s own todo requires `generate_context_scope_inventory.py`
to report `NEVER_SCOUTED=0, STALE=0` corpus-wide before `docspec.py`'s `context_scope` `FieldSpec` flips from `Req.E`
(elective) to `Req.R` (required). These 11 docs are a small, known, already-diagnosed residual blocking that terminal
state — worth closing deliberately rather than letting them silently persist as perpetual `NEVER_SCOUTED` stragglers
across every future incremental inventory run.

# Plan

- [ ] [SCRIPT] P2. **Trim or split each of the 6 exactly-1000L docs, then re-apply their pre-computed `context_scope`
      (below).** Preferred approach per this corpus's own precedent
      (`mtds_available_at_cross_asset_backfill_line_cap_remediation_2026_07_31.md`, cited by one of this session's own
      scouting agents as the sanctioned pattern): extract a completed/historical Progress Log section into
      `plans/archive/` (status: complete / nature: record docs are unbounded by the cap by design — see
      `check_line_caps.sh`'s own policy comment), leaving the live doc under 1000L with its open todos intact. Do NOT
      delete content to force a fit — only extract genuinely-closed history. Verify with
      `bash scripts/plan-hygiene/check_line_caps.sh <path>` (scoped mode) before re-adding `context_scope`. Docs:
  - `plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md` (1000L pre-commit)
  - `plans/active/data_completion_cefi_2026_07_15.md` (1000L pre-commit)
  - `plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` (1000L pre-commit)
  - `plans/active/data_completion_to_100_all_ag_2026_06_21.md` (1000L pre-commit)
  - `plans/active/github_actions_operator_gated_followups_2026_07_17.md` (1000L pre-commit)
  - `plans/active/instruments_completion_tracker_2026_07_06.md` (1000L pre-commit)
- [ ] [SCRIPT] P2. **Trim or split the 2 near-1000L docs** (same extraction pattern), then re-apply:
  - `plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` (999L pre-commit, +10L would-be
    addition)
  - `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` (999L pre-commit, +12L would-be
    addition — this doc already has a documented 2026-07-24 split history per its own banner and will likely need
    another extraction pass)
- [ ] [SCRIPT] P3. **Trim `plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md`** (1000L pre-commit,
      +11L would-be addition — discovered separately during this session's final scoped line-cap re-verification, not
      part of the original 6+2), then re-apply its pre-computed `context_scope` (below).
- [ ] [OPERATOR] P3. **Resolve the 2 locked docs** — either confirm the lock is stale/expired and safe to release (per
      the multi-agent-safety liveness-gating pattern: a dead `locked_by` claim can be inherited), or explicitly
      authorize scouting a locked doc's `context_scope` field as an exception, or leave them `NEVER_SCOUTED`
      indefinitely as a deliberate, documented exclusion (in which case
      `ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s own `FieldSpec` flip todo needs a stated carve-out for locked
      docs, since its done-when is corpus-wide 0/0):
  - `plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`
    (`locked_by: live-defi-rollout`)
  - `plans/active/issues/fleet_audit_triad_deferred_followups_2026_06_01.md` (`locked_by: harsh-fleet-audit`)

# Pre-computed `context_scope` (verified to resolve on disk 2026-08-03 — re-verify if this issue sits long enough for

the corpus to drift)

```
plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/verify.py,
  ]

plans/active/data_completion_cefi_2026_07_15.md:
  [
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_cefi_manifest.py,
    unified-trading-library/unified_trading_library/manifest_writer,
  ]

plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    /codex/02-data/defi-completeness-oracle.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]

plans/active/data_completion_to_100_all_ag_2026_06_21.md:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/data_completion_cefi_2026_07_15.md,
    /plans/active/data_completion_defi_2026_07_15.md,
  ]

plans/active/github_actions_operator_gated_followups_2026_07_17.md:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/07-security/self-hosted-runner-security-posture.md,
    /plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md,
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
    scripts/cicd/measure-billed-notify-cost.sh,
  ]

plans/active/instruments_completion_tracker_2026_07_06.md:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    /plans/archive/2026_07/honest_coverage_v2_instrument_denominator_2026_06_28.md,
  ]

plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md:
  [
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    agent-orchestrator/server/escalation.py,
    scripts/quality-gates-base/qg-host-governor.sh,
  ]

plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md:
  [
    /codex/02-data/pipeline-mode-partition.md,
    /plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md,
    instruments-service/scripts/enumerate_expected_universe.py,
  ]

plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/instrument_id_format_canonicalization_2026_07_08.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    market-tick-data-service/scripts/migrate_tradfi_manifest_usd_lin_2026_07_18.py,
    market-tick-data-service/market_tick_data_service/scripts/recover_tradfi_chain_manifest_registration_2026_07_22.py,
  ]
```

**Locked docs (proposed, NOT written — needs operator sign-off first):**

```
plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md:
  [
    features-service/features_service/delta_one/universe/mvp_universe_filter.py,
    deployment-service/scripts/vm/launch-features-vm.sh,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/scripts/vm/create-code-tarballs.sh,
  ]
```

(`fleet_audit_triad_deferred_followups_2026_06_01.md` had no proposed list computed — the scouting agent stopped at the
lock check before doing Phase-1 analysis; a future pass should do the full scout, not just apply this stub.)

# Progress Log

- **2026-08-03**: filed during the `/context-scout` corpus-wide backfill session, after auditing which of the 78
  `NEVER_SCOUTED` docs' scouting output could not ship due to the 1000-line hard cap or a `locked_by:` field. See
  `/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md` Progress Log for that session's full ship record (66/78
  docs shipped clean, `unified-trading-pm@00037ae0c`).
