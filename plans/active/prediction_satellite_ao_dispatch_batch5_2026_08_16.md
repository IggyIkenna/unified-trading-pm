---
doc_type: plan
title: Prediction satellite AO batch 5 — batch4's remaining Deferred-section residue (2 gate-cleared items + 1 untracked investigation)
summary: >-
  Extracted from `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s archival-prerequisite audit
  (`plans/active/issues/prediction_batch4_deferred_migration_and_archival_2026_08_14.md`), 2026-08-16. batch4 reached
  0 open top-level todos 2026-08-14 but carried four "Deferred" sections whose content had to be triaged before
  archival (per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 1) — evaporating a deferred
  item with the archived plan is itself a defect. Per-item disposition: the cqg recent-window re-enumeration item was
  already `[x]` done in batch4's own body (todo, line ~166); the politics/geo canonicalization item was already `[x]`
  done via `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s `[UAC] P2` todo; the tarball-overwrite-race item
  is still a live open NA design question already tracked at its source
  (`prediction_cross_venue_arb_and_coverage_2026_07_24.md`) plus a concrete instance doc
  (`issues/dp_vm_001_mdps_backfill_cefi_tarball_race_relaunched_2026_08_15.md`); the Kalshi historical mid-gap backfill
  is still tracked live at its source doc (`prediction_cross_venue_arb_and_coverage_2026_07_24.md`, `[SCRIPT] P1`);
  the Polymarket-perps-parked item is intentionally frozen (`BLOCKED-UPSTREAM`, no public API) in its own archived
  doc — none of these five need a new home. Three items had NO live home anywhere else and are extracted here: two
  were explicitly marked "Batch5 candidate" by batch4's own Progress Log (the combined `_index` manifest
  canonicalisation single-walk leg (a), and the IS POLYMARKET re-enumeration → `book_snapshot_5` backfill proof), plus
  one genuinely-untracked data-investigation gap found during this audit (the 49 canonical-only POLYMARKET trades days
  missing `title`/`slug`/`event_slug`). `status: draft` — a skill/audit-drafted AO batch is never auto-shipped;
  flipping to `active` to dispatch is an operator decision (CLAUDE.md "Plan destination — ASK BEFORE CREATING").
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-5, satellite-docs, deferred-extraction]
related:
  [
    /plans/archive/2026_08/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/archive/2026_08/issues/prediction_batch4_deferred_migration_and_archival_2026_08_14.md,
  ]
created: "2026-08-16"
last_updated:
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
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
  prediction_batch4_deferred_migration_and_archival_2026_08_14.md's archival-prerequisite audit — per-item
  disposition check across batch4's four Deferred sections, run to unblock the promote_qg_failure wall on PR #3244
  (escalation agt-63ec32) which required batch4's archive-candidate status resolved.
sequential: false
drift_direction: advance-code
---

# Prediction satellite AO batch 5 — batch4's remaining Deferred residue

`status: draft` — do not dispatch until an operator flips this to `active`.

## Todos

- [ ] [OPERATOR][DATA] P2. **Combined prediction `_index` manifest canonicalisation single-walk — leg (a) only
      remaining.** Reclassify the ~38,020 out-of-lifecycle POLYMARKET `empty_confirmed` rows to honest absence
      (lifecycle bounds already populated per batch4 todo #1) and audit whether the `SOURCE_RETURNED_ZERO` rows
      (1,953,482 live count) include out-of-lifecycle dates. Legs (b) lowercase/blank/UNKNOWN venue and (c) v4→v9
      schema re-walk are ALREADY RESOLVED (both measured at 0, 2026-08-07 finalize count) — do not re-derive them.
      `[OPERATOR]`: a manual manifest `--apply` flips real captured→attempted_failed on a false positive
      (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`), human review/execution required. Source:
      `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (P2/P3 residual-manifest items), extracted via
      `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s "Deferred — gated on a sibling todo landing" section
      (gate cleared 2026-08-07, `instruments-service@3617261f`). Repo: instruments-service. Done when: leg (a)'s
      38,020-row reclassification + the `SOURCE_RETURNED_ZERO` out-of-lifecycle scope audit are both complete, with
      live counts cited.
- [ ] [DATA] P3. **Re-enumerate the IS POLYMARKET universe for a recent past date (e.g. 06-22) → re-run the
      `book_snapshot_5` batch backfill for that date → verify `row_count>0`.** NICE-TO-HAVE — live `book_snapshot_5`
      already captures end-to-end; this only proves the batch path on a historical date whose IS parquet predates the
      `clob_token_ids` column. Bounded, idempotent, no operator gate (re-tagged off `[OPERATOR]` 2026-07-28 — the
      shard re-runs cleanly on preemption, satisfying CLAUDE.md's VM-launch safe-idempotent OR-clause). Repo:
      instruments-service (re-enumerate) + deployment-service (re-launch backfill). Source:
      `prediction_live_clob_depth_capture_2026_07_24.md` (its cross-dependency-deferred todo, `na-eligibility-audit
      2026-08-06` citation), extracted via `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s Deferred section
      (gate cleared 2026-08-07). Done when: the re-enumerated parquet carries populated `clob_token_ids` for the
      chosen date AND the re-run `book_snapshot_5` backfill for that date shows `row_count>0`.
- [ ] [DATA] P3. **Investigate whether the 49 canonical-only POLYMARKET `trades` days
      (2025-04-19..2025-06-05 + 2025-06-13) missing `title`/`slug`/`event_slug` are recoverable from the IS POLYMARKET
      reference universe / `prediction_canonical_question_group` / `market_lifecycle`.** These days sit OUTSIDE the
      348-date legacy bundle 4b-i enriched from (no `prediction_trades` legacy objects exist for them), so the
      legacy-enrich path cannot cover them. Sampled 2026-08-06 (4 days: 2025-04-19/05-15/06-05/06-13): canonical
      `data_type=trades` objects carry 46-141 shards/day, all `enrichment_fields_present=False`.
      `market_lifecycle` covers these dates per the manifest census, making recovery plausible but unverified.
      Genuinely untracked elsewhere (grep-confirmed 2026-08-16, no other live doc mentions this date set). Repo:
      instruments-service. Source: `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s own 4b-i scope note
      (P3, non-batchable at the time). Scratchpad evidence: `legacy_presence.json` + `audit_remaining_days.py` at
      `gs://market-data-tick-pred-prd-central-element-323112/_ops/4bi_scratchpad_2026_08_06/`. Done when: a
      recoverability verdict is recorded per-field (title/slug/event_slug), and if recoverable, either the fix ships
      or a follow-up `- [ ]` todo is filed citing the exact backfill approach.

## Progress Log

- 2026-08-16 (quality_gate_resolution firefighter, escalation agt-63ec32): drafted while resolving the
  `promote_qg_failure` wall on PR #3244 — `check_archive_candidates.sh` flagged batch4 (0 open todos, unlocked) as a
  new done-but-unarchived doc, and its own filed prerequisite issue
  (`prediction_batch4_deferred_migration_and_archival_2026_08_14.md`) required this per-Deferred-item disposition
  audit before archival could proceed safely. `status: draft` per the autonomous-mode safety rail — operator flips to
  `active` to dispatch.
