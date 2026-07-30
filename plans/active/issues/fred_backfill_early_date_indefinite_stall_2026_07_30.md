---
doc_type: issue
title:
  "FRED full-history backfill hangs indefinitely on the first chunk — reproducible on BOTH 1962-01-02 and 1970-01-01, no
  retry/error log ever fires, exceeds the adapter's own bounded-retry design by 2x+ before being killed"
summary: >-
  Discovered 2026-07-30 (slot 6) while launching the FRED macro backfill (instruments-service#macro_micro_econ_data
  ...capture_audit-003) after fixing an unrelated calendar-exemption bug (unified-api-contracts@6d87d95e, verified
  working via a --year 2024 smoke test). The FULL production launch (--start-floor 1962-01-02, the honest-coverage
  floor) stalls indefinitely on the very first chunk (1962-01-02..01-08): CPU drops to ~0% within 30s of starting and
  never recovers, with zero forward progress (no captured/skip/error log line for the venue) for 7+ minutes before being
  killed. Reproduced 3/3 times, including with --start-floor 1970-01-01 (ruling out 1962-01-02 specifically as the
  trigger). Crucially, FredAdapter's own bounded retry-with-backoff logic (3 attempts, 60s aiohttp timeout each, ~3min
  theoretical worst case) NEVER fires — no "transient error...retrying" warning, no ADAPTER_FETCH_FAILED event — meaning
  the hang is INSIDE a single fetch attempt, not being caught/retried at all. The 2024 --year smoke test (all dates
  within every series' valid range) worked perfectly (27 real rows in ~70s). No code fix attempted — this needs live
  process inspection (py-spy/strace, or added debug logging) beyond what GCS-log/serial-console observation from a
  worker slot can provide.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [fred, tradfi, backfill, stall, hang, aiohttp, dns, macro, data-correctness-adjacent]
related:
  [
    /plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
priority: P1
parent_epic: mtds_mdps_master
source: "macro_micro_econ_data_capture_audit-003, slot 6, escalation-continuation from agt-765e33"
execution_scope: orchestrator-agent
drift_direction: advance-code
assigned_role: data_engineering
assigned_vm: planning
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

# FRED full-history backfill hangs indefinitely on the first chunk

## What I found

Reproduced live, 3 separate VM launches, all identical symptom:

| VM                                    | `--start-floor`       | Result                                                   |
| ------------------------------------- | --------------------- | -------------------------------------------------------- |
| `tradfi-bf-fred-full-20260730-020236` | 1962-01-02 (default)  | CPU 72.6%→0.0% at t+30s; 0 progress after 7+ min; killed |
| `tradfi-bf-fred-full-20260730-021518` | 1962-01-02 (default)  | Identical pattern; 0 progress after 3m42s; killed        |
| `tradfi-bf-fred-full-20260730-022323` | 1970-01-01 (explicit) | Identical pattern; 0 progress after ~1min; killed        |

Every run: `--- Chunk 1/N: <floor> → <floor+7d> ---` prints, then the standard bootstrap logs
(`DomainValidationService`, `ResourceProfiler`, `ApiKeyReloader`, `ManifestReader: consolidated blob age...`,
`registered deployment...`) complete normally within ~5s, CPU spikes briefly (72-80%, consistent with the
`tradfi_catalog_reader` load + initial async setup), then drops to 0.0-0.2% and **stays there** — no
`StreamingParquetWriter: uploaded...` line (the per-series success marker), no `Skipping N venue(s)...` (the pre-flight
non-trading-day skip — moot here since 1962/1970 dates aren't holidays), no `Pre-flight: venue=FRED date=... skipping`
(the already-captured skip), no `SHARD_INCOMPLETE` warning, and critically **no
`FredAdapter: %s transient error [%s] (attempt %s/%s) — retrying in %.2fs` warning and no `ADAPTER_FETCH_FAILED` event**
— meaning `_fetch_fred_raw`'s own `except (aiohttp.ClientError, TimeoutError)` handler is never triggered.

The outer VM liveness (heartbeat blob, `PIPELINE_HEARTBEAT` lines from the vm-life-emitter, and the lightweight
`ResourceProfiler`'s 30s `RESOURCE_SAMPLE` lines) all continue ticking normally the entire time — this is NOT a full
process/VM hang, only the `mtds_chunk_loop.sh` → MTDS download-orchestration's fetch path for FRED specifically.

## What this rules out

- **Not the holiday-calendar bug I just fixed** (`unified-api-contracts@6d87d95e`) — that bug caused an INSTANT
  wrong-but-fast skip (`EXPECTED_HOLIDAY` stamped in <1s); this is a genuine multi-minute-plus hang with zero output.
- **Not sequential-vs-concurrent series fetching** — confirmed `_umi_fred.py::fetch_fred_series` uses
  `asyncio.gather(*(_fetch_one_series(...) for entry in KEY_SERIES))`, genuine concurrency across all 29 series.
- **Not date-specific to 1962-01-02** — reproduced identically starting from 1970-01-01 too.
- **Not the adapter's own documented retry/backoff bound** — `_FRED_MAX_RETRIES=3`, `_FRED_BACKOFF_FACTOR_S=1.0`,
  `_FRED_MAX_BACKOFF_S=30.0`, `create_aiohttp_session(timeout=60)` (a `aiohttp.ClientTimeout(total=60)`, covering
  connect+read) → theoretical worst case per series ≈ 3×60s + 1s + 2s ≈ 183s (~3min), run CONCURRENTLY across series
  (bounded by the single slowest chain, not summed). All 3 observed hangs exceeded this by 1.2-2.3x before being killed,
  with ZERO indication any retry cycle ever started.
- **Not a full VM/process deadlock** — the outer heartbeat + resource-profiler threads keep emitting on schedule the
  entire time, meaning the Python process is alive and the GIL isn't held continuously.
- **Not the 2024 smoke-test path** — `tradfi-bf-fred-2024-20260730-014447` (same code, same VM template, same day after
  the calendar fix landed) fetched 2024-01-04 successfully: 27 real rows across 27 partitions in ~70s total,
  `complete=True`. The ONLY variable that differs between the working and failing cases is which historical dates are
  being requested: 2024 (every series has real data) vs 1962/1970 (most of the 29 series predate their own coverage
  start — VIXCLS started 1990, SOFR 2018, etc.; only DGS-Treasury-family series realistically have depth to 1962).

## Working hypothesis (UNCONFIRMED — needs live process inspection)

The absence of ANY retry-warning or `ADAPTER_FETCH_FAILED` log line, combined with the aiohttp `ClientTimeout(total=60)`
apparently not firing even after 3-7+ minutes, points at something upstream of (or not covered by) that timeout:

- `create_aiohttp_session()` (`market_interface/adapters/defi/utils.py:107`) uses
  `aiohttp.TCPConnector(resolver=ThreadedResolver())` specifically to work around a macOS DNS issue. `ThreadedResolver`
  offloads DNS lookups to a thread pool; if that DNS lookup itself hangs (e.g. a resolver quirk specific to this GCE VM
  template/zone, or FRED's API host resolving inconsistently), it is NOT obviously guaranteed to respect
  `aiohttp.ClientTimeout` the same way an in-loop socket read would — this is a plausible, not confirmed, explanation.
- Alternatively: FRED's REST API may respond unusually (very large body, malformed payload, or a genuinely slow
  response) for a query whose date range predates a series' actual valid start, and something in the response-handling
  path (`await resp.json()` or downstream parsing) hangs on that specific shape rather than the connection itself timing
  out.

Neither is confirmed. This needs either `py-spy dump`/`gdb` against a live repro (SSH into a freshly-launched repro VM
while it's stuck) or added granular logging (`logger.info` immediately before/after `_ensure_session()`,
`session.get(...)`, and `await resp.json()`) redeployed and re-run to pinpoint the exact stuck line — bounded, not
attempted this session (backend-engineer/deeper-debugging scope, not a one-shot data_engineering task).

## Why it matters

- Blocks the actual deliverable of `macro_micro_econ_data_capture_audit_2026_06_05.md`'s
  `macro_micro_econ_data_capture_audit-003` todo ("Run the FRED backfill") for the full intended `1962-01-02..today`
  depth — the calendar-exemption fix is real, verified, and necessary but not sufficient; the launch itself cannot
  complete past its very first chunk.
- The affected window is specifically "dates before most of FRED's 29 series have real data" — likely the 1960s-1980s
  range given series start dates vary (DGS-Treasury family from 1962, several macro/inflation series from the 1940s-50s,
  but VIXCLS/SOFR/T10Y-spread family series are much newer). Once past that window (exact boundary unknown — needs the
  fix + a bounded probe to determine), the backfill likely behaves like the working 2024 case.
- Not itself a data-correctness issue (no wrong rows get written — the process just never produces a result for that
  chunk), but it silently consumes SPOT-VM compute indefinitely if not caught (exactly the "no fire-and-forget / verify
  T+10min" class of problem the workspace's own VM-launcher HARD RULE exists to catch — caught here precisely because
  that rule was followed).

## Recommended next steps

- [ ] [BACKEND] P1. Launch a fresh repro VM (`launch-tradfi-bf-fred.sh --start-floor 1962-01-02`), SSH in once the hang
      reproduces (CPU flat ~30s after chunk start), and get a live stack trace of the stuck `mtds_chunk_loop.sh` Python
      process (`py-spy dump --pid <pid>` or `py-spy dump --pid <pid> --locals` if installed, else attach
      `gdb     -p <pid>` + `py-bt`) to identify the exact stuck call (DNS resolution vs socket read vs response parsing
      vs something else entirely). Repo: market-tick-data-service (diagnosis only, no code change yet).
- [ ] [BACKEND] P1. Once the stuck call is identified: if it's `ThreadedResolver`-related, either swap to the default
      asyncio resolver (the macOS-specific issue it was added for is irrelevant on the Linux GCE VM template) or wrap
      the resolution itself in an explicit `asyncio.wait_for(..., timeout=N)`. If it's response-handling related, add
      defensive `resp.content.read(max_bytes=...)` bounding or a request-level explicit `asyncio.wait_for` wrapping the
      whole `_fetch_fred_raw_once` call so a hang anywhere inside it is force-cancelled and correctly routed through the
      EXISTING retry/backoff path (which already works correctly — it just never gets a chance to run). Repo:
      market-tick-data-service.
- [ ] [DATA] P2. Once fixed: determine the actual "most series have real data from here" boundary date via a bounded
      probe (e.g. `--start-floor 1980-01-01`, `--start-floor 1990-01-01` smoke tests), then relaunch the full
      `1962-01-02..today` production backfill, verify early progress past the fixed window, and flip
      `macro_micro_econ_data_capture_audit-003`'s checkbox with the VM name + verified evidence — per that todo's own
      done_definition, still outstanding.
- [ ] [TEST] P3. Add a regression test asserting `FredAdapter.fetch_series()` (or `_fetch_fred_raw`) completes within a
      bounded wall-clock time even when mocked to simulate FRED returning data for an out-of-range/pre-series-start date
      — so this class of hang is caught in CI rather than only discoverable via a live 64-year production launch. Repo:
      market-tick-data-service.

## Evidence log

- 3 VM launches + serial-console + `run.log` (GCS-teed stdout) + `vm-heartbeat` blob observation, this session,
  2026-07-30T02:02-02:23Z (see timestamps in the table above).
- Code read: `market_tick_data_service/market_interface/adapters/tradfi/fred_adapter.py` (retry constants, timeout,
  `_fetch_fred_raw`/`_fetch_fred_raw_once`), `market_tick_data_service/adapters/_umi_fred.py` (`asyncio.gather`
  confirmed), `market_tick_data_service/market_interface/adapters/defi/utils.py:107`
  (`create_aiohttp_session`/`ThreadedResolver`).
- Working comparison case: `tradfi-bf-fred-2024-20260730-014447` run.log, `2026-07-30T01:51:22-01:51:55Z` (27 rows,
  `complete=True`, ~70s total for the date).

## Progress Log

- **2026-07-30 (slot 6, macro_micro_econ_data_capture_audit-003 continuation)**: filed after 3 reproduced hangs across 2
  different start-floor dates. Diagnosis bounded to what a worker slot can observe from GCS logs + serial console (no
  direct SSH/py-spy access exercised this session — flagged as the next todo's exact starting point rather than guessed
  at). The unrelated calendar-exemption bug that motivated this launch attempt (`unified-api-contracts@6d87d95e`) is
  separately confirmed fixed and verified — this doc is scoped to the NEW, distinct stall discovered while trying to
  actually run the now-correctly-scoped backfill.
