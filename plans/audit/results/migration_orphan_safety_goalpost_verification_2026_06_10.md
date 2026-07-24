---
doc_type: audit-result
title:
  AUDIT — migration orphan-safety, beta-manifest goalpost preview, verified-delete gate, data sizing & schema-attribute
  completeness (the 'migrate once, never need a v10' verification harness) + MVP-tag / config-versioning reconciliation
summary: >-
  "Migrate once, never need a v10" verification-harness audit: maps the operator's 12 asks against the mature ①–⑫
  pre-apply audit and identifies the 5 uncovered verification concerns → new points ⑬–⑰ + a G4.5 cleanup gate. Core
  gaps: no GCS→manifest orphan sweep (class-E = real data with no manifest row = the v10 trigger), no schema-ATTRIBUTE
  completeness freeze (only cell completeness gated), no v9-projected beta-manifest preview, no byte-sizing rollup, no
  consolidated possible-manifest registry. Plus MVP-tag reconciliation + config-versioning (config_version distinct from
  code semver). ⑬–⑱ ALL HARD-BLOCK G4 --apply.
status: partial
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [deployment-api, deployment-ui, execution-service, instruments-service, strategy-service, unified-trading-library]
scope: [engineer, admin]
tags: [audit, migration, manifest, canonicalisation, mvp, single-walk, data-correctness, verification]
related:
  - plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md
  - plans/active/mvp_scope_catalogue_tagging_2026_06_08.md
  - plans/audit/instructions/canonical_form_cross_service_audit_checklist.md
created: 2026-06-10
audited_scope:
  migration orphan-safety + beta-manifest goalpost preview + verified-delete gate + data-sizing + schema-attribute
  completeness + MVP-tag/config-versioning reconciliation (the "migrate once, no v10" verification harness)
date: "2026-06-10"
auditor: ikennaigboaka [slot-3·laptop]
parent_epic: infrastructure_master
severity: P0
resulting_plan:
lib_version:
doc_versions_checked:
type: analysis
epic: manifest_master
parent_plan: active/master_data_canonicalisation_migration_catalogue_2026_06_07.md
source:
  [
    operator 2026-06-10 ("worried about GCS orphans after migration; want to check everything moved; dry-run dumped to a
    different place = a v9-beta manifest we can hook data-status/deployment-api/UI to in dev to see the goalposts;
    delete only paths that are in the manifest; re-audit read/write paths; know data size for download planning; migrate
    once — no v10 because we missed an attribute"),
    'operator 2026-06-10 ("MVP tag to the catalogues (instrument/strategy/features/models/execution config); data-status
    MVP tick; instrument config like the sports-leagues / prediction-markets filter, everything-or-nothing at the family
    grain; config versioning as distinct from code versioning")',
  ]
priority: P0
---

# AUDIT — "Migrate once, never need a v10" verification harness

> **Read this with `master_data_canonicalisation_migration_catalogue_2026_06_07.md` open.** That plan is the
> coordinator; its **①–⑫ pre-apply audit** is mature and already GREEN per-AG (cefi/sports/prediction dry-run-green;
> defi/tradfi in flight). This audit does **not** re-open ①–⑫. It identifies the **five verification concerns the
> operator raised that ①–⑫ does not cover**, specifies them as points **⑬–⑰ + a G4.5 cleanup gate**, and reconciles the
> MVP-tag / config asks against the **already-shipped** `mvp_scope` work. Goal: when G4 `--apply` runs, we can _prove_
> nothing was orphaned, lost, or schema-truncated — so we move to strategy/features/ML/execution without a manifest v10.

---

## 0. TL;DR — what's already covered vs. the real gaps

The migration machinery is far more complete than the operator's framing assumes. Mapping the eight asks:

| #   | Operator ask                                                                                             | Status                             | Where                                                                                                        |
| --- | -------------------------------------------------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| 1   | Re-audit read/write paths use the right path                                                             | ✅ **COVERED**                     | ①–⑫ point **⑤** (every reader PREFIX-matches `pipeline_mode=batch_*/`; `rg`→0 coarse-exact hits)             |
| 2   | Rollback / safety if migration wrong                                                                     | ✅ **COVERED**                     | point **⑫** (`_index/snapshots/pre_migration_2026_06_08.parquet`, drain done 2026-06-08)                     |
| 3   | Batch data == live data after migration                                                                  | ✅ **COVERED**                     | point **⑪** (batch=live symmetry keystone)                                                                   |
| 4   | Honest 4-state, no silent placeholders                                                                   | ✅ **COVERED**                     | points **③④**                                                                                                |
| 5   | **Orphan audit (GCS object → manifest); do we need them?**                                               | 🔴 **GAP**                         | no GCS→manifest scanner exists (only the _inverse_, phantom: manifest→GCS) → **⑬** below                     |
| 6   | **Dry-run dumped elsewhere = a renderable v9-beta manifest; hook data-status/deployment-api/UI in dev**  | 🔴 **GAP**                         | dry-runs emit verdicts/counts, not a loadable `_index` → **⑭** below                                         |
| 7   | **Delete only paths that exist in the manifest (genetic/script gate)**                                   | 🟡 **PARTIAL**                     | migration is copy-not-move; ⑫ is rollback but there is no _verified-delete_ of legacy twins → **G4.5** below |
| 8   | **Know the data size; pre-download to de-risk**                                                          | 🔴 **GAP**                         | nothing rolls bytes per AG×data_type×venue → **⑯** below                                                     |
| 9   | **Registry of all possible shard dynamics per AG (consolidation of the _possible_ manifest)**            | 🟡 **PARTIAL/SCATTERED**           | axis NAMES exist (`SHARD_AXIS_MATRIX`); value-domains scattered; no consolidated generator → **⑰** below     |
| 10  | **Run manifest where we have instruments but no MTDS data → seed denominator as `expected_unattempted`** | 🟡 **EXISTS, CeFi STUB**           | `enumerate_expected_universe.py` does this; **CeFi + Prediction are stubs** (now unblockable) → **⑱** below  |
| 11  | **Audit candle left/right edge-timestamp from external sources**                                         | 🟡 **SSOT EXISTS, make recurring** | `/codex/02-data/bar-boundary-candle-edge-convention.md` filed; add as standing check → **⑲** below           |
| 12  | **Make all of this RE-RUNNABLE post-migration (not one-shot)**                                           | 🔴 **GAP**                         | new points must fold into `canonical_form_cross_service_audit_checklist.md` → **CF-15…CF-21** (Durability §) |
| —   | **"No v10 because we missed an ATTRIBUTE"** (the deepest fear)                                           | 🔴 **GAP**                         | ⑧ checks _cell_ completeness, not _column/attribute_ completeness → **⑮** below                              |

**The honest read: the migration is correctness-safe; what's missing is the _provable-completeness + preview +
safe-cleanup_ layer.** That layer is cheap (one GCS walk powers ⑬, ⑮, ⑯ at once — respect single-walk discipline) and is
exactly what lets us stop worrying about a re-do.

---

## PART A — Migration verification & orphan safety

### ⑬ Orphan sweep (GCS object → manifest) — _answers "do we need those paths?"_

**Today only the inverse exists.** `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` (and the
`*_phantom_*` / `reconcile_*` family) detect **phantoms** = a manifest row claiming `captured` with **no** GCS object.
The operator's question is the **other direction**: a **GCS object with no manifest row = an ORPHAN**. **No tool does
this.** It must be built (it can reuse the reconciler's `prefix_tpls` + `list_blobs` threadpool machinery in reverse).

**The answer to "do we need them?" is not yes/no — it's a forced classifier.** Every object under a data bucket must
fall into **exactly one** of five classes. The migration is _provably complete_ only when class **(E)** is empty:

| Class                                                 | Definition                                                                                                   | Need it?                               | Action                                                                                                                                                                                                                                              |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **(A) Canonical + manifested**                        | v9-shape path, a manifest row resolves to it                                                                 | ✅ keep                                | none — this is the goal state                                                                                                                                                                                                                       |
| **(B) Legacy duplicate of an (A)**                    | old-shape path whose canonical twin exists in the new manifest **and is byte-identical** (crc32c match)      | ❌ redundant                           | **delete via G4.5** (the migration is copy-not-move, so these are the leftovers to clean)                                                                                                                                                           |
| **(C) Manifest infra**                                | `_index/`, `_index/per_vm/`, `_index/snapshots/`, `*.tmp`, `*.partial`, `_SUCCESS`                           | n/a                                    | **exclude** from orphan logic entirely                                                                                                                                                                                                              |
| **(C2) Non-data GCS paths** (operator add 2026-06-10) | VM logs, run artifacts, audit/sizing outputs, tarballs, terraform state, anything NOT a service-data parquet | ✅ keep, **but classify + understand** | **NEVER delete via this audit — separate treatment.** Still _enumerate and label_ them (which prefix, which producer, why) so the bucket is 100% accounted-for. "Not service data" ≠ "unknown" — an unlabelled non-data prefix is itself a finding. |
| **(D) Junk / superseded**                             | aborted/partial writes, retired schema versions, orphaned temp shards with no real rows                      | ❌                                     | **quarantine list → operator-approved delete pattern** (never auto-delete)                                                                                                                                                                          |
| **(E) Real data, NO manifest row**                    | parseable parquet, rows > 0, valid hive-key, but **nothing in the manifest points at it**                    | ✅ **WE NEED IT**                      | **this is the v10 you fear** — a silent write / a manifest-completeness bug. **Backfill `record_captured(...)`, do NOT delete.**                                                                                                                    |

> **Non-data paths are a first-class class, not "everything else" (operator 2026-06-10).** The sweep must produce a
> **prefix taxonomy** of the whole bucket: every top-level prefix → {service-data | manifest-infra | logs | run-artifact
> | terraform | tarball | unknown}. Deletion (G4.5) only ever touches class (B); (C)/(C2) are _understood and left_; (D)
> is operator-acked; (E) is a manifest hole to _fill_. The deliverable is "every byte in the bucket is in exactly one
> labelled class, and we can say why" — that is what makes "everything migrated" _provable_ rather than asserted.

> **This classifier IS the deliverable.** Run the orphan sweep, bucket every object into A–E, and the migration is done
> when **|E| = 0** and **|D|** is an operator-acked allowlist. Class **(E)** is precisely "we migrated the bytes but
> forgot to record them" — catching it now is what prevents a v10. Output: one parquet
> `_index/audit/orphan_sweep_<AG>_2026_06_xx.parquet` with
> `(uri, class, canonical_twin_uri, crc32c, row_count, reason)`.

**Bidirectional invariant (the real goalpost):** `phantom_count == 0` (⑫/reconciler) **AND** `orphan_class_E == 0` (⑬).
Phantom = manifest claims, GCS lacks. Orphan-E = GCS has, manifest lacks. Both zero ⇒ manifest ≡ GCS, exactly.

### ⑭ Beta-manifest preview — _the operator's "dump the dry-run somewhere and look at it"_

**Today's dry-runs print verdicts and counts; they do not emit a loadable `_index`.** The operator's idea is sharp and
cheap: have the migrator/rebuild dry-run **also write the would-be post-migration `_index` to a throwaway prefix**, then
point the existing (already env-configurable) data-status stack at it.

- **Producer**: add `--beta-manifest-out gs://<dev-bucket>/_index/availability_index.parquet` to the rebuild dry-run.
  Same code path, same v9 columns — it just writes the projected `_index` instead of (or in addition to) the summary.
  **No object is moved**; this is purely the manifest the operator would see _as if_ `--apply` had run.
- **Consumer (already works, no new code)**: `deployment-api` reads the consolidated `_index` from a bucket selected by
  `GCP_PROJECT_ID` + `DEPLOYMENT_ENV_SHORT` (prd/stg/dev); `deployment-ui` is stateless and just points at whichever
  API. So: drop the beta `_index` in the **dev** bucket, run `restart-deployment-stack.sh --api` with
  `DEPLOYMENT_ENV_SHORT=dev`, and the **data-status tab renders the post-migration goalposts visually** — coverage %,
  the 4-state breakdown, the drilldown — _before_ touching prod. Delete the dev `_index` afterward.
- **What this buys**: the operator literally _sees the goalposts_ (per-AG, per-data_type, per-venue coverage in the new
  shape) and can sign off on G4 against a picture, not a number. Run it per-AG; prod/staging untouched.

> Naming: call it **"v9 projected"** not "v9-beta" in code — `schema_version` is still 9; it's a _preview render_ of the
> v9 manifest, not a new schema version. (Avoids implying a v8.5/v9-beta schema that downstream would have to handle.)

### ⑮ Schema-attribute completeness freeze — _"no v10 because we missed an attribute"_

⑧ proves _cell_ completeness (catalogue ⊇ manifest present-set). It does **not** prove _column_ completeness — that
**every attribute the raw data physically carries** survives into the v9 row + the canonical parquet. That missed-column
case is the operator's deepest fear and is **not currently gated**. Add a one-time pre-apply check per AG×data_type:

1. Sample N recent source/legacy parquets per (AG, data_type, venue); union their **actual column set** (footer schema).
2. Diff against the v9 canonical contract (UAC schema for that data_type) + the manifest's recorded columns.
3. **Any source column not represented in the canonical target = a RED freeze.** Decide _now_, per column: carry it (add
   to the canonical schema **before** apply), or explicitly drop it with an operator-acked reason logged in the AG plan.
   **No silent truncation** — a dropped attribute discovered post-apply is the v10 trigger.

> This is the single highest-leverage addition. It is the difference between "the cells moved" and "every _byte of every
> attribute_ moved." Cheap: rides the same GCS walk as ⑬/⑯; touch the parquet footer, not the data.

### ⑯ Data-sizing rollup — _"know how much data, start pre-downloading"_

The ⑬ orphan walk already lists every object; `gcs_describe_object` already returns size. So **for free** on that walk,
roll up **bytes + object-count per (asset_group, data_type, venue, pipeline_mode)** → one
`_index/audit/data_sizing_<AG>.parquet`. Outputs the operator wants:

- Total corpus size per AG and per data_type → **download/storage planning** for the strategy/features/ML phase.
- The biggest cells (e.g. CeFi DERIBIT options trades) → pre-download candidates to de-risk the download side _now_,
  before strategy work depends on it.
- A before/after byte delta across the migration (copy-not-move means transient ~2× during the legacy-duplicate window;
  G4.5 reclaims it).

### ⑰ Possible-manifest registry (consolidated shard-dynamics SSOT + generator) — _operator add 2026-06-10_

> **Operator ask**: "a registry of all available shard dynamics per AG (venue, `data_type`, instrument_type, …) —
> effectively a consolidation of the possible manifest."

This is **foundational — logically UPSTREAM of ⑬/⑮/⑦** even though numbered later. A manifest is only auditable against
a _defined key-space_: ⑬ can only call a GCS object an "orphan" if its hive-key is outside the valid space; ⑮ needs the
authoritative column set; ⑦'s denominator needs the full could-exist space. Today that space is **real but scattered**
across three layers — the registry must _consolidate + generate_ from them, not redefine them:

| Layer of the space                                                               | Where it lives today                                                                                                                                                                             | State                                                         |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| **Axis names** (which columns are shard axes per service×AG)                     | `unified_api_contracts/registry/data_status_axis_matrix.py` — `SHARD_AXIS_MATRIX[(service, asset_group)]`                                                                                        | ✅ consolidated SSOT exists                                   |
| **Axis value-domains** (which venues / data_types / instrument_types can appear) | `registry/data_type_capability.py` (venue×data_type×instrument_type), `archetype_capability_matrix.py` (venues per AG), the IS catalogue (instruments), UAC league / prediction-group registries | 🟡 exists but **scattered**, not crossed into one enumeration |
| **Validity** (which combinations are legal)                                      | the `(instrument_type × data_type)` validity matrix (point ⑥) + `data_type_capability`                                                                                                           | ✅ exists                                                     |

**Deliverable — ONE canonical SSOT module, not a fourth scattered registry.** Add
`unified_api_contracts/registry/possible_manifest.py` exposing:

- `PossibleManifestSpec[asset_group]` — the authority object composing (importing, not re-declaring) the three existing
  layers: `SHARD_AXIS_MATRIX` (axis names) + `data_type_capability` / `archetype_capability_matrix` (value-domains) +
  the validity matrix (legal combos).
- `enumerate_possible_shard_keys(asset_group, *, catalogue) -> Iterator[ShardKey]` — crosses {axes × domains × validity
  × catalogue leaves} into the **complete set of valid shard keys** (the manifest as it _could maximally exist_).
- `is_valid_shard_key(asset_group, key) -> bool` + `canonical_path_templates(asset_group)` — the orphan validator + the
  path-shape SSOT.

**Canonical means the scattered re-derivations get DELETED and REDIRECTED here** (the "delete deprecated code" rule — no
parallel paths). Today four consumers each independently reach into the sub-registries and re-cross them:

| Consumer                                 | Today (scattered)                                            | After ⑰ (canonical)                                    |
| ---------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------ |
| `enumerate_expected_universe.py` (⑱)     | per-AG bespoke enumeration; CeFi/Prediction = STUB           | calls `enumerate_possible_shard_keys` → stubs fall out |
| `reconcile_phantom_manifest_rows_all.py` | hand-maintained `prefix_tpls` per AG (the Axis-10 drift bug) | derives from `canonical_path_templates`                |
| deployment-api denominator (⑦)           | re-derives genesis/launch/could-exist per consumer           | calls the registry                                     |
| orphan scan (⑬) + schema check (⑮)       | n/a (new)                                                    | consume the registry directly                          |

This is the part that makes the manifest _canonical, not scattered_: one module is the authority for "what could exist,"
every consumer reads it, and the per-consumer cross-products are removed. It is also the natural home to assert the axis
set is complete (no AG silently missing a dimension the data carries — composes with ⑮). **`SHARD_AXIS_MATRIX` and the
sub-registries stay** as the component inputs; ⑰ is the layer _above_ them (same pattern `archetype_capability_matrix`
already documents for itself) — it consolidates the _consumption surface_, it does not duplicate the taxonomy.

### ⑱ Catalogue-seeded denominator — _"run the manifest where we have instruments but zero MTDS data"_

> **Operator ask**: "run manifest for e.g. MTDS on something we have only instruments for (no MTDS data yet) — it
> populates the v9 denominator with everything as `expected_unattempted`, because we know the instruments exist, we just
> haven't tried to fetch them."

**This machinery EXISTS and is the right one** — `instruments-service/scripts/enumerate_expected_universe.py` does
exactly this: it enumerates the could-exist universe and writes `expected_unattempted` (via
`record_expected_empty(reason=EXPECTED_*)`) for every `(shard_key, day)` with no manifest row — driven by the IS
catalogue, **independent of whether MTDS fetched anything**. The 4-state denominator then reads as
`captured + empty + failed + expected_unattempted`, so a venue/`data_type` we've never attempted shows as a
fully-enumerated honest denominator, not as silently absent.

**The gap is coverage, and it lands squarely on slot-3 (CeFi):**

| AG             | Enumerator state (per script docstring)                                                                                    |
| -------------- | -------------------------------------------------------------------------------------------------------------------------- |
| TradFi         | ✅ FULL (calendar pre-skip)                                                                                                |
| DeFi           | ✅ FULL (chain genesis + protocol launch)                                                                                  |
| Sports         | ✅ FULL v2 (per-league from catalogue rollup)                                                                              |
| **CeFi**       | 🔴 **STUB** — "needs instruments-service catalog with per-instrument lifecycle (`available_from`/`available_to`/`expiry`)" |
| **Prediction** | 🔴 **STUB** — blocked on UAC `PREDICTION_GROUPS` registry                                                                  |

**The CeFi STUB is now UNBLOCKABLE**: `build_instrument_catalogue.py` shipped (2026-06-05) and provides exactly the
per-instrument lifecycle (`available_from`/`available_to`/`expiry`) the docstring says it was waiting on. So ⑱ for CeFi
= **"complete the CeFi enumerator using ⑰'s generator + the now-shipped catalogue"** — and it's the same root cause as
⑰: there was no consolidated generator crossing the catalogue with the valid `(venue, data_type, instrument_type)`
space. Do ⑰ once and the CeFi/Prediction enumerators fall out of it.

> **Cross-check against the master plan**: this overlaps `master_…catalogue` **G1-ENUM** (the v2 enumerator the plan
> already tracks, including the over-fan fix). Verify whether CeFi/Prediction enumerator-stub-completion is an _open_
> G1-ENUM todo; if yes, ⑱ just references it; if it fell through, ⑱ files it. **Do not double-implement** — grep
> `master_data_canonicalisation_migration_catalogue_2026_06_07.md` for G1-ENUM CeFi before writing a todo.

### ⑲ Candle edge-timestamp convention (left vs right label) — _operator add 2026-06-10_

> **Operator ask**: when candles come from external sources, audit whether they are **left-edge** (timestamp = bar
> _open_) or **right-edge** (timestamp = bar _close_) labelled. An issue/plan was already filed and may be fixed — but
> it must stay a **standing, re-runnable audit point**.

This already has a codex SSOT: **`/codex/02-data/bar-boundary-candle-edge-convention.md`** (+
`chart-candle-delivery-flow.md`). The audit point is: for **every external candle/OHLCV source** (per venue ×
timeframe), verify the ingested timestamp matches the canonical convention the SSOT mandates — a left/right-edge
mismatch silently shifts every bar by one interval (a `1h` bar mislabelled by edge is off by 60 min), which corrupts
every downstream feature/label/alignment **without ever failing a row-count or schema check**. It is invisible to ⑬/⑮
(the bytes and columns are all present and valid) — so it needs its own check:

1. Per external OHLCV source, confirm the adapter's documented edge convention against the SSOT.
2. Spot-check a known bar against an independent reference (e.g. a venue API call for a specific minute) to confirm the
   stored timestamp is the edge the SSOT says.
3. Confirm a single normalization point (no per-adapter drift) and that batch == live agree on the edge (composes with
   ⑪).

**Durable, not one-shot**: even if the filed issue is fixed today, a new source adapter can reintroduce the bug → this
belongs in the re-runnable audit instructions (CF-19 below), not just here.

### G4.5 — verified-delete cleanup gate (legacy twins) — _"only delete paths that are in the manifest"_

The migration is **copy-not-move** (per ②: "copy-not-move safe via rebuild dedup + migrate-before-rebuild"). So after a
green G4 apply, the **legacy-shape objects (class B) still exist** and must be cleaned — this is where the operator's
"only delete what's in the manifest" instinct is exactly right, and where a careless `gsutil rm` would be catastrophic.
Make the delete _genetically_ safe, not trust-based:

> **A legacy object is eligible for deletion ⟺ ALL of:**
>
> 1. its **canonical twin URI exists** in the post-apply `_index` (`capture_status=captured`), **and**
> 2. `gcs_describe_object(legacy).crc32c == gcs_describe_object(canonical).crc32c` (**content-identical**, not just
>    name-mapped), **and**
> 3. the legacy URI is **not itself a manifest-referenced path** (no row points at the old shape).

Anything failing (1)–(3) is **not** a class-B duplicate — it routes back to ⑬'s class (D)/(E) and is **never deleted by
this gate**. The crc32c check is the "genetic" guarantee the operator asked for: we delete a legacy copy only when we
can prove byte-for-byte that the canonical copy carries the same data _and_ the manifest knows about it. Implement as
`cleanup_legacy_twins_<AG>.py --dry-run|--apply` reading the ⑬ sweep output; `--apply` operator-gated like G4.

---

## PART B — MVP tag & config versioning

### B1. The MVP ask is ~50% already shipped — `mvp_scope_catalogue_tagging_2026_06_08.md`

Most of what the operator described **already exists or is planned**, and matches the operator's mental model exactly:

- ✅ **SHIPPED (Phase 1)**: `unified_api_contracts/canonical/crosscutting/mvp_scope.py` — an
  `is_mvp(asset_group, venue, instrument_type, data_type, *, base_ccy, league, market_group, source) -> bool`
  predicate + the `MVP_SCOPE` config + 56 tests (uac@d6e0775f). **It is rules-derived, not hardcoded** — exactly the
  operator's "we can't hardcode expiries" requirement. The grain is
  `(venue, instrument_type, data_type, [base_ccy/league/market_group])` = **everything-or-nothing at the family grain**
  (all expiries/strikes for an in-scope family; no per-strike filtering). _This is precisely the operator's "instrument
  config like the sports-leagues / prediction-markets filter."_
- 🔲 **OPEN (Phase 2)**: apply `is_mvp()` over the rolled-up instrument catalogue; **deployment-api
  `scope=mvp|could_exist|all` parameter**; **deployment-ui MVP toggle** (the operator's "MVP tick in data status") — L2
  playwright-gated.
- 🔲 **OPEN (Phase 3)**: `mvp_features` / `mvp_strategies` / `mvp_models` sections (features/strategy/model catalogues).

**So the operator's MVP ask is mostly "land Phases 2–3 of an existing plan," not net-new design.** The catalogues it
hangs off already exist: instrument (`build_instrument_catalogue.py` + `enumerate_expected_universe.py`), features
(`features_service/.../registry.py`, 1,382 specs/34 groups), strategy (archetype registry), model (UTL model_registry).
The sports-leagues config (`LEAGUE_CLASSIFICATION_DATA` in UAC) and prediction market-group config already are the
template — `mvp_scope.py` generalises them to one config across all five AGs.

### B1a. Execution config = a capability/compatibility PRE-FLIGHT (audit-and-enhance — NOT a new MVP catalogue)

> **Operator clarification 2026-06-10**: execution config is not "the venues the MVP strategies trade" — it's the
> **capability/compatibility matrix** that stops us configuring something physically impossible. Three dimensions: (i)
> **venue → possible instructions** (can you `lend` on aave_v3? can you `bet` here?); (ii) **market-data granularity →
> matchability** (a venue with only `ohlcv_1m` can't support tick-fidelity matching that needs L2/trades); (iii)
> **archetype → allowed actions** (`carry_staked_basis` can't place a bet; a betting-specific algo can't run on a
> staked-basis archetype). The point is **execution pre-flight that rejects incompatible configs**.

**This is ~80% already built — audit and enhance, do not rebuild.** Confirmed existing infrastructure:

- **Archetype → allowed actions** (dimension iii): `unified_api_contracts.internal.architecture_v2.archetype_capability`
  maps **archetype → (asset_group, instrument_type) cells with SUPPORTED / PARTIAL / BLOCKED**. _"staked_basis can't
  bet" is literally a BLOCKED cell here._ Enforced in execution by `slashing_archetype_gate.py` and
  `strategy-service/.../risk/v2/preflight.py`.
- **Venue → possible actions + fill/margin/settlement** (dimension i):
  `unified_api_contracts/registry/archetype_capability_matrix.py` — per-asset_group ontology (which venues serve the
  group, FillModel / MarginModel / SettlementModel / liquidation, `has_funding` / `has_event_settlement`). Plus the DeFi
  capability declarations (`registry/capability_declarations/_defi.py`, per CLAUDE.md).
- **Market-data granularity per venue** (dimension ii): `unified_api_contracts/registry/data_type_capability.py` — per
  `(venue, data_type, instrument_type)` with `batch_capable`, the granularity vocabulary (`trades`, `book_snapshot_5`,
  `derivative_ticker`, `futures_chain`, `ohlcv_1m`…), keyed to the **manifest shard columns**.
- **Execution-side gates**: `execution-service/.../engine/validation/data_availability_validator.py`,
  `engine/preflight.py`, `wallet_preflight_registry.py`;
  `unified-trading-library/.../config_interface/execution_config_schema.py` (the typed execution-config schema).

**The genuine gap = the CROSS-LINK, not the pieces.** Each dimension is encoded separately; what's missing is a single
composite pre-flight that asserts a proposed `(archetype × venue × instrument_type × required-matching-fidelity)` is
**jointly satisfiable**:

1. the archetype is **SUPPORTED** (not BLOCKED) on that `(asset_group, instrument_type)` cell, **and**
2. the venue serves the **action** the archetype needs (lend / stake / bet / perp-short), **and**
3. the **market-data granularity we actually have** (from `data_type_capability` ∩ the manifest's captured cells) is
   sufficient for the **matching fidelity** the archetype's actions require — i.e. don't run a tick-fill strategy on a
   venue×instrument where we only captured `ohlcv_1m`.

Point 3 is the part most likely _not_ yet wired: `data_type_capability` says what data _exists_; it isn't yet joined to
"therefore this matching/execution fidelity is/ isn't possible." **Action: a focused audit of the four modules above →
add the composite `assert_execution_config_compatible(...)` pre-flight (or extend `engine/preflight.py`) closing the
cross-link.** File as a todo under the execution epic, NOT the data-migration plan. This composes with — and consumes —
the migration's honest manifest: pre-flight reads the **post-migration 4-state** to know what granularity is actually
captured per venue, so it can only be done _after_ G4. (This is a natural Part-A→Part-B bridge: the migration makes
granularity honest; the execution pre-flight consumes it.)

### B2. "Code that understands we want ALL features" — already the design

The operator's "we'd have to write code so it understands we want all features… everything or nothing for that
`data_type`/venue/instrument_type" is **exactly** the family-grain `is_mvp()` + the catalogue enumerator: the config
declares the family (e.g. cefi×BINANCE×PERPETUAL×`funding_rate` is MVP), and `enumerate_expected_universe.py` populates
the leaves (every live expiry/strike for that family, from the per-date catalogue rollup — never hardcoded). Nothing new
to invent; it's Phase-2 wiring.

### B3. Config versioning — the one genuinely net-new (and small) concept

**Confirmed gap**: there is no concept of config versioning distinct from code/semver today. Features have
`formula_version` (a _formula_ version, baked into the GCS partition key) — that's the operator's "features code change
is a major change, already a thing." But **pure config** (which families are MVP, which leagues, which market-groups)
has **no independent version**. The operator's instinct is right and worth codifying:

- **Config change ≠ code change.** Changing `MVP_SCOPE` (add a venue to MVP) is data, not logic — it should **not**
  force a repo semver bump.
- **But it must be _tracked_** so data-status/coverage history is interpretable ("coverage dropped because we _added_
  scope, not because data regressed"). Lightweight proposal: a monotonic `config_version` integer + content-hash stamped
  on the `MVP_SCOPE` config (and the sports/prediction configs), surfaced in the manifest/data-status response so a
  coverage delta can be attributed to a scope change vs. a data change. **No GCS partition key** (unlike
  formula_version) — config versioning is metadata, not a path axis.
- **Decision needed**: is `config_version` a single global int, or per-config (one for MVP_SCOPE, one for leagues, one
  for prediction markets)? Recommend **per-config** (they change independently).

---

## Durability — these become RE-RUNNABLE audit instructions, not a one-shot (operator 2026-06-10)

> **Operator**: everything added here that isn't already in the audit-instruction set must be **augmented into it**, so
> that after the migration is complete we can still _re-run_ the audit. Format it to audit a corpus that has _already_
> migrated to v9 — some points (orphans, catalogues/registries, non-data-path classification, candle edge) stand
> permanently.

The everlasting SSOT is **`plans/audit/instructions/canonical_form_cross_service_audit_checklist.md`** (CF-1…CF-14 today
— explicitly "re-running the per-service audits proves the whole pipeline is in canonical form; an item with no owning
audit is a review-blocking coverage gap"). Every new point here is added as **CF-15…CF-21**, each mapped to an owning
per-service audit-instruction file, written in **steady-state form** ("the corpus is v9; assert X holds") not
migration-form ("migrate X to v9"):

| New CF    | Audit point (from this doc)                                                                                                                         | Owning instruction file                                       |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| **CF-15** | ⑰ possible-manifest registry is the canonical could-exist SSOT; consumers read it, no per-consumer re-derivation                                    | `manifest_master_audit_instructions.md`                       |
| **CF-16** | ⑱ denominator seeds from IS catalogue even at zero captured data (all-`expected_unattempted`); CeFi/Prediction FULL                                 | `instruments_master_audit_instructions.md` + per-AG           |
| **CF-17** | ⑬+⑯ bidirectional manifest≡GCS (phantom==0 ∧ orphan-E==0) + **full bucket prefix taxonomy** (every byte labelled incl. non-data/logs) + byte sizing | `manifest_master_audit_instructions.md` + each AG             |
| **CF-18** | ⑮ schema-attribute completeness — no source column silently dropped vs the v9 canonical contract                                                    | `mtds_mdps_master_audit_instructions.md` + per-AG             |
| **CF-19** | ⑲ candle edge-timestamp convention (left/right) per external OHLCV source matches `bar-boundary-candle-edge-convention.md`                          | `mtds_mdps_master_audit_instructions.md`                      |
| **CF-20** | ⑭ data-status/deployment-UI render the v9 manifest's coverage + denominator (could-exist) correctly from a clean read                               | `deployment_and_user_management_master_audit_instructions.md` |
| **CF-21** | G4.5 verified-delete safety — a legacy/duplicate object is deleted only if crc32c-identical to an in-manifest canonical twin                        | `manifest_master_audit_instructions.md`                       |

This is a **plan phase (V7 below), owned cross-cutting** — the migration is not "done" until the audit it passed is
_encoded as a re-runnable instruction_, so a future regression (a new adapter reintroducing the candle-edge bug, a new
writer creating orphans) is caught by re-running CF-1…CF-21 rather than rediscovered from scratch.

## Goalposts — the acceptance criteria for "migrate once, done"

Per AG, before we call the data layer finished and move to strategy/features/ML/execution. **Operator decision
2026-06-10: ⑬–⑱ ALL HARD-BLOCK G4 `--apply`** (no advisory tier — the cost is one shared GCS walk + the registry wiring
per AG on the pre-apply critical path, which is acceptable to guarantee "migrate once"):

1. **①–⑫ GREEN** (existing — most already are).
2. **⑰ possible-manifest registry [FOUNDATIONAL, HARD-BLOCK]**: the per-AG valid shard-key generator exists and is the
   SSOT ⑬/⑮/⑦/⑱ consume. _(Upstream of the rest — build first.)_
3. **⑱ catalogue-seeded denominator [HARD-BLOCK]**: CeFi + Prediction enumerators completed; a zero-data venue/data_type
   shows a fully-enumerated `expected_unattempted` denominator from the IS catalogue.
4. **⑬ orphan sweep [HARD-BLOCK]**: `orphan_class_E == 0` (no real data without a manifest row) **AND**
   `phantom_count == 0` (bidirectional manifest≡GCS), validated against ⑰'s key-space.
5. **⑭ beta preview [HARD-BLOCK]**: the projected v9 `_index` renders in dev data-status/UI; operator eyeballs the
   goalposts + signs off (the sign-off is the gate).
6. **⑮ schema-attribute completeness [HARD-BLOCK]**: every source column either carried into v9 or
   operator-acked-dropped; **zero silent truncations**.
7. **⑯ sizing [HARD-BLOCK]**: per-AG byte/object rollup published; biggest cells flagged for pre-download. _(Cheap —
   rides the ⑬ walk; hard-blocking it just means "the rollup must have been produced," not a quality bar.)_
8. **⑲ candle edge-timestamp [HARD-BLOCK]**: every external OHLCV source's left/right-edge label verified against the
   SSOT.
9. **G4 `--apply`** (operator-gated) → re-run ⑬ post-apply (must still be E==0).
10. **G4.5 verified-delete**: legacy twins deleted only via crc32c+manifest gate; post-cleanup byte delta matches
    expectation.
11. **CF-15…CF-21 encoded [DURABILITY GATE]**: every new point added to
    `canonical_form_cross_service_audit_checklist.md` in re-runnable v9-state form with an owning instruction file. The
    migration is not "done" until its audit is _re-runnable_.
12. **MVP**: Phase-2 deployment-api `scope=` + UI tick live; coverage reads ~100% with MVP-ON (the real readiness
    signal).

---

## Gap → remediation routing (where each becomes todos)

- **⑬/⑭/⑮/⑯/⑰/⑱ + G4.5** → add as a registered sub-plan under the master coordinator
  (`master_data_canonicalisation_migration_catalogue_2026_06_07.md`), e.g.
  `migration_verification_orphan_safety_2026_06_10.md` with `parent_epic: epics/manifest_master.md` — these are cross-AG
  verification tooling, run per-AG by slots 2–6 before their G4. **Single-walk discipline**: ⑬+⑮+⑯ share ONE GCS walk
  per AG. **Build order**: ⑰ (registry) is foundational → ⑱ (enumerators) + ⑬ (orphan validity) + ⑮ (columns) consume
  it. **⑱ overlaps master-plan G1-ENUM** — grep before filing (don't double-implement the CeFi/Prediction enumerator).
- **MVP Phases 2–3** → already in `mvp_scope_catalogue_tagging_2026_06_08.md`; nothing to file, just schedule.
- **config_version concept** → small design todo; recommend folding into the mvp_scope plan (it's the first
  config-as-data consumer) rather than a standalone plan.
- **Execution-config compatibility pre-flight (§B1a)** → audit-and-enhance todo under the **execution epic** (not the
  data plan); **post-G4** since it consumes the post-migration honest granularity. Audit the four existing capability
  modules → add the composite `assert_execution_config_compatible(...)` cross-link gate.

## Open decisions for the operator

1. **Class-D deletes**: auto-delete on an approved junk pattern allowlist, or always operator-confirm? (Recommend:
   allowlist for `*.tmp/*.partial/_SUCCESS`, operator-confirm for everything else.)
2. **Beta preview scope**: dev bucket in the _prod_ project (`central-element-323112-dev-*`) or a separate dev project?
   (Recommend: dev prefix in prod project — simplest, no cross-project IAM.)
3. **config_version**: global int vs per-config. (Recommend: per-config — MVP_SCOPE, leagues, prediction-markets change
   independently.)

### Resolved 2026-06-10

- ✅ **Gating**: ⑬–⑯ **ALL HARD-BLOCK** G4 `--apply` (operator). Goalposts §2–5 updated.
- ✅ **Execution config**: NOT a 6th MVP catalogue — it's the **capability/compatibility pre-flight** (§B1a). Audit +
  enhance the existing `archetype_capability` / `archetype_capability_matrix` / `data_type_capability` / execution
  preflight stack; the gap is the composite cross-link (granularity→matchability). Filed under the execution epic,
  post-G4.

---

## Appendix: Historical Progress Log (archived 2026-07-24, plan line-cap remediation split)

> **Provenance**: this appendix is the **full verbatim Progress Log** section (originally "## Progress Log") from
> `plans/active/migration_verification_orphan_safety_2026_06_10.md`, archived here as part of the 2026-07-24 plan
> line-cap remediation (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 18 / bucket (d)). The parent
> plan's own V7 todos already fold the durable CF-15…CF-21 protocol into
> `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md`, so this plan had become a **narrative
> citation, not the mechanism SSOT** — its 1024-line Progress Log is preserved here in full for archaeology, while the
> live plan file was trimmed to its still-relevant structure (banners, role/gating, the closed V0–V7 phased DAG, success
> criteria) and unlocked.
>
> **Still-open items at archive time were NOT dropped** — each of the 15 genuinely open `- [ ]` todos found embedded in
> this Progress Log (plus 3 more found in the parent's main body, outside this section) was forked verbatim into one of
> 4 small residual plans, grouped by topic:
>
> - `plans/active/prediction_cqg_residual_2026_07_24.md` (2 todos — prediction cqg-classifier coverage)
> - `plans/active/sports_prelaunch_cf5_verify_residual_2026_07_24.md` (2 todos — sports pre-launch-window + CF-5 relabel
>   land/verify)
> - `plans/active/defi_venue_lst_rates_residual_2026_07_24.md` (2 todos — defi venue hygiene + lst-rates aggregation)
> - `plans/active/infra_ops_residual_migration_verification_2026_07_24.md` (9 todos — the remaining infra/ops/audit
>   tail)
>
> Below, each forked item is replaced inline with a **`[FORKED 2026-07-24 → ...]`** pointer (no longer a live checkbox —
> it is tracked going forward in its child plan) quoting its own opening words for identification; everything else in
> this Progress Log — narrative, evidence, shas, and the 9 already-CLOSED `- [x]` items embedded in it — is preserved
> completely unmodified below.

## Progress Log

- 2026-06-17 (autonomous re-verification dispatch — the TWO v9-migration code prerequisites, at current HEAD) — a fresh
  dispatch to "complete the two code prereqs before the v9 `--apply`" found **both already shipped + merged + flipped**
  (the R-wave + 2026-06-16 Half-B tail did them); re-verified at current `live-defi-rollout` HEAD rather than redoing
  (would be a same-repo race + duplicate work). Rule-9 verdict, each item's sha:
  1. **R2-schema / CF-18 (UAC P0)** — **unified-api-contracts@715e2ed** (ancestor-of-HEAD ✓).
     `_schema_spec_{defi, prediction,tradfi}.py` + `schema_spec.py` + `test_schema_spec_completeness.py` all present;
     completeness suite **84/84 GREEN** (registry round-trip + alias hygiene + per-cell source-column completeness +
     previously-RED pins) → CF-18 is **0-RED at the contract level**. All 11 polymarket trades cols carried via
     `ColumnSpec.source_aliases`; defi rewards/risk_params/utilization + tradfi/trades SchemaSpecs added. No code change
     needed.
  2. **instrument_type per-type v9 column / Audit §K (IS P1)** — **instruments-service@b475ae8** (ancestor-of-HEAD ✓).
     Writer `engine/orchestrator/writers.py` `_derive_instrument_type()` stamps the REAL single type per venue×date
     shard (blank-when-mixed/absent — honest absence, never fabricated) at the non-sports `record_captured` call;
     `scripts/migrate_instruments_store_v9.py` carries `instrument_type` as a v9 manifest column with the venue-suffix
     backfill (`_backfill_instrument_type`) on the EXISTING single migration walk (single-walk discipline respected). No
     code change needed. **No forced tradeoffs, no impossibilities** — both prerequisites are GREEN at HEAD and the v9
     `--apply` is unblocked on the schema-completeness + instrument_type-column axes. (PARKED out-of-scope as
     dispatched: G4 `--apply`, VM runs, deletes.)

- 2026-06-16 (autonomous Half-B tail — UAC/IS/deployment-api vertical, FINAL — all 6 items DONE) — the schema /
  config_version / catalogue tail of A2 (the separate agent's mtds/mdps/PM-chore vertical ran concurrently and is
  untouched here). **All six dispatched items shipped QG-green + flipped; nothing DEFERRED/BLOCKED.** Final tally (every
  item's sha + verdict, rule-9):
  1. **R2-schema (UAC P0)** — VERIFIED already shipped **uac@715e2ed** (all 11 polymarket cols via `source_aliases` +
     defi rewards/risk_params/utilization + tradfi/trades; `test_schema_spec_completeness.py` GREEN → CF-18 0-RED at the
     contract level). Flipped.
  2. **config_version leagues+prediction (UAC P1)** — **uac@176f227**: shared `config_versioning.py` (ConfigDescriptor +
     deterministic `canonical_config_repr` + `compute_config_content_hash`), MVP_SCOPE refactored onto it,
     `sports_leagues_config_descriptor()` (hashes `LEAGUE_REGISTRY`) + `prediction_markets_config_descriptor()` (hashes
     `PredictionMarketCategory`+`_DEFAULT_RULES`), root-exported, 12 tests, UAC QG green 217s.
  3. **catalogue-reader E5 repoint (UTL P1)** — **utl@94775d05**: repointed to canonical `{env}/catalog.parquet`
     lifecycle roll-up (old `all.parquet` confirmed GONE from prod GCS; new object verified present — cefi 220,222 /
     defi 6,853 rows). Alias-aware → 48 reader tests stay green, UTL QG 115s. CatalogueBuilder retained (live IS
     builder). P2 CeFi symbol-format follow-up captured (todo above).
  4. **deployment-api scope + config_version triples (P1)** — **deployment-api@3390c98**: `scope=mvp|could_exist|all`
     param + `config_versions` triples on venue-year-coverage, helpers in new `_coverage_scope.py`, parity test
     (monotonicity + descriptor match). QG green.
  5. **deployment-api stale-read + CeFi UNION FLAG-1 (P1)** — **deployment-api@3390c98** (same ship): moved to
     stale-tolerant `read_manifest_index` (empty-live→`_index` fallback) + cell-grain source-UNION + `source_breakdown`.
  6. **IS R5-fix-3 + MVP catalogue view + instrument_type v9 col (P1)** — **instruments-service@b475ae8**: R5-fix-3 was
     NOT already correct (`_sports_ref_source("footystats_odds")` returned `odds_api` → `MissingSourceError`; fixed to
     `footystats` via a scoped override + corrected the 2 wrong tests); `mvp` column on `catalog.parquet` via UAC
     `is_mvp`; `instrument_type` populated v9 column riding the EXISTING v9 migrator (single-walk respected; writer
     stamps real type, blank-when-mixed, never fabricated). QG green, 164 tests. **Forced-tradeoff decisions (rule 1):**
     (a) CatalogueBuilder NOT deleted — it is live-wired in the IS orchestrator and is a different artifact from the
     lifecycle roll-up (documented, not a leftover). (b) The CeFi catalogue symbol-format mismatch (ccxt id vs bare
     manifest symbol) is genuinely separate normalisation work → captured as a P2 follow-up todo, not silently dropped
     (the reader's best-effort None→SOURCE_RETURNED_ZERO keeps it safe meanwhile). (c) `instrument_type` is left "" for
     venues without a derivable suffix (honest absence, not fabricated). **No genuine impossibilities.**
     Concurrent-safety: protected the peer agent's uncommitted PM WIP throughout (committed only my own files; unstaged
     foreign deletions before each flip commit). All 6 codeshas verified ancestor-of `origin/LDR`; Tier-C drain (≤30min)
     promotes each LDR→staging (v2-gated). Parallelised items 4-6 to two sub-agents to protect context.

- 2026-06-16 (autonomous Half-B tail — UAC vertical, ticks 1-2) — driving the UAC + IS + deployment-api schema/
  config_version/catalogue tail of A2 (separate agent owns mtds/mdps/PM-chores). **Item 1 (R2-schema) VERIFIED done +
  flipped** — it was already shipped at **uac@715e2ed** (CF-18 citadel column-carry: all 11 polymarket cols via
  `source_aliases` + defi rewards/risk_params/utilization + tradfi/trades + the full RED list); the
  `test_schema_spec_completeness.py` suite (155 tests incl. it) is GREEN, so the contract-level CF-18 is 0-RED. **Item 2
  (config_version for sports-leagues + prediction-markets) SHIPPED — uac@176f227** (Tier-C drain ≤30min → staging):
  extracted the generic `config_versioning.py` (ConfigDescriptor + sorted/deterministic `canonical_config_repr` +
  `compute_config_content_hash`), refactored MVP_SCOPE onto it (hash unchanged), added per-config
  version+hash+descriptor to `league_data.py` (hashes `LEAGUE_REGISTRY`) and `prediction_mapping.py` (hashes
  `PredictionMarketCategory` + `_DEFAULT_RULES`), all root-exported, with `test_config_versioning.py` (12 tests; 3
  hashes independently distinct). Full UAC QG green 217s. UAC is back CLEAN (T0 dirty window closed). **Item 3 (UTL E5
  catalogue-reader repoint) SHIPPED — utl@94775d05** (see the E5 ✅ todo above): repointed to the canonical
  `{env}/catalog.parquet` lifecycle roll-up (old `all.parquet` confirmed gone from prod GCS), alias-aware so legacy
  fixtures stay green; 48 reader tests + full UTL QG green 115s; CatalogueBuilder retained (live IS-orchestrator
  builder); surfaced a P2 CeFi symbol-format follow-up. Both T0 repos (UAC+UTL) now CLEAN. NEXT: deployment-api items
  4-5 + IS item 6 (no T0 dirty-dep concern).

- 2026-06-16 (decision 338 — cqg classifier COMPLETE; pass 2 shipped, uac@e0035fd + uac@8e3108d) — operator gave full
  granular direction; encoded all of it. **29 groups + OTHER → ~103 groups + OTHER + MISC_NOVELTY.** Three ships, all
  QG-green, all seeded in the 4 required places (enum + metadata + `PREDICTION_GROUPS` + classifier map); parity tests
  green. Sub-type detection lives in the projection layer (`classifiers.py`), NOT the taxonomy — `CLASSIFIER_VERSION`
  bumped `2026-05-23.3 → 2026-06-16.3` (lever for reclassifying existing OTHER rows).
  - **Pass 2A (uac@e0035fd):** crypto **PRICE_RANGE** split out for 12 coins (BTC/ETH **retrofitted** — "between $X-$Y"/
    multistrike no longer mislabeled UP_DOWN); political **TRUMP_APPROVAL_RATING / \_STATEMENTS / \_EXEC_ORDER** +
    **ELON_TWEET_COUNT / \_STATEMENTS / \_NET_WORTH**; geo **GEO_ISRAEL_IRAN / GEO_RUSSIA_UKRAINE / GEO_OTHER_BY_DATE**
    (conflict-token-gated, doesn't swallow intl elections); **BOX_OFFICE_OPENING_WEEKEND** (category-agnostic — movie
    titles are MISC-tagged); **GOLD/SILVER/CRUDE_OIL_PRICE_LEVEL**; **MISC_NOVELTY** (genuinely-uncategorised → explicit
    residual; OTHER stops being the silent ~80% bucket).
  - **Pass 2B (uac@8e3108d):** sports _*SPORTS*{LEAGUE}_{BETTYPE}** — 30 groups / 17 leagues. Bet-type (WINNER→MATCH /
    SPREAD / TOTAL / NRFI / F1 GP_WINNER / CONSTRUCTOR) from the slug; **per-league MATCH fallback\*\* → every
    known-league market groups (never silent OTHER). Matches the operator's "league x fixture x market-type" model
    (league + bet-type in the group; fixture = the recurring market_id instance).
  - **Fleet unblock:** the staging-backmerge bringing UAC 0.15.0 also landed a foreign
    `databento_classifier.py::classify_databento_symbol` at **331L** → codex-compliance ratchet (3 > 2) was failing
    **every** UAC LDR ship. Refactored to extract `_classify_databento_combo` + `_classify_databento_option`
    (331L→154L), behavior preserved (54 tests). "Fix CI in real time."
  - **Known residual (honest):** football "will-{team}-win" WITHOUT a league marker in slug/event_slug tags MISC (no
    team→league registry in the taxonomy) → MISC_NOVELTY; league-prefixed/event-slug'd football DOES route. A
    team→league table is a follow-up if a consumer needs it.
  - **249-b:** the cqg classifier is now richly populated → unblocked at the classifier level; reclassification
    (hash-diff) can run; remaining is materialisation + the operator-gated G4 apply.

- 2026-06-16 (autonomous run, FINAL — tail-cleanup complete) — **5 of 6 dispatch sub-items SHIPPED + flipped; 346
  verified-done in code + PRESERVED to a recoverable wip branch (lands on the next clean-dep window).** Final tally:
  **Item 4** STEP 5.92 collision → pm@3be7eb595 ✅ · **Item 5** V4 fleet-gate blast-radius VERIFIED green on 3 consumers
  - 2 libraries ✅ · **Item 1 / 249-a** prediction catalogue conditionId grain → is@c100834 + prod catalogue promoted
    0→668,384 rows ✅ · **Item 3 / 222-followup** 7 unsourceable lending re-phased (uac@6c74eaf) + 5 LST corrected as a
    false-signal (real data in the `lst-rates` bucket) + filed the lst-rates-aggregation follow-up ✅ · **Item 2a /
    384** sports 6,869 blank-capture_status phantom-drop → is@8b3c7ef ✅ · **Item 2b / 346** sports CF-5 `trades`
    case-fix — CODE DONE + QG-green + tested + verified, **preserved on `origin/wip-preserve/mtds-346-cf5-trades`
    (mtds@d0a15a3)** after 3 quickmerge retries blocked by a live sibling's continuous fleet manifest-regen (dirty
    deps); lands via the one-line quickmerge in the 346 todo above the instant deps are clean. All shipped changes
    QG-green + drift-clean. **Operator-reserved (untouched, per dispatch):** G4 `--apply`, V6 eyeball, decisions
    338 + 424. The destructive `--apply` legs of 384/346 execute at the operator-gated sports G4 (code produces 0-blank
    / correctly-relabeled output). Journaling this final entry via a throwaway worktree off origin/LDR — the shared PM
    clone is mid fleet manifest-regen by a sibling (canonical-dependency-manifest/workspace-manifest/master-plan churn,
    preserved in its `stash@{0}`), deliberately left untouched.

- 2026-06-16 (decision 338 — cqg classifier IMPROVED + shipped, uac@d52217f) — operator chose "improve the classifier
  first"; this is the high-confidence tranche (faithful pattern extensions; judgment-heavy genres deferred to the
  operator, below). **Shipped (QG-green 213s, 32/32 prediction unit tests):**
  - **10 alt-coin `{COIN}_UP_DOWN_DAILY`** (SOL/XRP/DOGE/BNB/ADA/AVAX/LINK/LTC/SUI/HYPE) — exact mirror of BTC/ETH DAILY
    (data-grounded: observed alt markets are range_bracket/monthly → DAILY-fallback; intraday/hourly NOT pre-built).
    Closes the two biggest OTHER buckets (SOL ~4,056 + XRP ~3,574 shards).
  - **FED dead-key bug FIX** — `(MACRO,"FED_RATE")` never matched (taxonomy emits underlying `FED_FUNDS`) → every FED
    market fell to OTHER; corrected to `FED_FUNDS` → routes to `FED_RATE_DECISION_PER_FOMC`.
  - **7 macro groups** — `UNEMPLOYMENT_RATE_PER_MONTH`, `NONFARM_PAYROLLS_PER_MONTH`, `GDP_PRINT_PER_QUARTER`,
    `PPI_PRINT_PER_MONTH`, `PCE_PRINT_PER_MONTH`, `TREASURY_YIELD_PER_PRINT`, `CRYPTO_FEAR_GREED_INDEX`.
  - **1 weather group** — `WEATHER_TEMP_DAILY` (London/NYC daily-temp factories, ~2,276 shards; both range_bracket +
    binary variants).
  - **`CLASSIFIER_VERSION` 2026-05-23.3 → 2026-06-16.1** → `CLASSIFIER_STABILITY_HASH` flips → existing OTHER rows get
    flagged for reclassification into the new groups (the lever, since the cqg projection maps in `classifiers.py` are
    not stability-hash inputs).
  - Each group seeded in all 4 required places (enum `CanonicalQuestionGroup` + `CANONICAL_GROUP_METADATA` +
    `honest_coverage.PREDICTION_GROUPS` cluster registry + `classifiers.py` map); parity tests confirm no omission.
    Files: `canonical/domain/predictions/canonical_groups.py` + `classifiers.py`,
    `canonical/crosscutting/honest_coverage.py`, `internal/schemas/_prediction_market_taxonomy.py`, +
    `tests/unit/test_predictions_canonical_groups.py`.
  - **249-b (cqg-grain catalogue) is now UNBLOCKED at the classifier level for these genres** — the reclassification
    pass (hash-diff) + 249-b catalogue can proceed for the covered groups; the residual OTHER is the operator-deferred
    list below.
  - **DEFERRED to operator (genuine judgment calls, NOT mechanical — surfaced, not auto-decided):** (1) crypto
    PRICE-RANGE/multistrike split (currently folds into `_UP_DOWN_DAILY` like BTC/ETH — needs a market-subtype
    distinction + a retrofit-BTC/ETH decision); (2) sports per-fixture grain (per-league vs per-market-type
    winner/spread/total/NRFI); (3) political-figure granularity (TRUMP_APPROVAL vs STATEMENTS vs EXEC_ORDER; same for
    Elon/Powell; + the cross-figure "{person} says {kw} N times" pattern); (4) geopolitics by-date (one group vs
    per-conflict); (5) culture/box-office/streaming families, F1 constructor-vs-GP-winner split, commodity price-LEVEL,
    intl-politics country/leadership long tail, and whether to add an explicit small `MISC_NOVELTY` residual. Corpus to
    theme from: `plans/audit/results/prediction_cqg_unknowns_corpus_2026_06_16.md`.

- 2026-06-16 (autonomous run, tail-cleanup tick 5) — **Item 2b / 346 (sports CF-5 oracle relabel = ZERO) ROOT-CAUSED +
  FIXED (code), quickmerge BLOCKED on a live sibling's dirty UTL dep.** Reproduced on the real prod MDPS sports index
  (`market-data-tick-sports-prd`, 584,257 empty_confirmed): **583,185 are data_type=`trades` whose league_id resolves
  100%** (the finding's "61.8% league-match / league-resolution" hypothesis was WRONG for the bulk). Real root cause:
  `_PER_FIXTURE_DERIVED_DATA_TYPES` listed the MDPS odds tick as lowercase `"trades"`, but membership is tested as
  `data_type.upper() in set` (step 6.5 truthset gate + `is_derived_captured`) → `"TRADES"` never matched → step 6.5
  silently skipped EVERY `trades` empty → all kept SOURCE_RETURNED_ZERO instead of the truthset-derived
  EXPECTED_NO_FIXTURE. **Fix: `"trades"`→`"TRADES"`** (mtds `rebuild_sports_manifest_v9.py`; file kept at the 900-line
  cap). Verified by direct `_step6_5_truthset_gate` call + a regression test (`trades` not-in-truth →
  EXPECTED_NO_FIXTURE; in-truth → stays SOURCE_RETURNED_ZERO, since trades is correctly excluded from the guaranteed
  set). MTDS QG green (90s), 27 tests pass. **SHIP BLOCKED (not a code blocker):** quickmerge's pre-flight dep-audit
  refuses because `unified-trading-library` is dirty with a LIVE sibling's WIP (17 files, mtime age 0–61s = actively
  editing — the F1/ streaming/manifest_writer work; PROTECT, never stomp). This is the "ship in dep order, don't spin"
  case — the 346 change is QG-green + verified in the MTDS working tree, ships the instant UTL goes clean. Reason-level
  only (status-diff GREEN; does NOT block the G4 apply). Retry armed.

- 2026-06-16 (autonomous run, tail-cleanup tick 4) — **Item 2a / 384 (sports 6,869 blank capture_status) FIXED —
  is@8b3c7ef.** Characterized on the real prod sports IS-store: all 6,869 are NaN→`""` capture_status + blank
  data_type + blank league_id (API_FOOTBALL\* skeleton rows) → invalid v9. The migrator skips `_honest_capture_status`
  for sports BY DESIGN (count isn't the sports captured-signal), so they survive blank; blank data_type ⇒ no valid cell
  ⇒ phantom → **dropped in the sports structural path** + loud-fail guard for the blank-status-with-real-data_type case.
  Verified on the full 2.69M-row index: 6,869 dropped, 0 residual blank, 3 valid states intact. 2 regression tests. Drop
  executes at the operator-gated G4 apply (not run standalone). En route I tried + REVERTED a `_honest_capture_status`
  NaN-aware tweak — `_ensure_v9_columns._as_text` already coerces NaN→"" before it runs, so that was dead code. Item 2b
  (346 sports CF-5 relabel) next.

- 2026-06-16 (operator decisions 338 + 424 RESOLVED) — both previously operator-reserved gates now decided; per-AG tail
  unblocked (modulo one catalogue dependency, below).
  - **338 (prediction cqg-classifier coverage) → operator chose (c) IMPROVE THE CLASSIFIER FIRST** (do NOT materialise a
    cqg grain over a ~80% `OTHER` corpus). Unknowns extracted for hand-theming →
    `plans/audit/results/prediction_cqg_unknowns_corpus_2026_06_16.md`. **Two breadcrumbs corrected by the extraction:**
    the classifier lives in **UAC**, not instruments-service; and `ClassifierConfidenceLow` is legacy — the modern
    "unknown" is the honest `OTHER` sentinel returned on a **closed-set lookup miss** (no probability threshold). Only
    **29 real groups + OTHER** exist (≈BTC/ETH up/down + FED/CPI/2028-election/Oscars); **79.6% of market×day shards
    route to OTHER** (per-shard; 94.5% per-distinct-market). Readable `question` text lives ONLY in the trades parquets
    (`catalog.parquet` carries condition_ids only). **Leverage:** Polymarket slugs are templated factories → ~15
    slug-template rules (alt-coin up/down, crypto range/multistrike, daily city-temp, sports-by-fixture, Trump-approval,
    elon-tweet-count, geopolitics-by-date, macro prints, box-office, "{person} says {kw} N times", F1, fear&greed,
    commodities, intl-politics long-tail, MISC residual) cover the bulk. NEXT: operator prunes/merges the menu → encode
    slug-template rules into the UAC cqg map. 249-a (conditionId grain) stays shippable independently; 249-b (cqg grain)
    unblocks once the map is extended. **NOT a destructive/apply step — no auto-fire.**
  - **424 (sports pre-launch window) → RESOLVED to the cross-AG `could_exist` model, NOT a bespoke policy.** Operator's
    framing: a sports **fixture** = the bettable "instrument" (catalogue of what we can bet on); **leagues** group
    fixtures like data-type×venue groups DeFi. The capture_status question is the SAME `could_exist` predicate (M3
    `shard_source_availability`) CeFi/DeFi already use, with **fixture/league as the catalogue unit**: could-exist + no
    data = real gap; **cannot-exist (pre-launch, or fixture/league not in IS+UAC) = expected-absent, NEVER
    `attempted_failed`.** "Pre-launch window" is simply the time-slice where `could_exist=false` because the fixture
    hasn't entered the catalogue. Resolves the tail: **384** (blank capture_status) → run each through `could_exist`
    (should-exist+empty → typed real-gap reason; shouldn't-exist → expected-absent); **346** (CF-5 relabel) → pre-launch
    rows fall to expected-absent / `keep_src_zero`, never `attempted_failed`. **DEPENDENCY (load-bearing):** correctness
    requires IS+UAC to actually enumerate the fixture/league catalogue **with launch/season dates** so `could_exist` can
    return false for the pre-launch slice. If those dates are absent, that catalogue-completeness — not a policy call —
    is the real prerequisite for 384/346. ACTION PENDING: verify the sports fixture/league catalogue + launch dates
    exist in IS/UAC before encoding 346.
    - **VERIFIED 2026-06-16 → catalogue + coverage dates EXIST; no data backfill prerequisite — 384/346 are encode-now
      (wiring, not data).** SSOT `unified-api-contracts/.../sports/league_data.py`. (1) **Coverage starts** (global
      per-source): `odds_api = 2020-06-06` (operator hypothesis confirmed); `api_football = 2015-01-01` source-wide BUT
      detail types `FIXTURE_EVENTS/LINEUPS/STATS`+`PLAYER_STATS` floored to `2020-06-06` via `DATA_TYPE_COVERAGE_START`
      (aligned to odds_api cutoff) — so "api_football effectively ~June-2020" holds for the detail/odds data; only
      fixtures-schedule/standings/teams reach back to 2015. Mirror `canonical/coverage_starts.py` re-exports the same
      SSOT (no drift). (2) **could_exist oracle already exists + wired**:
      `is_expected_for_source(source, league_id, day, data_type)` (UAC `registry/sports_per_source_rules.py`) returns
      typed `EXPECTED_PRE_SOURCE_COVERAGE_START` / `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` / `EXPECTED_PRE|POST_SEASON`;
      `_classify_sports(row)` (UTL `legacy_reason_classifier.py`) is the relabel engine behind 346. (3) **GRAIN
      CORRECTION to the 424 model**: the sports manifest atom is **league grain** `(league_id, data_type, date)`, NOT
      fixture grain — `LEAGUE_REGISTRY` carries `data_sources`+`season_months`+tier per league but **no per-league
      launch date** and there is **no independent per-fixture catalogue** (fixture existence is read back from captured
      data → circular for the rows in question; slot-4 finding 2026-06-07 already fixed
      `_SPORTS_PRESENT_COLS=[data_type,league_id,date]` to avoid denominator inflation). So **encode 384/346 at
      `league × source/data_type × date`**, mapping data_type→source via `SPORTS_DATA_TYPE_TO_SOURCE`;
      pre-coverage/off-season/source-doesn't-cover-league → expected-absent, never attempted_failed. (4) **v9 path
      caveat**: the could_exist decision is path-INDEPENDENT (keys on source/league/date) so v9 can't break it; the ONLY
      path-dependent piece is `is_fixture_scheduled` (`unified-trading-library/.../sports_fixtures.py`) which hardcodes
      the legacy `sports_reference/by_date/...` path + does NOT pass `pipeline_mode=` → under v9-migrated paths it
      silently returns False and over-classifies `EXPECTED_NO_FIXTURE`; pass `pipeline_mode=` (the arg already exists on
      `candidate_parquet_paths`) if the backfill runs against migrated paths. (5) **Seeder gap (P3, not blocking)**: IS
      `_enumerate_sports` (`scripts/enumerate_expected_universe.py`) still emits only the coarse pre-coverage slice +
      says "per-league enumeration deferred (v2 — needs leagues catalog)" — but the catalog now exists in UAC, so the v2
      per-league seeder is buildable today (wire `is_expected_for_source` into the seeder).

- 2026-06-16 (autonomous run, tail-cleanup tick 3) — **Item 3 (12 zero-data live venues) RESOLVED — 7 re-phased, 5
  corrected as false-signal (real data in a separate bucket).** Diagnosed each of the 12 against MTDS plumbing + the
  actual buckets: **(a) 7 lending venues** (EULER_V2-ARB/ETH, FLUID-ARB, VENUS-BSC/ETH, RADIANT-ETH, BENQI-AVA) have NO
  UAC `get_subgraph_id` → the `evm_defi` collector physically skips them → genuinely zero → **re-phased live→pipeline,
  uac@6c74eaf** (QG-green 214s; survived a STAGE-0.4 rebase onto a sibling's M2-REFINEMENT a56a7fc — no conflict, no
  defi_venues.py overlap). **(b) 5 LST venues** (ANKR/STADER/STAKEWISE/SWELL/MANTLE) are a FALSE zero-signal:
  `projected_index_defi.parquet` (market-data-tick-defi bucket) does NOT aggregate the LST corpus, which lives in the
  dedicated `lst-rates-central-element-323112` bucket where they have **900–1,967 captured rows EACH** (verified by
  reading its availability_index) → correctly `"live"`, NO backfill needed, left untouched. The residual is a
  data-status AGGREGATION gap (lst-rates not folded into the defi could-exist view) → filed as a precise P3 todo.
  Tooling notes: env var is `DEPLOYMENT_ENV=prod` (not `_SHORT`); the diagnostic `--dry-run` LST collect added a handful
  of benign recent-date entries to the lst-rates manifest (real captured rates, honest). MTDS working tree carries a
  SIBLING's WIP (live/replay/websocket) — left untouched (I only ran the CLI).

- 2026-06-16 (autonomous run, tail-cleanup tick 2) — **Item 1 / 249-a SHIPPED + prod catalogue PROMOTED (0 → 668,384
  rows).** is@c100834 + a real prod data-op. The prediction catalogue loader (`_iter_prediction_by_date_snapshots`)
  required a `canonical_question_group=` path partition the writer never emits (actual
  `day=/venue=POLYMARKET/[market=BTC/]instruments.parquet`) → 0 rows. Rewrote the loader to parse `day=`/`venue=`
  - read only `instruments.parquet` (excl. metadata sibling), and the rollup to accumulate the conditionId grain from
    every frame while gating the cqg grain behind a non-empty cqg. **RAN
    `build_instrument_catalogue --asset-group prediction`** on real prod: 4,542 by_date parquets → **668,384 rows
    promoted to `prod/catalog.parquet`** (`monotonic_ok`) = 334,192 unique conditionIds × {trades, market_lifecycle},
    ZERO cqg-bundle rows (correctly gated on 338). Verified by reading the promoted parquet back.
    `unique_instruments[prediction]` 0 → 334,192. Split the plan item: 249-a ✅, 249-b (cqg grain) stays `- [ ]` gated
    on 338. IS QG-green; 36 catalogue tests pass (blank-cqg test de-vacuumed to assert the conditionId grain now
    materialises).

- 2026-06-16 (autonomous run, tail-cleanup tick 1) — **Item 5 (V4 fleet-gate blast-radius) VERIFIED GREEN + Item 4 (STEP
  5.92 label collision) FIXED.** **Item 5 (rule-11 blast-radius):** ran the STEP 5.92 candle-edge checker
  (`check_bar_edge_open_ingestion.py --scope <repo>`) on 3 CONSUMER services (market-data-processing-service,
  features-service, market-tick-data-service) + 2 LIBRARIES (unified-trading-library, unified-api-contracts) — **exit 0
  on ALL five**; the only non-clean lines are 2 PRE-BASELINED latent WARNs (MDPS `_convert_timestamps`, MTDS
  `_normalise_ohlcv`, both already in `bar_edge_open_ingestion_baseline.yaml` + owned by
  `bar_edge_left_vs_right_remediation_2026_06_08.md` Phase 1) → WARN not FAIL. The V4 fleet gate does NOT red any
  consumer/library CI — no regression introduced by the prior run; rule 11 closed. **Item 4:** pm@3be7eb595 — renumbered
  the `category=` ban `STEP 5.92`→`STEP 5.98` (bar-edge keeps the canonical 5.92); cosmetic, `bash -n` clean, PM
  QG-green (53s full + content-sentinel hit), base-`*`.sh is live-sourced so fleet-live on merge (no rollout). Remaining
  tail: Item 1 (249-a prediction loader), Item 2 (sports 384/346), Item 3 (222-followup 12-venue re-phase).

- 2026-06-16 (autonomous run, END-OF-RUN report) — **harness open CODE items GREEN; ⑬–⑲ pre-apply harness is
  code-complete — only operator-gated items remain (by the plan's own design).** Shipped this run (all QG-green,
  drift-clean — every HEAD ancestor-or-equal of origin/LDR, no dirty trees):
  - **V1 ✅ (CF-16 enumerator-reads-V0)** — pm@45a3ed16e. All 5 `_enumerate_v2_*` FULL + dispatch-mapped; defi/tradfi/
    sports resolve validity via the V0-composed UAC layer; alive+no-manifest → `expected_unattempted`.
  - **V4 ✅ (CF-19 candle-edge standing check)** — pm@b10dacadf. Right-edge (`t_close`) convention codified +
    QG-enforced fleet-wide (STEP 5.92 in base-service.sh + base-library.sh, STEP 5.74, runtime `assert_close_edge`,
    cross-source equivalence fixtures in MTDS/MDPS/features). Single normalization point = MDPS processed candles.
  - **DATA-001 `VENUE_DATA_TYPE_CAPABILITIES` completeness ✅** — uac@f8fb613 (QG-green 212s, 69 tests). 5 captured-but-
    uncredited defi venues declared (data-grounded floors from prod `projected_index_defi.parquet`); de-vacuumed the
    DATA-001 test. pm@caf609aef.
  - **Diagnosed (root-caused, not just symptom-noted):** item 249 (prediction catalogue 0 rows) → loader
    `_iter_prediction_by_date_snapshots` skips every blob lacking a `canonical_question_group=` path partition the
    writer never emits (actual layout `venue=/market=`); (a) conditionId grain shippable, (b) cqg grain gated on 338.
    pm@16392c664.
  - **Findings filed:** P3 `STEP 5.92` label collision in base-service.sh; P3 12 `live`-phased defi venues with zero
    rows in the projected index (re-phase to `pipeline` or run backfill — declaring them would inflate the denominator).
  - **Verified end-state:** the ⑬–⑲ scaffold CODE (possible_manifest, orphan sweep, manifest_diff, schema completeness,
    beta writer, cleanup, reconcile) is all on LDR/staging; V1/V4 GREEN; the projected v9 indexes + adjudicated diffs +
    beta renders are assembled (per the R3/R7 entries below). **The ONLY remaining gates are OPERATOR-RESERVED by the
    plan's own design** (⑬–⑲ HARD-BLOCK G4 pending the operator goalpost eyeball; line 221 "operator OK between each
    AG"): V6 operator eyeball/sign-off, G4 `--apply` (destructive prod migration), and the operator-decision items 338
    (prediction cqg-classifier coverage) + 424 (sports pre-launch window). These are legitimate hard-stops (a
    destructive prod migration the operator explicitly reserved to eyeball), NOT autonomous leftovers — not auto-fired.
  - **Per-AG data-ops tail (owned by slot-2/slot-3 per the ownership table, now precisely scoped):** 249-a (prediction
    conditionId-grain loader rewrite), 384 (sports 6,869 blank capture_status), 346 (sports CF-5 relabel), 222-followup
    (12 zero-data venue re-phase). Each is a `- [ ]` todo with a named repo + (where I went deeper) a root cause.

- 2026-06-16 (autonomous run, cont.) — **DATA-001 `VENUE_DATA_TYPE_CAPABILITIES` completeness SHIPPED (data-grounded) —
  uac@f8fb613.** Enumerated all 19 declared-but-uncapabilitied defi venues; grounded against the prod
  `projected_index_defi.parquet` (1.58M rows). **5 with actual captured shards declared** (MAKER/FRAX/MORPHOVAULTS
  →vault_share_price, SOLEND/MARGINFI→lending_indices, earliest-captured floors) so the could-exist universe builder
  (reads `VENUE_DATA_TYPE_CAPABILITIES` directly) now credits their shards; declared ONLY the captured dt so no
  denominator inflation. **De-vacuumed the DATA-001 test** (was green via the unmapped→all-fallback; now asserts the
  registry dict directly). The 12 `live`-phased zero-data venues were NOT declared (would inflate the denominator) →
  filed as a P3 phase-accuracy finding (re-phase to `pipeline` or run the backfill). UAC QG-green (212s), 69 targeted
  tests pass. Methodology note: the autonomous data-ops allowance (real prod GCS read) was the difference between a
  guessed declaration and a correct one — the probe overturned my category assumptions (FRAX/MAKER are captured as
  ERC-4626 vaults, NOT lending).

- 2026-06-16 (autonomous run, slot ip-172-31-5-118) — **harness VERIFY pass: V1 (CF-16 enumerator-reads-V0) GREEN.**
  Both named repos clean at LDR (is 0/0, uac 0/0); all ⑬–⑲ scaffold scripts present + landed (`possible_manifest.py`,
  `migration_orphan_sweep.py`, `manifest_diff.py`, `migration_schema_completeness.py`, `beta_manifest_writer.py`,
  `cleanup_legacy_twins.py`, `reconcile_phantom_manifest_rows_all.py`). **V1 verdict (code-read):** all 5
  `_enumerate_v2_*` FULL + dispatch-mapped, zero live stubs; defi/tradfi/sports resolve validity via the V0-composed UAC
  layer (`valid_data_types_for_instrument_type` matrix + `CHAIN_GENESIS_DATES` + per-instrument lifecycle bounds — the
  exact 3 layers `possible_manifest` composes, no divergent re-derivation), and alive+no-manifest cells yield
  `expected_unattempted`; per-AG unit tests + the v1→v2 superset integration test cover it. Flipped V1. **V4 (CF-19
  candle-edge standing check) GREEN** — the right-edge (`t_close`) convention is codified
  (`/codex/02-data/bar-boundary-candle-edge-convention.md`) + QG-enforced as a STANDING check (not a one-off): STEP 5.92
  `check_bar_edge_open_ingestion.py` wired in both `base-service.sh` (~3153) + `base-library.sh` (~1154), STEP 5.74
  truncation ban, runtime `assert_close_edge`, and the independent-reference/batch==live cross-source equivalence
  fixture in MTDS + MDPS + features-service; single normalization point = MDPS processed-candle store; per-source edge
  labels documented + source-aware-handled. Filed a P3 finding (cosmetic `STEP 5.92` label collision in
  `base-service.sh`). Scope note for this run: the harness CODE (⑬–⑲ scaffolds) is fully shipped; remaining open `- [ ]`
  are VERIFY items (V1✅, V4✅, V6 — operator eyeball) + operator-gated apply/eyeball/decision items (G4 `--apply` line
  221, prediction cqg 338, sports pre-launch-window 424) which are legitimate hard-stops by the plan's own design
  (operator wants to eyeball goalposts + OK between each AG before the destructive prod migration) — journaled, not
  auto-fired.

- 2026-06-14 (late, slot-4) — **Canonicalisation DEPLOYED to the live service + fleet promotion pipeline unblocked.**
  After C1/C2/C3 shipped to LDR: (1) reconciled `main`+`staging` to LDR via clean-start force-sync
  (`admin-force-sync-all-to-main.sh --no-commit --force-version-override --repos "deployment-api unified-api-contracts"`;
  version-drift guard was a stale-local-PM-manifest false positive — actual versions advanced 0.6→0.7, protection
  restored). (2) Diagnosed the **fleet-wide deploy stall**: the semver-agent (staging→main promotion +
  version-bump/deploy dispatch) was DEAD since the LDR-trunk decoupling dropped `push:[staging]` quality-gates-v2,
  orphaning its `workflow_run:[v2@staging]` trigger — shipped the additive `push:[staging]` fix to the PM template
  (per-repo rollout tracked above). (3) Deployed the service directly: `deploy-shared.sh` built deployment-api from LDR
  → `uts-shared-deployment-api` rev `00026-clc`. (4) Found the **rollup Cloud Run Job pinned to an old image** (separate
  from the API service) — updated `uts-prod-data-status-rollup` to the new image + executed; rollup recomputed 21:42Z.
  **Verified LIVE: canonical venues (`BALANCER-ARBITRUM`/`-AVALANCHE`/`-BASE`…), defi card 95.63%, `unique_venues` 22
  (canonical-collapsed).** Full issue ledger captured as the labelled todos above.

- 2026-06-14 (later, slot-4) — **DeFi data-status "weird" fully root-caused + denominator/perf/canonicalisation fixes
  SHIPPED; could-exist headline now 29% (honest, was 3.2% artifact).** Chain of findings on the beta projected index:
  1. **Beta-render perf** (dapi `be6f0e4`): the beta preview bypasses the LIVE rollup and hit O(unique×rows) per-value
     `== v` loops — defi card >280s, drilldown >400s. Vectorised (`value_counts` in `coverage.py` breakdowns;
     `groupby`+cached `_build_underlying_grouping` in `breakdowns_domain.py`). **Card 280s→8s, drilldown >400s→39s.**
  2. **Root cause of the card↔drilldown split** (97.6% card vs 3.2% drilldown shards-weighted): the honest-coverage
     drilldown matched the raw **bare** venue (`UNISWAP_V3`, 195k captured rows) against the UAC-canonical
     `PROTOCOL-CHAIN` expected universe (`UNISWAP_V3-ETHEREUM`) → `found_shards≈0`. NOT a lifecycle over-count. **Gap is
     DEFI-ONLY** (cefi/tradfi/sports/prediction = 0.0% name-change under canonicalisation; defi = 99.5%).
  3. **Reader-side canonicalisation** (dapi `16fb6b8`): `_canonicalise_defi_venue_column` applies
     `normalize_defi_venue(venue, chain)` AFTER the bare-pair whitelist in `_read_defi_merged_index` (rewriting the
     stored column instead broke the card's whitelist → 0%; the data model is bare venue + chain reconstructed at read).
     **drilldown shards_found 26,747→245,607 (9×), could-exist 3.2%→29%**; card stable 98%, captured unchanged 346,542.
  4. **completion_pct = shards-weighted** (dapi `40c61a4`, operator decision: canonical completion =
     captured/could-exist): drilldown `completion_pct` was the attempt/date-blended ~42%; now the shards-weighted 29%
     (matching the overall rollup + the field doc); old value kept as `completion_pct_attempt_blended`.
  - **B (impossible combos) verified already-gated**: the could-exist denominator (846,840 shards) is capability-gated
    via `VENUE_DATA_TYPE_CAPABILITIES` (40/72 canonical venues registered → only declared dts; 32 fallback venues return
    empty dts → contribute 0). 29% is honest, not inflated by impossible combos.
  - **Migration scope confirmed UNCHANGED** for venue (G4 is path/schema only) — BUT operator wants the manifest
    migrated to canonical names too (below).
- [x] ✅ [DESIGN] P1. **C — DeFi venue-spelling canonicalisation DONE + DEPLOYED (2026-06-14).** `normalize_defi_venue`
      now collapses no-underscore ghosts (`AAVEV3→AAVE_V3`, `YEARNV3→YEARN_V3`, hyphenated
      `AAVEV3-ARBITRUM→AAVE_V3-ARBITRUM`) to the canonical underscore form BEFORE membership/alias resolution (UAC
      `660f272` + `test_no_underscore_ghost_spelling_collapses_to_underscore`). dapi reader whitelist + canon column
      rewritten to canonicalise-then-membership, **direct-`venue-chain`-concat preferred** when already canonical (fixes
      `SUSHISWAP+ARBITRUM→SUSHISWAP-ARBITRUM`, not the V3-forcing alias) — dapi `16fb6b8`+`40c61a4`+C3. One-shot
      stored-data migration tool `instruments-service/scripts/canonicalize_defi_manifest_venue_2026_06_14.py` written
      (dry-run 1.19M/1.58M rows, gated `--apply --confirm` / `--projection-out`, idempotent) for the G4 apply. **99.1%
      of captured defi rows now resolve into `ALL_DEFI_VENUES`; LIVE on `uts-shared-deployment-api` rev `00026-clc` +
      rollup recomputed — canonical venues (`BALANCER-ARBITRUM`…) confirmed serving.** Residuals carried to the todos
      below.

### Remaining known issues + investigations — beta-manifest eyeball → deploy arc (slot-4, 2026-06-14)

- [x] ✅ [DATA] P1. **G4 — TradFi apply — DONE** (DeFi/CeFi/Sports/Prediction G4 `--apply` COMPLETE 2026-06-29 per
      `master_data_canonicalisation`; **TradFi G4 `--apply` also DONE** 2020-2026 — 7 VMs, exit_code=0 fatal=0,
      completed 2026-07-06; independently GCS re-verified 2026-07-12 — canonical v9 `pipeline_mode=` partitions
      confirmed present for day=2020-01-02 and day=2026-01-15; corpus orphan sweep E=0 over 10.58M objects,
      2026-07-10T17:17:22Z re-confirmed 2026-07-12T08:28:38Z). The DeFi apply included
      `canonicalize_defi_manifest_venue_2026_06_14.py --apply --confirm` (C2) so the stored `_index` venue column is
      canonical. (was: "G4 — TradFi apply REMAINS + RESUME runbook... TradFi OOM-blocked — restart with lower
      concurrency / larger VM" — stale.) Corrected per operator ruling 2026-07-12, plan-reconciliation finding 128
      (`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2).
- **[FORKED 2026-07-24 → `infra_ops_residual_migration_verification_2026_07_24.md`]** "RESUME runbook (48 paused GCP
  schedulers + 26 AWS rules) un-pause — runs ONLY after TradFi G4 also verified..." — full verbatim text relocated to
  the child plan as part of the 2026-07-24 plan line-cap remediation split (see
  `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`).
- [x] ✅ [DATA] P2. **`VENUE_DATA_TYPE_CAPABILITIES` completeness — DONE (data-grounded).** — uac@f8fb613 (QG-green
      212s, 69 tests). Enumerated ALL declared-but-uncapabilitied defi venues: 19 of 124 `ALL_DEFI_VENUES` lacked a
      capability entry; cross-referenced `DEFI_VENUE_PHASE` + the prod `projected_index_defi.parquet` (1.58M rows) for
      ground-truth. **5 had ACTUAL captured shards (the real uncredited bug)** → declared with the data_type ACTUALLY
      observed + the earliest-captured date as the best-effort floor: `MAKER-ETHEREUM`→`vault_share_price` 2023-01-18,
      `FRAX-ETHEREUM`→`vault_share_price` 2023-10-19, `MORPHOVAULTS-ETHEREUM`→`vault_share_price` 2024-01-04,
      `SOLEND-SOLANA`→`lending_indices` 2022-11-01, `MARGINFI-SOLANA`→`lending_indices` 2025-01-01. Declared ONLY the
      captured data_type (not the broad set) so the could-exist denominator isn't inflated with uncaptured types; this
      also tightens `get_expected_data_types_for_venue` from the 25-item all-fallback → the single real dt.
      **De-vacuumed the DATA-001 test** (`test_mtds_venue_coverage.py::TestNewlyCapabilitiedDefiVenues`): it was passing
      via the unmapped→all-fallback; now asserts `VENUE_DATA_TYPE_CAPABILITIES[venue]` DIRECTLY (the registry the
      could-exist builder reads). **The other 14 (2 `pipeline`-phased = roadmap, legitimately uncapabilitied; 12
      `live`-phased have ZERO rows in the projected index) were NOT declared** — declaring a no-data venue would falsely
      inflate the could-exist denominator; the 12 are a phase-accuracy finding (next todo).
- [x] ✅ [DATA] P3. **12 `live`-phased zero-in-projected-index defi venues — RESOLVED + corrected (2026-06-16).** The
      original finding ("12 venues have ZERO rows") was PARTLY a FALSE SIGNAL — `projected_index_defi.parquet`
      (market-data-tick-defi bucket) does NOT aggregate the LST corpus, which lives in a SEPARATE bucket
      `lst-rates-central-element-323112`. Diagnosis split the 12: **(a) 7 lending venues**
      (`EULER_V2-ARBITRUM/ETHEREUM`, `FLUID-ARBITRUM`, `VENUS-BSC/ETHEREUM`, `RADIANT-ETHEREUM`, `BENQI-AVALANCHE`) have
      **no UAC `get_subgraph_id`** → the MTDS `evm_defi` collector logs "No subgraph ID … skipping" → genuinely zero
      everywhere → **re-phased live→pipeline** (uac@6c74eaf). **(b) 5 LST venues**
      (`ANKR/STADER/STAKEWISE/SWELL/MANTLE-ETHEREUM`, tokens ankrETH/ETHx/osETH/swETH/mETH in `_EVM_LST_ABI_METADATA`)
      **DO have captured data** in the `lst-rates` bucket (verified: ANKR 1,967 · STADER 1,045 · STAKEWISE 904 · SWELL
      1,129 · MANTLE 957 captured rows, venue stored bare) → correctly `"live"`, NO backfill needed, NOT re-phased.
      Residual = a data-status AGGREGATION gap (next todo), not a data gap. Verified by reading both
      `_index/availability_index.parquet` (lst-rates) + `projected_index_defi.parquet`.
- **[FORKED 2026-07-24 → `defi_venue_lst_rates_residual_2026_07_24.md`]** "NICE-TO-HAVE — fold the `lst-rates` corpus
  into the DeFi could-exist / data-status view..." — full verbatim text relocated to the child plan as part of the
  2026-07-24 plan line-cap remediation split (see `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`).
- **[FORKED 2026-07-24 → `defi_venue_lst_rates_residual_2026_07_24.md`]** "Orphan / junk defi venues — `VAULT` (generic,
  1113 captured rows...)" — full verbatim text relocated to the child plan as part of the 2026-07-24 plan line-cap
  remediation split (see `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`).
- [x] ✅ [SCRIPT] P1. **Per-repo `semver-agent.yml` rollout fleet-wide** — the PM template fix (additive
      `push:[staging]` trigger + `head_sha→github.sha` fallback) landed; the per-repo copies are still the OLD
      orphaned-trigger version. Regen via `rollout-workflow-templates.sh --template semver-agent` + commit per-repo +
      reach each repo's `main` (the trigger fires from the default branch). Restores staging→main promotion +
      version-bump/deploy dispatch that was DEAD fleet-wide since the LDR-trunk decoupling dropped `push:[staging]`
      quality-gates-v2. Verify it fires on a staging push. SSOT: `/codex/08-workflows/ci-cd-flow.md` § "LDR-trunk
      decoupling". — strategy-service@e884205a: spot-checked 11 fleet repos, both push:[staging] trigger + github.sha
      fallback present.
- **[FORKED 2026-07-24 → `infra_ops_residual_migration_verification_2026_07_24.md`]** "Rollup Cloud Run Job image lags
  the API deploy — `uts-prod-data-status-rollup`..." — full verbatim text relocated to the child plan as part of the
  2026-07-24 plan line-cap remediation split (see `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`).
- **[FORKED 2026-07-24 → `infra_ops_residual_migration_verification_2026_07_24.md`]** "deployment-ui — surface the
  could-exist vs manifest-capture distinction..." — full verbatim text relocated to the child plan as part of the
  2026-07-24 plan line-cap remediation split (see `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`).
- **[FORKED 2026-07-24 → `infra_ops_residual_migration_verification_2026_07_24.md`]** "Local-dev uvicorn restart
  flakiness — repeated `:8004` bind/port races..." — full verbatim text relocated to the child plan as part of the
  2026-07-24 plan line-cap remediation split (see `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`).

- 2026-06-14 (autonomous session, slot-4) — **OOW denominator exclusion SHIPPED end-to-end — DeFi coverage 22.11% →
  97.55%.** Two-repo dispatch complete:
  1. **deployment-api** (`coverage.py`, commit `149473c` + fix `90a8ad7`): `_build_coverage_for_cat` partitions
     `empty_confirmed` rows into OOW vs within-window using `is_out_of_coverage_window` (UAC function classifying 15
     lifecycle reasons — EXPECTED_PRE_GENESIS_CHAIN, EXPECTED_INSTRUMENT_NOT_LISTED, EXPECTED_PAST_SOURCE_COVERAGE_END,
     etc.). Denominator = `captured + within_window_empty + attempted_failed + expected_unattempted` — excludes OOW. Fix
     `90a8ad7` adds resilience: accepts both `error_reason` (live consolidated index column) and `reason` (beta
     projected parquet column) so the OOW partition fires correctly in beta mode.
  2. **deployment-ui** (`client.ts`, `mock-api.ts`, `HonestCoverageCard.tsx`, `tests/unit/oow-denominator.test.ts`,
     commit `ea1db02`): added `out_of_window?: number` to all three type shapes (`TurboSubDimension`,
     `TurboAssetGroupStatus`, `HonestCoverageStatusCounts`), all 8 mock blocks seeded with `out_of_window: 0`,
     `CoverageBar` renders a distinct slate-grey non-gap segment when `out_of_window > 0`, legend item "outside window —
     not a gap", 7 unit tests pass, 206/206 Playwright smoke tests pass.
  - **Verified on real GCS data** (`projected_index_defi.parquet`, 1.58M rows, updated 2026-06-11): 349,326 captured ·
    1,221,955 OOW empty · 6,016 within-window empty · 2,740 failed → denominator 358,082 → **97.55%** (vs 22.11% naive
    including OOW in denominator; +75.44pp improvement).

- [x] ✅ [DATA] P1. **OOW partition is now DATA-TYPE-AWARE — schedule-defining FIXTURES `SOURCE_RETURNED_ZERO`
      (no-match-day) counts as RESOLVED, not a gap (operator direction 2026-06-23).** A schedule-DEFINING data_type IS
      the source-of-truth for what exists to capture; sports `FIXTURES` (API-Football) returning 200+0-rows for a
      (league, day) means there genuinely were NO matches that day → out-of-window/resolved, like `EXPECTED_NO_FIXTURE`.
      Data-type-aware on purpose: an ENRICHMENT (`FIXTURE_STATS`/`PLAYER_STATS`/`ODDS`/`MATCHES`) `SOURCE_RETURNED_ZERO`
      stays an in-window gap (its zero may be a real miss; `MATCHES`/FootyStats is fixture-pinned, NOT schedule-defining
      — only `FIXTURES` qualifies). Shipped: **UAC** new `SCHEDULE_DEFINING_DATA_TYPES` (`frozenset({"FIXTURES"})`) +
      `is_resolved_schedule_empty(data_type, reason)` + `is_out_of_coverage_window(reason, data_type=None)` gains the
      optional `data_type` (`_honest_coverage_logic.py` / `honest_coverage.py` / `__init__.py`; +1 test class, 45 pass).
      **deployment-api** `coverage.py` + `coverage_metrics.compute_out_of_window_count` thread the `data_type` column
      through (5 new tests, 38 pass). **Codex** `honest-absence-downstream-handling.md` § "OOW Denominator Partition" +
      new subsection. **Re-measured golden window** (sports `_index`, 2025-09-01..2025-11-30): **FIXTURES 93.7% →
      100.0%** (233 no-match-day SRZ cells reclassified gap→resolved); **overall sports 46.6% → 46.9%** (overall stays
      low — the enrichment data_types are genuinely incomplete, correctly NOT affected). Repos: unified-api-contracts,
      deployment-api, unified-trading-pm. Provenance: operator directive 2026-06-23.

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
- **[FORKED 2026-07-24 → `infra_ops_residual_migration_verification_2026_07_24.md`]** "Rollup worker: precompute
  `unique_instruments` — the Cloud Run data-status rollup..." — full verbatim text relocated to the child plan as part
  of the 2026-07-24 plan line-cap remediation split (see `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`).
- [x] ✅ [DATA] P2. **249-a SHIPPED — prediction catalogue conditionId grain (0 → 668,384 rows promoted).** —
      is@c100834. Root cause confirmed: the loader `_iter_prediction_by_date_snapshots` required a
      `canonical_question_group=` PATH partition the writer NEVER emits (actual layout
      `day=/venue=POLYMARKET/[market=BTC/]instruments.parquet` + a `prediction_market_metadata.parquet` sibling), so
      every blob was skipped → 0-row catalogue. **Fix:** loader now parses `day=`/`venue=` (cqg optional), reads ONLY
      `instruments.parquet` (excludes the metadata sibling), reads venue-level + market-level (deduped by
      `(venue, conditionId)` in `_merge_lifecycle`); the rollup skips only EMPTY frames and accumulates the conditionId
      grain (`instrument_key`) from every frame, gating the cqg grain behind a non-empty `cqg_str`. **RAN on real prod**
      (`build_instrument_catalogue --asset-group prediction`): 4,542 by_date parquets → **668,384 rows promoted to
      `prod/catalog.parquet`** (`guard_reason=monotonic_ok`) = **334,192 unique conditionIds × {trades,
      market_lifecycle}**, ZERO `prediction_canonical_question_group` rows (cqg grain correctly absent).
      `unique_instruments` for prediction goes 0 → 334,192. Test de-vacuumed
      (`test_prediction_rollup_blank_cqg_emits_conditionid_grain_no_bundle`); IS QG-green; 36 catalogue tests pass.
- **[FORKED 2026-07-24 → `prediction_cqg_residual_2026_07_24.md`]** "249-b — prediction cqg grain
  (`prediction_canonical_question_group`) — GATED on operator decision 338..." — full verbatim text relocated to the
  child plan as part of the 2026-07-24 plan line-cap remediation split (see
  `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`).

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
  Projections at `gs://market-data-tick-<tag>-prd-…/\_index/audit/projected_index*<ag>.parquet`; diffs
  `/tmp/manifest*diff*<ag>.json`. **Per-AG verdicts (projected rows | diff | justification):**
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
- **[FORKED 2026-07-24 → `prediction_cqg_residual_2026_07_24.md`]** "Prediction cqg classifier coverage decision BEFORE
  the pred G4 apply: 542,169/573,536 objects (94.5%) route to attempted_failed[ClassifierConfidenceLow]..." — full
  verbatim text relocated to the child plan as part of the 2026-07-24 plan line-cap remediation split (see
  `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`).
- **[FORKED 2026-07-24 → `sports_prelaunch_cf5_verify_residual_2026_07_24.md`]** "Sports CF-5 oracle relabel = ZERO —
  ROOT-CAUSED + FIXED (code), preserved to a wip branch awaiting a clean-dep window..." — full verbatim text relocated
  to the child plan as part of the 2026-07-24 plan line-cap remediation split (see
  `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`).

- 2026-06-11 (~19:10Z, autonomous run) — **FINAL SIGN-OFF SWEEP SNAPSHOT: ALL FIVE AGs GREEN on final HEAD** — defi E=0
  (18:52Z) · cefi E=0 (19:00Z) · prediction E=0 (19:02Z) · tradfi E=0 (19:07Z) · sports odds E=0 + reference E=0
  (19:09–19:10Z); unknown*prefixes=0 on every surface. Reports refreshed at `\_index/audit/orphan_sweep*<ag>.parquet`(+
  sports per-bucket). This is the ⑬-input snapshot for the verdict packs.
  ALSO:`DATA*STATUS_BETA_MANIFEST_BLOB`smoke-verified END-TO-END against real GCS (deployment-api seam loaded the
  946,360-row tradfi projection with the env set; live index with it unset) — the operator's beta-render recipe is
  live:`DATA_STATUS_BETA_MANIFEST_BLOB='\_index/audit/projected_index*{asset_group}.parquet'`+`restart-deployment-stack.sh --api`.

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
  `transport=rest`). Logs `/tmp/r7_is*<ag>\_dry.log`. **TradFi market-tick R7 reference loop** (in flight): rebuild now
  projects via `--beta-manifest-out` (mtds@fa375c7), CF-11 reads the CONSOLIDATED index + collector receives re-emits
  (37,477 empty + 6,042 failed collected), row_key flattened for the differ; diff progressed 45,003→14,831 removed;
  remaining removals characterized = the 183,943 PRE-HIVE/no-instrument_type legacy objects' cells (FX 1,967 spot_pair ·
  CME chains · CBOE 15m · NYSE/NASDAQ equity 1m) — parser extended with legacy shapes C (hive-no-instrument_type) + D
  (pre-hive instrument-key, ported from the R1 backfill grammar) + an unparseable shape histogram; re-projection
  running.
- [x] ✅ [DATA] P1. **sports 6,869 blank-capture_status rows — FIXED (phantom drop).** — is@8b3c7ef. Characterized the
      6,869 against the real prod sports IS-store index (`instruments-store-sports-central-element-323112`): ALL are NaN
      capture_status (→ `""` via `_ensure_v9_columns._as_text`) AND blank `data_type` AND blank `league_id`, venues
      `API_FOOTBALL`/`API_FOOTBALL_FIXTURES`/`api_football`, dates 2019-01-01→2026-04-12 (370 with count>0, 6,499
      count==0). Root cause: the migrator deliberately skips `_honest_capture_status` for sports (`if not is_sports` —
      sports capture_status is enumerator/oracle-authoritative; instrument_count is NOT the sports captured-signal, 194k
      sports captured cells legitimately carry count==0), so these never-stamped skeleton rows survive blank = invalid
      v9. Since a blank data_type ⇒ no valid v9 cell ⇒ not re-stampable, they are **PHANTOM → dropped** in the sports
      structural path, with a **loud-fail guard** if a blank-status row ever has a real data_type (that would need an
      honest oracle re-stamp, not a drop). **Verified on the full prod index**: 2,694,638 → 2,687,769 rows (6,869
      dropped), **0 residual blank**, all 3 valid states intact (empty_confirmed 2,042,203 · captured 567,281 ·
      attempted_failed 78,285). 2 regression tests added. The drop EXECUTES at the operator-gated G4 `--apply` (the
      migrator's transform now produces 0-blank sports output); not run standalone (G4 is operator-reserved). Repo:
      instruments-service `scripts/migrate_instruments_store_v9.py`.

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
- **[FORKED 2026-07-24 → `sports_prelaunch_cf5_verify_residual_2026_07_24.md`]** "Sports pre-launch-window corpus
  decision (C3, 10,345 objects — operator-gated)..." — full verbatim text relocated to the child plan as part of the
  2026-07-24 plan line-cap remediation split (see `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`).

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
  in new `registry/\_schema_spec*{defi,prediction,tradfi}.py`(uac@715e2ed); the completeness checker now matches via
  UAC`carried_column_names` (canonical ∪ aliases — renamed-but-carried is GREEN, genuine drop stays RED; is ship).
  RE-RUN VERDICTS vs real prod GCS: **defi 0 RED (32 cells) · tradfi 0 RED (19) · prediction 0 RED (2)**. cefi
  re-verifies when R1's sweep re-run produces its report parquet. NOTE: the R-wave agents hit the account session limit
  (resets 10:10Z) — R2 was finished INLINE from their preserved WIP; R1/R4/R5/R6 resume per the brief in the master
  plan.

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

- 2026-06-16→17 (autonomous run — A2 mtds/mdps/PM-chores tail, the slice the UAC-vertical agent named "separate agent
  owns mtds/mdps/PM-chores"; this is the rule-9 FINAL report). **All 8 dispatch items resolved + flipped; 0
  scope-defers.** Repos: market-tick-data-service + market-data-processing-service + unified-trading-pm (the concurrent
  agent's unified-api-contracts / instruments-service / deployment-api were NOT touched). Final tally:
  - **R5-fix-1** (P0, mtds@657f615) — DIAGNOSED already-correct at LDR-tip: the
    `Invalid comparison datetime64[ns] vs date` raw compare no longer exists (every cefi-tardis date compare uses
    `.dt.date`/scalar `.date()`; exhaustive scan = 0 unguarded; `eb33603` repro now exits 0). Shipped the durable guard
    the dispatch asked for: new `test_tardis_resolve_symbols_date_boundary.py` (9 tests, real datetime64[ns] parquet at
    the boundary, re-catches a regression). **DECISION (rule 1):** shipped the boundary regression test rather than a
    no-op "fix" of already-correct code. Live BINANCE-FUTURES Tardis CSV re-smoke = BLOCKED-LIVE-VERIFY (real
    creds/network; `--block-network` here) — bug-class closed + test-guarded regardless.
  - **Massive futures endpoint** (mtds@657f615) — `fetch_futures_chain()` repointed `/v3/reference/futures/*` →
    `/futures/v1/{contracts,products}` (GA), products `name` merged via `_normalise_futures_contract(product_map=…)`;
    docstrings updated. Live HTTP verify = BLOCKED-LIVE-VERIFY (operator-gated entitlement).
  - **F-X1** (mtds@657f615) — rewrote the stale tautological bucket test → asserts the canonical `resolve_bucket_name`
    env-after-asset_group shape `market-data-tick-cefi-test-{pid}` (was encoding the legacy env-prefix shape). Green.
  - **A5 LIGHTER perp_funding** (mtds@657f615) — `_collect_lighter` rewired off the hand-rolled aiohttp+gzip loop onto
    the `TardisAdapter.download_csv` SSOT (mirrors `umi_tick_provider`) with **bare base-asset symbols** (`BTC`,…,
    dropped `-USDC`); deleted `_parse_lighter_market_stats_csv` + its tests; output contract
    (`write_defi_rows`/`record_zero_rows`) preserved; tests updated green. **DECISION (rule 1):** took the recommended
    SSOT-aligned fix (download_csv) over the symbol-only stop-gap. Live Tardis non-zero verify = BLOCKED-LIVE-VERIFY.
  - **B0-PRE** (read-only, pm@3214a18fd) — re-ran the DeFi `enumerate_expected_universe` v2 dry-run on the prod
    catalogue (`gs://instruments-store-defi-prd-…/prod/catalog.parquet`, 1,578,922 manifest rows, 2-day window):
    **52,862 candidates/2d** vs recorded 57,074/2d — same order, Δ≈−4.2K = catalogue drift, NOT a regression.
    `PROTOCOL_CAPABILITIES`=55 confirmed (37→55); 18 new venues honest could-exist; `native_staking_rates`/
    `vault_share_price` stay BLOCKED_UPSTREAM_CAPABILITY. Additive ⇒ NON-BLOCK; `--apply-write` seed stays G1.run-gated.
  - **GAP-7** (mdps) — VERIFIED already-shipped at **mdps@4363bce** (zero `dependency_checker` `category` params remain;
    every sig uses `asset_group`). The 3 residual `category` string refs are framework template-var / manifest-column
    names — a separate `category=`-ban vocab concern, NOT this rename. Flipped 2 stale-open checkboxes (downstream +
    cefi plans, pm@3214a18fd). **DECISION (rule 1):** verified + flipped rather than re-implement done work.
  - **M-COORD-4** (pm@d096d0220) — wired the `## 🟦 Gate-State Board (G0–G5 × asset_group)` into the master_data
    coordinator (🟢/🟡/🔴 per AG, sourced from the WAVE checkboxes + A–H verdict + per-AG G4 ticks + a per-cell basis +
    refresh note). Current: G0🟢 G1🟢(dry) G2🟡 G3🟢 G4🟡(operator-gated) G5🔴 all 5 AGs.
  - **C13** (mtds@712aa01 + pm@dd19f00dd) — relocated the 8 runnable defi migration scripts (oracle*relabel /
    chain_genesis / venue_launch / phantom_captured / captured_pre_existence / captured_vs_objects /
    index_venue_canonicalise / object_path) from PM `plans/audit/results/` → `mtds/scripts/` (script-homes SSOT);
    ruff-cleaned 16 trivial F541 so they're lint-clean in mtds; `.md` results + coverage query + a1–a6/cf*\* harnesses
    stay. **DECISION (rule 1):** auto-fixed the cosmetic ruff issues during relocation (a script must be lint-clean to
    live in mtds); MOVED (operator's documented intent) rather than deleted as spent one-offs (C0 walk C2–C7 still
    pending).
  - **VERIFIED END-STATE:** mtds LDR-tip QG-green (sentinel==HEAD); PM LDR drains to main via the standing `*/15`
    LDR→main PR. **Genuine non-completions (all credential/network-gated live probes the dispatch pre-authorised as
    BLOCKED-LIVE-VERIFY, code+tests shipped + QG-green):** R5-fix-1 Tardis re-smoke, Massive `/futures/v1` HTTP, A5
    Tardis non-zero. **Out of scope (untouched, by dispatch / operator-gate):** UAC/IS/deployment-api (concurrent
    agent), G4 `--apply` (operator HARD-STOP), and R5-fix-6 (the separate "wire-or-retire `MassiveTradfiRestConnector`"
    follow-on — now code-unblocked by the endpoint fix, but still needs a live probe + a wire/retire decision; left as
    its own open todo, not claimed here).

- 2026-06-17 (autonomous — Massive CME-futures transport correction, operator ping) — **The 2026-06-16 `/futures/v1`
  REST "fix" was a MIS-DIAGNOSIS** (corrected by the operator + a sibling agent's proven 5y ES pull): our Stocks-Starter
  REST tier is **equities-only — CME futures are NOT on the REST API**; the proven transport is Massive's **S3
  flat-files** (`flatfiles/us_futures_cme/minute_aggs_v1/…` over `files.massive.com`, **path-style addressing
  mandatory**, distinct `MASSIVE_S3_*` keys). Filed issue doc `massive_cme_futures_flatfiles_not_rest_2026_06_17.md`
  (pm@1c8004221) + corrected `tradfi_massive_dual_source` (re-opened futures todo → flat-files; gate UNLOCKED).
  **SHIPPED mtds@a311561**: new `massive_flatfiles.py` (path-style boto3 S3 + outright filter + ns LEFT→right-edge +
  1m→15m resample) + `massive_tradfi_rest_connector` futures path (`fetch_futures_minute_aggs`/`fetch_futures_chain`/
  `_s3_get_object_bytes`, dispatch routes futures→S3); **dead `/futures/v1` REST futures code +
  `_normalise_futures_contract` DELETED** (equities/options REST untouched); +11 mocked-S3 unit tests (40 pass/2 skip);
  mtds QG-green (codex 0, STEP 5.12b clean). **A sub-agent died on a transient 529 mid-implementation** (left
  `massive_flatfiles.py` + connector edits uncommitted + a 116-line duplicate-defs bloat that tripped the codex
  file>900 + method>50L gates); I reconciled it down here (deleted the duplicates → 736L, refactored the two methods to
  thin wrappers, added the missing tests + the `timedelta` top-import fix). Shipped via the **dirty-deps direct-LDR
  carve-out** (UAC+UTL were a concurrent agent's WIP). **Residual (named, NOT done):** connector has 0 production
  consumers → wiring into the live tradfi dispatch + the `us_futures_cme` bulk-backfill + roll back-adjustment + live
  `@requires_credentials` S3 verify are Phase-4b follow-ons tracked in the plan. Decisions (rule 1): corrected my own
  prior wrong flip; took the SSOT-aligned flat-files transport; finished the dead sub-agent's work in-slot rather than
  re-dispatch.

- 2026-06-21 (empirical live-index schema audit — operator "is v9 actually migrated, can I check the real status?") —
  **The LIVE consolidated `_index/availability_index.parquet` is ALREADY ~v9 across every asset_group** (measured the
  actual `schema_version` distribution, per the "trust the distribution, never the constant/checkbox" rule — NOT the
  projected/beta index): **defi 100.0% (3.90M rows) · sports 100.0% (1.76M) · tradfi 99.7% (2.28M, v4 tail 0.3%) ·
  prediction 97.9% (70K, v4 tail 2.1%) · cefi 96.6% (3.87M, v4/v5/v6 tail 3.4%)**, and the v9-added columns (`source` /
  `asset_group` / `pipeline_mode`) are present in all five. So the writers emit v9 and the overwhelming majority of
  historical rows are v9 — the migration is **effectively live in prod**, which the stale "G4 `--apply` parked (operator
  HARD-STOP)" framing above no longer reflects for the steady-state DATA. **NOT a clean 100%-everywhere bulk `--apply`**
  — the cefi/tradfi/pred legacy tails (old un-restamped shards) remain, so a final re-stamp sweep of those tails is the
  only residual; defi/sports are fully v9. Provenance: read on the human-planning VM via pyarrow over the live `-prd-`
  market-data-tick buckets.

- 2026-06-22 (CORRECTION + prod fix — the data-status "Unknown error" was BETA, not memory) — the live
  `uts-shared-deployment-api` Cloud Run service **had `DATA_STATUS_BETA_MANIFEST_BLOB` SET** (to
  `_index/audit/projected_index_{asset_group}.parquet`) — so the deployed data-status surfaces were rendering the
  **projected/beta preview, NOT the live index** (correcting the 2026-06-21 note's implication that the default non-beta
  path was already live). The market-tick-data-service detail (`/api/data-status/turbo`, full range) returned an
  **empty-body HTTP 500** ("Unknown error" in the UI) — the beta projected-index path crashing the heavy per-AG compute;
  a prior **8Gi→16Gi bump (rev 00073) stopped the OOM but NOT the 500**. **Fix: removed the beta env var**
  (`gcloud run services update --remove-env-vars=DATA_STATUS_BETA_MANIFEST_BLOB`, rev 00075) → endpoint now **HTTP 200
  with real live v9 data** (`overall_completion_pct 87.07`, `migration_in_progress:false`), verified stable (2nd call
  200/4.2s/26MB) with no new errors. **Durable**: the shipped `deploy-shared.sh` (deployment-service@10e2ddc) sets env
  via `--set-env-vars` without beta, so a future deploy won't re-introduce it. This is the operational half of the P2
  beta-retirement below; the code-level removal still stands.
  - [x] ✅ [CODE] P2. **Retire the CF-20 beta-manifest preview machinery** (target repo: **deployment-api**) — DONE
        2026-06-22. Operational half already live (beta env var removed, rev 00075). Code retirement shipped
        **deployment-api@d93e54a** (11 files, +79/-525): removed `DATA_STATUS_BETA_MANIFEST_BLOB` setting +
        `data_status_beta_manifest_blob` config field; `manifest_source.py`
        `is_beta_mode`/`is_service_beta`/`beta_eligible`/`BETA_ELIGIBLE_SERVICES` + the projected-index branch in
        `read_manifest_index` (live-only now, keeps the consolidated-blob stale fallback); the two-phase beta leg of
        `_rollup.py` + `data_status_rollup_worker.py`; beta-namespacing in `rollup_blob_path` (always
        `{svc}/{kind}.json.gz`); + beta tests removed. QG-green (ALL PASSED 65s, coverage ≥70%); 0 functional beta
        symbols remain. The 5 static `_index/audit/projected_index_{ag}.parquet` (cefi/defi/tradfi/sports/prediction
        `-prd-` buckets) **GCS-deleted** 2026-06-22 (verified nothing reads them: live service env beta-free, no
        standalone rollup Cloud Run Job). Redeploy rides the normal LDR→staging→main→image pipeline (env-var removal
        already fixed prod; code retirement is cleanup). (Operator-acked 2026-06-21/22. Provenance: live-index v9 audit,
        this plan's 2026-06-21/22 progress entries.)
  - **[FORKED 2026-07-24 → `infra_ops_residual_migration_verification_2026_07_24.md`]** "Re-stamp the legacy
    schema_version tails (target: mtds `migrate_*_to_v9_canonical.py` + ManifestWriter rebuild) — DEFERRED per operator
    2026-06-22..." — full verbatim text relocated to the child plan as part of the 2026-07-24 plan line-cap remediation
    split (see `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`).

## Deferred work — migrated to:

**Not yet identified** — the sole hit (line ~1352, "**Re-stamp the legacy schema_version tails**... DEFERRED — operator
2026-06-22: wait for the active backfill fleet to finish, then run in a quiet window") is a real, operator-acked
deferral (operator explicitly said wait for the active backfill fleet to drain before running), but no separate
successor plan exists or is needed — it remains this plan's own open `- [ ]` [DATA] P3 todo. The named "Trigger to
resume" condition (the `cefi-hyperliquid-2023..2026`, `mdps-backfill-tradfi`, `mdps-sports`, and `mtds-dex-pools-*`
backfill VMs reaching STOPPED) was already observed true as of the 2026-06-22 characterisation, but the actual `--apply`
run (gated on a pre-migration drain + operator sign-off, since it is irreversible) has not yet been executed. This plan
remains the owner until that run ships.

> **[EDIT 2026-07-24 — plan line-cap remediation split]** The "no separate successor plan exists or is needed" call
> above is superseded by this same split: the item IS now forked to its own tracked todo in
> `infra_ops_residual_migration_verification_2026_07_24.md` (see that plan for current status — the deferral condition
> and gating described above still apply, this note only corrects where the live todo lives).
