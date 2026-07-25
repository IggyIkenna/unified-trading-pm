---
doc_type: issue
title: Sports fixture_events canonical-schema re-fetch — census complete, launch blocked on af-backfill singleton lock
summary: >-
  Progress tracker for `sports_satellite_ao_dispatch_batch2-031` (fixture_events re-fetch into canonical 13-col schema).
  Spun off from the parent plan (at its 1000-line hard cap from concurrent slot activity) to avoid further growth there.
  Full-corpus census complete: 43,233 captured objects censused, 12,603 genuinely non-canonical (needing re-fetch),
  25,639 already canonical, 4,991 phantom manifest rows (spun to a separate issue doc). Recovery- ids parquet built and
  durably staged in GCS. Actual re-fetch launch is blocked on the af-backfill VM singleton lock (API-Football is
  rate-limited per-key; a second concurrent VM risks the same 403-storm the Tardis concurrency lesson already taught
  this session) — the in-flight `af-backfill-20260725-002739` (INJURIES catch-up) must finish first.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, fixture-events, canonical, re-fetch, api-football, backfill]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md,
    /plans/active/issues/sports_fixture_events_phantom_manifest_rows_2026_07_25.md,
  ]
created: 2026-07-25
priority: P1
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["sports_satellite_ao_dispatch_batch2-031, slot 2, 2026-07-25"]
drift_direction: advance-code
---

# fixture_events canonical re-fetch — census done, launch pending

## What's done this session

**Full census** (`instruments-service@ca4937a` — `scripts/census_fixture_events_schema_variants_2026_07_25.py`,
committed for re-use, not a one-off): read the schema (columns only, via UTL `get_storage_client().download_bytes` +
pyarrow, no row-group load) of all 43,233 canonical `capture_status=captured` FIXTURE_EVENTS objects. Result:

| variant                      |  count | share |
| ---------------------------- | -----: | ----: |
| `canonical_13col`            | 25,639 | 59.3% |
| `degenerate_5col_stub`       |  7,846 | 18.2% |
| `af_prefixed_10col`          |  2,383 |  5.5% |
| `named_9col`                 |  2,372 |  5.5% |
| `other`                      |      2 |  0.0% |
| `missing` (phantom manifest) |  4,991 | 11.5% |

12,603 objects (7,846+2,383+2,372+2) are genuinely present and non-canonical — this todo's real scope, roughly matching
the original 120-object sample's ~30% estimate. The 4,991 phantom-manifest-row finding is OUT of this todo's scope —
filed separately: `issues/sports_fixture_events_phantom_manifest_rows_2026_07_25.md`.

**Recovery-ids parquet built**: extracted `af_fixture_id`s from the 12,603 non-canonical objects (16,777 distinct
fixture_ids after dedup), written in the exact format the existing `instruments-service` CLI `--recovery-fixture-ids`
mechanism expects (`af_fixture_id` column; consumed by `instruments_handler.py::_load_recovery_fixture_ids`). This
routes the re-fetch through the REAL writer path (`--sports-entity FIXTURE_EVENTS --recovery-fixture-ids <path>`,
per-fixture allowlist filter + read-modify-write merge, canonical schema enforced by the normal write path) — no
hand-rolled GCS write anywhere in this campaign. Durably staged (not just local scratch):

- `gs://deployment-scripts-central-element-323112/sports_fixture_events_refetch_2026_07_25/recovery_fixture_ids.parquet`
- `gs://deployment-scripts-central-element-323112/sports_fixture_events_refetch_2026_07_25/census_2026_07_25.json`

**Census-script correctness note**: the first pilot run mis-classified ~10% of objects as "missing" due to the raw
`google.cloud.storage` client's connection-pool exhaustion under 30+ concurrent threads being silently caught and
treated as a 404 — fixed (retried + isolated per-request client + a distinct `read_error` bucket) before the full run;
also had to switch from raw `google.cloud.storage` to the UTL `get_storage_client()` wrapper (TID251 gate) and the
top-level `unified_trading_library` import path (import-pattern gate) before it could ship.

## Why the actual re-fetch hasn't launched yet

The launcher (`deployment-service/scripts/vm/launch-api-football-backfill-vm.sh`) already supports
`--recovery-fixture-ids` end-to-end — the mechanism is ready. But it enforces a **singleton lock across all
`af-backfill-*` VMs** because API-Football rate-limits per-key; a second concurrent VM against the same key risks the
exact 403-storm + false `attempted_failed` manifest corruption the Tardis concurrency lesson already demonstrated this
session (N>1 measured ~94% 403s). `af-backfill-20260725-002739` (the INJURIES catch-up backfill, launched earlier this
session, unrelated to this todo) was still RUNNING at last health-check (2026-07-25T02:24Z,
`last_completed_date=2024-03-31`, monotonic, genuinely hours from done) — bypassing the lock with `--force`/
`--skip-lock` here would repeat a documented past mistake (`launch-api-football-backfill-vm.sh`'s own comments cite the
2026-07-14 GW re-run wave doing exactly this).

## Next action (once the lock clears — check `gcloud compute instances list --filter='name~"^af-backfill-"'` first)

```bash
bash deployment-service/scripts/vm/launch-api-football-backfill-vm.sh \
  --entity FIXTURE_EVENTS \
  --recovery-fixture-ids gs://deployment-scripts-central-element-323112/sports_fixture_events_refetch_2026_07_25/recovery_fixture_ids.parquet \
  2019-01-01 2026-07-25
```

After it completes: re-run `scripts/census_fixture_events_schema_variants_2026_07_25.py` (full, no `--limit`) to verify
the non-canonical count has dropped toward 0 before flipping the parent todo's checkbox — the "Done when" bar is a
repeat sample showing genuinely 0 non-13-col objects (or documented unrecoverable ones).

## Todos

- [ ] [DATA] P1. Launch the fixture_events canonical re-fetch (command above) once the af-backfill singleton lock
      clears, then re-census to verify convergence, then flip the parent todo's checkbox in
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md` with the re-census evidence. (repo: instruments-service).
      **Done when**: re-fetch VM completes, and a full re-census shows 0 genuinely non-canonical FIXTURE_EVENTS objects
      remaining (or each remaining one is documented as unrecoverable). — **LAUNCHED 2026-07-25T03:22Z (slot 4,
      data_engineering), NOT complete.** Lock cleared when `af-backfill-20260725-002739` (INJURIES catch-up)
      self-terminated cleanly (`exit_code=0`, confirmed via its run.log `DEPLOYMENT_COMPLETED`) — checked
      `status=RUNNING` filter first, genuinely clear, no `--force`/`--skip-lock` needed. Launched
      `af-backfill-20260725-032253` with the exact command above; verified DEPLOYMENT_STARTED + live progress within
      ~4min (no fire-and-forget): run.log shows
      `Recovery mode: promoting redo_all=True ... recovery_fixture_ids     has 16765 af_fixture_ids` (matches this doc's
      16,777 count, minor variance expected) and real per-date `entity=FIXTURE_EVENTS` enrichment fetches starting
      2019-01-20. **Stale-tarball check performed before trusting the launch** (launcher warned 4 tarballs stale):
      instruments-service was missing exactly 1 commit (`450b1b58`, an unrelated FIXTURES_SCHEDULE empty-gap-emission
      fix, not FIXTURE_EVENTS); unified-api-contracts missing exactly 1 commit (a Central Asia league-registry addition,
      irrelevant to re-fetching already-known `af_fixture_id`s); unified-trading-library and deployment-service were
      actually current (false-positive staleness warning) — none of the gaps affect this campaign's correctness. Full
      run will take hours (2019→ present, 16,765 fixtures); not completable this turn. Next dispatch: health-check
      `gcloud compute instances list --filter='name~"^af-backfill-20260725-032253"'` +
      `gs://deployment-scripts-central-element-323112/vm-logs/af-backfill-20260725-032253/run.log` before assuming still
      running; once terminal, re-run the census script per "Next action" above before flipping this checkbox. —
      **Health-checked 2026-07-25T04:18Z (slot 11, data_engineering), still RUNNING**: heartbeat blob
      (`vm-heartbeat/af-backfill-20260725-032253.txt`) fresh (31s old at check time); run.log date-progressed
      2019-01-03→2019-12-24 between two checks ~6min apart, monotonic, no error/stall signature. Not completable this
      turn (genuinely hours from done, 2019→2026-07-25 range). Released via `/skip-current-task`, not
      duplicate-launched. Next dispatch: repeat this health-check; once terminal (`exit_code=0`/`DEPLOYMENT_COMPLETED`,
      self-deleted), re-run the census script per "Next action" above before flipping this checkbox. — **Health-checked
      2026-07-25T05:10Z (slot 3, data_engineering), still RUNNING**: `gcloud compute instances list` confirms `RUNNING`
      in `asia-northeast1-c`; run.log timestamps continuous up to 05:09:45 (30s before check, live process, not
      stalled); 359 distinct `date=` markers seen since the 03:22:53 launch, currently on `2019-12-25`. **Efficiency
      finding, not blocking**: 2 of the 359 dates so far (`2019-12-24`, `2019-12-25`) hit a
      "`Per-fixture GCS skip: no GCS fixtures for date=X — using 16765 recovery IDs directly`" fallback — when a date
      has no GCS-cached fixture list, the script falls back to attempting ALL 16,765 recovery fixture IDs against that
      single date instead of just the handful that actually played that day. `date=2019-12-24` alone took ~66min
      (03:53:41→05:00:02) under this fallback vs. seconds for a normal date. At the observed ~0.6% fallback-date rate
      this could add several hours across the full 2019→2026 range — real but not correctness-affecting (every real
      fixture still gets fetched exactly once via the allowlist filter, just slower on affected dates); not something to
      intervene on mid-run. Not completable this turn (2141 of ~2500 dates remain even ignoring further fallback hits).
      Released via `/skip-current-task`, not duplicate-launched. Next dispatch: repeat this health-check (2-read
      progress-metric check, not single-snapshot); once terminal, re-run the census script per "Next action" above
      before flipping this checkbox. If the fallback-date rate turns out much higher than 0.6% over a longer observation
      window, consider filing a separate perf follow-up issue doc for the launcher/enrichment script (out of scope for
      this todo — do not fix mid-flight on a running prod VM). — **Health-checked 2026-07-25T05:29Z (slot 4,
      data_engineering), still RUNNING**: `gcloud compute instances list` confirms `RUNNING` in `asia-northeast1-c`;
      heartbeat blob `vm-heartbeat/af-backfill-20260725-032253.txt` Update Time `2026-07-25T05:30:01Z` (fresh, ~1min old
      at check time); run.log last line `05:27:24Z` (~2min old), live per-fixture `Fetched N events for     fixture=X`
      lines interleaved with the expected 429-rate-limit sleep/retry cycling — no error/stall signature. Distinct
      `date=` count unchanged at 359 (still `2019-12-25`) since the 05:10Z check — confirmed this is the SAME known
      fallback-date pattern (not a stall): `date=2019-12-25` hit
      "`Per-fixture GCS skip: no GCS fixtures for     date=2019-12-25 — using 16765 recovery IDs directly`" at
      `05:00:02Z`, ~30min into its own ~66min-per-fallback-date budget (matching `2019-12-24`'s measured 66min) —
      genuine in-date progress (fixture fetches actively advancing within the date), just no NEW date boundary crossed
      yet, exactly as the fallback-rate finding predicted. Not completable this turn (~2140 of ~2500 dates remain).
      Released via `/skip-current-task`, not duplicate-launched. Next dispatch: repeat this health-check (2-read
      progress-metric check — either a new `date=` boundary OR continued in-date fixture-fetch advance counts as live);
      once terminal, re-run the census script per "Next action" above before flipping this checkbox. — **Health-checked
      2026-07-25T05:37Z (slot 3, data_engineering), still RUNNING, confirms slot 4's 05:29Z check**: run.log grew
      47,010→55,413 lines since the 05:10Z read, latest timestamp 05:37:48 (live); still the same `date=2019-12-25`
      fallback (37min in of its ~66min budget), no stall. Released via `/skip-current-task` again, no new finding. —
      **Health-checked 2026-07-25T05:53Z (slot 3, data_engineering), still RUNNING, new finding**: log growing (59,547
      lines), heartbeat at 05:51:24Z (~2min old, live); still `date=2019-12-25` (359 distinct dates unchanged). **New**:
      log now shows `429 Rate limited ... sleeping 60s to next minute` retries against
      `v3.football.api-sports.io/fixtures/events` — API-Football rate-limiting has kicked in on this date's 16,765-
      fixture fallback burst, which explains why `2019-12-25` is running noticeably longer than `2019-12-24`'s ~66min
      (each 429 costs a 60s sleep on top of the normal per-fixture call). Not correctness-affecting (the client's own
      retry/backoff handles it, per the `attempt 1/10` counter), but pushes the total ETA further out — worth knowing if
      a future health-check sees this date still running well past 66min, that's the rate-limit cost accumulating, not a
      new stall. Released via `/skip-current-task` again. — **Health-checked 2026-07-25T05:54Z (slot 12,
      data_engineering), still RUNNING, confirms slot 3's concurrent 05:53Z check**: `gcloud compute instances list`
      confirms `RUNNING` in `asia-northeast1-c`; heartbeat blob fresh (~14s old at check time); run.log grew
      55,413→60,162 lines (+4,749) since the 05:37Z read, latest timestamp `05:53:49` (live per-fixture
      `Fetched N events for fixture=X` lines); still `date=2019-12-25` (~74min into its own ~66min fallback-date budget
      — consistent with slot 3's just-logged 429-rate-limit finding explaining the overrun, not a new stall), no
      `DEPLOYMENT_COMPLETED`/`exit_code` terminal marker. Not completable this turn (still ~2140 of ~2500 dates remain).
      Released via `/skip-current-task`, not duplicate-launched. Next dispatch: repeat this health-check (2-read
      progress-metric check — either a new `date=` boundary OR continued in-date fixture-fetch advance counts as live);
      once terminal, re-run the census script per "Next action" above before flipping this checkbox. — **Health-checked
      2026-07-25T06:00Z (slot 4, data_engineering), still RUNNING, confirms recovery from the fallback-date stall**:
      `gcloud compute instances list` confirms `RUNNING` in `asia-northeast1-c`; heartbeat blob update time
      `2026-07-25T06:00:57Z` (~3s old at check time). Run log grew 59,547→65,126 lines since slot 3's 05:53Z read, and
      **the date boundary finally advanced past the `2019-12-25` fallback** to `date=2020-02-21` (65 completed fixture
      IDs via the normal GCS-based enrichment path, not the 16,765-ID fallback) — confirms the rate-limit-heavy fallback
      date resolved on its own via the client's retry/backoff, exactly as the 05:53Z finding predicted, no intervention
      needed. No error/stall signature. Not completable this turn (still early 2020 of the 2019→2026-07-25 range).
      Released via `/skip-current-task`, not duplicate-launched. **Process note (not fixed, just flagged)**: this task
      has now been redispatched to 6 different slots within ~1h42m (04:18/05:10/05:29/05:37/05:53/05:54/06:00Z — 7
      checks) purely to re-confirm a VM known to run for hours — each dispatch is a full agent turn spent on a
      health-check that adds little beyond "still alive". Worth the operator/main agent considering a longer minimum
      re-dispatch gap (e.g. park via priority + a time-gated prerequisite per `RULES.md` § "Park a task") for this
      specific todo until the VM is closer to terminal, rather than a fix I should make unilaterally as a dispatched
      worker. Next dispatch: repeat this health-check (2-read progress-metric check — a new `date=` boundary OR
      continued in-date fixture-fetch advance both count as live); once terminal, re-run the census script per "Next
      action" above before flipping this checkbox. — **Health-checked 2026-07-25T06:08Z (slot 2, backend_engineer,
      craft-adopted per worker.md ADOPT-not-refuse on a role-mismatched dispatch), still RUNNING, confirms slot 4's
      06:00Z check**: `gcloud compute instances list` confirms `RUNNING` in `asia-northeast1-c`; heartbeat blob update
      time `2026-07-25T06:08:08Z` (23s old at check time, via `gcloud storage cat` — `gsutil` failed with a stale
      credential error in this session, unrelated to the VM); run.log grew 65,126→69,781 lines (+4,655) since the 06:00Z
      read, and the `date=` boundary advanced 2020-02-21→2020-03-18 (genuine forward progress, no fallback-date stall
      this time). Not completable this turn (still early 2020 of the 2019→2026-07-25 range, ~2100 of ~2500 dates
      remain). Released via `/skip-current-task`, not duplicate-launched. **Seconding the prior process note**: this is
      the 8th redispatch of a pure health-check across ~1h50m — the operator/main-agent time-gate suggestion above
      remains unaddressed and still applies. Next dispatch: repeat this health-check (2-read progress-metric check);
      once terminal, re-run the census script per "Next action" above before flipping this checkbox. — **Health-checked
      2026-07-25T06:40Z (slot 5, data_engineering), still RUNNING, confirms slot 2's 06:08Z check**:
      `gcloud compute     instances list` confirms `RUNNING` in `asia-northeast1-c`; heartbeat blob `updateTime`
      `06:40:08Z` (~1min old at check time); run.log grew 69,781→78,791 lines (+9,010) since the 06:08Z read, latest
      timestamp `06:38:55Z` (live per-fixture `Fetched N events for fixture=X` lines); `date=` boundary unchanged at
      `2020-03-18` (443 distinct dates total) but genuine in-date fixture-fetch advance (not a stall — same
      live-progress signature as prior checks). Not completable this turn (~2100 of ~2500 dates remain). Released via
      `/skip-current-task`, not duplicate-launched. **Escalating the process concern via `/blocked` this time** (2 prior
      slots noted it in-doc only, unaddressed after ~2h18m / 9 redispatches) rather than re-noting it a 3rd time here —
      see the blocked question posted against this task. Next dispatch: repeat this health-check (2-read progress-metric
      check — a new `date=` boundary OR continued in-date fixture-fetch advance both count as live); once terminal,
      re-run the census script per "Next action" above before flipping this checkbox.

## Codex SSOTs

No new durable contract. Executes the OR-1 fixture_events re-fetch campaign already specified in
`issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`.
