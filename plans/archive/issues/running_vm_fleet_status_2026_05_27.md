---
title: Running VM Fleet Status & Kill/Keep Decision Matrix
created: 2026-05-27
source:
  - gcloud compute instances list (RUNNING)
  - gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log (last 400KB tails)
  - per-VM SSH (process state, CPU, local /tmp/vm-exec-*.log)
  - serial-port-output (boot-hung / network-wedged VMs)
resolved: 2026-06-07
priority: P2
status: RESOLVED
parent_epic: orchestrator_master
estimate_calibrated_ai_days: 0.2
estimate_class: infra
---

> ## ✅ ARCHIVED 2026-06-07 — BLOCKED-CREDENTIALS: operator declined Tardis (decision FINAL) + non-Tardis residuals all tracked
>
> Per the issue-doc-lifecycle SSOT, an issue blocked by a MADE operator decision with no actionable todos archives
> (ACKED-OUT-OF-SCOPE). The original banner said "do NOT archive until the Tardis-blocked items are resolved" — but the
> operator has **decided NOT to activate Tardis (final, won't-do)**, so those CeFi-paid-history items are
> `BLOCKED-CREDENTIALS` with a final operator decision, not pending work. The kill/keep decision matrix is **executed**
> (per the harsh 2026-06-01 status banner — all "kill" VMs terminated, keep set confirmed). Every non-Tardis residual
> has a live home, so nothing is dropped on archival:
>
> - **Tardis decision (P3 OPERATOR)** → `plans/active/issues/fleet_audit_triad_deferred_followups_2026_06_01.md`
>   (explicitly tracks "Tardis paid key intentionally NOT activated" + cites this doc).
> - **OKX-FUTURES symbol fix + backfill re-run** → done + tracked in `plans/epics/mtds_mdps_master.md` § "Fleet
>   data-fetch dispatch" (instruments-service@35a745ef; operational backfill follow-up noted there).
> - **SchemaContract registration for `odds_movement_15m`/`odds_snapshot_15m` (§F data-loss)** → tracked in
>   `plans/active/mdps_backfill_phase3_2026_05_22.md` + `plans/epics/predictions_master.md`.
> - **VM wheel-cache `gsutil -m cp` boot-hang (§C — GCS-helper-rule violation)** → MIGRATED to
>   `plans/epics/infrastructure_master.md` § "P3 — backlog" (deployment-service).
> - **Log-archive durability / 14-day-TTL crons** → `fleet_audit_triad_deferred_followups_2026_06_01.md`
>   (operator-deferred).
>
> No codex `SSOTs:` section; no new durable contract.

# Running VM Fleet Status — 2026-05-27 ~07:35 UTC

> **✅ OKX symbol-mapping FIXED 2026-06-02 (slot 7) — instruments-service@`35a745ef`.** The HTTP-400 OKX-FUTURES bug (§
> B below) is resolved: `_TARDIS_VENUE_EXCHANGES` (IS `reference_data/router.py`) had no OKX entries → discovery used
> the `okex` (spot) default → `BTC-USDT`; added `okx-futures→okex-futures` (+ swap/spot), live-validated vs the free
> `/exchanges/okex-futures` endpoint. Operational follow-up tracked in `mtds_mdps_master` (re-run OKX backfill next
> window). **Tardis-paid-key-dependent CeFi-history items REMAIN `BLOCKED-CREDENTIALS`** (operator won't activate) —
> this issue stays open for those; do NOT archive until the Tardis-blocked items are resolved/operator-acked.

> **🟦 OPERATOR DECISION LEDGER — 2026-06-01 (Ikenna, recorded slot-1).** Confirms + scopes for **slot 7**: **Tardis
> paid key stays NOT activated** (operator won't) → all Tardis-dependent CeFi-history items remain `BLOCKED-CREDENTIALS`
> with their ping intact — slot 7 does NOT unblock them. The **OKX symbol-mapping fix is independent of the key** → slot
> 7 ships it. Remaining venv fixes (sports-scheduler `instruments_service`, vm-zombie-watchdog
> `unified_trading_library`) are quick + actionable.

> **🔄 STATUS 2026-06-01 (harsh) — matrix almost fully settled.** Tardis renewal: operator chose NOT to activate (won't
> do). All "kill" VMs (8 zero-data CeFi + 4 boot-hung/crashed + prediction-2026 + us-backfill + qg-snapshot) are now
> TERMINATED. "Keep running" set confirmed alive. **"Keep-but-fix" trio resolved/triaged:**
>
> - ✅ **footystats-fwd** — root cause was NOT the launcher (that was lowercased @9ded013); it was
>   `orchestrator._get_instruments_bucket` re-uppercasing asset_group into the now-strict-lowercase
>   `resolve_bucket_name` (regressed when Option B shipped 2026-05-30). Fixed: **instruments-service@b5ffa65** (+5
>   regression tests). **VERIFIED 2026-06-01**: tarball rebuilt + manual relaunch `footystats-fwd-20260601-110002`
>   exited **rc=0**, polled today→+14, discovered fixtures (1/4/5/1 on 06-12..06-15), no `Unknown asset_group` error,
>   clean self-delete. ✅
> - ⚠️ **sports-scheduler** — venv/module error gone; now logs `0 upcoming fixtures within 48h` — likely genuine (verify
>   once footystats forward data flows again), not a crash.
> - ⚠️ **vm-zombie-watchdog** — running in `--dry-run`; no readable run.log at expected path — confirm it's actually
>   emitting before trusting it as the fleet janitor.
>
> Only the 2 ⚠️ verification items remain; the kill/keep decisions are all executed.

> **Decision doc.** Precise per-VM numbers from actual logs (not guesswork) so an operator can decide keep/kill.
> **Nothing has been killed.** Logs are already backed up (see § Log Backup) so any kill is safe. Project
> `central-element-323112`, all VMs zone `asia-northeast1-c`. **25 VMs RUNNING.**

## Executive summary

| Bucket                            | Count | State                                                                                                                          |
| --------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------ |
| ✅ Producing good data            | **5** | okx-2025 (partial/free-only), mdps-prediction-2025, mdps-sports-2022, mdps-sports-2023, mtds-dex-swaps-backfill                |
| 🟢 Healthy infra (keep)           | **1** | alerting-quietness                                                                                                             |
| 🔴 Running but producing ZERO     | **8** | okx-2020/21/22/23/24, binance-spot-2021, coinbase-2020, upbit-2025                                                             |
| 🟠 Boot-hung (never started work) | **3** | bybit-2024, hyperliquid-2025, kraken-2024                                                                                      |
| 🟠 Crashed / wedged / stalled     | **4** | deribit-2021 (OOM+unresponsive), prediction-2026 (network-wedged), sports-2025 (error-spinning), us-backfill (done, GCE stuck) |
| 🟠 Broken loop (alive, useless)   | **3** | sports-scheduler, vm-zombie-watchdog, footystats-fwd                                                                           |
| ⚪ Idle leftover                  | **1** | qg-snapshot                                                                                                                    |

**Two root causes dominate the CeFi failures:**

1. **Tardis API key is EXPIRED** (`code 11: "The provided API key is expired"`). Only ONE key exists (3 secret names,
   all identical, all expired, `[]` entitlements). Paid historical dates → **HTTP 401**. Only Tardis _free_ data
   (1st-of-month + recent days, which skips auth) succeeds — that's the only reason okx-2025 produces anything.
2. **Wrong okx-futures symbol IDs** → **HTTP 400** ("Invalid 'symbol' param"). This is the _numerically dominant_ error
   on OKX VMs (~1,100–1,350/window vs ~90–134 401s) and is independent of the key — it will keep failing even after key
   renewal.

**Cost signal:** ~**10× `e2-highmem-16` + 2× `e2-highmem-8`** are running while producing **zero** data ≈ **~$10/hr
(~$240/day)** wasted (rough on-demand asia-northeast1 estimate).

---

## Full per-VM table (exact numbers)

Counts are from the **last 400 KB** of each central log unless noted. "succ" = `streaming success` / POLARS aggregations
/ parquet writes. Time ≈ 07:35 UTC.

| #   | VM                      | machine    | role / producing                                      | proc               | CPU% | succ                      | free | 401     | 400      | other errs                 | last activity                | issue / verdict                                                                                       |
| --- | ----------------------- | ---------- | ----------------------------------------------------- | ------------------ | ---- | ------------------------- | ---- | ------- | -------- | -------------------------- | ---------------------------- | ----------------------------------------------------------------------------------------------------- |
| 1   | cefi-okx-futures-2020   | highmem-16 | OKX-FUTURES download → cefi bucket                    | alive              | 9.7  | **0**                     | 0    | 89      | **1350** | 36×503                     | 07:31 (400)                  | ZERO — bad symbols (400) + expired key (401)                                                          |
| 2   | cefi-okx-futures-2021   | highmem-16 | OKX-FUTURES                                           | alive              | 22.4 | **0**                     | 0    | 100     | **1258** | 35×503                     | 07:31 (400)                  | ZERO — bad symbols + expired key                                                                      |
| 3   | cefi-okx-futures-2022   | highmem-16 | OKX-FUTURES                                           | alive              | 23.0 | **0**                     | 0    | 93      | **1286** | 38×503                     | 07:31                        | ZERO — bad symbols + expired key                                                                      |
| 4   | cefi-okx-futures-2023   | highmem-16 | OKX-FUTURES                                           | alive              | 19.3 | **0**                     | 0    | 109     | **1291** | 32×503                     | 07:31 (400)                  | ZERO — bad symbols + expired key                                                                      |
| 5   | cefi-okx-futures-2024   | highmem-16 | OKX-FUTURES                                           | alive              | 15.6 | **0**                     | 0    | 134     | 1257     | 36×503                     | 07:31 (401)                  | ZERO — expired key + bad symbols                                                                      |
| 6   | cefi-okx-futures-2025   | highmem-16 | OKX-FUTURES                                           | alive              | 30.2 | **23**                    | 232  | 97      | 1146     | 26×503                     | 07:10 (succ)                 | PARTIAL — only free dates; paid → 401                                                                 |
| 7   | cefi-binance-spot-2021  | highmem-16 | BINANCE spot                                          | alive (PID7957)    | 103  | **0**                     | 0    | **270** | 0        | —                          | 07:27                        | ZERO — expired key (pure 401)                                                                         |
| 8   | cefi-coinbase-spot-2020 | highmem-16 | COINBASE spot                                         | alive (PID7977)    | 103  | **0**                     | 0    | 168     | 168      | 1                          | 07:32                        | ZERO — expired key + bad symbols                                                                      |
| 9   | cefi-upbit-2025         | highmem-16 | UPBIT spot                                            | alive (PID7976)    | 101  | **0**                     | 0    | **352** | 0        | 2                          | 07:33                        | ZERO — expired key (pure 401)                                                                         |
| 10  | cefi-deribit-2021       | highmem-8  | DERIBIT perp                                          | SSH timeout        | —    | 4                         | 0    | 0       | 4        | —                          | **2026-05-24 22:48** (~57h)  | OOM (peak_rss 24.4 GB) + VM unresponsive; only 2021-01-01 done                                        |
| 11  | cefi-bybit-2024         | highmem-16 | BYBIT (never launched)                                | **NOT running**    | 0    | —                         | —    | —       | —        | —                          | boot stuck 05-25 01:18       | BOOT-HUNG — `gsutil -m cp wheel-cache` deadlock (PIDs 6081/6120/6123/6286)                            |
| 12  | cefi-hyperliquid-2025   | highmem-16 | HYPERLIQUID (never launched)                          | **NOT running**    | 0    | —                         | —    | —       | —        | —                          | boot stuck 05-25 01:18       | BOOT-HUNG — gsutil deadlock (PIDs 6084/6122/6125/6281)                                                |
| 13  | cefi-kraken-spot-2024   | highmem-8  | KRAKEN (never launched)                               | **NOT running**    | 0    | —                         | —    | —       | —        | —                          | boot stuck 05-25 07:25       | BOOT-HUNG — gsutil deadlock (PIDs 5841/5879/5882/6028)                                                |
| 14  | mdps-prediction-2025    | standard-8 | prediction OHLCV → prediction bucket                  | alive              | 119  | POLARS 417 / Manifest 102 | —    | —       | —        | 0                          | 07:31 (fresh)                | ✅ HEALTHY — actively writing                                                                         |
| 15  | mdps-prediction-2026    | standard-8 | prediction OHLCV                                      | **SSH hangs**      | —    | 0                         | —    | —       | —        | 479 No-SchemaContract      | **2026-05-26 10:47** (~21h)  | NETWORK-WEDGED — `169.254.169.254 unreachable` ongoing; effectively dead                              |
| 16  | mdps-sports-2022        | standard-8 | sports odds candles y2022                             | alive              | 142  | POLARS 4005               | —    | —       | —        | 7 SchemaContract skips     | 07:30 (fresh)                | ✅ HEALTHY — minor UNIBET skip data-loss                                                              |
| 17  | mdps-sports-2023        | standard-8 | sports odds candles y2023                             | alive              | 150  | POLARS 3462               | —    | —       | —        | 64 SchemaContract skips    | 00:56 log / SSH active 07:34 | ✅ HEALTHY (GCS flush lag); 64 skips = data-loss concern                                              |
| 18  | mdps-sports-2025        | standard-8 | sports odds candles y2025                             | alive              | 146  | **0** in window           | —    | —       | —        | **372 MalformedTickField** | **2026-05-26 12:43** (~19h)  | STALLED — CPU spinning, dropping ALL rows, 0 output for 19h                                           |
| 19  | mtds-dex-swaps-backfill | standard-4 | DEX swaps → defi bucket                               | alive              | 41   | 220 parquet / 92 manifest | —    | —       | —        | 0                          | 07:31 (fresh)                | ✅ HEALTHY — 64,599 rows day=2026-03-22                                                               |
| 20  | footystats-fwd          | small      | hourly sports forward-poll cron                       | idle between crons | ~0   | 0                         | —    | —       | —        | exit_code=1 ×11+           | last run 00:11 failed        | BROKEN — every hourly run fails (~60s, SIGTERM at iter=4)                                             |
| 21  | us-backfill             | standard-2 | instruments-svc Understat XG_SHOTS backfill 2019→2026 | no sshd            | —    | —                         | —    | —       | —        | Understat 404s on 2019     | **2026-05-24 00:02** (~3.3d) | DONE/stalled on 404 wall; self-terminated but GCE stuck RUNNING                                       |
| 22  | alerting-quietness      | standard-2 | `alerting_service --mode live` PubSub subscriber      | alive              | ~0   | heartbeat #719            | —    | —       | —        | 0                          | 07:25 (fresh)                | 🟢 HEALTHY — keep                                                                                     |
| 23  | sports-scheduler        | small      | `deployment_service sports-trigger` poll loop /300s   | alive              | ~0   | loop fires every 5m       | —    | —       | —        | **100% dispatch fail**     | 07:29 (fresh)                | LOOP OK but BROKEN — every dispatch `No module named instruments_service`                             |
| 24  | vm-zombie-watchdog      | small      | `watchdog.py` reaper loop /300s                       | crash-loops        | 0    | **0 scans ever**          | —    | —       | —        | **562 crashes**            | per-300s                     | BROKEN — `No module named unified_trading_library`; **fleet has had ZERO zombie protection for 2.5d** |
| 25  | qg-snapshot             | small      | quality-gates snapshot (one-shot)                     | none               | 0    | none                      | —    | —       | —        | no GCS log                 | idle 5d                      | IDLE leftover — never wrote a log                                                                     |

---

## Root-cause detail

### A. Tardis expired key (HTTP 401) — blocks ALL CeFi paid-history

- Proof: `curl` of a paid date (deribit BTC-PERPETUAL 2021-01-15) with the key →
  `401 {"code":11,"message":"The provided API key is expired."}`. A free date (2021-01-01, 1st of month) → `200`.
- One key only: secrets `tardis-api-key`, `tardis-api-key-full`, `tardis-api-key-backup` are byte-identical (`TD.l6p…`),
  all expired, all `api-key-info` → `[]`.
- **No VM authenticates.** Producers ride free data (`"Free data date detected, skipping auth"`). okx-2025's 23
  successes = 232 free-date hits. binance-2021 / upbit-2025 have 0 free dates in range → pure 401, pure zero.
- **Unblock = operator renews Tardis subscription/key.**

### B. okx-futures symbol mismatch (HTTP 400) — the dominant OKX error

- Tardis rejects e.g. `BTC-USDT` and many dated contracts:
  `"Invalid 'symbol' param provided… use the okex-futures exchanges API for allowed values"`. Valid IDs look like
  `BTC-USD-260626`, `BTC-USD_UM-260626`.
- ~1,100–1,350 per window on every OKX VM — independent of the key. **Must fix the symbol mapping** or OKX history stays
  empty even after key renewal.

### C. Boot-hang — `gsutil -m cp wheel-cache` deadlock (bybit, hyperliquid, kraken)

- Startup script's final step "Caching compiled wheels to GCS" runs
  `gsutil -m -q cp /tmp/wheel-cache/*.whl gs://…/wheels/…`. The `gsutil -m` (snap-bundled, multiprocessing) deadlocked
  on May 25 (parent gsutil PID still alive, defunct `[python3]` zombie workers), and the **startup script blocks on it**
  → `market_tick_data_service` never launches. Load 0.00, idle, no central log. Will never self-recover.
- Violates workspace rule (GCS object ops should use `gcs_copy_object` REST helper, not subprocess `gsutil`). Fix: make
  wheel-cache step non-blocking / timeout-guarded / drop `-m`.

### D. Crashed / wedged

- **deribit-2021**: OOM — `peak_rss=24,414 MB`; completed only 2021-01-01 (4 streams, 3.45M rows) then went silent ~57h;
  SSH times out → VM unresponsive. Needs reduced batch size on relaunch.
- **prediction-2026**: serial console shows continuous `dial tcp 169.254.169.254:80: connect: network is unreachable`
  (guest-agent exhausted 100 retries) — NIC/metadata stack dead → can't reach GCS, SSH hangs. Needs `reset` or
  delete+relaunch.
- **sports-2025**: 146% CPU but 372 `MalformedTickField` errors (`bm_minutes_to_kickoff`/`h2h_columns` dropping ALL
  rows), 0 successful aggregation for ~19h — spinning, producing nothing.
- **us-backfill**: hit Understat 404 wall on 2019 leagues, self-terminated 3.3d ago, but GCE stuck RUNNING (shutdown
  signal never delivered).

### E. Broken-but-alive loops

- **vm-zombie-watchdog**: 562 `ModuleNotFoundError: unified_trading_library` crashes — UTL never installed in its venv →
  has **never run a single reap scan**. The fleet's zombie protection is OFF.
- **sports-scheduler**: poll loop healthy but 100% dispatches fail `No module named instruments_service` (missing pkg in
  venv).
- **footystats-fwd**: 11+ consecutive hourly `DEPLOYMENT_FAILED` (exit 1 at iter=4).

### F. Silent data-loss on otherwise-healthy VMs (worth a code fix, not a kill)

- **Sports `No SchemaContract registered`** for derived `odds_movement_15m`/`odds_snapshot_15m` on venues like
  MATCHBOOK/UNIBET → those instruments skipped (`recovery=alert`). Exact counts: sports-2022 = 7, sports-2023 = 64,
  prediction-2026 = 479. Fix: register contracts in
  `unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY`.
- **Tradfi `SCHEMA_VALIDATION_FAILED`** (1.15M rejects) — already fixed in code 2026-05-26 (session-grid); the 5 tradfi
  VMs on the old code were deleted earlier today; reprocess fresh.

---

## Log backup (done — kill is now safe)

- Durable archive bucket created (no expiry): **`gs://vm-logs-archive-central-element-323112`**.
  - The existing stream `gs://deployment-scripts-central-element-323112/vm-logs/` has a **14-day auto-delete lifecycle**
    and **no log at all** for boot-hung VMs — hence the dedicated archive.
- Snapshot `snapshot_20260527_1300/` holds **44 files**: 19 `run.log` (server-side GCS copy, incl. multi-GB sports
  logs) + **25 `serial-console.txt`** (the only surviving evidence for the 3 boot-hung VMs + watchdog + qg-snapshot,
  which have no run.log).
- **Recommendation:** for an ongoing solution, either (a) extend the archive with a daily `gcloud storage rsync` cron of
  `vm-logs/`, or (b) drop the 14-day delete rule on the source prefix. Both are non-destructive follow-ups.

---

## Recommended decision matrix (NOT yet executed)

| Action                                 | VMs                                                                                                           | Why                                                                |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| 🔑 **Operator: renew Tardis key**      | (unblocks all CeFi)                                                                                           | Single expired key blocks every paid-history download              |
| 🧹 **Kill now (zero data, big spend)** | okx-2020/21/22/23/24, binance-spot-2021, coinbase-2020, upbit-2025 (8× highmem-16)                            | Producing 0; will stay 0 until key renewed + symbols fixed. ~$8/hr |
| 🧹 **Kill (boot-hung/crashed)**        | bybit-2024, hyperliquid-2025, kraken-2024, deribit-2021                                                       | Never started / OOM-dead; ~$3.6/hr                                 |
| 🔄 **Reset or kill**                   | prediction-2026                                                                                               | Network-wedged; unrecoverable in place                             |
| 🧹 **Kill (done/idle)**                | us-backfill, qg-snapshot                                                                                      | Finished / never did anything                                      |
| 🩹 **Keep but FIX**                    | sports-2025 (MalformedTickField), sports-scheduler (venv), vm-zombie-watchdog (venv), footystats-fwd (exit 1) | Alive but broken — code/venv fix, not a kill                       |
| ✅ **Keep running**                    | mdps-prediction-2025, mdps-sports-2022, mdps-sports-2023, mtds-dex-swaps-backfill, alerting-quietness         | Healthy, producing / serving                                       |

> okx-2025 is a judgment call: it IS producing (free dates only). Keep if free-tier 2025 coverage is wanted; otherwise
> it's the same highmem-16 spend for partial data.
