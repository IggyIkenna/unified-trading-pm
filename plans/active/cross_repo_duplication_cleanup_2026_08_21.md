---
doc_type: plan
title: Cross-repo duplication cleanup — measured clone removal and centralisation
summary:
  Executes the removable half of the 2026-08-21 workspace-wide duplication audit — a block-level clone scan
  (2,682,560 sliding 30-line windows over 14,809 hand-written source files) that measured 16,166 redundant block
  occurrences plus a 42,900-line vendored contracts mirror. Scope is deliberately narrowed to targets no other active
  plan owns; three findings that collide with live AO-dispatched plans are annotated into those plans instead of being
  fixed here.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-api-contracts,
    features-service,
    execution-service,
    unified-trading-system-ui,
    ml-service,
    e2e-testing,
  ]
scope: [engineer]
tags: [duplication, refactor, centralisation, code-hygiene, clone-detection]
related:
  [
    /plans/active/execution_service_policy_and_fill_model_gaps_2026_08_19.md,
    /plans/active/strategy_service_centralization_fixes_2026_08_16.md,
    /plans/active/deployment_service_api_integration_cleanup_2026_08_18.md,
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/06-coding-standards/config-reloader-pattern.md,
  ]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
locked_by:
locked_since:
context_scope:
  [
    /codex/04-architecture/tier-and-import-architecture.md,
    /codex/06-coding-standards/config-reloader-pattern.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
supersedes:
superseded_by:
depends_on:
source: 2026-08-21 workspace-wide duplication audit (5 parallel tranche agents + mechanical block-level clone scan)
effort: high # multi-repo refactor with delete-risk; every removal needs a consumer check before it lands
assigned_role: infra
drift_direction: advance-code
---

# Cross-repo duplication cleanup

> **Track**: LOCAL / human plan (`assigned_vm: NA`) — driven from an interactive session with authoring sub-agents.
> Not ingested by the orchestrator.

## Measurement basis

Every LOC figure below was measured, not estimated, unless the todo says otherwise:

- 15,054 hand-written `.py` / `.ts` / `.tsx` files hashed; 14,809 of them block-scanned.
- 2,682,560 sliding 30-line normalised windows; 13,885 distinct blocks appear in ≥2 files.
- **16,166 redundant block occurrences** beyond one canonical copy, excluding the vendored mirror.
- Every headline pair re-diffed by hand with indentation stripped.

Scan scripts are reproducible and awk-based (no Python file analysis, per workspace rule).

## Scope discipline — what this plan deliberately does NOT touch

Three audit findings collide with plans that already own those files. Per the findings-triage rule
("fits another plan → annotate it, don't fix"), they are annotated there and excluded here:

| Finding                                                          | Owning plan                                           | Why excluded                                   |
| ---------------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------- |
| `BatchMatchingEngine` / `PaperMatchingEngine` consolidation      | `execution_service_policy_and_fill_model_gaps_2026_08_19` | Plan analyses both engines at its line 202-203 |
| strategy-service `config_reloaders.py` + `auth_s2s.py`           | `strategy_service_centralization_fixes_2026_08_16`    | `assigned_vm: planning`, live AO workers       |
| deployment-api → `deployment_service` import + `backends/` dedupe | `deployment_service_api_integration_cleanup_2026_08_18` | `assigned_vm: planning`, live AO workers       |

## Todos

### Annotate the three colliding findings into their owning plans

- [ ] [DOC] P1. Add a todo to `/plans/active/execution_service_policy_and_fill_model_gaps_2026_08_19.md` — collapse
      `engine/modes/batch/matching_engine.py:BatchMatchingEngine` and `engine/modes/live/matching_engine.py:PaperMatchingEngine`
      into one MEL wrapper parameterised by `mode`. Evidence: the two `submit_order` bodies differ only in
      `select_book_type(..., mode="batch")` vs `mode="live"`; `_resolve_price` and `_build_matcher_kwargs` are
      behaviourally identical (if/elif assignment vs early-return, verified by diff). Keep paper's helper style and
      batch's extracted `_execute_match_and_convert`. ~120 LOC, and it makes the matching step of
      `paper(W) == batch-rerun(W)` true by construction.
- [ ] [DOC] P1. Add a todo to `/plans/active/strategy_service_centralization_fixes_2026_08_16.md` — adopt UTL
      `ConfigReloaderBase` for `strategy_service/{pnl,position,risk}` config reloaders and collapse the three
      byte-identical `auth_s2s.py` copies.
- [ ] [DOC] P0. Add a todo to `/plans/active/deployment_service_api_integration_cleanup_2026_08_18.md` — deployment-api
      declares `deployment-service` as an editable path dep (`pyproject.toml:47,69,128`) and 15 non-test files import
      it, two at module level (`routes/deployments_inventory/_aggregation.py:22-23`, `_classification.py:20-21`). This
      contradicts `deployment_api/config_loader.py:4-10`'s own docstring. Fix is to hoist `CLOUD_RUN_JOBS` and
      `deployment_classification` to UAC. Also note `backends/aws.py` vs `aws_batch.py` (404/411 lines, 21 differing)
      and `backends/cloud_run.py` vs `gcp.py`.

### unified-api-contracts

- [ ] [AGENT] P0. Delete `unified_api_contracts/internal/ml_backup.py` — a 742-line checked-in backup file inside the
      SSOT contracts package. Verify zero importers first (grep + lazy re-export map in `internal/__init__.py`).
- [ ] [AGENT] P0. Collapse `canonical/domain/bookmaker_registry.py` and `canonical/domain/sports/bookmaker_registry.py`
      — 867 vs 868 lines with **1 differing line**. Keep one canonical definition, re-export from the other path.
- [ ] [AGENT] P1. Delete `internal/domain/features_sports/storage.py` — shasum-identical, zero-importer copy of
      `internal/sports.py`; its sibling `__init__.py` docstring already says the real storage types live elsewhere.
- [ ] [AGENT] P2. Reconcile `internal/risk.py` (1,061 lines) against `internal/domain/risk_service/risk.py` (579
      lines, 532 differing) — determine which is authoritative and re-export rather than duplicate.

### features-service

- [ ] [AGENT] P1. Adopt UTL `ConfigReloaderBase` across the 8 feature-family `config_reloaders.py` copies. The calendar
      and commodity copies differ by 3 lines out of 147; UTL's base class docstring already states it replaces this
      boilerplate.
- [ ] [AGENT] P1. Collapse the 8 byte-identical `features_service/*/auth_s2s.py` copies into one shared module.
- [ ] [AGENT] P2. Deduplicate `tests/*/smoke/test_shard_combinatorics.py` across the 4 feature families (57-82 shared
      blocks pairwise) into one parameterised suite.
- [ ] [AGENT] P3. Deduplicate `tests/{onchain,volatility}/unit/test_library_deps_integration.py`.

### execution-service — matching engines explicitly out of scope

- [ ] [AGENT] P1. Merge `execution_service/validation/instruction_validator.py` and
      `execution_service/utils/validation/instruction_validator.py` — 570 vs 561 lines, 59 differing. Pick one home,
      re-point importers.
- [ ] [AGENT] P1. Runtime-registration check on `execution_service/venues/` (2,030 LOC). Only importers found are
      tests and benchmarks, and it duplicates `defi_execution/connectors/` class-for-class — but it contains an
      `initializer.py`, so confirm nothing registers it dynamically before deleting. If the check is inconclusive,
      file an issue doc rather than deleting.
- [ ] [AGENT] P2. Assess `defi_execution/position_tracker.py` vs `services/position_tracker.py` (67 shared blocks) —
      report only if another plan owns either file.

### unified-trading-system-ui

- [ ] [AGENT] P0. Remove the `context/` vendored mirror — 245 Python files / 42,900 LOC mirroring UAC, codex and the
      PM corpus, with **zero references from any TS/TSX/JS file, tsconfig, next.config or package.json** (measured).
      Before deleting, repoint the fallback `SPEC_PATH` at `.github/workflows/uic-openapi-sync.yml:44`, which
      currently points into a `context/api-contracts/openapi/` path.
- [ ] [AGENT] P0. Fix the two active plans citing paths inside `context/` so the deletion does not rot them —
      `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md:508` and
      `/plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md:522,530`.
- [ ] [AGENT] P2. Deduplicate `components/ui/use-toast.ts` and `hooks/use-toast.ts` (126 shared blocks).
- [ ] [AGENT] P2. Deduplicate `app/api/strategy-evaluation/email/route.ts` and `lib/strategy-evaluation/email/route.ts`.
- [ ] [AGENT] P3. Report whether `lib/types/api-generated.ts` (dated 2026-06-08) is stale relative to
      `uic-openapi-sync.yml` — do not regenerate, just report.

### ml-service + e2e-testing

- [ ] [AGENT] P1. ml-service — collapse `ml_service/{inference,training}/auth_s2s.py` and adopt UTL
      `ConfigReloaderBase` for both `config_reloaders.py` copies (16 differing lines out of 112).
- [ ] [AGENT] P1. e2e-testing — collapse the 5 `scripts/*/smoke_matrix.py` copies (52-127 shared blocks pairwise) into
      one parameterised module driven by a domain table.
- [ ] [AGENT] P3. ml-service / features-service — deduplicate the `test_shard_combinatorics.py` copies that cross the
      two repos (56 shared blocks each) by hoisting the shared harness rather than cross-importing.

### unified-trading-pm doc corpus

- [ ] [OPERATOR] P2. Remove `plans/active/issues/_cefi_canonical_blueprint_2026_07_17.md` — a 52 KB underscore-prefixed
      leftover of the archived `plans/archive/2026_07/issues/cefi_canonical_blueprint_2026_07_17.md`, which is
      `status: resolved`. It is the only underscore-prefixed doc in `plans/active/issues/`. Deleting a plan doc is
      operator-gated.
- [ ] [OPERATOR] P3. Resolve the archive-mechanics duplicates — the same doc filed into two month folders
      (`mdps_backfill_phase3`, `mtds_backfill_phase3`, `instruments_backfill_phase3` in both `2026_05/` and `2026_06/`;
      `work_split_2026_05_22_ikenna` in `2026_05/` and `2026_07/`), plus `gcs_data_access_audit_log_cost` and
      `uac_weekly_validation_wif_secrets_missing` filed in both a month folder and `archive/issues/`, and the two
      hash-suffixed `sports_migration_master_plan` copies.
- [ ] [AGENT] P3. Characterise the 479-block overlap between `plans/epics/infrastructure_master.md` and
      `plans/epics/security_and_cross_cutting_master.md` (888 vs 877 lines, 87 differing) — determine how much is a
      shared epic section template versus genuinely duplicated content, and report before changing anything.

### Findings surfaced during execution (2026-08-21)

- [ ] [AGENT] P0. **Deleting `unified-trading-system-ui/context/` breaks a WORKSPACE-WIDE quality gate.**
      `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml` records entries under
      `unified-trading-system-ui/context/api-contracts/canonical-schemas/crosscutting/errors/__init__.py` and
      `unified-trading-system-ui/context/internal-contracts/schemas/events.py`. STEP 5.83 (ADAPTER CONTRACT-CALL
      REGRESSION RATCHET) scans the whole workspace, not one repo, so with `context/` deleted the step hard-fails in
      EVERY repo's gate — measured: it failed execution-service's otherwise-green run (its own gate body passed,
      552s). CORRECTED PROCEDURE: the baseline header states "DO NOT manually edit; the file is auto-generated" — the
      sanctioned fix for a deleted file is `check_adapter_contract_regression.py --regenerate-baseline` run FROM A
      KNOWN-GOOD HEAD. Do NOT regenerate while other repos carry uncommitted work: that would bake other sessions'
      in-flight state into a shared workspace-wide ratchet and mask real regressions. Correct sequencing — land the
      `context/` deletion, wait for a clean tree, then regenerate and land the baseline in one change.
      `check_runbook_execution_owner.py` also references the path; check it too.


- [ ] [OPERATOR] P0. **features-service and e2e-testing are coupled through the filesystem, and it broke 42 tests.**
      Nine `features-service/tests/*/unit/test_smoke_matrix.py` files `importlib`-load a SIBLING REPO at runtime via
      `_REPO_ROOT.parent / "e2e-testing" / "scripts" / <family> / "smoke_matrix.py"`, and three PRODUCTION modules
      (`features_service/{delta_one,sports,commodity}/smoke.py`) do the same; `e2e-testing/scripts/features/run_backfill.py`
      reaches back the other way. Provenance comment dates the split to 2026-07-31 "per script-homes.md". Measured
      consequence: this plan's e2e-testing `smoke_matrix.py` consolidation made features-service's gate fail
      **42 failed / 18,490 passed**, all 42 confined to `tests/{delta_one,multi_timeframe,volatility}/unit/test_smoke_matrix.py`.
      The loader already knows the sibling can be absent ("e2e-testing sibling not present in this CI checkout"), so
      these tests silently skip in CI and only bind locally — a check that does not check anything where it matters.
      This is a cross-repo architectural finding, not a cleanup item: decide whether the coupling is legitimised (a
      shared harness in UTL, which is a library and therefore legal) or removed.
- [ ] [AGENT] P1. **Unblock the e2e-testing consolidation without breaking features-service.** The 5 rewritten
      `scripts/<domain>/smoke_matrix.py` wrappers delegate to `_smoke_matrix_shared.py`, so the module-level symbols the
      features-service tests assert on are no longer in the wrapper namespace (hence `test_submodule_reexport` failing).
      Fix: have each wrapper re-export the shared symbols so the loaded module's namespace is unchanged. Do NOT land the
      e2e-testing change before this, or features-service goes red.
- [ ] [OPERATOR] P1. **e2e-testing cannot commit — a pre-existing `git stash pop` conflict blocks it.**
      `e2e-testing/docs/VM_BACKFILL_GUIDE.md` is `UU` carrying a live git conflict-marker pair
      markers, predating this session and owned by whoever holds that stash. Git refuses to commit ANY path while an
      unmerged entry exists, so this plan's e2e-testing work (-987 lines, gate green) is complete but unshippable.
      Related signal: 122 stash entries in this slot's `unified-trading-pm` checkout.
- [ ] [AGENT] P2. **`unified_api_contracts/internal/ml_backup.py` was investigated and NOT deleted** — it is still
      present (25 KB). Retrieve the reason and either delete it or record why a backup file belongs in the SSOT
      contracts package.
- [ ] [DOC] P3. **Correct a false provenance claim before it propagates**: a worker reported `internal/risk.py` carried
      "a live uncommitted WIP edit from another session (a DERIBIT margin-model addition)". Verified false — the file is
      not dirty and `DERIBIT` appears 3x in both the working copy and `HEAD`. It is committed code.
- [ ] [AGENT] P3. **Diagnostic-logging regression accepted during the ConfigReloaderBase migration**: the per-domain
      `_on_*_reload` callbacks previously logged instrument/venue/flag COUNTS into the `CONFIG_CHANGED` event details;
      `ConfigReloaderBase._handle_reload` emits only `{domain, service}`. strategy-service made the same trade in
      `054fae03`. Confirm this is intended fleet-wide or restore the counts in the base class.

## Verified NOT problems — do not "fix" these

- strategy-service's 18 v2 archetypes already share a real `BaseArchetypeEngineV2` (439 LOC) that is part of the
  determinism spine.
- deployment-api vs deployment-service is a principled split — only 19 basenames overlap across 1,095 files.
- e2e-testing vs system-integration-tests is a legitimate split; shared basenames trace to a documented canonical
  test template.
- UAC stays types-only; the UTL→UAC import direction is clean with zero banned deep-path imports.
- The `external/gateio/*` identical files are a deliberate venue-removal tombstone.
- UAC's near-empty DeFi scaffold directories are IN-FLIGHT, owned by `defi_live_poller_phased_build_2026_08_15.md`.

## Corrections carried forward from the audit

- The "two venue tables have conflicting values" finding was **withdrawn**. `VENUE_TO_ADAPTER_KEY` maps venue →
  adapter implementation; `VENUE_TO_DATA_SOURCE` maps venue → data vendor. `BYBIT: "tardis"` and `BYBIT: "bybit"`
  answer different questions. The residual finding is only that neither module says so.
- `execution_service/venues/` is **2,030 LOC**, not the 3,825 first reported.

## Progress Log

- **2026-08-21** — Plan created from the workspace-wide duplication audit. Scope narrowed after a conflict check found
  two `assigned_vm: planning` plans live in strategy-service, deployment-api and deployment-service, and one active
  plan already analysing both matching engines.

### Corrections to this plan's own premises (measured during execution, 2026-08-21)

- [x] ✅ **`ml_backup.py` is NOT a stray backup — the audit premise was WRONG and the P0 delete was correctly refused.**
      It is live, load-bearing code: `internal/__init__.py`'s lazy map has 6 entries pointing at it,
      `internal/ml/__init__.py` does `from ..ml_backup import *`, and real cross-repo importers exist in
      `ml-service` (`cross_asset_training_pipeline.py`, `cross_venue_spread.py`) and
      `unified-trading-library/unified_trading_library/ml/models.py`. Deleting it would have broken both repos.
      The misleading NAME is the actual finding.
- [ ] [AGENT] P2. **Rename `ml_backup.py` / finish the module split it defers.** Its own docstring says
      "The file was too large to properly split within time constraints... TODO: Complete proper module split".
      A file named `*_backup` that six lazy re-exports and two repos depend on is a navigability trap.
- [x] ✅ **The "`features_sports/storage.py` has zero importers" claim was also WRONG** —
      `tests/internal/unit/test_domain_new_modules.py` imported it. It was repointed to `internal/sports.py`
      before the delete, not deleted blind.
- [x] ✅ **A real bug was fixed in passing**: `canonical/domain/sports/bookmaker.py` used
      `from ..bookmaker_registry import ...` (double-dot), silently reaching the top-level copy instead of the
      canonical `sports/` one — contradicting its own docstring. Corrected to a single dot.
- [ ] [AGENT] P3. **One file was excluded from the UI ship**: `context/pm/docs/Odum Research Ltd.pdf` is still
      tracked. `quickmerge --files` word-splits on whitespace and the path contains a space, so it cannot be named;
      `--agent` mandates `--files`, so the unscoped path is unavailable. Delete it in a follow-up, or fix
      `quickmerge.sh` to accept a NUL-delimited file list.
- [ ] [AGENT] P3. **`lib/types/api-generated.ts` is ~3 months stale** — 479 paths vs UAC's live spec at 628 paths
      (last true regen 2026-05-16, reverted the same day in `91e45bdf`). The `uic-openapi-sync.yml` template fix has
      landed but `rollout-workflow-templates.sh` was NOT run, so the live per-repo workflow still carries the old
      fallback.

### Exact contract for the e2e-testing wrapper fix (derived 2026-08-21, do not re-derive)

The 42 features-service failures are `AttributeError`s: the new wrappers expose only `DomainSmokeConfig` and
`main`, but `features-service/tests/*/unit/test_smoke_matrix.py` loads the wrapper via `importlib` and calls
module-level symbols with the ORIGINAL (config-free) signatures. Measured call sites vs shared signatures:

| Test calls on the loaded module      | Shared function in `scripts/_smoke_matrix_shared.py`                    |
| ------------------------------------ | ----------------------------------------------------------------------- |
| `mod._viable_cells(None)`            | `_viable_cells(cfg, filter_asset_group)` — L127                         |
| `mod._build_cli_invocation(ag, date)`| `_build_cli_invocation(cfg, asset_group, date)` — L137                  |
| `mod._test_bucket("p", cat)`         | `_test_bucket(cfg, project_id, asset_group)` — L150                     |
| `mod._run_cell(asset_group=…, …)`    | `_run_cell(cfg, asset_group, date, project_id, dry_run)` — L280         |
| `mod.run_matrix(asset_group_filter=…)`| `run_matrix(...)` — L313                                                |
| `mod.SUPPORTED_ASSET_GROUPS`         | `CONFIG.supported_asset_groups`                                         |

So a plain re-export is NOT enough — the signatures differ by the leading `cfg`. Each wrapper must bind its own
CONFIG (e.g. `functools.partial(_shared._viable_cells, CONFIG)`) and define `SUPPORTED_ASSET_GROUPS`. Check
`mock.patch` targets still resolve after binding — several tests patch `_invoke_cli`, and a `partial` is not a
function object.

- [ ] [AGENT] P1. Apply the binding above to all 5 e2e-testing wrappers, then re-gate features-service. BLOCKED
      until the `docs/VM_BACKFILL_GUIDE.md` unmerged entry is resolved — git refuses to commit any path in that repo
      while it exists.

### BLOCKER: unified-api-contracts cannot gate green — cause is NOT this plan's diff (2026-08-21)

UAC's work is complete (-1,551 lines, shim removed, package imports verified with all 78 BOOKMAKER_REGISTRY
entries) but `quality-gates.sh --no-fix` exits 1 on two violations, neither introduced by this plan:

- [ ] [OPERATOR] P1. **STEP 5.96 blank-asset_group: 4 new violations, baseline 0, introduced by commit
      `e48adfa3` "refactor: centralize deployment observability contracts"** — another session's hoist of
      `cloud_run_job_registry.py` + `deployment_classification.py` into UAC (the same hoist this plan recommended
      for the deployment-api import fix). **Three of the four are FALSE POSITIVES.**
      `scripts/quality_gates/check_no_blank_asset_group.py:52` is
      `_BLANK_PATTERN = re.compile(r'asset_group\s*=\s*(?:""|\'\')')` searched against `raw_line` (L118) with no
      comment/docstring awareness, so it flags PROSE: `cloud_run_job_registry.py:24` (docstring),
      `:122` (a `#` comment), `deployment_classification.py:150` (docstring). Only
      `cloud_run_job_registry.py:70` (`asset_group="",`) is real code, and that one is a legitimate cross-asset
      T+1 recon job that wants the documented `# noqa: blank-asset-group  <reason>` opt-out.
      Two candidate fixes: (a) make the checker token-aware (skip COMMENT/STRING tokens via `tokenize`) — a
      fleet-wide enforcement change, should be deliberate; (b) noqa the one real callsite and accept prose
      false-positives. NOT done here: patching a shared gate checker unilaterally while other sessions gate
      against it is not a safe autonomous act.
- [ ] [OPERATOR] P2. **900-line cap**: `unified_api_contracts/internal/architecture_v2/__init__.py` is 1,423 lines,
      from commit `d44de9fb` "feat(uac): add authorized control instructions". Also pre-existing to this plan.

**Consequence**: UAC (-1,551) is unshippable, and because quickmerge's pre-flight refuses any repo whose path
dependency is dirty, ml-service (-45) and execution-service (-4,378) are blocked behind it despite both being
gate-verified.
