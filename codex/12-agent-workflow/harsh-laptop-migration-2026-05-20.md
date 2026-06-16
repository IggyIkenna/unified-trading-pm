---
scope: [engineer, admin]
title: Harsh laptop migration — from epiphanytechnologies.com to shared agent-orchestrator
created: 2026-05-20
owner: ikenna
audience: harsh
status: active
related:
  - codex/04-architecture/agent-orchestrator-overview.md
  - codex/05-infrastructure/per-tab-worktrees.md
  - codex/12-agent-workflow/README.md
  - agent-orchestrator/agents/main.md
  - agent-orchestrator/agents/worker.md
---

# Harsh laptop migration — to shared agent-orchestrator

> Goal: retire `orch.epiphanytechnologies.com` (Harsh's standalone orchestrator backend on his laptop) and consolidate
> onto the shared agent-orchestrator backend running on the Ikenna AWS VM at
> `https://api.agent-orchestrator.odum-research.com` (API) + `https://agent-orchestrator.odum-research.com/` (dashboard
> SPA).
>
> Harsh's laptop becomes a **worker host** that runs slot worktrees + crons + Claude Code sessions, but does NOT run its
> own FastAPI backend. All state lives centrally on the VM. One source of truth in the dashboard.

This doc is the canonical migration checklist for Harsh. Ikenna keeps it current as the shared setup evolves (see
"Change log" at the bottom).

> **⚠️ WORKTREE-MODEL UPDATE (2026-06-08) — Path-B reference-clones, tab-branch model RETIRED.** The slot-isolation
> mechanism in **Step 3 (`setup-tab-worktrees.sh --add-slot … --operator harsh` → `tab/harsh/<N>` worktrees)** and the
> per-worktree re-stamp in **Step 4.5** are SUPERSEDED. Each slot is now a **separate
> `git clone --reference … <url> .tabs/<N>/<repo>`** with its own `.git`, **independently checked out on
> `live-defi-rollout`** — no `tab/<op>/N` branch, no tab→LDR mirror, no diverged-tab class. Identity is per-clone
> `git config user.name "harshkantariya [slot-<N>·laptop]"` (plain, not `--worktree`). Stay current via
> `git pull --ff-only origin live-defi-rollout`; **ship ONLY via `quickmerge --agent --files`** (strict-quickmerge HARD
> RULE 2026-06-08 — direct code pushes to LDR are banned). Canonical SSOT: `cursor-configs/CLAUDE.md` § "Per-slot
> worktrees — Path-B reference-clones on LDR" + § "Strict quickmerge" + `codex/05-infrastructure/per-tab-worktrees.md`.
> **Email migration is DONE** — Harsh commits as `harshkantariya <harshkantariya@odum-research.com>` (see Change log
> 2026-06-08). The shared-backend / slot-range / token / cron steps below remain valid.

---

## Target architecture (after migration)

```
┌────────────────────────────────────────────────────────────────────┐
│   Shared backend (AWS VM, asia-northeast1-c equivalent on EC2)     │
│   - uvicorn FastAPI                  → https://api.agent-orch...   │
│   - SQLite state (orchestrator.db)                                 │
│   - WorkerLivenessKicker (tmux-kick every 45s)                     │
│   - TmuxPruner, ApiKeyReloader, …                                  │
│   - Dashboard SPA served from same uvicorn (Vite-built dist/)      │
│   - Cron: slot-cron-ff-pull (every 5 min)                          │
│   - Cron: slot-git-status-report (every 5 min @ :2,7,12,…)         │
│   - Slots running on VM:    9, 10, 11, 12  (Cluster A/B/C + spare) │
└────────────────────────────────────────────────────────────────────┘
                            ▲
                            │ HTTPS + JWT
                            │
┌───────────────────────────┴────────────────────────────────────────┐
│  Operator laptops (each is just a worker host, no backend)         │
│                                                                    │
│  Ikenna mac:                       Harsh laptop (Linux):           │
│  - .tabs/1..8 worktrees            - .tabs/13..20 worktrees        │
│  - Cron: slot-cron-ff-pull         - Cron: slot-cron-ff-pull       │
│  - Cron: slot-git-status-report    - Cron: slot-git-status-report  │
│    (slots 1-8)                       (slots 13-20)                 │
│  - Cursor/Claude Code interactive  - Cursor/Claude Code interactive│
│    sessions per slot                 sessions per slot             │
└────────────────────────────────────────────────────────────────────┘
```

**Slot range**: Harsh's slots are **13-20** by default (Ikenna owns 1-12 across local mac + AWS VM). This is
operator-tunable — if you need a different range, ping `ikenna@odum-research.com` before bootstrapping so the auth +
workspace assumptions match.

**No `orch.epiphanytechnologies.com` anymore.** That backend is decommissioned once the migration is verified (see "Step
8 — decommission").

---

## Pre-migration audit

Before changing anything, snapshot what's on Harsh's laptop today:

```bash
# What backend is Harsh's existing orchestrator running?
ssh harsh-laptop 'systemctl --user status orch* 2>&1 | head -10 || true; \
                  ps -ef | grep -iE "uvicorn|orchestrator|epiphany" | grep -v grep'

# What worktrees exist?
ls -d ${WORKSPACE_PATH}/.tabs/*/  2>/dev/null

# Active Claude sessions?
tmux ls 2>&1 | grep -iE "orch|slot|harsh"

# Pending work on Harsh's side (per the old file-based ledger format)?
cat ${WORKSPACE_PATH}/unified-trading-pm/harsh_orchestrator/LEDGER.md \
  | grep -E "🟢 IN FLIGHT|🟡 BLOCKED|🟡 IN-FLIGHT" || true
```

Save the output to a file (`/tmp/harsh-pre-migration-audit.txt`) — useful for verifying Step 7 below ("no work lost").

---

## Step 1 — read the canonical references

Read these BEFORE any commands. They are the source of truth that the migration commands wrap:

1. `unified-trading-pm/cursor-configs/CLAUDE.md` — workspace-wide HARD RULES (Quality Gates Are A Merge Prerequisite,
   Data Pipeline Correctness Is The Heartbeat, Every Active Ping Must Reference A Plan Item, etc.)
2. `unified-trading-pm/codex/04-architecture/agent-orchestrator-overview.md` — what the orchestrator is, its API
   surface, model tiers.
3. `unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md` — the 3-tier (operator → slot → sub-agent)
   isolation model + the `setup-tab-worktrees.sh` bootstrap.
4. `agent-orchestrator/agents/RULES.md` — slim shared rules for every agent (worker / main / review). Read first per its
   STEP 0 directive.
5. `agent-orchestrator/agents/worker.md` — what Harsh's per-slot Claude sessions should run as.
6. `agent-orchestrator/agents/main.md` — if Harsh wants to also run a "main" agent (orchestration assistant chat), this
   is the prompt.

---

## Step 2 — update workspace clones to current `main` / `live-defi-rollout`

Harsh's laptop already has `${WORKSPACE_PATH}/unified-trading-system-repos/`. Bring every clone to current state:

```bash
WORKSPACE_PATH="${HOME}/Code/unified-trading-system-repos"   # adjust as needed
cd "${WORKSPACE_PATH}"

# Per-repo branch convention (2026-05-20 reversal — everything on LDR):
#   - ALL repos including agent-orchestrator → branch `live-defi-rollout`
#   - main is the production-promotion branch only; LDR is the integration branch
#     (see codex/08-workflows/deployment-flow.md for the LDR → staging → main path)

# Update agent-orchestrator (now on LDR like everything else)
cd "${WORKSPACE_PATH}/agent-orchestrator"
git fetch origin live-defi-rollout
git checkout live-defi-rollout
git pull --ff-only origin live-defi-rollout

# Update unified-trading-pm next (workspace SSOT)
cd "${WORKSPACE_PATH}/unified-trading-pm"
git fetch origin live-defi-rollout
git checkout live-defi-rollout
git pull --ff-only origin live-defi-rollout

# Verify the migration doc lives where this README says it does
ls -la codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md
```

If any repo refuses to FF-pull (diverged because Harsh has uncommitted local edits): stash by file name (NOT
`git stash -u` blindly), pull, pop. See `per-tab-worktrees.md § "Step 7 — troubleshooting"` for the autostash-conflict
recovery recipe.

---

## Step 3 — bootstrap Harsh's slot range

Provision slot worktrees `13` through `20` (8 slots default — same count as Ikenna's local). Each `.tabs/<N>/` will
contain a per-repo worktree on branch `tab/harsh/<N>`.

```bash
cd "${WORKSPACE_PATH}"
# --start-slot is NOT supported by setup-tab-worktrees.sh (verified 2026-05-21).
# Use --add-slot in a loop:
for N in 13 14 15 16 17 18 19 20; do
    bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --add-slot $N --operator harsh
done
```

After bootstrap, verify:

```bash
ls -d "${WORKSPACE_PATH}/.tabs/"*/  # should show 13/, 14/, ..., 20/
ls -d "${WORKSPACE_PATH}/.tabs/13/"*/ | wc -l   # ~27 repos (each is a git worktree)
```

---

## Step 4 — get a JWT for the shared backend

Harsh logs in once to mint an auth token. The token persists at `${HOME}/.orch_token` (mode 600) and is used by the
reporter cron + any direct API calls.

```bash
# Replace <password> with operator-shared password (ask Ikenna out-of-band)
LOGIN_RESP=$(curl -sS -X POST https://api.agent-orchestrator.odum-research.com/api/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"username":"harsh","password":"<password>"}')
echo "$LOGIN_RESP" | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])" > "${HOME}/.orch_token"
chmod 600 "${HOME}/.orch_token"

# Sanity check — should print mode info, not 401
TOKEN=$(cat "${HOME}/.orch_token")
curl -sS https://api.agent-orchestrator.odum-research.com/api/mode \
    -H "Authorization: Bearer $TOKEN"
```

Per-slot worker tokens (used by the worker's `/boot` + `/heartbeat`) have been pre-issued by slot 11 on the VM
(2026-05-21, exp 2026-06-20) and staged at `/home/ubuntu/unified-trading-system-repos/.tabs/harsh-slot-tokens/` on the
shared VM. Copy them to your laptop after Step 3:

```bash
WORKSPACE_PATH="${HOME}/Code/unified-trading-system-repos"   # adjust as needed
VM="ubuntu@<vm-ip>"   # ask Ikenna for the IP or use the SSH alias

for N in 13 14 15 16 17 18 19 20; do
    mkdir -p "${WORKSPACE_PATH}/.tabs/${N}"
    scp "${VM}:/home/ubuntu/unified-trading-system-repos/.tabs/harsh-slot-tokens/slot-${N}.orch_token" \
        "${WORKSPACE_PATH}/.tabs/${N}/.orch_token"
    chmod 600 "${WORKSPACE_PATH}/.tabs/${N}/.orch_token"
done
```

If tokens have expired (30-day TTL): ping Ikenna to re-issue (runs the same `issue_token('harsh', ...)` script on the
VM).

---

## Step 4.5 — declare this laptop's commit identity (per-operator; codified 2026-06-05)

Harsh's laptop commits as **his own** GitHub account (`harshkantariya <harshkantariya@odum-research.com>`), not
Ikenna's. The identity scripts (`fix-commit-identity.sh` hook · `setup-tab-worktrees.sh` ·
`verify-slot-host-symmetry.sh`) read a per-machine declaration; without it they fall back to the Ikenna fleet default
and `verify` step 9 fails (or the hook rewrites his commits to Ikenna). Declare it ONCE per machine, then re-stamp the
already-provisioned worktrees:

```bash
WORKSPACE_PATH="${HOME}/Code/unified-trading-system-repos"   # adjust as needed

# 1. per-machine declaration (read by every git invocation, incl. the per-repo pre-commit hook)
git config --global slotIdentity.email "harshkantariya@odum-research.com"
git config --global slotIdentity.name  "harshkantariya"

# 2. re-stamp every existing slot worktree's per-worktree identity (his slots are tab/hk/<N>, host=laptop)
cd "${WORKSPACE_PATH}"
for d in .tabs/[0-9]*/*/; do
  [ -e "$d/.git" ] || continue
  slot="$(basename "$(dirname "$d")")"
  git -C "$d" config extensions.worktreeConfig true
  git -C "$d" config --worktree user.name  "harshkantariya [slot-${slot}·laptop]"
  git -C "$d" config --worktree user.email "harshkantariya@odum-research.com"
done
```

(Future `setup-tab-worktrees.sh --init/--add-slot/--reset-slot` runs now read the same declaration and provision the
correct identity automatically — the re-stamp loop above is only needed for worktrees provisioned before this fix.)
SSOT: `codex/05-infrastructure/per-tab-worktrees.md` § "Commit attribution".

---

## Step 5 — install the two crons (every 5 min, offset by 2 min)

```bash
WORKSPACE_PATH="${HOME}/Code/unified-trading-system-repos"   # adjust as needed

# Cron line 1 — fast-forward pull (origin/<branch> → local)
( crontab -l 2>/dev/null | grep -v "slot-cron-ff-pull";
  echo "*/5 * * * * cd ${WORKSPACE_PATH}/.tabs/13 && bash ${WORKSPACE_PATH}/unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh --all-slots --quiet --workers 4 >> /tmp/slot-cron-ff-pull.log 2>&1 # slot-cron-ff-pull"
) | crontab -

# Cron line 2 — git-status drift reporter (offset by 2 min to avoid collision)
( crontab -l 2>/dev/null | grep -v "slot-git-status-report";
  echo "2,7,12,17,22,27,32,37,42,47,52,57 * * * * cd ${WORKSPACE_PATH}/.tabs/13 && bash ${WORKSPACE_PATH}/unified-trading-pm/scripts/dev/slot-git-status-report.sh --quiet --slots 13,14,15,16,17,18,19,20 >> /tmp/slot-git-status-report.log 2>&1 # slot-git-status-report"
) | crontab -

# Verify
crontab -l | grep -E "slot-cron-ff-pull|slot-git-status-report"
```

After the first 5-min boundary, check both logs:

```bash
tail -20 /tmp/slot-cron-ff-pull.log
tail -20 /tmp/slot-git-status-report.log
```

Both should show per-slot per-repo activity. The dashboard's slot cards should now show GitStatusBadge for slots 13-20
(green/yellow/red dots).

---

## Step 6 — spawn Claude Code sessions per slot

Two patterns, pick by how Harsh prefers to work:

### Pattern A — dashboard-driven spawn (operator clicks "+ Spawn worker")

From the dashboard at `https://agent-orchestrator.odum-research.com/` go to **Fleet** → click "+ Spawn worker" on each
slot tile. The orchestrator backend on the VM does NOT spawn workers on Harsh's laptop directly — this pattern only
works when slots run ON the VM (slots 9-12). For Harsh's laptop slots (13-20), use Pattern B.

### Pattern B — local tmux-spawn from Harsh's laptop

Each slot gets its own tmux session running `claude --dangerously-skip-permissions`. Use
`unified-trading-pm/scripts/dev/spawn-local-slot.sh` (or the equivalent manual recipe):

```bash
for N in 13 14 15 16 17 18 19 20; do
    bash "${WORKSPACE_PATH}/unified-trading-pm/scripts/dev/spawn-local-slot.sh" \
        --slot $N \
        --operator harsh \
        --model claude-sonnet-4-6 \
        --effort high
done
```

Once spawned, each session needs the worker boot prompt pasted in. The canonical template is
`agent-orchestrator/agents/worker.md`. For Harsh, the per-slot prompt is:

```
You are slot <N> (find your slot number from PWD: .tabs/<N>/).
Boot via your worktree's .boot.md + register via /api/slots/<N>/boot.
Read agents/worker.md end-to-end before any work.
Server: https://api.agent-orchestrator.odum-research.com
Token: cat .orch_token  (per-slot JWT issued by Ikenna)
Model: Sonnet 4.6 high
```

(Pattern C — Cursor IDE instances — also works for Harsh if he prefers IDE chat over headless tmux. The `.tabs/<N>/` is
the workspace root; Cursor opens .tabs/13, then claude-code-chat boots the worker. The reporter cron does NOT depend on
tmux either way.)

### Local laptop vs fleet VM auth (post Phase 4b-cleanup 2026-05-28)

The fleet VMs and Harsh's laptop authenticate `claude` **differently**:

- **Fleet VMs** spawn workers via `tmux_spawn.spawn(env_file=…)` which sources a per-account setup-token env file
  (`~/.claude-accounts/<account_id>.env`) before `exec claude`. The legacy `~/.claude/.credentials.json` swap path was
  removed in Phase 4b-cleanup; spawns hard-fail if the account has no `oauth_token_env_file` in `accounts.json`. SSOT:
  [`./claude-cli-multi-account-headless-auth.md`](claude-cli-multi-account-headless-auth.md).

- **Harsh's laptop** is a single-operator host. Pattern B / Pattern C above launch `claude` directly without sourcing an
  env file, so `claude` reads `~/.claude/.credentials.json` from a normal interactive `claude /login` Harsh ran once on
  the laptop. There's no setup-token requirement for the laptop because there's no per-account isolation to enforce —
  Harsh's laptop = Harsh's personal claude subscription.

If Harsh ever needs to swap which subscription his local sessions consume (e.g. drain his Max quota during a
particularly heavy day and switch to a different account), the procedure is `claude /logout` then `claude /login`
interactively with the target account — NOT setup-tokens. Setup tokens are a fleet-VM concept.

---

## Step 7 — verify "no work lost" from epiphany backend

Cross-reference the pre-migration audit (Step 0):

1. **In-flight tasks from Harsh's old LEDGER.md**:
   - For each `🟢 IN FLIGHT` row in `unified-trading-pm/harsh_orchestrator/LEDGER.md` at audit time, check whether the
     work shipped:
     - YES (commit on `live-defi-rollout` for the repo named in the row) → mark row `✅ done` in the LEDGER with the
       SHA.
     - NO → add as a fresh backlog entry in the orchestrator backend (see `agents/main.md § Backlog YAML entry`).

2. **Pending pings from `harsh_orchestrator/_agent_pings.md`**:
   - Per the workspace `Every Active Ping Must Reference A Plan Item` HARD RULE, every active ping should already
     reference a plan-of-record. The ones that don't will be flagged by the 4-hour orphan-ping cron (which runs on
     Ikenna's local + the VM — Harsh doesn't need to install it).
   - Confirm Harsh's recent pings are still in the file (i.e. nothing was lost during the laptop's epiphany backend
     shutdown).

3. **Slot rows in shared backend**:
   ```bash
   TOKEN=$(cat "${HOME}/.orch_token")
   curl -sS "https://api.agent-orchestrator.odum-research.com/api/state" \
       -H "Authorization: Bearer $TOKEN" \
     | python3 -c "import json,sys; d=json.load(sys.stdin); [print(s['slot_id'],s['status'],s.get('current_task')) for s in d['slots'] if s['slot_id']>=13]"
   ```
   Expect 8 rows for slots 13-20, each either `idle` (no current task) or `working` (after Step 6 boot completes).

---

## Step 8 — decommission `orch.epiphanytechnologies.com`

Only after Step 7 verifies no work lost:

```bash
# On Harsh's laptop — stop the old backend
systemctl --user stop orch-epiphany 2>&1 || true
systemctl --user disable orch-epiphany 2>&1 || true

# Optional: archive the old config so future-Harsh can reference what was there
mv ~/.config/orch-epiphany ~/.config/orch-epiphany.ARCHIVED-2026-05-20

# DNS — remove the A/CNAME for orch.epiphanytechnologies.com (Ikenna will action
# from Cloudflare side once Harsh confirms ready)
```

After DNS removal, ping Ikenna to verify no stale clients are still hitting the old URL (look at the VM's nginx access
logs for traffic patterns).

---

## Operating norms (read once, then it's just work)

- **Branch per repo**: every workspace repo (including agent-orchestrator as of 2026-05-20 reversal) integrates on
  `live-defi-rollout`. Main is reserved for production promotion only (LDR → staging → main per
  `codex/08-workflows/deployment-flow.md`). `cron-branch-overrides.txt` is empty — no per-repo deviations.
- **Commit + push + flip plan checkbox in same agent turn**: the workspace has a HARD RULE on this (see CLAUDE.md §
  "Commit + Push + Flip Plan Checkboxes As You Ship Each Item"). Backfill-flipping later is reviewer- rejected.
- **Quality gates are a merge prerequisite**: `bash scripts/quality-gates.sh` exit 0 before any push. No exceptions
  without `BLOCKED-OPERATOR-DECISION`.
- **Foreign-files rule**: never `git checkout HEAD -- <conflicted_file>` on a file you don't own. Stash by name; if
  rebase autostash conflicts, abort and recover via dangling-commit reflog. Full incident recipe in
  per-tab-worktrees.md.
- **Sub-agents start fresh**: paste `SUB_AGENT_MANDATORY_RULES.md` at the top of every Task spawn. The PM repo has an
  inject helper.

---

## Sanity check (5-minute smoke after migration)

```bash
# 1. Token works
TOKEN=$(cat "${HOME}/.orch_token")
curl -sS https://api.agent-orchestrator.odum-research.com/api/mode -H "Authorization: Bearer $TOKEN"
# Expect: {"mode":"live", ...}

# 2. Crons installed
crontab -l | grep -cE "slot-cron-ff-pull|slot-git-status-report"
# Expect: 2

# 3. Worktrees present
ls -d "${WORKSPACE_PATH}/.tabs/"{13,14,15,16,17,18,19,20}/  2>&1
# Expect: 8 directory paths

# 4. Reporter has posted at least once
ssh agent-orchestrator-vm "TOKEN=\$(cat /home/ubuntu/unified-trading-system-repos/.tabs/9/.orch_token); \
    curl -sS http://127.0.0.1:8765/api/slots/13/git-status -H \"Authorization: Bearer \$TOKEN\" | head -c 300"
# Expect: JSON with host=<harsh-laptop-hostname>, repos array

# 5. Dashboard shows Harsh's slots
# Open https://agent-orchestrator.odum-research.com/ → Fleet tab
# Expect: slots 13-20 with GitStatusBadge (mostly green right after init)
```

---

## When something goes wrong

- **Reporter logs `[skip:no-token]` for every slot** — Ikenna hasn't issued per-slot tokens yet (Step 4 only mints the
  operator-level token; per-slot tokens are server-side). Ping Ikenna.
- **Reporter logs `HTTP 404 — slot N not found`** — backend doesn't have a row for slot N yet. Boot a worker into that
  slot (Step 6) — the row appears on first `/boot` call.
- **FF-pull cron logs `[skip:dirty]` for every repo** — that's normal during active work; the FF puller refuses to touch
  dirty trees. Once Harsh commits + pushes, the next cron tick will FF cleanly.
- **Dashboard shows red GitStatusBadge that won't go away** — either the reporter cron is broken (check
  `/tmp/slot-git-status-report.log`), or the repo is genuinely stuck (dirty >60 min OR clean+behind >10 min — both
  indicate operator should intervene).

---

## Change log

| Date       | Change                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 2026-05-20 | Initial doc — covers shared-backend migration, slot range 13-20, FF-pull + git-status-report crons                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 2026-05-21 | Step 3: drop `--start-slot` (not implemented — use `--add-slot` loop). Step 4: per-slot tokens pre-issued on VM at `.tabs/harsh-slot-tokens/`, exp 2026-06-20; added `scp` copy recipe.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| 2026-05-28 | Step 6: added "Local laptop vs fleet VM auth" subsection — clarifies that setup-tokens are a fleet concept, Harsh's laptop continues using `~/.claude/.credentials.json` from interactive `claude /login`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 2026-06-08 | **Operator git email → company `harshkantariya@odum-research.com`** (added as a 3rd verified email on the SAME CosmicTrader GitHub account — SSH key + collaborator access unchanged, no auth break). `slotIdentity.email` flipped + every UTS slot worktree (per-worktree) and root clone (repo-level) re-stamped; **global `user.email` deliberately kept personal** so non-UTS/personal repos are untouched. gcloud config + ADC and AWS already on the company identity; the dead personal-gmail gcloud credential was revoked. Intentional gmail refs left in place: personal-repo global config + the `DEMOTED_INTERNAL_EMAIL_HINTS` login-redirect / `STRIP_LIST` admin-audit in `unified-trading-system-ui`. Attribution docs + 3 identity-script comments updated → PM@971b8f882. Same session also brought slot-host symmetry to verifier-green (slot-prefix fix `tab/hkm`→`tab/hk`, FF-pull `--quiet` heartbeat, self-pull exec-bit `chmod` fix) and shipped a cross-platform reflog-reset guard (launchd/macOS + systemd-user `inotifywait`/Linux, wired into `bootstrap_vm.sh`) → PM@c8b0029be, AO@9b5fa2b. |

Future updates land here as the shared setup evolves (e.g. new cron, new agent.md spec, new dashboard panel that
requires opt-in).

---

## Related plans

- `plans/active/per_agent_worktrees_2026_05_10.md` — 3-tier worktree model
- `plans/active/agent_reliability_mitigations_2026_05_20.md` — Phase 1-4 features that the shared backend now ships
  (pre-spawn dirty gate, in_flight_files heartbeat, .agent-claim ownership, GHA webhook).
