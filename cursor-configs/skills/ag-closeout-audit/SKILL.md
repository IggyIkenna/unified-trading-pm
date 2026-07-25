---
name: ag-closeout-audit
description: >-
  Audit one asset-group's plan/issue corpus in unified-trading-pm to answer "if the AG's consolidated-closeout plan's
  own todos AND every currently-active AO-dispatch-batch (+ finalize) plan for this AG all run to completion, how many
  plan/issue docs are left orphaned — real remaining open work nothing currently active/dispatched actually covers —
  excluding genuinely cross-cutting (multi-AG) docs?" Classifies every AG-primary doc via a per-doc read (not checkbox
  count — this corpus has confirmed traps: prose-only remaining work, dated RE-TRIAGE sections overriding earlier
  checkmarks). Then, for orphaned docs carrying genuine AO-eligible bounded-outcome work, drafts (status: draft, never
  auto-shipped) the next `<ag>_satellite_ao_dispatch_batchN_<date>.md` + gated `batchN_finalize` plan pair, mirroring
  the pattern built for sports (`sports_satellite_ao_dispatch_batch2_2026_07_24.md` +
  `sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`). Parameterized by asset group — invoke as
  `/ag-closeout-audit <ag>` (e.g. `tradfi`, `defi`, `cefi`, `prediction`, `sports`). Trigger on `/ag-closeout-audit
  <ag>`, "run the sports treatment for <ag>", "audit <ag> orphans", "how many <ag> docs would be orphaned if we finished
  the consolidated plan", "<ag> closeout completeness check".
---

# /ag-closeout-audit — per-AG closeout completeness projection + next-batch drafting

Generalizes the sports-corpus closeout arc built 2026-07-24/25 (triage → `sports_satellite_ao_dispatch_batch2` →
`sports_satellite_ao_dispatch_batch2_finalize` → the orphan-projection audit) into a repeatable, AG-parameterized
procedure. cefi, defi, tradfi, and prediction each already have their own `<ag>_consolidated_closeout_2026_07_18.md`
sitting in the same pre-treatment state sports was in before this session — this skill is what closes that gap without
re-deriving the approach by hand each time.

**This skill answers a forward-looking completeness question — it is NOT `/plan-reconcile`.** `/plan-reconcile` fixes
what's already provably done (false-unchecked flips, contradiction resolution, archival) across the WHOLE corpus. This
skill projects forward ("if everything currently active/dispatched for this ONE AG finishes, what's still stuck?") and,
where warranted, drafts the next AO-dispatch batch to close the gap. Run `/plan-reconcile` first if the corpus might
have stale/false-unchecked state — this skill's classification is only as good as the frontmatter `status` it reads.

## Modes

- **Interactive (default, operator present)**: report the audit results directly in chat; if Phase 3 drafts new
  batch/finalize plans, present them for review before shipping — **never quickmerge a newly-drafted AO batch plan
  without explicit operator confirmation** (CLAUDE.md § "Plan destination — ASK BEFORE CREATING" HARD RULE — this
  applies to a skill-drafted plan exactly as it applies to a hand-authored one).
- **Autonomous / AO-dispatched**: run Phases 0-2 (audit + report) freely — read-only, no ruling needed. Phase 3
  (drafting a new batch/finalize pair) is a `status: draft` doc creation, which is safe to do autonomously (drafts are
  not ingested/dispatched), but flipping it to `status: active` to actually dispatch it is an operator decision — park
  it as a normal `- [ ]` follow-up item, never auto-flip.

## Phase 0 — discover the AG's covering-plan set (cheap, no agents)

For the target `<ag>`:

1. **Consolidated closeout doc(s)**: `plans/active/<ag>_consolidated_closeout_*.md` (the master plan), plus any
   `<ag>_consolidated_closeout_aggregated_sources_*.md` (discoverability index — like the sports one, treat as
   NON-covering: being listed there is not dispatch) and `<ag>_consolidated_audit_*.md` (an earlier audit that may have
   spawned the closeout). Confirm these exist — if there is no `<ag>_consolidated_closeout_*.md` yet, stop and tell the
   operator this AG hasn't been consolidated at all (a different, prior gap than this skill addresses).
2. **Existing AO-dispatch-batch + finalize pairs for this AG**: grep `plans/active/*.md` for `^assigned_vm: planning`
   docs whose `asset_group` includes `<ag>` and whose filename matches `<ag>_*(ao_dispatch|satellite)*batch*` or similar
   — read each to confirm it's a batch-extraction plan (cites `Source: <doc>` per todo) and check whether it has a
   paired `depends_on: [<slug>] + gate_on_depends: true` finalize plan (per `task_template.md` §4's
   finalize-plan-coverage rule — cross-check with
   `.venv/bin/python scripts/quality_gates/check_finalize_plan_coverage.py --workspace-root <root>` if convenient). Also
   check `plans/archive/2026_*/` for already-archived batches of this AG (their coverage is DONE, not a gap).
3. **AG-primary doc inventory**: enumerate every `plans/active/*.md` and `plans/active/issues/*.md` whose frontmatter
   `asset_group` list contains `<ag>`. Filter out docs whose `asset_group` also contains a genuinely DIFFERENT peer
   asset-group marker (any of `cefi`/`defi`/`tradfi`/`quant`/`options`/`cross-cutting`, EXCLUDING `<ag>` itself and the
   historically-confirmed same-work dual-tag `prediction` when auditing `sports` or vice versa — that pairing describes
   the same betting-market work tagged two ways, not two different scopes) — these are the deterministic cross-cutting
   candidates to exclude from the deep audit. This is a CANDIDATE filter only; the per-doc agent in Phase 1 re-checks
   scope from real content (step 5 below), since asset_group tagging is not perfectly reliable. Further exclude docs
   already `status: resolved`/`archived`/`superseded` — they're already closed, not orphans.

## Phase 1 — per-doc classification (Workflow tool, one agent per doc)

Given the AG-primary candidate list from Phase 0.3, launch a `Workflow` (`pipeline()` over the doc list — this corpus
runs 50-90+ AG-primary docs per AG, well past what's worth doing serially or by hand). Each agent:

1. Reads its target doc IN FULL, end to end — **never conclude from checkbox count alone** (confirmed trap: real
   remaining work expressed as numbered PROSE lists with zero checkboxes) and **always read to the doc's end**,
   including any dated `## Update` / `## RE-TRIAGE` / `## RESOLVED` section (confirmed trap: these override earlier
   `[x]` marks back to open, or vice versa — the latest dated section is authoritative).
2. Notes frontmatter `status` + `related:`.
3. Enumerates genuinely remaining open work (checkbox AND prose-form) as of now.
4. For each remaining item, greps the AG's consolidated-closeout doc AND every discovered batch/finalize plan (Phase
   0.1/0.2 — pass their paths into the agent's context) for this doc's filename/basename, reads any citing todo, and
   judges whether it fully closes the item or only partially covers it.
5. Sanity-checks real scope vs the asset_group tag (catches Phase 0.3's imperfect deterministic filter).
6. Returns a structured verdict: `archivable_now` / `archivable_after_planned_work` / `orphaned_partial_coverage` /
   `orphaned_never_touched` / `exclude_cross_cutting`, each with `reasoning` citing the specific evidence found.

Use the exact schema and covering-context prompt pattern from the sports run
(`plans/active/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`'s sibling audit, 2026-07-25) as the template
— swap in the discovered `<ag>` covering-plan paths.

## Phase 2 — synthesize + report

Count by verdict, excluding `exclude_cross_cutting`. Report to the operator: total AG-primary docs audited, counts per
verdict, and the full list of `orphaned_partial_coverage` + `orphaned_never_touched` paths with one-line reasoning each.
This alone answers "how many docs are left orphaned" — stop here if the operator only asked the audit question.

## Phase 3 — draft the next batch (only if the operator wants this AG progressed, not just measured)

For every orphaned doc, apply the SAME dispatch-scope eligibility test `task_template.md` uses (operator ruling
2026-07-23): is the remaining work a bounded, checkable outcome a worker can execute alone, or does it require an
undecided design/judgment call?

**Conflict check — BEFORE drafting any candidate todo (HARD, added 2026-07-25 per operator instruction: a
naively-extracted batch todo can regress work the consolidated plan already has in flight for the SAME file/fix from a
different angle).** For each candidate item, grep the AG's consolidated-closeout plan's OWN todos AND every existing
batch plan for this AG (Phase 0.1/0.2) for overlap on the same target file(s)/same underlying fix — not just "is this
covered" (Phase 1's question) but "does something ELSE already claim this exact ground, possibly with a different
approach". Three outcomes:

- **No overlap** — draft normally.
- **Clear duplicate or the other side is provably stale/superseded** (a newer dated section in either doc, a commit that
  already shipped one approach, an explicit supersession banner) — resolve by logic: do not draft a competing todo;
  instead cite the existing one and skip, or fold the residual delta into a note on the existing todo. Same auto-resolve
  bar as `/plan-reconcile`'s Phase 4: the evidence must make exactly one answer provably right, not just plausible.
- **Genuine conflict** (two todos would prescribe different fixes to the same file/mechanism, ordering is unclear, or
  it's not resolvable from evidence alone) — do NOT draft it silently. Surface it as a batched operator question (same
  format as `/plan-reconcile` Phase 4: both quotes + locations, why they conflict, options with a marked recommendation)
  before drafting/shipping that specific item. In autonomous mode, park it as `BLOCKED-OPERATOR-DECISION` in the new
  batch's own `## Deferred` section rather than guessing which side wins.

Only conflict-cleared bounded items become candidate todos for a new `<ag>_satellite_ao_dispatch_batch<N>_<date>.md` —
author it with the SAME discipline as `sports_satellite_ao_dispatch_batch2_2026_07_24.md`:

- Every todo ends with `Source: \`<doc>.md\`` and a **Done when** clause.
- Internally-sequential multi-step work in one source doc becomes ONE combined todo, not fanned-out steps that would
  race each other (confirmed pattern: `mdt_legacy_canonical_row_gap_2026_07_16.md`'s 5-step chain).
- Verify zero cross-todo file collisions before finalizing (same-priority todos in one plan run concurrently by default
  — CLAUDE.md's Plans rule).
- Anything still gated on a sibling todo landing or an unmade human/operator decision goes in an explicit `## Deferred`
  section, NOT dispatched speculatively.
- `assigned_vm: planning`, `execution_scope: orchestrator-agent`, `sequential:` unset unless the batch is genuinely a
  dependency chain.
- **`status: draft`** — this is the safety rail. A draft is not ingested/dispatched (`plans/PLAN_FORMAT.md`); flipping
  it to `active` is the operator's call, in interactive mode ask directly, in autonomous mode park it as a follow-up.

Pair it with `<ag>_satellite_ao_dispatch_batch<N>_finalize_<date>.md` in the SAME turn (`depends_on: [<batchN-slug>]`

- `gate_on_depends: true` + `sequential: true`) — per `task_template.md` §4's finalize-plan-coverage rule, ALSO
  `status: draft` until the batch itself is approved and dispatched. Validate both with
  `.venv/bin/python scripts/plan-hygiene/check_frontmatter_schema.py --files <paths>` and
  `bash scripts/plan-hygiene/check_todo_format.sh <paths>` before presenting them.

**Never quickmerge/ship the drafted pair without the operator explicitly approving it** (flip `status: draft` → `active`
yourself only after that approval, then ship).

## Codex SSOTs

- `plans/active/task_template.md` §4 — finalize-plan-coverage rule + dispatch-scope eligibility test this skill reuses
- `plans/PLAN_FORMAT.md` — `status: draft` semantics, frontmatter schema
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `/codex/11-project-management/` — findings triage, archival ritual
- Precedent: `plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md` +
  `plans/active/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`
