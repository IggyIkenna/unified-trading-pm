---
title:
  "Migration verification & orphan-safety — the 'migrate once, never need a v10' harness (canonical possible-manifest
  registry + bidirectional orphan sweep + schema-attribute completeness + catalogue-seeded denominator + candle-edge +
  verified-delete + projected-manifest preview), folded into re-runnable CF-15…CF-21"
created: 2026-06-10
parent_epic: epics/manifest_master.md
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

- [ ] [UAC] P0. Build `unified_api_contracts/registry/possible_manifest.py`: `PossibleManifestSpec[asset_group]` +
      `enumerate_possible_shard_keys(asset_group, *, catalogue) -> Iterator[ShardKey]` + `is_valid_shard_key(...)` +
      `canonical_path_templates(asset_group)`. **Composes (imports, never re-declares)** `SHARD_AXIS_MATRIX` (axis
      names) × `data_type_capability`/`archetype_capability_matrix` (value-domains) × the
      `(instrument_type × data_type)` validity matrix. Unit tests per AG. unified-api-contracts.
- [ ] [UAC] P0. Assert axis-completeness: each AG's spec declares every dimension its data physically carries (no AG
      silently missing a shard axis) — the CF-15/CF-18 join. Test fails RED on a missing axis. unified-api-contracts.
- [ ] [REFACTOR] P0. **Redirect + DELETE the scattered re-derivations** (no parallel paths): (a)
      `instruments-service/scripts/enumerate_expected_universe.py` drives from `enumerate_possible_shard_keys`; (b)
      `reconcile_phantom_manifest_rows_all.py` `prefix_tpls` derives from `canonical_path_templates`; (c) deployment-api
      denominator calls the registry (no re-derived genesis/launch). Grep-verify 0 bespoke cross-products remain.

## V1 — Catalogue-seeded denominator at zero data (CF-16) — per-AG

- [ ] [SCRIPT] P0. **CeFi**: complete the `enumerate_expected_universe.py` CeFi path (was STUB "needs IS catalog
      per-instrument lifecycle" — now unblocked by `build_instrument_catalogue.py` shipped 2026-06-05) via V0's
      generator; a 0-captured (venue, data_type) shows a full `expected_unattempted` denominator. **Cross-check
      master-plan G1-ENUM before writing — do not double-implement.** slot-3. instruments-service.
- [ ] [SCRIPT] P0. **Prediction**: complete the enumerator Prediction path (was STUB on `PREDICTION_GROUPS`) via V0.
      slot-3.
- [ ] [VERIFY] P0. **DeFi / TradFi / Sports**: verify the FULL enumerators now read V0's generator (no regression);
      0-data cell → `expected_unattempted` denominator. slot-2. instruments-service.

## V2 — Orphan sweep + bucket prefix taxonomy + sizing (CF-17) — slot-3 tool, both run

- [ ] [SCRIPT] P0. Build the **orphan sweep** (GCS-object→manifest, the inverse of the phantom reconciler): walk each AG
      bucket once; classify every object into (A) canonical+manifested / (B) legacy-duplicate-of-A / (C) manifest-infra
      / (C2) **non-data** (vm logs, run-artifacts, terraform, tarballs — understood, NEVER deleted) / (D) junk / (E)
      **real data with no manifest row**. Emit `_index/audit/orphan_sweep_<AG>.parquet`. **Single GCS walk** also
      produces V3 footers + sizing. instruments-service or mtds (per-AG owner). slot-3 builds, both run.
- [ ] [SCRIPT] P0. **Bucket prefix taxonomy**: every top-level prefix → labelled class; **0 `unknown` prefixes** is the
      acceptance bar ("every byte accounted for"). slot-3 tool.
- [ ] [SCRIPT] P0. **Sizing rollup**: bytes + object-count per `(asset_group, data_type, venue, pipeline_mode)` →
      `_index/audit/data_sizing_<AG>.parquet`; flag biggest cells for pre-download. Rides the same walk.
- [ ] [RUN] P0. Per-AG acceptance: `phantom_count==0` ∧ `orphan_class_E==0`. **Class (E) = backfill `record_captured`,
      NEVER delete** (it's the v10 hole). cefi/pred = slot-3; defi/tradfi/sports = slot-2.
- [ ] [SCRIPT] P0. **Manifest-diff tool (projected-vs-current) — operator 2026-06-10.** Build
      `instruments-service/scripts/manifest_diff.py`: load TWO `_index` parquets (the `beta_manifest_writer` PROJECTED
      v9 vs the CURRENT/live consolidated `_index`), diff by shard-key → report added / removed / changed cells +
      `capture_status` transitions + per-(AG,data_type,venue) row deltas. This is the manifest-vs-manifest diff
      (distinct from the orphan sweep's GCS-vs-manifest and the beta writer's projection) — it's what lets us SEE the
      goalposts as a delta before `--apply`. Reuses `possible_manifest.canonical_path_templates` for key alignment.
      slot-3 (cross-cutting tool); both AGs run it as part of the V5 projected-preview verdict.

## V3 — Schema-attribute completeness (CF-18) — slot-3 framework, both run

- [ ] [SCRIPT] P0. Framework: sample recent source/legacy parquets per (AG, data_type, venue); union footer columns;
      diff vs the v9 UAC canonical contract. slot-3.
- [ ] [RUN] P0. Per-AG: any source column not carried into v9 = RED → carry it (extend canonical schema BEFORE apply) or
      operator-ack the drop in this plan. **Zero silent truncation.** cefi/pred=slot-3; defi/tradfi/sports=slot-2.

## V4 — Candle edge-timestamp audit (CF-19) — per-AG owner of the external OHLCV source

- [ ] [VERIFY] P0. Per external OHLCV/candle source × timeframe, confirm left-edge(open)/right-edge(close) label matches
      `codex/02-data/bar-boundary-candle-edge-convention.md` + an independent reference bar; one normalization point;
      batch==live agree. (Issue already filed/maybe-fixed — this makes it a standing check.) Owner = the AG's source
      owner.

## V5 — Projected-manifest preview + data-status render (CF-20, ⑭) — slot-3 harness, both render

- [ ] [SCRIPT] P1. Add `--beta-manifest-out gs://<dev-bucket>/_index/availability_index.parquet` to the rebuild dry-run
      — writes the projected v9 `_index` (schema_version stays 9; "v9 projected", not a new schema), no objects moved.
      slot-3.
- [ ] [VERIFY] P1. Per-AG: drop the projected `_index` in the **dev** bucket, run `restart-deployment-stack.sh --api`
      with `DEPLOYMENT_ENV_SHORT=dev`; confirm data-status/deployment-UI render coverage % + 4-state + could-exist
      denominator + drilldowns; operator eyeballs the goalposts. Delete the dev `_index` after. cefi/pred=slot-3;
      defi/tradfi/sports=slot-2.

## V6 — Pre-apply verdict → G4 → verified-delete (CF-21)

- [ ] [VERIFY] P0. Per-AG pre-apply verdict: ⑬–⑲ all GREEN (added to that AG's ①–⑫ audit verdict). Feeds the master
      coordinator's G4 gate. cefi/pred=slot-3; defi/tradfi/sports=slot-2.
- [ ] [SCRIPT] P0. **G4.5 verified-delete** (`cleanup_legacy_twins_<AG>.py --dry-run|--apply`): a legacy object is
      deletable ONLY if its canonical twin is in the manifest (`captured`) AND `crc32c(legacy)==crc32c(canonical)`;
      class (C)/(C2)/(E) never deleted. `--apply` operator-gated like G4. Post-apply re-run orphan sweep (E still 0).
      slot-3 tool, both run.

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
