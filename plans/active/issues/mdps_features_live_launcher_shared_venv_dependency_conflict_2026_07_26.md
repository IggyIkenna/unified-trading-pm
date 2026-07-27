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
status: resolved
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
    /plans/active/issues/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md,
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
  interactive session, 2026-07-27 — deployment-service@0f0e0a7 (dep-install fix), @c5a716a (loud-failure propagation);
  live-VM confirmed via mdps-features-live-cefi-20260727-004133
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

## Update 4 — root cause of the clobber race identified; loud-failure propagation shipped; race is self-healing (not a bug)

**Root cause of the repeated clobber (closes the `[OPERATOR]` todo — no operator action needed):** the mechanism is
`google_cloud_scheduler_job.code_tarball_refresh_cron`
(`deployment-service/terraform/gcp/code_tarball_refresh_scheduler.tf`), schedule `*/30 * * * *` UTC, confirmed live:
`gcloud scheduler jobs list --location=asia-northeast1` shows `uts-prod-code-tarball-refresh-cron … ENABLED`. It invokes
a Cloud Run Job (`code-tarball-refresh`) that does ONE sparse-checkout of `deployment-service@live-defi-rollout` at the
START of each ~1.5min execution, then runs `refresh_code_tarballs.sh`, which calls `create-code-tarballs.sh` once per
tracked repo whose LDR-tip SHA changed since last tick (typically several of the ~11 tracked repos per tick).
`create-code-tarballs.sh` (lines ~518-524) unconditionally republishes `vm/setup-data-pipeline-vm.sh` +
`vm-exec-with-gcs-tee.sh` + `heartbeat_daemon.py` on **every** invocation, regardless of which repo it was asked to
build — from that execution's single bootstrap-checkout snapshot, with no SHA-gate on the vm/ files themselves. Net
effect: any manual publish of an uncommitted or just-committed fix can be overwritten by an already-in-flight cron
execution that bootstrapped its checkout moments earlier, and — because the same stale snapshot is re-uploaded once per
changed-repo within that one execution — it can look like a fast, repeating, adversarial clobber when it is actually one
stale execution's loop finishing.

**This is not a correctness bug, it is a self-healing timing window bounded to ≤1 cron tick (~30min):** "Source =
committed LDR" is the cron's documented, intended behavior (see its own header comment) — any execution that starts
_after_ a fix lands on `origin/live-defi-rollout` re-checks-out fresh and republishes the correct content. Verified
directly: `gsutil stat` + full content diff of the live GCS object against the local (fixed) file is byte-identical as
of this Update, generation `1785107836191943`, unchanged since the last manual publish (`23:17:16Z` on 2026-07-26) —
several cron ticks have fired since then with no further clobber, confirming convergence.

**A pre-existing, already-built guard closes the race for future interactive verification, no code change needed:**
`lc_verify_setup_script_freshness()` (`deployment-service/scripts/vm/lib/launcher_common.sh`, called automatically by
`lc_gcloud_create` for ~80 launchers) was root-caused for this EXACT failure class on 2026-07-12
(`issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`) and already supports `LC_SETUP_SCRIPT_FRESHNESS=auto`
(default `warn`, non-blocking) — auto-republishes the local script over GCS via `gcloud storage cp` immediately before
VM creation, closing the exact race window this issue hit. Used for this session's live-VM confirmation launch below.
**Recommendation (not actioned — a default-behavior change to shared fleet-wide infra needs explicit operator sign-off,
out of scope for this issue):** consider flipping the global default from `warn` to `auto` for
`LC_SETUP_SCRIPT_FRESHNESS` (tarballs' `LC_TARBALL_FRESHNESS` should stay `warn` — auto-republishing full tarballs
before every launch has a real latency/cost cost the setup-script-only check doesn't).

**Loud-failure propagation — shipped:** `setup-data-pipeline-vm.sh`'s `_self_delete_on_setup_failure` EXIT trap
previously nested its forensic upload (`vm-setup.log` + `SETUP_EXIT_STATUS`) AND its self-delete inside the SAME
`VM_SHUTDOWN_ON_COMPLETION=true` gate — so every long-running "live" launcher (`VM_SHUTDOWN_ON_COMPLETION=false` by
design: `launch-mdps-features-live.sh`, `launch-mtds-live-cefi-consolidated.sh`,
`launch-mtds-live-prediction-consolidated.sh`, `launch-perp-clob-live.sh`, `launch-prediction-live.sh`,
`launch-features-cross-cutting.sh`, `launch-cefi-fwd-daily-cron-vm.sh`, `launch-tradfi-fwd-daily-cron-vm.sh`) got
**zero** signal on a bootstrap failure — exactly this issue's original 2.5h silent stall. Confirmed this trap only ever
fires pre-launch (disarmed via `trap - EXIT` right before the real task execs, per its own comment: "A non-zero exit of
this setup script AFTER successful launch must NOT delete the VM"), so `VM_SHUTDOWN_ON_COMPLETION=false`'s real intent
("don't delete a successfully-launched live consumer when it later restarts") never applies to a bootstrap that never
reached launch — there is nothing worth preserving by leaving a bootstrap-failed VM running. Fixed: forensics upload +
self-delete now run unconditionally on any bootstrap failure; the same rc is also written to the canonical
`vm-logs/<vm>/EXIT_STATUS` blob (`_gcs.EXIT_STATUS_BLOB`) that `exit_code_fleet_monitor.py`'s
`read_terminal_exit_code()` already polls for terminated VMs — once the VM self-deletes, the _existing_
`DP_VM_EXIT_NONZERO` alert path picks it up for free, same as any other launcher's task-crash, with no new monitor
needed. `bash -n` clean, `quality-gates.sh` green. **Ship status**: blocked on the same foreign `unified-api-contracts`
dirty-dependency state that already blocked `deploy_features_service_cloud_run.sh` earlier this session (another agent's
active WIP, growing across retries — not safe to touch) — will retry quickmerge once it clears.

## Update 5 — live-VM confirmation: the ORIGINALLY-SCOPED bug is fixed; exposed a separate, already-anticipated bug

Deleted the previous VM (`--force` singleton-lock bypass not needed — nothing was RUNNING) and relaunched
`mdps-features-live-cefi-20260727-004133` with `LC_SETUP_SCRIPT_FRESHNESS=auto` (this launcher calls
`gcloud compute instances create` directly rather than through `lc_gcloud_create`, so the auto-freshness guard never
actually engaged for it — moot here since the live GCS object already matched the committed `0f0e0a7` fix byte-for-byte
per Update 4's verification).

**Result: dependency install succeeded cleanly for the first time.** `run.log` shows all 6 expected tarballs installed
(`uac`, `utl`, `deployment-service`, `mdps`, `mtds`, `features`), `uv pip install` completed with no unsatisfiable
conflict, no archived-repo pull-in — **this issue's two bugs (archived-repo tarball entries + unresolved compound
VM_SERVICE lookup) are CONFIRMED fixed against a real GCE VM boot**, not just the Update 1 isolated functional test.

The VM then failed one step later, at the actual service launch:
`python -m market_data_processing_service+features_service` (the raw, unsplit compound `VM_SERVICE` passed literally to
`python -m`) → `No module named ...`. This is a **separate, previously-unreachable bug** in the exec-dispatch layer
(never hit before because Gap-1's dependency-install failure always killed every prior attempt first) — filed separately
as `issues/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md`, since fixing it requires real design
work (neither MDPS's nor features-service's CLI today supports the launcher's "one co-located whole-asset-group live
consumer" premise — confirmed by reading both services' actual `argparse` contracts), not a mechanical patch, and the
launcher's own docstring already flags full operational launch as deferred pending unfinished Phase-13/15 wiring. VM
deleted after confirming the failure (no reason to bill an e2-standard-8 on a known-dead exec path).

**Net: this issue is now fully resolved for its own stated scope** (the shared-venv dependency conflict at install
time). Full end-to-end "MDPS+features actually computing candles live" confirmation is NOT achievable until the
successor issue's design question is resolved — tracked there, not here.

## Todos

- [x] [INFRA] P1. ~~Commit + ship (quickmerge) the two fixes~~ — **DONE**: `deployment-service@0f0e0a7`,
      `quality-gates.sh` green, landed on `live-defi-rollout`.
- [x] [OPERATOR] P2. ~~Identify what is repeatedly re-publishing~~ `setup-data-pipeline-vm.sh` — **DONE**, see Update 4:
      `uts-prod-code-tarball-refresh-cron` (Cloud Scheduler, `*/30 * * * *`) republishing vm/ scripts unconditionally
      from a per-execution bootstrap-checkout as a side effect of any tracked repo's tarball rebuild. Self-healing
      (converges within ≤1 tick of a landed fix); no operator action required.
- [x] [SCRIPT] P2. ~~Get a genuine live-VM confirmation of the fix~~ — **DONE**, see Update 5: dependency install
      succeeds cleanly on a real VM boot. (Full live-pipeline confirmation blocked on the separately-filed exec-dispatch
      design gap, not on anything in this issue's scope.)
- [x] [INFRA] P2. ~~loud-failure propagation~~ — **DONE**: `deployment-service@c5a716a`, `quality-gates.sh` green,
      shipped once the foreign `unified-api-contracts` dirty dependency cleared.
- [ ] [INFRA] P3. Consider flipping `LC_SETUP_SCRIPT_FRESHNESS` default from `warn` to `auto` fleet-wide (see Update 4
      recommendation) — operator decision, not actioned here (shared-infra default-behavior change, out of scope for
      this issue's bounded fix).

**Status: RESOLVED** for this issue's scope (shared-venv dependency conflict). Remaining P3 item is an operator-owned
recommendation, not a blocker; the exec-dispatch gap discovered during verification is tracked in its own issue doc
(linked above).
