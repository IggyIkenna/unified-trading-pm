---
doc_type: issue
title:
  citadel_satellite_ao_dispatch_batch1-004 wedged/failed on 4 different slots within ~1h via the fleet-wide post-compact
  respawn signature — durably parked
summary: >-
  Task `citadel_satellite_ao_dispatch_batch1-004` cycled through 4 consecutive slots (26, 23, 3, 15) between ~17:45Z and
  ~18:31Z on 2026-08-08 without ever completing — slots 26 and 23 hit the confirmed `slot_boot`->`forced_precompact`->
  `forced_compact`->silent (`worker_alive:false`) signature and were escalated via `reassign kill_worker:true`; slot 3
  never showed the classic wedge signature but also never completed the task (`slot_resume_skipped` at 18:28:21Z, ~6 min
  after boot, no completion event) before the task was redispatched again to slot 15. Same fleet-wide crash-loop pattern
  tracked in `review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md`, but — like
  `solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md` before it — this ONE task is disproportionately
  re-triggering it. Durably parked via `POST /api/backlog/{task_id}/park` (condition
  `auto_unpark__citadel_satellite_ao_dispatch_batch1-004`) per the standing 3rd-distinct-slot mitigation rule, to stop
  the churn while the fleet-wide root cause is being investigated.
status: open
nature: issue
asset_group:
  [ao] # corrected 2026-08-10 (/ag-closeout-audit cross-cutting) -- was [cross-cutting]. Content is 100% AO
  # fleet-wide slot-wedge/crash-loop reliability (repos:[agent-orchestrator]); its own todo 1 depends on
  # review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md, same incident/repo/author, tagged [ao] not
  # cross-cutting -- direct in-corpus evidence of the correct tranche.
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, tmux, crash-loop, task-affinity, live-incident, spawn-overhead, park]
related:
  - /plans/archive/2026_08/issues/review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md
  - /plans/active/issues/solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md
  - /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md
created: 2026-08-08
author: agt-22de53 (main)
parent_epic: infrastructure_master
priority: P1
source: >-
  Main-agent routine stale-slot sweep (STEP 2.4/2.6), 2026-08-08 17:45Z-18:32Z window. Escalated straight to durable
  park once the task hit a 4th distinct slot without completing, per the standing mitigation rule established in the
  solana repeat-wedge precedent.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-08
locked_since:
context_scope:
  [
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/routes/slots_ops.py,
    agent-orchestrator/server/auto_park.py,
  ]
---

# citadel_satellite_ao_dispatch_batch1-004 repeat-wedge — durably parked pending root cause

## What was found

Live, directly-observed during routine stale-slot sweeps (not a self-report):

| #   | Slot | `task_dispatched` | Outcome                                                                                                                                   |
| --- | ---- | ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | 26   | 17:45:47Z         | `slot_reassigned` 17:49:42Z (confirmed `forced_precompact`->`forced_compact`->silent signature) -> `reassign kill_worker:true`            |
| 2   | 23   | 18:09:18Z         | `slot_reassigned` 18:12:44Z (same confirmed signature) -> `reassign kill_worker:true`                                                     |
| 3   | 3    | 18:22:43Z         | `slot_resume_skipped` 18:28:21Z (~6min after boot, no completion event, no classic forced_compact signature but also no forward progress) |
| 4   | 15   | 18:31:41Z         | In progress at time of park decision — task parked before slot 15 could also fail                                                         |

Occurrences 1 and 2 are the identical fleet-wide signature already tracked in
`review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md` todo 1. Occurrence 3 is a variant (no forced_compact
silence, but still failed to make progress and released the task) — worth noting for whoever investigates the root cause
that the failure mode on this task isn't limited to the exact `forced_compact`->silent signature.

## Why it matters

- Same spawn-overhead/continuity cost as the tracked fleet-wide pattern, concentrated on one task: 4 wedge/release
  cycles in ~45 minutes with zero forward progress on the actual dispatch-batch work.
- Mirrors the `solana_dex_pool_swaps_indexer-002` precedent closely enough that the same "one task disproportionately
  re-triggers the fleet-wide issue" hypothesis applies — worth checking both tasks for a shared workload characteristic
  once the fleet-wide root cause (todo 1 in the TmuxPruner doc) is identified.

## Todos

- [x] ✅ [BACKEND] P1. Once `review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md` todo 1 identifies the
      fleet-wide TmuxPruner/keeper kill root cause, check specifically whether
      `citadel_satellite_ao_dispatch_batch1-004` (and `solana_dex_pool_swaps_indexer-002`) share a workload
      characteristic (prompt size, tool-call pattern, repo state, worktree size) that makes them disproportionately
      likely to trigger it vs. other tasks. Repo: agent-orchestrator. — **DONE 2026-08-10 (slot 10,
      `ao_satellite_ao_dispatch_batch19` todo 2, backend_engineer craft): NO shared workload characteristic — the
      repeat-wedge was a temporal + dispatch-mechanics artifact of the fleet-wide crash-storm, not a task-workload
      property. Full 4-dimension comparison (all four CHECKED with concrete measured data):** - **Prompt size — NOT a
      differentiator.** `citadel_satellite_ao_dispatch_batch1-004` brief = **111 chars** (live `GET /api/backlog` query,
      2026-08-10); `solana_dex_pool_swaps_indexer-002` brief was the same ~110-char plan-todo text (`[DATA] P1`, row now
      zeroed post-`done`). Both short, average `[DATA]` tasks. The boot prompt is dominated by the constant auto-loaded
      CLAUDE.md (~40 KB cap, identical for every task) + role files; the task-specific delta is ~110 chars. -
      **Tool-call pattern — NOT a differentiator.** Wedge fired at `forced_precompact` **42s–2 min after `slot_boot`**
      (slot 26: boot 17:46:06Z → forced_precompact 17:46:48Z; slot 11: boot 17:28:44Z → forced_precompact 17:30:44Z,
      2026-08-08) — before any task-specific tool-call pattern was reachable. The trigger is the keeper's pane
      `context%%` read (`context_lifecycle._read_pct`/`_tick_worker`, agent-orchestrator), independent of the task's
      tool calls. The identical early-boot wedge hit OTHER tool-call profiles in the same window — e.g. REVIEW/doc-role
      tasks `defi_expected_unattempted_backlog_1m_2026_07_03_finalize-002` and
      `ao_false_done_backlog_rows_and_unresolved_plan_refs-007` (slots 26). - **Repo state — NOT a differentiator.** The
      wedge hit at boot, before any repo work; the same slots later completed other tasks on the same repos. Both tasks
      are `[DATA]`, but `[REVIEW]` tasks wedged identically in the same window. - **Worktree size — NOT a
      differentiator.** solana-002 touches market-tick-data-service (measured 1.6G); citadel-004 touches
      features-service (1.8G) + deployment-service (932M) — mid-range of the fleet (execution-service 1.3G,
      strategy-service 594M, unified-trading-pm 915M). Decisively, worktree size is SLOT-CONSTANT (every slot clone
      holds every repo; the task only selects which to work), and the wedge was slot-level — slot 11 and slot 26 each
      wedged THREE DIFFERENT tasks in the same window — so it cannot discriminate between tasks. - **Actual mechanism
      (positive finding).** Both tasks wedged in the SAME 65-min window (2026-08-08 17:27–18:31Z) = the fleet-wide
      crash-storm peak (root-caused + fixed in the archived `review_slot1_tmuxpruner…` doc: remain-on-exit no-op +
      liveness false-positives + host contention; `agent-orchestrator@e32d962`/`c9dad3e`/`5a163e7`/`dd01255`).
      Fleet-wide in that window (live `GET /api/activity`): **34 forced_compact, 34 forced_precompact, 23
      tmux_session_lost, 32 worker_kicked, 12 forced_compact_ineffective** — wedge-signature events hitting **≥8
      distinct tasks** (solana-002, citadel-004, sports_taxonomy_p1_capture_and_contracts-019/-020,
      defi_compute_gcp_migration-008, defi_expected_unattempted…-finalize-002, ao_false_done_backlog_rows…-007,
      blocked_questions_ux_redesign…-001, cefi_chain_drop…-313de9df1f98, ao_satellite_ao_dispatch_batch7-003,
      defi_venue_lst_rates_residual-001). The two named tasks were merely tier-1/prio-20-50 queued tasks re-dispatched
      during the storm; each re-dispatch handed them to the next free slot, which wedged the same way — `park` was the
      only lever that stopped the churn (dispatch-mechanics artifact, not a workload signature). **Direct confirmation
      they are not inherently wedge-prone**: solana-002 ran CLEAN boot→work→done on slot 33 right after the storm
      (market-tick-data-service@3619f9e2, 24 tests); a COMPLETED task in the same window (defi_compute_gcp_migration-008
      on slot 11) hit forced_precompact→forced_compact and still succeeded; citadel-004's underlying P2.11.16 work was
      being executed on 2026-08-10 (slot 30). **Verdict**: no shared workload characteristic across any of the four
      dimensions — the wedge tracked host/time, not task.
- [ ] [OPERATOR] P2. **CHECKED 2026-08-09 (operator, interactive session) — LEAN UNPARK, best odds of the 3 sibling
      parked tasks, not a guarantee.** `agent-orchestrator@dd01255` (cited by one prior sub-agent pass) does NOT apply
      here — it fixes chat-loop-role (review/main) liveness, not standard worker dispatch. The relevant fix is
      `agent-orchestrator@e32d962` (TmuxPruner has-session debounce), confirmed live — and unlike
      `defi_compute_gcp_migration-009`, occurrences 1+2 in the table above ARE the exact classic
      `forced_precompact`→`forced_compact`→silent signature that fix targets. Occurrence 3 (slot 3,
      `slot_resume_skipped`, no forced_compact) is a different, still-unexplained variant, so this isn't a clean "root
      cause fixed" — but 2 of 4 failures matching a now-live fix is meaningfully better evidence than
      `defi_compute_gcp_migration-009`'s 3/3 unfixed-signature record. **I can't call
      `POST /api/backlog/citadel_satellite_ao_dispatch_batch1-004/unpark` from this interactive session — no write
      access to the orchestrator API from this checkout.** Operator: trigger the unpark via the dashboard directly if
      you agree with this read; if it re-wedges, that itself is useful evidence the residual (occurrence-3-shaped)
      mechanism is still live.
- [ ] [REVIEW] P3. Once unparked and re-dispatched, independently verify via `GET /api/activity` (filtered client-side
      by `task_id`, the `task=` query param does not actually filter server-side — confirmed 2026-08-08) that it
      completes a full boot->work->done cycle without re-wedging. Repo: unified-trading-pm (verification + checkbox flip
      only).

## Progress log

- **2026-08-10 (slot 10, `ao_satellite_ao_dispatch_batch19` todo 2, backend_engineer craft — investigation + doc-writeup
  only, no code shipped)**: Executed todo 1 (the workload-characteristic cross-check), now unblocked by the TmuxPruner
  root-cause closure. Measured all four dimensions against live orchestrator state + plan/docs: brief sizes (111 chars
  citadel-004 vs ~110 chars solana-002, via `GET /api/backlog`), worktree sizes of the involved repos (MTDS 1.6G,
  features 1.8G, deployment 932M — mid-range of the fleet), and the full `GET /api/activity` event streams for slots
  11/9/33/7/26/23/3/15 in the 2026-08-08 17:00-19:00Z window. Conclusion: **NO shared task-workload characteristic** —
  both tasks wedged during the SAME fleet-wide crash-storm window (2026-08-08 17:27-18:31Z), and the identical signature
  hit ≥8 distinct tasks including non-`[DATA]` REVIEW/doc tasks. The "repeat-wedge" appearance is a dispatch-mechanics
  artifact (the tier-1/prio-20-50 tasks kept being re-picked by the next free slot during the storm; `park` stopped the
  churn), corroborated by solana-002 running clean post-storm. Full comparison appended to todo 1 above.

- 2026-08-08 ~18:32Z (main agt-22de53): Filed after the 4th consecutive slot pickup without completion (slot 15),
  following the standing mitigation rule set by the solana precedent ("any task that wedges a SAME task id on a 3rd
  distinct slot -> go straight to durable park rather than trying skip-current-task again"). Skipped straight to `park`
  without attempting `skip-current-task` first, since that lever was already confirmed insufficient (per-slot-only) on
  the solana case. Task parked via `POST /api/backlog/citadel_satellite_ao_dispatch_batch1-004/park` — condition
  `auto_unpark__citadel_satellite_ao_dispatch_batch1-004` confirmed set in the response.
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
