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
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [admin, engineer]
tags: [agent-orchestrator, ci-cd, promotion-model, ldr-terminal, ci-cost, big-finding]
related:
  [
    /plans/archive/2026_08/task_usage_schema_drift_done_outage_2026_08_05.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
created: 2026-08-05
author: ikennaigboaka [interactive session]
parent_epic: orchestrator_master
priority: P2
assigned_vm: NA
execution_scope: local-only
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
- [ ] [INFRA] P2. Add a genuine LDR-triggered `quality-gates-v2` run for `ldr_terminal` repos (currently just
      agent-orchestrator), via a template extension (new manifest field, e.g. `ci_trigger_branch`, threaded through
      `quality-gates-v2.yml.tmpl` + `rollout-workflow-templates.sh`, defaulting to `main` for every other repo so
      nothing else changes). Done when: agent-orchestrator has a real, CI-server-enforced quality gate again, running on
      LDR pushes instead of a main-promotion PR that no longer exists for this repo.
- [ ] [OPERATOR] P3 (stretch, only if agent-orchestrator ever needs a real tagged release). Design a
      `ldr_terminal`-aware retarget of `semver-agent.yml.tmpl` — genuinely non-trivial (943 lines, ~20+ hardcoded `main`
      references, 2 cited past incidents from similar retargeting mistakes). Not needed today since nothing consumes
      agent-orchestrator's version number.
- [ ] [INFRA] P2. Fix propagation lag: `unified-trading-pm`'s own `main` branch still reads
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
      downstream finding, out of scope for that one-shot fix.

## Progress Log

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
