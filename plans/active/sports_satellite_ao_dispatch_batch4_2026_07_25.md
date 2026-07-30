---
doc_type: plan
title: Sports satellite AO batch 4 — conflict-recheck extraction from batch3's Deferred section
summary: >-
  Fourth AO-dispatch batch for sports, produced by the `/ag-closeout-audit` skill's "batchN methodology" (iterative
  drain): re-checks batch3's own `## Deferred — conflict-gated` section (6 docs, 7 AO-eligible candidates, 2026-07-25)
  against CURRENT state rather than running a fresh Phase-1/Phase-3 triage. 3 of the 7 candidates clear (their flagged
  conflict is either provably stale/superseded or provably non-overlapping with the still-open master-plan ground it was
  checked against); the other 4 remain genuinely conflicted and are queued as fresh operator-decision entries
  (`autonomous_session_operator_decisions_2026_07_25.md` #5-8) rather than silently drafted or dropped. No new Phase-1
  triage ran — batch2 (28/37 done, still in flight) and batch3 (draft, undispatched) were checked and neither touches
  any of the 7 candidates' ground, so nothing they've shipped changed the verdicts below beyond what's cited per item.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, deployment-api, market-tick-data-service]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-4, satellite-docs, conflict-recheck]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  ag-closeout-audit skill's "batchN methodology" section (added 2026-07-25) — step 1 re-check of
  sports_satellite_ao_dispatch_batch3_2026_07_25.md's own Deferred section, run before any fresh Phase-1 triage per the
  skill's iterative-drain instructions.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Sports satellite AO batch 4 — conflict-recheck extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review. All 3 todos below are same-priority and touch distinct files/docs (verified individually per todo) so
> they are safe to dispatch concurrently once activated.

## Todos

- [x] ✅ [DATA] P1. **DONE 2026-07-27 (data_engineering slot) — outcome (b): genuine regression found, NOT silently
      re-closed.** A fresh single-walk read of `_index/availability_index.parquet` shows the 2026-07-12
      zero-verification no longer holds: `(footystats, MATCHES)` pending_fetch=35,151, `(footystats, PREDICTIONS)`
      pending_fetch=35,151, `(footystats, ODDS)` pending_fetch=35,349. Root-caused (not just reported): the sports
      canonical universe grew to include ~300+ additional footystats-non- covered leagues since the last typing pass;
      the existing non-covered-league typing scripts
      (`type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py`,
      `type_footystats_odds_non_covered_leagues_2026_06_29.py`) haven't been re-run against the larger universe — live
      dry-run of both confirms they'd close 105,370 of the 105,651-row live total (99.7%). NOT a regression of the
      2026-07-08 write-path fixes (still correct/unaffected). Per this todo's own instruction,
      `footystats_matches_predictions_fetch_gaps_2026_07_08.md`'s todo #4 checkbox + `status: open` are left UNCHANGED
      (not silently re-closed) — filed as its own actionable finding:
      `issues/footystats_matches_predictions_odds_pending_fetch_universe_expansion_2026_07_27.md` (4 todos: re-run both
      existing typing scripts with `--apply`, root-cause the small ~281-row remainder, then re-verify + close out the
      source doc's todo #4). unified-trading-pm doc-only change, no code touched either repo.
- [x] ✅ [REVIEW] P1. **DONE 2026-07-26 (slot-5, review) — plus a genuine NEW finding+fix beyond the doc-sync scope.**
      Reconcile the stale last todo in `plans/active/issues/fixtures_manifest_legacy_backfill_2026_07_24.md` — a
      doc-sync gap, not a real conflict: (1) re-run the sanctioned census —
      `deployment-api/scripts/census_manifest_data_type_2026_07_24.py --service instruments-service --asset-group     sports --filter-prefix FIXTURES`
      against bucket `instruments-store-sports-prd-central-element-323112` — and record the current legacy `FIXTURES`
      row count; (2) confirm via `git log` in instruments-service that `e19c5a7a`/`47c1ffb3`/`e92efc78` are the commits
      that already wrote+ran the 1:1 restamp script (282,231/337,464 rows restamped, 55,233 dedup-collision residual) —
      do NOT write or run a new restamp script, the action this doc's last checkbox describes is already shipped in
      production; (3) edit the doc's last `[DATA] P0` todo: change it from an open action-item to a status note stating
      the restamp action shipped (cite the 3 SHAs) and the Done- when (census-zero) remains genuinely unmet purely
      because of the 55,233 residual rows, which are tracked and gated on a human delete-vs-leave decision entirely in
      the sibling doc `plans/archive/issues/fixtures_manifest_duplicate_collision_residual_2026_07_24.md`; (4) leave
      `status: open` on this doc (do not resolve it) until that sibling doc's todo closes — add a dated Update section
      recording this reconciliation pass. **Conflict-check clearance (2026-07-25 re-check):** the flagged "conflict"
      against `sports_consolidated_closeout_2026_07_19.md`'s own Track C1 (checked `[x]`, already documents the
      identical restamp with identical figures) was explicitly NOT a differing-approach conflict — both docs already
      agree on facts, this doc's own checkbox text was just never updated to match; re-verified 2026-07-25 the checkbox
      is still unedited (`last_updated: 2026-07-24`, no drift since). (repo: unified-trading-pm doc edit + read-only
      census run via deployment-api script). **Done when**: the census script has been re-run against prod with output
      recorded in the doc; the doc's last todo/checkbox text is updated to reflect action-shipped-but-Done-when-blocked
      status with the 3 commit-SHA citations and a cross-link to
      `fixtures_manifest_duplicate_collision_residual_2026_07_24.md`; a dated `## Update (2026-07-25)` section is added;
      no restamp script is written or re-run (docs-only change, zero production mutation) and `status: open` is left
      unchanged. Source: `issues/fixtures_manifest_legacy_backfill_2026_07_24.md`.

      **Evidence + a genuine new finding beyond scope**: re-ran the census live — `FIXTURES` is 100,801 (NOT the
                                                                              expected stable 55,233), because it's actively GROWING: 44,889 of the 100,801 rows were written TODAY
                                                                              (2026-07-26, single burst ~01:30 UTC) via `enumerator_run_id='enum-universe-sports-20260726-013031'` —
                                                                              the sports expected-universe enumerator (`enumerate_expected_universe.py`) has a 10th, previously-missed
                                                                              call site that seeds legacy `"FIXTURES"` `expected_unattempted` rows (its `_SPORTS_MANIFEST_DATA_TYPE_OVERRIDE`
                                                                              map had `ODDS_HORIZON_BUCKET` but no `FIXTURES` entry). This is a genuine, small, clear root-cause fix
                                                                              (one dict entry, directly analogous to the existing pattern) — fixed inline (not just documented) per
                                                                              findings-triage: added `"FIXTURES": "FIXTURES_SCHEDULE"` to the override map + a regression test (184/184
                                                                              pass) — `instruments-service@ca8bd7b3ab`. Full writeup + census output in the target doc's new
                                                                              `## Update (2026-07-26)` section (the doc's original `[DATA] P0` todo also flipped `[x]` citing the 3 SHAs).

- [x] ✅ [DIAG] P1. **DONE 2026-07-27 (data_engineering slot-10) — market-tick-data-service@76ca401f.** Sweep executed
      via a new read-only script
      (`market-tick-data-service/scripts/sweep_sports_odds_horizon_bucket_zombie_contamination_2026_07_27.py`):
      manifest-driven (single bounded `read_availability_index()` read, zero fresh corpus walk), then a bounded
      day-scoped `list_blobs` per in-scope `day=` partition (PATH DISCOVERY, not construction — live-confirmed the
      manifest's own `league_id` column value does NOT reliably match the real GCS path segment for this data_type, e.g.
      manifest `soccer_russia_premier_league` vs. real path `league_id=RUSSIA_PREMIER_LEAGUE`; both an uppercase
      short-code convention and a lowercase `soccer_x_y` convention coexist as SEPARATE real objects on some days).
      **Scope (deliberate, not silent)**: full sweep of the 17 "sparse" leagues (<=30 distinct captured days — 3,838
      shard rows across 24 distinct `day=` partitions, matching the root-cause mechanism: a board only goes idle/frozen
      when nobody is fetching fresh markets for it). The 26 actively-fetched leagues (114,015 shard rows, 85–996
      distinct days each, consistent daily volume — the opposite signature of a frozen board) were explicitly NOT swept
      this pass; a full-corpus sweep is ~118k GCS-object reads, squarely HEAVY I/O belonging on a dedicated VM per
      CLAUDE.md, not an interactive DIAG task — recommend a follow-up VM-run full sweep if population-wide certainty
      across all 43 leagues is ever needed. **Findings**: `RUSSIA_PREMIER_LEAGUE` zombie CONFIRMED STILL LIVE, spanning
      18 distinct `day=` partitions (wider than the 5 originally documented) — 3 bookmakers
      (bovada/williamhill/pinnacle) × 18 days = 54 contaminated rows / 20 contaminated shards, `staleness_seconds`
      ≈1349.8 days (≈3.7 years, using the shard's own materialised `staleness_seconds` column, no recompute needed).
      `AUSTRALIA_ALEAGUE`'s originally-documented zombie instance is NO LONGER PRESENT — live-verified
      `object_present     = False` for both control dates (2025-09-03, 2025-09-09); already resolved by intervening work
      between the 2026-07-14 diagnosis and this sweep. `CHINA_SUPER_LEAGUE` 2025-10-23 genuine-fixture control correctly
      EXCLUDED — object present, 0 repeated/zombie rows attributed to that league. Downstream P2 (purge/re-derive the
      contaminated `RUSSIA_PREMIER_LEAGUE` shards) is unblocked by this sizing but NOT started this pass (read-only DIAG
      scope only — zero GCS objects or manifest rows deleted/overwritten/re-derived). Source:
      `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`.

- [x] ✅ [DECISION] P2. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — see
      `/plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md` entries #5-8 (all now Status: resolved)
      and `/plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md` (wider-corpus re-audit).** **Resolve the 4
      still-conflict-gated candidates + the 2 still-excluded docs below** — the "Deferred — still genuinely
      conflict-gated" section (4 candidates, queued as operator-decisions entries #5-8) and the 2
      `doc_too_large_or_risky_for_batch` docs
      (`sports_canonical_universe_and_apifootball_reference_expansion_     2026_06_24.md`,
      `issues/sports_features_layer_findings_sweep_2026_07_18.md`) remain genuinely unresolved and were never converted
      into dispatchable todos here.

- [x] ✅ [REVIEW] P2. **DONE 2026-07-30 — filed `sports_satellite_ao_dispatch_batch8_2026_07_30.md` + `..._finalize`
      (both `status: draft`).** Read both docs in full (note: batches 5-7 already shipped in the interim, un-noticed by
      this todo's stale "checked batch5/batch5_finalize" text — re-verified neither doc appears in
      batch6/batch7/native_ao_extract either before drafting).
      **`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`: 0 new AO-eligible candidates**
      (confirmed fresh, not just re-cited) — every remaining item is either already `BLOCKED-OPERATOR`-tracked, a
      genuine scope-overlap conflict with the consolidated closeout's own separate dual-layout todos (parked in batch8's
      Deferred), or an explicit design/curation judgment call gated on the closeout's own unmade
      fold-in-vs-keep-satellite decision. **`issues/sports_features_layer_findings_sweep_2026_07_18.md` (PART 1 of 3 —
      parts 2/3 already fully reconciled by batch6): 5 candidates extracted** (a bucketing-bug root-cause, a
      cross-asset-group junk-symbol-guard false-positive fix cross-referenced against
      `instruments_foundation_phase0_cross_cutting_2026_07_24.md`'s stale G1.4, an Odds-API historical-backfill adapter,
      a bounded verify-or-rescope check, and a canonical-naming audit extension) **+ 3 items reconciled directly in the
      source doc as already resolved/duplicated elsewhere** (live in-play connector already shipped+running; a
      distinct-dimension-values UI listing already tracked generically in
      `prediction_phase_c_data_status_ui_2026_07_24.md`; the manifest-staleness DIAG already root-caused in
      `issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md`) — `unified-trading-pm@(this commit)`. Both
      new plans are `status: draft` per the skill's autonomous-mode rule; flipping to `active` is an operator decision,
      tracked as a follow-up, not auto-flipped.

## Deferred — still genuinely conflict-gated (re-checked 2026-07-25, NOT dispatched)

4 of the 7 candidates batch3 deferred remain genuinely conflicted after this re-check — none of the competing
master-plan ground they collide with has shipped/superseded/resolved, and none is provably non-overlapping the way the 3
todos above are. Each is now written up as a full operator-decision entry (previously only pointed at, per batch3's own
text, but never actually drafted) in `plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md`:

- **`data_completion_sports_2026_07_24.md` — Transfermarkt golden-window re-attempt (256 cells)**: conflicts with the
  still-open "Sports P2b" full-history-extension todo. See operator-decisions doc entry **#5**.
- **`data_completion_sports_2026_07_24.md` — ODDS+PREDICTIONS blank-reason golden-window measurement**: conflicts with
  the still-open, still-BLOCKED-PREREQUISITES "R1/R2/R3 final zero-missing gate" (0-blank-reason criterion). See
  operator-decisions doc entry **#6**.
- **`sports_legacy_fixtures_path_migration_2026_07_24.md` — the 2,319-date fixtures-path census**: 3 conflicts, all
  still open (Track S legacy-write-path elimination, Track E stale-consumer repoint, Track C1's 55,233-row dedup-
  collision residual still pending an un-ruled operator DELETE-policy decision). See operator-decisions doc entry
  **#7**.
- **`issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md` — STANDINGS/TEAMS/XG/MATCHES/FIXTURES phantom
  spot-check**: may share a root cause with Track S2's still-open "decision 16" day-partition investigation; genuine
  ambiguity, not resolvable from evidence alone. See operator-decisions doc entry **#8**.

Once the operator rules on entries #5-8, re-check per the same methodology this batch used — any that clear become a
`batch5` (or later) todo; this doc's own finalize plan's todo 2 should run that re-check first, same as this batch's
todo 1 did for batch3.

Also still deferred entirely (unchanged from batch3, no new evidence found this pass — flagged
`doc_too_large_or_risky_for_batch` by the original 2026-07-25 triage, need their own dedicated triage/design pass, not a
blind extraction or a re-triage re-check): `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`
(0 AO-eligible found anyway — all 8 remaining items are human-only design/operator-sign-off work) and
`issues/sports_features_layer_findings_sweep_2026_07_18.md` (the 73-todo sweep doc — 6 AO-eligible candidates found but
6 conflicts too, including a MAJOR overlap with the K-series UPPER-case migration operator decision already tracked in
the master plan). These were explicitly excluded from this batch's scope per the operator's 2026-07-25 instruction to
leave them out until they get a dedicated pass.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via the companion
`sports_satellite_ao_dispatch_batch4_finalize_2026_07_25.md`
(`depends_on: [sports_satellite_ao_dispatch_batch4_2026_07_25]`

- `gate_on_depends: true`), mirroring `sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md`'s pattern — whose own
  todo 2 re-checks the 4 still-conflict-gated Deferred items above once the operator rules on entries #5-8.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc. The
`/ag-closeout-audit` skill's "batchN methodology" section (`cursor-configs/skills/ag-closeout-audit/SKILL.md`) is the
SSOT for the re-check-before-fresh-triage procedure this plan followed.
