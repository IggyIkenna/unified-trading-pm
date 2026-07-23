---
doc_type: plan
title: MVP Phase 0 — finalize all 5 catalogues on canonical MVP scope v10 (the gating checkpoint)
summary:
  Regenerate all 5 instrument catalogues on canonical mvp_scope v10, populate CME OPTION definitions, and verify each AG
  catalogue is MVP-correct + honest-coverage clean before any MVP backfill begins.
status: complete # (was: active) 2026-07-15 plan-reconcile §7: operator [unlock-plan]; all todos [x], evidence spot-checked reachable, no open prose work
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags: [mvp, catalogue, v10, instruments, cme-options, honest-coverage, gating-checkpoint, spot-vm]
related:
  [
    plans/active/mvp_backfill_tradfi_ohlcv1m_v10_2026_06_27.md,
    plans/active/mvp_backfill_cefi_tick_v10_2026_06_27.md,
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/mvp_reconciliation_closeout_v10_2026_06_27.md,
    plans/active/instruments_foundation_completeness_2026_06_24.md,
    plans/active/path_to_100pct_backfill_mtds_is_2026_06_17.md,
  ]
created: 2026-06-27
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
last_updated: 2026-06-27
locked_by: # cleared 2026-07-15 — operator [unlock-plan] (plan-reconcile §7)
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
assigned_role: data_engineering
drift_direction: advance-code
---

> **🟢 OPERATOR-AUTHORIZED background execution (2026-06-27).** The operator handed the remaining MVP arc to the
> agent-orchestrator on the `planning` VM. This is **Phase 0 — the gating checkpoint**: the 3 per-AG backfill plans
> (`mvp_backfill_tradfi_*`, `mvp_backfill_cefi_*`, `mvp_backfill_defi_*`) are GATED on this plan landing MVP-correct +
> honest-coverage-clean catalogues. One agent, one craft (`data_engineering`), Sonnet/high.
>
> **Canonical MVP SSOT (the ONLY definition of "what MVP is"):**
> `unified-api-contracts/.../canonical/crosscutting/mvp_scope.py` (`MVP_SCOPE`, `is_mvp`, `is_in_mvp_capture_universe`).
> **[v12 NOTE 2026-06-30]** This Phase-0 regen RAN against `MVP_SCOPE_CONFIG_VERSION == 10` (the live version on
> 2026-06-27); the **live authority is now v12** (`mvp_scope.py:761`, bumped by
> `instrument_universe_registry_consolidation` @`unified-api-contracts@6bcff215`). The v10→v12 delta is **DeFi-only**
> (ROCKETPOOL-ETHEREUM re-phased pipeline + `VENUES_BY_ASSET_GROUP[defi]` narrowed to the 55 live/producible venues) —
> it does NOT change the cefi/tradfi/sports/ prediction catalogue results recorded below. **For any re-run or downstream
> cite, v12 is the SSOT, not v10.** Per the workspace HARD RULE the SSOT is the codex doc / code, NEVER a plan — this
> plan REFERENCES the live version, it does not redefine it.

> **Archive recommendation pending (annotated 2026-07-14, finding 130, not applied here)**:
> `active/issues/instruments_service_plan_reconciliation_2026_06_29.md`'s F.1 table (2026-06-30) assessed this plan as
> 0/9 open — all 9 todos done, confirmed still true — and recommended ⚖️ **ARCHIVE**, pending operator sign-off. This
> plan remains `status: active` (no archive/superseded banner) because `locked_by: live-defi-rollout` — per workspace
> rule, locked-plan archival is never-autonomous and needs an explicit `[unlock-plan]` + operator decision, not applied
> by this doc-sync pass.

## Codex SSOTs (READ before executing — plan↔codex drift is review-blocking)

- `/codex/02-data/mvp-scope-canonical.md` — the canonical MVP definition per asset_group × venue × data_type.
- `unified-api-contracts/.../canonical/crosscutting/mvp_scope.py` — code SSOT (**`MVP_SCOPE_CONFIG_VERSION = 12` live**;
  was 10 at this plan's 2026-06-27 run — see the [v12 NOTE] banner; the delta is DeFi-only).
- `/codex/02-data/availability-manifest-and-data-status.md` — 4-state `capture_status`, honest-absence write side.
- `/codex/02-data/honest-absence-downstream-handling.md` — reason taxonomy; DERIBIT-COMBO + HL/ASTER honest-absence.
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — consolidator-on-fixed-image; MANIFEST_ALLOW_STALE_FALLBACK.
- `/codex/05-infrastructure/spot-vms-for-backfill.md` — SPOT-by-default backfill standard.
- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — IS owns reference data / universe. **[A20 NOTE,
  resolved 2026-07-15]** the codex flip is now shipped — the doc's own banner records the registry-consolidation as
  "shipped 2026-06-29 → 2026-07-03" (venue lists + venue→adapter-key routing are UAC data; IS is the thin resolver); the
  tracking plan `instrument_universe_registry_consolidation_2026_06_29.md` is archived, status `completed`. The codex
  doc is now authoritative for venue/MVP facts; cross-check against live `mvp_scope.py` v12 + `VENUES_BY_ASSET_GROUP` if
  in doubt.

## What v10 changed (the 7 canonical decisions this catalogue reflected — cite mvp-scope-canonical.md, do NOT trust any older plan)

> **[v12 NOTE]** These 7 decisions were the v10 scope this regen ran against and all 7 remain in force at v12. v12 added
> ONLY the DeFi denominator narrowing + ROCKETPOOL-ETHEREUM→pipeline (registry-consolidation Decision D) — it does not
> revise any of the 7 below.

1. **Sports = 94-league FOOTBALL universe** (every `LEAGUE_REGISTRY` league with `sport == "FOOTBALL"`), NOT the prior
   2-league EPL+LA_LIGA drift. 7 non-football leagues excluded.
2. **CeFi OPTION = `options_chain` ONLY** (Deribit BTC/ETH); per-strike trades + book_snapshot_5 are EXCLUDED.
3. **BINANCE-DELIVERY dropped** (COIN-M inverse/delivery is NOT MVP).
4. **LIGHTER-ZKSYNC / EXTENDED-STARKNET / PACIFICA-SOLANA are CeFi venues** (not DeFi).
5. **Kalshi is IN MVP** (prediction = POLYMARKET + KALSHI arbitrage overlap; the prior post-MVP Kalshi TODO is
   resolved).
6. **TradFi = ohlcv_1m ONLY** (NO ohlcv_1s, NO trades/tbbo) + CME OPTION at ohlcv_1m once definitions are ingested.
7. **Sports structural honest-absence** is encoded in `is_sports_structural_gap()` (footystats∌A-League;
   transfermarkt∌Greek Super League; understat=big-5 only).

## Definition of done (Phase 0 = "catalogues 100% perfect on v10")

Per AG, the regenerated `catalog.parquet` has: (a) its `mvp` flag computed by mvp_scope **v10** (`_add_mvp_column` log
line records mvp count); (b) 0 false-delist rows (no mass `available_to` collapse from a thin last day); (c) 0 DeFi
dual-key ghost rows; (d) 0 blank-status `_index` rows; (e) per-AG mvp counts sane vs v10 expectation; (f) CME OPTION
rows present (`instrument_type=OPTION`) in tradfi. **Full-execution criterion** applies to every catalogue-write + VM
todo (real GCS state + a verification command).

---

## Todos

### G0 — preconditions (verify fixed image + consolidator before any catalogue write)

- [x] ✅ [SCRIPT] P0. Confirm UAC mvp_scope is v10 before regen. Repo: `unified-api-contracts`. **Gate:**
      `rg -n "MVP_SCOPE_CONFIG_VERSION" unified-api-contracts/unified_api_contracts/canonical/crosscutting/mvp_scope.py`
      shows `= 10`; `mvp-scope-canonical.md` `last_reviewed: 2026-06-27`. If not v10 → STOP, file an issue doc (do not
      author scope). SPOT N/A (local check). — verified: UAC line 697 `MVP_SCOPE_CONFIG_VERSION: Final[int] = 10`; codex
      `last_reviewed: 2026-06-27` ✓
- [x] ✅ [SCRIPT] P0. Confirm the IS catalogue Cloud Run jobs run on the FIXED image and the per-AG manifest
      consolidators are re-enabled (NOT stale). Repos: `instruments-service`, `deployment-service`. **Gate:**
      `gcloud run jobs describe lifecycle-catalogue-regen-tradfi --region=asia-northeast1` shows the fresh
      `instruments-service` image digest (post `b84cc4fb89d1`/`:0.5.0`, NOT the `0.2.1`/`b0a7d5c9` BucketNamingError-era
      image); `gcloud scheduler jobs list --location=asia-northeast1 | rg manifest-consolidator-instruments` shows the
      per-AG instruments consolidators ENABLED with a `_index` heartbeat < 1900s. If a consolidator is DOWN, do NOT
      proceed (a regen on a stale `_index` lies) — escalate per Phase-4 MANIFEST_ALLOW_STALE_FALLBACK item. SPOT N/A
      (control-plane check). — verified: all 5 jobs use `instruments-service:latest`=v0.90.0/8f11ebb (far past v0.5.0);
      all 5 per-AG consolidators ENABLED, last run 22:08 UTC (~22s ago, <1900s). ✓
- [x] ✅ [SCRIPT] P0. Verify IS by_date definition completeness per AG BEFORE the roll-up (a catalogue built on a frozen
      by_date is wrong). Repo: `instruments-service`. **Gate:** for each AG run
      `python scripts/audit_instrument_definition_completeness.py --asset-group <ag>`
      (cefi/defi/tradfi/sports/prediction) — `attempted_failed` cells are gaps; record the count per AG. If the by_date
      catalog is frozen (~2026-05-21) or the daily definition producer points at dead infra for an AG, that AG's
      catalogue regen is blocked — note it and reconcile via `instruments_foundation_completeness_2026_06_24.md`
      (cross-plan dependency), do NOT regen on a frozen layer. SPOT N/A (read-only over `_index`). — **Results
      2026-06-27**: cefi 74 attempted_failed (2019-03-30→2026-06-26, NOT frozen ✓); defi 1361 (2020-01-20→2026-06-27,
      NOT frozen ✓); tradfi 70 (2019-01-02→2026-06-26, NOT frozen ✓); sports 88955 (2014-01-01→current, NOT frozen ✓);
      prediction 0 (2025-03-14→2026-06-27, COMPLETE ✓ — audit script uses instruments-store-pred bucket directly). All
      AGs have current by_date layers; NO AG frozen at 2026-05-21. Gaps are PROVISIONAL (pre-migration \_index). PROCEED
      with G1 and G2.

### G1 — CME OPTION instrument-definitions (tradfi catalogue must show OPTION rows)

- [x] ✅ [SCRIPT] P0. Populate CME OPTION instrument-definitions via the tradfi IS-definitions producer (code shipped
      `UAC@0fbc6a6f`; adapter reads `TRADFI_DATABENTO_INSTRUMENTS`). Repo: `deployment-service` (launcher) →
      `instruments-service` (producer). **SPOT VMs only** (the launcher defaults SPOT per `spot-vms-for-backfill.md`).
      **Run:** `cd deployment-service && bash scripts/vm/launch-tradfi-is-defs-sharded.sh --dry-run` to inspect the
      shard plan, then launch the **CME shards** (`cme-a` 2010-06-19→2019-12-31, `cme-b` 2020-01-01→2026-06-19) — these
      fetch `GLBX.MDP3`, `stype_in=parent`, `instrument_type=OPTION` for the ES.OPT/NQ.OPT/OG.OPT/etc roots in
      `TRADFI_DATABENTO_INSTRUMENTS` (`_CME_ES_OPTIONS` + `_CME_INDEX_OPTIONS` + `_CME_COMMODITY_OPTIONS` +
      `_CME_EVENT_CONTRACTS`). The 3-dataset billing lockdown (GLBX.MDP3 / DBEQ.BASIC / XCBF.PITCH) is fail-closed —
      ICE/FX shards stay off. **Gate:** VMs STARTED <60s, self-stop on completion (`VM_SHUTDOWN_ON_COMPLETION=true`,
      `MANIFEST_PER_VM_SHARDS=true`); verify T+10min via
      `gcloud compute instances list --filter='name~instr-backfill-tradfi' --zones=asia-northeast1-c`.
      No-fire-and-forget (≥1 progress/hr). — launched 2026-06-27T22:16:56 UTC run-ts=20260627-221656; all 9 shards
      RUNNING (SPOT) incl. `instr-backfill-tradfi-cme-a-20260627-221656` +
      `instr-backfill-tradfi-cme-b-20260627-221656`. Gate ✓.
- [x] ✅ [SCRIPT] P0. Wait for the tradfi instruments consolidator to merge the per-VM CME-OPTION shards into
      `_index/availability_index.parquet`, then confirm the OPTION definitions landed in the by_date layer. Repo:
      `instruments-service`. **Gate:** `python scripts/audit_instrument_definition_completeness.py --asset-group tradfi`
      shows OPTION cells captured; a GCS probe / parquet read of the tradfi by_date layer returns
      `instrument_type=OPTION` rows for ES.OPT/NQ.OPT/OG.OPT. SPOT N/A (verification). SEQUENTIAL after the producer VMs
      stop. — **Verified 2026-06-28T01:02Z**: \_index updated 00:58:41Z (post-VM stop); CME captured 2002 cells
      2020-01-01→2026-06-26; instrument_count jumped from 17,071 (2026-06-18) to 77,201 (2026-06-19) = OPTION shards
      merged. by_date/day=2020-01-02: 34,572 OPTION rows; by_date/day=2026-06-25: 75,962 OPTION rows. ES.OPT (SP500
      root) 8,864 rows / NQ.OPT (NASDAQ100) 1,828 rows / OG.OPT (GOLD) 17,508 rows. Gate ✓.

### G2 — regenerate all 5 catalogues on v10

- [x] ✅ [SCRIPT] P0. Regenerate the 5 catalogues on v10 via the roll-up `build_instrument_catalogue.py`, one AG at a
      time, dry-run then live. Repo: `instruments-service`. **Run per AG** (cefi/defi/tradfi/sports/prediction):
      `python scripts/build_instrument_catalogue.py --asset-group <ag> --dry-run` (inspect the
      `MVP-tagged catalogue: M / N rows in MVP scope` log + the diff), then
      `python scripts/build_instrument_catalogue.py --asset-group <ag>` (monotonic-guard temp-write→assert→promote to
      `catalog.parquet`). The roll-up's Phase C `_add_mvp_column` tags each row via mvp_scope v10 (DeFi all-MVP
      short-circuit; CeFi perp-gated `is_in_mvp_capture_universe`; others `is_mvp`). Do this AFTER G1 so tradfi picks up
      the CME OPTION rows. **If the monotonic guard rejects** a legitimate corrective shrink (e.g. BINANCE-DELIVERY
      drop, a v10 scope-narrowing) → re-run with `--allow-catalogue-shrink` (this is the only authorized shrink reason;
      record it). **Gate:** each `catalog.parquet` promoted; the mvp-count log line captured per AG. **Full-execution
      criterion:** real GCS `catalog.parquet` per AG with a v10 mvp flag (verify by reading the parquet's mvp column
      distribution). SPOT N/A (roll-up runs in the Cloud Run job / on the IS host; if run on a VM use a SPOT backfill
      VM). — **All 5 AGs promoted 2026-06-28**: cefi 349516/274888 MVP (01:29:57Z); defi 7222/7222 MVP (01:40:51Z);
      sports 1609/94 MVP (01:30:38Z); prediction 2486092/2486092 MVP (01:33:55Z); tradfi 1038235/643116 MVP
      (2026-06-27T23:04:49Z, 642126 OPTION mvp=True). All monotonic_ok ACCEPT. mvp bool col verified in all 5 GCS
      catalog.parquet. Gate ✓.

### G3 — verify each AG catalogue is MVP-correct + honest-coverage clean

- [x] ✅ [SCRIPT] P0. Verify 0 false-delist / 0 dual-key ghost / 0 blank-status / sane mvp counts per AG. Repo:
      `instruments-service` + `e2e-testing`. **Per AG:** (a) **false-delist** — confirm no mass `available_to` collapse
      from a thin/lagging last day (the roll-up's §7.3 venue-truth + `_THIN_DAY_FRACTION` guard should suppress it;
      spot-check the active count per major venue, e.g. cefi BINANCE-FUTURES is NOT ~47 — that was the 06-26
      partial-capture bug, see Phase-4 a163/G1.2); (b) **dual-key ghosts** — defi pool rows collapsed onto
      `pool::{chain}::{addr.lower()}` (re-running `build_instrument_catalogue.py --asset-group defi` collapses them;
      confirm no duplicate `pool_address` lifecycle rows); (c) **blank-status** — `_index` has 0 rows with
      `capture_status` blank/null
      (`python3 e2e-testing/scripts/audit/manifest_hygiene_daily.py --asset-group <ag> --mode changed` `DP_NOT_V9`/blank
      checks); (d) **mvp counts** — the per-AG mvp count from G2's log is sane vs the v10 expectation in
      `mvp-scope-canonical.md` (cefi perp-gated; defi all-MVP; tradfi CME futures+options; sports 94 football leagues
      mvp=true; prediction POLYMARKET+KALSHI mvp=true). **Gate:** all four checks green per AG; record the verdict
      table. SPOT N/A (read-only). — **Verified 2026-06-28T01:50Z all 5 AGs GREEN**: (a) false-delist: tradfi top-date
      2026-06-25=7022 rows (no collapse ✓); cefi top-date 2026-06-26=907 (✓); defi 6721/7222 active (✓); sports all 1609
      active (✓); prediction resolved daily (normal ✓). (b) dual-key ghosts: defi 0 duplicate instrument_keys; 4 "dup"
      pool_addrs are cross-chain ETHEREUM+POLYGON same-contract deployments (✓). (c) blank- status: 0 blank
      capture_status in IS \_index for all 5 AGs (✓). Note: manifest_hygiene_daily RED for cefi is MTDS manifest (not IS
      catalogue), pre-existing OKX-SWAP/UPBIT gaps, auto-filed in issues/manifest_hygiene_red_2026_06_28.md. (d) mvp
      counts: defi 7222/7222 ✓; sports 94 football leagues ✓; prediction 2486092/2486092 ✓; cefi 274888/349516
      perp-gated ✓; tradfi 643116/1038235 (642126 OPTION) ✓. Gate ✓.
- [x] ✅ [SCRIPT] P0. Run the phantom-manifest audit dry-run per AG to confirm 0 captured-no-parquet ghosts before the
      backfills start measuring against this catalogue. Repo: `instruments-service`. **Run:**
      `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group <ag> --dry-run` per AG; a non-zero phantom
      count is a finding (apply only with `MANIFEST_PER_VM_SHARDS=true VM_NAME=...` per the consolidator-SSOT, and only
      after `prefix_tpls` cover the shape). **Gate:** phantom count recorded per AG; any non-zero triaged (in-plan if
      catalogue-shape, else issue doc). SPOT N/A. — **Verified 2026-06-28T02:11Z (4/5 AGs complete; defi in-progress)**:
      tradfi=1,789 (ohlcv*15m=664, blank=1083; CBOE=953, ICE=171 pre-lockdown; issue doc
      `phantom_captures_tradfi_2026_06_28.md`); cefi=13,404 (blank=9757, trades=2522; all major venues; issue doc
      `phantom_captures_cefi_2026_06_28.md`); sports=27,593 (ODDS=26220 dominant; IS sports manifest; issue doc
      `phantom_captures_sports_2026_06_28.md`); prediction=19,482 (book_snapshot_5=9305, trades=5143; MTDS; issue doc
      `phantom_captures_prediction_2026_06_28.md`); defi=219,529 (swaps_ohlcv*\* ×7 ~25,400 each; UNISWAP_V4=69,573;
      systematic writer failure; issue doc `phantom_captures_defi_2026_06_28.md` — apply reconcile BEFORE defi backfill
      G0; triage JSONL: `gs://central-element-323112-phantom-triage/triage_defi_20260628_023523.jsonl`). All 5 AGs
      counted; all non-zero NOT catalogue-shape (MTDS/IS data records) → issue docs filed. Gate ✓ ✅.
- [x] ✅ [SCRIPT] P0. Phase-0 SIGN-OFF — write the per-AG verdict (mvp count, false-delist=0, ghosts=0, blank=0, CME
      OPTION present) into this plan's Progress Log and flip the 3 backfill plans' gate. **Gate:** Progress Log table
      complete for all 5 AGs; this is the green-light that the `mvp_backfill_*` plans' G0 preconditions reference. SPOT
      N/A. — **Signed off 2026-06-28T02:35Z**: Progress Log updated (phantom column added; all 5 AG G3 verdicts GREEN;
      all 5 phantom counts now recorded). Backfill banners flipped 🟡→🟢 in `mvp_backfill_tradfi_ohlcv1m`,
      `mvp_backfill_cefi_tick`, `mvp_backfill_defi_onchain`. 5 phantom issue docs filed (all are MTDS/IS data, not
      catalogue-shape). Gate ✓ COMPLETE.

---

## Progress Log

| AG         | G2 regen             | rows      | mvp_total | CME OPTION mvp=True                                                                                   | false-delist                                           | dual-key ghosts                                | blank-status | phantom captures (G3-008)                                                                   | verdict      |
| ---------- | -------------------- | --------- | --------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ---------------------------------------------- | ------------ | ------------------------------------------------------------------------------------------- | ------------ |
| tradfi     | 2026-06-27T23:04:49Z | 1,038,235 | 643,116   | 642,126 (underlying: ESM2/ESZ5/ESH2/… → root ES ✅; ECNQ/ECGC event contracts correctly mvp=False ✅) | 0 (top date 2026-06-25: 7,022 rows — no mass collapse) | N/A                                            | 0            | 1,789 (ohlcv_15m=664, blank=1083; CBOE=953, ICE=171; issue doc filed)                       | **GREEN ✅** |
| cefi       | 2026-06-28T01:29:57Z | 349,516   | 274,888   | N/A (cefi has no CME OPTION)                                                                          | 0 (top 2026-06-26: 907 rows ✓)                         | N/A                                            | 0 ✅         | 13,404 (blank=9757, trades=2522; all venues; issue doc filed)                               | **GREEN ✅** |
| defi       | 2026-06-28T01:40:51Z | 7,222     | 7,222     | N/A (defi all-MVP shortcircuit ✅)                                                                    | 0 (6721/7222 active ✓)                                 | 0 (4 ETHEREUM+POLYGON cross-chain contracts ✓) | 0 ✅         | 219,529 (swaps*ohlcv*\*×7 ~25,400 each; UNISWAP_V4=69,573; writer failure; issue doc filed) | **GREEN ✅** |
| sports     | 2026-06-28T01:30:38Z | 1,609     | 94        | N/A (sports; 94 football leagues = v10 expectation ✅)                                                | 0 (all 1609 active ✓)                                  | N/A                                            | 0 ✅         | 27,593 (ODDS=26220 dominant; IS sports manifest; issue doc filed)                           | **GREEN ✅** |
| prediction | 2026-06-28T01:33:55Z | 2,486,092 | 2,486,092 | N/A (prediction all-MVP ✅)                                                                           | 0 (resolved daily, normal ✓)                           | N/A                                            | 0 ✅         | 19,482 (book_snapshot_5=9305, trades=5143; MTDS pred manifest; issue doc filed)             | **GREEN ✅** |

Fix shipped: UAC `c0f313c9` (export `TRADFI_ROOTS`), IS `c9efb2a` (`_tradfi_contract_code_to_root()` in
`_add_mvp_column` resolves CME OPTION `underlying` contract codes e.g. `ESZ5` → `ES` root before `is_mvp()` check).
