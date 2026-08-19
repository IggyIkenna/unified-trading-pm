---
doc_type: codex-ssot
title: Human Fleet — operator setup runbook (register a laptop into agent-orchestrator)
summary: >-
  Step-by-step runbook for a human operator (Ikenna or Harsh) to register their own laptop as a "human slot" in
  agent-orchestrator — mint a token, register, and install the recurring liveness/usage sync job. Explicitly covers the
  Claude Code CLI vs. Cursor/VS-Code-extension distinction: the commands are identical either way, but the heartbeat
  mechanism you must install differs — `statusLine` never fires inside the Cursor/VS-Code extension chat panel, so the
  correct mechanism (Phase 2b's transcript-polling `ao-liveness-heartbeat.py`, installed via the cron job below) is the
  one that works uniformly across a terminal `claude` session AND an IDE-extension session. All commands are one-time,
  run from a plain shell — nothing here differs by which surface you're reading this doc from.
status: current
nature: ssot
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [human-fleet, onboarding, agent-orchestrator, claude-code, cursor, dashboard]
related:
  [
    /plans/active/ao_human_fleet_integration_2026_08_15.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/05-infrastructure/claude-code-settings-symlink.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: "2026-08-19"
authoritative_for: [human-fleet operator onboarding steps]
referenced_by: []
owner: infra
last_reviewed: "2026-08-19"
code_refs:
  [
    agent-orchestrator/scripts/human_fleet/ao-register.sh,
    agent-orchestrator/scripts/human_fleet/install-fleet-sync-cron.sh,
    agent-orchestrator/scripts/human_fleet/ao-fleet-sync-tick.sh,
    agent-orchestrator/scripts/human_fleet/ao-liveness-heartbeat.py,
    agent-orchestrator/scripts/human_fleet/ao-usage-push.py,
    agent-orchestrator/server/auth.py,
    agent-orchestrator/server/config.py,
  ]
cadence: once per new operator (re-run only if the token expires — 30-day TTL — or a machine is replaced)
verifier: >-
  GET /api/agents?kind=human shows the operator's label with a fresh last_ping; crontab -l | grep 'ao-fleet-sync:<slot>'
  shows the installed entry
last_executed: "2026-08-16 (Ikenna, slot 9001)"
---

# Human Fleet — operator setup runbook

> Design + full rationale: `/plans/active/ao_human_fleet_integration_2026_08_15.md`. Architecture + the two hard
> guarantees (AO can never kill/kick a human slot; a human never competes with AO's own dispatch queue):
> `/codex/04-architecture/agent-orchestrator-worker-liveness.md § Human slots`. This doc is the **operator-facing
> "what do I actually run"** runbook — it doesn't re-derive the design, it points at it.

## Who has a slot

| Operator | Label    | Stable identity slot | Per-tab range (`.tabs/<N>` sessions) |
| -------- | -------- | -------------------- | ------------------------------------ |
| Ikenna   | `ikenna` | 9001                 | 91000–91999                          |
| Harsh    | `harsh`  | 9002                 | 92000–92999                          |

The stable slot is the one identity your task-claims attach to. The per-tab range is separate, automatic visibility —
each concurrently-open `.tabs/<N>` worktree session gets its own row (`<label>-tabN`) once the cron job below is
running, with zero extra setup.

## Prerequisite

Your machine already has the standard workspace bootstrap done (`/codex/05-infrastructure/workspace-setup.md`) and at
least one `.tabs/<N>` worktree with `agent-orchestrator` cloned inside it (`/codex/05-infrastructure/per-tab-worktrees.md`).
If not, do that first — this runbook only covers the human-fleet-specific piece on top.

## Why the CLI-vs-Cursor distinction matters here

Everything below is a plain shell command — run it from a terminal, or from a terminal panel inside Cursor, it makes no
difference. The one place client-shape actually matters is **which heartbeat mechanism reports you as alive**:

- An **earlier** mechanism (`ao-statusline-heartbeat.sh`) hooks Claude Code's `statusLine` feature. Confirmed against
  the official docs: `statusLine` is a **terminal-CLI-only** feature — the Cursor/VS-Code native extension's own chat
  panel never invokes it. A session run there would silently never report a heartbeat through that path.
- The **current** mechanism (`ao-liveness-heartbeat.py`, installed via the cron job below) polls the same local
  transcript file (`~/.claude/projects/<cwd-slug>/<session-id>.jsonl`) every Claude Code surface writes identically —
  terminal CLI, VS Code extension, Cursor extension — so "was this transcript touched recently" is a UI-agnostic
  liveness signal by construction. **This is the one this runbook installs.** Don't set up the standalone statusline
  script instead — it would leave your Cursor sessions invisible.

## Setup

### 1. Mint your token (once; 30-day TTL, renew by re-running this step)

From inside your `agent-orchestrator` checkout, with its venv active:

```bash
cd agent-orchestrator
source .venv/bin/activate
python3 -c "from server.auth import issue_token; t,e = issue_token('harsh', role='worker', machine='harsh-laptop'); print(t); print('expires', e)"
```

Copy the printed token (the long string on the first line).

### 2. Save the token

```bash
mkdir -p ~/.config/agent-orchestrator
nano ~/.config/agent-orchestrator/human-fleet-token   # paste the token, save, exit
chmod 600 ~/.config/agent-orchestrator/human-fleet-token
```

### 3. Register

```bash
AO_SLOT_ID=9002 bash scripts/human_fleet/ao-register.sh harsh
```

Expect `{"ok": true, ...}`. If you get a `401`, the token from step 1 wasn't saved correctly — re-check step 2.

### 4. Install the recurring sync job (liveness heartbeat + usage push, CLI- and Cursor-safe, per-tab-aware)

```bash
AO_HUMAN_LABEL=harsh bash scripts/human_fleet/install-fleet-sync-cron.sh 9002 --minutes 15
```

This installs one crontab entry that, every 15 minutes:

- pushes priced token usage for every recently-active local session (`ao-usage-push.py`, reads your own
  `~/.claude/projects/*.jsonl`, never a client-computed dollar figure — pricing happens server-side),
- sends one liveness heartbeat per currently-active `.tabs/<N>` tab (`ao-liveness-heartbeat.py`) plus a refresh of your
  stable identity slot (9002) from whichever tab was most recently active.

No further action needed — it runs identically whether that tab is a bare terminal `claude` session or a Cursor/VS-Code
extension chat panel.

### 5. (One-time, Cursor only) Make Cursor's Claude Code extension behave like the CLI

Unrelated to human-fleet specifically, but if you use Cursor at all you'll otherwise hit constant permission prompts the
CLI never shows — Cursor's extension resolves its own permission mode and ignores `permissions.defaultMode` in either
`settings.json`. Fix once, in Cursor's own user settings (`~/Library/Application Support/Cursor/User/settings.json` on
macOS):

```json
"claudeCode.allowDangerouslySkipPermissions": true,
"claudeCode.initialPermissionMode": "bypassPermissions"
```

Full detail: `/codex/05-infrastructure/claude-code-settings-symlink.md § Cursor permission-mode`.

## Verify

```bash
crontab -l | grep 'ao-fleet-sync:9002'          # the cron entry is installed
```

Then, from any machine with API access (or ask Ikenna to check):

```
GET /api/agents?kind=human
```

should show `"label":"harsh"`, `"role":"human"`, `"agent_kind":"human"`, with a fresh `last_ping` — and, once you have
more than one `.tabs/<N>` tab open, additional `harsh-tabN` rows alongside it. The dashboard's "Human Fleet" page
(Landing → Human Fleet) shows the same thing visually.

## Optional: run one real task through it

Once registered, you can claim and complete an actual backlog task end-to-end (not required for setup — this just
turns the dormant usage/billing capability into real numbers):

```bash
AO_SLOT_ID=9002 bash scripts/human_fleet/ao-claim.sh <task_id> --check-only   # confirm it's claimable first
AO_SLOT_ID=9002 bash scripts/human_fleet/ao-claim.sh <task_id>                # claim for real
# ... do the work, commit + push + flip the plan checkbox as normal ...
AO_SLOT_ID=9002 bash scripts/human_fleet/ao-done.sh <task_id> <sha> "<evidence>"
```

Note: the claim pre-flight check does **not** re-verify `gate_on_depends`/prerequisite state — it only checks that the
task isn't already dispatched and isn't near the front of AO's own queue. Don't force-claim a task the system itself
still shows as blocked; pick one that's genuinely ready.

## Troubleshooting

| Symptom                                              | Cause                                                                                                                    |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `ao-register.sh` returns 401                         | Token missing/wrong in `~/.config/agent-orchestrator/human-fleet-token` — redo step 1–2.                                 |
| Not appearing in `GET /api/agents?kind=human`        | Cron not installed, or hasn't ticked yet (up to 15 min) — check `crontab -l`.                                            |
| Appear in CLI sessions but not Cursor ones           | You installed the old `ao-statusline-heartbeat.sh` instead of the step-4 cron job.                                       |
| `harsh-tabN` rows not showing for a tab you're using | That tab hasn't had recent transcript activity within the recency window — send a message in it, wait for the next tick. |
