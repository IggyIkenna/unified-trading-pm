---
doc_type: codex-ssot
title: Quickmerge Architecture
summary:
  The quickmerge commit pipeline — 6 stages (dep-validation → pre-flight audit → local QG → act simulation → auto-fix →
  push/PR) plus the .qg_last_passed_sha two-pass sentinel that lets --agent skip Pass-2 QG re-runs when the sentinel ==
  HEAD.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quickmerge, quality-gates, ci, workflows, infrastructure]
related: [/codex/06-coding-standards/quality-gates.md, /codex/08-workflows/ci-cd-flow.md]
created: 2026-03-27
authoritative_for: [quickmerge pipeline stages, quickmerge --agent .qg_last_passed_sha sentinel gate]
referenced_by: [/codex/08-workflows/ci-cd-flow.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Quickmerge Architecture

Quickmerge is the standard commit workflow for all service repos. It runs all quality checks automatically before
creating a PR.

## Pipeline Stages

1. **Dependency Validation** (10s) — Check dependencies vs main branch; cascade if different
2. **Pre-Flight Audit** (15s) — Codex compliance check, auto-fix violations
3. **Local Quality Gates** (30s) — Docker with ruff==0.15.0, basedpyright, pytest
4. **Act Simulation** (1-2 min) — Exact GitHub Actions simulation with environment-aware project ID
5. **Auto-Fix** (inline) — LLM agent fixes failures, max 3 attempts
6. **Push & PR Creation** (5s) — Automated PR with auto-merge enabled

**Total time:** ~2-5 minutes

## Usage

```bash
# Standard (dependencies match main)
bash scripts/quickmerge.sh "feat: description"

# Agent sessions (Claude Code / sub-agents):
bash scripts/quickmerge.sh "feat: description" --agent

# Differential branching (dependencies differ from main) — HUMAN-ONLY
bash scripts/quickmerge.sh "feat: description" --dep-branch "my-feature"
```

> **`--dep-branch` is HUMAN-ONLY** (per CLAUDE.md "Git discipline"). Quickmerge exits(1) when `--dep-branch` is combined
> with `--agent`. Sub-agents must NOT use this flag; if dep repos are dirty, commit + push directly to
> `live-defi-rollout` instead (per CLAUDE.md "DO NOT quickmerge when dep repos are dirty" rule).

## Environment Awareness

- Branch builds: `ENVIRONMENT=development` → uses `GCP_PROJECT_ID_DEV`
- Main builds: `ENVIRONMENT=production` → uses `GCP_PROJECT_ID`

## Sentinel integration

The two-pass model uses a `.qg_last_passed_sha` sentinel file to prevent redundant QG re-runs in `--agent` mode.

**Written by**: `unified-trading-pm/scripts/quality-gates-base/base-service.sh` — on a **full** QG pass (all steps, no
skip flags), the script writes the current `git rev-parse HEAD` to `.qg_last_passed_sha` on clean exit (commit
`a8b758c58`).

**Read by**: `quickmerge.sh` at line 819 in `--agent` mode — it compares the sentinel SHA against the current HEAD:

- **SHA match** → Pass 1 is guaranteed for the current HEAD; all Pass 2 QG re-runs are skipped (sentinel IS the
  guarantee).
- **SHA mismatch / sentinel absent** → `EXIT 1: "Run quality-gates.sh on current HEAD first"`.

**Partial runs do NOT write the sentinel** and therefore cannot unblock `--agent`:

- `--skip-tests`
- `--skip-codex`
- `--quick`

If quickmerge blocks with a SHA mismatch after you believe QG passed, check which flags were used: any partial-run flag
means the sentinel was not written. Run the full `bash scripts/quality-gates.sh` (no flags) to generate the sentinel.

See also: `/codex/06-coding-standards/quality-gates.md` § "Two-Pass Workflow Model".

## Why Not Standalone Quality Gates

Running `bash scripts/quality-gates.sh` directly skips dependency validation, environment detection, and PR creation.
Always use quickmerge.

See also: `06-coding-standards/quality-gates.md`
