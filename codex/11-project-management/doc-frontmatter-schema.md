---
doc_type: codex-ssot
title: Documentation frontmatter schema — universal core + per-type fields (grep-native index)
summary:
  "The SSOT for every doc's frontmatter: a universal core on all doc types + per-type required/optional fields +
  closed-vocab enums, that turn frontmatter into a greppable L1 index. Mirrored by the docspec validator (W2)."
status: draft
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [frontmatter, rag, grep, doc-governance, docspec, agent-operating-framework]
related:
  [
    ../../plans/epics/agent_operating_framework_master.md,
    ../../plans/active/doc_frontmatter_schema_and_validator_2026_06_24.md,
    plan-hygiene.md,
  ]
created: 2026-06-24
authoritative_for:
  [doc frontmatter schema, doc_type vocabulary, per-type field requirements, frontmatter closed-vocab enums]
referenced_by:
owner: harsh
last_reviewed:
code_refs: []
---

# Documentation frontmatter schema

> **DRAFT for operator review.** The W2 deliverable of
> [`agent_operating_framework_master`](../../plans/epics/agent_operating_framework_master.md). This is the human SSOT; a
> `docspec` machine validator (W2 Phase 2) mirrors it in lockstep and is wired into the gate LAST (D7 "soak first").
> Enforcement, plans-folder backfill, and the L0 index are downstream workstreams (W3/W4/W5) — this doc defines the
> _shape_ only.

## 1. Why — frontmatter is the grep-native L1 index

The whole retrieval design is **grep-native, NOT vector-RAG** (epic § governing principle — embeddings rejected).
Frontmatter is the **L1 facet layer**: an agent narrows hundreds of docs to the relevant few with one `rg`, WITHOUT
opening any. Three properties make that work, all missing today and all this schema guarantees:

- **completeness** — every doc carries every field (an absent field would make grep silently miss it);
- **normalized closed-set values** — no prose in an enum (so `rg '^status: active'` is exact);
- **explicit search axes that don't exist today** — `doc_type`, `summary`, and the four domain axes below.

```bash
rg -l '^doc_type: codex-ssot' codex/ | xargs rg -l '^authoritative_for:.*manifest'   # the canonical manifest SSOT
rg -l '^asset_group:.*defi'  plans/active | xargs rg -l '^assigned_vm: vm-defi'        # defi work owned by vm-defi
rg -l '^repos:.*\bmtds\b'    plans/active                                              # everything touching mtds
rg '^(title|summary):'        codex/02-data/<slug>.md                                  # 2-line gist, no full read
```

## 2. Universal core — on EVERY doc type

Every non-exempt doc (§9) carries all of these. Empty optionals are present-but-empty (§6), never omitted.

| Field         | Req | Values                                                  | Purpose                                               |
| ------------- | --- | ------------------------------------------------------- | ----------------------------------------------------- |
| `doc_type`    | R   | the 9-value enum (§5)                                   | keystone search discriminator                         |
| `title`       | R   | human one-liner                                         | identity (NO `name` — filename is the id)             |
| `summary`     | R   | one-line "what this is / does"                          | highest-leverage RAG field — read instead of the body |
| `status`      | R   | per-type lifecycle enum (§5)                            | authority / freshness                                 |
| `nature`      | R   | `ssot\|guideline\|process\|design\|spec\|record\|notes` | content-kind facet (orthogonal to `doc_type`)         |
| `asset_group` | R   | list ⊂ domain enum (§5)                                 | **domain** axis (multi-value)                         |
| `stage`       | R   | list ⊂ pipeline enum (§5)                               | **pipeline** axis (multi-value)                       |
| `repos`       | R   | list ⊂ workspace-manifest repos                         | **code** axis (single-line; `[]` if none)             |
| `scope`       | R   | list ⊂ `engineer\|admin\|sales\|prospect\|investor`     | **audience** axis (who the doc is for)                |
| `tags`        | R   | open free-list                                          | topical RAG index (the overflow valve)                |
| `related`     | R   | list of doc slugs / paths                               | cross-links (`[]` if none)                            |
| `created`     | R   | `YYYY-MM-DD`                                            | —                                                     |

**The four search axes** — the heart of the index. They are independent and **multi-value lists** (a doc can be
`asset_group: [defi, cefi]`):

- `asset_group` — the trading domain (the same vocabulary as the pipeline's `--asset-group`).
- `stage` — where in the data→features→strategy→backtest→paper/live→execution→reporting pipeline.
- `repos` — which code repos the doc governs/touches (validated against `workspace-manifest.json`).
- `scope` — **audience** (engineer/admin/sales/prospect/investor). Already universal on the 826 codex docs; especially
  load-bearing for the knowledge base + commercial docs. Internal plans default to `[engineer, admin]`.

## 3. Per-doc-type fields

Universal core (§2) **plus** these. "R" = required (never empty/`NA` except `assigned_vm`); "O" = present,
value-or-empty.

| `doc_type`            | + Required                                                                                                                                                  | + Optional                                                                                         | `status` enum                                         |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| **plan**              | `parent_epic`, `assigned_vm` (registry ∪ `NA`), `execution_scope`, `priority`, `estimate_class`, `estimate_baseline_ai_days`, `estimate_calibrated_ai_days` | `last_updated`, `locked_by`, `locked_since`, `supersedes`, `superseded_by`, `depends_on`, `source` | `active·blocked·paused·complete·superseded·cancelled` |
| **epic**              | `name` (slug — the one place `name` survives), `tier` (L0–L5), `priority`, `assigned_vm`, `parent`                                                          | `co_operators`, `codex_ssots`, `related_plans`                                                     | `active·complete·superseded`                          |
| **issue**             | `parent_epic`, `priority`, `source`                                                                                                                         | `assigned_vm`, `resolved_by` (req when `resolved`), `locked_by`                                    | `open·blocked·resolved·false-positive·superseded`     |
| **audit-result**      | `audited_scope`, `date`, `auditor`, `parent_epic`, `severity` (P0–P3 of worst finding)                                                                      | `resulting_plan`, `lib_version`, `doc_versions_checked`                                            | `pass·partial·fail`                                   |
| **audit-instruction** | `tier`, `parent_epic`, `cadence`                                                                                                                            | `verifier`, `lifespan`                                                                             | `active·retired`                                      |
| **codex-ssot**        | `authoritative_for`                                                                                                                                         | `referenced_by`, `owner`, `last_reviewed`, `code_refs`                                             | `current·superseded·stale·draft`                      |
| **codex-runbook**     | `owner`, `cadence`, `verifier`, `last_executed`                                                                                                             | `code_refs`                                                                                        | `current·superseded·stale`                            |
| **agent-role**        | `role`, `does`, `does_not`, `triggers`                                                                                                                      | `scope_tools`, `reports_to`                                                                        | `draft·active·retired`                                |
| **cursor-rule**       | _(keep Cursor's `description`, `priority`, `alwaysApply`, `globs`)_                                                                                         | `tags`                                                                                             | — _(Cursor-governed; just add `doc_type`)_            |

Notes:

- **`assigned_vm` precedence (dispatch):** a plan's `assigned_vm` is authoritative for its OWN dispatch and
  **supersedes** its `parent_epic`'s `assigned_vm` when they differ — this is **not a conflict and not a validation
  error**. The epic's `assigned_vm` is the epic's own default/rollup; the strict matcher reads the **plan's** value only
  (W1 / D2). A plan's `assigned_vm: NA` → dispatched to nobody regardless of its epic.
- **`assigned_vm` is only on dispatchable units** — `plan` (required), `issue` (optional), `epic` (its own rollup
  default). **`audit-instruction` carries NO `assigned_vm`**: an instruction is a durable, cadence-run **template**, not
  a work item owned by a VM (a RUN produces an `audit-result`; routing a run is the cadence/scheduler's job, not the
  template's).
- **cursor-rule** is the one exception to the universal core: Cursor owns its schema. We add ONLY
  `doc_type: cursor-rule` so the corpus is uniformly discriminable; its existing `description` **serves as `summary`**
  (no redundant field). Lowest-priority migration.
- **agent-role** `does` / `does_not` / `triggers` are declared in **autonomy-gradient** terms (Proceed /
  Escalate-non-blocking / Gate). The full role-charter detail is W6, not W2 — here we only reserve the field shape.
- **`authoritative_for`** (codex-ssot) is the single highest-value codex field — "what this doc is THE SSOT for" — so an
  agent asking "the canonical rule for X" greps it and lands on the one right doc, not 826. 64 codex docs already carry
  it.
- **`code_refs`** (codex) is the L4 jump (doc→exact code/workflow path). Code stays frontmatter-free (§7).

## 4. The `nature` facet (content-kind, orthogonal to `doc_type`)

`doc_type` says _what artifact_ (plan, codex-ssot, …); `nature` says _what kind of content_, so two codex-ssots can be a
hard `ssot` vs a soft `guideline`. It also feeds **derived authority** (§6): a `nature: ssot` + `status: current` doc is
authoritative; a `nature: notes` + `status: draft` doc is not.

`ssot` (THE source of truth) · `guideline` (recommended practice) · `process` (a how-to / runbook procedure) · `design`
(architecture / rationale / why) · `spec` (a contract / schema / API surface) · `record` (an immutable log: audit
result, handoff, decision) · `notes` (working notes, not normative).

## 5. Closed-vocab enums (seed values — grown organically)

Closed facets are **enforced enums in the validator**, but **start small and grow as real needs surface** (NOT frozen
day-1). Target ≤~10–15 values each; past ~15 → consolidate, OR it should have been `tags` (the open free-list).

- `doc_type` (9):
  `plan · epic · issue · audit-result · audit-instruction · codex-ssot · codex-runbook · agent-role · cursor-rule`
- `nature` (7): `ssot · guideline · process · design · spec · record · notes`
- `asset_group` (8): `cefi · defi · tradfi · sports · prediction · cross-cutting · infrastructure · meta`
- `stage` (9): `data · features · strategy · backtest · paper · live · execution · reporting · meta`
- `scope` / audience (5): `engineer · admin · sales · prospect · investor`
- `priority` (4): `P0 · P1 · P2 · P3`
- `tier` (epic, 6): `L0 · L1 · L2 · L3 · L4 · L5`
- `status`: per-type (see §3) — NOT a single global enum.

**Registry-validated (not hand-grown enums):** `assigned_vm` → `orchestrator_vm_registry.yaml` ids ∪ `{NA}` ·
`parent_epic` → an epic slug under `plans/epics/` · `repos` → `workspace-manifest.json` repositories. These can exceed
15 values because they validate against a live registry, not a curated enum.

## 6. Conventions

- **Empty = `null` / `[]`, never omitted.** Every field is always present; an empty optional is `field:` (null) or
  `field: []` (list). So `rg '^summary: \S'` = "has a real summary"; a missing key is a **validator error**, not "N/A".
- **`assigned_vm` is the ONE mandatory field whose valid domain includes a sentinel** — `NA` (= intentionally unassigned
  / future plan → dispatched to nobody; D3). Every OTHER required field must be present + valid + never `NA`.
- **Multi-value axes are inline lists** (`asset_group: [defi, cefi]`) on a single line so each axis is one greppable
  line.
- **Derived authority, no freshness field (yet)** — trust is read from `nature` + `status` (+ `[gate]`/`[convention]`
  rule-tags in standards docs); we add NO separate `authority`/`review_by` field unless agents are observed acting on
  stale docs (C5).
- **`status` normalization is DEFERRED — SOFT during the soak.** The existing corpus uses 20+ ad-hoc `status` values; a
  value outside the per-type enum is a SOFT "normalize" warning (the content-pass worklist), **not** a HARD failure,
  while the gate is unenforced. The enum is the target the content pass converges to.
- **`scope` is AUDIENCE only** — a list of `engineer/admin/sales/prospect/investor`. A legacy PROSE `scope` (audit docs
  historically used `scope` for coverage text) is **rehomed to `audited_scope`** by the seed; `scope` resets to the
  audience default. Do not put prose in `scope`.

## 7. Code stays frontmatter-free

The doc↔code link is **doc-side primary**: docs carry `code_refs` (and may point at volatile state — e.g. the live
tradfi/cefi instrument universe yaml — rather than embedding data that changes). **Source files carry NO frontmatter.**
A code→doc pointer is rare + opt-in: a single `See: <doc>` / `Implements: <doc-slug>` comment line citing the _why_
behind non-obvious code (`rg "Implements:.*<slug>"` jumps doc→code); docstrings explain WHAT a function does, not the
reasoning (C8).

## 8. Migration mapping — existing `type:` → `doc_type` + `nature`

Today's single `type:` conflates artifact-kind and content-kind (audit: 30+ values across 826 codex + plans). The
migration (W7 for codex; W3 for plans) splits it:

| Existing `type:`                                                                                             | → `doc_type`                      | → `nature` (typical)                                                                              |
| ------------------------------------------------------------------------------------------------------------ | --------------------------------- | ------------------------------------------------------------------------------------------------- |
| `plan` / `active-plan` / `sub-plan`                                                                          | `plan`                            | from body                                                                                         |
| `epic`                                                                                                       | `epic`                            | —                                                                                                 |
| `issue` / `question` / `question-doc`                                                                        | `issue`                           | `notes` / `record`                                                                                |
| `audit-result` / `audit-findings`                                                                            | `audit-result`                    | `record`                                                                                          |
| `audit-instructions` / `audit`                                                                               | `audit-instruction`               | `process`                                                                                         |
| `runbook`                                                                                                    | `codex-runbook`                   | `process`                                                                                         |
| `architecture`                                                                                               | `codex-ssot`                      | `design`                                                                                          |
| `codex-ssot` / `codex-section-readme`                                                                        | `codex-ssot` (README → exempt §9) | `ssot`                                                                                            |
| `code` / `infra` / `infrastructure` / `data` / `strategy` / `business` / `deployment` / `feature` / `object` | `codex-ssot` (mostly)             | inferred — these were domain hints → set `asset_group`/`stage`/`tags`, pick `nature` from content |
| `coordination-doc` / `orchestration-doc` / `analysis` / `mixed` / `project-management` / `refactor`          | nearest of the 9 (case-by-case)   | `notes` / `record` / `design`                                                                     |

`type:` is retired once a doc is migrated.

## 9. Exemptions (no frontmatter — whitelisted as data)

`README.md` (every level) · roadmap / index files (`INDEX.md`, `*INDEX*.md`) · **ledgers / pings** (`_*.md`, e.g.
`_agent_pings.md`) · format-spec docs (`PLAN_FORMAT.md`, this file's siblings) · repo-root meta (`CLAUDE.md`,
`.cursorrules`) · generated artifacts. These are whitelisted in the validator (`scripts/docs/docspec.py` `is_exempt`)
and the L0 index generator; adding frontmatter to them is NOT required.

## 10. Machine validator (docspec — W2 Phase 2)

A `docspec` module (`scripts/docs/docspec.py`, proposed) mirrors this doc: the enums (§5) + a `FieldSpec` per field
(Required / Conditional / Optional, per `doc_type`) + `validate_frontmatter(doc_type, fm) -> [violations]`, with a thin
CLI reused by the plans backfill (W3), the QG completeness gate (W5), and ad-hoc agent checks. The validator and this
human SSOT are kept in lockstep; the gate is wired **last** (D7).
