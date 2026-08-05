---
doc_type: codex-ssot
title: Context Economy — Scoped Reads + Terse Responses
summary:
  SSOT for the rule that every agent working a task (not just plan-authoring agents) must scope tool-output reads
  narrowly (grep with context lines instead of whole-file reads when hunting one thing; targeted greps instead of broad
  corpus sweeps once a candidate is known) and default to plain, short prose in chat responses (no
  headers/bold/bullet-tree formatting for routine summaries, no restating evidence already visible in a diff/tool
  result). Applies to ANY task an agent runs, independent of whether it also involves plan authoring.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [context-economy, agent-behavior, token-cost, terseness, tool-usage]
related:
  [
    /codex/12-agent-workflow/pre-task-plan-conflict-check.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /plans/active/task_template.md,
  ]
created: 2026-08-03
authoritative_for: [tool-output read scoping, chat-response terseness default]
referenced_by: [CLAUDE.md § "Agent behavior"]
owner:
last_reviewed:
code_refs:
---

# Context Economy — Scoped Reads + Terse Responses

> Operator finding 2026-08-03: a single interactive investigation task (root-causing an odds-api quota exhaustion — not
> a plan-authoring session) burned ~228k context tokens. Root-caused into three buckets, only two of which are
> agent-controllable this doc addresses; the third (per-repo `CLAUDE.md` re-injected via `<system-reminder>` on every
> new directory touched, ~10-15k tokens each, identical content repeated per repo) is a harness mechanic, not fixable
> from inside a task — out of scope here.

## The rule

**Every agent working ANY task** — investigation, bug fix, audit, one-off question, not only plan-authoring or
AO-dispatched work — follows both halves below. Neither is plan-specific; both apply regardless of whether the task ever
touches a plan doc.

### 1. Scope tool-output reads narrowly

- **Grep with context, don't read the whole file, when hunting for one thing.** If the question is "does this file have
  a runaway retry loop" or "what does this function do," use `grep -n -A10 -B2 <pattern>` (or the `Grep` tool's
  context-line options) around the relevant symbol first. Only fall back to a full `Read` when the file is genuinely
  short, or when you've confirmed via grep that most of the file is relevant (e.g. reviewing an entire small module
  end-to-end for correctness).
- **Narrow a corpus grep before reading its hits.** A 40-60-file grep result is a candidate list, not a reading list —
  grep again with a tighter pattern (dates, exact identifiers, distinctive evidence strings — see
  `cursor-configs/skills/context-scout/SKILL.md` Phase 1 step 4a for the fingerprint-matching technique) to cut the
  candidate set BEFORE opening any of them in full.
- **Read a large doc in the smallest slice that answers the question**, not top-to-bottom. Use `offset`/`limit` (or
  `Grep` to find the right section first) rather than paging through a 600+-line doc in sequential chunks when only one
  section (e.g. the most recent Progress Log entries) is relevant.
- **This is a judgment call, not a hard cap** — a genuine full-file review (code review, adversarial audit, "read this
  doc end to end before touching it") legitimately needs the whole file. The failure mode this rule targets is reading
  whole files as the DEFAULT move when a scoped read would have answered the same question.
- **The same discipline applies to Bash/tool COMMAND OUTPUT, not just file reads.** `tail -60`/`cat` on a VM run.log, a
  quickmerge log, or a `tofu plan` — dumping the whole thing into context by default is the same failure mode as an
  unscoped file Read. Default to `grep -c`/`grep -n -A5` for an existence/count/exit-code check; use a small
  `tail -5`/`head -5` window to confirm a step finished; only pull a larger excerpt once something looks wrong and the
  detail is actually needed to diagnose it. Operator finding 2026-08-05: a session running several VM launches +
  quickmerge ships in one turn repeatedly dumped 30-60-line log tails and full `cat`s of run logs when a `grep -c`
  existence check or a 5-line tail would have answered the same question.

### 2. Default chat responses to plain, short prose

- **No headers/bold-heavy/bullet-tree formatting for routine summaries or progress updates.** Reserve structure
  (headers, tables, numbered lists) for cases that actually need it — comparing options, a multi-part answer the user
  will scan rather than read linearly, a final report the user will reference later. A one-paragraph status update does
  not need a header.
- **Don't restate information already visible in a diff, tool result, or file the user can see.** If a `git diff` or
  file edit already shows what changed, the chat response says what it means / what's next, not a re-narration of the
  diff's contents.
- **Match response length to the question.** A yes/no or single-fact question gets a sentence, not a structured writeup.
  This mirrors the general Claude Code system guidance ("responses should be short and concise," "match responses to the
  task") — this doc exists because that default was being violated in practice on this workspace's tasks specifically,
  not because the rule itself is new.

## What this doc does NOT cover

- The per-repo `CLAUDE.md` re-injection cost (harness-level `<system-reminder>` behavior triggered by touching a new
  repo directory) — not agent-controllable from inside a task.
- `context_scope` frontmatter / reading-list curation for plan and issue docs — that's
  `cursor-configs/skills/context-scout/SKILL.md` and `/plans/active/task_template.md` §2a (a different, complementary
  mechanism: pre-computing what a FUTURE worker should read, vs. this doc's concern of how the CURRENT worker reads and
  responds).
- Model/effort tier selection — `/codex/06-coding-standards/model-tier-selection.md`.

## Codex SSOTs

`/codex/12-agent-workflow/pre-task-plan-conflict-check.md` (the other "applies at task start, not just to plan
authoring" precedent this doc follows the same pattern as), `cursor-configs/skills/context-scout/SKILL.md`.
