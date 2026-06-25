---
title: Doc frontmatter schema + machine validator (grep-native RAG foundation)
parent_epic: agent_operating_framework_master
assigned_vm: harsh_pc
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: design
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 2.4
created: 2026-06-24
last_updated: 2026-06-24
locked_by: NA
locked_since: NA
depends_on: NA
---

# Doc frontmatter schema + machine validator (grep-native RAG foundation)

> **W2** of `agent_operating_framework_master` — the foundation. W3 (plans backfill), W4 (L0 index), W5 (QG gate), W6
> (role charters), W7 (codex), W8 (eval loop) all consume this schema. **No backfill / no gate in this plan** — this
> ships the _shape_ (human SSOT + machine validator) only; enforcement is wired LAST by downstream workstreams (D7,
> "soak first").

## Why

Frontmatter becomes the **structured, greppable index** (L1 of the L0–L4 architecture) that lets an agent narrow
hundreds of docs to the relevant few WITHOUT opening any — by `doc_type`/`asset_group`/`stage`/`repos`/`tags`/`status`.
Three things make it a real index, all missing today: **completeness** (every doc has every field → grep never silently
misses), **normalized closed-set values** (no prose in enums), and **explicit search axes that don't exist** today
(`doc_type`, `summary`, `asset_group`, `stage`, `repos`, `tags`). This plan defines the schema + the validator that
guarantees those properties; it is the grep-native, NOT vector-RAG, substrate (embeddings rejected — epic § governing
principle).

## Locked schema (operator, 2026-06-24)

**Universal core — on EVERY doc type** (plans, epics, issues, codex, audits, agent-roles):

| Field         | Values                                                                                                   | Purpose                                                           |
| ------------- | -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `doc_type`    | `plan\|epic\|issue\|audit-result\|audit-instruction\|codex-ssot\|codex-runbook\|agent-role\|cursor-rule` | the keystone search discriminator                                 |
| `title`       | human one-liner                                                                                          | identity (NO `name` — filename = id)                              |
| `summary`     | one-line "what this is / does"                                                                           | highest-leverage RAG field (read this, not the body)              |
| `status`      | per-type lifecycle enum                                                                                  | authority / freshness                                             |
| `nature`      | `ssot\|guideline\|process\|design\|spec\|record\|notes`                                                  | purpose facet (orthogonal to `doc_type`); feeds derived authority |
| `asset_group` | list ⊂ `cefi\|defi\|tradfi\|sports\|prediction\|cross-cutting\|infrastructure\|meta`                     | domain axis (multi-value)                                         |
| `stage`       | list ⊂ pipeline step (`data\|features\|strategy\|backtest\|paper\|live\|execution\|reporting\|meta`)     | pipeline axis (multi-value)                                       |
| `repos`       | inline list `[mtds, instruments-service]`                                                                | code axis (single-line so `rg '^repos:.*mtds'` works)             |
| `tags`        | inline open free-list                                                                                    | topical RAG index                                                 |
| `related`     | inline list of doc slugs                                                                                 | cross-links                                                       |
| `created`     | `YYYY-MM-DD`                                                                                             | —                                                                 |

**Per-type extensions** (examples; finalized in the SSOT):

- **plan/issue**: `parent_epic` (registry-validated), `assigned_vm` (`{registry}` ∪ `NA`), `execution_scope`,
  `priority`, `estimate_class`/`_baseline_ai_days`/`_calibrated_ai_days`, optional `supersedes`/`superseded_by`/
  `depends_on`/`locked_by`/`locked_since`/`source`.
- **epic**: `name` (the one place `name` survives, as the slug), `tier`, `priority`, `assigned_vm`, `parent`.
- **codex-ssot** (+): `authoritative_for` (what this doc is THE SSOT for — RAG-critical), `scope`, `referenced_by`,
  `owner`, `last_reviewed`, `code_refs`.
- **codex-runbook** (+): the 4-field execution SSOT `owner`/`cadence`/`verifier`/`last_executed`.
- **audit-result** (+): `audited_scope`, `date`, `auditor`, `parent_epic`, `resulting_plan`, `severity` (P0..P3).
- **agent-role** (+): `role`, `does`/`does_not` declared on the autonomy gradient, `triggers`, `scope`/`tools` (W6 owns
  the detail).

**Conventions (LOCKED):**

- **Empty = null / `[]`** (every field always present; `rg '^field: \S'` = has-value; machine-clean). `assigned_vm: NA`
  is a meaningful VALUE (intentionally-unassigned), NOT the empty convention.
- **`assigned_vm` is the ONE mandatory field whose valid domain includes a sentinel** (`NA`). All other mandatory fields
  must be present + valid + never `NA`; optional fields present, value-valid-of-its-type or empty (null/`[]`).
- **`asset_group`/`stage`/`repos` are multi-value LISTS** (a doc can be `[defi, cefi]`).
- **`code_refs` is doc-side primary**; code stays **frontmatter-free** (a rare opt-in `See:`/`Implements:` line for the
  _why_; docstrings explain WHAT). (C8 — W6/W7 own the code-link integrity check.)
- **Vocab governance**: closed-set facets (`doc_type`/`asset_group`/`stage`/`nature`/`status`) are enums in the
  validator + enforced, but **grown organically** — start small, add values as real needs surface (NOT frozen day-1).
  Target ≤~10–15 values per facet; past ~15 → consolidate OR it should have been `tags` (the open free-list).

## Phased execution DAG

### Phase 0 — Decide homes (no code) — small operator confirmations

- [x] ✅ [DOCS] P0. Homes DECIDED (operator delegated — 2026-06-24): (a) human SSOT =
      `codex/11-project-management/doc-frontmatter-schema.md` (DRAFTED), `plans/PLAN_FORMAT.md` to cross-reference for
      the plan family; (b) machine validator = `scripts/docs/docspec.py` (universal across doc types, consumed by
      plan-hygiene + the W5 gate). — PM (unpushed, pending review).

### Phase 1 — Human SSOT [depends: P0]

- [ ] [DOCS] P0. Write the `DOC_FORMAT`-equivalent human SSOT: universal
      core + per-type extensions + the null/`NA` conventions + the vocab-governance rule + the seed enum values (small,
      per "grown organically"). This is the mirror the validator enforces. **Gate**: SSOT covers every field in the
      table above + the per-type extensions. → drafted at `codex/11-project-management/doc-frontmatter-schema.md`
      (`status: draft`); flips ✅ on operator approval + ship.

### Phase 2 — Machine validator [depends: P1; parallel-ok with codex authoring]

- [ ] [CODE] P0. `docspec.py`: the enums (closed facets) + a `FieldSpec` model (Required / Conditional / Optional per
      doc_type) + `validate_frontmatter(doc_type, fm) -> [violations]`. Mirrors the human SSOT in lockstep. Reads
      `assigned_vm` against `orchestrator_vm_registry.yaml` ∪ `{NA}`; reads `parent_epic` against the epics registry.
      **Conditional fields**: e.g. `resolved_by` required when an issue is `resolved`. **Gate**: unit tests — a
      conformant doc of each type passes; a missing-mandatory / prose-in-enum / unknown-facet-value / bad-`assigned_vm`
      each fails with a precise violation; `bash scripts/quality-gates.sh` green.
- [ ] [CODE] P1. Expose a thin CLI (`python3 scripts/docs/docspec.py --check <path>`) so backfill (W3) + the gate (W5) +
      ad-hoc agent use share one validator. **Gate**: CLI exits non-zero with a readable violation list on a broken doc.

### Phase 3 — Wire-up is DEFERRED to downstream workstreams (NOT here)

- [ ] [DOCS] P1. Document explicitly in the SSOT + this plan that **enforcement is wired LAST** (D7 "soak"): W3
      backfills plans, W5 flips the plan gate warn→error, W6/W7 extend per-type coverage. This plan ships the shape +
      validator ONLY — no tree-wide enforcement, no backfill. **Gate**: the deferral is stated; no QG step added by this
      plan.

## Success criteria

- A single human SSOT defines the universal core + per-type schemas + the null/`NA` + vocab-governance conventions.
- `docspec.validate_frontmatter()` enforces it programmatically, with passing/failing unit tests per doc type, and a CLI
  the downstream workstreams reuse.
- Enums are seeded SMALL and documented as organically-grown; `assigned_vm`/`parent_epic` validate against the live
  registries.
- NO backfill and NO enforcing gate land in this plan (those are W3/W5) — the schema "soaks" first.

## Codex SSOT updates

- `codex/11-project-management/doc-frontmatter-schema.md` (NEW, proposed) — the human SSOT.
- `codex/11-project-management/plan-hygiene.md` — cross-reference the universal core + the validator.

## Progress Log

- 2026-06-24: **W2 design pass — operator delegated the open calls; three decisions locked + the human SSOT DRAFTED** at
  `codex/11-project-management/doc-frontmatter-schema.md` (`status: draft`, dogfoods its own schema). Decisions: (1)
  **codex `scope` = an AUDIENCE axis** (`engineer/admin/sales/prospect/investor`) — grounded in the measured 826-doc
  values, NOT pipeline-stage; KEPT as a distinct 4th search axis (don't retire/remap). (2) **cursor-rule keeps
  `description`** as its summary-equivalent (add only `doc_type`; no redundant `summary`). (3) **`doc_type` stays at 9**
  (organically grown); the messy existing `type:` (30+ values, measured) splits → `doc_type` + `nature` per the SSOT §8
  migration map; `authoritative_for` already on 64 codex docs (precedent). Homes decided (Phase 0 ✅). Pending operator
  review of the SSOT before ship (qg → quickmerge).
- 2026-06-24: Plan created as W2 of `agent_operating_framework_master` (the RAG foundation). Schema + conventions locked
  in the operator decision pass (universal core · `nature` purpose facet · three multi-value axes · null/`[]` empty
  convention · `assigned_vm` NA-sentinel · organically-grown enums · code frontmatter-free). Homes proposed (human SSOT
  - `docspec` validator) pending Phase-0 confirmation.
