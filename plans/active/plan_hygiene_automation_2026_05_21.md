---
title: Plan hygiene automation — scripts + runbook + cron
parent_epic: plan_hygiene_master
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - master_to_live_defi_2026_05_23.md
---

# Plan Hygiene Automation

Ships the scripts + runbook for `plan_hygiene_master`. Phase 1 (scripts) and Phase 2 (runbook) are the immediate
deliverable — Ikenna and Harsh can run `bash scripts/plan-hygiene/run_hygiene_sweep.sh` as part of their morning boot
sequence on the planning VM.

Codex SSOTs: `codex/11-project-management/active-plan-inventory-tracker.md` · `plans/epics/README.md`

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

- [ ] [SCRIPT] P0. Add `bash scripts/plan-hygiene/run_hygiene_sweep.sh` as first step in `ikenna_orchestrator/LEDGER.md`
      § "Morning boot sequence" (after `git fetch`).
- [ ] [SCRIPT] P0. Same addition to `harsh_orchestrator/LEDGER.md` § "Morning boot sequence".

## Phase 4 — Additional checks

- [ ] [SCRIPT] P2. `scripts/plan-hygiene/check_codex_refs.sh` — grep all `codex/...` path strings in active plans;
      verify files exist; report broken refs. (Mechanical only — semantic drift requires agent work; see
      `plan_hygiene_master` Phase 4.)
- [ ] [SCRIPT] P2. `scripts/plan-hygiene/check_estimate_sanity.sh` — verify
      `estimate_calibrated ≈ baseline × class_multiplier`; flag >20% drift.
- [ ] [SCRIPT] P2. `scripts/plan-hygiene/check_superseded_in_active.sh` — grep `plans/active/` for filenames + body text
      containing `SUPERSEDED`; those should be in `plans/archive/`.
- [ ] [SCRIPT] P2. Wire Phase 4 scripts into `run_hygiene_sweep.sh` as additional soft checks.

## Phase 5 — Pre-push hook

- [ ] [SCRIPT] P1. `scripts/plan-hygiene/install_hooks.sh` — installs `check_todo_regression.sh` +
      `check_frontmatter.sh` as `.git/hooks/pre-push` in `unified-trading-pm`. Prevents regressions at commit time.

## Phase 6 — Cron on planning VM

- [ ] [SCRIPT] P1. Add `run_hygiene_sweep.sh --ci` to planning-VM Cloud Run job (alongside orphan-ping-audit cron).
      Schedule `0 5 * * *` UTC. Failures append `## [hygiene-cron]` block to both orchestrator `_agent_pings.md` files.
- [ ] [SCRIPT] P2. Add cron job to `deployment-service/terraform/gcp/` Terraform (adjacent to
      `orphan_ping_audit_scheduler.tf`).

## Temporary states + canonical follow-up plans

- Phase 4-6 are not May-23 blockers — post-cutover scope.
- Phase 3 (morning boot wiring) is the highest-value non-shipped item.
