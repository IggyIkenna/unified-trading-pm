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
    /plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
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

- [x] ✅ [SCRIPT] P2. **DONE 2026-08-03 (slot-12).** Trim or split each of the 6 exactly-1000L docs, then re-apply their
      pre-computed `context_scope` (below).** Preferred approach per this corpus's own precedent
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
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-03 (same session).** Trim
      `plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` (999L pre-commit) — extracted the
      full 2026-08-02→2026-08-03 corroboration-wave history (677 lines, round 2 of this doc's own recurring remediation
      pattern) to
      `/plans/archive/2026_08/fleet_wide_qg_capacity_crisis_continues_day2_progress_log_history_2026_08_03.md`, kept
      only the 2 most recent live entries, re-applied `context_scope` (5 entries) — `unified-trading-pm@fcfd66f5e`.
      Verified via word-level (whitespace-normalized) diff: zero content removed across live+archive vs the original.
- [ ] [SCRIPT] P3. **`plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` — STILL OPEN,
      deliberately not attempted mechanically 2026-08-03.** This doc already went through TWO prior line-cap extraction
      rounds (2026-07-23 umbrella-split, 2026-07-24 second-tier extraction) — every major section is already down to a
      short verdict-pointer stub pointing at an archive doc. What remains is either (a) a LIVE operational runbook (the
      "Pre-migration drain" section's exact resume commands — 48 GCP schedulers + 26 AWS EventBridge rules to re-enable
      post-migration, still needed, not history) or (b) active coordination content (Gate-State Board, Dispatch waves,
      Sub-plan registry, Master coordination todos) that the orchestrator reads as current state, not narrative history.
      Forcing a mechanical trim here risks removing something still load-bearing rather than genuine closed history.
      **Needs a dedicated, careful read-through by whoever picks this up next — not a mechanical batch trim** — to find
      a genuinely safe extraction candidate (or conclude none exists and this doc needs a different remediation shape,
      e.g. promotion to `plans/epics/` at the 2000L epic cap instead of the 1000L active-plan cap, given its role as the
      migration's own coordinator).
- [x] ✅ [SCRIPT] P3. **DONE 2026-08-03 (same session).** Trimmed
      `plans/active/tradfi_manifest_content_recovery_completion_2026_07_24.md` (1000L pre-commit) — extracted the full
      "2026-07-21/22 continuation" Progress Log section (140 lines, zero open todos, round 2 of this doc's own recurring
      remediation pattern) to
      `/plans/archive/2026_07/tradfi_manifest_content_recovery_completion_history_2026_08_03.md`, re-applied
      `context_scope` (6 entries) — `unified-trading-pm@f7b4c03d6`. Verified via exact `diff` (byte-identical
      extraction) + line-count reconciliation (860 kept + 140 extracted = 1000 original).
- [x] ✅ [OPERATOR] P3. **RESOLVED 2026-08-03 — no operator action was actually needed.** Re-read `plans/PLAN_FORMAT.md`
      § "Plan Locking": `locked_by:` blocks ARCHIVAL only ("Agents MUST NOT archive locked plans"), not ordinary
      additive frontmatter edits. `context_scope` is exactly such an edit — applied to both locked docs directly, no
      unlock needed, no archival attempted:
  - `plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`
    (`locked_by: live-defi-rollout`, 1 open todo — genuinely not archival-eligible, but that's irrelevant here)
  - `plans/active/issues/fleet_audit_triad_deferred_followups_2026_06_01.md` (`locked_by: harsh-fleet-audit`, an
    explicit human "let it be" parking doc with 4 open todos — same reasoning, still not archived, just scouted)
  - Both shipped `unified-trading-pm@fcfd66f5e`. The earlier framing of this as `[OPERATOR]`-gated was itself the
    finding: it over-read the lock's scope. No carve-out is needed in `ao_satellite_ao_dispatch_batch3_2026_07_31.md`'s
    own `FieldSpec` flip todo — both docs are now genuinely scouted, same as any other doc.

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
- **2026-08-03 (slot-12) — DONE.** Trimmed all 6 exactly-1000L docs per the extraction pattern (completed/historical
  Progress Log entries moved verbatim to a new `plans/archive/2026_08/<doc>_progress_log_history_2026_08_03.md`
  companion per doc, a pointer note left in place, Todos sections untouched), then re-applied each doc's pre-computed
  `context_scope` (verified every path still resolves on disk before applying) and bumped `last_updated`. Result line
  counts (all well under the 1000L cap, no todo dropped): `ao_open_issues_consolidated_close_out_2026_07_17.md`
  1000→877L, `data_completion_cefi_2026_07_15.md` 1000→801L, `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`
  1000→866L, `data_completion_to_100_all_ag_2026_06_21.md` 1000→778L (a 3rd remediation pass on this doc — the extracted
  47 entries were themselves already-folded-out stub pointers left over from a 2026-07-24 fold-out, no primary content
  lost), `instruments_completion_tracker_2026_07_06.md` 1000→697L. Verified each with
  `bash scripts/plan-hygiene/check_line_caps.sh <path>` (scoped mode, all ✅ within cap) and `check_frontmatter.sh`/YAML
  parse (all clean). Full quality-gates.sh run clean (warn-only findings unrelated to this change). Checkbox flipped
  here.
- **2026-08-03 (same interactive session, slot 1, continued after slot-12's dispatch landed)**: trimmed + re-scouted
  `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` (round 2 of its own recurring extraction pattern) and
  `tradfi_manifest_content_recovery_completion_2026_07_24.md` (round 2, same pattern); applied `context_scope` to both
  locked docs after re-reading `plans/PLAN_FORMAT.md` and confirming `locked_by:` only blocks archival, not additive
  frontmatter edits — no unlock needed, no archival attempted. Shipped `unified-trading-pm@fcfd66f5e` (locked docs +
  fleet_wide) and `@f7b4c03d6` (tradfi). Deliberately did NOT force a trim on
  `master_data_canonicalisation_migration_catalogue_2026_06_07.md` — already twice-extracted, no safe historical content
  left, remaining bulk is live operational/coordination content; left as a genuinely open, clearly-scoped todo above
  rather than risk removing something load-bearing. **This doc still has 1 open todo, so it stays `active` per the
  archival ritual's zero-open-todos gate** — do not archive until that todo lands. **Lesson from this stretch**: making
  a new uncommitted edit to an unrelated file WHILE a different background quickmerge is still mid-flight in the same
  working directory can get that edit silently clobbered by the other run's own pull/stash cycle (confirmed once this
  session — a completed edit reverted to HEAD with no trace in `git stash list`, no data lost since the recipe +
  archive-doc target were still reconstructable, but redo work was needed); the fix is procedural — never touch this
  repo's working tree while a quickmerge you started is still running.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — added the sibling
  `ao_satellite_ao_dispatch_batch3_2026_07_31.md` (the plan whose context_scope FieldSpec flip todo this issue directly
  unblocks).
- **2026-08-03 (same interactive session, continued)**: root-caused why STALE was so much larger than NEVER_SCOUTED —
  `generate_context_scope_inventory.py`'s git-fallback (docs with no `last_updated:` frontmatter) treated ANY commit
  touching the file as proof of real content drift, with no concept of "mechanical reference-field repoint" (a cited doc
  archives/moves → every referrer's `context_scope`/`related`/`supersedes`/`superseded_by`/`depends_on` gets a
  bot-driven path rewrite, which isn't a content change). Measured: 169/304 STALE docs were on this fallback path, and
  103/169 (61%, ~34% of the corpus-wide STALE count) had ONLY this class of commit as their most recent touch. Fixed by
  walking bounded history (`_MAX_HISTORY_WALK=5`) and classifying each commit's diff against the reference-field block
  boundaries in the file's content AT that commit (not current HEAD's positions — an earlier same-session attempt reused
  current-file line offsets and made the count worse, reverted). Shipped `unified-trading-pm@256db458e`; validated clean
  (`ruff check`, `ruff format --check`, `basedpyright`) and via 2 consecutive full-corpus runs (3:19 wall-clock, down
  from an initial always-correct-but-slow 12:05). A different slot (slot-10) independently found + fixed a complementary
  false-**UP_TO_DATE** edge case in the same heuristic the same day (`unified-trading-pm@8470b3a70`) — the two fixes
  compose; final numbers below reflect both. Then re-scouted the full STALE+NEVER_SCOUTED backlog this fix surfaced (289
  docs; 1 excluded — `master_data_canonicalisation_migration_catalogue_2026_06_07.md`, tracked above as its own open
  todo) via a 24-batch `Workflow` fan-out (sonnet, 12 docs/batch) — 288/288 docs scouted clean, 0 errors, 0 skips
  (~5.25M subagent tokens, ~23 min). Verified every resulting diff was scoped to `context_scope:` + one Progress Log
  marker line before shipping (max single-file diff: 17 lines). Shipped in 6 quickmerge batches of ~50 files:
  `unified-trading-pm@657466188`, `@c394cd49e`, `@9463578a6`, `@3fac05949`, `@d4f9c0a09`, `@b3caa670a`. Final
  post-rescout inventory: **634 UP_TO_DATE / 7 STALE / 2 NEVER_SCOUTED** of 643 in-scope docs (down from 355/284/5 of
  644 pre-fix) — the residual 9 are new/touched-mid-session docs from other concurrent slots' work, the normal small
  backlog the hourly `context-scout.timer` picks up next run, not a gap in this pass.
  - **Recurring incident this stretch, now with a root cause**: shipping into this shared, heavily-concurrent clone hit
    real `git stash`-pop conflicts (quickmerge's own STAGE 0.4/5 auto-reconcile stashes the working tree, pulls, pops) —
    every single conflict across ~15 files was the SAME shape: another autonomous process (na-eligibility-audit, an
    operator-executed sweep, a todo-flip) appended its own Progress Log entry at the exact same end-of-file point my
    context-scout marker did. All were pure append/append collisions (verified via the 3-way `|||||||` base before
    resolving), safely resolved by keeping both sides; one delete/modify conflict (a doc archived mid-session by another
    process) resolved by accepting the archival, since an archived doc is out of `context_scope`'s in-scope status set
    anyway. Also hit the documented `shared_clone_concurrent_commit_message_swap_2026_07_28.md` class (quickmerge
    amended a foreign commit's trailer, content untouched, no data lost — caught via its own WARN, content re-verified
    via `git show --stat HEAD` before trusting anything) and transient `index.lock` contention from the standing
    `slot-cron-ff-pull.sh` 5-min cron plus another slot's own concurrent quickmerge (both benign, resolved on retry).
    Separately: `quickmerge.sh --files` takes SPACE-separated paths, not comma-separated — passing a comma-joined list
    makes its internal path-splitting treat the whole string as one literal (non-existent) path, which silently
    short-circuits to "no uncommitted changes, already committed" and can cause it to amend whatever commit happens to
    be at HEAD instead of committing your files. Caught before any content was lost (post-hoc `git show --stat`
    verification after every batch), but cost 2 wasted quickmerge cycles before switching to space-separation.
