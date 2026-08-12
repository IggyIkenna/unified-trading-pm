---
doc_type: plan
title: Convert the remaining fully-duplicated fleet workflow templates into unified-trading-ci reusable workflows
summary: >-
  shared_ci_workflow_repo_extraction_2026_08_06.md extracted the 2 files every repo calls via `uses:` (the actual
  cross-repo dependency surface) into unified-trading-ci. It deliberately left alone a SECOND, larger class: ~9 more
  workflow files that `rollout-workflow-templates.sh` propagates as FULL, byte-identical (or near-identical) copies into
  every one of the 26 fleet repos — not via `uses:`, via literal file-content duplication. Editing any one of them today
  means re-running the rollout script and touching ~24-26 repos' local copies. This plan converts each of those into a
  `workflow_call` reusable workflow hosted once in unified-trading-ci (the same pattern already proven for
  quality-gates-v2/image-build-gate), repoints every repo at a thin caller stub, and DELETES the now-redundant full
  per-repo copies — leaving only the unavoidable local trigger/`with:` stub GitHub Actions requires to exist physically
  in each calling repo.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    unified-trading-ci,
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
    deployment-ui,
    e2e-testing,
    execution-service,
    features-service,
    fund-administration-service,
    greeks-service,
    ibkr-gateway-infra,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    ml-service,
    strategy-service,
    system-integration-tests,
    trading-agent-service,
    unified-api-contracts,
    unified-trading-api,
    unified-trading-library,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags:
  [ci-cd, github-actions, reusable-workflows, workflow-templates, fleet-dedup, unified-trading-ci, incident-followup]
related:
  [
    /plans/archive/2026_08/shared_ci_workflow_repo_extraction_2026_08_06.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
assigned_role: infra
drift_direction: advance-code
depends_on: [shared_ci_workflow_repo_extraction_2026_08_06]
context_scope:
  [
    /plans/archive/2026_08/shared_ci_workflow_repo_extraction_2026_08_06.md,
    /codex/08-workflows/ci-cd-flow.md,
    unified-trading-pm/scripts/workflow-templates/rollout-workflow-templates.sh,
    unified-trading-pm/scripts/workflow-templates/self-hosted-qg-repos.txt,
    unified-trading-ci/.github/workflows/notify-slack.yml,
  ]
source:
  [
    "operator, interactive session, 2026-08-06 — asked, after shared_ci_workflow_repo_extraction_2026_08_06.md's
    dangling-reference sweep closed out, why every fleet workflow update still touches 100s of files across 20+ repos,
    whether those are 'just clones' that could run from unified-trading-ci instead, and directed scoping this out as its
    own full plan including deleting the per-repo copies once centralized. Separately confirmed (same session) that
    mixing a PUBLIC unified-trading-ci with PRIVATE fleet repos as callers is safe — see 'Confirmed technical facts'
    below.",
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Convert the remaining fully-duplicated fleet workflow templates into unified-trading-ci reusable workflows

## Why this plan exists

`shared_ci_workflow_repo_extraction_2026_08_06.md` fixed the actual `uses:`-based cross-repo dependency surface (2
reusable workflows + 2 composite actions) by hosting them in a new public `unified-trading-ci` repo. That plan is
functionally complete. But it deliberately scoped OUT a second, separate problem the operator flagged immediately after:
`unified-trading-pm/scripts/workflow-templates/` propagates **9 more workflow files** into every one of the 26 fleet
repos via `rollout-workflow-templates.sh` — not as thin `uses:` callers, but as **full, largely byte-identical copies**
written directly into each repo's `.github/workflows/`. Any edit to one of these files means re-running the rollout
script and touching ~24-26 repos' worth of copies (confirmed painful in practice: this is the literal "100s of files
changed across 20+ repos" the operator was describing). This plan closes that gap using the exact same technique already
proven for quality-gates-v2/image-build-gate: host the real logic once in `unified-trading-ci` as a `workflow_call`
reusable workflow, and replace every repo's full copy with the same kind of thin caller stub already in production for
the first 2 files.

**The operator explicitly directed deleting the per-repo full copies once centralized** — this plan does that, but
scoped precisely: the local **caller stub** (trigger config + `uses:` + `with:`/`secrets:`) is NOT deletable — GitHub
Actions has no mechanism for a repo to run a workflow that lives only in another repo without SOME file physically
present in `.github/workflows/` declaring the trigger. What gets deleted is the ~50-1000+ lines of actual job logic each
repo currently carries a full copy of; what replaces it is a stub of the same size class already shipped for
quality-gates-v2 (~20-200 lines, mostly trigger/dep-closure/`with:` config, not business logic).

## Confirmed technical facts (verified 2026-08-06, not assumed — read the actual files before trusting this section)

- **9 candidate files, characterized by grepping every template in `scripts/workflow-templates/` for `{{...}}`
  substitution markers** (excludes `image-build-gate.yml` + `quality-gates-v2.yml.tmpl`, already extracted):
  - **8 files are LITERALLY BYTE-IDENTICAL across every repo today — zero template markers, zero per-repo customization
    of any kind**: `main-backmerge-to-ldr.yml` (452L), `major-bump-issue-handler.yml` (323L), `notify-slack.yml` (464L,
    but see the notify-slack-specific note below — likely NOT migrated, see todo 1), `request-major-bump.yml` (219L),
    `staging-backmerge-to-ldr.yml` (231L), `staging-lock-check.yml` (110L), `update-dependency-version.yml` (350L),
    `version-registry-notify.yml` (48L). This is the simplest possible conversion target: no `{{DEP_REPOS}}`-style
    substitution to turn into a `with:` input, just the file's own content hosted once + every repo's copy replaced with
    an unparameterized (or near-unparameterized) `uses:` stub.
  - **1 file has ONE real per-repo variance point**: `semver-agent.yml.tmpl` (1034 lines!) uses `{{RUNS_ON}}`, same
    substitution mechanism as `quality-gates-v2.yml.tmpl`'s `{{DEP_REPOS}}`/`{{RUNS_ON}}` — which was ALREADY solved for
    that file via a `with: self_hosted_runner_labels:` input on the live reusable workflow. The identical pattern
    applies directly; this is precedent, not a new problem.
- **`{{RUNS_ON}}` resolves via `get_runs_on_value()` in `rollout-workflow-templates.sh`**: `[self-hosted, glue]` if the
  repo is listed in `scripts/workflow-templates/self-hosted-qg-repos.txt`, else GitHub-hosted `ubuntu-latest`. Real,
  necessary variance (not accidental duplication) — becomes a `with:` input on the reusable workflow, same shape as
  `quality-gates-v2.yml`'s already-shipped `self_hosted_runner_labels` input.
- **`notify-slack.yml` is structurally ALREADY a reusable workflow** (`on: workflow_call:` at its own top, confirmed by
  direct read) — it is not itself "logic that needs converting," it is logic ALREADY in the right shape, just not
  centrally hosted. `unified-trading-ci` already carries its own copy (confirmed via `ls`, 27062 bytes, byte-identical
  to PM's) because `unified-trading-ci`'s own `python-quality-gates-v2.yml` calls it locally
  (`uses: ./.github/workflows/notify-slack.yml`) — this ALREADY works today with zero further action, since both files
  live in the same repo now.
  - **PM's own `.github/workflows/notify-slack.yml` is NOT a rollout candidate** — confirmed via
    `grep -rl "uses: ./.github/workflows/notify-slack.yml" .github/workflows/`: **44 PM-internal-only workflows** call
    it locally (`ldr-to-main-promote.yml`, `sit-gate.yml`, `cloud-build-router.yml`, `semver-agent.yml`, etc.) — none of
    these are fleet-templated to other repos. PM keeps its own copy regardless of anything else this plan does.
  - **Whether any OTHER fleet repo's local `notify-slack.yml` copy is still needed once `main-backmerge-to-ldr.yml` +
    `semver-agent.yml` + `staging-backmerge-to-ldr.yml` are centralized is NOT yet confirmed** — if a given repo's ONLY
    local caller of `notify-slack.yml` is one of those 3 files, that repo's local copy becomes fully dead once they
    migrate and should be deleted too; if the repo has some OTHER local-only workflow that also calls it, the copy must
    stay. **This is todo 1** — a real per-repo audit, not assumed either way here.
- **2 of the 8 flat-copy files call `notify-slack.yml` LOCALLY** (confirmed via
  `grep -n "uses: \./\.github/workflows/notify-slack\.yml"`): `main-backmerge-to-ldr.yml` (line 437) and (per the file's
  own `{{RUNS_ON}}` sibling) `semver-agent.yml.tmpl` — both need this dependency edge tracked through the migration:
  once hosted IN `unified-trading-ci`, their local `./` reference resolves automatically against `unified-trading-ci`'s
  own already-present `notify-slack.yml` copy — no separate cross-repo `uses:` rewrite needed for THIS edge, unlike the
  original `unified-trading-pm/.github/workflows/python-quality-gates-v2.yml → notify-slack` edge did NOT need rewriting
  either, for the identical reason.
- **`request-major-bump.yml`'s own header comment claims "(thin caller -> PM reusable workflow)" — VERIFIED FALSE by
  direct read**: its only `uses:` line is `actions/checkout@v5`; it does not call into any PM-hosted reusable workflow
  at all. Stale/inaccurate comment in the source template — flag for correction regardless of this plan's outcome (todo
  9).
- **Public/private visibility mix is SAFE and already proven live** — checked explicitly because the operator asked:
  GitHub Actions permits ANY repo (public or private) to call a `uses:` reusable workflow hosted in a PUBLIC repo, with
  zero extra configuration; the restriction that caused the ORIGINAL `main_ci_red` incident only runs the other
  direction (a public caller cannot resolve a `uses:` into a PRIVATE callee). Confirmed via
  `gh repo view --json visibility` across the fleet 2026-08-06: `unified-trading-ci` is PUBLIC; 7 of the 26 fleet repos
  (`execution-service`, `features-service`, `market-tick-data-service`, `strategy-service`, `agent-orchestrator`,
  `ml-service`, `e2e-testing`) are PRIVATE. Live proof: `execution-service`/`strategy-service` (both PRIVATE) already
  ran `quality-gates-v2` successfully against the PUBLIC `unified-trading-ci` host during
  `shared_ci_workflow_repo_extraction_2026_08_06.md`'s dangling-reference sweep, same session. **The one real residual
  risk this design creates**: `unified-trading-ci` is now itself fleet-critical, load-bearing infrastructure — if IT is
  ever flipped private (the identical class of mistake that started the whole saga, just on the new host), every PUBLIC
  fleet repo breaks the same way PM breaking did. Worth a branch-protection/visibility-alerting recommendation, not a
  blocker — see todo 10.
- **26 repos total in `workspace-manifest.json`** (includes `unified-trading-pm` and `unified-trading-ci` themselves):
  `agent-orchestrator, alerting-service, batch-live-reconciliation-service, client-reporting-api, deployment-api, deployment-service, deployment-ui, e2e-testing, execution-service, features-service, fund-administration-service, greeks-service, ibkr-gateway-infra, instruments-service, market-data-processing-service, market-tick-data-service, ml-service, strategy-service, system-integration-tests, trading-agent-service, unified-api-contracts, unified-trading-api, unified-trading-ci, unified-trading-library, unified-trading-pm, unified-trading-system-ui`.
- **Not every repo necessarily carries every one of the 9 templates** — `rollout-workflow-templates.sh` supports
  `--repo`/`--template` filtering and the header comment documents a UI-only tier (`workflow-templates-ui/`) that is NOT
  part of this plan's scope. **Todo 1 confirms the actual per-repo distribution** before any conversion work starts — do
  not assume uniform fleet-wide presence.

## Design decisions (stated so a later reader can course-correct, not treated as pre-litigated)

- **One converted reusable workflow per source template, all hosted in `unified-trading-ci`** — mirrors the existing
  `python-quality-gates-v2.yml`/`image-build-validate.yml` placement; no new repo needed.
- **`notify-slack.yml` itself does NOT move as part of this plan's headline conversion** — it's already correctly
  positioned (PM keeps its 44-consumer local copy per `shared_ci_workflow_repo_extraction_2026_08_06.md`'s original
  ruling; `unified-trading-ci` already has its own copy for its internal use). Todo 1's per-repo audit determines
  whether OTHER repos' copies become deletable as a SIDE EFFECT of migrating their callers — this plan does not force
  that either way.
- **Every repo keeps a physical caller-stub file — never a bare cross-repo `uses:` with nothing local.** This is a hard
  GitHub Actions constraint, not a design preference; restated here because the operator's literal ask ("deleting all
  the per-repo workflows") could otherwise be misread as removing the trigger file entirely, which would silently
  disable that workflow fleet-wide.
- **Wave order mirrors the original plan's canary-then-waved approach**: one low-churn repo first per template family,
  verify a real GitHub Actions run (not just local QG) resolves and behaves identically, THEN fan out. Given 8 of 9
  targets are byte-identical today, the FIRST correctly-converted file de-risks the rest — todo ordering reflects this
  (todo 3 does ONE file fully end-to-end including a live CI-run verification before todo 4 starts the other 7 in
  parallel).
- **`scripts/workflow-templates/*.yml`/`*.yml.tmpl` for these 9 files get DELETED from PM once every repo's copy is
  converted** — the template's job (being the thing `rollout-workflow-templates.sh` propagates) goes away once nothing
  propagates a full copy anymore; the reusable workflow's canonical source becomes
  `unified-trading-ci/.github/workflows/<name>.yml` itself, edited directly there (same as
  `python-quality-gates-v2.yml`/`image-build-validate.yml` already work). `rollout-workflow-templates.sh` itself gets
  updated to stop listing these 8-9 files as rollout targets, but is NOT deleted (still needed for whatever remains
  templated, if anything, and for the UI-only tier).

## Todos

- [x] 1. [INFRA] P0. **Per-repo distribution + `notify-slack.yml` dependency audit** — see "Todo 1 findings" below.
      Live-bug fix shipped: execution-service@d537b812e, e2e-testing@14bec17, market-data-processing-service@8c5430aa.
- [x] 2. [INFRA] P0. **Correct `request-major-bump.yml`'s stale header comment** — the false claim ("thin caller -> PM
      reusable workflow") turned out to live in `rollout-workflow-templates.sh`'s own header listing (line 14), not
      inside `request-major-bump.yml` itself — corrected to describe what the file actually does (a self-contained
      canonical flat copy; its only `uses:` is `actions/checkout@v5`, no reusable-workflow call).
      `unified-trading-pm@037e181559`.
- [x] ✅ 3. [INFRA] P0. **Convert ONE file end-to-end as the pattern-proof — DONE 2026-08-07.**
      `version-registry-notify.yml` hosted in `unified-trading-ci` (`unified-trading-ci@b498ec2`) with a
      `self_hosted_runner_labels` input — **correction to this plan's own "Confirmed technical facts": the file is NOT
      zero-customization, its `runs-on` uses the `__RUNS_ON__` double-underscore substitution
      (`rollout-workflow-templates.sh`'s `get_runs_on_value()`), which the plan's `{{...}}`-only grep missed. Applies to
      all 9 files, not just this one — re-check each for `__RUNS_ON__` before assuming "zero markers."** Canary:
      `trading-agent-service` (lowest tag-count, public, non-CI-critical) — thin stub shipped
      (`trading-agent-service@baed4337`). Live-verified via a real (non-3-part, guard-skipped by design so it can't
      pollute the real Firestore version registry) tag push: `gh run view 31180100767` shows
      `Uses: IggyIkenna/unified-trading-ci/.github/workflows/version-registry-notify.yml@refs/heads/main (b498ec28091a0f810fb9ab059e77b4b3c08d4b46)`,
      `conclusion: success`, and the SAME "not plain 3-part X.Y.Z; not forwarding" guard message the original flat copy
      would have produced — behavior-equivalent, cross-repo `uses:` resolution proven live. Test tag deleted after
      verification (`v0.12.12-ci-canary-test`, both remote + local).
- [x] ✅ 4. [INFRA] P1. **Convert 5 of the 6 remaining flat-copy files — DONE 2026-08-07** (`main-backmerge-to-ldr.yml`,
      `major-bump-issue-handler.yml`, `request-major-bump.yml`, `staging-backmerge-to-ldr.yml`,
      `update-dependency-version.yml` — `staging-lock-check.yml` split out to todo 11, see below, a real landmine this
      todo's original scope didn't anticipate). Hosted all 5 in `unified-trading-ci@892bb81` with a
      `self_hosted_runner_labels` input (same pattern as todo 3). **Correction to this plan's own "Confirmed technical
      facts" — confirmed via independent re-research, not just todo 3's single-file finding**: ALL 6 files (not just
      `version-registry-notify.yml`) contain `__RUNS_ON__`, contradicting the "8 files are LITERALLY BYTE-IDENTICAL...
      zero template markers" claim. **`request-major-bump.yml` needed an additional fix actionlint caught**: its
      `workflow_dispatch: inputs:` (proposed_version/reason/approver) had to be mirrored onto the reusable workflow's
      `workflow_call: inputs:` too — `github`/`inputs` context rules differ between the two trigger types. **PM
      exception**: `major-bump-issue-handler.yml` and `request-major-bump.yml` were NOT converted for
      `unified-trading-pm` — independent re-research found PM's local copies are genuinely customized (dedup/cooldown
      Slack alerting via `notify-slack.yml`, richer than the fleet canonical), not stale; converting them would have
      regressed PM. PM's `main-backmerge-to-ldr.yml` matched canonical exactly and WAS converted
      (`unified-trading-pm@01c3dbbab9`). Fan-out order: `unified-api-contracts`/`unified-trading-library` first, then
      the other 22 non-PM carriers, then PM. Every one of the 24 non-PM carriers (main-backmerge-to-ldr.yml) + 24 (the
      other 4 files) shipped + independently re-verified via a direct `git show origin/live-defi-rollout:<path>` content
      check per repo (not just trusting quickmerge's own "✅ Landed" message — see the shared-clone race note below) —
      zero failures on the final sweep. Also had to re-baseline
      `scripts/quality_gates/workflow_template_drift_baseline.json` (PM's own local-only cross-repo parity checker
      flagged the 6 new `unified-trading-ci` reusable-workflow files as "new drift" against the old flat-copy template —
      correctly caught, explicitly blessed via `--baseline-write --baseline-write-allow-additions`). **Real gap found in
      `hosted-baseline.sh`-adjacent tooling, unrelated to this plan but discovered while shipping**: none — that was the
      separate PM self-hosted-revert session earlier the same day. **Process note (recurring today)**: this shared
      workspace is under heavy concurrent multi-session load — hit the
      `shared_clone_concurrent_commit_message_swap_2026_07_28.md` race repeatedly (quickmerge's own "already committed"
      check raced against a different session's commit and silently no-op'd at least twice, once losing uncommitted
      generated content entirely with an empty autostash left behind) and one genuine inherited-foreign-WIP stash-pop
      conflict (market-tick-data-service: `cloudbuild.yaml`/`Dockerfile`, unrelated GAR-auth hardening WIP — reset to
      HEAD without dropping the stash, never touched the content). Recovery pattern that worked every time: regenerate
      (cheap, script-driven) → `git add`+`git commit` immediately (close the race window) → quickmerge to push →
      **always independently verify via `git show origin/<branch>:<path>`**, never trust the tool's own success message
      alone. CI-VM impact of this rollout (resource-history-sampler, 5s granularity): real burst during the 24-repo push
      wave (max load_avg_1m 7.84, max CPU 60.7%, max RAM 28.6%, zero OOM kills), settled back to idle immediately after
      — the box absorbed a genuine fleet-wide CI wave cleanly at its current 16 vCPU/32GB size.
- [x] ✅ 5. [INFRA] P1. **Convert `semver-agent.yml.tmpl` — DONE 2026-08-07.** **Correction to this plan's own claim**:
      the file has 4 real per-repo variance points, not 1 — `__RUNS_ON__` (via `with: self_hosted_runner_labels:`,
      confirmed as double-underscore not `{{RUNS_ON}}`) PLUS `__REPO_NAME__`/`__SOURCE_DIR__`/`__VERSION_SOURCE__` (via
      new `with: repo_name/source_dir/version_source:` inputs) — found by verifying rather than trusting the plan's own
      "1 real variance point" claim, same discipline todo 3/4 already applied. Also found and fixed: (a) the conversion
      tooling (`make_reusable.py`) was silently dropping the file's top-level `env:` block entirely (jobs: wasn't the
      only section with markers); (b) a SEPARATE session's same-day squash-promote patch-fallback fix
      (`semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md`) had landed on 21 repos' rendered copies but
      never made it back into this canonical template — ported it in before converting, closing an SSOT-drift gap that
      would have silently regressed those repos on any future `rollout-workflow-templates.sh` run. Hosted in
      `unified-trading-ci` (`65111fc8890eae41df41c1fa19e663ec8ef7ff09`), actionlint-clean, structurally verified
      (YAML-parsed + `inputs`/`env`/`concurrency` blocks confirmed present). All 23 fleet repos converted to thin stubs
      and independently verified via `git show origin/live-defi-rollout:.github/workflows/semver-agent.yml` (not just
      trusting quickmerge's own success message — this session hit quickmerge.sh's own defensive "Reset to origin"
      discarding an already-made local commit 3 separate times, recovered each via `git cherry-pick`):
      agent-orchestrator, alerting-service, batch-live-reconciliation-service, trading-agent-service (canary),
      deployment-api, client-reporting-api, deployment-service, deployment-ui, e2e-testing, execution-service,
      features-service, fund-administration-service, greeks-service, ibkr-gateway-infra, instruments-service,
      market-data-processing-service, market-tick-data-service (its previously-tracked pre-existing test blocker had
      resolved by the time of this run — QG passed clean), ml-service, strategy-service, system-integration-tests,
      unified-api-contracts, unified-trading-api, unified-trading-library, unified-trading-system-ui. PM's own copy (640
      lines, genuinely customized — has its own `concurrency:` block already) intentionally NOT converted, same
      precedent as todo 4's PM exception for major-bump-issue-handler.yml/request-major-bump.yml. **Done-when status**:
      content/structure fully verified per-repo; the cross-repo `workflow_call` resolution mechanism itself was already
      live-proven end-to-end by todo 3's canary run — a full live re-verification specifically of the ported
      patch-fallback logic on a real `push:[main]` was not forced this session (would need an actual promote cycle per
      repo); the fleet promoter is healthy (see Progress Log) so this will exercise naturally on each repo's next real
      promotion, not left as a gap requiring further action.
- [x] ✅ 6. [INFRA] P2. **Delete now-dead `notify-slack.yml` copies — DONE 2026-08-07.** Re-verified per-repo rather
      than relying solely on todo 1's now-stale audit (todo 1 predates today's semver-agent.yml migration, which is
      exactly what made several repos' last local caller disappear) — grepped every fleet repo's `.github/workflows/`
      for any remaining `uses: ./.github/workflows/notify-slack.yml` reference. Result: 22 of 23 fleet repos had zero
      remaining local callers (their only callers were `main-backmerge-to-ldr.yml`/`staging-backmerge-to-ldr.yml`/
      `semver-agent.yml`, all now thin stubs whose logic — including the `notify-slack.yml` call — moved into
      `unified-trading-ci`). Deleted and independently verified via
      `git show origin/live-defi-rollout:     .github/workflows/notify-slack.yml` (absent) in each: agent-orchestrator,
      alerting-service, batch-live-reconciliation-service, client-reporting-api, deployment-api, deployment-ui,
      e2e-testing, execution-service, features-service, fund-administration-service, greeks-service, ibkr-gateway-infra,
      instruments-service, market-data-processing-service, market-tick-data-service, ml-service, strategy-service,
      system-integration-tests, trading-agent-service, unified-api-contracts, unified-trading-api,
      unified-trading-library, unified-trading-system-ui. **`deployment-service` KEPT** — still has a live local caller,
      `cloud-run-traffic-drift-check.yml`, unrelated to this migration. **PM's own copy KEPT** untouched (44
      internal-only consumers, confirmed unrelated). Process note: `unified-api-contracts` and `unified-trading-library`
      each hit quickmerge.sh's "Reset to origin" local-commit-discard bug during this todo too (on top of the 3 times
      during todo 5) — same recovery (`git cherry-pick`) worked every time; root cause is ordinary high push-contention
      from multiple concurrent sessions on the same repos' remotes (confirmed via `ps aux` showing other active Claude
      Code tabs working the same repo set), not a defect in this todo's approach.
- [x] ✅ 7. [INFRA] P2. **Delete the redundant template sources — DONE 2026-08-07.** **Correction to this plan's own "9"
      count**: only 7 of the original 9 candidate files are actually redundant now — `notify-slack.yml` was never
      migrated (PM's own copy stays the canonical source per this plan's own Design decisions) and
      `staging-lock-check.yml` is explicitly excluded pending todo 11's required-check-name fix, so deleting either
      would have broken something still live. Deleted the correct 7 from
      `unified-trading-pm/scripts/workflow-templates/`: `main-backmerge-to-ldr.yml`, `major-bump-issue-handler.yml`,
      `request-major-bump.yml`, `staging-backmerge-to-ldr.yml`, `update-dependency-version.yml`,
      `version-registry-notify.yml`, `semver-agent.yml.tmpl`. Updated `rollout-workflow-templates.sh`'s header comment
      (its "main rollout loop" is a directory glob, not a hardcoded list — nothing else to edit there once the files are
      gone). Verified via `bash rollout-workflow-templates.sh --dry-run`: only `image-build-gate.yml`,
      `notify-slack.yml`, `staging-lock-check.yml`, and `quality-gates-v2.yml.tmpl` still process (the 2 correctly-kept
      tier-1 templates plus the 2 from the separate, earlier `shared_ci_workflow_repo_extraction_2026_08_06.md`
      migration). Shipped `unified-trading-pm@79c4a72737`, independently verified via
      `git show origin/live-defi-rollout:     scripts/workflow-templates/main-backmerge-to-ldr.yml` (path does not
      exist) and the header comment no longer listing the 4 it used to.
- [x] ✅ 8. [INFRA] P2. **Fleet-wide dangling-reference re-sweep — DONE 2026-08-08.** Ran
      `grep -rln "uses:.*unified-trading-pm/.github/"` (plus a broader path-substring sweep, not just `uses:` lines, and
      across `.yml`/`.yaml`/`.sh`/`.py`/`.md`, not just workflow files) across all 24 fleet repos + PM itself, excluding
      `.claude/worktrees/` and `stale-pre-history-rewrite` noise, for all 9 converted files (`image-build-gate.yml`,
      `quality-gates-v2.yml` from the prior `shared_ci_workflow_repo_extraction_2026_08_06.md` migration, plus this
      plan's `version-registry-notify.yml`, `main-backmerge-to-ldr.yml`, `major-bump-issue-handler.yml`,
      `request-major-bump.yml`, `staging-backmerge-to-ldr.yml`, `update-dependency-version.yml`, `semver-agent.yml`).
      **Result: zero unexpected hits.** The only `unified-trading-pm/.github/` matches found were PM's own
      `agent-audit.yml`/`hosted-baseline/agent-audit.yml` (both reference `python-quality-gates-v2.yml`, not one of
      the 9) and `cassette-drift-check.yml`/`removed-symbols-workspace-sweep.yml` (both reference the `persist-event`
      composite action, not one of the 9) — genuine still-alive self-references, not dangling. Also checked PM's own
      docs/scripts for lingering references to the 7 deleted `scripts/workflow-templates/*.yml(.tmpl)` template sources
      (todo 7): zero hits outside `plans/archive/`. Unlike todo 23's precedent (which missed `agent-audit.yml` +
      composite-action consumers because its sweep only checked 2 caller files per repo), this sweep intentionally
      checked ALL file types and found no equivalent miss for this plan's 9 files.
- [x] ✅ 9. [DOC] P2. **Update `/codex/08-workflows/ci-cd-flow.md` — DONE 2026-08-08.** Added a "Second wave — the rest
      of the flat-copy fleet templates moved too (2026-08-07/08)" paragraph right after the existing "Host moved to
      `unified-trading-ci` (2026-08-06)" note, listing all 7 newly-hosted files (`version-registry-notify.yml`,
      `main-backmerge-to-ldr.yml`, `major-bump-issue-handler.yml`, `request-major-bump.yml`,
      `staging-backmerge-to-ldr.yml`, `update-dependency-version.yml`, `semver-agent.yml`), the
      `self_hosted_runner_labels` + `repo_name`/`source_dir`/`version_source` input shapes, the PM exception (3 files
      kept local/customized), the `notify-slack.yml` cascade-deletion consequence, and what
      `rollout-workflow-templates.sh` is now scoped to (`image-build-gate.yml` + `quality-gates-v2.yml.tmpl` as
      already-converted stubs, `notify-slack.yml` as the still-canonical full-content file, `staging-lock-check.yml` as
      the deliberately-not-yet-converted file pending todo 11). Describes the POST-this-plan state, not mid-migration.
- [ ] 10. [INFRA] P3. _(stretch, optional)_ **Add a branch-protection / visibility-change alert on
      `unified-trading-ci`** — given this plan makes it fleet-critical (11 reusable workflows/actions hosted there once
      this plan + the prior one both ship), consider whether the same accidental-private-flip class of incident that
      started `shared_ci_workflow_repo_extraction_2026_08_06.md` warrants a standing guard (a scheduled check via
      `gh api repos/IggyIkenna/unified-trading-ci` asserting `visibility == public`, alerting if not) rather than
      relying on someone noticing fleet-wide CI going red again. Genuinely optional — the risk already exists
      identically for `unified-trading-pm` today and has no such guard either; scope this as its own small follow-up if
      pursued, don't block this plan on it.

- [x] ✅ 11. [INFRA] P1. **`staging-lock-check.yml` converted — DONE 2026-08-08.** Applied option (a): updated the
      `require-staging-lock-check` ruleset's `required_status_checks` context string on all 16 affected repos
      (`alerting-service`, `batch-live-reconciliation-service`, `client-reporting-api`, `deployment-api`,
      `deployment-service`, `deployment-ui`, `execution-service`, `ibkr-gateway-infra`, `instruments-service`,
      `market-data-processing-service`, `market-tick-data-service`, `strategy-service`, `system-integration-tests`,
      `trading-agent-service`, `unified-api-contracts`, `unified-trading-library`) from bare `"check-staging-lock"` to
      `"check-staging-lock / check-staging-lock"` via the GitHub rulesets API, THEN converted. **Real bug found + fixed
      during the canary verification (not anticipated by this todo's own text)**: this file's canonical template carries
      its own `concurrency:` block. `make_reusable.py`/`make_stub.py`'s existing behavior (proven fine for the other 9
      files) copies that block into BOTH the hosted callee AND the local caller stub — for a `pull_request`-triggered
      caller specifically, having the IDENTICAL concurrency group (`${{ github.workflow }}-${{ github.ref }}`) declared
      on both sides is a self-referential collision that makes GitHub fail the ENTIRE run with zero jobs scheduled
      ("This run likely failed because of a workflow file issue", conclusion=`failure`) — silent and total, not a
      partial/job-level failure. Root-caused via 7 bisection iterations against a live throwaway branch
      (`trading-agent-service`, PR #402, closed without merging): confirmed NOT an issue for the other 8 files'
      `push`-triggered callers (`semver-agent.yml` has the identical duplicate-concurrency-declaration pattern and works
      live), so the fix (`SKIP_CALLER_CONCURRENCY` in `make_stub.py`) is scoped to this one `pull_request`-triggered
      file rather than applied fleet-wide. Live-verified after the fix: check-run
      `"check-staging-lock / check-staging-lock"` conclusion=`success` (run 31236639223). All 24 fleet repos converted
      to thin caller stubs and independently verified via
      `git show origin/live-defi-rollout:.github/workflows/staging-lock-check.yml | grep -c unified-trading-ci`
      (expect 3) — not just quickmerge's own exit code, which this session proved unreliable: 7 of the 24 repos'
      first-attempt pushes silently discarded the commit via quickmerge's known "Reset to origin" bug
      (`quickmerge_agent_regate_resets_branch_loses_local_commit_2026_07_31.md`) despite reporting `exit=0` —
      `deployment-service`, `execution-service`, `market-data-processing-service`, `strategy-service`,
      `unified-api-contracts` (needed 3 attempts total), `unified-trading-library` (needed 3 attempts total), and
      `unified-trading-system-ui` — every one recovered via `git log --all --oneline --grep=...` + `git cherry-pick`,
      re-verified independently after each retry. Deleted the now-redundant
      `scripts/workflow-templates/staging-lock-check.yml` template source and updated `rollout-workflow-templates.sh`'s
      header comment + stale usage examples (dry-run verified: only `image-build-gate.yml`, `notify-slack.yml`,
      `quality-gates-v2.yml.tmpl` still process). Shipped: `unified-trading-ci@686bca7` (hosted reusable workflow, final
      content after the debug session), `unified-trading-pm@79223bec17` (make_stub.py fix),
      `unified-trading-pm@b7e41849d6` (template deletion + script update, landed as a rebased sha on origin), plus one
      commit per fleet repo (24 total).

## Todo 1 findings (2026-08-06)

**Distribution is NOT uniform** (confirmed, don't assume): `unified-trading-ci` carries none of the 9 (it's the future
host, plus its own internal-use `notify-slack.yml` for `python-quality-gates-v2.yml`, unrelated to this audit).
`unified-trading-pm` carries `main-backmerge-to-ldr.yml`/`major-bump-issue-handler.yml`/`notify-slack.yml`/
`request-major-bump.yml`/`semver-agent.yml` but NOT `staging-backmerge-to-ldr.yml`/`staging-lock-check.yml`/
`update-dependency-version.yml`/`version-registry-notify.yml` (PM's own promotion model differs — not a defect, just
documented per this todo's "don't assume uniform presence" instruction).

**`notify-slack.yml` verdict, all 21 non-PM/non-CI repos that carry it**: the ONLY local callers anywhere in the fleet
are `main-backmerge-to-ldr.yml` and/or `semver-agent.yml` — **zero exceptions found** (checked every repo's full
`.github/workflows/` tree, not just the 9 candidate templates). Once todos 4 (main-backmerge) and 5 (semver-agent) both
migrate to `unified-trading-ci`-hosted reusable workflows, **every one of these 21 repos' local `notify-slack.yml`
copies becomes deletable** (todo 6) — the design decision's "OTHER local-only workflow might still depend on it" caveat
never actually materializes anywhere in the fleet.

**LIVE BUG FOUND, FIXED same session (P0, not part of this plan's original scope)**: `execution-service`, `e2e-testing`,
and `market-data-processing-service` carry `main-backmerge-to-ldr.yml` + `semver-agent.yml` (both of which call
`./.github/workflows/notify-slack.yml` locally) but were **missing the `notify-slack.yml` file itself** — a pre-existing
gap in `rollout-workflow-templates.sh`'s history, unrelated to today's `unified-trading-ci` extraction. Confirmed via
`gh run list`: every push to these 3 repos' `main-backmerge-to-ldr.yml`/`semver-agent.yml` since at least 2026-08-05 has
failed instantly (0s duration, GitHub's own diagnosis "workflow file issue") — a **multi-day live CI outage** on their
LDR→main backmerge and semver-tagging pipelines, discovered incidentally while auditing for this plan. Fixed via
`bash scripts/workflow-templates/rollout-workflow-templates.sh --template notify-slack.yml` (the sanctioned rollout
mechanism, dry-run verified first) + a quickmerge per repo. Not a consequence of anything in this plan's design —
flagged to the operator directly in-session, fixed immediately per the small+clear triage bar.

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — gate set / quickmerge / reusable-workflow rollout mechanism. **CORRECTED
  2026-08-12 (/plan-reconcile)**: todo 9 already applied its update 2026-08-08 (see Todos above) — this line was stale,
  still describing the update as pending.
- `/plans/archive/2026_08/shared_ci_workflow_repo_extraction_2026_08_06.md` — the prior plan this one directly follows;
  its "Confirmed technical facts" + Progress Log document the base state (the 2-file extraction, the revert incident,
  the dangling-reference sweep) this plan's own facts build on.

## Progress Log

- **na-eligibility-audit 2026-08-09 (round11 RECLASSIFY+satellite-extraction sweep, infra tranche)**: KEEP-NA, valid —
  unchanged. Sole open todo (todo 10, `[INFRA] P3`, "add a branch-protection/visibility-change alert on
  `unified-trading-ci`") is still explicitly self-described as "genuinely optional... consider whether... warrants a
  standing guard" — a design/priority call on WHETHER to build it, not a spec a worker can execute without that decision
  being made first; not satellite-extractable as-is. Checked against this round's accumulated-precedent list (IAM
  self-service, D16 all-repos, S5.1 tiering, plan-destination-AO-default, escalation-N=3-days, reversibility-qualified
  deletes, Option B retired, GSM secret + 5 Slack webhooks) — none resolve the "should we build this at all" question.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — unchanged since 2026-08-07. Re-read
  end-to-end; `grep -cE '^- \[ \]'` = 1, matching (todo 10 only). Checked against today's operator-Q&A rulings cheat
  sheet: no precedent matches a "should we build a standing visibility-change alert" question, and a fresh grep for any
  existing repo-visibility-monitoring precedent fleet-wide found none — todo 10 remains a genuine, explicitly
  self-described "genuinely optional... consider whether... warrants a standing guard" design/priority call, not a
  bounded spec. `assigned_vm: NA` correct.
- **2026-08-06 (interactive session)**: Plan authored immediately after
  `shared_ci_workflow_repo_extraction_2026_08_06.md`'s dangling-reference sweep closed out. Operator asked why fleet
  workflow updates still touch 100s of files across 20+ repos, whether those are "just clones" that could run from
  `unified-trading-ci` instead, and directed scoping this out as its own full plan including deleting the per-repo
  copies once centralized. All "Confirmed technical facts" above were verified via direct file reads / `gh` CLI calls in
  the same session before writing a single todo — see that section for the full evidence trail. Separately verified:
  public `unified-trading-ci` + mixed public/private fleet callers is safe (live proof: `execution-service`/
  `strategy-service`, both PRIVATE, already ran `quality-gates-v2` successfully against it). No phase executed yet
  beyond authoring; todo 1 is the next step.

- **2026-08-06 (later, interactive session) — todo 1 shipped**: Full per-repo distribution audit + `notify-slack.yml`
  dependency audit complete (see "Todo 1 findings" above). Incidentally discovered a live, multi-day CI outage
  (`execution-service`/`e2e-testing`/`market-data-processing-service` missing `notify-slack.yml` entirely despite two
  other rolled-out templates calling it locally) — flagged to the operator immediately, fixed same session via the
  sanctioned rollout script + a quickmerge per repo (`execution-service@d537b812e`, `e2e-testing@14bec17`,
  `market-data-processing-service@8c5430aa`). Todo 2 (request-major-bump.yml stale comment) is next.
- **context-scout 2026-08-07**: re-verified context_scope (5 entries) -- all 5 still resolve (plan, codex SSOT, and 3
  source paths already correctly scoped by the plan's author at creation); unchanged.
- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid. This is a large (8 open todos), high-blast-radius
  migration of fleet-wide GitHub Actions CI/CD machinery (26 repos, `workflow_call` reusable-workflow hosting + per-repo
  caller-stub replacement + deletion of the now-redundant full copies) — exactly the class this skill's own guidance
  flags for skepticism: "a multi-file, multi-day rewrite of live-dispatch-critical-path machinery" where
  "bounded/bundled-into-one-todo is not the same test as small/low-risk." The predecessor plan in this same lineage
  (`shared_ci_workflow_repo_extraction_2026_08_06.md`) already produced one real incident class (a visibility-flip
  mistake breaking fleet CI) that this plan's own "Confirmed technical facts" section explicitly re-verifies against
  before proceeding. Every todo completed so far (1-2) was executed via direct interactive operator sessions, not
  AO-dispatch, and the plan's own "Wave order" design deliberately requires live-CI-run verification at each step before
  fanning out — real judgment/operator-level work, not a worker-determinable outcome. Matches the established precedent
  for sibling CI/infra plans in this same corpus (`ci_pipeline_speed_and_cost_redesign_2026_08_05.md`'s own 2026-08-06
  na-eligibility-audit KEEP-NA ruling, cited in `ag_closeout_audit_infra_parked_2026_08_07.md` finding 20's
  classification of this exact doc as active, currently-executing, operator-driven work). `assigned_vm: NA` is correct,
  not a mis-default.
- **2026-08-07 (interactive session) — todo 5 shipped**: Full details in the todo's own checkbox above. Headline: found
  and corrected 2 real gaps beyond the conversion itself — a tooling bug (`make_reusable.py` dropping the file's
  top-level `env:` block) and an SSOT-drift bug (a same-day sibling fix landed on 21 repos' rendered copies but never
  reached the canonical template). All 23 fleet repos converted and independently verified. Also, tangential to this
  todo but discovered while shipping it: corrected a misdiagnosis in `fleet_promoter_glue_runner_stall_2026_08_06.md`
  and `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` (the "0 glue runners" blocker theory was wrong —
  `ldr-to-main-promote-fleet.yml` no longer depends on that pool; the real blocker was a separate, already-fixed
  scheduling livelock). Process note: this session hit the shared-checkout contention class documented in
  `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md` directly and repeatedly — several
  uncommitted doc/tool edits to files in `unified-trading-pm` were silently discarded mid-session by a concurrent
  session's `git pull --rebase --autostash`, and `quickmerge.sh` itself was observed doing a defensive "Reset to origin"
  that discarded an already-made local commit 3 times across this fan-out (each recovered via `git cherry-pick <sha>`
  from the dangling commit object — content was never actually lost, just required regenerating/recovering). Deferred: a
  few small doc corrections + the `make_stub.py` semver-agent.yml extension couldn't be durably committed to
  `unified-trading-pm` during this session's window due to that contention — the working logic survives in a scratchpad
  copy and needs reconciling back into the real tool file once the checkout settles (tracked as a todo, not silently
  dropped).
