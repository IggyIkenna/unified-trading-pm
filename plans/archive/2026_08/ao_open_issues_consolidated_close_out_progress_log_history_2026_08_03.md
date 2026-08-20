---
doc_type: plan
title:
  AO open-issues consolidated close-out — Progress Log history (2026-07-17 authoring through the 2026-07-28 A7 ruling)
summary: >-
  Line-cap remediation extraction from plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md's Progress Log —
  every entry from the plan's 2026-07-17 authoring through the 2026-07-28 A7 (escalation-pipeline unpause) ruling, moved
  verbatim so the live plan stays under the 1000-line hard cap. Every closed checkbox on the live plan already carries
  its own inline evidence summary; this file is the full narrative trail behind those summaries and the lessons-learned
  entries — read it only if a deeper citation on a specific finding's reasoning is needed.
status: complete
nature: record
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, deployment-ui]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, backlog, regen, worker-lifecycle, history, line-cap-remediation]
related: [/plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: script
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  - "line-cap remediation split, 2026-08-03, per
    plans/active/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md"
---

# AO open-issues consolidated close-out — Progress Log history

Extracted verbatim from `plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md`'s `## Progress Log` section
on 2026-08-03, to bring the live plan back under the workspace's 1000-line hard cap
(`scripts/plan-hygiene/check_line_caps.sh`). No content changed — only relocated. The live plan keeps its most recent
Progress Log entry (the 2026-08-02 na-eligibility-audit re-affirmation) inline, since it documents current status;
everything below predates it.

## Progress Log (historical entries)

- **2026-07-28 — A7 RULED (operator gated-decision closeout pass).** The escalation-pipeline pause's own stated blocking
  reason (W7/W8/W9 message-broker dependency) evaporated 2026-07-16 when W9 was archived NOT-REQUIRED (superseded by
  `assigned_role` dispatch) — the pause outlived its own justification. Applying the operator's standing theme ("unpause
  whatever needs unpausing to unblock a task" + "opt for full completions, no shortcuts, full functionality"): **UNPAUSE
  `escalation_and_disaster_recovery_master`** (`status: paused` → `active`), resume its 5 P1 todos to FULL completion,
  and land the `/api/escalate` vs `/api/escalation/{id}` naming-collision fix first as a new explicit P0 prerequisite
  (which was always correct regardless of the pause call). A7 table row + the "Externally blocked" section both updated
  to reflect the ruling; the naming-collision item retagged `BLOCKED-OPERATOR-DECISION` → `[BACKEND] P0` and moved to
  its real tracking home (`escalation_and_disaster_recovery_master.md`). Plan-only change, no code shipped.
- **2026-07-20 — Operator process correction: do NOT push new plans before the operator has read them.** I authored
  three plans and pushed them `status: active`, which meant AO could ingest and dispatch them before the operator saw a
  word. Verified no harm (0 ingested tasks from any of them at the time of correction), and all new plans were flipped
  to `status: draft`. **Standing rule from here**: a newly authored plan ships as `draft`, the operator reads it, and
  the operator flips it to `active` — authoring is not dispatching. Applies to every new plan, not just these.
- **2026-07-20 — A5 REVERSED within the hour (delete → keep).** The operator ruled multi-VM is likely to return for
  resilience/backup, so failover stays. The drafted retirement plan was removed before any worker saw it. **The
  reasoning error is worth keeping**: I read "0 failover events for all time" as evidence the module is DEAD, when the
  same measurement is equally evidence it is UNTESTED. Which reading applies depends on whether the capability is still
  wanted — that is a question about product intent, not about the code, and I could not have answered it from the
  codebase. Ask it before proposing deletion of any dormant infrastructure. The reversal also improved the work: the
  replacement plan targets the fact that failover's re-route and rollback paths have never once executed, which matters
  far more if you intend to rely on them than if you intend to delete them.

- **2026-07-20 — B1 CLOSED (by design, no defect) — but the question was mis-scoped, twice.** It asked about two ids and
  4 rows; the truth is five absent ids and 3 rows. **The framing itself was the bug**: "a plan todo should have a task
  row" is not the contract. The tasks table is a projection of currently-open DISPATCHABLE todos plus dispatched history
  — a `BLOCKED-*` todo is deliberately never ingested, and a todo checked off outside the dispatch loop has its
  still-queued row garbage-collected. So **a missing row is not evidence of a lost task**, which is why this item
  "decayed twice": each re-measurement found different numbers and read that churn as instability rather than as the
  designed projection doing its job. Generalisable: before auditing rows-vs-todos anywhere in AO, state which direction
  is authoritative — the plan checkbox is the SSOT (cf. A2), the row is a dispatch artifact.
- **2026-07-20 — B3 CLOSED by code-read + a live severity probe.** The unverified spill path splits cleanly on **pull vs
  push**: a pull-based spill can never violate paused (a paused slot never asks), a push-based one is where the bug
  always was. That is the reusable question for any future "does X respect paused?" audit — ask which direction the
  assignment travels, not which module it lives in. Found `failover._pick_least_loaded_slot` not only failing to exclude
  paused but PREFERRING it (load metric = pinned-task count, which is 0 for a paused slot by definition — the guard's
  absence and the metric's bias compound). Severity was settled by MEASURING rather than assuming: failover is stopped,
  never fired, 0 events for all time → latent P2, not a live P0. The probe also showed `fleet_registry_entries: 0`,
  which raised the better question (new P3): the module is cross-host machinery in an architecture that went single-VM
  on 2026-06-27, so deleting it may beat fixing it — sequence the ruling BEFORE the fix.
- **2026-07-20 — B4 CLOSED by read-only SSM audit; verdict inverted the assumption.** The question was "did the
  07-18/19/20 daily runs fire?" The answer is that firing was never the constraint: the timer is healthy and HAS fired
  every night, but **no reconcile run has ever completed, going back to the first install** — 5 dispatches, 0
  `plan_health_result` posts, 0 `plan_reconciler/*` branches, 0 PRs. Three distinct causes, now three todos: a P0
  prereq-reaper that kills freshly-spawned agents on a stale-timer slot (killed the 07-20 run 19s after boot), a slot
  race that made the 07-19 run never spawn at all, and an unexplained 7-min death class on 07-15/17/18. **Method note
  worth reusing:** the decisive evidence was NOT the journal (which lies — the 30s curl timeout makes a successful
  dispatch and a failed one look identical, `exit 1` both nights) but the **work product**: zero pushed branches and
  zero result rows. When a subsystem's monitoring is itself suspect, check for the artifact it is contractually required
  to produce, not for its own success signal. **Second-order lesson:** a "verify it ran" task is worth more than it
  looks — B4 was scoped as a cheap liveness check and surfaced a generic fleet-wide work-destroyer (the reaper) that no
  liveness check would ever have named.
- **2026-07-20 — Session-end (pre-compact). Lessons + corrections worth NOT re-learning:**
  - **Two claims of mine were WRONG and are corrected in-place** — (1) "bootstrap writes both dead regen vars": it
    already purged `REGEN_DB_PATH`; only `REQUIRE_VM_MATCH` lacked a purge (found by READING, not grepping —
    `_remove_env` lines look identical to `_upsert_env` in a grep). (2) "plan_health is a sonnet worker": it is
    **haiku** (`agents/plan_health.md`) — the token-spend concern was overstated.
  - **Measurement trap (bit twice, cost real time):** a read-only probe run as `ubuntu` does NOT inherit the systemd
    unit's `Environment=`, so `config.db_path()`/`state_json_path()` resolve the IN-REPO default, not
    `/var/lib/orchestrator/…`. This produced the wrong-DB audit AND the bogus AF-4 "no state.json found" alarm. When
    probing the VM, pass the path EXPLICITLY (`/var/lib/orchestrator/state.db`) until Phase-4 moves state in-repo.
  - **activity_log payload column is `details_json`** (not `detail`/`payload`); table cols are
    `id, ts, event_type, slot_id, task_id, details_json`. A grep for common names returns nothing and looks like "no
    data" when the data is right there.
  - **SSM gotchas:** the document is `AWS-RunShellScript` (NOT `-Command`), `--parameters` needs `commands=["…"]` as a
    JSON list, and any non-trivial remote script must be **base64-encoded** — raw semicolons/ quotes break the parameter
    parser. Nested here-doc + `def` inside the payload also fails; keep remote scripts flat.
  - **`git pull --rebase --autostash` UNSTAGES your staged files** — re-`git add` by name before committing, or the
    commit finds nothing. PM raced repeatedly this session; a pull→stage→commit→push retry loop is the reliable shape.
  - **QG scope:** basedpyright EXCLUDES `tests/` (`include=["server"]`) and ruff ignores F401/F841/F811 under `tests/*`
    — so IDE diagnostics on test files are NON-gating; only runtime test-pass + `server/` lint/types gate.
  - **Rejected approach:** making tuning knobs env-free by inheriting a plain `BaseModel` into the `BaseSettings` does
    NOT work — pydantic-settings then reads them by BARE env name. A NESTED sub-model is the only clean way (verified).
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
  pm@e0c796e3c + pm@071652432 (codex), ao@3d2c0e6 + ao@63d8284 (repo, both ~2026-07-18T10:28-10:35Z). Final state: 0
  dead links, 0 refs to any of the 12 deleted AO docs, 0 misleading-as-live markers **— scoped to what THIS sweep swept
  (`OPERATIONS.md` + the tab-mirror/\_agent_pings/vm-orchestrator/:8026/post-P5/Cloud-Run-as-live ref set), not
  fleet-wide.** NB: the earlier 3 "harshkantariya [main·harsh_pc]" AO-doc-cleanup commits (13c25d2e5/fca8d2643/19766e7)
  were from a SECOND Claude process bound to this same session on the office VS Code — verified correct + complete, then
  that duplicate process was terminated. AF-6 (ENV_VARS residual) is the only open item from this sweep,
  operator-decision-pending. **CORRECTION (2026-07-24, per
  `plans/active/issues/ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md`)**: `ao@19766e7`
  (2026-07-18T00:43:10+0530, same "duplicate process" commit chain noted above) deleted `AUDIT_FINDINGS_2026_05_18.md`,
  `PLAN.md`, and `MAIN_AGENT_CUTOVER_REVIEW.md` against `ao_docs_reconciliation_2026_07_15.md` Tier-6's explicit
  per-file keep/banner/repoint instructions for those three — a DIFFERENT batch this entry's sweep (`3d2c0e6`/`63d8284`,
  ~10h later) never touched. That left 5 dead doc-references live in shipped server code (`bootstrap.py`, `db.py`,
  `orm.py`, `models/__init__.py`, `routes/slots_worker.py`) at the time this Progress Log line was written — so the "0
  dead links, 0 refs to any of the 12 deleted AO docs" claim above was NOT true fleet-wide, only for the OPERATIONS.md
  batch. See the linked issue doc for the fix todos and current status.
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
07-16 sweep; (2) ~10 orphaned claude workers currently alive (the 3 doc-named PIDs plus a detached PPID-1 tree) — Defect
B is an active bleed, promoted to the plan's top code priority. Churn metrics confirm R1 works (spawn:dispatch 184:154
vs 1014:217 pre-fix) — the remaining spawn:done gap (184:27) is the lifecycle + park visibility classes, not the budget.
Source docs each carry a consolidation banner pointing here. **➡️ MOVED 2026-07-20 to
`ao_backlog_regen_integrity_2026_07_20.md` — do NOT action here.**
</content>
