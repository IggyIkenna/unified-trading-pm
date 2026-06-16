---
scope: [engineer, admin]
---

# Plan Hygiene — Silent Failure Modes, Tags, Crons, and Severity

> SSOT for the plan-hygiene guard system: what can go silently wrong, which script catches it, how severe it is, and
> when the automated sweeps run. Cross-referenced from `plans/PLAN_FORMAT.md` § "Canonical form + automated hygiene".
>
> Codified 2026-05-30 per `plan_hygiene_silent_failure_capture_2026_05_29.md` Phase 5.

---

## Why plan hygiene matters

Plans are the primary input to `regen_backlog_from_plan.py`, which seeds the dispatcher. A plan bug that isn't caught
within one cron cycle can:

- Cause tasks to rot in the queue (no P-priority → dispatcher de-prioritizes to `None`)
- Route work to the wrong VM (wrong `parent_epic` → operator confusion, no auto-detection)
- Make an entire plan invisible (authored but unpushed → zero tasks ingested)
- Leave tasks permanently blocked (prereq done but no one ran the unblock query)

The hygiene stack closes each of these gaps with an automated check that fires within 24 hours of a regression being
introduced.

---

## TL;DR

```
[1] Plans land on disk                  (operator / worker commits + pushes)
       ↓
[2] 4 silent-failure modes can break    (wrong format, wrong epic, unpushed, stuck-blocked)
       ↓
[3] 3 automated sweeps catch failures   (04:00 reaper, 05:00 hygiene, every-4h orphan-ping)
       ↓
[4] HARD failures block the sweep       (exit 1 → operator must fix before picking up new work)
[4] SOFT warnings surface in dashboard  (warn only → advisory; low-priority fix)
```

---

## The 4 Silent-Failure Modes

| #   | Mode                      | Root cause                                                                     | Detector                                  | Severity                                        |
| --- | ------------------------- | ------------------------------------------------------------------------------ | ----------------------------------------- | ----------------------------------------------- |
| 1   | **Malformed todo format** | `- [ ]` line missing `P[0-3]` tag → regen assigns priority `None` → task sinks | `check_todo_format.sh`                    | **HARD** (exit 1 on NO_PRIORITY)                |
| 2   | **Wrong `parent_epic`**   | Plan body content mismatches declared epic → work routed to wrong VM           | `check_parent_epic_alignment.py`          | SOFT (warn only)                                |
| 3   | **Unpushed plan files**   | Plan file dirty/untracked in a slot's PM worktree → invisible to all other VMs | `slot-git-status-report.sh` + Slack alert | Immediate Slack alert (no threshold)            |
| 4   | **Stale blockers**        | Blocker task `done` but blocked task stays `queued` forever                    | `reap_stale_blockers.py` cron (04:00 UTC) | Exit 1 on DEADLOCK/ORPHAN; info on PHANTOM_DONE |

### Mode 1: Malformed todo format

`check_todo_format.sh` scans every `- [ ]` line in `plans/active/*.md` and `plans/active/issues/*.md` for two failures:

- **NO_PRIORITY** (❌ HARD): no `P[0-3]` tag anywhere → regen defaults priority to `None` → dispatcher de-prioritizes.
- **NON_CANONICAL** (⚠️ SOFT): has P-tag but bracket order is wrong (e.g. `[TAG][P0]`, `[P0][TAG]`, `[P0]` alone).

Auto-fixer: `bash scripts/plan-hygiene/fix_todo_format.sh` (dry-run by default; `--apply` to write). Handles edge cases
including `[TAG — qualifier] P<n>.` → `[TAG] P<n>. body — qualifier` and `[CLAUDE.md] P<n>.` → `[CLAUDE-MD] P<n>.` (dots
banned in tags).

### Mode 2: Wrong `parent_epic`

`check_parent_epic_alignment.py` scores each plan body against the keyword surfaces defined in
`codex/12-agent-workflow/epic-keyword-surface.yaml`. If the highest-scoring epic differs from the plan's declared
`parent_epic:`, a WARN is emitted with the top-3 scores. Soft check: the heuristic can misfire on cross-domain plans
(e.g. a CEFI backfill plan touches manifest + MDPS keywords). Operators review the WARN list; no auto-fix.

### Mode 3: Unpushed plan files

`scripts/dev/slot-git-status-report.sh` reports an `unpushed_plans: [list]` field whenever a plan file
(`plans/active/*.md` or `plans/active/issues/*.md`) is dirty or untracked in the slot's PM worktree. The orchestrator's
`WorkerLivenessKicker._maybe_alert_unpushed_plans()` fires a Slack alert immediately on first detection (no staleness
threshold — any dirty plan is operator-actionable). Alert format: `🔴 Slot N has unpushed plan(s): X.md, Y.md`.
Throttled to once per 30 min per slot to avoid spam.

### Mode 4: Stale blockers

`scripts/orchestrator/reap_stale_blockers.py` queries tasks where `status=queued`, `prereqs.completed_tasks` includes a
task not yet `done`, and `queued_at < now - 3 days`. Three outcomes per finding:

- **PHANTOM_DONE** (info): blocker is `done` but the blocked task hasn't been picked up → auto-info log only; dispatcher
  will catch it on next tick.
- **DEADLOCK** (exit 1): both the task AND its blocker are stuck in `queued` → Slack alert with both task IDs; operator
  intervention required.
- **ORPHAN** (exit 1): blocker task ID not found in backlog at all → Slack alert; operator must reconcile or remove the
  prereq.

Run `--dry-run` to preview without alerts. Full doc: `codex/12-agent-workflow/stale-blocker-reaper.md`.

---

## Severity Ladder

The full sweep (`run_hygiene_sweep.sh`) classifies every check as HARD or SOFT:

### HARD — sweep exits 1, operator must fix before picking up new work

| Check                     | Script                     | Trigger                                                                        |
| ------------------------- | -------------------------- | ------------------------------------------------------------------------------ |
| Todo regression vs origin | `check_todo_regression.sh` | Any open `- [ ]` in origin was flipped/removed locally without a push          |
| Frontmatter validity      | `check_frontmatter.sh`     | Missing required frontmatter keys (`parent_epic`, `assigned_vm`, `estimate_*`) |
| Todo format — NO_PRIORITY | `check_todo_format.sh`     | `- [ ]` line has no `P[0-3]` anywhere; regen assigns `priority=None`           |
| Runbook governance fields | `check_runbook_fields.py`  | Runbook missing `owner` / `cadence` / `verifier` / `last_executed`             |

### SOFT — sweep warns, sweep exits 0, advisory only

| Check                       | Script                           | Trigger                                                                  |
| --------------------------- | -------------------------------- | ------------------------------------------------------------------------ |
| Todo format — NON_CANONICAL | `check_todo_format.sh`           | Has P-priority but wrong bracket format (e.g. `[TAG][P0]`)               |
| Parent-epic alignment       | `check_parent_epic_alignment.py` | `parent_epic:` value doesn't match a known epic keyword                  |
| Line caps                   | `check_line_caps.sh`             | Plan exceeds 500 lines (soft) or 1000 lines (hard cap within soft check) |
| Estimate sanity             | `check_estimate_sanity.sh`       | `estimate_calibrated_ai_days` drifts >20% from class-multiplied baseline |
| Superseded plans in active/ | `check_superseded_in_active.sh`  | Active plan has a `SUPERSEDED` banner (should be archived)               |
| Codex path refs resolve     | `check_codex_refs.sh`            | Codex link in a plan points to a non-existent file                       |

### Stale-blocker reaper (separate cron, separate severity)

The reaper (`reap_stale_blockers.py`) runs at **04:00 UTC**, 1 hour before the hygiene sweep. It has its own exit codes:

- Exit 0 — clean or PHANTOM_DONE only (informational; resolves on next worker boot)
- Exit 1 — DEADLOCK or ORPHAN found → Slack alert to orchestrator inboxes

---

## Closed Set of Valid Tags

Defined in `plans/PLAN_FORMAT.md` § "Canonical form + automated hygiene". Reproduced here for quick reference
(case-sensitive uppercase):

### Role tags

```
AGENT          Worker (AI agent) executes this
SCRIPT         Operator runs a named script
HUMAN          Operator action required; not dispatchable
HUMAN+AGENT    Joint: operator decision + agent implementation
AUDIT          Audit task (read-only investigation)
DESIGN         Architecture or design decision
SPEC           Specification authoring
VERIFY         Verification / QA / sampling task
CONFIG         Configuration change
IMPLEMENT      Implementation (prefer AGENT for agent-dispatchable items)
DEFERRED       Explicitly deferred with a named successor plan
DELEGATED      Handed off to another slot or operator
UI             UI modifier (appended as second tag, e.g. [AGENT] [UI] P1.)
CLAUDE-MD      CLAUDE.md / workspace config update
```

### Blocked-status tags (replace role tag when a task is externally blocked)

```
BLOCKED-CREDENTIALS        Waiting for operator to provision API key / account
BLOCKED-OPERATOR-DECISION  Waiting for operator to choose between named options
BLOCKED-UPSTREAM-OUTAGE    Third-party degraded; auto-resumes on health check
BLOCKED-PLAYWRIGHT         UI task on a fleet VM without a dev server
BLOCKED-OPERATOR           Generic operator unblock required
BLOCKED-INFRA              Infrastructure blocker (e.g. quota, VM unavailable)
```

### How to add a new tag

1. Open a PR to `plans/PLAN_FORMAT.md` — add the tag to the closed-set block in § "Cursor-Friendly Todo Checkboxes".
2. Update `CANONICAL_BODY_RE` in `scripts/plan-hygiene/check_todo_format.sh` if the tag has unusual casing or structure
   (standard `[A-Z][A-Z0-9_-]*` pattern covers most new tags automatically).
3. Run `bash scripts/plan-hygiene/check_todo_format.sh` after merging to confirm no existing todos are newly flagged.
4. Cross-link the new tag in this file under the correct category.

> A tag with dots (e.g. `[CLAUDE.md]`) or em-dashes inside brackets (e.g. `[BLOCKED — REASON]`) is **invalid** — the
> regex won't match it and `check_todo_format.sh` will flag all lines using it as NON_CANONICAL. Use hyphens:
> `[CLAUDE-MD]`, `[BLOCKED-REASON]`.

---

## Automated Cron Schedules

Three sweeps run on a fixed UTC schedule, offset to avoid resource contention on the planning VM:

| Sweep                | Schedule                                | Mechanism                                                                              | Log                                     |
| -------------------- | --------------------------------------- | -------------------------------------------------------------------------------------- | --------------------------------------- |
| Stale-blocker reaper | **04:00 UTC daily**                     | systemd `reap-stale-blockers.timer` on orchestrator VM                                 | `/var/log/orchestrator/reap_<date>.log` |
| Plan-hygiene sweep   | **05:00 UTC daily**                     | GCP Cloud Run Job `uts-prod-plan-hygiene-sweep` (+ systemd `plan-hygiene-sweep.timer`) | Cloud Run Logs                          |
| Orphan-ping audit    | **Every 4h** (`15 2,6,10,14,18,22 UTC`) | GCP Cloud Scheduler `uts-prod-orphan-ping-audit` + local crontab                       | `/tmp/orphan_pings_audit.log`           |

### Why the reaper runs 1 hour before the hygiene sweep

The reaper resolves PHANTOM_DONE states (blocker marked `done` but dependent still `queued`) before the sweep scans
prereq chains. This avoids false-positive DEADLOCK alerts that would self-resolve on the next worker `/boot`.

### Installer commands

```bash
# Stale-blocker reaper systemd timer
sudo bash scripts/orchestrator/install_reap_stale_blockers.sh

# Orphan-ping (local crontab)
crontab -e
# Add:
0 */4 * * * cd ${WORKSPACE_ROOT}/unified-trading-pm && bash scripts/agents/audit_ping_orphans.sh >> /tmp/orphan_pings_audit.log 2>&1
```

---

## Running the Sweep Manually

```bash
# Interactive (always exits 0 — prints PASS/FAIL table):
bash unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh

# CI mode (exits 1 on any HARD failure):
bash unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh --ci

# Individual checks (verbose output):
bash unified-trading-pm/scripts/plan-hygiene/check_todo_format.sh
bash unified-trading-pm/scripts/plan-hygiene/check_frontmatter.sh
python3 unified-trading-pm/scripts/plan-hygiene/check_parent_epic_alignment.py

# Auto-fix NON_CANONICAL todos (dry-run first):
bash unified-trading-pm/scripts/plan-hygiene/fix_todo_format.sh
bash unified-trading-pm/scripts/plan-hygiene/fix_todo_format.sh --apply
```

---

## Cross-References

- `plans/PLAN_FORMAT.md` — canonical tag set + todo format spec (§ "Cursor-Friendly Todo Checkboxes")
- `scripts/plan-hygiene/check_todo_format.sh` — NO_PRIORITY / NON_CANONICAL detection logic
- `scripts/plan-hygiene/fix_todo_format.sh` — mechanical rewriter for NON_CANONICAL patterns
- `scripts/plan-hygiene/run_hygiene_sweep.sh` — the full 9-check sweep orchestrator
- `codex/12-agent-workflow/stale-blocker-reaper.md` — blocker-reaper design, DEADLOCK/ORPHAN/PHANTOM_DONE categories
- `codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md` — unpushed-plan Slack alert (silent-failure
  mode 3)
- `codex/12-agent-workflow/epic-keyword-surface.yaml` — epic keyword surface for parent_epic alignment check
- `plans/active/plan_hygiene_silent_failure_capture_2026_05_29.md` — the plan that produced this doc
