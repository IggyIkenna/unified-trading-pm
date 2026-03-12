# Cosmictrader PR Merges — 2026-03-12

## Status: FULLY COMPLETE (2026-03-12)

Merged 4 cosmictrader PRs (`live-defi-rollout` feature branch) into local `main` across 4 repos. 3 older auto-branch PRs
closed as superseded. All quality gates passing post-merge.

---

## Merged PRs

### unified-trading-pm — PR #71 `chore: quality gate fixes, stash merge resolution`

**Branch:** `live-defi-rollout` → fast-forward merge into `main`

**What landed:**

- **144 cursor rules now active** — `.cursor/rules/` symlink (`unified-trading-pm/.cursor/rules/`) was previously
  pointing to an empty directory. PR #71 fast-forwarded `main` to `live-defi-rollout`, populating all 144 `.mdc` files
  across architecture, ci-cd, config, core, dependencies, documentation, imports, quality-gates, services, standards,
  testing, ui, workflow subdirectories.
- **`base-service.sh` glob array bug fixed** — 6 exclusion arrays (`IMPORT_INSIDE_EXCLUDE_GLOBS`,
  `EMPTY_STR_EXCLUDE_GLOBS`, `EMPTY_DICT_LIST_EXCLUDE_GLOBS`, `GCP_PROJECT_ID_EXCLUDE_GLOBS`,
  `SETUP_NO_SINK_EXCLUDE_GLOBS`, `DEEP_IMPORT_EXCLUDE_GLOBS`) were not prefixing `--glob` per element. Fixed with
  `for g in "${arr[@]+...}"; do extra+=(--glob "$g"); done` pattern.
- **`quality-gates.sh` PM-specific exclusion arrays** added for the above (excluding smoke-test-dev.py,
  github-integration/, validate-cloudbuild.py, etc.).
- **`derived-dependency-manifest.json`** — `elysium-defi-system` restored from
  `{"skipped": true, "reason": "not a directory"}` back to full external deps (aiohttp, fastapi, httpx, pydantic,
  pytest, pytest-asyncio, python-dotenv, pyyaml, ruff, uvicorn, vcrpy, web3; external_count: 12). Also picked up:
  `httpx>=0.28.1` for PM, `joblib` for UTL, `ib-insync` for UMI, `pytest-socket` for PM; UTL dep on UCI changed to
  `unified-cloud-interface[gcp]`.
- **Stash resolution** — stash held old versions of `canonical-dependency-manifest.json` and
  `derived-dependency-manifest.json`. Used `git checkout stash@{0} -- <specific-files>` to selectively restore only
  non-conflicting files (`.github/workflows/quality-gates.yml`, audit scripts, `workspace-manifest.json`).

**Commit:** `a39cb4d` (fast-forward to `live-defi-rollout`)

---

### unified-api-contracts — PR #34 `fix: add Hyperliquid* exports to __all__, enable_socket for binance live test`

**Branch:** `live-defi-rollout`

**What landed:**

- `HyperliquidFill`, `HyperliquidOpenOrder`, `HyperliquidPosition`, `HyperliquidUserState` already present in
  `__init__.py` (both import and `__all__` entries — 8 matches confirmed). Remote `__init__.py` was identical; no
  conflict.
- **Merge conflict resolved** in `tests/unit/test_binance_schema_coverage_smoke.py` docstring: HEAD described "Uses
  static fixture data from ticker_24hr.yaml cassette — no live API call" vs remote "Uses live API…". Kept HEAD (test
  actually uses `_BINANCE_TICKER_FIXTURE`, not live API). `@pytest.mark.enable_socket` already present in HEAD.

---

### unified-events-interface — PR #24 `fix: remove backward-compat wording from ServiceMode docstring`

**Branch:** `live-defi-rollout`

**What landed:**

- **`quality-gates.yml` CI improvements** — PM clone with `--depth 1`, strip `refs/heads/` prefix from branch names,
  removed `|| true` bypass patterns.
- **`ServiceMode` conflict resolved** — Remote tried to re-add `ServiceMode` with a cleaned deprecation docstring. HEAD
  had already removed it entirely. Kept HEAD (further along the deprecation path). Remote's re-addition discarded.

---

### features-multi-timeframe-service — PR #6 `feat: fix quality gates - lint, deps, tf_session_context Float32, event logging, schema contract`

**Branch:** `live-defi-rollout`

**What landed (HEAD wins on all source files — more complete):**

- **`google-cloud-pubsub>=2.28.0,<3.0.0`** added from remote to `pyproject.toml` dependencies.
- **`unified-feature-calculator-library>=0.2.0,<1.0.0`** already in HEAD (was missing from remote — root cause of 62
  pre-merge test failures).
- **Calculators** (`tf_momentum_alignment`, `tf_session_context`, `tf_structure_context`, `tf_vol_compression`,
  `wedge_confluence`): kept HEAD throughout — more complete implementations (Prometheus metrics integration,
  configurable TF pairs via `_tf_pairs`, extracted helper methods, `_REVERSAL_COLS`/`_CONTINUATION_COLS` lists,
  `tf_level_multi_confluence` computed not stub).
- **`app/calculators/__init__.py`** — kept HEAD: includes `HierarchicalRegimeCombiner`, `IntradayRegimeCalculator`,
  `MicroRegimeCalculator`, `TfRiskRewardCalculator`, `build_wedge_confluence_features`, `build_tf_rr_features`.
- **`config.py`** — kept HEAD: has `MICRO_BASELINE_BARS`, `VOL_SPIKE_THRESHOLD`, `STRESS_THRESHOLD` for Layer 3 micro
  regime.
- **`cli/main.py`** — kept HEAD: async implementation with `--date`/`--run-tag` args, `asyncio.run(_async_main())`,
  proper startup/shutdown lifecycle.
- **`tests/conftest.py`** — kept HEAD: socket blocking support (`--block-network` CLI option, `_enforce_block_network`
  fixture).
- All infrastructure (`.github/workflows/`, `scripts/`, `.gitignore`, `uv.lock`, `buildspec.aws.yaml`,
  `cloudbuild.yaml`, `pyrightconfig.json`) — kept HEAD via `git checkout HEAD -- <file>`.

**Post-merge fixes (same session):**

- `unified-internal-contracts` moved from `[project.dependencies]` to `[project.optional-dependencies] dev` — version
  alignment script rejected it from main deps (`uses=False`; only imported in tests, not production source). Editable uv
  source entry retained.
- `ASYNCIO_RUN_EXCLUDE_GLOBS` added to `scripts/quality-gates.sh` for `cli/main.py` and `cli/handlers/batch_handler.py`
  — both use `asyncio.run()` as legitimate sync-to-async entry points. QG grep heuristic false-positives on docstring
  "for" text. Documented in `QUALITY_GATE_BYPASS_AUDIT.md`.

**Final QG result:** 447 tests passed, 97.43% coverage (floor 96%), 0 violations. Commits: `d4030db`, `75c4c20`.

---

## Closed as Superseded (not merged)

| PR      | Repo                  | Branch                         | Reason                                                                                                                                                  |
| ------- | --------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PM #68  | unified-trading-pm    | `feat/cursor-rules-migration`  | 951-file diff from main — cursor rules + workflows + .cursorrules. Cursor rules (143 .mdc files) and workflow changes already in main via later merges. |
| UAC #26 | unified-api-contracts | `auto/20260309-070622-1534273` | Full workspace-sync dump from agent session 2026-03-09. Specific fixes (test file split) buried inside; branch diverged too far to merge safely.        |
| UAC #14 | unified-api-contracts | `auto/20260305-184807-648597`  | Full workspace-sync dump from agent session 2026-03-05. Changes incorporated via subsequent merges.                                                     |

---

## Key Decisions / Conflict Resolution Log

| File                                                                     | Conflict                                                                                           | Resolution                                                                 |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `unified-api-contracts/tests/unit/test_binance_schema_coverage_smoke.py` | Docstring: cassette-based vs live-API wording                                                      | Kept HEAD (cassette-based — test uses `_BINANCE_TICKER_FIXTURE`, not live) |
| `unified-events-interface/unified_events_interface/__init__.py`          | Remote re-added `ServiceMode`; HEAD had removed it                                                 | Kept HEAD (further along deprecation)                                      |
| `features-multi-timeframe-service/pyproject.toml`                        | HEAD had `unified-feature-calculator-library`; remote had `unified-internal-contracts` as main dep | Merged both; post-merge moved UIC to dev deps (test-only)                  |
| All FMTS source calculators + infra                                      | HEAD more complete (Prometheus, configurable TFs, Layer 3)                                         | Kept HEAD throughout via `git checkout HEAD -- <file>`                     |

---

## Notes

- **`elysium-defi-system` manifest** — was marked `skipped: not a directory` because cosmictrader generated the manifest
  without the repo locally. Restored to full deps since the repo is now present.
- **`unified-feature-calculator-library` naming** — remote branch used `unified-feature-calculator-library`; HEAD used
  the same. Kept. No rename needed.
- **PM stash pop conflict** — stash had old manifest files that conflicted with merged versions. Resolved by selective
  `git checkout stash@{0} -- <file>` for non-conflicting files only.
- **FMTS `uv.lock` uncommitted** — `git merge` failed with "local changes would be overwritten". Fixed by committing
  `uv.lock` before retry.
