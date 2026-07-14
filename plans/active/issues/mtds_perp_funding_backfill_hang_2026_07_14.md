---
doc_type: issue
title:
  mtds-perp-funding-backfill VM hangs silently at 2026-05-29 (kalshi_perp genesis date) — no crash, no error, zero
  progress for 53+ min
summary:
  "mtds-perp-funding-backfill (relaunched 2026-07-14T16:07:56Z per mtds_backfill_vm_startup_oom_rc137_2026_07_14's
  fix-verification todo) processed its full backfill range cleanly from 2023-11-01 through 2026-05-28, then went
  completely silent — no 'Perp funding collection complete' line, no error, no traceback, no crash — for 53+ minutes
  (confirmed via two independent checks 21.6min apart, both showing byte-identical last-progress timestamp
  2026-07-14T16:28:37Z). VM remains RUNNING with flat RESOURCE_SAMPLE heartbeats (rss~626-627MiB, cpu~0.2%) the entire
  time — alive, not crashed, just producing zero output. 2026-05-29 is the exact date kalshi_perp transitions from
  'before launch' (honest EXPECTED_PRE_VENUE_LAUNCH, cheap/instant) to its genesis date requiring a real fetch attempt —
  the log's last 'before launch' line for kalshi_perp is dated 2026-05-27, meaning the very next iteration (2026-05-29)
  is the first date kalshi_perp's collector must actually make a live call. This blocks
  mvp_backfill_defi_onchain_v10-002's G2 gate for perp_funding independent of, and in addition to, the already-tracked
  multi-day DRIFT sig-index walker drain."
status: open
nature: record
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [hang, backfill-vm, mtds, perp-funding, kalshi, defi, timeout]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md,
  ]
created: 2026-07-14
assigned_vm: planning
source: [mvp_backfill_defi_onchain_v10-002]
parent_epic: defi_master
priority: P1
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

Dispatched to `mvp_backfill_defi_onchain_v10-002` (G2 final DeFi MVP verification). Per the established cadence, checked
the DRIFT sig-index walker fleet (healthy, both walkers advancing normally — gap walker 1928→2151 parts, resume walker
8296→8538 parts over ~21.6min, zero errors). While tailing logs for the fleet, also opportunistically checked
`mtds-perp-funding-backfill` (relaunched by slot-11 at 2026-07-14T16:07:56Z per the OOM-fix verification todo in
`mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`) since it is one of the two VMs directly gating this task's
perp_funding data_type.

**Timeline of the hang**:

- VM launched 16:07:56Z (`--start 2023-11-01 --end 2026-07-14`), collecting cleanly — genuine "Perp funding collection
  complete for `<date>`: 2 records across 3 protocols" lines throughout, including honest-absence handling for
  `kalshi_perp` (pre-launch dates → `EXPECTED_PRE_VENUE_LAUNCH`) and `polymarket_perp` (DNS NXDOMAIN since 2026-06-21 →
  `attempted_failed`, correctly typed as `SOURCE_UNREACHABLE` not a silent zero).
- Last real progress line:
  **`2026-07-14 16:28:37,536 INFO Perp funding collection complete for 2026-05-28: 2 records across 3 protocols`**.
- From 16:28:37Z onward: **zero** "collection complete" / error / traceback / warning lines of any kind — only
  `RESOURCE_SAMPLE` (flat `rss=626-627MiB`, `cpu=0.0-0.4%`) and `PIPELINE_HEARTBEAT` lines, every ~30-60s, indefinitely.
- Confirmed via two independent checks: first at ~17:00Z (~32min silent), second at 17:21:44Z (~53min silent, byte
  identical last-progress timestamp both times) — this rules out a merely-slow date; the process is genuinely stuck, not
  working through a large per-date payload.
- VM status both checks: `RUNNING` (not preempted, not crashed, not self-deleted) — this is a true hang, not the rc=137
  OOM-kill pattern `mtds_backfill_vm_startup_oom_rc137_2026_07_14.md` already tracks (that issue's crashes are instant
  SIGKILLs with a clear `Killed`/`rc=137` marker; this VM shows no kill signal at all, just silence).

**Root-cause hypothesis (not yet confirmed by a live repro — no SSH access from this data_engineering craft-scoped
sandbox, same constraint noted in the sibling OOM issue doc)**: the immediately preceding log lines show
`kalshi_perp: 2026-05-26 is before launch (2026-05-29) — recording EXPECTED_PRE_VENUE_LAUNCH` and the same for
2026-05-27 — i.e. `kalshi_perp`'s launch date is **2026-05-29**, exactly the date immediately after the last
successfully processed date (2026-05-28). Every date up to and including 2026-05-28 takes the cheap, instant "before
launch" honest-absence branch for `kalshi_perp`; 2026-05-29 is the **first date that branch does not apply**, forcing
`kalshi_perp`'s collector into a real (non-honest-absence) fetch code path for the first time in this VM's entire run.
The hang starting at exactly this boundary is a strong (though not yet SSH-confirmed) signal that `kalshi_perp`'s
live-fetch path lacks a request timeout and is blocked indefinitely on a network call (or a retry/backoff loop that
never logs), analogous to `polymarket_perp`'s already-handled `SOURCE_UNREACHABLE` case but without that case's graceful
catch-and-record-failure wrapper.

Also worth noting (not the primary suspect, but present at the same moment): a `ManifestConsolidatorStaleError` fires on
essentially every date (consolidated blob age >120s threshold, same consolidator-lag class as
`defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`) but is caught gracefully (`ManifestFreshnessCache` logs
the error and "keeps previous membership set") — this does NOT appear to be the hang cause since it fired identically on
every prior date without stalling the loop; flagging only for completeness in case the two are related under different
load conditions.

## Why it matters

- Blocks `mvp_backfill_defi_onchain_v10-002`'s G2 gate for `perp_funding` **independent of** the already-tracked
  multi-day DRIFT sig-index walker drain — even once DRIFT's Helius-quota-gated backfill finishes, this VM will not
  reach `kalshi_perp`'s post-genesis dates (2026-05-29 onward, ~1.5 months short of `--end 2026-07-14`) without
  intervention.
- If the root-cause hypothesis is correct, **any other DeFi/CeFi venue with a mid-range genesis date** could trigger the
  identical silent hang the first time a backfill VM's date loop crosses that venue's launch boundary — this may not be
  `kalshi_perp`-specific or `perp_funding`-specific.
- A silent hang (VM stays `RUNNING`, heartbeats stay green, no error surfaces) is worse than a crash for operational
  visibility — nothing pages, nothing self-heals, and a naive dashboard check would read this VM as healthy indefinitely
  while it makes zero progress. Worth considering a "no data-progress for N minutes while RUNNING" liveness check at the
  deployment-observability layer, not just per-VM crash detection.

## Update — 2026-07-14 (slot-8) — CONFIRMED root cause (supersedes the missing-timeout hypothesis above)

No SSH access to the live VM was available (same constraint as noted above), so confirmation was via a **local repro
against the actual Kalshi public REST endpoints the collector calls** — `_perp_funding_kalshi_polymarket.py` issues
plain unauthenticated GETs, so the exact request shapes are reproducible without the VM. Findings:

1. **Every individual HTTP call the collector makes already has an explicit timeout and completes fast** — confirmed
   `GET /markets?category=Crypto&limit=1000` (`_fetch_kalshi_perp_market_tickers`) returns in ~0.3-1.2s/page, and
   `GET /markets/{ticker}/funding_rates` (`_fetch_kalshi_perp_funding_for_ticker`) returns a fast 404 (~0.3s) for every
   ticker probed. **The missing-timeout hypothesis is ruled out** — no individual request blocks.
2. **The real problem: `category=Crypto` on Kalshi's public `/markets` endpoint does not return the ~13 crypto perpetual
   contracts (BTC-PERP/ETH-PERP/etc.) the collector's docstring describes — it returns thousands of unrelated
   prediction-market tickers** (esports/politics/sports markets tagged `Crypto` for unrelated reasons, e.g.
   `KXMVESPORTSMULTIGAMEEXTENDED-...`). Paginating 15 pages (15,000 tickers) found **zero** tickers containing `PERP`,
   and the endpoint still had a `cursor` (more pages available) — `_fetch_kalshi_perp_market_tickers`'s loop caps at 50
   pages × 1000 = **up to 50,000 tickers**, all irrelevant. Also checked `/series?category=Crypto` (254 series, zero
   `PERP`-named) and a guessed `series_ticker=KXBTCPERP` (empty result) — **found no evidence Kalshi's public
   `api.elections.kalshi.com` host exposes a crypto-perpetuals product at all**; it may live on a different host, need
   different auth/whitelisting, or not exist yet as documented.
3. **Compounding bug**: `_fetch_kalshi_perp_funding_for_ticker`'s retry loop does not distinguish permanent failures
   from transient ones — a 404 (`not in _RETRYABLE`) still falls through to `resp.raise_for_status()` → `ClientError` →
   caught by the generic `except (aiohttp.ClientError, OSError)` → retried up to `_MAX_RETRIES` (3) with exponential
   backoff. Each irrelevant ticker therefore burns ~4 requests + ~7s of backoff sleep (~8s total) before giving up.
4. **Net effect**: iterating the (up to 50,000, confirmed ≥15,000) irrelevant tickers in batches of 5
   (`_COIN_BATCH_SIZE`) with a 1.0s inter-batch delay (`_BATCH_DELAY_SECONDS`), each ticker taking ~8s to fail via the
   retry loop above, works out to **hours-to-days of wall-clock churn, not a true infinite block** — it just presents
   identically to a hang because there is no per-ticker/per-batch progress logging (only a per-_date_ "collection
   complete" line, which never fires because the ticker loop for that date hasn't finished). This also means the
   original "add a timeout" fix (item 2 below, original text) **would not resolve this** — every call already times out
   fine; the loop is just processing an enormous irrelevant list.

**Revised recommendation**: item 2 below is superseded — the real fix needs (a) an operator/research decision on whether
Kalshi's crypto-perpetuals product is reachable at all (different host? different auth?) before more collector work is
invested, and (b) regardless of (a), a defensive fix so no future run can repeat a multi-hour churn: stop retrying
non-retryable HTTP statuses (404 is permanent, not transient) in the retry loop, and add a sanity cap on
`_fetch_kalshi_perp_market_tickers`'s result size (a real curated perp-contract list should be ~13 tickers, not
thousands) that short-circuits to an honest failure/log instead of silently proceeding into the funding-rate loop.

## Recommended decision

1. ✅ **Confirm the hang site** — DONE (see Update above): NOT a missing-timeout hang; a broken/likely-nonexistent
   ticker-discovery query causing catastrophic (thousands-to-tens-of-thousands ticker) sequential retry churn.
2. **NEEDS OPERATOR DECISION**: is Kalshi's crypto-perpetuals product actually reachable via a documented endpoint
   (different host/auth from `api.elections.kalshi.com`)? Until answered, item 2 below (the collector fix) cannot pick
   the right target query — only the defensive guard (no-retry-on-404 + ticker-count sanity cap) can ship without this
   answer.
3. **VM action** (infra-craft scope, not this session's): kill/relaunch `mtds-perp-funding-backfill` is NOT recommended
   until the defensive guard (item 2, revised) ships — otherwise a relaunch just repeats the same
   multi-hour-to-multi-day churn on 2026-05-29 onward.
4. Consider whether other venues share the same non-retryable-status-gets-retried bug pattern — worth a quick grep
   across venue collectors' retry loops once this one is fixed.

## Todos

- [x] [BACKEND] P1. Confirm the hang site: attach to (or locally repro) `kalshi_perp`'s live-fetch collector for its
      2026-05-29 genesis date; identify the blocking call (network request without timeout, retry loop, or lock wait).
      Repo: `market-tick-data-service`. — ✅ CONFIRMED 2026-07-14 (slot-8, local repro against the live Kalshi public
      API, no code changes needed to reproduce): NOT a missing-timeout hang — every individual HTTP call already times
      out and completes in <1.5s. Root cause is `_fetch_kalshi_perp_market_tickers`'s `category=Crypto` filter matching
      thousands of irrelevant non-perp tickers (confirmed ≥15,000, capped at 50,000) instead of the ~13 real perp
      contracts, combined with the retry loop retrying permanent 404s — see "Update" section above for full evidence.
- [ ] [BACKEND] P0. **Defensive guard (ships regardless of the endpoint-research answer below)**: in
      `_fetch_kalshi_perp_funding_for_ticker`, do not retry non-retryable HTTP statuses (404 and anything else outside
      `_RETRYABLE`) — fail fast on the first attempt instead of burning `_MAX_RETRIES` backoff cycles. In
      `_collect_kalshi_perp`, add a sanity cap on the tickers list returned by `_fetch_kalshi_perp_market_tickers` (e.g.
      warn + truncate or fail honestly if len(tickers) > ~100 — a real curated perp-contract list is ~13 tickers) so a
      broken ticker-discovery query can never again cause multi-hour-to-multi-day churn. Add a regression test pinning
      both behaviors. Repo: `market-tick-data-service`.
- [ ] [BACKEND/RESEARCH] P1. **Endpoint research (needs operator input)**: determine whether Kalshi's crypto
      perpetual-futures product (BTC-PERP/ETH-PERP/SOL-PERP/DOGE-PERP/~9 others per the module docstring) is reachable
      via a documented public endpoint at all — `category=Crypto` and `series_ticker=KXBTCPERP` on
      `api.elections.kalshi.com` both came up empty/irrelevant during this session's repro. If a real endpoint exists
      (different host, different query params, or requires auth), rewire `_fetch_kalshi_perp_market_tickers` to it. If
      it does not exist / requires credentials the workspace doesn't have, this is a `BLOCKED-CREDENTIALS` /
      `BLOCKED-OPERATOR-DECISION` case per the workspace's "external data always available" rule — build/keep the
      scaffold, flag status accordingly, do not silently descope. Repo: `market-tick-data-service`.
- [ ] [INFRA] P2. Once the P0 defensive guard (and ideally the endpoint fix) ship, relaunch
      `mtds-perp-funding-backfill --start 2026-05-29 --end 2026-07-14` (manifest-gated, skips already-captured dates)
      and verify it progresses past 2026-05-29 without hanging/churning (T+10min real-progress check, not just liveness)
      before resuming `mvp_backfill_defi_onchain_v10-002`'s G2 verification for perp_funding. Repo:
      `deployment-service`.
- [ ] [SCRIPT] P3. Grep other DeFi/CeFi venue collectors for retry loops that retry non-retryable HTTP statuses (the
      same "any `ClientError` gets retried regardless of status" bug pattern found here) — this may recur wherever a
      similar generic-except retry loop exists. Repo: `market-tick-data-service`.

## Evidence

- `mtds-perp-funding-backfill` full `run.log`, last progress line:
  `2026-07-14 16:28:37,536 INFO Perp funding collection complete for 2026-05-28: 2 records across 3 protocols` — no
  further progress/error/traceback lines through at least `2026-07-14T17:21:18Z` (53min+ silent), only
  `RESOURCE_SAMPLE`/`PIPELINE_HEARTBEAT` lines.
- Immediately preceding lines confirm `kalshi_perp` launch date = 2026-05-29
  (`"2026-05-26 is before launch (2026-05-29)"`, `"2026-05-27 is before launch (2026-05-29)"`).
- `gcloud compute instances describe mtds-perp-funding-backfill --zone=asia-northeast1-c` → `status: RUNNING` at both
  the ~17:00Z and 17:21:44Z checks (not preempted, not crashed).
- `gcloud compute operations list` for this instance shows no `preempted`/kill event during the hang window (checked as
  part of confirming this is not the sibling `rc=137` OOM-kill pattern).
- **2026-07-14 (slot-8) local repro** against the live public Kalshi API (`api.elections.kalshi.com/trade-api/v2`, same
  host + params `_perp_funding_kalshi_polymarket.py` uses):
  - `GET /markets?category=Crypto&limit=1000` — 15 consecutive pages fetched (15,000 tickers), all `status=active`, zero
    contain `PERP` in the ticker, `cursor` still present (more pages available; loop caps at 50 pages = 50,000).
  - `GET /markets/{ticker}/funding_rates` for a sampled ticker → `404` in ~0.34s (fast, not a hang at the request
    level).
  - `GET /series?category=Crypto&limit=1000` → 254 series, zero contain `PERP`.
  - `GET /markets?series_ticker=KXBTCPERP` (guessed real perp series ticker) → empty `markets: []`.
  - Conclusion: no evidence of a reachable crypto-perpetuals product on this host; the collector's ticker-discovery
    query returns thousands of unrelated prediction-market tickers instead.
