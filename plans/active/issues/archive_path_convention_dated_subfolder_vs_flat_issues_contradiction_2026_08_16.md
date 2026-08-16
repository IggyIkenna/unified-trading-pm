---
doc_type: issue
title: >-
  Two SSOTs disagree on the archived-issue-doc path — `plans/archive/<YYYY_MM>/issues/` (archival-discipline SSOT,
  used pervasively incl. within this same session) vs. `plans/archive/issues/` flat, no dated subfolder
  (issue-doc-lifecycle SSOT, explicit and unambiguous) — and the archival-discipline doc even cites BOTH forms itself
summary: >-
  Discovered live during routine doc-shipping work: `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`
  states the 6-step ritual moves a doc to `plans/archive/<YYYY_MM>/` (lines 67, 134, 196, 235, 242) but its OWN example
  citations elsewhere in the same file use the flat form `plans/archive/issues/<slug>.md` (lines 82, 108) — internally
  inconsistent. Separately, `/codex/11-project-management/issue-doc-lifecycle.md` is explicit and unambiguous: every
  terminal disposition (ACKED-INTO-PLAN/CODE/OUT-OF-SCOPE/AS-INVALID) archives an issue doc to flat
  `plans/archive/issues/` — no dated subfolder, ever, for issue-type docs. Live corpus evidence of both forms
  co-existing at scale: `plans/archive/2026_08/issues/` currently holds many docs (dated form, matches the
  archival-discipline SSOT's majority wording and is what this same session used for several retags), while at least
  one doc was independently archived this same session to flat `plans/archive/issues/` citing issue-doc-lifecycle.md
  explicitly as the authority. Neither actor was wrong per the SSOT they read — the SSOTs themselves disagree.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, archival, ssot-contradiction, doc-frontmatter-schema, issue-doc-lifecycle]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/issue-doc-lifecycle.md,
  ]
created: 2026-08-16
last_updated: "2026-08-16"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: infra
source: >-
  slot-16 (infra), discovered mid-task while archiving 3 different issue docs across a single 2026-08-16 session and
  noticing they landed under two different path shapes depending on which SSOT the actor happened to read.
author: slot-16
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/issue-doc-lifecycle.md,
  ]
---

# Archive path convention: dated-subfolder vs. flat `plans/archive/issues/` — two SSOTs disagree

## What was found (live, 2026-08-16)

Across one session, three separate archival actions (mine + two concurrent peers') landed issue docs at two different
path shapes:

- `plans/archive/2026_08/issues/<slug>.md` — the dated-subfolder form, matching
  `plan-completion-and-archival-discipline.md`'s majority wording ("the doc should now live under
  `plans/archive/<YYYY_MM>/`").
- `plans/archive/issues/<slug>.md` — the flat form, matching `issue-doc-lifecycle.md`'s EXPLICIT, unambiguous table
  (every terminal disposition → `plans/archive/issues/`, no dated component, stated 4 separate times in one table).

`plan-completion-and-archival-discipline.md` itself is internally inconsistent — it states the dated-subfolder rule as
the general ritual step, but its own worked examples (lines 82, 108) cite the FLAT form for issue docs specifically.
This reads like the flat form is the intended convention for `doc_type: issue` specifically (matching
issue-doc-lifecycle.md, the more specific/authoritative SSOT for issue docs), while the dated-subfolder form is
intended for `doc_type: plan`/general plan archival — but neither doc states this split explicitly, so every actor is
left to guess, and the live corpus now has both forms mixed at scale under `plans/archive/*/issues/` AND
`plans/archive/issues/`.

## Why it matters

Not a correctness bug (both paths are valid git locations, nothing is lost), but: (1) referrer-fixup tooling and
`check_reference_paths.py`-style greps that assume one shape will miss the other, (2) a future archival actor has no
way to know which is "right" without reading both SSOTs and noticing the conflict themselves (as this doc's author just
did), and (3) it's the kind of small inconsistency that compounds — every future archival either perpetuates the split
or requires re-deriving this exact investigation.

## Recommended decision

Either (a) `issue-doc-lifecycle.md`'s flat `plans/archive/issues/` is correct for `doc_type: issue` and
`plan-completion-and-archival-discipline.md`'s dated-subfolder wording should be scoped explicitly to `doc_type: plan`
only (with its own inconsistent lines 82/108 fixed to stop contradicting itself), or (b) the dated-subfolder form should
become canonical for both and issue-doc-lifecycle.md's table gets a one-line update. This is a naming/consistency call,
not a data-correctness one — low urgency, but worth resolving before the corpus split grows further.

## Todos

- [ ] [DOCS] P3. **Resolve which archive path convention is canonical for `doc_type: issue`** — read both SSOTs in
      full, pick one (recommend flat `plans/archive/issues/`, since issue-doc-lifecycle.md is the more specific,
      internally-consistent SSOT for this doc type), and fix the losing SSOT's wording (including
      `plan-completion-and-archival-discipline.md`'s own internal self-contradiction between its ritual-step wording
      and its own worked examples). **Done when**: both SSOTs agree, and the choice is stated explicitly (not left
      implicit via "the ritual says X but the examples say Y").
- [ ] [SCRIPT] P3. **Measure the live corpus split** — count how many issue docs currently sit under
      `plans/archive/*/issues/` (dated) vs. `plans/archive/issues/` (flat), and decide whether a one-time normalization
      pass (moving the minority form to match the winning convention from the todo above) is worth the referrer-fixup
      cost, or whether grandfathering existing docs in place (only enforcing the winning convention going forward) is
      the pragmatic call given `plans/archive/**` is explicitly outside the gated corpus per
      `doc-frontmatter-schema.md` §1 ("archives are closed records, never ship-blocking"). **Done when**: a count is
      reported and a normalize-vs-grandfather decision is recorded with rationale.

## Progress Log

- **2026-08-16 (slot-16, infra)** — filed. Discovered while completing a chain of concurrent-edit reconciliations
  across 3 issue docs in one session; not itself blocking any of that work, filed as a clean follow-up rather than
  resolved inline (a fleet-wide SSOT wording fix is outside this session's task scope per `infra.md`'s "file an issue
  doc + escalate — do not absorb unplanned scope").
