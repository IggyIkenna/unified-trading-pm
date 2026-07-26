---
doc_type: issue
title:
  launch-mdps-features-live.sh installs 3 archived/consolidated repos via an unresolved compound VM_SERVICE key — fix
  committed to origin/main, but the published GCS setup script keeps getting overwritten with the old version faster
  than it can be verified live
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
last_updated: 2026-07-27
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

## Update 3 — fix IS committed to origin/main; live-VM confirmation still blocked by a fast, repeating clobber

Ran the full ship sequence properly: `git pull --ff-only` (clean, no conflicts with an unrelated concurrent commit to
the same file), `quality-gates.sh --no-fix` (all gates passed),
`quickmerge.sh --agent --files 'scripts/vm/create- code-tarballs.sh scripts/vm/setup-data-pipeline-vm.sh'` — landed on
`live-defi-rollout` as commit `0f0e0a7`. Stashed one unrelated dirty file (a separate features-service deploy-script fix
from earlier in this session, not part of this fix) to get a clean tree, republished via
`create-code-tarballs.sh --asset-group cefi` (no `--allow-dirty- tarball` needed this time — sourced from the committed
tree), confirmed via `gsutil stat`/`cat` immediately after that the fix was live, then restored the stashed file.

Re-launched `launch-mdps-features-live.sh --asset-group cefi` (3rd attempt) — **identical pre-fix failure again** ("Code
deployed from GCS (28 repos)", same `position-balance-monitor-service==0.1.1` unsatisfiable error). Checked the live GCS
object immediately after: it no longer had the fix (`NEEDED_TARBALLS=`/`MTDS_DEPENDENT_SERVICES=` back at their pre-fix
positions), despite `gsutil stat`'s reported update-time matching my own publish almost exactly — meaning whatever is
overwriting this file ran again within roughly the same window as my publish, not 4 minutes later this time but
effectively immediately. Checked GCS Data Access audit logs for the object's write history — empty (Data Access logging
isn't enabled on this bucket, so there's no audit trail to name the actual writer). Searched this and other repos'
`.github/workflows/` for anything invoking `create-code-tarballs.sh` — found nothing, so it isn't
GitHub-Actions-triggered as far as this session could find.

**Given this is now the second clobber and it's landing faster than a manual publish→verify cycle can outrun, I stopped
rather than keep burning real VM billing (3 real e2-standard-8 launches so far) on repeated blind retries.** The fix's
correctness is not in question — it's independently confirmed via (a) the isolated functional test in Update 1 and (b)
`git show 0f0e0a7:scripts/vm/setup-data-pipeline-vm.sh` showing the correct committed content. What's unconfirmed is a
live end-to-end VM boot, purely because something keeps racing any manual publish attempt back to the pre-fix state.
This needs either: identifying and pausing/coordinating with whatever is doing this before the next verification
attempt, or enabling Data Access audit logging on `gs://deployment-scripts-central-element-323112` long enough to catch
the actual writer, or simply accepting eventual consistency — the fix IS on `origin/main` now, so the NEXT time anything
rebuilds tarballs from a fresh, current checkout (this session's clobber-source included, once it's running off a
checkout that has commit `0f0e0a7` or later), it should self-resolve without further action.

## Todos

- [x] [INFRA] P1. ~~Commit + ship (quickmerge) the two fixes~~ — **DONE**: `deployment-service@0f0e0a7`,
      `quality-gates.sh` green, landed on `live-defi-rollout`.
- [ ] [SCRIPT] P2. Get a genuine live-VM confirmation of the fix (3 attempts so far all hit either the pre-fix bug or a
      clobbered publish — see Update 3). Retry once whatever is overwriting
      `gs://deployment-scripts-central-     element-323112/vm/setup-data-pipeline-vm.sh` is identified/quiesced, or once
      enough time has passed that routine tarball-refresh activity would naturally be sourcing the now-committed
      `0f0e0a7`+ state. Done when: `run.log` for a fresh `mdps-features-live-cefi-*` VM shows a clean boot + heartbeat
      within a few minutes, then delete the VM.
- [ ] [INFRA] P2. `launch-mdps-features-live.sh` (and likely its MTDS/execution siblings sharing this
      tarball-then-install pattern) should propagate a non-zero `uv pip install` exit into a loud failure signal (an
      `attempted_failed`-style manifest row, an alert, or at minimum an early VM self-terminate) instead of leaving the
      VM running indefinitely with no process and no log — this general gap is independent of the two specific bugs
      above and would have caught either one in minutes instead of 2.5h / requiring a live re-check.
- [ ] [OPERATOR] P2. Identify what is repeatedly re-publishing
      `gs://deployment-scripts-central-element-323112/vm/     setup-data-pipeline-vm.sh` with old content — happened
      twice in this session (once ~4min after a publish, once within roughly the same minute), too fast to catch via
      `.github/workflows` grep or GCS audit logs (Data Access logging not enabled on this bucket). Needs either enabling
      Data Access logging on this bucket temporarily to catch the actual writer, or checking for a cron/systemd-timer
      job on some always-on VM/box that runs `create-code-tarballs.sh --all` or similar on a short interval.
