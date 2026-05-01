# Unified Trading System — Claude Code Instructions

## Environment: Venv Split (SSOT: venv-usage-ssot.mdc)

| Use case                  | Venv                        | Command                                                      |
| ------------------------- | --------------------------- | ------------------------------------------------------------ |
| **Quality gates / tests** | Repo `.venv`                | `cd <repo> && bash scripts/quality-gates.sh` — no activation |
| **IDE / general Python**  | Workspace `.venv-workspace` | `source \${WORKSPACE_ROOT}/.venv-workspace/bin/activate`     |

**Never** run `pytest` directly — uses wrong venv. Always use `quality-gates.sh`.

At session start, for general Python (not tests):

```bash
# WORKSPACE_ROOT = $UNIFIED_TRADING_WORKSPACE_ROOT or first workspace folder
source "\${WORKSPACE_ROOT:-.}/.venv-workspace/bin/activate"
which python  # .venv-workspace/bin/python
```

`.claude/settings.json` may prepend `.venv-workspace/bin` to PATH — if so, checks pass without manual activation.

## Rules: Read Before Coding

Read these before making ANY code changes:

1. `.cursorrules` — workspace standards (uv not pip, quickmerge not git push, etc.)
2. `.cursor/rules/no-empty-fallbacks.mdc` — no try/except fallback imports
3. `.cursor/rules/no-type-any-use-specific.mdc` — no Any types
4. `unified-trading-pm/codex/06-coding-standards/README.md` — coding standards
5. `unified-trading-pm/plans/PLAN_FORMAT.md` — plan format; **Cursor checkboxes** (`- [x]` / `- [ ]`) required on every
   todo
6. **Asset-group vocabulary** — the venue axis is **`asset_group`** (not `category`). Use `asset_group` everywhere new
   code touches it: CLI flag `--asset-group`, env vars `VM_ASSET_GROUP` / `MDPS_ASSET_GROUP`, Python symbols
   `VENUES_BY_ASSET_GROUP` / `DATA_TYPES_BY_ASSET_GROUP` / `VENUE_TO_ASSET_GROUP` / `MarketAssetGroup` /
   `get_bucket_for_asset_group`. **One intentional exception**: dict KEYS stay lowercase (`cefi` / `defi` / `tradfi` /
   `sports` / `prediction`). GCS hive-partition keys: `asset_group=` is **canonical** for new writes (per
   `market_tick_data_service/raw_tick_hive.py` SSOT — `RAW_TICK_ASSET_GROUP_HIVE_KEY = "asset_group"`); `category=` is
   the **legacy** form (`RAW_TICK_ASSET_GROUP_HIVE_KEY_LEGACY`) preserved on disk without re-keying. Readers must try
   canonical first then fall back to legacy (`reader.py` does this; the data-status reconciler regex must match both:
   `(?:category|asset_group)=`). Manifest pre-flight is hive-key-agnostic — it indexes by `(venue, data_type, date)`
   only, so legacy `category=` data on disk is correctly skipped iff the manifest has a captured row for it. Plan:
   `unified-trading-pm/plans/active/venue_axis_asset_group_vocabulary_2026_04_25.plan.md` (Waves A/B/E shipped; C/D =
   features-\* + execution-service consumer keys).

## Key Rules (Quick Reference)

- **Flat deps only** — every `pyproject.toml` has ONE list: `[project.dependencies]`. No
  `[project.optional-dependencies]` ever — not `dev`, not `test`, not any group. Never use `.[dev]` extras (e.g.
  `uv pip install -e .` not `uv pip install -e ".[dev]"`). Tests run locally, Cloud Build, Code Build, and GHA — all
  need all deps. Optional groups are pointless and create conflicts.
- `uv pip install` not `pip install`
- `ARG PROJECT_ID` +
  `FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest`
  in Dockerfiles — never `python:3.13-slim` or `pip install uv`
- `bash scripts/quickmerge.sh "message" --agent` not `git push` — always use `--agent` in Claude Code sessions
- **Push before quickmerge when you already committed locally** — If the branch has commits not on `origin`, run
  `git push -u origin <branch>` before quickmerge. Quickmerge’s stash only saves **uncommitted** work; aligning the
  branch to `origin/<branch>` can move the branch tip off local-only commits. Prefer: Pass 1 QG → then quickmerge (which
  commits + pushes), or push first if you committed manually.
- Two-pass model: `bash scripts/quality-gates.sh` first (Pass 1 — full), then `quickmerge --agent` (Pass 2 —
  lint/format/typecheck/codex, no tests, no act)
- **NEVER use `--dep-branch` in agent/Claude Code sessions** — it is a human-only flag. Quickmerge exits(1) if
  `--dep-branch` is combined with `--agent`. Branch is read automatically from `active_feature_branch` in
  `workspace-manifest.json` (currently: `live-defi-rollout`). Dep conflict? Commit dep repo first, then re-run.
- **DO NOT run quickmerge when local dep repos are dirty — unless the user explicitly asks.** If an upstream workspace
  dep repo (UAC / UTL / UCI / UEI / MTDS / URDI, etc.) has uncommitted local changes, quickmerging a downstream consumer
  is pointless and misleading: the consumer's path-dep resolution + `uv pip install -e ../<dep>` locally will pull the
  dirty tree, but the pushed branch will link to origin/<dep> which lacks those edits → CI green locally, red remotely,
  and the PR is a lie. Same applies to repeatedly quickmerging the SAME repo while other agents are mid-edit on it
  (you'll absorb their untracked files into your stash — see the concurrent-quickmerge feedback memory). Protocol: (1)
  check `git status` across every repo the target depends on, (2) if any dep is dirty, stop and report to the user, (3)
  proceed with quickmerge only on explicit user go-ahead or after the deps land. Two legitimate exceptions: the user
  explicitly says "just quickmerge / commit everything as-is", or the dirty files are purely advisory (generated SVGs /
  DAGs that always regen on QG).
- `from unified_trading_library.events import setup_events, log_event` — no fallbacks
- `basedpyright` not `pyright` (and always with `run_timeout 120 basedpyright <source_dir>/`)
- No `os.getenv()` — use `UnifiedCloudConfig`
- No `# type: ignore` to hide architectural violations — fix the root cause
- No `try/except ImportError` around library imports — fail loud
- Services use instruments-service for reference data, not MTDS — MTDS is for market data only
- Shard-level failure isolation — no `raise` inside per-venue/per-shard loops (see
  codex/04-architecture/shard-level-failure-isolation.md)
- Every adapter MUST classify errors through UAC `classify_venue_error()` and emit `ADAPTER_FETCH_FAILED` events
- **Signal Leasing / strategy-service signal broadcast** — External-counterparty signal emission MUST use shard-level
  failure isolation (D10) + `classify_venue_error()` + `ADAPTER_FETCH_FAILED` event. Counterparty credentials via
  `ApiKeyReloader` + HMAC signing; never raises to signal generator. SSOT:
  `codex/14-playbooks/shared-core/signal-broadcast-architecture.md`; architecture plan:
  `plans/active/signal_leasing_broadcast_architecture_2026_04_20.plan.md`.
- `logger.warning("%s", _err.message)` not `logger.warning(_err.message)` — the message is not a format string
- `.env` files must NEVER contain placeholder credential paths — ADC is the default
- **Bandit B108 / temp paths** — Never hardcode `"/tmp"` in Python. Use `tempfile.gettempdir()` (POSIX `TMPDIR`, macOS
  temp under `/var/folders/...`). For disk-usage probes, default to root + `gettempdir()` + `Path.home()` and skip
  missing paths. SSOT: `unified-trading-pm/codex/06-coding-standards/quality-gates.md` (Bandit B108 section).
- Service CLIs follow standardised axes: `--operation` (what), `--mode` (batch/live), `--asset-group` (domain). See
  `codex/06-coding-standards/cli-convention.md`.
- **Availability manifest v5 (honest-coverage)** — `ManifestWriter` writes proper shard columns (venue, chain,
  data_type, instrument_type, league_id, timeframe, feature_group, model_family, training_period, strategy_id,
  client_id, instruction_type) PLUS `capture_status` (`captured` / `empty_confirmed` / `attempted_failed`),
  `error_reason`, `attempted_at`. Adapters MUST distinguish empty-vs-failed:
  `record_empty(row_key=..., attempted_at=...)` for legitimately-zero-rows,
  `record_failed(row_key=..., error=classify_venue_error(exc), attempted_at=...)` for exceptions. **Never overload
  `venue`** with non-venue data. SSOT: `codex/02-data/availability-manifest-and-data-status.md`.
- **Sports GCS path SSOT** — Never hardcode `sports_reference/by_date/day=.../entity=.../...` paths inline. Use
  `from unified_api_contracts.sports import candidate_parquet_paths, candidate_parquet_uris, SPORTS_DATA_TYPE_TO_FOLDER, SPORTS_DATA_TYPE_LAYOUT, SportsPathLayout, sports_bucket_name`.
  The 2026-04-29 phantom-row audit incident (false 26% phantom for ODDS because the audit probed `entity=odds/` instead
  of `entity=footystats_odds/`) is the canonical reason this SSOT exists.
  `candidate_parquet_paths(data_type, day, league_id)` returns the ordered list of GCS paths to probe — caller checks
  each, first hit wins. Layout: per-league subpartition first (`entity={F}/league={L}/{F}.parquet`), bare path fallback
  (`entity={F}/{F}.parquet`), flat for singletons like VENUES (`{F}/{F}.parquet`). Module:
  `unified_api_contracts/canonical/domain/sports/gcs_paths.py`.
- **Sports source coverage windows** — Sources have launch dates; data-status must clip pre-launch dates from expected
  denominators or those days falsely render as `missing`. SSOT: `SOURCE_COVERAGE_START` dict in UAC
  `unified_api_contracts.sports` (api_football=2018-01-01, footystats=2019-01-01, understat=2015-01-16,
  transfermarkt=2019-01-01, soccer_football_info=2019-01-01, open_meteo=2019-03-02, **odds_api=2020-06-06**,
  mdps_odds_horizon_bucket=2020-06-06). Use `clip_dates_to_source_coverage(source, start, end)` and pass `source_key=`
  through helpers like `_sports_expected_dates_for_league` so the clip propagates. **Per-(source, data_type) overrides**
  live in `DATA_TYPE_COVERAGE_START` for entities with later coverage than the source-wide value:
  `("soccer_football_info", "SFI_PROGRESSIVE_STATS")` = 2020-01-01 (probed 2026-04-30: SFI's progressive endpoint
  returns empty for every match before this date), and
  `("api_football", "FIXTURE_EVENTS"|"FIXTURE_LINEUPS"| "FIXTURE_STATS"|"PLAYER_STATS")` = 2020-06-06 (api_football
  endpoints have data back to 2017-10 per live probes 2026-05-01 but our backfill never captured 2018-2020 due to
  pre-flight skips, and downstream odds_api also starts 2020-06-06 so pre-cutoff per-fixture data has no trading value).
  Pass `data_type=` through `clip_dates_to_source_coverage` / `get_source_coverage_start` to apply the override.
  Documented date-range gaps (provider outages, paused leagues) go in `KNOWN_COVERAGE_GAPS` (currently empty) and are
  filtered by `is_in_known_gap(source, data_type, iso_date)` — data-status drops them from the denominator and the
  orchestrator pre-skips them so VMs don't waste rate-limit quota grinding through known-empty range.
- **Manifest phantom audit** — Manifest can drift if adapters record `captured` for a shard but the parquet doesn't
  exist at the canonical path (stale rescan output, schema migration churn, broken denorm). The orchestrator's
  `_should_skip_shard` trusts the manifest, so phantoms cause permanent skip. Periodic audit:
  `instruments-service/scripts/reconcile_phantom_manifest_rows.py --dry-run` — uses `candidate_parquet_paths` SSOT to
  bulk-list all parquets per day, set-membership check vs each captured row, flips phantoms to `attempted_failed` so VMs
  auto-retry. Bulk-list pattern (one GCS list per day) = ~5 min for 600k rows; per-row `exists()` would take 16h.
  Critical: do NOT write empty placeholder parquets to mask phantoms — that's fudging data quality.
  `record_empty(row_key=...)` is for legitimately-empty source responses only (we tried, API returned 200+empty).
  Reconciliation incident: 2026-04-29 — 167k fake PLAYER_VALUES denorm rows + 15k legacy phantoms cleaned up.
- **VM tarball deployment** — Backfill / migration / smoke / forward-poll VMs boot via
  `gs://deployment-scripts-.../vm/setup-data-pipeline-vm.sh` and pull tarballs from `gs://deployment-scripts-.../code/`.
  Refresh tarballs after every code change with `bash deployment-service/scripts/vm/create-code-tarballs.sh <flag>`:
  `--all` (safest for any multi-repo feature), `--asset-group SPORTS|CEFI|TRADFI|DEFI|PREDICTION` (scoped to an
  asset_group's pipeline), `--include <repo>` (one-off addition). **Bare invocation only re-tars CORE**
  (UAC/UTL/MTDS/deployment-service) — forgetting the flag silently runs stale code. SSOT:
  `codex/05-infrastructure/vm-tarball-deployment.md`.
- **Singleton-locked launchers** — Adapters with shared API keys / per-IP rate limits use a singleton-lock pattern in
  the launcher (refuses launch if a same-prefix VM is RUNNING in the zone; `--force` bypass). Currently:
  `launch-sfi-forward-poll.sh`, `launch-mtds-prediction-backfill-vm.sh`. New rate-limited adapters should copy the
  pattern. Reference incident: 2026-04-19 SFI thundering herd (10 VMs / 6 hours / ~4 useful writes).

## Service Infrastructure Requirements (QG-Enforced as ERRORS)

Every service MUST have all of the following (enforced as errors in base-service.sh since 2026-03-24):

- **ServiceBootstrap** (STEP 5.61) — `ServiceBootstrap(` must appear in service source. Handles lifecycle events
  (STARTED/STOPPED/FAILED) automatically. Services do NOT emit these manually.
- **Health API** (STEP 5.62) — `api/main.py` with `make_health_router` from UTL. Must include `data_freshness` callback.
  Template: `market-tick-data-service/market_tick_data_service/api/main.py`.
- **Typed config reloaders** (STEP 5.34) — `config_reloaders.py` must use typed config class, never `object` type or
  `getattr(service_config, ...)`. Pattern: `start_domain_config_reloaders(service_config: MyServiceConfig)`.
- **Schema provenance** — All domain types (BaseModel, TypedDict, dataclass) must come from UAC (including
  `unified_api_contracts.internal`). No local definitions in service source (scripts/ excluded).
- **API key hot-reload** — Services fetching API keys from Secret Manager must use `ApiKeyReloader` from UTL, not
  one-shot `validate_api_keys_for_venues()`. See `codex/06-coding-standards/config-reloader-pattern.md`.

## DeFi Execution Architecture

**Interface credential convention**: execution-service fetches credentials from Secret Manager and injects them at
runtime via factory/constructor params. See `codex/04-architecture/interface-credential-convention.md`.

- Trade execution: `get_order_adapter(venue, api_key, api_secret, ...)` — keys as params
- DeFi execution: `connector.connect(config={"wallet_private_key": pk, "rpc_url": url})` — from config dict
- Sports execution: `adapter(credentials={"api_key": key})` — keys as params
- Reference data: `create_adapter(venue, api_key=key)` — keys as params
- MTDS market_interface / UEI / UFI: no keys needed

**RPC URL templates**: `CHAIN_RPC_TEMPLATES` in UAC `registry/capability_declarations/_defi.py` — SSOT for all chain→RPC
mappings. execution-service DeFi connectors import from UAC, never define their own.

**Flash loan receiver**: Deployed Solidity contract required for Aave flash loans. Source in
`deployment-service/contracts/FlashLoanReceiver.sol`. Deploy via
`bash deployment-service/scripts/deploy-flash-loan-receiver.sh --chain <name>`. Address in UAC
`config/testnet_contracts.yaml`. execution-service `connect()` validates on-chain (`eth_getCode`), fails loud if
missing. See `codex/04-architecture/flash-loan-receiver.md`.

**Contract registry schema**: `unified-config-interface/testnet_contracts.py` has `PROTOCOL_SCHEMAS` declaring required
contracts per protocol. Registry validates at load time — missing contracts raise `ValueError` with deploy command.

**Uniswap live swap**: execution-service `UniswapConnector.swap_exact_input()` executes live swaps via SwapRouter02
(`0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45`). Flow: ERC20 `approve(router, amount)` then `exactInputSingle`. Returns
`DeFiSwapResult` with tx hash, gas used, and effective price.

**DeFi error classification**: 13 structured error codes in execution-service `DefiErrorCode` (aave.py). Every revert
maps to a known code: `INSUFFICIENT_COLLATERAL`, `SLIPPAGE_EXCEEDED`, `TX_REVERTED`, etc. Execution-service routes on
code prefix (FAIL/RETRY/SKIP).

**DeFi pipeline flow**: instruments-service → market-tick-data-service → features-onchain-service → strategy-service →
execution-service. All via service CLIs. No standalone scripts. See the pipeline map discussion in this session's
memory.

**Removed providers** (do NOT reference): Elysium, Arkham, Bloxroute, Pyth, Infura — all deleted from UAC, MTDS, docs.

## Version Graduation (1.0.0 Process)

All repos start at 0.x.x. The semver-agent pre-1.0.0 override prevents automatic crossing to 1.0.0 (feat! on 0.x.x =
MINOR bump, not MAJOR). 1.0.0 is a deliberate human decision.

**How to graduate a repo to 1.0.0:**

1. GitHub UI: Actions → `request-major-bump` → Run workflow → proposed_version=1.0.0, reason="..."
2. CLI: `gh workflow run request-major-bump.yml --repo IggyIkenna/<repo> -f proposed_version="1.0.0" -f reason="..."`
3. Telegram sends you the approval issue link
4. Comment `/approve` on the GitHub Issue to execute the bump
5. Bump goes to staging → SIT validates → promotes to main

**Post-1.0.0 semver rules change:** feat! = MAJOR bump (opens approval issue), not MINOR.

**NEVER bump versions manually** — not in `pyproject.toml`, not in `workspace-manifest.json`, not in version floor
constraints in consumer repos. The semver-agent handles ALL version bumps automatically on merge to main based on
conventional commit prefixes (`feat:`, `fix:`, `feat!:`). Manually editing version numbers causes drift and conflicts
with CI/CD automation.

## PM/Codex Doc-Only Fast-Path

When quickmerging PM or codex repos:

- **Plans, docs, cursor rules** (plans/, docs/, cursor-configs/, cursor-rules/, _.md, _.mdc) → PR targets **main**
  directly. Plan agents fire immediately.
- **Scripts, workflows** (scripts/, .github/workflows/) → PR targets **staging**. Goes through SIT validation.

This ensures plan changes propagate instantly to agents (plan-health, rules-alignment, codex-sync) without waiting for
the full SIT cycle.

## Plan Locking

Plans with `locked_by: <branch>` in frontmatter cannot be archived by agents or deleted without `[unlock-plan]` in the
commit message. This prevents premature removal of plans that are actively being implemented.

- To lock: add `locked_by: live-defi-rollout` and `locked_since: 2026-03-16` to plan frontmatter
- To unlock: remove those fields from frontmatter
- PM quality-gates.sh blocks deletion of locked plans without `[unlock-plan]` tag
- **Agent unlock protocol:** Agents may ASK the human to unlock a plan when all todos are done, but must NEVER unlock
  autonomously. If approved, agent removes `locked_by`/`locked_since` and includes `[unlock-plan]` in commit.

## Workflow Templates (Canonical in PM)

Per-repo GitHub Actions workflows are managed as **canonical templates** in PM, not flat copies:

- **Templates SSOT:** `unified-trading-pm/scripts/workflow-templates/`
- **Rollout (generic):** `bash unified-trading-pm/scripts/propagation/rollout-workflow-templates.sh`
- **Rollout (semver-agent):** `bash unified-trading-pm/scripts/propagation/rollout-semver-agent.sh`

| Workflow                        | Pattern                                                     | Why                                     |
| ------------------------------- | ----------------------------------------------------------- | --------------------------------------- |
| `request-major-bump.yml`        | Reusable (`workflow_call`)                                  | `workflow_dispatch` supports forwarding |
| `major-bump-issue-handler.yml`  | Canonical template (flat copy)                              | `issue_comment` can't forward           |
| `staging-lock-check.yml`        | Canonical template (flat copy)                              | `pull_request` can't forward            |
| `update-dependency-version.yml` | Canonical template (flat copy)                              | `repository_dispatch` can't forward     |
| `semver-agent.yml`              | Template + substitution (`__REPO_NAME__`, `__SOURCE_DIR__`) | Repo-specific env vars                  |

**Never edit per-repo workflow copies directly.** Edit the PM template, then run the rollout script.

## Force-Sync Warning (CRITICAL)

`admin-force-sync-all-to-main.sh` overwrites remote main with local HEAD. **This can revert remote-only changes** —
especially version bumps made by GitHub Actions workflows (semver-agent, major-bump-approval).

**Before any force-sync:**

1. Run `bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh` — step [0.96] checks for remote
   staging/feature branch version drift
2. If drift is found: `git fetch origin staging && git checkout origin/staging -- pyproject.toml` per repo
3. Only force-sync after resolving all drift

**After a force-sync:** re-run version alignment to confirm no remote bumps were reverted.

## Testing Infrastructure (Emulators & Mocks)

All tests run credential-free (`CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`). Protocol-faithful emulators and mocks
replace live cloud services (see `unified-trading-pm/plans/archive/cicd_mock_hardening_2026_03_11.plan.md`).

**GCP Emulators** (auto-detected by SDK via env vars):

- Pub/Sub: `PUBSUB_EMULATOR_HOST=localhost:8085`
- GCS: `STORAGE_EMULATOR_HOST=http://localhost:4443` (fsouza/fake-gcs-server)
- BigQuery: `BIGQUERY_EMULATOR_HOST=localhost:9050`

**AWS**: `@mock_aws` decorator (moto) — no credentials, no emulator process needed.

**Network blocking**: `pytest --block-network` blocks all sockets; `@pytest.mark.allow_network` opts out.

**WS tests**: Use `MockWebSocketFeed` from `market-tick-data-service/tests/market_interface/fixtures/mock_ws_server.py`.

**DeFi unit tests**: Use `responses` library (`@responses.activate`, `passthrough=False`) for Hyperliquid REST. Mock
Web3 at the signing level — never hit real RPCs in unit tests.

**DeFi integration tests**: Use the shared Tenderly fork fixtures in `execution-service/tests/integration/conftest.py`.
Fixtures: `tenderly_fork` (session), `funded_wallet`, `flash_loan_receiver`, `aave_connector`, `uniswap_connector`. All
marked `@pytest.mark.allow_network`. Skipped if SM credentials unavailable.

**Local stack**: `bash unified-trading-pm/scripts/demo-mode.sh --seed` — no credentials required.

**Cassette parity**: `cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py` — runs on every commit.

## Local Development

Tier 0 is the canonical local-dev mode — Firebase Emulator Suite layered with `NEXT_PUBLIC_MOCK_API=true` so widgets
render against in-repo fixtures while sign-in / Firestore / Storage hit a local emulator pool seeded with the demo
personas. Same Firebase code path as staging and prod (only project ID + emulator hosts change). The two layers are
orthogonal: Firebase SDK paths bypass mock-handler, mock-handler doesn't intercept Firebase. Pre-2026-04-28 the
firebase-local handoff bypassed the mock-API flag and produced "Failed to load market data" on every API-driven widget;
commit `31ffa5d2` integrated them by default.

```bash
# Tier-based startup (preferred — unified-trading-system-ui)
cd unified-trading-system-ui
bash scripts/dev-tiers.sh --tier 0                     # Firebase emulators + Next dev + auto-seed (DEFAULT)
bash scripts/dev-tiers.sh --tier 1                     # Tier 0 + 2 API gateways (when NEXT_PUBLIC_MOCK_API=false needed)
bash scripts/dev-tiers.sh --tier 2                     # Tier 1 + downstream Python services (full fleet)
bash scripts/dev-tiers.sh --tier 0 --no-mock-api       # Firebase emulator only, no widget fixtures (auth-flow testing)
bash scripts/dev-tiers.sh --tier 0 --no-firebase-local # talk to a real Firebase project (rare; reproduce staging bug)
bash scripts/dev-tiers.sh --stop                       # stop all
bash scripts/dev-tiers.sh --status                     # check what's running

# Legacy PM-based startup (still works, broader scope)
bash unified-trading-pm/scripts/dev/dev-start.sh --all --mode mock    # start all UIs + APIs
bash unified-trading-pm/scripts/dev/dev-stop.sh                       # stop all
bash unified-trading-pm/scripts/dev/dev-status.sh                     # check status
```

Dev server on `http://localhost:3000`. Emulator UI on `http://localhost:4000` (Auth pool / Firestore docs). Health page:
`http://localhost:3000/health` — auto-detects tier, checks all connectors. Demo personas auto-seed on first boot;
re-seed manually with `npm run emulators:seed`.

Runtime tiers documented in `unified-trading-pm/codex/05-infrastructure/runtime-tiers-and-deployment.md` and
`unified-trading-pm/codex/14-playbooks/authentication/firebase-local.md`.

### 5 Mode Axes

| Axis       | Env Var           | Mock value    | Real value      | Controls                           |
| ---------- | ----------------- | ------------- | --------------- | ---------------------------------- |
| UI data    | `VITE_MOCK_API`   | `true`        | `false`         | Client-side mock data vs API calls |
| UI auth    | `VITE_SKIP_AUTH`  | `true`        | `false`         | OAuth login requirement            |
| API data   | `CLOUD_MOCK_MODE` | `true`        | `false`         | Sample data vs real cloud          |
| API auth   | `DISABLE_AUTH`    | `true`        | unset           | Token validation                   |
| Mock state | `MOCK_STATE_MODE` | `interactive` | `deterministic` | Stateful vs stateless              |

### Presets

| Preset       | Flag              | Use case                                                                   |
| ------------ | ----------------- | -------------------------------------------------------------------------- |
| **ci**       | `--mode ci`       | CI smoke tests, deterministic (no cache persistence)                       |
| **mock**     | `--mode mock`     | Local dev/UAT (default), interactive state persists in `.local-dev-cache/` |
| **api-real** | `--mode api-real` | Test APIs against real cloud data                                          |
| **real**     | `--mode real`     | Staging-like, needs credentials + OAuth                                    |

### Cache Cleanup

```bash
bash unified-trading-pm/scripts/dev/dev-stop.sh --clean     # stop + wipe .local-dev-cache/
bash unified-trading-pm/scripts/dev/dev-start.sh --reset     # wipe cache + start fresh
```

### Quick Test Reference

| What                 | Command                                             |
| -------------------- | --------------------------------------------------- |
| Python quality gates | `cd <repo> && bash scripts/quality-gates.sh`        |
| UI tests (headless)  | `cd <ui-repo> && CI=true npm test -- --run`         |
| UI smoke build       | `cd <ui-repo> && VITE_MOCK_API=true npx vite build` |

UIs on ports 5173-5183, APIs on 8004-8016. Port registry SSOT: `unified-trading-pm/scripts/dev/ui-api-mapping.json`.
Vitest must use `pool: "forks"` (not threads) to prevent zombie node processes.

Full guide: `unified-trading-pm/codex/08-workflows/local-dev.md`

## This is a Multi-Repo Workspace (NOT a monorepo)

Each subdirectory is an independent git repo. When editing, only commit to the target repo. Never run `basedpyright .`
from workspace root — always run per-repo with timeout.

## Batch = Live: Unified Pipeline Architecture (CRITICAL)

Batch and live use the **SAME code path, same component interactions**. The ONLY difference is execution fills. This
applies to ALL asset_groups — sports, DeFi, CeFi, TradFi. There is NO such thing as a "live-only strategy" or a
"batch-only strategy."

**Strategy P&L backtest (strategy alpha):** Strategy-service interacts with position-balance-monitor,
risk-and-exposure-service, execution-service — all co-located. Execution-service in "always fill" mode returns zero
execution alpha (fills at requested price). This isolates strategy P&L from execution quality. Strategy still goes
through ALL normal component interactions (position tracking, risk checks, etc.).

**Execution alpha measurement:** Execution-service has a matching engine for historical data. Matching engine produces
simulated fills using accurate assumptions (slippage, commission, latency, venue liquidity — NOT face-value odds).
Execution alpha = live fills P&L - simulated fills P&L. Saved for execution optimisation separately.

**NEVER:**

- Build standalone backtest engines that settle inline (e.g., `returned = stake * odds if won else 0`)
- Treat batch mode as "just replay data" — it must exercise the full service mesh
- Distinguish "live strategies" from "batch strategies" — there is no such distinction
- Build asset-group-specific backtest engines that bypass the unified pipeline

99% of the code path is identical between batch and live. The only seam that differs is the execution fill source
(matching engine vs real venue).

## System-First Architecture (No Ad-Hoc Solutions)

The 67-repo Unified Trading System already covers every domain. Before implementing anything — feature, fix, refactor,
new capability — **look at the existing system first**. Do NOT build ad-hoc solutions, duplicate sources of truth, or
create unnecessary repos/files. If a library is missing a feature, ADD the feature to the library. If the library's
approach is wrong, FIX it. Never work around it.

Key repo mapping: events → `unified-trading-library`, schemas → `unified-api-contracts` (external + internal via
`unified_api_contracts.internal`), cloud → `unified-cloud-interface`, config → `unified-config-interface`, market data →
`market-tick-data-service` (market_interface sub-package; UMI archived), execution (CeFi/DeFi/sports) →
`execution-service`, position → `position-balance-monitor-service`, reference data → `instruments-service` (URDI still
exists as library; sports/ sub-package in URDI), domain utils / ML / feature orchestration / feature calculators →
`unified-trading-library` (domain_client/, ml/, feature_service_base/, feature_calculator/ sub-packages), features →
`unified-features-interface`, sports reference → `unified-reference-data-interface` (sports/ sub-package), execution
algos / matching engine → `execution-service` (algo_library/, matching_engine/ sub-packages), UI → check existing 13 UIs
first.

**Citadel Import Rules (UAC):** All consumer repos import from UAC domain facades only
(`from unified_api_contracts.{domain} import ...`). Never import from `unified_api_contracts.canonical.*` or
`unified_api_contracts.normalize_utils.*` — those are UAC-internal. See `imports/uac-import-surface-enforcement.mdc`.

Full decision tree: `SUB_AGENT_MANDATORY_RULES.md` §0.

## Plan Format (Cursor Checkboxes)

When creating or editing plans in `plans/active/` or `plans/ai/`, every todo's first content line MUST start with a
Markdown checkbox: `- [x]` for done, `- [ ]` for pending. Format: `- [x] [SCRIPT] P0. Description...` or
`- [ ] [AGENT] P0. Fix...`. This ensures Cursor Plan Mode renders filled vs hollow circles correctly. See
`plans/PLAN_FORMAT.md` § Cursor-Friendly Todo Checkboxes.

## Citadel-Grade Planning Standards

Every plan MUST follow these standards. Agents creating plans that don't meet these standards MUST be corrected.

### 1. Pre-Audit Before Execution

Before writing any code, audit the blast radius:

- Search the entire workspace for every import/reference to symbols being moved, deleted, or renamed
- Build a **pre-audit manifest**: repo, file, line number, import statement, action needed
- Embed the manifest in the plan so executing agents don't need to re-scan
- If working with a subset of repos (background agent), document what you CAN'T verify

### 2. Phased Execution DAG

Plans MUST define execution phases with clear dependencies:

- **Phase N** items run in parallel within the phase
- **QG gates** between phases — next phase cannot start until prior phase QG passes
- Mark items as PARALLEL or SEQUENTIAL explicitly
- Draw the dependency graph (ASCII or Mermaid) in the plan context section

### 3. No Technical Debt

- No backwards compatibility shims, re-exports of old paths, or deprecation wrappers
- Clean breaks: old implementation deleted, new implementation in place, consumers updated
- **Exception**: When working on a single repo without all downstream siblings available, backwards compatibility IS
  allowed temporarily. Document it as a follow-up todo.
- When all 60+ repos are available (full workspace): zero technical debt, update everything

### 4. Parallelization

- Maximize parallel execution. If items have no dependency, they MUST be marked PARALLEL
- Group independent items into parallel batches
- Use separate agents for parallel work where possible
- Document the parallelization strategy in the plan

### 5. Success Criteria

Every plan MUST declare explicit success criteria per phase:

- **Code gates**: quality-gates.sh pass, basedpyright clean, ruff clean
- **Test gates**: unit tests pass, integration tests pass (specify which)
- **Deployment gates**: D1-D5 (if applicable)
- **Business gates**: B1-B6 (if applicable)
- The final phase MUST include workspace-wide QG validation of all affected repos

### 6. Downstream Consumer Updates

When modifying shared libraries (UAC, UTL, UCI, UEI):

- Pre-audit identifies EVERY downstream consumer
- Plan includes explicit fix items for each affected repo
- No "fix later" — all consumers updated in the same plan
- Quality gates run on each affected downstream repo

### 7. Single Source of Truth

- Types/schemas belong in ONE place. UAC for external data normalization, `unified_api_contracts.internal` for internal.
- No service should self-declare types that exist in contracts libraries
- No re-definition of enums, dataclasses, or Pydantic models that already exist upstream
- Pre-audit should catch self-declared duplicates and include them in the fix manifest

## Sub-Agents & Autonomous Agents: Full Rules Required (MANDATORY)

Sub-agents (Task tool, mcp_task) and autonomous agents (GHA workflows, Claude Code `--print`, Cursor background agents)
start with FRESH context and do NOT inherit your rules. Reduced context makes them miss rules unless you explicitly
provide them.

**CRITICAL: Agents in `--print` mode CANNOT read files from disk.** Telling them "read .cursorrules" is useless — they
never see it. Rules MUST be pasted directly into the prompt text.

**When launching ANY sub-agent or autonomous agent:**

1. **For local scripts:** Use `inject-mandatory-rules.sh`:
   ```bash
   RULES=$(bash unified-trading-pm/scripts/agents/inject-mandatory-rules.sh "$WORKSPACE_ROOT" "$REPO")
   ```
2. **For GHA workflows:** Load rules via `GITHUB_ENV` heredoc in a prior step, then prepend `${MANDATORY_RULES}` to the
   prompt.
3. **For Cursor/Claude Code sub-agents (Task tool):** Paste contents of
   `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the TOP of the prompt.
4. **If paste is impractical:** Include at TOP: "Before any action, read
   unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md and follow ALL rules strictly."
5. **Always include:** WORKSPACE_ROOT path. For tests: `cd <repo> && bash scripts/quality-gates.sh` (per-repo .venv).
   Never .venv-workspace for pytest.
6. **If rules injection fails, the agent MUST NOT proceed.** Exit with error.

Never rely on sub-agents "inheriting" rules — they cannot. Always inject the full rules. **SSOT:**
`unified-trading-pm/scripts/agents/inject-mandatory-rules.sh`

## Analysis Rules

When analyzing codebase architecture:

- EXCLUDE: .venv*, venv/, node_modules/, build/, dist/, *.egg-info/
- EXCLUDE: Documentation files (\*.md) when counting code usage
- EXCLUDE: Shell scripts when analyzing Python patterns
- FOCUS: Python source files in service directories only
- Use: `--glob '!.venv*' --glob '!**/.venv*/**'` with ripgrep

## Correct search commands for architectural analysis

```bash
rg "pattern" --type py --glob '!.venv*' --glob '!build' --glob '!tests'
grep -r "pattern" --include="*.py" --exclude-dir=".venv*" --exclude-dir="tests"
```

## Workspace Configs (Canonical in PM)

- **Canonical:** `unified-trading-pm/cursor-configs/`
- **Symlink:** `.cursor/workspace-configs` → `unified-trading-pm/cursor-configs`
- **Setup:** `bash unified-trading-pm/scripts/workspace/setup-workspace-config-symlink.sh`

**Workspaces:**

- `unified-trading-system-repos.code-workspace` — curated multi-repo set (~50 sibling repos + root / `.cursor` /
  `.venv-workspace`; edit `folders` in PM when the set changes)
- `workspace-libraries` — T0–T2 libraries
- `workspace-uis` — UI repos
- `workspace-trading` — execution, strategy, risk
- `workspace-data-pipeline` — instruments, market data, features
- `workspace-ml` — ML services
- `workspace-features` — feature services
- `workspace-infrastructure` — deployment, infra
- `workspace-complete` / `workspace-full-pipeline` — all repos

All paths use `${workspaceFolder}` — portable across users. Strict basedpyright (reportAny, reportUnknownMemberType,
reportUnknownVariableType = error).

## UAC Citadel Architecture

This repo uses a facade pattern with per-source co-location.

**Current layout**: `canonical/domain/` (sub-packages), `canonical/crosscutting/`, `external/{source}/` (flat, 80+
dirs), `normalize_utils/` (internal), `registry/`, root facades (market.py, execution.py, etc.)

**Deleted dirs** (do NOT reference): `canonical/normalize/`, `external/sports/`, `external/cloud_sdks/`,
`external/onchain/`, `external/macro/`, `schemas/`, `shared/`

**Import rules**: Services use `from unified_api_contracts import X` or `from unified_api_contracts.{domain} import X`.
Deep paths (`canonical.*`, `normalize_utils.*`) are UAC-internal only. SSOT:
`unified-trading-pm/codex/02-data/contracts-scope-and-layout.md`
