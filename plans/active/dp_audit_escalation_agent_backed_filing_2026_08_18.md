---
doc_type: plan
title: Data-pipeline audit escalation — agent-backed issue filing, replacing the raw Cloud Run commit path
summary: |
  The e2e-testing manifest-hygiene audit files RED findings by writing + `git commit`/`push`-ing a PM issue doc
  directly from inside an ephemeral Cloud Run Job — no quality gates, no safe-doc-push, no agent. That path has
  already silently dropped genuine RED findings 3 separate times in one week (git identity, frontmatter drift, same-
  day filename collision — see the archived incident doc). deployment-service's own data-pipeline self-monitoring
  substrate already solved this correctly (never raw-commit from an ephemeral runner — defer to a dispatched agent
  instead) but its dispatched worker's boot prompt assumes a doc is already filed, so the pattern isn't actually
  wired end-to-end anywhere. This plan closes that loop.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos: [agent-orchestrator, e2e-testing, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [data-pipeline, escalation, dp-audit, issue-filing, self-healing, agent-orchestrator, reliability]
related:
  [
    /plans/archive/issues/dp_audit_sibling_repo_cli_paths_and_escalation_commit_identity_2026_08_16.md,
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /codex/04-architecture/agent-orchestrator-ci-escalation-wall-types.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-18"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
effort: high
drift_direction: advance-code
supersedes:
superseded_by:
depends_on: []
source:
  [
    "Interactive session 2026-08-18, slot 3 — operator asked whether the deployment pipeline's escalation process
    adheres to safe-doc-push/quality-gates when filing issue docs; investigation found it doesn't for the e2e-testing
    manifest-hygiene audit specifically, traced the 3 documented silent-drop incidents, found deployment-service
    already has the correct 'defer to a dispatched agent, never raw-commit from an ephemeral runner' shape but its
    boot prompt doesn't close the loop, and the operator ruled 'always defer' (never a local-commit fast path) +
    human plan (assigned_vm: NA) via interactive Q&A.",
  ]
locked_by:
locked_since:
context_scope:
  [
    unified-trading-pm/agents/data_pipeline_failure.md,
    e2e-testing/scripts/audit/_dp_common.py,
    deployment-service/deployment_service/data_pipeline_monitors/escalation.py,
    deployment-service/deployment_service/data_pipeline_monitors/escalation_issue_writer.py,
    agent-orchestrator/server/escalation.py,
    /codex/11-project-management/doc-frontmatter-schema.md,
    scripts/docs/docspec.py,
  ]
---

# Data-pipeline audit escalation — agent-backed issue filing

## Why this doc exists

The e2e-testing manifest-hygiene audit (`uts-prod-dp-manifest-hygiene-{changed,full}`, a daily/weekly Cloud Run Job)
files a genuine RED finding by having `_dp_common.py::file_escalation_issue` write a
`plans/active/issues/<slug>_<date>.md` doc directly to disk, then commit + push it via raw subprocess `git`, from
inside the ephemeral job container — never touching `scripts/dev/safe-doc-push.sh` or `quality-gates.sh`, never
dispatching an agent. This has already **silently dropped a real RED finding three separate times in one week**
(documented in full in
`/plans/archive/issues/dp_audit_sibling_repo_cli_paths_and_escalation_commit_identity_2026_08_16.md`):

1. 2026-08-16 — no git identity in the container → `commit` failed → the doc was lost when the ephemeral container
   exited.
2. 2026-08-16/17 — the generated frontmatter had drifted from `doc-frontmatter-schema.md` → every auto-filed doc was
   failing `plan-hygiene`'s schema check.
3. 2026-08-17 — same-day `-changed` and `-full` runs wrote the identical filename → an `add/add` git conflict on the
   second commit silently dropped that run's findings.

All three were fixed by hardening the raw script in place — not by changing the underlying architecture, so the
failure *class* (an unsupervised subprocess deciding, alone, whether a finding survives) is still live.

**deployment-service already solved this correctly, for a different finding source.** Its own data-pipeline
self-monitoring substrate (`deployment_service/data_pipeline_monitors/escalation.py::route_finding` +
`escalation_issue_writer.py::write_issue_doc`) never attempts a raw commit from an ephemeral runner: when there's no
durable PM clone on disk, it skips the local write entirely, sets `file_issue_deferred: no_pm_clone_on_disk`, and
fires a best-effort `repository_dispatch` to `escalate-to-orchestrator` (`wall_type=data_pipeline_failure`) so a real
tmux-hosted agent-orchestrator worker picks it up. **But the dispatched worker's own boot prompt
(`unified-trading-pm/agents/data_pipeline_failure.md`) hard-assumes a PM issue doc is already filed** ("STEP 1 — READ
THE FILED ISSUE DOC") — it has no instructions for filing one itself from a candidate payload. So the correct pattern
exists on one side and is never actually exercised end-to-end.

**Operator decisions this session (2026-08-18, interactive Q&A):**

- The e2e-testing audit must **always defer to a dispatched agent** — never keep a local-commit fast path, even as a
  fallback-on-failure. Every RED finding costs a real agent dispatch; that's the accepted tradeoff for "sure, not
  silent."
- This is a **human plan** (`assigned_vm: NA`) — not auto-dispatched by the fleet.

## Todos

- [x] 1. ✅ [BACKEND] P1. Extend `unified-trading-pm/agents/data_pipeline_failure.md`'s boot prompt: when the boot
      `context` carries a DP\_\* finding/candidate payload but no pre-filed issue-doc slug, the worker files the doc
      itself FIRST — frontmatter mirroring e2e-testing's own hand-verified `docspec.py` template — THEN proceeds to
      STEP 1's existing diagnose-from-doc flow unchanged; the "doc already filed" path is untouched. —
      unified-trading-pm@6fca190fb8 (todo 4's live run still owes end-to-end exercise of this exact path).
- [x] 2. ✅ [BACKEND] P1. In `e2e-testing/scripts/audit/_dp_common.py`, deleted `file_escalation_issue`'s raw
      `path.write_text` + `_commit_and_push_pm_artifacts` subprocess `git add`/`commit`/`push` sequence entirely —
      per this session's operator decision, never attempt a local commit from inside the Cloud Run Job. Replaced it
      with: emit a `DP_ESCALATION_DEFERRED` event (via the existing `emit_dp_event` pubsub path) carrying the full
      finding/candidate details in `details`, then fire a `repository_dispatch` to `escalate-to-orchestrator` with
      `wall_type=data_pipeline_failure`, mirroring
      `deployment-service/deployment_service/data_pipeline_monitors/escalation.py::_dispatch_to_orchestrator`'s shape
      (same client_payload structure — repo/pr_number/wall_type/context/authoring_slot/model, same
      GH_PAT-from-Secret-Manager auth pattern). IAM check: confirmed live via `gcloud projects get-iam-policy` that
      the e2e-audit Cloud Run Job's SA (`unified-trading-sa`) already carries a PROJECT-LEVEL
      `roles/secretmanager.secretAccessor` binding (same SA deployment-service's own monitors run under, per both
      repos' terraform `google_service_account.unified_trading.email`) — no new IAM grant was needed. Rewrote
      `tests/unit/test_dp_audit.py`'s issue-filer coverage: a test asserts `file_escalation_issue` no longer
      imports/calls `subprocess`/`git`, and new tests confirm the `repository_dispatch` call fires with the
      finding's full candidate details on a genuine RED verdict + best-effort behavior on no-token/network-error. —
      e2e-testing@aa6e8a1498
- [x] 3. ✅ [BACKEND] P1. Fix
      `deployment-service/deployment_service/data_pipeline_monitors/escalation_issue_writer.py::write_issue_doc`'s
      frontmatter template — it currently emits only `title`/`created`/`author`/`parent_epic`/`assigned_vm`/
      `source`/`locked_by`, missing `doc_type`/`summary`/`status`/`nature`/`asset_group`/`stage`/`repos`/`scope`/
      `tags`/`related`/`priority` that `docspec.py`'s `PER_TYPE["issue"]` requires — the same frontmatter-drift bug
      class already fixed once in e2e-testing's `_dp_common.py` (`e2e-testing@c05ec220ec`). Mirror that fix's field
      derivation. Done-when: a new test parses the generated frontmatter with `yaml.safe_load` and asserts every
      docspec-required field for `doc_type: issue` is present and correctly valued. —
      deployment-service@f2fb7973126a5f59afe7ca943a65a4a162433225 (quality-gates.sh green, 313s; new test file
      `tests/unit/test_escalation_issue_writer.py` covers all universal-core + PER_TYPE["issue"] fields, summary
      truncation, and the asset_group derivation's plain/compound/absent shapes).
- [x] 4. ✅ [REVIEW] P1. End-to-end live verification — confirmed for real. Fired a real `repository_dispatch`
      (escalation `agt-2050ac`, repo `e2e-testing`, `wall_type=data_pipeline_failure`) with a payload explicitly
      labeled as a drill; a genuine dispatched `data_pipeline_failure` worker (slot 16) self-filed a schema-valid
      issue doc from the bare payload alone (todo 1's new STEP-1 path) at `unified-trading-pm@1ea9a7c3ce`, verified
      its own frontmatter against `docspec.py`'s `PER_TYPE["issue"]`, correctly recognized it as a drill (no
      root-cause chase), and resolved+archived it at `unified-trading-pm@8100c10056`. Full chain proven live: audit
      emits event with no local write → dispatch reaches AO → worker spawns → worker self-files → worker closes out
      correctly.
- [x] 5. ✅ [DOC] P2. Added a section to `/codex/05-infrastructure/data-pipeline-alerts.md` (the emit→route→escalate
      model SSOT) documenting the pattern this plan wires up, corrected the now-stale 2026-06-23 "PARTIAL" note
      (both actionable-frontmatter halves had actually already shipped), and cross-linked from
      `/codex/04-architecture/agent-orchestrator-ci-escalation-wall-types.md`'s `data_pipeline_failure` row (incl.
      bumping its `last_reviewed`). — unified-trading-pm@6fca190fb8
- [ ] [BACKEND] P3. \_(stretch, optional)\_ Consider extracting `write_issue_doc`'s frontmatter-template logic into a
      shared location (UTL or UAC — both e2e-testing and deployment-service already depend on them) instead of
      leaving two independent implementations after this plan. Deferred: the tier-and-import-architecture rule bans
      direct service-to-service imports, e2e-testing and deployment-service already carry other independently-
      duplicated DP\_\* code as existing precedent, and extraction into a shared dependency is a real design call
      with its own review surface — not a mechanical follow-up. Revisit if the two templates drift again.

## Progress Log

- **2026-08-18 (interactive session, slot 3)**: Filed. Investigation traced the raw-commit anti-pattern in
  e2e-testing's `_dp_common.py`, the 3 documented silent-drop incidents, and — while scoping the fix — discovered
  deployment-service's `data_pipeline_monitors` package already implements the correct "defer to a dispatched agent,
  never raw-commit from an ephemeral runner" shape, but the `data_pipeline_failure` boot prompt never learned to file
  a doc from a deferred candidate payload, so the pattern was never actually exercised end-to-end for any finding
  source. Operator ruled: always defer (no local-commit fast path) + human plan. No code changed this session.
- **2026-08-18 (same session)**: Todos 1/3/5 shipped (`unified-trading-pm@6fca190fb8` boot prompt + codex,
  `deployment-service@f2fb7973126a5f59afe7ca943a65a4a162433225` frontmatter fix,
  `unified-trading-pm@c934930ba50d0a91c3ca15899469336be6ec0b66` checkbox flip). Todo 2 shipped
  `e2e-testing@aa6e8a1498` — raw commit path fully removed, IAM/Secret-Manager access to `GH_PAT` confirmed already
  granted (same `unified-trading-sa` service account both Cloud Run job families already run under), checkbox flip
  `unified-trading-pm@10a898359b`.
- **2026-08-18, todo 4 live drill (same session, in progress)**: Fired a real `repository_dispatch` to
  `escalate-to-orchestrator` by hand (`gh api repos/IggyIkenna/unified-trading-pm/dispatches`), mirroring
  `_dispatch_escalation_to_orchestrator`'s exact `client_payload` shape, with a `context` payload explicitly labeled
  as a verification drill (not a real finding) instructing the spawned worker to file the doc, verify its own
  frontmatter, mark it `status: resolved` as a drill, and stop — never attempt a root-cause fix. GH Actions run
  `32137368186` (`escalate-to-orchestrator.yml`) completed `success`. Confirmed live via read-only SSM check
  (`GET localhost:8765/api/escalations/active` on the orchestrator VM) that AO created a real escalation row
  `agt-2050ac` (repo `e2e-testing`, `wall_type: data_pipeline_failure`, `created_at: 2026-08-18T12:32:30Z`) —
  proves the chain works end-to-end through AO ingestion. **Not yet proven**: a worker actually claiming it and
  filing the doc — `agt-2050ac` sat `status: queued`, `slot_id: null` for the full ~15min check window, and the
  live queue shows genuine fleet capacity pressure right now (a real escalation, `agt-63a017`, has been stuck
  `queued` 3+ hours on "no free configured slot"), not a defect in this fix. Deliberately did not try to jump the
  drill ahead of real queued escalations. Todo 4 stays open pending a worker actually dispatching; check
  `plans/archive/issues/dp_audit_escalation_drill_verification_2026_08_18.md` (once/if filed) or re-run the same SSM
  check against escalation id `agt-2050ac`.
