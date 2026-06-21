---
title: Data completion to 100% — all asset groups, batch + live, manifest v9 (MTDS + IS)
created: 2026-06-21
parent_epic: mtds_mdps_master
assigned_vm: planning
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
- [ ] [DATA] P0. **defi** — `launch-defi-backfill-vm.sh` (fill 2.31M unattempted: gas-fees [running] + lst-rates +
      dex-pools/swaps + lending-indices + liquidations + vault-share + pyth) + `launch-defi-forward-poll.sh` (LIVE).
      Repo: deployment-service.
- [ ] [DATA] P0. **tradfi** — full 3-dataset batch (GLBX done via CME-b; **DBEQ.BASIC**
      `launch-tradfi-bf-nasdaq/nyse-ohlcv-1m.sh` + **CFE/XCBF**) to fill 818k unattempted +
      `launch-tradfi-forward-poll.sh` (LIVE). Repo: deployment-service.
- [x] [DATA] P0. **sports** — `launch-mtds-sports-odds-backfill-vm.sh` + `launch-sports-is-gap-fill.sh` /
      `launch-sports-full-sweep-vm.sh` (IS sports 15.9%→100%) + `launch-footystats-forward-poll.sh` (LIVE). Repo:
      deployment-service. ✅ — VMs RUNNING (T+10min verified): odds-backfill=mtds-backfill-odds-{2020..2026} (7 VMs, chunk 1/31 writing rows), IS-sweep=sports-full-sweep-{2019..2026} (8 VMs, writing instruments-store parquets), fwd-poll=footystats-fwd-20260621-142249 (RUNNING). Bug fix: deployment-service@b42d98c (removed VM_TIER from sports MTDS launcher; --tier has no MTDS CLI arg)
- [x] [DATA] P0. **cefi — 802k `attempted_failed` TRIAGED** (CEFI lane 2026-06-21, measured from consolidated v9
      `_index`): by source — **tardis 753,341 + 22,519 phantom = 775,860 (96.7%) Tardis-gated** (batch_tardis;
      historical billing EXCLUDED → BLOCKED-CREDENTIALS) · **hyperliquid 30,835 + aster 17,675 = 48,510 free-venue
      re-fetchable** (native, no Tardis) · 124 misc. Re-fetchable failed cells span HL 2023-26 / ASTER 2024-26 across
      {trades, book_snapshot_5, derivative_ticker, liquidations}. Repo: deployment-service.
- [ ] [DATA] P0. **cefi — re-fetch the 48.5k free-venue (HYPERLIQUID+ASTER) failed cells** year-sharded via
      `launch-cefi-onchain-forward-poll.sh` (native venues = free; `--mode batch`). Expect a portion to resolve
      `attempted_failed→empty_confirmed` where the venue genuinely has no historical data_type (honest absence). Repo:
      deployment-service.
- [ ] [DATA] P0. **cefi — LIVE stream → ≥1 `live_<source>` row.** **BIG FINDING:** the named
      `launch-cefi-forward-poll.sh`/`launch-cefi-onchain-forward-poll.sh` run `--mode batch` → BILLED Tardis replay +
      `batch_<source>` rows (NOT free, NOT live) — running them as-named would violate the Tardis-billing exclusion AND
      miss the live goal. The FREE live path is `launch-mtds-live.sh --asset-group cefi` →
      `--operation websocket-streaming --mode live` (real-time exchange WS proxy, free; 18 cefi connectors registered
      since 2026-05-17 Phase 3.5). Blocker: that path is NOT wired into `setup-data-pipeline-vm.sh` (no `live_websocket`
      branch → falls through to `--mode batch`) + needs `--shard-spec`/`--instrument-ids`/`streaming_redis_url`. Fix =
      wire the live branch + local redis, then launch. Repo: deployment-service (+ verify MTDS handler). Reusable across
      ALL AGs (live=0 everywhere).
- [x] [DATA] P0. **cefi — IS reference-data VERIFIED 99.9%** (36,062/36,084 captured, fully schema_version=9, only 22
      failed) — done, no re-run. (CEFI lane 2026-06-21.)
- [x] [DATA] P1. **cefi — BLOCKED-CREDENTIALS ask FILED** for the 775.9k Tardis-gated failed cells (Tardis historical
      replay subscription, SM key `tardis-api-key`) — issue doc
      `plans/active/issues/cefi_tardis_historical_blocked_credentials_2026_06_21.md` + `CREDENTIAL APPROVAL REQUEST` in
      `plans/active/_agent_pings.md`. **Batch Tardis (historical) EXCLUDED — billing-gated (operator).** Repo:
      deployment-service. (CEFI lane 2026-06-21.)
- [ ] [IS] P1. **IS tradfi v9 canonicalisation** — only 46.6% at schema_version=9; run the tradfi `_index`
      canonicalisation walk (8→9: source/asset_group/pipeline_mode) so the index is fully v9. Repo: instruments-service
      / market-tick-data-service.
- [ ] [DATA] P1. **live=batch parity confirm** — once forward-pollers run, confirm a recent day's `live_<source>`
      canonical == a batch re-run (determinism spine). Repo: market-tick-data-service.

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
- [ ] [SCRIPT] P0. deployment-service — **`launch-tradfi-bf-nasdaq-ohlcv-1m.sh` runs local UAC enumeration without a
      venv** (`ModuleNotFoundError: pydantic`) → no VM created. Invoke via the workspace venv. Repo: deployment-service.
- [ ] [DATA] P1. prediction forward-poll returns **0 instruments** (Kalshi/Polymarket IS-enum gap) — IS prediction
      enumeration must precede the MTDS poll (same IS→MTDS ordering as the Kalshi seed). Repo: instruments-service.
- [ ] [TERRAFORM] P0. **deployment-service terraform must reflect the CANONICAL bucket names after the bucket-name
      updates** (operator 2026-06-21): the consolidator schedulers (`manifest_consolidator_scheduler.tf`) + any per-AG
      bucket refs must use the canonical `market-data-tick-{ag}-prd-…` / `instruments-store-{ag}-prd-…` (env-short) —
      the lst-rates malformed-bucket bug suggests launcher/terraform bucket drift; audit + `terraform apply` so every
      consolidator + launcher targets the canonical bucket. Repo: deployment-service. SSOT: bucket_name_ssot plans.

## Codex SSOT updates

- [ ] [DOCS] P2. codex/02-data/availability-manifest-and-data-status.md — add the 2026-06-21 per-AG snapshot + the
      live-mode-population gap as a tracked baseline.

## Progress Log

### 2026-06-21 — snapshot measured + fleet launch begun

Coverage snapshot above (measured, not memory). Kalshi seed VM re-launched (runner set-u fix mtds@74e228c). Fleet
launch + monitoring loop starting (this plan is the path-to-100% plan-of-record).

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
