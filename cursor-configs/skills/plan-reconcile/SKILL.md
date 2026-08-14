---
name: plan-reconcile
description:
  Audit the PM plans corpus (plans/active + plans/active/issues + plans/epics + the normative refs PLAN_FORMAT.md /
  task_template.md / INDEX.md) for cross-doc contradictions, done-but-unchecked todos, AND
  AO-dispatch-readiness defects (first-line truncation, unenforced ordering, bare section-shorthand, ambiguous verbs,
  inconsistent delete-tagging, missing definition-of-done, uncited symbol/file forcing exploratory round-trips,
  markdown structural well-formedness, internal self-consistency — per task_template.md §3), AND data-pipeline-milestones drift for the 5 asset-group consolidated
  closeouts (per data_pipeline_e2e_milestones_gate_2026_07_24.md's 14 cross-AG correctness criteria), adversarially
  verify every finding, then reconcile — auto-fix the mechanical classes (checkbox flips with hard
  evidence, supersession banners, status/frontmatter drift, dangling refs) AND anything a source of truth can settle
  (if a claim is countable, count it — do not escalate a provable fact), then route only genuine authority/preference
  calls to the operator as a batched interactive Q&A with options + a marked recommendation. ASK > PARK: park as
  BLOCKED-OPERATOR-DECISION only when nobody is reachable to answer. Also runs a lifecycle + hygiene pass:
  archive fully-done plans (verified, unlocked), flag near-complete plans (<=1 open todo) for consolidation, and leave
  the corpus canonical (prettier + run_hygiene_sweep.sh-green, within line-caps). Plan↔codex drift is in scope and
  plans→codex SSOT updates are applied ONLY after an explicit operator ruling. **Optionally topic-scoped** — invoke as
  `/plan-reconcile [<tranche>]` across the same 10 tranches `/ag-closeout-audit` uses (`cefi`, `defi`, `tradfi`,
  `prediction`, `sports`, `cross-cutting`, `ao`, `ci`, `infra`, `ui`), or `all` (the default with no argument — preserves
  today's whole-corpus behavior exactly) for smaller, faster sharded runs a scheduled AO trigger can complete
  reliably. Trigger on /plan-reconcile [<tranche>], "reconcile the plans", "reconcile <tranche>", "plan contradiction
  audit", "check the plans for contradictions", "flip done-but-unchecked plan items", "archive done plans",
  "consolidate near-empty plans".
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

**Reads `assigned_vm: NA` docs too (Phase 2's checkbox surfaces are not filtered by `assigned_vm`), but does not ask
whether a doc's OWN `NA` classification is still correct** — that reclassification question, over the same population,
is `/na-eligibility-audit`'s disjoint remit. A false-unchecked flip inside an NA doc is still this skill's job; deciding
the doc should flip to `assigned_vm: planning` is not.

## Topic-scoped (sharded) runs — added 2026-07-25

**`all` (no argument) is the default and preserves today's exact whole-corpus behavior — nothing changes for an existing
unscoped invocation.** Passing a specific tranche narrows the audited corpus for a smaller, faster run, using the SAME
classification mechanism `/ag-closeout-audit` uses (see that skill's "10 tranches" section for the full mechanism —
summarized here, corrected 2026-07-30 to match current reality): the 5 AGs
(`cefi`/`defi`/`tradfi`/`prediction`/`sports`) filter on `asset_group` directly; `cross-cutting` filters on
`asset_group: cross-cutting` + the classification already baked into
`cross_cutting_consolidated_closeout_2026_07_25.md`'s own Tracks; **`ao`/`ci`/`infrastructure`/`ui` are now real
dedicated `asset_group` enum values** (`ao`/`ci`/`infrastructure` since 2026-07-27, `ui` since 2026-07-30 — see
`docspec.py`/`PLAN_FORMAT.md`/`doc-frontmatter-schema.md` §5) — filter on `asset_group` directly exactly like the 5 real
AGs; `parent_epic` (`ao_consolidated_closeout_2026_07_25.md` / `ci_consolidated_closeout_2026_07_25.md` /
`infra_consolidated_closeout_2026_07_25.md` / `ui_consolidated_closeout_2026_07_30.md`'s own Sources lists) is only a
secondary hint for docs the tag doesn't yet cover, same caveat as `/ag-closeout-audit`. The normative refs
(`PLAN_FORMAT.md`, `task_template.md`, `INDEX.md`) and codex stay in scope for EVERY shard (they're corpus-wide policy,
not tranche-owned). `plans/ACTIVE_INDEX.md` is a self-declared STALE Day-1-2 historical relic (superseded by
`plans/active/INDEX.md`, per its own banner) — not a normative ref, out of scope for contradiction-checking.

**Why shard**: this corpus routinely runs 500+ active plans/issues — a full sweep is expensive enough that a
scheduled/cron AO trigger benefits from a smaller, bounded-runtime shard instead of always paying for the whole corpus.
Sharding trades completeness-per-run for reliability-per-run; it does not change what counts as a contradiction or a
false-unchecked todo.

**The real trade-off — cross-tranche contradictions are invisible to a single shard.** A contradiction between a cefi
doc and a tradfi doc (or between an `ao` doc and a `ci` doc) can only be caught by a run that sees BOTH sides — a
topic-scoped run genuinely cannot find it. Sharded runs are a good default for routine/scheduled sweeps; an occasional
`all` run (or a run explicitly covering the 2 tranches in question, if the collision is already suspected) is still
needed to catch genuinely cross-tranche contradictions. Don't let sharding become the ONLY mode this skill ever runs in.

**The scheduled cadence that resolves that trade-off (operator ruling 2026-08-06)** — the AO timer
(`agent-orchestrator/scripts/install-plan-reconciler-timer.sh`) runs BOTH modes on a weekly cycle, so neither the
reliability nor the cross-tranche-coverage half is sacrificed:

- **Sun-Fri: one sharded dispatch per tranche per day** (one worker each, same shape `ag_closeout`/`na_eligibility`
  already use). Bounded, and a tranche that fails is retried independently of its siblings.
- **Saturday: ONE unsharded `all` run, and the per-tranche shards do NOT fire that day.** This is NOT a staffing/low-
  activity consideration (this is an all-agent fleet — it runs identically every day); it's the fixed weekly slot for
  the only mode that can catch cross-tranche contradictions, reserved on its own day so it isn't racing 10 sibling
  workers for the same corpus (concurrent writes to a shared doc are exactly the collision the primary-owner rule exists
  to prevent). Corrected 2026-08-09 — the day itself doesn't need to be Saturday specifically, only fixed.

**Why this was ruled**: the unsharded daily run was measured on 2026-08-06 across every retained attempt — 7 of 8 ended
`reaped-stale` (died mid-run, several within 2-5 minutes of spawn, no `/done`), and the single completion took 13.5
hours (00:01:32 → 13:29:00), holding a slot for the whole day. A daily whole-corpus sweep is not a shape this corpus can
reliably finish; a weekly one, on a quiet day, is.

**Archival caution in a topic-scoped run**: before archiving a doc that looks fully done within the current shard, grep
the OTHER 9 tranches' consolidated-closeout docs (or their Sources lists) for a reference to it — a doc can be primary
to one tranche but still cross-referenced from another's Track content (the way this session's cross-cutting Tracks 2/13
explicitly flag overlap with the cefi/defi closeouts). Archiving it without checking would silently orphan the other
tranche's reference. When in doubt, leave it and note the cross-reference for a future `all` pass.

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
  candidate); **body over the line-cap** — TWO-TIER, no exceptions (2026-07-24 ruling, superseding the old
  umbrella-exemption model below): a normal plan in `plans/active/` is 500 soft / 1000 hard; a REAL epic
  (`plans/epics/*.md`) is 2000 hard flat. There is no longer an `umbrella: true`/`locked_by`+todos escape hatch that
  lets a plan in `plans/active/` grow past 1000L unflagged — a genuinely large hub/coordinator doc either fits under
  1000L, splits, or gets promoted to a real epic (which then gets the epic tier, not a free pass); `assigned_vm` outside
  `{planning, NA}` (`human-planning` = legacy alias for `planning`, accepted); `parent_epic` naming a non-existent epic;
  duplicate titles; missing required frontmatter per `plans/PLAN_FORMAT.md`. Emit per-doc **open/done checkbox counts**
  so the fully-done + near-complete candidates are computed deterministically (they are candidates, still verified in
  Phase 2/3 before any archival).

Flags are CANDIDATES, not findings — a "dangling" ref often resolves to `plans/archive/` or codex (parser artifact).

**`run_hygiene_sweep.sh` is a first-class STEP of this skill, and it BOOKENDS the run — not a footnote:**

- **Phase 0 (entry, read-only):** `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` — `--no-regen` exists
  precisely for this read-only input-gather (it avoids dirtying `master_to_live_defi_…`). Fold its output into the
  candidate set and **do not re-implement what it already checks**: frontmatter validity + schema, todo format,
  todo-regression vs origin, runbook fields, **conflict markers**, prettier-mangling, **the `depends_on` DAG (cycles +
  self-deps)**, **the `/plans/`+`/codex/` reference-path convention (format + existence, shrinking-ratchet baseline —
  `check_reference_paths.py`, `/codex/11-project-management/cross-reference-path-convention.md`)**, line caps, estimate
  sanity, superseded-in-active, codex path refs, parent-epic alignment, CLAUDE↔SUB_AGENT parity. A RED hard check here
  is a finding in its own right, before any agent runs. **What the mechanical checker can't decide, this skill's
  contradiction/archival phases should**: which of several ambiguous same-basename matches is the right target for a
  bare `related:` entry the 2026-07-23 migration left untouched; what the correct reference is when a doc has genuinely
  moved/been renamed/archived (the archival ritual's 6th step — grep every referrer, update each — is this skill's job
  to actually execute, not just check); and whether a dangling reference should be fixed (target existed, got lost) or
  removed (the claim itself is stale). Backlog: `/plans/active/issues/reference_path_convention_2026_07_23.md`. **Caveat
  (2026-08-02)**: this framing assumes the mechanical checker at least SURFACES the flag for the skill to adjudicate —
  verified 2026-08-02 that for `check_reference_paths.py` specifically, its `--quiet`, ratchet-gated invocation here
  often does not (see Phase 1 hunter 8, "Moved-doc referrer hunter", for the closing mechanism).
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

5. **AO-dispatch-readiness hunters** — added 2026-07-23 after an ad-hoc adversarial review found 6 defect classes in a
   single AO-eligible plan that none of Phase 0's mechanical checks or Phases 1-4's contradiction/staleness sweeps would
   have caught, because these are CONTENT-judgment defects, not structural ones — this is why they need an LLM pass
   (line 3 of the plan-quality four-line-defense architecture,
   `plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md`), not a regex in
   `run_hygiene_sweep.sh` (line 2). One hunter per active AO-eligible plan (`assigned_vm: planning` or a strong
   candidate for it), checking every open `- [ ]` todo against `task_template.md` §3's rules — these are the SAME rules,
   not a parallel spec, so a rule added to §3 is automatically in scope here. **NA plans (`assigned_vm: NA`) get the two
   SPECIFICITY sub-checks too** (definition-of-done, cited-symbol below) — a human working an NA todo interactively pays
   the SAME exploratory-round-trip cost a vague todo forces on an AO worker
   (`tool_call_batching_authoring_gap_ 2026_08_14`; the user runs NA regularly on the laptop, not just AO on the VM).
   The other sub-checks stay AO-only — ordering-machine-enforcement and delete/VM-launch-risk tagging exist because AO
   is UNATTENDED; an NA session has a human present who can catch those the same way they'd catch anything else
   mid-work:
   - **Line-1 completeness** (task_template.md §3): does the todo's actual FIRST PHYSICAL LINE — not the sentence as it
     reads to a human across a markdown line-wrap — carry the complete instruction (action + method + any hard
     constraint like ON-DEMAND vs SPOT)? A bolded clause that wraps onto line 2 mid-sentence is a genuine miss even
     though a human reader never notices (confirmed case: a "DO NOT EXECUTE" warning split across a markdown bold-span's
     line-wrap, invisible to a human, invisible to the AO dispatcher's own risk).
   - **Ordering stated once, machine-enforced or explicitly flagged as not** — a real dependency between todos restated
     inconsistently in two places, or resting on prose ("after the re-runs...") with no `sequential:`/`depends_on`+
     `gate_on_depends` and no explicit "not machine-enforced yet" guard note.
   - **No bare cross-doc `§X` shorthand** at a todo's first use — resolve it against the source doc and confirm the fact
     is actually restated, not just cited.
   - **No ambiguous verb** (`absorb`/`incorporate`/`handle`/`address`) where the literal action differs materially
     between readings.
   - **Delete/VM-launch-risk tagging consistency** (widened 2026-07-25, task_template.md finding O — a scoped
     `/plan-reconcile` pass found 8 of ~15 batch docs contain a GCS delete/`--apply` and 5 contain a VM launch, with no
     systematic check any were correctly tagged) — every todo deleting/overwriting prod data OR launching a billed VM
     either carries `[OPERATOR]` + cites the delete-safety protocol / exact approval command, or explicitly states why
     it doesn't need one (soft-delete window, an already-established idempotent copy-verify-delete pattern, etc.). Pull
     candidates from `scripts/plan-hygiene/check_delete_vm_launch_gating.sh`'s soft-warn output (mechanical pre-filter,
     not authoritative) and adjudicate each — that script cannot judge whether a stated justification is actually sound,
     only whether one exists at all.
   - **Definition-of-done present** — every todo states what evidence proves it's done, not just the goal.
   - **Cited symbol/file, not just a mechanism** (`tool_call_batching_authoring_gap_2026_08_14`, task_template.md §3
     framing note) — does the todo name a specific function/class/table/endpoint/file (grep-able, per the existing
     symbol-not-line-number rule) rather than only describing a mechanism or symptom ("move the loader off its
     PATH-PREFIX read" with no file/symbol named)? A todo with nothing grep-able GUARANTEES an exploratory Read/Grep
     round-trip before any edit is possible — the same class of cost hunter 1 already measures elsewhere, just paid at
     dispatch time instead of runtime. Not every todo needs this (a genuinely novel one-file fix may not have an
     existing symbol to cite) — flag only when the todo's own wording gives a worker nothing to grep for AND
     `context_scope` (§2a) doesn't already cover it. Auto-fixable when the missing symbol is findable in ≤1 grep
     (rewrite the todo to name it); otherwise route to the operator like any other scope finding.
   - **Bounded outcome, no judgment call** (operator ruling 2026-07-23,
     `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility") — is the
     todo's outcome DETERMINABLE by the dispatched worker alone (a checkable fact, a scoped change, an audit with a
     stated done-when), or does completing it actually require a design/judgment call ("figure out how X should look",
     "decide the right approach for Y") that isn't already decided? An audit todo is fine when precisely scoped ("does X
     match Y") — flag it only when the scope itself IS the open question. A flagged todo routes to the operator as a
     scope/authoring finding (not auto-fixable — resolving the judgment call is exactly the kind of authority-only
     decision Phase 4 already reserves for a ruling, not a mechanical rewrite): either the operator answers it now and
     the todo gets rewritten against that decision, or it gets pulled out of the AO-dispatched plan entirely into a
     LOCAL/human one. Findings route through the same Phase 3 adversarial-verification + Phase 4 routing as
     contradictions (auto-fix the mechanical rewrites directly with evidence; ask/park only genuinely ambiguous judgment
     calls, e.g. whether a delete needs `[OPERATOR]`).
6. **Data-pipeline-milestones drift** — added 2026-07-24 alongside `data_pipeline_e2e_milestones_gate_2026_07_24.md` (14
   cross-AG data-pipeline-correctness criteria: canonical adapters/registries/GCS paths, VM/billing monitoring, MDPS
   canonicalization, honest-coverage math, checkpoint cadence, AO-dispatch-readiness, MVP/batch=live=paper wiring). That
   doc's 64 todos are tagged `target: <file>` — most target the 5 asset-group consolidated closeouts. For each AG
   closeout, confirm every todo tagged for it has actually landed there (not just proposed) — an unlanded todo after its
   gate doc's `last_updated` is drift, same class as a stale checkbox. This is CONTENT correctness for data-pipeline
   plans specifically, distinct from hunter 5's general AO-dispatch-readiness format check — run both, they catch
   different things.
7. **Prose/structural-integrity hunters** — added 2026-07-24 (findings L/M, `task_template.md` §3) after an adversarial
   verification pass on `data_pipeline_e2e_milestones_gate_2026_07_24.md`'s 64-todo distribution found two defect
   classes NO existing hunter's checklist named: a heading whose parenthetical annotation split across a blank line
   (orphaning a floating `)`), and an invariant paragraph that contradicted itself in the same sentence and against the
   formula the same doc showed two paragraphs above. Neither is a todo-line rule (hunter 5) or a cross-doc contradiction
   (hunters 1-4) — both are WITHIN one doc's own newly-touched prose, so they slip through unless explicitly checked.
   Piggyback on whichever hunter already reads that doc in full (epic-cluster/topic hunters, items 1-2 — no new
   dedicated pass needed) and add these two checks for every heading/bold-span/invariant-paragraph the run's diff
   touched: (a) **structural well-formedness** — every `(`/`` ` ``/`**`/`[` opened on a heading or bold-span line closes
   on the SAME physical line, never across a blank line; (b) **internal self-consistency** — any stated
   rule/invariant/formula, re-derived against an example or formula the same doc shows elsewhere, must not contradict it
   or itself mid-sentence.
8. **Hedge-pointer / stale-candidate hunter** — added 2026-08-03 after a real todo
   (`../archive/2026_08/data_status_page_ux_and_canonicalisation_2026_07_16.md` todo P3) named 3 "candidates found by
   grep" for 4 follow-up items — only 1 of the 3 was a real owner, and 2 of the 4 items were actually owned by an
   entirely different, unlisted doc found only by a fresh corpus-wide grep. Grep the corpus for hedge language a doc's
   own prose/todos use in place of a confirmed reference — "candidates found by grep", "likely owned by", "probably
   tracked in", "TBD which doc covers this", "not yet identified" — and treat every hit as an unverified claim, same bar
   as hunter 4's plan↔codex drift: grep-then-READ every named candidate, confirm whether it actually owns/tracks the
   claim, and (per this workspace's grep-then-conclude ban) don't stop at the named candidates — a fresh corpus grep for
   the item's real owner is required before concluding "not yet identified" is still accurate. Mirrors
   `cursor-configs/skills/context-scout/SKILL.md` Phase 1 step 4, which does the identical verification but can only
   ever update `context_scope` — it is this skill's job (not context-scout's) to actually rewrite the doc's own hedge
   prose once a candidate is confirmed right, wrong, or replaced by a different real owner. If a confirmed owner's todo
   also happens to already be `- [x]`/shipped, fold the finding into Phase 2's done-but-unchecked flip too (this was the
   exact shape of the motivating incident — a stale pointer AND a flippable-done item at once).
9. **Moved-doc referrer hunter** — added 2026-08-02 (`issues/reference_path_convention_2026_07_23.md`'s "Confirm
   `/plan-reconcile` catches a doc moving without its referrers being updated" todo, dispatched via
   `infra_satellite_ao_dispatch_batch1_2026_07_26.md`), after determining the existing mechanism does NOT reliably catch
   this class for the dominant referrer shape. Verified by reading the actual code, not assuming from this skill's own
   prose: `check_reference_paths.py`'s existence check DOES scan every `/codex/...`/`/plans/...` reference ANYWHERE in
   body text, not just frontmatter (`GOOD_REF_RE.finditer(text)` over the whole doc) — but two things blunt it in
   practice. (a) `run_hygiene_sweep.sh` invokes it `--quiet` (its own line:
   `run_check ... check_reference_paths.py --quiet`), which suppresses the itemized per-file violation list — only a
   binary pass/fail per check reaches Phase 0's candidate set, never the actual dangling-ref lines, so Phase 1
   mechanical adjudicators have nothing to adjudicate even when the gate is red. (b) it is a SHRINKING-RATCHET check
   against a baseline with substantial slack (`reference_paths_baseline.yaml`; live-verified 2026-08-02: existence
   baseline 901, live count 913 — already over, unrelated to any specific move) — a moderate single-move regression (the
   cited incidents: 78/66/3 new dangling referrers each) can land entirely inside that slack without ever pushing the
   corpus-wide total over the ratchet ceiling, especially if unrelated fixes elsewhere in the same window offset the
   count. Net effect: for INLINE BODY-TEXT references (the dominant referrer shape — a doc archival/rename breaks
   citations scattered through OTHER docs' prose, not just their `related:` frontmatter list), the existing mechanism
   gives no per-move specificity and can silently miss a genuine regression, which is exactly what happened in all three
   of the cited 2026-07-25 incidents — none were caught by a `/plan-reconcile` pass; all were found by a human/agent
   noticing a broken link after the fact. (Frontmatter `related:`/`depends_on`/`supersedes` referrers ARE reliably
   caught today — Phase 0's own throwaway inventory script computes those directly, ungated by any ratchet, as genuine
   per-doc Phase-1 candidates every run; this hunter closes the remaining body-text gap, it does not duplicate that
   coverage.) **Fix**: for every doc that moved/archived/renamed since the last reconcile run
   (`git log --diff-filter=AR --name-status --since=<last-run-timestamp> -- plans/ codex/`), grep the FULL corpus body
   text (not just frontmatter) for the OLD path/basename; any hit is a hard finding routed straight to the existing
   Phase 4 auto-fix row ("Dangling ref where the target moved to archive/codex → Repoint the ref") — ungated by the
   ratchet, since a specific tracked move's referrers are a deterministic, provable check (the old path is gone, the new
   one exists, a grep hit names exactly which doc + line), not a preference call. Also re-run `check_reference_paths.py`
   WITHOUT `--quiet` (or capture its stdout directly instead of piping through `run_hygiene_sweep.sh`'s summary) so its
   itemized existence-violation list becomes a real Phase-1 candidate feed on every run, closing the residual gap for
   dangling refs the git-log-diff pass structurally can't catch (e.g. a referrer added after its target was already
   gone, so there's no "move" to diff against).

## Phase 2 — done-but-unchecked sweep

Sweep **every checkbox surface in the audit corpus**, not just active plans — the false-unchecked class hides in issue
docs and epics too. For every `- [ ]` in each of the three surfaces, hunt evidence the work already shipped:

1. **ACTIVE (non-draft) plans** — `plans/active/*.md` todos (the primary surface).
2. **Issue docs** — `plans/active/issues/*.md` action items / remediation checkboxes (an issue whose fix demonstrably
   shipped but whose `- [ ]` never flipped, or whose resolution warrants closing the doc).
3. **Epic checkboxes** — `plans/epics/*.md` items that reference a child plan/milestone: flip when that child is
   verifiably done (all its todos flipped, or it's archived). A ticked epic box over an unfinished child is the inverse
   contradiction (route to Phase 1), not a flip.

(`status: draft` plans are excluded — WIP, not yet dispatched.) **Sweep for `- [ ]` with a pattern that also catches
indented/star-bullet variants** (`grep -nE '^[[:space:]]*[-*] \[ \]'`, not the plain `^- \[ \]` anchor-only form) — a
2026-08-07 cross-check against `/na-eligibility-audit`'s Phase 0 inventory found a doc whose sole open item used
`  * [ ]` and was silently missed by the plain pattern; the plain form under-counts on any doc using that style. The
same HARD-evidence bar below applies to all three surfaces; evidence in descending strength — a flip requires at least
one HARD item:

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

**Line-cap-blocked-done is a distinct sub-case, not ordinary done-but-unchecked (2026-08-07 finding, surfaced by
`/na-eligibility-audit`)**: an item can carry full HARD evidence of shipping yet still be sitting over its own doc's
Phase 5 line-cap (normal plan >1000 hard, epic >2000 hard), where the split-then-close sequence that would let it be
safely checked off hasn't run yet. Do not simply flip it in place if the doc is over-cap — flipping checkboxes inside an
already-over-cap doc doesn't fix the cap violation and can mask how much the split actually needs to shed. Route it as
this skill's own Phase 4/5 split finding (operator-gated: splitting a plan is a planning decision) with a note that at
least one of the pending items is HARD-evidence-verified-done and should be closed as part of the split, not discovered
fresh afterward.

### 4. ZERO-CHECKBOX docs — this skill's standing responsibility, all 10 tranches (added 2026-07-30)

**This skill OWNS the zero-checkbox sweep.** A doc with no `- [ ]` and no `- [x]` at all has no surface for any of the
three sweeps above — it is invisible to `check_todo_format.sh`, to `regen_backlog_from_plan.py`, to the near-complete /
fully-done candidate computation in Phase 0, and to every orphan and NA audit that counts todos. It is the purest form
of the false-progress class this skill exists to kill: real remaining work written as prose, with nothing mechanical
able to see it. Named owner + named cadence, so it stops being a periodically-rediscovered one-off: **it runs as part of
this skill's own periodic run, every run.**

- **Corpus scope is ALL 10 tranches** — `cefi`, `defi`, `tradfi`, `prediction`, `sports`, `cross-cutting`, `ao`, `ci`,
  `infra`, `ui`, PLUS `asset_group: meta` and any doc whose tag doesn't resolve to a tranche at all. This is the
  correction: the previous sweep covered only the 5 original AGs, and that was a STRUCTURAL blind spot, not an oversight
  of execution — `ao`/`ci`/`infrastructure` (real enum values since 2026-07-27) and `ui` (since 2026-07-30) are
  precisely where prose-only process/incident write-ups collect. In a topic-scoped run, sweep your own tranche; an
  `all`/unscoped run must cover every one.
- **Per doc**: read it end to end, decide whether it holds genuine remaining work. If yes → convert each item into a
  canonical `- [ ]` [TAG] P<n>. todo in the doc (never leave it prose — `/codex/12-agent-workflow/`
  `plan-completion-and-archival-discipline.md` § 2). If no → it is a finished record: archive it via the 6-step ritual
  (a zero-open-todo doc archives regardless of line-cap — same codex doc, § "The line-cap does NOT block archival").
  Genuinely ambiguous → route through Phase 4 like any other judgment call.
- **Report the count every run** (docs with zero checkboxes found / converted / archived / routed), so a growing
  population is visible instead of silently accumulating between sweeps.
- **Standing register**: `/plans/active/issues/zero_checkbox_sweep_all_tranches_2026_07_31.md` tracks the sweep's owner,
  cadence, and running count across runs — read/update it each pass rather than re-deriving population definitions from
  scratch.

## Phase 3 — adversarial verification (nothing ships unverified)

Dedup candidates by (doc-pair, claim), then for each: an independent **refuter** (assume NOT real; attack via
scope/time/supersession/misquote) and an independent **confirmer** (re-locate both quotes, check which doc is
newer/authoritative via dates + banners + codex). Split votes go to a **tiebreaker**. Only CONFIRMED items proceed;
classify each as `contradiction` / `stale-drift` / `scope-difference` / `format-only`. Checkbox-flip candidates verify
the same way: the refuter attacks the evidence chain (sha actually reachable? artifact actually does the todo?).

## Phase 4 — resolution routing

**Auto-fix (no ruling needed — apply in Phase 5):**

| Class                                                          | Fix                                                                                                                                                                                                                 |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Done-but-unchecked with HARD evidence                          | Flip checkbox with `<repo>@<sha> + evidence`                                                                                                                                                                        |
| Terminal-status doc parked in `plans/active/`                  | Run the 5-step archival ritual — but `locked_by:` blocks archival without `[unlock-plan]` (ASK; in autonomous mode park it)                                                                                         |
| Fully-done plan (every todo `[x]`, `status: active`, UNLOCKED) | Verify each todo genuinely done via Phase-2 HARD evidence (a plan can be false-checked), then run the 5-step archival ritual. Any todo only soft-supported, or `locked_by:` set → park, never autonomous-archive    |
| Superseded content with no banner                              | Add the `> **SUPERSEDED by <doc> (<date>)**` banner; point to the successor                                                                                                                                         |
| Frontmatter status contradicting body completion banner        | Align frontmatter to reality (verify reality first, both directions possible)                                                                                                                                       |
| Dangling ref where the target moved to archive/codex           | Repoint the ref                                                                                                                                                                                                     |
| Duplicate/stale index rows (INDEX.md / ACTIVE_INDEX.md)        | Regenerate via the inventory tooling, never hand-sync                                                                                                                                                               |
| Hedge-pointer confirmed (hunter 9)                             | Rewrite the doc's own prose/todo to name the confirmed real owner directly (or state plainly that no owner exists), dropping the "candidates found by grep"/"TBD" framing — a confirmed fact, not a preference call |

**Completion + consolidation lifecycle (verify-then-archive; destination is operator-gated):**

- **Fully-done plan** (every todo `[x]`) — confirm each is genuinely done via the Phase-2 HARD-evidence bar (soft-only =
  contradiction finding, not an archive), then: UNLOCKED → archive via the 5-step ritual (auto-fix above); `locked_by:`
  set or any todo soft-only → park as `BLOCKED-OPERATOR-DECISION`. Never autonomous-archive a locked plan.
- **Near-complete plan** (≤1 open todo, or a remnant too small to justify a standalone plan) — the remnant should be
  **folded into a sibling plan under the same `parent_epic`** (or the epic hub) and the shell archived. But WHERE live
  work lives is a planning decision: interactive → ask with a recommended fold-target; autonomous/AO → **park with the
  specific recommended target named**, never auto-fold (moving live todos between plans without a ruling is
  review-blocking). Once the remnant is folded by ruling, the emptied shell archives as a fully-done plan.

  **The ONE narrow fold-by-default carve-out (operator ruling 2026-07-30).** Auto-folding without a ruling is authorized
  ONLY when BOTH hold:
  1. the single remaining open todo is tagged **`[REVIEW]` or `[DOC]`** — the two lowest-blast-radius classes, where a
     wrong fold target costs a re-read, not mis-routed engineering work; AND
  2. its `parent_epic` has **exactly one** obvious ACTIVE sibling plan — i.e. the fold target is not a choice at all, it
     is the only destination that exists. Two or more candidate siblings means the destination IS a preference call and
     the default rule above applies unchanged.

  Anything else stays operator-gated — a `[SCRIPT]`/`[DATA]`/`[OPERATOR]` remnant, a zero-sibling epic, a multi-sibling
  epic, or any remnant carrying a `locked_by:`. When the carve-out DOES apply, still record the fold both ways
  (FOLDED-OUT marker in the shell, FOLDED-IN section in the target) so Phase 5.9(d)'s conservation assertion balances.

  **Ongoing near-complete-plan handling routes through the regular audit cadence, not a one-off mechanism.** This
  skill's own periodic run plus `/ag-closeout-audit` and `/na-eligibility-audit` on their standing schedules already
  sweep the whole corpus for this shape — near-complete plans are a steady-state condition, not a backlog to be drained
  once. Do not build (or ask the operator to schedule) a special one-off near-complete sweep; if the cadence isn't
  catching them, fix the cadence.

| Claim provably wrong vs the source of truth | **AUTO-RESOLVE — do not escalate.** If a number/name/status is countable
or checkable (AST, `git cat-file`, `os.path.exists`, a newer dated banner in the same doc), RUN the check and fix it,
citing the command + output as evidence. Prefer deleting a derivable restated fact over correcting it — a hardcoded
count re-stales on the next bump. See Modes § "Calibration" |

**Operator ruling required (Q&A in interactive mode; park + alert ONLY if nobody is reachable — see Modes § ASK >
PARK):** SSOT-ownership disputes; two ACTIVE docs giving opposing directives; epic vs plan disagreeing about scope or
sequencing; conflicting numbers **that no source of truth can settle** (if one side is checkable, it is NOT a ruling —
go check it); neither side has hard evidence; **ANY resolution that edits a codex SSOT doc, EXCEPT the narrow MECHANICAL
codex-staleness carve-out** (operator ruling 2026-08-09, mirrors `agents/plan_reconciler.md` STEP 5.f2): auto-apply ONLY
when the codex text is factually stale per HARD evidence (same bar as a todo flip), the fix is a single unambiguous
substitution with no judgment call between multiple plausible values, it doesn't touch a HARD-STOP governance area
(delete-safety rules, human-only hard-stops, version-graduation rules), and you don't run a NEW measurement to produce
the corrected value (cite only existing evidence). Everything else stays operator-gated — the operator rectifies BEFORE
any agent touches an SSOT; **near-complete-plan consolidation** (which sibling/epic the remnant folds into); **archiving
a `locked_by:` plan** (even fully-done); splitting a plan over its line-cap (a normal plan >1000, or an epic >2000);
anything touching a `locked_by:` plan, kill-switch, funds isolation, or the May-23 critical path. Interactive format —
batched questions ordered P0→P1 hitting the chat box directly; recurring classes get ONE class-level question with
per-item exceptions; every question carries: the two quotes + locations, why they conflict, which doc looks
authoritative and why, and options A/B/C with the recommendation marked (never open-ended — SUB_AGENT_MANDATORY_RULES
escalation format). In autonomous/AO mode the same structured questions are raised as **AO operator alerts/escalations**
(orchestrator dashboard escalation with the options block) so the operator can rule asynchronously; the worker proceeds
with everything else and applies the ruled items on the next pass.

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
  you touched must never be left non-prettier, hygiene-red, or with malformed todos. Line-caps (two-tier, no exceptions,
  2026-07-24): a **normal plan** in `plans/active/` over 1000 (hard) is a split finding (operator-gated — splitting a
  plan is a planning decision), over 500 (soft) is a Phase-6 report note; a **REAL epic** (`plans/epics/*.md`) over 2000
  (hard) is likewise a split finding. Neither tier has an exemption — a plan does not get to be a long-lived hub while
  still counted as a plan; it either fits, splits, or gets promoted to a real epic. Canonical format is the contract,
  same as a `quality-gates.sh`-green tree for code.
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

## AO-VM handoff — LIVE (this skill's own doc was stale on the cadence; fixed ao_remediation_a_independent_fixes_2026_07_23 #8)

The handoff described below is DONE, not a target end-state: `plan_reconciler` (the `agents/plan_reconciler.md` worker
that folds this skill's autonomous contract in) runs automatically in autonomous mode via `plan-reconciler.timer` on the
central orchestrator VM — `agent-orchestrator/scripts/install-plan-reconciler-timer.sh` installs it. **Cadence as of
2026-07-30: every 2 hours, on EVEN hours at :00 UTC**, with an idempotency guard that makes every fire after the day's
first success a cheap no-op — so this is retry-until-capacity, not 12 reconciles a day. Widened from the 2026-07-29
hourly cadence because a whole-corpus run MEASURED 4175s (69.6min) on 2026-07-30 (45-50min even on a quiet corpus), well
past the 15-min inter-job stagger the hourly schedule assumed; the unit's `TimeoutStartSec` went 2450 → 6000 in the same
change. If a run ever needs more than ~2h, shard it by tranche (this skill already supports that) rather than growing
one monolithic run's budget again. The timer POSTs `{"mode": "reconcile"}` to `/api/plan-health/dispatch`, which spawns
the worker (opus / effort max / thinking on) on a free Max-plan slot. The autonomous contract above (no pauses, auto-fix
only, park rulings, notify on big findings) is exactly the non-interactive behaviour that daily worker runs under. This
skill (`/plan-reconcile`) stays directly invocable interactively any time — the timer is additive, not a replacement for
an on-demand run.

## Codex SSOTs

- `/codex/12-agent-workflow/commit-push-flip-rule.md` — flip cadence + format
- `/codex/11-project-management/doc-frontmatter-schema.md` + `plans/PLAN_FORMAT.md` — frontmatter truth
- `codex/11-project-management/` — findings triage, archival ritual, issue-doc lifecycle
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — assigned_vm/role semantics
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — AO-dispatch batch naming, the shared
  conflict-check protocol, and the assigned_vm:NA corpus ratchet
- `cursor-configs/skills/na-eligibility-audit/SKILL.md` — sibling skill (NA-doc validity/reclassification, disjoint
  population from this skill's contradiction/false-unchecked sweep)
- `cursor-configs/skills/context-scout/SKILL.md` Phase 1 step 4 — the mirrored hedge-pointer verification; that skill
  can only write `context_scope`, this skill (hunter 9) is the one that rewrites the doc's own prose
- `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — sub-agent spawn contract + escalation format
