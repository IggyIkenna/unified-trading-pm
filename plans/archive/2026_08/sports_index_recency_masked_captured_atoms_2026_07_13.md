---
doc_type: issue
title:
  Sports index — 189 atoms where a later empty_confirmed row recency-masks a still-present captured row (residue of the
  2026-07-13 captured->empty_confirmed oscillation; NOT blind-repaired, needs per-subclass adjudication)
summary: |
  While repairing the 2026-07-13 oscillation (21 captured atoms erased by the MTDS-twin cleanup after the v2 sports
  enumerator stamped EXPECTED_PRE/POST_SEASON empty_confirmed over them — enumerator guard shipped + 21 atoms
  re-stamped captured via VM_NAME=osc-repair-20260713), a single-index scan found 189 FURTHER atoms
  (data_type, league_id, date) that carry BOTH a captured row and an empty_confirmed row in the CURRENT raw index,
  where the empty row wins recency-only reader dedup (UTL manifest_writer._read_index._merge_shard_frames has NO
  captured-outranks tie-break, unlike the consolidator since 2026-07-12). The rows coexist because their dedup keys
  differ (service_name / venue / instrument dims), so consolidator dedup can never collapse them; atom-grain consumers
  (data-status, coverage) see whichever wins their own collapse rule. Subclasses: (a) 143 PLAYER_STATS atoms —
  captured rows written 2026-05-06 by service_name=fill-missing-player-stats (row_count NaN) vs EXPECTED_NO_FIXTURE
  empty rows whose written_at was refreshed to 2026-07-13T16:24:30.871968 by the MTDS-cleanup first-attempt re-stamp
  shard; needs on-disk object probes before any flip. (b) 46 FIXTURES atoms — empty rows are DELIBERATE
  truthset-evidenced flips (reason 'flipped_residual_attempted_failed_20260629...__truthset_20260628_confirms_no_fixtures')
  contradicting captured rows (venue=API_FOOTBALL, row_count 1-11): a truthset-vs-capture contradiction to adjudicate,
  NOT a blind re-stamp. Blind-stamping either subclass could undo operator-evidenced decisions, hence parked here.
  Atom lists: regenerate with the single-index scan in this doc (or from the 2026-07-13 session CSVs). Also carries
  the two hardening follow-ups: reader-side captured-outranks tie-break in _merge_shard_frames, and redeploying the
  expected-universe-v2-sports Cloud Run image so the shipped enumerator oscillation guard takes effect at 01:30Z.
  ADJUDICATED 2026-07-14 (scope grew to 244 atoms): 243 restamped captured via shard recency-repair-20260713,
  verify green twice, zero captured-key losses; ALL 100 FIXTURES cells were truthset gaps (see body). REMAINING:
  the INFRA image redeploy + the P3 fleet sweep + 2 residual atoms (parked blank-data_type row; new TEAMS/TFF
  nightly-image masking).
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer]
tags: [manifest, honest-coverage, oscillation, dedup, sports]
related:
  - plans/active/issues/manifest_consolidator_prune_race_overlapping_executions_2026_07_13.md
  - /codex/02-data/availability-manifest-and-data-status.md
created: 2026-07-13
author: unknown
parent_epic: sports_master
priority: P1
source: oscillation investigation 2026-07-13 (operator task "lets fix it")
assigned_vm: planning
resolved_by: ""
locked_by:
context_scope:
  [
    /plans/archive/issues/manifest_consolidator_prune_race_overlapping_executions_2026_07_13.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    instruments-service/scripts/enumerate_expected_universe.py,
    instruments-service/instruments_service/engine/orchestrator/sports_reference_core.py,
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Sports index — 189 recency-masked captured atoms (2026-07-13 oscillation residue)

## Context (fixed part, same day)

- Root cause of the oscillation class: `instruments-service/scripts/enumerate_expected_universe.py`
  `_enumerate_v2_sports` emitted `empty_confirmed` (per-day source-rule gate `is_expected_for_source` →
  `EXPECTED_PRE_SEASON`/`EXPECTED_POST_SEASON`, lifecycle rows, `EXPECTED_NO_PROVIDER_COVERAGE`, matchday
  `EXPECTED_NO_FIXTURE`) WITHOUT consulting capture evidence. Fixed by the `enumerate_v2` oscillation guard
  (`captured_set` — a seeder never emits `empty_confirmed` over a captured atom) + unit tests.
- The 21 fully-erased atoms (captured row deleted by `dedup_mtds_instruments_surface_duplicate_rows_2026_07_13.py`
  because the only same-identity twin was the enumerator's dishonest empty seed) were content-verified on disk and
  re-stamped captured via per-VM shard `VM_NAME=osc-repair-20260713`
  (`scripts/osc_repair_captured_over_empty_2026_07_13.py`).

## Open work

- [x] [DATA] P1. Subclass (a) — 143 PLAYER_STATS atoms: probe on-disk objects (UAC `candidate_parquet_paths`,
      PLAYER_STATS layout) for each (league, date); where an object with >=1 row exists, re-stamp captured at the
      canonical league-grain identity (same shard mechanism as osc-repair); where absent, DELETE-or-retype the stale
      `fill-missing-player-stats` captured row instead (it is the dishonest side then). Never blind-flip. — ✅
      2026-07-14 instruments-service@853cef81 (`scripts/recency_masked_adjudication_2026_07_13.py`): all 143 probed
      objects exist + parse with >=1 row → verdict `restamp-captured`, re-stamped at the masking empty row's identity
      via per-VM shard `VM_NAME=recency-repair-20260713`; the absent-object branch never fired (0 missing), so the
      delete-or-retype contingency stated above was never exercised. `--verify` green twice (02:41Z + 02:52Z
      2026-07-14, >=2 consolidator cycles): 243/243 read captured; captured-key diff vs pre-apply snapshot
      `availability_index.20260714-023838.recency_masked_adjudication_pre_apply.parquet` = 0 lost keys.
- [x] [DATA] P1. Subclass (b) — 46 FIXTURES atoms: adjudicate truthset-flip vs captured row (row_count 1-11,
      venue=API_FOOTBALL). The 2026-06-28 truthset says no fixtures; the captured parquet says rows exist. Decide per
      atom by content (open the parquet; a header-only/placeholder parquet → keep the flip; real fixture rows → truthset
      was incomplete for that league-day → re-stamp captured + note truthset gap). Operator-evidenced flips must not be
      silently undone. — ✅ 2026-07-14 instruments-service@853cef81: scope grew to **100 FIXTURES atoms** (46 original
      truthset-flips + 54 new post-doc maskings; operator ruled same evidence rules). Per-cell parquet inspection found
      genuine fixture rows dated to the exact league/day in **ALL 100 cells** → `restamp-truthset-gap`; zero flips
      upheld, zero ambiguous. See § "Truthset gap (PROMINENT)" below.
- [x] [CODE] P2. Reader-side hardening: mirror the consolidator's 2026-07-12 captured-outranks-recency tie-break in
      `unified_trading_library/unified_trading_library/manifest_writer/_read_index.py::_merge_shard_frames` (and any
      atom-grain collapse consumers) so a later bare `empty_confirmed` can never mask a captured row at read time. — ✅
      2026-07-14 unified-trading-library@17ee38de: leading captured-rank sort key mirroring the consolidator's
      `CASE WHEN capture_status = 'captured' THEN 1 ELSE 0 END DESC` (manifest_consolidator.py:1884); recency unchanged
      among equal-rank rows; degrades to pure recency on legacy frames without `capture_status`; +5 unit tests in
      `tests/unit/test_manifest_writer_per_vm.py`.
- [x] [INFRA] P1. ~~Redeploy the `expected-universe-v2-sports` Cloud Run job image with the shipped enumerator guard~~ —
      **SUPERSEDED 2026-07-23** by the "ROOT CAUSE CORRECTED" section below (the actual masking writer is a different
      job, `uts-prod-instruments-service-sports-fixtures`, not this one) and **RESOLVED 2026-07-24** by the downgrade
      todo's verification (see below): no redeploy action taken or needed on this job.
- [x] ✅ [DATA] P3. Sweep other asset groups for the same seeder-over-captured pattern (the enumerate_v2 guard is active
      for every asset_group now via main(); verify the nightly jobs' images pick it up fleet-wide). —
      instruments-service@2b165597 (already shipped; sweep-only verification, no code change needed).

## Adjudication outcome (2026-07-14, `scripts/recency_masked_adjudication_2026_07_13.py` @ instruments-service@853cef81)

- Live re-scan flagged **244** atoms (189 from this doc + 54 new post-doc FIXTURES maskings + 1 blank-data_type oddity).
  Verdicts: **143 PLAYER_STATS `restamp-captured`** + **100 FIXTURES `restamp-truthset-gap`** + **1
  `report-only-non-empty-winner`** (blank-data_type row: a BITGET-FUTURES/UNDERSTAT `attempted_failed` winner sitting in
  the SPORTS index dated 2026-06-26 — operator ruled OUT of scope, parked here; it is a cross-surface row-identity
  oddity, not a recency-masking).
- **243 re-stamps applied** via per-VM shard `_index/per_vm/recency-repair-20260713.parquet` (explicit `.write()`,
  cron-absorbed + pruned within one `*/1` cycle; consolidation never manually triggered). `--verify` green twice
  (02:41Z, 02:52Z): 243/243 atoms read captured in the canonical index; captured-key diff vs the pre-apply snapshot
  shows **0 lost / 0 gained captured keys** (see next bullet); snapshots retained under `_index/snapshots/`.
- **Finding — unattributed earlier apply at 2026-07-13T23:48–23:49Z**: the pre-apply snapshot already carried captured
  rows at the exact winner identities (service_name=instruments-service, venue="", source=api_football) for these atoms,
  stamped 23:48–23:49Z by an unidentified session (its shard was already absorbed + pruned by 02:33Z, no log found). The
  02:38Z apply was therefore an idempotent re-write over the same identities (hence the 0-gained key diff) and upgraded
  row_count evidence (the 23:49Z rows carried e.g. row_count=1.0 where the backing object holds 36/67 rows). End-state
  content is verified correct either way. If a second slot ran the same repair, dedup the dispatch.
- **Caveat**: FIXTURES/TFF_FIRST_LEAGUE/2018-03-08 resolves via the league-less day-level object
  `sports_reference/by_date/day=2018-03-08/.../entity=fixtures/fixtures.parquet` (67 rows, all leagues); league
  attribution was verified by content (`af_league_id=204` = TFF First League per UAC `league_data_other.py`, exactly 1
  fixture row that day) but the stamped manifest row_count reflects the 67-row object, not the 1 league row.

## Truthset gap (PROMINENT)

**All 100 adjudicated FIXTURES cells contradicted the 2026-06-28 truthset**: every flipped league-day's on-disk parquet
contains genuine fixture rows dated to that exact league/day (row*count 1–11). Zero flips were upheld. The
`truthset_20260628_confirms_no_fixtures` evidence class was systematically WRONG for these cells — the 06-28
truthset-flip class needs an **evidence-freshness lens** (a truthset snapshot must not outrank a newer/parseable on-disk
capture without content inspection) before any future flip campaign reuses it. Anyone re-running
`flipped_residual_attempted_failed*_\_*truthset*_`style campaigns must content-probe captures first (this
script's`--adjudicate` phase is the template).

## Regeneration recipe (single index read, no corpus walk)

Group the raw index by `(data_type, league_id, date)`; keep groups containing BOTH `captured` and `empty_confirmed`
rows; within each, sort by `(attempted_at, written_at)` and flag groups whose last row is not `captured`. 2026-07-13
measurement: 33,172 contested atoms total; 32,982 resolve captured on recency; 189 resolve empty_confirmed; 1 resolves
attempted_failed. Post-adjudication residual (2026-07-14 02:57Z): **2 masked atoms** — the parked blank-data_type row +
the new TEAMS/TFF_FIRST_LEAGUE/2026-07-13 nightly-image masking (see the INFRA todo).

## RE-TRIAGE (2026-07-23)

**Verdict: STILL OPEN, ACCURATE — confirmed actively ongoing, not just theoretically unfixed.** Re-ran this doc's own
"Regeneration recipe" against a fresh live read of the same index
(`gs://instruments-store-sports-prd-.../_index/availability_index.parquet`, 5,523,146 rows today) via
`unified_trading_library.get_storage_client()`/`resolve_bucket_name()`.

- **61 contested `(data_type, league_id, date)` atoms found** (both a `captured` and an
  `empty_confirmed`/`attempted_failed` row present); **56 resolve to a non-`captured` winner on recency** — up from the
  "2 masked atoms" residual recorded at the end of the 2026-07-14 adjudication.
- These are NOT a residue of the original 2026-07-13 oscillation — the winning (masking) rows' `written_at` timestamps
  span **2026-06-27 through 2026-07-23T04:06:54Z, i.e. as recent as ~4.7h before this check**, with fresh instances on
  nearly every day in between (07-16, 07-18, 07-19, 07-20, 07-21, 07-22, 07-23), mostly `FIXTURES`/`FIXTURE_STATS`
  `empty_confirmed` rows written by `service_name=instruments-service`, plus a handful of `trades` `attempted_failed`/
  `empty_confirmed` rows from `market-tick-data-service`. Example: `FIXTURES/BRASILEIRAO/2026-07-22` was masked by an
  `empty_confirmed` row written **2026-07-23T04:06:54Z** — today.
- This directly confirms the still-open `[ ] [INFRA] P1` todo above ("Redeploy the `expected-universe-v2-sports` Cloud
  Run image") is genuinely still needed — the guard fix itself (`instruments-service@ba306543`) IS present on the
  current `live-defi-rollout` HEAD (`git merge-base --is-ancestor ba306543 HEAD` → true), but masking is continuing in
  production regardless, meaning either the deployed job image predates the fix, the fix doesn't cover every emission
  path (e.g. the ordinary `FIXTURES` per-matchday gate vs. the season-boundary gates the guard specifically targeted),
  or a second emitter exists. Not root-caused further in this pass (out of scope for a re-triage) — flagging as
  confirmation, not a new separate finding, since the doc's own open INFRA todo already names this exact remediation.
- The `[x]` adjudication todos (a)/(b)/(c) (243-atom historical re-stamp, reader-side tie-break) hold: none of the 56
  currently-masked atoms overlap the previously-adjudicated PLAYER_STATS/FIXTURES sets by date — this is fresh churn
  from the still-unguarded live pipeline, not a regression of the 2026-07-14 fix. Status left `open`.

## ROOT CAUSE CORRECTED (2026-07-23, second pass) — the "redeploy image" todo targets the WRONG job

Before acting on the `[ ] [INFRA] P1` "redeploy `expected-universe-v2-sports`" todo, traced the ACTUAL writer of the
04:06:54Z masking row (`FIXTURES/BRASILEIRAO/2026-07-22`) via Cloud Run execution history rather than assuming. It does
not match `expected-universe-v2-sports` (which ran once today at 01:30:06Z–01:30:58Z, hours before the masking write) or
`is-daily-enum-sports` (13:30Z daily, last ran 07-22). The actual match:
**`uts-prod-instruments-service- sports-fixtures`**, with 4 parallel executions starting 04:25:55–57Z and one completing
04:26:53Z — squarely inside the masking window. Confirmed via `gcloud run jobs describe`: this job runs the GENERIC
instruments-service CLI
(`--operation=instruments --mode=batch --asset-group=SPORTS --sports-provider=API_FOOTBALL --run-tag=t1-recon`) — **a
completely different code path from `enumerate_expected_universe.py`**, where the `ba306543` oscillation guard lives.
This job's own `EXPECTED_NO_FIXTURE`/`EXPECTED_PAUSED_LEAGUE` empty-row emission (inside the regular sports
fixtures/reference batch-capture orchestrator, e.g. `sports_fixtures.py`/`sports_reference_core.py`) was **never covered
by that guard at all** — redeploying `expected-universe-v2-sports` (even with a fully fixed image, which the current
`:latest` tag as of 2026-07-23T08:07:36Z does contain) would change NOTHING, because it is not the job producing the
masking.

**Also checked whether the shipped reader-side fix (`unified-trading-library@17ee38de`, `_merge_shard_frames`'s
captured-outranks tie-break) neutralizes this in practice**: it does not, for this specific population — the tie-break
only applies WITHIN one dedup-key group, and this doc's own original framing is explicit that these atoms mask
CROSS-identity (differing `service_name`/`venue`/instrument dims), so the reader never even groups the captured and
masking rows together to apply the tie-break. This is a genuinely live, unmitigated gap.

**Corrected action item — replaces the INFRA redeploy todo above (not done, superseded by this)**:

- [x] [CODE] P1. **Extend the "never emit empty_confirmed over a captured atom" guard to the regular sports instruments
      batch-capture emission path** (`sports_fixtures.py`/`sports_reference_core.py` or wherever
      `uts-prod-instruments-service-sports-fixtures`'s `--operation=instruments --mode=batch --asset-group=SPORTS` run
      emits `EXPECTED_NO_FIXTURE`/`EXPECTED_PAUSED_LEAGUE`/etc.) — same guard shape as `ba306543`
      (`enumerate_expected_universe.py`'s `captured_set` check), applied to this SEPARATE code path. This is real code
      investigation + a fix + tests, not a redeploy — appropriately scoped as its own session's work, not rushed here.
      Repo: `instruments-service`. — ✅ 2026-07-30 instruments-service@4275b2d8: generalized the existing
      FIXTURES_SCHEDULE-only manifest-captured-set guard (`_manifest_captured_fixture_leagues`, used by
      `process_write._write_sports_fixture_venue`) into a data_type-parameterized
      `_manifest_captured_leagues_for_data_type`, and wired a new
      `_AfManifestHooks._manifest_index_guarded_captured_leagues` hook into `emit_empty_gaps_for_entity`
      (TEAMS/STANDINGS/INJURIES path in `sports_reference_core.py`) — same fail-safe (`None` on manifest-read failure →
      skip emission entirely) and `bucket=""`-disable contract as the existing GCS-presence guard. +9 unit tests
      (generalization proof, guard-unit coverage, and an end-to-end `emit_empty_gaps_for_entity`
      guard/fail-safe/regression suite in `tests/unit/test_sports_reference_core_manifest_index_guard.py`); full
      `quality-gates.sh` green (5051 passed) at instruments-service@4275b2d8.
- [x] [INFRA] P3. **Downgrade, don't drop, the original "redeploy `expected-universe-v2-sports`" todo** — that image IS
      now current (confirmed `:latest` contains `ba306543` as of 2026-07-23T08:07:36Z) and Cloud Run Jobs generally
      re-pull a mutable tag per execution, so no action is likely needed there specifically; keep as a low-priority
      verification only, not the primary fix. — ✅ 2026-07-24 VERIFIED via
      `gcloud run jobs describe expected-universe-v2-sports --project=central-element-323112 --region=asia-northeast1`:
      the job's container image is literally
      `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/instruments-service:latest` — a
      mutable `:latest` tag, not pinned to a digest or fixed version. Confirms Cloud Run Jobs re-pull the tag per
      execution as expected; no redeploy is needed to pick up future image updates. Recent executions
      (`expected-universe-v2-sports-pb5vj` 2026-07-24T01:30:06Z, `-n6gbs` 2026-07-23T01:30:06Z, `-fvrgf`
      2026-07-22T01:30:05Z) all completed successfully on the standard 01:30Z nightly cadence. **Resolved, no further
      action** — this todo and the superseded original redeploy todo above are both closed. The remaining live gap
      (masking writer is `uts-prod-instruments-service-sports-fixtures`, a different job) is tracked separately as the
      `[CODE] P1` "extend the guard" todo above, dispatched via
      `plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md`.

## Progress Log

- **context-scout 2026-08-03**: re-read in full; existing context_scope (6 entries) still accurate — no new source
  target or SSOT surfaced beyond what's already listed. Refreshed marker only.
- **P3 fleet-wide sweep 2026-08-05** (slot 2, data_engineering): code audit confirms the oscillation guard is active for
  ALL 5 asset groups. `enumerate_expected_universe.py::main()` (line 4568) passes `captured_set` unconditionally; the
  single choke point at lines 3337-3357 drops any `empty_confirmed` row whose atom already has a captured manifest row —
  this guard applies to cefi, defi, tradfi, sports, and prediction identically. Non-sports AGs have NO separate
  batch-capture `empty_confirmed` emission paths outside `enumerate_expected_universe.py` (unlike sports, whose
  `sports_reference_core.py`/`process_zero_records.py`/`weather.py` paths were the original masking writers — all now
  guarded: `_AfManifestHooks._manifest_index_guarded_captured_leagues` at instruments-service@4275b2d8, presence guards
  in `process_zero_records.py`). Cloud Run job registry confirms `expected-universe-v2-{ag}` and `is-daily-enum-{ag}`
  per-AG jobs exist for all 5 AGs using `instruments-service:latest` mutable tag; no non-sports equivalent of
  `uts-prod-instruments-service-sports-fixtures` exists. **Verdict: guard coverage is complete fleet-wide — all AGs are
  protected.** No code changes required; this closes the last open todo.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged. Note (out of scope to
  fix): the 2026-08-05 progress-log entry states this closes the last open todo, but `status:` frontmatter still reads
  `open`.
- **plan_reconciler 2026-08-09** (sports tranche, `agt-8da8df`): re-normalizing `locked_by: ""` (false-trips
  `check-locked-plan-deletion.sh`'s naive parser) to truly-blank `locked_by:` as a standalone commit, ahead of the
  status-flip + archive in the next commit — see that commit for the full resolution + a resurrection-after-first-
  archive finding.
