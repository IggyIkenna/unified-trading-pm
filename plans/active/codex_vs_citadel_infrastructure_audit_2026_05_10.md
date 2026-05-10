---
title: Codex vs Citadel-grade infrastructure audit — KEEP / LIFT / CONSOLIDATE / DELETE / ADD
type: plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: 13-day pre-cutover sprint
companion_to: master_to_live_defi_2026_05_23.md (cross-cutting Group A/B governance + readiness checklist hygiene)
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/codex_vs_citadel_infrastructure_specs_2026_05_08.md
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/epics/cross_cutting_2026_05_23.epic.md
related_codex:
  - codex/00-SSOT-INDEX.md
  - codex/06-coding-standards/README.md
  - codex/04-architecture/
---

# Codex vs Citadel-grade infrastructure audit

## Why this plan exists

The 67-repo workspace has accumulated codex SSOTs over months. Some are accurate; some have drifted from code; some
describe systems that were superseded; some are missing entirely. Before May-23 cutover, the operator wants a fresh-eyes
audit against a Citadel-grade non-HFT combination-system bar (alpha velocity + error-free correctness, not raw latency).
Output: per-area KEEP / LIFT / CONSOLIDATE / DELETE / ADD recommendations, each with a disposition (immediate fix /
pre-cutover fix / post-cutover backlog) and an owner. Pre-cutover items ship in this plan; post-cutover items get filed
into successor plans before the audit closes.

## Scope + non-goals

### In scope (must ship by 2026-05-23)

1. Audit pass across 12 areas: data / strategy / execution / risk / ML / position-balance / instruments / alerting /
   ops / governance / UI / testing.
2. Per-recommendation disposition: immediate / pre-cutover / post-cutover. Closed enum.
3. Immediate items shipped (codex doc rewrites, SSOT consolidations, ban-now patterns added to QG).
4. Pre-cutover items shipped (architecture clean-ups that compose with the live-DeFi cutover; e.g. dead-code deletion
   on cutover hot path).
5. Post-cutover items filed as new active plans before this plan archives — no orphan recommendations.
6. Audit sign-off doc: `plans/active/issues/codex_vs_citadel_audit_signoff_2026_05_22.md` operator-reviewed.

### Non-goals (post-cutover)

- Recommendations whose implementation spans weeks (large refactors, cross-asset_group reshuffles) — get filed but not
  shipped here.
- HFT-specific optimizations — out of scope per "non-HFT combination-system" framing.

## Pre-audit / blast radius

| Surface             | Audit kind                                                                                                            |
| ------------------- | --------------------------------------------------------------------------------------------------------------------- |
| codex/02-data       | Manifest schema, honest-absence, availability-at, contracts-scope-and-layout — drift vs UAC source                    |
| codex/04-architecture | Backtest groups, kill-switch, autonomous-recovery, capital-efficiency, MEV-protection, Tenderly, batch=live          |
| codex/05-infrastructure | Live-pipeline, runtime tiers, VM tarball, launcher-script SSOT — alignment with current launchers                |
| codex/06-coding-standards | QG steps, no-Any, no-fallback, CLI convention, performance targets — currency vs banned-pattern enforcement   |
| codex/07-security   | Secret rotation, S2S auth — alignment with credential plan output                                                     |
| codex/08-workflows  | Local-dev, deployment, dev-tiers — alignment with restart-deployment-stack.sh + tier scripts                          |
| codex/09-strategy   | Strategy summary, archetype canonicalisation — drift vs registry                                                      |
| codex/10-audit      | Past audits, foundational repos — historical not active                                                               |
| codex/14-playbooks  | Authentication, signal-broadcast, shared-core — currency                                                              |
| Workspace QG        | base-service.sh STEP 5.x — completeness vs CLAUDE.md HARD RULES                                                       |
| CLAUDE.md           | Self-consistency check (rules referencing each other, supersession map, dead rules)                                   |

## Phased execution DAG

```text
0 (area enumeration) → 1 (per-area audit, 12 parallel sub-agents) → 2 (per-recommendation disposition) →
3 (immediate items shipped) → 4 (pre-cutover items shipped) → 5 (post-cutover items filed as plans) →
6 (audit sign-off doc) → 7 (cutover gate)
```

## Phase 0 — Area enumeration (Day 1, ~0.25 AI-day)

- [ ] [AGENT] P0. **0.A Confirm 12-area scope.** Adjust per operator feedback before audit pass.
- [ ] [SCRIPT] P0. **0.B Codex doc inventory.** `find unified-trading-pm/codex -name "*.md" | xargs wc -l` — input to audit.

**Full-execution criterion**: § Audit findings has the 12-area table with per-area sub-agent assignment.

## Phase 1 — Per-area audit (Days 1-5, ~4 AI-days, 12 parallel sub-agents)

Each sub-agent owns one area. Output template per area: `plans/active/issues/codex_audit_{area}_2026_05_10.md`.

- [ ] [AGENT] P0. **1.A Data area.** SSOT discipline; manifest schema; honest-absence taxonomy; available_at; pipeline_mode; downstream-handling.
- [ ] [AGENT] P0. **1.B Strategy area.** Archetype canonicalisation; strategy-service co-location; signal-leasing; promote workflow.
- [ ] [AGENT] P0. **1.C Execution area.** Matching engine hooks; live-batch parity; DeFi connectors; order-state machine; flash-loan receiver.
- [ ] [AGENT] P0. **1.D Risk area.** Circuit breakers; kill-switch; pre-flight checks; per-archetype limits.
- [ ] [AGENT] P0. **1.E ML area.** Lifecycle; training/inference colocated; cache-delta hot reload; lookahead-bias.
- [ ] [AGENT] P0. **1.F Position-balance area.** Per-client lineage; reconciliation; custody pings.
- [ ] [AGENT] P0. **1.G Instruments area.** Catalogue completeness; reference-data adapters; per-asset_group coverage.
- [ ] [AGENT] P0. **1.H Alerting area.** Live rules; synthetic filter; severity tiers; on-call routing.
- [ ] [AGENT] P0. **1.I Ops area.** VM tarball; launcher SSOT; zombie watchdog; concurrent-write CAS.
- [ ] [AGENT] P0. **1.J Governance area.** CLAUDE.md HARD RULES self-consistency; SUB_AGENT_MANDATORY_RULES symlink; plan-format discipline; daily work-split.
- [ ] [AGENT] P0. **1.K UI area.** Tier-based startup; mock vs real; firebase-local; deployment-ui surfaces.
- [ ] [AGENT] P0. **1.L Testing area.** Emulator coverage; mock fixtures; integration tiers; cassette parity.

**Full-execution criterion**: 12 issue docs in `plans/active/issues/codex_audit_*_2026_05_10.md`, each with KEEP / LIFT / CONSOLIDATE / DELETE / ADD recommendation table + per-row evidence (file:line citations).

## Phase 2 — Per-recommendation disposition (Day 6, ~1 AI-day)

- [ ] [AGENT] P0. **2.A Disposition closed enum.** `IMMEDIATE` (codex doc rewrite / SSOT consolidation that ships in days) / `PRE_CUTOVER` (architecture clean-up that composes with cutover hot path) / `POST_CUTOVER` (large refactor, cross-quarter scope).
- [ ] [AGENT] P0. **2.B Per-recommendation tagging.** Every row in every audit issue doc gets a disposition + a 1-line reason + an owner.
- [ ] [AGENT] P0. **2.C Operator review.** Operator approves dispositions; disagreements surface as P0 ping.

**Full-execution criterion**: every audit-issue-doc row has a disposition; operator has signed off via Q&A or chat.

## Phase 3 — Immediate items shipped (Days 6-9, ~3 AI-days, parallel)

- [ ] [AGENT] P0. **3.A Codex doc rewrites.** Every IMMEDIATE-tagged codex doc gets the recommended rewrite. PRs shipped per "Commit + Push + Flip" cadence.
- [ ] [AGENT] P0. **3.B SSOT consolidations.** Duplicate SSOTs deleted; cross-references rewritten; QG steps added if a banned-pattern surface emerges.
- [ ] [AGENT] P0. **3.C CLAUDE.md hygiene.** Dead rules removed; supersession banners added; cross-references resolved.

**Full-execution criterion**: every IMMEDIATE row flipped `[x]` with `<commit-sha>` evidence; codex-vs-code drift count drops to 0 on IMMEDIATE rows.

## Phase 4 — Pre-cutover items shipped (Days 9-12, ~3 AI-days, parallel)

- [ ] [AGENT] P0. **4.A Architecture clean-ups on cutover path.** Each PRE_CUTOVER item gets shipped as a separate commit (or folded into an active plan if scope-aligned).
- [ ] [AGENT] P0. **4.B Per-area success criterion.** Each area has a pre-cutover-readiness assertion; QG green per affected repo.

**Full-execution criterion**: every PRE_CUTOVER row flipped `[x]`; affected repos QG + remote CI green.

## Phase 5 — Post-cutover items filed as plans (Day 12, ~1 AI-day)

- [ ] [AGENT] P0. **5.A Per-POST_CUTOVER row → plan or issue doc.** Every POST_CUTOVER recommendation gets a `plans/active/issues/<slug>_<post_cutover_date>.md` issue doc OR is folded into an existing plan with a `**MIGRATED FROM:** codex_vs_citadel_audit_2026_05_10` provenance line. No orphan recommendations.

**Full-execution criterion**: count(POST_CUTOVER rows) == count(filed-issue-docs OR migrated-plan-todos); zero orphans.

## Phase 6 — Audit sign-off doc (Day 13, ~0.5 AI-day)

- [ ] [AGENT] P0. **6.A `plans/active/issues/codex_vs_citadel_audit_signoff_2026_05_22.md`.** Aggregate findings, per-area summary, disposition counts, links to per-area issue docs + immediate/pre-cutover commit shas + post-cutover plan filings.
- [ ] [AGENT] P0. **6.B Operator sign-off.** Operator reviews + approves; doc status flips to `signed-off`.

**Full-execution criterion**: sign-off doc exists; operator approved; counts add up (immediate + pre-cutover + post-cutover == total).

## Phase 7 — Cutover gate (Day 13, ~0.25 AI-day)

- [ ] [AGENT] P0. **7.A Master plan row.** Group A item: "Codex vs Citadel audit signed off; pre-cutover items shipped."

**Full-execution criterion**: master plan row green.

## Cross-plan coordination

- `simulation_scenarios_topology_price_shocks_2026_05_09` — codex docs for scenario architecture audited as part of this pass.
- All 8 sibling plans spawned 2026-05-10 — every plan's codex SSOTs included in the audit per its area.

## Deferred work after 2026-05-10 plan-creation session

| Item                                            | Status              | Successor / blocker                                              |
| ----------------------------------------------- | ------------------- | ---------------------------------------------------------------- |
| Cross-asset_group reshuffles (large refactors)  | POST_CUTOVER        | Filed per Phase 5; named successor plans                         |
| HFT-specific optimizations                      | OUT_OF_SCOPE        | Non-HFT framing; not revisited                                   |

## Done definition

1. ✅ Phases 0-7 every checkbox flipped with evidence.
2. ✅ 12 per-area audit issue docs shipped.
3. ✅ Every IMMEDIATE + PRE_CUTOVER row shipped; every POST_CUTOVER row filed.
4. ✅ Sign-off doc operator-approved.
5. ✅ Master plan row green.

## Audit findings

(12 sub-agent issue docs link here.)

## DONE block

(Filled at completion.)
