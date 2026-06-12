---
title:
  "Migration verification & orphan-safety — the 'migrate once, never need a v10' harness (canonical possible-manifest
  registry + bidirectional orphan sweep + schema-attribute completeness + catalogue-seeded denominator + candle-edge +
  verified-delete + projected-manifest preview), folded into re-runnable CF-15…CF-21"
created: 2026-06-10
parent_epic: manifest_master
assigned_vm: vm-cross-cutting
status: active
priority: P0
estimate_class: design
estimate_baseline_ai_days: 11
estimate_calibrated_ai_days: 6.6
locked_by: live-defi-rollout
locked_since: 2026-06-10
source:
  - operator 2026-06-10 ("worried about GCS orphans after migration; prove everything migrated; projected v9 manifest we
    can hook data-status/deployment-UI to in dev to see the goalposts; delete only what's in the manifest; know the data
    size; migrate once — no v10 because we missed an attribute or a whole shard-dynamic")
  - operator 2026-06-10 ("registry of all possible shard dynamics per AG = consolidation of the possible manifest; run
    manifest where we only have instruments → seed denominator as expected_unattempted; candle left/right edge from
    external sources; everything new must be augmented into the re-runnable audit instructions; non-data GCS paths (vm
    logs) understood not deleted")
  - audit: plans/audit/results/migration_orphan_safety_goalpost_verification_2026_06_10.md (the full design + decisions)
codex_ssots:
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/pipeline-mode-partition.md
  - codex/02-data/bar-boundary-candle-edge-convention.md
  - plans/audit/instructions/canonical_form_cross_service_audit_checklist.md
---

# Migration verification & orphan-safety — the "migrate once" harness

> **Role**: this is the **G3.5 pre-apply verification gate** of
> `master_data_canonicalisation_migration_catalogue_2026_06_07.md` — it sits between **G3** (UNION view) and **G4**
> (`--apply`). The master coordinator's **①–⑫ pre-apply audit** already proves read/write paths (⑤), batch=live (⑪),
> 4-state honesty (③④), rollback (⑫). This plan adds the **provable-completeness + preview + safe-cleanup + durability**
> layer the operator's "no v10" concern exposes: points **⑬–⑲ + G4.5**, folded into re-runnable **CF-15…CF-21**.
>
> **Decisions baked in (operator 2026-06-10)**: ⑬–⑲ **ALL HARD-BLOCK** G4 `--apply`; execution config = a
> capability/compatibility pre-flight (audit-and-enhance, post-G4); config change ≠ code bump (config_version,
> per-config).
>
> **Gating & ownership** (foundation-completion-gate: the cross-cutting layer is GREEN before the per-AG layer):
>
> | Layer                                                                | Owner                                        | AGs                  |
> | -------------------------------------------------------------------- | -------------------------------------------- | -------------------- |
> | **Cross-cutting scaffolds** (V0 registry + all tooling + durability) | **slot-3 / vm-cross-cutting**                | —                    |
> | **Per-AG runs: CeFi + Prediction** (the two STUB enumerators)        | **slot-3 / vm-cefi + vm-prediction**         | cefi, prediction     |
> | **Per-AG runs: DeFi + TradFi + Sports** (FULL enumerators)           | **slot-2 / vm-defi + vm-tradfi + vm-sports** | defi, tradfi, sports |
>
> slot-2's per-AG runs are **BLOCKED-UNTIL** slot-3's V0 + tool scaffolds are GREEN (they consume them). This matches
> the account topology (`orchestrator_vm_registry.yaml`: iggy2london→cefi/prediction/cross-cutting;
> ikenna→defi/sports/tradfi).

## Phased execution DAG (gated)

```
V0  Canonical possible-manifest registry (CF-15)         ─┐ slot-3 · BLOCKS all per-AG
V1  Catalogue-seeded enumerator (CF-16)                   ─┤ slot-3 cefi/pred (complete STUBs) ∥ slot-2 defi/tradfi/sports (verify FULL)
V2  Orphan sweep + bucket prefix taxonomy + sizing (CF-17)─┤ slot-3 builds tool → both run per-AG (single GCS walk w/ V3+sizing)
V3  Schema-attribute completeness (CF-18)                 ─┤ slot-3 builds framework → both run per-AG (rides V2 walk)
V4  Candle edge-timestamp audit (CF-19)                   ─┤ per-AG owner of each external OHLCV source
V5  Projected-manifest preview + data-status render (CF-20)┘ slot-3 builds harness → both render per-AG in dev
        ↓ (⑬–⑲ GREEN per AG)
V6  Per-AG pre-apply verdict → [G4 --apply, operator] → G4.5 verified-delete cleanup (CF-21)
V7  Durability — encode CF-15…CF-21 into the checklist + per-service instruction files (slot-3, cross-cutting)
B   MVP Phase 2-3 + config_version + execution-config compatibility pre-flight (lower priority; references existing plans)
```

## V0 — Canonical possible-manifest registry (CF-15) — slot-3, BLOCKS all per-AG

- [x] ✅ [UAC] P0. Build `unified_api_contracts/registry/possible_manifest.py` (`PossibleManifestSpec` /
      `enumerate_possible_shard_keys` / `is_valid_shard_key` / `canonical_path_templates`); composes the 3 layers, never
      re-declares; `canonical_path_templates` GENERATES the `pipeline_mode=batch_<source>/` prefixes from the source
      registry (Axis-10 de-scatter at the root). 41 tests. — uac@483e8c2a (QG-green, staging PR #119).
- [x] ✅ [UAC] P0. Axis-completeness assertion (each AG's spec declares every physical shard axis; DeFi `chain` guarded;
      RED on a missing axis) — the CF-15/CF-18 join. — uac@483e8c2a.
- [x] ✅ [REFACTOR] P0. Redirect + DELETE the scattered re-derivations: (b) `reconcile_phantom_manifest_rows_all.py`
      `prefix_tpls` now DERIVES from `canonical_path_templates` (hand-list DELETED; **byte-identical superset** verified
      for all 4 AGs) — is@da74c72c; (a) `enumerate_expected_universe.py` already reads the UAC validity layer (G1-ENUM,
      2026-06-07) — STUB docstring corrected to FULL is@da74c72c; (c) deployment-api VERIFIED already-canonical (counts
      the materialised 4-state per F4 + reads canonical UAC `get_chain_genesis_date`/`get_protocol_launch_date` — no
      bespoke cross-product to redirect). Grep-verified.

## V1 — Catalogue-seeded denominator at zero data (CF-16) — per-AG

- [x] ✅ [SCRIPT] P0. **CeFi**: VERIFIED FULL (not re-implemented) — the G1-ENUM shape-aware v2 producer
      (`_enumerate_v2_cefi`, is@6ea46565, 2026-06-07) already completed the CeFi path via the now-shipped
      `build_instrument_catalogue.py` + the UAC validity matrix; the stale STUB docstring is corrected is@da74c72c.
      Cross-checked master-plan G1-ENUM — no double-implementation.
- [x] ✅ [SCRIPT] P0. **Prediction**: VERIFIED FULL — `_enumerate_v2_prediction` (G1-ENUM) drives per-market lifecycle +
      per-row data_type grain-binding from the prediction catalogue; STUB docstring corrected is@da74c72c.
- [ ] [VERIFY] P0. **DeFi / TradFi / Sports**: verify the FULL enumerators now read V0's generator (no regression);
      0-data cell → `expected_unattempted` denominator. slot-2. instruments-service.

## V2 — Orphan sweep + bucket prefix taxonomy + sizing (CF-17) — slot-3 tool, both run

- [x] ✅ [SCRIPT] P0. Built the **orphan sweep** `migration_orphan_sweep.py` (GCS→manifest, the phantom-reconciler
      inverse): single walk → forced 6-class taxonomy (A/B/C/C2/D/E) with **grain-aware wildcard covering** (manifest
      coarser than objects → blank manifest field = wildcard; the fix for the prediction `A=0` false-orphan class). 18
      tests. — is@da74c72c. **RAN on real prod GCS** (cefi 5.3M obj + prediction).
- [x] ✅ [SCRIPT] P0. **Bucket prefix taxonomy**: every top-level prefix labelled (incl. the separate
      `processed_candles` corpus + vm-staging/logs, understood + never raw-tick-deleted); **`unknown_prefixes==0`
      verified on the full cefi + prediction walks** ("every byte accounted for"). — is@da74c72c.
- [x] ✅ [SCRIPT] P0. **Sizing rollup** published: cefi total **22.8 TiB** across 101 cells (biggest: DERIBIT trades
      ~3.6 TiB, OKX/BINANCE/KRAKEN book_snapshot_5 ~1 TiB each — pre-download candidates); prediction 22.7 GiB. Rides
      the single walk. — is@da74c72c.
- [x] ✅ [RUN] P0. Per-AG acceptance: `orphan_class_E==0` ∧ `unknown_prefixes==0` — **🟢 GREEN ON ALL FOUR HIVE AGs
      (2026-06-11 ~14:32Z)**: defi E=0 (13:14Z) · cefi E=0 (13:14Z, was 74,392) · prediction E=0 (13:28Z, was 61,014) ·
      tradfi E=0 (14:32Z, was 47,102); unknown*prefixes=0 everywhere. Mechanics: backfill applies (prediction 17+7,445
      converted/2,477 cells; tradfi 14,707+987 converted/~350 cells; cefi 74,392 record-only/7,965 cells; defi 100%
      matcher-false-positive — 0 needed) + one-shot `manifest_consolidator.consolidate(force=True)` per bucket (per-VM
      backfill shards → consolidated index; NO data loss — every index ≥ its pre_migration_2026_06_08 snapshot) + sweep
      fixes (pre-hive blank-venue derivation via shared backfill parser is@f73abe4; lazy footer read via UCI
      `download_bytes` — 7 weekend 0-row shells honestly split to class D). Final reports:
      `\_index/audit/orphan_sweep*<ag>.parquet` (refreshed per AG). **Sports = R8 — 🟢 GREEN 2026-06-11 ~16:12Z** (BOTH
      sports buckets E=0 + unknown_prefixes=0 via the candidate_parquet_paths-driven sweep — see the R8-part-2 Progress
      Log entry; all 5 AGs now orphan-clean). NOTE for R7/R3 verdict packs: re-run all four sweeps once more on final
      HEAD for the sign-off snapshot (defi/cefi/pred verdicts predate the last two sweep fixes — non-material to their
      corpora, but Citadel re-verifies on final code).
- [x] ✅ [SCRIPT] P0. (is@d4190ba — scripts/manifest_diff.py + tests, grain-aware wildcard covering via
      possible_manifest, human + --out JSON) **Manifest-diff tool (projected-vs-current) — operator 2026-06-10.** Build
      `instruments-service/scripts/manifest_diff.py`: load TWO `_index` parquets (the `beta_manifest_writer` PROJECTED
      v9 vs the CURRENT/live consolidated `_index`), diff by shard-key → report added / removed / changed cells +
      `capture_status` transitions + per-(AG,data_type,venue) row deltas. This is the manifest-vs-manifest diff
      (distinct from the orphan sweep's GCS-vs-manifest and the beta writer's projection) — it's what lets us SEE the
      goalposts as a delta before `--apply`. Reuses `possible_manifest.canonical_path_templates` for key alignment.
      slot-3 (cross-cutting tool); both AGs run it as part of the V5 projected-preview verdict.

## V3 — Schema-attribute completeness (CF-18) — slot-3 framework, both run

- [x] ✅ [SCRIPT] P0. Framework `migration_schema_completeness.py`: footer-column union per (AG, data_type, venue) vs
      the v9 UAC canonical contract (`schema_spec.find_schema`); RED on any silently-dropped column; partition/meta
      columns excluded; rides the orphan-sweep object list (single-walk). 8 tests. — is@da74c72c.
- [x] ✅ [RUN] P0. (2026-06-11 R2 COMPLETE — CITADEL, zero acked drops: uac@715e2ed carries ALL source columns incl. the
      11 polymarket cols via source_aliases rename maps + new defi/tradfi/prediction SchemaSpecs; alias-aware matching
      via UAC carried_column_names shipped in the checker; VERDICTS: defi 0 RED/32 cells, tradfi 0 RED/19, prediction 0
      RED/2; cefi re-verifies on R1's sweep re-run) Per-AG: any source column not carried into v9 = RED → carry it
      (extend canonical schema BEFORE apply) or operator-ack the drop in this plan. **Zero silent truncation.**
      cefi/pred=slot-3; defi/tradfi/sports=slot-2.

## V4 — Candle edge-timestamp audit (CF-19) — per-AG owner of the external OHLCV source

- [ ] [VERIFY] P0. Per external OHLCV/candle source × timeframe, confirm left-edge(open)/right-edge(close) label matches
      `codex/02-data/bar-boundary-candle-edge-convention.md` + an independent reference bar; one normalization point;
      batch==live agree. (Issue already filed/maybe-fixed — this makes it a standing check.) Owner = the AG's source
      owner.

## V5 — Projected-manifest preview + data-status render (CF-20, ⑭) — slot-3 harness, both render

- [x] ✅ [SCRIPT] P1. `beta_manifest_writer.py` — `write_projected_index(df, --beta-manifest-out gs://<dev>/…)` writes
      the projected v9 `_index` (schema*version stays 9 = "v9 projected"); **dev-target HARD-guard** (refuses any
      prod/staging `_index`); no objects moved. Migrator dry-runs call it. 4 tests. — is@da74c72c. *(The per-AG dev
      render + operator goalpost eyeball remains — next item.)\_
- [x] ✅ [VERIFY] P1. Per-AG dev render — **DONE via the superseding `DATA_STATUS_BETA_MANIFEST_BLOB` mechanism**
      (deployment-api `services/manifest_source.py`, landed 2026-06-11: the env var redirects EVERY data-status surface
      to `_index/audit/projected_index_{asset_group}.parquet` in the SAME prd bucket — read-only, no dev-bucket copy,
      loud-fail on a missing projection; supersedes the dev-bucket-drop recipe — 3 of 5 dev buckets never existed).
      BETA-vs-LIVE rendered + captured for instruments + market-tick-data data-status views (all 5 AGs inline);
      evidence + per-AG verdict packs at `plans/audit/results/r3_beta_renders_2026_06_11/` (pm@a30de5abd). **Operator
      goalpost EYEBALL remains open — V6.** | regression: deployment-api tests/unit/services/test_manifest_source.py

## V6 — Pre-apply verdict → G4 → verified-delete (CF-21)

- [ ] [VERIFY] P0. Per-AG pre-apply verdict: ⑬–⑲ all GREEN (added to that AG's ①–⑫ audit verdict). Feeds the master
      coordinator's G4 gate. cefi/pred=slot-3; defi/tradfi/sports=slot-2.
- [x] ✅ [SCRIPT] P0. **G4.5 verified-delete** `cleanup_legacy_twins.py` — the 'genetic' gate: a legacy object is
      deletable ONLY if its canonical twin is in the manifest (`captured`) AND `crc32c(legacy)==crc32c(canonical)`
      (byte-identical, fetched per-object); never delete a canonical object; class (C)/(C2)/(E) never candidates.
      `--dry-run` default; `--apply` requires `--i-understand` + operator-gated like G4. 8 tests. — is@da74c72c. _(The
      `--apply` RUN stays operator-gated — post-apply re-runs the orphan sweep, E still 0.)_ slot-3 tool, both run.

## V7 — Durability: re-runnable audit instructions (operator 2026-06-10) — slot-3, cross-cutting

- [x] ✅ [DOC] P0. CF-15…CF-21 added to `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` in
      steady-state v9 form — pm@<pending-flip>. (Done in this planning session; flip on ship.)
- [x] ✅ [DOC] P0. Add the CF-15…CF-21 concrete checks to each owning per-service instruction file (`manifest_master`
      CF-15/17/21 · `instruments_master` CF-16 · `mtds_mdps_master` CF-18/19 · `deployment_and_user_management_master`
      CF-20) so re-running the per-service audit covers them — steady-state v9 form, concrete runnable commands. No CF
      item left without an owning audit. — pm@<flip>.

## B — MVP, config-versioning, execution-config compatibility (lower priority; reference existing plans)

- [ ] [SCRIPT] P1. MVP Phase 2-3 — already in `mvp_scope_catalogue_tagging_2026_06_08.md` (deployment-api
      `scope=mvp|could_exist|all` + UI tick + features/strategy/model sections). Schedule, do not re-file.
- [x] ✅ [DESIGN] P1. `config_version` (per-config monotonic int + content-hash on `MVP_SCOPE` / sports-leagues /
      prediction-markets; surfaced in data-status so a coverage delta attributes to scope-change vs data-change; NO GCS
      partition key) — DESIGN folded into `mvp_scope_catalogue_tagging_2026_06_08.md` § "Config versioning
      (config_version)" with per-config decision + 3 implementation todos. — pm@<flip>. slot-3.
- [ ] [DESIGN] P1. **Execution-config compatibility pre-flight** (audit-and-enhance, NOT a new catalogue) — composite
      `assert_execution_config_compatible(archetype × venue × instrument × required-matching-fidelity)` joining the
      existing `archetype_capability` (SUPPORTED/BLOCKED — "staked_basis can't bet") + `archetype_capability_matrix`
      (venue actions / fill-margin-settlement) + `data_type_capability` (L1/L2/trades/ohlcv granularity → matchability).
      **Post-G4** (consumes the post-migration honest granularity). File under the **execution epic**. slot-2.

## Success criteria

1. V0 registry is the single could-exist SSOT; 0 bespoke cross-products remain (grep-verified).
2. Per AG: `phantom_count==0` ∧ `orphan_class_E==0`; bucket prefix taxonomy has 0 `unknown`; sizing published.
3. Per AG: schema-attribute completeness GREEN (every source column carried or operator-acked); candle-edge GREEN.
4. Projected v9 `_index` renders in dev data-status/UI; operator goalpost sign-off per AG.
5. G4 `--apply` (operator) → orphan-E still 0 post-apply → G4.5 deletes only crc32c-identical in-manifest twins.
6. CF-15…CF-21 encoded in the checklist + owning per-service instruction files (re-runnable forever).

## Progress Log

- 2026-06-12 (~11:45Z, operator eyeball session) — **unique-instruments headline SHIPPED + LIVE** (operator: "the
  headline should be unique... the catalogue should be deduplicating" — correct on all counts). The lifecycle catalogue
  (`prod/catalog.parquet`, one row per instrument identity) IS the dedup source; the headline was summing per-shard
  `instrument_count` over the latest day. Shipped: `read_unique_instrument_count` (catalogue-backed, cached,
  null-honest) + per-AG/totals plumbing + the coverage-summary LIVE-rollup beta-bypass (same CF-20 rule as
  get_manifest_status) — deployment-api@5938b3e + prediction-bucket-kind fix; deployment-ui headline now leads with
  "unique instruments (catalogue-deduplicated)" (tsc clean · 837 vitest · 44 playwright smoke · regression
  tests/unit/unique-instruments-headline.spec.tsx). Missing catalogues BUILT+PROMOTED via build_instrument_catalogue:
  sports 789 rows, prediction 0 rows. **LIVE figures: totals 914,212 unique — CEFI 220,222 · TRADFI 686,348 · DEFI 6,853
  · SPORTS 789 · PREDICTION 0.** Serving note: dev API runs from the .tabs/4 clone (the main clone's ff-pull is blocked
  by a 60-file foreign WIP batch — protected, untouched).
- [ ] [SCRIPT] P2. **Rollup worker: precompute `unique_instruments`** — the Cloud Run data-status rollup
      (deployment_api/scripts/data_status_rollup_worker.py) predates the field; in LIVE (non-beta) mode the rollup
      fast-path serves coverage summaries WITHOUT unique_instruments until it recomputes them. Add the catalogue read to
      the worker + redeploy the Cloud Run job. Repo: deployment-api. Provenance: operator ask 2026-06-12.
- [ ] [DATA] P2. **Prediction catalogue roll-up finds 0 rows** — `build_instrument_catalogue --asset-group prediction`
      promoted a 0-row catalogue (the pred per-date defs under instruments-store-pred `instrument_availability/` aren't
      picked up by the default by-date prefix/layout). Wire the prediction-specific layout (market-lifecycle grain per
      build_prediction_catalogue_dataframe) so unique_instruments reads a real count (493 IS rows / ~thousands of
      markets expected). Repo: instruments-service. Provenance: /tmp/catalogue_prediction.log.

- 2026-06-12 (~10:35Z, operator beta-eyeball session) — **beta render made FULLY consistent**: the operator's "is it
  using the right manifest" check exposed (1) the live-rollup fast-path serving LIVE data in beta (fixed dapi@1f1ad77 —
  R3 agent's bypass, +2 regression tests) and (2) instruments-store beta reads silently falling back (no IS-store
  projections existed; callers' catalog fallbacks masked the loud-fail). Fixed:
  `migrate_instruments_store_v9 --projection-out` (is ship) materialized ALL FIVE IS-store projected indexes (tradfi
  20,388 · cefi 30,803 · defi 125,242 · sports 2,681,628 · prediction 493 rows at
  `gs://instruments-store-<ag>-prd/.../_index/audit/projected_index_<ag>.parquet`). VERIFIED in the running API:
  data-status manifest calls log BETA reads on BOTH bucket families, zero rollup serves. UI labelling note for the
  packs: the headline "25,873,530 instruments (latest day, sum across asset groups)" = Σ per-AG latest-day
  instrument/row counts (a per-day volume gauge), NOT unique instruments; all-time analog is `total_instruments` (cefi
  121.2B).

- 2026-06-11 (~21:35Z, autonomous run, END-OF-RUN) — **R3 RENDERS + VERDICT PACKS DONE — the full pre-apply harness is
  assembled; everything except the operator eyeball/sign-off is COMPLETE.** Beta renders captured via the new
  `DATA_STATUS_BETA_MANIFEST_BLOB` (BETA vs LIVE, instruments + market-tick-data data-status views, all AGs); five
  verdict packs + evidence at `plans/audit/results/r3_beta_renders_2026_06_11/` (pm@a30de5abd), each ending "G4 --apply:
  AWAITING OPERATOR". Dev stack stopped after capture. Self-audit: all .tabs/4 trees clean + every ship an ancestor of
  origin LDR; 3 dirty MAIN clones are OTHER live workers' WIP (protected, untouched). OPERATOR QUEUE (the only remaining
  work): ① read the 5 verdict packs → per-AG sign-off; ② decisions: prediction cqg-classifier coverage (P1, blocks
  prediction apply) · sports blank-capture_status 6,869 + C3 coverage-window · cefi 943 phantom downgrades ack; ③ fire
  the five G4 --applies (suggested order tradfi→cefi→defi→sports→prediction); ④ G4.5 verified-delete (incl. v1_archive
  398 + legacy twins); ⑤ un-drain consolidators + fleet resume → G5.

- 2026-06-11 (~20:50Z, autonomous run) — **TRADFI FINAL PROJECTION+DIFF ADJUDICATED (completes the R7 5-AG set)**. With
  the coalesce fix live (rode mtds@77f1a61), the definitive run: projected 946,360 rows (unparseable 106 of 902,878 =
  0.012%), diff collapsed 14,833→4,374 removed / 6,739→2,902 downgrades, **unchanged=57,841 + added=2 + 14
  empty→captured UPGRADES** (objects found where the index claimed empty). Residual adjudication (sweep-inventory join,
  sample-rate): **removed ≈79% garbage-venue rows (UNKNOWN/blank — correct v9 drops) + ~10% phantoms + ~11% legacy
  instrument_type respelling supersession** (combo/future rows → canonical futures_chain vocabulary; data present under
  the canonical key — same class as defi's venue-respelling verdict); **downgrades ≈91% phantom closed-market
  over-claims honestly reclassified** (spot-verified class) **+ ~9% weekend-boundary cells** (CME Sunday-session dates —
  calendar-aware CF-11 governs post-apply; NOTE for the verdict pack, not a blocker). With the agent's four verdicts
  (sports GREEN 0/0 · defi 5,320 respelling-justified · cefi garbage+phantom-justified · prediction superseded-grain +
  the cqg-classifier P1), **all FIVE AG projections now exist with adjudicated, justified diffs — the ⑬–⑲ analytic
  inputs are complete**. Remaining R3: dev beta-render eyeball packs (operator).

- 2026-06-11 (~20:30Z, autonomous run) — **R7 dispatch COMPLETE: CF-20 `--beta-manifest-out` wired into the FOUR
  remaining manifest rebuilds (defi/cefi/prediction/sports), projections run on prod, diffs adjudicated CITADEL-grade.**
  Ships: mtds@77f1a61 (wiring batch — shared `ProjectionCollector` imported into all four; the CF-11 staleness fix
  [direct CONSOLIDATED read PRIMARY, `read_availability_index` fallback-only] applied to cefi/prediction/sports; **defi
  gained its FIRST CF-11 honest-absence re-emit** [pure object-scan rebuild was silently dropping the whole 1.23M-row
  defi absence corpus]; sports gained `expected_unattempted` pass-through + read*consolidated_index; the tradfi loop's
  `write_projected_index` date-coalesce fix rode this batch as hand-off) + mtds@03fbc9b (adjudication fixes — prediction
  LEGACY `category=/data_source=` parser [578,162 pre-apply objects were 99.5% unparseable → 573,536 candidates parse];
  processed-candle corpus pass-through for defi+cefi [`processed_candles/` tree is outside the raw scan; prior captured
  processed rows were false-phantom-demoted]; cefi `spot`→`spot_pair` itype synonym [5,239 false phantom demotes —
  objects verified at spot_pair]; cefi double-hive-key parse [`asset_group=cefi/category=cefi/`, 6 objects → unparseable
  0]). ~25 unit tests added/extended across 7 test files (incl. the `_no_consolidated()` failing-storage seam retrofit
  to all CF-11 suites + `test_rebuild_projection_dates.py` regression for the mixed `processing_date`/`date` coalesce).
  Projections at
  `gs://market-data-tick-<tag>-prd-…/\_index/audit/projected_index*<ag>.parquet`; diffs `/tmp/manifest*diff*<ag>.json`.
  **Per-AG verdicts (projected rows | diff | justification):**
  - **sports (mdps odds)**: 786,508 rows | **GREEN — removed=0, captured_regressions=0, changed=0, 55,412 cells
    unchanged** | 17,288 blank-status rows (ODDS_API 2026-04-08 zero-count probe artifacts) honestly excluded — cell
    coverage unaffected. ⚠️ FINDING for the sports-AG owner: the CF-5 oracle relabel fired ZERO relabels
    (584,257/584,257 `keep_src_zero`) on the MDPS dry-run — the step 4–7 gates all fall through (suspect league_id
    resolution); reason-level relabel currently INERT (status-level diff unaffected).
  - **defi** (bucket market-data-tick-defi-prd, 2020-01-01→2026-06-11): 347,074 captured shards + 1,227,971 empty
    - 2,740 failed re-emits + 2,252 processed-captured pass-through ≈ 1.58M rows | **captured_regressions=0, changed=0;
      removed=5,320 — ALL justified**: 5,216 = legacy venue-RESPELLING duplicate cells (AAVEV3 2,528 / UNISWAPV2 1,264 /
      UNISWAPV3 1,256 / UNISWAPV4 168 — twin coverage VERIFIED 0-missing under the canonical spellings, e.g. AAVE*V3
      29,782/29,782 (date,dt) twins) + 104 = EIGENLAYER (rewards,staking) → (eigenlayer_rewards,staking) data_type/itype
      respelling per the on-disk path truth (twins verified). added 7,740 = NEW coverage (e.g. VAULT vault_share_price
      2020+) — additive. 5,332 unparseable = bare-venue `ticks_migrated*\*` leaves (by design unmanifestable; E7
      deletes).
  - **cefi** (2019-01-01→2026-06-11): 2,483,050 captured shards + 1,304,041 failed + 89,590 CF-11 reclassifies + 8,387
    processed pass-through ≈ 3.89M rows | removed=733 — ALL the dispatch-named GARBAGE class (venue=UNKNOWN 27 +
    Bitfinex F0 symbols-as-venue BTCF0/ETHF0/DOTF0/… — 0 GCS objects under any such venue path) → EXPECTED removals;
    captured→attempted_failed=943 — GENUINE phantom captured rows (spot-verified: BINANCE-SPOT 2021-01-04 BTCUSDC has
    trades objects but NO book_snapshot_5 object; 828+655 BINANCE-SPOT book/trades + DERIBIT chains) → the HONEST
    correction, presented per the tradfi precedent, not suppressed; empty→attempted_failed=3,853 = the CF-11
    GUARANTEED_WHEN_LISTED within-bounds reclassification (BY DESIGN).
  - **prediction** (pred-prd, 2025-01-01→2026-06-11): 573,536 objects read (full corpus, 2,102 s) → 1,355 captured cqg
    bundles + 542,169 ClassifierConfidenceLow + 2,330 empty / 2 failed re-emits = 545,855 projected rows | added=352
    (the NEW canonical `prediction_canonical_question_group` cells), removed=3,588 — the legacy RAW-grain cell families
    (`trades` / `prediction_trades` per-date rows incl. blank/UNKNOWN-venue artifacts and the btc/eth/other
    pseudo-itypes from `ticks_migrated_*` bundles) — SUPERSEDED BY DESIGN by the bundled cqg atom (the E5 rewrite spec:
    the canonical shard atom replaces the raw grain; live writer emits ONLY bundles); captured→empty=4 (2026-04-26..29 —
    dates where ZERO objects classify into any cqg, see the finding below); 7,462 residual unparseable = the 2026-04-19
    `ticks_migrated_*` per-underlying bundles (same by-design class as defi; no per-cid identity, unmanifestable at the
    canonical atom). **Cross-checks**: tradfi's `write_projected_index` coalesce regression-tested
    (`tests/unit/test_rebuild_projection_dates.py`); all CF-11 unit suites retrofitted with the `_no_consolidated()`
    failing-storage seam. Diff JSONs: `/tmp/manifest_diff_{defi,cefi,sports,prediction}.json` on the worker host.
- [ ] [DATA] P1. **Prediction cqg classifier coverage decision BEFORE the pred G4 apply**: 542,169/573,536 objects
      (94.5%) route to `attempted_failed[ClassifierConfidenceLow]` under the operator-corrected contract (None → NOT
      bundled, no "OTHER" fallback), and captured cqg bundles END 2026-04-14 (the 4 trail dates 2026-04-26..29 have real
      trades objects but ZERO classifiable bundles → honest captured→failed downgrade at the canonical grain). Either
      EXTEND the UAC `canonical_question_group` registry coverage (most Polymarket markets are
      sports/politics/entertainment outside the MVP crypto set) or operator-ratify that out-of-registry markets stay
      failed-for-retry. Repos: unified-api-contracts (+ rebuild re-run). Provenance: /tmp/r7_proj/prediction2.log
      2026-06-11.
- [ ] [DATA] P1. **Sports CF-5 oracle relabel fired ZERO relabels on the MDPS dry-run** (584,257/584,257
      `keep_src_zero`; truth set 189,740 pairs loaded, league match-rate 61.8%) — the step 4–7 gates all fall through
      (suspect league_id resolution / venue=bookmaker rows carrying no league mapping). Reason-level CF-5 relabel is
      currently INERT on MDPS (status-level diff unaffected — GREEN). Diagnose before relying on the relabel for the
      sports verdict pack. Repo: market-tick-data-service. Provenance: /tmp/r7_proj/sports.log 2026-06-11.

- 2026-06-11 (~19:10Z, autonomous run) — **FINAL SIGN-OFF SWEEP SNAPSHOT: ALL FIVE AGs GREEN on final HEAD** — defi E=0
  (18:52Z) · cefi E=0 (19:00Z) · prediction E=0 (19:02Z) · tradfi E=0 (19:07Z) · sports odds E=0 + reference E=0
  (19:09–19:10Z); unknown*prefixes=0 on every surface. Reports refreshed at
  `\_index/audit/orphan_sweep*<ag>.parquet`(+ sports per-bucket). This is the ⑬-input snapshot for the verdict packs. ALSO:`DATA*STATUS_BETA_MANIFEST_BLOB`smoke-verified END-TO-END against real GCS (deployment-api seam loaded the 946,360-row tradfi projection with the env set; live index with it unset) — the operator's beta-render recipe is live:`DATA_STATUS_BETA_MANIFEST_BLOB='\_index/audit/projected_index*{asset_group}.parquet'`+`restart-deployment-stack.sh
  --api`.

- 2026-06-11 (~18:50Z, autonomous run) — **R7 tradfi adjudication: ROOT CAUSE of the all-red diff FOUND + fixed (pending
  ship via the 4-rebuild batch)**. Chain of finds, each verified on real data: (1) rebuild legacy parser shipped
  (mtds@c21bc91) — unparseable 183,943→106 (99.94%); (2) manifest_diff coarse-query union + symmetric effective-status
  compare shipped (is@3a2d5a4 + follow-up) with regression tests; (3) **the remaining all-red diff (14,833 removed /
  6,739 downgrades) reduces to ONE bug in `_rebuild_projection.write_projected_index`: captured rows carry
  `processing_date`, re-emitted absence rows carry `date` — with BOTH columns present the rename-if-missing was skipped
  → every captured row's `date`=NaN → the differ dropped the ENTIRE captured side and read the projection as
  absence-only.** Coalesce fix written + unit-verified in
  `.tabs/4/market-tick-data-service/market_tick_data_service/scripts/_rebuild_projection.py` (uncommitted — the
  4-rebuild agent's QG-sweep batch owns the clone; the fix rides its batch or ships immediately after). ALSO genuinely
  adjudicated from the pre-fix diff: current tradfi index holds **phantom captured rows on closed-market days**
  (spot-verified ×3: 2020-01-01 BARCHART/CBOE/CME ohlcv_15m captured with 0 GCS objects) — the projection's
  captured→empty/failed downgrades for those are the HONEST correction, to present in the verdict pack, not suppress.
  Re-projection + final diff re-run follows the coalesce ship.

- 2026-06-11 (~18:15Z, autonomous run) — **R7 part 1: IS store-migrator re-dry-runs GREEN ×5 on final HEAD** (exit 0
  all): cefi 30,803 captured · defi 125,242 captured · tradfi 19,247 captured + 1,141 empty*confirmed · sports
  2,674,759 + 6,869 BLANK-status rows (see todo below) · prediction 4,693 planned/0 moved — every projected row
  v9-shaped (`schema_version=9`, `pipeline_mode=batch_instruments_service`, `source=instruments_service`,
  `transport=rest`). Logs
  `/tmp/r7_is*<ag>\_dry.log`. **TradFi market-tick R7 reference loop** (in flight): rebuild now projects via `--beta-manifest-out`
  (mtds@fa375c7), CF-11 reads the CONSOLIDATED index + collector receives re-emits (37,477 empty + 6,042 failed
  collected), row_key flattened for the differ; diff progressed 45,003→14,831 removed; remaining removals characterized
  = the 183,943 PRE-HIVE/no-instrument_type legacy objects' cells (FX 1,967 spot_pair · CME chains · CBOE 15m ·
  NYSE/NASDAQ equity 1m) — parser extended with legacy shapes C (hive-no-instrument_type) + D (pre-hive instrument-key,
  ported from the R1 backfill grammar) + an unparseable shape histogram; re-projection running.
- [ ] [DATA] P1. **sports instruments-store: 6,869 manifest rows with BLANK capture_status** (IS migrator dry-run
      2026-06-11 — invalid v9; the closed 4-state set excludes blank). Characterize (which entity/date families) →
      re-stamp with the honest status (or drop if phantom) BEFORE the sports G4 apply. Repo: instruments-service.
      Provenance: /tmp/r7_is_sports_dry.log.

- 2026-06-11 (~16:15Z, autonomous run) — **R8 part 2: SPORTS orphan sweep GREEN on BOTH buckets — `E==0` +
  `unknown_prefixes==0` (the last asset group; ALL 5 AGs now orphan-clean).** Tools:
  `instruments-service/scripts/migration_orphan_sweep_sports.py` (is@94ea099 + is@37793dd; 38 unit tests) —
  candidate_parquet_paths-driven, league-grain wildcard covering, ODDS aggregate-era data_type equivalence
  (`trades`↔legacy `ODDS` rows), ODDS_API wire-league remap DERIVED from `LEAGUE_REGISTRY` ⋈
  `DEFAULT_CLASSIFICATION_REGISTRY` (never hand-listed), parallel footer-read E/D zero-row split — and the sports
  recorder `scripts/backfill_orphan_class_e_sports.py` (league-keyed cells; source+pipeline_mode resolved via UAC
  `SOURCE_PRIORITY` with mode-follows-source). Verdicts (reports at
  `gs://<bucket>/_index/audit/orphan_sweep_sports.parquet`):
  - **odds bucket** (market-data-tick-sports, 361,710 objects, 6.73 GiB): A=361,650 · C=5 · C2=54 · D=0 · **E=0** ·
    unknown=0. The 20 E were the R5 smoke-probe day (2026-06-09, NEW `pipeline_mode=batch_odds_api` canonical shape, 20
    bookmaker venues × SEGUNDA*DIVISION) whose captured rows sat in the unconsolidated
    `_index/per_vm/smoke-probe-sports.parquet` shard → ONE-SHOT `consolidate(force=True)` (success=True; 786,408 →
    803,796 rows, ≥ pre — no loss) → E=0, NO recording needed. 3,816 first-pass D were legacy odds shapes the classifier
    then learned (2022 `source=ODDS_API/league=<canonical>` + 2025 `venue=ODDS_API/league=soccer*\*` wire keys) — all
    reclassified A (covered).
  - **reference bucket** (instruments-store-sports, ~898k objects, 9.88 GiB data): A=727,061 · B=33,647
    (`sports_reference_v2/` staging twins + legacy flat-by-day twins) · B2=398 (v1_archive — own disposition per the
    part-1 row-coverage gate) · C=119,873 · C2=5,151 (incl. reference-aux mappings + retired entities + the labelled
    `day=/venue=` instrument-DEFINITIONS tree) · **C3=10,345 (new disposition, below)** · D=1,490 (zero-row shells) ·
    **E=0** · unknown=0. Backfill: E **87,659 → 0** — ~81.8k distinct (day, data_type, league) cells footer-verified
    rows>0 and recorded over 3 passes (80,491 + 8,624 + 1) + 1 definitions-availability row (the 2 stray
    `day=2026-03-21/venue=BETFAIR` instrument-definition parquets, 1,542 rows, appended to
    `availability_index/instruments-service.parquet`) + 3 one-shot consolidations (success=True; index 2,681,044 →
    2,681,628 — no loss). Real divergence found + encoded: the sports entity map says footystats for STANDINGS/TEAMS
    while UAC `SOURCE_PRIORITY` (the writer-enforcement truth) allows only api_football (858 MissingSourceError cells
    pass-1), and ODDS must stamp BATCH_FOOTYSTATS not BATCH_ODDS_API (PipelineModeSourceMismatch — mode follows source);
    the recorder now resolves via SOURCE_PRIORITY.
  - **C3_pre_launch_window — NEW sweep disposition (10,345 objects)**: real data whose (data_type, day) is BEFORE the
    UAC sports coverage window (`SOURCE_COVERAGE_START`/`DATA_TYPE_COVERAGE_START`) — the 2026-04/05 footystats
    HISTORICAL fetches over 2018 days + api_football fixture sub-entities (FIXTURE_STATS/EVENTS/LINEUPS/PLAYER_STATS)
    before their 2020-06-06 window. The manifest CONTRACTUALLY refuses such rows (`ManifestWriter` pre-launch guard,
    born of the 2026-05-04 229,224-phantom-purge incident — it silently dropped the first-pass recordings, which is HOW
    this surfaced), so class E is the wrong label and record_captured is structurally impossible without a UAC window
    change → labelled disposition + the operator-gated todo below. Understood, never deleted.
- [ ] [DATA] P1. **Sports pre-launch-window corpus decision (C3, 10,345 objects — operator-gated)**: either extend the
      UAC windows (`SOURCE_COVERAGE_START["footystats"]` 2019-01-01 → 2018-01-01 — the footystats HISTORICAL season API
      demonstrably serves 2018 rows now on disk; + the api_football `DATA_TYPE_COVERAGE_START` sub-entity windows) and
      re-run `backfill_orphan_class_e_sports.py` to manifest the corpus, OR ratify the corpus as permanently
      outside-window (it then becomes a CF-21-style cleanup candidate). Blast radius of a window change: backfill
      orchestrators start fetching those windows (`clip_dates_to_source_coverage`), data-status denominators, the
      phantom audit. Repos: unified-api-contracts + instruments-service. Provenance: R8 sweep 2026-06-11 (C3 rows in the
      reference bucket's `orphan_sweep_sports.parquet`).

- 2026-06-11 (~14:50Z, autonomous run) — **R8 part 1: sports v1_archive ROW-coverage gate GREEN — fully superseded,
  drop-safe**. Archive integrity first (operator asked "is it corrupt?"): 398 daily fixtures parquets (364×2018 +
  2019/2020 COVID tail + 2024–2026 stragglers), 72,522 rows, **0 corrupt / 0 zero-row / 0 null keys**, 8 within-file
  duplicate fixture_ids (~0.01%, postponed-replay listings), source=api_football, `league` is a nested struct, and
  **home_xg/away_xg are NULL in ALL 72,522 rows** (schema-only — strengthens the 2026-06-01 column-supersession verdict:
  no xG values to lose). ROW gate: first join on v1 `fixture_id` read 100% missing — namespace mismatch (v1 id is a
  synthetic `LEAGUE:HOME_v_AWAY:date` string); the TRUE key is **v1 `source_fixture_id` ↔ v2 `af_fixture_id`**, and on
  that key **398/398 days OK, 72,522/72,522 rows covered, 0 uncovered**. v1_archive is superseded column-wise
  (2026-06-01 verdict) AND row-wise (today) → eligible for the G4.5 verified-delete list (operator-gated; nothing
  dropped yet). Remaining R8: sports orphan sweep (candidate_parquet_paths-driven) + the prediction dry plan regen on
  final HEAD.

- 2026-06-11 (~14:35Z, autonomous run) — **R1 COMPLETE: orphan_class_E==0 + unknown_prefixes==0 on ALL FOUR hive AGs**.
  Closing loop after the 13:20Z entry: tradfi 995 residual root-caused twice — (1) pre-hive blank-venue paths
  (`data_type=ohlcv_15m/indices/CBOE/...`) could NEVER read covered (venue is identity, never wildcarded) → sweep now
  derives (venue, instrument_type) for blank-venue objects via the SHARED backfill parser (importlib, single-source);
  995→7. (2) The last 7 = weekend 0-row schema shells (footer num_rows=0, ~4KB; legacy writer artifacts on non-trading
  days) — the sweep's docstring PROMISED a lazy footer read for would-be-E but never implemented it; now implemented via
  UCI `client.download_bytes` (first attempt used `blob.download_as_bytes` — UCI `list_blobs` yields read-surface-less
  `BlobMetadata`, silently no-opped) → honest class-D split → **tradfi E=0 (14:32Z)**. V2 [RUN] acceptance flipped
  GREEN; master plan R1 todo flipped. Remaining in this plan: R8 sports gates; R7/R3 re-run all four sweeps on final
  HEAD for the sign-off verdict packs.

- 2026-06-11 (~13:20Z, autonomous run) — **R1 round-2: cefi + defi GREEN; tradfi/prediction residuals**. Round-2 tool
  (is@c49d957: record-EVERY-converted-cell with footer-exact frames + cefi record-only support + legacy instrument_type
  canonicalisation) applied clean: prediction 34 converted/17 cells · tradfi 28,483/248 cells · cefi 74,392/7,965 cells
  — 0 escalations/verify-fails. **KEY MECHANISM FOUND**: backfill records land in PER-VM shards; the sweep reads the
  CONSOLIDATED index and the consolidators are drained → ran ONE-SHOT manual
  `manifest_consolidator.consolidate(force=True)` on all 4 market-data-tick `-prd` buckets (success=True; **NO data loss
  — every index ≥ its `pre_migration_2026_06_08` snapshot**: tradfi 144,314 vs 144,062 · pred 16,839 vs 16,812 · cefi
  2,728,435 vs 2,640,864 · defi 1,578,922 vs 1,569,805; the old "579k/35.8M" Phase-0 numbers were the LEGACY buckets).
  **POST-CONSOLIDATION SWEEPS: defi E=0 ✅ · cefi E=0 ✅ (was 74,392) · tradfi E=995 (was 28,491) · prediction E=7,445
  (REGRESSION from 34 — pre-consolidation)**; unknown_prefixes=0 everywhere.
  - **Prediction regression hypothesis (diagnose first)**: consolidation `dedup_dropped=14,315/31,154` — if dedup
    survivors (newer smoke-probe/backfill shard rows) carry different venue-spelling/grain fields than the dropped
    twins, wildcard coverage flips and previously-covered objects re-orphan. Characterize the 7,445 E in the refreshed
    `orphan_sweep_prediction.parquet` against the dropped-row keys BEFORE re-recording anything (do not blindly
    re-backfill — fix the dedup-vs-coverage interaction or the matcher).
  - tradfi 995 = one residual family — characterize from the refreshed report.
  - NEXT: diagnose prediction dedup interaction → fix (consolidator dedup priority or sweep matcher) → re-apply
    residuals → consolidate → re-sweep → E==0 ×4 → flip V2 acceptance. ALSO: the R5 smoke shards (VM_NAME=
    smoke-probe-\*) GOT CONSOLIDATED into the prod indexes by the force pass — verify their rows are honest probe rows
    or prune them in the same fix.

- 2026-06-11 (~11:15Z, autonomous run) — **R1 backfill EXECUTED + first acceptance re-sweeps (mixed)**. Tool
  `backfill_orphan_class_e.py` (is@0a2e542 + refinements) ran on real prod: **the matcher refinements proved most E was
  FALSE-POSITIVE** (venue-spelling/grain): defi 254,984→**ALL already-covered**; prediction 60,997/61,014 covered
  - 17 converted+recorded (clean); tradfi 32,387 covered + **14,707 objects converted to canonical v9** (8 zero-row junk
    skipped, 0 escalations) + 249 cells recorded after the row-key fix (omit empty `chain` — MalformedRowKeyError; is
    ship) + tbbo spec extended (ts*init + bid_size/ask_size aliases — uac ship). **RE-SWEEP VERDICTS**: defi **E=0 ✅
    unknown=0** · prediction E=34 (small residual — characterize) · tradfi E=28,495 (**tool gap: the record pass only
    records cells with a retained representative frame — the other converted-twin cells stay unrecorded; must record
    EVERY cell touched by conversion**) · cefi **E=74,392 — the tool's --asset-group choices EXCLUDE cefi** (first
    refined-matcher cefi verdict; needs cefi support in characterize/convert maps). unknown_prefixes=0 on ALL FOUR
    (taxonomy fully labelled). NEXT (the iterate-to-green loop, in order): (1) tool: record all converted cells (group
    objects→cells independent of frame retention; read a frame per cell on demand); (2) tool: add cefi to CLI +
    characterization (tardis corpus shapes); (3) prediction 34 residual characterization; (4) re-apply tradfi+cefi →
    re-sweep all → E==0. Reports: `\_index/audit/orphan_backfill*<ag>.parquet` + refreshed orphan_sweep parquets.

- 2026-06-11 (~09:00Z, autonomous run) — **V3/CF-18 GREEN (R2 ratified decision #2 COMPLETE)**: UAC carries every source
  column (prediction trades/prediction*trades incl. the 11 polymarket columns + trader-profile payload, defi
  rewards/risk_params/utilization/dex_pool_swaps subgraph fields, tradfi trades/tbbo) via `source_aliases` rename maps
  in new
  `registry/\_schema_spec*{defi,prediction,tradfi}.py`(uac@715e2ed); the completeness checker now matches via UAC`carried_column_names`
  (canonical ∪ aliases — renamed-but-carried is GREEN, genuine drop stays RED; is ship). RE-RUN VERDICTS vs real prod
  GCS: **defi 0 RED (32 cells) · tradfi 0 RED (19) · prediction 0 RED (2)**. cefi re-verifies when R1's sweep re-run
  produces its report parquet. NOTE: the R-wave agents hit the account session limit (resets 10:10Z) — R2 was finished
  INLINE from their preserved WIP; R1/R4/R5/R6 resume per the brief in the master plan.

- 2026-06-10 — plan filed from audit `migration_orphan_safety_goalpost_verification_2026_06_10.md`; CF-15…CF-21 drafted
  into the canonical checklist (V7 item 1); registered as G3.5 in the master coordinator. Awaiting operator review +
  2-agent dispatch (slot-3 cross-cutting+cefi+prediction; slot-2 defi+tradfi+sports).
- 2026-06-10 (slot-3·laptop, finish-to-DONE) — **cross-cutting foundation + scaffolds BUILT & QG/test-green** (ships on
  staging unlock — a fleet-wide `ml-service=0.3.0` breaking-MINOR cascade locked staging mid-session; all units are
  `quality-gates.sh`-green-ready):
  - **V0 (CF-15) — `unified_api_contracts/registry/possible_manifest.py`** + 35 unit tests (UAC QG exit-0, basedpyright
    clean). `PossibleManifestSpec` / `enumerate_possible_shard_keys` / `is_valid_shard_key` / `canonical_path_templates`
    COMPOSE the 3 existing layers (no redeclaration). **`canonical_path_templates` GENERATES the
    `pipeline_mode=batch_<source>/` prefixes from the source registry** (Axis-10 de-scatter at the root). Re-exported
    top-level + registry `__init__`. Finding: cefi source-provenance is a RED gap → `SOURCE_PRIORITY` under-lists cefi
    sources, so an explicit authoritative `_KNOWN_BATCH_SOURCES_BY_AG` floor is unioned with the registry derivation.
  - **V0 redirect** — `reconcile_phantom_manifest_rows_all.py` `prefix_tpls` now DERIVES from `canonical_path_templates`
    (hand-maintained per-AG lists DELETED); **proven byte-identical superset** of the prior hand-list for all 4 AGs
    (cefi 8 / defi 15 / tradfi 9 / prediction 6). `enumerate_expected_universe.py` stale STUB docstring fixed (CeFi +
    Prediction are FULL via the G1-ENUM v2 producer — **cross-checked: G1-ENUM already shipped them 2026-06-07, NOT
    re-implemented**). deployment-api denominator VERIFIED already-canonical (counts the materialised 4-state per F4 +
    reads canonical UAC `get_chain_genesis_date`/`get_protocol_launch_date` — no bespoke cross-product to redirect).
  - **V2 (CF-17) — `migration_orphan_sweep.py`** (GCS→manifest, the phantom-reconciler inverse): single bucket walk →
    forced 6-class taxonomy (A/B/C/C2/D/E) + bucket prefix taxonomy (0-`unknown` bar) + sizing rollup. + 16 unit tests.
    **RAN against real prod GCS (cefi)** — validated end-to-end; surfaced + fixed a real refinement: the cefi bucket
    co-hosts a separate `processed_candles/` corpus (own manifest) + `_vm_staging/` + `backfill-logs/` → now labelled
    (processed-data / staging / logs), excluded from raw-tick orphan-E (7,946 objects were mis-read as class-E before
    the fix). Post-fix smoke: orphan_class_E=0, unknown_prefixes=0.
  - **V3 (CF-18) — `migration_schema_completeness.py`** (footer-column union vs the v9 `schema_spec.find_schema`
    contract; RED on any silently-dropped column) + 8 unit tests. Rides the orphan-sweep object list (single-walk).
  - **V5 (CF-20) — `beta_manifest_writer.py`** projected-v9-`_index` preview writer (dev-target HARD-guard;
    `schema_version` stays 9 = "v9 projected") + 4 unit tests. Migrator dry-runs call
    `write_projected_index(df, --beta-manifest-out)`.
  - **V7 (durability)** — CF-15…CF-21 concrete re-runnable checks encoded into the 4 owning per-service instruction
    files.
  - **B** — `config_version` per-config design folded into the mvp_scope plan.
  - **V6 (CF-21) — `cleanup_legacy_twins.py`** verified-delete (the 'genetic' crc32c + in-manifest gate; legacy object
    deletable ONLY if crc32c-identical to an in-manifest canonical twin; `--apply` operator-gated + `--i-understand`) +
    8 unit tests.
- 2026-06-10 (slot-3, per-AG RUN against real prod GCS — corrected verdict):
  - **Orphan-sweep matching CORRECTNESS FIX (found by running it at scale, not by unit tests).** The first full walks
    reported implausible counts (**prediction `A_canonical_manifested=0`** was the tell). Root cause: the manifest is
    keyed at a COARSER grain than the per-instrument object path — manifest rows carry blank `chain`/`instrument_type`
    (and sometimes blank `venue`) meaning "any", while objects carry `chain=POLYGON` etc. An exact 5-tuple match
    over-discriminated → false orphans. **Fixed**: grain-aware "wildcard covering" (`build_covered_index` +
    `is_covered`, a fixed 8-way blank-combination lookup — manifest blank field = wildcard) + 2 regression tests; 68
    scaffold tests green. This is the operator's "validate, don't assert" discipline paying off — the bug would have
    falsely reported a massive migration hole.
  - **CeFi full walk (5.3M objects, 22.8 TiB)**: `unknown_prefixes=0` (every byte accounted for) + sizing rollup
    published (biggest cells: DERIBIT trades ~3.6 TiB, OKX/BINANCE/KRAKEN book_snapshot_5 ~1 TiB each — pre-download
    candidates). Legacy-B vs orphan-E split being re-derived with the corrected matcher.
  - **Prediction full walk (corrected matcher)**: A=85 / **B=512,437 legacy** (pre-G4: the prediction corpus is still at
    the legacy `category=prediction/data_source=…` shape, not yet migrated to canonical `pipeline_mode=`) / C2=583k
    non-data / D=0 / **E=61,014 candidate orphans** / `unknown_prefixes=0`. The false-orphan count collapsed **563,281 →
    61,014** with the fix. **Verdict: prediction is NOT orphan-clean** — the 61k candidate-E (objects on
    dates/data_types outside the manifest's captured coverage: 402 dates 2025-03-13→2026-04-29, data_types
    `{trades, prediction_trades, ''}`) need per-AG characterization + **`record_captured` backfill before G4** (class E
    → backfill, NEVER delete). This is the "no-v10" check WORKING (it found candidate holes); closing them is the per-AG
    operational tail (partly operator/per-AG backfill).
  - **HARD-STOP respected**: everything up to `--apply` only; G4 `--apply` + G4.5 verified-delete `--apply` stay
    operator-gated.
- 2026-06-10 (slot-3) — **SHIP PENDING — an active (legitimately-converging) breaking-cascade staging lock, NOT this
  work.** The shared staging lane is locked (`reason="SIT running"`, `since=07:07Z`, ~73 min) for the in-flight
  `ml-service` / `deployment-api` / `deployment-service` breaking cascade (`breaking_pending` = those 3). It is
  CONVERGING, not stuck — `system-integration-tests` went STAGING*GREEN 08:04Z and several repos MAIN_GREEN 08:15-17Z;
  the per-repo "Staging Lock Check" failures on other promotes are by-design (the lane is serialized while a breaking
  cascade validates). quickmerge correctly refuses to enter a locked staging (no override; the lock is also a
  server-side required check), so the code (V0 + redirect + 5 scaffolds, all QG/test-green) promotes once the cascade
  clears — no intervention needed, no incident. PM docs ship via the docs(plans) direct-LDR carve-out (lock-independent;
  `pm@3d95dbb49`, `pm@f9ee262b3`). Code auto-ships on unlock. *(An earlier note here overstated this as a ~7.5h stuck
  incident — that was a local-vs-UTC timestamp misread; corrected: it is a normal ~73 min converging cascade.)\_
- 2026-06-11 (slot-4, autonomous finish-to-DONE run) — **scaffolds CONFIRMED on `staging`** (the lock converged as
  predicted: IS `scripts/migration_orphan_sweep.py` + UAC `registry/possible_manifest.py` both present on
  `origin/staging`). **V2 manifest-diff tool BUILT**: `instruments-service/scripts/manifest_diff.py` — loads projected
  (beta-writer) vs current/live `_index` parquet (local or `gs://`), grain-aware wildcard-covering key alignment via
  `possible_manifest` (mirrors the orphan sweep's `build_covered_index` discipline so coarse-vs-fine keys don't read as
  false adds/removes), reports added/removed/changed cells + `capture_status` transition matrix + per-(asset_group,
  data_type, venue) row deltas, human + `--out` JSON; unit tests on synthetic parquets. IS `quality-gates.sh --no-fix`
  green; **quickmerge held on a concurrent in-slot UTL WIP clearing the dep-audit — ships next** (the V2 checkbox flips
  on the sha). `migrate_instruments_store_v9.py` setup_events (M-COORD-6 IS slice) rode the same batch. V1 (B6) per-AG
  enumerator-reads-V0 verification evidence lands with the ship report.
- 2026-06-11 (slot-4, autonomous run) — **V2 per-AG sweeps RUN on real prod GCS for the 3 remaining AGs** (defi / tradfi
  / prediction; report parquets at `gs://market-data-tick-<ag>-prd-…/_index/audit/orphan_sweep_<ag>.parquet`). **All
  three RED, as the no-v10 check is designed to be pre-backfill:**
  - **defi: E=254,984 · B=60,727 · D=42,531 · unknown_prefixes=6,010** (78.27 GiB sized cells). CHARACTERIZATION: the E
    sample is **CANONICAL-shaped** paths (`…/asset_group=defi/venue=ORCA|RAYDIUM|SOLEND|KAMINO/chain=SOLANA/…`, written
    2026-05-04) — i.e. the `solana_defi_legacy_migration_2026_05_27` Gate-2 outputs that were migrated but never
    `record_captured`'d into the `_index`; and the unknown prefixes are exactly the known legacy top-level trees from
    that same plan (`dex_pools/` 3,606 + `lending_indices/` 2,402 + `_manifests/` + `configs/`). → the defi E-fix = the
    planned record_captured backfill + finishing Solana Gates 2/3 (NOT new holes); the sweep taxonomy needs those 3
    legacy-tree prefix labels added (tool follow-up, slot-3).
  - **tradfi: E=47,102 · B=1,597,119 legacy twins · A=1,641 · D=163,112 · unknown_prefixes=7,147** (108.42 GiB sized).
    E + unknown characterization rides the report parquet; B≈1.6M = the expected pre-G4 legacy corpus (the CF-21
    verified-delete candidates post-apply).
  - **prediction: E=61,014 (UNCHANGED vs the corrected 2026-06-10 count — stable) · B=512,437 · unknown=0.**
  - Per ⑬ the G4 `--apply` stays HARD-BLOCKED until E==0 per AG: the per-AG `record_captured` backfill (class E, never
    delete) is the operational tail. cefi corrected re-run queued next (walk slot freed).
