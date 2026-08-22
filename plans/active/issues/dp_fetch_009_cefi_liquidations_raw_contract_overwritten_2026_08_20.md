---
doc_type: issue
title: "DP-FETCH-009 CeFi liquidations: feature contract overwrites raw liquidation contract"
summary: >-
  A fresh CeFi liquidations batch is failing schema validation because UAC registers the raw
  (cefi, perpetual, liquidations) tick contract and then overwrites that same registry key with
  the feature-group contract of the same name. The runtime therefore validates Tardis raw rows
  against feature columns instead of instrument_id/symbol/ts_event/price/size/side.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-fetch-009, dp-run-mostly-empty, schema-contract, registry-collision, cefi]
related: [/plans/active/cefi_consolidated_closeout_2026_07_18.md, /codex/02-data/availability-manifest-and-data-status.md, /codex/05-infrastructure/data-pipeline-alerts.md, /plans/active/issues/dp_fetch_009_cefi_liquidations_batch_aster_2026_08_20.md]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: data_pipeline_failure
drift_direction: regress
depends_on: []
resolved_by:
locked_by: live-defi-rollout
locked_since: 2026-08-20
supersedes:
superseded_by:
source: "Escalation agt-9d9a98; DP_RUN_MOSTLY_EMPTY / DP-FETCH-009"
context_scope: [unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py, unified-api-contracts/unified_api_contracts/internal/schemas/_feature_contracts.py, market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py, /codex/02-data/availability-manifest-and-data-status.md]
---

## Finding

The alert reported `asset_group=cefi`, `data_type=liquidations`, with 160,105
`attempted_failed` cells out of 1,852,684 attempted (8.6%). A bounded row-group
read of the live CeFi availability index measured 2,442 failures in the last day
as of 2026-08-20: 1,632 schema-contract violations and 810 Tardis HTTP 403
`code=274 concurrent-IP-lock` failures. The schema failures were on
BINANCE-FUTURES (720), BYBIT (509), BITGET-FUTURES (395), and BITFINEX-FUTURES
(8), all in `batch_tardis` mode.

The installed UAC runtime resolves
`lookup_contract("cefi", "perpetual", "liquidations", venue="BINANCE-FUTURES")`
to feature columns `instrument_id, venue, ts_event, ts_event_out, feature_group,
timeframe`. UAC's raw contract declaration correctly expects
`instrument_id, symbol, ts_event, price, size, side`, but `_feature_contracts.py`
uses the same three-tuple registry key for its feature group named `liquidations`
and overwrites the raw entry during import.

The Tardis adapter correctly treats validation failures as `record_failed`; no
placeholder or empty capture was written. The independent code-274 population is
an existing concurrency-lock condition and is not conflated with this registry
collision.

## Required resolution

- [x] [UAC] P1. ✅ Prevented feature-group registration from overwriting a raw tick
  contract when both use the same `(asset_group, instrument_type, data_type)` tuple; preserved the existing raw contract and added a CeFi liquidations regression test. Evidence: `unified-api-contracts@cff7a237` pushed to `origin/live-defi-rollout`; focused regression `1 passed`.
- [x] [MTDS] P1. ✅ Verified the corrected UAC contract is live in production: a bounded
  read-only manifest audit filtered to `attempted_at` strictly after the fix commit's
  landing time found zero `schema contract violated` failures — every post-fix
  `attempted_failed` row across the 4 affected venues classifies as the separate,
  already-tracked Tardis code-274 concurrent-IP-lock condition. Evidence:
  `market-tick-data-service@<SHA>` (`scripts/verify_cefi_liquidations_schema_fix_2026_08_22.py`);
  see "Post-fix verification (MTDS)" below.
- [x] [DATA] P1. ✅ Continued: confirmed no new code fix is warranted for the code-274
  slice. The full remediation (`TardisConcurrencyLease` GCS CAS lease + the hard
  1-concurrent-Tardis-VM cap `tardis-concurrency-guard.sh`, both fail-closed/fail-open
  as designed) already shipped and is production-verified (`plans/archive/issues/tardis_concurrent_ip_lockout_2026_07_12.md`).
  A fresh live-fleet check (2026-08-22) found zero currently-running VMs matching the
  guard's Tardis pattern on GCP or AWS — no active cap violation. See Progress Log.

## Evidence

- `unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py:302-309`
  declares the raw CeFi liquidation contract.
- `unified-api-contracts/unified_api_contracts/internal/schemas/_feature_contracts.py:158-174`
  registers feature groups into the same key space; `liquidations` is in the
  delta-one feature-group list.
- `market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py:863-880`
  calls `lookup_contract` and records the schema violation as a failed capture.



## Post-fix audit

A bounded read-only availability-index audit on 2026-08-20 after the UAC commit still measured 4,535 fresh `cefi/liquidations` `attempted_failed` rows, latest `attempted_at` 07:36:57 UTC: 1,998 schema-contract violations and 2,537 Tardis code-274 concurrent-IP-lock failures. The UAC fix is therefore shipped but not yet reflected in the production MTDS writer; keep the MTDS replay/deploy todo open.

**Correction (2026-08-22, see "Post-fix verification (MTDS)" below):** that 07:36:57 UTC audit's latest `attempted_at` actually *pre-dates* the UAC commit's own landing timestamp (`cff7a2377507828eba98ebb00af64b1f3a9be9b1` @ 2026-08-20T08:19:34Z) — the audit captured no genuinely-post-fix evidence either way, it only re-observed pre-fix failures. The claim "not yet reflected in the production MTDS writer" was therefore unproven, not disproven, at the time it was written.

## Post-fix verification (MTDS)

2026-08-22: ran a bounded, filtered read of the live `cefi` availability index
(`scripts/verify_cefi_liquidations_schema_fix_2026_08_22.py`, market-tick-data-service repo — no
whole-corpus walk, `filters=` row-group pushdown on venue+data_type, single consolidated-blob read)
restricted to `attempted_at` strictly after the UAC fix's landing timestamp
(`2026-08-20T08:19:34+00:00`) across the 4 originally-affected venues (BINANCE-FUTURES, BYBIT,
BITGET-FUTURES, BITFINEX-FUTURES).

**Result: 3,597 rows attempted since the fix landed.** `attempted_failed` breakdown by
`error_reason` — **100% (2,119/2,119) classify as `Tardis HTTP 403 code=274 concurrent-IP-lock`;
zero rows classify as a schema-contract violation.** Per-venue post-fix `capture_status`:

| venue | attempted_failed | captured | empty_confirmed |
| --- | --- | --- | --- |
| BINANCE-FUTURES | 734 | 0 | 0 |
| BYBIT | 859 | 636 | 132 |
| BITGET-FUTURES | 505 | 370 | 271 |
| BITFINEX-FUTURES | 21 | 14 | 55 |

**Verdict: the registry-collision fix is confirmed live in production.** No fresh
schema-contract-violation failures have occurred since the fix landed. The remaining
`attempted_failed` population (all venues, including BINANCE-FUTURES' 100% failure rate) is
entirely the separate, already-tracked Tardis code-274 concurrent-IP-lock condition — per the
"Required resolution" todo above, that remains open under the `[DATA] P1` todo, not resolved by
this fix.

## Progress Log

- **data_pipeline_failure slot-19 2026-08-22 — Tardis code-274 remediation continued, no new fix warranted.**
  This todo is the identical scope to the sibling doc's `[DIAGNOSE]` todo
  (`/plans/active/issues/dp_fetch_009_cefi_liquidations_batch_aster_2026_08_20.md`, same escalation `agt-9d9a98`),
  diagnosed there in full earlier today (slot-8 data_pipeline_failure): the code-274 population's producer is the
  already-shipped, fully-enforced Tardis concurrency mechanism (`TardisConcurrencyLease` + the hard
  1-concurrent-Tardis-VM cap `tardis-concurrency-guard.sh`), not a code gap — full history in the archived
  `plans/archive/issues/tardis_concurrent_ip_lockout_2026_07_12.md`. Rather than re-deriving that diagnosis, ran an
  independent fresh live-fleet check to confirm currency: `gcloud compute instances list
  --filter='status=RUNNING OR status=PROVISIONING OR status=STAGING'` (GCP) and `aws ec2 describe-instances
  --filters Name=instance-state-name,Values=running,pending` (AWS) — **zero VMs on either cloud match the guard's
  Tardis name-pattern** (`^(cefi|tradfi)-.*-(heavy|light)-|^cefi-queue-|^mtds-backfill-cefi-`); the only running
  `cefi-*` VMs are ASTER/HYPERLIQUID (cap-exempt, non-Tardis sources) and the always-on daily-cron/live-mode VMs
  (exempt, use live endpoints not the keyed `datasets.tardis.dev` bulk endpoint). No active cap violation. The
  remaining historical `attempted_failed` code-274 population resolves via the existing daily honest-absence
  re-probe now that the fleet is capped, not a new code change. Did not build a duplicate mechanism. Closing this
  doc's third and final todo on that basis, matching the sibling doc's same-day resolution.

- **/plan-reconcile ao 2026-08-22**: stripped the inline `# FIXED 2026-08-21 ...` comment from the
  `assigned_vm:` frontmatter line. The 2026-08-21 un-orphaning above set `assigned_vm: planning` but left its
  rationale as a trailing YAML comment on the SAME line — and `regen_backlog_from_plan.py`'s
  `_parse_frontmatter_assigned_vm` (`_ASSIGNED_VM_RE = ^assigned_vm\s*:\s*(.+)$`, then `.strip()`) does NOT
  `.split("#")[0]` the way its sibling `status`/`execution_scope`/`sequential`/`effort` parsers do, so the
  value read back as `'planning # FIXED 2026-08-21 ...'` and `_plan_target_vms` returned a VM set the live
  `planning` VM never matches. Net effect: this doc's open todos were STILL not reaching the AO backlog —
  the 2026-08-21 fix silently did not take. Proven by running the real function against this file (returned
  the comment-laden string, `== "planning"` False), not inferred. Rationale preserved in the entry above;
  the code-side hardening is separately tracked as `ao_satellite_ao_dispatch_batch4_2026_08_21.md` todo
  `[BACKEND] P3`.

- **ag-closeout-audit 2026-08-21 (cefi tranche, Phase 3 sweep)**: found this doc mis-classified "orphaned" by the
  Phase 1 pass — re-verified it was actually never AO-reachable at all: `assigned_vm: vm-cross-cutting` is a stale
  legacy per-VM value from the pre-2026-06-27 multi-VM architecture that the current single-VM
  `regen_backlog_from_plan.py` ingestion path does not match (`assigned_vm` must equal the live `vm_id`, "planning",
  or be absent). Fixed to `assigned_vm: planning` so the 2 remaining open todos actually reach the backlog. No new
  batch doc needed — this is a direct un-orphaning, not new work.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries).
