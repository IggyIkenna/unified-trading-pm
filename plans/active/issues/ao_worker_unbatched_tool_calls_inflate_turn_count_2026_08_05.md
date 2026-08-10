---
doc_type: issue
title:
  "AO workers frequently issue independent tool calls one-per-turn instead of batching them — measured, real, fleet-wide"
summary: >-
  A cost-per-task investigation (2026-08-05, interactive session) sampled the real transcript of a 600-turn DeepSeek
  task (`sports_consolidated_native_ao_extract-022`, slot 14, strong provenance) and found 506 separate Bash calls and
  69 separate Reads spread across 1,723 assistant turns, with 78% (1,350/1,722) of turn-to-turn gaps under 5 seconds —
  independent, parallelizable lookups (grep a keyword, check 3 candidate plan files, read 3 onboarding docs) fired one
  at a time in sequential turns rather than batched into fewer multi-tool turns. Because every turn resends the entire
  accumulated conversation as a cache-read (inherent to the stateless completions API), turn count is the actual cost
  multiplier — fleet-wide `task_usage` turn-count averages 77.7 (n=1,341, right-skewed to 500+ in the tail) despite
  CLAUDE.md already instructing "make all independent tool calls in parallel." This is not a DeepSeek-specific finding
  (the sampled task happened to run on `deepseek-v4-flash`, but the pattern is a general worker-prompt-adherence gap,
  not a model limitation) and is not itself a data-correctness issue — filing as its own issue per the findings-triage
  rule (outside every existing plan) rather than folding it into the DeepSeek flash A/B test, which is a different
  question (model choice, not tool-call batching).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, cost-optimization, worker-prompt, tool-use, turn-count, cache-read]
related:
  [
    /plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/audit/results/claude_account_usage_value_measurement_2026_08_01.md,
  ]
created: 2026-08-05
author: ikennaigboaka [interactive session]
parent_epic: orchestrator_master
priority: P2
assigned_vm: NA
execution_scope: local-only
resolved_by:
locked_by:
source: ["interactive session, cost-per-task investigation, transcript sample via SSM against the live orchestrator VM"]
drift_direction: advance-process
estimate_class: research
depends_on: []
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    agents/worker.md,
    cursor-configs/SUB_AGENT_MANDATORY_RULES.md,
    /plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md,
    /plans/active/ao_satellite_ao_dispatch_batch7_2026_08_06.md,
  ]
---

# AO workers issuing independent tool calls one-per-turn instead of batching — measured, real

## Evidence

Sampled transcript (`orch-slot-14`, task window `2026-08-05T12:06:38` → `15:17:00`, live/strong provenance, not a
backfill artifact): `{'Read': 69, 'Bash': 506, 'Edit': 40, 'Write': 10, ...}` across 1,723 assistant turns. Turn-to-turn
gap distribution: min 0.061s, median 1.07s, p90 17.2s, max ~18min; **78% of gaps were under 5 seconds** — consistent
with rapid sequential single-tool turns, not batched parallel calls or genuine waiting. The task's own first minute
shows the pattern concretely: 3 separate `Read` calls for `agents/RULES.md`/`worker.md`/`data_engineering.md` (the
mandatory boot-sequence docs), then 2 sequential `curl .../boot` calls, then a serial chain of `Read`/`grep`/`find`
calls hunting for the right plan file across 3 candidate locations — all independent, parallelizable lookups.

Fleet-wide `task_usage` turn-count stats (n=1,341, all models/providers, 2026-08-05): min 1, avg 77.7, max 2,452;
histogram is right-skewed with a real tail into the 500+ bucket (10 tasks, ~15% of total cache-read token volume despite
being <1% of tasks by count).

## Why this matters

Every turn in a stateless completions API resends the full accumulated conversation as input (mostly hitting cache).
Turn count — not context size per se — is therefore the direct multiplier on both real $ (for metered providers) and
quota consumption (for flat-rate Claude subscriptions, where burning through weekly/5-hour caps faster means fewer tasks
completed per subscription-dollar). Batching the independent lookups in the sampled task into ~50-100 multi-tool turns
instead of 500+ single-tool turns would plausibly cut that task's turn count 5-10x with no loss of capability —
CLAUDE.md already instructs this ("make all independent tool calls in parallel... if there are no dependencies between
them"), but the instruction is not being followed in practice, at least in this sample.

## Open follow-ups

- [x] [DATA] P2. **Confirm this is systemic, not one outlier task** — sample transcripts from 5-10 more completed tasks
      across different models/providers/plan-types (mirroring this session's SSM-based sampling method) and measure the
      same batching metrics (tool-calls-per-turn, % of turns with <5s gaps). Done-when: a written verdict on whether the
      single-tool-call-per-turn pattern generalizes fleet-wide or was specific to this task/worker. ✅ CONFIRMED
      SYSTEMIC — see Progress Log for the full 12-task measurement + a real parsing-bug fix found along the way.
- [x] [DOC] P2. **If confirmed systemic**, strengthen the parallel-tool-call instruction in `agents/worker.md` and/or
      `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — the existing CLAUDE.md instruction is present but evidently not
      being internalized during a worker's own boot-sequence reads (the sampled task's own first 3 tool calls were
      sequential reads of its own onboarding docs). Consider a concrete worked example in the boot sequence itself
      ("batch these N onboarding reads in one turn") rather than a general principle stated once. ✅
      unified-trading-pm@a20e52125 — added a concrete "batch these reads in one turn" worked example directly at
      `agents/worker.md`'s STEP 1 (the exact boot-sequence reads the original sample caught firing sequentially), plus a
      tight cross-referencing one-liner in `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` (budget-constrained —
      9832/10240 bytes after the edit, so it points back to worker.md's example rather than duplicating it).
  - [ ] [INFRA] P3. **Consider a soft turn-count circuit breaker** — no mechanism today stops a task at 150-200+ turns;
        a checkpoint/flag past a threshold would catch both this batching gap and any genuine stuck loop, and composes
        with the existing `deepseek_flash_ab_routing_test_2026_08_05.md` quality-audit's turn-count metric.

## Codex / related

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`
- `plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md` — the DeepSeek pro/flash A/B test this finding
  originated alongside (different question — model choice — but the same investigation).

## Progress Log

- **context-scout 2026-08-05**: populated context_scope (4 entries).

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **`/ag-closeout-audit ao` 2026-08-06 (autonomous)**: genuinely orphaned — cited nowhere in any covering plan/batch for
  this tranche. Its own NA self-classification stays out of scope (that's `/na-eligibility-audit`'s call, re-affirmed
  above the same day). Extracted the 2 bounded, sequential items (confirm-systemic sample, then strengthen the worker
  prompt if confirmed) into `ao_satellite_ao_dispatch_batch7_2026_08_06.md` todo 1 as one combined todo (internally
  sequential — item 2 is conditional on item 1's finding). Item 3 ("consider a soft turn-count circuit breaker") stays
  here — unscoped design fork, not batch material.

- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — added
  `/plans/active/ao_satellite_ao_dispatch_batch7_2026_08_06.md`, which now carries this doc's items 1-2 as a combined
  todo (item 3 is the only one still open here).

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — verified `ao_satellite_ao_dispatch_batch7_2026_08_06.md` (todo
  1, real verbatim match on the confirm-systemic + strengthen-prompt combined ask) is still `status: draft` /
  `assigned_vm: NA`, not yet an ACTIVE `planning` doc, so verdict 3 (already-duplicated) doesn't strictly apply — this
  doc stays the live tracking home until batch7 activates. Item 3 (soft turn-count circuit breaker) remains an unscoped
  design fork.

- **2026-08-08 (slot 25, `data_engineering`, dispatched via `ao_satellite_ao_dispatch_batch7_2026_08_06.md` todo 1)**:
  Executed items 1-2. **VERDICT: CONFIRMED SYSTEMIC.**

  **Method**: this worker's session runs directly ON the orchestrator VM (`i-0c9b283b31d6b5ca7` — confirmed via
  `curl localhost:8765/api/mode` succeeding and `state.db`'s real path being directly readable on local disk), so the
  sample ran via direct local sqlite/filesystem access rather than the SSM wrapper the original session used — same
  underlying data (`task_usage` joined with `tasks` for `plan_ref`, transcripts at
  `~/.claude-configs/orch-slot-<n>/projects/*/<claude_session_id>.jsonl`), no functional difference, just a shorter path
  once you're already on the box (mirrors the fix already recorded in
  `/plans/archive/issues/escalation_queue_reconciler_ssm_permission_gap_2026_08_08.md` — a dispatched worker calling
  `localhost` directly instead of routing SSM to reach the machine it's already running on). `ikenna-worker`'s IAM user
  does NOT have `ssm:SendCommand` on this instance (confirmed live, `AccessDeniedException`) and is not one of the two
  self-service identities in `orchestrator-cloud-identity-self-service.md`, so this also sidesteps that same gap.

  Stratified sample of **12 completed tasks**, 3 per (provider, model) bucket across all 4 live combinations
  (`anthropic/claude-sonnet-4-6`, `anthropic/claude-sonnet-5`, `deepseek/deepseek-v4-pro`,
  `deepseek/deepseek-v4-flash`), further diversified by `plan_ref` prefix so no two samples share a plan — spans
  finalize-plans, satellite-dispatch-batch todos, issue-doc fixes, and one-off completions (min 20 turns/task to have a
  meaningful gap distribution). Measured the same two metrics as the original sample (tool-calls-per-turn, %
  turn-to-turn gaps <5s) plus one the original didn't isolate explicitly: **% of turns that batch >1 tool call**.

  **Real methodological trap hit and fixed along the way** (worth recording — could silently poison a future re-run of
  this same method): the transcript JSONL streams ONE content block per line, with several lines sharing the SAME
  `message.id` for a single logical turn (confirmed live: message `5b18947b-...` in slot 14's transcript streams 3
  SEPARATE `TaskCreate` tool_use lines under one id). A first version of the sampling script treated `message.id` as a
  last-write-wins key (`turns[mid] = {...}`) — this silently collapsed every genuinely multi-tool turn down to whatever
  its LAST streamed line happened to carry, producing a false **0.0%-multi-tool-turns** reading across all 12 tasks AND
  a 60-file/~10,800-turn random fleet-wide scan before the bug was caught (spot-checked by hand-parsing one raw
  transcript file and finding 12 accumulated multi-tool message ids the buggy script had reported as single). Fixed by
  accumulating tool_use blocks per `message.id` across every line instead of overwriting. Numbers below are POST-fix
  (correct).

  **Fleet-wide results (12 tasks, all usable)**:

  | provider/model              | n      | avg % single-tool turns | avg % multi-tool turns | avg % gaps <5s |
  | --------------------------- | ------ | ----------------------- | ---------------------- | -------------- |
  | anthropic/claude-sonnet-4-6 | 3      | 95.5%                   | 4.5%                   | 24.3%          |
  | anthropic/claude-sonnet-5   | 3      | 95.4%                   | 2.9%                   | 42.6%          |
  | deepseek/deepseek-v4-flash  | 3      | 82.6%                   | 15.7%                  | 40.6%          |
  | deepseek/deepseek-v4-pro    | 3      | 78.8%                   | 19.6%                  | 24.1%          |
  | **overall**                 | **12** | **88.1%**               | **10.7%**              | **32.9%**      |

  Per-task raw metrics (n_turns / total_tool_calls / avg_tool_calls_per_turn / pct_multi_tool_turns /
  pct_gaps_under_5s): `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout-002` (sonnet-5)
  101/101/1.00/4.0%/47.0%; `no_active_paper_run_blocks_p1_2_determinism_recheck_..._finalize-59415e713f9a` (sonnet-5)
  29/31/1.07/3.4%/39.3%; `one_shot_complete_session_ownership_desync_2026_08_08_finalize-001` (sonnet-5)
  83/83/1.00/1.2%/41.5%; `defi_compute_gcp_migration-005` (sonnet-4-6) 75/76/1.01/1.3%/23.0%;
  `content_derived_backlog_task_ids-003` (sonnet-4-6) 59/62/1.05/3.4%/17.2%;
  `sports_taxonomy_p1_capture_and_contracts-014` (sonnet-4-6) 56/61/1.09/8.9%/32.7%; `one-off:agt-6f12db`
  (deepseek-v4-pro) 42/51/1.21/21.4%/12.2%; `sports_satellite_ao_dispatch_batch9-026` (deepseek-v4-pro)
  50/67/1.34/28.0%/40.8%; `tradfi_satellite_ao_dispatch_batch2_finalize-003` (deepseek-v4-pro) 63/70/1.11/9.5%/19.4%;
  `one-off:agt-6eb8c5` (deepseek-v4-flash) 220/250/1.14/11.8%/38.4%;
  `prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize-001` (deepseek-v4-flash) 60/75/1.25/23.3%/39.0%;
  `deployment_api_sigabrt_crash_loop-030` (deepseek-v4-flash) 100/115/1.15/12.0%/44.4%.

  **Interpretation**: the pattern generalizes fleet-wide, across every provider/model combo and plan-type sampled — no
  combo comes close to CLAUDE.md's "make all independent tool calls in parallel" being the norm; **~88-90% of turns fire
  exactly one (or zero) tool calls**. The specific 78%-gaps-under-5s figure from the original single-task sample was on
  the high end of what a broader sample shows (fleet avg 32.9%, range 12.2%-47.0% per-task) — so that one number doesn't
  generalize precisely — but the underlying claim (independent tool calls are overwhelmingly NOT batched) is confirmed,
  and even more starkly for Anthropic/Claude models (2.9-4.5% multi-tool) than for DeepSeek (15.7-19.6% multi-tool) —
  the opposite direction from what the original DeepSeek-sourced sample might have suggested, i.e. this is not a
  DeepSeek-specific gap.

  **Action taken (item 2)**: added a concrete "batch these onboarding reads in ONE turn" worked example directly into
  `agents/worker.md`'s STEP 1 boot sequence (the exact 2-3 reads the original sample caught firing as separate
  sequential turns), citing this doc's measured numbers so the instruction carries evidence, not just the restated
  general principle. Also added a tight cross-referencing bullet to `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
  (budget-constrained at 10KB — pointed back at worker.md's example rather than duplicating the worked example there).
  Shipped `unified-trading-pm@a20e52125`.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **1**, matching. Sole open item ("Consider a soft turn-count circuit breaker") uses the same "Consider" hedge phrasing
  this sweep treats as a judgment call, not a mandate, elsewhere in this tranche — no committed threshold or mechanism,
  a genuine design fork. Items 1-2 already correctly executed + closed via
  `ao_satellite_ao_dispatch_batch7_2026_08_06.md`.
