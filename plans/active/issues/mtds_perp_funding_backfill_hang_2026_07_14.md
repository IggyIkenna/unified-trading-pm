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
    plans/active/mtds_retry_safe_default_audit_2026_07_14.md,
  ]
created: 2026-07-14
assigned_vm: NA
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
- [x] [BACKEND] P0. **Defensive guard (ships regardless of the endpoint-research answer below)**: in
      `_fetch_kalshi_perp_funding_for_ticker`, do not retry non-retryable HTTP statuses (404 and anything else outside
      `_RETRYABLE`) — fail fast on the first attempt instead of burning `_MAX_RETRIES` backoff cycles. In
      `_collect_kalshi_perp`, add a sanity cap on the tickers list returned by `_fetch_kalshi_perp_market_tickers` (e.g.
      warn + truncate or fail honestly if len(tickers) > ~100 — a real curated perp-contract list is ~13 tickers) so a
      broken ticker-discovery query can never again cause multi-hour-to-multi-day churn. Add a regression test pinning
      both behaviors. Repo: `market-tick-data-service`. — ✅ market-tick-data-service@5a163d02 (2026-07-14, slot-8):
      non-retryable statuses (e.g. 404) now fail fast in `_fetch_kalshi_perp_funding_for_ticker` instead of retrying;
      `_collect_kalshi_perp` raises `ValueError` (honest `attempted_failed`) when ticker-discovery returns >100 tickers.
      Two regression tests added (`test_non_retryable_status_fails_fast`, `test_excessive_ticker_count_raises`). Full
      `quality-gates.sh` green.
- [x] [BACKEND/RESEARCH] P1. **Endpoint research (needs operator input)**: determine whether Kalshi's crypto
      perpetual-futures product (BTC-PERP/ETH-PERP/SOL-PERP/DOGE-PERP/~9 others per the module docstring) is reachable
      via a documented public endpoint at all — `category=Crypto` and `series_ticker=KXBTCPERP` on
      `api.elections.kalshi.com` both came up empty/irrelevant during this session's repro. If a real endpoint exists
      (different host, different query params, or requires auth), rewire `_fetch_kalshi_perp_market_tickers` to it. If
      it does not exist / requires credentials the workspace doesn't have, this is a `BLOCKED-CREDENTIALS` /
      `BLOCKED-OPERATOR-DECISION` case per the workspace's "external data always available" rule — build/keep the
      scaffold, flag status accordingly, do not silently descope. Repo: `market-tick-data-service`. — ✅ RESOLVED
      2026-07-14 (slot-9): the product IS reachable via a documented public endpoint — it is a SEPARATE margin/perps
      REST API (`docs.kalshi.com/margin`, `perps_openapi.yaml`), not a `category` filter on the prediction-markets host.
      Confirmed live: `GET https://external-api.kalshi.com/trade-api/v2/margin/markets` returns the real curated perp
      list (`KXBTCPERP`, `KXETHPERP`, `KXDOGEPERP`, `KXBCHPERP`, `KXDOTPERP`, …), no auth required; funding rates via
      `GET /margin/funding_rates/historical?ticker=&start_ts=&end_ts=` (Unix seconds, server-side windowed, no
      pagination needed for either endpoint). Rewired `_fetch_kalshi_perp_market_tickers` +
      `_fetch_kalshi_perp_funding_for_ticker` to the real host/paths/field names (`market_ticker`/`funding_time` replace
      the old `ticker`/`timestamp` guesses), rebased on top of the P0 defensive-guard commit
      (market-tick-data-service@5a163d02) so both fixes compose — non-retryable-status fail-fast and the ticker-count
      sanity cap are preserved. Also corrected the `KALSHI_PERP` entry in the UAC endpoint registry (was pointing at the
      prediction-markets host). 18/18 unit tests green (2 new endpoint-shape assertions), full `quality-gates.sh` green
      both repos. market-tick-data-service@56efdd7d, unified-api-contracts@ea68ef46.
- [x] [INFRA] P2. Once the P0 defensive guard (and ideally the endpoint fix) ship, relaunch
      `mtds-perp-funding-backfill --start 2026-05-29 --end 2026-07-14` (manifest-gated, skips already-captured dates)
      and verify it progresses past 2026-05-29 without hanging/churning (T+10min real-progress check, not just liveness)
      before resuming `mvp_backfill_defi_onchain_v10-002`'s G2 verification for perp_funding. Repo:
      `deployment-service`. — ✅ deployment-service (2026-07-14, slot-3): confirmed the then-running VM was still stuck
      at 2026-05-28 (89min+ silent) on the STALE pre-fix tarball (`mtds-code.manifest.json` pinned `ecd3a4d4`, predates
      `5a163d02`). Republished core tarballs (`create-code-tarballs.sh`) at MTDS `8d6b5644` (P0 fix only), deleted the
      hung VM, relaunched `launch-mtds-perp-funding-backfill-vm.sh --start 2026-05-29 --end 2026-07-14`. That run
      progressed cleanly past 2026-05-29 to full completion (`Batch complete: 47 results`, exit_code=0, clean
      self-delete) in ~18min real time — `kalshi_perp` fails FAST via the P0 sanity-cap guard instead of
      hanging/churning, confirmed on live infra. Mid-run, the endpoint-fix todo above landed on LDR
      (market-tick-data-service@56efdd7d + unified-api-contracts@ea68ef46), so that first completed run only recorded
      honest `attempted_failed` for kalshi_perp (pre-fix ticker-discovery code). Re-pulled, republished tarballs at MTDS
      `56efdd7d` (P0 fix + endpoint fix composed), relaunched the SAME range once more: also completed cleanly
      (`Batch complete: 47 results`, exit_code=0) and this time wrote REAL `kalshi_perp` funding-rate data (e.g.
      39/39/26 rows for 2026-07-12/13/14 to
      `gs://market-data-tick-defi-prd-central-element-323112/.../venue=KALSHI_PERP/...`) instead of honest-failure
      records — both the hang fix and the endpoint fix verified working end-to-end on live infra.
      `mvp_backfill_defi_onchain_v10-002`'s G2 gate for perp_funding is unblocked.
- [x] [SCRIPT] P3. Grep other DeFi/CeFi venue collectors for retry loops that retry non-retryable HTTP statuses (the
      same "any `ClientError` gets retried regardless of status" bug pattern found here) — this may recur wherever a
      similar generic-except retry loop exists. Repo: `market-tick-data-service`. — ✅ DONE 2026-07-14 (slot-14).
      **Confirmed 3 live instances of the exact same bug class**, plus a much broader systemic version: 1.
      `market_interface/adapters/onchain/glassnode.py::_get` (retry loop at line 182) — catches
      `(aiohttp.ClientError, asyncio.TimeoutError)` from `resp.raise_for_status()`, then decides retry-vs-fail via
      `classify_venue_error("GLASSNODE", type(exc).__name__)`. `GLASSNODE` has **zero entries** in
      `unified_api_contracts`'s `VENUE_ERROR_MAP`, so `classification` is always `None`, which falls back to
      `retry_safe = True` (line 191) — i.e. **every** `ClientResponseError` (a permanent 404/400/403 included) is
      retried up to `_MAX_RETRIES`, identical in kind to the Kalshi bug (bounded here to a few backoff cycles, not a
      catastrophic churn, but still wasted retries on permanent errors). 2.
      `market_interface/adapters/onchain/helius_solana.py::_rpc_call` (retry loop at line 158) — same
      `classify_venue_error("HELIUS", ...)` fallback-to-`True` bug; `HELIUS` is also **unregistered** in
      `VENUE_ERROR_MAP`. 3. `market_interface/adapters/onchain/helius_solana.py::get_enhanced_transactions` (retry loop
      at line 325) — **worse than 1/2**: no status check _at all_ before retry — `resp.raise_for_status()` on any
      non-200/429 status is caught generically and retried unconditionally up to `_MAX_RETRIES` regardless of whether
      the status is permanent (404/400/403) or transient (5xx). Note: this method currently has **zero callers** in the
      repo (dead code, not wired into any pipeline) — real-world blast radius is latent, not active, but the bug is real
      and would bite the moment it's wired up. 4. **Broader systemic pattern (not individually verified site-by-site —
      flagged for a dedicated audit, see new todo below)**: the exact fallback idiom
      `classification.retry_safe if classification is not None else True` appears at **~60 call sites across ~50 adapter
      files** (`market_interface/adapters/{defi,cefi,tradfi,sports,        onchain_perps,prediction,onchain}/*.py`, via
      `grep -rn "classification.retry_safe if classification is not        None else True"`). Spot-checked
      `onchain_perps/hyperliquid_adapter.py:419` — there the pattern is **only** logging metadata inside a
      `log_event(..., details={...})` block immediately followed by `raise` (does NOT gate a live retry decision at that
      call site), so NOT every hit is a confirmed active bug like 1-3 above — each site needs individual verification of
      whether `retry_safe` actually gates a retry loop (bug) or is pure observability (not a bug, though still a
      confusing default). **A safer `else False` convention already exists elsewhere in this same codebase** —
      `market_interface/adapters/defi/utils.py:80`, `market_interface/adapters/prediction/kalshi_adapter.py:403`,
      `cli/handlers/_defi_manifest.py:698`, and `market_interface/adapters/prediction/polymarket_adapter.py:510` all
      default unclassified errors to `retry_safe = False` (fail fast, don't blindly retry unknowns) — this is the
      correct/safe convention and should become the standard, not the ~60-site `else True` default.
- [x] [BACKEND] P1. **Fix the 2 confirmed live-loop instances** from the grep above: in
      `market_interface/adapters/onchain/glassnode.py::_get` and
      `market_interface/adapters/onchain/helius_solana.py::_rpc_call`, do not treat an unregistered venue in
      `VENUE_ERROR_MAP` as `retry_safe=True` by default — either register `GLASSNODE`/`HELIUS` in
      `unified_api_contracts`'s `VENUE_ERROR_MAP` with real per-status entries, or (simpler, no cross-repo change)
      branch on `exc.status` directly when `exc` is `aiohttp.ClientResponseError` (retry only on 429/5xx, fail fast
      otherwise) before ever consulting `classify_venue_error`. Also fix `helius_solana.py::get_enhanced_transactions`'s
      retry loop (line 325) to add the same status check even though it has no current callers (latent bug, cheap to fix
      now). Add regression tests pinning the fixed behavior (mirror `test_non_retryable_status_fails_fast` from the
      Kalshi fix, `market-tick-data-service@5a163d02`). Repo: `market-tick-data-service`. — ✅
      market-tick-data-service@b8218f8a (2026-07-14, slot-4): both `_get` and `_rpc_call` (plus
      `get_enhanced_transactions`, which had no status check at all) now branch on `exc.status` via a shared
      `_handle_response_error` helper in each module — retry only on 429/5xx, fail fast on everything else — before ever
      consulting `classify_venue_error`. Two regression tests added per adapter (`test_non_retryable_status_fails_fast`,
      mirroring the Kalshi fix). Full `quality-gates.sh` green (611s, host under heavy multi-slot contention; extended
      `PYRIGHT_TIMEOUT=400` used to ride out a transient basedpyright timeout — no code-side issue).
- [x] [BACKEND] P3. **Audit-scope**: individually verify each of the ~60
      `classification.retry_safe if     classification is not None else True` call sites found by
      `grep -rn "classification.retry_safe if classification is not None else True" market_tick_data_service/` —
      classify each as (a) gates a live retry loop → same bug class, fix like the P1 todo above, or (b) pure `log_event`
      observability metadata before an unconditional `raise` → not a functional bug, but consider standardizing to the
      safer `else False` convention (already used in `defi/utils.py`, `prediction/kalshi_adapter.py`,
      `cli/handlers/_defi_manifest.py`, `prediction/polymarket_adapter.py:510`) for consistency and to stop the pattern
      from silently becoming a live bug if someone later wires `retry_safe` into a retry decision at one of these sites.
      This is a genuinely audit-scope task (many files) — size it as its own plan rather than folding into this issue
      doc's remaining todos. Repo: `market-tick-data-service`. — ✅ DONE 2026-07-14 (slot-8): read all 70 grep hits
      (with ±8 lines context) across the 37 files. **Classification result: 2 of 70 sites gate a live retry loop
      (category a)** — `onchain/glassnode.py:191` and `onchain/helius_solana.py:167`, both already identified by the
      preceding P1-scoping todo and covered by the still-open `[BACKEND] P1` todo directly above (left untouched here to
      avoid colliding with that in-flight fix). **The other 68 sites across 35 files are category (b)** — every one is
      `classification = classify_venue_error(...)` →
      `log_event("ADAPTER_FETCH_FAILED", details={...,     "retry_safe": classification.retry_safe if classification is not None else True})`
      → an immediately-following unconditional `raise` / `raise CanonicalError(...)` / `raise exc` (a handful of tradfi
      adapters — e.g. `fear_greed_adapter.py`, `baker_hughes_adapter.py`, `eia_adapter.py`, `cftc_cot_adapter.py`,
      `databento_symbology.py` — log-and-continue with no raise at all). `retry_safe` is never read back or consulted
      for a retry decision at any of these 68 sites — confirmed functionally inert, matching the
      `hyperliquid_adapter.py:419` spot-check from the prior todo, generalized to the full set. **Fix shipped**:
      standardized all 68 to the safer `else False` convention per the recommendation, matching the existing
      `defi/utils.py` / `prediction/kalshi_adapter.py` / `cli/handlers/_defi_manifest.py` /
      `prediction/polymarket_adapter.py:510` precedent — zero functional/behavioral change (raise is unconditional at
      every site) but removes the latent "silently becomes a live bug if someone later wires retry_safe into a retry
      decision" risk the prior todo flagged. Full `quality-gates.sh` green (5473 passed, 16 skipped).
      market-tick-data-service@f82f29c1. **Follow-up (2026-07-14, dispatched P1/P3 agent)**: the convention is now
      pinned by its own plan — `plans/active/mtds_retry_safe_default_audit_2026_07_14.md` (QG lint banning the
      `else True` idiom, decision on the 2 residual non-status transient-path sites in glassnode/helius, codex SSOT
      update to `shard-level-failure-isolation.md`, issue-doc closeout).

## Update — 2026-07-14 (independent corroboration of the P2 relaunch, concurrent session)

Dispatched to execute this doc's [INFRA] P2 todo. On arrival the todo was already flipped `[x]` and pushed
(`unified-trading-pm@5a448b524`, slot-3) — HEAD ancestor-or-equal of `origin/live-defi-rollout` in this clone, synced by
the slot-cron ff-pull mid-session. Rather than re-do the work, independently re-verified the live infra myself (both
sessions were racing the same `mtds-perp-funding-backfill` VM name/GCS log path in real time, so my own checks are a
genuine independent confirmation, not a re-read of slot-3's writeup):

- **Old hung VM disposition**: `gcloud compute operations list --filter="targetLink~mtds-perp-funding-backfill"` shows
  the 16:07:56Z-launched hung VM was `delete`d at **2026-07-14T17:58:00Z** by `ikenna@odum-research.com` (~37min after
  this doc's last-observed-hang check at 17:21:44Z) — a deliberate human/operator-attributed delete, not a self-delete
  or preemption. Confirms item 1 of the dispatch ("stop old VM if still churning") was already done before this session
  started.
- **Tarball freshness at each relaunch**: confirmed via `gsutil cat .../mtds-code.manifest.json` +
  `.../unified-api-contracts-code.manifest.json` that the CURRENTLY published tarballs pin `commit_sha` exactly at
  `56efdd7da517b525c7ad7feda77d06263fc1550a` (MTDS) / `ea68ef46ac7a011af6f3d25b63c89ac38440dcf7` (UAC), both fix
  commits, republished at `2026-07-14T18:13:0x-14Z`. The first relaunch attempt (insert `17:59:11Z`, ~14min BEFORE that
  republish) ran on the P0-only tarball and correctly produced honest `attempted_failed` (ticker-discovery >100 sanity
  cap) for every `kalshi_perp` date — no churn, but no real data either, matching slot-3's writeup. The second relaunch
  (insert `18:23:22Z`, AFTER the republish) is the one that actually exercises the endpoint fix.
- **T+10 real-progress verify on the post-republish relaunch** (VM created 18:23:22Z, so T+10 = 18:33:22Z — this run
  actually finished well before that): `run.log` shows `kalshi_perp: wrote <N> funding rate rows for <date>` for **all
  47/47 dates** in the `2026-05-29`→`2026-07-14` range (e.g. 12 rows 2026-06-06, 39 rows 2026-07-13, 26 rows 2026-07-14)
  against the real margin API host, **zero** `ticker-discovery returned ... exceeding the sanity cap` churn lines
  anywhere in the full log (`grep -c` = 0), `Batch complete: 47 results collected` at `18:29:09Z` (~6min wall time, not
  18min — this was a warm per-VM manifest shard from the prior run so most non-kalshi/non-polymarket work was already
  cached), `[vm-exec] command exited rc=0`, clean self-delete. `polymarket_perp` continues to correctly fail honest
  (`SOURCE_UNREACHABLE`, pre-existing unrelated DNS NXDOMAIN issue, not in scope). Confirms `attempted_failed` rows from
  the first (pre-endpoint-fix) relaunch are NOT skip-worthy per `ManifestFreshnessCache.is_now_skip_worthy`
  (`unified_trading_library/manifest_freshness.py:256-274` — only `captured`/`empty_confirmed`/`EXPECTED_*` are
  skip-worthy; `attempted_failed` always retries), so the second relaunch correctly re-attempted every date rather than
  skip-gating on the first run's honest failures.
- **DRIFT resume-walker parts count** (dispatch item 4, cheap fleet check):
  `mtds-drift-sig-walker-resume-20260714-134435` parts count
  (`gsutil ls gs://market-data-tick-defi-prd-central-element-323112/_index/drift_v2_sig_index_parts/ | wc -l`) was 8,798
  at 17:45Z (per dispatch reference) → **9,549 at 18:49:13Z** → **+751 parts / 64.2min ≈ 11.7 parts/min (~702
  parts/hour)**. Walker target is `--back-to 2025-07-01`; `oldest=` date reached 2025-10-30 as of 18:48:19Z (from a
  session-start `oldest=2025-12-23` at 13:58:22Z — 54 calendar-days of history covered in ~4h50m of wall time ≈ 11.2
  days/hour). Remaining floor distance 2025-10-30→2025-07-01 ≈ 121 days → **extrapolated ~10.8h more** to reach the
  `--back-to` floor at the observed date-progress rate. Sibling gap walker (`mtds-drift-sig-walker-gap-20260714-134501`)
  already reached ITS floor (`2025-01-15`) and self-deleted cleanly at 17:35:21Z
  (`Walk complete: 229625000 new sigs ... across 2297 new parts`, exit_code=0) — not part of this rate calc.

**Net effect**: no code/infra action needed from this session — the P2 todo's actual work (stop old VM, relaunch onto
fresh fix-composed code, T+10 real-progress verify) is done and independently corroborated on live infra by two
concurrent sessions. `mvp_backfill_defi_onchain_v10-002`'s G2 gate for `perp_funding` is unblocked on the
`kalshi_perp`-hang axis; DRIFT's multi-day sig-walker drain remains the other tracked blocker (~10.8h ETA per the
extrapolation above).

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
