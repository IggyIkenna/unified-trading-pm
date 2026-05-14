---
title: Harsh-side thematic slot clusters — stable per-slot specialization map
type: orchestration-spec
status: draft
created: 2026-05-14
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

# Harsh-side Thematic Slot Clusters

> **Purpose**: stable per-slot specialization that persists across cycles. Each slot has a primary repo set, theme tags, and natural reserve work. Daily continuation prompts (`plans/active/continuation_prompts_harsh_<date>.md`) draw items from these clusters.
>
> **Why this exists**: shift Harsh-side orchestration from "main dispatches every DONE" → "slot self-pivots through its thematic queue" (Ikenna's Model A pattern). Reduces operator-main polling by ~70%.
>
> **Mirror on Ikenna side**: `ikenna_orchestrator/LEDGER.md` § "Today's slot assignments" (he keeps themes in the LEDGER table; we factor it out here since Harsh themes are more stable across cycles).

---

## How to use this doc

**For main orchestrator (start of cycle)**:
1. Read this doc for slot ↔ theme mapping.
2. Pull current BACKLOG items into per-slot queues based on repo overlap (each item names its repos).
3. Write today's `continuation_prompts_harsh_<date>.md` — paste 3-5 items per slot in priority order + reserve list.
4. Ping each slot ONCE at session start: "your continuation prompt is at <doc>:Slot N — execute in order, self-pivot, ping main only on BLOCKED or cross-side."

**For spawned slot agents**:
1. Read your slot section in this doc — confirm repo ownership.
2. Read `continuation_prompts_harsh_<date>.md` § "Slot N" — your prioritized queue + reserve.
3. Ship items in order. After each item DONE + pushed: ping DONE with SHA, then **immediately start next item without waiting for main dispatch**.
4. Only ping main on: BLOCKED (genuine gap), cross-side coordination needed, BIG finding (data correctness / multi-repo).
5. After all queue items DONE, pull from "Reserve" list in your section.

---

## Slot 2 — Deployment Infra & Lint Sweep

**Primary repos** (owned): `deployment-service` · `alerting-service` · `ml-training-service`
**Touch repos** (occasional): `deployment-ui` · `unified-trading-pm` (plan flips only)

**Themes**:
- VM launcher infra (`scripts/vm/launch-*.sh`) + singleton-lock + zombie-watchdog `VM_PREFIX_TO_BUCKET` registration
- Cluster B lint sweeps (C901 / N802 / B008) across owned repos
- Phase 0 cleanup absorption when other slots are saturated
- Shellcheck + bash syntax for deployment scripts

**Reserve queue** (pull when primary queue empty):
- `deployment-service` shellcheck sweep on any new launcher
- Codex audit for deployment-and-qg-strategy.md after Phase 3 changes
- VM_PREFIX_TO_BUCKET registration for any new VM types operator adds

**Coordination notes**:
- `deployment-service` overlaps with slot 7 (Phase 4 cron VM infra) and slot 8 (Phase 3 ratchet template) — coordinate file-level
- ml-training-service is largely yours; rare overlap with slot 4 (test failures)

---

## Slot 3 — Strategy Service & DeFi Paper Backtests

**Primary repos** (owned): `strategy-service` · `e2e-testing`
**Touch repos**: `unified-api-contracts` (archetype config) · `unified-trading-pm` · `features-service` (rare — feature-side strategy code)

**Themes**:
- Archetype validation coverage (per-archetype factory + calc branches; B-010 pattern)
- DeFi paper backtests — APD archetype (B-016) + future paper-runs
- V2BatchHarness + colocated_engine work
- Strategy-side Phase 8 coverage (factory paths, archetype resolvers, alpha smoke)
- Phase 1 cross-side prereq checks before paper launches

**Reserve queue**:
- strategy-service execution alpha smoke tests
- batch_live symmetry items that touch strategy code
- Phase 3 ratchet test fixtures for strategy-service

**Coordination notes**:
- Pair with slot 9 on shared cross-side ping content (DeFi backtests; both file similar prereq checks)
- strategy-service overlaps with slot 4 (general test failures) — coordinate

---

## Slot 4 — Test Failures Absorption & Service Lifecycle Coverage

**Primary repos** (owned): `features-service` · `ml-inference-service` · `instruments-service` · `market-tick-data-service` (occasional, slot 9 owns it primarily)
**Touch repos**: `unified-trading-library` (test utils)

**Themes**:
- Phase 0 test failure absorption (Cluster D pattern — when other slots are silent on assigned cleanup)
- ServiceBootstrap lifecycle coverage (B-006 pattern — STARTED/STOPPED/FAILED across services)
- General "diagnose-first" test failures across owned repos
- Coverage gaps on shared infrastructure

**Reserve queue**:
- features-service codex audit / Phase 6 emission policy fixes
- ml-inference-service publisher work
- Cross-repo test diagnostics (read failing test + code-under-test, fix the right side)

**Coordination notes**:
- Multi-repo theme: coordinate with slot 6 on execution-service touches; slot 9 on MTDS; slot 5 on risk
- B-006-pattern (lifecycle coverage) is a recurring item — runs every Phase 8 cycle

---

## Slot 5 — Risk Engine + Execution Alpha + Kill-Switch

**Primary repos** (owned): `risk-and-exposure-service` · `execution-service` · `pnl-attribution-service`
**Touch repos**: `deployment-api` (Phase 1 env-locking; occasional)

**Themes**:
- KILL_SWITCH_ACTIVATED + CIRCUIT_BREAKER_OPEN coverage (B-009 pattern)
- Risk event paths + emission policy (Phase 6.7 risk_state)
- Execution alpha measurement + matching engine coverage
- PnL attribution coverage (C901 sweeps, archetype buckets)
- Cluster F (deployment-service) absorption when needed
- Phase 3 TradFi migration work (instruments-service occasional)

**Reserve queue**:
- pnl-attribution-service archetype bucket extensions
- risk-and-exposure-service synthetic-fire test suite
- execution-service DeFi error classification coverage

**Coordination notes**:
- execution-service overlaps with slot 6 (custody/signing) + slot 4 (lifecycle) — coordinate file-level
- Phase 6.7 emission policy items overlap with slot 8 (UTL emission publisher)

---

## Slot 6 — Custody, Signing, UTL Coverage, Codex Audits

**Primary repos** (owned): `execution-service` (custody half) · `unified-trading-library` (helpers) · `unified-api-contracts` (occasional)
**Touch repos**: `codex/` doc updates · `pnl-attribution-service` (occasional Cluster B)

**Themes**:
- Custody + wallet signing surface coverage (B-012 pattern)
- UAC ×→x and similar UAC-side cleanup (Cluster A)
- Post-plan-phase codex audit (HARD RULE) — verify codex/ docs reflect shipped contracts
- UTL helper coverage (legacy_reason_classifier, signing helpers, manifest helpers)
- Phase 1 freeze-gate readiness audits (read-only verification)

**Reserve queue**:
- codex/04-architecture/ doc currency for any new architectural shifts
- UTL test coverage for new helpers (sports classifier, refdata cadence, etc.)
- DeFi error code classification taxonomy updates

**Coordination notes**:
- Most proactive slot — often self-initiates Cluster A/B cleanup when waiting
- execution-service overlaps with slot 5 (kill switch) + slot 4 (lifecycle) — coordinate file-level
- UAC overlaps with Ikenna side workspace-shared work

---

## Slot 7 — Deployment API + UI + Phase 4 Cron Infra

**Primary repos** (owned): `deployment-api` · `deployment-ui` · `unified-trading-pm` (scripts/qg_snapshot)
**Touch repos**: `deployment-service` (cron VM launchers) · `client-reporting-api` (occasional)

**Themes**:
- Phase 1 env-locking (B-001/B-002 pattern — tarball-block, env-lock UI)
- Phase 2 deploy-ready tracking (B-013 endpoint + UI panel)
- Phase 4 QG snapshot writer + cron VM (B-018 pattern — write-side complement)
- Deploy-readiness UI work + per-repo readiness panels
- Phase 4.B downstream items (alerting hooks, snapshot consumers)

**Reserve queue**:
- client-reporting-api coverage extensions
- deployment-ui vitest fixes
- Cloud Scheduler trigger management
- SHARD_AXIS_MATRIX drift if not absorbed by Ikenna slot 8

**Coordination notes**:
- deployment-api/ui paired — usually slot 7 owns both halves (read endpoint + UI panel)
- deployment-service overlaps with slot 2 (VM infra) — coordinate launcher file-level

---

## Slot 8 — UTL Coverage + QG Ratchet Rollout + Meta-QG

**Primary repos** (owned): `unified-trading-library` (manifest + emission publisher) · `deployment-service` (base-service.sh template) · all service repos (rollout via propagation script)
**Touch repos**: `unified-trading-pm` (scripts/quality_gates, scripts/propagation)

**Themes**:
- UTL manifest writer + emission publisher coverage (B-007/B-008 pattern)
- Phase 3 QG ratchet template work (base-service.sh STEP edits)
- QG STEP rollouts (5.74+ pattern)
- Batch_live symmetry meta-work (L2/L7 sweeps, STEP 5.77 pattern)
- Cross-repo lint + symmetry validation

**Reserve queue**:
- codex/06-coding-standards/quality-gates.md updates
- QG STEP additions for new patterns (e.g., new emission policy gates)
- Template-side ratchet enables that need workspace-wide rollout

**Coordination notes**:
- Owns the cross-cutting QG template (base-service.sh) — every service repo consumes it
- DO NOT enable new STEPs in template until all consumer repos pass with them (Path A vs Path B from B-014 brief)
- UTL overlaps with slot 4 (test utils) + slot 6 (helpers) — coordinate file-level

---

## Slot 9 — MTDS, PBM, DeFi Carry Backtest, Peripheral Pipeline

**Primary repos** (owned): `market-tick-data-service` · `position-balance-monitor-service` · `e2e-testing` (DeFi carry half)
**Touch repos**: `features-service` (peripheral scripts) · `instruments-service` (peripheral migrations)

**Themes**:
- MTDS handler maintenance + UAC facade migrations
- PBM test failures + coverage
- DeFi carry_staked_basis paper backtests (B-015 pattern)
- Peripheral pipeline_mode kwarg sweeps (cross-repo)
- MDPS work (when not absorbed by other slots)

**Reserve queue**:
- MTDS handler additions (Solana RPC, Pyth, new venues)
- PBM Phase 8 coverage extensions
- features-service sports peripheral scripts
- DeFi data-pipeline gap reporting (catches data-correctness issues)

**Coordination notes**:
- Pair with slot 3 on DeFi paper backtests (shared cross-side prereq pattern)
- MTDS overlaps with slot 4 (test failures) — usually slot 9 owns MTDS specifically
- Most likely slot to surface data-correctness BLOCKERs (B-015 BLOCKED pattern)

---

## Slot 1 — Main Orchestrator (your role)

**Primary repos**: `unified-trading-pm` (orchestration docs only)

**Themes**:
- Master plan refresh + inventory regeneration (`regenerate_active_plan_inventory.py`)
- Cross-side ping triage (Ikenna ↔ Harsh)
- Per-slot continuation prompt curation (start of cycle)
- Ping ledger triage (BLOCKED → answer, BIG finding → surface to operator)
- LEDGER row updates on STARTED/DONE (mechanical — most can be auto-polled)
- EOD scoreboards

**NOT your role anymore (after Lever 1+2 adoption)**:
- ❌ Per-DONE next-task dispatch (slots self-pivot through their queue)
- ❌ Mechanical LEDGER flips (auto-poll script handles)
- ❌ Daily theme reassignment (themes are stable per this doc)

**Polling cadence**: ~5-10 min during operator active (was ~1 min). Auto-poll handles mechanical work between manual polls.

---

## Cross-slot coordination matrix (collision-risk awareness)

| Repo | Primary slots | Coordination rule |
|---|---|---|
| execution-service | 4 (lifecycle), 5 (kill switch), 6 (custody) | file-level non-overlap; ping cross-slot if touching shared file |
| deployment-service | 2 (VM infra), 7 (cron), 8 (template) | distinct directories; template work always slot 8 |
| unified-trading-library | 4 (test utils), 6 (helpers), 8 (manifest/emission) | distinct modules; coverage tests serialise |
| unified-api-contracts | 6 (Cluster A), Ikenna side primary | Harsh slot 6 only on explicit asks; check cross-side ledger first |
| features-service | 4 (tests), 9 (peripheral) | usually distinct concerns |
| market-tick-data-service | 4 (tests), 9 (handlers/peripheral) | slot 9 owns; slot 4 absorbs Cluster D when needed |
| deployment-api / deployment-ui | 7 (primary) | almost always paired in slot 7 |
| pnl-attribution-service | 5 (primary), 6 (occasional Cluster B) | coordinate Cluster B sweeps via cross-slot ping |

---

## Cycle cadence

**Cycle length**: 4 days (mirroring Ikenna).
**Day-1**: Start with continuation prompts populated from current BACKLOG. Slots ship their queue.
**Day-2**: Slots continue self-pivot. Main reviews EOD scoreboards from Day-1 + populates Day-2 scope extension if a slot closed early.
**Day-3**: Same.
**Day-4**: EOD cycle close — all slots ship final scoreboard. Main writes cycle-close summary.

**Boundary marker**: end of Day-4 = cycle close. Archive that cycle's `continuation_prompts_harsh_<date>.md` to `plans/archive/`. Start next cycle Day-1.

---

## Adoption checklist (when you adopt this model)

- [ ] Operator approves this thematic clusters doc (review for accuracy vs actual slot capabilities)
- [ ] Operator approves the continuation_prompts template format
- [ ] Auto-poll script (`scripts/agents/harsh_auto_poll.sh`) tested + cron-scheduled
- [ ] Tomorrow morning: main writes Day-1 continuation_prompts from current BACKLOG + this doc's themes
- [ ] All 8 slot agents read this doc + their continuation prompt section ONCE at session start
- [ ] Operator validates pattern works after Day-1 (slot self-pivot reduces main interruptions?)

---

## Anti-patterns to avoid

- ❌ **Reassigning slots to off-theme work daily** — defeats the stability gain
- ❌ **Main writing per-DONE briefs** — let slots self-pivot
- ❌ **Continuation prompts with single item** — defeats the multi-item gain; always 3-5 items
- ❌ **Slots reading BACKLOG directly** — main still curates continuation_prompts (BACKLOG → per-slot queue mapping). Slots read continuation_prompts only.
- ❌ **Skipping the auto-poll** — manual polling is the operator-attention sink we're solving

---

## Versioning

This doc evolves as slot specializations stabilize. Updates require operator approval. Cycle-to-cycle drift is expected (~10% scope shift); large theme reassignment requires explicit operator decision + this doc update.
