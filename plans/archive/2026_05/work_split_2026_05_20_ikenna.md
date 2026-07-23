---
doc_type: plan
title: Ikenna work-split 2026-05-20 — Phase -2 + -1 + background QG sweep on slots 9-11
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    agent-orchestrator,
    execution-service,
    features-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/epics/mtds_mdps_master.md,
    issues/strategy_archetype_logic_audit_2026_05_20.md,
    /plans/archive/2026_05/strategy_repo_consolidation_2026_05_19.md,
    /plans/archive/2026_05/ml_repo_consolidation_2026_05_19.md,
    issues/mega_audit_and_plan_beefup_progression_2026_05_20.md,
  ]
created: "2026-05-20"
locked_by: live-defi-rollout
locked_since: 2026-05-20
supersedes: work_split_2026_05_19_ikenna.md
parent_epic: orchestrator_master
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
---

> **ARCHIVED 2026-05-21** — All AI-executable items complete. Deferred items (QG Cluster C, features-sports Track E)
> scoped to named successor plans. Migrated to `plans/archive/2026_05/`.

# Ikenna work-split 2026-05-20

> **Supersedes** `work_split_2026_05_19_ikenna.md` — slot 6/7/9 freeze gates remain; slots 9/10/11 re-themed to QG green
> background sweep on the Ikenna AWS VM while Harsh is offline (India timezone). Master plan `mtds_mdps_master.md` is
> the canonical ordering layer.

## Slot stack — local laptop (slots 1-8) + AWS VM background (slots 9-11)

| Slot   | Host            | Theme                                                                                                 | Phase ownership (per master coordinator) | Status                                                                                                                                                                      |
| ------ | --------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1      | Local           | Main orchestrator + ping audit + cron monitor                                                         | Phase 0, 2, 8                            | Continuous                                                                                                                                                                  |
| 2      | Local           | code_freeze §2.6 + R19 UAC import surface                                                             | Phase 1, 3, 4, 10                        | KEEP                                                                                                                                                                        |
| 3      | Local           | code_freeze §2.0-2.5 + batch_live_symmetry T1-3                                                       | Phase 1, 3, 4, 13                        | KEEP                                                                                                                                                                        |
| 4      | Local           | api_keys + defi_recursive_borrow + AWS migration owner                                                | Phase 5, 12 (live adapter)               | KEEP                                                                                                                                                                        |
| 5      | Local           | writegate + v8 backfill + writer SSOT + label-flip + dep-prop QG                                      | Phase 6, 7, 10, 14                       | KEEP (the v8-backfill anchor)                                                                                                                                               |
| **6**  | Local           | 🔴 FROZEN (was deployment_ui_lifecycle_tabs) — reassigned to A3 DeFi MISSING_EXPECTED remediation     | Phase 9 (denominator UI post-unfreeze)   | FROZEN                                                                                                                                                                      |
| **7**  | Local           | 🔴 FROZEN (was simulation_scenarios + defi_master P2-3) — reassigned to A3 Sports + A2 off-season gap | Resumes post-unfreeze                    | FROZEN                                                                                                                                                                      |
| 8      | Local           | defi_catalogue close + R-NEW-6 detector candidate                                                     | Phase 14                                 | KEEP                                                                                                                                                                        |
| **9**  | **✅ DONE**     | **QG GREEN SWEEP — Cluster A: instruments-service + UAC + UTL**                                       | Phase -1 (workspace QG prereq)           | ✅ UAC (already green); ✅ UTL@f63eb8e2 (9 violations fixed + pm@424b4319 checker bug); ✅ IS (already green, no changes needed)                                            |
| **10** | **🟢 DONE**     | **QG GREEN SWEEP — Cluster B: MTDS + features-service + MDPS**                                        | Phase -1                                 | ✅ MTDS@5c1631d green (no fixes by slot-10); ✅ features-service@31c38543 green (codex+imports+upload-API fixes); ✅ MDPS@e3441a9 green (within-tolerance, no fixes needed) |
| **11** | **🟡 PARALLEL** | **QG GREEN SWEEP — Cluster C: strategy-service + execution-service + ml-service**                     | Phase -1                                 | NEW theme tonight                                                                                                                                                           |

## Slot 9-11 dispatch — QG green sweep (Phase -1 owner)

> **Why background**: Harsh-side normally owns workspace-wide QG green per CLAUDE.md HARD RULE "Quality Gates Are A
> Merge Prerequisite" + the master coordinator Phase -1. Harsh is offline (India timezone) — slots 9-11 on Ikenna VM (or
> local if VM provisioning slips tonight) take ownership of QG sweep so Phase -1 can land GREEN without waiting for
> Harsh's day.
>
> When Harsh's primary backend wakes up (his laptop online again), Harsh-side slots resume QG ownership; slots 9-11 hand
> off via git rebase (Harsh absorbs the QG fixes from `live-defi-rollout`).

### Common boot steps (apply to slots 9, 10, 11)

```bash
# 1. Reset the slot worktree to clean LDR HEAD
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot <N>

# 2. Boot context: read CLAUDE.md HARD RULE + master coordinator Phase -1
cat unified-trading-pm/cursor-configs/CLAUDE.md   # § "Quality Gates Are A Merge Prerequisite"
cat unified-trading-pm/plans/active/mtds_mdps_master.md   # § "Phase -1: Workspace-wide QG green"

# 3. For EACH repo in the cluster, run:
cd <repo> && bash scripts/quality-gates.sh
# Capture failures → fix → re-run until exit 0 → commit + push to live-defi-rollout
```

### Slot 9 — Cluster A: instruments-service + UAC + UTL

**Spawn prompt** (paste at top of agent's first message):

```
You are Ikenna slot 9 background QG sweep — Cluster A. Boot via per-tab-worktrees
codex doc + master coordinator Phase -1.

Repos (in this order):
1. unified-api-contracts (UAC) — `cd unified-api-contracts && bash scripts/quality-gates.sh`
2. unified-trading-library (UTL) — `cd unified-trading-library && bash scripts/quality-gates.sh`
3. instruments-service — `cd instruments-service && bash scripts/quality-gates.sh`

For each repo: fix every QG failure (ruff / basedpyright / pytest / codex). Commit per
shippable unit; push to live-defi-rollout. Avoid touching foreign-dirty files. Re-run
until exit 0. When all 3 repos GREEN, post DONE ping to ikenna_orchestrator/pings/slot_9.md
+ heartbeat /done via dashboard.

DO NOT touch strategy-service or strategy_service/* archetype LOGIC during this work —
strategy-LOGIC freeze gate active until operator's Opus-1M strategy_archetype_logic_audit
lands tonight. Cluster A doesn't include strategy-service anyway, but flag if any QG
fix tempts you to edit strategy-side code (e.g. UAC schema used by strategy).

Plan-of-record: plans/active/work_split_2026_05_20_ikenna.md § Slot 9.
```

### Slot 10 — Cluster B: MTDS + features-service + MDPS

**Spawn prompt**:

```
You are Ikenna slot 10 background QG sweep — Cluster B. Boot via per-tab-worktrees
codex doc + master coordinator Phase -1.

Repos (in this order):
1. market-tick-data-service (MTDS) — `cd market-tick-data-service && bash scripts/quality-gates.sh`
2. features-service — `cd features-service && bash scripts/quality-gates.sh`
3. market-data-processing-service (MDPS) — `cd market-data-processing-service && bash scripts/quality-gates.sh`

For each repo: fix every QG failure. Commit per shippable unit; push to live-defi-rollout.
Cross-coordinate with slot 9 on UAC import drift (if you touch UAC, ping slot 9). Re-run
until exit 0.

DO NOT edit strategy-service or strategy archetype LOGIC. Strategy-LOGIC freeze gate active.

Plan-of-record: plans/active/work_split_2026_05_20_ikenna.md § Slot 10.
```

### Slot 11 — Cluster C: strategy-service + execution-service + ml-service

**Spawn prompt**:

```
You are Ikenna slot 11 background QG sweep — Cluster C. Boot via per-tab-worktrees
codex doc + master coordinator Phase -1.

Repos (in this order):
1. strategy-service — `cd strategy-service && bash scripts/quality-gates.sh`
2. execution-service — `cd execution-service && bash scripts/quality-gates.sh`
3. ml-service — `cd ml-service && bash scripts/quality-gates.sh`

⚠️ STRATEGY-LOGIC FREEZE GATE ACTIVE per master coordinator Phase 6 § "round 6":
- ONLY fix SURFACE QG failures (lint / typecheck / docstring / unused-import).
- DO NOT touch `strategy_service/engine/strategies/v2/` archetype logic.
- DO NOT touch `strategy_service/engine/allocator/` allocation logic.
- DO NOT touch collateral / liquidation / cross-venue-transfer / venue-restriction code.
- DO NOT touch deployment topology dynamic-config code.

If a QG failure would require editing any of the above LOGIC surfaces, stop + ping
slot-1 main to escalate to operator's tonight's strategy_archetype_logic_audit.

Otherwise: fix surface failures; commit per shippable unit; push to LDR. Re-run until
exit 0 on all 3 repos.

Plan-of-record: plans/active/work_split_2026_05_20_ikenna.md § Slot 11.
```

## Coordination

### Comms model

- **Status pings**: HTTP `/heartbeat` + `/progress` + `/done` + `/blocked` to dashboard (no git for status). Backend:
  Ikenna AWS VM if running there; otherwise local.
- **Code changes**: standard git → `live-defi-rollout`. Per-shippable-unit commit cadence (CLAUDE.md HARD RULE).
- **Cross-slot coord**: `ikenna_orchestrator/pings/slot_<N>.md` for intra-side signalling (each agent posts blocker /
  question / DONE).
- **Cross-side**: `plans/active/_agent_pings.md` for Ikenna ↔ Harsh signalling.

### Local vs VM split decision (operator picks tonight)

**Option A — Slots 9-11 on local laptop** (alongside 1-8):

- Pro: zero provisioning; ping files + worktrees already exist locally.
- Con: laptop must stay on; resource contention with 1-8.

**Option B — Slots 9-11 on Ikenna AWS VM** (true background):

- Pro: laptop can close; VM keeps working overnight.
- Con: ~10min provisioning step (SSH to VM, run `setup-tab-worktrees.sh --add-slot 9/10/11` on the VM's worktree set).

**Recommendation**: Option B for tonight (Harsh's offline window = perfect chance to verify VM workers). Codex covers
the setup at `/codex/05-infrastructure/agent-orchestrator-deploy.md § EC2 VM deploy`.

### Hand-off when Harsh wakes up

- Slot 9-11 post DONE ping → dashboard.
- Harsh's primary backend (laptop) wakes → operator picks up slots from his side OR keeps Ikenna-side ownership for one
  more day.
- Git LDR is the merge point — Harsh's slots see the QG-green commits from slots 9-11 automatically on next rebase.

## Phase -1 GREEN criterion (slots 9-11 done)

For each repo in clusters A+B+C:

- `bash scripts/quality-gates.sh` exit 0
- No `# type: ignore`, no fallback imports, no banned patterns
- Commit pushed to `live-defi-rollout`
- DONE ping to slot's per-slot ping file

When 9 repos GREEN (3 per slot × 3 slots) → Phase -1 lands → master coordinator unlocks Phase 0 + Phase 1.
