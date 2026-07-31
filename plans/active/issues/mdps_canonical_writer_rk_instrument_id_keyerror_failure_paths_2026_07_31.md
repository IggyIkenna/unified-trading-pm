---
doc_type: issue
title:
  market-data-processing-service's canonical_writer_streaming.py KeyErrors on two failure-handling paths after c78285b
  removed empty instrument_id from aggregate-bundle row_keys
summary: >-
  Commit c78285b ("fix(manifest): omit empty instrument_id from row_key for aggregate bundle writes") correctly stopped
  putting an empty `instrument_id` into the manifest `row_key` dict for tradfi chain-bundle aggregate writes, but left
  two direct-bracket `rk["instrument_id"]` accesses in the FAILURE-handling paths of `canonical_writer_streaming.py`.
  For any aggregate-bundle write that ALSO hits an error, these now raise `KeyError` instead of cleanly recording
  `attempted_failed`: (1) `close_candle_streaming_writer`'s `error is not None` branch at line 442 (`logger.error(...
  rk["instrument_id"] ...)`) — note the very next `_emit_status_for_shard` call at line ~453 already uses the safe
  `rk.get("instrument_id", "")`, so the log line crashes first and inconsistently; (2) the manifest-write-exception
  fallback at line 596 (`instrument_id=rk["instrument_id"]`), whose adjacent comment (lines 580-588) still asserts "rk
  always carries date/venue/instrument_type/league_id/underlying/instrument_id (set unconditionally at open time)" —
  that comment is now STALE for aggregate bundles. A KeyError here means the shard neither uploads nor records
  `attempted_failed`, leaving its capture_status unrecorded (an honest-coverage gap).
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [regression, manifest, attempted-failed, canonical-writer, honest-coverage, keyerror]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-31
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-07-31 (slot-1, review) during a pre-compact audit; originally direct-pinged to slot-4 (~03:12Z) as a
    chat-only ping that never became a tracked backlog todo, so it fell through. Re-verified live by main-agent
    (agt-9f21bc) 2026-07-31 05:05Z: both lines still present + unfixed; c78285b confirmed as the removing commit.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# MDPS canonical_writer_streaming: KeyError on aggregate-bundle failure paths

## What I found (verified live 2026-07-31 05:05Z, main-agent agt-9f21bc)

`market_data_processing_service/app/core/canonical_writer_streaming.py`:

- **Line 442** — inside `close_candle_streaming_writer`, the `if error is not None:` branch:

  ```python
  logger.error(
      "close_candle_streaming_writer: write failed for instrument_id=%s day=%s tf=%s: %s",
      rk["instrument_id"],   # <-- KeyError for aggregate-bundle writes (empty instrument_id omitted by c78285b)
      rk["date"],
      ctx.tf,
      error,
  )
  ```

  The immediately following `_emit_status_for_shard(...)` call (line ~453) already uses the safe
  `instrument_id=rk.get("instrument_id", "")` — so this is a straightforward inconsistency: the log line crashes before
  the safe emit is reached.

- **Line 596** — the manifest-write-exception fallback:

  ```python
  _emit_status_for_shard(
      capture_status="attempted_failed",
      error=f"MANIFEST_WRITE_FAILED: {exc}",
      ...
      instrument_id=rk["instrument_id"],   # <-- KeyError for aggregate-bundle writes
      venue=rk["venue"],
      date_str=rk["date"],
      ...
  )
  ```

  The adjacent comment (lines 580-588) still claims `rk` "always carries ... instrument_id (set unconditionally at open
  time above) — direct indexing fails fast on a genuine construction bug instead of silently substituting ''". After
  c78285b that invariant no longer holds for aggregate-bundle writes, so the comment is stale and the "fail fast on a
  construction bug" rationale now mis-fires on a legitimate (empty-instrument_id) aggregate row_key.

`grep -n 'rk\["instrument_id"\]' market_data_processing_service/app/core/canonical_writer_streaming.py` → lines
442, 596.

Removing commit confirmed: `c78285b7ca2039cc94f7e01f5baa887828ee9cea` "fix(manifest): omit empty instrument_id from
row_key for aggregate bundle writes" (2026-07-31 03:03:24Z).

## Why it matters

- These are the FAILURE-handling paths. A `KeyError` here means an aggregate-bundle write that hits any error (or a
  manifest-write exception) crashes instead of recording `attempted_failed` — so the shard's `capture_status` is left
  unrecorded, which is exactly the honest-coverage gap `_emit_status_for_shard` exists to prevent
  (`/codex/02-data/availability-manifest-and-data-status.md`, `…/honest-coverage-model.md`).
- Contradicts the shard-level failure-isolation contract (`/codex/04-architecture/shard-level-failure-isolation.md`):
  the error branch is supposed to classify + record, not raise.

## Recommended fix (concrete, bounded, worker-determinable — per the review agent)

- [ ] [BACKEND] P1. In `market_data_processing_service/app/core/canonical_writer_streaming.py`: change both
      `rk["instrument_id"]` accesses (line 442 log call, line 596 `_emit_status_for_shard` call) to
      `rk.get("instrument_id", "")`, matching the safe access already used at line ~453; update the now-stale comment at
      lines 580-588 so it no longer claims `instrument_id` is unconditionally present (note aggregate-bundle writes omit
      it per c78285b); add a regression test driving `close_candle_streaming_writer` with an aggregate (empty-
      instrument_id) `row_key` and `error is not None` (and separately a manifest-write exception) asserting it records
      `attempted_failed` with no `KeyError`. Only `instrument_id` was removed by c78285b — `venue`/`date` remain
      present, so scope the change to `instrument_id`. (repo: market-data-processing-service)

## Progress Log

- **na-eligibility-audit 2026-07-31** (tradfi tranche, dispatch agt-6d6eaf): **RECLASSIFY — `assigned_vm: NA` →
  `planning`.** Doc's own filing note (below) already flagged this as review-agent-assessed precisely-scoped/AO-eligible
  and invited exactly this flip; independently re-verified rather than rubber-stamped. Sole open todo is a single-file,
  worker-determinable fix with no open design call: the correct safe-access pattern (`rk.get("instrument_id", "")`) is
  already established 5x in the same file (lines 454, 475, 496, 548, 566), so applying it to the 2 remaining unsafe call
  sites is mechanical; the stale comment fix is a factual correction, not a design choice; the regression test has a
  fully stated done-when. Re-verified live against the current repo checkout (HEAD `bcfec9543`, ~8.5h newer than this
  doc's own 05:05Z check): both `rk["instrument_id"]` call sites (lines 442, 596) still present and unfixed — doc's
  claims still 100% current. Shared conflict-check
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) run and CLEARED: no active
  `assigned_vm: planning` plan in `parent_epic: infrastructure_master` claims this ground, no sibling batch/finalize doc
  drafted this run overlaps, and `tradfi_consolidated_closeout_2026_07_18.md`'s own Track content does not mention this
  fix. Filled previously-missing `assigned_role: backend_engineer` (per the `[BACKEND]` tag mapping) and
  `estimate_baseline_ai_days: 0.2` / `estimate_calibrated_ai_days: 0.08` (refactor class, single-file bounded fix). Per
  `check_finalize_plan_coverage.py` (globs `plans/active/*.md` only, not `issues/`), this `doc_type: issue` doc is
  structurally exempt from the companion finalize-plan requirement — none authored.
- 2026-07-31 05:05Z (main-agent agt-9f21bc): filed from review-agent (slot-1) msg 2841 after live re-verification of
  both lines and the removing commit. Set `assigned_vm: NA` per the ASK-BEFORE-CREATING hard rule; operator notified
  that the review agent assessed this precisely-scoped/AO-eligible and can flip `assigned_vm: planning` +
  `execution_scope` to auto-dispatch.
