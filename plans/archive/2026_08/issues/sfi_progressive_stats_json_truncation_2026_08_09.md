---
doc_type: issue
title:
  SFI progressive-stats occasionally returns a truncated JSON body ("Unterminated string") — already shard-isolated,
  root cause not yet diagnosed
summary: >-
  Found while verifying `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md`'s SFI mid-processing-hang todo via
  three real recent production runs (2026-08-06/08-07). No hang occurred in any of the three runs — all completed
  cleanly (exit_code=0) — but `sfi-backfill-20260807-123519`'s run.log shows 10 `json.JSONDecodeError`-shaped failures
  ("Unterminated string starting at: line 1 column N") out of 2254 per-date completions (~0.4%), each correctly caught
  by the existing per-match/per-league shard isolation in `instruments_service/engine/orchestrator/sfi.py`
  (`classify_and_emit_error` → `manifest.record_failed`, loop continues, run finishes normally). Not a hang, not
  data-loss-silent (the manifest honestly records `attempted_failed`), but a real recurring data-quality gap: some
  fraction of SFI_PROGRESSIVE_STATS shards never capture because the provider response is truncated mid-body.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sfi, sports, json-decode-error, shard-isolation, data-quality]
related:
  [
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-08-09"
author: cross_cutting_satellite_ao_dispatch_batch11-109fda319950 (slot-30, backend_engineer)
source: >-
  Discovered verifying the SFI mid-processing-hang todo in cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md —
  not itself in scope of that todo (that todo is about a HANG, this is a distinct low-frequency data-quality bug that is
  already correctly isolated, not silently swallowed).
resolved_by: instruments-service@ecfc2749
locked_by:
archive_exempt: true # 2026-08-10 slot-22: two-commit ritual
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
---

> **🗄️ ARCHIVED 2026-08-12 (/plan-reconcile)** — `status: resolved`, sole todo done, `resolved_by` filled, `locked_by`
> cleared (corpus-wide placeholder bug, option B ruling).

# SFI progressive-stats occasional JSON truncation

## What I found

Three real SFI backfill VM runs from 2026-08-06/08-07 (`sfi-backfill-20260806-140815`, `sfi-backfill-20260807-101503`,
`sfi-backfill-20260807-123519` — GCS logs at `gs://deployment-scripts-central-element-323112/vm-logs/<vm-name>/run.log`)
all completed with `exit_code=0` and monotonically advancing `[[VM_PROGRESS]]` markers — no hang, no stall, no watchdog
trip. Two of the three runs hit transient errors mid-run and recovered cleanly via existing shard isolation:

- `sfi-backfill-20260806-140815`: repeated `429` on the GCS manifest-cache write (`sfi_league_mapping_write`) — a
  storage-side rate limit, not an SFI API issue, retried/absorbed without stopping the run.
- `sfi-backfill-20260807-123519`: 10 occurrences of `Unterminated string starting at: line 1 column N` (classic
  `json.JSONDecodeError` shape) from `SoccerFootballInfoAdapter.get_progressive_stats` — the SFI provider response body
  was cut off mid-JSON. Each is caught by the per-match `try/except Exception` in
  `instruments_service/engine/orchestrator/sfi.py::_fetch_sfi_data` (around the
  `await _orch.asyncio.wait_for(adapter.get_progressive_stats(mid), timeout=30.0)` call), classified via
  `classify_and_emit_error`/`_classify_adapter_failure` as `error_code=UNKNOWN`, and recorded honestly as
  `manifest.record_failed` per expected league — the run continues to the next match/date without stalling. 10/2254
  (~0.4%) date-completions in that run carried at least one such failure.

## Why it matters

This is NOT the hang this batch's todo (`Diagnose the SFI backfill mid-processing hang...`) is about — that todo's
done-when (a relaunched SFI backfill completes or fails loud+isolated, never silently hangs) is fully satisfied by these
three runs, and the fixes that make it so (bounded HTTP timeouts in `reference_data/adapters/sports/adapters/base.py`
`_make_session()`, per-match `asyncio.wait_for` in `sfi.py`, and the VM-level `STALL_PROGRESS_REGEX=league` watchdog in
`deployment-service/scripts/vm/launch-sfi-backfill-vm.sh`) all landed 2026-06-19 through 2026-06-24 and are confirmed
still live. This JSON-truncation finding is a SEPARATE, lower-severity data-completeness gap: a small, low-frequency
(~0.4% of date-completions in the one run where it was measured) but recurring loss of SFI_PROGRESSIVE_STATS coverage
for specific matches, root cause not yet diagnosed (candidates: RapidAPI-side response truncation on large matches, a
proxy/gzip edge case, or an aiohttp buffering interaction — not investigated here). It IS honestly recorded
(`attempted_failed`, not silently dropped), so it is visible to the honest-coverage index and can be reconciled by a
future residual-closer re-attempt.

## Recommended decision

File as a bounded follow-up (not urgent — honest-coverage already reflects the gap, no silent data loss): investigate
whether `resp.json(content_type=None)` in `base.py::_get_with_retry` is racing a response body that's still streaming
(would want a `resp.read()` + explicit `json.loads()` with a clearer error, or a retry-on-`JSONDecodeError` path
distinct from the current retry-on-`aiohttp.ClientError` path, since a `JSONDecodeError` is NOT an `aiohttp.ClientError`
subclass and today gets zero retries before falling through to shard-level failure isolation). Low priority given the
~0.4% measured rate and existing honest-failure recording.

- [x] ✅ [CODE] P3. Diagnose why `SoccerFootballInfoAdapter.get_progressive_stats` occasionally receives a truncated
      JSON body from the SFI API (10/2254 date-completions in `sfi-backfill-20260807-123519`'s run.log,
      `gs://deployment-scripts-central-element-323112/vm-logs/sfi-backfill-20260807-123519/run.log`, error shape
      `Unterminated string starting at: line 1 column N`) and consider adding a targeted retry for
      `json.JSONDecodeError` in `instruments_service/reference_data/adapters/sports/adapters/base.py::_get_with_retry`
      (currently only `aiohttp.ClientError` is retried; a JSON decode error falls straight through to per-match shard
      isolation with zero retries). Done when: root cause identified and either fixed or documented as a genuine
      upstream provider limitation. Repo: instruments-service. — instruments-service@ecfc2749

## Progress Log

- **na-eligibility-audit 2026-08-10 (sports tranche)**: RECLASSIFY `assigned_vm: NA` → `planning`. Sole open todo is a
  single-repo (instruments-service), single-function diagnosis with two bounded terminal outcomes (fix, or document as a
  genuine upstream limitation) and an explicit stated done-when — meets the worker-determinable-outcome bar. Conflict
  -check (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) against every active
  `assigned_vm: planning` doc, the 5 draft `sports_satellite_ao_dispatch_batch{5,9,10,11,12}` docs, and
  `sports_consolidated_closeout_2026_07_19.md`: the only other `progressive_stats` hits are unrelated (a `.team`
  field-mapping bug, a contamination-code scan, and an odds-column question in
  `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`); `cross_cutting_satellite_ao_dispatch_batch11_2026_08_09.md` — the
  doc this issue was originally spun out of — explicitly says the JSON-truncation finding is "NOT this todo" and cites
  this doc as where it's tracked, confirming no competing claim. Clear to dispatch. Added missing
  `assigned_role: backend_engineer` (matches the discovering agent's own self-tagged role and the adapter-retry-logic
  nature of the work); corrected `execution_scope` `local-only` → `orchestrator-agent`. Single-todo issue doc —
  finalize-plan-coverage is structurally exempt (`check_finalize_plan_coverage.py` only globs `plans/active/*.md`) and
  archival on this one todo's own done-when is trivial, so no companion finalize doc authored.
