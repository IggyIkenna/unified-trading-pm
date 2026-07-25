---
doc_type: plan
title: CI/CD MVP — LDR→SIT→main, simplified single-path pipeline (supersedes the WS-L complex pipeline)
summary:
  "OPERATOR DECISION (Harsh + Ikenna, reaffirmed 2026-06-30): we do NOT need the complex CI/CD pipeline. The MVP is:
  commits reach LDR via local-green quality-gates + quickmerge (already enforced) → SIT validates → merge LDR→main.
  Staging is DORMANT (reversible switch kept). The promote gate set is exactly THREE things: SIT-green +
  quality-gates-v2 (on the promote PR) + quickmerge-provenance. Everything beyond that — label-check, the SIT cross-repo
  COMBINATION digest, the dep-order gate, version-out-of-source (D13/Phase-2), per-repo cross-repo SIT invariants — is
  OUT OF SCOPE and is what was BLOCKING the pipeline. This plan is the single SSOT for the simplified pipeline; it
  supersedes the WS-L plan family and resolves the promotion-stall issue docs. It also folds in the still-real HEALTH
  work needed to keep the MVP flowing (harden the flaky QG dep-clone, the legacy-ref cleanup, the --delete-branch guard,
  cron reliability, local↔CI parity)."
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, system-integration-tests]
scope: [engineer, admin]
tags: [cicd, mvp, ldr-main, single-path, staging-dormant, SIT, quickmerge, simplification]
related: [plans/active/issues/ldr_main_promotion_findings_consolidated_2026_06_29.md, /codex/08-workflows/ci-cd-flow.md]
created: 2026-06-30
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-12
locked_by: live-defi-rollout
locked_since: 2026-06-30
supersedes:
  [
    cicd_consolidated_remaining_2026_06_24.md,
    cicd_retire_staging_branch_2026_06_27.md,
    cicd_staging_main_deadcode_retirement_2026_06_27.md,
    cicd_phase2_foundation_2026_06_27.md,
    cicd_phase2_finalize_2026_06_27.md,
    cicd_phase2_semver_retarget_2026_06_27.md,
    cicd_sit_full_coverage_handoff_2026_06_27.md,
    cicd_workflow_sprawl_consolidation_2026_06_27.md,
    cicd_local_ci_parity_2026_06_27.md,
    cicd_misc_hygiene_2026_06_27.md,
    cicd_deployment_ui_followups_2026_06_27.md,
    cicd_aws_dual_cloud_build_2026_06_27.md,
  ]
superseded_by:
depends_on: []
source:
  operator directive 2026-06-30 (Harsh, Ikenna offline 2 days) — "we don't need the complex pipeline; MVP = run SIT and
  merge LDR→main; everything else out of scope"
assigned_role: infra
drift_direction: advance-code
---

## Deferred work — migrated to:

See inline `DEFERRED-OPERATOR-DECISION` annotation next to its `- [ ]` item in body for the specific successor /
blocker.

# CI/CD MVP — LDR→SIT→main

> **THE pipeline, simplified to the MVP.** A commit is green locally (`quality-gates.sh`) and reaches
> `live-defi-rollout` via `quickmerge`. SIT validates the LDR content. We merge LDR→main. That's it. `staging` stays
> dormant behind a reversible switch. This plan **supersedes the entire WS-L "complex pipeline" family** (see
> frontmatter `supersedes`) and **resolves** the promotion-stall issue docs. Full forensic detail of how we got here
> lives in `issues/ldr_main_promotion_findings_consolidated_2026_06_29.md` (the findings-of-record).

## The MVP gate set (the ONLY gates on LDR→main)

1. **SIT-green** — the cross-repo SIT suite validated this repo's LDR tree (`full-workspace-sit` on the promoted
   content). ✅ 2026-07-12 (finding 78): SIT-green is now an ENFORCED required check on every `ldr_main` repo's LDR→main
   promote PR (was: "closes the 2026-07-07/08 incident gap" outright — **narrowed 2026-07-14, finding 199**: this closes
   only the Layer-1 half of that incident — the gate now fires unconditionally instead of only consulting SIT for a
   BREAKING/unknown delta. It does NOT close Layer-2: on the actual 2026-07-07/08 incident, `full-workspace-sit` itself
   ran green due to a separate SIT test-coverage gap [no test re-derives IS's expected-universe from the live UAC
   registry], so this exact break class would still slip through even with SIT-green unconditionally enforced. Layer-2
   remains open, unresolved, all todos unchecked, per
   `issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`). See the DONE P1 todo below for the
   Layer-1 mechanism + fleet proof.
2. **quality-gates-v2** — the required check on the promote PR (per-repo correctness).
3. **quickmerge-provenance** — only quickmerge'd content reaches main (already enforced on the LDR side).

Plus the trivial mechanics that are not "gates": content-differs, don't-promote-a-RED-repo (Tier-A), runaway-breaker.

- [x] [INFRA] P1. ✅ Wired `sit-gate/fleet-green` as a REQUIRED status check on the LDR→main promote PR for all 23
      `ldr_main` repos — PM@`199f72bbd` (feature) → `fc5d717e0` (PAT-for-statuses fix) → `69f3f4cad` (set -e guard fix)
      → `2d81a138e` (htmlUrl→url field fix), all merged to main. **Mechanism**: `ldr-to-main-promote-fleet.yml` computes
      a FLEET-SHARED signal each tick (was the last COMPLETED `full-workspace-sit.yml` run on `system-integration-tests`
      green?) and POSTS it unconditionally as a commit status (context `sit-gate/fleet-green`) on every promote-PR head,
      regardless of the per-repo breaking/non-breaking classification (closing the exact gap the incident found);
      fail-closed on any read gap/error. `pin_branch_protection_rulesets.py` requires this context on the
      `require-quality-gates` ruleset for every repo with `promotion_model=ldr_main` ONLY — never for
      `unified-trading-pm` / `system-integration-tests` (their main-bound path is a different workflow that never posts
      this status; requiring it there would deadlock them permanently). Fleet-shared (not a per-repo SIT-tree
      fingerprint) so it can never discriminate against e2e-testing / ibkr-gateway-infra (structurally never
      SIT-tree-stamped, by design) the way a per-repo requirement would. **Rule-11 blast-radius proof (done BEFORE
      enabling)**: last 50 `full-workspace-sit` runs (2026-07-08→07-12) all green (48 success / 2 cancelled / 0 failed);
      pulled the exact in-script SIT-gate verdict live via a `workflow_dispatch --ref live-defi-rollout` dry-run across
      the whole fleet first. **Two live-canary bugs found + fixed before rollout** (via `only_repo=` scoped non-dry-run
      dispatches, not guesswork): (1) a bare `X=$(gh run list …)` followed by a separate `$?` capture aborted the WHOLE
      promoter job under `set -euo     pipefail` when the read failed (job conclusion=failure, run `29212085588`) —
      fixed to `if ! X=$(cmd) || [ -z     "$X" ]; then …; fi` (assignment-as-if-condition is `set -e`-exempt; verified
      with a local `bash -c` repro first); (2) `gh run list --json htmlUrl` is not a valid field (the field is `url`) —
      was silently forcing the signal to fail-closed every tick regardless of SIT's real state; also found + fixed (same
      commit) that the App token 403s on `statuses` POSTs ("Resource not accessible by integration") — switched to the
      PAT (`GH_PAT_FOR_ARM`), the already-proven-working credential for every other cross-repo write in this script;
      applied the same fix to the pre-existing (advisory, silently-broken) `semver-agent/label-check` POST while in the
      file. **Closing self-check (rule 11)**: ruleset applied to 2 consumer repos first (`market-tick-data-service`,
      `deployment-service`) as a canary — confirmed `sit-gate/fleet-green=success` + `semver-agent/label-check=success`
      actually posted on real promote-PR heads (verified via `commits/{sha}/status` API), then confirmed a real green
      promote PR **actually merged to main** through the new required check (`market-tick-data-service` PR #533 →
      main@`bbf73dad8984`, 2026-07-12T22:55:08Z). Rolled to the remaining 21 repos
      (`pin_branch_protection_rulesets.py --apply`, 21/21 applied, 0 failures); re-ran the dry-run → 0 drift
      (idempotent). **Fleet-wide real-run confirmation**: a subsequent full (unscoped) dispatch posted the status on all
      4 repos with a content delta that tick and 2 promoted clean through the new gate
      (`unified-api-contracts`→main@`4bd30f6d31b3`, `deployment-service`→main@`b25920aa9304`, both
      2026-07-12T22:58:07Z); the other 3 blocked for pre-existing, unrelated reasons (provenance / Tier-A ci_status, not
      this gate). Operator ruling 2026-07-12, finding 78.

## OUT OF SCOPE (the complexity we are removing — this is what was blocking)

These were the WS-L "complex pipeline" and are explicitly deferred/retired for the MVP. Removing them is the core of
Phase 1:

- **label-check gate** (semver-bump match in the promoter) — false-blocked UAC/mtds via the range-asymmetry bug; belongs
  to the version machinery, not the MVP promote.
- **SIT cross-repo COMBINATION workspace-digest** — thrashes under fleet churn (blocked features-service/agent-orch);
  the MVP keeps only the per-repo SIT-tree check.
- **dep-order gate** — turned one flaky tier-0 into a fleet-wide freeze (the overnight incidents); SIT already validates
  the assembled workspace, so it is redundant for the MVP.
- **version-out-of-source / D13 (Phase-2: foundation/finalize/semver-retarget)** — the entire tag→Firestore-registry
  versioning re-architecture. Not needed to "run SIT and merge." Shelved (reversible; revisit if/when wanted).
- **per-repo cross-repo SIT invariants / 21-of-21 full coverage** (`sit_full_coverage_handoff`) — beyond MVP.
- **deploy-infra items** folded from superseded plans, deferred (revisit post-MVP): AWS dual-cloud image build
  (`cicd_aws_dual_cloud_build`), cloudbuild silent-failure alerting, GHA billing-wall, deployment-ui pipeline
  follow-ups.

## Phase 1 — simplify the promoter to the MVP gate set (the unblock)

- [x] [WORKFLOW] P1. ✅ **label-check gate → advisory** (no longer blocks) — `ldr-to-main-promote-fleet.yml`, PM #729
      (merged main@7ffba64d). Unblocked unified-api-contracts + market-tick-data-service.
- [x] [WORKFLOW] P1. ✅ **SIT cross-repo COMBINATION workspace-digest check REMOVED**; per-repo
      `sit_validated_tree ==     LDR tree` kept — PM #729. Unblocked features-service (promoted via per-repo tree
      match).
- [x] [WORKFLOW] P1. ✅ **dep-order gate → advisory** (removed as a blocker; kills the flaky-tier-0 fleet-freeze) — PM
      #729.
- [x] [CONFIG] P1. Flip `e2e-testing` + `ibkr-gateway-infra` to `promotion_model=ldr_main` OR scope branch-health to
      skip non-`ldr_main` repos. ✅ — **Option A executed same-day**: PM #731 (merged 2026-06-30 08:41, PM@`3f2c6bc8`,
      "opt e2e-testing + ibkr-gateway-infra into ldr_main (MVP promote path)", cites this plan as SSOT). Verified
      2026-07-02: both repos carry `promotion_model: ldr_main` in `workspace-manifest.json`; both fully drained —
      `compare/main...live-defi-rollout` shows `files: 0` (content-identical; `ahead_by` is squash inflation);
      e2e-testing promote PR #428 MERGED 2026-06-30. Branch-health alert-noise motivation gone. (Checkbox was stale —
      the flip landed the same day the plan was written, between authoring and the deadlock-fix item below.)
- [x] [VERIFY] P1. ✅ Verified from `main`: market-tick-data-service (#469) + deployment-service (#321) +
      features-service (#733) all PROMOTED through the MVP gates (tree-equal); label-check advisory ("promoting
      anyway"); only UAC held by the kept provenance gate (real non-quickmerge code). No false blocks.

## Phase 2 — keep the MVP flowing (health work folded from superseded plans/issues)

- [x] [CICD] P1. ✅ **Harden the flaky QG dep-clone** — retry the primary `live-defi-rollout` clone 3× before the
      stale-tag fallback (the documented dep-resolution-skew root). PM@`4a0607a1` (live on LDR for 38 gates + merged
      main).
- [x] [CICD] P1. ✅ **Harden the promoter's superseded-ref cleanup** — `process_repo` now deletes the legacy no-slash
      `promote/<repo>` ref before per-SHA creation (PM@`980ef126`, LDR). Reaches main on PM's next promote.
- [x] [CICD] P0. ✅ **`--delete-branch` guard** — `process_repo` auto-closes any stale `head=live-defi-rollout` promote
      PR up-front (PM #732 → main). Self-healing land-mine removal.
- [x] [CICD] P0. ✅ **SIT-gate permanent-deadlock fix for SIT-uncovered repos** (root-caused from the 2026-06-30
      ci-failures branch-health alerts: e2e-testing in EVERY lag alert). e2e-testing (+ ibkr-gateway-infra) are
      `ldr_main` but NOT in `sit_cross_repo_validated_repos`, so `full-workspace-sit` never stamps their
      `sit_validated_tree` (anti-forgery, by design: "5 validated vs 21 stamped"); the breaking-differ returns `unknown`
      (no analyzable public surface) → the fail-closed SIT branch required a tree fingerprint that can NEVER exist →
      permanent block (NOT cron lag — the scheduled promoter ran and emitted
      `SIT GATE BLOCK e2e-testing … sit_validated_tree='unset'`). Fix: `process_repo` SIT gate now fail-OPENs for repos
      outside `sit_cross_repo_validated_repos` (SIT leaves/infra, no cross-repo contract to break; promote PR still
      v2+content+Tier-A gated on auto-merge). Covered repos unchanged. PM@`57880bbb` (LDR) + #735 → main@`d0a94729`
      (v2-green). **Verified end-to-end**: post-fix from-`main` run `28441670198` →
      `SIT GATE N/A e2e-testing … fail-OPEN` → `Promoted (1): e2e-testing` → PR
      [e2e-testing#428](https://github.com/IggyIkenna/e2e-testing/pull/428) armed (head
      `promote/e2e-testing/35e00d357092`, v2-gated auto-merge). deployment-ui/agent-orchestrator were transiently
      blocked (stale `sit_validated_tree`) and already self-healed (tree now matches LDR).
- [x] [CICD] P0. ✅ **Nightly T0 false-red fixed — self-clone in the QG dep loop deleted the job workspace**
      (root-caused from the 2026-07-03 ci-failures alerts: "CI REGRESSION unified-trading-library FAILING" + 7
      consecutive Overnight-T0 failures since 2026-06-27). unified-trading-library's `agent-audit.yml` listed the repo
      ITSELF in `dep_repos`; the callee clones each dep to `../<name>`, which for self IS `$GITHUB_WORKSPACE` — the LDR
      clone fails on the non-empty dir and the retry-hardening `rm -rf` (the P1 flaky-QG item above, PM@`4a0607a1`)
      deletes the runner's own checkout → `fatal: unable to get current working directory` → all 3 slices red → false
      FAILING ci_status → orchestrator T0 abort + dead-man-switch. Latent since 2026-06-01; masked by the content
      sentinel until the 2026-06-27 staging-retirement promotions changed main. main was NEVER code-broken (SIT
      auto-revalidated same morning). Fix both sides: dep list de-selfed UTL@`9ad8f98d5` (LDR) + fleet-wide self-skip
      guard in the callee loop PM #767 (MERGED main@07:09Z). Only UTL had a self-referencing dep list (fleet-scanned);
      the template generator already excludes self, agent-audit.yml was hand-written. **Runtime-verified same morning
      ("run it, don't read it")**: manual dispatch on UTL main run `28644627760` proved the guard ("Skipping self-clone
      of unified-trading-library") AND exposed bug #2 in the same hand list — it OMITTED `unified-api-contracts` (UTL's
      only real editable path dep) → `uv` "Distribution not found …/unified-api-contracts" (masked for weeks by the same
      content sentinel). Dep list corrected to the real closure `"unified-api-contracts"` (matching the templated QG
      caller) UTL@`c6718de5` (LDR). **VERIFIED GREEN end-to-end**: dispatch run `28644929850` (LDR workflow + PM@main
      callee) — all 3 QG slices + aggregate success. UTL LDR→main promote drain triggered (fleet run `28645228144`) so
      tonight's ~01:30Z Overnight T0 runs the corrected file from main.
- [x] [CICD] P1. ✅ **AWS image builds DISABLED per operator (Harsh) 2026-07-03 — DEFERRED-OPERATOR-DECISION on the
      `AWS_BUILD_ROLE_ARN` credential ask** (was BLOCKED-CREDENTIALS; ask remains filed for the re-enable path:
      `ikenna_orchestrator/pings/slot_0.md` § CREDENTIAL APPROVAL REQUEST — `AWS_BUILD_ROLE_ARN`). Context:
      `image-build-gate.yml` (fleet rollout 2026-06-27) NEVER passed — the secret was never provisioned in any repo
      (user account → no org secrets → `secrets: inherit` empty) → OIDC auth fail on every promote PR. Operator ruled
      AWS builds were a TEST; GCP Cloud Build is the production path; don't spend on AWS. Disabled all 3 AWS surfaces
      behind a **reversible switch** (operator-requested, mirrors the staging-toggle pattern; initial hard `if:false`
      PM@`f22fde880` superseded same-day by the switch PM@`d93388305`, PR #769): the GHA variable `AWS_BUILDS_ENABLED`
      (unset/false = OFF, default) gates (1) the `build-aws` job in `image-build-validate.yml` (per-CALLING-repo var;
      gate job passes on GCP alone when skipped; callers reference `@live-defi-rollout` → live fleet-wide immediately)
      and (2) `cloud-build-router-aws.yml` `route-build` (PM's var; effective on main after the promote PR); (3) deleted
      the native GitHub webhooks on ALL 18 CodeBuild projects in `427895769566`/ap-northeast-1 (verified 0 remain) —
      these built on EVERY push via GitHub-Hookshot, independent of GHA, and were the actual AWS spend. **The switch**:
      `bash scripts/cicd/toggle-aws-image-builds.sh on|off|status` (flips the vars fleet-wide + creates/deletes the
      CodeBuild webhooks in one command). RE-ENABLE (Ikenna, whenever wanted): provision `AWS_BUILD_ROLE_ARN` per the
      ping, then `toggle-aws-image-builds.sh on`.
- [ ] [CICD] P0. **Cron reliability — LEFT AS-IS per operator (2026-06-30).** GHA `schedule` fires ~1/1.5–2h
      (best-effort, drops ticks). Ikenna to decide when faster draining is needed. Options: (A) self-hosted VM heartbeat
      dispatching the promoter every 15 min via `gh workflow run` [recommended — deterministic]; (B) event-driven
      dispatch from quickmerge when content lands on a repo's LDR. The fleet still drains, just on a 30–90 min cadence.
- [ ] [CICD] P0. **Now-tracked here (added 2026-07-14, findings 107/201):** `scripts/quickmerge.sh` silently no-ops on a
      new-file-only ship — `quickmerge --agent --files '<newfile>'` where every `--files` path is untracked prints "No
      differences from main — nothing to merge" and exits 0 without staging/committing anything, because the no-diff
      guard (`git diff origin/main`, worktree-vs-commit) does not see untracked files (unlike the clean-tree guard
      elsewhere, which correctly uses `git status --porcelain`). Full repro + root cause + recommended fix:
      `issues/quickmerge_untracked_new_files_silent_noop_2026_06_23.md` (re-verified still-live 2026-07-12, current
      `quickmerge.sh` ~line 1188). This plan claims sole SSOT status for the pipeline/quickmerge area, so this bug is
      recorded here as the tracking home; fix not yet implemented.
- [x] [CICD] P1. ✅ **YAML-valid gate now fleet-wide, single-source** — moved the invocation from PM's repo-specific
      `quality-gates.sh` into the shared `base-service.sh` (referencing the ONE PM-hosted checker via `WORKSPACE_ROOT`),
      so every repo validates its own `.github/workflows` with zero per-repo copies. PM@`44280bb3` (LDR; live for all
      QG). Verified from system-integration-tests (15 workflows green). [operator-corrected approach: no rollout]
- [x] [CICD] P2. **Local↔CI parity** (folded from `cicd_local_ci_parity`): keep local `quality-gates.sh`-green a
      reliable predictor of server `quality-gates-v2`-green (manifest canonical-form churn-protection) — underpins the
      MVP's "commits reach LDR via local-green QG" premise. ✅ — PM@`611caf3b` (quickmerge→LDR, 2026-07-02). Full
      4-track audit (CI-side workflow · local base-service.sh · macOS-ARM/Ubuntu-24.04 portability · manifest churn
      forensics), then: **(1) env parity** — base-service.sh now exports CI's `CLOUD_PROVIDER=local` +
      `UNIFIED_TRADING_CLOUD_PROVIDERS_YAML` defaults (same when-unset condition); **(2) slice-completeness guard** —
      new blocking `check_qg_slice_completeness.py` machine-enforces the "3 CI slices = zero lost coverage" partition
      (was prose; the 2026-06-10 typecheck-false-green class); **(3) manifest canonical form** — root-caused the hourly
      cosmetic-churn loop (`ci_status_consolidator.py` wrote ascii-escaped/no-newline vs every other writer + prettier;
      57 reformat-only commits), fixed ALL 4 divergent writers (consolidator, ldr_ci_monitor, sync-manifest-versions,
      run-qg-baseline) to `json.dumps(indent=2, ensure_ascii=False)+"\n"`, new blocking
      `check_workspace_manifest_canonical.py` rejects non-canonical writes (verified red/green/--fix at runtime); **(4)
      platform** — quickmerge bare `python`→`python3` (broke stock macOS + Ubuntu 24.04 no-venv path), sentinel hash via
      portable `_qg_hash` (sha256sum-or-shasum — sentinel was permanently dead on macOS), `${EPOCHREALTIME}` profiler
      timestamps (BSD date has no `%N`), `LC_ALL=C` sort in the hash path — gate now behaves identically on Linux x86 /
      Ubuntu 24.04 / macOS ARM; **(5) matrix codified** — ci-cd-flow.md § parity matrix "Drive-to-parity hardening
      (2026-07-02)" table (closed vs sanctioned deltas). Verified: full PM `quality-gates.sh --no-fix` PASSED with both
      new guards green in-line; both guards runtime-verified to catch their regression class.

## Phase 3 — verify healthy, then archive the superseded family

- [x] [VERIFY] P1. ✅ Pipeline healthy — from-`main` run promoted mtds + deployment-service + features-service through
      the MVP gates with no false blocks; only real blocks remain (UAC provenance).
- [x] [DOCS] P2. ✅ Archived 12 superseded plans → `plans/archive/2026_06/` + 9 resolved issue docs →
      `plans/archive/issues/` (incl. the consolidated findings doc). Only `cicd_mvp_ldr_to_main_pipeline` remains
      active.
- [x] [DOCS] P2. ✅ `/codex/08-workflows/ci-cd-flow.md` MVP banner added (gate set + retired-gates note + pointer here);
      full rewrite of the 1208-line body deferred (Phase-3 follow-up below).
- [ ] [DOCS] P0. Full rewrite of `ci-cd-flow.md` body + the CLAUDE.md "Git discipline + shipping pipeline" section to
      the MVP (remove the complex-gate prose) — bigger contract edit, for operator review when Ikenna is back.

## Phase 4 — semver-agent trigger retarget (completes the shelved D13/Phase-2 retarget; un-shelved 2026-07-25)

> **Source**: operator directive 2026-07-25 (`/autonomous`, "we are NOT gonna use staging right now unless we flip the
> toggle, so under the ldr to main we need a full mechanism for that, all repos do it properly"). Found while resolving
> today's CI alerts: no `unified-trading-library` wheel has published since 2026-06-27 (F2, tracked in
> `issues/post_cutover_silent_assumption_sweep_2026_07_23.md`).
>
> **Root cause (confirmed by direct repro, not inference)**: `ldr-to-staging-promote.yml`'s `*/15` drain cron was
> correctly stopped 2026-06-28 per `staging_dormant_mode` (archived
> `/plans/archive/2026_06/cicd_retire_staging_branch_2026_06_27.md` — the OPERATOR END-STATE). But
> `scripts/workflow-templates/semver-agent.yml.tmpl` still triggers ONLY on `branches: [staging]`
> (`workflow_run: quality-gates-v2` + a direct `push: [staging]` fallback). With the drain off, `staging` never advances
> — verified directly: `unified-trading-library`'s `origin/staging` HEAD is `3df05de2a55df1093fa737a6fe01aebb943599e3`
> (2026-06-28T21:04:20, "Tier C auto-drain"), **526 commits behind** `origin/live-defi-rollout` as of 2026-07-25T15:27Z.
> So semver-agent has not fired since ~06-28 for ANY `ldr_main` repo → zero new tags minted → `publish-package.yml`
> (triggers on `push:[main]`) never sees new content → Artifact Registry frozen at whatever was last published
> pre-outage (`unified-trading-library` last version `0.55.0`, 2026-06-27T10:02:52). This is NOT the
> "instruments-service Cloud Build failure" incident from today's alerts (that repo builds UTL from a local path dep in
> CI, unaffected) — it's a separate, longer-running, previously-undiscovered outage this investigation surfaced.
>
> **Why this is safe to fix now (lower-risk than it looks)**: the archived
> `/plans/archive/2026_06/cicd_phase2_semver_retarget_2026_06_27.md` (Phase-2/D13, `status: superseded` by THIS plan,
> `depends_on: cicd_phase2_foundation` — already green) already shipped the HARD part — the writer mints a `vX.Y.Z` git
> tag instead of a `chore(release)` pyproject commit, for any repo flagged `version_source=git-tag` (confirmed:
> `unified-trading-library`'s live `.github/workflows/semver-agent.yml` already has `VERSION_SOURCE="git-tag"` hardcoded
> at 3 sites) — canaried on greeks-service, never fleet-rolled. The compute-next (tag-based) + bump-rate breaker
> (tag-based) legs are also done. **The ONLY missing piece is the TRIGGER**: retarget `branches: [staging]` →
> `branches: [main]` in the `.tmpl`, roll out via the existing `rollout-semver-agent.sh` /
> `rollout-workflow-templates.sh` mechanism. This does NOT touch the SIT/breaking-change gate (already solved
> differently + verified working today via the `sit-gate/fleet-green` mechanism, finding 78 above) — semver-agent's own
> label-check is already ADVISORY, not blocking (Phase 1 above), so retargeting its trigger cannot regress promotion
> safety, only versioning liveness.
>
> **Scope discipline (rule 11, blast-radius-before-fleet-rollout)**: retarget + prove on T0 first
> (`unified-trading-library`, `unified-api-contracts` — the two repos actually blocking real Cloud Build/publish issues
> today), verify a REAL tag mints + a REAL wheel appears in Artifact Registry end-to-end, THEN roll to the rest of the
> `version_source=git-tag` fleet. Repos still on the legacy pyproject-commit path are lower priority (not blocking
> anything today) — enumerate + decide per-repo in a later tick, don't block T0 on auditing all 23.

- [x] [WORKFLOW] P0. ✅ Retargeted `scripts/workflow-templates/semver-agent.yml.tmpl` trigger `branches: [staging]` →
      **`push: branches: [main]` only** — dropped the `workflow_run: quality-gates-v2` leg (redundant: the LDR→main
      promote PR already required-checks v2 before merge, and v2 also runs on `push:[main]`, so the tree is v2-validated
      by the time it lands). Full staging→main audit done (17 hooks classified): checkout / bump-rate scan / dispatch
      payload `"branch"` / label-check status SHA all → main HEAD; **git-tag repos derive the compute-next baseline from
      `git describe --tags` (NOT the stale `staging_versions` map — UTL read 0.43.0 there vs a live 0.56.0 tag → would
      have scanned 13 versions of ancient history → spurious breaking over-bump); legacy repos read the stable
      `versions` map (branch=main dispatch)**; the major-bump/1.0.0 graduation path deliberately still routes through
      staging. Validated: YAML parse OK, `bash -n` OK on all 8 run-blocks, actionlint finding-set IDENTICAL to the old
      copy (0 new issues). Evidence: `unified-trading-pm@0b128a7251a98e1c5f984383055f3dd386289c06` (carve-out
      `scripts/**` direct push).
- [x] [WORKFLOW] P0. ✅ **Rolled to T0 ONLY** (`unified-trading-library` + `unified-api-contracts`) via
      `rollout-workflow-templates.sh --repo <r> --template semver-agent.yml` (the correct tool — it substitutes
      `__VERSION_SOURCE__=git-tag` from the manifest; `rollout-semver-agent.sh` does NOT and would render a broken
      literal). Both installed copies now fire on `push:[main]`, byte-reproducible from the SSOT. Evidence:
      `unified-api-contracts@02a20f3b6e94647b1e2f2cf5b5668590d5f03e33` (quickmerge, landed LDR),
      `unified-trading-library@c143cd96a12588177aa0e37f1c8ed4ada98d54bf` (carve-out `.github/**` direct push —
      quickmerge timed out on transient connectivity + sentinel went stale on a concurrent promote/backmerge).
      **End-to-end live verification (tag mint → wheel in AR) is IN PROGRESS** — requires the changes to first promote
      LDR→main (the promote push itself self-activates the new `push:[main]` trigger), tracked in the VERIFY todo below.
- [ ] [VERIFY] P0. **T0 end-to-end live proof**: after the T0 changes promote LDR→main, confirm the promote push
      self-activates the new `push:[main]` trigger, semver-agent fires on `unified-trading-library` /
      `unified-api-contracts` main (`gh run list --workflow semver-agent.yml`), mints a new `vX.Y.Z` tag
      (`git tag --sort=-creatordate | head`), and `publish-package.yml` publishes a new wheel to Artifact Registry
      (`gcloud artifacts versions list     --package=unified-trading-library --repository=unified-libraries --location=asia-northeast1     --project=central-element-323112`).
      If the promotion cadence is too slow to observe in-session, document reasoned-through vs verified-live.
- [ ] [WORKFLOW] P1. Once T0 is proven, enumerate the remaining `ldr_main` + `version_source=git-tag` repos (23 total)
      and roll the same retarget fleet-wide via `rollout-workflow-templates.sh` (verify 0 drift after). **Known
      already-dead-on-staging: `unified-trading-api`** — its deployed `.github/workflows/semver-agent.yml` still
      triggers on `workflow_run/push:[staging]` (found 2026-07-25; a 3rd git-tag repo whose versioning is still frozen).
      PM's own copy references staging only vestigially (PM is no-staging by design) — do NOT retarget PM's copy without
      care.
- [ ] [DOCS] P1. **Reconcile the stale SSOT contradiction the retarget exposes** (found 2026-07-25):
      `/codex/08-workflows/ci-cd-flow.md` § "Release tag reconciler" still says "minting is moving to the PM reconciler"
      (Option B) — but Option B was DECIDED (`/plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md` §
      "Option B") yet NEVER built, and is architecturally incoherent for git-tag repos
      (`scripts/cicd/reconcile_release_tags.py` hard-refuses to mint for dynamic-versioned repos — "read the version,
      mint the matching tag is circular when the tag defines the version"; the script is a STALL DETECTOR whose own
      message points to semver-agent as the minter). Today's Phase-4 retarget makes **per-repo semver-agent-on-main**
      the live minter — update ci-cd-flow.md § Release tag reconciler + mark the Option-B doc's F2 minting sub-steps
      superseded. (Owner-review edit; codex contract change.)
- [ ] [VERIFY] P2. Confirm `instruments-service` (and any other real consumer, not just the local-path CI build) picks
      up the newly-published wheel where it matters (a real deployed image / Docker build, not just local-path CI).

## Operator decisions / notes

- **dep-order removal** (Phase 1) is the one behavior change with a trade-off (a dependent could reach main before its
  dep; cosmetic since deployments stage from LDR and SIT validates the LDR assembly). Recommendation: remove.
  Reversible.
- **Phase-2/D13 (version-out-of-source)** is shelved, not deleted — the superseded plans remain in archive as the spec
  if it's ever revived.
- **UAC provenance** + the flaky-QG **Cause A** are the two NON-bug blockers (a real violation + a real flake); they are
  in Phase 2 / owner-handled, not "remove the gate." UAC RESOLVED 2026-06-30 — PR #544 merged (v2+SIT-gated), the
  provenance marker advanced, UAC is content-identical on main.
- **Provenance-gate leak (finding, 2026-06-30) — for Ikenna.** The strict-quickmerge provenance gate runs ONLY on
  promote PR _creation_, not on _re-arm_ of an existing clean PR. A later promoter tick found UAC #544 clean and
  re-armed it past the provenance check → it merged on v2 despite the non-QM commits (that's how UAC self-resolved). So
  the quickmerge-provenance gate is NOT airtight — v2+SIT-validated content that bypassed quickmerge can still reach
  main via the re-arm path. For the MVP this is arguably acceptable (content isn't permanently stuck on a provenance
  technicality; it flows once SIT+v2 are green — the MVP's bar). DECISION for Ikenna: accept (MVP-aligned) or close the
  re-arm leak (re-run the provenance check before re-arming an existing PR).
- **Archival caveat (2026-06-30).** `cicd_consolidated_remaining` (archived) was a MULTI-workstream SSOT with ~51 open
  todos beyond the promote pipeline (WS-I service-to-service-auth migration, D13 version-out-of-source, misc P2/P3
  hygiene). Per the operator "everything else out of scope for now" directive these are DEFERRED, living in the archived
  plan as their record; a few codex docs (`/codex/07-security/service-to-service-auth.md`, `ci-cd-flow.md` body) still
  cite it. If any non-pipeline workstream (esp. WS-I service-auth) is still wanted, it needs re-homing into an active
  plan; otherwise the archived plan is the deferred spec.

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` (the pipeline SSOT — update to the MVP at Phase 3).
- `/codex/06-coding-standards/integration-testing-layers.md` (SIT's role).

## Progress Log

- 2026-07-25 (Phase 4 — LIVE end-to-end verification): The retargeted mechanism is **proven live**. UAC's change
  promoted LDR→main, and the promote push (`chore(promote): LDR → main (Option-B direct)`) **self-activated the new
  `push:[main]` trigger** — semver-agent fired on `unified-api-contracts` main at 2026-07-25T20:01:24Z (run
  `30172757220`, conclusion **success**). Its log confirms the full retargeted path ran correctly: "Triggered by push to
  main", `semver_policy=agent`, **"Baseline (latest git tag) … 0.71.0"** (the git-tag baseline — my Step-1 change —
  reading the tag REACHABLE from main HEAD, not the stale `staging_versions` map), commit-range scan,
  `Resolved bump category: breaking → Version: 0.71.0 → 0.72.0 (pre-1.0.0 override → MINOR)`, then the git-tag apply
  path "minting tag v0.72.0" → **"Tag v0.72.0 already exists — idempotent, nothing to do"**, and "Dispatched
  successfully to unified-trading-pm (attempt 1)". So trigger + checkout + git-tag baseline + bump-compute + git-tag
  apply + PM dispatch (branch=main) ALL executed live and correct. **Why no brand-new tag on UAC (yet)**: a pre-existing
  legacy-tag transient — v0.72.0 (minted 2026-06-27 on a staging→_backmerge commit `4ac8be3f`) is reachable from LDR but
  **not yet from main** (main is behind LDR on the promotion backlog), so `git describe @main`=v0.71.0 → computes 0.72.0
  → collides with the existing orphan → safe idempotent-skip (no wrong/dup mint). This **self-resolves**: the
  Option-B-direct promote carries tagged commits into main's ancestry (proven: UTL's v0.56.0 sits on a
  `chore(promote): LDR → main` commit and IS main-reachable), so as the promoter drains, main reaches v0.72.0 and the
  next run mints 0.73.0 fresh; and every FUTURE tag mints on main HEAD (reachable by construction). **UTL is the clean
  fresh-mint case** — its highest tag v0.56.0 is already main-reachable, so on its (still-pending) promote+fire it
  computes a FRESH 0.57.0 → real `git tag` push → publish-package → wheel. A background watcher is observing UTL for
  that fresh mint. **Verified-live**: trigger fires + full workflow logic runs to success (UAC).
  **Reasoned/pending-observation**: the brand-new-tag `git push` + Artifact-Registry wheel (gated only on the
  promotion-backlog drain / a main-reachable-baseline, not on the retarget). New finding logged as the orphan-tag
  transient above; no action needed (self-resolving) beyond letting the promoter run.
- 2026-07-25 (Phase 4 — semver-agent trigger retargeted staging→main, T0 shipped): Retargeted the fleet SSOT
  `semver-agent.yml.tmpl` from the dormant `staging` trigger to **`push: branches: [main]` only** (dropped the redundant
  `workflow_run: quality-gates-v2` leg — the LDR→main promote PR already required-checks v2), and rolled it to T0 only
  (`unified-trading-library` + `unified-api-contracts`) per rule-11 scoping. Shipped: `unified-trading-pm@0b128a725`
  (template), `unified-api-contracts@02a20f3b` (quickmerge), `unified-trading-library@c143cd96` (carve-out, quickmerge
  kept timing out on transient connectivity). Full 17-hook staging→main audit: checkout / bump-rate scan (`origin/main`)
  / dispatch payload `"branch":"main"` / label-check status SHA all retargeted; **git-tag repos now derive the
  compute-next baseline from `git describe --tags`** instead of the PM `staging_versions` map (which was stale by 13
  versions for UTL — 0.43.0 vs a live v0.56.0 tag — and would have scanned ancient history → a spurious breaking
  over-bump, the 2026-06-09 cascade class); legacy repos read the stable `versions` map (matching the PM consumer's
  `branch=main`→`versions[]` write). Validated: YAML parse OK, `bash -n` OK on all 8 run-blocks, actionlint finding-set
  IDENTICAL to the old copy (0 new issues). **DESIGN-CONFLICT RESOLVED (big finding)**: the 2026-07-23 revert
  (`df89ac54`, "minting moves to the PM reconciler (option B)") pointed at a centralized minter that a sub-agent
  investigation proved was **DECIDED but NEVER BUILT and is architecturally incoherent for git-tag repos** —
  `scripts/cicd/reconcile_release_tags.py` hard-refuses to mint for dynamic-versioned repos ("read the version, mint the
  matching tag is circular when the tag defines the version") and is only a STALL DETECTOR whose own message points to
  semver-agent as the minter. That revert was a localized 18-min edit to UTL's copy alone — the SSOT template was NEVER
  reverted (stayed staging-triggered since 2026-07-21). Fleet-wide tag-death empirically confirmed:
  `unified-trading-library`, `unified-api-contracts`, greeks/instruments/mtds/execution-service all have ZERO new v*
  tags since ~2026-06-27, so no live minter exists → no double-mint risk (the stall-detector reconciler simply stops
  alarming once tags flow). Today's operator dispatch (2026-07-25) + the coordinator's active direction chose
  semver-agent-on-main → this retarget is the coherent live fix. **Verified LIVE**: code shipped + all static validation
  green; the fleet-wide versioning-dead root cause confirmed by direct tag-date inspection. **Reasoned-through / PENDING
  live observation**: the tag-mint→wheel end-to-end (self-activates on the first LDR→main promote of these copies —
  GitHub evaluates the pushed commit's `push:[main]` trigger) — tracked in the new [VERIFY] P0 todo; driving/observing
  it next. **Discovered + logged as new todos**: `unified-trading-api` is a 3rd git-tag repo still on the dead staging
  trigger (next-wave rollout); the codex `ci-cd-flow.md` § "Release tag reconciler" + the Option-B doc are now
  stale/contradictory and need reconciliation.
- 2026-07-12 (finding 78 — SIT-fleet-green wired as a REQUIRED check, MVP gate-set item #1 now enforced): Read the
  current shape (`ldr-to-main-promote-fleet.yml`'s existing in-script SIT gate only consults SIT for a BREAKING/unknown
  delta — the 2026-07-07/08 incident's root cause, since a non-breaking delta never checked SIT at all). Built the fleet
  proof table BEFORE touching anything (rule 11): 23 `ldr_main` repos, 21 in `sit_cross_repo_validated_repos`
  (e2e-testing / ibkr-gateway-infra structurally excluded by design, not a gap); last 50 `full-workspace-sit` runs all
  green (48 success / 2 cancelled / 0 failed); confirmed via a live `workflow_dispatch --ref live-defi-rollout` dry-run
  that the design (a FLEET-SHARED "was the last completed SIT run green" signal, not a per-repo tree fingerprint) cannot
  discriminate against the 2 uncovered repos the way the existing per-repo gate does. Implemented:
  `ldr-to-main-promote-fleet.yml` posts `sit-gate/fleet-green` unconditionally on every promote-PR head;
  `pin_branch_protection_rulesets.py` requires it on `ldr_main` repos' `require-quality-gates` ruleset only (also fixed
  a pre-existing naming-drift gap — `require-quality-gates-main` — and extended the script's hardcoded REPOS list from
  17 to the full 25, closing a real drift the investigation surfaced). **Two bugs found only by live canary dispatch,
  not code review**: a `set -e`-killing bare assignment (job conclusion=failure on run `29212085588`) and a wrong
  `gh run list --json` field name (`htmlUrl` → `url`) that silently forced fail-closed every tick — both fixed and
  re-verified live before any ruleset change. Canaried on 2 consumer repos (market-tick-data-service,
  deployment-service) — confirmed the status posts green on real promote-PR heads AND a real PR merges through the new
  required check (market-tick-data-service #533 → main, 2026-07-12T22:55:08Z) — before rolling to the remaining 21 (0
  failures, dry-run re-check shows 0 drift). Fleet-wide unscoped dispatch afterward promoted 2 more repos clean through
  the gate. Total: 4 PM commits (`199f72bbd`→`fc5d717e0`→`69f3f4cad`→`2d81a138e`), all merged to main same session. MVP
  gate-set item #1 (SIT-green) is now actually enforced, matching items #2/#3.
- 2026-07-03 (overnight-alert sweep — self-clone T0 false-red FIXED, image-gate credential gap filed): Root-caused all
  four 2026-07-03 ci-failures alert families. (1) UTL "FAILING on main" + Overnight-T0 + dead-man-switch = ONE bug:
  agent-audit.yml self-referencing `dep_repos` + the dep-clone retry `rm -rf` deleting the job's own workspace (see new
  Phase-2 P0 item; fixed UTL@`9ad8f98d5` + PM #767 self-skip guard — real verification = tonight's ~01:30Z Overnight T0
  must go green). (2) SIT PASSED 04:21Z = auto-recovery working as designed, no action. (3) UAC "PROMOTION LAG 70
  commits / 9404m" = squash-inflated (content diff main…LDR was ONE file +12 lines, carried by promote PR #548,
  v2-green); real gap it surfaced = image-build-gate's missing `AWS_BUILD_ROLE_ARN` (new Phase-2 P1 BLOCKED-CREDENTIALS
  item — operator). Consider making branch-health lag content-based to stop squash-inflated alerts (folds into the
  existing alert-quality track).
- 2026-07-02 (local↔CI parity shipped — PM@`611caf3b`): 4 parallel discovery agents audited CI workflow vs
  base-service.sh vs platform (Linux x86 CI / Ubuntu 24.04 / macOS ARM) vs manifest churn. Key finding: CI runs the SAME
  `quality-gates.sh --no-fix` sliced 3-way, so parity is structural — residual deltas were env vars (closed), unenforced
  slice-partition claim (closed with a blocking guard), the manifest cosmetic-churn loop (root cause:
  `ci_status_consolidator.py` serialization divergence; all 4 writers fixed + blocking canonical guard), and 4 platform
  breaks/divergences (all fixed; the operator-relevant one: quickmerge's bare `python` broke on BOTH stock macOS and
  Ubuntu 24.04 outside a venv). Codified as the "Drive-to-parity hardening" table in ci-cd-flow.md § parity matrix. Two
  sanctioned deltas remain by design: CI's metadata-only fast-path + fix-mode sentinel semantics. REMAINING in this
  plan: the cron-cadence decision (operator) + Phase-3 doc rewrite (Ikenna) + provenance re-arm leak decision (Ikenna).
- 2026-06-30: Created as the single MVP SSOT per operator directive. Supersedes the WS-L complex-pipeline plan family
  (12 plans) and resolves the promotion-stall issue docs (statuses flipped the same day, ahead of the Phase-1 work).
  Phase-1 unblock (gate removal) + Phase-2 health work folded in so nothing is lost on archival.
- 2026-06-30 (Phase 1 + 3 done): Shipped the promoter simplification (PM #729 → main@7ffba64d) — label-check + dep-order
  → advisory, SIT-combination digest removed (per-repo tree check kept). Verified from `main`: mtds #469 +
  deployment-service #321 + features-service #733 all PROMOTED through the MVP gates, no false blocks; only UAC held by
  the kept provenance gate. Archived the 21 superseded/resolved docs (12 plans → archive/2026_06, 9 issue docs →
  archive/issues); ci-cd-flow.md MVP banner added. REMAINING: Phase 2 health items (flaky-QG, ref-cleanup, delete-branch
  guard, cron, YAML-gate coverage), the e2e/ibkr A/B decision, the UAC provenance re-ship (owner), and the Phase-3 full
  ci-cd-flow/CLAUDE.md rewrite (for Ikenna).
- 2026-06-30 (alert sweep + SIT-gate deadlock fixed): Triaged the ci-failures branch-health alerts (10:24→16:10). Most =
  known cron lag (confirmed draining — UAC's 69-commit backlog cleared). Self-healed/moot: features-service Cloud Build
  `f8ee89ba` (transient UAC dep-skew — `VenueVolumeObservation` now on UAC@main; features-service IS promoted, main==LDR
  content-identical) and the 1:45 staging-to-main ibkr failure (pre-#731-flip timing). ONE genuine new bug: e2e-testing
  permanently SIT-gate-blocked (see Phase-2 item above) → FIXED + verified (PM #735 → main@`d0a94729`; run `28441670198`
  promoted e2e-testing, PR e2e-testing#428 armed). **Note for owner (out of MVP scope):** features-service@main image
  build is stale-red (last build failed pre-UAC-catch-up; no rebuild since — main@`f3336945` has no new push). It will
  go green on the next features-service main push or a manual `gcloud builds` retrigger; it does NOT block promotion
  (the pipeline gates on v2+SIT, not the image build) and won't re-alert unless rebuilt.
