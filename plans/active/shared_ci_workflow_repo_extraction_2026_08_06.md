---
doc_type: plan
title: Extract shared reusable CI workflows into a new dedicated public repo (unified-trading-ci)
summary: >-
  unified-trading-pm was found accidentally PRIVATE on 2026-08-06, which broke `quality-gates-v2` fleet-wide — GitHub
  hard-blocks a PUBLIC repo from calling a `uses:` reusable workflow hosted in a PRIVATE repo (no permission setting
  fixes this). PM was flipped back public as the immediate fix. This plan is the durable follow-up: extract the small,
  self-contained set of reusable workflow/action files every other repo depends on into a new dedicated public repo
  (`unified-trading-ci`), so PM can go private again in the future (accidentally or deliberately) without breaking CI
  for anyone. Covers repo creation, the exact 5-file extraction, multi-machine workspace bootstrap (every slot on
  Ikenna's and Harsh's laptops + the AO planning VM), and a canary-then-waved migration of all 25 repos' `uses:`
  references, ending with PM itself.
status: active
nature: process
asset_group: [ci, infrastructure]
stage: [meta]
repos:
  [
    unified-trading-pm,
    ml-service,
    ibkr-gateway-infra,
    unified-trading-api,
    unified-trading-system-ui,
    fund-administration-service,
    trading-agent-service,
    system-integration-tests,
    greeks-service,
    deployment-ui,
    e2e-testing,
    execution-service,
    strategy-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    alerting-service,
    market-data-processing-service,
    unified-trading-library,
    unified-api-contracts,
    deployment-api,
    features-service,
    instruments-service,
    agent-orchestrator,
    market-tick-data-service,
    deployment-service,
  ]
scope: [engineer, admin]
tags:
  [
    ci-cd,
    github-actions,
    reusable-workflows,
    repo-visibility,
    multi-machine,
    workspace-manifest,
    cursor-workspace,
    incident-followup,
  ]
related:
  [
    /plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md,
    /plans/active/pm_own_workflows_wave2_self_hosted_runner_migration_2026_07_28.md,
    /plans/active/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
    /plans/active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: infra
drift_direction: advance-code
depends_on:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md,
    unified-trading-pm/.github/workflows/python-quality-gates-v2.yml,
    unified-trading-pm/workspace-manifest.json,
    unified-trading-pm/scripts/dev/setup-tab-worktrees.sh,
  ]
source:
  [
    "operator, interactive session, 2026-08-06 — reported main_ci_red on unified-api-contracts, root-caused to PM being
    accidentally private; operator directed: flip PM public, then move PM's self-hosted workflows to GitHub-hosted
    (folded into self_hosted_runner_public_repo_revert_2026_08_05.md as todo 24), then scope out in full a new dedicated
    public repo everything depends on for CI, covering every machine (Ikenna's + Harsh's laptop slots, the AO planning
    VM), workspace-manifest.json, and the cursor workspace configs — ml-service as canary, then lower-churn repos,
    ending with PM itself.",
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Extract shared reusable CI workflows into a new dedicated public repo (unified-trading-ci)

## Why this plan exists

`unified-trading-pm` was found flipped to PRIVATE on 2026-08-05/06 (cause not yet determined — not investigated as part
of the incident response; worth a separate look at `gh api repos/IggyIkenna/unified-trading-pm` audit events if anyone
wants to know exactly when/how). Because `unified-api-contracts` (and every other repo) is PUBLIC, this broke
`quality-gates-v2` fleet-wide: **GitHub hard-blocks a public repo from resolving a `uses:` reusable workflow hosted in a
private repo — there is no repo setting, org policy, or token scope that unlocks this; it is categorically different
from the "accessible from repos in the org/enterprise" setting, which only ever extends private→private/ internal
access, never private→public.** Evidence: `unified-api-contracts` PR #860 sat with `quality-gates-v2` never reporting a
check at all (0 jobs, not a failing job) from ~13:04 UTC 2026-08-05 until PM was flipped back public 2026-08-06, at
which point a fresh `workflow_dispatch` run immediately resolved real jobs again.

Flipping PM back to public (done, 2026-08-06) is the correct IMMEDIATE fix. But it re-exposes the same failure mode to a
single accidental visibility toggle happening again — and if PM was made private for a REAL reason (a sensitivity
concern, not just a fat-fingered setting), that reason is currently unaddressable without breaking CI for all 25 repos.
The durable fix: **the only thing that genuinely needs to be public is the ~5 small reusable-workflow/ action files
other repos' `uses:` lines resolve against — not all of PM.** Moving just those into a new, minimal, purpose-built
public repo lets PM's own visibility become a non-issue for CI ever again.

## Confirmed technical facts (verified 2026-08-06, not assumed — read the actual files before trusting this section)

- **Exactly 5 files are the real cross-repo dependency surface**, confirmed via
  `grep -rhoE "uses: IggyIkenna/unified-trading-pm/\.github/(workflows|actions)/..." --include="*.yml" .` across the
  whole fleet plus a read of each file's own internal `uses:`/local-dependency lines:
  1. `.github/workflows/python-quality-gates-v2.yml` (1341 lines) — the real reusable QG gate every repo's
     `quality-gates-v2.yml` caller invokes.
  2. `.github/workflows/notify-slack.yml` — a LOCAL dependency of #1 (`uses: ./.github/workflows/notify-slack.yml`
     inside python-quality-gates-v2.yml at 2 call sites) — must move together or #1 breaks the moment it's hosted
     somewhere that doesn't also carry this file at the same relative path.
  3. `.github/workflows/image-build-validate.yml` (311 lines) — the reusable image-build gate.
  4. `.github/actions/setup-python-tools/action.yml` — composite action, referenced directly by
     `system-integration-tests`/`strategy-service`.
  5. `.github/actions/setup-agent-tools/action.yml` — composite action, same pattern. None of these 5 files reference
     any OTHER PM-local file via a `./`-relative `uses:` or an explicit `repository:`-pinned checkout — confirmed by
     direct read, not inferred. The extraction is genuinely this small.
- **A handful of `agent-audit.yml` files across the fleet pin `python-quality-gates-v2.yml@main` instead of
  `@live-defi-rollout`** (the branch every OTHER caller uses) — a pre-existing inconsistency, not something this plan
  needs to preserve. `deployment-api/.github/workflows/quality-gates-v2.yml` (the REAL gate, not just `agent-audit.yml`)
  is also `@main`-pinned — worth reconciling as part of that repo's migration todo, not a separate cleanup pass.
  **Design decision**: `unified-trading-ci` gets ONE stable branch (`main`) — no LDR/staging promotion model, since its
  only content is CI YAML with no code to promote through tiers. Every caller fleet-wide converges on `@main`, which
  incidentally fixes the branch-pin inconsistency above as a side effect rather than a separate task.
- **A handful of legacy, pre-v2 `quality-gates.yml`/`python-quality-gates.yml` references exist** (3 `features-service`
  sub-package workflow files, 1 `deployment-ui` `agent-audit.yml`) — confirmed genuinely vestigial/pre-v2, out of scope
  for this plan; do not block the migration on them.
- **`image-build-gate.yml` is hand-maintained, not template-propagated** — confirmed byte-identical across every checked
  repo (`strategy-service`, `deployment-api`, `agent-orchestrator`, `system-integration-tests` all diff clean against
  `scripts/workflow-templates/image-build-gate.yml`), but `grep -rl image-build-gate unified-trading-pm/scripts/` finds
  it referenced nowhere in `rollout-workflow-templates.sh` or any other propagation script — this exact gap is already
  flagged as "UNCONFIRMED... a third script? hand-maintained per-repo?" in
  `self_hosted_runner_public_repo_revert_2026_08_05.md`'s own "Mechanism landscape" section. This plan's per-repo
  migration todos edit this file by hand (one `uses:` line) for the same reason that plan's authors couldn't find an
  automated path either; todo 3 below is an optional (not blocking) follow-up to close the gap for good.
- **`python-quality-gates-v2.yml` also `git clone`s `unified-trading-pm` itself for QG base scripts
  (`scripts/quality-gates-base/`, `scripts/quality_gates/`) — this clone is ALREADY PAT-authenticated (`clone_repo()`'s
  `git clone https://x-access-token:${GH_PAT}@github.com/...`, `GH_PAT` sourced from `secrets.GH_PAT`), not
  anonymous/public-only access.** This means PM going private again in the future will NOT break this clone step (a
  PAT-authenticated clone works regardless of the target's visibility, as long as the PAT has read access — which it
  must already, since this exact mechanism already clones OTHER private repos like `strategy-service`/`ml-service` as
  `DEP_REPOS` today). **Only the GitHub-native `uses:` reusable-workflow resolution is visibility-gated — everything
  else in this pipeline already tolerates PM being private.** This is why extracting just the 5 files above is
  sufficient; nothing else needs to move.
- **PM's own `quality-gates-v2.yml` currently calls the reusable workflow LOCALLY**
  (`uses: ./.github/workflows/python-quality-gates-v2.yml`) specifically because, per that file's own header comment,
  "PM cannot reference itself via a remote ref without a chicken-and-egg problem." Once the reusable workflow lives in
  `unified-trading-ci`, PM loses its special case and switches to the SAME remote-ref pattern as every other repo
  (`uses: IggyIkenna/unified-trading-ci/.github/workflows/python-quality-gates-v2.yml@main`) — a real simplification,
  not just parity.
- **Migration order is grounded in measured 7-day commit counts** (`git log --since="7 days ago" --oneline` per repo,
  run 2026-08-06), lowest-churn first, to keep early waves low-blast-radius: see the Todos section for the exact ordered
  list. `ml-service` is the explicit canary per operator instruction even though it isn't the lowest-churn repo (94
  commits/7d) — respected as-is, not overridden by the churn data.

## Design decisions (stated so a later reader can course-correct, not treated as pre-litigated)

1. **Repo name: `unified-trading-ci`** (operator-selected 2026-08-06 over `unified-ci-shared`).
2. **`unified-trading-ci` becomes the sole source of truth for the 5 extracted files.** PM's own copies are deleted once
   every caller (including PM) has migrated (Phase 5) — no dual-maintenance, no sync script between two "real" copies.
3. **Single `main` branch, no promotion tiers.** Simpler than PM's LDR/staging model; nothing here needs it.
4. **`unified-trading-ci` needs minimal CI of its own** (e.g., a YAML-lint / actionlint check on push) — NOT the full
   `python-quality-gates-v2.yml` pipeline (that would be circular — the repo hosting the gate doesn't need to run the
   gate on itself as a Python project, it isn't one). Scope this small in Phase 1; don't over-build it.
5. **Branch protection**: require at minimum that pushes to `main` go through quickmerge or a reviewed PR (mirrors fleet
   convention) — a broken `main` here breaks CI fleet-wide instantly, so treat it with the same care as any Tier-0
   shared dependency, not a throwaway scripts repo.

## Todos

### Phase 1 — Create + seed `unified-trading-ci`

- [ ] 1. [INFRA] P0. **Create the `unified-trading-ci` GitHub repo**
      (`gh repo create IggyIkenna/unified-trading-ci     --public --description "Shared reusable GitHub Actions workflows for the unified-trading-system fleet"`),
      default branch `main`, minimal branch protection per design decision 5. Evidence: repo URL + a confirmed
      `visibility: PUBLIC` via `gh repo view`.
- [ ] 2. [INFRA] P0. **Seed it with the exact 5 files** (verbatim from PM's `live-defi-rollout` HEAD, preserving
      relative paths): `.github/workflows/python-quality-gates-v2.yml`, `.github/workflows/notify-slack.yml`,
      `.github/workflows/image-build-validate.yml`, `.github/actions/setup-python-tools/action.yml`,
      `.github/actions/setup-agent-tools/action.yml`. Add a short `README.md` stating the repo's purpose and the "why
      this is separate from PM" rationale (link back to this plan + the incident) so a future reader doesn't wonder why
      CI plumbing lives outside PM. Add minimal own-CI (design decision 4). Evidence: commit SHA, and a byte-diff
      against PM's source files showing zero unintended drift at extraction time.
- [ ] 3. [INFRA] P3. _(stretch, optional)_ **Add `image-build-gate.yml` to `rollout-workflow-templates.sh`'s managed
      file set**, closing the pre-existing "hand-maintained, no propagation script" gap noted above — not required for
      this migration to succeed (the per-repo todos below hand-edit it same as always), but a natural opportunistic fix
      since every repo's copy is being touched anyway.

### Phase 2 — Multi-machine + workspace-tooling bootstrap

- [ ] 4. [INFRA] P0. **Add `unified-trading-ci` to `unified-trading-pm/workspace-manifest.json`** — a new entry under
      `repositories` (github_url, `type`, `status: active`, `dependencies: []`), plus slot it into
      `topologicalOrder.levels[]` (it has zero dependencies, so an early/independent level) and `publishingOrder`. This
      is the single source of truth `setup-tab-worktrees.sh` and `rollout-workflow-templates.sh` both derive their repo
      list from — every downstream step in this phase depends on this landing first. Evidence: manifest diff +
      `python3 -c "import json; json.load(open('workspace-manifest.json'))"` (valid JSON) + `setup-tab-worktrees.sh`'s
      `active_repos()` output includes it.
- [ ] 5. [INFRA] P1. **Add `unified-trading-ci` to the Cursor workspace configs** —
      `cursor-configs/unified-trading-system-repos.code-workspace` (the canonical all-repos view, `../../<repo>` path
      style) and `cursor-configs/workspace-complete.code-workspace` (bare `<repo>` style), plus
      `cursor-configs/workspace-infrastructure.code-workspace` (topic-scoped, CI tooling fits here). One
      `{"path": "unified-trading-ci"}` entry per file's `folders` array. Evidence: each file still parses as valid JSON
      post-edit + the new folder entry is present.
- [ ] 6. [INFRA] P2. **Sanity-check the workspace-root symlink claim before relying on it.** `setup-tab-worktrees.sh`
      documents `${WORKSPACE_ROOT}/unified-trading-system-repos.code-workspace` as "a symlink →
      `unified-trading-pm/cursor-configs/...`", but on this slot (tabs/3) it is currently a REGULAR FILE
      (`-rw-r--r--@`), not a symlink — confirmed via `ls -la`. Check every slot this plan touches: if the live file has
      actually diverged from the `cursor-configs/` copy, editing only `cursor-configs/` (todo 5) won't propagate there
      without either re-symlinking or a manual copy. Evidence: `ls -la` output per slot + either "confirmed symlink,
      todo 5 propagates automatically" or "regular file, re-synced explicitly" per slot touched.
- [ ] 7. [OPERATOR] P0. **Per-machine clone runbook — genuinely manual, no single AO/interactive worker can do this for
      another machine.** Once todo 4 lands (manifest updated), each machine owner runs, once per slot/worktree they own:
      `bash     cd <workspace-root-for-that-slot>     git clone git@github.com:IggyIkenna/unified-trading-ci.git     # OR, to pick up the manifest-driven provisioning path instead of a bare clone:     bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh   # re-run; existing slots don't auto-discover new manifest entries     `
      Concretely, this needs running on: **(a) every existing `.tabs/N` slot on Ikenna's laptop** (this session's own
      `.tabs/3` included — do it here too once todo 4 lands); **(b) every slot on Harsh's laptop** (operator to relay to
      Harsh — a different physical machine, cannot be actioned from this session); **(c) the AO planning VM**
      (`i-0dd9812a96cdda5dc` human-planning VM AND the central orchestrator VM `i-0c9b283b31d6b5ca7` / EIP
      `13.113.200.22` — both run per-slot worktrees off the same manifest per
      `/codex/05-infrastructure/per-tab-worktrees.md`; needs SSM access to run the clone/re-provision command remotely,
      or a slot's own cron `slot-cron-ff-pull.sh` cycle if that script is confirmed to pick up NEW manifest entries
      rather than only fast-forwarding existing ones — verify which before assuming it's automatic). Tagged `[OPERATOR]`
      because it's cross-machine coordination work no single dispatched worker can complete alone, not because of any
      risk/judgment call. Evidence: `git -C unified-trading-ci status` (or equivalent) succeeding on each machine/slot,
      listed explicitly per machine as it's done.

### Phase 3 — Canary: `ml-service`

- [ ] 8. [INFRA] P0. **Re-point `ml-service`'s `quality-gates-v2.yml` and `image-build-gate.yml`** `uses:` lines from
      `IggyIkenna/unified-trading-pm/...` to `IggyIkenna/unified-trading-ci/...@main`. Keep PM's own copies of the 5
      files live and untouched during this phase (don't delete anything in PM yet) — this is purely additive until
      Phase 5.
- [ ] 9. [INFRA] P0. **Make a small, low-risk real change in `ml-service`** (a trivial comment/whitespace edit is
      enough) and push it, to trigger a genuine `quality-gates-v2` run end-to-end against the new reference. Confirm:
      (a) the reusable workflow resolves (no "workflow not found"), (b) `secrets: inherit` still delivers
      `GCP_SA_KEY`/`GH_PAT`/`SLACK_CI_WEBHOOK_URL` correctly through the new 2-hop `uses:` chain (verify the
      `clone_repo unified-trading-pm` step inside the run actually succeeds, not just that the job started), (c) the run
      goes fully green. Evidence: the run's URL/id + explicit confirmation all 3 checks above passed, not just "the job
      started."
- [ ] 10. [INFRA] P1. **Confirm `image-build-gate.yml`'s re-point also works** with a real triggered run (its trigger
      may differ from quality-gates-v2's — check what actually fires it before assuming push/PR is enough). Evidence:
      run URL/id.

### Phase 4 — Fan out in measured-churn-ordered waves (lowest-churn first)

Order derived from `git log --since="7 days ago" --oneline` per repo, 2026-08-06 (excludes `ml-service`, already
migrated as canary, and `unified-trading-pm`, migrated last in Phase 5). Each wave: re-point both `uses:` lines per repo
(`quality-gates-v2.yml` + `image-build-gate.yml`), ship, confirm one real green run per repo before starting the next
wave — same discipline as `self_hosted_runner_public_repo_revert_2026_08_05.md`'s one-repo-at-a-time playbook, batched
here only for todo-count sanity, not for skipping per-repo verification.

- [ ] 11. [INFRA] P1. **Wave 1 (6 lowest-churn)**: `ibkr-gateway-infra` (25 commits/7d), `unified-trading-api` (40),
      `unified-trading-system-ui` (55), `fund-administration-service` (58), `trading-agent-service` (59),
      `system-integration-tests` (66). Evidence: one real green `quality-gates-v2` run URL per repo.
- [ ] 12. [INFRA] P1. **Wave 2**: `greeks-service` (69), `deployment-ui` (76), `e2e-testing` (85), `execution-service`
      (96), `strategy-service` (99), `batch-live-reconciliation-service` (106). Evidence: same.
- [ ] 13. [INFRA] P1. **Wave 3**: `client-reporting-api` (108), `alerting-service` (110),
      `market-data-processing-service` (162), `unified-trading-library` (178), `unified-api-contracts` (216),
      `deployment-api` (230 — also reconcile its stray `@main` pin to `@main` on the NEW repo, which is now correct by
      construction rather than a separate fix). Evidence: same.
- [ ] 14. [INFRA] P1. **Wave 4 (final 5)**: `features-service` (232), `instruments-service` (249), `agent-orchestrator`
      (312), `market-tick-data-service` (340), `deployment-service` (393). Evidence: same.
- [ ] 15. [INFRA] P2. **Fleet-wide re-point sweep for the stray `@main`-pinned `agent-audit.yml` copies** found during
      research (`client-reporting-api`, `market-data-processing-service`, `deployment-service`,
      `unified-trading-library`, `system-integration-tests`, `unified-api-contracts`, `ibkr-gateway-infra`,
      `instruments-service`, `features-service`, `market-tick-data-service`, `execution-service`,
      `batch-live-reconciliation-service`, `trading-agent-service`, `alerting-service`, plus PM's own copy) — these are
      lower-stakes (`workflow_dispatch`-only per earlier fleet audit) but should still converge on
      `unified-trading-ci@main` for consistency, not left pointing at a dead/stale PM ref. Evidence: fleet-wide grep
      showing zero remaining `uses: IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates-v2` hits
      anywhere outside PM's own not-yet-migrated copy (until Phase 5 lands).

### Phase 5 — Migrate PM itself last (it currently hosts the source of truth)

- [ ] 16. [INFRA] P1. **Re-point PM's own `quality-gates-v2.yml`** from the local
      `uses: ./.github/workflows/     python-quality-gates-v2.yml` self-call to the same remote-ref pattern every other
      repo now uses (`uses:     IggyIkenna/unified-trading-ci/.github/workflows/python-quality-gates-v2.yml@main`) —
      removes the chicken-and-egg special case documented in that file's own header. Verify PM has no OTHER
      internal-only consumer of its local `notify-slack.yml` copy before deleting it in the next todo (grep PM's own
      `.github/workflows/*.yml` for `uses: ./.github/workflows/notify-slack.yml` beyond the one being removed).
      Evidence: real green PM `quality-gates-v2` run URL.
- [ ] 17. [INFRA] P1. **Delete PM's own now-redundant copies** of the 5 extracted files (`python-quality-gates-v2.yml`,
      `notify-slack.yml` — only if todo 16's grep confirmed no other internal consumer — `image-build-validate.yml`,
      `.github/actions/setup-python-tools/`, `.github/actions/setup-agent-tools/`) once `unified-trading-ci` is
      confirmed the sole live source for all 25 repos (Phase 4 fully green). Evidence: PM's `git status` clean post
      -delete + a subsequent PM `quality-gates-v2` run still green (proves nothing silently depended on the deleted
      local copies).
- [ ] 18. [INFRA] P2. **Update the template sources** (`scripts/workflow-templates/quality-gates-v2.yml.tmpl` line ~64,
      `scripts/workflow-templates/image-build-gate.yml`) so any FUTURE repo's `rollout-workflow-templates.sh` render is
      correct out of the box, not just the 25 repos hand-migrated above. Evidence: a fresh render for one
      already-migrated repo (dry-run / diff against its current committed file) shows zero unintended change.

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — gate set / quickmerge / reusable-workflow rollout mechanism this plan operates
  within; needs a note added once this plan ships pointing future readers at `unified-trading-ci` as the actual host of
  the reusable QG/image-build gates (currently documents PM as the host).
- `/codex/05-infrastructure/per-tab-worktrees.md` — per-slot worktree model; needs its repo list / manifest reference
  implicitly covers the new repo once workspace-manifest.json (todo 4) lands, no separate edit expected.

## Progress Log

- **2026-08-06 (interactive session, main_ci_red incident)**: Plan authored immediately after the immediate incident fix
  (PM flipped back public, verified via a fresh `workflow_dispatch` run on `unified-api-contracts` resolving real jobs).
  Operator confirmed: LOCAL/human track, repo name `unified-trading-ci`, and directed marking
  `pm_own_workflows_wave2_self_hosted_runner_migration_2026_07_28.md` superseded (done, same session). Full
  dependency-chain verification (the 5-file extraction scope, the PAT-authenticated PM clone already being
  visibility-agnostic, the branch-pin inconsistency, the `image-build-gate.yml` propagation gap, and the measured-churn
  migration order) done via direct file reads before writing a single todo — see "Confirmed technical facts" above for
  the evidence trail. No phase executed yet beyond authoring; Phase 1 is the next step.
- **context-scout 2026-08-06**: first scout pass (prior 15-entry list was author-seeded at plan creation, never had a
  dated marker) — trimmed to 6 entries (2 codex SSOTs already named in the doc's own "Codex SSOTs" section, the
  incident-predecessor plan, the single largest reusable-workflow artifact, and Phase 2's two edit targets). The 9 cut
  entries (4 more extraction-scope workflow/action files, 2 templates, 3 cursor-configs JSONs) are each already fully
  named with path + role directly in this doc's own prose — kept reachable via body text, not context_scope, per MVI.
