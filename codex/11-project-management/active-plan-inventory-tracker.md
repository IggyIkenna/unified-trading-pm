---
scope: [engineer, admin]
title: Active Plan Inventory + Done-vs-Left Dashboard
type: project-management
status: living
last_reviewed: 2026-05-17
owner: pm-orchestrator
cadence: morning + EOD + before planning decisions (slot 1 main, both sides)
verifier: python3 unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py
last_executed: 2026-05-17
---

# Active Plan Inventory + Done-vs-Left Dashboard

> SSOT for the auto-tracked workspace-wide plan inventory that lives inside `master_to_live_defi_2026_05_23.md`. Shipped
> 2026-05-12 (PM@ab1a471f) to solve two coupled problems surfaced in the calibration thread:
>
> 1. **"What's done vs left across the workspace?"** — was a 20-line grep + manual tally every time.
> 2. **"Is the master plan truly wrapping every active plan?"** — was hidden until the orphan column made it visible (19
>    of 54 plans were not referenced by master or any epic at first run).

---

## What it is

A script (`unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py`) that:

1. Scans `plans/active/*.md` for every plan carrying `estimate_class` frontmatter.
2. Counts done/todo checkboxes in plan body (regex `- [x]` / `- [ ]`).
3. Computes `cal_remaining = estimate_calibrated_ai_days × todo / (done + todo)`.
4. Determines the **owner** by grepping each plan's filename stem across `master_to_live_defi_2026_05_23.md`
   - every `plans/epics/*.md`. First reference wins; "**orphan**" if none.
5. Writes a sorted markdown table (cal_left desc) between `<!-- AUTO-INVENTORY-START -->` and
   `<!-- AUTO-INVENTORY-END -->` markers in the master plan.
6. Emits an aggregate row: total plans + orphan count + TBD count + % done + total cal AI-days left.

**Idempotent**: only rewrites content between markers. Errors out if markers absent (operator adds the section

- markers once).

**Skipped files**: `INDEX.md`, `task_template.md`, `work_split_*`, `_agent_pings.md`, `continuation_prompts_*`,
`_AUDIT_*`, `_HANDOFF_*`, `_SESSION_HANDOFF_*` (all ephemeral or coordination-doc files, not real plans).

---

## Where the dashboard lives

`unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.md` § **Active plan inventory + Done-vs-Left dashboard
(auto-tracked)**, between the "Epics index" section and "What this plan is".

Columns: `Plan | Owner | Class | Checkboxes | % done | Cal left | Deadline`.

Note: the master plan's filename references "live_defi" historically but the plan itself is the **full May-23 cutover
umbrella** across all asset groups (DeFi + CeFi + TradFi + Sports + Predictions + cross-cutting), per its own Epics
index. The inventory tracks every active plan workspace-wide, not just DeFi plans.

---

## Refresh cadence

Main-orchestrator agent (Ikenna's slot 1 + Harsh's slot 1) runs the script at:

- **Morning ledger sweep** (~09:00 local) — to seed today's planning decisions with fresh numbers.
- **EOD** (~17:00 local) — to capture the day's progress flips for tomorrow's work-split sizing.
- **Before any planning decision** that depends on done-vs-left state (e.g. cutover go/no-go, scope-cut decision,
  deadline-slip risk readout).

Run from anywhere:

```bash
python3 unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py
```

Resolves paths relative to the script's location; no `cd` required. Stdout reports
`N plans, M orphans, K TBD, P% done overall, X cal AI-days left.`

---

## How to read the dashboard

- **Owner = `master`**: plan is referenced by `master_to_live_defi_2026_05_23.md` body.
- **Owner = `<epic-name>`** (e.g. `cefi_master`, `defi_master`, `predictions_master`): plan is referenced by that
  specific epic master.
- **Owner = `README`**: plan is referenced only by `plans/epics/README.md` (the epics-listing index). The plan itself is
  likely a master plan that should be wrapped by the May-23 umbrella but is currently self-floating.
- **Owner = `**orphan**`** (bold-marked): plan is not referenced by master OR any epic. Action: fold into the
  appropriate epic on the next substantive plan-touch (per Findings Triage HARD RULE; no mass-sweep — collision risk
  with owner agents).

- **Cal left = `TBD`**: plan has `estimate_baseline_ai_days: TBD` in frontmatter (calibration sweep 2026-05-11
  scaffolded these). Owner agent fills the baseline on next substantive touch.
- **Cal left = numeric**: `estimate_calibrated_ai_days × (todo / (done + todo))`. Recomputes every regeneration.

- **% done**: checkbox count (done / (done + todo) × 100). Note this is checkbox-count, not cal-AI-day-weighted — a plan
  with 50 trivial flips done + 5 hard flips remaining can show high % done with substantial cal_left.

- **Aggregate row**: orphan + TBD counts + workspace-wide % done (cal-weighted) + total cal AI-days left.

---

## When to use it

- **Daily planning** — feeds the daily work-split scope sizing (per CLAUDE.md "Daily Work-Split Process").
- **Cutover go/no-go** — total cal left × measured throughput rate → wall-clock projection to deadline.
- **Orphan triage** — operator periodically sweeps the orphan list, asks owner agents to fold into appropriate epics
  during normal plan-touch cycles.
- **Coverage audit** — verify the master plan + epics actually wrap the workspace; new plans added without epic
  reference show up as orphans within hours.

---

## When NOT to use it

- **Mid-iteration progress check**: use `git log --oneline live-defi-rollout --since='2 hours ago'` for real-time
  progress; the inventory only refreshes on script run, not on every commit.
- **Per-phase progress within a plan**: the dashboard rolls up to plan level. Phase-level state lives in the plan body's
  checkbox tree + `## Open questions` section.
- **Effort vs wall-clock prediction**: the inventory shows cal AI-days (effort) remaining, not wall-clock prediction.
  Multiply through the parallelism axis per `codex/08-workflows/estimation-calibration.md` § "Parallelism axis" for
  wall-clock floor.

---

## Composes with

- **Estimate Calibration framework** (CLAUDE.md HARD RULE + `codex/08-workflows/estimation-calibration.md`) — the
  `estimate_class` + `estimate_calibrated_ai_days` frontmatter is what the inventory reads.
- **Retrospective Ledger** (`codex/08-workflows/estimation-retrospective-ledger.md`) — workspace-wide throughput
  observations feed the realistic-pace number used in cutover projections.
- **Plan Filename Convention + 3-Layer Model** (CLAUDE.md) — the inventory respects the layer model: master at top,
  epics in middle, granular sub-plans below.
- **Findings Triage Discipline** (CLAUDE.md HARD RULE) — orphan resolution happens per-plan on owner agent's next
  substantive touch, NOT via mass-sweep.
- **Daily Work-Split Process** (CLAUDE.md) — work-split scope sizing reads the inventory's `cal_left` numbers to
  allocate slot scope.

---

## Anti-patterns

- **Reading the dashboard without re-running first**: numbers are stale between regenerations. Always re-run before
  planning decisions.
- **Mass-sweeping orphans into epics in a single commit**: collision risk per Findings Triage. Owner agents resolve
  their plan's orphan status on next plan-touch.
- **Treating `% done` as a release-readiness metric**: checkbox count is not weighted by criticality. A plan with 90%
  checkbox-done can still have the highest-risk 10% left.
- **Hand-editing content between markers**: the next script run overwrites manual edits. Adjust the script if you need a
  different column layout / sort order.

---

## Future extensions (deferred)

- **QG ratchet**: wire the script into `unified-trading-pm/scripts/quality-gates.sh` so PR-time QG fails if the
  inventory in master plan is stale vs filesystem state. Would force refresh on every PR. **Deferred** — current manual
  cadence is sufficient and the failure-mode of "PR blocked because dashboard stale" is operator-hostile.
- **Per-epic rollup**: separate inventory section per epic master, not just one workspace-wide table. **Deferred** — the
  Owner column already lets readers filter mentally.
- **Cal-weighted % done in main table**: today shows checkbox-count %; could show cal-AI-day-weighted % per row.
  **Deferred** — would require knowing per-checkbox cal weight, which plans don't carry.
- **Auto-refresh on every commit via post-commit hook**: rejected — every PM commit re-runs the script + creates noise
  commits. Daily manual cadence is correct granularity.
