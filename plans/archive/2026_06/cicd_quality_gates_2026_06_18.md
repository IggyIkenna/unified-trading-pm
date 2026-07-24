---
doc_type: plan
title: CI/CD Quality Gates — quickmerge, quality-gates.sh, local↔CI parity, worktree ship discipline
summary:
status: superseded
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-18
parent_epic: infrastructure_master
assigned_vm: harsh_pc
locked_by: live-defi-rollout
locked_since: 2026-06-18
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
parent_consolidation: cicd_docs_and_consolidation_2026_06_18
source:
  [
    qg_commit_quality_boundary_and_slot_ff_push_2026_06_03 (consolidated),
    ci_local_qg_parity_2026_06_08 (consolidated),
    worktree_ldr_unification_2026_06_08 (consolidated),
    cicd_contract_hardening_2026_06_01 (quality-gates subset),
  ]
---

> **⚠️ SUPERSEDED 2026-06-24 → [cicd_consolidated_remaining_2026_06_24.md](cicd_consolidated_remaining_2026_06_24.md)**
>
> The REMAINING open work from this plan is migrated to the consolidated CI/CD SSOT above, with its decision rationale
> preserved in that plan's **Decision Log (D1–D10)**. This plan is retained as the historical record — its DONE items +
> full narrative stay readable here. **Its open checkboxes have been neutralized to plain bullets** so the orchestrator
> backlog reads remaining CI/CD work from the consolidated plan ONLY (no double-count). Do NOT re-activate items here —
> work them in the consolidated plan.

> **Consolidated 2026-06-18** (see `cicd_docs_and_consolidation_2026_06_18`). **SSOT:**
> `/codex/08-workflows/ci-cd-flow.md` (the two-pass model, the QG sentinel, Path-B) + `CICD-WORKFLOW-CATALOG.md`. Zero
> open items dropped.

# CI/CD Quality Gates

**Scope.** The local quality boundary and the path to the integration branch: `quickmerge` two-pass + the
`.qg_last_passed_sha` / content sentinel, local↔CI byte-parity, and the Path-B per-slot worktree ship discipline.

## Open work

### Local ↔ CI parity + QG mechanics

- [SCRIPT] P1. Fix any non-SIT-delta divergence in the local↔CI matrix to byte-identical (the drive-to-parity catch-all;
  most root-causes closed, the catch-all stays). (ci_local_qg_parity)
- [SCRIPT] P2. QG dep-clone ref-determinism — resolve all deps at the same ref (no mixed-ref clone).
  (cicd_contract_hardening #23; composes with the LDR→staging drain verify in cicd_promotion_pipeline)
- [INFRA] P2. Churn-protection: idempotent plan-inventory regen + manifest-canonical-form + a `prettier --check` gate
  (three named writers still churn the worktree). (cicd_contract_hardening #2)
- [x] ✅ [SCRIPT] P1. e2e-testing editable self-install — add package-discovery to `pyproject.toml` (QG hygiene).
      (cicd_contract_hardening #1) — e2e-testing@23424ff | changed `[tool.setuptools.packages.find] include = []` →
      `[tool.setuptools] packages = []`; bypasses flat-layout autodiscovery that caused "Multiple top-level packages"
      error on `uv pip install -e .`; QG green.
- [x] ✅ [SCRIPT] P2. Wave-1 accommodation cleanup — revert the gate-loosenings now that the fleet is green.
      (cicd_contract_hardening #8) — PM@7adfefec9 (centralize PYSEC-2024-277/2025-183/2026-161 to fleet base) |
      e2e-testing@33549fe (MAX_DURATION env-override + remove centralized CVEs) | features-service@8e11b2e4
      (MAX_DURATION env-override + remove centralized CVE comment block)
- [SCRIPT] P3. Remove now-redundant local PYSEC-2024-277/2025-183/2026-161 entries from remaining repos:
  alerting-service, client-reporting-api, ml-service, system-integration-tests, trading-agent-service,
  unified-trading-api, unified-trading-library, greeks-service, strategy-service. (cicd_contract_hardening #8 follow-up)

### Path-B worktree ship discipline (worktree_ldr finish)

- [DOCS] P2. Rewrite AO `worker.md` + the boot-prompt `branch` fallback off the retired `tab/<op>/N` model.
  (worktree_ldr)
- [SCRIPT] P3. Prune vestigial tab-branch code in the slot scripts (keep the identity-prefix; careful surgery,
  documented-harmless no-ops). (worktree_ldr)
- [INFRA] P2. AO drift-tick is staged on LDR, inert until the agent-orchestrator LDR→main promotion lands — activate it
  then. (worktree_ldr)
- [INFRA] P2. E2e smoke: force a merge-conflict PR → auto-recover + escalate → VM Path-B worker (the closing
  verification; archives the section when green). (worktree_ldr)

### Cron / infra residuals

- [x] ✅ [SCRIPT] P1. `orphan-ping-audit` 4h local crontab — add a self-pull (Cloud Run copy exempt). (qg_commit L399) —
      PM@aa65d40a3 | added `K_SERVICE`-guarded `git pull --ff-only` at top of `audit_ping_orphans.sh`; Cloud Run exempt
      (clones fresh); lifecycle header added.
- [OPS] P0. AWS-VM half — verify `ROOT_PM`/`SLOT_DIR` + crons + not-stranded (Harsh-laptop half done; must run on the
  VM). (qg_commit L435/L441)
- [DESIGN] P3. LATER — crons self-pull from a QG-v2-gated ref (successor hardening; the self-pull already removed the
  foot-gun). (qg_commit L452)
- [CICD] P2. deployment-service CodeBuild BUILD exit 127 (uv/image not found) — live infra red, non-blocking (CodeBuild
  not required). (qg_commit L604)
- [x] ✅ [SCRIPT] P2. Finish the codex-not-a-separate-repo cleanup — `major-bump-approval.yml` write-back +
      `setup-workspace` clone remain. (qg_commit L808) — PM@8676d86 | fixed broken `unified-trading-codex/` runtime
      paths in `compute-epic-readiness.py` (WORKSPACE_ROOT→PM_ROOT, REPOS_DIR/EPICS_DIR now resolve to
      `unified-trading-pm/codex/`) and stale default in `check-repo-readiness.py` (`_PM_ROOT / "codex"`).

### Docs / SSOT hygiene (from the 2026-06-18 `docs/repo-management/` reconciliation)

- [DOCS] P2. Migrate `docs/repo-management/CI-CD-FLOW.md`'s unique bootstrap/venv/dependency-alignment/mock-infra
  content → `/codex/05-infrastructure/workspace-setup.md` (currently an 8-line stub), correcting the stale sync-to-main
  / force-push / three-tier bits to as-built (LDR-trunk); then delete `CI-CD-FLOW.md` (it's bannered NOT-the-SSOT in the
  meantime).
- [DOCS] P3. Repoint the ~18 residual references off the 4 retired CI/CD docs (`CI-CD-FLOW.md` / `docs/ci-cd-ssot.md` /
  `version-cascade-flow.md` / `sync-to-main-flow.md`) → `/codex/08-workflows/ci-cd-flow.md` across `.cursor/rules/*.mdc`
  (cicd-setup, ci-rollout-ownership, dependency-install-protocol, dependency-alignment-and-setup-flow,
  single-repo-vs-workspace-setup, prettier-docs-formatting, quality-gates-propagation-risk) +
  `codex/05-infrastructure/{cicd-setup,README,new-repo-setup}.md` +
  `scripts/{workspace/workspace-bootstrap.sh, repo-management/sync-all-to-main.sh, repo-management/README-ALIGNMENT-AND-SETUP.md}`;
  drop dead `§7`/`§2` anchors. The retired-doc stubs self-redirect, so this is cleanliness, not correctness.

## Verify-and-flip (likely shipped — confirm, then close)

- [x] ✅ [VERIFY] P3. uac `cassette_orphan_checker` intermittent xdist flakiness — CONFIRMED root-fixed 2026-06-23: the
      checker iterates `sorted()` throughout (`cassette_orphan_checker.py:81/87/195/256`; `set()` usages are
      membership-only, not order-dependent output) and the deterministic-sibling root-fix landed uac@f7627f8e
      (`test(sit): skip cross-repo workspace invariants in per-repo CI (no siblings)`). 18 tests, `tmp_path`-isolated;
      no xdist/random/shared-global state. (cicd_contract_hardening #19)

## Closed on consolidation (premise superseded — not carried)

- `[~]` Make tab branch names globally unique (precondition for fleet mirror) — CLOSED: SUPERSEDED-BY-PATH-B (tab
  branches + the tab-mirror are retired). (qg_commit L184)
- `[~]` Semantic cross-plan conflict-detector — CLOSED: SUPERSEDED →
  `orchestrator_agent_type_oversight_coverage_2026_06_17` (cross-link already in-body). (qg_commit L796)
- [x] ✅ [SCRIPT] P2. **Fix the STALE `unified-cloud-interface` reference in the QG cloud-SDK check.**
      `scripts/quality-gates-base/base-service.sh:1072` logs _"Direct cloud SDK imports found (route through
      unified-cloud-interface instead)"_ — but `unified-cloud-interface` is NOT a live repo (absorbed into UTL;
      `get_storage_client`/`get_secret_client` now live in `unified_trading_library.cloud_interface`). Update the
      message to name the current package, and review the stale `--glob '!**/unified-cloud-interface/**'` dead-repo
      exclusions (base-service.sh:1462 + STEP 5.12b § "No hardcoded gs:///s3:// outside unified-cloud-interface"). Edit
      the PM base template, then `rollout-quality-gates-unified.py` fleet-wide. Repo: unified-trading-pm. Provenance:
      2026-06-19 operator spotted the stale ref in the deployment-api QG output. — PM@923ee2e3f | QG-green; updated 5
      messages in base-service.sh (STEP 5.5/5.11/5.12b) + 2 messages in base-library.sh; removed dead
      `!**/unified-cloud-interface/**` glob exclusion; fleet-wide via sourcing (no rollout needed).

## Continuous verification

Local↔CI: a `quality-gates.sh --no-fix` green tree → the staging-PR `quality-gates-v2` is green with zero non-SIT-delta
divergence. Path-B: no slot is stranded behind LDR (the `slot_drift_check.py` invariant holds fleet-wide).

## 2026-06-22 — pytest-cov + xdist coverage-measurement bug (spurious fail-under)

Discovered on market-tick-data-service: QG coverage gate FAILED reporting "total of 46.4% < fail-under=79.0", but the
SAME run's `coverage.xml` (which combines the xdist workers) showed the REAL coverage = **83.95%** (only 1 genuinely
untested file). Root cause: pytest-cov + xdist `-n auto` (2 workers) — the `--cov-report=xml` combines worker data
correctly, but the terminal `--cov-fail-under` enforcement reads PARTIAL (controller-only) data → spurious low number →
false gate failure. ALL repos set `[tool.coverage.run]` with NO `parallel`/`concurrency`, so this is LATENT fleet-wide
(a bad xdist split can spuriously fail any repo's coverage gate). Fix = `parallel = true` +
`concurrency = ["thread","multiprocessing"]` + `sigterm = true` in `[tool.coverage.run]` so the combine is deterministic

- the fail-under reads combined data.

* [x] ✅ [CICD] P1. **mtds coverage parallel-combine fix SHIPPED** (market-tick-data-service@4a514cf, on LDR) — QG now
      green (coverage reads the real 83.95%, was spuriously failing at 46.4%). Verified: full QG PASSED 78s.
* [x] ✅ [CICD] P1. **Roll the coverage parallel-combine config fleet-wide** — DONE 2026-06-22. Added
      `parallel`/`concurrency`/`sigterm` to `[tool.coverage.run]` in ALL 19 python coverage-gated repos (+ mtds@4a514cf
      pre-dispatch = 20/20); every one verified carrying `parallel = true` on `origin/live-defi-rollout`, each shipped
      from a `quality-gates.sh --no-fix`-green tree with real combined coverage ≥ its `fail_under`. Per-repo shas:
      unified-trading-api@62a6d48 · greeks-service@85ac7ab (new run-block) · fund-administration-service@15627f3 ·
      alerting-service@35b57ff · execution-service@da24dc0 · strategy-service@e6d48a43 · client-reporting-api@0a60e18 ·
      ibkr-gateway-infra@bd3991a · batch-live-reconciliation-service@2fa6c9c · unified-api-contracts@2f89f5c ·
      ml-service@249da21 · trading-agent-service@722608c · system-integration-tests@b059ee2 ·
      unified-trading-library@a060eaa3 · deployment-service@f8cddf0 · features-service@070aa1a2 ·
      market-data-processing-service@65b6954 · instruments-service@363b123d · deployment-api@a6e880e. No real-debt repo
      (every repo's real coverage cleared its floor). greeks added (no prior run-block but coverage-gated + xdist —
      within the GOAL's intent). No canonical pyproject coverage template exists, so per-repo. Provenance: mtds spurious
      46.4% coverage-gate failure 2026-06-22.

## 2026-06-22 — mtds HTTP-timeout-hardening WIP (preserved, ship-blocked by file-size)

A stale prior-session WIP in the mtds slot (bounded `aiohttp.ClientTimeout(sock_connect=15,sock_read=60,total=120)`
across ~41 DeFi/handler/adapter fetch paths — `backfill_vm_silent_worker_stall_watchdog P3`) was reconciled best-of-both
onto current LDR (1 conflict resolved) + preserved on `origin/wip-preserve/mtds-http-timeouts-2026-06-22`. All 5160
tests pass, but it can't quickmerge-ship: the additive lines push 4 files over 900L (gas_fee_handler 909, polymarket
904, lending_indices 904, umi_tick_provider 902) + 2 functions over 50L (gas_fee `_collect_solana_live` 52L,
`_collect_btc_fees` 54L). The clone is now CLEAN + current (the operator's "dirty + behind LDR" is resolved); the WIP is
safe on the branch.

- [x] ✅ [MTDS] P3. **Ship the mtds HTTP-timeout-hardening WIP** — DONE 2026-06-22 (market-tick-data-service@adee3ebc).
      **Finding:** the timeout HARDENING itself was ALREADY LIVE on `live-defi-rollout` (41 files had
      `aiohttp.ClientTimeout(sock_connect=15, sock_read=60, total=120)`, 37 `ClientSession(` sites already passed
      `timeout=`) — a prior session had reconciled it onto LDR. The `wip-preserve/mtds-http-timeouts-2026-06-22` branch
      is STALE (based on an old LDR: its files were +45/+188/+51/+163 larger than current LDR, which had since
      refactored/shrunk them — so the "4 files >900L / 2 funcs >50L" blocker was an artifact of the stale base, NOT real
      on current LDR). So the restore-from-WIP / size-trim steps were moot; the remaining described deliverable was the
      **DRY extraction**, which shipped: created `market_tick_data_service/_http_timeouts.py` (single SSOT
      `BACKFILL_HTTP_TIMEOUT`) + migrated all 40 duplicated `_BACKFILL_HTTP_TIMEOUT` definitions to import it. Net −78
      lines; zero `_BACKFILL_HTTP_TIMEOUT` left; QG green (basedpyright clean, all tests pass — no-behavior-change
      constant move). Provenance: stale-WIP reconcile 2026-06-22 + DRY follow-through.

## Progress Log — 2026-06-22 autonomous rollout (coverage parallel-combine + mtds HTTP-timeout WIP)

> Append-only journal for the `/autonomous` dispatch executing the two 2026-06-22 P1/P3 items. The loop's handoff doc
> (no separate summary file). A compressed future-me resumes from here.

**Target set (TASK 1 — coverage parallel-combine).** 19 python repos carry a coverage gate + run xdist `-n auto`
(fleet-wide via `base-service.sh [3]`). 18 have an existing `[tool.coverage.run]` block; **greeks-service** has a
coverage GATE (`[tool.coverage.report] fail_under=70`) + xdist but NO `[tool.coverage.run]` block — equally vulnerable
to the spurious-partial-fail bug. **DECISION (rule 12f, within documented intent):** the dispatch's literal filter is
"has `[tool.coverage.run]`" but the operator's stated GOAL is "every repo's coverage gate reads COMBINED xdist data" →
greeks qualifies → include it (add a minimal `[tool.coverage.run]` parallel-combine block; no `branch`/`source` so the
measured % is unchanged). mtds already shipped (@4a514cf) — skipped. No canonical pyproject coverage template exists in
`scripts/propagation/` (the plan's "best via template" is aspirational) → per-repo edits.

**Why adding the config is always safe (never newly-breaks a green repo):** combined coverage ≥ partial
(controller-only) coverage always (union of covered lines), so the fix only moves the terminal fail-under number UP
toward the true value. Any currently-GREEN repo has terminal ≥ fail_under ⟹ real ≥ fail_under ⟹ stays green. The only
repos where real < fail_under are ones ALREADY red today (real debt) — there I revert the edit + record the repo, never
ship a misleading `fix(ci)` commit.

**Per-repo verification protocol:** edit `[tool.coverage.run]` → `quality-gates.sh --no-fix` → compare terminal coverage
to `coverage.xml` line-rate → if QG exit 0 (real ≥ fail_under): quickmerge ship `pyproject.toml`, record sha. If
coverage.xml real < fail_under: revert edit, record as real-debt (issue doc). If QG red for a NON-coverage reason:
revert edit, record as blocked+reason (do not ship).

**Shipped shas (TASK 1) — 18/19 (incl. mtds pre-dispatch):**

- market-tick-data-service@4a514cf — already shipped pre-dispatch (the proven fix).
- unified-trading-api@62a6d48 (real 80.6% ≥77) — pilot
- greeks-service@85ac7ab (new `[tool.coverage.run]` block — special)
- fund-administration-service@15627f3 (no-`branch` source-block — special; real 83.9%)
- alerting-service@35b57ff (real 80.3% ≥76)
- execution-service@da24dc0 (real 84.0% ≥70)
- strategy-service@e6d48a43 (real 84.9% ≥74)
- client-reporting-api@0a60e18 (real 73.9% ≥70)
- ibkr-gateway-infra@bd3991a (real 88.2% ≥51)
- batch-live-reconciliation-service@2fa6c9c (real 87.8% ≥80)
- unified-api-contracts@2f89f5c (real 94.24% ≥94)
- ml-service@249da21 (real 82.7% ≥70)
- trading-agent-service@722608c (real 73.5% ≥70)
- system-integration-tests@b059ee2 (real 9.09% ≥2)
- unified-trading-library@a060eaa3 (real 90.1% ≥80)
- deployment-service@f8cddf0 (real 72.3% ≥70)
- features-service@070aa1a2 (real 85.6% ≥70)
- market-data-processing-service@65b6954 (real 88.2% ≥85)

Verified: all 18 carry `parallel = true` on `origin/live-defi-rollout` pyproject.toml.

**Concurrency lesson (recorded so it doesn't recur):** running the base libraries (UAC/UTL) edits CONCURRENTLY with
their dependents tripped each dependent's quickmerge dirty-deps guard (a dirty base dep). One sub-agent even committed
UAC's in-flight pyproject as "inherited WIP" (harmlessly — the content was the same parallel-combine edit). FIX going
forward: ship a base library (UAC, UTL) ALONE first, commit it, THEN fan out its dependents. UAC@2f89f5c + UTL@a060eaa3
were re-verified clean (6-insertion pyproject only). deployment-service was re-shipped after UAC settled.

**2 repos initially BLOCKED — both turned out to be STALE-CLONE artifacts (NOT real reds), now RESOLVED + SHIPPED:**

- **instruments-service** → SHIPPED @363b123d (real 90.7% ≥88). The 3 `test_enumerate_expected_universe_v2.py` failures
  (`future` vs `futures_chain`) had ALREADY been fixed on LDR earlier 2026-06-22 (UAC@c0a15a50 `market_data_categories`
  - IS@cf2e9a21/f6d479f8 enumerator wiring); the first sub-agent's clone was simply behind / its editable-UAC stale. A
    `git pull --ff-only` (IS + the editable UAC) made the tests pass; QG green; shipped. Not a real heartbeat red.
- **deployment-api** → SHIPPED @a6e880e (real 82.0% ≥70). The "6 codex-compliance violations > 5" was stale (the gate is
  now V=4, within the ratchet tolerance of 5). The real (transient) blocker was a LOCAL-ONLY **version-alignment** nag —
  `version-alignment-gate.sh` flags the PM `workspace-manifest.json` `versions{}` lag vs `origin/main` (UTL/UAC/
  deployment-service version-bumped on `main` by the semver-agent promoting MY OWN rollout's repos). That gate
  `return 0`s under CI (`GITHUB_ACTIONS`/`CLOUD_BUILD`) — it does NOT run in the server `quality-gates-v2`. Shipped with
  `SKIP_VERSION_ALIGNMENT=true` (the gate's own designed escape hatch); all substantive gates (tests, coverage,
  basedpyright, lint, bandit, codex-compliance) ran fully and passed. Not a real red.

**TASK 1 COMPLETE — 20/20 repos carry the parallel-combine config on LDR; no real-debt; no permanent blocker.**

### Final report (rule 9) — both tasks DONE 2026-06-22

**TASK 1 (P1) — coverage parallel-combine fleet-wide: DONE, 20/20.** Every python coverage-gated repo now reads COMBINED
xdist worker data in its terminal `--cov-fail-under`, so a worker-split can't spuriously fail the gate (the mtds 46.4%
incident class is closed fleet-wide). Shipped 19 repos this session + mtds@4a514cf pre-dispatch; each from a
`--no-fix`-green tree with real combined coverage ≥ floor; all verified `parallel = true` on `origin/live-defi-rollout`.

**TASK 2 (P3) — mtds HTTP-timeout hardening: DONE.** The hardening itself was already live on LDR; completed the WIP's
DRY intent by extracting the 40 duplicated `_BACKFILL_HTTP_TIMEOUT` constants into `_http_timeouts.py`
(market-tick-data-service@adee3ebc, −78 lines, QG green).

**Forced-tradeoff / judgment decisions made under autonomy (rule 1/2/12f):**

1. **Included greeks-service** though the dispatch's literal filter was "has `[tool.coverage.run]`" (greeks had only a
   coverage `[report]` gate + xdist, no `run` block) — the operator's stated GOAL ("every repo's coverage gate reads
   combined xdist data") clearly covers it; added a minimal `run` block. greeks@85ac7ab.
2. **deployment-api shipped with `SKIP_VERSION_ALIGNMENT=true`** — the version-alignment gate is LOCAL-only (it
   `return 0`s under CI; it does NOT run in the server `quality-gates-v2`) and was tripping on transient PM-manifest
   version churn caused by MY OWN rollout's promotions (semver-agent bumped UTL/UAC/deployment-service on `main`). All
   substantive gates ran fully and passed. Not a quality bypass.
3. **Did NOT restore the stale `wip-preserve` branch for TASK 2** — it was based on an old LDR (files +45..+188 larger),
   so a blanket checkout would have reverted LDR's refactors. The hardening was already live; only the DRY extraction
   remained, applied fresh to current LDR.

**Process lesson recorded:** never edit a base library (UAC/UTL) concurrently with its dependents — a dirty base trips
every dependent's quickmerge dirty-deps guard (wave-C incident; one sub-agent even committed UAC's in-flight pyproject
as "inherited WIP", harmlessly). Ship base libs ALONE first, then fan out dependents.

**Nothing left for the operator to pick up.** No DEFERRED / BLOCKED items. Both checkboxes flipped with shas.
