---
doc_type: issue
title: Long-lived orchestrator VM logs are not backed up off-box (GCP + AWS) — lost on termination
summary:
  '**Finding 2026-07-02:** the durable-log streamer shipped by `vm_launcher_durable_log_observability_2026_06_19` covers
  batch/backfill VMs (run.log→GCS/S3 every 30s + EXIT_STATUS). Long-lived orchestrator VMs (planning / epic /
  central-brain / orchestrator-worker, GCP AND AWS) only `tee` a cold-boot bootstrap log to VM-local
  `/var/log/*-bootstrap.log`, ship no log content off-box, and run no logging agent — so their logs die with the VM.
  They were EXEMPTED from the coverage guard on a misleading "systemd/container logging" rationale (no agent is
  installed; journald is VM-local too).'
status: resolved
nature: process
asset_group: [ao]
stage: [meta]
repos: [deployment-service, agent-orchestrator]
scope: [engineer, admin]
tags: [vm, logging, observability, gcs, s3, long-lived, orchestrator]
related: [vm_launcher_durable_log_observability_2026_06_19]
created: "2026-07-02"
author: unknown
parent_epic: infrastructure_master
priority: P2
source:
  [
    "vm_launcher_durable_log_observability_2026_06_19 remaining-items review 2026-07-02",
    "deployment-service/scripts/vm launcher audit",
    "coverage-guard EXEMPT whitelist inspection tests/unit/test_vm_launcher_scripts.py:661",
  ]
assigned_vm: planning
resolved_by:
  deployment-service (all 3 build todos shipped; see cebb2425/a2f5ee2a in Todos, and the 2026-08-06 reclassify +
  2026-08-12 archive_exempt bridge in Progress Log)
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/vm_launcher_durable_log_observability_2026_06_19.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/scripts/vm/lib/aws_ec2_launch_lib.sh,
    deployment-service/tests/unit/test_vm_launcher_scripts.py,
    deployment-service/scripts/vm/launch-planning-vm.sh,
  ]
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-02
---

> **🟢 ARCHIVED 2026-08-14 — RESOLVED (all 3 build todos `[x]`, unlocked).** Reclassified `assigned_vm: NA → planning`
> 2026-08-06 and all 3 todos shipped (`deployment-service@cebb2425`, `@a2f5ee2a`) since — the 2026-07-02 "not needed
> right now" decision text describes the pre-2026-08-06 state, not a current blocker. `archive_exempt: true` (a
> 2026-08-12 bridge for the `locked_by:live-defi-rollout` placeholder cleanup) un-set per this doc's own instruction:
> "drop this line + git mv ... in that follow-on pass" — this is that pass, run as part of applying the
> `ao_orphan_audit_followup_triage_2026_07_30.md` disposition sweep.

## What I found

The `vm_launcher_durable_log_observability_2026_06_19` plan closed the batch/backfill freeze-and-lose incident, but a
review of its remaining items (2026-07-02) surfaced a distinct, still-open gap for **long-lived VMs**. Three tiers:

- **Tier 1 — batch/backfill VMs → fully backed up.** `run.log` streamed to GCS/S3 every 30 s + `EXIT_STATUS` +
  log-archive, via `lc_log_upload_trap_block` / `lc_aws_log_upload_trap_block` / `vm-exec-with-gcs-tee.sh`. Survives
  termination.
- **Tier 2 — live consolidated MTDS VMs (cefi/prediction) → partial.** `setup-cefi-live-consolidated-vm.sh:48` uploads
  `vm-setup.log` to `vm-logs/<vm>/` **only on the exit trap**; per-shard runtime `live-*.log` stay VM-local. Heartbeat
  sidecar is liveness-only.
- **Tier 3 — long-lived orchestrator VMs → NOT backed up.** `launch-planning-vm.sh`, `launch-central-brain-aws.sh`,
  `launch-orchestrator-worker-vm.sh` do only `exec > >(tee /var/log/<name>-bootstrap.log) 2>&1` (VM-local). No GCS/S3
  upload of that log; `agent-orchestrator` ships no runtime logs off-box; **no logging agent is installed anywhere**
  (`ops-agent` / `google-fluentd` / `amazon-cloudwatch-agent` grep = 0). They emit only a one-shot `STARTED` event + a
  60 s heartbeat blob (`vm-heartbeat/<vm>.txt` = `<epoch>\n<rc>\n<status>`, per
  `deployment_service/data_pipeline_monitors/_gcs.py:148`). To read them you must SSH in; on termination they are gone —
  the same incident class the parent plan was created to close, for a different VM set.

### The misleading exemption

Tier 3 launchers are whitelisted in the coverage guard
(`deployment-service/tests/unit/test_vm_launcher_scripts.py:661-687`) with reasons like _"no batch run-log lifecycle"_ /
_"systemd/container logging."_ That conflates _"doesn't need EXIT_STATUS"_ with _"doesn't need durable logs."_ A
long-lived VM accumulates more history before it dies, so it arguably needs off-box logs **more**. The guard exemption
should be corrected to reflect that these are deferred-not-exempt (or the gap closed).

(Possible partial exception: `launch-dashboard-vm.sh` is a container VM — if on COS, Docker stdout auto-ships to Cloud
Logging. The orchestrator VMs are plain Ubuntu `apt-get`, so no auto-logging.)

## Proposed fix (deferred per operator 2026-07-02 — not scheduled)

Add a lightweight **continuous log-tail shipper** for Tier 3: a `nohup` loop that `gcloud storage cp` / `aws s3 cp` the
bootstrap log + the orchestrator's own log dir to `vm-logs/<vm>/` every N seconds — same GCS/S3 contract as Tier 1,
minus the EXIT_STATUS/shutdown semantics (these VMs don't self-terminate). Small addition to
`scripts/vm/lib/launcher_common.sh` + `scripts/vm/lib/aws_ec2_launch_lib.sh`. When done, correct the coverage-guard
EXEMPT reasons accordingly.

- [x] ✅ [SCRIPT] P2. Add a continuous (non-terminating) log-tail→GCS shipper helper to `launcher_common.sh`; wire into
      `launch-planning-vm.sh`. — deployment-service@52234197 (lc_log_upload_continuous_block added;
      launch-planning-vm.sh sourced + wired; coverage guard EXEMPT entry removed, lc_log_upload_continuous_block added
      to STREAMER_TOKENS)
- [x] ✅ [SCRIPT] P2. AWS mirror in `aws_ec2_launch_lib.sh`; wire into `launch-central-brain-aws.sh`,
      `launch-orchestrator-worker-vm.sh`. (Was also `launch-epic-vm-aws.sh` — REMOVED 2026-07-24 with the rest of the
      per-epic-VM code; `launch-central-brain-aws.sh` is the sole surviving central/planning launcher.) —
      deployment-service@cebb2425 (lc_aws_log_upload_continuous_block added to aws_ec2_launch_lib.sh;
      launch-central-brain-aws.sh + launch-orchestrator-worker-vm.sh wired; launch-orchestrator-worker-vm.sh removed
      from EXEMPT, lc_aws_log_upload_continuous_block added to STREAMER_TOKENS)
- [x] ✅ [SCRIPT] P3. Once shipped, replace the misleading Tier-3 EXEMPT reasons in `test_vm_launcher_scripts.py`
      (durable-log coverage guard) with the streamer wiring, or a correct "long-lived continuous-tail (not EXIT_STATUS)"
      rationale. — deployment-service@a2f5ee2a (mechanism 5 documented in class docstring; EXEMPT comment reframed to
      require a durable-log path OUTSIDE the streamers; launch-dashboard-vm.sh given honest COS-auto-logging rationale;
      Tier-3 launchers already covered by STREAMER_TOKENS guard — verified 0 guard offenders at origin HEAD)

> **Decision (operator, 2026-07-02):** not needed right now. Captured here so the parent plan can archive without losing
> the finding. Revive by scheduling these todos.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — carries an explicit dated operator decision ('**Decision
  (operator, 2026-07-02):** not needed right now. … Revive by scheduling these todos') and is additionally
  `locked_by: live-defi-rollout`, which blocks autonomous archival/reclassification without an `[unlock-plan]`. Same
  ruling in `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s operator-decision Deferred list.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — reviewed against current doc content, list still
  accurate (unchanged).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **2026-08-06 (`/plan-reconcile ao`, operator ruling, interactive)**: **RECLASSIFIED `assigned_vm: NA` → `planning`**
  (+ `assigned_role: infra` added, which was absent). This doc sat in the "12 operator-gated docs" bucket of
  `/plans/archive/issues/ao_orphan_audit_followup_triage_2026_07_30.md`, whose todo describes all 12 as "a genuine
  design/judgment fork with no evidence-based tiebreaker". That description does not fit this doc: its three open todos
  are bounded implementation work naming concrete files (`launcher_common.sh`, `aws_ec2_launch_lib.sh`,
  `test_vm_launcher_scripts.py`), each with a stated done-when and no undecided design call — which meets the
  dispatch-eligibility bar in `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope
  eligibility". Corroborating internal evidence: the frontmatter already read `execution_scope: orchestrator-agent`
  while `assigned_vm` said `NA` — a self-contradiction consistent with the doc having inherited the operator-gated label
  from the _sweep that discovered it_ rather than from its own content.

  **⚠️ This SUPERSEDES the `na-eligibility-audit 2026-08-06` verdict immediately above**, which recorded "KEEP-NA, valid
  — … Operator-gated, design-judgment, or standing-corpus-ruling work remains open." That verdict is a prior-verdict
  re-verification ("content unchanged since last marker"), i.e. it inherited the original NA classification rather than
  re-deriving it from the todos — which is exactly how a mis-tag survives repeated audits. An explicit operator ruling
  outranks an automated audit verdict. **A future `/na-eligibility-audit` pass must NOT flip this back to NA on the
  strength of the older marker**; if it disagrees, it needs a fresh operator ruling, not a re-application of the
  superseded one.

- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).

- **2026-08-11 (slot-31 worker, task `long_lived_vm_logs_not_backed_up-003`)**: P3 completed. The code change was
  already shipped by `deployment-service@a2f5ee2a` (slot-19, 2026-08-11) but the checkbox had not been flipped. Verified
  at origin HEAD: (1) mechanism 5 (`lc_log_upload_continuous_block` / `lc_aws_log_upload_continuous_block`) documented
  in the `TestDurableLogStreamerCoverage` class docstring; (2) EXEMPT comment reframed to require a durable-log path
  OUTSIDE the streamers; (3) `launch-dashboard-vm.sh`'s misleading "container logging, no startup-script run.log" reason
  replaced with the honest COS-auto-logging (Docker stdout → Cloud Logging) rationale; (4) Tier-3 launchers
  (`launch-planning-vm.sh`, `launch-central-brain-aws.sh`, `launch-orchestrator-worker-vm.sh`) are covered by the
  STREAMER_TOKENS guard (wired continuous-tail streamers), no longer EXEMPT. Guard logic re-verified locally: 0
  offenders across all 174 GCP launchers. Flipped checkbox with evidence.
- **2026-08-12** — `locked_by`/`locked_since` cleared (corpus-wide fix, operator ruling Option B, interactive session
  2026-08-12; see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md). This doc has
  0 open todos, so clearing the placeholder lock immediately makes it archive-eligible. Per the ruling's explicit scope
  ("do NOT auto-archive in this same pass"), archival itself is deferred to a separate follow-on pass; bridged with
  `archive_exempt: true` (the sanctioned flip-then-mv two-commit pattern documented in
  `scripts/plan-hygiene/check_archive_candidates.sh`) so this commit doesn't trip the archive-candidates pre-commit
  gate. The follow-on pass should drop `archive_exempt` and `git mv` this doc to `plans/archive/[issues/]`.
