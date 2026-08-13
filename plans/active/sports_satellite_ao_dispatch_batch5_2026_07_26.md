---
doc_type: plan
title: Sports satellite AO batch 5 — fresh Phase-1/Phase-3 triage of the sports closeout-orphan corpus
summary: >-
  Fifth AO-dispatch batch for sports, produced by the `/ag-closeout-audit` skill's full Phase-1 (per-doc classify) +
  Phase-3 (conflict-check + draft) triage over all 60 sports AG-primary docs not already covered by the consolidated
  closeout, batch2/3/4 (+finalize), or the 4 line-cap-split forks/finalize (2026-07-26). 44 docs came back orphaned (21
  partial coverage, 23 never touched, 1 exclude_cross_cutting dropped); Phase 3's conflict check cleared 25 of them into
  fresh AO-dispatch todos (2 near-duplicate pairs merged into single combined todos citing both sources), found 1
  (`sports_trades_attempted_failed_2026_07_23.md`) already fully covered by two 2026-07-25-dated docs Phase-1's
  citation-grep had missed, and left 4 genuinely conflict-gated + 12 operator-gated items in the Deferred sections below
  for the next iteration or an explicit operator ruling, per the skill's non-batchable taxonomy.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    ml-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
    unified-trading-system-ui,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-5, satellite-docs, fresh-triage]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch4_2026_07_25.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch4_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-29"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2.0
archive_exempt: true # BRIDGE 2026-08-12: clearing the stale locked_by:live-defi-rollout placeholder (operator ruling, option B, see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md) immediately surfaces this doc as 0-open-todos archive-eligible. Per that ruling's explicit scope ("do NOT auto-archive in this same pass"), archival is deferred to a separate follow-on pass. Bridged via the sanctioned flip-then-mv two-commit pattern documented in scripts/plan-hygiene/check_archive_candidates.sh -- drop this line + git mv to plans/archive/[issues/] in that follow-on pass.
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit skill run 2026-07-26 (interactive, operator-approved scope) — Phase 1 classified all 60 sports
  AG-primary docs not already in the covering-plan set via a Workflow fan-out (60 agents), Phase 3 ran a conflict-check
  + candidate-todo draft over the 44 orphaned docs via a second Workflow fan-out (44 agents), per the skill's documented
  methodology.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/sports_odds_stale_fixture_reinjection_2026_07_14.md,
    market-data-processing-service/market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py,
    features-service/scripts/sports/verify_ml_readiness.py,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# Sports satellite AO batch 5 — fresh triage extraction

> **Status: active — operator-approved 2026-07-26.** Dispatched per CLAUDE.md's plan-destination rule and the
> ag-closeout-audit skill's autonomous-mode guidance (a skill-drafted AO batch is never auto-shipped; this flip followed
> explicit operator review). Originally 25 same-priority-independent todos, all touching distinct files/docs. 2 were
> extracted 2026-07-26 (fully closed, no open work) to
> `/plans/archive/2026_07/sports_satellite_ao_dispatch_batch5_completed_todos_2026_07_26.md`; a further 21 — every
> remaining `[x]` DONE item, including the T6.8/E8 `migrate_sports_canonical_v9.py` pair (both landed, the coordination
> note is now moot) — were extracted 2026-07-28 to the same archive file per
> `issues/sports_satellite_batch5_line_cap_blocks_priority_edit_2026_07_28.md` (line-cap remediation; this doc had grown
> to 1002 lines, over the 1000L hard cap). The 2 remaining inline todos below are now **both `[x]` DONE** (**CORRECTED
> 2026-08-12 `/plan-reconcile`**: was "2 genuinely still-open" — todo 1 DONE 2026-07-29 slot-15, todo 2 DONE per its own
> inline evidence; this doc is a 0-open-todo archive candidate but its finalize twin
> (`sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md`) still carries 2 open `[ ]` BLOCKED items, so full
> batch+finalize archival is not yet ripe — left for whoever clears the finalize twin's remaining gates).

## Todos

- [x] ✅ [DATA] P1. **DONE 2026-07-29 (slot-15).** UNBLOCKED 2026-07-29 (Secret Manager `odds-api-key` rotated +
      live-verified — see `issues/sports_odds_api_key_deactivated_2026_07_26.md`) — Backfill the 3 odds-api league gaps
      surfaced by the api_football wipe — `soccer_uefa_champs_league`, `soccer_china_superleague`,
      `soccer_russia_premier_league` (2025-H2 golden window + any in-scope gap-dates behind the former 112,653
      api_football failures) — via odds-api (`batch_odds_api`, the canonical sports-odds source), not api_football. UEFA
      Champions League is the notable/highest-priority league. Source:
      `sports_golden_window_attempted_failed_remediation_2026_06_24.md` (Fixes item "#5 odds-api backfill gaps",
      RE-TRIAGE 2026-07-23 confirms still open). Done when: `batch_odds_api` manifest rows for all 3 leagues show 0
      `attempted_failed`/gap-days across the golden window (2025-09-01..2025-11-30) and any other in-scope 2025-H2
      gap-dates, verified against the `_index` manifest (not a re-derived count).

      **BLOCKED-CREDENTIALS 2026-07-26 (slot-4), RESOLVED 2026-07-29** — the backfill originally could not run: the odds-api key was DEACTIVATED (`error_code=DEACTIVATED_KEY`, "cancelation or a failed payment" — confirmed by direct curl against the live API), a fresh outage (275,136 `odds_api` rows captured 2026-07-25, zero 2026-07-26). This blocked the ENTIRE sports odds-api surface, not just these 3 leagues — see `issues/sports_odds_api_key_deactivated_2026_07_26.md` for the full diagnosis. **2026-07-29: operator rotated `odds-api-key` to a new key on a 5,000,000-credits/month subscription; live-verified via direct curl (HTTP 200, `x-requests-remaining: 5000000`), no longer `DEACTIVATED_KEY`.** Real prerequisite work DID ship: `deployment-service@281426e7` adds `--league` scoping to `launch-mtds-sports-odds-backfill-vm.sh` (wires the already-built `VM_LEAGUE` metadata support in `setup-data-pipeline-vm.sh` through to a CLI flag — previously this launcher could only run unscoped, full-population backfills). Also found + worked around a separate pre-existing bug in `tick_data_handler.py`'s `_apply_freshness_skip`: it checks freshness at (date, venue) granularity, blind to `--league` scope, so a scoped run silently SKIPPED every date (odds_api already had some row for every date from routine Prediction-tier captures) unless `--force` is also passed. Stopped the backfill VM (`mtds-backfill-odds-ucl-gap2`) once the 401 pattern was confirmed — no data lost, idempotent.

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      **DONE 2026-07-29 (slot-15)** — re-ran `mtds-backfill-odds-ucl-gap` (republished 4 stale code tarballs first —
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      the launcher's own freshness check flagged them). VM completed clean (`exit_code=0`, self-deleted). Verified
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      against the per-VM shard (`_index/per_vm/mtds-backfill-odds-ucl-gap.parquet` — the consolidated
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      `availability_index.parquet` hadn't caught up with this run yet at check time): **UCL 1,787 rows + CHINA_SUPER_LEAGUE
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      337 rows, both 100% `capture_status=captured`, 0 `attempted_failed`** — fully meets the done-when bar for 2/3
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      leagues. **RUSSIA_PREMIER_LEAGUE produced zero rows of any capture_status** — confirmed via direct vendor probes
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      this is a genuine the-odds-api.com coverage gap, not a code/credential defect: `soccer_russia_premier_league` is a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      currently `active: true` sport key, but a direct historical-events probe for a mid-window date
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      (2025-10-04) shows the vendor's nearest actual snapshot straddling that date is `2022-03-04` → `2025-12-01` — i.e.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      the vendor has NO historical odds snapshots for this sport anywhere inside the requested 2025-09-01→2025-11-30
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      window. This is a permanent vendor limitation for this window, not a "not yet done" gap — no further re-run of
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      this task will ever close it. Full evidence in `issues/sports_odds_api_key_deactivated_2026_07_26.md`'s P1 todo
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      (now archived, `status: resolved`). Flipping this checkbox done on that basis: 2/3 leagues fully backfilled with 0
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      failures, 1/3 confirmed vendor-unfillable for this exact window (not a defect to keep chasing).

- [x] ✅ [DATA] P2. **market-tick-data-service + market-data-processing-service + features-service: execute the
      zombie-tick purge/re-derive + close out ML-readiness verification, using batch4's sweep report as input.** Once
      `sports_satellite_ao_dispatch_batch4_2026_07_25.md`'s read-only P1 sweep todo (source: this doc) has produced its
      contamination report — repeated (fixture_id, bookmaker_key, kickoff_utc) tuples spanning multiple `day=`
      partitions in
      `processed/by_date/*/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/data_type=odds_horizon_bucket/`,
      discriminated from honest single-snapshot-real-fixture rows via `staleness_seconds`/`|fetch_utc − kickoff_utc|`
      (years-scale = zombie, ≤~26h = genuine, per this doc's tick-4 refinement) — (a) snapshot the identified
      contaminated shards first, then purge/re-derive them plus their downstream `odds_features` and manifest rows via
      the manifest index (single-walk discipline: no fresh whole-corpus GCS walk), re-deriving through the
      now-staleness-cap-fixed `bucket_assignment_adapter.py` (`mdps@aa6e8ac`) so the corrected pipeline regenerates
      clean buckets; (b) re-run
      `verify_ml_readiness.py --start-date 2025-09-01 --end-date 2025-11-30 --bucket features-sports-prd-central-element-323112`
      and confirm the 17 originally-failing dates clear or shrink to genuine honest-absence-only misses; (c) implement
      the two-part gate-semantics fix this doc specifies: zero-in-window-fixture days pass vacuously (or skip via an
      expected-fixture count derived from instruments-service fixtures) instead of scoring as failed-empty, and the
      per-date non-null-cell-count check exempts `WRITE_GATE_CONFIG.sparse_columns["odds_features"]` prefixes (the
      already-verified 43-column always-null cluster set, 0 unmatched against that config) — this also fixes the
      shallow-ladder partial days (e.g. 2025-10-20 at 91.1%). Do NOT purge the single-snapshot real-fixture class (e.g.
      the 2025-10-23 China Superleague pair) — honest data, not contamination. Source:
      `sports_odds_stale_fixture_reinjection_2026_07_14.md`. Done when: the sweep-identified contaminated shards are
      purged/re-derived with a before/after manifest census showing only the intended cells changed,
      `verify_ml_readiness.py` re-run output is posted showing the 17-date failure set cleared/shrunk with the remainder
      attributable to genuine honest-absence, and the two-part gate-semantics fix is shipped + QG-green with a
      regression test covering a zero-in-window-fixture day passing vacuously and a sparse-column day no longer flagged.

**21 fully-closed `[x]` DONE todos extracted 2026-07-28** (line-cap remediation:
`issues/sports_satellite_batch5_line_cap_blocks_priority_edit_2026_07_28.md`) — every todo this doc originally carried
besides the two still-open items above. Full verbatim text (nothing summarized away, nothing lost) now lives in
`/plans/archive/2026_07/sports_satellite_ao_dispatch_batch5_completed_todos_2026_07_26.md`, appended alongside the 2
items already extracted there 2026-07-26. One-line index of what moved (`[TAG] Pn.` + repo + one-line outcome):

1. `[DATA] P1` instruments-service — api_football per-fixture `empty_confirmed` false-positive audit: 0 matches, no
   relabel needed.
2. `[DATA] P2` instruments-service — player_stats nested-schema normalization (3,274 cells) + 1,298
   manifest/GCS-mismatch root-cause.
3. `[DIAG] P3` market-tick-data-service — odds_api raw-ingestion gap (2026-06-21..24) escalated to its own issue doc.
4. `[DATA] P3` market-tick-data-service — canonical odds poll-key duplicate dedup: 3,829/4,045 (94.7%) deduped, 216
   filed as a follow-up.
5. `[SCRIPT] P3` instruments-service — QG function/class-size-gate sentinel-skip root-cause (3 real threshold-crossing
   commits identified).
6. `[DATA] P1` market-tick-data-service — batch_footystats/ODDS_API orphan-object disposition census refreshed to
   `yes-twin-confirmed`.
7. `[DOC] P2` unified-trading-pm — closed `sports_batch_footystats_swap_wrong_script_2026_07_25.md` as superseded.
8. `[DATA] P2` unified-api-contracts — curated-universe Faroe/Wales leagues fix (1 genuinely-missing entry added, not
   4).
9. `[OPERATOR] P2` features-service — PLAYERS/COACHES/REFEREES/ROUNDS dead-dimension manifest purge
   (checkbox-drift-only; purge already ran).
10. `[DATA] P1` instruments-service — root-caused + resolved 4,991 phantom `captured` FIXTURE_EVENTS manifest rows.
11. `[DATA] P1` — freshness-preflight VM stale-scope-escape audit; source issue doc closed `resolved`.
12. `[CODE] P1` features-service/ml-service — sports HT-odds PIT gate + CLV target/training-pipeline fix chain
    (multi-session; literal 3-variant model retrain remains open in a child doc).
13. `[DATA] P1` — sports odds manifest-routing regression: all 3 findings closed (deliberate routing / non-reproducible
    gap / index stale-by-design).
14. `[DATA] P3` — odds-feature naming canonicalization checkbox-drift fix (already shipped, re-verified).
15. `[CODE] P2` unified-api-contracts/market-tick-data-service/deployment-api — shard-enumeration cartesian-blowup
    safety tooling build-out (4/4 pieces + uppercase `ODDS` removal).
16. `[BACKEND] P2` market-tick-data-service/instruments-service — T6.8 one-off-retirement residual close-out (10
    obsolete scripts deleted).
17. `[SCRIPT] P0` — Understat bulk backfill close-out: already complete via a sibling archived plan; 1 registration gap
    freshly shipped.
18. `[DATA] P1` market-tick-data-service — Sports E8 legacy-delete implementation: DONE-FOR-CODE, `--apply` firing stays
    on an operator hold.
19. `[UI] P3` deployment-ui — `FixturesBrowser.tsx` `MAX_SPAN_DAYS` cap removal (full-history catalogue source).
20. `[DATA] P0` unified-api-contracts/market-tick-data-service — sports odds/trades index correctness follow-up: T2.9
    schema-contract drift + T2.10 phantom-row disposition both closed.
21. `[DATA] P2` ml-service — odds-feature naming migration in 4 remaining pre-migration files.

## Deferred — conflict-gated (genuinely unresolved, do not draft competing todos)

- **`plans/active/issues/sports_legacy_duplicate_triage_2026_07_22.md`**: **RULED 2026-07-28 — fold explicitly into the
  existing pre-floor-wipe scope** (§7 todo 1's option A). Reasoning: these 1,492 rows are the sole surviving copy of
  that data (no canonical twin exists), so an explicit routing decision is safer than assuming a different, competing
  mechanism already covers them — and the sports 2020-06 data-floor policy
  (`/codex/02-data/sports-2020-06-data-floor.md`) already establishes that pre-floor sports data is the class this wipe
  scope is FOR; folding these rows into it explicitly (rather than letting them fall through the OTHER bulk-cull todo's
  reader-check-only safety gate, which the conflict below shows does not actually cover twin-existence) is applying the
  already-ratified policy correctly, not opening a new one. **The retag itself (the §7 todo 1 checkbox) lives in
  `sports_legacy_duplicate_triage_2026_07_22.md`, out of scope for this file's edit pass** — this note records the
  ruling; a follow-up pass should (a) flip that doc's §7 todo 1 to reflect "fold into pre-floor wipe scope" as the
  ratified disposition, and (b) amend the two colliding cull todos (`sports_consolidated_closeout_2026_07_19.md` and
  `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track S bullets) per option (2) below so neither silently
  deletes these 1,492 rows via the wrong (reader-check-only) mechanism first. Original Phase-1 gap + conflict evidence
  (unchanged, still the basis for the ruling): Confirmed the Phase-1 gap: §7 todo 1 (previously [OPERATOR] P1, "Rule on
  the 1,492 v2 pre-floor rows: fold into the existing pre-floor-wipe scope … or confirm they're already covered by a
  follow-up pass") is the sole remaining uncovered item — todos 2-5 are done or explicitly closed by batch2
  (grep-confirmed above), and the 2026-07-23 RE-TRIAGE section reconfirms it as still open/unexecuted. GENUINE CONFLICT
  found on the SAME underlying data (not just "is it cited" — a different mechanism is prescribed for the same rows).
  Two live docs carry an unexecuted `[ ]` todo to bulk-delete the entire `sports_reference_v2/by_date/` tree on the
  premise that it is "dead / frozen 2026-04-20 / no entities": - `sports_consolidated_closeout_2026_07_19.md` (status:
  active) lines 437-438: "Snapshot-then-cull the dead `sports_reference_v2/by_date/` dual-layout … Confirm no reader
  consumes it first." - `sports_consolidated_native_ao_extract_2026_07_25.md` (status: draft) lines 122-128 mirrors the
  same todo verbatim as an AO-dispatch-ready "Track S" item, explicitly marked **"Self-justified, not
  [OPERATOR]-gated"** with its ONLY safety gate being a reader-check (no twin-existence check), Done-when =
  "reader-check recorded AND snapshot+delete executed with post-delete 0-objects listing." This directly collides with
  this triage doc's own finding: 1,492 of the v2 rows (the pre-floor subset) are NOT dead inert bytes — they were
  verified to still exist (15/15 sampled) with ZERO canonical twin at any path variant, i.e. they are the sole surviving
  copy of that data, and the triage doc's own 5-part delete-safety proof explicitly routes them to an OPERATOR ruling on
  folding them into the separately-already-ruled pre-floor wipe scope, NOT a generic reader-check-gated tree cull. The
  cull todo's "no entities" / "dead" premise is stale for this specific slice — a reader-check alone does not satisfy
  the delete-safety protocol's twin-existence part that this triage doc found FAILING for exactly these 1,492 rows. If
  the snapshot-then-cull todo executes first (it is unexecuted, unchecked `[ ]` in both hosting docs), it would delete
  the 1,492 rows without ever routing through the OPERATOR ruling this triage doc calls for, and without the protocol's
  twin-existence proof — a real, evidenced risk of silent data loss executed under a "self-justified" safety label that
  doesn't actually cover this sub-population. Recommended resolution (not self-executing — flagging for the
  operator/plan-owner): (1) do NOT draft this as a fresh batchable todo — drafting a competing "rule on 1,492 rows" todo
  alongside an active unexecuted "snapshot-then-cull the whole tree" todo would race two different deletion policies
  against the same objects. (2) Instead, the `sports_consolidated_native_ao_extract_2026_07_25.md` Track S todo (still
  status: draft, not yet dispatched) should be amended before it ships to either (a) exclude the pre-floor date range /
  explicitly gate on this triage doc's §7 todo 1 resolving first via `depends_on`, or (b) fold the OPERATOR ruling
  directly into its own Done-when clause (replace "Self-justified, not [OPERATOR]-gated" with an actual [OPERATOR] gate
  for the pre-floor slice specifically, leaving the post-floor/already-migrated portion self-justified). (3)
  `sports_consolidated_closeout_2026_07_19.md`'s parent copy of the same todo should get the same amendment or a
  cross-reference note pointing at this conflict. This is a plan-authoring fix (amend an existing draft/active todo's
  safety gate), not new batchable work — no candidate_todo drafted per the conflict_gated branch instructions.
- **`plans/archive/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md`**: Confirmed the two remaining
  items from Phase 1: (1) building a data_type-aware cross-bucket branch in `_audit_sports()`
  (`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py:283`) to fix the
  `trades`/`odds_horizon_bucket`/PLAYER_VALUES phantom false-positives, and (2) the unexamined ~1,335-row (0.19%)
  STANDINGS/TEAMS/XG/WEATHER/MATCHES/FIXTURES residual spot-check. Conflict check: item (2) is NOT merely uncited — it
  is already an ACTIVE, EXPLICITLY-TRACKED conflict in the covering set.
  `sports_satellite_ao_dispatch_batch4_2026_07_25.md`'s Deferred section and
  `autonomous_session_operator_decisions_2026_07_25.md` entry #8 state the residual "may share a root cause with Track
  S2's still-open 'decision 16' day-partition investigation; genuine ambiguity, not resolvable from evidence alone" —
  i.e. another in-flight track (Track S2 foldin) may already be about to resolve the same underlying mechanism via a
  different route, and which side should execute is explicitly awaiting an operator ruling.
  `batch4_finalize_2026_07_25.md` todo 2 is already machine-gated to re-check this exact item once the operator answers
  entries #5-8. Drafting a competing todo here would race that already-queued resolution path. Item (1), the
  cross-bucket branch, has zero citations anywhere in the 17-doc covering set (grepped for "_audit_sports",
  "_BUCKET_KIND_MAP", "cross-bucket", "two-card", "audit-split" — no hits outside the target doc itself), so on
  citation-overlap grounds alone it would look batchable. But it fails the dispatch-scope eligibility test on a
  different axis: the doc's own "Decision" section records an explicit operator ruling (2026-07-14): "leave code as-is,
  document only. No bucket-map change, no `--apply`, no market-data sports phantom path added in this session. This doc
  tracks the inconsistency and the unverified count for a future deliberate fix." The 2026-07-23 RE-TRIAGE reconfirms
  nothing has changed and explicitly frames the fix as still needing "a future deliberate fix" — i.e. a design/judgment
  decision the operator has not yet authorized executing, not a bounded checkable task a worker can just go build.
  Dispatching it now would reverse a standing operator decision without a fresh go-ahead — exactly the "figure out how X
  should look"/judgment-call pattern CLAUDE.md's dispatch-eligibility rule excludes from AO-eligibility. Recommended
  resolution: fold both remaining items into the operator-decisions doc as a combined ask (or extend entry #8) — the
  operator needs to (a) rule on the Track-S2/residual-spot-check sequencing already queued, and (b) explicitly authorize
  proceeding with the cross-bucket `_audit_sports()` fix (superseding the 2026-07-14 "leave as-is" decision) before
  either becomes AO-dispatchable. No candidate todo drafted; this doc stays open, awaiting the operator's ruling via the
  existing batch4/batch5 conflict-resolution pipeline.
- **`plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md`**: Genuine, currently-unresolved conflict — do
  not draft a competing AO todo. Side A (target doc): the 3 remaining ACTIVE-scope todos (manifest-schema extension for
  per-fixture capture presence; build_sports_fixture_catalogue_from_manifest(); extend catalog build to invoke
  reference-data adapters incl. api_football_reference.py fixtures/betfair.py runners) all write/derive from reference
  data under a bare `entity={fixtures,teams,injuries}/` path, and the manifest-schema design explicitly depends on
  correct `league_id` resolution. Side B (sports_consolidated_closeout_2026_07_19.md, Track S/Track E/Track V, all P1,
  currently open/active): Track S has an open todo to "Eliminate (or document) the legacy bare `entity=fixtures/` (no
  pipeline_mode=) write path" — the SAME path string the target doc's adapter-invocation todo would write more data
  into; the closeout's own Canonical-target section declares that bare path FROZEN since 2026-05-23 and explicitly names
  this exact target doc as one of 3 live artifacts currently violating that freeze. Track E is actively repointing ~9
  consumers off bare `entity=fixtures` onto the split `fixtures_schedule`/`fixtures_outcomes` naming — directly
  contradicting the target doc's plan to keep writing the bare path. Track V still tracks `league_id` canonical-form
  migration as UNRESOLVED — the exact prerequisite the target doc's manifest-schema-extension design needs and does not
  currently account for. This is not stale/superseded on either side: both are dated 2026-07-19/07-23/07-25 and both are
  open P1/P2 items today. Confirming the conflict is genuinely still open (not merely cited):
  `/plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md`'s only todo touching the target doc is an
  explicit cross-link/awareness note whose own text says "Neither doc's design is decided by this todo; it only makes
  the collision/dependency visible... do NOT implement either resolution." The target doc itself carries a 2026-07-23
  banner instructing readers not to design or ship its manifest-schema extension or entity path "against a stale read of
  either plan" and to check the closeout's Track C/S/E/V state first. Recommended resolution (for the operator, not
  auto-executable by a worker): decide, in one place, (1) whether the target doc's fixture-grain reference-data writes
  should move onto the closeout's `fixtures_schedule`/`fixtures_outcomes` split naming instead of
  `entity={fixtures,teams,injuries}/` before any manifest-schema-extension design starts, and (2) sequence the
  manifest-schema-extension design to START AFTER (not concurrently with) Track V's league_id canonical-form migration
  lands, since the schema design's own correctness depends on it. Until that ruling exists, none of the target doc's 3
  remaining ACTIVE-scope todos are independently AO-dispatch-eligible — dispatching any of them risks writing/designing
  against the frozen path the closeout is actively eliminating, or against a league_id form the closeout may still
  change under it.
- **`/plans/archive/2026_08/sports_legacy_fixtures_path_migration_2026_07_24.md`**: Confirmed via direct read: the doc's
  7 open todos are P0 per-date/league census, P1 schema-mapping spot-check, P1 migration-script dry-run, P1 --apply
  migration, P1 fallback-function removal, P2 [OPERATOR] snapshot-then-delete, P2 doc-sync. Only the P0 census is even
  referenced anywhere in the covering set (Phase-1 finding), and that reference is a genuine, already-adjudicated OPEN
  conflict, not a stale/superseded mention. `sports_satellite_ao_dispatch_batch3_2026_07_25.md` (line ~257) and
  `batch4_2026_07_25.md` (line ~150) both independently flag "3 conflicts, all still open" for this exact census
  candidate against `sports_consolidated_closeout_2026_07_19.md`'s own OPEN ground: (1) Track S (closeout line ~435) —
  "Eliminate (or document) the legacy bare `entity=fixtures/` write path still active today" — if that writer is still
  live, the census's snapshot could be stale/repopulated after migration; (2) Track E (closeout line ~460) — "Repoint
  the remaining stale `entity=fixtures` consumers" (9-file sweep) — unconfirmed whether these call sites are genuinely
  disjoint from this doc's own `sports_fixtures.py` fallback-removal scope, i.e. two plans could independently touch
  overlapping consumers; (3) Track C1 (closeout line ~274, checked `[x]` but explicitly PARTIAL — 282,231/337,464
  restamped, 55,233 dedup-key collisions unresolved, tracked in
  `issues/fixtures_manifest_duplicate_collision_residual_2026_07_24.md`, still `status: open` with no operator
  DELETE-policy ruling) — the census's `data_type=="FIXTURES"` population could systematically miscount
  label-only-restamped rows as "already covered" without a real GCS object-read check.
  `autonomous_session_operator_decisions_2026_07_25.md` entry #7 formalizes this as a live, unresolved operator fork:
  Option A (worker-recommended) = dispatch the census now with an explicit scope-correction folded into its Done-when
  (verify "canonical empty" via a real GCS object read, not the manifest label alone, closing the C1 gap) vs. Option B =
  hold the census entirely until the operator first rules on the 55,233-row DELETE-policy question in the C1 residual
  doc, so the census and the eventual migration plan design together in one pass. Entry #7's **Status is `open`** — no
  ruling has been made as of this audit. This is exactly the CONFLICT CHECK step-3 case: two docs (this plan's census +
  `sports_consolidated_closeout_2026_07_19.md` Track S/E/C1) prescribe/imply different orderings for the same underlying
  fixtures-path ground, and the ordering is NOT resolvable from evidence alone — it needs the operator to pick A or B.
  The remaining 6 todos (schema-mapping spot-check through doc-sync) are all sequentially downstream of the census's
  output (the census produces the load-bearing (date, league) set every later todo consumes), so they are transitively
  gated on the same unresolved decision — none of them can be usefully batched ahead of entry #7 resolving. No
  candidate_todo drafted; this doc's orphaned work is fully accounted for as already-flagged, still-open conflict_gated
  ground (entry #7), not a fresh gap to fold into a new AO-dispatch batch.

## Note — found fully covered on re-check (Phase-1 verdict superseded, not orphaned)

- **`plans/archive/issues/sports_trades_attempted_failed_2026_07_23.md`**: Not a genuine unresolved conflict — a
  duplicate-coverage finding that supersedes the Phase-1 "partial coverage" verdict. Re-grepping the full covering set
  (including the two docs Phase-1's evidence apparently didn't check, both dated 2026-07-25, one day after Phase-1's own
  2026-07-23 doc) shows BOTH remaining open items are already claimed, not just one: (1) the [DESIGN] P3 "flag
  check_high_attempted_failed owner" runbook-note item is covered verbatim by
  `sports_consolidated_native_ao_extract_2026_07_25.md` lines 280-285 — a `[DATA] P3` todo titled "Track S2 — write the
  check_high_attempted_failed runbook note for deployment-service", citing the identical
  87.2%-ratio/K1-K2-denominator-shrink content, "Done when: the runbook note is added", sourced from
  `sports_consolidated_closeout_2026_07_19.md:951-955` (status: draft, but explicitly included in the operator-supplied
  covering set as an active/draft AO-dispatch doc). (2) the [VERIFY] P3 "re-check ratio once K1/K2 fully flips + DELETE
  lands" item is covered by `sports_closeout_track_s2_foldin_2026_07_25.md` lines 200-205 as a
  `[DATA] P3 BLOCKED-PREREQUISITES` todo, explicitly "Filed: sports_trades_attempted_failed_2026_07_23.md", gated on the
  parent's Track V K1/K2 DELETE. Cross-checked both extraction docs against each other and against the parent
  `sports_consolidated_closeout_2026_07_19.md` (source of both) — `sports_closeout_track_s2_foldin_2026_07_25.md`'s own
  "Overlap reconciliation" header explicitly enumerates item (7) as "the check_high_attempted_failed runbook note
  (excluding the sibling re-check once K1/K2 DELETE executes sub-part — carried here below)", i.e. the two 2026-07-25
  docs were deliberately authored as a matched split of exactly these two items — no overlap between them, no
  different-approach conflict, both are live/consistent with each other and with the original doc's phrasing. No new
  candidate_todo should be drafted: doing so would create a genuine third duplicate of already-claimed ground. This doc
  has zero residual orphaned work once the full (including 2026-07-25-dated) covering set is considered; Phase-1's
  "orphaned_partial_coverage" verdict was based on a covering-set snapshot that predated/missed these two docs.

## Deferred — operator decision needed (BLOCKED-OPERATOR-DECISION, not batchable)

- **`plans/active/data_completion_sports_2026_07_24.md`**: **RULED 2026-07-28 — proceed with BOTH asks.** (1) The
  rate-limit calibration probe: applying the general theme's "live probing should be relaxed to cover all asset groups
  and shards wherever needed — err toward broader/more permissive scope, not narrower," authorize the one-time
  calibration probe as scoped (a bounded, time-boxed test from a disposable VM IP, not a shared production IP, so a
  temporary ban doesn't touch live captures — same isolation principle already applied to Tardis VM concurrency
  elsewhere in this workspace). (2) The API-Football daily-quota bump (300k→1.5M/day, 5x): applying "cost under $100 is
  not a concern, full backfills/migrations get done, don't let spend block completion" — proceed with the bump to reach
  full coverage faster rather than the slower skip-fresh-reruns branch. **Residual for the operator (per the
  credential-or-spend carve-out): the actual account-tier upgrade with the vendor is the one remaining concrete step**
  only the operator (or AO's self-service ambient identity, if it can provision this per finding W) can complete — the
  DIRECTION (yes, bump; yes, probe) is ruled here, the account action itself is not invented as already-done. **Done
  when**: the probe runs once (from an isolated VM) with each provider's real break-rate recorded, AND the quota-bump
  account action is completed + the backfill proceeds at the new ceiling — or, if the operator's own vendor-account step
  is still pending, the code/launcher side is fully prepped (scoped, ready to fire) with the account step named as the
  sole blocking residual. Confirmed the two genuinely uncovered items (lines 397-406 rate-limit calibration probe; line
  797 API-Football daily-quota bump) are NOT cited or overlapped by any doc in the covering set. Grep of
  calibrate_source_rate_limit.py / ramp-to-429 / SOURCE_RATE_LIMITS_RPM / SOURCE_PER_IP_LIMITS across all 16
  covering-set docs returns zero hits outside the target doc itself. Grep of 'API-Football' + 'daily
  cap/quota/Custom300/1.5M' hits batch2 (lines 168, 265, 501, 702-722) and sports_consolidated_closeout_2026_07_19.md
  line 614, but those are DIFFERENT concerns: batch2's hits describe (a) enrichment coverage percentages by data-type as
  diagnostic context, and (b) a VM-stop/relaunch incident triggered by hitting the SAME daily quota ceiling
  operationally -- not a proposal to bump the ceiling itself; sports_consolidated_closeout line 614 is a scope-boundary
  ruling for the UNRELATED 2013-2018 historical window ('no further api-football spend' there), not a ruling on the
  current ~34%-honest-coverage quota-bump lever. So no duplicate/competing todo exists anywhere -- this is a clean
  no-overlap case, not a conflict_gated one. Both remaining items, however, fail the dispatch-scope eligibility test on
  operator-decision grounds rather than conflict grounds: (1) Rate-limit calibration probe (line 397-406): the doc's own
  text labels it explicitly operator-gated ('operator-gated; blast from an IP, see when banned -- one-time test'). It
  requires launching an ephemeral VM whose PURPOSE is to intentionally trigger 429/bans against live third-party
  providers (understat, transfermarkt, open_meteo, soccer_football_info, polymarket_clob, polymarket_gamma_api) to find
  the break-rate -- an action with real external-facing consequences (temporary IP bans, provider ToS exposure) that the
  doc's author already withheld from unconditional dispatch. Per CLAUDE.md's VM-launch gating rule, this needs an
  explicit [OPERATOR] authorization, not a worker's unilateral judgment call on acceptable-risk thresholds. (2)
  API-Football daily-quota bump (line 797): the doc frames this as an explicit EITHER/OR -- 'operator bump to 1.5M/day
  OR multi-day skip-fresh re-runs.' The bump itself is a spend-authorization ask (300k/day -> 1.5M/day is a 5x cost
  increase on a metered API) squarely matching the operator_gated 'credential/spend ask' pattern. The doc does not
  resolve which branch to take, so a worker cannot determine the bounded action without that ruling first. Both items
  therefore route to the SAME gate (an operator ruling on acceptable external-facing risk / spend), so this doc as a
  whole classifies operator_gated rather than yielding a batchable todo. Recommended resolution: raise a single operator
  question bundling both asks (probe-VM go-ahead + quota-bump-vs-skip-fresh choice) in the next operator-decision-needed
  batch; once ruled, a follow-up pass can draft the now-bounded todo(s) against whichever branch is authorized.
- **`plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`**: **RULED
  2026-07-28 — authorize the third remediation attempt once the deploy is confirmed** (general theme: full
  backfills/migrations get done when not a regression; the underlying fix has already shipped and proven stable across 5
  consolidator cycles on a sibling bucket). This converts the standing "confirming + authorizing" ask below into a
  bounded, dispatchable sequence: (1) verify-deploy of `unified-trading-library@14301571` to the
  `uts-prod-manifest-consolidator-instruments-sports` Cloud Run job specifically; (2) deploy it if not yet deployed; (3)
  re-run `remediate_cross_ag_prediction_bleed_round3_2026_07_24.py` against `instruments-store-sports-prd`; (4)
  hold-verify across ≥2 real consolidator cycles (full completion, not a single immediate check) before closing. The
  actual todos (12-14) live in the archived issue doc itself, out of scope for this file's edit pass — this ruling is
  recorded here so a follow-up pass retags them. Confirmed the Phase-1 uncovered item: todos 12/13/14 (the
  manifest-consolidator TOCTOU fix, its deploy, then a re-run+hold-verify of the cross_ag_prediction remediation) are
  not cited or covered by any doc in the covering set. Todo 15 (the separate market-data-tick-sports-prd KALSHI
  empty_confirmed population) IS fully covered by sports_satellite_ao_dispatch_batch3_2026_07_25.md, which explicitly
  scopes itself as read-only classification and explicitly defers todos 12-14's fix as "explicitly
  BLOCKED-OPERATOR-DECISION" — so batch3 does not attempt to cover 12-14 either. CONFLICT CHECK finding (genuine,
  resolves by logic, not a competing-fix situation): todo 12's exact prescribed fix — capture unified-trading-library's
  manifest_consolidator._write_consolidated()'s CAS `if_generation_match` token from the SAME read that produces the
  merge payload (via download_bytes_with_generation), instead of a late blob.reload() — has ALREADY SHIPPED as
  unified-trading-library@14301571, closing the identical TOCTOU race in the same shared function, resolving the sibling
  issue docs plans/archive/issues/sports_odds_manifest_consolidator_captured_outranks_resurrection_2026_07_24.md and
  sports_odds_manifest_captured_outranks_blocks_legacy_leak_correction_2026_07_24.md (both status:resolved, full
  quality-gates green, 98/98 + 60/60 tests passing). Because _write_consolidated is a single shared library function
  used by every asset_group's consolidator (per our target doc's own ROUND 6 scope note), this fix's code-level content
  directly satisfies todo 12's ask — it is not a different/competing fix, it is the SAME fix, already merged. This is
  corroborated by plans/active/sports_consolidated_closeout_2026_07_19.md's Track V section, which cites the same commit
  fixing a TOCTOU revert on a DIFFERENT population (the league_id swap) and confirms it verified stable across 5
  consolidator cycles in production — i.e. the fix is not just merged but observed working live. What is NOT yet
  independently confirmed by anything in the covering set: (a) whether the specific
  uts-prod-manifest-consolidator-instruments-sports Cloud Run job (the one serving the instruments-store-sports-prd
  bucket this doc's bleed lives in, as opposed to the market-data-sports consolidator job the sibling docs verified) has
  actually been rebuilt+redeployed with the unified-trading-library@14301571-containing image (= todo 13), and (b) todo
  14's re-run of remediate_cross_ag_prediction_bleed_round3_2026_07_24.py against THIS specific bleed population plus
  the required multi-cycle hold-verify, which has never been attempted since the fix shipped. Why this stays
  operator_gated rather than batchable despite todo 12 likely already being satisfied: the target doc itself states, in
  its own frontmatter summary and in ROUND 7 body text, an explicit standing gate — "BLOCKED-OPERATOR-DECISION on
  scheduling that work... Do NOT re-attempt manifest remediation until it ships" and "this needs operator sign-off
  before any code/job change, not an autonomous patch" — because this is a manifest WRITE to a live,
  continuously-consolidating 5.5M+ row production index that has already silently reverted TWICE (once after ~30h43m,
  once after ~5min) under a fix that (at the time of writing) had not yet shipped. Even though the underlying library
  fix now appears to have shipped and been proven stable on a sibling bucket, confirming that + authorizing a third
  remediation attempt on THIS specific index is exactly the "code/job change sign-off" scenario the doc's own words gate
  on an operator decision, not a worker's unilateral judgment call — a worker re-running a manifest-write remediation
  script against a live production index with a documented double-failure history, based on the worker's own inference
  that a sibling fix "probably" covers this doc's bucket too, is the kind of irreversible-adjacent, high-blast-radius
  action task_template.md's dispatch-scope-eligibility rule reserves for human sign-off. Recommended operator decision
  to unblock: (1) confirm/deploy the unified-trading-library@14301571-containing image to the instruments-sports
  consolidator Cloud Run job specifically (verifying image build timestamp / library version pinned in that job's
  manifest vs. the commit's merge time), and if not yet deployed, authorize that deploy; (2) once deployed, authorize
  re-running remediate_cross_ag_prediction_bleed_round3_2026_07_24.py (already built, reusable, REMOVE-only) against the
  instruments-store-sports-prd bucket and the required multi-cycle (>=2 real consolidator cycles, not just immediate
  verify) hold-check before re-closing this doc. Once the operator gives that go-ahead, todos 13+14 collapse into a
  single bounded, checkable AO-eligible todo (verify-deploy -> run script -> poll N cycles -> record result) that a
  worker could execute without further judgment calls.
- **`plans/archive/issues/fixtures_manifest_duplicate_collision_residual_2026_07_24.md`**: **RULED 2026-07-28 — option
  (2), a scoped, verified DELETE against the production manifest.** Applying the general theme (opt for full
  completions, no shortcuts — permanent noise / tech debt is the option to AVOID; a tombstone mechanism that doesn't
  exist yet is unnecessary new tooling for what is a straightforward label-only duplicate cleanup, not sole-surviving
  data): these 55,233 rows are dedup-key collisions from an already-executed restamp (not the sole surviving copy of
  anything — a canonical twin/relabeling already exists per the doc's own framing), so leaving them as permanent noise
  or building new tombstone tooling are both worse than just deleting the duplicates properly. Execution: the standard
  delete-safety protocol applies (5-part proof, snapshot-then-write, fresh `gcs_bucket_soft_delete_retention_seconds()`
  check per finding T/U — if ≥604800s, this qualifies as reversibility-verified and does not need a fresh `[OPERATOR]`
  gate per CLAUDE.md's carve-out, mirroring the precedent already applied elsewhere in this exact corpus, e.g. this same
  file's `prediction_phantom_reconciler_wipes_bundle_atom` todo). **Done when**: all 55,233 duplicate rows are removed
  with a before/after manifest census confirming only the intended duplicate population changed and every
  restamped/canonical row survives untouched — full completion, not a partial run. The actual todo checkbox lives in the
  target issue doc, out of scope for this file's edit pass; this ruling is recorded here for a follow-up pass to retag
  it. Confirmed via full doc read: the doc's single open [DIAG] P2 todo asks to "decide + execute the resolution" for
  55,233 duplicate legacy FIXTURES manifest rows, among three explicitly-offered options — (1) leave as permanent noise,
  (2) scoped verified DELETE against the real prod manifest bucket
  (instruments-store-sports-prd-central-element-323112), or (3) investigate/build a tombstone mechanism that isn't
  verified to exist yet. Conflict check: grepped every doc in the covering set for "55,233" / the doc's slug. Three hits
  are pure citations, not competing/executing todos: sports_consolidated_closeout_2026_07_19.md (line ~321) just marks
  the parent restamp todo PARTIAL and points at this issue doc as the open tracker;
  sports_satellite_ao_dispatch_batch4_2026_07_25.md's todo (lines ~92-111) explicitly does a _reconciliation-only_ pass
  on a sibling doc (fixtures_manifest_legacy_backfill_2026_07_24.md) — its own "Conflict-check clearance (2026-07-25
  re-check)" note confirms it deliberately defers the actual delete-vs-leave call to this doc and performs zero
  production mutation; the "operator-decisions doc entry #7" reference (line ~150-152) confirms this exact fork is
  already logged as a pending, unruled operator decision elsewhere, not something any AO plan has taken on itself to
  resolve. No doc in the covering set proposes or attempts a different resolution path, so there is no genuine two-sided
  conflict — just consistent, correct non-resolution pending the operator. Given option (2) is an irreversible prod-data
  DELETE against 55,233 manifest rows and option (3) requires verifying/building tooling that may not exist, and the
  three-way choice itself needs explicit sign-off per the doc's own words, this fails the dispatch-scope eligibility
  test (not a worker-determinable bounded outcome) and is correctly operator_gated, not batchable. Recommended
  resolution: surface this to the operator as a single decision request — "leave-as-noise (zero risk, permanent tech
  debt) vs. scoped-verified-DELETE (closes SCHEDULE_DEFINING_DATA_TYPES narrowing, requires extending the
  f14b13ae/8e783d70 resurrection-safety verification to this bucket first) vs. tombstone (unverified feasibility)" —
  once ruled, the resulting concrete action (e.g. "run the verified-delete procedure" or "record the leave-as-noise
  decision in the doc") becomes a clean, batchable AO todo in the next dispatch batch.
- **`plans/active/issues/sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md`**: **Reviewed 2026-07-28,
  confirmed remains a permanent hard-stop — NOT retagged.** This is an irreversible prod-bucket GCS delete
  (`instruments-store-sports-prd`, soft-delete=0 per the doc's own framing) with execution authority withheld from
  agents by workspace HARD RULE regardless of how well-specified the mechanical steps already are (the operator already
  gave in-session Option-A authorization 2026-07-25 — what remains is literal human execution, not a decision). Conflict
  check: grepped the consolidated closeout (sports_consolidated_closeout_2026_07_19.md) and every batch2/3/4(+finalize)
  doc for the target objects (`day=all/entity=teams/teams.parquet`, `day=all/entity=venues/venues.parquet`) and the
  delete mechanism (`_legacy_archive`). Only batch2 (sports_satellite_ao_dispatch_batch2_2026_07_24.md) mentions these
  paths at all, and strictly to close ITS OWN investigation todo as "resolved-as-investigated" — it explicitly punts the
  actual delete, stating it "needs explicit operator sign-off... not a unilateral fold-that-can't-work or an
  irreversible delete." No genuine overlap/duplicate exists; nothing else claims this ground with a different approach.
  So there is no conflict to gate on. Eligibility: the single remaining todo is tagged `[OPERATOR] P2` and its own text
  states "Prod-bucket delete, human-gated — no agent runs this." This is a soft-delete=0 (irreversible) GCS delete
  against a PROD bucket (`instruments-store-sports-prd`), which per workspace HARD RULE is human-only regardless of
  scope-boundedness (the mechanical steps — backup-copy, verify, delete, verify-gone — are well-specified, but execution
  authority is explicitly withheld from agents by the doc author and by the corpus-wide prod-bucket-delete-is-human-only
  rule). The operator already gave in-session Option-A authorization (2026-07-25 banner) — what remains is not a
  design/judgment decision but literal execution of an irreversible prod delete, which stays human-only regardless. This
  is NOT a batchable AO todo; it cannot be drafted as a worker-executable candidate. Recommended resolution: this item
  stays parked as an `[OPERATOR]`-only action item for the operator (or an operator-supervised session) to physically
  execute per the doc's already-written backup→verify→delete→verify-gone steps; no new plan/todo should be drafted to
  route it through AO dispatch.
- **`plans/active/issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`**: Confirmed the doc's 4 remaining
  open todos: (A) manifest-slice replacement for check_api_football_dependency() [shipped in batch2,
  instruments-service@bd1da540 — Phase-1's covered item], (B) share path-template constants between writer and checker,
  (C) VERIFY real backfill speedup, (D) NEW mapping-coverage gap in _build_fixture_league_map_from_gcs needing an
  operator/architecture decision. Conflict check on B and C turned up real overlap that changes the Phase-1 picture for
  both, so neither should get a freshly-drafted competing todo: - B ("share path-template constants") — the SAME batch2
  commit that shipped item A explicitly states, in its own evidence text: "path-template duplication is moot since the
  hot path no longer touches them, per this todo's own anticipated outcome"
  (sports_satellite_ao_dispatch_batch2_2026_07_24.md:503-505). Once `_manifest_shows_fixtures_captured()` became the
  PRIMARY check and the hardcoded-path probe became a rare fallback-only path, the original rationale for unifying the
  templates (avoiding silent desync on a hot, frequently-exercised path) no longer applies with the same urgency — this
  is a same-batch, later-dated, on-the-record assessment that provably supersedes B's original framing, even though the
  target doc's own checkbox for B is still unchecked (doc not updated post-shipment). Drafting a new AO todo to "share
  path templates" would just re-litigate a call the shipping commit already made. Recommend only a doc-hygiene note (not
  an AO todo): flip the target doc's progress log to record B as resolved-by-side-effect of the batch2 fix, or
  explicitly re-affirm it's still wanted for defense-in-depth on the now-rare fallback path — that's a judgment call for
  the doc owner, not new dispatchable engineering work. - C ("confirm real backfill speedup") — batch2 explicitly
  deferred this because it was "gated on 2 sibling implementation todos" (the check_api_football_dependency()
  manifest-slice fix and the sports_fixtures.py:356 batching fix). Both of those sibling todos are now shipped (batch2's
  own todos, both `[x]`). Critically, sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md already carries an OPEN
  (`- [ ]`, not yet executed) todo whose entire job is to re-check exactly this gate and extract C as a new dispatchable
  todo once cleared: "(3) the `sports_dependency_check` real-backfill timing verification (gated on 2 sibling
  implementation todos) — same treatment... Done when: each of the 4 deferred items has either (a) a new tracked
  todo/plan created and dispatched because its gate cleared, or (b) an explicit, re-verified confirmation that its gate
  is still open" (batch2_finalize:88-100). Drafting a second, parallel todo for C here would race that existing finalize
  todo — same underlying fix, same file/mechanism (the doc's own VERIFY todo), no genuine ambiguity about which one is
  "right," just duplicate dispatch. The correct move is to let batch2_finalize's todo #88 do its job (it will land C as
  a new todo once it runs), not front-run it. That leaves D as the only item with no existing coverage and no in-flight
  resolution mechanism anywhere in the covering set (grep-0 for `_build_fixture_league_map_from_gcs` outside the target
  doc and the aggregated-sources inventory list, which is audit-only). D is explicitly NOT a bounded worker-executable
  outcome — the doc's own text says it "needs an operator/architecture decision on whether the mapping should use the
  broader Prediction+Features+Reference set (matching `_fetch_fixture_ids_via_api`'s fallback-path scope) or whether
  `fixture_ids_override`'s real callers only ever pass fixture_ids that already have a working non-GCS league source,
  making this dead weight — real verification of which, before choosing a fix, is required." This is a genuine
  two-option design fork (broaden the league-set the mapping draws from vs. conclude the gap is dead weight for real
  callers) that determines the shape of the eventual fix; it cannot be resolved by a worker alone. Recommend: raise to
  the operator as "should `_build_fixture_league_map_from_gcs`'s af_league_id→canonical mapping use the broader
  Prediction+Features+Reference league set, or is the current narrow `get_prediction_leagues()` scope fine because
  `fixture_ids_override`'s real callers never hit the gap in practice (needs a real-caller-usage check to confirm)?" —
  once ruled, the resulting fix becomes a normal bounded AO todo.
- **`plans/archive/issues/sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md`**:
  The remaining work in this issue doc cannot be batched into an AO-dispatch todo because it is explicitly
  operator-gated by the doc's own text: the [CODE] P2 todo says 'do NOT touch VENUE_DATA_TYPE_CAPABILITIES or the golden
  regression until' the operator's FINAL decision on retire-vs-scaffold, and a /blocked question requesting that
  sign-off was posted 2026-07-24 (slot 5) but remained PENDING as of the doc's latest content. The decision matters
  because retiring the capability declaration shrinks the sports honest-coverage denominator (an operator-visible metric
  change), so this is a genuine human decision point, not a determinable worker outcome. Recommended resolution: this
  doc should stay open and orphaned until the operator answers the pending /blocked question (BLK-c545ae54 referenced in
  the doc). Once answered, the resulting [CODE] P2 todo becomes trivially batchable (bounded: edit one registry dict +
  one golden JSON regression file, OR scaffold+BLOCKED-CREDENTIALS per the external-data-always-available rule) and
  should be picked up in the next AO-dispatch batch at that point. No conflicting work exists elsewhere in the covering
  set — the two doc hits found during the conflict check touch a different registry (DATA_TYPES_BY_ASSET_GROUP casing
  revert) and an already-resolved separate MDPS consumer-check, not this doc's retire/scaffold decision.
- **`plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md`**: Confirmed Phase-1: all 8 [DESIGN] P3
  todos (§1 decay-window statistic/window/data-source/output-shape, §2
  gate-statistic/sample-size/threshold-value/acceptance-test) remain unchecked with no later RE-TRIAGE/RESOLVED section.
  Conflict check: grepped every covering-set doc (consolidated closeout, audit, 3 closeout forks + finalizes,
  native_ao_extract + finalize, batch2/3/4 + finalizes) for
  arb-decay/alpha-gate/SportsArbDutchingEngine/decay_window/edge_bps_remaining. Only one hit:
  sports_satellite_ao_dispatch_batch2_2026_07_24.md mentions `SportsArbDutchingEngine` twice, but both are UNRELATED — a
  decimal-odds-field migration for features-service and a legacy-engine-migration todo — neither touches decay-window
  measurement or the alpha gate's pass/fail criteria. No genuine overlap; nothing else claims this ground. However this
  doc's own frontmatter (`assigned_vm: NA`, `execution_scope: local-only`) and body are explicit: it exists BECAUSE of
  operator ruling BLK-b567ce7d (2026-07-21) that this is brand-new zero-spec feature work requiring operator sign-off on
  acceptance criteria/thresholds BEFORE any implementation OR further spec-drafting dispatches. §3 "Open questions for
  operator sign-off before implementation dispatches" lists three unresolved judgment calls baked into the 8 todos
  themselves: (1) which assigned_role/repo-split owns eventual implementation (quant_dev vs backend_engineer,
  single-repo vs two-repo split), (2) p25-tail-aware vs mean for the §2 gate statistic — "a real risk-appetite decision,
  not a mechanical one" per the doc's own words, (3) whether the operator wants a provisional fixture-derived threshold
  value or insists on real paper-run soak data before any code ships. Every one of the 8 todos is phrased as "Define X,
  recommend Y" — i.e. the doc proposes a design and asks the operator to bless it, not a checkable/executable outcome a
  worker can determine alone. This is the textbook "figure out how X should look" pattern the dispatch-scope-eligibility
  rule excludes from AO batching (CLAUDE.md § Plans — operator ruling 2026-07-23). Drafting a competing/pre-empting AO
  todo here would violate the very ruling that spawned this doc.
- **`plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md`**: Confirmed via direct read: the doc has 5
  open todos, none overridden by a later dated section. Conflict check: grepped every
  batch2/3/4(+finalize)/consolidated-closeout/fork/foldin/hygiene/native-ao-extract doc for
  "SportsMatchingEngine"/"sports_matching" and for "BACKTESTS.md"/"backtest-groups verification". Result — no genuine
  conflict, only partial acknowledgment: batch2's dispatch plan (sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  lines 17-22 and 905-908) explicitly names todos 1/2/4 (run_sports_backtest CLI, fixture wiring, hermetic alpha_bps
  test) as EXCLUDED pending the SportsMatchingEngine-vs-L0Matcher decision (todo 3), and its finalize plan
  (batch2_finalize, lines 93-100) carries a re-check-and-extract-new-batch mechanism gated on that same decision
  landing. Batch3/batch4 (+finalizes, both status: draft) contain zero mentions of
  group_c/backtest_harness/run_sports_backtest — they don't touch this doc at all, so no overlap there either. Todo 5
  (DESIGN — decide backtest-groups verification-surface placement / docs/BACKTESTS.md) is mentioned nowhere in any
  covering plan except a bare re-listing in sports_consolidated_closeout_aggregated_sources_2026_07_24.md with no
  resolving or gating todo — it is completely untouched, not even acknowledged-and-excluded. So there is no
  competing/duplicate prescription anywhere in the covering set for either uncovered item — this is pure gap, not
  conflict. The two genuinely uncovered items are BOTH the plan's own [DESIGN] todos (3 and 5): todo 3 = resolve
  SportsMatchingEngine (dead code, zero callers) vs L0Matcher duplication — an architectural call between deleting
  unused code or wiring it in as the sports-specific matcher, which gates todos 1/2/4; todo 5 = decide whether the
  future harness belongs in the routine docs/BACKTESTS.md verification surface (currently dead per a sibling
  investigation) or stays a manual one-off, given sports is explicitly backtest-only/not-on-critical-path. Neither is a
  bounded, worker-determinable outcome — both are open-ended judgment/design calls per CLAUDE.md's
  dispatch-scope-eligibility rule (an audit/design todo is AO-eligible only when its outcome is a checkable fact or
  scoped change, never "figure out how X should look"). Todo 3 additionally is a hard prerequisite already correctly
  modeled by batch2/batch2_finalize's re-check-and-conditionally-extract mechanism — nothing new to draft there beyond
  what's already tracked. Todo 5 has no tracking mechanism anywhere, but is likewise a pure human design call
  (docs-placement / verification-surface strategy for sports), not something an AO worker can resolve alone. Recommended
  resolution: this doc needs an operator/architect ruling on both DESIGN items (ideally in one sitting since todo 3
  gates the implementation todos and todo 5 is independent-but-related scope-placement); once ruled, batch2_finalize's
  existing re-check todo already covers re-extracting todos 1/2/4, and todo 5 should be added as an explicit line item
  to that same re-check (or a follow-up doc) at that time. No new AO-dispatch todo should be drafted now — doing so
  would either restate the design question as a fake "todo" (violating the eligibility rule) or duplicate the re-check
  mechanism batch2_finalize already owns.
- **`plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md`**: **RESOLVED 2026-07-28 —
  operator direct answer: picked a paid sports-odds API quota tier and authorized proceeding with the resume.** The
  source doc's own todo (lines 134-138, "[DATA] P2. Live ODDS quota decision + cheap second source") is retagged there
  directly (see that file) — applying the doc's own top recommendation as the concrete tier (The Odds API Starter,
  ~$10/mo, 50k credits, for the live league set) + api_football `/odds` in-play as the free second source, per the
  operator's ruling. No longer operator_gated; the resulting connector-tuning + VM-cadence change is now a bounded,
  batchable AO todo (see the retagged checkbox in that doc). Prior conflict-check note (for provenance, still accurate):
  grepped the consolidated closeout (2026_07_19) and every batch2/3/4(+finalize) doc for "odds
  api"/"live.odds"/"book.set"/"quota tier"/"odds_horizon"/"LIVE_ODDS" — all hits found
  (sports_consolidated_closeout_2026_07_19.md:516, batch2:812/826/847/867/878/898/962/978, batch4:112/116) concern the
  MDPS `odds_horizon_bucket` REPROCESS/canonicalization migration (a distinct, unrelated mechanism), so no
  file/mechanism overlap exists for the now-unblocked quota-tier work either.
- **`plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md`**: The doc's entire remaining-work
  surface is a single sequential chain gated at its first step by an unresolved OPERATOR decision (pursue live
  sports-odds ingestion or not), with every downstream todo explicitly conditioned on that yes/no, and the chain's
  terminal step is itself a second OPERATOR go-ahead gate. No sub-slice is independently checkable/executable by a
  worker without that decision landing first, so this fails the dispatch-scope eligibility test at the very first todo —
  it is a human decision wearing a todo's clothes, exactly the pattern CLAUDE.md's plan-authoring rule calls out. The
  conflict check found the doc's cited blocker (cross-AG bleed bug) is already correctly owned by the consolidated
  closeout + batch3, with no competing-fix duplication against this doc's own todos, so nothing needs folding in from
  that angle either. Result: operator_gated, no candidate_todo drafted. Confirmed via full read: the doc has 6 open
  todos forming a strictly sequential chain, all P3, all human-plan-by-construction per operator ruling BLK-9d3a208c.
  Todo 1 is the load-bearing gate: "[OPERATOR] P3. Decide whether to pursue a live sports-odds ingestion path at all" —
  sports has zero live-odds infrastructure today (MTDS is architecturally batch/download-only per
  batch-live-architecture.md §4; no `live_odds_api` SOURCE_MODE_CAPABILITY exists), so this is a real
  infrastructure-investment decision, not a flag flip. Todos 2-6 (scope the MTDS live-odds connector, build
  launch-mtds-live-sports.sh/launch-mdps-features-live-sports.sh, build the FSS live handler, run the promote-workflow
  chain, and finally an [OPERATOR] go-ahead to flip to live) are each explicitly gated "Once Todo 1 is a yes" / depend
  on the prior step landing — none of them is independently dispatchable without that decision, and the terminal todo is
  itself another [OPERATOR] gate (full readiness-ladder Groups A-H sign-off). There is no bounded, worker-executable
  subset here: even Todo 2 ("scope the MTDS live-odds connector... as its own follow-up plan") is conditioned on Todo
  1's yes/no, which is undecided. CONFLICT CHECK: grepped sports_consolidated_closeout_2026_07_19.md and batch2/batch3
  dispatch docs for overlap on this doc's own mechanisms (live_odds_api, launch-mtds-live-sports.sh, promote-workflow
  activation) — no hits; the only overlapping ground is the doc's own SCOPE-OVERLAP banner's cited hard BLOCKER (the
  cross-AG prediction/sports instruments-index bleed bug, ROUND 4+), which IS actively owned elsewhere:
  sports_consolidated_closeout_2026_07_19.md tracks the bleed as a Canon-track item (lines 227-234, 407-414) and
  sports_satellite_ao_dispatch_batch3_2026_07_25.md (lines 133-146) has an active read-only classification todo citing
  the same ROUND 4-7 TOCTOU bug, explicitly noting the ROUND 6/7 remediation is BLOCKED-OPERATOR-DECISION. That is the
  correct owner for the blocker itself — this doc's own Todo 1 does not duplicate it (Todo 1 is about live-odds
  ingestion strategy, not the bleed fix), so no competing-fix conflict exists; the bleed bug is simply a stated pre-req,
  already tracked, not something to re-batch here. Separately, batch2 (lines 397-402) already SHIPPED the
  `SportsArbDutchingEngine` naming migration (strategy-service@4c55438c), which is unrelated to the
  factory-dispatch-wiring bug this doc cites as a Group-B prerequisite
  (`sports_arb_dutching_engine_not_wired_to_factory_2026_07_21.md`) — different issue, no overlap, and that issue doc is
  out of this doc's own todo scope anyway (a "prerequisites tracked elsewhere" bullet, not this plan's todo).
  Recommended resolution: this doc stays correctly orphaned-but-uncoverable by AO dispatch — it needs the operator to
  answer Todo 1 (pursue live sports-odds ingestion: yes/no) before any of its remaining work becomes batchable. Until
  then, none of Todos 2-6 should be drafted as AO-dispatch candidates since they're contingent on an undecided fork, and
  Todo 1 itself is explicitly tagged [OPERATOR]. Suggest surfacing this single question to the operator as a standalone
  decision ask (not a plan-of-work): "Pursue live sports-odds ingestion (new MTDS live connector +
  SOURCE_MODE_CAPABILITY entry) — yes, scope it as a follow-up plan, or no, mark this plan `status: cancelled`?"
- **`plans/active/sports_prelaunch_cf5_verify_residual_2026_07_24.md`**: **RULED 2026-07-28 — option (a): extend the
  coverage-start dates and backfill this data in.** Applying the general theme directly ("full backfills, full
  migrations — as long as an item isn't superseded by more recent work, DO IT"; "opt for full completions, no
  shortcuts... even if not MVP"; "cost under $100 is not a concern"): this is 10,345 real, non-fabricated objects (not a
  data-floor/fabrication case like the sports 2020-06-06 odds floor) sitting just outside the current official
  coverage-start constants — writing them off as permanently out-of-scope is the shortcut the theme says to avoid, and
  the backfill compute cost is trivial. **Full-completion mandate for whoever dispatches this**: this is a system-wide
  constant change, not a one-line edit — update `SOURCE_COVERAGE_START["footystats"]` (2019-01-01→2018-01-01) AND the
  api_football `DATA_TYPE_COVERAGE_START` sub-entity windows together, then propagate through every consumer
  (`clip_dates_to_source_coverage`, backfill orchestrators, data-status denominators, the phantom audit) — not just flip
  the constant and leave downstream consumers stale. Re-run `backfill_orphan_class_e_sports.py` afterward to manifest
  the corpus. The actual todo checkbox lives in the target doc, out of scope for this file's edit pass; this ruling is
  recorded here for a follow-up pass to retag it. Confirmed against the doc text (todo 2, lines 85-92): the C3
  pre-launch-window corpus (10,345 objects) previously required an explicit operator ruling between two mutually
  exclusive actions with real blast radius — (a) extend UAC coverage windows (SOURCE_COVERAGE_START["footystats"]
  2019-01-01→2018-01-01 + api_football DATA_TYPE_COVERAGE_START sub-entity windows) and re-run
  backfill_orphan_class_e_sports.py to manifest the corpus, or (b) ratify the corpus as permanently outside-window
  (becomes a CF-21-style cleanup candidate). Conflict check: grepped the consolidated closeout
  (sports_consolidated_closeout_2026_07_19.md) and every batch2/3/4(+finalize)/fork/foldin/hygiene/native-ao-extract doc
  for C3/footystats/SOURCE_COVERAGE_START/orphan_sweep_sports/backfill_orphan_class_e_sports/pre-launch-window. Found
  one substantive hit: sports_satellite_ao_dispatch_batch2_2026_07_24.md lines 550-567, a SHIPPED (checked,
  instruments-service@6cf44d31) fix to migration_orphan_sweep_sports.py's classifier ordering
  (is_covered_sports-before-_is_pre_launch bug causing stale pre-floor rows to misclassify as B_legacy_duplicate instead
  of C3_pre_launch_window). This is a classification-correctness bugfix, not a resolution of the underlying policy
  question — its own completion note explicitly says the "covered wins" semantics on the by_date-tree branch are
  "deliberately left untouched — a different, already-decided policy question (the v2 pre-floor 728-row disposition,
  issue doc §7 todo 1, [OPERATOR]-gated)", i.e. it corroborates rather than resolves that a separate operator decision
  remains open. No genuine conflict: the batch2 item fixes HOW rows get counted/labeled into the C3 bucket; the target
  doc's item 2 is WHAT TO DO with the C3 bucket once counted (extend windows vs ratify permanently outside-window).
  Different mechanisms, complementary not competing, no ordering ambiguity. Todo 1 (CF-5 relabel) is fully closed per
  Phase-1 evidence (batch2 line 462) and needs no further action here. Recommended resolution: this doc stays open
  pending an explicit operator ruling on the C3 window-extend-vs-ratify-permanently-outside-window fork; once ruled,
  whichever branch is chosen becomes a bounded, batchable AO todo (backfill_orphan_class_e_sports.py re-run + UAC window
  edit, or a CF-21-style cleanup/delete plan) — draft that follow-up only after the operator answers.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) -- swapped batch-naming/precedent-doc entries for
  the doc's own remaining active todo's real source + source-code targets (bucket_assignment_adapter.py,
  verify_ml_readiness.py).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **2026-08-09 (slot 16, data_engineering)**: Dispatched on the zombie-tick purge todo. Found
  `market-data-processing-service` had already shipped 2 loss-guard fixes today (`mdps@6b9ab9a`, `mdps@e273e72`, an
  incomplete slot-9 session) enabling `reprocess_sports_odds.py --force` to purge an all-zombie day — but before running
  it, discovered a BLOCKING architectural gap: the real, live zombie-contaminated `odds_horizon_bucket` shards sit at a
  legacy GCS path (no `pipeline_mode=`/`asset_group=` segments) that the purge script explicitly refuses to touch ("a
  separate, shadowed generation owned by the bucket-cutover lane," its own code comment), while `features-service`'s
  reader falls back to that exact legacy path whenever canonical is empty — which it always will be for these historical
  dates (root-caused to the 2026-07 legacy-bucket-cutover's PRESERVATION-not-migration disposition of ~90,947
  `odds_horizon_bucket` objects, and the daily reprocess cron's rolling-3-day-window scope never reaching back to
  historical dates). Running `--force` against the 18 known dates would NOT fix the bug — full evidence + root cause in
  `issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md` (P1, filed this
  session). **Separately, part (c) of this todo (the two-part gate-semantics fix) is superseded**: the source doc's own
  2026-08-08 operator-ruling banner says to switch `verify_ml_readiness.py` to the precedented aggregate ≥95% pass bar
  INSTEAD of implementing the two-part per-day exemption this todo's text still describes — that switch is tracked as
  its own gated `[CODE] P1` todo in `sports_taxonomy_p3_consumers_2026_08_08.md` (explicitly gated on THIS todo's
  part-(a) purge landing first). Neither (a) nor (c) as literally worded can be completed today; declining to flip this
  checkbox and filing `/blocked` rather than force through a partial or incorrect completion. No production data touched
  this session (read-only verification only).
- **2026-08-09 (slot 26, data_engineering)**: Operator answered slot 16's BLOCKED question — option B (fix
  `features-service/gcs_reader.py::read_bucketed_odds()`'s legacy-fallback trigger, not the writer). Shipped: a per-date
  manifest-marker check (`_canonical_odds_horizon_bucket_attempted`) so a genuine post-purge empty canonical is trusted
  as honest absence instead of silently re-falling-back to the still-contaminated legacy shard, + 6 unit tests. Full
  detail + the newly-split follow-up todos in
  `issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md`. **Still declining
  to flip this checkbox**: the reader/writer mismatch that blocked part (a) is now fixed, but the actual purge
  (`reprocess_sports_odds.py --force` against the reconciled dates) has not been re-run and `verify_ml_readiness.py` has
  not been re-verified — those remain open todos in the issue doc, tracked separately rather than force-completing this
  checkbox on partial progress.
- **2026-08-09 (slot 26, data_engineering, continued)**: Operator directed continuing to actual completion rather than
  parking. Shipped the sweep script's dual-prefix fix (`market-tick-data-service@926f9b20`/`c2dda59a7`) and re-ran it
  against production: recovers the exact original 2026-07-27 sizing (37 shards / 187 rows / 18 dates, 100% at the legacy
  path shape, 0 at canonical). Ran `reprocess_sports_odds.py --force` per-day against all 18 dates (2025-07-31 →
  2025-11-13); manifest-verified all 18 now carry a coarse `odds_horizon_bucket` row (`capture_status=captured`);
  spot-verified `features-service.gcs_reader.read_bucketed_odds('2025-09-02')` now returns 0 rows (previously silently
  served the 3 zombie RUSSIA_PREMIER_LEAGUE rows). Re-ran
  `verify_ml_readiness.py --start-date 2025-09-01 --end-date 2025-11-30 --bucket features-sports-prd-central-element-323112`:
  **the 17-date failure set cleared to 0 FAILED** (88/91 dates passed, Gate met: YES). Part (c) (gate-semantics fix)
  remains superseded per the prior entry's finding — untouched, tracked in `sports_taxonomy_p3_consumers_2026_08_08.md`.
  **Flipping this checkbox** — parts (a) and (b) as literally worded are genuinely done. One honest caveat: 3 of the 18
  purged dates (2025-10-23, 2025-11-11, 2025-11-13) report MISSING rather than FAILED in the verify output (no
  `odds_features` export exists at all for them, a distinct downstream gap unrelated to the zombie-tick contamination
  this todo targets) — NOT "genuine honest-absence" as the plan anticipated for the remainder; filed as its own new P2
  todo in the issue doc rather than silently absorbed into this checkbox's evidence or left uninvestigated. Full
  evidence trail: `issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md`.
