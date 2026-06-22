---
scope: [engineer, admin]
last_reviewed: 2026-05-30
---

# Agent Orchestrator — Backlog ↔ State DB Alignment Architecture

> **SSOT**: `agent-orchestrator/server/regen_backlog_from_plan.py` **Plan**:
> `plans/active/agent_orchestrator_backlog_state_alignment_2026_05_29.md` **Overview pointer**:
> `codex/04-architecture/agent-orchestrator-overview.md`

## Problem statement

The orchestrator maintains two task stores:

| Store                    | Location                   | Owner                                       |
| ------------------------ | -------------------------- | ------------------------------------------- |
| `backlog.yaml`           | `data/config/backlog.yaml` | `regen_backlog_from_plan.py` + manual edits |
| `state.db` `tasks` table | `data/state/state.db`      | Dispatcher + worker lifecycle               |

**Drift** occurs when rows exist in `state.db` that are no longer in `backlog.yaml` (zombies from completed plans), or
when `backlog.yaml` contains stale tasks whose plan-todo lines have been edited or removed. Without cleanup, zombie rows
accumulate and inflate queue counts, causing false "work available" signals.

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
    ├─ skip: INDEX.md, _agent_pings.md, _*.md
    ├─ [scope filter] skip plans where assigned_vm ≠ this VM's ORCHESTRATOR_VM_ID
    │  (global plans with no assigned_vm are included by every VM)
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
       - build current_briefs from same scope-filtered plan files
       - any yaml task whose brief ∉ current_briefs = orphan
       - delete orphan yaml entries
       - DELETE orphan state.db rows WHERE status='queued' AND dispatched_to IS NULL
       - NEVER touch done / dispatched rows
```

---

## Invariants

| Invariant                                                             | How enforced                                                                      |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **Dedup by brief**: same description text → same task, not duplicated | `existing_briefs` set; re-runs skip already-seen descriptions                     |
| **Dedup by task_id**: same slug-NNN → never re-issued                 | `existing_ids` set; `while task_id in existing_ids: next_index += 1`              |
| **No task steal**: dispatched rows never deleted                      | `prune_stale` filters `status='queued' AND dispatched_to IS NULL` only            |
| **Audit history preserved**: done rows never deleted                  | Same `prune_stale` filter                                                         |
| **Idempotent re-runs**: running regen twice produces the same state   | Both dedup sets guarantee this                                                    |
| **Per-VM scope**: each VM only sees its assigned plans                | `assigned_vm` frontmatter filter; global plans (no `assigned_vm`) seen by all VMs |

---

## Per-VM scope filter

```yaml
# plan frontmatter example
---
assigned_vm: vm-ml
title: "features registry versioning"
---
```

- If `assigned_vm: vm-ml` and `ORCHESTRATOR_VM_ID=vm-cefi` → plan skipped.
- If `assigned_vm: vm-ml` and `ORCHESTRATOR_VM_ID=vm-ml` → plan included.
- If `assigned_vm` absent → plan included on every VM (global plan).
- If `ORCHESTRATOR_VM_ID` unset → no filter (backward compatible; all plans ingested).

Configure via systemd drop-in:

```ini
# /etc/systemd/system/orchestrator.service.d/vm-scope.conf
[Service]
Environment=ORCHESTRATOR_VM_ID=vm-ml
```

---

## Environment variables

| Variable                                   | Default                 | Purpose                                                             |
| ------------------------------------------ | ----------------------- | ------------------------------------------------------------------- |
| `ORCHESTRATOR_PM_REPO_PATH`                | `../unified-trading-pm` | Override PM repo location                                           |
| `ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS` | `1800`                  | Tick cadence (30 min; was 6 h/21600); set to `0` to disable         |
| `ORCHESTRATOR_REGEN_PRUNE_STALE`           | `false`                 | Enable orphan pruning on every tick                                 |
| `ORCHESTRATOR_REGEN_DB_PATH`               | —                       | state.db path for safe-row deletion (yaml-only prune when unset)    |
| `ORCHESTRATOR_VM_ID`                       | —                       | VM identifier for `assigned_vm` scope filter (no filter when unset) |

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

### Brief-mutation accumulation (vm-ml/vm-trading-core historical bloat)

Root cause: each edit to an unchecked `- [ ] description` line generates a new `brief` that doesn't match the old brief,
causing a new task ID to be issued while the old one remains as an orphan. Fix: `prune_stale=true` with
`ORCHESTRATOR_VM_ID` scoping eliminates this accumulation going forward. One-shot cleanup requires running `prune_stale`
once on the affected VM.

---

## Anti-patterns

- **Never delete done/dispatched rows from state.db** — they are audit history + live work.
- **Never edit backlog.yaml manually to add/remove tasks** — `regen` is the SSOT; manual edits are overwritten or
  produce inconsistency.
- **Never run regen without `assigned_vm` scoping on multi-VM fleets** — without `ORCHESTRATOR_VM_ID` each VM ingests
  every plan → every VM's backlog = entire fleet's backlog.
- **Never set `ORCHESTRATOR_REGEN_PRUNE_STALE=false` when zombie count is high** — disable prune only for one-off
  diagnostics, then re-enable.

---

## Relationship to related systems

| System                          | Interaction                                                                                                                                        |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AutoSpawnLoop`                 | Reads `status='queued' AND dispatched_to IS NULL` — zombie rows trigger false autospawns. `prune_stale` eliminates this.                           |
| `FailoverLoop`                  | Reads `status='queued' AND dispatched_to IS NULL AND failover_allowed=True` — same zombie vulnerability.                                           |
| Manual `/api/backlog` POST      | Adds tasks directly without plan-todo dedup; these have empty `brief` and survive `prune_stale` (see invariant above).                             |
| `orchestrator_vm_registry.yaml` | Declares `master_plans` per VM (used by dispatcher affinity); `assigned_vm` in plans is the per-plan complement. Both are needed for full scoping. |
