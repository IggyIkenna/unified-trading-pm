---
title: Plan-hygiene → prek (staged-only) + fold-to-QG + 24h agentic contradiction RESOLUTION
created: 2026-06-10
source:
  - operator-design-decision-2026-06-10
  - .github/workflows/plan-health-agent.yml
  - scripts/plan-hygiene/run_hygiene_sweep.sh
locked_by: live-defi-rollout
parent_epic: plan_hygiene_master
priority: P2
status: active
---

## What I found

Plan-health today is split across two mechanisms in `.github/workflows/plan-health-agent.yml`:

1. **Deterministic hygiene** (`run_hygiene_sweep.sh` — frontmatter / todo-format / runbook-fields = hard; line-caps /
   estimate-sanity = soft) ran as (a) a standalone `plan-health-gate` GHA job on every PM PR to main, and (b) a morning
   planning-VM cron. It is **pure scripting** and was **NOT** in any commit-time gate, so a `docs(plans):` flip (the
   dominant plan change, which takes the prek hook only — never full QG) was ungated locally.
2. **LLM contradiction + doc-drift** — a daily Haiku run (`schedule: 0 2 * * *`) that is **REPORT-ONLY** (the prompt
   says "DO NOT EDIT, MOVE, COMMIT"): it detects + posts to Slack, but never RESOLVES. The resolver machinery
   (`plan_health` wall_type in `server/escalation.py` + `agent-orchestrator/agents/plan-health.md`) is built but the
   daily detector never dispatches to it.

## Design supersession (operator, 2026-06-12) — daily detector moves OFF Haiku/GHA onto a smart VM agent

> Operators (Harsh + Ikenna, 2026-06-12): the daily LLM layer below ("expensive + LLM → daily CI batch", Haiku) is
> SUPERSEDED for the daily path. Haiku-on-GHA is too shallow for the real job (cross-check codex ↔ plans ↔ epics ↔
> issue docs ↔ CODE STATE — "it's way more than frontmatter"), billing-fragile (2026-06-12 daily run died on the GHA
> billing wall — second outage this week), and paid, while the orchestrator infra runs Max-plan slots at $0 marginal.
> New daily shape (todos in "Daily deep reconciler" below): a systemd timer on the CENTRAL VM (vm-0
> `i-0c9b283b31d6b5ca7` — per `orchestrator_human_central_vm_split_2026_06_12.md` the machinery host; its legacy
> `ORCHESTRATOR_VM_ID` is literally `planning`) dispatches ONE deep `plan-reconciler` worker (opus, effort max, thinking
> on; long-running minutes→hour) that DETECTS **and** FIXES, with a **12h grace window** (never touches a plan whose
> newest git change is <12h old — protects running status on fresh plans). The per-commit prek gate, the PM→main
> `plan-health-gate`, and the escalation-based `plan_health` resolver for GATE failures all stay unchanged. The GHA
> daily job + the (silently broken) Cloud Run sweep retire AFTER the reconciler proves out (RULE-11 prove-then-retire).
>
> Audit findings backing this (2026-06-12): Cloud Run `uts-prod-plan-hygiene-sweep` (05:00 UTC) ENABLED but failing
> ~every other day with `Container called exit(1)` and ZERO stdout in Cloud Logging — it dies before its own inbox-ping
> failure handling, so nobody noticed; GHA `plan-health-agent.yml` daily (03:07) killed by the billing wall today; 3
> runtimes (GHA + Cloud Run + prek) doing overlapping sweeps.

## Design decision (operator, 2026-06-10)

- **Cheap + deterministic + per-change → prek (staged-files-only).** Catches plan-flips that skip full QG; fail-fast;
  zero CI credits; no sentinel needed (`files:^plans/` IS the skip). **Staged-files-only is mandatory** (not just nice):
  the corpus carries pre-existing violations, and a whole-corpus pre-commit gate would block every agent's plan commit
  on a violation they didn't cause (RULE-11 blast-radius).
- **origin-compare (todo-regression)** → stays at the daily cron / CI sweep (needs a fetch; too heavy for pre-commit).
- **Expensive + LLM + latency-tolerant → daily CI batch** (already there at 02:00). But it must move from DETECT-only to
  agentic RESOLVE: on findings, dispatch to the built `plan_health` orchestrator path.

## What shipped this session (PM, 2026-06-10)

- [x] ✅ `run_hygiene_sweep.sh --precommit` — lean STAGED-FILES-ONLY gate: computes staged `plans/**.md` via
      `git diff --cached`, runs the staged-scoped hard frontmatter check on only those, exits 1 on a hard failure in a
      plan THIS commit touches. <4s, no origin fetch, portable (macOS bash 3.2). — PM@<pending>
- [x] ✅ `check_frontmatter.sh` — accepts an explicit file list (relative or absolute, normalized); validates only those
      when passed (staged mode), else the full-corpus glob (unchanged cron/CI behaviour). — PM@<pending>
- [x] ✅ `.pre-commit-config.yaml` — `plan-hygiene` local hook (`files: ^plans/`, `pass_filenames: false`) →
      `run_hygiene_sweep.sh --precommit`. Verified live: `prek run plan-hygiene` PASSES on a clean plan; the staged
      frontmatter check exits 1 on the known-bad file (component-verified). — PM@<pending>

## Remaining todos

- [ ] [SCRIPT] P2. Add explicit-file-list support to `check_todo_format.sh` + `check_runbook_fields.py` (mirror the
      `check_frontmatter.sh` staged pattern), then add both to the `--precommit` gate so all three HARD checks are
      staged-scoped. repo: unified-trading-pm.
- [ ] [CI] P2. Fold the same `--precommit` (or a `--staged`) sweep into PM `quality-gates-v2` as a
      content-sentinel-gated step (server backstop on PM PRs), THEN retire the standalone `plan-health-gate` GHA job —
      **RULE-11 prove-then-retire**: prove the prek + v2-step combo catches the same hard failures on PM before deleting
      the job (don't open a gap). repo: unified-trading-pm.
- [x] ✅ [SCRIPT] P1. **24h agentic contradiction RESOLUTION** — DONE 2026-06-10 (`plan-health-agent.yml` STEP 4). Added
      STEP 4 to the daily `plan-health-agent.yml` job: a non-empty `contradictions[]` / `doc_drift[]` result now
      DISPATCHES one `escalate-to-orchestrator.yml` run per finding with `wall_type=plan_health` → the built
      `plan_health` resolver (`server/escalation.py` + `agent-orchestrator/agents/plan-health.md`) resolves it on LDR,
      instead of only posting to Slack. Daily/dispatch only (`!= pull_request`); non-fatal per dispatch (a hiccup never
      reddens the badge); the conservative detector + the orchestrator's 503/no-headroom backpressure throttle volume.
      Verified: actionlint clean + YAML parses; a live contradiction (needed to see a real dispatch) is rare-by-design,
      so verification is logic+lint, not a forced finding. repo: unified-trading-pm (+ agent-orchestrator).
- [ ] [DOC] P3. Pre-existing frontmatter violation: `plans/active/ci_status_firestore_side_store_2026_06_10.md` is
      missing `locked_by` (another agent's new plan today). Staged-scoping means it only blocks a commit that touches
      that file — but it should be fixed at source. Owner: whoever owns that plan. repo: unified-trading-pm.

## Daily deep reconciler (operator direction 2026-06-12 — supersedes the daily-Haiku layer; see banner above)

- [ ] [CODE] P1. **`plan-reconciler` agent profile** (`agents/plan-reconciler.md` + `server/plan_health.py`
      `mode="reconcile"` on `POST /api/plan-health/dispatch`): one-shot, long-running (minutes→hour) opus/effort-max/
      thinking-on worker on a Max-plan slot. Inputs: hygiene digest + full plan/epic/issue-doc corpus + CLAUDE.md +
      codex SSOTs named by plans. Does: (1) runs the deterministic sweep itself (subsumes the Cloud Run job); (2)
      cross-checks plans ↔ epics ↔ codex ↔ issue docs ↔ CODE STATE (verify cited shas via
      `git merge-base --is-ancestor … origin/live-defi-rollout`, claimed files/flags via rg — grep-then-read); (3)
      APPLIES safe fixes: flip todos ONLY with verifiable on-origin evidence, `fix_frontmatter.py`/todo-format,
      mark-superseded banners; (4) files what it can't safely fix as issue docs + inbox pings; (5) one
      `docs(plans): daily reconciliation` commit direct to LDR (sanctioned carve-out) + Slack summary. HARD LIMITS: 12h
      grace (skip plans with newest git touch <12h — `git log -1 --format=%ct -- <plan>`); no deletions; no archival of
      `locked_by` plans; no codex rewrites beyond confidence-flagged rows in v1. repo: agent-orchestrator.
- [ ] [INFRA] P1. **Daily systemd timer on the central VM** (vm-0 `i-0c9b283b31d6b5ca7`): `plan-reconciler.timer` → curl
      `POST localhost:8765/api/plan-health/dispatch {"mode":"reconcile"}` (internal-secret authed; central has it
      hand-wired). Installer script in agent-orchestrator `scripts/` (idempotent, like install-orchestrator-service);
      billing-proof (no GHA dependency). repo: agent-orchestrator.
- [ ] [TEST] P1. **Prove on vm-e2e-test first**: seed a synthetic violation set (stale unflipped todo with an on-origin
      sha + a frontmatter violation + a >12h-old contradiction + a <12h-old plan that must be SKIPPED) → dispatch
      reconcile mode → verify the worker fixes exactly the eligible set, skips the fresh plan, commits one
      `docs(plans):` unit, files the unfixable finding. Then install the timer on central. repo: agent-orchestrator.
- [ ] [CI] P2. **RULE-11 prove-then-retire** (after ≥3 green reconciler runs on central): (a) drop the `schedule:`
      trigger + Haiku steps from `plan-health-agent.yml` (KEEP the `pull_request` `plan-health-gate` job + the
      escalate-on-gate-failure path); (b) delete the Cloud Run job `uts-prod-plan-hygiene-sweep` + its scheduler + TF
      (`deployment-service/terraform/gcp/hygiene_sweep_scheduler.tf`) + `cron_hygiene_sweep_entrypoint.sh`; (c) update
      CLAUDE.md § "Plan Hygiene" + `codex/11-project-management/plan-hygiene.md` to the timer-on-central model. repos:
      unified-trading-pm + deployment-service.

## Why it matters

A `docs(plans):` flip is the most common plan change and it bypasses full QG (prek-only) — so plan hygiene was
effectively ungated at commit time, and contradictions were detected-but-never-fixed. This closes both: cheap hygiene
gates every plan commit locally (staged-safe), and the daily LLM check becomes agentic (detect → resolve), not a
Slack-only report.
