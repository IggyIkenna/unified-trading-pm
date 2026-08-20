---
doc_type: plan
title: Sports Track C venue-vocab cleanup dispatch + Track V league_id delete live-writer check
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 4) — two items from
  sports_consolidated_closeout_2026_07_19.md: dispatch Track C's venue-vocabulary cleanup
  (LADBROKES_UK->LADBROKES, SPORT888->BET888SPORT re-stamps, KALSHI/POLYMARKET purge) trusting
  current dispositions, and run a fresh live-writer check on the raw-keyed league_id population
  BEFORE Track V's 5-part-proof-gated DELETE fires, given a sibling doc found a live writer
  re-contaminating a different league-vocabulary population as recently as 2026-08-10.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [sports, canonicalization, venue, league_id, gcs-delete]
related:
  [/plans/active/sports_consolidated_closeout_2026_07_19.md]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 4, 2026-08-16"
locked_by:
context_scope:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/issues/sports_track_v_raw_league_id_delete_5part_proof_status_2026_08_14.md,
    /plans/archive/issues/sports_legacy_league_vocab_recontamination_2026_08_10.md,
  ]
locked_since:
resolved_by:
---

# Sports Track C venue-vocab cleanup + Track V league_id delete live-writer check

## Todos

- [ ] [DATA] P2. Execute Track C's venue-vocabulary cleanup (`sports_consolidated_closeout_2026_07_19.md`):
      LADBROKES_UK->LADBROKES, SPORT888->BET888SPORT re-stamps, and the KALSHI/POLYMARKET purge. Operator ruled
      2026-08-16: trust the current dispositions, no fresh reconfirmation needed despite the doc's history of
      casing/vocabulary reversals — dispatch directly. (repo: market-tick-data-service)
- [x] ✅ [DATA] P1. Before Track V's 5-part-proof-gated DELETE of the old raw-keyed `league_id` GCS objects fires, run a
      fresh live-writer check on THIS population specifically — confirm no live writer is still emitting the
      raw-keyed form. A sibling doc found a live writer re-contaminating a DIFFERENT league-vocabulary population as
      recently as 2026-08-10, so this class of bug is active in this codebase right now; do not assume the existing
      5-part proof already covers a writer that started contaminating after that proof was last run. Only once this
      check comes back clean does Track V's existing delete proceed under its own gate. (repos: instruments-service,
      market-tick-data-service) — **DONE 2026-08-17**: check came back clean, more robustly than the existing proof —
      full detail + evidence on
      `issues/sports_track_v_raw_league_id_delete_5part_proof_status_2026_08_14.md`'s 2026-08-17 Progress Log entry.
      Summary: a fresh path-only GCS scan (`list_stale_raw_league_id_candidates_2026_08_14.py`, read-only) over
      `2026-08-14..2026-08-17` found zero objects of any kind under this population's raw-shaped path — root-caused to
      `venue_fetch.py`'s writer having fully retired `data_type=trades` in favor of `data_type=odds` as of
      `market-tick-data-service@28e2eb36`/`@83a1abbdbf` (2026-08-16,
      `/plans/active/sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md`), independently verified live.
      The sibling doc's live-writer bug (`sports_legacy_league_vocab_recontamination_2026_08_10.md`) is a structurally
      unrelated write path (`instruments-service`'s `api_football_reference.py`, a different bucket) — confirmed via
      direct code read, not assumed. Track V's own delete stays gated on its own separate `[OPERATOR]`
      re-authorization (already filed as a `/blocked` question 2026-08-16) — not executed by this todo, which was
      scoped to the pre-check only.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 4, operator ruling)**: extracted from
  `sports_consolidated_closeout_2026_07_19.md`. Track V's underlying 5-part-proof-gated delete is unchanged by this
  plan — only the pre-check is new.
- **2026-08-17 (slot 27, data_engineering)**: Picked up the P1 live-writer-check todo (the P2 Track C venue-vocab todo
  remains open, not this session's assigned task). See the issue doc's 2026-08-17 Progress Log entry for full
  evidence. Checkbox flipped above.
- **context-scout 2026-08-17**: refreshed context_scope (4 entries) -- added
  `sports_track_v_raw_league_id_delete_5part_proof_status_2026_08_14.md` (where the DONE todo's own evidence actually
  lands, cited directly in this doc's checkbox) and the archived
  `sports_legacy_league_vocab_recontamination_2026_08_10.md` (the sibling doc this plan's own summary cites as
  finding the same-class live-writer bug).
