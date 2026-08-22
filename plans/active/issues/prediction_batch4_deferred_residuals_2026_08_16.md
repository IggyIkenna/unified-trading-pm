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
  follow-up); the tarball-overwrite race is a still-live open item in
  `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (confirmed via that doc's own na-eligibility-audit
  2026-08-08/09 Progress Log entries); the series-scoped historical Kalshi enumeration was separately extracted +
  closed via `prediction_satellite_ao_dispatch_batch9_2026_08_09.md` (archived, `instruments-service@3f2ddca0` +
  `e2e-testing@5e2f90e` — **this summary field corrected 2026-08-18 (plan_reconciler)**: it previously repeated the
  same stale "still open in cross_venue_arb_and_coverage" claim the body table below already corrected on
  2026-08-17; the frontmatter just hadn't been updated to match); the
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
last_updated: "2026-08-21"
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
    plans/archive/2026_08/prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
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
| Series-scoped historical Kalshi enumeration (2025-10→2026-04 mid-gap) | Extracted + closed via `prediction_satellite_ao_dispatch_batch9_2026_08_09.md` (archived) — `instruments-service@3f2ddca0` + `e2e-testing@5e2f90e` — no action needed. **Corrected 2026-08-17 (plan_reconciler)**: this row previously cited `prediction_cross_venue_arb_and_coverage_2026_07_24.md`, which no longer carries this item (verified via its current 2 open todos: tarball-race + fixture-pairing residual, neither Kalshi-related). |
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
- [x] [DATA] P3. **Investigate whether the 49 canonical-only POLYMARKET `trades` days (2025-04-19..2025-06-05 +
      2025-06-13, outside the 348-date legacy-bundle range) can recover `title`/`slug`/`event_slug` from the IS
      POLYMARKET reference universe** (`prediction_canonical_question_group`/`market_lifecycle`, which the manifest
      census confirms covers these dates) rather than from the legacy `prediction_trades` bundle (which does not
      exist for these days). Repo: unified-api-contracts + instruments-service (read path) +
      market-tick-data-service (enrichment script, if recoverable). Source:
      `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s 2026-08-06 finding (46-141 shards/day sampled, all
      `enrichment_fields_present=False`; evidence at
      `gs://market-data-tick-pred-prd-central-element-323112/_ops/4bi_scratchpad_2026_08_06/`). Done when: a dated
      verdict is recorded (recoverable — with the recovery mechanism identified — or genuinely not recoverable from
      any live source), committed to this doc's Progress Log. **Extracted 2026-08-17 (na-eligibility-audit,
      per-todo RECLASSIFY_SPLIT)** — bounded, worker-determinable investigation with a crisp done-when, no
      `[OPERATOR]` tag, no `depends_on` gate; promoted to `prediction_satellite_ao_dispatch_batch12_2026_08_17.md`
      todo 3. Execution + the dated verdict are now tracked there, not here.

## Progress Log

- 2026-08-16 (cicd escalation agent, slot 3, agt-8b735e): filed while executing
  `prediction_batch4_deferred_migration_and_archival_2026_08_14.md`'s todo 1 (dispatched here as part of resolving
  the `check_archive_candidates` CI ratchet blocking `live-defi-rollout`). Cross-checked all 4 Deferred sections
  against the live corpus (see table above) — 5 of 7 items already tracked elsewhere, 2 genuinely orphaned and
  migrated here as real `- [ ]` todos.
- **na-eligibility-audit 2026-08-17** [body-hash:2a51a9fb2b7eda72]: KEEP-NA, valid — 2 open todos. Todo 1
  ([OPERATOR][DATA] P2, reclassify 38,020 out-of-lifecycle manifest rows) is an explicit human-review-gated manual
  `--apply` manifest write per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (a false positive would
  silently mark good captured data as failed) — genuinely operator-gated. Todo 2 ([DATA] P3, investigate whether 49
  canonical-only POLYMARKET trades days can recover title/slug/event_slug from the IS reference universe) reads as a
  bounded, worker-determinable investigation with a clear done-when — tagging `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` for
  a future pass to promote via per-todo split rather than reclassifying the whole doc off one item. Doc stays NA.

- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries).

- **na-eligibility-audit 2026-08-17 (per-todo RECLASSIFY_SPLIT)** [body-hash:780392485c0f523f]: todo 2 (49-day
  title/slug/event_slug recoverability investigation) promoted — bounded, worker-determinable, no `[OPERATOR]` tag, no
  `depends_on` gate, crisp binary done-when; extracted to `prediction_satellite_ao_dispatch_batch12_2026_08_17.md`
  todo 3, checkbox flipped `[x]` citing the batch. Todo 1 (38,020-row manifest `--apply` reclassification) stays NA —
  confirmed permanent `[OPERATOR]` hard-stop per
  `plans/archive/2026_08/prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md`'s own "manifest `--apply`
  reserved for human execution forever" ruling. Doc stays NA (1 open item remains).
- **na-eligibility-audit 2026-08-18** [body-hash:f3121130a8653f4b]: KEEP-NA, valid -- the 1 remaining open item (manifest --apply reclassification of 38,020 out-of-lifecycle POLYMARKET rows) is a confirmed permanent [OPERATOR] hard-stop per /codex/02-data/gcs-and-manifest-delete-safety-protocol.md and a standing dated ruling in prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md. Doc stays NA.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-21 (prediction tranche)**: KEEP-NA, valid — the 1 remaining open item (manifest
  `--apply` reclassification of 38,020 out-of-lifecycle POLYMARKET rows) re-confirmed a permanent `[OPERATOR]`
  hard-stop per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (a false positive would silently mark
  good captured data as failed) and the standing ruling in
  `prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md`. Not re-litigated. Doc stays NA.
- **D2 execution pass 2026-08-22 (issues_corpus_completion_2026_08_21 dispositions, entry D2 — "Approve all queued,
  individually verified prod manifest/GCS corrections, each under its own stated precondition (retention check /
  fresh dry-run / snapshot-first)")**: dispatched here as `affected_docs[0]`. Re-checked the 1 open todo's stated
  gate FRESH before acting: this item's own precondition, per this doc's Progress Log and
  `prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md`'s 2026-08-07 entry, is **not** one of D2's three
  named precondition types (retention-check / fresh dry-run / snapshot-first) — it is "manifest `--apply` reserved
  for human execution forever," a standing permanent-`[OPERATOR]`-hard-stop ruling independently reconfirmed on
  2026-08-17, 2026-08-18, and 2026-08-21 (the same day as D2). Per
  `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3, a human-only hard stop is "never crossed
  autonomously … on any operator instruction that does not name the specific stop in the same turn" — D2's
  disposition text is generic across 7 sibling docs and names only the three mechanical precondition types above; it
  does not name this item's 38,020-row POLYMARKET reclassification specifically, nor does it assert the required
  human review/execution has occurred. No `--apply` command or script is named anywhere in this doc's chain either
  (consistent with the item genuinely being human-run tooling, not an agent-executable one). **Disposition:
  gate-failed-withheld** — the `--apply` was NOT executed. Todo 1 stays `- [ ]`, doc stays NA, unchanged. This
  withholding is itself the correct/expected outcome for this item, not a stall — see
  `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3 hard-stop #2 framing for why a manifest-correctness
  gate of this shape does not fall under §3a's reversibility carve-out (that carve-out covers GCS object/prefix/
  bucket deletes with a soft-delete undo window, not a manifest reason-code reclassification whose risk is a
  silent false-positive mark on already-captured data, which has no equivalent restore mechanism).

- **2026-08-21 — ruling D2 (Manifest/GCS correction batch)**: OPERATOR-RULED 2026-08-21 — APPROVED ALL under each
  item's stated precondition (retention check / fresh dry-run / snapshot-first). Execute serially, one item per
  verified step, citing the gate result inline. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md
  ledger. Already applied above (2026-08-22 D2 execution pass): this item's own precondition does not match D2's
  three named types, so the `--apply` was correctly withheld; todo 1 stays open, unchanged by this entry.
