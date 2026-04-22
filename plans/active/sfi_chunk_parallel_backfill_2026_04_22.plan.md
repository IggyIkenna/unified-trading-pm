---
title: "SFI backfill — chunk-safe multi-VM parallelisation (cut 6.3-year backfill from ~70 days to ~3-5 days)"
priority: P2
status: active
owner: agent
created: 2026-04-22
locked_by: live-defi-rollout
locked_since: 2026-04-22
type: code
epic: none
completion_gates:
  code: C5
  deployment: none
  business: none
repo_gates:
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
depends_on: [features_sports_upstream_coverage_gaps_2026_04_21]
isProject: false
---

## Context

Observed 2026-04-22: `sfi-backfill-20260421-231826` VM (fired by plan
`features_sports_upstream_coverage_gaps_2026_04_21`) processed **26 dates in 18 hours** =
**~1.4 dates/hour**. At that rate the full 2020-01-01..2026-04-21 window (2,300 days) would take **~68 days** of
single-VM wall-clock. Rate-limit bound: SFI (RapidAPI-proxied SharpAPI) returns 429 every ~60s and the adapter
respectfully sleeps to the next minute. Each date has ~900 matches × ~150 progressive_stats rows = ~137k rows
landed per date (data is correct, just slow).

Single-VM throughput is **accurate but unacceptable** for a 6.3-year backfill. Existing precedent in memory
`project_chunk_safe_manifest_migrations_pattern_shipped_2026_04_21` + codex
[`02-data/chunk-safe-manifest-migrations.md`](../../codex/02-data/chunk-safe-manifest-migrations.md): the SPORTS
FIXTURES rescan already uses a 3-mode chunk-safe pattern (single-VM / worker / coordinator) via
`rescan_sports_fixtures_canonical.py`. This plan applies the same shape to the SFI backfill, gated by the
`soccer-football-info-api-key` rate-limit constraint.

## Blast radius

| Repo                | Scope                                                                                                                                     |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| instruments-service | SFI orchestrator path: support `--chunk-id N/M` so one worker only processes 1/M of the date range. Already date-driven; chunk-split is pure date-partition math. |
| deployment-service  | `launch-sfi-backfill-vm.sh --chunks N`: fire N workers + 1 coordinator. Enforce ALL workers share one `sfi-*` prefix so the singleton lock still counts them as ONE logical job. |
| unified-trading-pm  | codex §2.4 cross-ref to the chunk-safe pattern.                                                                                           |

## PRE-AUDIT-FINDINGS (2026-04-22 — agent)

### Existing chunk-safe pattern to clone

Per memory `project_chunk_safe_manifest_migrations_pattern_shipped_2026_04_21`:

- SSOT: `instruments-service/scripts/rescan_sports_fixtures_canonical.py` + `deployment-service/scripts/vm/launch-sports-manifest-rescan-vm.sh --chunks N`.
- 3-mode pattern:
  1. **Single-VM** (default): process full range on one VM.
  2. **Worker**: `--chunk-id N --run-id R --date-start X --date-end Y` — writes partials to
     `_index/partial/<run-id>/<chunk-id>.parquet`.
  3. **Coordinator**: `--coordinate --run-id R` — waits for all partials, merges, deletes partials.
- Singleton-lock **allows sibling workers of the same run-id**; blocks everything else.

### SFI-specific constraint

**SFI shares one API key (`soccer-football-info-api-key`).** The 2026-04-19 thundering-herd incident (10
concurrent sfi-fwd-* VMs → ~4 useful writes) proved that naïvely paralleling N VMs does NOT multiply throughput —
each VM just hits 429 faster. The chunk-safe approach **must budget the rate limit across workers**.

SFI's observed throughput:
- ~140k rows/date × 1.4 dates/hour = ~200k rows/hour on one VM.
- Rate-limit is per-API-key per-minute. Measured: ~13-14 successful fetches per 60s window + 45s sleep.

**Strategy options:**
1. **Temporal chunk split + rate-share**: 4 workers, each handling ~1.5 years of dates, coordinating on a shared
   rate-limit semaphore (redis or GCS-lease-based). Complex but best throughput.
2. **Temporal chunk split + naive**: 4 workers, each doing full rate-limit back-off independently. Wall-clock is
   still ~68 days / 4 = ~17 days per chunk (workers complete in parallel → ~17 days total). Simpler but slower.
3. **Month-level chunking**: 76 workers, each handling 1 month. Over-parallel — would thrash on rate limit
   without coordination. REJECT.

**Recommendation**: Option 1 with a **GCS-lease rate-limit coordinator** (worker acquires lease to make an API
call; coordinator limits concurrent leases to the measured per-minute quota). Equivalent to a "one call per
worker per ~N seconds" contract distributed across the cluster.

Option 2 is acceptable if Option 1's coordinator is too much scope. Targets **~17 days** vs today's ~68.

### Rate-limit floor discovery

Before committing to Option 1 or 2, Phase 1 must **measure the effective per-minute quota**. The 60s-sleep
pattern in SFI logs suggests ~14 calls/min. With 4 workers each making 14 calls/min = 56 calls/min → likely
429s. Need to either (a) share the 14-call/min budget across workers, or (b) accept each worker at ~3-4
calls/min. Phase 1 measures the real ceiling.

## Pre-audit manifest

| File / thing to find                                                                                | Purpose                                                                                       | Expected outcome                                                                                      |
| --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `instruments-service/scripts/rescan_sports_fixtures_canonical.py`                                   | Chunk-safe 3-mode pattern reference.                                                          | Copy the `--chunk-id --run-id --date-start --date-end` + `--coordinate --run-id` CLI shape.         |
| `deployment-service/scripts/vm/launch-sports-manifest-rescan-vm.sh`                                 | Pattern for `--chunks N` fan-out launcher.                                                    | Copy the per-worker VM naming + coordinator VM boot.                                                  |
| `instruments-service/instruments_service/engine/orchestrator.py::_fetch_sfi_data` L4321+            | Current SFI fetch path. Already date-driven (iterates via `process_instruments` per date).    | Chunk-split = slice the caller's date range; no orchestrator-internal changes.                       |
| UTL rate-limit / lease primitives                                                                   | Does UTL carry a distributed lease helper today?                                              | Grep `RateLimit`, `Lease`, `TokenBucket`. If absent, Phase 2 adds one under `unified_trading_library/rate_limits/`. |
| SFI adapter at `instruments-service/instruments_service/reference_data/adapters/sports/adapters/soccerfootball_info.py` | Current rate-limit handling (429 + sleep pattern).                                            | Extend to call the GCS-lease acquire() before each HTTP call (Option 1).                             |

## Success criteria

- Phase 1: measured per-minute API quota for `soccer-football-info-api-key` documented in codex §2.4.
- Phase 2 (if Option 1): distributed rate-limit lease primitive in UTL + SFI adapter integration. 4 workers
  complete 2020-01-01..2026-04-21 in **≤ 5 days wall-clock** with zero data drops.
- Phase 2 (if Option 2 fallback): 4 independent chunks complete in **≤ 20 days wall-clock** (each chunk
  ~1.5 years × ~68d/6.3y = ~16 days, running in parallel). Accept 3x slower than Option 1.
- Phase 3: chunk-safe partial-merge coordinator written + shelled. `_index/partial/<run-id>/` parquets merged
  into the canonical per-date shards.
- Phase 4: codex §2.4 updated with chunk-safe cmd + rate-limit floor.

## Phases

### Phase 0: Pre-audit (measure ceiling) [SEQUENTIAL]

- [ ] [AGENT] P0. Grep UTL for any existing rate-limit-lease / distributed-semaphore primitive. Document in this
      plan's PRE-AUDIT section.

- [ ] [AGENT] P0. Fire a 1-hour experimental SFI fetch (narrow date range, e.g. `2020-01-01..2020-01-05`) with
      the current forward-poll launcher + log-tail the 429 pattern. Measure:
      - successful fetches per minute
      - sleep-seconds per 429 hit
      - total wall-clock per date
      Document the quota in this plan.

- [ ] [AGENT] P0. Read `rescan_sports_fixtures_canonical.py` + `launch-sports-manifest-rescan-vm.sh --chunks N`.
      Diagram the 3-mode protocol (single / worker / coordinator) here for fresh-context sub-agents.

### Phase 1: Chunk-safe CLI in instruments-service [SEQUENTIAL after Phase 0]

- [ ] [AGENT] P1. Add `--chunk-id N/M` flag to `instruments_service` CLI (or extend existing `--chunks` pattern
      used by the rescan script). `N=0..M-1`; on a 2300-day range with `M=4`, chunk 0 processes days
      2020-01-01..2021-08-15, chunk 1 processes 2021-08-16..2023-03-30, etc.

- [ ] [AGENT] P1. `--run-id R` flag for correlating partial writes.

- [ ] [AGENT] P1. Worker writes per-chunk progress markers to
      `_index/partial/sfi-backfill/<run-id>/<chunk-id>.parquet` — one row per completed date with
      `capture_status`, `row_count`, `attempted_at`. Coordinator reads these to detect done.

- [ ] [AGENT] P1. Unit tests: chunk-0 of a 4-chunk split on a 20-day range processes exactly 5 dates (2020-01-01..2020-01-05),
      writes partial markers, never overlaps with chunk-1.

### Phase 2: Rate-limit coordination (Option 1 if scope permits; Option 2 fallback) [SEQUENTIAL]

**Option 1 — GCS-lease rate-limit coordinator:**

- [ ] [AGENT] P2. Add `unified_trading_library/rate_limits/gcs_lease_coordinator.py`:
      `acquire(venue, lease_ttl_ms, max_concurrent) -> LeaseHandle` that writes a lease blob to
      `gs://coordination/leases/<venue>/<uuid>.json` with `expires_at`. Workers check blob count under the
      prefix; sleep and retry if `count >= max_concurrent`.

- [ ] [AGENT] P2. Wire SFI adapter to `await coordinator.acquire("soccer_football_info", ...)` before each
      `get()` call. Release on response or exception.

- [ ] [AGENT] P2. Unit tests + in-memory integration test (4 mock workers, one 14/min quota) proving
      distributed throughput matches measured ceiling ±20%.

**Option 2 fallback — independent chunks, no coordination:**

- [ ] [AGENT] P2. Skip Option 1. Each worker runs its own rate-limit state independently. Document in codex
      §2.4 the expected wall-clock ceiling (4 × single-VM / 4 = ~17 days for 6.3-year range).

### Phase 3: Launcher + coordinator VM [SEQUENTIAL]

- [ ] [AGENT] P1. Extend `deployment-service/scripts/vm/launch-sfi-backfill-vm.sh` with `--chunks N`:
      - Without `--chunks`: current single-VM shape (unchanged).
      - With `--chunks N`: generate `run_id=<ts>-<uuid>`; fire N worker VMs + 1 coordinator VM; all VMs
        labelled `run-id=<run_id>`; singleton lock counts SAME run_id siblings as one logical job.

- [ ] [AGENT] P1. Coordinator VM polls `_index/partial/sfi-backfill/<run-id>/` for N chunk parquets;
      when all present, merges into final per-date shards + deletes partials (mirrors the rescan
      coordinator pattern).

### Phase 4: Codex + smoke + quickmerge [SEQUENTIAL]

- [ ] [AGENT] P1. Update codex `02-data/sports-scheduling-and-sharding.md` §2.4:
      - Document measured rate-limit ceiling.
      - Cmd examples: single-VM (unchanged) vs `--chunks 4` 4-worker split.
      - Cross-ref `codex/02-data/chunk-safe-manifest-migrations.md` as the SSOT pattern.

- [ ] [AGENT] P1. `bash deployment-service/scripts/quality-gates.sh` + `bash instruments-service/scripts/quality-gates.sh` green.

- [ ] [AGENT] P1. Commit + push in dep order: instruments-service → deployment-service → PM.

- [ ] [HUMAN] P1. Fire 4-chunk real backfill:
      `bash deployment-service/scripts/vm/launch-sfi-backfill-vm.sh --chunks 4 2020-01-01 2026-04-21`.
      Track via `_index/partial/sfi-backfill/<run-id>/` + `ADAPTER_FETCH_FAILED` events.

- [ ] [HUMAN] P0. Approve unlock of this plan once 4-chunk backfill completes + data-status UI shows
      2020-2026 SFI_LEAGUES + SFI_PROGRESSIVE_STATS coverage for ≥ 90% of dates.

## Dependency graph

```
Phase 0 (measure + read reference pattern) [SEQUENTIAL]
      │
      ├─► Phase 1: Chunk-safe CLI (instruments-service)   [SEQUENTIAL]
      │
      ├─► Phase 2: Rate coordination (Option 1 or 2)      [SEQUENTIAL]
      │
      ├─► Phase 3: Launcher + coordinator VM              [SEQUENTIAL]
      │
      └─► Phase 4: Codex + smoke + quickmerge + HUMAN fire + unlock
```

Sequential by dependency chain — each phase's output feeds the next.

## SSOT cross-refs

- Chunk-safe pattern: `codex/02-data/chunk-safe-manifest-migrations.md` + memory
  `project_chunk_safe_manifest_migrations_pattern_shipped_2026_04_21.md`.
- SFI rate-limit incident: memory `project_rolling_window_cli_shipped_2026_04_21.md` + codex §2.4 reference to
  2026-04-19 thundering-herd.
- Existing SFI launcher: `deployment-service/scripts/vm/launch-sfi-backfill-vm.sh` (shipped by plan
  `features_sports_upstream_coverage_gaps_2026_04_21`).

## Out of scope

- Transfermarkt parallelisation — TM is season-driven not date-driven, and cache-hit short-circuit makes
  per-date work cheap after first trigger. TM doesn't need chunking.
- API-Football parallelisation — existing `launch-api-football-backfill-vm.sh` already ships chunking
  (observed `af-backfill-20260421-214057` running concurrently).
- FootyStats / Understat — not flagged as slow today.
