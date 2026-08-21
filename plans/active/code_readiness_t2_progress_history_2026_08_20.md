---
doc_type: plan
title: Code readiness T2 — progress history (2026-08-19 to 2026-08-20)
summary: >-
  Pure historical record, split out of code_readiness_t2_refdata_marketdata_2026_08_19.md when the parent hit its
  1000-line hard cap (2026-08-21). Carries the plan-authoring entry plus the 2026-08-19/2026-08-20 Progress Log
  entries verbatim. No open todos live here — the parent plan's `## Todos` section is the live, authoritative list;
  this doc exists so the audit trail (measurements, defects found+fixed, corrections) survives without re-inflating
  the active plan.
status: active
nature: process
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, market-data-processing-service]
scope: [engineer]
tags: [code-readiness, refdata, marketdata, tranche-2, history]
related:
  [
    /plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
locked_by:
locked_since:
context_scope: [/plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md]
supersedes:
superseded_by:
depends_on: []
source: >-
  Line-cap split of code_readiness_t2_refdata_marketdata_2026_08_19.md (crossed the 1000-line hard cap during
  2026-08-21 session activity) — moved the oldest, fully-historical Progress Log content out so the parent plan's
  live todos stay under the cap without losing the audit trail. Mirrors the T3/T5 sibling plans' identical split.
assigned_role: backend_engineer
effort: low # pure archival split, zero new work
drift_direction: none
---

# Code readiness T2 — progress history (2026-08-19 to 2026-08-20)

> Pure historical record. See `/plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md` for the live todo
> list and current Progress Log.

- 2026-08-19 — Plan authored. Allocation derived by `scripts/plan-hygiene/allocate_code_readiness_tranches.py`
  against the 892-doc active corpus. No code work started yet.

- 2026-08-20 — **T5 unblocked; the coverage-grain axes were already live.** Read the live artefact
  `gs://central-element-323112-honest-coverage/2026-08-19/coverage.json` (`schema_version: 2`) through T5's own
  engine (`cursor-configs/skills/honest-coverage-dump/scripts/shard_universe.py`) rather than inspecting the
  writer. MEASURED: both `by_venue_instrument_type` (172 `(ag, venue)` pairs) and
  `by_venue_instrument_type_data_type` (184 pairs) are populated for all 5 asset_groups; `detect_grain()` returns
  `"instrument_type"`; `iter_shard_cells()` yields **3,962** cells at `(asset_group, venue, instrument_type,
  data_type)` grain. The "add `instrument_type`/`data_type` columns to the coverage payload" todo was therefore
  already satisfied in production before this tranche started — the work left was not ADDING the axes but making
  them HONEST (below). Notified T5 in their plan's `## Inbound requests` with the two caveats they must carry into
  the re-run.

- 2026-08-20 — **Shard-atom defects in the coverage writer: found by measurement, fixed, regression-tested.**
  Three defects in `instruments-service/scripts/measure_honest_coverage.py`, each measured against the live
  2026-08-19 payload before any code was touched, each with a test PROVEN to fail on the pre-fix source and pass
  on the fixed one (ran the suite against `git show HEAD:` of the file to confirm, rather than assuming):

  1. **Level-5 display label was unstable across data_types — 24 groups.** `_representative_instrument_type()` was
     called inside each `(venue, itype_fold, data_type)` group, so the case-majority could differ per data_type
     and one logical shard grew TWO keys with its data_types split between them. `sports/LADBROKES` carried both
     `'ODDS'` (`data_types=['trades']`) and `'odds'` (`data_types=['odds']`). Level 4 was already clean (0 splits)
     — only level 5 leaked, so the two projections disagreed about what one shard is called. Fix: resolve the
     label ONCE per `(venue, case-folded instrument_type)` in the level-4 pass and have level 5 reuse it.
  2. **`'nan'` leaked as a real instrument_type key — 26 keys beside 85 blank ones.** `astype(str)` renders a
     missing value as the literal `"nan"`, and the grouping key never consulted
     `_BLANK_INSTRUMENT_TYPE_SENTINELS` (which already contained `"nan"` — defined, but unused for grouping).
     Fix: normalise every null spelling to `""` in `_casefold_instrument_type_series`, so one "never stamped an
     instrument_type" shard is one cell rather than up to five.
  3. **`data_type` was never case-folded — 6 split groups** (`sports` `ODDS_MOVEMENT`/`odds_movement` and
     `ODDS_SNAPSHOT`/`odds_snapshot`; `prediction` `MARKET_LIFECYCLE`/`market_lifecycle`). Fix: new
     `_casefold_data_type_series`, applied at level 5 ONLY. Deliberately NOT applied to level 3
     `by_venue_data_type`: that dict's KEYS feed deployment-api's `/distinct-values/{asset_group}` drift panel,
     which case-sensitively tracks the in-flight uppercase migration — merging there would blind the panel to the
     drift it exists to surface. A test pins both halves of that asymmetry.

  **Denominator impact, stated as a dated change per W3's "never a silent edit" rule:** these three collapse 86
  duplicate cells, so the true distinct-shard count at this grain is **3,876**, not the 3,962 the artefact
  currently reports (nor the 3,960 the headline quotes). Per-status ROW totals are unchanged — this re-partitions
  cells, it does not drop shards: captured 58,494,203 / attempted_failed 9,648,732 / expected_unattempted
  51,892,497 / empty_confirmed 93,065,443, reachable denominator 120,035,432 on 2026-08-19. The corrected count
  reaches the artefact on the next nightly `measure-honest-coverage` cron run; this tranche does not launch it.

  **Also measured, NOT fixed here** (needs an operator ruling on denominator semantics, so it is a tracked todo
  rather than a silent edit): level 4 drops fully-retired keys via `_drop_fully_retired_nested` and level 5 does
  not, so the two levels still disagree about which shards EXIST even though they now agree on naming.

- 2026-08-20 — **T1 inbound #2 worked; T1's stated cause was wrong, the underlying defect was real and worse.**
  T1 reported three hand-rolled `KNOWN_CHAINS` literals in `instruments-service` that "will not receive the
  SCROLL/PLASMA fix". MEASURED: all three already contained SCROLL and PLASMA, so that specific claim does not
  hold. The real drift ran in BOTH directions and predates it: each copy was missing `ASTER` (a venue that is its
  own L1 — `…-ASTER` venues therefore never split) and carried a phantom `STARKNET` that UAC deliberately
  excludes (`EXTENDED-STARKNET` is a CeFi on-chain perp CLOB that must NOT be DeFi-split, per
  `engine/orchestrator/writers.py`'s `VENUE_TO_ASSET_GROUP` guard). `build_instrument_catalogue.py`'s comment
  claimed it "Mirrors the UAC `KNOWN_CHAINS` set" — it did not; that comment is corrected in place rather than
  left to mislead the next reader. All three now import the UAC set
  (`unified_api_contracts.registry.capability_declarations._defi.KNOWN_CHAINS`, the path every already-correct
  consumer in the repo uses). Verified after the change by importing the module and asserting
  `_CATALOGUE_KNOWN_CHAINS is KNOWN_CHAINS` → True, `ASTER` present, `STARKNET` absent. This is a real behaviour
  change to the catalogue read-side venue split, in the correcting direction.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
