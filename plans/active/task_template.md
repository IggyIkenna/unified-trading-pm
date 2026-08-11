---
doc_type: plan
title: Task Template — How to Author a Plan
summary:
  How to author a plan the fleet can execute. Pick a TRACK (LOCAL/human vs AO-dispatched), copy the matching
  frontmatter, follow the todo format, and honour the AO rules (10-100 todos, intra-plan concurrency by default +
  when/how to serialise, split-into-plans for partial parallelism, draft-gated phases, per-task `[TAG]` roles). Read
  this BEFORE writing any plan. Dispatch + prerequisite mechanics (§4) are verified against `regen_backlog_from_plan.py`
  / `dispatch.py` so an author never relies on unbuilt behavior.
status: active
nature: process
asset_group:
  [meta] # corrected 2026-08-10 (/ag-closeout-audit cross-cutting) -- was [cross-cutting]. Content is 100%
  # project-management process/format documentation for how to author ANY plan corpus-wide (LOCAL and
  # AO-dispatched alike), identically applicable to every tranche -- genuinely process-spanning, matching its
  # own `stage: [meta]` and the `meta` asset_group definition exactly, not a "generic infra-data-pipeline
  # concern" (cross-cutting's actual bar).
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [template, format, canonical, agent-task, plan-authoring]
related: [/plans/archive/2026_07/ao_dispatch_correctness_regen_reconcile_2026_07_07.md, /plans/PLAN_FORMAT.md]
created: "2026-02-25"
last_updated: 2026-07-24 # was: 2026-07-23 — corrected 2026-07-24, added §3 findings L/M (markdown structural well-formedness, internal self-consistency) surfaced by an adversarial verification pass on data_pipeline_e2e_milestones_gate_2026_07_24.md's 64-todo distribution; prior entry: corrected 2026-07-23, plan_quality_four_line_defense_architecture_2026_07_23.md line-1 todo: added §3 rules for findings D/E/F/G/C (section-shorthand, ambiguous verbs, delete-risk tagging, definition-of-done, stale-checkbox pre-check) surfaced by an adversarial AO-dispatch-readiness review of sports_consolidated_closeout_2026_07_19.md
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class:
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
locked_by:
locked_since:
context_scope:
  [
    /plans/PLAN_FORMAT.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
    agent-orchestrator/server/dispatch.py,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
supersedes:
superseded_by:
depends_on:
source:
assigned_role: infra
drift_direction: advance-code
---

# Task Template — How to Author a Plan

> **READ THIS before writing any plan.** Pick your TRACK (§1), copy the matching frontmatter (§2), follow the todo
> format (§3). AO-dispatched plans have STRICT rules (§4). Editing a plan whose tasks are already live? §5. Canonical
> frontmatter schema: `plans/PLAN_FORMAT.md`. **Never hand-edit `backlog.yaml`** — the backend owns it; you author
> plans. **Authoring or maintaining a data-pipeline / asset-group consolidated-closeout plan?** Also check
> `/plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md`'s 14 cross-AG correctness criteria (canonical
> adapters/registries/GCS paths, VM/billing monitoring, MDPS canonicalization, honest-coverage math, checkpoint cadence,
> AO-dispatch-readiness, MVP/batch=live=paper wiring) — this template governs plan FORMAT; that doc governs
> data-pipeline CONTENT correctness for the same class of plan.

---

## 1. Pick your track — LOCAL vs AO-DISPATCHED

|                    | **LOCAL / human plan**                                     | **AO-DISPATCHED plan**                   |
| ------------------ | ---------------------------------------------------------- | ---------------------------------------- |
| Who executes       | you / an interactive session                               | background AO fleet workers              |
| `assigned_vm`      | `NA`                                                       | `planning`                               |
| `execution_scope`  | `local-only`                                               | `orchestrator-agent`                     |
| Ingested by regen? | **No** (never)                                             | **Yes** (when `status: active`)          |
| Length             | any (not ingested)                                         | **10-100 todos — STRICT**                |
| Use when           | operator-only work, design docs, trackers, dispatcher work | autonomous work you want the fleet to do |

**Default is LOCAL** unless you intend the fleet to pick it up. **HARD RULE (CLAUDE.md): ask the operator before
creating an AO plan** — _"agent-orchestrator plan or human plan?"_ A `status: draft` plan is never ingested regardless
of track — flip to `active` to dispatch.

**Defaulting to `assigned_vm: NA` is not a one-way door — and the NA backlog is size-ratcheted (2026-07-27).** A LOCAL
plan you're unsure about should still get a real look later: `/na-eligibility-audit` walks the whole `assigned_vm: NA`
corpus and reclassifies genuinely bounded work to `planning` (never a rename — the flip happens in place). The backlog's
doc/todo counts are hard-gated via `check_na_corpus_ratchet.py` in `run_hygiene_sweep.sh` — it must not grow unattended.
Naming/pairing convention for any batch/finalize doc this produces, plus the shared conflict-check every
reclassification runs before flipping: `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`.

---

## 2. Frontmatter (copy the matching block)

**AO-DISPATCHED** (fleet executes):

```yaml
---
doc_type: plan
title: <concise — what this plan achieves>
summary: <2–4 lines; NO ": " colon-space in unquoted text — use an em-dash —>
status: active # draft (NOT ingested) | active | blocked | paused | complete | cancelled | superseded (was: "active | draft (NOT ingested) | done | blocked" — corrected 2026-07-12, doc-reconciliation autofix finding 382, plan_reconciliation_operator_decisions_2026_07_11.md §A2 "50 reclassified" blanket ruling; PLAN_FORMAT.md:86 + scripts/docs/docspec.py:59 are the enforced enum, which has no "done" value)
nature: process # process | design
asset_group: [<group>] # e.g. [defi] [tradfi] [meta] -- agent-orchestrator-internal content (repos: [agent-orchestrator]
# + parent_epic: orchestrator_master -- worker lifecycle, dispatch, boot/context, spawn/recycle) is [ao], NOT
# [infrastructure]. `infra` is "generic infrastructure/hygiene work that ISN'T agent-orchestrator-internal"; `ao` is
# "agent-orchestrator dispatch/worker-lifecycle" specifically. This exact mistag recurred 3x within 8 days
# (2026-07-30..08-06, see ag_closeout_audit_infra_parked_2026_08_07.md findings 6/18/19) before being fixed by operator
# ruling 2026-08-07 -- check repos:/parent_epic: against this rule before defaulting to [infrastructure].
stage: [<stage>] # e.g. [data] [meta]
repos: [<repo>, ...]
scope: [engineer]
tags: [<tag>, ...]
related: [<doc>, ...]
created: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
parent_epic: <epic-slug> # REQUIRED — absence = orphan = review-blocking
assigned_vm: planning # planning = AO executes | NA = not dispatched
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra # refactor 0.4x | design 0.6x | infra 0.8x | brand-new 1.0x | research 1.2x
estimate_baseline_ai_days: <n>
estimate_calibrated_ai_days: <n × class-multiplier>
assigned_role: <default craft — data_engineering | infra | backend_engineer | ui_developer | review>
# model_tier: opus-required # optional — default sonnet (role-derived); fable-required = OPERATOR-REQUEST-ONLY (§4)
drift_direction: advance-code
depends_on: # optional — upstream plan slugs (documents ordering + gates archival)
# gate_on_depends: true    # optional — machine-hold this plan's tasks until depends_on tasks are done
# sequential: true         # optional — STRICT serial: task N waits for N-1 done — SHIPPED (was: "[ROLLING OUT — see §4]" — corrected 2026-07-12, doc-reconciliation finding 380, §A2 B-queue ruling: ao@ff6100ad shipped `_wire_sequential_prereqs` + `plan_order` with tests, and 3+ production plans/issues already set `sequential: true` in frontmatter, e.g. active/issues/v1_enumerator_dispatch_not_deletable_2026_07_06.md)
---
```

**LOCAL / human** — same block with `assigned_vm: NA` + `execution_scope: local-only`. Length is unconstrained (never
ingested). Use for operator-only work, trackers, design docs, and dispatcher-surgery plans.

---

## 2a. Populate `context_scope` yourself at authoring time — don't leave it for the next `/context-scout` sweep

`context_scope` (an elective frontmatter field, `plans/PLAN_FORMAT.md`) is a curated reading-list — codex SSOTs, related
plan/issue docs, key source paths — that saves the next worker a cold grep. `/context-scout` runs hourly and will
eventually backfill it if you skip this, but "eventually" has a real cost: a doc that sits `context_scope: []` between
filing and the next sweep is exactly the gap that lets a duplicate investigation happen (real incident —
`odds_api_key_quota_exhausted_4_days_after_provisioning_2026_08_02.md` was filed with no cross-reference to
`sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`, a sibling doc that had independently recorded the identical
exhaustion evidence a day earlier and already contained the full root-cause trail; the next worker to pick up the first
doc had to redo ~215k tokens of fleet-wide grepping before finding it, 2026-08-03).

**This costs you nothing extra to do**: CLAUDE.md's pre-task plan/issue conflict-check HARD RULE already requires
grepping `plans/active/` + `.../issues/` before starting any task — capture that grep's output into `context_scope`
instead of discarding it. Two additions worth the extra 30 seconds beyond a plain topic/keyword grep:

- **Grep by evidence fingerprint, not just topic** — if your doc's evidence includes a distinctive literal (an exact
  error code, an HTTP header value, a secret/resource name, a VM name), grep the corpus for that EXACT string, not just
  your topic keywords. Two docs independently recording the same fingerprint are very likely the same incident even if
  their titles look unrelated.
- **Link both directions** — if you find a genuine match, add it to your own `context_scope`, and (small edit,
  `context_scope`/`related` + a dated marker only) add your new doc to the found doc's `context_scope`/`related` too, so
  a worker who lands on either one sees both.

If you can't find anything worth citing yet (a genuinely novel investigation), leave `context_scope` unset — don't pad
it — `/context-scout` will pick it up on its next sweep once more of the corpus exists to cross-reference against. See
`cursor-configs/skills/context-scout/SKILL.md` for the full methodology (source-path hunting, hedged-candidate
resolution, fingerprint cross-referencing) if you want to do a more thorough pass than this quick authoring-time
version.

---

## 3. Todo format

- Every todo: `- [ ] [TAG] P0. <description>` (open) → `- [x] N. ✅ [TAG] P0. <desc> — <repo>@<sha> + evidence` (done).
- **Keep each todo's load-bearing content on the FIRST physical line** _(verified in `regen_backlog_from_plan.py`
  2026-07-21: `_parse_open_todos` captures only the first line matching `- [ ]`; wrapped/indented continuation lines are
  NOT parsed into the task brief the dispatcher sees)._ The `[TAG]`, `P<n>`, and the essential verb-phrase MUST be on
  line 1; treat continuation lines as human-only notes the worker's brief will not include. **Watch for the subtle
  failure mode** (caught 2026-07-23): a `**bold**` span that word-wraps across a markdown editor's soft line-break can
  put a physical newline INSIDE what reads as one continuous sentence to a human — the load-bearing clause after that
  wrap is invisible to the parser even though nobody notices reading it. When in doubt, check the raw file's actual line
  breaks (`grep -n` or the line-numbered Read output), not how the rendered markdown looks.
- **Reference SYMBOLS, never line numbers** _(operator rule 2026-07-21)_. A plan out-lives the code it points at — the
  moment any agent edits a file, every `file.tsx:821` / `:256-320` shifts and now points at the WRONG code (exactly what
  happened when one plan extracted shared primitives out of `Deployments.tsx` and every dependent plan's line refs went
  stale). Cite the **function / class / component / type / testid / endpoint** an agent can `grep` for (e.g. "the
  `useColumnSort` hook in `src/hooks/`", not "`Deployments.tsx:888`"); the agent locates the current position itself.
  Same for **counts** ("all N tests") — pin the stable thing ("keep every existing assertion in `foo.spec.ts` green"),
  not a number that a new test invalidates.
- **`[TAG]` → craft role** (per-task, AO): `[INFRA]`→infra · `[DATA]`→data_engineering · `[BACKEND]`→backend_engineer ·
  `[UI]`→ui_developer · `[REVIEW]`→review. Generic `[CODE]` / `[SCRIPT]` → the plan's `assigned_role`.
- **Priority** `P0`–`P3` (P0 = most urgent). Same-priority tasks run in plan-file order (§4).
- **Non-dispatchable** (kept visible, never ingested): a line containing `BLOCKED-<TOKEN>` (e.g. `BLOCKED-CREDENTIALS`,
  `BLOCKED-OPERATOR-DECISION`), `[OPERATOR]` (operator-only action), or a `_(stretch, optional)_` marker. **Do not
  confuse this ingestion-gate family with the `/done`-time disposition markers below** — `BLOCKED-<TOKEN>` keeps a todo
  OUT of the backlog entirely; the markers below are how a worker CLOSES a dispatched todo it cannot `[x]`-flip.
- **`/done`-time disposition markers** (server-recognized closures for a dispatched todo that cannot be `[x]`-flipped;
  ground truth `agent-orchestrator/server/verify.py`'s `_ADDED_*_LINE_RE`/`_diff_*_checkbox` family — a worker's `/done`
  M3 gate accepts any of these in place of a real checkbox flip):
  - **`CANCELLED`/`SUPERSEDED`** — the todo is re-scoped or dead, nothing left to complete. Replace the `- [ ] <brief>`
    line with a bold, non-checkbox bullet: `- **[TAG] P<n>. CANCELLED — SUPERSEDED <date> (<who>, per <ref>).**`
  - **`DEFERRED-BY-DESIGN`** — the operator has ruled a CLOSED, PERMANENT non-fix (no timeline, nothing to schedule).
    Line stays `- [ ]` but the text carries the literal marker: `- [ ] [TAG] P<n>. DEFERRED-BY-DESIGN — <why + ref>.`
  - **`BLOCKED-ON:<ref>`** — distinct from the `BLOCKED-<TOKEN>` ingestion-gate family above: this is genuinely still
    open, real work, temporarily blocked on ANOTHER owner's already-in-flight fix (not a permanent non-fix like
    DEFERRED-BY-DESIGN, not re-scoped/dead like CANCELLED — e.g. a RED-gated data-correctness todo whose real fix is
    owned by a different slot's active chain). Line stays `- [ ]`, text carries `BLOCKED-ON:<slug-or-doc-ref>` anywhere:
    `- [ ] [TAG] P<n>. BLOCKED-ON:<other-doc-slug> — <why + who owns the unblocking fix>.` The todo stays visible and
    dispatchable-looking in the plan text, but the disposition marker is what lets the worker holding it call `/done`
    (`reason: "todo_blocked_pending_other_owner"`) without a false `[x]` flip — it does NOT remove the todo from the
    backlog the way `BLOCKED-<TOKEN>` does; whoever resolves the blocking work still needs to come back and either flip
    it for real or re-tag it. Source:
    `/plans/archive/2026_07/issues/ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md`.
- **No bare cross-doc section shorthand** _(2026-07-23, adversarial-review finding D:
  `sports_consolidated_closeout_2026_07_19.md` had todos citing `§A2`/`§T`/`§W`-style labels that only resolved against
  a DIFFERENT document's internal sections — meaningless to an agent dispatched just that one todo)._ A `§X` reference
  is fine as a POINTER to a doc you also link, but the todo's first line must ALSO state the actual fact/finding that
  section stands for — never make the fact's meaning depend on a reader having the other doc open.
- **State the literal action, not a doc-shaped verb** _(finding E: "Absorb `<doc>.md`" was ambiguous between "do the
  engineering work that doc describes" and "fold its text into this plan" — very different tasks)._ Avoid
  `absorb`/`incorporate`/`handle`/`address` as the verb of a todo; write the literal action ("execute the fix in
  `<doc>`" or "merge `<doc>`'s open todos into this track").
- **Delete-risk tagging must be consistent within one plan** _(finding F: one plan had a prod-GCS-deleting todo tagged
  plainly while a sibling delete todo in the same doc was `[OPERATOR]` + cited the delete-safety protocol — reads as an
  oversight, not a decision)._ Any todo that deletes/overwrites prod data (GCS objects, manifest rows, DB rows): tag
  `[OPERATOR]` and cite `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` UNLESS you state explicitly why this
  specific delete is lower-risk (e.g. genuinely soft-delete/reversible) — silence reads as an oversight, not a ruling.
- **State the definition-of-done** _(finding G: several todos stated the problem/goal but not what evidence proves it's
  done — e.g. "wire the dependency gate for real" with no acceptance check)._ End each todo (or its first continuation
  line) with the concrete evidence a done-claim must cite — a passing check, a specific query returning zero rows, a
  build ID, etc. — not just the goal.
- **Before writing a NEW todo, check the doc doesn't already show it done** _(finding C: a later section of the SAME
  plan sometimes already recorded a todo's resolution — e.g. a Progress Log entry — while the checkbox up top stayed
  unflipped; a fresh reviewer skimming top-to-bottom re-investigates an already-solved problem)._ When editing a plan,
  grep the rest of the doc for the todo's subject before adding or leaving it open.
- **A digest of ANOTHER plan's todos is never real checkbox syntax** _(finding H, 2026-07-24: a coordination/umbrella
  plan that lists "referenced, not duplicated" todos from other plans for discoverability MUST NOT format those digest
  lines as `- [ ] [TAG] P<n>. ...` — verified via direct code read of `regen_backlog_from_plan.py`'s `_UNCHECKED_RE`,
  which is indentation-agnostic, so a NESTED digest checkbox is parsed exactly like a real one. If this plan is ever
  flipped to `assigned_vm: planning`, regen would dispatch the digest as a stub task duplicating the SAME work already
  tracked — with full context — in the referenced plan, going stale the moment that plan's real todo changes, and very
  likely blowing the 10-100 todo cap below. Format a digest line as `- **[TAG] P<n>.** ...` (bold, no `[ ]` brackets) —
  same information, same visual weight, structurally un-ingestable. This is a discoverability index, not a second copy
  of the dispatch surface; the referenced plan's OWN file is still the one place that todo actually ships from)._
- **A plan gated on a FORKED-OUT child's work states it as `depends_on` + `gate_on_depends: true`, not just prose**
  _(finding I, 2026-07-24: splitting an over-cap plan into a coordination-index parent + child plans is now a routine
  pattern — see `check_line_caps.sh`'s hard 1000L cap (no exemption; a genuinely large hub belongs in `plans/epics/`,
  which gets its own flat 2000L cap, not a free pass while still in `plans/active/`) — and it is easy to leave the real
  ordering constraint as header prose only, e.g. "Track 5 (C-GREEN gated on T1→T3)" after Track 1 moved to a separate
  child plan. Prose alone is invisible to the dispatcher: if the parent is ever flipped to `assigned_vm: planning`, the
  gated track's todos would be dispatchable immediately, concurrently with the child's still-open prerequisite work)._
  The SAME edit that forks a section out to a child plan must ALSO add that child's slug to the parent's `depends_on:`
  frontmatter (+ `gate_on_depends: true` if the parent has any remaining todo that genuinely can't start before the
  child finishes) — do not defer this to a follow-up.
- **Don't let a plan's own history balloon past cap — extract completed Progress Log sections AS YOU GO, don't wait for
  a remediation pass** _(finding J, 2026-07-24: `plan_line_cap_remediation_2026_07_23.md` had to clean up 30 plans that
  had silently grown to 1000-4780 lines, almost entirely from accumulated, fully-closed, dated Progress Log entries
  nobody extracted along the way — the same failure repeating one plan at a time is exactly what let the backlog
  reach 30. `check_line_caps.sh` (soft warn >500L / hard fail >1000L for a normal plan, hard fail >2000L for a REAL epic
  in `plans/epics/` — NO other exemption, `umbrella: true` no longer means anything, 2026-07-24 ruling) is now a REAL
  hard gate in `run_hygiene_sweep.sh` — both the corpus-wide sweep (a shrinking-ratchet baseline,
  `line_caps_baseline.yaml` — no NEW over-cap plan/epic tolerated) and the prek `--precommit` fast path (an absolute
  per-staged-file bar: if you're already editing a plan or epic that's over its cap, split/trim it before that commit
  lands, same as the frontmatter/todo-format gates next to it)._ When a Progress Log entry is fully closed (every todo
  it covers is `[x]`, nothing references it as still-open), don't leave it inline forever — once your plan crosses
  ~500L, extract the oldest fully-closed dated section(s) verbatim into an archive-bound `<slug>_history_<date>.md`
  (`status: complete`, `nature: record`, 0 open todos, lives in `plans/archive/2026_07/` or the current month) and leave
  a one-line pointer behind. This is cheap (minutes) done incrementally; it is expensive (a dedicated remediation plan)
  done as a 30-file backlog.
- **Every AG consolidated-closeout plan carries a 3x checkpoint cadence for each of the 5
  `data-pipeline-check-{is, mtds,mdps,features}` skills + `/data-pipeline-reconciliation`** _(finding K, 2026-07-24:
  `data_pipeline_e2e_milestones_gate_2026_07_24.md` §11 found execution reality varying sharply across the 5 AGs — defi
  and cefi had ZERO real RUN-todos for `-is`/`-mtds` despite both skills already supporting their shard atoms, and no
  doc anywhere stated the cadence was even expected)._ For each of the 4 check skills + reconciliation, a
  consolidated-closeout plan should carry 3 distinct DATED run checkpoints: a pre-backfill baseline run, a mid-backfill
  spot-check, and a post-backfill final gate. A todo that only ever ran the skill once, or references the skill by name
  without a dated run, does not satisfy this — cite the actual run (report path / dispatch_id / date) as the
  definition-of-done, same as any other evidence-backed completion claim.
- **A heading or bold/parenthetical span must close every bracket on the SAME physical line it opens on — never split
  across a blank line** _(finding L, 2026-07-24: an adversarial verification pass on
  `data_pipeline_e2e_milestones_gate_2026_07_24.md`'s distribution found a new `## MVP universe` heading whose
  parenthetical annotation opened `(gate-audit §14, 2026-07-24: ...` then, after a blank line, closed on its own
  orphaned line as a floating `)` — no existing check (mechanical or LLM) caught it because it's neither a todo-line
  rule nor a cross-doc contradiction, just a single doc's own markdown breaking mid-render)._ Before finalizing any
  heading/`**bold**`/parenthetical, check the raw line breaks (`grep -n`, not the rendered preview) — every `(`,
  `` ` ``, `**`, and `[` it opens must close before the next blank line or the next heading, whichever comes first.
- **A newly-written claim must not contradict itself in the same sentence, or contradict a fact/formula the SAME doc
  already shows elsewhere** _(finding M, 2026-07-24: the same verification pass found a "symmetric-inclusion invariant"
  paragraph that asserted `all_shards_coverage` "correctly includes it in both" and then, three words later, qualified
  that with "(denominator only...)" — directly contradicting itself and the formula shown two paragraphs above it)._
  Before shipping a paragraph that states a rule/invariant/formula, re-derive it against any example or formula the SAME
  doc already shows and confirm they agree; re-read the sentence once as a skeptic looking for the word that contradicts
  the clause right before it, not just for typos.
- **Before writing a recovery/backfill script, live-probe that the data source still exists** _(finding N, 2026-07-25:
  the worker on `sports_satellite_ao_dispatch_batch2-033` organically checked that the source GCS bucket was still
  reachable before writing STEP 1's script rather than trusting the plan's stale-as-of-authoring premise — the plan it
  was executing had tracked ~550,062 rows as recoverable for 8 days after the bucket had actually been deleted;
  `recovery_plan_source_liveness_probe_gap_2026_07_25.md`)._ A recovery/backfill todo's first step should confirm the
  named source (bucket/table/API) is still live, not assume the plan's authoring-time premise still holds.
- **Every AO-eligible todo containing a GCS delete/`--apply` mutation or a VM launch must be explicitly self-justified
  or operator-gated** _(finding O, 2026-07-25: a scoped `/plan-reconcile` pass across all 5 AGs' AO-dispatch batches
  found 8 of ~15 batch docs contain a delete/`--apply` operation and 5 contain a VM launch, with no systematic check
  that each is correctly tagged — only that SOME `[OPERATOR]` tag existed somewhere in the doc)._ Such a todo must
  either (a) state inline why it's a safe, already-established idempotent pattern (e.g. "copy → crc32c-verify → delete",
  the same shape used elsewhere in this doc family) needing no operator gate, or (b) carry `[OPERATOR]` + cite the
  delete-safety protocol / the exact approval command. A todo with neither is a real gap, not a style nitpick.
  Mechanically pre-flagged (soft) by `scripts/plan-hygiene/check_delete_vm_launch_gating.sh`; judged for real by
  `/plan-reconcile`'s AO-dispatch-readiness hunter (this is a content-judgment call, not a regex-decidable one).
- **A todo that resumes/restarts a paused writer must check for a sibling plan/issue fixing a bug on the SAME data path
  first** _(finding P, 2026-07-25: the operator ruled on exactly this — `defi_consolidated_closeout_2026_07_18.md`'s
  "resume the paused DeFi crons" todo would have resumed 3 collectors whose subgraph query bug a sibling plan existed
  specifically to fix; resuming blind would keep writing the same bad rows the sibling plan was created to stop)._
  Before drafting/dispatching a resume-a-writer todo, grep for any sibling doc fixing a defect on the same
  venues/writers/tables. If one exists and hasn't shipped: either gate the resume on it
  (`depends_on`+`gate_on_depends`), or split into affected-vs-unaffected scope — never resume everything
  unconditionally.
- **Finding O's `[OPERATOR]`-tag bar is PRIOR APPROVAL + VALIDATION, not raw scale/irreversibility alone** _(finding Q,
  2026-07-25, operator ruling: a cefi Track-1 live financial-tick migration and a `catalog.parquet` rebuild — both
  large, prod, hard-to-reverse — were ruled self-justifying with NO `[OPERATOR]` tag needed, because the migration was
  already explicitly operator-approved in principle AND every constituent script was individually dry-run-validated to a
  proven-safe outcome)._ Don't reflexively tag everything large/irreversible — check whether prior explicit approval
  - validation already exists; if so, state that inline as the justification (finding O's option (a)) rather than
    defaulting to `[OPERATOR]`.
- **Finding O now has a third self-justification path (c) — "reversibility-verified"** _(finding T, 2026-07-26, operator
  ruling: AO kept blocking on the operator for prod-bucket deletes even where the target had a real GCS Soft Delete
  recovery window, forcing the operator to answer and then separately ask a different, locally-supervised agent to
  actually run the already-approved command — pure toil with no safety benefit once the delete is genuinely
  reversible)._ A GCS delete todo may skip `[OPERATOR]` by citing a FRESH, same-run
  `gcs_bucket_soft_delete_retention_seconds(bucket)` check returning `>= 604800` (7 days) — state the actual queried
  value inline, per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a. **Verified, not asserted**: a
  2026-07 sports-plan todo self-justified on soft-delete WITHOUT querying the real policy — that is now the canonical
  negative example this finding exists to prevent. Path (c) never applies to a whole-bucket destroy (always
  `[OPERATOR]`-gated regardless of bucket policy) or when the fresh check returns below the threshold — those still need
  `[OPERATOR]`, but citing §3a's approve-executes flow (a FINAL operator answer authorizes the SAME worker session to
  execute immediately) rather than the old assume-a-human-runs-it-elsewhere framing.
- **`[OPERATOR]` is for genuine ambiguity or an external dependency — not reflexive caution on scale/prod/hard-to-
  reverse** _(finding U, 2026-07-27, operator ruling: a corpus-wide audit of 65 active plans/issues found dozens of
  `[OPERATOR]` tags on todos that were actually clear-scope and either read-only or reversibility-qualifiable — the gate
  had drifted from "genuine judgment call" to "anything that touches prod," defeating the point of unattended dispatch:
  the resolution was always pasting the already-approved command into an agent anyway)._ Positive test — tag
  `[OPERATOR]` ONLY when the todo is genuinely one of: **(i)** a business/spend/value judgment with no data-derivable
  answer (e.g. "activate a paid third-party tier", "accept this compliance risk") — a _standing_ answer already on
  record (e.g. a dated operator-decision-ledger entry) is NOT a live gate, cite the ruling and leave it as a record,
  don't re-ask; **(ii)** work that structurally requires a credential/access only a human holds (an API key, an OAuth
  grant) — tag as a credential-ask, not a blanket `[OPERATOR]`, once the credential exists the todo is dispatchable;
  **(iii)** a whole-bucket destroy or a target that fails a fresh reversibility check (finding T). Everything else
  defaults to NOT gated: **read-only/audit/census todos** ("count how many X need migration", "identify which rows are
  affected" — write a NEW artifact, touch nothing existing) can never hurt anything and must never carry `[OPERATOR]`,
  regardless of corpus size or bucket sensitivity; a **named-bucket, named-scope delete/migration/`--apply`** qualifies
  under finding T once reversibility-verified. **If the target bucket's soft-delete retention is missing or below
  604800s, that is not itself a reason to gate the todo — enable it**
  (`gcloud storage buckets update gs://<bucket> --soft-delete-duration=7d`, a one-line, low-risk config change, same
  action already taken for `instruments-store-sports-prd` 2026-07-26) **and re-check, THEN cite finding T** — do not
  default to `[OPERATOR]` just because the fix hasn't happened yet; make the fix part of the same todo.
- **A silent, hard-to-detect correctness-regression risk in shared fleet-wide code is a DIFFERENT class from finding
  T/U's reversibility carve-out — gate it on test coverage, not a human's judgment** _(finding V, 2026-07-27, operator
  ruling: a proposed `ManifestWriter` per-VM-shard caching optimization touched concurrency-critical code with a
  documented history of a real lost-entries bug; unlike a GCS delete there is no soft-delete safety net if a subtle bug
  ships — the risk is silent data loss across every concurrent writer, not something recoverable within a known
  window)._ This is NOT a business/value judgment (finding U (i)) — a human's opinion doesn't make the code more correct
  — so it does not default to `[OPERATOR]` either. Instead, state an EXPLICIT strengthened done-when: any existing
  regression suite covering the invariant at risk must stay green, AND a NEW adversarial test must be added that
  specifically exercises the failure mode the change could reintroduce (here: a second writer mutating the shard's GCS
  generation mid-flight, proving the fallback path actually catches it) — `quality-gates.sh` + that new test are the
  real safety net, the same bar every other shared-library change in this codebase already meets. Reserve actual
  `[OPERATOR]` for this class only when no test can meaningfully exercise the risk at all (e.g. a genuinely unobservable
  production race) — state that explicitly if so, don't default to it out of general unease.
- **A permission/IAM gap on the orchestrator's OWN cloud identity is never `[OPERATOR]`/`BLOCKED-CREDENTIALS` — grant it
  directly** _(finding W, 2026-07-27, operator ruling: a todo asking to grant `unified-trading-sa` Cloud Scheduler read
  access sat gated for an hour before the operator had to point out this is the exact class of thing the session had
  just spent hours making self-service — "the whole thing we just did")._ `unified-trading-sa` (GCP) and
  `uts-orchestrator-epic-role` (AWS) both hold IAM-self-management permission; every AO worker already runs AS these
  identities ambiently (no separate credential setup). A todo naming either identity + a specific missing role is a
  same-class fix as finding T's reversibility check: grant the specific role (never blanket
  `Owner`/`AdministratorAccess`), re-verify the actual capability live (call the real API, not just the IAM policy
  dump), cite both, done. See `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` for current
  grants + exact commands. Reserve `BLOCKED-CREDENTIALS` for a gap on a genuinely DIFFERENT identity this worker cannot
  assume.
- **When splitting an over-cap plan, correctness beats file count** _(finding R, 2026-07-25, operator ruling: asked
  whether to fork every Track with a real sequential/gating constraint into its own child+finalize even if small, vs.
  merge related Tracks to reduce file count — ruled "correctness over file count")._ Give any Track/section with a real
  ordering constraint its own child (+ mandatory finalize per finding already below) even if small — merging it into a
  broader plan either wrongly serializes that plan's unrelated items behind the constraint, or leaves the real ordering
  dispatcher-unenforced. File count is secondary to keeping every real constraint machine-enforceable via
  `depends_on`/`gate_on_depends`.
- **A todo flagging its own scope as unclear must stay non-dispatchable until the operator names it — never guess**
  _(finding S, 2026-07-25: a cefi todo's own text said "SCOPE UNCLEAR" — it wanted a multi-phase external plan "done"
  before a migration but never said which phase(s); the operator had to name the exact phases (1, 1b, 1c, 2, 5) before
  it could become real work)._ When a design/split pass finds a todo like this, leave it explicitly flagged
  non-dispatchable (not folded into any child) until scoped — a scope-undefined todo becomes an unbounded judgment call
  for whoever executes it, exactly what the dispatch-scope-eligibility rule bans.
- **A resumable script's `--report`/checkpoint file goes in a shared, task-id-keyed, durable location — never a
  per-slot-per-session scratchpad** _(finding X, 2026-08-06,
  `plans/active/issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md`: the same resumable-migration todo
  was independently dispatched to 3 concurrent slots, each writing its own `--report` checkpoint under its own
  `/home/ubuntu/.claude-configs/orch-slot-*/cc-tmpdir/**/scratchpad/` — none could see the others' progress, so two of
  the three slots re-derived 60+ date-shards' worth of already-done work as pure GCS-read cost, and the first slot's
  140-day head start was nearly lost entirely when its session ended without a closing Progress Log entry)._ When a
  todo's brief names a `--report`/checkpoint/resume-log flag, its checkpoint path MUST be a location every future worker
  that picks up the SAME task id can find and resume from, not an ephemeral per-session tmpdir:
  - **If the script already writes to a GCS bucket** (the common case for a data-migration/backfill script): put the
    checkpoint at `gs://<the-bucket-it-already-writes>/_ops/checkpoints/<task_id>.jsonl` — bucket-colocated with the
    data it tracks, durable, and readable by any slot regardless of host. (A live precedent for the bucket-colocated
    half of this pattern already exists — `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s 4b-i todo started
    uploading its merged checkpoint to `gs://<bucket>/_ops/prediction_trades_migration_checkpoint_<date>.jsonl`
    mid-incident; this finding is what makes the naming task-id-keyed instead of date-keyed, so a SECOND worker can
    locate it deterministically from the task id alone rather than having to know which date a prior worker happened to
    pick.)
  - **If the script has no natural GCS home** (a local analysis/audit driver): put it at
    `${WORKSPACE_ROOT}/.ao_checkpoints/<task_id>/<name>.jsonl` — `WORKSPACE_ROOT`
    (`/home/ubuntu/unified-trading-system-repos` on this deployment) is the SAME absolute path on every slot on this
    single-VM architecture host, so a path directly under it (never under a `.tabs/<N>/` slot subtree, and never under a
    per-session `cc-tmpdir/` scratchpad) is genuinely shared across slots and survives any one session ending.
  - State the resolved path literally in the todo brief — not `<path>`/`<checkpoint>`/`<scratchpad>` — so a cold-start
    worker knows exactly where to look before re-deriving anything. Example brief using the convention:
    `- [ ] [DATA] P2. Resume scripts/some_migration.py --apply --report gs://my-bucket/_ops/checkpoints/my-migration-task-007.jsonl (idempotent per-cell; pull this checkpoint first — do not restart from day 0). Repo: some-service. Done-when: all N shards report 0 anomalies.`

---

## 4. AO-DISPATCHED plans — STRICT rules

- **10–100 todos** (raised from 10-20, operator ruling 2026-07-23). Fewer is fine; group RELATED items so we don't get
  hundreds of tiny plans. A plan over 100 todos is banned for dispatch — it bloats the backlog and couples unrelated
  work. _(LOCAL plans are exempt.)_
- **Intra-plan concurrency is REAL and often intended — the plan is your unit of parallelism** _(corrected 2026-07-21,
  verified via code read of `regen_backlog_from_plan.py` + `dispatch.py`: single-agent stickiness is NOT enforced —
  regen sets no slot affinity, `_task_is_routable_to` returns True for any free slot. The old "one plan = one agent /
  split for ALL parallelism" framing was aspirational and is superseded)._ A plan's same-priority todos are each
  **independently dispatchable and run CONCURRENTLY across whatever workers are free** unless you gate them. This is a
  FEATURE — e.g. one plan with 5 independent `[REVIEW]` todos ("babysit this backfill VM", "confirm each un-downloadable
  item is genuinely absent upstream", …) fans out to 5 agents at once. **The one hard rule: concurrent todos MUST touch
  different files** (same file → two workers collide — banned by multi-agent safety). So, per plan:
  - **Independent tasks on different files → leave them ungated** (the default). Free throughput.
  - **A real dependency chain, OR tasks that share a file → `sequential: true`** (serialises the WHOLE plan).
  - **Partial parallelism** (some tasks parallel, THEN a step gated on them) is **NOT expressible inside one plan** —
    **SPLIT**: parallel work in Plan A; the gated step in Plan B with `depends_on: [A]` + `gate_on_depends: true`. Do
    NOT reflexively set `sequential: true` — it forecloses ALL intra-plan parallelism; use it only when tasks genuinely
    chain or share files.
- **An AUDIT is its own plan** (its findings shape later phases — keep it separable).
- **Bounded outcome only — no judgment calls in a todo** _(operator ruling 2026-07-23)._ A todo is eligible for
  `assigned_vm: planning` only if its outcome is DETERMINABLE by the dispatched worker alone: a checkable fact, a scoped
  code change, an audit with a stated done-when. **Not eligible**: open-ended research/design work whose answer isn't
  already decided — "figure out how the data pipeline should look for features" has no defined target and no way for an
  isolated worker to know when it's done; that's a human decision wearing a todo's clothes. **Audits ARE eligible when
  precisely scoped** — "does X match Y" / "count instances of Z" is a determinable fact, unlike "figure out what X
  should be"; scope, not the word "audit," is what makes it dispatchable. Resolve the judgment call FIRST — as a
  LOCAL/human plan or an interactive session — and write the properly-scoped AO todo against that decision's OUTCOME,
  never against the open question itself. SSOT: `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`
  § "Dispatch-scope eligibility".
- **Draft-gated phase chains** — for multi-phase work, ship each phase as a SEPARATE plan: the current phase is
  `status: active`, later phases are `status: draft` (regen skips drafts, so an unfinalised phase never floods the
  backlog); the phase's LAST todo finalises the next phase's todos and flips it `draft`→`active`. _[ACTIVE NOW: draft =
  not ingested; active→draft prunes queued tasks.]_ Distinct from `depends_on` + `gate_on_depends: true`, which INGEST
  the downstream and machine-hold it until upstream is done — use that when the downstream is already finalised.
- **Ordering + how prerequisites ACTUALLY work** _(verified in `regen_backlog_from_plan.py` 2026-07-21)._ Each todo
  becomes backlog task `<plan-slug>-NNN` with `plan_order` = its file position; tasks dispatch by
  `(tier, priority, plan_order)`. **Ordering controls DISPATCH order, NOT completion — same-priority todos still run
  concurrently.** A hard "finish-before" is a **prerequisite**, and there are ONLY TWO ways to create one from a plan —
  **there is NO per-todo prereq syntax; regen never parses prereqs from todo text** (so writing `(prereq: …)` in a todo
  line does nothing — corrected 2026-07-21; the earlier "add explicit `prereqs.completed_tasks`" advice was wrong,
  `RULES.md` confirms regen does not derive per-task prereqs from todos):
  1. **`sequential: true`** → `_wire_sequential_prereqs` sets each task's `completed_tasks` to its immediate predecessor
     by `plan_order` → the whole plan is a serial chain.
  2. **`depends_on: [plan-slugs]` + `gate_on_depends: true`** → `_wire_gate_on_depends_prereqs` makes every task of THIS
     plan wait on every task of the named upstream plan(s). **`depends_on` ALONE does NOT gate dispatch** (documents
     ordering + gates archival only). Enforcement: `dispatch.py::_prereqs_met` holds a `queued` task until all its
     `prereqs.completed_tasks` are `done` (and any named `prereqs.prerequisites` conditions are `true`). NEVER hand-edit
     `backlog.yaml` to add prereqs — author the frontmatter; the backend derives them.
- **Verify an "Ordering note" before asserting it's safe.** For multi-repo/multi-step DAG plans (audit→fix→verify,
  migrations), a note claiming step N can land before step M is a CORRECTNESS CLAIM, not a convenience aside — don't
  reason from the diff's code shape alone (e.g. "this branch doesn't read X" can still break at runtime if a live caller
  feeds it X's current state). Before writing the note, actually make the ISOLATED step-N diff (with M not yet landed)
  and run it through `bash scripts/quality-gates.sh`; only write "safe to land before M" if that run is green. If it
  turns out unsafe, encode the REAL dependency as `sequential: true` (intra-plan) or `depends_on` +
  `gate_on_depends: true` (cross-plan) so the backlog dispatcher enforces it — a human-readable "🔴 BLOCKED, don't
  dispatch" banner is NOT a dispatch gate; a worker picking up the plan cold can still claim the blocked todo before
  ever reading the banner. **Caveat (corrected 2026-07-15, plan-reconcile: confirmed via code read of
  `_parse_open_todos`/`task_still_dispatchable` in `regen_backlog_from_plan.py`, see
  `mtds_available_at_cross_asset_backfill_2026_07_13.md` Progress Log 2026-07-14)**: `sequential: true` only orders
  same-priority **ingested/dispatchable** todos by file position — a todo excluded from ingestion via a
  `BLOCKED-<TOKEN>`/`[OPERATOR]`/`_(stretch, optional)_` marker (§3) does NOT count as "the predecessor," so if that
  excluded todo is first in file order, the next todo dispatches immediately regardless of whether the excluded one is
  actually resolved — so do NOT place a non-dispatchable todo (a `[OPERATOR]` decision, a `BLOCKED-` gate) as the FIRST
  link in a `sequential` chain expecting it to hold the rest; it won't. Restructure so the true gate is a dispatchable
  todo, or move the pre-gate work into its own plan the downstream `gate_on_depends` _(corrected 2026-07-21 — the
  earlier "use `prereqs.completed_tasks` instead" was not actionable: authors cannot write per-task prereqs from a plan
  file; see the Ordering bullet above)_. Case study: `coinbase_bare_name_migration_2026_07_06.md` Step S2's "safe before
  S3" note was disproven by an actual QG run — see
  `plans/active/issues/coinbase_bare_name_migration_s2_ordering_2026_07_10.md` for the failure + the `sequential: true`
  fix.
- **Multi-role in one plan — SHIPPED** _(corrected 2026-07-21, was "[ROLLING OUT: today role is the plan-level
  `assigned_role` for ALL tasks]"; verified via code read of `_TAG_TO_ROLE` + `_task_role_from_tag` in
  `regen_backlog_from_plan.py` — per-task routing is live)._ Each todo routes to the role named by its `[TAG]`
  (`[BACKEND]`→backend_engineer · `[UI]`→ui_developer · `[REVIEW]`→review · `[DATA]`→data_engineering ·
  `[INFRA]`→infra); an unmapped/absent tag falls back to the plan's `assigned_role`. So a mixed backend+UI+review plan
  routes each task to the right role — no need to split by role. _(Dispatch nuance: a generic worker with no declared
  `slot_role` can still claim any task, so role is a correct STAMP but only GUARANTEED off-role where role-declared
  slots exist.)_
- **Model tier — sonnet/opus only (default).** Set `model_tier: opus-required` for hard reasoning; otherwise the role's
  default (sonnet) applies. **`fable-required` (Fable 5) is OPERATOR-REQUEST-ONLY** — never assign it unless the
  operator DIRECTLY asks for Fable (it is for the hardest / longest-running interactive work — overkill for routine
  dispatch). Effort: Haiku has NO effort levels (thinking on/off only); sonnet/opus/fable support `--effort` low→max.
  _[ROLLING OUT: fable spawn + per-model effort.]_
- **Every AO-dispatched plan needs a gated finalize plan (operator ruling 2026-07-24).** Alongside any
  `assigned_vm: planning` plan, author a companion `<plan-slug>_finalize_*.md` (`depends_on: [<plan-slug>]` +
  `gate_on_depends: true` + `sequential: true`) whose job is: (1) reconcile every completed todo's evidence back into
  its TRUE source doc(s) — either the plan's own checkboxes if self-contained, or every named source doc's corresponding
  checkbox if the plan was a batch-style extraction from other docs (do not trust a source doc's own copy of the
  evidence line — re-verify the cited commit exists); (2) re-check any deferred/excluded-at-authoring-time follow-up
  item to see whether its gate (a sibling todo landing, a human/operator decision) has since cleared, and spin it into a
  new tracked todo/plan if so; (3) run the standard 6-step archival ritual on the now-fully-done plan, including the
  corpus-wide referrer-path fixup; **(4) for a batch-style extraction plan, also check each SOURCE doc touched by (1) —
  if reconciling its checkbox(es) back left it with zero open todos, that source doc is now ALSO an archival candidate
  and needs the same 6-step ritual, not just its own checkbox flip.** Gap found + fixed 2026-07-26
  (`autonomous_session_operator_decisions_2026_07_25.md` entry #17): a finalize plan that only closes ITS OWN plan while
  leaving a now-fully-done source doc live and un-archived caused a real `run_hygiene_sweep.sh --ci` hard-fail (10
  violations, baseline 0, auto-remediated via PR #1545) — the omission is in this rule, not any one AG's plans. This is
  what closes the loop — without it, a batch extraction plan ships its own todos but leaves every source doc's checkbox
  stale and the plan itself never archives. Precedent: `sports_closeout_batch1_ao_ready_2026_07_24.md` /
  `sports_closeout_batch1_finalize_2026_07_24.md`, `sports_satellite_ao_dispatch_batch2_2026_07_24.md` /
  `sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`. Skip only for a plan that IS ITSELF already a finalize
  plan (no infinite regress) or a genuinely single-todo plan where archival is trivial enough to fold into that one
  todo's own done-when. Enforced (ratchet-mode, warn-only, wired into `quality-gates.sh`) by
  `scripts/quality_gates/check_finalize_plan_coverage.py`. **Create-time idempotency guard (2026-08-11)**: before
  authoring the companion, run
  `python3 scripts/quality_gates/check_finalize_plan_coverage.py --check-parent <plan-slug>` and refuse if the parent is
  already gated by an existing finalize plan — keyed on the `depends_on` relationship, never the filename shape (two
  `_finalize*` files can collide for one parent; `duplicate_finalize_plans_created_for_one_parent_2026_08_06.md`).
- **Finalize-plan todos: give the "reconcile source docs" todo and the "archive this plan" todo DIFFERENT `[TAG] P<n>.`
  prefixes (found 2026-07-31, `sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md`).** Both
  `batch2_finalize`/`batch3_finalize` authored these as `[DOC] P1` for BOTH todos — harmless until the self-archival
  todo lands in the SAME commit as its own `git mv`, at which point the AO done-gate's tag+priority disambiguator
  (`server/verify.py::_brief_is_checked_by_tag_in_text` — the fallback for exactly this "flip + archive in one commit"
  shape) finds 2 same-tag-priority checked lines and fails CLOSED (refuses `/done` rather than risk confirming the wrong
  todo) — a real `/done` rejection this exact session hit and had to retag around after the fact. Pick distinct
  tags/priorities at authoring time (e.g. `[REVIEW]` for reconciliation, `[DOC]` reserved for the archival todo alone)
  so this never collides.
- **NEVER hand-edit `backlog.yaml`.** Author plans; the backend derives the backlog.

---

## 5. Safely editing a plan whose tasks are already assigned to AO

_[SHIPPED 2026-07-07 (was: "ROLLING OUT ... edits to existing todos do NOT propagate" — corrected 2026-07-14,
doc-reconciliation vr2#10): `ao_dispatch_correctness_regen_reconcile_2026_07_07.md` Phases 2-5 all landed
(`ao@ff6100ad`+`c6a31ed6`+`f976b6e4`+`07035aba`), "ALL 3 ROOT CAUSES FIXED (RC-1/RC-2/RC-3)" per that plan's 2026-07-07
Progress Log — the table below is now the LIVE behavior, not a future target. **Caveat (known bug, see
`issues/backlog_regen_drops_handtuned_prereqs_2026_07_12.md` Defect B)**: `_reconcile_task_fields()` re-derives
`priority` from the plan's current `P<n>` tag on every regen tick with no "was this hand-overridden" check, so a
manually-set `priority` override on an already-derived task reverts on the next tick as long as the todo line is still
open — do NOT rely on a hand-tuned field surviving regen; edit the plan's `P<n>` tag itself instead.]_

Current behavior (SHIPPED 2026-07-07) — what the backend does to a task by its state:

| You change…              | `queued` / `blocked`   | `dispatched` (in-flight)                                  | `done` |
| ------------------------ | ---------------------- | --------------------------------------------------------- | ------ |
| **model / role / prio**  | updated in place       | adapt-in-place (retier stop-and-`--resume` if higher)     | no-op  |
| **reword a todo's text** | old removed, new added | old task `cancelled` + scoped-revert; new text = fresh    | no-op  |
| **remove a todo**        | pruned from backlog    | `cancelled` + scoped-revert (NOT deleted); UI shows count | kept   |

Scoped revert = the worker reverts ONLY its own task's touched files (`git restore`) — never whole-branch, never
`reset --hard`.

---

## 6. Safeguards (ALWAYS — these are battle-tested)

**Before you change files** — record what you'll touch and make a reference backup (do NOT switch to it):

```bash
FILES_TO_TOUCH="path/to/file1.py path/to/file2.py"
git branch "backup-before-<task>-$(date +%s)"   # reference point only
# Recovery — ONLY the files you touched:
#   git restore --source=<backup-branch> -- $FILES_TO_TOUCH
```

**NEVER**: `git reset --hard` / `git checkout <branch>` / `git clean -fd` a dirty tree · revert the WHOLE branch (other
agents share the repo — only revert your own files) · skip tests or add `|| true` / `@pytest.mark.skip` without a
documented reason · `# type: ignore` without fixing root cause · `Any` · `.get("k", {})` (fail loud) · hand-edit
`backlog.yaml` · auto-commit from an AO worker without reporting back.

**ALWAYS**: fix root causes, not symptoms · keep the list of files you touched (for a scoped revert) · test frequently ·
commit + push + flip the plan checkbox in the SAME turn (`docs(plans):` prefix) · cite evidence for a done claim
(`<repo>@<sha>` + a resolving build/run).

---

**This template is a LOCAL doc (not ingested). Copy §2 into a new `<slug>_<YYYY_MM_DD>.md` in `plans/active/` to
start.**

## Progress Log

- **context-scout 2026-08-03**: re-verified context_scope (5 entries) — still accurate, no changes needed.
- **context-scout 2026-08-03 (re-scout)**: refreshed context_scope (6 entries) -- added `dispatch.py`
  (agent-orchestrator/server), the other module §4's prerequisite mechanics are verified against per the doc's own
  summary, alongside the already-present `regen_backlog_from_plan.py`.
- **2026-08-03 (interactive session)**: Added §2a ("Populate `context_scope` yourself at authoring time") — an author
  who runs the pre-task conflict-check grep for a new doc should capture that grep into `context_scope` immediately,
  including a fingerprint-based cross-reference pass (grep for the doc's own distinctive evidence literals, not just
  topic keywords), rather than leaving the field empty until the next hourly `/context-scout` sweep. Prompted by a real
  gap: `odds_api_key_quota_exhausted_4_days_after_provisioning_2026_08_02.md` was filed without linking to
  `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`, which had already recorded the identical exhaustion evidence
  a day earlier — the next worker spent ~215k tokens rediscovering it. Companion change:
  `cursor-configs/skills/context-scout/SKILL.md` Phase 1 step 4a (fingerprint cross-referencing, applies to the
  scheduled sweep too) and a `PLAN_FORMAT.md` `context_scope` comment pointing here. (repo: unified-trading-pm,
  docs-only, no code changed)
- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — this IS the plan-authoring template/guide itself (own banner
  above: "This template is a LOCAL doc (not ingested)"), 0 tracked `- [ ]` todos. Structurally never AO-dispatchable and
  never archivable while it remains the live authoring SSOT every plan/agent cites.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-confirmed after the 2026-08-06 finding-X edit (shared
  task-id-keyed checkpoint convention addition). Still the plan-authoring template/guide itself, still 0 tracked `- [ ]`
  todos. Structurally never AO-dispatchable and never archivable while it remains the live authoring SSOT.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
