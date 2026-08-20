---
doc_type: epic
title: Agent Operating Framework Master (L5)
summary:
  L5 epic owning how agents work — strict per-plan dispatch (assigned_vm fail-closed matcher, epic→VM delegation
  DROPPED), grep-native (NOT vector-RAG) frontmatter/L0-index retrieval, role charters + autonomy gradient, and the
  retrieval-eval loop; workstreams W1–W10 (dispatch fix, docspec, backfill, L0 gen, QG gate, role registry+broker).
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, deployment-ui]
scope: [engineer, admin]
tags: [orchestrator, role-registry, frontmatter, rag, plan-hygiene, docspec, escalation, quality-gates]
related:
  [
    ../archive/orchestrator_strict_vm_matching_and_plan_frontmatter_governance_2026_06_24.md,
    ../archive/2026_06/agent_orchestrator_backlog_state_alignment_2026_05_29.md,
  ]
created: 2026-06-24
name: agent_operating_framework_master
tier: L5
priority: P0
assigned_vm: NA # corrected 2026-08-02 (operator ruling on plan_reconcile_parked_operator_decisions_2026_08_02.md § 2e, option A): this epic's own D2 drops epic->VM delegation for dispatch matching, and PLAN_FORMAT.md cites this epic as the SSOT for "NA is the expected value on every current epic" -- assigned_vm: planning here contradicted both. (was: planning, before that harsh_pc -- see git history for the 2026-07-14 finding-12 correction this superseded)
parent: master_to_live_defi_2026_05_23
co_operators: [harsh, ikenna]
codex_ssots: [/codex/11-project-management/plan-hygiene.md, /codex/12-agent-workflow/canonical-plan-flow.md]
related_plans:
  - ../active/ag_closeout_audit_rollout_2026_07_25.md
  - ../active/ao_consolidated_closeout_2026_08_12.md
  - ../active/ao_death_diagnostics_compaction_kpis_and_sequential_carveout_2026_08_15.md
  - ../active/ao_dispatch_plans_operator_item_separation_sweep_2026_08_16.md
  - ../active/ao_satellite_ao_dispatch_batch25_2026_08_19.md
  - ../active/ao_satellite_ao_dispatch_batch25_finalize_2026_08_19.md
  - ../active/asset_class_to_asset_group_rename_2026_07_21.md
  - /codex/11-project-management/doc-frontmatter-schema.md
  - ../active/cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md
  - ../active/cross_cutting_satellite_ao_dispatch_batch16_2026_08_17_finalize.md
  - ../active/data_pipeline_e2e_milestones_gate_2026_07_24.md
  - ../active/doc_body_link_checker_blind_to_backtick_citations_2026_08_02_finalize_2026_08_08.md
  - ../active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md
  - ../active/meta_plan_corpus_hygiene_ao_dispatch_batch1_finalize_2026_08_10.md
  - ../active/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01_finalize_2026_08_08.md
  - ../active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md
  - ../active/one_shot_complete_session_ownership_desync_2026_08_08_finalize_2026_08_08.md
  - ../active/task_template.md
last_updated: 2026-08-20
locked_by: live-defi-rollout
locked_since: 2026-06-24
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Agent Operating Framework Master (L5)

## Report

Live HTML ledger: https://claude.ai/code/artifact/08c154ae-be37-458d-9044-85de539d3ab2 (generated 2026-08-19,
`/plan-reconcile agent_operating_framework_master`)

**Owns**: how agents work + the automation framework that runs them — broader than the `agent-orchestrator` (AO) stack
alone (AO is one substrate). Four pillars: (1) **strict per-plan dispatch** (`assigned_vm` is the fail-closed matcher);
(2) a **grep-native documentation/retrieval system** (frontmatter as a structured, greppable index + an L0 map) so
agents find the _right_ doc fast; (3) the **agent operating model** (role charters + autonomy gradient + the
`[gate]`/`[convention]` rule split); (4) the **eval/maintenance loop** (audits-as-gate-staging) that keeps the index
honest and graduates delegation. The whole design is **grep-native, NOT vector-RAG** (operator-confirmed 2026-06-24).

> **🟢 Foundational reframe + minimum-usable re-scope (operator, 2026-06-26).** The _method_ this machinery serves is
> now an SSOT: [`/codex/12-agent-workflow/work-philosophy.md`](/codex/12-agent-workflow/work-philosophy.md) —
> codex-as-target, bidirectional drift, **plan-as-unit sized to one agent**, **role-per-plan** (`assigned_role`),
> durable craft-role boot prompts, judgment-at-authoring. **The priority is finishing AO so we can USE it for
> throughput**, so this epic is re-scoped to the must-haves and the rest is deferred to next quarter:
>
> - **KEEP (must-have, now):** **W6** role charters → realized as **durable craft-role boot prompts** (backend-engineer,
>   data_engineering, ui-developer, quant-dev, infra + main/review; craft not domain, domain comes per-plan via
>   frontmatter). **W2–W5** frontmatter (active-plans-first; cheap mechanical now, expensive organic; enforce gate
>   last). Plus the AO dispatch change to read `assigned_role` → boot prompt + model (no broker), and the plan-format
>   change (`assigned_role`, `drift_direction`, sizing rule, per-task `Gate:` — landed in `PLAN_FORMAT.md` +
>   `epics/README.md`).
> - **DEFER to next quarter:** **W7** (codex condense/frontmatter), **W8** (retrieval-eval loop), **W9** (message broker
>   / `(role,domain)` routing / `POST /api/messages`), **W10** (criticality registry), and the role/escalation _pilots_
>   (`role_registry_schema_and_broker_mvp`, `pm_role_charter_formalization`, `data_eng_role_vertical_pilot`,
>   `escalation_pipeline_mvp` + the `escalation_and_disaster_recovery_master` epic). They stay valid; they are not on
>   the make-AO-usable critical path. Pausing those 4 child plans is the remaining O1 mechanic (operator to confirm).

**Assigned VM**: `NA` (corrected 2026-08-02, operator ruling on `plan_reconcile_parked_operator_decisions_2026_08_02.md`
§ 2e — this epic's own D2 below drops epic→VM delegation for dispatch matching, so an epic-level `assigned_vm` is not a
live reassignment lever; PLAN_FORMAT.md cites this epic as its SSOT for "`NA` is the expected value on every current
epic". Individual child plans carry their own `assigned_vm` per D1-D4 below.)

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
> [`../archive/orchestrator_strict_vm_matching_and_plan_frontmatter_governance_2026_06_24.md`](../archive/orchestrator_strict_vm_matching_and_plan_frontmatter_governance_2026_06_24.md).
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
- **L4 `code_refs` granularity + enforcement (operator decision 2026-07-04 — captured, DEFERRED / aspirational):**
  - **Granularity = MODULE/PACKAGE DIRECTORY by default, not exact files.** Content-pass rot data (55-lane sweep
    2026-07-03/04) showed file-level citations rot on nearly every refactor (rename/split: `vol_carry_engine.py` →
    `carry.py`, `routes/data_status.py` → split) while their module dirs survive almost all of them (only full service
    consolidations kill a dir); repo-level is already covered by the `repos:` facet. Module-level keeps ~95% of the
    navigation value (25 repos → 1 repo → one 5–20-file dir + one `rg`) at ~10% of the rot rate. Exact file paths
    allowed ONLY for stable single-file entry points (e.g. `scripts/quickmerge.sh`, a QG checker) that demonstrably
    don't move.
  - **Enforcement = scheduled host-side existence audit (hygiene-sweep rider), warn + worklist — NEVER a blocking commit
    gate.** Structural reason: codex lives in PM, code lives in service repos — a rename in a service repo cannot
    atomically update PM codex docs, so a blocking gate would go red asynchronously on whoever touches PM next (rule-11
    blast-radius class), ambushing a mid-refactor agent with breakage it didn't cause. Also technically forced: server
    `quality-gates-v2` checks out ONE repo, so cross-repo path resolution is host-side-only. Optional courtesy:
    WARN-only note in code repos' local pre-push ("you moved paths referenced by codex `code_refs`: <list>"),
    skip-if-PM-absent.
  - **Backfill = a W7 rider, not a standalone pass**: when the W7 de-drift pass repairs a doc's body citations, it
    writes the verified survivors into `code_refs` at module granularity (near-free at that moment; current coverage
    25/805 codex docs). Existence checks catch structural rot only; semantic drift stays W8/eval-loop territory.
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

| WS  | Child plan                                           | Scope                                                                                                                | Serves          | Depends | Priority | Status                                                                                                                                                                |
| --- | ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- | --------------- | ------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| W1  | `dispatch_strict_vm_matching_2026_06_24`             | Strict `assigned_vm==backend` matcher in regen (D1–D6) + immediate `harsh_pc` relief + supersede-audit of priors     | dispatch        | —       | P3       | N/A — superseded (child plan archived `status: superseded`; whole premise dropped by the 2026-06-27 single-VM pivot; corrected 2026-08-06, was: "✅ created — ready") |
| W2  | `doc_frontmatter_schema_and_validator_2026_06_24`    | Universal-core + per-type schema SSOT + machine validator (`docspec`) + closed-vocab enums grown organically         | RAG foundation  | —       | P0       | ✅ **shipped**                                                                                                                                                        |
| W3  | `plans_frontmatter_backfill_2026_06_24`              | `PLAN_FORMAT` matrix + `task_template` + backfill ~112 active plans (collision-aware batches)                        | RAG             | W2      | P1       | ✅ **shipped**                                                                                                                                                        |
| W4  | `l0_doc_index_generator_2026_06_24`                  | Consumer-side local gitignored deterministic L0 index + FF-cron trigger + AO/deployment-ui rendered view             | RAG (L0)        | W2      | P1       | ✅ **shipped**¹                                                                                                                                                       |
| W5  | `doc_frontmatter_qg_gate_2026_06_24`                 | `check_plan_frontmatter_completeness.py` warn→error (enforce-LAST, active-only, archive exempt)                      | governance      | W3      | P1       | ✅ **shipped**²                                                                                                                                                       |
| W6  | `agent_role_charters_and_operating_model_2026_06_24` | Schema-ify 11 `agents/*.md` (0 FM today) + autonomy-gradient action decls + operating-model arch doc + rule-tagging  | operating model | W2      | P1       | ✅ **shipped**³                                                                                                                                                       |
| W7  | `codex_condense_and_frontmatter_2026_06_24`          | Condense over-verbose + fix stale/code-drifted codex (+ L4 module-level `code_refs` rider — see 2026-07-04 decision) | RAG (codex)     | W2      | P2       | **aspirational**                                                                                                                                                      |
| W8  | `retrieval_eval_loop_2026_06_24`                     | Audits-as-gate-staging retrieval-eval loop (an audit; logs what agents retrieved + whether the action was correct)   | eval            | W2, W4  | P2       | deferred (late)                                                                                                                                                       |

¹ W4 rendered view (AO/deployment-ui) remains open — P2 in `l0_doc_index_generator_2026_06_24`. ² W5 landed as the
stronger consolidated blocking gate (pm@d47886909), not the named warn→error flip. ³ W6 rule-tagging portion unverified
— rides W7 if absent. Evidence for all flips: the W-todo checkboxes below.

**Critical path:** W1 ships independently NOW (dispatch fix). W2 is the foundation for W3/W4/W5/W6/W7/W8. W3→W5
(backfill before the enforcing gate). W7/W8 are deferred (codex is its own effort; eval is sequenced late).

## Role-based agent expansion (2026-06-25)

Operator design pass — the framework generalizes from "PM-only dispatch" to a **role-based agent registry**. Key
reframe: this is **not greenfield** — the 11 `agents/*.md` are un-schematized registry rows, dispatch already derives
model/thinking per task, and `by-role/message` is a proto-broker. The expansion is **three generalizations + one
merge**:

1. **Charters → machine-readable rows** (realizes W6) — `agent-role` frontmatter (model/thinking/`lifecycle`/triggers/
   `does`/`does_not`/`escalation_to`/`temperament_base`), `docspec`-validated, grep-native (no vector store).
2. **Dispatch key `assigned_vm` (where) → `(role, domain)` (who+what)** — additive resolver beside strict `assigned_vm`;
   plan-ingestion UNCHANGED. This is what makes "any role, any situation" a lookup.
3. **`by-role/message` → a tagged ingest→queue→route broker (W9)** — a new `POST /api/messages` path on the existing AO
   FastAPI (**no new DNS**); dumb router (machine senders self-tag; one human-boundary tagger, no smart routing agent).
4. **Merge** — the two UIs (AO dashboard + deployment-ui) unify later; **defer-unify, deep-link now** (operator
   decision, 2026-06-25).

**Roles are child plans (instances), not epics.** Each role = charter + skills (on-demand verbs, light-JSON out) +
workflows (heavy fan-out, Opus only at synth) + triggers + a UI tab. `lifecycle` decides standing-holder (query roles:
DevOps/Data-Eng "is it healthy?") vs cold one-shot (fix-it roles: CI-escalate/DP-fix).

| WS / plan                                               | Kind                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Depends | Priority | Status      |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | -------- | ----------- |
| **W9** `role_registry_schema_and_broker_mvp_2026_06_25` | registry+broker spine — W6 registry schema DELIVERED + live; W9 message broker NOT REQUIRED (superseded by `assigned_role` dispatch); plan ARCHIVED 2026-07-16                                                                                                                                                                                                                                                                                              | W2      | P0       | 🗄️ archived |
| **W10** `agent_role_criticality_registry` (future)      | diligence dial `temperament × criticality(ag,env,path)` — BizDev+PM                                                                                                                                                                                                                                                                                                                                                                                         | W9      | P2       | proposed    |
| role `pm_role_charter_formalization_2026_06_25`         | W6 instance — PM charter DELIVERED + live (main.md); ARCHIVED 2026-07-16                                                                                                                                                                                                                                                                                                                                                                                    | W9      | P1       | 🗄️ archived |
| role `data_eng_role_vertical_pilot_2026_06_25`          | W6 instance — Data-Eng charter DELIVERED + live; ARCHIVED 2026-07-16 (Phase-0 triage bug carved out) (first full vertical; dispatched via `assigned_role: data-pipeline-engineer` (was: **dispatched harsh_pc** — corrected 2026-07-12, finding id 7, §A2 B-queue ruling; `harsh_pc` was a pre-2026-06-27 multi-VM host id, retired by the single-VM pivot; plan frontmatter `assigned_vm: NA` is current per its own 2026-07-12 historical-dispatch-note)) | W9      | P1       | 🗄️ archived |

**Escalation is its own epic** — [`escalation_and_disaster_recovery_master`](escalation_and_disaster_recovery_master.md)
owns the role-agnostic blocked→Slack→resolve→UI pipeline + the self-healing/auto-recovery substrate; composes with
`observability_master`. **Corrected 2026-07-23**: E1's child plan `escalation_pipeline_mvp_2026_06_25` was ARCHIVED
(operator) and its 5 UNBUILT todos absorbed into the epic itself, which is now E1's single tracking home; **and the
broker (W9) is NO LONGER a hard dependency** — `role_registry_schema_and_broker_mvp` was archived NOT-REQUIRED
2026-07-16 (superseded by `assigned_role` dispatch), and the reply path already exists via
`POST /api/blocked/{id}/answer`. (was: "E1 `escalation_pipeline_mvp_2026_06_25`, human-driven" + "The broker (W9) is its
hard dependency".)

**Fast-follow roles** (after the spine + Data-Eng pilot prove the pattern): DevOps, QA (UI-Playwright vs backend
chaos/load split), Business-Dev (owns the criticality registry), Trading-Analysis, CTO. Quant-research stays P2 (least
existing scaffolding). Starter set chosen by the operator (2026-06-25): **spine + PM + Data-Eng + Escalation-MVP** (4).
(was: QA/UAT framed purely as a not-yet-started fast-follow — **corrected 2026-07-14, finding 9**: QA/UAT's Phase 0
charter (`../archive/2026_07/uat_role_charter_2026_06_27.md`, W6 role instance; plan ARCHIVED 2026-07-16) already
shipped `agent-orchestrator@acbf930` — the SAME commit that shipped the spine's own Phase 1 — so QA/UAT work began
concurrently with, not strictly after, the spine + Data-Eng pilot; this section was never revised to reflect that.
`uat_role_charter_2026_06_27.md` is also missing from this epic's `related_plans` frontmatter.)

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

## AO issue register → see `orchestrator_master`

The 2026-07-16 AO issue-doc reconciliation sweep enumerates **every** AO issue doc (both epics, plus archived docs that
still carry open todos) in ONE register, deliberately not split across the two epics:
[`orchestrator_master.md` § AO issue register](orchestrator_master.md#ao-issue-register--2026-07-16-reconciliation-sweep).
Five docs under **this** epic appear there (`ao_skip_blind_spawn_budget_phantom_churn_2026_07_15`,
`ao_recovery_audit_layer1_deleted_2026_07_15`, `ao_docs_reconciliation_2026_07_15`,
`empty_output_category_count_ssot_contradiction_2026_07_03`, `ao_autospawn_role_blind_dispatch_starvation_2026_07_14` —
the last archived-yet-still-carrying-open-todos), alongside the four PM-QG hygiene docs that sit under this epic by
`parent_epic` but are not AO-runtime concerns. **Do not fork a second register here** — one list, one place, or the
enumeration rots again (which is the exact failure the sweep exists to fix).

## P0 — must complete first

### W1 — Strict per-plan VM matching (dispatch correctness)

> **Stale-ownership + moot-premise notice (corrected 2026-07-14, finding 203):** the linked owner below
> (`dispatch_strict_vm_matching_2026_06_24.md`) is `status: superseded` (archived at
> `archive/2026_06/dispatch_strict_vm_matching_2026_06_24.md`), its open items folded into
> `orchestrator_consolidated_remaining_2026_06_25.md`, which is now ALSO archived (`status: superseded`) with items
> folded onward again. `epics/orchestrator_master.md` separately (and independently) claims this same D1–D6 scope via
> that same now-archived plan. Neither owner needs reviving: the whole premise — matching a plan's `assigned_vm` to a
> specific backend VM id in a multi-VM fleet — was itself superseded by the 2026-06-27 single-VM pivot (dispatch is now
> role/skill-based via `assigned_role`, not per-VM `assigned_vm==backend` matching; see this epic's own 2026-06-26
> reframe note above). The three `- [ ]` P0 todos below are stale/not-applicable under the current architecture, not
> live blocking work.

Owned by [`../active/dispatch_strict_vm_matching_2026_06_24.md`](../active/dispatch_strict_vm_matching_2026_06_24.md).
The fail-closed `assigned_vm==backend` matcher (D1–D6) + immediate `harsh_pc` relief + the supersede-audit of the two
prior owners. Ships independently of the rest of the epic.

- [ ] [CODE] P3. **N/A — SUPERSEDED by the 2026-06-27 single-VM pivot** (child plan archived `status: superseded`;
      retagged 2026-08-06 by /plan-reconcile ao): `_resolve_plan_vms` returns the plan's OWN `assigned_vm` only (drop
      `parent_epic` branch); strict is the only mode; `_prune_stale` shares the gate. (W1)
- [ ] [INFRA] P3. **N/A — SUPERSEDED by the 2026-06-27 single-VM pivot** (child plan archived `status: superseded`;
      retagged 2026-08-06 by /plan-reconcile ao): Immediate `harsh_pc` relief — strict mode + restart → the 33
      mis-ingested tasks drop. `harsh_pc` is itself a retired pre-2026-06-27 host id. (W1)
- [ ] [DOCS] P3. **N/A — SUPERSEDED by the 2026-06-27 single-VM pivot** (child plan archived `status: superseded`;
      retagged 2026-08-06 by /plan-reconcile ao): Supersede-audit `orchestrator_v07_multi_vm_topology` +
      `agent_orchestrator_backlog_state_alignment`: migrate overlapping tasks here or complete them; mark
      done/not-required. (W1)

### W2 — Doc frontmatter schema + machine validator (RAG foundation)

Owned by
[`../active/doc_frontmatter_schema_and_validator_2026_06_24.md`](../active/doc_frontmatter_schema_and_validator_2026_06_24.md).
The universal-core + per-type schema SSOT + a `docspec` validator with closed-vocab enums (grown organically).
Everything else (W3–W8) depends on this shape.

- [x] [DOCS] P0. `DOC_FORMAT`-equivalent SSOT: universal core + per-type extensions + the `NA`/null conventions. (W2) —
      ✅ `/codex/11-project-management/doc-frontmatter-schema.md` (banner: CURRENT — fully enforced, BLOCKING
      2026-07-04).
- [x] [CODE] P0. Machine validator (`docspec`: enums + `FieldSpec` R/C/O + `validate_frontmatter()`), gate-wired LAST.
      (W2) — ✅ `scripts/docs/docspec.py`; gate-wired 2026-07-04 (pm@d47886909: `check_frontmatter_schema.py` calls
      `docspec.validate_frontmatter()`, BLOCKING HARD+SOFT; warn-only coverage check retired).

## P1 — after the P0 foundation

- [x] [DOCS] P1. **W3** — plans-folder backfill (matrix in `PLAN_FORMAT.md` + `task_template` + sweep ~112 active
      plans). — ✅ delivered via `frontmatter_full_corpus_coverage_2026_06_30` (archived complete) + the content pass
      (`frontmatter_content_pass_and_gate_consolidation_2026_06_30`): corpus docspec HARD=0 SOFT=0 on 1,298 live docs
      (2026-07-04).
- [x] [SCRIPT] P1. **W4** — L0 index generator (consumer-side local, gitignored, FF-cron-triggered) + AO rendered view.
      — ✅ generator `scripts/docs/gen_doc_index.py` (1,119 docs, ~1.4s, `--stale-check`) + FF-cron regen across EVERY
      PM clone incl. dirty trees (pm@b4d75366d, 2026-07-04). REMAINDER: the AO/deployment-ui rendered view stays open as
      P2 in `l0_doc_index_generator_2026_06_24` (human view, not on the agent path).
- [x] [SCRIPT] P1. **W5** — `check_plan_frontmatter_completeness.py` warn→error (enforce-LAST; active-only). — ✅
      superseded by a STRONGER end-state 2026-07-04 (pm@d47886909): ONE comprehensive blocking gate
      (`check_frontmatter_schema.py` backed by docspec, HARD+SOFT, live trees incl. codex + `*.mdc`; archives exempt).
- [x] [DOCS] P1. **W6** — agent-role charters (schema-ify the 11 `agents/*.md`) + operating-model arch doc +
      `[gate]`/`[convention]` rule-tagging. — ✅ charters: 14 `agents/*.md` carry full agent-role frontmatter, gated
      in-repo (agent-orchestrator@202c9b6, `check_agent_role_frontmatter.py` blocking, 14/14 green); operating model:
      `/codex/12-agent-workflow/work-philosophy.md` + role registry. Rule-tagging `[gate]`/`[convention]` not
      independently verified — if absent it rides W7 (aspirational).

## P2 — deferred (own efforts / sequenced late)

- [ ] [DOCS] P2. **W7** — codex condense + fix-stale, THEN frontmatter on 826 docs (may graduate to its own epic —
      bigger than frontmatter). **ASPIRATIONAL (operator, 2026-07-04)** — not scheduled; frontmatter half already
      delivered by `frontmatter_content_pass_and_gate_consolidation_2026_06_30` (corpus docspec 0/0 + blocking gate);
      remaining scope = condense/de-drift + the L4 module-level `code_refs` rider (see the 2026-07-04 locked decision
      above; fill at module granularity while repairing body citations, existence-audit host-side, never a blocking
      gate). Inputs ready when picked up: the content-pass anomaly log (stale docs, dead citations, SUPERSEDED-banner
      list, retype list) in that plan's Progress Log + P3.4 worklist.
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
- 2026-06-24: **W2 DONE + W3 cheap-pass sample SHIPPED.** `docspec` validator (`scripts/docs/docspec.py`, 15 tests) +
  `seed_frontmatter.py` built; the **5-per-doc_type mechanical sample applied in place to 35 PM docs** (all `docspec`
  hard=0) — new child plan `doc_frontmatter_mechanical_seed_and_sample_2026_06_24` (supersedes the proposed W3
  `plans_frontmatter_backfill` framing: broader = all doc types, mechanical-only). Operator-scoped DEFERRALS (todos in
  that plan): full rollout · `summary`/`tags` content · status normalization · **agent-role (W6) + cursor-rule**
  (cross-repo) · validator-green · **QG gate (W5)**. Schema refined: exemptions (ledgers/index) · `scope` vs
  `audited_scope` · status-soft-during-soak · issue `active`→`open`.
- 2026-06-25: **Role-based agent expansion scoped (operator design pass).** Reframed the framework as a role-based
  registry: charters→rows, dispatch key `assigned_vm`→`(role,domain)`, `by-role/message`→broker (W9), UIs merge later
  (defer-unify/deep-link). Added W9 (`role_registry_schema_and_broker_mvp`) + W10 (criticality registry, proposed) + two
  W6 role instances (`pm_role_charter_formalization`, `data_eng_role_vertical_pilot` — the latter dispatched to
  `harsh_pc`). Split out a new epic `escalation_and_disaster_recovery_master` (E1 `escalation_pipeline_mvp`). Starter
  set (4): spine + PM + Data-Eng + Escalation-MVP; all human-driven except the dispatched Data-Eng pilot. Quick win
  flagged: `alerting-service/.../claude_slack_agent.py` computes the AI triage then discards it (`_ = triage_text`).

## Assigned active plans

_18 active plans declare `parent_epic: agent_operating_framework_master` in their frontmatter. Workers pick up in priority order (P0 first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

_(no plans currently assigned at this priority)_

## P1 — important; post-current-gate

### [`ag_closeout_audit_rollout_2026_07_25`](../active/ag_closeout_audit_rollout_2026_07_25.md)
**status**: active · **estimate**: 4.8 cal AI-days (class: research)
**title**: AG closeout-audit rollout — cefi/defi/tradfi/prediction (sports treatment, generalized)

### [`ao_death_diagnostics_compaction_kpis_and_sequential_carveout_2026_08_15`](../active/ao_death_diagnostics_compaction_kpis_and_sequential_carveout_2026_08_15.md)
**status**: active · **estimate**: 1.6 cal AI-days (class: infra)
**title**: AO Death Diagnostics Consolidation, Compaction KPIs, and Sequential-Task Carve-out

### [`data_pipeline_e2e_milestones_gate_2026_07_24`](../active/data_pipeline_e2e_milestones_gate_2026_07_24.md)
**status**: active · **estimate**: 9.6 cal AI-days (class: research)
**title**: Data-pipeline E2E milestones gate — 14 cross-AG correctness criteria for the 5 asset-group consolidated closeouts

### [`one_shot_complete_session_ownership_desync_2026_08_08_finalize_2026_08_08`](../active/one_shot_complete_session_ownership_desync_2026_08_08_finalize_2026_08_08.md)
**status**: active · **estimate**: 0.24 cal AI-days (class: infra)
**title**: one_shot_complete session-ownership desync — finalize

## P2 — useful; opportunistic

### [`ao_consolidated_closeout_2026_08_12`](../active/ao_consolidated_closeout_2026_08_12.md)
**status**: active · **estimate**: 1.6 cal AI-days (class: infra)

### [`ao_dispatch_plans_operator_item_separation_sweep_2026_08_16`](../active/ao_dispatch_plans_operator_item_separation_sweep_2026_08_16.md)
**status**: active · **estimate**: 3.2 cal AI-days (class: infra)
**title**: AO-dispatch plan corpus sweep — separate operator-gated items from worker-dispatchable todos

### [`ao_satellite_ao_dispatch_batch25_2026_08_19`](../active/ao_satellite_ao_dispatch_batch25_2026_08_19.md)
**status**: active · **estimate**: 0.45 cal AI-days (class: refactor)
**title**: AO satellite AO batch 25 — conflict-clear bounded extraction from the 2026-08-19 na-eligibility-audit ao run

### [`ao_satellite_ao_dispatch_batch25_finalize_2026_08_19`](../active/ao_satellite_ao_dispatch_batch25_finalize_2026_08_19.md)
**status**: active · **estimate**: 0.24 cal AI-days (class: infra)
**title**: AO satellite AO batch 25 — finalize

### [`asset_class_to_asset_group_rename_2026_07_21`](../active/asset_class_to_asset_group_rename_2026_07_21.md)
**status**: active · **estimate**: 1.2 cal AI-days (class: refactor)
**title**: AssetClass → AssetGroup rename — domain enum only, cross-repo coordinated landing

### Context-scout frontmatter and plan-brainstorm plumbing
**status**: active · **estimate**: 0.8 cal AI-days (class: infra)
**title**: Complete context_scout plumbing + close a frontmatter-schema drift + add a plan-brainstorm skill

### [`cross_cutting_satellite_ao_dispatch_batch16_2026_08_17`](../active/cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md)
**status**: active · **estimate**: 2.0 cal AI-days (class: infra)
**title**: cross-cutting satellite AO dispatch batch 16 — 2026-08-17

### [`cross_cutting_satellite_ao_dispatch_batch16_2026_08_17_finalize`](../active/cross_cutting_satellite_ao_dispatch_batch16_2026_08_17_finalize.md)
**status**: active · **estimate**: 0.5 cal AI-days (class: infra)
**title**: Finalize — cross-cutting satellite AO dispatch batch 16 (2026-08-17)

### [`doc_body_link_checker_blind_to_backtick_citations_2026_08_02_finalize_2026_08_08`](../active/doc_body_link_checker_blind_to_backtick_citations_2026_08_02_finalize_2026_08_08.md)
**status**: active · **estimate**: 0.24 cal AI-days (class: infra)
**title**: check_doc_body_links.py backtick-citation blind spot — finalize

### [`meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10`](../active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md)
**status**: active · **estimate**: 0.6 cal AI-days (class: refactor)

### [`multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01_finalize_2026_08_08`](../active/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01_finalize_2026_08_08.md)
**status**: active · **estimate**: 0.4 cal AI-days (class: infra)
**title**: Multi-agent slot collision + safe-doc-push hardening — finalize

### [`na_docs_validity_and_ao_eligibility_audit_2026_07_26`](../active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md)
**status**: active · **estimate**: 14.4 cal AI-days (class: research)
**title**: >-

### [`task_template`](../active/task_template.md)
**status**: active
**title**: Task Template — How to Author a Plan

## P3 — backlog; revisit quarterly

### [`meta_plan_corpus_hygiene_ao_dispatch_batch1_finalize_2026_08_10`](../active/meta_plan_corpus_hygiene_ao_dispatch_batch1_finalize_2026_08_10.md)
**status**: active · **estimate**: 0.12 cal AI-days (class: refactor)
