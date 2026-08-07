---
doc_type: issue
title: >-
  AO worker slot pinned at 100% context / `pressure=thrashing` for 3+ hours — forced /pre-compact+/compact submits
  succeed every cycle but never reduce measured context%, and workers have no Tier-2 recycle escape unlike main/review
summary: >-
  Confirmed live (2026-08-06, ~10:30 UTC) via a read-only `state.db` query: orchestrator slot 3 (`status: working`,
  `context_used_pct: 100`, `context_pressure: thrashing`, `compactions_total: 160`) has been cycling `forced_precompact`
  → `forced_compact` roughly every 15-90 minutes since at least 07:39 UTC (8+ consecutive cycles in the sampled window),
  every submit confirmed `"submitted": true` (the pane genuinely received the injected `/pre-compact` and `/compact`
  text — this is NOT the already-fixed
  `cefi_tardis_derivative_ticker_historical_gap_ao_context_pct_stuck_post_compact_2026_08_06` submit-verification bug),
  yet `last_compacted_at` has not advanced past 07:42:13 and no `context_compact_observed` event (which requires a
  ≥25-point pct drop between keeper ticks) appears anywhere in the same window. Compare slots 4/6/7/9/14, sampled in the
  same query: all hit 100% at some point today and all show the SAME forced_precompact/forced_compact cycling, but each
  one EVENTUALLY produced a real `context_compact_observed` drop (e.g. slot 9: 100→0 three times in under 2 hours; slot
  14: 91→15 at 10:35) and is now healthy. Slot 3 is the one exception in the sample: the force mechanism is firing
  exactly as designed and is NOT stuck-on-submit, but the compaction it triggers is not actually working for this
  specific session — a materially different, still-open failure mode from the bug already fixed one day earlier.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, context-lifecycle, thrashing, compaction, worker-recycle]
related: []
created: 2026-08-06
author: interactive-session (tab 1)
priority: P2
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: agent-orchestrator@e608378
source:
  [
    "discovered 2026-08-06 while investigating whether the FleetView dashboard's 100%-context rows were real or stale —
    read-only state.db query (slots + activity_log) via query-ao-state-db-readonly.sh",
  ]
context_scope:
  [
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/tmux_spawn.py,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
  ]
---

> **🟢 ARCHIVED 2026-08-07** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule (trigger 2: a commit SHA fixes the issue). All 3 todos resolved by a parallel session's SAME
> live incident, filed independently the same day as
> [`/plans/archive/issues/ao_worker_context_saturation_unrecoverable_2026_08_06.md`](/plans/archive/issues/ao_worker_context_saturation_unrecoverable_2026_08_06.md)
> (both describe prod slot 3, `compactions_total: 160`, `context_pressure: thrashing`) — that doc's 7/7 todos shipped
> and archived first; this doc's own todos went stale-unflipped until this audit cross-checked them. Moved by the
> na-eligibility-audit 2026-08-07 ao-tranche pass.

# Worker slot stuck thrashing: force-compact submits but never reduces context%, and has no recycle fallback

## What I found

`context_lifecycle.py`'s module docstring (2026-08-05 ruling) splits behavior in two: main/review get a **Tier 2
checkpoint-recycle** escape (write a checkpoint, exit the session, respawn fresh) after N compactions in a window OR on
`pressure == "thrashing"`; workers get **only** the unconditional Tier-1 force `/pre-compact`→`/compact` inject, with no
recycle path mentioned anywhere in `_tick_worker`. Slot 3's live state shows exactly the scenario that gap doesn't
cover: `context_pressure: "thrashing"` (the same signal that WOULD trigger main/review's recycle), but as a worker it
only ever gets re-forced into the same compact cycle that has already failed to reduce its pct across 8+ consecutive
attempts.

Evidence (live query, 2026-08-06 ~10:30 UTC):

```
slot 3: status=working, context_used_pct=100, context_pressure=thrashing,
        compactions_total=160, last_compacted_at=2026-08-06 07:42:13
```

`activity_log` for slot 3 in the preceding ~3 hours: 8 paired `forced_precompact`/`forced_compact` events, ALL
`"submitted": true`, ZERO `context_compact_observed` events (which log only on a ≥25-point pct drop). By contrast, every
other sampled slot (4, 6, 7, 9, 14) shows the same forced-cycle pattern but WITH interleaved `context_compact_observed`
drops, and is measurably healthy at query time (pct 0-25%, `pressure: low/medium`).

## Why it's not the already-fixed bug

`context_lifecycle.py`'s own inline comment documents a similar-sounding, already-fixed issue
(`cefi_tardis_derivative_ticker_historical_gap_ao_context_pct_stuck_post_compact_2026_08_06`): a phase timestamp used to
advance even when `submit_to_pane` failed, permanently wedging the force state machine. That fix is confirmed working
live — slot 14 hit exactly this scenario today (91% pinned through a PRE_BOOT resume) and self-resolved at 10:35 once
the force fired. Slot 3's case is different: every submit reports `true` (the text really lands in the pane), so the
fix's own guard is satisfied — the problem is downstream of submission, in why the actual `/compact` isn't reducing the
measured pct once it runs. Possible causes not yet investigated: the pane's own readout is stuck (a display/parsing bug
in `worker_liveness.derive_context_used_pct` for this session specifically), the session is doing enough NEW work
between the `/pre-compact` skill's own commit/push/checkpoint activity and the subsequent `/compact` that it refills
faster than compaction can shrink it, or `/compact` itself is silently failing to run (erroring, or being intercepted by
something else in the pane) despite the text submitting cleanly.

## Why it matters

`compactions_total: 160` on one slot is a large number relative to the other sampled slots (54-93) — this pattern may
have been recurring for this slot over a longer period, not just today. A worker with no recycle escape and a compaction
that doesn't work has no self-healing path at all: it will keep re-triggering the same ineffective force cycle
indefinitely, burning tokens on repeated `/pre-compact` + `/compact` runs without ever actually freeing context, while
whatever task it's assigned continues to run in a context window that's permanently near-full.

## Todos

- [x] ✅ [SCRIPT] P2. Root-cause why slot 3's `/compact` submits cleanly but produces no measured pct drop — check
      whether the pane's context-percent readout itself is stuck/misparsing for this session
      (`worker_liveness.derive_context_used_pct`), or whether `/compact` is erroring silently, or whether new work
      between phases is refilling context faster than compaction frees it. Done when: a specific mechanism is identified
      with pane-log evidence, or a documented "inconclusive" verdict with what was ruled out. — **RESOLVED, checkbox was
      stale.** `ao_worker_context_saturation_unrecoverable_2026_08_06.md` (same live incident, filed independently the
      same day) identified the exact mechanism with pane-log evidence: the session had grown to ~971k message tokens,
      which with the 131,072-token completion reservation exceeds the model's 1,048,576 hard limit — every request
      including `/compact` itself 400s, because compaction must send the whole history to summarize it. Not a
      readout/parsing bug; a genuine hard-limit wedge.
- [x] ✅ [SCRIPT] P2. Add a Tier-2-style recycle escape for workers, gated the same way main/review's is
      (`pressure == "thrashing"` OR N forced-compacts in a window with no observed drop) — mirroring the existing
      checkpoint-write-then-exit pattern, respecting `one_task_per_session_enabled`'s normal fresh-session-per-task
      behavior. Done when: a unit test simulates N consecutive forced-compacts with no `context_compact_observed` drop
      for a `status=working` slot and asserts a recycle message is enqueued instead of yet another forced-compact
      attempt. — **RESOLVED, checkbox was stale, functionally equivalent mechanism shipped under a different name.**
      `agent-orchestrator@e608378`'s `_rearm_if_force_ineffective()` + `_recover_wedged_target()`
      (`server/context_lifecycle.py`): after `tuning.context_force_compact_wedge_after_failures` (default 3) consecutive
      ineffective forces with no observed drop, the target is classified terminally wedged and auto-recovered — kills
      the session, clears `claude_session_id` so the respawn takes the fresh-session branch instead of re-resuming the
      over-limit transcript. Gate condition matches this todo's own wording (N forced-compats with no observed drop);
      mechanism differs from the literal "recycle message enqueued" (it kills+respawns directly rather than messaging),
      but the functional intent — workers get an automatic escape instead of retrying forever — is met. Also extended to
      MAIN in the same session (`@33b3415`/`@6d791f6`), i.e. the doc's own "unlike main/review" framing no longer holds
      either way. Test: `tests/test_context_lifecycle.py::test_repeated_ineffective_forces_recover_the_wedged_session`.
- [x] ✅ [SCRIPT] P3. Check whether slot 3's current in-progress task (if any) is affected/stalled by running in a
      near-100%-context session this long — may need a manual intervention (reassign/kill+respawn) independent of the
      root-cause fix above, since that fix won't retroactively help the session already stuck. — **RESOLVED, checkbox
      was stale.** The companion doc's Progress Log records slot 3 was remediated in the SAME live incident via
      operator-approved `DELETE /api/slots/3` (killed the wedged tmux session, dropped the row so AutoSpawn respawned
      fresh with no stored session id).

## Progress Log

### 2026-08-06 — filed (interactive session, tab 1)

Discovered while investigating whether the FleetView dashboard's 100%-context rows were real or stale; confirmed real
via a read-only `state.db` query. Full diagnosis above.

### 2026-08-07 — na-eligibility-audit (tranche=ao, autonomous): found stale, archived

Cross-checking this doc against the live commit history (not just its own checkboxes) surfaced
`ao_worker_context_saturation_unrecoverable_2026_08_06.md` — a DIFFERENT session, filed the same day, diagnosing and
fixing the identical prod slot 3 incident (`compactions_total: 160`, same live evidence) under different framing
("unrecoverable one-shot latch" vs. this doc's "no recycle escape"). That doc's 7/7 todos shipped
(`agent-orchestrator@e608378`/`06a2865`/`33b3415`/`6d791f6`) and archived same-day; this doc never got the same
cross-reference and sat with its checkboxes stale-unflipped. Verified directly against `server/context_lifecycle.py`'s
live `_tick_worker`/`_rearm_if_force_ineffective`/`_recover_wedged_target` before archiving (not just trusting the
citation) — confirmed the recycle-escape mechanism genuinely exists now. All 3 todos closed with evidence above;
archived per issue-doc-lifecycle.md trigger 2. Two corpus referrers (`infra_satellite_ao_dispatch_batch8_2026_08_07.md`,
`ag_closeout_audit_infra_parked_2026_08_07.md` — both citing this doc's `asset_group` mistag as an open finding) updated
to the new archive path in the same commit; their mistag findings are now moot (an archived doc isn't in either audit's
candidate population) but left as historical record in those docs rather than edited, since correcting THEIR findings
content is outside this audit's scope.
