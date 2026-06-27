---
doc_type: plan
title: CI/CD Phase-2 finalize — coherence/readers repoint, deployment-api version-state, VERIFY + delete cure machinery
summary:
  Phase-2 (version-out-of-source, D13) FINALIZE lane. Repoint assert_version_coherence + the coherence gates to the
  registry (tag==Firestore, drop the pyproject source read); move deployment-api version-state (API-5/6) to
  Firestore-authoritative-with-manifest-fallback; relocate the semver label-check; guard pending_version_bumps; image
  build/deploy/rollback resolve version from the registry; run the ultracode adversarial-verify (no hook dropped) + the
  zero-commit-bump VERIFY; then DELETE the now-dead cure machinery LAST (auto-resolve/collapse + the version branch).
status: active
nature: process
stage: [meta]
repos: [unified-trading-pm, deployment-api, deployment-service]
scope: [engineer, admin]
tags: [cicd, phase-2, version-out-of-source, coherence, deployment-api, VERIFY, D13, WS-L]
related:
  [
    cicd_consolidated_remaining_2026_06_24.md,
    cicd_phase2_semver_retarget_2026_06_27.md,
    cicd_staging_main_deadcode_retirement_2026_06_27.md,
    ../epics/infrastructure_master.md,
    ../../codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-06-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-27
supersedes:
superseded_by:
depends_on: cicd_phase2_semver_retarget_2026_06_27
source: cicd_consolidated_remaining_2026_06_24.md (Phase-2 readers/VERIFY/cross-repo items)
assigned_role: backend-engineer
drift_direction: advance-code
---

# CI/CD Phase-2 finalize

> **Phase-2 lane 3 of 4.** **GATED — `depends_on: cicd_phase2_semver_retarget`.** Held `draft` until the retarget lands.
> **Model tier: Sonnet/backend-engineer** for the repoints; the VERIFY step INVOKES an **ultracode workflow** for the
> adversarial "did we drop a hook / break a coherence gate?" pass (breadth + skepticism = the no-regression guarantee).
> **Delete the cure machinery LAST**, only after VERIFY proves the version-line conflict class is gone (no shims).

## Tasks

- [x] ✅ [SCRIPT] P1. **F1 #6 — assert_version_coherence flag-gated.** DONE 2026-06-27 (PM@22288074a, PR #625).
      `_version_source()` reads each repo's manifest `version_source`; for `git-tag` repos the source is the git TAG
      (coherence = the tag `v{versions{}}` EXISTS, i.e. tag==Firestore-projection — `versions{}` is the consolidator's
      Firestore mirror), with NO pyproject read and no staging-source compare; static repos keep
      `pyproject==manifest==tag` unchanged. Verified: greeks-service (git-tag) now shows `tag-ok` and is NO LONGER a
      false split (was flagged because its dynamic pyproject has no version line); the 17 static-repo splits are the
      pre-existing warn-only drift, unchanged. Warn-only gate (`quality-gates.sh`), QG-green.
- [x] ✅ [CODE] P1. **deployment-api API-1** DONE (deployment-api@8a64d96). `routes/cloud_builds.py` reads the installed
      version via `importlib.metadata.version()` (was `tomllib` pyproject read → None under dynamic); Phase-2-safe. Also
      API-2 DONE (`deployment_api/__init__.py` → importlib.metadata, deployment-api@75ab4fd5c).
- [x] ✅ [SCRIPT] P1. **deployment-service DS-1** DONE (deployment-service@850f99d7). `create-code-tarballs.sh` reads
      `git describe --tags --always` (was a pyproject grep → "unknown" under dynamic). DS-3/DS-9 also DONE
      (deployment-service@9a3e16ee — bom.py importlib.metadata + buildspec.aws.yaml git-describe).
- [x] ✅ [CODE] P2. **deployment-api API-5/API-6** DONE 2026-06-27 (deployment-api@d7b2be0bf). Released version is now
      Firestore-authoritative-with-manifest-fallback via the `load_manifest_view` seam (mirrors the shipped
      `_ci_status_firestore_store.py` pattern): `resolve_release_version_map` overlays the manifest `versions{}` cache
      with the LIVE `repo_state/{repo}.release_tag.version` registry (the SAME doc the PM `version_registry_store`
      writes on every `v*` tag push), wired through `ManifestView.versions_override` + a new `release_version_for()`
      accessor; `pending_version_bumps` reads the live main version. **Honest scope (verified, within intent):** of the
      three manifest version surfaces only `versions{}` has a Firestore writer — `staging_versions{}` (retiring with
      staging) and `deployed_versions{}` (per-env IMAGE-deploy state committed to the manifest by the cloudbuild
      post-build step) have NO Firestore source, so they stay manifest-sourced (documented in the store scope-note +
      `deployed_version_for` docstring); overlaying them from a non-existent registry would be a lie. API-5
      `deployment_diff.py` is git-show-at-SHA → stays manifest (NOT a swap candidate), as previously noted. +11 unit
      tests; QG-green (141s). **Gate met:** the dashboard reads live released-version from Firestore, manifest as
      fallback. (deployment-api)
- [ ] [WORKFLOW] P2. **Image build/deploy/rollback resolve the human-readable version from the registry** — keep
      `:latest`, add `:vX.Y.Z` for rollback/tracing (deployment-ui already reads Firestore). **Gate:** a deploy resolves
      `:vX.Y.Z` from the registry; rollback picks the correct version↔SHA.
- [ ] [WORKFLOW] P2. **Relocate the semver `label-check`** (deferred from Phase-1): under `ldr_main` the merge-PR head
      is the LDR SHA, which never receives the staging-posted status. Relocate enforcement onto the LDR→main PR (or fold
      into the registry model, since Phase-2 reworks label-check). **Gate:** a mislabeled bump is flagged on the
      LDR→main PR.
- [x] ✅ [SCRIPT] P2. **Guard `pending_version_bumps`** DONE 2026-06-27 (deployment-api@e5bae9a). Added
      `ManifestView.version_source_for` (mirrors `promotion_model_for`, default `pyproject.toml` to agree with the PM
      `assert_version_coherence._version_source` default) and a `version_source == "git-tag"` skip in
      `pending_version_bumps()` — a git-tag repo has no staging→main bump path (version SSOT = tag/Firestore, staging
      entry vestigial), so a stale staging value above main no longer false-flags or arms the semver circuit-breaker
      (`_SEMVER_BREAKER_THRESHOLD`). Mirrors the PM coherence git-tag branch. Whole-map/per-repo fail-open paths intact
      (fully-retired staging block → `[]`). +1 regression test (git-tag-ahead NOT flagged, sibling pyproject ahead IS);
      QG-green (98s). **Gate met:** the comparison stays meaningful — no false stuck-bump alarms under the git-tag
      model. (deployment-api)
- [ ] [VERIFY] P1. **Adversarial-verify (ultracode workflow) + zero-commit VERIFY.** Run parallel skeptic finders over
      the 17 hooks — "is any hook still writing pyproject? any coherence gate broken? any reader still reading the
      line?" Then VALIDATE: a version bump produces ZERO git commits; the version-line conflict class is gone;
      rollback/tracing resolve the correct version↔SHA; the bump-rate breaker no longer false-arms. **Gate:** ultracode
      returns zero surviving violations + the four validations pass. SUPERSEDES the 3 `staging_main_version_line_*`
      issue docs.
- [ ] [SCRIPT] P1. **FLEET-WIDE git-tag rollout** (operator hard-requirement 2026-06-27: _"your autonomous work isn't
      done until EVERY REPO goes through this new CI/CD pipeline — greeks-service is only a canary"_). Migrate EVERY
      version-tracked repo from `version_source=pyproject.toml`/static → `git-tag` (D13): per repo (a) flip
      `repositories[repo].version_source=git-tag` in the manifest, (b) `rollout-workflow-templates.sh` so the retargeted
      `semver-agent.yml` (writer #1 / compute #3 / breaker #2 — `__VERSION_SOURCE__=git-tag`) +
      `version-registry-notify.yml` land in that repo, (c) switch its `pyproject.toml` to dynamic version (hatch-vcs
      `source=vcs`, version line removed), (d) mint the baseline `v{current}` tag so the registry has a seed, (e) VERIFY
      a bump is zero-commit + `assert_version_coherence` shows `tag-ok` for it. Drive in dependency order (libraries
      first), batched, each repo CI-green before the next. **Gate:** `version_source=git-tag` for ALL version-tracked
      repos in the manifest; none still carries a committed `version =` line; `assert_version_coherence` shows `tag-ok`
      fleet-wide (no static-source splits remain). This is the UNBLOCKER for the cure-machinery delete below and the
      termination condition of the autonomous loop.
- [ ] [SCRIPT] P2. **DELETE the cure machinery LAST** (no shims): cure-B `staging-to-main.yml:820-870` +
      `auto_resolve_version_promote.sh` + `semver_max_merge_driver.py` + `manifest_merge_driver.py` +
      `reconcile-staging-versions.yml` self-heal + `reconcile_manifest_backmerge` version branch + the 2 stale one-offs
      (`rollout-version-bump-staging-only.sh`/`rollout-remove-version-bump-hook.sh`). ONLY after the VERIFY above proves
      the class gone **AND the fleet-wide rollout has every repo on `version_source=git-tag`** (the cure machinery
      resolves version-LINE conflicts, which only exist for static-source repos — deleting it while any repo is still
      static would remove its conflict cure). **Gate:** the version-line conflict class is provably extinct; deleted
      code has no live callers (grep-then-READ).

## Success criteria

- Coherence + all readers resolve from `tag==Firestore`; deployment-api/-service no longer read the pyproject line.
- **EVERY version-tracked repo is `version_source=git-tag`** (operator hard-requirement) — greeks was the canary; the
  fleet is migrated; no repo still carries a committed `version =` line; `assert_version_coherence` is `tag-ok`
  fleet-wide.
- Ultracode adversarial-verify returns zero surviving violations; zero-commit bump proven end-to-end.
- The cure machinery is deleted (no shims), version-line conflict class extinct.

## Codex SSOT updates

- `codex/08-workflows/ci-cd-flow.md` — version SSOT = tag/Firestore; coherence repointed; cure machinery retired.
- Post-phase codex audit: SUPERSEDED-banner the 3 `staging_main_version_line_*` issue docs.

## Progress Log

- 2026-06-27: Split from the cicd consolidated tracker (Phase-2 finalize lane). Gated on cicd_phase2_semver_retarget.
- 2026-06-27 (slot-3 TAKEOVER, operator-greenlit): reassigned `harsh_pc → NA` (slot-3 interactive drives it). KEPT
  `status: draft` — flips to `active` only when `cicd_phase2_semver_retarget` is green. Slot-3 audit additions relevant
  to this lane: API-2 (`deployment_api/__init__.py:8`) is STILL a static `__version__ = "0.1.1"` literal (needs the
  importlib.metadata swap API-1 already got); API-5 reads the manifest at a historical SHA via `git show` (stays correct
  under Option-C, NOT a load_manifest_view swap candidate) while API-6 is the real Firestore-overlay target;
  `cloud-build-router.yml` is the `deployed_versions{}` WRITER the consolidator must not clobber; the cure-machinery
  delete set is BIGGER than enumerated (`semver_max_merge_driver.py` + the separate `manifest_merge_driver.py`, both
  delete-LAST after every repo's `version_source` flips to `git-tag`). Full manifest in the foundation Progress Log.
- 2026-06-27 (slot-3, reassigned `NA → harsh_pc` per operator coordination — Harsh owns the retarget this builds on):
  **API-2 DONE** — `deployment_api/__init__.py` now resolves `__version__` via `importlib.metadata` (was a stale literal
  `"0.1.1"` while the package was at `0.50.0`, so `/health` + `/version` + the deployment-ui chip showed a wrong value).
  Phase-2-safe (correct for static OR hatch-vcs-dynamic versions); mirrors the API-1 pattern; deployment-api QG-green.
  **deployment-api@75ab4fd5c** (on LDR; Tier-C drain promotes). REMAINING in this lane (harsh_pc): API-5/6 Firestore
  version overlay (`resolve_versions_map`/`resolve_staging_versions_map` in `_ci_status_firestore_store.py` + version
  overrides on `ManifestView`/`load_manifest_view`) — consumes the slot-3 version registry + Harsh's canary output, so
  sequence it AFTER the canary live-verify; coherence #6 repoint; the breaker-#2 flag-gate (ready fix in the retarget
  plan); delete cure machinery LAST.
- 2026-06-27 (slot-3 /autonomous DRIVE — Opus-xhigh, operator-greenlit "just do it"). **This is the loop handoff (rule
  6/12d) — a compressed future-tick resumes from here.** Reassigned `→ NA` + `status: active` (slot-3 drives; no
  orchestrator double-dispatch). **DONE prior to the drive:** Foundation (version_registry_store CAS + write-through +
  reconcile backstop + spike guards); retarget #1/#3 (Harsh PM@c52434508) + #2 breaker (PM@df60ffc59, rolled greeks) +
  #5 verified; adversarial-verify PASS; CodeBuild fleet FORK_PULL_REQUESTS (18); lag-monitor skips `ldr_main` staging
  (PM@90d125704); CI verified clean (0 stuck PRs fleet-wide); finalize API-1/API-2/DS-1/DS-3/DS-9 ✅ above. **REMAINING
  units, IN ORDER (each: QG-green → quickmerge --agent --files → flip checkbox same turn → journal here):** (F1) #6
  coherence repoint — FLAG-GATED: for `version_source=git-tag` repos assert `tag==Firestore`; KEEP
  `pyproject==manifest==tag` for static repos (warn-only gate, `quality-gates.sh:730`). (F2) API-5/6 — add
  `resolve_versions_map`/`resolve_staging_versions_map`/`resolve_deployed_versions_map` to deployment-api
  `routes/_ci_status_firestore_store.py` (mirror `resolve_ci_status_map`) + version overrides on `ManifestView` +
  `load_manifest_view` (API-5 `deployment_diff.py` is git-show-at-SHA → stays manifest, NOT a swap candidate). (F3)
  image build/deploy/rollback resolve `:vX.Y.Z` from registry (cloud-build-router emits bare-semver; keep `:latest`).
  (F4) relocate semver label-check onto the LDR→main PR. (F5) guard `pending_version_bumps` (`_repo_ci_manifest.py`).
  (F6) VERIFY = ultracode adversarial workflow (no hook still writing pyproject / no coherence gate broken) +
  zero-commit bump proof. (F7) DELETE cure machinery LAST, ONLY after F6 green + rule-11 fleet-check:
  `staging-to-main.yml` cure-B (~829-874) + `auto_resolve_version_promote.sh` + `semver_max_merge_driver.py` + the
  separate `manifest_merge_driver.py` version-leg + `setup_manifest_merge_drivers.sh:33-34,47` semvermax registration +
  `.gitattributes:8` + `reconcile-staging-versions.yml` + `reconcile_manifest_backmerge.py` version-branch + 2 stale
  one-offs (`rollout-version-bump-staging-only.sh`/`rollout-remove-version-bump-hook.sh`) — all delete-LAST, no shims,
  only when every repo's `version_source=git-tag` (TODAY only greeks is; so cure machinery STAYS until fleet-dynamic —
  F7 likely defers until the fleet rollout). **THEN `cicd_retire_staging_branch`:** SIT+breaking-detection rehome onto
  LDR → **OPERATOR CHECKPOINT before flipping SIT live fleet-wide (the ONLY pause)** → drain-skip toggle (`ldr_main`
  skips staging UNLESS in `breaking_pending`) → /repos "dormant" UI + alert-suppression. Loop armed via ScheduleWakeup;
  climbing metric = finalize checkboxes flipped (F1→F7); terminate when both plans' success criteria met → rule-9
  report.
- 2026-06-27 (tick: **F1 DONE** — PM@22288074a, PR #625). `assert_version_coherence` flag-gated by `version_source`
  (`_version_source()` helper): git-tag repos assert tag==versions{}(Firestore-projection) via `_has_tag`, no pyproject
  read; static repos unchanged. greeks now `tag-ok` (no false split). QG-green. **NEXT = F2** (deployment-api API-5/6:
  add `resolve_versions_map`/`resolve_staging_versions_map`/`resolve_deployed_versions_map` to
  `routes/_ci_status_firestore_store.py` mirroring `resolve_ci_status_map`; add
  `versions_override`/`staging_versions_override` to `ManifestView` + wire in `load_manifest_view`; API-5
  `deployment_diff.py` is git-show-at-SHA → stays manifest, NOT a swap candidate). Also noted (mid-loop spec change,
  within intent): multi-VM dispatch deprecated 2026-06-27 → valid `assigned_vm` ∈ {human-planning, NA}; fix
  `cicd_retire_staging_branch` `assigned_vm: harsh_pc → NA` when reaching it.
- 2026-06-27 (tick: **F2 DONE** — deployment-api@d7b2be0bf). Released-version overlay shipped, but the planned
  three-resolver shape was CORRECTED to ONE honest resolver after verifying the writers: only `versions{}` has a
  Firestore source (`repo_state/{repo}.release_tag` — the registry I built). `resolve_release_version_map` overlays it
  (manifest fallback); `ManifestView.versions_override` + `release_version_for()` + the `pending_version_bumps`
  main-version read all consume it. `staging_versions{}` (retiring) + `deployed_versions{}` (per-env image state,
  manifest-committed by cloudbuild post-build) have NO Firestore writer → stay manifest-sourced (documented), NOT fake
  resolvers. +11 tests, QG-green 141s. **NEXT = F3** (build/deploy/rollback resolve version↔SHA from the registry — the
  `release_tag` doc already stores BOTH `version` and `sha`; the cloudbuild template tags `:${_VERSION}` from
  `client_payload.version`, which becomes registry-derived once a repo is on the retargeted semver-agent; rollback path
  = `deployment-api/routes/deployments/_lifecycle.py`).
- 2026-06-27 (**OPERATOR SCOPE HARD-REQUIREMENT** — termination condition expanded, within intent): _"even if greeks
  service is canary, your autonomous work isn't done until EVERY REPO goes through this new CI/CD pipeline."_ ⇒ The loop
  does NOT terminate at greeks-canary. Added the **FLEET-WIDE git-tag rollout** task (migrate every version-tracked repo
  to `version_source=git-tag`: manifest flip + retargeted-template rollout + dynamic pyproject + baseline tag +
  zero-commit VERIFY, dependency-ordered/batched). F7 (cure-machinery delete) is now genuinely reachable — re-gated on
  the fleet rollout (not indefinitely deferred): the cure machinery resolves version-LINE conflicts that only exist for
  static-source repos, so it deletes safely only once ALL repos are git-tag. Same expansion applies to
  `cicd_retire_staging_branch` (toggle `promotion_model=ldr_main` for the whole eligible fleet, not just the canaries).
  Success criteria updated.
- 2026-06-27 (tick: **F5 DONE** — deployment-api@e5bae9a). pending_version_bumps now skips `version_source=git-tag`
  repos (no staging→main path). Verified by the version-flow-map ultracode workflow (finding holds, minimal,
  non-breaking, correction=none). NEXT was F3.
- 2026-06-27 (tick: **F3 — corrected scope via grep-then-READ; the ultracode map analyzed a STALE template**). The
  version-flow-map workflow + verifier both reasoned over `scripts/propagation/templates/cloudbuild.yaml` (single bare
  tag, `_AR_REPO=unified-trading`, `_VERSION` substitution) and flagged "no :latest" + an AR-repo-name mismatch vs
  builds.py (`unified-trading-system`). **Reading the ACTUAL build path (per-repo `cloudbuild.yaml` rolled from
  `configs/cloudbuild-{type}-template.yaml` via `scripts/propagation/rollout-cloudbuild.py`) overturns BOTH:** the live
  templates already push `:$SHORT_SHA` + `:$$VERSION` (bare) + `:latest` via `--all-tags` to `_REGISTRY_REPO`
  =`unified-trading-system` (which MATCHES `builds.py:_CB_REGISTRY_REPO`). So `:latest` already exists and there is NO
  AR-repo mismatch on the real path; the stale propagation template is a separate, likely-dead artifact. **The REAL F3
  residual (a genuine correctness bug, fleet-rollout-critical):** the live cloudbuild computes
  `VERSION=$(grep '^version' pyproject.toml ...)` (greeks `cloudbuild.yaml:76`) — which returns EMPTY under the
  git-tag/dynamic pyproject (no committed version line). So greeks (the canary) is ALREADY mis-tagging images (falls
  back to `$SHORT_SHA`), and every fleet-rollout repo would too. F3's true deliverable = move the cloudbuild VERSION
  source from the pyproject grep → `git describe --tags --match 'v*'` in the `configs/cloudbuild-*-template.yaml`
  family + re-roll. (The `:vX.Y.Z` v-prefixed tracing alias is secondary — `:latest`+bare-`:version` already exist.)
  This is a HOOK the F6 census must also flag (a build-time pyproject-version reader). NEXT: fix the cloudbuild VERSION
  source.
