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
- [ ] [SCRIPT] P1. **24h agentic contradiction RESOLUTION** — the daily plan-health agent is REPORT-ONLY; wire it so a
      non-empty `contradictions[]` / `doc_drift[]` result DISPATCHES each finding to the built `plan_health`
      orchestrator path (`POST /api/escalate wall_type=plan_health` → `agents/plan-health.md` worker resolves on LDR),
      instead of only posting to Slack. Reuse `escalate-to-orchestrator.yml`. repo: unified-trading-pm (+
      agent-orchestrator).
- [ ] [DOC] P3. Pre-existing frontmatter violation: `plans/active/ci_status_firestore_side_store_2026_06_10.md` is
      missing `locked_by` (another agent's new plan today). Staged-scoping means it only blocks a commit that touches
      that file — but it should be fixed at source. Owner: whoever owns that plan. repo: unified-trading-pm.

## Why it matters

A `docs(plans):` flip is the most common plan change and it bypasses full QG (prek-only) — so plan hygiene was
effectively ungated at commit time, and contradictions were detected-but-never-fixed. This closes both: cheap hygiene
gates every plan commit locally (staged-safe), and the daily LLM check becomes agentic (detect → resolve), not a
Slack-only report.
