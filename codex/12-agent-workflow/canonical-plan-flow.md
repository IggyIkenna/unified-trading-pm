---
scope: [engineer, admin]
---

# Canonical plan flow — audit → issue → plan → backlog → worker → ship

> SSOT for how plans authored by operators get autonomously picked up and shipped by orchestrator-managed workers.
> Companion to [PLAN_FORMAT.md](../../plans/PLAN_FORMAT.md) (todo schema) and
> [CLAUDE.md](../../cursor-configs/CLAUDE.md) (workspace rules).
>
> Codified 2026-05-29 after operator-driven audit revealed (a) regen ingestion latency gap and (b) the 4 silent-failure
> modes — both now tracked in `plans/active/plan_hygiene_silent_failure_capture_2026_05_29.md`.

## TL;DR — the closed loop

```
[1] Audit finds something            (audit-instructions docs in codex/10-audit/)
       ↓
[2] Issue filed in plans/active/issues/   (the WHAT and WHY)
       ↓
[3] Decision → Plan in plans/active/      (the HOW — phased, canonical-format todos)
       ↓
[4] git push origin live-defi-rollout     (the operator/worker pushes)
       ↓
[5] PM-pull cron on orchestrator host     (≤5 min — see "Gap & target" below)
       ↓
[6] PlanRegenLoop tick                    (every 6h today, target ≤30 min)
       ↓
[7] regen_backlog_from_plan.py parses → inserts new task_ids into backlog DB
       ↓
[8] Worker's next POST /api/slots/<N>/boot returns the next eligible task
       ↓
[9] Worker FF-pulls repos, works, commits + pushes per shippable unit
       ↓
[10] Worker POSTs /api/slots/<N>/done → flip plan checkbox → /boot next
```

Each numbered step is described below with its current implementation, known gaps, and where the gap is tracked.

---

## [1] Audits

- Tooling: `plans/audit/instructions/<slug>.md` — operator-authored audit instructions per epic / per surface.
- Output: findings filed as an issue in step [2].
- See also: `plans/audit/results/` for completed audit reports.

## [2] Issues — `plans/active/issues/`

- Filename convention: `<slug>_<YYYY_MM_DD>.md` (date-suffixed).
- Frontmatter (minimal): `title`, `created`, `author`, `source` (list of evidence), `locked_by`.
- Body sections (canonical, per Findings Triage HARD RULE):
  - `## What I found` — the empirical evidence.
  - `## Why it matters` — impact + downstream consequences.
  - `## Recommended decision` — proposed solution / the _what_ of the plan that will follow.
  - `## Scope` — link to the plan file in `plans/active/` once the plan exists.
  - `## Unblocks` — what flips green when the plan ships.
- Status: an issue exists to surface UNACKED work. Once acked into a plan, the issue is archived **immediately** (per
  Issue-Doc Lifecycle Discipline in CLAUDE.md).

## [3] Plans — `plans/active/`

Canonical frontmatter (REQUIRED):

```yaml
---
name: <slug>
title: <human-readable title>
parent_epic: <epic-slug> # REQUIRED — routes to the right VM via orchestrator_vm_registry.yaml
assigned_vm: vm-<id> # REQUIRED — explicit VM assignment; QG STEP 5.x enforces
priority: P0 | P1 | P2 | P3
status: active
estimate_class: refactor | design | infra | brand-new | research
estimate_baseline_ai_days: <N>
estimate_calibrated_ai_days: <N>
locked_by: live-defi-rollout
locked_since: YYYY-MM-DD
related:
  - issues/<companion-issue>.md
---
```

Canonical todos (REQUIRED — see also [PLAN_FORMAT.md § Canonical form + automated hygiene](../../plans/PLAN_FORMAT.md)):

```
- [ ] [TAG] P<0-3>. <description>
- [ ] [TAG] P<0-3>.<sub-id>. <description>     # sub-priority allowed
- [ ] [TAG][UI] P<0-3>. <description>          # multi-tag legal per UI HARD RULE
```

Hygiene scripts that catch malformed todos:

- `scripts/plan-hygiene/check_todo_format.sh` — HARD check. Fails sweep if any unchecked todo has no `P<n>` anywhere.
- `scripts/plan-hygiene/fix_todo_format.sh` — mechanical auto-fix for common bracket/priority misplacements.

## [4] Push to `origin/live-defi-rollout`

- Use `bash scripts/quickmerge.sh "msg" --agent` for promotion-to-main flow.
- Per Commit + Push + Flip HARD RULE: every shippable unit gets pushed per-unit + same-turn plan-flip.
- Workers' slot worktrees are on `tab/<operator>/<N>` branches; pushes target LDR directly.

## [5] PM-pull cron on orchestrator host

**Current implementation**: each slot's worktree is FF-pulled by `slot-cron-ff-pull.service` on the slot host (every 5
min). See `codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md`.

**🟡 Gap (2026-05-29)**: the **central orchestrator API host** and several per-VM orchestrator hosts do NOT have
`slot-cron-ff-pull.service` installed at all — confirmed absent on `vm-orchestrator` (`i-007e8d99d12831578`).
Operator-discovered when `plan_hygiene_silent_failure_capture` failed to enter the backlog despite being on LDR. Tracked
in `plans/active/plan_hygiene_silent_failure_capture_2026_05_29.md` § Phase 6 (P0).

**Target**: uniform PM-pull systemd timer (every 5 min) on every orchestrator host — same recipe as slot hosts but
scoped to the orchestrator's local PM clone path (`config.REPO_ROOT.parent / "unified-trading-pm"`).

## [6] PlanRegenLoop

**Current implementation**: `agent-orchestrator/server/regen_backlog_from_plan.py:PlanRegenLoop`. Runs as a daemon
Python thread inside the orchestrator FastAPI process. Default `DEFAULT_PLAN_REGEN_INTERVAL_SECONDS` = **6 hours**.
Override via `ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS` env var. Calls `regen()` on each tick. On-demand trigger
available via `POST /api/backlog/regen` (operator-authed).

**🟡 Gap (2026-05-29)**: 6h is too long for the operator-described "VMs autonomously act on plans immediately" workflow.
Each tick is ~100ms — there's no reason to wait 6h. Tracked in
`plans/active/plan_hygiene_silent_failure_capture_2026_05_29.md` § Phase 6 — target ≤30 min.

## [7] regen — parsing rules (per `regen_backlog_from_plan.py`)

The parser is **liberal**:

- `_UNCHECKED_RE = r"^\s*-\s+\[ \]\s+(.+)$"` — matches any unchecked-checkbox line.
- `_PRIORITY_RE = r"\bP([0-3])\b"` — extracts priority from anywhere in the body. No priority found → `priority=None`.
- `_TITLE_PREFIX_RE = r"^\s*(?:\[[A-Z]+\]\s+)?(?:P[0-3]\.\s*)?"` — strips OPTIONAL `[TAG]` and `P<n>.` prefix to produce
  a clean title.
- Skipped: `index.md`, `_agent_pings.md`, any filename starting with `_`.
- Skipped: `plans/active/issues/*.md` (the regen only scans `plans/active/*.md`).
- Idempotency: `task_id` = `<plan-slug>-<NNN>` (zero-padded to 3 digits, sequential per slug). Content-based dedupe by
  `brief` field.

### 4 silent-failure modes (codified 2026-05-29) and the hygiene checks that catch them

| Mode                                                               | Detection                                                         | Status                                              |
| ------------------------------------------------------------------ | ----------------------------------------------------------------- | --------------------------------------------------- |
| **(1)** Wrong todo format — `- [ ] Do thing` without `[TAG] P<n>.` | `check_todo_format.sh` (HARD) + `fix_todo_format.sh` (mechanical) | ✅ shipped 2026-05-29                               |
| **(2)** Wrong `parent_epic` (right format, semantically wrong)     | `check_parent_epic_alignment.py` (SOFT, planned)                  | 🟡 Phase 1 of `plan_hygiene_silent_failure_capture` |
| **(3)** Plan written but not pushed to LDR                         | Extension to `slot-git-status-report.sh` + Slack escalation       | 🟡 Phase 2 of `plan_hygiene_silent_failure_capture` |
| **(4)** Blocked task lingers indefinitely                          | `reap_stale_blockers.py` cron (daily 04:00 UTC)                   | 🟡 Phase 3 of `plan_hygiene_silent_failure_capture` |

## [8]-[10] Worker lifecycle

`POST /api/slots/<N>/boot` returns the next eligible task per the dispatcher's filters:

- Slot's `worktree` + `branch` (typically `tab/<operator>/<N>`).
- Account health (rate-limited / auth-failed accounts skipped per `_pick_next_account` rotation).
- Plan-level `assigned_vm` matches the slot's VM context.
- Blocker dependencies cleared.

Worker pulls task, FF-pulls repos, works, ships per Commit + Push + Flip discipline, calls `/done`, `/boot`s next.

### Worker-side dirty-plan story (codified 2026-05-29)

- **`slot-cron-ff-pull.sh` explicitly skips dirty worktrees** — design choice to never blow away an agent's uncommitted
  WIP. Cron log shows `[skip:dirty] unified-trading-pm (tab/X/N) — uncommitted changes`.
- **`slot-git-status-report.sh` reports dirty files** to `/api/slots/<N>/git-status` every ~5 min. Orchestrator stores
  this state; dashboard renders it; **Slack fires `🔴 Slot N git staleness — Dirty for: N min`** at the 5-min threshold.
- **Slack alerts do NOT auto-commit.** They're a nudge. The worker (or operator if interactive) must commit + push
  themselves. This is intentional — auto-commit on dirty WIP would conflict with mid-edit state.
- **Consequence**: an agent that sits on uncommitted plan changes for more than ~5 min creates a feedback loop:
  - Slack alerts every reporting interval.
  - The dirty worktree blocks FF-pull → falls behind LDR → conflicts on next attempted push.
  - Other agents working the same plan can't see the dirty agent's WIP until it's committed.
- **Right behaviour** (per Commit + Push + Flip HARD RULE): commit + push per shippable unit, same-turn plan-flip, no
  uncommitted state for more than the duration of a single edit + QG run.

## End-to-end latency budget (target after `plan_hygiene_silent_failure_capture` Phase 6 ships)

- Steps [4]→[5]: push lands; PM-pull cron runs → ≤5 min.
- Steps [5]→[6]: PlanRegenLoop tick → ≤30 min.
- Steps [6]→[7]: regen runs in-process → ~100ms.
- Steps [7]→[8]: worker `/boot` cycle → ≤1 min after current task `/done`.
- **Total push-to-pickup: ≤35 min in normal operation.**

Verified by the Phase 6 end-to-end test once it ships.

## Open issues / where to file new gaps

- All hygiene-loop gaps → extend `plans/active/plan_hygiene_silent_failure_capture_2026_05_29.md`.
- Orchestrator-host stability → `plans/active/api_host_chronic_impairment_2026_05_29.md`.
- Account rotation / auth failover → `plans/active/cross_operator_auth_failover_2026_05_29.md`.

## Cross-references

- [PLAN_FORMAT.md](../../plans/PLAN_FORMAT.md) — todo schema, frontmatter, hygiene scripts.
- [CLAUDE.md](../../cursor-configs/CLAUDE.md) — workspace rules incl. Commit + Push + Flip HARD RULE.
- [agent-orchestrator-overview.md](../04-architecture/agent-orchestrator-overview.md) — orchestrator architecture
  (parent context).
- [local-slot-host-symmetric-worker-model.md](./local-slot-host-symmetric-worker-model.md) — slot-host vs VM-host
  parity.
- [claude-cli-multi-account-headless-auth.md](./claude-cli-multi-account-headless-auth.md) — account / setup-token flow
  that the dispatcher rotation depends on.
