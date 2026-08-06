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

- [x] 1. ✅ [INFRA] P0. **Created `unified-trading-ci`** — public, default branch `main`, branch protection set
      (`allow_force_pushes: false`, `allow_deletions: false`) via `gh api .../branches/main/protection`. Evidence:
      https://github.com/IggyIkenna/unified-trading-ci, `gh repo view` confirmed `visibility: PUBLIC`.
- [x] 2. ✅ [INFRA] P0. **Seeded with the exact 5 files**, verified byte-identical via `diff` against PM's
      `live-defi-rollout` copies before commit (all 5 diffs empty). Added `README.md` (purpose + incident link) and
      minimal own-CI (`.github/workflows/lint.yml`, actionlint on push/PR — design decision 4, not the full QG
      pipeline). Evidence: `unified-trading-ci@f20c59f` (root commit, pushed to `main`).
- [ ] 3. [INFRA] P3. _(stretch, optional)_ **Add `image-build-gate.yml` to `rollout-workflow-templates.sh`'s managed
      file set**, closing the pre-existing "hand-maintained, no propagation script" gap noted above — not required for
      this migration to succeed (the per-repo todos below hand-edit it same as always), but a natural opportunistic fix
      since every repo's copy is being touched anyway.

### Phase 2 — Multi-machine + workspace-tooling bootstrap

- [x] 4. ✅ [INFRA] P0. **Added `unified-trading-ci` to `workspace-manifest.json`** — new `repositories` entry
      (`type: infrastructure`, `dependencies: []`, `ci_status: null` — bot-written-only field, left null per the
      single-writer guard, not asserted by hand), added to `topologicalOrder.levels[0]` alongside `unified-trading-pm`.
      **Correctness note for whoever edits this file next**: `topologicalOrder.levels[].description` gets embedded
      directly into an SVG `<!-- comment -->` by `generate_workspace_dag.py` — an XML comment cannot contain a literal
      `--` anywhere in its content (hit this directly: my first draft used `--` as a separator and broke
      `test_generate_workspace_dag_produces_valid_svg` with `ParseError: not well-formed`; fixed by using an em dash `—`
      instead, matching every other entry's existing convention). Evidence: `unified-trading-pm@087935952c`,
      `validate_workspace_manifest.py` + `check_workspace_manifest_canonical.py` both green.
- [x] 5. ✅ [INFRA] P1. **Added `unified-trading-ci` to the 3 Cursor workspace configs** (`../../` style for
      `unified-trading-system-repos.code-workspace`, bare-path style for `workspace-complete.code-workspace` and
      `workspace-infrastructure.code-workspace`). Evidence: same commit as todo 4;
      `check_workspace_code_workspace_drift.py --workspace-root .` passed (26 active+scaffolded repos, no drift).
- [x] 6. ✅ [INFRA] P2. **Checked — the workspace-root file is NOT a broken symlink, it's a genuinely different
      rendering** (bare `<repo>` paths, since it lives AT the workspace root rather than 2 levels down in
      `cursor-configs/`) — the drift guard's own canonical SSOT is explicitly the `cursor-configs/` copy, which already
      passed. Fixed the practical gap directly on this slot (`.tabs/3`): added the missing `unified-trading-ci` entry to
      the root `unified-trading-system-repos.code-workspace` in its own bare-path style. This file isn't tracked by any
      git repo (`.tabs/3/` itself has no `.git` — confirmed) — it's a per-slot local artifact, so this fix only applies
      to THIS slot; every other slot/machine needs the same one-line addition (folded into todo 7's runbook, since both
      are per-machine local-file work).
- [ ] 7. [OPERATOR] P0. **Per-machine clone runbook — genuinely manual, no single AO/interactive worker can do this for
      another machine.** **This slot (`.tabs/3` on Ikenna's laptop) is DONE**: `unified-trading-ci` cloned at
      `.tabs/3/unified-trading-ci`, root `.code-workspace` updated (todo 6). Still needed, once todo 4's manifest change
      is pulled by each machine: **(a) every OTHER `.tabs/N` slot on Ikenna's laptop**; **(b) every slot on Harsh's
      laptop** (operator to relay — different physical machine, cannot be actioned from this session); **(c) the AO
      planning VM** (`i-0dd9812a96cdda5dc` human-planning VM AND the central orchestrator VM `i-0c9b283b31d6b5ca7` / EIP
      `13.113.200.22` — both run per-slot worktrees off the same manifest per
      `/codex/05-infrastructure/per-tab-worktrees.md`; needs SSM access to run the clone/re-provision command remotely,
      or confirm `slot-cron-ff-pull.sh` picks up NEW manifest entries rather than only fast-forwarding existing ones
      before assuming it's automatic). Each: `git clone git@github.com:IggyIkenna/unified-trading-ci.git` + add the
      entry to that slot's root `.code-workspace` per todo 6's finding. Tagged `[OPERATOR]` because it's cross-machine
      coordination no single dispatched worker can complete alone. Evidence: `git -C unified-trading-ci     status`
      succeeding on each machine/slot, listed explicitly per machine as it's done.

### Phase 3 — Canary: `ml-service`

- [x] 8. ✅ [INFRA] P0. **Re-pointed `ml-service`'s `quality-gates-v2.yml` and `image-build-gate.yml`** `uses:` lines to
      `IggyIkenna/unified-trading-ci/...@main`. PM's own copies left untouched (purely additive, per design decision 2 —
      deletion is Phase 5 only). Evidence: `ml-service@8a514bf`.
- [x] 9. ✅ [INFRA] P0. **Real run triggered automatically by todo 8's push** (no separate throwaway commit needed — the
      `uses:` re-point commit itself fired a genuine `push` event). All 3 checks confirmed: (a) reusable workflow
      resolved cleanly — `content sentinel` job succeeded first, no "workflow not found"; (b) `secrets: inherit` through
      the new 2-hop `uses:` chain confirmed — the `Clone unified-trading-pm and dependencies` step (PAT- authenticated
      `clone_repo()`) shows `completed success` in the job's own step list; (c) full run green — `content sentinel` +
      `QG slice (tests)` + `QG slice (checks)` + aggregate `quality-gates-v2` job all `completed success`. Evidence:
      `ml-service` run 31072413095 (https://github.com/IggyIkenna/ml-service/actions/runs/31072413095), head SHA
      `8a514bf`.
- [x] 10. ✅ [INFRA] P1. **`image-build-gate.yml`'s trigger checked — it's `pull_request: branches: [main]` only** (not
      push/dispatch), so it won't fire again until ml-service's next real LDR→main promotion PR — did not manufacture a
      throwaway PR just to force it. The underlying mechanism (a `uses:` reusable-workflow reference resolving against
      `unified-trading-ci`) is identical in kind to what todo 9 already proved end-to-end for `quality-gates-v2.yml` —
      the two files differ only in which workflow calls the same resolution mechanism, not in the mechanism itself. Will
      get a natural real-world confirmation on ml-service's next promotion PR; not blocking further migration waves.

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
- **2026-08-06 (interactive session, execution)**: Phases 1-3 shipped. Todos 1-2 (`unified-trading-ci@f20c59f`), 4-6
  (`unified-trading-pm@087935952c`), 8-10 (`ml-service@8a514bf`, run 31072413095 fully green) all done — see each todo's
  own evidence line. Two real bugs caught and fixed along the way, not silently worked around: (1) the manifest's new
  level-0 `description` used a literal `--` separator, which broke SVG generation because
  `topologicalOrder.levels[].description` gets embedded into an XML comment (XML comments can't contain `--`) — fixed by
  using an em dash like every other entry; (2) `ci_status` was initially hand-set to `"MAIN_GREEN"` on the new entry,
  tripping the bot-only single-writer guard — corrected to `null`. Also hit and resolved a real (not cosmetic) merge
  conflict on `codex_doc_freshness_baseline.yaml` from a concurrent slot's own baseline-write, and had to learn
  `detect_template_drift.py --baseline-write-allow-additions` requires `--baseline-write` alongside it (not standalone)
  to actually persist. Todo 3 (optional stretch) and todo 7 (per-machine runbook — this slot done, every other machine
  still pending, genuinely cannot be actioned from this session) remain open. Phase 4 (23-repo fan-out) not yet started.
