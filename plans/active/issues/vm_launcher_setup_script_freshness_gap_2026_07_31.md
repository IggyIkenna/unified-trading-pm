---
doc_type: issue
title:
  "139 of 143 VM launchers call `gcloud compute instances create` directly, bypassing `lc_verify_setup_script_freshness`
  entirely — the fleet-wide preemption-signal systemd unit's own freshness is unverified"
summary: >-
  Found while hardening `launch-api-football-backfill-vm.sh`'s two best-effort GCS writes
  (infra_satellite_ao_dispatch_batch1_2026_07_26.md). A live sweep of every af-backfill preemption confirmed via `gcloud
  compute operations list` (5 events, 2026-07-25..2026-07-31) found the `PREEMPTED` marker missing 5/5 times — despite
  af-backfill booting via the shared `setup-data-pipeline-vm.sh` startup-script seam, which (per its own 2026-07-20/21
  comments) installs a `uts-preemption-signal.service` systemd unit specifically to write that marker fleet-wide, with
  its own 2-attempt retry + tight timeouts. Investigating why an already-hardened mechanism still misses 5/5 surfaced a
  structural gap: `lc_verify_setup_script_freshness` (the guard that would catch a stale copy of
  `setup-data-pipeline-vm.sh` on GCS) is only invoked automatically by `lc_gcloud_create` — and only 4 of 143 launcher
  scripts actually call `lc_gcloud_create`. The other 139 (including af-backfill, before this session's fix) call
  `gcloud compute instances create` directly and never invoke the freshness guard at all, despite `launcher_common.sh`'s
  own doc-comment claiming "every caller of lc_gcloud_create (~80 launchers) inherits it automatically" — that comment
  is itself stale; the real number is 4. This session could NOT confirm (bucket has no object versioning, so no
  historical generation to inspect) whether a stale `vm/setup-data-pipeline-vm.sh` GCS copy is the actual cause of the
  5/5 miss, but the absence of ANY freshness check across 139 launchers is a real, independently-confirmed gap
  regardless of whether it explains this specific incident.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [vm-launcher-runbook, spot-preemption, setup-script-freshness, gcs-staleness, fleet-wide]
related:
  [
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md,
    /plans/active/issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md,
    /plans/archive/issues/vm_tarball_upload_expired_wif_token_interactive_slot_2026_07_25.md,
  ]
created: 2026-07-31
author: unknown
last_updated: 2026-07-31
priority: P2
parent_epic: infrastructure_master
source: "Found while working infra_satellite_ao_dispatch_batch1-007 (slot 8, backend_engineer, 2026-07-31)"
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: infra
drift_direction: advance-code
locked_since:
depends_on: []
supersedes:
superseded_by:
context_scope:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
  ]
---

# 139 VM launchers bypass the setup-script freshness guard

## What I found

Working `infra_satellite_ao_dispatch_batch1-007` ("Make the launcher's two best-effort GCS writes reliable"), I
live-swept every `af-backfill-*` VM log dir in `gs://deployment-scripts-central-element-323112/vm-logs/` (50 total,
2026-07-17..2026-07-31) and cross- referenced against
`gcloud compute operations list --filter="operationType=compute.instances.preempted AND targetLink~'af-backfill'"`,
which returned exactly 5 confirmed preemption events: `af-backfill-20260726-013313`, `-103202`, `-20260727-011039`,
`-055450`, `-20260731-123439`. **All 5 have NO `PREEMPTED` marker** in their `vm-logs/` dir — a 100% miss rate on
confirmed preemptions, not a rare one-off.

This is surprising because `setup-data-pipeline-vm.sh` (every one of these VMs' `startup-script-url`) already installs a
dedicated `uts-preemption-signal.service` systemd unit (`scripts/vm/setup-data-pipeline-vm.sh:117-208`) specifically to
write this marker fleet-wide, with its own 2-attempt retry and a 25s `TimeoutStopSec` budget (dated 2026-07-20/21 in its
own comments — i.e. already hardened, and that hardening should have been live for all 5 sampled failures). Two working
theories, not yet distinguished:

1. **The GCS copy of `setup-data-pipeline-vm.sh` was stale** at these VMs' boot time (missing the systemd-unit section
   entirely, or an earlier/less-hardened version of it). Could not confirm: the
   `deployment-scripts-central-element-323112` bucket has no object versioning enabled and the object has only ONE
   generation on record, so there is no historical copy to inspect against the preemption dates.
2. **The systemd unit runs but still loses the race in practice** (aggregate 3 metadata curls + up to 2
   `gcloud storage cp` attempts can exceed 25s on a loaded/small VM, since `gcloud storage cp` itself has a real
   Python-interpreter cold-start cost that isn't accounted for in the unit's own budget comment).

Regardless of which (both may be true), a real, independently-confirmed structural gap exists:
`lc_verify_setup_script_freshness` (`scripts/vm/lib/launcher_common.sh:878+`) — the function that would catch theory 1
by comparing the local repo's `setup-data-pipeline-vm.sh` against the GCS copy's md5 and warn/enforce/auto-republish —
is only invoked automatically inside `lc_gcloud_create` (`launcher_common.sh:293`). Measured directly:

```
$ grep -l "lc_gcloud_create" scripts/vm/*.sh | wc -l
4
$ grep -l "gcloud compute instances create" scripts/vm/*.sh | wc -l
139
```

**139 of 143 launcher scripts call `gcloud compute instances create` directly and never invoke
`lc_verify_setup_script_freshness` at all** (grep-confirmed — none of the 139 call it directly either).
`launcher_common.sh:291-292`'s own comment — _"checked here, not per-launcher, so every caller of lc_gcloud_create (~80
launchers) inherits it automatically"_ — is itself stale/inaccurate: the real count of `lc_gcloud_create` callers is 4,
not ~80. This means the overwhelming majority of the fleet has **zero automated warning** if
`vm/setup-data-pipeline-vm.sh` (or any other GCS-fetched startup script) on GCS drifts from the repo — a VM silently
boots against stale startup logic with no signal, the exact failure mode `lc_verify_tarball_freshness` (a sibling guard,
already called by most launchers for code tarballs) was built to prevent for tarballs specifically.

## Why it matters

`setup-data-pipeline-vm.sh` is the shared startup-script seam for the majority of the SPOT fleet — it is where the
fleet-wide preemption-signal unit, the file-descriptor limit, Python/uv install, and (per its own comments) "every
future launcher" preemption-recovery guarantee live. If this ONE file can drift silently on GCS with no automated check
across 139 launchers, every guarantee documented as "fleet-wide because it lives in the shared seam" is only as reliable
as someone remembering to manually re-run `create-code-tarballs.sh` (or whatever uploads `vm/*.sh`) after every relevant
deployment-service commit — exactly the kind of best-effort, unenforced assumption this same workspace's tarball-pinning
system was built to eliminate for code tarballs. This directly bears on the confirmed 5/5 af-backfill marker-miss
finding above (RESOLVED for af-backfill specifically this session by making its own inline shutdown- script
self-contained and baked-in — see infra_satellite_ao_dispatch_batch1_2026_07_26.md's todo — but the other 138 raw-create
launchers remain unguarded either way).

## Recommended decision

This is bigger than a single bounded todo — it is a fleet-wide audit + remediation across up to 139 files, and the
remediation shape itself needs a decision (migrate callers to `lc_gcloud_create`, vs. add a standalone
`lc_verify_setup_script_freshness` call to each raw-create launcher, vs. accept the mechanism-level fix — my af-backfill
launcher's own inline shutdown-script no longer depends on the GCS copy of `setup-data-pipeline-vm.sh` being fresh at
all — as the actual pattern to propagate). Filing as a scoped audit + a design question, not attempting the 139-file
sweep here.

- [x] ✅ [INFRA] P2. Correct `launcher_common.sh:291-292`'s stale "~80 launchers" comment to the measured count (4) — a
      one-line doc fix, cheap and immediately actionable. (repo: deployment-service) — deployment-service@daf3ad5
- [x] ✅ [DATA] P2. Determine whether GCS object versioning can be retroactively enabled on
      `deployment-scripts-central-element-323112` (and the other `deployment-scripts-*` buckets) so a future incident of
      this shape has a historical generation to inspect — would have let this session confirm/refute theory 1 directly
      instead of leaving it open. (repo: deployment-service / infra — GCS bucket config, read the current bucket policy
      first) — **DETERMINED 2026-08-04 (slot 6, data_engineering): technically YES, but NOT recommended bucket-wide.**
      See Progress Log entry below for the full finding + risk analysis.
- [x] ✅ [SCRIPT] P2. **DEFAULT-RULED 2026-08-06, option (a): migrate high-value raw-create launchers to
      `lc_gcloud_create`.** First batch (3 launchers) shipped — deployment-service@6998cc228. Remaining ~136 raw-create
      launchers need a dedicated migration plan (see follow-up todo below).
- [ ] [SCRIPT] P3. **Follow-up: dedicated migration plan for remaining ~136 raw-create launchers to
      `lc_gcloud_create`.** Shape = option (a), operator-ruled 2026-08-06. First batch done:
      `launch-footystats-forward-poll.sh`, `launch-scenario-runner-vm.sh`, `launch-prediction-arb-detector.sh` (all
      migrated at deployment-service@6998cc228). Remaining complexity tiers: (1) ~54 no-SPOT startup-script-url
      launchers with large disk (250GB, need `${BOOT_DISK_SIZE%GB}` extraction), (2) launchers with `--boot-disk-type`
      env var override (lc_gcloud_create lacks this param — either add it or document the pd-balanced default is
      sufficient), (3) launchers using `--metadata-from-file` (e.g. strategy-test shutdown script — cannot migrate until
      lc_gcloud_create supports it or the feature is dropped). **Done when**: a dedicated plan is authored and
      dispatched covering the full remaining corpus.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries) -- swapped in the two named source files
  (`launcher_common.sh`, `setup-data-pipeline-vm.sh`) the doc's own root-cause section cites, dropped two related-issue
  entries to stay minimal.
- **data_engineering 2026-08-04 (slot 6) — GCS versioning retroactive-enablement determination**:
  - **Buckets**: `gcloud storage buckets list | grep deployment-scripts` returns exactly ONE bucket,
    `deployment-scripts-central-element-323112` — it's a documented SINGLETON (`terraform/gcp/main.tf:201-243` comment:
    "one physical bucket in the central project"). There are no other `deployment-scripts-*` buckets to consider.
  - **Can it be retroactively enabled? YES, mechanically** — `gcloud storage buckets update <bucket> --versioning` is a
    bucket-level toggle available on any existing bucket at any time (confirmed: `gcloud storage buckets update --help`
    lists `--[no-]versioning`). Live-checked the bucket now (`gcloud storage buckets describe … --format=json`):
    `uniform_bucket_level_access: false`, `soft_delete_policy.retentionDurationSeconds: "0"`, no `versioning` key
    present (= disabled, the default) — confirms versioning is currently OFF and nothing structural (e.g. a
    retention-lock) blocks turning it on.
  - **But it does NOT retroactively recover history** — GCS Object Versioning only versions objects created/overwritten
    AFTER it's enabled; it cannot reconstruct generations for objects already overwritten before the flag flips. So even
    if enabled today, it would NOT retroactively resolve theory 1 for the 5 already-confirmed af-backfill preemption
    events (2026-07-25..07-31) — those `vm/setup-data-pipeline-vm.sh` overwrites, if any happened, are already gone. It
    only helps a **future** incident of this shape, exactly as the todo's own title frames it.
  - **Risk-informed recommendation: do NOT enable it bucket-wide.** This exact bucket has documented incident history
    directly on point — `plans/archive/issues/deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md`: 57 TiB
    (~$1.3k/mo, growing ~8 TiB/day) of retained shadow copies from `vm-logs/run.log` re-uploads (every 30-120s,
    whole-file, 3-16 MiB each) and `deployments/active/*.json` heartbeats (~60s cadence). The 2026-06-01 remediation
    explicitly disabled soft-delete AND codified **"no versioning"** into Terraform (`main.tf:205,207-243`) as one of
    the two settings that fixed it. GCS Object Versioning has no per-prefix scope (unlike the Delete lifecycle rules,
    which DO support `matches_prefix`) — it is bucket-wide only, so turning it on would apply to the same
    `vm-logs/`/`deployments/active/` high-churn prefixes that caused the original incident, minting a new noncurrent
    generation on every overwrite.
  - **Partial mitigation, not a clean bill of health**: the bucket's existing Delete lifecycle rules (`age=14` on
    `vm-logs/`, `age=15` on `vm-heartbeat/`, `age=30` on the rest — live-reconfirmed via
    `gcloud storage buckets describe --format="json(lifecycle_config)"`) use bare `age` conditions with no `isLive`
    restriction, and GCS's `Age` condition is measured per-version from that version's own creation time — so noncurrent
    versions under those prefixes would still age out on the same 14/15/30-day windows rather than accumulating forever
    the way soft-delete's Google-managed shadow copies did (soft-delete objects sit outside lifecycle-rule reach
    entirely — the actual mechanism difference behind the original incident). Bounded ≠ free, though: it would still
    sustain a steady-state noncurrent-version multiplier on `vm-logs/` (the bucket's dominant contributor already) for a
    benefit that only serves a small set of genuinely low-churn files.
  - **The file that actually needs this (`vm/setup-data-pipeline-vm.sh` + `scripts/vm/lib/*`) is low-churn, not
    high-churn**: traced its writer — `scripts/vm/create-code-tarballs.sh:539` (`gcs_upload "vm" …`), invoked either by
    an operator manually or by `cloud-build/refresh-tarballs.cloudbuild.yaml` (fires only when a tarball is older than
    the latest `live-defi-rollout` commit) — i.e. per-relevant-commit, not a 30-120s loop. The `vm/` prefix currently
    has NO lifecycle rule at all (deliberately, per the archived doc: "launch-time working copies").
  - **Net**: bucket-wide versioning is technically available but reintroduces a shaped risk this same bucket already
    paid to eliminate, for a payoff (retroactive lookup) that the archived-and-gone incidents can't retroactively claim
    anyway. If the operator's pending remediation-shape decision (see the `[OPERATOR]` todo below) ends up wanting
    historical-generation visibility specifically for `vm/`-prefix files, the lower-risk path is scoping that need away
    from this singleton bucket (e.g. a dedicated low-churn bucket/prefix for launch-time config, or leaning on the
    existing `lc_verify_setup_script_freshness` md5-drift check, which already catches DRIFT prospectively without
    needing historical generations) rather than flipping versioning bucket-wide here. Left as informational context for
    the `[OPERATOR]` todo below, not a new decision to make — that todo's scope is the 139-launcher remediation shape,
    not this bucket's versioning policy specifically.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **slot-8 2026-08-08 (vm_launcher_setup_script_freshness_gap-004)**: Migrated first batch of raw-create launchers to
  `lc_gcloud_create` — `launch-footystats-forward-poll.sh` (e2-small/10GB), `launch-scenario-runner-vm.sh`
  (e2-standard-2/50GB), `launch-prediction-arb-detector.sh` (e2-standard-4/50GB). Pattern: tarball freshness check gated
  on `! DRY_RUN` → export `LC_DRY_RUN` → call `lc_gcloud_create` (drops `managed-by=deployment-service` from caller
  labels — added automatically by the wrapper). Also fixed a pre-existing duplicate `lc_verify_tarball_freshness` call
  in `launch-scenario-runner-vm.sh`. QG green (all gates passed, 227s). Shipped: deployment-service@6998cc228. Remaining
  ~136 launchers need a dedicated migration plan (follow-up todo added above).
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **data_engineering 2026-08-09 (slot 28) — live reproduction confirmed via `gcloud storage objects describe`**: while
  building a new raw-create launcher (`launch-prediction-kalshi-historical-gap-backfill-vm.sh`,
  `prediction_satellite_ao_dispatch_batch9_2026_08_09.md` todo 3), shipped a `setup-data-pipeline-vm.sh` fix
  (deployment-service@fe20aed8c, e2e-testing NODEPS routing gap), republished it via `lc_verify_tarball_freshness`'s
  auto-republish path, then launched — the VM failed with the EXACT SAME pre-fix error. Direct
  `gcloud storage objects describe gs://deployment-scripts-central-element-323112/vm/setup-data-pipeline-vm.sh` at that
  moment showed `Content-Length: 184235` (the OLD pre-fix size) with an `Update time` seconds AFTER my own republish — a
  concurrent agent's own launcher (on a different, not-yet-pulled local checkout) had raced my publish and clobbered it
  back to stale content in the same shared-fleet window theory 1 above already suspected but couldn't confirm (no object
  versioning). This is direct, dated evidence FOR theory 1 as a real, live mechanism (not just plausible) — filed here
  rather than a new issue doc since it's the same root cause this doc already tracks. Workaround shipped in the new
  launcher itself (not a `lc_gcloud_create` migration — that helper has no
  `--provisioning-model=SPOT`/`--instance-termination-action` support, which this backfill-VM-default-SPOT launcher
  needs): call `LC_SETUP_SCRIPT_FRESHNESS=auto lc_verify_setup_script_freshness` directly, immediately before its own
  `gcloud compute instances create`, narrowing (not eliminating) the race window to right before creation instead of
  leaving it wide open for the whole tarball-freshness-check duration beforehand. Does not touch the P3 follow-up todo's
  scope (the 136-launcher `lc_gcloud_create` migration) — `lc_gcloud_create` itself would need SPOT/disk-type support
  added before a SPOT launcher like this one could migrate to it.
