---
doc_type: issue
title:
  features-onchain-defi VM uv-pip-install hits unsatisfiable resolution — risk-and-exposure-service==0.1.0 vs
  unified-api-contracts>=0.2.38
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-service,
    execution-service,
    features-service,
    unified-api-contracts,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-16
author: ikenna-slot-3
resolved: 2026-05-17
resolution:
  SHIPPED — 3 dep-pin fixes (risk-and-exposure-service@83b10e0 UAC pin, ml-training-service@876f0e5 UTL pin) +
  deployment-service@a6f746f registered features_service in SERVICE_TARBALLS (proper fix; reverts wrong-direction NODEPS
  hack). VM 8 (features-onchain-defi-20260517-025847) installed cleanly + ran. P2 follow-up "uv pip compile pre-flight"
  remains DEFERRED (NICE-TO-HAVE).
source:
  [
    "VM serial console: features-onchain-defi-20260516-221350 (deleted 22:18 UTC)",
    Triggered by B-015 chain step (c) features-onchain DeFi backfill,
  ]
severity:
  P1 — blocks every features-{family}-{asset_group} backfill VM that drags risk-and-exposure-service into the install
  set
locked_by: live-defi-rollout
---

## What I found

Launched `features-onchain-defi-20260516-221350` via the consolidated
`launch-features-vm.sh --feature-family onchain --asset-group DEFI --start-date 2026-04-15 --end-date 2026-04-19 --mode batch --launch-mode full`.

VM downloaded all 27 tarballs successfully (freshly rebuilt 2026-05-16 21:14 UTC including features-service @ Option A
fix), then the startup script's editable install step **failed**:

```
uv pip install --no-sources -e /home/ikennaigboaka/workspace/uac
 -e /home/ikennaigboaka/workspace/utl ... -e /home/ikennaigboaka/workspace/risk
 ... -e /home/ikennaigboaka/workspace/features ...

  unified-api-contracts>=0.2.38,<1.0.0, we can conclude that
  risk-and-exposure-service==0.1.0 cannot be used.
  And because only risk-and-exposure-service==0.1.0 is available and
  you require risk-and-exposure-service, we can conclude that your
  requirements are unsatisfiable.

Script "startup-script-url" failed with error: exit status 1
```

The startup script `setup-data-pipeline-vm.sh` installs the **entire DEFI repo set** (27 packages) into a single venv —
including `risk-and-exposure-service` which is pinned to UAC `<some-old-range>`, while at least one of the other 26
packages pins UAC `>=0.2.38,<1.0.0`. The two pins are unsatisfiable together.

## Why it matters

- Blocks every DEFI features backfill VM (B-015 chain step c on critical path for the May-23 cutover).
- Not specific to my repro — the freshly-rebuilt tarballs are the canonical current LDR snapshot, so any DEFI VM
  launched today via the consolidated launcher will hit the same conflict.
- Side-finding (same launcher): the LEGACY wrappers (`launch-features-onchain-backfill-vm.sh` +
  `launch-features-backfill-vm.sh`) silently invoke `python -m features_onchain_service` against the **stale**
  `features-onchain-service-code.tar.gz` (2026-05-08, no Option A) — confirmed via prior VM
  `features-onchain-defi-backfill-20260516-220052` PREFLIGHT_SKIPPED rc=1. The legacy wrappers should redirect to the
  consolidated launcher per `features_repo_consolidation_2026_05_08.md` Phase 8A, but they instead delegate to the
  legacy code path against a stale tarball — masking the upstream UAC version pin issue until somebody (slot-3 here)
  uses the new launcher.

## Diagnosis

1. **Confirm the offending pin**: `grep -rn "unified-api-contracts" risk-and-exposure-service/pyproject.toml` plus every
   other repo in `DEFI_REPOS` (deployment-service/scripts/vm/create-code-tarballs.sh L61). At least one pin disagrees
   with the consensus `>=0.2.38,<1.0.0`.
2. **Likely root**: `risk-and-exposure-service` Phase 2.6 region-SSOT alignment or pyproject bump may be lagging UAC.
   Maybe the repo's pyproject still pins UAC by exact `==0.2.37` or `~=0.2.30`.
3. **Verify**: `cd risk-and-exposure-service && git log --oneline pyproject.toml | head -3` then read it for the pin.

## Recommended decision

**Phase 1 (immediate)**: Bring `risk-and-exposure-service` UAC pin into alignment with the consensus `>=0.2.38,<1.0.0`
range. Trivial pyproject.toml edit + push to LDR + rebuild risk-and-exposure-service-code.tar.gz + re-launch.

**Phase 2 (cross-cutting)**: Add a pre-flight check to `create-code-tarballs.sh` that runs `uv pip compile` against the
DEFI/CEFI/etc. repo sets and fails the build if the pins are unsatisfiable. Stops the next class of "VM dies at startup"
bug.

**Phase 3 (legacy launcher hygiene)**: Make `launch-features-{onchain,}-backfill-vm.sh` either (a) fully redirect to the
consolidated launcher, or (b) print a hard-fail with the migration command. Silent mis-routing to the legacy module +
stale tarball IS the cause of my first failed VM today.

## Action items

- [x] [SCRIPT] P0. Bring risk-and-exposure-service UAC pin into alignment with workspace consensus + rebuild tarball. ✅
      **DONE 2026-05-16 (slot-3)** — `risk-and-exposure-service@83b10e0` relaxed pin `>=0.2.38` → `>=0.1.0,<1.0.0`;
      tarball rebuilt 21:22 UTC; verified pin fix is present in tarball contents.
- [x] [SCRIPT] P0. VM 3 (`features-onchain-defi-20260516-222259`) failure root-caused + fixed ✅ **DONE 2026-05-16 23:30
      UTC (slot-1-main)** — `ml-training-service==0.1.0` pinned `unified-trading-library>=0.4.0,<1.0.0` but UTL is at
      0.3.167 (peer repos all use `>=0.1.0` or `>=0.3.0`). VM did NOT auto-delete — it sat IDLE for ~55 min because
      startup script exited rc=1 BEFORE STARTED was emitted; the no-fire-and-forget watchdog only catches VMs that emit
      STARTED then go silent, so VMs failing before STARTED slip through. Manual delete by slot-1-main at 23:07 UTC. Fix
      shipped `ml-training-service@876f0e5` (pin → `>=0.3.0,<1.0.0`); tarball rebuilt 22:29:57 UTC. Filed
      `plans/active/issues/aave_lending_rate_val_vm_no_shutdown_2026_05_16.md` for the watchdog hardening.
- [x] [SCRIPT] P0. VM 4 (`features-onchain-defi-20260516-233044`) failure root-caused + fixed ✅ **DONE 2026-05-16 23:52
      UTC (slot-1-main)** — pre-existing `betfairlightweight>=2.20` ↔ `requests<2.33.0` vs `execution-service` requires
      `>=2.33.0` flat-install conflict. Existing NODEPS opt-out only covered
      `synthetic-benchmark`/`strategy-paper`/`strategy-live` VM_TASKs. Fix shipped `deployment-service@9d37deb`: added
      `features-backfill` to the NODEPS allowlist; setup script re-uploaded 22:52:08 UTC. VM 5 launched as
      `features-onchain-defi-20260516-235216`. Cross-ref:
      `execution_service_betfairlightweight_requests_dep_conflict_2026_05_16.md`.
- [x] ✅ **[DESIGN] P1. Pre-flight dep-pin scan added to `create-code-tarballs.sh`.** slot-1-main 2026-05-17 04:55 UTC
      at `deployment-service@e4e37bb`. Scans CORE_REPOS + MERGED_EXTRA_REPOS pyproject.toml for too-high UAC (>0.1.x) /
      UTL (>0.3.x) pins; surfaces as WARN at tarball-build time so conflicts are caught in seconds instead of failing a
      VM after ~30 min uv-pip-install timeout. Lighter than full `uv pip compile` (which would need a venv + 30+ s) but
      covers the 100% mis-floor class. Skip via SKIP_PREFLIGHT=true for CI builds. **2026-05-17 11:50 UTC update —
      superseded by workspace-wide audit**: swapped inline regex check for
      `unified-trading-pm/scripts/quality_gates/check_workspace_pyproject_pin_drift.py` (shipped at PM@3eb05d9b).
      Refactor at `deployment-service@bef235e` — dynamic tomllib name→version peer scan across ALL workspace repos (not
      just UAC/UTL), catches mis-floor against any peer pkg. Same soft-WARN semantics preserved.
- [x] ✅ **[SCRIPT] P1. Both deprecated wrappers now hard-redirect to consolidated launcher.**
      `launch-features-onchain-backfill-vm.sh` already redirected (pre-existing). `launch-features-backfill-vm.sh`
      hard-redirect shipped at `deployment-service@760d59b` (slot-1-main 2026-05-17 04:35 UTC). Mapping translates
      legacy positional dashes → consolidated `--feature-family` underscores; calendar family special-cases to
      `--asset-group GLOBAL`. Legacy per-family gcloud-create code path left in place only as hard-fail safety net for
      partial-args callers.

## Cross-references

- B-015 chain: `plans/active/issues/defi_features_pipeline_not_run_2026_05_14.md` § "Status (2026-05-16 23:00 UTC
  update)".
- Consolidated launcher landing: `plans/active/features_repo_consolidation_2026_05_08.md` Phase 8A.
- VM tarball SSOT: `/codex/05-infrastructure/vm-tarball-deployment.md`.

execution: owner: slot-2 (features-service / risk-and-exposure-service owners) cadence: one-shot verifier: relaunch
features-onchain-defi VM via consolidated launcher → uv install succeeds → events flow last_executed: NEVER

---

## Triage — 2026-05-18

**Status**: CLOSED — SHIPPED **Triaged by**: slot-8 triage sweep **Reason**: Resolved 2026-05-17; 3 dep-pin fixes +
pre-flight scan added
