---
doc_type: issue
title:
  Sports FIXTURES pending_fetch "regression" (0 → 38,277) is phantom denominator inflation by the expected-universe
  enumerator — 30,892 truthset-confirmed no-fixture days seeded expected_unattempted and never resolved; remediation
  approved + in execution 2026-07-13
summary: |
  The P2a plan recorded FIXTURES pending EU regressing 0 → 38,277 since the 2026-06-29 gate pass and suspected the
  2026-07-08 unknown_league_backfill index op. Forensics (2026-07-13, snapshot diffs of
  _index/availability_index.parquet vs the 2026-06-28 21:39 snapshot and the 07-08 pre-op backup) CONFIRMED a
  different root cause: the nightly enum-universe-sports enumerator (_enumerate_v2_sports alive-day seeding) mints an
  expected_unattempted row for every alive (league, day) with no manifest row; run 20260628-213115 minted 32,303
  FIXTURES rows ~80 min BEFORE the truthset recovery, and the nightly cron adds ~60-130/day. The backfill/truthset
  recovery only wrote rows for days WITH fixtures, so no-fixture days (cups/second divisions: sparse calendars) were
  never resolved to empty_confirmed. The 07-08 op is exonerated (its pre-op backup already held 37,963 of the rows,
  byte-identical). "0 pending at gate pass" was a DIFFERENT metric (fixture-count depth vs LEAGUE_REGISTRY,
  100.10%); raw EU was already ~40,844 that night — the two metrics diverged silently. Row breakdown (38,255 deduped):
  30,892 truthset-confirmed no-fixture days (api-football's own season-complete data proves nothing was played);
  9 with real fixtures (3/3 sampled already have fixtures.parquet on disk — manifest-row gaps, not data gaps);
  7,354 outside truthset coverage (22 non-registry leagues × ~144 days + 2026-dated cells). Features inputs are
  essentially unaffected (captured corpus intact: 115,782 league-day cells / ~116,149 fixtures); the damage is the
  honest-coverage denominator and gate/foundation-freeze risk. Operator approved the 4-step remediation 2026-07-13
  (executing via workflow wf_8f931d1a-08f, snapshot-gated).
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, manifest, fixtures, expected-unattempted, honest-coverage, enumerator, data-correctness, denominator]
related:
  [
    plans/active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
    plans/active/sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md,
    plans/active/issues/sports_manifest_unknown_league_id_2026_07_08.md,
    codex/02-data/availability-manifest-and-data-status.md,
    codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-13
last_updated: 2026-07-13
parent_epic: sports_master
priority: P1
source: |
  Operator session 2026-07-13 — surfaced as the "38,277 FIXTURES pending regression" easy-unblock in the P2a plan
  during the sports plans audit; diagnosed by forensics workflow wf_3a605ad4-958; remediation approved by operator
  and dispatched as workflow wf_8f931d1a-08f.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# Sports FIXTURES pending-EU phantom denominator — diagnosis + approved remediation

## Root cause (CONFIRMED 2026-07-13)

1. **Enumerator alive-day seeding**: `enumerate_expected_universe.py::_enumerate_v2_sports` (~L794-795, 1648-1649) seeds
   `expected_unattempted` for every alive (league, day) with no manifest row. FIXTURES is the one data_type where the
   fixture calendar itself is the fetched artifact — so seasons alive ~300 days with matches on ~50 days over-seed
   massively (AUSTRALIA_CUP 970 rows, JLEAGUE_CUP 811, NORWEGIAN_CUP 811, …).
2. **Resolution step never ran**: the history backfill + truthset recovery iterated over fixtures that exist; nobody
   walked the seeded no-fixture days and stamped `empty_confirmed`. Nightly enum keeps minting ~60-130/day.
3. **Metric divergence**: the 06-29 "0 pending" gate (`run_fixture_completeness_audit_2026_06_25.py:177,205-230`) is
   depth-based (captured vs LEAGUE_REGISTRY counts; 77,755/77,677 = 100.10%) and only flags leagues with shortfall —
   blind to raw EU rows. Raw pending was already 40,844 at the 2026-06-28 21:39 snapshot. Never was 0. No regression.
4. **07-08 `unknown_league_backfill` op exonerated**: pre-op backup already held 37,963 pending rows; 37,773
   byte-identical atoms to today's set; 0 flipped-from-captured; the op removed exactly the 2,373 UNKNOWN rows + 1
   catalogue row per its issue doc.

Evidence artifacts: forensics scripts + outputs in session scratchpad `fixtures_regression/` (analyze_out.txt,
truthset_join.py, clobber_check.py); index snapshots current/2026-06-28/pre-07-08-bak; truthset
`_audits/fixtures_truthset_20260628-225553.parquet` (194,803 fixtures, season-complete from api-football).

## Row breakdown (38,255 deduped atoms, all source=api_football, blank error_reason)

| Bucket                           | Count  | Verdict                                                                                 |
| -------------------------------- | ------ | --------------------------------------------------------------------------------------- |
| In-truthset, no fixture that day | 30,892 | Genuine absence (api-football season-complete data) — should be `empty_confirmed`       |
| In-truthset, real fixtures exist | 9      | Manifest-row gaps; 3/3 sampled have fixtures.parquet on disk already                    |
| Outside truthset coverage        | 7,354  | 22 non-registry leagues × ~144 days + 2026-dated cells — needs evidence before any flip |

Features impact: none material (captured corpus intact; only the 9 cells were ever plausibly real, and their data is on
disk). Impact is honest-coverage % + foundation-gate / P2d final-gate risk.

## Approved remediation (operator, 2026-07-13) — executing via workflow wf_8f931d1a-08f

- [ ] [DATA] P1. Index safety snapshot to `_index/snapshots/` BEFORE any writes (gates all mutations).
- [ ] [DATA] P1. Truthset-evidenced flip of the 30,892 no-fixture cells → `empty_confirmed` with
      `error_reason=EXPECTED_NO_FIXTURE__truthset_20260628_confirms_no_fixtures`, via the manifest-writer per-VM shard
      path (never a hand-edit of the consolidated index), capped at dates ≤ 2026-06-28 (truthset snapshot date). One-off
      script mirrors `flip_residual_attempted_failed_2026_06_29.py`, committed with lifecycle markers.
- [ ] [DATA] P1. Reconcile the 9 real-fixture cells from the parquet already on disk (record_captured + .write());
      re-fetch any remainder.
- [ ] [DATA] P2. Extend the truthset audit (`audit_fixtures_via_api_football.py`) to the 7,354 outside-coverage cells
      (small API budget); evidenced flips only (no blanket flip — would fabricate absence); return keep/remove
      recommendation for the 22 non-registry leagues incl. denominator impact on other data_types (**operator decision,
      not auto-applied**).
- [x] [CODE] P1. Structural: season-fixture-calendar gate for FIXTURES in `_enumerate_v2_sports` (mirroring the
      footystats/understat gates; alive-day fallback where no calendar evidence exists — never silently shrink the
      denominator) + surface the raw EU pending metric in `run_fixture_completeness_audit_2026_06_25.py` so the depth
      gate and the raw index metric can never silently diverge again. ✅ — instruments-service@c03a95dd. Gate:
      `_AfFixtureCalendar` / `_build_af_fixture_calendar` (union of `_audits/fixtures_truthset_*.parquet`, consecutive
      seasons bridge inter-season gaps; jumps don't) → seeding branch yields `EXPECTED_NO_FIXTURE` (`empty_confirmed`)
      for calendar-evidenced no-fixture days, unchanged `expected_unattempted` for match days / no-evidence cells.
      Audit: `_count_raw_pending_fetch` (dedup latest-`written_at` per atom, non-`EXPECTED_` reasons) printed as
      `SUMMARY: depth X% | raw pending-fetch rows: N`. Evidence: QG green (ALL QUALITY GATES PASSED, 106s, exit 0);
      runtime-verified on real artifacts — truthset builds 94-league calendar, gate branch exercised both ways, metric
      reproduces the 38,255 forensics count on the 2026-07-13 index copy; 8 new unit tests. Nightly pickup: Cloud
      Scheduler `expected-universe-v2-sports-daily` (`30 1 * * *` UTC) → Cloud Run job on `instruments-service:latest` —
      effective after LDR→main promote rebuilds the image (next run ≥ 2026-07-14 01:30 UTC).
- [ ] [VERIFY] P1. Post-consolidation verification: in-truthset ≤06-28 no-fixture pending == 0; the 9 cells resolved;
      captured count did not decrease; depth audit still green; report the honest-coverage delta.

## Progress log

- 2026-07-13: Diagnosis confirmed (workflow wf_3a605ad4-958); operator approved the 4-step remediation; execution
  dispatched (workflow wf_8f931d1a-08f: snapshot → flip+reconcile ∥ truthset-extension ∥ structural fix → final verify).
  This doc filed at dispatch time; checkboxes flip with evidence as legs complete.
