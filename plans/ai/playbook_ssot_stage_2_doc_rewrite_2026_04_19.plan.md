---
title: "Playbook SSOT — Stage 2: apply rules to 40 docs"
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-19
depends_on:
  - playbook_ssot_stage_1_rules
# Sibling plans:
#   plans/active/playbook_ssot_stage_1_rules_2026_04_19.plan.md
#   plans/active/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md
---

# Stage 2 — Playbook SSOT doc rewrite (40 docs)

## Context

Stage 1 ([playbook_ssot_stage_1_rules_2026_04_19.plan.md](playbook_ssot_stage_1_rules_2026_04_19.plan.md)) extracts the
9-section grammar, tone rules, same-system principle, DART commercial axes, building-block dimensions, show/don't-show
discipline, data-licensing boundaries, pricing principles, and internal one-liners into
`codex/14-playbooks/_ssot-rules/`, and ships IM Decision Journey as the reference template.

Stage 2 applies those rules across the full experience surface: 8 more experience playbooks, plus new `shared-core/` /
`commercial-model/` / `demo-ops/` / `implementation-mapping/` directories. Existing impl-layer docs (`playbooks/`,
`authentication/`, `environments/`, `cross-cutting/`, `page-triage/`, `testing/`, `roadmap/`) remain authoritative for
engineering but get marked as implementation layer via README updates.

**Scope discipline:** this plan is doc-only. No code changes, no UI changes, no UAC changes. Pricing numbers get
placeholders (`TBD — Odum finance to populate`); structure is locked, numbers are out of scope.

## Decisions locked with user (2026-04-19)

| Decision                                           | Chosen                                                                                                                                                                                       | Rationale                                                                                            |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Directory structure (nested under `14-playbooks/`) | `_ssot-rules/`, `experience/`, `shared-core/`, `commercial-model/`, `demo-ops/`, `implementation-mapping/`, plus existing impl layers                                                        | Agent v1 proposed 7 top-level dirs; we nest under 14-playbooks to preserve codex numbered convention |
| Demo-ops consolidation                             | Merge agent v1's `demo-controls/` + `sales-ops/` into one `demo-ops/` dir                                                                                                                    | Related content; fewer dirs for v1; split later if doc count grows                                   |
| Registry-and-entitlements deferred                 | NOT created in Stage 2 — moves to Stage 3 because it ties to real UAC registry work, not just docs                                                                                           | Boundary: Stage 2 = docs only, Stage 3 = infra spec                                                  |
| Impl-layer docs retained                           | Keep `playbooks/`, `authentication/`, `environments/`, `cross-cutting/`, `page-triage/`, `testing/`, `roadmap/` as-is; add `[IMPL LAYER]` markers via README                                 | Load-bearing implementation anchors; throwing away would lose 3000 lines of real engineering context |
| Pricing numbers stubbed                            | `pricing-building-blocks.md` ships with 13 rows × 3 columns (internal cost / Tier A cost-plus / Tier B upfront+monthly) all populated with `TBD`                                             | Structure locked; numbers come from Odum finance in a separate (non-codex) commit                    |
| Cross-linking discipline                           | Every experience playbook links to: the matching impl-layer doc, the relevant cross-cutting shared-core doc, the commercial-model doc, the demo-ops restriction profile, the Playwright spec | Each doc must trace to both narrative and implementation                                             |
| 9 experience playbooks follow IM pattern           | pb1 marketing, pb2 hub + 2b DART + 2c Reg Umbrella, pb3 hub + 3a Reg Umbrella demo + 3b IM demo + 3c DART demo                                                                               | Stage 1 ships 2a IM as the pattern; Stage 2 replicates across 8                                      |
| Pb3a + Pb3b share one walkthrough core             | Both are UI-identical per user directive; Stage 2 writes one shared-core `client-reporting-demo-walkthrough.md` + two slim narrative overlays                                                | Avoids drift                                                                                         |

## Cross-references

- **Stage 1**
  [plans/active/playbook_ssot_stage_1_rules_2026_04_19.plan.md](playbook_ssot_stage_1_rules_2026_04_19.plan.md) —
  blocking dep. Stage 2 reads all of `_ssot-rules/` + the IM reference playbook.
- **Stage 3**
  [plans/active/playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md](playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md)
  — parallelisable after Stage 1. Stage 3 reads Stage 2's `commercial-model/` + `shared-core/` outputs but does not
  depend on Stage 2 completion for its own audit phase (3A).
- **Existing active plans** (cross-linked in Stage 2 deliverables):
  - [user_management_merge_2026_03_23.plan.md](user_management_merge_2026_03_23.plan.md) — fund/org/client provisioning
  - [share_class_architecture_2026_04_01.plan.md](share_class_architecture_2026_04_01.plan.md) — SMA vs Pooled
  - [deployment_topology_and_client_isolation_2026_04_17.plan.md](deployment_topology_and_client_isolation_2026_04_17.plan.md)
    — runtime profiles
  - [defi_demo_e2e_workflow_2026_03_30.plan.md](defi_demo_e2e_workflow_2026_03_30.plan.md) — pb3c DeFi specifics
  - [platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md](platform_strategy_families_and_haruko_gaps_2026_03_28.plan.md)
    — strategy families

## Mandatory read-set

**Stage 1 outputs (primary source):**

1. `codex/14-playbooks/_ssot-rules/*.md` — all 9 rule files
2. `/codex/14-playbooks/experience/im-decision-journey.md` — the reference pattern
3. `/codex/14-playbooks/experience/TEMPLATE.md`

**Impl-layer docs (to reference, not duplicate):** 4. `codex/14-playbooks/playbooks/*.md` — all 9 current playbooks
(impl layer) 5. `codex/14-customer-journeys/playbook-concepts/*.md` — 10 files 6.
`codex/14-playbooks/authentication/*.md`, `environments/*.md`

**Taxonomy sources:** 7. `/codex/09-strategy/architecture-v2/README.md` 8.
`/codex/09-strategy/architecture-v2/category-instrument-coverage.md` 9.
`/codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md` 10. `codex/02-venues/` 11. `unified-api-contracts/` — browse
registry dirs; don't modify

**Project rules:** 12. `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` 13.
`unified-trading-pm/plans/PLAN_FORMAT.md`

## Out of scope (explicit)

- Any code / UI / UAC / Playwright changes
- Populating real pricing numbers (structure only; `TBD` stubs)
- `registry-and-entitlements/` dir (Stage 3)
- Rewriting or deleting impl-layer docs (only README flags added)
- Changes to `page-triage/`, `testing/`, `roadmap/` (they remain where they are; roadmap/ gets superseded by Stage 3E
  but the file stays until Stage 3 lands)

## Phase breakdown

### Phase 2.1 — experience/ — 8 remaining playbooks

One per archetype, strictly following `_ssot-rules/01-grammar.md`. Each doc is ~150–300 lines. Content pulled from the
v1 feedback `_source-v1-feedback.md`, plus linked to its impl-layer counterpart.

- [ ] [AGENT] P0. `experience/marketing-journey.md` (pb1)
- [ ] [AGENT] P0. `experience/briefings-hub.md` (pb2 hub)
- [ ] [AGENT] P0. `experience/dart-briefing.md` (pb2b) — **MUST INCLUDE** a dedicated **"Does DART fit you?" pre-demo
      fit-check section** per rule 10. Four sub-sections: schema explainer (1 para, calm, non-technical) / "what we need
      from you" (bullets — instrument+venue context, intended action, size or target exposure, timeframe/urgency, order
      constraints, strategy id, lifecycle update behavior, essential risk+allocation constraints) / "what we do not need
      from you" (bullets — regime classification, raw model logic, signal-generation methodology, broader upstream IP) /
      "what you get with signals-only vs full DART" (2-column comparison). Tone per rule 02: let the prospect self-sort,
      no interrogation.
- [ ] [AGENT] P0. `experience/regulatory-umbrella-briefing.md` (pb2c)
- [ ] [AGENT] P0. `experience/staging-demo-journey.md` (pb3 hub)
- [ ] [AGENT] P0. `experience/regulatory-demo.md` (pb3a) — narrative overlay only; imports walkthrough from shared-core
- [ ] [AGENT] P0. `experience/investment-management-demo.md` (pb3b) — narrative overlay only; imports walkthrough from
      shared-core
- [ ] [AGENT] P0. `experience/dart-demo.md` (pb3c) — **MUST INCLUDE** a pre-qualification paragraph in the "Moment in
      journey" section that references rule 10's fit-check. Demo assumes the prospect has already self-sorted via pb2b's
      fit-check; demo flow either confirms signals-only vs full-DART by reading prospect's declared schema shape, or
      uses the demo itself to surface that decision. "What not to show" section gates research/backtest/promote surfaces
      unless full-DART resolved.
- [ ] [AGENT] P1. Extend `experience/README.md` — add full index of 9 playbooks, role-based reader paths.

### Phase 2.2 — shared-core/ — product truths reused across layers

Files that Stage 2 creates AND Stage 3 consumes. Every file MUST cite `_ssot-rules/` by rule number.

- [ ] [AGENT] P0. `shared-core/README.md`
- [ ] [AGENT] P0. `shared-core/same-system-principle.md` — full implementation map of rule 03's **5 sub-claims**
      (expanded 2026-04-19): (a) DART/IM/Reg surfaces = partitioned views of one internal system; (b) research infra ≡
      live infra — identical metric-generation components; (c) trading terminal = live/batch toggle over same component
      tree; (d) strategy catalogue rows carry phase tags (research/paper/live), no UI fork per phase; (e) paper trading
      same look+feel as live. Map which UI routes/components implement which claim, with pointers to the current code
      locations. Cites `/codex/09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md` + rule 03 itself. Explicitly state: **phase
      (research/paper/live) is orthogonal to maturity** — a LIVE_ALLOCATED strategy can still be viewed in research
      phase when a researcher re-runs it over historical data.
- [ ] [AGENT] P0. `shared-core/org-fund-client-entity-model.md` — the org → fund(Pooled/SMA) → clients → API-keys
      hierarchy. Transcludes from `/codex/14-customer-journeys/playbook-concepts/fund-org-hierarchy.md` +
      `sma-vs-pooled.md` but re-framed for experience layer.
- [ ] [AGENT] P0. `shared-core/shared-reporting-core.md` — the client-reporting surface that pb3a and pb3b share.
      Content from `cross-cutting/client-reporting.md` rewritten experience-layer style.
- [ ] [AGENT] P0. `shared-core/strategy-origin-vs-stack-depth.md` — the DART 2-axis commercial model (rule 04) written
      as a full doc with matrix diagram + worked examples. Cross-refs: DART briefing (pb2b), DART demo (pb3c),
      commercial-model/dart-entry-points.md.
- [ ] [AGENT] P0. `shared-core/venue-chain-instrument-scope.md` — venue × chain × instrument_type dimensions as the
      building blocks of demo restriction + pricing. Cites `codex/02-venues/` and
      `09-strategy/architecture-v2/category-instrument-coverage.md`.
- [ ] [AGENT] P0. `shared-core/instruction-schema-fit-and-package-boundaries.md` — **ADDED 2026-04-19**. Implementation
      map for rule 10. Defines: (a) full required/optional field list that Odum execution accepts; (b) venue ×
      instrument × execution-mode compatibility (which schema shapes work on which venues); (c) lifecycle behavior
      (replace / cancel / amend semantics); (d) **what signals-only integration enables downstream** (execution,
      reconciliation, positions, some P&L attribution, some analytics); (e) **what signals-only does NOT enable** (full
      P&L attribution that requires upstream research lineage, promote-pipeline metrics, backtest-vs-live comparisons
      that assume the research-layer ran); (f) package boundary — signals-only upgrade path to full DART. Cross-refs
      rule 10 + rule 04 axes + Stage 3B `stage-3b-instruction-schema-contract.md`.
- [ ] [AGENT] P0. `shared-core/data-licensing-boundaries.md` — full version of rule 07; enumerates "what DART sells" vs
      "what DART doesn't sell (raw data)". Internal pricing may use data-sensitive blocks.
- [ ] [AGENT] P0. `shared-core/client-reporting-demo-walkthrough.md` — THE shared walkthrough used by pb3a and pb3b.
      Single source of truth for the Pooled/SMA → fund → client → reporting-tabs flow.

### Phase 2.3 — commercial-model/

Maps building blocks to packages, tiers, and exclusivity modifiers.

- [ ] [AGENT] P0. `commercial-model/README.md`
- [ ] [AGENT] P0. `commercial-model/dart-entry-points.md` — the 3 commercial paths (reporting-only visibility /
      client-strategy+downstream / full-pipeline) × pricing tier + examples of who buys what. Cites
      `shared-core/strategy-origin-vs-stack-depth.md`.
- [ ] [AGENT] P0. `commercial-model/im-vs-reg-reporting-logic.md` — same UI, 2 commercial framings; how pricing differs.
- [ ] [AGENT] P0. `commercial-model/building-block-packaging.md` — which building blocks cluster into which standard
      packages (starter / platform / full DART / IM-allocator / Reg-Umbrella). 13 blocks × N packages matrix.
- [ ] [AGENT] P0. `commercial-model/pricing-building-blocks.md` — THE pricing doc. 3-column table (internal cost / Tier
      A cost-plus / Tier B upfront+monthly) × 13 rows. **Numbers = `TBD` stubs.** Rules from rule 08 enforced: 12-month
      min, internal private, Tier B only unlocks exclusivity/custom premiums.
- [ ] [AGENT] P0. `commercial-model/fixed-vs-variable-commercials.md` — Tier A (variable cost-plus) vs Tier B (fixed
      upfront + fixed monthly) decision tree.
- [ ] [AGENT] P0. `commercial-model/exclusivity-and-noncompete.md` — what exclusivity/non-compete means at each tier;
      premium structure; legal framing.

### Phase 2.4 — demo-ops/ (combines demo-controls + sales-ops per Stage 2 decisions)

How restriction profiles are configured, and how sales context flows into provisioning.

- [ ] [AGENT] P0. `demo-ops/README.md`
- [ ] [AGENT] P0. `demo-ops/demo-restriction-profiles.md` — how a profile is built from pre-call notes (category /
      family / archetype / venue / instrument-type / chain scope). Profile drives: demo user entitlements, catalogue
      filtering, nav visibility. Cross-refs Stage 3B's UAC combo rules.
- [ ] [AGENT] P0. `demo-ops/dart-demo-modes.md` — broader-platform vs turbo modes; when to use which; toggle pattern for
      prospect-facing upsell views.
- [ ] [AGENT] P0. `demo-ops/upsell-overlays.md` — showing "this is your base package" with a toggle to "this is next
      tier" during demos.
- [ ] [AGENT] P0. `demo-ops/pre-demo-curation-rules.md` — what to show / skip / skim on demo day per prospect profile.
- [ ] [AGENT] P0. `demo-ops/account-intelligence-record.md` — the CRM structure per prospect (org name, service
      interests, markets, commercial path, call notes, objections, inferred gaps, next-meeting hypothesis). Replaces
      "just a lead tag".
- [ ] [AGENT] P0. `demo-ops/pre-demo-discovery-framework.md` — what sales infers and records without interrogating the
      prospect (DART readiness, strategy state, exchange onboarding, treasury workflows, regulatory cover, etc.).
- [ ] [AGENT] P0. `demo-ops/demo-decision-matrix.md` — prospect profile → recommended demo path (flavour + mode +
      restriction profile + expected next commitment).
- [ ] [AGENT] P0. `demo-ops/meeting-history-and-interest-tracking.md` — how each demo session logs back to the
      account-intelligence record so the next call is cumulative.
- [ ] [AGENT] P0. `demo-ops/post-demo-followup-orchestration.md` — the 7-day stall trigger + what email / asset goes out
      / who provisions / qualification criteria for moving to next stage.

### Phase 2.5 — implementation-mapping/ — bridges narrative → code

- [ ] [AGENT] P0. `implementation-mapping/README.md`
- [ ] [AGENT] P0. `implementation-mapping/route-mapping.md` — every experience playbook section → list of concrete UI
      routes it exercises. Drives Playwright spec coverage.
- [ ] [AGENT] P0. `implementation-mapping/persona-and-user-prototype-mapping.md` — each experience audience → which
      persona fixture in `lib/auth/personas.ts` (admin / internal-trader / client-full / client-data-only /
      client-premium / prospect-im / prospect-dart[TBD] / prospect-reg[TBD] / investor / advisor).
- [ ] [AGENT] P0. `implementation-mapping/demo-email-and-provisioning-flow.md` — how a sales "book demo" click flows to
      user-management-ui provisioning + welcome email. Stubbed automation described; Stage 3E specifies what to build.
- [ ] [AGENT] P0. `implementation-mapping/playbook-to-qa-coverage.md` — every experience playbook → matching Playwright
      spec in `tests/e2e/playbooks/`. Red rows = specs not yet written.

### Phase 2.6 — Mark existing impl-layer docs

- [ ] [AGENT] P0. `/codex/14-playbooks/playbooks/README.md` — already created in Stage 1; verify it marks the dir as
      `[IMPL LAYER]` and points to `../experience/` for narrative.
- [ ] [AGENT] P1. Add a one-line
      `> **Layer:** Implementation. Narrative lives in [codex/14-playbooks/experience/](../../codex/14-playbooks/experience/).`
      header to each of the 9 impl-layer playbooks (02a/b/c, 03a/b/c, 01, 02, 03).
- [ ] [AGENT] P1. Similar header added to `cross-cutting/`, `authentication/`, `environments/` READMEs (if present;
      create if not).

### Phase 2.7 — Update top-level SSOT indices

- [ ] [AGENT] P0. `/codex/14-playbooks/README.md` — expand `## Layered structure` section from Stage 1; add sub-dir
      entries for `shared-core/`, `commercial-model/`, `demo-ops/`, `implementation-mapping/`.
- [ ] [AGENT] P0. `codex/00-SSOT-INDEX.md` — update `14-playbooks` row with new sub-dirs.

### Phase 2.8 — Verification

- [ ] [AGENT] P0. Every experience playbook (9 total) follows grammar rule 01. Grep `_ssot-rules/01-grammar.md` section
      headers against each playbook file — all 9 sections present, in order.
- [ ] [AGENT] P0. Every shared-core / commercial-model / demo-ops doc cites at least one `_ssot-rules/` file by number.
- [ ] [AGENT] P0. Pricing doc structure verified: 3 columns × 13 rows, all `TBD` stubs, rule 08 enforced (12mo min
      noted, internal column private).
- [ ] [AGENT] P0. Cross-link graph verified: every experience playbook links to matching impl-layer doc + shared-core +
      commercial-model + Playwright spec. Run `grep -c 'See \[' codex/14-playbooks/experience/*.md` — expect ≥ 4
      outbound links per file.
- [ ] [AGENT] P0. Tone audit on 3 random experience playbooks: paste first 10 lines of each in the report — should be
      commercial/calm/specific, not engineering.
- [ ] [AGENT] P0. Commit via
      `bash scripts/quickmerge.sh "docs(codex/playbooks): Stage 2 — apply SSOT rules across 40 docs" --agent --files "codex/14-playbooks/ codex/00-SSOT-INDEX.md"`.

## Critical files

**New (~35 files):**

- `experience/` — 8 more playbooks + README update (total 9 + template + README = 11 in experience/)
- `shared-core/` — README + 7 content files
- `commercial-model/` — README + 6 content files
- `demo-ops/` — README + 9 content files
- `implementation-mapping/` — README + 4 content files

**Modified:**

- `/codex/14-playbooks/README.md`
- `codex/00-SSOT-INDEX.md`
- `codex/14-playbooks/playbooks/*.md` (9 files get 1-line layer headers)
- `/codex/14-customer-journeys/playbook-concepts/README.md` (new)
- `/codex/14-playbooks/authentication/README.md` (edit header)
- `/codex/14-playbooks/environments/README.md` (edit header)

## Execution DAG

```
Stage 1 ✅ ──▶ Stage 2 Phase 2.1 (experience/ 8 docs) ──┐
                      ↓                                 │
                      Phase 2.2 (shared-core/)─────────►│
                      ↓                                 │
                      Phase 2.3 (commercial-model/)────►│
                      ↓                                 │
                      Phase 2.4 (demo-ops/)────────────►├──▶ Phase 2.6 (mark impl)
                      ↓                                 │        ↓
                      Phase 2.5 (implementation-map/)──►│   Phase 2.7 (SSOT indices)
                                                        │        ↓
                                                        └─► Phase 2.8 (verify + commit)
                                                                 ↓
                                                         Handoff ready for Stage 3
```

Phases 2.1 through 2.5 are parallelisable if split across multiple sub-agents. A single-agent execution runs them
sequentially.

## Verification

1. **Scale check**: count `codex/14-playbooks/**/*.md` — expect 60–70 files total post-Stage-2 (was 26 post-Stage-1).
2. **Grammar check**: every `experience/*.md` has all 9 sections from rule 01.
3. **Cross-link check**: per above, ≥ 4 outbound links per experience playbook.
4. **Tone check**: random sampling, no engineering jargon without definition, no AI-generic marketing phrases.
5. **Pricing structure check**: `commercial-model/pricing-building-blocks.md` has 3 columns × 13 rows, all
   `TBD`-stubbed.
6. **Impl-layer intact**: `codex/14-playbooks/playbooks/` + `authentication/` + `environments/` + `cross-cutting/` +
   `page-triage/` + `testing/` + `roadmap/` retain all content, only README-level edits.

## Handoff to Stage 3

Stage 3 ([playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md](playbook_ssot_stage_3_infra_spec_2026_04_19.plan.md))
reads Stage 2's `commercial-model/pricing-building-blocks.md` (structure only; numbers TBD) +
`shared-core/strategy-origin-vs-stack-depth.md` + `demo-ops/demo-restriction-profiles.md` as inputs to its UAC combo
rules (Stage 3B) and derivation engine (Stage 3C).

Stage 3's presentation (Stage 3D) references the experience playbooks; Stage 3E's refactor plan supersedes
`/codex/14-playbooks/roadmap/next-waves.md` (which can then be marked deprecated).

---

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Stage 2. DO NOT start this until Stage 1 is
merged on `live-defi-rollout`.**

---

You are executing **Stage 2 of the Playbook SSOT restructure** for the Unified Trading System at Odum Research.

### Pre-flight check (do this first)

Verify Stage 1 is merged on `live-defi-rollout`:

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm
git fetch origin
git log origin/live-defi-rollout --oneline -20 | grep "Stage 1"
ls codex/14-playbooks/_ssot-rules/
ls /codex/14-playbooks/experience/im-decision-journey.md
```

All 3 commands must succeed. If not, STOP and report blocker.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md` (Cursor
  checkboxes)
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 2.1 through 2.8 of this plan:
`plans/active/playbook_ssot_stage_2_doc_rewrite_2026_04_19.plan.md`

### Read-set (mandatory, in order)

1. This plan file
2. `plans/active/playbook_ssot_stage_1_rules_2026_04_19.plan.md` (for context)
3. All 9 files in `codex/14-playbooks/_ssot-rules/`
4. `/codex/14-playbooks/experience/im-decision-journey.md` (the pattern you replicate)
5. `/codex/14-playbooks/experience/TEMPLATE.md`
6. The 9 impl-layer playbooks in `codex/14-playbooks/playbooks/` (to link to, not duplicate)
7. `/codex/09-strategy/architecture-v2/README.md` + `category-instrument-coverage.md`
8. `codex/02-venues/` top-level
9. Existing active plans (for cross-linking): user_management_merge, share_class_architecture, deployment_topology,
   defi_demo_e2e, platform_strategy_families

### Deliverables

Create ~35 new markdown files across:

- `experience/` (8 playbooks: marketing-journey, briefings-hub, dart-briefing, regulatory-umbrella-briefing,
  staging-demo-journey, regulatory-demo, investment-management-demo, dart-demo)
- `shared-core/` (README + 7 docs)
- `commercial-model/` (README + 6 docs)
- `demo-ops/` (README + 9 docs)
- `implementation-mapping/` (README + 4 docs)

Modify:

- `/codex/14-playbooks/README.md`, `codex/00-SSOT-INDEX.md`
- One-line layer headers in 9 impl playbooks + cross-cutting/authentication/environments READMEs

Content sources for each file are listed in Phases 2.1–2.5. Each file must follow rule 01 grammar (experience/) or open
with a rule-citation (others). Every file must cross-link to its related impl-layer doc where one exists.

### Commit

```
bash scripts/quickmerge.sh "docs(codex/playbooks): Stage 2 — apply SSOT rules across 40 docs" \
  --agent \
  --files "codex/14-playbooks/ codex/00-SSOT-INDEX.md"
```

Fallback to manual commit if quickmerge is blocked by unrelated WIP.

### Success criteria

1. ✅ 35+ new files created; report file count per dir
2. ✅ All 9 experience playbooks grammar-compliant (list all 9 sections per file as proof)
3. ✅ Pricing doc structure valid (3 cols × 13 rows × TBD stubs)
4. ✅ Tone audit: paste first 10 lines of 3 random experience playbooks
5. ✅ Cross-link audit: report outbound-link count per experience playbook (≥ 4)
6. ✅ Commit SHA pushed

### What NOT to do

- Do NOT populate real pricing numbers.
- Do NOT delete or rewrite impl-layer content (only 1-line headers).
- Do NOT create `registry-and-entitlements/` (Stage 3).
- Do NOT touch any file on `live-defi-rollout` you haven't explicitly created/modified.
- Do NOT use `--dep-branch`.
- Do NOT generate generic AI-marketing prose. Re-read `_ssot-rules/02-tone-and-posture.md` before writing each file.

### Report back

- List of files created per dir
- Grammar compliance proof per experience playbook
- 3 tone-sample blocks
- Cross-link counts
- Commit SHA
- Blockers / open questions for the user before Stage 3 proceeds
