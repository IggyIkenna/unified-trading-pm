---
name: plan-reconcile
description:
  Audit the PM plans corpus (plans/active + plans/active/issues + plans/epics + the normative refs PLAN_FORMAT.md /
  task_template.md / INDEX.md / ACTIVE_INDEX.md) for cross-doc contradictions AND done-but-unchecked todos,
  adversarially verify every finding, then reconcile — auto-fix the mechanical classes (checkbox flips with hard
  evidence, supersession banners, status/frontmatter drift, dangling refs) AND anything a source of truth can settle
  (if a claim is countable, count it — do not escalate a provable fact), then route only genuine authority/preference
  calls to the operator as a batched interactive Q&A with options + a marked recommendation. ASK > PARK: park as
  BLOCKED-OPERATOR-DECISION only when nobody is reachable to answer. Also runs a lifecycle + hygiene pass:
  archive fully-done plans (verified, unlocked), flag near-complete plans (<=1 open todo) for consolidation, and leave
  the corpus canonical (prettier + run_hygiene_sweep.sh-green, within line-caps). Plan↔codex drift is in scope and
  plans→codex SSOT updates are applied ONLY after an explicit operator ruling. Trigger on /plan-reconcile, "reconcile
  the plans", "plan contradiction audit", "check the plans for contradictions", "flip done-but-unchecked plan items",
  "archive done plans", "consolidate near-empty plans".
---

# /plan-reconcile — plans corpus contradiction audit + reconciliation

Finds and fixes the two failure classes that rot the plans corpus: (1) **contradictions** — two docs making incompatible
claims about the same decision/status/number/owner/SSOT, epics disagreeing with their child plans, frontmatter
disagreeing with body banners; (2) **false-unchecked** — `- [ ]` todos whose work actually shipped but never got the
same-turn checkbox flip (the #1 false-progress source per CLAUDE.md). Every finding survives adversarial verification
before anyone acts on it. It also runs a **lifecycle + hygiene pass**: archive fully-done plans (all todos verified
`[x]`, unlocked), flag near-complete plans (≤1 open todo) for consolidation into a sibling/epic, and leave the corpus in
canonical format — prettier-clean, `run_hygiene_sweep.sh`-green, within the line-caps.

Runs against `unified-trading-pm/plans/{active,active/issues,epics}` + normative refs. Codex and archive are out of
audit scope but ARE valid evidence when adjudicating (a codex SSOT outranks any plan; `plans/archive/` explains dangling
refs).

## Modes

- **Interactive (default, operator present)**: findings that need a ruling become a structured Q&A (see Phase 4);
  operator decisions are applied immediately.
- **Autonomous / AO-dispatched** (`/plan-reconcile --autonomous`, or dispatched to the AO VM with no operator on the
  other end): NEVER pause for input. Apply the auto-fix classes; park every genuine judgment call as a
  `BLOCKED-OPERATOR-DECISION` entry in the issue doc (Phase 5) with options + recommendation per the
  SUB_AGENT_MANDATORY_RULES escalation format, and notify the operator. Inherits every safety rule
  (`cursor-configs/AUTONOMOUS_AGENT_RULES.md` when under `/autonomous`).

### ASK > PARK when the operator is reachable (HARD — added 2026-07-15 from a real failure)

**Parking is for an operator who is genuinely gone, not for a mode flag.** `/autonomous` means "don't BLOCK on them",
not "never speak to them". If the operator is in the session — and especially the moment they reply to anything —
**switch to interactive and ASK the batched Q&A** (Phase 4). Re-evaluate this every turn; the mode is a property of
_operator reachability_, not of how the run was invoked.

_(The failure: a run under `/autonomous` parked 8 decisions into an issue doc while the operator was actively replying
in-session. They then answered all of them in two rounds, in minutes. The park cost a full round-trip AND is what let
findings hide — a doc someone must go read is where a missed item survives; a question they answer is not.)_

**Parking is strictly worse than asking** — it defers the work, and it hides misses (see Phase 5.9(a)). Park only when
nobody is there to answer.

### Calibration: 9/9 [WORKER REC] ratified — the bar for "needs a ruling" is EVIDENCE, not vibes

On 2026-07-15 the operator ratified the marked `[WORKER REC]` on **9 of 9** escalations (3 async + 6 interactive), with
zero overrides. Read that correctly — it does NOT mean "auto-apply everything you'd recommend". It means the routing
test was wrong. **The test is not "does this feel like a judgment call?" — it is:**

> **Can the evidence make exactly one answer provably right?** If YES → resolve it, cite the proof, report it. If NO →
> ask (interactive) / park (nobody home).

**AUTO-RESOLVE (do not ask) when the answer is provable from code / git / filesystem / AST:**

- a factual number, name or status contradicted by the source of truth — _e.g. "is the ledger EventType set 37 or 39?"
  is `ast.parse` + `len(members)`. That was escalated; it should have been a one-command fix. If a claim is countable,
  COUNT IT._
- a ref whose target provably moved (the file is at the new path — `os.path.exists` says so)
- a stale date/banner contradicted by a newer dated banner in the same doc
- a checkbox whose commit is reachable on `origin/live-defi-rollout` (the existing HARD-evidence bar)
- Guardrail: "provable" means you RAN the check this turn and can paste the output. A confident inference is not a
  proof.

**STILL ASK / PARK — these are not correctness, they are authority or preference, and evidence cannot settle them:**

- **Blast radius**: any edit to a normative/SSOT doc (`codex/**`, `CLAUDE.md`) — the gate exists because the change
  reaches every agent, NOT because the evidence is weak. Strong evidence does not buy the authority.
- **An explicit human signal**: `locked_by:` is a person saying "not yours" — `[unlock-plan]` is theirs to give.
- **Preference with no ground truth**: where live work LIVES (fold targets), how to split a plan, priority tiering.
  Multiple answers are defensible; the operator's model of the roadmap decides.
- **Standing hard-stops**: funds isolation, kill-switch, wallet keys, `1.0.0`, the May-23 critical path.

**Batching (this worked — keep it):** ≤4 questions per round, ordered P0→P1, each carrying both quotes + locations, why
they conflict, which side is authoritative and why, and options with the recommendation marked FIRST. Recurring classes
get ONE class-level question with per-item exceptions (the 16-row fold table was approved as a single question).

## Phase 0 — deterministic inventory (cheap, no agents)

Write a throwaway script (scratchpad, NOT the repo; line-based frontmatter parse, no regex backtracking, never
`python3 << EOF`) that walks the corpus and emits:

- per-doc: path, size, `status`, `assigned_vm`, `parent_epic`, `depends_on`, `supersedes`, `superseded_by`, `related`,
  `locked_by`, `title`;
- mechanical flags: dangling `depends_on`/`related`/`supersedes` refs; **`depends_on` CYCLES** (A→B→A) and
  self-dependency (A→A) — a cycle gates archival forever, so neither plan can ever close (walk the live subgraph; a
  `depends_on` pointing at an ARCHIVED plan is NOT a finding — it means the prerequisite is done and the dependent is
  unblocked); **git conflict markers** (`<<<<<<<`/`=======`/`>>>>>>>`) left in a doc; `superseded_by` set while
  `status: active`; terminal status (`done`/`complete`/`superseded`) still sitting in `plans/active/`; **all todos `[x]`
  while `status: active`** (fully-done → archival candidate); **≤1 open todo remaining** (near-complete → consolidation
  candidate); **body over the line-cap** — normal plans 500 soft / 1000 hard (per `run_hygiene_sweep.sh`), but
  **long-lived master plans + epics (`plans/epics/*.md`, `*_master*`, living-inventory/hub plans) are EXEMPT from the
  500/1000 caps** (they are intentionally long), with a **strict 5000-line ABSOLUTE ceiling on ANY file regardless of
  type** (over 5000 = split finding, no exemption); `assigned_vm` outside `{planning, NA}` (`human-planning` = legacy
  alias for `planning`, accepted); `parent_epic` naming a non-existent epic; duplicate titles; missing required
  frontmatter per `plans/PLAN_FORMAT.md`. Emit per-doc **open/done checkbox counts** so the fully-done + near-complete
  candidates are computed deterministically (they are candidates, still verified in Phase 2/3 before any archival).

Flags are CANDIDATES, not findings — a "dangling" ref often resolves to `plans/archive/` or codex (parser artifact).

**`run_hygiene_sweep.sh` is a first-class STEP of this skill, and it BOOKENDS the run — not a footnote:**

- **Phase 0 (entry, read-only):** `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` — `--no-regen` exists
  precisely for this read-only input-gather (it avoids dirtying `master_to_live_defi_…`). Fold its output into the
  candidate set and **do not re-implement what it already checks**: frontmatter validity + schema, todo format,
  todo-regression vs origin, runbook fields, **conflict markers**, prettier-mangling, **the `depends_on` DAG (cycles +
  self-deps)**, line caps, estimate sanity, superseded-in-active, codex path refs, parent-epic alignment,
  CLAUDE↔SUB_AGENT parity. A RED hard check here is a finding in its own right, before any agent runs.
- **Phase 5 (exit, HARD green-gate):** re-run it **with** regen (`--ci`) and require **0 hard failures** + `0 orphans`
  before the run may be called done (see Phase 5).

It is the same gate the fleet already enforces (prek pre-commit via `--precommit`, CI `plan-health-agent.yml`, and the
daily cron) — so a deterministic corpus-wide check belongs THERE, not in this skill's prose, where it then runs on every
commit rather than only when someone happens to reconcile. `regenerate_active_plan_inventory.py` runs at Phase 5 (orphan
count >0 is review-blocking on its own).

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

Sweep **every checkbox surface in the audit corpus**, not just active plans — the false-unchecked class hides in issue
docs and epics too. For every `- [ ]` in each of the three surfaces, hunt evidence the work already shipped:

1. **ACTIVE (non-draft) plans** — `plans/active/*.md` todos (the primary surface).
2. **Issue docs** — `plans/active/issues/*.md` action items / remediation checkboxes (an issue whose fix demonstrably
   shipped but whose `- [ ]` never flipped, or whose resolution warrants closing the doc).
3. **Epic checkboxes** — `plans/epics/*.md` items that reference a child plan/milestone: flip when that child is
   verifiably done (all its todos flipped, or it's archived). A ticked epic box over an unfinished child is the inverse
   contradiction (route to Phase 1), not a flip.

(`status: draft` plans are excluded — WIP, not yet dispatched.) The same HARD-evidence bar below applies to all three
surfaces; evidence in descending strength — a flip requires at least one HARD item:

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

| Class                                                          | Fix                                                                                                                                                                                                              |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Done-but-unchecked with HARD evidence                          | Flip checkbox with `<repo>@<sha> + evidence`                                                                                                                                                                     |
| Terminal-status doc parked in `plans/active/`                  | Run the 5-step archival ritual — but `locked_by:` blocks archival without `[unlock-plan]` (ASK; in autonomous mode park it)                                                                                      |
| Fully-done plan (every todo `[x]`, `status: active`, UNLOCKED) | Verify each todo genuinely done via Phase-2 HARD evidence (a plan can be false-checked), then run the 5-step archival ritual. Any todo only soft-supported, or `locked_by:` set → park, never autonomous-archive |
| Superseded content with no banner                              | Add the `> **SUPERSEDED by <doc> (<date>)**` banner; point to the successor                                                                                                                                      |
| Frontmatter status contradicting body completion banner        | Align frontmatter to reality (verify reality first, both directions possible)                                                                                                                                    |
| Dangling ref where the target moved to archive/codex           | Repoint the ref                                                                                                                                                                                                  |
| Duplicate/stale index rows (INDEX.md / ACTIVE_INDEX.md)        | Regenerate via the inventory tooling, never hand-sync                                                                                                                                                            |

**Completion + consolidation lifecycle (verify-then-archive; destination is operator-gated):**

- **Fully-done plan** (every todo `[x]`) — confirm each is genuinely done via the Phase-2 HARD-evidence bar (soft-only =
  contradiction finding, not an archive), then: UNLOCKED → archive via the 5-step ritual (auto-fix above); `locked_by:`
  set or any todo soft-only → park as `BLOCKED-OPERATOR-DECISION`. Never autonomous-archive a locked plan.
- **Near-complete plan** (≤1 open todo, or a remnant too small to justify a standalone plan) — the remnant should be
  **folded into a sibling plan under the same `parent_epic`** (or the epic hub) and the shell archived. But WHERE live
  work lives is a planning decision: interactive → ask with a recommended fold-target; autonomous/AO → **park with the
  specific recommended target named**, never auto-fold (moving live todos between plans without a ruling is
  review-blocking). Once the remnant is folded by ruling, the emptied shell archives as a fully-done plan.

| Claim provably wrong vs the source of truth | **AUTO-RESOLVE — do not escalate.** If a number/name/status is countable
or checkable (AST, `git cat-file`, `os.path.exists`, a newer dated banner in the same doc), RUN the check and fix it,
citing the command + output as evidence. Prefer deleting a derivable restated fact over correcting it — a hardcoded
count re-stales on the next bump. See Modes § "Calibration" |

**Operator ruling required (Q&A in interactive mode; park + alert ONLY if nobody is reachable — see Modes § ASK >
PARK):** SSOT-ownership disputes; two ACTIVE docs giving opposing directives; epic vs plan disagreeing about scope or
sequencing; conflicting numbers **that no source of truth can settle** (if one side is checkable, it is NOT a ruling —
go check it); neither side has hard evidence; **ANY resolution that edits a codex SSOT doc** (plans→codex updates are in
scope for this skill but NEVER autonomous — the operator rectifies BEFORE any agent touches an SSOT);
**near-complete-plan consolidation** (which sibling/epic the remnant folds into); **archiving a `locked_by:` plan**
(even fully-done); splitting a plan over its line-cap (a normal plan >1000, or ANY file — master/epic included — over
the absolute 5000 ceiling); anything touching a `locked_by:` plan, kill-switch, funds isolation, or the May-23 critical
path. Interactive format — batched questions ordered P0→P1 hitting the chat box directly; recurring classes get ONE
class-level question with per-item exceptions; every question carries: the two quotes + locations, why they conflict,
which doc looks authoritative and why, and options A/B/C with the recommendation marked (never open-ended —
SUB_AGENT_MANDATORY_RULES escalation format). In autonomous/AO mode the same structured questions are raised as **AO
operator alerts/escalations** (orchestrator dashboard escalation with the options block) so the operator can rule
asynchronously; the worker proceeds with everything else and applies the ruled items on the next pass.

## Phase 5 — apply + commit

- PM-repo doc edits only; stage by name; mandatory pre-commit check `git status && git diff --cached --stat` (no path
  arg); pure doc/plan changes = prek-only (no full QG needed); commit prefix `docs(plans):`; ship per CLAUDE.md's
  git-discipline section (CODE via `quickmerge.sh --agent --files`; the `git-commit` skill was REMOVED 2026-07-17 — it
  predated quickmerge and taught direct code pushes). Batch related fixes into coherent commits (one commit per class or
  per plan, not one mega-commit).
- Big findings (data-correctness, May-23 critical path, cross-repo, SSOT contradiction) additionally follow the triage
  HARD RULE: **notify the operator + file `plans/active/issues/<slug>_<YYYY_MM_DD>.md`**. In autonomous mode the issue
  doc also carries every parked `BLOCKED-OPERATOR-DECISION` with its options block.
- **Plans→codex updates are part of this skill** — when the operator's ruling says the codex SSOT is the stale side,
  apply the codex edit (update the contract, stub the new pattern, or SUPERSEDED-banner the invalidated doc, per the
  post-phase codex-audit ritual) and condense the matching CLAUDE.md one-liner if it carries the stale claim. HARD GATE:
  a codex/SSOT edit is only ever applied AFTER an explicit operator ruling on that specific finding (chat answer or AO
  escalation response) — never from the agent's own judgment, however confident the evidence.
- **Leave the corpus hygiene-canonical (green-gate — HARD).** After applying fixes: prettier every touched `.md`;
  regenerate the inventory (`regenerate_active_plan_inventory.py`); then re-run `run_hygiene_sweep.sh --ci` and confirm
  **0 hard failures** before finishing (frontmatter / todo-format / todo-regression / runbook-fields all green). A plan
  you touched must never be left non-prettier, hygiene-red, or with malformed todos. Line-caps (tiered): a **normal
  plan** over 1000 (hard) is a split finding (operator-gated — splitting a plan is a planning decision), over 500 (soft)
  is a Phase-6 report note; **long-lived master plans + epics are exempt from the 500/1000 caps** (living hubs are meant
  to be long); but the **5000-line ABSOLUTE ceiling is universal** — ANY file over 5000 lines (master/epic included) is
  a split finding, no exemption. Canonical format is the contract, same as a `quality-gates.sh`-green tree for code.
- NEVER write agent memory; NEVER create `*_SUMMARY.md` — the final report is chat text.

## Phase 5.9 — the NO-MISS LEDGER (HARD — every one of these has actually been missed)

> Added 2026-07-15 after a real run silently dropped work in **three** separate ways. The class is always the same: a
> finding was identified, then quietly never delivered — no error, no failure, just absence. Counting is the defence.

**(a) Routed-to-operator MUST equal parked. Reconcile the counts, do not eyeball it.** Compute
`routed = |{confirmed findings where needs_operator OR NOT auto_fixable}|`, then assert `routed == parked_in_issue_doc`.
Print both numbers in the Phase-6 report. _(Real miss: 4 contradictions were routed to the operator; only 3 were written
into the issue doc. The 4th — a ledger `EventType` count in a funds-isolation-adjacent plan — was silently dropped, and
only surfaced because the operator asked.)_

**(b) A sub-agent SKIP is an ACTION POINT, not a statistic.** Every `skipped` item any apply-agent returns MUST be
enumerated into the issue doc with its reason — never reported as a bare count. Skips are where the genuinely-hard
findings collect: operator-gated calls, cross-file fixes outside a one-file mandate, truncated fix-text, and
fixes-that-are-actually-unsafe. _(Real miss: 45 agents returned 10 skips; the run reported "10 skipped" and surfaced
none of them — including one where the agent correctly refused because the target doc held a LATER reversal of the
fix.)_

**(c) VERIFY AT HEAD — never trust a commit summary.** After every commit, confirm the change actually landed:
`git show HEAD:<path> | grep <the-thing-you-changed>`. A green commit line does NOT mean your edit is in the commit.
_(Real miss: an archival commit moved 13 plans but landed them still `status: active` — prek stashes unstaged changes, a
hook conflicts, the restore fails, and your edits are silently rolled back while the working tree still LOOKS right.
`git mv` reporting `(100%)` rename similarity is the tell that content you expected to change did not.)_

**(d) Conservation on any MOVE.** When work moves between docs (a fold, a consolidation), assert it landed on the other
side: count FOLDED-OUT markers == FOLDED-IN markers == new folded-in sections. A move that deletes without adding is
data loss.

**(e) Every count in the final report must be a measurement, not a memory.** Re-derive it from the corpus or the run
artifacts at report time.

## Phase 6 — report

Finish with text: counts by severity/class, the applied-fix list (commit shas), the operator-decision list (or parked
issue doc path), refuted-candidate count, and coverage (docs read / batches / topics swept). **Include the Phase-5.9
ledger explicitly — `routed_to_operator == parked` and `agent_skips == enumerated`, as NUMBERS.** If either pair does
not balance, the run is NOT done: go park the difference before reporting. Report honestly what did NOT land, too — a
silently-dropped finding is the failure this skill exists to prevent, so a run that hides its own misses is worse than
one that reports them. Recommend a re-run cadence (post-major-phase or weekly) until the confirmed-findings count trends
to zero.

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
