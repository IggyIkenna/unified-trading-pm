---
doc_type: issue
title:
  execution-service's CONTRIBUTING.md is a stale instruments-service copy describing a retired PR-branch quickmerge
  workflow
summary: >-
  CONTRIBUTING.md in execution-service is titled "Contributing to Instruments Service", names `instruments_service/` as
  the source tree, and describes an obsolete PR-branch quickmerge workflow (auto/timestamp branches, `gh pr` auto-merge,
  `main` as the base branch) that no longer matches the current git/ship workflow (commit directly on
  `live-defi-rollout` via named-file staging, `--agent`/`--isolated` quickmerge, `docs(plans):` plan-flip). It also
  repeatedly instructs `git add -A`, which CLAUDE.md's "Commit + Push + Flip" HARD RULE bans.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [execution-service]
scope: [engineer]
tags: [docs, stale-doc, quickmerge, contributing-guide, git-discipline]
related:
  [
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch16_2026_08_13.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-14
last_updated: "2026-08-14"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
effort: medium
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found while verifying quickmerge `--isolated` end-to-end on execution-service for
  `plans/active/infra_satellite_ao_dispatch_batch16_2026_08_13.md`'s "Verify quickmerge isolation on a second (service)
  repo" todo (Source: `plans/archive/2026_08/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`).
  Needed a small, real, safe content change to ship through the isolated path and this doc's `git add -A` instances were
  the first thing that surfaced — worth its own todo rather than a full silent rewrite mid-task.
depends_on: []
context_scope: [execution-service/CONTRIBUTING.md, /codex/12-agent-workflow/commit-push-flip-rule.md]
---

# execution-service's CONTRIBUTING.md never got adapted from instruments-service

## What I found

`execution-service/CONTRIBUTING.md` (229 lines):

- Title: `# Contributing to Instruments Service` — wrong service.
- "File Locations" section: `Source code: instruments_service/`, `Config: instruments_service/config.py` — wrong repo
  entirely; execution-service's own tree is never mentioned.
- The whole "Committing Changes" / "Working with Multiple Agents" / "Troubleshooting" sections describe a **PR-branch
  quickmerge model**: `git checkout main`, timestamped `auto/<ts>` branches, `gh pr list`/`gh pr checks`, auto-merge.
  The current workflow (per `.claude/CLAUDE.md` → "Git discipline + shipping pipeline") commits directly on
  `live-defi-rollout` via `scripts/quickmerge.sh "<msg>" --agent --files '<paths>'`; there is no PR branch, no `main`
  base, no `gh pr` step in the standard path.
- Three call sites instruct `git add -A` (lines ~87, ~186, ~195 pre-fix) — CLAUDE.md's "Commit + Push + Flip" HARD RULE
  bans `git add .`/`-A` (stage by name only), precisely because a blanket add risks staging a peer's foreign WIP or an
  unintended file in a shared multi-agent checkout.

## Why it matters

A contributor (human or agent) following this file literally would: work on the wrong base branch model, expect a
`gh pr` review step that doesn't exist in the standard flow, and stage files with `-A` — the exact anti-pattern
CLAUDE.md's multi-agent-safety section calls out as how a peer's dirty WIP gets swept into an unrelated commit. It is
also just wrong on its face (wrong service name), which erodes trust in every other doc in the repo.

## What was fixed inline (small, same-turn)

The three `git add -A` instances were replaced with named-file staging (`git add <changed-files>`, with a comment citing
the HARD RULE) and a warning banner was added atop the "Committing Changes" section pointing at `.claude/CLAUDE.md` as
the authoritative workflow and at this issue doc for the fuller audit — unified-trading-pm's fix rule ("too big for a
line → todo") applied literally: fix what's small in place, track what's a real rewrite.

## Recommended decision

Rewrite `CONTRIBUTING.md` end-to-end against the current `.claude/CLAUDE.md` workflow: correct title/service name,
correct "File Locations" (execution-service's actual package layout), replace the PR-branch section with the
`--agent`/`--files`/`--isolated` quickmerge flow, and correct "Working with Multiple Agents" against the current
per-slot-worktree model (`/codex/05-infrastructure/per-tab-worktrees.md`) rather than "each session works on its own PR
branch". Worth checking whether other service repos share the same instruments-service-derived template (this may not be
execution-service-only).

## Todos

- [x] ✅ [DOC] P3. **DONE 2026-08-15 — rewrote `execution-service/CONTRIBUTING.md` end-to-end** against the current
      `.claude/CLAUDE.md` workflow: title (`Contributing to Execution Service`), File Locations (actual
      `execution_service/` package layout — adapters/algo_library/defi_execution/sports_execution/trade_execution/etc.,
      plus the real per-domain test dirs), the quickmerge section (direct commit on `live-defi-rollout` via
      `--agent --files`, no PR branch, no `gh pr` step), Branch Protection (LDR is the shared trunk; `main` is a
      promoted projection, not the base), and Working with Multiple Agents/Sessions (per-slot-worktree model, citing
      `/codex/05-infrastructure/per-tab-worktrees.md`, replacing the old "each session works on its own PR branch"
      framing). Evidence: `execution-service@72fbc742da`.
- [x] ✅ [DOC] P3. **DONE 2026-08-15 — grepped every repo checkout under `.tabs/15/` for `CONTRIBUTING.md`.** Of the 7
      live repos that have one (`deployment-service`, `execution-service`, `instruments-service`,
      `market-data-processing-service`, `market-tick-data-service`, `unified-api-contracts`, `unified-trading-library`),
      3 are byte-identical 219-line copies of the same stale instruments-service-derived template found in
      execution-service (title `# Contributing to Instruments Service`, `git checkout main` + `auto/timestamp`
      PR-branch + `gh pr` workflow, `Source code: instruments_service/`, 3× `git add -A`): **`deployment-service`,
      `market-data-processing-service`, `unified-trading-library`**. Filed as todos 3-5 below, one per repo.
      `instruments-service`'s own copy is correct (it IS about itself). `market-tick-data-service` and
      `unified-api-contracts` have their own distinct, non-stale content. The
      `*.stale-pre-history-rewrite-20260805T112618Z` shadow checkouts were excluded — not live working repos.
- [x] ✅ [DOC] P3. **DONE 2026-08-15 — rewrote `deployment-service/CONTRIBUTING.md` end-to-end** against the current
      `.claude/CLAUDE.md` workflow, following the `execution-service@72fbc742da` pattern: title
      (`Contributing to Deployment Service`), File Locations (actual `deployment_service/` package layout plus
      `terraform/`, `infra/`, `cloud-build/`, `packer/`, `deploy/`, `functions/`, `contracts/`, `runbooks/`, `grafana/`,
      `audit/`, `scripts/`, `tools/`), the quickmerge section (direct commit on `live-defi-rollout` via
      `--agent --files`, no PR branch, no `gh pr` step), Branch Protection, and Working with Multiple
      Agents/Sessions (per-slot-worktree model, citing `/codex/05-infrastructure/per-tab-worktrees.md`). Evidence:
      `deployment-service@514e0f8ff9`.
- [ ] [DOC] P3. Rewrite `market-data-processing-service/CONTRIBUTING.md` end-to-end, same pattern as
      `execution-service@72fbc742da` — repo: market-data-processing-service.
- [ ] [DOC] P3. Rewrite `unified-trading-library/CONTRIBUTING.md` end-to-end, same pattern as
      `execution-service@72fbc742da` — repo: unified-trading-library.

## Progress Log

- **2026-08-14 (slot-20, infra)**: filed while shipping the `--isolated` quickmerge verification for
  `infra_satellite_ao_dispatch_batch16_2026_08_13.md`. Inline fix (the `git add -A` instances + banner) shipped in the
  same commit as the verification ship; the full rewrite is left as tracked follow-up, not done here.
- **2026-08-15 (slot-15, interactive)**: picked up todo 1. Shipped the full rewrite via isolated-worktree quickmerge
  (`--agent --files 'CONTRIBUTING.md' --isolated`); full quality-gate re-gate passed (185s, 8503 tests). Landed on
  `live-defi-rollout` at `72fbc742da`, verified `ahead=0` against origin post-pull. Along the way found the caller-tree
  `unified-api-contracts` dependency clone was 1 commit behind `origin/live-defi-rollout` (clean tree, no local WIP — a
  plain staleness issue, safe `git pull --ff-only`), which had been blocking quickmerge's Stage-1 dependency validation;
  fast-forwarded it, no conflict. Todo 2 (cross-repo grep for the same stale template) remains open and unstarted — not
  attempted this session.
- **2026-08-15 (slot-15, interactive, cont'd)**: picked up todo 2. Grepped all 7 live repo checkouts with a
  `CONTRIBUTING.md`; found 3 more byte-identical copies of the stale template beyond execution-service:
  deployment-service, market-data-processing-service, unified-trading-library. Filed todos 3-5, one per repo. First ship
  attempt used `--isolated`; it failed the `check_evidence_backed_completion` gate because the isolated worktree
  (`/tmp/qm-iso-1603818/.tabs/15/unified-trading-pm/`) has no sibling `execution-service` checkout to resolve the
  pre-existing `execution-service@72fbc742da` citation against — a structural limitation of isolated mode in this
  multi-repo workspace, not a defect in the edit. Re-shipping from the main checkout (non-isolated) instead, since no
  other session has this file dirty.
- **2026-08-15 (slot-15, interactive, cont'd)**: picked up todo 3. Rewrote `deployment-service/CONTRIBUTING.md`
  end-to-end following the `execution-service@72fbc742da` pattern; shipped via quickmerge (non-isolated, `--agent
  --files 'CONTRIBUTING.md'`), full quality gate passed (docs-only fast path, 24s). Landed on `live-defi-rollout` at
  `514e0f8ff9`, post-push ancestry verified. Todos 4-5 (market-data-processing-service,
  unified-trading-library) remain open — not attempted this session.
