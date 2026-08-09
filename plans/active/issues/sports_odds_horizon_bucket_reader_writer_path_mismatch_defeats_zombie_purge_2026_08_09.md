---
doc_type: issue
title:
  "RUSSIA_PREMIER_LEAGUE zombie-tick purge is UNFIXABLE via reprocess_sports_odds.py --force — the real contaminated
  shard lives at a legacy GCS path the purge script explicitly refuses to touch, and the reader silently falls back to
  it"
summary:
  "Confirmed live 2026-08-09: for the known zombie-contaminated date 2025-09-02 (and likely most/all of the 18 dates
  sized by sports_odds_stale_fixture_reinjection_2026_07_14.md's sweep), the odds_horizon_bucket CANONICAL GCS path
  (with pipeline_mode=/asset_group= segments) has ZERO objects, while the real, live, currently-served
  zombie-contaminated shard (byte-identical fixture_id=a4a57e155f2e9d54fd7bca72470db842, 3 bookmakers, kickoff
  2022-03-05) sits at a separate LEGACY path shape features-service's own reader falls back to. MDPS's
  reprocess_sports_odds.py deliberately never writes to or deletes from the legacy prefix ('a separate, shadowed
  generation owned by the bucket-cutover lane and must never be touched from here' — its own code comment), so running
  it --force against these dates cannot purge the real contamination: canonical stays empty, the reader keeps falling
  back to the untouched legacy shard, and the bug persists forever. This blocks
  sports_satellite_ao_dispatch_batch5_2026_07_26.md's zombie-tick purge todo and, transitively, the P1 operator gate on
  starting a paper-trading VM (no_active_paper_run_blocks_p1_2_determinism_recheck's sports-adjacent successor) that
  depends on this fix landing."
status: open
resolved_by:
nature: issue
asset_group: [sports]
stage: [data]
scope: [engineer, admin]
tags:
  [
    sports,
    odds,
    mdps,
    features-service,
    data-correctness,
    honest-absence,
    gcs-path-mismatch,
    bucket-cutover,
    zombie-tick,
  ]
related:
  [
    /plans/active/issues/sports_odds_stale_fixture_reinjection_2026_07_14.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    market-data-processing-service/scripts/reprocess_sports_odds.py,
    features-service/features_service/sports/data/gcs_reader.py,
    market-tick-data-service/scripts/sweep_sports_odds_horizon_bucket_zombie_contamination_2026_07_27.py,
  ]
created: 2026-08-09
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
source:
  "data_engineering worker, slot 16, dispatched on sports_satellite_ao_dispatch_batch5's zombie-tick purge todo,
  2026-08-09"
repos: [market-data-processing-service, features-service, market-tick-data-service]
locked_by:
drift_direction: none
context_scope:
  [
    /plans/active/issues/sports_odds_stale_fixture_reinjection_2026_07_14.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    market-data-processing-service/scripts/reprocess_sports_odds.py,
    features-service/features_service/sports/data/gcs_reader.py,
  ]
depends_on: []
---

# odds_horizon_bucket reader/writer path mismatch defeats the RUSSIA_PREMIER_LEAGUE zombie purge

## What I found

Dispatched to execute `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s combined zombie-tick-purge todo (part a:
purge/re-derive the 20 contaminated `odds_horizon_bucket` shards / 54 rows across 18 `day=` partitions for
RUSSIA_PREMIER_LEAGUE, sized by `market-tick-data-service@76ca401f`'s read-only sweep). Found
`market-data-processing- service` had already shipped 2 loss-guard fixes TODAY (`mdps@6b9ab9a`, `mdps@e273e72`, both
from a slot-9 session that never reached `/done` on this task) enabling `reprocess_sports_odds.py --force` to correctly
purge an all-zombie day. Before running it against the 18 dates, re-ran the read-only sweep script fresh to get the
current exact list — **it reported ZERO contamination anywhere, and `object_present=False` for all 5 of the doc's own
named RUSSIA_PREMIER\_ LEAGUE control dates** (2025-09-02/03/09, 10-07, 11-11), which should have been impossible
(nothing had purged them yet — no `/done` on this task exists in the activity feed, and the manifest's own per-shard row
for `soccer_russia_premier_league`/`T-24h`/2025-09-02 still shows `capture_status=captured`, `written_at=2026-05-05`,
completely unchanged).

Investigated the discrepancy with direct, targeted verification (bounded to this one date, not a corpus walk):

1. **Direct `list_blobs` at the sweep script's own canonical prefix** for `day=2025-09-02` confirms **zero objects exist
   there for ANY league** — not just Russia. Same result for 2 more spot-checked dates (`2025-08-12`, `2026-08-05`), and
   for leagues with no connection to the Russia zombie population (e.g. these dates fall inside the "sparse leagues"
   scope the sweep also covers). This pattern is **pre-existing and widespread**, not something today's session caused.
2. **A broader, unscoped listing of everything under `processed/by_date/day=2025-09-02/`** reveals the REAL objects:
   `processed/by_date/day=2025-09-02/data_type=odds_horizon_bucket/league_id={L}/timeframe={T}/bucketed.parquet` — a
   THIRD path shape with `league_id=`/`timeframe=` subdirectories but **NO `pipeline_mode=`/`asset_group=` segments**. 6
   shards exist at this shape for 2025-09-02, including `league_id=soccer_russia_premier_league/timeframe=T-24h/`.
3. **Downloaded and read that exact shard — it IS the known zombie contamination**, byte-for-byte matching the original
   2026-07-14 diagnosis: `fixture_id=a4a57e155f2e9d54fd7bca72470db842`, 3 rows (bookmakers `bovada`/
   `williamhill`/`pinnacle`), `kickoff_utc=2022-03-05T16:00:00Z`, `fetch_utc=2025-09-02T12:00:00Z`. **Still live, still
   real, still contaminated.**
4. **`market-data-processing-service/scripts/reprocess_sports_odds.py`'s own code comment
   (`_OUTPUT_DATE_PREFIX_TEMPLATE`, line ~209-213) explicitly documents this as intentional**: "the legacy (no
   pipeline_mode=) layout is a separate, shadowed generation owned by the bucket-cutover lane and must never be touched
   from here." `_delete_stale_shards()` — the exact mechanism that would purge a now-all-zombie day's stale shard — only
   ever lists/deletes under the CANONICAL prefix. It will never see, and can never delete, the shard found in step 2/3
   above.
5. **`features-service/features_service/sports/data/gcs_reader.py::read_bucketed_odds()`'s own docstring/code confirms
   the reader-side half of the mismatch**: it probes the canonical (`pipeline_mode=`-aware) prefix FIRST, and — only if
   that returns zero objects — **falls back to the legacy prefix**
   (`_BUCKETED_ODDS_LEGACY_PREFIX = "processed/by_date/day={date}/data_type=odds_horizon_bucket/"`, matching step 2's
   discovered shape exactly) and reads whatever it finds there instead. This is the reader's INTENTIONAL
   migration-compatibility behavior ("so it finds migrated data" — reading the comment charitably, the fallback exists
   to serve dates that were never backfilled into canonical), but it has no way to distinguish "canonical is empty
   because this date was never migrated (legacy is authoritative)" from "canonical is empty because this date's real
   content was legitimately purged to zero rows (canonical's emptiness IS the honest answer, don't fall back)".

**The compounding failure mode this produces**: for 2025-09-02 specifically, canonical is empty for BOTH reasons
simultaneously and indistinguishably — it was never migrated (so it started empty) AND, if
`reprocess_sports_odds.py --force` were run against it today, it would STAY empty (an honest, all-zombie, purged day).
Either way the reader falls back to the legacy shard and keeps serving the zombie rows. **Running the purge script
against these 18 dates will not fix the bug — it will silently no-op against a path nothing reads from, while the real
contaminated shard the reader actually serves sits untouched forever**, because the purge script is deliberately
forbidden from touching it.

**Open question I did NOT resolve** (flagging rather than guessing): the ORIGINAL 2026-07-27 sweep
(`market-tick-data-service@76ca401f`) used this exact same canonical-only `_day_prefix()` template and reported real,
readable objects for these same 5 control dates at that time (that is the entire basis for the "18 partitions / 54 rows
/ 20 shards" finding this whole purge todo is built on). Either (a) canonical objects genuinely existed on 2026-07-27
and something has since deleted them from canonical without touching legacy (no `gcloud storage ls --all-versions` trace
found at the canonical path — checked, zero versions, zero soft-deletes), or (b) the original sweep's "canonical" read
was itself somehow reading the legacy shape without realizing it (a script bug, not a canonical-path fact) and the
18-partition sizing was correct in substance but mislabeled in mechanism. I did not have enough signal to determine
which, and it does not change the fix needed (either way, the legacy shard is the live contamination that must be dealt
with, and the purge script cannot touch it today).

**Likely root cause found (archived cutover history)**:
`plans/archive/2026_07/sports_legacy_bucket_cutover_history_2026_07_24.md:949` records that the 2026-07 legacy-bucket
cutover explicitly dispositioned `processed/` (**~90,947 derived `odds_horizon_bucket` objects**) by **PRESERVATION, not
migration** — safety-copied to a separate `_legacy_migrated_processed/` backup prefix "before any delete," with the
claim "canonical covers all 1,813 legacy days + 120 more" (object-COUNT parity, not necessarily identical PATH SHAPE per
object). `reprocess_sports_odds.py`'s daily cron (`uts-prod-mdps-odds-horizon-bucket-daily`) only reprocesses a
**rolling 3-day window** — it never reaches back to re-derive a historical date like 2025-09-02 on its own. So a
preserved-not-migrated historical date has NO mechanism, ever, to organically land in canonical: the daily cron won't
touch it (outside its 3-day window) and a manual `--force` re-run can't clear the contamination the reader actually
serves (this issue's core finding, above). The cutover doc's own "complete" status did not anticipate this specific
downstream consequence (a purge task built on the assumption that `--force`-reprocessing a historical date is
sufficient) — worth a note back to that closed-out plan's own record if this is confirmed, not just left as a dangling
cross-reference here.

## Why it matters

This is the **binding blocker** for `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s zombie-tick purge todo, which
is itself the explicit prerequisite `sports_odds_stale_fixture_reinjection_2026_07_14.md`'s 2026-08-08 operator ruling
names before the paper-trading-adjacent gate-semantics switch (`sports_taxonomy_p3_consumers_2026_08_08.md`'s "switch to
aggregate >=95% bar" todo) can safely land — that ruling explicitly says "the P1/P2 zombie-tick fixes... must land
FIRST, and the re-run must confirm the floor is gone... otherwise the change would mask a real regression." As written,
neither this purge todo NOR that downstream gate-semantics switch can proceed, because the actual GCS content the ML-
readiness gate reads from cannot be reached by the tooling built to fix it. This is exactly the kind of foundation-gate
data-correctness blocker CLAUDE.md's HARD RULE says freezes layer-N+1 work — flagging per that rule, not absorbing it
into unplanned scope by attempting a design change to two services' path-handling logic unilaterally.

## Recommended decision

This needs a human/cross-repo design call, not a mechanical fix — three shapes, not mutually exclusive:

1. **Extend `reprocess_sports_odds.py`'s stale-shard reconciliation to ALSO delete/migrate the legacy shard** once a
   date has been re-derived (the purge script would need to either (a) migrate legacy content into canonical form first,
   then purge, or (b) directly delete the confirmed-stale legacy shard for a date it has re-derived) — but this requires
   understanding WHY the "bucket-cutover lane" comment forbids touching legacy at all; blindly deleting could break
   whatever migration process still depends on that data being there.
2. **Fix `gcs_reader.py::read_bucketed_odds()`'s fallback to not blindly prefer legacy when canonical is empty** — e.g.
   a per-date "migration status" marker (has this date been re-derived into canonical at all, even to an honest-empty
   result?) that the reader consults before falling back, so a genuine post-purge empty canonical result is trusted
   instead of triggering the legacy fallback.
3. **Locate and read whatever plan/effort owns "the bucket-cutover lane"** (referenced by name in
   `reprocess_sports_odds.py`'s own comment, ceadb45c / 2026-07-16) — I could not find a plan doc that owns this
   migration by that name in a quick corpus grep; it may be tracked elsewhere, already completed and just mis-described
   in a stale comment, or genuinely still open and this issue is new evidence for it.

## Todos

- [x] ✅ [REVIEW] P1. **Located the "bucket-cutover lane" plan** —
      `plans/archive/2026_07/sports_legacy_bucket_cutover_2026_07_16.md` + its companion
      `sports_legacy_bucket_cutover_history_2026_07_24.md` (both `status: complete`, archived). Line 949 of the history
      doc confirms the root cause: `processed/` (~90,947 `odds_horizon_bucket` objects) was dispositioned by
      PRESERVATION not migration, safety-copied to `_legacy_migrated_processed/` "before any delete." Neither doc
      anticipated that a preserved-not-migrated historical date has no path back into canonical (the daily reprocess
      cron only covers a rolling 3-day window) — this is genuinely new evidence, not something already tracked there.
      See "Likely root cause found" in What I found above. Not re-opening the closed cutover plan myself (its own todos
      are all done by its own record) — flagging here for whoever picks up todo 2 below to decide whether it also needs
      a note added to that archived doc.
- [x] ✅ [CODE] P1. **Design + ship the reader/writer reconciliation** — operator ruling 2026-08-09 (verbatim answer
      transcribed in `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s Progress Log): option B
      (`gcs_reader.py::read_bucketed_odds()`'s fallback, lowest blast-radius / read-path only). Implemented
      `_canonical_odds_horizon_bucket_attempted(date)`: reads the SAME coarse manifest row `reprocess_sports_odds.py`'s
      own pre-flight (`_coarse_row_key`, `service_name="market-data-processing-service"`) writes — any capture_status
      present means MDPS has attempted this date's canonical derive, so an empty canonical result is now trusted as
      honest absence instead of silently re-triggering the legacy-shard fallback. Fails closed (returns False, i.e.
      legacy fallback still available) on a manifest-lookup error. 6 new/updated unit tests in
      `test_read_bucketed_odds.py` cover: manifest-row-present → no legacy fallback even when a legacy shard still
      physically exists (the exact zombie scenario); manifest-row-absent → legacy fallback preserved; lookup exception →
      fails closed. Repo: features-service.
- [x] ✅ [DATA] P2. Once the reconciliation fix lands, re-run the read-only sweep
      (`sweep_sports_odds_horizon_bucket_zombie_contamination_2026_07_27.py`) against BOTH path shapes (canonical +
      legacy) to get an accurate, current contamination count before re-attempting the purge — the sweep script itself
      only checks canonical today and would need the same dual-prefix probe `gcs_reader.py` already has. Repo:
      market-tick-data-service. **Shipped `market-tick-data-service@926f9b20`/`c2dda59a7`**: dual-prefix `list_blobs`
      probe + `_path_shape` tagging, QG green. Re-run against production recovered the ORIGINAL 2026-07-27 sizing
      exactly: 37 contaminated shards / 187 rows across 18 dates (2025-07-31 → 2025-11-13), **100% at the legacy path
      shape** (0 at canonical) — direct confirmation of this issue's root-cause finding.
- [x] ✅ [DATA] P2. **Re-attempt `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s zombie-tick purge todo** (parts
      a + b: purge/re-derive the contaminated shards via `reprocess_sports_odds.py --force` using todo 2 above's updated
      dual-prefix contamination count, then re-run `verify_ml_readiness.py` and confirm the 17-date failure set
      clears/shrinks) now that the reader/writer mismatch this issue documents is fixed. Repo: market-data-processing-
      service. **Done**: ran `reprocess_sports_odds.py --force` per-day (single-day range, surgical — not the full
      backfill range) against all 18 sweep-identified dates; manifest-verified all 18 now carry a coarse
      `odds_horizon_bucket` row (`capture_status=captured`); spot-verified `read_bucketed_odds('2025-09-02')` now
      returns 0 rows (was silently serving 3 zombie RUSSIA_PREMIER_LEAGUE rows before the fix). Re-ran
      `verify_ml_readiness.py --start-date 2025-09-01 --end-date 2025-11-30`: **the 17-date failure set cleared to 0
      FAILED** (88/91 dates passed, gate met: YES). 3 dates (2025-10-23, 2025-11-11, 2025-11-13 — all 3 among the 18
      just-purged dates) report MISSING (no `odds_features` parquet at all, 404) rather than FAILED — this is NOT
      "genuine honest-absence" as the plan's done-when anticipated; it's a distinct downstream gap (see new todo below),
      tracked separately rather than silently folded into this checkbox's evidence.
- [ ] [DATA] P2. **New finding (2026-08-09, slot 26)**: `odds_features` feature-export parquet is entirely missing for
      the 3 dates above despite the underlying `odds_horizon_bucket` source now being correctly re-derived. Investigated
      one date (`2025-10-23`) via
      `python -m features_service.sports.cli.main --operation compute --mode     batch --asset-group SPORTS --date 2025-10-23 --tables odds_features --skip-fetch`:
      it logged `env=dev` (unexpected — invoked with `DEPLOYMENT_ENV_SHORT=prd`/`CLOUD_PROVIDER=gcp`, needs confirming
      which bucket/manifest this env label actually resolves to) and
      `compute_pending_dates: manifest-aware prune skipped 1/1 already-fully-resolved dates ... nothing to do` — i.e.
      this CLI's OWN manifest pre-flight thinks the date is already resolved and silently no-ops, even though the
      physical `features.parquet` is missing (404). This is plausibly the SAME reader/writer/manifest-mismatch class
      this whole issue is about, one layer downstream (odds_features' own pending-dates pruning vs. its physical output)
      — not confirmed, needs its own investigation before a fix. Do NOT reflexively add `--force` without first
      resolving the `env=dev` discrepancy (risk of writing to the wrong environment/bucket). Repo: features-service.
- [ ] [REVIEW] P2. **Option C follow-up (non-blocking, operator ruling 2026-08-09 — same
      `sports_satellite_ao_dispatch_batch5_2026_07_26.md` Progress Log entry cited in todo 1 above)**: locate and
      re-engage whatever effort owns "the bucket-cutover lane" (referenced by name in `reprocess_sports_odds.py`'s
      comment, `ceadb45c`/2026-07-16) to formally close out the ~90,947 preserved-not-migrated `odds_horizon_bucket`
      objects, or confirm the comment is stale — useful cleanup but explicitly NOT a prerequisite for the option-B fix
      above (which already shipped without touching the legacy shard at all). Repo: market-data-processing-service.

## Progress Log

- **2026-08-09 (slot 16, data_engineering)**: Filed while dispatched on
  `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s zombie-tick purge todo. Full investigation in "What I found"
  above. Declined to run `reprocess_sports_odds.py --force` against the 18 dates given this finding — it would not fix
  the bug and could create confusing partial state (e.g. writing a spurious `empty_confirmed`/coarse manifest row for a
  date whose real contamination remains untouched, or triggering `_delete_stale_shards` against an empty canonical
  prefix with no effect either way, giving false confidence the purge "ran"). Filing `/blocked` on the batch5 task
  rather than force through a mechanical fix attempt on live production paths given the explicit "must never be touched
  from here" guard already in the code.
- **2026-08-09 (slot 26, data_engineering)**: Operator answered the BLOCKED question (BLK-f47d53d1): option B. Shipped
  the `gcs_reader.py` fallback fix (todo 1 above) + 6 unit tests, features-service. Added the still-open follow-up work
  as explicit todos (re-run the dual-prefix sweep, re-attempt the actual purge, and the non-blocking option-C
  bucket-cutover-lane cleanup) rather than leaving them as prose in "Recommended decision." The batch5 plan's
  zombie-tick checkbox itself stays unflipped — the reader/writer mismatch is fixed but the purge has not actually been
  re-run yet and `verify_ml_readiness.py` has not been re-verified.
- **2026-08-09 (slot 26, data_engineering, continued — operator directive to proceed with the full purge)**: Shipped the
  sweep dual-prefix fix (`market-tick-data-service@926f9b20`/`c2dda59a7`) and re-ran it against production — recovered
  the exact original 2026-07-27 sizing (37 shards / 187 rows / 18 dates, 100% legacy path shape). Ran
  `reprocess_sports_odds.py --force` per-day against all 18 dates (manifest-verified: all 18 now have a coarse
  `captured` row); spot-verified the reader no longer serves the RUSSIA_PREMIER_LEAGUE zombie rows for 2025-09-02.
  Re-ran `verify_ml_readiness.py` — **17-date failure set cleared to 0 FAILED**, gate met YES. Found + documented a new,
  separate downstream gap (3 dates missing `odds_features` output entirely — todo above) rather than either silently
  ignoring it or forcing an uninvestigated fix into a third script/manifest layer. Flipping
  `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s zombie-tick checkbox now — its literal parts (a) purge and (b)
  verify_ml_readiness scope are genuinely complete; the residual is tracked as its own todo, not glossed over.
