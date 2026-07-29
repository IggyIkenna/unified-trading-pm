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
last_updated: 2026-07-29
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

> # 🔴 BLOCKED-CREDENTIALS 2026-07-28 (slot 6) — item 1's backfill-launch todo conflicts with a same-day operator ruling elsewhere; NOT launched.
>
> This doc's item 1 todo cites an operator ruling ("Yes, do it — launch the ~1-month sports odds gap backfill,
> scope+spend approved") dated 2026-07-28. But `sports_odds_api_key_deactivated_2026_07_26.md` carries a SEPARATE
> operator ruling, ALSO dated 2026-07-28: reactivation of the `odds-api-key` Secret Manager secret is **DECLINED** ("we
> can use the odds API keys we already have for live+batch odds... do not reactivate or rotate the key"). I
> live-verified just now (via `unified-trading-sa`, direct `curl https://api.the-odds-api.com/v4/sports?apiKey=...`)
> that this exact secret — the ONLY `secret_name` hardcoded in `odds_api_adapter.py:229`, used for BOTH the live
> `/sports/{sport}/odds` endpoint AND the `/historical/sports/{sport}/odds` endpoint this backfill needs — still returns
> `error_code=DEACTIVATED_KEY`, unchanged since 2026-07-26 (matches every prior re-check through today, including that
> doc's own slot-7 entry dated 2026-07-28). I also grepped every other sports adapter
> (odds_engine/metabet/opticodds/polymarket/betfair) and the 5 other odds-adjacent GCP secrets
> (`odds-api-io-key`/`oddsjam-api-key`/`oddspapi-api-key(s)`/`opticodds-api-key`) — none are wired to any code path for
> `batch_odds_api` (corpus-wide zero code hits, per that doc's own 2026-07-27 audit). **There is no alternate
> already-working odds-api mechanism in this codebase.** Launching this backfill right now would 401 every request and
> burn VM spend for zero rows. Filed `BLK-e9c1c362` to the operator to reconcile the two same-day rulings — **not
> launching until answered.** Item 1's todo is retagged `BLOCKED-CREDENTIALS` above (on the checkbox's own line, per the
> `blocked_marker_continuation_line_not_scanned_2026_07_26.md` lesson) so `regen_backlog_from_plan.py` excludes it from
> re-dispatch until this is resolved.

> # 🟡 CORRECTED IN PART 2026-07-26 (same session, follow-up task) — the § (b) DENSITY MEASUREMENT checked the WRONG
>
> > BUCKET for the most recent week; the CODE BUG + FIX below are UNCHANGED and still correct.
>
> While working the follow-up plan item on the same pipeline
> (`sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md` todos 6/7/8), discovered that sports'
> canonical availability MANIFEST is deliberately routed to `instruments-store-sports-prd`, not
> `market-data-tick-sports-prd` (the 2026-06-07 sports-manifest-canonicalisation decision, code-enforced since
> 2026-07-13 — see `market_tick_data_service/engine/orchestrator/_manifest_bucket.py::_resolve_manifest_bucket`). **§
> (b)'s 90-day density table below reads `market-data-tick-sports-prd`, which is the architecturally non-authoritative
> bucket for sports manifest since 2026-07-13** — it correctly shows near-zero because that IS the deliberate, expected
> post-fix state, not evidence of a live capture blackout.
>
> **Re-checked against the correct bucket (`instruments-store-sports-prd`)**:
>
> - The 2026-06-27…2026-07-15 total gap (0 rows, confirmed in BOTH buckets) **is real** — independently corroborated by
>   `sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`, which found NO active scheduler/VM for
>   sports odds capture as of 2026-07-23 (a genuine dormancy, root-caused separately, not this doc's future-date-guard
>   bug).
> - **2026-07-21 through 2026-07-26 (today) is NOT a blackout** — the correct bucket shows real, growing activity:
>   captured rows 42 / 84 / 40 / 84 / 505 / 837 for 07-21..07-26 respectively (plus large `attempted_failed` /
>   `empty_confirmed` counts from 07-23 onward — the pipeline is clearly running and evaluating real fixtures, not
>   silent). Direct GCS listing confirms real parquet objects exist for every one of these dates.
> - **The actual defect this bug produces, precisely stated**: each day's manifest rows + GCS objects are written in a
>   SINGLE BATCH ~24-25h **after** the fixture date, just after UTC midnight of date+1 (measured `written_at`:
>   `date=2026-07-21` written 2026-07-22T00:57Z; `date=2026-07-22` written 2026-07-23T01:02Z; `date=2026-07-23` written
>   2026-07-24T00:53Z — a clean, consistent T+1 pattern, exactly the fingerprint of the future-date guard rejecting the
>   date all day then clearing at midnight). **The real loss is NOT total data loss — it's the entire pre-match HORIZON
>   GRID (T-24h, T-12h, T-6h, T-4h, T-2h, T-1h, T-10m, T-0) collapsing into one T+1-day-late historical re-fetch**,
>   destroying the odds-TRAJECTORY signal (CLV, drift, steam-move features) the adapter's own docstring says the 8-point
>   grid exists to capture, even though each day's data eventually arrives.
> - **DEPLOY CONFIRMED (2026-07-26, directly verified, not inferred)**: `gcloud artifacts docker images list` shows
>   `asia-northeast1-docker.pkg.dev/.../market-tick-data-service:latest` tagged `f6ea001` (built 2026-07-26T01:29:12Z),
>   a git descendant of `410d7569` (my fix); the image tagged `410d756` itself was built 2026-07-26T01:10:00Z (~18 min
>   after the fix was pushed to `live-defi-rollout` at 00:52Z — a fast auto-deploy-on-push pipeline, not a manual
>   trigger). A live execution (`uts-prod-market-tick-data-service-fast-t1-recon-cv7ch`, started 2026-07-26T01:35:57Z,
>   i.e. AFTER the `f6ea001` image became `:latest`) was directly log-inspected: 30+
>   `StreamingParquetWriter: uploaded market-data-tick-sports-prd-.../day=2026-07-26/pipeline_mode=batch_odds_api/.../ticks.parquet`
>   lines, zero `DATA_NOT_AVAILABLE` errors — **same-day capture is confirmed working in production, right now.**
>
> **Revised backfill-decision framing for the open operator item**: the ~1-month "gap" is NOT one undifferentiated
> blackout. Two distinct sub-questions: (1) the 2026-06-27…2026-07-15 true dormancy (~19 days, genuinely zero data,
> cause separate from this doc — see the linked scheduling-status doc) — a real backfill candidate if it matters for
> strategy training; (2) the 2026-07-16…2026-07-25 window, where daily coverage DOES exist but only as a single
> late/compressed snapshot instead of the intended 8-point pre-match horizon grid — recovering the LOST GRANULARITY (not
> lost days) would need historical re-fetches at the correct T-minus offsets, which the Odds-API historical endpoint can
> still serve since it takes any past timestamp. Both are now operator credits/priority calls, not worker ones, per the
> original disposition — this correction sharpens what's actually being decided.

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

> **Item 1's backfill fork RULED 2026-07-28 (operator direct answer: "Yes, do it — scope + spend approved").** This
> prose section is kept verbatim as the historical record the `## Todos` section was converted from; see that section's
> item 1 for the current retagged `[DATA] P0` status and the full backfill mandate.

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

## Todos

> Converted from the prose "Recommended decision / next steps" list above (verbatim text preserved) per
> `sports_satellite_ao_dispatch_batch6_2026_07_26.md`'s dispatch todo — `regen_backlog_from_plan.py` derives todos from
> checkboxes, and this doc previously carried none despite `assigned_vm: planning`, making its work structurally
> invisible to the backlog.

- [ ] [DATA] P0 — BLOCKED-CREDENTIALS (still true 2026-07-29 — a 2026-07-29 mechanical rephrase pass, commit
      `6edd4486a`, incorrectly stripped this line's `BLOCKED-CREDENTIALS` marker to "credential gate cleared",
      conflating the operator's LAUNCH-DECISION ruling below with the separate, still-unfixed CREDENTIAL gate — restored
      here after a fresh live re-check; see Progress Log). Confirm deploy (DONE, see banner) is unaffected by this
      correction; the backfill launch remains not executable. Deploy confirmation: DEPLOY CONFIRMED (2026-07-26,
      directly verified, not inferred) — see the dated correction banner above, image `f6ea001`/`410d756` digests + a
      log-inspected post-deploy execution with zero `DATA_NOT_AVAILABLE`. **Backfill DECISION: RULED 2026-07-28 —
      OPERATOR DIRECT ANSWER: "Yes, do it — launch the ~1-month sports odds gap backfill (scope + spend approved)."**
      Retagged from `[OPERATOR]` to `[DATA]` (decision approved) — but this is a DIFFERENT gate than the CREDENTIAL: the
      sole wired credential path (`odds-api-key` Secret Manager secret, `sports_odds_api_key_deactivated_2026_07_26.md`)
      still returns `error_code=DEACTIVATED_KEY` on direct live verification (re-confirmed 2026-07-29, this task), and
      that same doc's own 2026-07-28 operator ruling explicitly DECLINES to reactivate/rotate it, while asserting an
      alternate already-working key covers live+batch odds — no such alternate mechanism has been found wired anywhere
      in the codebase across 4+ independent audits (slot 6, slot 7, 2026-07-27 classification pass, this task). **Do NOT
      launch** until an operator names the actual working key/secret to point at (`BLK-e9c1c362` asked exactly this
      2026-07-28; no resolution has landed in this doc's corpus since). Per the reframed two-sub-question scope from the
      correction banner above, once unblocked, launch BOTH windows via the Odds-API historical endpoint, in full (no
      partial-window shortcut — per the operator's general "do not allow anything to partially complete" + "full
      backfills... DO IT" theme): 1. **The 2026-06-27…2026-07-15 total-gap window (~19 days, zero data)** — genuinely
      missing days; backfill every league's odds via the historical endpoint for this exact range. 2. **The
      2026-07-16…2026-07-25 granularity-loss window (~10 days, one late T+1 snapshot instead of the intended 8-point
      pre-match horizon grid: T-24h/T-12h/T-6h/T-4h/T-2h/T-1h/T-10m/T-0)** — re-fetch at the correct historical T-minus
      offsets for each fixture in this range to recover the lost odds-trajectory signal (CLV, drift, steam-move
      features), not just the single already-captured daily snapshot. **Done when**: both windows show full historical
      coverage in the manifest (verified via `read_capture_status_counts`/`read_availability_index`, manifest-only, no
      GCS walk) at the intended granularity, and this todo cites the launcher/dispatch evidence.
- [x] [DATA] P1. Verify DeFi's same-day capture was/wasn't also blocked, once
      `market-data-tick-defi-prd-central-element-323112`'s manifest consolidator is confirmed healthy (see the
      ManifestConsolidatorStaleError above — this itself may need its own issue doc if it's still stale; worker should
      check current state first, not assume it's still down). Compare a recent 10-day window against a 10-day window
      before that, same method as this doc's § (c). (repo: market-tick-data-service) — ✅ **Answered (2026-07-28)**:
      consolidator is HEALTHY now (a live probe read `date=2026-07-28` cleanly; the consolidated blob was itself briefly
      stale (455.6s > 120s) during the check but the reader's per-VM-shard fallback served the read honestly, per
      `manifest_consolidator_liveness_health_2026_06_01`, not a hard failure). Measured density
      (`scripts/check_defi_future_date_guard_blast_radius_2026_07_28.py`, manifest-only, no GCS walk): **Window A — 10
      days before the fix (2026-07-16..2026-07-25)**: 10/10 days with any row, Σ instrument_count=9,954,532. **Window B
      — recent 10-day window (2026-07-19..2026-07-28)**: 9/10 days with any row, Σ instrument_count=19,330,244 (higher
      volume, not lower). **Verdict: NOT AFFECTED** — both windows show near-full daily coverage; no evidence of a
      same-day capture blackout comparable to sports' pre-fix collapse. DeFi's capture path evidently does not route
      same-day dispatches through the same future-date-guard chokepoint the way sports did (or was never starved by it
      at the measured volume), consistent with the source doc's own Prediction blast-radius finding (also not affected).
- [x] [DATA] P3. Harden `odds_api_adapter.py`'s `_run_league_fetch_loop` with an explicit consecutive-non-422-failure
      counter (defense-in-depth for the mechanism in § (a) above) — even though the independent sentinel safeguard
      currently mitigates the worst outcome, a same-session failure counter would surface the condition faster and more
      directly than relying on the sentinel's later reconciliation pass. Low priority given the existing mitigation.
      (repo: market-tick-data-service) — ✅ **Shipped**: `market-tick-data-service@6f546b88` (tracks the longest streak
      of back-to-back non-422 `ClientResponseError`s per league-batch, logs a warning at streak≥3, returns the streak to
      the caller; 7 new unit tests in `tests/market_interface/unit/sports/test_odds_api_consecutive_failures.py`, QG
      green at ship time).

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

**2026-07-26 (later, same session) — CORRECTION while working the follow-up plan item on the same pipeline**
(`sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md` todos 6/7/8). Discovered § (b)'s density table
read `market-data-tick-sports-prd`, which has been the architecturally non-authoritative manifest bucket for sports
since 2026-07-13 (`_resolve_manifest_bucket()` deliberately routes sports manifest to `instruments-store-sports-prd` — a
documented 2026-06-07 decision, unrelated to this doc's bug). Re-checked against the correct bucket: the
2026-06-27…2026-07-15 dormancy is real (independently corroborated); 2026-07-21…2026-07-26 is NOT a blackout — real,
growing capture activity exists, but each day lands ~24-25h late in a single T+1 batch (measured via manifest
`written_at`), consistent with the future-date guard rejecting the date all day and clearing at midnight — collapsing
the intended 8-point pre-match horizon grid into one late historical re-fetch, not erasing the day's coverage entirely.
`date=2026-07-26` (today) shows a same-day (non-delayed) write at 01:17Z, ~25 min after the fix shipped — a strong but
indirect signal the fix already reached production (operator should still confirm via image digest, not just infer from
timing). Added a correction banner + this log entry; did not retract the core finding (the future-date guard bug and its
fix remain correct and necessary) — only the severity/framing of § (b)'s density argument for the most recent week.
Backfill decision reframed into two distinct sub-questions (true 06-27…07-15 dormancy vs 07-16…07-25
lost-granularity-not-lost-days) for the operator.

**2026-07-28 (slot 6, data_engineering)** — Dispatched item 1 (backfill launch). Read the sibling
`sports_odds_api_key_deactivated_2026_07_26.md` per the pre-task plan/issue conflict-check HARD RULE and found a
same-day operator-ruling contradiction (see banner above). Live-verified via `unified-trading-sa` (switched off the
ambiently-active `github-actions-deploy` identity, which lacked `secretmanager.versions.access`) that the `odds-api-key`
secret — the sole credential `odds_api_adapter.py` uses for both live and historical the-odds-api.com calls — still 401s
`DEACTIVATED_KEY`. Confirmed no alternate wired odds-api mechanism exists (grepped every sports adapter + all 6
odds-adjacent GCP secrets). Filed `BLK-e9c1c362` with 3 options (don't launch / launch anyway / investigate further),
recommending "don't launch." Not launching any VM or spending compute against a credential confirmed dead 2 days
running. Tagged the todo `BLOCKED-CREDENTIALS` and added this banner so the contradiction is visible before anyone else
re-dispatches this todo blind.

**2026-07-28 (slot 14, data_engineering)** — Worked `sports_satellite_ao_dispatch_batch6_2026_07_26.md`'s todo (this doc
was `assigned_vm: planning` but carried zero checkboxes, making its work invisible to `regen_backlog_from_plan.py`).
Added the `## Todos` section above, converting the 3 prose next-steps into checkboxes verbatim. Item 3 (consecutive-
non-422-failure counter) was already shipped by a prior slot session (`market-tick-data-service@6f546b88`, QG green, 7
tests) — confirmed and cited, not re-done. Item 2 (DeFi blast-radius) executed fresh: re-checked
`market-data-tick-defi-prd-central-element-323112`'s consolidator (HEALTHY now — the earlier
`ManifestConsolidatorStaleError` was transient/already resolved; a live probe read cleanly, with a brief 455.6s-stale
consolidated blob correctly recovered via the per-VM-shard fallback, not a hard failure) via
`scripts/check_defi_future_date_guard_blast_radius_2026_07_28.py` (manifest-only, no GCS walk). Measured Window A (10
days before the fix, 2026-07-16..2026-07-25): 10/10 days, Σ instrument_count=9,954,532. Window B (recent 10 days,
2026-07-19..2026-07-28): 9/10 days, Σ instrument_count=19,330,244. **Verdict: DeFi NOT AFFECTED** by the future-date
guard bug — both windows show near-full daily coverage, consistent with the source doc's own Prediction finding. Item 1
left unchecked `[OPERATOR]` per the dispatching todo's Step 2, with a note that its DEPLOY half is already satisfied by
the existing correction banner.

**2026-07-29 (slot 9, data_engineering)** — Dispatched item 1 again after a same-day (2026-07-29T00:51:59Z) mechanical
rephrase pass (`unified-trading-pm@6edd4486a`, "rephrase 24 already-resolved BLOCKED-* mentions to unblock AO dispatch",
sourced from `ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md`) had stripped this checkbox's
`BLOCKED-CREDENTIALS` marker and replaced it with "credential gate cleared 2026-07-28 (slot 6)" — a false status claim:
that commit's own premise was to fix mentions of an ALREADY-resolved block, but this item's credential block was never
resolved, only the separate launch DECISION was (operator said "yes, launch it" on 2026-07-28, but never fixed the
`odds-api-key` secret the launch depends on — two different gates, conflated by the rephrase). Re-verified live before
trusting either the checkbox text or the top banner: pulled `odds-api-key` fresh
(`gcloud secrets versions access latest --secret=odds-api-key --project=central-element-323112`) and curled
`https://api.the-odds-api.com/v4/sports?apiKey=...` directly — still `error_code=DEACTIVATED_KEY`, unchanged from every
check since 2026-07-26 (now 8 independent re-verifications, all identical). Checked `/api/blocked/stats` — 0 unanswered
across 696 total, so `BLK-e9c1c362` (filed 2026-07-28 asking the operator to reconcile the "launch it" vs "decline to
fix the key" contradiction) shows as answered somewhere, but no resolution commit or doc update reflects an answer back
into this corpus, and no alternate wired odds-api credential path exists (corpus-wide grep, consistent with every prior
audit) — so I am NOT treating an unlocatable "answered" status as license to launch. Restored the `BLOCKED-CREDENTIALS`
marker to the checkbox's own first line (matching the top banner's own claim about where the marker lives, and the
`blocked_marker_continuation_line_not_scanned_2026_07_26.md` convention) and rewrote the item to clearly separate the
DECISION gate (ruled, open) from the CREDENTIAL gate (still dead, declined-to-fix). Not launching any VM or spending
odds-api credits against a key confirmed dead for the 8th consecutive check. Did not flip the checkbox — nothing here is
actually done beyond what the correction banner already establishes. Flagging back to
`ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md`'s Progress Log that its source rephrase pass had at
least one false positive (this item) — its "24 already-resolved" premise should not be trusted uncritically for the
other files it touched without a similar per-item live-fact check, not just a text-pattern read.
