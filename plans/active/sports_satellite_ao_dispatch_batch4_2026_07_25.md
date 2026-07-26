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
priority: P1
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

- [ ] [DATA] P1. **Verify footystats MATCHES/PREDICTIONS/ODDS `pending_fetch` is still 0 and close the stale todo #4
      checkbox in this issue doc.** Read the live `_index/availability_index.parquet` (single-walk discipline,
      shard-merged via `_merge_shard_frames`, same dedup key the reader/consolidator use) and confirm
      `(footystats,     MATCHES)` + `(footystats, PREDICTIONS)` + `(footystats, ODDS)` `pending_fetch == 0` still holds.
      This was already verified 0 on 2026-07-12 per the now-archived
      `plans/archive/2026_07/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md` (`status: complete`,
      `instruments-service@e54ffc2a`'s `footystats_residual_closer_2026_07_12.py`, run to completion, explicitly citing
      THIS issue doc's own todo #4 as the closing mechanism) and item #7 (the cross-source VERIFY gate, also closed
      2026-07-12) — the underlying work already happened under a different plan's task dispatch, so this doc's own
      checkbox was never flipped to match. **Conflict-check clearance (2026-07-25 re-check):** the flagged conflict was
      `sports_consolidated_closeout_2026_07_19.md`'s own "Sports P2b" line (still reads "reference sources ... never
      started", inherited unedited from the superseded top-level coordinator) — provably stale for footystats
      specifically, per the archived plan's `status: complete` + explicit closing citation (re-verified current
      2026-07-25: archived plan still `status: complete`, this doc's todo #4 still `[ ]`, no drift). Do NOT re-run the
      typing pass or re-dispatch a backfill VM as a first move — that would only reproduce/waste-spend on an
      already-closed residual per this doc's own documented lesson. A single fresh manifest read is sufficient to
      confirm no regression. If the fresh read confirms zero across all three, flip this doc's own
      `- [ ] [DATA] P2. BLOCKED-PREREQUISITES ... Re-verify + re-dispatch footystats backfill VM after the above land`
      checkbox to `[x]`, citing both the fresh read and the 2026-07-12 archived-plan evidence chain, and flip this doc's
      frontmatter `status: open` → `status: resolved`. If the fresh read instead shows a genuine regression, do NOT
      silently re-close the checkbox — report the regression as a distinct new finding per the findings-triage rule
      instead of papering over it. (repo: unified-trading-pm doc edit; read-only manifest check against
      instruments-service sports data, no code change expected either way). **Done when**: a live manifest read is
      recorded showing the current (footystats, MATCHES/PREDICTIONS/ODDS) `pending_fetch` counts, AND either (a) all
      three read 0 and this doc's todo #4 checkbox + frontmatter `status` are flipped citing both the fresh read and the
      2026-07-12 archived-plan evidence, or (b) a nonzero count is found and filed as its own new finding (not silently
      re-closed). Source: `issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md`.
- [ ] [REVIEW] P1. **Reconcile the stale last todo in
      `plans/active/issues/fixtures_manifest_legacy_backfill_2026_07_24.md`** — a doc-sync gap, not a real conflict: (1)
      re-run the sanctioned census —
      `deployment-api/scripts/census_manifest_data_type_2026_07_24.py --service instruments-service --asset-group     sports --filter-prefix FIXTURES`
      against bucket `instruments-store-sports-prd-central-element-323112` — and record the current legacy `FIXTURES`
      row count; (2) confirm via `git log` in instruments-service that `e19c5a7a`/`47c1ffb3`/`e92efc78` are the commits
      that already wrote+ran the 1:1 restamp script (282,231/337,464 rows restamped, 55,233 dedup-collision residual) —
      do NOT write or run a new restamp script, the action this doc's last checkbox describes is already shipped in
      production; (3) edit the doc's last `[DATA] P0` todo: change it from an open action-item to a status note stating
      the restamp action shipped (cite the 3 SHAs) and the Done- when (census-zero) remains genuinely unmet purely
      because of the 55,233 residual rows, which are tracked and gated on a human delete-vs-leave decision entirely in
      the sibling doc `plans/active/issues/fixtures_manifest_duplicate_collision_residual_2026_07_24.md`; (4) leave
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
- [ ] [DIAG] P1. **market-tick-data-service: sweep the manifest-driven `odds_horizon_bucket` index to size the extent of
      the stale/zombie-tick contamination that predates the now-confirmed-shipped 2026-07-25 staleness-cap fix
      (`market-data-processing-service@aa6e8ac`, verified via `git log` — added `STALENESS_CAP_SECONDS`/
      `KICKOFF_PAST_CAP_SECONDS` to `_prepare_tick_data()`, 67/67 tests pass).** Scan
      `processed/by_date/*/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/data_type=odds_horizon_bucket/`
      — via the availability-manifest index (single-walk discipline; no fresh whole-corpus GCS walk) — for repeated
      `(fixture_id, bookmaker_key, kickoff_utc)` tuples spanning multiple `day=` partitions. Classify each hit using the
      doc's own already-specified discriminator: zombie (`staleness_seconds` = `fetch_utc − bm_time`, or
      `|fetch_utc − kickoff_utc|`, years-scale) vs. genuine single-snapshot real fixture (≤~26h) — do NOT flag the
      real-fixture class (e.g. the 2025-10-23 China Superleague pair) as contamination. Read-only: produce a report
      only, do NOT delete, overwrite, or re-derive any GCS object or manifest row. **Conflict-check clearance
      (2026-07-25 re-check):** the flagged conflict was `sports_consolidated_closeout_2026_07_19.md`'s own Track O
      "T-12h↔T-24h dead-zone / widen the T-24h staleness cap" item (line 494-496, still `[ ]` open, re-verified
      2026-07-25) — this is a DIFFERENT cap in a DIFFERENT file/mechanism entirely (Track O's is a per-horizon-target
      deviation cap in `bucket_assignment_adapter.py`'s TIER1_HORIZONS spacing logic; this todo's is the already-shipped
      fetch-based `STALENESS_CAP_SECONDS` zombie-tick rejection). This candidate is read-only and touches neither Track
      O's target file nor its mechanism, so it cannot regress or race that still-open item — provably no overlap, not
      just "not literally the same fix." NOTE FOR THE DISPATCHED WORKER: do not conflate the two staleness caps in your
      report — explicitly name which one you mean if the term comes up. (repo: market-tick-data-service, new read-only
      scan script; reads market-data-tick-sports-prd + the sports availability-manifest index only). **Done when**: a
      written report (scratchpad or a new read-only script under market-tick-data-service) cites total contaminated
      `day=` shard/row counts, the affected `league_id` list, and the zombie/genuine split for the 7 named control dates
      (Russia-Premier-League 2025-09-02/03/09, 10-07, 11-11; Australia-A-League 09-03/09-09; the 2025-10-23 real-fixture
      control), with the 2025-10-23 pair correctly excluded from the contamination count. Source:
      `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`.

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
