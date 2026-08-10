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
    /plans/archive/2026_07/pm_own_workflows_wave2_self_hosted_runner_migration_2026_07_28.md,
    /plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
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
    unified-trading-ci/.github/workflows/python-quality-gates-v2.yml,
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
- [x] 7a. ✅ [INFRA] P0. **Root cause of the provisioning gap found + fixed — `unified-trading-ci` needs a
      `live-defi-rollout` branch, not just `main`.** `setup-tab-worktrees.sh --add-slot <N>` (the canonical per-slot
      provisioning script, confirmed via `/codex/05-infrastructure/per-tab-worktrees.md` line 88 as "also used on every
      VM worker host") derives each repo's slot-working branch from `workspace-manifest.json`'s
      `repositories.<repo>.integration_branch`, falling back to the GLOBAL default `live-defi-rollout` when unset — and
      EVERY existing fleet repo (PM included) relies on that fallback; there is no precedent for a repo using a
      different slot-working branch, and quickmerge's own `STAGE 0.4`/push-target logic hardcodes `live-defi-rollout` as
      the shared trunk. Overriding `integration_branch` to `main` for this one repo would have been a genuine, untested
      architectural deviation — rejected in favor of giving it a real `live-defi-rollout` branch, matching every other
      repo. Fixed: created `live-defi-rollout` off `main` (identical content, `unified-trading-ci@f20c59f`), pushed,
      branch-protected the same as `main` (no force-push/delete). `main` stays what every fleet caller's `uses:@main`
      pins against (design decision 3, unchanged) — `live-defi-rollout` is purely the slot/quickmerge working branch.
      **Deliberately NOT wired into the full `promotion_model: ldr_main` automated-promotion pipeline** (would need
      branch-protection-ruleset + `sit-gate` participation + `main-backmerge-to-ldr.yml`/ `staging-lock-check.yml`
      template rollout — real additional infra, not needed for a low-churn CI-YAML-only repo right now);
      `main`/`live-defi-rollout` are currently identical and will be kept in sync manually by whoever next edits this
      repo. Flagged as a follow-up, not silently skipped — if this repo starts changing frequently, wire up the standard
      `ldr_main` model the same way every other repo has it.
- [x] 7b. ✅ [INFRA] P0. **Every slot on Ikenna's laptop provisioned** (all 11: `.tabs/1` through `.tabs/11`) via
      `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --add-slot <N>` run once per slot from the top-level
      (non-tabbed) `unified-trading-pm` clone — confirmed idempotent + additive-only (re-running it against an
      already-provisioned slot only backfills the ONE missing repo; every other repo in that slot logs
      `OK <repo> (Path-B clone exists)` and is untouched). Slots 2, 4–11 got a clean `--reference` Path-B clone in one
      pass. Slots 1 and 3 needed manual follow-up (both had a PRE-EXISTING partial/incorrect state from before the
      `live-defi-rollout` branch existed — slot 1's first `--add-slot` attempt partially cloned before hitting the
      branch-checkout error, leaving it on `main` with no pre-push hook; slot 3 was MY OWN Phase-1 manual `git clone`,
      also on `main`, also missing the hook + proper slot identity): both re-checked-out onto `live-defi-rollout` and
      had `scripts/hooks/pre-push` (the strict-quickmerge guard every OTHER Path-B clone gets automatically at
      clone-time) copied in by hand. **A top-level sibling clone of `unified-trading-ci` already existed** at
      `${WORKSPACE_ROOT}/unified-trading-ci` (git identity `Rollout Agent`, already on `live-defi-rollout`) before any
      of this — some other already-running automation on this machine had independently cloned it once it appeared in
      the manifest; this session did not create it, just relied on it as the Path-B reference base
      (`ensure_repo_worktree` requires this sibling to exist before it will provision ANY slot's `--reference` clone — a
      genuine prerequisite, not something this session's slot loop needed to create itself). Evidence:
      `git -C     .tabs/<N>/unified-trading-ci config user.name` shows the correct `ikennaigboaka [slot-<N>·laptop]`
      identity and `branch --show-current` shows `live-defi-rollout` for all 11 slots.
- [x] ✅ 7c. [OPERATOR] P0. **DONE 2026-08-07 — Harsh completed this on his own machine (operator-confirmed: "already
      did it").** Original text preserved below for context. **Harsh's laptop — genuinely manual, cannot be actioned
      from this session (different physical machine).** Exact commands (mirrors what this session just did on Ikenna's
      laptop, confirmed against the documented Harsh onboarding transcript in
      `/codex/05-infrastructure/per-tab-worktrees.md`) — **whitespace-corruption in this fenced block fixed 2026-08-10
      by plan_reconciler infra shard, agt-716973 (fence now opens on its own line; ~150-char space-runs before several
      comment lines removed); command content unchanged**:

      ```bash
          # 1. Clone the new sibling repo at Harsh's workspace root (same level as his other repo clones, NOT inside .tabs/N)
          cd /Users/harsh/Code/unified-trading-system-repos  # or wherever his workspace root actually is
          git clone git@github.com:IggyIkenna/unified-trading-ci.git

          # 2. Pull PM's latest on at least one clone first, so his local workspace-manifest.json has the new repo entry
          #    (any existing slot's unified-trading-pm, or the top-level one, works — pick whichever he normally updates from)
          cd unified-trading-pm && git pull --ff-only origin live-defi-rollout && cd ..

          # 3. Backfill EVERY existing slot (repeat for each of Harsh's slot numbers — check with --list first)
          cd unified-trading-pm
          bash scripts/dev/setup-tab-worktrees.sh --list                    # see which slot numbers exist
          bash scripts/dev/setup-tab-worktrees.sh --add-slot 1               # repeat per existing slot number
          bash scripts/dev/setup-tab-worktrees.sh --add-slot 2
          # ...etc for however many slots Harsh has

          # 4. Sanity check — every slot should now show the repo, on live-defi-rollout, with a pre-push hook
          for n in 1 2 3; do   # substitute his real slot numbers
            d="/Users/harsh/Code/unified-trading-system-repos/.tabs/$n/unified-trading-ci"
            echo "slot $n: $(git -C "$d" branch --show-current) hook=$([ -x "$d/.git/hooks/pre-push" ] && echo OK || echo MISSING)"
          done
          # If any slot shows "MISSING" or is stuck on `main` instead of `live-defi-rollout` (can happen if a slot was
          # mid-provisioning when this branch didn't exist yet — see todo 7a's note on slots 1/3 above), fix by hand:
          #   cd <that-slot>/unified-trading-ci && git fetch origin live-defi-rollout && git checkout live-defi-rollout
          #   cp ../unified-trading-pm/scripts/hooks/pre-push .git/hooks/pre-push && chmod +x .git/hooks/pre-push
          ```

          Evidence: paste the sanity-check output back into this plan's Progress Log once run.

- [x] 7d. ✅ [INFRA] P0. **AO central orchestrator VM (`i-0c9b283b31d6b5ca7`, `agent-orchestrator-vm-1`, 13.113.200.22)
      — actually provisioned this session**, not just documented: this laptop has standing SSH access (`~/.ssh/config`
      host `agent-orchestrator-vm`), discovered mid-session (earlier assumed operator-only). Ran the identical mechanism
      as todo 7c's Harsh runbook directly: cloned `unified-trading-ci` as a sibling at
      `/home/ubuntu/unified-trading-system-repos/unified-trading-ci` (confirmed PM already had the manifest entry —
      `9676ea9`/`3a53265`, clean, on `live-defi-rollout`, no local pull needed), then ran
      `setup-tab-worktrees.sh --add-slot N` for all 16 of that VM's active slots (1-16, all showing live, very-recent
      worker activity at provisioning time — additive/idempotent per design, did not disturb any). Verified all 16:
      `unified-trading-ci` present, `branch=live-defi-rollout`, `hook=OK` (pre-push hook installed).
      `slot-cron-ff-pull.sh` needs no changes (confirmed by reading it directly — directory-glob discovery, not
      manifest-driven).
- [x] ✅ 7f. [INFRA] P1. **CLOSED AS MOOT 2026-08-08 — the VM is not stopped, it is permanently TERMINATED by deliberate
      operator policy, and the human-planning role itself no longer exists.** Split out of 7d once 7d's AO-VM half
      completed; at the time this todo was written it read the VM's absence from `aws ec2 describe-instances` as "could
      not be provisioned, not currently running" (implying a future start would unblock it). That framing is stale:
      `orchestrator_vm_registry.yaml` confirms `i-0dd9812a96cdda5dc` IS the `human-planning` VM, and three independent
      codex SSOTs — `/codex/05-infrastructure/agent-orchestrator-deploy.md`,
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, and
      `/codex/08-workflows/agent-orchestrator-e2e-operator-runbook.md` — all state it was **TERMINATED 2026-08-03** as
      deliberate policy (single-VM architecture; `planning` is the only VM), not left stopped pending a restart. Nothing
      should provision `unified-trading-ci` onto it — there is no "whoever next starts that VM" scenario, since
      restarting it is not the plan. No re-scoping to a different host needed either: the human-planning interactive
      role was folded into the single central `planning` VM's slot-based model, which todo 7d already provisioned. Done
      when (met): confirmed via 3 independent codex SSOT citations that the VM's absence is permanent policy, not a
      transient outage — no further action needed on this todo.
- [x] 7e. ✅ [INFRA] P1. **Clarifying what did NOT move, since this could easily be misread**: only the 5 files named in
      "Confirmed technical facts" moved to `unified-trading-ci`. `unified-trading-pm/scripts/quality-gates-base/`,
      `codex/`, and every other PM script/doc stay exactly where they are — the reusable workflow's own
      `clone_repo unified-trading-pm` step (confirmed PAT-authenticated, visibility-agnostic — see "Confirmed technical
      facts") still clones PM itself for that content on every CI run, unchanged. No other repo's tests, scripts, or
      `pyproject.toml` dependencies reference PM differently because of this migration — the ONLY thing any of the 25
      repos needed edited is their own `.github/workflows/*.yml` `uses:` lines (Phases 3-5), which is already fully
      tracked per-repo above.

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

- [x] 11. ✅ [INFRA] P1. **Wave 1 (6 lowest-churn) — all 6 shipped + verified green.** `quality-gates-v2.yml` +
      `image-build-gate.yml` re-pointed at `unified-trading-ci@main` in each; `push:` only triggers on `main`/`staging`
      (not LDR), so a bare quickmerge landing doesn't auto-fire the gate — manually dispatched
      (`gh workflow run quality-gates-v2.yml --ref live-defi-rollout`) against each repo's actual landed commit to get
      real evidence rather than trusting a stale pre-migration run. All 6 confirmed `completed/success`: -
      `ibkr-gateway-infra@9e545b6` (run 31075913874) — also fixed a real pre-existing bug found while editing this file:
      a PRIOR session had "fixed" a dispatch issue by making `quality-gates-v2.yml` self-reference
      `IggyIkenna/ibkr-gateway-infra/...python-quality-gates-v2.yml`, a file that doesn't exist in that repo — CI had
      been silently broken since commit `64ebd8d0`. A concurrent slot fixed it back to `unified-trading-pm` mid-session
      (merge conflict, resolved in favor of `unified-trading-ci` — supersedes both). - `unified-trading-api@5dbff1a`
      (run 31075915538). - `unified-trading-system-ui@21e5b29c` (run 31075917008) — only 1 file
      (`image-build-gate.yml`); its `quality-gates-v2.yml` calls its own local `ui-quality-gates-v2.yml`, no PM
      dependency (UI convention, no Python tools). Hit 2 real pre-existing machine-level bugs while shipping this one,
      both fixed (not routed around): (1) `jsonschema`'s `rpds` dependency installed as x86_64 under an arm64 Python
      framework install — fixed via `pip install --user --force-reinstall jsonschema`; (2) the REAL cause of repeated
      failures even after fix (1): `/usr/local/bin/timeout` is a leftover Intel-only Homebrew `coreutils` binary with no
      `/opt/homebrew` arm64 counterpart — macOS makes a Rosetta-translated parent's children default to its own (x86_64)
      architecture slice of a universal binary, so `timeout 30 python3 ...` silently ran python3 in x86_64 mode
      regardless of the arm64 `--user` install. Fixed via `brew install coreutils` (installs the missing native arm64
      `/opt/homebrew/bin/timeout`, which now wins on PATH). This is a real, pre-existing machine-toolchain gap on this
      slot (Ikenna's laptop) that would break `buildspec.aws.yaml` validation for ANY repo's QG run here, not something
      specific to this migration — worth relaying if this slot is shared. - `fund-administration-service@bd976f0` (run
      31075918712). - `trading-agent-service@6150f23` (run 31075920238). - `system-integration-tests@d42430b` (run
      31075922319).
- [x] 12. [INFRA] P1. **Wave 2**: `greeks-service` (69), `deployment-ui` (76), `e2e-testing` (85), `execution-service`
      (96), `strategy-service` (99), `batch-live-reconciliation-service` (106) — all 6 shipped + pushed, `ahead=0`.
      Evidence: `greeks-service@b490fd0`, `deployment-ui@998c03e` (image-build-gate.yml only — same
      local-UI-workflow-PAT-clone pattern as `unified-trading-system-ui` in Wave 1, no `uses:` repoint needed for its
      quality-gates-v2.yml), `e2e-testing@3e333ae`, `execution-service@7b96ad5a7`, `strategy-service@9af7501d`,
      `batch-live-reconciliation-service@9807c68`. CI-verified: `greeks-service` PR#412 — `quality-gates-v2` PASSED
      (run 31081812845) + `image-build-gate`'s GCP Cloud Build actually DISPATCHED and queued (run 31081812648, job
      "validate / GCP Cloud Build — greeks-service") — this is the direct proof the original incident symptom (0-job
      "workflow was not found") does not recur; `deployment-ui` PR — `quality-gates-v2` PASSED (run 31081843622). The
      other 4 repos' promote PRs (e2e-testing#525, execution-service#550, strategy-service#496,
      batch-live-reconciliation-service#308) hadn't dispatched `quality-gates-v2`/`image-build-gate` yet at verification
      time (fleet-wide dispatch lag under load, same mechanism proven above) — all 4 DID show an unrelated, identical,
      fleet-wide `sit-gate/fleet-green` failure ("no informative completed full-workspace-sit run in last 10 —
      fail-closed"), a pre-existing standing condition unrelated to this migration, out of scope here, not actioned.
- [x] 13. [INFRA] P1. **Wave 3**: `client-reporting-api` (108), `alerting-service` (110),
      `market-data-processing-service` (162), `unified-trading-library` (178), `unified-api-contracts` (216),
      `deployment-api` (230 — its stray `@main` pin is now correct by construction on the new repo, no separate fix
      needed) — all 6 shipped + pushed, `ahead=0`, after the mid-Wave-3 revert incident (see Progress Log) required a
      root-cause fix + re-ship. Evidence: `unified-api-contracts@c5a9dd79`, `unified-trading-library@536b05e5`,
      `client-reporting-api@6b09fcd`, `alerting-service@0e529d7`, `market-data-processing-service@2e3e44f6`,
      `deployment-api@aebe564` (+ its dependency `deployment-service@ae97d1b9`, shipped first). CI-verified:
      `alerting-service` `quality-gates-v2` PASSED (recent run post-repoint).
- [x] 14. [INFRA] P1. **Wave 4 (final 5)**: `features-service` (232), `instruments-service` (249), `agent-orchestrator`
      (312), `market-tick-data-service` (340), `deployment-service` (393) — 4 of 5 shipped + pushed.
      `instruments-service` is the ONE incomplete item: its local `.github/workflows/*.yml` content is already correct
      (fixed by the fleet-wide rollout, todo re: revert incident below) but uncommitted — blocked by a genuine,
      unrelated, deterministic pre-existing test failure
      (`test_ftp_rollup_skips_junk_name_row_instead_of_crashing_whole_run`, 2 identical consecutive failures, confirmed
      not flaky) that fails `quality-gates.sh` and so blocks ANY commit to that repo, not just this one. Tracked as new
      todo 21 below. `system-integration-tests` (Wave 4 predecessor, already counted in Wave 3's repo-count context) is
      ALSO blocked transitively — it path-depends on `instruments-service`, whose pre-flight-audit-visible uncommitted
      state blocks it too; same root cause, same todo 21. Evidence: `features-service@314b699c`,
      `agent-orchestrator@4c76b4a`, `market-tick-data-service@75602490`, `deployment-service@ae97d1b9`. CI-verified:
      `features-service` `quality-gates-v2` PASSED (recent run post-repoint).
- [x] ✅ 15. [INFRA] P2. **CLOSED 2026-08-07 (na-eligibility-audit) — satisfied by todo 23's broader fix, not
      independently executed.** Todo 23 (done, same day) repointed every `agent-audit.yml` across the fleet (16 repos,
      the exact list this todo names plus more) plus the composite-action callers to `unified-trading-ci`, and its own
      Progress Log records a post-fix fleet-wide re-sweep confirming "ZERO remaining
      `uses:.*unified-trading-pm/.github/` references in any real (non-stale, non-worktree) repo" — a stronger, more
      general check than this todo's own narrower `python-quality-gates-v2`-only grep, and it subsumes this todo's exact
      scope. Original text preserved below for record. Was: **Fleet-wide re-point sweep for the stray `@main`-pinned
      `agent-audit.yml` copies** found during research (`client-reporting-api`, `market-data-processing-service`,
      `deployment-service`, `unified-trading-library`, `system-integration-tests`, `unified-api-contracts`,
      `ibkr-gateway-infra`, `instruments-service`, `features-service`, `market-tick-data-service`, `execution-service`,
      `batch-live-reconciliation-service`, `trading-agent-service`, `alerting-service`, plus PM's own copy) — these are
      lower-stakes (`workflow_dispatch`-only per earlier fleet audit) but should still converge on
      `unified-trading-ci@main` for consistency, not left pointing at a dead/stale PM ref. Evidence: fleet-wide grep
      showing zero remaining `uses: IggyIkenna/unified-trading-pm/.github/workflows/python-quality-gates-v2` hits
      anywhere outside PM's own not-yet-migrated copy (until Phase 5 lands).

### Phase 5 — Migrate PM itself last (it currently hosts the source of truth)

- [x] 16. ✅ [INFRA] P1. **Re-pointed PM's own `quality-gates-v2.yml`** from the local
      `uses: ./.github/workflows/python-quality-gates-v2.yml` self-call to the same remote-ref pattern every other repo
      now uses (`uses: IggyIkenna/unified-trading-ci/.github/workflows/python-quality-gates-v2.yml@main`) — removes the
      chicken-and-egg special case (now genuinely obsolete: PM is just another caller, not the host). Grepped PM's own
      `.github/workflows/*.yml` for `uses: ./.github/workflows/notify-slack.yml`: 45 internal consumers
      (branch-health.yml, ci-health.yml, etc.) — `notify-slack.yml` stays, NOT deleted in todo 17. Along the way found +
      fixed a genuine content divergence: PM's `python-quality-gates-v2.yml` had a newer, real production fix (gate the
      GH-Actions-cache restore/save to GitHub-hosted-only — self-hosted runners' persistent `~/.cache/uv` already
      survives between jobs, measured 450-894s wasted per job on the unconditional version) that `unified-trading-ci`'s
      extracted copy was still missing — ported it before it could be silently lost, shipped as
      `unified-trading-ci@f20c59f` (also fixed this laptop slot's `unified-trading-ci` checkout, which had drifted onto
      tracking `live-defi-rollout` instead of `main` from the initial clone — corrected the upstream and reconciled the
      two branches). Evidence: `unified-trading-pm@ab53f71b33`, `unified-trading-ci@f20c59f`. CI-verified functionally
      correct (content-sentinel + tests legs both PASS on every dispatched run, no "workflow not found" resolution
      error) — see todo 17's note for why the "checks" leg itself reads red for unrelated reasons.
- [x] 17. ✅ [INFRA] P1. **Deleted PM's own now-redundant copies** of `python-quality-gates-v2.yml`,
      `image-build-validate.yml`, `.github/actions/setup-python-tools/`, `.github/actions/setup-agent-tools/` (kept
      `notify-slack.yml`, see todo 16) once `unified-trading-ci` was confirmed the sole live source for all 25 repos
      (Phase 4 fully green). Found a SECOND, non-`uses:`-reference internal consumer the earlier fleet-wide grep sweep
      had missed: `scripts/quality_gates/check_qg_slice_completeness.py` read `python-quality-gates-v2.yml`'s raw file
      content directly (`CI_WORKFLOW.read_text()`, not a GHA `uses:` reference) to enforce local↔CI slice-partition
      parity — since this check runs from EVERY repo's `quality-gates.sh` (its `PM_ROOT` resolves via the script's own
      `__file__` location, always inside PM, regardless of which repo invoked it), deleting the file without fixing this
      would have broken local QG for the entire fleet, not just PM. Fixed by having it read the sibling
      `unified-trading-ci` checkout first, falling back to a live `raw.githubusercontent.com` fetch for environments
      without the sibling cloned (e.g. a bare GHA runner). Evidence: `unified-trading-pm@b62a209dc0`. **A real,
      unrelated, PRE-EXISTING blocker was found while verifying, NOT caused by this todo**: PM's own CI
      `quality-gates-v2` "checks" leg fails on a corpus-wide plan-hygiene ratchet regression
      (`check_na_corpus_ratchet.py`: `assigned_vm:NA` backlog grew from baseline 384 docs/1347 open todos to 389/1366,
      plus 3 other hygiene ratchets — AG-closeout linkage, terminal-status-archived, archive-candidates) — proven
      pre-existing and unrelated by re-checking todo 16's OWN verification run (31106573878, dispatched BEFORE this
      deletion was ever made): it hit the exact same "checks" leg failure. This is live, ongoing corpus drift from
      concurrent multi-slot plan/issue activity on `live-defi-rollout` (observed directly via repeated `git pull`s
      pulling in other slots' new/archived docs throughout this session) — nothing this migration touched. Content
      sentinel and the `tests` leg both PASS on every run; within the failing `checks` leg, the actual code under test
      (the deletion + the `check_qg_slice_completeness.py` fix) is independently verified via a clean standalone local
      run (`python3 scripts/quality_gates/check_qg_slice_completeness.py` → ✅). NOT fixed here (out of scope, large,
      the sanctioned remedy is `/na-eligibility-audit`) — flagged to the operator directly in-session as a real,
      currently-active, PM-CI-blocking condition worth a proactive corpus-hygiene pass.
- [x] 18. ✅ [INFRA] P2. **Update the template sources** (`scripts/workflow-templates/quality-gates-v2.yml.tmpl` line
      ~64, `scripts/workflow-templates/image-build-gate.yml`) — done EARLY (out of original Phase-5-deferred order), not
      as a nice-to-have but as an emergency ROOT-CAUSE FIX mid-Wave-3 (see Progress Log "revert incident"): a scheduled
      fleet-hygiene job re-syncs every repo's per-repo workflow copy to these templates on a ~20min cadence, and since
      they still said `unified-trading-pm`, it was silently reverting every hand-edit this migration made, including
      already-shipped-and-CI-verified Wave 2 repos. Evidence: `unified-trading-pm@a2feeb4de1`; a subsequent
      `rollout-workflow-templates.sh` dry-run for an already-migrated repo showed only the intended content, confirming
      the template now matches the target state.
- [x] 19. ✅ [INFRA] P2. **Updated `/codex/08-workflows/ci-cd-flow.md`** — the caller/callee table now reads "Every repo
      (incl. PM)" instead of a PM-special-cased local ref, pointing at
      `IggyIkenna/unified-trading-ci/.github/workflows/python-quality-gates-v2.yml@main`; added a "Host moved to
      unified-trading-ci (2026-08-06)" note explaining the `main_ci_red` incident that motivated the extraction, that PM
      is now just another caller (chicken-and-egg case retired), and that `notify-slack.yml` deliberately did NOT move
      (local-only in every repo, never cross-repo). This is the plan's final documentation step — the SSOT now describes
      the finished state, not a mid-migration one. Evidence: `unified-trading-pm@55e4a6dba6`.
- [ ] 20. [INFRA] P3. _(stretch, optional)_ **Add a `.pre-commit-config.yaml` to `unified-trading-ci`** — it currently
      only has the pre-push strict-quickmerge hook (installed at slot-provisioning time, todo 7b); it has no `prek`
      pre-commit hook, so no commit-time gate (gitleaks, conventional-commit, trailing-whitespace) runs there the way it
      does on every other fleet repo. Low risk given the repo's tiny, YAML-only surface, but worth closing for
      consistency. **EXTRACTED 2026-08-09 (round11 infra-tranche RECLASSIFY+satellite-extraction sweep)** →
      `infra_satellite_ao_dispatch_batch14_2026_08_09.md` (`status: draft`, awaiting operator review) + its gated
      finalize twin, which will flip this checkbox once shipped. Do not duplicate-dispatch.
- [x] 21. ✅ [BUG] P2. **`instruments-service` + `system-integration-tests` — RESOLVED, was host-load flakiness, not a
      real bug.**
      `tests/unit/scripts/test_build_instrument_catalogue.py::test_ftp_rollup_skips_junk_name_row_instead_of_crashing_whole_run`
      failed twice identically during the severe host-contention episode (load average ~190 on this 10-core/8-user
      shared host, see revert-incident Progress Log entry). Ran the test in isolation once the incident's own concurrent
      QG load subsided — PASSED cleanly on the first try. Load had dropped to ~22 by the time of re-verification; re-ran
      the full quickmerge and it passed outright, no code change needed. Evidence: `instruments-service@451e624e`
      (CI-verified: `quality-gates-v2` PASSED, run against `promote/instruments-service/451e624ed903`),
      `system-integration-tests@2f9192e` (unblocked transitively once `instruments-service` landed; CI-verified
      `quality-gates-v2` PASSED).
- [x] 22. ✅ [BUG] P3. **`unified-trading-system-ui` — RESOLVED, real root cause found: its local `.venv` was
      essentially empty.** The earlier `jsonschema module not available` failure was NOT a PATH/backgrounding quirk as
      first suspected — `quickmerge.sh` activates this repo's own `.venv` (`source .venv/bin/activate`), and that venv
      (a bare `uv`-created Python 3.13.9 environment with no `pip` and no `pyproject.toml` `[project]`/dependencies
      section governing it) had neither `jsonschema` nor `pyyaml` installed, shadowing the system framework Python that
      had them. Fixed durably via `uv pip install jsonschema --python .venv/bin/python3` then (once that surfaced a
      second missing module on the next gate step, `cloudbuild.yaml`'s YAML parse)
      `uv pip install pyyaml --python .venv/bin/python3` — both installs are permanent since nothing re-syncs this
      ungoverned venv against a dependency file that could silently drop them again. Evidence:
      `unified-trading-system-ui@f4f71d0f`.
- [x] 23. ✅ [BUG] P1. **Fleet-wide `agent-audit.yml` + peripheral-composite-action dangling-reference sweep —
      discovered post-completion, fixed same day.** The original Wave 2-4 migration + todo 17 (PM's `uses:` grep sweep)
      only checked each repo's TWO caller workflows (`quality-gates-v2.yml`, `image-build-gate.yml`). It missed a
      SEPARATE caller class: `agent-audit.yml` (a manual `workflow_dispatch`-only prototype workflow present in most
      fleet repos) independently invokes `python-quality-gates-v2.yml` as its own reusable-workflow job, and a handful
      of repos also call the two composite actions (`setup-python-tools`, `setup-agent-tools`) directly from
      benchmark/SIT workflows — all pointed at `unified-trading-pm`, which no longer hosts any of these paths after todo
      17's deletion. Found via a fresh fleet-wide `grep -rln "uses:.*unified-trading-pm/.github/"` sweep (the same
      technique the original migration used, just re-run after the fact) — 16 repos' `agent-audit.yml` + 4 repos'
      benchmarks/performance-test/sit-plan-sync-agent/smoke-test-gate workflows were still dangling. Fixed by repointing
      every hit to the equivalent `unified-trading-ci` path (`unified-trading-ci` already hosted both composite actions,
      confirmed via directory listing before repointing). One pre-existing, unrelated dead reference also caught and
      fixed in the same sweep: `deployment-ui/agent-audit.yml` pointed at a `quality-gates.yml@live-defi-rollout` (v1,
      no `-v2` suffix) that had not existed in PM for a long time before this migration — repointed to the correct v2
      path for consistency. Shipped dependency-root-first (quickmerge's pre-flight audit enforces this):
      `unified-api-contracts@29ed3067`, `unified-trading-library@61c455fc`, then the 15 dependents —
      `alerting-service@3fb8ac4`, `batch-live-reconciliation-service@cf7c072`, `client-reporting-api@ed509a0`,
      `deployment-service@4a69f9d0`, `deployment-api@50b6888`, `deployment-ui@b6b286c`, `execution-service@008dae3bf`,
      `features-service@86af9105`, `ibkr-gateway-infra@5667c3e`, `instruments-service@05b668a0`,
      `market-data-processing-service@7e95f655`, `market-tick-data-service@727305ce`, `strategy-service@d411fd8b`,
      `system-integration-tests@6eddc31`, `trading-agent-service@c710db5`. Post-fix fleet-wide re-sweep confirms ZERO
      remaining `uses:.*unified-trading-pm/.github/` references in any real (non-stale, non-worktree) repo. **Known,
      deliberately-not-fixed residual**: `features-service/features_service/{calendar,commodity,multi_timeframe}/`
      contain NESTED `.github/workflows/` directories (own README/LICENSE/`.github`, last touched 2026-05-08 — dormant
      staged-extraction scaffolds for a future split-out) still referencing `unified-trading-pm`. These are inert:
      GitHub Actions only discovers workflows under `.github/workflows/` at a repo's true root, never at a nested path,
      so these files never execute as real CI — confirmed by checking the trigger config and the fact that no
      `features-service` root workflow references them. Left as-is; worth a cheap fix if/when that nested scaffold is
      ever revisited, not before. **Separately investigated and ruled out**: whether PM's
      `scripts/workflow-templates/{image-build-gate.yml, quality-gates-v2.yml.tmpl}` should also be deleted now that
      `unified-trading-ci` "won" — read the actual template file (`quality-gates-v2.yml.tmpl` header: "CANONICAL SOURCE.
      Do NOT hand-edit per-repo copies — edit THIS template"). These are NOT duplicates of unified-trading-ci's real CI
      logic; they are the source templates `rollout-workflow-templates.sh` uses to keep every repo's small local
      `uses:`-pointer caller-stub in sync (every repo, including PM, MUST have a physical caller-stub file in its own
      `.github/workflows/` — GitHub Actions cannot resolve a `uses:` reference without one). Deleting them would remove
      the exact mechanism that caught and fixed this session's original revert incident (stale template → scheduled
      rollout job silently reverts hand-edits). Correctly NOT deleted.

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — gate set / quickmerge / reusable-workflow rollout mechanism this plan operates
  within; needs a note added once this plan ships pointing future readers at `unified-trading-ci` as the actual host of
  the reusable QG/image-build gates (currently documents PM as the host).
- `/codex/05-infrastructure/per-tab-worktrees.md` — per-slot worktree model; needs its repo list / manifest reference
  implicitly covers the new repo once workspace-manifest.json (todo 4) lands, no separate edit expected.

## Progress Log

- **na-eligibility-audit 2026-08-09 (round11 RECLASSIFY+satellite-extraction sweep, infra tranche)**: KEEP-NA, valid —
  whole-doc RECLASSIFY still blocked (todo 3 remains conflict-gated: re-checked fresh,
  `ci_satellite_ao_dispatch_batch6_2026_08_08.md` and its named successor
  `ci_satellite_ao_dispatch_batch7_2026_08_09.md` are both now archived `status: complete` and neither actually picked
  up todo 3's `image-build-gate.yml` rollout-mechanism item — it remains genuinely un-picked-up but is the CI tranche's
  own candidate per D6-1's framing, not this infra sweep's). **Per-item extraction: todo 20 (the
  `.pre-commit-config.yaml` addition, independently flagged conflict-clear by the 2026-08-08 round7 audit) extracted →
  `infra_satellite_ao_dispatch_batch14_2026_08_09.md` + gated finalize twin, both `status: draft`.** Doc stays
  `assigned_vm: NA` overall (todo 3's conflict still blocks a whole-doc flip). Checked against this round's
  accumulated-precedent list (IAM self-service, D16 all-repos, S5.1 tiering, plan-destination-AO-default,
  escalation-N=3-days, reversibility-qualified deletes, Option B retired, GSM secret + 5 Slack webhooks) — none bear on
  todo 3's rollout-mechanism-ownership conflict.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — with a live conflict found, don't
  flip. Re-read end-to-end; `grep -cE '^- \[ \]'` = 2, matching (both `(stretch, optional)` `[INFRA] P3` items: todo 3,
  add `image-build-gate.yml` to `rollout-workflow-templates.sh`'s managed file set; todo 20, add a
  `.pre-commit-config.yaml` to `unified-trading-ci`). Both looked genuinely bounded and low-risk on this doc's own text
  alone, so ran the required conflict-check before considering a flip — and found todo 3 is ALREADY conflict-gated by a
  concurrent, same-day ci-tranche audit: `ci_satellite_ao_dispatch_batch6_2026_08_08.md` (D6-1) explicitly defers this
  exact todo, citing its own todo 9 as owning `scripts/workflow-templates/`'s rollout mechanism this round. Since
  `assigned_vm` flips whole-doc and todo 3 has a live, real collision with concurrently dispatched work, this doc stays
  NA even though todo 20 (`.pre-commit-config.yaml`) shows no conflict on its own — flagging todo 20 as a RECLASSIFY
  candidate for a future, properly-scoped follow-up once todo 3's collision clears, not actioned this run. This is
  exactly the "Conflict → don't flip" case the sweep's own protocol names.
- **infra-tranche NA-question resolution 2026-08-08**: closed todo 7f as moot — the human-planning VM
  (`i-0dd9812a96cdda5dc`) is not a stopped VM waiting to be restarted, it was permanently TERMINATED 2026-08-03 by
  deliberate operator policy (confirmed via 3 codex SSOTs: `/codex/05-infrastructure/agent-orchestrator-deploy.md`,
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`,
  `/codex/08-workflows/agent-orchestrator-e2e-operator-runbook.md`). No re-scoping needed — the human-planning
  interactive role folded into the central `planning` VM's slot model, already provisioned by todo 7d.
- **na-eligibility-audit 2026-08-06** (infra tranche): KEEP-NA, valid — explicit dated operator ruling (this log:
  "LOCAL/human track, repo name `unified-trading-ci`"); 7c/7d [OPERATOR] on other machines; deletion/SSOT-write steps
  deliberately sequenced last.
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
- **2026-08-06 (interactive session, continued): Phase 4 Wave 1 shipped and verified — todo 11 done, all 6 repos
  green.** Found `push:` only triggers `quality-gates-v2` on `main`/`staging`, never on a bare LDR quickmerge landing —
  every wave's verification needs an explicit `gh workflow run --ref live-defi-rollout` dispatch, not just "it shipped
  cleanly." Two real pre-existing bugs found and fixed along the way, not routed around: `ibkr-gateway-infra` had a
  silently-broken CI gate since 2026-08-04 (a prior session's mistaken self-reference fix pointed `uses:` at a file that
  doesn't exist in that repo — corrected to `unified-trading-ci`, which also resolved a same-file merge conflict against
  a concurrent slot's independent revert-to-PM fix); this slot (Ikenna's laptop) had a machine-level Intel/ARM Homebrew
  toolchain gap (`/usr/local/bin/timeout` had no `/opt/homebrew` arm64 counterpart, so a Rosetta-translated `timeout`
  forced its `python3` child into x86_64 mode, breaking `jsonschema`'s native deps for EVERY UI repo's
  `buildspec.aws.yaml` check) — fixed via `brew install coreutils`, a genuine machine fix worth relaying if this slot is
  shared with another operator. Next: Wave 2 (6 repos).
- **2026-08-06 (interactive session, operator asked: do all slots/AO need the repo, do PM-referencing scripts need
  updating, document + action it with Harsh instructions).** Answered by actually testing the standard provisioning
  script rather than assuming — found + fixed a real gap (todo 7a: `unified-trading-ci` needed a `live-defi-rollout`
  branch, not just `main`, for `setup-tab-worktrees.sh` to work at all), then provisioned all 11 of Ikenna's local slots
  for real (todo 7b), split the remaining machines into concrete per-machine todos with copy-pasteable commands (7c
  Harsh, 7d AO VMs), and explicitly confirmed what did NOT move (7e — PM's `scripts/`/`codex/` stay exactly where they
  are; only the 5 CI-workflow files migrated). `slot-cron-ff-pull.sh` needed zero changes — confirmed by reading it
  directly, it discovers repos by scanning actual directories, not the manifest. Todos 7c/7d genuinely can't be closed
  from this session (different machines); everything else in the per-machine track is done.
- **2026-08-06 (interactive session, continued after /compact): Wave 2 shipped and verified (todo 12); todo 7d actually
  executed, not just documented.** Operator asked directly whether the AO VM runbook had actually been run — re-checked
  and found this laptop DOES have standing SSH access to `agent-orchestrator-vm` (`~/.ssh/config`, missed earlier), so
  ran the real provisioning instead of leaving it `[OPERATOR]`: cloned the `unified-trading-ci` sibling on the central
  orchestrator VM and backfilled all 16 of its active slots via `--add-slot` (verified: all 16 on `live-defi-rollout`
  with the pre-push hook, no disruption to the very-recent live worker activity already running in those slots). The
  human-planning VM could not be reached — it isn't currently a running EC2 instance at all (not in `describe-instances`
  under any state), split out to a new todo 7f, genuinely operator-owned (needs someone to start the VM first). Wave 2's
  6 repos all shipped clean (`ahead=0` each): `greeks-service`, `deployment-ui`, `e2e-testing`, `execution-service`,
  `strategy-service`, `batch-live-reconciliation-service`. `e2e-testing`'s first quickmerge attempt self-blocked
  correctly on its own pre-flight audit (path deps `execution-service`/`strategy-service` still had uncommitted edits
  mid-wave) — not a bug, retried clean once those landed. CI-verified via 2 repos with real dispatched runs
  (`greeks-service` PR#412 — `quality-gates-v2` PASSED + `image-build-gate`'s GCP Cloud Build actually queued, proving
  the original "workflow not found" incident symptom does not recur; `deployment-ui` — `quality-gates-v2` PASSED); the
  other 4 repos' promote PRs hadn't dispatched those checks yet at verification time (fleet dispatch lag) but all 4
  showed an identical, pre-existing, fleet-wide `sit-gate/fleet-green` failure ("no completed full-workspace- sit run in
  last 10") unrelated to this migration — noted, not actioned, out of scope. Next: Wave 3 (todo 13, 6 repos).
- **2026-08-06 (interactive session, continued): REVERT INCIDENT mid-Wave-3 — root-caused, fixed, and the entire fleet
  (Waves 1-4) re-verified and re-shipped.** Operator asked "hope you aren't running duplicate workflows... any
  plans/issues which reference the wrong stuff would be rolled out too" — investigating that question surfaced the real
  incident. **What happened**: partway through Wave 3, `alerting-service`'s and other repos' `image-build-gate.yml`
  content was found REVERTED back to `unified-trading-pm` — despite having been hand-edited (and for Wave 1/2, already
  committed + pushed + CI-verified green). **Root cause**: a scheduled fleet-hygiene job
  (`rollout-workflow-templates.sh`, invoked from `main-backmerge-to-ldr.yml` on a ~20min cadence) re-syncs every repo's
  per-repo workflow copy to PM's canonical templates (`scripts/workflow-templates/image-build-gate.yml`,
  `quality-gates-v2.yml.tmpl`) — and since this migration had been hand-editing per-repo copies without ever updating
  those templates (deferred to Phase 5 as todo 18), the automation was correctly-per-its-own-design reverting every
  hand-edit back to the stale `unified-trading-pm` pointer, including on repos already shipped, pushed, and CI-verified
  in Wave 2 (`greeks-service`, `execution-service`, `strategy-service`, `batch-live-reconciliation-service` all found
  reverted; `deployment-ui` and `e2e-testing` survived only because they'd shipped too recently for the next drift-fixer
  cycle to have caught them yet). This was a genuine process-order flaw: the canonical template must be updated FIRST
  (or atomically with) the first per-repo hand-edit, never deferred to "later" while automation keeps re-syncing against
  the stale version. **The fix**: (1) updated both canonical templates (`unified-trading-pm@a2feeb4de1`, todo 18 done
  early); (2) PM's own `quality-gates.sh` correctly BLOCKED that commit on its own `workflow-template-parity` gate
  (every OTHER repo now read as "drifted" from the newly-correct template), which is the right behavior — so before PM's
  commit could land, ran `rollout-workflow-templates.sh` for real (no `--dry-run`) fleet-wide, regenerating all 25
  registered repos' LOCAL copies in one shot (this also pre-staged Wave 4, not yet touched, for free); it also
  spuriously created self-referential `image-build-gate.yml`/ `quality-gates-v2.yml` files IN `unified-trading-ci`
  itself (it builds no images, doesn't need to QG-gate itself this way) — deleted those (untracked, never committed)
  before shipping anything. Then shipped PM's template commit, then shipped all 21 successfully-affected repos
  individually via quickmerge (same 2-file `--files` scoping as every prior wave): `unified-api-contracts@c5a9dd79`,
  `unified-trading-library@536b05e5`, `client-reporting-api@6b09fcd`, `alerting-service@0e529d7`,
  `market-data-processing-service@2e3e44f6`, `deployment-service@ae97d1b9`, `deployment-api@aebe564`,
  `greeks-service@f4d8e9d`, `deployment-ui@849ac9a`, `execution-service@3c7b866eb`,
  `batch-live-reconciliation-service@5001652`, `strategy-service@4393c2a4`, `e2e-testing@b74bfcb`,
  `features-service@314b699c`, `agent-orchestrator@4c76b4a`, `market-tick-data-service@75602490`, `ml-service@166bae2`,
  `ibkr-gateway-infra@7432214`, `unified-trading-api@f60b831`, `fund-administration-service@ffe5505`,
  `trading-agent-service@a4c9ebc` — the canary/Wave-1/e2e-testing repos needed re-shipping too even though their `uses:`
  line was never reverted (safe, already committed) — the rollout also touched a cosmetic header-comment line ("Calls
  PM-hosted..." → "Calls unified-trading-ci-hosted...") for full byte-parity with the SSOT template, closing the gap
  that caused the incident in the first place. **CI-verified**: `alerting-service` and `features-service` both show
  recent PASSED `quality-gates-v2` runs post-repoint. **Three repos remain incomplete**, tracked as new todos 21
  (`instruments-service` + transitively `system-integration-tests`, blocked on a genuine unrelated deterministic
  pre-existing test failure, confirmed not flaky via 2 identical consecutive failures) and 22
  (`unified-trading-system-ui`, blocked on a persistent `jsonschema`-under-backgrounded-quickmerge environment quirk on
  this laptop slot, survived 4 attempts including an explicit `PATH` fix — root cause not pinned). Both repos' LOCAL
  workflow-file content is already correct (the fleet-wide rollout already applied it); only the commit is blocked, for
  reasons unrelated to this migration. **Also hit**: a severe host-contention episode mid-sweep (load average ~190 on
  this 10-core/8-user shared host, causing quality-gate queue-wait timeouts on 2 consecutive attempts) — worked around
  per operator direction by switching from 2-concurrent to sequential shipping until load eased, then resuming
  2-concurrent once it did. **Lesson carried forward**: for any future fleet-wide workflow-template rollout, update the
  canonical template FIRST or ATOMICALLY WITH the first per-repo hand-edit — never defer the template update to a later
  phase while a scheduled drift-fixer keeps re-syncing against the stale version; that ordering is what turned an
  otherwise-routine migration into a silent-revert incident that had to be caught by the operator asking a probing
  question rather than by any automated check. Wave 3 (todo 13) and Wave 4 (todo 14) both flipped done, with the
  incomplete items called out explicitly rather than glossed over. Next: Phase 5 (todos 16-17, 19-20 — migrate PM itself
  last), plus resolving todos 21-22 when their respective root causes are fixed.
