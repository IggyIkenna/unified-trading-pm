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
- [x] ✅ [OPERATOR] P0. **Confirm it live after wiring** — CONFIRMED 2026-08-15. All three conditions met on
      `uts-prod-dp-exit-code-monitor` (hourly `0 * * * *`; the `*/5` in the original todo was corrected 2026-08-14). (a)
      The arming commits' CONTENT is on `origin/main` and in the live image — note SHA-ancestry is the WRONG test here,
      the LDR→main promote is a projection that rewrites SHAs, so `git merge-base --is-ancestor` reports "not promoted"
      for work that has fully landed; verify by content (`git cat-file -e origin/main:<path>`). (b) + (c) together in
      one measured line, 2026-08-15 07:20:58 UTC:
      `revocation deps_drain delivered for mdps-defi-2022-20260815-050859 -> ['vm-logs/…/DRAIN_REQUESTED.json', 'vm-census/admission-hold/….json'] (DP-VM-002)`
      — both markers written, and `deps_hold delivered for mdps-defi-` (DP-VM-001) shows prefix-family targeting working
      too. **30 distinct VMs received a delivery in 12h.** The mechanism is live and acting. Repo: deployment-service.
- [ ] [CODE] P0. **Register the 7 emitted-but-unregistered DP ids, or the revocation layer stays blind to them.**
      Measured 2026-08-15: `DP-LIVE-001/002/003/004`, `DP-VM-012`, `DP-WATCHER-005/006` are emitted by monitor source
      but appear in NEITHER closed set (`data-pipeline-alerts.registry.yaml`'s 54 ids, nor `AlertCode`), so
      `evaluate_revocation()` raises `UnknownAlertIdentityError` and `_apply_revocation` logs
      `revocation: <id> did not evaluate` and returns `{}`. **127 such rejections in 6h** on `uts-prod-dp-meta-watchers`
      alone (DP-WATCHER-006 ×68, DP-LIVE-004 ×34, DP-LIVE-001 ×15, DP-LIVE-003 ×10). This is NOT the whole mechanism
      failing — the registered ids (DP-VM-001/002) deliver correctly; it is a per-id registration gap. **The DP-LIVE
      family is the live-trading signal**, including `missing_live_producer_watcher` (DP-LIVE-003), which is the closest
      existing thing to the producer-silence trigger in `/plans/active/producer_silence_flatten_protocol_2026_08_14.md`
      — so this gap will silently swallow that plan's trigger too unless closed first. Each id needs a deliberate
      `DependentAction` (registering at `NONE` is safe and explicit; anything stronger on a LIVE code is a risk
      decision). Repo: unified-api-contracts + unified-trading-pm (registry).
- [ ] [CODE] P1. **Make an unregistered identity fail loudly at CI time, not silently at runtime.** The gap above
      survived because a `WARNING` in a Cloud Run job's logs is invisible until someone greps for it. Add a check that
      every `registry_id=` literal passed to `emit_finding()` resolves in `evaluate_revocation()`'s closed set — an AST
      sweep over the monitor source, in the same family as the anti-inertness guards. A code emitting into a policy
      layer that cannot key it is the same class of defect as a component with no caller. Repo: deployment-service.

> **CORRECTION 2026-08-15 (peer session, re-measured) — the "two layers deep" framing for DP-MANIFEST-001 was wrong,
> withdrawn.** DP-MANIFEST-001 is one of the 54 already-registered ids — identity was never its problem, and this
> session's self-scoped targeting (above) closes the rest. **What does NOT generalize, and is still bleeding**: identity
> resolution (`escalation.py:749 evaluate_revocation(...)`) is STRICTLY UPSTREAM of target resolution
> (`escalation.py:766 targets_for_finding(...)`) — an unresolvable identity raises at 749 and returns `{}` via the
> `logger.warning` at 751, so self-scoped/any targeting fix downstream can never reach an id that fails here. Latest
> measurement (2h window, `uts-prod-dp-meta-watchers`): **`DP-LIVE-004` ×38, `DP-WATCHER-006` ×13, `DP-LIVE-001` ×3,
> `DP-LIVE-003` ×2 — 56 rejections dropped on the floor** (supersedes the "127 in 6h" figure two todos up — same gap,
> later/narrower measurement window).
>
> **Ready to paste** (unified-api-contracts, `canonical/crosscutting/dependency_revocation.py`, immediately after the
> `DP-WATCHER-004` entry in `DP_FAILURE_MODE_ACTIONS`) — written and runtime-verified by the peer session, all seven
> resolve via `evaluate_revocation("DP-LIVE-001")` etc. (UAC resolves from source in the service venvs, so verification
> is immediate, no rebuild needed):
>
> ```python
>     "DP-WATCHER-005": _p(
>         _HOLD, _AGENT_URGENT,
>         "An OOM-killed consolidator IS CONSOLIDATOR_DOWN — same condition as DP-WATCHER-004 "
>         "reached by a different route, so it takes the same dependent action.",
>     ),
>     "DP-WATCHER-006": _p(
>         _NONE, _AGENT_URGENT,
>         "Generic per-execution Cloud Run Job failure, fired across the WHOLE job registry. A "
>         "single blanket action here would apply identically to unrelated job families, which is "
>         "why it is NONE rather than a guessed HOLD: the right policy is per-job and does not "
>         "exist yet. Registered deliberately so the identity RESOLVES — an unregistered id raises "
>         "and is swallowed as a log line, which is strictly worse than an explicit no-op.",
>     ),
>     "DP-VM-012": _p(
>         _HOLD, _AGENT_URGENT,
>         "A Cloud Run Service whose terminal_condition entered CONDITION_FAILED is not serving. "
>         "Hold dependents rather than launch them against a service that cannot answer.",
>     ),
>     "DP-LIVE-001": _p(
>         _HOLD, _AGENT_URGENT,
>         "A live stream blindspot means expected live shards are not arriving at all. Same shape "
>         "as DP-WATCHER-002 (never even attempted): downstream would read the absence as honest.",
>     ),
>     "DP-LIVE-002": _p(
>         _DRAIN, _AGENT_URGENT,
>         "Manifest says captured, GCS is empty — the manifest asserts data that does not exist, "
>         "so a dependent reads a hole believing it is real. This is DP-FETCH-001's condition "
>         "(absence unproven) on the live path, and takes its action: drain dependents before "
>         "they consume it.",
>     ),
>     "DP-LIVE-003": _p(
>         _HOLD, _AGENT_URGENT,
>         "A registered LONG_LIVED_LIVE producer prefix with ZERO running instances — nothing is "
>         "producing. The condition that hid a 5-week CME capture gap (deleted 2026-06-30, found "
>         "2026-08-09). Hold dependents rather than feed them a stream with no source.",
>     ),
>     "DP-LIVE-004": _p(
>         _NONE, _AGENT_URGENT,
>         "Shard alive but zero recent captures — a productivity gap, not a correctness one: "
>         "nothing false is written, so no dependent is misled (DP-WATCHER-003's reasoning). Left "
>         "at NONE also because its blast radius is unmeasured — it fired 34 times in 6h, and "
>         "arming a hold at that rate is an operator ruling, not an author's default.",
>     ),
> ```
>
> Actions are by strict analogy to already-ruled ids, never invented (e.g. `DP-LIVE-002` takes `DP-FETCH-001`'s DRAIN
> because it is the same "manifest asserts data that isn't in GCS" condition on the live path). **The two `_NONE`s are
> deliberate — do not "fix" them without an operator ruling**: `DP-WATCHER-006` fires across the whole job registry (a
> blanket action would hit unrelated families — the right policy is per-job and doesn't exist yet); `DP-LIVE-004` fires
> at a rate (38×/2h) where arming a hold is a risk decision, not an author's default. Registering either at `NONE` still
> fixes the bug on its own: the identity RESOLVES instead of raising and being swallowed.
>
> **The guard above (todo 150) — spec, from the peer session, build alongside**: AST-walk
> `deployment_service/data_pipeline_monitors/**.py`, collect every keyword argument named `registry_id` whose value is a
> string constant (17 today), parametrise a test per id, assert each `evaluate_revocation()`s without raising. AST, not
> grep — `rg 'DP-LIVE-003'` matches docstrings that NAME an id without emitting it. Include a `len(ids) >= 10`
> guard-the-guard assertion, or a renamed keyword makes the whole test suite pass vacuously (zero collected ids, zero
> failures).
>
> **This session's extension is a SECOND, independent arm, not a modification of the above** — the AST walk above can
> only ever see a `registry_id=` keyword argument; an emitter that bypasses `route_finding()` entirely (like
> `assert_consolidator_healthy`'s bare `log_event()` was, before this session's fix) has no such literal to extract, so
> the walk structurally cannot catch that failure mode. Build the second arm alongside the first, not gated on it
> landing first — it does not depend on the peer's guard existing.
>
> **Batching guidance (peer session, measured)**: the shared host's QG governor's per-repo sub-cap is NOT FIFO — a
> 42-minute wait was measured overtaken by runs aged 1:42 and 5:01, so every extra gate cycle is a fresh lottery, not a
> queue position. Finish every edit across BOTH repos (unified-api-contracts + deployment-service) first, gate ONCE over
> the whole batch, then make per-unit commits from that green tree — not gate-commit-gate-commit, which under current
> contention costs 4 waits instead of 1.
>
> **Shared-checkout note, and how this session's OWN plan edits were actually lost to it today**: slot 4's UAC and PM
> checkouts both currently hold other sessions' WIP. This session's local uncommitted edits to THIS plan file (a
> cron-host finding + a prediction-pipeline-vm.sh verification writeup, both re-applied above/below after being silently
> overwritten by an incoming `git pull` while staged-but-uncommitted — recovered from this session's own conversation
> context, not lost, but a real live instance of exactly the "stale local content" trap named earlier in this log)
> confirms: scope `--files` by name, never `git add -A`, and run `scripts/plan-hygiene/check_plan_stale_base.sh` before
> committing any plan — it is live in precommit now and catches the silent-revert case plain todo-counting misses. (If
> `test_pretooluse_slot_collision_guard.bats` fails under BATS, that is the fixed-as-of-`27979ca518` load flake, not a
> new break.)

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

- [x] ✅ [CODE] P1. **AWS-path admission gate — LANDED, deployment-service@92a550325.** Adds `lc_aws_admission_gate`
      called before `run-instances`, so a held family creates NO instance at all rather than booting one that exits 75
      after being billed — strictly better than the GCP wrapper's in-VM check. Reuses the same
      `revocation_admission_cli`, so there is ONE admission implementation and no subprocess object-storage CLI (which a
      HARD RULE bans, reads included — the earlier in-VM approach was correctly blocked by that guardrail and this is
      the better design it forced). Fail-open: no venv / no module / any rc but 75 → proceed. **A full
      `quality-gates.sh` on this exact tree passed ALL content checks.** The quickmerge re-gate was then SIGTERM'd by
      the QG governor at host load average **308** with 10 concurrent gate runs; quickmerge's own output says it:
      "Re-gate hit ONLY the duration budget — every content check passed. This is HOST CONTENTION, not your change."
      Recover: restore the blob and re-run quickmerge on a quiet host, or use the sanctioned `IGNORE_TIMEOUT=true` since
      the content is already verified green.

> **OPERATOR DECISION 2026-08-15 — migrate the lightweight `lc_`-helper launchers onto `vm-exec-with-gcs-tee.sh`**,
> rather than duplicating an admission check into the lightweight path or accepting it as permanently ungated. Removes
> the second, ungated launch path entirely instead of growing a parallel gate implementation for it.

> **CENSUS CORRECTED 2026-08-15 — the "158" figure was wrong, methodology error.** Grepping for any launcher that
> `source`s `launcher_common.sh` (162 hits) or contains the substring `lc_` (171 hits) counts launchers using ANY of its
> 20 shared `lc_*` helpers (singleton locks, tarball-pin writes, gcloud-create wrappers — used by canonical-path
> launchers too), not specifically the lightweight-observability opt-out. The actual signal is a launcher calling
> `lc_log_upload_trap_block`/`lc_log_upload_continuous_block` — the SSOT function whose own docstring names it "the
> lightweight equivalent for launchers that inline their own startup script" instead of routing through
> `vm-exec-with-gcs-tee.sh`. `grep -l 'lc_log_upload_trap_block\|lc_log_upload_continuous_block' launch-*.sh` → **12**,
> not 158. Of those 12, read in full (headers + one level of delegation):
>
> - **1 genuine migration candidate**: `launch-prediction-pipeline-vm.sh` — a real multi-stage MDPS→features backfill
>   that inlines its own startup script. This is the launcher the admission gate's threat model ("download into a
>   manifest that never updates") actually describes.
> - **2 false positives — wrapper scripts whose real data work is already gated**:
>   `launch-expected-universe-v2- historical-backfill-vm.sh` and `launch-features-sports-parallel-backfill-vm.sh` (also
>   independently DEPRECATED, superseded by `launch-features-vm.sh`, "will be archived") only use the lightweight
>   snippet for their OWN orchestrator-process observability — the actual per-chunk data downloads happen on CHILD VMs
>   launched via `launch-expected-universe-v2-vm.sh` / `launch-features-vm.sh`, both confirmed
>   (`grep -l setup-data-pipeline-vm.sh`) to already route through the canonical gated path. Migrating the wrapper would
>   gate nothing new.
> - **2 not data-capture launchers at all** — the admission-gate concept doesn't apply: `launch-planning-vm.sh` (the
>   orchestrator/dashboard infra host) and `launch-pipeline-e2e-check-driver-vm.sh` (an orchestration driver that itself
>   downloads nothing; the VMs it launches go through their own already-gated launchers).
> - **5 long-lived cron-HOST VMs, a different risk shape**: `launch-cefi-fwd-daily-cron-vm.sh`,
>   `launch-cefi-onchain-fwd-daily-cron-vm.sh`, `launch-cefi-perp-funding-daily-cron-vm.sh`,
>   `launch-tradfi-fwd-daily-cron-vm.sh`, `launch-funding-ensemble-daily-cron-host.sh`. These are ALWAYS-ON VMs that
>   fire a daily job in-place, not one-shot VMs launched fresh into a manifest snapshot — the marker-hold admission
>   model (block launch, not block an already-running host's next tick) may not fit this shape at all. Needs an operator
>   call, not a mechanical migration.
> - **2 validation harnesses**, lower urgency: `launch-aave-lending-rate-validation-vm.sh`,
>   `launch-amm-golden-fixture-validation-vm.sh` — read + compute a validation report rather than repeatedly
>   re-downloading into a stale manifest.
>
> Net: the real, currently-actionable migration scope is **one launcher** (`launch-prediction-pipeline-vm.sh`), not 158
> — no plan-split needed. The cron-host question is a separate, smaller operator decision, tracked as its own todo below
> rather than bundled into "migrate everything."

- [ ] [CODE] P1. **Migrate `launch-prediction-pipeline-vm.sh` onto `vm-exec-with-gcs-tee.sh`.** The one genuine
      lightweight-launcher migration candidate found by the corrected census above — a real multi-stage backfill (MDPS
      tick→OHLCV, features-cross-instrument, features-delta-one) inlining its own startup script instead of the
      canonical gated path. Needs its workload invocation adapted to the tarball-based CLI entrypoint model
      `setup-data-pipeline-vm.sh` expects, then a real VM launch verified end-to-end (boot, admission-gate check,
      workload completion) per the VM-launcher runbook's no-fire-and-forget rule — not a blind find/replace. Repo:
      deployment-service. **2026-08-15 — CODE WRITTEN + LIVE-VERIFIED, NOT YET SHIPPED (uncommitted local diff — held
      deliberately this session, re-typed here after the working copy was silently overwritten by an incoming pull
      mid-session; see the shared-checkout note above).** New `elif [[ "$VM_TASK" == "prediction-pipeline" ]]` branch in
      `setup-data-pipeline-vm.sh` (writes a runner script mirroring the launcher's original 3-stage per-date loop, then
      `_launch_with_tee`s it — inherits the admission-gate check + drain poll for free);
      `launch-prediction-     pipeline-vm.sh` rewritten to drop its own bespoke tarball build (now installs from the
      centrally-built tarballs via compound `VM_SERVICE=market_data_processing_service+features_service`, same pattern
      `launch-mdps-features-live.sh` already uses) and route through the canonical `setup-data-pipeline-vm.sh` path.
      `bash -n` clean, `shellcheck --severity=error` clean (the exact check `test_shellcheck_no_errors` runs). **Real
      1-day smoke VM launched and verified** (`prediction-pipeline-smoke-test`, 2026-08-01 range): confirmed via
      `gcloud compute instances describe --format=json(metadata)` that VM_TASK/VM_SERVICE/dates landed correctly, and
      via the VM's own `run.log` (read through UTL's `download_from_storage` — subprocess `gsutil` is guardrail-blocked
      for ad-hoc reads too, not just committed code) that the NEW dispatch branch fired
      (`bash /home/ikennaigboaka/workspace/prediction_pipeline_loop.sh`, not the old generic-fallback's
      `python -m     market_data_processing_service+features_service` literal-module-path bug), STAGE 1 started, and the
      real MDPS CLI connected to GCP, listed 2259 real trade files for 2026-08-01, and loaded 174,501 real prediction
      instruments before legitimately blocking on a live consolidator-merge lock (documented, expected behavior). No
      `admission HELD` — expected, nothing currently holds the prediction asset_group; proves the wiring reaches the
      gate, not that the gate blocks (needs a live hold to observe, out of scope for a smoke test). **Real trap hit and
      fixed along the way**: a `run.log` read right after re-launching returned the PRIOR failed attempt's content
      byte-for-byte (same-looking `deployment_id`, made it look like nothing had changed) — the GCS blob PERSISTS from a
      prior run until the new run's `heartbeat_daemon.py` uploader overwrites it, so an early read after relaunch can
      silently return stale evidence; always cross-check `deployment_id`/instance `creationTimestamp` before trusting
      log content as "this run's". **Remaining before shipping**: run the full `quality-gates.sh` (deferred this
      session, not yet run on these 2 files — batch it with the UAC/guard work above per the peer's QG-sweep guidance),
      quickmerge, then flip this checkbox with the real commit sha.
- [x] ✅ [OPERATOR] P2. **Marker-hold admission model applies to long-lived cron-HOST VMs — VERIFIED ALREADY SATISFIED,
      no code change needed.** Traced all 5 cron-HOST launchers' (`launch-cefi-fwd-daily-cron-vm.sh` + 4 siblings)
      actual daily trigger: none run the data work in-place on the host. Each cron.d entry `bash`-invokes a SEPARATE
      child launcher fresh every day (`cefi-fwd-daily-cron` → `launch-cefi-forward-poll.sh`;
      `cefi-onchain-fwd-daily-cron` → `launch-cefi-onchain-forward-poll.sh`; `cefi-perp-funding-daily-cron` →
      `launch-features-vm.sh`; `tradfi-fwd-daily-cron` → `launch-tradfi-forward-poll.sh`;
      `funding-ensemble-daily-cron-host` → `launch-funding-ensemble-paper-cron-vm.sh`), and every one of those 5 child
      launchers already sets `startup-script-url=gs://.../setup-data-pipeline-vm.sh` (confirmed via
      `grep -l setup-data-pipeline-vm.sh` on each) — the SAME canonical path whose shared `vm-exec-with-gcs-tee.sh`
      wrapper runs the admission check unconditionally for every `VM_TASK` branch (by design: "wired into the shared
      wrapper... so a new launcher cannot forget to opt in", `revocation_admission_cli.py`'s own docstring). The
      cron-HOST VM itself correctly uses the lightweight snippet (it does no data work, just idles + fires cron — the
      earlier census's read on it was right); the actual work each day is already admission-gated, one layer down. Repo:
      unified-trading-pm (decision, this entry) — no deployment-service change needed.
- [x] ✅ [CODE] P1. **`DP-CATALOG-001` (catalogue-stale) now stamps `upstream_entity`.** —
      **deployment-service@2cc79b2a7c.** `meta_watchers.check_catalogue_freshness` now sets
      `details["upstream_entity"] = "instrument-catalog"`, the registered UAC entity type
      (`unified_api_contracts.instruments_preflight_dag`, `upstream_entity_type="instrument-catalog"` at 2 call sites).
      `DP-CATALOG-001`'s policy is `_HOLD`/`_AGENT_URGENT` ("Catalog not running... Hold admission" —
      `dependency_revocation.py`), so this closes a real dormant path: `route_finding()` was already reached, the policy
      already said HOLD, only the target resolution was empty. Test updated (`test_catalogue_stale_emits_critical` now
      asserts the stamped field). Repo: deployment-service.

> **OPERATOR DECISION 2026-08-15 — `DP-MANIFEST-001`/`DP-WATCHER-004` resolve SELF-SCOPED, no UAC entity-graph
> registration.** Verified topology first: each manifest-consolidator instance maps 1:1 to one
> `(asset_group, market-data|instruments)` pair (`_BUCKET_PREFIX_TO_SCHEDULER_KEY_KIND` × `_KNOWN_ASSET_GROUPS` in
> `consolidator_liveness.py`) — it is not a fleet-wide shared surface the way `dependent_asset_groups()`'s own docstring
> speculatively describes. A stale consolidator only ever needs to hold its OWN asset_group's launches, the same shape
> as a dead VM holding its own family. Registering `"manifest-consolidator"` as an `upstream_entity_type` in UAC's
> `instruments_preflight_dag.py` was rejected: cross-repo, and it would stretch that graph's meaning (which today means
> "this admission-gate check requires entity X fresh") to cover something that isn't a per-preflight-trigger dependency
> at all. **Wiring reuses UTL's existing reader** — `consolidator_liveness.py`'s per-bucket stale/paused-reason logic
> (`REASON_SCHEDULER_PAUSED` / `REASON_HEARTBEAT_STALE`) is already built and tested; deployment-service's sweep calls
> it and wraps the result into a `PipelineFinding`, rather than re-deriving staleness from scratch a second time.
> deployment-service already depends on UTL everywhere, so this is the normal dependency direction, not a new one.

- [x] ✅ [CODE] P0. **Wire `DP-MANIFEST-001` into `route_finding()` by reusing UTL's consolidator-liveness reader.** —
      **deployment-service@e766285059.** New `consolidator_heartbeat_watcher.py` calls
      `ConsolidatorLivenessMonitor.check()` (the read-only per-bucket probe, NOT `.check_and_emit()` — avoids
      double-emitting through UTL's own `log_event()` channel) for both `market_data_bucket`/`instruments_store_bucket`
      per asset_group, and emits `PipelineFinding(registry_id="DP-MANIFEST-001", ...)` through
      `meta_watchers.emit_finding` (the PUBLIC alias — `_emit` directly would have tripped basedpyright
      `reportPrivateUsage` and pushed the ratchet from 1259→1260, caught by running `--lint` separately while the shared
      host's memory pressure blocked `--test`). **One deviation from the plan as written**: `tier=AUTO_RECOVER`, not
      `PAGE_OPERATOR` — matches the codex table's own "auto-recover (re-merge) then page" and reuses the SAME
      `_recover_consolidator` actuator `consolidator_oom_watcher` already wires (no `details["oom"]` here, so the
      relaunch stays same-tier). Mirrors `check_catalogue_freshness`'s consecutive-miss gate. Wired into `cli.py`'s
      sweep. Tests: 4 new (`test_consolidator_heartbeat_*`). Repo: deployment-service.
- [x] ✅ [CODE] P0. **Add self-scoped `asset_group`-only target resolution to `targets_for_finding()`.** —
      **deployment-service@e766285059.** New `elif` branch in `targets_for_finding()` (admission-scoped actions only —
      DEPS_DRAIN excluded, matches the operator's target-granularity ruling since asset_group-only has no VM to drain):
      resolves via `prefix_families_for([asset_group.value])` when no `vm_name`/`upstream_entity` is given.
      `consolidator_scheduler_watcher.check_consolidator_scheduler_paused` now stamps `details["asset_group"]` via a
      reverse-lookup against `meta_targets.consolidator_scheduler_job`/`consolidator_instruments_scheduler_job` (name
      construction, not string-parsing — can't drift from the real naming convention), closing DP-WATCHER-004 too. **A
      second, adjacent bug found while wiring this**: `escalation._apply_revocation()` never threaded `asset_group`
      through to `targets_for_finding()` AT ALL — meaning the already-shipped DP-CATALOG-001 fix
      (`deployment-service@2cc79b2a7c`) was fanning out FLEET-WIDE (`asset_group=None` → every dependent asset_group)
      instead of scoped to the specific AG whose catalogue was actually found stale. Fixed in the same commit:
      extracts + safely converts `details["asset_group"]` (degrades to `None` on an unrecognised value, never raises).
      Tests: 2 new for the threading fix, 2 for the self-scoped path, 1 for the fan-out-vs-self-unit precedence. Repo:
      deployment-service.

## Progress Log

### 2026-08-14 (later) — `DP-CATALOG-001` armed; `DP-MANIFEST-001` found to be a deeper gap than the todo it replaces claimed.

Picked up the open "dependency-fan-out stays dormant" P1. On implementing it, the todo's own premise was wrong on two
points, found by reading the actual production code instead of trusting the prior session's grep:
`meta_watchers.check_consolidator_liveness` never existed under that name, and `DP-MANIFEST-001` does not reach
`route_finding()` at all today — it is emitted by `assert_consolidator_healthy` in **unified-trading-library**
(`monitors/consolidator_liveness.py`) via UTL's bare `log_event()`, a different channel (event-log spine) with no
`PipelineFinding`, confirmed by `grep -rn 'registry_id="DP-MANIFEST-001"' deployment_service/` → zero hits outside
tests. Fixed what was real and re-scoped what wasn't:

**Shipped: `deployment-service@2cc79b2a7c`.** `check_catalogue_freshness` (DP-CATALOG-001, genuinely reaches
`route_finding()`, policy is `_HOLD`/`_AGENT_URGENT`) now stamps `details["upstream_entity"] = "instrument-catalog"` —
the one registered UAC entity type this alert corresponds to. Test updated to assert the field. Gate green (`--test`,
315s; `--fast`, 379s).

**Re-scoped, not fixed: `DP-MANIFEST-001`.** The operator's own named "money-burn" scenario has TWO independent
problems, not one missing field: (1) no production `route_finding()` call site exists for it at all — UTL's
`log_event()` path never reaches deployment-service's escalation system; (2) even a wired emitter would resolve zero
fan-out targets, because `"manifest-consolidator"` is not a registered `upstream_entity_type` in
`unified_api_contracts.instruments_preflight_dag` (only `fixtures`/`teams`/`instrument-catalog`/
`canonical_question_group_registry`/`instruments` are registered). `DP-WATCHER-004` (accidental scheduler pause, same
`_HOLD` policy) DOES reach `route_finding()` but hits problem (2) identically. This needs an operator call between two
real designs (register the entity in UAC vs. give deployment-service its own non-OOM consolidator-heartbeat watcher) —
written up as its own P0 todo above rather than silently patched with a no-op stamp, which would have reproduced this
plan's own headline lesson ("built ≠ called") on the operator's highest-named-priority scenario.

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

### 2026-08-15 — two traps worth not re-learning

**Prettier reformats conflict markers into valid markdown, defeating a naive grep.** A stash-pop conflict in this file
left a seven-angle-bracket "Stashed changes" marker, which prettier rewrote into a markdown blockquote by putting a
space between every bracket. An anchored grep for the raw marker then reported **zero markers** on a file that plainly
had them, and I relayed that "0 markers" result as fact. The repo's own `scripts/plan-hygiene/check_conflict_markers.sh`
catches it because it normalises whitespace first. Use it; do not hand-roll the check. Downstream cost of the false
negative: the resolution kept BOTH the flipped and unflipped copies of one todo, so the plan briefly claimed the AWS
gate was simultaneously landed and not landed.

**The stale-local-content trap is real, and `check_todo_regression.sh` is what catches it.** This slot's copy of this
plan was ~16h stale. A peer session had, in the meantime, both FIXED the catalogue-stale `upstream_entity` gap and filed
a far deeper P0 todo tracing `DP-MANIFEST-001` to `assert_consolidator_healthy` in unified-trading-library (it calls
bare `log_event()`, never reaches `route_finding()`, so that alert has no production call site at all — and
`"manifest-consolidator"` is not even a registered `upstream_entity_type`). Editing the stale copy and pushing would
have silently reverted both, with **no conflict signal** — exactly what CLAUDE.md's "full-file staging overwrites, not
merges" warns about. The todo-regression check flagged `origin=9 current=8` and stopped it. Two rules earned here:
`git diff origin/<branch> -- <path>` BEFORE pushing an edited plan, and treat a todo-count drop as a real loss until
proven otherwise.

**Corollary on inheriting a dead session's WIP.** The 16h-stale local edit was correctly inheritable by the liveness
rule, and inheriting it would still have been wrong — because "not actively held" is not the same as "still accurate".
Verify an inherited finding against the CURRENT origin before committing it: two of that note's three specifics had
already been overtaken.
