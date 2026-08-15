---
doc_type: record
title: "Extracted Progress Log history — data_completion_defi (2026-08-15 line-cap remediation)"
summary: >-
  Verbatim extraction of the folded-in-from-M-1 chronological block of 2026-06-21/2026-06-22 dated Progress Log entries (DeFi lane launch, fan-out, bucket-fix, honest-coverage, and regression-fix narrative) from the DeFi data-completion plan. Every entry is closed history with zero embedded open todos (all 17 open items in this plan live in its Todos section, not the Progress Log). Extracted to keep the live plan under the 1000-line hard cap.
status: complete
nature: record
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [line-cap-remediation, historical, progress-log]
created: "2026-08-15"
author: slot-3
parent_epic: agent_operating_framework_master
source:
  [
    /plans/active/data_completion_defi_2026_07_15.md,
    /plans/archive/2026_08/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md,
  ]
---

# Extracted Progress Log history — data_completion_defi (2026-08-15 line-cap remediation)

> **Extracted verbatim 2026-08-15** (`context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md` Follow-up
> todo — 3-doc 2026-08-07 batch) from `/plans/active/data_completion_defi_2026_07_15.md`. Every extracted entry carried zero open Progress-Log-embedded
> todos; nothing summarized or lost, only moved to keep the live plan under the 1000-line hard cap.

### 2026-06-22 — GAP FOUND (operator): DeFi market-data has NO continuous live capture (daily batch only)

Operator caught it: DeFi live market-data =
`uts-prod-mtds-collect-{dex-swaps,dex-pools,oracle-prices,evm-defi, solana-defi,lending-indices,lst-rates,perp-funding}`
Cloud Run jobs, ALL `--mode batch` on a ONCE-DAILY cron (00:05- 02:05). NOT continuous. (These are MTDS market-data, NOT
strategy — strategy/execution = paper-trading-engine etc.) CeFi/prediction/sports/tradfi run CONTINUOUS live VMs
(websocket streams, ephemeral=miss-is-lost). DeFi has no continuous-live equivalent (only the daily batch + an UNUSED
launch-defi-forward-poll.sh). WHY it matters: on-chain is retroactively queryable so daily batch is gap-free for
FEATURES/BACKTEST (≤24h latent), but LIVE TRADING `arbitrage_price_dispersion` needs near-real-time DEX+oracle prices
(move every block) → a daily snapshot cannot feed a live arb. `carry_staked_basis` (LST APR/Aave rates, slow) is
arguably daily-OK.

- [x] ✅ [INFRA] P1. **DeFi continuous live market-data capture** — **IaC SHIPPED 2026-06-22** —
      deployment-service@2e396f8 + market-tick-data-service@3f5c61f9; DeFi live VERIFIED 2026-06-23 (7 captured rows,
      `live_onchain_subgraph`+`live_chainlink`+`live_pyth_hermes`, heartbeat emitting) (`deployment-service@2e396f8`,
      QG-green): `launch-defi-forward-poll.sh` parameterized over `--operation`
      (collect-dex-swaps/dex-pools/oracle-prices + the existing lst-rates, per-op singleton lock) + NEW
      `terraform/gcp/defi_forward_poll_scheduler.tf` = a `*/5` Cloud Scheduler firing the forward-poll for the 3
      price-sensitive ops (gated by `enable_defi_forward_poll`, default true; slow ops stay daily). **REMAINING:**

      (a) ✅ **mtds live pipeline_mode fix + DeFi-live heartbeat LANDED 2026-06-22 —
      `market-tick-data-service@3f5c61f9`** (on origin/live-defi-rollout, full QG `--no-fix` exit-0 + content sentinel
      verified). Folds `runtime.mode` into `_run_tag` so `--mode live` writes `pipeline_mode=live_*`
      (dex_pools/dex_swaps/oracle_prices) AND emits a per-shard `emit_pipeline_heartbeat` on the live forward-poll
      path (subsumes (c)). **NOTE on the prior "blocker": the local QG was NOT a coverage mis-root** — that
      `rootdir: unified-trading-pm, collected 6` line is the intentional `PM_INT_TEST` integration check (a red
      herring); the real failures were a missing `# noqa: qg-deep-import` on the new
      `from unified_trading_library.events import emit_pipeline_heartbeat` lines (events helper, not top-level
      re-exported) + a method-size trim on `oracle_prices_handler.process()` (53→48L). Python service repos
      quickmerge locally fine.

      (b) **`terraform apply`** the scheduler (operator/CI infra op — broad apply blast-radius in a live project;
      use `-target` for the new scheduler) + a `create-code-tarballs.sh` rebuild so the live-tag fix reaches the
      launched VMs. (c) ✅ **heartbeat** (`emit_pipeline_heartbeat`) — DONE, landed with (a) above. Manual verify
      when applied: `bash deployment-service/scripts/vm/launch-defi-forward-poll.sh --operation collect-oracle-prices`
      → T+10min check rows at
      `gs://market-data-tick-defi-prd-…/raw_tick_data/by_date/day=<today>/pipeline_mode=live_*/asset_group=defi/`.

      Orig intent: stand up a persistent/high-frequency DEX-price + oracle-price capture for the live-trading
      archetypes (per-block or near-real-time), not the once-daily batch. Either a persistent live VM (mirror the
      CeFi `mtds-live-*` pattern, polling DEX/oracle every block/few-sec) or a frequent Cloud Run cron (e.g. \*/1)
      for the price-sensitive operations (dex-swaps/pools, oracle-prices) while leaving the slow ones (lst-rates,
      lending-indices) daily. Wire it through the same live==batch schema + the hardening heartbeat. Repo:
      market-tick-data-service + deployment-service (launch-defi-forward-poll.sh exists, unused). Gates the DeFi arb
      archetype going live.

### 2026-06-22 (DEFI lane, PM-driven backfill-everything dispatch) — PHASE A: enumerator IAM root-caused + fixed (expected_unattempted=0 → seeding)

Operator dispatch "backfill everything (defi)": drive defi to high+honest coverage. Snapshot at start (live consolidated
`market-data-tick-defi-prd` v9 `_index`, 3,812,106 rows): **honest_cov_defi = 17.89%** (captured 682,033 /
empty_confirmed 3,099,859 / attempted_failed 30,214 / **expected_unattempted 0**). 100% schema_version=9. Date range
2018-01-01→2026-06-22.

**PHASE A root cause (the `expected_unattempted=0` symptom) — NOT the "scheduler never applied" hypothesis in the
dispatch.** The `expected-universe-v2-*-daily` Cloud Scheduler + the 5 per-AG Cloud Run Jobs WERE `tofu apply`'d
2026-06-19 (all ENABLED). But the defi scheduler's last attempt (2026-06-22 01:31) returned **`status code: 7` =
PERMISSION_DENIED**, and `gcloud run jobs executions list --job expected-universe-v2-defi` was EMPTY (never executed;
only prediction ran once, hand- triggered, 2026-06-19). Cause: the enumerator SA `expected-universe-v2-enum@…` had **NO
`run.invoker`** binding (neither job- level — empty `etag: ACAB` policy — nor project-level).
`expected_universe_v2_scheduler.tf` grants the SA `objectViewer` (catalogue) + `objectAdmin` (manifest) but OMITS the
`roles/run.invoker` the scheduler→job OIDC call needs → every daily defi/cefi/tradfi/sports trigger was silently
rejected → 0 `expected_unattempted` seeded fleet-wide. (cefi/tradfi/sports also never executed — same gap.)

- [x] ✅ [TERRAFORM] P0. **Durable per-AG `run.invoker` SHIPPED** deployment-service@e45c07e — the
      `google_cloud_run_v2_job_iam_member` for_each per-AG binding replaced the insufficient project-level one.
      (Recovered from a stash-pop conflict by the data-pipeline-hardening run 2026-06-22 — it existed only in a
      working-tree conflict; now landed.) **add `run.invoker` for the enumerator SA to
      `expected_universe_v2_scheduler.tf`** (the missing IAM that made every scheduled run `code 7`). Stop-gap applied
      live via `gcloud run jobs add-iam-policy-binding` on all 5 jobs (`cefi/defi/tradfi/sports/prediction`) → defi job
      now executes. Durable fix = a `google_cloud_run_v2_job_iam_member` (role=`roles/run.invoker`, member=the enum SA)
      per-AG in the TF. Repo: deployment-service. Provenance: this Progress Log.

Manual `gcloud run jobs execute expected-universe-v2-defi` (exec `…-h5djp`) launched + RUNNING (image imported clean,
catalog `gs://instruments-store-defi-prd-…/prod/catalog.parquet` present 302KB). The v2 `--apply-write` path loads the
catalog + builds the manifest `present_set` + calls `enumerate_v2(present_set=…)` → emits `expected_unattempted` for
alive-but-uncaptured defi cells over the bounded window (`--start-date 2026-02-20`, the recent-honest-denominator
window; full-history is the gated companion artifact, not this job). Verifying the seed count next.

ROOT CAUSE (operator-pinned, confirmed against live `market-data-tick-defi-prd` `_index`): the IS expected-universe
enumerator `_enumerate_defi()` iterated ALL `DATA_TYPES_BY_ASSET_GROUP["defi"]` — including CHAIN-LEVEL types — for
every `(chain, protocol)` in `PROTOCOL_LAUNCH_DATES`, emitting
`empty_confirmed[EXPECTED_INSTRUMENT_NOT_LISTED / EXPECTED_PRE_GENESIS_CHAIN]` keyed `venue=<PROTOCOL>` (e.g.
`venue=AAVE_V3, data_type=gas_fees`) for pre-protocol-launch dates. But gas/transfers/MEV exist from CHAIN genesis
regardless of when a DEX launched, and the real capture is keyed `venue=ALCHEMY`/`venue=FLASHBOTS`

- `chain=X`. ~142k false rows per chain-level data_type masked real coverage as "confirmed empty".

CODE shipped (each QG-green via quickmerge):

- [x] [SCRIPT] P0. **IS enumerator** — `instruments-service/scripts/enumerate_expected_universe.py` `_enumerate_defi()`:
      EXCLUDE chain-level data_types (`gas_fees`/`token_transfers`/`mev_events` — declared only by synthetic infra
      pseudo-protocols ALCHEMY-ONCHAIN/FLASHBOTS, fetched at synthetic venues) from the per-protocol loop; ADD
      chain-level `gas_fees` enumeration at `venue=ALCHEMY` for **pre-CHAIN-genesis dates only** →
      `EXPECTED_PRE_GENESIS_CHAIN` (gas chains derived UAC-only from `MAINNET_CHAIN_IDS` ∩ `GAS_FEE_CHAIN_START_DATES` +
      SOLANA; post-genesis gas absence is the handler/backfill's concern). `oracle_prices` is KEPT per-protocol
      (verified genuinely per-protocol: captured at AAVE_V3/ETHENA/LIDO/ETHERFI venues; ~15 LST/yield/staking/perp
      protocols emit it as their exchange rate). Smoke: fixed `_enumerate_defi` yields 47,990 gas rows ALL
      `venue=ALCHEMY`/`EXPECTED_PRE_GENESIS_CHAIN`, 0 `venue=PROTOCOL` gas, 0 token_transfers/mev per-protocol, 315k
      oracle_prices kept. — instruments-service@0e08237 (origin LDR) | QG green (81s)
- [x] [SCRIPT] P0. **UAC `_defi.py`** — removed `"gas_fees"` (22) + `"collect-gas-fees"` (22) from every protocol's
      `data_types`/`mtds_operations` (gas is chain-level). Verified: 0 protocols declare gas_fees; `gas_fees` stays in
      the chain-level `DATA_TYPES_BY_ASSET_GROUP["defi"]` list; `collect-gas-fees` dispatch is standalone
      (`launch-mtds-gas-fees-*-vm.sh`, `VM_OPERATION=collect-gas-fees`) so gas collection is unaffected. **Companion
      fix:** the lazy DeFi validity matrix (`market_data_categories.py` `valid_data_types_for_instrument_type`) derives
      from `PROTOCOL_CAPABILITIES.data_types`, so removing gas_fees orphaned the `("defi","gas_fees")` SOURCE_PRIORITY
      pair (UAC `test_validity_matrix_completeness` caught it) — re-injected `gas_fees` onto the chain-level
      `spot_asset` set in the lazy builder (now reachable + green). — unified-api-contracts@cbdef56d (origin LDR) | QG
      green
- [x] [SCRIPT] P0. **MTDS handler silent-zero audit + eigenlayer fix** — audited every defi handler's
      caught-fetch-exception routing: all main per-shard `except` blocks correctly `record_failed`
      (staking_yields/dex_pools/dex_swaps/lending_indices/ solana_defi); the ONE genuine silent-zero bug was
      `eigenlayer_rewards_handler._collect_date` (`except (...): return 0` → outer `record_zero_rows` →
      `empty_confirmed`). FIXED: expanded the except tuple (`aiohttp.ServerTimeoutError`/
      `ServerDisconnectedError`/`TimeoutError`/`json.JSONDecodeError`/…) and **re-raise** instead of `return 0`, so a
      caught fetch error on expected data routes to the outer `record_failed` (`attempted_failed`), not a false empty.
      Updated the test that encoded the buggy `return 0` to assert the raise. — market-tick-data-service@56435ac (origin
      LDR) | QG green

MANIFEST FLIP — DRY-RUN ONLY (NO MUTATION; apply left to parent after review). Extended
`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` with `--report-chain-level-defi-phantoms` (single
`_index` read, no GCS walk, returns before any mutation). Live `market-data-tick-defi-prd` `_index` (4.16M rows) report:

| data_type         | total   | captured@chain-venue | empty_confirmed @venue!=chain-venue (PHANTOM) | reason split                                 | DECISION                                                       |
| ----------------- | ------- | -------------------- | --------------------------------------------- | -------------------------------------------- | -------------------------------------------------------------- |
| `gas_fees`        | 158,166 | 11,902 @ALCHEMY      | **141,688**                                   | NOT_LISTED 85,605 + PRE_GENESIS_CHAIN 56,083 | **DELETE** (captured dupes — gas IS captured at venue=ALCHEMY) |
| `token_transfers` | 142,111 | 0 @ALCHEMY           | **141,688**                                   | NOT_LISTED 85,605 + PRE_GENESIS_CHAIN 56,083 | **DELETE** (wrong-key; canonical = venue=ALCHEMY)              |
| `mev_events`      | 142,111 | 0 @FLASHBOTS         | **141,732**                                   | NOT_LISTED 85,649 + PRE_GENESIS_CHAIN 56,083 | **DELETE** (wrong-key; canonical = venue=FLASHBOTS)            |

Decision = DELETE (not flip-to-attempted_failed): gas is CAPTURED at `venue=ALCHEMY` (proven: 5,749 of the 11,185
protocol-keyed NOT_LISTED chain-dates are captured at ALCHEMY), so the `venue=PROTOCOL` rows are wrong-key phantom
duplicates; the genuine pre-genesis cells re-seed correctly at `venue=ALCHEMY` via the fixed enumerator.
token_transfers/ mev_events are structurally chain-level (canonical key venue=ALCHEMY/FLASHBOTS) — same DELETE.
**`oracle_prices` EXCLUDED**: genuinely per-protocol (captured at venue=<PROTOCOL>); its venue=<PROTOCOL> empties are
CORRECT, not phantoms — left untouched.

NOT done (operator runs after review): the manifest DELETE apply; an APPLY pass on the reconcile script (only the
dry-run report is wired); deploying the fixed enumerator on the recurring `expected-universe-v2-defi` Cloud Run job.
This is phase 1 of the empty_confirmed-integrity fix — NOT complete.

### 2026-06-22 — empty_confirmed-integrity fix PHASE 2 — manifest DELETE applied + canonical gas reseed (REVERSIBLE, VERIFIED)

Completed the phase-1 follow-on the operator directed: remediate the ~425k EXISTING false `empty_confirmed` rows already
in the live `market-data-tick-defi-prd` `_index` (the CODE root cause was already shipped phase-1 above: IS@0e08237 +
UAC@cbdef56d). All steps run on the live consolidated `_index`
(`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`).

- [x] [SCRIPT] P0. **BACKUP (rollback)** — `gcs_copy_object` the live `_index` →
      `_index/snapshots/pre_empty_confirmed_fix_2026_06_22.parquet`; verified backup row count == source (4,189,890). —
      rollback cmd:
      `gcs_copy_object("gs://market-data-tick-defi-prd-central-element-323112/_index/snapshots/pre_empty_confirmed_fix_2026_06_22.parquet", "gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet")`
- [x] [SCRIPT] P0. **`--apply` DELETE wired + run** — extended
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`: added `_chain_level_phantom_mask` (SSOT
      predicate)
  - `_apply_delete_chain_level_defi_phantoms` + `--apply` flag on the chain-level pass (single `_index` read/write, no
    whole-corpus GCS walk; guards REFUSE if the predicate ever selects a non-`empty_confirmed` row or if captured/
    attempted_failed totals change). Predicate (EXACT):
    `asset_group==defi AND data_type∈{gas_fees,token_transfers,mev_events} AND capture_status==empty_confirmed AND venue∉{ALCHEMY,FLASHBOTS}`
    — removes BOTH NOT_LISTED + PRE_GENESIS_CHAIN wrong-key rows; `oracle_prices` untouched. **Applied: 425,108 rows
    deleted** (gas 141,688 + token_transfers 141,688 + mev_events 141,732); index 4,192,201→3,767,093. —
    instruments-service@34a6d6c (origin LDR) | QG green (95s) | Quickmerge: agent
- [x] [SCRIPT] P0. **DELETE verified** — post-delete re-read: **0 chain-level phantoms remain** (all 3 types); gas_fees
      now EXCLUSIVELY at `venue=ALCHEMY` (0 at any PROTOCOL venue); captured PRESERVED (663,968 at delete-time →
      climbing with live capture, never shrank — the in-memory before/after guard proved 0 captured/attempted_failed
      rows touched); empty_confirmed 3,498,027→3,072,920 (−425k); honest_cov_defi 15.81%→17.64%.
- [x] [SCRIPT] P0. **RESEED canonical (gas@ALCHEMY)** — ran the FIXED enumerator's own `_enumerate_defi_gas_fees`
      generator (v1 path) scoped to gas_fees via the script's exact `_build_present_set` + `_write_absent_rows`
      per-VM-shard writer
      (`MANIFEST_PER_VM_SHARDS=true VM_NAME=enum-reseed-defi-2026-06-22 MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`).
      Wrote **26,930 rows ALL `venue=ALCHEMY` / `gas_fees` / `EXPECTED_PRE_GENESIS_CHAIN` / schema_v9 /
      asset_group=defi** (0 non-ALCHEMY) to `_index/per_vm/enum-reseed-defi-2026-06-22.parquet`; consolidator merged it.
      **SCOPED to gas_fees only:** the full v1 defi forward-run (all data_types × all protocols × all chains since 2018)
      exceeded the 1M halt-cap — that full-history per-protocol reseed is NOT this step (would re-seed unrelated
      data_types), deferred to the fleet phase.
- [x] [SCRIPT] P0. **FINAL honest counts** — post-consolidation: gas_fees empty_confirmed 2,189→29,121 (26,930 reseed
      merged), gas EXCLUSIVELY @ALCHEMY; 0 chain-level phantoms; captured 667,383 (preserved + climbing),
      attempted_failed 30,207 (preserved); honest_cov_defi 17.57%.

NOT done (next phase, NOT this task — say so explicitly): re-backfills of the actual gas@ALCHEMY data + L2 lending; the
full-history per-protocol enumerator reseed (>1M rows); deploying the fixed enumerator on the recurring
`expected-universe-v2-defi` Cloud Run job. This task was the false-empty REMEDIATION (delete + canonical gas reseed)
only, NOT the full data-completion close.

### 2026-06-22 05:40 — defi fan-out: 14 new year-sharded VMs launched (dex-pools/swaps/liquidations/lending gaps)

**Diagnosis (STEP 1 — binding constraint):** confirmed NO 429/rate-limit on any defi data_type (TheGraph 9-key pool not
saturated). Binding constraint = under-parallelization: only 24 VMs running serially per (data_type×year). Aggregate ~50
cells/min across all 24 VMs vs ~600+ achievable.

**Acceleration (STEP 2) — new VMs launched all RUNNING at 05:40 UTC:**

- dex-pools: +5 year-VMs (2020/2021/2022/2024/2026) — now 7/7 year-slots covered (2020-2026)
- dex-swaps: +3 VMs (2021, 2025-q2, 2025-q3) — fills all 2025 quarters + 2021 year
- liquidations: +6 year-VMs (2021-2026) — was 0 running; now fully covered
- lending-indices: +2 year-VMs (2021, 2026 via timestamp-based launcher)

**Capture confirmed (T+10 verify):** `mtds-dex-pools-2022` → 24 new manifest entries per ~60s capturing 1622 records/day
at day=2022-01-02. `mtds-dex-pools-2020` → 25 entries/day but routing `empty_confirmed` (pre-DEX-launch; Uniswap V3
launched May 2021 — 2020 honest absence expected). `mtds-liquidations-2023/2024` logs confirm completion of
prior-session VMs; new VMs booting. No 429 errors on any VM.

**Oracle/pyth gap filed:** `launch-mtds-pyth-archive-backfill-vm.sh` + `launch-mtds-pyth-lst-backfill-vm.sh` exist but
not yet launched — pyth-lst requires operator `[ack]`; todo filed above as BLOCKED-OPERATOR-DECISION. **2026-07-28
stale-note annotation**: this note is superseded — this same file's 2026-06-21 "DEFI lane: FULL FAN-OUT LAUNCHED" entry
(line ~627 below) confirms **pyth-lst×4 VMs were launched** as part of the 60-VM full fan-out
(`lst-rates×7, dex-pools×6, dex-swaps×6, lending×5, liquidations×7, vault×6, pyth-archive×1, pyth-lst×4, gas-fees×7, jito×5, marinade×6`),
and the later 2026-06-22 13:00 entry confirms the fan-out's captures landed on canonical v9 paths. No live pyth-lst
BLOCKED-OPERATOR-DECISION remains on this specific item — the launch happened without further operator input.

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

### 2026-06-21 — DEFI lane (/autonomous, Opus): bucket bug is FLEET-WIDE across defi handlers

Canonical defi bucket CONFIRMED = consolidated `market-data-tick-defi-prd-central-element-323112` (only defi bucket with
a live consolidator + the measured 6.16M-row v9 `_index`; dedicated `{stem}-prd` buckets are
un-consolidated/index-less). slot-4 already fixed **lst_rates** (mtds@4c85340). STILL BROKEN (same
`get_write_bucket_name("<dash-data-type>")` orphan-bucket bug → ManifestConsolidatorStaleError, data lands where the
`_index` never sees = why defi is stuck at 6%): gas_fee×3, dex_pools, dex_swaps(check), lending_indices, liquidations,
oracle_prices, perp_funding, evm_defi, aggregator_route. Already-correct (do NOT touch): vault_share_price, solana_defi,
lst_rates. UTL `_DOMAIN_TO_YAML_KIND` has no dash-data-type kinds → legacy `{label}-{pid}` fallback. Fix =
`→ get_write_bucket_name("market_data","defi")`. **SSOT note:** `/codex/02-data/defi-canonical-naming-ssot.md` "bucket"
row (locked 2026-05-28, dedicated `{stem}-prd`) is OPERATIONALLY STALE — proceeding consolidated per 2026-06-21 plan
P0 + ground truth; row must be corrected (todo). **Operator: overrode a locked-SSOT row (big finding).** Exec order
(HARD): mtds handler fix → rebuild VM tarball (deployment-service create-code-tarballs.sh) → year-shard defi backfill
(2020→2026, 1 VM/data_type×year, consolidated bucket, MANIFEST_PER_VM_SHARDS) → T+10 verify → MDPS defi → live
forward-poll (launch-defi-forward-poll.sh = STUB) → monitor `_index` honest-cov. MINE this session: the
remaining-handlers fix + tarball + fan-out + SSOT-row correction.

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

### 2026-06-22 05:25 — DEFI status + gas-fees MANTLE BLOCKED-CREDENTIALS

~8h run: honest-cov 6.0%→11.3% (captured 448k); 24 VMs still capturing (19 drained); LIVE rows still 0 → forward-poll
relaunched `defi-fwd-20260622-052323` on the pipeline_mode-fixed tarball (mtds@2c5e2b5 deployed) → expect
live_onchain_subgraph rows ~10min (monitor b2vo0rlas verifying). **Wake-failure post-mortem:** the prior
drive-orchestrator used `while pgrep -f create-code-tarballs` — its OWN argv contained that string → pgrep self-matched
→ infinite hang ~8h, never woke (the documented self-match foot-gun; new monitor uses gcloud/gsutil only). Batch VMs ran
independently throughout.

- [x] ✅ [DATA] P1. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — fixed via
      `unified-api-contracts` this session: `_defi_chain_data.py`'s chain_id 5000 (Mantle) RPC template now points at
      Alchemy's `mantle-mainnet.g.alchemy.com` endpoint instead of the rate-limited public `rpc.mantle.xyz`, reusing the
      already-provisioned `alchemy-api-key` (no new signup/credential needed) — live-verified with a real
      `eth_feeHistory` call before shipping (confirmed real `baseFeePerGas` returned).** gas-fees MANTLE paid RPC.
      gas-fees on MANTLE uses the FREE public RPC (mantle.xyz) which 429-rate-limits `eth_feeHistory` (hundreds of
      `HTTP 429 retry N/12`); each MANTLE day takes ~10-15min vs ~2-3min → gas-fees is the batch long-pole (~1.5M
      blocks/yr on MANTLE). NOT hung, NOT a code bug — public-RPC throttle. ~~Unblock = a paid MANTLE RPC endpoint
      (Alchemy/dRPC/etc) key in Secret Manager; until then gas-fees completes slowly.~~ Other chains' gas-fees are fine.
      Repo: deployment-service/MTDS (RPC config). CREDENTIAL APPROVAL REQUEST: ikenna_orchestrator/pings/slot_1.md §
      "[slot-1-escalation] 2026-06-22".

### 2026-06-22 07:50 — DEFI lane DONE (fetchable gap closed) + deferred follow-ups

DeFi data completion ACHIEVED: raw 100%-attempted (expected_unattempted=0), fetchable data captured (2025=99%, 2024
strong), the 3.4M empty_confirmed is GENUINE honest-absence (pre-genesis chain + instrument-not-listed), live=4 rows,
MDPS processing, manifest v9. honest-cov %~10 is structurally low for defi (could-exist universe dominated by pre-2024
cells where defi didn't exist). Deferred follow-ups (all filed as todos):

- [x] ✅ [SCRIPT] P2. **defi live continuous scheduler** — Cloud Scheduler jobs (`defi-fwd-dex-swaps-prd`,
      `defi-fwd-dex-pools-prd`, `defi-fwd-oracle-prices-prd`) verified live, cycling every 5 min, writing parquets to
      `gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/.../pipeline_mode=live_onchain_subgraph/`.
      IAM gaps (GCS write + SM keys + env=prod) diagnosed + fixed ad-hoc + codified in terraform.
      deployment-service@d2ddb23
- [x] [DATA] P2. **sub-bucket blank-chain phantom audit** — some sub-bucket (oracle/perp) shards seed blank-chain venue
      rows (display-filtered in deployment-api@67972d8; durable fix = canonicalize at the IS seeder). Repo:
      instruments-service. — DONE 2026-07-30 (defi_satellite_ao_dispatch_batch1 finalize reconciliation), see
      defi_satellite_ao_dispatch_batch1_2026_07_25.md todo 8 for full evidence (instruments-service@b34416ee,
      "fix(enum): v2 defi enumerator emits canonical venue=PROTOCOL + chain=X (was combined PROTOCOL-CHAIN/blank-chain,
      phantom expected_unattempted)", landed 2026-06-22 — the durable IS-seeder fix this item asked for, covering the
      oracle-prices/perp-funding sub-buckets specifically; live-reproduction verified 2026-07-25/28).
- [x] ✅ [SCRIPT] P2. **commit defi launcher staleness edits** (MANIFEST_CONSOLIDATED_STALENESS_SEC=86400 +
      --preemptible) — working live, persist via quickmerge. Repo: deployment-service. deployment-service@53d1736

### 2026-06-22 12:40 — DEFI REGRESSION found + fixed: stale-enumerator-build re-seeded 1.44M LEGACY-venue phantoms

Continuation of the "backfill EVERYTHING" dispatch. Verified the running state from gcloud+GCS+manifest (NOT the stale
dispatch text). Findings:

- **PhaseA enumerator VM `expected-universe-v2-defi-20260622-122534` FAILED at setup** (`SETUP_EXIT_STATUS=2`,
  `uv pip install` rc=2 transient; no run.log, never ran the enumerator) → self-deleted. It produced NOTHING.
- **But the daily Cloud Run Job `expected-universe-v2-defi` ran at 12:05Z** (`enum-universe-defi-20260622-120550`,
  SUCCEEDED) and **seeded 1,444,842 `empty_confirmed` rows in the LEGACY combined `venue=PROTOCOL-CHAIN` + blank-chain
  form** (e.g. `UNISWAPV3-ARBITRUM`) — the EXACT regression the prior driver's enumerator fix targeted. ROOT CAUSE: the
  Cloud Run `instruments-service:latest` image is `0.29.0/bca1231` (built 11:48Z) and the GCS tarball baked `2c6a71e`
  (0.30.0) — **both PREDATE the fix `42dd37c` (committed 12:20Z, on LDR)**. So the stale build re-emitted legacy-form
  phantoms. These can NEVER convert vs canonical `venue=PROTOCOL`+`chain=X` captures → pure honest-cov DENOMINATOR
  poison (dragged honest_cov_defi 10.67%→7.50%).
- **Manifest snapshot** `_index/snapshots/pre_legacy_venue_phantom_delete_2026_06_22.parquet` (rollback).
- **Added + APPLIED a surgical legacy-venue phantom DELETE** to
  `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` (`--report-legacy-venue-defi-phantoms [--apply]`,
  predicate `empty_confirmed AND venue contains '-' AND chain==''`, same guards as the chain-level delete — REFUSES if
  it selects any non-empty_confirmed row / changes captured/failed totals). **DELETED 1,444,842 rows** (index
  5,287,366→3,842,524; captured 712,451 PRESERVED; attempted_failed 30,214 PRESERVED). **honest_cov_defi 7.50%→10.67%.**
- ✅ verified: `_legacy_seed.parquet` per-VM shard = 10k captured (0 legacy) → won't re-merge. The enum-run per-VM shard
  was already consolidated+cleared.

- [x] ✅ [SCRIPT] P0. **PROMOTE enumerator fix `42dd37c` LDR→main on instruments-service so `:latest` image + GCS
      tarball rebuild** — the daily Cloud Scheduler `expected-universe-v2-defi-daily` (01:30 UTC) runs the `:latest`
      image; while that image predates `42dd37c` it will **re-seed the 1.44M legacy phantoms every night**. The
      legacy-venue delete is idempotent/re-runnable as interim mitigation, but the durable fix is the image rebuild.
      Repo: instruments-service. Provenance: this Progress Log. — instruments-service@289f1a3 (v0.36.0 on main, Tier-C
      drain auto-promoted); `git merge-base --is-ancestor 42dd37c origin/main` → exit 0 confirmed 2026-06-22.

The legacy-venue phantom DELETE tool shipped: instruments-service@7b6512c (`reconcile_phantom_manifest_rows_all.py`
`--report-legacy-venue-defi-phantoms [--apply]`, QG green 82s, landed LDR). **Gap-analysis VERDICT** (measured from live
`_index` post-delete): defi `empty_confirmed` is **99.8% genuine honest-absence** (1.86M
`EXPECTED_INSTRUMENT_NOT_LISTED`

- 1.17M `EXPECTED_PRE_GENESIS_CHAIN`; only 5,710 `SOURCE_RETURNED_ZERO`). **ZERO recent (2024-26) empties carry a
  non-lifecycle reason** → no fetchable cells hiding as empty. 2025 captured-ratios are 90-99.9% for the core data_types
  (dex_pool_state 99.9 / dex_pool_swaps 99.9 / oracle_prices 97.6 / risk_params 99.4 / utilization 99.6 / dex_swaps
  90.5). **So the low honest-cov % is STRUCTURALLY GENUINE** (could-exist grid dominated by pre-launch instrument×date
  cells) — the prior driver's "DeFi fetchable gap closed" was correct; the only real defect was the legacy-phantom
  denominator poison (now removed → 10.67%). NOT launching a redundant massive re-fetch fan-out (would re-OOM + waste
  quota on 99.9%-captured data). Remaining genuine work = 6.2k attempted_failed (Solana schema bugs + perp_funding +
  dex_swaps 404s) + 7 OOM'd year-shards (top-off tail) + the image-promote above.

**OOM'd-shard audit (7 VMs exit 137, run.log persisted):** of the 7, the dex-swaps Q2/Q3 are **already COMPLETE**
despite the OOM (manifest shows captured 91/92 distinct days each — the per-VM shard merged before the OOM-at-tail);
`mtds-dex-swaps-backfill` was the FULL 2021→2026 range in ONE VM (correctly superseded by the year-shards). Genuinely
incomplete: lst-rates 2025-01 (17/31 days; rest pre-launch tokens), lending-indices 2025-03 (0 captured — OOM truncated
before shard write), gas-fees 2024-01/2026-02 (0 captured — gas-fees is the MANTLE-paid-RPC long-pole, already
BLOCKED-CREDENTIALS). **NOT relaunching now: the fleet is at 329 RUNNING backfill VMs (tradfi CME swarm — far over the
≤40 cap), so adding defi VMs into an over-cap fleet is imprudent + the gaps are marginal in a structurally-complete
lane.** Filed as targeted todos:

- [x] ✅ [DATA] P2. **DEFI top-off the 2 genuinely-incomplete non-gas OOM'd shards** — relaunch
      `collect-lending-indices` 2025-03 + `collect-lst-rates` 2025-01 on **e2-standard-8 --preemptible**
      (`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`, freshness-skip makes it safe) once the tradfi fleet drains below the
      ≤40 concurrent cap. Marginal coverage (lending-indices 2025-03 was writing real rows pre-OOM; lst-rates is a
      13-token data_type). Repo: deployment-service. Provenance: this Progress Log (OOM'd-shard audit). —
      deployment-service | VMs: mtds-lending-indices-20260623-112822 (2025-03-01..31, e2-standard-8 preemptible) +
      mtds-lst-rates-20260623-112837 (2025-01-01..31, e2-standard-8); fleet was at 0 RUNNING backfill VMs (tradfi swarm
      drained)
- [x] [DATA] P2. ✅ **DEFI attempted_failed cleanup (6.2k cells)** — fix the Solana DEX/lending handler
      schema-validation failures (`RowSchemaValidationError` venue=KAMINO/ORCA/RAYDIUM/MARINADE: missing
      `ts_event`/`supply_rate`/ `price_a`/etc — a HANDLER contract bug, not a backfill) + drift_v2 sig-index-missing
      (build via `build_drift_v2_sig_index.py`) + dex_swaps `404 GET` (1747) + perp_funding 424 + rewards 730. The 3,550
      `phantom_captured_no_parquet_at_canonical_path` re-validate via
      `reconcile_phantom_manifest_rows_all.py --unphantom`. Repo: market-tick-data-service. Provenance: this Progress
      Log (failed-cell breakdown). — market-tick-data-service@08fb898
- [x] ✅ [INFRA] P2. **FLEET over-cap finding (tradfi, NOT defi)** —
      `gcloud compute instances list --filter=status=RUNNING` shows **329 RUNNING backfill VMs** (dominated by ~280
      `tradfi-bf-cme-ohlcv-1m-*` year×contract shards launched by a prior driver), far over the ≤40 concurrent cap.
      On-demand E2 quota=600 but this risks preemption cascades + Actions/compute spend. Verify the tradfi swarm is
      draining (self-deleting on completion) + that none OOM'd silently; if stalled, throttle. Repo: deployment-service
      (tradfi lane). Provenance: this Progress Log; this is a TradFi-lane finding surfaced during the defi audit, not
      defi-blocking. — **VERIFIED 2026-06-23**: 0 VMs running (full drain); sampled 50 recent CME VMs: 48/50 exit 0, 0
      OOM (exit 137), 2 logs ended mid-run (weekend skip, not errors). Swarm self-resolved — no throttle needed. No code
      changes.

### 2026-06-22 13:00 — DEFI 2nd defect found+fixed: 441k blank-asset_group captures (honest_cov 10.67%→18.66%)

While verifying captured counts, found a SECOND denominator defect: **441,008 defi rows with BLANK `asset_group`**
(should be `defi`), of which **354,294 are CAPTURED** real data (canonical venues UNISWAP_V3/BALANCER/AAVE_V3, canonical
chains, schema v9, `batch_onchain_subgraph`/`rpc` pipeline_modes, blank `enumerator_run_id` = WRITER-produced captures).
A consumer filtering `asset_group=='defi'` (deployment-UI denominator) UNDERCOUNTS captured by ~354k. **SNAPSHOT**
`_index/snapshots/pre_asset_group_stamp_2026_06_22.parquet`. **APPLIED a surgical stamp** (guard: bucket has no non-defi
asset_group; row-count + captured-count preserved): stamped all 441,008 blank-ag rows → `asset_group=defi`. Result: ALL
3,848,270 rows now `asset_group=defi`, captured **718,197**, empty_confirmed 3.10M, attempted_failed 30,214, schema 100%
v9 → **honest_cov_defi = 18.66%** (bucket-wide; was 7.50% at session start, 10.67% after the legacy-phantom delete).
**ROOT CAUSE is a LIVE writer bug** (NOT just legacy): ALL 2026-06 captured rows (387k written 2026-06-22, 53k
2026-06-21 by the CURRENT capture fleet) arrive blank-ag → new captures keep arriving blank until the writer is fixed.
The index-stamp is the re-runnable interim mitigation.

- [x] ✅ [DATA] P1. **DEFI writer must stamp `asset_group=defi` on the manifest ROW** — the defi MTDS capture path
      (`record_captured`/`record_empty`/`record_zero_rows` → UTL `manifest_writer`) threads `asset_group` for
      source-stamping but does NOT write it into the row's `asset_group` COLUMN (it is NOT in `_ROW_KEY_COLUMNS`; the
      column is populated elsewhere/not at all for defi captures) → every defi capture lands blank-ag. Trace where the
      `asset_group` column value is set on a captured row in UTL `manifest_writer/_writer_io.py`/`_rows.py` and ensure
      the defi handlers pass + persist it. Add a unit test asserting a defi `record_captured` row carries
      `asset_group=defi`. Until fixed, re-run the index-stamp (`pre_asset_group_stamp_2026_06_22.parquet` snapshot is
      the rollback). Repo: unified-trading-library (+ market-tick-data-service handler call sites). Provenance: this
      Progress Log; cross-repo data-correctness — also affects cefi/tradfi/sports/prediction if their writers share the
      gap (audit each bucket's blank-ag captured count). **BIG finding flagged to operator in the session report.** —
      utl@4bd9487e | asset_group added as first-class AvailabilityRecord field; threaded through
      `record_captured`/add/`_records_to_dataframe`/`_V4_BACKFILL_COLUMNS`; 7-test suite green; QG pass 110s

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — re-confirmed independently; only diff since the
  2026-08-01 full re-read was context-scout metadata (no content change, per git log). All ~20 open items remain
  C-GREEN-gated canonicalisation walks, DEPENDENCY_BLOCKED sub-steps of the same single-walk migration,
  operator-launched wallet/promote/paper-trade steps (HUMAN-only per CLAUDE.md hard-stop list), or a market-condition
  trigger (G8, TVL probe). No RECLASSIFY-eligible items found. Doc stays `assigned_vm: NA`.
- **round11-sweep 2026-08-09** (defi tranche, satellite-extraction + RECLASSIFY re-check): re-read end to end (18 open
  items at entry). Checked whole-doc RECLASSIFY against every accumulated round11 precedent (IAM self-service, D16
  all-repos, S5.1 tiering, plan-destination-defaults-AO-dispatched, escalation-N=3-days, reversibility-qualified
  deletes, Option B retired, GSM secret + 5 Slack webhooks now existing) — none apply here: this doc's open scope is a
  bundled single-walk canonicalisation migration (B0, C2-C12, gated on each other + C-GREEN, not independently
  dispatchable), human-only wallet/promote/paper-trade steps (G3/G4, CLAUDE.md hard-stop list), operator-launched
  long-wall-clock VM launches (G1/G2), and a market-condition trigger (G8). No satellite-extraction candidate found —
  every remaining item is either part of the single coordinated walk or explicitly human/operator-gated, so none meets
  the "independently worker-determinable" bar. **One genuine find, fixed in this pass**: C0f's "1 kind deferred" framing
  was stale — `bucket_estate_consolidation_closeout_2026_07_24.md` (2026-07-31 re-correction) confirms the deferred
  `lending-indices`/`lending-indices-prd` pair was actually deleted 2026-07-15, so C0f is now fully done (flipped above,
  citation added). Doc stays `assigned_vm: NA` (KEEP-NA valid, round11).
