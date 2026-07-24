---
doc_type: issue
title: Pinned VM tarballs are pruned within seconds → VM-tarball code deploys are unreliable (race + prune)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, market-data-processing-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-01
author: ikenna (slot 1)
source:
  [
    "bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md (migration attempt-1 failure, 2026-06-01)",
    deployment-service/scripts/vm/create-code-tarballs.sh + setup-data-pipeline-vm.sh,
    /codex/05-infrastructure/vm-tarball-deployment.md,
  ]
locked_by: live-defi-rollout
---

# Pinned VM tarballs are pruned → VM-tarball code deploys are unreliable

> **ARCHIVED 2026-06-01 (slot 7).** RESOLVED — loud-fail SHA-pin path shipped (deployment-service@a0fcba7 +
> `MTDS_TARBALL_SHA` case @58ee0a9). Misdiagnosed as a prune cron; real bug was a silent fallback now fixed. Residual
> (non-blocking) `create-code-tarballs.sh` dirty-tree abort is captured as a verify-on-C0 follow-up in
> `plans/active/defi_manifest_canonicalisation_2026_06_01.md` § G (RUN-ON-VM loud-fail confirmation). No further work on
> this issue doc.

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

**RESOLVED 2026-06-01** — the blocker was misdiagnosed as a prune cron; the real bug was a silent fallback.

- **Diagnosis correction**: there is **no aggressive prune** — `code/` has no GCS lifecycle rule (only `vm-logs/` @14d)
  and `cleanup_old_tarballs.py` is wired to **no** cron/scheduler. Empirically @sha pins **persist** (394 `code/`
  objects incl. many `@<sha>.tar.gz`). The "pruned within seconds" symptom was either a build that aborted on a dirty
  tree (the aggravator) or the floating-tarball race (point 1) — never a prune.
- **Fix shipped** (deployment-service@a0fcba7, `setup-data-pipeline-vm.sh`): a **SHA-pinned pull is now authoritative**
  — (a) pinned-but-missing tarball → hard `exit 1` (was `WARNING … skipping` → the exit-2 silent-stale hazard); (b) a
  pinned pull verifies the **pinned** `@sha.manifest.json` (not the floating manifest a concurrent rebuild can move);
  (c) self-verify: the pinned manifest's `commit_sha` must match the requested pin (prefix-compare), and a pin with no
  manifest also hard-fails. Composes with the mtds pin case (`MTDS_TARBALL_SHA`, `58ee0a9`) + the `TARBALL_EXPECTED_SHA`
  assert already present.
- **Net**: a C0/C6/G1 VM launch now either runs the exact pinned commit or **fails loudly** — never silently runs stale
  code. L0 unblocked for the RUN-ON-VM todos.

Residual (non-blocking): `create-code-tarballs.sh` still aborts on a dirty tree under parallel-agent churn — build from
a clean slot worktree (operator slots are kept clean). Archive this issue once a C0 dry VM run confirms the loud-fail
path in practice.
