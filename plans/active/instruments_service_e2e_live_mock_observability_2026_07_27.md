---
doc_type: plan
title: instruments-service E2E — live mode, mock scenarios, observability (Phases 5-7)
summary:
  Re-scoped from the never-completed Phases 5-7 of the archived 2026-03 instruments-service E2E audit
  (plans/archive/2026_07/e2e_testing_001_instruments_service_2026_03_22.md) — live-mode 15-min clock alignment,
  mock-mode failure scenarios, and observability/logging checks, none of which were ever run.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer]
tags: [e2e-testing, instruments-service, live-mode, mock-mode, observability]
related: []
created: 2026-07-27
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1
last_updated: 2026-07-27
supersedes: []
superseded_by:
locked_by:
locked_since:
depends_on:
source: [plans/archive/2026_07/e2e_testing_001_instruments_service_2026_03_22.md]
assigned_role: backend_engineer
drift_direction: none
---

# instruments-service E2E — live mode, mock scenarios, observability

## Context

The original instruments-service E2E audit (2026-03-21, archived 2026-07-27) completed Phases 1-4 plus a real 2026-03-23
DEFI-category audit that found 6 real bugs, but never ran Phases 5-7. Re-verify against current instruments-service
before assuming any of the below is still accurate — 4+ months have passed.

## Todos

- [x] ✅ [SCRIPT] P1. **Phase 5 — Live mode clock alignment. DONE 2026-07-30 (slot-15) — premise corrected + real bug
      found + fixed.** The literal command (`--operation live --mode batch --interval 15`) does not exist: `--operation`
      only accepts `instruments` (`--mode` is the batch/live selector), and `--interval` is not a flag anywhere in
      instruments-service or unified-trading-library (confirmed via `--help` + full-repo grep). Read the actual
      `--mode live` code path (`unified-trading-library/unified_trading_library/service_framework/_adapter.py:219-237`):
      it is a **one-shot, externally-triggered** run that defaults `start_date=end_date=today` and force-refreshes —
      there is no internal 15-minute wall-clock-aligned boundary-wait loop for this service (that primitive,
      `UTCAlignedScheduler`, lives in UTL's `streaming/utc_aligned_scheduler.py` and is consumed only by
      market-tick-data-service's `websocket_runner.py`). The CLI docstring's claim of "UTL ScheduledIO (wall-clock
      aligned)" is stale/aspirational — `class ScheduledIO` does not exist anywhere in the codebase. No Cloud
      Scheduler/terraform cron wires instruments-service `--mode live` to a 15-min external cadence either (only daily
      06:00/02:00 UTC crons exist) — confirmed via terraform grep. **5.1/5.2 (boundary-wait/`:00/:15/:30/:45`
      alignment): N/A, architecture doesn't implement it** — not a regression, this was never built for this service.

      **5.3/5.4 — actually run + verified** via `main_service_cli()` with `--operation instruments --mode live
                                  --asset-group cefi` under `CLOUD_MOCK_MODE=true`: confirmed `ServiceRuntime` STARTED log line, per-venue fetch
                                  logging (URDI[...] fetched N instruments across BYBIT-SPOT/COINBASE-SPOT/KRAKEN-SPOT/KRAKEN-FUTURES/
                                  LIGHTER-ZKSYNC/KALSHI-PERP/POLYMARKET-PERP/EXTENDED-STARKNET/ASTER), and defaults to today's UTC date as
                                  documented. **Real bug found + fixed**: a SIGTERM/Ctrl-C mid-run did NOT exit cleanly — `cleanup()`'s
                                  `publish_coordination_event("DATA_READY", ...)` call (instruments_handler.py:399, and the sibling
                                  `SPORTS_LIVE_STATS` call at :419) is guarded with `contextlib.suppress(RuntimeError, ValueError)` (intended to
                                  swallow the batch-mode `ValueError` `publish_coordination_event` raises when `_mode != "live"`), but in
                                  **live+`CLOUD_MOCK_MODE=true`**, UTL's `service_framework/_sink_factory.py::build_event_sink()` hands the process
                                  a plain `LocalFsEventSink` (write_event-only, no `publish_coordination_event`/`subscribe_coordination_events`) for
                                  ANY `runtime.is_mock` case regardless of batch/live mode — so the call raises `AttributeError`, which the
                                  suppress tuple didn't catch, crashing the whole shutdown with `SystemExit code=1` ("Service failed"). **Fixed**:
                                  broadened both suppress tuples to `(RuntimeError, ValueError, AttributeError)`. **Correction 2026-07-30
                                  (slot-11): the `<pending>` SHA above was never actually shipped — the suppress tuple was still
                                  `(RuntimeError, ValueError)` in the live tree when Phase 6 started, and the crash reproduced exactly
                                  as described (confirmed live: `--mode live --asset-group cefi` under `CLOUD_MOCK_MODE=true` crashed
                                  cleanup with the uncaught `AttributeError`).** Actually fixed + verified now: instruments-service@
                                  `518cc7a7` (shipped) broadens both suppress
                                  tuples; re-verified live against BYBIT-SPOT (clean cleanup, no traceback) and again via a mid-run
                                  SIGTERM against HYPERLIQUID (`SystemExit code=0`, no traceback). **Cross-cutting root
                                  cause flagged, not fixed here** (out of this plan's `repos: [instruments-service]` scope, and the shared UTL
                                  `events`/`events_interface` module pair looks like an in-progress migration — too risky to touch blind): the real
                                  fix belongs in `unified-trading-library/unified_trading_library/service_framework/_sink_factory.py` (or
                                  `event_sink.py`'s `LocalFsEventSink`) so mock+live mode gets a sink that implements the coordination-event
                                  protocol (the existing `MockEventSink` in `events/sink.py` already does, but nothing wires it into
                                  `build_event_sink()`) — every OTHER service following this same `cleanup()`+`contextlib.suppress` pattern is
                                  exposed to the identical crash. Filed:
                                  `plans/active/issues/utl_mock_mode_event_sink_missing_coordination_protocol_2026_07_30.md`.

                                  One additional, smaller finding: no per-venue `COMPLETED` UEI event exists in code (only `WRITE_FAILED`,
                                  `writers.py:429-436`) — success is implicit via a `processed`/`failed` counter dict, not a discrete event. 5.3's
                                  expectation of "per-venue COMPLETED" doesn't match the shipped event taxonomy; noted, not treated as a bug (a
                                  counter-based success signal is a legitimate design, just not what this todo assumed).

- [x] ✅ [SCRIPT] P2. **Phase 6 — Mock-mode failure scenarios. DONE 2026-07-30 (slot-11) — premise corrected (same
      pattern as Phase 5) + real bug fixed + shipped.** The literal `--scenario default/stress/missing_data` flag does
      NOT exist in this codebase (0 grep hits outside tests) — aspirational text from the March-2026 plan, never
      implemented. `--scenario` DOES exist as a real `ServiceCLI` flag but instruments-service never reads
      `runtime.scenario` — a complete no-op here. Per-item: **6.1 VERIFIED** (real
      `URDI[BYBIT-SPOT]: fetched 3314     instruments` under `CLOUD_MOCK_MODE=true`, no crash). **6.2/6.3/6.4 NOT
      DIRECTLY TESTABLE** — no volume/cardinality, mid-run-disappear, or fake-symbol-injection hook exists anywhere;
      documented as a premise gap rather than fabricated (6.3's real-world analogue, the Hyperliquid-0-instruments case,
      is the dedicated P3 "re-verify the 6 bugs" todo's job, not duplicated here — a live check attempt here was
      inconclusive, rate-limited 429s, not chased further). **6.5 VERIFIED** (`get_venues_for_asset_groups` scopes
      strictly to requested asset groups; the 6.1 run shows zero DEFI references when only cefi is requested; MTDS-side
      consumption is out of this plan's `repos: [instruments-service]` scope). **6.6 VERIFIED, premise corrected**
      (`_parse_expiry("not-a-date")` → `None` in all 3 real parsers, confirmed live — doesn't crash; but none of them
      log a warning, so "parser warns" is false, not treated as a bug). **6.7 VERIFIED via code** (`config_source` is a
      pure `is_mock` derived property; the 6.1 run's `data=mock` log line proves it). **Real bug found + genuinely
      fixed**: Phase 5's claimed `cleanup()` `AttributeError`-crash fix was never actually shipped (SHA was literally
      `<pending>` — verified: the crash still reproduced live before this fix). Actually fixed + re-verified twice
      (BYBIT-SPOT clean run + a mid-run SIGTERM against HYPERLIQUID exiting `code=0`) and shipped:
      instruments-service@`518cc7a7`. Blocked briefly on a pre-existing, unrelated repo-red (UAC@26092ac8 broke the
      sports two-registry disjoint invariant) — filed
      `plans/active/issues/instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md`, declared repo-blocker
      `RB-ecfc50de`, resolved once `unified-api-contracts` shipped the golden-fixture regen (`5f7b8136` in the rebased
      history) — full `quality-gates.sh` green, shipped clean.
- [x] ✅ [SCRIPT] P2. **Phase 7 — Observability. DONE 2026-07-30 (slot-6) — all 6 sub-checks run live against
      instruments-service, all PASS with 2 premise notes (same pattern as Phases 5/6), zero code changes needed.** Runs:
      `CLOUD_MOCK_MODE=true GCP_PROJECT_ID=mock-project .venv/bin/instruments-service --operation instruments     --mode live --asset-group cefi --venues <...> --dry-run --log-level INFO`
      (single-venue BYBIT-SPOT baseline, then multi-venue BYBIT-SPOT+HYPERLIQUID+LIGHTER-ZKSYNC, then
      BYBIT-SPOT+FAKE-EXCHANGE-SPOT for isolation), plus inspection of the mock-mode `LocalFsEventSink` jsonl
      (`.local-dev-cache/events/instruments-service.jsonl`). - **7.1 (ServiceRuntime log line, all dimensions):
      VERIFIED, premise note.** `service_runtime.py:202-211` logs
      `ServiceRuntime: op=%s mode=%s provider=%s env=%s data=%s testnet=%s dry_run=%s` — confirmed live twice (once at
      the `__bootstrap__` preliminary-mode phase, once at the real `op=instruments` phase after full arg resolution).
      This covers 7 of the dataclass's fields; `asset_group`, `scenario`, `log_level`, `requested_mode`,
      `gcp_project_id`, `storage_protocol`, `messaging_protocol`, `force`, `service_name` are NOT in this specific log
      line (though `asset_group` is separately visible via the "Venue override from CLI" line and other call sites).
      "All dimensions logged" is true for the CLI/env axes this line documents itself as covering, not literally every
      `ServiceRuntime` field — not treated as a bug (a wider log line is a legitimate but separate observability
      enhancement, out of a "verify current behavior" SCRIPT todo's scope). - **7.2 (UEI STARTED/COMPLETED/per-venue
      events): VERIFIED, premise note matching Phase 5's finding.** Confirmed via the local event sink: `STARTED` and
      `STOPPED` fire per run (service lifecycle taxonomy is STARTED/STOPPED/FAILED, not STARTED/COMPLETED — same
      correction Phase 5 already made). A domain-level `PROCESSING_STARTED` → `PROCESSING_COMPLETED` pair also fires per
      run with an aggregate `venues`/`total_records` count (not one event per venue). Per-venue signal on the SUCCESS
      path comes via `PUBLISHED_OK`/ `PUBLISHED_DEGRADED` (`completeness_fraction`, `missing: [...]` naming the absent
      venues) and `PIPELINE_HEARTBEAT` (`venues_ok` count), not a discrete "per-venue COMPLETED" event; per-venue signal
      on the FAILURE path is `ADAPTER_FETCH_FAILED` (see 7.5). Confirms + extends Phase 5's "no per-venue COMPLETED
      event" finding — the counter/completeness-fraction based design is consistent across both phases' evidence. -
      **7.3 (shard-level isolation, one venue failure doesn't crash others): VERIFIED live, two independent
      reproductions.** (a) `--venues BYBIT-SPOT HYPERLIQUID LIGHTER-ZKSYNC`: HYPERLIQUID hit real
      `429 Too Many       Requests` (classified `RATE_LIMIT`, `action=retry`, `retry_safe=true`) and retried for ~2 min
      while BYBIT-SPOT (3314 instruments) and LIGHTER-ZKSYNC (220 instruments) fetched and wrote independently; run
      finished exit=0, `Shard completeness OK: 3/3 venues written` once HYPERLIQUID's retries succeeded. (b)
      `--venues BYBIT-SPOT       FAKE-EXCHANGE-SPOT` (no registered URDI adapter for the fake venue — logged
      `No URDI adapter for 1 venue(s)`): BYBIT-SPOT still fetched + wrote (3314 instruments), run finished exit=0 with
      **no crash/traceback**, and the gap was reported honestly via
      `SHARD COMPLETENESS FAILURE date=... 1/2 venues written (50% complete)` + event-sink
      `SHARD_INCOMPLETE`/`PUBLISHED_DEGRADED` (`completeness_fraction: 0.5`, `missing:       ['FAKE-EXCHANGE-SPOT']`) —
      never a silent partial-success. Both cases confirm one venue's failure (transient or total) does not crash the
      batch; the working venues complete and the gap is surfaced, not hidden. - **7.4 (dry-run warning, "DRY RUN" + "UCI
      dry-run mode ACTIVE"): VERIFIED, exact match.** Every `--dry-run` run logged both
      `WARNING DRY RUN — no cloud writes will be performed` (`service_runtime.py:201`) and
      `WARNING UCI       dry-run mode ACTIVE — all data sinks redirected to local` (`cloud_interface/factory.py:448`). -
      **7.5 (`ADAPTER_FETCH_FAILED` classifies failed venues correctly): VERIFIED live.** The HYPERLIQUID 429 in 7.3 run
      (a) produced an `ADAPTER_FETCH_FAILED` event in the local sink:
      `{"venue": "hyperliquid", "endpoint":       "meta", "error_code": "RATE_LIMIT", "action": "retry", "retry_safe": true}`
      — correct classification via UAC's `classify_venue_error()`, matching the shard-level-failure-isolation contract
      (classify then continue, never crash the shard loop). Note: a venue with NO registered adapter at all (7.3 run
      (b)) does not emit `ADAPTER_FETCH_FAILED` (there's no fetch attempt to classify) — it surfaces via
      `SHARD_INCOMPLETE`/ `PUBLISHED_DEGRADED` instead; these are two distinct, correctly-separated failure modes
      (missing coverage vs. a failed fetch attempt), not a gap in classification. - **7.6 ("Memory watchdog started"
      logged): VERIFIED, exact match.** Every run logged
      `Memory watchdog started       for instruments-service (threshold=85.0%)` (`core/memory_monitor.py:253`) during
      `ServiceBootstrap`. - **No code changes shipped this phase** — no crash, silent placeholder, or misclassification
      found; both premise notes (7.1, 7.2) describe legitimate existing design, consistent with how Phase 5/6 treated
      equivalent gaps. Nothing to ship; this todo is evidence-only.
- [x] ✅ [VALIDATE] P3. **Re-verify the 6 bugs from the 2026-03-23 DEFI E2E audit are still real.** DONE 2026-08-01
      (slot-6) — all 6 re-verified live/via-code; **none are still real in their original form** — 0 to re-file. See
      Progress Log for full per-bug evidence.

## Progress Log

- 2026-07-27: Plan created, re-scoping the never-run Phases 5-7 out of the archived 2026-03 instruments-service E2E
  audit doc per operator decision (pre-June-1 stale-plans audit).

- **na-eligibility-audit 2026-07-30**: RECLASSIFY NA → planning — all 4 todos are bounded verification RUNS with
  explicit per-item done-when checklists (Phase 5 clock-alignment 5.1-5.4, Phase 6 mock scenarios 6.1-6.7, Phase 7
  observability 7.1-7.6, the 6-bug re-verify) — determinable by a worker alone.

- **slot-11 2026-07-30 — Phase 6 IN PROGRESS, blocked on repo-red before shipping.** Same premise-correction pattern as
  Phase 5: a literal `--scenario default/stress/missing_data` CLI flag does NOT exist anywhere in this codebase
  (confirmed via full-repo grep) — it's aspirational text carried over from the original March-2026 plan, never
  implemented. `--scenario` DOES exist as a real `ServiceCLI` flag
  (`choices=["default","stress","empty","normal", "heavy","light"]` — note `missing_data` isn't even a valid choice;
  `empty` is closest), but instruments-service never reads `runtime.scenario` (0 grep hits) — it's a complete no-op
  here. Per-item findings:
  - **6.1 (normal mock generation): VERIFIED.**
    `--operation instruments --mode live --asset-group cefi --venues BYBIT-SPOT` under `CLOUD_MOCK_MODE=true`: real
    adapter fetch (`URDI[BYBIT-SPOT]: fetched 3314 instruments`), `LocalFsEventSink` local writes, no crash (see the
    cleanup-crash fix below).
  - **6.2 (stress/10x cardinality): NOT DIRECTLY TESTABLE.** No volume/cardinality knob exists anywhere (`--scenario` is
    a no-op). Would require running all 5 asset-groups concurrently as a coarse proxy, or hand-writing a monkeypatch —
    out of a 1-hour SCRIPT-tagged "run and verify" scope. Documented, not fabricated.
  - **6.3 (missing_data mid-day): NOT DIRECTLY TESTABLE as a synthetic scenario** (no disappear-mid-run hook exists).
    Attempted to reuse the plan's own already-known real "Hyperliquid 0-instruments" case as genuine evidence instead of
    fabricating one, but a live `--venues HYPERLIQUID` run is network-bound + rate-limited (429s on the earliest-funding
    probe) and didn't complete in a reasonable test window — inconclusive, not chased further. The dedicated P3
    "re-verify the 6 bugs" todo below is the right place to actually re-confirm this case; not duplicated here.
  - **6.4 (fake symbol injection): NOT DIRECTLY TESTABLE via CLI** — no `FAKE-EXCHANGE`/`NOSYMBOL` hook exists (0 grep
    hits); would need a unit-level monkeypatch, out of this run-and-verify todo's scope.
  - **6.5 (missing DEFI category, IS side): VERIFIED.** `get_venues_for_asset_groups` (`venue_core.py:442`) scopes venue
    resolution strictly to the requested `asset_groups` list — the 6.1 run above (asset-group=cefi only) shows zero DEFI
    references/errors anywhere in the log, confirming IS cleanly skips an entirely-excluded category. The MTDS
    consumption side is out of this plan's `repos: [instruments-service]` scope (cross-repo boundary, same precedent as
    Phase 5).
  - **6.6 (corrupt expiry, `expiry="not-a-date"`): VERIFIED, with a premise correction.** All 3 real `_parse_expiry`
    functions (`coinbase_cde.py:83`, `tardis/parsing.py:154`, `databento/adapter.py:732`) catch `ValueError`/
    `TypeError` around `datetime.fromisoformat(...)` and return `None` (confirmed live: `_parse_expiry("not-a-date")` →
    `None`) — "doesn't crash" is TRUE. "Parser warns" is FALSE: none of the 3 log a warning: the caller (e.g.
    `coinbase_cde.py:181-183`) just treats `expiry is None` as a reason to skip the row via `continue`. Not treated as a
    bug (silent-skip is a legitimate, if under-observable, design) — noted as a premise correction, matching Phase 5's
    "5.3 doesn't match the shipped event taxonomy" pattern.
  - **6.7 (`config_source=local`, no GCS reads): VERIFIED via code + the 6.1 run.** `ServiceRuntime.config_source`
    (`service_runtime.py:246-248`) is a pure derived property: `"local" if self.is_mock else "gcs"`. The 6.1 run's
    `data=mock` in the `ServiceRuntime:` STARTED log line proves `is_mock=True`, so `config_source="local"` follows
    directly — no separate run needed (Phase 5 already exercised the same `is_mock=True` path end-to-end).
  - **Real bug found + genuinely fixed (correcting Phase 5's stale claim above): the `cleanup()` AttributeError crash.**
    Phase 5's Progress Log claimed this was fixed at `instruments-service@<pending>`, but the suppress tuple was still
    unfixed in the live tree when Phase 6 started (verified: the 6.1-style live run crashed with the exact described
    `AttributeError` before my fix). Actually fixed now: `instruments-service@518cc7a7` (shipped) broadens both
    `contextlib.suppress(RuntimeError, ValueError)` tuples (`instruments_handler.py:399,415`) to include
    `AttributeError`. Re-verified twice: (a) BYBIT-SPOT run above completes cleanup with no traceback; (b) a mid-run
    SIGTERM against HYPERLIQUID (`timeout` sending SIGTERM) shuts down cleanly (`SystemExit code=0`, no traceback) — the
    exact repro Phase 5 described.
  - **Shipping briefly blocked on a repo-blocker, now resolved + shipped.** `bash scripts/quality-gates.sh` on
    `instruments-service` failed 2 PRE-EXISTING tests unrelated to this fix (confirmed via `git checkout HEAD~1` on the
    one changed file — byte-identical failures): `test_expected_universe_golden.py[sports]` (golden=27, actual=31) and
    `test_sports_exempt_is_disjoint_from_uac_sports` (`overlap={'FOOTYSTATS'}`). Root cause:
    `unified-api-contracts@26092ac8` (landed 2026-07-30 11:11:38Z, ~30 min before this QG run) added
    `FOOTYSTATS`/`LADBROKES`/`BET888SPORT`/`SMARKETS` to `VENUES_BY_ASSET_GROUP["sports"]`, breaking the IS/UAC sports
    two-registry disjoint invariant. Filed
    `plans/active/issues/instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md` + declared repo-blocker
    `RB-ecfc50de`. Resolved once `instruments-service@5f7b8136` regenerated the sports golden fixture; rebased my local
    commit onto it, re-ran `quality-gates.sh` (ALL GREEN), and shipped via quickmerge to `instruments-service@518cc7a7`.

- **slot-6 2026-07-30 — Phase 7 DONE, all 6 sub-checks verified live, no code changes needed.** Ran
  `CLOUD_MOCK_MODE=true GCP_PROJECT_ID=mock-project instruments-service --operation instruments --mode live --asset-group cefi --venues <...> --dry-run`
  three ways (single-venue baseline, a 3-venue run that hit a real HYPERLIQUID 429 rate-limit, and a valid-venue +
  no-adapter-registered "fake venue" run) plus inspected the mock-mode local event sink
  (`.local-dev-cache/events/instruments-service.jsonl`). All 6 items PASS with 2 premise notes (same pattern as Phases
  5/6): (7.1) the `ServiceRuntime:` log line logs 7 of ~15 dataclass fields (op/mode/provider/env/ data/testnet/dry_run)
  — not literally every field, though the ones it documents itself as covering are all present; (7.2) service lifecycle
  is STARTED/STOPPED/FAILED (not STARTED/COMPLETED) plus a PROCESSING_STARTED/ PROCESSING_COMPLETED pair with aggregate
  venue counts — confirms + extends Phase 5's "no per-venue COMPLETED event" finding. (7.3) shard isolation confirmed
  via two independent live reproductions — a transient-but-recoverable HYPERLIQUID 429 and a total no-adapter-registered
  fake venue both left the OTHER venues fetching/writing normally, batch exit=0, gap surfaced honestly via
  `SHARD_INCOMPLETE`/`PUBLISHED_DEGRADED`, never a crash or silent partial-success. (7.4)/(7.6) dry-run +
  memory-watchdog log lines match the plan's exact expected strings. (7.5) `ADAPTER_FETCH_FAILED` fired with correct UAC
  classification (`error_code=RATE_LIMIT, action=retry, retry_safe=true`) for the HYPERLIQUID case; the no-adapter case
  correctly does NOT emit it (nothing was fetched to classify) — two distinct failure modes, not a classification gap.
  Full per-item detail in the todo above. Nothing to ship this phase — no crash, silent placeholder, or
  misclassification found.

- **slot-6 2026-08-01 — 6-bug re-verify DONE, none still real, 0 to re-file, no code changes needed.** Bug source:
  `plans/archive/2026_07/e2e_testing_001_instruments_service_2026_03_22.md` lines 158-163 (the real 2026-03-23 DEFI
  audit run). Per-bug verdict, each confirmed live (mock-mode CLI runs) and/or via code:
  - **Bug 1 (Balancer 400 Bad Request, P1): FIXED.** `_BALANCER_API = "https://api-v3.balancer.fi/graphql"`
    (`instruments_service/reference_data/adapters/defi/balancer.py:35`) already carries the `/graphql` path — confirmed
    live twice: (a) a direct `curl` replay of the adapter's exact `poolGetPools` GraphQL query against
    `api-v3.balancer.fi/graphql` returned 200 with real pool data; (b) a live
    `--asset-group defi --venues BALANCER-ETHEREUM --dry-run` CLI run fetched + processed real Balancer pools
    (junk-symbol filtering fired correctly on garbage tokens, no 400/`ADAPTER_FETCH_FAILED` for Balancer). `git log -S`
    shows the `/graphql` suffix present since the earliest commit touching this file (`7fa77592`) — this specific
    URL-mismatch bug, as described, was never present in the surviving `main`-descended history.
  - **Bug 2 (Aster lowercase `defi/ASTER` category, P2): PREMISE SUPERSEDED.** Aster is no longer a DeFi venue at all —
    UAC `VENUE_CATEGORY_MAP` (`unified-api-contracts/unified_api_contracts/registry/venue_constants.py:349`) maps
    `ASTER: "cefi"`, and its adapter lives at `instruments_service/reference_data/adapters/cefi/aster.py` (no
    `adapters/defi/aster.py` exists). Separately, the asset-group casing convention itself changed architecture-wide:
    `_asset_group_for_venue()` (`engine/orchestrator/process_write.py:68-103`) and the UAC `asset_group_key()` helper
    now derive a consistently-lowercase `"defi"`/`"cefi"` category for EVERY venue via canonical lookup, not a per-venue
    string a venue's own adapter could get wrong — the "some venues write DEFI/ uppercase, Aster writes defi/ lowercase"
    inconsistency this bug described cannot recur under the current design.
  - **Bug 3 (Hyperliquid 0 instruments in DEFI, P2): PREMISE SUPERSEDED.** Same reclassification as Bug 2 —
    `VENUE_CATEGORY_MAP` maps `HYPERLIQUID: "cefi"`, its adapter is `adapters/cefi/hyperliquid.py`, and there is no
    `hyperliquid` entry in the DeFi adapter directory (`adapters/defi/`) or its DEX factory registry — confirmed via
    grep, 0 hits. Hyperliquid is not invoked as part of `--asset-group defi` instrument discovery anymore, so a
    "Hyperliquid returns 0 DEFI instruments" run cannot reproduce (it isn't fetched as DEFI at all). UAC's
    `capability_declarations/_defi.py` still carries a legacy `"hyperliquid"`/`"aster"` capability entry, explicitly
    commented `# ── CeFi-style Perps (API-based, not on-chain) ──` — confirming the reclassification was deliberate, not
    an oversight.
  - **Bug 4 (missing `dataset_id=instruments_`/`instruments_defi` catalogue entries, P3): NOT REPRODUCIBLE.**
    `unified-trading-pm/configs/data-catalogue.instruments-service.yaml` no longer has a `dataset_id`-keyed schema at
    all — it's now `shard_status: {CEFI,TRADFI,DEFI,SPORTS,PREDICTION}: <venue>: {...}` (354 lines, DEFI section present
    and populated per-venue). Grepped instruments-service + UTL for any "not found in ... catalogue" / `dataset_id`
    validation warning mechanism — 0 hits; that check no longer exists in this form. Confirmed via 3 live mock-mode runs
    (`--asset-group cefi`, `--asset-group defi`, `--asset-group tradfi`, all `--dry-run`): zero catalogue/dataset_id
    warnings in any of them.
  - **Bug 5 (Pydantic settings UserWarning "custom validator is returning a value other than self", P3): NOT
    REPRODUCIBLE.** Confirmed by 3 live mock-mode CLI runs (0 UserWarnings) + a direct `UnifiedCloudConfig()`
    instantiation under `warnings.catch_warnings(record=True)` (0 warnings) + static analysis of the actual cause:
    `unified-trading-library/unified_trading_library/config_interface/cloud_config.py`'s `sync_project_id_from_gcp`
    `model_validator(mode="after")` (:742-747) still has a `self.model_copy(update=...)` branch — the literal pattern
    pydantic v2 warns on — but it is provably unreachable: `project_id` (`config_interface/base_config.py:72`, alias
    `GCP_PROJECT_ID`) and `gcp_project_id` (`cloud_config.py:319`, same alias `GCP_PROJECT_ID`) read from the IDENTICAL
    env var, so `project_id` can never be `None` while `gcp_project_id` is truthy — the guard
    `if self.project_id is None and self.gcp_project_id` never passes. The sibling validator
    `sync_mock_mode_from_data_mode` (:749-761) was already rewritten to use `object.__setattr__` specifically to dodge
    this exact warning class (its own docstring cites "pydantic v2's restriction on returning a new instance from
    mode="after" validators") — evidence this was a known, deliberately fixed issue elsewhere in the same file; the
    surviving `model_copy()` branch is dead code that happens not to fire, not a live bug.
  - **Bug 6 (`CFE` venue not in UAC `INSTRUMENT_TYPES_BY_VENUE`, P3): FIXED via rename.** The venue is now consistently
    `CBOE` everywhere (`venue_constants.py:38 CBOE = "CBOE"`), fully registered in `INSTRUMENT_TYPES_BY_VENUE`
    (`CBOE: {"EQUITY","ETF","OPTION","INDEX"}`, :488) plus every other UAC venue table
    (category/capabilities/fee-model/alpha-profile). Grepped instruments-service + UAC for a bare `"CFE"` venue string —
    0 hits outside historical comments and one unrelated `RootMetadata` exchange-name field (`tradfi_roots.py:262`,
    describing which physical exchange the VX ticker root trades on, not a venue-registry entry). Confirmed live:
    `--asset-group tradfi --venues CBOE --dry-run` ran clean (exit=0), zero "not in UAC"-style warnings.
  - **Net: 0 bugs re-filed.** Every original finding is either genuinely fixed (1, 6) or premise-superseded by an
    architecture change since 2026-03-23 that removed the code path the bug lived in (2, 3, 4, 5) — consistent with the
    "4 months have passed, some may already be fixed incidentally" framing this todo was written under. No code changes
    shipped this todo (evidence-only, same pattern as Phase 7 above).
