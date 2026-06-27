---
doc_type: plan
title: "CI/CD Phase-2 semver-agent retarget — version writer moves from pyproject-commit to git-tag+registry (17 hooks)"
summary: >-
  Phase-2 (version-out-of-source, D13) RETARGET lane — the high-blast-radius core. Repoint the semver-agent so it mints
  a git tag + registry event INSTEAD of committing pyproject.toml; retarget the compute-next (CURRENT from latest tag,
  baseline from tag SHA) + the bump-rate circuit breaker (count tag/registry events, not chore(release) commits); stop
  the PM self-bump pyproject write. The fleet SSOT `.tmpl` is the primary writer, so editing it triggers a fleet rollout
  behind the canary flag. HIGH RISK — Opus-xhigh single-agent + an ultracode adversarial-verify in the finalize lane.
status: draft
nature: infra
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cicd, phase-2, version-out-of-source, semver-agent, D13, WS-L, high-blast-radius]
related:
  [
    cicd_consolidated_remaining_2026_06_24.md,
    cicd_phase2_foundation_2026_06_27.md,
    cicd_phase2_finalize_2026_06_27.md,
    ../epics/infrastructure_master.md,
    ../../codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-06-27
parent_epic: infrastructure_master
assigned_vm: harsh_pc
assigned_role: backend-engineer
drift_direction: advance-code
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
depends_on: cicd_phase2_foundation_2026_06_27
source: cicd_consolidated_remaining_2026_06_24.md (Phase-2 17-hook audit, lines ~1196-1234)
---

# CI/CD Phase-2 semver-agent retarget

> **Phase-2 lane 2 of 4** (the hard one). **GATED — `depends_on: cicd_phase2_foundation`** (the registry write-path +
> dynamic-versioning canary must be green first). Held `draft` until foundation lands, then operator flips to `active`.
>
> **⚠️ MODEL TIER: OPUS 4.x extra-high (xhigh), single-agent — NOT Sonnet.** This is high-blast-radius spec'd execution
> (17 hooks, fleet `.tmpl` rollout). The model-gate self-check is a HARD RULE: if the executing agent is on Sonnet, it
> MUST STOP and escalate. xhigh buys regression-avoiding care, not novel design (architecture is decided, D13).
>
> The authoritative 17-hook no-regression manifest lives in the consolidated tracker
> `cicd_consolidated_remaining_2026_06_24.md` (HIGH/MED/LOW table). Follow the **risk-ranked retarget order** there.

## Tasks

- [ ] [SCRIPT] P1. **#1 — the writer.** `scripts/workflow-templates/semver-agent.yml.tmpl` apply-step (`.tmpl:639-680`):
      replace `sed -i pyproject` + `chore(release):` commit + push-to-staging with **mint `vX.Y.Z` tag +
      registry/Firestore event** (no pyproject write, no commit). This is a fleet rollout via
      `rollout-workflow-templates.sh` (rollout done only when every per-repo copy is committed + pushed). **Gate:** a
      bump on a canary repo mints the tag + registry event, produces ZERO commits; de-conflict with
      `reconcile_release_tags.py` (#9) so no double-mint.
- [ ] [SCRIPT] P1. **#3 — compute-next** (`semver-agent.yml:171-468`): read CURRENT from the latest `v*` tag (not
      pyproject `version =`) and baseline-SHA from the tag's SHA (not the commit-message grep). **Gate:** compute-next
      returns the correct next version against a tagged repo with no pyproject version line.
- [ ] [SCRIPT] P1. **#2 — bump-rate circuit breaker** (`semver-agent.yml:104-169`): count tag/registry events instead of
      `chore(release):` COMMITS; PRESERVE the pairs≥2 / consec≥3 / rate thresholds or the runaway class re-opens.
      **Gate:** the breaker still arms on a synthetic runaway (event-counted), no false-arm on normal cadence.
- [ ] [SCRIPT] P1. **#4 — PM self-bump** (`update-repo-version.yml:226-271`): stop writing pyproject + re-locking
      uv.lock; PM version becomes dynamic-from-tag like the fleet. **Gate:** a PM bump produces zero pyproject/uv.lock
      churn.
- [ ] [SCRIPT] P2. **#5 — manifest bookkeeping + resolvability gate** (`update-repo-version.yml:97-205,457`): the
      branch-pyproject leg dies; the tag leg must cover resolvability. **Gate:** the resolvability gate passes reading
      the tag, not the branch pyproject.
- [ ] [SCRIPT] P2. **#13 — major-bump handler** (`major-bump-issue-handler.yml:146-189` +2 template copies):
      approved-MAJOR mints a MAJOR tag instead of writing the line. **Gate:** an approved major-bump issue mints
      `vN.0.0`. NOTE: the 1.0.0 graduation ITSELF stays a human hard-stop — this only wires the mechanism.

## Success criteria

- The semver-agent mints tags + registry events; ZERO pyproject/version-line commits fleet-wide (behind the canary flag,
  then rolled out).
- compute-next + bump-rate breaker operate off tags/events with thresholds preserved.
- `rollout-workflow-templates.sh` rollout complete (every per-repo `.tmpl` copy committed + pushed).

## Codex SSOT updates

- `codex/08-workflows/ci-cd-flow.md` — semver-agent now tag/registry-driven; document the writer move + the de-conflict
  with `reconcile_release_tags.py`.

## Progress Log

- 2026-06-27: Split from the cicd consolidated tracker (Phase-2 retarget lane). Opus-xhigh; gated on
  cicd_phase2_foundation. The ultracode adversarial-verify ("no hook dropped / no coherence gate broken") runs in the
  finalize lane.
