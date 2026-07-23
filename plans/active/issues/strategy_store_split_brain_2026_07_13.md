---
doc_type: issue
title:
  "strategy-store split-brain: live writers use the unified FLAT bucket (per the 2026-05-20 operator decision) while
  deployment-api + the UI still read per-AG strategy-store-cefi — two live surfaces, drifting since ~2026-04/05"
summary:
  "Surfaced by the 2026-07-13 bucket estate audit and adversarially verified: cloud-providers.yaml declares ONE unified
  flat strategy-store-{pid} (D6 Phase 4 operator decision 2026-05-20) and every live strategy-service writer resolves it
  (flat bucket _index/latest.json written 2026-07-13 — today). But deployment-api defaults per-AG
  strategy-store-{cefi,tradfi,defi}-{pid} buckets (deployment_api_config.py:617-635, consumed by routes/services.py and
  advertised to both UIs — including a configs_grid/ path that matches ZERO objects), and
  unified-trading-system-ui/app/api/catalogue/envelope/route.ts:24 hardcodes strategy-store-cefi-central-element-323112
  whose catalogue/ was last written 2026-04-25 (the route claims 'regenerated daily'). The per-AG catalogue writer
  (unified-api-contracts/scripts/enumerate_envelope.py:1053) also hardcodes the cefi bucket while strategy-service's
  newer hedge_ratio/decision_context writers resolve FLAT — the two catalogue surfaces are actively diverging. tradfi/
  defi per-AG buckets exist EMPTY; cefi has real-but-stale content. Estate impact: 4 buckets serving one kind."
status: open
nature: notes
asset_group: [cross-cutting]
stage: [strategy, meta]
repos: [deployment-api, unified-trading-system-ui, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [gcs, strategy-store, split-brain, bucket-mismatch, stale-reads, ui]
related:
  [
    /plans/archive/2026_07/gcs_bucket_estate_cleanup_2026_07_10.md,
    /plans/archive/issues/terraform_bucket_estate_drift_resurrection_2026_07_13.md,
  ]
created: "2026-07-13"
parent_epic: infrastructure_master
priority: P1
source:
  "2026-07-13 bucket estate audit: hardcoded-name sweep flagged the UI literal; a dedicated verification agent confirmed
  writer-vs-reader targets via code reads (strategy_service/config.py:412-416 get_output_bucket ignores category;
  cloud_strategy_storage.py:189,266,343; gcs_storage_service.py:64) and live probes (flat bucket _index updated
  2026-07-13T18:22Z; per-AG cefi catalogue/ last 2026-04-25; per-AG tradfi/defi empty; deployment-api's advertised
  configs_grid/ matches no objects)."
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by:
---

# strategy-store split-brain (flat writers vs per-AG readers)

## Verified state

| Surface                           | Bucket                                           | Evidence                                                                                                                                                                                                                                                    |
| --------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ALL live strategy-service writers | FLAT `strategy-store-{pid}`                      | config.py:412-416 (get_output_bucket ignores category); cloud_strategy_storage.py:189,266,343; gcs_storage_service.py:64 resolve_bucket_name(kind="strategy-store") — yaml flat entry ignores asset_group by design; flat `_index/latest.json` = 2026-07-13 |
| deployment-api → both UIs         | per-AG `strategy-store-{cefi,tradfi,defi}-{pid}` | deployment_api_config.py:617-635 → settings.py:168-170 → routes/services.py:19-21,336-348; advertised `configs_grid/` matches no objects                                                                                                                    |
| UI catalogue route                | hardcoded `strategy-store-cefi-…`                | app/api/catalogue/envelope/route.ts:24; content last written 2026-04-25                                                                                                                                                                                     |
| per-AG catalogue writer           | hardcoded `strategy-store-cefi-…`                | unified-api-contracts/scripts/enumerate_envelope.py:1053                                                                                                                                                                                                    |

## Fix direction

1. Repoint deployment-api defaults + UI route + `enumerate_envelope.py` to the flat kind via the resolver (kind
   `strategy-store`); decide whether `configs/` + `catalogue/` content in the cefi bucket migrates to the flat bucket or
   gets regenerated there.
   - ✅ **UI leg DONE** — `unified-trading-system-ui@2796d38b` (2026-07-13): both catalogue GCS-proxy routes
     (`app/api/catalogue/envelope/route.ts:24`, `app/api/catalogue/instrument/route.ts:23`) repointed from
     `strategy-store-cefi-central-element-323112` to the unified flat `strategy-store-central-element-323112` (content
     verified present via `gcloud storage ls` before the flip); comments claiming "regenerated daily" corrected to
     reference this issue doc. `rg "strategy-store-cefi"` in unified-trading-system-ui now returns zero hits in live app
     code (a stale mirrored copy of `/codex/04-architecture/data-flow-map.md` under `context/codex/` still shows the old
     per-AG names — that mirror's SSOT is this PM repo's `codex/`, not in scope for a uts-ui-only session; update it
     when this doc's codex-alignment pass runs).
   - deployment-api defaults + `unified-api-contracts/scripts/enumerate_envelope.py` repoint **still open** (not this
     session's repo scope).
2. Then retire `strategy-store-{cefi,tradfi,defi}-{pid}` (cefi last — it holds the only real content) — this also closes
   M-1's A10 open question on the unmanaged flat strategy-store, in the OPPOSITE direction A10 assumed (the flat bucket
   is the keeper, per the yaml's operator decision).
3. Note: Terraform declares five per-AG env-suffixed strategy-store resources (main.tf:1249-1335) — remove alongside,
   per [[terraform_bucket_estate_drift_resurrection_2026_07_13]].

## Wave-3 fold assessment (2026-07-19) — bucket side RESOLVED, reader-code legs remain → STAYS OPEN

The Wave-3 execution+strategy fold ([[bucket_fold_execution_strategy_2026_07_17]], Fold D) + the 2026-07-14 per-AG
delete resolved the **bucket** side of the split-brain: `strategy-store-{cefi,tradfi,defi}-{pid}` deleted (cefi
residuals preserved to `legacy_cefi/`), the unified flat `strategy-store` re-tiered `-{env}-`, and the per-AG Terraform
blocks state-rm'd. **Remaining (why this stays open)**: the READER-code legs — deployment-api per-AG defaults
(`deployment_api_config.py:617-635`) + UAC `enumerate_envelope.py:1053` cefi hardcode — are still open, tracked as
closeout loose-ends 4c (deployment-api C+D-display WIP, `stash@{0}`) + 4d (UAC WIP) in
[[bucket_fold_closeout_2026_07_17]]. Close this issue when those two reader legs land.
