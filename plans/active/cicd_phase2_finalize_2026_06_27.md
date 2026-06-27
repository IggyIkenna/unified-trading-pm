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
asset_group: cross-asset
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
- [x] ✅ [WORKFLOW] P2. **Image build/deploy/rollback resolve the version from the registry** DONE 2026-06-27 (PM
      template @dc03bef18 + greeks re-roll @55c2f3b). **Substantive gate MET.** The real fix (found by grep-then-READing
      the LIVE build path, not the stale `propagation/templates/cloudbuild.yaml` the ultracode map analyzed): the
      `configs/cloudbuild-service-template.yaml` `extract-version` step now resolves VERSION from the git TAG
      (`git describe --match 'v*'` → highest v-tag ref → pyproject → short-sha) instead of a pyproject grep that returns
      EMPTY under the dynamic/git-tag model. Backward-compatible for static repos (nearest v-tag == pyproject version by
      coherence); FIXES git-tag repos (greeks was mis-tagging images to short-sha). Re-rolled to greeks via
      `rollout-cloudbuild.py` (remaining service repos re-roll in their fleet-rollout migration commit — backward-compat
      so no urgency). The service template already pushed `:latest` + bare `:$VERSION` + `:$SHORT_SHA` to
      `_REGISTRY_REPO=unified-trading-system` (which matches `builds.py:_CB_REGISTRY_REPO` — so the ultracode-flagged
      "no :latest" + AR-repo-name mismatch were artifacts of the stale template, NOT the live path). **`:vX.Y.Z`
      v-prefixed alias DELIBERATELY NOT added** (design decision, not a deferral): the bare `:$VERSION` tag IS the
      human-readable registry version and the immutable AR tag pins it version↔SHA for both rollback paths
      (revision-based live rollback is version↔SHA-N/A by design; tag-based rollback pins by construction) — a redundant
      `:v` alias buys only git-tag-string parity while risking junk "unknown-branch" build rows in
      `builds.py:_tag_to_entry` (would need a parser change for zero functional gain). **Gate met:** a deploy resolves
      the git-tag-derived human-readable version from the registry; rollback pins the correct version↔SHA.
      (unified-trading-pm, greeks-service)
- [x] ✅ [WORKFLOW] P2. **Relocate the semver `label-check`** DONE 2026-06-27 (PM@be15cfb88). Added a label-check gate
      to `.github/workflows/ldr-to-main-promote-fleet.yml` (the PM-owned fleet promoter — NOT a template) that
      re-derives the label-vs-computed-bump verdict on the LDR head: COMPUTED from the range commit subjects
      (breaking>minor>patch) refined by the SAME AST differ (is_breaking→breaking; else new>old exports→minor); EXPECTED
      from the latest LDR subject; on mismatch it BLOCKs the promote + posts a FAILING `semver-agent/label-check` status
      on the LDR head. Faithful copy of `semver-agent.yml.tmpl` Step-4 (verdicts never diverge — adversarial-verify
      confirmed parity). Reuses the SIT part-2 differ run (one differ call). **FAIL-OPEN** on any differ/fetch/api gap
      (never jams the drain — breaking_pending + v2 stay the backstops); dry-run never mutates GitHub.
      Adversarial-verify verdict: SHIP (bash-correct, semver parity, fail-open invariant holds, no false-block). The
      deeper "fold into the registry model" (relocate the semver-agent TRIGGER off staging) belongs to the
      staging-retire SIT-rehome. **Gate met:** a mislabeled bump is flagged on the LDR→main path. (unified-trading-pm)
- [x] ✅ [SCRIPT] P2. **Guard `pending_version_bumps`** DONE 2026-06-27 (deployment-api@e5bae9a). Added
      `ManifestView.version_source_for` (mirrors `promotion_model_for`, default `pyproject.toml` to agree with the PM
      `assert_version_coherence._version_source` default) and a `version_source == "git-tag"` skip in
      `pending_version_bumps()` — a git-tag repo has no staging→main bump path (version SSOT = tag/Firestore, staging
      entry vestigial), so a stale staging value above main no longer false-flags or arms the semver circuit-breaker
      (`_SEMVER_BREAKER_THRESHOLD`). Mirrors the PM coherence git-tag branch. Whole-map/per-repo fail-open paths intact
      (fully-retired staging block → `[]`). +1 regression test (git-tag-ahead NOT flagged, sibling pyproject ahead IS);
      QG-green (98s). **Gate met:** the comparison stays meaningful — no false stuck-bump alarms under the git-tag
      model. (deployment-api)
- [x] ✅ [VERIFY] P1. **Adversarial-verify + zero-commit VERIFY DONE 2026-06-27** (ultracode workflow
      `f7-cure-machinery-deletion-safety`). **VERDICT: the version-line-conflict GENERATOR is structurally EXTINCT** —
      23/23 git-tag repos (manifest PM@00dd2ab96); 22/23 have NO committed `version =` line (zero conflict surface);
      every LIVE version path mints a tag (semver-agent git-tag branch + PM self-bump retarget); an exhaustive re-grep
      found ZERO unexpected pyproject-version writers (the only `sed` paths are the now-unreachable legacy
      `else`-branches + the cure machinery itself). So a version-line MERGE CONFLICT can no longer be generated. One
      residual: PM's pyproject kept an INERT orphan `version = "1.2.595/596"` line (the final legacy sed ran ~2 min
      before the manifest flip committed) — no live writer touches it, so it can't diverge; strip alongside F7. **F7
      GATING (re)discovered:** the cure machinery is NOT safe to delete now — it's LIVE-WIRED to `staging-to-main.yml`
      (the retained, reversible staging path) + `.gitattributes merge=semvermax`; deleting the files orphans live
      callers. ⇒ **F7 reorders AFTER the SIT-rehome** (which retires the staging-path callers) — exactly the "delete
      LAST" intent. SUPERSEDES the 3 `staging_main_version_line_*` issue docs.
- [ ] [VERIFY] P1. **(superseded by the line above — kept for the original gate text)** **Hook-census DONE 2026-06-27**
      (ultracode workflow `version-flow-map` + a dedicated Explore census). RESULT — the retarget was thorough; the only
      surviving pyproject-version WRITERS are the two KNOWN/intended ones: (1) `update-repo-version.yml:243` (PM
      self-bump #4 — `sed`s PM's own version on every fleet version-bump dispatch; retargeted when PM ITSELF migrates to
      git-tag in the fleet rollout) and (2) the cure machinery (`major-bump-issue-handler.yml`,
      `auto_collapse_lossless_promote.sh`, the two merge-drivers — delete-LAST per F7). Every other hook is confirmed
      retargeted/registry-sourced (semver-agent mints tags, reconcile_release_tags reader→tags, assert_version_coherence
      version_source-aware, sync-manifest-versions reader→manifest, cloudbuild now git-describe, quickmerge
      display-only). **So "zero surviving violations" is GATED on the fleet rollout (PM→git-tag) + F7 (cure-machinery
      delete)** — this VERIFY flips GREEN only after those. zero-commit VERIFY: provable on greeks now (git-tag, no
      pyproject line); fleet-wide after the rollout. Run parallel skeptic finders over the 17 hooks — "is any hook still
      writing pyproject? any coherence gate broken? any reader still reading the line?" Then VALIDATE: a version bump
      produces ZERO git commits; the version-line conflict class is gone; rollback/tracing resolve the correct
      version↔SHA; the bump-rate breaker no longer false-arms. **Gate:** ultracode returns zero surviving violations +
      the four validations pass. SUPERSEDES the 3 `staging_main_version_line_*` issue docs.
- [x] ✅ [SCRIPT] P1. **FLEET-WIDE git-tag rollout** DONE 2026-06-27 (operator hard-requirement). **All 23
      version-tracked Python/library repos are `version_source=git-tag` on origin/LDR** (manifest committed
      PM@00dd2ab96). Per repo: manifest flip + retargeted `semver-agent[git-tag]` + `version-registry-notify` rolled +
      pyproject→dynamic hatch-vcs + baseline `v{current}` tag minted + cloudbuild VERSION patched to git-describe.
      Tooling built for it (PM `scripts/cicd/`): `migrate_repo_to_git_tag.py` (regression/1.0.0 safety audit — caught +
      refused deployment-api/instruments/UAC version-regressions until baseline tags minted),
      `migrate_one_repo_git_tag.sh`, `patch_cloudbuild_version.py` (surgical — after a whole-file re-roll CLOBBERED 7
      repos' custom cloudbuild steps, `fix_clobbered_cloudbuild.sh` restored stage-siblings/operability-probe +
      git-describe). **Libraries (UTL, UAC)** handled surgically (custom cloudbuilds preserved; UTL builds the base
      image every service FROMs) + a publish-gate added (`cloudbuild-library-template.yaml` + per-repo twine step: only
      a clean 3-part X.Y.Z wheel publishes, never a `.devN`). UAC also needed `generate_ui_reference_data._get_version`
      repointed to importlib.metadata (was a pyproject grep → 'unknown'). **PM** (the control repo, non-package,
      self-bumping): self-bump #4 retargeted to MINT a tag in git-tag mode (no more pyproject sed — the last writer,
      F6), flipped + baseline v1.2.595, pyproject version line kept vestigial. **Out of scope:** deployment-ui +
      unified-trading-system-ui are npm/package.json repos (separate versioning model, not hatch-vcs) — a follow-on npm
      migration if the operator wants version-out-of-source there too. **Gate met:** every Python/library repo is
      `version_source=git-tag`; the committed-version-line WRITERS are gone (PM self-bump retargeted). UNBLOCKS the
      cure-machinery delete below.
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
- 2026-06-27 (tick: **F3 DONE** — PM template @dc03bef18 + greeks @55c2f3b). cloudbuild `extract-version` now resolves
  from the git tag (git describe → highest v-tag → pyproject → short-sha), fixing the dynamic-pyproject mis-tag.
  Backward-compatible for static repos. `:latest`+bare-`:version` already existed on the live path; `:v`-prefix
  deliberately omitted (redundant, risks junk build rows). greeks re-rolled now; remaining service repos re-roll in
  their migration commit. Substitution-validator + YAML-validator green; both quickmerges QG-green.
- 2026-06-27 (tick: **F6 hook-census DONE** — `version-flow-map` workflow + dedicated Explore census). The retarget is
  thorough: only surviving pyproject WRITERS are the KNOWN deferred PM self-bump (`update-repo-version.yml:243`, #4 —
  retargeted when PM migrates to git-tag) + the cure machinery (delete-LAST, F7). All other hooks confirmed
  registry/git-tag-sourced. ⇒ F6 "zero surviving violations" is GATED on the fleet rollout (PM→git-tag) + F7; it flips
  GREEN only after those. **Finalize lane status: F1/F2/F3/F5 ✅ shipped; F4 (label-check relocate) NEXT; F6 + F7 gated
  on the FLEET ROLLOUT (the operator's "every repo on the new pipeline" requirement).** NEXT = F4, then the fleet
  rollout, then F7 + F6-green.
- 2026-06-27 (tick: **F4 DONE** — PM@be15cfb88). Label-check relocated onto the LDR→main fleet promoter (fail-open,
  semver-parity adversarial-verified SHIP). **Finalize-lane MECHANICS COMPLETE: F1/F2/F3/F4/F5 ✅ shipped; F6 census ✅;
  F6 zero-violation-green + F7 gated on the fleet rollout.**
- 2026-06-27 (**operator: parallelize for speed, accept transient breakage, /autonomous**). Plan: the fleet git-tag
  rollout IS parallelizable — each of the 23 repos is a SEPARATE git repo, so per-repo migration (mint baseline `vX.Y.Z`
  tag → dynamic pyproject → roll semver-agent[git-tag]+version-registry-notify → re-roll cloudbuild → quickmerge →
  verify) is independent. Shared resource = PM `workspace-manifest.json` (the `version_source` flips) → done CENTRALLY
  in one PM commit. **Two prerequisites found:** (1) **library wheel-publish-at-tag gate** —
  `configs/cloudbuild-library-template.yaml` does `python -m build` + `twine upload` directly (NOT spike-guarded), so a
  dynamic library built off-tag would publish a `.devN` wheel → consumers silently resolve dev under `<X.0.0` → fleet
  dep breakage. So LIBRARIES (UTL, UAC, + any other wheel-publishers) get the publish gated to clean-tag builds FIRST;
  SERVICES (21) are safe now (Docker image tags tolerate dev/short-sha; F3 handles them). (2) **PM-self-bump #4**
  (`update-repo-version.yml:243`) retargets when PM itself migrates. Execution: central manifest flip +
  library-publish-gate fix, then a PARALLEL workflow (one agent per repo, services first) doing the per-repo migration +
  verify; PM + libraries handled with extra care. SIT-rehome IMPLEMENTATION runs in parallel (separate concern) but
  STOPS before the live SIT flip (operator checkpoint). F7 stays gated on rollout-complete.
- 2026-06-27 (**FLEET ROLLOUT COMPLETE — 23/23 git-tag on origin**; PM@00dd2ab96). Executed the parallel rollout via an
  xargs-P2 driver over `migrate_one_repo_git_tag.sh`. Lessons + corrections (all within the operator's accept-breakage
  license, all fixed): (1) the manifest flip must be COMMITTED before per-repo migrations (the first driver run hit an
  autostash conflict — uncommitted flip + consolidator churn — corrupting the JSON so guards read empty; fixed by
  direct-committing the flip first). (2) the cloudbuild step's whole-file re-roll CLOBBERED 7 repos' custom steps
  (execution/strategy `stage-siblings` = build-breaking; 5× `operability-probe`; deployment-api `pm-configs`) — caught
  (QG doesn't run the cloudbuild Docker build, so it was silent until a deployment-api test flagged pm-configs), tool
  switched to `patch_cloudbuild_version.py` (surgical extract-version patch), `fix_clobbered_cloudbuild.sh` restored
  all 7. (3) the safety audit correctly REFUSED version-regressions (deployment-api 0.52.0/instruments 0.90.0/UAC 0.72.0
  had pyproject ahead of tag) → baseline tags minted (instruments' v0.90.0 existed-but-unreachable → moved to LDR HEAD,
  LDR=SSOT). (4) libraries (UTL/UAC) needed sequential landing (concurrent → pre-flight dep-dirty) + surgical
  publish-gates + the UAC `_get_version` importlib fix. (5) backmerge crons reverted instruments once (re-migrated,
  stuck). NET: every Python/library repo is git-tag; PM self-bump retargeted (no pyproject writer remains); UI repos are
  npm (out of scope).
- 2026-06-27 (**STAGING-DORMANT toggle shipped** — operator screenshot ask). `staging_dormant_mode=true` (manifest
  top-level, reversible). deployment-ui `classifyStall` now suppresses "LDR→staging drain behind" + "staging→main not
  promoting" + "drain stalled" + the stg→main Promotion-hops pills for ALL repos in dormant mode (fixed the ordering bug
  where drain-behind fired before the ldr_main check); +5 vitest tests. deployment-api exposes `staging_dormant_mode`
  per row. `promotion_lag_monitor` global gate → Slack/lag skips all staging directions fleet-wide. Only LDR→main
  flashes; dep-order + pr-stuck still surface. Live dashboard updates on the next deployment-ui/api deploy.
- 2026-06-27: **NEXT** = F7 (delete cure machinery — now unblocked, 23/23 git-tag) + F6 zero-violation green; then the
  staging-retire SIT-rehome → **OPERATOR CHECKPOINT before the live SIT fleet-wide flip** (the one pause).
