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
    /plans/archive/issues/sports_fixture_events_phantom_manifest_rows_2026_07_25.md,
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

**DEDUP NOTE (2026-07-25T06:44Z, slot 5, per main's ruling on `BLK-26dd0ee7`):** this section's own `- [ ]` checkbox
below was being independently derived into a SECOND AO-dispatchable task (`sports_fixture_events_refetch_progress-001`)
tracking the SAME VM as the parent plan's own todo (`sports_satellite_ao_dispatch_batch2-011`) — two separate
fleet-cooldown counters redundantly health-checking one VM, doubling the redispatch churn main flagged (9 redispatches
in ~2h18m). De-duped by converting this line to plain status prose (no longer `- [ ]`, so `regen_backlog_from_plan.py`'s
`_UNCHECKED_RE` stops deriving a task from it — confirmed via `task_still_dispatchable()` in
`server/regen_backlog_from_plan.py:1099`, which orphans a task once its brief no longer matches an open checkbox). The
parent plan's own todo (`sports_satellite_ao_dispatch_batch2-011`) remains the SINGLE dispatch point; it already
references this issue doc for full resume detail. Any slot currently holding the now-orphaned
`sports_fixture_events_refetch_progress-001` is unaffected until its next `/skip` or `/done` (the orphan check re-reads
this file at that point, per design — not a mid-flight yank). **Also**: `server/auto_park.py` already implements exactly
the auto-park-after-N-redispatches mechanism main asked for (`dispatch_cooldown_auto_park_skip_threshold=3`, default) —
it just never armed because every prior `/skip-current-task` call on this task omitted `reason_code` (defaults to
`"OTHER"`, which `server/routes/slots_ops.py`'s cooldown gate explicitly excludes — only `BLOCKED`/`PARKED`/`GATED`
count). **Next dispatch: pass `{"reason_code": "GATED"}` in the `/skip-current-task` body** (task is genuinely gated
behind the external VM, not undoable) so the existing cooldown/auto-park machinery actually engages after 3 more
qualifying skips — no new orchestrator code needed, this was a call-site gap, not a missing feature.

Status (tracked solely via the parent plan's `sports_satellite_ao_dispatch_batch2-011` todo — see the DEDUP NOTE above):
Launch the fixture_events canonical re-fetch (command above) once the af-backfill singleton lock clears, then re-census
to verify convergence, then flip the parent todo's checkbox in `sports_satellite_ao_dispatch_batch2_2026_07_24.md` with
the re-census evidence. (repo: instruments-service). **Done when**: re-fetch VM completes, and a full re-census shows 0
genuinely non-canonical FIXTURE_EVENTS objects remaining (or each remaining one is documented as unrecoverable). —
**LAUNCHED 2026-07-25T03:22Z (slot 4, data_engineering), NOT complete.** Lock cleared when `af-backfill-20260725-002739`
(INJURIES catch-up) self-terminated cleanly (`exit_code=0`, confirmed via its run.log `DEPLOYMENT_COMPLETED`) — checked
`status=RUNNING` filter first, genuinely clear, no `--force`/`--skip-lock` needed. Launched
`af-backfill-20260725-032253` with the exact command above; verified DEPLOYMENT_STARTED + live progress within ~4min (no
fire-and-forget): run.log shows
`Recovery mode: promoting redo_all=True ... recovery_fixture_ids     has 16765 af_fixture_ids` (matches this doc's
16,777 count, minor variance expected) and real per-date `entity=FIXTURE_EVENTS` enrichment fetches starting 2019-01-20.
**Stale-tarball check performed before trusting the launch** (launcher warned 4 tarballs stale): instruments-service was
missing exactly 1 commit (`450b1b58`, an unrelated FIXTURES_SCHEDULE empty-gap-emission fix, not FIXTURE_EVENTS);
unified-api-contracts missing exactly 1 commit (a Central Asia league-registry addition, irrelevant to re-fetching
already-known `af_fixture_id`s); unified-trading-library and deployment-service were actually current (false-positive
staleness warning) — none of the gaps affect this campaign's correctness. Full run will take hours (2019→ present,
16,765 fixtures); not completable this turn. Next dispatch: health-check
`gcloud compute instances list --filter='name~"^af-backfill-20260725-032253"'` +
`gs://deployment-scripts-central-element-323112/vm-logs/af-backfill-20260725-032253/run.log` before assuming still
running; once terminal, re-run the census script per "Next action" above before flipping this checkbox. —
**Health-checked 2026-07-25T04:18Z (slot 11, data_engineering), still RUNNING**: heartbeat blob
(`vm-heartbeat/af-backfill-20260725-032253.txt`) fresh (31s old at check time); run.log date-progressed
2019-01-03→2019-12-24 between two checks ~6min apart, monotonic, no error/stall signature. Not completable this turn
(genuinely hours from done, 2019→2026-07-25 range). Released via `/skip-current-task`, not duplicate-launched. Next
dispatch: repeat this health-check; once terminal (`exit_code=0`/`DEPLOYMENT_COMPLETED`, self-deleted), re-run the
census script per "Next action" above before flipping this checkbox. — **Health-checked 2026-07-25T05:10Z (slot 3,
data_engineering), still RUNNING**: `gcloud compute instances list` confirms `RUNNING` in `asia-northeast1-c`; run.log
timestamps continuous up to 05:09:45 (30s before check, live process, not stalled); 359 distinct `date=` markers seen
since the 03:22:53 launch, currently on `2019-12-25`. **Efficiency finding, not blocking**: 2 of the 359 dates so far
(`2019-12-24`, `2019-12-25`) hit a
"`Per-fixture GCS skip: no GCS fixtures for date=X — using 16765 recovery IDs directly`" fallback — when a date has no
GCS-cached fixture list, the script falls back to attempting ALL 16,765 recovery fixture IDs against that single date
instead of just the handful that actually played that day. `date=2019-12-24` alone took ~66min (03:53:41→05:00:02) under
this fallback vs. seconds for a normal date. At the observed ~0.6% fallback-date rate this could add several hours
across the full 2019→2026 range — real but not correctness-affecting (every real fixture still gets fetched exactly once
via the allowlist filter, just slower on affected dates); not something to intervene on mid-run. Not completable this
turn (2141 of ~2500 dates remain even ignoring further fallback hits). Released via `/skip-current-task`, not
duplicate-launched. Next dispatch: repeat this health-check (2-read progress-metric check, not single-snapshot); once
terminal, re-run the census script per "Next action" above before flipping this checkbox. If the fallback-date rate
turns out much higher than 0.6% over a longer observation window, consider filing a separate perf follow-up issue doc
for the launcher/enrichment script (out of scope for this todo — do not fix mid-flight on a running prod VM). —
**Health-checked 2026-07-25T05:29Z (slot 4, data_engineering), still RUNNING**: `gcloud compute instances list` confirms
`RUNNING` in `asia-northeast1-c`; heartbeat blob `vm-heartbeat/af-backfill-20260725-032253.txt` Update Time
`2026-07-25T05:30:01Z` (fresh, ~1min old at check time); run.log last line `05:27:24Z` (~2min old), live per-fixture
`Fetched N events for     fixture=X` lines interleaved with the expected 429-rate-limit sleep/retry cycling — no
error/stall signature. Distinct `date=` count unchanged at 359 (still `2019-12-25`) since the 05:10Z check — confirmed
this is the SAME known fallback-date pattern (not a stall): `date=2019-12-25` hit
"`Per-fixture GCS skip: no GCS fixtures for     date=2019-12-25 — using 16765 recovery IDs directly`" at `05:00:02Z`,
~30min into its own ~66min-per-fallback-date budget (matching `2019-12-24`'s measured 66min) — genuine in-date progress
(fixture fetches actively advancing within the date), just no NEW date boundary crossed yet, exactly as the
fallback-rate finding predicted. Not completable this turn (~2140 of ~2500 dates remain). Released via
`/skip-current-task`, not duplicate-launched. Next dispatch: repeat this health-check (2-read progress-metric check —
either a new `date=` boundary OR continued in-date fixture-fetch advance counts as live); once terminal, re-run the
census script per "Next action" above before flipping this checkbox. — **Health-checked 2026-07-25T05:37Z (slot 3,
data_engineering), still RUNNING, confirms slot 4's 05:29Z check**: run.log grew 47,010→55,413 lines since the 05:10Z
read, latest timestamp 05:37:48 (live); still the same `date=2019-12-25` fallback (37min in of its ~66min budget), no
stall. Released via `/skip-current-task` again, no new finding. — **Health-checked 2026-07-25T05:53Z (slot 3,
data_engineering), still RUNNING, new finding**: log growing (59,547 lines), heartbeat at 05:51:24Z (~2min old, live);
still `date=2019-12-25` (359 distinct dates unchanged). **New**: log now shows
`429 Rate limited ... sleeping 60s to next minute` retries against `v3.football.api-sports.io/fixtures/events` —
API-Football rate-limiting has kicked in on this date's 16,765- fixture fallback burst, which explains why `2019-12-25`
is running noticeably longer than `2019-12-24`'s ~66min (each 429 costs a 60s sleep on top of the normal per-fixture
call). Not correctness-affecting (the client's own retry/backoff handles it, per the `attempt 1/10` counter), but pushes
the total ETA further out — worth knowing if a future health-check sees this date still running well past 66min, that's
the rate-limit cost accumulating, not a new stall. Released via `/skip-current-task` again. — **Health-checked
2026-07-25T05:54Z (slot 12, data_engineering), still RUNNING, confirms slot 3's concurrent 05:53Z check**:
`gcloud compute instances list` confirms `RUNNING` in `asia-northeast1-c`; heartbeat blob fresh (~14s old at check
time); run.log grew 55,413→60,162 lines (+4,749) since the 05:37Z read, latest timestamp `05:53:49` (live per-fixture
`Fetched N events for fixture=X` lines); still `date=2019-12-25` (~74min into its own ~66min fallback-date budget —
consistent with slot 3's just-logged 429-rate-limit finding explaining the overrun, not a new stall), no
`DEPLOYMENT_COMPLETED`/`exit_code` terminal marker. Not completable this turn (still ~2140 of ~2500 dates remain).
Released via `/skip-current-task`, not duplicate-launched. Next dispatch: repeat this health-check (2-read
progress-metric check — either a new `date=` boundary OR continued in-date fixture-fetch advance counts as live); once
terminal, re-run the census script per "Next action" above before flipping this checkbox. — **Health-checked
2026-07-25T06:00Z (slot 4, data_engineering), still RUNNING, confirms recovery from the fallback-date stall**:
`gcloud compute instances list` confirms `RUNNING` in `asia-northeast1-c`; heartbeat blob update time
`2026-07-25T06:00:57Z` (~3s old at check time). Run log grew 59,547→65,126 lines since slot 3's 05:53Z read, and **the
date boundary finally advanced past the `2019-12-25` fallback** to `date=2020-02-21` (65 completed fixture IDs via the
normal GCS-based enrichment path, not the 16,765-ID fallback) — confirms the rate-limit-heavy fallback date resolved on
its own via the client's retry/backoff, exactly as the 05:53Z finding predicted, no intervention needed. No error/stall
signature. Not completable this turn (still early 2020 of the 2019→2026-07-25 range). Released via `/skip-current-task`,
not duplicate-launched. **Process note (not fixed, just flagged)**: this task has now been redispatched to 6 different
slots within ~1h42m (04:18/05:10/05:29/05:37/05:53/05:54/06:00Z — 7 checks) purely to re-confirm a VM known to run for
hours — each dispatch is a full agent turn spent on a health-check that adds little beyond "still alive". Worth the
operator/main agent considering a longer minimum re-dispatch gap (e.g. park via priority + a time-gated prerequisite per
`RULES.md` § "Park a task") for this specific todo until the VM is closer to terminal, rather than a fix I should make
unilaterally as a dispatched worker. Next dispatch: repeat this health-check (2-read progress-metric check — a new
`date=` boundary OR continued in-date fixture-fetch advance both count as live); once terminal, re-run the census script
per "Next action" above before flipping this checkbox. — **Health-checked 2026-07-25T06:08Z (slot 2, backend_engineer,
craft-adopted per worker.md ADOPT-not-refuse on a role-mismatched dispatch), still RUNNING, confirms slot 4's 06:00Z
check**: `gcloud compute instances list` confirms `RUNNING` in `asia-northeast1-c`; heartbeat blob update time
`2026-07-25T06:08:08Z` (23s old at check time, via `gcloud storage cat` — `gsutil` failed with a stale credential error
in this session, unrelated to the VM); run.log grew 65,126→69,781 lines (+4,655) since the 06:00Z read, and the `date=`
boundary advanced 2020-02-21→2020-03-18 (genuine forward progress, no fallback-date stall this time). Not completable
this turn (still early 2020 of the 2019→2026-07-25 range, ~2100 of ~2500 dates remain). Released via
`/skip-current-task`, not duplicate-launched. **Seconding the prior process note**: this is the 8th redispatch of a pure
health-check across ~1h50m — the operator/main-agent time-gate suggestion above remains unaddressed and still applies.
Next dispatch: repeat this health-check (2-read progress-metric check); once terminal, re-run the census script per
"Next action" above before flipping this checkbox. — **Health-checked 2026-07-25T06:40Z (slot 5, data_engineering),
still RUNNING, confirms slot 2's 06:08Z check**: `gcloud compute     instances list` confirms `RUNNING` in
`asia-northeast1-c`; heartbeat blob `updateTime` `06:40:08Z` (~1min old at check time); run.log grew 69,781→78,791 lines
(+9,010) since the 06:08Z read, latest timestamp `06:38:55Z` (live per-fixture `Fetched N events for fixture=X` lines);
`date=` boundary unchanged at `2020-03-18` (443 distinct dates total) but genuine in-date fixture-fetch advance (not a
stall — same live-progress signature as prior checks). Not completable this turn (~2100 of ~2500 dates remain). Released
via `/skip-current-task`, not duplicate-launched. **Escalating the process concern via `/blocked` this time** (2 prior
slots noted it in-doc only, unaddressed after ~2h18m / 9 redispatches) rather than re-noting it a 3rd time here — see
the blocked question posted against this task. Next dispatch: repeat this health-check (2-read progress-metric check — a
new `date=` boundary OR continued in-date fixture-fetch advance both count as live); once terminal, re-run the census
script per "Next action" above before flipping this checkbox. — **Health-checked 2026-07-25T06:48Z (slot 9,
data_engineering), still RUNNING, confirms slot 5's 06:40Z check**: `gcloud compute instances list` confirms `RUNNING`;
heartbeat blob updateTime `06:47:21Z` (~42s old); run.log grew 78,791→81,332 lines (+2,541) since the 06:40Z read,
latest timestamp `06:46:55Z` (live); `date=` boundary unchanged at `2020-03-18` (443 distinct dates, same as 06:40Z) —
genuine in-date advance, no stall, no error/ terminal marker. Not completable this turn. **Not re-escalating the
redispatch-frequency concern** — already raised via `/blocked` by slot 5 at 06:40Z and still pending an operator/main
answer; releasing quietly. Next dispatch: repeat this health-check; once terminal, re-run the census script per "Next
action" above before flipping this checkbox. — **Health-checked 2026-07-25T07:30Z (slot 6, data_engineering), still
RUNNING, confirms slot 9's 06:48Z check**: `gcloud compute instances list` confirms `RUNNING` in `asia-northeast1-c`;
heartbeat blob updateTime `07:30:37Z` (~28s old at check time, via `gcloud storage cat` — `gsutil` again failed with a
stale credential error in this session, same known unrelated issue slot 2 hit); run.log grew 81,332→93,609 lines
(+12,277) since the 06:48Z read, and the `date=` boundary advanced `2020-03-18`→`2020-03-19` (444 distinct dates total,
genuine forward progress, no fallback-date stall); latest tail lines show live per-fixture
`Fetched N events for fixture=X` interleaved with `429` rate-limit sleep/retry cycling, no
`DEPLOYMENT_COMPLETED`/`exit_code` terminal marker anywhere in the log (`grep -c` = 0). Not completable this turn (still
~2079 of ~2500 dates remain). **Not re-escalating the redispatch-frequency concern** — slot 5's 06:40Z `/blocked` is
still the open ask (this is now the 11th health-check redispatch across ~3h08m); releasing quietly via
`/skip-current-task {"reason_code": "GATED"}` per the DEDUP NOTE above so the auto-park cooldown machinery can engage.
Next dispatch: repeat this health-check (2-read progress-metric check — a new `date=` boundary OR continued in-date
fixture-fetch advance both count as live); once terminal, re-run the census script per "Next action" above before
flipping this checkbox. — **🔴 Health-checked 2026-07-25T08:34Z (slot 7, data_engineering), CRITICAL — not a routine
health-check, a live data-correctness incident**: `date=` boundary stuck at `2020-03-22` (447 distinct dates, unchanged
in-window); `run.log` showed the VM's API-Football key hit its **DAILY** request quota at exactly `08:12:00Z`
(`{'errors': {'requests': 'You have reached the request limit for the day...'}}`, 8,534 repeats 08:12-08:34Z, **zero**
successful `Fetched N ... for fixture=X` lines in that window — a genuine zero-forward-progress stall, not the
per-minute `429`/`rateLimit` sleep-retry pattern every prior check saw). Traced root cause in
`instruments-service/reference_data/adapters/sports/adapters/api_football.py`: all 4 per-fixture methods
(`get_fixture_statistics`/`get_fixture_events`/`get_fixture_lineups`/`get_fixture_player_stats`) swallow ANY exception
(including this hard, non-`rateLimit` failure — `is_rate_limit=False`, already re-raised immediately by
`_fetch_and_extract` per its own docstring) and `return []`. Because `sports_reference_fixtures.py`'s
`_gather_per_fixture_rows._fetch_one` is the ONLY place that increments `entity_failures`, and the exception never
reaches it, `_handle_empty_fixture_entity` takes the "legitimate empty" branch and stamps affected leagues
`EXPECTED_NO_FIXTURE`/`empty_confirmed` — silently corrupting every date this VM processes past 08:12Z, and (unverified
scope) potentially historical runs that hit any prior hard-failure class on these 4 entities.

Full writeup + fix scope: `issues/api_football_per_fixture_hard_failure_silently_recorded_empty_2026_07_25.md`
(`unified-trading-pm@9022488a2`, PR #1492). Filed `/blocked` `BLK-78a76a51` (this todo's own genuine judgment call —
stop the VM now vs leave running); **main ruled A — stop now** (SPOT+idempotent; empty_confirmed is worse than
attempted_failed since downstream won't retry it). **Fix shipped**: `instruments-service@f31fb2e9` — the 4 adapters now
re-raise after `_emit_fetch_failed`; 4 unit tests updated to expect the raise
(`test_get_fixture_{statistics,events,lineups,player_stats}_error_propagates`, mirroring the existing
`get_injuries_error_propagates` precedent); full `quality-gates.sh` green; verified the ALREADY-correct
`TestCF11PerFixtureEntityFailurePath` orchestrator suite now actually gets exercised end-to-end (previously it only
tested the orchestrator's handling of a mock that raised — the real adapter never did). **I could not execute the VM
stop myself**: `gcloud` auth expired mid-session on both available accounts
(`Unable to retrieve Identity Pool subject token: job is already completed`; non-interactive reauth impossible) —
flagged via `/progress` for another slot/main to run
`gcloud compute instances stop af-backfill-20260725-032253 --zone asia-northeast1-c`.

**Next dispatch (updated — supersedes the "repeat health-check" instruction above)**: (1) confirm the VM was actually
stopped (`gcloud compute instances list --filter='name~"^af-backfill-20260725-032253"'` should show `TERMINATED` or
absent); if still `RUNNING`, execute the stop. (2) Do NOT relaunch until the API-Football daily quota has reset
(unverified reset time — check account status or a lightweight `/status` call before relaunching). (3) On relaunch, the
fixed adapter code (`f31fb2e9`+) makes hard failures correctly `attempted_failed`, so a normal re-run will now retry
them instead of silently skipping — no separate relabeling step should be needed for genuinely NEW runs, but the window
this VM already wrote between `08:12Z` and its stop time was written under the OLD buggy code and must be treated as
suspect (re-fetch, don't trust its `empty_confirmed` cells at face value in the eventual re-census). (4) Only once the
VM reaches a genuine terminal state under the fixed code should the "Next action" census script re-run and this checkbox
flip.

**Update 2026-07-28 — operator decision received: relaunch now.** Rather than trying to precisely reconstruct the exact
suspect date-boundary (the run.log shows the `date=` pointer stuck at `2020-03-22` for the whole 08:12-08:34Z quota
window, but the exact first/last corrupted row isn't cheaply provable from the log alone), relaunched with `--force`
(redo_all=True) so every one of the 16,765 recovery-listed fixtures is freshly re-attempted end-to-end under the fixed
code — correctness over efficiency per the workspace's data-pipeline-correctness rule, and the API-Football account is
now confirmed on the expanded "mega plan" quota so the extra redundant work is affordable. Tarballs refreshed first
(`instruments-service@5a6deafd`, `unified-api-contracts@f3ae871c` — both confirmed "tarball fresh" by the launcher's own
freshness check at launch time, not just claimed). **New finding**: the original `2019-01-01` start date is now REJECTED
by a 2020-06-06 sports-data-floor guard in the launcher (`/codex/02-data/sports-2020-06-data-floor.md`) that either
wasn't wired in yet on 2026-07-25 or was never exercised by this specific campaign — corrected the launch to start
`2020-06-06` (pre-floor 2019 dates are fabrication-by-construction and were already wiped from GCS/manifest elsewhere,
so recovery-listed fixture_ids before the floor, if any, are expected to no-op harmlessly). Launched
`af-backfill-20260728-141821`
(`--force --entity FIXTURE_EVENTS --recovery-fixture-ids gs://deployment-scripts-central-element-323112/sports_fixture_events_refetch_2026_07_25/recovery_fixture_ids.parquet 2020-06-06 2026-07-25`)
— monitoring to completion. Once terminal, re-run the census script per "Next action" above before flipping the parent
todo's checkbox.

**Update 2026-07-25 (later same session) — VM stop confirmed; quota concern resolved differently than expected; relaunch
still PENDING an operator decision.** (1) The gcloud auth-expiry blocker above is now root-caused + fixed — see
`issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md` (a shared-runner WIF credential poisoning the
orchestrator VM's active gcloud account, third occurrence of a known class). VM stop executed + confirmed `TERMINATED`
from a separate, working gcloud session. (2) Operator reports the API-Football account is now on a "mega plan" with more
credits/quota — checked `api_football.py::get_live_quota`: the adapter reads the plan's REAL daily limit LIVE from
api-football's own `/status` endpoint on every run, superseding any hardcoded fallback, so the mega-plan upgrade needs
NO manual doc/config change — the next VM run self-discovers it. (3) **Not yet done**: tarballs have NOT been refreshed
(`create-code-tarballs.sh --asset-group SPORTS`) since `f31fb2e9` landed, so a relaunch right now would still run the
pre-fix code. (4) **Operator was asked and has not yet answered**: relaunch now (refresh tarballs then launch), or
review this todo's own relabeling scope (the `08:12Z`-onward suspect window, item 3 above) first. Whoever picks this up
next should re-ask rather than assume either direction.

## Codex SSOTs

No new durable contract. Executes the OR-1 fixture_events re-fetch campaign already specified in
`issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`.

## Todos

**DEDUP NOTE 2 (2026-07-29T09:xxZ, slot 14):** this section's `- [ ]` checkbox was re-introducing the EXACT duplicate-
dispatch bug the original DEDUP NOTE above (2026-07-25T06:44Z) already fixed once for this doc's first `## Todos`
section — a second checkbox-bearing `## Todos` header was added later (2026-07-28, on VM relaunch) and
`regen_backlog_from_plan.py` derived a second live task (`sports_fixture_events_refetch_progress-001`) tracking the SAME
VM as the parent plan's own `sports_satellite_ao_dispatch_batch2-002` todo — confirmed live: dispatched to this slot
within seconds of releasing `-002`'s own health-check. Converting to plain prose (no `- [ ]`) per the same fix, so the
parent plan's todo remains the SINGLE dispatch point. Status below unchanged, just no longer a checkbox.

[DATA] P1. **Monitor `af-backfill-20260728-141821` to completion, re-run the census script, then flip the parent plan's
checkbox** — relaunched 2026-07-28 (`--force`, `2020-06-06→2026-07-25`) under the fixed adapter code; not yet terminal.
Once done, re-run `census_fixture_events_schema_variants_2026_07_25.py` to verify convergence before flipping
`sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s `sports_satellite_ao_dispatch_batch2-002` todo. — **Health-checked
2026-07-28T15:23Z (slot 8, data_engineering), RUNNING, genuine progress**: `gcloud compute     instances list` confirms
`RUNNING` in `asia-northeast1-c`; heartbeat blob `updateTime` `15:22:50Z` (~29s old at check time); run.log shows live
per-fixture writes at `date=2020-12-16` (advanced from the `2020-06-06` start ~65min into the run), real GCS
fixture_events writes + manifest per-VM shard updates, no error/stall signature. Not completable this turn (~5.5 years
of the `2020-06-06→2026-07-25` range remain). Releasing via `/skip-current-task {"reason_code": "GATED"}` per this doc's
own DEDUP NOTE instruction, not repeating the redispatch-churn pattern already flagged above (9+ prior health-check
redispatches, unresolved `/blocked`) — not re-escalating, just complying with the documented next-action. —
**Health-checked 2026-07-28T15:55Z (slot 14, data_engineering), RUNNING, confirms slot 8's 15:23Z check**:
`gcloud compute     instances list` confirms `RUNNING`; heartbeat fresh; `date=` boundary advanced
`2020-12-16→2021-02-06` (~32min gap, genuine forward progress), live per-fixture fetches + normal rate-limit sleep/retry
cycling, no error/stall/terminal marker. Not completable this turn (~5.4 years remain). Releasing via
`/skip-current-task {"reason_code": "GATED"}`, same as slot 8. — **Health-checked 2026-07-28T19:31Z (slot 6,
data_engineering), RUNNING, confirms slot 9's 17:45Z check on the parent plan's own tracker (date=2021-09-15→
2021-09-26)**: `gcloud compute instances list` confirms `RUNNING` in `asia-northeast1-c`; heartbeat blob `updateTime`
`19:27:49Z` (fresh); 2-read progress-metric check over ~5min: run.log grew 75,747→76,291 lines (+544), `date=` boundary
advanced `2022-03-11→2022-03-13`, live per-fixture `Fetched N events for fixture=X` lines + normal rate-limit
sleep/retry cycling, `grep -c 'DEPLOYMENT_COMPLETED\|exit_code'` = 0 (no terminal marker). Genuine forward progress, no
stall. Not completable this turn (~4.3 years of the `2020-06-06→     2026-07-25` range remain). Releasing via
`/skip-current-task {"reason_code": "GATED"}`, not duplicate-launched. Next dispatch: repeat this health-check (2-read
progress-metric check — a new `date=` boundary OR continued in-date fixture-fetch advance both count as live); once
terminal (`DEPLOYMENT_COMPLETED`/`exit_code` marker, VM self-deleted/TERMINATED), re-run
`census_fixture_events_schema_variants_2026_07_25.py` (full, no `--limit`) before flipping
`sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s `sports_satellite_ao_dispatch_batch2-011` todo. — **Health-checked
2026-07-29T00:41Z-00:43Z (slot 6, data_engineering), RUNNING, confirms slot 14's 15:55Z check on 2026-07-28**: heartbeat
blob `updateTime` `2026-07-29T00:43:23Z` (fresh, `gcloud compute instances list` unavailable this check — active gcloud
account lacked `compute.instances.list` on this project, an account-permission gap unrelated to the VM itself;
heartbeat + run.log growth already establish liveness independently). 2-read progress-metric check over ~2min: run.log
grew 149,361→149,572 lines (+211), `date=` boundary advanced `2023-10-01→2023-10-03`, live per-fixture
`Fetched N events for fixture=X` lines + normal rate-limit sleep/retry cycling + a fresh `PIPELINE_HEARTBEAT` line at
`00:42:06Z`, `grep -c 'DEPLOYMENT_COMPLETED\|exit_code'` = 0 (no terminal marker). Genuine forward progress, no stall.
Not completable this turn (~3.2 years of the `2020-06-06→2026-07-25` range remain). Releasing via
`/skip-current-task {"reason_code": "GATED"}`, not duplicate-launched. Next dispatch: repeat this health-check (2-read
progress-metric check); once terminal, re-run the census script per "Next action" above before flipping this checkbox +
the parent todo. — **Health-checked 2026-07-29T03:49Z-03:53Z (slot 5, data_engineering), RUNNING, confirms slot 6's
00:41Z-00:43Z check**: `gcloud compute instances list` initially failed with a `compute.instances.list` permission gap
on the active `github-deploy` account (same WIF-poisoning class as
`issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`) — fixed in-session by switching to
`unified-trading-sa` per the RULES.md self-service-grant rule (an ambient identity switch, not a new grant), which then
confirmed `RUNNING` in `asia-northeast1-c`. 3-read progress-metric check over ~4min: heartbeat blob fresh at every read
(03:50:02Z, 03:51:04Z, 03:53:08Z, all <30s old at check time); run.log grew 194,345→195,178→195,670 lines; `date=`
boundary advanced `2024-09-19→2024-09-23→2024-09-28`, live per-fixture `Fetched N ... for date=X` + `GCS fixture lookup`
lines, no error/stall signature; `grep -c DEPLOYMENT_COMPLETED` = 0 at every read. **Tooling note (not a VM issue)**: an
earlier automated polling script transiently reported a false `TERMINAL_DETECTED` on an intermediate read whose backing
log file was never actually written to disk — re-verified directly against a fresh `gcloud storage cat` immediately
after and found zero genuine `DEPLOYMENT_COMPLETED`/`exit_code` occurrences anywhere in the log; the VM's own
`gcloud compute instances list` status (`RUNNING`) is the authoritative signal and was checked directly, not inferred
from the flaky script. Genuine forward progress, no stall. Not completable this turn (~1.9 years of the
`2020-06-06→2026-07-25` range remain, currently at `2024-09-28`). Releasing via
`/skip-current-task {"reason_code": "GATED"}`, not duplicate-launched. Next dispatch: repeat this health-check (2-read
progress-metric check — a new `date=` boundary OR continued in-date fixture-fetch advance both count as live); once
terminal (`DEPLOYMENT_COMPLETED`/`exit_code` marker, VM self-deleted/TERMINATED), re-run
`census_fixture_events_schema_variants_2026_07_25.py` (full, no `--limit`) before flipping this checkbox +
`sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s `sports_satellite_ao_dispatch_batch2-011` todo. — **Health-checked
2026-07-29T03:53Z-03:55Z (slot 10, data_engineering), RUNNING, confirms slot 5's 03:53Z check**:
`gcloud compute instances list` (via `unified-trading-sa`, already active) confirms `RUNNING` in `asia-northeast1-c`.
2-read progress-metric check over ~2min: heartbeat blob fresh at both reads (`updateTime` 03:54:10Z and 03:55:12Z, both
<1min old at check time); run.log grew 195,670→196,432 lines (+762); `date=` boundary advanced `2024-09-28→2024-10-01`,
live per-fixture `Fetched N events for fixture=X` +
`Recovery-mode merge for fixture_events/league=... : N existing rows + M new = T total` writes, no error/stall
signature; `grep -c 'DEPLOYMENT_COMPLETED\|exit_code'` = 0 at the second read. Genuine forward progress, no stall. Not
completable this turn (~1.8 years of the `2020-06-06→2026-07-25` range remain, currently at `2024-10-01`). Releasing via
`/skip-current-task {"reason_code": "GATED"}`, not duplicate-launched. Next dispatch: repeat this health-check (2-read
progress-metric check — a new `date=` boundary OR continued in-date fixture-fetch advance both count as live); once
terminal (`DEPLOYMENT_COMPLETED`/`exit_code` marker, VM self-deleted/TERMINATED), re-run
`census_fixture_events_schema_variants_2026_07_25.py` (full, no `--limit`) before flipping this checkbox +
`sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s `sports_satellite_ao_dispatch_batch2-011` todo. — **Health-checked
2026-07-29T05:00Z (slot 10, data_engineering), RUNNING, confirms this same slot's 03:53Z-03:55Z check**:
`gcloud compute instances list` confirms `RUNNING` in `asia-northeast1-c`; heartbeat blob `updateTime` `05:00:12Z` (~25s
old at check time). Progress-metric check vs. the 03:55Z read: run.log grew 196,432→211,257 lines (+14,825) over ~65min;
`date=` boundary advanced `2024-10-01→2025-01-17` (~3.5 months forward progress), live per-fixture
`Fetched N events for fixture=X` writes + normal rate-limit sleep/retry cycling, no error/stall signature;
`grep -c 'DEPLOYMENT_COMPLETED\|exit_code'` = 0 (no terminal marker). Genuine forward progress, no stall. Not
completable this turn (~1.5 years of the `2020-06-06→2026-07-25` range remain, currently at `2025-01-17`). Releasing via
`/skip-current-task {"reason_code": "GATED"}`, not duplicate-launched. Next dispatch: repeat this health-check (2-read
progress-metric check — a new `date=` boundary OR continued in-date fixture-fetch advance both count as live); once
terminal (`DEPLOYMENT_COMPLETED`/`exit_code` marker, VM self-deleted/TERMINATED), re-run
`census_fixture_events_schema_variants_2026_07_25.py` (full, no `--limit`) before flipping this checkbox +
`sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s `sports_satellite_ao_dispatch_batch2-011` todo. — **Health-checked
2026-07-29T08:59Z-09:01Z (slot 14, data_engineering), RUNNING, confirms slot 10's 05:00Z check — substantial progress**:
`gcloud compute instances     list` confirms `RUNNING` in `asia-northeast1-c`; heartbeat blob `updateTime` fresh at both
reads (`08:59:01Z` and `09:01:05Z`, ~2min apart matching the poll gap). 2-read progress-metric check: run.log grew
290,437→291,522 lines (+1,085) over ~2min; `date=` boundary unchanged at `2026-05-15` across both reads (no new date
boundary crossed in this short window, but genuine in-date fixture-fetch advance — live per-fixture
`Fetched N events for fixture=X` lines at both reads, same pattern as every prior live check, not a stall). **Notably
close to done now**: only ~2 months of the `2020-06-06→2026-07-25` range remain (down from ~1.5 years at the 05:00Z
check ~4h ago) — `grep -c 'DEPLOYMENT_COMPLETED\|exit_code'` = 0 at both reads (no terminal marker yet). Not completable
this turn. Releasing via `/skip-current-task {"reason_code": "GATED"}`, not duplicate-launched. Next dispatch: repeat
this health-check soon — at the observed pace this VM may reach terminal within the next few checks; once terminal,
re-run `census_fixture_events_schema_variants_2026_07_25.py` (full, no `--limit`) before flipping this checkbox +
`sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s `sports_satellite_ao_dispatch_batch2-002` todo. — **Health-checked
2026-07-29T14:14Z-14:17Z (slot 6, data_engineering), RUNNING but a NEW finding — genuine stall in useful progress,
different in kind from every prior check above**: `gcloud compute instances list` (via the ambient
`github-actions-deploy` account, which worked fine this check) confirms `RUNNING` in `asia-northeast1-c`; heartbeat blob
fresh at both reads (`14:14:58Z` and (epoch) `1785334620` ≈ `14:17:00Z`, ~2min apart matching the poll gap). 2-read
progress-metric check over ~3min: run.log grew 444,341→447,410 lines (+3,069), but **`date=` boundary UNCHANGED at
`2026-07-12` since `13:45:03Z` (~32min before my first read, ~35min total by my second)** — unlike the 09:01Z check's
"no new date but genuine in-date advance" caveat, here the growth is **100%
`ADAPTER_FETCH_FAILED venue=api_football ... You have reached the request limit for the day` pairs** (47,604 occurrences
at my second read, up from 44,562 at the first) — **zero** successful `Fetched N events for fixture=X` lines since
`13:14:43Z` (confirmed via `grep` on both log snapshots), i.e. a full **~1h+ of zero real forward progress**, not the
slow-but-genuine advance every prior check documented. This is the account's DAILY quota being hit (not the per-minute
429 rate-limit sleep/retry cycling seen in every earlier check) — the loop is NOT sleeping/backing off, it is spinning
through the 16,765-fixture recovery list for `date=2026-07-12` at full speed with every single call failing.
**Reassurance this is NOT a repeat of the 2026-07-25T08:12Z incident**: that incident's bug (hard failures silently
swallowed as `empty_confirmed`) is the one `instruments-service@f31fb2e9` fixed — here every failure surfaces as a
genuine `ERROR ... recovery=fail_fast` (the fixed code path), so no false-positive `capture_status` should be getting
written for `date=2026-07-12`; it simply isn't advancing until the vendor's daily quota resets.
`grep -c 'DEPLOYMENT_COMPLETED\|exit_code'` = 0 (no terminal marker; process has not crashed/exited, it is looping).
**Did NOT stop the VM** — SPOT VM billing is time-based regardless of call volume, so spinning vs. idling costs the
same, and GCS recovery-mode re-derives remaining fixture-ids from `date=` state on any restart, so a stop+relaunch buys
nothing until the vendor quota clears anyway; stopping is a judgment call better made by whoever next confirms this has
run for many more hours with zero recovery. Only ~13 days (`2026-07-12`→`2026-07-25`) remain in the whole
`2020-06-06`→`2026-07-25` range. Not completable this turn. Releasing via `/skip-current-task {"reason_code": "GATED"}`,
not duplicate-launched, not stopped. **Next dispatch: check whether the quota has reset and `date=` has advanced past
`2026-07-12` with fresh `Fetched N events` lines resuming — if STILL stuck at `2026-07-12` with zero successful fetches
many hours from now (i.e., this finding persists past a plausible quota-reset window), that is worth a `/blocked` to the
operator/main about whether to stop-and-wait-for-reset vs. let it keep spinning, since at that point it stops being
'nearly done, just waiting' and starts being a genuine multi-day stall.**

**Update 2026-07-29T15:00Z-15:10Z (interactive session, operator-present) — VM stopped+deleted; NEW lightweight VM-free
quota-check method found; confirmed still exhausted.** Independently reached the same "spinning uselessly" conclusion as
slot 6's 14:14Z finding (date= stuck, 100% quota-failure growth) and stopped+deleted `af-backfill-20260728-141821`. Per
this doc's own prior note, stop/restart doesn't save SPOT billing — but two probe relaunches
(`af-backfill-20260729-155012` — errored before VM creation, harmless; `af-backfill-20260729-155246` — DID launch,
confirmed `f31fb2e9` corruption-fix ancestor-present despite a stale-tarball warning for an unrelated CI commit, also
hit the same quota wall within ~2min, stopped+deleted) established that even the base `/status` read and
`entity=fixtures` ensure-call are now failing too — the exhaustion is total, not scoped to just `fixture_events` calls.
**New finding, useful for all future checks**: the launcher's own live-quota read (lines ~324-349 of
`launch-api-football-backfill-vm.sh`) is a standalone `gcloud secrets versions access --secret=api-football-api-key`

- `curl .../status` call — no VM needed to check current quota state. Direct probe:
  `curl -fsS -H "x-apisports-key: $(gcloud secrets versions access latest --secret=api-football-api-key --project=central-element-323112)" https://v3.football.api-sports.io/status`
  — an `errors.requests` field in the response means still exhausted; a `response.requests.{limit_day,current}` pair
  means reset (recompute remaining = limit_day - current). Confirmed still exhausted at 15:09Z via this method (zero VM
  cost). No VM currently running; will relaunch WITHOUT `--force` (normal skip-if-fresh run — the fixed code correctly
  recorded today's failures as `attempted_failed`, which a plain re-run will naturally retry, so a second `--force`
  redo-all is unnecessary and wasteful) once this probe shows quota restored. Monitoring via the VM-free probe on an
  hourly cadence rather than repeated VM launches. Releasing, not duplicate-launched, VM confirmed absent (not just
  stopped — deleted, per the singleton lock's RUNNING-status check).

**Checked 2026-07-29T15:22Z (slot 15, data_engineering)**: ran the same VM-free `/status` probe — still exhausted
(`errors.requests: "You have reached the request limit for the day..."`). Only 13 min since the 15:09Z probe, no reset
expected on that cadence; no VM launched (none needed for this check). Not a new data point, just confirms nothing has
changed since the last entry. Releasing via `/skip-current-task {"reason_code": "GATED"}`, respecting the established
hourly probe cadence rather than re-checking again immediately. Next dispatch: re-probe once ~1h has elapsed since the
15:09Z check (i.e. not before ~16:09Z), or sooner only if there's reason to think the vendor's reset window is closer.

**Checked 2026-07-29T20:14Z (slot 4, data_engineering)**: ran the same VM-free `/status` probe (well past the 16:09Z
next-check window, ~5h05m since the 15:09Z probe) — still exhausted, identical `errors.requests` payload. Also
independently confirmed via `gcloud compute operations list` (before finding this doc) that
`af-backfill-20260728-141821` was `stop`ped at `07:47:44-07:00` (=`14:47:44Z`) then `delete`d at `07:48:59-07:00`
(=`14:48:59Z`), both by the ambient compute default SA — consistent with this doc's own 15:00Z-15:10Z note that the
interactive operator session did the stop+delete (not a watchdog reap or a code bug); no new information there, just
independent corroboration of an already-documented action. **Sharpening the reset estimate**: the launcher's own comment
(`launch-api-football-backfill-vm.sh:88-89`) documents the daily quota as resetting `00:00 UTC` — so the real earliest
useful re-probe time is **`2026-07-30T00:00Z`** (~3h45m from this check), not just "another hourly probe" which will
predictably still read exhausted until then. No VM launched (none needed/useful pre-reset). Releasing via
`/skip-current-task {"reason_code": "GATED"}`. Next dispatch: do not bother re-probing before `2026-07-30T00:00Z`; once
past that time, re-probe once, and on a clean (non-`errors`) response relaunch WITHOUT `--force` per the 15:00Z-15:10Z
note (plain skip-if-fresh re-run — the fixed adapter code already correctly recorded `2026-07-12`'s failures as
`attempted_failed`, so a normal run retries them naturally; only ~13 days of the `2020-06-06→2026-07-25` range remain).
