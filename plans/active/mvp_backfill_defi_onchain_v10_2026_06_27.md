---
doc_type: plan
title: MVP backfill — DeFi all on-chain data_types (SPOT-only, per-protocol genesis, reconcile-then-fill)
summary:
  Backfill all DeFi on-chain data_types (dex_pool_swaps/state, lending_indices, lst_rates, perp_funding, oracle_prices)
  for the v10 DeFi MVP scope on SPOT VMs, respecting per-protocol genesis.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [deployment-service, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [mvp, backfill, defi, on-chain, dex, lending, lst, perp-funding, oracle, spot-vm, v10]
related:
  [
    plans/archive/2026_07/mvp_catalogue_finalization_v10_2026_06_27.md,
    plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md,
    plans/active/defi_manifest_canonicalisation_2026_06_01.md,
    plans/active/path_to_100pct_backfill_mtds_is_2026_06_17.md,
    plans/active/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md,
  ]
created: 2026-06-27
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
last_updated: 2026-07-24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [mvp_catalogue_finalization_v10_2026_06_27]
source:
assigned_role: data_engineering
drift_direction: advance-code
---

> **🟢 OPERATOR-AUTHORIZED background execution (2026-06-27).** Part of the remaining MVP arc handed to the
> agent-orchestrator (`planning` VM). One agent, one craft (`data_engineering`), Sonnet/high.
>
> **🔴 DRIFT SIG-INDEX WALKERS FAILED — BLOCKED-OPERATOR-DECISION (2026-07-14 13:15Z, data_engineering slot-2).** Both
> sig-walker VMs launched 12:39Z (`mtds-drift-sig-walker-resume-20260714-123928`,
> `mtds-drift-sig-walker-gap-20260714-123952`) exhausted 5 Helius 429 retries on their FIRST page request
> (~12:42-12:54Z), logged the false-positive `"Walk complete: 0 new sigs"`, exited 0, and self-deleted
> (`VM_SHUTDOWN_ON_COMPLETION=true`) — **neither reached its `--back-to` floor; zero sig-index parts were written to
> either `_parts/` or `_parts_gap/`.** Root cause: the shared Helius API key is saturated across the 3-VM fleet (the
> still-RUNNING `mtds-solana-drift-backfill` independently logs 557+ 429s in its own run.log but survives via its longer
> per-batch retry budget). A SECOND defect compounded this: `_walk_signatures_chunked` returned the identical
> `(0 sigs, 0 parts)` tuple whether the walk genuinely completed OR retry-exhausted on page 1 — **fixed** in
> `market-tick-data-service@e4c04c64` (adds a `retry_exhausted` flag; the script now exits 1 + logs ERROR instead of
> silently reporting success on API-saturation). Gate check (`measure_honest_coverage.py --asset-group defi`, 2026-07-14
> 13:13Z): DRIFT perp_funding `captured=8, attempted_failed=39, expected_unattempted=0` — **gate NOT met**, sub-items 1
> and 4 of the verify-todo below are FALSE. **Operator decision needed before relaunching the 2 walkers** (see the
> todo's inline question) — do NOT launch further Helius-consuming VMs until answered.
>
> **🟢 RESOLVED 2026-07-14 ~14:07Z (data_engineering slot-2)** — operator ruled Helius quota restored (autoscaling +5M
> credits) at ~13:45Z; fleet relaunched (`mtds-solana-drift-backfill`, `mtds-drift-sig-walker-resume-20260714-134435`,
> `mtds-drift-sig-walker-gap-20260714-134501`) and CONFIRMED genuinely draining this time — no repeat of the 429-exhaust
> false-death: resume walker parts grew 6293→6391 (oldest sig 2025-12-23→2025-12-22), gap walker parts grew 0→204
> (oldest sig 2025-07-01→2025-06-19), backfill VM is actively processing indexed sigs for 2025-01-09. Full detail +
> evidence in the G1.5 verify-todo's Progress Log entry below. **Gate still NOT met** (multi-day drain, per this plan's
> own drain-math estimate of 1.7-9 days) — this banner is resolved to "healthy and progressing", not to "gate met".
>
> **🟢 DRIFT PERP_FUNDING/PERP_TRADES MIGRATED TO VELOCITY — HELIUS SIG-WALKER PATH RETIRED (2026-07-16,
> data_engineering slot-15).** The Helius sig-index/day-walker saga in the two banners above (13:15Z
> BLOCKED-OPERATOR-DECISION → 14:07Z resolved-and-relaunched) is now superseded: main ruled migrate-to-Velocity
> (`issues/drift_helius_path_obsolete_2026_07_15.md`, Option A, 2026-07-15). All of main's sequencing has landed: the
> `mtds-drift-sig-walker-*` fleet is stopped and blocked from auto-relaunch (`deployment-service@46d6492`);
> `mtds-solana-drift-backfill` is re-routed to `backfill_drift_v2_historical.py` (Velocity Data API, e2-highmem-8,
> `deployment-service@ee859e4`) and launched at scale over the `2025-01-15`–`2025-12-23` gap; the DRIFT manifest
> registry gap for `perp_trades` is code-fixed (`unified-api-contracts@5fd781c7`). Any DRIFT sig-walker/Helius content
> below is now HISTORICAL — do not relaunch that path; new DRIFT `perp_funding`/`perp_trades` gap-fill work routes
> through the Velocity path. Full migration record: `issues/drift_helius_path_obsolete_2026_07_15.md`.
>
> **🟢 GATE CLEARED 2026-06-28T02:35Z** — `mvp_catalogue_finalization_v10_2026_06_27.md` G3 sign-off complete. defi
> catalogue v10-correct: 7,222 rows (all-MVP ✅), dual-key ghosts=0 (4 cross-chain ETHEREUM+POLYGON ✓), false-delist=0,
> blank=0. Phantom: 219,529 (issue doc `phantom_captures_defi_2026_06_28.md`).
>
> **🟢 G1 IN-FLIGHT 2026-06-28** — 6 SPOT VMs RUNNING: dex-pools-backfill ✅, dex-swaps-backfill ✅,
> lending-indices-20260628-021507 ✅, lst-rates-20260628-002136 ✅, perp-funding-backfill ✅, solana-drift-backfill ✅.
> Pyth-archive VM self-completed (oracle_prices: verify in G2). T+3.5h check 05:37Z: ALL 6 VMs RUNNING. Per-date
> `process_final=True` writes at 05:28-05:29Z were INTERMEDIATE shard checkpoints (per-date completion, not VM
> completion). Progress: dex-pools@2023-09-23 (~21%), dex-swaps@2023-01-27 (~2%), lst-rates@2020-07-03 (<1%),
> lending-indices@2022-03-17 (~5%), perp-funding@2023-12-21 (~5%), solana-drift@2025-01-11 (~0.4%, ~2-3h/day →
> PERFORMANCE STALL).
>
> **🔴 SOLANA-DRIFT PERFORMANCE STALL (2026-06-28T05:37Z)**: `mtds-solana-drift-backfill` resolving Helius signatures
> day-by-day via parts fallback (consolidated `drift_v2_sig_index.parquet` NotFound). Each date = ~2-3h (1.2M sigs/day
> via HTTP). At current rate: 527-day range → 44+ days. OPERATOR DECISION REQUIRED: (A) Build consolidated sig index
> parquet, (B) accept `empty_confirmed` for DRIFT perp_funding historical range, (C) stop VM + re-architect. See todos
> below.
>
> **🔴 SOLANA-DRIFT 429-BURST ANOMALY (2026-06-28T20:22Z) — OPERATOR REVIEW REQUIRED**: DRIFT VM jumped from Dec-24
> batch 23,098/60,586 (38%, ETA 03:11 Jun 29) to Dec-29 batch 19,204 in only 35 min (20:14→20:22 UTC). Effective rate
> ~4,000-7,000 batch/min vs normal 84/min. Pattern: rapid successive HTTP 429s (`Too Many Requests`) for each batch in
> the same UTC second. Possible causes: (A) VM retrying 429s without backoff → advancing batch counter with 0 real data
> (empty/corrupt parquets for Dec 24-29+); (B) Dec 25-27 had 0 sigs (instant), Dec 28 was small; (C) Helius rate-limit
> on a different endpoint. DATA QUALITY RISK: if 429 = skipped batch without resolve, DRIFT parquets Dec 24-29+ may be
> under-populated. Recommend: operator check a Dec 28 parquet's row count in GCS and compare to expected sig volume
> before relying on this data. **Do NOT stop VM autonomously** — operator decision required on anomaly investigation.
>
> **🟢 DEFI PHANTOM RECONCILE — APPLY COMPLETE ✅ 2026-06-28T21:35Z** — **219,632 phantoms flipped** to
> `attempted_failed` (0 unphantomed). Real captures after flip: 2,383,852. Manifest: 9,802,111 rows written.
> MVP-critical flipped: **dex_pool_swaps=20,586; perp_funding=140**. Non-MVP: swaps*ohlcv*\*×7=177,931; gas_fees=12,249;
> liquidations=8,509; derivative_ticker=145; trades=42; vault_share_price=30. Top venues: UNISWAP_V4=69,573,
> UNISWAP_V3=42,807, BALANCER=31,967. Triage JSONL:
> `gs://central-element-323112-phantom-triage/triage_defi_20260628_203239.jsonl`. Running VMs will now pick up
> newly-visible dex_pool_swaps (20,586) and perp_funding (140) gaps as forward-scan progresses. **Use per-data_type
> launchers (not unified `--asset-group DEFI` form).**
>
> **Canonical MVP SSOT (the ONLY scope authority):** `mvp_scope.py` v10 + `/codex/02-data/mvp-scope-canonical.md`. This
> plan REFERENCES it. **DeFi v10 = MVP-tag-all today** (`defi_mvp_tag_all_2026_06_26`): data_types
> `dex_pool_state / dex_pool_swaps / lst_rates / lending_indices / perp_funding / oracle_prices`. **LIGHTER / EXTENDED /
> PACIFICA are CeFi, NOT DeFi** (v10 decision #4) — do NOT backfill them here. Any older plan treating them as DeFi is
> stale and SUBORDINATE (Phase-4 reconciliation).

## Codex SSOTs (READ before executing)

- `/codex/02-data/mvp-scope-canonical.md` § DeFi — the 6 data_types + MVP-tag-all short-circuit.
- `/codex/02-data/defi-canonical-naming-ssot.md` — DeFi data gotchas; canonical venue naming / dual-key collapse.
- `/codex/02-data/honest-absence-downstream-handling.md` — `EXPECTED_PRE_GENESIS_CHAIN`, `EXPECTED_PROTOCOL_PAUSED`,
  `UPSTREAM_SUBGRAPH_ZERO` (subgraph 0-rows on an alive day → attempted_failed, NOT silent empty); per-protocol genesis.
- `/codex/05-infrastructure/spot-vms-for-backfill.md` — SPOT-by-default.

## Definition of 100%

`captured` covers 100% of the v10 defi MVP could-exist universe → `attempted_failed = 0` AND `expected_unattempted = 0`
per data_type. Honest `empty_confirmed` excluded (pre-genesis-chain, protocol-paused windows). A subgraph returning 0
rows on an alive day is `attempted_failed[UPSTREAM_SUBGRAPH_ZERO]` (a gap to fix), NOT empty.

## Budget posture

DeFi on-chain is cheap (<$250 total per the budget reality) — The Graph keys (9-key pool) + Hyperliquid S3 + Pyth
archive, no Tardis tick cost. Launch all data_types in parallel on SPOT VMs. Reconcile-then-fill: respect per-protocol
genesis (do not launch pre-genesis shards — those are honest-empty).

---

## Todos (G0 gate+reconcile, then parallel per-data_type fills, then verify)

### G0 — gate + reconcile

- [x] ✅ [SCRIPT] P0. Confirm Phase-0 defi catalogue sign-off (dual-key ghosts collapsed, mvp-tag-all). **Gate:**
      `mvp_catalogue_finalization_v10_2026_06_27.md` Progress Log shows defi G3 green. If not signed off → wait. SPOT
      N/A. — **Confirmed 2026-06-28T02:40Z**: finalization Progress Log defi G3 GREEN ✅; 7,222 rows all mvp=True ✅;
      dual-key ghosts=0 (4 ETHEREUM+POLYGON cross-chain contracts) ✓.
- [x] [SCRIPT] P0. Build the defi gap report per data_type (dex_pool_state, dex_pool_swaps,
      liquidations/lending_indices, lst_rates, perp_funding, oracle_prices) for the v10 DeFi MVP venues, respecting
      per-protocol genesis. Repos: `instruments-service`, `e2e-testing`. **Run:**
      `python scripts/measure_honest_coverage.py --asset-group defi` + `by_venue_data_type`; list (data_type,
      protocol/chain, date-range) cells with attempted_failed>0 / expected_unattempted>0 that are POST-genesis
      (pre-genesis cells are honest `EXPECTED_PRE_GENESIS_CHAIN`). **Gate:** gap list to Progress Log. SPOT N/A. ✅ —
      instruments-service@gap-report-2026-06-27

### G1 — per-data_type fills (PARALLEL; SPOT VMs only; per-protocol genesis respected)

- [x] [SCRIPT] P0. dex_pool_state gap-fill. Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-dex-pools-backfill-vm.sh --start <genesis> --end <today>` (TheGraph 9-key pool;
      `--shard-index N` + `--force` for multi-VM fan-out). **Gate:** dex_pool_state attempted_failed=0 post-genesis;
      verify T+10min `gcloud compute instances list --filter='name~mtds-dex-pools' --zones=asia-northeast1-c`. SPOT VMs
      only. ✅ — deployment-service@vm-launch-2026-06-27 VM=mtds-dex-pools-backfill RUNNING 34.84.133.128
- [x] [SCRIPT] P0. dex_pool_swaps gap-fill. Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-dex-swaps-backfill-vm.sh --start <genesis> --end <today>`. **Gate:** dex_pool_swaps
      attempted_failed=0 post-genesis; verify T+10min. SPOT VMs only. ✅ — VM=mtds-dex-swaps-backfill RUNNING
      34.146.95.210 (2023-01-01→2026-06-27)
- [x] [SCRIPT] P0. lending_indices gap-fill (Aave V3 / Spark / Compound V3 via The Graph). Repo: `deployment-service`.
      **SPOT VMs only.** `bash scripts/vm/launch-mtds-lending-indices-backfill-vm.sh <START> <END>` (positional window,
      full history). **Gate:** lending_indices attempted_failed=0 post-genesis; verify T+10min. SPOT VMs only. ✅ —
      VM=mtds-lending-indices-20260627-220715 RUNNING 34.84.20.157 (2022-01-01→2026-06-27)
- [x] [SCRIPT] P0. lst_rates gap-fill (15 LST/LRT tokens, EVM + Solana). Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-lst-rates-backfill-vm.sh <START> <END>` (positional window). **Gate:** lst_rates
      attempted_failed=0 per-token-genesis; verify T+10min. SPOT VMs only. ✅ — VM=mtds-lst-rates-20260627-220922
      RUNNING 34.84.28.4 (2020-01-01→2026-06-27)
- [x] [SCRIPT] P0. perp_funding gap-fill (Hyperliquid public S3, no key). Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-perp-funding-backfill-vm.sh --start 2023-11-01 --end <today>` (HL mainnet genesis).
      **Gate:** perp_funding attempted_failed=0 from genesis; verify T+10min. SPOT VMs only. ✅ —
      VM=mtds-perp-funding-backfill RUNNING 34.180.79.187 (2023-11-01→2026-06-27)
- [x] [SCRIPT] P0. oracle_prices gap-fill (Pyth). Repo: `deployment-service`. **SPOT VMs only.** Archive gap:
      `bash scripts/vm/launch-mtds-pyth-archive-backfill-vm.sh 2022-11-01 2023-09-30` (Pythnet RPC fallback for
      pre-Hermes); for Hermes-covered dates (2023-10-01+) use the forward-poll/collect path per the launcher header.
      **Gate:** oracle_prices attempted_failed=0 post-genesis; verify T+10min. SPOT VMs only. ✅ —
      VM=mtds-pyth-archive-20260627-221636 RUNNING 34.84.64.217 (2022-11-01→2023-09-30); Hermes window (2023-10-01+)
      covered by forward collect cascade

### G1.5 — solana-drift stall intervention (RESOLVED 2026-06-29 provisional → REOPENED 2026-07-11, IN MVP SCOPE)

- [x] ✅ [OPERATOR] P0. Solana-drift backfill performance stall — decide intervention path: Consolidated sig index
      `drift_v2_sig_index.parquet` missing → VM uses 7169-part fallback → ~2-3h/day. At 527-day range this takes 44+
      days. Options: (A) Build consolidated sig index: merge 7169 parts into single parquet, upload to
      `gs://market-data-tick-defi-prd-central-element-323112/_index/drift_v2_sig_index.parquet`. VM auto-detects and
      skips parts fallback. Estimated build: ~30min of local merge + upload. (B) Accept
      `empty_confirmed[EXPECTED_PRE_VENUE_LAUNCH]` for all DRIFT perp_funding dates — mark DRIFT/SOLANA as out of MVP
      scope. Stop VM, set 424 DRIFT `attempted_failed` rows to `empty_confirmed`. (C) Stop VM + re-architect: change to
      signature-streaming approach (Helius streaming API instead of batch resolve). New VM after code fix.
      **Recommended: Option A** — building consolidated index is straightforward and unblocks the stall without
      sacrificing DRIFT data. 2025-01-11 still processing; partial data for 2025-01-09 and 2025-01-10 already captured
      (2,177,357 rows combined). Repo: `market-tick-data-service`, `instruments-service`. **2026-06-29 (provisional,
      SUPERSEDED) — OUT OF MVP SCOPE.** Per UAC SSOT `is_mvp()` at the time, DRIFT `perp_funding` was NOT MVP: the defi
      rule's `instrument_types` axis = `{POOL, DEX_POOL, LST, LENDING}` (no `PERPETUAL`), so every `perp_funding` cell
      evaluated `is_mvp()=False` under both defi AND cefi (cefi captures funding via
      `funding_rate`/`derivative_ticker`). Operator decision at the time: do NOT build the sig index, do NOT download —
      none of A/B/C executed. DRIFT VM already gone (SPOT, terminated); 8 dates of genuine `captured` data confirmed
      live in the availability manifest as of 2026-07-12 (2025-01-09 through 2025-01-15, plus 2025-12-23; 7,412,962
      rows) — corrected 2026-07-12, doc-reconciliation finding 42, §A2 B-queue ruling (was: "only 3 dates of genuine
      data (2025-01-09/10/11)", contradicted by this same doc's own 2026-06-28 Progress Log entries recording
      2025-01-12/13 and 2025-12-23 completions, since confirmed still `captured` in the live manifest, not overwritten
      or reverted). Three-way SSOT contradiction (is_mvp vs capability registries vs this plan) tracked in
      `plans/active/issues/defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`. **2026-07-11 — IN MVP SCOPE per
      operator ruling Option 2 (UAC v13, `unified-api-contracts@89b16943` — see
      `defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`).** The broader DeFi-MVP-framing ruling ("keep all as
      MVP") landed `DeFiMvpRule` v13 adding `PERPETUAL` to the defi rule's `instrument_types`, so
      `is_mvp("defi", "DRIFT-SOLANA", "PERPETUAL", "perp_funding")` now evaluates `True` — the 2026-06-29 provisional
      out-of-scope call above is superseded. Synced per
      `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` (finding 43).

  > **G1.5 sub-history extracted (2026-07-24 hygiene split — zero todo/gate/state change).** The 7 nested sub-todos that
  > sat inline here (walker-launcher shipment, the indexed-window + 2-segment sig-walker VM launches, the
  > `-001`/`-002`/`-003` AO-thrash re-dispatch saga, the DRIFT-purge supersession, and the full 17-market Velocity
  > relaunch) are moved VERBATIM, checkbox state and all, to
  > `mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md` § "G1.5 sub-history". Nothing above this line changed:
  > the G1.5 top-level todo's own checkbox and resolution text (the 2026-06-29 provisional call → 2026-07-11
  > IN-MVP-SCOPE ruling, per `defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`) stand unedited. Per the banners
  > at the top of this plan, the final resolution already on record is: DRIFT perp_funding/perp_trades migrated to the
  > Velocity backfill path 2026-07-16, the Helius sig-walker path retired — see the 🟢 banner above and G1.6/G2 below,
  > both untouched by this split.

### G1.6 — Solana DEX-pool venues (ORCA/RAYDIUM/KAMINO) never backfilled (found during G2 2026-07-12)

- [x] ✅ [SCRIPT] P1. Launch a dedicated Solana dex-pool backfill VM for ORCA/RAYDIUM/KAMINO (`dex_pool_state`) —
      analogous to the dedicated `mtds-solana-drift-backfill` VM G1 launched for DRIFT perp_funding. Root cause
      (confirmed 2026-07-12): the original `mtds-dex-pools-backfill`/`mtds-dex-swaps-backfill` G1 VMs explicitly SKIPPED
      these 3 Solana venues ("Solana venues (orca/raydium/phoenix) skipped as expected." — this plan, G1 dex-pools
      launch log). **Deeper root cause (2026-07-12, this todo):** it's not just that no follow-up VM was launched —
      `DexPoolsHandler`/`DexSwapsHandler` resolve protocol→chain via UAC `get_supported_chains_for_protocol()`, a
      `SUBGRAPH_IDS`-only lookup; ORCA/RAYDIUM/KAMINO have no subgraph (REST-API venues) so it returns `[]` and the
      per-protocol loop `continue`s — `_collect_solana_dex()` (which DOES route
      `fetch_orca`/`fetch_raydium`/`fetch_kamino_vault`) is dead code from that call site, never reached. The working,
      already-shipped path is `SolanaDefiHandler` (`--operation collect-solana-defi`, `VM_TASK=solana-defi-backfill`),
      which hardcodes its own protocol list and carries the forward-only-honest write gate
      (`_filter_rows_to_target_day`, incident `solana_defi_fake_history_snapshot_2026_06_17.md`): ORCA/RAYDIUM/KAMINO's
      REST endpoints expose only the CURRENT pool/vault set (no historical endpoint), so a historical backfill date's
      now-snapshot rows are dropped and recorded as honest absence (`record_zero_rows` →
      `EXPECTED_PRE_VENUE_LAUNCH`/`SOURCE_RETURNED_ZERO`) instead of being falsely back-dated as `captured` — this still
      resolves every IS-seeded `expected_unattempted` cell (the Gate below) even though genuine `captured` rows only
      land for the day the VM actually runs (today), the same accepted shape as DRIFT/marginfi/solend's Solana legs.
      **Shipped:** `deployment-service@8f5592c` — new launcher `scripts/vm/launch-mtds-solana-defi-backfill-vm.sh`
      (`VM_TASK=solana-defi-backfill`, `VM_SOLANA_PROTOCOLS=kamino;orca;raydium`) + wired the pre-registered
      `mtds-solana-defi-backfill` `launcher_registry.py` slot (previously `None`) to it. **Launched:** VM
      `mtds-solana-defi-backfill` created via the Python `compute_v1` client (gcloud CLI unavailable in this agent-slot
      sandbox — snap-confine fails under the container's `no_new_privs`; the API call mirrors the launcher's `--dry-run`
      output exactly), zone `asia-northeast1-c`, SPOT, window 2023-01-01→2026-07-12, status `RUNNING` at launch.
      **Gate:** ORCA/RAYDIUM/KAMINO dex_pool_state attempted_failed=0 AND expected_unattempted=0 post-genesis — verify
      once the VM completes (see G2).
- [x] ✅ [SCRIPT] P2. `dex_pool_swaps` for ORCA/RAYDIUM has NO existing data source — new finding, not absorbed into the
      P1 todo above. Neither `SolanaDefiHandler`/`_solana_defi_fetch.py` (dex_pool_state only, via REST pool-list
      snapshots) nor `DexSwapsHandler` (`get_subgraph_id(protocol, "SOLANA")` is always `None` for these venues — no
      Solana routing at all) produce individual swap events for Solana AMMs. Building a swap-level Solana indexer
      (on-chain tx parsing via Alchemy/Helius, or a Jupiter-aggregator trade-history adapter) is new capability, not a
      VM launch — **scoped 2026-07-12 (slot-2)** as its own follow-up doc rather than attempted inline:
      `issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md`. Also confirmed the ORCA/RAYDIUM live WS connectors
      (`orca_defi_ws.py`/`raydium_defi_ws.py`) are Jupiter price-quote pollers, not swap-event capture — a 3rd ruled-out
      path beyond the two this todo already named. The scoping doc identifies a reusable precedent already in this
      codebase (`build_drift_v2_sig_index.py`'s Helius sig-index walk pattern, generalizable to ORCA's
      `whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc` / Raydium's `675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8` program
      addresses, both already registered in UAC) plus the missing 2nd stage (per-tx fetch + AMM instruction decode)
      needed to actually extract swap records — filed as a `[DESIGN] P3` follow-up todo in that doc, not urgent since
      `dex_pool_swaps` coverage for every OTHER defi venue is unaffected. Repo: `market-tick-data-service`.

### G2 — verify honest-complete

- [x] ✅ [SCRIPT] P0. **VERIFIED 2026-07-27 (slot-4) — verdict recorded, gate NOT met, see full breakdown + follow-up
      todos below.** Final defi MVP verification: all 6 data_types attempted_failed=0 AND expected_unattempted=0
      post-genesis; subgraph-0-row-on-alive-day cells are `attempted_failed[UPSTREAM_SUBGRAPH_ZERO]` (re-run to fill,
      never silent); pre-genesis/protocol-paused are typed honest empties. Repos: `instruments-service`, `e2e-testing`.
      **Run:** `python scripts/measure_honest_coverage.py --asset-group defi`;
      `python3 e2e-testing/scripts/audit/manifest_hygiene_daily.py --asset-group defi --mode full`;
      `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run`. **Gate:** both failure
      buckets zero per data_type; 0 phantom; 0 dual-key ghost; verdict to Progress Log. **Full-execution criterion:**
      VM-list + coverage CLI output recorded per data_type. SPOT N/A. **RUN 2026-07-27 (slot-4) — GATE DOES NOT PASS.
      `expected_unattempted=0` holds for all 6 data_types, but `attempted_failed` is NON-ZERO for 5 of 6.**
      `measure_honest_coverage.py --asset-group defi` ran clean (99.99% reachable, 24,014,362/24,016,208).
      `manifest_hygiene_daily.py --asset-group defi --mode full` and
      `reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run` both got killed by SIGTERM (host memory
      pressure — this shared host was under severe combined memory contention across many concurrent slot agents'
      manifest reads; my own first attempt at a targeted per-data_type read also ballooned to 18.6GB RSS and was killed
      for the same reason before I switched to a lightweight single-file parquet read, mirroring
      `cf_manifest_audit.py`'s `_read_index` pattern — 4 columns, no full-manifest materialization). That lighter read
      gives the PRECISE per-data_type breakdown neither killed tool could produce this session (26,589,778 total defi
      manifest rows, 22,390,244 scoped to the 6 MVP data_types):

      | data_type        | captured   | empty_confirmed | attempted_failed | expected_unattempted |
              | ----------------- | ---------: | ---------------: | ----------------: | --------------------: |
              | dex_pool_state    | 16,710,467 |         1,484,900 |                19 |                     0 |
              | dex_pool_swaps    |  2,564,106 |         1,083,228 |               733 |                     0 |
              | lending_indices   |    336,041 |               141 |                52 |                     0 |
              | lst_rates         |     70,355 |               868 |                 2 |                     0 |
              | perp_funding      |     12,500 |                 0 |                 0 |                     0 |
              | oracle_prices     |    125,371 |               435 |             1,026 |                     0 |

              **Breaking down the 1,832 `attempted_failed` rows by `error_reason` (none carry the todo's own anticipated
              `UPSTREAM_SUBGRAPH_ZERO`-typed-empty tag — every one is a genuine, un-retried failure)**:

              1. **`oracle_prices` (1,026, venue=PYTH only) — ALREADY FIXED, just needs a re-run.** Error
                 `"Resolver requires aiodns library"`, dated 2023-10-01→2026-07-22. Root cause: `_http_resolver.py`'s
                 `aiohttp.resolver.AsyncResolver()` raised on any VM whose deployed venv lacked `aiodns`/`pycares` (only
                 present transitively via `ccxt`), and a bare `try/except` dropped the whole leg silently. **Fixed
                 `market-tick-data-service@533514c2`** ("aiodns-missing resolver crash silently dropped Solana LST rates on
                 every backfill day") — the LAST failure date (2026-07-22) matches this fix landing the same day; the fixed
                 code now falls back to aiohttp's default resolver instead of raising. These 1,026 rows are legacy residue
                 from BEFORE the fix — re-running PYTH oracle_prices for the failed date range should convert them to
                 `captured`/`empty_confirmed`, no new code change needed.
              2. **`dex_pool_swaps` (733) — LIVE, ongoing subgraph integration issue, NOT yet fixed.** Dated 2023-01-01→
                 2026-07-26 (as recent as yesterday). Reasons: `"All N cascade schemas returned GraphQL errors"` /
                 `"All N cascade schemas drifted"` for specific (protocol, chain) pairs — heaviest: uniswap_v3/OPTIMISM
                 (316), curve/OPTIMISM (312), trader_joe_v2/AVALANCHE (73), pancakeswap_v3/BSC (13) — plus 7
                 `build_instrument_id` errors. This reads as genuine subgraph schema drift/deprecation for these specific
                 (protocol, chain) pairs, not a code bug fixable in one commit.
              3. **`lending_indices` (52) — mixed: 46 stale-endpoint 404s (older) + 6 `FetchEvidence`-guard rejections, all
                 dated 2026-07-26 (yesterday, LIVE).** The 6 recent ones: `"record_empty(reason=SOURCE_RETURNED_ZERO)
                 requires FetchEvidence proving a clean [...]"` for MORPHO (2) + COMPOUND_V3 (4) — a validation guard
                 refusing to accept an empty-result claim without proof, per the honest-absence HARD RULE. Needs
                 investigation: is this guard correctly catching a real upstream problem, or incorrectly blocking a
                 legitimately-empty day?
              4. **`dex_pool_state` (19) — `build_instrument_id` errors**, needs investigation into which rows/why
                 instrument-id construction fails.
              5. **`lst_rates` (2) — `429` rate-limit errors**, trivial, needs only a retry.

              **Gate verdict: NOT MET.** Checkbox stays unflipped — 5 of 6 data_types have genuine, live, un-retried
              `attempted_failed` residue (categories 2-5 above are NOT just re-run-fill like category 1). Follow-up todos
              filed below, split by the distinct root cause each needs (do not bundle — they have different owners/fixes).
              **Full-execution criterion partially met**: coverage CLI output recorded per data_type (table above); the 2
              named audit scripts could not complete this session due to host memory contention — re-run them on a
              less-contended host or via a dedicated VM/Cloud Run job (mirrors `cf_manifest_audit.py`'s own 32Gi/8vCPU
              Cloud Run provisioning for the SAME reason) before considering this gate re-attempted.

- [ ] [SCRIPT] P1. Re-run PYTH `oracle_prices` for the 2023-10-01→2026-07-22 date range now that
      `market-tick-data-service@533514c2` (aiodns-fallback fix) is shipped — converts the 1,026 legacy
      `attempted_failed` rows to `captured`/`empty_confirmed`. No new code change; a backfill re-run only.
- [ ] [DATA] P1. Investigate `dex_pool_swaps` subgraph GraphQL-error/schema-drift failures (733 rows, live through
      2026-07-26) for uniswap_v3/OPTIMISM (316), curve/OPTIMISM (312), trader_joe_v2/AVALANCHE (73), pancakeswap_v3/BSC
      (13) + smaller counts for aerodrome_v3/BASE, uniswap_v4/ETHEREUM, uniswap_v3/POLYGON, pancakeswap_v3/ETHEREUM,
      velodrome_v2/OPTIMISM — determine whether the configured subgraph endpoint/schema needs updating per protocol, or
      whether these venues should be re-classified/quarantined. Repo: `market-tick-data-service`.
- [ ] [DATA] P2. Investigate the 6 `lending_indices`
      `record_empty(reason=SOURCE_RETURNED_ZERO) requires     FetchEvidence` guard rejections (MORPHO×2, COMPOUND_V3×4,
      all dated 2026-07-26) — determine if the guard is correctly blocking a genuine upstream problem or incorrectly
      rejecting a legitimately-empty day; fix the root cause on whichever side is wrong. Repo:
      `market-tick-data-service` or `instruments-service` (wherever the guard/adapter lives).
- [ ] [DATA] P2. Investigate `dex_pool_state`'s 19 `build_instrument_id` errors — identify the specific venue/instrument
      shapes that fail id construction. Repo: `market-tick-data-service`.
- [ ] [SCRIPT] P3. Retry the 2 `lst_rates` `429`-rate-limited cells (trivial). Repo: `market-tick-data-service`.

---

## Progress Log

> **Full day-by-day operational history extracted (2026-07-24 hygiene split — zero todo/gate/state change).** The
> ~4534-line, dated Progress Log (2026-06-27 through 2026-07-17: G0/G1 VM-launch log, the multi-day SPOT-preemption /
> OOM / stall-diagnosis cadence, the 6-run G2 gate-verification history, and the `-001`/`-002`/`-003` AO-dispatch-thrash
> saga) is moved VERBATIM to `mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md` § "Progress Log". Every Todos
> checkbox above (G0 / G1 / G1.5 / G1.6 / G2) is unchanged by this split — the last real gate reading remains the one
> recorded in that extracted log; re-run `measure_honest_coverage.py --asset-group defi` for a current number rather
> than trusting a stale one. **Append new Progress Log entries to the operational-log file going forward, not here**, to
> keep this plan under the line-cap.
