---
doc_type: plan
title: Plan hygiene automation — scripts + runbook + cron
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: [/plans/archive/2026_07/master_to_live_defi_2026_05_23.md]
created: "2026-05-21"
parent_epic: plan_hygiene_master
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Plan Hygiene Automation

Ships the scripts + runbook for `plan_hygiene_master`. Phase 1 (scripts) and Phase 2 (runbook) are the immediate
deliverable — Ikenna and Harsh can run `bash scripts/plan-hygiene/run_hygiene_sweep.sh` as part of their morning boot
sequence on the planning VM.

Codex SSOTs: `/codex/11-project-management/active-plan-inventory-tracker.md` · `plans/epics/README.md`

---

## Phase 1 — Core scripts

- [x] ✅ [SCRIPT] P0. `scripts/plan-hygiene/check_todo_regression.sh` — compare every `plans/active/*.md` open todo
      count vs `origin/live-defi-rollout`; exit 1 on any regression. (PM@2026-05-21)
- [x] ✅ [SCRIPT] P0. `scripts/plan-hygiene/check_frontmatter.sh` — assert `---` on own first line; required fields; no
      deprecated fields. (PM@2026-05-21)
- [x] ✅ [SCRIPT] P1. `scripts/plan-hygiene/check_line_caps.sh` — soft-warn >500L, hard-fail >1000L; umbrella exemption
      for locked+>100 todos. (PM@2026-05-21)
- [x] ✅ [SCRIPT] P1. `scripts/plan-hygiene/check_archive_candidates.sh` — find plans with 0 open todos and >0 done;
      print list for operator review. (PM@2026-05-21)

## Phase 2 — Runbook

- [x] ✅ [SCRIPT] P0. `scripts/plan-hygiene/run_hygiene_sweep.sh` — orchestrates all Phase 1 checks + runs inventory
      regenerator; prints PASS/FAIL table; `--ci` flag for cron. (PM@2026-05-21)

## Phase 3 — Wire into morning boot

~~LEDGER.md wiring — dropped~~ `ikenna_orchestrator/LEDGER.md` and `harsh_orchestrator/LEDGER.md` are **offline fallback
only** since D0 migration (`d0_orchestrator_migration_2026_05_20`; CLAUDE.md). VMs do not reboot daily. Canonical wiring
path is Phase 6 (daily cron on planning VM). These todos are superseded:

- [x] ~~[SCRIPT] P0. Add `run_hygiene_sweep.sh` to `ikenna_orchestrator/LEDGER.md` boot sequence~~ — N/A: LEDGER is
      offline fallback only per D0.
- [x] ~~[SCRIPT] P0. Same addition to `harsh_orchestrator/LEDGER.md`~~ — N/A: cron (Phase 6) is the VM-side path.

## Phase 4 — Additional checks

- [x] ✅ [SCRIPT] P2. `scripts/plan-hygiene/check_codex_refs.sh` — grep all `codex/...` path strings in active plans;
      verify files exist; report broken refs. (Soft check — 16 broken refs found on first run.) (PM@2026-05-21)
- [x] ✅ [SCRIPT] P2. `scripts/plan-hygiene/check_estimate_sanity.sh` — verify
      `estimate_calibrated ≈ baseline × class_multiplier`; flag >20% drift. (PM@2026-05-21)
- [x] ✅ [SCRIPT] P2. `scripts/plan-hygiene/check_superseded_in_active.sh` — grep `plans/active/` for filenames + body
      text containing `SUPERSEDED`; those should be in `plans/archive/`. (PM@2026-05-21)
- [x] ✅ [SCRIPT] P2. Wire Phase 4 scripts into `run_hygiene_sweep.sh` as additional soft checks. (PM@2026-05-21)

## Phase 5 — Pre-push hook

- [x] ✅ [SCRIPT] P1. `scripts/plan-hygiene/install_hooks.sh` — installs `check_todo_regression.sh` +
      `check_frontmatter.sh` as `.git/hooks/pre-push` in `unified-trading-pm`. Prevents regressions at commit time.
      (PM@2026-05-21)

## Phase 6 — Cron on planning VM (primary wiring path)

- [x] ✅ [SCRIPT] P0. Add `run_hygiene_sweep.sh --ci` to planning-VM Cloud Run job (alongside orphan-ping-audit cron).
      Schedule `0 5 * * *` UTC. Failures append `## [hygiene-cron]` block to both orchestrator `_agent_pings.md` files.
      Assign to VM via `plan_hygiene_master` `assigned_vm:` field in epic frontmatter. — deployment-service
      `terraform/gcp/plan_hygiene_scheduler.tf` + `scripts/plan-hygiene/cron_hygiene_sweep_entrypoint.sh`
- [x] ✅ [SCRIPT] P1. Add cron job to `deployment-service/terraform/gcp/` Terraform (adjacent to
      `orphan_ping_audit_scheduler.tf`). Entrypoint: `scripts/plan-hygiene/cron_hygiene_sweep_entrypoint.sh` (clone PM @
      LDR, run sweep --ci, commit + push failure pings). — deployment-service `terraform/gcp/plan_hygiene_scheduler.tf`

## Temporary states + canonical follow-up plans

- Phase 4-6 are not May-23 blockers — post-cutover scope.
- Phase 6 (daily cron on planning VM) is the highest-value non-shipped item; replaces Phase 3.
