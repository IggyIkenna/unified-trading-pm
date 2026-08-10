---
doc_type: issue
title:
  AO dashboard shows 0% context for cicd1-shot / ag-closeout-auditor workers that are genuinely active — root- caused to
  a Claude Code spinner-variant gap in the pane-scraping fallback, not idleness
summary: >-
  Operator screenshot showed `cicd1-shot` agents (agt-152869, agt-834aca) and `ag-closeout-auditor` scheduled agents
  (agt-4203ad, agt-ce98fb) all reading "0%" in the dashboard's context column, despite being marked active 1min-1h ago,
  asking whether they're doing nothing or there's a display bug. Traced the actual mechanism in
  `agent-orchestrator/server/worker_liveness/__init__.py` (~line 500-570): `context_used_pct` is set from TWO sources —
  (1) the worker's own self-reported value via `/heartbeat`/`/boot`/`/done` POST bodies
  (`server/routes/slots_worker.py:252` `slot.context_used_pct = req.context_used_pct`), and (2) a server-side
  opportunistic fallback that scrapes the tmux pane's visible text for either an "X% until auto-compact" or "↑X.Xk
  tokens" marker — but ONLY when the pane's liveness classifier judges it as `"working"` (an active spinner line). The
  update itself is correctly monotonic-safe (`if derived_ctx_pct is not None and derived_ctx_pct >
  slot_row.context_used_pct: slot_row.context_used_pct = derived_ctx_pct` — never regresses a real reading to a scraped
  0), so the bug isn't a reset; it's that the value simply never gets a first real reading for these agent kinds.

  Live-verified via direct tmux pane capture (`tmux capture-pane -t orch-slot-2 -p -S -40`, SSM against
  `i-0c9b283b31d6b5ca7`) on `agt-834aca` (deployment-api, ldr_qg_failure, confirmed genuinely dispatched and working):
  the pane showed repeated `✻ Brewed for Ns · N monitors still running` / `✻ Crunched for Ns · N monitors still running`
  spinner lines — a DIFFERENT spinner subtitle variant than the normal tool-call-completion spinner, shown while the
  agent is waiting on background `Monitor` tool tasks (exactly the pattern this session itself used repeatedly for
  CI/build polling). This variant does not print a token-count readout anywhere in the visible pane, so neither
  `_AUTO_COMPACT_RE` nor `_TOKEN_USAGE_RE` ever matches, and `context_used_pct` never advances past its ORM default of 0
  (`nullable=False, default=0` — no way to currently distinguish "never sampled" from "genuinely near-zero" in the
  schema). `cicd1-shot`/escalation workers and scheduled auditors are exactly the agent kinds most likely to lean on
  `Monitor` for long CI/build waits, so they're disproportionately exposed to this gap versus a persistent
  conversational worker whose pane more often shows the normal tool-call spinner.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dashboard, context-tracking, worker-liveness, monitor-tool, ui, display-bug]
related:
  [
    /plans/archive/issues/context_compact_directive_did_not_fire_slot_rode_to_96pct_2026_07_27.md,
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
  ]
created: 2026-07-29
author: unknown
last_updated: 2026-07-29
priority: P2
parent_epic: orchestrator_master
source:
  "operator dashboard screenshot + direct ask, investigated live via SSM tmux capture-pane on orch-slot-2 (agt-834aca),
  2026-07-29 ~09:20 UTC"
execution_scope: local-only
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/06-coding-standards/ui-testing-layers.md,
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
    agent-orchestrator/server/worker_liveness/__init__.py,
    agent-orchestrator/server/orm.py,
    agent-orchestrator/dashboard/src,
  ]
---

# AO context-% shows 0% for Monitor-heavy one-shot/scheduled workers — a sampling gap, not idleness

## Evidence

- Code: `server/worker_liveness/__init__.py` ~500-570 — context scrape only runs inside the
  `classification == "working"` branch, matching `_AUTO_COMPACT_RE = r"(\d+)\s*%\s*until\s+auto-compact"` or
  `_TOKEN_USAGE_RE = r"[↑↓]\s*([\d.]+)\s*k\s+tokens"` against a 500-line-scrollback capture.
- Live pane capture, `agt-834aca` / `orch-slot-2` (confirmed genuinely dispatched, working on deployment-api's
  `ldr_qg_failure`):
  ```
  ✻ Brewed for 6s · 2 monitors still running
  ❯ send a /heartbeat now and continue your in-flight task
    Ran 2 shell commands
  ● Still running normally, no change. Continuing to wait for the Monitor's terminal notification.
  ✻ Crunched for 5s · 2 monitors still running
  ─────────────────────────────────────────────
  ❯
  ─────────────────────────────────────────────
    ⏵⏵ bypass permissions on · 2 monitors · ← for agents · ↓ to manage
  ```
  No `% until auto-compact` or `↑X.Xk tokens` text anywhere in the last 40 lines despite the worker being demonstrably
  active and mid-task.
- `server/orm.py:95` (SlotRow) / `:385` (AgentRow):
  `context_used_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)` — no NULL/never-sampled sentinel
  available in the current schema.

## Why not fixed inline this pass

A real fix needs either (a) a schema change to distinguish never-sampled from measured-near-zero (an Alembic-style
migration touching a live production DB — bigger, riskier lift than this investigation's remaining budget), or (b) a
dashboard-only display change (render "—"/"not sampled" instead of "0%" when never updated). Option (b) is a
`dashboard/src/` TypeScript change, and this workspace's own hard rule
(`/codex/06-coding-standards/ui-testing-layers.md`) requires a cited Playwright L2 regression spec before any UI tick
counts as done — not something to rush through without that coverage just to close this out same-session. Filing
properly-scoped rather than shipping an under-tested UI patch.

## Todos

- [ ] [UI] P2. Dashboard: when `context_used_pct == 0` AND the row has never had a `derived_ctx_pct` scrape succeed
      (needs a way to detect this — see DATA todo below), render "—" instead of "0%" for one-shot/ scheduled agent kinds
      specifically, with a `pw:L2` regression spec covering both the "genuinely fresh, real 0%" and "never sampled"
      cases so they don't get conflated.
- [ ] [DATA] P3. Decide the cheapest way to represent "never sampled": either (a) a schema migration adding a nullable
      `context_used_pct_sampled_at: datetime | None` column, or (b) reuse an existing signal (e.g. `last_ping` age vs
      `context_used_pct == 0`) as a heuristic without a schema change. Prefer (b) if it proves reliable enough —
      smaller, safer, no migration risk.
- [ ] [BACKEND] P3. Consider widening the pane-scrape to also recognize a "N monitors still running" spinner variant's
      OWN status text (if Claude Code CLI ever adds a token/context readout there in a future version) — not actionable
      today since the variant currently renders no such marker at all, but worth a follow-up check if the CLI's UI
      changes.

## Triage note

Not a functional bug in the sense of lost work or incorrect state — `cicd1-shot`/`ag-closeout-auditor` workers observed
this session (and independently, throughout the earlier CI-cost-reduction work) are genuinely doing real work while
reading 0%. This is purely a monitoring/display accuracy gap, but a real one worth closing since it actively misleads an
operator glancing at the dashboard into suspecting stuck/idle workers that are not stuck.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — not dispatchable as one unit: the `[UI] P2` explicitly depends
  on the `[DATA] P3`'s representation decision ('needs a way to detect this — see DATA todo below'), and a plan's
  independent same-priority todos run CONCURRENTLY by default, so flipping would dispatch the dependant and its
  prerequisite in parallel — partial-parallelism is not expressible in one doc (CLAUDE.md § Plans). The `[BACKEND] P3`
  is additionally declared 'not actionable today' pending an upstream Claude Code CLI change.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified (5 entries, unchanged; prior marker undercounted) — all still resolve and
  cover both the `[UI]`/`[DATA]` todo pair (dashboard + orm.py) and the `[BACKEND]` follow-up
  (worker_liveness/**init**.py).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — Prior verdict re-verified — content unchanged since the
  2026-08-06 marker. `[UI] P2`/`[DATA] P3` pair remains non-parallelizable (dependent todos, cannot flip as one unit);
  `[BACKEND] P3` remains not-actionable pending an upstream Claude Code CLI change.
- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — checked the split-into-Plan-A/Plan-B-via-
  depends_on+gate_on_depends pattern (now well-established elsewhere in this tranche, e.g. batch16/finalize) against
  this doc specifically: the `[DATA] P3` prerequisite item itself is not yet bounded (it only says "prefer (b) IF it
  proves reliable enough" — an open reliability question, not a resolved preference like batch16's source item), so
  splitting into a gated pair would still leave an undetermined-outcome todo in Plan A. Stays whole-doc NA. Other
  round7-10 precedents (credentials, delete-safety, IAM) do not apply. Corroborated same-day: `/ag-closeout-audit ao`
  batch12 lists this doc operator-gated (22), "also human/upstream-CLI-gated."

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read of all 3 open
  items. `[UI] P2` depends on `[DATA] P3`'s unresolved 'prefer (b) if it proves reliable enough' open reliability
  question (not a resolved preference); `[BACKEND] P3` stays blocked on an upstream Claude Code CLI change. round11
  (2026-08-09) already specifically considered and rejected the gated-pair-split pattern for this doc since the DATA
  prerequisite isn't itself resolved. No new facts found this pass.
