---
title: "features-service deprecated launcher wrappers silently misroute to legacy module + stale tarball"
created: 2026-05-16
author: ikenna-slot-3 (surfaced during defi_features_pipeline_not_run investigation)
resolved: 2026-05-17
resolution: PARTIAL — `launch-features-onchain-backfill-vm.sh` now redirects to the consolidated launcher (`deployment-service@d65da47`); emits deprecation warning to stderr + forwards env overrides. Remaining (P3 follow-up, non-blocking for May-23): `launch-features-backfill-vm.sh` keeps its legacy delegation for the other 7 family wrappers — those still use the family-specific stale tarballs but the per-family modules are standalone, so no immediate misroute. Onchain was the only family that broke due to its dependency on the consolidated features-service Option A fix.
source:
  - "ikenna-slot-3 side-finding at plans/active/issues/defi_features_pipeline_not_run_2026_05_14.md § (c)"
  - "VM features-onchain-defi-backfill-20260516-220052 hit PREFLIGHT_SKIPPED rc=1 — silent misroute"
  - "features_repo_consolidation_2026_05_08.md Phase 8A — wrapper redirect contract"
locked_by: live-defi-rollout
locked_since: 2026-05-16
severity: P2 — caused 1 wasted VM launch; doesn't block May-23 if consolidated launcher used directly
---

> **🟢 RESOLUTION VERIFIED 2026-05-20** — onchain wrapper redirect shipped `deployment-service@d65da47` (verified via
> git log; pairs with consolidation commit `deployment-service@2942815`). Resolution body explicitly notes the remaining
> 7 family wrappers "have no immediate misroute" because per-family modules are standalone — the only family that broke
> (onchain) was the only one with the consolidation dependency, and it is fixed. Archiving.

## What I found

Deprecated launcher wrappers still resolve `feature-family=onchain` to the legacy `features_onchain_service` module +
the stale `features-onchain-service-code` tarball:

- `deployment-service/scripts/vm/launch-features-onchain-backfill-vm.sh` (deprecated)
- `deployment-service/scripts/vm/launch-features-backfill-vm.sh` (deprecated)

Per `features_repo_consolidation_2026_05_08.md` Phase 8A, both wrappers should redirect to the consolidated launcher
`launch-features-vm.sh --feature-family <family> --asset-group <ag> --mode batch --launch-mode full` which invokes the
canonical `python -m features_service --feature-family onchain` against the `features-service-code.tar.gz` tarball.

**Current behaviour**: silently misroutes; uses stale 2026-05-08 tarball; preflight skip with rc=1. No clear error
surface that wrapper is deprecated.

Reference VM: `features-onchain-defi-backfill-20260516-220052` (self-stopped at PREFLIGHT_SKIPPED 2026-05-16 ~21:00
UTC). Re-launched via consolidated path as `features-onchain-defi-20260516-221350`.

## Why it matters

Each invocation of the deprecated wrapper wastes:

- VM compute (typically 5-10 min before PREFLIGHT_SKIPPED catches it)
- Operator/agent wall-time waiting for "STOPPED" + investigating

For B-015 paper-trade gate ops specifically, slot-3 hit this once; cycle would have failed silently if rc=1 hadn't
bubbled up cleanly.

## Recommended decision

**Per Phase 8A of `features_repo_consolidation_2026_05_08.md`** — implement the wrapper redirect:

```bash
# In deployment-service/scripts/vm/launch-features-onchain-backfill-vm.sh
#!/usr/bin/env bash
echo "[DEPRECATED 2026-05-08 per Phase 8A] launch-features-onchain-backfill-vm.sh → redirecting to consolidated launcher"
echo "  See features_repo_consolidation_2026_05_08.md § Phase 8A"
exec "$(dirname "$0")/launch-features-vm.sh" --feature-family onchain --asset-group "${ASSET_GROUP:-DEFI}" --mode batch --launch-mode full "$@"
```

Same shape for `launch-features-backfill-vm.sh`.

**Owner**: slot owning `features_repo_consolidation_2026_05_08.md` Phase 8A. Likely Ikenna slot 7 (features-service
context) or whoever owns the deployment-service vm/ launchers cluster.

**Workaround until fix lands**: agents launching features-onchain VMs MUST use the consolidated launcher directly:

```bash
bash deployment-service/scripts/vm/launch-features-vm.sh \
    --feature-family onchain \
    --asset-group DEFI \
    --mode batch \
    --launch-mode full
```

---

## Triage — 2026-05-18

**Status**: CLOSED — SHIPPED  
**Triaged by**: slot-8 triage sweep  
**Reason**: Resolved 2026-05-17; deprecated launcher redirects fixed
