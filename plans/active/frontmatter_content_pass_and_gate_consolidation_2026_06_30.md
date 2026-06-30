---
doc_type: plan
title: Frontmatter content pass + gate consolidation — populate summary/tags/authoritative_for, converge to one blocking check
summary:
  Follow-on to the (completed) full-corpus frontmatter coverage. Populate the SOFT content fields the structural pass
  left empty (summary/tags/authoritative_for, ~5.9k items), then make a single comprehensive BLOCKING frontmatter gate
  (backed by the docspec validator engine) and retire the interim warn-only check_docspec_coverage. Nice-to-have (P3) —
  the high-leverage payoff is codex authoritative_for/summary becoming searchable for the codex drift-fixing work.
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
last_updated: 2026-06-30
locked_by: NA
locked_since: NA
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

- [ ] [AGENT] P3. **Content pass — `summary`.** Draft a one-line `summary:` for every non-exempt doc still empty
      (~highest count across codex). Mechanical-assisted (derive from the H1/title + first paragraph), operator-reviewed
      in batches. **Gate**: docspec SOFT `summary` count → ~0 on the targeted trees.
- [ ] [AGENT] P3. **Content pass — `authoritative_for` (codex).** The highest-leverage field: state what each codex doc
      is THE SSOT for, so `rg '^authoritative_for:.*<topic>'` lands on one doc. **Gate**: every `nature: ssot` codex doc
      has a non-empty `authoritative_for`.
- [ ] [AGENT] P3. **Content pass — `tags`.** Topical free-list per doc (the overflow search axis). **Gate**: docspec
      SOFT `tags` count materially reduced on the targeted trees.
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

- `summary` / `authoritative_for` / `tags` populated across the live corpus (docspec SOFT → ~0 on targeted trees).
- A single comprehensive **blocking** frontmatter gate (backed by `docspec.validate_frontmatter`); `check_docspec_coverage`
  retired; one validator engine, no duplication.
- agent-role docs enforced in the agent-orchestrator repo.

## Progress Log

- 2026-06-30 — Plan created (operator decision) by splitting the deferred consolidation items out of the completed
  full-corpus coverage plan (now archived). P3 / nice-to-have, human-driven (`local-only`, `assigned_vm: NA`).
