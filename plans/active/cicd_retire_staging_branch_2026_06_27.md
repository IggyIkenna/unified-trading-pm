---
doc_type: plan
title: CI/CD retire the staging branch — re-home SIT onto LDR, single LDR→main path, ONE v2 (operator end-state)
summary:
  "OPERATOR END-STATE (directed + clarified 2026-06-27): a **GHA TOGGLE** decides, per repo, whether LDR promotes
  **through staging** or **straight to main**. The `staging` branch is **KEPT** (the toggle is REVERSIBLE — a
  major/breaking version bump or an operator decision still routes that repo THROUGH staging). The toggle changes ONLY
  the promote PATH, never the gates: **SIT, the quality-gate requirement, and the quickmerge-to-main requirement all
  remain the same**. PM already bypasses straight to main (and still runs plan-hygiene + the plan-health agent). For a
  direct repo, SIT re-homes onto a frozen LDR snapshot so the cross-repo breaking-change gate still runs on the
  actually-promoted content. Net: ONE gating v2 (not 2), SAME rigor, faster — drops the staging→main squash-divergence
  that made staging↔main diffs unresolvable. Supersedes cicd_staging_main_deadcode_retirement (that only removed the
  staging→main MERGE)."
status: draft
nature: process
stage: [meta]
repos: [unified-trading-pm, system-integration-tests]
scope: [engineer, admin]
tags: [cicd, WS-L, staging-removal, SIT-rehome, single-path, ldr_main, frozen-head, one-v2, D12]
related:
  [
    cicd_consolidated_remaining_2026_06_24.md,
    cicd_phase2_finalize_2026_06_27.md,
    cicd_staging_main_deadcode_retirement_2026_06_27.md,
    ../epics/infrastructure_master.md,
    ../../codex/08-workflows/ci-cd-flow.md,
    ../../codex/06-coding-standards/integration-testing-layers.md,
  ]
created: 2026-06-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-27
supersedes:
superseded_by:
depends_on: cicd_phase2_finalize_2026_06_27
source: operator directive 2026-06-27 (no staging branch; LDR→main only; stop running v2 twice)
assigned_role: infra
drift_direction: advance-code
asset_group: cross-asset
---

# CI/CD retire the staging branch

> **THE operator end-state for WS-L** (directed + clarified 2026-06-27): **a GHA TOGGLE per repo — LDR→main direct by
> default, OR through staging when a major/breaking bump / operator decision needs it.** The `staging` branch is KEPT
> (reversible). The toggle changes ONLY the promote PATH — **SIT + the quality-gate requirement + the quickmerge-to-main
> requirement all stay the same** (PM, already direct, still runs plan-hygiene + the plan-health agent). This CORRECTS
> the prior WS-L design which kept staging as a permanent "SIT/v2 sandbox" (`cicd_consolidated_remaining` lines
> 212/961/1115) and left v2 running 2× forever (LDR→staging v2 + LDR→main v2). **Model tier: OPUS-xhigh**
> (high-blast-radius — re-architects SIT + deletes the staging axis fleet-wide). **GATED —
> `depends_on: cicd_phase2_finalize`**: semver must be off staging first (Phase 2 removes the version-line/ semver
> dependency on the staging PR's v2-green; until then a breaking change still needs the staging semver path).
>
> **Why staging exists today (the ONLY pin):** SIT (cross-repo breaking-change tests) is triggered on the `staging`
> branch — `sit-gate.yml` locks staging, `sit-debounce-trigger.yml` assembles the pending set from `staging_versions`,
> the fleet runs SIT on staging content, emits `SIT_VALIDATED`. Everything else (semver, the staging→main merge) is
> already removable. **PM + agent-orchestrator ALREADY run no-staging** (`sit-debounce` `staging_excluded` set) — this
> plan extends that to all 21.
>
> **We keep the SIT SAFETY + KEEP the branch:** for a repo toggled to direct, SIT re-homes to run on a **frozen LDR
> snapshot** (the same snapshot the frozen-head promote uses), so the cross-repo breaking-change gate still runs — on
> the actual content being promoted. The `staging` branch is NOT deleted: it stays dormant and is re-entered whenever a
> repo is toggled back through staging (major/breaking/operator). Gates are identical on both paths.
>
> ---
>
> ## ⚠️ OPERATOR DESIGN CORRECTION (2026-06-27, slot-3) — TOGGLE OFF, do NOT delete the branch
>
> The operator clarified the end-state: **the `staging` branch is NOT deleted — its ROLE is toggled OFF and the toggle
> is REVERSIBLE.** Normal flow is **LDR→main direct** (staging bypassed, SIT re-homed onto the frozen LDR snapshot as
> above). **`staging` is RETAINED** as a dormant, operator-invokable path: a **major/breaking version bump OR an
> explicit operator decision** can still route a repo **through staging** for extra rigor (especially once
> live-trading). It must be **easy to revert to the old all-through-staging behavior** if ever needed.
>
> This SUPERSEDES the "delete the staging branch fleet-wide" framing in the tasks/success-criteria below — re-read those
> as **"toggle the staging ROLE off (per-repo `promotion_model=ldr_main`), keep the branch dormant + reversible."**
> Still apply: the SIT-re-home onto the frozen LDR snapshot, the frozen-head LDR→main promote, and ONE gating v2 on the
> direct path. **Gates are UNCHANGED on BOTH paths** — SIT + quality-gate + quickmerge-to-main for service repos,
> plan-hygiene + plan-health agent for PM. The thing actually removed is the staging→main **SQUASH** (the
> unresolvable-diff cause); the through-staging path is RETAINED for toggled-back repos and uses a clean merge, NOT the
> squash. The literal branch-deletion is replaced by a reversible toggle.
>
> **Mechanism = the existing per-repo `promotion_model` flag** (already `ldr_main` on 21 repos). Cutover = flip the
> flag; revert = unflip. A repo on `ldr_main` skips the LDR→staging drain entirely (see the new source-fix todo); a repo
> that needs staging (major/breaking/operator) is simply not `ldr_main`.
>
> **The monitoring MUST treat a toggled-off staging path as DORMANT, not STUCK** (the operator's "/repos tab + Slack +
> GHA shouldn't show these blocked" point):
>
> - [x] ✅ [SCRIPT] P1. `promotion_lag_monitor.py` skips the LDR↔staging directions for ALL `ldr_main` repos (was
>       PM-only) → no more "stuck staging" Slack/lag noise on cutover repos. **PM@90d125704** (PR #622). Reversible
>       (keyed on `promotion_model`; a repo routed through staging is monitored again).
> - [ ] [WORKFLOW] P1. **(source fix) `ldr-to-staging-promote.yml` must SKIP `ldr_main` repos** — they go LDR→main
>       direct, so no LDR→staging drain PR should be created for them. This removes the stuck-drain PRs + the CodeBuild
>       / `action_required` approval-gate blockages + the PAT-rate-limit churn AT THE SOURCE (today those PRs are
>       created then jam). Keep the drain running for non-`ldr_main` repos (the staging path for
>       major/breaking/operator).
> - [x] ✅ [UI] P2. deployment-ui **/repos** tab DONE 2026-06-27. A fleet-wide `staging_dormant_mode` toggle
>       (workspace-manifest top-level, reversible) suppresses every staging-direction signal for ALL repos:
>       `classifyStall` (repoCi.ts) now returns `none` for "LDR→staging drain behind" + "staging→main not promoting" +
>       "drain stalled" before the ldr-to-staging branch (fixed the ordering bug), the stg→main Promotion-hops pills
>       auto-suppress, and deployment-api exposes `staging_dormant_mode` per row (ManifestView.staging_dormant_mode).
>       Only LDR→main flashes; dep-order + pr-stuck still surface. +5 vitest tests, tsc+QG green. (deployment-ui +
>       deployment-api)
> - [x] ✅ [SCRIPT] P2. alert routing DONE 2026-06-27. `promotion_lag_monitor._main_direct_repos` reads the
>       `staging_dormant_mode` toggle → when on, EVERY repo is treated main-direct so the lag monitor + Slack skip ALL
>       staging directions fleet-wide (not just ldr_main). Reversible; +regression test. (unified-trading-pm)

## Tasks

- [ ] [WORKFLOW] P1. **Frozen-head LDR→main promote** (also fixes the live `action_required` jam — see the triage-queue
      root cause). The fleet bot snapshots the LDR tip to an immutable `promote/<repo>/<shortsha>` ref pushed with the
      write-collaborator PAT (not the App/bot), opens the LDR→main PR from THAT head, and arms auto-merge. **Gate:** a
      promote PR's head never moves under backmerge churn; v2 runs once on a stable, non-bot head (no
      `action_required`); auto-merge fires; the snapshot ref is deleted on merge.
- [ ] [WORKFLOW] P1. **Re-home SIT onto LDR.** Re-point `sit-gate.yml` / `sit-debounce-trigger.yml` /
      `system-integration-tests` to (a) assemble the cross-repo set from LDR tips (LDR ⊇ everything) instead of
      `staging_versions` + staging branches, (b) run SIT on the frozen LDR snapshot, (c) emit `SIT_VALIDATED` keyed to
      the LDR SHA. The LDR→main frozen-head promote gate consumes `SIT_VALIDATED` for breaking changes (the fleet bot
      already checks `breaking_pending` + `SIT_VALIDATED`). **Gate:** a deliberately-breaking cross-repo change is
      CAUGHT by SIT on LDR (no staging involved) and blocks the LDR→main promote until SIT-validated; a non-breaking
      change promotes on the single LDR→main v2.
- [ ] [SCRIPT] P1. **Drop the staging axis from the manifest + gates.** Remove `staging_versions` keying from
      `sit-debounce`/`sit-gate`/coherence; retire the `staging_excluded` special-case (all repos are now no-staging);
      `assert_version_coherence` no longer references staging. **Gate:** no gate reads `staging_versions`; coherence is
      `tag==Firestore` only (post Phase-2); QG green.
- [ ] [WORKFLOW] P1. **Delete the LDR→staging machinery.** Remove `ldr-to-staging-promote.yml`,
      `staging-backmerge-to-ldr.yml`, `staging-lock-check.yml`, `reconcile-staging-versions.yml`, and the
      `staging`-branch protection ruleset. **Gate:** grep proves no live caller of any deleted workflow; actionlint
      clean; the only promote path is LDR→main.
- [ ] [WORKFLOW] P1. **Fold in `cicd_staging_main_deadcode_retirement`** — `staging-to-main.yml`,
      `staging-conflict-ldr-main-fallback.yml`, `auto_resolve_version_promote.sh`, `auto_collapse_lossless_promote.sh`
      become dead once staging is gone; delete them here (no shims). **Gate:** the staging→main merge machinery no
      longer exists; that sibling plan is marked superseded.
- [ ] [INFRA] P1. **Delete the `staging` branch fleet-wide** (all 21 + PM/AO). ONLY after SIT-on-LDR is proven and the
      drain is removed. **Gate:** `git ls-remote --heads origin staging` returns empty for every repo; nothing breaks on
      the next promote cycle (verified T+1 cycle).
- [ ] [VERIFY] P1. **End-state proof.** (1) No repo has a `staging` branch. (2) A version bump + a normal change promote
      LDR→main with **exactly ONE gating v2** (the LDR→main PR) — confirm via run-count, no LDR→staging v2. (3) A
      breaking cross-repo change is still caught (SIT on LDR) before main. (4) The `action_required` jam class is gone
      (frozen head). **Gate:** all four proven on real promote cycles; update the WS-L design doc + `ci-cd-flow.md` to
      the no-staging end-state.

## Success criteria

- `staging` branch deleted fleet-wide; LDR→main is the single promote path; exactly ONE gating v2 per promotion.
- SIT (cross-repo breaking-change safety) still runs — on a frozen LDR snapshot, not a staging branch.
- The `action_required` promote jam is structurally eliminated (frozen, PAT-authored head).

## Codex SSOT updates

- `codex/08-workflows/ci-cd-flow.md` — replace the staging-in-the-flow model with the no-staging single-path LDR→main +
  SIT-on-LDR model; document the frozen-head promote.
- `codex/06-coding-standards/integration-testing-layers.md` — SIT now runs on the LDR snapshot, not staging.
- Correct the WS-L design block in `cicd_consolidated_remaining_2026_06_24.md` ("staging stays" → "staging removed").

## Progress Log

- 2026-06-27: Created on operator directive — the prior WS-L design kept staging permanently (SIT sandbox), which
  contradicted "no staging / LDR→main only / one v2". This plan re-homes SIT to LDR and deletes staging. Gated on
  Phase-2 finalize (semver-off-staging) + composes the frozen-head promote fix (which also clears the live
  action_required jam).
- 2026-06-27 (**STAGING-DORMANT toggle DONE** — operator screenshot ask "only LDR→main should be flashing; suppress
  staging alerts in this mode"). Shipped a reversible fleet-wide `staging_dormant_mode` toggle (workspace-manifest
  top-level): deployment-ui `classifyStall`/HopPills suppress all staging-direction signals (drain-behind, staging→main
  not-promoting, drain-stalled, stg→main hops) for ALL repos; deployment-api exposes the flag per row;
  `promotion_lag_monitor` global gate skips all staging directions in Slack/lag. Only LDR→main flashes; dep-order +
  pr-stuck still surface. The 21→23 `promotion_model=ldr_main` repos already had per-repo suppression; the toggle
  generalizes it to "this mode" + catches non-ldr_main repos (e.g. system-integration-tests). Live dashboard reflects it
  on the next deployment-ui/api deploy. **Remaining tasks** (frozen-head promote, SIT-rehome onto LDR, drop staging
  axis, delete LDR→staging machinery, delete the staging branch) are the deeper staging-retirement — the SIT-rehome
  carries the **OPERATOR CHECKPOINT before the live SIT fleet-wide flip**.
