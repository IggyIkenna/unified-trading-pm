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
> - [x] ✅ [WORKFLOW] P1. **(source fix) `ldr-to-staging-promote.yml` SKIPS main-direct repos** DONE 2026-06-27. The
>       drain's REPOS list now excludes repos that are main-direct — the fleet-wide `staging_dormant_mode` toggle OR a
>       per-repo `promotion_model=ldr_main`. No LDR→staging drain PR is created for them, clearing the stuck-drain PRs +
>       CodeBuild `action_required` + PAT churn AT THE SOURCE (pairs with the UI/Slack suppression). Breaking-change
>       safety retained on the LDR→main fleet promoter (SIT part-2 detect_breaking_change on main..LDR). Reversible:
>       flip `staging_dormant_mode` off / unset `ldr_main` → drain resumes (through-staging for
>       major/breaking/operator). (unified-trading-pm)
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
- 2026-06-27 (**SIT-rehome — adversarially-verified design + a CRITICAL SAFETY FINDING; NOT yet implemented, see why**).
  Ran the `sit-rehome-map` ultracode workflow (map → design → adversarial-verify). It uncovered that the SIT-rehome is a
  high-stakes SAFETY re-architecture with an UNBUILT prerequisite — so it is NOT safe to rush. **🔴 SAFETY FINDING (H2,
  big finding — cross-repo breaking-change gate):** for the 21 `ldr_main` fleet repos, the cross-repo breaking gate is
  effectively BROKEN today: (a) `breaking_pending` (the `ldr-to-main-promote-fleet.yml` SIT-gate part-1) is NEVER SET
  for them — it's only set by `update-repo-version.yml` off the semver-agent's `push:[staging]`, but `ldr_main` repos
  are excluded from the LDR→staging drain, so their content never reaches staging → part-1 is dead; (b) SIT-gate part-2
  requires `ci_status==SIT_VALIDATED && LDR_TREE==STAGING_TREE`, but NOTHING ever writes `SIT_VALIDATED` (the SIT
  cascade emits only `sit-passed`/`staging-validated`; `staging-to-main` only RESETS it) → part-2 can never PASS for a
  genuine breaking change (legit breaking changes are STUCK) AND it FAILS-OPEN at `:382-383` on a differ error / stale
  `STAGING_TREE` (so some breaking changes LEAK to main unvalidated). Net: ldr_main breaking changes are both stuck and
  leaky. **The SIT-rehome closes this** by (1) running SIT on a frozen LDR snapshot, (2) actually EMITTING
  `ci_status=SIT_VALIDATED` + a `sit_validated_tree` fingerprint keyed to the LDR SHA, (3) re-pointing part-2 to read
  `SIT_VALIDATED`+tree from **Firestore live** (NOT the stale manifest cache `:316` — the adversarial verdict's fatal
  correction H3) and tightening the fail-open to BLOCK for ldr_main (H2). **PREREQUISITE (H4):** the **frozen-head
  promote** task above (immutable `promote/<repo>/<shortsha>` ref) MUST exist first, else SIT validates a HEAD that
  drifts under backmerge churn (the `action_required` jam). **Corrected step order (verified):** (0) confirm Phase-2
  landed [DONE]; (1) SIT-on-frozen-LDR emits SIT_VALIDATED+tree to Firestore keyed to the frozen ref; (2) persist
  `sit_validated_tree` in `ci_status_store.py` (clear-on-status-change, unit-tested) + `ci-status-update.yml`; (3)
  part-2 reads SIT_VALIDATED+tree from Firestore live, then swaps `STAGING_TREE`→`sit_validated_tree`; (4) tighten
  part-2 fail-open→BLOCK for ldr_main (part-1 is no longer a backstop); (5) re-point `sit-gate`/`sit-debounce`/SIT-repo
  to assemble from LDR tips + drop `staging_versions` keying (the operator-scoped flip — KEEP staging
  dormant/reversible); (6) codex SSOT update. **Why not done in this session:** it is a fleet breaking-change gate with
  an unbuilt prerequisite (frozen-head promote) — implementing it correctly is its own careful effort; rushing it risks
  leaking breaking changes OR jamming the fleet promote. The verified design above IS the implementation spec; execute
  it as the next focused unit (frozen-head promote → steps 1-6). Full design + line-cited verdict: workflow
  `sit-rehome-map` (run wf_6d2bbbbf-1b0).
- 2026-06-27 (**SIT-rehome EXECUTION started — steps 2/3 landed + App-token jam fix shipped**). Operator lifted the
  SIT-live-flip checkpoint ("do all of it no shortcuts or waiting for approval") and asked to fold in a sibling agent's
  App-token finding. Progress:
  - ✅ **STEP 3 (store)** — `ci_status_store.py` persists `sit_validated_tree` (clear-on-any-non-SIT_VALIDATED-status, the
    load-bearing safety) + `--sit-validated-tree` CLI + `ci-status-update.yml` threading + 2 unit tests. Landed
    (PM@375b967).
  - ✅ **STEP 2 (producer)** — `full-workspace-sit.yml` stamps `ci_status=SIT_VALIDATED` + `sit_validated_tree` per repo on
    a GREEN cross-repo run, keyed to each sibling's LDR SHA/tree. **Key finding: full-workspace-sit ALREADY assembles
    from LDR tips** (clones `live-defi-rollout`), so "re-home SIT onto LDR" is already true — STEP 5 does NOT need to
    repoint sit-debounce/sit-gate (those stay for the dormant staging path); the only missing trigger is an on-block SIT
    dispatch from the fleet promoter + the nightly cron. Landed (system-integration-tests@1e92c0a). Additive (writes the
    signal only; no gate change until STEP 4).
  - ✅ **App-token promote deadlock fix (folded in per operator; sibling-agent finding CONFIRMED)** — `gh pr create` in
    `ldr-to-main-promote-fleet.yml` inherited the uts-ci-poller **App** token → promote PR lands quality-gates-v2 in
    `action_required` → required `pull_request` check never auto-runs → PR deadlocks BLOCKED. Verified structurally
    (line 474 inherits `GH_TOKEN`=App token; reactive force-dispatch at :546-572 was only a band-aid) + the sibling's
    A/B on a HELD head SHA (App-created→action_required; PAT-created→ran→merged). Fix: create the PR with
    `GH_PAT_FOR_ARM` (App token stays for rate-limited reads; auto-merge was already PAT). Shipped via `.github/**`
    direct-push carve-out (PM@860f64d0c; quickmerge sentinel lost the race to PM cron HEAD-churn twice). This is the
    `action_required`-jam half of the frozen-head task — frozen-head's REMAINING safety value (head can't drift between
    SIT-validate and merge) is STEP 1, still pending.
  - **Sibling promoters with the SAME App-token `gh pr create` (follow-ups, NOT changed — scoped decision):**
    `ldr-to-main-promote.yml` (PM-singular, line 138) has NO PAT wired + the sibling agent observed PM promotes work
    normally (likely because PM's heavily-churned LDR head gets v2 from `push` events, satisfying the required check by
    SHA) → do NOT speculatively destabilize the working promoter; watch-item, same 2-line fix if it ever jams.
    `ldr-to-staging-promote.yml` (staging drain, line 303) is DORMANT under `staging_dormant_mode` so the bug is moot;
    apply the same PAT-create fix when/if staging is reactivated (reversible path).
  - **IN PROGRESS — coupled STEPS 1+4+5** (all in `ldr-to-main-promote-fleet.yml` + a `get-doc` read primitive in
    `ci_status_store.py`): frozen-head promote (immutable ref so merged tree == SIT-validated tree, closing the TOCTOU),
    consumer reads SIT_VALIDATED+`sit_validated_tree` from **Firestore-live** and fail-CLOSED for ldr_main, on-block SIT
    dispatch. Adversarial-verify before landing (partial = fleet jams breaking changes).
- 2026-06-27 (**STEPS 1+4+5 IMPLEMENTED → adversarially verified → REVERTED (2 CRITICAL gaps caught pre-merge); operator
  decision required**). Implemented the coupled unit (atomic LDR sha+tree read; Firestore-live fail-CLOSED consumer gate;
  on-block SIT dispatch; frozen-head `promote/<repo>` ref) and ran 3 read-only adversarial sub-agents (safety/liveness/
  mechanics) BEFORE landing. Two CRITICAL findings, both DIRECTLY VERIFIED in the code, make it unsafe to ship as specced:
  (1) **liveness** — `resolve_status` no-downgrade (`SIT_VALIDATED:3 < MAIN_GREEN:4`) REJECTS every SIT_VALIDATED write
  once a repo is MAIN_GREEN → `sit_validated_tree` never re-written → the gate would jam every ldr_main repo on its 2nd
  breaking change forever; (2) **safety** — `run_cross_repo_invariants.sh` validates only 5 `REQUIRED_SIBLINGS` but the
  STEP 2 producer stamps SIT_VALIDATED on all 21 ldr_main repos → a breaking change in any of the other 16 promotes
  ungated (forged certificate). Plus HIGH design issues: mutable vs per-SHA promote ref; per-repo fingerprint can't
  express the cross-repo combination; differ `--source-dir` blind guess → silent false-negative. **Action:** reverted the
  uncommitted consumer+frozen-head (diff backed up `scratchpad/fleet_promoter_step145.diff`); the inert shipped building
  blocks (producer/store/get-doc/token-swap) stay. Full analysis + the corrected-design requirements + the operator's
  coverage-guarantee fork (A expand SIT to 21 / B scope to 5 / C workspace-digest) →
  `plans/active/issues/sit_rehome_safety_gate_gaps_2026_06_27.md`. **NOTIFYING OPERATOR** (big cross-repo safety-gate
  finding). The current state is safe (breaking ldr_main changes stay conservatively blocked, not leaked).
