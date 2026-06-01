---
title: "Pinned VM tarballs are pruned within seconds → VM-tarball code deploys are unreliable (race + prune)"
created: 2026-06-01
author: ikenna (slot 1)
source:
  - bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md (migration attempt-1 failure, 2026-06-01)
  - deployment-service/scripts/vm/create-code-tarballs.sh + setup-data-pipeline-vm.sh
  - codex/05-infrastructure/vm-tarball-deployment.md
locked_by: live-defi-rollout
---

# Pinned VM tarballs are pruned → VM-tarball code deploys are unreliable

## What I found

While running the legacy→canonical tick-bucket migration via the VM fleet (`VM_TASK=canonical-migration`), **all 20 VMs
failed exit-2**: the `mtds-code.tar.gz` they pulled did not contain the just-committed migration script. Diagnosis
uncovered THREE compounding deployment-infra problems:

1. **Floating-tarball race.** `setup-data-pipeline-vm.sh` pulls the floating `*-code.tar.gz` (no SHA). A parallel agent
   rebuilt `mtds-code.tar.gz` from a _different_ HEAD between my build and the VMs booting, so the VMs ran stale code.
   `create-code-tarballs.sh` itself documents this race but the default path does not avoid it.
2. **No mtds SHA-pin path.** `setup-data-pipeline-vm.sh` had pin cases for `unified-trading-library-code` /
   `unified-api-contracts-code` / `market-data-processing-service-code` but **NOT `mtds-code`** → the mtds tarball could
   only ever be pulled floating. (Added the missing case @deployment-service `58ee0a9`.)
3. **Pinned tarballs do not persist (the real blocker).** Even after a clean rebuild that logs
   `SHA-pinned copy: mtds-code@<sha>.tar.gz`, `gcloud storage ls gs://…/code/mtds-code@<sha>.tar.gz` returns _no object_
   seconds later. An aggressive prune cron deletes unreferenced pinned tarballs almost immediately, so the SHA-pin
   mechanism (the intended race fix) cannot be relied on for a freshly-built commit.

Additional aggravator: the slot worktree is under constant parallel-agent churn (UAC/UTL/MTDS dirtied by other agents),
so `create-code-tarballs.sh` (which blocks on a dirty tree) frequently aborts mid-build.

## Why it matters

This is a **cross-cutting infra blocker for every VM-tarball code deploy**, not just this migration. Any plan that
launches a VM running freshly-committed code is exposed:

- `defi_manifest_canonicalisation_2026_06_01.md` — "C0 — RUN ON A VM" (migrate_defi_canonical.py).
- `solana_defi_legacy_migration_2026_05_27.md`, the MDPS sharded backfills, sports rescans, etc. A VM can silently run
  **stale or wrong code** (or exit-2) while the dashboard shows it "ran" — a false-progress + data-correctness hazard.

## Recommended decision

Pick one (operator):

1. **Tune the prune cron** to retain pinned tarballs referenced by a launch (or for a TTL long enough to boot). Find the
   cron (likely a tarball-GC in deployment-service / a scheduler) and exclude `@<sha>` pins newer than e.g. 6h.
2. **Build into a dedicated, un-pruned bucket** for migration/one-shot launches (separate from the churned
   `deployment-scripts-…/code/` prefix).
3. **Add a `TARBALL_EXPECTED_SHA`-style per-repo verify** that fails the VM loudly (not exit-2 silent) when the pulled
   tarball's manifest sha ≠ the launcher's expected sha — at least converts silent-stale-code into a visible failure.

Until resolved, VM-tarball migrations should be treated as **BLOCKED-INFRA**; prefer local execution where the work is
pure GCS ops (e.g. the manifest-seed half of the bucket-SSOT remediation).

## Status

OPEN — `58ee0a9` added the mtds pin case (necessary but insufficient while pins are pruned). Awaiting operator decision
on prune-cron tuning vs dedicated bucket.
