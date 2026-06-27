---
doc_type: plan
title: CI/CD Phase-2 foundation — version-registry write-path (item B) + dynamic-versioning canary + spike guards
summary: 'Phase-2 (version-out-of-source, D13) FOUNDATION lane. Stands up the registry write-path BEFORE any reader repoints: the event-driven tag→Firestore write-through (item B), the per-repo dynamic-versioning setup on ONE canary repo, and the three sandbox-spike hygiene guards (clean-checkout-at-tag build, publish-only-plain-3-part, stale-editable audit). Additive and reversible — breaks nothing live. This is registry-write-path step ① in the risk-ranked retarget order.'
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cicd, phase-2, version-out-of-source, firestore, setuptools-scm, registry, D13, WS-L]
related: [cicd_consolidated_remaining_2026_06_24.md, cicd_phase2_semver_retarget_2026_06_27.md, ../epics/infrastructure_master.md, ../../codex/08-workflows/ci-cd-flow.md]
created: 2026-06-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-27
supersedes:
superseded_by:
depends_on:
source: cicd_consolidated_remaining_2026_06_24.md (Phase-2 section, lines ~1163-1356)
assigned_role: infra
drift_direction: advance-code
---

# CI/CD Phase-2 foundation — registry write-path + dynamic-versioning canary

> **Phase-2 lane 1 of 4** (foundation). **No upstream dep — parallel-startable.** Gates the rest of Phase-2: the
> semver-retarget lane (`cicd_phase2_semver_retarget`) `depends_on` THIS plan. **Model tier: Sonnet/infra** — spec'd,
> additive; the architecture is decided (D13). Full detail + the 17-hook audit live in the consolidated tracker
> `cicd_consolidated_remaining_2026_06_24.md`.
>
> **Canonical decision (D13):** git tags = the version SSOT; Firestore = the queryable read-mirror; manifest
> `versions{}` becomes a derived projection. Builds resolve the version from the git tag in-repo — they NEVER read
> Firestore, so the mirror tolerates eventual consistency.

## Tasks

- [~] [WORKFLOW] P1. **Item B — event-driven tag→Firestore write-through.** Build a workflow on `push: tags: v*` that
  writes `version↔SHA` to Firestore, mirroring the proven `ci-status-update.yml` (D2/WS-A-208) pattern: per-repo-doc
  CAS + `is_stale_write` ordering. The `*/30` `reconcile_release_tags.py` cron stays ONLY as a self-healing backstop,
  never the primary path. **CORRECTED 2026-06-27 (slot-3 audit, supersedes the prior "honest correction"):**
  `reconcile_release_tags.py` ALREADY writes Firestore — `_write_firestore_release_tags` (lines 170-183) writes
  `repo_state/{repo}.release_tag = {version, tag}` best-effort `merge=True`, GCP-gated, since commit `839ebacdd`
  (2026-06-11), and `reconcile-release-tags.yml` wires the GCP auth + firestore SDK for it. So item B is NOT greenfield
  — it is the **event-driven + per-repo-doc-CAS + `is_stale_write(commit_ts)` + version↔SHA UPGRADE** of an existing
  best-effort write, converging on the SAME `repo_state/{repo}.release_tag` doc (now adding `sha` + `commit_ts`).
  Existing `repo_state` consumers: `promotion_lag_monitor.py`, `ci_failure_watcher.py`. **Gate:** push a `v*` tag on a
  scratch repo → Firestore doc updated in ≤1 min; CAS rejects a stale concurrent write; actionlint-clean. **STATUS
  (slot-3 2026-06-27): IMPLEMENTED + LANDED, live-verify pending.** Shipped QG-green (21 unit tests, actionlint-clean):
  the CAS store `version_registry_store.py` (per-repo Firestore txn → `repo_state/{repo}.release_tag`, field-scoped
  `merge=True` preserving sibling fields, semver-monotonic no-downgrade), the PM handler `version-registry-update.yml`,
  the per-repo notify template `version-registry-notify.yml` — PM@7b2c956b9 (PR #616); `reconcile_release_tags.py`
  backstop routed through the SAME CAS store (+sha, no-downgrade) — PM@9bb9d5bfe. Local build verified (hatch-vcs
  resolves the tag). REMAINING (live gate): roll the notify workflow to the canary + push a real tag → assert the doc
  updates in ≤1 min + CAS rejects a stale write (needs #616 on main + GCP) — folded into the retarget-lane canary step.
- [~] [INFRA] P1. **Dynamic-versioning on ONE canary repo** (setuptools-scm/hatch-vcs, version resolved from git tags at
      build). Pick a low-traffic leaf already on `ldr_main` (e.g. `alerting-service` or `greeks-service`). **Gate:** a
      version bump produces ZERO `pyproject.toml`/git commits; `uv build` at a clean tag yields the exact `vX.Y.Z`; the
      editable path-source resolution for its consumers is unaffected (proven by the sandbox spike — local dev uses the
      path source, not the version number). **CANARY CHOSEN (slot-3): `greeks-service`** — 0 consumers (lowest blast
      radius), on `ldr_main`, hatchling, has a `v0.18.17` tag matching pyproject. Build feasibility verified locally.
      **⚠️ ORDERING FINDING — the canary flip is GATED on the flag-gated `.tmpl` writer (retarget hook #1), NOT just a
      pyproject edit:** the current semver-agent writer asserts a `version =` line exists before `sed`, so the instant a
      repo goes dynamic the writer SILENTLY refuses to bump it — the "zero-commit bump" gate can only be met once the
      writer mints a tag for a `version_source=git-tag` repo. So the correct sequence is (1) make the `.tmpl` writer
      branch on `version_source` (mint tag vs legacy sed) + roll out; (2) flip `greeks-service/pyproject.toml` →
      `dynamic=["version"]` + `[tool.hatch.version] source="vcs"`; (3) flip the manifest `version_source` → `git-tag`;
      (4) roll the notify workflow to greeks-service; (5) verify bump → tag + Firestore, zero commits. Step (1) is the
      Opus-xhigh `.tmpl` change — so this canary is the **BRIDGE into `cicd_phase2_semver_retarget`** (execute
      canary-first, behind the flag, at the head of that lane). Confirmed: a dynamic repo in CI (`uv sync`,
      shallow/no-tags) falls back to a `devN` version WITHOUT breaking the build — so the canary won't red
      greeks-service CI. **STATUS (slot-3 2026-06-27): IMPLEMENTED + LANDED, live-verify pending.** Shipped QG-green:
      (1) `__VERSION_SOURCE__` flag-gate added to `semver-agent.yml.tmpl` (compute + writer steps); (2) `rollout-workflow-
      templates.sh` `get_version_source()` substitution; (3) `workspace-manifest.json` `greeks-service.version_source=git-tag`;
      (4) `greeks-service/.github/workflows/semver-agent.yml` re-rendered (`VERSION_SOURCE="git-tag"` at 6 sites); (5)
      `version-registry-notify.yml` added to greeks-service; (6) `greeks-service/pyproject.toml` `dynamic=["version"]` +
      `hatch-vcs`. PM@c52434508; greeks-service@ad7e7ba. REMAINING (live gate): push a `v*` tag on greeks-service →
      assert Firestore doc `repo_state/greeks-service.release_tag` updates in ≤1 min + CAS rejects stale write. Needs
      PR #616 on `main`. Folded into retarget-lane canary step (the `cicd_phase2_semver_retarget` plan).
- [x] ✅ [INFRA] P1. **(spike guard #1) CI release build MUST be clean-checkout-at-tag.** DONE 2026-06-27
      (PM@33facf847). `scripts/build-library-wheel.sh` asserts the BUILT wheel's version is plain 3-part `X.Y.Z` after
      `python -m build` — a dirty tree / commits-past-tag yields `X.Y.Z.devN+g<sha>` (verified locally), which the guard
      REJECTS (exit 1). Catches both dirty-tree AND off-tag in one artifact check. `ALLOW_DEV_WHEEL=true` overrides for
      local dev. Static repos always pass. **Gate met.**
- [x] ✅ [SCRIPT] P1. **(spike guard) publish/tag ONLY plain 3-part X.Y.Z — reject dev/local-suffix.** DONE 2026-06-27.
      Enforced at FOUR layers: `build-library-wheel.sh` rejects non-plain built wheels (#1 above); the version-registry
      path rejects non-plain at every hop (`version-registry-notify.yml`, `version-registry-update.yml`,
      `version_registry_store.set_release_version` raises `ValueError`); plus `reconcile_release_tags.py`'s
      `_VERSION_RE` only tags plain 3-part. **Gate met:** a `.devN`/`+local` version reaches neither a published wheel
      nor the registry.
- [x] ✅ [CODE] P2. **(spike guard) editable-metadata staleness audit.** DONE 2026-06-27. Fleet-wide
      `rg "importlib\.metadata\.version"` (excl. venv/tests/build) → exactly TWO sites, BOTH Phase-2-safe (read the
      INSTALLED-DIST version, not a hardcoded self-assert): `deployment-api/routes/cloud_builds.py:413` (API-1,
      migrated) + `deployment-service/deployment_service/bom.py:90` (DS-3, verified). `reconcile_release_tags.py`
      creates exactly one tag per version (idempotent) → no multi-tag/one-commit hazard. NOTE for finalize:
      `deployment_api/__init__.py:8` is a STATIC `__version__` literal (NOT importlib.metadata) — make dynamic there
      (API-2). **Gate met.**

## Success criteria

- The tag→Firestore write-path exists, event-driven, ≤1-min latency, CAS-ordered; cron is backstop only.
- One canary repo is fully dynamic-versioned with zero-commit bumps + clean-tag builds, consumers unaffected.
- The three spike guards are enforced (clean-tree build, publish-only-clean, stale-editable audited).

## Codex SSOT updates

- `codex/08-workflows/ci-cd-flow.md` § "Release tag reconciler" — document the new tag→Firestore write-through + the
  clean-checkout-at-tag + publish-only-clean guards.

## Progress Log

- 2026-06-27: Split from the cicd consolidated tracker (Phase-2 foundation lane). Sandbox graduation spike already DONE
  (evidence in the consolidated plan): local editable dev survives 1.x/2.x graduation; the `<1.0.0` wall is
  published-path-only; 3 footguns captured here as guards.
- 2026-06-27 (slot-3 TAKEOVER, operator-greenlit): all 3 Phase-2 plans reassigned `harsh_pc → NA` (operator-driven;
  slot-3 interactive drives foundation→retarget→finalize end-to-end). A fresh no-regression audit (8-agent ultracode
  workflow, 7 cluster finders + skeptic) refreshed the 17-hook manifest against current code and found: (a) the stale
  "no-Firestore" claim CORRECTED above; (b) **5 hooks the inventory missed** — `manifest_merge_driver.py` (parallel
  max-semver resolver on `versions{}`/`staging_versions{}`/`deployed_versions{}`), `request-major-bump.yml` (2 fleet
  TEMPLATE copies, not pm-only), `staging-to-main.yml` version_delta promoter loop (gates main promotion off the
  manifest version maps — HIGH risk), `cloud-build-router.yml` (WRITES `deployed_versions{}` + the bare-semver image tag
  API-3 parses), `check-precommit-versions.py` (dormant re-installer of the deleted bump-library-version hook); (c) **7
  ordering hazards** (registry-write-before-reader, writer-before-resolvability-gate-flip, breaker-goes-inert,
  required-check-don't-delete-arm, promoter-reads-lagging-cache, cure-machinery-delete-LAST, build-backend-before-
  importlib-readers); (d) `version_source` field already exists on all 25 repos → extend its enum with `git-tag` as the
  per-repo canary flag (no new `version_model` field needed); (e) API-1 DONE, API-2 still STATIC (needs the same
  importlib.metadata swap), UI-3 does not exist (folds into API-3). Full manifest in the consolidated tracker.
- 2026-06-27 (slot-3 FOUNDATION BUILD): shipped 3 QG-green units. Item-B write-path (store + PM handler + notify
  template) PM@7b2c956b9 (PR #616); reconcile backstop CAS upgrade PM@9bb9d5bfe; spike guards #1+#2 (build-wheel
  plain-3-part assertion) PM@33facf847; spike guard #3 (importlib.metadata audit) clean. Foundation status: **item B
  implemented (live-verify pending), all 3 spike guards DONE; the canary remains** — it is gated on the flag-gated
  `.tmpl` writer (retarget hook #1), so it bridges into `cicd_phase2_semver_retarget` (execute canary-first there). Next
  major step = the Opus-xhigh `.tmpl` writer retarget behind the `version_source` flag.
- 2026-06-27 (slot-3 CANARY SHIPPED — context resumed after compaction): canary `[~]` implementation DONE. Shipped
  QG-green in two quickmerges: PM@c52434508 (`.tmpl` flag-gate + rollout substitution + manifest `version_source=git-tag`
  + dual-cloud-image-builds codex) and greeks-service@ad7e7ba (`pyproject.toml` hatch-vcs, `semver-agent.yml` re-rendered
  `VERSION_SOURCE="git-tag"`, `version-registry-notify.yml`, `image-build-gate.yml`, `buildspec.aws.yaml` pip fix). Side
  fix: `main-backmerge-to-ldr.yml` schedule-trigger removal rolled out to all 24 service repos (was blocking PM QG
  template-parity check). Foundation is CODE-COMPLETE; sole remaining gate is live-verify (PR #618 merged to main + a
  real `v*` tag push to greeks-service → Firestore doc). Folded into retarget-lane canary step per plan.
  **Deferred (retarget plan):** Codex SSOT update `codex/08-workflows/ci-cd-flow.md` § Release-tag-reconciler — document
  flag-gated `__VERSION_SOURCE__` + tag-mint write path; update when the retarget lane verifies the live gate.
- 2026-06-27 (slot-3 PIPELINE UNBLOCKED): PR #618 (LDR→main) MERGED to main (run 28285801855 ✅). Foundation code
  (`version-registry-update.yml`, `version_registry_store.py`, CAS upgrade) now on PM main. REMAINING live-verify gate:
  greeks-service changes (hatch-vcs, `version-registry-notify.yml`) must reach greeks-service main via Tier-C drain
  (LDR→staging→SIT→main, ~1-2h pipeline). Once there, push `v0.18.18` tag → assert `repo_state/greeks-service.release_tag`
  updates in ≤1 min + CAS rejects stale write. This is the retarget plan's first task gate (Opus-xhigh required). All
  code work on Sonnet complete; handing off to Opus via retarget plan.
