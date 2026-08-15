---
doc_type: issue
title:
  deployment-service basedpyright ratchet (1259) broken fleet-wide by a dependency backmerge — 1261 measured, zero
  deployment-service source changed
summary: >-
  Measured 2026-08-15 in slot 15: `basedpyright deployment_service/` reports 1261 errors, 2 over the checked-in
  `BASEDPYRIGHT_MAX_ERRORS=1259` ratchet in `deployment-service/scripts/quality-gates.sh:134`. This BLOCKS every
  quickmerge for deployment-service until fixed. Root cause is NOT in deployment-service: `git diff` between the last
  confirmed-green commit (`deployment-service@bf69b2b289`, quality-gates.sh --no-fix passed clean at that tree) and
  current HEAD (`7939f176`) touches only a Dockerfile + 2 shell launcher scripts — zero Python. The two editable-install
  local deps (`unified-api-contracts`, `unified-trading-library`) both advanced HEAD around 2026-08-15T01:20-01:23Z (a
  coordinated fleet backmerge window), and since they're path/editable-installed (not pinned wheels), ANY type-
  signature change in either repo immediately changes what basedpyright infers inside deployment-service without
  deployment-service's own git history recording anything.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, unified-api-contracts, unified-trading-library]
scope: [engineer]
tags: [basedpyright, type-check, ratchet, ci, dependency-drift, blocking]
related:
  [
    /plans/active/issues/dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md,
    /plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md,
  ]
created: 2026-08-15
last_updated: 2026-08-15
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Found while shipping Todo 2 of dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md (truncated-sweep
  detection) — quality-gates.sh failed on type-check with zero deployment-service files touched by my own diff.
context_scope:
  [
    deployment-service/scripts/quality-gates.sh,
    deployment-service/deployment_service/shard_builder.py,
    deployment-service/deployment_service/shard_calculator.py,
    deployment-service/deployment_service/smoke_test_framework.py,
    deployment-service/deployment_service/sports_latency_observation.py,
  ]
---

# deployment-service basedpyright ratchet broken by a dependency backmerge, not by deployment-service's own code

## What was measured (2026-08-15, slot 15)

1. `deployment-service`'s own `bash scripts/quality-gates.sh --no-fix` (task `bachblch7`, this session) passed fully —
   `✅ ALL QUALITY GATES PASSED (303s)` — on the tree that became `deployment-service@bf69b2b289`.
2. Minutes later, a background `slot-cron-ff-pull.sh`-style sync advanced this checkout's `deployment-service` HEAD to
   `7939f176` ("Merge remote-tracking branch 'origin/main' into _backmerge"). `git diff bf69b2b289..HEAD --stat` shows
   **only**: `Dockerfile` (1 line), `launch-backfill-defi-legacy-datatype-fold-vm.sh` (12 lines),
   `launch-sport-residue-blank-venue-purge-vm.sh` (new file, launcher script). **Zero `.py` files.**
3. A fresh `bash scripts/quality-gates.sh --no-fix` run on this new HEAD failed type-check:
   `❌ Type check FAILED — 1261 error(s) > BASEDPYRIGHT_MAX_ERRORS=1259`.
4. Reproduced standalone, deterministically, twice — including once against a brand-new empty `BASEDPYRIGHT_CACHE_DIR`
   (rules out cache-contention from a concurrent peer session in this same slot, per the slot-collision warning active
   this session): `.venv/bin/basedpyright deployment_service/` → **1261 errors, 0 warnings** both times. Every reported
   error is in `shard_builder.py`, `shard_calculator.py`, `smoke_test_framework.py`, or `sports_latency_observation.py`
   — files `git log -1 -- <those 4 paths>` shows were last touched by an unrelated, much older commit (`138c82d1`), not
   by anything in the `bf69b2b289..HEAD` range.

## Root cause — editable-installed local deps, not deployment-service source

`deployment-service`'s `LOCAL_DEPS` are path/editable installs of `unified-api-contracts` and `unified-trading-library`
(not pinned wheels) — so basedpyright's inference for any deployment-service call site into those packages depends on
THEIR current on-disk source, not a version pin deployment-service's own git history would show. Both moved HEAD in the
same window the backmerge landed:

- `unified-api-contracts` → `85caa70a` at `2026-08-15T01:20:55Z`. Candidate commits in that window: `53a5adc7`
  "feat(registry): LST token address SSOT — migrate 8 cited addresses..." and `bed96aa0` "fix(registry): drop eETH/rsETH
  from the LST address SSOT...".
- `unified-trading-library` → `bd587735` at `2026-08-15T01:23:34Z`. Candidate commit: `ff9cb5f8`
  "fix(pipeline-e2e-check): suffix GCS report blob with asset_group...".

**Update 2026-08-15 (same day, later pass) — all 5 candidates checked so far are RULED OUT.** Read the full diffs of the
original 3 candidates plus 2 more found by actually tracing the flagged files' import chains
(`shard_builder.py`/`shard_calculator.py` → `config_loader.py` → `unified_api_contracts.VenueMapping` +
`market_data_categories`; `smoke_test_framework.py`/`sports_latency_observation.py` →
`unified_trading_library.StorageClient`):

| Commit                             | Repo | What it actually changed                                                                                                   | Verdict                                                       |
| ---------------------------------- | ---- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `unified-api-contracts@53a5adc7`   | UAC  | New file `registry/lst_token_addresses.py` (additive only, unrelated module)                                               | Ruled out — deployment-service never imports this module      |
| `unified-api-contracts@bed96aa0`   | UAC  | Same new file, 10-line data edit                                                                                           | Ruled out — same reason                                       |
| `unified-trading-library@ff9cb5f8` | UTL  | `pipeline_e2e_check/report.py` (unrelated module, not imported by the 4 files)                                             | Ruled out                                                     |
| `unified-trading-library@b12ceab9` | UTL  | `StorageClient.download_bytes_range()` gains a fully-typed optional `generation` kwarg                                     | Ruled out — fully annotated, predates the window (2026-08-10) |
| `unified-api-contracts@316002f1`   | UAC  | `VenueMapping`/`market_data_categories`: adds `"PACIFICA-SOLANA"` string literals to existing `list[str]`/`dict[str, str]` | Ruled out — pure data-literal additions, no signature change  |

None of these touch a return type, parameter type, or class attribute annotation. Basedpyright's Unknown cascade in the
4 flagged files traces to `ConfigLoader`'s `.get(...)` calls (shard_builder.py) and `StorageClient` methods
(smoke_test_framework.py/sports_latency_observation.py) — but the classes themselves (`ConfigLoader`, `VenueMapping`,
`StorageClient`) were NOT touched by any commit in the backmerge window. **The "single culprit commit in a known time
window" theory this doc started with is not panning out** — ad-hoc commit-message-driven guessing has now cost real time
across 2 passes without a hit.

**Recommended methodology for the next attempt — bisection, not more guessing, and NOT on this shared checkout.**
`unified-api-contracts`/`unified-trading-library` are editable/path-installed LOCAL_DEPS shared by every slot session
via this same checkout (per the workspace's multi-agent-safety rule) — checking out an old commit in either repo here
would silently change what every OTHER concurrent process reading them sees. Do this instead: clone (or
`git worktree add`) an ISOLATED copy of both dependency repos, point a throwaway venv's editable install at that
isolated copy, then bisect by checking out each dependency repo at successive commits in the
`2026-08-14T11:40Z..2026-08-15T01:24Z` window (arming commit through the backmerge) and re-running
`basedpyright deployment_service/` after each, until the count flips from <=1259 to 1261. That pins the exact commit
without disturbing this shared checkout.

## Why this matters

`BASEDPYRIGHT_MAX_ERRORS=1259` is a hard-fail gate in `deployment-service/scripts/quality-gates.sh` — every quickmerge
for deployment-service is blocked until this is back at or under 1259. This is a genuinely different failure class from
the usual "someone's source regressed the ratchet" case the mechanism is designed for: an EDITABLE-INSTALL dependency
changed shape without deployment-service's own diff recording anything, so `git bisect` inside deployment-service alone
cannot find it — the fix has to be sought in the two dependency repos.

## Todos

- [ ] [CODE] P1. 5 candidate commits checked and ruled out 2026-08-15 (see updated Root Cause section — none touch a
      type signature). Next attempt MUST bisect in an ISOLATED worktree/clone of `unified-api-contracts` +
      `unified-trading-library` (never this shared checkout — editable installs mean a manual checkout here changes what
      every concurrent slot session sees), stepping through commits in `2026-08-14T11:40Z..2026-08-15T01:24Z` until
      `basedpyright deployment_service/` flips 1259→1261. DoD: `basedpyright deployment_service/` back to <=1259 (or
      ratchet the ceiling DOWN once fixed further, never up).
- [ ] [OPERATOR] P2. Two guessing passes (5 candidate commits total) have NOT found the root cause — "quickly" per this
      todo's original DoD has now elapsed. Decide whether to temporarily raise `BASEDPYRIGHT_MAX_ERRORS` (against the
      ratchet-only-goes-down norm) to unblock shipping — including the already-written, already-tested Todo 2 fix in
      `dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md` sitting uncommitted — while the isolated-worktree
      bisection above is pursued, or hold all deployment-service quickmerges until fixed. DoD: a stated decision, not a
      default.

## Evidence

- `deployment-service@bf69b2b289..HEAD` diff: `Dockerfile | 2 +-`, 2 shell launcher scripts, 0 `.py` files.
- `.venv/bin/basedpyright deployment_service/` → `1261 errors, 0 warnings, 0 notes`, reproduced twice (default cache +
  fresh isolated cache dir), both from `deployment-service` HEAD `7939f176`.
- `unified-api-contracts` HEAD `85caa70a` (2026-08-15T01:20:55Z), `unified-trading-library` HEAD `bd587735`
  (2026-08-15T01:23:34Z) — both editable-installed LOCAL_DEPS of deployment-service.

## Deferred work after 2026-08-15

| Item                                                                                              | State / why deferred                                                                                                                                                                                                                                                                    | Blocked on                                                 |
| ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Todo 2 of `dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md` (truncated-sweep signal) | **Code + tests WRITTEN, compile-checked, uncommitted** in `deployment-service` working tree (`exit_code_fleet_monitor.py` + `tests/unit/test_data_pipeline_monitors.py`) — cannot ship, quickmerge requires a green `quality-gates.sh` and this ratchet break is unrelated-but-blocking | This doc's Todo 1 (or an operator override of Todo 2 here) |

**Recommended next item**: root-cause Todo 1 above (start with `unified-api-contracts@53a5adc7`/`bed96aa0` and
`unified-trading-library@ff9cb5f8` — read their diffs for type-annotation changes) — it unblocks ALL deployment-service
shipping, not just this one change.
