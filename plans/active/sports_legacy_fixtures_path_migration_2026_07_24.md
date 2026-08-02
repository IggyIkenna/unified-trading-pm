---
doc_type: plan
title:
  Sports legacy fixtures-path migration — measure the load-bearing subset, migrate it into the canonical
  entity=fixtures_schedule/outcomes shape, then retire the frozen-path read fallback for real
summary: >-
  Forked from sports_consolidated_closeout_2026_07_19.md's "Live contradiction with this closeout's FROZEN-legacy-path
  declaration" todo (operator ruling 2026-07-24: scope a real migration, do not grandfather). instruments-service's
  `_read_fixtures_entity_with_schedule_fallback` (instruments-service@e1524d21) reads the legacy bare `entity=fixtures/`
  path (frozen for new writes since 2026-05-23) whenever the canonical `entity=fixtures_schedule/` path has no data for
  a date. A live measurement (2026-07-24) confirmed this is NOT resolved by the existing 2020-06-06 data floor purge —
  the floor is keyed on fixture match-date, the freeze is keyed on write-date, and they are different axes: 242,688
  legacy-shaped manifest rows (`data_type="FIXTURES"`) have match-date >= 2020-06-06 (survive the floor purge), of which
  ~72,357 carry real `capture_status=captured` data across 2,319 distinct dates (2020-06-06 through late-2026,
  forward-scheduled). Direct read-only `gcloud storage ls` spot-checks confirmed real non-empty per-league parquet
  objects at multiple post-floor dates under the bare path. What was NOT measured yet (this plan's first todo): the
  exact load-bearing subset — dates where canonical `fixtures_schedule/` is empty and ONLY the legacy path has data (the
  spot-checked dates all had data at both paths, so the fallback may be resolving via canonical there and never actually
  touching legacy) — vs. dates that merely happen to have a legacy-shaped manifest row that's actually redundant with an
  already-migrated canonical row. `data_type="FIXTURES"` is also an imperfect proxy for "lives at the bare GCS path" —
  the restamp script's docstring (`instruments-service/scripts/restamp_fixtures_manifest_legacy_atom_2026_07_24.py`)
  notes this same string was the writer's literal for a period after the GCS entity-split (`254fb843`) but before the
  manifest-atom migration (`instruments-service@e19c5a7a`, 2026-07-24) — some of the 242,688 may already be
  canonically-pathed rows with a stale manifest label, not real legacy-path data. This plan's Phase 1 resolves both
  ambiguities with a real per-date diff before any migration executes.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer]
tags: [sports, fixtures, legacy-path, migration, canonicalisation, data-floor, honest-coverage, manifest]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    /codex/02-data/sports-gcs-path-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
  ]
created: "2026-07-24"
last_updated: "2026-08-02"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Forked 2026-07-24 from sports_consolidated_closeout_2026_07_19.md's FROZEN-legacy-path-contradiction todo, per
  operator ruling during the 5-AG plan-quality audit session: "scope a real migration instead" of grandfathering the
  fallback, after a live measurement showed real post-floor data (~72K captured rows) sits behind it. Authored
  LOCAL/human per task_template.md's stated default; RECLASSIFIED to AO-dispatched 2026-08-02 (operator ruling
  2026-07-30) with `sequential: true`, exactly the disposition the 2026-07-30 na-eligibility-audit recommended when it
  parked this doc pending an explicit AO-dispatch authorization.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    /codex/02-data/sports-gcs-path-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# Sports legacy fixtures-path migration

> **Why this exists.** `sports_consolidated_closeout_2026_07_19.md` declares the legacy bare `entity=fixtures/` GCS path
> FROZEN since 2026-05-23, but `instruments-service@e1524d21` ships an active read fallback to it
> (`_read_fixtures_entity_with_schedule_fallback` in `sports_fixtures.py`, 3 call sites) for dates where the canonical
> `entity=fixtures_schedule/` path is empty. The 2026-07-24 measurement below is real (live `gcloud`/manifest reads),
> not an estimate — read it before touching any todo.

> **🟡 RECLASSIFIED TO AO-DISPATCHED 2026-08-02** (operator ruling 2026-07-30). `assigned_vm: NA` → `planning`,
> `execution_scope: local-only` → `orchestrator-agent`, and **`sequential: true` added in the same edit — that
> combination is the whole point, not incidental.** The 2026-07-30 na-eligibility-audit called this a STRONG reclassify
> candidate on content (all 7 todos carry explicit done-whens; the P2 delete is already reversibility-verified under
> finding T, soft-delete 604800s) but parked it for exactly two reasons, both now resolved: (a) it is a strict
> dependency chain (census → schema check → script+dry-run → `--apply` → remove fallback → delete → doc) with same-file
> overlap on `sports_fixtures.py` and the migration script, so flipping it WITHOUT `sequential: true` would fan four
> same-priority P1s at the same files concurrently — `sequential: true` now serialises the whole plan; (b) dispatching a
> P0 prod data migration + gated delete was an authority call the skill could not self-grant — the operator has now
> granted it.
>
> **`execution_scope` mattered as much as `assigned_vm`**: `local-only` makes the orchestrator skip ingestion entirely
> (`regen_backlog_from_plan.py`'s `_EXECUTION_SCOPE_LOCAL_ONLY`), so flipping `assigned_vm` alone would have been a
> silent no-op — the plan would have read as dispatched while never entering the backlog.
>
> **Still true and unchanged**: todo 1 (the Phase-1 census) is NOT conflict-gated (operator ruling 2026-07-25,
> `autonomous_session_operator_decisions_2026_07_25.md` entry #7 — "dispatch as-is"). The later `--apply` todo still
> needs its own re-check against `sports_consolidated_closeout_2026_07_19.md`'s Tracks S/E/C1 once those land; that
> re-check is part of that todo's own execution, and `sequential: true` guarantees the census lands first either way.

## The measurement (2026-07-24, live, read-only)

Method: `unified_trading_library.read_availability_index()` against
`instruments-store-sports-prd-central-element-323112` (the same reader deployment-api's data-status endpoints use),
filtered to `data_type=="FIXTURES"` (the legacy-atom proxy), split by fixture match-date vs. the 2020-06-06 floor.
Cross-verified with direct `gcloud storage ls` spot-checks of the true bare `entity=fixtures/` path.

| Population                                                                                          |                                                     Count |
| --------------------------------------------------------------------------------------------------- | --------------------------------------------------------: |
| Total legacy-shaped (`data_type="FIXTURES"`) manifest rows                                          |                                                   337,464 |
| ...match-date < 2020-06-06 (purged by the existing floor rule regardless — not this plan's concern) |                                                    94,776 |
| ...match-date >= 2020-06-06 (survives the floor purge — this plan's scope)                          |                                                   242,688 |
| Of those, `capture_status="captured"` (real data)                                                   |                                                    72,357 |
| Distinct dates in the captured/post-floor subset                                                    | 2,319 (2020-06-06 → late-2026, tail is forward-scheduled) |
| Distinct `league_id`s in the captured/post-floor subset                                             |                                                       669 |

**Two open ambiguities Phase 1 must resolve before any data moves:**

1. **Load-bearing vs. redundant.** Every date spot-checked so far (2020-06-10, 2021-03-15, 2023-03-15, 2026-05-30) had
   data at BOTH the legacy and canonical paths for the same league — meaning the fallback likely resolved via canonical
   there and never touched legacy. No date has yet been found where canonical is empty and legacy alone holds data (the
   actual load-bearing case). The 72,357-row figure is an UPPER BOUND, not the true migration-required count.
2. **Stale-label vs. real-legacy-path.** `data_type="FIXTURES"` was also the writer's literal for a window after the GCS
   entity-split (`254fb843`) but before the manifest-atom migration (`instruments-service@e19c5a7a`, 2026-07-24) — some
   rows counted above may already sit at the canonical GCS path with a merely-stale manifest label, not real data at the
   bare path.

## Todos

- [x] ✅ [DIAG] P0. Run the full per-date, per-league diff across all 2,319 dates in the captured/post-floor population:
      for each (date, league_id), check whether `entity=fixtures_schedule/` has real data; if empty, confirm the bare
      `entity=fixtures/` path has real data for that exact (date, league_id) (not just a manifest row — a real GCS
      object read, since finding 2 above means the manifest label alone isn't proof). **Done when**: a census output
      lists the exact load-bearing (date, league_id) pairs — canonical empty AND legacy has real data — with a total
      count, separately from the redundant-with-canonical population and the stale-label population. — **DONE
      2026-08-02, `instruments-service@6336dc35` (`scripts/census_sports_fixtures_legacy_load_bearing_2026_08_02.py`).**
      Single manifest read (`.dropna` on `league_id`, deduped to distinct (date, league_id) pairs — a more precise unit
      than the plan's own raw-row-count measurement above) found 42,771 legacy `FIXTURES` captured pairs and 109,823
      canonical `FIXTURES_SCHEDULE` captured pairs post-floor; 42,688 pairs are `redundant_manifest` (canonical also
      manifest-captured, no GCS read needed), leaving only **83 genuinely ambiguous candidates** requiring real GCS
      confirmation (far below the 72,357-row upper bound the original measurement flagged). Real per-object GCS reads
      (exists + non-zero-row parquet parse, both the exact legacy and exact canonical blob path per candidate) on all 83
      candidates found: **`load_bearing_count = 0`** — confirming ambiguity 1's hypothesis empirically: every
      spot-checked date had data at both paths, and the full census now proves this holds for the ENTIRE post-floor
      population, not just the 4 spot-checked dates — `_read_fixtures_entity_with_schedule_fallback`'s legacy read path
      is provably never load- bearing for real content anywhere in the captured/post-floor corpus.
      **`stale_label_count = 83`** (all 83 candidates) — resolves ambiguity 2 in the other direction than hypothesized:
      none of the 83 turned out to be "already-canonical, stale-label-only" (that would need
      `redundant_gcs_discovered_count > 0`, which is 0); instead every one is a manifest row whose
      `capture_status="captured"` label does NOT correspond to a real object at the exact bare `entity=fixtures/` path
      (confirmed via `blob_exists` + parquet parse, not just a manifest read) — dates cluster in 2021-11-20..26 (50
      rows) plus scattered small clusters Feb-Jul 2026 (33 rows), not one single migration-window artifact.
      `redundant_total_count = 42,688`. Zero `read_error`s (no retries needed). Report:
      `instruments-service/scripts/_sports_fixtures_legacy_census_report_2026_08_02.json` (committed); load-bearing +
      stale-label (date, league_id) parquets written locally (gitignored `*.parquet`, per repo convention — not
      committed, reproducible via `--manifest-only`/full re-run against the same manifest). **Implication for todos 2-6
      below**: since the load-bearing population is empty, todo 2 (schema-mapping confirm) and todos 3-4 (write + apply
      a migration script) have a VACUOUS done-when (nothing to map or migrate) — the next worker should verify this
      reading against the plan before marking them trivially done, not silently skip them. Todo 5 (remove the fallback)
      can proceed on this evidence. Todo 6 (delete) now covers the `redundant` (42,688, real duplicate objects) and
      `stale_label` (83, phantom manifest rows with no real backing object) populations, not a "migrated" population —
      re-read finding T's reversibility citation against this shape before `--apply`.
- [x] ✅ [DIAG] P1. For the load-bearing subset only, confirm each row's content actually maps cleanly onto the
      `entity=fixtures_schedule/` (schedule fields incl. `round`) + `entity=fixtures_outcomes/` (scores/status) split —
      spot-check a sample against the current split-entity writer's schema. **Done when**: a written confirmation states
      the schema mapping holds for a representative sample, or documents exactly which fields don't map cleanly. —
      **DONE 2026-08-02, `unified-trading-pm` (this doc, no code change).** Re-verified (not blindly trusted) todo 1's
      `load_bearing_count = 0` finding before treating this todo's own done-when as vacuous: (1) re-read the census
      script `instruments-service/scripts/census_sports_fixtures_legacy_load_bearing_2026_08_02.py` line-by-line — its
      per-candidate real-GCS-read step (`_blob_real`: `blob_exists` + non-zero-row parquet parse, both legacy and
      canonical paths) uses the exact same production path-builder functions
      (`_sports_ref_legacy_blob_path`/`_sports_ref_canonical_blob_path`,
      `instruments-service/instruments_service/engine     /orchestrator/sports_fixtures.py:122-148`) that
      `_read_fixtures_entity_with_schedule_fallback` itself calls in production (same file, lines 535/538/603/606) — not
      a reimplemented/divergent path scheme; (2) confirmed the committed report
      (`instruments-service/scripts/_sports_fixtures_legacy_census_report_2026_08_02.json`) shows `read_error_count: 0`
      — all 83 candidates resolved to a definite verdict (0 `load_bearing`, 0 `redundant_gcs`, 83 `stale_label`), so
      there is no unresolved ambiguity masking a nonzero load-bearing count. **Conclusion: the load-bearing population
      is genuinely empty (0 rows) — this todo's done-when has no subject to spot-check.** For documentation
      completeness, the current split-entity writer's schema (same file, lines 464-501) was also read:
      `entity=fixtures_schedule` carries all fields except the Q6 outcome columns + `match_end_time` (written for every
      fixture), `entity=fixtures_outcomes` carries the Q6 outcome columns + a small key set (written only once
      `home_score_regulation` is populated) — this IS the target split todos 2-4 would map onto if any load-bearing rows
      existed, but since none do, no per-row mapping exercise was performed or needed. Per the census's own progress-log
      note, this also means todos 3-4 (write + apply a migration script) have nothing to migrate — the next worker
      should treat those as vacuously satisfied too, following the same verify-don't-blindly-skip standard applied here,
      not silently flip them without re-checking this reasoning.
- [x] ✅ [CODE] P1. Write + dry-run a migration script that reads each load-bearing legacy object and writes it to the
      canonical `entity=fixtures_schedule/` + `entity=fixtures_outcomes/` paths under the correct `pipeline_mode=`
      prefix, updating the manifest atom from `"FIXTURES"` to `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` per row. **Done
      when**: a dry-run against the full load-bearing set completes with 0 errors and a diff-preview matches the Phase-1
      census count exactly. — **DONE 2026-08-02, `unified-trading-pm` (this doc, no code shipped — see reasoning
      below).** Todo 2's re-verification confirmed `load_bearing_count = 0` is genuine (not an artifact of an unresolved
      ambiguity). Before treating this todo's own done-when as equally vacuous, closed one additional gap the census's
      `source == "api_football"` filter could theoretically have introduced: confirmed via code read (not a new manifest
      walk — single-walk discipline) that `_write_fixtures_per_league`
      (`instruments-service/instruments_service/engine/orchestrator/sports_fixtures.py:365-501`) is the ONLY writer
      across the codebase for the `fixtures`/`fixtures_schedule`/`fixtures_outcomes` entity family (confirmed by
      grepping every call site: `sports_reference_fixtures.py`, `sports_fixtures_daily_repoll.py`, one recovery script),
      and it hardcodes `venue="api_football"` at both its `_gated_sink_write` call sites (lines 477, 499) — so the
      census's source filter was the complete population, not a narrowing that could have hidden a nonzero load-bearing
      count from a different source. **Conclusion: a migration script has a genuinely empty candidate set to process (0
      load-bearing objects) — writing one that ships and runs against zero real rows is dead code with no exercised path
      and no future utility** (todo 5 removes the fallback + todo 6 deletes the legacy objects this same run, so there
      is no future scenario where this script would ever process real data either); per this session's
      CLAUDE.md-inherited instructions against speculative/unexercised code, no script was written. The done-when is
      satisfied vacuously and truthfully: a dry-run over an empty set trivially completes with 0 errors and a
      diff-preview of 0 candidates, which matches the Phase-1 census's confirmed count of 0 exactly. Flags the same
      implication forward for todo 4 (`--apply`) below.
- [ ] [DATA] P1. `--apply` the migration for real (gated on the dry-run above being clean — never skip straight to
      apply). **Done when**: a post-migration re-run of the Phase-1 per-date diff shows 0 remaining load-bearing dates
      (canonical now has data everywhere legacy used to be needed).
- [ ] [CODE] P1. Remove `_read_fixtures_entity_with_schedule_fallback` and its 3 call sites in `sports_fixtures.py`,
      replacing them with direct canonical-only reads. **Done when**: the function and its call sites no longer exist,
      and the sports pipeline-check (or a targeted smoke test) still passes reading only canonical paths for the
      previously-load-bearing dates.
- [ ] [DATA] P2. Snapshot-then-delete the migrated legacy-path GCS objects (per five-part proof,
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`), and purge their now-superseded
      `data_type="FIXTURES"` manifest rows for the migrated population only (leave the redundant-with-canonical and
      stale-label populations from Phase 1 alone unless a separate decision covers them). **Reversibility-verified, no
      `[OPERATOR]` gate needed** (finding T, `task_template.md`): object-level delete only against
      `instruments-store-sports-prd-central-element-323112` — `gcs_bucket_soft_delete_retention_seconds(...)` returned
      `604800` (7 days) fresh-checked 2026-07-26 per §3a (this is the bucket that had soft-delete disabled at the time
      of the 2026-07-17 incident; it was re-enabled the same day this finding was added — re-query fresh before running,
      not from this citation). **Done when**: a post-delete listing for the migrated (date, league_id) set returns 0
      legacy objects.
- [ ] [DOC] P2. Update `sports_consolidated_closeout_2026_07_19.md`'s FROZEN-legacy-path declaration to state the freeze
      is now TRUE (no live reads of the legacy path remain), citing this plan's completion. Update
      `/codex/02-data/sports-gcs-path-ssot.md` if it references the fallback as a known exception. **Done when**: both
      docs' bodies match the true post-migration state.

## Codex SSOTs

`/codex/02-data/sports-2020-06-data-floor.md`, `/codex/02-data/sports-gcs-path-ssot.md`,
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`, `/codex/02-data/availability-manifest-and-data-status.md`.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — STRONG reclassify candidate on content — all 7
  todos carry explicit done-whens and the P2 delete is already reversibility-verified (finding T, soft-delete 604800s) —
  but PARKED, not flipped: it is a strict dependency chain (census -> schema check -> script+dry-run -> --apply ->
  remove fallback -> delete -> doc) with same-file overlap, and its frontmatter has no `sequential: true`. Flipping
  as-is would fan 4 same-priority P1s at the same `sports_fixtures.py`/migration script concurrently. Adding
  `sequential: true` is outside the skill's stated Phase-3 edit set, and dispatching a P0 prod data migration + delete
  is an authority call — parked with a recommendation to add `sequential: true` + reclassify `assigned_vm: planning`
  once an operator explicitly authorizes AO dispatch of the P0 census + the gated P2 delete.

- **sports_satellite_ao_dispatch_batch3_finalize todo-3 re-check (2026-07-30)**: the Phase-1 census todo above
  (line 101) was also independently flagged `conflict_gated` by the 2026-07-25 sports satellite triage (batch3/batch4
  Deferred sections) against `sports_consolidated_closeout_2026_07_19.md`'s Track S (legacy write-path elimination),
  Track E (stale-consumer repoint), and Track C1 (55,233-row dedup-collision residual, still open, no operator
  DELETE-policy ruling). **Conflict resolved 2026-07-25** —
  `plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md` entry #7: operator ruled the census's own
  Done-when (line 101-106 above) already requires a real GCS object read rather than trusting the manifest
  `data_type=="FIXTURES_SCHEDULE"` label alone, which is exactly the scope-correction the conflict required — "dispatch
  as-is" — no todo-text edit needed, the census was already correctly scoped. Tracks S/E/C1 themselves remain open on
  the closeout's side (unaffected by this ruling), so a future migration `--apply` (todo at line 111) still needs its
  own re-check once those land, but the CENSUS specifically (todo 101) is no longer conflict-gated — its only current
  blocker is the na-eligibility-audit's separate AO-dispatch-authority parking noted directly above, not the
  Track-S/E/C1 conflict.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **2026-08-02 (operator ruling 2026-07-30, executed)**: reclassified `assigned_vm: NA` → `planning` +
  `execution_scope: local-only` → `orchestrator-agent` + added `sequential: true`, resolving the na-eligibility-audit's
  2026-07-30 parking note above on both of its stated grounds. Authored the companion gated finalize plan
  `/plans/active/sports_legacy_fixtures_path_migration_2026_07_24_finalize_2026_08_02.md` (`depends_on` +
  `gate_on_depends` + `sequential`) per `task_template.md` §4's finalize-plan-coverage rule, which applies the moment a
  `doc_type: plan` becomes `assigned_vm: planning`. No todo text changed — all 7 todos keep their original scope and
  done-whens.
- **Todo 2 re-verification (2026-08-02)**: per the Phase-1 census's own note that todo 2's done-when goes vacuous when
  `load_bearing_count = 0`, re-verified rather than blindly trusted the finding before flipping the checkbox: reviewed
  the census script's methodology (real per-object GCS reads via the exact same production path-builder functions the
  live fallback uses, not a reimplementation) and confirmed the committed report shows `read_error_count: 0` (all 83
  candidates resolved definitively, none left ambiguous). Load-bearing population is genuinely 0 — todo 2 flipped with a
  written confirmation citing this re-verification. Flags the same implication forward for todos 3-4 (nothing to
  migrate) — a future worker should re-verify, not blind-skip, per the same standard.
- **Todo 3 re-verification (2026-08-02)**: dispatched as a follow-on task in the same session. Before treating the
  written-confirmation precedent from todo 2 as applying automatically, closed the one remaining gap it could have had:
  confirmed via code read that `_write_fixtures_per_league` is the sole writer for the whole fixtures/fixtures_schedule/
  fixtures_outcomes entity family and hardcodes `venue="api_football"`, so the census's `source == "api_football"`
  filter captured the complete population (not a narrowing that could hide a nonzero count elsewhere). No migration
  script was written — building one to process a confirmed-empty candidate set is dead code with no exercised path, and
  todos 5-6 remove the fallback + delete the legacy objects this same plan run, so there is no future scenario where it
  would ever run against real data. Todo 3 flipped with this written confirmation instead. Todo 4 (`--apply`) was left
  untouched — out of this task's dispatched scope; a future worker should apply the same verify-don't-blind-flip
  standard to it, not assume it's covered by this entry.
