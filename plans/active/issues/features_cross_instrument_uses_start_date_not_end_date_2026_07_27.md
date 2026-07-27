---
doc_type: issue
title:
  features-service cross_instrument's --date fallback uses --start-date instead of --end-date — likely reads the wrong
  delta_one input day (adjacent to the fixed multi_timeframe date bug)
summary: >-
  While fixing root cause B (features-multi-timeframe-service reading TODAY's date instead of the requested window —
  issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md), found that
  features_service/cross_instrument/cli/main.py's own "--date, fallback to --start-date" pattern likely reads the WRONG
  day: delta_one writes its target day's output keyed by --end-date (the actual requested day), not --start-date (the
  older lookback-window boundary), so cross_instrument's fallback to start_date would look for delta_one output at the
  wrong path whenever start_date != end_date. Not confirmed as a live failure (this session's
  CEFI/TRADFI:cross_instrument runs happened to succeed/fail for unrelated reasons — see cascade note below), so filed
  as a finding to verify, not a confirmed bug.
status: open
nature: issue
asset_group: [cefi, tradfi, prediction]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [features-service, cli, date-handling, cross_instrument, adjacent-finding]
related:
  [
    /plans/active/issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md,
    /codex/06-coding-standards/cli-convention.md,
  ]
created: 2026-07-27
priority: P3
parent_epic: infrastructure_master
source: "features_e2e_check_full_matrix_widespread_real_failures-002 (root cause B fix), slot-7, 2026-07-27"
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
---

# cross_instrument's --date fallback prefers --start-date, not --end-date (unverified, adjacent finding)

## What I found

`features_service/cross_instrument/cli/main.py` resolves its processing date as:

```python
date_val: str = (
    cast(str, args.date)
    if getattr(args, "date", None) is not None
    else cast(str, getattr(args, "start_date", ""))
)
```

`features_service/delta_one/cli/main.py` processes a full `[start_date, end_date]` range and writes output per day
within it — the caller's actual REQUESTED target day (what `pipeline_e2e_check.py --day <DAY>` resolves to) is always
`--end-date`, with `--start-date` being an older lookback boundary. When `start_date != end_date` (any multi-day
lookback window — the common case per `resolve_lookback.py`'s per-family windows), `cross_instrument` falling back to
`start_date` would look for delta_one's output under the WRONG day's `by_date/day=<start_date>/` prefix rather than the
day it actually needs.

**Not confirmed as a live bug this session** — this session's `CEFI:cross_instrument`/`TRADFI:cross_instrument` runs
either OOM'd (CEFI, unrelated to date selection — see root cause C in the referenced doc) or cascaded from
TRADFI:delta_one's own separate dependency-check failure (root cause A/F) before this date-selection question could be
isolated. Filing as a finding to verify, not asserting it's broken.

## Why it matters

If confirmed, this is the SAME class of bug as the just-fixed `multi_timeframe` issue (reading the wrong day relative to
what delta_one actually wrote), just with a different specific day (start vs. today) — worth checking alongside any
future work on this file.

## Todos

- [ ] [SCRIPT] P3. Verify whether `cross_instrument`'s `start_date` fallback ever diverges from `end_date` in a real run
      (any family/AG whose lookback window spans >1 day) and, if so, whether it actually fails to find delta_one's
      output (or coincidentally still finds valid data, as happened for CEFI in this session's run — see the referenced
      doc's Root cause C entry, where a valid 115,584-row dataset was loaded from `day=2026-06-28` despite the target
      day being `2026-06-29`). If confirmed broken, switch the fallback to `end_date` mirroring the `multi_timeframe`
      fix (`features-service` commit for root cause B).
