---
title: Plan Hygiene — Scripts, Runbook, and Cron
type: project-management
status: living
last_reviewed: 2026-05-21
owner: plan_hygiene_master
cadence: daily (cron) + on-demand
verifier: bash unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh
last_executed: 2026-05-21
---

# Plan Hygiene — Scripts, Runbook, and Cron

> SSOT for the workspace-wide plan hygiene system. Shipped 2026-05-21 (PM@0200b94b8).
> Work-tracker: `plans/active/plan_hygiene_automation_2026_05_21.md`.
> Epic: `plans/epics/plan_hygiene_master.md`.

---

## What it is

A suite of scripts that enforce structural and metadata quality across all plans in `plans/active/` and
`plans/epics/`. Catches broken frontmatter, missing required fields, oversized plans, and completed plans
sitting in `active/` instead of `archive/`.

---

## Scripts

All scripts live in `unified-trading-pm/scripts/plan-hygiene/`.

| Script | What it checks | Exit code |
| --- | --- | --- |
| `run_hygiene_sweep.sh` | Orchestrates all checks below + inventory regenerator | 0 = all pass, 1 = any hard failure |
| `check_frontmatter.sh` | `---` on own first line; required fields present; no deprecated fields | 0 = clean |
| `check_line_caps.sh` | Soft warn >500L, hard fail >1000L; umbrella exemption (locked + >100 todos) | 0 = no hard violations |
| `check_todo_regression.sh` | Every plan's open todo count ≥ count on `origin/live-defi-rollout` | 0 = no regressions |
| `check_archive_candidates.sh` | Plans with 0 open todos and >0 done — prints list for operator review | always 0 (informational) |
| `fix_frontmatter.py` | Auto-fix: unjam `---key:` lines, remove deprecated fields, add missing required fields | — (run manually) |

### Required plan frontmatter fields

`parent_epic` · `title` · `priority` · `status` · `estimate_class` · `estimate_baseline_ai_days` ·
`estimate_calibrated_ai_days` · `locked_by`

### Required epic frontmatter fields

`name` · `title` · `priority` · `status`

### Deprecated fields (plans)

`slug` · `deadline` · `owner` · `asset_group` · `horizon` · `operator` · `companion_to` · `companion_plans` ·
`spawned_from` · `parent_plan` · `related_codex` · `overview` · `date` · `type` · `author` · `plan_type`

### Deprecated fields (epics)

`owner` · `asset_group`

---

## How to run manually

```bash
cd unified-trading-pm
bash scripts/plan-hygiene/run_hygiene_sweep.sh          # full sweep with output
bash scripts/plan-hygiene/run_hygiene_sweep.sh --quiet  # suppress passing checks
bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci     # cron mode (no inventory regenerate)
```

To auto-fix frontmatter violations before committing:

```bash
python3 scripts/plan-hygiene/fix_frontmatter.py --dry-run   # preview changes
python3 scripts/plan-hygiene/fix_frontmatter.py             # apply fixes
```

---

## Cron (planning VM)

`run_hygiene_sweep.sh --ci` runs daily at `0 5 * * *` UTC on the planning VM Cloud Run job, alongside
`orphan_ping_audit_scheduler.tf`. On failure, appends a `## [hygiene-cron]` notification block to both
`ikenna_orchestrator/_agent_pings.md` and `harsh_orchestrator/_agent_pings.md`.

Terraform SSOT (when shipped): `deployment-service/terraform/gcp/hygiene_sweep_scheduler.tf`.
Entrypoint: `scripts/plan-hygiene/cron_hygiene_sweep_entrypoint.sh`.

Status: **Phase 6 of `plan_hygiene_automation_2026_05_21.md` — not yet shipped.**

---

## Estimate fields and AI-days accounting

Every active plan carries `estimate_class`, `estimate_baseline_ai_days`, and `estimate_calibrated_ai_days`.
These feed the inventory regenerator (`scripts/plans/regenerate_active_plan_inventory.py`) which computes
`cal_remaining = calibrated × (open_todos / total_todos)` and rolls up the workspace-wide AI-days total.

Multipliers per class: `refactor=0.4` · `design=0.6` · `infra=0.8` · `brand-new=1.0` · `research=1.2`.
Full SSOT: `codex/08-workflows/estimation-calibration.md`.

---

## Archive discipline

A plan is eligible for archival when:

1. `grep -c "^- \[ \]" <plan>` returns 0 (zero open todos).
2. No genuine DEFERRED prose in the body (prose deferrals must be converted to `- [ ]` todos first).

Archive destination: `plans/archive/YYYY_MM/`. Use `git mv` — do not copy-paste.

`check_archive_candidates.sh` surfaces eligible plans. `check_frontmatter.sh` also runs over `plans/archive/`
to keep archived plans schema-clean.
