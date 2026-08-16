---
doc_type: issue
title:
  "An AO worker can reach 100% context and become PERMANENTLY unrecoverable: the backend force-compact is a one-shot
  latch that never re-arms after a FAILED compaction, and heartbeat-silence recovery then resumes the same over-limit
  transcript forever (the third leg — client-side auto-compact disabled fleet-wide by a PreCompact hook — is FIXED as of
  2026-08-06)"
summary: >-
  Live on prod slot 3 (2026-08-06, deepseek-v4-flash account, 160 lifetime compactions): the session grew to ~971k
  message tokens, which with the 131,072-token completion reservation exceeds the model's 1,048,576 hard limit, so EVERY
  request 400s — including `/compact` itself, because compaction must send the whole history to summarize it. The slot
  was therefore pinned at `context_used_pct=100` with `context_pressure=thrashing` and could emit no heartbeat (ping
  went stale ~1h), while the watchdog respawned it at 12:41:15Z with `claude --resume <same-session>` (`last_msg`
  literally reads "↻ resumed after heartbeat-silence (context intact)") — reloading the same oversized transcript and
  re-wedging instantly. Three independent defects compose into "unrecoverable", and each one alone would have been
  survivable. (1) **[FIXED 2026-08-06 — operator ruling, see todo 1]** The client-side auto-compact safety net — the
  thing that should have fired around ~92% long before the hard limit — was UNCONDITIONALLY DISABLED fleet-wide by
  `unified-trading-pm/cursor-configs/hooks/precompact-block-auto.sh`, a `PreCompact` hook with `matcher: "auto"` that
  `exit 2`'d on every `compaction_reason == "auto"`. That hook is now deleted and its registration removed, so
  `context_lifecycle.py`'s docstring claim "Client-side auto-compact stays underneath as the final safety net" is true
  again; legs (2) and (3) below remain OPEN, so a wedge is still reachable if the net is ever bypassed. (2) The backend
  replacement (`_tick_worker`, force at `context_worker_force_compact_pct`=60) is gated on `state.forced_at is not
  None`, a latch re-armed only by an OBSERVED compaction i.e. a `context_used_pct` DROP — so a compaction that is
  submitted-but-fails (exactly this case: the `forced_compact` activity event at 12:46:30Z records `pct: 100, submitted:
  true`, and the compact then 400'd) latches the slot out of every future force attempt. The 2026-08-06
  `..._ao_context_pct_stuck_post_compact` fix hardened the DELIVERY half (only advance the timestamp when
  `submit_to_pane` verifies the text left the box) but not the OUTCOME half — a verified-submitted compaction that fails
  at the API layer still burns the latch. (3) `_HEARTBEAT_RESUME_MAX` does bound the resume loop, but the counter
  `self._heartbeat_resume_count` is IN-MEMORY, so an orchestrator restart (one happened at 12:45:22Z, four minutes after
  slot 3's resume) resets the budget to zero and the resume loop can run forever across restarts. Cost signal for the
  wedged stretch: 76.4M cache-read + 741k output tokens on a session that can no longer complete a single call.
  Remediated in-session by DELETE /api/slots/3 (kills the wedged tmux + drops the row so AutoSpawn takes the code's own
  `not stored_sid → fresh respawn` branch); that is a manual operator action, not a fix.
status: resolved
nature: issue
asset_group: [ao]
scope: [engineer]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
tags: [agent-orchestrator, context-lifecycle, auto-compact, watchdog, worker-liveness, self-healing, operator-reported]
related:
  [
    /plans/archive/issues/ao_blocked_question_not_retired_when_condition_resolves_2026_08_06.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-08-06
author: agent
last_updated: 2026-08-06
priority: P1
parent_epic: orchestrator_master
source:
  "operator-reported, interactive session (slot 2 host `hk`) — operator observed slot 3 in the Fleet tab sitting at 100%
  context with a blank context bar and a 1h-old ping, and asked both what was wrong and specifically whether
  auto-compact is disabled on AO workers. It is. Diagnosed read-only via AWS SSM against the prod planning VM."
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. 7/7 todos shipped (agent-orchestrator@e608378/06a2865/33b3415/6d791f6,
> unified-trading-pm@3dfe85837) and the Progress Log states 'This issue is COMPLETE... verified against live state
> rather than only unit-tested'; deferred loose findings are tracked in named sibling issue docs. Moved by the
> 2026-08-06 AO issue-doc archive sweep.

# AO worker context saturation is unrecoverable (non-re-arming force latch + resume loop; auto-compact leg FIXED)

## Evidence

Prod slot 3 tmux pane, captured 2026-08-06 (`sudo -u ubuntu tmux capture-pane -t orch-slot-3 -S -60`):

```
● API Error: 400 This model's maximum context length is 1048576 tokens.
  However, you requested 1102249 tokens (971177 in the messages, 131072 in the completion).
❯ /pre-compact
● API Error: 400 ... 1103465 tokens (972393 in the messages, 131072 in the completion) ...
❯ /compact
  ⎿ Error during compaction: API Error: 400 This model's maximum context length is 1048576 tokens...
                                                          100% context used
```

`GET /api/state` for the same slot: `status=working`, `context_used_pct=100`, `context_pressure=thrashing`,
`compactions_last_hour=0`, `compactions_total=160`, `last_spawned_at=12:41:14Z`, `worker_alive=false`,
`tmux_alive=true`, `current_task=null`.

Note the secondary reporting artefact: `context_pressure` is only recomputed when a heartbeat carrying
`context_used_pct` arrives (`state_store/slots.py` `derive_context_pressure` at the record site). A silent worker
therefore keeps whatever band it last had — slot 3 reads `thrashing` while `compactions_last_hour=0`, which by the live
formula would be `high`. The displayed band is a stale snapshot, not current state.

## Todos

- [x] ✅ [INFRA] P1. **Rule on `precompact-block-auto.sh` — the fleet-wide auto-compact kill.** RULED by the operator
      2026-08-06: option (b) — **auto-compact must be re-enabled; the block is gone.** Rationale (operator): the
      `/pre-compact` skill exists to make agents write context-only findings into their plan/issue docs, so a subsequent
      compact loses nothing durable — and if `/pre-compact`+`/compact` are for any reason not delivered, auto-compact is
      what prevents this thrashing class and caps the token spend. Shipped: `PreCompact` registration removed from
      `cursor-configs/settings.json` (hooks key now `PreToolUse` + `UserPromptSubmit` only) and
      `cursor-configs/hooks/precompact-block-auto.sh` DELETED (no shim). Durable rule recorded in
      `/codex/05-infrastructure/claude-code-settings-symlink.md` § "`PreCompact` stays UNREGISTERED". Stale local
      re-registrations are swept by `scripts/workspace/link-claude-skills.sh` step (4.5), whose `del(.["PreCompact"])`
      now serves that purpose explicitly. `server/context_lifecycle.py`'s docstring claim ("Client-side auto-compact
      stays underneath as the final safety net") needed no edit — it is TRUE again as of this change. —
      unified-trading-pm@3dfe85837, verified: `settings.json` parses and its `hooks` keys are exactly
      `['PreToolUse', 'UserPromptSubmit']`; `cursor-configs/hooks/` now contains only `context-threshold-nudge.sh`.
      Rollout note: hooks are read at SESSION START, so sessions already running keep the old registration — but that is
      fail-safe here, because the deleted script makes the stale hook exit 127, a NON-blocking hook error (only exit 2
      blocks), so auto-compact proceeds on those sessions too rather than staying blocked until respawn.

- [x] ✅ [INFRA] P1. **Re-arm the worker force-compact latch on a FAILED compaction, not only on an observed drop.**
      `_tick_worker` (`server/context_lifecycle.py`) early-returns while `state.forced_at is not None`, and the caller
      only clears it when a compaction is OBSERVED (a `context_used_pct` drop). A compaction that is verifiably
      submitted but then fails at the API layer leaves the latch set forever, which is precisely the state that needs
      another attempt. Add an outcome check: if pct has not dropped within N ticks of a force, clear `forced_at` and
      escalate rather than latching. Cite the sibling fix
      `cefi_tardis_derivative_ticker_historical_gap_ao_context_pct_stuck_post_compact_2026_08_06` — it fixed the
      delivery half of this same latch; this is the outcome half. **SHIPPED** — agent-orchestrator@e608378. New
      `_rearm_if_force_ineffective()` in `server/context_lifecycle.py`: `_TargetState` gained `forced_pct` (context%
      when `/compact` was accepted) + `ineffective_forces`; past `tuning.context_force_compact_retry_after_seconds`
      (new, default 300s) with no drop, the latch is cleared and the next tick forces again. An OBSERVED compaction
      resets the counter. Tests: `tests/test_context_lifecycle.py::test_ineffective_force_rearms_after_retry_window`,
      `…::test_ineffective_force_does_not_rearm_inside_grace_window` (no double-inject inside the window),
      `…::test_observed_compaction_resets_ineffective_counter`. Negative-controlled: with the knob set to 0 (old latched
      behaviour) 3 of these fail.

- [x] ✅ [INFRA] P1. **Never `--resume` a transcript that is known to be at/over the model's context limit.** Both
      resume paths in `server/worker_liveness_watchdog.py` (usage-cap ~line 1794, heartbeat-silence ~line 2109) pass
      `resume_session_id=stored_sid` unconditionally when one exists. Gate them: if the slot's last known
      `context_used_pct` is ≥ a saturation threshold, OR the pane shows a `maximum context length` 400, take the
      existing `not stored_sid → fresh respawn` branch instead. Recovery that restores the exact state that caused the
      failure is not recovery — and the `last_msg` it writes, "resumed after heartbeat-silence (context intact)",
      advertises the defect as a feature. **SHIPPED** — agent-orchestrator@e608378. Root cause was narrower than first
      written and is now recorded accurately: the gate already existed (`resume_lifecycle.classify_dead_worker`'s
      `resume_fresh_context_pct` check, added 2026-07-14 for the earlier slot-2 loop) — the two watchdog paths simply
      BYPASSED it. Both now consult the SAME knob (no second threshold invented) and fall through to the fresh-respawn
      branch, logging `slot_resume_skipped`. Tests:
      `tests/test_self_healing_hardening.py::test_heartbeat_silent_at_saturated_context_refuses_resume` and
      `…::test_heartbeat_silent_below_threshold_still_resumes` (proves normal context-preserving recovery is intact).

- [x] ✅ [INFRA] P2. **Persist `_heartbeat_resume_count` across orchestrator restarts.** It is an in-memory dict on the
      watchdog instance, so `_HEARTBEAT_RESUME_MAX` (`tuning.watchdog_heartbeat_resume_max`) is silently reset by any
      restart — slot 3's budget was zeroed by the 12:45:22Z restart four minutes after its resume. Move it to the slot
      row / state DB so the bound survives, otherwise the "bounded" resume loop is unbounded in practice. **SHIPPED** —
      agent-orchestrator@e608378. Persisted via the existing `dedup_state` int-map store (new
      `heartbeat_resume_count_path()`) rather than an ORM migration — same durable-state mechanism the alert throttles
      already use. Seeded in `__init__`, flushed on every mutation through `_persist_heartbeat_resumes` /
      `_clear_heartbeat_resumes`. Test: `…::test_heartbeat_resume_count_survives_restart` — a second watchdog instance
      (== a restart) still sees the spent budget and fresh-respawns instead of resuming.

- [x] ✅ [INFRA] P2. **Detect the terminal-wedge signature explicitly and auto-recover + alert.** A pane matching
      `maximum context length is \d+ tokens` after a forced `/compact` is a MEASURED terminal state, not a transient
      one: it cannot self-heal, every subsequent retry is wasted, and no heartbeat will ever arrive. Classify it, force
      a FRESH session (not a resume), and page it per `/codex/04-architecture/agent-orchestrator-alerting.md` (this is a
      failure, so it pages; the automatic recovery itself logs + digests, never pages). **SHIPPED** —
      agent-orchestrator@e608378, with one deliberate deviation from this todo's own wording: it does NOT page.
      Detection is by OUTCOME rather than by pane-scraping for `maximum context length` — after
      `tuning.context_force_compact_wedge_after_failures` (new, default 3) consecutive ineffective forces the target is
      terminally wedged, which is measured, cheaper, and does not depend on CLI error wording that changes between
      versions. `_recover_wedged_target()` kills the session, clears `claude_session_id` (the load-bearing half —
      without it every respawn path finds a stored id and re-resumes the over-limit transcript) and sets `status=killed`
      so AutoSpawn respawns FRESH. Routed to `notify_agent_stuck_respawned`, which logs + feeds the daily digest and
      does NOT page: per `/codex/04-architecture/agent-orchestrator-alerting.md` an automatic recovery never pages; only
      the cannot-recover escalation path does. Test: `…::test_repeated_ineffective_forces_recover_the_wedged_session`
      asserts the kill, the cleared session id and the notify.

- [x] ✅ [INFRA] P3. **Stop rendering a stale `context_pressure`/`context_used_pct` as if it were current.** Both fields
      freeze at their last heartbeat value, so a wedged or silent slot shows a confidently wrong band (slot 3:
      `thrashing` with `compactions_last_hour=0`, which the live formula would score `high`). Either recompute the band
      on read from the current `compactions_last_hour`, or mark the reading stale in `/api/state` (e.g. alongside the
      existing `worker_alive` chip) so the dashboard can grey it out rather than assert it. **SHIPPED —
      agent-orchestrator@06a2865.** Took the mark-it-stale option (not recompute-on-read): a recomputed band would still
      be built from stale inputs, so it would be a different confident lie rather than an honest "we don't know".
      `/api/state` gains `SlotView.context_reading_stale`, set when there is no recent heartbeat AND
      `context_used_pct > 0` — the `pct > 0` half matters, otherwise every idle slot at 0% would be flagged for a
      reading nobody could be misled by. The dashboard dims the fill + number and dashes the bar outline, with a
      `— STALE: last known, no recent heartbeat` tooltip and a `?` marker. Tests:
      `tests/test_context_lifecycle.py::test_context_reading_stale_flags_a_silent_slot` (asserts the exact prod slot-3
      shape flags, and an idle 0% slot does NOT), `…::test_context_reading_not_stale_for_a_live_worker`, plus playwright
      `dashboard/tests/e2e/context-pressure-bar.spec.ts` "a stale cell visibly de-emphasises the fill and number" —
      **pw:L2 ✓** (3 specs green in that file).

- [x] ✅ [INFRA] P1. **Extend the same saturation protection to the MAIN agent.** Filed + closed 2026-08-06 after the
      operator asked what was actually left: the original five fixes covered WORKER slots only, and main — which has no
      `SlotRow`, so none of the slot-based recovery reaches it — still had the exact bug. `main_agent_keeper.py`'s two
      failover paths (rate-limit ~L385, auth-failed ~L558) passed `resume_session_id=stored_sid` unconditionally, and
      `context_lifecycle._recover_wedged_target()` deliberately bailed for `slot_id is None`, logging an error and
      recovering nothing. This mattered more than its position in the list suggests: main is designed to run for DAYS
      (`context_lifecycle`'s own docstring), so it is the session most likely to reach the hard limit — the live one has
      been up since 2026-08-04. **SHIPPED — agent-orchestrator@33b3415 + @6d791f6.** (1) Both keeper paths now null the
      resume target when saturated, so the EXISTING "no stored_sid → fresh respawn" branch fires unchanged (one decision
      point, no new branch); logged as `main_agent_resume_skipped_context_saturated`. (2) A wedged main is now genuinely
      recovered: kill the session + clear its `AgentRow.claude_session_id` so AgentKeeper's respawn cannot reload the
      over-limit transcript. **A pane-only gate would have silently no-opped** — caught by verifying against the real
      session rather than trusting the first implementation: main's PANE parse returned `None` (its context readout had
      scrolled out of the captured window) while its `AgentRow` read a perfectly good 44%. @6d791f6 reads the durable
      row FIRST and falls back to the pane, because a gate that cannot fire is worse than no gate — it looks fixed.
      Verified live post-deploy: row reads 44%, gate returns "resumable" (44 < `resume_fresh_context_pct` 80), i.e. it
      is now measuring instead of blind. 5 tests:
      `tests/test_context_lifecycle.py::test_main_saturation_gate_prefers_the_durable_agentrow_reading`,
      `…::test_main_saturation_gate_drops_the_resume_target`, `…::test_main_saturation_gate_allows_a_resumable_session`,
      `…::test_main_saturation_gate_is_none_on_an_unreadable_pane` (fail-open on a bad measurement),
      `…::test_wedged_main_is_recovered_not_just_logged`.

## Lessons / traps (re-learned at cost — 2026-08-06 session)

- **A guard that cannot fire looks fixed, which is worse than no guard.** The first MAIN saturation gate (@33b3415) read
  main's context% from its tmux pane. Verified against the LIVE session, that parse returned `None` (the readout had
  scrolled out of the captured window) while main's `AgentRow` held a perfectly good 44% — so the gate would have
  silently no-opped on the exact session it exists to protect. @6d791f6 reads the durable row first. The general rule:
  **verify a guard against live state, not only against unit tests you wrote to pass.**
- **Writing ABOUT a lint/CI directive in a comment triggers the directive.** Removing a malformed suppression from
  `slack.py`, the replacement comment explained what had been removed — and quoted the directive's literal spelling, so
  ruff parsed the explanation as two more directives and the warning count went 1 → 2. Identical class to CLAUDE.md's
  rule that the CI-skip marker fires from a commit BODY that merely describes it. Describe such markers in prose, never
  verbatim.
- **A feature can look dead because something else already did its job.** The staleness re-remind's first manual sweep
  returned `stale_reminded=0` across 27 questions, 24 of them >8h old — which reads exactly like a broken feature. The
  periodic sweep had fired seconds earlier and the cooldown correctly deduped. **Check the logs before concluding a
  no-op**: `journalctl -u orchestrator | grep 'standing unanswered'` showed 23 successful re-reminds.
- **`worker_liveness_watchdog` does `del _CFG` (module scope) after deriving its constants.** Referencing `_CFG` inside
  a function raises `NameError` at runtime — use `get_config()` there. Cost: a broken edit that also failed two
  PRE-EXISTING tests, which is what caught it.
- **Slack rejects the ENTIRE post when any section exceeds 3000 chars** — it does not truncate. One 4,654-char question
  meant that row never paged at all, silently, including its original alert.
- **Rejected: recomputing the context-pressure band on read** (todo 6's other option). A band recomputed from a stale
  `compactions_last_hour` is still built from stale inputs — a different confident lie rather than an honest "unknown".
  Marking the reading stale was chosen instead.
- **Corrections to claims made earlier in this same session**, recorded so the wrong version does not survive: (1)
  `POST /api/slots/{id}/bootstrap` provisions WORKTREES, not sessions — it would not have rebooted slot 3;
  `DELETE /api/slots/{id}` was the correct lever. (2) The external-PR predicate was initially parked pending an operator
  ruling on "whether the orchestrator may make outbound network calls" — a false premise the operator challenged: it
  already shells to `gh` from `gh_rate_monitor`, `ci_status`, `ci_reconcile` and `escalation`, and monitors its own
  rate-limit pools. (3) The blocked queue was hypothesised to be full of moot questions; measured `retired=0` of 27 —
  the real problem was week-old questions being invisible, not moot.

## Deferred work after 2026-08-06

Both issues from this session are CLOSED (7/7 and 6/6). These are the loose findings it surfaced, now tracked where each
class already lives rather than duplicated into new docs:

| Item                                                                                                                       | Kind               | Blocked on                                                                                                                                                   |
| -------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Re-mint `~/.orch_token` on operator host `hk` (expired 2026-08-05; that host's Fleet git-status has been 401-silent since) | **Operator-owned** | Operator minting a dashboard JWT — tracked in `/plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md`                         |
| `main-backmerge-to-ldr` hanging fleet-wide (UAC runs cancelled at 1h9m / 4h41m, one pending 48m)                           | **Not done**       | Nobody — needs CI investigation; tracked in `/plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md`                  |
| Dashboard prettier 3.6.2 vs wrapper pin 3.9.5 disagree on formatting                                                       | **Not done**       | Nobody, but needs a judgment call (3.9.5 has a known proseWrap defect) — `/plans/active/issues/dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md` |
| Duplicate-finalize-plan root cause (idempotency guard + corpus detector)                                                   | **Done 2026-08-16** | `/plans/archive/2026_08/issues/duplicate_finalize_plans_created_for_one_parent_2026_08_06.md` (3/3 todos, unified-trading-pm@7247bb6a69)                    |

**Recommended NEXT: the `~/.orch_token` re-mint.** It is a one-minute operator action that restores fleet observability
for a whole host, and it is currently _silent_ — the Fleet tab shows stale git state rather than an error, which is the
same class of invisible-wrongness this session's issue was about. Then the backmerge hang: it deadlocks promotions
across repos, so it blocks more work than its P2 suggests.

## Progress Log

### 2026-08-06 (later) — MAIN-agent coverage closed; issue fully resolved

Operator asked what was actually remaining on the context front. Answer at that point: one real gap, and it was mine —
the fixes were worker-scoped, leaving the main agent exposed to the identical resume-a-saturated-transcript bug. Closed
it (todo 7 above), which took two commits because the first implementation was measurably blind: verifying the gate
against the live main session showed the pane parse returning None where the durable `AgentRow` had 44%.

**Coverage now, stated plainly:** worker slots (SlotRow-reported pct), review slots (slot-bound, same path), and main
(AgentRow-reported pct, pane fallback) all refuse a saturated `--resume` and all have a wedge-recovery path that clears
the resume target before respawn. Client-side auto-compact is re-enabled underneath all three as the final net —
verified clean across all 16 slot clones, not just the main workspace root.

**This issue is COMPLETE.** 7/7 todos, every one shipped, deployed to the orchestrator VM and verified against live
state rather than only unit-tested.

### 2026-08-06 — filed (interactive session, slot 2 host `hk`)

Operator observed slot 3 at 100% context with a blank bar and a stale ping and asked whether auto-compact is disabled on
AO workers. Answer: yes, fleet-wide, deliberately, via the `PreCompact` `matcher: "auto"` hook. Full diagnosis above.
Slot 3 itself was remediated during the session with `DELETE /api/slots/3` (operator-approved) — the wedged tmux session
was killed and the row dropped so AutoSpawn respawns with no stored session id, i.e. genuinely fresh. That is a manual
workaround; every todo above remains open.

The separate cosmetic half of the operator's report — the context bar rendering EMPTY at 100% because
`.ctx-fill.thrashing` had no CSS rule at all — was fixed in the same session (agent-orchestrator
`dashboard/src/styles.css`, regression spec `dashboard/tests/e2e/context-pressure-bar.spec.ts`) and is NOT part of this
issue.
