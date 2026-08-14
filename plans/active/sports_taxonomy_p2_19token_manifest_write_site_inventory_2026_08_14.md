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

### process_fetch.py (found mid-session; the other 4 `process_*.py` files remain the one open todo below)

`_per_fixture_gcs_fast_path` —
`pf_manifest.record_captured_from_counts(row_key={"date": date, "data_type": entity_name.upper()}, ..., pipeline_mode=_orch._pipeline_mode_for_sports_data_type(entity_name.upper()), ...)`
— a DYNAMIC (not literal) 19-token value (`entity_name.upper()`), ORDERED: the SAME expression is evaluated twice in one
call (row_key wants lowered, `pipeline_mode=` kwarg wants uppercase) — translate only the row_key occurrence, keep the
`pipeline_mode=` kwarg's `entity_name.upper()` untouched.

## Todos

- [x] ✅ [DATA] P0. **Finish classifying `sports_reference_core.py` in full + resolve
      `sports_reference_fixtures_write.py`'s `af_entity_dt` question.** DONE — see the "sports_reference_core.py" /
      "sports_reference_fixtures_write.py" sections above (full-file reads, every call site classified with exact line
      numbers; the `af_entity_dt` translation point is per-call-site, not upstream).
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
- **2026-08-14 (same session, follow-up)** — `sports_reference_core.py` + `sports_reference_fixtures_write.py`
  classification COMPLETED (the file-classification Explore agent finished after the entry above was written) — full
  files read, every call site classified with exact line numbers, resolving both open questions from the entry above:
  the `af_entity_dt` translation point is per-call-site (NOT upstream at `_entity_dt_for_short()`, which would have
  corrupted the `emit_empty_gaps_for_entity` passthrough's own lookups), and `emit_empty_gaps_for_entity` is confirmed
  as a 4-way cross-purpose hub needing call-site-local translation, never a parameter reassignment. See the updated
  "sports_reference_core.py" / "sports_reference_fixtures_write.py" sections above (todo 1 from the original entry is
  now folded into this doc's body, not a separate open item). Only the `process_*.py` sweep (todo below) and the
  `TRANSFER_RECORDS` scope question remain open.
