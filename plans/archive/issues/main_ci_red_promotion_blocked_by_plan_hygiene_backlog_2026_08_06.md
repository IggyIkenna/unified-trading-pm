---
doc_type: issue
title:
  "main_ci_red for unified-trading-pm: LDR→main promote PR blocked by a large plan-hygiene backlog on live-defi-rollout
  (112 archive candidates / 77 AG-closeout orphans / NA corpus over baseline) — operator decision requested"
summary: >-
  Escalation agt-80c470 (wall_type=main_ci_red, unified-trading-pm, 2026-08-06). main's quality-gates-v2 is red on 3
  lint-codex corpus checks (finalize-plan coverage, codex doc freshness, agent-rules size cap) — all 3 already FIXED on
  live-defi-rollout. But the LDR→main promote PR #2388 is blocked because the plan-hygiene hard gate
  (run_hygiene_sweep.sh --ci, folded into quality-gates-v2) fails on LDR content: 112 archive candidates (baseline 0),
  77 AG-closeout orphans (baseline 69), NA corpus over (391 vs 384 docs / 1364 vs 1347 todos). 104/112 candidates also
  exist on main. Neither main_ci_red boot remedy applies (re-firing v2 reproduces the failure; re-rolling main's stale
  quality-gates-v2.yml to the unified-trading-ci ref won't fix corpus-state checks). Only path to green main = clear the
  plan-hygiene backlog on LDR so the promote PR goes green. Operator decision requested via /blocked BLK-46fa5703
  (options A: clear backlog on LDR now, B: reclassify as plan_health / plan_reconciler, C: promotion intentionally
  paused; rec A). ALSO: this session's /done 400'd ("no active agent owns its session") — AgentRow agt-80c470 absent
  from the DB, a recurrence of cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29 (server-side fix
  agent-orchestrator@81f54a8 already shipped; see Progress Log).
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci, plan-hygiene, promotion, main_ci_red, escalation, operator-decision, recurrence]
related:
  [
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md,
    /plans/archive/issues/cicd_escalation_heartbeat_steals_slot_before_done_no_agentrow_2026_07_28.md,
  ]
created: "2026-08-06"
parent_epic: infrastructure_master
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
depends_on: [archive_candidates_content_verification_backlog_2026_08_06]
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
source: "slot 2, cicd escalation agt-80c470 (wall_type=main_ci_red, repo=unified-trading-pm, 2026-08-06)"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-ci/.github/workflows/python-quality-gates-v2.yml,
    /plans/archive/issues/archive_candidates_content_verification_backlog_2026_08_06.md,
    unified-trading-pm/scripts/plan-hygiene/check_archive_candidates.sh,
    agent-orchestrator/server/ci_reconcile.py,
    unified-trading-pm/.github/workflows/quality-gates-v2.yml,
  ]
---

# main_ci_red: promote PR blocked by plan-hygiene backlog on LDR

> **🗄️ ARCHIVED 2026-08-08 (/ag-closeout-audit ao)** — both todos `[x]` done, 0 open items. Operator ruling executed
> (option A, re-scoped as per-doc content verification via
> `archive_candidates_content_verification_backlog_2026_08_06.md`) and the causal chain independently re-verified
> 2026-08-07: promote PR #2514 (`unified-trading-pm@2c8bd8125`) `quality-gates-v2: SUCCESS`, MERGED
> 2026-08-07T23:19:35Z. Found sitting done-but-unarchived by `check_archive_candidates.sh` during this run; archived per
> `/codex/11-project-management/plan-completion-and-archival-discipline.md`.

## What I found (verified 2026-08-06, escalation agt-80c470)

1. **main is RED.** Last `quality-gates-v2` push run on main (head `7b5390649`, "fix: promote-provenance marker must
   verify true ancestry", 14:24Z) failed the lint-codex slice on 3 post-gate corpus checks:
   - Finalize-plan coverage regression (a new `assigned_vm: planning` plan shipped with no gated finalize plan)
   - Codex doc freshness regression
   - Agent-rules size cap violation (CLAUDE.md / SUB_AGENT_MANDATORY_RULES.md)
2. **Those 3 are already FIXED on live-defi-rollout** — they PASS on the promote PR runs (main ⊂ LDR; the corpus fixes
   are in the LDR-not-on-main commits).
3. **The LDR→main promote PR #2388 is genuinely BLOCKED**, not re-fireable. Its `quality-gates-v2` run fails the
   plan-hygiene hard gate (`run_hygiene_sweep.sh --ci`, a step in the checks leg) on LDR content:
   - **Archive candidates: 112** (baseline `candidate_count: 0` — must archive ALL to pass; a shrinking ratchet that
     refuses to raise)
   - **AG-closeout orphans: 77** (baseline 69)
   - **NA corpus: 391 docs vs 384 baseline, 1364 open todos vs 1347 baseline**
   - 104/112 archive candidates and 66/77 orphans also exist on main's own tree (main never surfaced them because its
     recent pushes were `[skip ci]` or failed the lint-codex slice before the plan-hygiene gate step ran).
4. **Promotion has been blocked on this backlog since ~2026-08-05 15:00Z** (last successful promote merge = PR #2276,
   14:18Z 08-05). Every promote-PR / LDR workflow_dispatch run since then is a FAILURE (0 successes across the last 300+
   QG runs for those triggers).
5. **The `ldr-to-main-promote.yml` bot keeps opening fresh per-SHA promote PRs** as LDR moves; each fails the same
   plan-hygiene gate. It is NOT wedged — it is correctly blocked on a red required check.

## Why neither boot remedy applies

- **(A) re-fire v2 on the PR head** → reproduces the same plan-hygiene failures.
- **(B) re-roll main's stale workflow** (main's `quality-gates-v2.yml` still calls the LOCAL
  `./.github/workflows/python-quality-gates-v2.yml`; LDR re-pointed to `IggyIkenna/unified-trading-ci/...@main` as part
  of the shared-CI-repo extraction) → doesn't change corpus-state checks; main would still fail them.

**Only path to green main = clear the plan-hygiene backlog on LDR so the promote PR goes green.** That is multi-hour,
judgment-heavy plan_health-class work (112 archival rituals + orphan links + NA shrink), so an operator decision was
requested rather than autonomously starting it.

## Operator decision (posted as /blocked BLK-46fa5703, 2026-08-06 ~14:40Z)

- **A (recommended):** a worker clears the full plan-hygiene backlog on LDR now — archive the 112 done-but-unarchived
  docs, link the AG-closeout orphans to their closeout family, shrink the NA corpus below baseline. Unblocks promotion
  permanently; main goes green after the promote PR merges.

  > **⚠️ A's wording above is CORRECTED by the 2026-08-06 ruling — do not execute it literally.** "Archive the 112
  > done-but-unarchived docs" reads as a mechanical batch pass. It is not one, and running it as one is actively
  > dangerous: `/plans/archive/issues/archive_candidates_content_verification_backlog_2026_08_06.md` exists precisely to
  > record that each candidate needs a per-doc content read, because "a doc can have every listed `- [ ]` checked while
  > its own summary/Progress Log still describes an open question", and that blind batch-flipping "would risk silently
  > mis-marking still-open work as resolved — **worse than staying blocked**." Proven live the same day: closing two
  > todos in `/plans/archive/issues/ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md` dropped it to 0 open todos
  > — instantly an archive candidate — while its own prose documents an unresolved, ongoing SQLite lock storm. A batch
  > pass would have archived a live production issue.

- **B:** reclassify as plan_health / route to the plan_reconciler; main stays red until the backlog is cleared.
- **C:** operator is already handling it / wants promotion paused.

## Recommended decision

- [x] ✅ [OPERATOR] P1. Decide BLK-46fa5703 (A/B/C). — **RULED 2026-08-06 (operator, interactive): A, RE-SCOPED as
      per-doc content verification.** Not B (leaves main red while all three gates grow), not C. Dispatch happened as a
      frontmatter change, not a verbal hand-off:
      `/plans/archive/issues/archive_candidates_content_verification_backlog_2026_08_06.md` flipped to
      `assigned_vm: planning` / `execution_scope: orchestrator-agent` / `assigned_role: review`, so AO workers execute
      it — the operator was explicit this runs **on the orchestrator, not in an interactive session**. That doc's
      existing todos are the method of record; see the ⚠️ correction under option A above for why the batch-archive
      reading is void. **Re-measured at ruling time** (the doc's own figures were already stale within hours):
      `check_archive_candidates` **120** (doc said 112, baseline 0), `check_ag_closeout_linkage` **81** orphans (doc
      said 77, baseline 69), `check_na_corpus_ratchet` over baseline — all three growing, which is what ruled out B/C.
- [x] ✅ [REVIEW] P2. **Re-fire / re-check the LDR→main promote PR once the backlog work lands, and confirm the causal
      chain actually holds.** — unified-trading-pm@2c8bd8125. Causal chain confirmed: 2 archive candidates (cefi cold
      compactor + sports phantom audits) cleared → `run_hygiene_sweep.sh --ci --no-regen` 0 hard failures → promote PR
      #2514 (SHA `2c8bd8125`) `quality-gates-v2: SUCCESS` → PR MERGED 2026-08-07T23:19:35Z. Plan-hygiene gate
      (`check_archive_candidates.sh`) was both necessary and sufficient.

## Progress Log

- **2026-08-06 (slot 2, cicd escalation agt-80c470):** Full diagnosis above. Posted /blocked BLK-46fa5703; no answer
  within the 2-min bounded wait, so the escalation stopped per the cicd one-shot contract. `/done` for this session
  400'd with `"one_shot_complete on slot 2 but no active agent owns its session 'orch-slot-2'"` —
  `GET /api/agents/agt-80c470` returns all-null (AgentRow absent). This is a RECURRENCE of
  cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29; the server-side fix (agent-orchestrator@81f54a8:
  heuristic reapers stamp `reaped-stale` instead of `lifecycle-complete`) was already shipped but does not repair
  already-broken rows. Rechecked slot 2 repos clean (ahead=0 on live-defi-rollout).
- **2026-08-06 (lessons, added pre-compact):** measurement traps to carry forward —
  - **"LDR is green" is a classification premise, not a measured green.** `main_ci_red` fires when main is failing and
    LDR is NOT in the failing set; but ci_reconcile's `_drop_stale_failures` treats a failing run that predates LDR's
    last commit as stale. So "main-only" here really meant "LDR advanced past the last failing run", NOT "its current
    state passes". LDR's plan-hygiene gate was actually RED on LDR content the whole time — that is what blocks the
    promote PR. Boot remedies assume real green-vs-red; verify by reading the actual promote-PR run, never the
    classification alone.
  - **A blocked promote PR is "blocked", not "wedged".** `ldr-to-main-promote.yml` keeps opening fresh per-SHA PRs and
    each fails the same required check — that is correct bot behavior. Re-firing v2 reproduces the same corpus-state
    failures; unblocking = fixing the corpus on LDR, not re-running CI.
  - **Re-rolling main's stale workflow does not fix corpus-state checks.** main's local
    `./.github/workflows/python-quality-gates-v2.yml` vs LDR's shared-CI-repo ref (`IggyIkenna/unified-trading-ci/...`)
    is a workflow-shape difference; the plan-hygiene step runs `run_hygiene_sweep.sh` against the repo's plan corpus
    either way. Remedy (B) only matters if the failure is workflow-content, not corpus-state.
  - **`GET /api/agents?session=` is unreliable for one-off lookups** (returned unrelated agents this session) — query by
    the agent id directly (`GET /api/agents/<id>`), which is what confirmed agt-80c470 is absent (all-null).
- **na-eligibility-audit 2026-08-07** (tranche=ao, autonomous): RECLASSIFY → `planning`. Re-measured live twice this
  session, ~15 minutes apart, because a sibling worker's concurrent fix (`unified-trading-pm@50b8643dc`, "fix all 5
  plan-hygiene sweep hard failures blocking LDR->main promote") landed mid-audit and changed the answer. First pass:
  archive candidates 12>0 (still failing), AG-closeout orphans 67<69 (passing), NA-corpus todos 1315>1311 (failing) —
  genuinely not yet actionable. Second pass, after the sibling's fix plus this audit's own doc3/doc4 work (which
  directly shrank the NA-doc count 381→379, crossing under baseline 380): `check_archive_candidates.sh` **0** (baseline
  0, PASS), `check_ag_closeout_linkage.py` **63** orphans (baseline 69, PASS), `check_na_corpus_ratchet.py` **379 docs /
  1308 todos** (baseline 380/1315, PASS) — all three now clear. Also added the missing `depends_on` link (the doc's own
  real precondition). The remaining `[REVIEW]` todo is now genuinely bounded and actionable: check the current LDR→main
  promote PR's `quality-gates-v2` result, and either confirm green or identify a residual cause as a separate issue — a
  checkable fact, not a judgment call. Conflict-check clear: grepped `infrastructure_master`-epic `assigned_vm:planning`
  docs for "promote PR" — 4 hits, none claim THIS specific PR/backlog-clearing follow-up (MTDS auto-merge arming, AWS
  CodeBuild webhook noise, other repos' promote PRs — all unrelated). Last live PR checked: #2435 (created 04:16:09Z),
  still `BLOCKED` at that snapshot — predates this audit's final push, so the dispatched worker should re-check the
  CURRENT promote PR fresh rather than trust this timestamp.
- **context-scout 2026-08-07**: populated/refreshed context_scope (6 entries).
- **2026-08-07 (slot 9, review task main_ci_red_promotion_blocked_by_plan_hygiene_backlog-001):** Confirmed PR #2514
  (`quality-gates-v2: SUCCESS`, MERGED 2026-08-07T23:19:35Z). Causal chain verified: archiving 2 docs (cefi cold
  compactor OOM `plans/archive/issues/cefi_live_event_cold_compactor_oom_and_legacy_path_check_2026_08_07.md` + sports
  phantom audits `plans/archive/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md`) cleared
  `check_archive_candidates.sh` from 2 candidates → 0 → hygiene sweep 0 hard failures → promote PR green + merged.
  Plan-hygiene gate was both necessary and sufficient; the earlier `content sentinel` timeout was a transient flap on
  the old high-backlog LDR, not a structural second blocker. [REVIEW] P2 flipped ✅. unified-trading-pm@2c8bd8125.
