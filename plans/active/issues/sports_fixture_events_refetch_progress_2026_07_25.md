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
      self-deleted), re-run the census script per "Next action" above before flipping this checkbox.

## Codex SSOTs

No new durable contract. Executes the OR-1 fixture_events re-fetch campaign already specified in
`issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`.
