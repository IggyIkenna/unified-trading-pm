---
doc_type: plan
title:
  Strict VM matching + frontmatter governance — DESIGN-CAPTURE APPENDIX (promoted to agent_operating_framework_master)
summary:
  Design-capture appendix for strict VM matching and frontmatter governance — rationale, research, and A/B decisions
  promoted to the agent_operating_framework_master epic and split child plans.
status: active
nature: process
stage: [meta]
repos: [agent-orchestrator, deployment-ui, instruments-service]
scope: [engineer, admin]
tags: [orchestrator, vm-matching, frontmatter, governance, design-capture, dispatch]
related: []
created: 2026-06-24
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 5
last_updated: 2026-06-24
locked_by: NA
locked_since: NA
supersedes:
superseded_by:
depends_on: []
source:
asset_group: cross-asset
drift_direction: advance-code
---

# Strict per-plan VM matching + plan frontmatter completeness governance

> **⚠️ PROMOTED — this is now the DESIGN-RATIONALE APPENDIX, not an execution plan (2026-06-24).** The decisions,
> research, audits, and A/B analysis below were promoted into the epic
> [`../epics/agent_operating_framework_master.md`](../epics/agent_operating_framework_master.md) (the durable SSOT) and
> split into per-workstream child plans (W1 `dispatch_strict_vm_matching_2026_06_24` · W2
> `doc_frontmatter_schema_and_validator_2026_06_24` · W3–W8 — see the epic's workstream registry). This doc is kept as
> the **rationale-of-record** (the full external-research URLs + the C1–C8 / D1–D21 decision pass + the audit numbers),
> so nothing is lost. `assigned_vm: NA` → it dispatches to **nobody**; its **§ Phased execution DAG below is
> SUPERSEDED** by the epic's workstreams — do NOT execute from it (read W1/W2/… instead).

## Problem

The local `harsh_pc` agent-orchestrator backend ingested **34 tasks**, of which only **1**
(`scripts_lifecycle_marker_rollout`) was actually assigned to `harsh_pc`; the other **33** came from ~14 data-pipeline
plans owned by `vm-tradfi` / `vm-defi` / `vm-cefi` / `vm-prediction` / `vm-sports` / `vm-ml`. Two compounding causes:

1. **Matching is non-strict by default.** `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH` defaults `False` ([config.py:538]), so a
   backend ingests its own plans **plus every "global/unassigned" plan**.
2. **Epic→VM delegation silently resolves to "global".** Active plans carry no own `assigned_vm`; they delegate via
   `parent_epic`. But regen reads plans from a `git archive <LDR> plans/active` snapshot that omits `plans/epics/` — so
   `_resolve_plan_vms` can't read the epic's VM, returns an empty set ("global"), and every backend adopts the plan.
   (Regression of the bug the code's own docstring says was fixed 2026-06-16, re-introduced by the 2026-06-23
   LDR-snapshot change.)

## Design decisions (LOCKED — operator, 2026-06-24)

- **D1. Strict, fail-closed matching is the enforced default.** A backend ingests a plan **iff**
  `plan.assigned_vm == backend_id`. Unset or `NA` → **nobody** picks it up. Mismatch → skip.
- **D2. `assigned_vm` is a mandatory, per-plan field; epic→VM delegation is DROPPED for matching.** `parent_epic` stays
  for orphan-check + priority rollup only. (Side effect: the `plans/epics`-not-in-snapshot bug becomes **moot** — the
  matcher never reads epics again.)
- **D3. `assigned_vm` valid domain = `{registry VM ids}` ∪ `{NA}`.** `NA` = intentionally unassigned / future plan →
  matches no backend → not dispatched. This is the ONE field where `NA` is a first-class valid value (it doubles as the
  "not yet live" switch). All OTHER mandatory fields must be present + valid + **never** `NA`; optional fields must be
  present and are valid-or-`NA`.
- **D4. Reassignment = edit `assigned_vm`, push to LDR.** Old backend prunes its **queued** tasks (already wired — prune
  shares the match gate, [regen_backlog_from_plan.py:338-346]); new backend ingests on next regen. Task ids are stable
  (`plan_ref` + item) so no id-level duplication.
- **D5. Mid-flight reassignment is operator-managed.** If the source backend has dispatched/in-flight (unflipped) tasks
  at reassignment, a small effort-duplication window is tolerated. The operator has the signal already (dashboard shows
  dispatched counts per backend) — drain first or accept the dup.
- **D6. Down VM → manual reassignment only** (agents do it, operator-gated). No automated failover, no `fallback_vm`
  field.
- **D7. Sweep-then-enforce.** Populate frontmatter on all active plans first; let it propagate to all slots/VMs; THEN
  flip the QG gate to enforcing. Archive plans are **excluded** from the gate.

### Considered & REJECTED (do not re-propose)

- **Per-task "claim marker" pushed to LDR at task START** (a `<!--claim:backend@ts-->` tag so a reassigned backend sees
  in-flight items). Correct in principle but **rejected for cost**: a claim commit would fire on _every task pickup
  fleet-wide_ (not just reassignment), ~doubling commit volume + PR-sync CI for a dedup benefit that only materializes
  in the rare, operator-gated mid-flight case. Operator-awareness (D5) covers it at zero cost. A zero-commit dashboard
  soft-warning on the reassignment path is the only acceptable future upgrade — out of v1 scope.

## Open for operator

- **Supersede targets**: no single dedicated "frontmatter" plan exists to supersede wholesale. The closest prior owners
  of this scope are `orchestrator_v07_multi_vm_topology_2026_05_21.md` (introduced `assigned_vm` mandatory) and
  `agent_orchestrator_backlog_state_alignment_2026_05_29.md` (backlog regen). Phase 5 adds **partial-supersede** banners
  pointing here for the VM-assignment + frontmatter scope, leaving their other scope intact. Confirm that's the intent
  (vs a full supersede).
- **Field-set decisions (D8–D10)** — gate the schema before backfill; see § Frontmatter audit + proposed schema below.

## Frontmatter audit + proposed schema (2026-06-24)

Two goals drive this schema:

1. **Dispatch correctness** — `assigned_vm` is the strict matcher (D1–D3).
2. **Fast-grep / RAG index** — frontmatter becomes a structured, greppable index so an agent narrows 110 plans to the
   relevant few WITHOUT opening any (search by asset_group / repo / topic / status).

### Audit

Methodology: parsed YAML top-level keys across **110 active plans, 25 epics, 58 issue docs**; enum value distributions
via `grep`. De-facto mandatory today (110/110 active): `title`, `status`, `priority`, `parent_epic`, `locked_by`,
`estimate_class`, `estimate_baseline_ai_days`, `estimate_calibrated_ai_days`.

Gaps & drift:

| Issue                                    | Evidence                                                                                          | Goal                          |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------- | ----------------------------- |
| `assigned_vm` missing on 20 active plans | 90/110 have it (the 20 listed below)                                                              | 1                             |
| `asset_group` essentially absent         | 0/110 active, 1/25 epics                                                                          | 2 (#1 search axis)            |
| no `repos` field                         | `repo_gates` on 3, `owner_repos` on 1 epic                                                        | 2                             |
| no `tags`/`keywords`                     | none                                                                                              | 2                             |
| `execution_scope` under-set              | 35/110; some hold the unfilled template literal                                                   | 1                             |
| malformed `status` values                | ~4 plans have prose in `status:` (e.g. `status: Phase 6.4… ✅ shipped…`)                          | both (breaks enum grep)       |
| `name` vs `title` drift                  | 17 active carry a stray `name`; epics carry both (23 each)                                        | both                          |
| epic-link field drift                    | `parent_epic` (active/issues) vs `parent` (epics) vs `epic` (task_template)                       | both                          |
| `task_template.md` wholly stale          | emits name/overview/type/epic/completion_gates/repo_gates/todos/isProject                         | new plans born non-conformant |
| field sprawl                             | ~20 one-off keys (umbrella, plan_of_record, parent_consolidation, gate, audit_ref, orchestrates…) | noise                         |

Clean closed sets confirmed: `priority` {P0:41, P1:37, P2:29, P3:3}; `estimate_class` {infra:63, refactor:16,
brand-new:15, design:11, research:5}; `status` ~all `active` (modulo the 4 malformed).

The 20 `assigned_vm`-gap plans: cefi_deribit_binance_futures_bundle_verification · cefi_ml_directional_continuous_live ·
colocated_feature_pipeline_in_memory_handoff · data_pipeline_acquisition_remediation · defi_governance_params_refresh ·
defi_mtds_subgraph_and_adapter_fixes · defi_onchain_derivable_values_and_date_drift ·
defi_pipeline_e2e_and_coverage_validation · harsh_day_master · mdps_adapter_protocol_pandas_to_polars ·
predictions_lookahead_and_reader_migration · predictions_ml_walk_forward_and_arb ·
predictions_other_bucket_and_ui_drilldown · sports_features_readiness_for_predictions ·
sports_fixtures_schema_split_completion · sports_odds_bookmaker_coverage_enumeration ·
sports_phantom_recon_and_coverage_windows · tradfi_cme_event_contract_backfill ·
tradfi_sp500_ml_and_arb_backtest_readiness · work_split_2026_05_22_ikenna.

### Proposed schema — plan family (active plans + issue docs)

MANDATORY — always present, valid, NEVER `NA` (except `assigned_vm`):

| Field                                                          | Values                                                                        | Serves | Notes                                                                  |
| -------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------- |
| `title`                                                        | human one-liner                                                               | RAG    | retire stray `name` on plans; filename is the slug                     |
| `summary`                                                      | one-line "what this does"                                                     | RAG    | NEW — grep this instead of opening the plan                            |
| `status`                                                       | `active\|blocked\|paused\|complete\|cancelled\|superseded`                    | both   | fix the 4 malformed                                                    |
| `priority`                                                     | `P0..P3`                                                                      | both   | clean already                                                          |
| `parent_epic`                                                  | epic slug (registry-validated)                                                | both   | canonical epic link; retire `epic`/`parent` aliases on non-epics       |
| `assigned_vm`                                                  | `{registry VM id}` ∪ `NA`                                                     | 1      | dispatch matcher; `NA` = future/unassigned → nobody                    |
| `execution_scope`                                              | `orchestrator-agent\|local-only`                                              | 1      | explicit on ALL (no implicit default)                                  |
| `asset_group`                                                  | `cefi\|defi\|tradfi\|sports\|prediction\|cross-cutting\|infrastructure\|meta` | 2      | NEW — auto-seed from `parent_epic`                                     |
| `repos`                                                        | inline list `[mtds, instruments-service]`                                     | 2      | NEW — single-line so `rg '^repos:.*mtds'` works; `NA` if cross-cutting |
| `tags`                                                         | inline list `[backfill, manifest, honest-absence]`                            | 2      | NEW — the topical RAG index                                            |
| `estimate_class` / `_baseline_ai_days` / `_calibrated_ai_days` | enum / N / N                                                                  | —      | already universal                                                      |
| `created`                                                      | `YYYY-MM-DD`                                                                  | —      | make mandatory (90/110 today)                                          |

OPTIONAL — present, value-or-`NA`: `related_plans` (inline list) · `source` (provenance / audit ref — absorbs
`audit_ref`) · `last_updated` · `locked_by` / `locked_since` · `supersedes` / `superseded_by` · `model_tier` /
`thinking_tier` · `depends_on`.

RETIRE / fold: `umbrella`, `plan_of_record`, `parent_consolidation`, `master`, `orchestrates`, `gate`, `smoke_gate` →
into `parent_epic` / `related_plans` / `tags`. (`name` stays only on epics as the slug.)

NA rule: mandatory fields present + valid + never `NA`; optional fields present, value valid-of-its-type OR literal
`NA`. `assigned_vm` is the one mandatory field whose valid domain includes `NA` (= intentionally unassigned / future
plan, dispatched to nobody).

### Why this is a fast-grep / RAG layer

Three things make frontmatter a real index, all missing today: **completeness** (every plan has every field → grep never
silently misses), **normalized closed-set values** (no prose in enums), and **explicit search axes that don't exist**
(`asset_group`, `repos`, `tags`, `summary`). Then an agent narrows the corpus without opening anything:

```
rg -l '^asset_group: defi' plans/active | xargs rg -l '^assigned_vm: vm-defi'   # defi work owned by vm-defi
rg -l '^repos:.*\bmtds\b'  plans/active                                          # everything touching mtds
rg -l '^tags:.*backfill'   plans/active                                          # topical sweep
rg '^(title|summary):'      plans/active/<slug>.md                               # 2-line gist, no full read
```

The single-line inline-list convention for `repos` / `tags` / `related_plans` is the key RAG optimization — each axis is
one greppable line.

### Open decisions (operator) — gate the field set BEFORE backfill

- **D8. RAG fields** — ship all of `summary` + `tags` + `repos` (the bulk of backfill effort), or trim?
- **D9. `asset_group`** — explicit field (best for grep; recommended) vs derive-from-`parent_epic` at read time (zero
  backfill, not directly grep-able)?
- **D10. Naming** — standardize plans on `title` and retire the 17 stray `name` fields — confirm?

## Other doc-type frontmatter audit + proposed schemas (multi-pass — first pass)

**Why this matters (the heavy-AO future).** AO is moving from a work-throughput parallelizer toward an always-on
automation layer: escalator agents (CI/CD), plan-reconciler (active-plans/issues/codex/code →
done-vs-remaining-vs-correct), and next — infra-scaling agents, test/staging/prod health, data-pipeline +
strategy/execution-VM monitoring, log-debugging. With a 2-person dev team this replaces the specialist desks a big shop
staffs. Those agents can only act correctly if they can **find the right doc fast** and **know what to do / not do** —
so every doc's frontmatter must be a clean, greppable, intent-bearing index. This pass audits + proposes frontmatter per
doc type. **Content/intent standardization + the controlled tag vocabulary are later passes** (acknowledged multi-pass,
back-and-forth effort).

### Landscape audit (measured 2026-06-24)

| Doc type          | Location                    | Count   | FM coverage | Current top keys                                                                                                                          | Gap for RAG / AO                                                                                                                                             |
| ----------------- | --------------------------- | ------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Codex SSOT        | `codex/**`                  | **826** | 826/826     | `scope`(826), `last_reviewed`(292), `status`(193), `title`(122), `authoritative_for`(64), `referenced_by`(64), `related`(61), `owner`(58) | `scope` universal but `title`/`status`/`authoritative_for`/`tags` spotty; no `doc_type`/`summary`/`domain` → agents can't reliably land on the canonical doc |
| Codex runbook     | `codex/15-runbooks`         | subset  | —           | + `verifier`/`last_executed`/`cadence`(29 each)                                                                                           | 4-field execution SSOT exists; needs `doc_type: codex-runbook`                                                                                               |
| Audit result      | `plans/audit/results`       | 84      | 53/84       | `type`,`status`,`title`,`epic`,`date`,`auditor`,`source`                                                                                  | 31 lack FM; `epic`≠`parent_epic` drift; no `summary`/`tags`/severity                                                                                         |
| Audit instruction | `plans/audit/instructions`  | 21      | 19/21       | `type`,`tier`,`name`,`epic`,`assigned_vm`,`last_updated`                                                                                  | fairly consistent; `epic`→`parent_epic`; add `summary`/`tags`                                                                                                |
| AO agent-role     | `agent-orchestrator/agents` | 11      | **0/11**    | (none)                                                                                                                                    | ZERO frontmatter — the agents that RUN the automation have no machine-readable role / triggers / boundaries                                                  |
| Cursor rule       | `**/.cursor/rules/*.mdc`    | 3043\*  | 3026        | `description`,`priority`,`alwaysApply`,`tags`,`globs`                                                                                     | already decent (Cursor schema); \*count inflated by per-repo duplication; low priority                                                                       |
| Archive plan      | `plans/archive`             | 1065    | 973         | (plan schema)                                                                                                                             | excluded from QG gate (D7); ~92 lack FM; leave                                                                                                               |

### Proposal — a UNIVERSAL CORE on every doc + per-type extensions

Highest-leverage primitive: **`doc_type`** — the discriminator that scopes any agent search.
`rg -l '^doc_type: codex-ssot'` → search only the knowledge base; `rg -l '^doc_type: agent-role'` → the agent playbooks.
Universal core (every doc, all types):

| Field      | Values                                                                                                   | Purpose                                 |
| ---------- | -------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| `doc_type` | `plan\|epic\|issue\|audit-result\|audit-instruction\|codex-ssot\|codex-runbook\|agent-role\|cursor-rule` | the search discriminator                |
| `title`    | human one-liner                                                                                          | identity (standardize off `name`)       |
| `summary`  | one-line gist                                                                                            | RAG — read this, not the whole doc      |
| `status`   | per-type lifecycle enum                                                                                  | authority / freshness                   |
| `tags`     | inline controlled-vocab list                                                                             | topical RAG index                       |
| `domain`   | `cefi\|defi\|tradfi\|sports\|prediction\|cross-cutting\|infrastructure\|meta`                            | domain axis (= `asset_group` for plans) |
| `related`  | inline list of doc slugs                                                                                 | cross-links                             |

Per-type extensions:

- **codex-ssot** (+): `authoritative_for` (what this doc is THE SSOT for — RAG-critical), `scope` (keep, already
  universal), `referenced_by`, `owner`, `last_reviewed`, `code_refs` (repos/paths it governs). → an agent asking
  "canonical rule for manifest honest-absence?" greps `authoritative_for`/`tags` and lands on the one right doc,
  not 826.
- **codex-runbook** (+): keep the 4-field execution SSOT `owner`/`cadence`/`verifier`/`last_executed`.
- **audit-result** (+): `audited_scope`, `date`, `auditor`, `parent_epic` (fix `epic` drift), `resulting_plan`,
  `severity` (P0..P3 of worst finding). Backfill the 31 missing FM.
- **audit-instruction** (+): keep `tier`/`assigned_vm`/`parent_epic` (rename from `epic`) + the core.
- **agent-role** (NEW — highest AO leverage): `role` (worker/escalate/monitor/plan-reconciler/…), `summary`, `does` /
  `does_not` (explicit boundaries — "what to do / not do"), `triggers` (when it fires), `scope`/`tools`, `related`. A
  machine-readable charter for every automation agent — the backbone for the infra-scaling / health / log-debug agents
  being added next.
- **cursor-rule**: already has `description`/`priority`/`alwaysApply`/`tags`/`globs`; just add `doc_type: cursor-rule`;
  otherwise leave (Cursor-governed). Lowest priority.

### Three biggest wins (priority order)

1. **`doc_type` everywhere** — turns the whole corpus into a scoped, greppable index (cheap, mechanical).
2. **Codex consistency (826 docs)** — `doc_type`+`title`+`summary`+`status`+`authoritative_for`+`tags` on every SSOT →
   agents reliably find the canonical "what to do" doc. The single biggest RAG payoff.
3. **agent-role frontmatter (11 docs, currently 0)** — charters for the automation agents themselves; tiny effort,
   directly enables the heavy-AO future (what each agent does / must not do).

### Deferred to later passes (flagged, not now)

- The controlled **tag vocabulary** (so `tags` grep doesn't miss synonyms) — needs a content pass.
- Doc **content/intent** standardization (separate from frontmatter).
- Archive backfill (excluded from the gate per D7); cursor `.mdc` dedup (3043 → de-duplicated).

### Open decisions (operator)

- **D11.** Adopt `doc_type` as the universal discriminator across all doc types? (rec: yes — the key RAG primitive)
- **D12.** Codex schema: enforce the core on all 826 at once (high value, big sweep), or start with the high-traffic
  dirs (`09-strategy`, `15-runbooks`, `04-architecture`, `02-data`) first?
- **D13.** agent-role frontmatter (incl. explicit `does`/`does_not`) — fold into this effort, or its own AO plan?

## External research + target architecture (2026-06-24)

> **Status: thinking captured, decisions NOT yet finalized.** Once the shapes below are agreed, this effort splits into
> an **epic + per-workstream child plans** (the current § Phased execution DAG becomes the dispatch child). Preserved
> here so the research isn't lost. Supersedes the "grep-only completeness" framing of the two audit sections above where
> they conflict — those audits stay valid as the _foundation_.

### A. Sources surveyed + takeaways

- **Diátaxis — docs by purpose** ([diataxis.fr](https://diataxis.fr/)). Four kinds on two axes (action↔knowledge,
  study↔work): **tutorial** (learn), **how-to** (solve a task), **reference** (look up facts), **explanation**
  (understand why). → classify by _purpose_, not just artifact type — a debugging agent wants a how-to; a
  design-decision agent wants explanation.
- **llms.txt — generated machine-readable doc map** ([llmstxt.org](https://llmstxt.org/); adopted by
  Anthropic/Cloudflare/Vercel). Format: H1 title → blockquote summary → H2 sections of `[name](url): note` links + an
  "Optional" section droppable for shorter context. → one small index agents read FIRST to route, instead of scanning
  the corpus.
- **AGENTS.md — open standard for agent instructions** ([agents.md](https://agents.md/); GitHub's
  [2,500-repo study](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/);
  donated to the Linux Foundation / AAIF, Dec 2025). Six areas (commands, testing, structure, style, git,
  **boundaries**). Findings: **3-tier boundaries — Always do / Ask first / Never do**; **specificity > vagueness**,
  **concrete examples > prose**, **persona clarity**; **LLMs reliably follow only ~150–200 instructions** (quality
  degrades as count grows). Cross-tool (Cursor/Codex/Windsurf/Aider…).
- **Metadata for RAG / enterprise retrieval** ([arXiv 2512.05411](https://arxiv.org/pdf/2512.05411),
  [Unstructured](https://unstructured.io/insights/how-to-use-metadata-in-rag-for-better-contextual-results),
  [Deasy Labs](https://www.deasylabs.com/post/using-metadata-in-retrieval-augmented-generation)). Metadata = a
  **pre-filter** narrowing the search space; **authority + recency weighting + reranking** float high-trust, current
  docs and down-weight stale/low-authority; **self-query** = agent turns an NL question into structured filters;
  **LLM-generated metadata** beats manual annotation at scale. → normalized, authority/recency-bearing facets make
  retrieval precise, _independent of grep-vs-vector_.
- **Context engineering** ([mem0](https://mem0.ai/blog/context-engineering-ai-agents-guide),
  [Redis](https://redis.io/blog/context-engineering-best-practices-for-an-emerging-discipline/)). **More context is
  worse** — a Chroma study found all 18 models degraded as input grew. → retrieve **less but right**; progressive
  disclosure (summary → full); keep always-loaded rules lean (the ~150–200 ceiling). This is the governing principle for
  the whole design.

### B. Retrieval-method DECISION — grep-native, NOT vector RAG (operator-confirmed 2026-06-24)

For agentic coding/ops the retrieval primitive is **grep/glob/read over the filesystem** — what Claude Code and Codex
actually use — **not** an embeddings/vector store. Grep is **exact** (no false-neighbour noise), **always fresh** (no
re-index lag), **transparent** (the agent sees _why_ a doc matched and reasons about its next search), and needs **zero
infra**. A vector DB adds staleness + opacity + ops cost for negative value on a structured corpus we control.
**Embeddings/hybrid retrieval is REJECTED.** The metadata best-practices above are applied to make _grep_ precise
(structured facets + a generated index + authority/recency), not to feed a vector store.

### C. Pass-1 proposal vs adopted upgrades

| Dimension        | Pass-1 (completeness)    | Adopted (state-of-the-art)                                                               |
| ---------------- | ------------------------ | ---------------------------------------------------------------------------------------- |
| Classification   | single `doc_type`        | two facets: `doc_type` (artifact) + `doc_kind` (Diátaxis purpose)                        |
| Find the doc     | per-query grep over 826  | **generated index** (`llms.txt`-style) per scope; read the map first                     |
| Boundaries       | 2-tier `does`/`does_not` | **3-tier Always / Ask-first / Never** (= the delegation dial)                            |
| Trust for acting | `status` only            | `authority` (`hard-rule\|normative\|informational\|draft`) + `last_reviewed`/`review_by` |
| Retrieval method | grep                     | grep-native, KEPT — made precise by facets + index (NOT embeddings)                      |
| Backfill         | manual                   | LLM-generated metadata + human spot-check (an AO automation)                             |
| Context budget   | "complete frontmatter"   | retrieve less but right; progressive disclosure; lean always-loaded rules                |
| Portability      | bespoke                  | align agent/repo docs to the AGENTS.md standard                                          |

### D. Target architecture

**D-1. Grep-native layered context** — every layer grep-navigable; each hop loads the minimum:

| Layer      | What                                                                                        | Reader                                  | Source                                                |
| ---------- | ------------------------------------------------------------------------------------------- | --------------------------------------- | ----------------------------------------------------- |
| L0 Map     | generated index (`llms.txt`-style) per scope: `title · summary · facets · path`             | humans monitoring + agents routing      | generated FROM frontmatter (CI artifact, never stale) |
| L1 Facets  | frontmatter (`doc_type`/`doc_kind`/`domain`/`authority`/`tags`/`repos`/`authoritative_for`) | agent narrows with one grep             | the doc                                               |
| L2 Summary | one-line `summary`                                                                          | agent confirms relevance before opening | the doc                                               |
| L3 Body    | full SSOT content                                                                           | agent, only the confirmed doc(s)        | the doc                                               |
| L4 Direct  | `code_refs` → exact code/workflow paths                                                     | agent jumps doc→code, no search         | frontmatter                                           |

Humans live at L0 and drop to L3/L4 only when needed; agents traverse L0→L4. The generated index is the "high-level
context" layer and is the SAME investment as the frontmatter (built from it).

**D-2. Boundary tier = delegation dial.** Agent-role docs declare each action Always / Ask-first / Never,
machine-readable + versioned. Graduating an agent (e.g. escalate-agent auto-closing CI PRs) = flipping actions
Ask-first→Always with an audit trail of when + on what evidence.

**D-3. Trust substrate.** `authority` + freshness on every doc; an acting agent declines/escalates on a stale or
non-normative doc rather than acting on it — the safety floor under gradual delegation.

**D-4. Maintenance / eval loop.** Frontmatter agent-maintained (LLM drafts `summary`/`tags`/`domain`, human
spot-checks); index regenerated in CI (drift = build break); a retrieval-eval signal logs what agents retrieved +
whether the action was correct — feeding both index quality AND the Ask-first→Always evidence.

### E. Open architecture decisions (finalize BEFORE the epic split)

- **D14.** Adopt the grep-native layered context (L0–L4) as the architecture? (rec: yes — confirmed in B)
- **D15.** `doc_kind` (Diátaxis) as a second facet alongside `doc_type`?
- **D16.** Generated index (`llms.txt`-style, per scope) as a CI artifact — in scope?
- **D17.** 3-tier boundaries (Always/Ask-first/Never) as the agent-role + delegation model?
- **D18.** `authority` + `review_by` freshness + the acting-agent "decline on stale" rule?
- **D19.** Agent-maintained frontmatter + retrieval-eval loop — in scope now, or a later phase?
- **D20.** Align agent/repo instruction docs to the AGENTS.md standard (cross-tool portability)?
- **D21.** Structure: promote to an epic (`agentic_docs_and_dispatch_master`) + per-workstream child plans, with the
  current § Phased execution DAG as the dispatch child? (rec: yes)

## Design synthesis — proposed schema, agent operating model, and open A/B choices (2026-06-24)

> **Framing.** This consolidates the research above into a concrete proposed design + the open A/B choices. **These
> decisions are ours.** Some patterns here are **unproven in our context** — treat them as strong candidates, not
> gospel; adopt the design, validate before trusting. **Our earlier ideas (§ External research + target architecture;
> the two audit sections) remain live candidates.** Where two approaches conflict, **BOTH are recorded** in § Open
> choices below — we pick later.

### Proposed schema + operating model

**Frontmatter system** (a human `DOC_FORMAT.md` SSOT + a machine schema module, e.g. a `docspec` in UAC/UTL):

- **Nine design principles:** (1) conventions-over-retrieval-infra (no RAG; grep + lifecycle; RAG = documented
  escape-hatch w/ trigger); (2) per-type closed schemas, not an optional grab-bag; (3) every field always present, empty
  when N/A (deterministic gate); (4) closed vocabs for scope/area/nature/status, `tags` open, scope/area orthogonal; (5)
  `summary` required (highest-leverage); (6) UTC ISO-8601 from the real clock; (7) **lifecycle = the other half**
  (aggressive archive; resolved-issues point at their resolver; mark stale); (8) agent attribution in commit trailers,
  not frontmatter (no `contributed_by`); (9) link fields repo-root-relative.
- **Universal core (9 required):** `title · type · status · scope · nature · summary · created · updated · created_by`.
  **Universal optional (present, may be empty):** `area · version · tags · related`.
- **`type`** (artifact, 10): adr·plan·issue·handoff·reference·architecture·role·standard·audit·audit-result.
- **`nature`** (content-kind facet, orthogonal to `type`, 7): ssot·guideline·process·design·spec·record·notes.
- **Two orthogonal domain axes:** `scope` (pipeline STAGE: data·features·strategy·backtest·paper·live·execution·
  reporting·meta) **+** `area` (package/layer: core·connectors·storage·ui·infra·tenancy·tooling).
- **Per-type status vocabs** (plan: draft/active/implementing/blocked/done/superseded; issue: open/blocked/resolved/
  false-positive; adr: proposed/accepted/superseded/deprecated; …).
- **Three time/version signals:** `created` (immutable) · `updated` (any edit) · `version` (design-revision key — bump
  only on substantive intent/scope change, NOT on progress/status/archive).
- **Conditional fields:** `worked_by` required when `status: implementing` (a plan-level **soft claim/lock** for
  parallel agents); `resolved_by` required when `status: resolved`.
- **Machine SSOT in code** (`docspec.py`: enums + `FieldSpec` R/C/O + `validate_frontmatter()`), `DOC_FORMAT.md` the
  human mirror, kept in lockstep; gate wired LAST ("soak first"). **Exemptions:** README/roadmap/format-specs/ repo-root
  files carry no frontmatter (whitelisted as data).
- **doc↔code link, code stays frontmatter-free:** docs carry `maps_to`/`path`/`verified`; code carries a greppable
  `Implements: docs/...` line + module docstrings; `rg "Implements:.*<slug>"` jumps plan→code.
- **Lifecycle:** done/superseded plans → `archive/`; `status: active|implementing|current` filter = the live set,
  regardless of history depth.
- **Migration recipe (sequencing):** author the SSOT → reconcile the plan format → migrate existing docs **with a
  throwaway ~20-line grep/yaml-lint run after each batch** (catch drift as introduced) → enforce the entry point;
  **machine-schema + gate wiring deliberately LAST.**

**Agent operating model:**

- **Three-layer context:** CLAUDE.md (universal) → **role boot** (a `type: role` doc whose body IS the boot prompt) →
  plan. The **role doc carries only the craft DELTA** (universal rhythm stated once — the concrete anti-bloat fix for
  our 955-line CLAUDE.md). A plan's `roles:` names which to boot. (Our AO already has the role-boot files:
  `agents/*.md`.)
- **Autonomy gradient (maps 1:1 to our orchestrator `conditions`/`blocked`):** Proceed (reversible/in-plan) · Escalate
  non-blocking (record question + recommendation, keep working) · Gate (consequential: irreversible·capital·live·
  outward·cross-cutting).
- **"Boot teaches, the gate enforces":** `type: standard` docs tag rules `[gate]` (machine-checkable; gate fails) vs
  `[convention]` (taught in boot).
- **Fleet substrate:** reference-clone slots (our Path-B model); the orchestrator spine (SQLite hot-state +
  activity-log + backlog + race-safe dispatch + conditions/blocked + claims/liveness); optional per-agent handoff docs
  (a plan→PR replay trail — an addition over our current thin per-slot state).

**Audit system** — directly relevant to our eval-loop + audit docs:

- **4th verification tier** (after gate + tests + plans): periodic, holistic, judged, **non-blocking**.
- **Audits are a staging ground for gates:** when a checkpoint becomes fully mechanical, **promote it to a `scripts/`
  gate and delete it from the audit** ("shed the bottom, grow at the top"); each checkpoint marks a `Gate?` candidate.
- Instruction = durable template (never permanently ticked); result = immutable dated scorecard recording the lib/code
  version + doc-versions-checked; a failed checkpoint raises an issue/plan, never gates a commit.

**L0 routing — two options:** a human-curated "Question → Source of truth" routing table (+ CLAUDE.md routing + grep),
**or** a generated index (the `llms.txt`-style map) — see C2.

### Open choices — A vs B (BOTH kept; decide later)

| #   | Topic                 | Option A                                                                                                | Option B                                                                                                                              | Note                                                                                                                                                   |
| --- | --------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| C1  | empty optional fields | literal `NA` sentinel (D6) — grep-visible                                                               | null scalar / `[]` list; **absence = gate failure**                                                                                   | NA = visible; null/`[]` = YAML-idiomatic + machine-clean                                                                                               |
| C2  | the L0 map            | **generate** an `llms.txt`-style index (D16)                                                            | NO generated index — curated SSOT routing table + CLAUDE.md routing + grep                                                            | generate vs curate; at ~826 codex docs the generated index likely earns its keep                                                                       |
| C3  | purpose facet         | `doc_kind` = Diátaxis (reference/how-to/explanation/tutorial) (D15)                                     | `nature` (ssot/guideline/process/design/spec/record/notes)                                                                            | two different vocabularies for "the second facet"                                                                                                      |
| C4  | domain axes           | `asset_group` + `repos`                                                                                 | a pipeline-`stage` axis + a `module`/package axis                                                                                     | UTS likely needs THREE: `asset_group` + pipeline-stage + `repos` — our pipeline IS data→features→strategy→backtest→execution                           |
| C5  | authority / trust     | explicit `authority` (hard-rule/normative/informational/draft) + `review_by` + "decline on stale" (D18) | derive it from `nature` + `status` (current/stale) + `version`/`verified` + `[gate]`/`[convention]` tags on rules (no separate field) | explicit tier vs derived                                                                                                                               |
| C6  | agent boundaries      | 3-tier Always / Ask-first / Never (D17, ex-AGENTS.md)                                                   | autonomy gradient: Proceed / Escalate-non-blocking / Gate (by reversibility/consequence)                                              | action-type vs consequence framing; the gradient's "escalate non-blocking" keeps the agent working — and it already maps to our `conditions`/`blocked` |
| C7  | dispatch matcher      | `assigned_vm` strict, fleet/multi-VM (D1–D3)                                                            | + a plan-frontmatter `worked_by` soft-claim (grep-visible) and an `executor` (agent/operator/mixed) field                             | not exclusive — `worked_by` complements our per-slot `.agent-claim` for cross-fleet visibility                                                         |
| C8  | code linking          | `code_refs` in doc frontmatter (doc→code)                                                               | bidirectional: doc `maps_to` + code `Implements:` line; **no frontmatter on code** (lean toward this)                                 | do we adopt the "no frontmatter on source" stance?                                                                                                     |

**✅ Decided (2026-06-24) — C-series locked (operator):**

- **C1 → null / `[]`** empty-field convention (grep-ideal: every field always present; `rg '^field: \S'` = has-value;
  machine-clean). `assigned_vm: NA` stays a meaningful VALUE, not the empty convention.
- **C2 → generate the L0 index — CONSUMER-SIDE, LOCAL, gitignored (FINAL 2026-06-24 per operator).** _(Supersedes the
  brief "committed/`uv.lock`" revision: at our doc-change frequency + multi-agent concurrency, a committed fleet-shared
  generated file is a multi-writer contention hotspot — concurrent index-changing commits conflict on the index file.
  Note: the most frequent change, a plan-flip `[ ]`→`[x]`, is a BODY edit so it does NOT change the index; the index
  moves only on frontmatter-identity events — create/rename/delete, `status` flip, re-tag/re-summary — but those still
  happen often + concurrently.)_ A deterministic `scripts/` generator (sorted, no timestamps, **repo-root-relative
  paths** → byte-identical across hosts), output **gitignored**. **Trigger: piggyback on the existing FF-pull cron**
  (`slot-cron-ff-pull.sh`, ~5 min) — after a pull that changed frontmatter, regenerate (stale-checked: only if
  frontmatter actually changed), so the index is fresh within the FF cadence at the exact moment new frontmatter lands;
  **no separate cron, no commit, zero git contention**. **+ on-demand stale-check** before an agent reads (covers the
  inter-tick gap). The committer just commits the doc change; the FF-cron propagates frontmatter; every consumer's local
  index converges (deterministic → identical). **Human visibility/debugging:** a central read-only rendered view served
  by the AO dashboard / deployment-ui (same generator, not a git artifact). NO GitHub Action.
- **C3 → `nature` vocab** (ssot/guideline/process/design/spec/record/notes) as the purpose facet; also feeds C5.
- **C4 → three axes:** `asset_group` (domain) + `stage` (pipeline step) + `repos` (code).
- **C5 → derive authority** from `nature` + `status` + `[gate]`/`[convention]` rule-tags; **no freshness field yet**
  (revisit only if agents act on stale docs).
- **C6 → autonomy gradient** (Proceed / Escalate-non-blocking / Gate) — already live as `conditions` / `/blocked`.
- **C7 → `assigned_vm` only** (status quo); no plan-level `worked_by`/`executor` — in-flight state stays in the backend
  `.agent-claim`.
- **C8 → doc-side `code_refs` is primary** — docs point to source / yaml / json, INCLUDING volatile state (e.g. the
  tradfi/cefi instrument universe) so a doc references the live file instead of embedding data that changes. **Code→doc
  pointers are RARE + optional**, only to cite the _why_ (a `See: docs/…` line for the thesis/rule behind non-obvious
  code); docstrings normally explain WHAT a function does, not the reasoning. **Code stays frontmatter-free.**

**✅ Decided (2026-06-24) — D-series, structure, supersede (operator):** (resolves the "open decisions" D8–D21 above)

- **D8 → yes, open-vocab `tags`** (single-line inline list; tighten to a controlled vocab later if needed).
- **D9 → `asset_group` explicit, auto-seeded** — with the clarification that **the frontmatter core is UNIVERSAL across
  all doc types** (not plan-only), and the three domain axes (`asset_group`, `stage`, `repos`) are **multi-value LISTS**
  (a doc can be `[defi, cefi]`; `cross-cutting`/`infrastructure`/`meta` are valid values). Backfill auto-seeds
  `asset_group` from `parent_epic` where one clear domain exists; multi/cross-cutting set by hand.
- **D10 → `title` only**; the filename is the identifier; drop `name` (retire the 17 strays + the epic duplicates).
- **D11 → `doc_type` on every doc** (the keystone discriminator).
- **D12 → plans folder FIRST** (this effort's first workstream); **codex is its OWN later plan/epic** — and bigger than
  frontmatter: condense the over-verbose docs + fix stale/code-drifted ones, then frontmatter.
- **D13 → agent-role docs = their own workstream plan** under the epic (not folded here).
- **D14 → grep-native layered context (L0–L4) is the architecture.**
- **D15–D18 subsumed:** D15 = `nature` (not Diátaxis; C3) · D16 = generate the index (C2) · D17 = autonomy gradient (C6)
  · D18 = derive authority, no freshness field yet (C5).
- **D19 → retrieval-eval loop IN the epic, sequenced late** (an audit, after schema + index land).
- **D20 → do NOT adopt the AGENTS.md filename standard** (stay CLAUDE.md-centric; the substance is already absorbed).
- **D21 → STRUCTURE (locked): this doc captures the decisions → becomes an EPIC → splits into per-workstream child
  plans.** The epic is **broader than AO** — "how agents work + the automation framework," of which AO is one part —
  **Epic name: `agent_operating_framework_master`** (operator delegated the choice; renamable).
- **Vocab governance (closed facets vs `tags`):** the closed-set facets (`doc_type`/`asset_group`/`stage`/`nature`/
  `status`) are **enums in the validator + enforced**, but **grown organically** — start small, add values as real needs
  surface (NOT frozen day-1). Target **≤~10–15 values per facet**; past ~15 → **consolidate** OR it should have been
  **`tags`** (the open free-list). Closed facets stay small + enforced; high-cardinality/topical overflow → `tags`.
- **Supersede → NOT a supersede.** The prior plans (`orchestrator_v07_multi_vm_topology`,
  `agent_orchestrator_backlog_state_alignment`) stay **separate**; audit them for tasks overlapping AO / agent-behaviour
  / this scope → **migrate those tasks into this epic, or complete them before / in parallel in logical order**; some
  may already be done or not required.

### Validated directions (high-confidence — keep)

grep-native / no-RAG (the research above + the documented escape-hatch: revisit only on an observed trigger, then hybrid
BM25+dense+reranker, never pure vector); `summary` as the highest-leverage field; `doc_type` discriminator +
folders-are-a-human-convenience; the two-facet classification; per-type closed schemas; sweep-then-enforce ("soak"); a
single `DOC_FORMAT` SSOT + a machine validator; lifecycle discipline; the three-layer / role-as-charter model; audits as
the eval / gate-staging loop.

### Sharpened directions + additional patterns

**Much of this already exists in OUR orchestrator.** Our `agent-orchestrator` already implements the key pieces: roles
are `agents/<role>.md` boot prompts opening "STEP 0 — read `RULES.md`" (= the role-boot layer); the **autonomy gradient
is literally our `conditions` (human-only gates) + non-blocking `/blocked`** (a worker posts
`{question, options, recommendation, can_continue}` and keeps working). So this isn't an abstract choice — **our system
already HAS the gradient machinery + the role-boot files**; the work is to schema-ify the `agents/*.md` (the 11
currently with 0 frontmatter) and declare each role's actions in gradient terms.

**Sharpened open choices:**

- **C6 → lean gradient** (already built: `conditions` = gate, `/blocked` = non-blocking escalation).
- **C8 → resolved direction:** code stays **frontmatter-free**; a module docstring (one-line summary) + an opt-in
  `Implements: docs/...` line is the code's greppable index (`rg "Implements:.*<slug>"` = plan→code); doc→code via
  `maps_to`/`code_refs`; an **`Implements:` integrity gate** warns if a module cites a draft/proposed doc.
- **C5 → a concrete alternative:** derive trust from `nature` (ssot/guideline) + `status` (current/stale) +
  `version`/`verified`, and for RULES specifically tag each `[gate]` (machine-enforced) vs `[convention]` (taught),
  rather than a separate `authority` field. So C5 = "explicit `authority` tier" **vs**
  "nature+status+[gate]/[convention]".
- **C7:** a plan-frontmatter `worked_by` soft-claim (grep-visible cross-fleet) would complement our per-slot
  `.agent-claim` — add a plan-level `worked_by` for fleet visibility.

**New patterns worth adopting (additive, not contradictions):**

- **`[gate]` / `[convention]` rule tagging** ("boot teaches, the gate enforces") — tag every CLAUDE.md/codex rule as
  machine-enforceable vs taught; the gate fails on `[gate]`, boot teaches the rest. Directly targets our 955-line
  CLAUDE.md (which mixes HARD RULES with conventions).
- **`Plan-Version` trailer + `version` (design-revision) field** — commits cite `Plan-Version: <plan>@vN`; the timeline
  key tying each chunk of work to the plan revision it targeted (`git log --grep`).
- **Audits-as-gate-staging** — each checkpoint marks a `Gate?` candidate; once a checkpoint becomes fully mechanical it
  **"graduates to the gate"** (becomes a `scripts/` check/test, is removed from the audit, kept only as a history
  pointer); "first run is a gap-find, later runs detect drift." The model for our retrieval-eval loop (D19) + audit
  docs.
- **Per-agent handoff doc** (an addition over our AO's current thin `.agent-claim` + evidence) — a living,
  continuously-committed `type: handoff` (Who · Read-first · State · Next · Gotchas · Decisions-locked) that traces
  plan→PR and lets you debug/replay an agent. Candidate for our observability/eval layer.
- **Agent-driven severity-ranked review → issue doc** — an agent fans out N reviewers → HIGH/MED/LOW findings +
  test-gaps + "what's solid" + a verdict, filed as a `type: issue` with `concerns`. A model for the "agent reviews,
  surfaces findings, human decides" delegation step you described.

**Reminder — design over implementation.** These patterns are strong candidates but **unproven in our context** (a v1 of
such a system ships with the usual concurrency/safety bugs), so we take the **design** and **verify it ourselves**
before trusting it in the fleet — never a copy of anyone's v1 code.

## Phased execution DAG — ⚠️ SUPERSEDED (do not execute)

> Split into the epic's workstreams: Phase 0/1 + supersede → **W1** (`dispatch_strict_vm_matching_2026_06_24`); Phase
> 2/3/4 → **W2/W3/W5** (schema · plans-backfill · QG gate); Phase 5 → W1/W6 docs; Phase 6 → **W6/W7** (role charters ·
> codex). Kept below for traceability only. `assigned_vm: NA` keeps these checkboxes non-dispatchable.

### Phase 0 — Pre-audit (no code change)

- [ ] [SCRIPT] P0. Enumerate every `plans/active/*.md`: current field coverage vs the target matrix, the ~18 plans
      lacking own `assigned_vm`, and the registry-valid VM ids (from
      `scripts/orchestrator/orchestrator_vm_registry.yaml`). Output a coverage table into this plan's Progress Log.
      **Gate**: table present + the delegating-plan list confirmed.

### Phase 1 — Strict matcher (agent-orchestrator) [depends: P0]

- [ ] [CODE] P0. In `server/regen_backlog_from_plan.py`: `_resolve_plan_vms` returns the plan's OWN `assigned_vm` only
      (drop the `parent_epic` resolution branch — D2); matcher fail-closed on unset/`NA` (D1/D3); make strict the
      **only** mode (retire the non-strict default of `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH`). Verify `_prune_stale`
      still shares the gate so reassigned-away plans' queued tasks GC (D4). **Gate**: unit tests — match / mismatch /
      `NA` / unset all fail-closed; reassignment prunes queued + leaves dispatched/done; `quality-gates.sh` green.
- [ ] [INFRA] P0. **Immediate relief for the running `harsh_pc` box**: set strict mode + restart so the 33 mis-ingested
      tasks drop on the next regen (operator-applied on their host; queued-only prune, no data loss). **Gate**:
      `harsh_pc` backlog == only `harsh_pc`-assigned plan tasks.

### Phase 2 — Field matrix [depends: P0; parallel with P1]

- [ ] [DOCS] P1. Define the mandatory-vs-optional frontmatter matrix for **active plans** in `plans/PLAN_FORMAT.md` —
      encode the table from § Frontmatter audit + proposed schema (incl. `assigned_vm` domain = registry ∪ `NA`;
      `NA`-only-on-optionals rule; the new `summary`/`asset_group`/ `repos`/`tags` RAG fields per D8–D10; retire-list).
      Blocked on D8–D10.
- [ ] [DOCS] P1. Update `plans/active/task_template.md` to emit the full field set (mandatory + every optional present
      as `NA`) so new plans are born compliant. **Gate**: a fresh plan from the template passes the Phase-4 gate.

### Phase 3 — Backfill sweep (active plans) [depends: P2]

- [ ] [SCRIPT] P1. Populate `assigned_vm` + all mandatory fields + `NA`-fill optionals across all ~112 active plans, in
      collision-aware batches. The ~18 delegating plans get their epic's VM (or `NA` if future) — list each value for
      operator review before committing. **Gate**: 0 active plans missing any field; spot-check 5 against the matrix.

### Phase 4 — QG gate, enforce-LAST [depends: P3]

- [ ] [SCRIPT] P1. Add `scripts/quality_gates/check_plan_frontmatter_completeness.py` (active plans only;
      `plans/archive/**` + `INDEX.md`/`_agent_pings.md` excluded). Land it **warn-only** first; flip to **error** only
      after Phase 3 lands and propagates to all slots/VMs (D7). **Gate**: gate red on a deliberately-broken plan, green
      on the swept tree.

### Phase 5 — Docs + supersede [depends: P1-P4]

- [ ] [DOCS] P1. Update CLAUDE.md (strict-matching rule + `assigned_vm` ∪ `NA` + mandatory-frontmatter gate) so every
      agent knows. Add partial-supersede banners to the prior plans (see Open-for-operator).
- [ ] [DOCS] P2. Codex SSOT updates: `codex/12-agent-workflow/` (regen/dispatch) + `codex/11-project-management/` (plan
      frontmatter governance).

### Phase 6 — other doc types (audited above; sequenced after the plan-family v1)

- [ ] [DOCS] P2. Apply the universal core + per-type schemas from § Other doc-type frontmatter audit to **codex-ssot**
      (826), **codex-runbook**, **audit-result/instruction**, **agent-role** (11). Sequence by the "three biggest wins":
      `doc_type` everywhere → codex consistency → agent-role charters. Blocked on D11–D13 + the tag-vocabulary content
      pass. May split into its own AO/codex plan if it outgrows this one.
- [ ] [DOCS] P3. **DEFERRED** — controlled tag vocabulary, doc content/intent standardization, archive backfill, cursor
      `.mdc` dedup. Named-successor plan(s) when the frontmatter shape is locked.

## Success criteria

- A backend ingests ONLY plans whose `assigned_vm` equals its id; `NA`/unset → nobody (proven by test).
- Reassignment moves queued tasks cleanly; dispatched/done untouched.
- Every active plan carries the full field set; QG enforces (active only, archive exempt).
- CLAUDE.md + codex reflect the rules; priors carry supersede banners.

## Codex SSOT updates

- `codex/12-agent-workflow/` — regen strict-matching + reassignment/prune model.
- `codex/11-project-management/plan-hygiene.md` (or new) — frontmatter completeness matrix + `NA` rule.

## Progress Log

- 2026-06-24: Plan created. Decisions D1–D7 locked with operator. Claim-marker considered + rejected (cost). Local AO
  stack fully torn down (both backends killed, systemd disabled, tmux/dashboard killed) and task state pruned (root +
  slot-2: tasks/blocked_queue/escalation_queue/conditions → 0, backups kept).
- 2026-06-24: Frontmatter audit run (110 active / 25 epics / 58 issues) + proposed schema written into § Frontmatter
  audit + proposed schema. Open field-set decisions D8–D10 raised.
- 2026-06-24: Extended audit to ALL other doc types (codex 826 / audit results 84 / audit instructions 21 / AO
  agent-role 11 [0 FM] / cursor .mdc 3043 / archive 1065) → § Other doc-type frontmatter audit, with a universal
  `doc_type` core + per-type schemas. Open decisions D11–D13 raised.
- 2026-06-24: Web research (Diátaxis, llms.txt, AGENTS.md / GitHub 2,500-repo study, RAG-metadata papers,
  context-engineering) captured into § External research + target architecture with all source URLs. **Retrieval-method
  DECISION: grep-native, embeddings/vector-RAG REJECTED** (operator-confirmed — major labs use grep for agentic coding;
  "retrieve less but right"). Target architecture drafted: grep-native layered context (L0–L4),
  boundary-tier-as-delegation-dial, trust/freshness substrate, agent-maintained index + eval loop. Architecture
  decisions D14–D21 raised. Epic/workstream split DEFERRED until shapes + decisions are finalized (operator). Still
  local, unpushed.
- 2026-06-24: Consolidated the proposed frontmatter schema + agent-operating-model + the A/B open choices into § Design
  synthesis (strong candidates, not yet locked — unproven in our context, validate before trusting). Earlier ideas KEPT
  as live candidates; conflicts recorded BOTH-ways in § Open choices (C1–C8) for later decision. Still local, unpushed.
- 2026-06-24: Sharpened the open choices — our OWN AO already implements the autonomy gradient (`conditions`+`/blocked`)
  - role-boot (`agents/*.md`), so C6 leans gradient and C8 has a resolved direction (`Implements:` pattern, code
    frontmatter-free). Additive patterns ([gate]/[convention] rule-tagging, Plan-Version trailer,
    audits-as-gate-staging, per-agent handoff docs, agent-driven severity-ranked review) captured in § Sharpened
    directions. Still local, unpushed.
- 2026-06-24: Operator decision pass — walked all open choices one-by-one. **C1–C8 + D8–D21 + structure + supersede now
  LOCKED** (recorded in the two ✅ Decided blocks). Headlines: null/`[]` empty convention · generate the L0 index
  locally · `nature` purpose facet · three multi-value axes (asset_group/stage/repos), universal across ALL doc types ·
  derive authority (no freshness field) · autonomy gradient · `assigned_vm`-only dispatch · doc-side `code_refs` (code
  frontmatter-free) · open `tags` · `title`-only naming · `doc_type` everywhere · plans-first then codex-as-own-plan ·
  layered L0–L4 · eval-loop late · no AGENTS.md. **Structure: this doc → an EPIC (broader than AO: "how agents work +
  the automation framework") → per-workstream child plans.** Still local, unpushed; ready to convert to the epic on go.
- 2026-06-24: **C2 REVISED** (operator) — the L0 index is now **committed (the `uv.lock` pattern)**, not gitignored:
  deterministic + repo-root-relative → byte-identical across hosts; regenerated-on-commit (PM prek hook + quickmerge);
  QG verifies-in-sync (no auto-regen → no FF-cron jam); consumers pull → identical fresh index, no local generation;
  shared/visible/diffable. Generates only when a frontmatter doc changes. **D10 reconfirmed** — no `name` field
  (filename-as-id is faster for identity lookup, rides free in every grep result as the path, and can't drift).
- 2026-06-24: **C2 FINALIZED → consumer-side LOCAL + gitignored** (reverses the committed/`uv.lock` note above).
  Operator: docs change constantly + multi-agent, so a committed fleet-shared index = a multi-writer contention hotspot.
  Final: deterministic local generator (relative paths), **triggered by piggybacking on `slot-cron-ff-pull.sh`** (regen
  after a pull that changed frontmatter, stale-checked) + on-demand stale-check before read; zero git contention;
  central read-only rendered view (AO dashboard / deployment-ui) for human visibility.
- 2026-06-24: Final small items closed — **vocab governance** (closed facets = enforced enums, grown organically, ≤~15
  values each; overflow → `tags`) and the **epic name `agent_operating_framework_master`**. Decision pass COMPLETE
  (C1–C8, D1–D21, structure, supersede, index mechanics, vocab, name all locked). Still local, unpushed; ready to
  convert to the epic + split workstreams on go.
