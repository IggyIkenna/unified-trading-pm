---
doc_type: issue
title:
  launch-mdps-features-live.sh installs 3 archived/consolidated repos via an unresolved compound VM_SERVICE key — fix
  written, NOT yet durable (clobbered once already)
summary: >-
  `launch-mdps-features-live.sh` sets `VM_SERVICE=market_data_processing_service+features_service` (a "+"-joined
  compound key), but `setup-data-pipeline-vm.sh`'s `SERVICE_TARBALLS` lookup only has single-service keys — the lookup
  always misses, silently falling to "unknown service → install every known tarball" (23+ repos incl. 3 that no longer
  exist: `pnl-attribution-service` / `risk-and-exposure-service` / `position-balance-monitor-service`, subtree-merged
  into `strategy-service` 2026-05-20, `deprecation-ledger.yaml` `known_import_count: 0`, archived on GitHub). Their
  tarballs are frozen from before the merge and no longer resolve against current UTL/UAC pins, so the combined `uv pip
  install -e <28 dirs>` fails with `position-balance-monitor-service==0.1.1` reporting an unsatisfiable conflict — exit
  status 1, no failure propagation, VM keeps billing indefinitely with no process and no log (silent stall, not a loud
  failure). **A fix for both layers is written and locally verified** (functional test: compound key now resolves to
  exactly the 6 tarballs MDPS+features actually need, `mtds-code` transitive dep correctly included,
  `strategy-paper`/`defi-paper`'s separate pbm/pnl/risk install branch left untouched since it's unverified whether
  `e2e-testing/colocated_engine.py` still imports those modules directly) — but is **NOT yet live**: publishing it via
  `create-code-tarballs.sh --allow-dirty-tarball` got silently overwritten by an unrelated concurrent tarball-refresh
  (`origin/main` has neither fix, since neither change is committed) within ~4 minutes, and a second verification VM hit
  the identical pre-fix failure. The fix must be committed to `origin/main` before any tarball-refresh (automated or
  another agent's) can durably pick it up — local uncommitted edits lose every race against a refresh sourced from the
  committed tree.
status: open
nature: issue
asset_group: [cefi, cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags:
  [
    mdps,
    features-service,
    vm-launcher,
    dependency-conflict,
    deprecated-repo-reference,
    live-launch,
    silent-failure,
    billing-waste,
    uncommitted-fix-clobbered,
  ]
related:
  [
    /plans/active/issues/cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md,
    /plans/active/cefi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /codex/04-architecture/deprecation-ledger.yaml,
  ]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: interactive session, operator-directed reader-bridge deploy verification, 2026-07-26
resolved_by:
---

# launch-mdps-features-live.sh compound-VM_SERVICE / archived-repo bug

## What I found (corrected — see Update below for the real root cause)

Launched `mdps-features-live-cefi-20260726-202458` as a brief verification that the MDPS+features live pipeline boots
correctly. The VM sat `RUNNING` for ~2.5h with zero progress signals (no `run.log` ever appeared; no `[vm-exec]` lines
on the serial console). SSH'd in and read `journalctl -u google-startup-scripts.service`: the startup script deploys all
28 monorepo repos' code tarballs ("Code deployed from GCS (28 repos)"), then runs ONE combined
`uv pip install --no-sources -e <28 dirs>`, which fails:

```
we can conclude that position-balance-monitor-service==0.1.1 cannot be used.
And because only position-balance-monitor-service==0.1.1 is available and you require
position-balance-monitor-service, we can conclude that your requirements are unsatisfiable.
Script "startup-script-url" failed with error: exit status 1
```

No error propagation past this point — `ps aux` confirmed no MDPS/features process ever started, and the VM
(e2-standard-8, on-demand) kept billing indefinitely with nothing running.

**Silent failure, not a loud one**: nothing about the VM's external signals (status=RUNNING, no crash, no
`attempted_failed` manifest row) distinguishes it from a slow-but-healthy boot — the exact "found asleep" stall class
the workspace's async-wait discipline warns about, except the launcher gives no loud signal to catch it on.

## Update (same session) — the real root cause is TWO bugs, not one bad pin

The operator asked "isn't position-balance-monitor-service folded into strategy-service now?" — correct, and it reframed
the whole diagnosis:

**Bug 1 — three archived repos still hardcoded as live.** `pnl-attribution-service` / `risk-and-exposure-service` /
`position-balance-monitor-service` were subtree-merged into `strategy-service` on 2026-05-20
(`codex/04-architecture/deprecation-ledger.yaml`: all three `known_import_count: 0`, "All workspace consumers re-pointed
to strategy_service/position/\*"). None of the three exist as checkouts in this workspace anymore. Yet
`create-code-tarballs.sh`'s `CEFI_REPOS`/`TRADFI_REPOS`/`DEFI_REPOS`/`SPORTS_REPOS`/`PREDICTION_REPOS`/
`ALL_SERVICE_REPOS` arrays all still hardcoded them — `strategy-service` (the actual replacement) was already present in
every one of those arrays alongside the 3 dead names. Their GCS tarballs are frozen artifacts from before the 2026-05-20
merge; installing one alongside current UTL/UAC pins is what produces the "unsatisfiable" conflict. **Fixed**: removed
all three from every array in `create-code-tarballs.sh` (comment added explaining why).

**Bug 2 (the actual trigger for THIS launcher) — an unresolved compound VM_SERVICE key.** `launch-mdps-features-live.sh`
sets `VM_SERVICE=market_data_processing_service+features_service` (a "+"-joined compound value), but
`setup-data-pipeline-vm.sh`'s `SERVICE_TARBALLS` associative array only has single-service keys. The lookup on the full
compound string always misses, so it falls to the `else` branch:
`log "WARNING: Unknown VM_SERVICE=... — installing all available tarballs"` — the exact same failure class this table's
own 2026-05-16 comment already documents for `features_service` alone, just triggered by a "+"-joined key this time.
This is why 28 repos got installed instead of the ~3 MDPS+features actually need, and why Bug 1's stale tarballs entered
the picture at all for this specific launcher. **Fixed**: added a compound-key-aware branch in
`setup-data-pipeline-vm.sh` that splits on "+" and resolves each component individually (falling back to a per-component
warning, not "install everything," for a genuinely unrecognized part). Also moved `MTDS_DEPENDENT_SERVICES`'s
declaration earlier in the script so the new branch can consult it — the existing single-service loop that adds
`mtds-code` as a transitive dependency only ever compared the _whole_ `$VM_SERVICE` string, so it would silently never
fire for a compound value (the exact "requirements are unsatisfiable" failure mode that already killed two MDPS backfill
VMs 2026-04-19, per that loop's own comment) without this fix.

**Verified via a standalone functional test** (extracted just the resolution logic, `set -euo pipefail`, 4 scenarios):
`market_data_processing_service+features_service` → exactly
`[uac, utl, deployment-service, market-data-processing- service-code, mtds-code, features-service-code]` (6 tarballs,
`mtds-code` correctly included); plain single-service `features_service` unchanged; genuinely-unknown-service fallback
unchanged; `strategy-paper` VM_TASK branch (which still explicitly installs the 3 "archived" tarballs for
`e2e-testing/colocated_engine.py` — left **untouched**, since it's unverified whether that file still imports those
modules directly despite the ledger's `known_import_count: 0` claim, and breaking a real live-trading VM class to be
tidy would be reckless) unchanged.

## Update 2 — the fix is NOT durable yet: got clobbered once already

Published via `create-code-tarballs.sh --asset-group cefi --allow-dirty-tarball` (deployment-service has uncommitted
changes — the fix itself). Confirmed the upload landed: `gsutil stat` showed a fresh object at `22:28:13Z`. Re-ran
`launch-mdps-features-live.sh --asset-group cefi` to verify live — **it hit the identical pre-fix failure** ("Code
deployed from GCS (28 repos)", same `position-balance-monitor-service==0.1.1` unsatisfiable error). Diffing the live GCS
object against the local fixed file (line counts, `MTDS_DEPENDENT_SERVICES=` position, grep for `compound`) proved the
live copy was back to the **original unfixed** script, re-uploaded at `22:32:35Z` — 4 minutes after mine, by something
else in this shared workspace (almost certainly an automated tarball-refresh job, or another agent, sourcing a clean
checkout of `origin/main`, which has neither fix since both are still local-only edits). **Any uncommitted fix loses
every race against a refresh sourced from the committed tree.** The fix must land on `origin/main` (via quickmerge, per
this repo's normal discipline) before it can be considered actually deployed — until then this issue stays open despite
the code being written and locally verified.

## Todos

- [ ] [INFRA] P1. Commit + ship (quickmerge) the two fixes in `deployment-service/scripts/vm/create-code-tarballs.sh`
      (remove `pnl-attribution-service`/`risk-and-exposure-service`/`position-balance-monitor-service` from the category
      arrays) and `setup-data-pipeline-vm.sh` (compound-VM_SERVICE-aware branch + `MTDS_DEPENDENT_SERVICES` moved
      earlier). Both are already written and locally verified (functional test in this doc's Update section); this todo
      is the commit + `create-code-tarballs.sh --asset-group cefi` republish, not new engineering.
- [ ] [SCRIPT] P2. After the fix is committed and republished, re-run
      `launch-mdps-features-live.sh --asset-group     cefi` once more to get a genuine live confirmation (both prior
      attempts hit the pre-fix bug — one before the fix existed, one because the fix got clobbered before the VM
      launched). Done when: `run.log` shows a clean boot + heartbeat within a few minutes, then delete the VM.
- [ ] [INFRA] P2. `launch-mdps-features-live.sh` (and likely its MTDS/execution siblings sharing this
      tarball-then-install pattern) should propagate a non-zero `uv pip install` exit into a loud failure signal (an
      `attempted_failed`-style manifest row, an alert, or at minimum an early VM self-terminate) instead of leaving the
      VM running indefinitely with no process and no log — this general gap is independent of the two specific bugs
      above and would have caught either one in minutes instead of 2.5h / requiring a live re-check.
- [ ] [INFRA] P3. Investigate what re-published the old `setup-data-pipeline-vm.sh` 4 minutes after this session's fix
      upload — if it's a recurring automated job, it should be identified (so future local testing knows to race against
      it or disable it temporarily) rather than left as an unexplained "something clobbered it."
