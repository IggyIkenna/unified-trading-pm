---
doc_type: issue
title: CeFi residual followups — deploy (item 1) + OKX-FUTURES manifest relabel (item 3) still open
summary: >-
  cefi_satellite_ao_dispatch_batch2-010 bundled 4 sub-items from
  cefi_residual_followups_after_honest_done_2026_07_17.md. Items 2 (features-service image build) and 4 (3 of 4 codex
  SSOT reconciliations) are done this pass. Item 1 (reader-bridge deploy to 4 live consumers) is infra-craft work
  outside backend_engineer scope; item 3 (OKX-FUTURES manifest instrument_type relabel, ~116,742 rows) needs a
  collision-aware dedup migration script, not a blind in-place relabel — both tracked here as follow-up todos rather
  than false-flipping the parent checkbox.
status: superseded
nature: issue
asset_group: [cefi]
stage: [data]
repos:
  [instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [cefi, deploy, manifest-relabel, follow-up, ao-dispatch, superseded]
created: 2026-07-26
priority: P1
parent_epic: cefi_master
source: [cefi_satellite_ao_dispatch_batch2_2026_07_26.md item cefi_satellite_ao_dispatch_batch2-010]
related:
  [
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /plans/active/cefi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/issues/cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md,
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by: cefi_batch2_010_misscoped_gated_bundle_2026_07_26
resolved_by:
drift_direction: advance-code
---

# SUPERSEDED — see cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md

This doc was filed by slot-3 before discovering that slot-10 had already filed
`issues/cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md` covering the SAME `cefi_satellite_ao_dispatch_batch2-010`
todo's 4 sub-items, already correctly gated. Per main's ruling on `BLK-dca02ac2`, all resolution evidence (items 2+4
done, items 1+3 remaining) has been merged into that doc's "Resolution update (2026-07-26, slot-3)" section instead of
duplicating it here. This doc is kept only as a redirect — do not action its (now-stale) content below.

# CeFi residual followups — 2 of 4 sub-items still open

## What I found

`cefi_satellite_ao_dispatch_batch2-010` bundled 4 sub-items from
`cefi_residual_followups_after_honest_done_2026_07_17.md` (Phase 0b/1/2) that no currently-active cefi plan covers. I
(slot-3, backend_engineer) completed 2 of the 4 in this pass:

- **Item 2 — features-service image build fix: ALREADY RESOLVED, no code change needed.** The image build's
  `CeFiWireCanonicalMap` ImportError was caused by a stale `ARG BASE_IMAGE_DIGEST` pin. The automated
  `update-dependency-version.yml` digest-refresh fan-out has since bumped it twice (`features-service@586a5cea`,
  `@8661a7af`). Verified via `gh run list --repo IggyIkenna/features-service --workflow=image-build-gate.yml`: the most
  recent run (2026-07-26T01:01:07Z, on commit `8661a7af`, the latest digest-refresh) is `conclusion: success`. No
  further action needed.
- **Item 4 — codex↔plan SSOT reconciliation: 3 of 4 done.** `unified-trading-pm@8e435b425` fixes
  `chart-candle-delivery-flow.md` and `per-asset-group-bucket-layouts.md` (both described the pre-D3/D4-migration
  bare-wire-symbol / uniform-`ticks.parquet` leaf; current writer output is per-instrument canonical-stem filenames,
  chain-bundle types being the sole `ticks.parquet` exception) and `read-time-filter-pushdown.md` (worked example used a
  bare wire ticker that no longer matches current filenames). The 4th cited contradiction
  ("`availability-manifest-and-data-status.md` 'immutable wire-form contract'") was grepped for verbatim and NOT found
  in the current doc — either already resolved by an earlier pass or a mischaracterization in the source audit. No edit
  made; flagging here rather than silently dropping it.

## Why it matters

Items 1 and 3 remain genuinely open and are why I did not flip `cefi_satellite_ao_dispatch_batch2-010`'s checkbox:

- **Item 1 — DEPLOY the reader-bridge to 4 narrow-read consumers (incl. an execution-service redeploy).** This is
  infra-craft work (VM/service deploy + redeploy verification), out of `backend_engineer` scope per
  `unified-trading-pm/agents/backend_engineer.md` `does_not`. I checked `gcloud run services list` for MTDS/MDPS/
  features/execution and found no Cloud Run services matching — these run via a VM-based deploy path I don't have
  visibility into from this worktree, and redeploying a live narrow-read consumer on the trading path without
  deployment-service context risks an outage. The reader-bridge code itself is confirmed already on `origin/main` per
  the source doc's 2026-07-18 Progress Log ("Reader-bridge VERIFIED READY") — this is a deploy/redeploy-only step, not
  new development.
- **Item 3 — OKX-FUTURES manifest `instrument_type` mislabel (~116,742 dated-futures rows tagged PERPETUAL, should be
  FUTURE).** This needs a new one-off migration script against the production `instruments-store-cefi-prd` manifest
  (`_index/availability_index.parquet` + per-VM shards), following the
  `scripts/relabel_deribit_combo_historical_to_empty_2026_06_27.py` snapshot-first pattern. Complication: the manifest
  row_key includes `instrument_type` (`unified_trading_library.manifest_writer._ROW_KEY_COLUMNS`), so relabeling
  PERPETUAL→FUTURE for a given (date, venue, instrument_id) can COLLIDE with an ALREADY-EXISTING FUTURE row for the
  identical shard atom — this needs the same dedup-aware "keep the correct row, drop the stale duplicate" logic as
  `scripts/canonicalize_cefi_instrument_type_legacy_lowercase_2026_07_16.py`, not a blind in-place relabel like the
  DERIBIT-COMBO script. Writing and dry-run-validating that collision-aware logic correctly, at production data volume,
  needs a dedicated pass — not safely rushed in a shared session alongside 3 other sub-items.

## Recommended decision

**SUPERSEDED — do not dispatch from this doc.** Both remaining-work items below are tracked as the live, canonical todos
in `issues/cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md` (`[OPERATOR]`-gated there so they do not
auto-dispatch). Struck here to prevent a duplicate backlog derivation from this superseded copy:

- ~~[INFRA] P1. Deploy the D3 reader-bridge to the 4 in-scope consumers~~ — see
  `cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md` todo 2.
- ~~[SCRIPT] P2. Write + dry-run-validate an OKX-FUTURES dated-futures PERPETUAL→FUTURE manifest relabel script~~ — see
  `cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md` todo 3.

## Codex SSOTs

`/codex/02-data/cross-asset-canonical-target-ssot.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/05-infrastructure/gcs-and-manifest-delete-safety-protocol.md`,
`/codex/05-infrastructure/vm-tarball-deployment.md`.
