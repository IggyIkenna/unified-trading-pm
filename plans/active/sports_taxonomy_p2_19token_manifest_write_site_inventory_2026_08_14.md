---
doc_type: plan
title: Sports taxonomy P2 — full manifest-write call-site inventory for the 19-token lowercase re-stamp
summary: >-
  The P2 19-token lowercase re-stamp's own plan scoped the registry/writer-side fix to "5 confirmed call sites, 8
  registries." This session found that scope is materially incomplete — every per-vendor sports reference-data writer
  (footystats/sfi/transfermarkt/understat/weather) plus large chunks of sports_reference_core.py stamp one of the 19
  uppercase tokens directly into the manifest, none of which were enumerated by the prior trace. This plan is the
  dedicated, properly-enumerated classification pass main directed (in place of a rushed session-bounded hand-patch of
  ~14 files) — vendor-by-vendor, each call site classified SIMPLE (safe to translate immediately) vs ORDERED (a UAC-axis
  registry lookup on the same variable must run first) per the pattern already proven in process_preflight.py/
  sports_dependency.py/writers.py/catalogue.py. A rushed hand-patch risks silently missing a site and reintroducing the
  exact split-token bug this whole migration exists to fix — worse than shipping nothing, since it would look done.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, migration, canonicalisation, manifest, call-site-inventory, 19-token, data_type]
related:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/sports_taxonomy_p2_consumer_inventory_2026_08_12.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
  ]
created: 2026-08-14
last_updated: 2026-08-14
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
sequential: false
priority: P0
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
effort: high
supersedes:
superseded_by:
drift_direction: advance-code
depends_on: [sports_taxonomy_p2_migration_2026_08_08]
gate_on_depends: false
context_scope:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py,
    instruments-service/instruments_service/engine/orchestrator/sports_reference_core.py,
  ]
source:
  [
    "sports_taxonomy_p2_migration-512ce1de0aa5 (slot-26), discovered while drafting the 19-token re-stamp's steps 2-3
    code",
  ]
locked_by:
locked_since:
---

# Sports taxonomy P2 — full manifest-write call-site inventory

> **Why this doc exists**: `sports_taxonomy_p2_migration_2026_08_08.md`'s 19-token lowercase re-stamp todo scoped the
> registry/writer-side fix ("step 2/3") to "5 confirmed manifest-boundary call sites" + "8 registries." Slot-18's
> 2026-08-14 resume session already found that "8 registries" framing was wrong (0 registries need a literal rewrite —
> the real fix is a translation-wrapper at 5 call sites). THIS session (slot-26, same day) found the "5 call sites"
> framing is _also_ wrong — it covered only `process_preflight.py`/`sports_dependency.py`/`writers.py`/`catalogue.py`/
> `sports_reference_fixtures_write.py`, but every OTHER per-vendor sports writer (footystats/sfi/transfermarkt/
> understat/weather) stamps its own 19-token value directly into the manifest too, completely unaudited by the prior
> trace. See `BLK-dc738bb5`, `BLK-0a3f3791`, `BLK-1479b716` (this session's blocked-questions) for the live decision
> trail; main's answer to BLK-1479b716 (Option A) is what created this doc.

## Code-prep branch (NOT merged — do not land until the VM re-stamp is scheduled in the same window)

`instruments-service@sports-taxonomy-p2-19token-lowercase-codeprep-2026-08-14` (pushed, PR not yet opened): 4 files
already fixed + locally QG-clean (ruff lint + format pass; not yet run against live GCS):

- `process_preflight.py` — `check_shard_freshness()` call: forward-translate `expected` via
  `canonical_sports_is_data_type(e) or e`, reverse-map `missing`/`stale` back to the original UAC-uppercase form. Also:
  `.get(m, m)` instead of `[m]` on the reverse-map lookups (found this session — a hard `[m]` KeyErrors whenever
  `check_shard_freshness`'s returned missing/stale contains a value outside the translated input list, as
  `test_process_instruments_all_venues_skipped_before_launch`'s loosely-mocked return demonstrated). **Also found this
  session, during the final verification sweep**: a SECOND, entirely separate write site at `process_preflight.py:754`
  (`record_captured_from_counts` in the ENRICHMENT-ONLY reprocess path, gated by a 5-entity `_self_manifested_enr`
  exclusion set — live/reachable, unlike `process_enrichment.py`'s dead 7-key-gated twin) was NOT part of the original
  "already fixed" description and was missed by every classification pass until a final whole-repo re-grep caught it —
  proof the "verify nothing was missed" REVIEW todo is load-bearing, not ceremonial. Fixed identically to the other
  `entity_name.upper()` SIMPLE sites.
- `sports_dependency.py` — `_API_FOOTBALL_FIXTURES_DATA_TYPES` widened to a superset
  (`{"FIXTURES", "FIXTURES_SCHEDULE", "fixtures_schedule"}`) rather than a hard swap, so the `.isin()` check is correct
  BOTH before and after the physical re-stamp — no ordering hazard on this one.
- `writers.py::_classify_venue_write` — lower `manifest_data_type` strictly AFTER
  `_orch._pipeline_mode_for_sports_data_type(manifest_data_type)` runs on the uppercase form.
- `catalogue.py::_write_catalogue_record` — lower `manifest_data_type` immediately (no lookup dependency in this
  function — `pipeline_mode` is hardcoded `BATCH_INSTRUMENTS_SERVICE`, not derived from `manifest_data_type`).

**Do NOT merge this branch to `main`/`live-defi-rollout` standalone** — instruments-service deploys as a Cloud Run Job
polling every ~15 min (`/codex/04-architecture/runtime-deployment-topology.md` §21); merging before the physical
re-stamp (P2's step-1 VM launch) runs would deploy the new lowercase-comparison logic against a still-uppercase manifest
on the very next poll, reproducing the exact case-sensitive `check_shard_freshness` mismatch / re-fetch-storm this whole
migration exists to prevent (`unified_trading_library/manifest_writer/_queries.py:149`, exact string match, no
case-insensitive fallback). Land this branch's commits ATOMICALLY with the VM launch, once ALL the sites below are also
fixed and the operator has approved the `[OPERATOR]` VM-launch todo on the parent plan.

## The classification method (proven correct on the 4 files above — apply identically below)

For every `manifest.record_captured(...)` / `record_failed(...)` / `record_empty(...)` /
`record_captured_from_counts(...)` / `record_expected_empty(...)` / `note_empty(...)` / `note_failed(...)` call that
writes one of the 19-token vocabulary into `data_type`:

1. Find the exact variable/literal carrying the token into the manifest write.
2. Grep the surrounding function (and anything it's called from/into) for a lookup on the SAME variable, and sort it
   into ONE of two buckets — **CORRECTED 2026-08-14 (mid-code-authoring)**, see the "NEW FINDING" section below for why
   the original single-bucket version of this step was wrong for one entry:
   - **UAC-registry lookup** (`get_entity_league_coverage`, `_pipeline_mode_for_sports_data_type`,
     `is_league_entity_covered`, `get_source_coverage_start`, `SPORTS_DATA_TYPE_TO_SOURCE`,
     `_RETIRED_SPORTS_DATA_TYPES`) — a plain Python dict/constant keyed on the PERMANENT uppercase UAC vocabulary,
     unrelated to what's on disk. Needs the ORIGINAL uppercase value — translate AFTER this runs.
   - **Manifest-read lookup** (`_should_skip_shard`, `_should_skip_date_for_per_league`, `ManifestWriter.lookup()`
     directly, `check_shard_freshness()`) — does an EXACT-MATCH read against the manifest's own stored `data_type`
     column (confirmed: `ManifestWriter.lookup()`'s docstring says "exact on every populated key";
     `_should_skip_date_for_per_league` docstring says "exactly as ManifestWriter.lookup would" and its body does a
     literal `_df[_col] == _want` filter). Post-restamp that column holds LOWERCASE — needs the TRANSLATED value,
     translate BEFORE this runs (same direction/timing as the writes, not the opposite).
3. **SIMPLE** (no lookup dependency, or the lookup uses its own independent literal — translating a manifest-write
   literal never touches a separate literal used elsewhere) → wrap with `canonical_sports_is_data_type(X) or X`
   immediately at the write.
4. **ORDERED against a UAC-registry lookup** (the SAME variable feeds both a registry lookup and a later write) → insert
   the translation AFTER the last registry-lookup use and BEFORE the first write use — cite both line numbers.
5. **ORDERED against a manifest-read lookup** (the SAME variable feeds both a skip-check/`.lookup()` and a later write)
   → insert the translation BEFORE the first manifest-read use (it needs the translated value too) — the skip-check and
   every write downstream then share the SAME translated value, cite the insertion line number.
6. Import: `from unified_api_contracts.sports import canonical_sports_is_data_type` (already the convention in the 4
   fixed files, matching the existing `FIXTURES_SCHEDULE` import).

**Known non-obvious trap** (found this session, `sports_reference_core.py`): the SAME small function can use its
`data_type` parameter for BOTH a lookup and a write, meaning "ORDERED" is a per-STATEMENT property, not a per-VARIABLE
one — do not assume translating a parameter once at function entry is always safe; check every use inside the function
body.

## Confirmed inventory — DONE (classified, not yet coded except the 4 files above)

### footystats.py — 23 call sites, ALL SIMPLE

Every write is a bare string literal (`"PREDICTIONS"`, `"MATCHES"`, or `"ODDS"`) — never a shared variable — so the
nearby UAC lookups (`get_source_coverage_start`, `_should_skip_date_for_per_league`,
`_pipeline_mode_for_sports_data_type`) each carry their OWN independent literal, untouched by translating a different
literal occurrence. Exact line numbers (row_key + parallel `data_type=` kwarg where present): 106/107, 126/127,
246(249,255), 275(278), 303(304,308), 326(327,331), 347(348), 368(369), 407(408) [PREDICTIONS]; 516/517, 536/537,
664(665,669), 689(690), 723(724), 738(739), 770(771) [MATCHES]; 1040(1043,1049), 1076(1079), 1104(1105,1109),
1129(1130), 1149(1150,1154), 1169(1170), 1199(1200) [ODDS]. Mechanical fix: replace each literal occurrence in the
row_key/kwarg (never the co-located lookup calls at footystats.py lines
90/100/351/372/411/501/510/727/742/774/900/1133/1173/1203, which must keep their own uppercase literal unchanged).

### sfi.py — 11 call sites, ALL SIMPLE

All write the literal `"SFI_PROGRESSIVE_STATS"`. Lines (row_key, + kwarg where present): 281(282), 289(292), 314(317),
480(483,489), 509(512), 546(549), 577(578), 586(589), 601(602), 609(612), 653(656). Two independent-literal lookups at
sfi.py:151 (`_should_skip_date_for_per_league`) and sfi.py:276 (`get_source_coverage_start`) — untouched.

### transfermarkt.py — 5 write sites + 1 manifest-read site, ALL ORDERED against the manifest-read (single shared fix

    point) — FIXED (`instruments-service` branch, this session)

`data_type` is carried by the local variable `_tm_data_type` (assigned at transfermarkt.py:559 —
`"TRANSFER_RECORDS" if _want_transfers else "PLAYER_VALUES"`), fed into
`_should_skip_date_for_per_league(data_type=_tm_data_type)` — a MANIFEST-READ lookup (see the corrected classification
method above), not a UAC-registry one. **Single fix, corrected**: translate `_tm_data_type` BEFORE the skip-check runs
(immediately after `_expected_pv_league_ids` is built, transfermarkt.py — right before the
`if _orch._should_skip_date_for_per_league(...)` call) so the skip-check AND all 5 downstream writes (lines 629→now
shifted, 935, 951, 959, 967 pre-edit numbering) share the one translated value. **`TRANSFER_RECORDS` resolved (see the
todo above)**: confirmed NOT a `SPORTS_DATA_TYPE_TO_SOURCE` member — `canonical_sports_is_data_type("TRANSFER_RECORDS")`
returns `None`, so the `or _tm_data_type` fallback leaves it untouched; not a 20th in-scope token, no special-casing
needed.

### understat.py — 14 call sites, ALL SIMPLE

XG: 98(99), 118(119), 220(221,225), 251(252), 290(291), 296(298), 309(310), 341(342). XG_SHOTS: 413(414), 433(434),
508(509,521), 538(539), 545(546), 578(579). Independent-literal lookups at 92/407 (`get_source_coverage_start`) —
untouched.

### weather.py — 9 call sites, ALL SIMPLE (2 collapse to 2 edits via shared helpers)

All write `"WEATHER"`. Two local helper closures cover most call-through sites: `_record_weather_empty` (def
weather.py:70, single edit at weather.py:95 fixes every invocation — lines 212/331/351/598/628) and
`_record_weather_failed` (def weather.py:103, single edit at weather.py:111 fixes invocations at lines 199/613).
Remaining direct sites: 126(127), 146(147), 314(317), 332(333), 531(534), 577(578), 595(596). Independent-literal lookup
at weather.py:120 (`get_source_coverage_start`) — untouched.

### sports_reference_core.py — full file read, cluster fully classified

`emit_empty_gaps_for_entity` (core.py:297) is the cross-purpose hub: within ONE invocation its `data_type` param is
consumed 4 different ways in this order — (1) core.py:330 `_presence_guarded_captured_leagues(data_type, ...)` —
ALREADY-SAFE, see below; (2) core.py:334→252 `_manifest_index_guarded_captured_leagues` →
`_manifest_captured_leagues_ for_data_type(data_type=data_type)` — needs LOWERCASE; (3) core.py:339
`get_entity_league_coverage(data_type)` — needs UPPERCASE; (4) core.py:343 loop →
`_emit_empty_gap_for_league(data_type, ...)` → core.py:262 `is_league_entity_covered` — needs UPPERCASE. Because (3)/(4)
run AFTER (2) and need the ORIGINAL value, translation for (2) must be a call-site-local expression at core.py:252 —
**never** a reassignment of the `data_type` parameter itself.

- `_emit_empty_gap_for_league` (core.py:257) — ORDERED. Bind
  `_dt_lower = canonical_sports_is_data_type(data_type) or data_type` immediately AFTER the core.py:262
  `is_league_entity_covered` check, then use `_dt_lower` in all three `record_empty` row_keys: core.py:265-266,
  core.py:281-282, core.py:289-290 (each also has an independent `source=_orch._sports_ref_source(data_type.lower())` at
  270/286/294 — already idempotent, untouched).
- `_manifest_index_guarded_captured_leagues` (core.py:228) — the READ at core.py:252 needs LOWERCASE, translated inline
  at that call only — do NOT mutate the function's own `data_type` param (reused UPPERCASE by the caller afterward, per
  the hub's ordering above).
- `_presence_guarded_captured_leagues` (core.py:187) — ALREADY-SAFE: its
  `_list_present_parquet_leagues(..., data_type.lower())` call (core.py:200) already does a bare `.lower()`,
  byte-identical to `canonical_sports_is_data_type()`'s output for any of the 19 tokens — do not touch.
- `note_failed` (def core.py:148, write at core.py:163) and `note_empty` (def core.py:173, write at core.py:176) —
  SIMPLE, single fix INSIDE each method body (no UAC-axis lookup anywhere in either method — the `data_type.lower()` at
  core.py:156/184 is a cosmetic log/source string, not a lookup). One fix per method covers every caller:
  `note_failed("TEAMS", ...)` (core.py:525, 536), `note_failed("STANDINGS", ...)` (core.py:643),
  `note_failed("INJURIES", ...)` (core.py:871), `note_empty(FIXTURES_SCHEDULE, ...)`
  (`sports_reference_fixtures.py:244`, the ONLY `note_empty` call in the whole codebase — confirmed by repo-wide grep),
  `note_failed(FIXTURES_SCHEDULE, ...)` (`sports_reference_fixtures.py:281`).
- Further `record_captured` sites found later in the file, all SIMPLE (literal token, no lookup dependency — the
  `emit_empty_gaps_for_entity(...)` call each function makes afterward passes a FRESH literal, not a reused variable):
  `_write_teams_and_venues` TEAMS (core.py:593-594 row_key, 598 kwarg), `_write_standings_per_league` STANDINGS
  (core.py:679, 682, 688), `_fetch_injuries` INJURIES (core.py:798, 801, 807).
- `_close_stale_enrichment_expected_unattempted_cells` (core.py:346) — 3× `record_empty` (core.py:440, 456, 477), all
  ORDERED, all gated by the SAME per-iteration `is_league_entity_covered(_lid, _dt_str)` check at core.py:439 — bind one
  translated local right after 439, reuse across all three.
- No `record_captured_from_counts` calls exist in this file. No NOT-19-TOKEN sites found — every value resolves to a
  confirmed member of the 19-key `SPORTS_DATA_TYPE_TO_SOURCE` vocabulary (verified against
  `unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py:209-262`).

### sports_reference_fixtures_write.py — `af_entity_dt` question resolved: per-call-site translation, NOT upstream

Full-file read confirms `af_entity_dt` (from `_entity_dt_for_short()`) is used for exactly two purposes: (1) manifest
writes wanting LOWERCASE, and (2) an opaque passthrough into `hooks.emit_empty_gaps_for_entity(af_entity_dt, ...)`
(lines 226, 313) — a DIFFERENT-FILE hook (`sports_reference_core.py`) that internally needs the UPPERCASE form for its
own lookups. **`af_entity_dt` is never used for a lookup within this file itself.** This means a single upstream
translation at `_entity_dt_for_short()`'s call site (line 331) would be WRONG — it would silently corrupt the
line-226/313 passthrough. Correct fix: translate a LOCAL COPY only at the write sites, leave `af_entity_dt` itself (and
its two passthrough uses) untouched/uppercase:

- `_write_fixture_entity_per_league` — `record_captured` at lines 163 (row_key) + 169 (kwarg).
- `_handle_empty_fixture_entity` — `record_failed` at lines 285 (row_key) + 298 (row_key, the no-league-mapping fallback
  branch) — these two branches are mutually exclusive within one call (the `if _fail_count > 0` / `else` at lines
  275/303), and the `else` branch's passthrough (line 313) never runs alongside a write, so there is no shared-variable
  reuse hazard here (unlike the per-league-loop case above).

### process_write.py / process_zero_records.py / process_completeness.py / process_enrichment.py / process_fetch.py — full sweep COMPLETE

All 5 files read in full. Verified in UAC source: `FIXTURES_SCHEDULE` is an immutable module constant (never reassigned
to a local var in these 5 files → inherently SIMPLE wherever it appears); `_pipeline_mode_for_sports_data_type`
internally does `.upper()` on its input, so it is case-insensitive and NOT actually an ordering hazard despite being
listed as an example lookup in the classification method above; `sports_reference.py`'s `_fetch_sports_reference_data`
only ever populates `counts` with the 7 keys
`{teams, standings, injuries, fixture_stats, fixture_events, fixture_lineups, player_stats}` — all confirmed 19-token
members, closing the "which entity" ambiguity for every `entity_name.upper()` / `pf_entity` dynamic site below.

**process_write.py** — 3 confirmed SIMPLE sites, all `FIXTURES_SCHEDULE`: line 293+299 (`record_captured`, one call,
wrap both), line 363 (`record_empty`), line 376 (`record_empty`). Remaining sites (455, 531, 574, 870) are NOT-SPORTS
(prediction / TradFi / venue-grain CEFI-DEFI-TRADFI) — confirmed out of scope, no fix needed.

**process_zero_records.py** — richest file, 6 confirmed sports sites:

- Lines 254+264 (`record_failed`/`record_empty`, share one `_row_key` built at line 247-251) — `FIXTURES_SCHEDULE`,
  SIMPLE, single fix point at line 249.
- Line 328 (`record_captured_from_counts`) + line 359 (`record_empty`) — `entity_name.upper()` ∈ {TEAMS, STANDINGS}
  (confirmed closed set), SIMPLE, no lookup dependency (pipeline_mode at 339 independently recomputes `.upper()`).
- Line 380 (`record_empty`) — `pf_entity` ∈ {FIXTURE_EVENTS, FIXTURE_LINEUPS, FIXTURE_STATS, PLAYER_STATS}, SIMPLE, fix
  at line 383.
- Line 436 (`record_empty`) — `_enr_entity` ∈ {PREDICTIONS, MATCHES, XG, WEATHER} — **ORDERED**: line 444 does
  `_enr_entity_to_sports_ref_entity[_enr_entity]`, a plain dict keyed by the uppercase literal — a naive top-of-loop
  reassignment would `KeyError`. Fix: wrap inline ONLY at the line-439 row_key literal
  (`canonical_sports_is_data_type(_enr_entity) or _enr_entity`); leave the `_enr_entity` variable itself untouched so
  line 444 still sees the original uppercase key.
- Lines 572/654/720 (`record_expected_empty`) — NOT-SPORTS (CeFi/DeFi pre-launch, no-adapter-yet, TradFi non-trading) —
  confirmed out of scope.

**process_completeness.py** — 1 confirmed sports sub-case, GENERIC-SHARED: line 602 (`record_failed`) is a ternary —
`FIXTURES_SCHEDULE` when `_failed_venue == "API_FOOTBALL"` (line 598), else a non-sports venue row_key. SIMPLE, fix ONLY
the true-branch literal at line 598, leave the else-branch untouched. Line 244 (`record_zero_rows`) is outside this
doc's 5 target write-methods, excluded per scope. Line 721 is NOT-SPORTS (CeFi-only thin-day correction).

**process_enrichment.py** — 1 structurally-GENERIC-SHARED but **currently dead** branch: line 190
(`record_captured_from_counts`, `entity_name.upper()`) is gated by `entity_name not in _self_manifested` (line 179-187),
and `_self_manifested` already covers the full 7-key set `sports_reference.py` can ever emit — so this branch never
executes today. No fix needed now; flag for re-check only if the sports-reference entity set ever grows beyond the
current 7 keys.

**process_fetch.py** — 1 confirmed sports site (matches the mid-session finding already in this doc, re-verified):
`_per_fixture_gcs_fast_path`, `entity_name.upper()` evaluated twice in one `record_captured_from_counts` call — the
row_key occurrence (line ~295) is ORDERED against the `pipeline_mode=` kwarg's independent `.upper()` re-evaluation
(line ~305); translate ONLY the row_key occurrence, leave `pipeline_mode=`'s uppercase untouched. No exclusion filter on
this site (unlike process_zero_records.py:328/359) — every entity `pf_counts` returns gets stamped here.

**Sweep total**: 11 confirmed sports 19-token write statements across the 5 files (7 SIMPLE fix points + 1 ORDERED + 1
GENERIC-SHARED/conditional-branch + 1 dead/no-fix-needed + the 1 already-known process_fetch.py ORDERED site), 10
additional call sites confirmed NOT-SPORTS (correctly out of scope), 1 call site excluded as outside the 5 target
write-methods. **Every `process_*.py` file is now fully classified — no remaining unclassified sports manifest-write
call site in this codebase.**

## NEW FINDING (2026-08-14, mid-code-authoring) — the READ side (skip-checks) has the SAME exact-match hazard, and is COMPLETELY OUTSIDE this doc's scope

This doc's title and every classification pass so far ("full manifest-**write** call-site inventory") only ever swept
`record_captured(...)`/`record_failed(...)`/`record_empty(...)`/`record_captured_from_counts(...)`/
`record_expected_empty(...)`/`note_empty(...)`/`note_failed(...)`. While mechanically fixing `understat.py`, found that
`_orch._should_skip_shard()` (def `venue_core.py:315`) does `manifest.lookup(row_key)` — and `ManifestWriter.lookup()`'s
own docstring (`unified-trading-library/unified_trading_library/manifest_writer/ _writer_io.py:166`) states plainly:
"Dimension matching is **exact** on every populated key." Independently confirmed in
`_should_skip_date_for_per_league()` (def `sports.py:416`), whose docstring says outright it matches "**exactly as**
`ManifestWriter.lookup` would" and whose body does `_df[_col].fillna("").astype(str) == _want` — a hardcoded exact
string equality against the raw uppercase `data_type` argument every caller passes it today.

**Failure mode if shipped as-is**: post-restamp, the manifest stores LOWERCASE `data_type`, but every vendor file still
calls these two skip-check functions with the UPPERCASE literal (same variable the WRITE side used pre-fix). The exact
match against the now-lowercase manifest will find **zero rows, forever** — the skip-check permanently returns "not yet
captured" even for shards that ARE captured. This does not corrupt data (writes still go through, now correctly
lowercase), but it silently defeats every per-date/per-league skip-check across every vendor that uses them — i.e. a
**permanent re-fetch storm** against every vendor API, for every date, from the moment the restamp lands. This is a
DIFFERENT bug shape than the one `check_shard_freshness()` produces (which the parent plan + `process_preflight.py`'s
already-shipped fix already cover), but it is the same ROOT hazard (exact-match manifest read against a raw uppercase
literal) and is **just as capable of reproducing "the exact split-token bug this whole migration exists to fix"** — this
time as silent cost/quota blowup rather than a stale-shard bug.

**Confirmed call-site count** (`grep -c "_should_skip_shard(\|_should_skip_date_for_per_league("` across the 7
vendor/core files already classified for writes): footystats.py=3, sfi.py=1, transfermarkt.py=1, understat.py=2,
weather.py=0, sports_reference_core.py=0, sports_reference_fixtures_write.py=0 — **7 confirmed read call sites**, not
yet individually classified (which literal each one passes, whether it's SIMPLE-safe to just wrap the argument at the
call, or whether the same variable is ALSO used in a write earlier/later in the same function — the ORDERED-vs-SIMPLE
method above applies here too, just for reads instead of writes). **`process_preflight.py`'s `check_shard_freshness()`
fix is NOT reusable here** — different function, different manifest-read primitive (`check_shard_freshness` vs
`.lookup()`/`_should_skip_date_for_per_league`'s own inline exact-match filter).

**Resolved (2026-08-14, same session, follow-up)**: the fix pattern is the SAME translation primitive as the write side
(`canonical_sports_is_data_type(X) or X`), just applied on the READ side, BEFORE the skip-check call instead of after —
see the corrected classification method (step 2's two-bucket split) above. This is not a separately-deferred task; it is
being fixed FILE-BY-FILE, inline with the write-side mechanical work, since both hazards live in the same functions and
require touching the same lines anyway. `transfermarkt.py`'s 1 read site is already fixed this way (see its section
above); the remaining 6 read sites (footystats.py=3, sfi.py=1, understat.py=2) are fixed as part of those files' own
write-side todo below, not a separate pass.

## Todos

- [x] ✅ [DATA] P0. **Finish classifying `sports_reference_core.py` in full + resolve
      `sports_reference_fixtures_write.py`'s `af_entity_dt` question.** DONE — see the "sports_reference_core.py" /
      "sports_reference_fixtures_write.py" sections above (full-file reads, every call site classified with exact line
      numbers; the `af_entity_dt` translation point is per-call-site, not upstream).
- [x] ✅ [DATA] P0. **Classify `process_write.py`, `process_zero_records.py`, `process_completeness.py`,
      `process_enrichment.py`, `process_fetch.py`** for sports 19-token manifest writes. DONE — see the
      "process_write.py / process_zero_records.py / process_completeness.py / process_enrichment.py / process_fetch.py"
      section above: 11 confirmed sports write statements classified (7 SIMPLE + 2 ORDERED + 1 conditional-branch
      SIMPLE + 1 currently-dead branch), 10 sites confirmed NOT-SPORTS. Classification phase for the ENTIRE codebase is
      now complete — remaining todos are code-authoring + verification, not further discovery.
- [x] ✅ [DATA] P1. **Resolve the `TRANSFER_RECORDS` open question** (found in transfermarkt.py). DONE — confirmed by
      direct read of `unified_api_contracts/canonical/domain/sports/league_data.py:208-262`:
      `SPORTS_DATA_TYPE_TO_SOURCE` has NO `"TRANSFER_RECORDS"` key (only `"PLAYER_VALUES": "transfermarkt"`), and
      `SPORTS_IS_DATA_TYPE_LOWERCASE_FORM` (line 297) is comprehension-derived FROM that dict's keys, so
      `canonical_sports_is_data_type("TRANSFER_RECORDS")` returns `None`. **Not a 20th in-scope token** — the existing
      `canonical_sports_is_data_type(_tm_data_type) or _tm_data_type` fallback formula already handles this correctly
      with zero special-casing: `PLAYER_VALUES` → `"player_values"`, `TRANSFER_RECORDS` → `None` → falls back to the
      original literal, untouched. No operator escalation needed; the single fix point at transfermarkt.py:606 is
      confirmed scope-safe as specified.
- [x] ✅ [DATA] P0. **NEW (discovered mid-code-authoring), then resolved same session: classify + fix the READ-side
      exact-match hazard** — `_should_skip_shard()`/`_should_skip_date_for_per_league()` call sites (7 confirmed:
      footystats.py=3, sfi.py=1, transfermarkt.py=1, understat.py=2) each pass `data_type` into an exact-match manifest
      read (`ManifestWriter.lookup()` / `sports.py:416`'s own inline exact-match filter), which the write-only sweep
      missed. Fix pattern resolved: same `canonical_sports_is_data_type(X) or X` primitive, applied BEFORE the
      skip-check instead of after — see the corrected classification method + "NEW FINDING" section above.
      `transfermarkt.py`'s site fixed this session; the remaining 6 (footystats.py=3, sfi.py=1, understat.py=2) are
      fixed inline with those files' write-side todo below, not a separate pass.
- [x] ✅ [DATA] P0. **Author + locally validate the fix code for ALL remaining files.** DONE — footystats.py (23 write +
      3 read sites), sfi.py (11 write + 1 read site), understat.py (14 write + 2 read sites), weather.py (9 write
      sites), sports_reference_core.py (note_failed/note_empty/`_manifest_index_guarded_captured_leagues`/
      `_emit_empty_gap_for_league`/TEAMS/STANDINGS/INJURIES/`_close_stale_enrichment_expected_unattempted_cells`),
      sports_reference_fixtures_write.py (2 methods), process_write.py/process_zero_records.py/
      process_completeness.py/process_fetch.py, and a NEW second site found in process_preflight.py:754 (see below) —
      all fixed, `instruments-service@5b1b2c72` on the held-back branch, NOT merged. Full `quality-gates.sh` green
      (ruff + basedpyright + full pytest suite, 5396 passed) — went beyond the "ruff + basedpyright at minimum" bar once
      the full-suite run surfaced 9 (then 5 more) pre-existing tests asserting the pre-migration uppercase form; all 18
      assertions across 6 test files updated to expect the new lowercase values, zero real regressions found. Also fixed
      2 latent bugs surfaced by the full-suite run: `process_preflight.py`'s `_to_original_entity[m]` hard lookup →
      `.get(m, m)` (KeyErrors when `check_shard_freshness`'s return isn't a subset of the translated input —
      demonstrated by a loosely-mocked test), and the second `process_preflight.py:754` write site itself.
- [x] ✅ [REVIEW] P0. **Verify NO manifest-write call site in the sports reference-data path was missed.** DONE — the
      systematic re-grep caught exactly one straggler (`process_preflight.py:754`, see above), confirming this todo is
      load-bearing, not ceremonial. Also caught (and fixed) a same-turn regression: 2 parallel same-file `Edit` calls in
      one message silently dropped one of two intended `replace_all` matches (`process_write.py:381` kept the old
      uppercase literal despite the tool reporting "all occurrences replaced") — a real tool-batching hazard, not just a
      classification gap; the fix going forward is to grep-verify every `replace_all` result rather than trust the
      tool's own success message, especially under same-file parallel edits. Final re-grep after all fixes: zero
      remaining literal-uppercase manifest-write/read sites outside the two confirmed-dead/confirmed-untouchable
      exceptions (`process_enrichment.py:191`'s dead branch; UAC-registry lookups' own independent literals).
- [ ] [OPERATOR] P0. **Bring the completed branch back to `sports_taxonomy_p2_migration_2026_08_08.md`'s `[OPERATOR]`
      19-token execution todo for the atomic land-and-launch decision** — this doc's job is now done: a fully
      classified + coded + locally-validated branch (WRITE side AND the READ side both fixed, full test suite green) at
      `instruments-service@5b1b2c72`. The actual merge + VM launch stays gated on that parent todo per BLK-0a3f3791's
      resolution (Cloud Run Job auto-deploy risk) and the parent plan's own atomicity rule — merge and VM launch happen
      in the SAME window, never separately, and only on explicit operator go-ahead.

## Progress Log

- **2026-08-14** — Authored (slot-26), per main's Option-A answer to BLK-1479b716. 4 files already fixed + pushed to
  `instruments-service@sports-taxonomy-p2-19token-lowercase-codeprep-2026-08-14` (not merged). 5 vendor files
  (footystats/sfi/transfermarkt/understat/weather) fully classified via 5 parallel Explore agents — 62 call sites total,
  57 SIMPLE + 5 ORDERED (all 5 ORDERED sites share one fix point in transfermarkt.py). `sports_reference_core.py`
  cluster + `process_fetch.py` partially classified mid-session (found via targeted reads + a raw-transcript grep, not
  yet exhaustively verified) — left as open todos rather than rushed to completion, per main's explicit reasoning that a
  session-bounded hand-patch risks silently missing a site.
- **2026-08-14 (same session, follow-up)** — `sports_reference_core.py` + `sports_reference_fixtures_write.py`
  classification COMPLETED (the file-classification Explore agent finished after the entry above was written) — full
  files read, every call site classified with exact line numbers, resolving both open questions from the entry above:
  the `af_entity_dt` translation point is per-call-site (NOT upstream at `_entity_dt_for_short()`, which would have
  corrupted the `emit_empty_gaps_for_entity` passthrough's own lookups), and `emit_empty_gaps_for_entity` is confirmed
  as a 4-way cross-purpose hub needing call-site-local translation, never a parameter reassignment. See the updated
  "sports_reference_core.py" / "sports_reference_fixtures_write.py" sections above (todo 1 from the original entry is
  now folded into this doc's body, not a separate open item). Only the `process_*.py` sweep (todo below) and the
  `TRANSFER_RECORDS` scope question remain open.
- **2026-08-14 (same session, second follow-up)** — `process_write.py`/`process_zero_records.py`/
  `process_completeness.py`/`process_enrichment.py`/`process_fetch.py` classification COMPLETED (5th and final parallel
  Explore agent finished, ~622s runtime). 11 confirmed sports 19-token write statements found across the 5 files (most
  significant new finding: `process_zero_records.py:436` is a second, previously-unknown ORDERED site — a dict keyed on
  the raw uppercase `_enr_entity` at line 444 that a naive fix would `KeyError`). All 10 files in the sports
  reference-data write path are now fully classified with exact line numbers; **the classification phase for this entire
  migration is done**. Only remaining open items: the `TRANSFER_RECORDS` scope question (P1, operator input needed) and
  the 3 code-authoring/verification/land todos below.
- **2026-08-14 (same session, third follow-up — code-authoring + verification COMPLETE)** — resolved `TRANSFER_RECORDS`
  (not a 20th token, confirmed via direct UAC source read). Discovered and resolved a classification-method error
  mid-authoring: `_should_skip_shard`/`_should_skip_date_for_per_league` are manifest-READS needing the translated value
  BEFORE the call (not UAC-registry lookups needing the original AFTER) — corrected the method, re-ordered
  transfermarkt.py's already-shipped fix, and fixed the 6 other read sites this surfaced (footystats.py=3, sfi.py=1,
  understat.py=2) inline with their write-side fixes. Authored + shipped fix code for all 9 remaining files
  (`instruments-service@5b1b2c72`). Full-suite `quality-gates.sh` run surfaced 14 pre-existing test failures (9 then 5
  more) — all confirmed the SAME root cause (tests asserting/mocking the pre-migration uppercase manifest form) except
  one genuine pre-existing bug (`process_preflight.py`'s hard `_to_original_entity[m]` lookup, fixed to `.get(m, m)`).
  Updated 18 assertions across 6 test files; fixed the dict lookup; found + fixed a second live write site
  (`process_preflight.py:754`) via the final systematic re-grep — proof that todo was load-bearing. Also hit and
  documented a same-turn tool hazard: parallel same-file `Edit` calls can silently drop a `replace_all` match despite
  reporting success — mitigated by grep-verifying every batch's result rather than trusting the tool's own message. Full
  suite green (5396 passed), branch pushed, NOT merged. **This doc's job is done** — remaining work is the
  `[OPERATOR]`-gated atomic land-and-launch on the parent plan.
