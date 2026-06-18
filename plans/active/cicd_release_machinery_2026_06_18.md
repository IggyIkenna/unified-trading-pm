---
title: CI/CD Release Machinery — semver, version surface, workflow sprawl, watchers + self-healing, gh-rate
name: cicd_release_machinery_2026_06_18
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
created: 2026-06-18
status: active
locked_by: live-defi-rollout
locked_since: 2026-06-18
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 9.6
parent_consolidation: cicd_docs_and_consolidation_2026_06_18
source:
  - semver_version_bump_skip_ci_promotion_block_2026_06_09 (consolidated)
  - cicd_workflow_sprawl_audit_2026_06_10 (consolidated)
  - gh_rate_budget_reduction_2026_06_10 (consolidated)
  - ci_pipeline_self_healing_gaps_2026_06_11 (consolidated)
  - ci_incident_findings_2026_06_09 (consolidated)
  - cicd_contract_hardening_2026_06_01 (release + alert-triage subset)
---

> **Consolidated 2026-06-18** (see `cicd_docs_and_consolidation_2026_06_18`). **SSOT:**
> `codex/08-workflows/ci-cd-flow.md`
>
> - `CICD-WORKFLOW-CATALOG.md`. The biggest bucket. Zero open items dropped. **Cross-source dedup applied:**
>   `cicd_contract_hardening` "Tier 5a–5d" (#37–40) were exact restatements of the `sprawl` consolidation items → kept
>   once (under Sprawl); the self_healing **G10** `staging-to-main` promotion-freeze P0s moved to
>   `cicd_promotion_pipeline` (promotion-flow owner); the AR-lag-metric duplicate (self_healing L582≡L585) collapsed to
>   one.

# CI/CD Release Machinery

**Scope.** Everything that versions, fans out, and keeps the pipeline self-healing: semver-agent + the manifest version
surface, the workflow-template sprawl/consolidation, the watcher/auto-recovery fleet, gh-rate budget, and alert-triage.

## Open work

### semver + version surface

- [ ] [SCRIPT] P1. Lossy dispatch queue — make `update-repo-version` records loss-proof (verified-live root cause).
      (semver)
- [ ] [SCRIPT] P2. Decouple SIT-harness hygiene from cascade validity (route harness lint to a fix-task, not a cascade
      block). (semver)
- [ ] [SCRIPT] P2. Retry-cap is alert-only — teach the watcher to diff the failing-slice log + dispatch a fix on cap.
      (semver)
- [ ] [SCRIPT] P2. Action-pin existence gate — resolve `uses:@ref` vs tags pre-rollout (the node24 phantom-tag class).
      (semver)
- [ ] [PROCESS] P3. Audit how a lint-red commit reached SIT LDR (the QG-before-commit miss). (semver)
- [ ] [SCRIPT] P2. Fleet rollout — semver-agent bounded-scan + Option-C to 23 repos (confirmed on 2; 21 unswept).
      (cicd_contract_hardening #6)
- [ ] [SCRIPT] P2. Add the `required_approving_review_count>0` flag to `verify_branch_protection_check_names.py`
      (audit-coverage gap). (cicd_contract_hardening #18)

### Workflow sprawl / consolidation (absorbs cicd_contract_hardening Tier 5a–5d)

- [ ] [SCRIPT] P2. Delete stale `tab/*` branches fleet-wide (13–21/repo; the tab-mirror is gone, the branches remain).
      (sprawl)
- [ ] [SCRIPT] P3. Fold `sit-starvation-detector.yml` into `sit-debounce-trigger.yml`. (sprawl ≡ contract_hardening #37;
      composes with the SIT auto-redispatch in cicd_sit_and_fleet)
- [ ] [SCRIPT] P3. Merge `ci-status-reconciler` + `ci-failure-watcher` into one `ci-health.yml`. (sprawl ≡
      contract_hardening #38)
- [ ] [SCRIPT] P3. Consolidate the `main-backmerge` drift-tick + `promotion-lag-monitor` into one branch-health monitor.
      (sprawl ≡ contract_hardening #39)
- [ ] [SCRIPT] P3. Extract a shared `agent-runner.yml`; collapse `conflict-resolution-agent` into
      `escalate-to-orchestrator`; migrate the paid-API agents to the VM orchestrator. (sprawl ≡ contract_hardening #40)

### Watchers + self-healing

- [ ] [WORKFLOW] P2. Build/validate the image on the `staging→main` PR head — the REAL deploy gate (must land before any
      main-required build check). (self_healing G5)
- [ ] [BUILD-FIX] P3. Decide the AWS ECR live-target — reconcile TF↔live or retire (gates the two superseded
      AWS-build-as-main-gate items below). (self_healing G5)
- [ ] [INFRA] P3. (optional) Make the GCP `…-live-defi-rollout` build also opt-in (operator-decision). (self_healing G5)
- [ ] [WORKFLOW] P2. `ci-failure-watcher` event-driven path (don't rely solely on the throttled cron). (self_healing
      G3b)
- [ ] [WORKFLOW] P2. Event-driven trigger for the v2-never-reported recovery (cron stays as the backstop). (self_healing
      G9b)
- [ ] [WORKFLOW] P2. Watchdog/alert for a stale `promotion_quarantine` + clean-merge (the deadlock signature;
      auto-recover shipped, the alert did not). (self_healing G7)
- [ ] [ORCHESTRATOR] P3. `ao-self-pull.sh` — restart on a stale process (not just on the FF transition; observed
      2026-06-16). (self_healing G3)
- [ ] [SCRIPT] P2. Surface a published-vs-required AR lag metric in `promotion_lag_monitor` / the dashboard (primitive
      ready; the L582≡L585 duplicate collapsed here). (self_healing G9a)
- [ ] [UI] P2. deployment-ui Repos-CI `working`/`pending` state per repo (orchestrator half shipped; UI render
      remaining). (self_healing G4)
- [ ] [SCRIPT] P2. One-off recovery audit — diff `wip-preserve/*` + reflog vs LDR per repo for silently-dropped commits.
      (self_healing G2)
- [ ] [WORKFLOW] P3. Name the missing backmerge file in the Tier-C runaway breaker's page (residual of the
      presence-audit). (self_healing G6)

### Alert-triage + visibility

- [ ] [SCRIPT] P2. Debounce `FEATURE_GREEN ↔ FAILING` ci-status flap alerts (N-tick suppression).
      (cicd_contract_hardening #24)
- [ ] [WORKFLOW] P2. Dashboard alert-parity — flag a staging head with ZERO check runs (composes with a
      failure-injection matrix). (cicd_contract_hardening #33)
- [ ] [WORKFLOW] P2. Persist failures must be VISIBLE — emit `::warning` on a ledger-write failure (bucket exists; the
      warning-emit does not). (cicd_contract_hardening #34)
- [ ] [SCRIPT] P2. CI-watcher — suppress the by-design `staging-lock-check` `locked` repository_dispatch "failure" (stop
      paging on a normal lock exit). (cicd_contract_hardening #7)
- [ ] [SCRIPT] P2. Alert when a slot `[skip:dirty]`s for > N consecutive ff-pull ticks (observability gap). (ci_incident
      F2)
- [ ] [SCRIPT] P3. CI dep-clone fallback — prefer the manifest-pinned tag over upstream `main` (the in-flight-rename
      gap). (ci_incident F4)
- [ ] [SCRIPT] P3. Add a tier-bulk-clone helper for `readiness-verifier` (NICE-TO-HAVE). (ci_incident F1)

### Workflow doc-truth cleanup (NEW — surfaced by the 2026-06-18 51-workflow read)

- [ ] [SCRIPT] P3. Fix workflow comment-vs-cron drift: `cloud-build-failure-watcher` header "15 min" vs cron `*/30`;
      `ci-status-reconciler` "10 min" vs `*/15`; `ldr-ci-monitor` "30-min tick" vs hourly; `publish-package` self-labels
      "Reusable workflow" with no `workflow_call`. (drift audit)
- [ ] [SCRIPT] P3. Drop stale "Telegram alert" comments / `send_telegram()` names (impl is Slack; Telegram retired
      2026-06-02) in: `secret-health-check`, `cassette-drift-check`, `plan-notification`, `agent-audit`,
      `overnight-dead-man-switch`, `fix-approval-timeout`, `cold-storage-cleanup`. (drift audit)
- [ ] [BUG?] P2. **VERIFY then fix:** `conflict-resolution-agent.yml` has a **duplicate `env:` key** in the dispatch
      step (the 2nd clobbers the 1st → GH_PAT/REPO_NAME/PR_NUMBER dropped); if real, the escalation dispatch fires with
      empty creds. (drift audit)
- [ ] [BUG?] P2. **VERIFY then fix:** `hotfix-mode.yml` does a bare `git push` (no rebase-retry) inside the shared
      `manifest-update` group — can lose a non-fast-forward race that `update-repo-version` (×5 retry) survives. (drift
      audit)
- [ ] [BUG?] P2. **VERIFY then fix:** `rollout-action-ref.yml` pins/commits `quality-gates.yml` (the **v1** filename)
      while the live check is `quality-gates-v2`; confirm it isn't re-pinning a retired workflow file fleet-wide. (drift
      audit)

### gh-rate budget + dep hygiene

- [ ] [INFRA] P2. Token-pool split for the promote/monitor Actions (same-repo read-only → `GITHUB_TOKEN`; promoters
      still on PAT). (gh_rate)
- [ ] [INFRA] P3. Firestore write-through for `reconcile-release-tags` (the last unmigrated poller). (gh_rate)
- [ ] [DEPS] P2. Fleet pip-lock hygiene — bump the vulnerable `pip` floor in 18 repos (ignore-covered but floors not
      applied). (cicd_contract_hardening #4)
- [ ] [DEPS] P2. **TRACKED-FOR-REMOVAL:** drop the aiohttp `--ignore-vuln` block when a patched aiohttp ships that vcrpy
      supports (standing operator pin). (cicd_contract_hardening #11)

### Operator-gated

- [ ] [OPERATOR] P2. vm-0 slot headroom / Overnight Dead Man Switch — operator look. (ci_incident F3)
- [ ] [OPERATOR] P2. Uninstall the Vercel GitHub App (UI-only; the code side is already clean — composes with the
      cicd_sit_and_fleet uts-ui closure). (cicd_contract_hardening #36)

## Verify-and-flip (likely shipped — confirm, then close)

- [ ] [VERIFY] P3. features-service `pyyaml >=6.0.0 → >=6.0.1` alignment — staged + QG-green, blocked only on a
      transient UAC dirty-dep; confirm it landed + flip. (gh_rate)

## Done on consolidation (no longer open)

- ~~Codex SSOT — fix ci-cd-flow.md tab-mirror / approve-handler docs~~ — **DONE 2026-06-18** as part of the Phase-1c
  ci-cd-flow.md refresh (33bad466c). (cicd_contract_hardening #41)

## Closed on consolidation (premise superseded — not carried)

- Make `plan-health-gate` a REQUIRED status check on PM main — CLOSED: the gate is already verified-green; only an
  operator ruleset-PATCH pends (BLOCKED-OPERATOR, not code). (cicd_contract_hardening #14)
- self_healing G5 — AWS CodeBuild webhook `PUSH ^main$` filter — CLOSED: TF↔live diverged + blocked on the AWS-build
  decision; superseded by the "build on the staging→main PR head" REAL item above. (self_healing G5)
- self_healing G5 — add a build check to `main` `required_status_checks` — CLOSED: BLOCKED-DESIGN (deadlocks the fleet,
  no PR-head build); superseded by the PR-head-gate item. (self_healing G5)
- self_healing G9a — wire `assert_deps_published_to_ar.py` into the prod image build + the `[~]` hard-BLOCK canary —
  CLOSED: the canary was REMOVED from `staging-to-main` (wrong gate; dev resolves deps from sibling clones, not AR);
  re-homed/deferred to the not-yet-started image-build cutover. (self_healing G9a)

## Continuous verification

semver: zero stranded version-bump dispatches (the queue is loss-proof). Sprawl: the ~51 workflows trend down as the
consolidations land. Self-healing: a stuck promotion PR auto-recovers without a worker; a ledger-write failure is
VISIBLE. The 3 BUG? items are each verified (real → fixed; not-real → closed with the finding).
