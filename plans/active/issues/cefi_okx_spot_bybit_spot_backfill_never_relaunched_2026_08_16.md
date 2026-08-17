---
doc_type: issue
title:
  "OKX-SPOT + BYBIT-SPOT CeFi backfill VM died (ordinary SPOT preemption, not OOM) and was never relaunched — real
  coverage gap still open"
summary: >-
  `cefi-queue-heavy-okxspot-x2-20260815-151408` (SINGLE_VM_QUEUE=1, OKX-SPOT+BYBIT-SPOT bundled, heavy tier,
  2025-01-01→2026-08-14 target range) died after ~31 minutes on 2026-08-15. Initial read mistook this for an OOM
  death; the deployment record's actual `host_metrics_window` samples show real memory dropped to ~7-8% and stayed
  low right up to the last sample before the VM disappeared — `reap_reason: "vm_not_running"` confirms ordinary SPOT
  preemption, the same pattern as every other VM death this session, not a memory-sizing problem. No progress was
  banked (no `PROGRESS.json` ever written) — both venues still have substantial real, never-attempted coverage gaps:
  OKX-SPOT 123/~561 days captured (~22%), BYBIT-SPOT 44/~561 days captured (~8%), each with hundreds of thousands of
  `expected_unattempted` rows in the 2025-01-01→2026-08-14 target range. This backfill has NOT been relaunched.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [cefi, tardis, spot-preemption, backfill-gap, okx-spot, bybit-spot]
related:
  [
    /plans/active/cefi_tardis_date_concurrency_2026_08_16.md,
    /plans/archive/issues/vm_relaunch_under_new_name_cannot_resume_prior_progress_checkpoint_2026_08_12.md,
    /plans/active/issues/cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16.md,
  ]
parent_epic: cefi_master
source: "Interactive session 2026-08-16/17, slot 4 — operator asked whether another VM had been blocked/forgotten
  during the queue-mode incident investigation; this doc captures the resulting chat-only findings that were never
  written down before context compaction"
assigned_vm: NA
created: 2026-08-16
resolved_by:
locked_by:
locked_since:
priority: P1
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/cefi_tardis_date_concurrency_2026_08_16.md,
    /plans/archive/issues/vm_relaunch_under_new_name_cannot_resume_prior_progress_checkpoint_2026_08_12.md,
    deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh,
  ]
---

# OKX-SPOT + BYBIT-SPOT backfill: real gap, never relaunched

## What happened

`cefi-queue-heavy-okxspot-x2-20260815-151408` launched 2026-08-15T15:17:54Z with
`VENUES="OKX-SPOT BYBIT-SPOT" YEARS="2025 2026" LAUNCH_GROUPS=heavy SINGLE_VM_QUEUE=1`, target range
`start_date=2025-01-01 end_date=2026-08-14` (deployment record `d8f22c81-a7c8-4a4a-9ad1-a2839fabaa93`). Died at
`completed_at=2026-08-15T16:00:02Z` (~31 min runtime), `exit_code=125`, `status=failed`,
`reap_reason: "vm_not_running"`.

**Corrected diagnosis** (initial read was wrong, corrected same session): the run.log's own `peak_rss=82,617.3MB`
line looked alarming at first glance and was initially read as an OOM death. The deployment record's real
`host_metrics_window` (whole-VM `mem_pct` samples, not the per-task figure in that log line) tells a different
story: `mem_pct` was 36.7%→47.6%→48.1% then dropped sharply to 7.7%/7.5%/8.3%/7.8%/8.0%/7.8%/7.8% and stayed there
through the last sample at `15:49:30Z`. Real memory was LOW, not high, right before the VM vanished.
`reap_reason: "vm_not_running"` means the whole GCE instance disappeared — consistent with ordinary SPOT
preemption (the same pattern already documented for every other VM death this session,
`vm_relaunch_under_new_name_cannot_resume_prior_progress_checkpoint_2026_08_12.md`), not a process-level OOM kill
(which would leave the VM running with the python process dead).

## Real coverage gap (checked live, not assumed)

Manifest query (`market-data-tick-cefi-prd-central-element-323112`, `data_type IN [trades, book_snapshot_5]`,
`date >= 2025-01-01`):

| venue     | distinct captured dates | expected_unattempted rows | empty_confirmed | attempted_failed |
| --------- | ------------------------ | -------------------------- | ---------------- | ----------------- |
| OKX-SPOT  | 123 (of ~561 in range, ~22%) | 556,298 | 96,115 | 199 |
| BYBIT-SPOT | 44 (of ~561 in range, ~8%)   | 327,555 | 47,584 | 1,312 |

This is real, substantial, never-attempted work — not a nearly-finished job. No `PROGRESS.json` was ever written
for the dead VM, so nothing was banked; a relaunch starts from the same gap.

## Recommended relaunch shape (not yet executed)

Two SEPARATE solo per-venue launches, not bundled via `SINGLE_VM_QUEUE=1` — mirrors what worked for the
BINANCE-FUTURES resume this session (see `cefi_tardis_date_concurrency_2026_08_16.md`) and avoids the queue-mode
false-empty-confirmed bug class documented in `cefi_queue_mode_tier3_sentinel_false_empty_confirmed_2026_08_16.md`
(now fixed at the code level, `market-tick-data-service@bd07cfc3`, but per-venue solo launches remain the safer
shape regardless):

```
VENUES="OKX-SPOT"   YEARS="2025" ONLY="OKX-SPOT:2025:heavy"   START_DATE="2025-01-01" ...
VENUES="BYBIT-SPOT" YEARS="2025" ONLY="BYBIT-SPOT:2025:heavy" START_DATE="2025-01-01" ...
```
(then a 2026 pass after each 2025 pass completes, same year-scoping mechanism). Both machine types would default to
`n2-highmem-16` (128GB) per the registry floor — confirmed identical to BINANCE-FUTURES via
`launch_budget_registry.machine_type_for(task="cefi-backfill", venue=...)`, already right-sized, no downsize
possible. Both now also benefit from the shipped Tier-3 sentinel existence-check fix and, once
`cefi_tardis_date_concurrency_2026_08_16.md`'s Phase 3 work is validated further, could use
`--batch-date-concurrency 3` for the same ~1.5x speedup confirmed on BINANCE-FUTURES — but should launch WITHOUT it
first if launched before that plan's own remaining validation work (concurrency-6 step, watermark-bug fix) is
resolved, to avoid compounding two in-flight changes on the same launch.

**Gated on**: the Tardis N=1 concurrent-VM cap — cannot launch either venue while the BINANCE-FUTURES resume
(`cefi-binance-futures-2026-heavy-20260817-010713` as of this doc's filing) or any other Tardis-consuming VM is
running. Check `gcloud compute instances list` for the current cap-relevant fleet before launching.

## Todos

- [ ] [DATA] P1. Relaunch OKX-SPOT solo (`ONLY=OKX-SPOT:2025:heavy START_DATE=2025-01-01`), once the Tardis N=1 slot
      is free. Gate behind `cefi_tardis_date_concurrency_2026_08_16.md`'s own remaining Phase 3 items settling first
      if both would otherwise want the same slot around the same time — don't race two in-flight investigations for
      the one VM.
- [ ] [DATA] P1. Relaunch BYBIT-SPOT solo (`ONLY=BYBIT-SPOT:2025:heavy START_DATE=2025-01-01`), same gating.
- [ ] [DATA] P2. After each venue's 2025 pass completes, launch its 2026 pass (`YEARS=2026`, dynamic end-date to
      yesterday, same `ONLY=`-scoped single-venue pattern).

## Progress Log

- 2026-08-16/17 — Filed retroactively during the `/pre-compact` ritual: this investigation (corrected OOM→SPOT-
  preemption diagnosis, live coverage-gap measurement, proposed relaunch shape) happened entirely in chat during the
  same session as the CeFi Tardis date-concurrency work and was never written to a tracked doc before this
  checkpoint — caught by the ritual's Step 1 audit rather than lost to compaction. No relaunch has been attempted
  yet; explicitly gated behind the Tardis N=1 slot, which was in continuous use by the BINANCE-FUTURES resume/canary
  work for the rest of this session.
- **na-eligibility-audit 2026-08-17 (cefi tranche)** [body-hash:472458851b18a12a]: KEEP-NA, valid — first audit pass (fresh doc, created 2026-08-16, no prior marker). All 3 open items DEPENDENCY_BLOCKED on the same Tardis N=1 concurrent-VM slot occupied by the live BINANCE-FUTURES backfill tracked in the sibling `cefi_tardis_date_concurrency_2026_08_16.md` plan (~316 days remaining at observed pace). A fully-specified relaunch command exists (§ "Recommended relaunch shape") but is not yet practically actionable, and sequencing against the sibling in-flight investigation for the one shared VM is a real coordination judgment, not a mechanical dispatch. Doc stays assigned_vm: NA.
