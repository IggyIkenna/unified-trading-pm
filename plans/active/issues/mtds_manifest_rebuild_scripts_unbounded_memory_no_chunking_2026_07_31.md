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
status: open
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

- [ ] [BACKEND] P2. Add a `--chunk-days` (or equivalent) flag to `rebuild_prediction_manifest.py` /
      `rebuild_tradfi_manifest.py` / `rebuild_defi_manifest.py` that internally loops over `[--start-date, --end-date]`
      in bounded sub-windows, flushing/discarding each sub-window's aggregates before starting the next — mirroring the
      `CHUNK_SIZE`-day pattern the VM backfill launchers already use for exactly this reason. Repo:
      market-tick-data-service. Done when: a full-range invocation with `--chunk-days` set shows bounded (non-growing
      across chunk boundaries) RSS on a real multi-month test range, with a regression test asserting the chunking
      loop's date-boundary math (no gaps/overlaps between chunks).
- [ ] [DATA] P1. Until the flag above lands, any dispatch of this plan's prediction/tradfi/defi full-range apply todos
      MUST invoke the existing script manually in bounded sub-ranges (e.g. quarterly) rather than one full-range shot,
      or move the apply to a dedicated VM (per the heavy-compute-on-shared-host rule) instead of the interactive/
      planning host. Repo: market-tick-data-service, deployment-service (if a VM launcher path is chosen instead).

## Codex SSOTs

`/codex/05-infrastructure/vm-launcher-runbook.md` § heavy-compute-on-shared-host rule.
