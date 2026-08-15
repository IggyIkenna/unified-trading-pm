---
doc_type: plan
title: Pacifica-Solana GCS discovery re-verify + rename/backfill migration
summary: >-
  Operator-ruled 2026-08-15 (na-eligibility-audit follow-up Q&A) — re-verify the 787-object PACIFICA-SOLANA
  discovery/classification fresh, then execute the rename + manifest-backfill migration to the canonical
  `PACIFICA-SOLANA:PERPETUAL:` filename prefix. Wallet-key provisioning (live order placement) was explicitly NOT
  authorized in this ruling — stays human-gated, out of scope for this plan.
status: active
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

- [ ] [SCRIPT] P1. Re-run the discovery/classification scan for `PACIFICA-SOLANA` raw-tick objects (same tooling used in
      `pacifica_solana_perp_reintegration_2026_08_14.md` — the two independent
      `market-data-tick-cefi-prd-.../venue=PACIFICA-SOLANA/` GCS scans) and confirm the object count/shape still matches
      the 787 figure. Report any drift before proceeding. (repos: instruments-service)
- [ ] [SCRIPT] P1. If the re-verify confirms clean: execute the rename migration — prefix each object's filename with
      `PACIFICA-SOLANA:PERPETUAL:` and backfill matching manifest rows (none currently exist for this venue's raw-tick
      history). Follow the standard reversibility-qualified GCS-rename pattern
      (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`). (repos: instruments-service,
      market-tick-data-service)

## Progress Log

- **2026-08-15 (na-eligibility-audit follow-up, operator ruling)**: extracted from
  `pacifica_solana_perp_reintegration_2026_08_14.md` per operator's "re-run discovery fresh, then migrate" answer.
  Wallet-key provisioning explicitly deferred (human sign-off required) — recorded separately in the source doc, not
  part of this plan.
