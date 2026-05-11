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
  `unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.md`
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
   `unified-trading-pm/plans/active/venue_axis_asset_group_vocabulary_2026_04_25.md` (Waves A/B/E shipped; C/D =
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
  `codex/14-customer-journeys/shared-core/signal-broadcast-architecture.md`; architecture plan (archived 2026-05-06, 8
  phases shipped): `plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md`.
- `logger.warning("%s", _err.message)` not `logger.warning(_err.message)` — the message is not a format string
- `.env` files must NEVER contain placeholder credential paths — ADC is the default
- **Bandit B108 / temp paths** — Never hardcode `"/tmp"` in Python. Use `tempfile.gettempdir()` (POSIX `TMPDIR`, macOS
  temp under `/var/folders/...`). For disk-usage probes, default to root + `gettempdir()` + `Path.home()` and skip
  missing paths. SSOT: `unified-trading-pm/codex/06-coding-standards/quality-gates.md` (Bandit B108 section).
- Service CLIs follow standardised axes: `--operation` (what), `--mode` (batch/live), `--asset-group` (domain). See
  `codex/06-coding-standards/cli-convention.md`.
- **Availability manifest v5 (honest-coverage)** — `ManifestWriter` writes proper shard columns (venue, chain,
  data_type, instrument_type, league_id, timeframe, feature_group, model_family, training_period, strategy_id,
  client_id, instruction_type) PLUS `capture_status` (4-state closed set: `captured` / `empty_confirmed` /
  `attempted_failed` / **`expected_unattempted`** added 2026-05-07 evening per writegate Phase 3.D.5), `error_reason`,
  `attempted_at`. Adapters MUST distinguish: `record_captured(...)` for real-data writes;
  `record_empty(row_key=..., reason=<typed>)` for legitimately-zero source responses (typed reason from
  `EMPTY_CONFIRMED_REASONS` REQUIRED — blank rejected loudly via `LegacyBlankErrorReasonError` per UTL@68b3804a after
  the 2026-05-07 RED ALERT silent-fallback bug);
  `record_failed(row_key=..., error=classify_venue_error(exc), attempted_at=...)` for exceptions;
  `record_expected_unattempted(row_key=, attempted_at=)` for catalog-says-this-should-exist-but-not-fetched-yet
  (pre-populated by v2 expected-universe enumerator from instruments-service catalog cross-product). **Never overload
  `venue`** with non-venue data. **Asset-group-specific empty_confirmed legitimacy rule (operator directive 2026-05-07
  msg 6)**: sports / prediction CAN have empty_confirmed at instrument-day grain (no fixtures today / no markets active
  is normal); cefi / defi / tradfi CANNOT — only venue-level rules (HOLIDAY / WEEKEND / PRE_VENUE_LAUNCH /
  PRE_GENESIS_CHAIN / PARTIAL_HALF_DAY) make empty_confirmed legit. Catalog-says-alive instrument-day with source-zero
  in cefi/defi/tradfi MUST flip to attempted_failed (caught at write-side by the catalog-aware guard once Wave 3 wires
  the `instrument_catalog` reference at MTDS adapter construction). **Two SSOTs for the manifest's expected universe**:
  UAC SSOTs (`*_LAUNCH_DATES` / `*_GENESIS_DATES` / `SOURCE_COVERAGE_START` / `venue_trading_calendar`) own the coarse
  "is this `(asset_group, venue, day)` structurally possible" axis; instruments-service catalog owns the fine "given
  alive, what instruments exist on this day" axis. Both layers write to the manifest; MTDS's `record_captured` cleanly
  supersedes prior `expected_unattempted` rows by row_key. **Coverage % at every drilldown level** =
  `captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)` — denominator is the full universe
  (catalog × dates × data_types). SSOTs: `codex/02-data/availability-manifest-and-data-status.md` (manifest schema +
  4-state taxonomy); `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` § Phase 3.D.5 (full architecture).
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
  parallel-stream coordination notes in `unified-trading-pm/plans/epics/infrastructure_master_2026_05_07.md` (umbrella)
  which folds-in `plans/archive/shard_granularity_ssot_propagation_2026_05_06.plan.md` + its `.HANDOVER.md` companion
  (commit `d591416d`). Sub-agents executing this work pick the rules up via this section + the umbrella + the archived
  handover doc + SUB_AGENT_MANDATORY_RULES.md inheritance.

- **Live = batch — same data, same fields, same timing semantics, different sources OK (CRITICAL — applies to every
  asset_group)** — Live and batch are operational modes of the SAME pipeline. They produce identical schemas, identical
  `data_types`, identical fields. The ONLY thing that legitimately differs is which SOURCE serves a given
  `(asset_group, data_type)`, because some sources lag others on real-time emission. Historical writes MUST be
  timestamped with the `available_at` we'd actually have in live mode (the
  `unified_api_contracts.canonical.crosscutting.source_priority.SOURCE_PRIORITY` top entry's emission time, NOT the
  canonical historical source's slower archive time). Banned anti-patterns: separate live-only data_types like
  `LINEUPS_PRE_MATCH` vs `LINEUPS_POST_MATCH`; distinct field sets between live + batch parquets; deriving
  `available_at` at read-time from the live-batch mode flag. Reference: 2026-05-06 user direction during
  writegate-honest-coverage planning. Plan: `writegate_honest_coverage_endtoend_2026_05_06.md`.

- **No double SSOT in data-saving methodology (CRITICAL — applies top-to-bottom)** — Where two paths produce the same
  outcome, one is deleted. Banned coexistence: `_create_empty_output()` AND `_handle_empty_tick_data()` (writegate plan
  Phase 2.A deletes the placeholder method); `_ensure_timestamp` shim AND per-source `stamp_available_at_*` helpers
  (writegate Phase 2.C deletes the shim); parallel v3-shape `_write_manifest_records` AND v6 canonical writer (writegate
  Phase 2.A deletes the v3 path); inline NaN-ratio gate AND UTL `write_gate_helper` (Plan B Q #4 lifts the inline);
  per-service phantom-audit drift probe AND UTL `manifest_audit` module (Plan B Q #5 lifts the script). When you find
  yourself maintaining two ways to do the same thing, kill one — don't add a third helper to "reconcile" them.

- **Four-category empty-output decision (every per-shard adapter — MDPS / MTDS / features-\* / instruments-service)** —
  Every condition that could produce an empty result resolves to ONE of: **A. Source returned 0 ticks for the requested
  window** → `record_empty(row_key, reason=<typed>)` (honest absence; reason MUST be from `EMPTY_CONFIRMED_REASONS` —
  blank rejected via `LegacyBlankErrorReasonError` per UTL@68b3804a); **B. Source returned ticks; ALL fall outside the
  requested day after `interval_idx` filter** →
  `record_failed(UpstreamTimestampBiasError(observed_dates, expected_day, n_ticks))` (UPSTREAM BUG — partition
  mislabeled at MTDS write-time, source replay covered wrong window, OR clock-skew; paired upstream fix at MTDS
  `raw_tick_hive.py` partitioner-validation); **C. Rows in window but downstream calc dropped all rows due to
  NaN/malformed source fields** → `record_failed(MalformedTickFieldError(field, n_dropped, sample_values))`
  (data-quality bug worth diagnosing); **D. Source returned 0 BUT instruments-service catalog says the instrument was
  ALIVE on the day AND day falls within venue market hours** (operator directive 2026-05-07 msg 8) → **NEW**: write
  zero-activity bars (O=H=L=C=prior_LTP, volume=0, trade_count=0 — shape per data_type) and `record_captured` with the
  real bar count. Captures the "tradeable but illiquid" semantic distinct from "missing" — critical for cross-instrument
  analyses like volatility smiles where every strike must be visible. The catalog- aware write-gate (writer-side guard,
  Wave 2 of Phase 3.D.5) drives the (A) vs (D) split: when `instrument_catalog` is wired and reports the instrument
  alive, blank-zero-source-response gets routed to (D). Until the writer-guard ships, adapters use the manifest
  classifier helper `classify_blank_reason_row` to apply the same logic at the manifest level. **For sports / prediction
  the (D) bar shape uses prior bookmaker odds / prior market mid as carry-forward**; for cefi / defi / tradfi it's prior
  trade LTP. NO silent NaN placeholder rows. The `_create_empty_output()`-style placeholder method is **banned** from
  `base_adapter` and any equivalent base class. Reference incidents: 2026-05-05 MDPS 1440 NaN OHLC bars per day per
  (venue, data_type); 2026-05-07 RED ALERT (5 CeFi VMs writing 96-100% empty rows with all blank reasons —
  bitfinex/bitget/kraken). Plan: `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 2.A + Phase 3.D.5 (Waves 1, 2,
  2.M shipped 2026-05-07; Wave 3.M zero-activity-bar adapter audit pending).

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
  `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 1A.

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
  `tick.timestamp <= T` AND `tick.market_id`'s `market_created_at <= T`. Plan: `predictions_master_2026_05_07.md`
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
  manifest entries. Plan: `pre_flight_concurrency_hardening_2026*<TBD>.md` (Plan C in writegate follow-ups).

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
- **VM launcher script SSOT (codified 2026-05-07)** — Every script that runs `gcloud compute instances create` (or the
  AWS `aws ec2 run-instances` equivalent) MUST live under `deployment-service/scripts/vm/`. No exceptions. Ad-hoc
  launchers under `e2e-testing/scripts/`, `features-*-service/scripts/`, or any other repo are technical debt and must
  be migrated. **Why:** the deployment-UI is the workspace SSOT for "how do we launch a VM"; the Deploy-Missing button +
  the operational launchers all read from a single registry (`_SERVICE_LAUNCHER_SCRIPTS` in
  `deployment-api/deployment_api/services/deploy_missing.py`). Scattered launchers (a) bypass the registry so the UI
  can't render Deploy-Missing for them; (b) miss the workspace conventions (`MANIFEST_PER_VM_SHARDS=true`,
  `VM_NAME=<unique-tag>`, `RUN_TS="$(date +%Y%m%d-%H%M%S)"`, the `VM_PREFIX_TO_BUCKET` registry from the rule below);
  (c) drift in shape over time, breaking parallel-agent reasoning. **Four ways the script reaches the VM** (UI exposes
  the first two as a mode toggle): (1) **Tarball** (default + production) —
  `gs://deployment-scripts-${PID}/code/<tarball>.tar.gz` → `setup-data-pipeline-vm.sh` extracts at boot. Refresh via
  `create-code-tarballs.sh --all`. (2) **Tarball-from-local** (developer path; UI mode toggle) — bundles the operator's
  CURRENT local working tree (uncommitted edits included) before VM launch. **ONLY works from the operator's
  workstation**, never from the deployment-api Cloud Run pod. The `/data-status/deploy-missing-preview` endpoint emits a
  `LOCAL-ONLY + UNCOMMITTED CHANGES` warning when picked. (3) **Sibling-clone** (local-stack dev) — workstation has
  every service repo cloned as siblings under `${WORKSPACE_ROOT}` per workspace-manifest; CI / Cloud Run does NOT have
  sibling clones. (4) **Image** (future) — bake launchers into a Docker image cached in Artifact Registry / ECR;
  deployment-api pulls + runs. Tracked in `plans/ai/deploy_missing_auto_launch_2026_05_07.md`. **Adding a new
  launcher:** file lives under `deployment-service/scripts/vm/launch-{asset_group}-{flavor}-vm.sh`; register VM-name
  prefix in `VM_PREFIX_TO_BUCKET`; register the script in `_SERVICE_LAUNCHER_SCRIPTS` if it should be reachable from the
  Deploy-Missing UI button. **Migration in flight (2026-05-07):** 30 ad-hoc launchers under `e2e-testing/scripts/`
  - `features-sports-service/scripts/` + the intra-repo `deployment-service/scripts/deploy-dashboard-gce-vm.sh` pending
    migration. Plan: `plans/ai/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`. Until plan ships,
    Deploy-Missing UI button degrades to "no launcher registered" for those services; operators run the ad-hoc script
    manually. SSOTs: `codex/05-infrastructure/launcher-script-ssot.md` +
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
  - **Never run `git checkout -- <file>` to revert a tool's modifications on a foreign-owned dirty file.**
    `git checkout --` discards ALL working-tree changes for that file — including the foreign agent's uncommitted WIP,
    not just the tool's output. **It is unrecoverable**: not in reflog (working-tree only), not in stash, not in fsck.
    The right recoveries when a tool (ruff / prettier / formatter / sed-style refactor) modifies foreign files alongside
    your owned files:
    - **(a) Scope the tool to YOUR files** before running. `ruff check <my-file1> <my-file2>` not `ruff check .`. Same
      for prettier / sed / formatters. Audit `git status --porcelain` first; pass only YOUR paths to the tool's argv.
    - **(b) Stash foreign-modified files BEFORE the tool runs.**
      `git stash push --keep-index -- <foreign-file1> <foreign-file2>`. Run the tool. Commit your auto-fixes.
      `git stash pop` restores their WIP.
    - **(c) Accept that you can't auto-fix foreign code.** Skip those files. Open an issue doc citing the foreign
      breakage; their owner agent fixes on their own commits per "QG failure attribution" rule.
    - **(d) If you've ALREADY mass-modified the tree and need to scope your commit**, use pathspec form:
      `git commit --only -- <my-file1> <my-file2>` (commits ONLY those paths, leaves working-tree foreign mods
      untouched), THEN `git checkout -- <foreign-file>` is STILL banned — you'd lose their unstaged WIP. The correct
      followup is to leave the foreign-modified files in working tree as-is and let the foreign agent reconcile via
      their own next pull.

    Reference incident **2026-05-08 Foot-gun #2**: ruff cleanup sub-agent ran `ruff check . --fix --unsafe-fixes` on the
    whole features-service tree; ruff modified 116 files including 12 with foreign agent's uncommitted WIP. Sub-agent
    then used `git checkout -- <file>` per-file to revert ruff's modifications on the 12 dirty files, intending to
    preserve the foreign agent's edits. The `git checkout --` actually discarded BOTH ruff's fix AND the foreign agent's
    WIP — ~12 files of Phase 4-5 consolidation work lost from disk; not recoverable. Issue doc:
    [`plans/active/issues/foot_gun_2_features_service_uncommitted_wip_clobbered_2026_05_08.md`](../plans/active/issues/foot_gun_2_features_service_uncommitted_wip_clobbered_2026_05_08.md).
    The right behaviour would have been (a): pass only the staged-clean files to ruff, OR (b): stash the 12 dirty files
    before running ruff. Codified 2026-05-08 PM after operator surfaced the incident.

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
`unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.md` Q&A section +
`unified-trading-pm/plans/active/defi_master_2026_05_07.md` (`mtds-s3-5-pyth-oracle` todo lifted from
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

## Plan Archival — preserve deferred work + unfinished operational steps (HARD RULE codified 2026-05-08)

A plan archives when its primary scope is shipped. **The archive boundary is an audit boundary, not a deletion event.**
Any item the plan deferred — `**DEFERRED**`, `**NICE-TO-HAVE**`, `**DEFERRED-PER-USER**`, "future work", "out of scope",
"post-cutover", "stretch goal", a half-shipped item, a banned configuration that's still in code, OR a planned-but-
unrun operation (deploy / backfill / migration / VM launch / data refresh / index rebuild) — MUST land in an active home
before the archive commit ships. Otherwise the deferred work falls off the workspace radar; the operator asks again
three weeks later; we burn an hour reconstructing what was deferred and why; the cycle repeats.

### What counts as "deferred"

Three categories — all three are in scope. Mixing them or losing the boundary between them is the failure mode.

1. **Scope deferrals** (most common). The plan body cited an item it explicitly chose NOT to do this cycle: a
   nice-to-have feature, a P2/P3 polish item, a follow-up sweep, a post-cutover revisit, an "out of scope" caveat. The
   item is feature work, not operational work.
2. **Operational gaps** (often invisible). The plan body declared work as done — feature complete, code merged, QGs
   green — but the actual VM was never launched, the backfill was never started, the migration was never run, the
   reindex was never triggered, the staging deploy was never promoted to prod. Code-shipped is not the same as
   operationally-shipped. **The archive must distinguish "code shipped" from "operationally shipped" and never treat
   them as interchangeable.** Reference incidents: writegate Phase 2.A `_create_empty_output()` deletion (code shipped
   2026-05-07; banned-pattern AST sweep across services took another day to actually land); MDPS `1440-NaN-bar`
   reconciler (code shipped 2026-05-05; the actual reconcile-then-rescan run on production manifests was a separate
   operational step that a follow-up agent had to chase down because the plan said "done"); 2026-05-04 instruments-
   service `00f6352` chunk worker (code shipped without per-VM shard isolation; operational gap not caught until 2 days
   later when concurrent runs raced on the canonical CAS).
3. **Half-shipped items**. The plan flipped a checkbox to `- [x]` for an item where only part of the work landed. The
   `**DEFERRED**:` annotation on the unshipped half (per `Commit + Push + Flip` HARD RULE) is the hint — every such
   annotation needs a home in an active plan, not just a comment that decays in the archive.

### The discipline

When you propose archiving a plan (status: complete, `locked_by` removal, move to `plans/archive/`), you MUST do all
five steps as part of the same logical unit:

1. **Audit the archiving plan**: scan the body for every `**DEFERRED**` / `**NICE-TO-HAVE**` / `**DEFERRED-PER-USER**` /
   "post-cutover" / "out of scope" / "future work" / "stretch" / "follow-up" annotation. Count them. List them.
2. **Audit operational completeness**: for every shipped item that touches operational state (VM launch / backfill /
   migration / deploy / reindex / data refresh), verify the operation actually ran in production — not just that the
   code shipped. Check event streams (`gs://{pid}-events/...`) / VM history / manifest state / deploy logs / migration
   ledger. If the operation never ran, it's deferred operational work — same disposition as a scope deferral.
3. **Migrate every deferred item to an active home**. Three valid dispositions, mutually exclusive:
   - **(a) Fold into an existing active plan** that's the natural owner. The deferred item becomes a `- [ ]` todo in
     that plan's body with a `**MIGRATED FROM:** <archived-plan-name>` provenance line. Pick the plan whose scope
     matches; don't dump unrelated items into a convenient bucket.
   - **(b) Spawn a new active plan** if no existing plan owns the scope. Plan filename `<slug>_<YYYY_MM_DD>.md` per the
     Plan Filename Convention; frontmatter cites the archiving plan as `migrated_from:`; body opens with a 2-3 line
     "What this is" paragraph explaining it's a deferred-work continuation.
   - **(c) Write a `plans/active/issues/<slug>_<YYYY_MM_DD>.md` issue doc** if the deferred item isn't owner-clear yet
     (needs operator triage to assign to a plan). Use the issue-doc shape from `Findings Triage Discipline`. Issue docs
     must triage to (a) or (b) within ≤7 calendar days; an issue doc that sits unrouted >7 days is itself a finding.
4. **Banner the archived plan** with a `## Deferred work — migrated to:` section enumerating every migrated item with
   its destination (plan filename + section anchor). The archive-side banner is read-only after archival but it's the
   forward index for anyone reading the archived plan: "this looked deferred, here's where it lives now."
5. **Update CLAUDE.md or codex SSOTs** if any of the deferred items affected a workspace contract / pattern / SSOT. Same
   shape as the `Post-Plan-Phase Codex Audit` HARD RULE — codex updates ride in the same logical unit as the archive
   commit, not "later."

### Operational-step verification recipe

Operational gaps are the easiest deferral to miss because the plan body looks complete. Quick verification probes:

- **VM-launched-and-finished**: `gcloud compute instances list --filter="name~<prefix>" --format="value(status)"` (look
  for absence) AND `gcloud storage ls gs://${PID}-events/events/<service>/<YYYY-MM-DD>/<vm-name>/` (look for STARTED +
  STOPPED events with non-empty progress between them).
- **Backfill ran to completion**: read the manifest at the expected coverage horizon — `captured` rows per
  `(asset_group, venue, data_type, day)` matching the planned scope. Counting rows is not validation; populating rows
  is. Probe a sample parquet to confirm it's not 1440-NaN placeholders (per `Honest absence vs fake placeholders`).
- **Migration ran**: post-migration manifest / on-disk schema matches the new shape; ZERO rows in legacy shape; reader
  fallback paths deleted. Migration scripts that say "run me once" (e.g.
  `instruments-service/scripts/migrate_local_sfi_to_canonical.py`) need explicit operator confirmation they ran on
  production buckets, not just locally.
- **Deploy promoted**: `gcloud run services describe <service>` revision matches the latest commit on `main` (or
  whichever branch the plan declared as the deploy source).

If ANY probe shows the operation didn't run, the plan is NOT done — even if every code commit landed. Either run the
operation now (and flip the checkbox + cite the operation evidence) or migrate the operational step to an active plan
per step 3.

### Why this matters

- **Operator-time-to-recall is expensive.** When the operator asks "what about X — I thought we had X scoped somewhere,"
  reconstructing the answer from grep + git log + chat history takes 30+ minutes per incident. Pre-archival migration is
  a 5-minute discipline that saves the 30-minute recall every time.
- **Code-shipped vs operationally-shipped is the silent failure mode.** Plans that say "done" without verifying the
  actual operation ran erode workspace trust in plan checkboxes. Once a few plans are caught with code-shipped-but-not-
  operationally-shipped state, every subsequent plan checkbox becomes suspect to the next reader.
- **Archive is forever.** Once a plan moves to `plans/archive/<slug>.plan.md` and `locked_by` clears, the deferred work
  is invisible to active scanning (`grep DEFERRED plans/active/*.md` won't find it). The archive is the archaeology
  layer; active is the search layer. Migrate deferred items BEFORE the archive boundary so they stay in the search
  layer.
- **Citadel-grade discipline.** Per `Citadel-Grade Planning Standards § 3 No Technical Debt` — every plan must close
  cleanly without leaving phantom work. Half-archived plans with surviving deferrals are technical debt in the planning
  layer.

### Anti-patterns

- **Archive-and-hope.** Plan archives, deferrals get dropped because "we'll remember." We won't. Operator asks 3 weeks
  later, time is wasted.
- **Defer-without-naming.** A plan body says "post-cutover" without a specific successor plan filename. The
  `Temporary state must have a named successor plan` rule already prohibits this for temporary states; this rule extends
  it to every deferral type at archive time.
- **Operational-rubber-stamp.** Marking an operation done because the code shipped, without checking the operation
  actually ran. Especially common for "ran the migration" / "kicked off the backfill" / "deployed to prod" — the
  verification probe takes <30s and catches multi-day silent failures.
- **Issue-doc graveyard.** Writing every deferral as an `issues/` doc instead of folding into a real plan. Issue docs
  are for unowned-yet items needing triage; they MUST resolve to a plan within 7 days. >7 days = the issue doc itself is
  a deferred item that should have been migrated.
- **Bulk-migrate-to-one-plan.** Dumping 15 unrelated deferrals into the same convenient destination plan because it's
  easy. Each deferral goes to the plan whose scope owns it; no convenience-bucket plans.

### Composes with

- `Plan Locking` (above) — `locked_by` removal is the technical gate for archival; this rule is the content gate.
- `Temporary state must have a named successor plan` — same shape, at-archive-time extension.
- `Commit + Push + Flip Plan Checkboxes As You Ship Each Item` — half-shipped items get `**DEFERRED**:` annotations
  during the plan's lifetime; this rule ensures those annotations migrate to an active home at archival.
- `Findings Triage Discipline` — issue-doc disposition (case 5 of the matrix) is the same shape as case (c) here.
- `Capture discoveries as plan todos immediately` — discoveries during a plan's lifetime get captured in real-time; this
  rule ensures none are lost when the plan closes.
- `Post-Plan-Phase Codex Audit` — codex updates at every phase boundary; this rule extends to the archive boundary for
  any deferred items affecting a workspace contract.
- `Citadel-Grade Planning Standards § 3 No Technical Debt` + `§ 7 Single Source of Truth` — archived plans with
  surviving deferrals are debt; the migration discipline closes the loop.

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
`unified-trading-pm/codex/14-customer-journeys/authentication/firebase-local.md`.

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

## Plan Filename Convention + 3-Layer Model (codified 2026-05-08)

| Directory                     | Extension        | Why                                                                                            |
| ----------------------------- | ---------------- | ---------------------------------------------------------------------------------------------- |
| `plans/active/`               | `<slug>.md`      | Native markdown preview in Cursor / VS Code / GitHub web UI                                    |
| `plans/epics/` (masters)      | `<slug>.md`      | Granular asset_group / domain umbrellas                                                        |
| `plans/epics/` (May-23 epics) | `<slug>.epic.md` | Domain-target wrappers for May-23 cutover                                                      |
| `plans/archive/`              | `<slug>.plan.md` | Frozen historical state — DO NOT rename, breaks archaeology in commit messages + external refs |
| `plans/ai/`                   | `<slug>.plan.md` | AI-generated staging dir; promotion to `active/` renames to `.md`                              |

**Rule.** New plans land in `plans/active/<slug>.md` (or `plans/epics/<slug>.md` for granular masters / `<slug>.epic.md`
for May-23 epics). Reviewers reject `.plan.md` filenames in `plans/active/` or `plans/epics/`. The 2026-05-08 sweep
(commits `aa72177d` rename + `cca954ff` cross-ref rewrite) is the codifying boundary.

**3-Layer plan model:**

```
master_to_live_defi_2026_05_23.md   ← umbrella-of-epics (May-23 cutover master, lives in active/)
        │
        ├── plans/epics/*.epic.md   ← May-23 deadline epics (domain-target wrappers)
        │       │
        │       └─ each references ↓
        │
        └── plans/epics/*.md        ← granular masters (asset_group umbrellas: cefi/tradfi/sports/predictions/etc.)
                │
                └─ each references ↓
        │
        └── plans/active/*.md       ← granular sub-plans (one workstream each)
                │
                └─ each references codex/, code, scripts/
```

- **Epics** orchestrate domain targets for May 23; consume granular masters + sub-plans. Read-mostly: writes only to
  consumed-plans table or end-state criteria.
- **Masters** are asset_group / domain umbrellas; consume sub-plans.
- **Sub-plans** own todos for a single workstream.
- None of the layers duplicates content — each adds orchestration above the layer below.

See [`plans/epics/README.md`](../plans/epics/README.md) and [`plans/PLAN_FORMAT.md`](../plans/PLAN_FORMAT.md) for the
canonical structure.

## Capture Discoveries As Plan Todos Immediately (HARD RULE codified 2026-05-07; EOD-audit clause added 2026-05-08)

Every side-discovery during plan execution — a bug in adjacent code, an edge case the plan missed, a refactor that
compounds value, a nice-to-have, a deferred follow-up, a doc update, "we should also fix X" — MUST go into a plan todo
at the moment it surfaces. Same logical unit as the discovery: finding → next 1-2 tool-calls is plan-edit + commit +
push. Tag P0-P3 + `**DEFERRED**` / `**NICE-TO-HAVE**` / `**DEFERRED-PER-USER**` body prefix + provenance citation.

Goes in: same plan if scope-aligned, different active plan if more apt, `plans/active/issues/<slug>_<YYYY_MM_DD>.md` if
no plan owns it yet. **Never just auto-memory. Never just chat summary.** Why: Claude Code sessions crash regularly
(terminal OOM / sandbox kill / context fill); pre-crash capture survives. The plan should always reflect the ideal final
solution shape so the operator keeps less in head + future agents inherit the full picture.

### End-of-cycle audit clause (added 2026-05-08 after Tab 5 EOD-summary regression)

The mid-execution rule above is necessary but not sufficient. End-of-cycle / DONE-block summaries are themselves a new
surface where deferrals leak: the agent writes a "Deferred to next cycle" section in chat or in the DONE block, the
items sound captured, but they're not `- [ ]` plan todos anywhere — so the next agent never sees them.

**Before declaring a cycle done — the moment you start writing your end-of-cycle chat summary or DONE block — every
deferral you list MUST already be a `- [ ]` plan todo (or a
`**DEFERRED**`annotation on an existing todo) in`plans/active/`.** If you catch yourself listing an item in the summary
that isn't a plan todo, STOP, add it as a plan todo (per the routing above), commit + push the plan-flip, THEN write the
summary citing the todo's location.

Audit recipe at end-of-cycle:

1. Draft the "Deferred to next cycle" / "Pending next session" / "Carryover" section of your chat summary or DONE block
   in scratch first.
2. For each line item, run: `grep -n "<distinctive phrase>" plans/active/*.md plans/active/issues/*.md`. Match → cite
   the file:line in the summary. No match → STOP, add the todo, then resume.
3. If the item lives only in chat (no plan, no issue doc), the rule fired and you violated it — fix BEFORE shipping the
   summary.

**Reviewers reject summaries with deferrals that grep-miss the active plans.** End-of-cycle is the single most common
loss-of-work surface (operator reads the summary, trusts the deferrals are captured, next-cycle reset doesn't pick them
up because they're not plan todos, three weeks later operator asks "what about X" and the answer is
reconstruction-from-chat).

Reference incident **2026-05-08 Tab 5 (Agent 5)**: end-of-cycle summary listed 4 deferrals — Phase 4/7/8/9, features-
onchain emission sites, Sub-E codex ML category, Phase 8 rehearsal-script hook. Of the 4, 3 WERE already plan todos (I
missed them by not grep-checking my own summary), 1 was NOT (Sub-E codex ML category — false-flipped `[x]` on the parent
todo while Sub-E's actual codex doc was reverted by foot-gun #3 5+ times). Operator caught the gap with "are those in
the plans" + "so that we know what to pick up." Cost: 15min audit + plan-todo addition. Avoidable cost: 30s grep at
end-of-cycle.

### Anti-patterns

- **"I'll mention it in chat — operator will catch it."** Chat scrolls. Operator-time-to-recall is expensive. Capture in
  a plan todo + reference the todo in chat.
- **"Auto-memory will save it."** Auto-memory is a recall surface for ME, not a planning surface for the next agent
  - the operator. Auto-memory entries don't become plan todos automatically; a plan-todo entry does become both.
- **False checkbox flips.** A parent todo flipped `[x]` because "the UAC half shipped" is wrong if the codex half was
  reverted. Flip the half that landed; leave the deferred half as `- [ ]` with `**DEFERRED**` annotation + reason
  citation. Reference: line 155 of `alerting_service_live_rules_2026_05_07.md` — corrected 2026-05-08 from false `[x]`
  (claimed codex update shipped) to split shape (UAC `[x]` + codex `[ ]` with foot-gun #3 citation).
- **End-of-cycle summary as planning surface.** Summary is a read-only narration of the cycle, not the durable record.
  Plan todos are the durable record.

### Composes with

- `Commit + Push + Flip Plan Checkboxes` (per-shippable-unit cadence — captures discoveries land WITH the work)
- `Plan Archival HARD RULE` (extends to archive boundary; this rule extends to EOD boundary)
- `Findings Triage Discipline` (case 1-5 routing for the discovery itself)
- `Cross-Plan Coordination Banners` (when a discovery affects an in-flight VM / refactor)
- `Plans Run To Actual Completion` (the operational-step verification recipe is a sister rule for "looks done but
  isn't"; this rule is for "documented as deferred but not actually captured")

## Commit + Push + Flip Plan Checkboxes As You Ship Each Item (HARD RULE)

This rule has TWO mutually-reinforcing halves. Both are non-negotiable. Violating either breaks parallel-agent
coordination and loses work.

### Half 1 — Commit + push at every shippable unit

A "shippable unit" is the smallest meaningful slice of work that QGs cleanly on its own — a helper + its tests, one
adapter migration, one reconciler, one consumer wire-in. **The moment a shippable unit is green, commit + push.** Do not
batch shippable units across a session waiting for a "natural pause."

- **Pushed = real.** A local-only commit is invisible to every other agent + every CI gate + every running VM that pulls
  from `live-defi-rollout`. Until you `git push`, your work doesn't exist as far as the rest of the workspace is
  concerned.
- **The cadence is per-shippable-unit, not per-hour or per-session.** Five shippable units in one session = five
  commit+push cycles, not one. Each cycle is small enough to revert cleanly if a downstream agent flags a regression
  half an hour later.
- **No "I'll commit after the next thing."** That's how 2-hour-old uncommitted work gets clobbered by a quickmerge
  stash, an auto-formatter pass, or another agent's `git add <file>` accidentally hoovering up your unstaged hunks
  (reference incident: PM@961980db — a teammate's local-uncommitted audit section got bundled into another agent's
  plan-flip commit because the second agent staged the whole file instead of `git add -p`-ing their own hunks).
- **End-of-session commits are a smell.** If you find yourself with 4 hours of uncommitted work as you're writing the
  handoff, the rule was already violated.
- **`live-defi-rollout` is the working branch.** VMs pull from it; CI runs against it. Push directly per the workspace
  dirty-deps rule (`git add <my-files> && git commit --no-verify && git push origin live-defi-rollout`) rather than
  waiting for a quickmerge → main promotion cycle.

### The mandatory pre-commit check (catches accidental bundling)

> **Under per-slot worktrees (2026-05-10):** cross-slot foot-guns #1–#3 are unrepresentable by construction — each slot
> has its own `.git/index`. **Within a slot**, sub-agents share the index, so the discipline below remains MANDATORY for
> any multi-sub-agent fan-out. Foot-gun #4 (prek auto-restore) is mitigated via per-slot `PREK_CACHE_DIR` but the
> bundled Edit→add→commit→push pattern below remains the right default. See
> [`codex/05-infrastructure/per-tab-worktrees.md`](../codex/05-infrastructure/per-tab-worktrees.md).

Before EVERY `git commit` in any repo where another agent might have staged or modified files in parallel, run:

```bash
git status                 # full picture: modified, staged, untracked
git diff --cached --stat   # NO PATH ARGUMENT — see the entire index
```

If anything is in the staged set or working tree that isn't yours, surgically un-stage it
(`git restore --staged <file>`) or `git stash --keep-index` the unrelated stuff before committing. **Never pass a
`<path>` argument to `git diff --cached --stat`** — that filters the output to just that path and masks other staged
hunks.

Reference incidents (all 2026-05-07 PM repo, all from concurrent-agent overlap):

- PM@961980db — bundled a teammate's local-uncommitted "Audit 2026-05-07" plan section because `git add <plan-file>`
  picked up the whole current file state, including their unstaged hunks.
- PM@611b9501 — bundled a teammate's `git mv` (plan promotion ai/→active/) because the agent only checked
  `git diff --cached --stat <single-path>` and missed the rename already sitting in the index. **The very commit that
  codified this rule was an instance of the foot-gun the rule warns about.** That's how easy it is to fall into; do the
  full-status check.
- PM@34075d84 (later reset to PM@7de75819, this session's mirror-image incident) — a parallel-agent's auto-commit swept
  up another agent's already-staged `git mv` renames into ITS commit, then the parallel agent reset its own commit and
  re-committed (7de75819) without those renames. Net: the original agent's staged work was **silently wiped from the
  index** without their `git mv` ever errroring, and they had to re-stage everything from disk. This is the inverse
  failure of #1+#2: those bundled foreign work IN; this one let foreign reset take work OUT. **Lesson:** if `git status`
  says "ahead by 1 commit" mid-session and you didn't make that commit, a concurrent agent has been moving HEAD — check
  `git log origin/<branch>..HEAD` before any further git operation. After every `git mv` / `git rm` / `git add`, before
  `git commit`, run `git diff --cached --name-status` to verify YOUR entries are still in the index. A parallel reset
  can erase staged renames without surfacing any error. Recovery is straightforward (re-stage from disk) but only if you
  notice — silent loss is the trap.

### Foot-gun #4 — auto-revert hook racing your edits (codified 2026-05-08)

A fourth, related failure mode hit during the 2026-05-08 work-split hardening session: the **prek pre-commit hook**
(plus concurrent agents on the shared working tree) was **restoring the working tree from
`/Users/.../.cache/prek/patches/<patch>.patch` between an `Edit` succeeding and the next `git add`/`git commit`
running** — silently wiping the just-edited content before it could be staged. The repeated message
`"Restored working tree changes from /Users/.../.cache/prek/patches/...patch"` in commit output is the diagnostic
signal: prek backs up the working tree before formatters run, and on hook failure (or some concurrent triggers) it
restores from that patch, undoing your in-flight edit.

Symptoms (any one is enough to confirm the failure mode):

- You ran `Edit`/`Write`, the tool reported success, but the next `git status` shows the file as unmodified.
- You committed, but `git show --stat HEAD` shows zero insertions to YOUR file (only foreign files in the commit) — even
  though you just edited it and your commit message describes that file.
- `git log --oneline -3` shows commits attributed to `semver-rollout[bot]` or another agent's identity that contain YOUR
  commit message but missing YOUR content.
- You see `"Restored working tree changes from .../prek/patches/"` in any commit/git output.

**The workaround (codified):**

1. **Tighten the Edit → stage → commit → push window.** The race is between the Edit completing and `git add` running.
   Every separate Bash call is a window. Pack them into ONE Bash command:

   ```bash
   git add <specific-file> \
     && git diff --cached --name-status \
     && git commit --no-verify -m "..." \
     && git push origin <branch> --no-verify
   ```

   No intermediate Bash calls (no `git status` / `git log` / `ls` between Edit and add). The whole sequence runs in a
   single shell process, faster than the hook's restore window.

2. **`--no-verify` IS authorized in this case** despite the workspace rule "Never skip hooks unless user explicitly
   requests." The condition is: (a) you have observed the auto-restore symptoms above wiping at least one of your edits
   in this session, AND (b) the alternative is losing real work. Per 2026-05-08 user direction _"fix to keep your work"_
   — that's the explicit authorization for this failure mode going forward; do NOT re-ask each session.

3. **Verify post-push with `git show --stat HEAD`.** If the commit landed but shows zero insertions to your file
   (foot-gun #1 + #4 combined: revert raced you, then a foreign-work-only commit went through under your message),
   re-Edit and retry. Don't assume the commit succeeded just because `git push` returned `0`.

4. **Stage explicitly by name, never `git add .` / `git add -A`.** Composes with the foot-gun #1 / #2 mitigations above
   — the auto-revert race amplifies foreign-bundling risk because the moment your file gets reverted, anything ELSE
   staged in the index (foreign agent's WIP) is what your commit will contain.

5. **If your file was repeatedly reverted across multiple Edit attempts**, the prek patch under `~/.cache/prek/patches/`
   is the likely restore source. The fix is to commit immediately after the first successful Edit, before prek's next
   patch cycle. There is currently no workspace-wide setting to disable prek's restore behaviour — the tighter Edit →
   commit window is the only mitigation.

**Anti-patterns:**

- **Don't** assume a successful Edit tool result means the file is on disk by the time you commit. Two seconds is enough
  for a restore to fire.
- **Don't** run `git status` / verification commands between Edit and commit "just to be safe" — every extra command
  widens the race window.
- **Don't** retry the same Edit + commit sequence five times hoping it sticks. Diagnose, then bundle Edit-adjacent ops
  into one Bash call.
- **Don't** silently use `--no-verify` outside this failure mode. It bypasses real safety hooks (lint, secret-scan,
  conventional-commits) when used routinely — the authorization is scoped to "auto-restore is observed wiping work."

Reference incidents (2026-05-08 work-split hardening session, this commit's preceding work):

- 8 commits' worth of plan-edit + isolation-table content lost across `~5` revert cycles before the bundled
  Edit→add→commit→push pattern was identified. Recovered by re-Editing + tight bundling. ~30 min lost.
- One commit (`b61824d8`) landed under `semver-rollout[bot]` with my commit message but ZERO insertions to my target
  file — only foreign files committed under my message. Diagnosed via `git show --stat HEAD` showing the mismatch.

### Half 2 — Flip the plan checkbox in the same logical unit

When working through a plan, you MUST flip the `- [ ]` checkbox to `- [x]` for each todo **as soon as the underlying
work is shipped (committed + pushed)** — not at the end of the session, not "after the next agent picks it up", not
batched into a single sweep at handoff time. The flip happens in the same logical unit of work as the code commit:

1. Ship the code commit (or commits) that complete the todo. **Push it.**
2. Edit the plan file: `- [ ] [SCRIPT] P0. Description...` →
   `- [x] [SCRIPT] P0. Description... (commit-sha + brief evidence)`.
3. Commit the plan flip in the PM repo with a `docs(plans):` prefix referencing the work commits. **Push it.**
4. Only then move to the next todo.

**Don't flip a checkbox unless the work is actually shipped.** Pushed commits count; local commits do NOT. If the work
is half-done (e.g. helper shipped but consumer wiring deferred), flip only the half that landed and append a
`**DEFERRED**:` note to the unshipped half explaining why.

**Every item your session touched but did NOT ship gets the same treatment**, not just half-shipped items. If your
session attempted Phase 3 + Phase 4 + Phase 11 but they never landed (sub-agent failed, blocker surfaced, scope didn't
fit, etc.), each of those items must have a body annotation explaining the blocker + successor — NOT a bare `- [ ]`
checkbox with empty `note:`. A bare unticked item is indistinguishable from "no agent has looked at this yet"; an
annotated unticked item says "agent X attempted, blocker Y, picks up at Z." The next agent needs that distinction to
avoid duplicating wasted effort. The annotation shape:

```yaml
- [ ] [AGENT] P0. Phase N — <description>.
      ...
status: blocked        # or "deferred-after-<successor>" / "design-shipped" / "helper-shipped"
note: "<YYYY-MM-DD> <agent-tag> attempted; blocker = <reason>; successor = <plan + phase>; resumes when <gate>."
```

Use `status:` values from the closed set: `todo` (unstarted, no agent has looked) / `done` / `design-shipped` (design
contract landed, wiring open) / `helper-shipped` (primitive landed, consumer wiring open) / `blocked` (attempted, gate
unmet) / `deferred-after-<successor>` (intentionally deferred behind a named gate).

**The flip belongs in a separate commit** in the PM repo (or bundled with other doc-only PM changes), with the canonical
message shape:

```
docs(plans): <plan-name> Phase <N>.<Tier> — <one-line summary of what shipped>

* <repo>@<sha> — <one-line>
* <repo>@<sha> — <one-line>
* ... (cite every code commit the flips reference)

Plan: <plan-filename>.
```

**Why `docs(plans):` and not `plan(<name>):`** — the conventional-commits pre-commit hook (rolled out 2026-05 across
every repo) only accepts the standard type set:
`build / chore / ci / docs / feat / fix / perf / refactor / revert / style / test`. `plan(...)` is rejected and the only
ways past it are `--no-verify` (banned per workspace rule "Never skip hooks") or `[QG-BYPASS: ...]` tags. `docs(plans):`
is conventional-commits-clean, semantically accurate (the plan file IS a doc), and matches existing PM precedent
(PM@e3457a08, PM@0e2eb08e, etc.). Codified 2026-05-08 after the PM@0e2eb08e Wave 4 flip surfaced the SSOT-vs-hook drift.

### Half 3 — Session-end deferred-work scoreboard (HARD RULE codified 2026-05-08)

When a single session touches **multiple items** in one plan AND ends with any of those items in non-final state
(blocked, deferred, half-shipped, design-only, helper-only), the plan body MUST contain a **single-place scoreboard**
listing every touched item's status + successor + blocker before the session ends. Per-item `**DEFERRED**:` annotations
are necessary but NOT sufficient — a future agent should NOT have to scan every checkbox in a 1000-line plan to know
what's pending.

**The scoreboard goes in the plan body** as a `## Deferred work after <YYYY-MM-DD> <session-tag> session` section,
positioned just before `## Temporary states + their canonical follow-up plans` (or wherever follow-up sections live in
the specific plan). Standard shape:

```markdown
## Deferred work after <YYYY-MM-DD> <session-tag> session

The <YYYY-MM-DD> <session-tag> session shipped <one-line summary>. Items still open are tracked here so the next agent
picks up cleanly without re-reading session notes.

| Phase / item     | Status as of <YYYY-MM-DD>  | Successor / blocker                                        |
| ---------------- | -------------------------- | ---------------------------------------------------------- |
| Phase 3 — <name> | `todo` (checkbox `- [ ]`)  | DEFERRED-AFTER-<gate-plan> Phase <N> completing            |
| Phase 8 — <name> | `done` (UTL@<sha> shipped) | Per-service consumer wire-in ships with Phase X/Y rollouts |
| Phase 9 — <name> | `design-shipped`           | DEFERRED-TO-<other-tab> — design contract in <codex doc>   |
| ...              |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **<topic>**: <one-line>; open in [`<other-plan>.md`](<other-plan>.md) Phase <N>.
- ...
```

**The rule fires at every session-end, every handoff, every "user is wrapping up" boundary** — not just plan archival.
The scoreboard is a forward-index for the next agent + a cheap read for the operator deciding what to fund next.
Pre-existing scoreboard from a prior session: extend the existing table (don't add a parallel one); the session-tag
header stays the same OR add a new `## Deferred work after <next-date> <session-tag>` section if the prior section was
already migrated to closed.

**Belt-and-braces with Half 2.** Half 2's per-item `**DEFERRED**:` annotations remain mandatory (the per-item view).
Half 3 adds the per-plan scoreboard view (the cross-item index). Both ship in the same logical unit as the session-end
commit — NOT a separate "I'll add the scoreboard later" task. If the scoreboard isn't in the plan body, the session
isn't over.

**When NOT to ship a scoreboard.** Trivial sessions that touch one item + ship it cleanly don't need a scoreboard — Half
2's per-item flip is sufficient. Heuristic: if your session updated 3+ phase statuses OR left 2+ items in non-final
state, ship the scoreboard.

### Why all three halves are non-negotiable

- The plan is the operator's read-only view of "what's left." If checkboxes lag the actual state, the operator can't
  trust them, and parallel agents re-do work that's already shipped.
- Two agents reading the same plan must see the same in-flight state. Stale checkboxes cause work-stealing collisions
  (two agents implementing the same item in parallel).
- "I'll commit + flip everything at the end" routinely loses items. Someone gets summoned mid-session, context fills up,
  the auto-formatter clobbers an unstaged file, the flip never happens, and the next agent reads the plan as if nothing
  was done.
- Per-shippable-unit pushes are the ONLY way the workspace's parallel-agent + per-VM-pull-from-`live-defi-rollout`
  - manifest-concurrency-protocol model works. A 4-hour uncommitted block is invisible to everything else and blocks no
    work but yours.

This applies to every plan in `plans/active/` and every working session — tier completions, partial flips inside a tier,
even single-item flips when that's all the session shipped. Reviewers reject sessions that ship code without the
matching plan flip, and reject sessions that have stale uncommitted work older than a single shippable unit.

## Post-Plan-Phase Codex Audit (HARD RULE codified 2026-05-08)

After every major plan-phase completion (a phase/tier landing as fully done — every checkbox in that phase flipped to
`- [x]`), run a **codex audit pass**: walk every codex doc the plan touches or _should have_ touched, verify the doc
reflects the new SSOT the plan established, and update or write the doc as part of the same logical unit. The plan's
"Codex SSOT updates" phase (typically the second-to-last phase) is the FORMAL codification of this rule — but the audit
happens at every major-phase boundary, not only at plan-end, so codex doesn't drift mid-plan.

### What the audit covers

For each major plan phase, ask three questions:

1. **Did this phase change a contract / shape / pattern that's described somewhere in codex?** If yes, find the doc(s)
   and update them. Examples: new UAC enum, new manifest column, new event type, new helper class, new architectural
   pattern, new shard atom dimension, new SSOT for any cross-cutting concern.
2. **Did this phase establish a new pattern that's NOT yet described in codex but should be?** If yes, write the new doc
   as a stub (entry-point + key principles + cross-references back to the plan), folding it into a later plan phase for
   full content. The stub IS part of the plan-phase deliverable.
3. **Did this phase invalidate an existing codex doc** (e.g. by changing the recommended approach, deprecating a
   pattern, replacing a workspace-wide rule)? If yes, update the doc to reflect the new state in the same commit, OR add
   a banner on the doc with `> **SUPERSEDED 2026-05-XX by <plan-name> Phase N — see <new-doc>**`.

### When to do it

- **At every major plan-phase boundary** (not just plan completion). A 5-phase plan does the audit 5 times, once per
  phase boundary. This prevents codex from drifting against the plan mid-execution.
- **Within the same logical unit as the phase-completion commit batch.** Plan flip + code commits + codex updates ride
  together in the same shippable unit per the Commit+Push+Flip rule.
- **Before the plan unlocks for archive.** Final unlock check: every codex doc the plan touched or should have touched
  is consistent with the shipped state.

### Stub vs full content

A codex doc stub is a legitimate intermediate state — entry-point with TL;DR, key principles, anti-patterns, and
cross-references back to the plan. Stubs SHIP at plan-mid (they document the design + signpost where the full content
will land). Full content is enhanced + promoted as the corresponding plan phase ships its work.

The codex doc paths the plan creates / enhances MUST be enumerated as explicit todos in the plan's "Codex SSOT updates"
phase. Plans that omit codex doc updates from their phase list are review-blocking — every plan that lands a contract /
pattern / architectural change MUST list the codex docs it touches.

### Why

Per CLAUDE.md "Master Plan — Live DeFi Trading" principle: **docs are the intent.** If codex describes the system as it
WAS before the plan landed, the workspace's "doc → plan → code" discipline is broken — agents reading the doc will write
code against the wrong contract. Even one stale doc creates collision risk in the parallel-agent workflow. The
audit-at-every-phase-boundary discipline keeps the doc layer ahead of (or at parity with) the code.

### Concrete pattern (the 2026-05-08 live-pipeline activation as reference)

The live-pipeline activation (3 plans + 4 codex docs landed 2026-05-08) follows this pattern:

- `live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 14 lists 8 codex docs (3 NEW + 5 UPDATE).
- `gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 7 lists 6 codex docs (1 NEW + 5 UPDATE).
- `features_repo_consolidation_2026_05_08.md` Phase 9 lists 6 codex docs (1 NEW + 5 UPDATE).
- All 4 NEW docs were stubbed at plan-creation time (codex/05-infrastructure/live-pipeline-architecture.md +
  replay-subsystem.md + codex/02-data/pipeline-mode-partition.md +
  codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md) so the design is captured upfront.
- Each plan phase that changes a contract or pattern triggers the relevant codex update before the phase commits flip to
  `- [x]`.

### Anti-patterns

- **Don't defer codex updates to plan-end.** Mid-plan agents reading a stale doc write incorrect code. Audit at every
  phase boundary.
- **Don't write codex docs without a plan reference.** Every NEW doc points back to the plan that owns it, so
  future-readers can find the work-context.
- **Don't update codex without flipping the plan checkbox.** The codex update IS part of the phase deliverable; if it's
  done, the checkbox flips.
- **Don't add a "we'll write the codex later" placeholder.** If the work is done but the doc isn't, the phase is not
  done — keep the checkbox at `- [ ]`.
- **Don't bypass the audit because "the plan didn't list a codex doc."** If the work changed a contract/pattern, the
  codex doc updates are in scope regardless of whether the plan listed them. Add the missing item to the plan + ship the
  doc + flip both as part of the same logical unit.

### Composes with

- `Capture discoveries as plan todos immediately` — codex gaps discovered mid-plan get captured as plan todos.
- `Plans must capture full codebase impact upfront` — codex docs touched by a plan MUST be enumerated in the plan body;
  not "deferred to later."
- `Cross-Plan Coordination Banners` — codex doc touchpoints often span multiple plans; banner them mutually.
- `Commit + Push + Flip Plan Checkboxes` — codex updates ship in the same logical unit as the code commits
  - plan flip.

## CI Verification After Every Push (HARD RULE)

Every `git push` to a branch that **triggers remote CI** MUST be verified — the repo's CI bot reports pass/fail to
Telegram. Verification is non-negotiable when CI runs; it's how we catch platform-specific failures (Python version
drift, missing deps in CI image, network-blocked tests, etc.) before they rot the workspace.

### Which pushes trigger CI (per current workflow trigger config)

Per `.github/workflows/quality-gates.yml` and the existing branch policy ("feat/\* → QG only, no PR. staging →
convergence. main → always stable"):

- **Pushes to `main`** → trigger Quality Gates + downstream workflows. **Always verify.**
- **Pull requests targeting `main`** → trigger Quality Gates on the PR head. **Verify on PR open + each new commit.**
- **Pushes to `live-defi-rollout` and other `feat/*` feature branches** → **DO NOT trigger remote CI**. Quality is
  enforced **locally** via `bash scripts/quality-gates.sh` before push, per the per-shippable-unit commit cadence in the
  rule above.

For feature-branch pushes the watcher's job is lighter: confirm the push landed on origin
(`git rev-list --left-right --count HEAD...origin/<branch>` returns `0 0`) and stop. No CI run to wait for; no failure
to diagnose. The merge-to-main step (via `quickmerge`'s eventual promotion or a manual `staging` PR) is when the full CI
gate fires — watcher discipline kicks in fully at that step.

If the workflow trigger config changes (e.g. CI starts firing on `live-defi-rollout` pushes), this section + the
workflow yaml become the joint SSOT — update both in lockstep so the rule stays accurate.

### The discipline

1. **Push.** If pushing to a CI-triggering branch (`main` direct, or PR commits to `main`), CI runs. If pushing to
   `live-defi-rollout` or other `feat/*`, CI does NOT run — confirm the push landed on origin
   (`git rev-list --left-right --count HEAD...origin/<branch>` returns `0 0`) and stop here.
2. **Set up a background CI watcher** (only when CI runs, per step 1) — spin up a sub-agent OR set a `ScheduleWakeup`
   timer for ~3-5 min after push to check `gh run list --branch <branch> --repo <owner>/<repo> --limit 5` (or
   equivalent) for the latest run's status. While the watcher runs, you proceed with other work — no blocking.
3. **On CI pass**: nothing more required.
4. **On CI fail**:
   - **Diagnose via remote logs first** — `gh run view <run-id> --log-failed --repo <owner>/<repo>`. The failure reason
     lives on the remote, not in your local working tree.
   - **Fix the root cause** in your code (or revert if your change is the cause and you can't fix immediately).
   - **Run quality-gates locally if needed** to verify the fix — but only on the specific files YOU edited (per the
     "only commit our own work" rule below). Avoid running QG over the whole repo if other agents have dirty files in
     the working tree, since their dirties will pollute the QG signal.
   - **Push again.** The CI watcher restarts.
5. **CI failures are NOT issues to flag** — they're things to fix in real time. No issue doc, no plan annotation, no
   "I'll get to it later." A red CI on `live-defi-rollout` blocks the workspace; fix immediately.
6. **The CI bot reports the underlying repo's status, not its own delivery result.** `ci-status-update.yml` derives the
   Telegram severity + conclusion from `client_payload.status`: `FAILING` → ❌ `Conclusion: failure` + `CRITICAL`
   severity; everything else (`FEATURE_GREEN` / `STAGING_GREEN` / `LOCAL_PASS` / `SIT_VALIDATED`) → ✅
   `Conclusion: success` + `INFO`. If the manifest-update job itself fails, the notification also flips to ❌ so a
   degraded write never shows a green tick. (Pre-2026-05-08 the bot rendered ✅ for every successful manifest write
   regardless of the underlying repo CI state — fixed in `.github/workflows/ci-status-update.yml`.)
7. **FAILING messages include a failure excerpt inline.** `python-quality-gates.yml` and `ui-quality-gates.yml` tee QG
   stdout+stderr to `/tmp/qg_output.log`, capture the last 30 lines (ANSI-stripped, ~1500 char cap), base64-encode and
   forward via `client_payload.failure_excerpt_b64`. `ci-status-update.yml`'s `build-message` job decodes +
   HTML-escapes + appends inside a `<pre>` block under a `Failure excerpt:` heading. Operators see the actual error
   (failing test name, lint rule, basedpyright type error) in the Telegram message body without clicking through to the
   run logs. Excerpt only renders when `STATUS=FAILING`; greens never carry it.

### The pre-requisite: only commit YOUR work

This whole protocol depends on a clean signal — when CI fails, it must be reasonable to assume the failure is from YOUR
commit, not from another agent's dirty files that got bundled into the staging set. Hence:

- **Stage files explicitly by name** (`git add <file1> <file2>`) — never `git add .` or `git add -A`. Implements the
  existing pre-commit-check rule but extends it: even if the dirty files would QG-pass, they're not yours and shouldn't
  ride your commit.
- **Never delete other agents' work from the local copy.** No `git reset --hard origin/<branch>`, no
  `git checkout origin/<branch> -- .`, no mass-revert. Their unstaged + uncommitted work is their in-flight session;
  stomping it loses real work and damages workspace trust.
- **If you must stash to keep your staged set clean**:
  `git stash push --keep-index -m "<other-agent>'s WIP staged-only commit"` before commit, `git stash pop` immediately
  after. Other agents may want to commit their own work seconds after yours; leaving their hunks stashed for hours
  blocks them.
- **Local QG isn't the source of truth.** Remote CI on `live-defi-rollout` is. Local QG is a dev-time sanity check;
  remote is the gate. Don't chase a green local QG by running on dirty trees that include foreign work — chase a green
  remote CI on a commit that contains only YOUR files.

### Why this matters

- **Live = batch principle for CI**: every commit needs the same remote validation. Local-only verification skips the CI
  safety net that catches platform-specific failures (Python version drift, missing deps in CI image, network- blocked
  tests, etc.).
- **VMs pull from `live-defi-rollout`**: a red CI on the branch can mean VMs that bounce mid-run pull broken code.
  Catching CI failures in real-time prevents this.
- **Parallel-agent regression detection**: if your push went green and a parallel agent's push immediately after went
  red, the failure is theirs. Your CI watcher gives you the timestamp + signal to know it's not yours — no re-debugging
  your own commit.
- **Trust + workflow**: workspace runs on the assumption that `live-defi-rollout` passes CI. Repeatedly pushing red
  commits and "I'll fix later" rots that assumption — every other agent's diagnostics get poisoned by foreign red CI.

### What this is NOT

- **Not a skill** — don't add a `/ci-watch` slash-command. The watcher is a sub-agent invocation OR a `ScheduleWakeup`
  invocation, set up inline as part of the push step. Skill-ification adds ceremony for a 30-second action.
- **Not a blocking step** — you don't sit and wait for CI. Push, schedule the check, continue with other work, react
  asynchronously when the check fires. The whole point is to keep moving.
- **Not for every micro-commit** — if you push 5 commits in a 10-minute window, one watcher per push is overkill; one
  watcher set 5 min after the LAST push is sufficient. CI runs the full HEAD; older commits' results don't matter if the
  latest is green.

## Grep-Then-Read, Not Grep-Then-Conclude (HARD RULE codified 2026-05-10)

When auditing / scanning / answering "does X exist in the codebase" / "is feature Y shipped" questions: **a literal grep
with 0 hits is NEVER sufficient to conclude the feature is missing.** Many features are resolved at runtime via patterns
where the literal name does NOT appear in the source: regex-based dispatch, StrEnum value lookups, factory registries,
dynamic attribute access, plugin discovery, configuration-driven wiring. A grep-then-conclude audit will report
false-negatives that waste cycles re-auditing + dispatching agents to "fix" already-shipped work.

### Reference incident (2026-05-08 → 2026-05-10 9-agent audit closure)

Cluster 9 audit reported 4 findings as "missing" based on literal grep with 0 hits. Three of the four were already
shipped via runtime-resolved patterns:

- **defi_archetypes Stream B ARBITRAGE_PRICE_DISPERSION**: cluster reported "zero references" in
  `pnl-attribution-service`. Reality: `pnl_attribution_service/engine/archetype_aggregator.py:59` uses `_SLOT_PREFIX_RE`
  regex + `:65` `_FUNDING_RATE_DISP_MARKER` — generic routing matches at runtime; the literal string
  `"ARBITRAGE_PRICE_DISPERSION"` is never a substring in source.
- **CeFi testnet wiring**: cluster reported "no testnet-specific branch paths or env toggles found." Reality: all 5 CCXT
  adapters had `testnet: bool = False` constructor param routing to `set_sandbox_mode(True)` — present in source but the
  audit grep used `testnet` as a token and conflated config-flag location with implementation.
- **Master plan Continuous-Verification column**: cluster reported "ABSENT" + recommended building it. Reality: the
  column was shipped at PM@`1d74f617` (master plan lines 767-825); the audit's grep didn't read far enough into the file
  to see it past the 1000-line top-of-file block.
- **DART backend manual-trade endpoints**: cluster spec said "build `/api/dart/manual-trade` + `/api/dart/preview` from
  scratch." Reality: `execution-service/execution_service/api/manual_instruction_api.py` (682 lines) +
  `preview_routes.py` (320 lines) + `manual_schemas.py` + `preview_schemas.py` + `ManualOperationHandler` all already
  shipped. Build agent re-audited + cancelled the redundant scope.

Each of these wasted between ~5min (re-audit) and ~2hr (dispatched implementation agent then cancelled). Aggregate
across the 9-agent audit: ~6-10 hours of avoidable cycles. Codifying the methodology prevents recurrence.

### The discipline (mandatory for every audit / scan / "does X exist" question)

1. **Run the literal grep first** — fast filter. `grep -rn "<exact-token>" --include='*.py' <scope>`.
2. **If 0 hits OR very few hits, escalate to read** — open the candidate consumer files + adjacent factory / dispatcher
   / registry modules. Spend 2-5 minutes reading the surrounding code.
3. **Look for these runtime-resolution patterns** before concluding "missing":
   - **Regex-based dispatch**: `re.compile(...)` patterns that match by structure rather than literal name (e.g.
     `_SLOT_PREFIX_RE`, `_FUNDING_RATE_DISP_MARKER`, route patterns in FastAPI/Flask).
   - **StrEnum / Literal value lookups**: registries keyed by enum member where the literal value is referenced only as
     `EnumName.MEMBER.value` — literal grep on the string value misses these.
   - **Factory / plugin registries**: dict-keyed dispatchers (`{"venue_name": VenueClass}`); the literal venue name may
     only appear in the registry seed, not in the consumer code path.
   - **Dynamic attribute access**: `getattr(obj, name)` / `setattr` / `__getattr__` hooks — the attribute name is a
     runtime variable, not a literal.
   - **Configuration-driven wiring**: YAML / JSON / `.env` config that maps string keys to behaviour at startup; the
     literal key only appears in the config file, not in code.
   - **Re-export chains**: `from .submodule import X` followed by `__all__ = ["X"]` — consumer code may import `X` from
     the root facade, never mentioning the submodule.
4. **For each runtime-resolution candidate found, verify the actual behaviour**:
   - Read the dispatch logic + trace the runtime path for the symbol in question.
   - Grep for the dispatch pattern itself (e.g. `grep -rn "_SLOT_PREFIX_RE\|_FUNDING_RATE_DISP_MARKER"`) — usually
     surfaces the runtime wiring in 1-2 hits.
   - If the runtime path resolves the symbol correctly, the feature IS shipped — flip your conclusion from "missing" to
     "shipped via runtime-resolution at <file:line>".
5. **When uncertain, ASK rather than CONCLUDE.** A 1-line operator question ("does ARBITRAGE_PRICE_DISPERSION ship via
   regex routing in pnl-attribution?") is cheaper than dispatching an agent to re-implement already-shipped work.
6. **For master-plan-scale documents (>50KB)**: read past the executive summary. Big plans bury concrete delivery
   evidence deeper than the introductory grep window. Use `wc -l <file>` to gauge document size; for >1000-line plans,
   chunked Reads with `offset` are mandatory before claiming "not present."

### Composes with

- `Findings Triage Discipline` (below) — case-1-to-5 routing assumes the finding is real; this rule is the prerequisite
  step that verifies the finding before triage.
- `Citadel-Grade Planning § 1 Pre-Audit Before Execution` — pre-audit blast radius requires the same grep-then-read
  rigour; lit grep with 0 hits on a removed symbol does NOT mean "no consumer affected." Read the runtime-resolution
  candidates.
- `Plans must capture full codebase impact upfront` — full impact enumeration depends on this rule firing during the
  pre-audit pass.
- `AST-walk QG STEP 5.65` (`unified-trading-pm/scripts/quality_gates/check_removed_symbols.py`) — codifies the
  grep-then-read pattern as runtime enforcement for removed-symbol detection: it parses the AST + walks attribute
  accesses (not just literal substring matches) to catch the regression class this rule is designed to prevent.

### Anti-patterns (banned)

- **"Grep returned 0 hits → feature missing"** without reading neighbouring files. The 4 reference incidents above are
  all instances of this anti-pattern.
- **"Spec says build X" without verifying X doesn't already ship.** Spawn-prompts to implementation agents must include
  "verify via grep-then-read that the feature doesn't already exist" as STEP 0 before any code authoring.
- **Reading only the executive summary of a >50KB plan** then concluding work is missing. The plan body is the
  authoritative state record; the summary is just the index.
- **Re-implementing already-shipped work because the audit was misframed.** If you discover mid-implementation that the
  feature already exists, STOP, document the misframing as a finding, withdraw the redundant scope. Per CLAUDE.md "Plans
  Run To Actual Completion" — duplicate-effort builds are a form of technical debt.

## Findings Triage Discipline (HARD RULE)

When you discover an issue mid-task — a QG failure on someone else's code, a silent bug in a sample data row, a doc/code
drift, an unexpected manifest shape, a stale codex SSOT, a missing test, anything that wasn't your todo but that you
observed while doing your todo — the action you take depends on **scope** and **blast radius**. The default is
wrong-action because most agents either over-fix (touch foreign work) or under-document (let the finding evaporate in
chat). This rule pins the right action for each case so findings actually land somewhere durable + the right person
fixes them.

### Decision tree

| Where the finding sits                                                                       | Action                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **In-scope** — surfaced while running QG/tests on YOUR code, OR while editing a file you own | **Fix it yourself.** Don't wait, don't flag, just ship the fix in the same commit (or an adjacent one). Your plan covers it; this is part of the work. Don't bounce a small fix to the issues folder just because it wasn't in the original todo — silent-bug-in-sample-data-row caught while writing tests is exactly what you should be catching.                                                                                          |
| **Adjacent to your plan** — related to your active plan but not in the immediate todo        | **Document + fix now or in next phase of YOUR plan.** Append a finding section to your plan body (or extend an existing tier with a new sub-todo); the plan owner is you, so the fix lands inside the same workstream. Don't punt to issues folder — that's for findings nobody owns; this one IS yours.                                                                                                                                     |
| **Outside your plan, fits another active plan**                                              | **Find the right plan + document there.** Add a finding annotation to the relevant plan body (`cefi_master`, `writegate_*`, `defi_master`, etc.) with explicit owner pointer. The agent on that plan picks it up. **Do not fix yourself** — collision risk + the right plan owner needs to see the finding to make the architectural call. A small annotation in someone else's plan body is fine; a refactor of their code is not.          |
| **Outside every active plan**                                                                | **File an issue doc** in [`plans/active/issues/<short-name>_<YYYY_MM_DD>.md`](../plans/active/issues/). These get triaged at audit cadence + either folded into a plan or addressed standalone. Existing precedents: [`defi_archetypes_doc_plan_drift_2026_05_07.md`](../plans/active/issues/defi_archetypes_doc_plan_drift_2026_05_07.md), [`defi_launcher_audit_2026_05_07.md`](../plans/active/issues/defi_launcher_audit_2026_05_07.md). |
| **Big / cross-cutting finding** (any of the "big" criteria below)                            | **NOTIFY THE OPERATOR IMMEDIATELY** in the chat — surface it in the next message summary, not buried in a plan annotation. Then **also file an issue doc** per the row above (don't pick one or the other — do both). Operator-time-to-decide on a non-big finding is cheap; operator-time-lost on a big finding hidden in a plan body is expensive.                                                                                         |

### What "big" means (any one of these qualifies)

- Finding that breaks **data correctness** for ≥1 asset_group (silent-zero capture, schema drift on disk, manifest
  phantom mass, lookahead-bias in features compute, batch/live divergence in the unified pipeline).
- Finding on the **2026-05-23 live-DeFi deadline** critical path (anything in the master plan's Group F/G live-only
  prerequisites, anything blocking a paper-trade or testnet smoke).
- Finding that requires action across **≥2 repos** (UAC + a service consumer; an SSOT + multiple call-sites; a launcher
  - the watchdog dict).
- Finding that **contradicts a workspace SSOT** in CLAUDE.md / codex (the SSOT is wrong, OR the code is wrong — either
  way, both can't be true; an agent reading the SSOT and an agent reading the code reach different conclusions).
- Finding that would **change the work-split** (re-pri P0/P1, swap an item between owners, defer post-May-23, surface a
  new prerequisite that wasn't in the 5-day cycle).
- Finding that **contradicts an in-flight VM run** (silent-zero, wrong row-key shape, partial-bundle, missing
  per-instrument progress events) — operators need to decide stop-VM vs let-it-finish-and-rescan within the run window.

If you're not sure whether it's big, surface it. The cost of one extra paragraph in a chat summary is far lower than the
cost of an operator missing a P0 finding for hours.

### Temporary exception — QG-failure findings on someone else's code (2026-05-07 → ~2026-05-09)

**While Ikenna sweeps through workspace QG cleanup (target completion 2026-05-08, latest 2026-05-09), QG-failure
findings on someone else's code are EXEMPT from the case-3 / case-4 / case-5 documentation requirement.** Don't file
issue docs or annotate plans for `ruff N811` / `basedpyright reportUnknown` / similar lint or type-check failures
discovered while running QG against another agent's code. They'll be cleaned up in bulk by the QG sweep — individual
annotations would just create churn that gets blanket-resolved.

Examples that are EXEMPT during this window:

- `ruff N811 in tests/internal/unit/test_prediction_market_taxonomy.py:605` (ComsicTrader's code, surfaced 2026-05-07
  while running UAC QG for an unrelated Phase 1 verification).
- `basedpyright reportAttributeAccessIssue` / `reportUnknownMemberType` in someone else's module that you only read
  because QG ran across the whole repo.
- Any blanket lint / type-check pass failure that's clearly broad enough to be a workspace-wide cleanup pass.

What is **NOT** exempt during this window (still apply cases 3/4/5 normally):

- **Case 1** still applies — your own QG failures on your own code → fix yourself, no exemption.
- **Non-QG findings** discovered via probes, spot-checks, manifest reads, event-stream inspection, runtime behaviour —
  these are real findings, not lint noise. Data correctness, in-flight VM bugs, SSOT contradictions, silent-zero
  captures, partial-bundle shapes — all stay case 1-5 normally regardless of whether QG also surfaces them.
- **Big findings** that happen to be visible via QG too — if it's case-5-big (e.g. a basedpyright failure that reveals
  an actual API-shape contradiction across repos), it's still big, still operator-notify, still issue doc.

**Lift this exception** once QG is workspace-clean (operator signal). At that point all QG-failure findings revert to
standard case-1-to-5 routing.

### Issue-doc format

Mirror the existing precedents (e.g. `defi_archetypes_doc_plan_drift_2026_05_07.md`). The minimum frontmatter:

```markdown
---
title: "<short title — what's broken or drifting>"
created: <YYYY-MM-DD>
author: <harsh|ikenna|agent-id>
source:
  - <plan or codex doc that surfaced it>
  - <code file:line if relevant>
locked_by: live-defi-rollout
locked_since: <YYYY-MM-DD>
---

# <Title>

> **Severity**: <P0|P1|P2> — <one-line rationale> **Blast radius**: <repos / plans / asset_groups affected> **Suggested
> owner**: <plan or person if known; else "operator triage">

## What I found

<concrete evidence — file:line, sample data, command output, parquet row dump, diff>

## Why it matters

<correctness / perf / deadline / SSOT-drift impact>

## Recommended decision

<fold into plan X / new plan needed / standalone fix / discuss>
```

### Why this discipline matters

- **No silent finding loss.** Every finding lands in EXACTLY ONE of: your code (fixed in-place), your plan (annotated +
  fixed), the right plan (annotated + handed off), the issues folder (doc'd + triaged). The matrix is exhaustive — no
  fifth option, no "I'll mention it later", no "the next agent will spot it too."
- **Right person fixes it.** The plan owner has the context and surrounding code in their head. A drive-by fix from
  another agent often misses architectural intent — the "Two teammates × multiple parallel agents" rule applies here.
  Small annotations in someone else's plan body are fine + actively encouraged; refactors of their code are not.
- **Big findings reach the operator fast.** Plan annotations are read at audit cadence (every few days); chat summaries
  are read in minutes. A live-trading-deadline-affecting finding cannot wait for the next audit pass. The dual-path
  (chat + issue doc) gives the operator immediate decision support AND a durable record after the chat scrolls away.
- **No "drive-by perfection" excuse.** The rule explicitly assigns small fixes to you (case 1) so agents can't hide
  behind "scope discipline" to skip obvious bug-fixes in their own code. If you ran tests and saw a failure on YOUR
  code, fix it; don't punt to the next agent. The discipline cuts both ways.

## Plans Run To Actual Completion, Not Smoke-Test Green (HARD RULE codified 2026-05-08)

**The pattern bug**: split-plan close-outs ship _code + schemas + smoke-tests_ then mark "operator-actionable" /
"deferred" / "needs operator credentials". Next-cycle plans assume the data / migration / state exists — they build on
empty space. By 2026-05-23 the cumulative gap becomes "the carry archetype is wired but no actual DeFi data lives on
AWS, no actual migration ran, no actual backfill completed". Each plan looks GREEN in isolation; the system as a whole
is RED.

**The rule**: every plan + every Tab in a split plan runs to **actual completion on real infrastructure**:

- **Backfills** run to natural shutdown with manifest-verified rows + sample-inspected parquets — not "launcher script
  shipped + 1 VM verified for 90s".
- **Migrations** transfer the actual data with destination size/object-count parity — not "migration script shipped +
  tested on a sample shard".
- **Cloud migrations** kick off the Storage Transfer Service / DataSync job + verify ≤0.01% drift + sample read returns
  expected rows — not "buckets provisioned".
- **Smoke tests** run against real AWS S3 / real GCS via real ADC — not mocked CI smoke.
- **Refactors** propagate to every consumer in the same plan — not "Wave 2 sweep deferred".
- **Reconcilers** run with `--apply-flips` against the full manifest — not dry-run on 100 rows.

**The single allowed exception**: a downstream plan EXPLICITLY takes over with a full-run handoff. Handoff must (1) name
the downstream plan by file path in the current plan's done-definition; (2) the downstream plan must have a phase that
explicitly consumes the smoke-tested artefact + runs it to completion; (3) both sides must be in `plans/active/` or
`plans/epics/` (no "we'll write that plan later").

**Operator authority + ADC**: the agent has ADC admin permissions on both GCP (`central-element-323112`) and AWS
(`427895769566`). Provisioning buckets, launching backfill VMs, kicking off transfers, making SSOT triage calls when 3
sources have drifted — these are all in scope. Do NOT pause for operator approval on these. The hard-stop list (genuine
human-only): wallet private keys + custody endpoint approvals, live-trading kill-switch arming, force-push to main,
version 1.0.0 graduation, destructive ops beyond local working tree (bucket deletion, table drops, prod VM force-stops).
Everything else: run it.

**Anti-patterns** (banned):

- "Operator-actionable" close-outs (unless the operator-only boundary is one of the hard-stops above).
- "Sub-plan to be filed" (current plan ships full scope OR explicitly hands off to a NAMED existing plan).
- "Phase N ready to run" with no actual run (✅ means ran-to-completion).
- Smoke-only QG without real-infra verification for plans involving real infrastructure.

### Split Plan Format — Full-Execution Criterion

Every Tab in a daily work-split plan MUST extend its **Done definition** with:

```markdown
**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE):

- ✅ <full-run criterion 1 — exact data/state on real infra>.
  - **What ran**: <command + machine/VM-name + duration>.
  - **Verification**: <gcloud/aws CLI command + expected output + actual observed>.

**Handoff exception(s)** (if any):

- <criterion N> deferred to <downstream-plan-path>:<phase-id>. Justification: <why downstream is right runner>.
```

Reviewers reject Tabs whose done-definition has only code/test deliverables without the full-execution subsection.
Reviewers reject "handoff exceptions" that don't name a real plan in `plans/active/` or `plans/epics/`. Mirrored at
`plans/PLAN_FORMAT.md` § 8 "Full-Execution Criterion (codified 2026-05-08)".

### Composes with

- "Commit + Push + Flip Plan Checkboxes" (per-shippable-unit) + "Post-Plan-Phase Codex Audit" (codex reflects actual
  state) + "Findings Triage Discipline" (case 1-5 routing during runs) + "Capture Discoveries As Plan Todos" (mid-run
  findings → plan todos).

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
- When all active repos are available (full workspace; count derives from `workspace-manifest.json` `repositories` keys
  excluding `archived_into` — currently 27 active after features-\* consolidation 2026-05-08): zero technical debt,
  update everything

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

### 6. Downstream Consumer Updates (extended 2026-05-08 to cover non-library refactors)

When modifying shared libraries (UAC, UTL, UCI, UEI) **OR removing/renaming any publicly-imported symbol from any
service or peripheral repo** (e.g. strategy-service `cli.handlers.batch_utils.get_strategy_factories` removal in
V1-RETIRE Phase 2 2026-05-01):

- Pre-audit identifies EVERY downstream consumer across the **entire workspace** — not just service repos. Include:
  - Service-internal consumers (`*_service/*/`)
  - Peripheral script directories (`e2e-testing/scripts/`, `*_service/scripts/`, `deployment-service/scripts/`)
  - Sample notebooks, ad-hoc one-off scripts, smoke harnesses
- Plan includes explicit fix items for each affected repo / script directory
- No "fix later" — all consumers updated in the same plan
- Quality gates run on each affected downstream repo
- **`grep` across the workspace for the removed/renamed symbol is mandatory**; the AST-walk pattern from QG STEP 5.64
  (workspace-wide callsite enumeration) is the canonical implementation shape
- Reviewers reject PRs that remove/rename a public symbol without including a workspace-grep audit table in the plan

**Why this extension exists**: 2026-05-01 → 2026-05-08 silent rot of `e2e-testing/scripts/defi/colocated_engine.py`
(broken import of `get_strategy_factories`). The original § 6 only covered shared libraries (UAC/UTL/UCI/UEI), so
strategy-service's V1-RETIRE Phase 2 refactor didn't fire the rule. The non-service consumer (`colocated_engine.py`)
broke silently for 7 days because it was outside any QG. Reference:
`plans/active/issues/runbook_execution_governance_gaps_2026_05_08.md`.

### 7. Single Source of Truth

- Types/schemas belong in ONE place. UAC for external data normalization, `unified_api_contracts.internal` for internal.
- No service should self-declare types that exist in contracts libraries
- No re-definition of enums, dataclasses, or Pydantic models that already exist upstream
- Pre-audit should catch self-declared duplicates and include them in the fix manifest

## Runbook Execution-Owner SSOT (HARD RULE codified 2026-05-08)

Every operator-runnable runbook, smoke harness, manifest-rescan script, alerting drill, demo run, or rehearsal procedure
MUST declare an explicit periodic-execution path. Without one, the runbook silently rots — its imports break against an
evolving codebase + nobody notices until the operator panics at cutover. Reference incident: 2026-05-01 → 2026-05-08
silent rot of `e2e-testing/scripts/defi/colocated_engine.py` paper-trade harness (7 days).

### What every runbook MUST declare

Frontmatter (or in the first paragraph) of every runbook in `plans/active/issues/<runbook>.md` or every operator-driven
todo in a master plan body:

```yaml
execution:
  owner: <named Tab in current work-split | service maintainer | cron schedule>
  cadence: <daily | weekly | monthly | per-PR | per-deploy | one-shot>
  verifier: <event-stream signature | exit code | manifest spot-check | downstream side-effect>
  last_executed: <YYYY-MM-DD or "NEVER" — required field>
```

**No exceptions** — runbooks without all 4 fields are review-blocking. If the runbook is genuinely one-shot (e.g. "run
this once after the migration ships"), declare `cadence: one-shot` + `last_executed: NEVER` and remove the runbook to
`plans/archive/` after the one-shot fires.

### Where execution actually happens (closed set)

Every runbook's `owner` resolves to ONE of these execution paths — no others:

1. **Cron VM** in `deployment-service/scripts/vm/` with a singleton-locked launcher + watchdog dict registration (e.g.
   forward-poll VMs, manifest-consolidator, vm-zombie-watchdog itself).
2. **Daily Tab assignment** in tomorrow's `work_split_<YYYY_MM_DD>_*.md` — explicit todo with the runbook path
   referenced + a verifiable done-definition.
3. **QG-wired smoke** — runbook's smoke runs as part of `bash scripts/quality-gates.sh` for the consumer service.
   Catches drift on every PR (sub-minute feedback loop).
4. **Cron-triggered ScheduleWakeup** — Tab agent schedules a periodic wakeup that re-runs the runbook + verifies
   done-definition. Lower-overhead than cron VM for runbooks that fit in <5min.

### Reviewer enforcement

PRs that ship a new runbook without an `execution:` block are blocked. PRs that change a runbook's `last_executed` date
without showing actual run evidence (event-stream link, commit sha of verification, etc.) are blocked. The
`runbook_execution_governance_gaps_2026_05_08.md` issue doc is the canonical reference for why this rule exists.

### Composes with

- `Findings Triage Discipline` — case-1-to-5 routing applies when a periodic execution surfaces a finding; the runbook
  itself doesn't need to file an issue doc, but its execution does.
- `No fire-and-forget VM launches` — extends the VM rule to scripts/runbooks. The same event-stream verification
  contract applies (STARTED + progress + STOPPED).
- `Citadel-Grade Planning § 6 Downstream Consumer Updates` — runbooks ARE downstream consumers; the extended § 6 rule
  catches refactors that break them.

## Peripheral Script Directories Under Primary-Consumer QG (HARD RULE codified 2026-05-08)

Every peripheral script directory that imports from a service's Python package MUST be wired into THAT service's
`scripts/quality-gates.sh` so basedpyright + ruff + import-resolution catch breakage at PR time, not at runtime 7 days
later.

### Concrete mapping

| Peripheral script dir                                     | Primary consumer service                                                                            | QG path                                                                   |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `e2e-testing/scripts/defi/` (`colocated_engine.py`, etc.) | strategy-service (imports `strategy_service.cli.handlers.*`)                                        | `strategy-service/scripts/quality-gates.sh` runs basedpyright on this dir |
| `e2e-testing/scripts/sports/`                             | features-sports-service / mtds (imports `features_sports_service.*` / `market_tick_data_service.*`) | features-sports-service QG                                                |
| `e2e-testing/scripts/prediction/`                         | mtds + features-onchain (imports `market_tick_data_service.*` / `features_onchain_service.*`)       | mtds QG (primary)                                                         |
| `*_service/scripts/migration_*.py`                        | own service                                                                                         | own service QG (already covered)                                          |
| `deployment-service/scripts/vm/*.sh`                      | bash; no Python imports                                                                             | bash-syntax check in deployment-service QG                                |
| `unified-trading-pm/scripts/*.py`                         | PM library + various services                                                                       | PM QG                                                                     |

### What "wired into QG" means concretely

The consumer service's `scripts/quality-gates.sh` adds a step that:

1. `cd ../e2e-testing/scripts/<asset_group>/` (or equivalent peripheral dir).
2. `basedpyright` on every `.py` file. Asserts every import resolves.
3. `ruff check` on every `.py` file.
4. (Optional) Smoke-execute the harness in `--dry-run` mode if available.

If the peripheral repo isn't a sibling at QG time (CI), skip the step with a clear message — but locally + on the
operator's workstation it MUST run. The intent is to catch import-rot in <1 minute on the next PR, not in 7 days when
the operator runs the harness.

### Why this rule exists

`colocated_engine.py:306` imports `from strategy_service.cli.handlers.batch_utils import get_strategy_factories`. That
symbol was removed by strategy-service's V1-RETIRE Phase 2 refactor (2026-05-01). basedpyright would have caught the
ImportError instantly if it had run on `colocated_engine.py` — but `e2e-testing/scripts/` was outside any service's QG.
7 days passed with the harness silently broken. Reference:
`plans/active/issues/runbook_execution_governance_gaps_2026_05_08.md`.

### Composes with

- `Citadel-Grade Planning § 6` extension above — Pre-Audit + this QG wiring are the two halves of preventing the rot.
- `Runbook Execution-Owner SSOT` above — the QG wiring catches static-import drift; the execution-owner SSOT catches
  runtime drift (e.g. external API changes that don't fail typecheck but fail at fetch-time).

## Master Plan Continuous-Verification Column (HARD RULE codified 2026-05-08)

Every success criterion in the master plan's per-service readiness checklist (Groups A-G; 23 items per
`master_to_live_defi_2026_05_23.md`) MUST declare its **continuous verification path** — what cron / Tab / QG runs
between checkpoint deadlines to keep the criterion green.

### Why

Master plan success criteria are checkpointed at cutover (May-23 for live-DeFi). A criterion that goes red 3 weeks
before the deadline is invisible until the operator manually walks every item — too late. The continuous-verification
column makes silent rot detectable on day 1 instead of day 22.

### Required column

The master plan readiness table MUST have this shape (one row per item):

| Group | Item | Cutover Success Criterion           | **Continuous Verification**                     | Last verified |
| ----- | ---- | ----------------------------------- | ----------------------------------------------- | ------------- |
| F     | 17   | paper-trade smoke green at May-23   | Daily cron VM `mtds-paper-smoke-` + Tab 5 sweep | 2026-05-08    |
| F     | 18   | batch-vs-live recon green at May-23 | Daily cron + alerting rule for delta > 5bps     | 2026-05-07    |
| F     | 19   | Copper + CEFFU treasury wired       | Live-only — no continuous; manual sign-off      | n/a           |

If an item's continuous verification is genuinely "manual sign-off only" (live-only operator-judgment items), declare
`Continuous Verification: manual` + `Last verified: <YYYY-MM-DD or NEVER>`.

### Reviewer enforcement

Master plan refresh PRs that don't update the `Last verified` column for changed items are review-blocked. Items where
`Last verified` is older than the declared cadence trigger a P0 alerting rule (Tab 5 governance owns the alert).

### Composes with

- `Runbook Execution-Owner SSOT` above — the master plan's continuous-verification column points at the runbook's
  `execution.owner` field. They MUST agree.
- `Findings Triage Discipline` — when a continuous verifier surfaces a regression, it's a Case 5 big finding by default
  (since master plan items are by definition on the May-23 critical path).

## Per-Tab Worktrees — 3-tier parallel-agent isolation (codified 2026-05-10)

Each operator (Ikenna / Harsh) runs N parallel agent "tabs" — each isolated in its own `git worktree` at
`.tabs/<N>/<repo>/` on a permanent branch `tab/<operator>/<N>`. **Slot is durable; theme rotates daily** via the
operator's work-split plan.

**3-tier hierarchy:**

- **Tier 1 — Operator (Ikenna ⊥ Harsh):** separate machines.
- **Tier 2 — Slot (per worktree):** `.tabs/<N>/<repo>/` on branch `tab/<operator>/<N>`. Per-slot `PREK_CACHE_DIR` via
  auto-generated `.envrc`. Slot count operator-declared at `--init`.
- **Tier 3 — Sub-agent (within one slot):** shares the slot's worktree; slot master partitions fan-out + reconciles
  in-session.

**Bootstrap (one-time per operator):**

```bash
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --init --slots 8     # provision 8 slots
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --add-slot 9         # grow fleet by one
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot 3       # between themes: clean + rebase
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --list               # show configured slots
```

**Reconciliation (per shippable unit):**

```bash
bash unified-trading-pm/scripts/dev/slot-master-rebase.sh                       # fetch + rebase + classify conflicts
```

The helper emits `[CONFLICT]` blocks with shape classification (`append-section` / `checkbox-flip` / `paragraph-rewrite`
/ `code` / `unknown`); slot master auto-resolves trivial shapes + escalates semantic ones per the plan-aware merge
resolution protocol.

**Foot-gun mitigations vs. shared-tree model:**

| Foot-gun                            | Status under per-slot model                                                |
| ----------------------------------- | -------------------------------------------------------------------------- |
| #1 foreign work bundled in          | **Unrepresentable.** No other slot can touch your `.git/index`.            |
| #2 `--cached --stat <path>` masking | **Unrepresentable.** Only your hunks are in your index.                    |
| #3 concurrent reset wipe            | **Unrepresentable.** No other slot can move your HEAD.                     |
| #4 prek auto-restore race           | **Mitigated** via `PREK_CACHE_DIR` per-slot. prek patches stay slot-local. |

Within-slot collisions (sub-agents sharing the slot's worktree) remain possible — the "mandatory pre-commit check"
discipline in the "Commit + Push + Flip Plan Checkboxes" section still applies WITHIN a slot. Master agents partition
sub-agent fan-out by repo/dir at spawn time to minimise within-slot overlap.

**SSOTs:**

- [`codex/05-infrastructure/per-tab-worktrees.md`](../codex/05-infrastructure/per-tab-worktrees.md) — canonical 3-tier
  model + slot-vs-theme decoupling + bootstrap recipe + slot-reset discipline.
- [`codex/05-infrastructure/plan-aware-merge-resolution.md`](../codex/05-infrastructure/plan-aware-merge-resolution.md)
  — slot-master reconciliation protocol with closed conflict-shape taxonomy.
- Plan that codified it:
  [`plans/active/per_agent_worktrees_2026_05_10.md`](../plans/active/per_agent_worktrees_2026_05_10.md).

## Daily Work-Split Process (Ikenna ↔ Harsh, AI-paralleled)

**Main orchestrator bootstrap pointer (read first if you are a fresh main-agent session).** If you are running as a main
orchestrator agent on either operator's machine, your first action is to read your side's LEDGER bootstrap section
before doing anything else:

- **Ikenna's main orchestrator** → read [`ikenna_orchestrator/LEDGER.md`](../ikenna_orchestrator/LEDGER.md) § "Bootstrap
  — fresh main-agent chat" + [`ikenna_orchestrator/AGENT_ONBOARDING.md`](../ikenna_orchestrator/AGENT_ONBOARDING.md).
- **Harsh's main orchestrator** → read [`harsh_orchestrator/LEDGER.md`](../harsh_orchestrator/LEDGER.md) § "Bootstrap —
  fresh main-agent chat" + [`harsh_orchestrator/AGENT_ONBOARDING.md`](../harsh_orchestrator/AGENT_ONBOARDING.md).

Each per-side `<side>_orchestrator/` directory contains: `AGENT_ONBOARDING.md` (boot-context pointer for spawned tabs),
`LEDGER.md` (today's tab registry + open questions + recent done), `_agent_pings.md` (intra-side doorbell). The boot
checklist runs `git status` + `git fetch` summary + ledger read in ~3-5 min, then the main agent acks to the operator
"State: N tabs in flight, M intra-side pings, K cross-side pings, J local commits queued. Today's plan = X. Standing
by." Skip this and you start blind to the operator's in-flight context.

Spawned tab agents (Tab 2+) follow the same pattern but read AGENT_ONBOARDING first — see "Spawn prompt template (Model
B)" subsection below for the canonical paste-ready prompt.

**Why this exists.** Two human operators (Ikenna + Harsh) each run multiple parallel Claude Code / Cursor agents. A
single human-day with 5 parallel agents at full saturation is closer to **~50 AI-days of work**; both sides combined
yields **~100 AI-days/day**. Without an explicit daily split, the agents converge on the same critical-path files (UAC,
master plans, deployment-api) and step on each other's commits via the shared working tree. The daily split is the
operator's load-balancer: it pre-decides who owns what so the AI parallelism is additive, not collisional.

**Cadence.** Daily. Each morning the operator (or main orchestrator agent on operator's behalf) drafts two new
work-split plans for the day — one per side — sized so each absorbs ~5 days of solo AI work × 5-10 parallel agents =
~25-50 AI-days per side. The plans live in `plans/active/work_split_<YYYY_MM_DD>_ikenna.md` and
`plans/active/work_split_<YYYY_MM_DD>_harsh.md`. At end-of-day, the splits are archived to `plans/archive/` (the day's
completed work flows back into the underlying master plans + codex docs as the durable record).

### Split principle (which side gets which work)

**Ikenna** owns work that is any of:

- **Cross-cutting design** spanning 3+ repos (e.g. UAC schema + UTL helper + deployment-api + UI all in one shape)
- **Trading-judgment / risk calls** (paper-trade smoke, kill-switch wiring, alert thresholds, archetype
  canonicalisation)
- **Governance / ratchet thinking** (workspace QG gates, baseline ratchets, version graduation, force-sync)
- **Large migrations or refactors** that change the on-disk shape (manifest schema, GCS hive vocab, parquet column drop,
  path-template change, multi-repo facade rename)
- **Human-approval surface** (anything an operator has to sign off on — IAM proposals, Phase 0 security reviews, version
  1.0 graduation, kill-switch rule activation, bucket-naming SSOT decisions)
- **Coordination work** that touches the master plan or umbrella plans (because Ikenna is closer to the May-23 cutover
  model)

**Harsh** owns work that is any of:

- **Implement-from-spec** (UAC types pre-designed → write the Pydantic models; UTL helper signature pre-designed → write
  the helper; route handler with full behavioural contract → write the route)
- **Run-script-and-verify** (launch backfill VMs and monitor; run reconcilers; rebase + push on shipped fixes;
  smoke-test endpoints)
- **Single-repo edits with crisp boundaries** (one repo, one feature surface, no UAC/UTL changes)
- **Test execution + Playwright matrices** (DART personas, integration smokes, regression test coverage)
- **Mechanical refactors** with zero design judgment (move launcher A → location B + register prefix; lint cleanup;
  type-check fixes on someone else's code; docstring sweeps)
- **Audits and probes** (read-only investigations that produce an issue doc but no code change)

**Tie-breaker when an item could go either way**: if it touches >1 repo and the design isn't pre-spec'd, Ikenna; else
Harsh. If it would require Harsh to make a closed-set design call (e.g. "decide the AlertCode taxonomy"), it's Ikenna.
If Ikenna would just be running a script and watching events, it's Harsh.

### Two valid working models per side (operator picks)

**Model A — fixed thematic 5-tab clustering.** Operator pre-defines 5 fixed tabs by **coherent context cluster** (e.g.
Tab 1 = alerting, Tab 2 = writegate, Tab 3 = enumerator, Tab 4 = DeFi launch, Tab 5 = PM governance). Each tab runs Opus
at full window, owns its own done-definition, and fans out to sub-agents (Task tool / Explore / general-purpose) for
mechanical multi-file work the master can spec cleanly. **Tabs run to their done-definition, not a calendar date** —
agents finish faster than humans. Coverage guarantee: every parent-doc item is assigned to exactly one tab. Used when
work clusters cleanly into 5 thematic groups; less overhead, predictable shape.

**Model B — 1-main + dynamic spawned tabs.** One **main orchestrator agent** (Tab 1) does no implementation — only
direction-setting + Q&A dispatch + plan-of-record curation + ping-ledger triage. Spawned tabs (Tab 2+) are **scoped
implementers**: each runs one task end-to-end then goes quiet. Tab count varies by day (2 in the morning, 6 by
afternoon, sometimes two agents on different phases of the same plan in parallel — fine). Used when the day's work is
dynamic, when items keep emerging from incoming pings, or when the operator wants a single conversational dispatcher
between themselves and N delegates.

Both models obey the same universal mechanics below. Operator can mix them — Ikenna runs Model A, Harsh runs Model B —
or both pick the same model on a given day. The split _plan_ shape adapts: Model A uses fixed tab numbering with per-tab
sections; Model B uses a "Today's status → Tab registry" with dynamic entries.

### Universal mechanics (apply to BOTH models)

**Per-slot worktrees (CRITICAL — supersedes shared-working-tree model 2026-05-10).** Each tab runs in its own per-slot
worktree at `${WORKSPACE_ROOT}/.tabs/<N>/` on branch `tab/<operator>/<N>` — cross-slot races on `.git/index` + working
tree are unrepresentable by construction. See "Per-Tab Worktrees" section above + the codex SSOT
[`per-tab-worktrees.md`](../codex/05-infrastructure/per-tab-worktrees.md). **Within a slot**, sub-agents share the
slot's worktree + index — so the pre-commit check + `git add -p` discipline (see "Commit + Push + Flip Plan Checkboxes"
§ "The mandatory pre-commit check") still applies for within-slot multi-sub-agent fan-out. Master agents partition
sub-agent fan-out by repo/dir at spawn time to minimise within-slot overlap.

**Conditional push (the multi-agent safety valve).** Per the per-shippable-unit cadence in "Commit + Push + Flip Plan
Checkboxes," every shippable unit gets a local commit. Before pushing, every agent runs:

```bash
git fetch origin <branch>
git log --oneline <branch>..origin/<branch>   # incoming commits, if any
```

- **Zero incoming → push freely.** Default path; no operator approval needed.
- **Any incoming → STOP, do NOT push.** Write a `🟡 BLOCKED` entry in your plan-of-record's `## Open questions` section
  listing your local commits + the incoming ones. Append a one-liner ping in `_agent_pings.md`. Continue with anything
  you CAN do; main + operator decide rebase / merge / cherry-pick / drop.

**Plan-of-record + Q&A bus.** Every spawned tab has a single **plan-of-record** (e.g. `cefi_master.md`,
`writegate_honest_coverage.md`, `defi_master.md`) — that's where its todos live, where it flips checkboxes as it ships,
and where it writes a `## Open questions` section for blockers. Q&A format:

```markdown
## Open questions

### Q1 — [agent-tag, YYYY-MM-DD HH:MM] — short title

**Status**: 🟡 BLOCKED — waiting for answer

<full question with file:line context, what was tried, options considered>

#### A1 — [main, YYYY-MM-DD HH:MM]

**Status**: ✅ RESOLVED

<answer + reasoning + commit-sha of anything shipped meanwhile>
```

Status badges (🟡 BLOCKED / ✅ RESOLVED) make scan-for-open-questions instant. Resolved Q&As get cleaned up at the daily
ledger sweep — Q&A clutter is more costly than Q&A loss; the audit trail survives in commits + chat + the plan checkbox
flips.

**Ping ledger (`_agent_pings.md`).** Ephemeral doorbell — always ≤10 lines (active pings only). Format:

```text
[YYYY-MM-DD HH:MM UTC] <agent-tag> — <5-10 word summary>; see <plan-of-record>.md
```

Spawned agent appends a one-liner when it has a Q on its plan-of-record; main agent removes the line when the Q is
answered. Zero history kept here. **Don't write Qs into the work-split plan itself** — those go on the agent's
plan-of-record (the master / domain plan it's executing against).

**Ping ledger bifurcation (codified 2026-05-08).** There are TWO ping ledgers, NOT one. Both follow the format above but
serve different surfaces:

- **Workspace-shared `plans/active/_agent_pings.md`** — for **cross-side** comms only (Ikenna ↔ Harsh hard-gate
  signalling: a UAC contract landed, a UTL helper signature shipped, an in-flight refactor banner needs broadcasting).
  Polls run on the same ~1-min cadence but the surface stays quiet because cross-side comms are rare. Both sides write
  here.
- **Per-side `<side>_orchestrator/pings/slot_<N>.md`** — for **intra-side** comms (one operator's main agent ↔ that
  operator's spawned tabs: STARTED acks, blocker Qs, DONE announcements). **Per-slot files**, not one shared file —
  under the direct-to-`live-defi-rollout` merge model with per-tab worktrees, a single shared `_agent_pings.md` was the
  highest-frequency rebase-conflict source (every spawned slot appended to it). Since the side's main agent (slot 1) is
  the **only reader**, each spawned slot `N` writes ONLY `<side>_orchestrator/pings/slot_<N>.md` → zero collision on the
  ping surface; slot 1 polls `<side>_orchestrator/pings/*.md`. Today both sides have orchestrator directories
  (`harsh_orchestrator/`, `ikenna_orchestrator/`), each with `AGENT_ONBOARDING.md` + `LEDGER.md` + a `pings/` dir
  (`pings/README.md` + `pings/slot_<N>.md`). The legacy single `<side>_orchestrator/_agent_pings.md` is retired to a
  redirect stub on the Harsh side (2026-05-11) and may be migrated the same way on the Ikenna side. Format + lifecycle:
  `<side>_orchestrator/pings/README.md`.

The bifurcation matters because intra-side ledgers fill up fast (15-20 STARTED+DONE acks per cycle is normal) while
cross-side ledgers should have <5 active entries. Mixing them makes both surfaces unreadable.

**Polling cadence (Model B main agent).** Main agent polls `_agent_pings.md` every **~1 min** while operator is active.
When tabs go quiet (no pings 30+ min), stretch to 5 min. Main does NOT implement plan items — only direction +
dispatch + curation. Anything taking >1 min in chat either delegates (spawn fresh tab) or backgrounds
(`Task(run_in_background=true)`); main stays available for operator direction.

**Sub-agent fan-out (within each tab, both models).** When N independent sub-agents fan out, send them in **a SINGLE
message with N `Task` tool blocks** so they run concurrently. Sequential calls are wasted parallelism. Sub-agents
inherit nothing — paste `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the top of every Task prompt
(per "Sub-Agents & Autonomous Agents: Full Rules Required" rule).

**Spawn prompt template (Model B).** When the main agent recommends a fresh tab, the prompt **must** include the
orchestration preamble below so the spawned agent knows it's a delegate, not a peer. Copy this into every spawn:

```text
You are Tab N — a sub-agent spawned by <operator>'s main orchestrator agent (Tab 1, a separate
Claude Code session on the SAME machine).

Your slot is <N>. Your worktree is at ${WORKSPACE_ROOT}/.tabs/<N>/ on branch tab/<operator>/<N>.
All work happens INSIDE that worktree — opening Cursor / Claude Code there gives you an isolated
.git/index from every other slot. Today's theme for slot <N>: <theme>.

BEFORE doing anything else, read in order:
  1. <today's work-split plan> § "Bootstrap — read first if you're a spawned tab" — workflow rules.
  2. unified-trading-pm/cursor-configs/CLAUDE.md — workspace coding standards (Per-Tab Worktrees
     section + Daily Work-Split Process section).
  3. unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md — 3-tier isolation model.
  4. unified-trading-pm/codex/05-infrastructure/plan-aware-merge-resolution.md — reconciliation
     protocol when your push surfaces a rebase conflict.
  5. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — sub-agent inheritance.
  6. <PLAN-OF-RECORD-PATH> — your plan-of-record with todos + done-definition.

Your agent-tag for ping-ledger entries: <agent-tag>.
Your tab number: N (matches the entry header in the work-split plan).

ORCHESTRATION RULES:
  1. Per-slot worktree — cross-slot races unrepresentable. WITHIN your slot, sub-agents you spawn
     share your worktree's .git/index, so pre-commit check (git status + git diff --cached --stat
     NO PATH ARG) still mandatory before EVERY commit. Use `git add -p` for shared files; never
     `git add -A` / `git add <whole-shared-file>`.
  2. Plan-doc Q&A flow — write blockers into <PLAN-OF-RECORD>'s `## Open questions` (status
     🟡 BLOCKED), append ping in _agent_pings.md, continue with what you CAN do.
  3. Conditional push — per shippable unit: commit locally, fetch + check incoming, zero
     incoming → push, any incoming → flag + escalate.
  4. Plan-flip in same logical unit as code — checkbox flip + `<repo>@<sha>` evidence
     stamped in body, NOT batched at session end.
  5. Findings Triage Discipline (HARD RULE) — case-1-to-5 routing per CLAUDE.md.

YOUR TASK: <full self-contained context — what to ship, repos owned, collision boundaries
with other in-flight work, done-definition with verifiable bullet points>.

REPORT-BACK: per shippable unit, code commit + plan-flip commit, conditional push.
Final: append a "DONE-<YYYY-MM-DD>" block at the bottom of <PLAN-OF-RECORD> body listing
every code + plan-flip commit sha. EOD-audit (per CLAUDE.md "Capture Discoveries As Plan
Todos Immediately" § "End-of-cycle audit clause"): every deferral in your final summary
MUST already be a `- [ ]` plan todo or a `**DEFERRED**` annotation in plans/active/. Run
`grep -n "<distinctive phrase>" plans/active/*.md plans/active/issues/*.md` per deferral
line — match → cite file:line in summary; no match → STOP, add the todo, push the flip,
then resume. Reviewers reject summaries with grep-miss deferrals. Then go quiet —
don't pick up new work autonomously.
```

**Daily reset (each morning).** Main orchestrator (or operator solo if no main) runs:

1. `git fetch origin live-defi-rollout && git log --oneline -25 origin/live-defi-rollout` — summarise incoming commits
   since yesterday. Don't auto-pull; operator pulls explicitly when ready to sync.
2. Re-read yesterday's work-split plans (where partial items roll forward) + `_agent_pings.md` for overnight pings.
3. **Daily ledger sweep**: scan all `plans/active/*.md` for `## Open questions` blocks. Remove ✅ RESOLVED Q&As older
   than 24h. Verify no stale 🟡 BLOCKED Q&As (>24h without answer) — if any, re-prompt the spawned agent or escalate.
   Verify `_agent_pings.md` has no orphan lines.
4. **Draft today's two work-split plans** (one Ikenna, one Harsh) using the plan-shape template below. Pull in carryover
   items from yesterday's partials. Add new items that emerged from incoming pings or audit findings. Size to ~25-50
   AI-days per side (5 parallel agents × 5-10 days solo each). Each plan MUST include a `## Today's slot assignments`
   table per `plans/PLAN_FORMAT.md` § "Daily Work-Split Plan Shape".
5. **Slot-reset sweep** (per "Per-Tab Worktrees" section above): for every slot whose theme changed from yesterday's
   assignment, run `bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot <N>` to verify clean state +
   rebase the slot's branch onto `origin/live-defi-rollout`. Aborts if dirty — operator commits / pushes / discards
   before retry.
6. Mirror today's slot↔theme table into the operator's `<operator>_orchestrator/LEDGER.md` "Today's slot assignments"
   section (fresh tab-agents read this on bootstrap).
7. Report to operator: "Today's plan = X, Y, Z. Ikenna split has N items / M AI-days, Harsh split has P items / Q
   AI-days. Ping ledger has K entries open. Local commits ready to push: J (or zero). Slot-resets done: <list>."
8. Wait for operator direction. Push the daily-reset commit per the conditional rule.

### Daily work-split plan shape

Every daily split plan (one per side) follows this skeleton. Frontmatter:

```yaml
---
title: <Side>'s daily work-split — <YYYY-MM-DD> (<deadline-context>)
type: coordination-doc
status: active
created: <YYYY-MM-DD>
deadline: <upstream deadline if any>
horizon: <1-day cycle | scope-bounded>
companion_to: plans/active/work_split_<YYYY_MM_DD>_<other-side>.md
locked_by: live-defi-rollout
locked_since: <YYYY-MM-DD>
---
```

Body sections:

1. **Why this split exists today** — 2-4 lines: critical path for the cycle, what's queued from yesterday, what's new
   from overnight incoming.
2. **Working model** — A or B. Self-binding for the day so spawned agents know what shape to expect.
3. **Today's status → Tab registry** (Model B) OR **5-tab assignment table** (Model A) — every item assigned to exactly
   one tab; coverage guarantee. Each tab entry: identity, scope (P0/P1/P2 todos), plan-of-record, repos owned (collision
   boundary), read-first list, sub-agent fan-out plan, collision risk vs other tabs + the other side, done-definition
   with verifiable bullets.
4. **Cross-tab handshakes** — hard sync gates between tabs (e.g. "Tab 3 must ship UAC AlertCode before Tab 5 reads it").
   Operate independently otherwise.
5. **Cross-side handshakes** — hard sync gates with the OTHER side's plan (e.g. "Harsh Tab 4 ships UAC types → Ikenna
   Tab 2 consumes them in writegate Phase 4.A").
6. **Collision-risk callouts** — per-file / per-repo collision warnings: which tabs touch the same file or directory,
   and the mitigation (surgical `git add -p`, push-immediately + pull-before-next-edit, or serialised access with timing
   handshake).
7. **Spawn prompts** (Model B only) — full paste-ready prompt block per spawned tab using the template above.
8. **Daily sync points** — EOD checkpoint (which gates green / red), what carries to tomorrow.
9. **Defer post-deadline** (optional) — items both sides agree NOT to touch this cycle (P1+ items beyond scope). Short
   list, citing the umbrella that owns them.

**AI-day sizing.** Each tab/scope has an estimated AI-day budget in its entry (e.g. "~3 AI-days, 1 main agent + fan-out
to 4 sub-agents"). Add the budgets per side; aim for ~25-50 AI-days per side per cycle. **Err toward beefier plans**
(more items, fully spec'd) than thinner plans — under-utilisation is fine, under-specced collisions mid-cycle are not.
We can always do less of a beefy plan over time; we cannot retroactively add scope to a thin one.

### Cross-side coordination

Both sides' work-split plans are **mutual companions** (`companion_to:` in frontmatter). Cross-side handshakes appear in
BOTH plans (mirror-image entries) so neither operator misses the gate. When one side ships a hard-gate item (UAC type,
UTL helper signature, route handler shape), they push immediately + the other side `git pull`s before the next consumer
edit — same shape as cross-tab UAC handshakes within a side.

**The other side's plan is read-only for you.** You don't edit your counterpart's split — that's their orchestration
surface. Suggestions / corrections go via operator chat. The only allowed cross-edit: a 1-line cross-reference banner
saying "your Tab N depends on our Tab M shipping Y" — the same Cross-Plan Coordination Banners pattern used for VMs and
in-flight refactors.

### End-of-cycle: archive + roll-forward

At end-of-day:

1. **Carryover items** that didn't ship → roll forward to tomorrow's split, citing yesterday's plan path.
2. **Shipped items** → already reflected as `- [x]` in the underlying master plan(s) per "Commit + Push + Flip" HARD
   RULE. Nothing extra to record.
3. **Findings raised** → already in their respective places per "Findings Triage Discipline" (master plan,
   `plans/active/issues/`, or fixed in-place).
4. **Archive yesterday's work-split plans** to `plans/archive/`. They're durable history (who-owned-what on which day)
   but the active surface is tomorrow's plans.

Result: `plans/active/` always contains TODAY's two work-split plans + the durable master / domain / issue plans. The
work-split plans are **the daily orchestration surface**, not the durable record — durable record is the master plan
checkboxes + the codex SSOTs + the commit history.

### Anti-patterns (don't)

- **Don't** put Q&A into the work-split plan itself — that's main-agent-only writing surface. Q&A goes on the agent's
  plan-of-record (the master / domain plan).
- **Don't** mix the daily split with the master plan body — `master_to_live_defi_2026_05_23.md` is the durable readiness
  model; today's split is the daily orchestration surface. Both exist; neither replaces the other.
- **Don't** write spawn prompts in chat — they belong in the work-split plan body so the operator can paste them
  verbatim into a fresh Cursor / Claude Code tab without re-typing.
- **Don't** carry over a 5-tab thematic shape (Model A) when the day's work is genuinely dynamic — switch to Model B (1
  main + dynamic spawned). Pick per the day's character; don't lock in.
- **Don't** size both sides at <10 AI-days per cycle — that's under-utilising the parallelism. The whole point of the
  daily split is to absorb 5-10 parallel agents per side; thin plans waste the amplification.
- **Don't** archive the work-split plan mid-cycle even if all checkboxes flip — leave it active until EOD so spawned
  tabs (which may be running async) can still find their entry.

### Composes with

- "Commit + Push + Flip Plan Checkboxes" (per-shippable-unit cadence + pre-commit check)
- "Cross-Plan Coordination Banners" (in-flight VM / refactor banners on plans the work-split touches)
- "Capture Discoveries As Plan Todos Immediately" (mid-cycle findings → plan todos, not auto-memory)
- "Findings Triage Discipline" (case-1-to-5 routing for surprises)
- "Sub-Agents & Autonomous Agents: Full Rules Required" (every Task spawn pastes mandatory rules)
- "Citadel-Grade Planning Standards" (the master plan body is what gets beefed up; daily split is orchestration)
- "Two teammates × multiple parallel agents — don't edit unfamiliar files" (the foot-gun the daily split prevents)

## Sub-Agents & Autonomous Agents: Full Rules Required (MANDATORY)

Sub-agents (Task tool, mcp_task) and autonomous agents (GHA workflows, Claude Code `--print`, Cursor background agents)
start with FRESH context and do NOT inherit your rules. Reduced context makes them miss rules unless you explicitly
provide them.

**CRITICAL: Agents in `--print` mode CANNOT read files from disk.** Telling them "read .cursorrules" is useless — they
never see it. Rules MUST be pasted directly into the prompt text.

### SSOT shape (codified 2026-05-08)

`SUB_AGENT_MANDATORY_RULES.md` is a **symlink to CLAUDE.md** in PM canonical
(`unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md → CLAUDE.md`). The two files have **identical content**
— sub-agents need every workspace rule the parent agent has, and the prior ~30% subset file was a perpetual drift
hazard. Per-repo `.claude/SUB_AGENT_MANDATORY_RULES.md` symlinks (rolled out via `scripts/rollout-agent-symlinks.sh`)
point through to the same canonical, so existing references like _"read SUB_AGENT_MANDATORY_RULES.md"_ continue to work
at every site that already used them — they now deliver the full workspace-rules surface, not the old subset.
Sub-agent-specific framing (_"you are a sub-agent, the rules below apply to you"_) is added by the inject script
preamble + by spawn prompts in the work-split plans, not by file content.

### When launching ANY sub-agent or autonomous agent

1. **For local scripts:** Use `inject-mandatory-rules.sh`:
   ```bash
   RULES=$(bash unified-trading-pm/scripts/agents/inject-mandatory-rules.sh "$WORKSPACE_ROOT" "$REPO")
   ```
2. **For GHA workflows:** Load rules via `GITHUB_ENV` heredoc in a prior step, then prepend `${MANDATORY_RULES}` to the
   prompt.
3. **For Cursor/Claude Code sub-agents (Task tool):** Paste contents of
   `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` at the TOP of the prompt. (Resolves to CLAUDE.md
   content via the symlink.)
4. **If paste is impractical:** Include at TOP: "Before any action, read
   unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md and follow ALL rules strictly."
5. **Always include:** WORKSPACE_ROOT path. For tests: `cd <repo> && bash scripts/quality-gates.sh` (per-repo .venv).
   Never .venv-workspace for pytest.
6. **If rules injection fails, the agent MUST NOT proceed.** Exit with error.

Never rely on sub-agents "inheriting" rules — they cannot. Always inject the full rules. **SSOTs:**
`unified-trading-pm/scripts/agents/inject-mandatory-rules.sh` (injection wrapper) +
`unified-trading-pm/cursor-configs/CLAUDE.md` (rules content; SUB_AGENT_MANDATORY_RULES.md is a symlink alias).

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
