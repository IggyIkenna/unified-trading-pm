---
doc_type: issue
title: >-
  Pipeline smoke sweep across asset groups — 3 tooling false-green defects fixed, a 15h CeFi backfill outage caught, and
  a data-recency map
summary: >-
  A cross-asset-group run of the data-pipeline smoke checks found more wrong with the CHECKING than with the pipeline.
  Three defects that each produced a false or misleading verdict were fixed and shipped: a Phase 0 bucket gate that
  false-negatived all five asset groups (and would have provisioned five duplicate buckets against the sub-100
  consolidation), a checker that exited 0 when it had proved nothing, and an invalid DEPLOYMENT_ENV surfacing as N
  identical per-cell failures instead of one clear message. Separately the sweep caught that the CeFi backfill had been
  silently down for ~15 hours, and produced a per-asset-group data-recency map showing sports is ~4 weeks stale and
  prediction cannot resolve its bucket at all.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-trading-pm, deployment-service]
scope: [engineer, admin]
tags: [smoke-test, false-green, data-recency, buckets, deployment-env]
related:
  [
    /plans/archive/issues/vm_startup_scripts_no_auto_rollout_to_gcs_2026_07_19.md,
    /plans/archive/issues/backfill_vm_disk_starvation_misdiagnosed_as_tardis_quota_2026_07_18.md,
    /plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md,
  ]
created: 2026-07-20
author: unknown
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend
drift_direction: advance-code
depends_on: []
source: ["cross-asset-group smoke sweep run 2026-07-20 while completing the CeFi throughput close-out"]
resolved_by:
locked_by:
context_scope:
  [
    /plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/issues/backfill_vm_disk_starvation_misdiagnosed_as_tardis_quota_2026_07_18.md,
  ]
---

# Pipeline smoke sweep — findings

## 1. Three tooling defects, each a false or misleading verdict (ALL FIXED + SHIPPED)

| #   | Defect                                                                                                               | Impact                                                                                                                                                                                 | Fix                                                                                  |
| --- | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| 1   | Phase 0 gate used `gcloud storage buckets describe`, needing `storage.buckets.get` the `unified-trading-sa` SA lacks | Reported "GAP MISSING" for **all 5** asset groups even though the buckets exist; following it literally provisions 5 DUPLICATE buckets against `bucket_estate_consolidation_to_sub100` | object-level probe distinguishing MISSING(404) from EXISTS-but-EMPTY, in BOTH skills |
| 2   | Checker returned `1 if (failed or ambiguous) else 0`                                                                 | An all-skipped run has failed=0/ambiguous=0, so a run that launched no VM and proved NOTHING exited **0 = success**                                                                    | proved-nothing guard, `market-tick-data-service@a7c06565`                            |
| 3   | No validation of `DEPLOYMENT_ENV` before launching                                                                   | An invalid value surfaced only as N identical `launcher_script_nonzero_rc=1` rows; one bad env var cost a full TradFi run                                                              | fail-fast with a targeted hint, `mtds@f06baa28` + `instruments-service@5b509c0b`     |

**The `prd` vs `prod` trap (defect 3) is worth remembering**: the SHORT form `prd` is correct in bucket names
(`market-data-tick-tradfi-prd-*`, via `DEPLOYMENT_ENV_SHORT`) but the launchers hard-validate `prod|staging|dev`. So
`prd` looks right, fails everywhere, and reads as a pipeline defect rather than a typo.

Defect 1 was caught only because a control test was run against a bucket known to be readable — `describe` failed on
`market-data-tick-cefi-prd-*` too, which the same session had been reading objects from continuously. **Never trust a
"missing" verdict from a metadata API this service account cannot call.**

## 2. The CeFi backfill was silently down for ~15 hours

Found during the sweep, unrelated to it: no `cefi-queue` VM was running and the previous one's last activity was
2026-07-19 19:06 (VM deleted). The primary 15-20TB backfill had simply stopped.

Relaunched at the frontier, and a **keep-alive watchdog** now guards it — it relaunches on death, enforces the cap-1
Tardis rule (deleting extras, newest kept), and logs upload progress so a stall is visible. A backfill that can stop
without anyone noticing is the real defect; the watchdog is the mitigation, not the cure.

## 3. Data-recency map (check this BEFORE choosing a smoke day)

| asset_group | last captured             | note                                                                          |
| ----------- | ------------------------- | ----------------------------------------------------------------------------- |
| cefi        | 2026-07-20                | healthy                                                                       |
| tradfi      | 2026-07-13                | ~1 week stale                                                                 |
| sports      | 2026-06-24                | **~4 weeks stale**                                                            |
| prediction  | n/a — `BucketNamingError` | `market-data` has no `prediction` entry; it is the dedicated flat `pred` kind |

**Smoking a day an asset_group has no data for produces failures that look like pipeline defects but are not.** The
TradFi run is the worked example: 15 checks / 8 passed, and every "failure" traced to 2026-07-15 having ZERO captured
tradfi rows (265 `expected_unattempted` + 88 `empty_confirmed`, last captured 2026-07-13). VM ground truth confirmed it
— 3 of 4 VMs wrote `0 total records`. `--auto-day` did substitute captured days, but those returned 0 rows too, which is
consistent with Databento's entitlement window on older days.

**TradFi's one genuinely green cell is `FX/ohlcv_24h`** — force + skip (genuine) + canonical all passed, proving the
Yahoo daily path end-to-end. Bucket paths showed no parquet/manifest asymmetry.

## 4. Still open

- ~~**prediction** cannot be smoked until its bucket resolution is fixed (dedicated `pred` flat kind, not a
  per-asset_group `market-data` entry).~~ **STALE (na-eligibility-audit 2026-08-06)**: already fixed elsewhere —
  `data_pipeline_e2e_milestones_gate_2026_07_24.md:463` documents the fix pattern as already known/applied, and
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md:812-815` independently labels this exact sub-item
  "DUPLICATE/STALE ... same BucketNamingError class already root-caused and fixed." The other two sub-items below (DeFi
  migration gate, sports staleness) remain genuinely open/unverified per the 2026-08-03 entry below.
- **DeFi** smoke is blocked while `canonical-migration-defi-rebuild` runs — the consolidated manifest goes stale
  (measured 1111s > the 120s threshold), the reader falls back to per-VM shards, and `--require-captured` cannot
  determine capture state, so every cell filters out. A watcher is armed to run it automatically once the fleet lands
  AND the manifest is fresh again.
- **sports** is ~4 weeks stale — worth understanding why before treating any sports smoke result as a pipeline verdict.

## Todos

- [ ] [DATA] P1. **Unblock the 3 still-open smoke gaps** — prediction cannot be smoked until its bucket resolution is
      fixed (dedicated `pred` flat kind, not a per-asset_group `market-data` entry); DeFi smoke stays blocked while
      `canonical-migration-defi-rebuild` runs (consolidated manifest goes stale, a watcher is armed but has not yet
      fired); sports is ~4 weeks stale and the cause is unconfirmed.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA-STALE — `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`
  analysed this doc's '## 4. Still open' 3 items verbatim and found sub-item (1) (prediction bucket resolution)
  DUPLICATE/STALE — the same BucketNamingError class already root-caused and fixed elsewhere. Citation fix, not a
  reclassification: re-verify the remaining 2 sub-items (DeFi migration gate, sports staleness cause) before treating
  this as live.

- **na-eligibility-audit 2026-08-03 (cross-cutting tranche)**: KEEP-NA, valid — **the 2026-07-30 entry's own "re-verify
  the remaining 2 sub-items" instruction is still outstanding** (no evidence found of anyone completing it in the 2+
  weeks since). Confirming this honestly rather than silently re-stamping the doc: this run did not attempt a live
  GCS/manifest check of current DeFi-migration-gate or sports-recency state (that class of live-infra verification is
  `/data-pipeline-reconciliation`'s scope, not a plan-hygiene classification pass), so sub-items 2-3 remain unverified,
  not resolved. Given this doc is P1 and now 2+ weeks stale with an unexecuted self-instruction, flagging in this run's
  report for operator/main-agent attention rather than leaving it quietly re-marked KEEP-NA.
- **context-scout 2026-08-03**: refreshed context_scope (3 entries, unchanged from prior scout — still accurate: the
  bucket-consolidation + disk-starvation archived sibling docs and the batch1 satellite plan that analysed this doc's
  "Still open" section).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, stale items — sub-item 1 (prediction bucket-resolution fix) is
  stale/already-fixed-elsewhere, annotated inline below with citations. Sub-items 2-3 (DeFi smoke / sports staleness)
  remain genuinely unverified (live GCS/manifest verification is /data-pipeline-reconciliation's scope, not this
  skill's) — doc stays NA overall, single checkbox bundling all 3 cannot be partially closed.
