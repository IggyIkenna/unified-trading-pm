---
doc_type: issue
title:
  "collect-* DeFi Terraform stagger already violates its own 02:25 UTC finish deadline — solana-defi/mev-events/
  bridge-events/lst-seasonal-rewards worst-case finishes land at 02:30-03:05 UTC"
summary: >-
  `deployment-service/terraform/gcp/defi_collection_scheduler.tf`'s header declares the 14-job `collect-*` stagger "must
  finish by 02:25 UTC" so the downstream features-onchain T+1 recon (claimed to start 02:30 UTC) sees fresh manifest
  entries, and already flags (2026-07-22 follow-up note) that `solana-defi` alone can finish ~02:30 — i.e.
  pre-existing-violated even before this doc. Recomputing worst-case (schedule-start + timeout_seconds) for every job
  scheduled in the 02:xx window confirms and extends that: `collect-solana-defi` finishes 02:30 UTC (exactly the claimed
  consumer start), `collect-bridge-events` finishes 02:35 UTC (10 min past the stated deadline), and
  `collect-lst-seasonal-rewards` (a separate file, deliberately scheduled AFTER the `collect-*` fan-out) finishes 03:05
  UTC — 35 min past its own stated consumer time. Separately, the downstream job both header comments cite by line
  number (`t1_batch_scheduler.tf:124-128` / `:131-135`, "features-onchain T+1 recon") does not exist at those lines, or
  anywhere, in the current file — the citation is stale and the claimed 02:30 UTC consumer deadline cannot currently be
  verified against a real Cloud Scheduler job.
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [defi, terraform, cloud-scheduler, t1-freshness, stagger, honest-absence]
related:
  [
    plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    plans/archive/issues/defi_five_never_captured_venues_fix_2026_07_22.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: 2026-07-28
parent_epic: defi_master
source: [data_engineering slot-16, 2026-07-28, dispatched via defi_satellite_ao_dispatch_batch1-016]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

## What I found

`deployment-service/terraform/gcp/defi_collection_scheduler.tf:28-33` declares the stagger contract for the 14
`collect-*` Cloud Run Jobs:

```hcl
# Stagger schedule (must finish by 02:25 UTC so features-onchain T+1 at
# 02:30 UTC sees fresh manifest entries — see t1_batch_scheduler.tf:124-128.
# NOTE (2026-07-22, residual_defi_pipeline_completion follow-up): this
# deadline already looked tight with 11 jobs (solana-defi alone can finish
# ~02:30) before mev-events/bridge-events were added below; flagged to the
# t1_batch_scheduler.tf owner separately, not silently absorbed here.)
```

So the file's own author already flagged this as tight-to-violated for `solana-defi` alone, on 2026-07-22, and
explicitly deferred the fix to "the `t1_batch_scheduler.tf` owner" rather than resolving it in this file. That flag was
never closed out with a tracked doc — this is that doc.

**Recomputing worst-case finish (`schedule` start-of-minute UTC + `timeout_seconds`) for every job in the 02:xx
window**, from `defi_collect_operations` (`defi_collection_scheduler.tf:77-183`):

| Job                     | `schedule`           | `timeout`      | Worst-case finish |
| ----------------------- | -------------------- | -------------- | ----------------- |
| `collect-solana-defi`   | `5 2 * * *` (02:05)  | 1500s (25 min) | **02:30 UTC**     |
| `collect-mev-events`    | `10 2 * * *` (02:10) | 900s (15 min)  | **02:25 UTC**     |
| `collect-bridge-events` | `15 2 * * *` (02:15) | 1200s (20 min) | **02:35 UTC**     |

`collect-solana-defi` lands exactly on the claimed 02:30 UTC consumer start (zero margin — the 2026-07-22 note's
"~02:30" estimate is confirmed precisely by the terraform's own `timeout_seconds`, not an approximation).
`collect-bridge-events` — one of the two jobs the 2026-07-22 note says were added _after_ that note was written — is
worse: its worst-case finish is **02:35 UTC**, 10 minutes past the file's own stated 02:25 UTC deadline and 5 minutes
past the claimed 02:30 UTC consumer start. This is the concrete instance of the deferred flag; it was never separately
tracked.

A second, adjacent job outside this file compounds the risk:
`deployment-service/terraform/gcp/lst_seasonal_rewards_scheduler.tf` declares `collect-lst-seasonal-rewards`,
deliberately scheduled to fire _after_ the `collect-*` fan-out completes (its own header, lines 33-39, places it at
"02:25 UTC ... BEFORE the features-onchain-service T+1 recon at 02:30 UTC"). Its actual declared schedule/timeout
(`lst_seasonal_rewards_scheduler.tf:81-87`): `schedule = "25 2 * * *"` (02:25 UTC), `timeout = 2400` (40 min) →
**worst-case finish 03:05 UTC** — 35 minutes past the 02:30 UTC consumer time its own header comment claims it precedes.

**A third finding, which undermines verifying any of the above against the real downstream consumer**: both header
comments cite `t1_batch_scheduler.tf` by line number for the "features-onchain T+1 recon" job that supposedly starts at
02:30 UTC — `defi_collection_scheduler.tf:29` cites `t1_batch_scheduler.tf:124-128`;
`lst_seasonal_rewards_scheduler.tf:37` cites `t1_batch_scheduler.tf:131-135`. Neither line range names a
features-onchain job in the current file: lines 123-127 are the `sports-fixtures-midnight` entry, and lines 156-160 are
`market-data-processing` (the file has since grown, so exact line numbers drift, but grepping the whole file for
`onchain` / `features-onchain` in `t1_batch_scheduler.tf`'s `t1_batch_services_all` map returns zero matches). A
corpus-wide grep across every `deployment-service/terraform/gcp/*.tf` file for a Cloud Scheduler job or Cloud Run Job
named `*onchain*t1-recon*` / `*features-onchain*t1*` also returns zero matches — the only `features-onchain-service`
resource in the whole terraform tree is the `lst-seasonal-rewards` collector itself
(`lst_seasonal_rewards_scheduler.tf:98`, `service_name = "features-onchain-service"`), which is a _producer_ into this
pipeline, not the T+1 recon _consumer_ the deadline exists to protect. So either the features-onchain T+1 recon job was
removed/renamed from `t1_batch_scheduler.tf` without updating these two header comments (stale cross-reference), or it
was never actually declared there. Either way, the "02:30 UTC" deadline these two files stagger against cannot currently
be confirmed against a live Cloud Scheduler resource.

## Why it matters

- **A documented, self-flagged deadline violation has sat untracked since 2026-07-22** — the file's own author wrote
  "flagged to the `t1_batch_scheduler.tf` owner separately, not silently absorbed here," which is exactly the kind of
  deferred-but-unretrieved flag the PM findings-triage rule exists to catch. Two more jobs (`bridge-events`,
  `lst-seasonal-rewards`) were added after that note without re-checking the deadline, and both worsen it (02:35 and
  03:05 UTC worst-case respectively, vs. the 02:25 UTC contract).
- **If the "features-onchain T+1 recon at 02:30 UTC" consumer genuinely still exists** (just relocated/renamed without
  the header comments being updated), it may be reading a manifest that `collect-solana-defi` / `collect-bridge-events`
  / `collect-lst-seasonal-rewards` haven't finished writing to yet on their worst-case (timeout-bound) days — a T+1
  staleness risk that would surface as a silently-incomplete features-onchain pass, not a loud failure, matching this
  corpus's honest-absence concerns.
- **If that consumer job no longer exists**, the entire staggering rationale in both files' headers is stale
  documentation describing a constraint that no longer binds anything — worth confirming either way so the next person
  staggering a new `collect-*`/onchain-adjacent job isn't solving for a deadline that's either still live and violated,
  or already moot.

## Recommended decision

- [ ] [INFRA] P1. Resolve the `t1_batch_scheduler.tf:124-128`/`:131-135` cross-reference: confirm whether a
      "features-onchain T+1 recon" Cloud Scheduler job currently exists anywhere in `deployment-service/terraform/gcp/`
      (git-blame/history search if it's genuinely gone from `t1_batch_scheduler.tf`) — if it exists under a new
      name/location, correct both header citations (`defi_collection_scheduler.tf:29`,
      `lst_seasonal_rewards_scheduler.tf:37`) to point at it; if it no longer exists, remove or rewrite both headers'
      deadline framing so they don't cite a phantom consumer. Repo: deployment-service. Source: this doc.
- [ ] [INFRA] P2. Once the real (or confirmed-absent) consumer deadline is established, either (a) re-stagger
      `collect-solana-defi` (02:05→earlier start or a shorter timeout budget) and `collect-bridge-events` (currently
      worst-case 02:35 UTC) so their worst-case finish lands at or before the confirmed deadline, or (b) if no live T+1
      consumer depends on a hard 02:25/02:30 UTC cutover, update the header comments to state the real constraint (or
      that there is none) instead of the current unverifiable one. Repo: deployment-service. Source: this doc.
- [ ] [INFRA] P2. Re-check `collect-lst-seasonal-rewards`'s 02:25 UTC start against whatever the P1 todo above
      determines is the real downstream deadline — its own 40-minute timeout budget (worst-case 03:05 UTC finish) is the
      single largest violation found in this doc. Repo: deployment-service. Source: this doc.
