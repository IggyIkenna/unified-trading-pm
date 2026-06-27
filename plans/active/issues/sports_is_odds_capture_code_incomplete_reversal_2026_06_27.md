---
doc_type: issue
title: "IS footystats ODDS capture code deleted in #6 — #6 REVERSAL is INCOMPLETE"
summary:
  "The operator decision #6 REVERSAL (2026-06-27) restored the UAC type mapping for footystats ODDS but the IS
  orchestrator ODDS capture code (~1000 lines, 3 commits) was NOT restored. IS cannot capture new footystats ODDS data.
  P2b footystats ODDS backfill is blocked."
nature: process
stage: [data-ingestion]
repos: [instruments-service]
scope: [engineer]
tags: [sports, footystats, odds, capture-code, reversal, p2b-blocker]
related: []
created: 2026-06-27
parent_epic: sports_master
priority: P0
status: active
assigned_vm: NA
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-27
---

## Finding

The operator decision **#6 REVERSED (2026-06-27)** stated: *"footystats ODDS are pre-match snapshot reference data that
STAY in IS; the removal is reversed."*

Task 003 (slot 8, 2026-06-27) correctly restored `"ODDS": "footystats"` to `SPORTS_DATA_TYPE_TO_SOURCE` in UAC
(`unified-api-contracts@c75101be`). However the **IS orchestrator footystats ODDS capture code** was deleted in #6 and
was NOT restored:

| Commit | Description | Impact |
|--------|-------------|--------|
| `6404abd` | `#6 ODDS=MTDS removal — remove footystats odds fetch from IS orchestrator` | `-362` lines in `footystats.py`, `-263` lines in `test_orchestrator_sports.py` |
| `2a0be03` | `#6 coherent unit IS half — remove footystats ODDS adapter layer and test cleanup` | `-64` lines in `adapters/footystats.py`, `-125` lines in tests |
| `4f6a32e` | `#6 ODDS=MTDS — finalize IS orchestrator cleanup (rename method, clean comments)` | Cleanup commits |

**Net result**: `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` dict in IS `__init__.py` is missing `"ODDS": PipelineMode.BATCH_FOOTYSTATS`;
`_fetch_footystats_odds` function deleted from `footystats.py`; footystats adapter layer stripped.

**What currently works**:
- 194,789 existing IS footystats ODDS rows are INTACT (were NOT wiped, confirmed by plan P1c progression)
- UAC `SPORTS_DATA_TYPE_TO_SOURCE["ODDS"] == "footystats"` is correct (Task 003 restored it)

**What is BROKEN**:
- IS cannot capture NEW footystats ODDS data (no fetch code, no pipeline_mode mapping)
- `launch-footystats-backfill-vm.sh --entity ODDS_SNAPSHOTS` would attempt to call IS but IS has no ODDS handler
- P2b Todo 5 (`footystats history → zero-missing … ODDS`) CANNOT complete without the capture code

## Blast radius

- **P2b blocker** (`sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md` Todo 5)
- **P2c blocker** (features history ML-ready requires P2b complete)
- **Features compute Task 001** (`sports_p2_features_history_to_ml_ready-001`) blocked by P2b

## Operator decision required

Two options:

**Option A — Restore the IS ODDS capture code** (~1000 lines, 3 removal commits must be reversed + integrated with
post-#6 changes `acfd5ac`, `4f6a32e`). Enables the P2b footystats ODDS backfill to run and capture 2019→present.

**Option B — Treat the 194,789 existing ODDS rows as the complete history** (accept no new ODDS backfill; P2b footystats
Todo 5 changes gate to "existing rows intact, no new pending-fetch"). Future-forward footystats ODDS captures would also
remain blocked unless the code is eventually restored.

> Slot 8 recommends **Option A** — the operator #6 REVERSAL implies ODDS data should flow into IS; 194k rows is
> incomplete history (coverage starts 2019; meaningful gaps exist in 2021-2023 era).

## Next step

Operator confirms A or B → assign to a slot to implement (Option A) or update P2b plan gate (Option B).

## Progress Log

### 2026-06-27 — slot 8 investigation

Found while investigating open finding from compacted session context:
- `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` in IS `__init__.py` line 168-194 missing `"ODDS"` entry
- `footystats.py` — no `_fetch_footystats_odds` function; 362 lines removed in `6404abd`
- Adapter layer: `adapters/footystats.py` stripped of ODDS adapter in `2a0be03`
- `launch-footystats-backfill-vm.sh` references `--entity ODDS_SNAPSHOTS` (the API exists; the IS handler does not)
- Commits after removal modified `footystats.py` further (`acfd5ac` G1 write-universe gate), so a clean `git revert` of
  `6404abd` would conflict — requires manual restoration with post-#6 context applied.
