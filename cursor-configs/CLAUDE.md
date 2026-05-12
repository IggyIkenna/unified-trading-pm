# Unified Trading System — Claude Code Instructions

> **Lean index** of workspace rules. Each rule has a 1-line essence + a pointer to its full SSOT (codex doc, plan, or
> code). When a rule applies to your current task, **Read the pointer for full text + edge cases** — don't act from
> memory of an older CLAUDE.md.
>
> Trim 2026-05-11: was 2758 lines / 211KB; now ~999 lines / ~58KB. SSOT pointers added; mature wisdom moved to codex.

---

## Environment: Venv Split (SSOT: `cursor-rules/venv-usage-ssot.mdc`)

| Use case                  | Venv                        | Command                                                      |
| ------------------------- | --------------------------- | ------------------------------------------------------------ |
| **Quality gates / tests** | Repo `.venv`                | `cd <repo> && bash scripts/quality-gates.sh` — no activation |
| **IDE / general Python**  | Workspace `.venv-workspace` | `source ${WORKSPACE_ROOT}/.venv-workspace/bin/activate`      |

**Never** run `pytest` directly — wrong venv. Always `quality-gates.sh`. Set
`WORKSPACE_ROOT="${UNIFIED_TRADING_WORKSPACE_ROOT:-.}"` for general Python work.

---

## Master Plan — Live DeFi Trading by 2026-05-23

Two DeFi archetypes (`carry_staked_basis` lead + `leveraged_funding_arb`) live on a real wallet ≥7 continuous days by
2026-05-23, with hedge legs across 6 perp venues + AWS↔GCP cloud parity.

- **Working plan**: `plans/active/master_to_live_defi_2026_05_23.md`
- **Codex SSOT companion**: `codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md`
- **Principle**: **docs are the intent**. Order: doc → plan → code. Drift between any pair is review-blocking.
- **Per-service readiness checklist**: 7 groups / 23 items (A code-health · B data-correctness · C runtime-parity · D
  coverage · E operability · F trading-prereq · G operator-UX). Live-only items: F+G cover paper-trade / Copper+CEFFU /
  live-testnet / batch-vs-live recon / circuit-breakers / DART manual-trade gate.

---

## Rules: Read Before Coding

1. `.cursorrules` — workspace standards (uv not pip, quickmerge not git push, etc.)
2. `.cursor/rules/no-empty-fallbacks.mdc` — no try/except fallback imports
3. `.cursor/rules/no-type-any-use-specific.mdc` — no Any types
4. `unified-trading-pm/codex/06-coding-standards/README.md` — coding standards
5. `unified-trading-pm/plans/PLAN_FORMAT.md` — plan format; Cursor checkboxes (`- [x]` / `- [ ]`) required
6. **Asset-group vocabulary**: venue axis is `asset_group` (not `category`). CLI flag `--asset-group`, env vars
   `VM_ASSET_GROUP` / `MDPS_ASSET_GROUP`. Dict KEYS stay lowercase (`cefi`/`defi`/`tradfi`/`sports`/`prediction`). GCS
   hive-key: `asset_group=` canonical (per `market_tick_data_service/raw_tick_hive.py`); `category=` legacy (preserved
   on disk; readers try canonical → fall back). Plan: `plans/active/venue_axis_asset_group_vocabulary_2026_04_25.md`.

---

## Key Rules (Quick Reference)

### Dependencies + builds

- **Flat deps only** — every `pyproject.toml` has ONE `[project.dependencies]`. No `[project.optional-dependencies]`. No
  `.[dev]` extras.
- `uv pip install` not `pip install`.
- Dockerfiles: `ARG PROJECT_ID` +
  `FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest`
  — never `python:3.13-slim` or `pip install uv`.

### Git discipline

- `bash scripts/quickmerge.sh "msg" --agent` not `git push` for promotion-to-main flows. Always `--agent` in Claude Code
  sessions.
- **DO NOT quickmerge when dep repos are dirty (2026-05-06 rule).** Dirty deps → commit + push directly to
  `live-defi-rollout`. Don't ask user to switch — it's the institutional default.
- Push before quickmerge if you committed locally (quickmerge stash only saves uncommitted).
- Two-pass model: Pass 1 = `bash scripts/quality-gates.sh` (full). Pass 2 = `quickmerge --agent`
  (lint/format/typecheck/codex, no tests).
- `--dep-branch` is human-only — quickmerge exits(1) if combined with `--agent`.

### Imports + types

- `from unified_trading_library.events import setup_events, log_event` — no fallbacks.
- `basedpyright` not `pyright`; always `run_timeout 120 basedpyright <source_dir>/`.
- No `os.getenv()` — use `UnifiedCloudConfig`.
- No `# type: ignore` to hide architectural violations — fix root cause.
- No `try/except ImportError` around library imports — fail loud.
- `logger.warning("%s", _err.message)` not `logger.warning(_err.message)` — the message is not a format string.
- `.env` files NEVER contain placeholder credential paths — ADC is the default.
- Bandit B108: no hardcoded `"/tmp"` — use `tempfile.gettempdir()`. SSOT: `codex/06-coding-standards/quality-gates.md`.

### Service architecture

- Services use **instruments-service** for reference data, not MTDS. MTDS is for market data only.
- Shard-level failure isolation — no `raise` inside per-venue/per-shard loops. SSOT:
  `codex/04-architecture/shard-level-failure-isolation.md`.
- Every adapter MUST classify errors via UAC `classify_venue_error()` + emit `ADAPTER_FETCH_FAILED`.
- **Signal Leasing / strategy-service signal broadcast** uses shard-level isolation + `classify_venue_error()` +
  HMAC-signed counterparty creds via `ApiKeyReloader`. SSOT:
  `codex/14-customer-journeys/shared-core/signal-broadcast-architecture.md`.
- Service CLIs: `--operation` (what) `--mode` (batch/live) `--asset-group` (domain). SSOT:
  `codex/06-coding-standards/cli-convention.md`.

### Manifest + honest absence

- **Availability manifest v5+** — `ManifestWriter` writes shard columns + 4-state `capture_status` (`captured` /
  `empty_confirmed` / `attempted_failed` / `expected_unattempted`). Adapters distinguish `record_captured()` /
  `record_empty(reason=...)` / `record_failed(error=..., attempted_at=...)` / `record_expected_unattempted(...)`. Never
  overload `venue` with non-venue data. Asset-group-specific empty rules: sports/prediction CAN have `empty_confirmed`
  at instrument-day grain; cefi/defi/tradfi CANNOT (only venue-level
  HOLIDAY/WEEKEND/PRE_LAUNCH/PRE_GENESIS/PARTIAL_HALF_DAY are legit). SSOTs:
  `codex/02-data/availability-manifest-and-data-status.md` + writegate plan Phase 3.D.5.
- **Honest absence vs fake placeholders (CRITICAL)** — three categories of "missing":
  1. **Expected upstream-source gap** → `record_empty(reason=<typed>)`. NaN downstream is fine; the crime is masking
     absence.
  2. **Unexpected upstream-pipeline gap** (manifest says captured but row missing) → STOP,
     `DependencyError(fail_fast=True)`.
  3. **Reader/schema-drift bug** (data exists, reader can't find) → RAISE LOUD; never silently emit empty placeholders.
  - Reference incident 2026-05-05 MDPS: 1440 NaN OHLC bars/day for years before hand-inspection caught them. Manifest
    said `captured`; parquet was 1440 rows of garbage. Validation = read sample parquets + assert OHLC populated, NOT
    just count rows. Downstream-consumption SSOT: `codex/02-data/honest-absence-downstream-handling.md`.
- **Four-category empty-output decision** — every adapter resolves blank to: A=`record_empty(reason=)` honest;
  B=`record_failed(UpstreamTimestampBiasError)` partition mislabeled; C=`record_failed(MalformedTickFieldError)` data
  quality; D=write zero-activity bars + `record_captured` (when catalog says alive AND day in market hours). SSOT:
  writegate plan Phase 2.A + Phase 3.D.5.
- **Reason taxonomy** — closed set in UAC `EMPTY_CONFIRMED_REASONS` (17 EXPECTED\_\* + `SOURCE_RETURNED_ZERO`):
  `EXPECTED_HOLIDAY` / `EXPECTED_WEEKEND` / `EXPECTED_PAUSED_LEAGUE` / `EXPECTED_PRE_SOURCE_COVERAGE_START` /
  `EXPECTED_PRE_GENESIS_CHAIN` / `EXPECTED_PRE_VENUE_LAUNCH` (UAC@ac218dc) / `EXPECTED_INSTRUMENT_NOT_LISTED` /
  `EXPECTED_INSTRUMENT_DELISTED` / `EXPECTED_PARTIAL_HALF_DAY` / `EXPECTED_OUTSIDE_TRADING_HOURS` /
  `EXPECTED_OUTSIDE_TRANSFER_WINDOW` / `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON` (Wave 3.X dim #6) /
  `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` (Wave 3.X dim #7) / `EXPECTED_DEPRECATED_DATA_TYPE` /
  `EXPECTED_REFDATA_CADENCE_CHANGE` (manifest_migration_master C.1/C.11) / `EXPECTED_KNOWN_SOURCE_GAP` (UAC@174f401
  2026-05-11) / `SOURCE_RETURNED_ZERO`. Blank reason rejected via `LegacyBlankErrorReasonError`. Canonical enum:
  `unified_api_contracts.canonical.crosscutting.honest_coverage.EmptyConfirmedReason`. SSOT:
  `codex/02-data/honest-absence-downstream-handling.md` § "Reason taxonomy".
- **Cluster validation MANDATORY** at `record_captured()` for bundled data_types (`options_chain`, `futures_chain`,
  `prediction_canonical_question_group`, sports per-fixture-bundles). UTL guard raises `MissingClusterValidationError`
  if `expected_root_clusters` + `cluster_extractor` kwargs absent. QG STEP 5.64 enforces statically. SSOT: writegate
  plan Phase 1A.
- **`available_at` is per-row, write-time, equal to live-pipeline-arrival**. Stamping helpers:
  `unified_trading_library.availability_stamping.stamp_available_at_*`. UTL `record_captured` calls
  `assert_available_at_present` internally. SSOT: UAC `availability_semantics.AVAILABILITY_AT_SEMANTICS`.
- **Service-output emission policy (writegate slice b/c)** — every service publish path through
  `_resolve_policy_output_data_type` + `_publish_emission_check` (generalised publisher; ohlcv_1h-specific helpers
  deleted — no double SSOT). Slice (b) MDPS POC shipped 2026-05-11; slice (c) Phase 6.2+ generalised across `ohlcv_1h` /
  `ohlcv_1m` / `ohlcv_24h` / `book_snapshot_5`; remaining 8 services rolling out via Phase 6.3-6.9. SSOT:
  `codex/02-data/service-output-emission-semantics.md` + `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`
  slice (b)+(c).
- **Prediction market lifecycle timing** — instruments capture `market_created_at` / `resolution_time` /
  `settlement_time` per market_id + `canonical_question_group` membership. MTDS CLOB respects lifecycle bounds. Plan:
  `plans/active/predictions_master_2026_05_07.md`.

### Shard-granularity SSOT (CRITICAL)

Shard atom MUST be identical across (a) writer atomicity, (b) manifest row key, (c) data-status display, (d) downstream
pre-flight gate, (e) deployment-UI drilldown. Drift between any two = silent correctness bug. Per-asset-group matrix

- layer discipline ([UAC] / [UTL] / [per-service] / [deployment-api+ui]) + 4-pillar validation gate (row count > 0 OR
  `record_empty`; NaN ratio < threshold; schema matches contract; cluster coverage ≥ expected for bundled). SSOT:
  `plans/epics/infrastructure_master_2026_05_07.md` + archived
  `plans/archive/shard_granularity_ssot_propagation_2026_05_06.plan.md` + `.HANDOVER.md`.

### Live = batch (CRITICAL)

Live and batch are operational modes of the SAME pipeline. Identical schemas, identical data_types, identical fields.
Only legitimate diff is which SOURCE serves a given `(asset_group, data_type)` (some sources lag real-time). Historical
writes timestamped with the `available_at` we'd actually have in live mode (UAC SOURCE_PRIORITY top entry's emission
time). Banned: separate live-only data_types (`LINEUPS_PRE_MATCH` vs `LINEUPS_POST_MATCH`); distinct field sets between
live + batch parquets; deriving `available_at` at read-time. SSOT: writegate plan
`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`.

### Bucket-name SSOT (b+) — env-aware bucket architecture (codified 2026-05-11)

`deployment-service/configs/cloud-providers.yaml` is canonical. Every bucket lookup goes through
`unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud=..., kind=..., asset_group=..., env=...)`
— never inline f-string `gs://{bucket}/...` (QG STEP 5.69 ratchet enforces). Env tier (`${DEPLOYMENT_ENV}` →
staging/prod/development) extends to ALL buckets across both clouds. `pipeline_mode` lives in PATH, NOT bucket name.
Region-pinned: GCP `asia-northeast1`, AWS `ap-northeast-1` (Tokyo same-metro, ~5× cheaper egress). VM launchers MUST
read `DEPLOYMENT_ENV`. SSOT: `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md` +
`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`.

### Other key rules (SSOT pointers)

- **Sports GCS path SSOT**: `unified_api_contracts.sports.candidate_parquet_paths()` etc. Module:
  `unified_api_contracts/canonical/domain/sports/gcs_paths.py`. Reference: 2026-04-29 phantom-row audit incident.
- **Sports source coverage windows**: UAC `SOURCE_COVERAGE_START` + `DATA_TYPE_COVERAGE_START` + `KNOWN_COVERAGE_GAPS`
  - `clip_dates_to_source_coverage()` + `is_in_known_gap()`.
- **VIX 15m source layering**: Barchart preload (2020-01-02 → 2025-11-12) + Yahoo rolling 60d window + 2025-11-13 →
  today−60d honest gap. UAC `BARCHART_VIX_FIRST/LAST_DATE`, `YAHOO_VIX_15M_WINDOW_DAYS`, `is_vix_15m_gap_date()`. Route:
  MTDS `umi_tick_provider.py` (CBOE, ohlcv_15m) → `_fetch_yahoo_vix_15m` BEFORE generic Databento.
- **Manifest concurrency principle** — read-once + per-date freshness check + write-time CAS for any multi-worker
  manifest consumer. TTL 60s. Reference impl: `/tmp/fill_missing_ohlcv.py` (`_refresh_captured_cache`). SSOT:
  `codex/02-data/availability-manifest-and-data-status.md`.
- **Manifest phantom audit** —
  `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group X --dry-run`. Always run on
  same-region GCE VM. SSOT: `codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit". Do NOT write
  empty placeholder parquets to mask phantoms.
- **VM tarball deployment** — refresh tarballs after every code change with
  `bash deployment-service/scripts/vm/create-code-tarballs.sh <flag>`. SSOT:
  `codex/05-infrastructure/vm-tarball-deployment.md`.
- **VM launcher script SSOT** — every `gcloud compute instances create` lives under `deployment-service/scripts/vm/`. No
  exceptions. SSOTs: `codex/05-infrastructure/launcher-script-ssot.md` +
  `codex/05-infrastructure/vm-tarball-deployment.md`.
- **VM Naming Convention** — first segment must be a prefix in `VM_PREFIX_TO_BUCKET` in
  `deployment-service/scripts/vm/vm_zombie_watchdog.py`. After dict edit, **relaunch watchdog VM**. Without dict
  registration, VM is invisible to zombie watchdog (silent money burn). Reference incident 2026-05-05.
- **Singleton-locked launchers** — adapters with shared API keys / per-IP rate limits use a singleton-lock pattern
  (refuses launch if same-prefix VM RUNNING in zone; `--force` bypass). Reference: SFI 2026-04-19 thundering herd.
- **No fire-and-forget VM launches (CRITICAL)** — every VM launch paired with active event-stream verification. Events
  at `gs://{pid}-events/events/{service}/{YYYY-MM-DD}/{correlation_id}/hour={H}/*.jsonl`. Required: `STARTED` within
  60s + ≥1 progress event/hour + `STOPPED`/`FAILED` at exit. SSH-tailing logs is a dev crutch; production runs through
  `unified-events-interface` UI. Reference: 2026-05-05 MDPS 21 VMs emitted STARTED+STOPPED but output was 1440 empty
  placeholder bars per day.
- **Per-VM shard isolation** — every multi-worker backfill MUST set `VM_NAME=<unique-tag>` +
  `MANIFEST_PER_VM_SHARDS=true`. `ManifestWriter` raises `MultiWorkerWithoutShardIsolationError` if missing. QG STEP
  5.66 enforces.
- **Temporary state must have a named successor plan** — partial implementations require a
  `## Temporary states + their canonical follow-up plans` section listing successor plan filenames. Reviewers reject
  partials lacking a successor reference.

### Two teammates × multiple parallel agents (CRITICAL)

Harsh AND Ikenna both work this workspace, **each running multiple parallel agents**. Untracked files in any repo, dirty
mid-edit state, or remote commits in last few minutes are almost always someone else's in-flight work. **Do not touch
files outside your clear context** to clear a QG gate.

- **Never** `git checkout origin/<branch> -- .` (dumps remote work into your tree).
- **Never** `git checkout -- <file>` to revert a tool's modifications on a foreign-owned dirty file — UNRECOVERABLE
  (discards their unstaged WIP).
- Right recoveries when a tool modifies foreign files: (a) scope tool to YOUR files; (b) stash foreign-modified files
  before tool runs (`git stash push --keep-index -- <files>`); (c) accept you can't auto-fix foreign code; (d) if
  already mass-modified, use `git commit --only -- <my-files>`.
- **Untracked file in a dep repo = NOT YOURS.** Reference incident 2026-05-06 PM `pipeline-coverage-matrix.md`.
- Right escape valve when QG fails on file you don't own: tell the user.

Reference incident **2026-05-08 Foot-gun #2** (ruff sweep): `ruff check . --fix --unsafe-fixes` modified 116 files
including 12 with foreign agent's uncommitted WIP. `git checkout --` to revert ruff's modifications discarded BOTH
ruff's fix AND foreign agent's WIP. ~12 files of consolidation work lost. Right behaviour was (a) scope ruff to your
files OR (b) stash dirty files before ruff. Issue doc:
`plans/active/issues/foot_gun_2_features_service_uncommitted_wip_clobbered_2026_05_08.md`.

### Clear context = implement, don't ask

When the plan / SSOT / prior turns name the canonical approach with a `[SCRIPT] P0` todo (file:line + exact change),
**ship it**. Asking when the answer is specified wastes operator time. Don't apply when destructive beyond
authorization, foreign files involved, or plan says "AWAITING USER DIRECTION." Reference 2026-05-06 user direction:
_"you are a grown up man, please take the decisions on your own for such trivial minor things"_.

---

## Service Infrastructure Requirements (QG-Enforced as ERRORS)

- **STEP 5.61** `ServiceBootstrap(...)` must appear in service source — handles STARTED/STOPPED/FAILED.
- **STEP 5.62** `api/main.py` with `make_health_router` from UTL + `data_freshness` callback.
- **STEP 5.34** `config_reloaders.py` uses typed config class — never `object` or `getattr(service_config, ...)`.
- **Schema provenance** — domain types from UAC (or `unified_api_contracts.internal`) — no local definitions.
- **API key hot-reload** — `ApiKeyReloader` from UTL, not one-shot `validate_api_keys_for_venues()`. SSOT:
  `codex/06-coding-standards/config-reloader-pattern.md`.

---

## DeFi Execution Architecture

Pointer chain. Full specs in codex:

- **Interface credential convention**: `codex/04-architecture/interface-credential-convention.md`. Trade execution:
  `get_order_adapter(venue, api_key, api_secret, ...)`. DeFi: `connector.connect(config={...})`. Sports:
  `adapter(credentials={...})`.
- **RPC URL templates**: `CHAIN_RPC_TEMPLATES` in UAC `registry/capability_declarations/_defi.py` — SSOT.
- **Flash loan receiver**: deployed Solidity contract required for Aave. Source:
  `deployment-service/contracts/FlashLoanReceiver.sol`. Address in UAC `config/testnet_contracts.yaml`. SSOT:
  `codex/04-architecture/flash-loan-receiver.md`.
- **Contract registry schema**: `unified-trading-library/unified_trading_library/config_interface/testnet_contracts.py`
  `PROTOCOL_SCHEMAS` dict + `TestnetContractRegistry` class + `get_testnet_contract_registry()` accessor — validates
  `config/testnet_contracts.yaml` at load (corrected from stale `unified-config-interface/testnet_contracts.py` per slot
  8 audit EX-2).
- **Uniswap live swap**: execution-service `UniswapConnector.swap_exact_input()` via SwapRouter02
  `0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45`.
- **DeFi error classification**: 13 codes in UAC
  `unified_api_contracts.canonical.crosscutting.errors.defi.DefiErrorCode`, consumed by execution-service DeFi
  connectors (e.g. `protocols/aave.py` imports `DefiErrorCode` from UAC). Routes on FAIL/RETRY/SKIP prefix (corrected
  from stale "in execution-service `DefiErrorCode` (aave.py)" per slot 8 audit EX-5).
- **DeFi pipeline flow**: instruments-service → MTDS → features-onchain → strategy → execution. All via service CLIs.
- **Removed providers** (do NOT reference): Elysium, Arkham, Bloxroute, Infura.
- **Pyth — UNBANNED 2026-05-06** for Solana on-chain price feeds (Hermes batch + PythNet live). Solana-only; other
  chains use Chainlink. Plan: `plans/active/defi_master_2026_05_07.md`.

---

## Version Graduation (1.0.0 Process)

All repos start 0.x.x. Pre-1.0.0 override: `feat!` on 0.x.x = MINOR not MAJOR. **NEVER bump versions manually** —
semver-agent handles all bumps on merge.

Graduate to 1.0.0:

1. GitHub Actions → `request-major-bump` workflow → proposed_version=1.0.0
2. Or CLI: `gh workflow run request-major-bump.yml --repo IggyIkenna/<repo> -f proposed_version="1.0.0" -f reason="..."`
3. Comment `/approve` on the auto-created GitHub Issue
4. Bump → staging → SIT → main

Post-1.0.0: `feat!` = MAJOR (opens approval issue).

---

## PM/Codex Doc-Only Fast-Path

When quickmerging PM or codex repos:

- **Plans, docs, cursor rules** (`plans/`, `docs/`, `cursor-configs/`, `cursor-rules/`, `*.md`, `*.mdc`) → PR targets
  **main** directly.
- **Scripts, workflows** (`scripts/`, `.github/workflows/`) → PR targets **staging** (full SIT cycle).

---

## Plan Locking

`locked_by: <branch>` in frontmatter prevents archival without `[unlock-plan]` in commit message. Lock: add
`locked_by: live-defi-rollout` + `locked_since: <YYYY-MM-DD>`. Unlock: remove fields + include `[unlock-plan]` tag.
**Agents may ASK operator to unlock; never unlock autonomously.**

---

## Plan Archival — preserve deferred work + operational gaps (HARD RULE)

**Archive boundary is an audit boundary, not a deletion event.** Before archiving:

1. **Audit the plan body** — scan for `**DEFERRED**` / `**NICE-TO-HAVE**` / `**DEFERRED-PER-USER**` / "post-cutover" /
   "out of scope" / "future work" / "stretch" / "follow-up" annotations.
2. **Audit operational completeness** — for every "shipped" item touching VM launch / backfill / migration / deploy,
   verify the operation actually ran in production (event streams / VM history / manifest state / migration ledger).
   **Code-shipped is not operationally-shipped.**
3. **Migrate every deferred item** to an active home: (a) fold into existing active plan with `**MIGRATED FROM:**`
   provenance line; (b) spawn new active plan with `migrated_from:` frontmatter; (c) write
   `plans/active/issues/<slug>_<YYYY_MM_DD>.md` if no plan owns it (resolve to a plan within ≤7 days).
4. **Banner the archived plan** with `## Deferred work — migrated to:` enumerating every migrated item + destination.
5. **Update CLAUDE.md / codex** if any deferred item affects a workspace contract.

Operational verification probes: VM-finished (`gcloud compute instances list` absence + STARTED+STOPPED in events);
backfill-complete (manifest captured rows match planned scope; sample parquet OHLC populated, not 1440-NaN);
migration-ran (post-migration on-disk schema matches new shape; legacy reader paths deleted); deploy-promoted
(`gcloud run services describe` revision matches main).

Composes with: Plan Locking (technical gate); Temporary state must have a named successor plan; Commit + Push + Flip;
Findings Triage Discipline (issue-doc disposition); Capture Discoveries As Plan Todos; Post-Plan-Phase Codex Audit;
Citadel-Grade Planning § 3 + § 7.

---

## Workflow Templates (Canonical in PM)

**Templates SSOT**: `unified-trading-pm/scripts/workflow-templates/`. **Never edit per-repo workflow copies directly** —
edit the PM template, then run rollout: `bash unified-trading-pm/scripts/propagation/rollout-workflow-templates.sh`
(generic) or `rollout-semver-agent.sh`.

| Workflow                        | Pattern                        | Why                               |
| ------------------------------- | ------------------------------ | --------------------------------- |
| `request-major-bump.yml`        | Reusable (`workflow_call`)     | dispatch supports forwarding      |
| `major-bump-issue-handler.yml`  | Canonical template (flat copy) | issue_comment can't forward       |
| `staging-lock-check.yml`        | Canonical template (flat copy) | pull_request can't forward        |
| `update-dependency-version.yml` | Canonical template (flat copy) | repository_dispatch can't forward |
| `semver-agent.yml`              | Template + substitution        | repo-specific env vars            |

---

## Force-Sync Warning (CRITICAL)

`admin-force-sync-all-to-main.sh` overwrites remote main with local HEAD. **Can revert remote-only changes** —
especially version bumps from semver-agent / major-bump-approval workflows. Before any force-sync:

1. `bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh` — step [0.96] checks remote drift.
2. Resolve drift: `git fetch origin staging && git checkout origin/staging -- pyproject.toml` per repo.
3. Re-run version alignment after to confirm no remote bumps reverted.

---

## Testing Infrastructure (Emulators & Mocks)

Tests run credential-free (`CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`). SSOT:
`plans/archive/cicd_mock_hardening_2026_03_11.plan.md`.

- **GCP Emulators**: `PUBSUB_EMULATOR_HOST=localhost:8085`, `STORAGE_EMULATOR_HOST=http://localhost:4443`,
  `BIGQUERY_EMULATOR_HOST=localhost:9050`.
- **AWS**: `@mock_aws` decorator (moto).
- **Network blocking**: `pytest --block-network`; `@pytest.mark.allow_network` opts out.
- **WS tests**: `MockWebSocketFeed` from MTDS `tests/market_interface/fixtures/mock_ws_server.py`.
- **DeFi unit tests**: `responses` library (Hyperliquid REST). Mock Web3 at signing level — never hit real RPCs.
- **DeFi integration tests**: shared Tenderly fork fixtures in `execution-service/tests/integration/conftest.py`.
- **Local stack**: `bash unified-trading-pm/scripts/demo-mode.sh --seed`.
- **Cassette parity**: `cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py` (every commit).

---

## Local Development

Full guide: `codex/08-workflows/local-dev.md`.

### Deployment-stack restart (SSOT)

For deployment-api (port 8004) + deployment-ui (port 5183):

```bash
bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh           # both
bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --api      # api only
bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --ui       # ui only
bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --stop     # stop both
```

Always real cloud mode (`CLOUD_PROVIDER=gcp`, `CLOUD_MOCK_MODE=false`). Hardcoded ports 8004/5183 — UI dials 8004
verbatim on `localhost`.

### Other tiers

```bash
# Tier-based (preferred — UI repo)
cd unified-trading-system-ui && bash scripts/dev-tiers.sh --tier 0    # default: Firebase emulators + Next dev + auto-seed
bash scripts/dev-tiers.sh --tier 1   # + 2 API gateways
bash scripts/dev-tiers.sh --tier 2   # full fleet
bash scripts/dev-tiers.sh --stop / --status

# Legacy PM-based
bash unified-trading-pm/scripts/dev/dev-start.sh --all --mode mock
bash unified-trading-pm/scripts/dev/dev-stop.sh
bash unified-trading-pm/scripts/dev/dev-status.sh
```

Runtime tiers: `codex/05-infrastructure/runtime-tiers-and-deployment.md`. Firebase-local:
`codex/14-customer-journeys/authentication/firebase-local.md`.

### Mode axes + presets

5 axes: `VITE_MOCK_API` / `VITE_SKIP_AUTH` / `CLOUD_MOCK_MODE` / `DISABLE_AUTH` / `MOCK_STATE_MODE`. Presets:
`--mode ci|mock|api-real|real`.

### Cache cleanup

```bash
bash unified-trading-pm/scripts/dev/dev-stop.sh --clean     # stop + wipe .local-dev-cache/
bash unified-trading-pm/scripts/dev/dev-start.sh --reset
```

UIs 5173-5183, APIs 8004-8016. Port registry: `unified-trading-pm/scripts/dev/ui-api-mapping.json`. Vitest:
`pool: "forks"` only.

---

## This is a Multi-Repo Workspace (NOT a monorepo)

Each subdirectory is independent git repo. Only commit to target repo. **Never** run `basedpyright .` from workspace
root — always per-repo with timeout.

---

## Batch = Live: Unified Pipeline Architecture (CRITICAL)

Batch + live use SAME code path, same component interactions. ONLY difference: execution fills. Applies to ALL
asset_groups.

- **Strategy P&L backtest** (strategy alpha): strategy-service interacts with position-balance-monitor,
  risk-and-exposure-service, execution-service (in "always fill" mode). Goes through ALL normal component interactions.
- **Execution alpha measurement**: execution-service has matching engine for historical data (slippage, commission,
  latency, venue liquidity). Execution alpha = live fills P&L − simulated fills P&L.
- **Never**: build standalone backtest engines that settle inline; treat batch as "just replay data"; distinguish "live
  strategies" from "batch strategies"; build asset-group-specific backtest engines.

99% of code path identical between batch + live. Only seam that differs is the execution fill source.

---

## System-First Architecture (No Ad-Hoc Solutions)

Before implementing anything — feature, fix, refactor — **look at the existing system first**. Do NOT build ad-hoc
solutions, duplicate sources of truth, or create unnecessary repos/files. If a library is missing a feature, ADD it. If
the library's approach is wrong, FIX it. Never work around it.

Key repo mapping: events → UTL · schemas → UAC (external + `unified_api_contracts.internal` for internal) · cloud →
unified-cloud-interface · config → unified-config-interface · market data → MTDS (UMI archived) · execution →
execution-service · position → position-balance-monitor-service · reference data → instruments-service · domain utils

- ML + feature orchestration → UTL · features → unified-features-interface · sports reference → URDI · execution algos
- matching engine → execution-service · UI → check existing 3 UIs first (`unified-trading-system-ui` consolidated
  portal + `deployment-ui` + `user-management-ui`).

**Citadel Import Rules (UAC)**: consumer repos import from UAC domain facades only
(`from unified_api_contracts.{domain} import ...`). Never `unified_api_contracts.canonical.*` or
`unified_api_contracts.normalize_utils.*` — UAC-internal. SSOT: `imports/uac-import-surface-enforcement.mdc`.

Full decision tree: `SUB_AGENT_MANDATORY_RULES.md` §0.

---

## Plan Format (Cursor Checkboxes)

Every todo's first content line MUST start with `- [x]` / `- [ ]`. Format: `- [x] [SCRIPT] P0. Description...`. SSOT:
`plans/PLAN_FORMAT.md` § Cursor-Friendly Todo Checkboxes.

---

## Plan Filename Convention + 3-Layer Model (codified 2026-05-08)

| Directory                     | Extension                                               |
| ----------------------------- | ------------------------------------------------------- |
| `plans/active/`               | `<slug>.md`                                             |
| `plans/epics/` (masters)      | `<slug>.md`                                             |
| `plans/epics/` (May-23 epics) | `<slug>.epic.md`                                        |
| `plans/archive/`              | `<slug>.plan.md` (DO NOT rename)                        |
| `plans/ai/`                   | `<slug>.plan.md` (promotion to active renames to `.md`) |

**3-layer model**: cutover master (`master_to_live_defi_2026_05_23.md`) → epics (`plans/epics/*.epic.md` for May-23,
`*.md` for granular masters) → granular sub-plans (`plans/active/*.md`). None duplicates content; each adds
orchestration above the layer below.

SSOTs: `plans/epics/README.md` + `plans/PLAN_FORMAT.md`.

---

## Capture Discoveries As Plan Todos Immediately (HARD RULE)

Every side-discovery during plan execution (bug in adjacent code, edge case the plan missed, refactor that compounds
value, nice-to-have, deferred follow-up, doc update) MUST go into a plan todo at the moment it surfaces. Same logical
unit as the discovery. Tag P0-P3 + `**DEFERRED**` / `**NICE-TO-HAVE**` / `**DEFERRED-PER-USER**` body prefix +
provenance. **Never just auto-memory. Never just chat summary.**

**End-of-cycle audit clause**: before declaring done, every deferral in your end-of-cycle summary MUST already be a
`- [ ]` plan todo or `**DEFERRED**` annotation in `plans/active/`. Recipe: grep for distinctive phrase per deferral
line; match → cite file:line; no match → STOP, add todo, push the flip, then resume. Reviewers reject summaries with
grep-miss deferrals.

Anti-patterns: "I'll mention it in chat" (chat scrolls); "auto-memory will save it" (it's recall, not planning); false
checkbox flips (flip only the half that landed; leave deferred half `- [ ]` with annotation); end-of-cycle summary as
planning surface.

Composes with: Commit/Push/Flip; Plan Archival; Findings Triage; Cross-Plan Banners; Plans Run To Actual Completion.

---

## Active Plan Inventory + Done-vs-Left Dashboard (auto-tracked)

Workspace-wide plan tracking surface. `unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py` scans every
`plans/active/*.md` with `estimate_class` frontmatter, counts done/todo checkboxes, computes
`cal_remaining = estimate_calibrated_ai_days × todo/(done+todo)`, looks up epic owner via reference grep across master +
`plans/epics/*.md`, writes a sorted markdown table (cal_left desc) between `<!-- AUTO-INVENTORY-START -->` and
`<!-- AUTO-INVENTORY-END -->` markers in `master_to_live_defi_2026_05_23.md` § "Active plan inventory + Done-vs-Left
dashboard".

**Run cadence** (main-orchestrator slot 1, both sides): morning ledger sweep + EOD + before any planning decision that
depends on done-vs-left state. Idempotent; only rewrites content between markers.

```bash
python3 unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py
```

**Reads** in the dashboard: `Plan | Owner | Class | Checkboxes | % done | Cal left | Deadline`. Owner = `master` /
`<epic-name>` / `**orphan**` (not referenced by master or any epic — fold into appropriate epic on owner agent's next
plan-touch, NOT via mass-sweep). TBD baselines (from 2026-05-11 calibration sweep scaffold) show `Cal left: TBD` until
owner agent fills the baseline.

**Note on the master plan filename**: `master_to_live_defi_2026_05_23.md` is historically named but is actually the
**full May-23 cutover umbrella** across all asset groups (DeFi + CeFi + TradFi + Sports + Predictions + cross-cutting),
per its own Epics index. The inventory tracks every active plan workspace-wide.

Full SSOT: `codex/11-project-management/active-plan-inventory-tracker.md` — logic, refresh cadence, how-to-read the
columns, when-to-use vs when-not-to-use, anti-patterns, deferred extensions (QG ratchet, per-epic rollup, cal-weighted
%).

---

## Commit + Push + Flip Plan Checkboxes As You Ship Each Item (HARD RULE)

Two halves; both non-negotiable. Under per-slot worktrees: cross-slot foot-guns #1-#3 unrepresentable. Within-slot
multi-sub-agent fan-out shares index — pre-commit check below applies.

### Half 1 — Commit + push at every shippable unit

A "shippable unit" = smallest meaningful slice that QGs cleanly. Per-shippable-unit cadence, NOT per-hour or
per-session.

- **Pushed = real.** Local-only commit is invisible to other agents + CI + VMs.
- `live-defi-rollout` is the working branch. Push directly when deps dirty:
  `git add <files> && git commit && git push origin live-defi-rollout`.

### The mandatory pre-commit check (catches accidental bundling)

```bash
git status                 # full picture
git diff --cached --stat   # NO PATH ARGUMENT — see entire index
```

If anything not yours: `git restore --staged <file>` or `git stash --keep-index <file>` before commit. **Never** pass a
path arg to `git diff --cached --stat` (foot-gun #2).

Reference incidents (all 2026-05-07 PM, all from concurrent-agent overlap):

- PM@961980db — bundled teammate's local-uncommitted plan section.
- PM@611b9501 — bundled teammate's `git mv` rename.
- PM@7de75819 — parallel-agent's auto-commit swept up your already-staged renames + reset its own commit.

### Foot-gun #4 — prek auto-restore racing your edits

Diagnostic: `"Restored working tree changes from .../prek/patches/"` in commit output OR file shows unmodified after
successful Edit OR commit lands under wrong author with empty diff in `git show --stat HEAD`.

Workaround:

1. Bundle Edit→stage→commit→push into ONE Bash call (no intermediate `git status` between Edit and add).
2. **`--no-verify` IS authorized** when (a) auto-restore symptoms observed in this session AND (b) alternative is losing
   real work. Per 2026-05-08 user direction _"fix to keep your work"_. Don't re-ask each session. **Precedence note (G-3
   reconciliation 2026-05-12)**: the Bash tool description's "never skip hooks unless explicitly asked" rule is the
   DEFAULT; this Foot-gun #4 clause IS the explicit user ask, scoped to prek auto-restore symptoms. The two are NOT in
   conflict — Foot-gun #4 is the explicit authorization the Bash tool description requires; outside this clause (and
   CLAUDE.md "Git Safety Protocol"), `--no-verify` remains forbidden absent operator ask per turn.
3. Verify post-push with `git show --stat HEAD` — if zero insertions to your file, re-Edit + retry.
4. Stage explicitly by name; never `git add .` / `-A`.
5. If repeatedly reverted across multiple Edit attempts, prek patch under `~/.cache/prek/patches/` is restore source.
   Tighter Edit→commit window is the only mitigation today. Per-tree `PREK_CACHE_DIR` (per-tab `.envrc`) reduces races
   (canonical env var per `unified-trading-pm/scripts/dev/setup-tab-worktrees.sh:133` + `codex/05-infrastructure/per-tab-worktrees.md:155`).

### Half 2 — Flip the plan checkbox in the same logical unit

When working a plan: flip `- [ ]` → `- [x] (commit-sha + brief evidence)` AS SOON AS work is shipped (committed +
pushed). NOT at end of session, NOT batched.

1. Ship code commit. **Push it.**
2. Edit plan: `- [x] [SCRIPT] P0. Description... (commit-sha + evidence)`.
3. Commit plan flip with `docs(plans):` prefix. **Push it.**
4. Then move to next todo.

**Don't flip a checkbox unless work is actually shipped (pushed).** Half-shipped → flip only the half that landed +
append `**DEFERRED**:` annotation.

Status closed set: `todo` / `done` / `design-shipped` / `helper-shipped` / `blocked` / `deferred-after-<successor>`.

Flip commits use `docs(plans):` (NOT `plan(...)` — rejected by conventional-commits hook). Format:

```
docs(plans): <plan-name> Phase <N>.<Tier> — <one-line summary>

* <repo>@<sha> — <one-line>
* <repo>@<sha> — <one-line>

Plan: <plan-filename>.
```

### Half 3 — Session-end deferred-work scoreboard

Multi-item session ending with non-final state → plan body MUST contain
`## Deferred work after <YYYY-MM-DD> <session-tag> session` table listing every touched item's status + successor +
blocker. Per-item `**DEFERRED**` annotations are necessary but NOT sufficient — future agent shouldn't have to scan
every checkbox in a 1000-line plan.

Scoreboard goes in plan body before `## Temporary states + their canonical follow-up plans`. Standard shape:
`| Phase / item | Status as of <date> | Successor / blocker |`.

Heuristic: if session updated 3+ phase statuses OR left 2+ items in non-final state, ship the scoreboard.

---

## Post-Plan-Phase Codex Audit (HARD RULE)

After every major phase completion, run codex audit pass: walk every codex doc the plan touches OR should have touched,
verify the doc reflects the new SSOT, update or write as part of same logical unit.

Three questions per phase:

1. **Did this phase change a contract / shape / pattern in codex?** Find the doc + update.
2. **Did this phase establish a NEW pattern not yet in codex?** Write a stub (entry-point + key principles +
   cross-references) — fold full content into a later plan phase.
3. **Did this phase invalidate an existing codex doc?** Update OR add
   `> **SUPERSEDED 2026-05-XX by <plan> Phase N — see <new-doc>**` banner.

Codex doc paths plan creates/enhances MUST be enumerated in plan's "Codex SSOT updates" phase. Plans omitting this are
review-blocking.

Anti-patterns: defer codex updates to plan-end; write codex docs without plan reference; update codex without flipping
the plan checkbox; "we'll write codex later" placeholder.

---

## CI Verification After Every Push (HARD RULE)

Every `git push` to a branch that triggers remote CI MUST be verified. CI bot reports to Telegram.

**Which pushes trigger CI**:

- Pushes to `main` → trigger QG + downstream. **Always verify.**
- PRs targeting `main` → trigger QG on PR head. **Verify on PR open + each new commit.**
- Pushes to `live-defi-rollout` and other `feat/*` → **DO NOT trigger remote CI.** Quality enforced locally via
  `bash scripts/quality-gates.sh` before push. Confirm push landed on origin
  (`git rev-list --left-right --count HEAD...origin/<branch>` returns `0 0`); stop.

**The discipline** when CI runs: push → set up background CI watcher (sub-agent OR `ScheduleWakeup` ~3-5min after push)
checking `gh run list --branch <branch> --repo <owner>/<repo> --limit 5`. Continue with other work; react
asynchronously.

**On CI fail**: diagnose via `gh run view <run-id> --log-failed --repo <owner>/<repo>` (NOT local). Fix root cause. Run
quality-gates locally only on YOUR specific files. Push again. CI watcher restarts.

**CI failures are NOT issues to flag** — fix in real time. Red CI on `live-defi-rollout` blocks workspace.

The CI bot reports underlying repo's status, not its own delivery result. `client_payload.status=FAILING` → ❌
`CRITICAL`; everything else → ✅ `INFO`. FAILING messages include failure excerpt inline (last 30 lines QG output,
ANSI-stripped, in `<pre>` block).

The pre-requisite: only commit YOUR work — see `Two teammates × multiple parallel agents`.

---

## Grep-Then-Read, Not Grep-Then-Conclude (HARD RULE codified 2026-05-10)

**A literal grep with 0 hits is NEVER sufficient to conclude a feature is missing.** Many features are runtime-resolved
where the literal name does NOT appear in source: regex-based dispatch, StrEnum value lookups, factory registries,
dynamic attribute access, plugin discovery, configuration-driven wiring.

The discipline:

1. Run literal grep first (fast filter).
2. If 0/few hits, escalate to READ — open candidate consumer files + factory / dispatcher / registry modules. Spend 2-5
   minutes reading.
3. Look for runtime-resolution patterns: regex dispatch (`re.compile()`), StrEnum value lookups
   (`EnumName.MEMBER.value`), factory/plugin registries (dict-keyed dispatchers), dynamic attribute access
   (`getattr(obj, name)`), configuration-driven wiring (yaml/json/.env), re-export chains.
4. Verify runtime path with grep on dispatch pattern itself.
5. When uncertain, ASK rather than CONCLUDE.
6. For >50KB plans, read past executive summary (use `wc -l` to gauge size).

Reference incident 2026-05-08 → 2026-05-10 9-agent audit: Cluster 9 reported 4 findings as missing based on literal grep
with 0 hits; 3 of 4 were already shipped via runtime-resolved patterns (~6-10 hours of avoidable cycles). Codified in QG
STEP 5.65 `unified-trading-pm/scripts/quality_gates/check_removed_symbols.py` (AST-walk attribute accesses, not literal
substring).

Anti-patterns: "grep returned 0 hits → feature missing" without reading; "spec says build X" without verifying X doesn't
already ship; reading only executive summary of >50KB plan; re-implementing already-shipped work.

---

## Findings Triage Discipline (HARD RULE)

When you find something broken / drifting outside your task:

| Where it sits                               | Action                                                                 |
| ------------------------------------------- | ---------------------------------------------------------------------- |
| In your code / file you own                 | **Fix yourself** in same commit                                        |
| Adjacent to your plan                       | Document + fix now in YOUR plan (same workstream)                      |
| Outside your plan, fits another active plan | **Annotate that plan body** with finding callout — DO NOT fix yourself |
| Outside every active plan                   | File `plans/active/issues/<short-name>_<YYYY_MM_DD>.md`                |
| **Big finding**                             | NOTIFY OPERATOR IMMEDIATELY in chat AND file an issue doc              |

"Big" = data correctness for ≥1 asset_group / May-23 critical path / cross-repo / contradicts workspace SSOT / would
change work-split / contradicts in-flight VM run.

Issue-doc format: frontmatter (`title` / `created` / `author` / `source[]` / `locked_by` / `locked_since`) + body
sections (`## What I found` / `## Why it matters` / `## Recommended decision`). Severity P0-P2; suggested owner if known
else "operator triage".

---

## Plans Run To Actual Completion, Not Smoke-Test Green (HARD RULE)

**Code-shipped is NOT operationally-shipped.** Every plan runs to actual completion on real infrastructure:

- **Backfills** run to natural shutdown with manifest-verified rows + sample-inspected parquets.
- **Migrations** transfer actual data with destination size/object-count parity.
- **Cloud migrations** kick off Storage Transfer Service / DataSync + verify ≤0.01% drift + sample read returns expected
  rows.
- **Smoke tests** run against real AWS S3 / real GCS via real ADC.
- **Refactors** propagate to every consumer in the same plan.
- **Reconcilers** run with `--apply-flips` against full manifest.

Single allowed exception: downstream plan EXPLICITLY takes over with full-run handoff (named by file path; downstream
must have a phase that consumes the smoke-tested artefact + runs to completion; both in `plans/active/` or
`plans/epics/`).

**Operator authority + ADC**: ADC admin perms on both GCP (`central-element-323112`) + AWS (`427895769566`). Provision
buckets, launch VMs, kick transfers, make SSOT triage calls. **Do NOT pause for operator approval on these.** Hard-stop
list (genuine human-only): wallet private keys + custody endpoint approvals, live-trading kill-switch arming, force-push
to main, version 1.0.0 graduation, destructive ops beyond local working tree.

Anti-patterns: "operator-actionable" close-outs (unless hard-stop); "sub-plan to be filed" (current plan ships full
scope OR explicitly hands off); "Phase N ready to run" with no actual run; smoke-only QG without real-infra
verification.

**Split Plan Format — Full-Execution Criterion**: every Tab in daily work-split MUST extend Done definition:

```markdown
**Full-execution criterion**:

- ✅ <full-run criterion 1 — exact data/state on real infra>.
  - **What ran**: <command + machine/VM-name + duration>.
  - **Verification**: <gcloud/aws CLI + expected output + actual observed>.

**Handoff exception(s)** (if any):

- <criterion N> deferred to <downstream-plan>:<phase-id>. Justification: <why downstream is right runner>.
```

Mirrored at `plans/PLAN_FORMAT.md` § 8.

---

## Estimate Calibration — Per-Class Multipliers (HARD RULE codified 2026-05-11)

Claude's training-intuition AI-day estimates run **1.5-3× conservative** for this workspace's parallel-agent + sub-agent
fan-out + per-tab-worktree pattern. Conservative estimates → operators undersell scope → real throughput exceeds plan →
unscheduled work piles up as technical debt. Apply the multiplier at plan-write time:

| Class       | Multiplier | Typical work                                                                           |
| ----------- | ---------- | -------------------------------------------------------------------------------------- |
| `refactor`  | 0.4×       | Mechanical changes across N files (rename, migrate to helper, lint sweep)              |
| `design`    | 0.6×       | New artefact (plan, codex doc, UAC schema, helper module)                              |
| `infra`     | 0.8×       | Real-infra ops (VM launch + verify, backfill, cloud migration with drift verification) |
| `brand-new` | 1.0×       | Novel feature with no template                                                         |
| `research`  | 1.2×       | Scope unknown upfront; investigation-heavy                                             |

**Don't apply** when work is serial-only by construction (wallet keys, kill-switch, force-push, version 1.0.0),
single-tab without sub-agent fan-out, external-dependency-bound (counterparty wait), or first touch on a brand-new
domain. **When in doubt, pick the higher class** — optimism is the failure mode this corrects.

**Frontmatter convention** (every active plan written after 2026-05-11):

```yaml
estimate_class: refactor | design | infra | brand-new | research
estimate_baseline_ai_days: <pre-calibration estimate>
estimate_calibrated_ai_days: <baseline × multiplier>
effective_concurrent_slots: 1 | 2-4 | 5-8 # OPTIONAL — see "parallelism axis" in SSOT
```

Multi-class plans use the dominant class for plan-level + override per-phase inline. Legacy plans retrofit on next
substantive update — **do NOT mass-sweep** (collision risk per Findings Triage).

**AI-day vs wall-clock**: `class_multiplier` measures **intra-slot** compression (sub-agent fan-out within one slot).
The workspace also runs **multi-slot parallelism** — up to 8 slots per operator (16 workspace-wide). For plans that
parallelise across slots, `wall_clock_days = phase_serial_floor + max_concurrent_phase / effective_concurrent_slots`,
bounded by the serial-dependency floor (phases with hard ordering cannot parallelise). DON'T double-discount: the class
multiplier already captures intra-slot fan-out; the slot divisor is on top, not instead. Plans that declare
`effective_concurrent_slots > 1` SHOULD annotate per-phase `(SERIAL — depends on...)` / `(PARALLEL with phases X/Y)` so
the floor is computable.

**Cross-plan slot contention**: a plan's `effective_concurrent_slots` is the _capacity_ number; the daily
`work_split_<YYYY_MM_DD>_ikenna.md` + `..._harsh.md` files are the operator's _realised_ slot allocation across ~50-100
active plans competing for capacity. Wall-clock estimates are necessary but not sufficient without checking the
work-split allocation for the cycle in question.

**Retrospective ledger** at `codex/08-workflows/estimation-retrospective-ledger.md` — every plan archive appends a row
(`Plan | Class | Calibrated | Actual | Ratio | Notes`). When 8+ rows land for a class with median ratio drifting ±20%
from 1.0, propose updated multiplier in `docs(codex):` PR.

Full SSOT: `codex/08-workflows/estimation-calibration.md` (anti-patterns, "when not to apply" detail, per-phase override
format, ledger governance).

---

## Citadel-Grade Planning Standards

Every plan MUST:

1. **Pre-Audit Before Execution** — workspace-wide grep for every removed/renamed symbol; build pre-audit manifest (repo
   / file / line / import / action). Embed in plan. Document what you CAN'T verify if subset.
2. **Phased Execution DAG** — explicit dependencies, QG gates between phases, items marked PARALLEL or SEQUENTIAL,
   ASCII/Mermaid graph in context.
3. **No Technical Debt** — no backwards compat shims, re-exports of old paths, deprecation wrappers. Clean breaks.
   Exception: single-repo work without downstream siblings → backwards compat allowed temporarily; document as follow-up
   todo. Full workspace = zero tech debt, update everything.
4. **Parallelization** — independent items marked PARALLEL.
5. **Success Criteria per phase** — code gates (QG / basedpyright / ruff) + test gates + deployment gates D1-D5 +
   business gates B1-B6. Final phase = workspace-wide QG validation.
6. **Downstream Consumer Updates (extended 2026-05-08)** — every removed/renamed PUBLIC symbol from any service or
   peripheral repo: pre-audit identifies EVERY downstream consumer workspace-wide (service-internal + peripheral
   scripts + sample notebooks). Workspace `grep` mandatory; AST-walk pattern from QG STEP 5.64 is canonical impl.
   Reference incident 2026-05-01 → 2026-05-08 silent rot of `e2e-testing/scripts/defi/colocated_engine.py` (broken
   import of `get_strategy_factories`).
7. **Single Source of Truth** — types in UAC (external) or `unified_api_contracts.internal` (internal). No self-declared
   duplicates.

---

## Runbook Execution-Owner SSOT (HARD RULE)

Every operator-runnable runbook / smoke harness / manifest-rescan / alerting drill MUST declare execution path:

```yaml
execution:
  owner: <named Tab in current work-split | service maintainer | cron schedule>
  cadence: <daily | weekly | monthly | per-PR | per-deploy | one-shot>
  verifier: <event-stream signature | exit code | manifest spot-check | downstream side-effect>
  last_executed: <YYYY-MM-DD or "NEVER">
```

**No exceptions** — runbooks without all 4 fields review-blocking. Closed set of execution paths:

1. **Cron VM** in `deployment-service/scripts/vm/` with singleton-locked launcher + watchdog dict registration.
2. **Daily Tab assignment** in tomorrow's `work_split_<YYYY_MM_DD>_*.md`.
3. **QG-wired smoke** — runbook's smoke runs as part of `bash scripts/quality-gates.sh` for consumer service.
4. **Cron-triggered ScheduleWakeup**.

Reference: `plans/active/issues/runbook_execution_governance_gaps_2026_05_08.md`.

---

## Peripheral Script Directories Under Primary-Consumer QG (HARD RULE)

Every peripheral script directory that imports from a service's Python package MUST be wired into THAT service's
`scripts/quality-gates.sh` so basedpyright + ruff + import-resolution catch breakage at PR time, not runtime.

| Peripheral dir                       | Primary consumer service       | QG path                                                              |
| ------------------------------------ | ------------------------------ | -------------------------------------------------------------------- |
| `e2e-testing/scripts/defi/`          | strategy-service               | `strategy-service/scripts/quality-gates.sh` runs basedpyright on dir |
| `e2e-testing/scripts/sports/`        | features-sports-service / mtds | features-sports-service QG                                           |
| `e2e-testing/scripts/prediction/`    | mtds + features-onchain        | mtds QG                                                              |
| `*_service/scripts/migration_*.py`   | own service                    | own service QG                                                       |
| `deployment-service/scripts/vm/*.sh` | bash; no Python                | bash-syntax check in deployment-service QG                           |
| `unified-trading-pm/scripts/*.py`    | PM library + various           | PM QG                                                                |

Wired = `cd ../e2e-testing/scripts/<asset_group>/` then basedpyright + ruff. If peripheral repo isn't sibling at QG time
(CI), skip with clear message.

Reference: `colocated_engine.py:306` import of `get_strategy_factories` removed by V1-RETIRE Phase 2 (2026-05-01); 7
days silently broken until manual harness run on 2026-05-08.

---

## Master Plan Continuous-Verification Column (HARD RULE)

Every success criterion in master plan readiness checklist (Groups A-G; 23 items) MUST declare continuous-verification
path — what cron / Tab / QG runs between checkpoint deadlines to keep criterion green.

Required column shape: `| Group | Item | Cutover Criterion | **Continuous Verification** | Last verified |`

Manual sign-off items declare `Continuous Verification: manual` + `Last verified: <date or NEVER>`. Master plan refresh
PRs without `Last verified` updates are review-blocked.

---

## Per-Tab Worktrees — 3-tier parallel-agent isolation

3 tiers: **Operator** (separate machines) → **Slot** (per worktree, `.tabs/<N>/<repo>/` on `tab/<operator>/<N>`,
per-slot `PREK_CACHE_DIR` via auto `.envrc`) → **Sub-agent** (within one slot; shares slot's worktree).

**Bootstrap**:

```bash
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --init --slots 8
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --add-slot 9
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot 3
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --list
```

**Reconciliation**: `bash unified-trading-pm/scripts/dev/slot-master-rebase.sh` (fetch + rebase + classify conflicts per
shape: `append-section` / `checkbox-flip` / `paragraph-rewrite` / `code` / `unknown`).

Cross-slot races on `.git/index` are unrepresentable. Within-slot multi-sub-agent fan-out shares index — pre-commit
check still applies.

SSOTs: `codex/05-infrastructure/per-tab-worktrees.md` + `codex/05-infrastructure/plan-aware-merge-resolution.md` +
`plans/active/per_agent_worktrees_2026_05_10.md`.

---

## Daily Work-Split Process (Ikenna ↔ Harsh, AI-paralleled)

**Main orchestrator bootstrap**: if you are running as a main orchestrator agent, your first action is to read your
side's LEDGER bootstrap before anything else:

- **Ikenna's main** → `ikenna_orchestrator/LEDGER.md` § "Bootstrap — fresh main-agent chat" + `AGENT_ONBOARDING.md`.
- **Harsh's main** → `harsh_orchestrator/LEDGER.md` § "Bootstrap" + `AGENT_ONBOARDING.md`.

Per-side `<side>_orchestrator/` directory contains: `AGENT_ONBOARDING.md` + `LEDGER.md` + `pings/` (per-slot
`pings/slot_<N>.md`). Boot checklist runs `git status` + `git fetch` + ledger read in ~3-5 min, then ack "State: N tabs
in flight, M intra-side pings, K cross-side pings, J local commits queued. Today's plan = X. Standing by."

### Why this exists

Two operators × multiple parallel agents = **~65-75 AI-days/day per side measured (2026-05-11) ramping to ~120-150
AI-days/day per side observed (2026-05-12 density-push Day-1)**, **~180+/side theoretical ceiling** at full 7-slot
fan-out × 5× sub-agent compression (G-9 update 2026-05-12: 5 of 7 Ikenna slots ✅ FULL-CYCLE-CLOSE on Day-1 of a 4-day
cycle = ~5× calibrated pace). Without daily split, agents converge on critical-path files (UAC, master plans,
deployment-api) and step on each other. Daily split is operator's load-balancer.

### Cadence + split principle

Daily morning. Drafts `plans/active/work_split_<YYYY_MM_DD>_ikenna.md` + `..._harsh.md`. **Sized ~250-400 cal AI-days
per side per 4-day cycle** (≈ 65-100 cal AI-days/side/day, anchored to 2026-05-12 Day-1 measured pace where 5 of 7
Ikenna slots closed entire 4-day cycle scope in 1 calendar day = ~5× prior calibration). **Bake in SCOPE EXTENSION
layers per continuation_prompts pattern** — if a slot closes early, pull reserve list / Cycle 2 PREP / P1 bugs /
cross-side absorption WITHIN the cycle deadline. **The cycle calendar is FIXED (external freeze gate);
scope-within-cycle EXPANDS.** End-of-day archived.

**Ikenna**: cross-cutting design (3+ repos), trading-judgment / risk calls, governance / ratchet thinking, large
migrations / refactors changing on-disk shape, human-approval surface, master plan / umbrella coordination.

**Harsh**: implement-from-spec, run-script-and-verify, single-repo edits with crisp boundaries, test execution +
Playwright matrices, mechanical refactors, audits / probes (read-only).

Tie-breaker: >1 repo + design not pre-spec'd → Ikenna; closed-set design call required → Ikenna; running script and
watching events → Harsh.

### Two valid working models per side

**Model A** — fixed thematic 5-tab clustering. Each Tab pre-defined coherent context cluster. Used when work clusters
into 5 thematic groups.

**Model B** — 1-main + dynamic spawned tabs. Main does direction + Q&A dispatch + plan curation + ping triage; no
implementation. Spawned tabs scoped implementers; tab count varies. Used for dynamic work / incoming pings.

### Universal mechanics

- **Per-slot worktrees** (see Per-Tab Worktrees section above).
- **Conditional push** — `git fetch` + check incoming → 0 → push freely; any incoming → STOP, document in plan-of-record
  `## Open questions` (🟡 BLOCKED), append ping in `_agent_pings.md`, continue with what you CAN.
- **Plan-of-record + Q&A bus** — every spawned tab has single plan-of-record. Q&A in `## Open questions` with badges 🟡
  BLOCKED / ✅ RESOLVED. Resolved cleaned at daily ledger sweep.
- **Ping ledger bifurcation** (codified 2026-05-08): TWO ledgers:
  - **Workspace-shared `plans/active/_agent_pings.md`** — cross-side comms only (Ikenna ↔ Harsh hard-gate signalling).
  - **Per-side `<side>_orchestrator/pings/slot_<N>.md`** — intra-side comms (main ↔ spawned tabs). Per-slot files (zero
    collision). Bidirectional — main may append `[main → slot N]` messages.
- **Polling cadence** (Model B main): ~1 min while operator active; 5 min when tabs quiet.
- **Sub-agent fan-out**: send all `Task` calls in SINGLE message. Sub-agents inherit nothing — paste
  `SUB_AGENT_MANDATORY_RULES.md` at top of every Task prompt.

### Daily plan shape + reset

Frontmatter: `title` / `type: coordination-doc` / `status: active` / `created` / `deadline` / `horizon` / `companion_to`
(the other side's split) / `locked_by: live-defi-rollout`.

Body: Why this split today / Working model (A or B) / Today's status → Tab registry / Cross-tab handshakes / Cross-side
handshakes / Collision-risk callouts / Spawn prompts (Model B) / Daily sync points / Defer post-deadline.

Daily reset: `git fetch` + summarise; re-read yesterday's splits + `_agent_pings.md`; sweep ✅ RESOLVED >24h Q&As; draft
today's two splits; slot-reset for theme changes (`setup-tab-worktrees.sh --reset-slot <N>`); mirror slot↔theme into
`<operator>_orchestrator/LEDGER.md`; report to operator.

Anti-patterns: Q&A in work-split plan (use plan-of-record); spawn prompts in chat (belong in plan body); 5-tab Model A
when work is dynamic (switch to B); thin plans <10 AI-days; archive mid-cycle.

Composes with: Commit/Push/Flip; Cross-Plan Banners; Capture Discoveries; Findings Triage; Sub-Agents; Citadel-Grade;
Two teammates × multiple parallel agents.

---

## Cross-Plan Coordination Banners (codified 2026-05-07)

When launching ANY VM or starting an in-flight refactor (manifest schema / file structure / UAC contract / parquet
columns / hive-vocab / path templates / error-reason taxonomy), add a top-of-file `> **🟢 VM RUNNING — ...**` or
`> **🟡 IN-FLIGHT REFACTOR — ...**` banner to every other active plan whose work is influenced. Reader contract: scan
top-of-file banners before touching the affected surface. Banner-add is part of the launch/refactor-start logical unit;
banner-remove owned by launcher when VM auto-shutdowns or refactor lands.

---

## Sub-Agents & Autonomous Agents: Full Rules Required (MANDATORY)

Sub-agents start FRESH and do NOT inherit your rules. **Agents in `--print` mode CANNOT read files from disk** — rules
MUST be pasted into the prompt text.

`SUB_AGENT_MANDATORY_RULES.md` is a **lean 10KB file** (separate from this CLAUDE.md as of 2026-05-11) — paste at top of
every Task spawn. Per-repo `.claude/SUB_AGENT_MANDATORY_RULES.md` symlinks resolve to PM canonical.

When launching ANY sub-agent / autonomous agent:

1. **Local scripts**:
   `RULES=$(bash unified-trading-pm/scripts/agents/inject-mandatory-rules.sh "$WORKSPACE_ROOT" "$REPO")`.
2. **GHA workflows**: load via `GITHUB_ENV` heredoc; prepend `${MANDATORY_RULES}` to prompt.
3. **Cursor/Claude Code Task tool**: paste contents of `SUB_AGENT_MANDATORY_RULES.md` at TOP of prompt.
4. **If paste impractical**: include at TOP "Before any action, read SUB_AGENT_MANDATORY_RULES.md and follow ALL rules
   strictly."
5. **Always include** WORKSPACE_ROOT path. Tests: `cd <repo> && bash scripts/quality-gates.sh`.
6. **If rules injection fails, agent MUST NOT proceed.** Exit with error.

SSOTs: `unified-trading-pm/scripts/agents/inject-mandatory-rules.sh` (injection wrapper) +
`cursor-configs/SUB_AGENT_MANDATORY_RULES.md` (lean rules content).

---

## Analysis Rules

When analyzing codebase architecture:

- EXCLUDE: `.venv*`, `venv/`, `node_modules/`, `build/`, `dist/`, `*.egg-info/`
- EXCLUDE: docs (`*.md`) when counting code usage; shell scripts when analyzing Python patterns
- FOCUS: Python source in service directories
- Use: `--glob '!.venv*' --glob '!**/.venv*/**'` with ripgrep

```bash
rg "pattern" --type py --glob '!.venv*' --glob '!build' --glob '!tests'
grep -r "pattern" --include="*.py" --exclude-dir=".venv*" --exclude-dir="tests"
```

---

## Workspace Configs (Canonical in PM)

- **Canonical**: `unified-trading-pm/cursor-configs/`
- **Symlink**: `.cursor/workspace-configs` → `unified-trading-pm/cursor-configs`
- **Setup**: `bash unified-trading-pm/scripts/workspace/setup-workspace-config-symlink.sh`

**Workspaces**: `unified-trading-system-repos.code-workspace` (curated multi-repo) + `workspace-libraries` /
`workspace-uis` / `workspace-trading` / `workspace-data-pipeline` / `workspace-ml` / `workspace-features` /
`workspace-infrastructure` / `workspace-complete` / `workspace-full-pipeline`.

All paths use `${workspaceFolder}` — portable. Strict basedpyright (`reportAny` / `reportUnknownMemberType` /
`reportUnknownVariableType` = error).

---

## UAC Citadel Architecture

Facade pattern with per-source co-location.

**Current layout**: `canonical/domain/` (sub-packages) · `canonical/crosscutting/` · `external/{source}/` (flat, 80+
dirs) · `normalize_utils/` (internal) · `registry/` · root facades (`market.py`, `execution.py`, etc.).

**Deleted dirs** (do NOT reference): `canonical/normalize/` · `external/sports/` · `external/cloud_sdks/` ·
`external/onchain/` · `external/macro/` · `schemas/` · `shared/`.

**Import rules**: services use `from unified_api_contracts import X` or `from unified_api_contracts.{domain} import X`.
Deep paths (`canonical.*`, `normalize_utils.*`) are UAC-internal only. SSOT:
`codex/02-data/contracts-scope-and-layout.md`.
