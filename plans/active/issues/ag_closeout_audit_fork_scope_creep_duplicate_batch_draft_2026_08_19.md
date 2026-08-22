---
doc_type: issue
title: >-
  A forked sub-agent given a narrow reconciliation task independently re-ran its parent's full Phase-1 Workflow and
  drafted a duplicate `batchN` plan — no reservation/collision-detection exists for concurrent same-tranche
  ag-closeout-audit-style batch drafting
summary: >-
  During the 2026-08-19 `/ag-closeout-audit cross-cutting` run (dispatch agt-ae73cd, slot 27), the top-level
  ag_closeout_auditor session spawned a `subagent_type: "fork"` sub-agent ("Track A") with a narrowly-scoped task
  (reconcile 4 prior outstanding parked docs + apply already-determined mistag retags). Because a fork inherits the
  FULL parent conversation context — including the parent's own narration about running the skill's Phase 1
  Workflow — the fork went beyond its assigned scope and independently re-ran a Phase-1-style classification over
  the same 49-candidate never-cited population the parent was concurrently processing, then drafted
  `cross_cutting_satellite_ao_dispatch_batch19_2026_08_19.md` and shipped it before the parent's own (independently
  drafted, non-overlapping) batch19 was ready to ship. The parent caught the collision only when its own push
  failed with a dirty-tree note, compared both drafts item-by-item (found zero source-doc overlap — genuine
  duplicate-effort, not duplicate-content), discarded its own draft, and re-shipped its items as `batch20`. No work
  was lost and no duplicate todo was created, but real live coordination overhead was spent detecting and resolving
  a collision that a naming/reservation convention could have prevented or at least flagged before either side
  wrote a file. The batchN naming scheme (`<tranche>_satellite_ao_dispatch_batch<N>_<date>.md`, N = "next number
  after the highest existing one") has no mechanism to reserve a number or detect a same-day, same-tranche
  in-flight draft before another process picks the same one.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ag-closeout-audit, fork, sub-agent-scope, concurrent-dispatch, batch-naming, agent-orchestrator, near-miss]
related:
  [
    /plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_19.md,
    /plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-19"
author: ag_closeout_auditor (cross-cutting tranche, dispatch agt-ae73cd, slot 27)
last_updated: "2026-08-19"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/issues/ag_closeout_audit_cross_cutting_parked_2026_08_19.md,
  ]
source: >-
  Discovered live during the 2026-08-19 `/ag-closeout-audit cross-cutting` run (dispatch agt-ae73cd, slot 27) — full
  incident narrative in `ag_closeout_audit_cross_cutting_parked_2026_08_19.md` Part C.
---

# Fork scope creep produced a duplicate `batchN` draft — no collision-reservation exists

## What happened (2026-08-19, cross-cutting tranche)

1. Top-level `ag_closeout_auditor` session (slot 27) began Phase 0-1 of the skill: Phase 0 discovery, then launched
   its own Phase 1 `Workflow` (49 agents) over the never-cited candidate population.
2. In parallel, the same session spawned a `subagent_type: "fork"` sub-agent with a SEPARATE, narrower task: reconcile
   4 prior dated parked docs and apply their already-determined mistag retags (an explicit Part 1/2/3 checklist with
   no mention of re-running Phase 1).
3. The fork — which inherits the parent's FULL conversation context, including the parent's own narration about
   running Phase 1 — independently ran a Phase-1-style classification of its own over the same population, found 7
   `orphaned_never_touched` candidates, and drafted + shipped `cross_cutting_satellite_ao_dispatch_batch19_2026_08_19.md`
   (`unified-trading-pm@697c15573e`) before the parent's own draft was ready.
4. The parent's own independently-derived batch19 draft (7 items, DISJOINT source docs from the fork's 6) hit a
   dirty-tree failure when it tried to ship under the same filename. The parent diagnosed the collision, verified
   zero item-level overlap, discarded its own draft, and re-shipped as `batch20`
   (`unified-trading-pm@679cde5a74`).

## Why this matters beyond this one incident

- **No data was lost and no duplicate todo landed** — this time. The collision was caught only because a git push
  failed and the parent happened to diagnose it correctly rather than force-pushing over the fork's work.
- **The root mechanism is structural, not a one-off mistake**: forks inherit full parent context by design (that's
  the point of forking — cheap, cache-shared, contextually-aware sub-agents). A narrowly-scoped fork prompt does
  NOT reliably prevent the fork from also acting on inherited narrative about what the PARENT is concurrently
  doing — the fork's own first response to this exact situation ("that was an unnecessary test call on my part…
  the two real background tasks are unaffected") shows it was visibly confused about which of "parent" vs "fork"
  it was, before eventually doing real (if scope-expanded) work.
- **The `batchN` naming convention has zero collision defense**: `generate_ag_closeout_audit_candidates.py` / the
  skill's own drafting step picks "next number after the highest existing one" by listing existing files at draft
  time — there is no lock, reservation, or "in-flight draft" marker, so two processes computing "next number" within
  the same window will independently compute the SAME number.
- This is a narrower, more far-reaching-in-practice variant of the concurrent-sharded-tranche-worker hazard the
  skill's own SKILL.md already documents (`git stash` ban for N-workers-per-tranche) — but that section assumes the
  N workers are independently AO-dispatched siblings, one per tranche. This incident shows the SAME class of
  collision can happen from a single session spawning its own fork, which is a much more common, less-visible
  pattern (any session using `Agent(subagent_type: "fork")` for ANY task is a candidate, not just this skill's own
  documented multi-tranche dispatch).

## What was NOT touched by this session (deliberately, per findings-triage — this needs a design decision)

No fix implemented here — this is a process/design gap, not a mechanical bug with an obvious one-line patch.
Candidate directions (not evaluated in depth, listed for whoever picks this up):

- A lightweight file-based or API-based reservation when a batchN draft begins (e.g. touch a
  `.batch-draft-lock-<tranche>` marker with a TTL before starting Phase 1, check-then-touch).
- Tighten fork prompts for this skill specifically to explicitly disclaim any inherited narrative about the
  parent's own concurrent Phase 1 run ("you are NOT running Phase 1, do not re-derive it from context even if you
  see it mentioned").
- Accept the current after-the-fact detection (a failed push + manual diagnosis) as sufficient, given it worked
  cleanly this time with zero data loss — document the recovery pattern (compare items, discard-and-renumber the
  loser) as the sanctioned response rather than building prevention.

## Todos

- [x] N. ✅ [OPERATOR] P3. Direction decided 2026-08-21 per D33 ruling (ADOPTED-REC, autonomous-dispatch authority,
      AUTONOMOUS_AGENT_RULES rule 2): Tighten fork-prompt language — cheapest reduction; a full lock's maintenance
      cost isn't justified by one zero-loss incident. — /plans/active/issues_corpus_completion_dispatch_2026_08_21.md
      ledger D33.
- [ ] [DOCS] P3. Implement the D33-ruled fix: tighten the fork-prompt language in
      `cursor-configs/skills/ag-closeout-audit/SKILL.md`'s "Running as one of N concurrent sharded tranche workers"
      section — generalize it to explicitly disclaim inherited narrative about a parent's own concurrent Phase 1
      run, covering single-session-forks-itself (not just AO-dispatched sibling workers). Done-when: SKILL.md's
      language is live and this doc is closed citing the commit.

## Progress Log

- **2026-08-19 (ag_closeout_auditor, dispatch agt-ae73cd, slot 27)**: filed during the cross-cutting run's
  pre-compact audit, after the live incident was caught, diagnosed, and resolved without data loss (see
  `ag_closeout_audit_cross_cutting_parked_2026_08_19.md` Part C for the full resolution trail). Recorded as a
  tracked follow-up per the workspace's "every deferral is a `- [ ]` todo, never prose" rule — this finding had
  only existed as narrative in the parked-findings doc before this entry.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche)**: KEEP-NA, valid — first verdict for this doc. Both open todos are
  explicit judgment/design calls per the doc's own text: todo 1 is a stated "genuine judgment call" between
  building a prevention mechanism vs. accepting the observed after-the-fact recovery as sufficient; todo 2 is
  gated on todo 1's outcome (nothing to implement until a direction is ruled). Not mechanically bounded. Doc stays
  `assigned_vm: NA`.
- **2026-08-21 — ruling D33 (Fork batch-draft collision prevention)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Tighten fork-prompt language — cheapest reduction; a full lock's
  maintenance cost isn't justified by one zero-loss incident. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
