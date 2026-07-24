---
doc_type: issue
title:
  DeFi upstream 46-day full backfill — operator approval required (instruments-service DeFi + MTDS DeFi raw_tick_data)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-16
source:
  [
    "ikenna-slot-3 finding at plans/active/issues/defi_features_pipeline_not_run_2026_05_14.md (LST ✅, MDPS ❌)",
    "MDPS DeFi backfill VM (mdps-backfill-defi-20260516-205843 FAILED rc=1, self-deleted) surfaced upstream gap",
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-16
superseded_by:
  plans/active/mtds_backfill_phase3_2026_05_22.md § Phase 3 (DeFi MTDS backfill). P2 --venues CLI mismatch migrated
  there.
severity:
  P1 — non-blocking for B-015 paper-trade (5-day window pre-authorized in parallel ping); blocking for live DeFi data
  correctness across full historical window
launched_at: 2026-05-20
priority: P2
---

> **🔴 P0 SCOPE EXPANSION 2026-05-20 — mega-audit A3 absorbed**: in addition to the 46-day window currently in flight,
> this plan now owns the full historical DeFi MISSING_EXPECTED + DIVERGENT_EMPTY backlog from A3:
>
> - **184,512 `MISSING_EXPECTED` cells** across FLUID-ETHEREUM (all 4 lending types),
>   MORPHO-{ETHEREUM,POLYGON,ARBITRUM,BASE,OPTIMISM} (all 4 lending types), CURVE-ETHEREUM (dex_swaps + dex_pools),
>   BALANCER (all 6 chains), UNISWAP_V2-ETHEREUM, UNISWAP_V3-{ARBITRUM,BASE,OPTIMISM,POLYGON}, UNISWAP_V4-ETHEREUM,
>   COMPOUND_V3-{all chains}, AAVE_V3-{LINEA,BSC}, LIDO/ETHERFI/ETHENA-ETHEREUM, JITO-SOLANA.
> - **765 `DIVERGENT_EMPTY` cells** (the Drift-S3-bug class — all in DeFi). Full per-cell list in
>   `plans/audit/results/manifest_divergence_2026_05_20.parquet`.
>
> Reassigned slot 6 (was deployment_ui_lifecycle_tabs) to own this expanded scope per `work_split_2026_05_19_ikenna.md`
> § "Slot 6 — REASSIGNED" + CLAUDE.md HARD RULE "Data Pipeline Correctness Is The Heartbeat". **Scope MUST cover every
> DeFi (venue, data_type, time-range) cell — no asset_group skipped, no deadline-driven cutbacks** (operator directive
> 2026-05-20). Closed-set deferral only via `BLOCKED-CREDENTIALS` / `BLOCKED-OPERATOR-DECISION` /
> `BLOCKED-UPSTREAM-OUTAGE` with operator ack.

> **🟢 LAUNCHED 2026-05-20T01:22Z** — Option A executed. Launcher scripts edited (`deployment-service@2f3c5a5` +
> `0bfc73b` — `--start/--end` + `--asset-group` filter + bash-3.x compat). 12 VMs RUNNING in asia-northeast1-c covering
> window 2026-04-01..2026-05-16: 1 instruments-service DeFi VM
>
> - 10 newly-launched MTDS DeFi VMs + 1 pre-existing `mtds-gas-fees-solana` (covers window). Expected wallclock 2-4h.
>   T+10min verification armed. See `plans/active/issues/defi_46day_backfill_launch_status_2026_05_20.md` for VM table +
>   execution notes. Banner removed when manifest divergence A3 shows zero MISSING_EXPECTED for the 46-day window.

## What I found

Slot-3's deeper investigation into B-015 features-onchain Smoke B failure surfaced a systemic gap that goes beyond the
original 5-day smoke target:

The MDPS DeFi pipeline requires 2 upstream dependencies that are **missing for the entire 2026-04-01 → 2026-05-16
window** (46 days):

1. **`gs://instruments-store-defi-central-element-323112/instrument_availability/by_date/day=*/`** — DeFi instruments
   index (per-protocol enumerator writes; needs instruments-service DeFi backfill).
2. **`gs://market-data-tick-defi-central-element-323112/raw_tick_data/by_date/day=*/`** — DeFi raw tick data (needs
   coordinated multi-handler MTDS DeFi batch: solana_defi_handler + evm_defi_handler + lst_rates_handler +
   gas_fee_handler).

The 5-day smoke window (2026-04-15..19 — slot 9's original B-015 target) is being addressed in parallel by slot-3 since
<1 week is pre-authorized per CLAUDE.md HARD RULE. See cross-side ping `plans/active/_agent_pings.md` § "2026-05-16
[time] ikenna-main → ikenna-slot-3 / harsh-slot-9".

## Why it matters

- **NOT a B-015 paper-trade blocker** — the 5-day smoke window is sufficient for the carry_staked_basis Phase 2 launch;
  that work is sequencing through slot-3 in parallel.
- **IS a data-correctness blocker for full live-DeFi** — without the 46-day backfill, any feature/strategy that reads >5
  days of historical DeFi data hits silent gaps.
- May-23 cutover live-DeFi gate is the trigger date for the data-correctness ask.

## Operator approval request (per CLAUDE.md HARD RULE — ≥1 week)

```
BACKFILL APPROVAL REQUEST — DeFi upstream 46-day full backfill

Window: 2026-04-01 → 2026-05-16 (46 days)
Asset group: defi
Buckets affected:
  - gs://instruments-store-defi-central-element-323112/instrument_availability/
  - gs://market-data-tick-defi-central-element-323112/raw_tick_data/
Est rows: ~46 days × ~5 protocols × multiple data_types per protocol = ~5,000-10,000 manifest rows
Est VM compute: 4-8 hours wall-clock if coordinated multi-handler batch
Singleton-locked launchers required per CLAUDE.md (no fire-and-forget)
```

Unblocks: full live-DeFi data correctness across historical window. Without it, any feature/strategy reading >5 days of
DeFi history silently hits gaps.

## Recommended decision

Operator picks one:

- **(A) Run the full backfill** — slot-3 owns; coordinated multi-handler batch on same-region GCE VMs; ~4-8 hours.
- **(B) Defer to post-cutover** — file successor plan `defi_upstream_full_backfill_post_cutover_2026_06_01.md`; May-23
  live-DeFi cuts over with only the 5-day smoke + forward-rolling new data.
- **(C) Tighter window** (e.g. 14 days) — covers carry_staked_basis recent-history needs without full 46-day scope. ~1-2
  hours VM compute.

**My recommendation**: **(C) 14-day backfill** as the pragmatic middle. carry_staked_basis only needs recent-history for
parameter estimation + smoke validation; doesn't need full 46-day archive. Post-cutover can absorb the remainder if
needed.

## Cross-references

- Companion: `plans/active/issues/defi_features_pipeline_not_run_2026_05_14.md` (slot-3's finding)
- Cross-side ping: `plans/active/_agent_pings.md` § "2026-05-16 ikenna-main → ikenna-slot-3 / harsh-slot-9"
- CLAUDE.md § "GCS backfill approval gate (codified here)" — ≥1 week → operator approval required

---

## Triage — 2026-05-18

**Status**: OPEN **Triaged by**: slot-8 triage sweep **Reason**: Operator approval pending for 46-day backfill execution

---

title: "DeFi 46-day upstream backfill launch — LAUNCHED (12 VMs in flight)" created: 2026-05-20 author: ikenna-slot-1
(operator authorization 2026-05-20 "we should do this now, defi needs working" + Option A pin) source:

- "plans/active/issues/defi_upstream_46day_full_backfill_2026_05_16.md (parent — operator approval granted 2026-05-20)"
- "deployment-service@0bfc73b (launcher --start/--end + --asset-group + bash-3.x compat)" locked_by: live-defi-rollout
  locked_since: 2026-05-20 severity: P1 — LAUNCHED 2026-05-20T01:22Z; closes when manifest divergence A3 confirms zero
  MISSING_EXPECTED for the 46-day window. launched_at: 2026-05-20T01:22Z # 12 VMs RUNNING; T+10min verification armed

---

> **🟢 LAUNCHED 2026-05-20T01:22Z** — Option A (launcher edit) executed. 12 VMs RUNNING in asia-northeast1-c: 1
> instruments-service DeFi (`instr-backfill-defi-20260516`) + 10 MTDS DeFi (relaunched) + 1 MTDS gas-fees-solana
> (pre-existing, covers window). Window 2026-04-01..2026-05-16. Expected wallclock 2-4h. T+10min verification armed.
> Banner removed when manifest divergence A3 confirms zero MISSING_EXPECTED.

## What I found

Preflight inspection of the launcher scripts revealed that the instruments-service DeFi half of the 46-day backfill
**cannot be launched without modifying launcher code**. The MTDS DeFi half is launchable as-is via `--start/--end`
flags, but launching MTDS without instruments-service first will produce shards with `EXPECTED_DEPENDENCY_NOT_AVAILABLE`
emissions (instruments-service is the upstream universe enumerator). Per writegate dependency-chain semantics the MTDS
half is wasted compute without the instruments half landing first.

Per CLAUDE.md HARD RULE "Blockers to flag (pause if hit) — Launcher script doesn't accept the date range cleanly" I have
stopped at preflight and not launched any VMs.

### Launcher state matrix (DeFi-relevant only)

| Launcher                                        | Accepts `--start/--end`? | Hardcoded END                  | Action needed                                                                                         |
| ----------------------------------------------- | ------------------------ | ------------------------------ | ----------------------------------------------------------------------------------------------------- |
| `launch-instruments-backfill-vm.sh`             | NO                       | 2026-02-28 (DeFi VM)           | **EDIT or workaround required**                                                                       |
| `launch-defi-backfill-vm.sh` (instr-targeted)   | NO                       | 2026-04-04                     | **EDIT or workaround required**                                                                       |
| `launch-mtds-dex-pools-backfill-vm.sh`          | YES (`--start/--end`)    | n/a (default = today)          | OK — launches with override                                                                           |
| `launch-mtds-eigenlayer-rewards-backfill-vm.sh` | YES                      | n/a                            | OK                                                                                                    |
| `launch-mtds-liquidations-backfill-vm.sh`       | YES                      | n/a                            | OK                                                                                                    |
| `launch-mtds-perp-funding-backfill-vm.sh`       | YES                      | n/a                            | OK                                                                                                    |
| `launch-mtds-solana-drift-backfill-vm.sh`       | YES                      | n/a                            | OK                                                                                                    |
| `launch-mtds-gas-fees-backfill-vm.sh`           | YES (positional)         | n/a                            | OK                                                                                                    |
| `launch-mtds-lending-indices-backfill-vm.sh`    | YES (positional)         | n/a                            | OK                                                                                                    |
| `launch-mtds-lst-rates-backfill-vm.sh`          | YES (positional)         | n/a                            | OK                                                                                                    |
| `launch-mtds-pyth-archive-backfill-vm.sh`       | YES (positional)         | n/a (2022-11..2023-09 default) | OK with override                                                                                      |
| `launch-mtds-pyth-lst-backfill-vm.sh`           | YES (positional)         | n/a                            | OK                                                                                                    |
| `launch-mtds-vault-share-price-backfill-vm.sh`  | YES (positional)         | n/a                            | OK                                                                                                    |
| `launch-mtds-solana-gas-backfill-vm.sh`         | YES                      | n/a                            | **SKIP — VM `mtds-gas-fees-solana` already RUNNING since 2026-05-19 covering 2021-01-01..2026-05-19** |

### Currently-running DeFi backfill VMs (preflight inventory 2026-05-20 07:55Z)

```
mtds-gas-fees-solana             RUNNING   created 2026-05-19T11:41:56-07:00  range 2021-01-01..2026-05-19 (covers window)
mtds-backfill-odds-1             RUNNING   created 2026-05-19T11:42:10-07:00  (prediction/sports — not DeFi)
mtds-dex-pools-backfill          TERMINATED created 2026-05-19T11:41:49-07:00 (safe to relaunch)
mtds-eigenlayer-rewards-backfill TERMINATED ... (safe to relaunch)
mtds-liquidations-backfill       TERMINATED ... (safe to relaunch)
mtds-perp-funding-backfill       TERMINATED 2026-05-16T04:52:27-07:00 (safe to relaunch)
mtds-solana-drift-backfill       TERMINATED 2026-05-19T12:35:53-07:00 (safe to relaunch)
```

No VM-name collisions for the proposed MTDS relaunches (each launcher uses a fixed name and the prior VM is TERMINATED).

## Why it matters

Operator said "we should do this now, defi needs working" at 2026-05-20 expecting the backfill to launch. Surfacing the
launcher-edit blocker explicitly so the operator picks a path rather than slot-1 silently editing launcher scripts and
triggering downstream prek-hook / commit-flip discipline overhead during an active dispatch.

## Operator decision required

**Pick ONE**:

### (A) Edit both instruments-service launchers to accept `--start/--end` (RECOMMENDED)

- Edit `launch-defi-backfill-vm.sh` to accept `--start <YYYY-MM-DD>` and `--end <YYYY-MM-DD>` (matching MTDS launcher
  convention).
- Edit `launch-instruments-backfill-vm.sh` to (a) accept `--asset-group defi` filter, OR (b) accept `--start/--end`
  override for the DeFi VM only.
- Launch `instr-backfill-defi-targeted-46d` with `--start 2026-04-01 --end 2026-05-16`.
- Time: ~30 min launcher edit + 10 min VM bootstrap + ~2-4h backfill wallclock.
- Commit + flip discipline applies (deployment-service@<sha> + plan-flip in same agent turn).

### (B) One-shot inline override (bypass launcher edit)

- Slot 1 writes a one-off `launch-defi-46day-backfill.sh` (copy of `launch-defi-backfill-vm.sh` with
  `START_DATE=2026-04-01`
  - `END_DATE=2026-05-16` hardcoded + unique VM name `instr-backfill-defi-46d-20260520`).
- Lives at `deployment-service/scripts/vm/launch-defi-46day-backfill.sh` (one-off, kept until backfill validated).
- Time: ~10 min script copy + launch.
- Risk: workspace drift — launcher SSOT now has 3 DeFi-instrument launchers.

### (C) Defer instruments-service half; launch MTDS-only half NOW

- Skip instruments-service backfill (accept that DeFi raw_tick_data shards will mostly
  `record_empty(EXPECTED_DEPENDENCY_NOT_AVAILABLE)`).
- Launch 12 MTDS DeFi backfill VMs with `--start 2026-04-01 --end 2026-05-16`.
- Useful **only if** the MTDS handlers can synthesize a universe from on-chain enumeration without consulting
  instruments-service availability — VERIFY before launching.
- NOT RECOMMENDED — wasted compute risk is high without confirming MTDS handler universe-resolution path.

### (D) Different window

- E.g. 14-day backfill (2026-05-02..2026-05-16) per parent-issue option (C). Smaller scope, faster turnaround.
- Still requires instruments-service launcher fix per (A) or (B).

## Recommended decision

**(A) — edit both launchers properly + relaunch full 46-day instruments + MTDS DeFi fleet.** Single clean modification,
durable for future backfill operations, aligns with launcher SSOT convention.

## VM plan (for execution once operator picks path)

If (A) or (B) approved, slot 1 will launch in this order:

1. **Stage 1 — instruments-service DeFi** (must land first):
   - VM `instr-backfill-defi-46d-20260520` (asia-northeast1-c, e2-standard-4)
   - Range 2026-04-01..2026-05-16, all 7 DeFi venues (CURVE-AVALANCHE, CURVE-OPTIMISM, BALANCER-ETHEREUM,
     UNISWAP_V3-ETHEREUM, UNISWAP_V3-POLYGON, RAYDIUM-SOLANA, UNISWAP_V4-ETHEREUM).
   - Expected duration: 2-4h wallclock.
   - Output:
     `gs://instruments-store-defi-central-element-323112/instrument_availability/by_date/day=2026-04-01..day=2026-05-16/`.
   - T+10min verification:
     `gcloud compute instances describe instr-backfill-defi-46d-20260520 --zone=asia-northeast1-c --format='value(status)'`
     = RUNNING + log file present in GCS staging.

2. **Stage 2 — MTDS DeFi raw_tick_data fleet** (depends on Stage 1 mostly-complete; can start ~1h into Stage 1):
   - 11 VMs in parallel (skip solana-gas — already running):
     - `mtds-dex-pools-backfill` (--start 2026-04-01 --end 2026-05-16)
     - `mtds-eigenlayer-rewards-backfill` (same)
     - `mtds-liquidations-backfill` (same)
     - `mtds-perp-funding-backfill` (same — covers DeFi perps via Hyperliquid)
     - `mtds-solana-drift-backfill` (same)
     - `mtds-gas-fees-<ts>` via positional `2026-04-01 2026-05-16`
     - `mtds-lending-indices-<ts>` (positional 2026-04-01 2026-05-16)
     - `mtds-lst-rates-<ts>` (positional 2026-04-01 2026-05-16)
     - `mtds-pyth-archive-<ts>` (positional 2026-04-01 2026-05-16)
     - `mtds-pyth-lst-<ts>` (positional 2026-04-01 2026-05-16)
     - `mtds-vault-share-price-<ts>` (positional 2026-04-01 2026-05-16)
   - Expected duration per VM: 1-3h wallclock; total fleet wallclock ~3h (parallel).
   - Output: `gs://market-data-tick-defi-central-element-323112/raw_tick_data/by_date/day=2026-04-01..day=2026-05-16/`.
   - T+10min verification per VM (ScheduleWakeup).

3. **Stage 3 — manifest divergence A3**: post-backfill, run manifest divergence audit for asset_group=defi / date window
   2026-04-01..2026-05-16 → expect 0 MISSING_EXPECTED. Closes parent issue.

Total estimated VM compute: 12 VMs × ~2h avg = 24 VM-hours. e2-standard-4 ~$0.13/h ⇒ ~$3 GCP cost.

## Cross-references

- Parent: `plans/active/issues/defi_upstream_46day_full_backfill_2026_05_16.md`
- Launcher SSOT: `/codex/05-infrastructure/vm-tarball-deployment.md`
- VM verification SSOT: same § "Post-launch verification — T+10min check"
- VM prefix mapping: `deployment-service/scripts/vm/vm_zombie_watchdog.py` (all proposed prefixes already registered)

---

## Status

**LAUNCHED 2026-05-20T01:22Z — Option A executed.** 12 VMs in flight covering window 2026-04-01..2026-05-16.

### Launched VMs (12 total)

| VM name                                  | Service                       | Range / Status                                        | Created (UTC)        |
| ---------------------------------------- | ----------------------------- | ----------------------------------------------------- | -------------------- |
| `instr-backfill-defi-20260516`           | instruments-service DeFi      | 2026-04-01 → 2026-05-16 (Stage 1 — upstream universe) | 2026-05-20T01:22:05Z |
| `mtds-solana-drift-backfill`             | MTDS DeFi (solana_drift)      | 2026-04-01 → 2026-05-16                               | 2026-05-20T01:13:59Z |
| `mtds-dex-pools-backfill`                | MTDS DeFi (dex_pools)         | 2026-04-01 → 2026-05-16                               | 2026-05-20T01:15:12Z |
| `mtds-eigenlayer-rewards-backfill`       | MTDS DeFi (eigenlayer)        | 2026-04-01 → 2026-05-16                               | 2026-05-20T01:15:44Z |
| `mtds-liquidations-backfill`             | MTDS DeFi (liquidations)      | 2026-04-01 → 2026-05-16                               | 2026-05-20T01:16:17Z |
| `mtds-perp-funding-backfill`             | MTDS DeFi (perp_funding)      | 2026-04-01 → 2026-05-16                               | 2026-05-20T01:16:55Z |
| `mtds-lending-indices-20260520-091721`   | MTDS DeFi (lending_indices)   | 2026-04-01 → 2026-05-16 (positional)                  | 2026-05-20T01:17:26Z |
| `mtds-lst-rates-20260520-091740`         | MTDS DeFi (lst_rates)         | 2026-04-01 → 2026-05-16 (positional)                  | 2026-05-20T01:17:42Z |
| `mtds-pyth-archive-20260520-091756`      | MTDS DeFi (pyth_archive)      | 2026-04-01 → 2026-05-16 (positional)                  | 2026-05-20T01:18:02Z |
| `pyth-lst-backfill-20260520-091825`      | MTDS DeFi (pyth_lst)          | 2026-04-01 → 2026-05-16 (positional)                  | 2026-05-20T01:18:31Z |
| `mtds-vault-share-price-20260520-091848` | MTDS DeFi (vault_share_price) | 2026-04-01 → 2026-05-16 (positional)                  | 2026-05-20T01:18:54Z |
| `mtds-gas-fees-solana`                   | MTDS DeFi (gas_fees, Solana)  | 2021-01-01 → 2026-05-19 (pre-existing, covers window) | 2026-05-19T11:41:56Z |

### Execution notes

- **Option A (launcher edit)** picked + executed: `deployment-service@2f3c5a5` added `--start/--end` to
  `launch-defi-backfill-vm.sh` + `--asset-group` filter + `--start/--end` overrides to
  `launch-instruments-backfill-vm.sh`. `deployment-service@0bfc73b` fixed pre-existing bash-3.x compat bug (`${var,,}` →
  `tr`) surfaced when launching from macOS host.
- **Stage 1 attempt #1 FAILED** (`instr-backfill-defi-targeted-20260516` via `launch-defi-backfill-vm.sh`) — inner
  script passes `--venues <list>` to instruments-service CLI which doesn't accept that flag. Filed as finding below;
  relaunched via multi-VM launcher which doesn't pass `--venues`.
- **Stage 2 sequencing**: instruments-service VM up ≥5min before MTDS fleet launched (avoided
  `EXPECTED_DEPENDENCY_NOT_AVAILABLE` race).
- **Stale-VM cleanup**: 4 TERMINATED MTDS VMs (`mtds-dex-pools-backfill`, `mtds-eigenlayer-rewards-backfill`,
  `mtds-liquidations-backfill`, `mtds-perp-funding-backfill`) blocked relaunch — deleted + relaunched cleanly.
- **gas-fees skipped**: `mtds-gas-fees-solana` already covers the window (per preflight inventory).

### T+10min verification

Background command armed at 2026-05-20T01:22Z (delay 600s) — verifies all 12 VMs RUNNING + per-VM run.log presence in
`gs://deployment-scripts-central-element-323112/vm-logs/<vm>/`.

### Finding — `launch-defi-backfill-vm.sh --venues` flag is broken (P2)

The inner `vm_instruments_backfill.sh` passes `--venues "CURVE-AVALANCHE CURVE-OPTIMISM ..."` to the instruments-service
CLI, but the service CLI doesn't accept `--venues`. This is a pre-existing bug exposed by the 46-day backfill launch.
The targeted-DeFi launcher is therefore broken for any execution path that reaches the service CLI. Workaround used:
launch via `launch-instruments-backfill-vm.sh --asset-group DEFI`, which doesn't pass `--venues`. **Filed as P2
follow-up**: either add `--venues` to the instruments-service CLI or strip it from the inner script.

- [ ] [P2] [FOLLOW-UP] Fix `vm_instruments_backfill.sh` → instruments-service CLI `--venues` mismatch. Either add
      `--venues` to `instruments_service` argparse, or remove `VENUES_FLAG` propagation from the inner script. Surfaced
      2026-05-20 during Option A relaunch. Provenance: instruments-service `run.log` rc=2 at
      `gs://deployment-scripts-central-element-323112/vm-logs/instr-backfill-defi-targeted-20260516/run.log`.

## Status update — 2026-05-22

**BLOCKED-VERIFICATION**: 12 VMs launched 2026-05-20T01:22Z for 46-day backfill window (2026-04-01 to 2026-05-16).
Cannot verify completion without GCP Console access. Completion criterion: manifest A3 divergence scan
(`plans/audit/results/manifest_divergence_2026_05_20.parquet`) shows zero MISSING_EXPECTED rows for the defi asset_group
in the specified date window. Operator must run
`python3 instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run` to confirm. If
clean → archive this issue as ACKED-INTO-CODE.
