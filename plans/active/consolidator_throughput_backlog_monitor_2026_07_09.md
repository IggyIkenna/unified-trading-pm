---
doc_type: plan
title: Consolidators tab — per-AG backlog + consolidation throughput monitor
summary:
  Make the Consolidators cockpit tab answer "is the consolidator keeping up?" — surface the per-asset_group backlog
  (per-VM shards written since the last consolidated-index run, i.e. not yet absorbed) and a live throughput view of
  shards absorbed per tick. v1 is cheap + no consolidator change (backend backlog field from a single shard-prefix list
  + a client-accumulated session sparkline that INFERS merged/tick from backlog deltas). v2 (the truthful
  merged-per-tick histogram, sourced by instrumenting the consolidator job) is DEFERRED + still under discussion. LOCAL
  plan — built interactively in this slot.
status: active
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, deployment-api, unified-trading-library]
scope: [engineer]
tags: [deployment-observability, cockpit, consolidator, manifest, backlog, throughput, deployment-ui]
related: [deployment_observability_expansion_2026_07_08.md]
created: "2026-07-09"
last_updated: "2026-07-09"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: ui-developer
drift_direction: advance-code
---

# Consolidators tab — per-AG backlog + consolidation throughput monitor

> **LOCAL / human plan** (`assigned_vm: NA`, executed interactively in this slot — NOT AO-dispatched). Follows the
> Consolidators-tab live-monitor rewrite (`deployment-ui@9476927`). Operator feedback: the index-age/budget bar is a
> low-value "countdown to next consolidation"; the real questions are **is the consolidator keeping up (backlog)** and
> **how much is it absorbing per tick (throughput)**.

## Design decisions (captured 2026-07-09)

- **Backlog = per-VM shards newer than the consolidated index.** Each VM writes ONE `_index/per_vm/{instance}.parquet`
  shard (rewritten on flush; `BlobMetadata.last_modified` per blob). The consolidator (per-AG Cloud Run Job + Cloud
  Scheduler, `*/1 * * * *`) merges them into the consolidated index every minute. Backlog for an AG = count of shards
  with `last_modified` > consolidated-index `last_modified` (written since the last run → not yet absorbed). Computable
  from ONE per-AG prefix list — **single-walk-safe** (the same list `_per_vm_shards_exist` already does).
- **The merged-per-tick throughput time-series is recorded NOWHERE today, and CANNOT be reconstructed after the fact**
  (each shard file carries only its latest mtime). A true time-series needs a source that logs each run as it happens.
- **v1 (this plan) = cheap, no consolidator change.** Backend returns the backlog COUNT (point-in-time, real). The UI
  already polls every 15s → the FRONTEND accumulates the polled backlog samples into a session-scoped rolling window and
  renders a live sparkline per AG; "shards absorbed this tick" is INFERRED from backlog drops between samples. Honest
  limits: window = your current watching session (resets on reload); "merged" is inferred (backlog delta), not the job's
  real count. Both are exactly what v2 fixes.
- **v2 (DEFERRED, under discussion) = the truthful merged-per-tick histogram.** Instrument the consolidator job to
  record `{ts, asset_group, shards_merged, backlog_after, rows_added, duration_ms}` per run to a durable store; the
  endpoint returns the last N runs → an exact histogram with real numbers + durable history. See the WS-2 section.

## Codex SSOTs (READ before touching each area)

- Manifest consolidator runtime (Cloud Run Job + Scheduler `*/1`, per-(kind, AG), `unified_trading_sa` objectAdmin):
  `codex/05-infrastructure/manifest-consolidator-ssot.md`.
- Availability manifest / per-VM shard layout + single-walk: `codex/02-data/availability-manifest-and-data-status.md`.
- Consolidator health endpoint: `deployment-api/deployment_api/routes/health_consolidator.py` (`ConsolidatorAgHealth`,
  `_ag_health`); per-VM shard helpers `unified_trading_library.manifest_writer._state` (`_per_vm_shards_exist`,
  `_consolidated_blob_age_sec`).
- UI testing gate (playwright L2): `codex/06-coding-standards/ui-testing-layers.md`.

---

## WS-1 — v1: backlog field + live session throughput (BUILD NOW)

- [x] 1. ✅ [BACKEND] P1. **UTL backlog helper** — `per_vm_shard_backlog(client, bucket, index_last_modified)` next to
     `_per_vm_shards_exist` (manifest_writer `_state.py`): ONE `_index/per_vm/*.parquet` list, returns
     `(pending, total)` where pending = non-legacy shards with `last_modified` STRICTLY AFTER the index's; missing/None
     mtime → not pending (honest under-count). Exported via facade + top-level `__init__`/`__all__`. —
     `unified-trading-library@da31ef2` + 5 unit tests (`test_per_vm_shard_backlog.py`), UTL QG green.
- [x] 2. ✅ [BACKEND] P1. **Endpoint field** — `pending_shard_count` + `total_shard_count` on `ConsolidatorAgHealth`;
     `_ag_health(..., include_backlog=True)` computes them via ONE `per_vm_shard_backlog` list (also yields shard
     existence, so no double-list); gated opt-in so the `/freshness` reuse (`consolidator_posture`) pays no extra list.
     `_mock_response` carries reps (cefi 2/6, defi 47/48). — `deployment-api@575810d` + 2 unit tests. (3 pre-existing
     unrelated QG failures in `test_data_status_drilldown.py` — DeFi uniswap pool schema, another agent's code.)
- [x] 3. ✅ [UI] P1. **Backlog display** — `pending_shard_count`/`total_shard_count` on `ConsolidatorAssetGroup`
     (health.ts) + "backlog (pending shards) N / total" per AG card (prominent when > 0). — `deployment-ui@8eb4001`.
     `pw:L2 ✓` cockpit.spec.ts O5 (cefi 47/48).
- [x] 4. ✅ [UI] P1. **Live throughput sparkline** — session rolling window (~40 samples ≈ 10 min) accumulated from the
     polls; per-AG recharts Area sparkline (`chart-theme` tones); "−N absorbed" derived from backlog drops; honest
     caption ("this session · inferred from backlog deltas"). — `deployment-ui@8eb4001`. `dataviz` skill loaded
     (single-series, no legend, 2px line). `pw:L2 ✓` O5 (sparkline accumulates across polls).
- [x] 5. ✅ [BACKEND] P1. **FINDING — cefi false-degraded fix (per-AG staleness budget).** Root cause (verified vs live
     GCS + Cloud Run): cefi market-tick is a DAILY batch, its consolidator effectively runs ~every 5 min (executions 5
     min apart; index age climbed 174→228s), but the endpoint judged every AG against a uniform 120s budget → cefi
     `degraded` ~60% of the time. Fix: `_AG_STALENESS_BUDGET_SEC`/`_budget_for` — cefi = 86400s (its launchers'
     `MANIFEST_CONSOLIDATED_STALENESS_SEC`), others keep 120s default. — `deployment-api@90ace9f` + unit test; live cefi
     now `age=120s status=ok`.
- [x] 6. ✅ [UI] P2. **Poll cadence 15s→30s** — consolidation changes every 1–5 min, so 15s over-polled. —
     `deployment-ui@b00454b` (O5 test waits the new 30s 2nd-poll).
- [ ] [REVIEW] P1. QG both repos green; **deploy deployment-api** (Cloud Build) so the live tab shows the real backlog +
      the cefi fix, and cite `Evidence: cloudbuild=<id>` SUCCESS. Verify the live endpoint returns `pending_shard_count`
      and cefi=ok.

## WS-2 — v2: truthful merged-per-tick histogram (DEFERRED — 🟡 UNDER DISCUSSION / nice-to-have)

> **Not built. Design captured so we don't lose it.** The consolidator job KNOWS its exact merge count (its merge step
> lists + reads every shard). Recording that per run gives an exact, durable histogram — replacing v1's inferred,
> session-only view. Deferred because it edits the consolidator job code and **redeploys ~10-20 Cloud Run Jobs + the AWS
> Batch mirror** — a data-correctness-critical-path change whose real cost is blast radius + rollout care, not dollars.

- [ ] [DESIGN] P3. **Store decision — OPEN.** GCS/S3 rolling history object (recommended: zero new IAM, each job writes
      its own cloud's bucket it already has objectAdmin on, reuses the endpoint read path; ~$2-4.50/mo GCS Class-A) vs
      Firestore (native TTL + query, cheaper writes ~$1/mo, `ci_status` precedent, BUT +IAM +client dep, and the AWS
      mirror would need GCP creds — cross-cloud). **Cost is negligible either way (< ~$5/mo); the decision is
      architecture-fit + blast radius.** OPEN sub-question: does the AWS Batch mirror actually consolidate any of the 5
      AGs (cefi/defi/tradfi/sports/prediction), or is it GCP-only? All 5 index buckets are GCP → if GCP-only, Firestore
      is clean same-cloud and the cross-cloud concern is moot.
- [ ] [INFRA] P3. **Instrument the job** — after each merge, append
      `{ts, asset_group, shards_merged, backlog_after,     rows_added, duration_ms}` (~15 lines; the merge already knows
      `len(shards)`). Rolling window cap (last 24-48h). Staged rollout (one AG first, verify, then fan out); rollback
      story documented.
- [ ] [BACKEND] P3. **Endpoint history** — `/api/health/consolidator` (or a `/consolidator/{ag}/history`) returns the
      last N runs; the UI swaps the inferred sparkline for the real merged/tick histogram (drop the "inferred" caption).

## Progress Log

- 2026-07-09 — Plan created (LOCAL). Verified: `BlobMetadata.last_modified` is available per blob → true backlog is a
  single-list computation (single-walk-safe). Consolidator runs every 1 min per-AG (Cloud Run Job + Scheduler). v1 needs
  ZERO consolidator change. v2 store/cost analysis captured; v2 deferred as nice-to-have pending the GCS-vs-Firestore +
  AWS-mirror-scope decision.
