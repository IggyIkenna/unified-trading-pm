---
doc_type: codex-ssot
title: Foundation-Completion-Gate Discipline
summary:
  The 9-layer sequencing rule (orchestration→reference→availability-oracle→manifest→market-data→features→
  strategy/execution→live-adapters→perf) — no plan ships layer N+1 items before layer N is GREEN-audited +
  manifest-divergence 0 for the affected asset_groups; referenced from CLAUDE.md Citadel standard item 8. 2026-07-28
  refinement adds the granular per-AG sub-sequence inside layers 1/4/5 (code → canonical migration → catalogue/
  consolidator verified → smoke-test skills GREEN → backfill to 100% → live+T+1) plus the downstream ML/strategy/
  batch/paper/live ordering.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    agent-orchestrator,
    deployment-service,
    execution-service,
    features-service,
    instruments-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: [foundation-gate, layering, plan-review, audit, sequencing]
related:
  [
    ../../plans/archive/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md,
    ../../plans/epics/mtds_mdps_master.md,
    /codex/11-project-management/citadel-grade-planning-standards.md,
    /codex/11-project-management/issue-doc-lifecycle.md,
  ]
created: 2026-05-20
authoritative_for: [foundation-completion-gate rule, layer sequencing table]
referenced_by:
  [
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/11-project-management/citadel-grade-planning-standards.md,
    /codex/11-project-management/issue-doc-lifecycle.md,
    plans/epics/mtds_mdps_master.md,
  ]
owner:
last_reviewed: 2026-10-27
code_refs:
---

# Foundation-Completion-Gate Discipline

> **SSOT** for sequencing plans across architecture layers. Referenced from CLAUDE.md § "Citadel-Grade Planning
> Standards" item 8.

## The rule

**No plan may ship items in layer N+1 before layer N has GREEN audit + manifest divergence = 0 for the affected
asset_groups.**

Parallel-up across asset_groups within a layer is encouraged. Parallel-up across layers is review-blocking.

## The layers (workspace-canonical, locked 2026-05-20)

| N   | Layer                                                                                      | GREEN criterion                                                       |
| --- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| 0   | orchestration (`agent-orchestrator`)                                                       | C11 audit GREEN — orchestrator-service contract                       |
| 1   | reference (`instruments-service`)                                                          | C0/C1/C2/C3 audits GREEN — IS→{MTDS,features,strategy,execution}      |
| 2   | availability oracle (`expected_coverage()` + UAC continuity + gap calendars)               | A2 dump verified by operator                                          |
| 3   | manifest substrate (v8 schema + typed `EmptyConfirmedReason` + `DIVERGENT_EMPTY` detector) | A3 divergence report = 0 `MISSING_EXPECTED` for affected asset_groups |
| 4   | market data (`market-tick-data-service`)                                                   | C0/C4/C5 audits GREEN — MTDS preflight wired                          |
| 5   | features (`features-service`)                                                              | C4/C6 audits GREEN — missing-data downgrade policy live               |
| 6   | strategy + execution                                                                       | C5/C6/C7/C8 audits GREEN                                              |
| 7   | live adapters                                                                              | parallel to 4 once batch (layer 4) is honest                          |
| 8   | perf                                                                                       | gated on layer 6 GREEN — never optimise a broken pipeline             |

Master tracker for the audits + GREEN states:
[plans/active/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md](../../plans/archive/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md).

## Why this rule exists (the retrospective insight)

The 2026-Q1 to 2026-Q2 master plan optimised for "DeFi live by 2026-05-23", which inherently rewarded going wide on
execution-service and paper-trade scaffolding before going deep on data correctness. Agents optimised for the named
gate.

Result: by 2026-05-19, the workspace had ~14 launchers with silent log-upload bugs, multiple MTDS handlers with
hardcoded venue URLs ignoring instruments-service, manifest v4 holdouts emitting silent absences, and a paper-trade plan
layered on top of all of it. The mega audit (Phase A-F) exists as the corrective rebuild from foundation up.

The diagnosis: agents weren't told the foundation-gate rule explicitly. The master plan's success metric drove
parallel-up across layers. This SSOT codifies the rule so future agents have a hard discipline.

## How to apply

### When writing a plan

1. **Identify the layer** the plan operates in (use the table above).
2. **Verify the prior layer is GREEN** for the asset_groups your plan touches.
   - Check the mega-audit tracker's audit-status column.
   - If prior layer is RED → STOP. Either work on the prior-layer plan, or scope your plan strictly to refactor/codex/QG
     work that doesn't depend on the prior layer.
3. **Mark the layer + parallel-asset-groups** in your plan frontmatter:
   ```yaml
   layer_n: 4 # market data
   parallel_asset_groups: [cefi, defi, tradfi, sports, prediction]
   prior_layer_green_required: [C0, C4, C5] # audit IDs
   ```
4. **Within-layer parallel work is encouraged**: a plan in layer 4 may ship CeFi + DeFi + TradFi handlers in parallel
   slots, because they share the same prior-layer dependency (layer 3 manifest substrate). What's banned is shipping a
   layer-5 features fix while layer 4 is still RED for that asset_group.

### When reviewing a plan

A plan that ships layer-N+1 items before layer-N GREEN is **review-blocking**. The plan must either:

- Be re-scoped to wait for layer N, OR
- Be split: layer-N portion ships first, layer-N+1 portion gates on that.

### When dispatching slots

The orchestrator MUST NOT dispatch a slot to layer-N+1 work while that slot's asset_groups have a RED layer-N audit.
Even if the work "looks ready" — the RED state means the contract underneath is unverified and the layer-N+1 work will
accumulate placeholders that the next audit will need to undo.

## Anti-patterns (review-blocking)

- "We'll come back and fix data later, ship execution first" — the exact failure mode that produced the 2026-05-19
  audit-undo cost.
- "Layer-N+1 is independent of layer-N for this asset_group" — almost always wrong; verify by reading the contract audit
  doc, not by intuition.
- "We have a placeholder for the layer-N piece" — placeholders without a named successor are banned per CLAUDE.md §
  "Temporary states". Foundation gate is the stronger version: even WITH a named successor, layer-N+1 work on top of a
  placeholder is banned.
- "The layer-N audit is in-flight, we can start layer-N+1 in parallel" — no. Start layer-N+1 when the audit lands GREEN,
  not when it's spawned.

## Composition with existing rules

- **Capture Discoveries As Plan Todos**: if you discover a layer-N gap while working on a layer-N+1 plan, the foundation
  gate makes you STOP. Add the discovery to the layer-N plan and pause your work; do not paper over with a placeholder.
- **No fire-and-forget VM launches**: same root pattern (verify before proceeding). Foundation gate is the design-time
  version; VM launch verification is the runtime version.
- **External Data Is Always Available**: a layer-N adapter blocked on credentials goes to `BLOCKED-CREDENTIALS` status,
  not `DEFERRED`. The layer doesn't go GREEN until the adapter scaffolds + credential ask is acked, but layer-N+1 work
  can wait on the credential rather than on a full re-build.
- **Plans Run To Actual Completion**: "shipped" for foundation-gate purposes means operationally-shipped —
  manifest-verified, divergence = 0, audit GREEN. Code-merged is NOT GREEN for this rule.

## Reference incident

The 2026-05-19 → 2026-05-20 audit cycle that produced the mega-audit framework. Specifically: 14-launcher EXIT-trap bug
(deployment-service@6b4610c), Drift S3 silent-absence (`is_mtds_contract_audit_2026_05_20.md`), and the discovery that
6+ MTDS handlers hardcode venue URLs despite IS providing the canonical adapter. All three are layer-N (data
correctness) gaps that the master plan walked past on its way to layer-7 (paper trade).

## Worked example — MTDS/MDPS migration layers 1-3

`plans/epics/mtds_mdps_master.md` is the concrete instantiation of this gate for the MTDS/MDPS data-pipeline migration.
Phases -2 → 2 are layers 1-3 (QG-green foundation → bucket SSOT canonicalisation → physical GCS migrations). Phase 3 (VM
relaunches + live adapter cutover) is layer-4 and is hard-blocked by the Phase 2 gate. Any plan proposing Phase 3 work
while Phase 2 items are still open is a direct violation of this rule. Agents should read that epic before scheduling
any migration-adjacent work.

## 2026-07-28 refinement — the granular per-AG sub-sequence inside layers 1/4/5

Operator ruling (Ikenna, 2026-07-28) resolves layers 1 (reference/IS) and 4 (market data/MTDS) — and, once repeated,
layer 5 (features/MDPS) — into an explicit sub-sequence. This does NOT renumber the layer table above; it's the
within-layer resolution the table left implicit. Per asset_group, in order:

1. **Code changes** for that AG's adapters/handlers ship first.
2. **Canonical migrations run + non-canonical paths are removed** from the manifest and GCS objects are migrated (no
   non-canonical residue left behind "for later").
3. **Instrument catalogue rollups + manifest consolidators are verified WORKING** — not just deployed; prove they
   actually produce correct rollups/consolidated state.
4. **Smoke-test skills run GREEN for that AG** — `/data-pipeline-check-is` + `/data-pipeline-check-mtds` prove every
   shard's adapter actually works, not just that the code compiles.
5. **Backfill to 100% completion** — zero `attempted_failed` rows, zero FALSE `empty_confirmed` (a genuine absence is
   fine; a lazily-stamped one is not).
6. **Live data pipeline + T+1 backfill wired for batch.**

Asset groups run this 1→6 sequence IN PARALLEL with each other (unchanged from the existing "parallel-up across
asset_groups within a layer is encouraged" rule above) — the sequencing is within one AG's layer-1/4 work, not across
AGs.

**The one explicit concurrency exception**: MDPS + features-service work MAY start CONCURRENTLY with an AG's layer-4
sub-sequence, using whatever SAMPLE data is already filled, for development/testing purposes only — this does NOT let
MDPS/features reach their OWN GREEN/100% state early; that still requires the AG's MTDS layer to hit step 6 first. Once
an AG's MTDS is fully 100% (step 6), MDPS and features each run the SAME steps 2→6 (canonical migration →
catalogue/consolidator verified → smoke-test [`/data-pipeline-check-mdps`, `/data-pipeline-check-features`] → backfill
to 100% → live+T+1) until THEY independently reach 100% for that AG.

**Downstream of layer 5 completion, per the operator's named product path**: machine learning work is scoped first to
**cefi and sports** (their prediction/ML layers); strategy-service work for the **defi-basis and staked-basis**
archetypes (including equity-perps/tokenized-stocks and NASDAQ-spot exposure) plus **cefi ML strategy** comes next; then
**batch execution** on tick data where available; then **live execution in paper-trader mode**; **real (live-money)
execution is the final stage** — consistent with this doc's existing layer-6/7/8 ordering and CLAUDE.md's hard-stop on
version graduation.
