---
scope: [engineer, admin]
---

# Estimation Calibration — Per-Class Multipliers + Retrospective Ledger

> SSOT for time-estimate calibration in this workspace. Plan authors apply the multiplier from the class table; the
> retrospective ledger ([estimation-retrospective-ledger.md](estimation-retrospective-ledger.md)) feeds back actuals so
> calibration self-corrects over time.
>
> Codified 2026-05-11 after ~7 days of empirical evidence showed Claude's training-intuition estimates running 1.5-3×
> conservative for this workspace's parallel-agent pattern, causing operators to undersell scope into daily work-splits
> and leave throughput on the floor.

---

## Why this exists

**The problem**: Conservative estimates → undersold scope in daily work-splits → real throughput exceeds plan →
unscheduled work piles up as technical debt → next cycle's plans bake in the same conservatism.

**The empirical baseline** (2026-05-04 → 2026-05-11, 7 days):

- **1751 commits** across 8 active repos (`unified-trading-pm`, `unified-api-contracts`, `unified-trading-library`,
  `market-tick-data-service`, `market-data-processing-service`, `instruments-service`, `features-service`,
  `deployment-service`) on `live-defi-rollout` — ~250 commits/day workspace-wide.
- **2026-05-11 work-split**: `~15 AI-days` (Ikenna, 4 slots) + `~21 AI-days` (Harsh, 5 slots) =
  `~36 AI-days / 4-day cycle = ~9 AI-days/day` _scheduled_ burn (the BUDGET, not throughput). Measured 2026-05-11
  _delivered_ throughput = ~130 cal AI-days/day workspace (~65/side, commit-derived). Per CLAUDE.md the load-balancing
  _ceiling_ is `~80-100 AI-days/day per side`, so scheduled scope is roughly 1/5 of theoretical capacity.
- **Plan-vs-actual spot checks** (see [retrospective ledger](estimation-retrospective-ledger.md)): multiple plans
  estimated at 2-6 AI-days landed in 1 session with sub-agent fan-out, ratios ranging 0.17×-0.50× of nominal.

The gap is real and systematic, not noise.

---

## The multipliers

Apply to your **training-intuition baseline**: "how long would this take a single Claude session, working serially,
without sub-agent fan-out, without parallel slots."

| Class       | Multiplier | Typical work                                                                                                     | Why this multiplier                                                              |
| ----------- | ---------- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `refactor`  | **0.4×**   | Mechanical changes across N files with high context share (rename a symbol; migrate to a new helper; lint-sweep) | Sub-agent fan-out + grep-then-edit compresses sharply; little design exploration |
| `design`    | **0.6×**   | New artefact: plan, codex doc, UAC schema, helper module                                                         | One author per artefact; sub-agents help with sections + tests + audits          |
| `infra`     | **0.8×**   | Real-infra ops: VM launch + verify, backfill to natural completion, cloud migration with drift verification      | Verification + waiting on cloud + event-stream watch is wall-clock-bound         |
| `brand-new` | **1.0×**   | Novel feature with no template (first VM launcher of a new shape; first contract of a new domain)                | Genuinely novel design exploration; no compression to extract                    |
| `research`  | **1.2×**   | Scope genuinely unknown upfront; investigation-heavy ("what's broken in X"; "is Y feasible")                     | Should expand on uncertainty discoveries, not contract                           |

**When in doubt, pick the higher class.** Optimism is the failure mode this framework corrects, not pessimism.

---

## Parallelism axis — AI-day vs wall-clock

The class multipliers above measure **intra-slot compression**: how much one slot's effort shrinks when sub-agent
fan-out + workspace-context-share + per-tab-worktree isolation kick in. The seed retrospective entries are all
single-slot-with-fan-out observations.

The workspace also runs **multi-slot parallelism**: each operator (Ikenna + Harsh) has up to 8 concurrent slots
(`tab/<operator>/<N>` worktrees), so up to 16 slots workspace-wide can work on different phases of the same plan or on
different plans simultaneously. This is a **wall-clock divisor** orthogonal to class multipliers:

```
calibrated_ai_days   = baseline_ai_days × class_multiplier      (intra-slot effort, what we already track)
wall_clock_days      = calibrated_ai_days / effective_concurrent_slots   (when plan parallelises)
```

`effective_concurrent_slots` is bounded by the **serial-dependency floor** — phases with hard ordering (Phase 2 needs
Phase 1's artefact) cannot parallelise. A 12-AI-day plan with 4 sequential phases is at most ~3 AI-days wall-clock per
phase even with 8 slots. A 12-AI-day plan with 4 independent phases collapses to ~3 AI-days wall-clock total at 4-slot
fan-out, ~1.5 days at 8-slot fan-out.

### Optional frontmatter field

```yaml
effective_concurrent_slots: 1     # default; single-slot serial work
effective_concurrent_slots: 2-4   # typical multi-phase plan with some serial deps
effective_concurrent_slots: 5-8   # heavily-parallel multi-phase plan; rare
```

Use the **range form** when the parallelism axis is ambiguous (depends on what other slots are doing this cycle). Most
plans omit this field — the daily work-split is the operator's actual decision on slot allocation, and the plan can't
predict it upfront. Use only when the plan EXPLICITLY decomposes into independent phases that operators routinely fan
out across slots (master plans, multi-domain umbrella plans, batch backfills).

### Per-plan parallelism declaration — phase-level serial-vs-parallel

The slot divisor only applies to phases that ACTUALLY parallelise. A plan with 4 sequential phases (Phase 2 needs Phase
1's artefact) cannot collapse below the serial-floor wall-clock of `sum(per-phase calibrated_ai_days)`, no matter how
many slots are available.

Plans that declare `effective_concurrent_slots > 1` SHOULD also annotate per-phase parallelism in the body:

```markdown
## Phase 1 — Foundation (SERIAL — Phases 2/3/4 depend on this; ~2 AI-days calibrated)

## Phase 2 — Domain A handler (PARALLEL with Phase 3, Phase 4; ~3 AI-days calibrated)

## Phase 3 — Domain B handler (PARALLEL with Phase 2, Phase 4; ~3 AI-days calibrated)

## Phase 4 — Domain C handler (PARALLEL with Phase 2, Phase 3; ~3 AI-days calibrated)

## Phase 5 — Integration (SERIAL — needs Phases 2/3/4; ~2 AI-days calibrated)
```

Wall-clock floor for the above: `2 (Phase 1) + max(3,3,3) (Phases 2/3/4 fan out at 3+ slots) + 2 (Phase 5) = 7 days`,
NOT `13 / 3 ≈ 4.3 days`. The class-multiplier compresses each phase's effort; the slot divisor compresses ACROSS phases
that ACTUALLY parallelise; the serial-floor bounds both.

When in doubt, mark a phase SERIAL — over-parallelising leads to half-finished phases that block their dependents when
the slot frees up.

### Cross-plan slot contention — the work-split layer

A single plan's `effective_concurrent_slots` is the UPPER BOUND assuming the operator allocates that many slots to it.
In reality, the workspace is running ~50-100 active plans across both operators × 8 slots each, and slot allocation is
competitive. The `plans/active/work_split_<YYYY_MM_DD>_ikenna.md` + `..._harsh.md` files are the operator's daily
decision on:

- Which plans get slots this cycle.
- Which slot/sub-agent works on which plan-phase.
- Cross-tab handshakes (when slot 2 needs slot 5's output before starting).
- Cross-side handshakes (when Ikenna's slot 7 needs Harsh's slot 3's artefact).

Wall-clock estimate for a plan in a given cycle =
`phase_serial_floor + max_concurrent_phase_calibrated / slots_actually_allocated_this_cycle`. The plan's
`effective_concurrent_slots` is the _capacity_ number; the work-split's slot allocation is the _realised_ number.

When estimating "will this plan ship by deadline X", read the plan's parallelism declaration AND check whether the
current/upcoming work-split actually allocates the needed slots. The plan-level estimate is necessary but not sufficient
— without the work-split allocation, you're estimating in a vacuum.

### Don't double-discount

If you set `effective_concurrent_slots: 4` for a plan, the wall-clock prediction is `calibrated / 4`, NOT
`baseline / 4 × 0.4 (refactor)`. The class multiplier already captures intra-slot sub-agent fan-out — applying it again
on top of the slot divisor double-counts the same compression.

### Workspace ceiling sanity check (corrected 2026-05-11)

**Two throughput numbers, often confused — keep them straight:**

1. **Scheduled scope** = AI-days totalled in the daily work-split's slot table. Conservative because it bakes in safety
   margin for blocked slots + Q&A bus latency + collisions. 2026-05-11 split was ~36 cal AI-days/4-day-cycle workspace =
   ~9/day workspace = ~4.5/day per side. **This is the BUDGET, not the throughput.**
2. **Delivered throughput** = cal AI-days actually shipped (commit-derived, weighted by commit type — substantive ship
   ~1.5, service code ~1.2, plan flip ~0.15, coordination ping ~0.05). 2026-05-11 measured **~130 cal AI-days/day
   workspace = ~65/side**, derived from 343 same-day commits across 8 active repos (`unified-trading-pm` 286, services
   47, bot 10, with class-weighted average ~0.38 cal AI-days/commit).

**The new ceiling**:

- **Measured sustained: ~65-75 cal AI-days/day per side** (~130-150 workspace; 2026-05-11 sampled at upper end).
- **Theoretical ceiling: ~80-100 cal AI-days/day per side** (~160-200 workspace) at 8 slots × 8-12 cal AI-days/slot/day
  post-class-multiplier with zero foot-gun rework + active operator load-balancing + sub-agent fan-out depth 4-6.
- **Below-this signals scope slip**: 2026-05-04→11 average commit rate ~250/day workspace × class-weighted ~0.4 =
  ~100/day workspace = ~50/side. Below 50/side sustained = something is blocking.

**Why the old "~50/side ceiling" was wrong**: it conflated scheduled budget (4.5/side measured) with throughput ceiling
(65/side measured). Original "~50/side" number derived from a back-of-envelope `8 slots × 6 cal AI-days/slot/day` that
ignored coordination commits + plan-flip work + governance burn — all of which are real cal AI-days delivered into the
workspace, just not into a single plan's checkbox count.

**How to apply to projections**: when you need to estimate "will N cal AI-days of scope finish in M days," divide by
**~100-130 cal AI-days/day workspace** (the measured 7-day average) for the realistic-pace projection. Use
**~150-180/day** only for the stretch-target projection (push pace, sub-agent fan-out maxed, minimal foot-guns). Don't
use the scheduled-budget number — it understates real throughput ~7×.

---

## When the multipliers don't apply

Calibration assumes the work pattern that's been measured. Stop applying the multiplier and use the baseline (or higher)
when:

1. **Serial-only by construction** — wallet-key approval, kill-switch arming, force-push, version 1.0.0 graduation (the
   human-only hard-stops listed under "Plans Run To Actual Completion").
2. **Single-tab work** — no sub-agent fan-out planned + no parallel slot context to lean on.
3. **External-dependency-bound** — waiting on a counterparty (CEFFU custody onboarding, Copper integration approval,
   exchange API key issuance). Calendar time, not work time.
4. **First touch on a brand-new domain** — first VM launcher in a new asset_group, first connector to a new venue. Treat
   as `brand-new` class until 2-3 retrospective entries calibrate it.

---

## Frontmatter convention

Every active plan + wrapper plan written **after 2026-05-11** adds three new frontmatter fields:

```yaml
estimate_class: refactor | design | infra | brand-new | research
estimate_baseline_ai_days: <pre-calibration estimate as integer or range, e.g. 6 or "6-8">
estimate_calibrated_ai_days: <baseline × multiplier, e.g. 2.4 or "2.4-3.2">
```

**Epic exemption (codified 2026-05-21)**: epics in `plans/epics/` are everlasting and do NOT carry these three fields.
Estimation lives on the active plans they reference (which are organised into the epic's priority blocks). Full epic
frontmatter rules: [`../../plans/epics/README.md`](../../plans/epics/README.md).

For **multi-class plans** (e.g. a master plan with design + infra + refactor phases), use the dominant class for the
plan-level field and override per-phase inline:

```markdown
## Phase 4 — Backfill all DeFi history into AWS S3

**Class**: infra. **Baseline**: 8 AI-days. **Calibrated**: 6.4 AI-days (8 × 0.8).
```

For **legacy plans** (created before 2026-05-11), retrofit the frontmatter on next substantive update — don't sweep all
of them at once (collision risk with their owner agents).

---

## Retrospective ledger workflow

Every plan archive (per `Plan Archival` HARD RULE in CLAUDE.md) adds a row to
[estimation-retrospective-ledger.md](estimation-retrospective-ledger.md):

| Plan | Class | Calibrated estimate | Actual | Ratio | Notes |

**Actual** = wall-clock AI-days from first commit on the plan to the last logical-unit commit (checkbox-flip or
archive-commit), counted in continuous working days, not calendar.

**Ratio** = actual / calibrated. Above 1.0 means we underestimated even after calibration; below 1.0 means we still have
room to compress the multiplier.

**Recalibration**: when 8+ rows land for a given class with median ratio drifting more than ±20% from 1.0, propose an
updated multiplier in a `docs(codex):` PR + this doc.

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
- **Plans Run To Actual Completion** (CLAUDE.md): "Code-shipped is NOT operationally-shipped" — the `infra` multiplier
  already accounts for the verification tail; don't re-discount it.
- **Capture Discoveries As Plan Todos Immediately** (CLAUDE.md): if scope expands mid-plan and you need to add todos,
  recalibrate the new todos with the same multiplier.
- **Plan Archival** (CLAUDE.md): retrospective ledger row is part of the archive logical unit.

---

## Anti-patterns

- **Multiplying a multiplied number** — the calibrated number is the final estimate; don't apply 0.5× to it again.
- **Picking a low class to make scope look bigger** — the goal is honest scope sizing, not gaming the work-split.
- **Skipping the retrospective ledger row** — calibration only self-corrects if actuals get logged.
- **Sweeping every active plan to retrofit frontmatter** — owner agents update on next touch; mass-sweeps collide.
