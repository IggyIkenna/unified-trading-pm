---
type: analysis
title:
  AUDIT — migration orphan-safety, beta-manifest goalpost preview, verified-delete gate, data sizing & schema-attribute
  completeness (the 'migrate once, never need a v10' verification harness) + MVP-tag / config-versioning reconciliation
epic: manifest_master
auditor: ikennaigboaka [slot-3·laptop]
date: "2026-06-10"
status: for-operator-review
parent_plan: active/master_data_canonicalisation_migration_catalogue_2026_06_07.md
source:
  - operator 2026-06-10 ("worried about GCS orphans after migration; want to check everything moved; dry-run dumped to a
    different place = a v9-beta manifest we can hook data-status/deployment-api/UI to in dev to see the goalposts;
    delete only paths that are in the manifest; re-audit read/write paths; know data size for download planning; migrate
    once — no v10 because we missed an attribute")
  - operator 2026-06-10 ("MVP tag to the catalogues (instrument/strategy/features/models/execution config); data-status
    MVP tick; instrument config like the sports-leagues / prediction-markets filter, everything-or-nothing at the family
    grain; config versioning as distinct from code versioning")
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
| 11  | **Audit candle left/right edge-timestamp from external sources**                                         | 🟡 **SSOT EXISTS, make recurring** | `codex/02-data/bar-boundary-candle-edge-convention.md` filed; add as standing check → **⑲** below            |
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

> **Operator ask**: "a registry of all available shard dynamics per AG (venue, data*type, instrument_type, …) —
> effectively a consolidation of the \_possible* manifest."

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
`captured + empty + failed + expected_unattempted`, so a venue/data*type we've never attempted shows as a
fully-enumerated \_honest* denominator, not as silently absent.

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

This already has a codex SSOT: **`codex/02-data/bar-boundary-candle-edge-convention.md`** (+
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
data*type/venue/instrument_type" is **exactly** the family-grain `is_mvp()` + the catalogue enumerator: the config
declares the \_family* (e.g. cefi×BINANCE×PERPETUAL×funding*rate is MVP), and `enumerate_expected_universe.py` populates
the \_leaves* (every live expiry/strike for that family, from the per-date catalogue rollup — never hardcoded). Nothing
new to invent; it's Phase-2 wiring.

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
