---
doc_type: issue
title: instruments-service QG RED — _fetch_sports_reference_data() exceeds MAX_FUNCTION_LINES (206L > 200L)
summary: >-
  instruments-service's quality-gates.sh fails STEP "Function/class/method size exceeded" on
  instruments_service/engine/orchestrator/sports_reference.py:50 _fetch_sports_reference_data() (206 lines,
  MAX_FUNCTION_LINES=200). Discovered while rolling out an unrelated scripts/setup.sh fix
  (infra_satellite_ao_dispatch_batch1-002) — confirmed pre-existing and unrelated to that change.
status: open
nature: process
asset_group: [sports]
stage: [meta]
repos: [instruments-service]
scope: [engineer]
tags: [quality-gates, coding-standards, sports, function-size]
related: [/plans/active/sports_consolidated_closeout_2026_07_19.md]
created: 2026-07-26
parent_epic: infrastructure_master
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
priority: P2
depends_on: []
source:
  [
    "instruments-service quality-gates.sh run 2026-07-26 (slot-11, task infra_satellite_ao_dispatch_batch1-002)",
    "instruments_service/engine/orchestrator/sports_reference.py:50",
  ]
---

## What I found

Running `bash scripts/quality-gates.sh` on `instruments-service` (to verify an unrelated `scripts/setup.sh` change)
fails with:

```
❌ Function/class/method size exceeded:
  ./instruments_service/engine/orchestrator/sports_reference.py:50:_fetch_sports_reference_data(): 206L
```

`MAX_FUNCTION_LINES` default is 200 (`scripts/quality-gates-base/base-service.sh:194`); the function is 6 lines over.
Confirmed **pre-existing and unrelated** to my change: my commit (`instruments-service@fb125d09`) touches only
`scripts/setup.sh`; `git log` shows `sports_reference.py` was last touched 3 commits earlier (`b00e4433` "restrict
per-fixture sports enrichment to MVP leagues, not the wider FIXTURES curated universe").

This is a hard-failing gate (not a ratchet/baseline-warn) — `instruments-service` QG is RED for ANY commit until this is
fixed, blocking all shipping in this repo under the green-tree rule.

## Why it matters

Blocks the `scripts/setup.sh` fleet-rollout leg for `instruments-service` (part of
`plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md` item "Fix the `scripts/setup.sh` bootstrap-uv fallback
… + roll it out fleet-wide") and blocks every OTHER pending commit to this repo until fixed.

## Recommended decision

Split `_fetch_sports_reference_data()` (or extract a helper) to bring it back under 200 lines. This is sports-domain
orchestration logic (api_football adapter enrichment fetch), not infra — routes to a data/backend-engineering craft, not
this issue's author's craft (infra).

- [ ] [BACKEND] P1. Split/refactor `_fetch_sports_reference_data()` in
      `instruments-service/instruments_service/engine/orchestrator/sports_reference.py:50` to bring it under the
      `MAX_FUNCTION_LINES=200` cap (currently 206L) — extract a helper function for one of its internal phases (e.g. the
      per-fixture enrichment call or the manifest-write block) without changing behavior. **Done when**:
      `bash scripts/quality-gates.sh` in `instruments-service` no longer reports "Function/class/method size exceeded"
      for this function, and the rest of the gate stays green. Repo: instruments-service.
