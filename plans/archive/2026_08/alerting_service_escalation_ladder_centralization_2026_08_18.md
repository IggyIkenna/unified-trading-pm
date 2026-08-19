---
doc_type: plan
title: Centralize disaster-recovery escalation-ladder decisions in alerting-service
summary: >-
  deployment-service's data-pipeline watchers today decide AND act on every finding synchronously, in-process —
  alerting-service only ever hears about it AFTER the fact, over a one-directional channel, with zero decision
  authority. Operator-approved Option C keeps fast AUTO_RECOVER self-healing untouched in deployment-service and
  moves the harder FILE_ISSUE / PAGE_OPERATOR tiers behind a real escalation-ladder policy layer in alerting-service —
  reusing the existing lifecycle-events pub/sub channel, closing the one-directional gap with a light, GCS-durable
  return path (never a synchronous RPC), and relocating the GitHub repository_dispatch delivery call alongside
  alerting-service's other outbound notifiers.
status: complete
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, alerting-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [escalation, disaster-recovery, alerting-service, deployment-service, self-healing, circuit-breaker, gcs-durable-state]
related:
  [
    /plans/epics/observability_master.md,
    /plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md,
    /plans/active/deployment_service_api_integration_cleanup_2026_08_18.md,
    /plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md,
    /plans/archive/2026_08/migration_script_canonicalization_into_deployment_service_2026_08_18.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-18"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
depends_on:
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md,
    /plans/epics/observability_master.md,
    deployment-service/deployment_service/data_pipeline_monitors/escalation.py,
    deployment-service/deployment_service/data_pipeline_monitors/escalation_dedup.py,
    deployment-service/deployment_service/data_pipeline_monitors/revocation_actuator.py,
    deployment-service/scripts/recovery/_durable_state.py,
    alerting-service/alerting_service/notifiers/router.py,
    alerting-service/alerting_service/circuit_breaker.py,
    alerting-service/alerting_service/subscribers/alert_subscriber.py,
    alerting-service/alerting_service/persistence/storage_store.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py,
  ]
supersedes:
superseded_by:
source:
  [
    "Approved in an earlier conversation thread but never authored — written up this session per operator
    instruction. Pre-task conflict-check grepped plans/active/ + plans/active/issues/ for
    'alerting-service'/'escalation ladder'/'escalation architecture' -- no live plan or issue doc covers this
    architecture question. The one directly-adjacent prior-art doc found,
    /plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md, is ARCHIVED (fully shipped 2026-08-17),
    not a live conflict -- its RevocationActuator/EscalationTarget work is read as prior art + the direct precedent
    for this plan's revocation-cascade decision below, not duplicated.",
  ]
---

# Centralize disaster-recovery escalation-ladder decisions in alerting-service

## Why this plan exists

`deployment_service/data_pipeline_monitors/escalation.py`'s `route_finding()` decides AND acts on every data-pipeline
finding fully synchronously, in one watcher execution: it runs the `AUTO_RECOVER` actuator (or falls through), applies
the dependency-revocation verdict, writes the PM-clone issue doc, AND fires a GitHub `repository_dispatch` to
fast-spawn an orchestrator worker — all before it ever calls `log_event()`, which is the ONLY thing that reaches
alerting-service. alerting-service is purely a passive Slack/PagerDuty notifier over that channel: zero decision
authority over anything that already happened.

The operator weighed three options and chose the hybrid (Option C): leave `AUTO_RECOVER` (`_recover_consolidator`,
`_recover_backfill_vm`, `_recover_stalled_vm`, `_recover_preempted_vm` — the `_DP_RECOVERY_ACTIONS` table) completely
untouched in deployment-service (fast, local, no dependency on a second service's uptime), and route only the harder
`FILE_ISSUE` / `PAGE_OPERATOR` tiers through a real policy layer in alerting-service — an escalation ladder ("try N
times, then escalate"), starting with relocating the GitHub-dispatch delivery call itself.

## Current state — re-verified 2026-08-18 against the actual code

The background this plan was approved against is confirmed accurate, with two refinements:

- **`route_finding()` (`deployment-service/deployment_service/data_pipeline_monitors/escalation.py`) is still fully
  synchronous and still owns the GitHub dispatch.** `_dispatch_to_orchestrator()` fires a `repository_dispatch` to
  `IggyIkenna/unified-trading-pm` gated on `should_dispatch` (PAGE_OPERATOR tier, OR a confirmed FILE_ISSUE, OR an
  `AUTO_RECOVER` actuator that fell through) — deployment-service's own code, not alerting-service's.
- **The `lifecycle-events` channel is one-directional, confirmed via `alert_subscriber.py` + `cli.py`.**
  `deployment_service/data_pipeline_monitors/cli.py` wires `PubSubEventSink(topic="lifecycle-events", ...)`;
  `alerting-service/alerting_service/subscribers/alert_subscriber.py` subscribes to `lifecycle-events-sub` and routes
  via `alerting_service/notifiers/router.py::route_event` → `_route_data_pipeline_event`. Nothing publishes back the
  other way.
- **Refinement 1 — dedup-before-dispatch already lives right next to the call being relocated.**
  `escalation_dedup.py`'s `check_dispatch_dedup_for_finding()` / `check_relaunch_dispatch_budget()` gate
  `_dispatch_to_orchestrator()` today. Relocating the dispatch call without relocating (or re-deriving) this dedup
  logic would either lose the dedup entirely or leave deployment-service silently deduping a call it no longer makes —
  so Phase 2 below moves both together, not the HTTP call alone.
- **Refinement 2 — deployment-service already has a proven, GCS-durable, race-free state pattern for exactly this
  class of problem**, used TWICE already for closely related needs: `escalation_dedup.py`'s
  `check_dispatch_dedup_gcs()` (dispatch-dedup checkpoint, for the Cloud Run Job host with no local PM clone) and
  `revocation_actuator.py`'s actuation budget — both built on `scripts/recovery/_durable_state.py`'s `ShardedState`
  (one-GCS-object-per-fact, atomic create-if-absent, day-partitioned). This is the load-bearing precedent for the
  return-path design below: this codebase has already solved "share small, low-frequency state across process
  boundaries that don't share a filesystem or a live connection" exactly this way, twice, under real production load
  (`ShardedState`'s own docstring cites the 2026-08-10 incident where a tempdir-backed counter silently reset every
  Cloud Run Job execution).
- **`alerting_service/circuit_breaker.py` is real but a different shape than what's needed as-is.** It IS the closest
  existing building block (a CLOSED→OPEN→HALF_OPEN state machine on a sliding error-rate window), confirming the
  operator's instinct — but its state lives in plain in-process `dict`s (`self._errors`, `self._states`), keyed on
  `service:venue`, tracking `SERVICE_ERROR` events only. It does not survive a process restart and has no notion of a
  per-finding-identity retry ladder. Phase 3 below reuses its STATE NAMES and transition shape, not its storage.

## Decided design — the return path (deployment-service ↔ alerting-service)

**The gap that needs closing**: once alerting-service owns the escalation-ladder decision (Phase 3) and the GitHub
dispatch (Phase 2), deployment-service's OWN remaining FILE_ISSUE-tier action — writing the PM-clone issue doc via
`escalation_issue_writer.write_issue_doc()`, which stays in deployment-service (see Phase 2's third todo for why) —
has no visibility into what alerting-service has already decided. Its NEXT watcher tick, for the same still-broken
condition, should be able to see "alerting-service's ladder is already at rung N for this finding" without a live
call.

**Chosen mechanism: a GCS-durable state blob, written by alerting-service, read best-effort by deployment-service on
its next tick.** Alternatives considered and rejected:

1. **Synchronous RPC** (deployment-service calls an alerting-service HTTP endpoint to ask "what's the ladder state")
   — REJECTED. This re-introduces exactly the coupling Option C exists to avoid, just one tier up: deployment-service's
   Cloud Run Job would gain a new live network dependency + auth surface on a second service's uptime for
   non-time-critical bookkeeping. The whole point of keeping `AUTO_RECOVER` independent was "basic self-healing
   should not sit behind a second service's availability" — a live call for `FILE_ISSUE`/`PAGE_OPERATOR` context
   reintroduces the identical risk one tier later, for materially less benefit (the read is advisory annotation, not
   a control decision).
2. **A new PubSub topic FROM alerting-service back to deployment-service** — REJECTED for v1. Heavier to build (new
   topic + subscription + IAM + a persistent subscriber loop) for state that changes at watcher-cron cadence, not
   real-time; deployment-service's watchers are cron-triggered scripts that run, act, and exit — not a long-lived
   event-loop consumer — so a poll-on-next-tick read fits the existing execution model far better than adding a
   second listener.
3. **A GCS-durable state blob, read on next tick** — CHOSEN. Reuses the exact proven `ShardedState`-shaped pattern
   already load-bearing in this same code area (see "Refinement 2" above), needs no new topic/subscription, and
   degrades exactly like every other cross-cutting read in this codebase: best-effort, never raises, absent state
   reads as "no ladder context" (today's behavior, unchanged).

**Where the state lives, concretely** (own-bucket-per-writer, not a shared bucket either service has to reach into
for both directions):

- **Escalation-ladder state** (Phase 3, alerting-service-owned and alerting-service-written): alerting-service's own
  bucket (`alerting-service-<project>`, `alerting_service/persistence/storage_store.py::_bucket_name()`'s existing
  convention), under a new `alerting/state/escalation-ladder/<identity>.json` prefix — sibling to the existing
  `alerting/state/cooldowns.json`. deployment-service gets READ-ONLY access (Phase 1) — the lighter, lower-risk
  direction for a new cross-service IAM grant.
- **Dispatch-dedup + relaunch-budget checkpoints** (Phase 2, relocating to alerting-service but NOT changing owner
  bucket): stay in deployment-service's existing `deployment-scripts-<project>` bucket, same
  `vm-census/dispatch-dedup-checkpoint/` / `vm-census/relaunch-dispatch-budget/` prefixes `escalation_dedup.py`
  already uses — continuity of existing state matters more here than tidy bucket ownership, since a mid-migration
  cutover to a fresh bucket would silently reset both budgets to zero. alerting-service gets WRITE access here
  instead (it is now the one making the gated call).

**Shared identity, so the two repos can never derive two different keys for the same finding**: a new small
`unified-api-contracts` module (Phase 1) is the SSOT for the identity-key derivation both repos import — not a second
independently-hand-rolled regex in each repo. `escalation_dedup.py`'s own docstring already documents a near-miss
from exactly this class of drift (a tuple-signature regex that silently failed to match 5 of 8 corpus docs over a
comma-vs-no-comma formatting difference); a two-repo identity scheme with no shared SSOT is the same risk at a wider
blast radius.

**Aside, not in scope for this plan**: `alerting_service/persistence/storage_store.py::_bucket_name()` derives its
bucket name inline (`f"alerting-service-{project_id}"`) rather than via CLAUDE.md's `resolve_bucket_name()` UAC
helper — a pre-existing pattern this plan's Phase 3 code reuses as-is (consistency with the surrounding module beats
a scope-creeping fix here) rather than silently perpetuating without comment.

## Decided (not deferred) — the revocation cascade stays in deployment-service

The operator's framing left this a genuine open choice: stay in deployment-service with alerting-service gaining
visibility/override, vs. full migration later. **Decision: stays in deployment-service, unmigrated, for now** —
`_apply_revocation()` / `RevocationActuator` (`deployment-service/deployment_service/data_pipeline_monitors/
revocation_actuator.py`) are explicitly OUT of scope for the Phase 3 alerting-service policy layer.

**Reasoning, grounded in a directly on-point precedent already in this codebase**: the archived
`/plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md` plan already ruled on the closely analogous
question for the deadman/watcher-of-watchers layer (2026-08-14 entry) — `DP-WATCHER-001`/`DP-WATCHER-002` deliberately
do NOT route through alerting-service, because "routing it back through the alerting spine it exists to backstop
would re-couple them" (`/codex/05-infrastructure/data-pipeline-alerts.md` § "Watching the watchers", Layer 2). Revocation
is the same shape of risk: a drain/hold decision that depends on alerting-service's availability is a worse trade than
the visibility it would gain, for the identical reason `AUTO_RECOVER` stays local under Option C — revocation is
functionally part of the "fast, local, must-work-even-if-alerting-service-is-down" tier, not the
"already-can't-self-heal, judgment-shaped" tier this plan's ladder targets.

Revocation is not fully dark to alerting-service today, either: `_fleet_halt_visibility()` already emits
`DP_REVOCATION_FLEET_HALT` via the same `log_event()` path every other DP_* finding uses, so alerting-service (and
Slack) already has READ-ONLY visibility into every revocation action without owning any control over it — the
"visibility without migration" half of the operator's framing is therefore already satisfied by existing code, not a
gap this plan needs to close.

**Revisit condition, stated explicitly** (not a vague "someday"): only once deployment-service's live-deployment
surface genuinely splits into multiple independent services — the exact trigger the operator named ("as more live
deployments get split up") — should full migration be reconsidered, because only then does a SINGLE deployment-service
process stop being able to see the whole dependency graph locally, which is what makes local revocation correct today.

## Phase 1 — Shared identity contract + IAM verification

- [x] [INFRA] P1. Add `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/escalation_identity.py`
      exposing ONE pure function that derives a canonical identity string from a finding's `(registry_id, vm_name,
      asset_group, data_type)` fields — mirrors the two identity shapes `deployment-service/deployment_service/
      data_pipeline_monitors/escalation_dedup.py` already established in `_dispatch_checkpoint_identity()` (tuple-keyed)
      and `find_open_issue_for_vm()` (vm_name-keyed), so both repos derive the SAME GCS object key without duplicating
      (and risking drift in) the derivation logic. Export it alongside `DATA_PIPELINE_ALERT_RULES` in
      `unified_api_contracts/canonical/crosscutting/alerting/`. Done-when: a unit test asserts identical output for
      both known identity shapes, and Phases 2-4 import this function rather than re-deriving either shape locally.
      **✅ DONE (2026-08-18)** — `derive_escalation_identity()` added, tuple-keyed branch verified byte-identical to
      `_dispatch_checkpoint_identity()`'s source; vm-keyed shape is a NEW canonical definition (no prior standalone
      derivation existed for it in `find_open_issue_for_vm()`, which only does substring/tag matching) — uses the
      same sanitization convention with a `"vm|"` disambiguating prefix, keeping the two identity spaces disjoint by
      construction. Also exported through the top-level `unified_api_contracts/alerting.py` consumer-facing facade
      (not just the crosscutting `__init__.py`), mirroring `DATA_PIPELINE_ALERT_RULES`'s existing dual-export
      pattern. Raises `ValueError` when neither shape resolves (identity derivation, not dedup-applicability —
      callers resolve that first) — flag for Phase 2/3 authors if never-raises semantics were expected instead.
      9 unit tests (parametrized parity against inlined reference oracles + precedence + disjointness + determinism).
      `quality-gates.sh` green. Shipped `unified-api-contracts@d80c599c15`.
- [x] [INFRA] P1. Verify + grant the cross-service IAM this design needs, BEFORE building on top of it: (a)
      alerting-service's actual Cloud Run runtime identity needs WRITE access to deployment-service's durable-state
      bucket (`deployment-scripts-<project>`, resolved via `deployment-service/scripts/recovery/_durable_state.py`'s
      `state_bucket()`) for the relocated dispatch-dedup + relaunch-budget checkpoints (Phase 2); (b)
      deployment-service's Cloud Run Job runtime identity needs READ access to alerting-service's own bucket
      (`alerting-service-<project>`, resolved via `alerting-service/alerting_service/persistence/storage_store.py`'s
      `_bucket_name()`) for the new escalation-ladder state (Phase 3/4). Check the CURRENT service accounts each
      service actually runs as (`gcloud run services describe` / `gcloud run jobs describe` — do not assume
      `unified-trading-sa`) before granting anything; if either identity already qualifies for IAM self-service per
      `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`, grant directly rather than treating it as
      operator-gated. Done-when: a scratch object written from alerting-service's live runtime identity is read back
      successfully from deployment-service's live runtime identity, and vice versa — not just an IAM-policy dump.
      **✅ DONE (2026-08-18)** — checked the ACTUAL runtime identities rather than assuming: alerting-service runs as
      Cloud Run service `dp-alerting-subscriber` (asia-northeast1); deployment-service's data-pipeline-monitor
      watchers run as Cloud Run Jobs `uts-prod-dp-*` (`uts-prod-dp-meta-watchers`, `uts-prod-dp-heartbeat-watcher`,
      etc., same region). **Finding: both already run as the SAME service account**,
      `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` — confirmed via
      `gcloud run services describe`/`gcloud run jobs describe`. `gcloud projects get-iam-policy` shows this SA
      already holds project-wide `roles/storage.admin`, which covers both target buckets — no new grant needed,
      the design's IAM prerequisite was already satisfied by the existing shared-SA architecture. **Live round-trip
      verified anyway, per the done-when bar** (not just an IAM-policy dump): wrote a scratch object to
      `deployment-scripts-central-element-323112` via `get_storage_client()`, read it back, deleted it; same for
      `alerting-service-central-element-323112` — both buckets confirmed reachable/writable/readable under the
      shared identity. No IAM changes made (nothing needed granting); no code shipped for this todo (verification +
      documentation only).

## Phase 2 — Relocate the GitHub-dispatch delivery call

- [x] [BACKEND] P1. Add `alerting-service/alerting_service/notifiers/orchestrator_dispatch.py` (sibling to
      `pagerduty.py` / `uts_live_alerts_slack.py` / `data_pipeline_slack.py`) that owns the ACTUAL GitHub
      `repository_dispatch` HTTP call — port `deployment-service/deployment_service/data_pipeline_monitors/
      escalation.py::_dispatch_to_orchestrator()`'s body (the `GH_PAT` Secret-Manager fetch, the
      `IggyIkenna/unified-trading-pm` `dispatches` POST, the `escalate-to-orchestrator`/`data_pipeline_failure`
      payload shape, the `_VM_LIFECYCLE_EVENTS`-based relaunch-context text) so it reads its inputs from the
      `event_name`/`details` dict `alerting_service/notifiers/router.py::_route_data_pipeline_event` already
      receives (registry_id, vm_name, relaunch_launcher, deployment_id, asset_group all already ride in
      `event_details` today via `route_finding()`'s stamping — no new field needs to be added to the emitted event
      for this phase). Done-when: the ported function has its own unit tests (best-effort/never-raises, the 200-299
      success path, the `HTTPError`/network-failure paths) at parity with the deployment-service original's existing
      coverage, and is called from `_route_data_pipeline_event` gated on the finding's escalation tier
      (`file_issue`/`page_operator`).
      **✅ DONE (2026-08-18)** — `orchestrator_dispatch.py` ports the body verbatim (same GH_PAT fetch, same
      `dispatches` POST target, same payload shape/relaunch-context text), with one deliberate deviation: the GH_PAT
      fetch is cached per-process (mirrors `pagerduty.py`'s pattern) rather than per-call, since alerting-service is
      a warm Cloud Run Service (the original's per-call fetch exists only because deployment-service's Cloud Run Job
      gets a fresh container per execution). Wired into `router.py::_route_data_pipeline_event` via a new sibling
      `orchestrator_dispatch_gate.py` (split out because `router.py` was already at 1099/1100 lines — mirrors the
      existing `coalesce.py`/`kill_switch_rules.py` split pattern), gated on `escalation_tier in ("file_issue",
      "page_operator")`. Full unit-test parity (best-effort/never-raises, 200-299 success, HTTPError/network-failure
      paths). `quality-gates.sh` green. Shipped `alerting-service@96ab851608`.
- [x] [BACKEND] P1. Port the dedup/budget logic that gates the call above — `escalation_dedup.py`'s GCS-checkpoint
      variant ONLY (`check_dispatch_dedup_gcs()`, `check_relaunch_dispatch_budget()`; NOT `check_dispatch_dedup`/
      `check_dispatch_dedup_vm`, which read the local PM clone — alerting-service, a Cloud Run Service, has none)
      into a new `alerting-service/alerting_service/notifiers/orchestrator_dispatch_budget.py`, reading/writing the
      SAME `deployment-scripts-<project>` bucket + `vm-census/dispatch-dedup-checkpoint/` /
      `vm-census/relaunch-dispatch-budget/` GCS prefixes the deployment-service originals already use — state
      continuity across the cutover, not a fresh zeroed budget. Uses Phase 1's shared UAC identity function instead
      of re-deriving `_dispatch_checkpoint_identity()`/`_shard_group_key()` independently. Done-when: a live GCS read
      of an EXISTING checkpoint/budget object (one actually written by deployment-service pre-migration) produces the
      identical skip/dispatch verdict deployment-service's original code would have produced for that same state.
      **✅ DONE (2026-08-18)** — `orchestrator_dispatch_budget.py` ports `check_dispatch_dedup_gcs()`/
      `check_relaunch_dispatch_budget()` using `derive_escalation_identity()` from UAC instead of re-deriving
      identity. One known limitation, documented not silently absorbed: `vm_prefix()`'s longest-prefix matching
      needs deployment-service's `VM_PREFIX_TO_BUCKET` registry, which alerting-service (Tier 4, no
      service-to-service deps) cannot import — a point-in-time (2026-08-18) copy of just the 246 dict KEYS (not
      values) was embedded, flagged as a drift-risk needing promotion to a shared UAC registry later. **Live
      verification against real pre-migration GCS state** (read-only, a no-op-write proxy, nothing mutated):
      `derive_escalation_identity()` reproduced the real checkpoint key `cefi|book_snapshot_5|dp-fetch-009.json`
      exactly; replaying its stored `max_attempted_at` produced the identical skip/new-activity verdict the
      original would; `_ShardedState.count()` against a real budget group matched the real GCS listing exactly
      (confirmed a shard-year-grouping discrepancy in older objects is NOT a port defect — deployment-service's own
      current source has the identical regex). Shipped `alerting-service@96ab851608`.
- [x] [BACKEND] P1. DELETE `_dispatch_to_orchestrator()`, its `_DISPATCH_*`/`_GH_PAT_SECRET` constants, and the
      `should_dispatch`/dedup-dispatch block inside `route_finding()` from `deployment-service/deployment_service/
      data_pipeline_monitors/escalation.py` — no shim, no dead re-export (CLAUDE.md "Delete deprecated code"). Also
      delete the now-unused `check_dispatch_dedup_gcs`/`check_relaunch_dispatch_budget`/`check_dispatch_dedup_for_finding`
      call sites from `escalation.py` (KEEP `escalation_dedup.py`'s `check_dispatch_dedup`/`find_open_issue_for_tuple`/
      `find_open_issue_for_vm` — the ORIGINAL PLANNING ASSUMPTION was that these still gate deployment-service's OWN
      `write_issue_doc()` call; **CORRECTED 2026-08-18 (Phase 4 finding, see that section's Progress Log note) — this
      was already stale at planning time**: a fresh `rg` found ZERO production call sites for any of the three in
      `deployment_service/`, only test references — `write_issue_doc()`'s actual dedup is its own same-day-slug
      `path.exists()` check. Kept as-is anyway per this todo's own instruction (deleting them wasn't in scope here),
      just noting the "gates write_issue_doc()" justification for keeping them was never true). `route_finding()`'s
      `result["dispatch"]` key and the `event_details["fast_spawn_dispatched"]`/
      `"fast_spawn_skipped"` stamping go with it — the dispatch verdict now only exists on the alerting-service side.
      Done-when: `rg -l _dispatch_to_orchestrator deployment-service/` returns nothing, deployment-service's
      `quality-gates.sh` is green, and a live end-to-end fire of a real or synthetic FILE_ISSUE-tier finding proves
      the SAME orchestrator fast-spawn now happens via alerting-service's new path with deployment-service's watcher
      emitting nothing but the plain `DP_*` event.
      **✅ DONE (2026-08-18)** — done directly (not delegated, given the deletion's precision requirements). Removed
      `_dispatch_to_orchestrator()`, `_DISPATCH_PM_REPO`/`_DISPATCH_EVENT_TYPE`/`_DISPATCH_WALL_TYPE`/
      `_GH_PAT_SECRET`, the `should_dispatch`/`actuator_needs_worker`/dedup-dispatch block, `result["dispatch"]`,
      `event_details["fast_spawn_dispatched"/"fast_spawn_skipped"]`. Also removed now-fully-dead imports
      (`escalation_dedup` module import — zero remaining call sites in this file once the dispatch dedup calls were
      gone; `json`, `urllib.error`, `urllib.request`, `HTTPResponse`, `get_secret_client`, `target_repo_for`) and
      reworded the stale module docstring describing the now-relocated dedup architecture. **Real regression caught
      and fixed in the same change**: `event_details["escalation_tier"]` was being stamped from the raw
      `finding.tier` BEFORE the actuator-fallthrough logic resolved `effective_tier` — meaning a finding whose
      actuator failed (declared `auto_recover`, falls through to `file_issue`) would have stamped `escalation_tier=
      "auto_recover"`, silently breaking alerting-service's new gate (`escalation_tier in ("file_issue",
      "page_operator")`) for exactly the "wired actuator failed, hand off to a worker" case the old in-process
      `actuator_needs_worker` check used to correctly escalate. Fixed to stamp `effective_tier` (post-fallthrough)
      instead. **Verification**: `rg -l _dispatch_to_orchestrator deployment-service/` returns nothing (confirmed).
      Dispatched a sub-agent to fix the ~20 test sites across 3 files that referenced the deleted symbols — it
      correctly identified several tests as needing FULL DELETION (not just unmocking) beyond what was hinted,
      since their entire premise was `route_finding()`'s now-removed dispatch decision (e.g. all 7 "route_finding
      wiring" tests in `test_escalation_dedup.py`, `test_critical_attempts_dispatch` in
      `test_data_pipeline_monitors.py`) — that coverage now lives in alerting-service's own
      `test_orchestrator_dispatch.py`/`test_orchestrator_dispatch_budget.py` (already shipped, Phase 2). Full
      `quality-gates.sh` green (independently re-verified, not just the sub-agent's self-report). **Live
      end-to-end fire NOT performed** — deliberately: doing so would fire a REAL `repository_dispatch` against the
      production `IggyIkenna/unified-trading-pm` repo, spawning a real AutoSpawn worker, a genuine production side
      effect not worth triggering just to prove this todo — verified instead via the ported code's own unit-test
      parity (Phase 2) + this deletion's static confirmation (`rg` + green gate) that deployment-service no longer
      has any code path capable of firing the old dispatch. Shipped `deployment-service@269ce1f268`.

## Phase 3 — Build the escalation ladder in alerting-service

- [x] [BACKEND] P1. Add `alerting-service/alerting_service/escalation_ladder.py`: a GCS-durable retry-counter modeled
      on `circuit_breaker.py`'s CLOSED/OPEN/HALF_OPEN state shape and naming (CLOSED = below the escalation
      threshold, OPEN = escalated, HALF_OPEN = probation after a cooldown) but backed by durable per-identity state
      instead of `circuit_breaker.py`'s in-process dicts — own implementation (not a cross-repo import of
      deployment-service's `scripts/recovery/_durable_state.ShardedState`) using
      `alerting_service/persistence/storage_store.py`'s existing bucket-resolution convention
      (`alerting-service-<project>`), under a new `alerting/state/escalation-ladder/<identity>.json` prefix, identity
      from Phase 1's shared UAC function. Records occurrence count, first-seen timestamp, current rung, and
      last-escalated-at. Done-when: a unit test proves state survives a fresh-process re-instantiation (reads back a
      previously-written rung after simulating a restart) and a CLOSED→OPEN transition fires exactly once per
      crossing (no re-fire on every subsequent occurrence while already OPEN — mirrors `circuit_breaker.py`'s
      existing "no transition → empty string" return contract).
      **✅ DONE (2026-08-18)** — `LadderState`/`record_occurrence()`/`get_state()`, `DEFAULT_ESCALATION_THRESHOLD =
      3`. Mirrors `circuit_breaker.py`'s return contract (`STATE_OPEN` on transition, `""` on none) with one
      necessary extension: `None` on a durable-read/write FAILURE (bucket unresolvable/GCS exception — a failure
      mode in-process dicts never had), fails OPEN (treated like a transition, never like a silent `""`) so a
      GCS hiccup can't accidentally suppress a real escalation. **HALF_OPEN implemented with real semantics** (a
      genuine judgment call, not left structural): never re-dispatch WITHIN the cooldown window once OPEN; a
      recurrence AFTER the window elapses ages OPEN→HALF_OPEN and immediately re-fires HALF_OPEN→OPEN (bumping
      `rung`), so a still-recurring PAGE_OPERATOR-tier condition doesn't go permanently muted after its first
      escalation. Tests prove: fresh-process durability (write via one fake-client instance, read via a separate
      one, no shared Python state), CLOSED→OPEN fires exactly once (5 further OPEN-state occurrences all return
      `""`), and the HALF_OPEN re-escalation path.
- [x] [BACKEND] P1. Wire `alerting_service/notifiers/router.py::_route_data_pipeline_event` to run every
      FILE_ISSUE/PAGE_OPERATOR-tier DP_* event through the new ladder BEFORE Phase 2's relocated dispatch call — a
      CLOSED→OPEN transition (or an already-OPEN state) is what now gates the dispatch, replacing the old
      always-dispatch-if-tier-matches-and-not-deduped behavior with a genuine "try N occurrences quietly [Slack-mirror
      only], the Nth crossing escalates [fires the dispatch]" ladder. State the threshold explicitly in code and here
      — start at 3 occurrences within the event's existing `_RECURRING_ALERT_COOLDOWNS` window (reuse that table's
      per-event cadence rather than inventing a second one) — not a "tune this later" placeholder. Done-when: a
      scripted replay of N synthetic FILE_ISSUE-tier events for one identity dispatches zero times for occurrences
      1..N-1 and exactly once on occurrence N, verified against the ladder + Phase 2's dispatch module together (not
      each mocked in isolation).
      **✅ DONE (2026-08-18)** — wired into `orchestrator_dispatch_gate.py` (Phase 2's module) before its existing
      dedup+dispatch call. `_RECURRING_ALERT_COOLDOWNS`/`_dedup_window_for` extracted from `router.py` into a new
      sibling `recurring_alert_cooldowns.py` (avoids a circular import — `router.py` already imports the gate
      module — and kept `router.py` under its 1100-line cap: 1100→~1074 lines, call site unchanged); both
      `router.py`'s own deduplicator and the ladder now consult the SAME table, not a second independently-tuned
      one. **Done-when literally satisfied**: `test_muted_for_n_minus_one_then_dispatches_exactly_once_on_n`
      replays 3 real `router._route_data_pipeline_event` calls through the REAL ladder + REAL dedup-budget module
      (only the storage client and the actual GitHub dispatch call faked) — 0, 0, then 1 dispatch, staying 1 on a
      further occurrence. `quality-gates.sh` green (independently re-verified). Shipped `alerting-service@0ea2857cc8`.
      **Phases 1-3 of this plan are now fully complete** — only Phase 4 (deployment-service reads the ladder back)
      and Phase 5 (a small codex cross-reference doc) remain.

## Phase 4 — Return path: deployment-service reads the ladder

- [x] [BACKEND] P2. In `deployment-service/deployment_service/data_pipeline_monitors/escalation.py::route_finding()`,
      before the `FILE_ISSUE`-tier `write_issue_doc()` call, add a best-effort (never-raises, matching every other
      cross-cutting read already in this module) GCS read of alerting-service's
      `alerting/state/escalation-ladder/<identity>.json` (Phase 3's state, identity from Phase 1's shared function)
      via Phase 1(b)'s IAM grant. When present, thread the ladder context (occurrence count, rung, first-seen) into
      `event_details` and into `escalation_issue_writer.py::write_issue_doc()`'s initial doc body, so a human or a
      dispatched worker opening the filed issue sees the full recurrence history in one place instead of
      reconstructing it from repeated individual Slack alerts. Absent/unreadable state degrades to today's behavior
      exactly — never blocks or delays issue-filing. Done-when: a live fire against a real, already-OPEN ladder state
      (seeded via Phase 3's test harness) produces an issue doc whose body visibly carries the occurrence count and
      rung, and a live fire with no ladder state (a genuinely first-ever finding) produces a doc byte-shape-identical
      to today's (no missing-field crash, no dangling blank ladder section).
      **✅ DONE (2026-08-18)** — `event_details` gains `ladder_occurrence_count`/`ladder_rung`/`ladder_first_seen_at`
      + a 4th key not in the original spec, `ladder_state` (CLOSED/OPEN/HALF_OPEN — added because "rung 2, 5
      occurrences" alone is ambiguous about current escalation status). Reads the SAME raw JSON shape directly via
      `get_storage_client()` (never imports `alerting_service.escalation_ladder` — would violate the Tier-4
      no-service-deps rule). Threaded into `write_issue_doc()`'s body via `dataclasses.replace(finding,
      details={**finding.details, **ladder_context})`, mirroring the existing `_oom_investigate_finding()` pattern
      already in this file — no signature change to `write_issue_doc()` itself. **Both done-when scenarios verified
      live against real infra** (real `alerting-service-central-element-323112` bucket, scratch PM-clone tmp dirs,
      never touching the real PM clone): a seeded OPEN state (`occurrence_count=5, rung=2`) produced a doc body
      visibly carrying all 4 fields, cleaned up after; a fresh never-seeded identity produced a doc with zero
      `ladder_*` keys, byte-shape-identical to pre-Phase-4 behavior. `quality-gates.sh` green (independently
      re-verified). Shipped `deployment-service@a9eb4f5465`.
- [x] [REVIEW] P2. Check whether `escalation_dedup.py`'s existing OPEN-issue-doc dedup (`check_dispatch_dedup`, still
      owned by deployment-service post-Phase-2) needs a change so a doc already carrying a ladder-escalated
      annotation is not silently read as "no new activity" purely because `max_attempted_at` hasn't moved — an
      escalation-worthy RECURRENCE is itself new information even when the underlying data hasn't changed. The two
      signals (data freshness vs. occurrence frequency) may turn out to be genuinely orthogonal and need no
      reconciling — state which, with the reasoning, in this doc's Progress Log; do not leave it implicit.
      **✅ DONE (2026-08-18) — no code change needed, genuinely orthogonal.** `checkpoint_has_new_activity()`'s
      `max_attempted_at` tracks whether the underlying `attempted_failed` backlog DATA moved (a
      correctness/freshness signal); the ladder's `occurrence_count`/`rung` tracks how many times the SAME alert
      fired (a recurrence-frequency/notification-fatigue signal). Forcing a ladder rung-bump to count as "new
      activity" would reopen the exact "30+ redundant dispatches for one already-diagnosed condition" bug
      `check_dispatch_dedup` was built to close, for precisely the case (a static, already-diagnosed backlog
      re-triggering the ladder without new data) most likely to trip it — the ladder already has its own dedicated
      escalation signal (the dispatch itself, firing once per CLOSED→OPEN/HALF_OPEN→OPEN crossing), so there's no
      gap for `check_dispatch_dedup` to fill. **Correction to this doc's own Phase 2 entry** (a doc/comment that
      misled is a finding, fixed in the same turn per the workspace hard rule): Phase 2's "KEEP
      `escalation_dedup.py`'s `check_dispatch_dedup`/`find_open_issue_for_tuple`/`find_open_issue_for_vm` — those
      still gate deployment-service's OWN `write_issue_doc()` call" claim is **factually stale** — a fresh `rg`
      across `deployment_service/` found ZERO production call sites for any of these three functions (only
      `tests/unit/test_escalation_dedup.py` references them). `write_issue_doc()`'s only actual dedup is its own
      same-day-slug `path.exists()` check, unrelated to `check_dispatch_dedup`. Not chased further here (out of
      this todo's scope — this todo is about whether the ladder needs to interact with that dedup, and the answer
      is no either way, whether or not it's currently wired) — flagged as a fact for whoever next touches
      `escalation_dedup.py`'s call-site wiring.

## Phase 5 — Revocation cascade

- [x] [DOCS] P3. Add a short cross-reference note to `/codex/05-infrastructure/data-pipeline-alerts.md` § "Watching
      the watchers" (or a new adjacent subsection) recording this plan's decision above: `_apply_revocation()` /
      `RevocationActuator` stay in deployment-service, not migrated into alerting-service's new policy layer, citing
      the same 2026-08-14 DP-WATCHER independence ruling in
      `/plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md` this plan's reasoning is grounded in,
      plus the stated revisit condition (only on a genuine multi-service split of deployment-service's live-deployment
      surface). Done-when: the note exists and both this plan and the codex doc cross-link each other.
      **✅ DONE (2026-08-18)** — added a new "Revocation cascade stays local to deployment-service (2026-08-18
      ruling)" subsection immediately after "Watching the watchers", citing the DP-WATCHER independence ruling, the
      `_fleet_halt_visibility()`/`DP_REVOCATION_FLEET_HALT` existing-visibility fact, and the stated revisit
      condition verbatim. Cross-linked both directions: this plan already cited the codex doc in its own "Codex
      SSOTs" table; added this plan's path to the codex doc's `referenced_by:` frontmatter. **All 5 phases of this
      plan are now complete** — every todo checked, plan ready for archival.

## Codex SSOTs

| Doc | Why it's cited |
| --- | --- |
| `/codex/05-infrastructure/data-pipeline-alerts.md` | The `escalation` tier registry (`auto_recover`/`file_issue`/`page_operator`) this ladder gates on, + the "Watching the watchers" independence precedent Phase 5's decision is grounded in. |
| `/codex/04-architecture/autonomous-recovery-matrix.md` | The agent-vs-human self-healing scope `AUTO_RECOVER` already implements and this plan deliberately leaves untouched. |
| `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md` | Governs whether Phase 1's IAM grants are self-service or need a distinct credential ask. |
| `/plans/epics/observability_master.md` | Parent epic — owns alerting-service, the Incident Gateway, and the Layer-0/1 recovery substrate this plan extends. |

## Progress Log

- **2026-08-18**: Plan authored per operator instruction (approved in an earlier conversation thread, never previously
  written up). Re-verified the "one-directional channel" and "zero decision authority" background claims directly
  against current code (`escalation.py`, `alert_subscriber.py`, `cli.py`, `router.py`) — both hold. Found
  `escalation_dedup.py`'s existing GCS-durable checkpoint pattern (`check_dispatch_dedup_gcs`, built on
  `_durable_state.ShardedState`) as the load-bearing precedent for the return-path design, and the archived
  `alert_driven_dependency_revocation_2026_08_12.md` plan's 2026-08-14 DP-WATCHER independence ruling as the direct
  precedent for the revocation-cascade decision — both cited above rather than re-derived from scratch. Confirmed
  `parent_epic: observability_master` (not `escalation_and_disaster_recovery_master`, which owns the AGENT-facing
  `/blocked` role-agnostic escalation pipeline, a different domain; not `infrastructure_master`, too generic) by
  reading both candidate epics' actual scope — `observability_master` explicitly owns alerting-service + the
  Layer-0/1 recovery substrate + the auto-recovery matrix connection, and is the same epic the directly-analogous
  archived revocation plan used.
