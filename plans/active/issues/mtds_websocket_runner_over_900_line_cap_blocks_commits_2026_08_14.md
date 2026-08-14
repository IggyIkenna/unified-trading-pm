---
doc_type: issue
title: MTDS websocket_runner.py is 902 lines — the 900-line hard gate blocks every market-tick-data-service commit
summary: |
  market_tick_data_service/live/websocket_runner.py went from 892 to 902 lines in market-tick-data-service@0974060a
  (2026-08-14), breaching the flat 900-line file-size hard gate. quality-gates.sh now fails for every MTDS change
  regardless of what it touches, so no code can be committed to the repo until the file is split. Found while gating an
  unrelated one-line consumer migration.
status: open
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, mtds, live-trading, blocker]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: 2026-08-14
last_updated: 2026-08-14
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
    market-tick-data-service/scripts/quality-gates.sh,
    /codex/06-coding-standards/quality-gates.md,
  ]
resolved_by:
supersedes:
superseded_by:
depends_on:
locked_by:
locked_since:
source: MTDS quality-gates run during the 2026-08-14 batch-vs-live audit verification pass
---

# MTDS websocket_runner.py is 902 lines — the 900-line hard gate blocks every commit

## Evidence

`bash scripts/quality-gates.sh --no-fix` in market-tick-data-service, 2026-08-14:

```
❌ Files exceed 900 lines:
  ./market_tick_data_service/live/websocket_runner.py: 902 L
❌ Quality gates FAILED: 1 hard gate/ratchet step(s) failed.
```

Measured line counts across the introducing commit:

| Ref                                                                                                         | Lines |
| ----------------------------------------------------------------------------------------------------------- | ----- |
| `0974060a~1`                                                                                                | 892   |
| `0974060a` ("lazily register a buffer for fan-out connector tick ids in LiveWebsocketRunner.record_tick()") | 902   |
| `HEAD` / `origin/live-defi-rollout`                                                                         | 902   |

The file-size gate is a flat cap, not a ratchet baseline — there is no "existing violation" carve-out, so this is not
absorbable and every subsequent MTDS commit fails the gate no matter which files it changes. Confirmed by hitting it on
a change that touched only `scripts/` and `cli/handlers/`.

## Why it is filed separately

The blocker was twice added as a todo to
[`/plans/active/cross_ag_live_capture_parity_2026_08_14.md`](/plans/active/cross_ag_live_capture_parity_2026_08_14.md)
and twice lost to a concurrent write — a peer session in the same shared slot checkout was rewriting that plan, and
`safe-doc-push`'s post-push sync restored the landed version over the local edit both times. Filed as its own doc
because a new filename cannot collide with a peer's in-flight edit of an existing one.

## Todos

- [ ] [DATA] P0. Bring `market_tick_data_service/live/websocket_runner.py` back under 900 lines by extracting a cohesive
      unit (the tick-id fan-out buffer added by `0974060a` is the obvious candidate, being the newest and most
      self-contained addition) — DoD: `bash scripts/quality-gates.sh` exits green in market-tick-data-service, cited by
      its terminal output, not by the line count alone.
- [ ] [DATA] P0. Coordinate with whoever owns `market-tick-data-service@0974060a` before editing — the commit is hours
      old, the slot is shared, and the multi-agent rule is not to edit a peer's recently-pushed file blind — DoD: state
      in this doc who was consulted or that the owning session is confirmed finished.
- [ ] [DATA] P1. Ship the blocked consumer migration once the gate is green —
      `scripts/delete_bybit_spot_spot_nonsense_manifest_2026_07_07.py` still did
      `VENUE_DATA_TYPE_CAPABILITIES.get(_VENUE, {})` then `sorted(caps.keys())` after the typed-record migration, which
      raises `AttributeError` on the new `VenueCapabilityRecord` inside a `--apply` delete script's safety gate; the fix
      plus 10 stale prose references to the deleted `VENUE_DATA_TYPE_NO_BATCH_SOURCE` are sitting uncommitted in the
      slot-5 checkout — DoD: the fix landed via quickmerge with the gate green.
- [ ] [DATA] P2. Consider whether the file-size gate should report the delta against the cap in its failure message so
      the introducing commit is obvious without a `git show | wc -l` bisect — DoD: a decision recorded here; this is a
      nice-to-have, not a blocker.

## Progress Log

_(append dated entries here)_
