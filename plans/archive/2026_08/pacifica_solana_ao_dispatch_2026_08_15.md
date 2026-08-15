---
doc_type: plan
title: Pacifica-Solana GCS discovery re-verify + rename/backfill migration
summary: >-
  Operator-ruled 2026-08-15 (na-eligibility-audit follow-up Q&A) — re-verify the 787-object PACIFICA-SOLANA
  discovery/classification fresh, then execute the rename + manifest-backfill migration to the canonical
  `PACIFICA-SOLANA:PERPETUAL:` filename prefix. Wallet-key provisioning (live order placement) was explicitly NOT
  authorized in this ruling — stays human-gated, out of scope for this plan.
status: complete # archived 2026-08-15 — every todo done; both re-verifies found zero remaining write work
nature: process
asset_group: [defi]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
tags: [defi, canonicalization, pacifica, manifest, gcs-migration]
related: [/plans/active/pacifica_solana_perp_reintegration_2026_08_14.md]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A, 2026-08-15"
locked_by:
context_scope:
  [
    /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
locked_since:
resolved_by:
---

# Pacifica-Solana GCS discovery re-verify + migration

## Why this exists

`pacifica_solana_perp_reintegration_2026_08_14.md` found 787 `PACIFICA-SOLANA` raw-tick GCS objects resolvable to the
canonical filename prefix once the venue was re-added to `VENUES_BY_ASSET_GROUP["cefi"]`, but the
discovery/classification scan is from before this session and needs a fresh run before trusting its count. Operator
ruling 2026-08-15 (this session's na-eligibility-audit follow-up): re-run discovery fresh, then migrate if it still
checks out — not a blind migrate, not a hold.

## Todos

- [x] ✅ [SCRIPT] P1. Re-run the discovery/classification scan for `PACIFICA-SOLANA` raw-tick objects (same tooling used
      in `pacifica_solana_perp_reintegration_2026_08_14.md` — the two independent
      `market-data-tick-cefi-prd-.../venue=PACIFICA-SOLANA/` GCS scans) and confirm the object count/shape still matches
      the 787 figure. Report any drift before proceeding. (repos: instruments-service) —
      `unified-api-contracts@475270d5`. **Count/stem-count CONFIRMED clean (787 objects, 5 stems — unchanged).** But a
      real DRIFT was found, not a clean pass-through: see Progress Log below.
- [x] ✅ [SCRIPT] P1. **CAVEAT ADDED 2026-08-15 by todo #1's re-verify — READ BEFORE EXECUTING.** The rename half of
      this todo may already be done: a fresh scan found all 787 objects' filenames ALREADY canonical on disk (see
      Progress Log). Do NOT execute a rename against objects that may already be renamed. Re-run
      `market-tick-data-service/scripts/reconcile_pacifica_quarantine_2026_08_15.py` fresh (per its own docstring) AND
      independently check manifest-row state (NOT re-verified by todo #1 — do not assume either way) before taking any
      action. If that re-verify confirms objects are already canonical: skip the rename, and backfill manifest rows only
      if genuinely still absent. Follow the standard reversibility-qualified GCS-rename pattern
      (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) for whatever write work actually remains. (repos:
      instruments-service, market-tick-data-service) — `unified-api-contracts@84d62f242e`. **Both re-verifies confirm NO
      write action remains**: fresh script re-run classified all 787 objects `canonical_already` (5/5 stems);
      independent `read_availability_index_safe` check found 787 manifest rows already present (`ohlcv_1m`/`captured`,
      1:1 with the objects). Corrected the now-doubly-stale `quarantine.py` docstring + registry claims accordingly (see
      Progress Log). The delete-safety protocol's rename/write path was not invoked — nothing to rename or backfill.

## Progress Log

- **2026-08-15 (todo #2 done — both re-verifies confirm zero remaining write work)**: re-ran
  `market-tick-data-service/scripts/reconcile_pacifica_quarantine_2026_08_15.py` fresh per todo #1's caveat — confirmed
  again: all 787 objects, 5/5 stems `canonical_already`. **Independently checked manifest-row state** (todo #1
  explicitly had not) via `read_availability_index_safe(bucket, filters=[("venue", "=", "PACIFICA-SOLANA")])` against
  the live `market-data-tick-cefi-prd-central-element-323112` bucket: **787 rows already present**, all
  `data_type=ohlcv_1m`/`capture_status=captured`, one-to-one with the 787 GCS objects, spanning 2025-07-15..2025-12-31.
  **Conclusion: both the rename and the manifest-backfill are already complete — no write work remained to execute**, so
  the delete-safety protocol's proof gate / reversibility-qualified rename pattern was not invoked (nothing to write).
  Corrected the now-doubly-stale claims in `quarantine.py` (module docstring's "no lane / no manifest rows... still
  on-disk non-canonical" + the registry entry's `reason`/`verified_by`, which still said manifest state was unchecked) —
  `unified-api-contracts@84d62f242e`; full QG green (362s). The on-disk/manifest change's original mechanism remains
  UNCONFIRMED (no rename/backfill commit found in either repo's git log across either todo's re-verify) — out of scope
  to root-cause here, noted for any future investigation. **Every todo in this plan is now done and unlocked — archiving
  per the plan-completion-and-archival HARD RULE.**

- **2026-08-15 (todo #1 done — re-verify found a real drift, not a clean confirm)**: re-ran
  `market-tick-data-service/scripts/reconcile_pacifica_quarantine_2026_08_15.py` fresh (`uv sync` + direct run against
  the prod `market-data-tick-cefi-prd-...` bucket, read-only, no GCS writes). **Count/shape confirmed**: 787 objects, 5
  unique stems (BTC/ETH/HYPE/SOL/XRP-USDC@LIN) — unchanged from the original scan. **Drift found**: the script's own
  classification now buckets all 5 stems as `canonical_already` (previously implied non-canonical/"resolved"). Verified
  this is real, not a script artifact, by calling `discover_objects()` directly and inspecting raw GCS blob names —
  confirmed live paths read e.g.
  `raw_tick_data/by_date/day=2025-07-16/pipeline_mode=batch_tardis/asset_group=cefi/venue=PACIFICA-SOLANA/instrument_type=perpetual/data_type=ohlcv_1m/PACIFICA-SOLANA:PERPETUAL:BTC-USDC@LIN.parquet`
  — the canonical `PACIFICA-SOLANA:PERPETUAL:` prefix is already on the actual filename today. Checked for an
  explanatory mechanism: `git log --since="2026-08-15 07:00" --all -i --grep=pacifica` in both `instruments-service` and
  `market-tick-data-service` returned **zero commits** — no tracked rename/migration landed between the original scan
  and this re-verify, so the on-disk change's mechanism is UNCONFIRMED (possibly an ongoing/scheduled capture process
  legitimately re-writing these shards with the modern adapter's canonical id-builder, possibly something else — not
  established here, out of this todo's scope to root-cause). Did NOT check manifest-row state (todo #2's concern, not
  re-verified here — do not assume either way). **Corrected the stale claim** in
  `unified_api_contracts/canonical/quarantine.py`'s `QUARANTINE_REGISTRY["PACIFICA-SOLANA"]` entry (`reason` +
  `verified_by` fields, which explicitly asserted "Objects are UNCHANGED on disk... still the bare BASE-QUOTE@LIN stem")
  — `unified-api-contracts@475270d5f9`, per the workspace's stale-doc-is-a-finding hard rule; full QG green (384s).
  **Added a caveat to todo #2 above** so its dispatch doesn't blindly execute a rename against objects that may already
  be renamed — it still needs its own fresh re-verify (both object AND manifest state) before any write, exactly as its
  own text already required, now with concrete evidence of why that requirement is load-bearing here.

- **2026-08-15 (na-eligibility-audit follow-up, operator ruling)**: extracted from
  `pacifica_solana_perp_reintegration_2026_08_14.md` per operator's "re-run discovery fresh, then migrate" answer.
  Wallet-key provisioning explicitly deferred (human sign-off required) — recorded separately in the source doc, not
  part of this plan.
