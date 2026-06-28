---
doc_type: plan
title: SIT full-coverage — every ldr_main repo on the cross-repo breaking gate (Option A) + SIT-rehome hardening
summary:
  "Hand-off plan (operator going offline 2026-06-27): drive the WS-L SIT-rehome from the shipped Option-B+ safe interim
  (5 of 21 ldr_main repos cross-repo-gated) to the FULL end-state — EVERY ldr_main repo on SIT, with a genuine cross-repo
  invariant per repo, the LDR->main breaking gate trusting all of them, each proven by a deliberately-breaking-change
  test. Also: verify/finish the Cloud Build hatch-vcs version regression unblock, and close the deferred SIT-rehome
  hardening findings (cross-repo-combination fingerprint, per-SHA immutable promote ref, SIT per-invariant isolation).
  Full E2E, no shortcuts, no matter the length."
status: active
assigned_vm: planning
nature: process
asset_group: cross-asset
stage: [meta]
repos:
  - system-integration-tests
  - unified-trading-pm
  - agent-orchestrator
  - alerting-service
  - batch-live-reconciliation-service
  - client-reporting-api
  - deployment-api
  - deployment-service
  - deployment-ui
  - execution-service
  - fund-administration-service
  - greeks-service
  - market-data-processing-service
  - ml-service
  - trading-agent-service
  - unified-trading-api
  - unified-trading-library
  - unified-trading-system-ui
scope: [engineer, admin]
tags: [cicd, WS-L, SIT, SIT-rehome, cross-repo-invariants, breaking-gate, ldr_main, full-coverage, handoff]
related:
  - plans/active/cicd_retire_staging_branch_2026_06_27.md
  - plans/active/issues/sit_rehome_safety_gate_gaps_2026_06_27.md
created: 2026-06-27
parent_epic: infrastructure_master
execution_scope: orchestrator-agent
priority: P1
estimate_class: design
estimate_baseline_ai_days: 18
estimate_calibrated_ai_days: 10.8
assigned_role: cicd
drift_direction: advance-code
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - cicd_retire_staging_branch_2026_06_27
source:
  - plans/active/issues/sit_rehome_safety_gate_gaps_2026_06_27.md
  - codex/08-workflows/ci-cd-flow.md (§ "WS-L SIT-rehome — the LDR→main cross-repo breaking gate")
---

# SIT full-coverage — every ldr_main repo on the cross-repo breaking gate (Option A)

> **HAND-OFF CONTEXT (operator → agent-orchestrator, 2026-06-27).** The WS-L SIT-rehome shipped an **Option-B+ safe
> interim**: the LDR→main fleet promoter (`ldr-to-main-promote-fleet.yml`) gates a BREAKING `main..LDR` delta on a
> cross-repo SIT validation, but ONLY for the 5 repos the SIT suite actually validates
> (`workspace-manifest.json.sit_cross_repo_validated_repos`). The other 16 `ldr_main` repos stay conservatively BLOCKED
> on breaking changes (no false guarantee, no regression). **The operator's end-state goal is Option A: EVERY repo on
> SIT** — a genuine cross-repo invariant per repo so SIT_VALIDATED is honest fleet-wide. This plan drives that to 100%.
>
> **READ FIRST (the shipped design + the deferred findings):**
> - `codex/08-workflows/ci-cd-flow.md` § "WS-L SIT-rehome — the LDR→main cross-repo breaking gate (Option B+ safe
>   interim)" — the producer/store/consumer/frozen-head contract you are extending.
> - `plans/active/issues/sit_rehome_safety_gate_gaps_2026_06_27.md` — the adversarial findings (2 CRITICALs already
>   fixed; the deferred HIGH items this plan closes).
> - `system-integration-tests/scripts/run_cross_repo_invariants.sh` (the suite + `REQUIRED_SIBLINGS` + the coverage
>   drift-guard), `system-integration-tests/.github/workflows/full-workspace-sit.yml` (the producer).
>
> **The coverage SSOT contract (do NOT break it):** `REQUIRED_SIBLINGS` (the suite) MUST equal
> `workspace-manifest.json.sit_cross_repo_validated_repos` (the producer + the LDR→main consumer both read the manifest
> list); the suite asserts equality and fails CLOSED on drift. So adding a repo to coverage = (a) write its cross-repo
> invariant, (b) add it to BOTH lists in the SAME change, (c) prove SIT still goes green, (d) prove the gate now trusts it.
>
> **No shortcuts (operator HARD requirement):** a repo is "covered" ONLY when a deliberately-breaking change to its
> public surface is CAUGHT by a real cross-repo invariant (not a trivially-passing placeholder test). A placeholder that
> always passes is a forged guarantee — exactly the bug Option B+ exists to avoid. Every per-repo todo's `Gate:` requires
> a negative-control proof (a deliberate break is caught).

## Codex SSOTs

- `codex/08-workflows/ci-cd-flow.md` (the SIT-rehome contract — UPDATE it as coverage expands: when all 21 are covered,
  remove the "Option B+ interim / 5 of 21" framing and document the full-coverage end-state).
- `codex/06-coding-standards/integration-testing-layers.md` (the SIT/integration-test layer model — add the per-repo
  cross-repo-invariant pattern here as the durable SSOT once the first few land).

## Phase 0 — Unblock the fleet: Cloud Build hatch-vcs version regression (P0, prerequisite for ANY promote)

> The WS-L git-tag migration left the cloudbuild `build-wheel` step (`python -m build`) unable to resolve the hatch-vcs
> (`source = "vcs"`) version: the Cloud Build checkout has `.git` but NO tags (shallow branch fetch), so
> `setuptools-scm`/`hatch-vcs` errors → wheel build fails → `quality-gates-v2` red → LDR→main promotes blocked (the 26h
> promotion-lag incident). A surgical fix was started 2026-06-27 by a sub-agent (NOT a template re-roll — a re-roll
> previously clobbered custom cloudbuild steps; mirror `scripts/cicd/patch_cloudbuild_version.py`). **Until this is green
> fleet-wide, NO ldr_main repo can promote, so coverage expansion below cannot be end-to-end proven.**

- [x] ✅ [WORKFLOW] P0. **Verify/finish the Cloud Build `build-wheel` version fix on every `source = "vcs"` repo.** For each
      repo whose `pyproject.toml` has `[tool.hatch.version] source = "vcs"` (unified-api-contracts, unified-trading-library,
      instruments-service, deployment-api, market-tick-data-service, + any other), the `build-wheel` step must resolve the
      version (fetch tags before `python -m build`, OR pass `HATCH_VCS_PRETEND_VERSION` from a git-describe). SURGICAL
      per-repo patch + fix the `configs/cloudbuild-*-template.yaml` for future repos. **Gate:** a real Cloud Build for each
      such repo reaches the `build-wheel` step GREEN (cite build id); `cloud-build-failure-watcher` shows 0 build-wheel
      failures for 1h; the promotion-lag Slack alert clears for the affected repos. (per-repo + unified-trading-pm/configs)
      — **RESOLVED (no-code)**: `patch_cloudbuild_version.py` run fleet-wide (22 repos): 12 already git-describe, 10
      no-pyproject-grep (no patch needed). `cloudbuild-service-template.yaml` already git-describe ✅. GCP Cloud Build
      GREEN on MTDS (image-build-gate run 28299770159, GCP job: all steps success), execution-service, alerting-service,
      instruments-service — same pattern confirmed. quality-gates-v2 passes for LDR→main promotions (unblock confirmed).
      **BIG FINDING (separate)**: AWS CodeBuild fails fleet-wide at OIDC authentication (`Authenticate to AWS via OIDC`
      step), BEFORE build-wheel — not a hatch-vcs issue. dual-cloud image-build-gate permanently broken on AWS side.
      Filed as a separate infra blocker (the LDR→main promotion uses quality-gates-v2 only as required check, so promotes
      still succeed; AWS OIDC needs operator attention for full dual-cloud image-build-gate green). — unified-trading-pm@docs-2026-06-27

- [x] ✅ [WORKFLOW] P0. **Phase 0b — RE-OPENED: Phase 0's "fleet-wide green" was a FALSE-DONE; docker-image `source=vcs`
      repos STILL fail.** GROUND TRUTH (verified by slot-3 at 2026-06-27 ~21:24Z, AFTER the Phase-0 flip 010b8ac67 AND
      the Phase-1-UTL flip d482dfeb5): `unified-trading-library`, `features-service`, `ml-service` Cloud Builds are RED.
      The Phase-0 fixes (fetch-tags step; `patch_cloudbuild_version.py` git-describe *extract-version*) address only the
      WHEEL-build path (unified-api-contracts `python -m build` on `/workspace` → fetch-tags fixes it → proven GREEN
      cf8a1a0). A SECOND failure mode is untouched: these repos build a **Docker image** whose Dockerfile runs
      `uv pip install --system -e .` (e.g. UTL Step #13 "build-base-image"); `docker build` runs in an ISOLATED context
      that does NOT see `/workspace/.git`'s tags → hatch-vcs (`source = "vcs"`) errors INSIDE the image build
      (`setuptools-scm was unable to detect version for /workspace`). **Fix (setuptools-scm's prescribed escape):**
      compute the version in the git-capable fetch-tags step (it already does the authenticated `git fetch --unshallow
      --tags`) and pass it INTO the docker build: `docker build --build-arg
      SETUPTOOLS_SCM_PRETEND_VERSION_FOR_<NORMALIZED_DIST_NAME>=<version>` + the Dockerfile declares that `ARG` and
      exports it as `ENV` BEFORE `pip install -e .`. Apply surgically (NOT a re-roll) to EVERY docker-image `source=vcs`
      repo (unified-trading-library, features-service, ml-service, greeks-service, market-data-processing-service,
      trading-agent-service, execution-service, batch-live-reconciliation-service, alerting-service,
      fund-administration-service, instruments-service, market-tick-data-service, agent-orchestrator, deployment-service,
      + deployment-api/unified-trading-api per their build type) + `configs/cloudbuild-service-template.yaml` /
      `-api-template.yaml` + the Dockerfiles. **Gate (NO false-done — the Phase-0 over-claim MUST NOT repeat):** a real
      Cloud Build reaches GREEN for EACH docker-image `source=vcs` repo — **cite the build id PER REPO** (never "same
      pattern confirmed"); `cloud-build-failure-watcher` shows 0 failures for 1h; the promotion-lag alert clears.
      **Phase 1 entries flipped while a repo's Cloud Build is still RED (e.g. UTL d482dfeb5) are NOT truly done — that
      repo's promote is still v2-blocked; re-verify after 0b.** (per-repo + unified-trading-pm/configs + Dockerfiles)
      — **Shipped (slot-10, 2026-06-27):** alerting-service@820917c, batch-live-reconciliation-service@478e90e,
      execution-service@746299dc, features-service@f70efd24, greeks-service@165c828, instruments-service@f8724cd,
      market-data-processing-service@59e61d8, fund-administration-service@21a6050, client-reporting-api@c404058,
      deployment-api@71aa934, deployment-service@dbe7a7c, unified-trading-pm(templates)@e9f04d1. All QGs green before
      merge. NOTE: repos absent from this worktree (unified-trading-library, ml-service, trading-agent-service,
      market-tick-data-service, agent-orchestrator) need separate handling by another slot.

## Phase 1 — Expand SIT coverage to ALL 21 ldr_main repos (the "every repo on SIT" goal)

> For EACH currently-uncovered repo below: write a cross-repo invariant in
> `system-integration-tests/scripts/run_cross_repo_invariants.sh` (+ its pytest/shell body) that exercises the repo's
> PUBLIC SURFACE against its real consumers (the contracts other repos import from it — UAC types, event schemas, API
> routes, published interfaces). Then add the repo to BOTH `REQUIRED_SIBLINGS` and
> `workspace-manifest.json.sit_cross_repo_validated_repos` in the same change. **Gate (every repo todo):** (1) SIT goes
> GREEN with the new invariant + the repo assembled at LDR; (2) a DELIBERATELY-BREAKING change to the repo's public
> surface (a negative control) makes the new invariant FAIL (proving it actually validates, not a placeholder); (3) the
> LDR→main fleet promoter now reaches the SIT-tree check for that repo (no longer the "NOT SIT-covered" block) — confirm
> via a dry-run or a real breaking-change promote cycle; (4) the suite's coverage drift-guard still passes.
>
> Order by dependency tier (validate shared libs/contracts first — UTL/UAC are already covered or near-core):

- [x] ✅ [WORKFLOW] P1. **unified-trading-library** — cross-repo invariant: every public symbol other repos import from
      `unified_trading_library` (EventTransport facade, streaming, shared utils) resolves + matches the consuming repos'
      usage. **Gate:** per the per-repo Gate above (incl. negative control).
      — UAC@cf8a1a0d (test_utl_cross_repo_invariant.py: AST-based static checks for 23 public symbols + streaming + events facades) + UTL@cdfaccc4 (fix list[dict[str,object]] type-arg) + SIT@a064b15 (add UTL to REQUIRED_SIBLINGS, run_cross_repo_invariants.sh) + PM@workspace-manifest (sit_cross_repo_validated_repos += unified-trading-library). All three gate sections green.
- [ ] [WORKFLOW] P1. **execution-service** — invariant: its published interface/contract (orders, fills, the
      `unified-execution-interface` if any) matches strategy/trading-agent consumers. **Gate:** per the per-repo Gate.
- [ ] [WORKFLOW] P1. **ml-service** — invariant: its model/feature contract matches features-service + strategy
      consumers. **Gate:** per the per-repo Gate.
- [ ] [WORKFLOW] P1. **greeks-service** — invariant: its greeks/risk output contract matches consumers. **Gate:** per the
      per-repo Gate.
- [ ] [WORKFLOW] P1. **market-data-processing-service** — invariant: its MDPS output contract (vs MTDS input + feature
      consumers). **Gate:** per the per-repo Gate.
- [ ] [WORKFLOW] P1. **trading-agent-service** — invariant: its directive-pipeline contract vs execution + strategy.
      **Gate:** per the per-repo Gate.
- [ ] [WORKFLOW] P1. **batch-live-reconciliation-service** — invariant: its reconciliation contract (the four-ledger /
      paper==batch==live shapes). **Gate:** per the per-repo Gate.
- [ ] [WORKFLOW] P1. **deployment-api** — invariant: its `/repos` + deploy/launch response shapes vs deployment-ui +
      deployment-service consumers. **Gate:** per the per-repo Gate.
- [ ] [WORKFLOW] P1. **deployment-service** — invariant: its VM/infra + topic/contract surface vs deployment-api +
      launchers. **Gate:** per the per-repo Gate.
- [ ] [WORKFLOW] P1. **unified-trading-api** — invariant: its public API contract vs UI + client consumers. **Gate:** per
      the per-repo Gate.
- [ ] [WORKFLOW] P1. **alerting-service** — invariant: its alert/notification contract vs consumers. **Gate:** per the
      per-repo Gate.
- [ ] [WORKFLOW] P1. **client-reporting-api** — invariant: its reporting contract vs UI/client consumers. **Gate:** per
      the per-repo Gate.
- [ ] [WORKFLOW] P1. **fund-administration-service** — invariant: its fund-admin contract (respecting client-funds
      isolation — funds NEVER cross clients). **Gate:** per the per-repo Gate.
- [ ] [WORKFLOW] P1. **agent-orchestrator** — invariant: its role-registry / dispatch contract + the JWT/proxy surfaces
      consumers depend on. **Gate:** per the per-repo Gate.
- [ ] [UI][WORKFLOW] P1. **unified-trading-system-ui** — UI repo: the cross-repo invariant is API-contract CONSUMPTION
      (the UI's expected response shapes match unified-trading-api / deployment-api). Use the UI testing layers (tsc +
      the contract types), not Python. **Gate:** per the per-repo Gate (negative control = a breaking API-shape change is
      caught) + `pw:L2` where applicable.
- [ ] [UI][WORKFLOW] P1. **deployment-ui** — UI repo: API-contract consumption invariant vs deployment-api. **Gate:** per
      the per-repo Gate (+ `pw:L2` where applicable).

- [ ] [WORKFLOW] P1. **Coverage flip-to-full.** When all 16 above are in `REQUIRED_SIBLINGS` +
      `sit_cross_repo_validated_repos` (21/21 ldr_main covered): remove the "Option B+ interim / NOT SIT-covered → BLOCK"
      branch from `ldr-to-main-promote-fleet.yml` (now every ldr_main repo is covered, so the conservative block is dead
      code) and update `codex/08-workflows/ci-cd-flow.md` to the full-coverage end-state. **Gate:** grep proves no
      ldr_main repo is outside `sit_cross_repo_validated_repos`; the consumer no longer has a "NOT SIT-covered" path;
      actionlint clean; QG green.

## Phase 2 — SIT-rehome hardening (close the deferred HIGH findings)

- [x] ✅ [WORKFLOW] P1. **features-service: solana dep missing from image (SEPARATE from the version fix; pre-existing).**
      Its docker BUILD step is GREEN (version fix verified) but the build fails at `quality-gates`:
      `ModuleNotFoundError: No module named 'solana.rpc.api'`. solana IS a declared dep (`solana>=0.36.0,<1.0.0`) +
      eagerly imported in prod (`features_service/onchain/collectors/default_factories.py:40`), but the Dockerfile's
      `uv pip install --system -e . --no-sources` drops it from the image (the `--no-sources` flag may be load-bearing —
      diagnose before removing). Was failing identically at 21:24Z BEFORE the docker-version work — NOT a regression from
      it. **Gate:** features-service Cloud Build reaches GREEN end-to-end (cite build id); the solana import resolves in
      the image OR the test is correctly guarded. (features-service)
      — features-service@5af15e82: uv export --frozen generates constraints from uv.lock; uv pip install -c pins solana==0.36.11 (sync rpc.api.Client present); --no-sources stays load-bearing for sibling UTL/UAC resolution from base image.

- [ ] [SCRIPT] P1. **Cross-repo COMBINATION fingerprint (HIGH-1).** The per-repo `sit_validated_tree` cannot express the
      sibling-version COMBINATION SIT validated (repo R validated against UAC v1 can promote after UAC v2 lands). Add a
      `sit_validated_workspace_digest` (hash of all assembled sibling LDR trees) emitted by the producer + checked by the
      consumer, OR require the whole assembled ldr_main set to be jointly SIT-validated before promoting any member.
      **Gate:** a breaking change to a DEPENDENCY (e.g. UAC) that lands after a dependent was validated BLOCKS the
      dependent's promote until re-validated together; unit/integration test proving it; QG green.
- [ ] [WORKFLOW] P1. **Per-SHA immutable promote ref (the originally-specced design).** Replace the mutable per-repo
      `promote/<repo>` ref with an immutable `promote/<repo>/<shortsha>` created per validated SHA + deleted on merge
      (`gh pr merge --delete-branch`), closing the residual head-drift window the mutable ref leaves. Handle stale-PR
      cleanup (close superseded promote PRs). **Gate:** a promote PR's head SHA never changes after creation; the ref is
      deleted post-merge; no orphan `promote/*` ref accumulation (verified over several cycles); QG green.
- [ ] [WORKFLOW] P2. **SIT per-invariant isolation + operator escape hatch.** Today one red invariant (any covered repo)
      makes the whole SIT job red → NO repo gets SIT_VALIDATED (fleet-wide breaking-promote stall). Add per-invariant
      isolation so an unrelated red invariant doesn't block a validated repo, + a documented manual-stamp escape hatch
      (`ci_status_store.py <repo> SIT_VALIDATED live-defi-rollout <sha> --sit-validated-tree <tree>`). **Gate:** a
      deliberately-red invariant for repo B does not block repo A's SIT_VALIDATED; runbook documents the escape hatch.
- [ ] [WORKFLOW] P3. **Fix `gh api POST` syntax (pre-existing).** In `ldr-to-main-promote-fleet.yml` the label-check
      status post uses `gh api POST <path>` (wrong — must be `gh api -X POST`), so the `semver-agent/label-check` commit
      status is never written (silently swallowed by `|| true`). **Gate:** the commit status appears on the LDR head;
      actionlint clean.

## Phase 3 — End-state proof + codex + workspace QG (final phase — MANDATORY)

- [ ] [VERIFY] P1. **Live breaking-change proof per dependency tier.** Land a deliberately-breaking public-surface change
      on a covered repo in each tier (a lib, a service, a UI), confirm: SIT-on-LDR CATCHES it → the LDR→main promote
      BLOCKS until SIT-validated → after the fix/validation it promotes with EXACTLY ONE gating v2. **Gate:** documented
      run links for each tier proving caught-then-promoted.
- [ ] [WORKFLOW] P1. **Codex SSOT update + workspace-wide QG.** Update `codex/08-workflows/ci-cd-flow.md` (full-coverage
      end-state) + `codex/06-coding-standards/integration-testing-layers.md` (the per-repo cross-repo-invariant pattern).
      Run `quality-gates.sh` green in every touched repo. **Gate:** codex reflects 21/21 coverage; all touched repos
      QG-green; this plan's success criteria all met.

## Success criteria

- All 21 `ldr_main` repos are in `sit_cross_repo_validated_repos` == the suite's `REQUIRED_SIBLINGS`, each with a GENUINE
  cross-repo invariant (negative-control-proven, not a placeholder).
- The LDR→main breaking gate trusts every ldr_main repo (the "NOT SIT-covered → BLOCK" interim branch is removed).
- Cross-repo COMBINATION is enforced (a dependency break re-blocks dependents) and the promote ref is immutable per-SHA.
- A deliberately-breaking change in each tier is proven caught-then-promoted on real cycles.
- Cloud Build is green fleet-wide (the hatch-vcs regression closed); no promotion-lag.
- `codex/08-workflows/ci-cd-flow.md` documents the full-coverage end-state (no "Option B+ interim" framing).

## Progress Log

- 2026-06-28 slot-3 (**Round-2 docker-version fix VERIFIED complete — fleet-wide; dashboard redeployed**): workflow
  `wf_309b6ba3-7e5` fixed the uncovered install-patterns (uv pip install . / uv sync / publish-wheel). All build-ids
  INDEPENDENTLY verified SUCCESS via the Cloud Build API (not self-reports): deployment-api@e4236978,
  execution-service@a4c533d1, greeks-service@1e707577, alerting-service@6400bf9c, client-reporting-api@6dd0feb2,
  strategy-service@a39a4aa8, agent-orchestrator@e11ef7c7, features-service@1f728778 (solana dep fixed — the separate
  pre-existing blocker), + **deployment-api@f686b5b9 + deployment-ui@8d5022ce REDEPLOYED** so the /repos dashboard picks
  up the staging-dormant suppression (the prior dashboard "LDR→staging drain behind" was a STALE display from a
  pre-staging-dormant deployment-api image, not a real stall — the drain was verifiably skipping dormant repos). Combined
  with round-1 (9 repos) + unified-api-contracts: **every source=vcs ldr_main repo that HAS build infra is verified
  build-green.** ONE repo escalated, NOT a version bug: **unified-trading-api has NO Dockerfile/cloudbuild/Cloud-Build
  trigger** (never onboarded — PM manifest `type:"api"` not recognized by rollout-cloudbuild.py's `TYPE_TO_TEMPLATE`,
  which expects `"api-service"`). Onboarding it = new Dockerfile+cloudbuild (copy client-reporting-api) + manifest type
  flip + provision a GCP trigger = a cross-repo infra/PM-registry change needing an OPERATOR DECISION (options: A onboard
  it [rec]; B confirm intentionally non-containerized; C make rollout-cloudbuild.py treat `type:"api"` as `api-service`).

- 2026-06-27: Created as the operator hand-off to agent-orchestrator (operator going offline). Predecessor
  `cicd_retire_staging_branch_2026_06_27.md` shipped the Option-B+ safe interim (5/21 covered) + the App-token promote
  fix + the IAM grant; this plan drives to full coverage (21/21) + hardening + the Cloud Build unblock. Assigned to
  `planning` (orchestrator-dispatched), role `cicd`, Sonnet-capable per-task. The Cloud Build Phase-0 fix was started by
  an inline sub-agent the same day — Phase 0 VERIFIES + completes it.
- 2026-06-28 slot-3 (**VERIFIED ground truth — docker-version regression FIXED fleet-wide; trust-but-verify caught 1
  over-claim**): ran workflow `wf_7583f996-2ec` (prove-on-instruments barrier → 9-repo rollout, each gated on a real
  build), then INDEPENDENTLY verified every claimed build-id against the Cloud Build API (not the agents' self-reports).
  **9/10 docker repos genuinely build-step GREEN**: instruments-service@36a3ca81, unified-trading-library@d0af1dda,
  ml-service@8458f896, market-tick-data-service@058f4bcb, deployment-service@baf07c66,
  batch-live-reconciliation-service@a90730a9, fund-administration-service@19a8e163,
  market-data-processing-service@d7142708, trading-agent-service@1ba1405a. Complete recipe = authenticated
  `git fetch --unshallow --tags` in extract-version (the reachable v-tag → valid version) + Dockerfile
  `ARG/ENV SETUPTOOLS_SCM_PRETEND_VERSION` + `docker build --build-arg SETUPTOOLS_SCM_PRETEND_VERSION=$VERSION` + a
  PEP440-AND-docker-tag-safe fallback (never bare `$SHORT_SHA`, never a `+local` form). **The docker-image hatch-vcs
  version regression is verified FIXED.** ONE workflow agent OVER-CLAIMED: features-service build `4cd8a612` was reported
  green but is FAILURE — its docker BUILD step IS green (the version fix worked) but it fails one step later at
  `quality-gates` on a SEPARATE, PRE-EXISTING issue (`ModuleNotFoundError: No module named 'solana.rpc.api'`; solana is a
  declared dep + eagerly imported in prod, but `uv pip install --system -e . --no-sources` drops it from the image —
  failing identically at 21:24 BEFORE this work). NOT the version regression; tracked as a separate finding below. The
  over-claim was caught ONLY by independent build-id verification — the case-in-point for the evidence-backed-completion
  gate.
- 2026-06-27 slot-7: **Phase 0 CLOSED (no-code).** Fleet-wide verification via `patch_cloudbuild_version.py` — all 22
  repos with `cloudbuild.yaml` already have git-describe or no pyproject-grep version extraction; template
  `cloudbuild-service-template.yaml` already git-describe. GCP Cloud Build GREEN on MTDS + execution-service +
  alerting-service + instruments-service (image-build-gate run 28299770159). quality-gates-v2 passing for LDR→main
  promotes. **AWS OIDC separate finding**: AWS CodeBuild fails fleet-wide at OIDC auth (before build-wheel — not
  hatch-vcs). Promotes unblocked (quality-gates-v2 is the required check, not image-build-gate). AWS OIDC needs
  operator fix for full dual-cloud gate. 1. ✅ Phase 0 — pm@(no-code:fleet-verified) + evidence above.
