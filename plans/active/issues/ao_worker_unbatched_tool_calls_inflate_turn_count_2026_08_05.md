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
    /plans/active/deepseek_flash_ab_routing_test_2026_08_05.md,
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
    /plans/active/deepseek_flash_ab_routing_test_2026_08_05.md,
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

- [ ] [DATA] P2. **Confirm this is systemic, not one outlier task** — sample transcripts from 5-10 more completed tasks
      across different models/providers/plan-types (mirroring this session's SSM-based sampling method) and measure the
      same batching metrics (tool-calls-per-turn, % of turns with <5s gaps). Done-when: a written verdict on whether the
      single-tool-call-per-turn pattern generalizes fleet-wide or was specific to this task/worker.
- [ ] [DOC] P2. **If confirmed systemic**, strengthen the parallel-tool-call instruction in `agents/worker.md` and/or
      `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — the existing CLAUDE.md instruction is present but evidently not
      being internalized during a worker's own boot-sequence reads (the sampled task's own first 3 tool calls were
      sequential reads of its own onboarding docs). Consider a concrete worked example in the boot sequence itself
      ("batch these N onboarding reads in one turn") rather than a general principle stated once.
  - [ ] [INFRA] P3. **Consider a soft turn-count circuit breaker** — no mechanism today stops a task at 150-200+ turns;
        a checkpoint/flag past a threshold would catch both this batching gap and any genuine stuck loop, and composes
        with the existing `deepseek_flash_ab_routing_test_2026_08_05.md` quality-audit's turn-count metric.

## Codex / related

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`
- `plans/active/deepseek_flash_ab_routing_test_2026_08_05.md` — the DeepSeek pro/flash A/B test this finding originated
  alongside (different question — model choice — but the same investigation).

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
