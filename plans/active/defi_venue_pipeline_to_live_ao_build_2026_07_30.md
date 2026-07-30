---
doc_type: plan
title: DeFi 6-venue pipeline→live build — genuine IS adapters, healthy cron, 90-day backfill, catalogue, phase flip
summary: >-
  Executes the operator's 2026-07-29 ruling on issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md —
  count ANKR/STADER/STAKEWISE/SWELL/MANTLE/MAKER toward the `defi` completeness_pct denominator, but only after they
  genuinely EARN "live" status. Split out of the issue doc (per its own 2026-07-30 scope assessment + the
  defi_satellite_ao_dispatch_batch6 audit) because the ruling demands full completion across 4 real sub-steps and 3
  repos — not a single bounded todo.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [defi, honest-coverage, venue-phase, instruments-service, backfill, ao-build]
related:
  [
    /plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md,
    /plans/active/defi_venue_pipeline_to_live_ao_build_finalize_2026_07_30.md,
  ]
created: "2026-07-30"
last_updated: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Split from /plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md's sole remaining open
  todo per that doc's own 2026-07-30 scope assessment ("recommend this become its own dedicated multi-todo build plan")
  and defi_satellite_ao_dispatch_batch6_2026_07_30.md's independent same-day agreement. Operator ruling already on
  record (2026-07-29: "both: count them AND build out the real IS universe") — this plan executes it, does not re-ask.
---

# DeFi 6-venue pipeline→live build

## Why this plan exists

`issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md` traced a real honest-coverage undercount: 11
`phase=="pipeline"` DeFi venues with genuine capture are structurally excluded from the `defi` `completeness_pct`
denominator. The operator ruled (2026-07-29) to count qualifying venues toward the denominator, but ONLY once they
genuinely earn "live" — no partial rollout, no re-creating the same false-"already working" premise an earlier
adversarial-verify pass already caught once on this exact doc (see that doc's "BLOCKED 2026-07-22" section: a
`DEFI_VENUE_MTDS_CAPTURED` claim of "months-long" capture turned out to be a single synthetic sample, not production
data).

Scope: exactly the 6 venues already shipped as `DEFI_VENUE_MTDS_ADAPTER_VERIFIED_NOT_YET_SCHEDULED` (content-verified
accurate, 2026-07-22): **ANKR-ETHEREUM, STADER-ETHEREUM, STAKEWISE-ETHEREUM, SWELL-ETHEREUM, MANTLE-ETHEREUM,
MAKER-ETHEREUM**. The other 5 originally-investigated venues (FRAX/ALCHEMY/FLASHBOTS/ACROSS/STARGATE) had their
capture-path defects fixed 2026-07-22 (see `plans/active/issues/five_broken_defi_capture_paths_shipped_2026_07_22.md`)
but have not had their data content-verified the way these 6 have — out of scope for this plan; a future plan can cover
them once they clear the same bar.

**Ordering is real** (`sequential: true`): cron health must be confirmed before the 90-day backfill runs against it (no
point backfilling against a cron that's about to be re-fixed and change behavior); catalogue registration and the final
phase-flip both need the IS adapters to exist first. IS-adapter work and the cron fix touch different repos/files and
could in principle run in parallel, but the whole chain is short enough (5 todos) that serializing correctly beats
splitting into two plans just to parallelize two todos.

## Todos

- [ ] [DATA] P1. Build genuine `instruments-service` reference-data adapters/universe entries for all 6 venues
      (ANKR-ETHEREUM, STADER-ETHEREUM, STAKEWISE-ETHEREUM, SWELL-ETHEREUM, MANTLE-ETHEREUM, MAKER-ETHEREUM), mirroring
      the existing adapter pattern already used for BLAZESTAKE / KAMINO_LENDING / MORPHOVAULTS (fixed 2026-07-22 per the
      source issue doc). Each venue must resolve through `instruments-service`'s `_build_defi_venues()` /
      expected-universe builder as a real reference-data adapter — not a bare MTDS-only on-chain handler with no IS
      counterpart, which is the exact gap `DEFI_VENUE_PHASE`'s current invariant (`phase=="live" ⟺ IS-producible`) flags
      today. Done-when: a targeted `instruments-service` CLI/pytest check confirms all 6 venues resolve with
      non-placeholder instrument entries.

- [ ] [DATA] P1. Fix/confirm the production cron backing these 6 venues' capture so it reliably writes real per-day
      manifest shards going forward — not the one-off manual-invocation samples the source doc's investigation found.
      Per that investigation: `uts-prod-mtds-collect-lst-rates` was crash-looping (OOM, then hung to the 1200s timeout)
      on both tracked runs, and the 6 GCS objects that exist today were written by a manual/ad-hoc invocation ~80-120
      min after the cron's failed attempts; MAKER's manifest-registration gap is a stated execution-order artifact of
      that manual run, not a separate bug — verify it self-resolves once the real cron runs cleanly. Reuse the
      crash-loop fix pattern already shipped for the sibling `uts-prod-mtds-collect-gas-fees` cron (see
      `five_broken_defi_capture_paths_shipped_2026_07_22.md`) if the same OOM/timeout root cause applies. Done-when: 3
      consecutive real cron-triggered (Cloud Scheduler-fired, not manual `gcloud run jobs execute`) daily runs each
      write a `capture_status=captured` manifest row for all 6 venues, verified via Cloud Run job execution history + a
      manifest query.

- [ ] [DATA] P1. Run the 90-day historical backfill for all 6 venues via direct local invocation — no VM launch needed
      per the source doc's own estimate (~2,340 lightweight RPC calls, well under a constrained rate limit) — now that
      the cron is confirmed healthy (prior todo). Done-when: the availability manifest shows ≥90 days of
      `capture_status=captured` rows per venue (or a documented, source-cited reason for any specific-day gap — e.g. a
      genuine upstream outage), each row's `source=` field correctly tagged per
      `/codex/02-data/pipeline-mode-partition.md`.

- [ ] [DATA] P1. Register all 6 venues in the instruments catalogue so downstream consumers see a complete universe, not
      just a manifest-side capture stream (ruling item 4). Done-when: the instruments catalogue / data-status surface
      shows all 6 venues with non-zero, non-placeholder instrument counts.

- [ ] [DATA] P1. Flip `DEFI_VENUE_PHASE` for all 6 venues (ANKR/STADER/STAKEWISE/SWELL/MANTLE/MAKER) from `"pipeline"`
      to `"live"` in `unified-api-contracts/unified_api_contracts/registry/defi_venues.py`; confirm
      `VENUES_BY_ASSET_GROUP["defi"]` (`market_data_categories.py:395`) picks the flip up automatically (no separate
      edit needed there — it derives from `DEFI_VENUE_PHASE`); re-measure `completeness_pct` for `defi` before/after via
      `instruments-service/scripts/measure_honest_coverage.py --asset-group defi --diagnose-layer1` against the live
      prod manifest and report the exact before/after `n_expected`/`n_present`/`completeness_pct` numbers in this todo's
      evidence line (the source doc's last measurement: `n_expected=109, n_present=3, completeness_pct=2.75`, pre-flip
      baseline to diff against). Also confirm
      `instruments-service/tests/unit/test_orchestrator_helpers.py::test_defi_set_equals_uac_denominator_drift_guard`
      stays green post-flip, or deliberately update it to match the new intended state if it legitimately must change
      (the source doc's investigation flagged this exact test as a likely casualty of a naive flip). Operator ruling
      already on record (2026-07-29, cited in this plan's frontmatter `source:`) — do not re-ask; cite it as the
      authorization for changing this production honest-coverage number.

## Progress Log

- **2026-07-30** — plan authored (split from the issue doc's oversized single todo per that doc's own recommendation +
  the independent batch6-audit agreement same day). Companion finalize plan:
  `/plans/active/defi_venue_pipeline_to_live_ao_build_finalize_2026_07_30.md`.
