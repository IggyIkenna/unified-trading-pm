---
doc_type: issue
title:
  "instruments-service sports_reference_core.py/sports_reference_fixtures.py exceed the 200L/50L function-size gate on
  HEAD — surfaced only by a full (non-sentinel-skipped) quality-gates.sh run"
summary:
  "Discovered incidentally while shipping an unrelated fix (measure_honest_coverage.py column-prune hardening,
  2026-07-16). A full, unscoped bash scripts/quality-gates.sh run on a clean live-defi-rollout HEAD (a66fc295, files
  confirmed via `git status` NOT dirty/WIP) fails the [5/6 SIZE CHECKS] Function/class/method size gate: 3 functions
  across 2 files the reporting agent never touched: sports_reference_core.py:139
  _AfManifestHooks.emit_empty_gaps_for_entity() 89L (limit 50L for a class method), sports_reference_core.py:230
  _fetch_teams_and_standings() 205L (limit 200L), sports_reference_fixtures.py:518 _write_per_fixture_entities() 253L
  (limit 200L). quality-gates.sh's own comment block explicitly says these two files were DECOMPOSED and REMOVED from
  FUNCTION_SIZE_EXTRA_EXCLUDES on 2026-06-11 because they were supposed to 'now pass the 900-line/200-line gates
  directly' — meaning a later commit (candidates: a66fc295 'stop LEAGUE_MAP_INCOMPLETE record_failed...', 493393c8
  'api_football blank-league_id + FIXTURES-completeness orphan bugs...', 86cc71ff 'presence-based honest absence...',
  all same-day 2026-07-16 sports-domain commits) re-grew one or more of these functions past the ratchet without the
  size gate catching it at commit time. Root-cause hypothesis (not confirmed): quality-gates.sh has a
  green-content-sentinel that skips the expensive TESTS+TYPE CHECK+SIZE CHECK phases when the tree is byte-identical to
  the last known-green run; if these sports commits landed via a workflow that reused a stale sentinel (or the
  size-check ran but its failure was non-fatal at the time under a different violation-budget), the regression could
  ship silently. NOT a data-correctness bug — pure code-quality/maintainability ratchet debt. Did not block the
  reporting agent's own change (measure_honest_coverage.py is a different file/subsystem and passed every check on its
  own scoped test file); documented per the Findings-triage HARD RULE (outside every plan -> issue doc) rather than
  fixed inline, since decomposing 3 functions (up to 253L) in a sports/api_football domain the reporting agent does not
  own carries real regression risk without domain review."
status: resolved
nature: issue
asset_group: [sports]
stage: [meta]
repos: [instruments-service]
scope: [engineer]
tags: [code-quality, function-size, qg-ratchet, sports, quality-gates, sentinel-skip]
related: [/plans/active/codex_violations_ratchet_to_five_2026_06_10.md]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by: instruments-service@ac22305c
locked_by:
source: >-
  discovered while executing a defence-in-depth P2 todo in data_status_page_ux_and_canonicalisation_2026_07_16.md § "P1
  — Honest Coverage: remaining hardening" (unrelated file/subsystem) — a full bash scripts/quality-gates.sh run (not the
  usual QG_SLICE-scoped/sentinel-shortcut path) surfaced this pre-existing violation on HEAD.
depends_on: []
---

# instruments-service sports_reference function-size gate regression (pre-existing, HEAD)

## What was found

Running the FULL `bash scripts/quality-gates.sh --no-fix` (all 6 phases, no `QG_SLICE` scoping) against a clean
`live-defi-rollout` HEAD (`a66fc295`, `git status` confirmed no dirty/WIP on these files) fails phase 5's
Function/class/method size check:

```
❌ Function/class/method size exceeded:
  ./instruments_service/engine/orchestrator/sports_reference_core.py:139:_AfManifestHooks.emit_empty_gaps_for_entity(): 89L
  ./instruments_service/engine/orchestrator/sports_reference_core.py:230:_fetch_teams_and_standings(): 205L
  ./instruments_service/engine/orchestrator/sports_reference_fixtures.py:518:_write_per_fixture_entities(): 253L
```

Limits (from `unified-trading-pm/scripts/quality-gates-base/base-service.sh`): `MAX_FUNCTION_LINES=200`,
`MAX_METHOD_LINES=50`, `MAX_CLASS_LINES=900`, `MAX_FILE_LINES=900`.

## Why this is surprising

`instruments-service/scripts/quality-gates.sh`'s `FUNCTION_SIZE_EXTRA_EXCLUDES` comment block (lines ~169-191)
explicitly documents that `sports_reference.py` was split into `sports_reference_core.py` /
`sports_reference_fixtures.py` sibling modules on 2026-06-11 specifically so they'd "now pass the 900-line/200-line
gates directly" and were REMOVED from the exclude list on that basis. This full-gate run proves that guarantee no longer
holds for 3 functions across the two split modules.

## Likely cause (not confirmed — needs the owning team's investigation)

`git log -1` on both files points to `a66fc295` ("fix(sports): stop LEAGUE_MAP_INCOMPLETE record_failed for
out-of-universe per-fixture rows", 2026-07-16 00:11:55 UTC). Same-day sibling commits `493393c8` ("api_football
blank-league_id + FIXTURES-completeness orphan bugs...") and `86cc71ff` ("presence-based honest absence...") are also
same-day sports-domain candidates. One or more of these likely grew a function past its ratchet limit without the size
gate blocking the commit — which would only happen if that commit's own quality-gates run either (a) used a
green-content-sentinel shortcut that skipped the SIZE CHECKS phase, or (b) ran the gate scoped (`QG_SLICE=...`) in a way
that excludes phase 5.

## Why this is filed as an issue, not fixed inline

The reporting agent's own task was a column-prune/`read_dictionary` memory hardening in
`scripts/measure_honest_coverage.py` — a different file, different subsystem (Layer-2 coverage measurement vs.
sports/api_football fixture ingestion), with zero code relationship to the 3 flagged functions. Per the Findings-triage
HARD RULE, an out-of-plan finding this size (decomposing 3 functions, one of them 253 lines, in a domain — sports
fixture/entity persistence — the reporting agent does not own) is not a same-commit or ≤30-min fix; it needs the owning
engineer to decompose the functions with domain context, the same way the 2026-06-11 split did for the rest of the
module.

## Acceptance

- [ ] [BACKEND] P3. Decompose `_AfManifestHooks.emit_empty_gaps_for_entity()` (89L → ≤50L),
      `_fetch_teams_and_standings()` (205L → ≤200L), and `_write_per_fixture_entities()` (253L → ≤200L) into sibling
      helper functions/methods, mirroring the 2026-06-11 `sports_reference.py` decomposition pattern (pure code motion,
      no behavior change).
- [ ] [SCRIPT] P3. Root-cause WHY the size gate didn't block whichever commit introduced this (sentinel-skip vs
      scoped-gate run) and note the fix/process change so future same-day sports commits can't silently regress this
      ratchet again.
- [ ] [SCRIPT] P3. Re-run a FULL (non-sliced) `bash scripts/quality-gates.sh` and confirm phase 5's
      Function/class/method size check passes clean for these 2 files.

## RE-TRIAGE (2026-07-23)

**Verdict: RESOLVED BY LATER WORK.** Re-measured the 3 flagged functions directly against current `live-defi-rollout`
HEAD in `instruments-service`:

- `_AfManifestHooks.emit_empty_gaps_for_entity()` — now `sports_reference_core.py:221`, spans lines 221-246 (26 body
  lines, well under the 50L method limit); originally 89L.
- `_fetch_teams_and_standings()` — now `sports_reference_core.py:569`, spans lines 569-599 (31 lines, well under 200L);
  originally 205L.
- `_write_per_fixture_entities()` — now `sports_reference_fixtures.py:854`, spans to EOF at line 893 (~40 lines, well
  under 200L); originally 253L.

Root cause + fix: `instruments-service@ac22305c` ("fix(sports): decompose 3 oversized orchestrator functions past size
gate", 2026-07-21) decomposed all 3 into 9 named helpers (`_fetch_and_cache_teams`/`_write_teams_and_venues`/
`_fetch_and_cache_standings`/`_write_standings_per_league`; `_prepare_fixture_entity_df`/
`_write_fixture_entity_per_league`/`_handle_empty_fixture_entity`; `_presence_guarded_captured_leagues`/
`_emit_empty_gap_for_league`) and removed the two files from `FUNCTION_SIZE_EXTRA_EXCLUDES` again — confirmed the
current `scripts/quality-gates.sh` comment block (lines ~191-200) documents this exact history and the files carry no
active exclusion entry today.

**New finding, flagged not fixed (outside this doc's 4 assigned files)**: this issue is a near-exact duplicate of
`plans/active/issues/instruments_service_codex_compliance_ceiling_drift_2026_07_20.md`, which documents the identical 3
functions with the identical line counts (89L/205L/253L) as a "regrowth by 2026-07-20." Both were resolved by the same
`ac22305c` commit, but that other doc's `status:` is still `open` and its `resolved_by:` is still blank as of this
re-triage — it was not in this agent's assigned slice so it was left untouched, but it should be re-triaged/closed too.

Root-cause-of-the-gate-miss (this doc's 2nd acceptance item) was never separately investigated and remains open in
spirit, though moot now that the exclusion-workaround path was abandoned in favor of an actual decomposition; the
original `- [ ]` acceptance checkboxes are left unchanged per the additive-annotation instruction.
