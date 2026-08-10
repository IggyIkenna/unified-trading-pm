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
author: unknown
parent_epic: predictions_master
priority: P0
source:
  "plan-reconciliation audit of work_split_2026_05_22_ikenna.md ahead of archival, 2026-07-13 session (slot 3) —
  Workflow-orchestrated verification pass, adversarially re-checked"
assigned_vm: NA
resolved_by:
locked_by:
context_scope:
  [
    /plans/archive/2026_08/issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md,
    /plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
    /plans/archive/2026_05/kalshi_api_migration_to_elections_subdomain_2026_05_20.md,
    execution-service/execution_service/sports_execution/adapters/exchanges/kalshi.py,
  ]
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

> **🟢 RELAUNCHED — STALL RESOLVED (2026-07-27/28).** Live Kalshi/Polymarket prediction tick capture was confirmed
> genuinely down for ~29 days (last real day `2026-06-28`, no producer VM or Cloud Run service running anywhere in the
> fleet) and has been relaunched: 4 fresh `prediction-live-{venue}-{data_type}-*` VMs are running and the consolidated
> manifest confirms captured `live_kalshi`/`live_polymarket_clob` rows through `day=2026-07-27`. See the dated
> 2026-07-27 Progress Log entry for the original diagnosis and the 2026-07-28 entry for the relaunch evidence.

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

1. ~~Confirm/deny whether `raw_tick_data/by_date/` is genuinely stalled at `day=2026-06-28` (check the live capture
   process/VM logs directly) vs. a path/prefix read artifact.~~ ✅ **GENUINE STALL, confirmed 2026-07-27** (slot-12) —
   see the dated Progress Log entry below.
2. ~~Fix `e2e-testing@dbf8e78`'s regression at `validate_batch_live_smoke_matrix.py:552` (swap back to the
   elections-subdomain host) and actually build the missing regression check this time so it can't silently reappear a
   third time.~~ ✅ **DONE 2026-07-27** (`prediction_satellite_ao_dispatch_batch1_2026_07_25.md` todo 1, slot per that
   plan) — `e2e-testing@371ac1b` repoints `_fetch_kalshi_instruments()` at `api.elections.kalshi.com`; new
   `tests/unit/test_validate_batch_live_smoke_matrix.py` scans the module's own source for the dead host string (not
   just the one call site) so a third reintroduction anywhere in the file fails the build.
3. ~~Triage the growing `kalshi/markets` / `kalshi/market_lookup` schema-drift GitHub issue chain (#45→#590) — decide
   whether this is a Kalshi-side API change requiring a UAC schema bump, or an endpoint that's been retired.~~ ✅
   **RESOLVED 2026-07-26** (via `/plans/archive/2026_07/prediction_satellite_ao_dispatch_batch3_2026_07_26.md` todo 1's
   schema-drift half, archived). Root cause: the "23 endpoints" was one weekly auto-filed snapshot issue listing all
   currently-failing endpoints (only 2 of 23 Kalshi) — not 23 separate regressions. Not a live API/schema drift:
   `KalshiMarket` (schemas.py) + the endpoint registry already correctly documented the March-2026 dollar-field
   migration; only the 2 VCR cassette fixtures (`markets.yaml`, `market_lookup.yaml`) used as the drift-diff baseline
   were stale (pre-migration shape / an expired test ticker). Re-recorded both against live data;
   `validate_schemas.py` + all 4 `tests/vcr/test_kalshi_vcr.py` tests green. Shipped `unified-api-contracts@c03161a1`.
   Closed the 10 superseded weekly snapshots (#45,#46,#47,#60,#102,#319,#416,#541,#555,#590) as duplicates of #673;
   commented on #673 with the fix (the other 21 unrelated endpoint failures in that snapshot are untouched, out of
   scope).

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

## 2026-07-27T22:10Z — GENUINE STALL confirmed (slot-12): live prediction capture has been down ~29 days, no bucket/path artifact

**Verdict: GENUINE STALL, not a read artifact.** Read-only diagnosis, no fix/backfill/VM-launch/manifest-write in scope
per this todo.

- **Bucket-form ruled out**: `gcloud storage buckets list --filter="name~market-data-tick.*pred"` returns exactly
  `market-data-tick-pred-prd-central-element-323112` (the one this doc's original finding checked) + a `-test-` sibling
  — no env-less/legacy variant exists to have been misread.
  `resolve_bucket_name(kind="market-data-tick-prediction", asset_group="prediction")` resolves to the same prd bucket,
  confirming it's the canonical target.
- **Partition-shape ruled out**: the bucket's only tick-data prefix is
  `raw_tick_data/by_date/day=.../pipeline_mode=.../ asset_group=prediction/...` — no alternate cqg-first or other
  top-level layout exists (only `_index/`, `_migration_backup/`, `_vm_staging/`, `processed_candles/`, `raw_tick_data/`
  at bucket root).
- **Direct GCS evidence**: `day=` partitions with a `pipeline_mode=live_kalshi` or `pipeline_mode=live_polymarket_clob`
  subdirectory exist for every day through `day=2026-06-28`, then **never again** through `day=2026-07-26` (today is
  2026-07-27) — a clean, total stop, not a thin/patchy gap. Meanwhile
  `pipeline_mode=batch_kalshi`/`batch_polymarket_clob` partitions DO appear intermittently in that same window
  (`day=2026-07-09`, `07-16`, `07-18..07-26`) — i.e. the SAME bucket, SAME base path shape is demonstrably being written
  to by BATCH jobs throughout, which rules out a bucket- or path-level misread: if the read path were wrong, batch data
  wouldn't be visible there either.
- **Manifest corroboration** (bounded predicate-pushdown read of `_index/availability_index.parquet`, filtered to
  `pipeline_mode LIKE '%live%' AND capture_status='captured'`, not a corpus walk): max captured date is
  `live_kalshi`→`2026-06-29`, `live_polymarket_clob`→`2026-06-28`. `day=2026-06-29` itself has **zero objects in GCS**
  (`gcloud storage ls .../day=2026-06-29/` matches nothing) — that one manifest row is a phantom/unbacked entry, so the
  last REAL captured live day for both venues is `2026-06-28`, matching the original finding exactly. Gap as of today:
  **~29 days**.
- **Producer VM/process state — confirmed absent, not just quiet**: the two launchers that create live prediction
  producers (`deployment-service/scripts/vm/launch-mtds-live-prediction-consolidated.sh`,
  `VM_PREFIX=mtds-live-prediction-consolidated`; `launch-prediction-live.sh`, `VM_PREFIX=prediction-live-{venue}-{dt}`)
  have **zero matching instances** anywhere in the current GCP fleet
  (`gcloud compute instances list --filter="name~mtds-live-prediction OR name~prediction-live"` — 0 rows, checked
  against the full unfiltered instance list too, which shows an active fleet of 20+ VMs for cefi/defi/features/etc., so
  this isn't a listing-permissions gap). No Cloud Run service for prediction/kalshi/ polymarket exists either
  (`gcloud run services list` — 16 services, none prediction-related). There is therefore no running process to pull
  logs from — the producer isn't silently failing, it simply isn't running.
- **What this is NOT**: not the `instruments-store-pred-prd-` vs `-prediction-` env-short/env-less split documented in
  `prediction_live_clob_depth_capture_2026_07_24.md` (that's the UNIVERSE bucket a live runner reads to know what to
  poll, a different bucket kind from the tick-data bucket checked here) — that mechanism was considered and excluded by
  the same corroborating batch-data-flows-fine evidence above, but is flagged as a plausible root-cause angle for
  whoever picks up the remediation follow-up (not this todo's scope).
- **Remediation is explicitly out of scope for this todo** (read-only diagnosis only) — relaunching either live producer
  is a follow-up todo for whoever owns the live-capture remediation, informed by this verdict.

## 2026-07-28T03:40Z — RELAUNCHED, stall broken (slot-11, `prediction_satellite_ao_dispatch_batch5_2026_07_26.md` todo 4)

**Universe pre-flight**: confirmed the live-runner's `resolve_bucket_name(kind="instruments-store-prediction")` call
resolves to the correct env-short `instruments-store-pred-prd-central-element-323112` (not the stale legacy bucket
flagged above as "considered and excluded" — re-verified fresh, not just excluded as the prior-stall cause). The
universe data itself was fresh as of the `day=2026-07-27` IS daily-enum run for BOTH venues — the cqg-first
`canonical_question_group=<G>/day=<D>/venue=<V>/instruments.parquet` layout is a dead/legacy write path (frozen at
`day=2026-07-22`); the live writer now uses the full-hive
`day=<D>/pipeline_mode=<PM>/asset_group=prediction/ venue=<V>/canonical_question_group=<G>/instruments.parquet` shape
(2026-07-21 IS migration), which the live-runner's blob filter already handles (it pattern-matches venue/day/filename
segments regardless of full path shape) — a documentation-staleness false alarm, not a functional gap.

**Launch**: relaunched via the per-shard `launch-prediction-live.sh` (4 independent VMs, one per venue×data_type shard):
`prediction-live-kalshi-trades-20260727-223731`, `prediction-live-kalshi-book-snapshot-5-20260727-223753`,
`prediction-live-polymarket-trades-20260727-234622`, `prediction-live-polymarket-book-snapshot-5-20260727-234650`. All 4
STARTED within T+60s.

**Verified alive ~5h post-launch (2026-07-28T03:40Z)**: all 4 VMs show live `PIPELINE_HEARTBEAT`/`ManifestWriter` log
activity matching current wall-clock time (per-VM manifest shard entry counts climbing every ~10s). Manifest-confirmed
capture (bounded predicate-pushdown read of `_index/availability_index.parquet`, not a corpus walk): `live_kalshi` max
captured date = `2026-07-27` (62,342 captured rows), `live_polymarket_clob` max captured date = `2026-07-27` (393,819
captured rows). The ~29-day stall is broken; live capture resumed same-day as launch.

## Todos

- [ ] [DATA] P2. **Verify the Kalshi execution-service paper-order flow end-to-end** — still genuinely open: only the
      elections-subdomain URL swap shipped; no test/log/commit confirms the paper-order flow was ever actually verified
      end-to-end. **KEEP-NA-STALE-DUPLICATE (na-eligibility-audit 2026-08-04)**: this exact deliverable is owned by
      `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5 (routed via
      `issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md`'s `[DATA] P1` todo, itself
      `BLOCKED-OPERATOR-DECISION`) — not independently dispatchable here; do not reclassify this doc on this checkbox.

## Progress Log

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — 1 open ([DATA] P2, verify the Kalshi
  execution-service paper-order flow end to end). CONFLICT: this is the same deliverable as
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5's second leg, which is itself correctly gated on the
  credential reshape in `issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md` (the root cause of why
  this verification could never have passed). Leave it owned there.

- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — swapped `predictions_master.md` epic for
  `execution-service/.../adapters/exchanges/kalshi.py`, the real source target of the sole open todo (verify the Kalshi
  paper-order flow end-to-end).

- **na-eligibility-audit 2026-08-04 (prediction tranche)**: KEEP-NA, STALE-DUPLICATE citation fix — the sole open
  checkbox (verify Kalshi paper-order flow end-to-end) is a verbatim duplicate of
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5 (via
  `kalshi_execution_credential_secret_name_mismatch_2026_07_26.md`'s `[DATA] P1` todo, which states verbatim "this is
  the ORIGINAL verification `kalshi_live_capture_regression_and_drift_2026_07_13.md` asked for"). The 2026-07-30 marker
  already noted this as a CONFLICT in prose but never annotated the checkbox itself; annotated in place with the
  citation now so a future run/dispatcher doesn't treat it as independent unclaimed work. Left unchecked — the
  underlying verification genuinely hasn't happened (`BLOCKED-OPERATOR-DECISION` on the live-vs-demo-host question,
  unresolved as of today). Not reclassified — this is a citation fix, not a scope change. Doc stays NA.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-07 (prediction tranche, autonomous)**: KEEP-NA-STALE-DUPLICATE, re-verified — the
  citation added 2026-08-04 to `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5 is still current.
  Independently re-traced both hops: this doc's checkbox <->
  `kalshi_execution_credential_secret_name_mismatch_2026_07_26.md`'s `[DATA] P1` todo (states verbatim "this is the
  ORIGINAL verification ... asked for") <-> batch6 todo 5 (still `assigned_vm: planning` / `status: active`, gated Todo
  2 still open) — all three consistent, no drift. Left unchecked; not reclassified. Doc stays NA.

- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-09 (prediction tranche)**: KEEP-NA-STALE-DUPLICATE, re-verified — unchanged since the
  2026-08-07 marker (only intervening commit is today's context-scout refresh). The sole open item (Kalshi
  paper-order-flow end-to-end verification) remains correctly duplicate-tracked at
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5, itself gated on
  `kalshi_execution_credential_secret_name_mismatch_2026_07_26.md`'s `BLOCKED-OPERATOR-DECISION` item. Doc stays NA.
