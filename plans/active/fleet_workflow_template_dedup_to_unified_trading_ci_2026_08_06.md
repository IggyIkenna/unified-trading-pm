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
asset_group: [ci, infrastructure]
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
    /plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
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
    /plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md,
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
      `unified-trading-pm@<pending, shipping alongside this flip>`.
- [ ] 3. [INFRA] P0. **Convert ONE file end-to-end as the pattern-proof, including a live (non-local) CI run** — pick
      the smallest, lowest-blast-radius flat-copy candidate (`version-registry-notify.yml`, 48 lines, likely the
      simplest) as the canary: host it in `unified-trading-ci/.github/workflows/`, replace its copy in ONE low-churn
      fleet repo with a thin caller stub, ship, and confirm via `gh run list`/`gh run view` that the ACTUAL GitHub
      Actions run (not just local `quality-gates.sh`) resolves the cross-repo `uses:` and produces the same behavior as
      the old flat copy. Done-when: a real GH Actions run ID cited, `conclusion: success` (or behavior-equivalent to the
      pre-migration copy if the workflow doesn't run on every push).
- [ ] 4. [INFRA] P1. **Convert the remaining 6 straightforward flat-copy files** (`main-backmerge-to-ldr.yml`,
      `major-bump-issue-handler.yml`, `request-major-bump.yml`, `staging-backmerge-to-ldr.yml`,
      `staging-lock-check.yml`, `update-dependency-version.yml`) using the pattern proven in todo 3 — host each in
      `unified-trading-ci`, verify the `notify-slack.yml` local-reference edge for the 2 that need it (todo 1's
      finding), then fan the caller-stub replacement out fleet-wide per repo (respecting dependency-root-first ordering
      the same way `shared_ci_workflow_repo_extraction_2026_08_06.md`'s Wave 2-4 did — `unified-api-contracts`
      /`unified-trading-library` before their dependents). Done-when: every repo that carried a full copy (per todo 1's
      table) now carries only the thin stub, each shipped + evidenced with `<repo>@<sha>`.
- [ ] 5. [INFRA] P1. **Convert `semver-agent.yml.tmpl`** (1034 lines — the largest and only one with real per-repo
      substitution beyond `{{RUNS_ON}}`'s already-proven pattern) — separated from todo 4 given its size and the fact
      it's the one file genuinely worth an isolated careful review rather than batching with the trivial ones; convert
      its `{{RUNS_ON}}` substitution to a `with: self_hosted_runner_labels:` input exactly matching
      `quality-gates-v2.yml`'s already-shipped shape, verify its `notify-slack.yml` local-reference edge resolves the
      same way as todo 4's `main-backmerge-to-ldr.yml` case, then fan out fleet-wide. Done-when: every repo carrying
      `semver-agent.yml` now carries only the thin stub, evidenced with `<repo>@<sha>` + a real GH Actions run
      confirming semver-agent behavior is unchanged post-migration (a real version-bump PR label check, not just a no-op
      smoke run).
- [ ] 6. [INFRA] P2. **Delete now-dead `notify-slack.yml` copies per todo 1's audit** — for every non-PM repo where todo
      1 determined the ONLY local callers were files now migrated to `unified-trading-ci` (todos 4-5), delete that
      repo's local `notify-slack.yml` copy; leave PM's untouched (44 internal-only consumers, confirmed unrelated).
      Done-when: zero repos outside PM carry a `notify-slack.yml` copy with zero remaining local callers of it.
- [ ] 7. [INFRA] P2. **Delete the 9 now-redundant template sources from
      `unified-trading-pm/scripts/workflow-templates/`** and remove their entries from `rollout-workflow-templates.sh`'s
      target list (header comment + the main rollout loop) — mirrors exactly how
      `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 17 deleted PM's own now-redundant
      `python-quality-gates-v2.yml`/`image-build-validate.yml` local copies once `unified-trading-ci` became the sole
      live source. **Gated on todos 3-6 being fully shipped and CI-verified fleet-wide** — do not delete the templates
      while any repo still depends on `rollout-workflow-templates.sh` regenerating a flat copy from them. Done-when:
      `scripts/workflow-templates/` contains none of the 9 converted files; `rollout-workflow-templates.sh` no longer
      references them; a fresh `--dry-run` shows no attempt to roll out a deleted template.
- [ ] 8. [INFRA] P2. **Fleet-wide dangling-reference re-sweep, same technique as
      `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 23** — after todos 3-7 land, run
      `grep -rln "uses:.*unified-trading-pm/.github/" --include="*.yml"` across the whole fleet one more time (excluding
      stale/worktree noise) to catch any OTHER caller class this plan's own todos might have missed (the precedent for
      this exact miss is todo 23 itself — the original extraction's `uses:` sweep only checked 2 caller files per repo
      and missed `agent-audit.yml` + composite-action consumers). Done-when: zero unexpected
      `unified-trading-pm/.github/` hits remain for any of the 9 converted files.
- [ ] 9. [DOC] P2. **Update `/codex/08-workflows/ci-cd-flow.md`** — extend the existing "Host moved to
      `unified-trading-ci` (2026-08-06)" note (added by the prior plan) to state that the SAME hosting model now covers
      this second class of workflow (list the 9 file names), and that `rollout-workflow-templates.sh`'s role is now
      limited to whatever remains genuinely templated (the UI-only tier + any future thin-caller-stub propagation), not
      full-content duplication. Done-when: the doc accurately describes the POST-this-plan state, not a mid-migration
      one.
- [ ] 10. [INFRA] P3. _(stretch, optional)_ **Add a branch-protection / visibility-change alert on
      `unified-trading-ci`** — given this plan makes it fleet-critical (11 reusable workflows/actions hosted there once
      this plan + the prior one both ship), consider whether the same accidental-private-flip class of incident that
      started `shared_ci_workflow_repo_extraction_2026_08_06.md` warrants a standing guard (a scheduled check via
      `gh api repos/IggyIkenna/unified-trading-ci` asserting `visibility == public`, alerting if not) rather than
      relying on someone noticing fleet-wide CI going red again. Genuinely optional — the risk already exists
      identically for `unified-trading-pm` today and has no such guard either; scope this as its own small follow-up if
      pursued, don't block this plan on it.

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

- `/codex/08-workflows/ci-cd-flow.md` — gate set / quickmerge / reusable-workflow rollout mechanism; needs todo 9's
  update once this plan ships.
- `/plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md` — the prior plan this one directly follows; its
  "Confirmed technical facts" + Progress Log document the base state (the 2-file extraction, the revert incident, the
  dangling-reference sweep) this plan's own facts build on.

## Progress Log

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
