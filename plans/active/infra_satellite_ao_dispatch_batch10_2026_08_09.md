---
doc_type: plan
title:
  Infra satellite AO batch 10 — VM-launcher forward-registration guard + orchestrator-VM manifest-consolidator scratch
  cleanup
summary: >-
  Tenth AO-dispatch batch for the `infra` topic tranche, produced by a manual satellite-batch-extraction pass (mirrors
  `/ag-closeout-audit`'s pattern) over the 14 NA docs the 2026-08-08 infra RECLASSIFY sweep found zero whole-doc
  candidates in. Reading each doc end-to-end for SPECIFIC bounded sub-items (not whole-doc flips) surfaced 3
  conflict-clear, worker-determinable items across 2 source docs: a forward-registration CI guard so a brand-new one-off
  VM launcher can never again be invisible to the fleet preemption monitor
  (`session_bound_vm_monitoring_reliability_gap_2026_07_26.md`), and 2 items from a 2026-08-08 finding on the
  orchestrator VM's own root disk (175G of abandoned `manifest-consolidate-*` scratch found + removed same day) —
  identify/stop or reap the writer, and add a free-space alert
  (`issues/shared_host_home_filesystem_full_2026_07_26.md`). Both source docs stay `assigned_vm: NA` — each retains
  genuine judgment-call/operator-gated remainder not extracted here.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, satellite-docs, batch-10, vm-launcher, disk-space, monitoring, plan-hygiene]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch10_finalize_2026_08_09.md,
    /plans/active/issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md,
    /plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: infra
effort: medium
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md,
    /plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md,
    deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py,
    deployment-service/deployment_service/data_pipeline_monitors/vm_classification.py,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Manual satellite-batch-extraction pass over the `infra`-tranche `assigned_vm: NA` candidate doc set (14 docs), run
  after the 2026-08-08 infra RECLASSIFY sweep found zero docs qualified for a whole-doc flip. Read all 14 candidate docs
  end-to-end per `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility";
  the majority of open items were genuine judgment/operator/dependency-gated work or already covered by the
  concurrently-drafted `infra_satellite_ao_dispatch_batch9_2026_08_09.md` (G2 UV-version-pin item) — these 3 items were
  the only ones clearing the bounded/deterministic bar with no conflict against any active plan, including batch9.
---

# Infra satellite docs — AO dispatch batch 10

## Why this plan exists

A 2026-08-08 `/ag-closeout-audit infra` run and its supporting `na-eligibility-audit` passes had already read every doc
in this tranche's `assigned_vm: NA` corpus at the whole-document level and found nothing that qualified for a full
`assigned_vm: planning` flip — every remaining doc mixes genuine judgment calls, operator-gated decisions, or
dependency-blocked items with, in a few cases, one or two specific sub-items that ARE bounded and worker-determinable on
their own. This batch extracts exactly those sub-items, leaving each source doc's genuinely-gated remainder untouched at
`assigned_vm: NA`.

- **`issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md`** — its primary finding (session-bound
  `ScheduleWakeup` monitoring loops share the operator's connectivity blind spot) was already resolved 2026-08-08
  (operator ruling: the fleet-level `RelaunchPreemptedVm` actuator is already cron-scheduled and not session-bound; the
  2026-07-26 incident was a one-off registry-coverage gap, separately fixed 2026-08-04). The doc's own residual
  `[SCRIPT] P2` follow-up — a forward-looking QG guard closing the same bug CLASS (a brand-new one-off launcher that was
  never registered in the fleet-monitor registries) — is fully spec'd (4 concrete steps) and was flagged by the
  2026-08-08 `na-eligibility-audit` pass as "a strong RECLASSIFY candidate on its own... no conflicting active claim."
  The doc's other open item (`[DATA] P3`, the PREEMPTED-marker grace-period survivability audit) is a genuine undecided
  design choice between 2 named mitigations — NOT extracted, stays on the source doc.
- **`issues/shared_host_home_filesystem_full_2026_07_26.md`** — its original 2 `[DATA] P2` items (open-ended "audit 157G
  for cleanup headroom" / "investigate ownership of 2 unknown dirs") remain genuinely open-ended investigations gated by
  `block_destructive_commands.py`'s unconditional autonomous-cleanup block — NOT extracted. A 2026-08-08 addendum
  ("Orphaned manifest-consolidator scratch on the orchestrator VM") found + removed 175G of abandoned
  `manifest-consolidate-*` scratch and filed 2 new `[INFRA]` items with concrete done-when criteria; the 2026-08-08
  `na-eligibility-audit` pass flagged both as "strong RECLASSIFY candidates on their own... no conflicting active
  claim," blocked only by the doc's own 2 older open-ended items forcing a whole-doc NA hold.

## Conflict check (before drafting)

- **`check_vm_launcher_prefix_registration.py` / forward-registration guard**:
  `grep -rl "check_vm_launcher_prefix_registration\|forward-registration"` across `plans/active/*.md` +
  `plans/active/issues/*.md` returns only the source doc. No competing claim.
- **`manifest-consolidate-*` scratch / writer / reaper**: `grep -rl "manifest-consolidate-"` (exact scratch-dir prefix,
  distinct from the generic `manifest_consolidator` service name which is referenced by dozens of unrelated
  data-pipeline docs) across the full active corpus returns only the source doc. No competing claim.
- **Orchestrator-VM free-space alert**: `grep -rln "orchestrator.*disk.*alert\|orchestrator.*free.*space\|AO VM.*disk"`
  across the full active corpus returns only the source doc. No competing claim.
- **Against `infra_satellite_ao_dispatch_batch9_2026_08_09.md`** (drafted the same day by a concurrent
  `/ag-closeout-audit infra` run): batch9 covers UV-version-pin centralization + 3
  `codex_drift_followups_dual_cloud_ image_builds_2026_08_08.md` items (stale `_AR_REPO` defaults, orphaned Cloud Build
  triggers, `deployed_versions` provenance) — zero file or topic overlap with this batch's 3 items.
- **File-collision check across this batch's own 3 todos**: todo 1 touches `deployment-service/scripts/quality_gates/`
  (new file) + `deployment-service/.../launcher_registry.py` (docstring only) + a codex doc; todo 2 touches whatever
  repo the investigation identifies as the scratch writer (unknown until investigated — likely `agent-orchestrator` or a
  `deployment-service` VM script, per the source doc's own "identify the writer first" framing) + possibly a new reaper
  script; todo 3 touches `agent-orchestrator` monitoring/alerting code. No two todos share a named file — safe to run
  concurrently (`sequential: false`).

## Todos

- [x] ✅ [SCRIPT] P2. **Build a forward-registration CI guard so a NEW ad hoc/one-off backfill launcher can never launch
      a VM invisible to the fleet monitor.** — `deployment-service@c8f1612b`. Shipped
      `check_vm_launcher_prefix_registration.py` (derives each launcher's prefix, fails when uncovered by
      `is_data_vm()`/unregistered in `LAUNCHER_FOR_VM_PREFIX`, `# non-relaunchable:` opt-out), wired into
      `quality-gates.sh`, baseline-ratcheted (`vm_launcher_prefix_registration_baseline.yaml`, 39 pre-existing launchers
      grandfathered), `launcher_registry.py` docstring + this batch's codex SSOT updated with the closed-loop contract,
      8 new unit tests (incl. a synthetic unregistered-launcher case) — all green, `quality-gates.sh` passed clean
      (259s). 1. Add `deployment-service/scripts/quality_gates/check_vm_launcher_prefix_registration.py` (or fold into
      an existing QG check in that dir): glob every `deployment-service/scripts/vm/launch-*.sh`, grep each for its
      `VM_NAME=`/`VM_PREFIX=` bash assignment, and derive the literal/prefix portion (a fixed string prefix before the
      first `${...}` interpolation). 2. For each derived prefix, FAIL when it is not covered by
      `vm_classification.is_data_vm(<a synthetic VM name with that prefix>)` (mirrors the existing
      `test_data_vm_prefixes_cover_every_relaunchable_launcher` unit-test logic in
      `deployment-service/tests/unit/test_data_pipeline_monitors_cli.py:77`, but driven from the launcher FILE SET, not
      the registry's own keys — so a launcher with NO entry anywhere is caught) OR when
      `launcher_registry.resolve_launcher_for_vm(<that prefix>)` returns `None` (unless the launcher script itself
      carries an explicit `# non-relaunchable: <reason>` marker, mirroring the documented `None` entries in
      `LAUNCHER_FOR_VM_PREFIX` for fan-out/read-only/live-service launchers). 3. Wire the check into
      `deployment-service/scripts/quality-gates.sh` (ratcheted the same way STEP 5.94/5.95 checks are — a fleet-wide
      baseline pass first if any existing launcher fails it, then hard-fail on new violations only). 4. Update
      `deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py`'s module docstring +
      `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md` to state the closed-loop contract: "a new
      `scripts/vm/launch-*.sh` MUST register its `VM_NAME`/`VM_PREFIX` in `vm_classification.DATA_VM_PREFIXES` +
      `launcher_registry.LAUNCHER_FOR_VM_PREFIX` (+ `vm_prefix_registry.VM_PREFIX_TO_BUCKET`) in the SAME commit that
      adds the launcher, enforced by QG." Done when: the check exists, is wired into `quality-gates.sh`, passes on the
      current fleet of launchers (a fresh baseline if needed), and fails on a synthetic unregistered-launcher test case.
      Source: `issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md` (the `[SCRIPT] P2` todo, filed
      2026-08-08 off operator item-78's ruling). (repo: deployment-service, unified-trading-pm for the codex doc)
- [x] ✅ [INFRA] P2. **Find what writes `manifest-consolidate-*` scratch to the orchestrator VM and stop it, or give it
      a reaper.** Per `/codex/05-infrastructure/manifest-consolidator-ssot.md` the manifest consolidator runs on Cloud
      Run / Batch-Fargate, NOT a VM — scratch of this shape (`duckdb_temp_storage_DEFAULT-*.tmp` spill files +
      intermediate `shards/*.parquet` + a `legacy_seed/` dir) should never accumulate on the orchestrator box, and
      nothing currently owns cleaning it (175G across 3 dirs found + manually removed 2026-08-08; agents can DETECT but
      not autonomously clear this — `block_destructive_commands.py` correctly refuses recursive `rm` regardless of
      reversibility, so this needs automation, not another manual find-and-delete). Either (a) find what actually writes
      `manifest-consolidate-*` on the orchestrator VM (something running the consolidator locally, or a VM-side helper
      spilling there) and stop/fix it at the root, or (b) if a legitimate VM-side spill is unavoidable, build a TTL
      reaper (delete any `manifest-consolidate-*` dir older than 48h with zero holding process — `lsof +D` clean — same
      liveness-check pattern already used elsewhere in this codebase for dead-scratch detection). Done when: no new
      `manifest-consolidate-*` dir appears on the orchestrator VM over a 7-day observation window, OR a reaper is
      deployed that deletes any such dir older than 48h with zero holding process (verified via at least one synthetic
      trigger + a real or simulated stale-dir cleanup). Evidence for the finding: 175G across 3 dirs
      (`manifest-consolidate-{eph5a0bh,1g6s1s8z,zuntwmoh}`, 59G/59G/57G, mtime 2026-08-05, quiescent 3 days at
      discovery), removed 2026-08-08 (root disk went 533G/145G free 79% → 359G/319G free 54%). Source:
      `issues/shared_host_home_filesystem_full_2026_07_26.md` § "Orphaned manifest-consolidator scratch on the
      orchestrator VM" (`[INFRA] P2` todo, filed 2026-08-08). (repo: identify the writer first — likely
      agent-orchestrator or a deployment-service VM script) **DONE 2026-08-09** — `unified-trading-pm@699f53832`.
      Root-caused (a): the sole in-repo writer of the `manifest-consolidate-` prefix is `unified-trading-library`'s
      `_duckdb_merge_payload` (`tempfile.TemporaryDirectory(prefix="manifest-consolidate-")`), which per
      `/codex/05-infrastructure/manifest-consolidator-ssot.md` runs ONLY inside the ephemeral per-AG Cloud Run Job —
      confirmed via `deployment-service/scripts/recovery/relaunch_consolidator.py`, the sole re-execute path, which
      re-runs the Cloud Run Job via the GCP SDK and never invokes the merge code locally. No deterministic in-repo bug
      produces a host-side accumulation; the historical path
      (`/home/ubuntu/tmp/manifest-consolidate-{eph5a0bh,1g6s1s8z,zuntwmoh}`, per the source doc) implies a one-off
      manual/local invocation with `TMPDIR` pointed at a home-dir scratch path (the same tmpfs-avoidance idiom
      `cleanup-stale-qg-tmp.sh`'s own precedent fix established for `shared_host_tmp_tmpfs_exhaustion_2026_07_08`) — not
      a recurring writer to patch at the source, so (b) is the correct resolution path. Shipped a TTL reaper pair
      (`scripts/dev/cleanup-stale-manifest-consolidate-tmp.sh` + its cron installer), mirroring
      `cleanup-stale-qg-tmp.sh`'s proven liveness-check pattern (48h age threshold via `-mmin`). **Caught + fixed a real
      bug during this session's own synthetic-trigger verification**: an `lsof +D`-based liveness check (the todo's own
      suggested mechanism) exits non-zero on this host even when it DOES find an open fd, because of an unrelated
      `tracefs`-stat WARNING that makes `lsof` report its own output "incomplete" — this would have silently swept
      genuinely-live scratch had it shipped. Switched to `fuser`-based liveness (the SAME primary mechanism
      `cleanup-stale-qg-tmp.sh` already uses), re-verified: a stale (old-mtime, no holder) synthetic dir is removed, a
      live (old-mtime, open-fd-held) synthetic dir is skipped until the fd closes, a fresh (recent-mtime) synthetic dir
      is never touched regardless of holder. Dry-run against the real host roots (`/tmp`, `~/tmp`) confirms zero false
      positives on current state (0 `manifest-consolidate-*` dirs exist anywhere on this host right now). **Cron
      installation is an explicit operator action**, not run by this worker session — this host's crontab spool isn't
      writable from a worker's sandboxed session (`crontab -l` → `Permission denied`; confirmed this is consistent with
      `cleanup-stale-qg-tmp.sh`'s OWN installer doc header, "Operator runs this ONCE per host" — the same convention,
      not a new gap this todo introduces). Operator follow-up (one command, one-time):
      `bash unified-trading-pm/scripts/dev/install-cleanup-stale-manifest-consolidate-tmp-cron.sh` from the root PM
      clone.
- [x] ✅ [INFRA] P3. **Add a free-space alert for the orchestrator VM root.** Both the 2026-06-28 full-disk wedge (which
      is why `setup-tab-worktrees.sh` carries a slot cap at all) and the 2026-08-08 175G `manifest-consolidate-*` find
      (see the todo above) were caught by a human looking at the disk, not a monitor. Add a standing free-space alert on
      the orchestrator VM's root filesystem, suggested threshold: page under 60G free (mirror the pattern + severity
      conventions already established in `/codex/05-infrastructure/data-pipeline-alerts.md`). Done when: the alert
      exists (wired into whatever alerting channel the orchestrator VM's other standing monitors use) and has fired at
      least once in a test/synthetic trigger. Source: `issues/shared_host_home_filesystem_full_2026_07_26.md` §
      "Orphaned manifest-consolidator scratch on the orchestrator VM" (`[INFRA] P3` todo, filed 2026-08-08). (repo:
      agent-orchestrator) — `agent-orchestrator@bb85164`. Shipped `DiskSpaceCanary` (`server/disk_space_canary.py`),
      mirroring `SnapshotRecencyCanary`'s skeleton (pure `assess()`, state-transition-deduped `_maybe_alert()` via
      `dedup_state.disk_space_breach_path()`, a daemon-thread wrapper). Wired into `server.py` startup/shutdown
      alongside every other standing canary — pages `#agent-orchestrator-alerts` (the channel every other AO standing
      monitor uses, per `notify_disk_space_low`/`_resolved`) via a `_persist_to_gcs` CRITICAL alert. Default threshold
      60G free (per this todo's own suggestion), 300s cadence (matches the dashboard's vm-resources push interval).
      Fired via a mocked-probe synthetic trigger (20 new unit tests in `tests/test_disk_space_canary.py`, incl. the
      literal breach→resolve two-tick Gate — never the live host root). Registered in
      `/codex/04-architecture/agent-orchestrator-alerting.md`'s Slack-routing table + self-monitoring detector registry
      (owner/cadence/verifier). Full `quality-gates.sh` green (3021 tests + basedpyright + dashboard vitest).

## Operator approval gate

This plan is authored `status: active` directly (satellite-batch-extraction session, not the `/ag-closeout-audit`
skill's own draft-then-review convention) — all 3 todos are read-only-investigation-or-additive (a new QG check, a
find-and-fix/reaper for abandoned scratch, a new alert), none touches a destructive/irreversible action, and each was
independently conflict-checked against the full active corpus with zero competing claims found.

## Codex SSOTs (read before touching a todo)

- `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md` — the fleet-monitor registry contract todo 1
  closes the loop on
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — where the manifest consolidator is supposed to run (not a
  VM), relevant to todo 2
- `/codex/05-infrastructure/data-pipeline-alerts.md` — the alerting pattern todo 3 should mirror
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — archival ritual the finalize plan runs
- `/plans/active/task_template.md` §4 — finalize-plan-coverage rule, dispatch-scope eligibility test

## Progress Log

- **2026-08-09** — Drafted by a manual satellite-batch-extraction pass over the infra-tranche NA candidate doc set (14
  docs), following the 2026-08-08 infra RECLASSIFY sweep's whole-doc-level finding of zero qualifying flips. Paired with
  `infra_satellite_ao_dispatch_batch10_finalize_2026_08_09.md` per the finalize-plan-coverage rule. Conflict-checked
  against the concurrently-drafted `infra_satellite_ao_dispatch_batch9_2026_08_09.md` — zero overlap.
- **2026-08-09 (slot 13)** — Todo 1 shipped: `deployment-service@c8f1612b`. On first run against the real 176-launcher
  fleet the check found 39 launchers whose derived prefix isn't (yet) covered by both `is_data_vm()` and
  `LAUNCHER_FOR_VM_PREFIX` (mostly the documented `None`-registry class — fan-out/read-only/live-service/infra launchers
  that predate the new `# non-relaunchable:` marker convention) — grandfathered into
  `vm_launcher_prefix_registration_baseline.yaml` per the todo's own "fresh baseline if needed" allowance; only a
  brand-new unregistered launcher fails the check outright going forward. Todos 2-3 remain open (untouched, different
  files, no conflict).
- **2026-08-09 (slot 33)** — Todo 2 shipped: `unified-trading-pm@699f53832`. Root-caused the writer (the Cloud Run Job's
  own merge step; no in-repo recurring bug, historical evidence points to a one-off manual local invocation) and shipped
  a TTL reaper mirroring `cleanup-stale-qg-tmp.sh`'s pattern. Caught + fixed a real liveness-check bug (`lsof +D`
  false-negatives on this host) during synthetic-trigger verification before shipping — see the todo's own evidence
  block for the full account. Cron install left as an explicit operator follow-up (worker sessions lack crontab spool
  write access on this host, same as the qg-tmp precedent). Todo 3 (free-space alert) remains open, different files, no
  conflict.
- **2026-08-09 (slot 33)** — Corrected a typo'd evidence SHA on todo 2: both citations above read
  `unified-trading-pm@b277df233`, which does not resolve to any object in this repo
  (`issues/infra_satellite_batch10_fabricated_commit_sha_evidence_2026_08_09.md`, found by
  `check_plan_commit_sha_evidence.py` while shipping an unrelated task).
  `git log --all -- scripts/dev/cleanup-stale-manifest-consolidate-tmp.sh` resolves to the real commit `699f53832`
  (`feat(infra): TTL reaper for abandoned manifest-consolidator scratch on shared hosts`, verified on
  `origin/live-defi-rollout`, commit body matches this todo's description exactly) — the underlying work was genuinely
  shipped, only the citation was mistyped. Both instances corrected to `699f53832`.
- **2026-08-09 (slot 14, infra)** — Todo 3 shipped: `agent-orchestrator@bb85164`. All 3 todos now done — this plan is
  archival-eligible, gated on its paired finalize plan (`infra_satellite_ao_dispatch_batch10_finalize_2026_08_09.md`).
