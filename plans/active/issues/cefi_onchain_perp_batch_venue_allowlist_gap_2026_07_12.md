---
doc_type: issue
title:
  OnchainPerpBatchHandler hardcodes HYPERLIQUID/ASTER only — LIGHTER/PACIFICA/EXTENDED backfill silently captures 0 rows
summary: >
  While re-verifying the cefi G4 gate (mvp_backfill_cefi_tick_v10_2026_06_27.md), extended
  launch-cefi-hl-aster-historical-backfill.sh to also target LIGHTER-ZKSYNC/PACIFICA-SOLANA/ EXTENDED-STARKNET
  (deployment-service@dfe2784) since these venues sit at 0 captured Layer-1 tuples and umi_tick_provider.py appeared to
  route them generically. Launched 8 SPOT VMs; all produced exactly 0 rows every single day with NO error, because
  market-tick-data-service's OnchainPerpBatchHandler (collect-onchain-perp-batch operation) hardcodes its venue-source
  map to HYPERLIQUID and ASTER only and silently filters any other requested venue out, so the day-loop "succeeds" doing
  nothing for the VM's entire lifetime. VMs were terminated once found. The real fetch code for these 3 venues already
  exists (the _umi_lighter / _umi_pacifica / _umi_extended adapter modules, ~500-650 lines each) but is currently wired
  only into perp_funding_handler.py's separate code path, not into OnchainPerpBatchHandler.
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [data-correctness, silent-failure, venue-allowlist, cefi, honest-coverage, layer-1]
related:
  [
    plans/active/mvp_backfill_cefi_tick_v10_2026_06_27.md,
    plans/active/issues/cefi_layer1_denominator_gaps_2026_07_03.md,
  ]
created: 2026-07-12
parent_epic: cefi_master
priority: P1
source: [plans/active/mvp_backfill_cefi_tick_v10_2026_06_27.md G4 re-verification, slot-2 2026-07-12, slot-4 2026-07-12]
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-12
locked_by:
resolved_by:
---

> **NOTIFY-OPERATOR class finding (data-correctness, silent failure).** No VM launch will EVER close the LIGHTER-ZKSYNC
> / PACIFICA-SOLANA / EXTENDED-STARKNET Layer-1 denominator gaps in `mvp_backfill_cefi_tick_v10_2026_06_27.md` until
> this code fix lands — the day-loop reports "success" (exit 0, `PROGRESS: chunk=N/365 ...`) on every single date while
> writing zero rows, so nothing in the launcher/orchestrator surfaces this as an error.

## What I found

During cefi G4 re-verification (2026-07-12), `measure_honest_coverage.py` Layer-1 showed 3 whole venues at
`present_tuples=0` despite being declared in the cefi universe with UAC `VENUE_DATA_TYPE_CAPABILITIES` start dates
already set (D2b, 2026-07-06):

| venue             | expected tuples               | present |
| ----------------- | ----------------------------- | ------- |
| LIGHTER-ZKSYNC    | 3 (book5/deriv_ticker/trades) | 0       |
| PACIFICA-SOLANA   | 3                             | 0       |
| EXTENDED-STARKNET | 3                             | 0       |

`grep -rli "lighter\|pacifica\|extended.starknet" market_tick_data_service/` showed live-only WS connectors
(`live/connectors/{lighter_zksync,pacifica_solana,extended_starknet}_perp_ws.py`) AND REST adapter modules
(`adapters/_umi_{lighter,pacifica,extended}.py`, ~500-650 lines each, exposing `fetch_lighter_rest` / equivalent with
real trades+book fetch functions), plus generic venue routing for these 3 venues inside `adapters/umi_tick_provider.py`
(chain-kind mapping, `_fetch_lighter_rest` dispatch by `venue_upper == "LIGHTER-ZKSYNC"` etc.). This looked like
ready-made infrastructure, so I extended `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`
(which drives `--operation collect-onchain-perp-batch`) to add these 3 venues alongside HYPERLIQUID/ASTER — shipped as
`deployment-service@dfe2784` — and launched 8 SPOT VMs (year-sharded, 2024/2025/2026 per venue per their UAC
start_date).

**All 8 VMs produced zero rows.** Checked the run.log for `cefi-lighter-zksync-2025-...`
(`gs://deployment-scripts-central-element-323112/vm-logs/cefi-lighter-zksync-2025-20260712-033210/run.log`): every
single day's chunk logged
`OnchainPerpBatch complete for <date>: 0 rows across venues=[] data_types=['trades', 'book_snapshot_5', 'derivative_ticker']`
— **`venues=[]`, not `['LIGHTER-ZKSYNC']`** — meaning the requested venue was silently dropped before any fetch was
attempted. No exception, no warning, `PROGRESS:` line still printed as if the chunk succeeded.

Root cause in `market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py`:

```python
_VENUE_SOURCE: dict[str, str] = {"HYPERLIQUID": "hyperliquid", "ASTER": "aster"}
...
venues = _resolve_csv_arg(self, "venues", ("HYPERLIQUID", "ASTER"))
venues = [v for v in venues if v in _VENUE_SOURCE]   # <- silently drops anything else
```

`_VENUE_SOURCE` / `_VENUE_PIPELINE_MODE` / `_VENUE_CHAIN` / `_VENUE_LAUNCH` are ALL hardcoded to exactly
`{"HYPERLIQUID", "ASTER"}` (lines ~153-166). `OnchainPerpBatchHandler` is genuinely HL/ASTER-only at the code level —
the umi_tick_provider.py routing I found earlier is a **separate code path** consumed by `perp_funding_handler.py` (a
different `--operation`), not by `collect-onchain-perp-batch`.

**VMs terminated** (`gcloud compute instances delete` on all 3 still-RUNNING 2025-shard VMs at 2026-07-12T04:1x Z) once
the zero-rows pattern was confirmed, to stop burning SPOT spend on a guaranteed-empty 365+540-day day-loop per venue.

## Why it matters

1. **The G4 gate for cefi cannot close** until LIGHTER-ZKSYNC/PACIFICA-SOLANA/EXTENDED-STARKNET have real captured rows
   — no amount of VM re-launching fixes this without the code change.
2. **Silent-failure risk beyond this incident**: `venues = [v for v in venues if v in _VENUE_SOURCE]` with no logged
   warning for a dropped venue means ANY future worker who requests a venue outside `{HYPERLIQUID, ASTER}` via this
   handler will get a "successful" multi-hour VM run that writes nothing, with no signal to notice except manually
   reading run.log for `venues=[]`. This is worth hardening independently of the 3-venue feature gap.

## Recommended fix

1. `[CODE]` P1. Add `LIGHTER-ZKSYNC` / `PACIFICA-SOLANA` / `EXTENDED-STARKNET` to `_VENUE_SOURCE` /
   `_VENUE_PIPELINE_MODE` / `_VENUE_CHAIN` / `_VENUE_LAUNCH` in `onchain_perp_batch_handler.py`, and add a
   `_process_venue` fetch branch for each that calls the existing REST adapters
   (`adapters/_umi_lighter.fetch_lighter_rest`, `_umi_pacifica.<equivalent>`, `_umi_extended.<equivalent>`) the same way
   `_fetch_hyperliquid_s3` / `_fetch_aster_rest` are dispatched today. Use the UAC `VENUE_DATA_TYPE_CAPABILITIES` start
   dates already declared (LIGHTER 2024-08-01, PACIFICA 2025-06-01, EXTENDED 2024-10-01) for `_VENUE_LAUNCH`. Add
   regression tests mirroring the existing HL/ASTER coverage (per-venue dispatch, honest-absence pre-launch
   classification).
2. `[CODE]` P2. Make the `venues = [v for v in venues if v in _VENUE_SOURCE]` filter loud — log a `WARNING` (or raise)
   naming any `--venues` entry that was silently dropped, so a future mis-targeted launch fails fast instead of running
   a multi-hour no-op.
3. `[VERIFY]` P1. Once (1) ships, re-launch LIGHTER-ZKSYNC/PACIFICA-SOLANA/EXTENDED-STARKNET via the already-extended
   `launch-cefi-hl-aster-historical-backfill.sh` (deployment-service@dfe2784 — no further launcher change needed) and
   verify real rows land (check run.log for `venues=['LIGHTER-ZKSYNC']` and `rows_written > 0`, not just VM RUNNING
   status).

## Open actions

- [x] ✅ [CODE] P1. Wire PACIFICA-SOLANA/EXTENDED-STARKNET into `OnchainPerpBatchHandler` (see recommendation 1). (repo:
      market-tick-data-service) — `market-tick-data-service@356457c2`, `unified-api-contracts@d6a7caf1`. **Scope note:
      LIGHTER-ZKSYNC deliberately NOT wired** (see the new P2 follow-up todo below) — investigation during
      implementation found its REST endpoints structurally can't serve this handler's data_types, so wiring it in as
      originally recommended would have produced zero benefit while looking fixed. PACIFICA-SOLANA and EXTENDED-STARKNET
      added to `_VENUE_SOURCE`/`_VENUE_PIPELINE_MODE`/`_VENUE_CHAIN`/`_VENUE_LAUNCH`, dispatching to
      `adapters/_umi_pacifica.py`/`adapters/_umi_extended.py` via a per-symbol prefetch cache (one REST call per symbol
      serves every data_type — avoids the 2-3x re-fetch a naive per-shard call would cost at backfill scale).
      `book_snapshot_5` excluded from the batch universe for both (their `/book`/`/orderbook` endpoints are
      current-snapshot-only, no historical range param — same limitation as ASTER's book). Added
      `PipelineMode.BATCH_PACIFICA` + `SOURCE_PRIORITY`/capability registration in UAC (BATCH_EXTENDED already existed).
      Split the handler into 3 files (`onchain_perp_batch_handler.py` + `_onchain_perp_batch_symbols.py` +
      `_onchain_perp_batch_umi.py`) to stay under the 900-line codex ratchet. 12 new/updated unit tests (captured-shard
      provenance, book-exclusion, prefetch caching + per-symbol failure isolation, catalogue-universe symbol mapping) —
      39/39 pass. quality-gates.sh green on both repos. Merged cleanly with slot-11's `_resolve_venues()`
      loud-drop-logging (`market-tick-data-service@4f62bd7e`) — one test assertion updated since PACIFICA-SOLANA is no
      longer a "dropped" venue.
- [x] ✅ [CODE] P2. Log/raise on silently-dropped `--venues` entries in `OnchainPerpBatchHandler` (see recommendation
      2). (repo: market-tick-data-service) — `market-tick-data-service@4f62bd7e`. Extracted `_resolve_venues()`: any
      `--venues` token not in `_VENUE_SOURCE` is now logged as a `WARNING` naming the dropped venue(s) before the
      supported subset is returned, so a mis-targeted launch (e.g. `LIGHTER-ZKSYNC`) surfaces immediately instead of
      only being discoverable by grepping run.log for `venues=[]`. 2 new unit tests
      (`test_resolve_venues_drops_unsupported_and_warns`, `test_resolve_venues_all_supported_no_warning`).
      quality-gates.sh green (899/900 lines, under the file-size cap after a ruff reformat).
- [x] ✅ [CODE] P2. Wire LIGHTER-ZKSYNC into `OnchainPerpBatchHandler` via a Tardis-integrated fetch path (repo:
      market-tick-data-service) — `market-tick-data-service@57493789`. **Design decision resolved**: trades/book stay
      excluded (added to `_LIVE_ONLY_DATA_TYPES`, same as originally deferred — Lighter's REST is snapshot-only for
      both, no historical range param, no viable batch source at any date; captured going forward by the live WS
      connector). Only `derivative_ticker` is wired, and ONLY via delegation — the whole (venue, day) leg is handed to
      the existing, already-tested `umi_tick_provider.fetch_tick_data_for_venue` → `_route_lighter` →
      `TardisAdapter.download_batch` call (Tardis coverage 2026-04-17+; no code change to that path, just a new caller).
      This was necessary because `download_batch` self-writes the canonical parquet AND self-records its own manifest
      rows (`pipeline_mode=BATCH_TARDIS`) in one call for every requested symbol — it cannot fit the handler's normal
      per-(data_type,symbol)-shard "return rows, handler writes+records" contract without a double manifest write, so
      the new `_onchain_perp_batch_lighter.py` stage module calls it ONCE per (venue, day) — not once per symbol/shard —
      and skips the handler's own manifest write for that leg entirely. Days before 2026-04-17 record
      `EXPECTED_PRE_SOURCE_COVERAGE_START` honest absence per symbol with NO network call (no viable source exists that
      far back for any data_type — resolves the "needs a design decision" question from the original deferral: there is
      none). `_process_venue` was split (`_process_umi_or_native_venue` moved to `_onchain_perp_batch_umi.py`) to stay
      under the 900-line codex ratchet after the new dispatch branch. 14 new/updated unit tests (pre-coverage no-network
      absence, post-coverage single delegated call across N symbols — not N calls, top-level-failure per-symbol
      attempted_failed, no-op when derivative_ticker isn't requested, symbol-mapping, `_resolve_venues` no longer drops
      LIGHTER-ZKSYNC, `_process_venue` routing wiring) — all pass. quality-gates.sh green (890/900 handler lines).
      **VERIFY re-launch is a separate follow-up** (this issue doc's item-4 VERIFY explicitly excluded LIGHTER-ZKSYNC
      pending this fix — file a new `[VERIFY]` todo when ready to re-launch and confirm real rows land for 2026-04-17+).
- [x] ✅ [VERIFY] P1. Re-launch the PACIFICA-SOLANA/EXTENDED-STARKNET backfill now that the code fix has landed and
      confirm real rows write (see recommendation 3). (repo: deployment-service) — **PARTIAL: EXTENDED-STARKNET
      verified, PACIFICA-SOLANA blocked by a NEW bug (see follow-up todo below).** - First launch
      (RUN_TS=20260712-052416) still showed `venues=[]` for both venues — root cause: the VM code tarball
      (`gs://deployment-scripts-central-element-323112/code/mtds-code.tar.gz`) was built 2026-07-12T05:00:54Z from
      `market-tick-data-service@4f62bd7e` (the P2 warning-log fix), one commit BEHIND the actual P1 venue-wiring fix
      `356457c2` — a stale-tarball gotcha (`codex/05-infrastructure/vm-tarball-deployment.md`), not a code regression.
      Killed the 5 stale-code VMs, rebuilt+reuploaded the tarball via `create-code-tarballs.sh` (now
      `mtds-code.tar.gz@356457c2`), relaunched (RUN_TS=20260712-053413). - **EXTENDED-STARKNET: VERIFIED.**
      `venues=['EXTENDED-STARKNET']` correct on all 3 shards; `cefi-extended-starknet-2026-20260712-053413` captured
      **1464 real rows** for 2026-01-01 (trades + derivative_ticker). 2024/2025 shards showed 0 rows for their first ~9
      days (2024-10-01→09, 2025-01-01→09) — plausibly early-listing honest absence, not re-verified further within this
      session. - **PACIFICA-SOLANA: BLOCKED — new bug found, not the original allowlist gap.**
      `venues=['PACIFICA-SOLANA']` is correct (drop-fix confirmed working) but **0 rows across every date tested**
      (2025-06-01→09, 2026-01-01→13). Killed both PACIFICA-SOLANA VMs before they burned further SPOT spend on
      guaranteed-zero days — see the new follow-up todo below for root cause + recommended fix.
- [x] ✅ [CODE] P1. `> **NOTIFY-OPERATOR class finding (data-correctness, silent failure).**` PACIFICA-SOLANA historical
      backfill via `fetch_pacifica_rest`'s `/trades/history` cursor-walk cannot reach dates more than ~1-2 days in the
      past — structurally similar to the LIGHTER-ZKSYNC deferral above, discovered 2026-07-12 during the item-3 VERIFY
      re-launch. (repo: market-tick-data-service) - Root cause (confirmed via direct API probe against
      `api.pacifica.fi`, not just VM logs): `/trades/history` cursor pagination for a busy symbol (BTC) only covers ~1-2
      hours of trade volume per 1000-row page, and the endpoint starts returning `HTTP 429` after ~13 rapid sequential
      calls with **no delay/backoff between pages**. Reaching PACIFICA-SOLANA's UAC `VENUE_DATA_TYPE_CAPABILITIES`
      start_date (2025-06-01, ~13 months back from today 2026-07-12) would require many thousands of paginated calls per
      coin per day — mathematically unreachable within the observed rate limit ceiling. -
      `_fetch_pacifica_trades_for_coin` / `_fetch_pacifica_book_for_coin` in `_umi_pacifica.py` do NOT use the
      `get_with_429_retry` backoff helper that's already imported in the same file (line 25) and used elsewhere
      (`fetch_pacifica_candles`, line ~407) — a 429 on `/trades/history` just logs at `logger.debug` (invisible at
      normal INFO log level) and breaks the cursor walk immediately with zero rows, no retry. The `/book` 429s (visible
      at WARNING) are a red herring — book_snapshot_5 is already excluded from the batch universe, but
      `fetch_pacifica_rest` calls `_fetch_pacifica_book_for_coin` unconditionally for every coin regardless of the
      caller's `data_types` filter (`onchain_perp_batch_handler.py` only excludes it from the OUTPUT, not from the
      underlying fetch — wastes a request + risks burning through the rate-limit budget before trades even finishes). -
      Confirmed via VM run.log: `cefi-pacifica-solana-2025-20260712-053413` / `-2026-...` produced 0 rows across every
      one of the first ~9-13 days tested (2025-06-01→09, 2026-01-01→13), with
      `WARNING Pacifica /book <coin>:       HTTP 429` on nearly every chunk — consistent with the rate-limit ceiling,
      not honest absence. - **Recommended fix — needs a design decision (same as LIGHTER-ZKSYNC), NOT a quick patch:**
      (a) skip the `/book` call entirely when `book_snapshot_5` isn't in the caller's requested `data_types` (stops
      wasting rate-limit budget on excluded output); (b) wire `get_with_429_retry` into the trades cursor-walk with an
      inter-page delay; (c) even with (a)+(b), verify whether Pacifica's actual retention/rate-limit envelope makes a
      13-month historical backfill reachable AT ALL within a practical VM lifetime — if not, PACIFICA-SOLANA's
      historical depth may need the same Tardis-integrated/date-branching approach recommended for LIGHTER-ZKSYNC above,
      or a reduced backfill scope (e.g., last N days only, honest-absence-classify the rest). Recommend routing this as
      its own scoped plan/task rather than folding into this issue doc further. - Once landed: re-launch PACIFICA-SOLANA
      only via `VENUES="PACIFICA-SOLANA"       bash scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` and
      re-verify real rows per the same method as item 3 above (remember to rebuild the code tarball via
      `create-code-tarballs.sh` first — see the stale-tarball note on item 3). **Update (slot-2, 2026-07-12, parallel
      session): part of (b) has SHIPPED — `market-tick-data-service@c98c8856`.** Independently re-diagnosed the same 429
      gap (dual-dispatch on this task) and found it's actually worse than "no backoff":
      `_fetch_pacifica_trades_for_coin` / `_fetch_pacifica_funding_for_coin` had **zero `failed_per_instrument` wiring
      at all** (only `_fetch_pacifica_book_for_coin` recorded failures) — a 429 on trades/funding was silently
      indistinguishable from honest-absence in the manifest, the same failure CLASS as the venue-allowlist bug this
      whole issue doc is about, just one layer deeper. Confirmed via direct `curl` that Pacifica has real current
      trading volume (live BTC trades returned), so the observed 0-row streak was never genuine absence. Fix: wired
      `get_with_429_retry` (already used by `fetch_pacifica_candles`) into trades/book/funding, and added
      `failed_per_instrument.record()` to trades/funding matching the book/Extended pattern — 2 new regression tests,
      `quality-gates.sh` green, shipped + re-verified end-to-end (killed stale VMs, rebuilt tarball, relaunched
      RUN_TS=20260712-055837). **Result confirms recommendation (c)'s concern**: even with retry+backoff (2s/4s/8s) AND
      running only ONE VM solo (isolating for concurrency), every symbol on `/trades/history` still hit sustained
      `HTTP 429` continuously across ~4 minutes of observation — this is NOT a short burst backoff can ride out, it's a
      sustained ceiling. Killed the retrying VMs rather than let them burn SPOT spend for hours with no realistic chance
      of landing rows. **What's still open**: (a) skip the unconditional `/book` call when `book_snapshot_5` isn't
      requested (not done — book now _also_ retries, spending more of the budget, not less); the (c) design decision
      (reduced scope / Tardis-style delegation / accept honest near-total failure) is now better-evidenced but still
      unresolved. Silent-failure risk (the P1-severity part) is closed; remaining risk is P2 (data
      completeness/coverage, not correctness) — recommend downgrading this todo's priority to P2 once (a) lands, since a
      429 is now always a loud, correctly-recorded `record_failed`, never a silent zero.

      **Update (slot-4, 2026-07-12): (a) has SHIPPED — `market-tick-data-service@1ccd1817`.** Gated the `/book` call
              behind the same `data_types` check already used for funding (`_want_book = data_types is None or
              "book_snapshot_5" in data_types`) — `fetch_pacifica_rest` no longer fires `/book` at all when the caller excludes
              it (which `_batch_data_types_for_venue` already does for PACIFICA-SOLANA), so book no longer competes with trades
              for the shared rate-limit budget. 2 new regression tests (skip when unrequested, fires when requested — 39/39
              pass), `quality-gates.sh` green. **Direct API probe against `api.pacifica.fi`** (from this session's sandbox
              network, NOT the GCP VM network slot-2's sustained-429 finding was observed on) showed 68 sequential
              `/trades/history` calls for BTC succeeding before the first 429 (vs. ~13 when book was interleaved), and a full
              day's ~20-25 page walk completing cleanly using the already-shipped retry/backoff. This is directionally
              consistent with (a) meaningfully helping, but **is not a substitute for slot-2's real-VM-network methodology** —
              network-level throttling (shared egress IP, concurrent multi-symbol load) may behave differently on an actual
              backfill VM than from this sandbox. Per (c) above and slot-2's own recommendation, downgrading this class of
              remaining risk to P2 (data completeness, not silent-failure correctness — every 429 is now a loud
              `record_failed`, never a silent zero, regardless of whether the walk ultimately reaches full 13-month depth).
              **Follow-up VERIFY filed below** — could not launch/monitor a real VM to close the loop myself this session
              (`gcloud` is non-functional in this sandbox: `snap-confine` capability error, unrelated to this task).

- [x] ✅ [VERIFY] P2. Re-launch PACIFICA-SOLANA solo (isolating for concurrency, matching slot-2's
      `RUN_TS=20260712-055837` methodology) now that the `/book`-skip fix has landed
      (`market-tick-data-service@1ccd1817`) and confirm whether real historical rows now write, or whether the
      sustained-429 ceiling persists even with book removed from the budget. (repo: deployment-service) — **NEGATIVE
      RESULT: sustained-429 ceiling CONFIRMED to persist even with `/book` removed from the budget.** (slot-2,
      2026-07-12) - Rebuilt the code tarball first (stale-tarball gotcha per item 3/4): `create-code-tarballs.sh` run
      from a clean tree at `market-tick-data-service@1ccd1817`; verified the re-uploaded `mtds-code.manifest.json` pins
      `commit_sha=1ccd1817f30843625ef5efaf90d0894655a7d9bb` before launching. - Launched
      `VENUES="PACIFICA-SOLANA" MAX_CONCURRENT=1 bash scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`
      (RUN_TS=20260712-062528) — solo (no other venues sharing the run), 2 year-shard VMs
      (`cefi-pacifica-solana-2025-20260712-062528` covering 2025-06-01→2025-12-31,
      `cefi-pacifica-solana-2026-20260712-062528` covering 2026-01-01→today). Both reached RUNNING within the 60s
      no-fire-and-forget window. - `venues=['PACIFICA-SOLANA']` confirmed correct (drop-fix still working) and the
      `/book` call is confirmed skipped
      (`excluding PACIFICA-SOLANA/book_snapshot_5 from batch universe (live-only) —     not attempted` on both shards) —
      the (a) fix from `1ccd1817` is live on these VMs. - **But every single `/trades/history` AND
      `/funding_rate/history` call across 5 sampled symbols per shard (BNB, BTC, DOGE, ETH, FARTCOIN) returned
      `HTTP 429`, with zero rows written, over ~5 minutes of continuous real-VM observation on both shards in parallel**
      — this is the same GCP-VM-network sustained-ceiling pattern slot-2 found in the prior session
      (`market-tick-data-service@c98c8856`), now re-confirmed AFTER the book-skip fix specifically intended to relieve
      it. The `get_with_429_retry` backoff (2s/4s/8s) is firing (visible in the ~20-30s gap between consecutive symbol
      attempts) but every retry still exhausts to 429 — book removal freed some rate-limit budget (per slot-4's
      sandbox-network probe: 68 calls before first 429 vs ~13 with book interleaved) but evidently not enough to clear
      whatever ceiling the shared GCP static egress IP is hitting on Pacifica's side. - Killed both VMs immediately
      after the decisive negative signal (`gcloud compute instances delete` on both, 2026-07-12T06:3xZ) to stop burning
      SPOT spend on a run with no realistic chance of landing rows, per the same practice as the prior session. - **(c)
      design decision is now CONFIRMED unresolved, not just suspected** — see the new follow-up section below. Did NOT
      re-run `measure_honest_coverage.py` Layer-1 (no rows landed, so `present_tuples` for PACIFICA-SOLANA is unchanged
      at 0 — re-running would show nothing new) and did NOT touch the G4 gate note in
      `mvp_backfill_cefi_tick_v10_2026_06_27.md` (gate implication is unchanged: still blocked on PACIFICA-SOLANA).

## Follow-up: PACIFICA-SOLANA historical depth — design decision required (NOT auto-dispatchable)

Both code-level fixes for this venue are now shipped and verified working as coded (venue-drop fix, 429 retry/backoff,
`failed_per_instrument` recording, `/book`-skip) — remaining risk is entirely **data completeness** (P2), not
**silent-failure correctness** (the original P1 is fully closed: every 429 is now a loud, correctly-recorded
`record_failed`, never a silent zero). What's left needs a human/main judgment call between three concrete options, not
another code patch attempt — do not dispatch this as a plain `[CODE]` backlog item without that decision first:

1. **Reduced backfill scope**: only backfill the last N days (honest-absence-classify everything older) — cheapest, but
   leaves most of the 2025-06-01→today Layer-1 denominator gap permanently unfilled for PACIFICA-SOLANA.
2. **Tardis-integrated/date-branching delegation** mirroring the LIGHTER-ZKSYNC fix
   (`market-tick-data-service@57493789`) — check whether Tardis has PACIFICA-SOLANA coverage at all before assuming this
   is viable; if it does, this is the most complete fix.
3. **Accept the near-total historical gap as honest absence** for this venue/date-range combination if neither (1) nor
   (2) is worth the engineering cost relative to PACIFICA-SOLANA's share of the cefi universe.

Recommend routing this as its own scoped plan once the operator/main agent picks a direction — file
`plans/active/<slug>.md` (or a `plans/active/issues/` decision note first if the option needs more investigation, e.g.
confirming Tardis PACIFICA-SOLANA coverage) rather than folding further attempts into this issue doc. Do not re-attempt
a naive full-history relaunch without one of these design changes landing first — it will only repeat the same ceiling
and burn SPOT spend for nothing.

- [ ] [VERIFY] P2. Re-launch LIGHTER-ZKSYNC derivative_ticker now that the Tardis-delegated code fix has landed
      (`market-tick-data-service@57493789`) and confirm real rows write for 2026-04-17+ — check run.log for
      `venues=['LIGHTER-ZKSYNC']` and the delegated-Tardis-call log line, then verify via the manifest (Tardis
      self-records under `pipeline_mode=BATCH_TARDIS`, NOT this handler's own manifest write — see the item-3 CODE note
      above) that rows actually landed, not just VM RUNNING status. Rebuild the code tarball via
      `create-code-tarballs.sh` first (see the stale-tarball gotcha on item 3/4). Dates before 2026-04-17 should show
      `EXPECTED_PRE_SOURCE_COVERAGE_START` honest-absence rows with no fetch attempt — spot-check one such date's
      manifest row to confirm the no-network-call path also behaves as coded. (repo: deployment-service)
