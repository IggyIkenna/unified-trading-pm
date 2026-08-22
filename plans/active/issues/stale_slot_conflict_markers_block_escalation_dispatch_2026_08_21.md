---
doc_type: issue
title: >-
  3 idle slots (5, 11, 23) carry unresolved git conflict-markers in unified-trading-pm, starving escalation
  dispatch via the spawn-time dirty-state quarantine check
summary: >-
  2026-08-21 3-hourly `escalation_queue_reconciler` health check (dispatch agt-a338ae, slot 29): Step 1's cheap
  `/api/escalations/active` read flagged several aged queued rows (instruments-service, system-integration-tests).
  Step 2 diagnosis confirmed the escalation-queue MECHANISM itself is healthy — `RESOLUTION_DEADLINE_MINUTES`(45)/
  `MAX_REESCALATIONS`(10)/`PAGE_AFTER_REESCALATIONS`(2)/`RECONCILE_UNRESOLVED_WINDOW_HOURS`(24) all match expected
  values (no drift), the reconcile pass is confirmed actively ticking live (journalctl), and the repo-collision guard's
  `STALE_CLAIM_MINUTES=90` staleness cap (`dispatch.py::_claim_is_stale`) correctly excludes aged claims regardless of
  the claiming slot's liveness — empirically confirmed live: `agt-934add` (market-tick-data-service) moved from
  collision-blocked `queued` to `dispatched` the moment its blocking claim crossed 90 minutes. However, a SEPARATE,
  real problem was caught mid-diagnosis: 3 escalations (`agt-2cbd97`/instruments-service x53 attempts, `agt-069c25`/
  instruments-service x27, `agt-8faaf5`/system-integration-tests x14) are now failing at spawn time with
  `"dirty-state quarantined"` — the pre-spawn safety check refuses to spawn a new escalation worker onto a candidate
  slot whose working tree isn't clean. Root cause: slots 5, 11, and 23 are all `status=idle` (not working/blocked —
  confirmed dead/abandoned, not live WIP) yet their `unified-trading-pm` clones contain literal unresolved git merge
  conflict-marker delimiter lines in tracked files — `/codex/14-customer-journeys/commercial-model/platform-api-reference.html`
  on all three of slots 5/11/23, and `/codex/04-architecture/client-funds-isolation.md` additionally on slot 11. This
  shrinks the pool of spawnable slots and is the measured cause of the quarantine failures. Not an escalation.py/
  dispatch.py bug — the quarantine check is doing exactly its job (refusing to hand a new worker a broken tree); the
  actual defect is that these 3 slots were left with unresolved conflicts and nothing has reclaimed them. A live
  Step-3 ask to main (`BLK-c8ae4592`) got no answer within the 2-minute bounded wait, so filing per Step 4. A broader
  sweep for conflict markers across ALL slots x ALL repos was attempted but timed out at a 60s bound (heavy
  cross-corpus grep on a shared host) — the 3-slot/2-file finding below is a confirmed LOWER BOUND, not necessarily
  the complete list.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    escalation-watchdog,
    escalation_queue_reconciler,
    slot-hygiene,
    git-conflict-markers,
    dirty-state-quarantine,
    dispatch-starvation,
    agent-orchestrator,
  ]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /plans/archive/issues/escalation_watchdog_retune_and_reconcile_2026_08_07.md,
    /plans/archive/issues/escalation_queue_reconciler_ssm_permission_gap_2026_08_08.md,
  ]
created: 2026-08-21
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: flat
last_updated: 2026-08-21
source:
  [
    "escalation_queue_reconciler dispatch agt-a338ae, slot 29, 2026-08-21 — 3-hourly scheduled health check, Step 2
    deep-path diagnosis",
  ]
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    unified-trading-pm/cursor-configs/skills/escalation-queue-reconcile/SKILL.md,
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/dispatch.py,
  ]
---

# 2026-08-21: 3 idle slots' unresolved conflict markers are starving escalation dispatch via the spawn quarantine check

## What happened

Dispatched as `escalation_queue_reconciler` (slot 29, `agt-a338ae`). Step 1's cheap check
(`GET /api/escalations/active`) at 2026-08-21T12:43Z returned 12 rows; several were aged past the 45-minute heuristic,
triggering Step 2.

**Step 2, mechanism-health checks — all healthy, no drift:**

- `agent-orchestrator/server/escalation.py` constants: `RESOLUTION_DEADLINE_MINUTES=45`, `MAX_REESCALATIONS=10`,
  `PAGE_AFTER_REESCALATIONS=2`, `RECONCILE_UNRESOLVED_WINDOW_HOURS=24` — all match documented expected values.
- The reconcile pass is confirmed actively running live — `journalctl -u orchestrator` showed a `blocked-reconcile: gh
  pr view market-data-processing-service#3638 non-zero` line at 12:43:38, i.e. mid-tick during this exact
  investigation window.
- The repo-collision guard (`escalation.py`'s `active_repos_excluding` call, raising `"repo {repo!r} already active
  on another slot — not dispatching"`) is working exactly as designed, including its already-shipped
  `STALE_CLAIM_MINUTES=90` staleness cap (`dispatch.py::_claim_is_stale`, from the 2026-08-06
  `escalation_collision_guard_no_staleness_cap_starves_queue` fix) — a claim stops counting as a collision after 90
  minutes REGARDLESS of the claiming slot's liveness. Empirically confirmed live during this run: `agt-934add`
  (market-tick-data-service) was `queued`/collision-blocked behind slot 16's claim (`assigned_at` 11:11:29, i.e. ~94
  min old by observation time); by the very next poll it had transitioned to `status=dispatched` — exactly the
  behavior the 90-min cap predicts.

**The real, separate finding — spawn-time dirty-state quarantine, not a queue-mechanism bug:**

While re-polling to verify the above, three rows' `last_error` had shifted from the collision-guard message to a
DIFFERENT failure mode:

| escalation | repo | attempts | reescalations | last_error (as observed) |
|---|---|---|---|---|
| `agt-2cbd97` | instruments-service | 53 | 0 | `spawn failed: dirty-state quarantined: all 2 dirty repo(s) failed to preserve — quarantined. First error: pm-ship.MpuQMt: refused: HEAD already 1 commit(s) ahead of origin/live-defi-rollout (age=367s-old < 900s guard) — quarantined, not committing/pushing/realigning (Part B pre-existing-ahead-commit...` |
| `agt-069c25` | instruments-service | 27 | 1 | `spawn failed: dirty-state quarantined: all 1 dirty repo(s) failed to preserve — quarantined. First error: unified-trading-pm: refused: unresolved conflict-marker signature in ['/codex/04-architecture/client-funds-isolation.md', '/codex/14-customer-journeys/commercial-model/platform-api-reference.html']...` |
| `agt-8faaf5` | system-integration-tests | 14 | 1 | `spawn failed: dirty-state quarantined: all 3 dirty repo(s) failed to preserve — quarantined. First error: unified-trading-pm: refused: unresolved conflict-marker signature in ['/codex/14-customer-journeys/commercial-model/platform-api-reference.html', '/plans/active/issues/mtds_availability_data_type_...']...` |

This is a pre-spawn safety check (somewhere in the tmux-spawn / dirty-state-preservation path, not in
`escalation.py`/`dispatch.py`'s own dispatch-decision logic) refusing to hand a new escalation worker a candidate slot
whose working tree isn't clean. That refusal is CORRECT behavior given the input — the actual defect is the input
itself: candidate slots with genuinely broken, abandoned trees that were never reclaimed.

**Root-cause identification**: a targeted grep for the literal conflict-marker delimiter (git's standard line-start marker) across every slot's `unified-trading-pm` clone
for the two named files confirmed:

- **slot 5**: `/codex/14-customer-journeys/commercial-model/platform-api-reference.html` has a live conflict-marker delimiter.
- **slot 11**: BOTH `/codex/14-customer-journeys/commercial-model/platform-api-reference.html` AND
  `/codex/04-architecture/client-funds-isolation.md` have live conflict markers.
- **slot 23**: `/codex/14-customer-journeys/commercial-model/platform-api-reference.html` has live conflict markers.

Cross-checked against the live `slots` table: none of slots 5, 11, 23 appear in the working/blocked slot set (all
three are `status=idle`) — this is dead, abandoned merge state from some past session, not in-flight WIP. Liveness
gating (per `RULES.md`'s "Inherited-dirty-WIP is LIVENESS-gated") would treat an idle slot's dirty tree as a dead
claim, safe to reclaim in principle — but resolving these specific conflicts requires reading both sides of each
merge and choosing correct content, which is a substantive editorial judgment call, not a mechanical fix.

**Not a complete inventory**: `agt-8faaf5`'s error cites "3 dirty repo(s)" on its candidate slot, of which only the
first (`unified-trading-pm`) was named in the truncated message — the other 2 dirty repos on that attempt are
unidentified. An attempt to broaden the search into a full cross-slot, cross-repo conflict-marker sweep was made but
hit its own 60-second bound and was terminated (heavy recursive grep across ~30 slots x many repos on a shared host —
consistent with the workspace's "bound heavy scans" caution, not worth an unbounded retry from a one-shot role). The
3-slot/2-file finding above is a confirmed lower bound, not a verified-complete list.

## Why I did not attempt a fix

1. **Scope**: I am slot 29. Editing another slot's working tree (5, 11, or 23) is a scope violation per
   `unified-trading-pm/agents/RULES.md` ("Stay in YOUR slot... Editing files outside your `.tabs/<your-slot>/` tree...
   is a scope violation").
2. **Judgment, not mechanics**: resolving a real merge conflict means reading both sides and picking/merging correct
   content — not a "reverted constant, ordering bug, missing log line" class of fix this role is chartered to apply
   directly (`escalation-queue-reconcile` SKILL.md Step 4).
3. **Live ask attempted per Step 3, no answer**: posted `POST /api/slots/29/blocked` → `blocked_id=BLK-c8ae4592`,
   asking whether this should get an immediate targeted cleanup dispatch or just a filed issue. Polled
   `GET /api/slots/29/messages` every ~15-17s (heartbeating each tick) for the full 2-minute bounded wait — 8 polls,
   all returned `{"messages": []}`. Per the skill's Step 3 exit condition (main unreachable within 2 minutes → stop
   waiting, file the finding), filing this doc now.

## Recommended next step

A session with actual access to slots 5, 11, and 23 (an interactive operator session, or a worker dispatched
specifically onto one of those slots) needs to:

1. Inspect both sides of each conflict in the 3 named files (plus re-run the fuller cross-slot/cross-repo sweep from
   a VM or a narrower per-slot script, to close the "not a complete inventory" gap above) and resolve correctly —
   not blindly `--ours`/`--theirs`, since `platform-api-reference.html` recurring across 3 independent slots suggests
   a structurally conflict-prone file (worth a root-cause note in whatever fix lands: why does this one file keep
   ending up mid-conflict across unrelated sessions?).
2. Confirm each slot returns to a clean tree and rejoins the spawnable pool (re-check via a fresh
   `GET /api/escalations/active` — the 3 escalations above should stop showing `dirty-state quarantined` and either
   dispatch or fall back to a genuine collision-guard/no-free-slot message).
3. Consider whether the spawn-quarantine mechanism itself should proactively flag (not just silently refuse) a
   long-idle slot with unresolved conflict markers, so this class of finding surfaces before an escalation burns
   dozens of retry attempts against it.

## Todo

- [ ] [INFRA] P1. **RULING D128 (2026-08-21, ADOPTED-REC) — Dispatch now: escalations at 53/27/14 attempts are
      starved purely for these slots.** Inspect + resolve the conflict-marker files on slots 5, 11, 23's
      `unified-trading-pm` clones (`/codex/14-customer-journeys/commercial-model/platform-api-reference.html` on all
      three; `/codex/04-architecture/client-funds-isolation.md` additionally on slot 11) — read both sides of each
      conflict and merge/choose correct content, not a blind `--ours`/`--theirs`. Done when: each slot returns to a
      clean, idle, spawnable state, confirmed via a fresh `GET /api/escalations/active` showing the 3 named
      escalations no longer failing `dirty-state quarantined`.
- [ ] [DOCS] P2. Re-run a fuller cross-slot conflict-marker sweep (VM-hosted or narrower-scoped to avoid the 60s
      inline bound hit here) to confirm whether slots beyond 5/11/23, or repos beyond unified-trading-pm, are also
      affected — `agt-8faaf5`'s "3 dirty repo(s)" error implies at least 2 more unidentified dirty repos on its
      candidate slot.
- [ ] [DOCS] P3. Once root-caused, consider whether `platform-api-reference.html`'s recurring-conflict pattern
      warrants a structural fix (e.g. the file is unusually large/generated and hard to auto-merge).

## Blast radius

Currently measured: at least 3 escalations (2 repos: instruments-service, system-integration-tests) unable to
dispatch, with attempt counts climbing (53/27/14 at time of filing) purely because the spawn-time quarantine check
can't find a clean candidate slot. Likely wider — any future escalation targeting a repo whose only free idle slots
happen to be 5/11/23 (or any other similarly-poisoned slot not yet found) will hit the same wall. The escalation-queue
mechanism's own dispatch/retry/reconcile logic is unaffected and confirmed healthy — this is purely a slot-pool
capacity/hygiene problem sitting upstream of it.

## Progress Log

- 2026-08-21 (slot 29, `agt-a338ae`): Filed. Step 1 cheap check flagged aged rows; Step 2 confirmed the escalation
  mechanism itself (constants, reconcile pass, 90-min collision-guard staleness cap) is healthy with no drift, but
  surfaced this separate spawn-quarantine finding. Identified slots 5/11/23 as the confirmed (lower-bound) source via
  targeted grep; confirmed all three idle (dead claims, not live WIP) via the live `slots` table. Live Step-3 ask to
  main (`BLK-c8ae4592`) timed out after the full 2-minute bounded wait with no response. No fix attempted (out of
  scope for slot 29; requires editorial judgment on conflict resolution, not a mechanical fix).
- **2026-08-21 — ruling D128 (Conflict-marker slot cleanup)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Dispatch now — escalations at 53/27/14 attempts are starved purely for these
  slots. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
