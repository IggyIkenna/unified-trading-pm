---
title:
  "features-onchain-defi VM uv-pip-install hits unsatisfiable resolution — risk-and-exposure-service==0.1.0 vs
  unified-api-contracts>=0.2.38"
created: 2026-05-16
author: ikenna-slot-3
source:
  - "VM serial console: features-onchain-defi-20260516-221350 (deleted 22:18 UTC)"
  - "Triggered by B-015 chain step (c) features-onchain DeFi backfill"
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

- [ ] [SCRIPT] P0. Bring risk-and-exposure-service UAC pin into alignment with workspace consensus + rebuild tarball.
- [ ] [DESIGN] P1. Add `uv pip compile` pre-flight to `create-code-tarballs.sh` per-asset-group set.
- [ ] [SCRIPT] P1. Hard-redirect or hard-fail the deprecated `launch-features-{onchain,}-backfill-vm.sh` wrappers so
      they cannot silently use the legacy module + stale tarball.

## Cross-references

- B-015 chain: `plans/active/issues/defi_features_pipeline_not_run_2026_05_14.md` § "Status (2026-05-16 23:00 UTC
  update)".
- Consolidated launcher landing: `plans/active/features_repo_consolidation_2026_05_08.md` Phase 8A.
- VM tarball SSOT: `codex/05-infrastructure/vm-tarball-deployment.md`.

execution: owner: slot-2 (features-service / risk-and-exposure-service owners) cadence: one-shot verifier: relaunch
features-onchain-defi VM via consolidated launcher → uv install succeeds → events flow last_executed: NEVER
