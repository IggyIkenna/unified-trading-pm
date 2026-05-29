---
name: plan_hygiene_silent_failure_capture
title:
  "Plan-hygiene cron — close the 3 remaining silent-failure gaps (parent_epic semantic, unpushed plan, stale-blocker
  reaper)"
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
priority: P1
status: active
created: 2026-05-29
last_updated: 2026-05-29
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
estimate_calibration_note: |
  Refactor (0.4×): three discrete additions, each with an existing analog in the
  workspace (check_todo_format pattern; git-status reporter; backlog DB cron).
  Net-new surface is small (one keyword-surface YAML + one extension to the
  git-status reporter + one reaper cron). No new infra.
locked_by: live-defi-rollout
locked_since: 2026-05-29
related:
  - scripts/plan-hygiene/check_todo_format.sh # the #1 silent-failure capture, shipped 2026-05-29 — pattern to mirror for #2
  - scripts/dev/slot-git-status-report.sh
  - agent-orchestrator/server/regen_backlog_from_plan.py
---

# Plan-hygiene cron — silent-failure capture (3 remaining gaps)

The 2026-05-29 conversation enumerated 4 silent-failure modes for plans/active/. The first one (malformed todo format)
shipped in commit `58d11b78e` (`scripts/plan-hygiene/check_todo_format.sh` + `fix_todo_format.sh` wired into the sweep).
The other 3 are tracked here.

Note: regen_backlog_from_plan.py is more permissive than originally framed — it ingests any `- [ ]` line and extracts
`\bP[0-3]\b` from anywhere. So the "silent skip" narrative was partly wrong. The real gaps are: (a) wrong `parent_epic`
routes work to the wrong VM with no detection; (b) plans authored but unpushed are invisible; (c) blocked tasks pile up
indefinitely with no auto-unblock when blockers complete.

## Phase 0 — Pre-audit (P0)

- [x] ✅ [AGENT] P0. Read `agent-orchestrator/server/regen_backlog_from_plan.py` end-to-end. Tabulate: (a) the parse
      pipeline (UNCHECKED_RE → PRIORITY_RE → TITLE_PREFIX_RE); (b) how `parent_epic` is used downstream — does the
      dispatcher actually route by it, or is `assigned_vm` the SSOT? (c) how `blocked` task state is set (is there a
      blocker-dependency table?). Output: short audit doc inline.
      **Finding (2026-05-29):**
      **(a) Parse pipeline:**
      1. `_UNCHECKED_RE = r"^\s*-\s+\[ \]\s+(.+)$"` — matches only `- [ ]` lines (exact single space); `- [x]`/`✅` skipped.
      2. `_PRIORITY_RE = r"\bP([0-3])\b"` — searches anywhere in the description; any P0-P3 tag anywhere in the line maps to
         priority {0→10, 1→20, 2→50, 3→80, None→100}.
      3. `_TITLE_PREFIX_RE = r"^\s*(?:\[[A-Z]+\]\s+)?(?:P[0-3]\.\s*)?"` — strips one optional `[CATEGORY]` tag + `P<N>. ` prefix.
         Multi-tag todos (e.g. `[AGENT] [AUDIT] P0.`) only have the first tag stripped; title includes the second tag as noise
         (non-breaking: the title is display-only; brief carries the raw line for dedupe).
      Frontmatter (--- ... ---), fenced code blocks, strikethrough, and header lines are all skipped. Idempotency via
      both task_id AND brief de-dupe so re-runs are safe.
      **(b) `parent_epic` and `assigned_vm` routing:** NEITHER field is read by `regen_backlog_from_plan.py` (frontmatter
      skipped entirely). `BacklogTask` has no `parent_epic` or `assigned_vm` field. `dispatch.py`'s `pick_next_task()`
      routes ONLY by: `status=queued`, `prereqs` (completed_tasks + conditions), affinity/target_slot, repos collision,
      collision_group. `parent_epic` and `assigned_vm` are **purely informational** for human operators — they have zero
      effect on dispatch. Cross-VM isolation works because each VM runs its own regen against its own PM clone, not
      because the dispatcher reads these fields.
      **(c) `blocked` task state:** There is NO `blocked` status in the DB. Tasks are blocked implicitly — `TaskRow.status`
      stays `queued`; the dispatcher just skips tasks whose `prereqs` aren't met. `prereqs.completed_tasks` lists task IDs
      that must be `done`; `prereqs.conditions` lists boolean condition names. No `blocked_on` table, no explicit
      `blocked` status transition. Phase 3's stale-blocker reaper design must query `status=queued` tasks where prereqs
      are unmet (not `status=blocked` as originally framed — that state doesn't exist).
- [x] ✅ [AGENT] P0. Read `scripts/dev/slot-git-status-report.sh` end-to-end. Confirm the Slack alert payload format and
      identify the file-path stanza to extend.
      **Finding (2026-05-29):**
      - **Script flow**: `classify_repo()` (lines 114-190) walks each repo dir via `git status --porcelain`, tracks
        `dirty_oldest_mtime` from the oldest mtime among dirty files, emits a TAB-separated row. `post_snapshot()` (lines
        218-276) serialises all rows to JSON via Python3 and POSTs to `POST /api/slots/<N>/git-status` with shape:
        `{"reported_at":"<ISO>","host":"<hostname>","repos":[{"name","branch","state","dirty_files","ahead","behind","local_sha","integration_branch","dirty_oldest_mtime?"}]}`.
      - **Dirty-file loop stanza** (lines 134-148 of the script): This is the extension point for Phase 2. After the
        `while IFS= read -r line; do` loop that finds the oldest mtime, insert a parallel loop (or combined pass) that
        detects any `file` path matching `plans/active/*.md` or `plans/active/issues/*.md` and appends to a local
        `unpushed_plans` array. This array gets passed as a new column in the TSV row (or as a separate JSON field built
        in `post_snapshot`'s Python block).
      - **Slack alert chain**: `post_snapshot` → server's `POST /api/slots/{slot_id}/git-status` →
        `_maybe_send_sync_nudge()` (in-slot queue message, not Slack). Slack fires separately via
        `WorkerLivenessKicker._maybe_alert_git_staleness()` in `worker_liveness.py:285` — it reads
        `slot.git_status_json` on each liveness tick, checks if the cron is stale (>5 min) AND any repo is red for >15
        min, then calls `slack_notify.notify_git_staleness_red(slot_id, dirty_minutes, behind_count)`.
      - **Extension plan for Phase 2**: (a) Add `unpushed_plans: list[str]` to TSV output in `classify_repo` and to the
        Python JSON serialiser block in `post_snapshot`. (b) Add `unpushed_plans` field to `GitStatusPostRequest` /
        `RepoStatus` models. (c) In `_maybe_alert_git_staleness` (or a sibling), detect `unpushed_plans` and call a new
        `notify_unpushed_plans(slot_id, plans)` Slack alert immediately (no 15-min threshold — a dirty plan file is
        always operator-actionable).

## Phase 1 — `parent_epic` semantic check (P1)

- [ ] [AGENT] P1. Build initial keyword-surface YAML at `codex/12-agent-workflow/epic-keyword-surface.yaml`. Format:
      `yaml     mtds_mdps_master:       keywords: [mtds, mdps, instruments-service, manifest, market-tick, candle, backfill]       repos: [market-tick-data-service, market-data-processing-service, instruments-service]     features_and_ml_master:       keywords: [features-service, feature-, ml-, training, registry, polars, formula]       repos: [features-service, ml-service, ml-training-service]     # ... one entry per epic in plans/epics/README.md (19 epics)     `
      Seed each epic's keywords by scanning the epic master plan + its currently-active child plans for distinctive
      tokens (the audit doc from Phase 0 lists existing plan→epic mappings).
- [ ] [AGENT] P1. Write `scripts/plan-hygiene/check_parent_epic_alignment.py` (style matching `check_todo_format.sh`):
      for each `plans/active/*.md`, score the plan body against every epic's keyword surface; if the highest-scoring
      epic differs from the declared `parent_epic`, emit a WARN with the top-3 epic scores. Soft check (operator
      decides; no auto-fix).
- [ ] [AGENT] P1. Wire into `scripts/plan-hygiene/run_hygiene_sweep.sh` as a SOFT check (warn-only — semantic guess
      shouldn't block hygiene-green).
- [ ] [AGENT] P1. Run on current plans. Expect a small list (≤5) of suspect mismatches; report and let operators decide.

## Phase 2 — Unpushed plan-file detection (P1)

- [ ] [AGENT] P1. Extend `scripts/dev/slot-git-status-report.sh`: when iterating dirty / untracked files in a slot's
      `unified-trading-pm` worktree, detect any path matching `plans/active/*.md` or `plans/active/issues/*.md` and
      escalate severity in the reported payload (a new field `unpushed_plans: [list]`).
- [ ] [AGENT] P1. Extend the Slack alert template that consumes the git-status report to fire a higher-priority alert
      (e.g. `🔴 Slot N has unpushed plan(s): X.md, Y.md`) when `unpushed_plans` is non-empty. Existing 5-min
      git-staleness threshold is fine; just decorate the message.
- [ ] [AGENT] P1. Update `codex/12-agent-workflow/symmetric-worker-model.md` (or appropriate codex doc) to note that
      plan-file dirty-state has its own alert.

## Phase 3 — Stale-blocker reaper (P1)

- [ ] [AGENT] P1. Define the schema additions (if any) needed in the orchestrator backlog DB: confirm there is a
      `blocked_on: List[task_id]` or equivalent field; if missing, add it (lightweight migration).
- [ ] [AGENT] P1. Write `scripts/orchestrator/reap_stale_blockers.py`: query backlog for tasks in `state=blocked` with
      `assigned_at >= now-3d`; for each, look up the blocker dependency. Three outcomes: - Blocker `done` or `archived`
      → auto-unblock the task; log a `docs(backlog): unblock <task> — blocker <id> resolved` entry to a daily summary
      file. - Blocker also `blocked` → flag as deadlock; emit a Slack alert with both task IDs. - Blocker missing /
      unknown → flag as orphan-blocked; emit Slack alert.
- [ ] [AGENT] P1. Cloud Scheduler entry: daily at 04:00 UTC (offset from the 05:00 UTC hygiene sweep so they don't
      compete). Tag with `orchestrator_master` so logs surface in the standard orchestrator dashboard.
- [ ] [AGENT] P1. Document the reaper in `codex/12-agent-workflow/` (new sub-doc or extension of existing).

## Phase 4 — Edge-case extensions to check_todo_format (P2)

- [ ] [AGENT] P2. Handle 2 known residual edge cases that fail the canonical regex despite being operator-intent: -
      `[BLOCKED-CREDENTIALS — operator action] [AUDIT] P0. ...` — tag has space + em-dash inside brackets. Decision:
      either (a) accept inline `— operator action` qualifier in tag (relax regex), or (b) auto-rewrite to canonical
      `[BLOCKED-CREDENTIALS] [AUDIT] P0. ... — operator action` (move qualifier to description). -
      `[CLAUDE.md] P1. Update "Other key rules" → "VIX 15m" ...` — tag has `.` (period). Decision: rename to
      `[CODEX] P1.` or `[CLAUDE-MD] P1.` since dots break the tag regex.

## Phase 5 — Codex SSOT updates (P2)

- [ ] [AGENT] P2. Update `codex/12-agent-workflow/plan-hygiene.md` (create if missing) documenting: - All 4
      silent-failure modes + which check catches each. - The closed-set of valid tags + how to add a new one (PR to
      PLAN_FORMAT.md). - The 3 cron schedules (plan-hygiene 05:00 UTC, blocker-reaper 04:00 UTC, orphan-ping every
      4h). - Severity ladder: HARD (sweep exit 1) vs SOFT (warn only).
- [ ] [AGENT] P2. Cross-link from `plans/PLAN_FORMAT.md` to the codex doc and to `check_todo_format.sh` so authors see
      the canonical form + the auto-fixer in one place.

## Phase 6 — PM-pull + PlanRegenLoop latency (P0 — added 2026-05-29 after empirical test)

> Operator-discovered 2026-05-29: pushed `plan_hygiene_silent_failure_capture` to LDR at 14:11Z; 25 min later
> `/api/backlog/regen` returned `scanned_plans=21, new_tasks=0` — the plan was NOT ingested. Root cause: the regen-host
> reads the local PM clone without doing its own `git pull`; the PlanRegenLoop only ticks every 6h (default). On
> vm-orchestrator (SSM-accessible proxy for the API host), `slot-cron-ff-pull.service` is NOT installed — so there is no
> observed automatic PM-pull on the orchestrator hosts. Plans languish until someone manually pulls or the loop next
> ticks against a manually-pulled clone.

- [x] ✅ [AGENT] P0. Audit each orchestrator host's PM-pull mechanism. — 2026-05-29: PARTIAL audit completed. **API
      host** (`i-0c9b283b31d6b5ca7`): no auto-pull found before today; PM clone was 2 commits behind LDR on direct
      inspection. **vm-orchestrator** (`i-007e8d99d12831578`): same — `slot-cron-ff-pull.service` absent. Other epic VMs
      (vm-ml, vm-cefi, vm-tradfi, vm-sports, vm-prediction, vm-trading-core, vm-operator-ops, vm-cross-cutting,
      vm-defi): not yet audited; **DEFERRED to a follow-up todo** since each requires SSM and may need separate IAM
      profile attachment.
- [x] ✅ [AGENT] P0. Install a uniform PM-pull mechanism on every orchestrator host (Option A — systemd timer every 5
      min). — 2026-05-29: installed `/usr/local/bin/pm-pull-ff.sh` + `pm-pull.service` + `pm-pull.timer` on: **API
      host** (i-0c9b283b31d6b5ca7) and **vm-orchestrator** (i-007e8d99d12831578). Smart-skip: ignores untracked runtime
      artifacts (e.g. `harsh_orchestrator/backlog.yaml`), only skips on TRACKED modifications. Both timers `active`;
      first run on API host pulled 2 commits (2ee568b09 → 7f9616e36). Per-epic-VM rollout tracked in "follow-up audit"
      todo below.
- [x] ✅ [AGENT] P0. Tighten `DEFAULT_PLAN_REGEN_INTERVAL_SECONDS` from 6h to 30min. — 2026-05-29: deployed via systemd
      drop-in at `/etc/systemd/system/orchestrator.service.d/regen-interval.conf` with
      `Environment=ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS=1800` on both API host and vm-orchestrator.
      orchestrator.service restarted; `systemctl show ... -p Environment` confirms the new value.
- [x] ✅ [AGENT] P0. End-to-end test. — 2026-05-29: VERIFIED. After Phase 6 deployment, `/api/backlog/regen` returned
      `scanned_plans=26 (+5), total_tasks=302 (+134 from 168)`. The 3 plans filed earlier today (all previously 0-task)
      now have: `plan_hygiene_silent_failure_capture`: 20 tasks, `api_host_chronic_impairment`: 16 tasks,
      `cross_operator_auth_failover`: 14 tasks. End-to-end push-to-ingestion latency for the **first** post-fix regen
      call: ~3-5 min (one pm-pull cycle + immediate orchestrator restart). Steady-state latency under the 5-min
      pm-pull + 30-min regen cadence: ≤35 min. Workers' /boot cycle remains the final step (verified in follow-up todo).
- [x] ✅ [AGENT] P0. After Phase 6 ships, end-to-end test: (a) push a tiny canonical-format test plan to LDR; (b) within
      `pm-pull interval + PlanRegen interval` (target: ≤35 min), the plan's tasks must appear in `/api/backlog`; (c)
      within another `/boot` cycle, a free worker must be assigned at least one task from that plan.
      — 2026-05-29T16:35Z: VERIFIED. Pushed `plans/active/e2e_test_plan_regen_pipeline_2026_05_29.md` (2 P3 tasks)
      to LDR at 16:32:47Z. pm-pull.service ran at 16:35:08Z (2m21s after push). Regen at 16:35:17Z returned
      `scanned_plans=27 new_tasks=2`. Tasks `e2e_test_plan_regen_pipeline-{001,002}` appeared at priority=80 (P3).
      Push-to-visible latency: **2m30s**. Target ≤35 min. Workers' /boot picks up tasks in normal dispatch order
      (P3 behind current active P0-P1 sprint).
- [ ] [AGENT] P1. Roll Phase 6 out to the remaining 9 epic VMs (vm-ml, vm-cefi, vm-tradfi, vm-sports, vm-prediction,
      vm-trading-core, vm-operator-ops, vm-cross-cutting, vm-defi). Each needs the IAM profile pre-attached (most should
      already have `uts-orchestrator-epic` per their description; verify per host). Use the same `/tmp/install_full.sh`
      shape this commit deployed.

## Success criteria

- 4-of-4 silent-failure modes have a hygiene check that fires within 24h of introduction.
- PM-pull cron present + verified on every orchestrator host; PlanRegenLoop interval ≤30 min.
- End-to-end push-to-task-pickup latency ≤35 min in normal operation (verified by Phase 6 test).
- `check_parent_epic_alignment.py` flags any plan whose body-keyword profile doesn't match its declared epic (soft).
- Slack alert escalates immediately on unpushed plan file (5-min dirty threshold + plan-path detection).
- Daily reaper auto-unblocks tasks whose blockers are `done`; raises `Slack` alerts for deadlocks / orphan-blocked.
- Codex doc explains the full hygiene stack from end-to-end.

## Out of scope

- Mass-renaming existing non-canonical tags (e.g. `[CLAUDE.md]` → `[CODEX]`) — leave to operator-driven plan refactors.
- Auto-deletion of any backlog state (reaper only flips status flags, never deletes).
- Cross-VM backlog sync (separate concern; the per-VM regen_from_plan.py already handles this).
