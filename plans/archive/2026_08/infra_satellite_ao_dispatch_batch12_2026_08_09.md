---
doc_type: plan
title: Infra satellite AO batch 12 — managed-by launcher label standardization (batch1's last cleared deferral)
summary: >-
  Twelfth AO-dispatch batch for the `infra` topic tranche. Single source: the one remaining CLEARED-but-unbatched item
  from `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s Deferred section (item 5, "`managed-by` launcher label
  standardization") — re-checked by that batch's own finalize plan
  (`infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` todo 2, 2026-08-09) and confirmed CLEARED: both competing
  claims on the adjacent files (this batch's own PROGRESS.json launcher-lib rollout, and the Cloud-Run job terraform
  `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` touched) have shipped, so the collision risk that
  originally parked this item is gone. Drafted as batch1 archives so the item is not lost to archival. Low value on its
  own (the source doc's own text: `launched_by` already answers "who launched this" for most operator purposes) — P3,
  single bounded todo.
status: complete
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [infra, ao-dispatch, satellite-docs, batch-12, vm-launcher, labels]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch12_finalize_2026_08_09.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: infra
effort: medium
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
supersedes:
superseded_by: /plans/archive/2026_08/infra_satellite_ao_dispatch_batch12_2026_08_09.md
depends_on: []
source: >-
  `infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` todo 4 (archival of batch 1) — migrating batch 1's last
  cleared-but-unbatched Deferred item into a real home per the finalize plan's "nothing may be lost to archival" step.
---

# Infra satellite docs — AO dispatch batch 12

> **ARCHIVED 2026-08-10** — Single todo shipped and verified (slot 17, infra, 2026-08-10): an investigation into
> `managed-by=deployment-service` GCE launcher-label coverage confirmed all 35 `grep -L` hits already carry the label at
> runtime via shared helpers, per-family libs, or child-launcher delegation — 0 genuine gaps. Closed out by
> `/plans/active/infra_satellite_ao_dispatch_batch12_finalize_2026_08_09.md`. No Deferred items; source-doc
> reconciliation completed in batch 1's own finalize (`infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`).

## Why this plan exists

`infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s Deferred item 5 parked `managed-by` launcher-label standardization
because it touched `deployment-service/scripts/vm/launch-*.sh` (adjacent to that batch's own in-flight PROGRESS.json
launcher-lib rollout) and Cloud-Run job terraform (which `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` was
also touching). Both competing claims have since shipped (re-verified by the finalize plan's todo 2, 2026-08-09),
clearing the collision. Live re-measurement (2026-08-09): `142/177` `launch-*.sh` scripts under
`deployment-service/scripts/vm/` set a `managed-by=deployment-service` GCE label; `35` do not.

## Conflict check (before drafting)

- Grepped every active + archived `infra_*batch*`/`*finalize*` doc and
  `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` for `managed-by.*launcher\|launcher label` — no other live
  claim on this delta.
- The PROGRESS.json launcher-lib rollout (batch 1) and the Cloud-Run terraform (cross-cutting batch1b) are both fully
  shipped/archived — no active edit in flight on either adjacent surface.

## Todos

- [x] ✅ [INFRA] P3. **Standardize the `managed-by=deployment-service` GCE label across all
      `deployment-service/scripts/vm/launch-*.sh` launchers.** Live-measured 2026-08-09: 35 of 177 launchers omit the
      label (`grep -L 'managed-by=' scripts/vm/launch-*.sh` lists the exact set). Add the label to each missing
      launcher's `--labels=` gcloud invocation, following the existing `purpose=...,...,managed-by=deployment-service`
      convention already used by the 142 conformant launchers (see `launch-backfill-candle-manifest-vm.sh:181` for the
      reference shape). Done when: `grep -L 'managed-by=' scripts/vm/launch-*.sh` returns empty, and `quality-gates.sh`
      stays green (shell-script tests, if any, unaffected — this is a label-string addition only, no control-flow
      change). Source: `infra_satellite_ao_dispatch_batch1_2026_07_26.md` Deferred item 5. Repo: deployment-service. —
      **INVESTIGATED 2026-08-10 (slot 17, infra) — 0 genuine runtime gaps found; no code change made.** The naive
      `grep -L 'managed-by=' scripts/vm/launch-*.sh` text-search this todo's own "Done when" criterion relies on is a
      false-positive generator: it greps each launcher FILE's own text for the literal string, but doesn't account for
      indirection — a launcher that sources a shared helper or delegates to a child launcher gets the label injected at
      RUNTIME without the string appearing in its own file. Traced all 35 hits (still exactly 35 on re-measure today,
      out of 180 launchers now on disk vs. 177 at drafting — corpus grew, ratio held) to their actual
      `gcloud compute instances create` / `aws ec2 run-instances` call site and confirmed every one already carries the
      label or its cross-cloud equivalent: - **8 files** call `lc_gcloud_create`
      (`scripts/vm/lib/launcher_common.sh:528`), which unconditionally appends `,managed-by=deployment-service` to every
      `labels_str` at line 542 ("Appended centrally here so all launchers inherit it without a per-copy edit") —
      `launch-canonical-smoke-vm.sh`, `launch-deribit-options-chain-daily.sh`, `launch-footystats-forward-poll.sh`,
      `launch-instruments-smoke-vm.sh`, `launch-pipeline-e2e-check-driver-vm.sh`, `launch-prediction-arb-detector.sh`,
      `launch-qg-snapshot-vm.sh`, `launch-scenario-runner-vm.sh`. - **11 files** (`launch-tradfi-bf-*.sh`) source
      `_tradfi-ohlcv-launcher-lib.sh`, whose `ohlcv_create_vm()` (line ~400) has `managed-by=deployment-service` baked
      directly into its own unconditional `--labels=` line —
      `launch-tradfi-bf-{cboe-indices-ohlcv-24h,cboe-ohlcv-1m,cfe-ohlcv-1m,cme-ohlcv-1m,fred,fx-ohlcv-24h,       ice-ohlcv-1m,ice-ohlcv-24h,krx-equities-ohlcv-24h,nasdaq-ohlcv-1m,nyse-ohlcv-1m}.sh`. -
      **10 files** are AWS EC2 launchers (`*-aws.sh` + `launch-ec2-vm.sh`/`launch-orchestrator-worker-vm.sh`) — zero
      `gcloud compute instances create` calls in any of them (verified via grep count), so the GCE `managed-by=` label
      doesn't apply; they all route through `lib/aws_ec2_launch_lib.sh`, which centrally injects the
      cross-cloud-equivalent `managed-by=deployment-service` EC2 TAG at line 170 ("the GCP managed-by label" — the lib's
      own comment names the parity explicitly). - **1 file** (`launch-data-pipeline-fleet-monitor.sh`) isn't a
      compute-instance launcher at all — it fires an already-provisioned Cloud Run Job (`gcloud run jobs execute`);
      terraform owns that Job's config, there is no GCE instance to label. - **5 files** are thin wrappers/orchestrators
      with no `gcloud`/`aws` call of their own, each delegating to an already-labeled child launcher (verified each
      child directly contains `managed-by=`): `launch-cefi-week-test.sh` → `launch-cefi-forward-poll.sh`;
      `launch-expected-universe-v2-historical-backfill-vm.sh` → `launch-expected-universe-v2-vm.sh`;
      `launch-features-backfill-vm.sh` (DEPRECATED shim) → `launch-features-vm.sh`;
      `launch-features-onchain-backfill-vm.sh` (DEPRECATED shim) → `launch-features-backfill-vm.sh` →
      `launch-features-vm.sh`; `launch-sku-matrix-v2-benchmark.sh` → `launch-synthetic-benchmark-vm.sh`. 8+11+10+1+5 =
      35, fully accounted for. The underlying provenance goal this todo exists for ("a live GCE instance WITHOUT this
      label is provably ad-hoc") already holds for every one of these 35 — mechanically satisfying the literal `grep -L`
      criterion by inserting a redundant `managed-by=deployment-service` string into files that either have no
      `--labels=` flag to attach it to (the Cloud Run trigger, the pure wrappers) or would duplicate a label the shared
      helper/child already injects, would be dead/misleading code, not a real fix — against this workspace's own
      no-dead-code / no-redundant-validation standard. No `deployment-service` commit made; closing with this
      investigation as the evidence. Repo: unified-trading-pm (this doc only).

## Operator approval gate

**RULED 2026-08-09 (operator, bulk approval): approved.** Flipped `status: draft` → `status: active` in
`unified-trading-pm@78e91572f3` ("flip 14 satellite-extraction batches draft->active for AO dispatch") alongside 13
sibling batches (ao batch9-16, infra batch11-14, prediction batch10, sports batch12); its finalize twin was drafted
alongside it, gated on this plan per the finalize-plan-coverage rule. This banner was stale (still read "awaiting
review" against an already-`active` frontmatter) until fixed by `/ag-closeout-audit infra` 2026-08-10.

## Codex SSOTs (read before touching a todo)

- `/codex/05-infrastructure/vm-launcher-runbook.md` — launcher conventions
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — archival ritual the finalize plan runs
- `/plans/active/task_template.md` §4 — finalize-plan-coverage rule

## Progress Log

- **2026-08-09 (slot-31)** — Drafted while archiving `infra_satellite_ao_dispatch_batch1_2026_07_26.md`
  (`infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` todo 4), to give batch 1's one remaining
  cleared-but-unbatched Deferred item (item 5) a real home before archival. Paired with
  `infra_satellite_ao_dispatch_batch12_finalize_2026_08_09.md` per the finalize-plan-coverage rule.
- **2026-08-10 (slot 17, infra)** — Only todo shipped (investigation, no code change): re-measured the 35-launcher set
  (still 35/180, matching the original 35/177 ratio), traced each to its actual `gcloud compute instances create` /
  `aws ec2 run-instances` call site, and confirmed all 35 already carry `managed-by=deployment-service` (or the
  cross-cloud AWS-tag equivalent) at runtime via a shared helper, a shared per-family lib, or delegation to an
  already-labeled child launcher — see the todo's own evidence block for the full per-file breakdown. 0 genuine gaps;
  the naive per-file grep this todo's "Done when" criterion used doesn't account for indirection. This plan is now
  archival-eligible, gated on its finalize twin (`infra_satellite_ao_dispatch_batch12_finalize_2026_08_09.md`).
