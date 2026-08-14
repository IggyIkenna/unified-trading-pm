---
doc_type: codex-ssot
title: Tool-call batching — collapse sequential calls that gain nothing from being sequential
summary: >-
  Every extra tool call re-reads the entire cached prompt prefix and costs a full model round-trip. 57.3% of measured
  calls were consecutive same-tool chains collapsible into one. Batch independent calls; keep result-dependent ones
  sequential.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [cost, agent-behavior, performance, tool-calls, cache-reads]
related: [/codex/12-agent-workflow/context-economy.md, /codex/12-agent-workflow/async-wait-and-poll-discipline.md]
created: 2026-08-10
authoritative_for: [tool-call batching rule for every agent surface, collapsible-call and cache-read cost baseline]
referenced_by: []
owner:
last_reviewed:
code_refs: [agent-orchestrator/server/model_pricing.py]
---

# Tool-call batching

> **The rule in one line**: if two tool calls do not depend on each other's results, they belong in ONE call.

## Why this is expensive, not merely untidy

An agent turn does not send "just the new message" — it re-reads the whole cached conversation prefix. So the cost of a
turn is roughly the size of the context, and the cost of a task is roughly `context_size x number_of_turns`. Turn count,
not context size, is therefore the lever you actually control mid-task.

Measured on a controlled 4h25m window (2026-08-10, laptop-only, 3,123 API calls):

| Measure                                              | Value                                    |
| ---------------------------------------------------- | ---------------------------------------- |
| Mean cache-read tokens per API call                  | **405,833**                              |
| Share of total list-priced spend that is cache READ  | **79.7%** (cache writes a further 12.2%) |
| Calls in a consecutive same-tool chain (collapsible) | **57.3%**                                |
| Bash alone                                           | **52.8%** of all calls                   |
| Bash calls that sat inside a chain                   | **69%**                                  |
| Longest observed chains                              | runs of 20, 23, 26, 28, 32               |
| Median gap between consecutive calls                 | **10.5s**                                |
| Aggregate agent-time inside collapsible chains       | **8.6 hours**                            |

Collapsing half of those chains removes roughly **46% of the bill** and, because each collapse also removes a model
round-trip, buys back a comparable share of wall-clock. Same work done, roughly twice the throughput per quota window.

Note what this is NOT: it is not "think less", and it is not a quality trade. Thinking is 68.8% of OUTPUT tokens but
only ~5.5% of cost — output is 8.1% of the bill. Cutting reasoning to save money is the wrong lever by an order of
magnitude. Cutting redundant round-trips is the right one.

## Do this

- **Compound shell.** `cd x && pytest -q && git status` as ONE Bash call, not three. Chain with `&&` when a later step
  should be skipped on failure, `;` when each must run regardless.
- **Multiple `tool_use` blocks in one message** for independent calls — reading four files, grepping three patterns,
  checking two repos' status. These are independent by construction; nothing is learned by spacing them out.
- **`replace_all: true`, or one Write**, instead of a serial run of near-identical Edits on the same file.
- **Never re-read a file you have already read** in this session unless you have edited it since, and never re-read a
  file you just edited to "verify" — Edit and Write fail loudly, so a successful call already IS the verification.
- **Ask for the whole answer at once.** `wc -l a b c` beats three `wc -l` calls;
  `git status && git diff --cached --stat` beats two turns.

## Do NOT batch these

The exception is narrow and real: **a call whose INPUT depends on a previous call's OUTPUT must stay sequential.**
Batching there does not save a round-trip, it just produces a call built on a guess.

- Anything gated on a decision you have not made yet ("if the test fails, then …").
- A destructive or outward-facing action that a preceding check is supposed to authorise. Never bundle the check and the
  irreversible act into one call — the check exists precisely to be read first.
- Steps in a documented runbook whose ordering is the point.

When you are unsure whether a later call depends on an earlier one, ask what you would do differently given each
possible result. If the answer is "nothing", they are independent — batch them.

## Reviewing for this

A role doc, runbook, or skill that walks an agent through a numbered one-command-per-step procedure is actively teaching
the anti-pattern, and undermines this rule wherever it is loaded. Prefer "run these together" phrasing, and reserve
numbered sequential steps for genuinely ordered work.

## A written rule alone already failed once — the hooks that enforce it (2026-08-11 to 2026-08-14)

This doc's own baseline measurement (below) is what a WRITTEN rule alone produced: `SUB_AGENT_MANDATORY_RULES.md`
carried a batching directive from ~2026-08-05, and five days later a controlled re-measurement still found 57.3% of ALL
calls sitting in collapsible chains. Restating the rule a third time was not going to fix it — the fix was moving
enforcement to the moment the behavior happens, not to session-start context competing with everything else:

- **`PostToolUse` nudge** (`cursor-configs/hooks/batching-nudge.py`) — fires in-loop on the 2nd+ consecutive
  round-tripped same-tool call (calls inside one message are correctly distinguished from a real round-trip by latency,
  not tool identity — see that hook's own docstring for why a naive same-tool counter punishes CORRECT batching). Fires
  earlier and harder on repeated same-file `Edit` calls specifically, since a later edit almost never depends on an
  earlier edit's own `tool_result`.
- **`PreToolUse` hard block** (`cursor-configs/hooks/block-same-file-edit-spam.py`, 2026-08-14) — the one case measured
  confident enough to actually DENY rather than nudge: the 5th+ consecutive round-tripped `Edit` call on the SAME file.
  `replace_all: true` and `Write` are always exempt/valid escape hatches, so this can never wedge an agent — it can only
  be escaped WITH the batched fix, never by retrying the identical pattern. Every other tool stays nudge-only; a real
  block needs a much higher false-positive bar than an advisory (see that hook's own module docstring for the full
  reasoning on why Bash/Read/Grep chains are NOT safe to hard-block the same way).
- Measured after both hooks + a lowered nudge threshold: laptop multi-tool-turn% 6.4%→7.6% and AO 6.3%→9.8% within ~2.5h
  of shipping (2026-08-14, small early sample — direction real, magnitude not yet proof of a durable shift). Fleet-wide
  propagation is automatic: both hooks live in the git-tracked, per-slot-symlinked `cursor-configs/hooks/` dir (see
  `/codex/05-infrastructure/claude-code-settings-symlink.md`), and Claude Code watches `settings.json` live — no session
  restart needed to pick up either a logic change or a brand-new hook entry.

## Authoring-time: reduce the calls a task NEEDS, not just how it makes them

Everything above governs the EXECUTING agent's own habits. It says nothing about whether the TASK ITSELF arrived needing
fewer calls in the first place — a vague todo forces an exploratory Grep pass no hook can collapse away, because there
is genuinely nothing to batch yet at the moment the agent starts. Two authoring-time levers, both real gaps found and
fixed 2026-08-14 (`tool_call_batching_authoring_gap_2026_08_14`):

- **Cite the symbol/file, not just the mechanism.** `plans/active/task_template.md`'s existing specificity rules (cite
  symbols not line numbers, state the literal action verb, state a concrete definition-of-done) exist for plan
  durability and dispatch-correctness — but the SAME rules are what let a worker reach its first `Edit`/`Write` call in
  one or two round-trips instead of eight. A todo that names a mechanism but no file/symbol ("move the loader off its
  PATH-PREFIX read") guarantees a Grep before any edit is possible; one that names the exact function/table
  (`_sweep_account`, `deepseek_message_usage`) does not. This mirrors Anthropic's own published guidance on scoping
  agent prompts to one file/scenario and pointing at exact patterns rather than describing a problem in the abstract
  (`code.claude.com/docs/en/best-practices`, "Provide specific context in your prompts").
- **`context_scope` must actually reach the worker, not just the plan file.** `task_template.md` §2a has authors
  pre-compile a reading-list (codex SSOTs, related docs, key paths) at authoring time specifically so a worker doesn't
  re-derive it. Until 2026-08-14 this field was parsed by `/context-scout` and then discarded — never propagated past
  `regen_backlog_from_plan.py` into the actual `/boot` payload a worker receives, so every dispatched task paid for
  context-gathering a plan author had already done for it. Fixed: `context_scope` now threads through
  `BacklogTask`/`TaskBrief`/`to_task_brief` end-to-end (`server/regen_backlog_from_plan.py`'s
  `parse_frontmatter_context_scope`, `server/dispatch.py`'s `to_task_brief`), and `agents/worker.md` now instructs a
  worker to read every `context_scope` entry as part of its normal startup reads, batched — not grep around for context
  already handed to it.
- **Unscoped "investigate X" tasks are a named anti-pattern, not just a style nit** — Anthropic's own Claude Code docs
  name this "the infinite exploration": an unscoped investigation fills context with hundreds of file reads, and the
  documented fix is either narrow the scope or route it through a subagent whose only output is a compiled summary. This
  is the SAME failure mode CLAUDE.md's own dispatch-eligibility rule already targets ("AO-eligible = outcome
  determinable by the worker alone... resolve open-ended judgment calls as a LOCAL plan first") — the gap is
  enforcement, not the rule's existence.

## Baseline for re-measurement

Anyone re-measuring after guidance changes should beat: **3,123 calls, 57.3% collapsible, 405,833 mean cache-read tokens
per call** (2026-08-10). Measure by deduplicating on `requestId` and UNIONING content blocks across every JSONL line
sharing it — keeping only the first line silently drops `tool_use` blocks and will understate tool activity badly (this
exact mistake produced a false "71% of turns are tool-free" reading before it was caught).
