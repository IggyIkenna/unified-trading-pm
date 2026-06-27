---
doc_type: plan
title: Mechanical frontmatter rollout — seed all plans/active docs (derivable fields only)
summary: Run the already-shipped mechanical seeder (scripts/docs/seed_frontmatter.py --apply) in place over every top-level doc in plans/active/ so each carries the derivable universal-core + per-type plan fields, leaving summary/tags present-but-empty. Mechanical ONLY — no content pass, no status normalization, no enforcement gate, no other dirs.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [frontmatter, mechanical-seed, plans-active, grep-native, ao-fleet-test]
related: [doc_frontmatter_mechanical_seed_and_sample_2026_06_24.md, doc_frontmatter_schema_and_validator_2026_06_24.md, ../epics/agent_operating_framework_master.md, ../../codex/11-project-management/doc-frontmatter-schema.md]
created: 2026-06-27
parent_epic: agent_operating_framework_master
assigned_vm: harsh_pc
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
last_updated: 2026-06-27
locked_by: NA
locked_since: NA
supersedes:
superseded_by:
depends_on: [doc_frontmatter_schema_and_validator_2026_06_24]
source: [operator request 2026-06-27 — roll out the mechanical frontmatter seed to every plans/active doc (AO fleet-test plan), reuses the seeder + validator shipped by doc_frontmatter_mechanical_seed_and_sample_2026_06_24 (scripts/docs/)]
assigned_role: infra
drift_direction: advance-code
---

# Mechanical frontmatter rollout — `plans/active`

Apply the **mechanical** frontmatter seed to every top-level doc in `plans/active/` and leave it validator-green on the
HARD checks. This is the cheap, derivable-only pass — it fills the universal-core + per-type **plan** fields the seeder
can derive (`doc_type`, `title`, `nature`, `stage`, `repos`, `scope`, `assigned_vm`-from-epic, …), **preserves any
existing values**, and leaves the expensive content fields (`summary`, `tags`) **present-but-empty** for a later pass.

The tooling already exists (shipped by `doc_frontmatter_schema_and_validator` + `doc_frontmatter_mechanical_seed`); this
plan only **runs it at scale** over `plans/active` and verifies. 102 top-level docs today; ~78 still lack `doc_type`.

## Scope — and explicit non-goals ("only the mechanical one, nothing else")

**IN scope:** the 102 top-level `plans/active/*.md` docs; derivable universal-core + per-type plan fields only;
non-destructive (existing values preserved); validator-green on HARD violations.

**OUT of scope (do NOT do any of these — they are other workstreams):**

- ❌ `summary` / `tags` **content** pass (LLM-drafted one-liners + topical tags) — leave present-but-empty.
- ❌ `status` value **normalization** (mapping ad-hoc statuses → the per-type enum) — content decision, not mechanical.
- ❌ any **enforcement / QG gate** (`check_*_frontmatter` warn→error) — that is W5, enforce-LAST.
- ❌ the `plans/active/issues/` subdir (67 docs, `doc_type: issue`) — separate doc_type, separate follow-up.
- ❌ `codex/`, `plans/epics/`, or any other doc tree.
- ❌ schema / `docspec.py` / `seed_frontmatter.py` changes — use them as shipped; if the seeder is wrong, file an issue
  doc, don't fix it here.

## Codex SSOTs

- [`codex/11-project-management/doc-frontmatter-schema.md`](../../codex/11-project-management/doc-frontmatter-schema.md)
  — the universal-core + per-type **plan** required/optional fields + null/`NA` conventions this seed targets.
- Tooling: `scripts/docs/seed_frontmatter.py` (`--apply`) + `scripts/docs/docspec.py` (`--check`).

## Todos

- [x] [SCRIPT] P1. **Seed in place.** Run `python3 scripts/docs/seed_frontmatter.py --apply plans/active/*.md`
      (top-level only). Derivable universal-core + per-type plan fields are filled; existing values preserved;
      `summary`/`tags` left present-but-empty. **Gate**: every `plans/active/*.md` has `doc_type: plan` + the plan
      per-type required fields present; no `summary`/`tags` content was written; no file outside `plans/active/*.md`
      changed (`git status` clean of other paths). ✅ — unified-trading-pm@4d3083639
- [x] [SCRIPT] P1. **Validator-green (HARD).** Run `python3 scripts/docs/docspec.py --check plans/active/*.md`; it must
      exit 0 on HARD violations. SOFT/needs-content findings (empty `summary`/`tags`) are expected and acceptable.
      **Gate**: zero HARD violations across all top-level active-plan docs; SOFT-only remainder is the deferred content
      pass, not this plan. ✅ — docspec.py exit 0, HARD=0 across all 102 docs
- [x] [SCRIPT] P2. **Ship + flip.** Commit the seeded docs to `live-defi-rollout` (docs-only → direct-push carve-out)
      and flip these checkboxes in the same turn with the `docs(plans):` prefix. **Gate**: pushed; the three checkboxes
      above are flipped to `[x]` with the commit sha cited. ✅ — unified-trading-pm@4d3083639

## Success criteria

- All 102 top-level `plans/active/*.md` carry the mechanical frontmatter (derivable fields populated, existing values
  untouched, `summary`/`tags` present-but-empty).
- `docspec.py --check plans/active/*.md` is HARD-green.
- Nothing outside the mechanical seed changed — no content pass, no status normalization, no gate, no other dirs.

## Progress Log

- 2026-06-27 — Plan authored (operator request, AO fleet-test candidate). Born `draft`; flip to `active` to green-light
  AO ingestion. 102 top-level docs in scope; ~78 currently lack `doc_type`.
