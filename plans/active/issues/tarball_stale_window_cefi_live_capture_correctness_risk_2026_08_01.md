---
doc_type: issue
title: >-
  code-tarball-refresh outage window (2026-07-30T13:02Z→2026-08-01T12:42Z) left MTDS's floating tarball missing several
  "100% empty live capture" bugfixes — credible data-correctness risk, needs manifest-level confirmation
summary: >-
  Todo #3 of `/plans/archive/issues/code_tarball_refresh_job_silently_failing_since_2026_07_30_2026_08_01.md` (archived
  2026-08-01, resolved) asked to audit whether any VM launched under `LC_TARBALL_FRESHNESS=warn` (default) during the
  code-tarball-refresh outage ran on materially stale code. Confirmed: `mtds-code.tar.gz`'s floating manifest was not
  successfully rebuilt between (at latest) `2026-07-30T13:02Z` and `2026-08-01T12:42:24Z` (~47.5h) — during that window,
  `market-tick-data-service@live-defi-rollout` received several commits explicitly described as fixing "100% empty live
  capture" (Binance-Futures/ASTER wire-shape, OKX-FUTURES canonical-id/channel) plus a same-day cefi perp_funding
  manifest-write data-loss regression+revert. Any VM that pulled the floating `mtds-code` tarball in that window (and
  did not separately pin `MTDS_TARBALL_SHA`) ran without these fixes. Confirmed real backfill-fleet VM activity occurred
  inside the window, but the one concrete VM I traced (`cefi-queue-heavy-binancefutu-x17`) turned out to run the Tardis
  HISTORICAL-file backfill path, not the live-WS path the fixes target — so it is likely unaffected by these SPECIFIC
  fixes. **UPDATE 2026-08-01 (todo #2 closed): CONFIRMED P0.** The manifest-level check found `ASTER book_snapshot_5` on
  the live consolidated VM (`mtds-live-cefi-consolidated-*`) 100% empty (zero `captured` rows) continuously from
  `2026-07-30` through the present moment (`2026-08-01T14:00Z`, ~1h20m after the tarball was finally rebuilt) — the fix
  never reached production because the `LONG_LIVED_LIVE` VM was never relaunched. See "## CONFIRMED — 2026-08-01
  manifest check" below for the full breakdown + the new `[INFRA] P0` relaunch todo.
status: open
nature: issue
asset_group: [cefi]
stage: [live]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [vm-tarball-deployment, data-correctness, cefi, live-capture, audit-followup]
related:
  [
    /plans/archive/issues/code_tarball_refresh_job_silently_failing_since_2026_07_30_2026_08_01.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: "2026-08-01"
author: unknown
parent_epic: infrastructure_master
priority: P0
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [code_tarball_refresh_job_silently_failing_since_2026_07_30_2026_08_01-worker]
resolved_by:
locked_by:
context_scope:
  [
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /plans/archive/issues/code_tarball_refresh_job_silently_failing_since_2026_07_30_2026_08_01.md,
    deployment-service/scripts/vm/setup-cefi-live-consolidated-vm.sh,
    market-tick-data-service/market_tick_data_service/live/connectors/aster_book_liq_ws.py,
  ]
depends_on: []
---

# code-tarball-refresh stale window — cefi live-capture correctness risk (2026-08-01)

## What I found

Working todo #3 of `/plans/archive/issues/code_tarball_refresh_job_silently_failing_since_2026_07_30_2026_08_01.md`
(archived 2026-08-01, resolved): "Audit whether any VM launched since 2026-07-30T13:02Z under
`LC_TARBALL_FRESHNESS=warn` ran on materially stale code for a repo with a real bugfix shipped in that window."

**Staleness windows established** (each tarball's `.manifest.json` `commit_sha`/`created_at`, checked 2026-08-01):

| repo (tarball)                                                                                                                               | floating tarball `created_at`                                                  | real (non-ci/deps) fix commits since 2026-07-30T13:02Z     |
| -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| `mtds-code`                                                                                                                                  | `2026-08-01T12:42:24Z` (i.e. floating for ~47.5h through the whole outage)     | ~30, several explicitly "100% empty live capture"          |
| `market-data-processing-service-code`                                                                                                        | `2026-07-31T18:17:07Z`                                                         | 8, incl. honest-absence/manifest correctness fixes         |
| `strategy-service-code`                                                                                                                      | `2026-07-30T23:48:55Z`                                                         | 5                                                          |
| `execution-service-code`                                                                                                                     | `2026-07-30T21:05:20Z`                                                         | 5                                                          |
| `ml-service-code`                                                                                                                            | `2026-07-30T21:05:17Z`                                                         | 0                                                          |
| `batch-live-reconciliation-service-code`                                                                                                     | `2026-07-27T01:31:13Z` (stale since BEFORE the outage)                         | 1, perf-only (column projection), not a correctness change |
| `unified-api-contracts-code`, `unified-trading-library-code`, `instruments-service-code`, `deployment-service-code`, `features-service-code` | all rebuilt `2026-08-01T10:00Z`–`12:42Z` (manual rebuilds, per the parent doc) | many, but the manual rebuild closed most of the window     |

**Highest-materiality MTDS commits inside the ~47.5h stale window** (all confirmed ancestors of the current,
finally-rebuilt `mtds-code` tarball SHA `b2a450e87a30`, i.e. they landed on LDR but were NOT reflected in the floating
tarball until `2026-08-01T12:42:24Z`):

- `4f244845` (2026-07-30T17:07:09Z) — "real Binance-Futures depthUpdate wire shape (b/a, not bids/asks) for
  BINANCE-FUTURES + ASTER book_snapshot_5 -- fixes 100% empty live capture"
- `8a6bbc97` (2026-07-30T22:55:39Z) — "OKX-FUTURES @LIN/@INV canonical-id marker + missing derivative_ticker channel --
  fixes 100% empty live capture"
- `fb32fb65` (2026-07-30T16:48:22Z) — revert of a SAME-DAY regression that "silently dropped every
  kalshi_perp/polymarket_perp/hyperliquid manifest write since ~14:12 UTC" (i.e. a ~2.5h internal window,
  `14:12`→`16:48 UTC` same day, where the bug WAS live before its own revert)
- `a1198300` (2026-07-31T05:41:03Z) + `699c563b` (2026-07-31T09:15:32+0100) — cefi perp_funding manifest re-stamp/race
  fixes (KALSHI_PERP/POLYMARKET_PERP canonical venue field)

**VM-launch evidence gathered** (`gs://deployment-scripts-central-element-323112/vm-logs/`, filtered to VM names
embedding `20260730`/`20260731`/`20260801`, ~1050 total launches in that date range fleet-wide):

- `cefi-queue-heavy-binancefutu-x17-20260730-193717` and `-20260801-120637` both launched AFTER the `4f244845`
  Binance-Futures fix landed (17:07:09Z on 07-30), and neither wrote a `TARBALL_PINS.json` at all (no pins recorded for
  ANY repo — fully floating), confirming they pulled whatever `mtds-code` tarball was floating at boot, which per the
  above was pre-fix. **However**, their `LAUNCH_PARAMS.json` shows `launcher: launch-cefi-sharded-backfill.sh`,
  `START_DATE: 2026-02-01`, and `PROGRESS.json` shows `last_completed_date: 2020-04-28` — this is the Tardis
  HISTORICAL-file backfill path (walking backward through history from 2026-02-01), a DIFFERENT code path than the
  live-WebSocket wire-shape parsing the `4f244845`/`8a6bbc97` fixes target. **This VM is likely NOT exposed to those
  specific fixes** — recording this as a negative finding so a follow-up doesn't re-spend time chasing it.
- **UPDATE (2026-08-01, todo #1 follow-up) — the production continuous live-capture VM IS located, and it DID restart
  inside the window.** The naming-convention gap in the original pass (b) is resolved: the launcher is
  `deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh` (startup: `setup-cefi-live-consolidated-vm.sh`),
  VM name prefix `mtds-live-cefi-consolidated-` — a SINGLE consolidated GCE VM (Pattern A tarball boot,
  `lifecycle_class=LONG_LIVED_LIVE`, `VM_SHUTDOWN_ON_COMPLETION=false`) that runs all 17 MVP CeFi websocket-streaming
  shards
  (`python -m market_tick_data_service --operation websocket-streaming --mode live --asset-group CEFI --shard-spec cefi:<VENUE>:<data_type> --mvp-mode`,
  one per venue×data_type) as background processes supervised by an in-VM bash loop that restarts individual DEAD SHARD
  PROCESSES every 60s. **That shard-level restart re-execs the SAME already-installed venv/tarball — it does NOT
  re-fetch code.** The MVP shard list (`setup-cefi-live-consolidated-vm.sh` §6) includes exactly the venues/data_types
  the stale-window fixes target: `BINANCE-FUTURES:trades`, `BINANCE-FUTURES:book_snapshot_5`,
  `OKX-FUTURES:trades/book_snapshot_5/derivative_ticker`, `ASTER:book_snapshot_5`/`liquidations`.
  (KALSHI_PERP/POLYMARKET_PERP/HYPERLIQUID `perp_funding` — the `fb32fb65` revert's venues — are NOT in this VM's shard
  list at all; that data_type is captured via a different mechanism, out of this VM's scope — narrows todo #2's manifest
  check to a separate capture path for those three.)

  **VM-level restart cadence: NONE automatic.** `lifecycle_class=LONG_LIVED_LIVE` (`vm_prefix_registry.py:1021`) is
  documented + code-enforced as "run until operator tears them down" (`heartbeat_stall_watcher.py:97,396`: "a
  live-capture producer must never be auto-killed"); the launcher is also singleton-locked (refuses a second concurrent
  launch). So the ONLY way this VM gets a fresh tarball pull is a **manual** operator delete+relaunch, or an unplanned
  crash/preemption forcing a manual relaunch — never an automated cadence.

  **Confirmed: a relaunch DID land inside the stale window.** `gcloud compute instances list` shows exactly one
  currently-RUNNING instance: `mtds-live-cefi-consolidated-20260731-211041`, `creationTimestamp 2026-07-31T21:10:49Z` —
  squarely inside `2026-07-30T13:02Z`–`2026-08-01T12:42Z`. GCS heartbeat-blob history
  (`vm-heartbeat/mtds-live-cefi-consolidated-*.txt`) shows an EARLIER incarnation,
  `mtds-live-cefi-consolidated-20260730-010147` (created `2026-07-30T01:01:47Z`, BEFORE the window opened) — so the VM
  was torn down and relaunched at some point between `07-30T01:01` and `07-31T21:10`, and that relaunch landed inside
  the window. The current instance's metadata carries no `*_TARBALL_SHA` pin and GCS has no
  `vm-logs/mtds-live-cefi-consolidated-20260731-211041/TARBALL_PINS.json` — fully floating, confirming it fetched
  whatever `mtds-code.tar.gz` was live in GCS at its `2026-07-31T21:10:49Z` boot. Per this doc's own tarball-manifest
  table, the floating tarball was NOT rebuilt between `2026-07-30T13:02Z` and `2026-08-01T12:42:24Z` — so this exact
  boot fell inside the dead zone and would have pulled the PRE-FIX tarball, missing both `4f244845`
  (BINANCE-FUTURES/ASTER, landed `2026-07-30T17:07:09Z` — before this boot) and `8a6bbc97` (OKX-FUTURES, landed
  `2026-07-30T22:55:39Z` — also before this boot). **This resolves the original "could not locate" uncertainty: the
  production live-capture host DID restart inside the window, unpinned, on exactly the affected venues** — todo #2's
  manifest check is now the confirming step, not a speculative one, and should be treated as high-urgency.

## Why it matters

- Two of the unpicked-up fixes are explicitly self-described by their own commit message as "fixes 100% empty live
  capture" for BINANCE-FUTURES/ASTER and OKX-FUTURES — **confirmed** (see updated finding above): the production
  `mtds-live-cefi-consolidated-*` VM DID restart/relaunch and pull the floating `mtds-code` tarball inside the 47.5h
  window (boot `2026-07-31T21:10:49Z`, unpinned), and its MVP shard list runs exactly these venues/data_types. Unless
  todo #2's manifest check shows otherwise, this VM would have captured ZERO rows for BINANCE-FUTURES
  trades/book_snapshot_5, OKX-FUTURES trades/book_snapshot_5/derivative_ticker, and ASTER book_snapshot_5/liquidations
  from its boot until the tarball was finally rebuilt (`2026-08-01T12:42:24Z`) or until an operator manually relaunched
  it again — silently (this is the exact same failure class root-caused in
  `defi_morpho_lending_indices_never_wired_2026_07_12.md`, the incident `lc_verify_tarball_freshness` itself was built
  to catch — but `warn` mode never blocks).
- The `fb32fb65` revert describes ACTUAL, CONFIRMED data loss ("silently dropped every kalshi_perp/polymarket_perp/
  hyperliquid manifest write") during its own ~2.5h introduction-to-revert window on 2026-07-30 — orthogonal to the
  tarball-staleness question (that damage happened regardless of any VM's tarball freshness, since it was live on LDR
  itself), but worth cross-checking manifests for that exact narrower window too.
- Per the data-pipeline-correctness HARD RULE, a credible risk like this cannot be silently closed — it needs a
  manifest-level check, not just code-archaeology, before anyone can say "no impact."

## CONFIRMED — 2026-08-01 manifest check (todo #2)

Read the single `market-data-tick-cefi-prd-{project}/_index/availability_index.parquet` object, filtered (row-group
pushdown, `columns=`+`filters=` — no whole-corpus walk) to `date` in `[2026-07-30, 2026-08-01]`, then
per-`(venue, data_type)` breakdown by `pipeline_mode`/`capture_status`/`attempted_at`. One-off script (delete-when this
doc closes): `market-tick-data-service/scripts/check_cefi_tarball_stale_window_capture_status_2026_08_01.py`.

**Venue-name trap avoided**: the manifest carries `KALSHI-PERP` (hyphen) + `KALSHI_PERP` (underscore, near-empty) +
`POLYMARKET-PERP` (hyphen — NOT `POLYMARKET_PERP` as this doc's todo originally spelled it). Confirmed the vocabulary
the writer actually emits before concluding "no rows" for the wrong spelling (the exact failure class
`/codex/05-infrastructure/vm-tarball-deployment.md`'s sibling docs warn about).

**CONFIRMED P0 — `ASTER book_snapshot_5` (`pipeline_mode=live_aster`, the `mtds-live-cefi-consolidated-*` VM):** **100%
`empty_confirmed`, ZERO `captured` rows**, every single day `2026-07-30` → `2026-07-31` → `2026-08-01` (513/513/513
rows, `instrument_count` sum = 0 on all three days) — an exact, unbroken match for commit `4f244845`'s own description
("fixes 100% empty live capture" for BINANCE-FUTURES + ASTER book_snapshot_5). **Still ongoing at check time**: the most
recent `attempted_at` on `2026-08-01` is `14:00:01Z` (~1h20m AFTER the `mtds-code` tarball was finally rebuilt at
`12:42:24Z`) and is STILL 100% `empty_confirmed` — because `lifecycle_class=LONG_LIVED_LIVE` means the running VM
(`mtds-live-cefi-consolidated-20260731-211041`, booted `2026-07-31T21:10:49Z`, unpinned) never re-fetches code on its
own; only a manual relaunch pulls the now-fixed tarball. **This is the confirmed incident this todo was written to catch
— see new todo below.**

**Partially recovered (NOT currently a confirmed zero stretch, but WAS broken during part of the window):**

- `BINANCE-FUTURES book_snapshot_5` (`live_binance`): 100% empty on `2026-07-30` (717/717 `empty_confirmed`), then
  recovered starting `2026-07-31T~22:00Z` (716/718 `captured` that day) and fully healthy on `2026-08-01` (717/717
  `captured`, `84,474` total instrument-rows as of `14:00Z`). Recovery timing does not cleanly line up with the
  tarball-freshness timeline (the tarball was still stale when captures resumed) — root cause of why BINANCE self-healed
  while ASTER did not is NOT determined by this manifest-only check (would need code-path comparison, out of this todo's
  scope); flagging the discrepancy rather than guessing.
- `OKX-FUTURES book_snapshot_5` / `derivative_ticker` (`live_okx`): 100% empty on `2026-07-30`, then PARTIAL recovery
  (only ~24% captured, 34/139 rows) on both `2026-07-31` and `2026-08-01` — still substantially degraded, not fully
  healthy, but not a clean 100%-zero stretch either.

**Separate, PRE-EXISTING findings (NOT caused by this tarball-staleness incident — both predate `2026-07-30`, filed here
for visibility per the data-pipeline-correctness HARD RULE, not to be conflated with the confirmed P0 above):**

- `OKX-FUTURES trades` (`live_okx`): 100% `empty_confirmed`/`expected_unattempted` (zero `captured`) on EVERY day
  `2026-07-30` through `2026-08-01` (still zero as of `13:52Z` today) — but also zero-or-near-zero on most days back to
  `2026-07-20` (intermittent chronic issue, not a new regression from this incident).
- `POLYMARKET-PERP perp_funding` (`batch_polymarket_perp` — a BATCH path, NOT the live-capture VM/tarball this doc is
  about): `attempted_failed` every day `2026-07-28` through `2026-07-31` (zero `captured` ever in this window). Chronic,
  predates the window, unrelated to tarball staleness.
- `KALSHI-PERP`/`HYPERLIQUID` `perp_funding`: healthy (captured daily, both batch paths) — no issue.

## Todos

- [x] ✅ [DATA] P1. Identify the actual deployment mechanism for continuous live CEFI tick capture (VM vs. long-lived
      service/Pub/Sub-fed process) — confirm whether it restarts/relaunches on any cadence, and if so, whether that
      cadence intersected `2026-07-30T13:02Z`–`2026-08-01T12:42Z`. (repo: market-tick-data-service) — **pure
      investigation, no code change needed. Confirmed via live GCE/GCS evidence, see updated "What I found" above:
      single consolidated GCE VM (`mtds-live-cefi-consolidated-*`, `LONG_LIVED_LIVE`, Pattern A tarball boot), NO
      automated restart cadence (operator-manual relaunch only, singleton-locked, never auto-killed), and the
      currently-running instance (`-20260731-211041`) booted `2026-07-31T21:10:49Z` — inside the stale window,
      unpinned.**
- [x] ✅ [DATA] P1. Check manifest `capture_status`/row-counts for `BINANCE-FUTURES`, `ASTER` (`book_snapshot_5`),
      `OKX-FUTURES` (`derivative_ticker`), and `KALSHI_PERP`/`POLYMARKET_PERP`/`HYPERLIQUID` `perp_funding` for
      `2026-07-30` through `2026-08-01`. **CONFIRMED P0**: see "## CONFIRMED — 2026-08-01 manifest check" above —
      `ASTER book_snapshot_5` is a currently-ongoing, unbroken 100%-empty stretch across the whole window on the live
      consolidated VM. (repo: market-tick-data-service)
- [x] ✅ [INFRA] P0. **DONE 2026-08-01T15:18Z, deployment-service@aa146bc verification run.** Manually relaunched
      `mtds-live-cefi-consolidated-*` — confirmed genuine stale-tarball case per the VM-delete guardrail (heartbeat
      64s-fresh = alive, not a stale/dead-VM situation; old instance `-20260731-211041` booted before the tarball fix,
      unpinned, no `TARBALL_PINS.json`), then launched the replacement via `--force` (bypasses the singleton lock; never
      deletes-first). New instance `mtds-live-cefi-consolidated-20260801-151833` booted clean (`VM SETUP     COMPLETE`,
      all 17 shards started, exit 0) and was left running ~15h alongside the old instance before this session resumed (a
      long suspension, not a stuck boot — heartbeat daemon stayed alive throughout, status field just never updates past
      "starting", a separate cosmetic bug worth a P3 note but not investigated further here). **Verified via the per-VM
      manifest shard for `2026-08-02` (today), filtered to `attempted_at > 05:00Z`: RELAUNCH SUCCEEDED for the
      tarball-staleness-affected venues** — `BINANCE-FUTURES` (book_snapshot_5 718/720 captured, trades 714/716
      captured), `HYPERLIQUID` (book_snapshot_5/derivative_ticker/trades all majority `captured`, thousands of real
      instrument-rows), `KRAKEN-FUTURES` (book_snapshot_5/derivative_ticker majority `captured`), `OKX-FUTURES`
      (book_snapshot_5/derivative_ticker partial `captured`) — all now receiving real market data, confirming the
      relaunch (and the underlying tarball fix) genuinely worked for these shards. Retired the old, now-redundant VM
      (`gcloud compute instances delete mtds-live-cefi-consolidated-20260731-211041`) once the new one was confirmed
      healthy — was double-billing ~$17/day extra + carrying zero remaining value once superseded.
      **`ASTER book_snapshot_5`/`liquidations` did NOT recover** — see the new todo below; this is now CONFIRMED as a
      separate, deeper bug, not caused by (or fixable via) the tarball-staleness incident this doc tracks. (repo:
      deployment-service)
- [x] ✅ [DATA] P0. **ROOT-CAUSED + FIXED 2026-08-02 — `ASTER book_snapshot_5`.** Confirmed root cause via a real live
      wire probe (both from an external network AND replayed with the production-scale instrument count):
      `wss://fstream.asterdex.com/stream` **silently drops an oversized combined-stream SUBSCRIBE frame** — no ack, no
      error, connection stays healthy, zero data for ANY subscribed symbol thereafter. Reproduced the exact boundary:
      163 streams (~4089 bytes JSON payload) subscribes fine; 164 streams (~4112 bytes) is silently dropped forever.
      `AsterBookWSConnector` (via the inherited `BinanceFuturesBookWSConnector._open_and_subscribe`) sends ASTER's FULL
      ~500-symbol MVP perpetual universe in **one** SUBSCRIBE frame — always past the ~4.1KB cliff — so 100% of ASTER
      book_snapshot_5 windows were empty_confirmed by design, on a WS connection that looks perfectly healthy (matches
      every observed symptom: `_in_connectivity_gap()` false, manifest writer running continuously, zero captured rows).
      Same failure class already fixed once in this codebase for Polymarket CLOB WS (`polymarket_clob_ws.py`
      `_MAX_ASSETS_PER_SUBSCRIBE` chunking) — applied the identical fix here: `AsterBookWSConnector` now overrides
      `_open_and_subscribe`/`subscribe`/`unsubscribe` to send ≤100-stream chunks (`_ASTER_MAX_STREAMS_PER_SUBSCRIBE`)
      instead of the base class's single-frame behaviour. Verified: (1) the exact 164-stream reproduction now succeeds
      after chunking, (2) all 15 pre-existing + 1 new regression unit test pass, (3) `basedpyright` clean on the touched
      files. The earlier "instrument-window flush failed ... ASTER:PERPETUAL:1000LUNC-USDT@LIN" log line is a SEPARATE,
      minor secondary issue (an exception in `_publish_boundary_event` AFTER `_record_empty_window` already succeeded —
      not the root cause; worth a P3 note, not investigated further here). The transient single Redis restart (`06:26Z`)
      remains a confirmed red herring (unrelated, ran healthy 15h before/after). (repo: market-tick-data-service,
      `market_tick_data_service/live/connectors/aster_book_liq_ws.py`) — **Shipped: market-tick-data-service@593bd425.**
- [x] ✅ [DATA] P1. **RESOLVED 2026-08-02 — `ASTER liquidations` is NOT broken; the earlier "multi-day unbroken zero
      stretch" characterization does not hold up under a direct manifest re-check.** A filtered
      `read_availability_index` read (venue=ASTER, data_type=liquidations, date≥2026-07-30, `pipeline_mode=live_aster` —
      the exact live-capture VM this doc is about) shows **15 real, non-zero-`instrument_count` `captured` rows spread
      across all 4 observed days** (2026-07-30: 2, 2026-07-31: 9, 2026-08-01: 3, 2026-08-02: 1, out of ~535-613
      attempts/day) — including events well BEFORE the `4f244845`/`8a6bbc97` book_snapshot_5 fixes even landed. This is
      exactly the shape of a genuinely low-frequency venue event being correctly captured, not a systematic capture
      failure — consistent with this todo's own reasoning that the sibling book_snapshot_5 SUBSCRIBE-batch-size bug
      (fixed in market-tick-data-service@593bd425) cannot apply here (liquidations subscribes one small all-market
      `!forceOrder@arr` stream, well under the ~4.1KB SUBSCRIBE-frame cliff that broke book_snapshot_5's ~500-symbol
      single-frame subscribe). Did NOT need to wait the planned 24-48h post-fix window — the manifest's own historical
      rows already answer the question directly (note: as of this check, `book_snapshot_5` was STILL 100% empty even on
      2026-08-02, latest `attempted_at` 11:56Z — before the `593bd425` fix landed at 12:18:25Z — confirming the live VM
      has not yet been relaunched with that fix; unrelated to this liquidations finding, which does not depend on that
      relaunch). No further live-probing or REST base-rate comparison needed. One-off verification script (reproducible;
      delete-when this doc closes):
      `market-tick-data-service/scripts/check_aster_liquidations_capture_rate_2026_08_02.py` (also removed the prior
      `check_cefi_tarball_stale_window_capture_status_2026_08_01.py`, whose own `Delete-when: after todo #2 is closed`
      condition had already fired). (repo: market-tick-data-service) — **Shipped: market-tick-data-service@b3c1122.**
- [x] ✅ [DATA] P1. **ROOT-CAUSED + FIXED 2026-08-02 — `DERIBIT derivative_ticker` (FUTURE/OPTION, 89% of DERIBIT's
      universe).** Confirmed the IS-universe-side mechanism this todo predicted, via a direct read of the real
      production `DERIBIT` `instruments.parquet` (2026-08-02, single bounded object read — not a corpus walk):
      instruments-service's live-mode DERIBIT universe writer (`ccxt_adapter.py`'s CCXT adapter, routed via
      `_build_canonical_future_key`/`_build_canonical_option_key` in `tardis/parsing.py`, per the 2026-07-18 operator
      ruling (recorded here in `tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md`) that "the quote
      is ALWAYS present — DERIBIT included") publishes FUTURE/OPTION `instrument_key` values WITH an explicit quote
      segment (e.g. `DERIBIT:FUTURE:BTC-USD@INV-20260814`, `DERIBIT:OPTION:BTC-USD@INV-20260814-50000-C` — confirmed on
      2,581 of 2,906 real rows: 73 FUTURE + 2,508 OPTION), but `deribit_ws.py`'s
      `_build_deribit_canonical_id`/`_instrument_to_deribit_name` pair dropped the quote and required a bare
      `BASE@MARKER` shape in the reverse regexes — every real FUTURE/OPTION canonical id IS actually publishes therefore
      failed to match, silently falling through to an invalid passthrough subscribe channel Deribit's WS never
      recognizes (same "healthy WS, zero data" symptom as the ASTER bug, confirmed different mechanism: id-format drift,
      not a subscribe-batch limit). PERPETUAL (the other 21 instruments) was already correct and unaffected — this is
      why the original connector-level probe on `BTC-PERPETUAL` came back clean. Fix: pass `quote_asset` through to
      `build_instrument_id` in the FUTURE/OPTION branches of `_build_deribit_canonical_id`, and make the reverse regexes
      in `_instrument_to_deribit_name` accept (and discard) an optional `-QUOTE` segment before the `@LIN`/`@INV` marker
      (the quote is always reconstructable from the marker alone — `USDC` for `@LIN`, implicit `USD` for `@INV` — so
      only the match needed fixing, not the wire-name reconstruction). Verified: all 2,581 real production FUTURE/OPTION
      instruments now round-trip correctly (canonical → Deribit wire name → canonical), 0 failures post-fix vs. 100%
      failure pre-fix; unit tests updated (both the quote-inclusive real shape and the quote-dropped legacy shape, which
      the optional regex group keeps backward-compatible); `quality-gates.sh` full green. (repo:
      market-tick-data-service) — **Shipped: market-tick-data-service@2c73a66c.**
- [x] ✅ [INFRA] P0. **DONE 2026-08-02T13:08Z, deployment-service (VM relaunch only — see the NEW P0 finding below for
      the unresolved recovery).** Confirmed genuine staleness first (heartbeat 31s-fresh = alive-not-stale; the running
      instance's `book_snapshot_5` was still 100% empty at `attempted_at=11:56:01Z`, before `593bd425` landed at
      `12:18:25Z` — confirming it never picked up the fix). Verified all 4 launcher-gated tarballs
      (`mtds-code`/`unified-api-contracts-code`/`unified-trading-library-code`/`deployment-service-code`) were freshly
      rebuilt (`mtds-code@b3c1122`, includes `593bd425` as an ancestor — confirmed via `git merge-base --is-ancestor`),
      then launched the replacement via `--force` (bypasses the singleton lock, never deletes-first):
      `mtds-live-cefi-consolidated-20260802-130832`. `lc_verify_tarball_freshness` confirmed all 4 tarballs current at
      launch time. Verified clean boot via SSH: `=== VM SETUP COMPLETE ===`, all 17 MVP shards running (`ps aux` count =
      17), ManifestWriter actively flushing. 11 of 17 shards showed real non-zero-instrument captures within ~9 min
      (BINANCE-FUTURES, HYPERLIQUID, KRAKEN-FUTURES, DERIBIT, OKX-FUTURES derivative_ticker, BYBIT-FUTURES
      derivative_ticker — 2188 real captured rows total). Retired the confirmed-stale old instance
      (`mtds-live-cefi-consolidated-20260801-151833`, still running pre-fix code) once the new one was confirmed
      healthy. **`ASTER book_snapshot_5`/`liquidations` did NOT recover on the new VM either** — see the new P0 finding
      below; this is now a SEPARATE, deeper problem than "code hadn't been deployed yet." (repo: deployment-service)
- [x] ✅ [DATA] P0. **ROOT-CAUSED + FIXED 2026-08-02 — a SEPARATE, deeper gateway limit explains why the `593bd425`
      chunking fix alone did not resolve production.** Per this todo's own request, captured the ACTUAL production
      subscribe behavior via a live wire probe against the real `wss://fstream.asterdex.com/stream` gateway (not a
      synthetic reproduction): a single ≤200-stream subscribe on one connection works cleanly (real depth5 data flows
      immediately); replaying the connector's EXACT chunked-subscribe sequence against ASTER's real 523-symbol
      production perpetual universe (from `fapi.asterdex.com/fapi/v1/exchangeInfo`) reproduces the incident exactly —
      4/6 SUBSCRIBE acks, ZERO data frames in 15s. Binary-searched the boundary live: **200 subscribed streams on one
      connection is fine; 205 gets the connection closed with WS close code `3003` / reason
      `"subscribed channels     exceeds limit"`** — an independent, PER-CONNECTION cumulative cap (matches Binance's own
      documented combined-stream "200 streams per connection" limit, which ASTER inherits byte-for-byte as a
      Binance-API-compatible venue) — separate from the ~4.1KB per-FRAME size cap `593bd425` fixed. The connector's
      chunked SUBSCRIBE frames all land on the SAME one connection, so the connection hits this 200-stream cap and gets
      closed by the gateway within moments of the ~5th/~6th frame, before any depth data can flow; the reconnect loop
      then reopens + immediately resubscribes the full universe again, re-hitting the same cap in a tight loop — a
      perfectly healthy-looking connection (no parse errors, no read exceptions, matches the reported shard-log symptom
      exactly) that never survives long enough to receive a single frame. Fix: `AsterBookWSConnector` is now a
      coordinator that shards the instrument universe across multiple `_AsterBookShard` connections (each ≤190 streams,
      headroom below the hard 200 cap), fanning their tick streams into one — `_ASTER_MAX_STREAMS_PER_SUBSCRIBE`
      (per-frame chunking) is UNCHANGED and still needed within each shard. Unit tests updated (17/17 green) + 2 new
      regression tests (per-shard frame chunking, cross-shard universe partitioning); `quality-gates.sh` full green.
      **`ASTER liquidations`'** "ZERO rows in the first 9 minutes" observation in this same todo is NOT a new finding —
      it's consistent with the sibling resolution above (a single all-market stream, genuinely ~1-9 events/day
      historically; a 9-minute window is far too short to expect one) — no separate liquidations fix needed. (repo:
      market-tick-data-service) — **Shipped: market-tick-data-service@28049156.**
- [x] ✅ [INFRA] P0. **VERIFIED 2026-08-02T14:39Z, deployment-service.** Confirmed the running old VM
      (`mtds-live-cefi-consolidated-20260802-130832`, heartbeat fresh but tarball built 13:31:18Z — `2c73a66c`, NOT
      including `28049156`, confirmed via `git merge-base --is-ancestor`) was genuinely stale, not just old-but-fine.
      Rebuilt the 4 gated core tarballs (`bash deployment-service/scripts/vm/create-code-tarballs.sh`, no scope flag =
      CORE); confirmed `mtds-code` manifest now pins `28049156` as an ancestor. `--force` relaunched (never
      deletes-first): `mtds-live-cefi-consolidated-20260802-142543`. `lc_verify_tarball_freshness` confirmed all 4
      tarballs current at launch. Verified clean boot via SSH (`=== VM SETUP COMPLETE ===`, 17/17 MVP shards running).
      Read the per-VM manifest shard directly (`_index/per_vm/mtds-live-cefi-consolidated-20260802-142543.parquet`,
      bypasses manifest-consolidator lag), filtered to `venue=ASTER, data_type=book_snapshot_5`: **501/521 rows
      `captured` (20 `empty_confirmed`), 515 distinct `instrument_id` symbols, 51,553 total captured instrument-rows,
      spread across 8 distinct flush-cycle minute-buckets from `14:29Z` to `14:39Z`** — confirms the multi-connection
      sharding fix works in production across multiple symbols and multiple flush cycles, not just the single BTC probe
      used during root-cause. Retired the confirmed-stale old instance
      (`gcloud compute instances delete mtds-live-cefi-consolidated-20260802-130832`) once the new one was verified
      healthy. (repo: deployment-service)
- [x] ✅ [DATA] P3. File a SEPARATE issue doc for the two pre-existing, unrelated chronic findings surfaced incidentally
      by this check: `OKX-FUTURES trades` intermittent zero-capture (going back to at least `2026-07-20`, live pipeline)
      and `POLYMARKET-PERP perp_funding` permanently `attempted_failed` since at least `2026-07-28` (batch pipeline).
      Neither is caused by the tarball-staleness incident this doc tracks. — unified-trading-pm@858b88eb9 (repo:
      market-tick-data-service)

## Codex SSOTs

`/codex/05-infrastructure/vm-tarball-deployment.md`, `/codex/02-data/data-pipeline-correctness-hard-rule.md`.

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (5 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

## Follow-ups

- [ ] [DATA] P3. Fix heartbeat status field that never updates past 'starting' on LONG_LIVED_LIVE VMs (cosmetic, 'worth
      a P3 note', flagged 2026-08-01).
- [ ] [DATA] P3. Investigate the 'instrument-window flush failed ASTER:PERPETUAL:1000LUNC-USDT@LIN' exception in
      _publish_boundary_event (minor, 'worth a P3 note, not investigated further', flagged 2026-08-02).

> **2026-08-06 archive-candidate audit**: Doc's own entries flag two unfixed bugs as 'worth a P3 note but not
> investigated further here' — prose-only deferrals never turned into tracked `- [ ]` todos (all incident todos
> themselves are done, but these two would evaporate on archival).
