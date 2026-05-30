# Plan Hygiene — Silent-Failure Capture Stack

> SSOT for the hygiene sweep, its 4 silent-failure detectors, cron schedules, and severity model.
> Cross-referenced from `plans/PLAN_FORMAT.md` § "Canonical form + automated hygiene".

---

## Why plan hygiene matters

Plans are the primary input to `regen_backlog_from_plan.py`, which seeds the dispatcher. A plan bug
that isn't caught within one cron cycle can:

- Cause tasks to rot in the queue (no P-priority → dispatcher de-prioritizes to `None`)
- Route work to the wrong VM (wrong `parent_epic` → operator confusion, no auto-detection)
- Make an entire plan invisible (authored but unpushed → zero tasks ingested)
- Leave tasks permanently blocked (blocker `done` but no one ran the unblock query)

The hygiene stack closes each of these gaps with an automated check that fires within 24 hours of
a regression being introduced.

---

## The 4 silent-failure modes

| # | Mode | Root cause | Detector | Severity |
|---|------|-----------|----------|---------|
| 1 | **Malformed todo format** | `- [ ]` line missing `P[0-3]` tag → regen assigns priority `None` → task sinks | `check_todo_format.sh` | **HARD** (exit 1 on NO_PRIORITY) |
| 2 | **Wrong `parent_epic`** | Plan body content mismatches declared epic → work routed to wrong VM | `check_parent_epic_alignment.py` | SOFT (warn only) |
| 3 | **Unpushed plan files** | Plan file dirty/untracked in a slot's PM worktree → invisible to all other VMs | `slot-git-status-report.sh` + Slack alert | Immediate Slack alert (no threshold) |
| 4 | **Stale blockers** | Blocker task `done` but blocked task stays `queued` forever | `reap_stale_blockers.py` cron (04:00 UTC) | Exit 1 on DEADLOCK/ORPHAN; info on PHANTOM_DONE |

### Mode 1: Malformed todo format

`check_todo_format.sh` scans every `- [ ]` line in `plans/active/*.md` and
`plans/active/issues/*.md` for two failures:

- **NO_PRIORITY** (❌ HARD): no `P[0-3]` tag anywhere → regen defaults priority to `None` →
  dispatcher de-prioritizes.
- **NON_CANONICAL** (⚠️ SOFT): has P-tag but bracket order is wrong (e.g. `[TAG][P0]`,
  `[P0][TAG]`, `[P0]` alone).

Auto-fixer: `bash scripts/plan-hygiene/fix_todo_format.sh` (dry-run by default; `--apply` to
write). Handles edge cases including `[TAG — qualifier] P<n>.` → `[TAG] P<n>. body — qualifier`
and `[CLAUDE.md] P<n>.` → `[CLAUDE-MD] P<n>.` (dots banned in tags).

### Mode 2: Wrong `parent_epic`

`check_parent_epic_alignment.py` scores each plan body against the keyword surfaces defined in
`codex/12-agent-workflow/epic-keyword-surface.yaml`. If the highest-scoring epic differs from the
plan's declared `parent_epic:`, a WARN is emitted with the top-3 scores. Soft check: the
heuristic can misfire on cross-domain plans (e.g. a CEFI backfill plan touches manifest + MDPS
keywords). Operators review the WARN list; no auto-fix.

### Mode 3: Unpushed plan files

`scripts/dev/slot-git-status-report.sh` reports a `unpushed_plans: [list]` field whenever a
plan file (`plans/active/*.md` or `plans/active/issues/*.md`) is dirty or untracked in the slot's
PM worktree. The orchestrator's `WorkerLivenessKicker._maybe_alert_unpushed_plans()` fires a
Slack alert immediately on first detection (no staleness threshold — any dirty plan is
operator-actionable). Alert format: `🔴 Slot N has unpushed plan(s): X.md, Y.md`.
Throttled to once per 30 min per slot to avoid spam.

### Mode 4: Stale blockers

`scripts/orchestrator/reap_stale_blockers.py` queries tasks where `status=queued`,
`prereqs.completed_tasks` includes a task not yet `done`, and `queued_at < now - 3 days`. Three
outcomes per finding:

- **PHANTOM_DONE** (info): blocker is `done` but the blocked task hasn't been picked up → auto-info
  log only; dispatcher will catch it on next tick.
- **DEADLOCK** (exit 1): both the task AND its blocker are stuck in `queued` → Slack alert with
  both task IDs; operator intervention required.
- **ORPHAN** (exit 1): blocker task ID not found in backlog at all → Slack alert; operator
  must reconcile or remove the prereq.

Run `--dry-run` to preview without alerts. Full doc: `codex/12-agent-workflow/stale-blocker-reaper.md`.

---

## Closed set of valid tags

Defined in `plans/PLAN_FORMAT.md` § "Canonical form + automated hygiene". Reproduced here for
quick reference (case-sensitive uppercase):

```
AGENT | SCRIPT | HUMAN | HUMAN+AGENT | AUDIT | DESIGN | SPEC | VERIFY | CONFIG | IMPLEMENT
DEFERRED | DELEGATED | UI
BLOCKED-CREDENTIALS | BLOCKED-OPERATOR-DECISION | BLOCKED-UPSTREAM-OUTAGE
BLOCKED-PLAYWRIGHT | BLOCKED-OPERATOR | BLOCKED-INFRA
```

**To add a new tag**: open a PR against `plans/PLAN_FORMAT.md` updating the closed-set block
above AND update `check_todo_format.sh`'s documentation comment if the new tag affects the
canonical-regex logic. Tags containing dots (e.g. `CLAUDE.md`) are banned — use hyphens
(`CLAUDE-MD`).

---

## Severity ladder

| Level | Condition | Sweep exit code | Action required |
|-------|-----------|-----------------|-----------------|
| **HARD** | `check_todo_format.sh` NO_PRIORITY ≥ 1 | Exit 1 (with `--ci`) | Fix before picking up new work |
| **HARD** | `check_todo_regression.sh` fails | Exit 1 (with `--ci`) | Revert or re-apply the intended change |
| **HARD** | `check_frontmatter.sh` fails | Exit 1 (with `--ci`) | Fix missing/invalid frontmatter fields |
| **HARD** | `check_runbook_fields.py` fails | Exit 1 (with `--ci`) | Add missing `owner`/`cadence`/`verifier`/`last_executed` |
| **SOFT** | NON_CANONICAL format (has P-tag) | Warn only | Auto-fix recommended; non-breaking |
| **SOFT** | `check_parent_epic_alignment.py` warns | Warn only | Operator review; may be intentional |
| **SOFT** | `check_line_caps.sh` (>500 / >1000 lines) | Warn only | Trim plan; split into sub-plans |
| **SOFT** | `check_estimate_sanity.sh` (±20% drift) | Warn only | Recalibrate estimate |
| **SOFT** | `check_superseded_in_active.sh` finds expired plans | Warn only | Archive candidates |
| **SOFT** | `check_codex_refs.sh` broken paths | Warn only | Fix or remove stale codex links |

Run the full sweep:

```bash
bash scripts/plan-hygiene/run_hygiene_sweep.sh        # interactive (always exits 0)
bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci   # CI/cron mode (exits 1 on hard failures)
```

---

## Cron schedules

Three crons form the hygiene pipeline. They are offset to avoid resource contention on the
planning VM:

| Cron | Schedule | Mechanism | Owner | Log |
|------|----------|-----------|-------|-----|
| **Stale-blocker reaper** | `04:00 UTC daily` | systemd `reap-stale-blockers.timer` on orchestrator VM | `vm-orchestrator` | `/var/log/orchestrator/reap_<date>.log` |
| **Plan hygiene sweep** | `05:00 UTC daily` (`0 5 * * *`) | GCP Cloud Run Job `uts-prod-plan-hygiene-sweep` | `vm-orchestrator` | Cloud Run Logs |
| **Orphan-ping audit** | `Every 4h` (`0 */4 * * *`) | GCP Cloud Run Job `uts-prod-orphan-ping-audit` (+ local crontab) | `vm-orchestrator` + local | `/tmp/orphan_pings_audit.log` |

### Reaper install

The stale-blocker reaper must run on the orchestrator VM (direct SQLite `state.db` access):

```bash
sudo bash scripts/orchestrator/install_reap_stale_blockers.sh
```

See `codex/12-agent-workflow/stale-blocker-reaper.md` for full operator guide.

### Orphan-ping install (local)

```bash
crontab -e
# Add:
0 */4 * * * cd ${WORKSPACE_ROOT}/unified-trading-pm && bash scripts/agents/audit_ping_orphans.sh >> /tmp/orphan_pings_audit.log 2>&1
```

---

## Cross-references

- Canonical tag set + format spec: `plans/PLAN_FORMAT.md` § "Cursor-Friendly Todo Checkboxes"
- Stale-blocker reaper detail: `codex/12-agent-workflow/stale-blocker-reaper.md`
- Unpushed-plan Slack alert: `codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md` § "Drift reporter"
- Epic keyword surface (parent_epic check): `codex/12-agent-workflow/epic-keyword-surface.yaml`
- Auto-fixer: `scripts/plan-hygiene/fix_todo_format.sh`
- Sweep runner: `scripts/plan-hygiene/run_hygiene_sweep.sh`
