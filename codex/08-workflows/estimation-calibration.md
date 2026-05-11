# Estimation Calibration — Per-Class Multipliers + Retrospective Ledger

> SSOT for time-estimate calibration in this workspace. Plan authors apply the multiplier from the class table; the
> retrospective ledger ([estimation-retrospective-ledger.md](estimation-retrospective-ledger.md)) feeds back
> actuals so calibration self-corrects over time.
>
> Codified 2026-05-11 after ~7 days of empirical evidence showed Claude's training-intuition estimates running
> 1.5-3× conservative for this workspace's parallel-agent pattern, causing operators to undersell scope into
> daily work-splits and leave throughput on the floor.

---

## Why this exists

**The problem**: Conservative estimates → undersold scope in daily work-splits → real throughput exceeds plan →
unscheduled work piles up as technical debt → next cycle's plans bake in the same conservatism.

**The empirical baseline** (2026-05-04 → 2026-05-11, 7 days):

- **1751 commits** across 8 active repos (`unified-trading-pm`, `unified-api-contracts`, `unified-trading-library`,
  `market-tick-data-service`, `market-data-processing-service`, `instruments-service`, `features-service`,
  `deployment-service`) on `live-defi-rollout` — ~250 commits/day workspace-wide.
- **2026-05-11 work-split**: `~15 AI-days` (Ikenna, 4 slots) + `~21 AI-days` (Harsh, 5 slots) = `~36 AI-days /
  4-day cycle = ~9 AI-days/day` *scheduled* burn. Per CLAUDE.md the load-balancing *ceiling* is `~50 AI-days/day per
  side`, so scheduled scope is roughly 1/5 of theoretical capacity.
- **Plan-vs-actual spot checks** (see [retrospective ledger](estimation-retrospective-ledger.md)): multiple plans
  estimated at 2-6 AI-days landed in 1 session with sub-agent fan-out, ratios ranging 0.17×-0.50× of nominal.

The gap is real and systematic, not noise.

---

## The multipliers

Apply to your **training-intuition baseline**: "how long would this take a single Claude session, working serially,
without sub-agent fan-out, without parallel slots."

| Class | Multiplier | Typical work | Why this multiplier |
|---|---|---|---|
| `refactor` | **0.4×** | Mechanical changes across N files with high context share (rename a symbol; migrate to a new helper; lint-sweep) | Sub-agent fan-out + grep-then-edit compresses sharply; little design exploration |
| `design` | **0.6×** | New artefact: plan, codex doc, UAC schema, helper module | One author per artefact; sub-agents help with sections + tests + audits |
| `infra` | **0.8×** | Real-infra ops: VM launch + verify, backfill to natural completion, cloud migration with drift verification | Verification + waiting on cloud + event-stream watch is wall-clock-bound |
| `brand-new` | **1.0×** | Novel feature with no template (first VM launcher of a new shape; first contract of a new domain) | Genuinely novel design exploration; no compression to extract |
| `research` | **1.2×** | Scope genuinely unknown upfront; investigation-heavy ("what's broken in X"; "is Y feasible") | Should expand on uncertainty discoveries, not contract |

**When in doubt, pick the higher class.** Optimism is the failure mode this framework corrects, not pessimism.

---

## When the multipliers don't apply

Calibration assumes the work pattern that's been measured. Stop applying the multiplier and use the baseline (or
higher) when:

1. **Serial-only by construction** — wallet-key approval, kill-switch arming, force-push, version 1.0.0 graduation
   (the human-only hard-stops listed under "Plans Run To Actual Completion").
2. **Single-tab work** — no sub-agent fan-out planned + no parallel slot context to lean on.
3. **External-dependency-bound** — waiting on a counterparty (CEFFU custody onboarding, Copper integration approval,
   exchange API key issuance). Calendar time, not work time.
4. **First touch on a brand-new domain** — first VM launcher in a new asset_group, first connector to a new venue.
   Treat as `brand-new` class until 2-3 retrospective entries calibrate it.

---

## Frontmatter convention

Every active plan written **after 2026-05-11** adds three new frontmatter fields:

```yaml
estimate_class: refactor | design | infra | brand-new | research
estimate_baseline_ai_days: <pre-calibration estimate as integer or range, e.g. 6 or "6-8">
estimate_calibrated_ai_days: <baseline × multiplier, e.g. 2.4 or "2.4-3.2">
```

For **multi-class plans** (e.g. a master plan with design + infra + refactor phases), use the dominant class for the
plan-level field and override per-phase inline:

```markdown
## Phase 4 — Backfill all DeFi history into AWS S3

**Class**: infra. **Baseline**: 8 AI-days. **Calibrated**: 6.4 AI-days (8 × 0.8).
```

For **legacy plans** (created before 2026-05-11), retrofit the frontmatter on next substantive update — don't sweep
all of them at once (collision risk with their owner agents).

---

## Retrospective ledger workflow

Every plan archive (per `Plan Archival` HARD RULE in CLAUDE.md) adds a row to
[estimation-retrospective-ledger.md](estimation-retrospective-ledger.md):

| Plan | Class | Calibrated estimate | Actual | Ratio | Notes |

**Actual** = wall-clock AI-days from first commit on the plan to the last logical-unit commit (checkbox-flip or
archive-commit), counted in continuous working days, not calendar.

**Ratio** = actual / calibrated. Above 1.0 means we underestimated even after calibration; below 1.0 means we still
have room to compress the multiplier.

**Recalibration**: when 8+ rows land for a given class with median ratio drifting more than ±20% from 1.0, propose
an updated multiplier in a `docs(codex):` PR + this doc.

---

## How to use the multiplier in a plan

1. Write the **baseline** estimate from your training intuition (do this BEFORE looking at the multiplier table —
   anchoring bias).
2. Pick the class. If split across classes, list each phase's class.
3. Multiply. Stamp both numbers in the frontmatter (so a future reader can audit your calibration).
4. Use the **calibrated** number in any work-split scope total, daily-burn projection, or operator status update.
5. On plan archive, add a retrospective ledger row.

---

## Composes with

- **Citadel-Grade Planning Standards** (CLAUDE.md): calibrated estimates are an input to phase-level success criteria.
- **Daily Work-Split Process** (CLAUDE.md): work-split scope totals MUST use calibrated AI-days, not baseline.
- **Plans Run To Actual Completion** (CLAUDE.md): "Code-shipped is NOT operationally-shipped" — the `infra`
  multiplier already accounts for the verification tail; don't re-discount it.
- **Capture Discoveries As Plan Todos Immediately** (CLAUDE.md): if scope expands mid-plan and you need to add
  todos, recalibrate the new todos with the same multiplier.
- **Plan Archival** (CLAUDE.md): retrospective ledger row is part of the archive logical unit.

---

## Anti-patterns

- **Multiplying a multiplied number** — the calibrated number is the final estimate; don't apply 0.5× to it again.
- **Picking a low class to make scope look bigger** — the goal is honest scope sizing, not gaming the work-split.
- **Skipping the retrospective ledger row** — calibration only self-corrects if actuals get logged.
- **Sweeping every active plan to retrofit frontmatter** — owner agents update on next touch; mass-sweeps collide.
