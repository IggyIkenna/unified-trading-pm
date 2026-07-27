---
doc_type: plan
title: >-
  Audit the ~444 `assigned_vm: NA` active docs — validity-check, reclassify AO-eligible content into satellite batches,
  re-verify total coverage
summary: >-
  Scoped 2026-07-26 per operator directive, for a FUTURE session (not this one). The 2026-07-25/26 `/ag-closeout-audit`
  9-tranche run + this session's mass-flip only ever acted on ORPHANED docs (no active plan covering them) — it never
  re-examined the ~450 already-`assigned_vm: NA` docs' individual content, since those are "owned" (an active LOCAL plan
  already exists), not orphaned, by the skill's own definition. Sampling that population this session found it is a
  genuine MIX: correctly-scoped human/design work (majority, expected), real stale bloat (`v2_engine_venue_buildout` has
  a `DECOMMISSIONED — BLOCKED-OPERATOR-DECISION` item still sitting as an open checkbox instead of closed;
  `org_migration_to_odumresearch` is correctly `status: paused` and NOT actually a gap), and — the population this plan
  exists to find — genuinely AO-eligible bounded work that was simply defaulted to NA and never mined. This plan is the
  systematic version of that sampling: per-doc validity audit + reclassification, not another orphan sweep (orphan
  sweeps are already correctly excluding this population by design).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, assigned-vm, plan-hygiene, validity-audit, reclassification, ag-closeout-audit, orphan-detection]
related:
  [
    /plans/active/issues/blank_assigned_vm_dispatch_classification_gap_2026_07_26.md,
    /plans/active/issues/ag_closeout_audit_scope_widening_triage_2026_07_26.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/task_template.md,
    /plans/PLAN_FORMAT.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 14.4
assigned_role: backend_engineer
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator directive 2026-07-26, immediately after this session's mass-flip work surfaced (a) a naming-convention miss
  in the first flip pass, (b) 58 docs with a genuinely blank assigned_vm never classified either way, and (c) the
  structural question of why ~1,780 open todos still sit in already-active assigned_vm:NA docs post-audit. Operator
  explicitly scoped this as NEXT-session work, and explicitly chose the LOCAL/human track over AO-dispatched when asked
  (2026-07-26).
drift_direction: advance-code
---

# Audit the ~444 `assigned_vm: NA` docs for validity + AO-eligibility

> **Why this is its own plan, not a continuation of tonight's mass-flip**: the mass-flip (and the `/ag-closeout-audit`
> runs before it) operate on ORPHANED docs — those with no active plan already covering their remaining work. An
> `assigned_vm: NA`, `status: active` doc is, by definition, NOT orphaned (it has an owner: itself) — the orphan-sweep
> correctly never touches it. This plan is a DIFFERENT question: "is this doc's OWN `NA` self-classification still
> correct, and is its content still true?" That is real per-doc judgment work — hence LOCAL, per the operator's explicit
> choice when asked (2026-07-26) — not a mechanical sweep to hand to AO blind.

## Numbers as of 2026-07-26 (re-verify at session start — they will have moved)

- ~451 docs currently `assigned_vm: NA`, ~1,780 open todos across them (vs. ~592 now `planning`-tagged after tonight's
  two mass-flip rounds + the blank-`assigned_vm` classification pass).
- 444 of those 451 are in a LIVE status (`open`/`active`) — only ~2 are `status: paused`/correctly excluded already; the
  rest are the real audit population.
- 2 concrete stale-bloat examples already found this session (do NOT re-derive, just apply):
  `v2_engine_venue_buildout_2026_06_15.md` (32 open todos, split into 5 AO children 2026-07-13, parent has ≥1 stale
  `DECOMMISSIONED` item still open) and `org_migration_to_odumresearch_2026_06_07.md` (27 todos, `status: paused` since
  2026-07-12 — confirmed NOT a gap, correctly excluded already, exclude from re-audit).
- Separately-tracked, adjacent gaps NOT to duplicate here: `ag_closeout_audit_scope_widening_triage_2026_07_26.md` (~44
  remaining `asset_group: infrastructure`/`meta` docs never swept by any tranche) and the 30 docs this session's
  `blank_assigned_vm_dispatch_classification_gap_2026_07_26.md` just flipped to `planning` (those 30 still need the
  standard conflict-check before their todos are trusted for dispatch — fold that check into Phase 2 below rather than
  re-doing it separately).

## Phase 0 — Tooling (re-verify before trusting, don't re-derive from scratch)

- [ ] [SCRIPT] P1. **Fix the blank/NA detection script's known false-positive** before running any bulk sweep: a
      single-line `grep -lE '^assigned_vm:\s*$'` misses a multi-line YAML value (key on its own line, value on an
      indented continuation line — found live on `sports_consolidated_closeout_2026_07_19.md` this session, caught only
      by `check_frontmatter_schema.py` rejecting a duplicate before it shipped). Parse frontmatter properly (PyYAML on
      the extracted `---...---` block) rather than line-grepping for this and every future sweep.
- [ ] [SCRIPT] P2. Generate the current, re-verified list of `assigned_vm: NA` + `status` ∈ {active, open} docs, split
      by which of the 9 tranches (cefi/defi/tradfi/prediction/sports/cross-cutting/ao/ci/infra) each belongs to — reuse
      `/ag-closeout-audit`'s now-fixed (2026-07-26) membership rule (sweeps `asset_group: infrastructure`/`meta` too,
      not just `cross-cutting`).

## Phase 1 — Per-tranche validity + classification audit (the real work — read every doc end-to-end, not checkbox counts)

For EACH of the 9 tranches, read every `assigned_vm: NA` doc belonging to it (per Phase 0's list) and, per doc, record
one of four verdicts with evidence:

1. **KEEP-NA, valid** — genuinely human/design/judgment work, content still accurate. No action.
2. **KEEP-NA, stale items** — some open checkboxes are superseded/decommissioned/already-done-elsewhere (like
   `v2_engine_venue_buildout`'s pattern) — close those specific items with evidence, doc stays NA otherwise.
3. **RECLASSIFY → planning** — the doc's remaining open work (in whole or in part) is bounded/deterministic-outcome and
   was simply defaulted to NA, never actually assessed. Extract into Phase 2.
4. **ARCHIVE** — fully resolved or fully moot (like a stale `org_migration`-shaped doc), 6-step archival ritual.

- [ ] [REVIEW] P2. cefi tranche — audit all `assigned_vm: NA` cefi-tagged docs per the 4-verdict rubric above.
- [ ] [REVIEW] P2. defi tranche — same.
- [ ] [REVIEW] P2. tradfi tranche — same.
- [ ] [REVIEW] P2. prediction tranche — same.
- [ ] [REVIEW] P2. sports tranche — same (note: `sports_consolidated_closeout_2026_07_19.md` is explicitly OUT of scope
      here — it already carries a 2026-07-23 operator ruling to stay NA, verified this session, do not re-open).
- [ ] [REVIEW] P2. cross-cutting tranche — same.
- [ ] [REVIEW] P2. ao tranche — same.
- [ ] [REVIEW] P2. ci tranche — same.
- [ ] [REVIEW] P2. infra tranche — same.

**Done when** (per tranche): every `assigned_vm: NA` doc in that tranche has a recorded verdict + evidence, either
inline in the doc itself (Progress Log entry) or in a per-tranche audit-results doc under `plans/audit/results/`.

## Phase 2 — Consolidate RECLASSIFY findings into AO-eligible satellite batches

- [ ] [DOC] P2. Per tranche, for every doc/todo verdicted RECLASSIFY in Phase 1: run the SAME conflict-check methodology
      `/ag-closeout-audit` already uses (against every currently-active plan + this session's newly flipped batches)
      before drafting, then extract into a new (or the tranche's next-numbered) satellite `_ao_dispatch_batchN` + gated
      `_finalize` pair — canonical `task_template.md` AO frontmatter (`assigned_vm: planning`,
      `execution_scope: orchestrator-agent`, `parent_epic`, `assigned_role`, 10-100 todos, `[TAG] P#.` format),
      `status: draft` until explicitly flipped (same ask-before-creating discipline as tonight).
- [ ] [REVIEW] P2. **Fold in the standing debt from tonight's own work**: the 30 docs
      `blank_assigned_vm_dispatch_classification_gap_2026_07_26.md` flipped to `assigned_vm: planning` still need this
      same conflict-check before their content is trusted for dispatch — do not re-audit them from scratch, just run the
      conflict-check step against them here.

## Phase 3 — Re-run the orphan-detector to verify total coverage

- [ ] [REVIEW] P1. Run `/ag-closeout-audit all` across all 9 tranches AFTER Phase 1+2 land. **Done when**: the orphan
      count for every tranche reflects the post-reclassification corpus (docs archived in Phase 1 no longer appear; docs
      reclassified to `planning` in Phase 2 are correctly excluded as "covered"; nothing NEW shows up as orphaned that
      wasn't already known). Compare against tonight's baseline orphan counts per tranche (recorded in
      `ag_closeout_audit_rollout_2026_07_25.md`'s Round 6/7 sections) to confirm real movement, not just re-measuring
      the same numbers.

## Phase 4 — Final QA on everything this plan touched

- [ ] [SCRIPT] P2. Run `check_frontmatter_schema.py`, `check_todo_format.sh`, and `check_line_caps.sh` across every doc
      touched or created in Phases 1-2 (archived docs, reclassified docs, new batch/finalize pairs). Fix anything red
      before considering this plan done — same standard this session held itself to on every commit.
- [ ] [SCRIPT] P3. Verify every new/touched doc carries correct tags per its tranche (`asset_group`, `stage`, `tags`)
      and is listed in its tranche's consolidated-closeout Sources — a doc that's been reclassified but not added to its
      tranche's Sources list is exactly the "orphan invisible to the sweep" bug this session already fixed twice (entry
      #18/#25 in `autonomous_session_operator_decisions_2026_07_25.md`) recurring in a new form.
- [ ] [DOC] P3. Update this plan's own Progress Log with final tallies (docs archived / reclassified / kept-NA /
      stale-items-closed, per tranche), matching the Round-N summary discipline
      `ag_closeout_audit_rollout_2026_07_25.md` already established.

## Codex / SSOTs to read before starting

- `plans/active/task_template.md` §1-4 (LOCAL vs AO track, AO frontmatter, todo format, AO-dispatched strict rules).
- `cursor-configs/skills/ag-closeout-audit/SKILL.md` (the orphan-detection + conflict-check methodology Phase 1-3 above
  deliberately reuses — this plan generalizes it to an already-owned population, not orphans).
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" (the
  determinable-outcome-by-the-worker-alone bar for what may move to `planning` in Phase 2).

## Progress Log

- **2026-07-26** — Scoped by operator directive for a future session, immediately after this session's mass-flip (30
  draft batch/native_ao_extract plans flipped across 2 rounds) + the blank-`assigned_vm` classification pass (57 docs,
  198 todos surfaced) revealed the deeper structural gap this plan exists to close. Operator explicitly chose the
  LOCAL/human track (not AO-dispatched) when asked. Not started.
