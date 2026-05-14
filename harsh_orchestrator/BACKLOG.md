---
title: Harsh-side slot backlog
type: orchestration-backlog
status: active
locked_by: live-defi-rollout
---

# Harsh-side Slot Backlog

> Main orchestrator's dispatch queue. When a slot pings DONE, pick the top `QUEUED` item that fits the slot's capacity and mark it `DISPATCHED → slot N YYYY-MM-DD`. Agents do NOT read this file — task briefs go in LEDGER.
>
> Update cadence: mark DISPATCHED on spawn, DONE on confirmed push, add new items as they unlock.

---

## How to read this

| Field | Meaning |
|-------|---------|
| **Est** | Wall-clock per slot (not cal-AI-days) |
| **Model** | Sonnet unless marked Opus |
| **Prereq** | Must be true before dispatching |
| **Plan-ref** | File + section to read for context |

Status values: `QUEUED` · `DISPATCHED → slot N YYYY-MM-DD` · `DONE @sha YYYY-MM-DD`

---

## Tier 1 — Dispatch-ready (no cross-side blocker)

### B-001 · Phase 1 env-locking — deployment-api tarball-block
- **Status**: DONE @deployment-api@0574e9e 2026-05-14 (slot 7 — 8 unit tests pass; plan checkbox flipped)
- **Task**: Add env-aware validation in `deployment-api` to reject tarball deploy method for staging/prod (HTTP 400). `--override-tarball-block` emergency flag with audit log. Unit tests: dev allows both, staging+prod reject without override.
- **Repos**: `deployment-api`
- **Est**: 2h · **Model**: Sonnet
- **Plan-ref**: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 1

### B-002 · Phase 1 env-locking — deployment-ui env selector lock
- **Status**: DONE @deployment-api@f0c0c43+deployment-ui@2c8de22 2026-05-14 (slot 7 — tarball-from-local radio blocked for staging/prod; 18 vitest pass; plan checkbox flipped)
- **Task**: In deployment-ui, grey out / disable tarball deploy option when env selector is staging/prod. Show tooltip "tarball blocked in staging/prod — use image deploy". QG: `pnpm build` + vitest green.
- **Repos**: `deployment-ui`
- **Est**: 2h · **Model**: Sonnet
- **Plan-ref**: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 1
- **Note**: Can run parallel with B-001; both read same env config shape.

### B-003 · batch_live Tab 3 — L2 fix-batch (21 violations)
- **Status**: DONE @PM@06c6213c 2026-05-14 (slot 8)
- **Task**: 21 L2 violations across `features-service`, `strategy-service`, `market-tick-data-service` — mode-axis discipline (RuntimeMode × BatchExecutionMode misuses). Read `batch_live_symmetry_2026_05_10.md` § Tab 3 § "L2 fix-batch" for the exact file:line list. Fix each: move to seam OR unify path. Serialise commits within slot (no parallel sub-agents on same repo). Then enable L2 STEP in base-service.sh.
- **Repos**: `features-service` + `strategy-service` + `market-tick-data-service` + `unified-trading-pm`
- **Est**: 3h · **Model**: Sonnet
- **Plan-ref**: `plans/active/batch_live_symmetry_2026_05_10.md` § Tab 3
- **Prereq**: Phase 0 Cluster E slot 8 tsc done (Tab 2 UAC already on LDR ✅)

### B-004 · strategy-service 2 remaining test failures
- **Status**: DONE @strategy-service@PM@2acbd9bb 2026-05-14 (slot 9 — UTL@67c532bd propagation resolved all 4 failures; 1544 tests pass; no code change needed)
- **Task**: Slot 4 Wave 2 fixed 15/17 pre-existing failures. 2 remain (likely from `TestResolverFactoryCoverage` or `test_factory_builds_all_v1_archetypes` group). Diagnose-first: read test + code-under-test. Fix code if code drifted; fix test if test drifted from SSOT; file issue doc if ambiguous. QG green.
- **Repos**: `strategy-service`
- **Est**: 1h · **Model**: Sonnet
- **Plan-ref**: `strategy-service/tests/` (no plan-of-record; standalone fix)

### B-005 · Writegate Phase 6.9 — features-sports emission policy
- **Status**: DONE @features-service@0de7fee6 2026-05-14 (already wired by prior commits on LDR; slot 5 confirmed — no action needed)
- **Task**: Wire `publish_with_policy` at the sports live-handler write boundary in `features-service` (same pattern as Phase 6.5 batch_handler@a93dc3b4 but for sports live path). Add STRICT_FAIL seed in UAC if missing. QG green.
- **Repos**: `features-service` + `unified-api-contracts` (if seed missing) + `unified-trading-pm`
- **Est**: 2h · **Model**: Sonnet
- **Plan-ref**: `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` § Phase 6.9
- **Prereq**: UTL@67c532bd on LDR ✅

### B-006 · Phase 8.A surface-1 — service startup coverage
- **Status**: DISPATCHED → slot 4 2026-05-14 (start after Phase 0 Cluster D/E/F fully green)
- **Task**: 100% coverage target on STARTED/STOPPED/FAILED bootstrap paths. Sub-agent fan-out across 5 services (execution, risk, features, MDPS, instruments). For each: run `bash scripts/quality-gates.sh`; identify uncovered lines in `ServiceBootstrap` call path; add unit tests hitting the lifecycle events. Target: 0 uncovered lines in startup/shutdown paths.
- **Repos**: `execution-service` + `risk-and-exposure-service` + `features-service` + `market-tick-data-service` + `instruments-service`
- **Est**: 4h (sub-agent fan-out within slot) · **Model**: Sonnet
- **Plan-ref**: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 8.A surface "service startup"
- **Prereq**: Phase 0 all clusters green (QG must be clean before coverage work)

### B-007 · Phase 8.A surface-2 — manifest writer coverage
- **Status**: DISPATCHED → slot 8 2026-05-14
- **Task**: 100% coverage on `ManifestWriter.record_*` call paths in UTL. Add tests for: `record_captured` happy-path, `record_empty` with each reason taxonomy entry, `record_failed` with `attempted_at`, `record_expected_unattempted`. Verify `assert_available_at_present` fires on every `record_captured` path.
- **Repos**: `unified-trading-library`
- **Est**: 3h · **Model**: Sonnet
- **Plan-ref**: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 8.A surface "manifest writer"
- **Prereq**: Phase 0 Cluster D done (UTL test suite green)

### B-008 · Phase 8.A surface-3 — emission publisher coverage
- **Status**: DISPATCHED → slot 8 2026-05-14
- **Task**: 100% coverage on `publish_with_policy` + `_publish_emission_check` + `_resolve_policy_output_data_type` in UTL. Add unit tests: STRICT_FAIL policy blocks on mismatched output; WARN_ONLY policy logs but passes; NAN_FILL policy fills NaN correctly. Run `bash scripts/quality-gates.sh` — all tests green.
- **Repos**: `unified-trading-library`
- **Est**: 3h · **Model**: Sonnet
- **Plan-ref**: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 8.A surface "emission publisher"
- **Prereq**: Phase 0 Cluster D done

### B-009 · Phase 8.A surface-4 — kill switch + circuit breaker coverage
- **Status**: DISPATCHED → slot 5 2026-05-14 (start after Phase 0 all clusters green)
- **Task**: 100% coverage on `KILL_SWITCH_ACTIVATED` + `CIRCUIT_BREAKER_OPEN` event paths. Test: kill switch fires → no further orders emitted; circuit breaker trips on N consecutive failures → CIRCUIT_BREAKER_OPEN event emitted; deactivation re-arms. Verify: no order emitted after kill switch without explicit deactivation.
- **Repos**: `risk-and-exposure-service` + `execution-service`
- **Est**: 3h · **Model**: Sonnet
- **Plan-ref**: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 8.A surface "kill switch"
- **Prereq**: Phase 0 all clusters green

### B-010 · Phase 8.A surface-5 — validation logic coverage (per-archetype)
- **Status**: DISPATCHED → slot 3 2026-05-14
- **Task**: 90% coverage on per-archetype calc validation paths in `strategy-service`. Target: `carry_staked_basis` + `arbitrage_price_dispersion` validation branches. Sub-agent fan-out per archetype. Run `bash scripts/quality-gates.sh`.
- **Repos**: `strategy-service`
- **Est**: 4h (sub-agent fan-out) · **Model**: Sonnet
- **Plan-ref**: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 8.A surface "archetype calcs"
- **Prereq**: B-004 (remaining test failures fixed first)

### B-011 · Phase 8.A surface-6 — VM deploy script coverage
- **Status**: DISPATCHED → slot 2 2026-05-14 (start after slot 5 finishes deployment-service Cluster F + Phase 0 green)
- **Task**: 95% coverage on `deployment-service/scripts/vm/launch-*.sh` paths. Bash-level: `shellcheck` all launchers. Python-level: unit tests for singleton-lock check, zombie-watchdog dict registration, tarball-uri construction. Verify `VM_PREFIX_TO_BUCKET` dict registration for any new VM prefixes.
- **Repos**: `deployment-service`
- **Est**: 3h · **Model**: Sonnet
- **Plan-ref**: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 8.A surface "VM deploy scripts"
- **Prereq**: Phase 0 all clusters green

### B-012 · Phase 8.A surface-7 — custody + wallet signing coverage
- **Status**: DISPATCHED → slot 6 2026-05-14 (execution-service + UTL are clean; start now — no Phase 0 blocker on these repos)
- **Task**: 100% coverage on `WalletProvisioningConfig` load + `signing_surface` dispatch in execution-service. Test: CLOUD_KMS_ENCRYPTED path signs correctly; wrong config → raises loud at boot (not at trade time). Mock signing at the KMS client level (no real keys).
- **Repos**: `execution-service` + `unified-trading-library`
- **Est**: 3h · **Model**: Sonnet
- **Plan-ref**: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 8.A surface "custody + wallet"
- **Prereq**: Phase 0 all clusters green

---

## Tier 2 — Ready after Tier 1 lands

### B-013 · Phase 2 — 99%-repo deploy-ready tracking
- **Status**: DONE @deployment-api@1f22e22+deployment-ui@2dfefa1+PM@b6e58906 2026-05-14 (slot 7 — endpoint + UI tab; 19 unit tests + 6 vitest; pnpm build green)
- **Task**: New deployment-api endpoint `/api/repos/deploy-ready` — walks last 5 daily QG snapshots per repo; returns `deploy_ready: true` if all 5 green + zero P0 issue docs + no `🟡 IN-FLIGHT REFACTOR` banner. Deployment-ui panel showing per-repo readiness.
- **Repos**: `deployment-api` + `deployment-ui`
- **Est**: 3h · **Model**: Sonnet
- **Plan-ref**: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 2
- **Prereq**: B-001 + B-002 (Phase 1 env-locking done first)

### B-018 · Phase 4.A — daily QG snapshot writer + cron VM
- **Status**: DISPATCHED → slot 7 2026-05-14 (natural follow-on after B-013 DONE; write-side of deploy-ready read endpoint)
- **Task**: Author `unified-trading-pm/scripts/quality_gates/snapshot.sh` — walks all workspace repos, runs `bash scripts/quality-gates.sh --quick` per repo (parallel where possible), captures per-repo status + first error line + duration, writes `quality_gates_snapshot_YYYY_MM_DD.parquet` to `gs://${PROJECT_ID}-deployment-events/quality_gates_snapshot/`. Schema: `repo, pull_sha, qg_status, failing_step, first_error_line, duration_seconds, snapshot_at`. Wire cron VM via existing `deployment-service/scripts/vm/launch-...` pattern. Register VM prefix in `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` dict. Smoke-test snapshot on 3 repos first, then full workspace run.
- **Repos**: `unified-trading-pm` + `deployment-service` (cron VM launcher)
- **Est**: 3h · **Model**: Sonnet
- **Plan-ref**: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 4 line 1
- **Prereq**: None (B-013 read-side already shipped)

### B-014 · Phase 3 — QG ratchet STEPs enable + rollout
- **Status**: DISPATCHED → slot 8 2026-05-14 (prep now; start rollout only after B-006/B-009/B-010/B-011/B-012 all DONE)
- **Task**: Enable STEP X.N1 (tarball-env-block), X.N2 (coverage-targets-enforcement), X.N3 in `base-service.sh` template. Run rollout: `bash scripts/propagation/rollout-quality-gates-unified.py`. Verify all service repos pass with new STEPs. Commit + push per repo.
- **Repos**: `deployment-service` (base-service.sh) + all service repos
- **Est**: 2h · **Model**: Sonnet
- **Plan-ref**: `plans/active/deployment_and_qg_strategy_implementation_2026_05_13.md` § Phase 3
- **Prereq**: B-006 through B-012 (Phase 8.A surfaces passing before ratchet enables)

---

## Tier 3 — Cross-side dependency / operator decision needed

### B-015 · DeFi carry_staked_basis backtest run (paper mode)
- **Status**: DISPATCHED → slot 9 2026-05-14 (Phase 1 cross-side prereq check FIRST; launch after Ikenna ACK)
- **Task**: Run `carry_staked_basis` archetype end-to-end in paper/batch mode for 30 days. Verify P&L attribution, hedge leg fills, LST margin positions. Monitor event stream.
- **Repos**: `strategy-service` + `execution-service` + `e2e-testing`
- **Est**: 4h (launch + monitor) · **Model**: Sonnet
- **Plan-ref**: `plans/active/defi_master_2026_05_07.md` § "paper-trade gate"
- **Prereq**: DeFi pipeline green end-to-end (instruments → MTDS → features → strategy → execution); Ikenna confirms backtest start date ready

### B-016 · DeFi arbitrage_price_dispersion backtest run (paper mode)
- **Status**: DISPATCHED → slot 3 2026-05-14 (parallel with B-015; cross-side prereq check first)
- **Task**: Same shape as B-015 for `arbitrage_price_dispersion`. Parallel with B-015 if separate slots.
- **Repos**: `strategy-service` + `execution-service` + `e2e-testing`
- **Est**: 4h · **Model**: Sonnet
- **Plan-ref**: `plans/active/defi_master_2026_05_07.md` § "paper-trade gate"
- **Prereq**: Same as B-015

### B-017 · defi_recursive_borrow DESCOPE — successor plan filing (doc-only)
- **Status**: DONE @PM 2026-05-14 (slot 9 filed successor plan; slot 5 confirmed — no action needed)
- **Task**: File the post-cutover successor plan for `defi_recursive_borrow_archetypes_2026_05_10.md`. Steps: (1) annotate current plan body with descope decision ("May-23 ships archetype documented; Phase 2-3 Solidity + execution halves deferred"); (2) file `plans/active/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md` with `migrated_from:` frontmatter + migrated todos with `**MIGRATED FROM:**` provenance; (3) add successor banner to current plan; (4) rerun `python3 scripts/plans/regenerate_active_plan_inventory.py`. PM only — no code changes.
- **Repos**: `unified-trading-pm`
- **Est**: 1h · **Model**: Sonnet
- **Plan-ref**: `plans/active/defi_recursive_borrow_archetypes_2026_05_10.md` + CLAUDE.md § "Plan Archival"

---

## Dispatch log

| Date | Item | Slot | Done SHA |
|------|------|------|----------|
| 2026-05-14 | B-007 client-reporting-api B008 sweep | slot 7 | client-reporting-api@e936eb4 + PM@130dcd5e ✅ |
| 2026-05-14 | B-003 batch_live Tab 3 L2 fix-batch | slot 8 | PM@06c6213c ✅ |
| 2026-05-14 | B-001 deployment-api tarball-block | slot 7 | deployment-api@0574e9e ✅ |
| 2026-05-14 | B-002 deployment-ui env selector lock | slot 7 | DISPATCHED |
| 2026-05-14 | B-004 strategy-service 2 remaining test failures | slot 9 | strategy-service@PM@2acbd9bb ✅ |
| 2026-05-14 | B-005 Writegate Phase 6.9 features-sports | slot 5 | DISPATCHED |
| 2026-05-14 | B-017 defi_recursive_borrow successor plan | slot 5 | DISPATCHED |
| 2026-05-14 | B-007 Phase 8.A manifest writer coverage | slot 8 | DISPATCHED |
| 2026-05-14 | B-008 Phase 8.A emission publisher coverage | slot 8 | DISPATCHED |
| 2026-05-14 | B-002 deployment-ui env selector lock | slot 7 | deployment-api@f0c0c43+deployment-ui@2c8de22 ✅ |
| 2026-05-14 | B-010 Phase 8.A archetype validation coverage | slot 3 | DISPATCHED |
| 2026-05-14 | B-013 Phase 2 deploy-ready tracking | slot 7 | DISPATCHED |
| 2026-05-14 | B-005 Writegate Phase 6.9 features-sports | slot 5 | features-service@0de7fee6 ✅ (prior commits; slot 5 confirmed) |
| 2026-05-14 | B-017 defi_recursive_borrow successor plan | slot 5 | PM ✅ (slot 9 filed; slot 5 confirmed) |
| 2026-05-14 | B-006 Phase 8.A service startup coverage | slot 4 | DISPATCHED (after Phase 0 green) |
| 2026-05-14 | B-009 Phase 8.A kill switch coverage | slot 5 | DISPATCHED (after Phase 0 green) |
| 2026-05-14 | B-011 Phase 8.A VM deploy scripts coverage | slot 2 | DISPATCHED (after slot 5 + Phase 0 green) |
| 2026-05-14 | B-012 Phase 8.A custody + wallet signing coverage | slot 6 | DISPATCHED |
| 2026-05-14 | B-014 Phase 3 QG ratchet STEPs enable + rollout | slot 8 | DISPATCHED (prep now; rollout after B-006-B-012 all DONE) |
| 2026-05-14 | B-009 Phase 8.A kill switch + circuit breaker coverage | slot 5 | START (Phase 0 effectively green per operator @12:04) |
| 2026-05-14 | B-015 DeFi carry_staked_basis paper backtest | slot 9 | DISPATCHED (Phase 1 cross-side prereq check FIRST) |
| 2026-05-14 | B-018 Phase 4.A daily QG snapshot writer + cron VM | slot 7 | DISPATCHED (natural follow-on to B-013) |
| 2026-05-14 | B-010 Phase 8.A archetype validation coverage | slot 3 | strategy-service@4ede3b2 + PM@4f4df625 ✅ (93.18% coverage; 38 new tests) |
| 2026-05-14 | B-016 DeFi arbitrage_price_dispersion paper backtest | slot 3 | DISPATCHED (parallel with B-015; Phase 1 cross-side prereq check FIRST) |
| 2026-05-14 | B-013 Phase 2 deploy-ready tracking | slot 7 | deployment-api@1f22e22 + deployment-ui@2dfefa1 + PM@b6e58906 ✅ |

---

## How main updates this file

1. **Slot pings STARTED** → no change (LEDGER handles this)
2. **Slot pings DONE** → mark item `DONE @sha YYYY-MM-DD` in dispatch log; pick next QUEUED item for that slot; write LEDGER brief; update item to `DISPATCHED → slot N YYYY-MM-DD`
3. **New item unblocked** → add to appropriate Tier with prereq cleared
4. **Operator redirects a slot** → mark item back to `QUEUED`; note redirect reason inline
