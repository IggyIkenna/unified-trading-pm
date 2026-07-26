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
assigned_vm: NA
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

## Re-verification 2026-07-26 (`/plan-reconcile cross-cutting`) — both reader legs LANDED; one NEW Terraform leg found

> **Why this pass happened**: the tracker this doc named — `bucket_fold_closeout_2026_07_17.md` — has since been
> **archived** to [`plans/archive/2026_07/`](/plans/archive/2026_07/bucket_fold_closeout_2026_07_17.md) (folded by
> `unified-trading-pm@58801d799`), and that fold moved only its `_KIND_ALIASES` checkbox, not the 4c/4d Progress-Log
> loose ends. So this doc's stated closure condition pointed at a doc that no longer tracks it. Re-verified directly
> instead of re-implementing, per `cross_cutting_consolidated_closeout_2026_07_25.md` Track 13's own criterion.

**✅ Reader leg 4c — deployment-api per-AG defaults: LANDED.** `deployment-api/deployment_api/deployment_api_config.py`
now defines `effective_strategy_store_{cefi,tradfi,defi}_bucket` as three properties that each
`return resolve_bucket_name(cloud=…, kind="strategy-store")` — the FLAT yaml kind — with an inline comment citing the D6
Phase 4 operator decision. The `STRATEGY_STORE_{CEFI,TRADFI,DEFI}_BUCKET` env aliases survive only as override hooks and
resolve to the same flat bucket when empty.

**✅ Reader leg 4d — UAC `enumerate_envelope.py` cefi hardcode: LANDED.**
`unified-api-contracts/scripts/enumerate_envelope.py` now sets `GCS_BUCKET = f"strategy-store-prd-{_PROJECT_ID}"` (flat

- Fold-D env-tiered). The string `strategy-store-cefi-…` survives at :1053 only inside the explanatory comment that
  records the old drift and links back to this doc.

**✅ Bucket retirement CONFIRMED (live probe, not a doc claim).** `gcloud storage ls` (2026-07-26): all three per-AG
buckets return **404 not found** — `strategy-store-cefi-central-element-323112`,
`strategy-store-tradfi-central-element-323112`, `strategy-store-defi-central-element-323112`. The flat
`strategy-store-prd-central-element-323112` exists and holds real content (`_index/`, `backtests/`, `catalogue/`,
`configs/`, `hedge_ratio_snapshots/`).

**✅ Root Terraform: clean.** `rg 'strategy-store' deployment-service/terraform/main.tf` → zero hits; the five per-AG
resource blocks this doc's fix-direction §3 named are gone.

**❌ NEW — one Terraform leg still points at the DELETED buckets (this is why the doc stays open).** The _per-service_
stack was missed by the root-level state-rm:

- `deployment-service/terraform/services/strategy-service/gcp/terraform.tfvars:19-21` still sets
  `strategy_bucket_cefi/tradfi/defi = "strategy-store-{ag}-${PROJECT_ID}"` — all three 404 per the probe above.
- `deployment-service/terraform/services/strategy-service/gcp/main.tf:234-236` wires those same variables into the
  strategy-service Cloud Run job's **GCSFuse mount list** (`read_only = false`) and into
  `STRATEGY_BUCKET_{CEFI,TRADFI, DEFI}` env vars (`main.tf:202-204`).
- Blast radius, measured not assumed: `rg 'STRATEGY_BUCKET_(CEFI|TRADFI|DEFI)' strategy-service/` returns **zero hits**,
  so the env vars are dead config (strategy-service resolves the flat kind via `resolve_bucket_name`). The live risk is
  the **mount list**: a `terraform apply` of this stack either fails on three non-existent buckets or re-creates them —
  resurrecting exactly the split-brain the Wave-3 fold retired.

- [ ] [INFRA] P1. **Drop the 3 dead per-AG `strategy-store` legs from the strategy-service Terraform stack** — remove
      `strategy_bucket_{cefi,tradfi,defi}` from
      `deployment-service/terraform/services/strategy-service/gcp/{terraform.tfvars,terraform.tfvars.example,main.tf}`
      (and the AWS `terraform.tfvars.example` equivalents), including the 3 GCSFuse mount entries at `main.tf:234-236`
      and the 3 env vars at `main.tf:202-204`; if the job needs the strategy store mounted at all, mount the flat
      `strategy-store-prd-${PROJECT_ID}` once instead of three per-AG names. **Done when**:
      `rg     'strategy_bucket_(cefi|tradfi|defi)' deployment-service/terraform/` returns zero hits, `terraform plan` on
      the strategy-service stack is clean, and no plan output proposes creating a `strategy-store-{cefi,tradfi,defi}-*`
      bucket.
