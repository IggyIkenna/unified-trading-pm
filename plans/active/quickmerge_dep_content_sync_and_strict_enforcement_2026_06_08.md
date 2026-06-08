---
title: Quickmerge dep-content sync (vs LDR, not version) + strict-quickmerge HARD enforcement
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
execution_scope: local-only
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
created: 2026-06-08
orchestrated_by: plans/active/cicd_contract_hardening_2026_06_01.md
related_plans:
  - plans/active/qg_commit_quality_boundary_and_slot_ff_push_2026_06_03.md
  - plans/active/worktree_ldr_unification_2026_06_08.md
  - plans/active/ci_local_qg_parity_2026_06_08.md
source:
  - chat design session 2026-06-08 (operator + vm-planning)
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Quickmerge dep-content sync + strict enforcement

> **Orchestrated by** `cicd_contract_hardening_2026_06_01.md`. Independent of the cascade jam; build in parallel. **Core
> principle: LDR is the SSOT.** Local-green is only meaningful if your local dep tree == LDR's dep content.

## Problem (what we found)

Two gaps, both confirmed against the live machinery:

1. **The dep gate is version-typed, not content-typed.** `quickmerge` STAGE 1.6 compares the consumer's pinned dep
   **version numbers** vs `staging_versions`; STAGE 1.7 checks dep `ci_status` tier. Neither inspects **content**. But
   local QG resolves deps via **editable path** (`tool.uv.sources … path = "../X", editable = true`), so it builds
   against your **working-tree** copy of every dep. Result: an **uncommitted or LDR-divergent** dep edit (same version)
   → consumer green locally, red at staging, and **both gates wave it through** because the version never changed. The
   only existing protections are discipline ("never quickmerge with dirty deps") + the human-only `--dep-branch`, with
   no machine gate.

2. **Strict-quickmerge is a written rule, not an enforced one.** Direct LDR pushes that skip quickmerge dodge 1.6/1.7
   entirely and never open a staging PR ("pile up behind main"). There is no HARD block on bypassing quickmerge for
   code.

## Decision

- **Gate dep CONTENT vs LDR** (not version): every editable dep worktree must be **clean and == its
  `origin/live-defi-rollout` ref** before a consumer QG/quickmerge counts. This converts an "invisible local edit" into
  a tracked, committed dep — at which point 1.6/1.7 + the cascade already close the staging gap. The gate does **not**
  need to check staging; it needs to refuse _invisible_ deps.
- **Strict quickmerge = HARD block** on direct-to-integration code pushes, with **one carve-out**: changes to **PM repo
  scripts / CI workflow files that must reach `main` to unblock the pipeline** (the chicken-and-egg case) may go direct.

## Pre-audit

- [ ] [SCRIPT] P1. Enumerate the transitive editable-dep closure per repo (reuse `get_dep_repos()` from
      `rollout-workflow-templates.sh` / the derived-manifest generator) — the gate must walk the **full DAG** (consumer
      → mtds → utl/uac), not just direct deps, or a dirty utl two hops down slips through.

## Phase 1 — Dep-content gate in quality-gates.sh (#1 dep-chain order + #4 content) (depends: Pre-audit)

- [ ] [SCRIPT] P1. Add a pre-test QG step: for each transitive editable dep `D`, check `git -C <D> status --porcelain`
      (dirty?) and `git -C <D> merge-base --is-ancestor HEAD origin/live-defi-rollout` + reverse (== LDR ref?).
      Classify:
  - **dirty OR ahead-of-LDR-unpushed** → **BLOCK**: "commit+push `<D>` to LDR first; local QG is testing against dep
    content staging will never see."
  - **behind its committed manifest-version ref** → WARN (stale base).
  - **clean + == LDR** → PASS (local-green now means "green vs the shared base").
- [ ] [SCRIPT] P1. Enforce **dep-chain ORDER locally** (#1): QG refuses to certify a consumer until each dep in DAG
      order is itself LDR-clean + QG-green — i.e. drive T0 (utl/uac) green-on-LDR, then dependents, then leaves.
      Surfaces the order the cascade needs, at local-QG time.
- [ ] [SCRIPT] P1. Human-only `--allow-dirty-deps` escape (loud warning) that **taints** the sentinel
      (`.qg_last_passed_sha` → records `DIRTY_DEPS`) so it can NEVER satisfy a quickmerge promotion. Mirrors the
      `--dep-branch` / `--skip-dep-tier-gate` human-only pattern. Agents are hard-blocked from it.

## Phase 2 — Strict-quickmerge HARD enforcement (#5) (depends: Phase 1)

- [ ] [SCRIPT] P1. Add a server-side + local guard: a **code** commit reaching the integration branch that did not pass
      through quickmerge is rejected. Carve-out allowlist (the ONLY direct-push class): PM `scripts/**` + `.github/**`
      and any repo's `.github/workflows/**` **when the change must reach `main` to unblock CI** (the chicken-and-egg).
      Everything else: HARD block.
- [ ] [DOCS] P1. Codify in CLAUDE.md + `SUB_AGENT_MANDATORY_RULES.md` + `codex/08-workflows/ci-cd-flow.md`: "Strict
      quickmerge is a HARD RULE. Direct integration-branch code pushes are banned except PM-scripts / CI-workflow
      changes that must sync to `main` to unblock the pipeline." Replace the looser FF-push exception language;
      **reconcile with** `qg_commit_quality_boundary_and_slot_ff_push_2026_06_03.md` (do not fork — merge the two
      exception sets into one).

## Phase 3 — Agent attribution end-to-end (#8) (parallel)

- [ ] [SCRIPT] P2. Confirm every commit carries `[slot-<N>·<host>]` author name (already shipped 2026-06-04) AND that
      **CI workflows surface it**: `head_commit.author.name` flows into `quality-gates-v2` / promote / SIT logs + Slack
      alerts, so a failing run names the agent. Add the author-name to the CI run summary + the orchestrator alert
      payload.

## Success criteria

- A consumer with a dirty/LDR-divergent editable dep **cannot** get a clean QG sentinel (proven on a representative
  CONSUMER repo, not just PM — rule 11).
- A direct code push to LDR (non-carve-out) is rejected locally and server-side.
- Dep-order local-QG sweep drives T0→dependents→leaves green in order.
- CI logs + Slack name the committing agent on every run.

## Codex SSOT updates

`codex/06-coding-standards/quality-gates.md` (dep-content gate), `codex/08-workflows/ci-cd-flow.md` (strict-quickmerge
HARD rule + carve-out), CLAUDE.md § Git discipline + § Quality Gates, `SUB_AGENT_MANDATORY_RULES.md` § ship discipline.
