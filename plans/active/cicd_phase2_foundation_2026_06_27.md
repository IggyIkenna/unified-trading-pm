---
doc_type: plan
title: "CI/CD Phase-2 foundation — version-registry write-path (item B) + dynamic-versioning canary + spike guards"
summary: >-
  Phase-2 (version-out-of-source, D13) FOUNDATION lane. Stands up the registry write-path BEFORE any reader repoints:
  the event-driven tag→Firestore write-through (item B), the per-repo dynamic-versioning setup on ONE canary repo, and
  the three sandbox-spike hygiene guards (clean-checkout-at-tag build, publish-only-plain-3-part, stale-editable audit).
  Additive and reversible — breaks nothing live. This is registry-write-path step ① in the risk-ranked retarget order.
status: active
nature: infra
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cicd, phase-2, version-out-of-source, firestore, setuptools-scm, registry, D13, WS-L]
related:
  [
    cicd_consolidated_remaining_2026_06_24.md,
    cicd_phase2_semver_retarget_2026_06_27.md,
    ../epics/infrastructure_master.md,
    ../../codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-06-27
parent_epic: infrastructure_master
assigned_vm: NA
assigned_role: infra
drift_direction: advance-code
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

- [ ] [WORKFLOW] P1. **Item B — event-driven tag→Firestore write-through.** Build a workflow on `push: tags: v*` that
      writes `version↔SHA` to Firestore, mirroring the proven `ci-status-update.yml` (D2/WS-A-208) pattern: per-repo-doc
      CAS + `is_stale_write` ordering. The `*/30` `reconcile_release_tags.py` cron stays ONLY as a self-healing
      backstop, never the primary path. **CORRECTED 2026-06-27 (slot-3 audit, supersedes the prior "honest
      correction"):** `reconcile_release_tags.py` ALREADY writes Firestore — `_write_firestore_release_tags` (lines
      170-183) writes `repo_state/{repo}.release_tag = {version, tag}` best-effort `merge=True`, GCP-gated, since commit
      `839ebacdd` (2026-06-11), and `reconcile-release-tags.yml` wires the GCP auth + firestore SDK for it. So item B is
      NOT greenfield — it is the **event-driven + per-repo-doc-CAS + `is_stale_write(commit_ts)` + version↔SHA UPGRADE**
      of an existing best-effort write, converging on the SAME `repo_state/{repo}.release_tag` doc (now adding `sha` +
      `commit_ts`). Existing `repo_state` consumers: `promotion_lag_monitor.py`, `ci_failure_watcher.py`. **Gate:** push
      a `v*` tag on a scratch repo → Firestore doc updated in ≤1 min; CAS rejects a stale concurrent write;
      actionlint-clean.
- [ ] [INFRA] P1. **Dynamic-versioning on ONE canary repo** (setuptools-scm/hatch-vcs, version resolved from git tags at
      build). Pick a low-traffic leaf already on `ldr_main` (e.g. `alerting-service` or `greeks-service`). **Gate:** a
      version bump produces ZERO `pyproject.toml`/git commits; `uv build` at a clean tag yields the exact `vX.Y.Z`; the
      editable path-source resolution for its consumers is unaffected (proven by the sandbox spike — local dev uses the
      path source, not the version number).
- [ ] [INFRA] P1. **(spike guard) CI release build MUST be clean-checkout-at-tag.** Building at `v1.0.0` from a DIRTY
      tree produced `1.0.1.dev0+…d<date>` (a prerelease), NOT `1.0.0`. Add a clean-tree assertion (or fresh checkout at
      the exact tag) to the release build. **Gate:** a deliberately-dirty build FAILS loudly instead of publishing a dev
      version.
- [ ] [SCRIPT] P1. **(spike guard) publish/tag ONLY plain 3-part X.Y.Z — reject dev/local-suffix versions.** uv pulled a
      `1.0.1.dev0` prerelease under `<2.0.0` when it was the only candidate. Extend `reconcile_release_tags.py`'s
      existing plain-3-part restriction to the Phase-2 publish step. **Gate:** a `.devN`/`+local` wheel is refused at
      publish.
- [ ] [CODE] P2. **(spike guard) editable-metadata staleness audit.** `importlib.metadata.version()` reported `0.13.0`
      while live git was `0.13.1.dev1` (editable version frozen at install). Grep for self-version asserts via
      `importlib.metadata.version` that would break under dynamic versioning; re-resolve from git or accept staleness.
      Also: the release reconciler must never place two release tags on one commit (multi-tag/one-commit confused
      setuptools-scm in the spike). **Gate:** the audit list is produced + each entry resolved or annotated.

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
