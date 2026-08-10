---
doc_type: issue
title: >-
  cefi-fwd-20260806-064507 (GCE STANDARD/on-demand, deliberately instances.stop'd) classified PREEMPTED and paged
  CRITICAL DP_VM_PREEMPTED_NO_RELAUNCH — closed with an is_spot veto in classify_terminated_vm
summary: >-
  A cefi-fwd forward-poll VM launched by `launch-cefi-forward-poll.sh` (no `--provisioning-model=SPOT` — always
  on-demand) was deliberately `instances.stop`'d by `unified-trading-sa` (two `instances.insert` 13s apart, two
  `instances.stop` ~2-2.5 min apart, zero `compute.instances.preempted` operations — all confirmed via `gcloud compute
  instances describe` + `gcloud logging read`), yet `exit_code_fleet_monitor.classify_terminated_vm` resolved
  `TerminationVerdict.PREEMPTED` and the `RelaunchPreemptedVm` actuator's failure-to-relaunch (correctly — there was
  nothing to resume) self-emitted a CRITICAL `DP_VM_PREEMPTED_NO_RELAUNCH` page. Root cause: BOTH existing preemption
  signals (the in-guest GCS `PREEMPTED` marker written by the shared `setup-data-pipeline-vm.sh` shutdown seam, and the
  `was_instance_preempted` Compute-Operations-API fallback) are trusted unconditionally once either says `True` —
  neither is cross-checked against the instance's OWN `scheduling.provisioning_model`, so a stale/incorrect signal from
  either source flows straight through to a false PREEMPTED verdict. Fixed with a defense-in-depth veto: a new
  `ComputeEngineClient.aggregated_list_instances` field (`scheduling_provisioning_model`, unified-trading-library) feeds
  a new `deployment_service._compute_ops.make_scheduling_model_checker`, consulted only on the candidate-preempted path,
  which lets `classify_terminated_vm`'s new `is_spot` parameter veto `preempted=True` whenever the instance is confirmed
  non-SPOT — making a STANDARD VM structurally incapable of producing a PREEMPTED verdict regardless of which upstream
  signal was wrong. The exact shutdown-script bug (if any) that produced the false GCS marker for this specific VM was
  NOT pinned down (see "What I did not resolve" below) — the veto closes the observable symptom either way.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [cefi, vm, preemption, false-positive, monitoring, data-pipeline, dp-vm-008, alerting]
related:
  [
    /plans/archive/2026_08/issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md,
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: "2026-08-06"
author: unknown
priority: P2
parent_epic: observability_master
source:
  "Operator live-diagnosed via gcloud compute instances describe + gcloud logging read (2026-08-06), handed to a
  sub-agent to verify against code and fix at the root."
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: none
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/archive/2026_08/issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/deployment_service/data_pipeline_monitors/_compute_ops.py,
    deployment-service/scripts/vm/launch-cefi-forward-poll.sh,
  ]
---

# cefi-fwd VM PREEMPTED false positive on a STANDARD (on-demand) instance — closed with a scheduling-config veto

## What I found

**The evidence (operator-supplied, re-verified against code, not re-run live):**

- VM `cefi-fwd-20260806-064507`: `gcloud compute instances describe` showed `scheduling.provisioningModel: STANDARD`,
  `preemptible: false`. `launch-cefi-forward-poll.sh` (the launcher `LAUNCHER_FOR_VM_PREFIX["cefi-fwd-"]` maps to) never
  passes `--provisioning-model=SPOT` — confirmed by reading the launcher's `gcloud compute instances create` invocation
  directly. GCE structurally cannot preempt a STANDARD instance.
- `gcloud logging read` audit logs: two `v1.compute.instances.insert` 13 seconds apart (06:45:13Z, 06:45:26Z), then two
  `v1.compute.instances.stop` (06:53:26Z, 06:55:45Z) — all by `unified-trading-sa`. A separate query for
  `jsonPayload.event_subtype="compute.instances.preempted"` scoped to this project/timeframe returned **zero rows** for
  this VM.
- The monitor still fired CRITICAL `DP_VM_PREEMPTED_NO_RELAUNCH`.

**Root cause, traced through the actual code (not assumed):**

`exit_code_fleet_monitor.sweep()` resolves `is_preempted` two ways, in order: (1) `_gcs.is_vm_preempted` — a GCS
`vm-logs/{vm}/PREEMPTED` blob written by an in-guest shutdown-script; (2) if that blob is absent AND the VM would
otherwise resolve to the `GONE_NO_CAPTURE` candidate path, `preemption_op_checker` — the
`ComputeEngineClient.was_instance_preempted` Operations-API fallback (added 2026-07-31 for a DIFFERENT, opposite-
direction bug: an early preemption whose in-guest marker never got written in time — see
`cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md`). **Whichever one says `True` is trusted
unconditionally** — `classify_terminated_vm` had no way to cross-check it against the instance's own scheduling config,
so a stale/incorrect signal from EITHER source flows straight through to `TerminationVerdict.PREEMPTED` ->
`DP_VM_PREEMPTED` (AUTO_RECOVER) -> `escalation._recover_preempted_vm` -> `RelaunchPreemptedVm`, which (correctly, per
its own contract) found no `LAUNCH_PARAMS.json`/checkpoint to resume for a VM that ran ~8-10 minutes and captured
nothing, failed the relaunch, and self-emitted the CRITICAL `DP_VM_PREEMPTED_NO_RELAUNCH` page — precisely as designed
for "a relaunch legitimately could not happen," just fed a false premise.

**What I did NOT resolve — the exact write path for this specific VM's false signal.** I read the shared shutdown-
script seam (`setup-data-pipeline-vm.sh` § "0b. SPOT-preemption signal", installed on EVERY VM booted from this script —
including non-SPOT `cefi-fwd-*`, since it's the SAME shared `startup-script-url` every launcher uses, SPOT or not) end
to end: it gates the actual blob-write on `curl .../computeMetadata/v1/instance/preempted` returning literally `"true"`,
which per GCP's documented semantics should read `false` for a STANDARD instance on ANY shutdown trigger (including a
deliberate `instances.stop`). I could not find a logic bug in that gate by static reading, and I have no live access to
this specific VM's serial console / shutdown-script execution log to confirm whether the blob genuinely existed (my
hypothesis) or whether the Operations-API fallback path was consulted and returned an incorrect `True` (I could not find
a bug there either — `was_instance_preempted`'s server-side filter + client-side exact-match both read correctly against
the user's own "zero preemption operations" finding). **I chose not to over-fit a specific narrative to unverifiable
runtime state** — the shipped fix is a defense-in-depth veto that closes the OBSERVABLE symptom regardless of which
upstream signal was wrong, per this task's own explicitly-endorsed acceptable resolution ("gate `preempted=True` so it
can never be set for a VM whose scheduling config is STANDARD/on-demand").

**The double-`instances.insert` (13s apart) — investigated, NOT fixed, flagging only — UPGRADED to P2, it recurs on
every relaunch, not a one-off.** This looks like the launcher's own singleton-lock check
(`gcloud compute instances list --filter='name~"^cefi-fwd-[0-9]" AND status=RUNNING'`) racing a near-simultaneous second
invocation: a freshly-inserted VM takes some seconds to reach `RUNNING`, so two invocations within that window can both
see "no existing running VM" and both proceed to create. **Operator-supplied follow-up evidence (same incident window,
post-fix): a SECOND near-simultaneous double-launch happened on the very relaunch of the first.**
`cefi-fwd-20260806-064507` (06:45:13/06:45:26Z double-insert, the original false-positive-preempted VM) TERMINATED, then
`cefi-fwd-20260806-065757` (06:57:57Z — ~12 min later, apparently a relaunch of the first) ALSO TERMINATED, and
`cefi-fwd-20260806-065837` (06:58:43Z — only **46 seconds** after `-065757`) is the one left RUNNING. So the race fired
TWICE in one incident window, once per launch attempt — this is a recurring pattern tied to every cefi-fwd launch
(manual/cron-triggered or relaunch alike), not a rare fluke. I searched `plans/active/issues/` for an existing cefi-fwd
duplicate-launch doc and found none (the operator's own search also came up empty) — this is a genuinely new
observation, not a known/tracked issue. I did NOT fix it here: it is a separate mechanism (a launcher-side TOCTOU race,
not the classifier) from this doc's false-PREEMPTED-page root cause (the veto closes that regardless of whether the
duplicate-insert race is ever fixed) — bounding it properly (a short-lived GCS/Firestore lock, or a
create-then-verify-singleton retry) deserves its own scoped fix rather than a rushed addition here. Upgraded from P3 to
P2 given it recurs deterministically rather than being a one-off — see the follow-up todo below.

## What shipped

1. **`unified-trading-library`** — `ComputeEngineClient.aggregated_list_instances` (GCP impl) now additionally carries a
   `scheduling_provisioning_model` key (`"STANDARD"`/`"SPOT"`/...) per instance dict, read from
   `instance.scheduling.provisioning_model` — same "strictly additive, no consumer unpacks the dict" convention already
   established for the `metadata` key (2026-07-20). New unit tests:
   `tests/cloud_interface/unit/test_gcp_compute_scheduling_provisioning_model.py`.
2. **`deployment-service`**:
   - `_compute_ops.make_scheduling_model_checker(project_id)` — `vm_name -> scheduling.provisioning_model | None`,
     mirroring the existing `make_preemption_op_checker`'s never-raises contract.
   - `exit_code_fleet_monitor.classify_terminated_vm(..., is_spot: bool | None = None)` — when `is_spot is False`
     (confirmed non-SPOT), a `preempted=True` input is VETOED: classification falls through to the normal
     exit_code/captured-based path instead of resolving PREEMPTED. `is_spot is None` (unresolvable) preserves prior
     behavior exactly.
   - `exit_code_fleet_monitor.sweep(..., scheduling_model_checker=...)` — consults the checker ONLY when a candidate-
     preempted verdict is about to fire (bounded extra API call, same discipline as `preemption_op_checker`), logs a
     WARNING when it vetoes a false signal, and passes the resolved `is_spot` through to `classify_terminated_vm`.
   - `cli.py` wires `scheduling_model_checker=_compute_ops.make_scheduling_model_checker(_project_id())` into the live
     `exit-code` sweep, next to the existing `preemption_op_checker` wiring.
   - New unit tests in `tests/unit/test_data_pipeline_monitors.py`: pure-classification veto cases (`is_spot=False` over
     both `EXIT_NONZERO`- and `GONE_NO_CAPTURE`-shaped inputs, `is_spot=True`/`None` preserve prior behavior), a full
     `sweep()` reproduction of this exact VM's shape (STANDARD + false GCS marker -> vetoed to `GONE_NO_CAPTURE`, no
     `DP_VM_PREEMPTED_NO_RELAUNCH`), a bounded-cost guard (checker never called off the candidate-preempted path), and
     direct `_compute_ops.make_scheduling_model_checker` tests.

Evidence: deployment-service@5bd0017b96c9a79811a966033b875e165a010c11 (QG-green,
`bash scripts/quality-gates.sh --no-fix` sentinel matched HEAD before commit),
unified-trading-library@59acbe2fa5910c28357c35fe1d0969dd0c8326f0 (QG-green, same sentinel discipline). Both landed on
`live-defi-rollout` via `quickmerge.sh --agent`.

## Why it matters

A false `PREEMPTED` verdict on a deliberately-stopped VM burns an on-call CRITICAL page (`DP_VM_PREEMPTED_NO_RELAUNCH`)
for zero actual incident — worse than a silent miss, because it actively misdirects triage toward "check the SPOT
relaunch path" for a VM that was never SPOT at all. Any launcher sharing `setup-data-pipeline-vm.sh` as its
`startup-script-url` while NOT itself passing `--provisioning-model=SPOT` (cefi-fwd is one; there may be others) was
exposed to this class before the veto shipped.

## Recommended decision

- [x] ✅ [OPERATOR] P2. **RESOLVED 2026-08-08 — no trigger needed, already picked up by the routine build cadence.**
      Once `deployment-service`/`unified-trading-library` land on `live-defi-rollout` and promote to `main`, confirm (or
      trigger) a fresh `deployment-api` build+deploy so the live `uts-prod-dp-exit-code-monitor` Cloud Run job actually
      picks up the fix (same deploy-lag gap `cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md`
      flagged for the prior preemption fix). Done when
      `gcloud artifacts docker images list asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/deployment-api --include-tags --sort-by=~UPDATE_TIME --limit=1`
      shows an `UPDATE_TIME` after this fix's merge commit. **Live-checked 2026-08-08**: fix commit
      `deployment-service@5bd0017b` landed `2026-08-06T10:53:59+01:00`; the `deployment-api` image has since been
      rebuilt repeatedly (5 builds on 2026-08-08 alone), latest `sha256:fc6deaf8` tagged `latest`,
      `UPDATE_TIME     2026-08-08T07:23:26` — well after the fix commit.
      `gcloud run jobs describe uts-prod-dp-exit-code-monitor` confirms the job references `deployment-api:latest`, and
      Cloud Run Jobs pull the tag fresh per execution, so the live monitor already runs the fixed code. This was never
      actually an operator-only action — `deployment-api` rebuilds on a routine, frequent cadence (multiple builds/day
      observed) independent of any manual trigger.
- [x] ✅ [SCRIPT] P2. Fix the `launch-cefi-forward-poll.sh` singleton-lock TOCTOU race — CONFIRMED RECURRING, not a
      one-off: it fired on BOTH the original launch (`-064507`/`-064513`/`-064526`, insert timestamps 13s apart) AND its
      own relaunch 12 minutes later (`-065757` then `-065837`, only 46s apart) in the same incident window. **Shipped
      `deployment-service@4c28ca640f6b6921f39c493c69995a04984df5f3`** (2026-08-06, the same day as this doc — an atomic
      GCS create-if-absent singleton lock, `lc_acquire_singleton_lock`, gating the RUNNING-VM check) — found still
      live + tested on `cefi_satellite_ao_dispatch_batch9_2026_08_07.md` todo 2's 2026-08-09 pickup; see that plan's
      flipped checkbox for the full re-verification (6 regression tests incl. a 12-process concurrent-race proof, all
      green). This checkbox and the plan's were left stale for 3 days because 4 successive na-eligibility-audit passes
      checked plan-claim status, not live code state — closing both now.
- [ ] [SCRIPT] P3. If runtime/serial-console access to a freshly-`instances.stop`'d `cefi-fwd-*` VM is ever available
      before it self-cleans, capture the shutdown-script's own log line
      (`[preemption-shutdown] wrote PREEMPTED signal for ...` vs "FAILED") to pin down whether the false signal came
      from the GCS blob write itself or the Operations-API fallback — closes the "What I did not resolve" gap above. Not
      blocking: the veto already closes the observable symptom either way.

## Progress Log

- 2026-08-06: filed after verifying the operator's live `gcloud` diagnosis against the actual code (confirmed:
  `launch-cefi-forward-poll.sh` never passes `--provisioning-model=SPOT`; `classify_terminated_vm` and
  `preemption_op_checker` both trusted their respective signals unconditionally with no scheduling-config cross-check).
  Shipped the `is_spot` veto (deployment-service + unified-trading-library, both QG-green) rather than chasing the
  unverifiable exact write-path bug. Searched `plans/active/issues/` for a prior cefi-fwd duplicate-launch doc per this
  task's instruction — found none; the double-insert race was initially filed as a new, separate P3 flag.
- 2026-08-06 (same day, follow-up): shipped both fixes —
  `unified-trading-library@59acbe2fa5910c28357c35fe1d0969dd0c8326f0` (`aggregated_list_instances`
  scheduling_provisioning_model field) then `deployment-service@5bd0017b96c9a79811a966033b875e165a010c11` (the `is_spot`
  veto), both via `quickmerge.sh --agent` after a genuinely QG-green tree (sentinel verified == HEAD before each
  commit). Received further live evidence mid-ship: the duplicate-launch race recurred a SECOND time in the same
  incident window, on the relaunch of the original VM (`-065757`/`-065837`, 46s apart) — confirms it is a deterministic
  recurring pattern, not a one-off, so upgraded that follow-up from P3 to P2 (still not fixed in this pass — a
  launcher-side TOCTOU fix is a separate, scoped piece of work). Status stays `open` pending the `deployment-api`
  redeploy confirmation ([OPERATOR] todo above) and the P2 launcher-race follow-up.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid (OVERRIDE of the classifier's
  RECLASSIFY draft verdict, per this run's own Phase-2 conflict-check). The line-175 [SCRIPT] P2 TOCTOU-race item is
  ALREADY claimed by cefi_satellite_ao_dispatch_batch9_2026_08_07.md todo 2 (status: draft, awaiting operator approval;
  identical 13s/46s evidence, explicit "do not touch" note pointing at this exact doc/line) — reclassifying this doc
  would create a duplicate-dispatch surface once batch9 is approved. Item 167 is [OPERATOR]-gated by nature; item 181 is
  time-gated/opportunistic (also independently deferred by batch9's own cross-tranche review). Doc stays NA;
  batch9-finalize is the designated mechanism to flip the line-175 checkbox once batch9 ships.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries, was 5) -- the prior list was 100% source paths with
  zero codex/plan pointers despite `related:` naming 4 relevant docs; added the two directly-relevant codex SSOTs
  (data-pipeline-alerts, spot-vms-for-backfill) and the shard24 false-page doc (shares the exact `preemption_op_checker`
  mechanism this doc's root cause implicates), dropping `setup-data-pipeline-vm.sh` and `gcp_compute.py` (lower
  forward-relevance -- the former only matters for the not-blocking P3 follow-up, the latter's additive change is
  already shipped and verified) to stay within the 6-entry cap.
- **context-scout 2026-08-07 (batch11 independent re-verify)**: all 6 entries confirmed resolving on disk; content
  unchanged.
- **round5-cefi-question-resolution 2026-08-08**: line-168 `[OPERATOR]` deploy-confirmation item flipped `[x]` —
  live-checked `gcloud artifacts docker images list` shows `deployment-api` rebuilt `2026-08-08T07:23:26` (well after
  this doc's `2026-08-06T10:53:59+01:00` fix commit), and `gcloud run jobs describe uts-prod-dp-exit-code-monitor`
  confirms it runs `deployment-api:latest`. This was never a genuine operator-only decision — `deployment-api` rebuilds
  on a routine multi-times-daily cadence independent of manual triggering.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — never re-litigated (established
  ruling). The remaining line-181 `[SCRIPT]` P2 TOCTOU-race item is still ALREADY claimed by
  `cefi_satellite_ao_dispatch_batch9_2026_08_07.md` todo 2 (confirmed re-checked in that batch's own text, "unclaimed by
  any other" caveat notwithstanding — this doc IS the claim it's checking against); reclassifying here would create a
  duplicate-dispatch surface. Independently re-confirmed by `cefi_satellite_ao_dispatch_batch10_2026_08_08.md`'s
  "Deferred — operator-gated" section (drafted/activated the same day, a separate `/ag-closeout-audit` run), which lists
  this exact doc and reaches the identical conclusion ("item 2 is already covered by an active in-flight batch9 todo").
  Line-187 `[SCRIPT]` P3 item remains explicitly time-gated/opportunistic, not blocking. Doc stays NA; the 2026-08-07
  conflict citation and this run's independent reaffirmation both hold.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — root-cause fix (is_spot veto) shipped
  and live-confirmed. TOCTOU singleton-lock item (line 182) is correctly cited as claimed by
  cefi_satellite_ao_dispatch_batch9_2026_08_07.md todo 2 — verified that todo is still `- [ ]` open as of this run (fix
  not yet shipped), so this doc's checkbox correctly stays open per its own 'flip both together' instruction. Not yet
  ready to close.
- **2026-08-09 (batch9 todo 2 pickup, slot 27)**: this "fix not yet shipped" premise (repeated across 4 prior
  na-eligibility-audit passes) was WRONG — `deployment-service@4c28ca640f` had already shipped the atomic-GCS
  singleton-lock fix on 2026-08-06, the same day this doc was filed and a full day before batch9 was even drafted. Every
  prior audit checked "is an active plan claiming this line" without checking whether the claiming plan's underlying
  code had already landed. Re-verified live: `lc_acquire_singleton_lock` gates the RUNNING-VM check in
  `launch-cefi-forward-poll.sh`; 6 regression tests in `TestAcquireSingletonLock`
  (`tests/unit/test_vm_launcher_scripts.py`), including a 12-process concurrent-race test proving exactly 1 of 12
  simultaneous racers wins — all 11 tests re-run green. Flipped this checkbox + batch9 todo 2 together in the same
  commit, citing the pre-existing commit. No new deployment-service code shipped by this pass — closing a stale
  paperwork gap only.
