---
doc_type: audit-instruction
title: features_and_ml_master_audit_instructions
summary:
  Weekly audit of features-service (8 feature families), ml-service (inference + training), the IS→features contract,
  and greeks-service as a data-pipeline derivation peer (NOT ml) — enforcing all feature schemas live in UAC (no local
  defs), calculator math-drift, registry SSOT, feature_writer stamp/versioning, and feature-formula-versioning doc↔code
  alignment.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-service,
    features-service,
    greeks-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: [audit, features, ml, uac, manifest, data-correctness, verification]
related: []
created: "2026-05-22"
tier: L1
parent_epic: features_and_ml_master
cadence: weekly (minimum)
verifier:
lifespan:
type: audit-instructions
epic: features_and_ml_master
assigned_vm: vm-ml
last_updated: 2026-05-29
---

# Features + ML Master — Audit Instructions

## Epic Scope

features-service (8 feature families: DeFi, CeFi, TradFi, Sports, Predictions, Macro, On-Chain, Cross-Asset), ml-service
(inference + training pipelines), IS→features contract. All feature schemas must be in UAC; no local definitions.
**greeks-service** is also in scope as a **data-pipeline derivation peer of features-service** (computes option
Greeks/IV from market-data marks) — it sits in the **data-pipeline layer, NOT ml** (ml is strictly downstream of it).
See [§ Greeks-service](#greeks-service-data-pipeline-derivation--batch--live) for its dedicated checklist.

## Triggers

- Weekly (minimum cadence)
- After model retrain (verify training pipeline manifest compliance)
- When strategy-service reports feature shape mismatch at inference time
- After any UAC feature schema change
- After `ml_repo_consolidation` completes (verify merged repo structure)
- **After any edit to `features_service/delta_one/app/calculators/`** (math drift potential — items r, s)
- **After any edit to `features_service/delta_one/app/features/registry.py`** (registry SSOT drift — items i, j, o)
- **After any edit to `features_service/delta_one/app/core/feature_writer.py`** (stamp / metadata drift — items k, l,
  live-versioning)
- **After any edit to `/codex/02-data/feature-formula-versioning.md` or
  `/codex/04-architecture/artifact-versioning.md`** (doc-code drift — items p, t)
- **After a `live-defi-rollout` push to features-service** (composes with CI-Verification HARD RULE)
- **After the FIRST successful features-service write to any `gs://features-delta-one-{ag}-{pid}/`** — that write is the
  only signal that unblocks items (l) / (live-versioning) / (batch-live). Until it happens, those items stay BLOCKED —
  see `plans/active/issues/features_service_defi_data_loading_blockers_2026_05_29.md`.

## Checklist

- [ ] (a) **All 9 computation-type families have a CLI entry**: the `--feature-family` argument in `features-service`
      CLI must accept all 9 currently-shipped families (matching subdirectories in `features_service/` excluding
      `api`/`cli`/`common`): `calendar`, `commodity`, `cross_instrument`, `delta_one`, `multi_timeframe`, `onchain`,
      `performance_features`, `sports`, `volatility`. Find:
      `features-service --feature-family $UNKNOWN --help 2>&1 | head -3` returns the canonical list. Verify: every
      subdirectory matches a CLI choice. **Asset-group coverage** (CEFI / DEFI / TRADFI / PREDICTION) is enforced per
      family via the `--asset-group` argument — NOT a per-family directory. Computation-type axis ≠ asset-group axis.

- [ ] (b) **IS→features contract**: `is_features_contract_audit_2026_05_20.md` (archived at
      `plans/audit/archive/is_features_contract_audit_2026_05_20.md`) — confirm findings closed at archive time + no
      follow-up RED items active in `plans/active/`

- [ ] (c) **ml-service inference end-to-end test**: inference path has a test that exercises the full pipeline (features
      → model → signal) with mock data. Find: `rg "inference|predict" ml-service/tests/ --include="*.py" -l` (or merged
      ml-service path post-consolidation)

- [ ] (d) **Training pipeline manifest compliance**: training outputs emit manifest rows with correct `schema_version`,
      `asset_group`, and `available_at` (write-time, not read-time derivation). Read: training pipeline output path —
      verify `record_captured()` called with `cluster_*` kwargs

- [ ] (e) **Feature schemas in UAC**: no local feature schema definitions in features-service or ml-service. Grep:
      `rg "class.*Schema|dataclass" features-service/ --include="*.py"` — every schema must import from UAC

- [ ] (f) **No os.getenv() in feature computation**: all config via `UnifiedCloudConfig`. Grep:
      `rg "os\.getenv" features-service/ ml-service/ --include="*.py"` — should be 0 hits

- [ ] (g) **PYTEST_UNIT_DIR override wired**: `quality-gates.sh` uses `PYTEST_UNIT_DIR="tests/"` to collect all
      per-family tests (not just root-level `tests/unit/`). Check: `features-service/scripts/quality-gates.sh` — verify
      override is set before `source base-service.sh`

- [ ] (h) **ml-service repo consolidation complete**: `ml_repo_consolidation_2026_05_19.md` archived at
      `plans/archive/2026_05/ml_repo_consolidation_2026_05_19.md` (= complete). Verify merged repo at `ml-service/` has
      no duplicate code paths or conflicting imports

### Registry SSOT + Formula Versioning

> Shipped 2026-05-28 across 5 phases in `plans/active/features_registry_status_versioning_2026_05_28.md`. Codex SSOT:
> `/codex/02-data/feature-formula-versioning.md`.

- [ ] (i) **Registry covers every CALCULATOR_REGISTRY group**: every key in
      `features_service.delta_one.app.calculators.CALCULATOR_REGISTRY` must have ≥1 `FeatureSpec` entry in
      `features_service.delta_one.app.features.registry._SPECS`. A calculator added without registry entry =
      un-versioned, un-trackable feature. Run:
      `cd features-service && .venv/bin/python -c "from features_service.delta_one.app.calculators import CALCULATOR_REGISTRY; from features_service.delta_one.app.features.registry import build_full_registry; reg = {s.group for s in build_full_registry()}; missing = set(CALCULATOR_REGISTRY) - reg; print('missing:', sorted(missing))"`
      Verify: empty `missing` set. Currently 34/34 groups covered (1,382 specs).

- [ ] (j) **Status + Implementation closed-set Literals haven't drifted**: the `Status = Literal[...]` and
      `Implementation = Literal[...]` declarations in `registry.py` must match exactly what
      `/codex/02-data/feature-formula-versioning.md` § "Status field" + § "FeatureSpec extensions" document. A silent
      widening of either set breaks the test-gate filter (item m) + the consumer pin pattern. Find:
      `grep -A 10 "^Status = Literal\|^Implementation = Literal" features_service/delta_one/app/features/registry.py`
      Verify: Status set = `{verified, tested, in_dev, listed, blocked, deprecated, need_data}`; Implementation set =
      `{custom, ta_lib, pandas_std, numpy_std}`.

- [ ] (k) **Formula version stamped on every parquet write path**: `feature_writer._write_parquet` MUST (1) call
      `_resolve_group_version` for the group, (2) include `"feature_group_version": str(version)` in the `partition`
      dict it passes to `data_sink.write(...)`, AND (3) pass
      `metadata=self._build_parquet_metadata(df, feature_group, version)` to `df.write_parquet(...)`. There must be NO
      per-row `feature_group_version` column on the DataFrame (operator directive 2026-05-28 — millions-of-files cost).
      Both batch and live writer paths. Find:
      `rg "_resolve_group_version|_build_parquet_metadata|feature_group_version" features_service/delta_one/app/core/feature_writer.py`
      Verify: helpers invoked from `_write_parquet`; `feature_group_version` is a partition dict key (not a
      `with_columns(...)` call); no `_stamp_version_columns` helper exists.

- [ ] (l) **Path partition + file-level metadata round-trip on real GCS parquets**: sample a recent parquet from
      `gs://features-delta-one-{ag}-{pid}/` and verify the version is stamped in BOTH the path AND the file-level
      metadata, and that they AGREE. Drift = path/metadata mismatch (writer bug), or legacy un-stamped writes sneaking
      back in. Run:
      `python -c "import re, pyarrow.parquet as pq; path='<gs path>'; pf = pq.ParquetFile(path); meta = {k.decode(): v.decode() for k,v in (pf.metadata.metadata or {}).items() if not k.startswith(b'ARROW')}; path_v = re.search(r'feature_group_version=(\d+)/', path).group(1); print('path:', path_v, 'meta:', meta.get('feature_group_version')); assert path_v == meta['feature_group_version'], 'PATH/METADATA MISMATCH'; print('metadata:', meta)"`
      Verify: (a) GCS path contains `feature_group_version={N}/` segment between `feature_group=...` and
      `timeframe=...`; (b) file-level metadata has 3 keys: `feature_group_version`, `feature_column_versions`,
      `feature_group`; (c) path version int == metadata version int; (d) no `feature_group_version` COLUMN on the
      parquet's schema; (e) sentinel `0` only appears on groups without registered specs (currently should be empty —
      Phase 2 covered all 34).

- [ ] (m) **2.4 / 2.6 / 2.7 parametrize on `status ∈ {verified, tested}` only**: the Phase 2 mass-catalogue (1,329
      "listed" specs) MUST NOT false-fail these gates. Drift = someone removes the filter; CI suddenly red on un-audited
      specs. Find:
      `rg "build_full_registry|status in" tests/delta_one/unit/test_registry_invariants.py tests/delta_one/unit/test_distribution_sanity.py tests/delta_one/unit/test_cross_timeframe_sanity.py`
      Verify: every `@pytest.mark.parametrize` over specs filters on `s.status in {"verified", "tested"}` or
      `s in _VERIFIED_GROUPS` equivalent.

- [ ] (n) **FINDING-B group-level fail-fast isolation**: `BatchHandler._process_groups` MUST return `True` if ANY group
      succeeded (not `all(...)`) AND `_process_one_group` must call `record_group_failed(...)` on each failure path
      (orchestrator returned False, emission policy rejected, exception). Drift = single-group exception poisoning the
      whole batch. Find:
      `rg "record_group_failed|succeeded_groups|failed_groups" features_service/delta_one/cli/handlers/batch_handler.py features_service/delta_one/cli/handlers/_failed_group_manifest.py`
      Verify: helper invoked on all 3 failure paths; aggregator returns `True if succeeded_groups else False`; manifest
      carries per-group success/failure rows with `PipelineMode.BATCH_DATABENTO`.

- [ ] (o) **"Listed" promotion backlog is monitored**: the count of specs at `status="listed"` should TREND DOWNWARDS
      over time as we hand-audit each group. If the backlog grows without verifies/tested promotions, the registry is
      decaying into a write-only catalogue. Run: `features-status` (from features-service venv) — read the bottom-line
      `listed (un-audited): N` count. Verify: snapshot N week-over-week. Trend: ↓ (decreasing). At 2026-05-28 baseline:
      `listed=1329, verified=28, tested=19`. Audit window: if `listed` count hasn't decreased in 4 weeks, flag the audit
      owner to promote at least the high-priority specs.

- [ ] (p) **Codex-named implementation files exist at documented paths**: `/codex/02-data/feature-formula-versioning.md`
      § "The four files" claims 4 concrete paths exist. Drift = file rename / move without codex update. Run:
      `for f in features_service/delta_one/app/features/registry.py features_service/delta_one/app/features/formula_hash.py features_service/delta_one/app/features/status_report.py features_service/delta_one/app/core/feature_writer.py; do test -f features-service/$f && echo "OK $f" || echo "MISSING $f"; done`
      Verify: all 4 OK. Any MISSING ⇒ update the codex doc or restore the file.

- [ ] (q) **Total Phase 1-4 test count is at or above baseline (8,400)**: regression check against silent test removal.
      The 6 test files Phase 1-4 added/extended: `test_registry_invariants.py`, `test_distribution_sanity.py`,
      `test_cross_timeframe_sanity.py`, `test_registry_status_versioning.py`, `test_feature_writer_versioning.py`,
      `test_status_report_cli.py`. Run:
      `cd features-service && timeout 300 .venv/bin/python -m pytest tests/delta_one/unit/test_registry_invariants.py tests/delta_one/unit/test_distribution_sanity.py tests/delta_one/unit/test_cross_timeframe_sanity.py tests/delta_one/unit/test_registry_status_versioning.py tests/delta_one/unit/test_feature_writer_versioning.py tests/delta_one/unit/test_status_report_cli.py -q 2>&1 | tail -3`
      Verify: `passed >= 8400`, `failed == 0`. Drift = count drops without explicit removal commit; investigate
      `git log --oneline -- tests/delta_one/unit/`.

- [ ] (r) **Drift detection baseline: no math change without `formula_version` bump**: run
      `features-status --check-drift`, diff against the previously-recorded baseline. Every hash change MUST be paired
      with a `formula_version` bump in the same commit. Hash changed + version didn't = the silent-rewrite anti-pattern.
      Run:
      `cd features-service && features-status --check-drift > /tmp/current_baseline.txt; diff /tmp/baseline_2026_05_28.txt /tmp/current_baseline.txt`
      Verify: every diff line where the hex changed has a matching `git log` entry that ALSO bumped the relevant
      `FeatureSpec.formula_version`. Pure-comment edits (canonicaliser strips them) MUST NOT show up — if they do, the
      canonicaliser regressed.

- [ ] (s) **Bump policy enforcement (formula vs config)**: any `feat:` / `feat!:` / `fix:` commit touching a
      `_calculate_features` method in `features_service/delta_one/app/calculators/` should ALSO bump the corresponding
      group's specs' `formula_version` in `registry.py`. Drift = math edit that ships without version bump (silent
      v1-tagged-but-v2-formula rows in GCS). Run:
      `git log --since='last audit' --pretty=format:'%H %s' -- features_service/delta_one/app/calculators/ | while read sha msg; do git show --stat $sha -- features_service/delta_one/app/features/registry.py | grep -q "formula_version" || echo "MISSED BUMP: $sha $msg"; done`
      Verify: zero `MISSED BUMP` lines. Config-only edits (window size, threshold value) are EXEMPT — those are at the
      consumer-config layer, not the formula layer (operator directive 2026-05-28: "rsi 14 vs rsi 18, that is config
      change").

- [ ] (t) **CLAUDE.md `Service architecture` § "Feature formula versioning" block is accurate**: the 6-line block cites
      registry SSOT path, the `features-status` CLI, the bump-on-math-only rule, the sentinel, and the codex SSOT. Each
      MUST still resolve to a real artifact. Find:
      `sed -n '/Feature formula versioning/,/SSOT:/p' cursor-configs/CLAUDE.md` Verify: registry path still exists;
      `features-status` console-script entry still in features-service `pyproject.toml`; codex SSOT
      `/codex/02-data/feature-formula-versioning.md` still exists.

- [ ] (u) **Fetch-failure → `attempted_failed`, never `empty_confirmed` — PER-ADAPTER swallow audit (codified
      2026-06-01)**: every features-service adapter doing external I/O (DefiLlama / on-chain RPC / vendor REST in
      `onchain/adapters/*`, `delta_one`, etc.) must route a fetch error to `record_failed` (`attempted_failed`), NOT
      swallow it (`except: … return []/None/empty-DataFrame`) into a `record_empty` (`empty_confirmed`) — a swallowed
      timeout/RPC error mislabeled as honest-empty corrupts the features manifest + the strategy preflight that reads
      it. Grep:
      `rg -U "except\b[^\n]*:\s*\n(\s*[^\n]*\n)?\s*return (\[\]|None|\{\}|pd\.DataFrame\(\))" features-service/ --include="*.py" -g '!*test*'`
      then read each adapter's outer fetch try/except. **Closed per-adapter checklist — check EVERY adapter.** Full
      spec: `defi_master_audit_instructions.md` item (u)/(aa).

### Greeks-service (data-pipeline derivation — batch + live)

> Codified 2026-06-01 (operator). greeks-service is a **young repo** brought to full workspace parity
> (workspace-manifest
>
> - `.code-workspace` + canonical GHA workflow suite incl `quality-gates-v2` + semver-agent ci/cd versioning — same as
>   every other service). It is a **general data-pipeline service for all strategies and clients** (computes option
>   Greeks/IV from market marks) — **NOT** a per-strategy or per-client instance, and **NOT** ml (ml is downstream). Its
>   dependencies are **DATA, not code**: it reads **market-data-processing-service / market-tick-data marks** (and
>   **features-service data** where required) + the usual code deps **UTL + UAC only** (no `features-service`/`mdps`
>   _code_ imports). Both batch and live therefore reduce to **pre-flight checks on the input data + compute**.

- [ ] (greeks-deps) **Code-deps are UTL + UAC only (data-deps not code-deps)**: `greeks-service/pyproject.toml`
      `[project.dependencies]` contains NO `features-service` / `market-data-processing-service` /
      `market-tick-data-service` editable deps — only `unified-trading-library` + `unified-api-contracts` (+ fastapi/
      uvicorn for the live API). Grep:
      `rg "features-service|market-data-processing|market-tick-data" greeks-service/pyproject.toml` → 0 hits. (Verified
      2026-06-01: ✅ deps = UTL/UAC/fastapi/uvicorn.)
- [ ] (greeks-batch-preflight) **Batch = pre-flight on input data + compute**: `greeks_service/batch/backfill.py`
      (`GreeksBackfillProcessor`) reads MDPS/MTDS `mark_update` parquets from GCS and computes per shard. It MUST do an
      explicit **data-availability pre-flight** (manifest/object presence for the requested `asset_group`×date horizon)
      and emit a typed failure / honest-empty when inputs are absent — NOT silently produce zero rows. (2026-06-01 gap:
      backfill reads parquet directly with no explicit availability pre-flight — see greeks build-gap todo.)
- [ ] (greeks-live-preflight) **Live = pre-flight on data + compute**: `greeks_service/api/main.py` exposes
      `make_health_router` with a `data_freshness` callback (QG STEP 5.62 ✓) and `inputs/mark_update_sub.py` subscribes
      to live marks. Confirm the live path pre-flights mark availability/freshness before publishing Greeks (readiness
      gates on input freshness, not just process liveness).
- [ ] (greeks-scope) **What greeks-service computes — CeFi + DeFi options (operator 2026-06-01)**: greeks-service
      computes per-option Greeks (Δ/Γ/Θ/vega/ρ + 2nd-order vanna/volga) via `kernels/black_scholes.py`
      (`BlackScholesKernel.compute(spot, strike, time_to_expiry, volatility, right, dividend_yield)`) for **CeFi
      options** (Deribit primary — BTC/ETH; then Binance/OKX/Bybit options) **and DeFi options** (on-chain options
      protocols — Lyra/Aevo/Premia/Dopex/…). Inputs per option: strike/expiry/right from the IS `InstrumentRecord`
      (never re-derived from venue strings), spot + mark from MDPS/MTDS `mark_update`. Output: `pricing_ledger`
      (Greeks/IV) to GCS + live. Verify BOTH `asset_group=cefi` and `asset_group=defi` option paths are exercised
      (currently `mark_update_handler` handles the generic option path; confirm DeFi marks carry the needed fields).
- [ ] (greeks-iv-source) **IV comes from the features-volatility SURFACE FITTER — greeks does NOT fit (operator
      2026-06-01)**: the **vol-surface fitter lives in features-service `volatility/`** —
      `calculators/tradfi_vol_surface.py` (`TradFiVolSurfaceCalculator`) + `vol_surface_term_structure.py` +
      `volatility_calculator.interpolate_iv_at_moneyness(...)` — which **fits observed IVs at REAL (listed) strikes and
      interpolates** → ATM (50-delta) + `iv_at_{90,100,110}_moneyness` + 7d/30d/90d term structure, written to
      `features-volatility-{ag}` GCS. greeks-service only **consumes** an IV and computes the Greeks. Verify the
      IV-resolution contract: today `mark_update_handler` uses `msg.implied_volatility` directly for CeFi (Deribit
      quotes IV) and the `implied_vol_from_price` solver elsewhere — but it does **NOT yet read the fitted/interpolated
      surface**. For any (strike, expiry) without a directly-quoted IV (most DeFi options; CeFi off-the-board strikes;
      risk-scenario Greeks), greeks MUST consume the features-volatility interpolated IV (read as **data** from the
      features-volatility bucket via pre-flight — never a features-service code import). **Gaps (2026-06-01):** (a)
      greeks reads NO features-volatility surface data yet (per-option IV / solver only); (b) DeFi IV path unbuilt (DeFi
      marks may not quote IV → needs the surface or a solver + underlying spot); (c) TradFi solver path needs
      `underlying_spot` in the schema; (d) **`second_order_greeks` is duplicated** —
      `features_service/volatility/calculators/second_order_greeks.py` AND `greeks_service/kernels/black_scholes.py`
      both compute vanna/volga → pick ONE SSOT (greeks-service owns Greeks; features-volatility should consume, or
      vice-versa); (e) **`TradFiVolSurfaceCalculator` is misnamed** — its config default is `{"CEFI": ["BTC","ETH"]}`,
      so it actually serves CeFi crypto options → rename/generalise to an asset-group-agnostic `VolSurfaceCalculator`
      covering cefi+defi.
- [ ] (greeks-topology) **Deployment topology = data-pipeline layer; batch separate / live in features VM; shared**:
      verify the deployment topology DAG (`deployment-service/configs/RUNTIME_TOPOLOGY_DECISIONS.md` + topology SVG)
      places greeks in the **data-pipeline layer (not ml)**: **batch** as a **separate** scheduled job/VM; **live**
      **co-located inside the features VM** as a **single shared service for all strategies/clients** (NO per-strategy /
      per-client instance — Greeks generalise across the book). ml consumes greeks output downstream; greeks never
      depends on ml.
- [ ] (greeks-batch-live-parity) **Batch == live (same schemas/handlers)**: the batch (`GreeksBackfillProcessor` →
      `MarkUpdateHandler` → `PricingLedgerWriter`) and live (`mark_update_sub` → `MarkUpdateHandler` → writer) paths
      share the SAME handler + output schema (`pricing_ledger_writer`), differing only in source (GCS parquet vs live
      sub) — per the workspace Batch=Live invariant.

### Batch vs Live Parity

- (batch-live) **Batch adapter output**: confirm each adapter in scope produces manifest rows with
  `capture_status=captured` for a known date range using the batch invocation path (`--mode batch`). Run against mock
  data if real upstream is unavailable (`CLOUD_MOCK_MODE=true`).
- (live-adapter) **Live adapter parity**: for each batch adapter, confirm the live adapter exists, accepts the same
  schema, and emits `available_at` at write-time (not read-time). Confirm no `DIVERGENT_EMPTY` rows for live mode.
- (mock-upstream) **Mock upstream pattern**: audits for this data layer MUST be runnable without hitting real APIs.
  Document fixture paths and `CLOUD_MOCK_MODE=true` invocations so downstream services can be audited independently.
- (live-versioning) **Live writes also stamp `feature_group_version`**: live mode uses the SAME
  `feature_writer._write_parquet` code path as batch (per the Batch=Live HARD RULE). Live parquets in
  `gs://features-delta-one-{ag}-{pid}/...` MUST carry the same sidecar column + file-level metadata as batch. Sample a
  recent live parquet via item (l)'s recipe; verify the stamp is present and `> 0` (no live writes should hit the legacy
  `0` sentinel).

## Canonical-form cross-service audit coverage (CF-1…CF-12)

> SSOT: `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` (read it for the CF-1…CF-12
> definitions + the per-service ownership matrix). features-service is a **COMPUTED downstream** service: it owns the
> manifest/path FORM checks (CF-1/2/3/5/7/8/9/11/12) against its `features-{onchain,delta-one,volatility,…}-{ag}`
> indices; **CF-4 is EXEMPT (computed — no external vendor `source`; lineage is the upstream cell)**; **CF-6 is
> PROPAGATED** (features carry upstream `expected_unattempted`, they do not originate it); **CF-10 is n/a** (features do
> not fetch raw market data). Audit method is always DATA-STATE (read the `_index` distribution / sample parquets),
> never a code constant — per the manifest-v8 lesson (constant said v8 while 0% of 7.4M rows were v8).

- [ ] (CF-1) **schema_version = v9 in ACTUAL features rows**: read the `schema_version` distribution from each prod
      features `_index` (`features-onchain-{ag}`, `features-delta-one-{ag}`, `features-volatility-{ag}`, …) and a sample
      of parquets — assert the modal value is `v9`, not just that `MANIFEST_SCHEMA_VERSION` says 9. Run a
      consolidated-index read (e.g. `gcs` list of `_index/*.parquet` per bucket → polars `value_counts()` on
      `schema_version`). RED if any non-v9 rows remain unmigrated. Cross-ref: composes with item (d) (training-pipeline
      manifest compliance) — same write path.

- [ ] (CF-2) **`asset_group=` not `category=` on features paths + rows**: grep features object paths for a `category=`
      hive segment (`gcs` list `features-*-{ag}` → assert 0 `category=` segments; the canonical segment is
      `asset_group=`); read the features `_index` rows and assert there is NO `category` field (canonical column is
      `asset_group`). Code side already emits `asset_group=` (archived `venue_axis_asset_group_vocabulary`) — this is a
      DATA-STATE confirmation, not a code grep.

- [ ] (CF-3) **`pipeline_mode=` hive partition on features paths**: confirm the features object paths carry a
      `pipeline_mode=batch*` / `pipeline_mode=live*` PARTITION SEGMENT (not merely the column). Path-list a sample from
      each `features-*-{ag}` bucket and assert the segment exists for both batch and live writes. Cross-ref: the
      `PipelineMode.BATCH_DATABENTO` value already asserted in item (n) — this verifies it materialises as a path
      partition, not just a manifest field.

- [ ] (CF-4) **EXEMPT — computed-exempt classification, zero spurious blank-source RED**: features outputs are COMPUTED
      (no external vendor `source`; lineage is the upstream MTDS/MDPS cell), so per `data_source_provenance`
      `COMPUTED_SOURCES` features must be classified computed-exempt. The check is therefore the INVERSE of an
      external-ingest check: confirm the features `_index` does NOT raise a blank-external-source RED — i.e. features
      cells are correctly recognised as computed-exempt and are NOT flagged for a missing `source` column. Read the
      provenance audit output for the `features-*-{ag}` buckets and assert 0 `BLANK_EXTERNAL_SOURCE` findings on
      features cells (any such finding = a mis-classification of a computed service as an external ingest, and must be
      fixed by adding features to `COMPUTED_SOURCES`, not by stamping a fake `source`).

- [ ] (CF-5) **Typed `EmptyConfirmedReason` on every empty features cell**: read the empty-reason histogram from the
      features `_index` and assert 0 blank / untyped rows. For computed-downstream features the valid set is
      `EXPECTED_UPSTREAM_EMPTY` (upstream cell was empty), `EXPECTED_DEPRECATED_DATA_TYPE` (retired feature group),
      `EXPECTED_OUTSIDE_PROCESSING_SCOPE`, and `SOURCE_RETURNED_ZERO` only when the upstream genuinely returned zero and
      the calculator legitimately produced no rows. Cross-ref: item (n)'s `record_group_failed(...)` is the
      `attempted_failed` (NOT empty) path — verify a poisoned group lands as `attempted_failed`, not as a blank-reason
      `empty_confirmed`.

- [ ] (CF-6) **`expected_unattempted` PROPAGATED from upstream (not originated)**: features do not originate the 4th
      state — they propagate it. Verify that when an upstream (MTDS/MDPS/IS) cell is `expected_unattempted` /
      `empty_confirmed`, the features pre-flight reads that upstream manifest state and records the owed features cell
      with `EXPECTED_UPSTREAM_EMPTY` (or carries the upstream `expected_unattempted` forward) rather than silently
      skipping it or writing a phantom captured row. Run a prod features batch on post-Phase-1+2 code over a horizon
      with a known upstream gap; confirm the owed features rows materialise with the propagated reason. Cross-ref: this
      is the downstream half of the MTDS/MDPS CF-6 origination check.

- [ ] (CF-7) **Canonical names — underscore data_type / feature-group names; no legacy drift**: grep the features
      writers/calculators for `data_type=` / feature-group literals and read the corpus `feature_group` / `data_type`
      strings from the `_index` — confirm underscore-canonical (no hyphen, no glued `_V{N}`, no `VENUE-CHAIN`). Find:
      `rg "data_type=|_DATA_TYPE|feature_group=" features-service/ --include="*.py" -g '!*test*'` then cross-check
      against the registry SSOT (`features_service/delta_one/app/features/registry.py` group names). Cross-ref: item (i)
      already asserts every `CALCULATOR_REGISTRY` group has a registry spec — this adds the NAME-canonicality check on
      the emitted strings.

- [ ] (CF-8) **`available_at` per-row, write-time, honest (no read-time / lookahead derivation)**: read the
      `available_at` distribution from the features `_index` vs the data day boundary; assert it is stamped at
      write-time per row (not derived at read-time, not lookahead). Cross-ref: item (d) already requires write-time
      `available_at` on training outputs and the (live-versioning) item requires live==batch write-time stamping — CF-8
      is the corpus-wide DATA-STATE confirmation that batch and live derive `available_at` identically.

- [ ] (CF-9) **env-split bucket `{kind}-{env}-{project}` resolved via `resolve_bucket_name()`**: grep features-service
      for inline `gs://` f-strings (QG STEP 5.69 already ratchets this) and confirm every features bucket lookup is
      env-tiered (`-prd`/`-test`) and canonical. Find:
      `rg "gs://features" features-service/ --include="*.py" -g '!*test*'` → expect 0 inline f-strings; every lookup
      goes through `resolve_bucket_name(cloud=..., kind=..., asset_group=..., env=...)`.

- [ ] (CF-10) **n/a** — features do not fetch raw market data, so there is no pre-genesis / pre-launch phantom-captured
      class to relabel. (The phantom-captured check is owned by MTDS + instruments-service per the SSOT matrix.)

- [ ] (CF-11) **fetch-failure → `attempted_failed`, never `empty_confirmed` (no swallow)**: cross-ref item (u) — the
      per-adapter swallow audit for features-service external I/O (DefiLlama / on-chain RPC / vendor REST in
      `onchain/adapters/*`, `delta_one`, …) is the CF-11 owner. Confirm every features adapter routes a fetch error to
      `record_failed` (`attempted_failed`), NOT an `except: … return []/None/empty-DataFrame` swallowed into a
      `record_empty`. Re-run item (u)'s grep + per-adapter read; CF-11 GREEN iff item (u) is GREEN.

- [ ] (CF-12) **batch == live symmetry**: diff the features batch vs live schema + data_type/feature-group set per
      asset_group; confirm one code path (`feature_writer._write_parquet` for both) and that `available_at` is not
      derived at read-time in either mode, with no live-only feature groups. Cross-ref: the (batch-live), (live-adapter)
      and (live-versioning) items already assert single-code-path + same-stamp parity — CF-12 is the
      schema/data_type-set DATA-STATE diff that closes them out.

## Success Criteria

- All checklist items (a)-(t) GREEN
- All applicable CF items (CF-1/2/3/5/7/8/9/11/12) GREEN; CF-4 confirmed computed-exempt (zero spurious blank-source
  RED); CF-6 confirmed propagated from upstream; CF-10 n/a
- features-service QG exits 0 with full per-family test collection
- IS→features contract audit has zero open RED items
- `features-status --check-drift` produces zero unexplained hash diffs against the prior baseline (every diff has a
  matching `formula_version` bump in the same commit)
- "Listed" backlog is trending DOWN week-over-week (item o)
- All 4 codex-named implementation files exist + all 4 helper helper functions exported from `registry.py`
  (`build_full_registry`, `get_specs_by_group`, `compute_group_version`, `compute_column_versions`)

## Output Format

Result file at `plans/audit/results/features_and_ml_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date       | Result file                                                      | Status                                                                                                                                                                                                            |
| ---------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-29 | `plans/audit/results/features_and_ml_master_audit_2026_05_29.md` | GREEN=14, DRIFT=3 (a/b/h — text fixed in same commit), BLOCKED=3 (l, live-versioning, batch-live — composes with `features_service_defi_data_loading_blockers_2026_05_29.md`), NOT-RUN=2 (c, d — ml-service punt) |
