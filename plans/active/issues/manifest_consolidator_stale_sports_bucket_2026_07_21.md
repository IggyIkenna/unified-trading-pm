---
doc_type: issue
title:
  Manifest consolidator behind/down for instruments-store-sports-prd bucket — ManifestConsolidatorStaleError during live
  backfill
summary: >-
  During a live TRANSFERMARKT backfill VM run (tm-backfill-20260721-195637, 2026-07-21), date 2025-06-09's processing
  hit `unified_trading_library.manifest_writer._state.ManifestConsolidatorStaleError`: the consolidated
  availability_index for bucket `instruments-store-sports-prd-central-element-323112` was >120s stale (measured 233.6s,
  later 306-360s on subsequent reads) while per-VM shards existed, and the read path correctly refused to fall back to a
  per-VM shard merge (documented OOM-avoidance guard) rather than silently degrading. Shard-level failure isolation
  caught the exception and the run continued to the next date without crashing, but 06-09 was left uncaptured until a
  second VM run re-fetched it. Found as a side effect of an unrelated cache-hit validation task, not a targeted
  investigation.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-library, deployment-service]
scope: [engineer]
tags: [manifest, consolidator, staleness, sports, transfermarkt, backfill, infra]
related: [plans/active/issues/batch4_strategy_ui_archived_plan_residuals_2026_07_21.md]
created: "2026-07-21"
parent_epic: infrastructure_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [batch4_strategy_ui_archived_plan_residuals-003]
resolved_by:
locked_by:
depends_on: []
---

# What I found

While running a TM backfill VM (`tm-backfill-20260721-195637`) for an unrelated cache-hit-speedup validation task, date
`2025-06-09`'s processing raised:

```
unified_trading_library.manifest_writer._state.ManifestConsolidatorStaleError: Consolidated availability_index for
bucket='instruments-store-sports-prd-central-element-323112' is stale or missing (older than
MANIFEST_CONSOLIDATED_STALENESS_SEC=120s) while per-VM shards exist — the manifest consolidator is behind or DOWN.
Refusing to fall back to the per-VM shard merge (can OOM on large buckets). Remediation: fix the consolidator Cloud
Run Job + Scheduler for this bucket; set MANIFEST_ALLOW_STALE_FALLBACK=true to force the recovery merge.
```

Subsequent reads in the SAME run kept logging
`ManifestReader: consolidated blob age Ns > 120s threshold — falling back to per-VM shards` with the staleness growing
across the run (233.6s → 306.5s → 341.9s → 345.3s → 360.4s), confirming the consolidator was NOT catching up during the
~1h10m the VM ran — it's been behind or down for a sustained period, not a single transient blip.

**Impact observed**: the exception was raised inside the per-shard processing loop for date 06-09 and was CAUGHT cleanly
by shard-level failure isolation (per `codex/04-architecture/shard-level-failure-isolation.md`) — the run logged the
error and continued to date 06-10 without crashing. This is the correct resilience behavior. But it meant 06-09's data
was never captured in that run; a second, unrelated re-run of the same window had to re-fetch it (confirmed: 06-09
succeeded on retry, 127 teams captured, ~2m45s).

# Why it matters

The manifest consolidator being behind/down for this bucket means:

1. Every read for this bucket pays the per-VM-shard-merge fallback path instead of the fast consolidated-index path
   (visible cost: every date's `TRANSFERMARKT short-circuit` check logged the staleness warning).
2. Any date/shard that happens to hit the consolidator at the wrong moment (mid-write, or during a sustained outage like
   this one) can hard-fail rather than degrade — by design, since the guard explicitly refuses an OOM-risking
   full-bucket merge. That's the right call structurally, but it means a DOWN consolidator directly costs real backfill
   coverage (06-09 here), not just latency.
3. This wasn't caught by any existing monitor before I stumbled into it — worth checking whether the consolidator's
   Cloud Run Job + Scheduler has its own health/staleness alerting for the sports bucket specifically.

# Recommended decision

Not investigated further — this was a side-effect finding during unrelated work, not a targeted diagnosis. Filing so
someone with consolidator visibility can check whether the Cloud Run Job/Scheduler for
`instruments-store-sports-prd-central-element-323112` is genuinely down, and if so, restart/fix it and confirm the
consolidated blob catches up (staleness should trend back toward 0, not keep growing).

## Todos

- [ ] [INFRA] P2. Check the manifest-consolidator Cloud Run Job + Scheduler status for
      `instruments-store-sports-prd-central-element-323112` — confirm whether it's genuinely down/erroring or just
      lagging under load, and get the consolidated blob's staleness trending back down. (repo: unified-trading-library
      or the consolidator's owning infra repo — grep `codex/05-infrastructure/manifest-consolidator-ssot.md` for the
      exact deployment target)
- [ ] [INFRA] P3. Consider whether this bucket/consolidator pairing needs its own staleness alert (the 120s threshold
      being breached for 1h10m+ straight during a live backfill went unnoticed until an unrelated task's logs surfaced
      it). (repo: deployment-service or wherever consolidator alerting lives)

## Codex SSOTs

`codex/05-infrastructure/manifest-consolidator-ssot.md`, `codex/04-architecture/shard-level-failure-isolation.md`.
