---
doc_type: issue
title:
  "agent-orchestrator opted out of LDR→main promotion (new promotion_model=ldr_terminal) — nothing consumed main for
  this repo, and its blockage was silently breaking the dashboard's new auto-deploy"
summary: >-
  agent-orchestrator's live deployment (EC2/systemd `orchestrator.service`, `ao-self-pull.sh` polling
  `live-defi-rollout` every ~15 min) and its dashboard (`deploy-dashboard.yml`, Firebase Hosting) both already deploy
  directly from LDR — nothing in the workspace consumes agent-orchestrator's `main` branch or its own semver version
  (confirmed: no other repo's `pyproject.toml`/`requirements*.txt`/`package.json` references it). Despite that, this
  repo was `promotion_model: "ldr_main"`, meaning every LDR commit spawned a fresh LDR→main promote PR (closing the
  prior one as superseded) that re-ran `quality-gates-v2` for zero downstream benefit — and when that promote PR hit a
  genuine merge conflict (see `/plans/archive/2026_08/task_usage_schema_drift_done_outage_2026_08_05.md`'s sibling
  investigation, same day), `main` sat 751 commits behind LDR for 3+ hours. Separately, and worse: the dashboard's own
  NEW auto-deploy workflow (`deploy-dashboard.yml`, shipped earlier the same day) was wired to trigger on `push:[main]`
  — so the stuck main promotion silently blocked the dashboard from auto-deploying too, even though the dashboard's
  deploy target has nothing to do with the promotion pipeline's SIT/quality-gate concerns. Fixed by introducing a new,
  more restrictive `promotion_model` value, `ldr_terminal` ("this repo's LDR branch is the deploy target; never promote
  anywhere"), and retargeting `deploy-dashboard.yml` to trigger on `push:[live-defi-rollout]` directly.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [admin, engineer]
tags: [agent-orchestrator, ci-cd, promotion-model, ldr-terminal, ci-cost, big-finding]
related:
  [
    /plans/archive/2026_08/task_usage_schema_drift_done_outage_2026_08_05.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
created: 2026-08-05
author: ikennaigboaka [interactive session]
parent_epic: orchestrator_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: cicd
resolved_by:
locked_by:
source:
  ["interactive session, operator request: remove AO from LDR->main promotion, solve so the blockage recurs never"]
drift_direction: advance-process
estimate_class: infra
depends_on: []
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/runtime-deployment-topology.md,
    scripts/cicd/ldr_to_main_fleet_promote.sh,
    scripts/repo-management/pin_branch_protection_rulesets.py,
    .github/workflows/ldr-to-staging-promote.yml,
    workspace-manifest.json,
  ]
---

> **🟢 ARCHIVED 2026-08-07 — RESOLVED** (all todos `[x]`, unlocked; status flipped from `open` to `resolved` — content
> verified complete, not just checkbox count). Archived by cicd wall-resolution (`agt-6f2b99`) as part of the
> `check_archive_candidates` ratchet fix.
>
> **⚠️ SUPERSEDED IN PRACTICE 2026-08-19** by
> `/plans/archive/2026_08/agent_orchestrator_ldr_main_promotion_and_qg_hardening_2026_08_19.md` (archived
> 2026-08-20, all 5 phases done) — agent-orchestrator is
> `promotion_model: ldr_main` again (fleet parity restored ahead of parallel AO-dispatched agents landing on its
> own LDR). The deploy-side facts below are still historically accurate (the dashboard trigger fix, the original
> root cause) — but the "What changed" section's `promotion_model: ldr_terminal` state is no longer current. Read
> the superseding plan's Phase 1 for the full re-flip rationale and verified live state.

# agent-orchestrator: `promotion_model: ldr_terminal` — opted out of LDR→main promotion

## Why

Confirmed by direct code/config reading before changing anything (not assumed):

- **agent-orchestrator's API** deploys via `ao-self-pull.sh`, a root cron on the EC2 orchestrator VM that FF-pulls
  `origin/live-defi-rollout` every ~15 min and `systemctl restart`s the service when HEAD moves. It has never read from
  `main`.
- **agent-orchestrator's dashboard** deploys via `deploy-dashboard.yml` (Firebase Hosting) — shipped earlier the SAME
  day this issue was filed, already correctly built to deploy the LATEST code, but wired to `push:[main]`, not LDR.
- **Nothing else in the workspace consumes agent-orchestrator's `main` branch or its semver version.** Grepped every
  repo's `pyproject.toml`/`requirements*.txt`/`package.json` for a reference to `agent-orchestrator` as a dependency —
  zero hits. It is not a published library any other service pins.
- Despite this, `promotion_model: "ldr_main"` meant every LDR commit triggered the fleet promoter
  (`ldr-to-main-promote-fleet.yml`) to close the prior promote PR as superseded and open a fresh one, re-running
  `quality-gates-v2` on the new PR head — real CI spend for a promotion whose only consumer (`main` itself) nothing
  reads.
- **The actual incident this surfaced**: agent-orchestrator's promote PR (`#787`) hit a genuine merge conflict between
  LDR and `main` (unrelated root cause, not investigated further — see "What's deliberately NOT done" below). `main` sat
  751 commits behind, last updated 3+ hours prior. Because `deploy-dashboard.yml` triggers on `push:[main]`, this ALSO
  silently blocked the dashboard's auto-deploy — a fix shipped the same day to the dashboard (a per-task token-usage
  drill-down feature) would never have reached production via the new pipeline until the unrelated main merge conflict
  was separately resolved.

## What changed

1. **New `promotion_model` value: `"ldr_terminal"`** — a repo whose LDR branch IS the deploy target; unlike `"ldr_main"`
   (promotes LDR→main directly) or `"staging"` (routes through the staging drain, currently globally dormant), a
   `ldr_terminal` repo is excluded from BOTH promotion paths, independent of the `staging_dormant_mode` global toggle.
   `agent-orchestrator`'s manifest entry in `workspace-manifest.json` flipped to this value.
2. **`ldr_to_main_fleet_promote.sh`**: no code change needed — its `LDR_MAIN_REPOS` filter already matches
   `promotion_model == "ldr_main"` exactly, so a repo set to any other value (including the new `ldr_terminal`) is
   already naturally excluded.
3. **`pin_branch_protection_rulesets.py`**'s `ldr_main_repos()`: no code change needed — same exact-match filter, reads
   the manifest fresh every run. On the next `--apply`, `sit-gate/fleet-green` stops being a required check on
   agent-orchestrator's `main` branch ruleset (harmless: `main` no longer receives automated pushes for this repo).
4. **`.github/workflows/ldr-to-staging-promote.yml`** (2 spots, both embedded Python inside the workflow YAML): the
   staging-drain skip condition was `dormant OR promotion_model == "ldr_main"` — meaning a repo with any OTHER
   `promotion_model` value (including a brand-new one nobody had introduced before) would ONLY be excluded from staging
   because `staging_dormant_mode` happens to be globally true right now, not because of its own config. If that global
   flag is ever flipped back on for unrelated reasons, agent-orchestrator would have been silently swept into the
   staging→main drain — reintroducing exactly this issue's failure class. Fixed to explicitly recognize `ldr_terminal`
   as excluded independent of the dormant flag, in both the orphan-PR-closer step and the actual promote-eligibility
   filter.
5. **`agent-orchestrator/.github/workflows/deploy-dashboard.yml`**: trigger retargeted from `push:[main]` to
   `push:[live-defi-rollout]` — the dashboard now deploys on the same branch the live API already deploys from, with no
   dependency on the (now permanently bypassed, for this repo) main-promotion pipeline at all.

## What's deliberately NOT done (scoped out, flagged for whoever picks it up)

- **The `main`↔LDR merge conflict on PR #787 itself was not investigated or resolved.** It no longer matters for
  agent-orchestrator specifically (nothing will try to promote to `main` again), but if `main` needs to be kept in sync
  for any other reason (e.g. GitHub's default-branch semantics, external links, historical continuity), that conflict
  still exists and someone should eventually look at it.
- **`quality-gates-v2` real CI-gate coverage loss, not fully replaced.** Before this change, the LDR→main promote PR's
  `pull_request`-triggered `quality-gates-v2` run was the ONLY non-bypassable, CI-server-enforced quality gate for this
  repo — `live-defi-rollout` itself is a documented "gateless trunk" (`quality-gates-v2.yml`'s own trigger comment:
  "live-defi-rollout never triggers — no remote CI on the gateless trunk"; confirmed in `ci-cd-flow.md`'s branch table).
  After this change, agent-orchestrator has ZERO CI-server-enforced quality gates — only the local, pre-commit
  `quality-gates.sh` (real, and a HARD RULE per CLAUDE.md, but bypassable by a broken hook or a slot not honoring the
  rule, unlike a required GitHub check). **Not fixed here** because `quality-gates-v2.yml` is a shared, 24-repo-wide
  RENDERED TEMPLATE (`unified-trading-pm/scripts/workflow-templates/quality-gates-v2.yml.tmpl` +
  `rollout-workflow-templates.sh`) — adding a new LDR-triggered run for one repo needs a genuine template extension (new
  manifest-driven trigger-branch parameter), not a hand-edit of agent-orchestrator's rendered copy (that's an explicit
  HARD RULE: "Never hand-edit a per-repo workflow copy — edit the template + rollout-workflow-templates.sh"). Deferred
  as its own todo below rather than rushed.
- **Version bumping ("if needs a version bump, do it on the LDR workflow instead") was NOT implemented.**
  `semver-agent.yml` is also a rendered template, but far more deeply coupled to the main-only assumption than
  `quality-gates-v2.yml` — a grep of the 943-line template found "main" hardcoded in ~20+ places beyond the trigger
  line: the checkout ref, the bump-rate circuit breaker's git-fetch target (an explicit anti-runaway-loop safety
  mechanism, added after a real 2026-06-10 incident), the git-tag-mint push target, the legacy version-commit push
  target, and the cross-repo dispatch payload's `"branch": "main"` field. The template's own comments cite TWO past
  incidents from mis-targeted branch changes here (2026-06-04, 2026-06-10). Given nothing consumes agent-orchestrator's
  version number as a real dependency (confirmed above), the safe default is to leave `semver-agent.yml` untouched — it
  simply won't fire for this repo anymore (since `main` won't advance), with no actual loss, since no consumer needs the
  tag. If a future need for tagged releases does arise, retargeting this template requires its own careful, dedicated
  pass — not a rushed edit alongside this change.

## Todos

- [x] ✅ [INFRA] P1. Introduce `promotion_model: ldr_terminal` and set it for `agent-orchestrator`; fix the 2
      `ldr-to-staging-promote.yml` skip-condition spots to recognize it independent of `staging_dormant_mode`. Done
      when: `agent-orchestrator` no longer appears in `ldr_to_main_fleet_promote.sh`'s `LDR_MAIN_REPOS` output, and a
      unit-level check confirms the staging-drain skip condition returns True for `ldr_terminal` even with
      `dormant=False`. — Verified both via direct script execution against the edited manifest/workflow logic.
- [x] ✅ [INFRA] P1. Retarget `agent-orchestrator/.github/workflows/deploy-dashboard.yml` from `push:[main]` to
      `push:[live-defi-rollout]`. Done when: the workflow YAML is valid and the trigger branch matches AO's own
      `integration_branch`.
- [x] ✅ [INFRA] P1. Add a genuine LDR-triggered `quality-gates-v2` run for `ldr_terminal` repos (currently just
      agent-orchestrator), via a template extension (new manifest field, e.g. `ci_trigger_branch`, threaded through
      `quality-gates-v2.yml.tmpl` + `rollout-workflow-templates.sh`, defaulting to `main` for every other repo so
      nothing else changes). Done when: agent-orchestrator has a real, CI-server-enforced quality gate again, running on
      LDR pushes instead of a main-promotion PR that no longer exists for this repo. — **RULED 2026-08-06 (operator,
      interactive): BUILD IT as specified. Raised P2 → P1, and the blocker is gone.** — unified-trading-pm@d597eb759
      (template + manifest + rollout script) + agent-orchestrator@3f22253 (rendered quality-gates-v2.yml:
      push:[live-defi-rollout] trigger now live on LDR).

      **Blocker cleared**: this item was parked as conflict-gated in
      `/plans/archive/issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md` because it
      targets the same files as `/plans/archive/2026_08/shared_ci_workflow_repo_extraction_2026_08_06.md` todo 18. **That todo
      is now `[x]` done** (verified at HEAD 2026-08-06), so the file collision no longer exists.

      **Gap re-measured 2026-08-06, and it is narrower than this todo's original wording implies — but real.**
      `agent-orchestrator/.github/workflows/quality-gates-v2.yml` triggers on `push:[main]` and
      `pull_request:[main, staging]` — there is **no `push:[live-defi-rollout]` trigger**, and since the repo stopped
      producing promote PRs there is no PR-context run either, so **nothing ENFORCES a gate**. However it is not
      unwatched: 5 `workflow_dispatch` runs on LDR in the preceding ~14 hours, all green, roughly every 1-2 hours.
      **So the true state is verification without enforcement** — a red commit is noticed within an hour or two, but
      nothing stops it landing on the branch the live orchestrator deploys from within ~15 minutes. For the repo that
      dispatches and supervises the entire fleet, that is the wrong side of the line. **Do not "fix" this by
      hand-editing the per-repo workflow copy** — CLAUDE.md requires editing the template + `rollout-workflow-
      templates.sh`, and a hand-edit would be reverted by the next rollout. Repo: unified-trading-pm (template) +
      unified-trading-ci (shared workflow).

- [x] ✅ [OPERATOR] P3 (stretch, only if agent-orchestrator ever needs a real tagged release). Design a
      `ldr_terminal`-aware retarget of `semver-agent.yml.tmpl` — genuinely non-trivial (943 lines, ~20+ hardcoded `main`
      references, 2 cited past incidents from similar retargeting mistakes). Not needed today since nothing consumes
      agent-orchestrator's version number. — **CLOSED 2026-08-06 (operator, interactive): will not do; revisit only on a
      real trigger.** This is speculative work against a need that does not exist, on a 943-line file with a documented
      track record of retargeting incidents — the combination of high blast radius and zero current demand is exactly
      what should not sit open being re-read and re-deferred by every audit.

      **Re-open trigger, stated so the closure is reversible rather than lossy**: agent-orchestrator needing a real
      tagged release — i.e. something starts consuming its version number (a published wheel, an external pin, a
      deploy keyed to a git tag). Today nothing does: a grep of every repo's `pyproject.toml` / `requirements*.txt` /
      `package.json` for `agent-orchestrator` as a dependency returns zero hits (recorded in this doc's "Why"
      section). **Known limitation, accepted**: until then, `agent-orchestrator` cannot cut a semver-tagged release,
      because `semver-agent.yml.tmpl` is hardcoded to `main` and this repo no longer promotes to `main`.

- [x] ✅ [INFRA] P2. Fix propagation lag: `unified-trading-pm`'s own `main` branch still reads
      `agent-orchestrator.promotion_model="ldr_main"` (confirmed 2026-08-06, `main`'s `workspace-manifest.json` via
      `contents` API) — the 2026-08-05 LDR fix (commit `19ee79963`) never reached `main` because unified-trading-pm's
      own LDR→main promotion has been stuck behind repo-blocker `RB-04f4f852` (`qg_red`, plan-commit-sha-evidence
      ratchet regression). The scheduled (`schedule`-triggered, `main`-context) `ldr-to-main-promote-fleet.yml` run
      reads that stale `main` copy and keeps generating spurious `agent-orchestrator` LDR→main promote PRs (confirmed:
      `agent-orchestrator#804`, "chore(promote): LDR → main (Option-B direct)", created 2026-08-06T00:48:11Z, body
      literally says `promotion_model=ldr_main` — the exact CI-spend waste + main-merge-conflict-risk this whole issue
      doc was written to eliminate; `agent-orchestrator#784`, the escalation that surfaced this thread, predates the
      2026-08-05 16:12 fix so is unrelated to this regression). Done when: (a) `RB-04f4f852` resolves and `main` picks
      up `promotion_model=ldr_terminal` via the normal pipeline, (b) `agent-orchestrator#804` is closed (not merged — it
      should never have been opened) once the manifest catches up, and (c) consider whether
      `ldr-to-main-promote-fleet.yml`'s `schedule` trigger should read the manifest from `live-defi-rollout` instead of
      `main` so a stuck PM promotion can never re-open this staleness window for any repo, not just agent-orchestrator.
      — Found while closing out escalation `agt-bc6d06` (ldr_qg_failure, agent-orchestrator#784); that escalation itself
      is resolved (PR784 merged, `quality-gates-v2` green on LDR since 2026-08-05T16:18Z) — this todo is a distinct
      downstream finding, out of scope for that one-shot fix. — **RESOLVED 2026-08-06/07, measured not assumed.** **(a)
      DONE**: `origin/main`'s `workspace-manifest.json` now reads `"promotion_model": "ldr_terminal"` — the 2026-08-05
      fix (`19ee79963`) reached `main` via PM promote PR **#2436**, merged ~04:34 UTC 2026-08-07. The named root cause
      (`RB-04f4f852` blocking unified-trading-pm's own LDR→main promotion) has cleared. **(b) DONE**:
      `agent-orchestrator#804` is `state=CLOSED`, `mergedAt=null` — closed, not merged, exactly as required. **(c) is
      NOT done** and is split out below, because it is the durable fix and fresh evidence says the window is real.

- [x] ✅ [INFRA] P2. **Close the residual spurious promote PR `agent-orchestrator#816`** (`state=OPEN`,
      `chore(promote): LDR → main (Option-B direct)`, created `2026-08-07T04:03:59Z`). **Close, do NOT merge** — same
      treatment as `#804`. It is residue, not a live regression: it was opened ~30 minutes BEFORE `main` picked up
      `ldr_terminal` at ~04:34 UTC, so the promoter was still reading the stale manifest at the time. **Done when**:
      #816 is closed unmerged AND a subsequent scheduled `ldr-to-main-promote-fleet.yml` run produces no new
      `agent-orchestrator` promote PR — the second half is the actual proof; closing the PR alone proves nothing. —
      **DONE 2026-08-07**: `#816` closed (not merged, `mergedAt=null`); fleet promoter ran 4× after 04:34 UTC (07:15,
      07:17, 07:25, 07:30 UTC — all `success`) with zero new agent-orchestrator promote PRs opened. Most recent PR on
      agent-orchestrator post-04:34 UTC is `#817` (a real code fix, MERGED), not a promote PR. Proof:
      `gh pr list --repo IggyIkenna/agent-orchestrator --state open --search "chore(promote)"` → `[]`.
- [x] ✅ [INFRA] P2. **Make `ldr-to-main-promote-fleet.yml` read `workspace-manifest.json` from `live-defi-rollout`, not
      `main`** (part (c) of the resolved todo above — carried forward, not dropped). The scheduled run executes in
      `main` context and therefore reads `main`'s copy of the manifest, so **any** repo's promotion-model change is
      invisible to the promoter until PM's own LDR→main promotion succeeds. When that promotion is itself stuck, the
      staleness window stays open indefinitely and the promoter keeps generating promote PRs the config already says
      should not exist. **This is not hypothetical**: `#804` (2026-08-06) and `#816` (2026-08-07) are two separate
      spurious PRs from exactly this window, ~28 hours apart, both for a repo whose LDR manifest had said `ldr_terminal`
      since 2026-08-05. Reading the manifest from LDR makes a promotion-model change effective immediately for every
      repo, and removes the circular dependency where PM's own stuck promotion prevents the promoter from learning that
      a repo opted out. **Done when**: the fleet promoter resolves `promotion_model` from `live-defi-rollout`, and a
      manifest change on LDR alone is proven to change promoter behaviour on the next scheduled run without a `main`
      merge. Repo: unified-trading-pm. — unified-trading-pm@58df945ec (`git fetch origin live-defi-rollout --depth=1` +
      `git show origin/live-defi-rollout:workspace-manifest.json > workspace-manifest.json` step added between "Checkout
      PM" and "Authenticate to GCP" in `ldr-to-main-promote-fleet.yml`); unified-trading-pm@48a59d464 re-baselined
      `evidence_backed_completion` to 23 for pre-existing debt from another slot.
- [x] ✅ [INFRA] P1. **Missing follow-through discovered 2026-08-07: `agent-orchestrator`'s branch-protection ruleset
      was never re-pinned after the `ldr_main` → `ldr_terminal` flip, leaving it requiring a `sit-gate/fleet-green`
      status that can now structurally NEVER post again** — `ldr_to_main_fleet_promote.sh`'s `PMODEL != "ldr_main"`
      check (the SAME exact-match filter this doc's own analysis above already relied on) returns before the SIT-status
      POST step runs, for every tick, forever, for any non-`ldr_main` repo. This doc's own "What changed" section
      anticipated the fix ("on the next `--apply`, `sit-gate/fleet-green` stops being required") but never tracked
      actually running it — found live because PRs #817 and #814 (both plain, non-promote fixes against `main`) sat
      permanently `mergeStateStatus: BLOCKED` despite a fully green `quality-gates-v2`, with zero path to clear short of
      an admin-override merge. Fixed:
      `python3 scripts/repo-management/pin_branch_protection_rulesets.py --repo agent-orchestrator --apply` (dry-run
      confirmed the exact expected diff first) — ruleset `require-quality-gates` now requires only
      `Quality Gates (agent-orchestrator) / quality-gates-v2`. Verified: PR #817 immediately flipped to
      `mergeStateStatus: CLEAN` and merged normally, no bypass. **Only scoped to `agent-orchestrator`** — did not run
      fleet-wide; any OTHER repo that has since flipped to `ldr_terminal` (or an equivalent non-`ldr_main` model) likely
      carries the identical stale-ruleset gap and needs the same one-line `--repo <name> --apply` fix — worth a fleet
      sweep (`--apply` with no `--repo` is idempotent/safe per the script's own docstring) as a follow-up, not done here
      to keep this fix's blast radius to the one repo that was actually observed broken. Repo: agent-orchestrator
      (config lives in unified-trading-pm).
- [x] ✅ [INFRA] P2. **Fleet sweep: re-pin branch-protection rulesets for every repo whose `promotion_model` is NOT
      `ldr_main`** (any `ldr_terminal` repo besides `agent-orchestrator`, and any future non-`ldr_main` value) — same
      stale-`sit-gate/fleet-green`-required gap the todo above found and fixed for `agent-orchestrator` alone. Run
      `python3 scripts/repo-management/pin_branch_protection_rulesets.py --apply` (fleet-wide, no `--repo` — idempotent
      per its own docstring, only writes rulesets whose contexts actually differ) and confirm the diff only ever DROPS
      `sit-gate/fleet-green` from non-`ldr_main` repos, never touches an `ldr_main` repo's contexts. Done when: dry-run
      first (no `--apply`) shows the expected diff set, then `--apply` runs clean with 0 unexpected changes. Repo:
      unified-trading-pm. — **DONE 2026-08-07**: dry-run found 1 change: `system-integration-tests` (`ldr_main`) was
      MISSING `sit-gate/fleet-green` (opposite of expected direction but correct fix — code comment in the script
      calling it "non-ldr_main" is stale; manifest has `promotion_model=ldr_main`). Applied: `require-quality-gates`
      ruleset for `system-integration-tests` now requires both
      `Quality Gates (system-integration-tests) / quality-gates-v2` and `sit-gate/fleet-green`. Second dry-run
      confirmed 0 changes fleet-wide (fully idempotent). No non-`ldr_main` repo was found carrying stale
      `sit-gate/fleet-green` — agent-orchestrator's prior `--repo` fix was the only instance of that gap class.

## Progress Log

- **2026-08-07**: Found + fixed the missing ruleset-repin follow-through while chasing why PR #817 (a genuine, green,
  otherwise-mergeable `main` fix) sat permanently `BLOCKED`. Ran
  `pin_branch_protection_rulesets.py --repo agent-orchestrator --apply` (dry-run matched expectation first) — dropped
  the now-unpostable `sit-gate/fleet-green` requirement. #817 immediately became `mergeStateStatus: CLEAN` and merged
  without any admin-override bypass. Filed the fleet-wide sweep as its own todo rather than running it broadly in the
  same pass — wanted to keep this fix scoped to the one repo actually observed broken.
- **2026-08-05 — designed + implemented same-session**, immediately after root-causing the `task_usage` schema-drift
  `/done` outage (same day, unrelated root cause, but the SAME stuck-main-promotion PR was noticed while investigating
  why the dashboard's new auto-deploy hadn't fired for a same-day feature). Confirmed via direct reads of
  `ldr_to_main_fleet_promote.sh`, `pin_branch_protection_rulesets.py`, and `ldr-to-staging-promote.yml` (not assumed
  from doc descriptions) that the minimal-diff fix was a single new `promotion_model` value plus 2 small Python-in-YAML
  edits — no changes needed to the fleet promoter script itself, since its exact-match filter already naturally excludes
  anything that isn't literally `"ldr_main"`.
- **context-scout 2026-08-05**: populated context_scope (6 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **2026-08-06 (cicd escalation agt-bc6d06)**: dispatched to fix `ldr_qg_failure` on `agent-orchestrator#784` — verified
  it was already resolved (PR784 merged 2026-08-05T09:48:49Z, well before the 2026-08-05 16:12 `ldr_terminal` fix;
  `quality-gates-v2` on LDR confirmed green across 9+ consecutive runs since 2026-08-05T16:18:33Z, no new push since).
  While verifying, found this doc's fix has NOT fully propagated: `unified-trading-pm@main`'s manifest still shows
  agent-orchestrator as `ldr_main` (stuck behind repo-blocker `RB-04f4f852`), and the scheduled fleet-promote run keeps
  re-opening spurious agent-orchestrator promote PRs off that stale copy (`#804`, opened 2026-08-06T00:48). Logged as a
  new P2 todo above rather than fixed in-session (root cause is a different repo's qg_red blocker, out of scope for a
  one-shot ldr_qg_failure escalation).

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **`/ag-closeout-audit ao` 2026-08-06 (autonomous)**: genuinely orphaned, all 3 open items reviewed — none extracted
  into a batch. Item 1 (LDR-triggered `quality-gates-v2` template extension) is **CONFLICT-GATED**: it targets the same
  files (`quality-gates-v2.yml.tmpl`, `rollout-workflow-templates.sh`) as
  `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 18 ("update the template sources... so any FUTURE repo's
  render is correct out of the box"), a large, actively-shipping plan created the same day — not resolvable from
  evidence alone whether todo 18 already covers a `ci_trigger_branch`-style parameterization or is a narrower fix;
  drafting a competing todo here risks colliding with in-flight work. Item 2 is explicitly `[OPERATOR]`-tagged
  stretch/not-needed-today. Item 3 (propagation-lag fix) is blocked on a separate repo's `RB-04f4f852` qg_red blocker —
  time/dependency-gated, not directly actionable here. Parked, not silently dropped.
