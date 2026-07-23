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
status: superseded
nature: process
asset_group: cross-asset
stage: [meta]
repos: [unified-trading-pm, system-integration-tests]
scope: [engineer, admin]
tags: [cicd, WS-L, staging-removal, SIT-rehome, single-path, ldr_main, frozen-head, one-v2, D12]
related:
  [
    /plans/archive/2026_06/cicd_consolidated_remaining_2026_06_24.md,
    /plans/archive/2026_06/cicd_phase2_finalize_2026_06_27.md,
    /plans/archive/2026_06/cicd_staging_main_deadcode_retirement_2026_06_27.md,
    ../epics/infrastructure_master.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/06-coding-standards/integration-testing-layers.md,
  ]
created: 2026-06-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
last_updated: 2026-06-30
locked_by: live-defi-rollout
locked_since: 2026-06-27
supersedes:
superseded_by: cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
depends_on: cicd_phase2_finalize_2026_06_27
source: operator directive 2026-06-27 (no staging branch; LDR→main only; stop running v2 twice)
assigned_role: infra
drift_direction: advance-code
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
>   - ↳ **Follow-up DONE 2026-06-28 — deployment-ui@81375bd.** Operator /repos report (2026-06-27) found residual
>     staging framing despite the above: HopPills "LDR→stg 35f / stg→main 14f" still rendered and the promotion-blocked
>     panel still read "staging→main draining cleanly" (the original suppression lived ONLY in `classifyStall`→cell="—",
>     so a stale served bundle / the un-guarded HopPills component + the never-reframed panel leaked staging). Hardened:
>     extracted `isStagingDormant(row)` as the SSOT predicate (repoCi.ts) now used by `classifyStall` + HopPills (own
>     guard, belt-and-suspenders) + StallReasonCell + the panel; panel title + empty-state reframe to **LDR→main** /
>     "Staging dormant — LDR→main direct; no staging→main promotion" when the fleet is dormant. Regression coverage
>     added (the gap that let it ship wrong): +4 `isStagingDormant` vitest unit tests + a dormant mock repo
>     (alerting-service, 35f/14f staging deltas + drain_stalled) + **3 e2e specs** (hops+drain-chip suppressed under
>     dormant; STILL shown for the non-dormant agent-orchestrator case; panel reframes to LDR→main). **pw:L2 ✓ (43 e2e
>     green)** + tsc+ESLint+84 vitest+build green. ⚠️ Display only SHOWS once the served deployment-ui bundle redeploys
>     (Build-LDR opt-in stamped on the commit). (deployment-ui)
>   - ↳ **DESIGN CORRECTION DONE 2026-06-28 — deployment-ui@d98a753.** Operator: don't HIDE the dormant staging signals
>     — SHOW them muted. The 81375bd cut suppressed them (HopPills→null, hops cell→"—", classifyStall→"none"), which
>     threw away real data and meant flipping staging back on would need a structural change. Reworked so dormancy is
>     purely a STYLING concern: `classifyStall` is now dormant-AGNOSTIC (reports the real git-delta kind); the render
>     layer (HopPills / StallReasonChip / StallReasonCell) calls `isStagingDormant(row)` to render the staging hops +
>     stall reason + drain-stalled **MUTED** (grey via `TONE_TEXT.gray`, never red) + a "dormant · ignored" tag — flip
>     staging relevant → the same cells return to red-when-behind, zero structural change. Tests updated to the new
>     contract (classifyStall dormant→real kind not "none"; e2e: dormant SHOWS muted+tagged vs the non-dormant
>     agent-orchestrator showing the SAME signal RED). **pw:L2 ✓ (43 e2e green)** + tsc+ESLint+910 vitest+build green.
>     Same redeploy caveat below. (deployment-ui)
> - [ ] ⚠️ [SCRIPT] P1. **REDEPLOY the `deployment-dashboard` service — the dashboard fixes have NEVER reached the
>       operator's live /repos.** Root-cause of the operator's persistent stale-staging view: the live
>       `deployment-dashboard` Cloud Run service serves image `:07d09a56` (NOT a current-history commit — genuinely
>       stale, predates even the classifyStall fix). That service is built ONLY by
>       `deployment-api/cloudbuild-dashboard.yaml` → `Dockerfile.dashboard` (a SINGLE image = deployment-api FastAPI
>       HEAD + the deployment-ui Vite SPA baked from `deployment-ui-src/` staged at submit time). The earlier
>       "deployment-ui REDEPLOYED 8d5022ce" built the **standalone deployment-ui nginx image**
>       (`deployment-ui/cloudbuild.yaml`, SHORT_SHA=b0d8eac) — that artifact does NOT feed `deployment-dashboard`, so
>       NONE of the dormant fixes ever went live. **Runbook (operator/new-tab — needs the live SHORT_SHA convention used
>       for rev-70):** from `deployment-api/` (clean @ LDR tip 920d98e), stage the deployment-ui tree at
>       `./deployment-ui-src/` (`git -C ../deployment-ui archive d98a753 | tar -x -C deployment-ui-src` — the
>       dormant-display tip), then
>       `gcloud builds submit . --config=cloudbuild-dashboard.yaml --region=asia-northeast1 --substitutions=_UI_BRANCH=live-defi-rollout,SHORT_SHA=<sha>`
>       →
>       `gcloud run services update deployment-dashboard --region=asia-northeast1 --image=…/deployment-dashboard/deployment-dashboard:<sha>`
>       → verify the new revision + curl the served bundle for `isStagingDormant`. NOT raced from the monitor session
>       (concurrent prod-build collision risk; this is the new-tab's "confirm /repos post-redeploy" scope).
>       (deployment-api)
> - [x] ✅ [SCRIPT] P2. alert routing DONE 2026-06-27. `promotion_lag_monitor._main_direct_repos` reads the
>       `staging_dormant_mode` toggle → when on, EVERY repo is treated main-direct so the lag monitor + Slack skip ALL
>       staging directions fleet-wide (not just ldr_main). Reversible; +regression test. (unified-trading-pm)

## Progress Log — 2026-06-29 (operator-driven /repos accuracy + fleet-drain unblock)

- ✅ **CRITICAL: repaired the broken fleet-promote** — `ldr-to-main-promote-fleet.yml` had a YAML break (the
  `CURRENT_WORKSPACE_DIGEST` embedded `python3 -c` heredoc sat at column-0 inside a 10-space `run: |` block → the file
  FAILED TO PARSE → the ENTIRE fleet LDR→main promote had been dead, fleet-wide no draining). Re-indented the python to
  the block base (verified parses + compiles col-0). Shipped **LDR@7ecd7aa9c + main@3c82b6ad5** (`.github` carve-out
  direct-to-main — a broken promote can't self-promote). Fleet promote run 28350383721 = SUCCESS; deployment-api#249 /
  market-tick-data-service#467 / deployment-service#318 promoting; SIT auto-dispatched for the `unknown-delta` repos.
  (unified-trading-pm)
- ✅ **UTL phantom root-blocker cleared** — `unified-trading-library` ci_status was stale FAILING (its QG failure was
  FLAKY — the dep-clone phantom-version class; a fresh QG-v2 on main came back SUCCESS). Cleared FAILING→MAIN_GREEN via
  the `ci_status_store.py` producer (Firestore SSOT) after verifying green. Unblocked deployment-api's dep-order hold.
- ✅ **LDR→staging drain cron STOPPED** — removed the `*/15` schedule from `ldr-to-staging-promote.yml` (kept
  workflow_dispatch + repository_dispatch + the orphan-close step). Fleet is LDR→main-direct so the drain was a no-op
  burning ~2-3k GHA-min/mo (operator cost call). **PM@eaac8a681.** + orphan-close step (closes stuck dormant drains at
  source) **PM@a3733cf7f**. Closed 3 orphaned stuck drains (batch-live-reconciliation#203, strategy-service#361,
  unified-api-contracts#523).
- ✅ **/repos display: dormant-aware + deployed-artifact** — dormant staging signals SHOW muted ("dormant · ignored",
  grey not red) not hidden; LDR→main lag chip tone tracks ACTIONABILITY (red only if genuinely stuck); drain panel
  LDR→staging row "dormant · not scheduled"; image column tracks the DEPLOYED artifact (source-deployed / bundled-in /
  tier3 via `_SERVICE_NAME` attribution). deployment-ui@d98a753/9551408, deployment-api@b1e1041/acf5764 +
  Dockerfile.dashboard ARG fix @2f270d2, deployment-service@70e208f. Live on uts-shared-deployment-api rev 00130.
- ⚠️ **Follow-ups (not blockers)**: (1) the **flaky dep-clone** in QG (phantom-version → stale-deps) is what made UTL
  flake — it will re-trip the dep-order gate + the overnight Dead-Man-Switch; durable fix = harden the QG
  dep-resolution. (2) **deployment-ui + agent-orchestrator** read `unknown-delta` (TS / differ source-dir) — they
  promote once the auto-dispatched SIT validates their tree (coverage flipped 21/21, `7e0177e1e`); if not, they need
  genuine SIT invariants (no forged manifest edits). See `issues/sit_rehome_safety_gate_gaps_2026_06_27.md`.

## Tasks

- [x] ✅ [WORKFLOW] P1. **Frozen-head LDR→main promote** (also fixes the live `action_required` jam) DONE 2026-06-27
      (Option B+). The fleet bot pins the promote PR head to a bot-controlled `promote/<repo>` ref force-updated to the
      validated `LDR_SHA` ONLY past the gate, and the PR is **PAT-authored** (an App-authored promote PR lands v2 in
      `action_required` and deadlocks — proven by A/B on a held head; the App-token→PAT `gh pr create` fix shipped
      separately PM@860f64d0c). So the async auto-merge can only ever merge gate-validated content (closes the
      live-branch-drift TOCTOU). Mutable-per-repo ref (safe: force-update is gate-gated; differ evaluates the full
      `main..LDR` range) rather than the originally-specced per-SHA ref. **PM@95bb7b5c6.** (unified-trading-pm)
- [x] ✅ [WORKFLOW] P1. **Re-home SIT onto LDR** DONE 2026-06-27 (Option B+ safe interim). `full-workspace-sit` ALREADY
      assembles the cross-repo set from LDR tips (clones `live-defi-rollout`) and now emits `SIT_VALIDATED` +
      `sit_validated_tree` keyed to the LDR tree — but ONLY for `sit_cross_repo_validated_repos` (the repos the suite
      actually validates; the other 16 ldr_main repos stay conservatively BLOCKED on breaking, no forged guarantee). The
      LDR→main consumer gates a BREAKING `main..LDR` delta on Firestore-live
      `sit_validated_tree == the promoted LDR     tree` (decoupled from the no-downgrade status rank), fail-CLOSED, with
      a differ source-dir guard. `sit-gate.yml` / `sit-debounce-trigger.yml` are UNCHANGED (kept for the
      dormant/reversible staging path — per the operator correction above). **Gate:** a deliberately-breaking cross-repo
      change on a COVERED repo is CAUGHT by SIT on LDR and blocks LDR→main until SIT-validated; a non-breaking change
      promotes on the single LDR→main v2. Producer+drift- guard system-integration-tests; consumer/store/manifest
      PM@95bb7b5c6 + docs PM@7433c138f. **Adversarially verified (2 rounds): both CRITICAL gaps closed.**
      Expand-coverage + cross-repo-combination deferred → issues/sit_rehome_safety_gate_gaps_2026_06_27.md.
      (unified-trading-pm + system-integration-tests)
- [x] ⏭️ SUPERSEDED [SCRIPT] P1. ~~Drop the staging axis from the manifest + gates~~ — SUPERSEDED by the OPERATOR DESIGN
      CORRECTION above (keep `staging` dormant + REVERSIBLE). `staging_versions` keying + `sit-debounce`/`sit-gate` STAY
      (they drive the dormant/reversible through-staging path for major/breaking/operator). The "drop" framing is
      retired.
- [x] ⏭️ SUPERSEDED [WORKFLOW] P1. ~~Delete the LDR→staging machinery~~ — SUPERSEDED (keep dormant + reversible).
      `ldr-to-staging-promote.yml` etc. are RETAINED (they skip ldr_main/dormant repos at source but resume on toggle-
      back). NOT deleted.
- [x] ⏭️ SUPERSEDED [WORKFLOW] P1. ~~Fold in `cicd_staging_main_deadcode_retirement` (delete staging→main machinery)~~ —
      SUPERSEDED (the through-staging path is retained for toggled-back repos; it uses a clean merge, not the squash —
      only the unresolvable-diff SQUASH was the problem and that path is dormant, not deleted).
- [x] ⏭️ SUPERSEDED [INFRA] P1. ~~Delete the `staging` branch fleet-wide~~ — SUPERSEDED by the operator correction: the
      branch is KEPT (dormant), its ROLE toggled off reversibly via `promotion_model=ldr_main` / `staging_dormant_mode`.
- [ ] [VERIFY] P1. **End-state proof** (PARTIAL — re-scoped to the dormant-not-deleted end-state). DONE: (2) exactly ONE
      gating v2 on the LDR→main direct path (no LDR→staging v2 for ldr_main repos); (4) the `action_required` jam class
      is gone (PAT-authored + frozen head). PENDING a live exercise: (3) a deliberately-breaking cross-repo change on a
      COVERED repo caught by SIT-on-LDR before main (the gate is shipped + adversarially verified but unexercised until
      a real breaking change lands; currently the fleet promote is also blocked by the Cloud Build hatch-vcs regression
      — being fixed in parallel). (1) is N/A (branch kept dormant, not deleted). `ci-cd-flow.md` updated (PM@7433c138f).

## Success criteria

- `staging` branch deleted fleet-wide; LDR→main is the single promote path; exactly ONE gating v2 per promotion.
- SIT (cross-repo breaking-change safety) still runs — on a frozen LDR snapshot, not a staging branch.
- The `action_required` promote jam is structurally eliminated (frozen, PAT-authored head).

## Codex SSOT updates

- `/codex/08-workflows/ci-cd-flow.md` — replace the staging-in-the-flow model with the no-staging single-path LDR→main +
  SIT-on-LDR model; document the frozen-head promote.
- `/codex/06-coding-standards/integration-testing-layers.md` — SIT now runs on the LDR snapshot, not staging.
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
  - ✅ **STEP 3 (store)** — `ci_status_store.py` persists `sit_validated_tree` (clear-on-any-non-SIT_VALIDATED-status,
    the load-bearing safety) + `--sit-validated-tree` CLI + `ci-status-update.yml` threading + 2 unit tests. Landed
    (PM@375b967).
  - ✅ **STEP 2 (producer)** — `full-workspace-sit.yml` stamps `ci_status=SIT_VALIDATED` + `sit_validated_tree` per repo
    on a GREEN cross-repo run, keyed to each sibling's LDR SHA/tree. **Key finding: full-workspace-sit ALREADY assembles
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
- 2026-06-27 (**SIT-rehome COMPLETE — Option B+ shipped + adversarially verified ×2**). Operator chose "safe interim".
  Shipped: store decouple + get-doc + consumer gate + manifest `sit_cross_repo_validated_repos` (PM@95bb7b5c6, hotfix
  c3160ae89 for a manifest autostash-conflict I pushed); producer scoping + suite drift-guard
  (system-integration-tests); App-token→PAT promote-PR fix (PM@860f64d0c); codex ci-cd-flow B+ section + codex-freshness
  ratchet-down (PM@7433c138f). Frozen-head + Re-home-SIT tasks flipped DONE; the 4 staging-DELETE tasks SUPERSEDED by
  the operator keep-dormant correction; End-state-proof PARTIAL (gate live + verified, awaiting a live breaking-change
  exercise + the Cloud Build hatch-vcs regression fix). 2 re-verification rounds confirmed both original CRITICAL gaps
  (MAIN_GREEN liveness jam + 5-of-21 over-stamp) CLOSED; the residual is_stale_write jam also fixed. Deferred (tracked
  in issues/sit_rehome_safety_gate_gaps_2026_06_27.md): expand SIT coverage to all 21; cross-repo-combination
  fingerprint; per-SHA immutable ref. **Separately found + fixed/fixing operator-flagged fleet fires**: Cloud Build
  failures = hatch-vcs can't detect version in the `build-wheel` step (`.git` present but no tags in the Cloud Build
  shallow checkout) — a regression from the WS-L git-tag migration, blocking v2 → the 26h promotion lag (surgical
  per-repo fix in flight via a sub-agent); IAM grant `github-actions-deploy@ roles/cloudbuild.builds.editor`
  (market-tick-data-service-prod trigger PERMISSION_DENIED) DONE.
- 2026-06-27 (**STEPS 1+4+5 IMPLEMENTED → adversarially verified → REVERTED (2 CRITICAL gaps caught pre-merge); operator
  decision required**). Implemented the coupled unit (atomic LDR sha+tree read; Firestore-live fail-CLOSED consumer
  gate; on-block SIT dispatch; frozen-head `promote/<repo>` ref) and ran 3 read-only adversarial sub-agents
  (safety/liveness/ mechanics) BEFORE landing. Two CRITICAL findings, both DIRECTLY VERIFIED in the code, make it unsafe
  to ship as specced: (1) **liveness** — `resolve_status` no-downgrade (`SIT_VALIDATED:3 < MAIN_GREEN:4`) REJECTS every
  SIT_VALIDATED write once a repo is MAIN_GREEN → `sit_validated_tree` never re-written → the gate would jam every
  ldr_main repo on its 2nd breaking change forever; (2) **safety** — `run_cross_repo_invariants.sh` validates only 5
  `REQUIRED_SIBLINGS` but the STEP 2 producer stamps SIT_VALIDATED on all 21 ldr_main repos → a breaking change in any
  of the other 16 promotes ungated (forged certificate). Plus HIGH design issues: mutable vs per-SHA promote ref;
  per-repo fingerprint can't express the cross-repo combination; differ `--source-dir` blind guess → silent
  false-negative. **Action:** reverted the uncommitted consumer+frozen-head (diff backed up
  `scratchpad/fleet_promoter_step145.diff`); the inert shipped building blocks (producer/store/get-doc/token-swap) stay.
  Full analysis + the corrected-design requirements + the operator's coverage-guarantee fork (A expand SIT to 21 / B
  scope to 5 / C workspace-digest) → `plans/active/issues/sit_rehome_safety_gate_gaps_2026_06_27.md`. **NOTIFYING
  OPERATOR** (big cross-repo safety-gate finding). The current state is safe (breaking ldr_main changes stay
  conservatively blocked, not leaked).
