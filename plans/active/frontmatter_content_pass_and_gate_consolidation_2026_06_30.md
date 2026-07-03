---
doc_type: plan
title: Frontmatter content pass + gate consolidation — populate summary/tags/authoritative_for, converge to one blocking check
summary:
  Follow-on to the (completed) full-corpus frontmatter coverage. Populate the SOFT content fields the structural pass
  left empty (5,887 items measured 2026-07-03 — summary/tags/authoritative_for PLUS related/status/repos + audit
  fields; one read per doc fills all of them), then make a single comprehensive BLOCKING frontmatter gate (backed by
  the docspec validator engine) and retire the interim warn-only check_docspec_coverage. Nice-to-have (P3) — the
  high-leverage payoff is codex authoritative_for/summary becoming searchable for the codex drift-fixing work.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [frontmatter, docspec, content-pass, gate-consolidation, doc-governance, grep-native]
related:
  [
    ../archive/2026_06/frontmatter_full_corpus_coverage_2026_06_30.md,
    doc_frontmatter_schema_and_validator_2026_06_24.md,
    ../epics/agent_operating_framework_master.md,
    ../../codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: 2026-06-30
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
assigned_role: infra-engineer
drift_direction: advance-code
last_updated: 2026-07-03
locked_by: NA
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    operator decision 2026-06-30 — split the deferred consolidation work out of the completed full-corpus coverage plan
    into its own nice-to-have (P3) plan; that plan is archived complete,
  ]
---

# Frontmatter content pass + gate consolidation

The structural coverage is **done + enforced (warn-only)** — see the archived
[`frontmatter_full_corpus_coverage_2026_06_30`](../archive/2026_06/frontmatter_full_corpus_coverage_2026_06_30.md):
every live doc carries a valid `doc_type` + universal-core + per-type fields + valid enums, and
`check_docspec_coverage.py` surfaces any HARD rot (non-blocking). This plan is the **value layer on top**: fill the
content fields that make frontmatter actually answer queries, then collapse to a single blocking gate.

## Why P3 / nice-to-have

The corpus is already HARD-green and rot is surfaced every QG run, so nothing is at risk. The payoff here is *quality of
search*: a populated `authoritative_for` lands an agent on the one right codex SSOT, and `summary` lets it read a 1-liner
instead of opening the doc — most valuable right before the codex↔code drift-fixing push. Worth doing, not urgent.

## Codex SSOTs

- [`codex/11-project-management/doc-frontmatter-schema.md`](../../codex/11-project-management/doc-frontmatter-schema.md)
  — the universal-core + per-type fields + the two-checks lifecycle this plan executes.
- Validator engine: `scripts/docs/docspec.py` (`validate_frontmatter` — SOFT vs HARD); the surviving gate must call it,
  not reimplement it.

## Todos

> **Execution shape (2026-07-03 recalibration — measured, see Progress Log):** the corpus needing content = 1,017 docs
> / 17 MB (~4.2M tok to read); p50 doc = 10 KB, only 36 docs < 2 KB — so NO Haiku/length split (one model, one prompt,
> uniform quality; wrong metadata is worse than empty). **One read per doc fills ALL its content fields** — never run
> per-field passes (3× the read cost). Folder-scoped Sonnet (medium) agents, because the folder ledger is what gives
> `authoritative_for` uniqueness + a consistent tag vocabulary; ~40-60 docs per agent instance, big trees
> (09-strategy/04-architecture/14-customer-journeys) split by subfolder with the ledger handed between chunks. Order by
> churn: codex first (stable + highest leverage), then plans/audit + plans/epics, plans/active LAST; skip dirty /
> recently-pushed docs (other slots), second sweep catches stragglers. Commit+push per folder as it lands.

- [x] [SCRIPT] P3.0 **Mechanical pre-pass — no LLM.** Fill `created` (804 empty) from git first-commit date
      (`git log --follow`, filename-date cross-check for plans); normalize literal `NA` → null on
      `locked_by`/`locked_since`/`depends_on` (29). **Gate**: docspec SOFT `created` + literal-NA counts → 0. —
      ✅ unified-trading-pm@8d9167827 (825 files, frontmatter-only one-liners). Evidence: docspec re-sweep post-apply:
      created/locked_by/locked_since/depends_on SOFT = 0/0/0/0; corpus total SOFT 5,887 → 5,053.
- [x] [AGENT] P3.1 **Pilot folder — `codex/11-project-management` (14 docs), operator eyeball gate.** One Sonnet
      (medium) sub-agent fills, per doc in ONE read: `summary`, `tags` (prefer the harvested lexicon),
      `authoritative_for` (codex-ssot; unique across the folder — keep a topic→doc ledger), `related` (sibling
      cross-links), `status` (normalize to the per-type enum; codex current/stale is a judgment from the read),
      `repos` (manifest-validated), + `code_refs` ONLY where the body already cites a path AND the path exists.
      NEVER guess operator fields (`owner`/`verifier`/`supersedes`/`resolved_by`/`source`/estimates) — emit them on a
      worklist instead. **Gate**: operator reviews the pilot diff before any fan-out. —
      ✅ unified-trading-pm@091318d21 (14 docs, frontmatter-only). Evidence: docspec HARD=0 all 14; content-SOFT → 0
      except valid-empty `repos`/`related` `[]`; authoritative_for corpus-collision-checked. **Fan-out still gated on
      the operator eyeball of this diff.**
- [ ] [AGENT] P3.2 **Fan-out — remaining trees with the pilot prompt.** Per-folder Sonnet agents (≤10 parallel), codex
      → plans/audit (+ audit-result fields `severity`/`audited_scope`/`auditor`/`date` from the body) → plans/epics →
      plans/active last. **Gate**: docspec content-SOFT count (5,887 baseline) → ~0 on targeted trees, measured per
      folder commit.
- [ ] [SCRIPT] P3.3 **`referenced_by` reverse-link post-pass (codex).** Derive from the corpus link graph AFTER the
      content pass lands (the pass creates new `related` edges). **Gate**: codex `referenced_by` populated
      mechanically, no LLM.
- [ ] [OPERATOR] P3.4 **Operator worklist (~80 items).** `owner`/`verifier` (30 each) + unstated `cadence` +
      `supersedes`/`resolved_by`/`source`/`tier`/`priority`/plan estimates — people/authority/provenance claims agents
      must not fabricate. **Gate**: worklist table delivered; operator ticks it off.
- [ ] [AGENT] P3. **Make the single gate comprehensive — back it by `docspec`, don't reimplement.** Expand the blocking
      `check_frontmatter_schema` to enforce the full schema (universal-core + enums + all doc types incl. codex +
      cursor-rule, and the now-populated content fields) by **calling `docspec.validate_frontmatter()`** rather than
      growing a second hand-rolled validator (avoids two validators drifting). Re-add codex to its default corpus.
      **Gate**: one gate enforces everything docspec checks; corpus stays HARD-green (+ SOFT-green once content lands).
- [ ] [SCRIPT] P3. **Retire `check_docspec_coverage.py`** once the comprehensive blocking gate is live. **Gate**:
      docspec-coverage removed from `quality-gates.sh`; the single comprehensive blocking check is the sole frontmatter
      gate; schema SSOT banner updated to drop the two-checks lifecycle.
- [ ] [SCRIPT] P3. **agent-role enforcement (separate repo).** Wire the docspec check into the `agent-orchestrator`
      repo's own quality-gates (its `agents/*.md` are not reachable from PM CI). **Gate**: agent-role docs gated in-repo.

## Success criteria

- All content-fillable SOFT fields populated across the live corpus — `summary` / `tags` / `authoritative_for` /
  `related` / `status` / `repos` (+ audit-result fields) via the LLM pass; `created` / NA-normalization /
  `referenced_by` via script (docspec SOFT → ~0 on targeted trees, operator-only items excepted).
- A single comprehensive **blocking** frontmatter gate (backed by `docspec.validate_frontmatter`); `check_docspec_coverage`
  retired; one validator engine, no duplication.
- agent-role docs enforced in the agent-orchestrator repo.

## Progress Log

- 2026-06-30 — Plan created (operator decision) by splitting the deferred consolidation items out of the completed
  full-corpus coverage plan (now archived). P3 / nice-to-have, human-driven (`local-only`, `assigned_vm: NA`).
- 2026-07-03 — **Measured the corpus + recalibrated the todos (operator-approved).** docspec sweep: 1,298 docs checked,
  5,887 SOFT violations across 1,072 docs; 1,017 docs (17 MB ≈ 4.2M tok) still need content fields. Per-field: tags
  1,013 · summary 955 · related 931 · created 804 · authoritative_for 735 · status 913 (662 empty + 251 non-enum) ·
  repos 141 · audit fields (severity 84 / audited_scope 76 / auditor 33 / date 33) · runbook owner/cadence/verifier
  30/50/30 · literal-NA 29. Decisions (operator, 2026-07-03): Sonnet-only (no Haiku length-split — p50 doc 10 KB, only
  36 docs < 2 KB; savings marginal vs misroute risk); ONE read fills ALL fields (the original 3 per-field passes would
  read the corpus 3×); expanded field set beyond the 3 planned (add related/status/repos + audit fields; code_refs
  opportunistic-verified-only); `created`+NA-normalization+`referenced_by` are SCRIPT work, not LLM;
  owner/verifier/supersedes/provenance stay operator-only. Todos restructured P3.0–P3.4 accordingly.
- 2026-07-03 — Corpus is no longer HARD-green (3 issue docs with HARD rot, invalid `nature` enums — all three authors
  reached for issue-ish values `issue`/`audit`/`data-correctness` the closed vocab lacks; recurring instinct → consider
  an enum addition at gate-consolidation time). Non-blocking (warn-only gate working as designed); not this plan's
  scope to fix the 3 docs.
- 2026-07-03 — **P3.0 shipped** (pm@8d9167827): 804 `created` + 29 NA normalized, 825 files; SOFT 5,887 → 5,053.
- 2026-07-03 — **P3.1 pilot shipped** (pm@091318d21): 14 docs in `codex/11-project-management`, all six content fields;
  docspec HARD=0, content-SOFT → 0 (bar valid-empty `[]`). **Discoveries:** (1) validator↔schema tension — schema §6
  says empty `repos: []`/`related: []` is legal, but the FieldSpec flags it SOFT "required but empty"; MUST be resolved
  (validator accepts empty-list, or the blocking gate enforces a subset) BEFORE the gate-consolidation todo flips
  blocking, else valid docs red the gate. (2) Pilot surfaced codex-content rot for the codex-audit process (NOT fixed —
  body edits out of scope): `architecture-constraints.md` filename↔title mismatch; `codex-delta-canonical-brief.md`
  internally inconsistent dates + orphaned targets (marked `stale`); `plan-hygiene.md` says hygiene-sweep Terraform
  "not yet shipped" but `deployment-service/terraform/gcp/hygiene_sweep_scheduler.tf` exists on disk (CODEX-STALE);
  `secrets-migration-tracking.md` cites non-existent `unified-config-interface/` (renamed → unified-cloud-interface) +
  a pre-refactor UTL path; ADR-2026-04-25 cites a pre-refactor deployment-api symbol path. (3) Legacy
  `cadence`/`verifier`/`last_executed`/`type` blocks on 2 docs (plan-hygiene, active-plan-inventory-tracker) — operator
  to decide codex-runbook re-typing vs dropping legacy fields. (4) `owner` empty on 12/14 docs +
  `secrets-migration-tracking.md` has a legacy PROSE `authoritative_for` (pre-existing) — both → P3.4 operator
  worklist.
