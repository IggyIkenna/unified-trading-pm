---
doc_type: issue
title:
  _freshness_preflight() builds missing_entities only from `missing`, never from `stale`, so any stale-not-missing
  sports date silently ESCAPES the CLI --sports-entity scope and falls back to the legacy unscoped fetch-everything —
  burning shared singleton-locked API-Football quota (fleet-wide blast radius); a FIXTURES-only backfill VM was measured
  burning ~7000 calls on one date before main stopped it
summary: >-
  On 2026-07-25 a FIXTURES-only backfill (af-backfill-20260725-125405, launched `--sports-entity FIXTURES` by slot 11 to
  conserve enrichment budget) was measured by slot 4 silently fetching teams+stats+events+lineups+player_stats for ~1761
  fixtures on a single date (2026-04-18) — API-Football quota dropped 73705 -> 66788 (~7000 calls) in ~1h. Slot 4
  code-read the root cause: `instruments_service/engine/orchestrator/process_preflight.py` `_freshness_preflight()`
  builds `missing_entities` ONLY from the `missing` set (guarded `if is_sports_run and missing:`, ~lines 568-570), never
  from the `stale` set. A date that is stale-not-missing (stale=[FIXTURES], missing=[] — the schema-version-mismatch
  re-fetch trigger, NOT a first-time capture) therefore yields `missing_entities=[]`, and
  `process_enrichment.py::_fetch_sports_reference_block` then passes `entities_to_fetch=None` via its `... if
  missing_entities else None` fallback — which is the LEGACY unscoped "fetch every reference block" path, completely
  bypassing the CLI `--sports-entity` restriction. Because API-Football uses a shared, singleton-locked key, an unscoped
  burn like this can exhaust the daily quota and then block ALL sports API-Football work fleet-wide — the same failure
  class already hit today at 08:12Z. Any date in the 2020-06-06..2026-07-25 range whose FIXTURES row predates a schema
  bump is a candidate to re-trigger this, so it is NOT a one-off. Main (agt-52bb99) ruled option A on the live blocked
  question (BLK-aa5efbbb) and, after the owning worker did not execute the stop, stopped the VM itself as a protective
  billing-waste cap (now TERMINATED). Relaunch of the FIXTURES-only backfill is gated on the fix below.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags:
  [sports, api-football, freshness-preflight, scope-escape, enrichment, quota, billing-waste, data-pipeline, stale, P0]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
priority: P0
parent_epic: sports_master
source:
  "slot 4 (data_engineering) code-read diagnosis + measured quota burn during
  sports_curated_universe_domestic_selection_remaining-001; main (agt-52bb99) ruled BLK-aa5efbbb=A + executed the
  protective VM stop, 2026-07-25 ~13:40-13:50Z"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# Sports freshness-preflight stale-not-missing dates escape --sports-entity scope → unscoped shared-quota burn

## Evidence (2026-07-25, slot 4 code-read + measured; main verified + stopped the VM)

- VM `af-backfill-20260725-125405` (asia-northeast1-c), launched `--sports-entity FIXTURES` (scoped by slot 11 to avoid
  enrichment-budget burn), was measured fetching teams+stats+events+lineups+player_stats for ~1761 fixtures on a single
  date (2026-04-18). API-Football quota 73705 -> 66788 (~7000 calls) in ~1h.
- Root cause (code-confirmed): `process_preflight.py::_freshness_preflight()` builds `missing_entities` only from the
  `missing` set (`if is_sports_run and missing:`, ~L568-570), never from `stale`. stale=[FIXTURES], missing=[] →
  `missing_entities=[]`.
- `process_enrichment.py::_fetch_sports_reference_block` then receives `entities_to_fetch=None` (the
  `... if missing_entities else None` fallback), which is the LEGACY unscoped fetch-everything path — bypassing
  `--sports-entity` entirely.
- Blast radius: API-Football key is shared + singleton-locked; unscoped burns can exhaust the daily quota and block ALL
  sports API-Football work fleet-wide (same failure class as today 08:12Z). Any 2020-06-06..2026-07-25 date whose
  FIXTURES row predates a schema bump can re-trigger it → NOT a one-off.
- Containment: main ruled BLK-aa5efbbb=A (stop + fix + relaunch-after-fix); the owning worker did not execute the stop
  within a tick, so main executed `gcloud compute instances stop af-backfill-20260725-125405 --zone=asia-northeast1-c`
  itself (protective billing cap; a VM stop is not a launch, autonomous per the kill-switch matrix;
  idempotent/skip-aware so zero written-data loss). Verified STATUS=TERMINATED.

## Todos

- [ ] [DATA] P0. Fix `_freshness_preflight()` so a `stale` (not just `missing`) entity contributes to `missing_entities`
      (or, equivalently, so `_fetch_sports_reference_block` NEVER falls back to the unscoped fetch-everything path when
      a CLI `--sports-entity` scope was supplied — an empty `missing_entities` under an explicit scope must fetch
      NOTHING outside that scope, not EVERYTHING). **Done when**: a stale-not-missing date under
      `--sports-entity FIXTURES` fetches ONLY fixtures (no teams/stats/events/lineups/player_stats), proven by a unit
      test with stale=[FIXTURES]/missing=[] asserting `entities_to_fetch == ['FIXTURES']` (never `None`), and a dry-run
      over a known stale date shows zero out-of-scope API-Football calls.
- [ ] [DATA] P1. After the fix lands + is quality-gates green, relaunch the FIXTURES-only backfill (SPOT, skip-aware,
      resumes from measured progress) and confirm the quota-burn rate matches FIXTURES-only expectations (no enrichment
      blocks fetched). Record final/again quota_remaining.
- [ ] [DATA] P2. Audit whether the earlier 08:12Z quota exhaustion and any other in-flight sports backfills hit the same
      stale-scope-escape (grep run logs for enrichment fetches on `--sports-entity`-scoped runs); if any already-running
      VM is escaping scope, stop it too. Cross-ref
      `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md`.

## Triage / charter note

Filed per the big-finding triage rule (data-pipeline correctness + billing-waste + fleet-wide blast radius). Main
(agt-52bb99) diagnosed via slot 4's code-read + measured evidence, ruled the live blocked question (A:
stop/fix/relaunch), and — because the owning worker stayed heads-down on its own task and did not execute the directed
stop within a tick — executed the protective VM stop itself (a reversible, safe-idempotent billing cap, not a
data-destroying delete and not a VM launch, so within the autonomous protective-arming scope; no operator gate required
for a stop). The FIX is a code change owned by a DATA/backend worker; relaunch is gated on it. Severity P0 because the
shared singleton-locked API-Football quota is a fleet-wide chokepoint and the scope-escape is confirmed +
recurrence-prone, not hypothetical.
