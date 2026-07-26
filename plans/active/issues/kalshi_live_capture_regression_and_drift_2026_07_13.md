---
doc_type: issue
title:
  Kalshi elections-subdomain migration regression re-introduced in e2e-testing + possible stalled prediction tick
  capture + growing schema drift (surfaced by work_split_2026_05_22_ikenna.md retirement audit)
summary:
  "Reconciling the now-archived `work_split_2026_05_22_ikenna.md` (2026-07-13) surfaced two findings never actually
  closed out despite the parent Kalshi migration/credential-provisioning plans being marked complete: (1) `e2e-testing@
  dbf8e78` (2026-06-22) reintroduced the dead `https://trading-api.kalshi.com/trade-api/v2/markets` host into
  `scripts/validation/validate_batch_live_smoke_matrix.py:552` — a month AFTER `kalshi_api_migration_to_elections_
  subdomain_2026_05_20.md` (archived 2026-05-23) declared the elections-subdomain migration done — because that plan's
  Phase 4 'add a predictions_master regression check for the elections-subdomain URL' item was never actually added, so
  nothing caught the regression; (2) `gs://market-data-tick-pred-prd-central-element-323112/raw_tick_data/ by_date/` has
  no day partitions after `day=2026-06-28` (~2 weeks stale as of 2026-07-13), suggesting live Kalshi/ prediction tick
  capture may have silently stalled. Corroborating context: unified-api-contracts' `weekly-validation. yml` (still
  running on schedule, confirmed via `gh run list`) shows real, growing Kalshi schema drift — `kalshi/ markets` missing
  `subtitle`/`liquidity`/`yes_bid`/`yes_ask`/`no_bid` fields + a `result` type mismatch (null→string), and
  `kalshi/market_lookup` returning HTTP 404 (ENDPOINT_BROKEN) — tracked across an open, un-triaged GitHub issue chain
  that has grown from 11 to 23 failing endpoints since May."
status: open
nature: notes
asset_group: [prediction]
stage: [data]
repos: [e2e-testing, market-tick-data-service, unified-api-contracts, execution-service]
scope: [engineer, admin]
tags: [kalshi, prediction, regression, live-capture, schema-drift, data-correctness, e2e-testing, big-finding]
related:
  [
    ../../epics/predictions_master.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md,
    ../../archive/2026_05/kalshi_api_migration_to_elections_subdomain_2026_05_20.md,
    ../../archive/2026_07/work_split_2026_05_22_ikenna.md,
  ]
created: 2026-07-13
parent_epic: predictions_master
priority: P0
source:
  "plan-reconciliation audit of work_split_2026_05_22_ikenna.md ahead of archival, 2026-07-13 session (slot 3) —
  Workflow-orchestrated verification pass, adversarially re-checked"
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

## What I found

While reconciling `work_split_2026_05_22_ikenna.md` (a 2026-05-22 dispatch snapshot being retired — every plan it
tracked is independently archived/complete), a verification pass on its dangling "remaining work" items turned up two
findings that are **not** bookkeeping staleness — they point at real, currently-unaddressed problems in the live
Kalshi/prediction pipeline.

### 1. The elections-subdomain migration regression is back, live, in CI

`kalshi_api_migration_to_elections_subdomain_2026_05_20.md` (archived 2026-05-23, `status: complete`) shipped the
subdomain swap across UAC/instruments-service/MTDS/execution-service/e2e-testing/UI (commits `UAC@5729197`,
`instruments-service@79ad855`, `MTDS@28b84ce`, `execution-service@8a3cbe48`, `e2e-testing@badfbc4`,
`unified-trading-system-ui@664c3992`), but its Phase 4 item "add a `predictions_master` regression check for the
elections-subdomain URL" was checked off as `DEFERRED-OPERATOR-DECISION` (credential-blocked), never actually
implemented.

One month later, `e2e-testing@dbf8e78` (2026-06-22) hardcoded the OLD, dead host straight back into
`scripts/validation/validate_batch_live_smoke_matrix.py:552`:

```
https://trading-api.kalshi.com/trade-api/v2/markets
```

Nothing caught this because the regression check that would have caught it was never built. This line is live and broken
in the current tree today.

### 2. Prediction tick capture may have silently stalled (~2 weeks)

`gcloud storage ls gs://market-data-tick-pred-prd-central-element-323112/raw_tick_data/by_date/` shows day partitions
stopping at `day=2026-06-28` — no July partitions at all, as of this session (2026-07-13). This wants an operator/agent
check on whether live Kalshi/prediction tick capture has actually stopped, or whether this is a read/path artifact.

### 3. Corroborating context — real, growing Kalshi schema drift

`unified-api-contracts`' `weekly-validation.yml` is running on schedule (confirmed via `gh run list`, 11+ runs since
2026-05-20 — so the earlier claim that this dispatch "never ran" was wrong), but it is not passing cleanly. The
2026-07-13 run shows:

- `kalshi/markets`: DRIFT — missing `subtitle`, `liquidity`, `yes_bid`, `yes_ask`, `no_bid`; `result` type mismatch
  (`null` → `string`)
- `kalshi/market_lookup`: `ENDPOINT_BROKEN` — HTTP 404

This is tracked in an open, un-triaged GitHub issue chain (#45 → #590, all still OPEN) that has grown from 11 to 23
failing endpoints since May. This drift is a plausible contributing factor to finding #2 above (a capture path that
can't parse the current response shape would fail silently or degrade over time) but that link is not yet confirmed —
flagging as context, not as a settled causal claim.

### Also still genuinely open (lower severity, not new — carried here for visibility since their original tracking doc is being archived)

- Kalshi execution-service paper-order flow was never actually verified end-to-end (only the URL swap shipped; no
  test/log/commit found).
- `manifest_master.md` still carries an unflipped `- [ ]` P2 checkbox for "prediction bucket naming migration" that
  looks functionally superseded by the 2026-07-13 legacy-bucket decommission
  (`data_completion_to_100_all_ag_2026_06_21.md` E1-E8) but was never explicitly closed — worth a docs-only flip, not
  new work.

## Why this matters

Findings #1 and #2 are exactly the class of gap the "add a regression check" item existed to prevent, and #2 touches
live data-pipeline correctness directly (a stalled capture path silently produces gaps that look like "genuine
unavailability" downstream rather than a known, fixable break). Per the data-pipeline-correctness HARD RULE this should
not sit un-triaged.

## Suggested next step

1. Confirm/deny whether `raw_tick_data/by_date/` is genuinely stalled at `day=2026-06-28` (check the live capture
   process/VM logs directly) vs. a path/prefix read artifact.
2. Fix `e2e-testing@dbf8e78`'s regression at `validate_batch_live_smoke_matrix.py:552` (swap back to the
   elections-subdomain host) and actually build the missing regression check this time so it can't silently reappear a
   third time.
3. ~~Triage the growing `kalshi/markets` / `kalshi/market_lookup` schema-drift GitHub issue chain (#45→#590) — decide
   whether this is a Kalshi-side API change requiring a UAC schema bump, or an endpoint that's been retired.~~ ✅
   **RESOLVED 2026-07-26** (via `prediction_satellite_ao_dispatch_batch3_2026_07_26.md` todo 1's schema-drift half).
   Root cause: the "23 endpoints" was one weekly auto-filed snapshot issue listing all currently-failing endpoints (only
   2 of 23 Kalshi) — not 23 separate regressions. Not a live API/schema drift: `KalshiMarket` (schemas.py) + the
   endpoint registry already correctly documented the March-2026 dollar-field migration; only the 2 VCR cassette
   fixtures (`markets.yaml`, `market_lookup.yaml`) used as the drift-diff baseline were stale (pre-migration shape / an
   expired test ticker). Re-recorded both against live data; `validate_schemas.py` + all 4
   `tests/vcr/test_kalshi_vcr.py` tests green. Shipped `unified-api-contracts@c03161a1`. Closed the 10 superseded weekly
   snapshots (#45,#46,#47,#60,#102,#319,#416,#541,#555,#590) as duplicates of #673; commented on #673 with the fix (the
   other 21 unrelated endpoint failures in that snapshot are untouched, out of scope).

---

## 2026-07-14T11:00Z — BATCH CHAIN RESOLVED: all 6 root causes closed with a production capture (423 rows / 6,407 trades); doc stays open for the 3 live-side follow-ups

The batch-capture half of this doc is CLOSED end to end. The final two links, shipped and production-verified today:

- **Root Cause #5 — per-venue lifecycle partition** (`instruments-service@1fa9177f`): `_write_market_lifecycle` now
  partitions `{group, day, venue}` → `day={d}/group={g}/venue={V}/market_lifecycle.parquet`; POLYMARKET's write can no
  longer clobber KALSHI's rows. Production-verified after the forced IS prediction re-run 2026-07-07..12 (VM
  `instr-backfill-pred-rc5b-20260714`, DEPLOYMENT_COMPLETED exit 0; the first launch was SPOT-preempted at 13 min —
  idempotent relaunch per design): **KALSHI's 1,362 lifecycle rows are back** at
  `day=2026-07-09/group=OTHER/venue=KALSHI/` with per-venue leafs present for BOTH venues on every checked day. MTDS
  readers were verified layout-tolerant in advance (`mtds@5bb0e2c3` prefix-list + suffix-match).
- **Root Cause #6 — Kalshi rejects millisecond timestamps** (`market-tick-data-service@d2040f8f`): with the lifecycle
  restored, the adapter self-discovered all 1,362 real tickers for the first time — and every request 400'd with
  Kalshi's explicit `"min/max timestamp must be in seconds, not milliseconds"` (verified live via curl).
  `download_batch` derived `after_ts` as `timestamp()*1000`; now seconds, + a regression test pinning the exact value.
  This bug was UNREACHABLE until RC#1–5 were fixed (the adapter never got past ticker discovery), which is why six root
  causes stacked.
- **Production capture proof (2026-07-09, VM `mtds-backfill-pred-kalshi-rc6-20260714`, DEPLOYMENT_COMPLETED exit 0)**:
  `KalshiAdapter.download_batch: 2026-07-09 — 6407 trades (rejected pre=0 post=0)`; per-VM manifest shows **423
  `captured` trades rows + 23 `captured` prediction_canonical_question_group rows (6,407 trades)**, superseding the
  legacy dishonest empties (captured outranks non-captured in the consolidator); real per-instrument parquet at
  `raw_tick_data/by_date/day=2026-07-09/pipeline_mode=batch_kalshi/...:trades/KALSHI:PREDICTION_MARKET:*.parquet`.
- `book_snapshot_5` note: Kalshi has no historical order-book restore — book snapshots are a LIVE-capture surface; a
  batch force-leg on a past day is honestly empty by construction (last night's `empty_confirmed SOURCE_RETURNED_ZERO`
  row is the correct steady-state for that cell).
- The three live-capture follow-ups listed above (live stall triage at day=2026-06-28, the e2e-testing host regression,
  the schema-drift issue chain) remain open — they are the LIVE half, out of scope of the batch chain this doc's
  root-causes cover.
