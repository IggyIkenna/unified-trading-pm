---
name: plan-brainstorm
description: >-
  Pre-authoring interrogation gate for a new plan — before drafting any plan doc from an ambiguous ask, restate the
  goal, grep existing plans/issues/codex for what's already decided, then ask 1-2 pointed clarifying questions ONLY on
  the parts that would genuinely change the resulting work (never interrogation for its own sake). Resolves
  `task_template.md`'s "dispatch-scope eligibility" bar and finding S ("scope unclear must stay non-dispatchable until
  the operator names it") BEFORE the doc is written, instead of catching an underscoped todo after the fact via
  `/plan-reconcile` or `/na-eligibility-audit`'s post-hoc audits. Ends by classifying the resolved scope (bounded/
  deterministic -> AO-eligible; still a judgment call -> stays LOCAL) and running the existing "AO plan or human plan?"
  hard-rule question before authoring. Trigger on `/plan-brainstorm`, "help me scope this into a plan", "turn this idea
  into a tracked plan", "I want to build X, help me figure out what the plan should say", "is this ready to be a todo
  yet".
---

# /plan-brainstorm — pre-authoring scope-interrogation gate

**The gap this closes**: `task_template.md`'s dispatch-scope-eligibility rule and finding S already ban an underscoped
todo ("figure out how X should look" wearing a todo's clothes) — but today that bar is enforced _after_ a plan is
written, caught by `/plan-reconcile` or `/na-eligibility-audit` on their next sweep. This skill is the missing
_pre_-authoring step: run it before drafting, not after. It does not replace either audit — a plan that skips this skill
and ships underscoped is still caught by them; this just means fewer should reach that point underscoped in the first
place.

**When to skip this skill**: the ask is already fully scoped (a named repo, a named file/symbol, a stated done-when) —
go straight to `task_template.md` and author. This skill is for the genuinely ambiguous case, not a mandatory gate on
every plan.

## Step 1 — restate the goal

State back, in one or two sentences, what you understood the ask to be — not a repeat of the user's words, a restatement
in your own terms. If restating it is already hard, that itself is a signal the ask is underscoped — proceed to Step 2
expecting real questions, not a formality.

## Step 2 — check what's already decided (grep first, ask second)

Before asking the user anything, grep for it — the same discipline as the pre-task-plan-conflict-check hard rule
(`grep plans/active/` + `.../issues/` first; a hit means read it before assuming anything is still open) and the
doc-retrieval L0→L4 flow (`DOC_INDEX.generated.md`, then `codex/` frontmatter facets). A question whose answer already
exists in a plan, an issue doc, or a codex SSOT is not a clarifying question — it's a research gap on your side. Only
what's genuinely undecided anywhere in the corpus reaches Step 3.

## Step 3 — ask 1-2 pointed questions, never more

Of what's left ambiguous after Step 2, ask **only the questions whose answer would change what gets built or how it's
scoped** — never ask for the sake of thoroughness. Bias hard toward **1-2 questions**, batched together, not a
back-and-forth interview. A question that doesn't change the resulting todo's shape isn't worth asking. Typical
high-value questions:

- Which of two plausible interpretations of the ask is meant (when both are genuinely live, not when one is obviously
  right from context).
- Whether this should be scoped as one bounded change or is actually gesturing at open-ended design work ("figure out
  how the pipeline should look" vs. "add field X to schema Y").
- A concrete constraint the ask didn't state but the answer changes the plan shape (a deadline, a repo boundary, whether
  existing in-flight work should be extended vs. superseded).

Low-value questions to avoid: anything answerable by reading the code/doc corpus yourself; a this-or-that where both
branches produce the same first todo; confirming something the user's own phrasing already made unambiguous.

## Step 4 — classify the resolved scope

Once Steps 1-3 leave a scope you could hand to an isolated worker with a determinable outcome, apply
`task_template.md`'s own bar (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope
eligibility"):

- **Bounded, deterministic outcome** (a checkable fact, a scoped code change, an audit with a stated done-when) →
  eligible for `assigned_vm: planning`. Proceed to the **existing** HARD RULE: ask the operator _"agent-orchestrator
  plan or human plan?"_ before creating it — this skill does not shortcut that question, it just means you now have a
  scope worth asking it about.
- **Still fundamentally a judgment/design call** with no single decided target — even after Steps 1-3 — stays
  `assigned_vm: NA` (LOCAL). Don't force it into AO-shape by picking an arbitrary answer yourself; write the LOCAL plan
  (or a design doc) capturing the resolved-so-far scope and the remaining open question explicitly, per finding S —
  non-dispatchable until named.

## Step 5 — write the plan from the resolved scope, not the Q&A transcript

The plan's "Why this doc exists" section states the resolved goal directly, as if it had been fully scoped from the
start — cite the operator's answers inline where they shaped a concrete decision (a `source:` frontmatter line, same
convention already used across the corpus, e.g. `"operator ask 2026-07-29, interactive session slot 1"`), but don't
narrate the back-and-forth as the doc's content.

## Codex SSOTs

- `plans/active/task_template.md` §4 "Bounded outcome only — no judgment calls in a todo" — the eligibility bar this
  skill resolves scope against
- `plans/active/task_template.md` finding S — the specific failure mode ("SCOPE UNCLEAR" left undispatchable until
  named) this skill exists to prevent upstream of
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `/codex/12-agent-workflow/pre-task-plan-conflict-check.md` — the grep-first discipline Step 2 reuses
- `cursor-configs/skills/plan-reconcile/SKILL.md`, `cursor-configs/skills/na-eligibility-audit/SKILL.md` — the post-hoc
  audits this skill is meant to reduce the workload of, not replace
