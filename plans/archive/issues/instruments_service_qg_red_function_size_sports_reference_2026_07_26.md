---
doc_type: issue
title: instruments-service QG RED — _fetch_sports_reference_data() exceeds MAX_FUNCTION_LINES (206L > 200L)
summary: >-
  instruments-service's quality-gates.sh fails STEP "Function/class/method size exceeded" on
  instruments_service/engine/orchestrator/sports_reference.py:50 _fetch_sports_reference_data() (206 lines,
  MAX_FUNCTION_LINES=200). Discovered while rolling out an unrelated scripts/setup.sh fix
  (infra_satellite_ao_dispatch_batch1-002) — confirmed pre-existing and unrelated to that change.
status: resolved
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
resolved_by: instruments-service@2d706d2c (slot-4) + instruments-service@<pending> (slot-7, process_write.py)
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

# instruments-service QG RED — `_fetch_sports_reference_data()` exceeds MAX_FUNCTION_LINES (206L > 200L)

> **🟢 RESOLVED 2026-07-26.** `_fetch_sports_reference_data()` is back under `MAX_FUNCTION_LINES=200`
> (`instruments-service@2d706d2c` + `instruments-service@<pending>` — see `resolved_by` above and the todo below).
> Archived here (plan_health hygiene-sweep hard-gate fix, escalation `agt-24e69c`) per
> `/codex/11-project-management/issue-doc-lifecycle.md`'s archive-on-resolve rule.

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

- [x] ✅ [BACKEND] P1. **DONE 2026-07-26** — `_fetch_sports_reference_data()` is back under `MAX_FUNCTION_LINES=200`.
      Landed independently by slot-4 (`instruments-service@2d706d2c`, "extract MVP/recovery fixture filters to fix
      function-size QG violation") while slot-7 (this task's assignee) was mid-way through its OWN equivalent fix in the
      same window — a genuine same-target race, not a duplicate-work mistake on either side. slot-4's approach:
      extracted the MVP-league + recovery-allowlist filters into a NEW `sports_reference_filters.py` cohesion module (a
      same-file extraction would have pushed the sibling `sports_reference_fixtures.py` over the 900L file cap:
      896→975L) — same fix shape slot-7 had independently converged on (extract those exact two filter blocks), just a
      different target module. slot-7 adopted slot-4's already-shipped, already-tested version on conflict (git
      `show HEAD:<path>` over the redundant local edit) rather than shipping a second, functionally-identical fix.
      Verified: `bash scripts/quality-gates.sh` reports `✅ Function/class/method size OK` post-merge, no regression.

      **Related finding (same session, different file)**: fixing this exposed that `instruments-service@9c203ce1`
                                  (an earlier, unrelated `cross_cutting_satellite_ao_dispatch_batch1-012` commit, same slot) had pushed
                                  `process_write.py` from exactly 900→904 lines (`MAX_FILE_LINES` cap) — undetected by 2 full `quality-gates.sh`
                                  runs that both reported "ALL QUALITY GATES PASSED" in between. Fixed via docstring compaction (904→895L,
                                  verified format-stable post `ruff format`) — `instruments-service@<pending, ships alongside this todo>`. The
                                  SILENT-MISS mechanism (2 real, independently-confirmed violations across 2 different files/check-classes both
                                  surviving multiple full "ALL QUALITY GATES PASSED" runs) is tracked as its own, now-P1, issue:
                                  `/plans/active/issues/qg_size_gate_sentinel_skip_root_cause_2026_07_25.md` (pre-existing doc, added corroborating
                                  evidence + a new instrumentation todo this session — not duplicated here).
