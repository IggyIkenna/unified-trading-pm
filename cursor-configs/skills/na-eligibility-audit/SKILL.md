---
name: na-eligibility-audit
description: >-
  Audit the `assigned_vm: NA` plan/issue corpus (currently ~390 docs / ~1,370 open todos, tracked live via
  `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py`) for validity — is each doc's own NA self-classification
  still correct, and is its content still true? Per doc, verdicts one of: **KEEP-NA valid** (genuine
  operator-gated/judgment/investigation work, evidenced — the majority, expected), **KEEP-NA-STALE** (content already
  duplicated verbatim in an active `assigned_vm: planning` doc — a checkbox-citation fix, not a reclassification),
  **RECLASSIFY** (bounded, deterministic-outcome work simply defaulted to NA and never assessed — flip to `assigned_vm:
  planning` after the shared conflict-check clears it), or **ARCHIVE** (fully resolved/moot). Promotes the one-off
  `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` plan's proven methodology into a repeatable,
  tranche-parameterized skill (same 10 tranches `/ag-closeout-audit` uses, `ui` included) with an incremental mode (skip
  docs already verdicted since their last edit — a daily full re-read of ~390 docs is not the design) and a standing
  size-ratchet report (`check_na_corpus_ratchet.py`) so the backlog is visibly shrinking-or-flat, never silently
  growing. **Explicitly does NOT hunt orphaned docs** (no active plan covers them at all — that's `/ag-closeout-audit`'s
  corpus) and does NOT run the corpus-wide contradiction/ false-unchecked sweep (that's `/plan-reconcile`'s corpus) —
  this skill's population is already-owned NA docs specifically. Trigger on `/na-eligibility-audit [<tranche>]`, "audit
  the NA docs", "check if this NA plan can be reclassified", "fold NA work into AO dispatch", "is the NA backlog
  growing", "which NA docs are actually AO-eligible".
---

# /na-eligibility-audit — assigned_vm:NA validity + reclassification audit

Generalizes `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s proven multi-session methodology (77 docs
reclassified `NA → planning` across its first two sessions, ~65 more identified-and-triaged in a third) into a
repeatable, `/`-invocable, tranche-parameterized skill — the same treatment `/ag-closeout-audit` got for orphan
detection. Where that skill asks "is anything uncovered?", this skill asks a different question about a DIFFERENT,
population that in practice OVERLAPS `/ag-closeout-audit`'s: **"of the docs that already have an owner
(`assigned_vm: NA`), is that self-classification still correct?"** Operator ruling 2026-08-08 (ao round-5,
`na_and_ag_closeout_audit_population_overlap_2026_07_31.md`): `generate_ag_closeout_audit_candidates.py` deliberately
does NOT exclude `assigned_vm: NA` docs from its candidate population -- keep it that way, since a never-cited NA doc
might genuinely be a mis-tracked orphan this skill alone wouldn't catch. So an `assigned_vm: NA`,
`status: active`/`open` doc is NOT by definition safe from `/ag-closeout-audit` -- the two skills' populations can
legitimately claim the same doc, and the 4th conflict-check surface
(`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) is the load-bearing mechanism that
prevents a double-dispatch, not population disjointness. Sampling the NA population has repeatedly found it is a genuine
mix, not a monolith: real evidenced judgment work (majority), stale-but-harmless duplication, and genuinely
mis-defaulted AO-eligible content.

**Out of scope** (route there instead of duplicating): orphan detection with no active covering plan
(`/ag-closeout-audit`'s corpus); corpus-wide contradiction/false-unchecked-checkbox sweeps across the WHOLE corpus
regardless of `assigned_vm` (`/plan-reconcile`'s corpus, though its Phase 2 "done-but-unchecked" bar is the SAME
evidence bar this skill uses for a KEEP-NA-STALE verdict).

**Why RECLASSIFY volume is inherently low per run (2026-08-07 clarification, so this doesn't get re-derived from
scratch)**: `assigned_vm` flips at the WHOLE-DOC level, not per-todo, and the bar is that the doc's ENTIRE remaining
scope must be bounded/deterministic. A doc with 15 open todos where one item's operator question just got answered does
NOT become RECLASSIFY-eligible — the other 14 are usually still real judgment/design work, so the doc correctly stays NA
(confirmed live: a full 10-tranche, 373-doc run on 2026-08-07 found only 4 genuine whole-doc RECLASSIFYs). **This is not
the corpus's main unblock-to-AO pathway.** `/ag-closeout-audit`'s satellite-batch extraction
(`<topic>_satellite_ao_dispatch_batchN.md`) is — it pulls just the specific newly-actionable item(s) out of an NA-heavy
doc into their own small `assigned_vm: planning` doc without needing the WHOLE source doc to qualify. If a session's
real question is "why isn't previously-unblocked work reaching AO", check satellite-batch cadence for that topic before
assuming this skill's RECLASSIFY rate is the bottleneck.

## The verdict rubric (unchanged from the proven plan — do not re-derive a new one)

For each `assigned_vm: NA`, `status` ∈ `{active, open}` doc with ≥1 open todo:

1. **KEEP-NA, valid** — genuinely human/design/judgment/operator-gated work, content still accurate. Record a dated
   Progress Log line in the doc itself (`**na-eligibility-audit YYYY-MM-DD**: KEEP-NA, valid — <one-line why>`) so a
   future incremental run can skip it (see Phase 0). No other action.
2. **KEEP-NA, stale items** — some open checkboxes are superseded/decommissioned/already-done-elsewhere. Close those
   specific items with evidence (same HARD-evidence bar as `/plan-reconcile` Phase 2); doc stays NA otherwise.
   **Distinct sub-case (2026-08-07 finding, do not conflate with ordinary staleness)**: an item can have full HARD
   evidence of being shipped yet be genuinely un-flippable right now because the doc itself sits over its
   `/plan-reconcile` Phase 5 line-cap and the split-then-close sequence hasn't executed — the work is real and done, the
   checkbox mechanics are just gated. Do not classify this as GENUINE_WORK-remaining or as ordinary staleness; report it
   as a `/plan-reconcile` line-cap-split finding instead (that skill's Phase 5 owns the split), and leave the checkbox
   open with a note pointing at the blocking line-cap rather than closing it out of sequence.
3. **KEEP-NA-STALE (already-duplicated)** — the doc's own remaining open checkboxes describe work an active
   `assigned_vm: planning` doc already extracted verbatim (checkbox simply never got flipped to cite the extraction).
   Fix the citation, do NOT reclassify — flipping `assigned_vm` here would dispatch a duplicate.
4. **RECLASSIFY → planning** — bounded/deterministic-outcome work, simply defaulted to NA and never assessed. Run the
   shared conflict-check (Phase 2 below) BEFORE flipping — never flip on the classifier's verdict alone.
5. **ARCHIVE** — fully resolved or fully moot. Run the standard 6-step archival ritual
   (`codex/11-project- management/`), never autonomous on a `locked_by:` doc.

Bounded-outcome bar for verdict 4 is the SAME test `/plan-reconcile`'s AO-dispatch-readiness hunters and
`/ag-closeout-audit`'s Phase 3 already use — `/codex/12-agent-workflow/agent-orchestrator-single-vm- architecture.md` §
"Dispatch-scope eligibility": is the outcome determinable by the worker alone, or does it need a design/judgment call
that isn't already decided? A flagged judgment call stays NA even if the classifier marks it `ao_eligible: true` — the
classifier's verdict is a strong signal, not a final ruling (the proven plan's own Phase-3 run kept 3 of 6
classifier-flagged candidates NA on independent review — see its Progress Log for why each one stayed).

## Naming, grouping, and the conflict-check — all live in ONE codex doc, not restated here

`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` is the SSOT for: how a RECLASSIFY
verdict's doc gets renamed/paired (it doesn't — `assigned_vm` flips IN PLACE, name unchanged, plus a bolt-on
`{stem}_finalize_{today}.md` per `/ag-closeout-audit`'s own pairing convention § 1), which frontmatter axis to group by
(§ 2 — `parent_epic`, not `asset_group`'s inconsistent non-AG split), and the conflict-check protocol (§ 3) every
RECLASSIFY candidate must clear before flipping. Read it before running Phase 2 below; this skill does not maintain its
own copy of that procedure.

## Modes

Same calibration as `/plan-reconcile` and `/ag-closeout-audit` — **Interactive** (operator present): RECLASSIFY flips
and ARCHIVE candidates get a batched Q&A when there's real ambiguity; a provable verdict (evidence makes exactly one
answer right) is just applied, not asked. **Autonomous/AO-dispatched** (`/na-eligibility-audit --autonomous`): never
pause; apply auto-fixable classes, park every genuine judgment call as `BLOCKED-OPERATOR-DECISION` in the tranche's
finding, notify the operator. **ASK > PARK** the moment the operator is reachable — same HARD rule as the two sibling
skills (parking is for a genuinely-gone operator, not a mode flag).

## Phase 0 — inventory + incremental diff (cheap, no agents)

Run `python3 scripts/plan-hygiene/generate_na_doc_tranche_inventory.py --tranche <tranche|all> --json` — reuse this
tool's PyYAML-based classification, do not re-derive frontmatter parsing (a line-grep sweep of this population has
already produced two confirmed false-negatives: a multi-line `assigned_vm` value and a `* [ ]` star-bullet checkbox
format, both fixed in that script — re-implementing your own scan risks reintroducing either bug class).

**Incremental mode (the default for a scheduled/daily run — do not re-read all ~390 docs every time):** for each doc in
scope, grep its own body for a dated `na-eligibility-audit YYYY-MM-DD` (or the earlier
`na_docs_validity_and_ao_eligibility_audit` Progress Log precedent) verdict marker. Skip a doc from Phase 1 when BOTH
hold: (a) it carries such a marker, and (b) the doc's `last_updated` frontmatter (or, if absent, its git last-commit
date) is NOT newer than that marker's date — nothing has changed since it was last verdicted. A doc with no marker, or
edited since its last marker, is in scope. **Interim mitigation for date-fallback false-positives (until the
content-hash SCRIPT ships):** when a doc enters scope only because condition (b) failed — it HAS a prior marker but its
`last_updated`/git-date is newer — verify the actual diff before handing it to Phase 1: find the marker commit via
`git log --oneline -- <doc-path>` to identify the SHA at or after the marker date, then run
`git diff <marker-sha>..HEAD -- <doc-path>`. If the diff touches ONLY frontmatter fields (`context_scope:`,
`last_updated:`, `status:`, etc.) and zero body lines, treat the doc as unchanged and skip it from Phase 1 — a
frontmatter-only commit is not a substantive re-assessment trigger and is the confirmed false-positive class documented
in `issues/na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md`. A real body edit
(new or changed todo text, Progress Log entry, verdict section update, or any prose change) keeps the doc in scope
normally. This manual check is unnecessary once the content-hash SCRIPT is live. **`/context-scout`-only sub-case**: a
body-level `/context-scout` Progress Log line (not frontmatter, not a verdict marker) previously produced the same
false-positive class — fixed by generalizing `body_content_hash()`'s marker-stripping to a sibling-marker family; see
`issues/na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md`. **A full unscoped run** (no
incremental filter) is still the right call after a long gap or before a `--update-baseline` on the ratchet — just
expect it to look like the proven plan's own first session (dozens of sub-agents, multi-hour).

Report the Phase-0 split up front: total in-tranche docs, already-verdicted-and-unchanged (skipped), in scope this run.

### Primary-owner rule for multi-tranche docs — ONLY the owning tranche writes the marker (HARD, added 2026-07-30)

**The problem, measured**: the 10-way tranche split does not partition this corpus cleanly. On 2026-07-30 one doc
appeared in the candidate set of **6 of 9** tranches, and in the worst tranche **up to 47%** of its docs also appeared
in at least one other. Because the scheduled shape is one CONCURRENT worker per tranche (one dispatch each —
`na-eligibility-auditor.timer`), every one of those shared docs had N workers all trying to write the SAME
incremental-skip verdict marker into the SAME file at the same time. The result was an N-way merge-conflict storm, and
markers that frequently never landed at all — which silently defeats Phase 0's whole incremental design (a doc with no
marker is re-read in full every single run, forever).

**The rule — apply in Phase 0, before any Phase-1 fan-out:**

1. For every doc in this tranche's candidate set, compute its **owning tranche** from `parent_epic`, using the
   `parent_epic`→tranche mapping already blessed in
   `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 2 (`parent_epic` is single-valued and
   maps 1:1 onto a real `plans/epics/{parent_epic}.md`, which is exactly why that doc names it the clean grouping axis —
   `asset_group` is multi-valued and is the source of the overlap in the first place).
2. **Only the owning tranche writes the verdict marker.** A non-owning tranche that also sees the doc still reads it,
   still classifies it, and still reports its verdict in that tranche's own report — it just does NOT write the dated
   `na-eligibility-audit YYYY-MM-DD` marker (nor any other in-file edit to that shared doc: no `assigned_vm` flip, no
   checkbox-citation fix, no archival). Those writes are the owning tranche's job, so exactly one worker ever touches
   the file.
3. If two tranches' verdicts for the same shared doc DISAGREE, that is a finding, not a race to resolve by writing
   first: report it and route it through the normal conflict path (Phase 2 / operator ruling), never let
   last-writer-wins pick the answer.

**Machine-enforcement is a tracked follow-up, deliberately NOT shipped with this rule.** Once the hand-applied rule has
been validated over a few real runs, `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` should emit an explicit
`owning_tranche` field per doc so a worker filters to the docs it owns instead of re-deriving the mapping inline. That
work is the `[SCRIPT] P2` todo already tracked in
`/plans/archive/issues/sharded_per_tranche_audit_stash_race_and_multitranche_marker_gap_2026_07_30.md` — do not open a
second one here.

### NEVER `git stash` as one of several concurrent sharded tranche workers (HARD, added 2026-07-30)

`refs/stash` is a **single shared LIFO stack per `.git` directory** — it is not worktree-scoped, so worktree isolation
does NOT protect it (`/codex/05-infrastructure/per-tab-worktrees.md` § "What worktree isolation does NOT cover"). A
`stash push` in worker A followed by a `stash pop` in worker B pops **A's** entry, not B's. That exact push/pop race on
2026-07-30 swapped two workers' unrelated changesets. **If you need a pristine-tree comparison, use a throwaway second
worktree at HEAD instead** — `git worktree add <scratch-path> HEAD`, read it, `git worktree remove <scratch-path>`. The
same hazard applies to the `--autostash` flavours (`git pull --rebase --autostash` drives the same stack), so prefer an
explicit `git pull --ff-only` from an already-clean tree.

## Phase 1 — per-tranche classification (the real work)

Fan out read-only sub-agents (max 10 parallel; paste `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the top of every
spawn; set `model=` explicitly), one per tranche (or split a large tranche further, same shape the proven plan used — 9
for `doc_type:plan`, 10 for `doc_type:issue`, when volume warrants the split). Each hunter reads every in-scope doc in
its tranche END TO END (not a checkbox count — this corpus has confirmed traps: prose-only remaining work, a dated
RE-TRIAGE section overriding an earlier checkmark, a `DECOMMISSIONED` item deliberately left unchecked as "ruled-out,
not completed") and returns one of the four verdicts + evidence per doc.

**HARD — splitting a large tranche is the ORCHESTRATOR's decision, made up front, never a dispatched hunter's own call
(2026-08-07 finding)**: on a 10-tranche run, 2 of 10 hunters (`cross-cutting` at 81 docs, `defi` at 41 docs) responded
to a large doc list by spawning their OWN further sub-agents to split the load, then returned a "done" final message
that was really just "I launched helpers, I'll wait for their results" — but a sub-agent's final message IS terminal;
there is no "wait" state for an agent that has already returned. That first-level report was worthless (zero output
files), and the orchestrator has no visibility into a nested child's existence until the grandchild independently
completes and its own notification happens to surface (it worked out this time, but only because the harness happened to
still track the grandchildren — do not rely on that; a hunter has no way to know or guarantee it). **A dispatched
Phase-1 hunter must never itself call the Agent/Task tool.** If a tranche is large enough to warrant splitting, the
orchestrator splits it BEFORE Phase 1 starts — explicit separate dispatches (e.g. `defi-batch-1-of-6` .. `-6-of-6`),
each given its own disjoint doc sublist and its OWN pre-agreed output filenames (`na_audit_<tranche>_detail_batchN.json`
/ `_blocks_batchN.md`) — never left to an individual hunter's discretion mid-task. State this constraint explicitly in
every Phase-1 spawn prompt ("you must personally Read every doc yourself; do not delegate").

**Verify completeness before trusting a hunter's per-doc verdict set — do not skip this, even under time pressure**
(2026-07-27 finding: a sonnet-tier hunter classifying
`honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` reported only 6 of its 14 actual open items on
the first pass; caught only because Phase 2's own conflict-check happened to require tracing the doc closely enough to
notice the count didn't add up — an under-read this size would otherwise have shipped an incomplete extraction batch
silently). For every doc before moving it past Phase 1, run `grep -cE '^- \[ \]' <doc>` and compare against the sum of
the hunter's own reported verdicts for that doc (KEEP items

- RECLASSIFY items + ARCHIVE items, counting a multi-item KEEP-NA-stale-items verdict's named checkboxes). A mismatch
  means the doc was under-read — re-dispatch it for a fresh full read (or re-read it directly yourself) before authoring
  any Phase 2/3 output against it; never extract, close, or flip a doc's content on a partial read.

**The verification grep pattern itself has the same false-negative class Phase 0 already patched in the inventory script
(2026-08-07 finding)**: `grep -cE '^- \[ \]'` misses an indented/star-bullet open item (`  * [ ]`), same bug as the
`* [ ]` false-negative noted in Phase 0 above — confirmed live on `defi_expected_unattempted_backlog_1m_2026_07_03.md`,
which grepped 0 via the plain pattern but Phase 0's inventory annotation said `open_todos=1` (the correct count). **Use
`grep -nE '^[[:space:]]*[-*] \[ \]' <doc>` for the verification count, not the plain anchor-only pattern** — and treat a
mismatch against Phase 0's own `open_todos` annotation for that doc (not just against the hunter's self-reported total)
as an equally valid trigger to broaden the pattern and re-check before concluding a doc has zero or N open items.

**Never re-litigate an established ruling.** A doc whose own text already cites an explicit dated operator ruling, a
`depends_on`+`gate_on_depends` gate on a still-open prerequisite, or a "🟡 DO NOT DISPATCH" banner is KEEP-NA on that
citation alone — confirm the citation is real (grep it), don't re-derive the underlying judgment call yourself. Two more
citation classes count exactly the same way, added after a live incident
(`plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md`, BLK-29884333, 2026-07-31 — a prior
na-eligibility-audit RECLASSIFY of that exact doc caused three real mis-dispatches of a banner-guarded, multi-day
fleet-core rewrite before the operator/main-agent caught and reverted it): **(a) a banner or body sentence redirecting
work to a DIFFERENT doc/plan** (e.g. "Do NOT start work from this doc alone", "tracked and executed via `<other doc>`")
— even when this doc's own todo text reads as a clean, bounded, fully-scoped AO-dispatchable item, a redirect banner
means the DISPATCH MECHANISM is wrong (flipping this doc's `assigned_vm` would let backlog-regen derive tasks directly
from it, bypassing the doc it's supposed to route through); **(b) an inline `assigned_vm: NA #`-comment or a Progress
Log entry documenting that THIS SAME SKILL previously reclassified this doc and was reverted** — a revert is a standing
ruling, not a stale data point to re-evaluate fresh. Also stay skeptical of a todo's own "fully-scoped, AO-dispatchable"
self-framing when the underlying change is a multi-file, multi-day rewrite of live-dispatch-critical-path machinery —
bounded/bundled-into-one-todo is not the same test as small/low-risk; the
`ao-dispatch-batch-naming-and-conflict-check.md`-flavoured "worker-determinable outcome" bar still applies on top of
whatever the doc's own prose claims.

## Phase 2 — conflict-check before any RECLASSIFY flip

For every doc verdicted RECLASSIFY in Phase 1, run the shared conflict-check protocol
(`ao-dispatch-batch-naming-and-conflict-check.md` § 3) against every currently-active `assigned_vm: planning` plan in
the same `parent_epic`, any sibling batch/finalize doc drafted earlier in this same run, the tranche's own
consolidated-closeout doc, **and the 4th surface** — any `status: draft` `{ag}_satellite_ao_dispatch_batch{N}_*.md` for
the same tranche from a PRIOR `/ag-closeout-audit` or `/na-eligibility-audit` run, not just this one; grep its
`Source:`/`## Deferred`/`## Already covered` citations for the candidate doc's path before flipping. Clear → proceed to
Phase 3. Conflict → do NOT flip; file the conflicted item in the run's Deferred/parked list for an explicit operator
ruling, same as `/ag-closeout-audit`'s sports-batch3 precedent (23 of 25 candidates held back there over exactly this
check).

## Phase 3 — apply

- **RECLASSIFY, conflict-cleared**: flip `assigned_vm: NA → planning` in place (no rename), correct `execution_scope` to
  `orchestrator-agent` if stale, fill `assigned_role` if missing (validate against the live `agents/*.md` registry,
  never hand-type a near-miss), author the companion `{stem}_finalize_{today}.md` per `task_template.md`'s
  finalize-plan-coverage rule (`plan` doc type only — an issue doc is structurally exempt,
  `check_finalize_plan_coverage.py` only globs `plans/active/*.md`).
- **KEEP-NA-STALE**: fix the checkbox citation only (cite the extracting doc's commit/sha); zero `assigned_vm` or
  backlog impact — pure hygiene so a future run doesn't re-flag the same content as an unaddressed orphan.
- **ARCHIVE**: standard 6-step ritual, `locked_by:` blocks it without `[unlock-plan]` (ask, never autonomous).
- **KEEP-NA valid/stale-items**: write the dated Progress Log verdict marker (Phase 0's incremental-skip anchor) even
  when nothing else changes — an audited-and-confirmed doc needs that marker or every future run re-reads it from
  scratch.
- **Long one-line markers get auto-wrapped by the autostage formatter on commit (2026-08-06)**: a multi-sentence marker
  line comes back from the pre-commit hook prettier pass re-wrapped across several lines, leaving the worktree ahead of
  the staged index — the commit attempt aborts with a staged-vs-worktree mismatch (`MM` status). Fix: `git add` the
  reformatted files and re-commit; no content is lost. Also: the PM pre-commit branch-drift hook refuses to commit while
  behind origin — under concurrent sharded waves (sibling workers pushing marker commits) expect mid-run `git fetch` +
  overlap check + `git pull --ff-only`, and if a sibling also edited one of your files, restore that ONE file from
  origin first and re-apply your marker (never `git stash` — shared LIFO, banned for sharded workers).

## Phase 4 — apply + commit

PM-repo doc edits only; stage by name; mandatory pre-commit `git status && git diff --cached --stat` (no path arg);
commit prefix `docs(plans):`; ship per CLAUDE.md's git-discipline section (`quickmerge.sh --agent --files`). Batch
related fixes into coherent commits (one per tranche or per verdict class, not one mega-commit). Big findings
(data-correctness, cross-repo, SSOT contradiction surfaced along the way) additionally follow the triage HARD RULE:
notify the operator + file `plans/active/issues/<slug>_<date>.md`. NEVER write agent memory; NEVER create `*_SUMMARY.md`
— the final report is chat text.

## Phase 1b — blocker-classification tag (STANDARD, every run, added 2026-08-07)

Every Phase-1 hunter tags each open todo with a SECOND, finer-grained blocker-classification tag alongside the
KEEP-NA/RECLASSIFY/ARCHIVE verdict above — this is not optional and not a special-request extra; it is how Phase 5
reports the corpus every run, the same way a 373-doc/1,272-todo full sweep produced it live on 2026-08-07:

- `OPERATOR_QUESTION` — the item itself is an unresolved question/decision needing the operator's input (explicit
  `[OPERATOR]` tag, "ruling needed", a named judgment call with no decision on record).
- `CREDENTIAL_BLOCKED` — needs a vendor API key/account/secret the agent can't self-serve (`PERMISSION_DENIED` on the
  trading GCP/AWS service accounts is agent-self-serviceable per codex, NOT this class).
- `DEPENDENCY_BLOCKED` — cite the root blocker and what THAT reduces to (usually one of the two tags above, or in-flight
  `GENUINE_WORK`).
- `GENUINE_WORK` — real, unblocked build/design/investigation work.
- `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` — this is the SAME finding as a RECLASSIFY candidate under the primary rubric,
  tagged here specifically when the hunter's confidence is lower than a clean RECLASSIFY call (e.g. only PART of a
  multi-todo doc looks bounded, or the hunter wants a second pass before committing to a flip). **This tag is not a dead
  end** — see the closing-the-loop rule below.

Each hunter writes a per-tranche `_blocks.md` consolidating the DISTINCT questions/asks found (dedup near-identical asks
across docs into one entry, cite every doc/todo it unblocks) under `## Operator questions` /
`## Credentials/access needed` headings — this is the artifact that makes the corpus's real Q&A/credential surface
batchable instead of buried across hundreds of docs.

**Close the loop on `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` — it must not just sit flagged forever (2026-08-07 finding).** A
prior one-off session tagged 169 items this way across a full run and then stopped, because that session was scoped
read-only. On a standard `/na-eligibility-audit` run (which IS authorized to apply verdicts), every
`MISCLASSIFIED_LIKELY_AO_ELIGIBLE` item from THIS run or a PRIOR run's report is a mandatory Phase-1 input list for the
NEXT run on that tranche: re-assess it against the primary RECLASSIFY bar (bounded, deterministic, whole-doc-qualifies)
and either promote it to a real RECLASSIFY (through Phase 2's conflict-check, same as any other candidate) or downgrade
it to KEEP-NA with a marker explaining why it doesn't clear the bar after a second look. A tag that never gets
re-examined is exactly the false-progress class this whole skill exists to prevent — track it the same way Phase 0
tracks incremental-skip markers, not as prose.

## Phase 5 — report, including the ratchet

Finish with text: per-tranche verdict counts (KEEP-NA valid / KEEP-NA-STALE / RECLASSIFY / ARCHIVE), **and the Phase 1b
blocker-classification totals — grand total plus a per-tranche breakdown of OPERATOR_QUESTION / CREDENTIAL_BLOCKED /
DEPENDENCY_BLOCKED / GENUINE_WORK / MISCLASSIFIED_LIKELY_AO_ELIGIBLE counts, same shape as the 2026-08-07 run (373 docs
/ 1,272 todos: 210 OPERATOR_QUESTION, 42 CREDENTIAL_BLOCKED, 334 DEPENDENCY_BLOCKED, 517 GENUINE_WORK, 169
MISCLASSIFIED_LIKELY_AO_ELIGIBLE)** — this is a standing stat every run reports now, not a special request. Also report:
docs flipped + their new open-todo count entering the AO backlog, docs archived, checkboxes corrected, and any parked
`BLOCKED-OPERATOR-DECISION` items. **Then run `python3 scripts/plan-hygiene/check_na_corpus_ratchet.py` and report its
verdict verbatim** (current NA doc-count + open-todo count vs. baseline). If this run's own RECLASSIFY/ARCHIVE work
shrank the corpus, re-run with `--update-baseline` and note the old→new numbers in the report — do not leave a shrunk
corpus sitting above a stale, looser baseline (that silently wastes the very ratchet this skill exists to keep honest).
If the corpus grew despite this run (new NA content added elsewhere outfacing this run's own reclassifications), report
that plainly too — a grown-then-hidden number is worse than a grown-and-reported one.

## Scheduled cadence

Runs automatically in autonomous mode via `na-eligibility-auditor.timer` on the central orchestrator VM —
`agent-orchestrator/scripts/install-na-eligibility-auditor-timer.sh` installs it. **Cadence as of 2026-07-30: every 2
hours, on ODD hours at :30 UTC** (a per-tranche idempotency guard makes every fire after that tranche's first success of
the day a cheap no-op, so this is retry-until-capacity, not 12 audits a day). The ODD-hour phase is deliberately 1 hour
offset from `ag-closeout-auditor.timer` (:30 on EVEN hours): both jobs fan out one dispatch per tranche, so a same-hour
overlap would double the instantaneous slot demand. The other two scheduled jobs sit on their own phases —
`docs-reconciler.timer` :15 hourly, `plan-reconciler.timer` :00 on EVEN hours. Sharded the same way `ag_closeout` is:
one dispatch per tranche, fired in batches (each installer carries its own concurrency cap), each its own free slot —
which is exactly why the primary-owner and no-`git stash` rules in Phase 0 above are HARD. Still directly invocable
interactively any time.

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — naming/pairing convention, grouping
  semantics (§ 2 `parent_epic`-as-grouping-axis is the SSOT behind Phase 0's primary-owner rule), the shared
  conflict-check protocol, and the NA-corpus ratchet rationale
- `/codex/05-infrastructure/per-tab-worktrees.md` § "What worktree isolation does NOT cover" — why `git stash` is banned
  for concurrent sharded tranche workers (`refs/stash` is one shared LIFO stack per clone)
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" —
  bounded-outcome bar for a RECLASSIFY verdict
- `plans/active/task_template.md` §§ 1-4 — LOCAL vs AO-dispatched tracks, AO frontmatter, finalize-plan-coverage rule
- `plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` — the origin plan this skill generalizes; its
  Progress Log is the evidence base for the verdict rubric and every calibration note above
- `cursor-configs/skills/ag-closeout-audit/SKILL.md` — sibling skill (orphan detection, disjoint population)
- `cursor-configs/skills/plan-reconcile/SKILL.md` — sibling skill (corpus-wide contradictions, disjoint concern)
- `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — sub-agent spawn contract + escalation format
