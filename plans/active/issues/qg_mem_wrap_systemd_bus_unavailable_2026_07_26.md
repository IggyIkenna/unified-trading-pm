---
doc_type: issue
title:
  quality-gates.sh's MEM_WRAP (systemd-run --user --scope) TOCTOU-races a transient D-Bus outage under host contention,
  silently mis-reporting a real basedpyright pass as "Type check FAILED/timeout"
summary: >-
  Hit live 2026-07-26 while shipping an unrelated MDPS fix
  (`tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`'s `_list_instrument_files` P1 todo).
  `quality-gates.sh`'s [4] TYPE CHECK step wraps `basedpyright` in `systemd-run --user --scope -p MemoryMax=... -- ...`
  (the 2026-05-15 OOM-mitigation `MEM_WRAP`). The script's own preflight probe (`systemd-run --user --scope -p
  MemoryMax=100M --quiet -- true`) is meant to detect an unusable systemd user session and fall back to running
  unwrapped — but it only runs ONCE, before the real (much longer, ~80s+ full-run) invocation. Under heavy host
  contention (multiple slots' QG runs concurrently opening/closing D-Bus user-session scopes), the probe can pass at one
  instant while the REAL wrapped `basedpyright` call fails moments later with the identical `Failed to connect to bus:
  No medium found` error — a TOCTOU race, not a permanently-broken host (a bare `command -v systemd-run` + a standalone
  probe both succeed/fail consistently when run in isolation; only the in-script sequence intermittently disagrees under
  load). When the wrapped call fails this way, `run_timeout` produces ZERO output (the subprocess never started) and a
  nonzero exit — which the gate's own branching (`PYRIGHT_EXIT -ne 0 && ERROR_COUNT -eq 0 && WARN_COUNT -eq 0` → `"Type
  check FAILED/timeout"`) cannot distinguish from a genuine 120s analysis timeout. This blocks the whole
  `quality-gates.sh` run (and therefore `quickmerge --agent`, which re-gates on push) even though `basedpyright` itself,
  run unwrapped (`QG_MEM_CAP=0`, the script's own documented escape hatch), completes cleanly in ~7s. Confirmed via 3
  independent reproductions: (1) two consecutive `bash scripts/quality-gates.sh` runs both hit the false failure under
  `load average: 9.55` (8 cores); (2) a direct `.venv/bin/basedpyright market_data_processing_service/` (unwrapped)
  completed in 7.5s with real output; (3) manually replaying the EXACT wrapped invocation (`systemd-run --user --scope
  -p MemoryMax=10G -p MemorySwapMax=0 --quiet -- .venv/bin/basedpyright ...`) reproduced the identical `Failed to
  connect to bus: No medium found` failure with zero basedpyright output.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, ci-infra, systemd, dbus, basedpyright, mem-wrap, flaky-gate, quickmerge]
related:
  [
    /plans/active/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md,
    /codex/06-coding-standards/quality-gates-memory-governance.md,
  ]
created: 2026-07-26
parent_epic: infrastructure_master
priority: P2
source: [worker, slot 4, hit live shipping market-data-processing-service@22b926c]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-26
locked_since:
---

# QG MEM_WRAP TOCTOU-races a transient D-Bus outage under host contention

## What I found

`scripts/quality-gates-base/base-service.sh`'s `[4] TYPE CHECK` step wraps `basedpyright` via `MEM_WRAP` (the 2026-05-15
OOM-mitigation `systemd-run --user --scope -p MemoryMax=$QG_MEM_CAP ...`). A ONE-TIME preflight probe decides whether to
use the wrapper (`command -v systemd-run && systemd-run ... -- true`), but the real invocation runs much later and much
longer. On a shared, heavily-loaded host (observed `load average: 9.55` on 8 cores, multiple slots' concurrent QG runs),
the probe can pass while the real wrapped call fails moments later with the same
`Failed to connect to bus: No medium found` error `systemd-run` throws when the D-Bus user session is transiently
unreachable. This produces a subprocess that never starts (zero output, nonzero exit) — which the gate's failure branch
cannot distinguish from a genuine analysis timeout, so it prints the generic `"Type check FAILED/timeout"` and
hard-fails the whole gate (and `quickmerge --agent`'s re-gate on push) even though the code is genuinely clean.

## Why it matters

This is a **false negative on the fleet's own tooling**, not a real code defect — it silently blocks `quickmerge` on ANY
repo, for ANY agent, whenever host contention is high enough to trigger the race (which is exactly when MANY slots are
shipping concurrently — the worst possible time for a spurious gate failure). An agent without the patience/context
budget to diagnose past the misleading "timeout" label could easily mis-attribute this to their own change and waste
time debugging code that was never broken, or (worse) reach for a banned bypass flag. The documented `QG_MEM_CAP=0`
escape hatch works but is not self-discoverable from the failure message alone — nothing in the "Type check
FAILED/timeout" output hints that MEM_WRAP/D-Bus is the actual cause.

## Recommended decision

- [ ] [AGENT] P2. In `scripts/quality-gates-base/base-service.sh`'s `[4] TYPE CHECK` step, detect a MEM_WRAP-specific
      launch failure (the real invocation's captured output is empty/contains `Failed to connect to bus` AND `MEM_WRAP`
      was non-empty) and retry ONCE unwrapped (i.e. without `"${MEM_WRAP[@]}"`) before concluding a genuine failure —
      mirrors the script's own existing single-retry patterns elsewhere in this file. Add a clear log line
      distinguishing "MEM_WRAP launch failed, retried unwrapped" from a genuine basedpyright timeout, so the next agent
      hitting this doesn't have to re-derive the diagnosis from scratch. New regression/smoke coverage: a fake
      `systemd-run` shim (in `PATH` for the test) that fails on its FIRST invocation and succeeds on a second, asserting
      the retry-unwrapped path recovers and reports basedpyright's real result. (repo: unified-trading-pm)
- [ ] [AGENT] P3. Consider whether the preflight probe should re-run (or the wrapper should be re-validated) when the
      real invocation is markedly longer than the probe (a 100ms `true` vs. an 80s+ `basedpyright` run) rather than
      trusting a single point-in-time check — lower priority than the todo above since the retry-on-failure fix covers
      the actual observed failure mode without needing to predict WHEN the race might occur. (repo: unified-trading-pm)

## Progress log

- 2026-07-26 (slot 4): Filed while shipping `market-data-processing-service@22b926c` (the
  `tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md` `_list_instrument_files` P1 fix). Worked
  around via the documented `QG_MEM_CAP=0` escape hatch to ship; not fixed in this session (different repo/topic from
  the dispatched task).
