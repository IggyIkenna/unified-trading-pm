---
doc_type: plan
title: CI/CD Phase-2 semver-agent retarget — version writer moves from pyproject-commit to git-tag+registry (17 hooks)
summary: Phase-2 (version-out-of-source, D13) RETARGET lane — the high-blast-radius core. Repoint the semver-agent so it mints a git tag + registry event INSTEAD of committing pyproject.toml; retarget the compute-next (CURRENT from latest tag, baseline from tag SHA) + the bump-rate circuit breaker (count tag/registry events, not chore(release) commits); stop the PM self-bump pyproject write. The fleet SSOT `.tmpl` is the primary writer, so editing it triggers a fleet rollout behind the canary flag. HIGH RISK — Opus-xhigh single-agent + an ultracode adversarial-verify in the finalize lane.
status: active
nature: process
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cicd, phase-2, version-out-of-source, semver-agent, D13, WS-L, high-blast-radius]
related: [cicd_consolidated_remaining_2026_06_24.md, cicd_phase2_foundation_2026_06_27.md, cicd_phase2_finalize_2026_06_27.md, ../epics/infrastructure_master.md, ../../codex/08-workflows/ci-cd-flow.md]
created: 2026-06-27
parent_epic: infrastructure_master
assigned_vm: NA
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
assigned_role: backend-engineer
drift_direction: advance-code
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

- [x] ✅ [SCRIPT] P1. **#1 — the writer.** DONE 2026-06-27 (harsh_pc, PM@c52434508). `semver-agent.yml.tmpl` apply-step
      flag-gates on `__VERSION_SOURCE__`: for `git-tag` repos it mints an annotated `vX.Y.Z` tag (no pyproject write, no
      `chore(release)` commit) and pushes via the PAT'd `origin` so `version-registry-notify` fires; legacy `sed`+commit
      for static repos. Rolled to greeks-service (canary). Integrates with the slot-3 foundation
      (tag→notify→`version_registry_store` CAS→Firestore).
- [x] ✅ [SCRIPT] P1. **#3 — compute-next.** DONE 2026-06-27 (harsh_pc, PM@c52434508). For `git-tag` repos CURRENT comes
      from `git describe --tags --abbrev=0 --match 'v*'` and baseline-SHA from the tag's commit (not the pyproject grep
      / commit-message grep); legacy pyproject read for static repos.
- [x] ✅ [SCRIPT] P1. **#2 — bump-rate circuit breaker.** DONE 2026-06-27 (slot-3 takeover, PM@df60ffc59 / PR #620).
      Flag-gated: for `version_source=git-tag` repos it counts `v*` TAG mints in the last hour
      (`git for-each-ref ... creatordate:unix`) instead of `chore(release)` COMMITS — which are 0 for a dynamic repo, so
      without this the breaker went INERT (ordering hazard #3). The trip thresholds (pairs≥2 / consec≥3 / rate≥6) are
      PRESERVED; the >=6/hr backstop carries runaway protection (the adjacent-pair signature doesn't apply to tags).
      Inert for static repos. Scratch-simulated (counts tags in window) + rolled to greeks-service.
- [ ] [SCRIPT] P1. **#4 — PM self-bump** (`update-repo-version.yml:226-271`): stop writing pyproject + re-locking
      uv.lock; PM version becomes dynamic-from-tag like the fleet. **Gate:** a PM bump produces zero pyproject/uv.lock
      churn. NOTE (slot-3): DEFERRED until PM itself flips to `version_source=git-tag` — PM is still static, so this is
      not on the canary's critical path.
- [x] ✅ [SCRIPT] P2. **#5 — resolvability gate.** DONE-BY-VERIFICATION 2026-06-27 (slot-3): NO change needed. The
      gate's `check_resolvable()` (`update-repo-version.yml:517-538`) checks the **tag-leg FIRST**
      (`git/ref/tags/v$VERSION` → 200 → resolvable); since #1's writer now mints that tag before dispatch, a `git-tag`
      repo resolves via the tag-leg, and the branch-pyproject leg (b) remains the static-repo fallback. Only the stale
      comment at :472-473 ("NO workflow creates release tags today") should be refreshed (cosmetic).
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
- 2026-06-27 (slot-3 TAKEOVER, operator-greenlit): reassigned `harsh_pc → NA` (slot-3 interactive drives it). KEPT
  `status: draft` per this plan's own gating note (line 46) — flips to `active` only when `cicd_phase2_foundation` is
  green (registry write-path + dynamic-versioning canary). The 17-hook manifest is REFRESHED + EXPANDED by the slot-3
  no-regression audit: **+5 hooks** (`manifest_merge_driver.py`, `request-major-bump.yml` ×2 templates,
  `staging-to-main.yml` version_delta loop, `cloud-build-router.yml` deployed_versions writer,
  `check-precommit-versions.py` dormant trap), **4 corrections** (#11-b semvermax deletion footprint =
  `setup_manifest_merge_drivers.sh:33-34,47` + `auto_resolve_version_promote.sh:25,37-39` + `.gitattributes:8`; #14
  blast-radius is fleet-rollout not pm-only via 2 templates; #16 under-classifies the separate
  `manifest_merge_driver.py`; API-3 regex OK for bare-semver — confirmed by `cloud-build-router.yml`), and the **7
  ordering hazards** are the no-regression critical path. Full detail in `cicd_phase2_foundation_2026_06_27.md` Progress
  Log + the consolidated tracker.
- 2026-06-27 (slot-3 → harsh_pc HANDOFF, operator-coordinated): **harsh_pc (Harsh) is the ACTIVE owner of this lane** —
  reassigned back `NA → harsh_pc`. Harsh shipped the writer (#1) + compute (#3, `git describe` CURRENT + tag
  baseline-SHA)
  - the greeks-service canary flip (pyproject → dynamic + `version_source=git-tag`) in **PM@c52434508**
    (`__VERSION_SOURCE__` flag-gate). This INTEGRATES with the slot-3 foundation: greeks has the rolled
    `version-registry-notify.yml`, and the writer pushes the tag via the PAT'd `origin`, so
    `tag → notify → version-registry-update → version_registry_store (CAS) → Firestore` is wired end-to-end. Slot-3's
    parallel `.tmpl` edit was redundant and was dropped (never pushed; no fleet impact). **⚠️ OPEN GAP for harsh_pc —
    breaker (#2) is NOT flag-gated (ordering hazard #3, "breaker goes inert"):** the bump-rate circuit breaker still
    counts `chore(release)` COMMITS unconditionally, but a `version_source=git-tag` repo (greeks) produces NONE → all
    three counters read 0 → the breaker is INERT → runaway-tag protection is silently lost on the canary. **Ready fix
    (slot-3-simulated, drop into the breaker step after the REBUMP_PAIRS loop, before the `Pending-bump scan` echo):**
  ```bash
  VERSION_SOURCE="__VERSION_SOURCE__"
  if [ "$VERSION_SOURCE" = "git-tag" ]; then
    git fetch origin --tags --quiet 2>/dev/null || true
    NOW_EPOCH=$(date +%s)
    RECENT_BUMPS=$(git for-each-ref --format='%(creatordate:unix)' 'refs/tags/v[0-9]*' 2>/dev/null \
      | awk -v n="$NOW_EPOCH" '($1 != "" && $1 > n - 3600)' | wc -l | tr -d ' ')
    RECENT_BUMPS="${RECENT_BUMPS:-0}"
    echo "Dynamic repo: counted ${RECENT_BUMPS} v* tag mint(s) in the last hour (commit-pair signature N/A)."
  fi
  ```
  This re-derives the rate from `v*` tag mints (the dynamic bump event); the >=6/hr trip backstop then carries runaway
  protection. CONSECUTIVE/REBUMP_PAIRS stay 0 (the commit-pair signature doesn't apply to tags). Verified in a scratch
  repo: counts tags in the window correctly; inert for static repos. (slot-3 audit ordering-hazard #3.)
- 2026-06-27 (slot-3 TAKEOVER #2, operator-directed — Harsh paused): reassigned `harsh_pc → NA`, `status → active`
  (foundation green; #1/#2/#3/#5 done; canary wired). **Breaker #2 SHIPPED** (PM@df60ffc59 / PR #620) + rolled to
  greeks-service (canary copy now has the breaker dynamic branch + the writer/compute flag-gate; greeks QG-green). #1/#3
  were Harsh's (PM@c52434508); #5 verified no-change-needed (tag-leg covers); **#4 deferred** (PM still static), **#13
  deferred** (MAJOR bumps rare + 1.0.0 is a human hard-stop). **REMAINING in this lane:** the live canary verify (a
  greeks bump → tag → notify → Firestore, zero commits) + the fleet rollout of the breaker fix to the other repos (inert
  for static, but keeps the .tmpl↔copies in sync). Then the finalize lane.
