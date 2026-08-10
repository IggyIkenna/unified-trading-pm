---
doc_type: issue
title:
  AO dashboard shows 0% context for cicd1-shot / ag-closeout-auditor workers that are genuinely active — root- caused to
  a Claude Code spinner-variant gap in the pane-scraping fallback, not idleness
summary: >-
  RE-ROOT-CAUSED 2026-08-10 (the 2026-07-29 pane-scraping mechanism below is SUPERSEDED by the transcript probe,
  agent-orchestrator@c6e6d98). The dashboard's 0% context column is TWO defects rendering identically: (A) the
  register/poll roles never populate `AgentRow.context_used_pct` at all — measured over the whole live corpus, `custom`
  0/151 non-zero and `plan_reconciler` 0/21, all time — because only slot workers post it via `/heartbeat`; and (B) a
  same-day regression (agent-orchestrator@bef2f6b deleted `main_pct`, the only writer of main's AgentRow pct, then
  repointed `_sync_main_slot_row` at that now-never-written field) which clobbers main's `SlotRow(0)` to 0 every keeper
  tick, fighting `_read_pct`'s probe ratchet and manufacturing phantom compactions — live proof, `compactions` row 2811
  logs main "compacting" 39->0 sixty seconds before the REAL 39->5 event, inflating `compactions_total` until
  `derive_context_pressure` returned "thrashing" and fired a premature recycle (main recycled 4x in 5h). Both BACKEND
  fixes shipped 2026-08-10 with red-verified regression tests; residual work is main's own self-report, the
  never-sampled sentinel, and the dashboard's "—" rendering. Original 2026-07-29 report follows.

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
last_updated: 2026-08-10
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

> **🔴 RE-ROOT-CAUSED 2026-08-10 — the mechanism below is SUPERSEDED.** The pane-scraping fallback this issue blamed
> (`worker_liveness._AUTO_COMPACT_RE` / `_TOKEN_USAGE_RE`) was REPLACED wholesale by the transcript-based
> `server/context_probe.py` on 2026-08-08 (agent-orchestrator@c6e6d98, "measure worker context from transcripts, learn
> window per model") — for the reasons in that module's own docstring, which measured the pane as blind 9/11 of the
> time. The 0% therefore has a DIFFERENT cause than the one recorded in the 2026-07-29 Evidence section; the section is
> kept for provenance, not as a current description. See "## 2026-08-10 — measured re-root-cause" below.

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

## 2026-08-10 — measured re-root-cause

Operator screenshot again ("I see a lot of 0% contexts — is main doing anything?"). Measured read-only against the live
`state.db` and `/api/agents` (AWS SSM, `i-0c9b283b31d6b5ca7`). Main was NOT idle: ping 11s, `last_msg` "Handled poll:
BLK-8252b53d already answered; routed 4 orphan commits", 6 compactions, 0→100% context in 11 minutes. The 0% is TWO
distinct defects that happen to render identically:

**(A) The register/poll roles never populate `AgentRow.context_used_pct` at all.** The Agents panel renders that column
(`routes/agents.py:314`). Slot WORKERS post their figure via `/api/slots/{id}/heartbeat`, but `main`/`review`/
`plan_reconciler`/one-shot `custom` agents use `/api/agents/{id}/poll`, and only `main.md`/`review.md` document sending
`context_used_pct` at all. Measured over the whole live corpus (206 agent rows, all time): `custom` **0/151** non-zero,
`plan_reconciler` **0/21** — never once, since the roles exist. `main` 11/13 and `review` 18/21 DID carry values, but
those were written server-side by `context_lifecycle.main_pct`'s probe ratchet, not by the agents themselves.

**(B) A regression, ~3h old at time of writing: main's SlotRow is clobbered to 0 every keeper tick, manufacturing
phantom compactions.** agent-orchestrator@bef2f6b (2026-08-10 09:27, "collapse main_pct into the unified \_read_pct slot
path") DELETED `main_pct` — the only writer of main's `AgentRow.context_used_pct` — and repointed `_sync_main_slot_row`
at that same field as its input, asserting in its docstring it is "the CLI's figure, posted by main on every tick". Per
(A) it is not posted; `AgentPollRequest.context_used_pct` defaults to `0`, so the field reads 0 forever. Two writers
then alternate on `SlotRow(0)`: `ContextLifecyclePolicy._read_pct` ratchets it UP to the probe reading, and
`_sync_main_slot_row` writes the raw 0 back over it. Any such overwrite ≥ `COMPACTION_DROP_THRESHOLD` (30) is read by
`update_slot_ping` as a compaction. Live proof — `compactions` row 2811 records main "compacting" **39→0** at 09:54:13,
sixty seconds before the REAL **39→5** `context_compact_observed` event at 09:55:17. The inflated `compactions_total`
drives `derive_context_pressure` to `"thrashing"`, which fired `context_recycle_requested` at 09:55:17 on a session with
only ONE genuine compaction in window. Main was recycled 4× between 04:42 and 09:32.

Downstream blast radius beyond the cosmetic column: a stored 0 cannot cross the 60% force-compact threshold, and
`_read_pct` reads this same row — so the policy is blind on main for the part of each cycle the 0 is winning.

## Todos

- [x] [BACKEND] P0. Stop `_sync_main_slot_row` writing a 0 self-report into `SlotRow(0)` — defect (B). A `0` is "not
      reported", never a measurement (the same 0-is-falsy convention `_main_context_pct_if_unrecoverable` already uses
      12 lines up), so skip the `update_slot_ping` entirely rather than clobber the probe-ratcheted value and
      manufacture a compaction. — agent-orchestrator@809c405 (code; see the provenance note in the Progress Log — that
      SHA is a PEER's commit that absorbed this change from the shared index) + agent-orchestrator@55c87c9 (tests) +
      regression test `test_zero_self_report_never_clobbers_the_probe_ratcheted_slot_value` (verified RED without the
      guard: asserts `39 == 0`, reproducing live `compactions` row 2811 exactly) +
      `test_real_self_report_still_writes_through_with_` `compaction_detection` proving a genuine 90→5 drop is still
      detected.
- [x] [BACKEND] P1. Populate the Agents-panel CONTEXT column for slot-bound register/poll agents — defect (A). Added
      `state_store.backfill_agent_context_from_slots`, an exact sibling of the existing
      `backfill_agent_accounts_from_slots` mirror (same "fill only the unset value, never clobber a real one"
      invariant), wired into the same keeper-tick reconcile block. Keys on the `orch-slot-` session prefix, which
      excludes main by construction — mirroring `SlotRow(0)` back onto main's AgentRow would close a feedback loop with
      `_sync_main_slot_row`, which READS that row to WRITE that slot. — agent-orchestrator@809c405 (code, same
      shared-index provenance caveat) + agent-orchestrator@55c87c9 (tests) + 3 tests in
      `tests/test_reap_orphan_agents.py`.
- [ ] [BACKEND] P1. Close the shared-index commit-contamination window this session hit for real (see the Progress Log
      provenance note): `quickmerge.sh --files` stages its named paths with `git add` and only then runs a BARE
      `git commit`, so any peer session in the same slot checkout that commits inside that window absorbs the staged
      files into ITS commit. Measured 2026-08-10: agent-orchestrator@809c405, a `docs(context)` commit about DeepSeek's
      token ceiling, shipped this issue's `main_agent_keeper.py` + `state_store/` fix to origin under its message and
      authorship, while the matching tests were left behind uncommitted (landed separately as @55c87c9). Existing guards
      do not cover this: `autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md` addresses the autostash pop,
      not the stage→commit race, and quickmerge's own `_qm_locked_git_commit` flock does not help — it SERIALISES
      commits without SCOPING them, so the peer's turn under the lock still commits whatever this session had staged.
      **The remedy already exists in this workspace and quickmerge simply has not adopted it**:
      `scripts/dev/safe-doc-push.sh` defaults to isolated-worktree mode (`SDP_ISOLATED=1`), building a private index in
      a throwaway worktree at `origin/<branch>`, copying in ONLY the named files, and leaving the caller's working tree
      untouched — added for the same class of race per
      `/plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md` (F6). Port that to
      `quickmerge.sh --files`, or at minimum swap the `git add` + bare `git commit` for an explicit
      `git commit -- <files>` pathspec, which ignores the rest of the index.
- [ ] [BACKEND] P2. Make main actually self-report `context_used_pct`, closing defect (A) at source for the one role the
      slot-mirror cannot cover (main is not on an `orch-slot-N` session). `agents/main.md:293` already instructs
      `"context_used_pct": <0-100, your /usage estimate>` on every `/poll`, yet the live row read 0 with a fresh ping —
      so either the CLI estimate is not being substituted or the field is being dropped. Determine which, then fix the
      role file or the poll contract. Until then main's reading comes solely from `_read_pct`'s probe ratchet.
- [ ] [DATA] P3. Decide the cheapest way to represent "never sampled": either (a) a schema migration adding a nullable
      `context_used_pct_sampled_at: datetime | None` column, or (b) reuse an existing signal (e.g. `last_ping` age vs
      `context_used_pct == 0`) as a heuristic without a schema change. Prefer (b) if it proves reliable enough —
      smaller, safer, no migration risk. NOTE 2026-08-10: materially less urgent now the slot-mirror fills the common
      case; the residual is a genuinely slot-less agent (cloud `review`) that has never reported.
- [ ] [UI] P3. Dashboard: render "—" rather than "0%" for the residual never-sampled case the DATA todo above defines,
      with a `pw:L2` regression spec covering both "genuinely fresh, real 0%" and "never sampled" so they don't get
      conflated. Downgraded P2→P3 on 2026-08-10: the two BACKEND fixes above remove the misleading 0% for every
      slot-bound agent kind, which was the reported symptom.
- [x] [BACKEND] P3. ~~Consider widening the pane-scrape to recognize the "N monitors still running" spinner variant~~ —
      **MOOT, not done.** The pane-scrape is no longer the context mechanism: agent-orchestrator@c6e6d98 (2026-08-08)
      replaced it with the transcript-based `context_probe.py`, which reads `message.usage` off every assistant turn and
      so never depended on what the spinner renders. Closing rather than carrying a todo against deleted machinery.

## Triage note

**2026-07-29 (still true for defect A):** not a functional bug in the sense of lost work or incorrect state —
`cicd1-shot`/`ag-closeout-auditor` workers are genuinely doing real work while reading 0%. A monitoring/display accuracy
gap, but a real one worth closing since it actively misleads an operator glancing at the dashboard into suspecting
stuck/idle workers that are not stuck.

**2026-08-10 — this is NO LONGER purely cosmetic.** Defect (B) writes state: it fabricates `compactions` rows, which
inflate `compactions_total` → `derive_context_pressure` → `"thrashing"` → premature `context_recycle_requested` on a
healthy main, and it parks a 0 in the row `_read_pct` consults, which cannot cross the 60% force-compact threshold. The
2026-07-29 "purely display" framing must not be carried forward to the whole issue.

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

- **interactive session 2026-08-10 (operator screenshot: "a lot of 0% contexts — is main doing anything?")**:
  re-root-caused against LIVE state (read-only SSM to `state.db` + `/api/agents`) and found the 07-29 mechanism
  SUPERSEDED — see "## 2026-08-10 — measured re-root-cause". Main was verifiably busy, not idle. Split into defect (A)
  never-populated AgentRow column and defect (B) a ~3h-old regression from agent-orchestrator@bef2f6b manufacturing
  phantom compactions on main's SlotRow. Shipped both BACKEND fixes (`_sync_main_slot_row` 0-guard +
  `backfill_agent_context_from_slots` mirror), 5 new tests, the (B) regression test verified RED against the unfixed
  code before landing. Retired the `[BACKEND] P3` pane-scrape todo as moot (its machinery was deleted on 08-08).
  Corrected the "purely a display gap" triage framing — (B) writes state and drives premature recycles. NOTE: this doc
  is no longer whole-doc NA — the two remaining BACKEND/DATA todos are bounded, but the `[UI] P3` still carries the
  pw:L2 gate, so the prior non-parallelizable finding stands for the UI item alone.

- **PROVENANCE NOTE 2026-08-10 — the code fix shipped inside a PEER's commit.** Recorded because the `- [x]` evidence
  SHAs above do not read as this session's own work and would otherwise look falsified. Both fixes were authored and
  gated here (quality-gates.sh PASSED, 3172 passed/4 skipped, against HEAD 905c210), but the shipping step raced a peer
  session sharing this slot-4 checkout — the slot clones share ONE `.git`, so a peer's commit advances HEAD and consumes
  the shared index. `quickmerge.sh --files` had already `git add`-ed the three source files when the peer's own bare
  `git commit` ran, absorbing them into agent-orchestrator@809c405
  (`docs(context): record DeepSeek's measured 1,048,565-token ceiling`) — which then pushed to origin, putting this fix
  LIVE under an unrelated message with no tests attached. quickmerge itself then failed on `.git/index.lock`. The tests
  were committed cleanly afterwards as @55c87c9. Nothing was lost and no history was rewritten (809c405 was already
  pushed; force-push is banned), but the fix and its tests are split across two commits with misleading provenance on
  the first. Filed as the new `[BACKEND] P1` todo above. Separately, this session's own `git pull` earlier triggered an
  autostash conflict in the peer's `tests/test_context_probe.py`; it was NOT resolved on their behalf and their stash
  was left intact — they resolved and landed it themselves (@905c210).

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read of all 3 open
  items. `[UI] P2` depends on `[DATA] P3`'s unresolved 'prefer (b) if it proves reliable enough' open reliability
  question (not a resolved preference); `[BACKEND] P3` stays blocked on an upstream Claude Code CLI change. round11
  (2026-08-09) already specifically considered and rejected the gated-pair-split pattern for this doc since the DATA
  prerequisite isn't itself resolved. No new facts found this pass.
