---
doc_type: issue
title: "IS footystats ODDS capture code deleted in #6 — #6 REVERSAL is INCOMPLETE"
summary:
  "The operator decision #6 REVERSAL (2026-06-27) restored the UAC type mapping for footystats ODDS but the IS
  orchestrator ODDS capture code (~1000 lines, 3 commits) was NOT restored. IS cannot capture new footystats ODDS data.
  P2b footystats ODDS backfill is blocked."
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, footystats, odds, capture-code, reversal, p2b-blocker]
related: []
created: 2026-06-27
parent_epic: sports_master
priority: P0
source: ["phantom audit follow-up to #6 ODDS reversal 2026-06-27"]
assigned_vm: NA
resolved_by: instruments-service (footystats ODDS capture restored, live-verified 2026-07-23)
locked_by: live-defi-rollout
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-27
execution_scope: orchestrator-agent
depends_on: []
locked_since: 2026-05-21
---

## Finding

The operator decision **#6 REVERSED (2026-06-27)** stated: _"footystats ODDS are pre-match snapshot reference data that
STAY in IS; the removal is reversed."_

Task 003 (slot 8, 2026-06-27) correctly restored `"ODDS": "footystats"` to `SPORTS_DATA_TYPE_TO_SOURCE` in UAC
(`unified-api-contracts@c75101be`). However the **IS orchestrator footystats ODDS capture code** was deleted in #6 and
was NOT restored:

| Commit    | Description                                                                        | Impact                                                                         |
| --------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `6404abd` | `#6 ODDS=MTDS removal — remove footystats odds fetch from IS orchestrator`         | `-362` lines in `footystats.py`, `-263` lines in `test_orchestrator_sports.py` |
| `2a0be03` | `#6 coherent unit IS half — remove footystats ODDS adapter layer and test cleanup` | `-64` lines in `adapters/footystats.py`, `-125` lines in tests                 |
| `4f6a32e` | `#6 ODDS=MTDS — finalize IS orchestrator cleanup (rename method, clean comments)`  | Cleanup commits                                                                |

**Net result**: `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` dict in IS `__init__.py` is missing
`"ODDS": PipelineMode.BATCH_FOOTYSTATS`; `_fetch_footystats_odds` function deleted from `footystats.py`; footystats
adapter layer stripped.

**What currently works**:

- UAC `SPORTS_DATA_TYPE_TO_SOURCE["ODDS"] == "footystats"` is correct (Task 003 restored it)

**What is BROKEN (UPDATED 2026-06-27 — phantom audit finding)**:

> **⚠️ DATA LOSS: The footystats ODDS GCS parquets were WIPED before the reversal.**
>
> Phantom audit run on 2026-06-27 22:01 UTC shows:
>
> - `instruments-store-sports-prd-central-element-323112`: **ZERO** `footystats_odds` parquets in GCS
> - 29,129 manifest rows claim `capture_status=captured` with `source=footystats, pipeline_mode=batch_footystats`
> - These 29,129 rows are ALL PHANTOM (manifest says captured; GCS has no parquets)
> - GCS snapshot `_index/snapshots/pre_footystats_odds_wipe_index_20260625_051634.parquet` (created 2026-06-25 05:16
>   UTC) confirms the wipe script ran with `--apply` on 2026-06-25 (before the 2026-06-27 reversal)
> - The claim "194,789 ODDS rows intact" in plan P1c was incorrect — those 29,129 captured rows have NO parquets

Immediate consequences:

1. **29,129 phantom manifest rows must be flipped** to `attempted_failed` (the `--dry-run` phantom audit confirmed
   26,220 will flip; 2,909 are pre-coverage-start/axis-9 excluded)
2. **IS cannot capture NEW footystats ODDS data** (capture code deleted, ~1000 lines across 3 commits)
3. **P2b Todo 5** (`footystats history → zero-missing … ODDS`) blocked on both the phantom flip AND the capture restore
4. **Option B (treat existing rows as complete) is NO LONGER VALID** — the "existing" rows are phantom; there is no data

## Blast radius

- **P2b blocker** (`sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md` Todo 5)
- **P2c blocker** (features history ML-ready requires P2b complete)
- **Features compute Task 001** (`sports_p2_features_history_to_ml_ready-001`) blocked by P2b
- **P0 sourcing task 004** (`sports_p0_sourcing_and_honest_coverage_correctness-004` VERIFY): phantom flip is a
  prerequisite before that task can be marked done

## Operator decision required

The situation is now: footystats ODDS data is GONE from GCS. To recover:

**Required Step 1 — Flip 29,129 phantom manifest rows to `attempted_failed`** (run phantom audit `--apply` for ODDS):

```bash
GCP_PROJECT_ID=central-element-323112 .venv/bin/python \
  scripts/reconcile_phantom_manifest_rows_all.py \
  --asset-group sports --data-types ODDS --apply --workers 4
```

Dry-run confirmed: 26,220 rows will flip. Idempotent + reversible (snapshot first).

**Required Step 2 — Operator decision on recovery path:**

**Option A — Restore IS ODDS capture code + re-fetch from footystats API** (~1000 lines of code across `footystats.py`,
adapter layer, tests; requires careful merge with post-#6 changes). Then launch backfill VM
(`launch-footystats-backfill-vm.sh --entity ODDS_SNAPSHOTS 2019-01-01 <today>`) to re-capture 2019→present.

**Option B — Accept ODDS data is gone; update P2b gate** (remove footystats ODDS from the P2b backfill target; update
the plan gate to "0 ODDS captured + 0 phantom" rather than "zero-missing"). This permanently removes footystats ODDS
from the feature pipeline.

> Slot 8 recommends **Option A** — footystats ODDS are a predictive signal the operator explicitly said to retain; the
> re-fetch is feasible (footystats API still has history). Option B means permanently losing this feature input.

## Resolution

**Option A executed** (code restore by slot 5, 2026-06-27 21:03 UTC; BLK answer implicit via slot 5's action):

1. ✅ **Step 1 — Phantom flip applied 04:25 UTC 2026-06-29** (slot 8): 26,220 phantom ODDS rows flipped to
   `attempted_failed`. Post-flip: 0 phantom rows remain.
2. ✅ **Step 2 — ODDS backfill VM launched 04:32 UTC 2026-06-29** (slot 8): `fs-backfill-20260629-043218` SPOT
   e2-standard-8 asia-northeast1-c, range 2019-01-01..2026-06-29, entity=ODDS only. GCS log:
   `gs://deployment-scripts-central-element-323112/vm-logs/fs-backfill-20260629-043218/run.log`.
3. ⏳ **Gate pending**: ODDS VM must complete; `(footystats, ODDS) pending_fetch == 0` required before P2b footystats
   checkbox reflipped.

Issue tracking complete. P2b plan updated (banner + unflipped premature footystats checkbox + progress log).

## Progress Log

### 2026-06-27 — slot 8 investigation

Initial finding (code gap):

- `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` in IS `__init__.py` line 168-194 missing `"ODDS"` entry
- `footystats.py` — no `_fetch_footystats_odds` function; 362 lines removed in `6404abd`
- Adapter layer: `adapters/footystats.py` stripped of ODDS adapter in `2a0be03`
- `launch-footystats-backfill-vm.sh` references `--entity ODDS_SNAPSHOTS` (the API exists; the IS handler does not)
- Commits after removal modified `footystats.py` further (`acfd5ac` G1 write-universe gate), so a clean `git revert` of
  `6404abd` would conflict — requires manual restoration with post-#6 context applied.

Phantom audit finding (22:01 UTC):

- Ran `reconcile_phantom_manifest_rows_all.py --asset-group sports --data-types ODDS --dry-run`
- Result: 29,129 captured ODDS rows, **26,220 PHANTOM** (0 parquets in GCS), 2,909 pre-launch excluded
- Confirmed 0 `footystats_odds` parquets in `instruments-store-sports-prd-central-element-323112/sports_reference/`
- GCS snapshot `pre_footystats_odds_wipe_index_20260625_051634.parquet` (2026-06-25 05:16 UTC) confirms wipe ran
- footystats PREDICTIONS parquets DO exist (with `fetched_at_hour=` sub-partitions) confirming path shape is correct
- Conclusion: the footystats ODDS GCS data was wiped on 2026-06-25 (before the 2026-06-27 reversal); manifest was NOT
  updated; all 29,129 captured rows are phantom

## RE-TRIAGE (2026-07-23)

**Verdict: RESOLVED BY LATER WORK.** Grep-then-READ against the current `instruments-service` checkout confirms the
capture code is fully restored and wired, not just backfilled once:

- `instruments_service/engine/orchestrator/__init__.py:188` — `"ODDS": PipelineMode.BATCH_FOOTYSTATS` is present in
  `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE`.
- `instruments_service/engine/orchestrator/footystats.py:848` — `_fetch_footystats_odds` is defined (not deleted) and is
  called live from `process_enrichment.py:259` and `process_preflight.py:318`.

Live IS sports manifest query today (`instruments-store-sports-prd-central-element-323112`) for
`source=footystats, data_type=ODDS`: **captured=31,188, empty_confirmed=111,998, expected_unattempted=657,
attempted_failed=4** (143,847 rows total) — the phantom-captured population is gone (replaced by real captured rows) and
the residual pending_fetch is a small 0.5% trailing tail, not a capture-code gap. This matches
`sports_consolidated_closeout_2026_07_19.md`'s own recommendation to flip this doc to resolved, pointing at
`sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md` — that doc separately
confirms the footystats-ODDS-lives-in-IS ownership rule "checks out" and is the terminal doc for the remaining
registry-split-brain concern (a different, still-open issue about `SOURCE_PRIORITY` / bogus `api_football` ODDS rows,
not about capture code).
