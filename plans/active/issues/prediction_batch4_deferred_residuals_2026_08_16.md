---
doc_type: issue
title: >-
  prediction_satellite_ao_dispatch_batch4 archival — the 2 Deferred items with genuinely no tracked home elsewhere
summary: >-
  `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` reached zero open top-level todos 2026-08-14 and is being
  archived per `/plans/archive/2026_08/issues/prediction_batch4_deferred_migration_and_archival_2026_08_14.md` todo 1 (audit
  its 4 "Deferred" sections before the archival move, per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 1 — a deferred item must not evaporate with
  the archived plan). Cross-checking each Deferred bullet against the live corpus found 5 of 7 already have a tracked
  home: the fixture-pairing residual and the politics/geo cross-venue canonicalization audit are both `[x]` complete
  in `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` (lines 517, and the fixture-pairing team-alias-table
  follow-up); the tarball-overwrite race and the series-scoped historical Kalshi enumeration are both still live
  open items in `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (confirmed via that doc's own
  na-eligibility-audit 2026-08-08/09 Progress Log entries, "2 open" citing exactly these two, lines ~172/380); the
  Polymarket historical-date `book_snapshot_5` row-proof is `[x]` complete in
  `prediction_live_clob_depth_capture_2026_07_24.md` (line 247); and `prediction_perps_kalshi_polymarket_parked_2026_07_24.md`
  is itself `status: complete`. Only 2 genuinely have no other tracked home — this doc gives them one.
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [prediction, archival, plan-hygiene, deferred-migration, manifest, ao-dispatch]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/issues/prediction_batch4_deferred_migration_and_archival_2026_08_14.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-16
author: claude-agent
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_honest_coverage_empty_reasons.py,
  ]
source:
  [
    "prediction_satellite_ao_dispatch_batch4_2026_07_26.md \"Deferred — gated on a sibling todo landing\" + \"Deferred
    — time-gated\" sections",
    "prediction_batch4_deferred_migration_and_archival_2026_08_14.md todo 1 (this doc's own trigger)",
  ]
---

# prediction batch4 archival — the 2 un-migrated Deferred residuals

## What I found

Full per-bullet disposition of `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s 4 Deferred sections:

| Item                                                                 | Disposition                                                                             |
| --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Fixture-pairing residual (team-alias tables)                          | Already tracked + partially shipped in `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` — no action needed. |
| Politics/geo cross-venue canonicalization audit                       | `[x]` ✅ COMPLETE in `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` line 517 — no action needed. |
| `[OPS]` tarball-overwrite race (concurrent fleet tarball clobber)      | Still a live open item in `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (confirmed via that doc's own 2026-08-08/09 na-eligibility-audit notes) — no action needed, already has a home (mis-tagged `prediction` there rather than `infra`/`ci`, a pre-existing tagging note in that doc, not new). |
| Series-scoped historical Kalshi enumeration (2025-10→2026-04 mid-gap) | Still a live open item in `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (same audit note) — no action needed. |
| `prediction_perps_kalshi_polymarket_parked_2026_07_24.md` BLOCKED-UPSTREAM | Doc's own `status: complete` — no open item remains. No action needed. |
| Polymarket historical-date `book_snapshot_5` row-proof                | `[x]` ✅ COMPLETE in `prediction_live_clob_depth_capture_2026_07_24.md` line 247 — no action needed. |
| `[OPERATOR][DATA]` `_index` manifest single-walk (out-of-lifecycle reclassification) | **Genuinely untracked elsewhere** — migrated below. |
| `[DATA] P3.` 49 canonical-only POLYMARKET `trades` days lacking `title`/`slug`/`event_slug` | **Genuinely untracked elsewhere** — migrated below. |

## Todos

- [ ] [OPERATOR][DATA] P2. **Prediction `_index` manifest canonicalisation — reclassify the remaining 38,020
      out-of-lifecycle POLYMARKET `empty_confirmed` rows to honest absence** (legs (b) lowercase/blank/UNKNOWN venue
      and (c) schema-v4 rows are already resolved = 0, per batch4's 2026-08-07 finalize count — only leg (a)
      remains). A manual manifest `--apply` write — reserved for human review per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (a false positive would silently mark good captured
      data as failed). Repo: unified-trading-pm (manifest) + market-tick-data-service (source of the lifecycle
      bounds). Source: `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s "Deferred — gated on a sibling todo
      landing" section (gate cleared 2026-08-07, `instruments-service@3617261f`). Done when: a fresh manifest read
      confirms the 38,020-row out-of-lifecycle `empty_confirmed` population reclassified to the honest
      `EXPECTED_INSTRUMENT_NOT_LISTED`/`DELISTED` reasons, with the new count cited.
- [ ] [DATA] P3. **Investigate whether the 49 canonical-only POLYMARKET `trades` days (2025-04-19..2025-06-05 +
      2025-06-13, outside the 348-date legacy-bundle range) can recover `title`/`slug`/`event_slug` from the IS
      POLYMARKET reference universe** (`prediction_canonical_question_group`/`market_lifecycle`, which the manifest
      census confirms covers these dates) rather than from the legacy `prediction_trades` bundle (which does not
      exist for these days). Repo: unified-api-contracts + instruments-service (read path) +
      market-tick-data-service (enrichment script, if recoverable). Source:
      `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s 2026-08-06 finding (46-141 shards/day sampled, all
      `enrichment_fields_present=False`; evidence at
      `gs://market-data-tick-pred-prd-central-element-323112/_ops/4bi_scratchpad_2026_08_06/`). Done when: a dated
      verdict is recorded (recoverable — with the recovery mechanism identified — or genuinely not recoverable from
      any live source), committed to this doc's Progress Log.

## Progress Log

- 2026-08-16 (cicd escalation agent, slot 3, agt-8b735e): filed while executing
  `prediction_batch4_deferred_migration_and_archival_2026_08_14.md`'s todo 1 (dispatched here as part of resolving
  the `check_archive_candidates` CI ratchet blocking `live-defi-rollout`). Cross-checked all 4 Deferred sections
  against the live corpus (see table above) — 5 of 7 items already tracked elsewhere, 2 genuinely orphaned and
  migrated here as real `- [ ]` todos.
- **context-scout 2026-08-16**: populated context_scope (2 entries).
