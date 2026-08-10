---
doc_type: plan
title: AO satellite AO batch 7 — seventh dispatch batch extracted from the AO tranche's satellite docs
summary: >-
  SEVENTH AO-dispatch batch for the `ao` topic tranche, produced by the `/ag-closeout-audit ao` skill run (2026-08-06,
  autonomous mode, scheduled `ag_closeout_auditor` dispatch, slot 10). Phase 0 re-derived the tranche's covering-plan
  set (unchanged in shape from batch6's own run: batch1+finalize archived, batch2-6+finalizes active — batch5/batch6
  still `status: draft`, awaiting operator approval — plus `ao_open_issues_consolidated_close_out_2026_07_17.md`). Phase
  0.3's Orthogonality/meta sweep found + retagged 2 genuine `ao` mistags (bare `[meta]` with `orchestrator_master`
  `parent_epic`) directly, contributing 2 of this batch's 3 todos. Phase 1 cross-referenced
  `generate_ag_closeout_audit_candidates.py --tranche ao`'s 3 never-cited candidates plus
  `check_ag_closeout_linkage.py`'s broader `ao`-tagged orphan list against every existing batch's own text (not just the
  mechanical pre-filter, which undercounts once a Deferred section starts text-citing basenames — same lesson batch6
  already recorded) to isolate what is genuinely new since batch6's 2026-08-04 run: 3 docs archived directly (all-done
  bookkeeping, zero risk), 2 docs retagged directly (meta mistags), 3 bounded items extracted into this batch, and 1
  doc's remaining items deferred on a genuine conflict against a same-day, actively-shipping sibling plan
  (`shared_ci_workflow_repo_extraction_2026_08_06.md`) — surfaced, not silently dropped. One doc
  (`deepseek_flash_ab_routing_test_2026_08_05.md`) confirmed NOT orphaned: a large, actively-maintained, self-covering
  LOCAL plan with its own live Deferred table.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-7, satellite-docs]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md,
    /plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md,
    /plans/active/ao_satellite_ao_dispatch_batch6_finalize_2026_08_04.md,
    /plans/active/ao_satellite_ao_dispatch_batch5_2026_08_03.md,
    /plans/active/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 0.48
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /plans/active/ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/autospawn.py,
  ]
source: >-
  /ag-closeout-audit ao skill run 2026-08-06 (autonomous, scheduled ag_closeout_auditor dispatch, slot 10) — Phase 0
  confirmed the tranche's covering-plan set unchanged in shape from batch6's own run. Phase 1 diffed
  `generate_ag_closeout_audit_candidates.py`'s 3 never-cited candidates + `check_ag_closeout_linkage.py`'s broader
  `ao`-tagged orphan list against every existing batch/finalize's own text (Deferred sections included) to isolate
  genuinely-new-since-batch6 material — a direct per-doc read (not a re-run of the full 64-doc Workflow fan-out, since
  the delta since 2026-08-04 was small enough to review directly: ~9 candidate docs total). Phase 3's conflict-check ran
  against the whole `plans/active` corpus for every candidate's target file(s)/mechanism before drafting.
---

# AO satellite AO batch 7

> **`status: active`** — approved 2026-08-08 after a fresh conflict-check found no blocking overlap and all 3 todos
> re-verified still genuinely open (see Progress Log). **`assigned_vm: planning` /
> `execution_scope: orchestrator-agent`** — the `ao` tranche's 2026-07-17 "local execution only" ruling was explicitly
> LIFTED 2026-08-08 (operator, interactive); see batch5's Progress Log for the full citation trail. AO-dispatchable now,
> same as every other tranche. Authored autonomously (scheduled dispatch) and originally shipped `status: draft` pending
> operator approval.

## Why this plan exists

A fresh `/ag-closeout-audit ao` run (2026-08-06) confirmed the tranche's covering-plan set is unchanged in shape since
batch6's 2026-08-04 run (batch5/batch6 both still `status: draft`, awaiting operator approval — per Phase 0.2's rule, a
draft batch still counts as covering). Rather than re-running the full 64-member Workflow fan-out batch6 already did two
days ago, this run diffed the mechanical pre-filter's candidate list against every existing batch's full text (Deferred
sections included, per batch6's own lesson that a doc merely _named_ in a Deferred section reads as "cited" to the cheap
filter while still being genuinely uncovered) to isolate what changed: **9 docs needed a fresh look** — 4 genuinely new
(created 2026-08-05/08-06, after batch6's scan), 2 pre-existing docs the mechanical filters disagreed on (present in
`check_ag_closeout_linkage.py`'s broader orphan list but absent from every batch's text), 1 doc believed AO-tagged that
turned out to be `[meta]`-tagged and out of scope until retagged (mirroring batch6's own "8 more genuine mistags found
outside the scan" pattern), and 2 more `[meta]`-tagged docs surfaced by the same sweep. Verdict on all 9: 3
`archivable_now` (all-`[x]`, done directly — see Progress Log, same zero-risk-housekeeping precedent batch6 set for
`ao_docs_reconciliation_2026_07_15.md`), 2 mistags retagged directly (`[meta]` → `[ao]`), 1 confirmed NOT orphaned
(self-covering active plan), and the remainder split 3 AO-eligible-and-drafted (this batch's 3 todos) vs. 1 partially
conflict/operator/time-gated (parked below, not silently dropped).

## Rules for every worker on this plan

- Put each todo's new test cases in a test module named for that todo's own concern. The 3 todos below are
  file-disjoint.
- **File-adjacency (soft caution, not a hard collision)**: todo 2 (`autospawn.py` spawn-success path) and todo 3
  (`worker_liveness_watchdog.py` `_tick_once()` reorder) both cite the SAME source issue doc
  (`/plans/archive/2026_08/issues/ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md`) for their own separate
  checkbox. Re-pull that doc fresh immediately before flipping your checkbox regardless of which todo you picked up — no
  code-file overlap, but a stale read on the source doc's own file could silently clobber the other todo's flip.
- Do not edit a source issue doc's checkboxes beyond appending your evidence line to the todo you executed. The paired
  finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md`) reconciles evidence back into
  every source doc and runs archival.
- No todo below deletes prod data, mutates a GCS bucket, or launches a VM.

## Todos

- [x] [DATA] [DOC] P2. **Confirm whether the fleet-wide single-tool-call-per-turn pattern is systemic, then strengthen
      the worker prompt if it is — one combined todo since the second half is conditional on the first's finding.**
      Sample transcripts from 5-10 more completed tasks (mirror the source doc's own SSM-based sampling method: pull
      real transcripts across different models/providers/plan-types) and measure the same batching metrics
      (tool-calls-per-turn, % of turn-to-turn gaps under 5s) already measured on the one sampled task
      (`sports_consolidated_native_ao_extract-022`, 506 Bash + 69 Read calls across 1,723 turns, 78% sub-5s gaps). If
      the pattern generalizes fleet-wide (not specific to that one task/worker), strengthen the parallel-tool-call
      instruction in `agents/worker.md` and/or `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` with a concrete worked
      example in the boot sequence itself (e.g. "batch these N onboarding reads in one turn") rather than relying on the
      general principle CLAUDE.md already states once. If it does NOT generalize, record that verdict with the sampled
      evidence and stop — no doc change needed. **Done when**: a written verdict (systemic / not systemic) with the raw
      per-task metrics for all 5-10 sampled tasks exists in the source doc's Progress Log; if systemic, the doc edit
      lands with a concrete example, not just a restated principle; the source doc's first 2 `- [ ]` items flip `[x]`
      citing the evidence + (if applicable) the commit sha. The 3rd item ("consider a soft turn-count circuit breaker")
      is explicitly OUT of scope for this todo — unscoped design fork, see Deferred. Source:
      `/plans/active/issues/ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md` (its first 2 items only).
      Repo: agent-orchestrator, unified-trading-pm. ✅ unified-trading-pm@a20e52125 — CONFIRMED SYSTEMIC (12-task
      stratified sample across all 4 provider/model combos, 88.1% single/0-tool turns, only 10.7% multi-tool turns
      fleet-wide; full raw metrics + a real parsing-bug fix found along the way in the source doc's Progress Log).
      Strengthened `agents/worker.md` STEP 1 with a concrete worked example + a cross-referencing bullet in
      `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`. Source doc's first 2 items flipped `[x]`.

- [x] [SCRIPT] P2. **Reset `spawn_retry_count = 0` in the shared automatic spawn-success path so a slot's diagnostic
      retry-with-pane-diagnosis capability isn't permanently disabled after one lifetime retry-cap trip.** In
      `agent-orchestrator/server/autospawn.py` (~lines 2086-2110, "Shared success point for ALL spawn callers"), add the
      reset alongside the other fields already cleared there (`tmux_session`/`last_spawned_at`/`account_id`/the alert
      latch). Add a regression test mirroring the existing spawn-success-resets-fields tests, asserting
      `spawn_retry_count` returns to 0 after a successful spawn even when it was previously non-zero. Also correct
      `notify_spawn_failed`'s alert text so it no longer implies a dead end ("slot stays down until manual respawn or
      reclaim") when Trigger-3 (`worker_liveness_watchdog.py`'s heartbeat-silent kill+respawn) will, in practice,
      usually recover the slot ~15 min later without manual action. **See this plan's file-adjacency rule before
      starting.** **Done when**: the new regression test passes; full `agent-orchestrator` `quality-gates.sh` green; the
      alert text no longer overstates the dead-end. Source:
      `/plans/archive/2026_08/issues/ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md` (its 1st item only).
      Repo: agent-orchestrator. ✅ agent-orchestrator@bc37d03 — spawn_retry_count=0 added to shared spawn-success path
      (autospawn.py:2146); test_do_spawn_resets_spawn_retry_count added (tests/test_autospawn.py:1367); "stays down
      until manual respawn" text corrected to Trigger-3 auto-recovery message (worker_liveness/_auth_failover.py). QG
      green.

- [x] ✅ [SCRIPT] P2. **Reorder `WorkerLivenessWatchdog._tick_once()`'s cleanup/reconcile sub-mechanisms ahead of the
      daily-kill-cap early-return, and fix a stale docstring.** — agent-orchestrator@bc37d03 (reorder + docstring fix) +
      agent-orchestrator@53492cb (notify_watchdog_kill cap-hit alert text disclosure +
      test_tick_daily_cap_still_runs_orphan_session_reclaim regression test). Verified: orphan-session reclaim
      (`_tick_once`, server/worker_liveness_watchdog.py) runs ahead of the `_daily_cap_reached()` check; full
      `quality-gates.sh` green (2769 passed). Today `if self._daily_cap_reached(): return` sits after
      `_sweep_dirty_slots`/`_sweep_unpushed_slots` (deliberately moved ahead of it in a prior incident fix) but before
      everything else — including orphan-session reclaim, whose OWN comment already states it is cleanup of an
      already-dead worker, not a new kill decision, so it is mis-gated by sitting after the cap check. Move
      cleanup/reconcile mechanisms (starting with orphan-session reclaim) ahead of the cap check, using the same
      rationale as the already-fixed sweeps. For the mechanisms that genuinely ARE new-kill triggers, make a deliberate,
      documented call on whether each should also survive a cap-hit day or correctly stay gated — don't leave the
      boundary implicit; record the reasoning in the module docstring or an inline comment next to each decision. Fix
      the stale "default 20" docstring reference (module docstring, ~lines 37/41) to match the live default (50,
      `config.py:1090`). Update `notify_watchdog_kill`'s cap-hit alert text to disclose which mechanisms actually go
      dormant on a cap-hit day, not just future kills. **See this plan's file-adjacency rule before starting.** **Done
      when**: a regression test proves orphan-session reclaim (and any other cleanup mechanism moved) still runs on a
      cap-hit tick; the docstring matches the live default; the alert text is accurate; full `agent-orchestrator`
      `quality-gates.sh` green. Source:
      `/plans/archive/2026_08/issues/ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md` (its 2nd item only — its
      3rd item is explicitly operator-decision-framed, stays in that doc). Repo: agent-orchestrator.

## Deferred — the 1 partially-declined doc + the 1 confirmed-not-orphaned doc

**Ledger check**: 9 docs needing a fresh look this run − 3 `archivable_now` (archived directly) − 2 meta-mistags
(retagged directly, one fully self-covering with no batch extraction needed, one contributing 2 of this batch's 3 todos)
− 1 confirmed-not-orphaned − 1 doc contributing 1 of this batch's 3 todos (its 3rd item declined) − 1 doc fully declined
= 1 doc with ALL its remaining items declined, named below (count verified against this run's own per-doc read, not
eyeballed).

- **Conflict-gated** (against a same-day, actively-shipping sibling plan's own claim on the same files):
  `agent_orchestrator_ldr_terminal_promotion_2026_08_05.md`'s 1st item (LDR-triggered `quality-gates-v2` template
  extension) — targets the same files (`quality-gates-v2.yml.tmpl`, `rollout-workflow-templates.sh`) as
  `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 18, not resolvable from evidence alone whether the two are the
  same fix or independent; its 2nd item is explicitly `[OPERATOR]`-tagged stretch/not-needed-today; its 3rd item is
  blocked on a separate repo's `RB-04f4f852` qg_red blocker (time/dependency-gated, different repo's problem). Full
  reasoning on the source doc's own Progress Log — re-check next iteration once
  `shared_ci_workflow_repo_extraction_2026_08_06.md` lands or `RB-04f4f852` clears (both are the specific named gates to
  re-check per the skill's iterative-drain methodology, not a re-derivation from scratch). **RESOLVED (per this batch's
  own finalize doc, `ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md` todo 3)**: both gates confirmed cleared,
  and the underlying work independently landed + archived 2026-08-07 — no batch-8 spin-off needed after all.
- **Too-large/unscoped-design** (declined as part of todo 1's own source doc, not a separate doc):
  `ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md`'s 3rd item ("consider a soft turn-count circuit
  breaker") — a "consider whether..." fork with no stated done-when, same class batch5/6 already declined elsewhere.
- **Operator-gated** (declined as part of todo 2/3's own source doc, not a separate doc):
  `ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md`'s 3rd item — explicitly framed as "worth an operator
  decision" (whether heavy one-off scripts should be barred from the shared host during full-fleet hours).
- **Confirmed NOT orphaned** (no action needed, noted for completeness): `deepseek_flash_ab_routing_test_2026_08_05.md`
  — a large, actively-maintained LOCAL plan (`assigned_vm: NA` by deliberate operator choice) with its own live Deferred
  table tracking every one of its open items (next real milestone: its 24h A/B window closes ≈2026-08-06 20:41 UTC).
  Self-covering; extracting from it here would duplicate its own tracking, not close a gap.

None of the above are re-triageable by re-running this same mechanical filter again without new information — the next
`/ag-closeout-audit ao` pass should re-check each one's _specific named gate_ (per the skill's iterative-drain
methodology step 1), not re-derive the classification from scratch.

## Codex SSOTs (read before starting a todo)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, `…/agent-orchestrator-overview.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`, `/codex/04-architecture/agent-orchestrator-worker-liveness.md`,
`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

## Progress Log

- **2026-08-06** — Authored by `/ag-closeout-audit ao` (autonomous mode, scheduled `ag_closeout_auditor` dispatch, slot
  10). Phase 0 confirmed the covering-plan set unchanged in shape from batch6's run. Phase 1 diffed the mechanical
  never-cited/orphan pre-filters (`generate_ag_closeout_audit_candidates.py`: 3 never-cited;
  `check_ag_closeout_linkage.py`: 15 broader `ao`-tagged orphans) against every existing batch/finalize's full text
  (union, then subtract everything already named in batch5/batch6's own Deferred sections or their Todos' `Source:`
  citations) to isolate 9 docs genuinely needing a fresh look, then read each directly (no Workflow fan-out — the delta
  was small enough for a direct per-doc read this run). Results, each independently verified before acting: (1)
  `features_cross_instrument_smoke_verify_unbounded_memory_second_ao_outage_2026_08_01.md` and
  `na_eligibility_auditor_timer_not_yet_installed_2026_07_27.md` — both `archivable_now` (all todos already `[x]`,
  `status` never flipped off `open`) — archived directly, referrer paths fixed corpus-wide (structured leading-slash
  citations only; already-archived docs' historical prose mentions left untouched per convention). (2)
  `escalation_watchdog_stale_merged_pr_false_unresolved_2026_08_06.md` — already `status: resolved`, both todos `[x]`,
  simply never archived — archived directly. (3) `ao_done_categorization_display_and_quickmerge_gate_2026_08_06.md` and
  `ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md` — both genuine `[meta]`→`[ao]` mistags (content squarely
  agent-orchestrator-internal), retagged directly; the former is fully self-covering (no extraction needed), the latter
  contributed todos 2-3 above. (4) `deepseek_flash_ab_routing_test_2026_08_05.md` — confirmed NOT orphaned
  (self-covering active LOCAL plan). (5) `ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md` — genuinely
  orphaned, contributed todo 1 above (its 2 sequential items combined per the skill's "internally-sequential work
  becomes ONE todo" rule). (6) `agent_orchestrator_ldr_terminal_promotion_2026_08_05.md` — genuinely orphaned but ALL 3
  items declined: item 1 conflict-gated against `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 18 (same target
  files, same-day actively-shipping sibling plan — not resolvable from evidence alone, so parked rather than drafting a
  possibly-competing todo), item 2 explicit `[OPERATOR]` stretch, item 3 blocked on a different repo's `RB-04f4f852`.
  Phase 3's conflict-check ran against the whole `plans/active` corpus for every drafted todo's target file(s) — todo
  1's target files (`agents/worker.md`, `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`) and todos 2-3's target files
  (`autospawn.py`, `worker_liveness_watchdog.py`) all came back clear (the `_tick_once`/daily-kill-cap string hit 2
  false-positive matches — batch3's todo 2 deliberately sidestepped `_tick_once` by building a standalone module
  instead, and the other hit was a different `usage_poller.py::_tick_once()` on an unrelated topic). Left
  `status: draft` deliberately — flipping to `active` is the operator's call.
- **Parked-findings ledger**: 1 finding parked this run (the conflict-gated `agent_orchestrator_ldr_terminal_promotion`
  item) — written durably on its own source doc's Progress Log (Phase 3 ran this session, so this batch's own Deferred
  section above is the primary durable home per the skill's parking rule; the source-doc note is a pointer back to it,
  not a duplicate record).
- **2026-08-08 (operator-authorized draft→active review)** — Re-ran the shared 3-surface conflict-check against (a)
  active `assigned_vm: planning` plans in `parent_epic: orchestrator_master` (only the batch finalize twins, all
  correctly `gate_on_depends`-held), (b) sibling batches 5/6/8 (no new overlap), (c)
  `ao_open_issues_consolidated_close_out_2026_07_17.md` (not touched by this batch's todos, no conflict). All 3 todos'
  Source docs (`ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md`,
  `ao_human_gated_recovery_audit_closable_gaps_2026_08_06.md`) re-verified still `status: open` with the specific
  referenced items still `[ ]` — no stale/already-done items found (unsurprising, this batch was drafted only 2 days
  prior). Applied the same `assigned_vm`/`execution_scope`-unchanged treatment as batch5/batch6 (see batch5's Progress
  Log for the full investigation); flipped `status: draft → active` only. Fixed the stale draft-era H1 banner to match.
- **2026-08-08 (operator, interactive)**: RULED — the 2026-07-17 local-only ruling is LIFTED going forward; see batch5's
  Progress Log for the full note. `assigned_vm: NA → planning`, `execution_scope: local-only → orchestrator-agent`
  applied here too.
- **2026-08-08 (slot 25, `data_engineering`, dispatch `ao_satellite_ao_dispatch_batch7-001`)**: Executed todo 1. Sampled
  12 real completed tasks (stratified across all 4 live provider/model combos + diverse plan_refs) directly on the
  orchestrator VM (this worker's session runs ON `i-0c9b283b31d6b5ca7` — direct `localhost:8765`/local sqlite access, no
  SSM needed; `ikenna-worker` lacks `ssm:SendCommand` on this instance regardless, confirmed live). **Verdict: CONFIRMED
  SYSTEMIC** — fleet-wide only 10.7% of turns batch >1 tool call (88.1% single/0-tool). Full raw metrics + a real
  transcript-parsing-bug catch (message-id stream accumulation, not overwrite) are in the source doc's Progress Log.
  Strengthened `agents/worker.md`'s STEP 1 boot sequence with a concrete worked example + a budget-fit cross-reference
  in `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`. Source doc's first 2 items flipped `[x]`. Todo 2/3 (file-adjacent,
  same source doc) untouched by this dispatch.
