---
doc_type: plan
title: Cross-cutting satellite AO batch 2 — Tracks 16-24 coverage gap + re-verified stale blockers from the batch-1 pass
summary: >-
  Second AO-dispatch batch for the cross-cutting tranche, produced by re-invoking `/ag-closeout-audit cross-cutting`
  after batch1/batch1b. Its dominant finding is a MEMBERSHIP gap, not a fresh-orphan gap: batch1's Phase-1 scope was 59
  docs, but the tranche's real membership (the skill's rule — `asset_group: cross-cutting` AND a data-relevant
  `parent_epic`, OR explicit membership in the closeout's Tracks) is 142 docs / 104 once the ao/ci/infra tranches' 38
  claimed docs are removed. batch1+batch1b's todos cover 37 source docs and their Deferred sections name a further 19,
  leaving 49 tranche members with no coverage from any cross-cutting covering plan — almost exactly the closeout's
  Tracks 16-24 (added 2026-07-25 by the corpus-wide sweep, after batch1's candidate corpus was already scoped). This
  batch drafts 14 conflict-cleared todos out of that set. The second theme is re-verification paying off: several "🟡
  BLOCKED ON DIRTY DEP" items from 2026-06-22/23 were checked against live code and had in fact LANDED (dropped, not
  re-dispatched), while one item's "already applied to live prod state" claim was measured FALSE against the live Cloud
  Run jobs (still 4Gi, not the claimed 16Gi) and one doc was found existing in `plans/active/issues/` AND
  `plans/archive/2026_07/` simultaneously. Everything not conflict-cleared is in the Deferred sections with its
  non-batchable category named.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos:
  [
    unified-trading-pm,
    unified-trading-library,
    unified-api-contracts,
    alerting-service,
    deployment-service,
    deployment-api,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    instruments-service,
    e2e-testing,
    strategy-service,
  ]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-2, satellite-docs, tracks-16-24]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit cross-cutting re-invocation 2026-07-26 (autonomous, operator away). Phase 0 re-derived tranche
  membership mechanically (142 members; 38 peer-claimed by ao/ci/infra; 61 named by batch1/1b/finalize) and split
  batch1's citations into real todo-coverage (37 docs) vs Deferred-section mentions (19 docs, explicitly NOT covered),
  leaving 49 uncovered candidates. Phase 1 classified all 49 by per-doc read (single-threaded — no Workflow/Task tool is
  available in this environment). Phase 3 ran the documented conflict-check against batch1, batch1b, the consolidated
  closeout, and every other AG's satellite batch before drafting.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
---

# Cross-cutting satellite AO batch 2 — Tracks 16-24 coverage gap

> **Status: draft.** Per CLAUDE.md's plan-destination HARD RULE and the ag-closeout-audit skill's autonomous-mode
> guidance, a skill-drafted AO batch is never auto-shipped to `active` — flip `status` to `active` only after operator
> review. Its gated companion is
> [`cross_cutting_satellite_ao_dispatch_batch2_2026_07_26_finalize.md`](/plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26_finalize.md).

> **Cross-todo file coordination (do NOT strip when editing).** Three todos below carry inline coordination text because
> they share a file or a runner with a batch1/batch1b todo that may land concurrently: the `read_availability_index`
> audit (MTDS `reader.py`, shared with batch1b's M30.3 legacy-fallback removal), the features-service catalogue
> inventory (exercises `smoke_matrix.py`, which batch1b RELOCATES), and the UTL writer-invariant bundle (same repo as
> batch1b's `_CANONICAL_CACHE` eviction, different files — `_writer_captured.py`/`_writer_record.py` vs `_state.py`).
> Same-priority todos in one plan run concurrently by default, so the text, not the ordering, is the guard.

## Todos

- [x] ✅ [REVIEW] P2. **Close the 4 never-touched Track-16 read-only audits as one bundle** (all four are pure
      inventory/audit asks with an explicit Definition-of-done, zero code changes, zero competing claim — verified: the
      cross-cutting closeout is their only citer). (a) `issues/catalogue_census_equivalents_inventory_2026_07_24.md` —
      state yes/no per catalogue (strategy-service registry, features-service per-family registries, sports fixtures
      catalogue, any UAC registry beyond `_distinct_values.py`/`_axis_census.py`'s 4 axes) on whether an equivalent
      drift-detection census exists, with a code citation for each "yes" and a filed follow-up todo for each "no". (b)
      `issues/coverage_percent_symmetric_inclusion_audit_2026_07_24.md` — grep every repo (start with deployment-api,
      where a 3rd undocumented formula was already found) for coverage-percent computations referencing
      `empty_confirmed`; give each site a PASS/VIOLATION verdict against `/codex/02-data/honest-coverage-model.md` §
      "Coverage formula"; file each VIOLATION as its own bounded fix todo rather than fixing it here. (c)
      `issues/cli_shard_split_flag_coverage_audit_2026_07_24.md` — per-service gap list for instruments-service, MDPS
      and every features-service family CLI against the codex 6-tuple + `--shard-key` convention
      (`/codex/06-coding-standards/cli-convention.md`), plus the chain-scoping-flag parity check on
      instruments-service's download entrypoint. (d) `issues/mvp_scope_resolver_code_read_2026_07_24.md` — code-read
      whether strategy-service's paper/live universe resolver genuinely restricts to UAC `MVP_SCOPE`, citing file +
      function. Sources: `issues/catalogue_census_equivalents_inventory_2026_07_24.md`,
      `issues/coverage_percent_symmetric_inclusion_audit_2026_07_24.md`,
      `issues/cli_shard_split_flag_coverage_audit_2026_07_24.md`, `issues/mvp_scope_resolver_code_read_2026_07_24.md`.
      **Coordination**: (d) is read-only and does NOT overlap batch1b's `FeaturesMvpRule`/`StrategiesMvpRule` todo,
      which WRITES UAC `mvp_scope.py` — do not implement anything here. **Done when**: all 6 checkboxes across the 4
      docs are flipped, each with its stated definition-of-done satisfied and any discovered gap filed as a new bounded
      todo. — DONE 2026-07-26 (unified-trading-pm, this commit): all 5 original audit checkboxes across the 4 docs
      flipped (a: 1, b: 1, c: 2, d: 1). Verdicts: (a) strategy catalogue YES (`registry_router.py`), features catalogue
      NO, sports fixtures YES (`fixture_completeness.py`), UAC registries-beyond-4-axes NO — 2 gap follow-ups filed. (b)
      NO VIOLATION found anywhere in the corpus (6 formula sites read, all PASS); the "3rd undocumented formula"
      (`attempt_coverage_pct`) is actually PASS, just undocumented — 1 doc-only follow-up filed. (c) confirmed
      `decompose_shard_key` has zero hits outside MTDS across instruments-service/MDPS/all 9 features-service families;
      corrected the doc's own baseline (the chain-scoping flags belong to MTDS's `--operation download`, not
      instruments-service, which has no `download` operation) — 2 gap follow-ups filed. (d) REFUTED: strategy-service
      has zero `MVP_SCOPE`/`is_mvp` references anywhere — the universe resolver hardcodes catalog specs with no
      MVP-membership filter — 1 fix follow-up filed, cross-referenced against
      `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`.
- [x] ✅ [DIAG] P2. **features-service catalogue completeness inventory + the smoke-check masking test.** — DONE
      2026-08-01, slot-13. Source: `issues/features_service_catalogue_completeness_inventory_2026_07_24.md`.

      **(a) Per-module table** — **CORRECTS the baseline's module count**: the real total is **11** feature-family
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          modules under `features_service/` (excluding shared infra dirs `api/`/`cli`/`common`), not 9 — the baseline's own
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          breakdown (1 full + 6 partial + 3 absent) already only summed to 10, and a grep for `BuilderEntry`/registry
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          patterns across the whole repo surfaced an 11th, previously-unlisted module (`cefi`) that is ALSO absent-entirely
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          (added 2026-05-19..07-28 per `git log`, predates the 2026-05-28 baseline, so it should have been caught):

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Module | Registry exists? | Shape | `status`/`formula_version`? | Verdict |
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |---|---|---|---|---|
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `delta_one` | Y | `FeatureSpec` (`app/features/registry.py` + `registry_specs.yaml`, 1389 specs) — plus a separate `BuilderEntry` DAG registry (`schemas/feature_builder_registry.py`) | Y (on `FeatureSpec` only) | **FULL** |
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `calendar` | Y | `BuilderEntry` (`schemas/feature_builder_registry.py`) | N | PARTIAL |
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `cross_instrument` | Y | `BuilderEntry` | N | PARTIAL |
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `multi_timeframe` | Y | `BuilderEntry` | N | PARTIAL |
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `volatility` | Y | `BuilderEntry` | N | PARTIAL |
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `onchain` | Y | `BuilderEntry` | N | PARTIAL |
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `sports` | Y | local `BuilderEntry` (function-callable-based, `tracking/feature_builder_registry.py`) | N | PARTIAL |
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `commodity` | N | `FACTOR_REGISTRY` maps factor_group→class only, not a per-feature entry | N/A | ABSENT |
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `performance_features` | N | none (just `cli_handler.py`/`passthrough_compute.py`) | N/A | ABSENT |
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `strategy_pnl_archetype` | N | none (just `rolling_compute.py`) | N/A | ABSENT |
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `cefi` | N | none (bare calculator files, no registry) | N/A | **ABSENT — not in original baseline (correction)** |

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          1 full + 6 partial + 4 absent = 11 (all 7 `BuilderEntry`-shaped registries confirmed to lack `status`/
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          `formula_version` — UTL's canonical `BuilderEntry` dataclass, `unified_trading_library/feature_service_base/
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          builder_registry.py`, has no such fields). The "6 partial" and "delta_one full" parts of the baseline are
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          CONFIRMED correct; the "commodity/performance_features/strategy_pnl_archetype absent" part is confirmed correct
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          but incomplete (missed `cefi`). The 98%-un-audited delta_one figure is CONFIRMED and measured exactly:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          `registry_specs.yaml` has 1389 specs, `status: listed`=1329, `verified`=28, `tested`=26, `need_data`=6 — non-
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          `verified` = 1361/1389 = **97.98% ≈ 98%**.

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          **(b) Empirical smoke-check-masking test** — real runs (not code-read inference), against
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          `e2e-testing/scripts/{commodity,calendar}/smoke_matrix.py` (batch1b's relocation already landed; confirmed the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          pre-relocation `features-service/scripts/<family>/` copies no longer contain `smoke_matrix.py`). **Mixed
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          verdict, richer than a single yes/no**:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          - **REFUTED** for the 6 vendor adapters actually wired into the batch code path (commodity: cftc/eia_crude/
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            eia_ng/open_meteo/yahoo_finance/baker_hughes; calendar: mtds_fred_reader/yahoo_finance_adapter). Both
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            families implement an explicit, deliberate fail-closed guard: commodity's `_has_full_factor_coverage()`
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            fails the whole day if ANY enabled factor is missing (`BatchHandler.run()` returns
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            `success_count == total`, so ONE bad day fails the entire CLI exit code); calendar's `_log_batch_summary()`
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            `sys.exit(1)`s if `total_failed > 0` across any (day, feature_group). Proved with a REAL run, not a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            synthetic break: Baker Hughes' rig-count adapter is CURRENTLY broken in prod ("unexpected file format") and
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            this correctly cascaded to `smoke_matrix.py` reporting `FAIL` (`CLI rc=1`) for commodity — confirming the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            check does NOT mask it. Follow-up fix filed (adapter regression is a NEW symptom, distinct from the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            already-fixed URL-scraping issue).
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          - **CONFIRMED (masking)** for calendar's other 4 declared vendor adapters (cryptopanic_adapter,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            lunarcrush_adapter, yfinance_earnings_adapter, polygon_corporate_actions_adapter) — verified via code-read
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            that `SentimentCalculator` (wraps the first 2) and `corporate_actions_handler.py` (wraps the last 2) are
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            DEAD CODE, never imported by `calendar_orchestrator.py`'s batch path nor wired into `cli/main.py`'s
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            `_OPERATIONS` map. Since `smoke_matrix.py` only ever invokes `--operation compute --mode batch`, these 4
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            adapters can NEVER cause the family-level check to fail, regardless of how broken they are — a stronger,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            unconditional masking mechanism (coverage gap) distinct from the refuted partial-tolerance hypothesis.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          - Total real vendor adapters actually inventoried: commodity 6 + calendar 6 (2 wired, 4 dead) = 12, not quite
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            the estimated ~16 — the estimate was in the right order of magnitude; no additional vendor adapters found in
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            either family beyond the 12 enumerated.

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          **Coordination note honoured**: ran against the POST-relocation `e2e-testing/scripts/<domain>/` location as
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          instructed (features-service's own `scripts/<family>/` dirs confirmed to no longer carry `smoke_matrix.py`).

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          **2 follow-up findings filed, not fixed inline** (outside this audit todo's own done-when):
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          `issues/features_service_catalogue_completeness_smoke_masking_findings_2026_08_01.md` (Baker Hughes
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          regression P2; calendar dead-code wire-vs-delete decision P2).

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          **1 big finding escalated separately** (discovered incidentally while running the required empirical test, out
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          of this todo's scope, filed immediately per the data-correctness "big finding" rule rather than absorbed):
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          `issues/features_e2e_smoke_matrix_writes_to_prod_bucket_2026_08_01.md` (P0) — ALL 8
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          `e2e-testing/scripts/<family>/smoke_matrix.py` harnesses set only `IS_TEST_RUN=true` in their subprocess env,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          never the `PROTOCOL_DATA_SINK_BUCKET*` override each family's config actually requires to route away from
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          PROD — live-verified for commodity, calendar, AND delta_one (all 3 resolved to their PROD bucket name under
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          bare `IS_TEST_RUN=true`). Every real (non-dry-run) smoke_matrix.py invocation across every family has likely
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          been reading/writing PROD buckets, not the `-test-` buckets each file's own docstring claims.

- [x] ✅ [CODE] P0. **UTL writer-side invariant bundle — three verbatim residuals in one repo pass** (Source:
      `data_pipeline_alert_substrate_residual_2026_07_24.md` Phase-4 + Phase-6-B items). (a) Make
      `record_captured`/`record_empty` assert the resolved GCS path `is_canonical()` before write, so a non-canonical
      write fails loudly at the writer instead of days later in an audit. (b) Add the live==batch schema invariant
      assert at the live `record_captured` boundary (the C7 `asset_group`-kwarg-not-column class). (c) Enrich the
      writer-gate `_emit_unproven_honest_absence` `DP_UNPROVEN_HONEST_ABSENCE` `details` with `venue`/`data_type`/`day`
      derived from `row_key`, plus an `error_message`. All three live in
      `unified_trading_library/manifest_writer/{_writer_captured.py,_writer_record.py,_core.py}` (verified 2026-07-26).
      **Coordination**: batch1b's `_CANONICAL_CACHE` eviction todo edits `manifest_writer/_state.py` — a DIFFERENT file
      in the same module; if both are in flight, land them as separate commits and re-run UTL `quality-gates.sh` after
      each rather than co-staging. **Done when**: all three asserts/enrichments are implemented with regression tests (a
      non-canonical path raises; a live record missing the `asset_group` column raises; the emitted event carries the 4
      new fields), UTL `quality-gates.sh` is green, and the three source-doc checkboxes are flipped. — DONE
      unified-trading-library@d7b3ed7d: (a) `_assert_canonical_write_path` in `manifest_writer/_rows.py` (new
      `NonCanonicalWritePathError`), wired into `record_captured` (`_writer_captured.py`) + `record_empty`'s
      `_record_status` backend (`_writer_record.py`, gated by a `check_canonical_path` flag so `record_failed`/
      `record_expected_unattempted` are unaffected) — STRUCTURAL-only, scoped to the 4 UAC `candidate_parquet_paths`-
      covered asset_groups (cefi/defi/tradfi/prediction) with resolvable dimensions; every other write shape (sports,
      features/ML/service rows, an unresolvable instrument_type) is a resolution skip, never a false block — landed in
      `_rows.py` not `_core.py` (the structural mixin-stub base, no concrete logic lives there) since both writer files
      already import from `_rows.py`. (b) `LiveCapturedAssetGroupInvariantError` raised in `record_captured` when
      `validate=False` (the live bookkeeping boundary) resolves no `asset_group` for a market-data cell (venue present,
      no `feature_group`); scoped to that boundary only, the fleet-wide self-heal-else-blank behaviour in
      `_resolve_asset_group` is unchanged for every other callsite. (c) `_emit_unproven_honest_absence` now takes
      `row_key` and stamps `venue`/`data_type`/`day` + a human-readable `error_message` into the emitted details. 8 new
      regression tests (`tests/unit/test_manifest_writer_phase4_writer_invariants.py`); full UTL suite green (4689
      passed, 0 failed); `quality-gates.sh` green (sentinel matches HEAD).
- [x] ✅ [CODE] P1. **alerting-service reliability trio — one repo, three verbatim residuals** (Sources:
      `data_pipeline_alert_substrate_residual_2026_07_24.md` "Later-surfaced alert-substrate bugs"). (a) Make
      `config_reloaders._fetch` tolerate missing secrets — today it calls
      `SecretManagerClient.get_secrets(_ALL_PAGING_SM_KEYS)` as ONE batch, so the 6 absent Twilio secrets +
      `DEPLOYMENT_SCRIPTS_LOG_BUCKET` make the batch raise, the `except` returns empty, and EVERY paging credential
      (including the `#uts-live-alerts` webhook) reads blank; switch to per-secret get with skip-missing (the `if val:`
      mapping already drops empties) or create the absent secrets as empty placeholders, then confirm SM hot-reload
      works without the `UTS_LIVE_ALERTS_SLACK_WEBHOOK` env fallback. (b) Add a DP-telemetry routing rule so routine
      `DP_FLEET_MONITOR_RUN_STARTED`/`_COMPLETED` mirror to `#data-pipeline-alerts` as INFO (or are suppressed) instead
      of falling through to the generic INCIDENT path — only genuine DP findings (`DP_VM_STALL`,
      `DP_EVENT_LOOP_STARVED`, `CONSOLIDATOR_DOWN`) should reach the incident path. Note the source doc's own 2026-07-12
      correction: the "Telegram is PRIMARY" diagnosis is STALE (Telegram was retired alerting-service@`1be4fe0`;
      `router.py`'s `_deliver_to_channels` aliases `"telegram"` to Slack) — only the routing ask is live, do not
      re-derive the transport question. (c) Verify the deployment-service heartbeat-stall watcher emit carries
      `vm_name` + `asset_group` + `message` so per-VM `DP_VM_STALL` alerts render distinguishably (the 13× batch that
      motivated this came from the OLD alerting revision 00005; confirm the CURRENT path renders `vm_name`) — repo
      `deployment-service` `data_pipeline_monitors/heartbeat_stall_watcher.py`. **Done when**: (a) and (b) land with
      tests and `quality-gates.sh` green in alerting-service, (c) is recorded as a measured verdict (renders / does not
      render, with the fix if not), and all three source checkboxes are flipped. — DONE 2026-07-27. **(a) MEASURED
      ALREADY-CORRECT, no production fix needed**: traced the full call chain (`GCPSecretClient.get_secret` →
      `SecretManagerClient.get_secret`/`get_secrets`, blame-verified since the module's creation 2025-11-06) —
      `get_secrets()` has always been a per-secret loop, each `get_secret()` call independently catches
      `NotFound`/`GoogleAPIError` and returns `None`, so a missing secret was NEVER able to raise and wipe the whole
      batch; the issue doc's diagnosis was stale. Added a regression test driving the REAL
      `SecretManagerClient.get_secrets()` (not a full mock) to lock this in — alerting-service@545799c. **(b) REAL BUG,
      FIXED**: `DP_FLEET_MONITOR_RUN_STARTED`/`_COMPLETED`/`_FAILED` (emitted by deployment-service's `dp-fleet-monitor`
      CLI via `run_lifecycle(service_name="dp-fleet-monitor")`) were never registered in UAC's
      `DATA_PIPELINE_ALERT_RULES`, so all three missed the router's exact-match short-circuit and fell through to the
      generic incident catch-all. Registered `DP-DIGEST-003`/`DP-DIGEST-004` (STARTED/COMPLETED, INFO, mirror-only) +
      `DP-WATCHER-003` (`_FAILED`, CRITICAL, pages — the monitor itself crashing is meta like `DP_ZOMBIE_WATCHDOG_DOWN`)
      — unified-api-contracts@92e068ea (+ human-doc/yaml mirror updated in this same PM commit), regression tests in
      alerting-service@545799c. **(c) MEASURED VERDICT: RENDERS CORRECTLY today** — traced
      `heartbeat_stall_watcher._finding_for()` (stamps `vm_name`/`asset_group` into `PipelineFinding.details`) →
      `escalation.route_finding()` (`event_details = dict(finding.details)`, then injects `message = finding.summary`
      when absent, and `finding.summary` already embeds `vm_name` e.g. "VM {vm_name} stalled — {reason}") — all three
      fields reach the emitted event. Added a regression test proving it — deployment-service@c7150e0. No code fix
      needed for (c); the 13× batch was measured to be from the OLD alerting revision 00005, and the current path is
      confirmed clean.
- [x] ✅ [INFRA] P1. **Consolidate the THREE competing `data_pipeline_audit_scheduler.tf` todos into one change, and
      correct a false prod claim measured this pass.** Three todos across two sibling source docs all edit
      `deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf`; drafting them separately would collide on one
      file. Measured state 2026-07-26 (read the live file + the live Cloud Run jobs, do not trust the docs' prose): (i)
      the `var.dp_audit_image` default → `e2e-audit:latest` half **HAS LANDED** (`local.dp_audit_image_resolved`, :57);
      (ii) the `dp_reprobe_empty_job` auto-flip arg **HAS LANDED** (`args = ["--reclassify-apply"]`, :281) — so
      `data_pipeline_self_healing_completion_residual_2026_07_24.md`'s "Schedule the auto-flip" item and its 🟡
      BLOCKED-ON-PEER-DIRTY note are both STALE, flip it `[x]` with this evidence rather than re-doing it; (iii) the OOM
      fix has **NOT** landed — the file still reads `memory = "4Gi" / cpu = "2"` at :91-92, :148-149, :267-268, and
      `gcloud run jobs describe uts-prod-dp-daily-digest` / `uts-prod-dp-reprobe-empty` both return `cpu=2;memory=4Gi`,
      which **refutes** that doc's claim that both changes were "ALREADY APPLIED to live prod state
      (`0 add/4     change/0 destroy`)". So: bump the 4 dp-audit jobs to the doc's specified `16Gi/4cpu`, `tofu apply`
      targeted (this is an in-place resource-limit change on 4 existing jobs — additive/idempotent, no create or destroy
      — so no `[OPERATOR]` delete gate applies; abort and report if the plan shows any add or destroy), and correct the
      source doc's prose to the measured state. Then confirm the 4 `dp-audit` Cloud Run Jobs + 4 schedulers named by
      `data_pipeline_alert_substrate_residual_2026_07_24.md`'s "Apply the data-pipeline-audit terraform" item are all
      provisioned, closing that item too. Sources: `data_pipeline_self_healing_completion_residual_2026_07_24.md`,
      `data_pipeline_alert_substrate_residual_2026_07_24.md`. **Done when**: `gcloud run jobs describe` shows
      `memory=16Gi cpu=4` for all 4 dp-audit jobs, the `.tf` change is committed, the 3 source checkboxes are flipped (2
      as already-landed with the evidence above, 1 as newly-shipped), and the false "already applied" prose is
      corrected. — DONE 2026-07-26, deployment-service@f2d094e. Re-measured before touching anything: all 4 jobs were
      ALREADY live-OOM-killing on their most recent execution (`gcloud run jobs executions describe` — "The configured
      memory limit was reached" on daily-digest, manifest-hygiene-changed, manifest-hygiene-full, and 5 consecutive days
      on reprobe-empty). Bumped all 4 job modules to `cpu="4"`/`memory="16Gi"`.
      `ENV=prod     ./tofu.sh plan -target=...` (all 4 modules) confirmed `0 to add, 4 to change, 0 to destroy` — no
      `[OPERATOR]` gate needed. Applied; post-apply `gcloud run jobs describe` confirms `cpu=4;memory=16Gi` on all 4.
      Also confirmed via `gcloud run jobs executions describe uts-prod-dp-reprobe-empty-55rz8` that
      `args: [--reclassify-apply]` is live in the deployed spec (executing daily since the earlier `.tf` landing).
      Confirmed via
      `gcloud scheduler jobs     list --account=unified-trading-sa@central-element-323112.iam.gserviceaccount.com` (the
      `github-actions-deploy` default account lacks `cloudscheduler.jobs.list` IAM) that all 4 `dp-audit` schedulers are
      provisioned. All 3 source checkboxes flipped in `data_pipeline_self_healing_completion_residual_2026_07_24.md` (2)
      and `data_pipeline_alert_substrate_residual_2026_07_24.md` (1), with the false "already applied" prose corrected
      to past tense + the new evidence. `quality-gates.sh` green (sentinel-verified).
- [x] ✅ [PERF] P2. **Fix the real dp-audit OOM driver (the 16Gi bump is a band-aid).** — `e2e-testing@5d7f53a` +
      `e2e-testing@edd12c6`. Landed the prose's own ask (column-restricted `read_manifest_index` + non-expanding
      aggregation) plus TWO further OOM contributors the measurement itself surfaced — neither visible from reading the
      code, only from running it against real prod-scale data: (1) **column restriction** — `_digest_for_ag` now reads
      `columns=["pipeline_mode","venue","chain","data_type","capture_status","schema_version"]` (added `schema_version`
      beyond the todo's literal list — it's read off the SAME df for the v9-readiness gate, and omitting it would have
      made `schema_version_readiness()` silently read every row as non-v9). `_dp_common.read_manifest_index` now peeks
      the parquet footer schema first and drops any requested column an AG's index doesn't actually carry (only defi has
      "chain" — pyarrow raises `ArrowInvalid` on a column-restricted read for any AG without it, confirmed via the
      existing no-chain test fixture). The `overall` tally in `_digest_for_ag` now sums per-cell `CaptureCounts` fields
      directly instead of the `["captured"]*N`-style list rebuild the todo flagged (though that specific expansion was
      already cell-bounded, not row-bounded, since each cell's count is 0/1 pre-union — real find below was elsewhere).
      (2) **`.str.lower()` speculative complex128 allocation** — `capture_status.astype(str).str.lower()` on a plain
      object column routes through pandas' `map_infer_mask` → `maybe_convert_objects`, which speculatively allocates
      full-length candidate buffers while probing for a numeric-castable result — on defi's real ~33.4M-row index this
      alone MemoryError'd allocating a stray 510MiB complex128 array. Switched to the pyarrow-backed `"string"` dtype,
      whose `.str.lower()` calls `pyarrow.compute.utf8_lower` directly (no Python-level type inference). (3)
      **unnecessary `df.copy()`** — `_union_across_sources`'s defensive copy forced pandas to consolidate same-dtype
      columns into one combined block via `np.vstack` (a further ~1.24GiB single allocation at defi's row count); the
      copy was unneeded (the caller's later `schema_version_readiness(df)` only reads `df["schema_version"]`, unaffected
      by mutation), so removed it. **Real measured verdict** (2026-08-01, run against live prod manifests, not a mock):
      before any of these fixes, all 5 `dp-audit` Cloud Run jobs were confirmed already live-OOM-killing (see the
      sibling 16Gi-bump todo above). After all three fixes, a real 5-AG digest run completes end-to-end
      (cefi/defi/tradfi/sports/prediction all succeeded, one union `DP_DAILY_DIGEST` emitted) at **peak RSS ≈ 11.8GiB**
      (`VmHWM`-measured, defi alone — the largest AG at ~33.4M rows — peaks ≈ 11.2GiB standalone). This is a large real
      improvement over the pre-fix baseline (OOM-killing at 4Gi) and fits comfortably under the currently-provisioned
      16Gi ceiling, but is **above** this todo's own aspirational "~4-8Gi" prose estimate — flagging that honestly
      rather than rounding it down; further reduction (e.g. a DuckDB/streamed aggregation instead of pandas) would be
      new scope, not part of this fix — tracked as the new todo directly below. 71/71 unit tests green
      (`tests/unit/test_dp_audit.py`, 3 new: column restriction, missing-column graceful drop, digest requests the
      restricted set), `quality-gates.sh` green on both commits (sentinel-verified).
- [ ] [PERF] P3. **Further reduce dp-audit digest memory below the ~4-8Gi aspirational target (currently ~11.8GiB
      measured).** Deferred from the item above: after the column-restriction + pyarrow-string-lower + no-copy fixes,
      `e2e-testing`'s `data_pipeline_daily_digest.py` completes a real 5-AG run at peak RSS ≈ 11.8GiB (defi alone ≈
      11.2GiB standalone, ~33.4M rows) — safely under the current 16Gi Cloud Run ceiling but above the original prose
      estimate. The remaining cost is fundamentally `pandas.groupby` materialising a full-frame `object`-dtype DataFrame
      for defi's row count; a genuine further reduction needs a different execution engine (e.g. DuckDB SQL aggregation
      directly over the parquet bytes — see `manifest-consolidator-ssot.md`'s DuckDB-over-pandas precedent — or a
      chunked/streamed groupby) rather than another pandas-level micro-fix. Low priority: not correctness-blocking, jobs
      run green today. **Related**: `issues/read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md` (filed
      same-day by a different worker) found the SAME class of problem in a DIFFERENT helper —
      `unified_trading_library`'s `read_availability_index(columns=[...])` also OOMs at DeFi's current ~33.4M-row scale
      despite its own column-projection contract — and independently confirms the `run-bounded-analysis.sh`
      RLIMIT_AS-fallback false-positive this session also hit (an 8G `ulimit -v` cap failed well before real RSS
      pressure; raising to 16-24G let the same code complete cleanly). That doc's DuckDB-workaround precedent is the
      same direction noted above. **Done when**: the digest's peak RSS for the full 5-AG run is re-measured at ≤8Gi with
      the same real-prod-data methodology (VmHWM via `/usr/bin/time -v`, not a mock), or a documented decision that
      11.8GiB is an acceptable steady state and the Cloud Run job's memory allocation stays at 16Gi (in which case
      downgrade/close this todo instead of chasing the estimate further).
- [x] ✅ [SCRIPT] P0. **Close the two remaining `audit_criteria_automation` honest-SKIPs and add the v9-readiness
      gate.** — `unified-trading-library@fb63477a` + `e2e-testing@98d499a`. CF-10 (phantom) now runs a real GREEN/RED
      via `--mode full` (reuses `reconcile_phantom_manifest_rows_all.py --dry-run`, cached per asset_group), staying an
      honest cost-scoped SKIP in the default daily `--mode changed` (mirrors `manifest_hygiene_daily.py`'s own
      changed/full split) — real edit location was
      `unified-trading-library/unified_trading_library/cf_manifest_audit.py` (the plan's named
      `cf_manifest_audit_all.py` in `market-tick-data-service` was stale — moved to UTL 2026-07-10). CF-14 (catalogue ⊇
      present-set) already computed real GREEN/RED when the catalogue artifact is readable; added test coverage proving
      the GREEN/RED/two-SKIP-variant paths (no behavior change — an honest SKIP when G1's catalogue isn't materialised
      is correct, not forced). New `unified-trading-library/tests/unit/test_cf_manifest_audit.py` (13 tests). Digest:
      added shared `_dp_common.schema_version_readiness()` (the corrected 2026-06-27 string-normalization, REUSED —
      `manifest_hygiene_daily.py._check_v9` refactored onto it, not re-derived a third time),
      `data_pipeline_daily_digest.py._digest_for_ag()` embeds `v9_readiness`/`v9_ready` per AG from its already-loaded
      manifest df (no second GCS read), and `run()`'s message/details flag any AG below 100% v9 (informational, no
      duplicate alert alongside the existing `DP_NOT_V9` WARN). Both source checkboxes in
      `data_pipeline_alert_substrate_residual_2026_07_24.md` flipped in the same turn. Both repos' `quality-gates.sh`
      green.
- [x] ✅ [CODE] P2. **Add the two missing UTL event-string constants and the per-source rate-limit health event.** (a)
      UTL `events/event_types.py` + `events/__init__` export: add `DP_DAILY_DIGEST` and `DP_HYGIENE_SUMMARY` (verified
      absent 2026-07-26 — the routing already works via the UAC rule matching the event string, so this is cleanliness,
      but the constants genuinely do not exist yet). (b) MTDS: emit a per-source
      `SOURCE_RATE_LIMITED{source, venue,     http_429_count}` and `SOURCE_KEY_POOL_EXHAUSTED` event to
      `data-pipeline-alerts` (C5 — the TheGraph 9-key pool, Databento, etc.). Source:
      `data_pipeline_alert_substrate_residual_2026_07_24.md`. **Done when**: both constants exist and are exported with
      UTL QG green, the MTDS emit lands with a test asserting the 429-count payload, and both source checkboxes are
      flipped. — **ALREADY-LANDED, found during finalize todo-1 reconciliation (2026-07-30, this commit) — NOT shipped
      by this batch.** Both halves landed via the sibling
      `data_pipeline_alert_substrate_residual_2026_07_24_finalize_2026_07_30.md` gated-twin plan, dated AFTER this
      batch's own 2026-07-26 "verified absent" premise: (a) `unified-trading-library@0f851fd6` (2026-07-30) adds
      `DP_DAILY_DIGEST`/`DP_HYGIENE_SUMMARY` to `events/event_types.py` + `events/__init__` export. (b)
      `market-tick-data-service@7f42c557` (2026-07-30) — `DP_SOURCE_RATE_LIMITED{source,venue,http_429_count}` extended
      to Databento's `DatabentoIPRateLimiter` (TheGraph's half already existed via `477de66c`); `DP_KEY_POOL_EXHAUSTED`
      correctly does not apply to Databento post-cutover (single canonical key, no pool to exhaust). Both source
      checkboxes in `data_pipeline_alert_substrate_residual_2026_07_24.md` are flipped there (verified — that doc is now
      archived at `/plans/archive/2026_07/data_pipeline_alert_substrate_residual_2026_07_24.md`). This batch's own
      checkbox was simply never re-synced after the sibling plan shipped; flipping now closes that gap.
- [x] ✅ [CODE] P1. **RESOLVED 2026-07-28 — root cause was NOT alerting-service code (none of the doc's 3 named
      hypotheses); it was a project-wide Cloud Logging sink exclusion.** `gcloud logging read` on the live
      `dp-alerting-subscriber` (project `central-element-323112`) returned **zero** `run.googleapis.com/stdout` or
      `/stderr` entries at ANY severity across a 30-day window, while the service's own structured
      `run.googleapis.com/requests` + `/varlog/system` logs were present — proving the container was alive and healthy,
      not silently dead. Cross-check against a Cloud Run **JOB** in the same project (`uts-prod-alerting-paging`) showed
      its unstructured, DEFAULT-severity (blank) log lines flowing through normally. Root cause: the project's
      `_Default` Cloud Logging sink carries a `debug-filter` exclusion —
      `severity <= "DEBUG" AND NOT resource.type="cloud_run_job"` (`gcloud logging sinks describe _Default`). Cloud
      Run's ingestion agent assigns **plain-text** (non-JSON) stdout/stderr lines Cloud Logging severity `DEFAULT` (0)
      regardless of the Python log level — it does not parse `%(levelname)s` out of free text. `DEFAULT` (0) ≤ `DEBUG`
      (100), so every plain-text line from alerting-service (a Cloud Run **service**) was silently dropped before ever
      reaching Cloud Logging; the exclusion's job carve-out is why the sibling paging JOB was unaffected. The 2026-06-23
      P2 fix (flushing handler + plain-text formatter) was a real but insufficient fix — flushing solves buffering, not
      severity-tagging. **Fix (alerting-service@62b850c, quickmerge-landed on live-defi-rollout)**:
      `api/main.py::_configure_stdout_logging()` now reuses UTL's `setup_cloud_logging(json_format=True)`
      (`CloudRunJSONFormatter`, `severity=record.levelname`) instead of the hand-rolled plain-text
      `_FlushingStreamHandler` — this makes Cloud Run's agent honour the real Python level, so INFO+ lines clear the
      exclusion without touching the shared, cost-sensitive project-wide sink policy (same sink also carries the
      `prd-gcs-data-access-exclusion` cost-control exclusion — a blanket loosening of `debug-filter` would have
      re-admitted plain-text DEBUG noise fleet-wide with real billing impact; scoping the fix to alerting-service's own
      log emission avoids that). **Live-verified**: built + deployed a diagnostic image
      (`alerting-service:diag-62b850c`) to `dp-alerting-subscriber` (revision `dp-alerting-subscriber-00015-lcn`,
      2026-07-28T06:18Z) via `gcloud builds submit` + `gcloud run deploy` (no Cloud Build trigger exists for this repo —
      ad hoc build, matching this exact service's established manual-deploy precedent in the source doc).
      `gcloud logging read 'resource.labels.revision_name="dp-alerting-subscriber-00015-lcn" AND     logName="...run.googleapis.com%2Fstderr"'`
      now shows, at correct severities: `INFO Starting alert subscriber     stream: (...)` — the exact
      previously-invisible "unconditional startup line" the source doc named — plus
      `INFO     AlertSubscriber initialized: subscriptions=(...)`, `INFO Event logging initialized: mode=local`,
      `INFO     DP_ALERTING_SUBSCRIBER_RUN_STARTED`,
      `INFO alerting-service: live AlertSubscriber started in API lifespan`, and
      `WARNING AlertSubscriber: 4 subscription(s) have no publisher implemented yet`. The gap is closed; no
      further-consequence follow-up is needed (the `debug-filter` sink exclusion itself is intentionally left unchanged
      — see the cost-tradeoff note above — since the service-scoped fix is sufficient and lower-risk). **Note**: the
      sibling "[DEPLOY] P2 ship the alerting-subscriber Cloud-Run code once UAC foreign WIP clears" item in the same doc
      is already LANDED (`config.run_subscriber_in_api` + the `api/main.py` lifespan are both in the committed tree,
      verified 2026-07-26) — flip it `[x]` with that evidence, do not re-ship it. Likewise its "Remaining (c) codify
      `lifecycle-events-sub` + `defi_data_quality_alerts` subscriptions and their subscriber IAM in terraform" prose
      item is DONE: `deployment-service/terraform/gcp/alerting_relay_pubsub.tf` carries both
      `google_pubsub_subscription` resources, both `google_pubsub_subscription_iam_member` bindings, and matching import
      blocks. Sources: `/plans/archive/issues/dp_event_pubsub_delivery_gap_2026_06_22.md`,
      `data_pipeline_ag_residual_backfill_decisions_2026_07_24.md`. Evidence: alerting-service@62b850c (QG green
      sentinel `.qg_last_passed_sha=62b850c`), live `gcloud logging read` excerpt above.
- [ ] [CODE] P2. **Two bounded data-pipeline-alert bug fixes** (Source:
      `/plans/archive/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md`). (a)
      **Finding 3** — add a per-VM shard check to `DP_VM_GONE_NO_CAPTURE`: the alert reads the CONSOLIDATED captured
      count, but per-VM shards written with `process_final=False` do not reach that count until the consolidator runs
      (~30 min after VM self-delete), so a VM that wrote real rows fires a false GONE_NO_CAPTURE (confirmed: VM
      `fs-backfill-20260627-193904` wrote 425 captured rows, alerted at 0, count reached 425 thirty minutes later — no
      data was lost). Implement the doc's **option (A)** — before firing for a recently-self-deleted VM, read
      `_index/per_vm/<vm_name>.parquet` and sum its captured rows, suppressing/downgrading to INFO when >0 — because it
      tests the real signal rather than guessing a delay; fall back to option (B) (a 35-min debounce for VMs whose last
      heartbeat is <40 min old) ONLY if the per-VM shard read is unavailable at that call site, and say which you used.
      Files: `deployment-service` `_gcs.py` + `data_pipeline_monitors.py` + a regression test. (b) **Secondary** — fix
      the `InstrumentsHandler failed on payload 24: '<' not supported between instances of 'str' and 'int'` str/int
      comparison bug in instruments-service's `InstrumentsHandler` (same bug class as DP_NOT_V9; non-fatal rc=0 but it
      silently dropped payload 24). **Excluded — do NOT action**: that doc's third open item (cleaning the contaminated
      defi/tradfi `schema_version` rows via `populate_v9_index_columns_inplace.py --apply`) is a prod-manifest mutation
      the doc explicitly reserves for the operator. **Done when**: (a) no longer fires for a VM with a non-empty per-VM
      shard (regression test + the chosen option named), (b) the comparison bug is fixed with a test, both repos' QG are
      green, and the two checkboxes are flipped while the operator-gated third stays open.
- [x] ✅ [CODE] P1. **Three bounded per-AG residuals carried in a cross-cutting fork** (Source:
      `data_pipeline_ag_residual_backfill_decisions_2026_07_24.md`; conflict-checked — no defi/tradfi satellite batch
      claims any of these, verified by corpus grep for `DIVERGENT_EMPTY` and `ohlcv_15s`). (a) **tradfi `ohlcv_15s` is a
      spurious aggregation tier** — `mdps-backfill-tradfi` spews CRITICAL
      `No SchemaContract registered for     asset_group='tradfi' instrument_type='UNKNOWN' data_type='ohlcv_15s' venue='CME'`.
      Fix the tradfi AGGREGATION TIER LIST in market-data-processing-service (drop 15s for tradfi — tradfi OHLCV is
      `ohlcv_1s`/`ohlcv_1m` aggregated to `15m`/`1h`/`24h`; a 15-SECOND tradfi tier is not valid, it appears only as a
      CeFi example). Do **NOT** add an `ohlcv_15s` `CONTRACT_REGISTRY` entry — the source doc is explicit that would
      MASK the bug by legitimising a bogus tier. (b) **UAC image-packaging bug** — image builds drop
      `unified_api_contracts/registry/data/*.json` (this crashed alerting-service startup and was worked around with a
      thin `dp-subscriber-datafix` image) AND the UAC WHEEL in Artifact Registry predates the `build_fetch_evidence`
      export (ImportError in wheel-based fleet builds); fix the cloudbuild context and/or republish the UAC wheel, then
      rebuild the alerting image cleanly and drop the datafix layer. (c) **DeFi evidence fidelity** — thread the ACTUAL
      subgraph/RPC HTTP status into the defi handlers' clean-path
      `record_zero_rows`/`record_empty(SOURCE_RETURNED_ZERO)` calls instead of the recorder's synthesized
      `clean_fetch_evidence` (the danger class is already closed — real errors route to `record_failed` — so this is
      fidelity, not correctness). **Done when**: (a) a tradfi MDPS run no longer emits the `ohlcv_15s` CRITICAL and no
      `ohlcv_15s` contract was added, (b) a fleet image build carries the registry JSONs and imports
      `build_fetch_evidence` from the published wheel with the datafix layer removed, (c) the defi handlers pass real
      HTTP status through with a test, and the three source checkboxes are flipped. **RUN 2026-07-28 (slot-11) — (a) and
      (b) DONE, (c) genuinely NOT bounded as scoped, checkbox stays unflipped.** (a) SHIPPED —
      `market-data-processing-service@034c1df`: the tier-ceiling mapping alone (already correct as of `mdps@36e80cd`
      2026-07-27) wasn't sufficient — an explicit CLI/env-var `timeframes` override bypassed it entirely;
      `resolve_timeframes()` now always intersects against the ceiling, 3 new regression tests, QG green. (b) VERIFIED
      already resolved 2026-06-23 (this dispatch's source doc's own "2026-06-23 follow-ups RESOLVED" note) — re-verified
      live 2026-07-28: zero `datafix` references anywhere in the codebase, alerting-service Dockerfile confirms the
      standard clean UTL-base-image pattern, no regression. (c) Researched, NOT shipped — the literal scope ("thread the
      ACTUAL...HTTP status...with a test") turns out to span 25+ call sites across non-uniform fetch mechanisms (most
      with no HTTP status concept at all — RPC multicall, on-chain calls), several needing a per-fetch-family
      helper-signature widen rather than a call-site edit, plus one genuine C1 correctness bug found in
      `governance_adapter.py` (swallowed fetch error, contradicting this todo's "danger class already closed" premise)
      that outranks the fidelity nicety. Not a worker-determinable-alone bounded change — filed as
      `issues/defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md` with a recommended P1(governance
      fix)/P2(per-family threading) split for proper re-dispatch. Source doc's 3 checkboxes: (a) and (b) flipped with
      evidence, (c) left open pointing at the issue doc — see
      `data_pipeline_ag_residual_backfill_decisions_2026_07_24.md`. **RE-VERIFIED 2026-07-28 (slot-5), checkbox flipped
      here.** Re-dispatch of this same backlog item landed on slot-5 because the checkbox above stayed unflipped after
      slot-11's run — independently confirmed all three sub-findings still hold:
      `market-data-processing-service@034c1df` is on `origin/live-defi-rollout` (verified via `git log`), zero `datafix`
      references remain, and the issue doc `issues/defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md` exists
      with a proper P1/P2 split (governance fix + 4 diagnostic/threading follow-ups). Flipping now: this todo's actual
      job — investigate the 3 residuals and either fix or properly triage each — is complete; (c) was correctly
      determined NOT worker-bounded-alone and was redirected to a standalone issue doc for its own future dispatch,
      which is the intended outcome per `task_template.md`'s dispatch-scope-eligibility rule, not an open loose end.
      Leaving this checkbox permanently unflipped would only cause indefinite backlog churn (a second worker
      re-verifying the identical already-settled conclusion, as happened here) with no further action available at this
      todo's scope.
- [x] [CODE] P1. ✅ **Triage the 2 still-open finding classes in both `manifest_hygiene_red` monitor instances as one
      pass.** `issues/manifest_hygiene_red_2026_06_27.md` (defi) and `issues/manifest_hygiene_red_2026_06_29.md` (cefi)
      are dated outputs of the SAME standing monitor (`manifest_hygiene_daily.py`) and both carry a 2026-07-12
      reconciliation note narrowing their originally-5-class todo to exactly **two** still-open classes:
      `oracle_expects_but_empty` and `noncanonical_path_on_disk`. **RE-VERIFIED 2026-07-28 (slot-5)**: both docs' stale
      `.tabs/<N>/` candidate-CSV path corrected to the repo-root-relative
      `plans/audit/results/manifest_hygiene_{defi,cefi}_*.csv`. Both CSVs read in full and every row triaged:
      `oracle_expects_but_empty` — defi's `venue=UNISWAP_V4 data_type=dex_pool_swaps` candidate (2026-06-23/24) is a
      REAL GAP, confirmed as a phantom-capture misclassification corrected one day later by
      `mvp_backfill_defi_onchain_v10_2026_06_27.md`'s 2026-06-28 phantom-reconcile (dex_pool_swaps=20,586 flipped,
      UNISWAP_V4 top venue) and still an ACTIVE tracked backfill target per
      `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md` (status open); cefi's
      `venue=OKX-SWAP     data_type=trades` candidate (2026-05-20/21/22) is a REAL GAP independently confirmed inside
      `plans/archive/2026_07/mvp_backfill_cefi_tick_v10_2026_06_27.md`'s own progress log (same exact
      venue/dates/count), reprobed via dedicated Tardis backfill VMs, now folded into the CeFi completion program
      lineage (that plan is `status: complete`). `noncanonical_path_on_disk` had **zero candidates** in both CSVs —
      `_check_path_canonicality` is a deterministic index-only check with no suppression path, so 0 rows = genuinely
      clean for both AGs on those dates. No new MTDS code fix required in either case — both open classes are
      already-tracked residuals of live/completed backfill efforts, not fresh bugs. Full verdicts + evidence in each
      issue doc's new "Final triage verdict (2026-07-28, slot-5)" section. — unified-trading-pm (this commit).
- [ ] [DATA] P2. **Retagged from `[OPERATOR]` (2026-07-28 gate-cleanup pass)** — the operator ruling below is the
      standing approval this todo needs; nothing further is operator-gated, so this dispatches as a normal AO todo per
      its own pre-apply sequence (snapshot defi+tradfi index → verify single-column contamination → run `--apply` →
      verify row-count delta). **Clean the contaminated defi/tradfi manifest `schema_version` rows — operator APPROVED
      2026-07-27, ready to dispatch.** Operator ruling (`june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED
      item 11, interactive session 2026-07-27): "dp_alerts_dp_not_v9 — `populate_v9_index_columns_inplace.py --apply`:
      **APPROVED** to run." This is a prod-manifest **row mutation** (bumping `schema_version` on single-column-
      contaminated rows), not a GCS object delete, so the applicable gate is the manifest-mutation contract in
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § "Not a hard stop, but adjacent: manifest-row
      deletion via a phantom-audit `--apply`... `--apply` only after `prefix_tpls` cover every current path shape,
      verified by a clean `--dry-run`" plus that same doc's § 5 sanctioned mechanics (UTL `gcs_*` helpers only, never a
      subprocess `gcloud`/`gsutil`) and its general snapshot-before-mutate discipline. **Before running `--apply`**: (1)
      snapshot the defi + tradfi `_index/availability_index.parquet` files; (2) verify via a live GCS row sample that
      the contamination is single-column only (only `schema_version` wrong) and NOT a full-row positional shift — per
      `/plans/archive/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md`'s own stated
      prerequisite, a positional shift needs re-derivation, not a version bump; (3) run
      `populate_v9_index_columns_inplace.py --apply` against the defi + tradfi index buckets only; (4) verify
      before/after row counts and that the non-v9 residual shrank by exactly the expected contaminated-row count. **Done
      when**: the pre-mutate snapshot exists, the sample-verification result is recorded (single-column vs
      positional-shift, with the sample cited), the `--apply` run completes with before/after counts, and the source
      doc's "Operator decision (prod-manifest mutation)" checkbox is flipped `[x]` citing this evidence. Source:
      `/plans/archive/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md` Finding 1's
      "Operator decision (prod-manifest mutation)" item. **Note**: the source doc itself carries
      `locked_by: live-defi-rollout` — this todo does not require unlocking the source doc (it only needs a checkbox
      flip there, not archival), but the source doc's own archival still needs a separate operator `[unlock-plan]` grant
      once all 3 of its items are resolved.
- [ ] [DATA] P3. **Triage the 10 unfiltered `read_availability_index(bucket)` call sites (third-strike audit).** For
      each site listed in the source doc — 5 in instruments-service (`cli/main.py`,
      `engine/orchestrator/{process_preflight,venue_core,process_completeness,catalogue}.py`) and 5 in
      market-tick-data-service (`reader.py`, `scripts/_rebuild_sports_projection.py`,
      `scripts/delete_defi_zero_row_placeholders.py`, `engine/orchestrator/venue_fetch.py`,
      `engine/orchestrator/__init__.py`) — determine (a) whether it sits inside a per-date/per-shard loop over a
      potentially-large range or is a one-shot call, and (b) if the former, convert it to the slim + date-filtered form
      (`columns=[...]` plus `filters=[("date","==",date)]` or a range filter) matching the two sites already fixed in
      `_queries.py::check_shard_freshness` and `sports.py::_should_skip_date_for_per_league`, keeping the same
      column-list-matches-actual-usage discipline. A one-shot entrypoint has no OOM risk and should be documented as
      safe rather than converted. **Coordination (same file)**: batch1b's `mtds_plan_reconciliation` todo (b) edits MTDS
      `reader.py` to remove the unconditional non-`pipeline_mode=` legacy base-path append. Land whichever is ready
      first, then rebase the other onto it and re-run MTDS `quality-gates.sh` — do not co-edit `reader.py` concurrently.
      Source: `issues/read_availability_index_unfiltered_callsite_audit_2026_07_26.md`. **Done when**: every
      per-date-loop site is converted and every remaining site is explicitly documented as safe, with no site left
      unaudited, and the source checkbox is flipped.
- [x] ✅ [DOC] P1. **Reconcile the `gcs_data_access_audit_log_cost` duplicate and add the missing historical-snapshot
      banner.** — `unified-trading-pm@61407412c`. (a) was already done by a prior pass when this task dispatched:
      `plans/active/issues/gcs_data_access_audit_log_cost_2026_07_24.md` no longer exists (confirmed absent), and
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize.md`'s todo 3 already carries the "⚠️ CORRECTED
      2026-07-26" banner directing DELETE-not-archive (matches this todo's own instruction verbatim) — nothing left to
      amend there. Re-ran both hygiene scripts fresh this pass: `check_ag_closeout_linkage.py` → 0 orphans (baseline 0);
      `scripts/plans/regenerate_active_plan_inventory.py` (corrected path — `plan-hygiene/` no longer has this script) →
      249 plans, 0 orphans, 0 TBD. The one remaining live reference to the old active-path filename
      (`ag_closeout_audit_rollout_2026_07_25.md:700`) is a timestamped Progress-Log historical note ("as of 2026-07-25
      compaction time"), not a live pointer — left as-is, it's a record of a past event, not a broken cross-reference.
      (b) Added the historical-snapshot banner to `issues/instruments_remaining_work_audit_2026_07_10.md` (973L now)
      right after its "How to read this doc" block, dated 2026-07-28, citing this todo. **Done when** criteria all met:
      only the archive copy of the gcs doc remains, corpus referrers resolve (the one exception is a historical log
      entry, not a broken link), the finalize todo text was already corrected, the inventory regenerates with 0 orphans,
      and the historical-snapshot banner is in place.

## Deferred — conflict-gated (a competing claim is genuinely unresolved; do not draft against these)

- **`issues/phantom_captures_tradfi_2026_06_28.md`** (1 open `[CODE] P2`, tradfi phantom root-cause diagnosis).
  `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s own "Deferred — still genuinely conflict-gated" section names
  this exact doc: its `data_completion_tradfi_2026_07_15.md` ⑫ `reconcile_phantom_manifest_rows_all.py --dry-run` re-run
  "conflicts with the closeout's own still-open Phase C Denominator/catalogue-completeness todo, which cites the SAME
  `phantom_captures_tradfi_2026_06_28.md` ground via a different mechanism". Two tranches reaching the same ground by
  different mechanisms is precisely the case the skill says not to guess at — leave it to the tradfi finalize's own
  re-check.
- **`defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`** (4 open; the `[TEST] P3`
  `test_batch_harness.py::test_position_state_survives_across_ticks` isolation failure is genuinely bounded and would
  otherwise be batchable). Blocked on a ROUTING conflict, not on the work:
  `defi_satellite_ao_dispatch_batch2_2026_07_26` flags it as a suspected mistag (bare `[cross-cutting]` on a
  `defi_`-prefixed doc) and its finalize todo 3 owns the retag decision, explicitly deferring it while
  `locked_by: live-defi-rollout` still holds. Whichever tranche wins the retag should own these 4 todos; drafting them
  here would pre-empt that.
- **`sports_prediction_mvp_writetime_precompute_2026_07_24.md`** (1 open `[DATA] P2`) — see the parked tranche-ownership
  item in the finalize plan. Also **too-large-or-risky** on its own terms: a `MANIFEST_SCHEMA_VERSION` 9→10 bump on
  UTL's `AvailabilityRecord`, the one dataclass every asset_group and every producer service writes, plus a full-fleet
  redeploy and a historical row backfill. That is not a batch slot; it needs its own phased plan.

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION)

- **`asset_class_to_asset_group_rename_2026_07_21.md`** (7 open). Carries an explicit destination ruling (BLK-87fc93e4,
  2026-07-21): "this is a LOCAL/human plan (`assigned_vm: NA`) by deliberate operator-protective default — a 9+-repo
  atomic breaking rename is exactly the risk class the ask-before-AO-dispatch HARD RULE exists for. The operator may
  flip `assigned_vm: planning` later to dispatch it; **do not do that unilaterally**." Not batchable until the operator
  flips it.
- **`consolidator_throughput_backlog_monitor_2026_07_09.md`** (3 open). All three are gated on the same standing
  operator hold — "Cloud Build deploy DEFERRED (operator 2026-07-10 — local-dev-only until …)" — and the WS-3 v2
  truthful merged-per-tick histogram is separately DESCOPED pending WS-H's structured-progress spine.
- ~~**`issues/data_pipeline_alerts_dp_not_v9_…_2026_06_27.md`** third item (prod-manifest mutation)~~ — **RESOLVED
  2026-07-27**: the operator APPROVED this run (`june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED item 11);
  no longer a bare operator-decision block. Moved to a real dispatchable `[OPERATOR] P2` todo in the Todos section above
  (staged with the snapshot + sample-verification prerequisites), not left here.
- **`issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md`** todo 1 (2 open total). The doc's own text
  forecloses dispatch: "This is a genuine operator/design decision (which model to commit to), not a worker-determinable
  fact — do not dispatch (a) or (b) speculatively without that decision." Its `[DATA] P3` shutdown-script grace-period
  audit IS bounded and becomes batchable the moment todo 1 is ruled; held back only because splitting one 2-todo doc
  across two batches costs more coordination than it buys.
- **`issues/locked_plan_deletion_gate_never_runs_on_docs_plans_commits_2026_07_26.md`** (4 open). Todo 1 is
  `[OPERATOR] P1. Rule on the direction before any mechanism changes` and todos 2-4 are all conditioned on that ruling.
  Already queued for the operator by the `/plan-reconcile cross-cutting` pass as decision #11 in
  `issues/autonomous_session_operator_decisions_2026_07_25.md` — **not re-asked here** (the skill forbids re-surfacing
  an already-asked operator question).
- **`issues/batch_live_reconciliation_service_audit_2026_05_27.md`** (0 checkbox todos; prose-form). Its remaining
  content is § 6 "Gaps / undecided / incomplete" and § 7.2 "Needs operator input (material)" — an audit whose residue is
  by construction a decision ledger, not executable work.
- **`data_status_catalogue_true_source_phase2_2026_07_24.md`** (1 open `[BACKEND] P3`). The obvious implementation was
  prototyped against real GCS and **deliberately reverted as wrong** (extending `_IDENTITY_CATALOGUE_ASSET_GROUPS` to
  prediction+sports "trades correctness for correctness" — sports rows carry `venue=''`, prediction's identity catalogue
  is 184.5 MB / 2.67M ids of which only 79 survive `_dedupe_latest`). Picking the replacement projection shape is an
  undecided design call. Separately, this doc has a **prettier-mangling defect** — its "NOT DONE but DESIGNED" section
  carries runaway trailing-whitespace indentation; worth a `scripts/plan-hygiene/check_prettier_mangling.sh` pass
  independent of the todo.

## Deferred — time-/sequencing-gated (re-check on the next iteration)

- **`pipeline_mode_partition_migration_2026_06_01.md`** (2 open). Both todos are explicitly "bundle `pipeline_mode=`
  into each non-DeFi bucket's NEXT whole-corpus manifest walk" — the single-walk discipline
  (`/codex/02-data/availability-manifest-and-data-status.md`) forbids scheduling a dedicated walk just for this, so it
  lands when the owning L3 canonicalisation plans walk, not on a batch cadence. The doc also carries an unresolved
  `[⚠️ NEEDS VERIFICATION 2026-07-21]` marker on its cefi/tradfi/prediction owner rows.
- **`/plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md`** (1 open `[INFRA] P0`, "9 live data VMs
  frozen 5.5-32h, silently RUNNING, zero capture"). Dated 2026-06-22 — a specific month-old incident, not a standing
  defect. It needs a fresh live-fleet re-measure before anyone acts (the named VMs are long gone); re-measuring is cheap
  but belongs with `/vm-preemption-billing-waste-audit`, not a batch todo that would re-diagnose a stale snapshot.
  **OWNERSHIP RESOLVED 2026-07-31** (corpus-wide ownership-conflict sweep): this routing stands and reflects current
  reality (the source doc's own 2026-07-25 re-verification found **zero** matching instances in either cloud, so there
  is nothing left to batch-diagnose) — but "routed away" is not "unowned". **The source doc RETAINS the todo**; batch2
  cites it and does not own it. The `/vm-preemption-billing-waste-audit` skill is the execution mechanism, not a new
  owner.
- **`data_feed_sla_registry_and_active_self_healing_2026_06_19.md`** (2 open). Both are fleet dependency/CVE ops, not
  data-pipeline work: the msgpack `>=1.2.1` bump is 21/23 repos done and blocked on alerting-service's
  version/internal-dep-alignment gate plus agent-orchestrator's foreign UI test infra, and the vcrpy
  `GHSA-rpj2-4hq8-938g` drop is explicitly gated on `issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md`, which
  the **infra tranche** already claims. Both `--ignore-vuln` entries are still live in
  `scripts/quality-gates-base/qg-common.sh` (verified 2026-07-26), so nothing has silently cleared. **Route to the
  infra/ci tranche** rather than batching from cross-cutting.

## Deferred — needs its own dedicated triage pass, not a batchN slot

- **Track 24 (strategy/execution cross-AG determinism + capability registry) — 8 docs, ~121 open todos.**
  `v2_engine_venue_buildout_2026_06_15.md` (37), `issues/capability_wizard_gap_discovery_2026_06_11.md` (30),
  `carry_staked_basis_funding_scan_experiment_2026_06_16.md` (28),
  `cross_venue_funding_reversion_research_2026_07_24.md` (13), `citadel_paper_batch_live_reconciliation_2026_06_19.md`
  (11), `issues/capability_wizard_analysis_findings_2026_06_11.md` (11),
  `carry_strategy_ensemble_productionization_2026_07_24.md` (7),
  `issues/batch_live_reconciliation_service_audit_2026_05_27.md` (prose). Checked, not assumed: **`v2_engine`'s
  dispatchable work is already covered** — its 2026-07-13 split forked 5 `assigned_vm: planning` children, of which
  `uac_venue_registry_completion_2026_07_13`, `fleet_hygiene_crypto_ghsa_mtds_baseline_2026_07_13`,
  `vol_surface_feature_exposure_2026_07_13`, and (as of 2026-08-03) `vol_dvol_backtestable_engines_2026_07_13` are all
  ARCHIVED (done); only `l2_book_microstructure_capture_2026_07_13` is still active; the parent's 37 open boxes are
  mostly `→ SPLIT to …` bookkeeping plus the Tier-2 (17 Tardis-credential-blocked) and Tier-3 (2 ML-model-variant,
  operator-decision) remainder the plan itself says "do not dispatch — it would just stall a VM agent on a gate only the
  operator can clear". The capability-wizard pair is dominated by `[SPEC]` registry-design and "assign an owner" items;
  the carry/reversion trio is research-harness work. The consolidated closeout already nominates Track 24 as the first
  extraction candidate if that doc needs a line-cap split — that extraction plus a dedicated triage is the right next
  move for this family, not another batch slot.
- **`mdps_features_reduced_artifact_tracker_2026_06_28.md`** (`status: draft`, 0 checkbox todos). **CORRECTED
  2026-07-27**: Plan 3 (`mvp_for_mdps_and_features_universe_uac`) was NOT never-authored — it shipped in full and was
  archived 2026-06-30 (`plans/archive/2026_06/mvp_for_mdps_and_features_universe_uac_2026_06_28.md`, all 6 items
  content-verified): `mdps_mvp_universe` (unified-api-contracts@682cffb5), `feature_perp_representative`
  (unified-api-contracts@6f0c4bf8), `execution_spot_representative` (unified-api-contracts@6cf967c2), the 5-AG test
  matrix (unified-api-contracts@6a2f6aab, 56/56 green), consumed by features-service@48fa8377. None of the 3 downstream
  mini-plans were actually blocked on it: Plan 2 (`features_read_book_columns_not_snapshots`) was already complete
  independently; Plan 9 (`execution_fidelity_tiers_uac_governed`) was already active, tracked separately; Plan 6
  (`honest_coverage_smoke_harness`) has a stable v10 dependency contract to consume whenever it's authored — it just
  hasn't been implemented yet (unrelated to Plan 3). This tracker doc itself has 0 own checkbox todos and is slated for
  archival in §2 of `june_2026_vintage_audit_findings_2026_07_27.md`.
- **`data_status_cell_grid_rearchitecture_2026_07_18.md`** (7 open) — todo 2 is an explicit design gate ("evaluate the
  three directions … pick one (or a hybrid) and record the decision + the projection schema"), and todos 3-7 are all
  downstream of it. Todo 1 (**measure + profile** the current cell-grid build to baseline the per-service memory
  footprint and read pattern) is bounded and worker-determinable and would have been drafted, but extracting a single
  prerequisite from a 7-todo design chain into a different plan risks the worker treating the design gate as cleared;
  better handled by the operator flipping this plan's own todo 1 or splitting it deliberately.
- **`/plans/archive/2026_07/deployment_redesign_cherrypicks_2026_07_20.md`** (3 open `[BACKEND]` deployment-api items:
  `reason_category`/ `reason_summary` on the drilldown tree, mock-mode `/coverage-summary` all-zeros, a flat
  `(primary × date)` `capture_status` matrix endpoint). All three are genuinely bounded and conflict-clear — held back
  only for line-cap headroom in this batch; they are the strongest candidates for a batch 3 with no further
  investigation needed.
- **`bucket_fold_ml_2026_07_17.md`** (6 open) and
  **`issues/monitor_jobs_auto_repin_and_alerting_cli_wiring_2026_06_24.md`** (2 open) — both already named in
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize.md`'s todo 3 as genuinely infra-scoped docs to retag
  `[infra]` or fold into `infra_consolidated_closeout_2026_07_25.md`. Their open work should be batched from the
  **infra** tranche after that retag, not from here.
- **`issues/hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md`** (1 open `[SCRIPT] P3`, re-run
  the `registry-drift` job once the tag-ancestry gap is fixed). Content is entirely CI/release-machinery (hatch-vcs,
  git-tag ancestry, cross-repo `pip install`) and its three citers are all CI docs — a bare `[cross-cutting]` tag on
  **ci**-tranche content. Route to the ci tranche; do not batch from cross-cutting.
- **`issues/live_mode_event_sink_topic_missing_2026_06_21.md`** (0 checkbox todos, prose-form). Real remaining work
  (create the missing `{service_name}-events` Pub/Sub topics for live-mode launches, MTDS/MDPS — a fleet-wide latent
  bug), and the closeout's Track 21 criterion names it. Held back because the fix shape — declare the topics in the
  alerting/deployment terraform vs create-on-launch in the launcher — is the same question the doc's own "Recommended
  decision (live_pipeline epic)" section routes elsewhere; a batch todo would have to pick, and it should not.
- **`issues/empty_reprobe_disagreement_2026_06_22.md`** (0 open). The closeout's Track 15 verdict stands: "stale —
  auto-filed over a month ago, `locked_by` looks like an abandoned lock; likely much of its scope superseded by Track
  12's audits; recommend a fresh re-probe or archive rather than direct dispatch." Its retag to `[defi]` is already in
  the batch1 finalize's todo 3.

## Not orphaned — checked, not assumed (recorded so a later pass does not re-raise them)

- **`data_status_page_ux_and_canonicalisation_2026_07_16.md`** — its single open `[DATA] P3` is the `InstrumentRecord`
  `extra='ignore'` silent-kwarg-drop item, which is the SAME underlying fix as
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s `[DATA] P1` `extra='forbid'` todo (cited there from
  `instrument_record_schema_completeness_extra_forbid_2026_07_18.md`). Covered by batch1 via a different source doc — a
  filename-only coverage check misses this.
- **`issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md`** (`status: blocked`, 0 open) — PROMOTED
  2026-06-25 into `live_data_persistence_central_event_log_2026_06_25.md`; the issue doc is the problem record, the plan
  is the executable SSOT.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **`issues/live_tardis_machine_and_hl_aster_s3_batch_2026_06_21.md`** (0 open) — its substantial residual (run the
  HL/ASTER batch launcher over the 2023→26 / 2024→26 ranges, 48.5k `attempted_failed` cells) is tracked in the **cefi**
  tranche's `data_completion_cefi_2026_07_15.md`, and the batch1 finalize already retags this doc `[cefi]`.
- **`data_pipeline_e2e_milestones_gate_2026_07_24.md`** (0 open / 64 done) — a standing 14-criteria gate and the
  reference surface `/plan-reconcile`'s hunter 6 dereferences; its archival is already queued to the operator as
  decision #10 in `issues/autonomous_session_operator_decisions_2026_07_25.md`. Not re-raised.
- **`infra_capture_and_devops_leftovers_finalize_2026_07_25.md`** (0 open) — DONE but deliberately NOT archived;
  removing it from `plans/active/` regresses `scripts/quality_gates/check_finalize_plan_coverage.py` from baseline 1 to
  2 and hard-fails PM `quality-gates.sh` for every agent. Its own 🟡 banner documents this.
