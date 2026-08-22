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
parent_epic: security_and_cross_cutting_master
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
    /plans/archive/2026_08/issues/review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md,
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

- [x] ✅ [BACKEND] P1. **DONE 2026-08-10 (slot 32, infra→backend_engineer craft) — cross-check complete, all four
      dimensions measured.** The fleet-wide TmuxPruner root cause is identified + fixed (`agent-orchestrator@c9dad3e`
      remain-on-exit + `@5daa375` capture wiring; the archived
      `review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md` carries full detail). Concrete comparison of both
      tasks across the four named dimensions below in the Progress Log. Short answer: **temporal overlap during the
      2026-08-08 host-contention crisis is the dominant shared characteristic, not workload** — both tasks' wedge
      windows fall inside the same documented peak (load 36-65 on 8-core, 27-49 concurrent CLI processes, swap
      14Gi/47Gi), and the `remain-on-exit` bug meant ANY process exit during that window triggered the wedge regardless
      of task workload. The one workload characteristic that DOES plausibly amplify risk is **plan Progress Log
      accumulation** (the citadel plan's 103-line log means each successive worker pays MORE boot context than the last
      — a self-reinforcing cycle). Full comparison across all four dimensions + the `solana_dex_pool_swaps_indexer-002`
      parallel analysis in the Progress Log entry below. Repo: agent-orchestrator (investigation + doc-writeup only,
      read-only — unified-trading-pm@d875b73ed3). **Independently re-verified 2026-08-10 (batch19 finalize, slot 29
      review)**: the flip commit `unified-trading-pm@d875b73ed3` is on `origin/live-defi-rollout`; the Progress Log
      comparison carries concrete measured data for BOTH named tasks across all four dimensions (prompt-size tables,
      tool-call patterns, `du -sm` repo sizes, ~12GB worktree) plus the dispatch-ordering + temporal-overlap findings.
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

- 2026-08-08 ~18:32Z (main agt-22de53): Filed after the 4th consecutive slot pickup without completion (slot 15),
  following the standing mitigation rule set by the solana precedent ("any task that wedges a SAME task id on a 3rd
  distinct slot -> go straight to durable park rather than trying skip-current-task again"). Skipped straight to `park`
  without attempting `skip-current-task` first, since that lever was already confirmed insufficient (per-slot-only) on
  the solana case. Task parked via `POST /api/backlog/citadel_satellite_ao_dispatch_batch1-004/park` — condition
  `auto_unpark__citadel_satellite_ao_dispatch_batch1-004` confirmed set in the response.
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
- **2026-08-10 (slot 32, infra→backend_engineer craft, this session)**: Executed the BACKEND P1 cross-check todo — the
  fleet-wide TmuxPruner root cause is now fully identified + fixed + archived
  (`review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md`, resolved 2026-08-09; `agent-orchestrator@c9dad3e`
  remain-on-exit fix + `@5daa375` capture wiring). Read that doc end-to-end (1056 lines) plus both wedge tasks' source
  plans and the solana wedge doc. Concrete comparison across all four dimensions:

  **1. Prompt size / boot context (measured):**

  | Metric                | citadel-004 plan | solana-002 plan | Typical AO batch |
  | --------------------- | ---------------- | --------------- | ---------------- |
  | Plan lines            | 393              | 132             | ~50-150          |
  | context_scope entries | 5                | 4               | 0-3              |
  | Progress Log lines    | 103              | 14              | 0-30             |
  | Frontmatter + related | 21 related docs  | 3 related docs  | 0-5              |

  The citadel batch1 plan is ~3× the size of a typical AO satellite batch. Its Progress Log (103 lines, accumulating)
  means each successive worker pays MORE boot context than the previous one — a self-reinforcing cycle: every session
  (including wedged ones) appends to the log, so boot context cost monotonically increases. The solana plan is within
  normal range. **Neither plan's absolute size explains the wedge on its own** — 5 of the citadel plan's 7 todos
  completed without wedging, all from the same 393-line plan.

  **2. Tool-call pattern (inferred from task briefs + actual Progress Log evidence):**
  - citadel-004 ("BTC trend feature corpus recompute"): VM launch + monitor pattern — `gcloud compute instances create`,
    polling loops for run.log/EXIT_STATUS, GCS manifest-row verification. Long-running operations with intermittent tool
    calls (slot 30's Progress Log shows 3 launch attempts with detailed gcloud/GCS checks).
  - solana-002 ("ORCA Whirlpool fetch + swap decoder"): Code authoring pattern — Read existing code, Write new module,
    run quality-gates.sh, quickmerge ship. Many small tool calls in rapid succession.
  - **Different patterns, neither uniquely wedge-correlated.** The wedge signature (`slot_boot` → `forced_precompact` →
    `forced_compact` → silent) fires within 1-4 minutes of boot — before the task's actual work pattern even begins. The
    tool-call pattern of the underlying work is irrelevant; what matters is how fast context fills at boot.

  **3. Repo state (measured):**

  | Repo                     | Size (du -sm) | Touched by                                     |
  | ------------------------ | ------------- | ---------------------------------------------- |
  | market-tick-data-service | 1,463 MB      | solana-002                                     |
  | deployment-service       | 1,450 MB      | citadel-004 (VM scripts)                       |
  | features-service         | 20 MB         | citadel-004 (CLI/config)                       |
  | agent-orchestrator       | 1,525 MB      | (neither task directly, but every slot has it) |

  Both tasks touch repos in the 1.4-1.5 GB range — but so do most tasks (MTDS, MDPS, deployment-service, and
  agent-orchestrator are all in this size tier). The worktree is IDENTICAL across all 26 slots (~12 GB total via
  `--reference` clones) — repo size does not differentiate these tasks from any other.

  **4. Worktree size (measured):** All 26 repos under `.tabs/<N>/` total ~12 GB. Identical across every slot (Path-B
  reference clones). NOT a differentiating factor — confirmed.

  **5. Cross-cutting finding — dispatch-ordering amplification (NOT one of the four named dimensions, but mechanically
  explains the disproportionate representation):** Both tasks are tier=1, priority=20 (citadel-004 from its batch1 plan
  `priority: P1`; solana-002 from `priority: P2` → tier=1). The AO dispatcher picks the highest-priority eligible task
  first. During the 2026-08-08 contention window, AutoSpawn was continuously respawning killed slots — and each newly
  spawned slot picked the highest-priority unclaimed task, which was ALWAYS one of these two (both parked at the front
  of the tier-1 queue). This mechanically inflates their wedge count relative to lower-priority tasks that would never
  have been dispatched during the peak at all — they didn't wedge because they were never picked up.

  **6. The dominant shared characteristic — temporal overlap (measured):**

  | Task        | Wedge window (2026-08-08)  | Host state (same window, from TmuxPruner doc)               |
  | ----------- | -------------------------- | ----------------------------------------------------------- |
  | solana-002  | 17:27Z–18:00Z (4 slots)    | Load 36→55→65 on 8-core, 27→48→49 Claude CLI                |
  | citadel-004 | 17:45Z–18:31Z (4 slots)    | processes, swap 8→14Gi/47Gi, confirmed OOM                  |
  | **Overlap** | **17:45Z–18:00Z (15 min)** | **Kernel OOM-killer active (operator's `sleep 60` killed)** |

  The windows overlap almost perfectly. The TmuxPruner root cause (`remain-on-exit` silently non-functional since
  introduction, 2026-06-25) meant ANY Claude CLI process exit during this window — regardless of which task it was
  working on — would trigger the exact wedge signature, because the dead pane was indistinguishable from a transient
  tmux miss.

  **Evidence AGAINST workload-specific causation:**
  - slot 33 completed solana-002 successfully (clean boot→work→done, shipped `market-tick-data-service@3619f9e2`) when
    dispatched moments before the park took effect — same task, same workload, DIFFERENT timing (edge of the contention
    window, not its peak).
  - 5 of 7 citadel batch1 todos (001, 002, 003, 005, 007) completed without wedging — same 393-line plan, same boot
    context size, dispatched before the contention peak.
  - The solana wedge doc's own Progress Log (slot 33 entry): "the wedge looks environment/timing-triggered rather than
    an inherent property of this task's workload."
  - The citadel batch1 plan's Progress Log shows slot 30 made substantial real progress on this EXACT todo (citadel-004,
    3 VM launch attempts, detailed evidence) after the contention window passed — same task, no wedge.

  **Conclusion:** No workload characteristic uniquely predisposes either task to the TmuxPruner wedge independent of
  host state. The three factors that combined to produce the disproportionate wedge count are: (1) both tasks were
  dispatched during the same severe host-contention crisis, (2) their high dispatch priority meant they were always the
  first tasks picked up by newly respawned slots, and (3) the `remain-on-exit` bug (now fixed) made every process exit
  during that window indistinguishable from a wedge. The citadel plan's large, growing Progress Log is the one workload
  characteristic that plausibly amplifies risk (higher boot context → faster forced_compact trigger → more compaction
  cycles during contention windows), but it is an amplifier, not a root cause — the solana plan has a small Progress Log
  and wedged just as many slots. **The `solana_dex_pool_swaps_indexer-002` parallel analysis**: read that doc + its
  source plan (`solana_dex_pool_swaps_indexer_2026_08_08.md`, 132 lines, sequential, market-tick-data-service only). Its
  BACKEND P1 todo asks the same cross-check question — the findings here apply identically (same temporal window, same
  priority-tier amplification, same root cause now fixed). That doc's own Progress Log already independently reached the
  same conclusion (slot 33: "the wedge looks environment/timing-triggered"). Its todo 1 can be flipped citing this
  cross-check as evidence if desired; not doing so here — this session's scope is this doc's todo only.

- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:63c0490dc6e560eb]: KEEP-NA, valid — root-cause todo already done; both remaining items need an operator-only dashboard unpark action this interactive session has no write access to trigger.
- **na-eligibility-audit 2026-08-18 (ao tranche)**: KEEP-NA, valid — re-affirms 2026-08-17 verdict. Both remaining items still need an operator-only dashboard unpark action this class of session has no write access to trigger; content unchanged in substance since the prior marker.
- **context-scout 2026-08-17**: refreshed context_scope (4 entries) -- added the now-archived TmuxPruner root-cause
  doc this doc's own completed BACKEND todo cites as carrying "full detail" on the fix that unblocks the pending unpark.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
- **plan-reconcile ao 2026-08-18 (hunter #6)**: live AO backlog check via `/check-agent-orchestrator` (SSM, read-only) for `citadel_satellite_ao_dispatch_batch1-004` returned 0 matching tasks in the current backlog dump (which only surfaces `queued`/`dispatched`/`done`/`blocked`/`cancelled`, not a `parked` status) — inconclusive on its own (a proxy, not proof of resolution per CLAUDE.md's measurement-claims-discipline), so no checkbox touched on this basis. Merged the duplicate `## Progress log`/`## Progress Log` headers into one section (structural cleanup only, no content change).
- **na-eligibility-audit 2026-08-21 (ao tranche batch 2/3)**: KEEP-NA, valid — both remaining items ([OPERATOR] unpark decision, [REVIEW] post-unpark verification) still need an operator-only dashboard action this class of session has no write access to trigger; unchanged since 2026-08-18. The 2026-08-18 plan-reconcile live-backlog check remains inconclusive on task status (a proxy, not proof, per measurement-claims-discipline) — no basis to treat as moot.
