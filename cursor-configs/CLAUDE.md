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

## Master Plan — Live DeFi Trading by 2026-05-23

**The current orchestration target.** Two DeFi archetypes (`carry_staked_basis` lead + `leveraged_funding_arb`) live on
a real wallet ≥7 continuous days by 2026-05-23, with hedge legs across 6 perp venues (Bybit, Deribit, Binance, OKX,
Hyperliquid, Aster) and full AWS↔GCP cloud parity.

- **Working plan (current state, todos, Q&A, risk register):**
  `unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.plan.md`
- **Codex SSOT companion (durable readiness model + doc-touchpoint map):**
  `unified-trading-pm/codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md`

**Principle.** _Docs are the intent._ Codex SSOTs are ahead of the code and in line with the plans. Order of operations:
**doc → plan → code**. Drift between any pair (doc/plan/code) is a review-blocking failure. Before any change in scope
of the doc-touchpoint map (manifest schema, batch=live, cloud-agnostic, custody, live observability, P&L attribution,
operational modes, ML lifecycle, hot reload, service-infra requirements, asset-group vocabulary, lookahead bias), read
the listed SSOTs first; commit must touch **all** of them or the PR explicitly states why a given SSOT is unaffected.

**Per-service readiness checklist** (7 groups / 23 items): A · Code health (1-3) · B · Data correctness (4-8) · C ·
Runtime parity (9-11) · D · Coverage & shard (12-14) · E · Operability (15-16) · F · Trading prerequisites — live-only
(17-22) · G · Operator UX — live-only (23). Live-only groups F + G cover backtest fidelity (real gas / matching engine /
cost+yield precision), 2-year batch backtest run, Copper + CEFFU treasury, live testnet replicating prod, batch-vs-live
reconciliation + P&L attribution, circuit breakers + kill switches + alerting + auto-recovery, and the DART manual-trade
gate.

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
- **DO NOT quickmerge when dep repos are dirty — commit + push to `live-defi-rollout` directly instead (2026-05-06 rule
  update).** If an upstream workspace dep repo (UAC / UTL / UCI / UEI / MTDS / URDI, etc.) has uncommitted local changes
  from another agent, quickmerging a downstream consumer is misleading: the consumer's path-dep resolution +
  `uv pip install -e ../<dep>` locally will pull the dirty tree, but the pushed branch will link to origin/<dep> which
  lacks those edits → CI green locally, red remotely, and the PR is a lie. Same applies to repeatedly quickmerging the
  SAME repo while other agents are mid-edit on it (you'll absorb their untracked files into your stash). **Right
  behaviour when deps are dirty**: run `bash scripts/quality-gates.sh` (Pass 1 — full), then
  `git add <my-files> && git commit -m "..." && git push origin live-defi-rollout` directly on the affected repo. Skip
  the quickmerge → main promotion. VMs pull from `live-defi-rollout`, not `main`, so rapid iteration doesn't need the
  main promotion. Quickmerge-to-main is for landing finished features, not every commit. **QG failure attribution**: if
  QG fails on code YOU wrote, fix it + re-run + then commit + push; if QG fails on code another agent wrote (verify via
  `git blame` / `git log`), continue staging + committing + pushing your work anyway — they fix their breakage on their
  own commits. **Do NOT ask the user for approval** to switch from quickmerge to commit+push when deps are dirty — this
  is the Citadel-grade institutional default per user direction 2026-05-06: _"do things to the Citadel institutional
  grade, the proper solution, no shortcuts, no hacks. Where you're convicted, just do it the proper way rather than
  stopping every two seconds to ask me."_ Legitimate exceptions where quickmerge is still fine: user explicitly says
  "just quickmerge / commit everything as-is", or the dirty files are purely advisory (generated SVGs / DAGs that always
  regen on QG).
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
  `codex/14-playbooks/shared-core/signal-broadcast-architecture.md`; architecture plan (archived 2026-05-06, 8 phases
  shipped): `plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md`.
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
- **Honest absence vs fake placeholders (CRITICAL — applies top-to-bottom across every service)** — when a service runs
  end-to-end, every output row must reflect REAL work OR a clearly-flagged honest gap. Three categories of "missing",
  each with a different action — wrong action = silent data corruption.
  1. **Expected upstream-source gap** — the original data source genuinely doesn't provide data for that key (venue
     didn't exist on date, instrument delisted, source's coverage start is later than target, sport league paused,
     pre-genesis days). Action: emit empty parquet (or omit row) and `record_empty(row_key=..., attempted_at=...)` in
     the manifest. NaN downstream is fine — tree-based ML and rank-based allocators handle 1–10% missing data natively.
     The crime isn't NaN; the crime is masking absence.
  2. **Unexpected upstream-pipeline gap** — the upstream SERVICE was supposed to capture/process for that key (raw
     bucket `capture_status=captured` per manifest, or audit shows it should exist) but the row is missing. Action:
     STOP. Do not proceed downstream. `DependencyError(fail_fast=True)` is the correct guard at the boundary — resolve
     by running the upstream backfill for the missing window, NOT by `--skip-dependency-check`. The instruments-service
     → MTDS → MDPS → features-\* → strategy chain only works if each layer hard-fails when its upstream isn't current.
  3. **Reader / schema-drift bug** — data IS in the upstream bucket but the service's reader can't find it (wrong path
     template, stale filename pattern, evolved schema, dropped grouping column). Action: RAISE LOUD, fix the bug. NEVER
     silently produce empty placeholder rows that LOOK populated. Reference incident **2026-05-05**: MDPS reader
     expected legacy `ticks.parquet` while MTDS had evolved to per-instrument `{instrument_id}.parquet` files; MDPS
     silently emitted 1440 empty `open=high=low=close=None` placeholder bars per day per (venue, data_type) for years
     before being caught by hand-inspecting a sample parquet. Manifest checks said `captured` because the parquet
     existed; the parquet was 1440 rows of garbage.

  **Principle**: NaN/empty + `empty_confirmed` for honest gaps is fine. Empty placeholders that look populated are worse
  than missing data because they evade detection — manifest sees `captured`, downstream features compute garbage on
  garbage, models/strategies trained on empty bars produce confidently-wrong signals. When in doubt, fail loud.
  Validation-by-output-inspection (read a sample parquet, assert OHLC populated, assert at least one instrument-shard
  exists per (venue, data_type)) is required at every backfill boundary, not just QG. Counting rows is not validation;
  populating rows is. **Downstream-consumption SSOT** (NaN-handling tolerances, anti-pattern catalogue, pre-flight gates
  per consumer): `unified-trading-pm/codex/02-data/honest-absence-downstream-handling.md`.

- **No fire-and-forget VM launches (CRITICAL — production observability)** — every VM launch MUST be paired with active
  verification that the VM is emitting structured events. Events stream to
  `gs://{pid}-events/events/{service}/{YYYY-MM-DD}/{correlation_id}/hour={H}/*.jsonl` (JSONL, schema:
  `{event, service, timestamp, metadata: {service_name, severity, details: {correlation_id, ...}}}`). Required events at
  minimum: `STARTED` within 60s of launch, at least one progress event per hour while running, and `STOPPED` or `FAILED`
  at exit. Verification protocol after every launch: (1) wait 90s,
  `gcloud storage ls gs://{pid}-events/events/{service}/{today}/{vm-name}/` — directory exists with `hour=*` partition;
  (2) read first JSONL, assert `event=="STARTED"`; (3) every 10–15min recheck for new events — stalled progression ==
  silently-broken, kill and diagnose via the last event's `metadata.details`; (4) on auto-shutdown verify
  `event in ("STOPPED","FAILED")` with non-empty metadata. `STATUS=RUNNING` from gcloud only means VM is alive — NOT
  that workload is making progress. SSH-tailing logs is a dev crutch; production runs through `unified-events-interface`
  UI. When this Claude session launches VMs, the launch-and-monitor pair is ONE todo: launching without scheduling
  event-verification is fire-and- forget. Reference incident **2026-05-05**: 21 MDPS VMs launched, 6 cefi shards emitted
  STARTED + STOPPED cleanly but output was 1440 empty placeholder bars per day — events told the truth, but absence of
  intermediate progress events with row counts (e.g. `INSTRUMENT_PROCESSED`) should have been the silent-success signal.
  Adapters MUST emit per-instrument progress events with row counts so silent-success-with-zero-output is detectable
  from the event stream alone.

- **Shard-granularity SSOT (CRITICAL — applies top-to-bottom across every service)** — The shard atom MUST be identical
  across (a) writer atomicity boundary (parquet finalize + `record_captured`), (b) manifest row key (v5 columns:
  `asset_group, venue, chain, data_type, instrument_type, instrument_id, league_id, timeframe, feature_group, model_family, ...`),
  (c) data-status display rollup, (d) downstream service pre-flight gate, (e) deployment-UI drill-down + parquet
  download
  - schema view. Drift between any two = silent correctness bug. TradFi MVP partial-bundle (ES.OPT 18 dates with
    single-parent fills passed manifest as `captured`), MDPS empty-placeholder (1440 NaN OHLC bars/day for years passed
    as `captured`), and Databento per-schema drop (bundled `ohlcv_1m;trades` lost ohlcv on 429 marked complete) are all
    instances of this class.

  **Per-asset-group shard-key matrix:**
  - **CeFi spot/perp**: (asset_group, venue, data_type, instrument_type, instrument_id, day) — per-instrument (35GB
    roots, source atom is per-instrument-per-day).
  - **CeFi options/futures**: (asset_group, venue, data_type, `options_chain`/`futures_chain`, root, day) — bundled by
    root.
  - **TradFi futures**: (asset_group=tradfi, venue, data_type, instrument_type, root, day) — bundled, non-trading days
    pre-skipped via `venue_trading_calendar` + recorded as `empty_confirmed`.
  - **TradFi ETFs**: (asset_group=tradfi, venue, data_type, instrument_type, instrument_id, day) — per-instrument.
  - **TradFi options**: (asset_group=tradfi, venue, data_type, `options_chain`, root, day) — bundled, 11-cluster ES.OPT
    taxonomy (ES + E1A–E5A weeklies + EW1–EW4 + EOM).
  - **DeFi**: (asset_group=defi, **chain**, venue/protocol, data_type, instrument_id_or_protocol_id, day) — `chain` is a
    first-class v5 axis; pre-genesis dates per chain are `empty_confirmed`.
  - **Sports**: (asset_group=sports, source, data_type, league_id, fixture_id or day-aggregate, day) — paused-league
    windows (`KNOWN_COVERAGE_GAPS`) and pre-`SOURCE_COVERAGE_START` dates are `empty_confirmed`.
  - **Prediction**: (asset_group=prediction, venue, data_type, **canonical_question_group**, day) — raw market_ids
    bundled into canonical names (BTC up/down, S&P up/down) like options-chain bundling. UAC SSOT for the market_id →
    canonical_question_group mapping is required (greenfield item if not yet present).

  **Layer discipline (tag every change before implementing):**
  - **[UAC]** — contracts, shard-key shapes, `feature_group → required_inputs` DAG SSOT, `SOURCE_COVERAGE_START` /
    `DATA_TYPE_COVERAGE_START` / `KNOWN_COVERAGE_GAPS`, `available_at` semantics per source, prediction
    canonical-question grouping, `venue_trading_calendar`.
  - **[UTL]** — cross-service runtime utilities: `ManifestWriter`, dual-vocab probe utility (the 5 phantom-audit drift
    axes lifted from `reconcile_phantom_manifest_rows_all.py` into one shared module), write-gate helper (row count +
    NaN ratio + schema + cluster coverage), `LookaheadBiasError`, schema-introspection helper, `run_lifecycle`.
  - **[per-service]** — only what genuinely differs: source-specific `available_at` stamping, calculator/adapter
    business logic.
  - **[deployment-api / deployment-ui]** — per-service download endpoint + schema-view route, data-status drill-down to
    leaf parquet.
  - **Do not duplicate cross-service utilities per-service.** If you find one inlined (e.g. NaN-ratio check copy-pasted
    across calculators), lift to UTL.

  **`available_at` is a write-time column, never derived at read-time** (read-time inference can't tell "available now"
  from "available when the fixture happened"; sports temporal-availability stamping rules):
  - Lineups: `kickoff - 60min` (conservative — clip earlier leaks).
  - Injuries: event-time of the injury report (so feature for fixture F sees only injuries from prior fixtures).
  - Pre-match odds: publication time per snapshot (opening days before, closing at kickoff).
  - Post-match (understat xG, fixture_stats, results, sfi_progressive): `match_end_time` — NEVER available pre-kickoff.
  - Weather forecasts: forecast-**issue** time (distinct from forecast-target time).
  - If `available_at` is missing on disk for a source, stamp it at backfill-replay time before downstream consumes.

  **`LookaheadBiasError` raised loud at every features-\* + MDPS compute, not warn-mode**: every input row consumed must
  satisfy `input.available_at <= target_ts - horizon`. Strict-mode raise, not log-and-continue. Currently fires for
  lst_yields; extend to every features-\* calculator. The UAC `feature_group → required_inputs` DAG drives the check.

  **Validation gates per `record_captured` — 4 pillars** (any failure → `record_failed` with typed `error_reason`, never
  `record_captured` with garbage rows):
  1. **Row count > 0** unless source response was legitimately empty (then `record_empty`, not `record_captured`).
  2. **NaN ratio per column < threshold** (per-feature-group threshold in UAC; the carry-tracer `write_gate_rejected`
     pattern, currently inlined per-calculator — must be lifted to a UTL helper).
  3. **Schema matches contract** (columns + types match UAC schema declaration).
  4. **Cluster coverage ≥ expected** for bundled shards. Implementation:
     `ManifestWriter.record_captured(expected_root_clusters: dict[str, int], cluster_extractor: Callable[[str], str])`;
     under-coverage triggers `record_failed(ClusterCoverageError(missing=..., observed=...))` instead of writing the
     parquet. Generalises to `options_chain` (ES.OPT 11-cluster), `futures_chain`, prediction canonical-question
     bundles, sports fixture bundles.

  Without all four, manifest is presence-only and partial bundles / empty placeholders pass silently. Reference
  incidents: TradFi MVP **2026-05-06** (ES.OPT 18 single-parent fills, since refilled) and MDPS **2026-05-05** (1440
  empty placeholder bars/day persisted for years before hand-inspection caught them).

  **Manifest migration, NOT fallback**: when any manifest drifts from v5 canonical shape (pre-v5 row schema,
  off-canonical paths, wrong row keys), write a one-time migration script (precedent
  `instruments-service/scripts/migrate_local_sfi_to_canonical.py`) and **remove** the fallback reader. The one
  documented exception that survives: hive-vocab `category=` vs `asset_group=` on-disk legacy preservation per the
  Asset-group vocabulary section above (reader tries canonical first, falls back to legacy; do NOT rekey on-disk data).
  Everything else: migrate, then delete the fallback path. Aligns with workspace "no try/except fallback imports" + "no
  compat shims" rules.

  **Companion plan + executor handover**: full per-service verify/fix/lift/build checklist with anti-patterns and
  parallel-stream coordination notes in `unified-trading-pm/plans/active/infrastructure_master_2026_05_07.plan.md`
  (umbrella) which folds-in `plans/archive/shard_granularity_ssot_propagation_2026_05_06.plan.md` + its `.HANDOVER.md`
  companion (commit `d591416d`). Sub-agents executing this work pick the rules up via this section + the umbrella + the
  archived handover doc + SUB_AGENT_MANDATORY_RULES.md inheritance.

- **Live = batch — same data, same fields, same timing semantics, different sources OK (CRITICAL — applies to every
  asset_group)** — Live and batch are operational modes of the SAME pipeline. They produce identical schemas, identical
  `data_types`, identical fields. The ONLY thing that legitimately differs is which SOURCE serves a given
  `(asset_group, data_type)`, because some sources lag others on real-time emission. Historical writes MUST be
  timestamped with the `available_at` we'd actually have in live mode (the
  `unified_api_contracts.canonical.crosscutting.source_priority.SOURCE_PRIORITY` top entry's emission time, NOT the
  canonical historical source's slower archive time). Banned anti-patterns: separate live-only data_types like
  `LINEUPS_PRE_MATCH` vs `LINEUPS_POST_MATCH`; distinct field sets between live + batch parquets; deriving
  `available_at` at read-time from the live-batch mode flag. Reference: 2026-05-06 user direction during
  writegate-honest-coverage planning. Plan: `writegate_honest_coverage_endtoend_2026_05_06.plan.md`.

- **No double SSOT in data-saving methodology (CRITICAL — applies top-to-bottom)** — Where two paths produce the same
  outcome, one is deleted. Banned coexistence: `_create_empty_output()` AND `_handle_empty_tick_data()` (writegate plan
  Phase 2.A deletes the placeholder method); `_ensure_timestamp` shim AND per-source `stamp_available_at_*` helpers
  (writegate Phase 2.C deletes the shim); parallel v3-shape `_write_manifest_records` AND v6 canonical writer (writegate
  Phase 2.A deletes the v3 path); inline NaN-ratio gate AND UTL `write_gate_helper` (Plan B Q #4 lifts the inline);
  per-service phantom-audit drift probe AND UTL `manifest_audit` module (Plan B Q #5 lifts the script). When you find
  yourself maintaining two ways to do the same thing, kill one — don't add a third helper to "reconcile" them.

- **Three-category empty-output decision (every per-shard adapter — MDPS / MTDS / features-\* / instruments-service)** —
  Every condition that could produce an empty result resolves to ONE of: **A. Source returned 0 ticks for the requested
  window** → `record_empty(row_key, attempted_at)` (honest absence); **B. Source returned ticks; ALL fall outside the
  requested day after `interval_idx` filter** →
  `record_failed(UpstreamTimestampBiasError(observed_dates, expected_day, n_ticks))` (UPSTREAM BUG — partition
  mislabeled at MTDS write-time, source replay covered wrong window, OR clock-skew; paired upstream fix at MTDS
  `raw_tick_hive.py` partitioner-validation); **C. Rows in window but downstream calc dropped all rows due to
  NaN/malformed source fields** → `record_failed(MalformedTickFieldError(field, n_dropped, sample_values))`
  (data-quality bug worth diagnosing). NO silent NaN placeholder rows. The `_create_empty_output()`-style placeholder
  method is **banned** from `base_adapter` and any equivalent base class. Reference incident: 2026-05-05 MDPS 1440 NaN
  OHLC bars per day per (venue, data_type) for years passed manifest as `captured`. Plan:
  `writegate_honest_coverage_endtoend_2026_05_06.plan.md` Phase 2.A deletes `_create_empty_output` workspace-wide.

  **Reason taxonomy (codified 2026-05-07 — operator direction).** The 3-category model above is the WRITE-side
  discipline. The EXPRESSION of the categories in the manifest uses a structured `error_reason` taxonomy (closed set
  under UAC `EMPTY_CONFIRMED_REASONS`): `EXPECTED_HOLIDAY` / `EXPECTED_WEEKEND` / `EXPECTED_PAUSED_LEAGUE` /
  `EXPECTED_PRE_SOURCE_COVERAGE_START` / `EXPECTED_PRE_GENESIS_CHAIN` / `EXPECTED_INSTRUMENT_NOT_LISTED` /
  `EXPECTED_INSTRUMENT_DELISTED` / `EXPECTED_PARTIAL_HALF_DAY` / `SOURCE_RETURNED_ZERO`. Every `(shard_key, day)` in the
  expected universe gets a manifest row — calendar-pre-skip cases emit `record_expected_empty(reason=EXPECTED_<X>)`
  instead of "no row at all." **NO parquet on disk for bad/partial- expected days** — manifest reason IS the SSOT;
  downstream consumers read the manifest, not the parquet, to determine absence semantics. Per-service consumer-class
  audit (execution skips / ML NaN-fills / rolling-window features adjust denominator while keeping window size /
  same-day features NaN-fill / cross-instrument calcs propagate per-leg) is the workspace contract — see
  [`codex/02-data/honest-absence-downstream-handling.md`](unified-trading-pm/codex/02-data/honest-absence-downstream-handling.md)
  § "Reason taxonomy (codified 2026-05-07)" + § "Per-service consumer-class audit." Plan: writegate Phase 2.E ships UTL
  contract extension + per-service writer migration + per-service consumer-class audit.

- **Cluster validation MANDATORY at `record_captured` for bundled shards (CRITICAL — runtime + static enforcement)** —
  For any `data_type ∈ unified_api_contracts.canonical.crosscutting.honest_coverage.BUNDLED_DATA_TYPES`,
  `ManifestWriter.record_captured` REQUIRES `expected_root_clusters` + `cluster_extractor` kwargs. UTL guard raises
  `MissingClusterValidationError` if absent. **QG STEP 5.64 statically walks every `record_captured(` callsite + asserts
  the kwargs are passed when the literal data_type is bundled** — fails CI if missing. Bundled types include
  `options_chain` (ES.OPT 11-cluster taxonomy), `futures_chain` (per-root spreads / butterflies),
  `prediction_canonical_question_group` (per-canonical-group market_id sets), and the sports per-fixture-bundle
  data_types `ODDS_SNAPSHOT` / `ODDS_MOVEMENT` / `ARBITRAGE` (per-league-tier expected bookmaker sets). Adding a new
  bundled data_type means adding it to UAC `BUNDLED_DATA_TYPES` AND seeding its registry — no half-measures, no
  helper-call-pattern. The standalone `check_cluster_coverage` helper is private to UTL after the contract change;
  callers that try to use it directly outside `record_captured` get a deprecation error. Plan:
  `writegate_honest_coverage_endtoend_2026_05_06.plan.md` Phase 1A.

- **`available_at` is per-row, write-time, equal to live-pipeline-arrival (workspace-wide)** — Every shard's parquet
  contains an `available_at` column. Each row's value = when the live pipeline would have actually had that row's
  information per `unified_api_contracts.canonical.crosscutting.availability_semantics.AVAILABILITY_AT_SEMANTICS`. NEVER
  derived at read-time. Stamping helpers: `unified_trading_library.availability_stamping.stamp_available_at_*`. UTL's
  `record_captured` calls `assert_available_at_present` internally — missing or null `available_at` →
  `LookaheadBiasError`. Per-source rules (from CLAUDE.md historical-source-vs-live-pipeline section): Sports lineups →
  `kickoff − 60min`; fixture_events → per-row `event_time`; injuries → per-row `report_time` / `occurrence_time`;
  fixture_stats / fixture_player_stats → `match_end_time` (detected via cascade: api_football native → SFI progressive
  freeze → footystats / understat → low-confidence `kickoff + 120min` fallback); fixtures → `announced_at`; reference
  tables → `fetch_completed_at`; weather → forecast-issue-time. CeFi / DeFi / TradFi tick-level data → tick timestamp +
  source-priority scrape latency.

- **Prediction market lifecycle timing (instruments-service + MTDS — CRITICAL for prediction shard correctness)** —
  Prediction markets (Polymarket / Kalshi / others) are NOT static instruments; each market has a lifecycle:
  `market_created_at` (when listed), `resolution_time` (outcome determined), `settlement_time` (payouts). Recurring
  canonical groups (`BTC_UP_DOWN_HOURLY`, `BTC_UP_DOWN_DAILY`, `SPX_UP_DOWN_DAILY`, `ELECTION_PRESIDENT_2028`, etc.)
  cycle through multiple market_ids over time — HOURLY = 24/day, DAILY = 1/day, ELECTION = 1 over months/years.
  Instrument definitions in instruments-service MUST capture all three lifecycle timestamps per market_id PLUS the
  canonical_question_group membership. MTDS CLOB capture must respect lifecycle bounds: NO ticks before
  `market_created_at`, NO new ticks after `settlement_time` (the market is closed; post-settlement data is not
  informative for prediction). Cluster validation per `(canonical_question_group, day)` checks that all expected
  market_ids with active windows in that day are represented (HOURLY → 24 clusters expected, DAILY → 1, etc.).
  LookaheadBiasError respects per-market lifecycle: a feature compute at time T can only consume ticks where
  `tick.timestamp <= T` AND `tick.market_id`'s `market_created_at <= T`. Plan: `predictions_master_2026_05_07.plan.md`
  (asset_group umbrella; folds-in
  `plans/archive/predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`).

- **Temporary state must have a named successor plan (no silent "fix later")** — When a plan ships a partial
  implementation that is not the final shape (e.g. UAC `PREDICTION_GROUPS = {}` empty registry until
  canonical_question_group SSOT lands; SOURCE_PRIORITY top-entry-only until multi-source merge plan lands; per-service
  DAG until UAC DAG SSOT lands), the partial state MUST be documented in a
  `## Temporary states + their canonical follow-up plans` section of that plan, with the named successor plan filename
  listed. NO temporary state is silently accepted as final. NO "we'll fix it later" without a named doc. Reviewers
  reject any partial implementation lacking a successor reference. Reference: writegate-honest-coverage plan
  `Temporary states + their canonical follow-up plans` section.

- **Per-VM shard isolation for concurrent backfills (workspace rule — codified 2026-05-06)** — Every multi-worker
  backfill (multiple chunk processes locally OR multiple GCE VMs writing to the same manifest) MUST set
  `VM_NAME=<unique-tag>` + `MANIFEST_PER_VM_SHARDS=true` per worker. The manifest consolidator merges per-VM shards
  under `_index/per_vm/{vm_name}.parquet` into the canonical `_index/availability_index.parquet` with last-writer-wins
  on identical row*key. Without this, concurrent workers race on the canonical CAS and the
  retry-15-then-unconditional-write fallback clobbers each other's rows. `ManifestWriter.__init__` runtime guard: if
  multi-process detection fires AND per-VM shard isolation isn't set → raise `MultiWorkerWithoutShardIsolationError`.
  New base-service.sh QG STEP 5.66 AST-walks launcher scripts that fork multi-process; asserts envvar setting. Reference
  incident: 2026-05-04 instruments-service `00f6352` + `619a32e` chunk workers without isolation clobbered each other's
  manifest entries. Plan: `pre_flight_concurrency_hardening_2026*<TBD>.plan.md` (Plan C in writegate follow-ups).

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
- **VIX 15m source layering (workspace-wide rule, applies across MTDS / data-status / manifest / features-\*)** — VIX
  15m intraday has TWO non-overlapping sources and one accepted gap. All layers must understand the layering or they
  silently corrupt history.
  1. **Barchart historical preload** (`BARCHART_VIX_FIRST_DATE` 2020-01-02 → `BARCHART_VIX_LAST_DATE` 2025-11-12) —
     one-time bulk import sat in GCS as ~15 daily parquet files; manifest already has `captured` rows for every trading
     day in the range. **Never re-fetch via Yahoo for these dates** — the rolling 60-day window doesn't reach them, so a
     Yahoo round-trip returns empty and stamping `empty_confirmed` overwrites real history. MTDS `_fetch_yahoo_vix_15m`
     short-circuits to empty WITHOUT calling Yahoo when `BARCHART_VIX_FIRST_DATE <= target <= BARCHART_VIX_LAST_DATE` —
     the manifest is left untouched so the existing Barchart row stands.
  2. **Yahoo Finance 15m rolling window** (`get_yahoo_vix_15m_start()` ≈ today − 60d → today) — used for all dates past
     `BARCHART_VIX_LAST_DATE`. UAC `YAHOO_VIX_15M_WINDOW_DAYS = 60` is the SSOT for the window length; if Yahoo ever
     extends to 90, bump that constant only.
  3. **Honest gap** (2025-11-13 → today − 60d) — no source covers this range. UAC `is_vix_15m_gap_date(date)` returns
     True; MTDS returns empty so the orchestrator records `empty_confirmed`. Data-status must understand this is an
     accepted gap (denominator clip), not a coverage hole.

  **Routing surface**: in `market_tick_data_service/adapters/umi_tick_provider.py`, the (CBOE, ohlcv_15m) shard is
  routed to `_fetch_yahoo_vix_15m` BEFORE the generic Databento route — Databento's GLBX.MDP3 doesn't carry the spot VIX
  index, so the legacy path silently emptied the data_type via `_DATABENTO_SUPPORTED_DATA_TYPES` filtering.
  **Pre-2020-01-02 dates** are out of scope for VIX 15m (no source ever existed); the route returns empty without
  calling Yahoo. Reference incident **closeout 2026-05-06**: 17 VIX 15m days were filled manually via
  `/tmp/fill_vix_15m_yahoo.py` because the route wasn't wired; the helper this rule references uses the same shape.

- **Manifest concurrency principle (workspace-wide)** — Any script that consumes the availability manifest as a "to-do
  list" (instruments-service backfills, MTDS gapfills, MDPS reprocessors, features-\* recomputes, strategy-service
  archetype runs, execution-service event replays, deployment-service backfill VMs, end-to-end test suites) MUST follow
  the **read-once + per-date freshness check + write-time CAS** pattern when concurrent workers may operate on the same
  manifest:
  1. **Startup**: bulk-read the canonical manifest ONCE, cache the skip-set (`captured` / `empty_confirmed` /
     `attempted_failed`) and derive the missing list. Trust this cached view for the work-selection decision.
  2. **Mid-run** (per-date / per-shard): before firing the expensive remote call (Databento, Tardis, web scrape, etc.),
     do a **TTL-refreshed targeted lookup** of just THIS row_key in the canonical manifest. The TTL is 60s by default —
     enough to amortise the GCS read across 6-10 fetches without burning a full re-read per item. If the row is now
     `captured` → skip (a concurrent worker beat us; their parquet is on disk and the manifest is honest).
  3. **Write-time**: `ManifestWriter.record_captured` writes to the per-VM shard with CAS semantics; the consolidator
     daemon merges per-VM shards into the canonical manifest with dedup (last-writer-wins on identical row_key). This is
     the only safe race-resolution point for the actual write.
  4. **What NOT to do**: (a) per-date full-manifest re-reads — burns ~30MB GCS read per fetch, more expensive than the
     duplicate fetch we'd avoid; (b) blind iteration with no freshness check — concurrent workers' progress is wasted;
     (c) aggressive cache TTL (<30s) — hammers GCS for marginal gain. The TTL is a tuneable knob; 60s is the default.
  5. **Reference incident 2026-05-05**: TradFi MBT/MET full backfill — launched 2 originals (chronological from
     2022-01-01) + 2 helpers (`--clip-after 2025-01-01`). Without the per-date check, originals would have wasted ~336
     Databento fetches per root re-doing helpers' work when chronological iteration reached the helpers' range. With the
     principle baked in, originals naturally skip helper-captured dates; helpers finish the late slice 2 hours before
     originals reach it. Saves ~1.5 hours wall-clock + ~672 wasted Databento calls.
  6. **Reference impl**: `/tmp/fill_missing_ohlcv.py` (`_refresh_captured_cache` + `_is_now_captured` helpers) is the
     canonical pattern. Future scripts should mirror this shape — `_TTL_SECONDS=60`, in-memory `(root, date)` set,
     refresh-on-demand at fetch time. New backfill scripts MUST include this pattern; refactor existing scripts that run
     multi-VM (instruments-service per-source backfills, MTDS per-venue VMs, MDPS reprocess pipelines) to add it.
- **Manifest phantom audit** — Manifest can drift if adapters record `captured` for a shard but the parquet doesn't
  exist at the canonical path (stale rescan output, schema migration churn, broken denorm). The orchestrator's
  `_should_skip_shard` trusts the manifest, so phantoms cause permanent skip. Periodic audit:
  `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group {cefi|defi|tradfi|prediction|sports} --dry-run`
  (multi-asset-group; `reconcile_phantom_manifest_rows.py` is sports-only and being phased out). Five drift axes the
  audit handles: (1) hive-vocab `category=` vs `asset_group=`, (2) instrument_type casing PERPETUAL vs perpetual, (3)
  empty schema-4 instrument_type, (4) path-prefix drift `day=*/` vs `raw_tick_data/by_date/day=*/`, (5) chain-bundle
  equivalence `option`↔`options_chain` / `future`↔`futures_chain`. Plus: HTTP pool tuned to `2*workers` (default 10
  silently truncates `list_blobs()` under 64-worker concurrency). **Always run on a same-region GCE VM** — cross-region
  listing is 18× slower (~12 prefixes/sec from laptop vs 222/sec on `asia-northeast1-c`). Recipe:
  `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit — re-runnable recipe".
  Critical: do NOT write empty placeholder parquets to mask phantoms — that's fudging data quality.
  `record_empty(row_key=...)` is for legitimately-empty source responses only (we tried, API returned 200+empty).
  Reconciliation incidents: 2026-04-29 — 167k fake PLAYER_VALUES denorm rows + 15k legacy phantoms cleaned up;
  2026-05-04 — 130,897 false-positive phantoms across CeFi diagnosed as path-prefix + chain-bundle drift, audit
  hardened, real residual = 354 (99.7% reduction).
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
- **VM Naming Convention** — Every `gcloud compute instances create <NAME>` must use a name whose first segment is a
  prefix listed in `VM_PREFIX_TO_BUCKET` in
  [`deployment-service/scripts/vm/vm_zombie_watchdog.py`](../../deployment-service/scripts/vm/vm_zombie_watchdog.py). If
  your launcher needs a new prefix, add it to the dict (with the right shard bucket, or `None` for heartbeat-only) in
  the same change. **A VM whose prefix is not in the dict is invisible to the zombie watchdog** — it can sit RUNNING
  forever burning money on a network partition. Patterns:
  - Asset-group market-data: `{asset_group}-{venue}-{flavor}-{ts}` (e.g.
    `cefi-bitfinex-spot-2023-heavy-20260504-194158`); `asset_group ∈ {cefi, defi, tradfi, prediction, sports}`.
  - Forward-poll: `{asset_group}-fwd-{ts}` (e.g. `cefi-fwd-20260504-...`) or `{source}-fwd-{ts}` for sports.
  - Source-keyed sports backfill: `{source}-backfill-{ts}` where `source ∈ {af, fs, tm, sfi, us, openmeteo}`.
  - MTDS asset-group-scoped backfill: `mtds-{operation}-{ts}` (e.g. `mtds-perp-funding-`, `mtds-prediction-`,
    `mtds-gas-fees-`, `mtds-lst-rates-`, `mtds-vault-`).
  - Singletons / one-offs (instr-discovery, manifest-consolidator, watchdog): bare service prefix is fine
    (`manifest-consolidator-{ts}`, `vm-zombie-watchdog-{ts}`); never use a name with no timestamp unless it's a true
    singleton like `mtds-perp-funding-backfill` whose launcher hardcodes the bare name.
  - Always use `RUN_TS="$(date +%Y%m%d-%H%M%S)"` for the trailing entropy — sortable and greppable. UUIDs are not used
    and add nothing the watchdog cares about. After editing the dict, **relaunch the watchdog VM**
    (`gcloud compute instances delete vm-zombie-watchdog-* --zone=asia-northeast1-c --quiet` then
    `bash deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh`) — the running watchdog only fetches the Python at
    boot. Reference incident: 2026-05-05 — 5 prefixes (`cefi-bitfinex-`, `cefi-bitget-`, `cefi-kraken-`,
    `mtds-perp-funding-`, `instr-`) silently zombied because their launchers were added without dict updates. SSOT for
    the table: the Python file. The launcher comment block is documentation, not the dict.

- **Two teammates × multiple parallel agents — don't edit unfamiliar files (CRITICAL)** — Harsh AND Ikenna both work
  this workspace continuously, **each running multiple parallel agents (Cursor + Claude Code sessions in flight at the
  same time)**. Untracked files in any repo, dirty mid-edit state, or remote commits that landed in the last few minutes
  are almost always someone else's in-flight work. **Do not touch a file outside your clear context just to clear a QG
  gate, lint check, or scope-registry check.** Formatting / mechanical fixes on files YOU are already legitimately
  editing are fine. Editing untracked files, codex docs you haven't read, or plan files you're not working on is NOT.
  - **Never run `git checkout origin/<branch> -- .`** as a recovery move — it dumps remote changes (including other
    agents' just-landed work) into your working tree, and your subsequent commits absorb their content as if it were
    yours.
  - **If a quickmerge stash conflict happens**, resolve by reading the specific file and editing surgically, NOT by
    mass-resetting the working tree. Mass resets pull in 20+ files of noise from old stashes that then look like "your"
    changes.
  - **Untracked file in a dep repo = NOT YOURS.** Reference incident **2026-05-06**:
    `unified-trading-pm/codex/02-data/pipeline-coverage-matrix.md` was Ikenna's untracked WIP. Claude added a `scope:`
    frontmatter to it to satisfy a workspace-wide codex scope-registry QG check. Prettier then double-formatted the
    edit, the file landed in Claude's commit. If Ikenna had unsaved local edits, they were lost.
  - **The right escape valve when a QG gate fails on a file you don't own**: tell the user. The cost of one extra
    question is far lower than the cost of clobbering a teammate's work. Workspace rule **"DO NOT run quickmerge when
    local dep repos are dirty unless the user explicitly asks"** applies here too — same shape, different surface.

- **Clear context = implement, don't ask** — When the plan / SSOT / prior turns in the same conversation already name
  the canonical approach with a `[SCRIPT] P0` todo (file:line + exact change), **just ship it.** Asking the user to pick
  between (a)/(b)/(c) when the plan already specifies the answer wastes their time and signals indecision. Apply when
  the plan has a concrete todo, the user has chosen direction earlier in the conversation, a workspace SSOT names the
  fix shape, or an audit report concluded with a specific recommendation. **Don't apply when** the operation is
  destructive beyond what was authorized, the work would touch files outside your clear context (see "Two teammates"
  rule above — these compose), or the plan explicitly says "AWAITING USER DIRECTION." Reference user feedback
  2026-05-06: _"you are a grown up man, please take the decisions on your own for such trivial minor things dont wait
  for me to guide you everywhere"_ + _"execute when the plan already specifies the fix."_

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

**Removed providers** (do NOT reference): Elysium, Arkham, Bloxroute, Infura — all deleted from UAC, MTDS, docs.

**Pyth — UNBANNED 2026-05-06** for Solana on-chain price feeds. `carry_staked_basis` LST yields (jitoSOL / mSOL / bSOL)
need on-chain Solana prices; Chainlink covers EVM only (Arb / Base / Polygon), not Solana; no viable Switchboard wiring
exists in workspace. Re-add Pyth via Hermes (HTTPS pull) for batch and PythNet (Solana RPC) for live. Scope: Solana-only
price reads. Other chains continue using Chainlink. Decision recorded in
`unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.plan.md` Q&A section +
`unified-trading-pm/plans/active/defi_master_2026_05_07.plan.md` (`mtds-s3-5-pyth-oracle` todo lifted from
`plans/archive/consolidated_defi_data_pipeline_2026_04_15.plan.md`).

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

### Deployment-stack restart (SSOT — overrides earlier guidance)

For the **deployment-api (port 8004) + deployment-ui (port 5183)** pair — the data-status / deployment-flow stack — the
canonical local script is:

```bash
bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh           # restart both
bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --api      # restart deployment-api only
bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --ui       # restart deployment-ui only
bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --stop     # stop both, don't restart
```

**This script supersedes the prior `dev-start.sh --api deployment-api` + `cd deployment-ui && npm run dev` two-step.**
Do NOT use the legacy two-script invocation for this pair.

Behaviour:

- **Always real cloud mode** (`CLOUD_PROVIDER=gcp`, `CLOUD_MOCK_MODE=false`) — no mock flag. Reads the same Cloud Run
  rollup bucket the shared `uts-shared-deployment-api` Cloud Run service does, so the in-region slicer fast-path lights
  up locally too (Jan 2018 → today response in <2s instead of 5+ min).
- **Hardcoded ports** (8004 / 5183) — `deployment-ui/src/contexts/CloudProviderContext.tsx` resolves the API base via
  `window.location.hostname`; on `localhost` it dials port 8004 verbatim. Changing either port breaks the UI's
  same-origin proxy and every widget shows "Failed to load".
- **CLI flags scope the restart** — `--api`/`--ui`/`--all` (default) — so day-to-day tweaks don't bounce the other.
- **Startup logs / pids** under `${TMPDIR}/deployment-stack-pids/` (macOS: `/var/folders/.../`, Linux: `/tmp/`).

### Other tiers (unchanged)

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

## Commit + Push + Flip Plan Checkboxes As You Ship Each Item (HARD RULE)

This rule has TWO mutually-reinforcing halves. Both are non-negotiable. Violating either breaks parallel-agent
coordination and loses work.

### Half 1 — Commit + push at every shippable unit

A "shippable unit" is the smallest meaningful slice of work that QGs cleanly on its own — a helper + its tests, one
adapter migration, one reconciler, one consumer wire-in. **The moment a shippable unit is green, commit + push.**
Do not batch shippable units across a session waiting for a "natural pause."

- **Pushed = real.** A local-only commit is invisible to every other agent + every CI gate + every running VM that
  pulls from `live-defi-rollout`. Until you `git push`, your work doesn't exist as far as the rest of the workspace
  is concerned.
- **The cadence is per-shippable-unit, not per-hour or per-session.** Five shippable units in one session = five
  commit+push cycles, not one. Each cycle is small enough to revert cleanly if a downstream agent flags a regression
  half an hour later.
- **No "I'll commit after the next thing."** That's how 2-hour-old uncommitted work gets clobbered by a quickmerge
  stash, an auto-formatter pass, or another agent's `git add <file>` accidentally hoovering up your unstaged hunks
  (reference incident: PM@961980db — a teammate's local-uncommitted audit section got bundled into another agent's
  plan-flip commit because the second agent staged the whole file instead of `git add -p`-ing their own hunks).
- **End-of-session commits are a smell.** If you find yourself with 4 hours of uncommitted work as you're writing
  the handoff, the rule was already violated.
- **`live-defi-rollout` is the working branch.** VMs pull from it; CI runs against it. Push directly per the
  workspace dirty-deps rule (`git add <my-files> && git commit --no-verify && git push origin live-defi-rollout`)
  rather than waiting for a quickmerge → main promotion cycle.

### The mandatory pre-commit check (catches accidental bundling)

Before EVERY `git commit` in any repo where another agent might have staged or modified files in parallel, run:

```bash
git status                 # full picture: modified, staged, untracked
git diff --cached --stat   # NO PATH ARGUMENT — see the entire index
```

If anything is in the staged set or working tree that isn't yours, surgically un-stage it (`git restore --staged <file>`)
or `git stash --keep-index` the unrelated stuff before committing. **Never pass a `<path>` argument to
`git diff --cached --stat`** — that filters the output to just that path and masks other staged hunks.

Reference incidents (both 2026-05-07 PM repo, both bundled foreign work into a single agent's commit):

* PM@961980db — bundled a teammate's local-uncommitted "Audit 2026-05-07" plan section because `git add <plan-file>`
  picked up the whole current file state, including their unstaged hunks.
* PM@611b9501 — bundled a teammate's `git mv` (plan promotion ai/→active/) because the agent only checked
  `git diff --cached --stat <single-path>` and missed the rename already sitting in the index. **The very commit
  that codified this rule was an instance of the foot-gun the rule warns about.** That's how easy it is to fall
  into; do the full-status check.

### Half 2 — Flip the plan checkbox in the same logical unit

When working through a plan, you MUST flip the `- [ ]` checkbox to `- [x]` for each todo **as soon as the underlying
work is shipped (committed + pushed)** — not at the end of the session, not "after the next agent picks it up", not
batched into a single sweep at handoff time. The flip happens in the same logical unit of work as the code commit:

1. Ship the code commit (or commits) that complete the todo. **Push it.**
2. Edit the plan file: `- [ ] [SCRIPT] P0. Description...` → `- [x] [SCRIPT] P0. Description... (commit-sha + brief evidence)`.
3. Commit the plan flip in the PM repo with a `plan(...)` prefix referencing the work commits. **Push it.**
4. Only then move to the next todo.

**Don't flip a checkbox unless the work is actually shipped.** Pushed commits count; local commits do NOT. If the
work is half-done (e.g. helper shipped but consumer wiring deferred), flip only the half that landed and append a
`**DEFERRED**:` note to the unshipped half explaining why.

**The flip belongs in a separate commit** in the PM repo (or bundled with other doc-only PM changes), with the
canonical message shape:

```
plan(<plan-name>): flip <Phase>.<Tier> checkboxes (<one-line summary of what shipped>)

* <repo>@<sha> — <one-line>
* <repo>@<sha> — <one-line>
* ... (cite every code commit the flips reference)

Plan: <plan-filename>.
```

### Why both halves are non-negotiable

- The plan is the operator's read-only view of "what's left." If checkboxes lag the actual state, the operator can't
  trust them, and parallel agents re-do work that's already shipped.
- Two agents reading the same plan must see the same in-flight state. Stale checkboxes cause work-stealing collisions
  (two agents implementing the same item in parallel).
- "I'll commit + flip everything at the end" routinely loses items. Someone gets summoned mid-session, context fills
  up, the auto-formatter clobbers an unstaged file, the flip never happens, and the next agent reads the plan as if
  nothing was done.
- Per-shippable-unit pushes are the ONLY way the workspace's parallel-agent + per-VM-pull-from-`live-defi-rollout`
  + manifest-concurrency-protocol model works. A 4-hour uncommitted block is invisible to everything else and
  blocks no work but yours.

This applies to every plan in `plans/active/` and every working session — tier completions, partial flips inside a
tier, even single-item flips when that's all the session shipped. Reviewers reject sessions that ship code without
the matching plan flip, and reject sessions that have stale uncommitted work older than a single shippable unit.

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
