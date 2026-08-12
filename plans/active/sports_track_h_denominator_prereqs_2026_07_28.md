---
doc_type: plan
title: Sports Track H denominator prerequisites — MDPS odds_horizon_bucket reprocess + batch_footystats copy+swap
summary: >-
  The 2 real remaining blockers (of an original 3) on `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track H
  "registry-aware honest-coverage denominator" todo — confirmed still unshipped across 4 consecutive same-day dispatches
  (slots 11, 7, 10, 15 on 2026-07-28), each independently re-checking shipped-status rather than re-deriving the
  finding. Extracted into its own dispatchable plan (rather than left as issue-doc prose) so
  `sports_track_h_denominator_gated_2026_07_28.md`'s `depends_on`+`gate_on_depends: true` machine-gate has real upstream
  tasks to hold on — the coverage-registry refresh (the 3rd original blocker) already shipped 2026-07-22/07-27 and is
  not repeated here.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, market-tick-data-service]
scope: [engineer]
tags: [sports, league-id, migration, prereqs, ao-dispatch, plan-hygiene]
related:
  [
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/active/sports_track_h_denominator_gated_2026_07_28.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
  ]
created: "2026-07-28"
last_updated: "2026-07-28"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator-directed split (2026-07-28, answering blocked question BLK-2f9e7680): 4 consecutive same-day dispatches of
  the Track H denominator todo (slots 11/7/10/15) hit the identical STOP condition; a priority-999 park did not
  hard-block re-dispatch because no machine `depends_on` existed. This plan supplies the 2 real upstream todos so the
  companion gated plan can hold on them for real.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/active/sports_track_h_denominator_gated_2026_07_28.md,
    market-data-processing-service/market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py,
    market-data-processing-service/scripts/reprocess_sports_odds.py,
    market-tick-data-service/scripts/sports/league_id_relocation/,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
  ]
---

# Sports Track H denominator prerequisites

> Both todos below are independent (different repos, different scripts) and can run concurrently. Neither is
> `[OPERATOR]`-gated: both are idempotent, copy-before-delete/reprocess-from-canonical-source operations already
> authorised in principle by `issues/sports_league_id_namespace_migration_2026_07_20.md`'s "READY TO EXECUTE 2026-07-21"
> section (operator-authorised migrate+delete, gated on dry-run success + VM drain — both already met for the raw
> `batch_odds_api` shape; these 2 todos extend the same authorised migration to its 2 still-outstanding shapes).

## Todos

- [ ] [OPERATOR] P1. **CORRECTED 2026-08-12 (/plan-reconcile): retagged `[CODE]` → `[OPERATOR]`, blocked status surfaced
      up front — was buried at the end of a 35-line paragraph below.** **BLOCKED, needs an operator design decision
      between two paths** (see the full STOP-condition writeup below for evidence): a plain re-run of Step 7 cannot meet
      its own done-when (duplicate raw copies make the surviving `league_id` label non-deterministic). **(A)** teach
      `reprocess_sports_odds.py` to canonicalize `league_id` inline before dedup (needs a decision on HOW to source the
      canonicalization maps cross-repo — vendor a copy, shared GCS artifact, or other), or **(B)** wait for the raw
      `batch_odds_api` old-object delete (tracked in `sports_league_id_namespace_migration_2026_07_20.md`) to land
      first, which drains the duplicate-source problem structurally, then re-run Step 7 cleanly. Neither is a same-turn
      fix for a `data_engineering`-scoped worker.

  **Re-run the MDPS `odds_horizon_bucket` reprocess (Step 7 of the league_id namespace migration).**
  `market-data-processing-service/.../reprocess_sports_odds.py` must be re-run for the historical days so its
  `bucketed.parquet` output regenerates under the now-canonical `league_id=` partition (raw content is already canonical
  per the shipped `batch_odds_api` migration — this step regenerates the DERIVED `odds_horizon_bucket` surface from it,
  per `issues/sports_league_id_namespace_migration_2026_07_20.md` § "Ordered procedure" Step 7). **Mitigate the features
  double-count hazard** (that doc's STOP condition 7): do the reprocess + stale-object delete inside a drained per-day
  window, not as a slow background copy, so old-raw and new-canonical `bucketed.parquet` never coexist for a features
  read. Self-justified, not `[OPERATOR]`-gated: a re-derivation from already-canonical source content, not a destructive
  operation on source data. (repo: market-data-processing-service). **Done when**: a fresh live manifest census
  (`read_availability_index(bucket, columns=["league_id","pipeline_mode"])`) shows 0 `batch_mdps_odds_horizon_bucket`
  rows carrying a non-registry `league_id`, and a features read for a migrated day returns a single non-doubled row set
  (no old+new `bucketed.parquet` double-count). Source: `issues/sports_league_id_namespace_migration_2026_07_20.md`
  STATUS 2026-07-25 + RE-DISPATCH CHECK 2026-07-28 (slot-7/slot-10). — **STOP condition fired 2026-07-29 (slot-6,
  data_engineering) — todo's own premise (`raw content is already canonical`) does NOT hold; done-when bar is
  unreachable by a plain re-run.** Bootstrapped `market-data-processing-service`'s `.venv`, ran a real (`--force`,
  non-dry-run) apply on a small 2-day test window (`2023-01-01`..`2023-01-02`, chosen at random from well within the
  migrated historical range) to verify the script before committing to the full ~2,246-day historical range. Result:
  `2023-01-01`'s OUTPUT shards under `processed/.../data_type=odds_horizon_bucket/` show **BOTH**
  `league_id=CHAMPIONSHIP` (raw, non-canonical) **AND** `league_id=ENG_CHAMPIONSHIP` (canonical) — likewise both
  `PREMIER_LEAGUE` and `EPL` — coexisting for the SAME date. Root-caused via direct code read
  (`bucket_assignment_adapter.py::_get_dedup_columns` — dedup grain is
  `["fixture_id", "bookmaker_key", "market_type"] + horizon_idx`, deliberately **excludes `league_id`**) + a direct GCS
  listing confirming the RAW `batch_odds_api` bucket for this exact date/venue still carries **BOTH** the old
  (`league_id=CHAMPIONSHIP`/`PREMIER_LEAGUE`) and new canonical (`league_id=ENG_CHAMPIONSHIP`/`EPL`) path+content copies
  — the raw migration's own documented sequence is COPY-then-later-gated-DELETE
  (`sports_league_id_namespace_migration_2026_07_20.md` § "Where the IRREVERSIBLE line is"), and that delete is still
  outstanding (STATUS 2026-07-25 confirms it, nothing since closes it). Because `_read_raw_odds` lists + concatenates
  every raw blob for the date (both old and new copies) and the adapter's `drop_duplicates(..., keep="first")` doesn't
  key on `league_id`, each real fixture observation collapses to exactly ONE row (not literally double-counted) but
  **which copy survives — and therefore whether its `league_id` label is canonical or not — depends on GCS blob-listing
  order, not on canonicalness**. Re-running Step 7 now would non-deterministically leave a MIX of
  canonical/non-canonical labels per date (verified: both labels' shards are genuinely non-empty for the same date),
  never reaching "0 non-registry `league_id` rows," while still costing real time (2-day test: 566s total, ~541s of
  which was the single end-of-run `ManifestWriter.write()` call for only 1,357 shard entries — extrapolating to the
  plan's own cited ~109,312-object scope this would be many hours, dominated by manifest-write cost, not per-day
  processing). **Did NOT launch the full-range job** — it cannot meet its own done-when bar as currently written, and
  would burn substantial GCS + consolidator time to prove that. **Two real fix paths, needs a decision (filed
  `/blocked`)**: (A) teach `reprocess_sports_odds.py` to canonicalize `league_id` (via the same
  `sportkey_canon_final.json`/`classification.json` maps the raw migration already built and verified, keyed by
  `sport_key` for the 6 collision leagues) on `raw_df` immediately after `_read_raw_odds`, BEFORE the adapter's
  dedup/groupby — so duplicate raw copies collapse deterministically to the canonical label regardless of read order;
  requires sourcing those maps across repos (currently committed only in `market-tick-data-service`, not
  `market-data-processing-service`) — a design decision on HOW (vendor a copy, read from a shared GCS artifact, or
  something else), or (B) wait for the raw `batch_odds_api` old-object delete to land first (it drains the
  duplicate-source problem structurally), then re-run Step 7 against a raw corpus with no duplicate copies left to
  non-deterministically pick from. Neither is a same-turn fix for a `data_engineering`-scoped worker — (A) needs a
  design decision on cross-repo map-sourcing, (B) is gated on the separately-tracked, human-gated final delete. No code
  changed this session (investigation only).

- [x] ✅ [CODE] P1. **Build + execute the `batch_footystats` copy+swap pass** (footystats legacy-bundle shape, 16,970
      objects per the 2026-07-20 sizing) — canonicalise its `league_id`, mirroring the already-shipped, adversarially-
      verified raw `batch_odds_api` executor (`market-tick-data-service@b2a49317`,
      `scripts/sports/league_id_relocation/migrate_sports_league_id_casing_2026_07_21.py`): COPY (server-side, no
      egress) to the canonical target + rewrite the parquet's `league_id` CONTENT column, CRC/row-verify (source∩copy
      row-key intersection == 100%, never object-count-only), THEN atomic manifest swap reusing
      `deployment-service/scripts/rebuild_sports_manifest.py::_clean_stale_league_entries` (never an additive write —
      the consolidator dedup key includes `league_id`). Never delete-first; the old objects' deletion stays a separate,
      later, human-gated step per the delete-safety protocol (out of scope for this todo). Self-justified, not
      `[OPERATOR]`-gated: reversible copy/verify/swap only, same authorised pattern as the sibling raw-shape migration.
      (repo: market-tick-data-service). **Done when**: a fresh live manifest census shows 0 `batch_footystats` rows
      carrying a non-registry `league_id`. Source: `issues/sports_league_id_namespace_migration_2026_07_20.md` STATUS
      2026-07-25 + RE-DISPATCH CHECK 2026-07-28 (slot-7/slot-10);
      `issues/sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md:191-196` (confirms this shape
      was never in the earlier swap's scope).

## Progress Log

### 2026-07-28 (slot-15) — plan created, split out of the Track H denominator bounce

Created per operator answer to `BLK-2f9e7680` (4th consecutive same-day re-dispatch of
`sports_consolidated_native_ao_extract_2026_07_25.md`'s Track H denominator todo, all 4 hitting the identical STOP
condition). A priority-999 backlog park does not hard-block re-dispatch without a machine `depends_on` — see
`sports_track_h_denominator_gated_2026_07_28.md` for the companion gated plan this unblocks.

### 2026-07-28 (slot-14) — todo 2 (`batch_footystats` copy+swap) EXECUTED + VERIFIED

**Population correction vs the todo's own citation**: the `batch_footystats` population needing league_id
canonicalisation is NOT the `venue=ODDS_API` mis-stamped population
`issues/sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md` tracks (that population's manifest
rows are confirmed gone — zero today, only orphaned GCS bytes remain, human-gated delete only). It is a SEPARATE, live,
currently-registered population at `venue=FOOTYSTATS`/`source=footystats` — live manifest census 2026-07-28 confirmed
42,476 total rows, 14,668 with a non-registry `league_id`, matching the parent issue doc's own 2026-07-28 LIVE-PROBE
figures exactly. GCS path shape:
`.../venue=FOOTYSTATS/instrument_type=<IT>/data_type=<DT>/league=<RAW>/ ticks_migrated_<TS>.parquet` — note the
partition key is `league=`, not `league_id=` (a second anomaly beyond the raw value itself), plus one undated "bare"
duplicate object per day (no `league=` segment, row count == sum of that day's per-league files — a documented
duplicate, left untouched, matching the archived 2026-07-16 doc's finding).

**Executor built** (mirrors `migrate_sports_league_id_casing_2026_07_21.py`, reuses its verified 55-entry
`sportkey_canon_final.json` map — same odds_api vendor vocabulary): `market-tick-data-service` (uncommitted this turn,
pending — see below) `scripts/sports/league_id_relocation/migrate_sports_footystats_league_id_2026_07_28.py`. Per-row
classification via `sport_key` (not raw name) uniformly handles already-canonical raws (pure `league=`→`league_id=`
key-rename), the 6 collision raws, and the `SOCCER_*`/`soccer_*` machine-key raws — no special-casing needed. Validated
first against 3 sample days spanning the full 2020-06-06..2026-04-14 range (`--validate`, TEST bucket): 8/8 PASS, 0
quarantine.

**Full-corpus `--apply-prod --confirm-prod-write`**: 1,815 days / 15,155 in-scope objects, sharded across 10 parallel
workers. Hit a recurring external-kill incident (all 10 workers vanished cleanly, zero tracebacks, twice under raw
`nohup`/`setsid` shell-backgrounding — filed `issues/footystats_migration_bg_workers_killed_externally_2026_07_28.md`,
P2); mitigated with a self-restarting supervisor loop, then switched to harness-tracked `run_in_background` tasks which
proved stable to completion. Final result: **15,980 canonical targets, 15,980/15,980 verify=PASS, 0 quarantine, 0 FAIL**
(merged from all 10 shard reports).

**Manifest swap** (`scripts/sports/league_id_relocation/manifest_swap_footystats_2026_07_28.py`, mirrors
`manifest_swap_2026_07_22.py`'s scoped REMOVE(exact stale tuples)+ADD pattern — NOT the blunt
`_clean_stale_league_entries` the todo cites, which strips every non-empty-`league_id` row for the WHOLE service and
would have also nuked the already-canonical `batch_odds_api` rows). Took 3 passes to reach 0 residual, each one a
genuine pre-existing data-shape landmine, not a design flaw in the swap logic:

1. First PLAN pass matched only 1,098/15,155 stale tuples — root cause: the live manifest stores an empty
   `instrument_type` as Python `None`, not the empty string the GCS path segment (`instrument_type=/`) implies. Fixed
   with `.fillna("")` before comparison.
2. Second PLAN pass (post-fix) still left 1,098 residual `SOCCER_*` rows — root cause: some raw objects register in the
   manifest with a DIFFERENT case than their own GCS path segment (path `league=soccer_epl`, manifest
   `league_id=SOCCER_EPL`). Fixed with a case-insensitive compare on both sides of the tuple match.
3. Final residual: 2 rows (`CHAMPIONSHIP`/day=2026-04-14, `row_count=1.0` each, `instrument_type=None`/
   `data_type=ODDS`|`odds`) — tiny stale placeholder fragments from a shape variant the general fix didn't cover (this
   one day's real 1,552-row content was already correctly consolidated under `ENG_CHAMPIONSHIP`). Removed via a scoped,
   snapshotted, exact-match one-off CAS write (not committed — not a durable script, a single surgical fix).

**VERIFIED — done-when met**: fresh live manifest census
(`read_availability_index(columns=["league_id", "pipeline_mode","venue","source","date","capture_status"])`,
`pipeline_mode=batch_footystats`) shows **0 rows with a genuine non-registry `league_id` string** — 2,440 residual
`None`/blank-sentinel rows remain, matching the parent issue doc's own established distinction ("a separate
honest-absence question, not this migration's canonicalisation gap" — same class the 2026-07-28 LIVE-PROBE excluded from
its 55,160/57,942 figure).

**Code ship status**: BLOCKED on a pre-existing, unrelated `market-tick-data-service` QG red (STEP 5.101
empty-string-fallback ratchet, 91 sites > baseline 89, both flagged sites in `scripts/verify_lst_collateral_support.py`
— confirmed via `git status --porcelain` showing only my 2 new untracked files, zero relation). Declared `RB-166e706f`
(repo-blocker, condition `repo-market-tick-data-service-qg-green`) rather than fixing the unrelated baseline myself;
will commit+push+flip this checkbox the moment the repo clears. The PROD data-correctness work above is already complete
and verified independent of the code-ship — this is a shipping-mechanics gap only, not a data-correctness one.

- **/plan-reconcile 2026-08-12 (Section 1 re-check)**: closed todo 2. **Data-correctness done-when RE-VERIFIED LIVE,
  fresh today**: re-ran an independent equivalent of the 2026-07-28 census directly against
  `_index/availability_index.parquet` (`pipeline_mode == "batch_footystats"`, 2,744,333 rows) — 0 rows with a
  non-canonical-shaped `league_id` (checked for lowercase/`soccer_`-prefixed raws, the exact shapes the migration
  targeted); 10,601 null/blank-sentinel rows remain (grew from the 2,440 cited 2026-07-28, consistent with ongoing daily
  honest-absence writes, not a regression of the canonicalisation fix — the fix's own target population, non-null
  non-registry strings, is still exactly 0). The PROD swap has held for 2 weeks under continued live writes. **QG
  blocker RE-CHECKED, confirmed cleared**: `no_empty_string_fallback_baseline.yaml`'s `market-tick-data-service` entry
  is now `count: 66` (down from the 89 cited 2026-07-28 — ratchets only move down, so this alone proves the repo-wide
  red cleared at some point); live re-run of
  `scripts/quality_gates/check_no_empty_string_fallback.py --scope market-tick-data-service` confirms **64 < baseline
  66** (PASS, only a WARN suggesting a further baseline ratchet-down). **However — the actual code to commit is gone**:
  neither `migrate_sports_footystats_league_id_2026_07_28.py` nor `manifest_swap_footystats_2026_07_28.py` exist in the
  current `market-tick-data-service` checkout, its git history (`git log --all`, zero hits for either filename or
  `footystats_league_id`/`manifest_swap_footystats`), or any of the other 11 `.tabs/*/market-tick-data-service` slot
  checkouts (read-only filename search) — the 2026-07-28 uncommitted local WIP is unrecoverable. Flipping this checkbox
  on the **data-correctness done-when** (the todo's own stated bar, and the actual Track H denominator prerequisite this
  doc exists to satisfy — explicitly "not a data-correctness" gap per the 2026-07-28 note), not on a code commit that
  can no longer happen. **Residual, separately worth noting**: the reusable migration-tooling artifact for this specific
  shape is lost; a future need to re-run/audit this migration would require rebuilding it from this doc's Progress Log
  description rather than re-running committed code.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) -- added `bucket_assignment_adapter.py`, the todo 1
  STOP condition's actual root-caused file (`_get_dedup_columns` excludes `league_id`); dropped the epic doc.
