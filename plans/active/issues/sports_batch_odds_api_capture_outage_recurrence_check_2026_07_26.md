---
doc_type: issue
title: >-
  batch_odds_api capture outage recurrence check — NOT the 2022 mechanism, but a LIVE, SEVERE, CURRENT one found and
  fixed (a future-date guard silently blocked 100% of same-day sports odds capture for ~1 month)
summary: >-
  Dispatched to check whether the confirmed 2022-09-07…2022-10-01 canonical under-capture outage (32 days / 550,062
  keys, per `mdt_legacy_canonical_row_gap_2026_07_16.md`'s SUPERSEDED banner) is still live in the current
  `batch_odds_api` capture pipeline. It is not the SAME mechanism — but a DIFFERENT, currently-live, more severe one was
  found and fixed this session. `TickDataHandler._check_early_exit()` (market-tick-data-service) gates every `process()`
  call on `hours_since_midnight(date) < 0` ("has the full day fully elapsed") REGARDLESS of asset_group, even though the
  function's own historical design comment states `"Sports/Prediction: immediate. DeFi: immediate"` (only CEFI/Tardis
  ~6h and TRADFI/Databento T+1 have genuine provider-settlement lag) — the carve-out was never implemented in code. Live
  GCP log inspection (2026-07-26) confirmed every `uts-prod-market-tick-data-service-fast-t1-recon` execution triggered
  by the production 5-minute sports-scheduler cron logs `DATA_NOT_AVAILABLE: date=2026-07-26 is in the future` and
  no-ops before `process_ticks()`/`OddsApiAdapter` are ever called — exiting 0 with ZERO manifest writes (not even
  `attempted_failed`). Manifest density (consolidated availability index, no GCS walk) confirms the
  2026-06-21…2026-07-26 window carries only 227 batch_odds_api shards / 22,298 instrument_count vs 2,042 shards /
  375,762 in the same calendar window in 2024 and 2,301 shards / 390,404 in 2025 — a ~94% collapse, not a seasonal
  pattern. The sparse activity that DID land (2026-07-16, 07-18..07-20) lines up with past-date backfill/reprocessing
  runs, which pass the old guard fine. Fix shipped this session (market-tick-data-service@410d7569):
  SPORTS/PREDICTION/DEFI now only block genuinely future dates (`date` has not started yet); CEFI/TRADFI/ALL keep the
  original strict gate. Separately traced the exact mechanism the todo asked about (`odds_api_adapter.py`'s
  per-timestamp catch-`aiohttp.ClientResponseError`-and-`continue` in `_run_league_fetch_loop`, which has no
  consecutive- failure counter) — confirmed it still exists, but a sub-agent trace found it is largely MITIGATED for the
  "false honest-absence" concern by an independent sentinel safeguard (`sentinels.py`'s
  `record_zero_rows(was_expected=True)`, driven by instruments-service's fixture catalog) that routes an
  expected-but-uncaptured shard to `attempted_failed` (retried), not silently to `empty_confirmed` — so that specific
  2022-style mechanism is judged NOT the live threat; the future-date guard is.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    sports,
    data-pipeline-correctness,
    odds-api,
    capture-outage,
    future-date-guard,
    live-bug,
    big-finding,
    manifest,
    investigation,
  ]
related: [./mdt_legacy_canonical_row_gap_2026_07_16.md, /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md item 5",
    'mdt_legacy_canonical_row_gap_2026_07_16.md Loose ends #1 ("BIG FINDING → operator + own issue doc")',
  ]
---

# batch_odds_api capture outage recurrence check — live bug found + fixed, backfill decision needed

## What I found

**Task**: determine whether the canonical `batch_odds_api` sports capture pipeline is still susceptible to the confirmed
2022-09-07…2022-10-01 outage pattern (32 days / 550,062 legacy-only keys, per
[`mdt_legacy_canonical_row_gap_2026_07_16.md`](./mdt_legacy_canonical_row_gap_2026_07_16.md)'s SUPERSEDED banner — the
ground truth this doc cites, not the doc's own since-retracted 92%/14-month headline).

### (a) Inspected the adapter/scheduler for a silent-skip mechanism

Read `market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py` end to end. Found one real
candidate: `_run_league_fetch_loop`'s per-timestamp fetch loop catches `aiohttp.ClientResponseError` and, unless the
message contains `"OUT_OF_USAGE_CREDITS"`, just logs a warning and `continue`s — no consecutive-failure counter, no
re-raise, no signal returned to the caller distinguishing "N calls failed" from "0 rows because no fixtures." A
sub-agent traced the full caller chain (`umi_tick_provider.py` → `orchestrator/__init__.py` → `venue_fetch.py` →
`sentinels.py`) and found this is **largely mitigated** for the specific 2022-style failure mode: `sentinels.py`'s
`_emit_sports_v2_sentinels` cross-checks each `(bookmaker, league, fixture)` shard against an **independent** oracle
(instruments-service's own fixture catalog, NOT derived from the Odds-API response) and routes an
expected-but-uncaptured shard to `record_zero_rows(was_expected=True)` → internally `record_failed(...)` →
`capture_status="attempted_failed"` (retried), never silently to `empty_confirmed`. This is a real, if narrower-scoped,
safeguard — its correctness depends on IS's fixture catalog being populated, which was not re-verified here. **Verdict
on this specific mechanism: exists in code, but not judged the live threat** — see the mechanism actually found below.

### (b) Measured recent (90-day) canonical density — found something much bigger

Using the consolidated availability index for `market-data-tick-sports-prd-central-element-323112`
(`unified_trading_library.manifest_writer.read_availability_index` — manifest-only, no GCS walk, per the single-walk
discipline), filtered to `pipeline_mode` containing `batch_odds_api`:

| Window (2026-06-21 … 2026-07-26, 36 days) | days w/ any row |  shards | Σ instrument_count |
| ----------------------------------------- | --------------: | ------: | -----------------: |
| **2026 (current)**                        |      **8 / 36** | **227** |         **22,298** |
| 2025 (same calendar window)               |         29 / 36 |   2,301 |            390,404 |
| 2024 (same calendar window)               |         33 / 36 |   2,042 |            375,762 |

This is **not** a seasonal/off-season pattern — both prior years show normal density in the identical calendar window.
Day-by-day detail shows a **total** gap (0 shards, not just batch_odds_api but every sports `pipeline_mode`) from
2026-06-25 through 2026-07-15 (22 days), a sparse burst on 07-16 / 07-18 / 07-19 / 07-20 (67/83/42/23 shards), then
**another total gap from 2026-07-21 through 2026-07-26 (today) — 6 consecutive days, zero rows.**

### (c) Root-caused the live gap via direct GCP log/scheduler inspection (not guesswork)

- `uts-prod-sports-scheduler-cron` (Cloud Scheduler, `*/5 * * * *`, ENABLED) **is** firing correctly and **is**
  dispatching real per-fixture triggers today, e.g.
  `Triggering Cloud Run Job for shard market-tick-data-service-odds_t1h-<fixture> ... python -m market_tick_data_service --operation download --mode batch --asset-group SPORTS --start-date 2026-07-26 --end-date 2026-07-26 --run-tag live`.
- Every one of 6+ sampled `uts-prod-market-tick-data-service-fast-t1-recon` executions from those dispatches
  (2026-07-26, ~00:35-00:41 UTC) logs, verbatim: `ERROR DATA_NOT_AVAILABLE: date=2026-07-26 is in the future` — for
  **today's own date**, not a genuine future date — then `Batch complete: 1 results collected` and
  `Container called exit(0)`. The job "succeeds" from Cloud Run's perspective; zero capture work happens; nothing is
  written to the manifest.
- Root cause: `TickDataHandler._check_early_exit()` (`market_tick_data_service/cli/handlers/tick_data_handler.py`) calls
  `_hours_since_midnight(date) < 0`, which is `(now_utc - (target_date + 1 day)).total_seconds() < 0` — **negative for
  the entire calendar day of `date`**, only turning non-negative once that day has fully elapsed (UTC). This applies
  **unconditionally to every asset_group**. Git history (`7db373809795f...`, 2026-06-11) shows the ORIGINAL comment this
  replaced explicitly said: `"Sports/Prediction: immediate. DeFi: immediate."` (only CEFI/Tardis ~6h and
  TRADFI/Databento T+1 have real provider-settlement lag) — but the code never implemented that per-asset-group
  carve-out for the hard block, only for the softer `_warn_provider_lag` warnings. **This has been live since at least
  2026-06-11** and plausibly explains the entire 2026-06-25 onward gap (the isolated 07-16..07-20 activity lines up with
  past-date backfill/reprocessing runs, which pass the old guard fine since their `date` argument is already in the past
  by the time they run).

### (d) Fixed this session

`market-tick-data-service@410d7569` (shipped to `live-defi-rollout`, QG green, 7 new/updated unit tests in
`tests/unit/test_handler.py::TestFutureDateGuard`):

- `_check_early_exit` now calls a new `_needs_full_day_elapsed(asset_groups)` helper — `True` for CEFI/TRADFI/ALL
  (unchanged strict gate: block until the day has fully elapsed), `False` for SPORTS/PREDICTION/DEFI (new: only block if
  `_is_strictly_future_date(date)`, i.e. `date` has not started yet — same-day dispatches now proceed).
- Regression tests cover: SPORTS same-day now proceeds to `process_ticks`; SPORTS strictly-future-date is still skipped;
  CEFI same-day is still skipped (pre-fix behavior preserved).

**Not yet verified**: whether the running `uts-prod-market-tick-data-service-fast-t1-recon` Cloud Run Job image has
picked up this fix — shipping to `live-defi-rollout` does not itself rebuild/redeploy the production container.
Operator/next dispatch should confirm the image was rebuilt via the standard LDR→staging/main promote + Cloud Build
pipeline and that `DATA_NOT_AVAILABLE: date=<today> is in the future` stops appearing in
`uts-prod-market-tick-data-service-fast-t1-recon` logs post-deploy.

### Blast-radius check (brief, not exhaustive)

- **Prediction**: checked `market-data-tick-pred-prd-central-element-323112` density for the trailing 10 days vs the
  prior 10 — 9/10 and 10/10 days with data respectively, volume actually higher recently (20,161 vs 3,651 rows). **Not
  affected** by this bug (or affected by a negligible margin) — its capture path evidently doesn't route same-day
  dispatches through this exact guard the same way, or requests already-past dates by design.
- **DeFi**: could not measure — `market-data-tick-defi-prd-central-element-323112`'s consolidated availability index was
  found STALE during this investigation (`ManifestConsolidatorStaleError`: blob age 2204s > 120s threshold, consolidator
  behind/down), a separate, orthogonal infra finding. Since the original design comment also said `"DeFi: immediate"`,
  DeFi's same-day capture may be similarly affected — **unverified, flagged as a follow-up todo below**, not claimed
  either way.

## Why it matters

Live sports odds capture (the pre-kickoff horizon-grid snapshots the whole point of `batch_odds_api` is to capture) has
been **silently near-zero for roughly a month** (2026-06-25 onward, with the exception of two short backfill-driven
windows), heading into and continuing through today's session (2026-07-26), for a different and more severe reason than
the historical 2022 outage this todo was scoped to check. This is a `data-pipeline-correctness-hard-rule` **big
finding**: current sports strategy/ML features consuming pre-match odds have been running on a starved feed for ~1
month, and the standard capture flow gives ZERO signal of this (job exits 0, error is logged but doesn't fail the job or
write a manifest row of any kind — not even `attempted_failed`).

## Recommended decision / next steps

1. **[OPERATOR] P0 — confirm deploy + decide on backfill.** Confirm the fix (`market-tick-data-service@410d7569`) has
   reached the production `uts-prod-market-tick-data-service-fast-t1-recon` image (check `gcloud run jobs describe`
   image digest / trigger a redeploy if the standard promote pipeline hasn't picked it up yet), then confirm the
   `DATA_NOT_AVAILABLE` error stops appearing in fresh executions. Separately: decide whether the ~1-month gap
   (2026-06-25…2026-07-25, all leagues) should be backfilled via the Odds-API historical endpoint (credits-cost /
   priority tradeoff — an operator call, not a worker one).
2. **[DATA] P1. Verify DeFi's same-day capture was/wasn't also blocked**, once
   `market-data-tick-defi-prd-central-element-323112`'s manifest consolidator is confirmed healthy (see the
   ManifestConsolidatorStaleError above — this itself may need its own issue doc if it's still stale; worker should
   check current state first, not assume it's still down). Compare a recent 10-day window against a 10-day window before
   that, same method as this doc's § (c). (repo: market-tick-data-service)
3. **[DATA] P3. Harden `odds_api_adapter.py`'s `_run_league_fetch_loop`** with an explicit consecutive-non-422-failure
   counter (defense-in-depth for the mechanism in § (a) above) — even though the independent sentinel safeguard
   currently mitigates the worst outcome, a same-session failure counter would surface the condition faster and more
   directly than relying on the sentinel's later reconciliation pass. Low priority given the existing mitigation. (repo:
   market-tick-data-service)

## Verdict (per the dispatching todo's done-when)

**Root cause found — DIFFERENT mechanism than the 2022 outage, and it IS/WAS still live**: not the
swallowed-per-timestamp-fetch-error pattern in `odds_api_adapter.py` (checked, largely mitigated by an independent
safeguard), but a future-date guard in the orchestrating CLI handler (`tick_data_handler.py`) that blocked 100% of
same-day sports odds capture, unconditionally, since at least 2026-06-11. **Fixed this session**
(`market-tick-data-service@410d7569`); deploy-confirmation and the historical-gap backfill decision are the two items
still open, both requiring operator input (see above). Operator notified per the data-pipeline-correctness-hard-rule
big-finding trigger.

## Progress Log

**2026-07-26 (slot 8, data_engineering)** — Investigation + fix executed per
`plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md` item 5. Read
`mdt_legacy_canonical_row_gap_2026_07_16.md` for the 32-day/550,062-key ground truth. Inspected `odds_api_adapter.py`;
dispatched a sub-agent to trace the full manifest-status caller chain for the swallowed-exception mechanism (found:
largely mitigated by an independent sentinel safeguard). Measured 90-day manifest density (manifest-only, no GCS walk) —
found a ~94% density collapse vs the same calendar window in 2024/2025, confirmed NOT seasonal. Live-inspected GCP Cloud
Scheduler + Cloud Run Job logs directly (`gcloud logging read` / `gcloud run jobs executions list`) — found the
scheduler firing correctly but every dispatched capture job rejecting `date=2026-07-26` as "in the future." Traced to
`TickDataHandler._check_early_exit`/`_hours_since_midnight`; git history confirmed the function's own removed comment
documented `"Sports/Prediction: immediate. DeFi: immediate"` as the intended design, never implemented. Fixed + tested +
shipped (`market-tick-data-service@410d7569`, QG green, 7 new tests). Checked Prediction (not affected); DeFi check
blocked by an unrelated stale-manifest-consolidator condition on that bucket (flagged as a follow-up, not chased further
this session). Filed this issue doc + 3 follow-up todos; notifying operator now per the big-finding trigger.
