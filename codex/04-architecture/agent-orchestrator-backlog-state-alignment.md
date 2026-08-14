---
doc_type: codex-ssot
title: Agent Orchestrator — Backlog ↔ State DB Alignment Architecture
summary:
  Backlog↔state.db alignment — PlanRegenLoop regenerates backlog.yaml from plans/active/*.md `- [ ]` todos every 30 min
  (dedup by brief + slug-NNN id); prune_stale deletes orphan yaml + queued-undispatched state.db zombie rows, never
  done/dispatched rows.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [orchestrator, plan-hygiene, self-healing, backlog, infrastructure]
related: [/codex/04-architecture/agent-orchestrator-overview.md, /codex/04-architecture/agent-orchestrator-autospawn.md]
created: 2026-05-30
authoritative_for: [agent-orchestrator backlog-to-state.db alignment and regen]
referenced_by:
  [
    /codex/04-architecture/agent-orchestrator-autospawn.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
    plans/audit/instructions/orchestrator_master_audit_instructions.md,
  ]
owner:
last_reviewed: 2026-07-25
code_refs:
---

# Agent Orchestrator — Backlog ↔ State DB Alignment Architecture

> **SSOT**: `agent-orchestrator/server/regen_backlog_from_plan.py` **Plan**:
> `plans/active/agent_orchestrator_backlog_state_alignment_2026_05_29.md` **Overview pointer**:
> `/codex/04-architecture/agent-orchestrator-overview.md`

## Problem statement

The orchestrator maintains two task stores:

| Store                    | Location                   | Owner                                       |
| ------------------------ | -------------------------- | ------------------------------------------- |
| `backlog.yaml`           | `data/config/backlog.yaml` | `regen_backlog_from_plan.py` + manual edits |
| `state.db` `tasks` table | `data/state/state.db`      | Dispatcher + worker lifecycle               |

**Drift** occurs when rows exist in `state.db` that are no longer in `backlog.yaml` (zombies from completed plans), or
when `backlog.yaml` contains stale tasks whose plan-todo lines have been edited or removed. Without cleanup, zombie rows
accumulate and inflate queue counts, causing false "work available" signals.

**The park-only hand-edit exception (RULED 2026-08-02, `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 2b).**
CLAUDE.md's "never hand-edit `backlog.yaml`" rule is about AUTHORING task content — that must always come from a plan's
own `- [ ]` todos via `regen_backlog_from_plan.py`, never a hand-typed row, or the next regen silently overwrites or
duplicates it. It is NOT a blanket ban on every field of every row: **an agent MAY hand-edit an EXISTING row's
`priority`/`prereqs` fields to park it** (e.g. dropping priority to de-prioritize, or adding a prerequisite condition to
gate it), provided (a) the row's task content itself is untouched, and (b) the SAME park intent is also authored into
the source plan's frontmatter/body in the same edit (`depends_on` + `gate_on_depends: true` is the plan-authored
equivalent — see `defi_morpho_lending_indices_never_wired_2026_07_12.md`'s 2026-07-31 correction for the canonical
pattern), so the next `regen_backlog_from_plan.py` run re-derives the SAME park state from the plan rather than silently
reverting the hand-edit. A hand-edit with no matching plan-side authoring is still the banned case — it will not survive
the next regen and hides the real park decision from anyone reading the plan.

---

## The `tasks` table is a projection, not a completion ledger

**Provenance**: the B1 audit, where this item decayed TWICE because each re-measurement read normal projection churn as
instability (`ao_scheduled_agent_hygiene_2026_07_20` todo 6) — a future reader must not repeat that mistake.

The `tasks` table holds currently-OPEN DISPATCHABLE todos plus dispatched/done history — it is **not** a historical
record of every todo that ever existed. Two entirely normal, non-alarming ways a row disappears or never appears:

- **`BLOCKED-*` todos are deliberately never ingested** (`BLOCKED-CREDENTIALS` / `-OPERATOR-DECISION` / `-BILLING` / …)
  — they wait on an external unblock, not on dispatch, so regen skips them on every tick by design.
- **A todo checked off (or edited) OUTSIDE the dispatch loop** — by hand, or by a different agent — has its still-
  `queued` row garbage-collected as an orphan on the next `prune_stale` tick (its `brief` no longer matches any live
  plan line; see "Brief-mutation accumulation" below).

**A missing row is therefore never by itself evidence of a lost or dropped task.** Check the plan file's own checkbox
state first — that is the actual source of truth — before treating an absent backlog/DB row as an incident.

## Auditing `status=done` honesty — `audit_false_done.py` / `audit_stale_gate_references.py` cadence

`scripts/orchestrator/audit_false_done.py` (`--db data/state/state.db --pm ../unified-trading-pm`) checks every `done`
row with a plan_ref against its plan's actual checkbox state. Per
`backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md`'s closing ruling: the gated mechanism itself
(`check_plan_flip`'s hard-409 at `/done`-time) needs no periodic sweep to PREVENT a new false-`done` row — that part is
structural. The "run once per close-out session, not on a cron" framing from that ruling is now **SUPERSEDED
2026-07-25** by explicit operator instruction, once real runtime was measured live on the orchestrator VM (~5.4 s) and
judged well within a periodic budget: both this tool and its sibling `audit_stale_gate_references.py` (~5.6 s) now run
as systemd timers on the central orchestrator VM — `audit-false-done.timer` every 4 h,
`audit-stale-gate-references.timer` every 1 h (`scripts/audit-false-done.{service,timer}`,
`scripts/audit-stale-gate-references.{service,timer}`, installed via
`scripts/install-audit-crons.sh --operator ubuntu --start`). The original UNAUDITABLE→auditable-transition concern (a
legacy row's `brief_hash` backfills silently the moment regen next touches it, surfacing old poison at an unpredictable
time) is a reason a NAIVE cron could be misleading if read as "clean = provably nothing wrong, forever" — it is not a
reason not to run the check regularly; an hourly/4-hourly cadence just means that surfacing happens within one tick
instead of waiting for someone to remember to run it by hand. **A nonzero exit from either service is a real finding,
not a bug** — check `journalctl -u audit-false-done.service` / `-u audit-stale-gate-references.service`; neither timer
pages or alerts today (no Slack/on-call wiring exists for these findings yet — that's a real, separate scope decision,
not assumed). See `ao_backlog_regen_integrity_2026_07_20.md` todo 7 for the original ruling and
`gate_completed_tasks_trusts_stale_done_after_checkbox_unflip_2026_07_25.md`'s Progress Log for the cadence change.

## `/done`-time completion-acceptance gates (sha-on-origin + idempotency/owner-check)

Two structural hard-409 gates sit in `server/routes/slots_worker.py`'s `done_slot()`, alongside `check_plan_flip` above,
closing the specific false-done surfaces named in `reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md`
and `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` (both archived, `plans/archive/issues/`):

- **Sha-on-origin gate** (`tuning.done_require_origin`, default `True`, `server/config.py`). A `/done` whose reported
  sha verifies locally but is NOT found on any origin branch 409s with `sha_not_on_origin` instead of reading as durably
  done — closes the specific false-done shape where a slot's push failed silently (e.g. its detached quickmerge got
  reaped mid-run) but the task still read `done` server-side with the code never on origin.
- **Idempotency + owner-check gate** (pre-existing, predates both source docs — comment-marked `B1`). A second `/done`
  on an already-`done` task 409s (`slot_done_rejected_already_done`); a `/done` from a slot that isn't the task's
  `dispatched_to` owner 409s (`slot_done_rejected_not_holder`) — both logged as activity events before any
  reconciliation logic runs, closing the double-`/done` risk from a failover-driven double-dispatch.

---

## Regen lifecycle

`PlanRegenLoop` runs in the orchestrator background and calls `regen()` every 30 minutes (default
`DEFAULT_PLAN_REGEN_INTERVAL_SECONDS = 1800`, `regen_backlog_from_plan.py`) after a short startup settle (a
freshly-pushed plan must reach the backlog within ~1 min of boot, so the first tick fires almost immediately, then
normal cadence). The prior 6 h / 21600 s cadence lagged newly-pushed plans by up to 6 h and was tightened (operator cap
2026-06-02: 30 min max).

```
PM repo (plans/active/*.md)
    │
    ├─ sorted *.md files
    ├─ skip: INDEX.md, _*.md (underscore-prefixed)
    ├─ [scope filter] skip plans not dispatchable: assigned_vm ≠ planning,
    │  execution_scope: local-only, or status: draft
    │
    ↓  _parse_open_todos()
    │  - skip YAML frontmatter
    │  - skip fenced code blocks
    │  - skip strikethrough lines
    │  - skip done checkboxes (- [x] ...)
    │  - capture unchecked lines (- [ ] ...)
    │
    ↓  dedup by brief (text-exact match on raw description line)
    │  - skips if description already in backlog.yaml
    │
    ↓  append new BacklogTask with auto-incremented slug-NNN id
    │
backlog.yaml (append-only by default)
    │
    └─ [prune_stale=True] also run _prune_stale():
       - build current_briefs from the same dispatchable plan files
       - any yaml task whose brief ∉ current_briefs = orphan
       - delete orphan yaml entries
       - DELETE orphan state.db rows WHERE status='queued' AND dispatched_to IS NULL
       - NEVER touch done / dispatched rows
```

---

## Dispatch-correctness update (2026-07-07 — `ao_dispatch_correctness_regen_reconcile`)

The append-only flow above is **superseded**: regen is now a **reconcile**, and dispatch carries per-task craft + order.
The three 2026-07-07 fleet-stall root causes are fixed here.

**RC-1 — regen RECONCILES existing tasks (not append-only).** For each plan todo, regen matches the existing task by
(`plan_ref`, brief) and UPDATES its `model` / `effort` / `thinking` / `assigned_role` / `priority` / `plan_order` in
place when they drift (`_reconcile_task_fields`, `summary.reconciled`) — so a plan retier / re-home reaches an
already-queued task on the next tick instead of being silently inert (the frozen-backlog bug). Removal of a todo whose
task is **dispatched** → the task is marked terminal `cancelled` (not a zombie `dispatched` row, not a hard delete); the
worker's next `/heartbeat` returns `cancel_task` and it reverts ONLY its own in-flight files + stops. Queued orphans
still hard-delete.

**Execution order + strict-serial.** Each task carries `plan_order` (its ordinal among the plan's open todos, re-derived
every tick); dispatch sorts `(tier, priority, plan_order, plan_ref)`, so same-priority tasks (e.g. 10× P0) hold
plan-file order and a mid-file insert lands in place. `sequential: true` (plan frontmatter) auto-chains each task's
`prereqs.completed_tasks` to its predecessor (rebuilt each tick — a reorder can't deadlock).

**RC-2 — dynamic per-task craft + one-plan-one-agent stickiness.** A todo's `[TAG]` (INFRA/DATA/BACKEND/UI/REVIEW) gives
the task's craft role, overriding the plan's `assigned_role` per-task (mapped tag; generic tags fall back) — so ONE plan
carries multiple crafts. `TaskBrief.assigned_role` is returned to the worker; `SlotRow.last_role` tracks the craft it
last served. The worker ADOPTS a new craft (reads `agents/<role>.md`) on a role change and NEVER `/skip`s a
role-mismatch (`worker.md` HARD RULE) — killing the dispatch→refuse→skip thrash. `_claim_plan_for_slot` pins a plan's
sibling tasks to the first-claiming slot with `affinity="medium"` (+ `queued_at` reset) **only when the plan is
`sequential: true`** — the pin is gated on `task.sequential` (2026-07-24 operator ruling,
`agent-orchestrator@867b1731e`) and is a NO-OP for the default non-sequential plan, whose siblings stay
`target_slot=None, affinity="none"` and fan out freely. For a pinned sequential plan a slow owner still spills to a free
slot after `target_slot_timeout_seconds`. **Fleet parallelism ≈ the count of independently-ready TASKS, not active-plan
count** — one non-sequential plan's N independent same-priority todos dispatch to N slots concurrently
(`task_template.md` §4); splitting into separate plans is required only for a real ordering dependency or same-file
overlap.

**RC-3 — slot_skips hygiene.** A per-(slot,task) skip expires after `slot_skip_ttl_hours` (default 24h, config,
0=disable) in `slot_skipped_tasks(ttl_hours=)`, so a stale skip can't starve dispatch across respawns; the prune clears
skips for GC'd/cancelled tasks; `POST /api/slots/{id}/unskip-task` + `/clear-skips` replace the manual-SQL unskip.

Code: `regen_backlog_from_plan.py` (reconcile / plan_order / sequential / per-task-role / cancel-prune), `dispatch.py`
(sort + `to_task_brief`), `state_store/slots.py` (`assign_task_to_slot` / `_claim_plan_for_slot` / skip helpers),
`orm.py` + `bootstrap.py` (`SlotRow.last_role`), `routes/slots_worker.py` + `agents/worker.md` (cancel + adopt-not-
refuse).

**Session-tier realign + Fable + per-model effort (Phase 3/7 — the capability chain, now landed).** Model / effort /
thinking are **spawn-fixed** per tmux session (`_build_claude_flags`), so a plan re-tier of a LIVE worker is applied by
**kill + respawn `--resume`** at the new tier (context preserved) — never `/model` send-keys. `server/model_tier.py` is
the ONE source of truth: `MODEL_RANK` (`haiku<sonnet<opus<fable` — consolidates the former two drifting `_MODEL_RANK`
copies), the `--effort` ladder `[low,medium,high,xhigh,max]`, `model_supports_effort` (Haiku has NONE — passing
`--effort` to it is an API 400, gated at the single spawn emission site), and `needs_respawn` (the realign decision).
`WorkerLivenessWatchdog` Trigger-5 (`_maybe_realign_tier`) applies it: a working, non-thinking, non-cooldown slot whose
running tier ≠ its current task's required tier resume-respawns at the task tier and **persists the new tier back to
`SlotRow`** (else it thrashes). MID-TASK (same task) = model-upgrade only; a `/done`→next BOUNDARY (current_task
changed) = realign any direction (the opus→sonnet down-shift). `_slot_required_model` also honours `affinity=medium`
stickiness within the `queued_at` spill window (the idle-slot upgrade path). **Fable** is a first-class tier (top of the
rank; `ModelTier` + `_coerce_model` + `model_tier: fable-required` frontmatter) but **operator-request-only** (plans
default sonnet/opus; task_template §4). A plan/role sets any effort level directly via `effort:` (validated vs the
ladder). `ultracode` is intentionally never wired (session-only `--settings` mode; operator decision). **Deferred
(minor)**: role-only soft-signal on a same-tier craft change; per-account Fable capability gating (all accounts
currently spawn any model — a Fable spawn on a non-capable account hard-errors; an operator-config concern, Fable being
rare/operator-only).

Code (Phase 3/7): `server/model_tier.py` (rank / ladder / haiku-gate / `needs_respawn`), `worker_liveness_watchdog.py`
(Trigger-5 realign + persist-back), `autospawn.py` + `dispatch.py` (`_MODEL_RANK` import; `_slot_required_model`
medium), `tmux_spawn.py` (`--effort` haiku gate), `regen_backlog_from_plan.py` (`effort:` field + `fable-required`),
`role_registry.py` (`_coerce_model` fable), `models/_types.py` (`ModelTier` fable).

---

## Invariants

| Invariant                                                             | How enforced                                                           |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| **Dedup by brief**: same description text → same task, not duplicated | `existing_briefs` set; re-runs skip already-seen descriptions          |
| **Dedup by task_id**: same slug-NNN → never re-issued                 | `existing_ids` set; `while task_id in existing_ids: next_index += 1`   |
| **No task steal**: dispatched rows never deleted                      | `prune_stale` filters `status='queued' AND dispatched_to IS NULL` only |
| **Audit history preserved**: done rows never deleted                  | Same `prune_stale` filter                                              |
| **Idempotent re-runs**: running regen twice produces the same state   | Both dedup sets guarantee this                                         |
| **Ingestion scope**: only dispatchable plans are ingested             | `assigned_vm` frontmatter filter (§ below)                             |

---

## Ingestion scope filter (`assigned_vm`)

Since the single-VM migration (2026-06-27) there is ONE orchestrator, so ingestion is a plan-level gate, not a per-VM
routing decision. `assigned_vm ∈ {planning, NA}` only (enum authority:
`/codex/11-project-management/doc-frontmatter-schema.md`):

- `assigned_vm: planning` (or `human-planning`, a legacy alias) AND not `execution_scope: local-only` AND not
  `status: draft` → the plan's `- [ ]` todos are ingested into the backlog.
- `assigned_vm: NA` → not dispatched to anyone (default for new plans).
- Any `vm-defi`/`vm-cefi`/`vm-ml`/… value is a STALE multi-VM-era artifact — flip to `planning`/`NA` on next touch.

The `ORCHESTRATOR_VM_ID` env filter is a retired multi-VM artifact: unset (its only current state) means no per-VM
filter, which is exactly the single-VM reality. Work routes to slots by **skill** (`assigned_role` / per-task `[TAG]`),
not by VM — see the single-VM SSOT § "Dispatch".

---

## Environment variables

| Variable                                   | Default                 | Purpose                                                                                                                |
| ------------------------------------------ | ----------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `ORCHESTRATOR_PM_REPO_PATH`                | `../unified-trading-pm` | Override PM repo location                                                                                              |
| `ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS` | `1800`                  | Tick cadence (30 min; was 6 h/21600); set to `0` to disable                                                            |
| `ORCHESTRATOR_REGEN_PRUNE_STALE`           | `true`                  | Enable orphan pruning on every tick (verified `server/config.py:786`, 2026-07-25 — was documented `false` here, stale) |
| `ORCHESTRATOR_REGEN_DB_PATH`               | —                       | state.db path for safe-row deletion (yaml-only prune when unset)                                                       |
| `ORCHESTRATOR_VM_ID`                       | — (unset)               | Retired multi-VM filter; unset = no filter = the single-VM reality                                                     |

---

## Drift audit recipe

Run on the target VM (requires a valid JWT):

```bash
# 1. Compare state.db queued count vs backlog.yaml task count
QUEUED=$(sqlite3 data/state/state.db "SELECT COUNT(*) FROM tasks WHERE status='queued' AND dispatched_to IS NULL;")
YAML_TASKS=$(python3 -c "
import yaml
with open('data/config/backlog.yaml') as f:
    d = yaml.safe_load(f)
print(len([t for t in d.get('tasks', []) if t.get('status', 'queued') != 'done']))
")
echo "state.db queued: $QUEUED | backlog.yaml tasks: $YAML_TASKS | drift: $((YAML_TASKS - QUEUED))"

# 2. Find zombie state.db rows (rows not in backlog.yaml)
python3 -m server.regen_backlog_from_plan --verbose --prune-stale --db-path data/state/state.db
```

Fleet-wide audit: `unified-trading-pm/scripts/orchestrator/verify_fleet_prune_state.sh` (fires per-VM SSM query,
computes drift, flags ✅/⚠️).

---

## Recovery if drift detected

### Orphan yaml tasks (bloat in backlog.yaml)

Enable `prune_stale` on the affected VM:

```bash
# 1. Via systemd drop-in (persistent)
cat > /etc/systemd/system/orchestrator.service.d/prune.conf <<EOF
[Service]
Environment=ORCHESTRATOR_REGEN_PRUNE_STALE=true
Environment=ORCHESTRATOR_REGEN_DB_PATH=/path/to/data/state/state.db
EOF
systemctl daemon-reload && systemctl restart orchestrator

# 2. Via CLI (one-shot, same session)
python3 -m server.regen_backlog_from_plan --prune-stale --db-path data/state/state.db
```

Fleet rollout: `unified-trading-pm/scripts/orchestrator/run_fleet_enable_prune.sh`.

### Zombie state.db rows (rows without matching backlog.yaml entry)

`prune_stale` also cleans state.db (only `status='queued' AND dispatched_to IS NULL`). If orphan rows are in status
`done` or `dispatched`, they are intentionally kept as audit history — do not delete manually.

### Brief-mutation accumulation

Root cause: each edit to an unchecked `- [ ] description` line generates a new `brief` that doesn't match the old brief,
causing a new task ID to be issued while the old one remains as an orphan. Fix: `prune_stale=true` with
`ORCHESTRATOR_VM_ID` scoping eliminates this accumulation going forward. One-shot cleanup requires running `prune_stale`
once on the affected VM.

### Same-plan brief collision silently conflates two todos (fixed `agent-orchestrator@3474b95`)

`plan_tasks_by_brief` was a plain `{brief: task}` dict — when two todos in the SAME plan hard-wrap to a byte-identical
first physical line (common when a plan clones a todo template across asset-group lanes and the distinguishing detail
falls on a wrapped continuation line), both resolved to ONE existing task on every regen tick: the LATER doc occurrence
always won `_reconcile_task_fields`, permanently overwriting the earlier task's `plan_order` (corrupting a
`sequential: true` chain) while the earlier occurrence never got its own task at all (silently invisible to dispatch,
its work never queued). Fix: `_group_plan_tasks_by_brief` groups existing same-plan tasks sharing a brief into a LIST
(sorted by id/creation order), and a per-tick `brief_occurrence_index` matches the Nth doc occurrence of a brief to the
Nth candidate positionally, instead of a `.get()` collapse; `_warn_on_brief_collisions` logs once per plan so a human
can reword the colliding lines. Root-caused + fixed via
`plans/archive/issues/mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29.md`.

### `sequential: true` chain-walk must exclude same-tick orphans (fixed `agent-orchestrator@77769ab`)

A same-tick TEXT reword of an open todo (e.g. a retag) makes the OLD row's brief stop matching any live todo (it's an
orphan, pending prune) while a FRESH row is created for the new text. If `_wire_sequential_prereqs`' chain walk runs
BEFORE `_prune_stale` removes that orphan in the same `regen()` pass, the orphan's stale `plan_order` can sort into the
middle of the fresh `(plan_order, id)` chain and hijack the immediate-predecessor slot — letting a downstream task
dispatch while its true (still-open) predecessor is still `queued`. Fix: restrict the chain walk to each tick's live
(non-orphan) task ids per plan. Same source issue doc as above.

### `/done`'s M3 checkbox-flip verification ALSO requires an exact brief match — annotate AFTER, never BEFORE

Same `brief` exact-single-line-match mechanism as "Brief-mutation accumulation" above, but a distinct consumer:
`server/verify.py::_brief_is_currently_checked` (the M3 gate `POST /api/slots/<N>/done` runs before accepting a
cross-repo plan-flip) requires a `- [x] <brief>` line where `<brief>` matches the task's dispatched `brief` field
**exactly**, on that one physical line — not the whole multi-line todo body. Flipping `[ ]`→`[x]` AND prepending your
own annotation/evidence text before the original brief on that SAME first line (e.g.
`- [x] ✅ **DONE 2026-...** — <your summary>. <original brief text>`) breaks the exact-match and the `/done` call is
rejected with `cross_repo_pm_file_touched_no_checkbox_flip` even though the flip genuinely happened (confirmed
2026-07-31, `defi_satellite_ao_dispatch_batch6-005`) — indistinguishable from the already-documented
`git mv`-in-same-commit trap in `unified-trading-pm/agents/RULES.md` § 2, but a different root cause. **Fix**: keep the
checkbox's first line byte-identical to the dispatched `brief` (just `[ ]`→`[x]`); put every annotation/evidence
paragraph on the lines/paragraphs AFTER it, never before it on the same line — matches the pattern already used
throughout this corpus for evidence-bearing flips (e.g. `- [x] ✅ [TAG] Pn. <original text unchanged>` followed by a new
paragraph starting `**DONE <date>** — ...`).

### A `done` task's checkbox is flipped back to `[ ]` after an audit — does dispatch notice?

**Mechanically**: yes, the work redispatches, but under a **new** task_id, not the old one. Next regen tick, the
reopened line is invisible to the reconcile match (`plan_tasks_by_brief` only looks at what's CURRENTLY in
`backlog.yaml`, and the old id was already pruned the tick it went `done`) — so `regen_backlog_from_plan.py`'s ADD pass
mints a fresh id and queues it like any other new todo. The **old** id's `TaskRow` is never touched — it keeps reading
`status=done` forever (see "Never delete done/dispatched rows" above), citing whatever `done_sha` the audit later
determined was wrong.

**The residual risk**: `_completed_task_satisfied` (`server/dispatch.py`) trusts ANY `status=done` row by task_id alone
— it has no notion of "is this id still the current representation of the work". For a `gate_on_depends`-wired plan this
mostly self-heals within one regen cycle (`_wire_gate_on_depends_prereqs` adds the new id to every downstream gate;
`_scrub_completed_upstream_prereqs` drops the stale old id the same tick it's pruned) — but the SAME function also
treats an id absent from both yaml and DB as satisfied (the 2026-06-29 whole-fleet-idle-block fix), so the window
between "old id scrubbed" and "new id wired in" is silently satisfied too, not blocked. A `completed_tasks` reference
set outside that auto-managed wiring (hand-authored — banned by the plan-authoring convention "no per-todo prereq
syntax", but the data model does not technically enforce the ban) never self-heals at all.

**Detection**: `scripts/orchestrator/audit_stale_gate_references.py` (shipped 2026-07-25, mirrors
`audit_false_done.py`'s pattern) finds the exact, mechanically-verifiable case — an orphaned `done` id still named in
some live task's `completed_tasks`, whose own plan currently has an open todo hashing IDENTICALLY to its stored
`brief_hash` (the same line, un-reworded, just un-checked). Runs hourly on the live VM via
`audit-stale-gate- references.timer` (see "Auditing `status=done` honesty" above) as well as on-demand; it is read-only
(report-only, no `--fix`) — correct a confirmed finding via `POST /api/backlog/{id}/reopen`-style mutation or by
re-wiring the affected plan's `depends_on`, not by hand-editing `backlog.yaml`. A clean run means "no exact-reopen
collision found", not "no drift is possible" — a reopened todo that was ALSO reworded on the same edit is undetectable
by this tool (no plaintext brief survives an orphaned row to fuzzy-match against). SSOT for the full investigation:
`plans/archive/issues/gate_completed_tasks_trusts_stale_done_after_checkbox_unflip_2026_07_25.md`.

---

## Anti-patterns

- **Never delete done/dispatched rows from state.db** — they are audit history + live work.
- **Never edit backlog.yaml manually to add/remove tasks** — `regen` is the SSOT; manual edits are overwritten or
  produce inconsistency. **Explicit park-only exception (ruled 2026-08-02,
  `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 2b):** tuning `priority` / `priority_override` /
  `prereqs.prerequisites` on an ALREADY-DERIVED entry to defer its dispatch — the "Park a task" recipe in
  `unified-trading-pm/agents/RULES.md` § 4 — is sanctioned for any agent, not operator-only. This is narrower than the
  ban above: it never adds a new id, never removes an existing one, and never hand-edits
  `title`/`description`/dependency-derived fields — those stay regen-only. A park survives the next regen tick only
  because `priority_override: true` is set alongside it (regen preserves, never reverts, an overridden priority);
  re-verify both fields stuck after the next `PlanRegenLoop` tick or `POST /api/backlog/regen`, per the known-bug note
  in RULES.md § 4.
- **Never run regen without `assigned_vm` scoping on multi-VM fleets** — without `ORCHESTRATOR_VM_ID` each VM ingests
  every plan → every VM's backlog = entire fleet's backlog.
- **Never set `ORCHESTRATOR_REGEN_PRUNE_STALE=false` when zombie count is high** — disable prune only for one-off
  diagnostics, then re-enable.
- **Never treat a missing `tasks` row as evidence of a lost task on its own** — see "The `tasks` table is a projection,
  not a completion ledger" above; check the plan file's checkbox first.

---

## Relationship to related systems

| System                          | Interaction                                                                                                                                        |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AutoSpawnLoop`                 | Reads `status='queued' AND dispatched_to IS NULL` — zombie rows trigger false autospawns. `prune_stale` eliminates this.                           |
| `FailoverLoop`                  | Reads `status='queued' AND dispatched_to IS NULL AND failover_allowed=True` — same zombie vulnerability.                                           |
| Manual `/api/backlog` POST      | Adds tasks directly without plan-todo dedup; these have empty `brief` and survive `prune_stale` (see invariant above).                             |
| `orchestrator_vm_registry.yaml` | Declares `master_plans` per VM (used by dispatcher affinity); `assigned_vm` in plans is the per-plan complement. Both are needed for full scoping. |
