---
name: infrastructure_master_audit_instructions
type: audit-instructions
epic: infrastructure_master
assigned_vm: vm-cross-cutting
tier: L4
last_updated: 2026-06-01
---

# Infrastructure Master — Audit Instructions

## Epic Scope

VM lifecycle management (`lifecycle_class`, zombie watchdog, zone policy), tarballs (`create-code-tarballs.sh`), per-tab
worktrees, GCS object operations (UTL library only, no subprocess), bucket SSOT (`resolve_bucket_name()`), cloud
bootstrap. Hard rules: asia-northeast1-c default zone; no cross-region fallback; no subprocess gsutil/gcloud.

**CI/CD pipeline contract (added 2026-06-01).** This epic also owns the **end-to-end code-promotion pipeline** — the
single contract that every host (VM orchestrator, VM worker, operator/Harsh laptop) follows to move code to a remote
branch and ultimately to a deployed image. The contract: **quickmerge is the only sanctioned merge path** → it is
**gated on a full quality-gates run** (the `.qg_last_passed_sha` sentinel) → it **never force-pushes** → it opens an
**auto-PR to `staging`** with auto-merge on green → **SIT runs at staging** (per-repo CI + the full-workspace cross-repo
SIT) → promotion **cascades to `main`** via semver-agent → `main` **triggers image builds for GCP (cloudbuild) + AWS
(buildspec) + Cloud Run deploy**. Branch-triggered builds are supported for hotfix / fast-dev image cycles, and the
**tarball path** (`create-code-tarballs.sh`) is the local-code alternative — SHA-pinned + manifest-stamped so it is
**tagged as such**. Dirty trees are reconciled (slot crons) and QG-green-everywhere is the standing precursor. Before
this section existed, these checks were scattered across `orchestrator_master` (quickmerge symmetric model, dirty-tree
crons), `deployment_and_user_management_master` (deploy/promote API), and `observability_master` (LDR-CI-red
monitoring), and **no single audit verified the contract end-to-end** — exactly the blind spot that let `staging` drift
~1 month undetected (see `plans/active/issues/full_cicd_sit_target_state_2026_05_24.md`).

Codex SSOTs: `codex/05-infrastructure/vm-tarball-deployment.md`, `codex/05-infrastructure/per-tab-worktrees.md`,
`codex/05-infrastructure/gcs-object-operations.md`, `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`,
`codex/08-workflows/ci-cd-flow.md` (engineer SSOT), `codex/08-workflows/deployment-flow.md` (operator SSOT),
`codex/05-infrastructure/deployment-and-qg-strategy.md` (tarball-vs-image + 4-tier QG enforcement),
`codex/06-coding-standards/quality-gates.md` (two-pass model + sentinel)

## Triggers

- Weekly (minimum cadence)
- After any VM topology change (new VM prefix, VM removed)
- After any new prefix added to `VM_PREFIX_TO_BUCKET` in `vm_zombie_watchdog.py`
- When bucket name SSOT plan advances a phase
- After operator laptop onboarding or cron re-setup
- **After any change to `scripts/quickmerge.sh`, `scripts/quality-gates*.sh`, `scripts/quality-gates-base/`, or any
  `scripts/workflow-templates/*` template** (the CI/CD machinery)
- **After a new repo is added to the active workspace** (must inherit branch protection + the canonical workflow)
- **After the `quality-gates-v2` required-check name changes** (or any future v3 migration)
- **When the CI/CD target-state plan (`full_cicd_sit_target_state_2026_05_24.md`) advances a tier (A–E)**
- **After any change to `deployment-service/cloudbuild.yaml`, `buildspec.aws.yaml`, or
  `scripts/vm/create-code-tarballs.sh`** (the build + tarball machinery)

## Checklist

- [ ] (a) **All VM_PREFIX_TO_BUCKET entries have lifecycle_class**: every non-`None` entry is a `VmPrefixSpec` with
      `lifecycle_class=LifecycleClass.<EPHEMERAL_BATCH|...>`. Read:
      `deployment-service/scripts/vm/vm_zombie_watchdog.py` — verify no raw bucket strings without lifecycle_class

- [ ] (b) **Experiment VM names include run_id**: `EPHEMERAL_EXPERIMENT` VMs use pattern `{prefix}{run_id}-{ts}`. Read:
      relevant VM launch scripts in `deployment-service/scripts/vm/` — verify naming for exp- prefixes

- [ ] (c) **Zone default is asia-northeast1-c, no cross-region fallback**: all `gcloud compute instances create`
      commands default to `asia-northeast1-c` with stockout fallback only to `-b` or `-a` (same region). Grep:
      `rg "us-central1\|us-east1\|europe-" deployment-service/scripts/vm/ --include="*.sh"` — should be 0 hits

- [ ] (d) **No subprocess gsutil/gcloud for per-object ops**: all per-object GCS work uses UTL library. Grep:
      `rg "subprocess.*gsutil|subprocess.*gcloud" --include="*.py"` — should be 0 hits in migration scripts and VM
      launch scripts (CLI tooling may use gsutil, but not per-object loops)

- [ ] (e) **resolve_bucket_name() for all bucket lookups — QG STEP 5.69**: no inline `gs://` f-strings. Run: QG STEP
      5.69 passes workspace-wide

- [ ] (f) **verify-slot-host-symmetry.sh exits 0**: operator laptop has both crons installed and ran within 10 min. Run:
      `bash unified-trading-pm/scripts/verify-slot-host-symmetry.sh`

- [ ] (g) **Orphan-ping audit cron active**: Cloud Scheduler job `uts-prod-orphan-ping-audit` is ENABLED in
      `central-element-323112` / `asia-northeast1`. Check:
      `gcloud scheduler jobs describe uts-prod-orphan-ping-audit --location=asia-northeast1`

### CI/CD Pipeline Contract (added 2026-06-01)

> The promotion contract: **quickmerge-only → QG-sentinel-gated → no force-push → auto-PR-to-staging → SIT-at-staging →
> cascade-to-main → image-builds (GCP + AWS + Cloud Run)**, with branch-triggered builds + the tarball local-code path
> as tagged alternatives, dirty-tree reconciliation, and QG-green-everywhere as the standing precursor. Every item is
> grep/`gh`/`gcloud`-verifiable. Most checks are read-only; the live-fleet checks (h6, k1) need a logged-in host.

**Promotion path is quickmerge-only + sentinel-gated + never force-pushes**

- [ ] (h1) **quickmerge is QG-sentinel-gated.** `scripts/quickmerge.sh` reads `.qg_last_passed_sha` and refuses to
      proceed on mismatch/absence. Grep: `rg -n "qg_last_passed_sha" scripts/quickmerge.sh` — ≥1 hit in the Pass-2
      verification block.
- [ ] (h2) **Only a FULL QG run writes the sentinel.** The sentinel is written in `quality-gates-base/base-service.sh`
      only on clean exit with no skip flags. Grep:
      `rg -n "qg_last_passed_sha" scripts/quality-gates-base/base-service.sh` — the
      `git rev-parse HEAD > .../.qg_last_passed_sha` line must be guarded by "no skip flags / full run". Confirm
      `--skip-tests|--skip-typecheck|--skip-codex|--quick` do NOT reach the write.
- [ ] (h3) **quickmerge never force-pushes.** Grep:
      `rg -n "push .*--force|--force-with-lease|push -f\b" scripts/quickmerge.sh` — expect **0** real hits (comment
      keywords like `enforce-*` are fine). Cross-check `codex/08-workflows/ci-cd-flow.md` § "Conditional Push Protocol"
      still bans force-push to LDR.
- [ ] (h4) **Human commits auto-PR to `staging` with auto-merge.** Grep:
      `rg -n "gh pr (create|merge).*(staging|--auto)" scripts/quickmerge.sh` — PR base is `staging` for human commits,
      `main` only for `[skip ci]` automation, and `gh pr merge --auto --squash` is enabled.
- [ ] (h5) **`--dep-branch` is human-only / agents route through staging.** Grep:
      `rg -n "dep-branch cannot be used|--dep-branch" scripts/quickmerge.sh` — the staging-first model rejects
      `--dep-branch` for the agent path.
- [ ] (h6) **Slot-host symmetry: every host runs the same quickmerge contract.** `verify-slot-host-symmetry.sh` exits 0
      on each operator/worker host (FF-pull + git-status crons installed + recent). Run:
      `bash unified-trading-pm/scripts/verify-slot-host-symmetry.sh`. (Shares check k1 of `orchestrator_master`.)

**Branch protection enforces the gate everywhere (QG-green-everywhere precursor)**

> **CANONICAL MECHANISM = RULESETS, not classic branch protection (corrected 2026-06-01).** The workspace enforces the
> QG gate via GitHub **rulesets** (`require-quality-gates` on main, `require-staging-lock-check` on staging), managed by
> `scripts/repo-management/pin_branch_protection_rulesets.py` + verified by `verify_branch_protection_check_names.py`.
> Classic `/branches/.../protection` is a SECONDARY/legacy surface that some repos also carry — do NOT audit it as the
> primary gate (the first 2026-06-01 run did, and mis-reported the state). The required check context is DERIVED from
> each repo's live workflow file, so the gate is "v2" iff the repo's default-branch workflow is `quality-gates-v2.yml`.

- [ ] (i1) **Ruleset required-check is consistent on every repo.** Run (read-only):
      `python3 scripts/repo-management/verify_branch_protection_check_names.py` → exit 0 / "ALL RULESETS CONSISTENT:
      True". This confirms each repo's ruleset requires exactly what its workflow emits (no name drift).
- [ ] (i2) **Every repo's required check is `quality-gates-v2`, not retired v1 `quality-gates`.** From the same verifier
      output, **no repo's MAIN/STAGING required context may be `…/quality-gates` (v1)**. A repo shows v1 iff its
      default-branch workflow is still `workspace-qg.yml` — migrate the workflow to `quality-gates-v2.yml` (then re-pin
      with `pin_branch_protection_rulesets.py --apply --repo <r>`). **Migration is GATED on that repo's v2 QG being
      green** — enabling the v2 required check on a red repo blocks ALL its merges. (2026-06-01 ground truth: 9/17 on
      v2; **8 still on v1**, 7 of which are blocked on pre-existing QG-red — see result file +
      `ci_canonical_v2_migration`.)
- [ ] (i3) **No force-push to `main`/`staging`.** Confirm via the ruleset (`non_fast_forward` rule present) and that no
      repo allows force-push on protected refs.
- [ ] (i4) **Admin bypass is constrained.** Where classic protection is also present, `enforce_admins.enabled == true`
      (or the ruleset's `bypass_actors` is limited to intended roles). NB: `--admin`/admin merges are gated by
      `enforce_admins`; a controlled admin-merge requires temporarily relaxing it (relax → merge → restore), never
      leaving it off.
- [ ] (i5) **LDR is unprotected-by-design but MONITORED.** LDR has no branch protection (rapid direct-push by design,
      per `ci-cd-flow.md`), so its CI-red must be a watched signal, not silently accumulated. Verify the Tier-A
      LDR-CI-red ping exists (cross-ref `full_cicd_sit_target_state_2026_05_24.md` Tier A `[AGENT] P0` item).

**SIT at staging + concurrent-push serialization**

- [ ] (j1) **Per-repo CI runs on push/PR to staging+main.** `scripts/workflow-templates/workspace-qg.yml.tmpl` triggers
      include `push:[main,staging]` + `pull_request:[main,staging]`. Grep the template.
- [ ] (j2) **Full-workspace cross-repo SIT exists + is scheduled.** `system-integration-tests` repo has
      `scripts/run_cross_repo_invariants.sh` + `.github/workflows/full-workspace-sit.yml` (clones the manifest
      `topologicalOrder.levels` set; nightly + `workflow_dispatch` + `repository_dispatch[full-workspace-sit]`). Confirm
      it FAILS on skip (the guarded cross-repo tests must run for real, not skip when siblings present).
- [ ] (j3) **Promotion is gated on SIT.** A repo cannot promote to `staging`/`main` while the full-workspace SIT is RED
      for its layer (Tier B/C of the CI/CD target-state plan). Document current automation state (manual vs bot).
- [ ] (j4) **Concurrent pushes are serialized, not raced.** quickmerge honors the `staging_status.locked` flag in
      `workspace-manifest.json` and otherwise relies on GitHub's native auto-merge queue. Grep:
      `rg -n "staging_status|locked|auto-merge queue" scripts/quickmerge.sh`. **Known gap to document if unchanged:**
      there is no hard cross-slot serialization (flock/queue) beyond the advisory lock + GitHub queue — if a tighter
      guarantee is wanted, file it as a gap.

**`main` triggers builds; branch-triggered + tarball alternatives exist and are tagged**

- [ ] (k1) **`main` triggers GCP + AWS image builds.** `deployment-service/cloudbuild.yaml` (GCP Artifact Registry,
      `asia-northeast1-docker.pkg.dev`) + `buildspec.aws.yaml` (ECR) both build, run QG inside the image
      (`quality-gates.sh --no-fix --quick`), and push. Cloud Build triggers configured via
      `scripts/setup-cloud-build-triggers.sh`. Confirm trigger inventory:
      `gcloud builds triggers list --region=<region>` (read-only).
- [ ] (k2) **Immutable-tag provenance parity (GCP vs AWS).** `buildspec.aws.yaml` tags `:$VERSION` + `:latest`.
      `cloudbuild.yaml` must also push an immutable tag (`:$VERSION` or `:$SHORT_SHA`), not `:latest`-only — otherwise
      GCP rollbacks/audit lose provenance. Grep:
      `rg -n ":latest|SHORT_SHA|_VERSION|TAG_NAME" deployment-service/cloudbuild.yaml`. (2026-06-01 baseline: GCP pushes
      `:latest`-only — provenance asymmetry, AMBER.)
- [ ] (k3) **Branch-triggered builds are supported for hotfix / fast-dev cycles.** Cloud Build supports manual /
      branch-scoped triggers (`cloudbuild.yaml` "Manual trigger" header; `setup-cloud-build-triggers.sh`). Confirm a
      documented way to build an image off an arbitrary branch without going through `main`.
- [ ] (k4) **Tarball path is the local-code alternative AND tagged-as-such.** `create-code-tarballs.sh` writes both a
      mutable `{repo}-code.tar.gz` and a **SHA-pinned `{repo}-code@{sha}.tar.gz` + `{repo}-code@{sha}.manifest.json`**
      sibling manifest. Grep:
      `rg -n "@\{?sha|manifest.json|allow-dirty-tarball" deployment-service/scripts/vm/create-code-tarballs.sh`.
- [ ] (k5) **Tarball path blocks dirty trees by default.** `create-code-tarballs.sh` refuses a dirty tree unless
      `--allow-dirty-tarball` (audit-logged, emergency-only). Grep:
      `rg -n "allow-dirty-tarball|dirty" deployment-service/scripts/vm/create-code-tarballs.sh`.

**Dirty-tree reconciliation across hosts**

- [ ] (l1) **FF-pull + git-status crons exist and are cross-platform.** `scripts/dev/slot-cron-ff-pull.sh` (FF-only,
      skips dirty/ahead/diverged) + `scripts/dev/slot-git-status-report.sh` (POSTs drift to orchestrator). Both present
      and referenced by `verify-slot-host-symmetry.sh`.
- [ ] (l2) **No 9-hour-old uncommitted WIP on any slot.** Spot-check the orchestrator Fleet tab / git-status reports: no
      slot worktree dirty for >1 working session (the Commit+Push+Flip HARD RULE applies to interactive operator slots
      too). Operator-judgment check.

### E2E Cross-Cutting Verification

- (e2e-batch-live) **Batch-live round-trip**: pick one (venue, data_type) pair, run batch adapter → confirm manifest row
  → run live adapter → confirm same schema row. Requires only one working adapter pair, not all.
- (mock-upstream) **Independent audit**: cross-cutting audits MUST be runnable with `CLOUD_MOCK_MODE=true` to test
  infrastructure, error classification, and isolation patterns without real cloud access.

## Success Criteria

- All 7 VM/GCS checklist items (a–g) GREEN
- No zombie VMs (zombie watchdog returns empty list)
- verify-slot-host-symmetry.sh exits 0
- QG exits 0 for deployment-service

**CI/CD pipeline contract GREEN (h–l):**

- quickmerge is sentinel-gated, never force-pushes, and auto-PRs to staging (h1–h5)
- **Every active repo** has `quality-gates-v2` required on BOTH `main` and `staging`, force-push disabled, and
  `enforce_admins` on — 0 repos on retired v1, 0 repos `none` (i1–i4)
- Full-workspace cross-repo SIT runs (not skips) and gates promotion (j2–j3)
- Both GCP and AWS builds push an immutable version/sha tag + run QG-in-image (k1–k2)
- Tarball path is SHA-pinned + manifest-stamped and blocks dirty trees by default (k4–k5)
- Dirty-tree FF-pull + git-status crons live on every slot host; no stale-WIP slots (l1–l2)

## Output Format

Result file at `plans/audit/results/infrastructure_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date       | Result file                                                                                                     | Status                                                                                                                  |
| ---------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| 2026-06-01 | [infrastructure_master_audit_2026_06_01.md](../results/infrastructure_master_audit_2026_06_01.md)               | First CI/CD-contract run — RED on branch-protection consistency (i)                                                     |
| 2026-06-17 | [cicd_pipeline_vs_plans_drift_audit_2026_06_17.md](../results/cicd_pipeline_vs_plans_drift_audit_2026_06_17.md) | Pipeline↔plans drift audit — 0 live regressions; 25 drift findings (3 need a decision, mostly doc/SSOT lag) for triage |
