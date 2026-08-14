---
doc_type: plan
title: Arm alert-driven dependency revocation — give the actuator a production caller
summary: >-
  The revocation mechanism is BUILT and INERT. Measured 2026-08-14: nothing calls RevocationActuator.actuate() outside
  tests, so no alert has ever revoked anything and none will. The read side is fully wired (heartbeat drain poll,
  vm-exec admission gate) — the fleet is listening and nothing is speaking. Split out of
  alert_driven_dependency_revocation_2026_08_12 (which hit its 1000-line hard cap) because arming is separate work from
  building. The target resolver now exists (deployment-service@cf5e041e7); what remains is the call site, which is
  blocked by a real import cycle, plus release-bookend wiring and live confirmation.
status: active
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, unified-api-contracts]
scope: [engineer, admin]
tags: [alerting, self-healing, vm-lifecycle, drain, dependency-dag, escalation]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /plans/active/alert_driven_dependency_revocation_2026_08_12.md,
  ]
created: "2026-08-14"
last_updated: 2026-08-14
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
effort: high
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    deployment-service/deployment_service/data_pipeline_monitors/escalation.py,
    deployment-service/deployment_service/data_pipeline_monitors/revocation_actuator.py,
    deployment-service/deployment_service/data_pipeline_monitors/revocation_targets.py,
    deployment-service/deployment_service/vm_prefix_registry.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/dependency_revocation.py,
  ]
supersedes:
superseded_by:
depends_on: alert_driven_dependency_revocation_2026_08_12
source:
---

# Arm alert-driven dependency revocation

> **The mechanism is built and has never fired.** Split from
> `/plans/active/alert_driven_dependency_revocation_2026_08_12.md` on 2026-08-14. That plan's Phases 1-7 are done and
> green; this one carries the work that makes any of it reach a VM. The parent MUST NOT be archived until this closes.

> **This plan cannot be archived until this phase is done.** Phases 1-6 are genuinely complete and green, and the READ
> side is fully wired: `heartbeat_cli` polls for a drain marker on every tick, and `vm-exec-with-gcs-tee.sh` gates
> admission and exits 75. But **nothing writes a marker.** Measured 2026-08-14: `rg 'RevocationActuator|\.actuate\('`
> over deployment-service, excluding tests, returns **its own definition and nothing else** — zero production call
> sites. `resolve_dependents()` is likewise consumed only inside UAC. The fleet is listening and nothing is speaking, so
> no alert has ever revoked anything and none will.
>
> This was not visible from the plan's own state: every Phase 4 todo is ✅ and each is honestly ticked — the actuator
> WAS built, tested and shipped. "Built" and "called" are different properties, and Phase 4 only ever claimed the first.
> Recording that here because the same shape of gap will hide in any plan that ships a component without an explicit
> caller-side todo.

> **OPERATOR DECISION 2026-08-14 — target granularity: DEPS_DRAIN targets the SPECIFIC RUNNING VM.** Admission actions
> (`DEPS_HOLD` / `FLEET_HALT`) target the PREFIX FAMILY. This follows the semantics rather than cutting across them: a
> drain speaks to a process that is running right now and must flush what it is holding, so it needs that instance's
> name; a hold speaks to launches that have not happened yet, which are only identifiable by family. It also means the
> two markers a `DEPS_DRAIN` now writes are keyed differently on purpose — `vm-logs/<vm-name>/` for the drain,
> `vm-census/admission-hold/<prefix>/` for the hold — and the resolver must return both, not one reused twice.

- [x] ✅ [CODE] P0. **Resolve dependents to actuation targets.** `evaluate_revocation()` answers WHAT action; nothing
      answers WHO to apply it to. `resolve_dependents(upstream_entity, asset_group)` returns `(asset_group, data_type)`
      pairs, but the actuator takes a VM prefix / Cloud Run job name — the translation layer between them does not
      exist, and it is the reason nothing calls `actuate()`. Build it against the registries the Phase 0 census already
      enumerated (`LAUNCHER_FOR_VM_PREFIX` / `VM_PREFIX_TO_BUCKET`: 243 prefixes, 178 mapping to 104 launcher scripts).
      **Design call MADE by the operator 2026-08-14**: DEPS_DRAIN targets the SPECIFIC RUNNING VM; DEPS_HOLD and
      FLEET_HALT target the prefix family. A drain therefore yields both shapes, keyed differently on purpose. Repo:
      deployment-service. — **deployment-service@cf5e041e7**: `revocation_targets.py` (`targets_for_finding`,
      `family_of`, `prefix_families_for`, `running_vms_in`) + 12 tests; gate 3436 passed / 1 xfailed. Prefix matching is
      ANCHORED (an unanchored match would halt an unrelated estate) and `family_of` takes the LONGEST match so an
      extended-backfill VM is not swept up by the broader family.

> **Resolver groundwork (measured 2026-08-14, read-only).** `VmPrefixSpec` has NO `asset_group` field, so
> `(asset_group, entity)` must match on the prefix STRING — reuse `_scheduler_jobs_for()`'s technique, not a second one.
> `vm_prefix_registry` resolves buckets AT IMPORT and raises `BucketNamingError` without `GCP_PROJECT_ID`, so import it
> lazily and degrade (same contract as `_STORAGE_AVAILABLE`). `resolve_dependents()` is fleet-wide when
> `asset_group=None`, so one alert fans out to many targets — the budget is keyed per (alert, target).
>
> **CORRECTION (2026-08-14, on implementing):** the "import it lazily and degrade" advice above was WRONG and is struck.
> The gate BANS both function-level imports (AST-detected) and `try/except ImportError` shims, and three existing
> consumers (`relaunch_backfill_vm`, `relaunch_stalled_vm`, `vm_zombie_watchdog`) already import `VM_PREFIX_TO_BUCKET`
> at module top level. Import it at the top like they do; the defensive version cost a gate round-trip to discover.

- [x] ✅ [CODE] P0. **Call `actuate()` from `escalation.route_finding()`.** — **deployment-service@79864746c.** The
      mechanism is ARMED: `actuate()` has a production caller and fires for every finding, independent of tier. The
      import cycle was broken by inverting the actuator's FLEET_HALT visibility to an injected callable (that one
      import, used only to announce a halt, was the whole blocker), and room was made by extracting
      `escalation_issue_writer.py` with a TYPE_CHECKING-only type import (escalation.py 958 → 930). **A correctness fix
      fell out of it**: the announcement now calls `log_event` directly instead of `meta_watchers.emit_finding`, which
      calls `route_finding` — announcing from INSIDE `route_finding` would have re-entered the escalation hop and re-run
      revocation against the announcement. The original design carried that edge and it never fired only because the
      actuator had no caller. The `xfail(strict=True)` guard is removed: strict failed on PASS the moment the call site
      landed, which is exactly what forced its removal in the same commit. That is the seam every DP finding already
      passes through, and revocation must fire there INDEPENDENT of tier — a `DEPS_DRAIN` verdict applies whether the
      finding is `auto_recover`, `file_issue` or `page_operator`, unlike `_DP_RECOVERY_ACTIONS` which is auto-recover
      only. Use `finding.registry_id` as the alert identity (the finer key — `DP-FETCH-007`/`009` share one `AlertCode`)
      and fall back to `finding.event`. Must never crash the sweep: same `except Exception` contract the existing
      actuator dispatch already uses. Record the outcome in `event_details` so the Slack alert says what was revoked.
      Repo: deployment-service.
- [x] ✅ [CODE] P0. **Emit and release the bookend.** — **deployment-service@375835a9a.** Wired into
      `meta_watchers.reconcile_resolved()`, which already finds alerts that fired on a prior sweep and did not re-fire.
      Release re-derives targets with the SAME `targets_for_finding()` call delivery used, so no extra state is
      persisted and the halves cannot drift. Documented imprecision: the alert key carries the EVENT, not the finer DP
      id; both id-pairs sharing an event today resolve to the same action, so released == delivered.
      `test_release_has_a_production_caller` added — the same AST guard that caught the actuator.
      `RevocationActuator.release()` exists and is tested but has no production caller either, so even once holds are
      written, nothing clears them — a revocation that cannot be released is an outage with extra steps, and this is the
      alerting SSOT's close-bookend rule. Wire release to the condition-resolved path. Repo: deployment-service.
- [x] ✅ [TEST] P0. An anti-inertness guard: a test asserting `actuate()` has at least one non-test caller. —
      **deployment-service@cf5e041e7** (guard, AST-based not grep) + **@79864746c** (xfail removed once wired) +
      **@375835a9a** (same guard now covers `release()`). The whole mechanism sat wired-but-unreachable through six
      green phases; a grep-level guard is what makes that unrepeatable. Repo: deployment-service.
- [ ] [OPERATOR] P0. **Confirm it live after wiring**: the monitor runs as the `uts-prod-dp-exit-code-monitor` Cloud Run
      Job on a `*/5` schedule, so verify (a) the job's deployed image contains the wiring commit
      (`gcloud run jobs describe`), (b) an execution actually invoked revocation (log a `DP-REVOCATION-*` line), and (c)
      a marker appears in `vm-census/admission-hold/` for a real condition. A green Cloud Build is NOT this —
      `Evidence: cloudbuild=<id>` plus an execution log line is. Repo: deployment-service.

> **📏 COVERAGE NUMBERS CORRECTED 2026-08-14 — I got this wrong twice, both times by counting the wrong thing.** First I
> reported "179/184 covered" by counting launchers that SOURCE `launcher_common.sh`; that lib only MENTIONS the wrapper
> in comments. Then "148/184 gated, 158 ungated" by counting `lc_` helper USERS — but those sets overlap, so the two
> numbers were not complements and 158 was never the ungated count.
>
> **Measured properly** (direct reference OR via a lib that actually routes to the wrapper): **173 of 186 gated, 13
> truly ungated.** Of those 13: **8 are the AWS path** (`launch-*-aws.sh` — a genuinely separate cloud path, the real
> gap), 1 is a GCP capture VM (`launch-features-backfill-vm.sh`), and 4 are structurally non-capture
> (`launch-cefi-week-test.sh`, `launch-orchestrator-worker-vm.sh`, `launch-sku-matrix-v2-benchmark.sh`,
> `launch-data-pipeline-fleet-monitor.sh`).
>
> **`launch-data-pipeline-fleet-monitor.sh` must NEVER be gated.** It runs the sweep that DELIVERS revocation, so
> holding it on a revocation marker would be self-locking: the fleet could not clear a hold because the thing that
> clears holds is itself held. Any future "gate everything" pass must carve it out explicitly.
>
> Two lessons, both mine this session: reading what a lib DOES beats counting who sources it (twice); and two
> overlapping sets are not complements.

- [ ] [CODE] P1. **Admission-gate coverage is 173/186 launchers — the real gap is the 8 AWS-path launchers** (measured
      2026-08-14). Only launchers routing through `setup-data-pipeline-vm.sh` → `vm-exec-with-gcs-tee.sh` get the
      admission check and the heartbeat drain poll; the 158 that use `launcher_common.sh`'s `lc_` helper get the
      LIGHTWEIGHT observability snippet, which deliberately omits the tarball+venv+heartbeat-daemon install and
      therefore has neither gate. The two sets overlap, so the honest statement is: the canonical path is gated, the
      lightweight path is not, and a per-launcher census is needed to say which real VMs are uncovered. Either add the
      admission check to the `lc_` helper (it needs no venv — it can curl the marker) or document the lightweight path
      as deliberately ungated. Repo: deployment-service.
- [ ] [CODE] P1. **The dependency-fan-out half of `targets_for_finding()` stays dormant for the non-VM findings Phase 6
      tested, not just for future emitters generally** — found 2026-08-14 by a second session reading this commit's own
      diffs before relaying "is this actually fine" back to the operator. `targets_for_finding()` needs EITHER `vm_name`
      OR `upstream_entity` to produce a target; confirmed via
      `grep -n "upstream_entity" meta_watchers.py     consolidator_scheduler_watcher.py` → zero hits. `DP-MANIFEST-001`
      (consolidator-down) and `DP-CATALOG-001` (catalogue-stale) — 2 of the 4 P0 scenarios the archived plan's Phase 6
      tests actually exercise — carry neither field in their `PipelineFinding.details` (they are not VM-lifecycle
      alerts, so no `vm_name`; `upstream_entity` is never set by either watcher). So even once every todo above ships,
      those two will resolve **zero actuation targets** in production — the VM-lifecycle family (DP-VM-001/002/003,
      which is what is actually firing live right now) will genuinely work; the fan-out family will look armed (todos
      ticked, tests green, the anti-inertness guard satisfied) but stay silently inert for these two, the exact "built ≠
      called" shape this plan already named once. Fix: have
      `meta_watchers.check_consolidator_liveness`/`check_catalogue_freshness` and
      `consolidator_scheduler_watcher.check_consolidator_scheduler_paused` stamp `details["upstream_entity"]` (the UAC
      entity name the failed check corresponds to — e.g. `"instrument-catalog"` for catalogue-stale) so
      `targets_for_finding()`'s existing `resolve_dependents()` path actually has something to resolve against. Repo:
      deployment-service.

## Progress Log

### 2026-08-14 — ARMED. The mechanism fires for the first time.

`actuate()` and `release()` both have production callers. The plan's defining defect — six green phases, every component
complete and tested, and nothing ever calling any of it — is closed.

**Shipped.** `deployment-service@cf5e041e7` (target resolver + AST guard) · `@79864746c` (arming: the call site) ·
`@375835a9a` (release bookend) · `@ad73fdf6d` (launcher-test flake) · `e2e-testing@0fe3cc520` (contrast rows).

**Three things had to be true to make the call site legal, and all three were real defects.** The actuator imported
`escalation` solely to ANNOUNCE a FLEET_HALT — one import, for alerting, inside a module whose job is delivery.
Inverting it to an injected callable was correct on its own terms and happened to be the entire blocker. `escalation.py`
was at 958/960, so the issue-doc writer moved to its own module behind a `TYPE_CHECKING`-only type import (930 now). And
the announcement went through `meta_watchers.emit_finding`, which calls `route_finding` — while running INSIDE
`route_finding`. That is re-entrant: it would have re-run revocation against the announcement. The original design
carried that edge and it never fired only because the actuator had no caller.

**`xfail(strict=True)` earned its keep.** The guard failed on PASS the moment the call site landed, which is what forced
the marker's removal in the same commit rather than letting it outlive the defect. Use strict for any guard that
documents a known-broken state.

**A grep-based guard would have been fooled by prose.** `rg '\.actuate\('` matches docstrings, so deleting the real call
would have left a comment satisfying the guard. Both guards parse AST and match `Call` nodes.

**What is NOT done, and why — none of it is "not started".**

| Item                                | State                                                                                                                                                                                                                                                                                                                                                                                     |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Live confirmation                   | **Waiting**, not work. All commits are on LDR; none has promoted to `main`, which runs `*/15`. Confirming now would confirm the OLD image. Do not dispatch the promote workflow to hurry it — ad-hoc dispatches into that shared concurrency slot cost a measured 2h+ livelock on 2026-08-07.                                                                                             |
| Lightweight-launcher admission gate | **Guardrail-blocked.** Reading the marker from a venv-free startup script needs a subprocess cloud-CLI object read, which an orchestrator guardrail bans (reads included) and QG 5.105 would fail regardless. Not circumvented; three options are in the issue doc.                                                                                                                       |
| Live-path (dependency-health)       | **Deliberately not built.** Measured: `probe_fn` has ZERO production injection sites and the built-in probes report healthy by default, so no dependency-health alert can fire at all. Registering our services would have added rows nothing can observe — coverage-shaped inaction, the same defect this plan just spent itself removing. Sequencing recorded in the issue doc instead. |

**The pattern worth carrying out of this plan.** Three separate systems here were individually complete, individually
tested, and collectively inert: the revocation actuator (no caller), the dependency-health policy (no consumer), the
health prober (no injected probe). Each passed review because each layer was genuinely finished. The cheap defence is an
anti-inertness guard per layer — assert the thing has a non-test caller — and it belongs with the component, not in a
checklist.
