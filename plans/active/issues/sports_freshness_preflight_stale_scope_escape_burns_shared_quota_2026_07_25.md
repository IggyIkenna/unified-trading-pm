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

- [x] ✅ [DATA] P0. Fix `_freshness_preflight()` so a `stale` (not just `missing`) entity contributes to
      `missing_entities` — instruments-service@08387531. `process_preflight.py`'s per-entity-skip block now gates on
      `is_sports_run and (missing or stale)` and builds `missing_entities = list(dict.fromkeys([*missing, *stale]))`
      (deduped union), so a stale-not-missing entity can no longer produce an empty `missing_entities` that
      `_fetch_sports_reference_block`'s `entities_to_fetch=missing_entities if missing_entities else None` would then
      resolve to the unscoped `None` fetch-everything fallback. 2 new regression tests in
      `tests/unit/test_orchestrator_gaps.py::TestFreshnessPreflightStaleScopeEscape`: `stale=["FIXTURES"]/missing=[]`
      asserts `outcome.missing_entities == ["FIXTURES"]` (never empty/None-triggering); a second proves stale+missing
      dedupe into one union. `quality-gates.sh` green (full run, sentinel-verified). **Not yet done**: a live dry-run
      over a real stale date confirming zero out-of-scope API-Football calls — no VM launch/relaunch was performed in
      this turn; that's the P1 todo immediately below, still gated on operator/next-dispatch confirmation of quota state
      per the domestic-selection issue doc's tracker.
- [ ] [DATA] P1. **RELAUNCHED 2026-07-25T15:18Z (slot 7), FIX CONFIRMED HOLDING, NOT yet terminal** —
      `af-backfill-20260725-151845` (tarballs rebuilt + SHA-verified to carry the fix), launched from the
      domestic-selection issue doc's tracker (don't duplicate-launch). **Positive confirmation 2026-07-25T15:45Z**: the
      VM's run.log processed date **2026-04-18 — the EXACT date that triggered the original scope-escape** (1747
      fixtures) — and logged `Per-fixture enrichment: 1747 fixtures x 0 entities = 0 calls queued` +
      `Entity-scoped mode: restricting to FIXTURES only`, i.e. zero out-of-scope enrichment calls, unlike the pre-fix
      run which burned ~6900 calls on this exact date. Live quota corroborates: `daily_remaining` 64965→64928 in ~27min
      (~37 calls total, consistent with ~1 call/date), nowhere near the prior ~6900-calls-in-under-an-hour signature.
      **Fix is proven correct in production on the reproduction case, not just unit tests.** Still running (large
      2020-06-06..2026-07-25 range) — not yet terminal, not a hang. **Next dispatch**: health-check to terminal
      (`gcloud compute instances list` + `run.log` tail), record final `quota_remaining`, THEN this todo + the parent
      relaunch todo in the domestic-selection doc both flip together.
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
