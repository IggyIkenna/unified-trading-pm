---
doc_type: plan
title: AO satellite AO batch 19 — dispatch-ordering unpark + TmuxPruner wedge cross-check
summary: >-
  NINETEENTH AO-dispatch batch for the `ao` topic tranche — output of a full `/ag-closeout-audit ao` Phase 0-3 run,
  2026-08-10 (72-doc candidate corpus, generate_ag_closeout_audit_candidates.py + a per-doc Workflow classification
  pass). Of 72 ao-primary docs classified, exactly 2 bounded, conflict-clear, AO-eligible items survived direct
  verification (a Phase-1 Workflow's own ao_eligible:true calls on 2 OTHER docs were checked against those docs'
  extensive prior audit history and overridden to false — see this run's parked-findings append for detail; do not
  re-derive those two as candidates without re-reading that reasoning first).
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer]
tags:
  [ao, agent-orchestrator, ao-dispatch, close-out, batch-19, satellite-docs, satellite-extraction, dispatch-ordering]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch19_finalize_2026_08_10.md,
    /plans/active/issues/ao_dispatch_ignores_same_doc_operator_predecessor_todo_2026_08_08.md,
    /plans/active/issues/citadel_satellite_ao_dispatch_batch1_004_repeat_wedge_parked_2026_08_08.md,
    /plans/active/issues/ag_closeout_audit_ao_parked_2026_08_10.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
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
    /plans/active/issues/ao_dispatch_ignores_same_doc_operator_predecessor_todo_2026_08_08.md,
    /plans/active/issues/citadel_satellite_ao_dispatch_batch1_004_repeat_wedge_parked_2026_08_08.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  `/ag-closeout-audit ao` run, 2026-08-10 (ag_closeout_auditor, dispatch agt-6df661, slot 15). Phase 0:
  generate_ag_closeout_audit_candidates.py --tranche ao (72 members, 8 never-cited). Phase 1: a Workflow classified all
  8 never-cited + 63/64 cited-somewhere docs (1 gap closed by direct read); every ao_eligible:true verdict was then
  independently re-verified by reading the source doc + its full Progress Log before being trusted (2 of 4 initial
  true-calls did not survive this check — see parked-findings append for the full reasoning on
  `nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md` and
  `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md`, both correctly stay NA). Conflict-check: grepped
  every `status: draft`/`active` `ao_satellite_ao_dispatch_batch*` (1-18) + finalizes for both source docs' basenames —
  zero hits for `ao_dispatch_ignores_same_doc_operator_predecessor_todo`; `citadel_satellite_ao_dispatch_batch1_004`
  appears only in `ag_closeout_audit_cross_cutting_parked_2026_08_10.md` (a retag-provenance note, not a coverage
  claim). No overlap found.
---

# AO satellite AO batch 19

> **`status: draft`** — pending operator approval, same convention as batch5-18: flip to `active` to dispatch.
> **`assigned_vm: planning` / `execution_scope: orchestrator-agent`** once approved.

## Why this plan exists

A full Phase 0-3 `/ag-closeout-audit ao` sweep (72-doc candidate corpus) found the tranche in very good health — 18
prior batches already extracted essentially everything bounded and conflict-clear. Only 2 genuinely orphaned,
AO-eligible, conflict-clear items remained after direct verification of every `ao_eligible:true` classification against
each source doc's own Progress Log (not just trusting the classifier's one-line verdict):

1. `ao_dispatch_ignores_same_doc_operator_predecessor_todo_2026_08_08.md` — the underlying design decision (option a)
   was RULED 2026-08-09 and implemented; the only remaining work is the mechanical follow-through (a live `unpark` API
   call the ruling session couldn't issue) plus a verification pass. Todo 2 on that source doc ("Consider whether
   task_template.md's authoring convention should require an explicit `depends_on`...") is explicitly NOT extracted here
   — it is a genuine cross-repo design question (agent-orchestrator dispatch logic + unified-trading-pm template
   convention), not a bounded mandate; stays parked on the source doc.
2. `citadel_satellite_ao_dispatch_batch1_004_repeat_wedge_parked_2026_08_08.md` — its `[BACKEND] P1` todo's own stated
   prerequisite (`review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md` todo 1, the fleet-wide TmuxPruner root
   cause) is done and archived, so the workload-characteristic cross-check this todo asks for is now unblocked and
   independently worker-executable. The doc's OTHER two todos ([OPERATOR] P2 unpark decision, [REVIEW] P3 verify) stay
   parked — the operator's own 2026-08-09 note on todo 2 explicitly frames the unpark as "if you agree with this read,"
   i.e. still requires the operator's actual sign-off, not just execution access (unlike item 1 above, where the
   decision was already fully ruled).

## Rules for every worker on this plan

- **Do not edit either source doc's OTHER remaining checkboxes** beyond appending your evidence line to the todo you
  executed. The paired finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch19_finalize_2026_08_10.md`)
  reconciles evidence back into both source docs.
- The 2 todos below are file-disjoint (different source docs, different repos-of-action) — safe to run concurrently.
- Todo 1's `unpark` call is a single, already-decided, reversible API call (re-park is available via the same mechanism
  if it turns out to be wrong) — not a judgment call. If the live call itself errors or behaves unexpectedly, stop and
  file a fresh issue doc rather than guessing at a workaround.

## Todos

- [ ] [INFRA] P2. **Unpark the ruled-and-ready dispatch-ordering task, then verify clean re-dispatch.** Source:
      `/plans/active/issues/ao_dispatch_ignores_same_doc_operator_predecessor_todo_2026_08_08.md` todos 1 (the "standing
      follow-up" prose inside the already-`[x]`'d `[DOC] P1` todo) + 3 (`[REVIEW] P3`). (a) Issue
      `POST /api/backlog/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock-0d5981dddb99/unpark` against the live
      orchestrator (`$SERVER_URL`) — confirm the response shows the condition
      `auto_unpark__plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock-0d5981dddb99` flipped true. (b) Once it
      re-dispatches, verify via `GET /api/activity` (client-side filter by task id — the `task=` query param does not
      filter server-side, confirmed 2026-08-08) that it completes a full boot→work→done cycle without re-triggering a
      near-identical blocked-nudge. **Done when**: the task is unparked, dispatches, and completes cleanly (or, if it
      re-triggers the same block, that itself is evidence for a fresh finding — report either outcome). Repo:
      agent-orchestrator (live API action, no code change).
- [x] ✅ [BACKEND] P1. **TmuxPruner-wedge workload-characteristic cross-check.** Source:
      `/plans/active/issues/citadel_satellite_ao_dispatch_batch1_004_repeat_wedge_parked_2026_08_08.md` todo 1. Now that
      the fleet-wide TmuxPruner/keeper root cause is identified and fixed (`agent-orchestrator@e32d962`, TmuxPruner
      has-session debounce — see the archived `review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md`), check
      specifically whether `citadel_satellite_ao_dispatch_batch1-004` and `solana_dex_pool_swaps_indexer-002` (the two
      named repeat-wedge tasks) share a workload characteristic — prompt size, tool-call pattern, repo state, worktree
      size — that makes them disproportionately likely to trigger it vs. other tasks. **Done when**: a concrete
      comparison is written into the source doc citing the actual measured characteristics of both tasks (not just "no
      obvious pattern found" without having checked all four dimensions). Repo: agent-orchestrator (investigation +
      doc-writeup only, read-only). — **DONE 2026-08-10 (slot 10, backend_engineer craft, doc-writeup only — no code
      shipped).** Comparison written into the source doc todo 1 (flipped `[x]` there too). All four dimensions measured
      and checked — prompt size (briefs 111 / ~110 chars, both short; boot prompt dominated by constant CLAUDE.md),
      tool-call pattern (wedge fired `forced_precompact` 42s–2min post-`slot_boot`, before any pattern existed; keeper
      pane `context%%` trigger, not task tools), repo state (wedge pre-work, hit `[REVIEW]` tasks identically), worktree
      size (involved repos mid-range 0.9–1.8G; slot-constant, so can't discriminate). Both wedged in the SAME 2026-08-08
      17:27–18:31Z fleet-wide crash-storm (in-window: 34 forced_compact, 23 tmux_session_lost, ≥8 distinct tasks hit
      incl. non-`[DATA]`); solana-002 ran clean post-storm (market-tick-data-service@3619f9e2). **Verdict: no shared
      workload characteristic — temporal + dispatch-mechanics artifact, not task workload.**

## Codex SSOTs (read before starting)

`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`,
`/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-10 (ag_closeout_auditor, `/ag-closeout-audit ao`, dispatch agt-6df661)**: Authored after a full Phase 0-3
  sweep of the 72-doc `ao` candidate corpus. Conflict-checked against every `status: draft`/`active`
  `ao_satellite_ao_dispatch_batch*` (1-18) + finalizes — no overlap found for either source doc. See the run's own
  parked-findings append (`ag_closeout_audit_ao_parked_2026_08_10.md`) for the full per-doc classification ledger,
  including the 2 `ao_eligible:true` classifier calls that were checked and overridden to false on direct verification.

- **2026-08-10 — dispatch-enablement fix (autonomous run, slot 1).** The operator approved this batch, and
  `status: draft` → `active` was flipped accordingly. That alone did NOT make it dispatchable: this doc was authored
  `assigned_vm: NA` + `execution_scope: local-only`, both of which
  `regen_backlog_from_plan.py::_plan_contributes_briefs` rejects outright, so its 2 todos would never have reached the
  AO backlog. Its own peer batches (batch13, batch17) are `planning` / `orchestrator-agent`. Corrected to match, so the
  approval takes effect. The source parked doc's todo text ("Flip to `status: active` to dispatch") was itself
  incomplete and is the reason this was missed — noted here so the next batch approval checks all three fields, not just
  `status`.
