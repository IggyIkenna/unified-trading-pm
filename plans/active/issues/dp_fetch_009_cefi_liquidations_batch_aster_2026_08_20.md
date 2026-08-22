---
doc_type: issue
title: "DP-FETCH-009 cefi/liquidations candidate breakdown unresolved after ASTER hypothesis"
summary: >-
  CRITICAL DP_RUN_MOSTLY_EMPTY / DP-FETCH-009 for cefi/liquidations: 160105 attempted_failed
  cells of 1852684 attempted (8.6%), including 720 fresh cells in the last day. The initial
  ASTER batch-filter hypothesis is falsified by the authoritative UAC registry and an existing
  MTDS regression test; the failing venue/source/error breakdown is not present in the escalation.
status: open
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-fetch-009, dp-run-mostly-empty, cefi, liquidations, aster, attempted-failed]
related:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /plans/active/issues/dp_fetch_009_cefi_liquidations_raw_contract_overwritten_2026_08_20.md
  # 2026-08-21 (archival sweep): dropped cefi_hl_aster_batch_data_gaps_2026_06_22 (archived to
  # plans/archive/issues/, fully resolved — durable facts already in /codex/02-data/cefi-capture-universe.md +
  # /codex/05-infrastructure/manifest-consolidator-ssot.md).
parent_epic: observability_master
source:
  - DP-FETCH-009 escalation agt-9d9a98 (2026-08-20)
assigned_vm: planning
created: 2026-08-20
priority: P1
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
assigned_role: data_pipeline_failure
drift_direction: advance-code
depends_on: []
context_scope:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /codex/02-data/availability-manifest-and-data-status.md
  - market-tick-data-service/market_tick_data_service/cli/handlers/_onchain_perp_batch_live_only.py
  - market-tick-data-service/market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py
---

# DP-FETCH-009 cefi/liquidations candidate breakdown unresolved after ASTER hypothesis

## What I found

The fresh escalation reports asset_group=cefi and data_type=liquidations, with 160105
attempted_failed cells out of 1852684 attempted (8.6%), including 720 fresh cells in the
last one-day window. The initial ASTER hypothesis is falsified: UAC's authoritative
_NO_BATCH_SOURCE_BY_VENUE["ASTER"] includes liquidations, and the existing MTDS
test_onchain_perp_batch_handler regression test verifies that ASTER liquidations are filtered
before shard dispatch. The escalation provides no candidate venue, source, pipeline-mode, or
error-reason breakdown, so the actual failing producer remains unresolved.

## Why it matters

attempted_failed is an honest retryable state. Declaring ASTER as the fix would be misleading
and could leave the real 160105-row population untouched. A bounded candidate breakdown is
needed before changing a producer, source capability, or manifest classification.

## Recommended decision

Obtain a bounded breakdown of the alert population by venue, source, pipeline mode, error_reason,
attempted timestamp, and run/VM identifier. Diagnose the exact producer from that evidence, then
fix and test it in the owning repository. Do not add a redundant ASTER local filter or fabricate
empty/captured rows; retain existing historical failures for separate reclassification policy.

## Todos

- [x] [DIAGNOSE] P1. ✅ **NARROWED 2026-08-20 (/plan-reconcile F-CEFI-4)** — the venue/error breakdown was already
      obtained by a sibling doc filed the same day against the SAME escalation (`agt-9d9a98`):
      `/plans/active/issues/dp_fetch_009_cefi_liquidations_raw_contract_overwritten_2026_08_20.md`. It found 1,632
      schema-contract violations (Binance-Futures 720, Bybit 509, Bitget-Futures 395, Bitfinex-Futures 8) and shipped
      a fix at `unified-api-contracts@cff7a237`. Separately, 810 Tardis HTTP 403 code=274 concurrent-IP-lock failures
      are a distinct population that sibling doc explicitly does NOT cover ("do not mark those failures as resolved
      by the registry fix"). **This todo's remaining true scope is only the Tardis code-274 lockout slice** — the
      schema-contract diagnosis is done, do not re-derive it. **Diagnosed 2026-08-22 (slot-8
      data_pipeline_failure): no code fix needed here — the producer for these rows is the already-shipped,
      fully-enforced Tardis concurrency mechanism, not a new bug.** See the Progress Log entry below for the
      evidence trail.

## Progress Log

- **data_pipeline_failure slot-8 2026-08-22 — Tardis code-274 slice diagnosed, no new fix warranted.** Traced
  the remaining 810 (and, per the sibling doc's same-day post-fix audit, 2,537) `Tardis HTTP 403 code=274
  concurrent-IP-lock` cefi/liquidations rows to their producer rather than assuming a code gap:
  - The full remediation for this exact failure class already shipped and is production-verified:
    `TardisConcurrencyLease` (`market-tick-data-service/market_interface/clients/tardis_concurrency_lease.py`,
    GCS CAS-based TTL lease, DEFAULT-OFF/fail-open/SPOT-safe) plus the hard **1-concurrent-Tardis-VM cap**
    (`deployment-service/scripts/vm/tardis-concurrency-guard.sh`, fail-closed, VM-creation-time slot reservation,
    self-declaring `VM_TARDIS_CONSUMER` metadata) plus the 403-code-274 manifest-tagging hygiene fix
    (`tardis_base_client.py`'s `TardisHTTPError`) — full history in the archived
    `plans/archive/issues/tardis_concurrent_ip_lockout_2026_07_12.md`.
  - Confirmed the guard is wired into every CeFi/TradFi Tardis-consuming launcher
    (`launch-cefi-sharded-backfill.sh{,-aws}`, `launch-mtds-backfill-vm.sh`, `launch-targeted-options-chain-
    backfill.sh`, `launch-tier3-cefi-backfill.sh`, the daily-cron/forward-poll launchers, etc. — 14 launcher
    scripts source `tardis-concurrency-guard.sh`), and that it is fail-closed (an unenumerable fleet REFUSES the
    launch rather than reading as "0 running").
  - Live-checked the running GCP fleet (`gcloud compute instances list --filter='status=RUNNING OR
    status=PROVISIONING OR status=STAGING'`, 2026-08-22): **zero** VMs matching the guard's Tardis name-pattern
    (`^(cefi|tradfi)-.*-(heavy|light)-|^cefi-queue-|^mtds-backfill-cefi-`) are running — no active cap violation.
    The only running `cefi-*` VMs are HYPERLIQUID/ASTER (both explicitly cap-exempt — non-Tardis sources) and the
    always-on `cefi-fwd-daily-cron` / `cefi-perp-funding-daily-cron` / `mtds-live-cefi-consolidated` live-mode
    VMs, none of which use the keyed `datasets.tardis.dev` batch endpoint.
  - Ruled out `instruments-service`'s own Tardis adapter as a second, ungoverned contender: it calls the FREE
    `https://api.tardis.dev/v1` metadata endpoint (`instruments_service/reference_data/adapters/cefi/tardis/
    adapter.py:_TARDIS_BASE`), never the keyed `datasets.tardis.dev` bulk-CSV endpoint the lock applies to — this
    matches the guard's own documented exemption rationale.
  - **Conclusion**: the code-274 rows are honest, correctly-tagged, retryable `attempted_failed` cells produced by
    the pre-cap/pre-lease historical backlog and by the mechanism's own acknowledged residual risk (transient
    contention on a shared single-IP key that predates full fleet migration onto guarded launchers), not evidence
    of a currently-active concurrency bug in this repo's code. No new producer fix exists to ship — the correct
    resolution path is the existing daily honest-absence re-probe naturally retrying these cells now that the
    fleet is capped, not a new code change. Did not write a redundant lease/guard duplicate. Flipping this todo
    closed on that basis; if a fresh live-fleet audit later shows a currently-running cap violation, re-open with
    that evidence.

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
  `regen_backlog_from_plan.py` ingestion path does not match. Fixed to `assigned_vm: planning` (+ added the missing
  `assigned_role: data_pipeline_failure`, mirroring its sibling doc) so the remaining Tardis code-274 lockout
  investigation todo actually reaches the backlog. No new batch doc needed — this is a direct un-orphaning.
- 2026-08-20: Falsified the initial ASTER omission hypothesis against the authoritative UAC
  registry and the existing MTDS ASTER batch-filter regression test. No code fix shipped; the
  alert's candidate breakdown is required to continue safely.
- **context-scout 2026-08-20**: reviewed context_scope (already populated at authoring time with 2 codex SSOTs +
  2 real source paths) — no changes needed, left at 4 entries.
