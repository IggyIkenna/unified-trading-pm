---
title: "Playbook SSOT — Stage 1: extract rules + reference template"
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-19
depends_on: []
blocks:
  - playbook_ssot_stage_2_doc_rewrite
  - playbook_ssot_stage_3_infra_spec
# Sibling plans:
#   plans/active/playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md
#   plans/active/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md
# Parent:
#   plans/archive/we-need-a-documented-foamy-mango.md (the original playbook SSOT plan — Stage 0 — already shipped)
---

# Stage 1 — Playbook SSOT rules extraction + reference template

## Context

The playbook SSOT at [codex/14-playbooks/](../../codex/14-playbooks/) shipped in commit `162c7a40` as 23 docs of IA +
implementation spec. Follow-up agent feedback (2026-04-19, "Polished v1") flagged that the current docs read as
engineering operating notes — correct content, wrong register for sales / product / leadership. The fix is a new
**experience layer** with its own grammar, tone, and decision model, layered over the existing implementation docs.

Before rewriting 40 docs (Stage 2) or spec'ing infra (Stage 3), the rules that govern those rewrites need to be locked.
This plan extracts the rules from the v1 feedback into clean, citable files under `codex/14-playbooks/_ssot-rules/`,
writes **one** reference experience playbook (IM Decision Journey) as the canonical template, and updates the dir README
to signal the new layering.

**Scope discipline:** this plan ships rules + one reference template. It does NOT rewrite the other 8 experience
playbooks, does NOT create commercial-model / demo-ops / sales-ops dirs, does NOT touch infra. Those are Stage 2 and
Stage 3.

## Decisions locked with user (2026-04-19)

| Decision                                        | Chosen                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Rationale                                                                                           |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Layer separation                                | Experience layer sits alongside implementation layer under `codex/14-playbooks/` (nested, not parallel top-levels)                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Keeps codex numbered-dir convention; one SSOT dir per semantic layer                                |
| Experience grammar                              | 9 sections per doc: Audience / Moment in journey / What Odum must prove / Experience goal / Walkthrough / Key messages / What not to show / Desired next step / Internal handoff                                                                                                                                                                                                                                                                                                                                                                                                               | v1 agent feedback; enforced across all 9 experience playbooks                                       |
| Tone / posture                                  | Calm, specific, credible, lightly guided, never desperate. Axis.to / podlabs.xyz as tone benchmarks (restraint, specificity, institutional posture)                                                                                                                                                                                                                                                                                                                                                                                                                                            | User directive 2026-04-19                                                                           |
| Naming                                          | Human titles in public-facing docs ("Investment Management Briefing"), internal pb1/pb2/pb3 labels retained for engineering cross-ref                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Internal shorthand stays; external copy reads institutional                                         |
| DART commercial model                           | 2-axis: strategy origin (Odum-strategy vs client-strategy) × stack depth (reporting-only visibility / client-strategy+downstream / full-DART-pipeline)                                                                                                                                                                                                                                                                                                                                                                                                                                         | Cleaner than the earlier 3-path framing; adopt wholesale                                            |
| Same-system principle (**expanded 2026-04-19**) | Five sub-claims: (a) DART/IM/Reg-Umbrella client surfaces are partitioned views of the same internal Odum operating system; (b) research infrastructure ≡ live infrastructure — any metric generated in research is generated live via the same component; (c) trading terminal is a live/batch toggle over the same component tree; (d) strategy catalogue rows carry phase tags (research/paper/live) rather than forking the UI per phase; (e) paper trading has same look and feel as live. **Phase (research/paper/live) is orthogonal to maturity (CODE_NOT_WRITTEN → LIVE_ALLOCATED).** | Codify as named rule 03. Pre-drafted by master planner in this session for Stage 1 agent reference. |
| Data licensing boundary                         | DART is enriched platform services, NOT direct raw-data resale. Pricing can use data-sensitive building blocks internally; external framing is enriched services                                                                                                                                                                                                                                                                                                                                                                                                                               | Commercial/legal guardrail                                                                          |
| Pricing tier model                              | 2 external tiers: Tier A (cost-plus, low margin) + Tier B (fixed upfront + fixed monthly, premium). Internal cost column kept private (codex-only, not in client-facing copy). 12-month minimum commitment on both tiers                                                                                                                                                                                                                                                                                                                                                                       | User directive 2026-04-19                                                                           |
| Reference template first                        | Write 1 experience playbook (IM Decision Journey) completely before replicating across the other 8                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | De-risks template quality; user can calibrate tone before scaling                                   |
| Internal one-liners                             | DART = "accelerator for strategy, research, execution, control — the same system Odum uses internally"; IM = "allocate capital to Odum-managed strategies; reporting built in (same stack as Odum uses itself)"; Reg Umbrella = "operate regulated activity under Odum's FCA permissions; onboarding, compliance, MLRO, supervision, reporting included"                                                                                                                                                                                                                                       | User one-liners 2026-04-19, lightly polished                                                        |

## Cross-references

- **Stage 2**
  [plans/active/playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md](playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md)
  — applies these rules to 40 docs. Cannot start until Stage 1 Phase 1.9 verification passes.
- **Stage 3**
  [plans/active/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md](playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md)
  — infra spec. Can run in parallel with Stage 2 once Stage 1 locks the rules.
- **Parent SSOT work** (archived): [plans/archive/00-MASTER-CICD-PLAN.md](../archive/00-MASTER-CICD-PLAN.md) — lineage
  reference (Stage 0 audit trail) 14-playbooks skeleton plan.
- **Existing experience playbook draft**: the v1 agent feedback in the 2026-04-19 conversation will be saved as
  `/codex/14-customer-journeys/_ssot-rules/_source-v1-feedback.md` in Phase 1.0 for stable citation.

## Mandatory read-set (before any work)

Agents executing this plan MUST read:

**Current SSOT state:**

1. [/codex/14-customer-journeys/README.md](/codex/14-customer-journeys/README.md) — current state of the playbook SSOT
2. [/codex/14-customer-journeys/glossary.md](/codex/14-customer-journeys/glossary.md) — canonical terms (DART, SMA,
   Pooled, etc.)
3. [/codex/14-customer-journeys/information-architecture.md](/codex/14-customer-journeys/information-architecture.md) —
   IA tree
4. [/codex/14-customer-journeys/playbooks/03c-demo-dart.md](/codex/14-customer-journeys/playbooks/03c-demo-dart.md) —
   richest existing impl-layer doc; reference for what "route-first" looks like so the rewrite doesn't regress

**Hard taxonomy sources (authoritative for rule derivation):** 5.
[/codex/09-strategy/README.md](/codex/09-strategy/README.md) 6.
[/codex/09-strategy/architecture-v2/README.md](/codex/09-strategy/architecture-v2/README.md) — 18 archetypes × 8
families × 7 axes 7.
[/codex/09-strategy/architecture-v2/category-instrument-coverage.md](/codex/09-strategy/architecture-v2/category-instrument-coverage.md)
— coverage matrix + 10 block-list groups 8.
[/codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md](/codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md)
— lock_state × maturity model 9.
[/codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md](/codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md) — UI demo
parity (drives rule 03: same-system-principle) 10. [codex/02-venues/](../../codex/02-venues/) — venue registry

**Active plan context (don't duplicate their work):** 11.
[plans/active/user_management_merge_2026_03_23.plan.md](user_management_merge_2026_03_23.plan.md) 12.
[plans/active/share_class_architecture_2026_04_01.plan.md](share_class_architecture_2026_04_01.plan.md) 13.
[plans/active/defi_demo_e2e_workflow_2026_03_30.plan.md](defi_demo_e2e_workflow_2026_03_30.plan.md)

**Source material for Stage 1 extraction:** 14. `/codex/14-customer-journeys/_ssot-rules/_source-v1-feedback.md` — saved
in Phase 1.0

**Project rules (mandatory):** 15.
[unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md](../../cursor-configs/SUB_AGENT_MANDATORY_RULES.md) 16.
[unified-trading-pm/plans/PLAN_FORMAT.md](../PLAN_FORMAT.md) — Cursor checkbox format

## Out of scope (explicit)

- Rewriting the 8 other experience playbooks (Stage 2)
- Creating `commercial-model/`, `demo-ops/`, `sales-ops/`, `registry-and-entitlements/`, `implementation-mapping/` dirs
  (Stage 2)
- Populating pricing numbers in `pricing-principles.md` — only the rules (2-tier, 12mo min, internal private), numbers
  come in Stage 2
- Any UI code changes
- Any infra spec work (Stage 3)
- Deleting or archiving existing `codex/14-playbooks/playbooks/` docs — they remain as impl-layer siblings; Stage 2 may
  mark them `[IMPL LAYER]` via a META file or README update

## Phase breakdown

### Phase 1.0 — Pre-drafted by master planner ✅

> **These 4 artefacts are pre-committed by the master planner in commit `<stage-1-prefill>` (2026-04-19) and MUST NOT be
> overwritten by the Stage 1 agent:**
>
> - `/codex/14-customer-journeys/_ssot-rules/_source-v1-feedback.md`
> - `/codex/14-customer-journeys/_ssot-rules/03-same-system-principle.md` (includes the 5 sub-claims + phase/maturity
>   orthogonality)
> - `/codex/14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md` (2-axis matrix + 3 paths + worked examples)
> - `/codex/14-customer-journeys/_ssot-rules/08-pricing-principles.md` (2-tier Tier A/B, 12mo min, internal private,
>   per-block mixable)

- [x] [MASTER] P0. Pre-draft `_ssot-rules/_source-v1-feedback.md` + rules 03, 04, 08 (done this session).
- [x] [AGENT] P0. Verify the 4 pre-drafted files exist and are well-formed. DO NOT overwrite; if you find inconsistency
      with the 2026-04-19 decisions table above, flag in the report rather than editing.

### Phase 1.1 — Extract rule files from v1

Extract each rule into its own short, focused file (target 80–200 lines each). Every file opens with a 1-line purpose +
cites the v1 source by line range.

- [x] [AGENT] P0. `_ssot-rules/README.md` — dir map, ordering, how to cite rules, relationship to experience/ layer.
- [x] [AGENT] P0. `_ssot-rules/01-grammar.md` — the 9 sections every experience playbook has. Include the canonical
      ordering and a 1-line purpose per section.
- [x] [AGENT] P0. `_ssot-rules/02-tone-and-posture.md` — calm/specific/credible/non-desperate; Axis.to + podlabs.xyz
      benchmark notes (what to borrow, what not to borrow); anti-AI-tone guardrails; common phrasing to avoid (waitlist
      energy, conversion pressure, generic "revolutionary" language).
- [x] [MASTER] P0. `_ssot-rules/03-same-system-principle.md` — **PRE-DRAFTED 2026-04-19**. 5 sub-claims: partitioned
      views + research/live infra parity + terminal live/batch toggle + catalogue phase tags + paper-same-look-and-feel.
      Phase orthogonal to maturity. Agent verifies; does not overwrite.
- [x] [MASTER] P0. `_ssot-rules/04-dart-commercial-axes.md` — **PRE-DRAFTED 2026-04-19**. 2-axis matrix (strategy origin
      × stack depth) + 3 practical paths + worked examples. Agent verifies; does not overwrite.
- [x] [AGENT] P0. `_ssot-rules/05-building-block-dimensions.md` — 13 building blocks (reporting core, regulatory
      umbrella reporting, IM allocator reporting, strategy-service entry, instructions integration, research/promote
      pipeline, execution layer, venue packs, chain packs, instrument-type packs, analytics packs,
      exclusivity/non-compete premium, custom solution premium). These become the columns in Stage 2's pricing doc and
      the dimensions in Stage 3B's UAC combo rules.
- [x] [AGENT] P0. `_ssot-rules/06-show-dont-show-discipline.md` — the "what to show first" / "what not to show unless
      asked" rule. Every experience playbook must have both sections. Include DART demo-mode variants (broader platform
      vs turbo).
- [x] [AGENT] P0. `_ssot-rules/07-data-licensing-boundaries.md` — DART is enriched services, not raw-data resale.
      Internal pricing may use data-sensitive blocks; external framing must be enriched services. Cite UAC licensing
      tier dimension.
- [x] [MASTER] P0. `_ssot-rules/08-pricing-principles.md` — **PRE-DRAFTED 2026-04-19**. 2-tier external model (Tier A
      cost-plus / Tier B fixed upfront+monthly), 12mo min, internal cost codex-private, per-block tier mixable,
      exclusivity/custom premiums Tier B only. No numbers (Stage 2 populates). Agent verifies; does not overwrite.
- [x] [AGENT] P0. `_ssot-rules/09-internal-commercial-oneliners.md` — the 3 user-provided one-liners (DART / IM / Reg
      Umbrella) as internal sales shorthand. Every public-facing doc expands these into a calm paragraph; internal docs
      can use them directly.
- [x] [AGENT] P0. `_ssot-rules/10-strategy-instruction-schema-principles.md` — **ADDED 2026-04-19**. The fit-check layer
      for the `(Client, downstream-integration)` DART path (rule 04). Defines: what Odum execution needs
      (instrument+venue context, intended action, size/target exposure, timeframe/urgency, order constraints,
      strategy/instruction id, lifecycle updates/replace/cancel behavior, essential risk+allocation constraints); what
      Odum does NOT need (regime classification logic, raw model logic, signal-generation methodology, broader upstream
      IP); package boundaries (signals-only gets downstream operating surfaces + some analytics; does NOT auto-get
      research/backtest/promote); pre-demo fit-check discipline (pb2b must include this layer; prospect self-sorts
      before demo). Enforcement: any DART-path commercial quote references this rule. Cross-refs rule 04 + rule 08
      (instruction integration depth as pricing dimension).

### Phase 1.2 — Write IM Decision Journey reference template

- [x] [AGENT] P0. Create `codex/14-playbooks/experience/` dir.
- [x] [AGENT] P0. Write `experience/TEMPLATE.md` — empty 9-section skeleton with 1-line guidance per section, marked as
      the authoritative template. Cite rules 01–09.
- [x] [AGENT] P0. Write `experience/im-decision-journey.md` — the full reference playbook using the template. Content
      comes verbatim from the v1 agent feedback (Playbook 2a — Investment Management briefing section), adapted to sit
      cleanly in this format. This is the PATTERN that Stage 2 replicates for the other 8 playbooks.
- [x] [AGENT] P0. `experience/README.md` — what lives in this dir, grammar enforcement rule, test-coverage expectation
      (every experience playbook has a matching Playwright spec), how it relates to impl-layer docs.

### Phase 1.3 — Signal the layered structure

- [x] [AGENT] P0. Update `/codex/14-customer-journeys/README.md` — add a `## Layered structure` section explaining:
      experience layer (narrative, sales-owned) on top; impl layer (current playbooks/, authentication/, environments/,
      cross-cutting/, page-triage/, testing/, roadmap/) underneath; rules in `_ssot-rules/`. Include a "start here"
      reader-path per role (sales → experience/; engineer → playbooks/ + cross-cutting/; admin → all).
- [ ] [AGENT] P0. Update `codex/00-SSOT-INDEX.md` row for `14-playbooks/` to reflect the layered structure (add one line
      mentioning experience/ + \_ssot-rules/).
- [ ] [AGENT] P1. Add a `## Layer` note to `/codex/14-customer-journeys/playbooks/README.md` (create if missing) marking
      it as `[IMPL LAYER]` and pointing to `experience/` for narrative.

### Phase 1.4 — Verification

- [ ] [AGENT] P0. Verify all 9 rule files exist, each < 250 lines, each cites v1 source.
- [ ] [AGENT] P0. Verify `experience/im-decision-journey.md` follows grammar 01 strictly (all 9 sections present + in
      order).
- [ ] [AGENT] P0. Verify 00-SSOT-INDEX + codex/README + 14-playbooks/README are internally consistent.
- [ ] [AGENT] P0. Run `grep -r '\-\- for Stage 2 \-\-' codex/14-playbooks/` — all Stage 2 handoffs should be flagged
      with this marker.
- [ ] [AGENT] P0. Commit via
      `bash scripts/quickmerge.sh "docs(codex/playbooks): Stage 1 — extract SSOT rules + IM reference template" --agent --files "codex/14-playbooks/_ssot-rules/ codex/14-playbooks/experience/ /codex/14-customer-journeys/README.md codex/14-playbooks/playbooks/ codex/00-SSOT-INDEX.md"`.

## Critical files

**New:**

- `codex/14-playbooks/_ssot-rules/` — 11 files (README + \_source-v1-feedback + 9 rule files)
- `/codex/14-customer-journeys/experience/README.md`
- `/codex/14-customer-journeys/experience/TEMPLATE.md`
- `/codex/14-customer-journeys/experience/im-decision-journey.md`

**Modified:**

- `/codex/14-customer-journeys/README.md` (add layered-structure section)
- `codex/00-SSOT-INDEX.md` (update 14-playbooks row)
- `/codex/14-customer-journeys/playbooks/README.md` (new; flag as impl layer)

## Execution DAG

```
Phase 1.0 (save v1) ──▶ Phase 1.1 (extract 9 rules) ──┐
                                                      │
                                                      ▼
                                       Phase 1.2 (template + IM playbook)
                                                      │
                                                      ▼
                                       Phase 1.3 (signal layering)
                                                      │
                                                      ▼
                                       Phase 1.4 (verify + commit)
                                                      │
                                                      ▼
                              ┌───────────────────────┴───────────────────────┐
                              ▼                                               ▼
                     Stage 2 (8 more playbooks)              Stage 3 (infra spec)
```

## Verification

1. Fresh-reader test: hand an engineer unfamiliar with this convo only
   `/codex/14-customer-journeys/_ssot-rules/01-grammar.md` — they should produce a compliant playbook skeleton from the
   rule file alone.
2. Tone test: read `experience/im-decision-journey.md` aloud — it should sound like Axis.to / podlabs.xyz, NOT like
   AI-generated marketing copy.
3. Cross-citation: every rule file cites `_source-v1-feedback.md` with line or section refs.
4. Stage 2 unblocked: a Stage 2 agent can read all 9 rules + the IM playbook and understand what to produce for the
   other 8.

## Handoff to Stage 2

Stage 2's plan
([playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md](playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md)) takes
over here. Stage 2 agent reads all 9 rules + the IM playbook, then replicates the pattern across DART, Reg Umbrella, pb1
marketing, pb2 hub, pb3 hub, and the 3 demo playbooks; creates commercial-model/ / demo-ops/ / shared-core/ /
implementation-mapping/ dirs; marks existing impl-layer docs.

---

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Stage 1.**

---

You are executing **Stage 1 of the Playbook SSOT restructure** for the Unified Trading System at Odum Research.

### Mandatory rules injection

Before any action, read and apply:

- `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md` — every todo in your
  plan files uses Cursor checkboxes (`- [x]` / `- [ ]`)
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 1.0 through 1.4 of this plan:
`plans/active/playbook_ssot_stage_1_rules_2026_04_19.plan.md` in the `unified-trading-pm` repo.

### Read-set (mandatory, in this order)

1. This plan file (`plans/active/playbook_ssot_stage_1_rules_2026_04_19.plan.md`)
2. `/codex/14-customer-journeys/README.md`, `glossary.md`, `information-architecture.md`, `playbooks/03c-demo-dart.md`
3. `/codex/09-strategy/architecture-v2/README.md` + `category-instrument-coverage.md`
4. `/codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md`
5. `codex/02-venues/` (top-level index)
6. **Pre-drafted artefacts** (already on `live-defi-rollout`, do not overwrite):
   - `/codex/14-customer-journeys/_ssot-rules/_source-v1-feedback.md`
   - `/codex/14-customer-journeys/_ssot-rules/03-same-system-principle.md`
   - `/codex/14-customer-journeys/_ssot-rules/04-dart-commercial-axes.md`
   - `/codex/14-customer-journeys/_ssot-rules/08-pricing-principles.md` Read these first — rules 01, 02, 05, 06, 07, 09
     must match their style + cite the same v1 source.

### Deliverables

**Create (6 rule files + experience assets + README markers):**

- `/codex/14-customer-journeys/_ssot-rules/README.md`
- `/codex/14-customer-journeys/_ssot-rules/01-grammar.md`
- `/codex/14-customer-journeys/_ssot-rules/02-tone-and-posture.md`
- `/codex/14-customer-journeys/_ssot-rules/05-building-block-dimensions.md`
- `/codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md`
- `/codex/14-customer-journeys/_ssot-rules/07-data-licensing-boundaries.md`
- `/codex/14-customer-journeys/_ssot-rules/09-internal-commercial-oneliners.md`
- `/codex/14-customer-journeys/_ssot-rules/10-strategy-instruction-schema-principles.md` (**ADDED 2026-04-19**)
- `/codex/14-customer-journeys/experience/README.md` + `TEMPLATE.md` + `im-decision-journey.md`
- `/codex/14-customer-journeys/playbooks/README.md` (flag as impl layer)

**Do NOT create (already pre-drafted by master planner):**

- `_source-v1-feedback.md` / `03-same-system-principle.md` / `04-dart-commercial-axes.md` / `08-pricing-principles.md`

**Modify:**

- `/codex/14-customer-journeys/README.md` — add `## Layered structure` section
- `codex/00-SSOT-INDEX.md` — update the `14-playbooks/` row

**Commit via:**

```
cd unified-trading-pm
bash scripts/quickmerge.sh "docs(codex/playbooks): Stage 1 — extract SSOT rules + IM reference template" \
  --agent \
  --files "codex/14-playbooks/_ssot-rules/ codex/14-playbooks/experience/ /codex/14-customer-journeys/README.md /codex/14-customer-journeys/playbooks/README.md codex/00-SSOT-INDEX.md"
```

If quickmerge is blocked by unrelated pre-existing WIP (e.g. dep-alignment failures on files you haven't touched), fall
back to manual `git add <explicit-files> && git commit && git push origin live-defi-rollout`. DO NOT stage any file you
didn't create or modify.

### Success criteria (report back with each)

1. ✅ Pre-drafted 4 files (`_source-v1-feedback`, rules 03, 04, 08) verified untouched — paste SHA of file via
   `git log -1 --format=%H -- <path>`.
2. ✅ 6 new rule files created (01, 02, 05, 06, 07, 09) + README — all cite `_source-v1-feedback.md` by section.
3. ✅ `experience/im-decision-journey.md` follows the 9-section grammar from rule 01 (list all 9 sections in your
   report).
4. ✅ Tone audit: paste the first 5 lines of `im-decision-journey.md` in your report — they should be commercial, calm,
   institutional; NOT engineering-speak. Benchmark against rules 02 + pre-drafted rule 03 tone.
5. ✅ Commit SHA pushed to `origin/live-defi-rollout`.

### What NOT to do

- Do NOT overwrite the 4 pre-drafted files (`_source-v1-feedback.md`, rules 03, 04, 08). If you find inconsistency with
  the plan's decisions table, flag in the report instead of editing.
- Do NOT rewrite any existing `codex/14-playbooks/playbooks/*.md` content (mark as impl-layer only).
- Do NOT create `commercial-model/`, `demo-ops/`, `sales-ops/`, or `implementation-mapping/` dirs (Stage 2's job).
- Do NOT populate pricing numbers anywhere. Rule 08 is principles-only.
- Do NOT touch any file currently in WIP diff on `live-defi-rollout` that you didn't modify yourself (check `git status`
  before staging).
- Do NOT use `--dep-branch` flag.
- Do NOT generate generic AI-marketing prose. Tone benchmark: Axis.to + podlabs.xyz + the pre-drafted rule 03 + 04 + 08
  style. Re-read rule 02 before every doc you write.

### Report back

Return a concise summary:

- list of files created (with line counts)
- first 5 lines of `im-decision-journey.md` (tone check)
- commit SHA
- any blockers / gaps / questions for the user before Stage 2 can proceed

### SOURCE_V1

[The agent invoking this prompt should paste the full "Client Experience Playbooks — Polished v1" document from the
2026-04-19 conversation here, verbatim, before sending. It is the source material for Phase 1.0. If unavailable, request
it from the user before proceeding.]
