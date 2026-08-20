---
doc_type: plan
title:
  Codex-violation ratchet to ≤5 fleet-wide + split the egregious oversized files (registry.py 18k, orchestrator.py 8k,
  …)
summary:
  Ratchet all repo codex-violation budgets to ≤5 fleet-wide and split egregious oversized source files (registry.py 18k,
  orchestrator.py 8k).
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, alerting-service, client-reporting-api, deployment-api, deployment-service, e2e-testing]
scope: [engineer, admin]
tags: [codex, lint, ratchet, file-size, refactor, quality-gates, basedpyright]
related: [plans/active/ci_local_qg_parity_2026_06_08.md, plans/active/cicd_contract_hardening_2026_06_01.md]
created: 2026-06-10
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only # corrected 2026-07-14, was: orchestrator-agent (invalid pairing w/ assigned_vm: NA per task_template.md's two valid tracks; no AO-dispatch banner present in body — verify-rerun-2 finding 87; matches operator ruling 2026-07-12 finding 9 applied to sibling plans)
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 18.0
estimate_calibrated_ai_days: 7.2
last_updated: 2026-08-19
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    operator direction 2026-06-10 ("take codex violations down to max 5; we have a ~10k-line file in instruments-service
    that's way too much — make a PM active plan"),
    slot-3 fleet audit 2026-06-10 (the grep -P parity fix exposed the true counts; budgets had sprawled to 24),
  ]
assigned_role: backend_engineer
effort: medium # explicit 2026-08-09 (check_effort_signal_ratchet --only) — matches backend_engineer's own existing default (agents/backend_engineer.md thinking: medium), no behavior change
drift_direction: advance-code
context_scope:
  [
    /codex/06-coding-standards/quality-gates.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    features-service/features_service/delta_one/app/features/registry.py,
    instruments-service/instruments_service/engine/orchestrator/,
  ]
---

# Codex-violation ratchet to ≤5 fleet-wide

## Problem

`CODEX_MAX_VIOLATIONS` (the per-repo lint-codex budget in each `scripts/quality-gates.sh`) is a **ratchet-DOWN**
mechanism — a temporary ceiling for PRE-EXISTING violations that must only ever shrink toward 0. Instead it has
**sprawled to 24** on the worst repos, normalising real debt: banned `os.getenv`, local schema definitions, deep UAC
imports, `Any` types, empty-fallbacks, backward-compat shims, and **files that are maintainability hazards**
(`features-service/registry.py` is **18,328 lines**; `instruments-service/orchestrator.py` **8,192**;
`deployment-api/data_status_service.py` **6,663**; `unified-trading-api/seed.py` **5,169**;
`agent-orchestrator/server.py` **4,470**; `market-tick-data-service/orchestrator.py` **4,219**).

**Why now**: until 2026-06-10 the `grep -P` portability bug (`ci_local_qg_parity_2026_06_08.md`, FIXED) made every macOS
slot **false-pass** the deep-import lint-codex check — so local QG under-counted and the budgets were never trustworthy
locally. With local now the honest oracle (local count == CI count), a ratchet-down is **enforceable + verifiable on the
slot** before CI.

**Target (operator 2026-06-10): every repo's `CODEX_MAX_VIOLATIONS` ≤ 5** (0 is the ideal; 5 is the hard ceiling), and
**no source file > 900 lines** without a documented, time-boxed exception. Budgets only ratchet DOWN from here — a bump
is review-blocking (the sole sanctioned exception was deployment-api 23→24 on 2026-06-10 to unblock the promotion while
this plan lands; that is itself a P1 item below).

## Principle (the ratchet contract)

1. A budget is the count of CURRENTLY-failing lint-codex check-classes (each check is a binary `V += 1`). The list of
   classes is the SSOT in `scripts/quality-gates-base/base-service.sh` (os.getenv / deep-imports / Any / raw-json /
   empty-fallbacks / schema-provenance / file-size / function-size / backward-compat / hardcoded-project-id / …).
2. **Every fix ratchets the budget DOWN in the same commit** — fix a class, drop `CODEX_MAX_VIOLATIONS` by the number of
   classes you cleared, update the in-file comment with what was fixed. Never leave a fixed violation with a stale
   higher budget.
3. **File-size + function-size are first-class violations**, not exempted by a glob forever. An oversized file
   `FUNCTION_SIZE_EXTRA_EXCLUDES`-excluded today (e.g. `features-service/registry.py`) is HIDDEN debt — Phase 1 splits
   it and removes the exclude.
4. **No new violations**: a repo at ≤5 must not regress; CI v2 + the now-honest local gate enforce it.

## Public-API + cross-repo safety contract (HARD — every split/move obeys this)

**Established fact (slot-3 audit 2026-06-10):** the big-file targets are **service-internal** — no other repo imports
`DataStatusService`, the instruments `engine.orchestrator` functions, or `features.registry` (verified: cross-repo
service-import grep is EMPTY; the no-service↔service-deps rule holds — services integrate via UAC contracts + HTTP/GCS,
NOT Python imports). So Phase-1 splits change **only in-repo callers**, and the contract is to keep even those
unchanged:

1. **Pre-audit before moving any symbol** (Citadel #6): `rg "<symbol>" --type py` across the WORKSPACE (not just the
   repo) to enumerate every importer + caller. 0 cross-repo hits is the expected + required state for service internals;
   a cross-repo hit on a service internal is itself a bug to surface (it violates no-service↔service).
2. **Default = preserve the surface.** The original module (or its `__init__`) **re-exports** every moved public symbol,
   and the facade class keeps every public method (thin delegation/mixins). Result: `from x.orchestrator import foo` and
   `service.get_manifest_status()` resolve unchanged → **no caller edits, no QG regression**. Tests-green + a clean
   `basedpyright` on the repo prove the surface held.
3. **If a symbol genuinely must move/rename** (rare; only when the old name is wrong), migrate **ALL callers in the same
   unit** (the pre-audit list) — never leave a dangling import. For a service internal that's all in-repo; there is no
   cross-repo caller to chase.
4. **Phase 2 (the ONE cross-repo surface — UAC) is ADDITIVE-FIRST:** UAC re-exports the symbol at the one-level facade
   WITHOUT removing the deep path, so every existing two-level consumer keeps working; each consumer repo then migrates
   its own call sites + ratchets its own budget as a separate tracked todo; the deep path is removed only after the
   pre-audit shows zero remaining importers fleet-wide. No consumer ever breaks mid-flight.
5. **Data-file moves (registry.py / seed.py) keep the LOADED object identical** — the loader must produce byte-equal
   `FeatureSpec`/seed objects (assert in a migration test), so `get_specs_by_group` / pinned `formula_version` consumers
   (ML/strategy) see no change.

## Prerequisite (DONE)

- [x] ✅ `ci_local_qg_parity` grep-P → rg --pcre2 fix (PM@7427ade8a) — local macOS now counts identically to CI, so a
      slot can prove a ratchet-down before pushing. Verified 2026-06-10.

## Per-repo current state (slot-3 audit 2026-06-10)

> **2026-06-11 ratchet snapshot (this plan's session 1)** — budgets now: deployment-api **24** (25-bump reverted),
> execution-service **21**, market-tick-data-service **0** (16→15→0 2026-06-11, mtds_coverage_75_and_codex_zero plan —
> MTDS@cddb122; MIN_COVERAGE also 60→75, measured 82.2%), strategy-service **10**, market-data-processing-service **7**,
> deployment-service **1**, ibkr **1**, ml-service **3**, instruments 4, unified-trading-api **0 (pinned)**,
> batch-live-recon 1, features/UTL/PM 0, UAC 7 (ratcheted 7→2 @128e065; lxml = execution-service+canonical-range todo).
> All six P1 monoliths + the P2 >1k tail are SPLIT and shipped; the table below is the original baseline for reference.

| Repo                           | Budget | Over 5? | Worst file (lines)                 | Notes                                                |
| ------------------------------ | ------ | ------- | ---------------------------------- | ---------------------------------------------------- |
| deployment-api                 | 24     | ⬛ +19  | data_status_service.py (6,663)     | also data_status_drilldown 2,586 / data_status 2,550 |
| execution-service              | 24     | ⬛ +19  | kraken_rest_adapter.py (1,299)     | many adapters >1k; deep imports (34 raw)             |
| market-tick-data-service       | 16     | ⬛ +11  | orchestrator.py (4,219)            | tardis_adapter 2,880 / solana_defi_handler 2,125     |
| strategy-service               | 11     | ⬛ +6   | catalog.py (2,371)                 | batch_handler 1,570                                  |
| market-data-processing-service | 10     | ⬛ +5   | canonical_writer.py (2,412)        | live_workers 1,731                                   |
| deployment-service             | 8      | ⬛ +3   | —                                  | violation classes (no >900 file in top-3)            |
| unified-api-contracts (lib)    | 7      | ⬛ +2   | —                                  | library — schema-provenance/import classes           |
| ml-service                     | 5      | ✅ =5   | cloud_feature_provider.py (1,202)  | at ceiling — hold + split the >1k files              |
| instruments-service            | 4      | ✅      | **orchestrator.py (8,192)**        | budget OK but the 8k file is excluded HIDDEN debt    |
| ibkr-gateway-infra             | 4      | ✅      | —                                  |                                                      |
| batch-live-reconciliation      | 1      | ✅      | —                                  |                                                      |
| features-service               | 0      | ✅      | **registry.py (18,328)**           | budget 0 but registry.py EXCLUDED = HIDDEN debt      |
| unified-trading-api            | none   | ?       | seed.py (5,169)                    | get budget; split seed.py                            |
| agent-orchestrator             | none   | ?       | server.py (4,470)                  | get budget; split server.py (worker_liveness 1,215)  |
| unified-trading-library (lib)  | 0      | ✅      | —                                  |                                                      |
| unified-trading-pm             | 0      | ✅      | generate-ui-vision-pptx.py (1,717) | script-dir; lower priority                           |

> "none" = no `CODEX_MAX_VIOLATIONS` override (uses the base default). Phase 0 pins the real number per repo.

## Phase 0 — Per-repo violation census (do FIRST; cheap, unblocks everything)

- [x] ✅ [AUDIT] P1. DONE 2026-06-10 (slot live-defi-rollout) — census written to
      `plans/audit/results/codex_violation_census_2026_06_10.md`: 25 repos run, 5 over-ceiling (deployment-api 24,
      execution-service 22, MTDS 15, strategy 10, MDPS 7), 3 immediate no-code ratchets (deployment-service 8→1, ibkr
      4→1, ml 5→3), `none`-budget repos all at 0 current violations (agent-orchestrator runs a custom gate with no codex
      section — budget-pin todo stays in Phase 4). Original: For EVERY service+library repo, run
      `QG_SLICE=lint-codex bash scripts/quality-gates.sh --no-fix` (now honest post-parity-fix) and record the per-class
      breakdown (which of the ~24 check-classes fire, and the file/line offenders for each) into
      `plans/audit/results/codex_violation_census_2026_06_10.md`. This is the remediation matrix: it converts each
      repo's opaque budget number into a concrete fix-list. Capture the `none`-budget repos' real counts. Repo:
      unified-trading-pm (audit doc) — read-only across the fleet.

## Phase 1 — Split the egregious oversized files (biggest maintainability win; each is its own dispatchable unit)

> Rule: decompose by COHESION (one concern per module), keep the public import surface stable (re-export from the
> original module's `__init__`/facade so consumers don't churn), add no behaviour change, QG-green + tests-green per
> split, and REMOVE any `FUNCTION_SIZE_EXTRA_EXCLUDES` glob that was hiding the file. Ratchet the repo's file-size
> violation away in the same commit.

- [x] ✅ [REFACTOR] P1. DONE 2026-06-11 — features-service@82918a6d: registry.py 18,328 L → 411 L loader+validator;
      1,382 specs moved to `features_service/delta_one/app/features/registry_specs.yaml` (human-editable SSOT); one-shot
      `scripts/dump_registry_to_yaml.py` migration; YAML-load equality + closed-set validation test
      (tests/delta_one/unit/test_registry_yaml_loader.py); pyyaml promoted to direct dep; registry.py removed from
      FUNCTION_SIZE_EXTRA_EXCLUDES; budget stays 0; full QG green (16,980 tests; one unrelated calendar ordering-flake
      verified pass-in-isolation + green on rerun). Original: **features-service `registry.py` (18,328 L) — it's DATA,
      not code (operator 2026-06-10).** The file is **1,382 `FeatureSpec(...)` literals + only 11 functions** — a
      declarative data table living in a `.py`. Do NOT "split into per-group .py modules" (still code-shaped data).
      Instead **separate the data from the loader**: - Move the 1,382 specs into a **data file** — `registry/specs.yaml`
      (human-editable SSOT; one block per spec: name/group/period/formula_version/implementation/status/…) OR a
      generated `specs.parquet` if a generator is preferred. "Adding a feature = add a row" stays true, in YAML not
      Python. - `registry.py` shrinks to a **~80-line loader+validator**: read the data file → build the `FeatureSpec`
      objects → run the closed-set validation the docstring describes (group ∈ CALCULATOR_REGISTRY, status ∈ enum,
      version is int) at import → expose `get_specs_by_group` / `max(formula_version)` unchanged. Tests 2.2–2.5 keep
      parametrising over the loaded specs (public surface identical). - If round-tripping by hand is error-prone, ship a
      one-shot `scripts/dump_registry_to_yaml.py` that emits the data file from the current literals (the migration),
      then delete the literals. Remove the `FUNCTION_SIZE_EXTRA_EXCLUDES` glob. Repo: features-service.
- [x] ✅ [REFACTOR] P1. DONE 2026-06-11 — instruments-service@cb51c98: orchestrator.py 8,192 L → `engine/orchestrator/`
      package (16 cohesion modules + 863-line thin `__init__` re-exporting every symbol; defi/sports(×5)/prediction… per
      the plan grouping extended by real cohesion); weather.py deep-import flipped to the new one-level facade (cleared
      the surfaced deep-import class → V back to 4/4); FUNCTION_SIZE exclude narrowed from the whole monolith to 2
      carrying modules (process.py 1,963 L legacy `process_instruments` body + sports_reference.py — justified in-file
      citing this plan); contract-call conservation verified (114 ≥ baseline 99); full QG green. Follow-up: decompose
      `process_instruments()` (next todo). Original: **instruments-service `orchestrator.py` (8,192 L / 89 functions) —
      abstract by asset-group + core.**
- [x] ✅ [REFACTOR] P3. DONE 2026-06-11 — instruments-service@a576a29: `process_instruments()` 1,931 L decomposed by
      stage into process*{preflight,fetch,enrichment,write,zero_records,completeness}.py (316–642 L each; process.py now
      322 L facade); sports_reference fetcher 882 L → sports_reference*{core,fixtures}.py (sports_reference.py 212);
      both FUNCTION_SIZE_EXTRA_EXCLUDES entries REMOVED; 2 surfaced lazy imports hoisted; budget ratcheted 4→3
      (remaining: os.getenv / pip-install-in-Dockerfile / broad-except); full QG green. Original: decompose
      `process_instruments()` + remove the excludes. The module mixes per-asset-group logic with venue/date core + sink.
      Suggested package `engine/orchestrator/`: `defi.py`
      (`_build_defi_venues`/`clear_defi_universe_cache`/`_get_defi_manifest_high_watermarks`/
      `_enforce_defi_monotonicity`/`filter_defi_instruments_by_relevance`/`_normalize_wrapped_token`), `sports.py`
      (`_canonical_league_id`/`_af_id_from_canonical`/`_lifecycle_columns_from_af_response`/
      `_flatten_canonical_fixture_for_disk`/league-team-standings caches/`_should_skip_date_for_per_league`),
      `prediction.py` (`_extract_prediction_canonical_group`/`_compute_prediction_shards`), `venue_core.py`
      (`_get_venue_epoch`/`_should_skip_shard`/`get_venues_for_asset_groups`/`is_venue_available`/`earliest_venue_date`/
      `filter_instruments_by_date`), `sink.py` (`_gated_sink_write`/`_coerce_adapter_output`), `failure.py`
      (`_classify_adapter_failure`). `orchestrator.py` becomes the thin coordinator that imports + sequences these.
      Repo: instruments-service.
- [x] ✅ [REFACTOR] P1. DONE 2026-06-11 — deployment-api@6b7aa69: data_status_service.py 6,663 L → 638-line facade +
      15-module `services/data_status/` package (defi/sports/coverage/manifest/missing_shards/venue_resolution/cli/
      breakdowns/mtds/rollup_cache/... all ≤864 L); `DataStatusService` keeps all 80 public methods (delegation, zero
      caller churn). Mid-flight foreign F4 seeded-4state-denominator fix (deployment-api@644e439) GRAFTED into the split
      layout (helpers + seeded branch in data_status/mtds.py; its test adapted to load mtds.py — all 147 data-status
      tests green). Bonus: last strategy_service import (treasury NAV) flipped to UTL → strategy-service path-dep
      REMOVED from pyproject + PM workspace-manifest (no-service↔service HARD RULE), budget ratcheted back 25→24 (the
      transient 25th class was the manifest-alignment edge). drilldown/routes follow-up stays below. Original:
      **deployment-api `data_status_service.py` (6,663 L / 69-method god-class) — abstract the domain logic out
      (operator 2026-06-10).**
- [x] ✅ [REFACTOR] P2. DONE 2026-06-11 — deployment-api@5127517: routes/data_status.py 2,550 → package (5 modules);
      services/data_status_drilldown.py 2,586 → package (5 modules); routes/deployments.py 968 → package (crud/
      lifecycle); services/shard_detail.py 1,777 → package; + Phase-2b facade flips (routes/config.py +
      utils/path_combinatorics.py to one-level registry imports). **budget 24→22** (file-size + deep-imports classes
      CLEARED — all 8 two-level registry call sites flipped; supersedes the plan's "23→24 revert" item, landing below
      23); honest measured 22; full QG green. Remaining classes to ≤5 per the in-file comment: fn-size, os.getenv,
      Any-types, schema-provenance (Phase 3) et al. Original: drilldown + routes facade treatment. Suggested package
      `services/data_status/`: `defi.py`
      (`_is_legacy_defi_venue_row`/`_read_defi_merged_index`/`_allowed_defi_venue_chain_pairs`/
      `_filter_to_canonical_defi_venues`/`_filter_legacy_defi_rows`), `sports.py` (`_is_sports_reference_venue`/
      `_is_understat_venue`/`_is_transfer_window_venue`/`_is_sparse_sports_entity`/`_get_reference_expected_dates`),
      `coverage.py`
      (`get_coverage_summary`+`_resolve_coverage_cat_list`/`_select_coverage_group_axis`/`_pack_row_filters`/
      `_apply_row_filters`/`_build_breakdowns`/`_calculate_completion_rate`), `manifest.py` (`get_manifest_status`/
      `_get_manifest_status_sync`/`_scan_category_manifest`), `missing_shards.py` (`calculate_missing_shards`+sync+
      `_tally_missing_venues`), `venue_resolution.py` (`_resolve_venue_start`/`_resolve_expected_dates`/
      `_build_venue_breakdown`/`_apply_mtds_honest_coverage`), `cli.py` (`_build_cli_cmd`/`run_data_status_cli`). The
      `DataStatusService` becomes a thin **facade** that composes these (mixins or delegation) — same public methods, no
      caller churn. `data_status_drilldown.py` (2,586) + `data_status.py` (2,550) get the same treatment. Repo:
      deployment-api.
- [x] ✅ [REFACTOR] P1. DONE 2026-06-11 — unified-trading-api@42f12ab: seed.py confirmed DATA → 5,169 L → 470 L thin
      loader + 72 `mock_data/seed_data/*.json` domain files; seed.py excludes removed from FUNCTION*SIZE/EMPTY*\*/
      IMPORT_INSIDE globs; `CODEX_MAX_VIOLATIONS=0` pinned; equality + org-integrity tests extended
      (tests/unit/test_seed_quality.py); full QG green. Original: **unified-trading-api `seed.py` (5,169 L)** — if it's
      seed DATA (fixtures/records), same pattern as registry.py: move the data to a data file + a thin seeding loader;
      if it's seed LOGIC, split by domain. Census (Phase 0) confirms which. Repo: unified-trading-api.
- [x] ✅ [REFACTOR] P1. DONE 2026-06-11 — agent-orchestrator@951e3e6: server.py 4,505 L → 597 L (lifespan + app
      assembly + account-rotation helpers kept for test patch-surface) + 9 `server/routes/*.py` APIRouter modules
      (232–830 L each) + `_deps.py`; route table (76 APIRoutes: path/method/endpoint/response_model/deps/status)
      byte-identical pre/post via worktree diff; runtime smoke on :8799 (live :8765 untouched, no restart); 480 tests
      green; zero caller/test edits. worker_liveness/state_store reviewed: NOT split (next todo). Original:
      **agent-orchestrator `server.py` (4,470 L)** — split by surface into routes/\*.
- [x] ✅ [REFACTOR] P3. DONE — agent-orchestrator@209937f ("split worker_liveness/state_store/worktree_clean_check/
      models into packages behind unchanged import paths; all modules <900; patch surfaces module-bound"). Verified
      2026-06-12 (plan-flip backfill by slot-5): `server/worker_liveness/` is a package (`__init__.py` 476 L +
      `_respawn.py`/`_git_alerts.py`/`_auth_failover.py`) and `server/state_store/` likewise (`__init__.py` 242 L +
      slots/tasks/agents/activity/account_usage/\_time) — both facades well under the 900-line cap, the
      `server.worker_liveness.*` / `server.state_store.*` patch surfaces intact (the full AO suite incl. the ~30
      namespace patches runs green; 529+ tests). Was: **decomposition requires test edits** (zero-caller-edit split
      impossible). Repo: agent-orchestrator.
- [x] ✅ [REFACTOR] P1. COMPLETE 2026-06-11 — orchestrator half @1681f85 (below) + **adapters half @eb33603**:
      tardis*adapter 2,907→449 facade + 5 transport/concern modules (symbol_resolution/csv_transport/cefi_shards/
      batch_download/bulk_download, all <900); solana_defi_handler 2,175→658 facade + 3 venue/stage modules
      (drift/amm/yield); 255 patch-surface tests green, 94/94 defs conserved, zero cross-repo code refs; budget
      ratcheted 16→15 (file-size class still fires on websocket_runner 912 / solana_lst_archival 988 /
      rebuild_sports_manifest_v9 1137 / migrate*\*\_v9 1284+1056 — named next targets in-file). Original half:
      market-tick-data-service@1681f85: orchestrator.py 4,219 L → `engine/orchestrator/` package (7 modules ≤824 L:
      venue_fetch / partitioned_writer / sentinels / manifest_finalize / preflight / symbol_rules / \_state + thin
      `__init__`); namespace-patch regression in the dt-start-date gate fixed (sentinels route UAC gates via `_orch.`);
      foreign asset_group-provenance fix (MTDS@5df7872-adjacent) grafted into manifest_finalize; contract-call
      conservation 79 ≥ baseline 67; full QG green. REMAINING in this item: `tardis_adapter.py` (2,880) +
      `solana_defi_handler.py` (2,125) — decompose by venue/transport. Repo: market-tick-data-service.
- [x] ✅ [REFACTOR] P2. **strategy-service DONE 2026-06-11** — strategy-service@590f65cf: catalog.py 2,371→140-line
      facade + 6 archetype-family modules; batch_handler.py 1,570→847 + 4 concern modules; TARGET_UNIVERSE content-hash
      identical pre/post; budget ratcheted 11→10 (census-honest). Cross-repo finding surfaced: execution-service
      `defi_target_universe_rebalance_recommender.py:310` imports `specs_for_archetype` from the strategy-service module
      path — KNOWN/sanctioned via UAC `service_contract_map.py:216` forbidden_exceptions + deprecation_ledger (move to
      UAC registry long-term); facade preserves the path so the consumer is unaffected. **MDPS DONE 2026-06-11** —
      market-data-processing-service@1cdf3ec: canonical_writer 2,412→536 facade + 4 modules
      (manifest/shaping/stamping/streaming); live_workers 1,731→516 + 2 modules (chain/streaming); databento classifier
      import flipped to its new UAC `external/databento` home + the banned MTDS path-dep REMOVED from pyproject
      (no-service↔service); budget ratcheted 10→7 (census-honest); full QG green. **execution-service DONE 2026-06-11**
      — execution-service@48eec983: kraken_rest_adapter 1,299→683+443+283 / uniswap 1,245→565+478+342 / aave
      1,136→629+578 / manual_instruction_api 1,085→815+368 / gcs_data_loading 1,012→781+281 + amm/betfair companions,
      all below 900 with facade modules preserved; budget ratcheted 24→21 (census-honest); full QG green (292s). lxml
      advisory: not a direct execution-service dep (transitive) — tracked under the pip-audit class in Phase 4. ITEM
      COMPLETE — flipping checkbox:
- [x] ✅ [REFACTOR] P3. COMPLETE 2026-06-11 — **cloud_feature_provider DONE** — ml-service@e011c82: 1,202→774 facade +
      `feature_query_support.py` (298) + `sports_feature_loader.py` (219); the loader resolves `get_storage_client`
      through the facade module so the existing test patch surface (`cloud_feature_provider.get_storage_client`) keeps
      intercepting; full QG green (2,181 tests). **training_orchestrator DONE 2026-06-11** — ml-service@b62c9fe:
      1,027→879 + `training_targets.py` (243, pure functions, patch surface intact); `_add_ml_training_args` 243 L →
      7-line dispatcher over 6 section helpers; both census Any-sites cleared; budget ratcheted 3→1 (only
      schema-provenance remains — Phase 3); MAX_FILE_LINES 1300→1000 (one 963 L file left, drop-to-900 noted in-file).
      **PM scripts DONE 2026-06-11** — unified-trading-pm@075f64279: generate-ui-vision-pptx 1,717→21-line entry +
      `scripts/ui_vision_pptx/` package (6 modules ≤607, python-pptx pyright carve-out extended to the package);
      `gcs_migration_bundle_2026_05_08.py` (1,143) + its tests DELETED per script-homes (one-off whose migration
      completed — Phase 9 ✅ 2026-05-20, plan archived). ITEM COMPLETE.

## Phase 1.5 — >900-line tail (post-sweep inventory 2026-06-11; the named worst offenders above are ALL split)

- [x] ✅ [REFACTOR] P1. **UTL `manifest_writer.py` 5,716L SPLIT 2026-06-11** — unified-trading-library@22f7030a: 13
      concern modules behind a package facade (`manifest_writer/__init__.py` re-exports the full pre-split surface;
      layout (a) — package shadows, monolith deleted). Pure code motion AST-verified (62/62 top-level defs + 37/37
      ManifestWriter methods verbatim; mixin composition Ingest/Record/Validation/Captured/Io over a
      `ManifestWriterCore` structural base — strict basedpyright 0 errors). Namespace-patch pre-audit honoured: all
      fleet patch targets (`lookup_contract`, `read_availability_index`, `_emit_manifest_load_size`,
      `_should_flush_to_gcs`, `_WRITE_FLUSH_INTERVAL`, `_time.sleep`, in-place `_WRITE_BUFFER`/`_INDEX_CACHE`/
      `_CANONICAL_CACHE`/`_LIVE_WRITERS` mutations) resolve via the facade (`_mw.`) and verified intercepting. All
      modules <900L (file-size class CLEARED); UTL size excludes retargeted from `*/manifest_writer.py` to the 7 modules
      carrying verbatim >50L methods; CODEX_MAX_VIOLATIONS stays 0, full QG green (118s). Consumer smokes:
      MDPS/deployment-api/features-service venv imports + MDPS test_canonical_writer_record_helpers 44 passed. Remaining
      from this line (NOT done here): `manifest_consolidator.py` (1,360) audit + `__init__.py` 2,279 facade-verify —
      tracked by the P3 tail item below. Repo: unified-trading-library.
- [x] ✅ [REFACTOR] P2. **DONE — verified 2026-07-27**:
      `find market_tick_data_service -name "*.py" -exec wc -l {} \; | awk '$1>900'` returns ZERO files fleet-wide in
      MTDS. All 11 named files were split (e.g. `lending_indices.py` →
      `lending_indices_{handler,rpc,morpho,parsers,subgraph}.py`; `dex_pools.py`/`dex_swaps.py`/`oracle_prices.py`/
      `gas_fee.py`/`perp_funding.py` likewise decomposed into per-concern handler modules, all <900L);
      `umi_tick_provider` now 633L, `evm_defi_handler` 606L, `solana_lst_archival` 817L. Was: MTDS >900 tail (11 files):
      umi_tick_provider 2,093 / evm_defi_handler 1,430 / lending_indices 1,390 / perp_funding 1,363 / databento_adapter
      1,360 / dex_pools 1,097 / oracle_prices 1,085 / polymarket_adapter 1,023 / solana_lst_archival 988 / dex_swaps 980
      / gas_fee 944 / websocket_runner 912 — split below 900 by venue/stage (drops the file-size class → 15→14). Repo:
      market-tick-data-service.
- [x] ✅ [REFACTOR] P3. **alerting router + ml pipeline DONE 2026-06-12** — alerting-service@8b12fcb: router.py
      1,022→821 + coalesce.py (119, predecessor WIP completed) + kill_switch_rules.py (145; `_publish_kill_switch_event`
      patch target preserved — router stays the caller, moved body routes log_event via the router namespace); 793 unit
      tests green, full QG green at budget 0. ml-service@6004170: uniform_training_pipeline 963→698 +
      IncrementalTrainingMixin (303; IncrementalResult re-exported, get_trainer routed via the facade for patchability);
      18/18 incremental tests green; MAX_FILE_LINES dropped 1000→900 per the in-file note; full QG green at budget 0.
      Both shipped via the dirty-deps carve-out (orchestrator-gated per the amended agents-edit/orchestrator-ships
      protocol, operator 2026-06-12).
- [x] ✅ [REFACTOR] P3-partial. **features delta_one orchestrator DONE 2026-06-12** — features-service@966b985a:
      922→798 + ManifestOutcomeMixin (orchestrator_manifest.py; ManifestWriter + validate_batch_completeness patch
      surfaces preserved via facade-namespace routing; the moved 87L manifest method honestly split to satisfy the 50L
      method cap its old home was excluded from); 10,290 tests green, quickmerge proper. onchain orchestrator (1,409)
      remains in the tail below.
- [x] ✅ [REFACTOR] P3-partial. **features onchain orchestrator DONE 2026-06-12** — features-service@06a83fb6: 1,409→835
      facade + 3 stage mixins (manifest/calculators/daily-loop, delta_one pattern; all patch surfaces module-bound via
      `X as X` aliases; >50L moved methods honestly split); 1,286 onchain unit + 12 integration tests green; full QG
      green at budget 0.
- [x] ✅ [REFACTOR] P3-partial. **UAC >900 audit DONE 2026-06-12** — unified-api-contracts@f1599ee: 4 logic-heavy splits
      behind unchanged paths (honest_coverage 1,141→788 / source_priority 1,018→562 / strategy_service instruction
      913→49+2 / synthetic 930→822; 76/76 symbols AST-identical) + 7 declarative exemptions DOCUMENTED with measured
      decl ratios in the SIZE_EXTRA_EXCLUDES header (errors/defi 90%, alerting/rules 84%, \_sports_match_contracts 92%,
      data_type_capability 91%, contracts.py, events.py, ml/schemas.py) + the operator data-registry set; 3 split
      entries REMOVED from the exclude list (size-exclude ratcheted); 363 module tests + 444 cassette-parity green;
      restaking_rewards.py deferred (lives in the wizard lane's architecture_v2 WIP).
- [x] ✅ [CODE] P1. **execution-service ≤5 ACHIEVED 2026-06-12** — execution-service@5b17132e: budget 7→**3**.
      Schema-provenance CLEARED honestly (167 measured sites: 160 `# CORRECT-LOCAL` with role-specific reasons incl. 11
      UAC-name-collision disambiguations, 4 dead types deleted, 0 moves — cross-repo grep found zero genuine external
      consumers); BaseModel-in-service cleared by the same markers; cloud-KMS glob documented (BYPASS_AUDIT §15, no UCI
      KMS facade exists); domain-client cleared via UTL.domain flip + base-gate bug confirmed. Remaining 3 honest:
      fn-size (25 pre-existing 51–133L methods, tracked in the 2026-05-17 issue), pip-audit (lxml FIXED; new
      mako/ujson/twisted/pyarrow advisories — coordinated unit below), project-id (2 unregistered-bucket sites needing
      cloud-providers.yaml registration first). 1,254 relevant tests green.
- [x] ✅ [REFACTOR] P3-partial. **strategy >900 tail DONE 2026-06-12** — strategy-service@08582739:
      archetype_slot_resolver 1,199→93 facade + 5 asset-group modules (STRATEGY_TYPE_TO_SLOT SHA-256 identical
      pre/post); legacy_strategy_mapping 1,048→172 loader + 55-row YAML SSOT + byte-equality pin test (registry.py
      precedent); portfolio archetypes 958→112 + base/simple/rank modules; zero caller churn, zero patch targets,
      basedpyright strict 0; budget stays 4 (file-size was excluded-dir hidden debt, honestly removed).
- [x] ✅ [CODE] P2. **RE-INVESTIGATED + CLOSED 2026-08-14** (`infra_satellite_ao_dispatch_batch16_2026_08_13.md` unit) —
      live state no longer matches this todo's 2026-06-12 diagnosis: execution-service's `pyproject.toml`/`uv.lock`
      already carry mako 1.3.12, twisted 26.4.0, ujson 5.13.0 (all at or above the cited fix versions — shipped in an
      untracked earlier pass); only pyarrow stayed at 23.0.1 (PM canonical still caps `<24.0.0`). A live pip-audit run
      (no `--ignore-vuln` extras — `QG_PIP_AUDIT_COMMON_IGNORES` is empty fleet-wide) plus a full `QG_SLICE=lint-codex`
      run on execution-service both came back **zero vulnerabilities / zero ❌** — pyarrow 23.0.1's only cited advisory
      (PYSEC-2026-113) is already fixed at this version and no other live CVE requires 24.0.0. **Verdict: the PM
      canonical-range widen is NOT executed** — there is no live security driver for it, and forcing a major pyarrow
      bump with none would be unjustified churn. execution-service's `CODEX_MAX_VIOLATIONS` ratcheted 3→0 in the same
      unit — execution-service@bb49911d27 (fn-size + hardcoded-project-id-prod classes also independently cleared).
      Re-open only if a future pip-audit run reports a genuine pyarrow finding. Original: **pip-audit follow-ups
      surfaced 2026-06-12 (execution unit)** — pyarrow 23.0.0 fix needs 24.0.0 but PM canonical caps `<24.0.0`
      (workspace-constraints.toml:80) → coordinated widen unit like the lxml one; + twisted 25.5.0 (fix 26.4.0 = major,
      via binance-futures-connector), mako 1.3.12 + ujson 5.12.1 in-range bumps. Repos: unified-trading-pm +
      execution-service (+lockers). **REHOME CHECK 2026-07-27**: no `infra_*_satellite_ao_dispatch_batch2*` plan exists
      yet (`ls plans/active/ | grep -i 'infra.*batch2'` → empty) — staying open here per the fallback instruction rather
      than pointing at a plan that doesn't exist. Rehome into batch2's own drafting pass once it exists.
- [x] ✅ [CODE] P2. **CLOSED 2026-08-09 (`/ag-closeout-audit infra` daily run) — DONE, stale checkbox reconciled.**
      Domain-client base-gate check was retargeted **2026-07-30** — verified live in
      `scripts/quality-gates-base/base-service.sh:1416-1426` today: "NO separate `unified_domain_client` package
      anywhere in the workspace. RETARGETED 2026-07-30: this check previously demanded imports come FROM
      `unified_domain_client`... fix retargets this check to the real invariant: domain-client symbols must come from
      `unified_trading_library`." The live gate (line 1532) now greps
      `from unified_trading_library|from unified_domain_client` as the accepted pattern set — matches the fix this todo
      asked for. This item was one of the 4 bundled into `infra_satellite_ao_dispatch_batch1_2026_07_26.md` § Deferred
      item 2 (G1); all 4 confirmed done via `infra_batch3_g1_g2_deferred_gate_update_2026_08_07.md`'s re-check (see that
      doc, now archived). Was: **STALE + self-contradictory (confirmed 2026-06-12)** — it demanded
      `unified_domain_client` which existed NOWHERE in the workspace (clients live in `unified_trading_library.domain`),
      had no opt-out, and CONTRADICTED the deep-import check for the same symbol.
- [x] ✅ [CODE] P3. **CLOSED 2026-08-08 (na-eligibility-audit, round7 RECLASSIFY sweep) — DONE via the cross-referenced
      doc.** `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s own copy of this exact item is `[x]` DONE at
      `unified-api-contracts@194f3f7f`: `is_at_risk` now resolves
      `LIQUIDATION_PARAMS_REGISTRY[AAVE_V3].health_factor_critical` (`1.15`) instead of the hardcoded `1.1`, mirroring
      execution-service's local copy; every consumer grepped, only a bare re-export found; a pinning regression test
      added (`tests/internal/unit/domain/execution_service/test_defi_position.py`); QG green. Independently re-verified
      this pass: `git merge-base --is-ancestor 194f3f7f origin/live-defi-rollout` confirms ancestor. Original text
      preserved below for record. Was: **UAC `internal/domain/execution_service/defi_position.py` STALE vs the live
      local copy** — UAC hardcodes liquidation threshold 1.1; the execution-service local uses
      `LIQUIDATION_PARAMS_REGISTRY[MarginModel.AAVE_V3].health_factor_critical` (1.15). Reconcile UAC to the
      registry-driven form. Repo: unified-api-contracts. **MIGRATED 2026-07-27** — confirmed present with real content
      as its own `[CODE] P3` todo in `infra_satellite_ao_dispatch_batch1_2026_07_26.md` ("Reconcile UAC's stale
      `defi_position.py` liquidation threshold to the registry-driven form"). Cross-referencing rather than leaving 2
      live copies of the same work — track it there going forward; not executed yet.
- [x] ✅ [CODE] P3. **DONE — `execution-service@980a6ad0`** ("feat(execution): wire delta-proxy repricer into live MM
      QUOTE-instruction handling", 2026-07-28). The "separate, concurrent workstream" the 2026-07-27 correction below
      referred to has landed: `DeltaProxyRepricer` is imported and wired into
      `execution_service/engine/quote_maintenance.py` (module docstring line 1 states the wiring; import at line 74)
      plus `execution_service/v2/handlers.py`, with `tests/unit/engine/test_delta_proxy_repricer.py` (+328L),
      `test_quote_maintenance.py` (+236L) and `test_router_and_handlers.py` (+67L) — 873 insertions across 6 files.
      **Independently re-verified 2026-08-02** (na-eligibility-audit, infra tranche), not taken on the finding's word:
      `git show --stat 89fbf99d` in the execution-service checkout,
      `git merge-base --is-ancestor 89fbf99d origin/live-defi-rollout` → ancestor confirmed, and the live wiring + test
      file re-read on disk. This closes finding 1 of
      `/plans/archive/issues/ag_closeout_audit_infra_parked_2026_07_31.md`, carried forward unreconciled by three
      consecutive `/ag-closeout-audit infra` runs (07-31, 08-01, 08-02) because that skill is scoped out of
      false-unchecked flips — it is in scope for this skill's KEEP-NA-stale-items verdict, which uses the same HARD
      evidence bar. Original text preserved below for the record. Was: **CORRECTED 2026-07-27**: the "dead-code delete
      candidate" framing below was WRONG per the operator's 2026-07-27 ruling
      (`june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED #19): it is **NOT dead code** — its dependency
      `UnderlyingTracker` is tested/used elsewhere, but the repricer class itself has zero tests/callers because it was
      built and never wired in. **Real work needed is the OPPOSITE of deletion: wire it into the live execution
      handler + add tests** (MM delta-proxy repricing IS wanted). A separate, concurrent workstream owns the actual
      execution-service code wire-in — this todo is the PLAN reference only. **REHOME CHECK 2026-07-27**: no
      `infra_*_satellite_ao_dispatch_batch2*` plan exists yet — staying open here (corrected framing) rather than
      pointing at a plan that doesn't exist; rehome into batch2 once drafted. Was:
      `execution_service/engine/ delta_proxy_repricer.py` is unreferenced (zero imports repo-wide, 2026-06-12 sweep) —
      dead-code delete candidate per the delete-deprecated rule; needs a quick operator/architect confirm it isn't a
      planned consumer's WIP. Repo: execution-service.
- [x] ✅ [CODE] P2. **deployment-api 16→6 (2026-06-12)** — deployment-api@94e4feb: wave-4b agent cleared 10 classes
      (schema-provenance CORRECT-LOCAL triage, os.getenv, Any-types, imports-in-fn, empty-fallbacks); honest measured
      V=6; full QG green. One step from the ≤5 ceiling.
- [x] ✅ [REFACTOR] P3-partial. **instruments refdata adapters DONE 2026-06-12** — instruments-service@354ab43: tardis
      1,348 / databento ~1,222 / polymarket 1,184 → packages behind unchanged paths (all modules <900, \_pkg_ref
      namespace proxies; the package-shadowed old polymarket.py removed — it was silently dead + dragging coverage;
      exclude globs retargeted to package depth); 3,548 tests green, quickmerge proper. REMAINING: `_solana_utils.py`
      (1,016) — deferred at agent limit.
- [x] ✅ [REFACTOR] P3-partial. **agent-orchestrator server tail DONE 2026-06-12** — agent-orchestrator@209937f:
      worker_liveness 1,215 / state_store 1,118 / worktree_clean_check 1,012 / models 932 → packages behind unchanged
      import paths (patch surfaces module-bound; WorkerLivenessKicker dynamic attrs declared; intra-package privacy
      pragmas); scripts/check.sh exit 0 (basedpyright 248→0 errors after orchestrator cleanup), 505 tests green; shipped
      direct-to-LDR per the AO G6 transitional model.
- [x] ✅ [REFACTOR] P3. **DONE 2026-08-08** — instruments-service@06791d0e: `_solana_utils.py` (1,068L) split into
      `_solana_utils.py` (815L, RPC+cache+timestamp resolution) + `_solana_pool_discovery.py` (271L, pool-discovery
      concern). All callers updated (`raydium.py` import split; test patch paths repointed to
      `_solana_pool_discovery.*`; `quality-gates.sh` exclusion arrays extended; `QUALITY_GATE_BYPASS_AUDIT.md` updated).
      Pre-existing sports golden drift + `smoke_matrix.py` BETFAIR fallback bug fixed in the same commit. 5,234 tests
      green. **REWRITTEN 2026-07-27** (per `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s "Findings surfaced
      during extraction" — this catch-all is "almost entirely superseded by `[x]` items ABOVE it in the same doc"):
      every other named file in the original list below is now split and `[x]` above (instruments refdata adapters
      `@354ab43`; features onchain/delta_one orchestrators `@06a83fb6`/`@966b985a`; strategy archetype_slot_resolver +
      legacy_strategy_mapping + portfolio archetypes `@08582739`; agent-orchestrator
      worker_liveness/state_store/worktree_clean_check/models `@209937f`; alerting router `@8b12fcb`; ml
      uniform_training_pipeline `@6004170`; UAC honest_coverage `@f1599ee`, 1,141→788). The genuine residual, from THIS
      catch-all's own original scope, was **instruments-service `_solana_utils.py`** — now done. Caveat noted
      2026-07-27: `api_football.py` (1,201L) and `footystats.py` (1,199L) are sports-tranche scope, out of this item.

## Phase 2 — Deep-import facade (the 8 repos the parity audit flagged)

- [x] ✅ [REFACTOR] P2. COMPLETE 2026-06-11 — facade: UAC@c8287d3 (all 46 fleet-consumed two-level symbols at the
      one-level facade; 3 modules via PEP 562 lazy `__getattr__` for root-init cycles). Consumer call-site flips shipped
      per-repo: deployment-api@5127517 (all 8 sites, class CLEARED), execution-service@fb116d98 (class CLEARED),
      strategy-service@6aff0c48 (class CLEARED, zero deep sites remain), MDPS@4b6c53a (class CLEARED),
      instruments-service@cb51c98 (weather.py), SIT@a458443 (3 test files). MTDS's remaining deep imports are
      `canonical.partition_paths` in migration scripts (NOT registry symbols — outside this item's scope, stays in its
      V=15 accounting). Deep-path removal from UAC deferred until a fleet-wide pre-audit shows zero importers
      (additive-first contract). Original: Re-export the two-level symbols at the UAC one-level facade
      ({market_data_categories, data_status_axis_matrix, chain_env, defi_venues, withdrawal_approval_rules,
      tardis_free_coverage, …}), then switch the call sites to `from unified_api_contracts.registry import <X>` and drop
      each repo's deep-import violation. Affected services (per the 2026-06-10 audit): deployment-api,
      execution-service, instruments-service, market-data-processing-service, market-tick-data-service,
      strategy-service, system-integration-tests. Repo: unified-api-contracts (facade) + the 7 consumers (call sites +
      ratchet).
- [x] ✅ [CODE] P1. SUPERSEDED-SATISFIED 2026-06-11 — deployment-api@5127517 ratcheted 24→**22** (below the 23 target):
      Phase 2 cleared the deep-import class AND the route/service splits cleared file-size. (Interim history: a
      transient 24→25 bump by slot-1 for manifest-alignment was reverted same-day @6b7aa69 once the PM
      workspace-manifest dep edge was fixed.) Original: budget 23→24 revert once deep-imports clear. Repo:
      deployment-api.

## Phase 3 — Schema provenance (local types → UAC)

- [ ] [REFACTOR] P2. Move local `BaseModel`/`TypedDict`/`dataclass` domain types out of service source into
      `unified_api_contracts` domain modules (or `unified_api_contracts.internal`) per the schema-provenance check — the
      `# CORRECT-LOCAL:` marker is for genuine response-shape DTOs only; real domain contracts must live in UAC.
      Per-repo; biggest contributors first (per the Phase-0 census). Repos: UAC + the offending services. **ACKNOWLEDGED
      (not migrated) 2026-07-27**: `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s Deferred item 17 already flags
      this (alongside the Phase 4 per-repo catch-all this doc's own Phase 4 section had) as
      "TOO-LARGE-OR-RISKY-FOR-A-BATCH-TODO ... not precisely scoped enough to be worker-determinable as written" — needs
      its own dedicated phased design pass, not a batch-todo extraction. Stays open here as-is; no duplicate created.

## Phase 4 — Residual violation classes

- [x] ✅ [CODE] P1. **ml-service CODEX_MAX_VIOLATIONS=0 ACHIEVED 2026-06-12 (Phase-3 pilot)** — ml-service@00855f6:
      schema-provenance cleared honestly (29 `# CORRECT-LOCAL` markers on genuinely process-local types, 4 dead
      TypedDicts deleted; no UAC moves needed), budget 1→0. First repo to complete the full 5→0 journey.
- [x] ✅ [CODE] P2. **deployment-api 22→16 (2026-06-12)** — deployment-api@0686968: os.getenv class + comment
      false-positives + empty-fallback sites cleared across 17 files (honest measured V=16); full QG green. Remaining to
      ≤5: fn-size, Any-types, schema-provenance (Phase 3) et al per in-file comment.
- [x] ✅ [CODE] P2. **execution-service 11→7 (2026-06-12)** — empty-fallback + project-id classes cleared + the lxml
      pip-audit class (>=6.1.0 bump rode this unit); honest measured V=7. Remaining: schema-provenance (~183 types,
      Phase 3), fn-size, cloud-SDK (KMS facade gap), domain-client (stale check target), deep-imports.
- [x] ✅ [REFACTOR] P1. **UTL manifest_writer split FINISHED 2026-06-11** — unified-trading-library@22f7030a: stash
      popped, predecessor's 12 staged modules verified against HEAD (def-name conservation exact), facade `__init__`
      wired (+ new `_core.py` structural base), 2 patch-interception gaps the WIP missed fixed (`_should_flush_to_gcs`
      call + `_WRITE_FLUSH_INTERVAL` read now resolve via `_mw.`), consumer smokes + MDPS record-helpers suite green,
      full UTL QG exit 0. Shipped via the dirty-deps carve-out (UAC carried foreign prospectus-lane WIP at quickmerge
      pre-flight; Pass-1 sentinel green). Repo: unified-trading-library.
- [x] ✅ [CODE] P2. **execution-service imports-inside-functions class CLEARED 2026-06-11** —
      execution-service@2fdc348c: 116 sites across 57 files (51 hoisted: stdlib/UAC/UTL/light deps; 65 justified
      per-line `# noqa: imports-inside-functions`: lazy heavy SDKs nautilus/web3/driftpy/solana, per-provider KMS,
      call-time patch surfaces, sanctioned/tracked cross-service); budget ratcheted 12→11; full QG green (7,692 tests;
      the isolation_policy/rpc_fallback patch-surface lazies were load-bearing and kept lazy). BONUS finding: 2
      UNSANCTIONED cross-service imports surfaced (leg_controller_runner→strategy_service.position,
      mtds_book_provider→market_tick_data_service.reader + its path dep) — filed in
      utl_uac_reuse_consolidation_remediation_2026_06_10.md. Shipped via the dirty-deps carve-out (UAC/MTDS carry the
      mtds_coverage_75 lane's WIP).

- [x] ✅ [CODE] P2. COMPLETE 2026-06-12 — coordinated lxml bump: PM canonical range widened to `>=6.1.0,<7.0.0`
      (workspace-constraints.toml + canonical-dependency-manifest.json, shipped by the wave-3 lxml agent);
      e2e-testing@eaa2f37 + system-integration-tests@8000740 re-locked; execution-service bumped its direct dep (lxml
      used only as the BeautifulSoup parser backend — no direct lxml API use) + re-locked, rode the 11→7 ratchet unit.
      Original: **lxml PYSEC-2026-87 fleet bump (coordinated unit)** — 2026-06-11 diagnosis: lxml is NOT a UAC dep; the
      vulnerable 5.4.0 lock lives in execution-service (direct dep `lxml>=5.0,<6.0` pyproject:290) +
      e2e-testing/system-integration-tests locks, and the fleet canonical range `lxml>=5.0,<6.0` (PM
      `workspace-constraints.toml:58` + `canonical-dependency-manifest.json:204-205`) CONFLICTS with the ≥6.1.0 fix. One
      unit: widen the PM canonical range to `>=6.1.0,<7.0.0`, bump execution-service (+e2e/SIT) pyproject, re-lock, full
      tests (lxml 6.x API check on the consuming code), ratchet execution-service's pip-audit class. Repos:
      unified-trading-pm + execution-service + e2e-testing + system-integration-tests.

- [x] ✅ [CODE] P2a. No-code census-honest ratchets shipped 2026-06-11: deployment-service 8→1
      (deployment-service@8d8cac5), ibkr-gateway-infra 4→1 (ibkr-gateway-infra@d76447e), ml-service 5→3 (in flight, QG
      running). All three QG-green at the new budgets before commit.
- [x] ✅ [CODE] P2d. **MDPS ≤5 ACHIEVED 2026-06-11** — market-data-processing-service@4b6c53a: budget 7→1 (only
      schema-provenance remains — Phase 3). Cleared: deep-imports (registry sites flipped to one-level facade),
      os.getenv, asyncio.run-in-loop, imports-in-fn, run_lifecycle pairing (live_mode_handler), preflight
      emit_preflight_skip (process_handler + orchestration_service). 31 files, full QG green.
- [x] ✅ [TEST] P2. **MTDS `tests/market_interface/` (70 test files) is NOT collected by the QG** (2026-06-11 finding,
      eb33603 unit) — the gate runs the default `PYTEST_UNIT_DIR` (`tests/unit/` [+integration]), so the adapter
      canonical-output suites never run in QG/CI. **Pointer, not the SSOT for this fix** (resolved
      `autonomous_session_operator_decisions_2026_07_25.md` entry #34, 2026-07-26): a competing widening exists in
      `/plans/archive/issues/mtds_ungated_test_families_2026_07_17.md`, which measured the real cost as 40 pre-existing
      failures (not absorbable in the same unit as this todo assumes) and prescribed a narrower target list +
      fix-the-40-first ordering — turning on the whole tree with 40 known failures unfixed would red every unrelated
      MTDS commit. **That doc's fix landed and it is now archived (2026-07-31, na-eligibility-audit ci tranche) — all 70
      files gated, `PYTEST_UNIT_DIR` widened `market-tick-data-service@4849d4f6`, this todo's own stated satisfaction
      condition is met.** Repo: market-tick-data-service.
- [x] ✅ [CODE] P2c. **none-budget repos pinned at 0 (census-honest) 2026-06-11** — alerting-service@c41baf1,
      client-reporting-api@c8a32ff, fund-administration-service@3d32a3e, greeks-service@9efb1e7,
      trading-agent-service@09d8dae (each double-QG-green at budget 0 before ship); system-integration-tests pinned 0 +
      QG-green, quickmerge pending peer-clean deps (this plan's other lanes) — shipped by the orchestrating slot when
      lanes land. unified-trading-api was pinned 0 earlier (@42f12ab); agent-orchestrator runs a custom gate without a
      codex section (pin N/A — documented census exception).
- [x] ✅ [CODE] P2b. **strategy-service ≤5 ACHIEVED 2026-06-11** — strategy-service@6aff0c48: budget 10→4. Cleared 6
      classes: deep-imports (both registry sites flipped to the one-level facade, zero deep sites remain), os.getenv
      (recovery_event_helper → StrategyServiceConfig fields), imports-in-fn (8 sites hoisted), empty-dict/list (5
      justified noqas), prod-project-id-in-tests, fn-size (close_all execute()s + PreflightRunner.run +
      SportsFeatureSubscriber extracted). Remaining 4: empty-str (~85 sites), broad-except (17), BaseModel routers
      (Phase 3), STEP 5.37 Reg-T. FINDING: UAC `LIQUIDATION_PARAMS_REGISTRY` has NO REG_T MarginModel row and
      `LiquidationParams` lacks initial-margin fields — `risk/v2/greek_model.py`'s 0.5/1.5 Reg-T multipliers cannot be
      wired to the registry until UAC adds them (UAC-side todo for the 5.37 class).
- [x] ✅ [CODE] P2. **≤5-CEILING GOAL ACHIEVED FLEET-WIDE — verified 2026-07-27**:
      `grep -H '^CODEX_MAX_VIOLATIONS' */scripts/quality-gates.sh` across all 25 repos shows the max value is **5**
      (deployment-api only; its own further 5→0 stretch goal is tracked separately below + cross-referenced into
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md`). Every other repo is at 0-4: alerting-service/
      client-reporting-api/features-service/fund-administration-service/greeks-service/market-tick-data-service/
      ml-service/system-integration-tests/trading-agent-service/unified-trading-api/unified-trading-library/
      unified-trading-pm at 0; batch-live-reconciliation-service/deployment-service/ibkr-gateway-infra/
      market-data-processing-service at 1; unified-api-contracts at 2; execution-service/instruments-service at 3;
      strategy-service at 4 (agent-orchestrator runs a custom gate with no codex section — documented census exception,
      unaffected). This satisfies this plan's own Success Criteria #1 verbatim
      ("`grep CODEX_MAX_VIOLATIONS */scripts/quality-gates.sh` shows no value > 5"). The broader "clear the remaining
      check-classes toward 0" ambition per-repo is NOT fully done (several repos still carry 1-4) but is no longer
      blocking anything — ≤5 is the plan's stated ceiling, not a mandate to reach 0 everywhere; further reduction is
      opportunistic, tracked per-repo where a concrete follow-up exists (deployment-api below) rather than as one
      open-ended catch-all. Was: Per repo, clear the remaining check-classes the census surfaces — `os.getenv` →
      `UnifiedCloudConfig`, `Any` → specific types, empty-string/dict/list fallbacks → fail-fast, backward-compat shims
      → delete, function/method-size > limits → extract. Ratchet `CODEX_MAX_VIOLATIONS` down to ≤5 per repo as classes
      clear. Repos: all over-5 (deployment-api, execution-service, market-tick-data-service, strategy-service,
      market-data-processing-service, deployment-service, unified-api-contracts).

## Success criteria

- Every service + library repo's `CODEX_MAX_VIOLATIONS` ≤ 5 (verified:
  `grep CODEX_MAX_VIOLATIONS */scripts/quality-gates.sh` shows no value > 5), and every repo's lint-codex slice is green
  on a now-honest LOCAL run + CI v2.
- No source file > 900 lines without a `# QG-allow:` exception carrying a named successor plan + date; the four
  > 4,000-line files (registry 18k / orchestrator 8k / data_status 6.6k / seed 5.1k / server 4.4k) are split.
- No `FUNCTION_SIZE_EXTRA_EXCLUDES` glob hides an oversized file (every exclude removed or justified in-file).
- Budgets only ratcheted DOWN; a bump is review-blocking (enforce in the PR template / reviewer checklist).

## deployment-api — remaining 5 (added 2026-06-19)

- [x] ✅ [INFRA] P2. **Drive deployment-api codex violations 5 → 0.** **DONE (na-eligibility-audit 2026-08-03)** —
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s "Drive deployment-api's codex violations from 5 to 0" todo
      (DONE 2026-07-26) shipped this exact work: `deployment-api@4c4b007` cleared all 3 remaining classes
      (imports-inside-functions, direct-cloud-SDK, broad-except) to `V=0`, `CODEX_MAX_VIOLATIONS` ratcheted 3→0, full
      `quality-gates.sh` green (5077 passed). Same-commit ruff ratchet-down also verified:
      `unified-trading-pm@a674e1ff3` ("flip deployment-api codex-violations item (deployment-api@4c4b007)") lowers
      `scripts/quality_gates/ruff_rule_ratchet_baseline.yaml`'s deployment-api row `dtz` 11→10 and `tid251` 20→19,
      confirmed ancestor of `origin/live-defi-rollout`. Ratcheted **6→5** on 2026-06-19 (cleared the deep-UAC-import in
      `utils/pipeline_mode_paths.py` → facade `from unified_api_contracts import Mode`). Remaining 5, all
      pre-existing/foreign (surfaced when the version-alignment lag unblocked the QG during the dep-order-surface ship):
      (1) **imports-inside-functions** (`firebase_auth.py`, `health_routes.py`, `workers/deployment_processor.py` — some
      are deliberate lazy/circular-avoidance; triage each); (2) **direct cloud-SDK imports**
      (`from google.cloud import …` in firebase_auth / health_routes — route through
      `unified_trading_library.cloud_interface` `get_storage_client`/`get_secret_client`); (3) **files >900 lines**; (4)
      **function/method size** (~24 over the limit, e.g. `deployment_manager.run_deployment_background` 155L,
      `services/deploy_missing_launch.launch_deploy_missing_vm` 236L). Ratchet `CODEX_MAX_VIOLATIONS` down as each
      clears. Repo: deployment-api. Provenance: 2026-06-19 operator review. **MIGRATED 2026-07-27** — confirmed present
      with real content (the identical 4-class breakdown) as its own `[INFRA] P2` todo in
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md` ("Drive deployment-api's codex violations from 5 to 0").
      Cross-referencing rather than leaving 2 live copies of the same work — track it there going forward; not executed
      yet. Re-verified 2026-07-27: deployment-api's `CODEX_MAX_VIOLATIONS` is still 5 (fleet-wide check above).

## Codex SSOT updates

- `/codex/06-coding-standards/quality-gates.md` § "CODEX_MAX_VIOLATIONS is a ratchet-down, ≤5 ceiling" + the file-size /
  function-size limits as first-class (not glob-exempt-forever).
- `/codex/06-coding-standards/README.md` § file-size discipline (900 max / 700 warn) — cross-link the worst-offender
  split plan.

## Out of scope (named)

- Changing the lint-codex CHECK definitions / adding new classes — that is `harden_grepable_rules_into_ci_gates`
  territory; this plan only DRIVES THE COUNTS DOWN against the existing checks.
- The `ci_local_qg_parity` grep-P fix (DONE — prerequisite, not part of this plan's scope).

## Archive-readiness verdict (2026-07-27, `/plan-vintage-audit` migration pass)

**Unlock GRANTED** 2026-07-27 (`june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED #19: "codex_violations —
unlock GRANTED") — this doc's `locked_by: live-defi-rollout` no longer blocks archival on its own. The plan's own
Success Criteria #1 (fleet-wide `CODEX_MAX_VIOLATIONS` ≤ 5) is now met and verified, both the MTDS and this catch-all's
own >900-line-tail scope are done (flipped above), and the 2 items already duplicated in
`infra_satellite_ao_dispatch_batch1_2026_07_26.md` (UAC `defi_position.py`, deployment-api 5→0) are now cross-referenced
rather than left as 2 live copies. **NOT archived** — real remainder genuinely exists and has nowhere else to go yet:
pip-audit follow-ups (pyarrow/twisted/mako/ujson), the domain-client base-gate retarget (parked in batch1's Deferred,
not yet landed), the corrected `delta_proxy_repricer.py` wire-in item, Phase 3's schema-provenance migration
(acknowledged too-large-for-a-batch-todo in batch1's Deferred), and deployment-api's own 5→0 stretch. None of these have
a `batch2` to rehome into yet (`infra_*_satellite_ao_dispatch_batch2*` does not exist as of this pass) — per this
migration's own fallback instruction, they stay open here rather than pointing at a plan that doesn't exist. Re-check
for a `batch2` on the next pass and rehome then.

## Progress Log

- **na-eligibility-audit 2026-08-18** (infra tranche) [body-hash:2789cba752f52748]: KEEP-NA, valid — unchanged since
  2026-08-09; now 1 open item (was 2 — the pip-audit/domain-client Phase-4 catch-alls closed since). Sole remaining
  item (Phase 3 schema-provenance local-types-to-UAC migration) is explicitly acknowledged in-doc as needing "its
  own dedicated phased design pass, not a batch-todo extraction" — not worker-determinable alone.
- **na-eligibility-audit 2026-08-09** (infra tranche) [body-hash:d073265da4a96484]: KEEP-NA, valid — 2 open items remain
  (pip-audit fleet-wide bump: DEPENDENCY_BLOCKED; Phase 3 schema-provenance migration: GENUINE_WORK, both explicitly
  too-large-for-a-batch-todo). The stale G1-item-1 duplicate this doc carried was independently closed today by the
  `/ag-closeout-audit infra` run (dispatch agt-3b6f6b), cross-verified via `base-service.sh:1416-1426`.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, stale items — closed the UAC
  `defi_position.py` item with hard evidence (`unified-api-contracts@194f3f7f`, ancestor-verified), which was already
  DONE in the cross-referenced `infra_satellite_ao_dispatch_batch1_2026_07_26.md` but never reflected back here. Doc
  stays NA overall: the 3 remaining items (pip-audit follow-ups, the domain-client base-gate retarget, Phase-3
  schema-provenance) were checked against today's operator-Q&A rulings cheat sheet and against every newer infra batch
  (batch1/6/7) — none is a clean match. The domain-client base-gate retarget's `base-service.sh`/`base-library.sh`
  contention (batch1 finding 2, "batch these 4 deferred items into ONE sequential unit in the next infra batch") now
  appears CLEARED — the two sibling claims that created it
  (`cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s lint-generalization item, done;
  `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md`, archived) are both resolved, and a corpus-wide grep found zero
  other open todos touching either file — but this doc's own item is only 1 of the 4 the operator ruled must land as ONE
  bundled `sequential: true` unit, so a solo flip here would violate that ruling rather than honor it; flagging as a
  strong RECLASSIFY-candidate for a fresh, properly-scoped batch bundling all 4, not actioned this run. The pip-audit
  item remains genuinely blocked (batch1 finding 7: dep-manifest contention across `workspace-constraints.toml` + 15
  repos, "genuinely too large for a batch todo") — `cve_affected_pinned_deps_remediation_2026_06_18.md` (an active
  `assigned_vm: planning` doc) covers ujson/twisted/ msgpack but not pyarrow/mako, so only partial overlap. Phase 3's
  schema-provenance migration remains an explicitly acknowledged too-large-for-a-batch-todo design pass.
  `assigned_vm: NA` correct.
- **na-eligibility-audit 2026-08-07** (infra tranche): KEEP-NA, valid — unchanged since 2026-08-02; re-verified the 5
  open items fresh. The UAC `defi_position.py` citation (line ~373) remains correctly cross-referenced into
  `infra_satellite_ao_dispatch_batch1_2026_07_26.md` (no new citation needed — same conclusion as the 2026-07-30 audit).
  Re-checked whether a newer infra batch (4/6/7, batch2/3/5 archived) now covers the pip-audit follow-ups or the
  domain-client base-gate retarget: `grep -rlE 'domain-client base-gate|unified_domain_client'` and a pyarrow/twisted/
  mako/ujson grep across `plans/active/` both still resolve only to `infra_satellite_ao_dispatch_batch1_2026_07_26.md`
  (Deferred, unlanded) and `batch4_2026_07_31.md` (which itself states "the other 3 uncovered items... remain correctly
  gated by batch1's own Deferred classification") — still genuinely unrehomed, consistent with the 07-30/08-02 finding.
  The `_solana_utils.py` split and the Phase-3 schema-provenance item are unchanged (bounded-but-undone refactor /
  design-judgment-call respectively). No stale items to close this pass.
- **na-eligibility-audit 2026-07-30** (infra tranche, dispatch agt-30721a): KEEP-NA, stale-items — the 2 checkboxes
  already carrying a "MIGRATED 2026-07-27" citation (UAC `defi_position.py` reconcile; deployment-api codex-violations
  5→0) are confirmed correctly cross-referenced into `infra_satellite_ao_dispatch_batch1_2026_07_26.md`, no new citation
  needed. Doc stays NA overall — Phase 3 schema-provenance migration is a genuine design/judgment call (already flagged
  too-large-for-a-batch-todo in batch1's own Deferred section). Re-checked whether
  `infra_satellite_ao_dispatch_batch2_ 2026_07_27.md` (which now exists, unlike when this doc's own "does not exist as
  of this pass" note was written) covers the pip-audit-bump / domain-client base-gate retarget /
  `delta_proxy_repricer.py` wire-in items this doc flags as waiting for exactly such a batch: confirmed zero hits, still
  genuinely uncovered — flagging these 3 items as a future RECLASSIFY candidate for a dedicated follow-up pass, not
  actioned this run.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, stale items — 1 item closed with
  verified evidence.** In scope this run because the doc was edited since its 2026-07-30 marker (context-scout
  backfill + a 2026-07-31 ci-tranche flip of the MTDS `PYTEST_UNIT_DIR` item). Read end-to-end; `grep -cE '^- \[ \]'` =
  **7** at entry, matching this verdict's item count, **now 6**. Closed: the `delta_proxy_repricer.py` `[CODE] P3` item,
  which `execution-service@980a6ad0` (2026-07-28) already satisfied — evidence re-derived from the execution-service
  checkout this run (`git show --stat`, ancestor check against `origin/live-defi-rollout`, live re-read of
  `quote_maintenance.py`'s import + the test file), not accepted from the reporting doc. Doc stays NA on the remaining
  6: Phase 3's schema-provenance migration is flagged too-large-for-a-batch-todo in batch1's own Deferred section (a
  genuine design pass, not a bounded todo), 2 items (UAC `defi_position.py`, deployment-api 5→0) are already
  cross-referenced into `infra_satellite_ao_dispatch_batch1_2026_07_26.md`, and the 3 flagged as awaiting a batch2
  (pip-audit bumps, domain-client base-gate retarget, `delta_proxy_repricer` — the last now closed above) are re-checked
  again this run: `infra_satellite_ao_dispatch_batch2_2026_07_27.md` still does not cover the remaining 2.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) -- swapped in the doc's own flagship examples
  (features-service `registry.py`, instruments-service `engine/orchestrator/`) since prior scope was codex/plan-only;
  dropped README.md + batch2 (batch2 no longer covers the remaining items per the na-eligibility-audit note above).
- **context-scout 2026-08-15**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **context-scout 2026-08-19**: re-scouted; context_scope unchanged (4 entries), all 4 paths still resolve, still accurate.
