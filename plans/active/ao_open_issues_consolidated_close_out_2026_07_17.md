---
doc_type: plan
title:
  AO open-issues consolidated close-out — one local plan for every still-open agent-orchestrator issue doc, each item
  re-verified against code + the live planning-VM before inclusion
summary: |
  2026-07-17 operator-session sweep of the 10 open AO issue docs — every doc's claims re-verified against the current
  LDR code AND the production orchestrator on the planning VM (read-only SSM — live state.db, activity_log, process
  table, clone freshness) before a todo was admitted here. Measured live state at authoring — clones fresh (AO + PM
  behind=0, clean); churn much improved post-R1 (24h — 184 autospawns / 154 dispatched / 27 done vs the pre-fix
  1014/217/101) but 96 tmux_session_lost + 158 worker_polling_dead per day keeps the worker-lifecycle class hot; ~10
  orphaned claude processes alive right now (16 claude procs vs 4 live tmux sessions, incl. the 3 PIDs the
  orphaned-workers doc named and one fully-detached PPID-1 tree); audit_false_done reports **2 LIVE false-done rows**
  (sports_cf8…-001/-002 — real UTL fixes shipped 07-13/14, plan checkboxes never flipped; both predate the @86b8b8b
  gate so they are legacy poison, not a gate bypass); l2_book…-005/-007 STILL absent from the tasks table while their
  plan todos are open; the mvp-defi park is HOLDING (yaml priority 999); brief_hash NULL tail now 54 (moves). This plan
  is the single execution vehicle: each todo cites its source doc, and each source doc's archival is gated on its todos
  here. LOCAL track — operator-driven, never dispatched.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, deployment-ui]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    dispatch,
    backlog,
    regen,
    worker-lifecycle,
    orphan-process,
    auto-park,
    observability,
    consolidation,
  ]
related:
  [
    issues/ao_skip_blind_spawn_budget_phantom_churn_2026_07_15.md,
    issues/orchestrator_concurrent_qg_saturation_and_dispatch_divergence_2026_07_17.md,
    issues/orphaned_workers_on_tmux_loss_stale_dispatch_2026_07_17.md,
    issues/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md,
    issues/mvp_backfill_defi_v10_002_dispatch_thrash_2026_07_16.md,
    issues/regen_positional_task_ids_not_content_stable_2026_07_17.md,
    issues/ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16.md,
    issues/ao_residuals_after_dispatch_hardening_2026_07_17.md,
    issues/ao_recovery_audit_layer1_deleted_2026_07_15.md,
    issues/ao_docs_reconciliation_2026_07_15.md,
    qg_host_adaptive_resource_governor_2026_07_14.md,
    ../epics/orchestrator_master.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  - "operator 2026-07-17 — 'for all the remaining issues check which are live vs resolved … for all the relevant open
    issue docs create ONE plan, local execution'"
  - "Live verification sweep this session: code at agent-orchestrator@6a30e45 / pm@bf2fbcfc5; production probe via
    read-only SSM on i-0c9b283b31d6b5ca7 (state.db mode=ro, activity_log 24h, ps/tmux, audit_false_done.py)"
---

# AO open-issues consolidated close-out

> **Human plan — operator session executes it** (`assigned_vm: NA`, never ingested). ONE plan for the whole remaining
> AO-issue pile so nothing needs rediscovering. Every todo below was admitted only after re-verifying its source doc's
> claim against current code AND the live VM — the classification table is the evidence record. Code ships via
> `quickmerge.sh --agent --files`; each shippable unit flips its todo here AND updates its source issue doc in the same
> turn; a source doc archives (5-step ritual) when its last todo here lands.

## Verified classification of the 10 open docs (2026-07-17, this session)

| #   | Issue doc                                         | Verdict                                                | Evidence (measured this session)                                                                                                                                                                                                                                                                                                                                                                                |
| --- | ------------------------------------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `ao_skip_blind_spawn_budget_phantom_churn`        | **PARTIAL** — churn fixed, visibility half open        | R1 `ao@7baeedc`+`bf9a61b` on LDR; 24h spawn:dispatch now 184:154 (was 1014:217). No auto-park anywhere in `server/` — the silent-stuck class is live.                                                                                                                                                                                                                                                           |
| 2   | `orchestrator_concurrent_qg_saturation…`          | **LIVE** — nothing shipped                             | No QG throttle in `dispatch.py`/`autospawn.py` (grepped). Governor on the VM was `MODE=token K=2` (owned by `qg_host_adaptive_resource_governor`, NOT this plan).                                                                                                                                                                                                                                               |
| 3   | `orphaned_workers_on_tmux_loss_stale_dispatch`    | **LIVE** — both defects                                | Defect B measured NOW: 16 claude procs vs 4 live tmux; the 3 named PIDs (294936/1934909/1863748) still alive after ~4h + a detached PPID-1 tree. Defect A: requeue-on-dead exists since `ao@5b07bd3` but the resume-pending branch strands tasks (the 07-17 incident path); no `stale_dispatch_reclaimed` invariant exists. Right-now dispatched=2 both live (clean instant, hot class: 96 session-losses/24h). |
| 4   | `backlog_task_done_status_diverges…`              | **RESOLVED-CODE, 2 poisoned rows found by THIS audit** | `_diff_flips_checkbox` live in `verify.py:527`; all 4 fix commits on LDR + deployed (clone behind=0). `audit_false_done`: **false_done=2** — `sports_cf8_available_at_backfill_regression-001/-002`, done_shas = real UTL fixes (07-13/14, PREDATE the gate) → legacy poison, not a bypass.                                                                                                                     |
| 5   | `mvp_backfill_defi_v10_002_dispatch_thrash`       | **PARTIAL** — park holding                             | yaml `priority: 999` live on `-001`. Open: unpark wiring; the ID-shift park-loss defect (converges with #6); auto-park design (converges with #1).                                                                                                                                                                                                                                                              |
| 6   | `regen_positional_task_ids_not_content_stable`    | **LIVE** — nothing shipped                             | `_make_task_id` positional at `regen_backlog_from_plan.py`; NULL-hash tail measured 54 (was 56, moves); 0 non-done NULL rows (confirmed again).                                                                                                                                                                                                                                                                 |
| 7   | `ao_service_clone_frozen_by_untracked_checkpoint` | **PARTIAL** — root cause fixed, alerting open          | Service + PM clones behind=0 clean (measured). ff-pull streak alert still fires only when EVERY repo is dirty (read the script) — single-frozen-clone still silent. hk-host repos all behind=0 today.                                                                                                                                                                                                           |
| 8   | `ao_residuals_after_dispatch_hardening`           | **LIVE** — 5 open todos                                | l2_book-005/-007 STILL absent (only 4 rows, all done — re-measured). `ORCHESTRATOR_DB_PATH` gap bit AGAIN this session (audit tool needed explicit `--db`). Two items externally blocked (paused plan / awaiting design).                                                                                                                                                                                       |
| 9   | `ao_recovery_audit_layer1_deleted`                | **OPEN by operator ruling**                            | Ruling B (re-home producer), sequenced LAST after AO correctness work. Consuming half live, mock-fed.                                                                                                                                                                                                                                                                                                           |
| 10  | `ao_docs_reconciliation`                          | **LIVE tracker** — needs close-out pass                | Tiers 1–6 partially applied piecemeal across later sessions; which tiers actually landed has never been re-verified in one pass.                                                                                                                                                                                                                                                                                |

Docs checked and deemed AO-relevant: all 10. Other open issue docs in `plans/active/issues/` (sports/cefi/defi/etc.) are
NOT AO and are deliberately out of scope here.

## Todos

### Phase 0 — DB-state corrections (no code, operator-gated live changes)

- [ ] [BACKEND] P0. **Reopen the 2 live false-`done` rows found by this session's audit** —
      `sports_cf8_available_at_backfill_regression-001` (`done_sha=utl@f5f15e3a`) and `-002` (`utl@0f55cc2b`). Both
      done_shas are REAL UTL fixes whose plan checkboxes (`sports_cf8…_2026_07_13.md:348` and `:856`) never flipped;
      both predate the `@86b8b8b` checkbox-flip gate, so this is legacy poison the 07-16 sweep missed (they were likely
      UNAUDITABLE then; regen backfilled their `brief_hash` since). **OWNERSHIP (operator 2026-07-18): the underlying
      work is NOT AO's — it lives in `sports_cf8_available_at_backfill_regression_2026_07_13.md` (status: open, epic
      `mtds_mdps_master`, role `data_engineering`). The "is the work genuinely done" verdict + the checkbox flip belong
      to that plan's owner, not this AO plan.** The two rows: `-001` (`:348`) is a `[ ]`-open DATA re-emit task while
      the backlog row shows `done`; `-002` (`:856`) is a `[x]`-DONE BACKEND task the audit only flags because the cited
      `done_sha` isn't the commit that flipped the checkbox. AO scope here shrinks to: notify the sports/data owner to
      verify + flip (or reopen), then RE-RUN the audit. **Gate**: `audit_false_done.py --db … --pm …` reports
      `false_done: 0` after the sports owner's ruling is applied; the per-row decision is recorded on
      `backlog_task_done_status_diverges…`. Source: doc #4 + this session's probe.
- [ ] [BACKEND] P1. **Close doc #4 (`backlog_task_done_status_diverges…`) for real.** Its todos are all `[x]` and it
      left `status: open` awaiting "an independent skeptical audit" — this session's audit found the 2 rows above, so
      the doc closes only after Phase-0 todo 1 lands. Also record the corollary amendment: the "no periodic sweep
      needed" ruling holds for the gated mechanism, but the UNAUDITABLE→auditable transition (regen backfilling
      `brief_hash` onto a legacy row) can SURFACE old poison at any time — so `audit_false_done.py` runs once per
      close-out/audit session (cheap, already scripted), not on a cron. **Gate**: doc flipped `resolved` + `resolved_by`
      filled + archived per ritual.

### Phase 1 — backlog/regen integrity (code)

- [ ] [BACKEND] P1. **Sibling-reset guard: never silently recycle a `done` row.** `bootstrap.py` brief_hash-mismatch
      reset must refuse to reset a row that is `done` with a `done_sha`, logging an ERROR naming both briefs (a done row
      is audit history). Unit test where a done row's id is claimed by a different brief → row SURVIVES + error emitted;
      bug-inject to prove the test bites. Source: doc #6 todo 2. **Gate**: test green + bug-injection proof.
- [ ] [BACKEND] P1. **Hand-tuned-field preservation across positional-ID shift.** The regen preserves
      `priority`/`priority_override`/`prereqs.prerequisites` keyed by task id — an id shift (sibling completes →
      suffixes renumber) silently drops a park (measured: the mvp-defi park was lost exactly this way on 07-17,
      re-applied under `-001`). Key the preservation by `brief` (the same key the reconcile path already uses), not by
      id. Regression test: park a task, remove a sibling todo, regen → park survives under the new id. Source: doc #5
      fix-todo 3 (the NEW [CODE] P1). **Gate**: test green; the live park survives the next real regen tick after a
      todo-count change.
- [ ] [BACKEND] P2. **Bound the NULL-`brief_hash` tail (54 rows, all `done`).** Decide + implement ONE of: backfill from
      `git show <done_sha>:<plan_ref>` where recoverable; age the exemption out (no in-flight NULL rows exist —
      re-measured 0 this session); or accept permanently with the WHY in the docstring + a growth alarm (growth =
      backfill regression, the real signal). Do NOT blanket-reset. Source: doc #6 todo 1. **Gate**: the doc's stated
      gate — count 0, or recorded decision + growth check.
- [ ] [BACKEND] P2. **Explain the l2_book absent rows.** `l2_book…-005/-007`: plan todos open (`BLOCKED-*` markers) on
      an ingested plan, no task rows (re-measured: only 4 l2_book rows, all done). Trace whether the orphan-GC pruned
      them (correct-ish: `BLOCKED-*` todos are non-dispatchable by design and SHOULD have no row — if so, record that as
      the designed behaviour and make `regen`/docs say it explicitly) or whether regen re-derives them under other ids.
      **Do NOT close by re-reopening** (decayed twice). Source: doc #8 todo 5. **Gate**: doc #8's stated gate — a
      recorded explanation, and either correct rows or a recorded by-design decision.
- [ ] [BACKEND] P2. **`audit_false_done` false-positive class — the AO/regen lesson from studying the sports rows.**
      (Operator 2026-07-18: the sports work itself is its owner's; but any AO/regen improvement surfaced by studying it
      belongs here.) `sports_cf8…-002`'s plan checkbox IS already `[x]` — the audit flags it ONLY because the row's
      cited `done_sha` isn't the commit that flipped the checkbox. Decide the intended contract: should
      `audit_false_done` / `verify.check_plan_flip` treat a checkbox that is currently `[x]` as HONEST regardless of
      which commit flipped it (checkbox state = truth), or must the `done_sha` itself be the flip-commit (provenance =
      truth)? A "checkbox `[x]` but wrong sha" false-positive pollutes the gate's signal. Trace both consumers, pick the
      rule, and make the audit + the done-gate agree on it. Source: sports_cf8 study, this session. **Gate**: a recorded
      decision; `audit_false_done` no longer flags an already-`[x]` row whose work is genuinely complete (or explicitly
      does, by ruling, with the reason documented).

### Phase 2 — worker lifecycle (code)

- [ ] [BACKEND] P1. **Orphan-process reap (Defect B) — the biggest live bleed.** ~10 orphaned `claude` workers are alive
      right now on the VM (16 procs vs 4 live sessions; 3 are the doc's named PIDs, ~4h old, one tree fully detached at
      PPID 1), burning CPU + account budget and racing re-dispatched work. Implement BOTH halves: (a) the TmuxPruner
      kills the worker process tree whose slot config-dir maps to a dead/absent session (match by
      `claude_session_id`/config dir, never by name-grep alone); (b) a periodic orphan sweep (config-dir → PID → slot
      liveness) catching residue incl. PPID-1 trees. Guards: never kill a PID belonging to a live session; **honor
      `boot_grace_seconds` — NEVER reap a slot's process inside its fresh-spawn grace window (a booting worker's tmux
      session isn't registered yet; this is the exact 6/6-AutoSpawn-workers-killed-56-120s-post-spawn incident class —
      config.py boot_grace_seconds exists precisely for this)**; dry-run mode; log every kill with slot + PID + age.
      Source: doc #3 Defect B. **Gate**: the doc's regression — simulated `tmux_session_lost` leaves zero detached
      claude processes for that slot; live sweep on the VM reports 0 orphans (one-time cleanup of the current ~10
      included).
- [ ] [BACKEND] P1. **Stale-dispatch invariant (Defect A, resume-path aware).** The pruner's requeue (`ao@5b07bd3`)
      already releases on a "requeue" verdict, but a `resume-pending` verdict keeps the task bound — and when the resume
      never happens (07-17 incident: slots went `killed` holding tasks), nothing reconciles. Add the reconciler
      invariant: a task `dispatched` to a slot with `worker_alive=false` AND `tmux_session IS NULL` for > one pruner
      tick beyond `resume_attempts` exhaustion → auto-release + `stale_dispatch_reclaimed` activity event. Must NOT
      fight the resume path — only fire after resume is exhausted/impossible. Source: doc #3 Defect A + doc #2
      symptom 1. **Gate**: doc #3's regression test; live `dispatched` count equals live-worker-held count across a 24h
      window (spot-checked); **AND an explicit no-double-dispatch assertion — a task released by this invariant is NEVER
      simultaneously live on a resumed worker. The release fires strictly AFTER `resume_lifecycle` marks resume
      exhausted/impossible (order the two so the same task can never reach two agents); test the exact race (resume
      in-flight when the invariant tick fires → invariant defers, no release).**
- [ ] [INFRA] P3. **Root-cause the 96/day `tmux_session_lost` rate** (or record it as accepted churn). The 07-17
      incident was 5 losses in one second (backend/tmux blip); today's rate is 96/24h with 158 `worker_polling_dead`.
      Either find the driver (backend restarts? host pressure? tmux server?) or record the rate as expected with the
      lifecycle machinery absorbing it. Source: doc #3 timeline + this session's measurement. **Gate**: a named cause
      with evidence, or a recorded accepted-churn decision with the measured baseline.

### Phase 3 — spawn/park visibility (code + policy)

- [ ] [BACKEND] P2. **Durable auto-park for fleet-skipped tasks (the visibility half R1 exposed).** R1 made
      fleet-skipped tasks count 0 toward the spawn budget — which silenced the churn but also the SIGNAL (nothing tells
      anyone the task is stuck). Auto-park at ≥N distinct within-TTL skips carrying a `BLOCKED|PARKED|GATED` reason via
      the durable `priority_override`/false-prereq recipe (`ao@8dd5763`), WITH an unpark path when the condition clears,
      and an operator-visible surface (activity event + dashboard flag — the same class as `needs_operator_count`). This
      closes doc #1's last todo AND doc #5's auto-park design todo in one mechanism. **DEPENDS ON Phase-1
      preserve-by-`brief` (Phase 1 todo 2): an id-keyed park is silently dropped on the next id-shift regen, so
      auto-park is NOT durable until that lands — sequence Phase 1 first.** **Park = the ≥N-skips escalation of the ONE
      fleet-scoped cooldown store built in Phase-6 (blocked-task cooldown); reuse that store, do not build a second
      park-specific cooldown.** Sources: doc #1 todo 2, doc #5 fix-todo 3(design). **Gate**: a fleet-skipped task
      auto-parks with a visible reason; clearing the condition unparks it; test-pinned.
- [ ] [ADMIN] P2. **Wire the mvp-defi unpark.** `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` (still
      `false`) must be flipped by whoever lands the seed-chain/backfill progress (`data_completion_defi_2026_07_15`'s
      owner), or the park outlives its reason. Add the pointer on that plan + a line in the park's prereq description
      naming the flipper. Source: doc #5 fix-todo 2. **Gate**: the owning plan carries the flip instruction; condition
      documented.

### Phase 4 — infra/ops hardening

- [ ] [INFRA] P1. **State home = ONE in-repo source (`data/state/`); drop the two-places + the env overrides.** The
      wrong-DB GC incident + THREE bitten diagnostic sessions were the "one concept, two places" footgun:
      `ORCHESTRATOR_DB_PATH`/`ORCHESTRATOR_STATE_JSON` are set in the systemd unit (→ `/var/lib/orchestrator/…`, out of
      repo) while `config.py`'s default is in-repo `data/state/…`, so a CLI tool run as `ubuntu` without the unit env
      resolves the WRONG path. Operator ruling 2026-07-18: **keep AO backend state IN the repo, one definition, no
      duplicate var.** Resolution: make `config.py`'s in-repo `data/state/{state.db,state.json}` the SINGLE SSOT —
      REMOVE the unit `Environment=ORCHESTRATOR_DB_PATH/STATE_JSON` lines + `ReadWritePaths=/var/lib/orchestrator`, and
      stop setting those vars anywhere (the default IS the path → nothing to duplicate; service + CLI agree). ⚠️ **This
      reverses the deliberate `/var/lib` redeploy-wipe protection** — so it becomes a HARD requirement that the deploy
      path preserve state instead: `ao-self-pull.sh` + any redeploy/re-clone MUST NEVER `git clean -x` / wipe
      `data/state/` (it is gitignored → a bare FF-pull is already safe; the guard is against `clean -fdx` + fresh
      clone), and the SnapshotLoop S3/GCS archive stays the DR fallback. Migration (operator-gated, live): move the
      running `/var/lib/orchestrator/*.db` → `data/state/` on the VM, then restart. Source: doc #8 todo 2 + operator
      2026-07-18. **Gate**: `config.db_path()` as `ubuntu` with no env prints the in-repo path; service + a CLI audit
      tool resolve the SAME db; a simulated redeploy (FF-pull + `git clean -fd`) leaves `data/state/` intact.
- [ ] [INFRA] P2. **Duplicate-purpose env-var sweep (verify-consumer-then-remove).** Audit 2026-07-18: (1)
      `ORCHESTRATOR_OPERATOR` is written `= ORCHESTRATOR_VM_ID` by `bootstrap_vm.sh` on every host, but
      `host_operator()` already DERIVES operator from `vm_id` when unset → pure redundancy; stop writing it in bootstrap
      (keep the field as an optional override). (2) `ORCHESTRATOR_DB_PATH`/`STATE_JSON` two-places — folded into the
      state-home item above. (3) CHECKED & **KEEP** — `GOOGLE_CLOUD_PROJECT` vs `GCP_PROJECT_ID` are NOT a removable
      duplicate: the former is a Google-SDK standard the client reads directly, the latter is workspace canon (`auth.py`
      reads `google_cloud_project or gcp_project_id` — different consumers). (4) CHECKED & **KEEP** — the
      `WORKSPACE_ROOT`/`UNIFIED_TRADING_WORKSPACE_ROOT`/`ORCHESTRATOR_WORKSPACE_ROOT` trio is deliberately separate
      (own-config vs ambient passthrough, documented in `config.py`). **Gate**: `OPERATOR` no longer written by
      bootstrap + a host with only `VM_ID` set resolves the same operator; keep-decisions recorded in ENV_VARS.md.
- [ ] [INFRA] P2. **Per-repo freeze-streak alert in `slot-cron-ff-pull.sh`.** Verified still absent: the dirty-streak
      WARN fires only when EVERY repo in a sweep skips — a single frozen clone (the exact 2-day outage mode) stays
      silent. Make the streak per-repo (repo X `[skip:dirty]`/`[skip:ff-failed]` N consecutive ticks → WARN naming the
      repo). NOTE (operator 2026-07-18): the "UI surface" agent doc #7 mentioned is a DIFFERENT scope — the backlog
      details pop-up (what tasks exist, their prerequisites, how tasks/plans connect) — and has not started (UI design
      not final). It does NOT cover this, so this is a standalone task with no cross-agent dependency. **SURFACE
      (operator 2026-07-18): NOT a Slack alert — feed the per-repo/per-slot freeze signal into the `deployment-ui` FLEET
      TAB (where clone/slot status is already shown) so a SINGLE stuck repo on a SINGLE slot is obvious at a glance, and
      improve that page to make the state easy to check on demand.** So the work spans two repos: (1)
      `agent-orchestrator` `slot-cron-ff-pull.sh` emits a per-repo/per-slot freeze-streak signal (behind-origin N
      consecutive ticks); (2) `deployment-ui` fleet tab renders it (per repo × slot, not one global flag). Source: doc
      #7 todo 3 + operator 2026-07-18. **Gate**: a deliberately-frozen single clone shows as stuck in the deployment-ui
      fleet tab within N ticks (naming the repo + slot).
- [ ] [INFRA] P2. **Fleet-wide frozen-clone sweep.** hk-host root repos measured behind=0 today, but the VM's SLOT
      clones + any other hosts were not swept. One pass: every host's root + slot clones, `HEAD..origin/LDR > 0` with
      untracked-only dirt → unfreeze (plain FF, per the doc's recipe). Source: doc #7 todo 4. **Gate**: sweep output
      recorded; zero frozen clones remain.
- [ ] [INFRA] P2. **Dispatch-time full-QG throttle (coordinate, don't duplicate).** The shared-host "≤2 full QG" cap is
      unenforced at dispatch — 4-6 concurrent full-QG pytests saturated the VM on 07-17 (doc #2). The RAM/CPU admission
      governor (`qg_host_adaptive_resource_governor_2026_07_14`, active P1) is the natural enforcement point but was
      measured `MODE=token K=2` on this VM. Scope here: (a) record the requirement on the governor plan (dispatch-aware
      QG admission on the orchestrator host), (b) if the governor's Phase-3 ledger is not landing soon, implement the
      minimal dispatcher-side stagger (cap simultaneous ship-phase tasks per host). Do NOT build a second governor.
      Source: doc #2 fix-direction 1. **Gate**: concurrent full-QG on the VM measurably capped (via governor or
      stagger), evidence cited.

### Phase 5 — doc close-outs + audits

- [ ] [INFRA] P3. **07-12 degradation onset: name it or close it.** `worker_polling_dead` 0→587 + spawn:dispatch
      0.6:1→44:1 on 2026-07-12 was never explained (mechanism since fixed). One `activity_log` excavation pass → either
      a named cause or a recorded not-worth-it decision. Source: doc #8 todo 3. **Gate**: doc #8's gate — not silence.
- [ ] [REVIEW] P2. **`ao_docs_reconciliation` close-out pass.** Verify tier-by-tier (1–6) what has since landed (several
      tiers were executed piecemeal: Tier-4 → `ao_residuals`; X2 → recovery doc; some Tier-1 flips landed in later
      commits), apply/route what remains, then flip the tracker `resolved` + archive. Its own X5 lesson applies: every
      edit lands committed+pushed in the same session. Source: doc #10. **Gate**: each tier marked landed/routed/dropped
      with evidence; doc archived.
- [ ] [REVIEW] P3. **Archive each source doc as its items land** (5-step ritual each: migrate deferred → banner →
      codex-alignment → codex update if a contract changed → clear lock). Docs #2 and #6-frontmatter carry bogus fields
      (`last_updated: 2026-06-27` predating `created`; stray `locked_by: live-defi-rollout`) — repair at archival.
      **Gate**: `plans/active/issues/` contains no resolved-but-unarchived AO doc; inventory regenerated.

### Phase 6 — operator-reported dispatch-policy gaps (2026-07-17, verified this session before writing)

> Reported verbally by the operator 2026-07-17; each item below was VERIFIED against code + the live VM before being
> written down. Per the operator's instruction these are RECORDED, not fixed, in this session.

- [ ] [BACKEND] P2. **Paused-slot semantics — verified CORRECT in code; pin it with tests + close the one unchecked
      path.** Findings (2026-07-17): `dispatch.pick_next_task` excludes paused via `_slot_configured` (`dispatch.py:186`
      — "paused: an explicit operator 'do not use this slot'"); AutoSpawn excludes paused (`autospawn.py:631`
      spawnability + `:2031` review/paused guard); `plan_health._pick_free_slot` and `escalation._pick_free_slot` both
      skip `paused`/`killed`; a paused slot's `/heartbeat` only refreshes ping + drains messages, never dispatches
      (`slots_worker.py:316`); the TmuxPruner never overwrites `paused` and never releases a paused slot's task
      (operator intent preserved). So the operator's expectation — no new task, no new work on a paused slot — HOLDS in
      code today. Remaining: (a) one regression test pinning "a paused slot receives no task from ANY path" (dispatch,
      autospawn, plan_health, escalation, AND the dead-slot failover/spill path — the spill path was NOT verified this
      session); (b) verify the dashboard renders paused distinctly so an operator-paused slot is never mistaken for a
      stuck one. NOTE (2026-07-18): the cited line numbers (`dispatch.py:186`, `autospawn.py:631/:2031`,
      `slots_worker.py:316`, etc.) DRIFTED after the config `.tuning.` call-site refactor — **verify by SYMBOL**
      (`_slot_configured`, `pick_next_task`, `_pick_free_slot`), not line. **Gate**: the all-paths test exists +
      bug-injection proves it bites; spill-path verdict recorded.
- [ ] [BACKEND] P1. **plan_health cadence — MEASURED 21 dispatches in 5.5h (11:02→16:30Z), overlapping instances
      confirmed (`superseded-plan_health` exit reasons + one ACTIVE at probe time).** Operator policy: once per 4–8h
      unless CI-triggered — NOT every 15–30 min. Root cause found: `main-backmerge-to-ldr.yml` § "Ping plan-health
      agent" POSTs `/api/plan-health/dispatch` on EVERY LDR→main promotion that lands PM content (fleet promote runs
      `*/15`, PM is busy — today's session alone drove ~10 promotions), and the server endpoint has NO cooldown, NO
      already-running coalesce (only the failure-page cooldown is deduped; the singleton reaper kills stragglers after
      the fact, which is where the `superseded-plan_health` churn comes from). Fix to implement: (a) server-side
      min-interval gate on `/api/plan-health/dispatch` (default 4h, `mode=reconcile` exempt, explicit `force=true` for
      operator/CI-emergency use) + at-most-one-live coalesce (a dispatch while one is active returns the active
      dispatch_id, HTTP 200, no spawn); (b) keep the promotion ping as a TRIGGER but let the server gate absorb the
      frequency (trigger-rich, execution-throttled); (c) operator to ratify the interval (4h vs 8h). Also noted: every
      plan_health boot logs `boot_read_unconfirmed` for `agents/worker.md` (the file exists — the worker just never
      confirms it), a per-boot noise line worth one look while in the file. **Gate**: measured dispatch rate ≤ 1 per
      interval over a 24h window with promotions still flowing; zero `superseded-plan_health` exits in that window.
- [ ] [BACKEND] P1. **Blocked-task redispatch cooldown + change-triggered re-eligibility + worker ETA (operator policy,
      new mechanism).** Today a skip-as-blocked only blocks the SKIPPING slot (24h slot-scoped TTL); any other idle
      same-role slot re-claims the task within ~minutes (measured: 117 `slot_task_skipped`/24h; the mvp thrash doc
      recorded 3 re-derivations of the same verdict in ~35 min). Operator policy to implement, verbatim: (1) when a
      worker declines a task as BLOCKED after reading the plan, the task is not re-dispatchable to ANY slot for a base
      cooldown of 10–15 min; (2) within/after that window, re-dispatch EARLY only if something RELEVANT changed — a
      prerequisite flip, a plan-todo/regen change on that task, a park/priority change — i.e. change-triggered
      re-eligibility, else (3) no change → next attempt no sooner than 1h; (4) the worker MAY supply an estimated
      unblock time on skip (e.g. "VM finishes in ~15 min") — extend the `/skip-current-task` payload with
      `estimated_unblock_minutes`, and the cooldown becomes that estimate (+small buffer) instead of the defaults.
      Design note: this is the missing middle layer between the existing slot-scoped skip TTL and Phase-3's auto-park
      (park = the ≥N-skips escalation of the same mechanism; the cooldown handles the 1st–Nth skip window). **Build
      exactly ONE fleet-scoped cooldown store** (keyed by task*id, with change-listeners on prerequisite/regen/park
      events) that is REUSED by Phase-3 auto-park AND AF-1's escalator backoff — do NOT ship three separate
      cooldown/backoff engines (they diverge). \*\*New tunables (base cooldown, 1h fallback, N-skip park threshold,
      escalator cap) go on the env-free `config.tuning` / `TuningDefaults`, NOT a new `ORCHESTRATOR*\*` alias** (per the
      2026-07-18 config split); reuse existing knobs where they fit (`slot_skip_ttl_hours`,
      `orphaned_task_reclaim_grace_seconds`, `dispatch_ack_timeout_seconds`). Sources: operator 2026-07-17 + doc #5's
      fleet-wide-cooldown gap. **Gate**: regression tests (skip-blocked → no cross-slot redispatch inside base cooldown;
      prereq flip → immediate re-eligibility; no change → 1h; ETA honoured); measured redispatch-of-declined-task rate
      drops to the policy curve on the live VM.
- [ ] [INFRA] P1. **plan_reconciler daily 01:00 UTC was NOT RUNNING — part (a) DONE 2026-07-18 window armed; (b)/(c) +
      two NEW defects remain.** **(a) ✅ RE-ENABLED 2026-07-17T18:03Z (operator request, this session)**: ran
      `install-plan-reconciler-timer.sh --operator ubuntu --time 01:00` via SSM; verified `is-enabled=enabled`,
      `NextElapseUSecRealtime=Sat 2026-07-18 01:04:12 UTC`, unit files on disk. The Persistent catch-up fired
      immediately and **actually dispatched `agt-55b581`** (plan_reconciler, live on `orch-slot-2` at 18:04:25Z) — a
      bonus run the operator can inspect today alongside tomorrow's. **Diagnosis CORRECTED by the pre-install
      forensic**: the units were NOT absent — they existed since Jul 14 15:23 and were `enabled`; the timer was
      evidently INACTIVE (stopped), which `is-enabled` does not detect and `list-timers` omits (no next-elapse) — that's
      why it fired 07-15 then silently never again, and why yesterday's probe saw nothing. Journal history was
      unrecoverable (vacuumed), so WHAT stopped it is unknowable now; the liveness check below is the durable answer.
      **Two NEW defects found by the re-enable, to fix in code**: (1) the dispatch script's `curl --max-time 30` is
      shorter than the endpoint's real latency (measured 56s: initiated 18:03:29 → dispatched 18:04:25), so EVERY timer
      run logs `HTTP 000 / FAILURE` even when the dispatch succeeds — a false-failure that would mask real ones; bump to
      ≥120s or make the endpoint return 202 immediately. (2) `systemctl enable` alone doesn't guarantee a scheduled
      timer — the liveness assertion must check **`is-active` + a computed next-elapse**, not `is-enabled`. Remaining:
      **(b)** the daily liveness assertion (digest line or guard-cron: timer `is-active` AND next-elapse exists AND last
      successful dispatch < 26h → alert on breach); **(c)** audit whether the 2026-07-15 run (`agt-2d8441`) AND today's
      `agt-55b581` COMPLETED their work product (operator suspects the 07-15 one did not): pull their
      `plan_health_result`/`reconciler_candidate` events + any PM commits, record the verdict. **Gate**: the 2026-07-18
      01:04 UTC run visible in the journal AND a completed result event; false-failure curl fixed; liveness check alerts
      when the timer is deliberately stopped in a test.

### Phase LAST — operator-sequenced

- [ ] [BACKEND] P2. **Recovery-audit Layer-1 producer rewire (operator ruling B, "do it at last").** Stand up the
      standalone recovery-audit-signoff producer (NOT an AO worker-role): consume PubSub `agent-recovery-actions`, POST
      verdicts to the live `POST /safety-ops/signoffs`; unmock the DART feed; clean the stale `routes/agents.py:146`
      comment. Only start once Phases 0–4 are done (the operator's sequencing). Source: doc #9. **Gate**: a real signoff
      flows PubSub→producer→alerting-service→DART with the mock feed retired; codex Layer-1 banner replaced with the
      live description.

### Phase 7 — INDEPENDENT AGENT-AUDIT FINDINGS (Claude, 2026-07-17) — ⚠️ NOT from the issue docs

> **These are MY OWN findings** from a fresh pass over the AO codebase, the live DB/activity-log, and the codex AO docs
> — kept deliberately SEPARATE from Phases 0–6 (which trace to issue docs or operator reports) so the operator can
> review them on their own merits. **REVIEWED + RATIFIED 2026-07-18**: AF-1 (ratified + root-cause-why-they-fail added),
> AF-2 (folded into the Phase-6 plan_health throttle — no separate work), AF-3 (LOW priority — 40 MB is not big; only
> unbounded growth matters), AF-4 (ratified — build the snapshot-age assertion), AF-5 (ratified + EXPANDED to
> per-account/agent/slot token+message usage), AF-6 (done, ao@c03ccce). Scope honesty: codex claims were SPOT-checked
> (alerting, governor, paused semantics, recovery Layer-1 — the last two via Phases 0–6 work), not exhaustively diffed;
> the deep codex↔code diff belongs to the Phase-5 `ao_docs_reconciliation` close-out. One false lead corrected along the
> way: an early probe reported `qg-host-governor.sh` missing from the VM — wrong path (it lives in
> `scripts/quality-gates-base/`, not `scripts/dev/`); at the real path it answers `MODE=token K=2` (drift already
> recorded on the governor plan, no new item).

- [ ] [BACKEND] P1. **(AF-1) CI-wall escalator burn: 189 dispatches / 7d for 50 escalations, 83 UNRESOLVED (43%).**
      Measured from `activity_log` (7d, wall_type=`ldr_qg_failure`): `escalation_queued=50`, `escalation_dispatched=189`
      (≈3.8 dispatches per escalation — redispatch churn), `escalation_resolved=108`, `escalation_unresolved=83`. Every
      dispatch is a full cicd agent session; nothing in any open issue doc tracks escalator EFFICACY — the alerting
      codex governs how escalations PAGE, not whether they WORK. Proposal: (a) an unresolved-escalation triage pass
      (what are the 83 — one recurring wall or many?); (b) a redispatch cap + backoff per escalation_id — **implemented
      ON the ONE fleet-scoped cooldown store from the Phase-6 blocked-task item, not a separate escalator engine**; (c)
      a resolved:dispatched efficacy KPI in the daily digest; **(d) RATIFIED (operator 2026-07-18) — root-cause WHY the
      escalators fail: sample the 83 unresolved and classify the cause — boot prompt too shallow / missing context, the
      QG-failure payload handed to them is insufficient, OR the failures are genuinely too hard for the cicd role+model
      (→ needs a model bump / human hand-off). Route the fix by class (prompt hardening vs richer failure context vs
      model tier vs escalate-to-operator).** **Gate**: the 83 are explained WITH a cause-class breakdown; redispatch per
      escalation capped; efficacy KPI visible; the prompt/context/model fix (whichever the classification points to) is
      applied or a follow-up filed.
- [ ] [INFRA] P2. **(AF-2) plan_health true daily volume is 55 dispatches/24h — 13 of which produced NO result.**
      `plan_health_dispatched=55`, `plan_health_result=42`, `plan_health_dispatch_failed=4` in the last 24h — worse than
      the 5.5h sample in Phase 6, and each run is a **haiku** worker (`agents/plan_health.md` `model: haiku` — NOT
      sonnet; the cheap radar) digesting ~449 plan skeletons. MEASURED 2026-07-18 (6-day activity_log): 288 dispatched /
      186 result / 59 failed → only ~65% produce a result; run duration median 280s, mean 288s, p90 6.5 min, max 10.5
      min. The result-less dispatches are pure waste (superseded/died mid-run). This is EVIDENCE strengthening the
      Phase-6 cooldown item, plus one addition: the cooldown gate should also require the PREVIOUS dispatch to have
      posted its result (or timed out) before a new one spawns. **Gate**: folded into the Phase-6 plan_health item's
      acceptance.
- [ ] [BACKEND] P3. **(AF-3) `activity_log` has NO retention policy — unbounded growth on the hot DB.** 83,813 rows
      spanning 20 days (~4.2k/day), db 40 MB. Agents get `prune_finished_agents` (7d) and tasks get orphan-GC;
      `activity_log` has nothing (grepped `state_store/` — no delete/prune path). Fine today, but it is silent unbounded
      growth on the dispatch-hot SQLite file, and the log IS the fleet's audit stream. CONTEXT (operator asked
      2026-07-18): **83k rows / 40 MB is NOT big for SQLite** (it handles millions of rows comfortably) — there is NO
      problem today; the only real risk is UNBOUNDED growth over MONTHS (write-latency creep on the write-hot DB). So
      this stays **low priority**: a simple age-based prune (90d) OR just a growth alarm suffices — not urgent, no
      redesign. Proposal: age-based retention (e.g. 90d) with optional archive-to-S3 via the existing snapshot loop
      before delete. **Gate**: a retention decision recorded + implemented (or explicitly deferred with the growth-alarm
      in place).
- [ ] [INFRA] P2. **(AF-4) Disaster-recovery snapshots are wired but their RECENCY is unverified — silent-by-absence
      risk.** `gcs_sync.SnapshotLoop` runs and `ORCHESTRATOR_S3_BUCKET=uts-orchestrator-state-427895769566` is set
      (systemd env; GCS unset by design on the AWS host). But no local `state.json` was found at the expected path
      during the probe, and NOTHING asserts snapshot age — a broken snapshot loop would look exactly like a working one
      until the day state.db is lost (same class as the reconciler timer that silently vanished, Phase 6). **RE-VERIFY
      FIRST (2026-07-18) — the "no local state.json at the expected path" evidence is likely a PROBE ARTIFACT**: the
      probe ran as `ubuntu` without the systemd env, so it checked the in-repo default, not
      `/var/lib/orchestrator/state.json` (same root as the Phase-4 DB_PATH bug). Once Phase-4 moves state in-repo to
      `data/state/`, the default path IS correct and the artifact disappears. **RATIFIED (operator 2026-07-18: "decide
      yourself" → BUILD it)** — a silent snapshot failure = eventual data loss, and the age assertion is cheap.
      Proposal: (a) re-measure the S3 object's last-modified NOW (the REAL signal, independent of local path); (b) add a
      snapshot-age assertion (digest line or health endpoint: last successful snapshot < N hours, alert on breach); (c)
      one documented restore drill. **Gate**: measured snapshot age recorded; the age assertion alerts when the loop is
      deliberately stopped in a test.
- [ ] [BACKEND] P2. **(AF-5) Dispatch→done conversion is ~18% and NO surfaced metric tracks fleet efficiency.** 24h: 310
      boots / 154 dispatches / 27 done — ≈11.5 boots and ≈5.7 dispatches per completed task even with the spawn budget
      fixed (the leaks are 117 skips + 96 session-losses, i.e. Phases 2/3/6 mechanics). The OBSERVABILITY gap is
      separate and unowned: no dashboard/digest KPI exposes boots-per-done or dispatch→done conversion, so the fleet
      "looks busy" while ~4 of 5 dispatches produce no completion, and nobody sees a regression until an operator
      manually reads the activity log (how every incident in this plan was found). Proposal: daily-digest + dashboard
      KPIs (spawns, dispatches, done, conversion %, boots-per-done, top skip reasons) with a wow-level alert on sharp
      regression. **RATIFIED + EXPANDED (operator 2026-07-18): ALSO attribute USAGE per slot / agent / account —
      tokens + messages consumed — so it is visible WHERE the account budget goes.** Today nothing shows which
      agent/slot/account burned the quota, yet the fleet hits usage limits even across 4 accounts; add per-account +
      per-agent token/message counters (sourced from the usage-poller / transcript sizes) and a "usage by account" view
      on the same surface, so an account nearing its cap and the agent driving it are both visible before failover
      fires. **Gate**: the efficiency KPIs render; a per-account usage breakdown is visible; the 2026-07-12-class
      degradation (spawn:dispatch 0.6:1→44:1) would have been caught within one digest cycle.
- [x] [REVIEW] P3. ✅ **(AF-6) `ENV_VARS.md` residual multi-VM framing — DONE (ao@c03ccce).** Resolved as part of the
      `ao_config_env_var_consolidation_2026_07_18` Phase-4 rewrite: ENV_VARS.md was rewritten to the two-class shape,
      dropping the retired `tab/<vm_id>/<slot>` branch example and the "Fleet VM (epic worker)" section header for the
      single-VM `planning` reality, verified against `server/config.py`.

## Externally blocked (tracked, not actionable here)

- `/api/escalate` vs `/api/escalation/{id}` collision — **blocked on `escalation_pipeline_mvp` un-pausing** (operator
  ruling). Lives at doc #8 todo 1; must be resolved BEFORE any escalation code is written. BLOCKED-OPERATOR-DECISION.
- Backlog-relations UI — **blocked on the design agent's deliverable** (brief handed 07-17,
  `agent-orchestrator/docs/BACKLOG_RELATIONS_UX_BRIEF.md`). Lives at doc #8 todo 4. BLOCKED-UPSTREAM-DESIGN.

## Codex SSOTs

- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` + `…/agent-orchestrator-overview.md` — AO
  runtime architecture (dispatch/spawn/slots).
- `codex/04-architecture/agent-orchestrator-alerting.md` — actionable-only alerting (Phase-3/4 visibility surfaces).
- `codex/04-architecture/recovery-defence-in-depth-layers.md` + `…/autonomous-recovery-matrix.md` — Layer-1 rewire.
- `codex/05-infrastructure/per-tab-worktrees.md` — slot clones, ff-pull, shared uv cache.
- `codex/06-coding-standards/quality-gates.md` — the shared-host QG cap Phase-4 enforces.
- `codex/12-agent-workflow/async-wait-and-poll-discipline.md` — measured-verdict discipline for every gate above.

## Progress Log

- **2026-07-18 — Phase-7 ratification + measured plan_health**: operator reviewed the audit findings. plan_health
  MEASURED on the live VM: **~59 dispatches/24h (one every ~24 min)** — far above the 4–8h target; run duration median
  280s; 7d = 204 results (110 with findings, 94 empty). Its output is GENUINELY useful (real catches this session:
  data_completion_defi/tradfi stale-fork contradictions vs the newer consolidated closeouts; a CLAUDE.md Tardis
  doc_drift where the "16/4 defaults ~93% idle → scale up" guidance is contradicted by the 350x-collapse issue doc) —
  but it re-reports the SAME unresolved findings every cycle because the consumer side isn't closing them; the Phase-6
  throttle + close-the-loop is the fix. Ratifications: AF-1 (+root-cause-why-escalators-fail), AF-3 low-pri (40 MB is
  not big), AF-4 build snapshot-age assertion, AF-5 +per-account/agent token+message usage attribution. Added a Phase-1
  todo for the `audit_false_done` false-positive class surfaced by the sports rows. Freeze-streak re-routed to the
  deployment-ui fleet tab (per-repo×slot), not Slack (+deployment-ui added to `repos`). Plan-only.
- **2026-07-18 — Cross-cutting review pass (operator-requested drift/regression check)**: read the whole plan for
  contradictions + regression risks and patched 9 points. (1) Phase-4 `DB_PATH`/`STATE_JSON` two-places → **one in-repo
  source** (operator ruling: AO state in the repo, not `/var`) + a HARD deploy-preservation guard replacing the reversed
  `/var/lib` wipe-protection; added a duplicate-purpose env-var sweep item (stop writing redundant
  `ORCHESTRATOR_OPERATOR=VM_ID`; `GOOGLE_CLOUD_PROJECT`/`GCP_PROJECT_ID` + the `WORKSPACE_ROOT` trio checked & kept).
  (2) verify-by-symbol note (line refs drifted after the config `.tuning.` refactor). (3) Phase-2 orphan-reap must honor
  `boot_grace_seconds` (booting-worker-kill incident class). (4) Phase-2 stale-dispatch gate now asserts
  no-double-dispatch, fires strictly after resume exhaustion. (6) ONE fleet-scoped cooldown store reused by blocked-task
  cooldown + auto-park + AF-1 escalator backoff (not three). (7) Phase-3 auto-park now DEPENDS ON Phase-1
  preserve-by-`brief`. (8) new tunables → env-free `TuningDefaults`, reuse existing knobs. (9) AF-4 "no state.json"
  flagged as a probe artifact to re-verify (wrong path / env-not-loaded), resolves once state is in-repo. AF-6 flipped
  ✅ DONE (fixed in ao@c03ccce). No todo undoes another; nothing shipped to code — plan-only.
- **2026-07-17T18:05Z** — Reconciler timer RE-ENABLED per operator request (Phase-6 item, part (a)): installed via SSM,
  `enabled` + armed for 2026-07-18 01:04:12 UTC; the Persistent catch-up dispatched `agt-55b581` (live now on slot-2)
  despite the dispatch script logging a FALSE failure (curl 30s < endpoint's measured 56s — new defect recorded on the
  todo). Pre-install forensics corrected the diagnosis: units existed + enabled since Jul 14 but the timer was INACTIVE
  — `is-enabled` can't see that; the liveness check must assert `is-active` + next-elapse.
- **2026-07-18** — AO documentation stale-reference sweep (operator-directed, separate from the issue-doc work above):
  deleted `host-offline-failover.md` (codex) + `OPERATIONS.md` (repo) per operator ruling; purged
  OPERATIONS/tab-mirror/\_agent_pings/vm-orchestrator/:8026/post-P5/Cloud-Run-as-live refs across the AO codex + repo
  doc set; made the codex e2e-operator-runbook self-contained (was an OPERATIONS.md wrapper). Shipped pm@20f06b2b7 +
  pm@e0c796e3c + pm@071652432 (codex), ao@3d2c0e6 + ao@63d8284 (repo). Final state: 0 dead links, 0 refs to any of the
  12 deleted AO docs, 0 misleading-as-live markers. NB: the earlier 3 "harshkantariya [main·harsh_pc]" AO-doc-cleanup
  commits (13c25d2e5/fca8d2643/19766e7) were from a SECOND Claude process bound to this same session on the office VS
  Code — verified correct + complete, then that duplicate process was terminated. AF-6 (ENV_VARS residual) is the only
  open item from this sweep, operator-decision-pending.
- **2026-07-17 (final)** — Phase 7 added: five INDEPENDENT agent-audit findings (AF-1..AF-5) from a fresh pass over the
  AO code, live DB/activity-log, and codex spot-checks — kept separate from the issue-doc-derived phases per operator
  instruction, pending operator review. Headlines: 189 CI-escalator dispatches/7d with 83 unresolved (43%); plan_health
  at 55 dispatches/24h with 13 result-less; no activity_log retention; DR snapshot recency unverified; dispatch→done
  conversion ~18% with no surfaced efficiency KPI. One false lead corrected (governor script path).
- **2026-07-17 (later)** — Phase 6 added: four operator-reported dispatch-policy items, each verified against code + the
  live VM before writing (paused-slot semantics CORRECT in code; plan_health measured at 21 dispatches/5.5h with
  overlaps, root cause = per-promotion backmerge ping with no server cooldown; blocked-task redispatch cooldown policy
  captured verbatim incl. change-triggered re-eligibility + worker ETA; plan_reconciler timer ABSENT from the VM — one
  run ever, 2026-07-15). Recorded, not fixed, per operator instruction.
- **2026-07-17** — Plan authored from the operator-requested verification sweep of all 10 open AO issue docs. Every
  doc's claims re-checked against code (`agent-orchestrator@6a30e45`) and the live VM (read-only SSM: state.db,
  activity_log 24h, ps/tmux, clone freshness, `audit_false_done.py`). Two NEW findings from the sweep itself: (1) 2 live
  false-`done` rows (`sports_cf8…-001/-002`) — legacy poison surfaced by regen's `brief_hash` backfill, missed by the
  07-16 sweep; (2) ~10 orphaned claude workers currently alive (the 3 doc-named PIDs plus a detached PPID-1 tree) —
  Defect B is an active bleed, promoted to the plan's top code priority. Churn metrics confirm R1 works (spawn:dispatch
  184:154 vs 1014:217 pre-fix) — the remaining spawn:done gap (184:27) is the lifecycle + park visibility classes, not
  the budget. Source docs each carry a consolidation banner pointing here.
