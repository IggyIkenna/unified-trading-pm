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
  `canonical_sports_is_data_type(e) or e`, reverse-map `missing`/`stale` back to the original UAC-uppercase form.
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
2. Grep the surrounding function (and anything it's called from/into) for a UAC-axis REGISTRY lookup on the SAME
   variable (`get_entity_league_coverage`, `_pipeline_mode_for_sports_data_type`, `is_league_entity_covered`,
   `get_source_coverage_start`, `SPORTS_DATA_TYPE_TO_SOURCE`, `_RETIRED_SPORTS_DATA_TYPES`,
   `_should_skip_date_for_per_league`).
3. **SIMPLE** (no lookup dependency, or the lookup uses its own independent literal — translating a manifest-write
   literal never touches a separate literal used elsewhere) → wrap with `canonical_sports_is_data_type(X) or X`
   immediately at the write.
4. **ORDERED** (the SAME variable feeds both a lookup and a later write) → insert the translation AFTER the last lookup
   use and BEFORE the first write use — cite both line numbers explicitly.
5. Import: `from unified_api_contracts.sports import canonical_sports_is_data_type` (already the convention in the 4
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

### transfermarkt.py — 5 call sites, ALL ORDERED (single shared fix point)

`data_type` is carried by the local variable `_tm_data_type` (assigned at transfermarkt.py:559 —
`"TRANSFER_RECORDS" if _want_transfers else "PLAYER_VALUES"`), fed into
`_should_skip_date_for_per_league(data_type= _tm_data_type)` at transfermarkt.py:597-603 BEFORE every write. **Single
fix**: insert `_tm_data_type = canonical_sports_is_data_type(_tm_data_type) or _tm_data_type` at transfermarkt.py:606
(immediately after the skip-check's early-return block ends) — covers all 5 downstream writes at lines 629, 935, 951,
959, 967. **Open question (flag for operator/plan-author, not resolved by this doc)**: `"TRANSFER_RECORDS"` is NOT one
of the 19 tokens enumerated in the parent plan's todo text. Confirm whether it is a 20th in-scope token (if it's a
member of `SPORTS_DATA_TYPE_TO_SOURCE`, `canonical_sports_is_data_type()` will already translate it, silently widening
the re-stamp's scope beyond "19") or should be excluded from this migration entirely.

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

## Confirmed inventory — IN PROGRESS (partial; NOT fully classified — the two open todos below)

### sports_reference_core.py cluster (large file — partial results this session)

Confirmed from `emit_empty_gaps_for_entity`/`_emit_empty_gap_for_league`/`_manifest_index_guarded_captured_leagues`
(traced in the parent plan's session before this doc was split out):

- `_emit_empty_gap_for_league` (core.py:257) — 3× `record_empty` (lines ~265, ~281, ~289) want the row_key's `data_type`
  LOWERED; the SAME parameter feeds `is_league_entity_covered(_canon_lid, data_type)` (line ~262) which must stay
  UPPERCASE — ORDERED, translate inline at each `record_empty` row_key, not the function parameter.
- `_manifest_index_guarded_captured_leagues` (core.py:228) —
  `_manifest_captured_leagues_for_data_type(data_type= data_type)` (line ~252) is a manifest READ needing the LOWERED
  form — ORDERED, translate inline at this one call.
- `emit_empty_gaps_for_entity` (core.py:297) — `get_entity_league_coverage(data_type)` (line ~339) stays UPPERCASE, no
  change needed there.
- `_presence_guarded_captured_leagues` (core.py:187) — ALREADY SAFE: its
  `_list_present_parquet_leagues(..., data_type .lower())` call (line ~200) already does a bare `.lower()`, which is
  byte-identical to `canonical_sports_is_data_type()`'s output for any of the 19 tokens (the UAC mapping IS
  `{key: key.lower() for key in ...}`) — do not touch this line.
- **NEWLY FOUND mid-session** (raw grep, not yet fully traced): `note_failed`/`note_empty` (core.py:148/173) are called
  with bare uppercase literals — `hooks.note_failed("TEAMS", exc, ...)` (core.py:525, 536),
  `hooks.note_failed( "STANDINGS", exc, ...)` (core.py:643), `hooks.note_failed("INJURIES", exc, ...)` (core.py:871),
  `hooks.note_empty(FIXTURES_SCHEDULE, ...)` (`sports_reference_fixtures.py:244`),
  `hooks.note_failed( FIXTURES_SCHEDULE, exc)` (`sports_reference_fixtures.py:281`) — these are 6 MORE manifest-write
  call sites (TEAMS/ STANDINGS/INJURIES/FIXTURES_SCHEDULE) not covered by the cluster above and not yet
  lookup-dependency-checked.

### process_fetch.py (found mid-session, not yet cross-checked against the other process_*.py files)

`_per_fixture_gcs_fast_path` —
`pf_manifest.record_captured_from_counts(row_key={"date": date, "data_type": entity_name.upper()}, ..., pipeline_mode=_orch._pipeline_mode_for_sports_data_type(entity_name.upper()), ...)`
— a DYNAMIC (not literal) 19-token value (`entity_name.upper()`), ORDERED: the SAME expression is evaluated twice in one
call (row_key wants lowered, `pipeline_mode=` kwarg wants uppercase) — translate only the row_key occurrence, keep the
`pipeline_mode=` kwarg's `entity_name.upper()` untouched.

## Todos

- [ ] [DATA] P0. **Finish classifying `sports_reference_core.py` in full** (it is a large file — this session covered
      the `emit_empty_gaps_for_entity` cluster + found `note_failed`/`note_empty` sites by grep but did not exhaustively
      read the whole file). Confirm exact current line numbers (may have shifted), confirm no further
      `record_captured`/`record_failed`/`record_empty`/`record_captured_from_counts` sites exist beyond what's listed
      above, and classify the 6 `note_failed`/`note_empty` sites (TEAMS/STANDINGS/INJURIES/FIXTURES_SCHEDULE) per the
      SIMPLE/ORDERED method above. Also confirm `sports_reference_fixtures_write.py`'s `af_entity_dt` (from
      `_entity_dt_for_short()`) is used ONLY for manifest writes within that file (no lookup use there) — if so, a
      single translation at the `_entity_dt_for_short()` call site (sports_reference_fixtures_write.py:331) is
      sufficient for that file's 2 call-site families, rather than per-call-site translation.
- [ ] [DATA] P0. **Classify `process_write.py`, `process_zero_records.py`, `process_completeness.py`,
      `process_enrichment.py`, `process_fetch.py`** (beyond the one `process_fetch.py` site already found) for sports
      19-token manifest writes — these files handle MULTIPLE asset groups via shared helpers, so each call site needs
      confirmation of whether the specific `data_type` passed is actually a sports 19-token value or a different
      asset_group's, per the same SIMPLE/ORDERED method.
- [ ] [DATA] P1. **Resolve the `TRANSFER_RECORDS` open question** (found in transfermarkt.py): is it a 20th in-scope
      token for this re-stamp, or excluded? Check
      `unified_api_contracts.canonical.domain.sports.league_data .SPORTS_DATA_TYPE_TO_SOURCE` membership and cross-check
      against the parent plan's explicit 19-token list. Escalate to the operator if ambiguous (affects re-stamp scope,
      not just this doc).
- [ ] [DATA] P0. **Once every site above is classified, author + locally validate the fix code for ALL remaining files**
      (footystats.py, sfi.py, transfermarkt.py, understat.py, weather.py, sports_reference_core.py,
      sports_reference_fixtures_write.py, and whichever `process_*.py` files todo 2 confirms) on the SAME held-back
      branch as the 4 already-fixed files
      (`instruments-service@sports-taxonomy-p2-19token-lowercase-codeprep-2026-08-14`) — commit, push to that branch, do
      NOT merge. Run `bash scripts/quality-gates.sh` (ruff + basedpyright at minimum) before each commit.
- [ ] [REVIEW] P0. **Once the full branch is complete, verify NO manifest-write call site in the sports reference-data
      path was missed** — re-run the systematic grep this doc's inventory was built from
      (`grep -rn "record_captured(\|record_failed(\|record_empty(\|record_captured_from_counts(\|record_expected_empty( \|note_empty(\|note_failed(" instruments_service/engine/orchestrator/*.py instruments_service/reference_data/ *.py`)
      against the fixed branch and confirm every 19-token site above (and any new one the grep surfaces) is accounted
      for in the diff. A partial fix that looks complete is the exact failure mode this doc exists to prevent.
- [ ] [OPERATOR] P0. **Bring the completed branch back to `sports_taxonomy_p2_migration_2026_08_08.md`'s `[OPERATOR]`
      19-token execution todo for the atomic land-and-launch decision** — this doc's job ends at a fully classified +
      coded + locally-validated branch; the actual merge + VM launch stays gated on that parent todo per BLK-0a3f3791's
      resolution (Cloud Run Job auto-deploy risk) and the parent plan's own atomicity rule.

## Progress Log

- **2026-08-14** — Authored (slot-26), per main's Option-A answer to BLK-1479b716. 4 files already fixed + pushed to
  `instruments-service@sports-taxonomy-p2-19token-lowercase-codeprep-2026-08-14` (not merged). 5 vendor files
  (footystats/sfi/transfermarkt/understat/weather) fully classified via 5 parallel Explore agents — 62 call sites total,
  57 SIMPLE + 5 ORDERED (all 5 ORDERED sites share one fix point in transfermarkt.py). `sports_reference_core.py`
  cluster + `process_fetch.py` partially classified mid-session (found via targeted reads + a raw-transcript grep, not
  yet exhaustively verified) — left as open todos rather than rushed to completion, per main's explicit reasoning that a
  session-bounded hand-patch risks silently missing a site.
