---
doc_type: codex-ssot
title: Plan Hygiene — Scripts, Runbook, and Cron
summary:
  The `run_hygiene_sweep.sh` script suite (9 structural checks) + required/deprecated plan + epic frontmatter fields +
  cron/GHA cadence (daily sweep, Plan Health Agent) + archive-eligibility discipline for `plans/active/` +
  `plans/epics/`.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, cron, frontmatter, archive, quality-gates, docspec]
related:
  [
    /codex/11-project-management/doc-frontmatter-schema.md,
    ../../plans/epics/plan_hygiene_master.md,
    ../../plans/archive/2026_05/plan_hygiene_automation_2026_05_21.md,
  ]
created: 2026-05-21
authoritative_for: [plan-hygiene script suite (structural checks), required/deprecated plan frontmatter field list]
referenced_by:
  [
    /codex/11-project-management/active-plan-inventory-tracker.md,
    /codex/11-project-management/codex-audit-playbook.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
  ]
owner: plan_hygiene_master
last_reviewed: 2026-07-24
code_refs:
  [
    scripts/plan-hygiene/run_hygiene_sweep.sh,
    scripts/plan-hygiene/fix_frontmatter.py,
    scripts/plan-hygiene/cron_hygiene_sweep_entrypoint.sh,
    scripts/plan-hygiene/build_health_digest.sh,
    scripts/docs/docspec.py,
    .github/workflows/plan_health-agent.yml,
    deployment-service/terraform/gcp/hygiene_sweep_scheduler.tf,
  ]
type: project-management
cadence: daily (cron) + on-demand
verifier: bash unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh
last_executed: 2026-05-21
---

# Plan Hygiene — Scripts, Runbook, and Cron

> SSOT for the workspace-wide plan hygiene system. Shipped 2026-05-21 (PM@0200b94b8). Work-tracker:
> `plans/active/plan_hygiene_automation_2026_05_21.md`. Epic: `plans/epics/plan_hygiene_master.md`.

---

## What it is

A suite of scripts that enforce structural and metadata quality across all plans in `plans/active/` and `plans/epics/`.
Catches broken frontmatter, missing required fields, oversized plans, and completed plans sitting in `active/` instead
of `archive/`.

---

## Scripts

All scripts live in `unified-trading-pm/scripts/plan-hygiene/`.

| Script                            | What it checks                                                                                                                                                                                                                                                                                                                                                                                       | Exit code                          |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `run_hygiene_sweep.sh`            | Orchestrates all checks below + inventory regenerator                                                                                                                                                                                                                                                                                                                                                | 0 = all pass, 1 = any hard failure |
| `check_frontmatter.sh`            | `---` on own first line; required fields present; no deprecated fields                                                                                                                                                                                                                                                                                                                               | 0 = clean                          |
| `check_line_caps.sh`              | Plans (`plans/active/*.md`): soft warn >500L, hard fail >1000L, NO exemption. Epics (`plans/epics/*.md`): hard fail >2000L. Ratchet-baselined (`line_caps_baseline.yaml`), real hard gate in the sweep + prek `--precommit` (2026-07-24; the old `umbrella: true`/`locked_by`+todos escape hatch was removed the same day — a large hub doc either fits under 1000L, splits, or becomes a real epic) | 0 = count ≤ baseline               |
| `check_todo_regression.sh`        | Every plan's open todo count ≥ count on `origin/live-defi-rollout`                                                                                                                                                                                                                                                                                                                                   | 0 = no regressions                 |
| `check_archive_candidates.sh`     | Plans with 0 open todos and >0 done — prints list for operator review                                                                                                                                                                                                                                                                                                                                | always 0 (informational)           |
| `check_codex_refs.sh`             | All `codex/...` paths in plan bodies resolve to real files                                                                                                                                                                                                                                                                                                                                           | always 0 (soft)                    |
| `check_estimate_sanity.sh`        | `estimate_calibrated ≈ baseline × class_multiplier` within ±20%                                                                                                                                                                                                                                                                                                                                      | always 0 (soft)                    |
| `check_superseded_in_active.sh`   | No `*SUPERSEDED*` filenames or superseded `parent_epic` slugs in `active/`                                                                                                                                                                                                                                                                                                                           | always 0 (soft)                    |
| `check_claude_subagent_parity.sh` | Every `## ` topic in `CLAUDE.md` has a counterpart in `SUB_AGENT_MANDATORY_RULES.md` (topic-parity drift — a rule added to CLAUDE.md must reach sub-agents)                                                                                                                                                                                                                                          | always 0 (soft)                    |
| `install_hooks.sh`                | Installs `check_todo_regression.sh` + `check_frontmatter.sh` as `.git/hooks/pre-push`                                                                                                                                                                                                                                                                                                                | — (run once)                       |
| `fix_frontmatter.py`              | Auto-fix: unjam `---key:` lines, remove deprecated fields, add missing required fields                                                                                                                                                                                                                                                                                                               | — (run manually)                   |

### Required plan frontmatter fields

`parent_epic` · `title` · `priority` · `status` · `estimate_class` · `estimate_baseline_ai_days` ·
`estimate_calibrated_ai_days` · `locked_by`

> **Universal core + machine validator (W2, 2026-06-24).** The full cross-doc-type schema — the **universal core**
> required on EVERY doc (`doc_type`/`title`/`status`/`created`/…) plus the per-`doc_type` field specs, closed-vocab
> enums, and `null`/`NA` conventions — is the SSOT [`doc-frontmatter-schema.md`](./doc-frontmatter-schema.md). Its
> machine mirror is `scripts/docs/docspec.py` (`docspec.validate_frontmatter()` + the `--check` CLI), the same engine
> the completeness gate should call rather than reimplement. The narrow structural list above is the **currently
> blocking** subset; per the schema doc's enforcement sequencing (§11, soak-then-gate), broader enforcement is wired by
> the downstream workstreams (W3 backfill → W5 gate flip → W6/W7 per-type), not duplicated here.

### Required epic frontmatter fields

`name` · `title` · `priority` · `status` · `assigned_vm` · `tier`

> **[DELTA 2026-05-22]** Added `assigned_vm` and `tier` to required epic fields to match CLAUDE.md ("required
> `assigned_vm` + `tier` + `priority` frontmatter") — the codex previously listed only `name/title/priority/status`.
> `check_frontmatter.sh` must enforce all 6 fields.

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

`run_hygiene_sweep.sh --ci` runs daily at `0 5 * * *` UTC via the `uts-prod-plan-hygiene-sweep` Cloud Run job. On hard
failure it posts a Slack alert to `#agent-orchestrator-alerts` (webhook secret `AGENT_ORCHESTRATOR_SLACK_WEBHOOK`);
details stay in the Cloud Run job logs.

> The pre-2026-07-04 delivery (append a `## [hygiene-cron]` block to the `_agent_pings.md` orchestrator inboxes +
> auto-commit) is RETIRED, together with the every-4h orphan-ping audit cron (`uts-prod-orphan-ping-audit` job +
> scheduler + terraform, all deleted). The ping-ledger channel is dead — agent comms go through the agent-orchestrator
> HTTP server.

Terraform SSOT: `deployment-service/terraform/gcp/hygiene_sweep_scheduler.tf`. Entrypoint:
`scripts/plan-hygiene/cron_hygiene_sweep_entrypoint.sh`.

## Plan Health Agent (GHA — `.github/workflows/plan_health-agent.yml`, daily 02:00 UTC)

Report-only daily audit. The deterministic `build_health_digest.sh` runs the full hygiene sweep (including
`check_claude_subagent_parity.sh`) and hands a compact digest + plan skeletons to a cheap Haiku agent. The agent does
the **two things a script cannot**:

1. **Cross-plan contradiction** — pairs of plans assigning contradictory status / architecture to the same scope.
2. **Doc-drift (CLAUDE.md / SUB_AGENT vs live plans)** — a governance-doc rule CLAIM that is contradicted or superseded
   by an active plan/epic (e.g. CLAUDE.md framing `source=` as TradFi-only while the active plan declares it
   crosscutting). This is the **semantic** counterpart to the deterministic topic-parity check: parity catches a topic
   that never reached SUB*AGENT; doc-drift catches a topic whose \_content* has gone stale vs the plans. CLAUDE.md is
   injected into the agent prompt (`WORKSPACE_RULES_CLAUDE`); SUB_AGENT arrives as the `MANDATORY_RULES` block.

Output JSON: `{"contradictions": [...], "doc_drift": [{"doc","claim","contradicted_by","description"}]}` → GHA run
summary + Slack one-liner (`contradictions: N | doc-drift: M`).

---

## Epic-foundation model (codified 2026-05-21)

**Epics in `plans/epics/<slug>.md` are everlasting** — no date suffix, no `estimate_*` fields. Required epic
frontmatter: `name` · `title` · `type: epic` · `priority` · `status` · `assigned_vm`.

Active plans in `plans/active/<slug>_YYYY_MM_DD.md` MUST carry `parent_epic:` pointing to a live (non-SUPERSEDED) epic
slug. Active plans without `parent_epic:` are **ORPHANS** — review-blocking at PR time. `check_frontmatter.sh` flags
orphans. The `check_superseded_in_active.sh` script flags plans whose `parent_epic:` still points to a `*SUPERSEDED*`
slug.

Epics are **exempt** from `estimate_class` / `estimate_baseline_ai_days` / `estimate_calibrated_ai_days` — those fields
live on active plans only. The `check_frontmatter.sh` script should NOT require estimate fields on epics.

Full SSOT: `plans/epics/README.md` (epic-flow + lifecycle + 10-VM topology).

---

## Estimate fields and AI-days accounting

Every **active plan** (not epics) carries `estimate_class`, `estimate_baseline_ai_days`, and
`estimate_calibrated_ai_days`. These feed the inventory regenerator
(`scripts/plans/regenerate_active_plan_inventory.py`) which computes
`cal_remaining = calibrated × (open_todos / total_todos)` and rolls up the workspace-wide AI-days total.

Multipliers per class: `refactor=0.4` · `design=0.6` · `infra=0.8` · `brand-new=1.0` · `research=1.2`. Full SSOT:
`/codex/08-workflows/estimation-calibration.md`.

---

## Archive discipline

A plan is eligible for archival when:

1. `grep -c "^- \[ \]" <plan>` returns 0 (zero open todos).
2. No genuine DEFERRED prose in the body (prose deferrals must be converted to `- [ ]` todos first).

Archive destination: `plans/archive/YYYY_MM/`. Use `git mv` — do not copy-paste.

`check_archive_candidates.sh` surfaces eligible plans. `check_frontmatter.sh` also runs over `plans/archive/` to keep
archived plans schema-clean.
