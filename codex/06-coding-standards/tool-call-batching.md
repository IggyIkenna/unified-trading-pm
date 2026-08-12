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

## The trigger is PRE-call, not post-hoc

State the rule as a thing to do **before** a call, or it will not change behaviour:

> **Before any Bash/Read/Grep, ask: _what else will I want to know regardless of how this one comes out?_ Fold that into
> the same call.**

This matters because the earlier phrasing ("batch independent calls") describes an OUTCOME. An outcome-shaped rule is
one you can only grade yourself against after the fact, when the round-trip is already spent and the finding is "noted
for next time" — which never arrives, because the next call has its own new context and the same instinct fires. The
pre-call question has a checkable answer at the only moment the answer is still actionable.

Measured failure of the outcome phrasing (2026-08-11 session): a `PreToolUse` hook printed the batching reminder **~88
times in one session** and was acknowledged nearly every time without the next call changing shape. Acknowledging cost
nothing and looked like compliance; the acknowledgement itself became the green signal with no behaviour behind it. If
you find yourself agreeing with this rule more than once in a session, you are not applying it — treat the second
reminder as evidence, not as a nudge.

The question also has a useful side effect: it surfaces what you actually want to know. "What else, regardless?" tends
to return the check you would otherwise have skipped (the `git status` alongside the `git diff`, the second repo's
state, the file's size before you read it), so the batched call is usually a BETTER-informed call, not merely a cheaper
one.

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

## Baseline for re-measurement

Anyone re-measuring after guidance changes should beat: **3,123 calls, 57.3% collapsible, 405,833 mean cache-read tokens
per call** (2026-08-10). Measure by deduplicating on `requestId` and UNIONING content blocks across every JSONL line
sharing it — keeping only the first line silently drops `tool_use` blocks and will understate tool activity badly (this
exact mistake produced a false "71% of turns are tool-free" reading before it was caught).
