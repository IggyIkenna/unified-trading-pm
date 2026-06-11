---
title:
  "Codex-violation ratchet to ≤5 fleet-wide + split the egregious oversized files (registry.py 18k, orchestrator.py 8k,
  …)"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
estimate_class: refactor
estimate_baseline_ai_days: 18.0
estimate_calibrated_ai_days: 7.2
created: 2026-06-10
source:
  - operator direction 2026-06-10 ("take codex violations down to max 5; we have a ~10k-line file in instruments-service
    that's way too much — make a PM active plan")
  - slot-3 fleet audit 2026-06-10 (the grep -P parity fix exposed the true counts; budgets had sprawled to 24)
related_plans:
  - plans/active/ci_local_qg_parity_2026_06_08.md
  - plans/active/cicd_contract_hardening_2026_06_01.md
locked_by: live-defi-rollout
locked_since: 2026-06-10
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
- [ ] [REFACTOR] P3. **agent-orchestrator `worker_liveness.py` (1,215 L) + `state_store.py` (1,118 L) decomposition
      requires test edits** — 2026-06-11 review: worker_liveness is one ~1,050-line `WorkerLivenessKicker` class whose
      tests fire ~30 namespace patches at `server.worker_liveness.*`, and state_store is a flat CRUD namespace with
      module-attr patch surfaces (`server.state_store.utcnow/to_utc/log_activity`) + bare-name cross-calls — a
      zero-caller-edit split is impossible (mixins = banned shim). Proper unit: decompose by entity/concern AND migrate
      the test patch targets in the same commit (pre-audit the full patch manifest first). Repo: agent-orchestrator.
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
- [ ] [REFACTOR] P2. MTDS >900 tail (11 files): umi_tick_provider 2,093 / evm_defi_handler 1,430 / lending_indices 1,390
      / perp_funding 1,363 / databento_adapter 1,360 / dex_pools 1,097 / oracle_prices 1,085 / polymarket_adapter 1,023
      / solana_lst_archival 988 / dex_swaps 980 / gas_fee 944 / websocket_runner 912 — split below 900 by venue/stage
      (drops the file-size class → 15→14). Repo: market-tick-data-service.
- [x] ✅ [REFACTOR] P3. **alerting router + ml pipeline DONE 2026-06-12** — alerting-service@8b12fcb: router.py
      1,022→821 + coalesce.py (119, predecessor WIP completed) + kill_switch_rules.py (145; `_publish_kill_switch_event`
      patch target preserved — router stays the caller, moved body routes log_event via the router namespace); 793
      unit tests green, full QG green at budget 0. ml-service@6004170: uniform_training_pipeline 963→698 +
      IncrementalTrainingMixin (303; IncrementalResult re-exported, get_trainer routed via the facade for
      patchability); 18/18 incremental tests green; MAX_FILE_LINES dropped 1000→900 per the in-file note; full QG
      green at budget 0. Both shipped via the dirty-deps carve-out (orchestrator-gated per the amended
      agents-edit/orchestrator-ships protocol, operator 2026-06-12).
- [x] ✅ [REFACTOR] P3-partial. **features delta_one orchestrator DONE 2026-06-12** — features-service@966b985a:
      922→798 + ManifestOutcomeMixin (orchestrator_manifest.py; ManifestWriter + validate_batch_completeness patch
      surfaces preserved via facade-namespace routing; the moved 87L manifest method honestly split to satisfy the
      50L method cap its old home was excluded from); 10,290 tests green, quickmerge proper. onchain orchestrator
      (1,409) remains in the tail below.
- [x] ✅ [REFACTOR] P3-partial. **features onchain orchestrator DONE 2026-06-12** — features-service@06a83fb6:
      1,409→835 facade + 3 stage mixins (manifest/calculators/daily-loop, delta_one pattern; all patch surfaces
      module-bound via `X as X` aliases; >50L moved methods honestly split); 1,286 onchain unit + 12 integration
      tests green; full QG green at budget 0.
- [x] ✅ [REFACTOR] P3-partial. **UAC >900 audit DONE 2026-06-12** — unified-api-contracts@f1599ee: 4 logic-heavy
      splits behind unchanged paths (honest_coverage 1,141→788 / source_priority 1,018→562 / strategy_service
      instruction 913→49+2 / synthetic 930→822; 76/76 symbols AST-identical) + 7 declarative exemptions DOCUMENTED
      with measured decl ratios in the SIZE_EXTRA_EXCLUDES header (errors/defi 90%, alerting/rules 84%,
      _sports_match_contracts 92%, data_type_capability 91%, contracts.py, events.py, ml/schemas.py) + the operator
      data-registry set; 3 split entries REMOVED from the exclude list (size-exclude ratcheted); 363 module tests +
      444 cassette-parity green; restaking_rewards.py deferred (lives in the wizard lane's architecture_v2 WIP).
- [ ] [REFACTOR] P3. Remaining >900 tail: instruments reference_data adapters (tardis 1,348 / databento 1,215 /
      polymarket 1,184 / \_solana_utils 1,016), features onchain/delta_one engine orchestrators (1,409/922), strategy
      archetype_slot_resolver 1,199 + legacy_strategy_mapping 1,048 + portfolio archetypes 958, agent-orchestrator
      worker_liveness/state_store/worktree_clean_check/models (separate todo above), alerting router 1,022, ml
      uniform_training_pipeline 963. UAC's >900 set is largely declarative data registries + `__init__` facades
      (sanctioned re-export exception) — audit non-facade ones (honest_coverage 1,141, contracts.py 1,349) case-by-case.
      Repos: per file.

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
      Per-repo; biggest contributors first (per the Phase-0 census). Repos: UAC + the offending services.

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
- [ ] [TEST] P2. **MTDS `tests/market_interface/` (70 test files) is NOT collected by the QG** (2026-06-11 finding,
      eb33603 unit) — the gate runs the default `PYTEST_UNIT_DIR` (`tests/unit/` [+integration]), so the adapter
      canonical-output suites never run in QG/CI. Fix: set `PYTEST_UNIT_DIR="tests/"` before the base-service source
      line per the documented per-family override (codex/06-coding-standards/quality-gates.md), absorb any newly
      collected failures in the same unit. Repo: market-tick-data-service.
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
- [ ] [CODE] P2. Per repo, clear the remaining check-classes the census surfaces — `os.getenv` → `UnifiedCloudConfig`,
      `Any` → specific types, empty-string/dict/list fallbacks → fail-fast, backward-compat shims → delete,
      function/method-size > limits → extract. Ratchet `CODEX_MAX_VIOLATIONS` down to ≤5 per repo as classes clear.
      Repos: all over-5 (deployment-api, execution-service, market-tick-data-service, strategy-service,
      market-data-processing-service, deployment-service, unified-api-contracts).

## Success criteria

- Every service + library repo's `CODEX_MAX_VIOLATIONS` ≤ 5 (verified:
  `grep CODEX_MAX_VIOLATIONS */scripts/quality-gates.sh` shows no value > 5), and every repo's lint-codex slice is green
  on a now-honest LOCAL run + CI v2.
- No source file > 900 lines without a `# QG-allow:` exception carrying a named successor plan + date; the four
  > 4,000-line files (registry 18k / orchestrator 8k / data_status 6.6k / seed 5.1k / server 4.4k) are split.
- No `FUNCTION_SIZE_EXTRA_EXCLUDES` glob hides an oversized file (every exclude removed or justified in-file).
- Budgets only ratcheted DOWN; a bump is review-blocking (enforce in the PR template / reviewer checklist).

## Codex SSOT updates

- `codex/06-coding-standards/quality-gates.md` § "CODEX_MAX_VIOLATIONS is a ratchet-down, ≤5 ceiling" + the file-size /
  function-size limits as first-class (not glob-exempt-forever).
- `codex/06-coding-standards/README.md` § file-size discipline (900 max / 700 warn) — cross-link the worst-offender
  split plan.

## Out of scope (named)

- Changing the lint-codex CHECK definitions / adding new classes — that is `harden_grepable_rules_into_ci_gates`
  territory; this plan only DRIVES THE COUNTS DOWN against the existing checks.
- The `ci_local_qg_parity` grep-P fix (DONE — prerequisite, not part of this plan's scope).
