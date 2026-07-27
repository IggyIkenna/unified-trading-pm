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
  tranche-parameterized skill (same 9 tranches `/ag-closeout-audit` uses) with an incremental mode (skip docs already
  verdicted since their last edit — a daily full re-read of ~390 docs is not the design) and a standing size-ratchet
  report (`check_na_corpus_ratchet.py`) so the backlog is visibly shrinking-or-flat, never silently growing.
  **Explicitly does NOT hunt orphaned docs** (no active plan covers them at all — that's `/ag-closeout-audit`'s corpus)
  and does NOT run the corpus-wide contradiction/ false-unchecked sweep (that's `/plan-reconcile`'s corpus) — this
  skill's population is already-owned NA docs specifically. Trigger on `/na-eligibility-audit [<tranche>]`, "audit the
  NA docs", "check if this NA plan can be reclassified", "fold NA work into AO dispatch", "is the NA backlog growing",
  "which NA docs are actually AO-eligible".
---

# /na-eligibility-audit — assigned_vm:NA validity + reclassification audit

Generalizes `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s proven multi-session methodology (77 docs
reclassified `NA → planning` across its first two sessions, ~65 more identified-and-triaged in a third) into a
repeatable, `/`-invocable, tranche-parameterized skill — the same treatment `/ag-closeout-audit` got for orphan
detection. Where that skill asks "is anything uncovered?", this skill asks a different question about a DIFFERENT,
disjoint population: **"of the docs that already have an owner (`assigned_vm: NA`), is that self-classification still
correct?"** An `assigned_vm: NA`, `status: active`/`open` doc is by definition not orphaned — `/ag-closeout-audit`
correctly never touches it. Sampling that population has repeatedly found it is a genuine mix, not a monolith: real
evidenced judgment work (majority), stale-but-harmless duplication, and genuinely mis-defaulted AO-eligible content.

**Out of scope** (route there instead of duplicating): orphan detection with no active covering plan
(`/ag-closeout-audit`'s corpus); corpus-wide contradiction/false-unchecked-checkbox sweeps across the WHOLE corpus
regardless of `assigned_vm` (`/plan-reconcile`'s corpus, though its Phase 2 "done-but-unchecked" bar is the SAME
evidence bar this skill uses for a KEEP-NA-STALE verdict).

## The verdict rubric (unchanged from the proven plan — do not re-derive a new one)

For each `assigned_vm: NA`, `status` ∈ `{active, open}` doc with ≥1 open todo:

1. **KEEP-NA, valid** — genuinely human/design/judgment/operator-gated work, content still accurate. Record a dated
   Progress Log line in the doc itself (`**na-eligibility-audit YYYY-MM-DD**: KEEP-NA, valid — <one-line why>`) so a
   future incremental run can skip it (see Phase 0). No other action.
2. **KEEP-NA, stale items** — some open checkboxes are superseded/decommissioned/already-done-elsewhere. Close those
   specific items with evidence (same HARD-evidence bar as `/plan-reconcile` Phase 2); doc stays NA otherwise.
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

`codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` is the SSOT for: how a RECLASSIFY verdict's
doc gets renamed/paired (it doesn't — `assigned_vm` flips IN PLACE, name unchanged, plus a bolt-on
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
edited since its last marker, is in scope. **A full unscoped run** (no incremental filter) is still the right call after
a long gap or before a `--update-baseline` on the ratchet — just expect it to look like the proven plan's own first
session (dozens of sub-agents, multi-hour).

Report the Phase-0 split up front: total in-tranche docs, already-verdicted-and-unchanged (skipped), in scope this run.

## Phase 1 — per-tranche classification (the real work)

Fan out read-only sub-agents (max 10 parallel; paste `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the top of every
spawn; set `model=` explicitly), one per tranche (or split a large tranche further, same shape the proven plan used — 9
for `doc_type:plan`, 10 for `doc_type:issue`, when volume warrants the split). Each hunter reads every in-scope doc in
its tranche END TO END (not a checkbox count — this corpus has confirmed traps: prose-only remaining work, a dated
RE-TRIAGE section overriding an earlier checkmark, a `DECOMMISSIONED` item deliberately left unchecked as "ruled-out,
not completed") and returns one of the four verdicts + evidence per doc.

**Never re-litigate an established ruling.** A doc whose own text already cites an explicit dated operator ruling, a
`depends_on`+`gate_on_depends` gate on a still-open prerequisite, or a "🟡 DO NOT DISPATCH" banner is KEEP-NA on that
citation alone — confirm the citation is real (grep it), don't re-derive the underlying judgment call yourself.

## Phase 2 — conflict-check before any RECLASSIFY flip

For every doc verdicted RECLASSIFY in Phase 1, run the shared conflict-check protocol
(`ao-dispatch-batch-naming-and-conflict-check.md` § 3) against every currently-active `assigned_vm: planning` plan in
the same `parent_epic`, any sibling batch/finalize doc drafted earlier in this same run, and the tranche's own
consolidated-closeout doc. Clear → proceed to Phase 3. Conflict → do NOT flip; file the conflicted item in the run's
Deferred/parked list for an explicit operator ruling, same as `/ag-closeout-audit`'s sports-batch3 precedent (23 of 25
candidates held back there over exactly this check).

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

## Phase 4 — apply + commit

PM-repo doc edits only; stage by name; mandatory pre-commit `git status && git diff --cached --stat` (no path arg);
commit prefix `docs(plans):`; ship per CLAUDE.md's git-discipline section (`quickmerge.sh --agent --files`). Batch
related fixes into coherent commits (one per tranche or per verdict class, not one mega-commit). Big findings
(data-correctness, cross-repo, SSOT contradiction surfaced along the way) additionally follow the triage HARD RULE:
notify the operator + file `plans/active/issues/<slug>_<date>.md`. NEVER write agent memory; NEVER create `*_SUMMARY.md`
— the final report is chat text.

## Phase 5 — report, including the ratchet

Finish with text: per-tranche verdict counts (KEEP-NA valid / KEEP-NA-STALE / RECLASSIFY / ARCHIVE), docs flipped +
their new open-todo count entering the AO backlog, docs archived, checkboxes corrected, and any parked
`BLOCKED-OPERATOR-DECISION` items. **Then run `python3 scripts/plan-hygiene/check_na_corpus_ratchet.py` and report its
verdict verbatim** (current NA doc-count + open-todo count vs. baseline). If this run's own RECLASSIFY/ARCHIVE work
shrank the corpus, re-run with `--update-baseline` and note the old→new numbers in the report — do not leave a shrunk
corpus sitting above a stale, looser baseline (that silently wastes the very ratchet this skill exists to keep honest).
If the corpus grew despite this run (new NA content added elsewhere outfacing this run's own reclassifications), report
that plainly too — a grown-then-hidden number is worse than a grown-and-reported one.

## Scheduled cadence

Runs automatically once a day, autonomous mode, via `na-eligibility-auditor.timer` on the central orchestrator VM —
`agent-orchestrator/scripts/install-na-eligibility-auditor-timer.sh` installs it (07:00 UTC, staggered 2h after
`ag-closeout-auditor.timer`'s 05:00 UTC, which is itself staggered after `docs-reconciler.timer` 03:00 UTC and
`plan-reconciler.timer` 01:00 UTC — four daily deep audits, 2h apart, never contending for the same free slot). Sharded
the same way `ag_closeout` is: one dispatch per tranche, up to 9 concurrent, each its own free slot. Still directly
invocable interactively any time.

## Codex SSOTs

- `codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — naming/pairing convention, grouping
  semantics, the shared conflict-check protocol, and the NA-corpus ratchet rationale
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" —
  bounded-outcome bar for a RECLASSIFY verdict
- `plans/active/task_template.md` §§ 1-4 — LOCAL vs AO-dispatched tracks, AO frontmatter, finalize-plan-coverage rule
- `plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` — the origin plan this skill generalizes; its
  Progress Log is the evidence base for the verdict rubric and every calibration note above
- `cursor-configs/skills/ag-closeout-audit/SKILL.md` — sibling skill (orphan detection, disjoint population)
- `cursor-configs/skills/plan-reconcile/SKILL.md` — sibling skill (corpus-wide contradictions, disjoint concern)
- `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — sub-agent spawn contract + escalation format
