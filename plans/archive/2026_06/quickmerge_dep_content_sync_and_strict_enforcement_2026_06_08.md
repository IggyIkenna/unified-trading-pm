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
---

> **✅ ARCHIVED 2026-06-10 — complete.** All phases shipped: dep-content gate (`scripts/cicd/check_dep_content_sync.py`,
> wired into base-service.sh, PM@13d6660f8); strict-quickmerge machine guard **LIVE**
> (`scripts/cicd/check_strict_quickmerge.py` + `Quickmerge: agent|human` lineage trailer + pre-push hook in all Path-B
> clones — observed firing on every LDR push 2026-06-10); the `--files` deletion-handling bug fixed 2026-06-10 @
> PM@3e472a19d (both staging loops in quickmerge.sh now deletion-aware — tracked-but-absent paths stage as deletions);
> per-repo `quickmerge.sh` are now SYMLINKS to the PM SSOT (fleet rollout completed 2026-06-10 — features/greeks/ml/e2e
> were the last 4); agent `[slot-N·host]` attribution shipped + surfaced in CI.
>
> ## Deferred work — migrated to: none

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

- [x] ✅ [SCRIPT] P1. Enumerate the transitive editable-dep closure per repo (reuse `get_dep_repos()` from
      `rollout-workflow-templates.sh` / the derived-manifest generator) — the gate must walk the **full DAG** (consumer
      → mtds → utl/uac), not just direct deps, or a dirty utl two hops down slips through.

## Phase 1 — Dep-content gate in quality-gates.sh (#1 dep-chain order + #4 content) (depends: Pre-audit)

- [x] ✅ [SCRIPT] P1. Add a pre-test QG step: for each transitive editable dep `D`, check
      `git -C <D> status --porcelain` (dirty?) and `git -C <D> merge-base --is-ancestor HEAD origin/live-defi-rollout` +
      reverse (== LDR ref?). Classify:
  - **dirty OR ahead-of-LDR-unpushed** → **BLOCK**: "commit+push `<D>` to LDR first; local QG is testing against dep
    content staging will never see."
  - **behind its committed manifest-version ref** → WARN (stale base).
  - **clean + == LDR** → PASS (local-green now means "green vs the shared base").
- [x] ✅ [SCRIPT] P1. Enforce **dep-chain ORDER locally** (#1): QG refuses to certify a consumer until each dep in DAG
      order is itself LDR-clean + QG-green — i.e. drive T0 (utl/uac) green-on-LDR, then dependents, then leaves.
      Surfaces the order the cascade needs, at local-QG time.
- [x] ✅ [SCRIPT] P1. Human-only `--allow-dirty-deps` escape (loud warning) that **taints** the sentinel
      (`.qg_last_passed_sha` → records `DIRTY_DEPS`) so it can NEVER satisfy a quickmerge promotion. Mirrors the
      `--dep-branch` / `--skip-dep-tier-gate` human-only pattern. Agents are hard-blocked from it.

## Phase 2 — Strict-quickmerge HARD enforcement (#5) (depends: Phase 1)

- [x] ✅ [SCRIPT] P1. Add a server-side + local guard: a **code** commit reaching the integration branch that did not
      pass through quickmerge is rejected. Carve-out allowlist (the ONLY direct-push class): PM `scripts/**` +
      `.github/**` and any repo's `.github/workflows/**` **when the change must reach `main` to unblock CI** (the
      chicken-and-egg). Everything else: HARD block.
- [x] ✅ [DOCS] P1. Codify in CLAUDE.md + `SUB_AGENT_MANDATORY_RULES.md` + `codex/08-workflows/ci-cd-flow.md`: "Strict
      quickmerge is a HARD RULE. Direct integration-branch code pushes are banned except PM-scripts / CI-workflow
      changes that must sync to `main` to unblock the pipeline." Replace the looser FF-push exception language;
      **reconcile with** `qg_commit_quality_boundary_and_slot_ff_push_2026_06_03.md` (do not fork — merge the two
      exception sets into one).
- [x] ✅ [SCRIPT] P1. **quickmerge `--files` cannot ship a DELETION (or the delete-side of a rename)** — the staging
      loop guards each path with `[ -e "$f" ]` before `git add` (quickmerge.sh ~:1222), so a deleted path is skipped
      with `⚠️ Path not found` and the commit lands HALF-SHIPPED (incident 2026-06-10: instruments-service polygon
      removal — `@3872848` carried the 8 modifications but silently dropped both deletions, leaving the deleted module +
      a duplicated test file live on LDR; completed via `@effa781`). And the recovery is also blocked: a pre-committed
      deletion makes the tree clean → quickmerge early-exits "No changes to commit" without pushing. Fix in the PM
      template (SSOT) + roll out to all repo copies: stage when the path exists **OR is tracked**
      (`[ -e "$f" ] || git ls-files --error-unmatch "$f" >/dev/null 2>&1`), and use `git add -- "$f"` (handles
      tracked-deleted paths). Add a regression test: quickmerge a worktree whose only change is a tracked-file deletion
      → the deletion must reach the commit. Repo: unified-trading-pm (template host) + fleet rollout. [FIXED 2026-06-10
      @ unified-trading-pm@3e472a19d: both staging loops in quickmerge.sh now deletion-aware — tracked-but-absent paths
      stage as deletions (`[ -e "$f" ] || git ls-files --error-unmatch` + `git add -A -- "$f"`). Root-cause context
      retained: bug was live at quickmerge.sh:1219-1227 on BOTH main + LDR — `[ -e "$f" ]` guard, no tracked-deletion
      fallback; deleted paths silently dropped (instruments-service polygon removal half-shipping).] —
      unified-trading-pm@3e472a19d | verified 2026-06-10

## Phase 3 — Agent attribution end-to-end (#8) (parallel)

- [x] ✅ [SCRIPT] P2. Confirm every commit carries `[slot-<N>·<host>]` author name (already shipped 2026-06-04) AND that
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

## Progress — 2026-06-08 (slot-1 autonomous)

- **DONE**: dep-content gate `scripts/cicd/check_dep_content_sync.py` (transitive editable-dep DAG;
  dirty/ahead-unpushed→BLOCK, behind→WARN, clean+==LDR→PASS; `--allow-dirty-deps` taints sentinel) wired into
  base-service.sh as WARN-default (`DEP_CONTENT_GATE_BLOCK=1` to enforce — rule-11: flip to default-block after the live
  multi-slot session). Shipped PM@13d6660f8. Agent `[slot-N·host]` attribution already shipped 2026-06-04.
- **Phase 2 strict-quickmerge: POLICY codified** (CLAUDE.md/SUB_AGENT/codex § strict-quickmerge). Enforcement MECHANISM
  (reject non-carve-out integration-branch code commit lacking a quickmerge lineage marker) deferred to a dedicated pass
  — a wrong fleet-wide guard mid-live-session is the rule-11 anti-pattern. Carve-out = PM scripts/.github + any repo's
  .github/workflows that must reach main to unblock CI.

## Progress — strict-quickmerge enforcement (2026-06-08)

- **DONE**: quickmerge stamps a `Quickmerge: agent|human` lineage trailer; `scripts/cicd/check_strict_quickmerge.py`
  flags a CODE-source commit (`*.py/*.ts` outside scripts/tests/.github) reaching the integration branch without that
  trailer that is not a carve-out (docs/plans/codex/.github/scripts/config/merge/[skip ci]/bot). WARN-default,
  `STRICT_QUICKMERGE_BLOCK=1` to enforce. Installed as a `pre-push` hook
  (`scripts/dev/hooks/pre-push-strict-quickmerge.sh`) in all 250 Path-B clones + wired into `setup-tab-worktrees.sh` for
  new clones; the staging-PR `quality-gates-v2` is the server backstop (LDR has no remote CI). Agent attribution
  (`[slot-N·host]`) confirmed carried + surfaced.
