---
name: docs-reconcile
description:
  Audit the codex + retrieval-layer surfaces (codex/**, DOC_INDEX.generated.md's generator, and the cross-agent
  doctrine files CLAUDE.md/AGENTS.md/.cursorrules) for the failure classes the plans-scoped /plan-reconcile does not
  cover: schema<->generator drift (gen_doc_index.py's _PER_TYPE_FACETS silently falling out of sync with docspec.py),
  cross-agent-instruction gaps (a retrieval rule living in only one of the three agent-facing files when it's meant to
  govern all), authoritative_for collisions (two codex-ssot docs both claiming to be THE SSOT for the same topic,
  defeating "grep lands on the one right doc"), placeholder/near-empty summary: fields that make the L2 grep-and-
  read-summary step useless, broken links — both frontmatter path-references (related/codex_ssots/supersedes/etc,
  via docspec.validate_doc_references()) and inline markdown body links (`[text](../foo.md)`, via
  check_doc_body_links.py) that silently break the "jump doc→doc" retrieval flow — and a doc contradicting ITSELF
  (an invariant/formula paragraph undercutting its own claim mid-sentence, a heading/bold-span bracket breaking across
  a blank line). Deterministic checks first (the QG
  scripts), then a multi-agent semantic sweep for what structure alone can't catch, adversarially verified, then
  reconciled — auto-fix the mechanical classes, route authority calls to the operator. Out of scope: plan-lifecycle
  contradictions and done-but-unchecked todos (that's /plan-reconcile's corpus). Trigger on /docs-reconcile, "check the
  doc retrieval layer", "is DOC_INDEX still working", "audit the codex docs", "check doc frontmatter quality", "check
  for broken links", "did the doc retrieval design decay".
---

# /docs-reconcile — retrieval-layer + codex doc health audit

Finds and fixes the failure classes that make the grep-native L0→L1→L2→L3→L4 retrieval design
(`/codex/11-project-management/doc-frontmatter-schema.md`) quietly stop working even though every doc still passes the
existing structural frontmatter gate (`check_frontmatter_schema.py` — required fields + closed-vocab enums, already
hard-blocking since 2026-07-04). This skill covers what THAT gate cannot see:

1. **Schema<->generator drift** — `scripts/docs/gen_doc_index.py`'s hand-maintained `_PER_TYPE_FACETS` dict silently
   falling out of sync with `scripts/docs/docspec.py`'s `DOC_TYPES`/`PER_TYPE` (a new doc_type or a renamed per-type
   field with no matching generator update).
2. **Cross-agent-instruction gaps** — a retrieval or governance rule meant to reach every agent (Claude Code, Codex,
   Cursor) living in only ONE of the three files that carry shared instructions (`cursor-configs/CLAUDE.md`,
   `AGENTS.md`, `.cursorrules`/`.cursor/rules/`). Real regression found 2026-07-23: the "grep DOC_INDEX first" doctrine
   was CLAUDE.md-only despite AGENTS.md being documented as the shared file — Codex/Cursor agents never got it.
3. **`authoritative_for` collisions** — two `codex-ssot` docs, both `status: current`, both claiming the same topic in
   `authoritative_for:`. The whole point of the field is "grep it, land on the ONE right doc" (doc-frontmatter-schema.md
   §3) — a collision means an agent's grep is a coin flip.
4. **Content-quality gaps the schema doesn't score** — a present-but-useless `summary:` (placeholder text, "TBD", or too
   short to substitute for opening the doc — the L2 "read summary instead of body" step depends on this being real), and
   codex staleness OUTSIDE the 4 cutover-critical dirs `check_codex_doc_freshness.py` already gates (report-only —
   widening the blocking gate is an operator call, not this skill's to make unilaterally).
5. **Broken links** — two distinct surfaces, two distinct checkers: (a) FRONTMATTER path-shaped free_list fields
   (`related`/`codex_ssots`/`supersedes`/`superseded_by`/`depends_on`/`related_plans`/`referenced_by`) via
   `docspec.validate_doc_references()`, already wired into `check_frontmatter_schema.py` and ratcheted against
   `scripts/plan-hygiene/doc_reference_baseline.yaml`; (b) inline markdown BODY links (`[text](../foo.md)`) via
   `scripts/quality_gates/check_doc_body_links.py` (added 2026-07-23 — the frontmatter checker never looked at doc
   bodies, so a dead `[the SSOT](../foo.md)` inside a doc's prose was invisible to every existing gate), ratcheted
   against `scripts/quality_gates/doc_body_link_baseline.yaml`. Both are SHRINKING ratchets (pre-existing dead links
   tolerated, only NEW breakage fails) — a link resolving under NONE of doc-dir-relative / PM-root-relative / a
   `plans/archive/**` basename fallback is broken; a `/codex/...`-style leading-slash target is PM-root-relative, not
   filesystem-absolute (see check_doc_body_links.py's `_resolve()` for why that distinction matters).
6. **Internal self-consistency + structural well-formedness** — added 2026-07-24 after an adversarial verification pass
   on a plans-corpus distribution found the SAME defect class already live in a codex doc: `honest-coverage-model.md`'s
   newly-added "symmetric-inclusion invariant" paragraph asserted a claim then, three words later, contradicted it in
   the same sentence — and contradicted the formula the doc itself showed two paragraphs above. No existing check here
   catches a doc contradicting ITSELF (every check above is cross-doc: schema-vs- generator, collision-vs-collision,
   link-vs-target) — a doc can pass every one of them and still be internally wrong. Also covers markdown structural
   breaks in the same class (a heading/bold-span/parenthetical whose bracket closes on an orphaned line after a
   blank-line break, rendering broken even though nothing else is "wrong").

**Out of scope (that's `/plan-reconcile`'s corpus):** plan-lifecycle contradictions, done-but-unchecked plan todos, plan
archival/consolidation. If a finding is actually about a plan contradicting another plan or its epic, route it there
instead of duplicating that skill's work here.

## Modes

- **Interactive (default, operator present)**: `authoritative_for` collisions, codex-freshness-gate widening, and any
  `locked_by:`-doc edit become a structured Q&A (Phase 3); operator decisions are applied immediately.
- **Autonomous / AO-dispatched** (`/docs-reconcile --autonomous`, or dispatched to the AO VM with no operator on the
  other end): NEVER pause for input. Apply the Phase-3 auto-fix classes as-is; park every genuine authority call
  (`authoritative_for` collision, freshness-gate widening, `locked_by:` doc) as a `BLOCKED-OPERATOR-DECISION` entry in
  `plans/active/issues/<slug>_<date>.md` with options + recommendation per the SUB_AGENT_MANDATORY_RULES escalation
  format, and notify the operator. Inherits every safety rule (`cursor-configs/AUTONOMOUS_AGENT_RULES.md` when under
  `/autonomous`).

**Scheduled cadence (ao_remediation_a_independent_fixes_2026_07_23 #8):** runs automatically once a DAY, autonomous
mode, via `docs-reconciler.timer` on the central orchestrator VM —
`agent-orchestrator/scripts/install-docs-reconcile- timer.sh` installs it (default 02:00 UTC, staggered 1h after
`plan-reconciler.timer`'s 01:00 UTC so the two daily deep audits never contend for the same free slot). The timer POSTs
`{"mode": "docs_reconcile"}` to `/api/plan-health/dispatch`, which spawns `agents/docs_reconciler.md` (opus / effort max
/ thinking on) on a free Max-plan slot to run this skill end-to-end; its "result" is the worker's `/done` evidence
string carrying the Phase-5 report summary (this skill reports as chat text, not a structured findings payload). Still
directly invocable interactively any time — the timer is additive, not a replacement for an on-demand run.

**ASK > PARK when the operator is reachable** (same calibration as `/plan-reconcile`, added there 2026-07-15 from a real
failure): parking is for an operator who is genuinely gone, not for a mode flag. If the operator is in the session — and
especially the moment they reply to anything — switch to interactive and ASK, even mid-autonomous-run. Re-evaluate every
turn; the mode is a property of operator reachability, not of how the run was invoked.

**Never weakened by either mode:** the codex-freshness gate stays a report-only widen-ask (this skill cannot flip
`check_codex_doc_freshness.py`'s scope itself, in autonomous mode or otherwise); an `authoritative_for` collision is
never auto-resolved by picking a side — evidence can show the collision exists but never which doc should keep the
topic, so it is always a park/ask, never an auto-fix, regardless of mode.

## Phase 0 — deterministic checks (cheap, no agents)

Run first, in order, over the live PM tree:

- `python3 scripts/quality_gates/check_doc_retrieval_layer_parity.py --workspace-root "$WORKSPACE_ROOT"` — schema<->
  generator parity + the two-surface doctrine check (already a hard PM QG gate; a RED here is priority-0, fix before
  anything else).
- `python3 scripts/plan-hygiene/check_frontmatter_schema.py` (no args = full corpus) — confirms the structural baseline
  is still zero-violations; this skill does not re-implement it.
- `python3 scripts/quality_gates/check_codex_doc_freshness.py --workspace-root "$WORKSPACE_ROOT" --strict` — run in
  `--strict` (ignore the ratcheted baseline) to see the TRUE current staleness count across all 4 cutover-critical dirs,
  not just "no new regression." Report the gap between strict-count and baseline as a Phase-5 finding, never silently
  absorbed.
- `python3 scripts/docs/gen_doc_index.py` — smoke-run the generator itself; a non-zero exit here means the L0
  index is not buildable at all, which is more urgent than any downstream drift check.
- `python3 scripts/quality_gates/check_doc_body_links.py` (no args = full corpus) — inline markdown BODY link existence
  check (frontmatter path-refs are already covered inside `check_frontmatter_schema.py` above, via
  `docspec.validate_doc_references()` — do not re-run that check here). A RED here (exit 1) means a NEW body link broke
  beyond the ratcheted baseline. Also report the TOTAL debt, not just "zero NEW": count the `known_broken` entries in
  `scripts/quality_gates/doc_body_link_baseline.yaml` (`grep -c '^\s*-' ...`) — a shrinking-ratchet check that only ever
  reports "zero new" can hide totally-stagnant pre-existing debt forever if nobody looks at the baseline size itself,
  same "don't silently absorb the gap" rule as the freshness check below.

## Phase 1 — multi-agent semantic sweep

Fan out read-only sub-agents (max 10 parallel; paste `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the top of every
spawn; set `model=` explicitly, default sonnet):

1. **`authoritative_for` collision hunters** — `rg -A0 '^authoritative_for:' codex/**/*.md`, group by topic string
   (fuzzy-match near-duplicates, e.g. "manifest schema" vs "manifest schema v9"), flag any topic claimed by 2+
   `status: current` docs. Verify it's a real collision, not a parent/child split (e.g. one doc is the general SSOT, the
   other is a narrower sub-topic — read both bodies before flagging).
2. **Summary-quality hunters** — sweep `summary:` fields corpus-wide for placeholder/near-empty patterns (< ~40 chars,
   "TBD", "see body", a bare restatement of the title). Read the doc body to confirm the summary really is unusable
   before flagging (a short summary can still be a complete one).
3. **Doctrine-consistency hunters** — beyond the two hardcoded QG surfaces, sweep `.cursor/rules/*.mdc` and
   `agents/*.md` (role charters) for retrieval-doctrine references that have gone stale (naming a retired file path, a
   superseded index format, or contradicting the current L0/L1/L2/L3/L4 terminology).
4. **Codex-freshness scope report** — for docs outside the 4 gated dirs, report staleness distribution (not a per-doc
   finding list) so the operator can decide if/when to widen the ratchet.
5. **Broken-link triage hunters** — batch the `known_broken` entries from BOTH `doc_reference_baseline.yaml` and
   `doc_body_link_baseline.yaml` that fall inside your audit scope (skip the rest — the two baselines are corpus-wide,
   not scoped to whatever slice you're reconciling) and, for each, determine: (a) does it still reproduce (target still
   absent) or did it get fixed since seeding (baseline entry is now stale dead weight — flag for `--update-baseline`
   cleanup, not a finding); (b) if still broken, is the target provably MOVED (renamed file, or graduated to
   `plans/archive/**` under a different name than the basename fallback catches) — auto-fixable, repoint it; or is it a
   genuine dead reference with no clear successor — surface as a P1/P2 finding for someone to either fix the prose or
   delete the dead link, this is NOT an authority question so it does not need an operator ruling the way an
   `authoritative_for` collision does.
6. **Internal self-consistency + structural-integrity hunters** — added 2026-07-24 (item 6 above). Scope to codex docs
   touched since the last clean run (or, on a full sweep, any doc whose body was edited in the last 24h — checking the
   whole corpus every run is not the point, catching what just landed is). For each: (a) **structural well-formedness**
   — every `(`/`` ` ``/`**`/`[` opened on a heading or bold-span line must close on the SAME physical line, never split
   across a blank line (`grep -n` the raw file, not the rendered preview — a floating orphaned `)` two lines after a
   heading is the tell); (b) **internal self-consistency** — any newly-added paragraph stating a rule/invariant/formula
   must be re-derived against an example or formula the SAME doc shows elsewhere, and checked for self-contradiction
   within one sentence (read it once as a skeptic hunting for the word that undercuts the clause before it). Piggyback
   this on whichever hunter already opens that doc's full body (item 2's summary-quality read is the natural host) — no
   new dedicated pass needed, just an explicit item on the checklist so it isn't assumed as a side-effect of reading.

Candidate contract: `<relpath>` + verbatim quote ≤200 chars + why it's a finding; severity P0 (breaks retrieval
correctness — collision, generator crash) / P1 (degrades retrieval — dead summary, stale doctrine ref, broken link with
no obvious successor) / P2 (report-only — freshness distribution outside gated scope, or a broken link that's genuinely
ambiguous where it should point).

## Phase 2 — adversarial verification

Dedup by (doc, claim). For each P0/P1 candidate: an independent **refuter** (is this actually a parent/child split, not
a collision? is the "placeholder" summary actually adequate for its doc's simplicity?) and an independent **confirmer**.
Split votes go to a tiebreaker. Only CONFIRMED findings proceed to Phase 3.

## Phase 3 — resolution routing

**Auto-fix (no ruling needed):**

| Class                                                                                            | Fix                                                                                  |
| ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| Schema<->generator drift (missing/stale facet entry)                                             | Fix `_PER_TYPE_FACETS` directly against the live `docspec.py`                        |
| Doctrine missing from a surface                                                                  | Add the pointer section, mirrored from the surface that already has it               |
| Stale doctrine reference (retired path/terminology)                                              | Update the reference to the current L0/L1/L2/L3/L4 shape                             |
| Derivable placeholder summary (the doc's own title/first-paragraph makes a real summary obvious) | Write it, cite the source line                                                       |
| Broken link (frontmatter ref or body link) where the target provably moved                       | Repoint the ref/link, then re-run `--update-baseline` on the matching checker        |
| Baseline entry that no longer reproduces (link got fixed since seeding)                          | Drop it via `--update-baseline` on the matching checker (dead weight, not a finding) |

**Operator ruling required:** any `authoritative_for` collision (which doc keeps the topic is an authority call, not a
correctness call — evidence can show the collision exists but not which side should own it); widening the codex-
freshness gate beyond the 4 cutover-critical dirs; any edit that would touch a `locked_by:` doc's frontmatter. Batch ≤4
questions per round, each with both quotes + locations, why they conflict, and options with the recommendation marked
first (SUB_AGENT_MANDATORY_RULES escalation format).

## Phase 4 — apply + commit

PM-repo doc/script edits only; stage by name; mandatory pre-commit `git status && git diff --cached --stat` (no path
arg); ship per CLAUDE.md's git-discipline section (`quickmerge.sh --agent --files`). Pure doc-only changes get the
doc-only fast path quickmerge already applies internally — do not bypass quickmerge itself. Batch related fixes into
coherent commits. NEVER write agent memory; NEVER create `*_SUMMARY.md` — the final report is chat text.

**Ship each coherent batch as you finish it — never hold every fix to the end of the run (HARD, added 2026-08-06).**
This mirrors `agents/plan_reconciler.md`'s existing "COMMIT INCREMENTALLY … PUSH each checkpoint" contract, which this
skill lacked. The reason is measured, not stylistic: scheduled workers in this family die mid-run often (32 of 65
retained runs across the 7 scheduled jobs ended `reaped-stale` — killed without ever reaching `/done`), and when a run
dies the ONLY thing that survives is what it already pushed. A batch sitting uncommitted in the worktree when the
session is reaped is lost work that has to be re-derived from scratch on the next run. Push each batch; do not
accumulate.

Note what this does and does not buy you: checkpointing protects work already DONE, it does not protect a run that dies
before finishing its first batch (plan_reconciler's 2026-08-03/08-04 deaths were 1m48s and 5m14s in — nothing to
checkpoint yet). Sharding is the fix for that class; this is the fix for losing hours of completed work.

## Phase 5 — report

Finish with text: counts by severity/class, applied-fix list (commit shas), operator-decision list, refuted-candidate
count, and the codex-freshness scope-report numbers from Phase 0/1.4. Report the strict-vs-baseline freshness gap
explicitly even if not fixing it this run — a widening gap invisible outside the report is the failure this skill exists
to prevent. Report the broken-link ratchet numbers the same way: total `known_broken` count in each of
`doc_reference_baseline.yaml` / `doc_body_link_baseline.yaml`, how many of those fall in-scope for this run, how many
were confirmed-still-broken vs auto-fixed (target moved) vs cleared (baseline entry no longer reproduces) vs left as a
genuine-dead-link finding for someone to fix later — a "zero NEW breakage" gate pass is not the same claim as "zero
broken links," and the report must not conflate the two.

## Codex SSOTs

- `/codex/11-project-management/doc-frontmatter-schema.md` — the frontmatter schema this skill's generator-parity check
  guards
- `scripts/docs/docspec.py` / `scripts/docs/gen_doc_index.py` — the schema's machine SSOT + the L0 generator it guards
- `scripts/docs/docspec.py`'s `validate_doc_references()` (wired into `check_frontmatter_schema.py`) — FRONTMATTER
  path-ref existence check, ratcheted against `scripts/plan-hygiene/doc_reference_baseline.yaml`
- `scripts/quality_gates/check_doc_body_links.py` — inline markdown BODY link existence check, ratcheted against
  `scripts/quality_gates/doc_body_link_baseline.yaml`; has its own unit tests in the sibling
  `test_check_doc_body_links.py`
- `plans/archive/2026_07/docs_retrieval_layer_reconcile_2026_07_23.md` — this skill's origin + the AGENTS.md gap it
  fixed
- `cursor-configs/skills/plan-reconcile/SKILL.md` — the sibling skill for plans-corpus contradictions (different scope,
  see "Out of scope" above); it has its own, separate dangling-ref auto-fix rule scoped to `depends_on`/`related`/
  `supersedes`/`superseded_by` inside the PLANS corpus specifically — this skill's broken-link checks cover the CODEX
  corpus (+ any doc type `check_frontmatter_schema.py`'s live doc trees include)
- `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` — sub-agent spawn contract + escalation format
