---
title: Data completion to 100% — all asset groups, batch + live, manifest v9 (MTDS + IS)
created: 2026-06-21
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: local-only # operator-owned 2026-06-21 — Ikenna drives this himself; orchestrator agents must NOT auto-dispatch its todos (they handle only CI/CD escalations + plan-health). Remove this line to re-enable agent dispatch.
estimate_class: infra
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 8
locked_by: live-defi-rollout
priority: P0
status: active
---

# Data completion to 100% — all AGs, batch + live, manifest v9

Operator 2026-06-21: drive MTDS market-data + IS reference-data to **100% honest-coverage across every asset group,
batch AND live, manifest v9** — and DON'T STOP until done. The **only** sanctioned exclusion is **batch Tardis (cefi
historical)** which gates on billing; **live Tardis is free → hook it up**.

## Measured snapshot 2026-06-21 (consolidated v9 `_index`, prd, central-element-323112)

| AG     | MTDS rows | MTDS v9% | MTDS honest-cov% | MTDS capture (cap/empty/failed/unattempted) | IS honest-cov%          | LIVE rows |
| ------ | --------- | -------- | ---------------- | ------------------------------------------- | ----------------------- | --------- |
| cefi   | 3.87M     | 96.6%    | **33.9%**        | 1.31M / 1.28M / **802k failed** / 482k      | 99.9%                   | **0**     |
| defi   | 6.17M     | 100%     | **6.0%**         | 369k / 3.48M / 6k / 2.31M                   | 100%                    | **0**     |
| tradfi | 1.94M     | 99.7%    | **5.3%**         | 103k / 1.01M / 10k / 818k                   | 96% (v9 only **46.6%**) | **0**     |
| sports | 920k      | 100%     | **37.7%**        | 346k / 574k / 164 / 0                       | **15.9%**               | **0**     |
| pred   | 42k       | 96.5%    | **40.5%**        | 17k / 24.5k / 50 / 338                      | 100%                    | **0**     |

**Three structural facts:** (1) **LIVE = 0 rows on every AG** (MTDS+IS) — the live/forward pipeline has never been
populated; (2) low defi/tradfi % is mostly `expected_unattempted`+`empty_confirmed` (writer- seeded honest absence — the
unattempted cells need batch runs to convert to captured); (3) cefi carries **802k `attempted_failed`** (needs
re-fetch/diagnosis). Fleet was DRAINED at snapshot time (only gas-fees + monitoring running) — nothing non-billing was
driving to 100%.

## Path to 100% — per-AG launch matrix (the fleet)

Each batch backfill fills `expected_unattempted` → captured; each forward-poll starts the LIVE stream (live accumulates
from launch, continuously). Launch with per-VM T+10min verify (no fire-and-forget).

- [x] [DATA] P0. **prediction** — Kalshi deep-history seed (bulk→canonical, IN FLIGHT: `mtds-prediction-kalshibulk-*`) +
      Polymarket batch re-fetch for `expected_unattempted` + `launch-prediction-forward-poll.sh` (LIVE). Repo:
      deployment-service. ✅ — VMs running: kalshi-seed=mtds-prediction-kalshibulk-20260621-135650,
      polymarket-batch=mtds-prediction-polymarket-20260621-140847 (2025-03-13→2026-06-20),
      fwd-poll=prediction-fwd-20260621-140902 (deployment-service@26af6dd)
- [x] ✅ [DATA] P0. **defi** — `launch-defi-backfill-vm.sh` (fill 2.31M unattempted: gas-fees [running] + lst-rates +
      dex-pools/swaps + lending-indices + liquidations + vault-share + pyth) + `launch-defi-forward-poll.sh` (LIVE).
      Repo: deployment-service. — deployment-service@49caaca | year-sharded VMs launched: gas-fees×6 (2020-26),
      lst-rates×7 (2020-26), dex-pools×6 (2021-26), dex-swaps×6 (2021-26), lending-indices×5 (2022-26), liquidations×6
      (2021-26), vault-share×6 (2021-26), pyth-archive×1 (2022-11→2023-09); forward-poll=STUB (skip). PATH fix required:
      export PATH="/snap/google-cloud-cli/current/bin:$PATH" before launcher calls. **LIVE PATH WIRED 2026-06-21**: stub
      replaced with real launcher (deployment-service@48d57a5); VM `defi-fwd-20260621-212906` launched
      (`collect-lst-rates --mode live`, e2-standard-8, `VM_TASK=defi-live-lst`,
      `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`, `MANIFEST_PER_VM_SHARDS=true`); T+10min verify pending.
- [x] ✅ [DATA] P0. **tradfi** — full 3-dataset batch (GLBX done via CME-b; **DBEQ.BASIC**
      `launch-tradfi-bf-nasdaq/nyse-ohlcv-1m.sh` + **CFE/XCBF**) to fill 818k unattempted +
      `launch-tradfi-forward-poll.sh` (LIVE). Repo: deployment-service. — deployment-service@f243eb4 | 17 VMs RUNNING
      (CME×7 2026, NASDAQ×4 2023-26, NYSE×4 2023-26, CBOE/XCBF×1 2026, tradfi-fwd×1 2026-06-20); VM_TASK=mtds-backfill +
      VM_SOURCE=databento + MANIFEST_PER_VM_SHARDS=true confirmed on all.
- [x] [DATA] P0. **sports** — `launch-mtds-sports-odds-backfill-vm.sh` + `launch-sports-is-gap-fill.sh` /
      `launch-sports-full-sweep-vm.sh` (IS sports 15.9%→100%) + `launch-footystats-forward-poll.sh` (LIVE). Repo:
      deployment-service. ✅ — VMs RUNNING (T+10min verified): odds-backfill=mtds-backfill-odds-{2020..2026} (7 VMs,
      chunk 1/31 writing rows), IS-sweep=sports-full-sweep-{2019..2026} (8 VMs, writing instruments-store parquets),
      fwd-poll=footystats-fwd-20260621-142249 (RUNNING). Bug fix: deployment-service@b42d98c (removed VM_TIER from
      sports MTDS launcher; --tier has no MTDS CLI arg)
- [x] [DATA] P0. **cefi — 802k `attempted_failed` TRIAGED** (CEFI lane 2026-06-21, measured from consolidated v9
      `_index`): by source — **tardis 753,341 + 22,519 phantom = 775,860 (96.7%) Tardis-gated** (batch_tardis;
      historical billing EXCLUDED → BLOCKED-CREDENTIALS) · **hyperliquid 30,835 + aster 17,675 = 48,510 free-venue
      re-fetchable** (native, no Tardis) · 124 misc. Re-fetchable failed cells span HL 2023-26 / ASTER 2024-26 across
      {trades, book_snapshot_5, derivative_ticker, liquidations}. Repo: deployment-service.
- [x] [DATA] P0. ✅ **cefi — re-fetch the 48.5k free-venue (HYPERLIQUID+ASTER) failed cells — DIAGNOSED, mechanism gap
      found (CEFI lane 2026-06-21).** Launched `launch-cefi-onchain-forward-poll.sh` HL+ASTER 2023/24→2026 → **NO-OP**:
      the cefi `--operation download` orchestrator STRIPS HL/ASTER (they're `defi` in `VENUE_TO_ASSET_GROUP`) even with
      explicit `--venues` (`Skipping 2 DeFi venues … use collect-* handlers` / `No active venues` for every date) → VMs
      deleted (no fire-and-forget). Actual HL batch source = **requester-pays S3** (`HyperliquidS3Downloader`,
      `_fetch_hyperliquid_s3`; `aws-hyperliquid-s3` secret EXISTS) + ASTER REST, routed via umi/onchain-perps, **but no
      launcher exists + the orchestrator defi-strip blocks the cefi download path**. The data_types (trades /
      book_snapshot_5 / derivative_ticker) are **live-WS-primary → now covered FORWARD by the launched mtds-live VM**. A
      genuine HISTORICAL re-fetch needs a dedicated HL-S3 / ASTER-REST batch launcher (+ resolve the HL cefi-vs-defi
      asset_group classification) — see
      `plans/active/issues/cefi_free_venue_historical_refetch_mechanism_2026_06_21.md`. Repo: deployment-service /
      market-tick-data-service. — uac@0d0e00a8 (defi_venues.py + defi_protocol_registry.py: remove HL/ASTER from
      ALL_DEFI_VENUES/DEFI_VENUE_PHASE/DEFI_VENUE_TO_PROTOCOL → VENUE_TO_ASSET_GROUP now maps both to "cefi") +
      deployment-service@8a027c0 (launch-cefi-hl-aster-historical-backfill.sh: 7 year-shards, HL 2023-26 + ASTER
      2024-26, cefi-hyperliquid-/cefi-aster- prefixes, requester-pays S3 + REST, registered in VM_PREFIX_TO_BUCKET)
- [x] [DATA] P0. **cefi — LIVE stream → ≥1 `live_<source>` row ✅ VERIFIED (cefi LIVE 0 → 1).** First-ever operational
      live MTDS run; cleared a 5-bug first-run chain (live mode had never run on ANY AG): (1) GCS setup-script
      transiently corrupted by a sync baking an uncommitted edit → fixed to clean deployment-service@efdb9df; (2)
      missing Pub/Sub lifecycle topic `market-tick-data-service-events` (UTL `_sink_factory` `{service}-events`) →
      created (unblocks live for ALL AGs); (3) topic IAM — granted `pubsub.publisher` to the compute SA; (4)+(5)
      `MTDSShardManifestRecorder._resolve_row_key` row_key bugs (`asset_group` not a row-key column + `"day"`→`"date"`
      per UTL `_ROW_KEY_COLUMNS`) → market-tick-data-service@46adace (slot-3 shipped the equivalent fix to LDR; I
      deployed it via the mtds tarball). **Evidence:** `mtds-live-cefi-hyperliquid-trades-20260621-155352` per_vm shard
      `gs://market-data-tick-cefi-prd-…/_index/per_vm/…155352.parquet` @15:57Z holds a row
      `venue=HYPERLIQUID data_type=trades date=2026-06-21 pipeline_mode=live_hyperliquid` — the cefi live pipeline is
      operational (rows accrue as trades flow; first window was empty_confirmed). Findings filed:
      `plans/active/issues/live_mode_event_sink_topic_missing_2026_06_21.md`. Repo: market-tick-data-service /
      deployment-service. (CEFI lane 2026-06-21.)
- [x] [DATA] P0. **cefi — bug#7 live-capture schema-validation FIXED + durably shipped (CAPTURED windows no longer
      raise).** 6th first-run bug: live `record_captured` passes a row_count-only bookkeeping df (real ticks
      validated+written by `LiveWebsocketTickSink`), but `ManifestWriter.record_captured` ran `_maybe_validate` →
      `validate_row_df` against the full tick contract → every captured window raised `RowSchemaValidationError` (only
      empties recorded). Fix BOTH paths (operator-directed; `pipeline_mode`+`source` carry provenance): UTL
      `record_captured` gained a `validate: bool = True` gate (skips `_maybe_validate` when False) —
      unified-trading-library@057264fd (converged with slot-3's `78481472`); the live recorder passes `validate=False` —
      market-tick-data-service@e6b0f29. Both QG-green (UTL 139s / mtds 96s) via isolated name-correct worktrees
      (churn-immune), on remote `live-defi-rollout`. Deployed: fresh UTL+mtds tarballs (fixes verified inside) →
      `gs://deployment-scripts-central-element-323112/code/` @17:51Z. **Relaunch surfaced bug#8 (`MissingSourceError`):
      HYPERLIQUID/ASTER reclassified to cefi (UAC 0.30.0) but their sources were never registered —
      `SOURCE_PRIORITY     [(cefi,trades)]` was `['tardis']` only → writer rejected `source='hyperliquid'`. Fixed:
      registered `hyperliquid`+`aster` on the 5 cefi perp data_types
      (trades/ohlcv_1m/book_snapshot/liquidations/derivative_ticker) — unified-api-contracts@`061cfd01` (QG-green 225s,
      +4 tests updated); closes the cefi source-provenance RED gap for HL/ASTER. UAC tarball redeployed @18:24Z; VM
      relaunched `…182708`.** ✅ **VERIFIED end-to-end:** per-VM shard
      `market-data-tick-cefi-prd-…/_index/per_vm/…182708.parquet` holds **3 `capture_status=captured` rows, row_count>0
      (BTC 87 / ETH 238 / SOL 40), source=hyperliquid, pipeline_mode=live_hyperliquid** — NO RowSchemaValidationError,
      NO MissingSourceError. cefi LIVE now captures real trades (not just empty). Repo: unified-trading-library /
      market-tick-data-service / unified-api-contracts. (CEFI lane 2026-06-21.)
- [x] [DATA] P0. **cefi — IS reference-data VERIFIED 99.9%** (36,062/36,084 captured, fully schema_version=9, only 22
      failed) — done, no re-run. (CEFI lane 2026-06-21.)
- [x] [DATA] P1. **cefi — BLOCKED-CREDENTIALS ask FILED** for the 775.9k Tardis-gated failed cells (Tardis historical
      replay subscription, SM key `tardis-api-key`) — issue doc
      `plans/active/issues/cefi_tardis_historical_blocked_credentials_2026_06_21.md` + `CREDENTIAL APPROVAL REQUEST` in
      `plans/active/_agent_pings.md`. **Batch Tardis (historical) EXCLUDED — billing-gated (operator).** Repo:
      deployment-service. (CEFI lane 2026-06-21.)
- [x] ✅ [IS] P1. **IS tradfi v9 canonicalisation** — only 46.6% at schema_version=9; run the tradfi `_index`
      canonicalisation walk (8→9: source/asset_group/pipeline_mode) so the index is fully v9. Repo: instruments-service
      / market-tick-data-service. — GCS-verified 2026-06-21: `instruments-store-tradfi-prd` `_index` = 14629 rows, 100%
      schema_version=9, asset_group=tradfi (100%), source 0% blank. Mechanism:
      `instruments-service/scripts/populate_is_index_v9_2026_06_19.py --apply` (run by prior session sub-agent; see
      progress note 2026-06-21 15:42).
- [ ] [DATA] P1. **live=batch parity confirm** — once forward-pollers run, confirm a recent day's `live_<source>`
      canonical == a batch re-run (determinism spine). Repo: market-tick-data-service.
- [ ] [DATA] P1. **defi live continuous scheduler + pipeline_mode fix** — `launch-defi-forward-poll.sh` wires the
      end-to-end live path (VM `defi-fwd-20260621-212906`, deployment-service@48d57a5). T+10min verified: VM RUNNING
      (118% CPU, 5.7GB RAM), ≥12 rows written to `market-data-tick-defi-prd-central-element-323112`. **BLOCKER found**:
      `lst_rates_handler.py` hardcodes `PipelineMode.BATCH_ONCHAIN_SUBGRAPH` on all 7 write calls — ignores
      `--mode live` arg → rows land as `pipeline_mode=batch_onchain_subgraph` not `live_onchain_subgraph`. Fix: in
      `market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py` replace hardcoded
      `PipelineMode.BATCH_ONCHAIN_SUBGRAPH` with `PipelineMode.LIVE_ONCHAIN_SUBGRAPH` when `self.args.mode == "live"`
      (or read from the CLI arg). All 7 occurrences on lines 456/600/608/617/ 625/714/724. Same fix needed fleet-wide
      for every defi collect-\* handler that hardcodes BATCH\_. Repo: market-tick-data-service. **DEFERRED** —
      successor: this todo (2026-06-21). Also remaining: (i) cron/Cloud Scheduler to run `launch-defi-forward-poll.sh`
      daily; (ii) add collect-oracle-prices, collect-gas-fees as additional daily forward-poll VMs.

## 12-HOUR TARGET — mass-parallel sharding (operator 2026-06-21)

Goal: ALL data downloaded within **12h** via fan-out, not serial single-VMs. Quota is NOT the constraint —
asia-northeast1 **CPUS 50,532 / E2_CPUS 600 / PREEMPTIBLE 60,000** (used ~19) → room for ~75 e2-standard-8 (or hundreds
preemptible) in parallel. Shard model (from `launch-mdps-sharded-backfill.sh`): **one VM per (asset_group × data_type ×
year)**; per-VM manifest shards merge cleanly (UTL ManifestWriter `MANIFEST_PER_VM_SHARDS`). 7yr × ~5 AG × ~N data-types
→ a few-hundred-VM fan-out; each VM does ONE year → wall-clock collapses from weeks → ~1yr-of-runtime (hours).

**Ordering (HARD — raw before merge):** (1) **MTDS raw** year-sharded FIRST (the actual download) → (2) **MDPS**
`launch-mdps-sharded-backfill.sh` (merge, ~30 VMs, one cmd) AFTER raw lands → (3) **live runners**. Launching MDPS
before raw is complete merges incomplete raw — gate it.

**Sharding mechanism per layer:**

- MTDS raw: each per-data-type launcher takes `START END`; wrap as `for y in 2020..2026: launch … $y-01-01 $y-12-31` →
  one VM per (data_type × year). Data-types: defi {lst-rates, dex-pools, dex-swaps, lending-indices, liquidations,
  vault-share, pyth, gas-fees, jito/marinade}; tradfi {DBEQ-nasdaq, DBEQ-nyse, CFE/XCBF}; sports {odds}; pred
  {kalshi(bulk-seed=1 VM, can't shard the 33GB download but convert is year-internal), polymarket}.
- **Wave-1 caveat (2026-06-21):** the first single-VM launches (lst-rates/odds/pred-fwd) defaulted to a SINGLE DAY
  (2026-06-20) — inadequate for full history; the loop RE-LAUNCHES them year-sharded.
- `backfill-cluster.sh --cluster <name> --start-date --end-date --asset-group` = generic date-range cluster fan-out.
- Use `--preview`/`--dry-run` on each sharded launcher before the real fan-out; cap concurrent at the E2 quota (≤~70
  e2-standard-8) — overflow → preemptible or stagger.

## Autonomous loop (don't-stop-till-done)

Termination: per-AG MTDS honest-cov% → ~100% (modulo genuine `empty_confirmed` honest absence) AND ≥1 `live_<source>`
row present per AG AND IS sports/tradfi v9 complete. Progress metric = per-AG captured-row count climbing + `live_*`
rows appearing. Monitor re-checks the consolidated `_index` per AG each tick; relaunches any stalled/failed/terminated
backfill VM; flat metric → diagnose (`run.log`), never spin. Excluded from 100%: cefi batch-Tardis historical (billing).

## Wave-1 verify findings (2026-06-21) — fix before the sharded fan-out

The no-fire-and-forget verify caught real blockers (do NOT mass-shard into these):

- [x] **Manifest consolidator HEALTHY** — cefi/defi/tradfi/prediction market-data consolidator Cloud Run Jobs all
      executed 13:45 (crons ENABLED). NOT a global blocker. (sports/instruments-tradfi-legacy crons PAUSED — expected.)
- [x] **kalshi converter bug FIXED** — `_slice_day` filter type-mismatch (corpus `timestamp[s]` vs tz-aware-ns) →
      ArrowNotImplementedError; now adapts to the column type + timestamp[s] regression test (mtds, QG-green).
- [x] [SCRIPT] P0. ✅ **`launch-mtds-lst-rates-backfill-vm.sh` bucket bug FIXED** — `get_write_bucket_name("lst-rates")`
      → `get_write_bucket_name("market_data", asset_group="DEFI")` at 4 sites in `lst_rates_handler.py`. Now resolves
      canonical `market-data-tick-defi-prd-central-element-323112`. Repo: market-tick-data-service — mtds@4c85340
- [x] ✅ [SCRIPT] P0. deployment-service — **`launch-mtds-sports-odds-backfill-vm.sh` passes `--tier 1`** which the MTDS
      CLI rejects (`unrecognized arguments: --tier 1`). Drop/fix the arg. Repo: deployment-service. —
      deployment-service@b51729b: root cause = `setup-data-pipeline-vm.sh` mtds-backfill handler assembled
      `--tier $VM_TIER`, but the MTDS download CLI has NO `--tier` flag ("Tier-1=Odds API" is an ARCHITECTURE label,
      selected by asset_group→venue auto-routing; the Odds-API paid-plan tier is encoded in the SM API key). Removed the
      bad arg; VM_TIER now logged informational-only. Fixed handler uploaded to
      `gs://deployment-scripts-…/vm/setup-data-pipeline-vm.sh`; broken `mtds-backfill-odds-1` VM (was erroring every
      chunk ~1.5h) deleted; odds backfill relaunching on the fixed handler.
- [x] [SCRIPT] P0. deployment-service — **`launch-tradfi-bf-nasdaq-ohlcv-1m.sh` runs local UAC enumeration without a
      venv** (`ModuleNotFoundError: pydantic`) → no VM created. Invoke via the workspace venv. Repo: deployment-service.
      ✅ — `python3` → `"${WORKSPACE_ROOT}/.venv-workspace/bin/python3"` — deployment-service@e31817b
- [x] ✅ [DATA] P1. prediction forward-poll returns **0 instruments** (Kalshi/Polymarket IS-enum gap) — IS prediction
      enumeration must precede the MTDS poll (same IS→MTDS ordering as the Kalshi seed). Repo: instruments-service. — VM
      `instr-backfill-pred` launched 2026-06-21 16:57 UTC, confirmed RUNNING + writing Kalshi instruments (log:
      `date=2026-06-14: 1 stale + 1 missing venues/entities — will re-fetch (stale=['POLYMARKET'], missing=['KALSHI'])`).
      IS prediction index will have Kalshi rows after this run (prior state: 1944 POLYMARKET rows, 0 KALSHI rows).
- [ ] [DATA] P1. **sports — FootyStats ODDS source↔pipeline_mode mismatch (fail_fast)** [SPORTS-lane finding
      2026-06-21]: footystats fwd-poll fetches odds fine (29 snapshots/date) but the write FAILS validation — "Batch
      manifest row `source='footystats'` disagrees with `pipeline_mode='batch_odds_api'` (expects source='odds_api')".
      FootyStats odds are written under the odds_api pipeline_mode instead of a footystats-source-consistent mode.
      **This is the source-provenance / pipeline_mode surface** (UAC `source_priority.py`/`pipeline_mode.py` — the
      in-flight provenance lane's files). Fix belongs there: either footystats odds use `pipeline_mode=batch_footystats`
      (source=footystats) or the writer derives pipeline_mode from source. footystats fixtures/predictions/matches DO
      write OK; only ODDS fail. Repo: market-tick-data-service / unified-api-contracts (provenance lane). DO NOT fix
      from SPORTS lane (collision).
- [x] [DATA] P1. ✅ **sports — ODDS coverage OVER-COUNTS failures: live-instrument guard mislabels genuine
      "book-doesn't-price-this-fixture" as `attempted_failed`** — market-tick-data-service@050a091 | venue_fetch.py:
      exclude prediction-market venues (Kalshi/Polymarket/Novig/BetOpenly/ProphetX) from Odds-API bookmaker scope;
      sentinels.py: route uncovered (book, league) pairs → record_empty(EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE) instead
      of record_zero_rows(was_expected=True); tests updated (2 new coverage-branch tests) | QG ✅ --no-fix [SPORTS-lane
      finding 2026-06-21, measured]: the MTDS odds expected-universe (sentinel fan-out) enumerates **every bookmaker ×
      every fixture** (BETFAIR, KALSHI, PROPHETX, NOVIG, BETOPENLY, POLYMARKET, ONEXBET…). For a 2024-02-17 soccer
      fixture only a few books price it; the rest return zero. The writer tries `record_empty(SOURCE_RETURNED_ZERO)` but
      the manifest **live-instrument guard REJECTS it** ("instruments-service catalog says 'trades' was ALIVE on
      KALSHI/2024-02-17 → use record_failed, EmptyFromLiveInstrumentError") → marks `attempted_failed`. Result: odds
      shard reads **~72% attempted_failed** (1,260/1,758 on the sampled date) while 128k odds rows DID land — coverage
      looks far worse than reality. Root: the odds expected-universe is too broad (a niche US book ≠ a valid venue for
      EPL) AND/OR the live-instrument guard is too coarse for per-(bookmaker,league,fixture) odds — a bookmaker not
      pricing a fixture is **honest absence** (empty_confirmed), not a fetch failure. Fix belongs in MTDS odds-writer +
      the odds expected-universe enumeration (scope to valid book×league pairs) + possibly relax the
      EmptyFromLiveInstrumentError guard for odds. Repo: market-tick-data-service / unified-api-contracts. Same class as
      the IS fixtures silent-empty fix (is@0db2450) but INVERTED (genuine-empty forced to failed). DO NOT fix from
      SPORTS-IS lane. **CANONICAL-COVERAGE DESIGN (operator 2026-06-21):** record genuine non-coverage as honest
      absence, not failure, via OBSERVED-coverage rules (so honest-cov reflects reality + existing mislabels migrate):
      (1) **Source separation** — Kalshi/Polymarket are PREDICTION MARKETS (asset_group=prediction; sourced via
      polymarket_clob/kalshi connectors), NOT Odds-API bookmakers. Remove KALSHI/POLYMARKET from the Odds-API book set;
      their prices flow through the prediction pipeline into canonical format; pred-vs-book dispersion is a
      FEATURE-layer join, not a source merge. (2) **(bookmaker × league) observed-coverage map** = the 80/20:
      `covered := observed     odds-count > 0 across history`. A book that NEVER priced a league doesn't cover it → all
      (book, league, \*) cells are NOT-EXPECTED / `empty_confirmed(reason=BOOKMAKER_NO_LEAGUE_COVERAGE)`, never
      attempted_failed (handles regional books: a UK book ≠ Brazil Série B; Pinnacle≈global; DraftKings≈US). (3) **(book
      × league × season)** rolling window — coverage changes per season (book adds/drops leagues). (4) **per-fixture
      big-vs-small** (finest, optional) — within a covered league a book may skip minor fixtures; conservative:
      covered-league + both-teams-top-tier ⇒ expect, else allow empty_confirmed. **Where:** observed-coverage registry →
      UAC canonical (DERIVED from captured odds, refreshed periodically); odds expected-universe (sentinel fan-out,
      MTDS) reads it → only enumerates in-coverage; relax the EmptyFromLiveInstrumentError guard for odds so
      in-coverage-but-unpriced ⇒ empty_confirmed. **Migration:** reconcile script re-labels existing `attempted_failed`
      → `empty_confirmed(BOOKMAKER_NO_COVERAGE)` where (book,league) observed-out-of-coverage → the ~72%-failed
      collapses to genuine absence + honest-cov reads healthy. Repo: UAC + market-tick-data-service (coordinate with
      provenance lane).
- [ ] [DATA] P1. **sports — manifest DOUBLE-COUNTING: consolidated FIXTURES inflated ~1.16× by pipeline_mode dedup-key
      drift** [SPORTS-lane finding 2026-06-21, operator: "fix duplications, no double counting"]: the consolidated
      `availability_index` has 2 rows for the same (date, league, fixture) cell — e.g. EPL 2019-08-09 (1 real game) has
      a `pipeline_mode=batch_instruments_service` row (older runs, fixture_id=None) AND a
      `pipeline_mode=batch_api_football` row (current runs). The consolidator dedups "last-write-wins BY MANIFEST KEY",
      but pipeline_mode is IN the dedup key → the same logical cell under two pipeline_modes survives as 2 rows →
      inflates captured counts (76,087 raw → 65,521 distinct-by-fixture_id, ~16%). Root = the source-aware pipeline_mode
      standardization is MID-FLIGHT (old = generic `batch_instruments_service`, new = `batch_api_football`); historical
      rows not yet migrated to the canonical source-aware mode. **This is the provenance/pipeline_mode lane's domain**
      (they are editing `pipeline_mode.py` / `source_priority.py` now). Fix = (a) standardize sports IS-fixtures
      pipeline_mode to ONE canonical value + (b) migrate historical `batch_instruments_service` sports rows → canonical,
      so the dedup-key collapses the dups. Repo: unified-api-contracts + unified-trading-library (manifest_consolidator)
      — coordinate with provenance lane. DO NOT fix from SPORTS-IS lane (collision with active pipeline_mode edits).
- [x] ✅ [SCRIPT] P1. **sports — IS `_write_team_mapping` GCS-429 redundant-write FIXED** (instruments-service, this
      lane): the STATIC team-mapping table (UAC EPL/Bundesliga constants, byte-identical every call) was re-written to
      the SAME GCS blob on EVERY backfill date (~1.1k writes/run/VM → GCS hot-object 429s, ~16% rejected, no retry; the
      blob was still correct since 84% succeeded — waste + 429-spam, not data loss). Now write-once-per-process. The
      operator's transfer-window point: the canonical source
      `unified_api_contracts.canonical.domain.sports.transfer_windows.is_transfer_window_open()` ALREADY gates
      `transfer_records` (sports_per_source_rules.py) — applies to roster/transfer data, NOT this static table nor
      per-fixture match stats. Repo: instruments-service.
- [x] [TERRAFORM] P0. ✅ **deployment-service terraform bucket-name audit complete** —
      `manifest_consolidator_scheduler.tf` confirmed correct (canonical `${local.deployment_env_short}` throughout for
      all Group A AG buckets; legacy entries intentional for MDPS Phase 0f); deleted deprecated
      `launch-manifest-consolidator-vm.sh` (should have been deleted 2026-05-20 per codex); fixed stale
      `market-data-tick-defi-central-element-323112` echo in `launch-mtds-dex-swaps-backfill-vm.sh` →
      `market-data-tick-defi-prd-${PROJECT_ID}`. No terraform apply needed (scheduler already correct). —
      deployment-service@164e21d

## Codex SSOT updates

- [x] ✅ [DOCS] P2. codex/02-data/availability-manifest-and-data-status.md — add the 2026-06-21 per-AG snapshot + the
      live-mode-population gap as a tracked baseline. — unified-trading-pm@7c3926f3f

## Progress Log

### 2026-06-21 ~22:00 — tradfi `live_databento` source-stamp FIXED + 2 manifest cleanups actioned

**`live_massive` -> `live_databento` (root cause FIXED, UAC@1205ae44).** The relaunched live producer
`mtds-live-tradfi-cme-trades-20260621-213416` CONNECTS + authenticates (`session_id` issued) + streams real databento
ticks - but stamped `pipeline_mode=live_massive`. Root cause (corrected after reading both sides):
`live_source_for_venue` resolved tradfi live via the BATCH `SOURCE_PRIORITY[0]=massive`. First instinct (remove
massive's `Mode.LIVE`) was WRONG - `test_massive_and_databento_are_live_and_replay_capable` documents an explicit
**operator 2026-06-05** decision that massive (Polygon.io 15-min REST) IS live-capable; reverted that. Real fix: the
SOLE tradfi live **WS producer** is `databento_tradfi_ws`, so a `tradfi` branch in `live_source_for_venue` returns
`databento` (mirrors `_PREDICTION_LIVE_SOURCE_FOR_VENUE`); batch path unchanged. Verified
`live_pipeline_mode_for_venue(tradfi,*)=live_databento`

- 48/48 tests green. Shipped via **isolated-worktree promotion** (UAC had a concurrent LIVE peer editing
  `_source_priority_data.py`/cefi-perp venues; preserved their WIP, never bundled it). Codex SSOT + CLAUDE.md corrected
  (my earlier bug-#1/#2 framing was inaccurate: the key resolves fine - verified 32-char secret; massive is not
  "batch-only"). **Deploy pending:** live VM bakes UAC from a GCS tarball -> running producer keeps `live_massive` until
  a `create-code-tarballs.sh` rebuild from clean LDR + relaunch (tracked todo added; daily cron reuses the old tarball).

**2 manifest cleanups (operator "DO THAT too"):** (1) **MDPS 15m/24h** - LAUNCHED `mdps-backfill-tradfi-20260621-213646`
(RUNNING) re-aggregating the 1m corpus -> ohlcv_15m/24h. (2) **equity `ohlcv_1s`** - investigated: NOT a clean phantom.
DBEQ ALLOWS ohlcv-1s (allowlist) + the validity matrix lists it, but `expected_coverage` deliberately excludes it ->
genuine opposite-direction OPERATOR DECISION (fetch-it vs deliberate-exclude); reframed `[DATA-OPERATOR]` rather than
blindly dropping or backfilling. honest-cov now **14.3%** (323,836 captured, up from 5.3% baseline).

### 2026-06-21 22:00 — "finish the current": parallelized for speed; honest completion picture

**Odds backfill 1→7 parallel year-shards** (`mtds-backfill-odds-{2020..2026}`, all RUNNING) — odds has ~15M req
remaining (no rate concern) so sharded with `--force` (idempotent re-fetch of static historical odds → guarantees 100%
coverage, ~7x faster than the single 304-chunk VM). **Enrichment** healthy: `sports-enrich-2019-2022` chunk 24/49,
`2023-2026` chunk 17/43 — finish current ranges ~2h. **Live** VM relaunched (`...213937`), op=websocket- streaming
mode=live (no 401 from the new VM; verifying publish).

**Coverage measured (availability_index):** core enrichment entities 8-13% captured-of-TOTAL (FIXTURE_STATS 13%,
EVENTS/LINEUPS 11%, MATCHES 13%, PLAYER_STATS 8%, ODDS 13%) — but TOTAL includes many no-fixture cells that become
empty_confirmed (raw log: "No fixtures for date → empty_confirmed markers"), so honest-cov is higher. Climbs as the 2
enrich VMs finish their chunks. **API-Football is daily-cap-bound (Custom300=300k/day, only 70k used — UNDER-used
because of empty-date stretches).** The 2 VMs finish their first pass ~2h; full multi-year enrichment to 100% needs
either more API-Football daily budget (operator → 1.5M/day = the 5x lever) or a multi-day multi-pass. ONE monitor
(b2tp3vezk) watches all 10 sports VMs, wakes on actionable event only.

### 2026-06-21 21:40 — ODDS API UPGRADED (blocker RESOLVED) + API-Football rate analysis

**Odds API blocker GONE:** operator upgraded the Odds API; `odds-api-key` (the secret the sports MTDS pipeline uses) now
returns HTTP 200 with **14,999,964 requests remaining**. Relaunched: odds backfill `mtds-backfill-odds-1`
(2020-06→2026-03, `--tier` bug already fixed) + fresh live VM `mtds-live-sports-odds-api-trades-20260621-213937` (old
one 401-dead since 19:07). Both verifying T+10min → live_odds_api rows + historical odds backfill resume.

**API-Football rate (operator Q "is 18k/30min maximising"):** NO per-minute (600/min vs 1200 ceiling, 704 free when
checked) — but per-minute is NOT the bottleneck. Plan=**Custom300** (300k/day); used 67.8k today, 232k left. The
per-fixture enrichment = millions of calls → **daily-cap-bound, inherently multi-day**. Pushing per-minute just exhausts
300k sooner then stalls to reset (same daily total). **The 5x completion lever = bump the daily cap to 1.5M/day**
(operator plan upgrade) — NOT a code/throttle/VM-count change. Throttle left at 0.12s (correct; lowering it is
pointless + 429-risky when daily-bound).

### 2026-06-21 — SPORTS lane: enrichment OOM fix + final autonomous state

**Enrichment OOM (fixed):** the per-fixture enrichment OOM-killed python (7.2GB anon-RSS) on the full-sweep default
`e2-standard-2` (8GB) — the in-memory fixtures catalogue + (league×entity) coverage map + per-fixture entity buffers
exceed 8GB. Relaunched both `sports-enrich-{2019-2022,2023-2026}` on **e2-standard-8 (32GB)** → stable (0 429s, fetches
climbing, entity-skip active). FOLLOW-UP: full-sweep/enrich launcher should default enrichment to e2-standard-8 (the
fixtures-only phase is fine on e2-standard-2; only the per-fixture enrichment needs the RAM).

**Final autonomous state (operator away 2h):** ALL code shipped + verified — 5 bugs, concurrency-safe throttle, 3
manifest migrations (odds AF 44%→7%, blanks 743k→0+dedup, 507k entity-coverage relabel + 92% player-stat skip),
Live==Batch wiring (LIVE_ODDS_API). ONLY blocker = **Odds API OUT OF CREDITS** (operator top-up; blocks live rows +
remaining odds backfill — code proven, VM running, emits on credit return). API-Football enrichment + fixtures fill is
rate-bound multi-day (1.2k/min ceiling, used fully, 0 waste). Sweep loop monitors VM health/OOM/credit-return.

### 2026-06-21 — SPORTS lane STATE SNAPSHOT (autonomous, operator away 2h) — for context-compression resume

**SHIPPED (all green):** `--tier` (deployment-service@b51729b) · silent-empty→attempted_failed (is@0db2450,+10 tests) ·
team_mapping GCS-429 write-once (is@865aea9) · **concurrency-safe self-enforced rate limiter** (is@e29ba65 — fixes the
burst→429→52s-minute-sleep thrash that capped enrichment at ~46/min vs 1200/min cap) · UAC entity-coverage map
(uac@9ea84499, sub-agent C). IS tarball rebuilt @e29ba65.

**RUNNING VMs:** odds-backfill `mtds-backfill-odds-{2020..2026}` (7, ODDS-API key, separate quota) · enrichment
`sports-enrich-{2019-2022,2023-2026}` (2, RELAUNCHED on fixed throttle — verify rate post-boot) · **sports LIVE** sports
LIVE producer (RELAUNCHED again post MTDS key-fix — see below; the `...184015` instance booted clean past the enum fix
but hit a SECOND bug: `OddsApi: no API key` because the connector referenced a nonexistent `MarketConfig.odds_api_key`
attribute; FIXED mtds@670be2f). Fixtures phase COMPLETE (265k captured / 1,356 leagues; VMs self-deleted).

**LIVE==BATCH (operator caught this) — UAC ENUM FIX LANDED:** sports had **0 `live_*` rows** — footystats fwd-poll wrote
`batch_*` (forward-over-future, NOT live). The true live producer
(`launch-mtds-live.sh --asset-group sports --shard-spec sports:odds_api:trades` → `odds_api_ws` WSFeedConnector →
`live_odds_api`) FAILED at boot with `No PipelineMode for source 'odds_api' in mode 'live'` — the `PipelineMode` closed
set had `BATCH_ODDS_API`/`REPLAY_ODDS_API` but no `LIVE_ODDS_API`. FIX (uac@249ca53f, LDR): added
`PipelineMode.LIVE_ODDS_API` + flipped `SOURCE_MODE_CAPABILITY["odds_api"]` to `{BATCH, LIVE, REPLAY}` + the test-side
SSOT `EXPECTED_SOURCE_MODE_CAPABILITY` + replaced `test_no_sports_source_is_live_yet` with
`test_odds_api_is_the_first_live_sports_source` (the other sports vendors stay live-less). `REPLAY_ODDS_API` already
existed (replay-capable). QG green (223s), source-mode + cassette tests pass. The live VM pip-installs UAC fresh at boot
→ it picks up the new enum once LDR has it; VM relaunched as `...184015` (same lowercase `odds_api` venue + 5-league
instrument-ids). Same canonical schema as batch (Live==Batch). cefi proved the live path works after its 5-bug first-run
chain (AG-agnostic infra bugs, fixed).

**SECOND LIVE-CHAIN BUG — MTDS connector key-resolution (FIXED mtds@670be2f, LDR):** post enum-fix, `...184015` booted
CLEAN through `websocket-streaming mode=live` + `DEPLOYMENT_STARTED` + wrote 5 per-VM manifest shards (the 5 leagues) —
proving the enum fix worked — but emitted `OddsApi: no API key — stream yields nothing` so 0 rows. ROOT CAUSE:
`odds_api_ws._get_api_key()` referenced `MarketConfig().odds_api_key`, an attribute that does NOT exist (the config
class is `MarketDataProviderConfig`, which exposes `odds_api_secret_name` not a resolved key); the bare `except`
swallowed the `AttributeError` → None → BLOCKED-CREDENTIALS message DESPITE the `odds-api-key` secret existing (32-char
value verified in Secret Manager). FIX: resolve via the canonical
`get_secret_client(project_id=cfg.gcp_project_id).get_secret(cfg.odds_api_secret_name)` (the same pattern the WORKING
batch `OddsApiAdapter` + `DatabentoBaseClient` use). 30 connector unit tests pass; QG green; basedpyright clean on the
change (the 3 file-level Any errors are pre-existing JSON-parse lines, not the edit). The VM pip-installs MTDS fresh at
boot → relaunched to pick up `670be2f`.

**THIRD (TERMINAL) BLOCKER — The Odds API credits EXHAUSTED → `BLOCKED-CREDENTIALS` (operator top-up, 2026-06-21):**
with the key-fix live, VM `...190258` now SENDS the key — the API authenticates the request but returns **HTTP 401
`OUT_OF_USAGE_CREDITS`**. Verified directly: the `odds-api-key` secret is a VALID key (the free `/v4/sports/` list
endpoint returns 200 with EPL/Serie-A active), but the credit-costing `/v4/sports/{sport}/odds` endpoint returns
`{"error_code":"OUT_OF_USAGE_CREDITS"}` with headers `x-requests-used: 5000060 / x-requests-remaining: -60`. The 7
odds-BACKFILL VMs (2020-2026 historical odds) drained the entire quota on the SAME `odds-api-key` secret. **The full
code+infra live path is now PROVEN end-to-end** (enum ✓ + key-resolution ✓ + DEPLOYMENT_STARTED + per-VM manifest shards
written + graceful 401 honest-absence, 0 crashes) — the ONLY remaining gap is credits. The connector polls every 60s and
will emit `live_odds_api` rows with NO further code change the moment credits return. VM `...190258` LEFT RUNNING so it
auto-produces on top-up.

> **CREDENTIAL APPROVAL REQUEST — odds-api-live-credits (operator action 2026-06-21):** Vendor: The Odds API
> (https://the-odds-api.com/#get-access). What I need: top up / upgrade the `odds-api-key` Secret-Manager key's monthly
> credit quota (current usage 5,000,060 — quota fully consumed by the 2020-2026 historical backfill on the SAME key). A
> SEPARATE live-only key (its own quota) would prevent the backfill from re-draining live; otherwise live + backfill
> must share. Unblocks: the FINAL `≥1 live_odds_api` sports row (Live==Batch sports gate). Without it: VM `...190258`
> stays up
>
> - honest-absences (0 rows) until credits return — no further code work needed.

**3 MIGRATION SUB-AGENTS in flight (opus), IS ships BLOCKED on a LIVE foreign UTL WIP**
(`manifest_writer/_writer_captured.py`, peer actively editing — do NOT stomp; their tracked waiters fire when UTL goes
clean):

- **A** (agentId in transcript): canonicalise legacy `batch_instruments_service` sports rows → `batch_<source>` + fill
  blank reasons → fixes the 130,828 blank-reason cells + the ~1.16× double-count (pipeline_mode dedup-key drift). IS
  migration script.
- **B**: odds (book×league) observed-coverage map + sentinel wiring + migration → fixes the ~72% mislabelled
  `attempted_failed` (Kalshi/Polymarket removed as they're prediction-markets not Odds-API). UAC+MTDS.
- **C** (a2c87b13142bd5311): UAC@9ea84499 shipped — `is_league_entity_covered(league,entity)` + new
  `EmptyConfirmedReason.EXPECTED_NO_PROVIDER_COVERAGE`. Dry-run: **~92% of leagues never yield player-stats** → skip
  kills the waste; **506,959 cells** relabel → expected-empty. IS write-path + migration ready, pending UTL-clear.

**WRITE-PATH AUDIT (regression-proof):** record_empty rejects blank (`LegacyBlankErrorReasonError`) + invalid reasons;
`pipeline_mode: PipelineMode` REQUIRED; schema_version=9. So all issues are LEGACY data → migrations fix them; no live
regression.

**NEXT (autonomous loop, `/tmp/sports_autoloop.sh` watcher armed):** (1) verify sports live ≥1 row; (2) verify
enrichment post-throttle rate (if still latency-bound/sequential → the per-fixture fetch needs concurrency = next fix);
(3) when UTL clears → resume A/B/C → ship + run their `--apply` migrations (snapshot first) → honest-cov jumps to
reality; (4) once C's entity-skip lands → rebuild tarball + relaunch enrichment (drops ~92% wasted player-stat calls).
Raw backfill is rate/credit-bound (multi-day, API ceiling) — running efficiently.

### 2026-06-21 — CEFI lane: live producer unblocked (missing lifecycle topic — fleet-wide finding)

First-ever operational live MTDS launch crashed: `NotFound: 404 … market-tick-data-service-events`. UTL
`_sink_factory.py:44` derives the live lifecycle topic `f"{service_name}-events"` but terraform/enum canonical is the
shared `service-lifecycle-events` → the per-service topic never existed (live mode has NEVER run on any AG → latent
fleet-wide). **Created `market-tick-data-service-events`** (unblocks live MTDS for ALL asset groups — one service) +
relaunched `mtds-live-cefi-hyperliquid-trades-20260621-151424`. Systemic fix (UTL sink → `service-lifecycle-events`, or
terraform per-service topics; also hits MDPS/features/strategy/execution live) filed:
`plans/active/issues/live_mode_event_sink_topic_missing_2026_06_21.md`. Also handled (this lane): shared-tree collisions
(a sync transiently baked my uncommitted setup-vm edit into the GCS startup script → 1st VM a no-op dud; fixed GCS to
clean efdb9df + redeployed) + reconciled to the concurrent live-wiring commit deployment-service@efdb9df.

Coverage snapshot above (measured, not memory). Kalshi seed VM re-launched (runner set-u fix mtds@74e228c). Fleet
launch + monitoring loop starting (this plan is the path-to-100% plan-of-record).

### 2026-06-21 — SPORTS lane (/autonomous, Opus): odds flowing; API-Football credential block + silent-empty bug FIXED

**Shipped:** `--tier` launcher bug (deployment-service@b51729b). Silent-empty manifest bug (instruments-service@0db2450,
QG-green sentinel b5b8b72; direct-LDR under dirty-deps carve-out — UAC/UTL dirty with concurrent provenance WIP).

**MTDS odds = HEALTHY + flowing hard.** 7 year-shard VMs `mtds-backfill-odds-{2020..2026}` (--force, 2020-06→2026-06)
RUNNING, writing real bookmaker odds (WilliamHill/DraftKings/Ladbrokes/… EPL); odds-2026 124k rows, odds-2020 30k,
climbing. `pipeline_mode=batch_odds_api` → `market-data-tick-sports-prd-…` (canonical consolidator ENABLED \*/1).

**Root cause (operator-confirmed): IS fixtures gap = CREDENTIAL block, now lifted.** Full-sweep fetched 0 fixtures/date
→ `errors.plan` (free API-Football, dates 2026-06-20..22 only). Operator upgraded → **Custom 1200 r/min, 5 seats, 300k
r/day** (re-tested: 2024-01-13 → 927 fixtures). Killed 8 false-writing full-sweep VMs (each wrote only ~2 dates false
`empty_confirmed` before kill → small blast radius).

### 2026-06-21 — DEFI lane: FULL FAN-OUT LAUNCHED + real root-cause of catalog blocker FIXED

**60 MTDS defi market-data VMs LAUNCHED** (all data_types × years 2020→2026; lst-rates×7, dex-pools×6, dex-swaps×6,
lending×5, liquidations×7, vault×6, pyth-archive×1, pyth-lst×4, gas-fees×7, jito×5, marinade×6) — no quota errors, no
OOM, ALL confirmed writing to **consolidated `market-data-tick-defi-prd`** (bucket fix verified live). Plus 6→ IS
catalog year-shard VMs (capturing real instruments). Drive-to-done monitor armed (refresh consolidators + wake on fleet
drain). **CATALOG BLOCKER — REAL ROOT CAUSE (corrects earlier diagnosis):** MTDS `assert_defi_catalog_fresh` →
`run_preflight(DEFI_COLLECT_DAILY)` requires the **`instrument-catalog` lifecycle ROLL-UP artifact**
(`build_instrument_catalogue.py`), NOT the per-venue instrument records. The IS instruments-backfill writes records with
**blank data_type** (consolidated IS index = 117k rows, data_type all empty) → preflight finds no `instrument-catalog` →
`age=None` → MTDS routes honest-absence (empty). FIX: triggered Cloud Run jobs **`lifecycle-catalogue-regen-defi` (exec
7844r)** + `instrument-catalogue-regen` (c2cwk) — the roll-up producer (last defi run was 2026-06-19 = stale, the reason
defi was stuck). Once the artifact is fresh (<24h) the per-date preflight passes → MTDS captures. **Watcher besyyb23t**
waits for the roll-up → consolidates instruments-defi → verifies a dex-pools VM flips empty→capturing. **RESUME:** if
besyyb23t shows capturing → the running 60 VMs auto-capture their remaining dates; **re-run any shard that recorded
early empties** (catalog wasn't fresh when they started) after the roll-up — empties aren't terminal (empty_confirmed is
re-attempted; only `captured` is skip-worthy). Then: execution-defi consolidator → measure defi honest-cov climbing →
MDPS defi (`launch-mdps-sharded-backfill.sh defi`) → defi live (reuse cefi `live_websocket`/ `--shard-spec` wiring
deployment-service@efdb9df, or scheduled collect-\* re-run for recent days). Live background tasks: drive-monitor
b874zr2s4 + catalog-gate besyyb23t.

**Silent-empty FIX (operator directive "empty_confirmed→attempted_failed, they're wrong"):** (1) `api_football.py`
`_extract_response` raises `ApiFootballResponseError` on a non-empty `errors` envelope → routes to `failed_venues` →
`attempted_failed`, not silent empty; (2) `process.py` `_fixtures_fetch_failed` helper (venue ∉ `non_error_venues`,
guarded `not _skip_urdi`) threaded → `_zero_sports_empty_fixture_markers` writes `record_failed` on fetch-error,
`record_empty` only for a clean genuine-empty day. +10 unit tests; QG 71s green.

**ARCHITECTURE (operator Q): odds coverage IS gated on fixtures.** MTDS odds expected-universe = per-(bookmaker, league,
fixture) sentinel fan-out (`venue_fetch.py:89`, `sentinels.py`) from the IS fixtures catalogue;
`sports_catalog_reader.py:150` "no row in catalog → silently skipped". So fixture-with-no-odds is visible in
manifest/data-status **only if the fixture is in the catalogue**. IS fixtures 15.9% ⇒ odds `expected_unattempted=0`
(artificially complete). **HARD ORDER: backfill IS fixtures FIRST → catalogue completes → odds sentinel fan-out
enumerates real universe → odds gaps visible → odds fills.**

**LIVE:** `sports-scheduler-cron` RESUMED (_/5); `uts-prod-sports-scheduler` Cloud Run job ran (Completed); footystats
fwd-poll relaunched (today..+14d). Only deprecated `_-legacy-cron` paused (expected).

### 2026-06-21 — DEFI lane: blocker fixes IN FLIGHT — full dependency chain mapped

The defi MTDS backfill has a hard prerequisite CHAIN (same IS→MTDS contract as sports). Status of each link:

1. **Bucket fix DONE** (mtds@4c85340 lst_rates + mtds@1c99e5c 8 handlers → consolidated `market-data-tick-defi-prd`; VM
   tarball rebuilt @14:36Z; SSOT corrected pm@12c4d89a6). Proof CONFIRMED writes to consolidated bucket.
2. **Blocker B (catalog) — IN FLIGHT:** MTDS `assert_defi_catalog_fresh` needs `captured instrument-catalog` rows
   (per-date, <24h) in `instruments-store-defi-prd/_index/availability_index.parquet` — they were ABSENT for the range.
   FIX: launched 7 year-shard IS catalog VMs `instr-backfill-defi-{2020..2026}` (e2-standard-8, RUNNING). **After they
   write → MUST trigger `uts-prod-manifest-consolidator-instruments-defi`** (IS consolidated index was fresh @15:08 so
   it won't auto-include the new shards) → then MTDS preflight sees the catalog.
3. **Blocker A (OOM rc=137) — IN FLIGHT:** e2-standard-4 kernel-OOM on per-day manifest reload. FIX: background
   sub-agent bumping all defi MTDS launchers → `e2-standard-8` (+ adding MANIFEST_PER_VM_SHARDS/VM_NAME to
   vault-share-price + gas-fees for concurrent year-shards). Also triggered
   `uts-prod-manifest-consolidator-execution-defi` (exec lz2dp) to refresh the 23.7d-stale market-data index (reduces
   per-day reload memory). **REMAINING EXEC ORDER (resume here):** (i) IS catalog VMs done → trigger
   `…-instruments-defi` consolidator → confirm captured instrument-catalog rows in IS index. (ii) RE-PROOF:
   `MACHINE_TYPE=e2-standard-8 launch-mtds-lst-rates… --force 2025-01-01 2025-01-31` → verify it CAPTURES (not empty) +
   no OOM. (iii) FAN-OUT the ready year-shard matrix (2020→2026, ~47 VMs, hardened launchers). (iv) trigger
   `…-execution-defi` consolidator → confirm defi honest-cov climbing in the consolidated `_index`. (v) MDPS defi
   (`launch-mdps-sharded-backfill.sh defi`). (vi) defi LIVE forward-poll (stub; coord with cefi lane's `live_websocket`
   setup-data-pipeline-vm.sh wiring — defi live is on-chain RPC, re-run handlers --mode live for recent days). Watchers
   in flight: IS-catalog completion + launcher-edit sub-agent.

**NEXT (this lane):** rebuild+upload instruments-service tarball (@0db2450) → relaunch full-sweep **--force**
(re-fetches the ~16 false-empty dates → self-reconciles + fills 2019-2026 on paid plan; shard finer given 300k/day) →
catalogue fills → odds expected-universe real → measure IS+MTDS sports honest-cov climbing → gate features-sports on raw
→ ≥1 live row.

### 2026-06-21 — SPORTS lane: RATE-LIMIT root-caused + fixed (operator: "only ~1k req/hr vs 1.2k/min — way too slow")

**Root cause (the throttle thundering-herd):** sports adapter `_MIN_REQUEST_INTERVAL=0.1s` = 600 req/min PER VM. 8
all-entities full-sweep VMs × 600 = 4800/min slammed the API-Football **1.2k/min** cap → every VM 429s → the adapter's
"sleep to next UTC-minute boundary" (`base.py` `_get_with_retry`) → all 8 idle ~50s, wake together, overshoot again →
fleet collapsed to **~22 req/min** (operator's dashboard: ~1k/hr). The heavy load was the **per-fixture enrichment**
fan-out (`/fixtures/players`, `/fixtures/events`, lineups, stats — N calls/fixture).

**Fix (operator-steered: fixtures-first + fewer VMs):** killed the 8 thrashing VMs. Relaunched **2 FIXTURES-ONLY VMs**
(is-gap-fill `--entity FIXTURES`, split 2019-2022 / 2023-2026) = 2×600/min ≈ the 1.2k/min cap with **NO thundering
herd**. **Verified flowing at full speed, zero rate-limiting** ("Fetched 639 fixtures for date=2019-03-02", multiple
dates/sec). FIXTURES = ~1 call/date (~2920 total for 8yr) → catalogue fills in **minutes**, not days. Also shipped
full-sweep `--entity` flag (deployment-service@4caeaf3) for fixtures-first phasing.

**Architecture confirmed (operator's Q): enrichment reads fixtures from GCS** — `_per_fixture_gcs_fast_path`
(process.py:191) lets per-fixture entities read fixture IDs from GCS, so fixtures-first composes: Phase-1 FIXTURES
(fast), Phase-2 enrichment (heavy) reads the Phase-1 GCS fixtures. The all-entities full-sweep did NOT use this split
(grabbed fixtures + enriched inline per date → the thrash).

**Phased plan (autonomous):** Phase-1 FIXTURES (running, ~mins) → Phase-2 ENRICHMENT (per-fixture entities, 2 VMs at the
1.2k/min cap, GCS-fixture fast path) = **multi-day, rate-cap-bound** (millions of per-fixture calls; 300k/day now,
operator upgrading to 1.5M/day; per-minute 1.2k is the binding constraint — no agent can exceed the API ceiling, but 2
VMs use it FULLY without thrash). Odds backfill (7 VMs, separate ODDS-API key, no contention) + live (footystats +
scheduler) continue. Background monitor armed: fixtures-complete → auto-launch enrichment.

### 2026-06-21 — DEFI lane (/autonomous, Opus): bucket bug is FLEET-WIDE across defi handlers

Canonical defi bucket CONFIRMED = consolidated `market-data-tick-defi-prd-central-element-323112` (only defi bucket with
a live consolidator + the measured 6.16M-row v9 `_index`; dedicated `{stem}-prd` buckets are
un-consolidated/index-less). slot-4 already fixed **lst_rates** (mtds@4c85340). STILL BROKEN (same
`get_write_bucket_name("<dash-data-type>")` orphan-bucket bug → ManifestConsolidatorStaleError, data lands where the
`_index` never sees = why defi is stuck at 6%): gas_fee×3, dex_pools, dex_swaps(check), lending_indices, liquidations,
oracle_prices, perp_funding, evm_defi, aggregator_route. Already-correct (do NOT touch): vault_share_price, solana_defi,
lst_rates. UTL `_DOMAIN_TO_YAML_KIND` has no dash-data-type kinds → legacy `{label}-{pid}` fallback. Fix =
`→ get_write_bucket_name("market_data","defi")`. **SSOT note:** `codex/02-data/defi-canonical-naming-ssot.md` "bucket"
row (locked 2026-05-28, dedicated `{stem}-prd`) is OPERATIONALLY STALE — proceeding consolidated per 2026-06-21 plan
P0 + ground truth; row must be corrected (todo). **Operator: overrode a locked-SSOT row (big finding).** Exec order
(HARD): mtds handler fix → rebuild VM tarball (deployment-service create-code-tarballs.sh) → year-shard defi backfill
(2020→2026, 1 VM/data_type×year, consolidated bucket, MANIFEST_PER_VM_SHARDS) → T+10 verify → MDPS defi → live
forward-poll (launch-defi-forward-poll.sh = STUB) → monitor `_index` honest-cov. MINE this session: the
remaining-handlers fix + tarball + fan-out + SSOT-row correction.

### 2026-06-21 — CEFI lane (/autonomous, Opus): triage measured + live-path diagnosed

Measured cefi from consolidated v9 `_index` (3.87M rows; cov 33.9% = 1.31M cap / 1.28M empty / 802k failed / 482k
unatt). **802k failed triage (measured):** source=tardis 753,341 + 22,519 batch*tardis phantoms = **775,860 Tardis-gated
(96.7%)** → historical re-fetch is billing-gated (operator EXCLUDED) → BLOCKED-CREDENTIALS. Free-venue re-fetchable =
hyperliquid 30,835 + aster 17,675 = **48,510** (native, no Tardis). Top error_reasons: UNCLASSIFIED_ADAPTER_ERROR
689,899 / VENUE_FETCH_FAILED 83,923 / phantom_no_parquet 22,700 / HTTP_429 3,652. **IS cefi VERIFIED 99.9%
(36,062/36,084, all v9) — done.** **BIG FINDING — live path:** operator named
`launch-cefi-forward-poll.sh`/`launch-cefi-onchain-forward-poll.sh` for the live stream, but BOTH run `--mode batch` →
BILLED Tardis replay +
`batch*<source>`rows (would violate the Tardis-billing exclusion AND not produce`live\_<source>`). The genuine FREE live path = `launch-mtds-live.sh
--asset-group cefi` (`--operation websocket-streaming --mode
live`, real-time exchange-WS proxy; 18 cefi connectors registered since the 2026-05-17 Phase 3.5 rollout — the handler's "registry empty at Phase 3.1" docstring is STALE). Gap: `setup-data-pipeline-vm.sh`has NO`live_websocket`branch (generic fall-through hardcodes`--mode
batch`), and the handler needs `--shard-spec`+`--instrument-ids`+`streaming_redis_url`. **Plan: wire the live branch +
local redis into setup-data-pipeline-vm.sh → launch mtds-live cefi → verify ≥1 live row** (reusable for all AGs — live=0
fleet-wide). Then year-shard the 48.5k free-venue failed re-fetch + file the BLOCKED-CREDENTIALS ask for the 775.9k
Tardis-gated.

### 2026-06-21 — DEFI lane: bucket fix SHIPPED + PROOF found 2 more blockers (gating the fan-out)

Shipped: mtds@1c99e5c (8 remaining defi handlers → consolidated bucket, QG green) + rebuilt mtds-code.tar.gz @14:36Z +
SSOT row corrected (pm@12c4d89a6). **PROOF VM** (lst-rates Jan-2025, fresh tarball, mtds-lst-rates-20260621-144131):
**bucket fix CONFIRMED WORKS** — wrote per-VM shards to
`market-data-tick-defi-prd-central-element-323112/_index/per_vm/`, NO ManifestConsolidatorStaleError. BUT proof surfaced
2 NEW blockers that gate the whole defi fan-out (do NOT mass-launch until both fixed — would yield 0 captured + OOM):

- [x] ✅ [DATA] P0. **DEFI BLOCKER B (showstopper): `assert_defi_catalog_fresh` fails → handler routes HONEST ABSENCE**
      (records empty_confirmed, does NOT fetch). Every date logged `instrument-catalog(age=Nones, max=86400s)` missing →
      expected_unattempted would convert to empty_confirmed NOT captured. **Root cause: ALL 145,467 rows in
      `instruments-store-defi-prd-central-element-323112/_index/availability_index.parquet` had `data_type=''` (empty)
      and 70,410 rows had `asset_group=None` — UTL `_filter_index()` requires `data_type='instrument-catalog'` AND
      `asset_group='defi'`. Backfill script set both columns on all rows (145,343 rows now satisfy the preflight
      filter). Source-code fix `e8acef1` (IS `_write_catalogue_record` DeFi branch) prevents recurrence.** —
      instruments-service@de8e164 (backfill script) | 2026-06-21 17:22 UTC
- [x] ✅ [SCRIPT] P0. **DEFI BLOCKER A: rc=137 (SIGKILL/OOM)** on e2-standard-4 after ~2 days — likely
      ManifestFreshnessCache/ManifestReader loading the 6.16M-row consolidated `_index` per-day, or boot-disk (img 10GB
      vs 50GB unresized). Fix = bump MACHINE_TYPE (e2-standard-8/16) on the defi launchers and/or a manifest-read memory
      knob. Repo: deployment-service (+ maybe mtds/utl). Diagnosing (sub-agent). **Fan-out matrix is READY** (year-shard
      2020→2026 per data_type, ~47 concurrent-safe VMs; vault-share-price + gas-fees launchers MISSING
      `MANIFEST_PER_VM_SHARDS` → must add it or run sequential; dex-pools/dex-swaps/liquidations need `VM_NAME=` per
      shard; pyth-archive = single fixed window; `launch-defi-backfill-vm.sh` = IS instruments, NOT the MTDS matrix).
      Execute the matrix only AFTER B+A are green + a re-proof shows `captured` climbing. — deployment-service@c89c90c |
      All defi MTDS launchers confirmed e2-standard-8 + MANIFEST_PER_VM_SHARDS=true; added VM_NAME to METADATA in
      vault-share-price + gas-fees launchers (were missing from per-VM shard key).

### 2026-06-21 — TRADFI lane: launcher bugs diagnosed + fixed; CME-2026 canary verifying

Measured (consolidated v9 `_index`, `market-data-tick-tradfi-prd-…`): **1.94M rows, 99.7% v9** (only 6444 at v4). The
dispatch's "v9 46.6%" is the **instruments-store (IS)** index, NOT the MTDS market-data index — MTDS tradfi is already
v9. Capture: 102936 captured / 1.007M empty / 10013 failed / **818k expected_unattempted** (5.3% honest-cov).
**Fillable-gap reality (3-dataset subscription):** only `ohlcv_1s`/`ohlcv_1m` on GLBX.MDP3(CME) /
DBEQ.BASIC(NASDAQ,NYSE) / XCBF.PITCH(CBOE) are batch-fillable; the unattempted ohlcv_1s/1m is **ALL 2026-YTD** (CME
160767, NYSE 48270, NASDAQ 14184, CBOE 212; pre-2026 already attempted=empty/captured). The remaining ~595k unattempted
is genuine honest absence under the subscription: `trades`/`tbbo` (L1, >1yr free window), `mbp_10` (L2, >1mo),
`ohlcv_15m`/`24h` (DERIVED, aggregated not fetched), and `ICE`/`BARCHART`/`YAHOO`/`FX` venues (off the 3-dataset
allowlist; ICE→IFUS.IMPACT not subscribed). Adapter `_get_dataset_for_exchange` correctly maps NASDAQ/NYSE→DBEQ.BASIC,
CBOE→XCBF.PITCH (launcher header comments mentioning XNAS.ITCH are stale; routing is on-allowlist). **Two launcher bugs
(root-caused via T+10min run.log verify — both rc=0/1 with 0 rows = SILENT FAILURE):**

1. Wrapper bare-`python3` UAC enumeration (ModuleNotFoundError) — **already fixed by peer @e31817b** (uses
   `${WORKSPACE_ROOT}/.venv-workspace/bin/python3`; verified UAC-importable). No action.
2. **`VM_TASK=cefi-backfill` (copy-paste) + no `--source`** → routed AWAY from the chunked MTDS-download branch; handler
   raised `--source databento|massive is REQUIRED` on every payload. FIX (deployment-service): lib
   `_tradfi-ohlcv-launcher-lib.sh` → `VM_TASK=mtds-backfill` + `VM_SOURCE=${OHLCV_SOURCE:-databento}`;
   `setup-data-pipeline-vm.sh` reads `VM_SOURCE` + adds `--source $VM_SOURCE` in the mtds-backfill BASE_CLI. (UAC
   `_VENUE_SOURCE_EXCLUSIONS` excludes only `massive` for CBOE → `databento` is capable for every tradfi OHLCV venue.)
   Plus end-date clipped to **yesterday** (Databento T+1). GCS startup re-uploaded with the fix (reset/collision-proof).
   **CME-2026 canary `tradfi-bf-cme-ohlcv-1m-es-2026-145146` relaunched + watcher armed.** ⚠️ Peer concurrently adding
   the `mtds-live` branch to the SAME `setup-data-pipeline-vm.sh` (live, dispatch item 3) — non-overlapping hunks.

- [x] ✅ [DATA] P0. **tradfi fan-out after canary-green**: NASDAQ + NYSE full DBEQ year-shards (2023-04-15→2026,
      force-window re-attempts wrongly-empty equity history) + CBOE/XCBF (needs a CBOE wrapper — VX-futures universe) +
      CME 2026. Repo: deployment-service. — deployment-service@f243eb4 | CBOE wrapper created
      (`launch-tradfi-bf-cboe-ohlcv-1m.sh`, XCBF.PITCH/VX.FUT, 2026-01-01 floor) + forward-poll fixed
      (VM_TASK=mtds-backfill + VM_SOURCE=databento + VM_NAME + MANIFEST_PER_VM_SHARDS). All 17 VMs RUNNING.
- [x] ✅ [SCRIPT] P1. **deployment-service: launcher fix committed durably** — deployment-service@9aca3a5 (lib
      `VM_TASK=mtds-backfill` + `VM_SOURCE=databento` + yesterday-end; startup `--source $VM_SOURCE` in mtds-backfill
      BASE_CLI). Shipped via isolated-worktree promotion (peer's relentless reset of the shared tree + the dirty-deps
      carve-out blocked normal quickmerge); QG-green 51s; GCS startup re-uploaded with the fix. CME-2026 canary PROVEN
      capturing (`GLBX.MDP3/ohlcv_1m → batch_databento` parquets + per-VM manifest shard).

### 2026-06-21 15:18 — TRADFI batch fan-out LIVE + PROVEN (15 VMs capturing)

Launcher fix committed ds@9aca3a5 (isolated-worktree promotion past peer collision). **15 tradfi-bf VMs all confirmed
capturing** `→ batch_databento` parquets + per-VM manifest shards: CME-2026 (7 roots, GLBX.MDP3), NASDAQ full-history
2023-26 (4, DBEQ.BASIC), NYSE full-history 2023-26 (4, DBEQ). NASDAQ-2024 proven writing REAL equity data (SNPS/INTU/…
613/529/… rows) → the prior equity `empty_confirmed` history WAS wrongly-empty; the force-window DBEQ re-run fills it
(big honest-cov lever). Monitoring the drain (VMs self-delete on completion); will re-measure honest-cov + relaunch any
failure on wave completion. REMAINING tradfi: CBOE/XCBF (VX-futures wrapper — small gap), IS v9 canonicalisation
(instruments-store index 46.6%→100%; the `canonicalize_instruments_store_index.py` N2/F5/N4 dedup + asset_group/source/
pipeline_mode bump — overlaps peer's UAC source_priority work), LIVE forward-poll (peer building `mtds-live` branch).

### 2026-06-21 15:42 — TRADFI lane: ALL 3 dispatch items launched/done

- ✅ [IS] **IS tradfi v9 canonicalisation DONE** (sub-agent, verified on live blob): `instruments-store-tradfi-prd`
  `_index` now **schema_version 100% v9** (was 46.6%), **asset_group 100% `tradfi`** (was absent), **source 0% blank**
  (`instruments_service`), **pipeline_mode 0% blank** (`batch_instruments_service`), capture_status 14045/581 unchanged
  (no fabrication). Mechanism = `instruments-service/scripts/populate_is_index_v9_2026_06_19.py --apply` (the
  column-bump walk; the named `canonicalize_instruments_store_index.py` is dedup-only). Pre-apply snapshot written.
- ✅ [DATA] **LIVE forward-poll wired** — fixed `launch-tradfi-forward-poll.sh` (same cefi-backfill/no-`--source` bug):
  ds-commit (VM_TASK=mtds-backfill + VM_SOURCE=databento + VM_DATA_TYPES=ohlcv_1m). Launched the **daily-cron host VM**
  `tradfi-fwd-daily-cron-20260621-154132` (RUNNING, fires 06:00 UTC daily → `launch-tradfi-forward-poll.sh` T-1) + an
  immediate T-1 forward-poll. Fixed launcher uploaded to the cron's GCS path. This is the tradfi LIVE/recurring
  mechanism (markets are T+1; daily forward-poll = the live keep-current path).
- ✅ [DATA] **CBOE/XCBF launched** (3rd subscribed dataset) — peer had committed a `launch-tradfi-bf-cboe-ohlcv-1m.sh`
  (better 2026-floor scope); I accidentally clobbered it then **restored their version + fixed a real venue bug**
  (`XCBF`→`CBOE`: the adapter maps CBOE→XCBF.PITCH; `XCBF` is unmapped→GLBX default). Launched CBOE-2026 (VX.FUT). Keep-
  both-sides reconcile (ds@f43f50a restore + @3bed824 venue fix).
- Batch fan-out (15 VMs CME/NASDAQ/NYSE) still draining + capturing `batch_databento`. CBOE + forward-poll capture
  verification in flight. The 3-dataset tradfi batch (GLBX+DBEQ+XCBF) is now ALL launched.

### 2026-06-21 16:25 — ohlcv_1s added (CME+CBOE only; equities don't support it)

Operator: grab ohlcv_1s. Shipped ds@47c56d7 — lib + forward-poll default VM_DATA_TYPES now `ohlcv_1m;ohlcv_1s`
(OHLCV_DATA_TYPES env override). **Key correction:** ohlcv_1s is expected ONLY for **CME + CBOE (futures)** per UAC
`expected_coverage` (`CME:[trades,ohlcv_1s,ohlcv_1m,tbbo]`, `CBOE:[ohlcv_15m,ohlcv_1s,ohlcv_1m]`); **NASDAQ/NYSE list
`[ohlcv_1m]` only** — equities (DBEQ.BASIC) have NO 1s, and the MTDS pre-flight correctly drops it
(`dropping data_types not supported per UAC: ['ohlcv_1s']`). So equity-1s is NOT a gap. Deleted the 8 no-op equity-1s
VMs; launched **CME-1s full-history** (7 roots × 2019-2026) + CBOE-1s. The default-both is harmless for equities
(pre-flight drops 1s, fetches 1m). Operational health verified: 0 real rate-limit events fleet-wide, 0 code failures,
liquid tickers captured.

### 2026-06-21 16:40 — CME event contracts (binary/event markets) — IS + MTDS

Operator: capture CME event markets. The 9 CME event-contract roots (ECES/ECBTC/ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E/ECNQ,
GLBX.MDP3 .OPT parents, Databento coverage from 2025-09-28, classified EVENT_CONTRACT). On-allowlist (GLBX subscribed);
UAC has `CME:{...,EVENT_CONTRACT}`. Findings:

- **IS index had ZERO event-contract instruments** — `launch-tradfi-event-contract-backfill.sh` (VM_TASK=instruments-
  backfill, `--operation instruments`, no `--source` needed) had **never run**. Launched it
  (`tradfi-event-contract-backfill-20260621-163633`); verifying EC instrument definitions land in
  `instruments-store-tradfi-prd` `_index`.
- **MTDS had 1438 captured EC\* cells** (all 9 roots, 2025-09-28→2026-06-17: trades 1296, ohlcv_1m 124, ohlcv_1s 18) —
  ohlcv sparse because the EC roots weren't in the CME OHLCV backfill. Launched a dedicated **MTDS EC\* OHLCV backfill**
  (9 EC roots, 2025-09-28→yesterday, ohlcv_1m+1s) to complete it.
- ohlcv_1s health re-confirmed: CME-1s capturing (es-2024 `data_type=ohlcv_1s`); **0 rate-limit events across 38 VMs**
  (no self-cap needed). CME-1s full-history wave was timeout-killed partway → relaunched the remaining roots
  (CL/GC/ES_OPT + MNQ tail) in background.

### 2026-06-21 17:49 — TRADFI LIVE producer launched (live_databento; live==batch)

Operator probe: the forward-poll = `batch_databento` (T-1 download), NOT real-time `live_databento` → tradfi LIVE rows
still 0. Launched the genuine live producer: `mtds-live-tradfi-cme-trades-20260621-174904` (e2-standard-8,
LONG*LIVED_LIVE) via
`launch-mtds-live.sh --asset-group tradfi --shard-spec tradfi:CME:trades --instrument-ids "ES;NQ;CL;GC"`. The
`databento_tradfi_ws` connector subscribes `schema=trades`, `SType.PARENT`, aggregates → live candles stamped
`live_databento` (live==batch: same schema/data_types,
pipeline_mode=`live*<source>`). Uses the existing `databento-api-key` (in Secret Manager). US markets OPEN (17:49 UTC).
Verifying it connects to Databento **Live** streaming (the one open question = whether the account's subscription
includes Real-Time/Live; if not → genuine BLOCKED-CREDENTIALS, the only acceptable non-completion). Watcher armed.

- [x] ✅ [SCRIPT] P2. **deployment-service: harden the VM log-uploader thread** — on the CME-1s VMs the GCS run.log
      uploader froze ~16:35 (large 1s logs) while the run + heartbeat + shard-writes continued fine (heartbeat fresh, no
      premature watchdog kill). Cosmetic (can't tail those logs) but worth a try/except + re-arm in the uploader loop.
      Repo: deployment-service (setup-data-pipeline-vm.sh uploader daemon). — unified-trading-library@5ed6824c
      (lifecycle/uploader.py: daemon-thread + 90s join timeout caps blocking upload_bytes();
      test_blocking_upload_does_not_freeze_loop added)

### 2026-06-21 — DEFI lane: RE-SEQUENCED per operator (IS→100%→rollup→MTDS) + real hang root-cause

**Operator correction (CORRECT):** run the catalogue roll-up AFTER instruments are 100%, THEN MTDS — the catalog-stale
honest-absence is EXPECTED (live catalog has no historical snapshots until the lifecycle roll-up builds them); don't run
MTDS before the catalog. So I KILLED the premature 60-VM MTDS fan-out (was burning empties + hung). **Real stuck
root-cause (fleet-health diag — NOT rate limits):** sync GCS read (`ManifestFreshnessCache.bulk_load()` /
`assert_defi_catalog_fresh` → stale-index 28-shard merge) blocks the asyncio event loop every ~3rd date (60s cache TTL)
→ log-uploader starves → VM looks hung. Fleet-wide. FIX in flight: agent af7784c36 wraps blocking reads in
`asyncio.to_thread`. (A `VenueRateLimiter` 10rps token-bucket already exists → no rate-cap needed; 0 × 429 observed.)
**TheGraph 9-key sharding SHIPPED (mtds@5830cc8):** dex_pools/dex_swaps were single-key (`thegraph-api-key`) → now
round-robin across the 9-key SM pool (`thegraph-api-key[-2..9]`); base-client count 20→actual. (Operator's point.)
**STATE NOW:** IS instruments backfill COMPLETE (VMs gone). Catalogue roll-up `lifecycle-catalogue-regen-defi-7844r`
**FAILED** (failedCount=1) — diagnosing (bzjvsz4qj) + must re-run on the complete IS set. 12 leftover MTDS VMs killed.
**LIVE (operator Q):** live==batch (same canonical schema/path/data_types; only `pipeline_mode=live`). Defi live source
= ON-CHAIN (Alchemy RPC / TheGraph / Pyth Hermes), **NOT databento** (that's tradfi). Defi live = collect-\* handlers
`--mode live` polling forward (launch-defi-forward-poll.sh stub → wire). **REMAINING SEQUENCE (autonomous, operator away
2h):** (1) re-run roll-up (after confirming IS 100% + IS consolidated) → produces fresh instrument-catalog. (2) rebuild
VM tarball with sharding+asyncio fixes. (3) re-run MTDS defi fan-out → VERIFY capture (canary) + no hang. (4)
execution-defi consolidator → honest-cov climbing. (5) MDPS defi. (6) defi live forward-poll → ≥1 live row. (7)
terminate at 100%. Live agents: af7784c36 (asyncio fix), bzjvsz4qj (rollup diag).

### 2026-06-21 17:55 — TRADFI live_databento: diagnosed (3 bugs + subscription unknown) — FLAGGED not stomped

Launched a real tradfi live producer (`mtds-live-tradfi-cme-trades`) to test live==batch. It FAILED — 3 precisely
root-caused bugs in the (peer's, in-flight) `mtds-live` / `databento_tradfi_ws` live scaffold + 1 vendor unknown.
**Deleted the broken VM** (it wrote 4 wrong `live_massive` empty rows). Bugs (filed for the live-pipeline lane; NOT
fixed here — the UAC file is actively peer-edited + needs a tarball rebuild + the subscription is unconfirmable):

- [x] ✅ [SCRIPT] P1. **mtds: `databento_tradfi_ws._get_api_key()` reads the raw Pydantic field
      `cfg.databento_api_key`** (None unless `DATABENTO_API_KEY` env set) → logs
      `no API key — connection skipped (BLOCKED-CREDENTIALS)`. The BATCH path resolves the key from the
      `databento-api-key` **secret** via the secret client (works). Fix: `_get_api_key` fallback-resolves
      `databento_secret_name` via `get_secret_client()` like batch. Repo: market-tick-data-service. —
      market-tick-data-service@e532105
- [x] ✅ [SCRIPT] P1. **UAC: `live_source_for_venue(tradfi,…)` mis-stamped live rows `live_massive`** — resolved tradfi
      live/replay via the BATCH `SOURCE_PRIORITY[0]=massive`. **CORRECTION** to the original framing: `massive` IS
      live-capable (operator 2026-06-05, Polygon.io 15-min REST — NOT batch-only; do NOT remove its `Mode.LIVE`). Real
      root cause: the SOLE tradfi live **WS producer** is `databento_tradfi_ws` (massive/yahoo/barchart have no live WS
      connector). Fix = a `tradfi` branch in `live_source_for_venue` → `databento` (mirrors
      `_PREDICTION_LIVE_SOURCE_FOR_VENUE`); batch path unchanged (`get_primary_source(tradfi,*)=massive`). —
      unified-api-contracts@1205ae44 | verified `live_pipeline_mode_for_venue(tradfi,*)=live_databento` + 48/48
      `test_source_priority_pipeline_mode.py` green | isolated-worktree promotion (concurrent peer WIP on
      `_source_priority_data.py` preserved, not bundled).
- [x] ✅ [DATA] P1. **launch-mtds-live.sh tradfi instrument-ids format** —
      `CME:FUTURES:ES;CME:FUTURES:NQ;CME:FUTURES:CL;CME:FUTURES:GC` (`_parse_instrument_id` needs
      `venue:type:underlying`). — relaunched `mtds-live-tradfi-cme-trades-20260621-213416` → CONNECTED + authenticated
      (`session_id` issued) + streaming live ticks.
- [x] ✅ [DATA-OPERATOR] P0. **Databento Real-Time/Live subscription CONFIRMED** (operator 2026-06-21: the usage-based
      plan includes Live data + 1yr L1 / 1mo L2-L3 history — the live WS is NOT subscription-blocked). The producer
      connects + authenticates against `wss://live.databento.com`.
- [ ] [DATA] P1. **Deploy the `live_databento` stamp fix (UAC@1205ae44) to the running live producer** — the live VM
      bakes UAC from a GCS **tarball** (working-tree tar), so `mtds-live-tradfi-cme-trades-*` keeps `live_massive` until
      a `create-code-tarballs.sh` rebuild **from a clean LDR checkout** (NOT this peer-WIP dev workspace) + relaunch.
      The daily forward-poll cron relaunches but REUSES the existing tarball — a tarball rebuild is the gating step.
      Repo: deployment-service. Provenance: this Progress Log. NOTE: the dispatch's tradfi LIVE item (forward-poll T-1 +
      daily-cron host) IS done (`batch_databento`); `live_databento` websocket is beyond-dispatch peer-domain work, now
      fully diagnosed for them.

### 2026-06-21 — DEFI lane: CATALOG GATE OPEN — capturing real data; full fan-out relaunched

**BREAKTHROUGH:** canary captured real lst_rates to
`market-data-tick-defi-prd/raw_tick_data/by_date/day=2026-06-14/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=STAKEWISE/.../data_type=lst_rates/...`
(stakewise/ankr/etherfi/puffer ETHEREUM + jito SOLANA). Full fix stack works. **TRUE catalog root-cause (after
bucket/sharding/asyncio/rollup/data_type/staleness layers):** the MTDS preflight reads
`build_bucket("instruments","defi")` = **`instruments-store-defi-central-element-323112` (env-LESS legacy, 23.9d
stale)**, but ALL writers (IS backfill, catalogue roll-up, data_type stamp) wrote **`instruments-store-defi-prd-…`
(env-SHORT, fresh)**. Reader↔writer bucket mismatch (same env-less-vs-`-prd-` class as the orig market-data bug).
**IMMEDIATE FIX (applied):** `gcs_copy_object` synced `…-prd-…/_index/availability_index.parquet` → the env-less bucket
(fresh 18:32; valid 24h via staleness=86400; MTDS writes market-data not instruments so env-less stays fresh through the
run). **Full 60-VM fan-out relaunched** (agent ab14773159be4e222) — gate open → real capture. execution-defi
consolidator next.

- [x] ✅ [DATA] P1. **DEFI durable bucket-align fix (so env-less can't re-stale):** the instruments preflight reader
      `build_bucket("instruments","defi")` resolves env-LESS legacy; canonical writers use env-SHORT `-prd-`. Align:
      make the reader resolve canonical `-prd-` (verify per-AG it doesn't break cefi/tradfi/sports — they may be
      env-less-aligned), OR point the IS consolidator to also refresh env-less. Until then a periodic env-short→env-less
      index sync keeps defi capture alive. Repo: unified-trading-library (build_bucket) / instruments-service.
      Provenance: this Progress Log. — market-tick-data-service@72f7c14 | replaced
      `build_bucket("instruments", project_id=project_id, asset_group="defi")` with
      `get_bucket_name("instruments", "defi")` in `_defi_manifest.py`; yaml delegation now fires → env-SHORT `-prd-`
      bucket resolved
- [x] ✅ [SCRIPT] P2. **commit the defi launcher staleness edits** (MANIFEST_CONSOLIDATED_STALENESS_SEC=86400 added to
      11 defi MTDS launchers — working locally, used by the live fan-out; persist via quickmerge). Repo:
      deployment-service. — deployment-service@e74517c

### 2026-06-21 19:40 — TRADFI honest-cov re-measured: 5.3% → 13.8% (captured TRIPLED), still climbing

Consolidated `_index`: captured **102,936 → 310,180** (3×), `ohlcv_1s` **3,187 → 48,656** (15×), schema 99.7% v9.
Landed: NYSE ohlcv_1m **125,915** (full DBEQ equity history — was ~0/wrongly-empty), CME ohlcv_1m 68,729 + ohlcv_1s
49,171, NASDAQ 36,295, CBOE 135. **0 failures from this backfill** (the 9,998 `attempted_failed` are STALE 2026-04-30→
05-26 pre-existing runs). 12 CME-1s VMs still finishing (re-armed finalizer). The flat 818k `expected_unattempted` is
**structural honest-absence**, not a gap: trades/tbbo/mbp_10 (L1/L2 window-bound, un-backfillable historically),
ohlcv_15m/24h (MDPS-DERIVED not MTDS-fetched), ICE (off-allowlist). Two real manifest items found:

- [ ] [DATA-OPERATOR] P2. **NYSE/NASDAQ `ohlcv_1s` expected_unattempted (~31k cells) — GENUINE OPERATOR DECISION, not a
      clean phantom (investigated 2026-06-21).** The original "equities don't support 1s → drop" framing is WRONG: the
      Databento allowlist ALLOWS `DBEQ.BASIC + ohlcv-1s` (it IS available), and the `(tradfi,equity)`/`(tradfi,etf)`
      validity matrix + the design comment explicitly list equity 1s ("fetched alongside 1m for every GLBX.MDP3 /
      DBEQ.BASIC instrument_type"). BUT `expected_coverage NASDAQ/NYSE=[ohlcv_1m]` DELIBERATELY excludes 1s (equity 1s =
      thousands of tickers × seconds = enormous volume — a plausible deliberate exclusion), and the MTDS pre-flight
      drops it. So the two registries genuinely DISAGREE and the resolution is **opposite-direction +
      high-cost-if-wrong**: (A) if equity 1s is in-scope → ADD it to `expected_coverage` + backfill (the cells become
      CAPTURED, more data); (B) if deliberately excluded → gate the IS enumerator's seed on `expected_coverage` (the
      cells stop being seeded). Per "don't fix apparent inconsistency blindly" this needs the operator's call on whether
      equity `ohlcv_1s` is in-scope to fetch. Repo: unified-api-contracts (expected_coverage / market_data_categories) +
      instruments-service enumerator. Provenance: this Progress Log.
- [ ] [DATA] P2. **ohlcv_15m/24h (~207k unattempted) are MDPS-derived** (aggregated from 1m/1s), not MTDS-fetched — they
      convert to captured when MDPS aggregation runs over the new 1m/1s corpus. **LAUNCHED 2026-06-21:**
      `mdps-backfill-tradfi-20260621-213646` (RUNNING, `launch-mdps-backfill-vm.sh tradfi 2020-01-01 2026-06-20 full`) —
      re-aggregates the captured 1m corpus into 15m/24h. Leave open until the manifest shows the 15m/24h cells
      converting captured (verify post-drain). Repo: market-data-processing-service. **PRACTICAL BLOCKER (2026-06-21):**
      the MDPS `ManifestWriter` rewrites the WHOLE per-VM shard parquet PER CELL ("930 total entries, 1 new" every
      ~30ms) → sustained GCS 429 object-mutation rate-limits + O(n²) cost; at 207k target cells it will not
      realistically complete (consolidated index still shows 103,651 unattempted each for 15m/24h while the VM has
      written only ~930 entries). Pre-existing MDPS behavior. Needs the per-VM shard write BATCHED (accumulate N cells /
      debounce, then one write) before a large MDPS backfill is practical. Repo: market-data-processing-service
      ManifestWriter.

### 2026-06-21 — DEFI lane: capturing works, but honest-cov BLOCKED by venue-format mismatch in expected_unattempted seeding

Full ~60-VM fan-out CAPTURING real data (dex-pools 5232 rec/day, dex-swaps 44k-102k/yr,
lst/liq/vault/pyth/gas/jito/marinade) → canonical v9 path. BUT **honest-cov only 6.0%→6.2%** after 50min: captured
369k→384k, **expected_unattempted FLAT at 2.31M** — captures create NEW rows, DON'T convert the unattempted. **ROOT
CAUSE: format mismatch.** expected_unattempted rows: venue=`BALANCER-ARBITRUM` (legacy combined PROTOCOL-CHAIN) +
chain=`''` (blank) + dates 2026-02-20..06-18 (recent window only). Captured rows: venue=`BALANCER` + chain=`ARBITRUM`
(CANONICAL per defi-canonical-naming-ssot) + dates 2021..2026. Different shard keys → never match → the 2.31M
legacy-format unattempted are effectively PHANTOMS the canonical captures can't convert. (Also 3.5M empty_confirmed =
genuine honest absence → max honest-cov ≈ 43% once 2.31M convert, NOT 100%; "100%"=fetchable-gap-closed.) **FIX (in
flight):** re-seed the defi expected-universe in CANONICAL venue/chain format (the `expected-universe-v2-defi`
enumerator / `enumerate_expected_universe.py` still emits legacy PROTOCOL-CHAIN) so captures convert it; OR
phantom-reconcile the legacy unattempted. The CAPTURING is correct + real; only the seeded denominator is mis-formatted.
Agent dispatched. Batch fan-out continues (39 VMs mid-year-shard, progressing).

- [x] ✅ [DATA] P0. **DEFI expected-universe canonical re-seed:** `enumerate_expected_universe.py` /
      `expected-universe-v2-defi` seeds expected_unattempted with LEGACY venue=`PROTOCOL-CHAIN`/chain=blank; handlers
      capture canonical venue=`PROTOCOL`/chain=X → no conversion → honest-cov stuck. Fix enumerator to emit canonical
      venue/chain (per defi-canonical-naming-ssot) + re-seed (replace legacy unattempted) + phantom-reconcile leftovers.
      Repo: instruments-service. Provenance: this Progress Log. — instruments-service@38cec01 | `_enumerate_defi` now
      emits `venue=protocol.upper()` (e.g. BALANCER) + `chain=ARBITRUM` separately; conflict-merged with concurrent
      upstream fix at 3e8fcd0

### 2026-06-21 — DEFI honest-cov fix LANDED (root-cause in code) + codified

Enumerator root-caused + FIXED in code: `enumerate_expected_universe.py:395` emitted legacy `venue=PROTOCOL-CHAIN` →
canonical `venue=PROTOCOL` (quickmerged). The 2.31M `expected_unattempted` were ALL legacy-format phantoms → removed;
canonical universe re-seeded. **honest-cov 6.2% → 10.1%** (captured 392k; expected_unattempted 2.31M→0; total
6.21M→3.88M after phantom removal) and CLIMBING as the fan-out flips canonical empties→captured. 3.46M empty_confirmed =
genuine pre-genesis/pre-launch honest absence (correct denominator). **5 durable root-causes codified** in CLAUDE.md +
codex `defi-canonical-naming-ssot.md` § "DeFi data-pipeline DURABLE gotchas" (pm@d752c584c). Durable build_bucket
env-less→-prd- reader-align dispatched (replacing the stop-gap index-copy). Batch fan-out still capturing (drive monitor
bdnexk0ku).
