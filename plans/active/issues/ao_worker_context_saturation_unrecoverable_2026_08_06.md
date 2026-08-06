---
doc_type: issue
title:
  "An AO worker can reach 100% context and become PERMANENTLY unrecoverable: client-side auto-compact is disabled
  fleet-wide by a PreCompact hook, the backend force-compact is a one-shot latch that never re-arms after a FAILED
  compaction, and heartbeat-silence recovery then resumes the same over-limit transcript forever"
summary: >-
  Live on prod slot 3 (2026-08-06, deepseek-v4-flash account, 160 lifetime compactions): the session grew to ~971k
  message tokens, which with the 131,072-token completion reservation exceeds the model's 1,048,576 hard limit, so EVERY
  request 400s — including `/compact` itself, because compaction must send the whole history to summarize it. The slot
  was therefore pinned at `context_used_pct=100` with `context_pressure=thrashing` and could emit no heartbeat (ping
  went stale ~1h), while the watchdog respawned it at 12:41:15Z with `claude --resume <same-session>` (`last_msg`
  literally reads "↻ resumed after heartbeat-silence (context intact)") — reloading the same oversized transcript and
  re-wedging instantly. Three independent defects compose into "unrecoverable", and each one alone would have been
  survivable. (1) The client-side auto-compact safety net — the thing that should have fired around ~92% long before the
  hard limit — is UNCONDITIONALLY DISABLED fleet-wide by
  `unified-trading-pm/cursor-configs/hooks/precompact-block-auto.sh`, a `PreCompact` hook with `matcher: "auto"` that
  `exit 2`s on every `compaction_reason == "auto"`; `context_lifecycle.py`'s own module docstring still asserts
  "Client-side auto-compact stays underneath as the final safety net", which is FALSE in the shipped config. (2) The
  backend replacement (`_tick_worker`, force at `context_worker_force_compact_pct`=60) is gated on `state.forced_at is
  not None`, a latch re-armed only by an OBSERVED compaction i.e. a `context_used_pct` DROP — so a compaction that is
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
status: open
nature: issue
asset_group: [ao]
scope: [engineer]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
tags: [agent-orchestrator, context-lifecycle, auto-compact, watchdog, worker-liveness, self-healing, operator-reported]
related:
  [
    /plans/active/issues/ao_blocked_question_not_retired_when_condition_resolves_2026_08_06.md,
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

# AO worker context saturation is unrecoverable (auto-compact disabled + non-re-arming force latch + resume loop)

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

- [ ] [INFRA] P1. **Rule on `precompact-block-auto.sh` — the fleet-wide auto-compact kill.** The hook
      (`unified-trading-pm/cursor-configs/hooks/precompact-block-auto.sh`, wired as a `PreCompact` hook with
      `matcher: "auto"` in `cursor-configs/settings.json`) unconditionally `exit 2`s every automatic compaction, so the
      CLI's own last-resort safety net never runs for ANY worker. Decide + implement one of: (a) keep the block but make
      it conditional — allow auto-compact above a hard ceiling (e.g. ≥85%) where losing an uncheckpointed turn is
      strictly better than wedging the session; (b) drop the block now that the backend force path exists; (c) keep it
      as-is and accept that the backend path is the ONLY net, in which case todos 2-4 become mandatory, not optional.
      Whatever is chosen, fix `server/context_lifecycle.py`'s module docstring, which currently claims "Client-side
      auto-compact stays underneath as the final safety net" — that statement is false today.

- [ ] [INFRA] P1. **Re-arm the worker force-compact latch on a FAILED compaction, not only on an observed drop.**
      `_tick_worker` (`server/context_lifecycle.py`) early-returns while `state.forced_at is not None`, and the caller
      only clears it when a compaction is OBSERVED (a `context_used_pct` drop). A compaction that is verifiably
      submitted but then fails at the API layer leaves the latch set forever, which is precisely the state that needs
      another attempt. Add an outcome check: if pct has not dropped within N ticks of a force, clear `forced_at` and
      escalate rather than latching. Cite the sibling fix
      `cefi_tardis_derivative_ticker_historical_gap_ao_context_pct_stuck_post_compact_2026_08_06` — it fixed the
      delivery half of this same latch; this is the outcome half.

- [ ] [INFRA] P1. **Never `--resume` a transcript that is known to be at/over the model's context limit.** Both resume
      paths in `server/worker_liveness_watchdog.py` (usage-cap ~line 1794, heartbeat-silence ~line 2109) pass
      `resume_session_id=stored_sid` unconditionally when one exists. Gate them: if the slot's last known
      `context_used_pct` is ≥ a saturation threshold, OR the pane shows a `maximum context length` 400, take the
      existing `not stored_sid → fresh respawn` branch instead. Recovery that restores the exact state that caused the
      failure is not recovery — and the `last_msg` it writes, "resumed after heartbeat-silence (context intact)",
      advertises the defect as a feature.

- [ ] [INFRA] P2. **Persist `_heartbeat_resume_count` across orchestrator restarts.** It is an in-memory dict on the
      watchdog instance, so `_HEARTBEAT_RESUME_MAX` (`tuning.watchdog_heartbeat_resume_max`) is silently reset by any
      restart — slot 3's budget was zeroed by the 12:45:22Z restart four minutes after its resume. Move it to the slot
      row / state DB so the bound survives, otherwise the "bounded" resume loop is unbounded in practice.

- [ ] [INFRA] P2. **Detect the terminal-wedge signature explicitly and auto-recover + alert.** A pane matching
      `maximum context length is \d+ tokens` after a forced `/compact` is a MEASURED terminal state, not a transient
      one: it cannot self-heal, every subsequent retry is wasted, and no heartbeat will ever arrive. Classify it, force
      a FRESH session (not a resume), and page it per `/codex/04-architecture/agent-orchestrator-alerting.md` (this is a
      failure, so it pages; the automatic recovery itself logs + digests, never pages).

- [ ] [INFRA] P3. **Stop rendering a stale `context_pressure`/`context_used_pct` as if it were current.** Both fields
      freeze at their last heartbeat value, so a wedged or silent slot shows a confidently wrong band (slot 3:
      `thrashing` with `compactions_last_hour=0`, which the live formula would score `high`). Either recompute the band
      on read from the current `compactions_last_hour`, or mark the reading stale in `/api/state` (e.g. alongside the
      existing `worker_alive` chip) so the dashboard can grey it out rather than assert it.

## Progress Log

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
