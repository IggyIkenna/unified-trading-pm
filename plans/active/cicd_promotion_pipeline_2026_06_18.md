---
title: CI/CD Promotion Pipeline (LDR → staging → SIT → main → image) + ci_status SSOT
name: cicd_promotion_pipeline_2026_06_18
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
created: 2026-06-18
status: active
locked_by: live-defi-rollout
locked_since: 2026-06-18
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 6.4
parent_consolidation: cicd_docs_and_consolidation_2026_06_18
source:
  - ldr_trunk_promotion_decoupling_2026_06_10 (consolidated)
  - ci_status_firestore_side_store_2026_06_10 (consolidated)
  - ldr_tarball_auto_refresh_2026_06_17 (consolidated)
  - cloud_build_router_aws_parity_2026_06_10 (consolidated)
  - promotion_queue_conflict_wall_pileup_2026_06_17 (consolidated)
  - cicd_contract_hardening_2026_06_01 (promotion-flow subset)
---

> **Consolidated 2026-06-18** from the plans above into one lean tracker (see `cicd_docs_and_consolidation_2026_06_18`).
> **Pipeline shape SSOT:** `codex/08-workflows/ci-cd-flow.md` (the as-built mermaid + branch model) + the drill-down
> `docs/repo-management/CICD-WORKFLOW-CATALOG.md`. Each item carries its provenance. Zero open items were dropped — REAL
> → Open work; likely-shipped → Verify-and-flip; premise-superseded → Closed; AWS-parity → Deferred annex.

# CI/CD Promotion Pipeline + ci_status SSOT

**Scope.** The commit→LDR→staging→SIT→main→image flow and the `ci_status` source-of-truth that gates it: the promote
bots (`ldr-to-staging-promote` / `ldr-to-main-promote` / `staging-to-main`), the breaking-change cascade, the
Firestore-side-store ci_status migration, and the prod image build.

## Open work

### ci_status Firestore SSOT — the live core (Phases 3–4 unshipped)

- [ ] [CI] P2. Migrate `staging-backmerge-to-ldr.yml` + `main-backmerge-to-ldr.yml` ci_status readers to Firestore.
      (ci_status_firestore)
- [ ] [CODE] P2. Orchestrator dashboard / `server/` ci_status read path → Firestore collection query.
      (ci_status_firestore)
- [ ] [CODE] P2. Phase 3 consolidator (Cloud Run Job + Scheduler): writes Firestore aggregate → manifest, one
      commit/interval. (ci_status_firestore)
- [ ] [CI] P2. Phase 3 — drop the git-commit half of the dual-write; retire `ci-status-reconciler.yml`.
      (ci_status_firestore)
- [ ] [VERIFY] P2. Phase 4 — full drain → ZERO ci_status commits; gates behave identically; dashboard live.
      (ci_status_firestore)
- [ ] [SCRIPT] P3. `_align_workspace_manifest.py` + `generate_workspace_dag.py` → read snapshot/store.
      (ci_status_firestore)
- [ ] [CODE] P3. `set_status` explicit txn `max_attempts` / retry on Aborted/DeadlineExceeded (Finding 2).
      (ci_status_firestore)
- [ ] [DOCS] P2. Phase 4 — codex SSOT + CLAUDE.md one-liner (ci_status is Firestore-backed). (ci_status_firestore)

### Promote-flow correctness

- [ ] [WORKFLOW] P0. **`staging-to-main` must promote non-bumping QG-green content** (not only repos in
      `staging_commits`) — bug #11; non-breaking staging merges are currently INVISIBLE to the drain (only the manual
      fallback works). (cicd_contract_hardening #35 ≡ self_healing G10; tracked HERE as the promotion-flow owner)
- [ ] [WORKFLOW] P0. Break the bottom-up dep-order deadlock — a T0 lib stuck `STAGING_GREEN` on chore content blocks the
      cone; verify once #11 lands. (cicd_contract_hardening, self_healing G10)
- [ ] [WORKFLOW] P1. Fix the `Merge staging → main` step shell bug (`& ready_set`, missing `--title/--body`) + smoke.
      (self_healing G10)
- [ ] [SCRIPT] P2. Durable fix for the staging-unlock / check-staging-lock refresh gap — re-run open-PR checks after
      lock clears. (cicd_contract_hardening #20)
- [ ] [SCRIPT] P2. Lock writes `[skip ci]` → backmerge skips → stale `staging_status` in the LDR copy; reconcile
      non-quickmerge readers. (cicd_contract_hardening #21)
- [ ] [WORKFLOW] P2. Batch a breaking fan-out into ONE cascade over the union of dependents (stop per-consumer
      serialization). (cicd_contract_hardening #29)
- [ ] [SCRIPT] P1. **Unblock the last UAC-0.24.0 dep-update consumer — `e2e-testing` PR #333 v2 red on TID251 ratchet.**
      The UAC-0.24.0 fan-out drained 10/11 once the honest_coverage adapter-contract baseline was fixed (PM@`d3ce018f9`,
      see `data_feed_sla_registry_and_active_self_healing_2026_06_19.md`); `e2e-testing` is the lone straggler. Repo:
      **e2e-testing**. Failure: `quality-gates-v2` `lint-codex` slice → STEP 5.95 `check_ruff_rule_ratchet.py` →
      `e2e-testing/tid251 > baseline 5` (direct `google.cloud`/`boto3` in `scripts/sports/`:
      `live_arb_scanner.py`/`odds_api_live_feed.py`/`prediction_market_scanner.py`/`run_weekly_pipeline.py`).
      **Gotchas:** (1) plain `ruff --select TID251` shows CLEAN (repo pyproject has no banned-api table) — reproduce
      with `.venv/bin/python scripts/quality_gates/check_ruff_rule_ratchet.py --workspace-root <ws> --scope e2e-testing`
      (uses `ruff --isolated` + its own banned-api `--config`); (2) local QG may block first on "Version alignment
      failed" (stale tag) → `git fetch origin --tags --force`; (3) e2e **LDR is already at baseline (tid251=5)** and
      `agt-20cba0` landed `02912ad` routing google.cloud→UTL, so FIRST measure the dep-update branch TIP — it may just
      be stale/needs regenerating vs current staging rather than new violations. **Fix** (if real): route remaining
      sites through `from unified_trading_library.cloud_interface import get_storage_client, get_secret_client` — NEVER
      raise `ruff_rule_ratchet_baseline.yaml`; land on LDR via quickmerge so the regenerated dep-update branch inherits
      it. **Collision:** `agt-20cba0` + the dep-update flow are actively on this branch —
      `git log origin/staging..dep-update/unified-api-contracts-0.24.0` first, coordinate, never force-push their WIP;
      prefer the LDR root-cause fix over editing the dep-update branch. Done =
      `check_ruff_rule_ratchet --scope e2e-testing` ≤ baseline on LDR/staging AND PR #333 `quality-gates-v2` green.
- [ ] [SCRIPT] P2. Consumer re-pin breaking verdict — run `detect_breaking_change.py` on the consumer surface (re-pins
      still unconditionally `feat!`). (cicd_contract_hardening #31)
- [ ] [SCRIPT] P2. Review `cloud-build-router.yml` membership in the `manifest-update` concurrency group (non-replayable
      payload). (cicd_contract_hardening #27)
- [ ] [SCRIPT] P3. Collapse local `verify_service_token` copies onto the UTL factory (4 repos). (cicd_contract_hardening
      #3)

### LDR-trunk decoupling tail

- [ ] [SCRIPT] P1.5. Compose with dep-clone ref-determinism — verify the LDR→staging drain resolves all deps at the
      staging ref. (ldr_trunk)
- [ ] [SCRIPT] P3. Host stale-PR / stale-checkout monitoring (Track D) — extend slot Slack monitoring. (ldr_trunk; the
      two P3 monitoring checkboxes were the same item — deduped to one)
- [ ] [INFRA] P3. Perf follow-up (NICE-TO-HAVE) — codeload tree tarball instead of git clone (needs
      `create-code-tarballs.sh` to accept an explicit SHA). (ldr_tarball)

### Operator-gated

- [ ] [OPERATOR] P3. Residual intermittent v2 `conclusion=action_required` — root is the GitHub-Settings approval toggle
      (auto-recover already self-heals the symptom). (promotion_queue)

- [ ] [INFRA] P1. **GHA runner provisioning failures block PR #501 (LDR→main drain) — investigate quota/infrastructure.
      [agt-c251c2] [DEFERRED]** Observed 2026-06-22 19:37–19:47 UTC: 5+ consecutive `quality-gates-v2` + 2+
      `ldr-to-main-promote` runs on PM repo all failed with `0 steps ran` in 1–2 seconds. Runner never starts.
      `content-gate` and all jobs show `"steps": []`. Not a YAML/code issue (YAML valid, no workflow file changes since
      last passing run `1498a12ef0` at 19:18). Not affecting other repos (UTL QG was green at 14:49). Pattern: per-repo
      transient GHA runner provisioning failure. Possible causes: GHA concurrent-job quota exhausted, runner-pool issue,
      or GitHub service degradation. PR #501 auto-merge will fire once GHA recovers + `ldr-to-main-promote` `*/15` cron
      re-triggers a passing v2. **Named successor**: this plan. Monitor `ldr-to-main-promote` and `quality-gates-v2`
      cron recovery.

## Verify-and-flip (likely shipped — confirm, then close)

- [x] ✅ [VERIFY] P3. First-use watch (normal quickmerge lands on LDR, ~15m drain auto-merges, `--hotfix` hits the lock)
      — CONFIRMED LIVE 2026-06-23: a `feat: LDR → staging (Tier C auto-drain)` run succeeded 10:32 UTC; continuous
      LDR→staging auto-merges are landing (execution-service#351, strategy-service#274). Staging-lock machinery
      (`staging-lock-check.yml` + quickmerge STAGE 1.5) present for the `--hotfix` path. (ldr_trunk)
- [ ] [VERIFY→CORRECTED 2026-06-23] P3. `quickmerge.sh` STAGE lock/status read is **NOT** cut over to
      `tier_c_promotion_gate.py` — the prior premise was inaccurate. quickmerge reads `ci_status`/`staging_status`
      **directly from `workspace-manifest.json`** (STAGE 1.5 `git show origin/main:workspace-manifest.json`; STAGE 1.7
      `repos[dep].ci_status`), which is the offline-fallback cache. The Firestore overlay
      (`tier_c_promotion_gate.py::_overlay_firestore_ci_status`, Phase-2 migrated) is consumed by the **promote bots**,
      not quickmerge (0 refs in quickmerge.sh). The local manifest read is correct-by-design as the offline fallback;
      whether quickmerge needs any further cutover is gated on the ci_status Firestore Phases 3–4 (above) — stays OPEN
      with that owner. (ci_status_firestore)
- [x] ✅ [VERIFY] P3. "Drain remaining un-promoted LDR content" / "drain to completion → STAGING_GREEN" — CONFIRMED
      2026-06-23: no stranded content fleet-wide. 22/25 repos `MAIN_GREEN`; the 3 `FEATURE_GREEN` (deployment-ui /
      market-tick-data-service / unified-trading-system-ui) show `staging...LDR` ahead_by>0 but **files:0** (the
      squash-count artifact = zero content delta, not un-drained work); staging unlocked (`breaking_pending:[]`). The
      one-time drain completed. (cicd_contract_hardening #5 ≡ #10, deduped)

## Deferred — AWS image-build reactivation annex (cloud_build_router; dormant: GCP-primary / AWS-secondary)

All 6 open `cloud_build_router_aws_parity` items are AWS dual-cloud-parity work, premised on the AWS VM fleet being
reactivated. The GCP path is canonical and live; in-image QG was **dropped** (operator 2026-06-17,
`_RUN_INIMAGE_QG:false`). **DEFERRED until the AWS fleet is reactivated** (named condition, not closed):

- [ ] [SCRIPT] P2. Author the AWS build router (mirror `cloud-build-router.yml`); decide router-in-GHA vs
      CodeBuild-native. **DEFERRED-AWS**
- [ ] [SCRIPT] P2. Mirror `notify-build-not-configured` gating into the AWS router. **DEFERRED-AWS**
- [ ] [SCRIPT] P2. `buildspec.aws.yaml` generator/template + generate fleet-wide. **DEFERRED-AWS**
- [ ] [TEST] P2. Cross-cloud parity test (same Dockerfile / QG / tag / provenance dispatch) in deployment-service QG.
      **DEFERRED-AWS**
- [ ] [SCRIPT] P3. Replace the CodeBuild PUSH webhook with router-driven starts OR document the webhook model.
      **DEFERRED-AWS**
- [ ] [DOC] P2. Codex SSOT § "Dual-cloud image builds" — router→buildspec→QG→push→provenance, both clouds.
      **DEFERRED-AWS**

## Closed on consolidation (premise superseded — not carried)

- `ldr_tarball` AWS-bucket mirror refresh — CLOSED: premised on AWS-fleet reactivation; folded into the AWS annex above.
  (ldr_tarball)

## Continuous verification

ci_status migration: `% of ci_status transitions written to Firestore` climbs to 100% (Phase 4 = zero git commits).
Promote-flow: a non-breaking staging merge reaches `main` without a manual fallback PR (bug #11 closed).
