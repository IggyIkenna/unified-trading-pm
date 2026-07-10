---
name: plan-reconcile
description:
  Audit the PM plans corpus (plans/active + plans/active/issues + plans/epics + the normative refs PLAN_FORMAT.md /
  task_template.md / INDEX.md / ACTIVE_INDEX.md) for cross-doc contradictions AND done-but-unchecked todos,
  adversarially verify every finding, then reconcile — auto-fix the mechanical classes (checkbox flips with hard
  evidence, supersession banners, status/frontmatter drift, dangling refs) and route judgment calls to the operator as
  an interactive Q&A with options + a marked recommendation; in autonomous/AO mode raise those as AO operator
  alerts/escalations and park them as BLOCKED-OPERATOR-DECISION instead of asking. Plan↔codex drift is in scope and
  plans→codex SSOT updates are applied ONLY after an explicit operator ruling. Trigger on /plan-reconcile, "reconcile
  the plans", "plan contradiction audit", "check the plans for contradictions", "flip done-but-unchecked plan items".
---

# /plan-reconcile — plans corpus contradiction audit + reconciliation

Finds and fixes the two failure classes that rot the plans corpus: (1) **contradictions** — two docs making incompatible
claims about the same decision/status/number/owner/SSOT, epics disagreeing with their child plans, frontmatter
disagreeing with body banners; (2) **false-unchecked** — `- [ ]` todos whose work actually shipped but never got the
same-turn checkbox flip (the #1 false-progress source per CLAUDE.md). Every finding survives adversarial verification
before anyone acts on it.

Runs against `unified-trading-pm/plans/{active,active/issues,epics}` + normative refs. Codex and archive are out of
audit scope but ARE valid evidence when adjudicating (a codex SSOT outranks any plan; `plans/archive/` explains dangling
refs).

## Modes

- **Interactive (default, operator present)**: findings that need a ruling become a structured Q&A (see Phase 4);
  operator decisions are applied immediately.
- **Autonomous / AO-dispatched** (`/plan-reconcile --autonomous`, or run under `/autonomous`, or dispatched to the AO
  VM): NEVER pause for input. Apply only the auto-fix classes; park every judgment call as a `BLOCKED-OPERATOR-DECISION`
  entry in the issue doc (Phase 5) with options + recommendation per the SUB_AGENT_MANDATORY_RULES escalation format,
  and notify the operator. Inherits every safety rule (`cursor-configs/AUTONOMOUS_AGENT_RULES.md` when under
  `/autonomous`).

## Phase 0 — deterministic inventory (cheap, no agents)

Write a throwaway script (scratchpad, NOT the repo; line-based frontmatter parse, no regex backtracking, never
`python3 << EOF`) that walks the corpus and emits:

- per-doc: path, size, `status`, `assigned_vm`, `parent_epic`, `depends_on`, `supersedes`, `superseded_by`, `related`,
  `locked_by`, `title`;
- mechanical flags: dangling `depends_on`/`related`/`supersedes` refs; `superseded_by` set while `status: active`;
  terminal status (`done`/`complete`/`superseded`) still sitting in `plans/active/`; `assigned_vm` outside
  `{planning, NA}` (`human-planning` = legacy alias for `planning`, accepted); `parent_epic` naming a non-existent epic;
  duplicate titles; missing required frontmatter per `plans/PLAN_FORMAT.md`.

Flags are CANDIDATES, not findings — a "dangling" ref often resolves to `plans/archive/` or codex (parser artifact).
Also run the existing hygiene tooling and fold its output in: `run_hygiene_sweep.sh`,
`regenerate_active_plan_inventory.py` (orphan count >0 is review-blocking on its own).

## Phase 1 — multi-agent contradiction sweep

Fan out read-only sub-agents (**max 10 parallel**; paste `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the top of
every spawn — injection failure = that agent MUST NOT proceed; set `model=` explicitly, default sonnet):

1. **Epic-cluster hunters** — partition all docs by `parent_epic` into read batches (~≤300 KB each) so EVERY doc is read
   in full by exactly one hunter. Each hunter reads its batch + the epic hub doc, compares plan↔plan, plan↔epic, and
   frontmatter↔body, and returns (a) contradiction candidates, (b) a per-doc claims digest (≤12 one-line claims with
   line refs). Multi-batch epics get a **reconciler** agent fed all that epic's digests to catch cross-batch pairs
   (grep-then-READ before reporting). Epics themselves get an epic-vs-epic sweep.
2. **Topic hunters** — one per cross-cutting theme (canonical-ID, manifest/coverage, CI/CD shape, agent-orchestrator
   lifecycle, buckets/IAM, VM/SPOT policy, data-completion claims, batch=live, milestones/dates, instruments SSOT,
   sports/prediction, tradfi sourcing, defi providers, plan-format meta, UI/deployment, quality gates — extend as the
   corpus evolves). Grep the corpus for topic signals, READ hits with context, hunt contradictions the epic partition
   structurally can't see.
3. **Mechanical adjudicators** — batches of Phase-0 flags; each reads the flagged doc + ref target and rules real vs
   parser artifact.
4. **Codex-alignment hunters** — for each active plan, read the codex docs its `Codex SSOTs:` section (or inline
   `codex/…` refs) cites and flag plan↔codex drift both ways: the plan contradicting the SSOT (plan is wrong or codex is
   stale) — drift is review-blocking per CLAUDE.md either way. These findings feed the plans→codex update path in
   Phase 5.

Candidate contract (all hunters): both sides cited as `<relpath>:<line>` + verbatim quote ≤200 chars; severity P0 (could
mis-route live work: opposing directives, SSOT conflict, wrong gate/status) / P1 (material drift) / P2 (stale refs,
index drift) / P3 (cosmetic). NOT contradictions: scope/asset-group/time differences; resolved issue docs describing
history; properly-bannered supersession (an UNbannered superseded doc that still reads authoritative IS a finding).

## Phase 2 — done-but-unchecked sweep

For every `- [ ]` todo in ACTIVE (non-draft) plans, hunt evidence the work already shipped. Evidence bar, in descending
strength — flip requires at least one HARD item:

- **HARD**: a pushed commit implementing the item, verified reachable (`git log`/`gh api` on the named repo;
  `git merge-base --is-ancestor <sha> origin/live-defi-rollout` or on main); the named artifact demonstrably live (the
  script/workflow/gate exists at the cited path and does what the todo says — READ it); a Cloud Build / deploy claim
  resolving SUCCESS via `gcloud builds describe` (PLAN_FORMAT § 8b: run it, don't read it); manifest/runtime state
  showing the backfill/migration completed.
- **SOFT (never sufficient alone)**: another doc says it's done; a Progress Log paragraph claims completion; the epic's
  checkbox is ticked. Soft-only evidence = report as a _contradiction_ finding (docs disagree about doneness), do NOT
  flip.

Flip format is the CLAUDE.md HARD RULE: `- [x] … — <repo>@<sha> + <one-line evidence>`, committed with the
`docs(plans):` prefix (**not** `plan(...)` — hook-rejected). Half-done items: flip only the shipped half, annotate the
rest `**DEFERRED**:` with why.

## Phase 3 — adversarial verification (nothing ships unverified)

Dedup candidates by (doc-pair, claim), then for each: an independent **refuter** (assume NOT real; attack via
scope/time/supersession/misquote) and an independent **confirmer** (re-locate both quotes, check which doc is
newer/authoritative via dates + banners + codex). Split votes go to a **tiebreaker**. Only CONFIRMED items proceed;
classify each as `contradiction` / `stale-drift` / `scope-difference` / `format-only`. Checkbox-flip candidates verify
the same way: the refuter attacks the evidence chain (sha actually reachable? artifact actually does the todo?).

## Phase 4 — resolution routing

**Auto-fix (no ruling needed — apply in Phase 5):**

| Class                                                   | Fix                                                                                                                         |
| ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Done-but-unchecked with HARD evidence                   | Flip checkbox with `<repo>@<sha> + evidence`                                                                                |
| Terminal-status doc parked in `plans/active/`           | Run the 5-step archival ritual — but `locked_by:` blocks archival without `[unlock-plan]` (ASK; in autonomous mode park it) |
| Superseded content with no banner                       | Add the `> **SUPERSEDED by <doc> (<date>)**` banner; point to the successor                                                 |
| Frontmatter status contradicting body completion banner | Align frontmatter to reality (verify reality first, both directions possible)                                               |
| Dangling ref where the target moved to archive/codex    | Repoint the ref                                                                                                             |
| Duplicate/stale index rows (INDEX.md / ACTIVE_INDEX.md) | Regenerate via the inventory tooling, never hand-sync                                                                       |

**Operator ruling required (Q&A in interactive mode; park + alert in autonomous mode):** SSOT-ownership disputes; two
ACTIVE docs giving opposing directives; epic vs plan disagreeing about scope or sequencing; conflicting numbers where
neither side has hard evidence; **ANY resolution that edits a codex SSOT doc** (plans→codex updates are in scope for
this skill but NEVER autonomous — the operator rectifies BEFORE any agent touches an SSOT); anything touching a
`locked_by:` plan, kill-switch, funds isolation, or the May-23 critical path. Interactive format — batched questions
ordered P0→P1 hitting the chat box directly; recurring classes get ONE class-level question with per-item exceptions;
every question carries: the two quotes + locations, why they conflict, which doc looks authoritative and why, and
options A/B/C with the recommendation marked (never open-ended — SUB_AGENT_MANDATORY_RULES escalation format). In
autonomous/AO mode the same structured questions are raised as **AO operator alerts/escalations** (orchestrator
dashboard escalation with the options block) so the operator can rule asynchronously; the worker proceeds with
everything else and applies the ruled items on the next pass.

## Phase 5 — apply + commit

- PM-repo doc edits only; stage by name; mandatory pre-commit check `git status && git diff --cached --stat` (no path
  arg); pure doc/plan changes = prek-only (no full QG needed); commit prefix `docs(plans):`; push per the `git-commit`
  skill. Batch related fixes into coherent commits (one commit per class or per plan, not one mega-commit).
- Big findings (data-correctness, May-23 critical path, cross-repo, SSOT contradiction) additionally follow the triage
  HARD RULE: **notify the operator + file `plans/active/issues/<slug>_<YYYY_MM_DD>.md`**. In autonomous mode the issue
  doc also carries every parked `BLOCKED-OPERATOR-DECISION` with its options block.
- **Plans→codex updates are part of this skill** — when the operator's ruling says the codex SSOT is the stale side,
  apply the codex edit (update the contract, stub the new pattern, or SUPERSEDED-banner the invalidated doc, per the
  post-phase codex-audit ritual) and condense the matching CLAUDE.md one-liner if it carries the stale claim. HARD GATE:
  a codex/SSOT edit is only ever applied AFTER an explicit operator ruling on that specific finding (chat answer or AO
  escalation response) — never from the agent's own judgment, however confident the evidence.
- NEVER write agent memory; NEVER create `*_SUMMARY.md` — the final report is chat text.

## Phase 6 — report

Finish with text: counts by severity/class, the applied-fix list (commit shas), the operator-decision list (or parked
issue doc path), refuted-candidate count, and coverage (docs read / batches / topics swept). Recommend a re-run cadence
(post-major-phase or weekly) until the confirmed-findings count trends to zero.

## AO-VM handoff (target end-state)

This skill is written to be dispatchable: author a wrapper plan (ASK the operator first — plan-destination HARD RULE;
`assigned_vm: planning`, `assigned_role` per the role registry, `execution_scope` PM-repo-only) whose todos invoke
`/plan-reconcile --autonomous` on a cadence. The autonomous contract above (no pauses, auto-fix only, park rulings,
notify on big findings) is exactly the non-interactive behaviour the AO worker needs. Until that plan exists, the skill
stays operator-triggered.

## Codex SSOTs

- `codex/12-agent-workflow/commit-push-flip-rule.md` — flip cadence + format
- `codex/11-project-management/doc-frontmatter-schema.md` + `plans/PLAN_FORMAT.md` — frontmatter truth
- `codex/11-project-management/` — findings triage, archival ritual, issue-doc lifecycle
- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — assigned_vm/role semantics
- `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — sub-agent spawn contract + escalation format
