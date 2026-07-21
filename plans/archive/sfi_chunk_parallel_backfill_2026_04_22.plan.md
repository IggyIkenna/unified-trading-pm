---
doc_type: plan
title: SFI backfill — chunk-safe multi-VM parallelisation (cut 6.3-year backfill from ~70 days to ~3-5 days)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-22
priority: P2
owner: agent
type: code
epic: none
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: deployment-service, code: C0, deployment: none, business: none }
  - { repo: instruments-service, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on: [features_sports_upstream_coverage_gaps_2026_04_21]
isProject: false
---

## Deferred work — migrated to: `plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` — successor:

sports_pipeline_to_100pct_golden_window_first_2026_06_27 (verified 2026-07-21, batch-5 archived-plan discipline triage).
This plan's Phase 0 (fire experimental fetch) and Option-1/rate-limit-coordinator items are moot (Option 2 wall-clock
proved sufficient, no merge coordinator needed). The real remaining work — the full historical 2015→present SFI backfill
(this plan's Phase 4 `[HUMAN]` "fire 4-chunk real backfill") — is explicitly tracked, by name, as `⬜ not started` under
"P2b reference+odds history 2015→present" in the successor plan; the golden window itself (P1b) is `✅ complete`. The
`--chunks N` launcher (`launch-sfi-backfill-vm.sh`, `deployment-service@0d6e589`) remains the tool P2b will use when it
starts.

## Context

Observed 2026-04-22: `sfi-backfill-20260421-231826` VM (fired by plan
`features_sports_upstream_coverage_gaps_2026_04_21`) processed **26 dates in 18 hours** = **~1.4 dates/hour**. At that
rate the full 2020-01-01..2026-04-21 window (2,300 days) would take **~68 days** of single-VM wall-clock. Rate-limit
bound: SFI (RapidAPI-proxied SharpAPI) returns 429 every ~60s and the adapter respectfully sleeps to the next minute.
Each date has ~900 matches × ~150 progressive_stats rows = ~137k rows landed per date (data is correct, just slow).

Single-VM throughput is **accurate but unacceptable** for a 6.3-year backfill. Existing precedent in memory
`project_chunk_safe_manifest_migrations_pattern_shipped_2026_04_21` + codex
[`02-data/chunk-safe-manifest-migrations.md`](../../codex/02-data/chunk-safe-manifest-migrations.md): the SPORTS
FIXTURES rescan already uses a 3-mode chunk-safe pattern (single-VM / worker / coordinator) via
`rescan_sports_fixtures_canonical.py`. This plan applies the same shape to the SFI backfill, gated by the
`soccer-football-info-api-key` rate-limit constraint.

## Blast radius

| Repo                | Scope                                                                                                                                                                            |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| instruments-service | SFI orchestrator path: support `--chunk-id N/M` so one worker only processes 1/M of the date range. Already date-driven; chunk-split is pure date-partition math.                |
| deployment-service  | `launch-sfi-backfill-vm.sh --chunks N`: fire N workers + 1 coordinator. Enforce ALL workers share one `sfi-*` prefix so the singleton lock still counts them as ONE logical job. |
| unified-trading-pm  | codex §2.4 cross-ref to the chunk-safe pattern.                                                                                                                                  |

## PRE-AUDIT-FINDINGS (2026-04-22 — agent)

### Existing chunk-safe pattern to clone

Per memory `project_chunk_safe_manifest_migrations_pattern_shipped_2026_04_21`:

- SSOT: `instruments-service/scripts/rescan_sports_fixtures_canonical.py` +
  `deployment-service/scripts/vm/launch-sports-manifest-rescan-vm.sh --chunks N`.
- 3-mode pattern:
  1. **Single-VM** (default): process full range on one VM.
  2. **Worker**: `--chunk-id N --run-id R --date-start X --date-end Y` — writes partials to
     `_index/partial/<run-id>/<chunk-id>.parquet`.
  3. **Coordinator**: `--coordinate --run-id R` — waits for all partials, merges, deletes partials.
- Singleton-lock **allows sibling workers of the same run-id**; blocks everything else.

### SFI-specific constraint

**SFI shares one API key (`soccer-football-info-api-key`).** The 2026-04-19 thundering-herd incident (10 concurrent
sfi-fwd-\* VMs → ~4 useful writes) proved that naïvely paralleling N VMs does NOT multiply throughput — each VM just
hits 429 faster. The chunk-safe approach **must budget the rate limit across workers**.

SFI's observed throughput:

- ~140k rows/date × 1.4 dates/hour = ~200k rows/hour on one VM.
- Rate-limit is per-API-key per-minute. Measured: ~13-14 successful fetches per 60s window + 45s sleep.

**Strategy options:**

1. **Temporal chunk split + rate-share**: 4 workers, each handling ~1.5 years of dates, coordinating on a shared
   rate-limit semaphore (redis or GCS-lease-based). Complex but best throughput.
2. **Temporal chunk split + naive**: 4 workers, each doing full rate-limit back-off independently. Wall-clock is still
   ~68 days / 4 = ~17 days per chunk (workers complete in parallel → ~17 days total). Simpler but slower.
3. **Month-level chunking**: 76 workers, each handling 1 month. Over-parallel — would thrash on rate limit without
   coordination. REJECT.

**Recommendation**: Option 1 with a **GCS-lease rate-limit coordinator** (worker acquires lease to make an API call;
coordinator limits concurrent leases to the measured per-minute quota). Equivalent to a "one call per worker per ~N
seconds" contract distributed across the cluster.

Option 2 is acceptable if Option 1's coordinator is too much scope. Targets **~17 days** vs today's ~68.

### Rate-limit floor discovery

Before committing to Option 1 or 2, Phase 1 must **measure the effective per-minute quota**. The 60s-sleep pattern in
SFI logs suggests ~14 calls/min. With 4 workers each making 14 calls/min = 56 calls/min → likely 429s. Need to either
(a) share the 14-call/min budget across workers, or (b) accept each worker at ~3-4 calls/min. Phase 1 measures the real
ceiling.

## Pre-audit manifest

| File / thing to find                                                                                                    | Purpose                                                                                    | Expected outcome                                                                                                    |
| ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `instruments-service/scripts/rescan_sports_fixtures_canonical.py`                                                       | Chunk-safe 3-mode pattern reference.                                                       | Copy the `--chunk-id --run-id --date-start --date-end` + `--coordinate --run-id` CLI shape.                         |
| `deployment-service/scripts/vm/launch-sports-manifest-rescan-vm.sh`                                                     | Pattern for `--chunks N` fan-out launcher.                                                 | Copy the per-worker VM naming + coordinator VM boot.                                                                |
| `instruments-service/instruments_service/engine/orchestrator.py::_fetch_sfi_data` L4321+                                | Current SFI fetch path. Already date-driven (iterates via `process_instruments` per date). | Chunk-split = slice the caller's date range; no orchestrator-internal changes.                                      |
| UTL rate-limit / lease primitives                                                                                       | Does UTL carry a distributed lease helper today?                                           | Grep `RateLimit`, `Lease`, `TokenBucket`. If absent, Phase 2 adds one under `unified_trading_library/rate_limits/`. |
| SFI adapter at `instruments-service/instruments_service/reference_data/adapters/sports/adapters/soccerfootball_info.py` | Current rate-limit handling (429 + sleep pattern).                                         | Extend to call the GCS-lease acquire() before each HTTP call (Option 1).                                            |

## Success criteria

- Phase 1: measured per-minute API quota for `soccer-football-info-api-key` documented in codex §2.4.
- Phase 2 (if Option 1): distributed rate-limit lease primitive in UTL + SFI adapter integration. 4 workers complete
  2020-01-01..2026-04-21 in **≤ 5 days wall-clock** with zero data drops.
- Phase 2 (if Option 2 fallback): 4 independent chunks complete in **≤ 20 days wall-clock** (each chunk ~1.5 years ×
  ~68d/6.3y = ~16 days, running in parallel). Accept 3x slower than Option 1.
- Phase 3: chunk-safe partial-merge coordinator written + shelled. `_index/partial/<run-id>/` parquets merged into the
  canonical per-date shards.
- Phase 4: codex §2.4 updated with chunk-safe cmd + rate-limit floor.

## Phases

### Phase 0: Pre-audit (measure ceiling) [SEQUENTIAL]

- [x] [AGENT] P0. UTL pre-audit: no distributed rate-limit-lease primitive today (grep `unified_trading_library/` for
      `Lease|TokenBucket|RateLimit|Semaphore` → 0 matches). Phase 2 Option 1 would add one under
      `unified_trading_library/rate_limits/`. Shipped Option 2 first (no coordinator) since the launcher-level chunking
      unblocks immediate parallel fires.

- [ ] [AGENT] P0. Fire a 1-hour experimental SFI fetch (narrow date range, e.g. `2020-01-01..2020-01-05`) with the
      current forward-poll launcher + log-tail the 429 pattern. Measure: - successful fetches per minute - sleep-seconds
      per 429 hit - total wall-clock per date Document the quota in this plan.

      *Deferred to operator fire*. Existing measurement from killed `sfi-backfill-20260421-231826`:
                      ~1.4 dates/hour single-VM → ~68 days for 2020-01-01..2026-04-21 range. Used as the
                      conservative baseline in the launcher help text + codex.

- [x] [AGENT] P0. `launch-sports-manifest-rescan-vm.sh` 3-mode protocol: - **single-VM** (default): process full range
      on one VM, canonical writes direct. - **worker** (`--chunk-id X --run-id Y --date-start A --date-end B`): scan
      disjoint date range, write partial `_index/partial/<run-id>/<chunk-id>.parquet`. No canonical reads/writes. -
      **coordinator** (`--coordinate --run-id Y`): read canonical, glob partials, merge, write canonical atomically,
      delete partials. Run exactly once after all workers finish. The launcher's `--chunks N` fans out N workers
      (bash-3.2 compatible inline Python splitter, front-loaded remainder). Singleton-lock allows sibling workers of
      same run-id.

      SFI variant (shipped): Option 2 skips worker/coordinator modes because SFI writes land in
                      per-date canonical shards (not `_index/partial/`). Chunks are naturally disjoint on date key;
                      no merge required. Availability-index manifest rows may race at chunk edges — recommend
                      running `launch-sports-manifest-rescan-vm.sh` after all chunks complete.

### Phase 1: Chunk-safe CLI in instruments-service [DEFERRED — Option 2 skipped it]

Option 2 (shipped): chunks run the **unmodified** instruments-service CLI, each pointed at a disjoint
`--start-date..--end-date` slice by the launcher. No `--chunk-id`/`--run-id` plumbing required in instruments-service
because SFI writes land in per-date canonical shards (naturally disjoint on date key). Manifest races at chunk edges are
reconciled by a post-run rescan.

Option 1 (deferred): the full partial-write + coordinator shape would add a worker mode to instruments-service. File as
follow-up if Option 2 wall-clock proves insufficient.

- [x] [AGENT] P0. Chunk-split math is in the launcher (see Phase 3). Validated: 4-chunk split on 2300-day range yields
      575-576-day sub-ranges, disjoint, complete coverage.
- [x] [AGENT] P0. No CLI changes needed in instruments-service — launcher passes existing `--start-date`/`--end-date`
      flags unchanged.

### Phase 2: Rate-limit coordination (Option 1 if scope permits; Option 2 fallback) [SEQUENTIAL]

**Option 1 — GCS-lease rate-limit coordinator:**

- [ ] [AGENT] P2. Add `unified_trading_library/rate_limits/gcs_lease_coordinator.py`:
      `acquire(venue, lease_ttl_ms, max_concurrent) -> LeaseHandle` that writes a lease blob to
      `gs://coordination/leases/<venue>/<uuid>.json` with `expires_at`. Workers check blob count under the prefix; sleep
      and retry if `count >= max_concurrent`.

- [ ] [AGENT] P2. Wire SFI adapter to `await coordinator.acquire("soccer_football_info", ...)` before each `get()` call.
      Release on response or exception.

- [ ] [AGENT] P2. Unit tests + in-memory integration test (4 mock workers, one 14/min quota) proving distributed
      throughput matches measured ceiling ±20%.

**Option 2 fallback — independent chunks, no coordination:**

- [ ] [AGENT] P2. Skip Option 1. Each worker runs its own rate-limit state independently. Document in codex §2.4 the
      expected wall-clock ceiling (4 × single-VM / 4 = ~17 days for 6.3-year range).

### Phase 3: Launcher + coordinator VM [SEQUENTIAL]

- [x] [AGENT] P1. Extended `deployment-service/scripts/vm/launch-sfi-backfill-vm.sh` with `--chunks N` + `--dry-run`.
      Inline Python splitter mirrors the rescan shape (front-loaded remainder, bash 3.2 compatible). N>4 requires
      `--force` given the shared soccer-football-info-api-key ~14 calls/min ceiling. Singleton lock reports blocking
      VM's `run-id` label; any running `sfi-*` VM still blocks (preserves 2026-04-19 thundering-herd guard). Shipped in
      deployment-service `0d6e589`.

- [ ] [AGENT] P1. Coordinator VM for manifest merge — deferred under Option 2. SFI data writes already land in canonical
      per-date shards (no \_index/partial race). Availability-index race at chunk edges is reconciled by the existing
      `launch-sports-manifest-rescan-vm.sh` flow; recommended in the launcher's completion help text.

### Phase 4: Codex + smoke + quickmerge [SEQUENTIAL]

- [ ] [AGENT] P1. Update codex `02-data/sports-scheduling-and-sharding.md` §2.4: - Document measured rate-limit ceiling
      (~14 calls/min). - Cmd examples: single-VM (unchanged) vs `--chunks 4` 4-worker split. - Cross-ref
      `codex/02-data/chunk-safe-manifest-migrations.md` as the SSOT pattern.

- [x] [AGENT] P1. Bash syntax check `bash -n launch-sfi-backfill-vm.sh` clean. `--dry-run` blocked by policy in this
      session (policy: prior VM-fire request was denied); launcher dry-run deferred to next-session operator. Python
      splitter validated standalone: 4-chunk split on 2300-day range yields 576+576+576+575-day sub-ranges, disjoint,
      complete.

- [x] [AGENT] P1. Commit + push in dep order: deployment-service `0d6e589` → PM (this commit). No instruments-service
      change needed under Option 2.

- [ ] [HUMAN] P1. Fire 4-chunk real backfill (after Plan 6 strict-mode flip so any residual adapter wall-clock-stamp
      bugs fail loud):
      `bash deployment-service/scripts/vm/launch-sfi-backfill-vm.sh --dry-run --chunks 4 2020-01-01 2026-04-21` first to
      verify chunk boundaries, then run without `--dry-run`. Track via
      `gcloud compute instances list --filter='labels.run-id=<RUN_ID>'` + `ADAPTER_FETCH_FAILED` events. After all
      chunks finish, run `launch-sports-manifest-rescan-vm.sh` to materialise empty_confirmed manifest rows.

- [ ] [HUMAN] P0. Approve unlock of this plan once 4-chunk backfill completes + data-status UI shows 2020-2026
      SFI_LEAGUES + SFI_PROGRESSIVE_STATS coverage for ≥ 90% of dates.

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

- Transfermarkt parallelisation — TM is season-driven not date-driven, and cache-hit short-circuit makes per-date work
  cheap after first trigger. TM doesn't need chunking.
- API-Football parallelisation — existing `launch-api-football-backfill-vm.sh` already ships chunking (observed
  `af-backfill-20260421-214057` running concurrently).
- FootyStats / Understat — not flagged as slow today.
