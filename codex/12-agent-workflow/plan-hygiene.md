# Plan Hygiene — Silent Failure Modes, Tags, Crons, and Severity

> SSOT for the plan-hygiene guard system: what can go silently wrong, which script catches it,
> how severe it is, and when the automated sweeps run.
>
> Codified 2026-05-30 per `plan_hygiene_silent_failure_capture_2026_05_29.md` Phase 5.

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

| # | Mode | What goes wrong | Detection | Severity |
|---|------|-----------------|-----------|----------|
| 1 | **Malformed todo format** | `- [ ]` line has wrong tag/priority format. `regen_backlog_from_plan.py` ingests any `- [ ]` line, but a line with no `P[0-3]` anywhere gets `priority=None` — the dispatcher de-prioritises it to the bottom of the queue indefinitely. | `check_todo_format.sh` | HARD (missing P-tag) / SOFT (has priority, wrong format) |
| 2 | **Wrong `parent_epic`** | An active plan's `parent_epic:` frontmatter value doesn't match any known epic keyword. The regen loop treats the plan as an orphan and the inventory regenerator flags it in the dashboard. | `check_parent_epic_alignment.py` | SOFT |
| 3 | **Unpushed plan files** | A worker authors or updates a plan locally but never pushes. The regen loop on the orchestrator host never sees the change — todos stay invisible and are not dispatched. | `slot-git-status-report.sh` (posts to `/api/slots/<N>/git-status` every 5 min; dirty `plans/active/*.md` paths trigger a Slack alert throttled to 1/slot/30 min) | HARD (alert-on-detect; operator must push) |
| 4 | **Stale-blocked tasks** | A task's prereq task is itself stuck (`queued` with unmet prereqs), or the prereq task_id no longer exists in the backlog. The dispatcher skips the blocked task silently on every worker `/boot` cycle — it never escalates. | `reap_stale_blockers.py` — classifies `DEADLOCK` (both blocked), `ORPHAN` (missing prereq), `PHANTOM_DONE` (resolves next boot) | HARD for DEADLOCK/ORPHAN (exit 1 → Slack alert) |

---

## Severity Ladder

The full sweep (`run_hygiene_sweep.sh`) classifies every check as HARD or SOFT:

### HARD — sweep exits 1, operator must fix before picking up new work

| Check | Script | Trigger |
|-------|--------|---------|
| Todo regression vs origin | `check_todo_regression.sh` | Any open `- [ ]` in origin was flipped/removed locally without a push |
| Frontmatter validity | `check_frontmatter.sh` | Missing required frontmatter keys (`parent_epic`, `assigned_vm`, `estimate_*`) |
| Todo format — NO_PRIORITY | `check_todo_format.sh` | `- [ ]` line has no `P[0-3]` anywhere; regen assigns `priority=None` |
| Runbook governance fields | `check_runbook_fields.py` | Runbook missing `owner` / `cadence` / `verifier` / `last_executed` |

### SOFT — sweep warns, sweep exits 0, advisory only

| Check | Script | Trigger |
|-------|--------|---------|
| Todo format — NON_CANONICAL | `check_todo_format.sh` | Has P-priority but wrong bracket format (e.g. `[TAG][P0]`) |
| Parent-epic alignment | `check_parent_epic_alignment.py` | `parent_epic:` value doesn't match a known epic keyword |
| Line caps | `check_line_caps.sh` | Plan exceeds 500 lines (soft) or 1000 lines (hard cap within soft check) |
| Estimate sanity | `check_estimate_sanity.sh` | `estimate_calibrated_ai_days` drifts >20% from class-multiplied baseline |
| Superseded plans in active/ | `check_superseded_in_active.sh` | Active plan has a `SUPERSEDED` banner (should be archived) |
| Codex path refs resolve | `check_codex_refs.sh` | Codex link in a plan points to a non-existent file |

### Stale-blocker reaper (separate cron, separate severity)

The reaper (`reap_stale_blockers.py`) runs at **04:00 UTC**, 1 hour before the hygiene sweep. It has its own exit codes:

- Exit 0 — clean or PHANTOM_DONE only (informational; resolves on next worker boot)
- Exit 1 — DEADLOCK or ORPHAN found → Slack alert to orchestrator inboxes

---

## Closed Set of Valid Tags

Tags appear in the role-tag bracket immediately after `- [ ] ` (canonical form: `- [ ] [TAG] P<n>. description`).

The tag set is **closed** — the regex enforces `[A-Z][A-Z0-9_-]*` (uppercase, digits, hyphens only; no dots, no spaces, no em-dashes in the tag itself).

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

1. Open a PR to `plans/PLAN_FORMAT.md` — add the tag to the closed-set table in § "Cursor-Friendly Todo Checkboxes".
2. Update `CANONICAL_BODY_RE` in `scripts/plan-hygiene/check_todo_format.sh` if the tag has unusual casing or structure
   (standard `[A-Z][A-Z0-9_-]*` pattern covers most new tags automatically).
3. Run `bash scripts/plan-hygiene/check_todo_format.sh` after merging to confirm no existing todos are newly flagged.
4. Cross-link the new tag in `codex/12-agent-workflow/plan-hygiene.md` (this file) under the correct category.

> A tag with dots (e.g. `[CLAUDE.md]`) or em-dashes inside brackets (e.g. `[BLOCKED — REASON]`) is **invalid** —
> the regex won't match it and `check_todo_format.sh` will flag all lines using it as NON_CANONICAL. Use hyphens:
> `[CLAUDE-MD]`, `[BLOCKED-REASON]`.

---

## Automated Cron Schedules

Three sweeps run on a fixed UTC schedule. All three are installed on the orchestrator VM:

| Sweep | Schedule | Script | Exit semantics |
|-------|----------|--------|----------------|
| Stale-blocker reaper | **04:00 UTC daily** (systemd timer: `reap-stale-blockers.timer`) | `scripts/orchestrator/reap_stale_blockers.py` | Exit 1 → DEADLOCK/ORPHAN found → Slack alert |
| Plan-hygiene sweep | **05:00 UTC daily** (systemd timer: `cron_hygiene_sweep_entrypoint.sh`) | `scripts/plan-hygiene/run_hygiene_sweep.sh --ci` | Exit 1 → any HARD check fails → orchestrator inboxes notified |
| Orphan-ping audit | **Every 4h** at `15 2,6,10,14,18,22 UTC` (GCP Cloud Scheduler + local crontab) | `scripts/agents/audit_ping_orphans.sh` | Appends `## [orphan-ping-cron]` notification to both orchestrator inboxes if orphans found |

### Why the reaper runs 1 hour before the hygiene sweep

The reaper resolves PHANTOM_DONE states (blocker marked `done` but dependent still `queued`) before the sweep scans
prereq chains. This avoids false-positive DEADLOCK alerts that would self-resolve on the next worker `/boot`.

### Installer commands

```bash
# Stale-blocker reaper systemd timer
sudo bash scripts/orchestrator/install_reap_stale_blockers.sh

# Plan-hygiene sweep systemd timer
# (entrypoint: scripts/plan-hygiene/cron_hygiene_sweep_entrypoint.sh)
sudo systemctl enable --now plan-hygiene-sweep.timer

# Orphan-ping (local cron)
crontab -e
# Add: 15 */4 * * * cd ${WORKSPACE_ROOT}/unified-trading-pm && bash scripts/agents/audit_ping_orphans.sh >> /tmp/orphan_pings_audit.log 2>&1
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

- `plans/PLAN_FORMAT.md` — canonical todo format + full tag table (§ "Cursor-Friendly Todo Checkboxes")
- `scripts/plan-hygiene/check_todo_format.sh` — NO_PRIORITY / NON_CANONICAL detection logic
- `scripts/plan-hygiene/fix_todo_format.sh` — mechanical rewriter for NON_CANONICAL patterns
- `scripts/plan-hygiene/run_hygiene_sweep.sh` — the full 9-check sweep orchestrator
- `codex/12-agent-workflow/stale-blocker-reaper.md` — blocker-reaper design, DEADLOCK/ORPHAN/PHANTOM_DONE categories
- `codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md` — unpushed-plan alert (silent-failure mode 3)
- `plans/active/plan_hygiene_silent_failure_capture_2026_05_29.md` — the plan that produced this doc
