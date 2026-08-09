---
doc_type: issue
title:
  "SETUPTOOLS_SCM_PRETEND_VERSION=0.99.0 (VM tarball bootstrap) is now BELOW unified-api-contracts' own >=0.106.0 floor
  — breaks `uv pip install` on EVERY VM launch that installs uac + any repo requiring it"
summary:
  "deployment-service/scripts/vm/setup-data-pipeline-vm.sh sets SETUPTOOLS_SCM_PRETEND_VERSION=0.99.0 before the
  tarball-based editable-install pass (tarballs have no .git history, so hatch-vcs/setuptools_scm can't derive a real
  version — this pretend-version is the documented workaround, per the script's own comment: 'Must be <1.0.0 and >= the
  highest lower-bound in any cross-package constraint'). That invariant is now VIOLATED: `market-tick-data-service`
  commit 8baed21f ('chore(deps): re-pin unified-api-contracts to 0.106.0 (major/breaking floor)') raised MTDS's
  `unified-api-contracts` floor from >=0.98.0 to >=0.106.0 — and `market-data-processing-service`,
  `unified-trading-library`, and `deployment-service` ALL independently already declare
  `unified-api-contracts>=0.106.0,<1.0.0` too (grepped live). Since 0.99.0 < 0.106.0 (confirmed via
  `packaging.version.Version` comparison), uac's pretend-version no longer satisfies ANY of these repos' floor, so `uv
  pip install --no-sources -e uac -e utl -e mdps -e mtds` (the exact install line `setup-data-pipeline-vm.sh` runs)
  fails immediately with an unsatisfiable-constraint resolution error on every VM boot that installs this combination —
  confirmed live TWICE this session (`mdps-backfill-cefi-20260809-140132`, `mdps-backfill-cefi-20260809-140809`, both
  `SETUP FAILED rc=1` ~1s into the pip install step). Reproduced the ROOT CAUSE locally: the identical editable-install
  command against the SAME exact commit SHAs succeeds cleanly on a normal git checkout (real version resolution works),
  but fails specifically under the tarball/pretend-version scheme once the constraint floor crosses 0.99.0 — this is a
  real, currently-live, deterministic breakage, not a transient/environmental flake."
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, market-tick-data-service, market-data-processing-service, unified-trading-library]
scope: [engineer, admin]
tags: [infra, vm-launcher, tarball, setuptools-scm, uac, dependency-floor, fleet-wide, big-finding]
related:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch5_2026_08_09.md,
  ]
created: 2026-08-09
last_updated: 2026-08-09
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  slot 22, cross_cutting_satellite_ao_dispatch_batch5-77d480c19d08, discovered while backfilling MDPS candles,
  2026-08-09
---

# VM tarball bootstrap's pretend-version (0.99.0) is now below uac's real dependency floor (>=0.106.0)

## What I found

`deployment-service/scripts/vm/setup-data-pipeline-vm.sh:940`:

```bash
export SETUPTOOLS_SCM_PRETEND_VERSION="0.99.0"
```

With the comment's own documented invariant: "Must be <1.0.0 and >= the highest lower-bound in any cross-package
constraint (e.g. features-service requires unified-trading-library>=0.13.0,<1.0.0 — 0.99.0 satisfies both bounds; 0.0.0
would fail the >=0.13.0 floor)."

That invariant broke: `market-tick-data-service@8baed21f` ("re-pin unified-api-contracts to 0.106.0 (major/breaking
floor)") raised MTDS's own `unified-api-contracts` requirement to `>=0.106.0,<1.0.0`. Live grep confirms
`market-data-processing-service`, `unified-trading-library`, and `deployment-service` ALL already independently require
`unified-api-contracts>=0.106.0,<1.0.0` too — so this isn't an MTDS-only problem, it's the CURRENT floor across the
whole tarball-installed set. `0.99.0 < 0.106.0` (verified:
`packaging.version.Version("0.99.0") < packaging.version.Version("0.106.0")` → `True`).

**Live evidence (2026-08-09):** two consecutive VM launches (`mdps-backfill-cefi-20260809-140132`,
`mdps-backfill-cefi-20260809-140809`) both failed at the identical step:

```
Installing Python dependencies...
  uv pip install --no-sources -e /home/ikennaigboaka/workspace/uac -e /home/ikennaigboaka/workspace/utl \
    -e /home/ikennaigboaka/workspace/mdps -e /home/ikennaigboaka/workspace/mtds
SETUP FAILED rc=1 — uploading log + EXIT_STATUS, scheduling self-delete
```

**Root-caused, not just observed:** reproduced the exact same `uv pip install --no-sources -e ... -e ... -e ... -e ...`
command against IDENTICAL commit SHAs on a real git checkout (normal version resolution, no pretend-version) — it
succeeds cleanly (exit 0, all ~180 packages resolved). The failure is specific to the tarball/pretend-version path.

## Why it matters

This breaks `uv pip install` on **every VM launch** that installs `unified-api-contracts` alongside any repo declaring
the new `>=0.106.0` floor — which per the live grep above is already MDPS, MTDS, UTL, and deployment-service
simultaneously. Any backfill/reprocess/pipeline-check VM using `setup-data-pipeline-vm.sh` (the shared Pattern-A startup
script referenced by `startup-script-url=` across essentially every launcher in `deployment-service/scripts/vm/`) is
affected right now, not just the MDPS backfill launcher this was discovered through. This is a
foundation-completion-gate-class blocker — every VM-based backfill across the fleet should be assumed broken until this
is fixed and verified.

## Recommended fix

Bump `SETUPTOOLS_SCM_PRETEND_VERSION` past the new real floor while staying `<1.0.0` (e.g. `"0.199.0"` — the script's
own comment already documents the exact invariant to preserve:
`>= the highest lower-bound in any cross-package constraint`, `<1.0.0`). This is a single-line change in a SHARED,
high-blast-radius bootstrap script (`deployment-service/scripts/vm/setup-data-pipeline-vm.sh`) that every VM launcher's
`startup-script-url` points at — flagging for operator awareness given the blast radius, even though the fix itself is
small. After the fix: verify live with an actual VM launch (not just a local repro) before considering this closed,
since the failure mode is specific to the tarball/no-git-history path a local checkout can't exercise.

## Todo

- [ ] [INFRA] P0. **Bump `SETUPTOOLS_SCM_PRETEND_VERSION` in `setup-data-pipeline-vm.sh` past the current real
      `unified-api-contracts` floor** (currently >=0.106.0 across MDPS/MTDS/UTL/deployment-service — check for any
      HIGHER floor elsewhere in the fleet before picking the new pretend value) **and add a standing check/comment
      reminder so this doesn't silently regress again as floors keep rising** (e.g. a QG script that greps every repo's
      `pyproject.toml` for its highest `unified-api-contracts>=X` floor and asserts the pretend-version is still above
      it). Repo: deployment-service.
- [ ] [INFRA] P0. **After the fix, launch a real verification VM** (mirrors this issue's own repro:
      `market-tick-data-service` + `market-data-processing-service` + `unified-api-contracts` +
      `unified-trading-library`) and confirm `uv pip install` succeeds and the VM reaches real processing, not just that
      setup completes. Repo: deployment-service.
