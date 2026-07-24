---
doc_type: plan
title: Data completion to 100% — historical Progress Log record (2026-06-21..06-24 sessions)
summary: >-
  Archive-bound record of fully-completed historical Progress Log entries extracted VERBATIM from
  data_completion_to_100_all_ag_2026_06_21.md (M-1) during the 2026-07-24 plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md). Covers the 2026-06-21 through 2026-06-24 session
  entries (continuous-paper dispatch, DeFi live-capture verification, per-AG audit narrative). No open todos are
  contained here — every checkbox in this file is already [x]. This is a read-only historical record, not an active work
  surface.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui]
scope: [engineer, admin]
tags: [backfill, manifest, honest-coverage, data-completion, mtds, instruments, live-trading, history, archive-bound]
related:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: docs_reconciler
last_updated: 2026-07-24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  data_completion_to_100_all_ag_2026_06_21 (M-1) -- extracted 2026-07-24, plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md), fully-completed Progress Log material with zero open
  todos, moved verbatim to relieve the parent's line-cap breach.
drift_direction: advance-code
---

# Data completion to 100% — historical Progress Log record (2026-06-21..06-24 sessions)

> **Split from M-1 on 2026-07-24** (`data_completion_to_100_all_ag_2026_06_21.md`, plan line-cap remediation,
> `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`). This is a **verbatim** extraction of fully-completed
> Progress Log entries (2026-06-24 autonomous B2 completion, 2026-06-23 continuous-flow sessions, 2026-06-22
> canonical-form/continuous-paper/GAP-analysis sessions) — every checkbox below was already `[x]` in M-1 before the
> move; nothing was dropped, reworded, or re-checked. **This file is archive-bound record only** — it is not an active
> work surface and carries no open todos. Read `data_completion_to_100_all_ag_2026_06_21.md` for the live program
> (measured snapshot, per-AG launch matrix, current Progress Log, cross-cutting scope).

## Progress Log (historical — extracted verbatim from M-1)

### 2026-06-24 (autonomous B2 deep-dive completion — 4 remaining UI/backend findings → verified-DONE)

Operator `/autonomous` dispatch: complete the 4 remaining B2 deep-dive findings to verified-DONE. All flipped ✅ above
with evidence; the residual stashed tick-2 live-path regression test was shipped first (`strategy-service@4bf16796`).

- **#1 wallet-transfers backend** — `IntraClientRebalanceCoordinator` → `strategy-service@1450019e`: emit-time Phase-E.3
  netting coordinator (N per-strategy intra-client transfers → ONE `TransferIntent` per
  `client×{unordered venue pair}×asset×transfer_type`; signed-sum netting, zero-net drop, bidirectional collapse,
  deterministic per-period `idempotency_key`) + raises `CrossClientTransferForbiddenError` on cross-client `add_request`
  (logs `CROSS_CLIENT_TRANSFER_FORBIDDEN` at ERROR). 10 unit tests (4 codex-mandatory cases + netting). Codex
  `client-funds-isolation.md` updated PLANNED→shipped.
- **#2 paper-trading under the platform nav shell** — `unified-trading-system-ui@0dba2705` (dir-move
  `app/paper-trading/`→`app/(platform)/paper-trading/` + `layout.tsx` tab bar Overview·Ledgers·Coins), verified at tip
  `@44790f93`. pw:L2 ✓ (76 passed) | regression `tests/smoke/paper-trading-nav-shell.smoke.spec.ts`. LIVE:
  `/paper-trading` now 302→`/login` on `odum-portal-00042-fhj` = under the `(platform)` auth shell (was public).
- **#3 candle+trade-triangle chart + coin drilldown** — `unified-trading-system-ui@44790f93` (`CoinPriceChart` +
  overview→coin `<Link>`s) + `e2e-testing@aef3294` (`_coin_history.py` emits per-coin daily-close `price_series`; live
  in GCS, 31 coins). pw:L2 ✓ | regression `tests/smoke/paper-trading-coin-chart.smoke.spec.ts`. LIVE: `coin-price-chart`
  testid present in deployed prod bundle.
- **#4 research de-mock + cross-links** — `unified-trading-system-ui@44790f93` (deleted `MOCK_STRATEGY_BACKTESTS`, now
  `useStrategyBacktests()` real hook + honest-empty; research↔paper cross-links). pw:L2 ✓ | regression
  `tests/smoke/research-real-data.smoke.spec.ts`. LIVE: `paper-to-research-link` testid present in deployed bundle.
- **Deploy**: rebuilt + deployed `odum-portal` (Cloud Build `615ba18c` → revision `odum-portal-00042-fhj` @ 100%
  traffic, asia-northeast1). The cold-start original-finding was flipped ✅-superseded (minScale=1 already live,
  verified warm) → `PM@3c242c98f`.

**Live-verification method + honest limitation:** the live prod surface uses REAL auth (Firebase email/password
Sign-In), not the `demo-token-admin` localStorage fixture the pw:L2 mock build accepts (`admin@odum.internal` is a test
fixture, NOT a real account — no password). So I could not log in to eyeball the rendered pixels behind the auth wall
(operator credentials needed; I deliberately did not extract a prod login from Secret Manager). Verified instead by (a)
deploy-landed (gcloud revision @ 100% traffic), (b) #2's behavioural `/login` redirect, (c) grepping the deployed prod
JS chunks for the finding testids — `coin-price-chart` (#3) + `paper-to-research-link` (#4) both PRESENT. pw:L2 (76
passed) covers the rendered behaviour against the exact committed code.

**Two discoveries captured (do not lose):**

1. **Region-consolidation cost finding** → `[INFRA] P3` todo in the B2 block above (odum-portal prod fans to 3 regions
   but only asia is warm/min=1; europe+us are min=0 ≈$0; recommend asia-only — operator scope decision pending). The
   surprise: the 3-region setup is already nearly free.
2. **Side-effect to flag (operator):** finding #2 made `/paper-trading` **login-gated** (under the platform shell now,
   as the finding asked — previously open at the root layout). If paper-trading should be viewable WITHOUT full platform
   login, that's a follow-up — flag it and I'll file the todo.

### 2026-06-23 (continuous-flow session — DeFi live now CAPTURING; per-AG live+batch audit)

Operator dispatch: continuous flow across live + batch for ALL 5 AGs (live producer running + landing rows + heartbeat;
batch continuous to ≤T-1; no seam). Measured current state from CONSOLIDATED `-prd-` `_index` (NOT the 2026-06-21
snapshot):

- **Live producers RUNNING for all 5 AGs** (fleet reshipped today, tarballs rebuilt 2026-06-23 09:42Z from clean LDR):
  cefi×16 mtds-live VMs, tradfi×1 (cme-trades) + fwd-daily-cron, sports×1 (odds-api), prediction×4 (kalshi+polymarket ×
  trades+book), and — the MAIN GAP — **DeFi had NO live producer running**.
- **DeFi LIVE forward-poll STOOD UP (PART A primary deliverable).** Launched the 3 price-sensitive defi live ops via
  `launch-defi-forward-poll.sh` (`defi-fwd-dex-swaps/-dex-pools/-oracle-prices-20260623-102*`, e2-standard-8,
  `VM_MODE=live`, `MANIFEST_PER_VM_SHARDS=true`, `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`, heartbeat-wrapped). The
  prior-session defi-handler `pipeline_mode` fix (mtds@ad3318d/@2c5e2b5: `dex_pools/dex_swaps/oracle_prices_handler`
  resolve `live_*` via `resolve_pipeline_mode(...,"live")`) is in the current tarball. **VERIFIED end-to-end:** the
  freshly-consolidated defi `_index` (10:34:40Z, after the VMs ran) holds **DEFI LIVE = 37 rows, 7 captured / 128,642
  captured rows**, modes `live_onchain_subgraph` (31) + `live_chainlink` (5) + `live_pyth_hermes` (1), dtypes
  `dex_pool_state/lst_rates/oracle_prices/dex_pool_swaps`, date 2026-06-23 — and **PIPELINE_HEARTBEAT emitting**
  (`vm=defi-fwd-* ag=DEFI task=defi-live-* source=vm-life-emitter`, 60s). The defi live pipeline is OPERATIONAL +
  captures real rows with source-aware live `pipeline_modes` (batch=live). Consolidator merged the per-VM shards
  cleanly.
  - **Residual (filed as P1 todos below): 30 defi-live `attempted_failed`** — `oracle_prices` Pyth-Hermes HTTP 400 ("Odd
    number of digits" = malformed feed-id query encoding) + some dex subgraph failures. Core path works; these are
    per-feed bugs, not a pipeline outage.
- **Live measured per AG (consolidated `_index`, captured-with-rows):** cefi 85 captured live rows; tradfi 7 captured;
  sports 6 captured; **prediction 68,314 live rows but ALL `empty_confirmed` / 0 captured** — a real live-capture BUG
  (see P0 below), NOT market-quiet.
- **Batch max-captured-date per AG (gap to T-1=2026-06-22):** defi 2026-06-22 (CURRENT ✅); cefi 2026-06-20 (2d); tradfi
  2026-06-18 (4d); sports 2026-06-09 (13d); prediction 2026-05-22 (32d). Batch-gap backfills tracked as P0/P1 todos
  below.

### 2026-06-23 (continuous-flow session — verified state + residual ownership)

Closing state after the live+batch sweep (consolidated `-prd-` `_index`, measured):

**LIVE producers (PART A):**

- **defi ✅ NOW CAPTURING** — 7 captured live rows / 128,642 rows, modes `live_onchain_subgraph`+`live_chainlink`+
  `live_pyth_hermes`, heartbeat emitting. **Seam-free continuity proven**: the 4 live-relevant defi `data_types`
  (`dex_pool_state`/`dex_pool_swaps`/`lst_rates`/`oracle_prices`) carry BOTH `batch_*` AND `live_*` rows in the same
  `_index` (batch=live, same schema). The was-empty MAIN gap is closed.
- **cefi/tradfi/sports ✅** — live VMs healthy (PIPELINE_HEARTBEAT + per-VM shards updating 60s); cefi 85 / tradfi 7 /
  sports 6 captured live rows in consolidated `_index`.
- **prediction ⚠️ live RUNNING + heartbeat but 0 captured (68,314 empty_confirmed)** — see P0 todo above. Root cause
  fully diagnosed: (1) the 4 running prediction-live VMs were launched 2026-06-22 20:12Z, PREDATING the `_is_universe`
  honest-skip fix (mtds@9447c71, committed 2026-06-23 08:37Z, now in the 09:42Z tarball); (2) MORE FUNDAMENTAL — the IS
  prediction instrument-availability universe
  (`instrument_availability/by_date/.../venue=POLYMARKET/instruments.parquet`) is STALE at max `day=2026-05-22` across
  all cqg groups with NO `clob_token_ids` column populated for current days, so the live runner's `day>=today` filter
  finds NO active token-id universe → honest empty. The `expected-universe-v2-prediction` Cloud Run job (triggered this
  session, Completed) only seeds `_index` expected_unattempted from
  `gs://instruments-store-pred-prd-…/prod/catalog.parquet` — it does NOT write the token-id `instrument_availability`
  parquet; the `lifecycle-catalogue-regen-prediction-daily` job that would is PAUSED. **This is the deep IS-write-path
  blocker the dedicated plan `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` documents** (its "needs a
  focused fresh-context IS session" line + the env-short `instruments-store-pred-prd-` vs env-less
  `instruments-store-prediction-` bucket split to confirm). Owned there; relaunching the live VMs alone won't fix it
  without a fresh-today token-id universe.

**BATCH continuity (PART B) — recent-window gaps, gated behind the running backfill fleet's singleton locks:**

- defi batch is CURRENT (max 2026-06-22). cefi 2026-06-20 (2d) / tradfi 2026-06-18 (4d) / sports 2026-06-09 (13d) /
  prediction 2026-05-22 (32d).
- **tradfi daily forward cron is BROKEN** — `tradfi-fwd-daily-cron-*` run.log shows "tradfi-fwd cron fire FAILED rc=0",
  last actual fire 2026-06-21T15:43Z; the daily T-1 catch-up isn't launching → the 4-day gap. The recent-window
  re-backfill (`launch-tradfi-bf-cme-ohlcv-1m.sh --start-floor 2026-01-01` → `2026-01-01..2026-06-22` shards) is READY
  but the launcher's GLOBAL singleton lock REFUSES while the prior session's 2025 year-shard fleet is still RUNNING
  (Databento rate-ceiling design). So tradfi/sports/prediction recent-gap backfills are SERIALIZED behind the draining
  fleet — launch them once the running `tradfi-bf-*-2025` / `cefi-*` / sports-provider backfills finish.

**Residual (all tracked as P0/P1 todos above; none silently dropped):** prediction live IS-universe write-path (→
prediction-CLOB plan); tradfi-fwd cron repair + recent-gap re-backfill (lock-serialized); sports/prediction recent batch
gap; defi oracle Pyth-Hermes HTTP-400; defi `*/5` forward-poll Cloud Scheduler (terraform `enable_defi_forward_poll`
default=true but the `defi-fwd-*-poll` jobs are not deployed — needs an operator-grade `terraform apply` with the proper
remote-state backend, NOT a blind local apply).

### 2026-06-22 (canonical-form session audit) — this session's backfills wrote CANONICAL data; one writer-bug residue (blank asset_group), NO migration needed

Operator dispatch: backfills that ran THIS SESSION before the canonical fixes landed may have written NON-CANONICAL data
— AUDIT (read-only, all AGs) then migrate only what's needed + safe.

**STEP 1 — ASSESS (read-only, all 5 AGs).** Ran `market_tick_data_service/scripts/audit_canonical_form.py` (CF-1..CF-7)
against each AG's CANONICAL consolidated `-prd-` `_index/availability_index.parquet` (all fresh, consolidator ran
21:01–21:02Z; defi 4.06M / cefi 3.91M / tradfi 6.81M / sports 1.76M / prediction 142k rows). Then a **session-scoped**
pass isolating rows with `written_at|attempted_at == 2026-06-22` (the session's writes) vs the legacy baseline.

- **This session's CAPTURED writes are CANONICAL across the board.** `schema_version=9` = 100% of session writes in
  EVERY AG (zero sub-v9); blank `pipeline_mode` = 0 captured; blank `source` = 0 captured; no glued `PROTOCOL-CHAIN`
  venue in defi/tradfi/sports/prediction.
- **CF-7 cefi `BINANCE-FUTURES`/`BYBIT-FUTURES`/… is a FALSE POSITIVE** — the audit's `_VENUE_CHAIN` regex
  (`^[A-Z0-9_]+-[A-Z]+$`) is defi-shaped; cefi venues carry a CANONICAL market-type suffix
  (`venue_constants.py:12 BINANCE_FUTURES="BINANCE-FUTURES"`). 27 session live rows under those venues are canonical. No
  migration.
- **The sub-v9 / blank-source / blank-pm counts the whole-corpus CF audit reports (cefi 131k sub-v9, defi/tradfi blank
  pm/source, prediction 1,454 sub-v9) are PRE-EXISTING legacy** (the ongoing `*_manifest_canonicalisation` walk +
  empty/expected_unattempted rows) — NONE are in this session's captured writes.
- **The ONE genuine session-written defect — blank `asset_group` on captured rows** (filed as the new P1 todo above):
  defi **61,989** (`swaps_ohlcv_*`, MDPS `batch_onchain_subgraph`) + cefi **1,515** (HYPERLIQUID `batch_hyperliquid`).
  Root cause = a per-VM manifest shard written WITHOUT the `asset_group` column (defi: `mdps-defi-2025-20260622-074035`;
  `df.columns` lacks `asset_group`) → consolidates as `asset_group=NaN`. Every other field on these rows is canonical +
  `row_count>0` (real data).

**STEP 2 — MIGRATE: deliberately NOT performed (it would be non-durable + unsafe).** (1) An index-only `asset_group`
re-stamp is **transient** — the live consolidator re-merges the column-less per-VM shard every tick and re-blanks it;
the durable fix is the WRITER (MDPS swaps_ohlcv shard must emit the `asset_group` column) → filed as a tracked code
todo, not a data migration. (2) **Live/active writers are producing RIGHT NOW** — cefi per-VM shards timestamped
20:23Z/20:27Z + live mtds shards (mtime < minutes); per the mission's liveness rule I do NOT migrate actively-written
defi/cefi cells. (3) cefi self-heals (fresh HL shards stamp `asset_group=cefi`); defi needs the writer fix then
re-consolidation. No `_index` was mutated → no snapshot needed (read-only audit; zero collision with the live writers +
the peer DeFi agent).

**Conclusion (no over-claim):** this session's backfills did NOT write the bad-data classes the dispatch worried about
(non-canonical venue / sub-v9 / blank source/pm / wrong-env bucket / glued paths) — those are all either pre-existing
legacy or false positives. The single real residue is a blank-`asset_group` WRITER bug (73.5k captured rows, defi+cefi),
which is a code fix (now tracked), not a safe/durable data migration. Audit scripts: `/tmp/session_scope_analyze.py` +
`audit_canonical_form.py` (the latter is the committed CF tool).

### 2026-06-22 (autonomous, continuous-paper FINISH dispatch) — blocker #1 was a MISDIAGNOSIS; item A LANDED; B2 design locked

Resumed the "make DeFi paper trading run continuously like live" dispatch. **FIRST TASK (blocker #1) RESOLVED — it was
NOT a fleet QG-harness coverage defect.** The prior session's "rootdir: unified-trading-pm, collected 6 → false 32.69%"
is the **intentional `PM_INT_TEST` integration check** (base-service.sh runs
`…/tests/integration/test_pm_scripts_integration.py` against PM by design; the MAIN unit run streams to a tempfile +
passed = 5289 collected). The REAL local-QG failures on the staged mtds change were: (1) a missing
`# noqa: qg-deep-import` on the new `from unified_trading_library.events import emit_pipeline_heartbeat` lines (the
checker treats `…events import X` as a deep import of `unified_trading_library`; `emit_pipeline_heartbeat` is NOT
top-level re-exported so the canonical pattern is the single-line import + `# noqa: qg-deep-import`, exactly as the
green `tick_data_handler.py:39`); (2) ruff I001 wrapped the line >120c when my noqa carried prose → moved the marker off
the `from` line → re-broke the checker (fix: short bare `# noqa: qg-deep-import`); (3) `oracle_prices_handler.process()`
grew to 53L (>50 limit) → trimmed comments to 48L. **Conclusion: python service repos quickmerge locally fine — no
`base-service.sh` change needed.**

- **A. mtds live pipeline_mode + DeFi-live heartbeat — ✅ LANDED `market-tick-data-service@3f5c61f9`** (origin/LDR; full
  `quality-gates.sh --no-fix` exit-0, content sentinel verified; quickmerge ff-rebased 368c488b→83b4a833, files
  byte-identical). `--mode live` now writes `pipeline_mode=live_*` on dex_pools/dex_swaps/oracle_prices AND emits a
  per-shard `emit_pipeline_heartbeat` on the live forward-poll path. Subsumes the old "(c) heartbeat deferred" TODO.
- **B2 DESIGN LOCKED (building next):** strategy-service new `--operation paper-stream --mode paper` = a bounded loop
  (`--stream-duration-seconds` + `--stream-interval-seconds`) that each tick calls the EXISTING
  `run_paper(client_id=…, start_date, end_date, run_id=STABLE)` against a window ending TODAY (so continuous-capture
  fills drive fresh trades), writing to a STABLE per-day run_id `paper-stream-{ag}-{YYYYMMDD}` under a **SEPARATE client
  `firm-paper-stream`** (NOT `firm-paper-determinism` — `daily_ledger_digest.py` uses `resolve_canonical_run`, so a
  same-client stream would HIJACK the determinism digest's run resolution; separate client = full isolation of the ε=0
  proof). The existing `/paper-trading` page is **client-parameterised** (`searchParams.get("client")`) + already
  5s-polls (B3 shipped), so `/paper-trading?client=firm-paper-stream` renders the live stream with ZERO UI change.
  `run_paper` already accepts an explicit `run_id` (default `paper-{ts}-{uuid8}`); `paper-stream-…` sorts
  lexicographically newest → canonical for its client. batch=live preserved (each tick is a deterministic run; loop
  timing is operational, never in the ledger). Deploy as a Cloud Run job (deployment-service), distinct from
  `uts-prod-paper-engine-run-cron` (untouched).

### 2026-06-22 (autonomous, continuous-paper dispatch) — B1 capture + B3 UI live-feed shipping; B2 engine next

Operator dispatch: "make DeFi paper trading run CONTINUOUSLY like it's live" (continuous on-chain data → streaming paper
engine → existing UI live). Substrate mapped by 3 Explore agents. Status:

- **B1 (continuous DeFi capture) — deployment-service LANDED `deployment-service@2e396f8`** (on origin/LDR):
  parameterized `scripts/vm/launch-defi-forward-poll.sh` over `--operation` (collect-dex-swaps/dex-pools/oracle-prices +
  the existing lst-rates), per-op singleton lock, + NEW `terraform/gcp/defi_forward_poll_scheduler.tf` = a `*/5` Cloud
  Scheduler firing the forward-poll for the 3 price-sensitive ops, gated by new var `enable_defi_forward_poll` (default
  true). Slow ops (lst-rates/lending-indices) stay daily. QG-green (114s).
  - **mtds pipeline_mode live-tag fix WRITTEN + test-green (5243 passed) but local quickmerge BLOCKED by the known
    QG-harness coverage mis-root** (`rootdir: unified-trading-pm, collected 6 items` → false 32.69% coverage, plan P3.1
    fleet defect; server `quality-gates-v2` is authoritative). Files staged in clone:
    `market_tick_data_service/cli/handlers/{dex_pools,dex_swaps,oracle_prices}_handler.py` +
    `tests/unit/test_dex_pools_handler.py`. The fix: live runs wrote `pipeline_mode=batch_*` because the parquet write
    used `run_tag` (defaults batch, independent of `--mode`); now folds `runtime.mode` into `_run_tag` so `--mode live`
    → `live_*`. **TODO P1: land this once the coverage-harness mis-root is fixed (or via server gate).** Heartbeat
    (`emit_pipeline_heartbeat`) on the DeFi live path deferred (UTL top-level export or sanctioned noqa) — **TODO P2**.
- **B3 (UI live feed) — LANDED `unified-trading-system-ui@a67e3c34`** (origin/LDR, QG+pw:L2 69-pass green). **Prod
  odom-portal deploy BLOCKED in this env:** the SA lacks `serviceusage.services.use` on
  `central-element-323112_cloudbuild` → `gcloud builds submit` forbidden (operator/CI must deploy the image; code is
  landed regardless). `unified-trading-system-ui`: ledger React-Query hooks already polled 30s; introduced DRY
  `LIVE_LEDGER_REFETCH_MS=5000` (+`*2` for heavy rollups) + `refetchIntervalInBackground` + `staleTime:0` so the
  existing `/paper-trading` page refreshes ~5s (near-real-time); added a "LIVE • updated Ns ago" indicator + a
  regression smoke (`tests/smoke/paper-trading-ledger.smoke.spec.ts`, fails if reverted to 30s). pw:L2 ✓ (69 passed).
  **ALSO fixed the UI capability-verdict-matrix parity drift** (= P2.11.20 UI half):
  `public/ capability-verdict-matrix.json` was stale at 57 archetypes (no TSMOM_BTC_CTA) vs UAC 58 → copied UAC
  byte-identical + bumped `tests/unit/wizard/parity-gates.test.ts` 57→58. This unblocked ALL UI ships (the UI repo QG
  was red on LDR).
- **B2 (continuous streaming paper engine) — NOT STARTED (design locked).** Minimal safe path: a new strategy-service
  `--operation paper-stream --mode paper` = a bounded loop (duration+interval) that each tick calls the EXISTING
  `run_paper` machinery against the latest rolling window, writing to a STABLE continuous `run_id` (e.g.
  `paper-stream-{ag}-{date}`) so the CRA `resolve_canonical_run` keeps resolving it + the UI (now 5s-poll) renders it
  live. Reuse ALL existing ledger writers + canonical InstrumentKey (NO new metadata maps). DISTINCT from the daily
  determinism run (different op + run_id; do NOT touch `uts-prod-paper-engine-run-cron`). batch=live preserved (each
  tick is a deterministic run). Deploy as a Cloud Run job / scheduled. Repos: strategy-service (+deployment-service
  job).
- **Deploy steps owned by parent (no fire-and-forget):** (1) `terraform apply` `defi_forward_poll_scheduler` in
  `deployment-service/terraform/gcp/` (target the new scheduler + var); (2) manual one-shot verify:
  `bash deployment-service/scripts/vm/launch-defi-forward-poll.sh --operation collect-oracle-prices` → T+10min check
  rows land at
  `gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=<today>/pipeline_mode=live_*/asset_group=defi/`;
  (3) odom-portal UI deploy `cd unified-trading-system-ui && bash scripts/deploy-cloud-run.sh --env=prod --cloud`.

### 2026-06-22 — GAP (operator): paper trading is DAILY-recon + 15-min-signal, NOT continuous/block-level

Operator: even for PAPER we want >daily (block-level) trade/position updates + UI at that rate. Found: the deployed
paper engine is PRODUCTION `strategy-service:latest` (NOT e2e-testing; e2e has only the run-paper.sh smoke). Cadence:
`uts-prod-paper-engine-run-cron 0 2 * * *` (DAILY, `--mode paper --rolling-days 7`, `purpose=paper-week-determinism` =
the citadel paper==batch ε=0 RECONCILIATION, not a live trader) + `paper-signal-engine-15m */15`. So paper trades/
positions update 15-min (signals) / daily (recon), NEVER block-level. Cadence cascade for block-level paper (the
operator vision): (1) continuous market data [DeFi daily-batch gap above]; (2) a CONTINUOUS/streaming paper engine
consuming the live tick/block stream + booking positions per-tick — distinct from the daily determinism job; (3) UI
(DART/deployment-ui) streaming trade/position updates at that rate. None exist today. Relates to
citadel_paper_batch_live_reconciliation_2026_06_19.md (the determinism spine; this is the LIVE- continuous companion).

- [x] ✅ [INFRA] P1. **Continuous (block/tick-level) paper-trading engine + UI — CODE COMPLETE 2026-06-22** (both halves
      shipped; only the operator/CI deploy remains, tracked as the new `[INFRA] P1 deploy` todo below). **UI HALF**
      `unified-trading-system-ui@a67e3c34` (5s-poll `/paper-trading`, client-parameterised by `?client=`). **ENGINE HALF
      (B2) SHIPPED** — `strategy-service@5557e7ef` (new `--operation paper-stream --mode paper`: a bounded loop
      [`--stream-duration-seconds`/`--stream-interval-seconds`] re-running the EXISTING `run_paper` each tick over a
      window ENDING TODAY, writing a STABLE per-UTC-day run_id `paper-stream-{ag}-{YYYYMMDD}` under a SEPARATE client
      `firm-paper-stream`; `stream_window_dates`/`stream_run_id` helpers + 11 unit tests; QG-green) +
      `deployment-service@ae9d6e6` (registered the `paper-stream` Cloud Run job [PAPER umbrella] +
      `paper_stream_scheduler.tf` — hourly self-healing 55-min loop). batch=live preserved (each tick is a deterministic
      `run_paper`; loop cadence is operational, never in the ledger). The determinism client
      (`firm-paper-determinism`) + `daily_ledger_digest` are UNTOUCHED (separate client → `resolve_canonical_run`
      isolation). The existing 5s-poll page renders it live at `/paper-trading?client=firm-paper-stream` with ZERO UI
      change. **Prod UI deploy BLOCKED here:** this env's SA lacks `serviceusage.services.use` on
      `central-element-323112_cloudbuild` → `gcloud builds submit` forbidden; the odom-portal image deploy is an
      operator/CI step. Beyond the daily determinism run: a streaming strategy-service paper mode that consumes the live
      market-data stream (per CeFi live VMs + the new DeFi continuous capture) and books trades/positions per-tick,
      emitting block-level updates the UI (DART) renders live. **Depends on the DeFi continuous-data P1 (item below).**
      CeFi-only partial implementation is possible (CeFi live VMs ARE running), but the `arbitrage_price_dispersion`
      archetype requires DeFi continuous data. Repos: strategy-service + unified-trading-system-ui + deployment-service.
      SSOT: citadel_paper_batch_live_reconciliation_2026_06_19.md (determinism) + this (live-continuous). **UI EXISTS —
      feed it, don't build it**: the page is `unified-trading-system-ui/app/paper-trading/{ledgers, coin/[coin]}` + DART
      (`components/dart/`); today it renders the DAILY paper-run output. Continuous mode = the live- paper engine writes
      the 4 ledgers (Instruction/Position/Passive/Pricing) + PnL per-tick → this existing page polls/ streams them
      real-time (block-level trades/positions/PnL), SAME page, just a live feed. Daily determinism recon stays untouched
      alongside. Unblocked once DeFi continuous-data P1 ships.

- [x] ✅ [INFRA] P1 deploy (C). **[DeFi pipeline ✅ VERIFIED 2026-06-23 · paper-stream ✅ DEPLOYED+VERIFIED 2026-06-23
      (operator-creds slot)] Deploy + verify the continuous DeFi pipeline + paper-stream** — **PAPER-STREAM DONE**:
      rebuilt+pushed `strategy-service:latest`=`sha256:ec8eafef…` (`0.36.0,a7991b78`, Cloud Build `6589c139`) carrying
      the B2 `--operation paper-stream` op + 2 fixes shipped this session: (i) cloudbuild operability-probe
      `CLOUD_MOCK_MODE=true` `strategy-service@8b68cd3d` (was deterministically failing EVERY strategy-service image
      build since 06-21 — nested `docker run` can't reach metadata → GcsEventSink STARTED ConnectTimeout at step 8;
      canonical ml-service pattern restored); (ii) `run_id` `paper-stream-['DEFI']-…`→`paper-stream-defi-…` bug +
      regression test `strategy-service@f6ef1d2b` (`_cli_asset_group` is a LIST, `str(list)` embedded the Python repr).
      `tofu apply -target=module.paper_stream_job.google_cloud_run_v2_job.job -target='google_cloud_scheduler_job.paper_stream_cron[0]'`
      vs prod state (`terraform/state/prod`) → Cloud Run job `uts-prod-paper-stream` + hourly cron
      `uts-prod-paper-stream-cron` (ENABLED `0 * * * *`). Manual exec `uts-prod-paper-stream-vmspv` (fixed image)
      verified RUNNING, **no crash-loop @ T+10** (0 FAILED / 3 execs), writing
      `gs://central-element-323112-client-reports/ledger/client_id=firm-paper-stream/run_id=paper-stream-defi-20260623/`
      = `run_manifest.json` + all 4 ledgers (instruction tape growing live 4.85kiB / passive / pricing / transfer),
      DISTINCT client from `firm-paper-determinism` (`resolve_canonical_run` isolation intact).

      Residual NON-paper-stream sub-parts: (b) VM-tarball rebuild is for VM-mtds (defi-live already verified without
                                                                                                                  it); (c) odom-portal UI image auto-promotes via LDR→staging→main→image CI (NOT a manual blocker; UI code
                                                                                                                  landed `unified-trading-system-ui@a67e3c34`). (the CODE is all landed: mtds live-tag
                                                                                                                  `market-tick-data-service@3f5c61f9`, B1 forward-poll IaC `deployment-service@2e396f8`, B2 paper-stream engine
                                                                                                                  `strategy-service@5557e7ef` + job/scheduler `deployment-service@ae9d6e6`). Remaining operational steps + WHO
                                                                                                                  can run them in this env (SA = `unified-trading-sa@central-element-323112`, NOT GCP-admin — proven:
                                                                                                                  `projects.getIamPolicy` denied): (a) **`tofu apply -target` the schedulers**
                                                                                                                  (`defi_forward_poll_scheduler.tf` + `paper_stream_scheduler.tf`, both gated by `enable_*`/`paper_stream_enabled`
                                                                                                                  default-true) — **operator/CI** (no `tofu`/`terraform` binary in this slot env; the deployment-service CI
                                                                                                                  applies it). (b) **`create-code-tarballs.sh` rebuild from clean LDR** so the mtds live-tag fix + the
                                                                                                                  paper-stream engine reach launched VMs/jobs — **runnable by this SA** (GCS-writable) once the workspace clones
                                                                                                                  are clean.

                                                                                                                  (c) **odom-portal UI image deploy** (`bash scripts/deploy-cloud-run.sh --env=prod --cloud`) — **operator/CI**:
                                                                                                                  this SA lacks `serviceusage.services.use` on `central-element-323112_cloudbuild` → `gcloud builds submit` is
                                                                                                                  FORBIDDEN (the ONE genuine IAM-denied step, surfaced to the operator; the UI code is landed
                                                                                                                  `unified-trading-system-ui@a67e3c34` and rides the normal LDR→staging→main→image CI path on promotion
                                                                                                                  regardless). (d) **manual one-shot proof of the live capture**
                                                                                                                  (`bash deployment-service/scripts/vm/launch-defi-forward-poll.sh --operation collect-oracle-prices`) —
                                                                                                                  **runnable by this SA** (compute-capable) → T+10min check rows at
                                                                                                                  `gs://market-data-tick-defi-prd-…/raw_tick_data/by_date/day=<today>/pipeline_mode=live_*/asset_group=defi/`;
                                                                                                                  needs a fresh tarball (b) first or the launched VM runs the OLD batch-tag mtds. Repos: deployment-service + (CI)
                                                                                                                  unified-trading-system-ui.

- [x] ✅ [INFRA] P2 — paper-trading UI cold-start latency **FIXED 2026-06-23 (autonomous tick-1)**: set `minScale=1` on
      Cloud Run `odum-portal` + `client-reporting-api` (asia-northeast1) via
      `gcloud run services update --min-instances=1` — VERIFIED warm (odum-portal `/paper-trading`=0.61s, CRA
      `/health`=0.42s; was multi-second cold) + the previously stuck panels now RENDER (`loadingCount=0`: **P&L
      Attribution** shows real data [By factor CARRY $38/FEES $-81; By venue UNISWAP_V3 $-16/DERIBIT $-27; By layer],
      Data-quality 3/345 drivable) — so the **attribution "stuck Loading…" was 100% cold-start, cured by the warm fix
      (no CRA "empty-not-error" code change needed)**. Durable: `deploy-shared.sh:223` already passes
      `--min-instances=1`, `gcloud run deploy` preserves the flag on image redeploy, and no deploy path forces `=0`.
      (us-central1 secondary/staging UIs left at 0 — not the operator's surface, warming them is needless cost.)
      Original finding:
- [x] ✅ ~~[INFRA] P2 **NICE-TO-HAVE**~~ **(superseded by the ✅ FIXED above — minScale=1 on odum-portal +
      client-reporting-api, verified warm 2026-06-23)** — paper-trading UI cold-start latency original finding
      (discovered 2026-06-23 deploying B2). The live `/paper-trading?client=firm-paper-stream` book is SLOW on first
      load after idle — NOT a network issue. Root cause: both `odum-portal` (Next.js UI) AND `client-reporting-api` (CRA
      backend) run on Cloud Run with **`min-instances=0`** → they scale to zero and cold-start on the first request. The
      CRA is the worst offender (Python + the heavy UTL import chain + 2Gi → multi-second boot). The paper-trading
      panels async-fetch the CRA via the Next rewrite `/api/client-reporting/:path* → CRA /api/v1/:path*`, so a cold CRA
      makes the panels spin for many seconds. **Proof it's cold-start not network**: when warm, `/paper-trading`=~0.4s,
      CRA `/health`=~0.3s, DNS/connect=ms. **Fix**: set `minScale>=1` (keep ≥1 warm instance) on `odum-portal` +
      `client-reporting-api` in their Cloud Run config / deploy scripts
      (`unified-trading-system-ui/scripts/deploy-cloud-run.sh` + the CRA service) — trade-off is a small always-on cost;
      operator decides. Repos: deployment-service (Cloud Run config) + unified-trading-system-ui (UI deploy).
      Provenance: B2 paper-stream deploy session 2026-06-23.
- [x] ✅ [DATA] P1 **paper-trading DeFi ledger 0x→canonical symbols — FIXED + LIVE-VERIFIED 2026-06-23 (autonomous
      tick-2)**: `strategy-service@81d9dba2` (DeFi LP/vault engines now book the leg on the catalog spec's canonical
      `symbol` — yvUSDC/sUSDe/sDAI — not the 0x pool/vault address; feature feeds keep the address) + image rebuilt
      (`0.37.0`/`c9953c4a`) + paper-stream re-executed. **VERIFIED in the live `firm-paper-stream` instruction ledger
      (mtime 2026-06-23T19:03:49Z)**: `asset_symbol=yvUSDC/sUSDe/sDAI`, `instrument_key=YEARN_V3:DEX_POOL:yvUSDC` /
      `ETHENA:DEX_POOL:sUSDe` / `MAKER:DEX_POOL:sDAI` — NO `0x`; `strategy_id` = full canonical slug
      `DEFI_LP_VAULT@yearnv3-yvusdc1-ethereum-usdc-v2-prod`. (Verification gotcha logged: an early/transitional ledger
      read at 18:41 still showed the address — re-reading the climbing metric at 19:03 confirmed the fix; don't conclude
      a stall from one early read.) **Residual SHIPPED 2026-06-23 (autonomous):** the faithful live-path regression test
      (`tests/unit/cli/handlers/test_paper_run_vault_symbol_live_path.py`) landed `strategy-service@4bf16796` (version
      drift cleared — local==main 0.37.0; QG-green, the test PASSES against current HEAD, proving the tick-2 live-path
      symbol fix is genuinely in the code, not just the engine-only unit path). Original finding:
- [x] ✅ ~~[DATA] P1~~ **(superseded by the ✅ above — strategy-service@81d9dba2, live-verified 2026-06-23)**
      paper-trading DeFi ledger shows RAW 0x addresses, not canonical symbols (found 2026-06-23 deep-dive of
      `/paper-trading?client=firm-paper-stream`). The Net-in-coin / Delta-per-coin tables, the instruction-ledger
      "Strategy" column, and the PnL-by-strategy snapshot all render raw DEX-pool contract addresses
      (`0xBe53A1…`/`0x9D39A5…`/`0x83F20F…`) instead of canonical token symbols (yvUSDC / sUSDe / sDAI) — while the
      drilldown dropdown DOES show canonical strategy slugs (`@yearnv3-yvusdc1-ethereum` etc). So the DeFi paper-run
      InstrumentKey→`asset_symbol`/`asset_canonical_id`/`strategy_id` derivation (`derive_ledger_asset_fields`, UAC
      `internal/reference/ledger_asset_resolution.py`) is NOT resolving DEX-pool addresses to symbols — it falls back to
      the raw 0x; the instruction "Strategy" column = the pool ADDRESS, not the canonical strategy id. Violates the
      batch=live "derive from canonical InstrumentKey, never raw" HARD RULE. Repos: strategy-service (`paper_run_emit` /
      ledger writer) + UAC (DeFi DEX-pool asset resolution). Provenance: B2 deep-dive 2026-06-23.

      - **PARTIAL (autonomous 2026-06-23, NOT yet landed in the live ledger — stall-safety stop):**
                                                                                                                    `strategy-service@81d9dba2` shipped + image `c9953c4a` (`0.37.0`) rebuilt + paper-stream re-executed. FIXED:
                                                                                                                    `strategy_id` now writes the full canonical slug `DEFI_LP_VAULT@yearnv3-yvusdc1-ethereum-usdc-v2-prod` (was
                                                                                                                    the address). The catalog spec (`catalog_yield_defi.py` `DEFI_LP_VAULT`/POOL/CONCENTRATED) now carries a
                                                                                                                    canonical `"symbol"` (yvUSDC/sUSDe/sDAI/…); the engine (`engine/strategies/v2/defi_lp/vault.py:116,175,219`)
                                                                                                                    emits `AtomicLeg.instrument = self.params.get("symbol") or vault_address`; a unit test asserts the
                                                                                                                    engine→`compute_benchmark_fill`→`trade_fill_records`→`derive_ledger_asset_fields` chain → `yvUSDC`. QG-green.

                                                                                                                  **STILL OPEN — the live ledger row STILL emits `asset_symbol=0xBe53…` / `instrument_key=YEARN_V3:DEX_POOL:0x…`**
                                                                                                                  after a fresh tick on the rebuilt image (verified via `gcloud storage cat` the instruction `.jsonl`, mtime
                                                                                                                  confirmed = new tick). Root remaining gap: at RUNTIME `self.params["symbol"]` is EMPTY for the live strategies →
                                                                                                                  engine falls back to the address. The catalog + engine + unit-test path are all correct, so the gap is the
                                                                                                                  **spec.initial_config["symbol"] → engine.params propagation** in the GroupBRunner/paper_run replay
                                                                                                                  instantiation, OR the running paper-stream strategies carry **stale registered config** (registered before the
                                                                                                                  `symbol` was added → need re-registration / fresh spec load).

                                                                                                                  NEXT: trace how `_load_dex_lp_ticks`/`_load_*_vault` + GroupBRunner build the engine's `params` from the spec
                                                                                                                  and confirm `symbol` reaches `engine.params`; add a test that exercises the LIVE replay path (paper_run →
                                                                                                                  emitted ledger row), asserting `"0x" not in` the row's `instrument_key` (the unit test covered the engine path,
                                                                                                                  not the replay path, so it passed while live failed).

- [x] ✅ [UI] P2 **NICE-TO-HAVE — wire candle+trade-triangle chart + coin-drilldown link into live paper-trading** —
      **SHIPPED + LIVE-VERIFIED 2026-06-24: `unified-trading-system-ui@44790f93` (`CoinPriceChart`
      candle+entry/exit-triangle component on `/paper-trading/coin/[coin]` + overview→coin drilldown `<Link>`s) +
      `e2e-testing@aef3294` (`_coin_history.py` emits per-coin daily-close `price_series`; live in GCS for all 31
      coins). pw:L2 ✓ (76 passed) | regression: `tests/smoke/paper-trading-coin-chart.smoke.spec.ts` | LIVE:
      `coin-price-chart` testid confirmed in deployed `odum-portal-00042-fhj` prod bundle (asia-northeast1).** (found
      2026-06-23). The candle-with-trade-markers chart EXISTS (`components/trading/candlestick-chart.tsx` +
      `components/research/signal-overlay-chart.tsx` with `setMarkers` triangles, lightweight-charts v5) but only in the
      RESEARCH/backtest surface — the live `/paper-trading` overview + per-coin page (`/paper-trading/coin/[coin]`,
      recharts Area/Scatter + filled/missed counts) do NOT render the underlying-price candle with entry/exit triangles,
      and the overview tables do NOT link to the per-coin drilldown (no click-through). Also: wallet movements are a
      TABLE only (no per-venue/per-strategy graph), and the P&L-Attribution panel sits on "Loading…". Repos:
      unified-trading-system-ui. SSOT: citadel_paper_batch_live_reconciliation_2026_06_19.md. Provenance: B2 deep-dive
      2026-06-23.
- [x] ✅ [UI] P1 **paper-trading is OUTSIDE the platform nav shell — 3 sub-routes only cross-linked by inline text**
      (found 2026-06-23, operator UX complaint). `app/paper-trading/` has NO `layout.tsx` → it renders under the ROOT
      layout, NOT the `(platform)` shell (vertical-nav / site-header / `service-tabs`). So inside paper-trading there is
      NO persistent tab/banner; the 3 pages (`/paper-trading` overview, `/paper-trading/ledgers`,
      `/paper-trading/coin/[coin]`) are stitched only by inline `<Link>`s (overview→ledgers→coin), and the overview does
      NOT link directly to the coin drilldown. **Fix**: add `app/paper-trading/layout.tsx` with a tab bar (Overview ·
      Ledgers · Coins) + direct overview→coin links + bring paper-trading under/into the platform shell so it's
      reachable from the top nav like the rest. Repos: unified-trading-system-ui (UI playwright gate applies: pw:L2 +
      regression spec). Provenance: B2 deep-dive 2026-06-23. **CODE SHIPPED**: `unified-trading-system-ui@0dba2705` —
      moved `app/paper-trading/` → `app/(platform)/paper-trading/` (inherits platform shell) + added `layout.tsx` tab
      bar (Overview · Ledgers · Coins). TS+ESLint clean. **VERIFIED + flipped 2026-06-24 (`[BLOCKED-PLAYWRIGHT]` cleared
      — chromium-capable slot): pw:L2 ✓ (76 passed) | regression: `tests/smoke/paper-trading-nav-shell.smoke.spec.ts` |
      LIVE: deployed `odum-portal-00042-fhj` (asia-northeast1) — `/paper-trading` now 302-redirects to `/login` (i.e. it
      is under the `(platform)` auth shell, where it was previously public/root-layout), the direct behavioural proof
      the shell move landed in prod.**
- [x] ✅ [UI] P2 **research (historical/backtest) surface is MOCK-fixture-backed + not linked from paper-trading** —
      **SHIPPED + LIVE-VERIFIED 2026-06-24: `unified-trading-system-ui@44790f93` (research execution dialog de-mocked —
      `MOCK_STRATEGY_BACKTESTS` fixture deleted, now sources `useStrategyBacktests()` real hook + honest-empty fallback;
      research↔paper cross-links `research-to-paper-link` + `paper-to-research-link`). pw:L2 ✓ (76 passed) | regression:
      `tests/smoke/research-real-data.smoke.spec.ts` | LIVE: `paper-to-research-link` testid confirmed in deployed
      `odum-portal-00042-fhj` prod bundle.** (found 2026-06-23). Research IS routed at
      `app/(platform)/services/research` (inside the shell, nav-reachable), BUT the execution/backtest/features panels
      use `MOCK_STRATEGY_BACKTESTS` / `fixtures/build-data` — demo data, NOT real strategy backtest performance; real
      backtest hooks exist (`use-strategies`/`use-orders` `BacktestsResponse`) but the research equity/signal charts
      (`equity-chart-with-layers`, execution dialogs) are fed by mocks. And research is NOT reachable from the
      paper-trading pages (they're outside the shell). **Fix**: wire the research charts to the real backtest API (CRA
      `…/clients/{id}/backtest` + the gateway backtest hooks) and cross-link research ↔ paper-trading. Repos:
      unified-trading-system-ui (+ verify CRA backtest endpoint returns real data). Provenance: B2 deep-dive 2026-06-23.
- [x] ✅ [INFRA] P3 **NICE-TO-HAVE — consolidate `odum-portal` prod deploy to a single region (`asia-northeast1`) while
      it's internal-only** — `deployment-service@9b4d23b` (deploy-ui.sh prod fan-out → asia-northeast1 only; europe/us
      services left at min=0; option-a safe/reversible). **OPERATOR DECISION 2026-06-24 (FINAL): REVERTED `9b4d23b` →
      back to 3-region prod fan-out, `deployment-service@4f6421e` (with a corrected comment so it isn't re-consolidated
      blind).** Sequence: operator first chose KEEP (asia-only looked free/cleaner) — but tracing the public domain then
      revealed **`www.odum-research.com` routes via Firebase Hosting + the `odum-research.com` Cloud Run domain mapping
      to EUROPE-WEST4, NOT asia** (verified 2026-06-24: www + europe-direct return identical bodies). So asia-only
      deploys left the public www domain ONE DEPLOY STALE — the new coins-index page 404'd on `www/paper-trading/coin`
      while asia-direct + `portal.odum-research.com` (→asia) + UAT were all fresh. Operator then chose REVERT (3-region
      keeps every www-fronting region current; the
      ~~$0 cost was never the concern). Lesson: a single-region
      consolidation MUST first confirm where the public domain actually routes. **PROCESS NOTE (mis-file corrected):**
      this was first filed as a bare `- [ ]` while the operator's scope decision was still pending → the orchestrator
      backlog-regen auto-dispatched it (any open checkbox = actionable) and a worker shipped option-a BEFORE the
      operator chose; an operator-pending item MUST carry status `[BLOCKED-OPERATOR-DECISION]` (regen skips it), never a
      bare `- [ ]`. (found 2026-06-24, operator cost question during the B2 deploy). `deploy-ui.sh:146` fans the prod
      deploy out to 3 regions (`europe-west4` + `us-central1` + `asia-northeast1`), but only **asia-northeast1 is warm**
      (`min=1` — the cold-start fix) and is the ONLY region with a co-located `client-reporting-api` backend + the GCS
      data (all in Tokyo); `europe-west4` + `us-central1` `odum-portal` sit at **`min=0`** (scale-to-zero, ≈$0
      idle) with NO local CRA. So the 3-region layout already costs ≈ the single warm asia stack either way
      (~~$35–60/mo);
      consolidating saves deploy-simplicity (1× not 3× `gcloud run deploy`) + guarantees zero cross-region egress, NOT
      runtime $.
      **No global LB / serverless-NEG backend fronts `odum-portal`** (verified 2026-06-24 —
      `gcloud compute backend-services list --global` returns empty), so europe/us are not load-balanced;
      `www.odum-research.com` routing (domain-mapping vs DNS) must be confirmed before DELETING those services. **Fix
      (operator scope decision):** (a) SAFE/reversible — set `DEPLOY_REGIONS=("asia-northeast1")` for prod in
      `deploy-ui.sh` (stops the 3× fan-out, leaves idle europe/us at min=0); or (b) FULL — also delete the europe/us
      `odum-portal` Cloud Run services after confirming `www` routing. Repo: deployment-service
      (`scripts/cloud-run/deploy-ui.sh`). Provenance: B2 deploy session 2026-06-24.
- [x] ✅ [UI] P1 **follow-up bug from #2 (operator-reported 2026-06-24): the "Coins" nav-shell tab 404'd** — **FIXED
      `unified-trading-system-ui@8d33ce56`.** The finding-#2 `layout.tsx` tab bar pointed "Coins" →
      `/paper-trading/coin`, but that route had NO index page (only the dynamic `/coin/[coin]`), so the tab (and a
      direct hit) 404'd ("Page not found"). Added `app/(platform)/paper-trading/coin/page.tsx` — a coins index listing
      every coin in the book as a drilldown card (`coin-link-{coin}` → `/paper-trading/coin/{coin}`), reusing the
      overview's `/api/paper-trading` source + honest empty/error states. pw:L2 ✓ (**77 passed**, +1 new) | regression:
      `tests/smoke/paper-trading-nav-shell.smoke.spec.ts` ("the Coins tab resolves to the coins index (not a 404)") |
      VERIFIED: `/paper-trading/coin` → HTTP **200** (was 404) on the served prod `.next` build. Deploy to UAT
      (`odum-portal-staging`) + prod (`odum-portal`) in flight. Repo: unified-trading-system-ui. Provenance: operator UX
      report 2026-06-24.
- [x] ✅ [DATA] P1 **wallet transfers have NO per-strategy grain + NO cross-strategy netting (mover gap) — UI must not
      scope transfers "by strategy"** — **UI FIX SHIPPED 2026-06-23** `unified-trading-system-ui@c58bc608`: removed
      `strategyId` param from `useLedgerTransfers` + `TransfersPanel`; transfers panel now scopes by
      `client × venue × asset` (correct grain) with explanatory note. `IntraClientRebalanceCoordinator` backend
      **DEFERRED** to Phase E.3 (strategy-service, separate plan item below). Repos: unified-trading-system-ui.
      Provenance: B2 deep-dive 2026-06-23 (sub-agent code read). **Note**: backend netting deferred — see next item.
- [x] ✅ [INFRA] P1 **SHIPPED 2026-06-23 (autonomous)** — `IntraClientRebalanceCoordinator` landed
      `strategy-service@1450019e` (`strategy_service/transfer_coordinator.py` + 10 unit tests). The emit-time Phase-E.3
      coordinator nets N per-strategy intra-client transfers into ONE `TransferIntent` per
      `client × {unordered venue pair} × asset × transfer_type` (signed sum, drop zero-nets, bidirectional flows
      collapse to a single net-direction transfer; deterministic per-period `idempotency_key`), and raises
      `CrossClientTransferForbiddenError` on any cross-client `add_request` (defence-in-depth alongside the
      execution-service consume-time raise; logs the `CROSS_CLIENT_TRANSFER_FORBIDDEN` audit marker at ERROR for
      alert-on-attempt). Tests cover all 4 codex-mandatory cases (happy intra-client netting / structural
      single-`client_id` on every emitted intent / coordinator-rejects-cross-client / alert-on-attempt) + netting
      correctness (bidirectional cancel-to-zero, net-direction flip, transfer-type isolation, idempotency determinism).
      **No UAC change** — reuses the canonical
      `TransferIntent`/`BusTransferType`/`TransferPurpose`/`CrossClientTransferForbiddenError`. Codex updated
      (`client-funds-isolation.md` PLANNED→shipped). QG-green. **Note**: wiring the coordinator into a live per-strategy
      rebalance-emit loop is future work — strategy-service has no live transfer-emit pipeline today (transfers are
      consumed by execution-service's `TransferCoordinator`), so the shipped unit is the tested, importable netting +
      isolation primitive future rebalance code builds on. (The UI half of this finding — transfers panel scoped by
      `client × venue × asset`, not by strategy — was already ✅ above, `unified-trading-system-ui@c58bc608`.)
      Provenance: task-082 2026-06-23.
- [x] ✅ [INFRA] P2. **Wire `IntraClientRebalanceCoordinator` into strategy-service live transfer-emit loop**
      (strategy-service) — Phase E.3: wired. Added `RebalanceEmitPipeline` shim, `REBALANCE_PERIOD_TICK` IPC handler in
      `ClientWorker`, `enable_transfer_rebalancing` kwarg through `make_worker_target`, and `rebalance_pipeline` field
      on `ClientContext`. 9 new unit tests (pipeline disabled/enabled/isolation + IPC integration).
      `strategy-service@171758fe`. Provenance: task-090 2026-06-24.
