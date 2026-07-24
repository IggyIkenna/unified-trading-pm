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
status: resolved
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, manifest, fixtures, expected-unattempted, honest-coverage, enumerator, data-correctness, denominator]
related:
  [
    plans/active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
    plans/archive/2026_07/sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md,
    plans/active/issues/sports_manifest_unknown_league_id_2026_07_08.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-13
last_updated: 2026-07-20
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
resolved_by: instruments-service@e95838d5
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

- [x] [DATA] P1. Index safety snapshot to `_index/snapshots/` BEFORE any writes (gates all mutations). ✅ —
      `_index/snapshots/availability_index_20260713_141117.parquet` (crc32c `N9pFJg==` matches source, size 94,505,080
      bytes verified via gcs_describe_object).
- [x] [DATA] P1. Truthset-evidenced flip of the 30,892 no-fixture cells → `empty_confirmed` with
      `error_reason=EXPECTED_NO_FIXTURE__truthset_20260628_confirms_no_fixtures`, via the manifest-writer per-VM shard
      path (never a hand-edit of the consolidated index), capped at dates ≤ 2026-06-28 (truthset snapshot date). One-off
      script mirrors `flip_residual_attempted_failed_2026_06_29.py`, committed with lifecycle markers. ✅ —
      instruments-service@e95838d5 (`scripts/fixtures_eu_truthset_flip_2026_07_13.py`, dry-run then real). Flipped
      exactly **30,183**: the join reproduces 30,892 without a date filter; the ≤06-28 cap itself excludes 709 cells
      dated 06-29→07-13 (verified to the row). Shard `fixtures-eu-flip-20260713-142325.parquet` merged via
      `uts-prod-manifest-consolidator-instruments-sports` (execution -llb88); pairs provenance at
      `_audits/fixtures_eu_flip_pairs_20260713.parquet`.
- [x] [DATA] P1. Reconcile the 9 real-fixture cells from the parquet already on disk (record_captured + .write());
      re-fetch any remainder. ✅ — 8/9 reconciled from on-disk parquet; EMPEROR_CUP 2018-01-01 re-fetched live from
      api_football (af_league_id=102 season=2017, 1 fixture) + canonical parquet written, then record_captured. 9/9
      `captured` post-consolidation. NOTE: first reconcile9 shard was pruned without merging (consolidator race, see
      linked issue); idempotent re-run at 14:31Z landed all 9.
- [x] [DATA] P2. Extend the truthset audit (`audit_fixtures_via_api_football.py`) to the 7,354 outside-coverage cells
      (small API budget); evidenced flips only (no blanket flip — would fabricate absence); return keep/remove
      recommendation for the 22 non-registry leagues incl. denominator impact on other data_types (**operator decision,
      not auto-applied**). ✅ — 66 (league,season) pairs audited, 114 API calls, 0 failures; **4,494** evidenced flips
      applied (`EXPECTED_NO_FIXTURE__truthset_20260713-*`); 20 cells proven fetch_needed; 49 proven-empty held by the
      7-day in-progress-season caution. Recommendation returned (see follow-up todo below): REMOVE all **24**
      non-registry league_ids (21 numeric af/FootyStats-ambiguous ids + LA_LIGA_2 + RFPL + SCOTTISH_LEAGUE_CUP_185).
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
- [x] [VERIFY] P1. Post-consolidation verification: in-truthset ≤06-28 no-fixture pending == 0; the 9 cells resolved;
      captured count did not decrease; depth audit still green; report the honest-coverage delta. ✅ — all assertions
      PASS on the re-downloaded consolidated index (14:56Z): target class 30,183 → **0**; 9/9 captured; raw captured
      1,064,351 → 1,064,360 (+9 only, zero decreases in any data_type; atom-level set check found 0 lost captured
      atoms); depth gate exit 0 (194.50% — registry expected-counts undercount actual fixtures; the plan's earlier
      "~100.1%" phrasing measured a different registry snapshot) with the new raw-metric line printing
      `SUMMARY: depth 194.4989% | raw pending-fetch rows: 3569`. **Delta: pending 38,255 → 3,569 (−90.7%)** = 30,183
      truthset flips + 9 captured + 4,494 audit-ext flips. Residual 3,569 is fully decomposed and contains ZERO
      dishonest in-truthset cells: 2,471 non-registry-league cells awaiting the de-registration ruling + 1,098
      post-cutoff trickle (2026-06-29→07-13; ages out via daily capture; includes the 20 fetch_needed + 49
      caution-held). empty_confirmed 280,946 → 315,623 (+34,677, every row carries an EXPECTED\_-prefixed per-cell
      evidence reason).

Follow-ups (post-remediation):

- [x] [DATA] P2. ~~BLOCKED-OPERATOR-DECISION~~ RULED by operator 2026-07-13 ("drop and canonicalise") + EXECUTED
      (workflows wf_3a2669a9-eb4 + wf_5aba24bc-258). ✅ Evidence: instruments-service@21b76b3e (catalogue/enumerator
      de-registration gates + 3 one-off dereg scripts + 4 recon scripts, QG green, quickmerge-landed); index purge
      60,373 rows via CAS backup-then-rewrite (pre-purge snapshot `availability_index_20260713T153010Z.parquet`);
      captured-row accounting ZERO-LOSS: 1,651 rows parked to `_audits/parked_league_rows_20260713.parquet` (LA_LIGA_2
      691 + RFPL 868 + SCOTTISH_LEAGUE_CUP_185 16 + numeric-id scatter 76; independently re-downloaded +
      atom-reconciled) + 1 atom re-keyed LA_LIGA_2→SEGUNDA_DIVISION (crc32c-verified copy, source object deleted
      post-verification) — most re-key candidates had identical canonical twins already on disk so parked instead;
      catalogue rebuilt+promoted (24,569 rows, 0 under the 24, league-grain exactly 94); index now **94 distinct
      league_ids, set-identical to `get_expected_leagues_for_source("api_football")`**; enumerator zero-seed proof run
      enum-universe-sports-20260713-163406 scan-only: 12,951 candidate rows, **0 under the 24**, 94 leagues; depth gate
      exit 0 (98.46%), raw pending-fetch EU now **778** (from 38,255 at diagnosis). Nightly enum cron picks up the
      shipped gates after the next LDR→main promote rebuilds `instruments-service:latest` (Cloud Scheduler
      `expected-universe-v2-sports-daily` 01:30 UTC). Original recommendation text follows: (recommendation: REMOVE from
      the FIXTURES/enumeration universe — numeric ids are af-id↔FootyStats-season-id ambiguous, several are phantom
      twins of covered canonical leagues; removes 60,364 phantom denominator rows across all data_types and stops ~89
      new phantom cells/day still minted by the enum cron). MUST re-key, not delete, 1,647 captured rows:
      LA_LIGA_2→SEGUNDA_DIVISION (667 footystats ODDS + 25 MATCHES; `_LEAGUE_ALIASES`),
      SCOTTISH_LEAGUE_CUP_185→SCOTTISH_LEAGUE_CUP (16 FIXTURE_STATS; ≥100-suffix rule), RFPL (868 understat XG —
      preserve under a defined key or park until the curated-set definition). Mirror the UNKNOWN-league precedent
      (`backfill_remove_unknown_league_phantom_2026_07_09.py`: snapshot-first, hard-abort on real captured data).
- [x] [DATA] P3. Fetch the 20 proven fetch_needed post-cutoff cells (enumerated in `_audits/` audit-extension
      provenance) if the daily pipeline has not captured them by ~2026-07-20; re-check the 49 caution-held cells then
      too. ✅ RESOLVED EARLY (operator instruction 2026-07-13, evening) — instruments-service@903f2659
      (`scripts/fixtures_trickle_resolution_2026_07_13.py`). Fresh season-complete truthset
      `_audits/fixtures_truthset_20260713-172514.parquet` (94 leagues × seasons 2025-2026, 188/188 pairs, 0 fetch
      failures) re-evidenced the whole post-cutoff trickle (758 deduped pending cells 2026-06-29..07-13): 6
      proven-fixture cells (UCL/UEL/UECL July qualifiers; the rest of the earlier 20 already captured by the daily
      pipeline) re-fetched + canonical parquet + record_captured (shard `trickle-fetch-20260713`); 684 proven
      zero-fixture cells ≤ 2026-07-12 (incl. the 49 previously caution-held, now past-dated) flipped to
      `empty_confirmed` `error_reason=EXPECTED_NO_FIXTURE__truthset_20260713-172514` (shard
      `trickle-flip-20260713-20260713-172908`). Pre-write snapshot
      `_index/snapshots/availability_index_20260713T172334Z.parquet` (size+crc verified). Cron-only consolidation (no
      manual overlap); content-verified on the re-downloaded canonical: 684/684 flipped, 6/6 captured, residual pending
      2026-06-29..07-12 = **0**; exactly 68 cells dated 2026-07-13 remain (day not final — left to the daily pipeline /
      the new enumerator calendar gate).

## Progress log

- 2026-07-13: Diagnosis confirmed (workflow wf_3a605ad4-958); operator approved the 4-step remediation; execution
  dispatched (workflow wf_8f931d1a-08f: snapshot → flip+reconcile ∥ truthset-extension ∥ structural fix → final verify).
  This doc filed at dispatch time; checkboxes flip with evidence as legs complete.
- 2026-07-13 (later): Remediation COMPLETE — all 4 approved steps executed + verified (5/5 workflow legs green, 0
  errors). Pending 38,255 → 3,569 (−90.7%), zero clobbers, depth gate green, structural gate shipped
  (instruments-service@e95838d5 + @c03a95dd; nightly enum pickup after next LDR→main promote rebuilds the image, ≥
  2026-07-14 01:30 UTC). Open: the 24-league de-registration ruling (BLOCKED-OPERATOR-DECISION above) + the 20
  fetch_needed cells. Side-finding filed separately: manifest-consolidator prune race (shard pruned without merging when
  two executions overlap) — [[manifest_consolidator_prune_race_overlapping_executions_2026_07_13]]
  (plans/active/issues/manifest_consolidator_prune_race_overlapping_executions_2026_07_13.md).
- 2026-07-13 (night): Post-cutoff trickle backlog resolved through 2026-07-12 per operator instruction (see the flipped
  P3 todo above for full evidence) — raw pending-fetch FIXTURES EU now **68** (all dated 2026-07-13, ages out via the
  daily pipeline; was 778 this afternoon, 38,255 at diagnosis). All open todos in this doc are now complete; remaining
  watch item: confirm the nightly enumerator calendar gate goes live after the next LDR→main image rebuild
  (`expected-universe-v2-sports-daily`, ≥ 2026-07-14 01:30 UTC).
- 2026-07-13 (final): CLOSED OUT. (1) The independent verifier found 20 pre-window pending cells (2026-05-20→06-24)
  outside every sweep's date bounds — all 20 proved to be **manifest-orphans** (canonical parquets already on disk with
  truthset-exact row counts); reconciled to `captured` via per-VM shard `fetch20-20260713` (zero API fetches, 20/20
  verified by content post-consolidation 17:56:44Z; script `--vm-name` param shipped instruments-service@270509fd).
  **Pending for ALL dates ≤ 2026-07-12 = 0; total pending = the 68 today-cells only.** (2) Calendar-gate rollout
  CONFIRMED for tonight: promote PR #765 auto-merged (main@8299e3dc), Cloud Build 3a077ae1 SUCCESS
  (`:latest`=sha256:5f2f029f, tagged 8299e3d), all 4 sports Cloud Run jobs repinned (jobs also resolve `:latest` at
  execution time) — tonight's 01:30 UTC run executes the new gate. (3) Related fixes shipped same-day: oscillation guard
  instruments-service@ba306543 (+21 atoms repaired; 189 parked in
  [[sports_index_recency_masked_captured_atoms_2026_07_13]]) and consolidator prune-race fix
  unified-trading-library@97212d3b (prod fleet rollout in flight). Residual work when 2026-07-13 closes: daily fetch
  captures today's match-day cells; one evidenced flip pass for today's no-fixture remainder (same pattern/script).
- 2026-07-13 (evening): 24-league de-registration RULED + EXECUTED + independently verified (see flipped todo above for
  full evidence). Sports availability index now carries exactly the 94-league trading universe; raw pending-fetch EU 778
  (was 38,255 this morning). Execution note: the first executor agent completed every mutation (re-key, park, purge,
  catalogue rebuild) with in-flight verification but died before shipping; a finisher leg re-ran QG (green), produced
  the enumerator zero-seed proof, and quickmerge-landed the 12 files as instruments-service@21b76b3e. Verifier also
  attributed a benign 21-atom captured→empty_confirmed oscillation in SEGUNDA_DIVISION/BRASILEIRAO to a generic
  16:24:30Z full-index dedup rewrite (pre-existing behavior, objects verified on disk), NOT the purge. Remaining open
  here: the P3 fetch_needed re-check (~2026-07-20) below.
- 2026-07-14 (day-closeout of 2026-07-13): the 68 intentionally-deferred 2026-07-13 cells RESOLVED now the day is final.
  Pre-write snapshot `_index/snapshots/availability_index_20260714T000752Z.parquet` (80,290,383 bytes, crc32c `Vr7oSQ==`
  verified). Enumeration on the downloaded canonical: exactly 68 deduped pending FIXTURES EU cells, ALL dated 2026-07-13
  (one per league; 0 pre-window residue; 0 dated later). Fresh season-complete truthset
  `_audits/fixtures_truthset_20260714-001053.parquet` (94 leagues × seasons 2025-2026, 188/188 pairs, 0 failures; built
  00:10-00:12Z 07-14 — postdates the day's end; NOTE the audit script's default bucket lacks the `-prd-` segment,
  artifact server-side copied into the prd `_audits/`, size+crc verified). Classification: **68/68 proven zero-fixture
  on 07-13** (66 by day-absence within truthset-evidenced seasons; COPA_MX + GREEK_SUPER_LEAGUE_2 by season-empty query
  evidence — fixtures=0 for BOTH 2025+2026) → all 68 flipped `empty_confirmed`
  `error_reason=EXPECTED_NO_FIXTURE__truthset_20260714-001053` (shard `closeout-0713-flip-20260714-001955`, dry-run
  first). Side-finding fixed in-scope: ALLSVENSKAN + BRASILEIRAO_SERIE_B 2026-07-13 were stamped
  `empty_confirmed/EXPECTED_NO_FIXTURE` at 00:02Z 07-14 (daily run, calendar built from the now-stale 07-13T17:25
  truthset) but the FRESH truthset proves 3 fixtures existed — both re-fetched live from api_football (1+2 rows),
  canonical parquets written, record_captured + explicit .write() (shard `closeout-0713-fetch`). Script's flip window
  parametrized (`--flip-cutoff-date`/`--backlog-lo-date`, defaults preserve the original window) — shipped
  instruments-service@a771e3e2 via the dirty-deps carve-out (QG blocked solely by UAC@7354de78 ICE-index golden drift in
  `test_expected_universe_golden[tradfi]`; regen belongs to that tradfi plan — annotated, not fixed, collision risk; all
  other gates green, 4334 passed). Cron-only consolidation (per-minute Cloud Run job; both shards absorbed ≤2 cycles, no
  manual executions). Content verification on the re-downloaded canonical: 68/68 flipped with the fresh reason; 2/2
  captured (row_count 1 and 2); **residual deduped pending FIXTURES EU for dates ≤ 2026-07-13 = 0**; zero captured-count
  decreases in any data_type (atom-level: 2 blank-asset_group ARGENTINA_PRIMERA_NACIONAL 07-04/07-05 atoms were re-keyed
  to `asset_group=sports` with identical row_counts by a concurrent 23:49Z re-assertion sweep — not a loss; FIXTURES
  captured atoms 58,649 → 93,877 incl. that sweep's +35k). Pairs/cells provenance:
  `_audits/closeout_0713_flip_pairs_20260714.parquet` + `_audits/closeout_0713_fetch_cells_20260714.csv`. The
  post-cutoff trickle class in this issue is now fully closed through 2026-07-13; remaining open here: the P3
  fetch_needed re-check (~2026-07-20).
- 2026-07-14 02:00Z: **CALENDAR GATE LIVE AND VERIFIED IN PRODUCTION.** The 01:30Z scheduled run OOM'd at the old
  8Gi/2cpu (first run with the heavier new-image profile — captured-set suspect, tracked in the enum issue doc); job
  bumped to 16Gi/4cpu and re-executed: expected-universe-v2-sports-v97dj GREEN 01:57:24Z. Run log evidence: calendar
  gate ON (4 truthset artifacts unioned incl. tonight's 20260714-001053, 60,213 fixture-days, 94 leagues),
  `EXPECTED_NO_FIXTURE: 38` seeded as empty_confirmed (phantom minting dead), oscillation guard dropped 35
  empty_confirmed rows whose atoms are captured ("a seeder never overrides capture evidence" — 35 saves on first night),
  45,267 candidates written, run_id enum-universe-sports-20260714-015652. The full remediation chain — evidenced flips,
  de-registration, calendar gate, oscillation guard, day-closeout — is now operating end-to-end.
- 2026-07-14 (fixes): **The fixture day-boundary staleness class flagged in the 07-14 closeout is now FIXED in code**
  (operator-approved 3-fix set, shipped instruments-service@bd6b797a + @c78c7a0e via the dirty-deps direct-push
  carve-out — quickmerge pre-flight blocked solely by live foreign UTL WIP; full `quality-gates.sh --no-fix` GREEN on
  the shipped tree, sentinel at 0782f9af; the a771e3e2-era tradfi golden drift is gone, fixed upstream by bdb2dc69).
  **FIX 1 — T+1 closing re-poll** (@c78c7a0e): `sports_fixtures_daily_repoll` window extended to `[today-1, today+8]`
  (`_DEFAULT_LOOKBACK_DAYS=1`, parameterized `lookback_days=`) so the day just ended gets one final post-day-end upsert
  — finished-overnight FT results land (the status=1H mid-game capture class) and late reschedules stamp the closed day;
  docstring Window contract + behavior tests updated, dedicated T+1 test added. **FIX 2 — evidence-freshness rule in the
  enumerator calendar gate** (@bd6b797a): `_AfFixtureCalendar` carries a per-(league, season) evidence clock parsed from
  the truthset artifact NAME (producer run*ts — immutable under server-side copies, unlike GCS `timeCreated`, which the
  closeout's own copy would have reset; rationale in `_af_truthset_built_at`); `is_no_fixture_day` requires
  `evidence_built_at > end of the stamped day (UTC)`, bridged inter-season-gap days need BOTH adjacent season queries
  fresh; stale-covered days keep the pending `expected_unattempted` seed — a stale absence stamp is now structurally
  impossible. Unit tests include the exact ALLSVENSKAN 2026-07-13 scenario (stale 20260713-172514 calendar covering
  07-13 → pending, NOT EXPECTED_NO_FIXTURE; fresh 20260714-001053 → stampable). **FIX 3 — audit script prd bucket
  default** (@bd6b797a): `audit_fixtures_via_api_football.py` default bucket now resolves via
  `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")` (runtime-verified ==
  `instruments-store-sports-prd-central-element-323112`, write blob under the gate's `\_audits/fixtures_truthset*`union
  prefix — no more server-side copies);`--bucket` stays as the explicit override. **Rollout**: tonight's 16Gi
  re-execution ran the PREVIOUS image — the nightly enum (`expected-universe-v2-sports-daily`, 01:30Z) picks up FIX 2
  only after the next LDR→main promote rebuilds `instruments-service:latest`; until then the 00:0xZ daily-run ordering
  can still stamp same-day absences off a stale calendar, and the day-closeout sweep remains the backstop. Same-commit
  inherit: 5 stranded empty-string-fallback `# noqa`annotations in`reconcile_lending_indices_phantom.py` (dead autostash
  WIP; ratchet restored to exactly the 366 baseline).
