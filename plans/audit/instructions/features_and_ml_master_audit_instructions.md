---
name: features_and_ml_master_audit_instructions
type: audit-instructions
epic: features_and_ml_master
assigned_vm: vm-ml
tier: L1
last_updated: 2026-05-28
---

# Features + ML Master — Audit Instructions

## Epic Scope

features-service (8 feature families: DeFi, CeFi, TradFi, Sports, Predictions, Macro, On-Chain, Cross-Asset), ml-service
(inference + training pipelines), IS→features contract. All feature schemas must be in UAC; no local definitions.

## Triggers

- Weekly (minimum cadence)
- After model retrain (verify training pipeline manifest compliance)
- When strategy-service reports feature shape mismatch at inference time
- After any UAC feature schema change
- After `ml_repo_consolidation` completes (verify merged repo structure)
- **After any edit to `features_service/delta_one/app/calculators/`** (math drift potential — items r, s)
- **After any edit to `features_service/delta_one/app/features/registry.py`** (registry SSOT drift — items i, j, o)
- **After any edit to `features_service/delta_one/app/core/feature_writer.py`** (stamp / metadata drift — items k, l, live-versioning)
- **After any edit to `codex/02-data/feature-formula-versioning.md` or `codex/04-architecture/artifact-versioning.md`** (doc-code drift — items p, t)
- **After a `live-defi-rollout` push to features-service** (composes with CI-Verification HARD RULE)

## Checklist

- [ ] (a) **All 8 feature families have active adapters**: each family has at least one adapter with batch+live parity.
      Find: `rg "class.*Feature.*Adapter|class.*Handler" features-service/ --include="*.py" -l` Verify: 8 families
      covered (DeFi, CeFi, TradFi, Sports, Predictions, Macro, On-Chain, Cross-Asset)

- [ ] (b) **IS→features contract**: `is_features_contract_audit_2026_05_20.md` findings all addressed. Check: any
      outstanding RED items in that audit have been absorbed into active plans

- [ ] (c) **ml-service inference end-to-end test**: inference path has a test that exercises the full pipeline (features
      → model → signal) with mock data. Find: `rg "inference|predict" ml-service/tests/ --include="*.py" -l` (or merged
      ml-service path post-consolidation)

- [ ] (d) **Training pipeline manifest compliance**: training outputs emit manifest rows with correct schema*version,
      `asset_group`, and `available_at` (write-time, not read-time derivation). Read: training pipeline output path —
      verify `record_captured()` called with cluster*\* kwargs

- [ ] (e) **Feature schemas in UAC**: no local feature schema definitions in features-service or ml-service. Grep:
      `rg "class.*Schema|dataclass" features-service/ --include="*.py"` — every schema must import from UAC

- [ ] (f) **No os.getenv() in feature computation**: all config via `UnifiedCloudConfig`. Grep:
      `rg "os\.getenv" features-service/ ml-service/ --include="*.py"` — should be 0 hits

- [ ] (g) **PYTEST_UNIT_DIR override wired**: `quality-gates.sh` uses `PYTEST_UNIT_DIR="tests/"` to collect all
      per-family tests (not just root-level `tests/unit/`). Check: `features-service/scripts/quality-gates.sh` — verify
      override is set before `source base-service.sh`

- [ ] (h) **ml-service repo consolidation complete**: if `ml_repo_consolidation` plan is complete, verify merged repo
      has no duplicate code paths or conflicting imports. Check: `ml_repo_consolidation_2026_05_19.md` completion status

### Registry SSOT + Formula Versioning

> Shipped 2026-05-28 across 5 phases in
> `plans/active/features_registry_status_versioning_2026_05_28.md`. Codex SSOT:
> `codex/02-data/feature-formula-versioning.md`.

- [ ] (i) **Registry covers every CALCULATOR_REGISTRY group**: every key in
      `features_service.delta_one.app.calculators.CALCULATOR_REGISTRY` must have ≥1
      `FeatureSpec` entry in `features_service.delta_one.app.features.registry._SPECS`. A
      calculator added without registry entry = un-versioned, un-trackable feature.
      Run: `cd features-service && .venv/bin/python -c "from features_service.delta_one.app.calculators import CALCULATOR_REGISTRY; from features_service.delta_one.app.features.registry import build_full_registry; reg = {s.group for s in build_full_registry()}; missing = set(CALCULATOR_REGISTRY) - reg; print('missing:', sorted(missing))"`
      Verify: empty `missing` set. Currently 34/34 groups covered (1,382 specs).

- [ ] (j) **Status + Implementation closed-set Literals haven't drifted**: the
      `Status = Literal[...]` and `Implementation = Literal[...]` declarations in
      `registry.py` must match exactly what `codex/02-data/feature-formula-versioning.md`
      § "Status field" + § "FeatureSpec extensions" document. A silent widening of
      either set breaks the test-gate filter (item m) + the consumer pin pattern.
      Find: `grep -A 10 "^Status = Literal\|^Implementation = Literal" features_service/delta_one/app/features/registry.py`
      Verify: Status set = `{verified, tested, in_dev, listed, blocked, deprecated, need_data}`;
      Implementation set = `{custom, ta_lib, pandas_std, numpy_std}`.

- [ ] (k) **Formula version stamped on every parquet write path**:
      `feature_writer._write_parquet` MUST (1) call `_resolve_group_version` for the
      group, (2) include `"feature_group_version": str(version)` in the `partition`
      dict it passes to `data_sink.write(...)`, AND (3) pass
      `metadata=self._build_parquet_metadata(df, feature_group, version)` to
      `df.write_parquet(...)`. There must be NO per-row `feature_group_version`
      column on the DataFrame (operator directive 2026-05-28 — millions-of-files
      cost). Both batch and live writer paths.
      Find: `rg "_resolve_group_version|_build_parquet_metadata|feature_group_version" features_service/delta_one/app/core/feature_writer.py`
      Verify: helpers invoked from `_write_parquet`; `feature_group_version` is a
      partition dict key (not a `with_columns(...)` call); no `_stamp_version_columns`
      helper exists.

- [ ] (l) **Path partition + file-level metadata round-trip on real GCS parquets**:
      sample a recent parquet from `gs://features-delta-one-{ag}-{pid}/` and verify
      the version is stamped in BOTH the path AND the file-level metadata, and that
      they AGREE. Drift = path/metadata mismatch (writer bug), or legacy un-stamped
      writes sneaking back in.
      Run: `python -c "import re, pyarrow.parquet as pq; path='<gs path>'; pf = pq.ParquetFile(path); meta = {k.decode(): v.decode() for k,v in (pf.metadata.metadata or {}).items() if not k.startswith(b'ARROW')}; path_v = re.search(r'feature_group_version=(\d+)/', path).group(1); print('path:', path_v, 'meta:', meta.get('feature_group_version')); assert path_v == meta['feature_group_version'], 'PATH/METADATA MISMATCH'; print('metadata:', meta)"`
      Verify: (a) GCS path contains `feature_group_version={N}/` segment between
      `feature_group=...` and `timeframe=...`; (b) file-level metadata has 3 keys:
      `feature_group_version`, `feature_column_versions`, `feature_group`; (c) path
      version int == metadata version int; (d) no `feature_group_version` COLUMN on
      the parquet's schema; (e) sentinel `0` only appears on groups without
      registered specs (currently should be empty — Phase 2 covered all 34).

- [ ] (m) **2.4 / 2.6 / 2.7 parametrize on `status ∈ {verified, tested}` only**: the
      Phase 2 mass-catalogue (1,329 "listed" specs) MUST NOT false-fail these gates.
      Drift = someone removes the filter; CI suddenly red on un-audited specs.
      Find: `rg "build_full_registry|status in" tests/delta_one/unit/test_registry_invariants.py tests/delta_one/unit/test_distribution_sanity.py tests/delta_one/unit/test_cross_timeframe_sanity.py`
      Verify: every `@pytest.mark.parametrize` over specs filters on
      `s.status in {"verified", "tested"}` or `s in _VERIFIED_GROUPS` equivalent.

- [ ] (n) **FINDING-B group-level fail-fast isolation**:
      `BatchHandler._process_groups` MUST return `True` if ANY group succeeded
      (not `all(...)`) AND `_process_one_group` must call
      `record_group_failed(...)` on each failure path (orchestrator returned False,
      emission policy rejected, exception). Drift = single-group exception poisoning
      the whole batch.
      Find: `rg "record_group_failed|succeeded_groups|failed_groups" features_service/delta_one/cli/handlers/batch_handler.py features_service/delta_one/cli/handlers/_failed_group_manifest.py`
      Verify: helper invoked on all 3 failure paths; aggregator returns
      `True if succeeded_groups else False`; manifest carries per-group success/failure
      rows with `PipelineMode.BATCH_DATABENTO`.

- [ ] (o) **"Listed" promotion backlog is monitored**: the count of specs at
      `status="listed"` should TREND DOWNWARDS over time as we hand-audit each group.
      If the backlog grows without verifies/tested promotions, the registry is decaying
      into a write-only catalogue.
      Run: `features-status` (from features-service venv) — read the bottom-line
      `listed (un-audited): N` count.
      Verify: snapshot N week-over-week. Trend: ↓ (decreasing). At 2026-05-28 baseline:
      `listed=1329, verified=28, tested=19`. Audit window: if `listed` count hasn't
      decreased in 4 weeks, flag the audit owner to promote at least the high-priority
      specs.

- [ ] (p) **Codex-named implementation files exist at documented paths**:
      `codex/02-data/feature-formula-versioning.md` § "The four files" claims 4
      concrete paths exist. Drift = file rename / move without codex update.
      Run: `for f in features_service/delta_one/app/features/registry.py features_service/delta_one/app/features/formula_hash.py features_service/delta_one/app/features/status_report.py features_service/delta_one/app/core/feature_writer.py; do test -f features-service/$f && echo "OK $f" || echo "MISSING $f"; done`
      Verify: all 4 OK. Any MISSING ⇒ update the codex doc or restore the file.

- [ ] (q) **Total Phase 1-4 test count is at or above baseline (8,400)**: regression
      check against silent test removal. The 6 test files Phase 1-4 added/extended:
      `test_registry_invariants.py`, `test_distribution_sanity.py`,
      `test_cross_timeframe_sanity.py`, `test_registry_status_versioning.py`,
      `test_feature_writer_versioning.py`, `test_status_report_cli.py`.
      Run: `cd features-service && timeout 300 .venv/bin/python -m pytest tests/delta_one/unit/test_registry_invariants.py tests/delta_one/unit/test_distribution_sanity.py tests/delta_one/unit/test_cross_timeframe_sanity.py tests/delta_one/unit/test_registry_status_versioning.py tests/delta_one/unit/test_feature_writer_versioning.py tests/delta_one/unit/test_status_report_cli.py -q 2>&1 | tail -3`
      Verify: `passed >= 8400`, `failed == 0`. Drift = count drops without explicit
      removal commit; investigate `git log --oneline -- tests/delta_one/unit/`.

- [ ] (r) **Drift detection baseline: no math change without `formula_version` bump**:
      run `features-status --check-drift`, diff against the previously-recorded
      baseline. Every hash change MUST be paired with a `formula_version` bump in
      the same commit. Hash changed + version didn't = the silent-rewrite anti-pattern.
      Run: `cd features-service && features-status --check-drift > /tmp/current_baseline.txt; diff /tmp/baseline_2026_05_28.txt /tmp/current_baseline.txt`
      Verify: every diff line where the hex changed has a matching `git log` entry
      that ALSO bumped the relevant `FeatureSpec.formula_version`. Pure-comment edits
      (canonicaliser strips them) MUST NOT show up — if they do, the canonicaliser
      regressed.

- [ ] (s) **Bump policy enforcement (formula vs config)**: any `feat:` /
      `feat!:` / `fix:` commit touching a `_calculate_features` method in
      `features_service/delta_one/app/calculators/` should ALSO bump the
      corresponding group's specs' `formula_version` in `registry.py`. Drift =
      math edit that ships without version bump (silent v1-tagged-but-v2-formula
      rows in GCS).
      Run: `git log --since='last audit' --pretty=format:'%H %s' -- features_service/delta_one/app/calculators/ | while read sha msg; do git show --stat $sha -- features_service/delta_one/app/features/registry.py | grep -q "formula_version" || echo "MISSED BUMP: $sha $msg"; done`
      Verify: zero `MISSED BUMP` lines. Config-only edits (window size,
      threshold value) are EXEMPT — those are at the consumer-config layer, not
      the formula layer (operator directive 2026-05-28: "rsi 14 vs rsi 18, that
      is config change").

- [ ] (t) **CLAUDE.md `Service architecture` § "Feature formula versioning" block is accurate**:
      the 6-line block cites registry SSOT path, the `features-status` CLI, the
      bump-on-math-only rule, the sentinel, and the codex SSOT. Each MUST still
      resolve to a real artifact.
      Find: `sed -n '/Feature formula versioning/,/SSOT:/p' cursor-configs/CLAUDE.md`
      Verify: registry path still exists; `features-status` console-script entry
      still in features-service `pyproject.toml`; codex SSOT
      `codex/02-data/feature-formula-versioning.md` still exists.

### Batch vs Live Parity

- (batch-live) **Batch adapter output**: confirm each adapter in scope produces manifest rows with
  `capture_status=captured` for a known date range using the batch invocation path (`--mode batch`). Run against mock
  data if real upstream is unavailable (`CLOUD_MOCK_MODE=true`).
- (live-adapter) **Live adapter parity**: for each batch adapter, confirm the live adapter exists, accepts the same
  schema, and emits `available_at` at write-time (not read-time). Confirm no `DIVERGENT_EMPTY` rows for live mode.
- (mock-upstream) **Mock upstream pattern**: audits for this data layer MUST be runnable without hitting real APIs.
  Document fixture paths and `CLOUD_MOCK_MODE=true` invocations so downstream services can be audited independently.
- (live-versioning) **Live writes also stamp `feature_group_version`**: live mode uses
  the SAME `feature_writer._write_parquet` code path as batch (per the Batch=Live HARD
  RULE). Live parquets in `gs://features-delta-one-{ag}-{pid}/...` MUST carry the same
  sidecar column + file-level metadata as batch. Sample a recent live parquet via
  item (l)'s recipe; verify the stamp is present and `> 0` (no live writes should
  hit the legacy `0` sentinel).

## Success Criteria

- All checklist items (a)-(t) GREEN
- features-service QG exits 0 with full per-family test collection
- IS→features contract audit has zero open RED items
- `features-status --check-drift` produces zero unexplained hash diffs against the
  prior baseline (every diff has a matching `formula_version` bump in the same commit)
- "Listed" backlog is trending DOWN week-over-week (item o)
- All 4 codex-named implementation files exist + all 4 helper helper functions
  exported from `registry.py` (`build_full_registry`, `get_specs_by_group`,
  `compute_group_version`, `compute_column_versions`)

## Output Format

Result file at `plans/audit/results/features_and_ml_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.

## Linked Results

| Date                      | Result file | Status |
| ------------------------- | ----------- | ------ |
| (populated as audits run) |             |        |
