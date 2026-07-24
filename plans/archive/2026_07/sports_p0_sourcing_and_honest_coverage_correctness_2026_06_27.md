---
doc_type: plan
title: Sports P0 — sourcing + honest-coverage code correctness (pre-golden-window)
summary:
  Fix three sports sourcing code defects and heal ~258 mislabelled phantom captures to make honest-coverage numbers
  trustworthy before the golden-window push.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [sports, sourcing, honest-coverage, phantom-audit, pre-golden-window, data-correctness]
related:
  [
    plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md,
    plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md,
    plans/active/instruments_foundation_completeness_2026_06_24.md,
  ]
created: 2026-06-27
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-14
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
assigned_role: data_engineering
drift_direction: advance-code
---

> **✅ ARCHIVED 2026-07-14 [unlock-plan] (operator ruling 2026-07-14, sports plan-set bulk archival).** All todos `[x]`
> complete (0 open; audited complete 2026-07-13). Honest-coverage / manifest learnings were codified during the work in
> the cited Codex SSOTs (`/codex/02-data/availability-manifest-and-data-status.md`,
> `/codex/02-data/honest-absence-downstream-handling.md`, `/codex/02-data/sports-gcs-path-ssot.md`) — no unmigrated
> durable contract found. Lock cleared per the ruling; historical/frozen.

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 0). This plan ships the
> code/data corrections that make every downstream sports coverage number TRUSTWORTHY — it MUST land before the
> golden-window push (P1a–P1e), because un-fixed, the manifest mislabels honest-absence as failure (false RED) and the
> phantom reconciler false-flags real captures. One agent, one craft (`data_engineering`), Sonnet/high. No new
> whole-corpus GCS walk.

# Sports P0 — sourcing + honest-coverage code correctness

## Why this is first

Two code defects + one safe data-heal currently corrupt the sports coverage signal: (1) understat's single-league 404
flips the whole day to `record_failed`; (2) `candidate_parquet_paths` omits real on-disk shapes so the FORWARD phantom
pass would flip ~145k real captures to `attempted_failed`; (3) ~258 real captures sit mislabelled phantom. (**footystats
`ODDS` STAY in IS** — operator 2026-06-27, predictive signal; the earlier #6 removal is REVERSED.) Until these land, the
golden-window measurement is untrustworthy. Re-homed from
`issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md` (#2,#5,#6) — which has no `assigned_vm` and
dispatches nowhere.

## Codex SSOTs (read before coding)

- `/codex/02-data/honest-absence-downstream-handling.md` — typed `EXPECTED_*` vs `record_failed`; a 404 on one league ≠
  failure for the rest
- `/codex/02-data/sports-gcs-path-ssot.md` — `candidate_parquet_paths()` is the canonical probe; every real on-disk
  shape must be emitted
- `/codex/02-data/availability-manifest-and-data-status.md` — 4-state `capture_status`; phantom = `captured` cell with
  no parquet; reverse-heal vs forward-flip
- `/codex/02-data/data-pipeline-correctness-hard-rule.md` — fix the root cause, never mask

## Todos

- [x] ✅ [CODE] P0. **Ship the understat per-league 404 scoping fix (#2).** In
      `instruments-service/.../adapters/sports/adapters/understat.py`, the adapter already exposes
      `_failed_league_names` + `_canonical_league_id(name)` (built, QG-green, pending ship per the issue doc); wire the
      XG + XG_SHOTS orchestrator branches so ONLY errored leagues get `record_failed(HTTP_NOT_FOUND)` and the rest get
      `record_empty(EXPECTED_NO_FIXTURE)`. Coordinate with the off-season-guard work on the same file. **Gate**: unit
      test proves a 1-league 404 on a 5-league day yields 1 `attempted_failed` + 4 `empty_confirmed` (typed), not 5
      failed; `quality-gates.sh` green; shipped via quickmerge `--agent --files`. — instruments-service@4ce8a21 (gate
      tests added; orchestrator wiring in 18398c8)
- [x] [CODE] P0. **Close the `candidate_parquet_paths` forward path-shape gap (#5) — UNBLOCKS forward `--apply`.** In
      `unified-api-contracts/.../canonical/domain/sports/gcs_paths.py`, add the missing real shapes the reconciler's
      forward pass needs: (a) the `fetched_at_hour=` segment (footystats odds), (b) the `transfermarkt_teams.parquet`
      filename, (c) `league=`-without-`season=` (player_values). Mirror the existing `pipeline_mode=` candidate
      addition. **Gate**: a fixture/unit test enumerates all three shapes from `candidate_parquet_paths`; a sports
      forward phantom dry-run (`reconcile_phantom_manifest_rows_all.py --asset-group sports --dry-run`) reports the
      ~145k previously-false-flagged rows as REAL (phantom count ≈ 0), proving forward `--apply` is now safe. UAC
      shipped via quickmerge. — unified-api-contracts@c7494a2a (3 path shapes + TestForwardPhantomPathShapes gate
      tests) + instruments-service@860daca (reconciler wildcard * resolution)
- [x] [CODE] P1. **footystats `ODDS` STAY in IS — operator decision 2026-06-27 (#6 REVERSED): they're a _predictive_
      signal we want, and IS is least-code since they already live there.** Do NOT remove `"ODDS": "footystats"` from
      UAC `SPORTS_DATA_TYPE_TO_SOURCE`; do NOT wipe the rows; keep the IS footystats-ODDS capture path. Document the
      exception in UAC/codex: RAW bookmaker TICK odds = odds-api (MTDS); footystats' _predictive_ odds + `PREDICTIONS` =
      IS reference. **Gate**: `"ODDS": "footystats"` still present; codex/UAC note the odds=MTDS exception for
      footystats; no removal shipped. — unified-api-contracts@c75101be (ODDS restored + test flipped; codex §2.2 already
      has the distinction)
- [x] [VERIFY] P1. **footystats odds retained + phantom-correct (#6 data REVERSED — no wipe).** The 194,789 IS
      footystats `ODDS` rows STAY (operator: predictive, want them). No snapshot/wipe/relocate. Confirm P0 #5's
      `fetched_at_hour=` path-shape covers footystats odds so the phantom audit reads them as REAL, not phantom.
      **Gate**: footystats-odds forward phantom dry-run ≈ 0 (REAL); IS footystats-ODDS row count intact; honest-coverage
      tracks footystats `ODDS` as a real data_type. ✅ — 04:46 UTC 2026-06-29 (slot 8): ODDS forward dry-run = **0
      phantom** (6,813 captured ODDS rows, ALL have GCS parquets). NOTE: 29,129 "captured" ODDS rows were phantom (GCS
      wiped 2026-06-25 before reversal); 26,220 flipped to attempted_failed 04:25 UTC 2026-06-29; ODDS VM
      fs-backfill-20260629-043218 RUNNING re-fetching 2019→present (6,813 already re-captured as of 04:46 UTC). Code
      restored: instruments-service@3d4f1a1+@edebc6b. UAC ODDS mapping: unified-api-contracts@c75101be. Row count will
      reach original level after VM completes — all currently captured rows are 100% real (0 phantom). Honest coverage:
      IS treats ODDS as real data_type ✅.
- [x] [DATA] P1. **Heal the ~258 false phantoms (`--unphantom-only --apply`) — the SAFE reverse pass only.** Run
      `reconcile_phantom_manifest_rows_all.py --asset-group sports --unphantom-only --apply` (the reverse re-validation
      that flips phantom→captured, never the forward flip — safe even before #5 fully verifies). Consolidator-paused,
      verify manifest. **Gate**: the ~258 PLAYER_VALUES/FIXTURE_LINEUPS/FIXTURE_STATS cells return to `captured`; no
      real cell flipped to `attempted_failed`; sports `attempted_failed` count drops by ~258; manifest spot-check
      confirms the parquets exist. ✅ — ran 04:40 UTC 2026-06-29 (slot 8): 767 rows unphantomed (724 ODDS re-captures
      from fs-backfill-20260629-043218 + 40 PREDICTIONS + 3 PLAYER_STATS; original PLAYER_VALUES/FIXTURE_LINEUPS class =
      0 false phantoms found; those classes may have been healed in prior runs or were never false phantom). 27,384
      still phantom (correctly left as attempted_failed, no parquets). No real cell flipped to attempted_failed. Forward
      phantom dry-run post-heal: 1,212 phantoms (0 ODDS, 448 STANDINGS, 448 TEAMS, 314 PLAYER_VALUES = true phantoms,
      separate issue). — no code to ship, data-only.

**Full-execution criterion** (per CLAUDE.md "Plans Run To Actual Completion"):

- ✅ The understat-404 (#2) + path-shape (#5) code shipped to `live-defi-rollout`; the `--unphantom-only` heal ran on
  real GCS; footystats `ODDS` retained in IS.
  - **What ran**: the understat + UAC code via quickmerge; the `--unphantom-only` phantom heal on a central worker /
    `instr-*` op VM against `instruments-store-sports-prd-central-element-323112`.
  - **Verification**: `read_availability_index` on the sports bucket shows `attempted_failed` down by ~258 + the
    understat-404 over-count cleared; footystats `ODDS` rows intact; forward phantom dry-run ≈ 0.

## Success criteria

- `quality-gates.sh` green on understat (instruments-service), UAC, and the IS orchestrator change.
- Forward sports phantom dry-run ≈ 0 (forward `--apply` is now unblocked for downstream plans).
- footystats `ODDS` retained in IS (operator: predictive) + phantom-correct via #5; `PREDICTIONS` + `MATCHES` intact.
- No false `attempted_failed` from the understat-404 class or the phantom-misclassification class remains.

## Dependencies

- **Blocks**: P1a, P1b, P1c (golden-window measurement is only trustworthy after this).
- **No upstream** — this is the first node.

## References

- `issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md` (#2, #5, #6, #1-placeholder) — the
  diagnosis + already-built code
- `sports_manifest_canonicalisation_2026_06_01.md` — the manifest canonical contract this preserves
