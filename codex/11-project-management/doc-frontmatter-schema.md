---
doc_type: codex-ssot
title: Documentation frontmatter schema — universal core + per-type fields (grep-native index)
summary:
  "The SSOT for every doc's frontmatter: a universal core on all doc types + per-type required/optional fields +
  closed-vocab enums, that turn frontmatter into a greppable L1 index. Mirrored by the docspec validator (W2)."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [frontmatter, rag, grep, doc-governance, docspec, agent-operating-framework]
related:
  [
    /plans/epics/agent_operating_framework_master.md,
    /plans/archive/2026_06/doc_frontmatter_schema_and_validator_2026_06_24.md,
    /codex/11-project-management/plan-hygiene.md,
  ]
created: 2026-06-24
authoritative_for:
  [doc frontmatter schema, doc_type vocabulary, per-type field requirements, frontmatter closed-vocab enums]
referenced_by:
  [
    /codex/11-project-management/plan-hygiene.md,
    plans/archive/2026_07/frontmatter_content_pass_and_gate_consolidation_2026_06_30.md,
    plans/archive/issues/plan_issue_epic_consolidation_2026_06_30.md,
  ]
owner: harsh
last_reviewed: 2026-10-27
code_refs: []
---

# Documentation frontmatter schema

> **CURRENT — fully enforced, BLOCKING (2026-07-04).** The W2 deliverable of
> [`agent_operating_framework_master`](../../plans/epics/agent_operating_framework_master.md). This is the human SSOT; a
> `docspec` machine validator (`scripts/docs/docspec.py`) mirrors it in lockstep. The two-checks lifecycle is
> **complete**: the live corpus reached **zero violations (HARD=0 SOFT=0, 1,298 docs) on 2026-07-04** and the single
> comprehensive blocking gate is live — `scripts/plan-hygiene/check_frontmatter_schema.py` calls
> `docspec.validate_frontmatter()` over the live trees (plans/active + epics + audit, codex, `*.mdc`) and **fails PM QG
> on any violation, HARD or SOFT**. The interim warn-only `check_docspec_coverage.py` is RETIRED. `plans/archive/**`
> **is deliberately outside the gated corpus** (operator decision 2026-07-04: archives are closed records — structurally
> seeded, summaries backfilled opportunistically, never ship-blocking).`agent-orchestrator/agents` (agent-role) is a
> separate repo, covered by that repo's gate (still a plan todo).

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

| Field         | Req | Values                                                         | Purpose                                               |
| ------------- | --- | -------------------------------------------------------------- | ----------------------------------------------------- |
| `doc_type`    | R   | the 9-value enum (§5)                                          | keystone search discriminator                         |
| `title`       | R   | human one-liner                                                | identity (NO `name` — filename is the id)             |
| `summary`     | R   | one-line "what this is / does"                                 | highest-leverage RAG field — read instead of the body |
| `status`      | R   | per-type lifecycle enum (§5)                                   | authority / freshness                                 |
| `nature`      | R   | `ssot\|guideline\|process\|design\|spec\|record\|notes\|issue` | content-kind facet (orthogonal to `doc_type`)         |
| `asset_group` | R   | list ⊂ domain enum (§5)                                        | **domain** axis (multi-value)                         |
| `stage`       | R   | list ⊂ pipeline enum (§5)                                      | **pipeline** axis (multi-value)                       |
| `repos`       | R   | list ⊂ workspace-manifest repos                                | **code** axis (single-line; `[]` if none)             |
| `scope`       | R   | list ⊂ `engineer\|admin\|sales\|prospect\|investor`            | **audience** axis (who the doc is for)                |
| `tags`        | R   | open free-list                                                 | topical RAG index (the overflow valve)                |
| `related`     | R   | list of doc slugs / paths                                      | cross-links (`[]` if none)                            |
| `created`     | R   | `YYYY-MM-DD`                                                   | —                                                     |

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

| `doc_type`            | + Required                                                                                                                                                  | + Optional                                                                                                                                                                                                           | `status` enum                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **plan**              | `parent_epic`, `assigned_vm` (registry ∪ `NA`), `execution_scope`, `priority`, `estimate_class`, `estimate_baseline_ai_days`, `estimate_calibrated_ai_days` | `last_updated`, `locked_by`, `locked_since`, `supersedes`, `superseded_by`, `depends_on`, `gate_on_depends`, `sequential`, `plan_order`, `source`, `assigned_role` (elective — registry), `context_scope` (elective) | `draft·active·blocked·paused·complete·superseded·cancelled` (`draft` = WIP/not-finalised → NOT ingested; flip to `active` to green-light dispatch. `depends_on` documents ordering + gates archival, NOT dispatch — UNLESS `gate_on_depends: true`, which makes regen wire it into a real cross-plan dispatch gate; `sequential: true` serialises a plan's own tasks. Full parallelism/prereq semantics: `plans/active/task_template.md` §4.) |
| **epic**              | `name` (slug — the one place `name` survives), `tier` (L0–L5), `priority`, `assigned_vm`, `parent`                                                          | `co_operators`, `codex_ssots`, `related_plans`                                                                                                                                                                       | `active·paused·complete·superseded` (`paused` = deliberately deferred by operator decision; todos valid but MUST NOT be dispatched until un-paused — added 2026-07-12 per operator ruling)                                                                                                                                                                                                                                                    |
| **issue**             | `parent_epic`, `priority`, `source`                                                                                                                         | `assigned_vm`, `resolved_by` (req when `resolved`), `locked_by`, `context_scope` (elective), `author` (elective)                                                                                                     | `open·blocked·resolved·false-positive·superseded`                                                                                                                                                                                                                                                                                                                                                                                             |
| **audit-result**      | `audited_scope`, `date`, `auditor`, `parent_epic`, `severity` (P0–P3 of worst finding)                                                                      | `resulting_plan`, `lib_version`, `doc_versions_checked`                                                                                                                                                              | `pass·partial·fail`                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **audit-instruction** | `tier`, `parent_epic`, `cadence`                                                                                                                            | `verifier`, `lifespan`                                                                                                                                                                                               | `active·retired`                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **codex-ssot**        | `authoritative_for`                                                                                                                                         | `referenced_by`, `owner`, `last_reviewed`, `code_refs`, `implementation_status` (elective)                                                                                                                           | `current·superseded·stale·draft`                                                                                                                                                                                                                                                                                                                                                                                                              |
| **codex-runbook**     | `owner`, `cadence`, `verifier`, `last_executed`                                                                                                             | `code_refs`                                                                                                                                                                                                          | `current·superseded·stale`                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **agent-role**        | `role`, `does`, `does_not`, `triggers`                                                                                                                      | `scope_tools`, `reports_to`                                                                                                                                                                                          | `draft·active·retired`                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **cursor-rule**       | _(keep Cursor's `description`, `priority`, `alwaysApply`, `globs`)_                                                                                         | `tags`                                                                                                                                                                                                               | — _(Cursor-governed; just add `doc_type`)_                                                                                                                                                                                                                                                                                                                                                                                                    |

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
- **`assigned_role`** (plan, **ELECTIVE**, added 2026-07-14): the craft role dispatching a plan's todos — validated
  against the LIVE registry of `role:` values under `unified-trading-pm/agents/*.md` (e.g. `data_engineering`, `infra`,
  `backend-engineer`, `ui-developer`, `review`, …), not a hand-grown enum, so a new role file is instantly a valid value
  with no schema edit. Elective (like `implementation_status`) because ~26 plans predate the field and legitimately
  carry no value yet; a PRESENT value is HARD-validated — a hand-typed near-miss (`data-pipeline-engineer`,
  `infra-engineer` — 19 occurrences found + fixed 2026-07-14) silently routes nowhere in AO dispatch, so a typo here is
  a real defect, not a content gap. Per-task `[TAG]` routing (`[INFRA]`/`[DATA]`/`[BACKEND]`/`[UI]`/`[REVIEW]` → role)
  is documented in `plans/active/task_template.md` §3 but not yet independently machine-validated — today
  `assigned_role` is the single source of truth for a plan's dispatch role.
- **`context_scope`** (plan + issue, **ELECTIVE**, added 2026-07-30): a minimal free-list reading list — codex SSOTs,
  related plan/issue docs, and key source paths — a worker should read before touching this doc, computed and maintained
  by the daily `/context-scout` skill (`agent-orchestrator`'s `context_scout` plan-health dispatch mode). Elective, not
  optional: most of the ~550-doc corpus predates the field and is backfilled incrementally, not all at once, so a
  present-but-empty convention would just be noise on every doc `/context-scout` hasn't reached yet. Target 2-6 entries
  — this is a curated pointer list for cutting a fresh worker's cold-start context burn, not an exhaustive index; see
  `cursor-configs/skills/context-scout/SKILL.md` for the population procedure. **Consumption side (shipped
  2026-08-08)**: `agents/RULES.md` § "0. STEP 0" now instructs every worker to read a dispatched task's `plan_ref`
  `context_scope` entries before starting any todo (a no-op fallback when absent) — fleet-wide, not pilot-scoped,
  because the instruction degrades safely on the ~66% of the corpus still `NEVER_SCOUTED`/`STALE` (measured via
  `scripts/plan-hygiene/generate_context_scope_inventory.py`, re-run periodically). Corpus coverage crossing "majority
  `UP_TO_DATE`" is a precondition for any FURTHER enforcement (e.g. a QG-style dispatch gate) — not yet met as of the
  2026-08-08 measurement; see `/plans/archive/2026_08/issues/context_scope_consumption_enforcement_2026_07_30.md` for
  the design rationale + freshness-measurement history.
- **`author`** (issue, **ELECTIVE**, added 2026-08-04): the author of the issue doc. Mandated by worker.md §4.5
  (FINDINGS CLOSURE, HARD RULE 2026-06-10) which requires issue-doc frontmatter to carry
  `title`/`created`/`author`/`source[]`. Elective, not required: only 6 of 444 existing issue docs carry `author` today
  (2026-08-04); Required would red the tree. Backfill to the existing corpus is a tracked follow-up; new issue docs
  SHOULD include `author` per worker.md §4.5.
- **`authoritative_for`** (codex-ssot) is the single highest-value codex field — "what this doc is THE SSOT for" — so an
  agent asking "the canonical rule for X" greps it and lands on the one right doc, not 826. 64 codex docs already carry
  it.
- **`implementation_status`** (codex-ssot, **ELECTIVE** — a third requirement level, operator decision 2026-07-06): the
  strategy-archetype implementation-maturity axis
  (`design · code-shipped · stub · active · theoretical-only · live · complete`), restored after enum normalization
  flattened it out of `status:` (which is doc-lifecycle, not implementation maturity). **Elective ≠ optional**: an
  optional key must be present-but-empty (§6); an elective key is legitimately ABSENT on docs where the axis doesn't
  apply — only `codex/09-strategy/architecture-v2/**` archetype docs carry it (66 docs at restore time). The value is
  enum-validated (HARD) when present. Don't add elective fields casually — present-but-empty stays the default
  convention; elective exists for subfolder-scoped axes where corpus-wide empty keys would be noise.
- **`code_refs`** (codex) is the L4 jump (doc→code). **Point at the smallest STABLE unit — module/package directory by
  default; an exact file only for stable single-file entry points** (content-pass rot data: file citations break on most
  refactors, their module dirs survive; repo-level is already the `repos:` facet). Existence is checked by a scheduled
  host-side audit, never a blocking commit gate (codex lives in PM, code in service repos — no cross-repo atomicity).
  Backfill deferred (W7 rider); full locked decision: `plans/epics/agent_operating_framework_master.md` § "L4
  `code_refs` granularity + enforcement". Code stays frontmatter-free (§7).

## 4. The `nature` facet (content-kind, orthogonal to `doc_type`)

`doc_type` says _what artifact_ (plan, codex-ssot, …); `nature` says _what kind of content_, so two codex-ssots can be a
hard `ssot` vs a soft `guideline`. It also feeds **derived authority** (§6): a `nature: ssot` + `status: current` doc is
authoritative; a `nature: notes` + `status: draft` doc is not.

`ssot` (THE source of truth) · `guideline` (recommended practice) · `process` (a how-to / runbook procedure) · `design`
(architecture / rationale / why) · `spec` (a contract / schema / API surface) · `record` (an immutable log: audit
result, handoff, decision) · `notes` (working notes, not normative) · `issue` (an incident / defect / gap report — the
natural value for `plans/active/issues/` docs; added 2026-07-06 after three independent authors reached for it against
the enum).

## 5. Closed-vocab enums (seed values — grown organically)

Closed facets are **enforced enums in the validator**, but **start small and grow as real needs surface** (NOT frozen
day-1). Target ≤~10–15 values each; past ~15 → consolidate, OR it should have been `tags` (the open free-list).

- `doc_type` (9):
  `plan · epic · issue · audit-result · audit-instruction · codex-ssot · codex-runbook · agent-role · cursor-rule` —
  **PATH-derived and path-checked (HARD, 2026-07-06)**: the validator derives the true type from the doc's location
  (`docspec.doc_type_for_path`) and a declared `doc_type:` that contradicts it is a HARD violation ("fix the field or
  move the doc"). A doc in `plans/active/issues/` IS an issue — declaring `doc_type: plan` there was the recurring
  authoring mistake this check kills.
- `nature` (8): `ssot · guideline · process · design · spec · record · notes · issue`
- `asset_group` (11):
  `cefi · defi · tradfi · sports · prediction · cross-cutting · ao · ci · infrastructure · ui · meta` (`ui` added
  2026-07-30 — deployment-ui/deployment-api/unified-trading-system-ui closeout tranche, mirroring the 2026-07-27
  `ao`/`ci`/`infrastructure` split; see `ui_consolidated_closeout_2026_07_30.md`)
- `stage` (9): `data · features · strategy · backtest · paper · live · execution · reporting · meta`
- `scope` / audience (5): `engineer · admin · sales · prospect · investor`
- `priority` (4): `P0 · P1 · P2 · P3`
- `tier` (epic, 6): `L0 · L1 · L2 · L3 · L4 · L5`
- `status`: per-type (see §3) — NOT a single global enum.

**Registry-validated (not hand-grown enums):** `assigned_vm` → `orchestrator_vm_registry.yaml` ids ∪ `{NA}` ·
`parent_epic` → an epic slug under `plans/epics/` · `repos` → `workspace-manifest.json` repositories · `assigned_role`
(plan, elective) → a `role:` value under `unified-trading-pm/agents/*.md`. These can exceed 15 values because they
validate against a live registry, not a curated enum.

## 6. Conventions

- **Empty = `null` / `[]`, never omitted.** Every field is always present; an empty optional is `field:` (null) or
  `field: []` (list). So `rg '^summary: \S'` = "has a real summary"; a missing key is a **validator error**, not "N/A".
  The ONE exception: **elective** fields (§3 `implementation_status`) are legitimately absent where their axis doesn't
  apply — enum-validated only when present.
- **Schema-sanctioned valid-empties (2026-07-04, validator in lockstep):** a present-but-empty **list** `repos: []` /
  `related: []` is VALID (§2 "[] if none" — a doc may genuinely govern no repo / have no sibling);
  `authoritative_for: []` is VALID when `status` ∈ {superseded, stale, draft} (a non-current doc claims no SSOT topic);
  a **superseded epic** may leave `name`/`tier`/`priority`/`parent` empty (retired identity). All other required-empty
  remains a SOFT "needs content".
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
`.cursorrules`) · generated artifacts · **`plans/active/scratch_scenarios_day1/*.md`** (structured scenario-design specs
feeding `/codex/04-architecture/scenario-injection-architecture.md` — tables, not tracked plans with priorities/todos).
These are whitelisted in the validator (`scripts/docs/docspec.py` `is_exempt`, basename set `EXEMPT_BASENAMES` +
directory-prefix set `EXEMPT_DIR_PREFIXES`) and the L0 index generator; adding frontmatter to them is NOT required.

## 10. Machine validator (docspec — W2 Phase 2)

A `docspec` module (`scripts/docs/docspec.py`, proposed) mirrors this doc: the enums (§5) + a `FieldSpec` per field
(Required / Conditional / Optional, per `doc_type`) + `validate_frontmatter(doc_type, fm) -> [violations]`, with a thin
CLI reused by the plans backfill (W3), the QG completeness gate (W5), and ad-hoc agent checks. The validator and this
human SSOT are kept in lockstep; the gate is wired **last** (D7).

## 11. Enforcement sequencing — soak-then-gate (the wiring is LAST)

**The schema + validator ship BEFORE any enforcement, on purpose.** A frontmatter gate that hard-fails on day one would
red every ship across the fleet while the existing corpus is still non-conformant. So enforcement is wired **last** (the
D7 "soak"), and only after the corpus it gates has converged. Each workstream is a separate plan:

- **W2 (`doc_frontmatter_schema_and_validator`) — THIS deliverable.** Ships the shape (this doc) + the `docspec`
  validator + CLI **ONLY**. No tree-wide enforcement, no backfill, no new blocking QG step. The schema "soaks" first.
- **W3 (plans backfill).** Backfills `plans/active/*` + `plans/archive/*` frontmatter to this schema using the CLI until
  the plans corpus is HARD-green.
- **W5 (plan-gate flip).** Flips the plan-hygiene completeness gate **warn → error** once the plans corpus is green —
  the first place enforcement actually blocks.
- **W6 / W7 (per-type coverage).** Extend coverage to the remaining doc types (W7 = codex; W6 = role-charters), converge
  the SOFT content fields (`summary`/`tags`/`authoritative_for`), then collapse to the **one comprehensive blocking
  gate** under `check_frontmatter_schema` (per the two-checks lifecycle in the header banner).

The soak ended 2026-07-04: the corpus converged to zero violations and the single comprehensive blocking gate
(`check_frontmatter_schema.py`, docspec-backed) now fails QG on any HARD or SOFT violation across the live trees
(archives excluded). The staging contract above is retained as the historical record of how enforcement was sequenced.
