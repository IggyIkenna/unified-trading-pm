---
title:
  "Proper instrument catalogue — lifecycle roll-up from per-date definitions + IS completeness gate (all asset groups,
  v9)"
created: 2026-06-04
parent_epic: epics/instruments_master.md
assigned_vm: vm-cross-cutting
status: active
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
locked_by: live-defi-rollout
locked_since: 2026-06-04
source:
  - cefi_manifest_canonicalisation_2026_06_01.md Dim-7 P3 (the v2-enumerator `catalog.parquet` has NO producer)
  - operator architecture decision 2026-06-04 (lifecycle catalogue = roll-up of the per-date `by_date/` instrument
    definitions; materialise + overwrite with a monotonic row-count promotion guard; v9, NOT v10)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# Proper instrument catalogue — lifecycle roll-up + IS completeness gate (all asset groups)

> **FOUNDATION-GATE (HARD).** instruments-service is the foundation MTDS/MDPS sit on; it must be **perfect before the
> MarketTick-data migration `--apply` runs**. This plan makes the **proper instrument catalogue** real (the
> time-independent known-instrument universe), derived from the maintained per-date definitions, so every downstream
> "could-exist" computation (expected_unattempted, coverage denominators, instrument-existence guards) reads a SSOT that
> is correct AND self-refreshing. **The MTDS migration DRY-RUN may proceed** (gated only on all code being available +
> the manifest being ready); the MTDS `--apply` is gated on this plan being GREEN. **v9, NOT v10** — this is part of the
> v9 canonicalisation, no new schema version is introduced.

## Why this exists — the catalogue has no producer, and a static snapshot is wrong two ways

The v2 expected-universe enumerator (`instruments-service/scripts/enumerate_expected_universe.py`) requires
`--catalog-path` = a `catalog.parquet` (`InstrumentCatalogEntry`: one row per instrument + `available_from`/
`available_to` lifecycle window). It is a **cumulative, all-instruments-ever lifecycle catalogue**, NOT a current
snapshot — the enumerator emits `EXPECTED_INSTRUMENT_DELISTED` for `date > available_to`, which is only possible if the
file **retains delisted instruments with `available_to` stamped**.

**Finding (slot-3, 2026-06-04):** workspace-wide grep shows **NO automated/recurring producer** writes that
`catalog.parquet` — only the launcher (`launch-expected-universe-v2-vm.sh`) + its test reference the path. So today it
is an operator-supplied, hand-maintained snapshot. A static snapshot is **stale two ways at once**: (1) missing newly
listed instruments, AND (2) wrong about what is still alive (a since-delisted instrument is shown alive → its cells are
marked `expected_unattempted` forever instead of `DELISTED`).

**The relationship (the fix):** the lifecycle catalogue is a **derivative of the maintained per-date definitions**. IS
already writes `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet` daily (the point-in-time,
reproducible-batch source — the "what existed on date t" slice; protected by the "never copy instrument definitions
between dates" rule). For each instrument: `available_from` = first day it appears across the `by_date/` snapshots,
`available_to` = last day. So the data already exists; the catalogue is a roll-up of it. Build it **from** `by_date/`
and it is correct + self-refreshing, with no separate artifact to drift.

## Operator design decisions (2026-06-04) — transcribe, do not re-litigate

1. **Materialise the proper catalogue** (do NOT switch to a transient in-enumerator read). Write it to the canonical
   path the launcher + enumerator already expect:
   `gs://instruments-store-{ag_short}-{env_short}-{project}/{env}/catalog.parquet` (per asset group). The existing
   enumerator/launcher then consume it unchanged.
2. **Overwrite on regen — NOT a separate file per day.** Regenerate → write to a **temp/new name** → assert row count is
   **strictly `>=` the current catalogue** (instrument rows grow **monotonically** — new listings add rows; delisted
   rows persist with `available_to` set) → on pass **promote** (replace canonical + delete the temp/previous); on a
   **regression (`<`)** treat it as a bug / incomplete regen → **keep the previous good catalogue, alert, do NOT
   overwrite**. (Caveat to encode: a legitimate corrective shrink — removing a bad instrument row — needs an explicit
   `ALLOW_CATALOGUE_SHRINK` override; the ratchet is a safety default, not an absolute.)
3. **v9, NOT v10.** Part of the v9 canonicalisation; no schema-version bump.
4. **Foundation gate.** This must be GREEN before the MTDS data migration `--apply`. The MTDS dry-run + manifest-rebuild
   dry-run may still run (gated on code-ready + manifest-ready), but the irreversible `--apply` waits on this.

## The four requirements (operator, 2026-06-04)

- [x] ✅ [AUDIT] P0. **IS completeness gate — `instrument_availability/by_date/` is 100% complete (no
      `attempted_failed`) per the UAC expected shard universe (venues × data_types × dates), ALL asset groups + sports
      fixtures (same service).** Build/extend a completeness check that, per AG, diffs the captured `by_date/`
      instrument-definition cells against UAC's expected `(venue × instrument-defn data_type × date)` universe and
      reports `attempted_failed`/missing. **DELICATE — cannot be fully trusted until the manifest + data migrations
      run:** the current `_index` is pre-migration (v8/mixed; cefi 100% v8, see cefi plan), so a "complete" verdict now
      is provisional. Run it BEST-EFFORT now (surface gross gaps) and RE-RUN as a hard gate AFTER the IS manifest
      canonicalisation lands. No catalogue/enumerator output can be trusted while this is RED for an AG. Repo:
      instruments-service (+ UAC for the expected-universe definition). assigned_vm: vm-cross-cutting. — **SHIPPED (tool
      built, provisional)** instruments-service@4026d79e | `scripts/audit_instrument_definition_completeness.py` reads
      the IS availability `_index`, tabulates instrument-definition cells by `capture_status`, surfaces every
      `attempted_failed` cell as a gap (per-venue counts + `(venue,date,data_type)` sample), verdict
      `COMPLETE     (provisional)`/`INCOMPLETE` (exit 0/2). Pure `summarise_completeness()` unit-tested (status
      tabulation, attempted_failed surfacing, blank→captured coercion, empty index). QG `--no-fix` exit 0; 15/15 tests
      green. **Best-effort cefi run EXECUTED 2026-06-05** (read-only, single `_index` read): **30,803
      instrument-definition cells, ALL `captured` — 0 `empty_confirmed` / 0 `attempted_failed` / 0
      `expected_unattempted` → VERDICT `COMPLETE (provisional)`, exit 0.** No external/venue API calls (reads the
      consolidated availability manifest only). PROVISIONAL stands: this proves nothing FAILED among the cells the
      pre-migration `_index` tracks, NOT that the full UAC expected universe is covered — the **hard-gate** re-run (full
      `venue × instrument-defn data_type × date` expected-universe diff) is still post-IS-manifest-canonicalisation.
      (The run was initially blocked by a stale UAC dep worktree — 317 behind LDR carrying a 2-week-old foreign VM
      commit `02b83705` — resolved by realigning that worktree to LDR per operator decision 2026-06-05.)
- [x] ✅ [CODE] P0. **Roll-up producer — derive the lifecycle catalogue from the per-date `by_date/` definitions.** New
      instruments-service script/job (per AG, AG-agnostic core): walk
      `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet`, aggregate to one
      `InstrumentCatalogEntry` row per instrument (`instrument_id`, `instrument_type`, `venue`, `chain`/`league_id`,
      `available_from`=min present day, `available_to`=max present day or null if present on the latest day), write
      `{env}/catalog.parquet` with the **monotonic-guard promotion** (req-2 mechanism above). Reuse the existing
      `InstrumentCatalogEntry` / `_catalog_from_dataframe` contract the enumerator already consumes (no schema drift).
      Cloud-agnostic I/O (`get_storage_client`, `resolve_bucket_name` — never inline `gs://`). +unit tests (roll-up
      lifecycle math; monotonic-guard accept/reject/override). Repo: instruments-service. — **SHIPPED**
      instruments-service@4026d79e | `scripts/build_instrument_catalogue.py`. AG-agnostic core:
      `build_catalogue_dataframe()` (pure lifecycle math — first/last day windows, `available_to=None` when present on
      the latest snapshot day) + `evaluate_monotonic_guard()` (pure: first-run/grow/equal accept, shrink reject,
      `--allow-catalogue-shrink` override) + `promote_catalogue()` (temp-first write → guard → copy-over canonical →
      delete temp). Writes the canonical path the launcher (`launch-expected-universe-v2-vm.sh` L165-174) + v2
      enumerator read: `get_write_bucket_name("instruments", ag)` + `{DEPLOYMENT_ENV}/catalog.parquet`. Output columns
      consumed by `enumerate_expected_universe._catalog_from_dataframe` (no schema drift — verified by a test that feeds
      the rolled-up frame straight into the enumerator helper). Cloud-agnostic via `get_storage_client`/
      `get_write_bucket_name`. v9, NOT v10. **By_date download is concurrent** (instruments-service@d00fe2d9 —
      `ThreadPoolExecutor`, `MAX_DOWNLOAD_WORKERS=16`, I/O-bound per coding standards; the single-threaded walk timed
      out on the full corpus) + a `--max-blobs` DIAGNOSTIC cap that **forces dry-run** (a truncated walk is incomplete →
      never promotable). QG `--no-fix` exit 0; 18/18 tests green; ruff + import-patterns clean. **Live cefi dry-run
      PROVEN end-to-end 2026-06-05 on real prod GCS** (`instruments-store-cefi-prd-central-element-323112`): concurrent
      walk of `by_date/` → rolled up instruments → monotonic guard `ACCEPT (no_prior_catalogue)` →
      `[dry-run] would     promote …/prod/catalog.parquet`, exit 0. **No external/venue API calls** — reads our own
      already-captured `by_date/` parquets (the catalogue is a roll-up of stored data, not a re-fetch); does NOT require
      the manifest migration. NOTE: `list_blobs` over the whole prefix is the dominant cost for the full corpus → the
      full unbounded run belongs on the Phase-2 VM trigger, not a laptop.
- [ ] [INFRA] P1. **Trigger on every instruments update (per AG; reference data → generally ≤ a few times/day).** Wire
      the roll-up to run after each IS instrument-definition write per AG (event-driven off the IS write, or a frequent
      scheduler keyed to the IS update cadence — pick per the IS update mechanism; do NOT fire-and-forget). The v2
      enumerator's recurring run (cefi Dim-7 P3, currently BLOCKED) then reads an always-fresh catalogue. Repo:
      deployment-service (terraform) + instruments-service. assigned_vm: vm-cross-cutting.
- [ ] [CODE] P1. **All asset groups adopt the proper catalogue.** cefi / defi / tradfi / **sports (fixtures)** /
      prediction each produce + consume their `{env}/catalog.parquet` via the same roll-up. Verify each AG's
      `_enumerate_v2_*` reads it and emits `expected_unattempted` against the real, current universe. Per-AG slices
      drive via the sibling AG masters (cefi → slot-3, defi → slot-2, sports → slot-4, prediction → slot-5, tradfi →
      slot-6); vm-cross-cutting owns the shared roll-up + the gate. > **⚠️ PREDICTION + SPORTS are NOT a plain
      `build_instrument_catalogue.py --asset-group <ag>` run — they need a > granularity-aware producer (slot-5
      readiness audit 2026-06-04).** The generic roll-up emits one catalogue row per > `by_date` `instrument_key`, which
      is the WRONG grain for the bundled-atom AGs: **prediction's** captured atom is > the per-**cqg** bundle
      (`data_type=prediction_canonical_question_group`, `instrument_id=canonical_question_group`) > — a
      condition_id-grain catalogue inflates the denominator by the cqg→condition_id fan-out. The prediction > producer
      must roll up `market_lifecycle/by_canonical_group/` (the per-cqg lifecycle IS already writes, >
      `orchestrator.py:3380-3456`) → one `CatalogRow` per cqg, and the enumerator must emit ONLY >
      `prediction_canonical_question_group` for prediction. Full spec + the gated-upstream (0-object >
      `by_canonical_group/` until the IS prediction backfill) dependency: >
      `prediction_manifest_canonicalisation_2026_06_01.md` § "⑦ PREDICTION SLICE". Sports has the analogous per-league >
      vs per-fixture grain question — confirm with slot-4 before a plain run. > **cefi slice progress (slot-7,
      2026-06-05):** (a) **enumerator-read VERIFIED** — integration test > (instruments-service@eb00e2ad,
      `test_cefi_enumerator_reads_rollup_catalogue_and_emits_expected_unattempted`) > proves producer →
      `_catalog_from_dataframe` → `enumerate_v2(asset_group=cefi)` emits NOT_LISTED / DELISTED / >
      `expected_unattempted` (and skips captured cells) correctly against the rolled-up catalogue. (b) **cefi
      catalogue > APPLIED 2026-06-05 (213,990-row catalogue promoted; guard ACCEPT; live enumerator check ✓; data_type
      null for single-grain cefi)** — real producer run over the full cefi `by_date/` corpus (28,174 parquets)
      promoting > `instruments-store-cefi-prd-…/prod/catalog.parquet`. Migration-stability confirmed: the IS
      canonicalisation > re-keys `by_date` PATHS (`pipeline_mode=` partition, `category=`→`asset_group=`) + re-versions
      the `_index` to v9, > but it is a **path-only `gcs_copy_object` re-key** — instrument identity/lifecycle columns +
      which-instruments- > existed-when are unchanged, so the catalogue CONTENT is migration-stable (a now-built
      catalogue == a > post-migration one; the monotonic guard makes any regen safe). Follow-up: confirm the producer's
      `by_date/` walk > prefix still resolves once the objects gain the `pipeline_mode=` partition (top prefix + `day=`
      regex are robust; > verify post-migration). defi / tradfi remain plain `--asset-group <ag>` runs;
      prediction/sports need the > granularity-aware producer above.
- [ ] [CODE] P1. **FINDING (slot-7, 2026-06-04) — two divergent catalogue read-paths must be reconciled.** The
      standalone v2 enumerator (`enumerate_expected_universe.py --catalog-path`) + the launcher
      (`launch-expected-universe-v2-vm.sh` L165-174) read **`{env}/catalog.parquet`** (the path this plan's roll-up
      producer now writes). But the UTL runtime reader `unified_trading_library/instruments_catalog_reader.py`
      `_CATALOG_BLOB` reads a **different** object — `reference_data/instruments/{asset_group}/all.parquet` — which is
      what the _current-snapshot_ `CatalogueBuilder.write_to_gcs` (instruments-service
      `reference_data/catalogue/catalogue_builder.py`) emits (a live URDI fetch, NOT a lifecycle roll-up). So the MTDS
      preflight / UTL-side "could-exist" cross-ref reads a snapshot at one path while the enumerator reads the lifecycle
      catalogue at another → they can disagree on whether an instrument exists. Reconcile in Phase 3: point
      `instruments_catalog_reader._CATALOG_BLOB` at `{env}/catalog.parquet` (the roll-up output) AND decide
      CatalogueBuilder's fate (retire its all.parquet write, or keep it as a distinct current-snapshot artifact with a
      clearly-different consumer). Repo: unified-trading-library + instruments-service. assigned_vm: vm-cross-cutting.

## Phased DAG + gates

1. **Phase 0 — completeness audit (best-effort now → hard gate post-migration).** Req-1. Output: per-AG
   complete/incomplete verdict + gap list. Gate: no downstream catalogue trust while RED.
2. **Phase 1 — roll-up producer + monotonic guard.** Req-2. Gate: unit tests green + a dry-run roll-up over a real AG
   produces a catalogue that matches a hand-spot-check of `by_date/` lifecycle for sample instruments.
3. **Phase 2 — trigger wiring.** Req-3. Gate: observed re-generation on a real IS update + the monotonic guard rejects a
   truncated input in test.
4. **Phase 3 — all-AG adoption + enumerator unblock.** Req-4. Gate: each AG's v2 enumerator reads the fresh catalogue;
   cefi Dim-7 P3 enumerator-cron unblocks (now points at a self-refreshing catalogue).
5. **GATE → MTDS migration `--apply`.** Foundation-completion-gate: IS catalogue GREEN for the AG before its MTDS
   `--apply`. Dry-runs are NOT gated on this.

## Codex SSOT updates (required before archival)

- `codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — add the lifecycle-catalogue roll-up contract
  (catalogue = roll-up of `by_date/` definitions; canonical path; monotonic-guard regen; v2-enumerator consumer).
- `codex/02-data/availability-manifest-and-data-status.md` — note the catalogue as the could-exist-universe SSOT feeding
  `expected_unattempted`.

## Cross-references + supersedes

- **SUPERSEDES** `cefi_manifest_canonicalisation_2026_06_01.md` Dim-7 P3 (enumerator-cron, BLOCKED-OPERATOR-DECISION):
  the recurring enumerator is no longer the unit of work — this plan is. Once Phase 3 lands, the cefi Dim-7 P3 cron is a
  thin wrapper over the now-fresh catalogue.
- **Per-date denominator refinement (separate, smaller P3 — tracked in cefi plan):** the deployment-api coverage
  denominator (deployment-api@d55bcb6) reads ONE current IS availability snapshot, not the per-date `by_date/`
  definitions, so it is not per-date point-in-time-correct (the universe as-of each historical date). Optional
  follow-up; NOT part of this foundation plan.

## Pre-audit / open questions for the executor

- Confirm the exact `by_date/` instrument-definition columns per AG (and the sports-fixtures analog) before writing the
  roll-up aggregation keys.
- Confirm whether the IS `_index` (post-canonicalisation) is the right completeness source for Req-1, or whether the
  expected-universe must come from UAC `DATA_TYPES_BY_ASSET_GROUP` × the IS catalog × dates (mirror
  `enumerate_expected_universe._enumerate_v2_*`).
- Confirm the canonical catalogue object path matches `resolve_bucket_name` output for `kind="instruments-store"` (the
  launcher hardcodes `instruments-store-{ag_short}-{env_short}-{project}/{env}/catalog.parquet`; the producer must write
  exactly where the enumerator reads).
