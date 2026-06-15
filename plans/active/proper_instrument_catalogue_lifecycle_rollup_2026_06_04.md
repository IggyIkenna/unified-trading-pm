---
title:
  "Proper instrument catalogue — lifecycle roll-up from per-date definitions + IS completeness gate (all asset groups,
  v9)"
created: 2026-06-04
parent_epic: instruments_master
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
      deployment-service (terraform) + instruments-service. assigned_vm: vm-cross-cutting. **TF AUTHORED
      deployment@98bee4b** — `terraform/gcp/lifecycle_catalogue_scheduler.tf` (NEW): per-AG `for_each`
      (cefi/defi/tradfi/sports/prediction) Cloud Run Job + Cloud Scheduler running `build_instrument_catalogue.py`
      (sports `--by-date-prefix`), 01:00 UTC daily (after IS FAST refresh, before downstream regens), bounded job. The
      two pre-existing schedulers (`catalogue_regen` / `instrument_catalogue`) run DIFFERENT scripts — this is the FIRST
      to schedule the lifecycle roll-up. **REMAINING (apply-gated)**: `terraform apply` + T+10min per-AG execution
      verify (infra apply pipeline).
- [ ] [CODE] P1. **All asset groups adopt the proper catalogue.** cefi / defi / tradfi / **sports (fixtures)** /
      prediction each produce + consume their `{env}/catalog.parquet` via the same roll-up. Verify each AG's
      `_enumerate_v2_*` reads it and emits `expected_unattempted` against the real, current universe. Per-AG slices
      drive via the sibling AG masters (cefi → slot-3, defi → slot-2, sports → slot-4, prediction → slot-5, tradfi →
      slot-6); vm-cross-cutting owns the shared roll-up + the gate. > **⚠️ PREDICTION + SPORTS are NOT a plain
      `build_instrument_catalogue.py --asset-group <ag>` run — they need a > granularity-aware producer (slot-5
      readiness audit 2026-06-04).** The generic roll-up emits one catalogue row per > `by_date` `instrument_key`, which
      is the WRONG grain for the bundled-atom AGs: **prediction's** captured atom is > the per-**cqg** bundle
      (`data_type=prediction_canonical_question_group`, `instrument_id=canonical_question_group`) > — a
      condition\*id-grain catalogue inflates the denominator by the cqg→condition_id fan-out. The prediction > producer
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
      prediction/sports need the > granularity-aware producer above. > **tradfi slice (slot-7, 2026-06-05): APPLIED** —
      651,985-row catalogue promoted to > `instruments-store-tradfi-prd-…/prod/catalog.parquet` (guard ACCEPT, exit 0;
      live enumerator ✓). Liveness > PROVISIONAL — see the capture-freeze FINDING below (tradfi recent capture
      degraded). **defi slice: APPLIED 2026-06-05** (4,171-row catalogue →
      `instruments-store-defi-prd-…/prod/catalog.parquet`, guard ACCEPT, exit 0; live enumerator ✓; 57 protocol-chain
      venues; frozen 2026-05-07 with a FULL last day = 3,599 active) on the pooled producer (~23 min for 64,724
      parquets; the prior single-pool run timed out at 30 min). > **Producer perf fix instruments-service@c340f2dc** —
      `_tune_download_pool` enlarges the GCS HTTP pool to > workers=16 (was throttled to ~8 → the "Connection pool is
      full" warning); ~2x faster full-corpus walk, verified > live (pool_maxsize 16). > **🟢 G1-ENUM SHAPE-AWARE
      ENUMERATOR DONE 2026-06-07 (vm-cross-cutting / slot-7):** the central fix the cross-AG over-fan FINDING called for
      — `is@6ea46565` `_row_data_types` filters the v2 enumerators to valid instrument-type/data-type pairs via the UAC
      matrix `uac@97c26dbe` (`valid_data_types_for_instrument_type`), preserving prediction grain-binding; cefi
      OPTION/COMBO leaves yield zero per-leaf rows and impossible combos are excluded. Per-AG slices (sports
      league-grain, prediction per-cqg) verify their matrix rows + re-run dry-runs before apply-write.
- [ ] [CODE] P2. **NICE-TO-HAVE (slot-7, 2026-06-07) — DeFi G1-ENUM validity is instrument_type-grain, not
      venue/protocol-grain.** The defi matrix is the UNION across `PROTOCOL_CAPABILITIES` per instrument_type, so a
      hybrid-protocol data_type leaks to every instrument of that type — e.g. GMX (`pool` + `perp_funding`) makes
      `pool`→`perp_funding` "valid" for ALL pools incl. Uniswap → some residual false `expected_unattempted` for non-GMX
      pools. Far smaller than the pre-G1-ENUM all-data_types fan-out, but a refinement: key DeFi validity per
      `(venue/protocol, instrument_type)` (the enumerator already has `instr.venue`). Provenance: G1-ENUM impl
      2026-06-07. Repo: unified-api-contracts + instruments-service. assigned_vm: vm-cross-cutting. parent_epic:
      instruments_master.
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
- [ ] [DATA] P1. **FINDING (slot-7, 2026-06-05) — IS `by_date` instrument-definition capture is FROZEN ~2026-05-21
      fleet-wide, and tradfi DEGRADED before the freeze.** Surfaced by the real apply (the catalogue is a faithful
      roll-up → it exposes the input's coverage horizon). cefi: latest captured day **2026-05-21** (16 days stale as of
      2026-06-05), last day FULL (3,473 active / healthy). tradfi: capture **degraded from ~16-18K instruments/day to
      ~2/day after 2026-05-04** (only `CBOE:INDEX:VIX` + `FX:SPOT_PAIR:KRW-USD` on recent days), then **stopped after
      2026-05-22**. defi: frozen **2026-05-07** (~31 days stale), last day FULL (3,599/4,171 active → catalogue usable).
      **Consequence**: the applied catalogues are honest **snapshots-as-of-the -freeze** — cefi's is usable (full last
      day); **tradfi's marks ~651K instruments "delisted"** (available*to ≤ 2026-05-04) because recent capture broke, so
      its liveness is NOT trustworthy until tradfi capture is fixed + the catalogue regenerated (monotonic guard makes
      the regen safe). The freeze is \_likely the deliberate pre-migration drain* (no instruments backfill until C-GREEN
      per `instruments_manifest_canonicalisation_2026_06_01.md`), in which case the catalogues refresh when capture
      resumes post-canonicalisation — BUT the **tradfi 16K→2/day degradation from 2026-05-04 is anomalous** (not a clean
      freeze) and must be diagnosed by the tradfi slice owner (slot-6 / `tradfi_manifest_canonicalisation` +
      `tradfi_master`). The completeness audit (capture_status) did NOT catch this (sparse days still `captured`;
      stopped days have no rows → not `attempted_failed`) — confirms the verdict is PROVISIONAL and motivates a
      **coverage-horizon check** (warn when the latest `by_date` day is > N days stale OR the per-day instrument count
      drops sharply) added to the producer/audit (**NICE-TO-HAVE**, slot-7). Repo: instruments-service (capture) + the
      tradfi vertical. assigned_vm: vm-cross-cutting (catalogue) / slot-6 (tradfi root-cause).
- [x] ✅ [CODE] P1. **Tradfi instrument-definition capture — diagnose+restore Databento, then add Massive as a DUAL
      reference source (remediation for the freeze FINDING above).** Repo: instruments-service. assigned_vm: slot-6 /
      tradfi vertical (`tradfi_master.md` + `tradfi_manifest_canonicalisation_2026_06_01.md`). **Status:
      BLOCKED-CREDENTIALS on Databento billing (operator, 2026-06-05) → Massive is the PRIMARY restore path, not just
      resilience.** Two parts: **(A) Databento re-run is BLOCKED — do NOT attempt** (the ~16-18K→~2/day degradation
      after 2026-05-04 then stop after 2026-05-22 cannot be fixed by re-running Databento: no billing budget right now —
      operator-gated `BLOCKED-CREDENTIALS`, awaiting [ack] on a Databento subscription/billing ask). Note the
      degradation diagnosis (is it billing-lapse vs adapter break?) for the record, but the fix is NOT a Databento
      re-run while billing is unavailable. **(B) PRIMARY — make Massive the tradfi reference source** so `by_date/`
      refills to today WITHOUT Databento (Massive is already the sanctioned tradfi dual-source market-data vendor → its
      subscription is live; confirm it covers the `/v3/reference/*` endpoints, which are billed separately from bars).
      Once Massive feeds `by_date/`, the catalogue producer (`build_instrument_catalogue.py`) rolls it up automatically
      (re-run the apply; monotonic guard accepts the growth). Massive is **Polygon.io-API compatible** — the existing
      `instruments-service/.../reference_data/adapters/tradfi/polygon.py` already implements the `/v3/reference/tickers`
      (equity/ETF/index) + `/v3/reference/options/contracts` (options chains) schemas + pagination, so build a
      `MassiveReferenceDataAdapter` (or re-point that Polygon-shaped reader at Massive's base URL + Massive
      Secret-Manager creds — DO NOT revive the **removed Polygon.io vendor**; Massive is the sanctioned vendor). Wire it
      into the IS reference factory + stamp `source=massive` per the source-provenance contract. **Coverage caveats
      (from `tradfi_massive_dual_source_2026_05_28.md`)**: equities/ETF/index + options chains are proven on Massive;
      **futures `/v3/reference/futures/contracts` returned 200+empty as of 2026-05-30** (subscription propagation —
      investigate the `s3://flatfiles/` path as the futures-reference alternative). Per the External-Data rule: if
      Massive futures-reference is still blocked, ship the adapter scaffold + unit tests anyway and file a
      `BLOCKED-CREDENTIALS`/`BLOCKED-UPSTREAM` ping (do not descope). Cloud-agnostic I/O; no `os.getenv`; QG-green
      before commit; commit+push+flip. Cross-ref: the freeze FINDING above +
      `data_source_provenance_all_asset_groups_2026_06_01.md`. — **✅ SHIPPED 2026-06-07 (slot-6).** Massive is now the
      tradfi reference source. **Canonicalisation lives in UAC** (operator decision — same canonical schema regardless
      of source): `unified_api_contracts/external/massive/{schemas,normalize}.py` raw→`InstrumentRecord` normalisers
      (equities/ETF via `/v3/reference/tickers`; **futures via `/futures/vX/contracts`** — the WORKING path,
      operator-confirmed; `/v3/reference/futures/*` 404s; FX; CBOE index + **SPX/VIX OPRA index options**),
      MIC→canonical-venue tagging, `DATA_SOURCE_TO_SECRET[massive]=MASSIVE_API_KEY` + `VENUE_TO_DATA_SOURCE[MASSIVE]`.
      Thin IS `MassiveReferenceDataAdapter` + factory `--source massive` routing (re-points CME/NASDAQ/NYSE/CBOE/FX off
      Databento; MASSIVE pseudo-venue key fetch) threaded CLI→handler→orchestrator→URDI→factory.
      **unified-api-contracts@12974b11 (PR#91) + instruments-service@c0f2f39c (PR#407)**; both `quality-gates.sh` green.
      **Backfill RUN TO COMPLETION** (`--source massive`, 2026-05-05→2026-06-07, 34 dates, all 5 venues, **~32.7K
      instruments/day, 0 write-failures**, prod `instruments-store-tradfi-prd`; previously-frozen dates 05-23+ refilled;
      spot-verified real/unique/typed). **Catalogue re-applied** (`build_instrument_catalogue.py --asset-group tradfi`):
      monotonic guard **ACCEPT 684,372 rows (was 651,985, +32,387)**, promoted `prod/catalog.parquet`; **liveness
      restored — 32,711 instruments current** (incl 31,282 SPX/VIX options) vs the freeze's "VIX + KRW-USD only"; v2
      enumerator parses it (684,372 entries). **C-#6 contract (2026-06-07)**: instrument-definition rows are
      producer-emitted (`pipeline_mode=BATCH_INSTRUMENTS_SERVICE`) → `source` is NOT vendor-stamped (batch
      `source⇔pipeline_mode` SSOT); the vendor is the adapter routing concern, not a per-row manifest tag.
- [ ] [DATA] P1. **FINDING (slot-6, 2026-06-07) — ICE futures + CME futures-OPTIONS not on Massive →
      BLOCKED-CREDENTIALS.** Massive Futures (Futures Developer plan, live) covers CME-group only (XCME/XNYM/XCEC/XCBT);
      ICE (Brent/softs, 8 roots) returns 0 contracts. Massive has **no options-on-futures product**
      (`/futures/vX/options` 404; all 8,000 futures products are `type=single`) — the old databento ~16-18K/day was CME
      ES _futures-options_. With Databento billing-blocked, both are uncovered (SPX/VIX OPRA _index_ options ARE
      captured on CBOE as the relevant vol-complex; VX _futures_ also absent on Massive → stays Yahoo-15m/Barchart,
      synthetic VIX forward derivable from VIX options). **Operator ask**: an ICE-futures + CME-futures-options
      reference source (or unblock Databento billing). Repo: instruments-service. assigned_vm: vm-tradfi.
- [ ] [CODE] P2. **FINDING (slot-6, 2026-06-07) — MTDS Massive market-data connector uses the WRONG futures endpoint.**
      `market-tick-data-service/.../adapters/tradfi/massive_tradfi_rest_connector.py` maps
      futures→`/v3/reference/futures/contracts` (404s); the working Massive path is **`/futures/vX/contracts`** (+
      `/futures/vX/products` for contract size / `unit_of_measure_qty`). Fix the MTDS connector's futures endpoint
      shape. Repo: market-tick-data-service. assigned_vm: vm-tradfi.

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

## Progress Log — R4-IS-freeze execution (2026-06-11, slot-4 autonomous)

> Master-plan ratified decision #4 (CITADEL): diagnose + resume IS definition collection, backfill the ~2026-05-21→now
> gap BEFORE any could-exist seed, then re-run catalogue roll-ups + v2 enumerates per AG. Cross-noted in
> `master_data_canonicalisation_migration_catalogue_2026_06_07.md` § R4.

### Root cause — THREE layers, not two

1. **The scheduled producers have been structurally DEAD for months (pre-drain layer A).**
   - `instruments-service-daily-trigger` (Cloud Scheduler, 08:30 UTC) → Workflows `instruments-service-daily` → tries to
     run Cloud Run **job `instruments-service` which does not exist** → HTTP 404 in step `run_instruments` — **FAILED
     every single day since ≥2026-03-13** (executions-retention horizon; likely longer). Its container args are also the
     pre-convention CLI shape (`--mode instruments --CEFI`), so it would be wrong even if the job existed.
   - `instruments-daily-backfill` (Cloud Scheduler, 21:07 Europe/London) → Cloud Function `trigger-instruments-job` (env
     `JOB_NAME=instruments-daily-backfill` — also names no existing Cloud Run job) — **zero invocation logs since its
     2025-11-13 deploy**; scheduler `status.code: -1`.
   - Definition capture was actually carried by **manually launched `instr-backfill-*` VMs**
     (`deployment-service/scripts/vm/launch-instruments-backfill-vm.sh`). Last runs: cefi+tradfi written 2026-05-22
     ~13:25–13:35Z; defi `day=2026-05-22` written 2026-05-27 ~13:28Z (to the LEGACY bucket — see layer C). When the
     instruments canonicalisation freeze stopped manual launches, capture froze — the "freeze ~2026-05-21" IS the end of
     manual runs, not a new break.
2. **The 2026-06-08 pre-migration drain (layer B)** then paused the two (already-dead) schedulers.
3. **Bucket-generation split (layer C, defi-specific).** The 2026-05-27 defi VM run wrote `day=2026-05-09…2026-05-22` to
   the **legacy** bucket `instruments-store-defi-<pid>` while the catalogue roll-up reads the canonical env-short bucket
   `instruments-store-defi-prd-<pid>` (stops 2026-05-08) — exactly the "defi frozen 2026-05-07" symptom in the FINDING
   above. tradfi prd was already restored to 2026-06-07 by the slot-6 Massive run (2026-06-07).

### NEW P0 BUG found+fixed during backfill — defi venue-tag underscore regression (c7d9bb2)

The defi re-run dropped **the entire fetched universe of 21 venues** (UNISWAP*V3-\*, PANCAKESWAP_V3-\*, AAVE_V3-\* all
chains, SUSHISWAP_V3-\*, AERODROME_V3-BASE, CAMELOT_V3-ARBITRUM, VELODROME_V2-OPTIMISM, …): `uniswap_v3.py` +
`aave_v3.py` built `\_venue_prefix = protocol_slug.replace("*",
"").upper()`→`PANCAKESWAPV3-BASE`, which the URDI venue filter (`urdi_reference_provider.\_fetch_one`) drops as unknown-venue. Commit c7d9bb2 (2026-05-23 — the day after the last good capture) renamed the canonical to the underscore form but **updated only the comments, not the code**. Worse, the completeness check then **excluded those venues from `expected`** ("fetched OK but 0 records after filtering") → days wrote "complete-looking" with 31/55 venues — the exact silent-thinning class the coverage-horizon check NICE-TO-HAVE above anticipates. **FIX shipped**: `\_venue_prefix
=
protocol_slug.upper()`in both adapters (instruments-service, slot-4; QG`--no-fix`exit 0 — sentinel 87f93ff; landed on LDR via`quickmerge
--agent
--files`as **instruments-service@0ae4e481**, Tier-C drain promotes). defi backfill re-run with the fix +`--force` over
2026-05-09→2026-06-11.

### Schedulers RESUMED (exactly these two — drain-exempt per ratified decision #4)

- `instruments-daily-backfill` → ENABLED 2026-06-11 (was PAUSED 2026-06-08 by the drain)
- `instruments-service-daily-trigger` → ENABLED 2026-06-11 (was PAUSED 2026-06-08 by the drain)
- NOT resumed: all `uts-prod-manifest-consolidator-instruments-*` + every market-data/consolidator scheduler (stay
  drained per the master plan).
- NOTE: resuming restores the pre-drain state, but both paths are still dead downstream (layer A) — see the
  producer-repair todo added below.

### Backfill runs (local, instruments-service `.venv`, ADC; per-VM shard isolation respected:

`VM_NAME=r4-is-backfill-local[-defi|-tradfi]` + `MANIFEST_PER_VM_SHARDS=true` → writes land in
`_index/per_vm/<tag>.parquet`, never CAS on the main `_index`)

| AG     | Window                | Command                                                         | Result (per-day counts in `/tmp/r4_is_backfill/*.log` on the operator host)                                                                                                                                                                                                                                                                  |
| ------ | --------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| cefi   | 2026-05-23→2026-06-11 | `--operation instruments --mode batch --asset-group CEFI`       | ✅ EXIT=0 — ~3.7–4.9K records/day across 15/16 venues; DERIBIT-COMBO upstream 400 (Deribit dropped `kind=combo` from `get_instruments`) every day → honest `attempted_failed` rows written                                                                                                                                                   |
| defi   | 2026-05-09→2026-06-11 | same + `--asset-group DEFI --force` (re-run with venue-tag fix) | ✅ EXIT=0 — ~5.9K records/day across 52–53/57 venues (bugged 31-venue first-pass days verified overwritten); persistent vendor-side failures all days: AAVE_V3-OPTIMISM (subgraph schema: `Query` has no field `reserves`), MORPHO-ETHEREUM/BASE (graphql 400), DRIFT-SOLANA (`data.api.drift.trade/stats/markets` 404) → `attempted_failed` |
| tradfi | 2026-06-08→2026-06-11 | same + `--asset-group TRADFI --source massive`                  | ✅ EXIT=0 — 31,683–31,685 records/day across 4/5 venues (NASDAQ/NYSE/CBOE/FX); **CME futures missing** — Massive `/futures/vX/{products,contracts}` now 404s (worked 2026-06-07; upstream/subscription regression) → recorded attempted_failed                                                                                               |

**Coverage VERIFIED (successor session, 2026-06-11 ~09:10 UTC)** — per-AG `by_date/` day listings are contiguous across
the entire freeze window: cefi 2026-05-01→2026-06-11 (42/42 days; backfilled days carry 15 venue dirs incl. the
canonical flat `day=X/venue=Y/` shape — the legacy writer's nested `day=X/day=X/venue=Y/` shape stops at 05-22), defi
2026-05-01→2026-06-11 (only hole = 2026-05-04, which PRE-dates the freeze window and the legacy-bucket era — out of R4
scope, noted), tradfi 2026-05-01→2026-06-11 (contiguous; 06-08+ days lack `venue=CME` per the upstream 404 above). defi
spot checks: day=2026-05-09 (52 venues), 05-10 + 05-15 (53) — the `--force` re-run did overwrite the bugged 31-venue
first pass.

**sports/prediction — REPORT ONLY (known producer gaps, per the master-plan R4 dispatch):** prediction
`instrument_availability/by_date/` last WRITE is 2026-05-12 (POLYMARKET; partitions are event/expiry-keyed so day=
values run to 2029) — the prediction IS backfill is already plan-homed as a **G5 post-`--apply`** step (prediction
canonicalisation plan ⑦/⑧ row) and its catalogue needs the cqg-grain producer (this plan's P0 above); sports
`sports_reference/by_date/` last footystats write 2026-06-01 (fixture/event-date-keyed), catalogue blocked on the
fixture-grain producer (same P0). Neither AG has a `prod/catalog.parquet` → no roll-up/enumerate attempted (matches the
enumerate dispatch scope cefi/defi/tradfi).

### Catalogue roll-ups re-run (post-backfill, 2026-06-11 09:13–09:25 UTC — local MAIN-clone `.venv`; cloud Cloud-Run path NOT used: `instruments-service:latest` is still the stale 2026-06-10T07:51 image whose `resolve_bucket_name` BucketNamingError failed the 01:00 lifecycle-catalogue-regen executions — master plan § G1 addendum; the image-watch monitor re-executes the cefi job when the new digest lands)

| AG     | by_date parquets walked | Catalogue rows (prev → new)    | Monotonic guard | Promoted to `prod/catalog.parquet` |
| ------ | ----------------------- | ------------------------------ | --------------- | ---------------------------------- |
| cefi   | 28,489                  | 213,990 → **220,222** (+6,232) | ACCEPT          | ✅ 09:16:35Z, exit 0               |
| defi   | 66,525                  | 4,171 → **6,853** (+2,682)     | ACCEPT          | ✅ 09:18:32Z, exit 0               |
| tradfi | 11,595                  | 684,372 → **686,348** (+1,976) | ACCEPT          | ✅ 09:24:35Z, exit 0               |

(defi's +64% jump is the venue-tag fix + the 05-09→06-11 re-capture restoring the 21 dropped venues to the lifecycle
universe; logs `/tmp/r4_is_backfill/catalogue_<ag>.log`.)

### v2 enumerator scan-only re-runs (NO `--apply-write`; `--catalog-path gs://instruments-store-<ag>-prd-…/prod/catalog.parquet`, window 2018-01-01→2026-06-11)

- The default `--max-writes-per-run 1_000_000` halt-safety trips in SCAN mode too (counts candidates) — both cefi+defi
  first runs aborted `max_writes_exceeded` at 1,000,001; re-ran with the cap at 500M.
- **cefi: 35,894,676 candidate rows** (per-instrument grain) against a present-set of 2,639,403 manifest rows. Reason
  distribution: EXPECTED_INSTRUMENT_NOT_LISTED 30,413,209 · blank-reason 2,583,053 · EXPECTED_INSTRUMENT_DELISTED
  1,701,209 · EXPECTED_PRE_VENUE_LAUNCH 1,197,205. (The CSV report write then OOM'd the 2GB tmpfs `/tmp` — counts above
  are from the scan itself, which completed; report-dir needs a disk-backed `--report-dir` on this host. Partial CSV
  purged.)
- **defi: 167,458,116 candidate rows** vs present-set 1,569,805. Distribution: EXPECTED_INSTRUMENT_NOT_LISTED
  142,200,664 · blank-reason 23,864,620 · EXPECTED_INSTRUMENT_DELISTED 1,392,832. (Same tmpfs CSV failure — counts from
  the completed scan; partial CSV purged.)
- **tradfi: 109,235,280 candidate rows** vs present-set from 686,348-instrument catalogue. Distribution:
  EXPECTED_INSTRUMENT_NOT_LISTED 71,590,541 · EXPECTED_INSTRUMENT_DELISTED 27,266,491 · blank-reason 10,378,248. Also
  emitted `G1-ENUM bundle-grain: no underlying for tradfi leaf 'ICE:COMBO:…'` warnings (ICE combo leaves dropped from
  roll-up — consistent with the ICE BLOCKED-CREDENTIALS finding above).
- **Scan-only verdict**: all three AGs enumerate cleanly off the fresh catalogues at per-instrument grain — the
  could-exist seed sizes are cefi ~35.9M / defi ~167.5M / tradfi ~109.2M rows. NO `--apply-write` was passed anywhere
  (the ratified G4 could-exist seed remains gated). Two scan-tooling notes for the seed owner: (a) the blank-reason
  bucket (in-coverage-but-absent) is the actual `expected_unattempted` payload — cefi 2.58M / defi 23.9M / tradfi 10.4M;
  (b) `--report-dir` must point at disk (not the 2GB tmpfs default) for full-universe CSV reports at this scale.

### New todos from R4 (capture-discoveries rule)

- [ ] [INFRA] P0. **Rebuild the IS daily definition producer** — the resumed schedulers point at dead infra: recreate
      the Cloud Run job (or repoint the `instruments-service-daily` Workflow / the `trigger-instruments-job` function)
      at a CURRENT image with the CURRENT CLI convention (`--operation instruments --mode batch --asset-group …`),
      per-VM shard env, and the post-2026-06-10 UAC cloud-providers.yaml (stale-image `resolve_bucket_name` class from
      the master plan G1 addendum). Until this lands the dailies only "succeed" at the scheduler layer. Repo:
      deployment-service (terraform/launcher) + instruments-service (image). assigned_vm: vm-cross-cutting. parent_epic:
      instruments_master. Provenance: R4-IS-freeze root-cause (Progress Log above).
- [ ] [DATA] P1. **tradfi CME futures reference gap from 2026-06-08** — Massive `/futures/vX/products` +
      `/futures/vX/contracts` 404 (worked on the 2026-06-07 slot-6 run; upstream endpoint/subscription regression).
      `BLOCKED-UPSTREAM-OUTAGE`: re-probe, and when restored re-run `--asset-group TRADFI --source massive` for the
      missing days so `venue=CME` refills; then regen the tradfi catalogue. Repo: instruments-service. assigned_vm:
      slot-6/tradfi vertical. Provenance: R4 backfill log 2026-06-11.
- [ ] [DATA] P2. **defi silent-thinning hardening** — the completeness check moves venues whose entire result was
      filtered out into "excluded from expected", so a 100%-drop bug looks complete. Make "fetched>0 but 0 after venue
      filtering" a SHARD COMPLETENESS FAILURE (attempted_failed), not an exclusion; pairs with the coverage-horizon
      NICE-TO-HAVE above. Repo: instruments-service (`engine/urdi_reference_provider.py` + completeness). Provenance:
      c7d9bb2 regression went undetected 19 days. assigned_vm: vm-cross-cutting.

### R5 (2026-06-15) — prod data-status shows 0 instruments: the MONITORING read goes blind on the stale consolidated index (operator-reported, deployment-ui screenshot)

**Symptom**: prod `uts-shared-deployment-api` → `instruments-service/data-status` shows Instrument Coverage Summary 0
rows / Data Coverage 0.0% / 14760 "missing shards" across all asset_groups — even though R4 (above) rebuilt the
catalogues + `_index` on 2026-06-11 and they are present in GCS.

**Diagnosis (this session)** — the DATA exists; the READ is blind:

- `instruments-store-cefi-prd` `_index/availability_index.parquet` = 40,714 rows / 18,731 `captured` (written 2026-06-14
  12:19); `prod/catalog.parquet` = 220,222 rows (06-11). defi-prd `_index` 196,535 / 69,255 captured. So the catalogue +
  index are real.
- UTL `read_availability_index` applies a ~120 s LIVE-trading staleness gate (`_resolve_consolidated_staleness_sec`).
  Consolidated index >120 s old ⇒ it DROPS the consolidated index and falls back to the per-VM shard merge.
  `_index/per_vm/` holds only 2 seed shards (`_legacy_seed.parquet`, `r4-is-backfill-local.parquet`) ⇒ ~0 rows.
  Reproduced locally: `DataStatusService._get_coverage_summary_sync('instruments-service')` ⇒
  `totals.shards=0, unique_instruments=0, asset_groups={}` while the parquet has 40,714 rows. The
  `uts-prod-data-status-rollup` job writes the empty `full.json.gz`/`coverage.json.gz` the UI caches.
- The consolidated index is stale because the `uts-prod-manifest-consolidator-instruments-*-cron` (`*/1`) are all PAUSED
  — **intentionally, per this plan's "NOT resumed … stay drained per the master plan"** + the held
  manifest-canonicalisation `--apply`. So the staleness is a CONSEQUENCE of the held-migration drain, not a pipeline
  failure. **Resuming consolidators / applying the migration / rebuilding the dead producers (P0 above) is the
  operator's `--apply`-gated call — left untouched (held-migration hard-stop).**
- **v9 (operator asked)**: prod is NOT on the v9 beta. `DATA_STATUS_BETA_MANIFEST_BLOB` is unset on
  `uts-shared-deployment-api` ⇒ reads the LIVE consolidated `_index` (mixed `schema_version` {4,8,9}; only ~320/40,714
  cefi rows are v9 — v9 migration ~1% done, gated behind the held `--apply`). The v9 projected index
  `_index/audit/projected_index_{ag}.parquet` exists but prod doesn't read it.

**Fix constraint**: UTL is the deployment-api BASE image (`FROM unified-trading-library:latest`), so a UTL change does
NOT reach prod without a UTL image rebuild + base-digest bump (slow). The migration-safe fix must be
**deployment-api-local** (ships fast via the new `deployment-api-main-deploy` auto-deploy).

- [ ] [DATA] P1. **Stale-tolerant data-status monitoring read** — in deployment-api
      `services/manifest_source.read_manifest_index`, when `read_availability_index(bucket)` returns empty AND the
      consolidated `_index/availability_index.parquet` exists (live staleness gate dropped a stale-but-valid index),
      read that consolidated blob DIRECTLY (no live-freshness gate) so the monitoring view shows the stale catalogue +
      its `written_at` age instead of 0. Monitoring read ≠ live-trading read: live readers keep the 120 s gate
      (unchanged); only the data-status path opts into stale tolerance. Migration-safe (read-only; no consolidator
      resume; no writes). Surface the staleness (the rows carry `written_at`; the UI freshness/`migration_in_progress`
      fields already exist). Repo: deployment-api. assigned_vm: vm-cross-cutting. parent_epic: instruments_master.
      Provenance: R5 (operator-reported 2026-06-15).

### R6 (2026-06-15) — producer rebuild: P0 layer-1 (dead image) FIXED; cloud catalogue-rollup has a remaining run_rollup error (layer-2)

The P0 "rebuild the dead IS producer" had **two layers**; layer 1 is now fixed:

1. **FIXED — no fresh IS image since 06-10**: `instruments-service-build` fails at the in-image `quality-gates` step
   (`log_section: command not found` / exit 127 — QG can't run without the PM harness/git in the image; **same
   fleet-wide bug as deployment-api**). So `:latest` was stuck at stale 2026-06-10 `0.2.1` (BucketNamingError) and every
   producer job ran it. Fix: added `_RUN_INIMAGE_QG` gate to `instruments-service/cloudbuild.yaml` (default true; build
   trigger sub = false) + force-synced to main → fresh **`instruments-service:0.5.0` / `89e7c86` / `:latest`** built +
   pushed 2026-06-15 12:13. `lifecycle-catalogue-regen-*` + daily jobs reference `:latest` → auto-use it (no repoint).
   **Verified the image blocker is gone**: the cefi job now imports + starts + runs (no import-time BucketNamingError).

2. **OPEN — cloud `lifecycle-catalogue-regen-cefi` still exits 1 in `run_rollup` (~75 s, NOT OOM)**: on the fresh image
   it fails fast inside `build_instrument_catalogue.py::run_rollup` (call at line 1117). Truncated cloud traceback (cuts
   at the `run_rollup(` frame, no exception line); a 16Gi/4cpu re-run failed identically in ~75 s → not memory. The SAME
   rollup ran GREEN **locally** on 06-11 (R4) → **cloud-Cloud-Run-env-specific** (env/startup/grpc-fork class), not a code
   regression. A local `--dry-run` won't reproduce (local works). Catalogue can still be refreshed via the R4 local path.

- [ ] [INFRA] P1. **Diagnose the cloud lifecycle-catalogue-regen run_rollup fast-fail on the fresh image** — the truncated
      cloud traceback hides the exception; add a top-level `traceback.print_exc()` flush (or `PYTHONFAULTHANDLER=1` + `-u`)
      in `build_instrument_catalogue.py::main` so the Cloud Run job logs the real error, then fix it (likely a Cloud-Run-env
      class — grpc/GCS fork-pool init, or a job env the local `.venv` has). Until fixed, the catalogue refreshes via the R4
      local-run path. Repo: instruments-service (+ deployment-service job env). assigned_vm: vm-cross-cutting. parent_epic:
      instruments_master. Provenance: R6 (2026-06-15).

**R6 follow-up (2026-06-15, same session) — the traceback-flush step is DONE; it narrowed the cause but revealed the real
blocker is logging suppression**: shipped `logger.exception` in `build_instrument_catalogue.py::main` (instruments-service@LDR+main),
rebuilt the image (`:latest` now the instrumented build), re-ran cefi with `PYTHONFAULTHANDLER=1`+`PYTHONUNBUFFERED=1`.
**Result: the cloud job emits ZERO log output** — no `run_rollup` INFO lines (run_id / "Found N by_date" / workers=), and
the `logger.exception("…FAILED…")` record never appears in `textPayload` OR `jsonPayload`. The ONLY output is Python's
C-level default-excepthook traceback (still truncated at the `return run_rollup(` frame) + "Container called exit(1)".
**Diagnosis**: `logging.*` is suppressed in the bare `python build_instrument_catalogue.py` Cloud Run Job invocation (UTL/
structured-logging handler not emitting in the job context — the service `ServiceBootstrap` that configures logging never
runs for a plain-script job), so every `logger.*` (incl. the new `logger.exception`) vanishes; only the excepthook reaches
stderr, and that single write is truncated. RULED OUT: BucketNamingError (image fixed), OOM (16Gi re-run failed identically
at ~75 s), task timeout (`timeoutSeconds: 1800`, dies ~75 s), catchable Python exception (the `except BaseException`
handler's `logger.exception` never fired → it's an uncatchable death OR logging-suppressed). The script runs GREEN locally
(R4 06-11), so it is **cloud-Job-invocation-specific**.

- [ ] [INFRA] P1 (supersedes the line above). **Make the cloud lifecycle-catalogue-regen log, then fix the real error.**
      Two sub-steps: (a) since `logger.*` is suppressed in the bare-script job, add `print(..., flush=True)` BISECTION
      markers before each `run_rollup` phase (storage-client init / bucket resolve / by_date listing / download-pool /
      dedup / monotonic-guard / promote-write) — `print` reaches stdout regardless of the logging config — to localize the
      death (PYTHONUNBUFFERED is already set on the job); OR call the service logging bootstrap / `logging.basicConfig(stream=sys.stdout)`
      at the top of `main` so `logger.*` emits in the job. (b) With the failing phase identified, fix it (suspects: a
      job-only env the local `.venv` provides, or a native grpc/pyarrow/GCS call). Until fixed, the catalogue refreshes via
      the R4 local-run path (works). Note: the cefi job currently carries diagnostic env `PYTHONFAULTHANDLER=1`+`PYTHONUNBUFFERED=1`
      (harmless; aids the next attempt). Repo: instruments-service + deployment-service (job env/bootstrap). assigned_vm:
      vm-cross-cutting. parent_epic: instruments_master. Provenance: R6 follow-up (2026-06-15).

---

## R7 — Data-status coverage semantics: genesis-clip the date denominator + headline CAPTURED vs ATTEMPTED (2026-06-14)

**Context.** Operator drill-down review surfaced two real defects in the Data Coverage card:
(1) `dates_expected` counted calendar days from the global search horizon even for young asset groups whose
data genesis is recent — penalising them for days that pre-date their existence ("dates_found/dates_expected
= 70.23%" was depressed by impossible days); (2) the headline showed a single ambiguous `completion_pct`
that conflated two distinct questions — *did we try everywhere we should* (attempt) vs *did we capture what
we tried* (capture) — and the operator was right that `empty_confirmed` (declared no-data) must not count
against capture.

**FIX #1 — genesis-clip the date denominator (SHIPPED to LDR; DEPLOYING to prod).**
`deployment_api/services/data_status/manifest.py` (~L491): after `effective_start = get_effective_start_date(...)`,
clip it forward to the service's earliest *observed* date (`index[service==svc].date.min()`) when that genesis
is later than the configured horizon. Young AGs (e.g. PREDICTION) are no longer charged for pre-genesis days.

**FIX #2 — headline CAPTURED vs ATTEMPTED, both labelled.**
- Backend (SHIPPED to LDR; DEPLOYING to prod): `manifest.py` now emits two new overall fields alongside the
  legacy ones — `overall_capture_coverage_pct` (= shards-weighted capture = `shards_found/shards_expected`) and
  `overall_attempt_coverage_pct` (venue-expected-weighted mean of per-category `attempt_coverage_pct`; falls
  back to `completion_pct_dates` when no shards expected). `empty_confirmed` does NOT count against capture
  (the 4-state honest_coverage SSOT + `attempt_coverage_pct` already exclude it — operator's point, confirmed).
- UI (CODED, tsc-clean, regression-tested; **NOT shipped from this host** — see blocker): `DataStatusTab.tsx`
  headline now leads with `overall_capture_coverage_pct` labelled **"captured"** + a conditional **"attempted"**
  line for `overall_attempt_coverage_pct` (tooltips explain the split), falling back to `overall_completion_pct`
  when the new fields are absent (older API). `api/client.ts` types the two optional fields. Regression test
  `tests/unit/data-coverage-headline.test.tsx` (vitest, pure `coverageHeadline()` contract) asserts the
  captured/attempted labels + fallback.

**Deploy.** deployment-api `main` force-synced from LDR → fires the `deployment-api-main-deploy` auto-deploy
trigger (genesis clip + new fields go live in prod; preserves beta env + 8Gi). The current (old) prod UI
ignores the new fields and shows the genesis-clipped `completion_pct_dates` — so FIX #1 is visible in prod
immediately; FIX #2's labelled split appears once the UI ships.

- [ ] [UI] P1. **Ship the R7 Data Coverage headline relabel from a clean env.** Change is preserved on
      `deployment-ui` branch `wip-preserve/r7-coverage-labels-ui` (tsc-clean; 3 files: DataStatusTab.tsx,
      api/client.ts, tests/unit/data-coverage-headline.test.tsx). **Blocked on THIS host only:** local vitest/
      playwright cannot run — `npm ci` then vitest dies with `Cannot find native binding @rolldown/binding-linux-x64-gnu`
      (npm optional-deps bug npm#4828; the suggested rm-lock+node_modules fix would rewrite the committed lock,
      declined). pw:L2 is a HARD-RULE gate for UI changes → ship via a UI-capable slot whose `npm ci` is healthy:
      cherry-pick/quickmerge from the wip-preserve branch, run QG + pw:L2, promote. assigned_vm: a UI-capable slot.
      parent_epic: instruments_master. Provenance: R7 (2026-06-14).

### R7 follow-up — prod `/api/data-status` full-CLI path 500s in-container (2026-06-15)

Verifying R7 live, the **turbo `/manifest`** path works (emits the new `overall_capture_coverage_pct` /
`overall_attempt_coverage_pct` fields — R7 confirmed deployed on image `71dd732`), but its rollup cache reads
0/0 for `prediction` (same empty-rollup root cause as R6). Forcing the non-turbo card endpoint
(`GET /api/data-status?...&force_refresh=true`) returns **HTTP 500**: the `run_data_status_cli` path shells out
to the deployment-service CLI which dies with `Error: Could not find configs directory. Run from
deployment-service or specify --config-dir` inside the Cloud Run image. So the full-CLI data-status path is
non-viable in-container; only the turbo path serves prod.

- [ ] [INFRA] P2. **Make the deployment-api in-container `run_data_status_cli` find its config dir** (or drop the
      CLI-subprocess path in favour of the in-process turbo compute). Either bundle `deployment-service/configs/`
      into the deployment-api image + pass `--config-dir`, or replace the `subprocess` CLI shell-out in
      `data_status_service.run_data_status_cli` with the in-process manifest compute the turbo path already uses
      (the CLI subprocess is the only reason the `force_refresh`/card path 500s). Repo: deployment-api.
      assigned_vm: vm-cross-cutting. parent_epic: instruments_master. Provenance: R7 follow-up (2026-06-15).
