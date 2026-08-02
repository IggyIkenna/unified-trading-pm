---
name: context-scout
description: >-
  Maintain the `context_scope` frontmatter field (an elective free_list on `plan` and `issue` docs,
  `scripts/docs/docspec.py`) — a minimal reading-list of codex SSOTs, related plan/issue docs, and key source paths a
  worker should read before touching that doc, computed per-doc rather than left for every worker to re-derive via a
  fresh cold grep. Follows the MVI (Minimal Viable Information) principle — a short, curated list a worker can read in
  full, not an exhaustive index. Runs incrementally (skip docs already scouted and unchanged since) via
  `scripts/plan-hygiene/generate_context_scope_inventory.py`, so a daily re-run is cheap once the corpus is caught up.
  Trigger on `/context-scout`, "backfill context_scope", "populate the reading list for this plan", "what should I read
  before working on `<doc>`", "is context_scope stale".
---

# /context-scout — context_scope frontmatter maintenance

Maintains a DIFFERENT axis of every plan/issue doc than the other daily plan-health skills: not
status/orphan-coverage/NA-eligibility, but **what should a worker read first**. `/plan-reconcile`, `/ag-closeout-audit`,
and `/na-eligibility-audit` all judge a doc's own correctness; this skill never touches a doc's `status`, todos, or body
content beyond adding a dated marker — it only reads a doc and writes back a `context_scope:` list.

**Out of scope**: judging whether a doc's status/todos are still correct (that's
`/plan-reconcile`/`/na-eligibility-audit`), orphan detection (`/ag-closeout-audit`), or codex-doc health
(`/docs-reconcile`). A doc this skill scouts may separately need one of those audits — this skill doesn't run them and
doesn't defer to them; it's a disjoint concern.

## Why a minimal list, not an exhaustive one

The point is to cut a worker's cold-start context burn, not maximize recall. A `context_scope` with 15 entries is no
better than none — nobody reads 15 files before starting. Target **2-6 entries per doc**: the codex SSOT(s) the doc's
own subject matter depends on, any plan/issue this doc supersedes or is gated on (when not already obvious from
`depends_on`/`supersedes`), and — only when the doc's work is clearly anchored to specific code — 1-3 source paths
(directories or well-known filenames, never line numbers, same citation discipline as `task_template.md` §3).

## Phase 0 — inventory (cheap, no agents)

Run `python3 scripts/plan-hygiene/generate_context_scope_inventory.py --json`. Reuses `scripts/docs/docspec.py`'s PyYAML
frontmatter parser — do not re-derive frontmatter parsing with a line-grep (that bug class — a multi-line YAML value or
a non-standard checkbox bullet silently missed — has recurred twice already in this repo's other inventory scripts). Per
doc, the script verdicts:

- **NEVER_SCOUTED** — no `context_scope` field, or present but empty.
- **STALE** — has `context_scope`, but no dated `context-scout YYYY-MM-DD` Progress Log marker at or after the doc's
  last-touched date (frontmatter `last_updated`, falling back to the file's git last-commit date).
- **UP_TO_DATE** — marker date already covers the doc's last-touched date. Skip.

Report the split up front (total in-scope docs, never-scouted, stale, up-to-date-skipped). **The first-ever run will
show hundreds of NEVER_SCOUTED docs — expect it to look like a real backfill (many sub-agent batches), not a quick daily
pass.** Every subsequent run should be small (only docs created or edited since yesterday), which is the entire point of
the incremental design — if a run ever looks like a full re-scan again, something is wrong with the marker/date logic;
report that plainly rather than silently paying the full cost every day.

## Phase 1 — per-doc scouting (the real work)

Batch the in-scope docs (NEVER_SCOUTED + STALE) into groups of ~10-15 and fan out read-only sub-agents via a `Workflow`
`pipeline()` (max 10 concurrent per this workspace's sub-agent cap; paste `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
at the top of every spawn; set `model=` explicitly — sonnet is enough for this, no architecture/trading judgment
involved). Each hunter, per doc:

1. Reads the doc's frontmatter (`related`, `depends_on`, `supersedes`, `parent_epic`) and body (Why section, todos, any
   `Codex SSOTs:` list already present).
2. Extracts every codex/plan/issue path the doc's OWN text already cites — these are free, no judgment required, just
   collection.
3. Judges whether the doc's substance implies an unstated codex SSOT it should but doesn't cite (e.g. a doc doing a GCS
   delete that never mentions the delete-safety protocol). **Never guess a plausible-sounding codex path** —
   grep-then-READ the candidate (per this workspace's grep-then-conclude ban) and confirm the doc actually exists and
   actually covers the claim before adding it. An unconfirmed guess becomes a Phase 5 suggestion, not a written
   `context_scope` entry.
4. Adds 1-3 source paths only when the doc's work is clearly anchored to specific code — a directory or a well-known
   module name a worker would `grep` for, never a line number (a plan outlives the code it points at; see
   `task_template.md` §3's identical rule for todos).
5. Verifies every proposed entry actually resolves — `/codex/...` and `/plans/...` paths must exist on disk, source
   paths must exist in the named repo — before returning. A dead pointer in a reading-list field is worse than an absent
   field; drop anything that doesn't resolve and note it was dropped.
6. Returns a **minimal** ordered list (2-6 entries) — resist padding; if a doc genuinely only needs one codex doc, write
   one.

## Phase 2 — apply

- Write `context_scope: [...]` into the doc's frontmatter (YAML flow-list, matching the existing style already used in
  the corpus, e.g. `ao_slot_capacity_policy_ci_scheduled_split_2026_07_29.md`). This is the ONLY frontmatter field this
  skill ever writes.
- Append a dated Progress Log marker: `**context-scout YYYY-MM-DD**: populated/refreshed context_scope (<n> entries)` —
  this is Phase 0's incremental-skip anchor for every future run. Never skip writing this, even when the computed list
  is short.
- Stage by name, mandatory pre-commit `git status && git diff --cached --stat` (no path arg), commit prefix
  `docs(plans):`, ship per CLAUDE.md's git-discipline section (`quickmerge.sh --agent --files`). Batch by cohort (e.g.
  one commit per ~50 docs), not one mega-commit and not one commit per doc.
- A Phase-1 "unstated SSOT" suggestion that could NOT be confirmed does not get written anywhere in the doc — carry it
  into the Phase 3 report only, so a human can judge it without the doc itself making an unverified claim.

## Phase 3 — report

Finish with text: total docs scouted this run (never-scouted vs stale), total skipped (up-to-date), entries written (avg
per doc), any doc where Phase 1 found ZERO confirmable entries (report these — a doc with genuinely no reading-list is
fine, but worth surfacing so a human can sanity-check it isn't a scouting failure), and every unconfirmed "unstated
SSOT" suggestion surfaced in Phase 1 step 3. Like `docs_reconciler`/`ag_closeout_auditor`/`na_eligibility_auditor`, this
is chat-text only — there is no separate structured-findings endpoint. NEVER write agent memory; NEVER create a
`*_SUMMARY.md` file.

## Modes

**Interactive** (operator present, or invoked directly against one doc — `/context-scout <path>`): scout that one doc
synchronously, no Workflow fan-out needed for a single doc. **Autonomous (scheduled)**: the `all` default — Phase 0
across the whole corpus, Phase 1 fan-out, Phase 2 apply, Phase 3 report, never pausing; a doc whose Phase-1 judgment is
genuinely ambiguous (step 3's unconfirmed-SSOT case) is reported, never guessed.

## Scheduled cadence

Fires hourly via `context-scout.timer` on the central orchestrator VM
(`agent-orchestrator/scripts/install-context-scout-timer.sh`, staggered to :52 past the hour, after `plan-reconciler`
(:00), `docs-reconciler` (:15), `ag-closeout-auditor` (:30), and `na-eligibility-auditor` (:45) — so this run's Phase 0
sees that hour's other corpus fixes/retags first); the dispatch wrapper itself gates to at-most-once-per-day and only
retries the remaining hours in the day if an earlier attempt 503'd on capacity — same retry-until-capacity design as the
sibling timers. Still directly invocable interactively any time, against the whole corpus or a single doc path.

## Codex SSOTs

- `/codex/11-project-management/doc-frontmatter-schema.md` — `context_scope` field definition (elective, `plan`/`issue`
  doc types)
- `plans/active/task_template.md` §3 — symbol-not-line-number citation discipline (same rule this skill's Phase 1 step 4
  follows)
- `cursor-configs/skills/na-eligibility-audit/SKILL.md`, `cursor-configs/skills/docs-reconcile/SKILL.md` — sibling
  scheduled plan-health skills (disjoint concerns, same dispatch/report shape)
- `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — sub-agent spawn contract
