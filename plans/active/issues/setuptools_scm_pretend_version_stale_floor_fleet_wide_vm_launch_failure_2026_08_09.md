---
doc_type: issue
title: >-
  Stale fleet-wide SETUPTOOLS_SCM_PRETEND_VERSION="0.99.0" broke every VM launch that installs
  unified-api-contracts + unified-trading-library + instruments-service together — fixed to 0.199.0
summary: >-
  Every `deployment-service` VM launcher (18 files) sets `SETUPTOOLS_SCM_PRETEND_VERSION="0.99.0"` on
  the VM so hatch-vcs-based internal packages (uac/utl/service packages, which ship without `.git`
  history in the code tarball) resolve to a static version instead of failing `setuptools_scm.get_version()`.
  The chosen constant was documented as needing to stay `<1.0.0` and `>=` the highest cross-package
  floor pin. Today (2026-08-09) `instruments-service@b3e5f69c` and `unified-trading-library@6319d308`
  re-pinned their own `unified-api-contracts` floor to `>=0.106.0,<1.0.0` (a major/breaking bump) —
  higher than the static `0.99.0`, so EVERY VM launch installing uac+utl+instruments together started
  failing `uv pip install` with "unified-api-contracts>=0.106.0 ... unified-trading-library==0.99.0
  cannot be used ... your requirements are unsatisfiable", captured as a bare `SETUP_EXIT_STATUS=1`
  with the real uv error text never reaching the GCS-uploaded `vm-setup.log` (only visible via the
  VM's live serial console before self-delete). Found while launching chunk 3/7 of the sports
  historical expected_unattempted backfill (3 consecutive real VM failures, confirmed reproducible,
  ruled out as a genuine dependency-graph conflict via a clean local `uv pip install` against the
  same tarball SHAs — resolves fine with a real git-tag-derived version). Fixed by bumping the
  constant to `0.199.0` across all 18 launcher files (mechanical, identical change, comfortably above
  the new 0.106.0 floor, still `<1.0.0`).
status: resolved
nature: issue
asset_group: [infra]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [vm-launcher, setuptools-scm, hatch-vcs, dependency-pin, fleet-wide, cross-repo, backfill]
related:
  [
    /plans/active/issues/sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md,
  ]
created: 2026-08-09
author: ikennaigboaka [slot-14]
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: data_engineering
resolved_by: deployment-service@<pending-sha>
locked_by:
locked_since:
source: >-
  Discovered live while diagnosing 3 consecutive SETUP_EXIT_STATUS=1 failures launching sports
  expected_unattempted backfill chunk 3/7 (2026-08-09, slot 14).
drift_direction: advance-code
depends_on: []
---

# Stale fleet-wide SETUPTOOLS_SCM_PRETEND_VERSION broke every uac+utl+instruments-service VM launch

## What I found

`deployment-service/scripts/vm/setup-data-pipeline-vm.sh` (and 17 sibling launcher files that
duplicate the same env var — see list below) sets:

```bash
export SETUPTOOLS_SCM_PRETEND_VERSION="0.99.0"
```

The code tarball shipped to a VM explicitly excludes `.git` (`create-code-tarballs.sh`'s
`tar czf ... --exclude='.git' ...`), so hatch-vcs on the VM cannot derive a real version from git
tags — `SETUPTOOLS_SCM_PRETEND_VERSION` gives every hatch-vcs-based internal package (uac, utl, and
the service packages) a fixed fake version instead of a hard failure. The value was chosen to satisfy
"`<1.0.0` and `>=` the highest lower-bound in any cross-package constraint" (the script's own comment,
citing `unified-trading-library>=0.13.0` as the example floor at the time).

Today, `instruments-service@b3e5f69c1993bdd56d2b8f4688b2fd9b1d14da52` ("chore(deps): re-pin
unified-api-contracts to 0.106.0 (major/breaking floor)") and the matching
`unified-trading-library@6319d308ec739c95a79e6a94be7a343158439447` both bumped their own
`unified-api-contracts` floor to `>=0.106.0,<1.0.0`. `0.99.0 < 0.106.0` in semver terms (comparing
minor `99` vs `106`), so the static pretend-version stopped satisfying its own invariant — every VM
that installs `uac` alongside anything requiring `unified-api-contracts>=0.106.0` now fails
`uv pip install` with an unsatisfiable-resolution error.

**Confirmed via live VM serial console** (the actual uv error never reaches the GCS `vm-setup.log` —
that log only captures explicit `log "..."` calls, and the `uv pip install ... | tail -5` line at
`setup-data-pipeline-vm.sh:1005` prints straight to the VM's own console/journal instead):

```
Because unified-api-contracts>=0.106.0,<1.0.0, we can conclude that
unified-trading-library==0.99.0 cannot be used.
And because only unified-trading-library==0.99.0 is available and you
require unified-trading-library, we can conclude that your requirements
are unsatisfiable.
```

3 consecutive real VM failures on the same chunk/window
(`expected-universe-v2-sports-20260809-133328`, `-133743`, `-134428`), same tarball SHAs each time —
ruled out as a genuine dependency-graph regression by reproducing the exact same
`uv pip install --no-sources -e uac -e utl -e instruments` locally against the same tarball SHAs with
a real git-tag-derived version (`unified-trading-library==0.76.4.dev618+g262a85310a7a`): resolves and
installs 204 packages cleanly. The failure is specific to the VM's git-less tarball + the stale
pretend-version, not the actual pyproject.toml pin graph.

## Why it matters

This breaks **every VM launch, fleet-wide**, that installs `unified-api-contracts` alongside anything
now requiring `>=0.106.0` — not just the sports backfill that surfaced it. 18 launcher files carry the
identical stale constant:

`launch-features-backfill-vm-aws.sh`, `vm_instruments_backfill.sh`, `setup-data-pipeline-vm.sh`,
`launch-ec2-vm.sh`, `setup-prediction-live-consolidated-vm.sh`, `launch-mtds-backfill-vm-aws.sh`,
`launch-defi-backfill-vm-aws.sh`, `vm_instruments_reference.sh`, `launch-mdps-backfill-vm-aws.sh`,
`launch-prediction-pipeline-vm.sh`, `launch-aave-lending-rate-validation-vm.sh`,
`setup-cefi-live-consolidated-vm.sh`, `setup-data-pipeline-vm-aws.sh`,
`launch-amm-golden-fixture-validation-vm.sh`, `launch-instruments-backfill-vm-aws.sh`,
`launch-cefi-sharded-backfill-aws.sh`, `launch-vm-zombie-watchdog.sh`, `vm_mtds_backfill.sh` (all
under `deployment-service/scripts/vm/`).

Every failure surfaces only as a bare `SETUP_EXIT_STATUS=1` with no error text in the GCS-uploaded
log — a second, smaller gap worth a follow-up (below).

## Recommended decision

Fixed directly (small, mechanical, identical change across all 18 files — within the
outside-plan-small-and-clear ≤30min triage bar): bumped the constant from `"0.99.0"` to `"0.199.0"`
in every file (verified via `grep -c` that each had exactly 1 occurrence before and after; `bash -n`
syntax-checked all 18 post-edit). `0.199.0` clears the new `0.106.0` floor with headroom for future
bumps, stays `<1.0.0`.

## Still open

- [ ] [SCRIPT] P2. `setup-data-pipeline-vm.sh`'s `uv pip install ... | tail -5` (and the 3 other
      un-logged `uv pip install` call sites in the same file, lines ~1005/1008/1021/1483) should also
      pipe through the `log()` wrapper (or `2>&1 | tee -a "$LOG" | tail -5`) so a REAL uv resolution
      failure's actual error text reaches the GCS-uploaded `vm-setup.log` instead of only being
      visible via a live `gcloud compute instances get-serial-port-output` race against the VM's
      ~10s self-delete-on-failure window. This bug class (bare `SETUP_EXIT_STATUS=1`/`rc=1` with zero
      diagnostic text) will recur on the next genuine pin/version issue without this fix. (repo:
      deployment-service)
- [ ] [SCRIPT] P3. Consider replacing the hand-maintained per-file constant with a single sourced
      value (e.g. a `lib/pretend-version.sh` all 18 launchers `source`) so the next floor bump is a
      one-line change instead of an 18-file mechanical sweep. Out of scope for this fix (kept the
      diff minimal/mechanical to unblock the live-blocked backfill fast). (repo: deployment-service)

## Progress Log

- **2026-08-09 (slot 14, data_engineering)**: Root-caused + fixed while blocked on sports backfill
  chunk 3/7 launch (3 consecutive real `SETUP_EXIT_STATUS=1` failures). Diagnosed via live VM serial
  console capture (the GCS log doesn't carry the real uv error) + a clean local repro that ruled out
  a genuine pin conflict. Bumped `SETUPTOOLS_SCM_PRETEND_VERSION` `0.99.0` -> `0.199.0` across all 18
  launcher files + updated the two explanatory comments in `setup-data-pipeline-vm.sh`. Filed the 2
  follow-ups above rather than absorbing them into this fix (different shape: logging visibility +
  a refactor, not part of unblocking the live backfill). Resuming the sports chunk 3 launch now that
  this is shipped.
