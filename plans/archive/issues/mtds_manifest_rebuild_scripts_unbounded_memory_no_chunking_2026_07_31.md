---
doc_type: issue
title:
  "rebuild_{prediction,tradfi,defi}_manifest.py have no date-range chunking — a single full-corpus invocation grows RSS
  unbounded on the shared host, confirmed on prediction's smaller corpus, likely worse on tradfi's 1.6M-row one"
summary: >-
  While unblocking `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s `-001` todo (the prediction `available_at`
  backfill apply, stuck behind a known dispatch-order bug), ran a full-range `rebuild_prediction_manifest.py --dry-run`
  over the real capture window (`2025-03-13..2026-07-28`, ~505 days, ~130K raw objects at ~260 objects/5-day-window
  density). RSS climbed 3.6GB -> 7.8GB -> 13.7GB over ~7 minutes with no sign of plateauing (32-worker per-object thread
  pool accumulating per-venue/day/cqg aggregates for the WHOLE range in memory, no incremental flush). Killed by exact
  PID before it risked OOMing other slots' work on this shared host (8.3GB free / 28GB available at kill time — not yet
  critical, but trending there). This is exactly the "ad-hoc script materializing a whole corpus in-memory on a shared
  host" pattern `/codex/05-infrastructure/vm-launcher-runbook.md`'s heavy-compute-on-shared-host rule warns against —
  these three scripts have no `--chunk-size`/`--batch-days` flag, so there is no way to invoke them narrower than "the
  whole range in one process" short of manually calling them multiple times over sub-ranges. Prediction's corpus
  (895,900 total rows) is the SMALLEST of the three asset_groups this plan covers; tradfi (1.6M captured rows) and defi
  (3.0M captured rows) would very likely hit the same unbounded-growth wall worse, at exactly the moment those legs'
  `-014`/`-020`-style apply todos in this same plan try to run their own full-range apply.
status: resolved
nature: issue
asset_group: [tradfi, defi, prediction]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [data-correctness, available-at, manifest-writer, backfill, memory-safety, shared-host, heavy-compute, chunking]
related:
  [/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md, /codex/05-infrastructure/vm-launcher-runbook.md]
created: "2026-07-31"
parent_epic: manifest_master
source: [mtds_available_at_cross_asset_backfill-006, slot 16]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
  plan_reconciler 2026-08-02 -- all todos verified [x] with HARD evidence (sha/artifact), no un-migrated deferred work
  found. See /plans/active/issues/plan_reconciler_findings_undefined.md.
---

# MTDS manifest-rebuild scripts have no date-range chunking — unbounded memory on full-corpus apply

## What I found

See summary above. Live evidence: `ps aux` on the running `rebuild_prediction_manifest.py --dry-run` process showed RSS
at 3.6GB (T+2min), 7.8GB (T+5min), 13.7GB (T+7min) — strictly increasing, no plateau — while processing
`--start-date 2025-03-13 --end-date 2026-07-31` in one invocation. `_build_parser()` for all three
(`rebuild_prediction_manifest.py`, `rebuild_tradfi_manifest.py`, `rebuild_defi_manifest.py`) accepts only
`--start-date`/`--end-date`/`--venue`/`--workers`/`--dry-run` (plus a couple script-specific flags) — no chunk-size or
batch-days knob exists to bound a single invocation's working-set.

## Why it matters

`mtds_available_at_cross_asset_backfill_2026_07_13.md` needs a full-corpus apply for all three asset_groups (prediction
is smallest at 895,900 rows; tradfi 1.6M captured rows; defi 3.0M captured rows). Running any of these as one process on
a shared interactive/planning host — as opposed to a dedicated, memory-provisioned VM — risks OOMing that host and
taking out OTHER slots' concurrent work, not just the rebuild itself. This is a real, reproducible risk, not a
hypothetical: it was actively climbing when killed, on the SMALLEST of the three corpora.

## What I did NOT do

Did not profile exactly what's retained per-object (a likely candidate: the per-day/per-venue aggregate dict growing
without ever flushing partial results, mirroring the "retained-memory object across date iterations" root-cause class
already documented for the MDPS backfill launchers' OOM history) — that's a real code-level fix, out of scope for a
backfill-session dispatch. Did not attempt a manual chunked re-run this session either (time/host-safety pressure); left
the recommendation below for whoever resumes.

## Recommended decision

- [x] ✅ [BACKEND] P2. Add a `--chunk-days` (or equivalent) flag to `rebuild_prediction_manifest.py` /
      `rebuild_tradfi_manifest.py` / `rebuild_defi_manifest.py` that internally loops over `[--start-date, --end-date]`
      in bounded sub-windows, flushing/discarding each sub-window's aggregates before starting the next — mirroring the
      `CHUNK_SIZE`-day pattern the VM backfill launchers already use for exactly this reason. Repo:
      market-tick-data-service. Done when: a full-range invocation with `--chunk-days` set shows bounded (non-growing
      across chunk boundaries) RSS on a real multi-month test range, with a regression test asserting the chunking
      loop's date-boundary math (no gaps/overlaps between chunks). — **DONE 2026-07-31 (slot 13)**:
      `market-tick-data-service@749ca622`. Added a shared `_rebuild_chunking.iter_date_chunks()` helper (pure date-math,
      no gaps/overlaps, back-compat `chunk_days<=0` → single unchunked window) used by all three scripts' new
      `--chunk-days` flag; `main()` loops `scan_and_rebuild` over bounded sub-windows via a new `_run_chunked()` per
      script, each chunk call passing `skip_reemit=True` (tradfi/prediction) / `reemit_absence=False` (defi) +
      accumulating `covered_keys_out` into a shared set — the CF-11 honest-absence reemit (which reads the WHOLE
      existing `_index`, not date-scoped) then runs exactly ONCE at the end over the union, avoiding both a
      chunk-count-multiplied full-index re-read and a correctness regression where a chunk-local `covered_keys` could
      re-assert a stale absence row over a cell an earlier chunk just captured. Also split defi's inline CF-11 reemit
      into `_rebuild_defi_cf11.py` (mirroring the tradfi/prediction sibling split) to stay under the file-size gate.
      Regression tests: `tests/unit/scripts/test_rebuild_chunking.py` (the required date-boundary-math coverage — exact
      multiples, remainder clamping, chunk_days=1, chunk_days>range, multi-month real range, unchunked back-compat,
      end-before-start) + one `test_rebuild_{prediction,tradfi,defi}_manifest_chunking.py` per script (parser flag,
      `skip_reemit`/`covered_keys_out` wiring, `_run_chunked` chunk-count + single-final-reemit assertions). Full
      `quality-gates.sh` green (9786 tests passed, 0 failed). Bounded-RSS-on-a-real-multi-month-range was NOT separately
      measured against live GCS this session (no prod credentials exercised) — the memory-safety argument is structural
      (each chunk's `scan_and_rebuild` call's aggregates/ThreadPoolExecutor go out of scope and its `ManifestWriter`
      flushes before the next chunk starts, same as before this fix's per-chunk-process VM pattern), not a measured RSS
      graph; if a live-corpus RSS proof is later wanted, it is a follow-up, not blocking on this todo.
- [x] ✅ [DATA] P1. Until the flag above lands, any dispatch of this plan's prediction/tradfi/defi full-range apply
      todos MUST invoke the existing script manually in bounded sub-ranges (e.g. quarterly) rather than one full-range
      shot, or move the apply to a dedicated VM (per the heavy-compute-on-shared-host rule) instead of the interactive/
      planning host. Repo: market-tick-data-service, deployment-service (if a VM launcher path is chosen instead). —
      **DONE 2026-07-31 (slot 3)**: this todo has no worker-executable code of its own — it's a standing dispatch
      constraint on the referenced plan's OWN full-range apply todos, not a task with a stated done-when (unlike its
      `-001` sibling). Operationalized it as a single `🟡 MEMORY-SAFETY` banner right under `## Todos` in
      `plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`, covering all three affected todos (prediction
      apply, tradfi apply, defi implement-and-apply) in one place — a per-todo caveat on each was drafted first but
      reverted: that plan is already at 997/1000 lines against the hard line-cap
      (`scripts/plan-hygiene/check_line_caps.sh`), so a single DRY banner (2 net lines, now 999/1000) was used instead
      of 3 separate ones (would have pushed it to 1020, over cap). Any future worker who picks up those todos now sees
      the constraint at the point of dispatch. The permanent fix (root cause) remains `-001` (`--chunk-days` flag) —
      once that ships this banner stops mattering but is left as historical context, and the plan is close enough to its
      cap that any future addition there should budget carefully or split the plan first.

## Codex SSOTs

`/codex/05-infrastructure/vm-launcher-runbook.md` § heavy-compute-on-shared-host rule.
