---
doc_type: plan
title:
  Infra satellite AO batch 9 — UV version centralization (G2) + 3 dual-cloud-image-builds codex-drift follow-up fixes
summary: >-
  Ninth AO-dispatch batch for the `infra` topic tranche, produced by `/ag-closeout-audit infra` (autonomous mode,
  2026-08-09). Two independent sources: (1) `infra_batch3_g1_g2_deferred_gate_update_2026_08_07.md`'s G2 item (move the
  hardcoded UV version pin into a canonical source) — its sibling G1 (4 bundled base-service.sh/base-library.sh items)
  is now confirmed fully done via other channels (see that doc, archived this same run), clearing G2 to extract alone;
  live re-scoping found the constant hardcoded in 6 files, not the originally-estimated 3. (2) 3 conflict-clear,
  deterministic-outcome items from `issues/codex_drift_followups_dual_cloud_image_builds_2026_08_08.md` (a same-day
  net-new candidate, never previously evaluated by any infra covering doc) — stale Cloud Build substitution defaults, a
  possible orphaned trigger pair, and a dead provenance write-path. That source doc's own 4th item (AWS IAM read access)
  is operator-gated and NOT extracted here. Two of the four todos below (2 and 4) both touch
  `.github/workflows/cloud-build-router.yml`, so this plan runs `sequential: true`.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, satellite-docs, batch-9, plan-hygiene, cloud-build, uv]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch9_finalize_2026_08_09.md,
    /plans/archive/2026_08/issues/infra_batch3_g1_g2_deferred_gate_update_2026_08_07.md,
    /plans/active/issues/codex_drift_followups_dual_cloud_image_builds_2026_08_08.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/ag_closeout_audit_infra_parked_2026_08_09.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
assigned_role: infra
effort: medium
sequential: true
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_08/issues/infra_batch3_g1_g2_deferred_gate_update_2026_08_07.md,
    /plans/active/issues/codex_drift_followups_dual_cloud_image_builds_2026_08_08.md,
    scripts/quality-gates-base/base-service.sh,
    scripts/quality-gates-base/base-library.sh,
    scripts/workspace/resolve-canonical-versions.py,
    .github/workflows/cloud-build-router.yml,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit infra` run 2026-08-09 (ag_closeout_auditor scheduled worker, slot 22, dispatch agt-3b6f6b). Phase
  0 re-derived the covering set (9 covering docs, 50 members, 13 never-cited). Step 1 of the iterative-drain methodology
  re-checked `infra_batch3_g1_g2_deferred_gate_update_2026_08_07.md`'s own gate live against source code (not doc
  prose): G1's 4 items all confirmed done, G2 confirmed still open + conflict-clear. Phase 1 classified the 3 net-new
  members; `codex_drift_followups_dual_cloud_image_builds_2026_08_08.md` was conflict-checked (grepped all 9 infra
  covering docs + a corpus-wide grep for each target file/mechanism — see per-todo evidence below) and found
  conflict-clear. See `issues/ag_closeout_audit_infra_parked_2026_08_09.md` for the full run report.
---

# Infra satellite docs — AO dispatch batch 9

## Why this plan exists

**G2 (UV version pin centralization).** `infra_batch3_g1_g2_deferred_gate_update_2026_08_07.md` tracked two gates: G1 (a
4-item base-service.sh/base-library.sh bundle) and G2 (move the hardcoded `0.10.8` UV-version literal into a single
canonical source). Re-checked live today: **G1 is fully done** — all 4 items landed via other channels over the past 10
days and were never cross-referenced back to the gate doc (see that doc's archived Progress Log for full evidence: the
domain-client base-gate retarget 2026-07-30, the pip/cryptography/idna/pygments ignore-vuln drops via
`cve_affected_pinned_deps_remediation_2026_06_18.md`'s 2026-07-30 fleet-wide sweep, and a pre-existing uv drift-guard).
**G2 is still genuinely open** and, now that G1's claim on base-service.sh/base-library.sh has cleared, conflict-clear.
Live re-scoping found the `0.10.8` literal hardcoded in **6** places, not the 3 originally estimated: `scripts/setup.sh`
(×2 call sites), `scripts/workspace/workspace-bootstrap.sh` (`REQUIRED_UV="0.10.8"`),
`scripts/self-hosted-runners/hosted-baseline/python-quality-gates-v2.yml`, `scripts/quality-gates-base/base-service.sh`
(×3), `scripts/quality-gates-base/base-library.sh` (×3). `scripts/workspace/resolve-canonical-versions.py` currently has
no UV-version constant at all (it only resolves `uv_sources` path-based deps) — the centralization genuinely does not
exist yet.

**3 items from `codex_drift_followups_dual_cloud_image_builds_2026_08_08.md`.** That doc's own 5 findings surfaced while
live-verifying GCP/AWS state for an unrelated codex-drift-fix todo. Its own "Recommended decision" section already
self-assessed findings 1-3 and 5 as bounded/deterministic (no operator call needed); finding 4 (AWS IAM read access) is
explicitly operator-gated and excluded here (stays with the source doc as its own `[OPERATOR]` todo).

## Conflict check (before drafting)

- **UV version (`0.10.8`, `REQUIRED_UV`, uv-version-centralization)**: grepped all 9 infra covering docs + a corpus-wide
  `rg` for `REQUIRED_UV|uv.version.*centraliz|uv_version` — zero hits outside
  `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s own Deferred item 3 (the origin of G2) and the now-archived gate
  doc. No competing claim.
- **`_AR_REPO` (cloudbuild.yaml template default + cloud-build-router.yml hardcode)**: grepped the corpus for
  `_AR_REPO\b` (word-boundary, distinct from deployment-api's own `_AR_REPO_OVERRIDES` Python dict, a different
  mechanism in a different file — confirmed by reading
  `issues/deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md` in full: it audits a hand-maintained
  service-name→AR-repo-name allowlist consumed by `_get_ar_repo_name()` in deployment-api's own code, never touches
  `scripts/propagation/templates/cloudbuild.yaml` or the GHA workflow's Cloud Build trigger substitution). No genuine
  overlap — adjacent domain, different files, different mechanism.
- **`api-contracts-build`/`api-contracts-feature-build` GCP triggers**: no other active plan/issue references either
  trigger name.
- **`deployed_versions`/`deployed_versions_aws` manifest provenance**: no other active plan/issue proposes changing this
  write path (mentions found elsewhere in the corpus are all read-side consumers, not competing writers).
- **File-collision check across this batch's own 4 todos**: todo 1 touches 6 UV-pin files + a canonical-source file
  (none shared with todos 2-4); todo 2 touches `scripts/propagation/templates/cloudbuild.yaml` +
  `.github/workflows/cloud-build-router.yml`; todo 3 touches no repo file (GCP trigger API only); todo 4 touches
  `.github/workflows/cloud-build-router.yml` + `.github/workflows/cloud-build-router-aws.yml` +
  `workspace-manifest.json`. **Todos 2 and 4 share `cloud-build-router.yml`** — this plan runs `sequential: true`
  accordingly (matches the precedent set for G1's own 4-item bundle, parked for the identical reason).

## Todos

- [x] ✅ [INFRA] P2. **Centralize the UV version pin.** — unified-trading-pm@e5697ac5c. `UV_VERSION = "0.10.8"` added to
      `resolve-canonical-versions.py` (single canonical source); all 6 sites now derive from it via
      `grep -oP '^UV_VERSION = "\K[^"]+'` (bash sites) or a direct raw-fetch + grep (the GHA YAML site, since the
      dependency-clone step hasn't run yet at "Install uv" time). Verified: corpus-wide grep for `0.10.8` shows zero
      hits outside the canonical definition + plan/issue-doc prose; `test-setup-sh-uv-bootstrap-fallback.sh` updated to
      match the new shape and passes (5/5); `quality-gates.sh` ran green on alerting-service (a `base-service.sh`
      consumer) with the drift-guard confirmed resolving `_uv_pin=0.10.8` correctly; `quality-gates.sh` also green on
      unified-trading-pm itself. NOTE: `scripts/self-hosted-runners/hosted-baseline/python-quality-gates-v2.yml` is a
      point-in-time snapshot (per `hosted-baseline.sh`'s own header) — the truly-live copy of this reusable workflow
      lives in the separate `unified-trading-ci` repo and still has the old literal; out of this plan's
      `repos:     [unified-trading-pm]` scope, filed as a follow-up issue doc (see Progress Log). Original text: Add a
      single canonical `UV_VERSION` constant (natural home: `scripts/workspace/resolve-canonical-versions.py`, alongside
      its existing dependency-version resolution logic, or `canonical-dependency-manifest.json` if that's a better fit
      for how `resolve-canonical-versions.py` already reads its other pins — worker's call, consistent with how the
      existing `uv_sources` mechanism is structured) and update all 6 hardcoded `"0.10.8"` sites to read from it instead
      of a literal: `scripts/setup.sh` (2 call sites: the `pip install "uv==$UV_VERSION"` fallback path and the
      curl-install path), `scripts/workspace/workspace-bootstrap.sh` (`REQUIRED_UV`),
      `scripts/self-hosted-runners/hosted-baseline/python-quality-gates-v2.yml` (the `pip install     "uv==..."` step —
      a GHA workflow YAML, so this site reads the constant via whatever mechanism the other 5 use, e.g. a shared
      env/step output, not a Python import), `scripts/quality-gates-base/base-service.sh` (3 sites: the
      install-fallback, the drift-check comparison, the drift-warning message),
      `scripts/quality-gates-base/base-library.sh` (same 3 sites, mirrored). Done when: exactly ONE file defines the
      literal `0.10.8`, all 6 consumer sites derive from it (grep confirms zero remaining bare `"0.10.8"` string
      literals outside the new canonical definition site and any test fixtures that intentionally assert against it),
      and `quality-gates.sh` stays green on at least one repo touched by `base-service.sh` (confirms the drift-guard
      still fires correctly post-refactor). Source: `infra_batch3_g1_g2_deferred_gate_update_2026_08_07.md` (G2) /
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md` § Deferred item 3. (repo: unified-trading-pm)
- [x] ✅ [INFRA] P3. **Fix the stale `_AR_REPO` default in the 2 dead/orphaned template sites.** —
      unified-trading-pm@809d6b8d22. (1) `scripts/propagation/templates/cloudbuild.yaml`'s `_AR_REPO` substitution
      default reads `"unified-trading"` but the real Artifact Registry repo is `unified-trading-system` (verified live
      2026-08-08: `unified-trading` returns `NOT_FOUND`) — update the default, or confirm the template is fully
      superseded by the per-repo `_REGISTRY_REPO` convention (check whether
      `rollout-workflow-templates.sh --template cloudbuild.yaml` is still ever invoked) and delete/retire it instead.
      (2) `.github/workflows/cloud-build-router.yml`'s `gcloud builds triggers run` call hardcodes the same stale
      `_AR_REPO=unified-trading` in its `--substitutions` list — remove or correct it (confirm first that no per-repo
      `cloudbuild.yaml` still references `_AR_REPO` instead of `_REGISTRY_REPO` before deleting). Done when: no live
      code path can produce a build using the stale `unified-trading` AR-repo name. Source:
      `issues/codex_drift_followups_dual_cloud_image_builds_2026_08_08.md` findings 1-2. (repo: unified-trading-pm)
- [x] ✅ [INFRA] P3. **Check + clean up the possibly-orphaned `api-contracts-build`/`api-contracts-feature-build` GCP
      Cloud Build triggers.** Both confirmed dead + deleted 2026-08-10 (GCP-only todo; no repo commit). Evidence:
      `gcloud builds     triggers describe api-contracts-build` / `api-contracts-feature-build`
      (`--project=central-element-323112     --region=asia-northeast1`) both bind to the stale
      `repositories/api-contracts` in connection `iggyikenna-github` — the GitHub repo was renamed
      `api-contracts`→`unified-api-contracts` (`IggyIkenna/unified-api-contracts`;
      `gh api repos/IggyIkenna/api-contracts` redirects to the new name). `api-contracts-build` (`^main$`): last build
      2026-06-19, and `main` is pushed daily (2026-08-10T08:42Z, 07:06Z) with zero trigger builds — stale binding
      receives no webhook events — while the current `unified-api-contracts-live-defi-rollout` trigger fires SUCCESS
      daily (2026-08-10 10:21, 10:16, 09:56…). `api-contracts-feature-build` (`^feat/.*`): **0 builds ever**. Deleted
      both via `gcloud builds triggers delete <name> --project=central-element-323112 --region=asia-northeast1 --quiet`
      → `Deleted     [.../triggers/api-contracts-build]` + `Deleted [.../triggers/api-contracts-feature-build]`;
      verified both absent from `gcloud builds triggers list` and the current `unified-api-contracts-live-defi-rollout`
      trigger intact. Source: `issues/codex_drift_followups_dual_cloud_image_builds_2026_08_08.md` finding 3. (repo:
      unified-trading-pm / GCP project central-element-323112)
- [ ] [INFRA] P3. **Decide + fix `deployed_versions`/`deployed_versions_aws` manifest provenance.** Both
      `cloud-build-router.yml` and `cloud-build-router-aws.yml` write-intend these `workspace-manifest.json` fields on a
      successful build, but live state (verified 2026-08-08) shows `deployed_versions` present-but-empty
      (`{"dev": {},     "staging": {}, "prod": {}}`) and `deployed_versions_aws` entirely absent — either the write path
      is broken or was never fully wired. Either (a) fix the write path so both fields actually populate on a successful
      build (the workflows already contain the intended `jq` write logic per the grep evidence in the source doc — trace
      why it isn't landing, e.g. a `[skip ci]`-triggered commit not actually pushing, a stale manifest read before the
      write, a race with a concurrent build), or (b) remove the dead write-intent code and stop presenting the manifest
      as a build-provenance source anywhere in the codebase/docs. Done when: a real build's `deployed_versions` entry is
      confirmed populated post-fix (option a), or all dead write-intent code + any doc claiming provenance-via-manifest
      is removed (option b) — worker's call on which, since the doc's own "why it matters" note argues (a) is more
      valuable (provenance should be answerable), but either resolves the finding. Source:
      `issues/codex_drift_followups_dual_cloud_image_builds_2026_08_08.md` finding 5 / todo 4. (repo:
      unified-trading-pm)

## Operator approval gate

**RULED 2026-08-09 (operator): approved.** Flipped `status: draft` → `status: active`; its finalize twin was already
`status: active` per the no-double-gate ruling and stays correctly gated either way.

## Codex SSOTs (read before touching a todo)

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — the procedure this batch was produced by
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the conflict-check protocol applied
  above
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — archival ritual the finalize plan runs
- `/plans/active/task_template.md` §4 — finalize-plan-coverage rule, dispatch-scope eligibility test

## Progress Log

- **2026-08-09** — Drafted by `/ag-closeout-audit infra` (autonomous mode, scheduled daily run, slot 22, dispatch
  agt-3b6f6b). Paired with `infra_satellite_ao_dispatch_batch9_finalize_2026_08_09.md` in the same run per the
  finalize-plan-coverage rule.
- **2026-08-10 (slot 14, infra)**: Todo 2 shipped. Deleted dead `scripts/propagation/templates/cloudbuild.yaml` (fully
  superseded by `configs/cloudbuild-*-template.yaml` using `_REGISTRY_REPO`; not referenced by
  `rollout-workflow-templates.sh`). Fixed `_AR_REPO=unified-trading`→`unified-trading-system` in
  `.github/workflows/cloud-build-router.yml` +
  `scripts/self-hosted-runners/hosted-baseline/{cloud-build-router,image-build-validate}.yml`. Also fixed
  plan-discipline ratchet in `codex_vs_repo_docs_ssot_audit` (added Deferred banner). unified-trading-pm@809d6b8d22.
- **2026-08-10 (slot 17, infra)**: Todo 3 shipped (GCP-only, no repo commit). Confirmed + deleted the orphaned
  `api-contracts-build` / `api-contracts-feature-build` Cloud Build triggers in project central-element-323112 (region
  asia-northeast1). Both bound to the stale `repositories/api-contracts` connection binding (repo renamed
  `api-contracts`→`unified-api-contracts` in IggyIkenna org); `api-contracts-build` silent since 2026-06-19 despite
  daily `main` pushes while the current `unified-api-contracts-live-defi-rollout` trigger builds SUCCESS daily;
  `api-contracts-feature-build` had zero builds ever. Deleted both via `gcloud builds triggers delete --quiet` and
  verified them absent from `gcloud builds triggers list` with the current trigger intact.
