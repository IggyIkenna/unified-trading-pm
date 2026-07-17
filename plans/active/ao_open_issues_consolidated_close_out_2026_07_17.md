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
repos: [agent-orchestrator, unified-trading-pm]
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
      UNAUDITABLE then; regen backfilled their `brief_hash` since). First DIAGNOSE whether the underlying work is
      genuinely done (the UTL fixes shipped — the todos may be flippable rather than reopenable); then either flip the
      plan checkboxes (if the work is complete, making the rows honest) or `POST /api/backlog/{id}/reopen` (if not).
      **Gate**: `audit_false_done.py --db … --pm …` reports `false_done: 0`, and the decision per row is recorded on
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

### Phase 2 — worker lifecycle (code)

- [ ] [BACKEND] P1. **Orphan-process reap (Defect B) — the biggest live bleed.** ~10 orphaned `claude` workers are alive
      right now on the VM (16 procs vs 4 live sessions; 3 are the doc's named PIDs, ~4h old, one tree fully detached at
      PPID 1), burning CPU + account budget and racing re-dispatched work. Implement BOTH halves: (a) the TmuxPruner
      kills the worker process tree whose slot config-dir maps to a dead/absent session (match by
      `claude_session_id`/config dir, never by name-grep alone); (b) a periodic orphan sweep (config-dir → PID → slot
      liveness) catching residue incl. PPID-1 trees. Guards: never kill a PID belonging to a live session; dry-run mode;
      log every kill with slot + PID + age. Source: doc #3 Defect B. **Gate**: the doc's regression — simulated
      `tmux_session_lost` leaves zero detached claude processes for that slot; live sweep on the VM reports 0 orphans
      (one-time cleanup of the current ~10 included).
- [ ] [BACKEND] P1. **Stale-dispatch invariant (Defect A, resume-path aware).** The pruner's requeue (`ao@5b07bd3`)
      already releases on a "requeue" verdict, but a `resume-pending` verdict keeps the task bound — and when the resume
      never happens (07-17 incident: slots went `killed` holding tasks), nothing reconciles. Add the reconciler
      invariant: a task `dispatched` to a slot with `worker_alive=false` AND `tmux_session IS NULL` for > one pruner
      tick beyond `resume_attempts` exhaustion → auto-release + `stale_dispatch_reclaimed` activity event. Must NOT
      fight the resume path — only fire after resume is exhausted/impossible. Source: doc #3 Defect A + doc #2
      symptom 1. **Gate**: doc #3's regression test; live `dispatched` count equals live-worker-held count across a 24h
      window (spot-checked).
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
      closes doc #1's last todo AND doc #5's auto-park design todo in one mechanism. Sources: doc #1 todo 2, doc #5
      fix-todo 3(design). **Gate**: a fleet-skipped task auto-parks with a visible reason; clearing the condition
      unparks it; test-pinned.
- [ ] [ADMIN] P2. **Wire the mvp-defi unpark.** `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` (still
      `false`) must be flipped by whoever lands the seed-chain/backfill progress (`data_completion_defi_2026_07_15`'s
      owner), or the park outlives its reason. Add the pointer on that plan + a line in the park's prereq description
      naming the flipper. Source: doc #5 fix-todo 2. **Gate**: the owning plan carries the flip instruction; condition
      documented.

### Phase 4 — infra/ops hardening

- [ ] [INFRA] P1. **`ORCHESTRATOR_DB_PATH` into `.env.local` via bootstrap** — the one-concept-two-places footgun that
      caused the wrong-DB GC incident and has now bitten THREE diagnostic sessions (twice on 07-17, once again in this
      session's probe). Bootstrap writes it; idempotent; service unit stays authoritative. Source: doc #8 todo 2.
      **Gate**: doc #8's gate — plain `config.db_path()` as ubuntu with no overrides prints
      `/var/lib/orchestrator/state.db`.
- [ ] [INFRA] P2. **Per-repo freeze-streak alert in `slot-cron-ff-pull.sh`.** Verified still absent: the dirty-streak
      WARN fires only when EVERY repo in a sweep skips — a single frozen clone (the exact 2-day outage mode) stays
      silent. Make the streak per-repo (repo X `[skip:dirty]`/`[skip:ff-failed]` N consecutive ticks → WARN naming the
      repo). NOTE: doc #7 says the operator routed "UI surface + alerting" to a separate agent — check with the operator
      whether that agent shipped anything BEFORE building; if it exists, verify + close instead. Source: doc #7 todo 3.
      **Gate**: doc #7's gate — a deliberately-frozen clone WARNs within N ticks.
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

### Phase LAST — operator-sequenced

- [ ] [BACKEND] P2. **Recovery-audit Layer-1 producer rewire (operator ruling B, "do it at last").** Stand up the
      standalone recovery-audit-signoff producer (NOT an AO worker-role): consume PubSub `agent-recovery-actions`, POST
      verdicts to the live `POST /safety-ops/signoffs`; unmock the DART feed; clean the stale `routes/agents.py:146`
      comment. Only start once Phases 0–4 are done (the operator's sequencing). Source: doc #9. **Gate**: a real signoff
      flows PubSub→producer→alerting-service→DART with the mock feed retired; codex Layer-1 banner replaced with the
      live description.

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

- **2026-07-17** — Plan authored from the operator-requested verification sweep of all 10 open AO issue docs. Every
  doc's claims re-checked against code (`agent-orchestrator@6a30e45`) and the live VM (read-only SSM: state.db,
  activity_log 24h, ps/tmux, clone freshness, `audit_false_done.py`). Two NEW findings from the sweep itself: (1) 2 live
  false-`done` rows (`sports_cf8…-001/-002`) — legacy poison surfaced by regen's `brief_hash` backfill, missed by the
  07-16 sweep; (2) ~10 orphaned claude workers currently alive (the 3 doc-named PIDs plus a detached PPID-1 tree) —
  Defect B is an active bleed, promoted to the plan's top code priority. Churn metrics confirm R1 works (spawn:dispatch
  184:154 vs 1014:217 pre-fix) — the remaining spawn:done gap (184:27) is the lifecycle + park visibility classes, not
  the budget. Source docs each carry a consolidation banner pointing here.
