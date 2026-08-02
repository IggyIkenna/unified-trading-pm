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
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, ci-infra, systemd, dbus, basedpyright, mem-wrap, flaky-gate, quickmerge]
related:
  [
    /plans/archive/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md,
    /codex/06-coding-standards/quality-gates-memory-governance.md,
  ]
created: 2026-07-26
parent_epic: infrastructure_master
priority: P2
source: [worker, slot 4, hit live shipping market-data-processing-service@22b926c]
assigned_vm: planning
status: resolved
resolved_by: "unified-trading-pm@d59230eaa (P2, 2026-07-30) + analysis-closed P3 (2026-08-01, slot 12, no code change)"
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-01
locked_since:
---

> **✅ RESOLVED 2026-08-01.** Both todos closed. P2 (the actual observed failure mode): shipped
> `unified-trading-pm@d59230eaa` (2026-07-30) — `_qg_run_basedpyright_attempt()` retries once unwrapped on the
> MEM_WRAP-TOCTOU signature, with hermetic bats coverage. P3 (this session, slot 12): analysis-closed, no code change —
> see the todo's resolution note + Progress log for why a preflight re-validation adds no coverage the P2 retry doesn't
> already provide. Archived.

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

- [x] ✅ [AGENT] P2. In `scripts/quality-gates-base/base-service.sh`'s `[4] TYPE CHECK` step, detect a MEM_WRAP-specific
      launch failure (the real invocation's captured output is empty/contains `Failed to connect to bus` AND `MEM_WRAP`
      was non-empty) and retry ONCE unwrapped (i.e. without `"${MEM_WRAP[@]}"`) before concluding a genuine failure —
      mirrors the script's own existing single-retry patterns elsewhere in this file. Add a clear log line
      distinguishing "MEM_WRAP launch failed, retried unwrapped" from a genuine basedpyright timeout, so the next agent
      hitting this doesn't have to re-derive the diagnosis from scratch. New regression/smoke coverage: a fake
      `systemd-run` shim (in `PATH` for the test) that fails on its FIRST invocation and succeeds on a second, asserting
      the retry-unwrapped path recovers and reports basedpyright's real result. (repo: unified-trading-pm) —
      unified-trading-pm@d59230eaa
- [x] ✅ [AGENT] P3. Consider whether the preflight probe should re-run (or the wrapper should be re-validated) when the
      real invocation is markedly longer than the probe (a 100ms `true` vs. an 80s+ `basedpyright` run) rather than
      trusting a single point-in-time check — lower priority than the todo above since the retry-on-failure fix covers
      the actual observed failure mode without needing to predict WHEN the race might occur. (repo: unified-trading-pm)
      **Resolved by analysis, no code change**: re-read `base-service.sh`'s MEM_WRAP block (~L159-166) and the
      `_qg_run_basedpyright_attempt` call-site (~L1087-1111) plus the P2 fix's own bats fixture
      (`tests/test_qg_mem_wrap_typecheck_retry.bats`'s fake `systemd-run`, which fails BEFORE ever exec'ing the wrapped
      command). This confirms the actual failure mechanism: `systemd-run`'s D-Bus connection attempt is the thing that
      races, and that attempt happens at the START of each invocation (probe's, and separately the real call's) — never
      mid-flight after basedpyright has already been exec'd inside the scope (a live cgroup scope isn't torn down by a
      later D-Bus hiccup; only the initial `systemd-run → dbus` handshake can fail). So the "80s+ real run vs 100ms
      probe" framing in this todo's premise doesn't describe the actual race window — what elapses between the ONE-TIME
      preflight probe and the real call's OWN systemd-run attempt is what matters, and the real call's own attempt is
      exactly the thing the P2 retry already observes and reacts to, unconditionally, regardless of how much time has
      passed since the probe. Re-running the preflight probe (or re-validating the wrapper) immediately before the real
      call would face the identical TOCTOU window the real call's own systemd-run invocation already faces — it adds a
      second point-in-time check with the same race exposure, not a fix for it, and duplicates protection the reactive
      retry already provides deterministically. Conclusion: no additional preflight re-validation is warranted; P2's
      retry-on-failure is the correct fix and fully covers this failure mode independent of timing. No code shipped for
      this todo (analysis-only closure).

## Progress log

- 2026-08-01 (slot 12): Closed P3 (todo 2) by analysis, no code change. Read `base-service.sh`'s MEM_WRAP setup
  (~L159-166) and the `_qg_run_basedpyright_attempt` retry call-site shipped for P2 (~L1087-1111), plus
  `tests/test_qg_mem_wrap_typecheck_retry.bats`'s fake `systemd-run` fixture (models the D-Bus failure as occurring
  BEFORE the wrapped command ever execs). This establishes that the race is confined to `systemd-run`'s own D-Bus
  handshake at each invocation's start — never a mid-run failure inside an already-launched cgroup scope — so the "real
  invocation is markedly longer than the probe" framing in the todo's premise isn't the operative variable. The P2 retry
  reacts to the REAL call's own launch failure directly (not a stale proxy from an earlier probe), so it already covers
  this regardless of elapsed time since the preflight check; a re-validated preflight immediately before the real call
  would face the identical race window the real call's own systemd-run attempt already faces — redundant exposure, not a
  fix. Both todos now closed; archiving this issue doc per `/codex/11-project-management/issue-doc-lifecycle.md` (trigger
  2: commit SHA fixes the issue — P2's SHA plus this analysis-closure for P3). Fixed the two live corpus referrers so
  archival doesn't leave a broken path/stale status: `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`
  (path updated to `/plans/archive/issues/...`) and `plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md` (status
  note updated from "still live" to resolved).
- 2026-07-30 (slot 14): Shipped P2 todo 1 — `unified-trading-pm@d59230eaa`. Factored the [4] TYPE CHECK basedpyright
  invocation into `_qg_run_basedpyright_attempt()` (wrap-prefix param), called once with `"${MEM_WRAP[@]}"`; on the
  MEM_WRAP-TOCTOU signature (exit≠0, 0 errors, 0 warnings, MEM_WRAP non-empty, output empty or containing "Failed to
  connect to bus") logs `MEM_WRAP launch failed, retried unwrapped` and retries once with no wrap prefix, then falls
  through to the existing genuine-failure check unchanged (so a still-failing retry, or a non-MEM_WRAP failure, is
  reported exactly as before — no new failure mode). New `tests/test_qg_mem_wrap_typecheck_retry.bats` (9 tests):
  hermetic fake-systemd-run/fake-basedpyright fault injection covering recovery, the already-unwrapped no-retry case,
  genuine basedpyright errors not being mistaken for the race, and the bounded single-retry (no infinite loop); plus
  grep-based sync-guard tests against the real file. Verified: `bash -n` syntax clean; all 9 bats tests green (built
  bats-core from source into scratch — not installed on this box, matching the precedent in
  `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md`); sanity-checked the tests actually catch a regression by
  reverting the retry call in a scratch copy (2 behavioral tests correctly failed); real `QG_SLICE=typecheck` run on
  this dev box passed clean (this box's systemd-run permanently fails "Failed to connect to bus" — confirms the
  pre-existing preflight-probe fallback already handles the _permanent_ case; this fix targets the narrower _transient_
  probe-passes-then-real-call-fails race, which can't be reproduced live here, hence the hermetic test); full
  `quality-gates.sh` green end-to-end. Left P3 (todo 2, preflight re-validation) untouched — separate, lower-priority
  scope not part of this dispatch. Shipping hit a very busy `live-defi-rollout` (3 peer-push races across 2 quickmerge
  attempts); each resolved via the documented `git pull --rebase --autostash` + retry recipe, no force-push. Also
  reverted (not committed) incidental unrelated dirt from PM's always-on `fix_frontmatter.py` post-gate touching
  `defi_consolidated_closeout_2026_07_18.md` / `cefi_instruments_store_blank_data_type_residual_2026_07_29.md` each QG
  run — expected repo-hygiene side effect, out of this task's scope.
- 2026-07-26 (slot 4): Filed while shipping `market-data-processing-service@22b926c` (the
  `tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md` `_list_instrument_files` P1 fix). Worked
  around via the documented `QG_MEM_CAP=0` escape hatch to ship; not fixed in this session (different repo/topic from
  the dispatched task).
