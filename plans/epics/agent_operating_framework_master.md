---
name: agent_operating_framework_master
title: "Agent Operating Framework Master (L5)"
type: epic
tier: L5
status: active
priority: P0
assigned_vm: harsh_pc
parent: master_to_live_defi_2026_05_23
co_operators: [harsh, ikenna]
created: 2026-06-24
last_updated: 2026-06-24
locked_by: live-defi-rollout
locked_since: 2026-06-24
related_plans:
  - ../active/orchestrator_strict_vm_matching_and_plan_frontmatter_governance_2026_06_24.md # design-capture doc this epic was promoted from (full research + A/B rationale appendix)
  - ../active/orchestrator_v07_multi_vm_topology_2026_05_21.md # prior assigned_vm owner — supersede-audit target (W1)
  - ../active/agent_orchestrator_backlog_state_alignment_2026_05_29.md # prior backlog-regen owner — supersede-audit target (W1)
codex_ssots:
  - codex/11-project-management/plan-hygiene.md # frontmatter completeness matrix + NA rule (to extend)
  - codex/12-agent-workflow/canonical-plan-flow.md # regen/dispatch flow (to extend with strict matching)
---

# Agent Operating Framework Master (L5)

**Owns**: how agents work + the automation framework that runs them — broader than the `agent-orchestrator` (AO) stack
alone (AO is one substrate). Four pillars: (1) **strict per-plan dispatch** (`assigned_vm` is the fail-closed matcher);
(2) a **grep-native documentation/retrieval system** (frontmatter as a structured, greppable index + an L0 map) so
agents find the _right_ doc fast; (3) the **agent operating model** (role charters + autonomy gradient + the
`[gate]`/`[convention]` rule split); (4) the **eval/maintenance loop** (audits-as-gate-staging) that keeps the index
honest and graduates delegation. The whole design is **grep-native, NOT vector-RAG** (operator-confirmed 2026-06-24).

**Assigned VM**: `harsh_pc` (the local fleet-test host where this framework is being designed + driven; reassign
per-workstream as work dispatches — D4).

## Why this epic exists

AO is moving from a work-throughput parallelizer toward an **always-on automation layer**. Planned agent roles:
escalator agents (CI/CD), a plan-reconciler (active-plans / issues / codex / code → done-vs-remaining-vs-correct), and
next — infra-scaling agents, test/staging/prod health monitors, data-pipeline + strategy/execution-VM monitoring, and
log-debugging. With a **2-person dev team (Harsh + Ikenna)** this replaces the specialist desks a large shop staffs.
Those agents can only act correctly if they can **find the right doc fast** and **know what they may / may not do** — so
every doc's frontmatter must be a clean, greppable, intent-bearing index, and every role must carry a machine-readable
charter.

The immediate trigger: the local `harsh_pc` backend ingested **34 tasks** of which only **1** was actually assigned to
it — the other 33 came from ~14 data-pipeline plans owned by other VMs, because matching defaults non-strict and epic→VM
delegation silently resolved to "global". That dispatch bug is W1; the documentation / retrieval / operating-model
build-out is the rest of the epic.

## Governing principle — retrieve less but right (grep-native, no RAG)

For agentic coding/ops the retrieval primitive is **grep/glob/read over the filesystem** — what Claude Code and Codex
actually use — **not** an embeddings/vector store. Grep is exact (no false-neighbour noise), always fresh (no re-index
lag), transparent (the agent sees _why_ a doc matched), and needs zero infra. A vector DB adds staleness + opacity + ops
cost for negative value on a structured corpus we control. **Embeddings/hybrid retrieval is REJECTED** (documented
escape-hatch only: revisit on an observed trigger, then BM25+dense+reranker, never pure vector). "More context is worse"
(Chroma: all 18 models degraded as input grew) → progressive disclosure, lean always-loaded rules (~150–200-instruction
ceiling). The metadata best-practices from the research (authority/recency, self-query pre-filter) are applied to make
**grep** precise — structured facets + a generated index — not to feed a vector store.

> Full external research (Diátaxis · llms.txt · AGENTS.md / GitHub 2,500-repo study · RAG-metadata papers ·
> context-engineering) with source URLs and the A/B rationale is preserved in the design-capture appendix:
> [`../active/orchestrator_strict_vm_matching_and_plan_frontmatter_governance_2026_06_24.md`](../active/orchestrator_strict_vm_matching_and_plan_frontmatter_governance_2026_06_24.md).
> This epic is the distilled, durable SSOT; the appendix is the rationale-of-record.

## Target architecture — grep-native layered context (L0–L4)

Every layer is grep-navigable; each hop loads the minimum. Humans live at L0 and drop to L3/L4 only when needed; agents
traverse L0→L4.

| Layer      | What                                                                                                | Reader                           | Source                                                    |
| ---------- | --------------------------------------------------------------------------------------------------- | -------------------------------- | --------------------------------------------------------- |
| L0 Map     | generated index (`llms.txt`-style) per scope: `title · summary · facets · path`                     | humans monitoring; agents route  | generated FROM frontmatter (consumer-side local artifact) |
| L1 Facets  | frontmatter (`doc_type`/`nature`/`asset_group`/`stage`/`repos`/`status`/`tags`/`authoritative_for`) | agent narrows with one grep      | the doc                                                   |
| L2 Summary | one-line `summary`                                                                                  | agent confirms relevance         | the doc                                                   |
| L3 Body    | full SSOT content                                                                                   | agent, only the confirmed doc(s) | the doc                                                   |
| L4 Direct  | `code_refs` → exact code/workflow paths                                                             | agent jumps doc→code, no search  | frontmatter                                               |

The generated index is the "high-level context" layer and is the SAME investment as the frontmatter (built from it).
**Trust substrate:** authority is _derived_ (from `nature` + `status` + `[gate]`/`[convention]` rule-tags), no separate
freshness field yet — revisit only if agents act on stale docs. **Delegation dial:** role charters declare each action
on the autonomy gradient; graduating an agent = moving an action across the gradient with an audit trail.

## Locked design decisions (operator, 2026-06-24)

The full C1–C8 + D1–D21 rationale + the considered-and-rejected set live in the design-capture appendix. The
load-bearing locks:

**Dispatch (D1–D6):**

- **D1.** Strict, fail-closed matching is the enforced default: a backend ingests a plan **iff**
  `plan.assigned_vm == backend_id`. Unset/`NA` → **nobody**; mismatch → skip.
- **D2.** `assigned_vm` is a mandatory per-plan field; **epic→VM delegation is DROPPED for matching** (`parent_epic`
  stays for orphan-check + priority rollup only — this also makes the `plans/epics`-not-in-snapshot bug moot).
- **D3.** `assigned_vm` valid domain = `{registry VM ids}` ∪ `{NA}`. `NA` is the ONE mandatory field whose valid value
  includes the unassigned sentinel (= future/not-yet-live → dispatched to nobody).
- **D4.** Reassignment = edit `assigned_vm`, push to LDR; old backend prunes its **queued** tasks (shares the match
  gate), new backend ingests on next regen. Task ids are stable → no id-level duplication.
- **D5.** Mid-flight reassignment is operator-managed (small effort-dup window tolerated; the operator has the
  dispatched-count signal). **D6.** Down VM → manual reassignment only (no automated failover, no `fallback_vm`).
- **Rejected:** a per-task claim-marker pushed to LDR at task start (correct in principle, rejected for commit/CI cost;
  a zero-commit dashboard soft-warning is the only acceptable future upgrade).

**Frontmatter / retrieval (C-series + D8–D21):**

- **Universal core on EVERY doc type** (not plan-only): `doc_type` (the keystone discriminator) · `title` (no `name` —
  filename is the id, D10) · `summary` (highest-leverage field) · `status` · `nature` (purpose facet:
  ssot/guideline/process/design/spec/record/notes — C3) · `tags` (open free-list, D8) · `related` · `created`.
- **Three multi-value domain axes** (lists; a doc can be `[defi, cefi]`): `asset_group`
  (cefi/defi/tradfi/sports/prediction/cross-cutting/infrastructure/meta) + `stage` (pipeline step) + `repos` (code) —
  C4/D9. Auto-seed `asset_group` from `parent_epic` where one clear domain exists.
- **Empty-field convention = null / `[]`** (every field always present; `rg '^field: \S'` = has-value; machine-clean).
  `assigned_vm: NA` stays a meaningful VALUE, not the empty convention (C1).
- **Derive authority** from `nature` + `status` + `[gate]`/`[convention]` rule-tags; **no freshness field yet** (C5).
- **L0 index = generated, CONSUMER-SIDE LOCAL, gitignored** (C2, FINAL): deterministic generator (sorted, no timestamps,
  repo-root-relative paths → byte-identical across hosts), output gitignored, **triggered by piggybacking the FF-pull
  cron** (`slot-cron-ff-pull.sh`, regen only when frontmatter changed) + on-demand stale-check before read; zero git
  contention. Human view = central read-only render (AO dashboard / deployment-ui), not a git artifact.
- **`code_refs` is doc-side primary** (docs point to source/yaml/json, including volatile state); code→doc pointers are
  rare + optional (`See:`/`Implements:` line for the _why_); **code stays frontmatter-free** (C8).
- **Autonomy gradient** (Proceed / Escalate-non-blocking / Gate) — already live as AO `conditions` + `/blocked` (C6).
- **Dispatch matcher = `assigned_vm` only** (status quo); no plan-level `worked_by`/`executor` — in-flight state stays
  in the backend `.agent-claim` (C7).
- **Vocab governance:** closed-set facets (`doc_type`/`asset_group`/`stage`/`nature`/`status`) are enums in the
  validator + enforced, but **grown organically** (start small, ≤~10–15 values each; past ~15 → consolidate OR it should
  have been `tags`). High-cardinality/topical overflow → `tags` (the open free-list).
- **Sequencing:** plans-folder FIRST (D12); **codex is its own later plan/epic** and bigger than frontmatter (condense
  over-verbose + fix stale, THEN frontmatter on 826). agent-role docs = their own workstream (D13). retrieval-eval loop
  IN the epic, sequenced late (D19). **Do NOT adopt the AGENTS.md filename standard** — stay CLAUDE.md-centric (D20).
- **Sweep-then-enforce ("soak"):** populate frontmatter everywhere → propagate to all slots/VMs → flip the QG gate to
  enforcing LAST; archive plans excluded from the gate (D7).

## Workstream registry (child plans)

This epic captures the design; the work splits into per-workstream child plans (D21). The current design-capture
appendix's Phased DAG became **W1**.

| WS  | Child plan                                           | Scope                                                                                                               | Serves          | Depends | Priority | Status             |
| --- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | --------------- | ------- | -------- | ------------------ |
| W1  | `dispatch_strict_vm_matching_2026_06_24`             | Strict `assigned_vm==backend` matcher in regen (D1–D6) + immediate `harsh_pc` relief + supersede-audit of priors    | dispatch        | —       | P0       | ✅ created — ready |
| W2  | `doc_frontmatter_schema_and_validator_2026_06_24`    | Universal-core + per-type schema SSOT + machine validator (`docspec`) + closed-vocab enums grown organically        | RAG foundation  | —       | P0       | ✅ created — ready |
| W3  | `plans_frontmatter_backfill_2026_06_24`              | `PLAN_FORMAT` matrix + `task_template` + backfill ~112 active plans (collision-aware batches)                       | RAG             | W2      | P1       | proposed           |
| W4  | `l0_doc_index_generator_2026_06_24`                  | Consumer-side local gitignored deterministic L0 index + FF-cron trigger + AO/deployment-ui rendered view            | RAG (L0)        | W2      | P1       | proposed           |
| W5  | `doc_frontmatter_qg_gate_2026_06_24`                 | `check_plan_frontmatter_completeness.py` warn→error (enforce-LAST, active-only, archive exempt)                     | governance      | W3      | P1       | proposed           |
| W6  | `agent_role_charters_and_operating_model_2026_06_24` | Schema-ify 11 `agents/*.md` (0 FM today) + autonomy-gradient action decls + operating-model arch doc + rule-tagging | operating model | W2      | P1       | proposed           |
| W7  | `codex_condense_and_frontmatter_2026_06_24`          | Condense over-verbose + fix stale/code-drifted codex, THEN frontmatter on 826 (may graduate to its own epic)        | RAG (codex)     | W2      | P2       | deferred           |
| W8  | `retrieval_eval_loop_2026_06_24`                     | Audits-as-gate-staging retrieval-eval loop (an audit; logs what agents retrieved + whether the action was correct)  | eval            | W2, W4  | P2       | deferred (late)    |

**Critical path:** W1 ships independently NOW (dispatch fix). W2 is the foundation for W3/W4/W5/W6/W7/W8. W3→W5
(backfill before the enforcing gate). W7/W8 are deferred (codex is its own effort; eval is sequenced late).

## Composition with other epics

- **`orchestrator_master`** — owns the AO multi-VM stack this framework dispatches on (registry, per-VM backend,
  AutoSpawn, safety). W1 lands in `agent-orchestrator`'s `regen_backlog_from_plan.py`; the role charters (W6) schema-ify
  its `agents/*.md`. This epic is the _operating model_; `orchestrator_master` is the _runtime_.
- **`plan_hygiene_master`** — owns plan frontmatter/line-cap/archive hygiene; W3/W5 extend its `plan-hygiene.md` SSOT +
  its QG sweep with the completeness matrix.
- **`observability_master`** — the L0 rendered view + the eval-loop signal (W4/W8) compose with the dashboard/alerting
  surface.

## Out of scope

- Embeddings / vector-RAG (rejected — escape-hatch only).
- The AGENTS.md filename standard (substance absorbed; stay CLAUDE.md-centric — D20).
- A separate `authority`/freshness frontmatter field (derived for now — C5).
- A plan-level `worked_by`/`executor` claim field (in-flight state stays in the backend `.agent-claim` — C7).
- Cursor `.mdc` dedup + archive backfill + the controlled tag-vocabulary content pass (later passes — D-deferred).

## P0 — must complete first

### W1 — Strict per-plan VM matching (dispatch correctness)

Owned by [`../active/dispatch_strict_vm_matching_2026_06_24.md`](../active/dispatch_strict_vm_matching_2026_06_24.md).
The fail-closed `assigned_vm==backend` matcher (D1–D6) + immediate `harsh_pc` relief + the supersede-audit of the two
prior owners. Ships independently of the rest of the epic.

- [ ] [CODE] P0. `_resolve_plan_vms` returns the plan's OWN `assigned_vm` only (drop `parent_epic` branch); strict is
      the only mode; `_prune_stale` shares the gate. (W1)
- [ ] [INFRA] P0. Immediate `harsh_pc` relief — strict mode + restart → the 33 mis-ingested tasks drop. (W1)
- [ ] [DOCS] P0. Supersede-audit `orchestrator_v07_multi_vm_topology` + `agent_orchestrator_backlog_state_alignment`:
      migrate overlapping tasks here or complete them; mark done/not-required. (W1)

### W2 — Doc frontmatter schema + machine validator (RAG foundation)

Owned by
[`../active/doc_frontmatter_schema_and_validator_2026_06_24.md`](../active/doc_frontmatter_schema_and_validator_2026_06_24.md).
The universal-core + per-type schema SSOT + a `docspec` validator with closed-vocab enums (grown organically).
Everything else (W3–W8) depends on this shape.

- [ ] [DOCS] P0. `DOC_FORMAT`-equivalent SSOT: universal core + per-type extensions + the `NA`/null conventions. (W2)
- [ ] [CODE] P0. Machine validator (`docspec`: enums + `FieldSpec` R/C/O + `validate_frontmatter()`), gate-wired LAST.
      (W2)

## P1 — after the P0 foundation

- [ ] [DOCS] P1. **W3** — plans-folder backfill (matrix in `PLAN_FORMAT.md` + `task_template` + sweep ~112 active
      plans).
- [ ] [SCRIPT] P1. **W4** — L0 index generator (consumer-side local, gitignored, FF-cron-triggered) + AO rendered view.
- [ ] [SCRIPT] P1. **W5** — `check_plan_frontmatter_completeness.py` warn→error (enforce-LAST; active-only).
- [ ] [DOCS] P1. **W6** — agent-role charters (schema-ify the 11 `agents/*.md`) + operating-model arch doc +
      `[gate]`/`[convention]` rule-tagging.

## P2 — deferred (own efforts / sequenced late)

- [ ] [DOCS] P2. **W7** — codex condense + fix-stale, THEN frontmatter on 826 docs (may graduate to its own epic —
      bigger than frontmatter).
- [ ] [DOCS] P2. **W8** — retrieval-eval loop (audits-as-gate-staging; logs retrieval + action-correctness; feeds index
      quality + the delegation-graduation evidence).
- [ ] [DOCS] P3. **DEFERRED** — controlled tag vocabulary · doc content/intent standardization · archive backfill ·
      cursor `.mdc` dedup. Named-successor plan(s) when the frontmatter shape is locked.

## Progress Log

- 2026-06-24: Epic created from the design-capture appendix
  (`orchestrator_strict_vm_matching_and_plan_frontmatter_governance_2026_06_24.md`) after the full operator decision
  pass (C1–C8, D1–D21, structure, supersede, index mechanics, vocab, name all LOCKED). Workstream registry W1–W8
  enumerated. W1 + W2 child plans created (the two ready P0s). W3–W8 proposed for materialization pending operator
  review of the set.
