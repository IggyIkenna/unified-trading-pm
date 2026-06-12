---
title: "Per-tab worktrees — 3-tier isolation for parallel-agent flow"
scope: workspace
status: active
last_updated: 2026-05-10
last_reviewed: 2026-05-17
owner: workspace-platform
owner: ikenna
related_plans:
  - plans/archive/per_agent_worktrees_2026_05_10.md
related_codex:
  - codex/05-infrastructure/plan-aware-merge-resolution.md
  - ../../cursor-configs/CLAUDE.md
---

# Per-tab worktrees — 3-tier isolation for parallel-agent flow

> **⚠️ SUPERSEDED 2026-06-08 → Path-B reference-clones (the `tab/<op>/N` tab-branch model is RETIRED).** Each slot is
> now a **`git clone --reference <workspace>/<repo> <url> .tabs/<N>/<repo>`** with its OWN `.git`, checked out directly
> on **`live-defi-rollout`** — separate clones (no ref races), shared object store via `--reference` (no disk blowup).
> This drops the entire tab-branch sync tax: **`tab-mirror-to-ldr.yml` is DISABLED fleet-wide**, the tab-rebase/upstream
> self-heal in `slot-cron-ff-pull.sh` is moot, and the diverged-tab recovery class no longer exists. Stay current with
> `git -C <slot>/<repo> pull --ff-only origin live-defi-rollout`; ship via `quickmerge --agent --files`; the only
> invariant is HEAD ancestor-or-equal of `origin/live-defi-rollout` (`scripts/cicd/slot_drift_check.py`). Commit
> attribution is in the author NAME (`[slot-<N>·<host>]`), independent of branch. Migration (2026-06-08): slots 2-11
> reclined to Path-B; **all prior uncommitted WIP preserved to `origin/wip-preserve/slot-<N>` branches**. SSOT for the
> new model: `plans/active/worktree_ldr_unification_2026_06_08.md`. **Everything below describing `tab/<op>/N` branches,
> tab-mirror, upstream tracking, and diverged-tab recovery is HISTORICAL** — retained for the slot-1 transitional window
>
> - context, not the current model.

**TL;DR (HISTORICAL — tab-branch model).** Each operator (Ikenna / Harsh) runs N parallel agent "tabs." Each tab gets
its own permanent worktree at `.tabs/<N>/<repo>/` on a permanent **role-encoded** branch. Cross-tab races on
`.git/index` + working tree become unrepresentable by construction. Slot is the durable identity; theme (writegate /
cefi-master / defi / etc.) is the daily assignment via the operator's orchestrator LEDGER slot↔theme table.

## Slot-number → role → branch-prefix scheme

The slot number alone decides whether a tab is a **main** agent or a **worker**, and the branch prefix encodes **both
operator and role** so a `git branch` listing is self-describing:

| Slot range                      | Role       | Branch                     | Harsh       | Ikenna (his choice)                |
| ------------------------------- | ---------- | -------------------------- | ----------- | ---------------------------------- |
| `1..MAIN_SLOT_MAX` (default 20) | main agent | `tab/${MAIN_PREFIX}/<N>`   | `tab/hkm/3` | `tab/iim/3`                        |
| `> MAIN_SLOT_MAX`               | worker     | `tab/${WORKER_PREFIX}/<N>` | `tab/hk/21` | `tab/ii/21` _(or `iggy`/`ikenna`)_ |

- **Harsh (operator `hk`)**: `MAIN_PREFIX=hkm`, `WORKER_PREFIX=hk` — these are fixed on Harsh's side.
- **Ikenna** owns his own prefixes: `--operator ii` gives the symmetric `tab/iim/<N>` / `tab/ii/<N>`, or he can
  env-override `MAIN_PREFIX` / `WORKER_PREFIX` (e.g. `iggy`, `ikenna`) — his call.
- No D/F ref collision: `hk` and `hkm` are distinct ref path components.
- `setup-tab-worktrees.sh` derives both prefixes from `--operator` (`<op>` worker, `<op>m` main) unless overridden;
  `MAIN_SLOT_MAX` (default 20) is the main/worker boundary.

## The 3-tier hierarchy

```
Tier 1 — Operator (Ikenna ⊥ Harsh)
    Physical machine boundary. No shared local state.
    Reconciliation: fetch + push via origin/live-defi-rollout. Cross-side
    coordination via workspace-shared plans/active/_agent_pings.md.

Tier 2 — Slot (within one operator)              ←── THIS DOC'S SCOPE
    Per-slot worktree at .tabs/<N>/<repo>/ on a permanent role-encoded
    branch: tab/<main-prefix>/<N> for slots 1..20 (main agents),
    tab/<worker-prefix>/<N> for slots 21+ (workers). See the scheme
    table above. Slot count is operator-declared at --init.
    Slot is durable identity; theme is daily assignment.
    Reconciliation: slot master rebases + pushes per shippable unit; plan-
    aware merge resolution for cross-slot conflicts. See
    plan-aware-merge-resolution.md.

Tier 3 — Sub-agent (within one slot)
    Sub-agents share the slot's worktree. Master agent partitions fan-out
    to non-overlapping repos/dirs so within-slot collisions are rare.
    Master is in-session reconciler when they happen.
```

## Bootstrap

One-time per operator, runs on the operator's workstation:

```bash
# Provision 8 slots for this operator (typical; pick N for peak parallel count).
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --init --slots 8

# Add a 9th slot later if peak grows.
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --add-slot 9

# Between themes on the same slot — verify clean + rebase onto origin/live-defi-rollout.
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot 3

# List configured slots + their current branch heads.
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --list

# Rare: shrink fleet (remove a slot — only when really retiring it).
bash unified-trading-pm/scripts/dev/teardown-tab-worktrees.sh --slot 9
```

After `--init`, every active repo in `workspace-manifest.json` has a worktree at `.tabs/<N>/<repo>/` for each slot. The
operator opens Cursor at `.tabs/<N>/` and the tab is isolated.

## Operator setup recipe (paste-ready)

This section is the operator runbook — paste-ready commands + verification probes for each step. Works identically for
Ikenna and Harsh; the only operator-specific detail is the choice of slot count N (see step 1).

> **Precondition.** Workspace already bootstrapped via
> [`scripts/workspace/workspace-bootstrap.sh`](../../scripts/workspace/workspace-bootstrap.sh) — i.e. all 26 active
> sibling repos are cloned under `$WORKSPACE_ROOT`, `.venv-workspace` exists, and `git status` is clean across every
> repo on `live-defi-rollout`. Confirm with:
>
> ```bash
> cd "$WORKSPACE_ROOT"
> for r in $(python3 -c "import json; d=json.load(open('unified-trading-pm/workspace-manifest.json')); print('\n'.join(k for k,v in d['repositories'].items() if not v.get('archived_into')))"); do
>     [ -d "$r/.git" ] || { echo "MISSING: $r"; continue; }
>     dirty=$(git -C "$r" status --porcelain | wc -l | tr -d ' ')
>     [ "$dirty" != "0" ] && echo "DIRTY:   $r ($dirty files)"
> done
> echo "(empty output = workspace clean and ready)"
> ```
>
> If anything's dirty, commit/push or stash before running `--init`. Slot worktrees branch off
> `origin/live-defi-rollout` (or a local-existing slot branch); leaving uncommitted state in the main clone DOES NOT
> propagate into the new slots, but it's good hygiene to start clean.

### Step 1 — pick N (slot count)

Rule of thumb: **N = peak concurrent Cursor / Claude Code tabs you expect to run**, +1-2 headroom for surge days.

| Operator | Recommended N | Rationale                                                            |
| -------- | ------------- | -------------------------------------------------------------------- |
| Ikenna   | 8             | Cross-cutting design + governance; typically 5-6 active tabs daily.  |
| Harsh    | 6-8           | Implementation-from-spec; tab count varies by daily work-split size. |

You can grow later with `--add-slot <N>`. Don't undersize — empty slots cost ~10 MB of metadata each (Git worktrees
share `.git/objects` with the main clone). Oversizing costs nothing operationally.

### Step 2 — run `--init`

```bash
cd "$WORKSPACE_ROOT"
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --init --slots 8
```

For Harsh (or anyone with a non-default `$USER`), set the branch prefix explicitly if you want a different naming:

```bash
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --init --slots 6 --operator harsh
# → branches will be tab/harsh/1, tab/harsh/2, ..., tab/harsh/6
```

Default behaviour reads `$USER` from the environment, so on Harsh's machine `$USER=harsh` (or similar) is picked up
automatically; the `--operator` flag is for override only.

**Expected output** (excerpt — full output is one block per slot × 26 repos):

```
[setup-tab-worktrees] Initialising 8 slots for operator 'harsh' under /Users/harsh/Code/.../.tabs/
[setup-tab-worktrees] Provisioning slot 1 (branch tab/harsh/1) ...
[setup-tab-worktrees]   ENV  slot 1 .envrc written (PREK_CACHE_DIR=.../prek)
[setup-tab-worktrees]   ADD  alerting-service → /Users/.../.tabs/1/alerting-service (branch tab/harsh/1)
...
[setup-tab-worktrees]   SKIP user-management-ui (no sibling clone at ...)
[setup-tab-worktrees] Provisioning slot 2 (branch tab/harsh/2) ...
...
[setup-tab-worktrees] Done. 8 slots ready. Next: assign themes via the daily work-split plan + harsh_orchestrator/LEDGER.md slot↔theme table.
```

Runtime: ~30s per slot on a typical Mac (network-free; worktrees share git objects with the main clone). 8 slots ≈ 3-4
minutes total.

### Step 3 — verification probes

After `--init` returns, run these in order:

```bash
# Probe 1 — all N slots provisioned with one worktree per active repo on the right branch.
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --list
# Expected: "slot 1: branch=tab/<op>/1 head=<sha>" through "slot N: branch=tab/<op>/N head=<sha>"
# All HEADs should equal the current live-defi-rollout tip.

# Probe 2 — git worktree list for PM shows N+1 entries (main clone + N slots).
git -C unified-trading-pm worktree list
# Expected: main clone line + N lines under .tabs/<N>/unified-trading-pm

# Probe 3 — each slot's .envrc declares PREK_CACHE_DIR + SLOT_NUMBER.
cat .tabs/1/.envrc
# Expected:
#   export UNIFIED_TRADING_WORKSPACE_ROOT=".../.tabs/1"
#   export PREK_CACHE_DIR=".../.tabs/1/.cache/prek"
#   export SLOT_NUMBER="1"
#   export SLOT_OPERATOR="<your-user>"

# Probe 4 — isolated index check: edit a file in slot 1, confirm main clone is unaffected.
echo "spike" > .tabs/1/unified-trading-pm/SPIKE_DELETE_ME.md
git -C .tabs/1/unified-trading-pm status --porcelain   # should show ?? SPIKE_DELETE_ME.md
git -C unified-trading-pm status --porcelain           # should be empty
rm .tabs/1/unified-trading-pm/SPIKE_DELETE_ME.md       # clean up
```

If any probe fails, re-run `--init` (idempotent) or fall back to manual `git worktree add` per the script's logic.

### Step 4 — update orchestrator LEDGER slot↔theme table

Open `<operator>_orchestrator/LEDGER.md` and update the `## Today's slot assignments` table with today's themes per the
daily work-split plan. Example for Harsh:

```markdown
## Today's slot assignments

**Slot count:** 6 (set 2026-05-11; grow with `--add-slot <N>` if peak parallel work exceeds).

| Slot | Theme                    | Plan-of-record / scope                                         |
| ---- | ------------------------ | -------------------------------------------------------------- |
| 1    | main orchestrator        | (this LEDGER) — direction-setting + Q&A dispatch + ping triage |
| 2    | mtds prediction smoke    | plans/active/predictions_master.md                             |
| 3    | features-onchain Phase 5 | plans/active/features_repo_consolidation_2026_05_08.md         |
| 4    | (idle)                   | —                                                              |
| 5    | (idle)                   | —                                                              |
| 6    | (idle)                   | —                                                              |
```

The daily work-split plan (`plans/active/work_split_<YYYY_MM_DD>_<operator>.md`) is the authoritative source for the
theme assignments. The LEDGER mirrors it so fresh tab-agents bootstrap with the mapping in hand.

### Step 5 — open Cursor at a slot

For each tab you want to spawn, two equivalent options — pick the one matching how you like the file tree rendered:

```bash
# Option A — Open as folder (single-root; flat file tree of all 27 repos as subdirs).
code "$WORKSPACE_ROOT/.tabs/<N>"

# Option B — Open as multi-root workspace (named labels per repo, custom emojis, folder grouping).
# The .code-workspace file is auto-copied into each slot by --init / --add-slot
# (provision_slot → copy_workspace_file), so this works immediately after Step 2.
code "$WORKSPACE_ROOT/.tabs/<N>/unified-trading-system-repos.code-workspace"

# OR for Claude Code CLI in a terminal:
cd "$WORKSPACE_ROOT/.tabs/<N>" && claude
```

Both options produce identical isolation — the window's CWD is rooted at the slot, all Git operations from any tab in
that window hit the slot's `.git/index`. Option B just gives you the curated multi-root view from
`unified-trading-system-repos.code-workspace`. The relative paths in the workspace file resolve against the slot dir.

The slot's `.envrc` will load `PREK_CACHE_DIR` + `SLOT_NUMBER` if you have direnv installed (otherwise source it
manually or set the env vars explicitly). Cursor's TypeScript server + file indexer cache per-workspace-path, so the
first open warms the cache; subsequent opens are instant.

### `.code-workspace` path-style contract (canonical vs slot copies)

Two distinct consumers read the multi-root workspace file, and they need **different `folders[].path` styles** — this is
deliberate, not drift:

| Consumer                  | File                                                                                    | `folders[].path` style         | Why                                                                                                            |
| ------------------------- | --------------------------------------------------------------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| Main-worktree view (root) | repos-root symlink → `.cursor/workspace-configs/` (dir symlink → the tracked canonical) | `../../<repo>` + `../../` root | Canonical lives 2 levels deep under `unified-trading-pm/cursor-configs/`; `../../` resolves to the repos root. |
| Slot copies (`.tabs/N/`)  | `.tabs/N/unified-trading-system-repos.code-workspace`                                   | bare `<repo>` + `.` root       | Slot file is 1 level deep; bare names resolve to the slot's own `.tabs/N/<repo>`.                              |

**Canonical SSOT** = `unified-trading-pm/cursor-configs/unified-trading-system-repos.code-workspace` (git-tracked). The
repos-root `unified-trading-system-repos.code-workspace` is a symlink whose chain resolves to it, so committing the
canonical durably fixes the main-worktree view.

`copy_workspace_file()` (in `setup-tab-worktrees.sh`) does **not** plain-`cp` the canonical into a slot — that would
carry the `../../<repo>` paths verbatim, which from `.tabs/N/` resolve to the **main** worktree (a silent footgun: the
dirs exist, so no error, but the slot's SCM panel points at the main checkout). Instead it rewrites paths to
bare-relative on copy (`../../<repo>` → `<repo>`, `../../` → `.`).

A blocking QG step (`scripts/quality_gates/check_workspace_code_workspace_drift.py`, wired into `quality-gates.sh`)
asserts the canonical `folders[]` (minus the workspace-root entry) == the active+scaffolded repo set in
`workspace-manifest.json`, and that no listed path is a known archived/consolidated repo. This closes the drift class
that caused VS Code's `<repo> does not appear to be a git repository` error. SSOT for the incident + remediation:
`plans/active/workspace_config_drift_remediation_2026_06_01.md`.

**Verify CWD before pasting the spawn prompt.** In a Cursor terminal of the new window:

```bash
pwd                                                              # → .../.tabs/<N>
git -C unified-trading-pm rev-parse --abbrev-ref HEAD            # → tab/<operator>/<N>
```

If `pwd` returns the main workspace root or the branch is `live-defi-rollout`, you opened the wrong directory.

### Step 6 — daily theme rotation

When the daily work-split plan reassigns slot `<N>` to a new theme:

```bash
# 1. From WITHIN the slot's worktree, commit + push any leftover WIP.
cd "$WORKSPACE_ROOT/.tabs/<N>/<repo-of-leftover-wip>"
# Use the per-shippable-unit commit cadence per CLAUDE.md "Commit + Push + Flip" rule.

# 2. From the workspace root, reset the slot to clean state on origin/live-defi-rollout.
cd "$WORKSPACE_ROOT"
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot <N>
# → verifies clean status across all 26 repos in the slot
# → fetches origin
# → rebases tab/<operator>/<N> onto origin/live-defi-rollout
# Aborts with file list if dirty; operator commits / stashes / discards before retry.

# 3. Update the orchestrator LEDGER slot↔theme table (manual edit) with the new theme.

# 4. The tab agent in that slot picks up the new theme on its next message — no Cursor restart needed.
```

Pinned to the daily work-split plan's "Daily reset" checklist (per [`CLAUDE.md`](../../cursor-configs/CLAUDE.md) §
"Daily Work-Split Process" § "Daily reset (each morning)" steps 5-6).

### Step 7 — troubleshooting

| Symptom                                                                                                                                                                                                                                           | Likely cause                                                                                                                                                                                                                                                                                                                                                                                               | Fix                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `--init` reports `SKIP <repo>` for an unexpected repo                                                                                                                                                                                             | Repo not cloned as sibling under `$WORKSPACE_ROOT`                                                                                                                                                                                                                                                                                                                                                         | Re-run `bash scripts/workspace/workspace-bootstrap.sh --skip-fresh` to clone missing repos; then re-run `--init` (idempotent).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `--reset-slot <N>` aborts with "dirty file(s)" + an unfamiliar file                                                                                                                                                                               | Foreign-agent WIP OR runtime artifact (e.g. `.local-dev-cache/`, `catboost_info/`)                                                                                                                                                                                                                                                                                                                         | Per CLAUDE.md "Two teammates" rule: do NOT `git checkout --` foreign WIP. For runtime artifacts: discard with `git checkout --`. For WIP: commit/stash.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Cross-slot foot-gun-shaped behaviour (foreign work bundled)                                                                                                                                                                                       | You're not in a slot worktree — main clone state leaked                                                                                                                                                                                                                                                                                                                                                    | `cd $WORKSPACE_ROOT/.tabs/<N>/` and start fresh. Confirm with `git rev-parse --show-toplevel` → should resolve to a path under `.tabs/<N>/`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| prek auto-restore wipes your edits mid-session                                                                                                                                                                                                    | Per-slot `PREK_CACHE_DIR` not exported (direnv not loading `.envrc`)                                                                                                                                                                                                                                                                                                                                       | Manually: `source $WORKSPACE_ROOT/.tabs/<N>/.envrc` before any commit, OR install direnv + run `direnv allow`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `git worktree add` fails with "already checked out at .../.tabs/<N>/"                                                                                                                                                                             | Stale worktree entry after a manual `rm -rf .tabs/<N>/`                                                                                                                                                                                                                                                                                                                                                    | `git -C <repo> worktree prune` to clean the registry, then re-run `--add-slot <N>`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Branch `tab/<op>/<N>` already exists with diverged history                                                                                                                                                                                        | Slot was previously used + branched off an older `live-defi-rollout`                                                                                                                                                                                                                                                                                                                                       | `setup-tab-worktrees.sh --reset-slot <N>` rebases onto current origin/live-defi-rollout (assuming clean state).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `git rebase` produces conflicts during `--reset-slot`                                                                                                                                                                                             | The slot has commits not on `live-defi-rollout` (genuinely-divergent slot)                                                                                                                                                                                                                                                                                                                                 | Manual resolution: enter the slot, resolve conflicts, `git rebase --continue`, push the slot branch. Then re-run `--reset-slot` if needed.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `Applying autostash resulted in conflicts. Your changes are safe in the stash.` during `git pull --rebase --autostash`                                                                                                                            | A foreign agent's mid-edit working-tree content (auto-stashed by the rebase) conflicts with the new HEAD. Common when a slot has foreign-dirty files (e.g. `uv.lock`, `.pre-commit-config.yaml`) and you rebase onto remote.                                                                                                                                                                               | **`git rebase --abort`** — keeps the autostash intact, restores pre-rebase state. Then `git stash push -- path/to/your_file` (only your files by name), retry the rebase, and `git stash pop` your stash. **NEVER `git checkout HEAD -- <conflicted_file>` followed by `git stash drop`** — that destroys the foreign agent's only copy of their WIP. Per CLAUDE.md "Two teammates" rule, the dropped-commit hash printed by `git stash drop` is reachable via `git stash store <hash>` until next GC, but treat any drop of an autostash you didn't create as a near-miss incident requiring a ping in `<side>_orchestrator/pings/slot_<N>.md`. Incident reference: slot-1 2026-05-19 strategy-service autostash drop (recovered via dangling commit e53ad7c).                                                                                                                                                                                                                                  |
| A concurrent agent in your shared `.tabs/<N>/` worktree moves `HEAD` / `FETCH_HEAD` / the slot branch under you; push to `live-defi-rollout` rejected; `FETCH_HEAD`-based diagnostics contradict each other (e.g. "already on LDR" when it isn't) | Shared `.git` — another interactive session OR an orchestrator-spawned worker in the same worktree runs `fetch` / `commit` / `rebase`, rewriting shared refs mid-task                                                                                                                                                                                                                                      | Verify against `origin/live-defi-rollout` (NEVER `FETCH_HEAD`). Promote your commit via a throwaway worktree off the integration branch — see "Isolated-worktree promotion under shared-worktree ref races" below. Do NOT autostash-rebase the shared dirty tree.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| A slot worktree silently falls dozens/hundreds of commits behind `origin/live-defi-rollout` even though the FF-pull cron runs every 5 min and the remote is configured correctly                                                                  | **FF-pull starvation**: an uncommitted local edit COLLIDES with an incoming changed file, so every `git pull --ff-only` aborts. Both crons treat "couldn't FF" as a benign skip, so nothing alerts and the slot keeps falling behind. (Reference: slot-5 unified-trading-pm 963 behind, 2026-06-01.)                                                                                                       | The **FF-pull starvation watchdog** now pages on this (see "FF-pull starvation watchdog" below): a `FF-PULL STARVATION — slot N / repo` message lands in the slot inbox naming the colliding files. Remediate per the ping: `git stash push -- <colliding paths> && git pull --ff-only && (commit-or-restore the stash)`. The colliding file is usually foreign WIP — **stash-by-name, do NOT discard** (Two-teammates HARD RULE).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `git pull` / `git fetch --tags` is rejected with `! [rejected] vX.Y.Z -> vX.Y.Z (would clobber existing tag)` (commonly `v1.0.0` / `v1.2.0` after a repo graduates to 1.0.0)                                                                      | **Stale local release tag**: a local lightweight tag points at a different object than the remote's tag of the same name. The remote tag was re-created / annotated by **semver-agent** (the SSOT for version tags); git refuses to clobber a local tag on fetch by default, which also blocks the branch FF inside `git pull`. (Reference: unified-trading-library `v1.0.0`/`v1.2.0`, slot-5 2026-06-01.) | **`git fetch origin --tags --force`** — a **local-only** ref update that points the stale local tags at the canonical remote objects. No commits are lost (the old tag's commit stays reachable via branch history) and **nothing is pushed**. Then re-run `git pull --ff-only`. Safe because semver-agent owns release tags on the remote and the remote is always canonical for them — **never** force-push local tags the other way (`git push --tags --force` to remote is banned; it can revert a semver-agent bump). `slot-cron-ff-pull.sh` now fetches `--tags --force` (both the phase-1 main-clone prefetch and the phase-2 per-repo fetch), so cron-driven hosts **auto-heal stale release tags fleet-wide** — linked tab worktrees share the main clone's `.git/refs`, so one forced tag sync fixes every slot at once. The clobber error therefore only surfaces on a manual `git pull` between cron ticks (or on a host without the cron installed), where the one-liner clears it. |

### Isolated-worktree promotion under shared-worktree ref races (canonical fix, codified 2026-06-01)

**Symptom.** A concurrent agent shares your slot's `.git` — another interactive session, or an orchestrator-spawned
worker operating in the same `.tabs/<N>/<repo>/` worktree. It commits / rebases / fetches, so `HEAD`, the slot branch,
and **especially `FETCH_HEAD`** move under you mid-task. Your `git push origin HEAD:live-defi-rollout` is rejected as
non-fast-forward, and any diagnostic that reads `FETCH_HEAD` gives contradictory answers — you can even conclude "my
work is already on LDR" when it is **not** (the moving `FETCH_HEAD` momentarily pointed at the worker's local tip, which
contained your own commit as an ancestor, so the file content matched byte-for-byte).

**Two hard don'ts** (both are variants of the foreign-WIP-destruction foot-gun):

1. **Never trust `FETCH_HEAD` when the worktree is shared.** `FETCH_HEAD` is rewritten by _any_ agent's `git fetch` in
   the shared `.git`. Verify only against the stable remote-tracking ref:
   `git merge-base --is-ancestor <sha> origin/live-defi-rollout` and `git cat-file -e origin/live-defi-rollout:<path>`.
2. **Never autostash-rebase the shared dirty tree** to "integrate" the remote (see the autostash row above) — it stashes
   the concurrent agent's WIP and can drop it.

**Canonical fix — promote YOUR work via a throwaway worktree off the integration branch.** This never touches the shared
`.tabs/<N>/` tree, so the concurrent worker is undisturbed:

```bash
# Your work is already committed on the slot branch; MINE=<your commit sha>.
git -C <repo> fetch origin live-defi-rollout
git -C <repo> worktree add --detach /tmp/promote-$$ origin/live-defi-rollout
git -C /tmp/promote-$$ cherry-pick "$MINE"

# On conflict: KEEP LDR's side for hunks that are the OTHER agent's content (their uncommitted work your
# commit happened to snapshot) — they commit it themselves. Keep-ours strip of one conflicted file:
#   awk 'BEGIN{keep=1} /^<<<<<<< /{keep=1;next} /^=======$/{keep=0;next} /^>>>>>>> /{keep=1;next} {if(keep)print}' \
#       FILE > FILE.tmp && mv FILE.tmp FILE        # NOTE: BEGIN{keep=1} is mandatory, else pre-conflict text is dropped
#   (restore a botched resolution with: git checkout -m -- FILE)

# Trim any other-agent content that AUTO-merged in cleanly but is NOT on LDR (reset that file to LDR, re-add only
# your hunk):
#   git -C /tmp/promote-$$ checkout origin/live-defi-rollout -- <file>   # then re-insert just your section

# PRE-PUSH GATE — the changeset must be YOURS-ONLY:
git -C /tmp/promote-$$ add -A
git -C /tmp/promote-$$ diff --cached origin/live-defi-rollout --stat                 # only your files
git -C /tmp/promote-$$ diff --cached origin/live-defi-rollout | grep '^[-+]' | grep -v '^[-+][-+]'
#   ^ every +/- line must be yours; a foreign +/- means you still need to trim.

git -C /tmp/promote-$$ commit --no-verify -m "docs(...): ... (yours-only, no other-agent content)"
git -C /tmp/promote-$$ fetch origin live-defi-rollout && git -C /tmp/promote-$$ rebase FETCH_HEAD   # FETCH_HEAD safe here: isolated worktree
git -C /tmp/promote-$$ push origin HEAD:live-defi-rollout
git -C <repo> worktree remove /tmp/promote-$$ --force
```

**The principle.** Get YOUR work onto LDR without (a) clobbering the concurrent agent's _committed_ work (keep LDR's
side on conflicts) or (b) imposing their _uncommitted_ snapshot that your commit incidentally captured (trim it; they
push their own). The pre-push gate — `git diff --cached origin/live-defi-rollout` showing only your lines — is the
contract; if a `+`/`-` isn't yours, trim it before pushing. If your work was bundled with a concurrent worker's sweep
and the operator pre-acked shipping it ("worst case commit some of it"), keeping it is allowed — but the default is
trim, to avoid a future merge clash when they push their own copy.

Incident reference: slot-1 2026-06-01 data-source-provenance promotion — `FETCH_HEAD` race led to a false "already on
LDR" read; cherry-pick dragged the worker's in-flight "zero-rows=silent-lie" sweep into `defi`/`mtds_mdps`/`manifest`;
resolved by keep-LDR-side on the `defi` conflict + trimming the dragged sweep from `mtds_mdps`/`manifest`, pushed clean
as a provenance-only commit.

### Cron self-pull + Path-B per-slot ref refresh (codified 2026-06-12)

**Self-pull (every machine-run PM cron).** Each cron's crontab LINE — the immutable anchor — refreshes its OWN script
from `origin/live-defi-rollout` before running it, so a stale/dirty root PM clone never starves the cron of current code
(the chicken-and-egg that froze clones hundreds of commits behind). The snippet is emitted by the shared helper
`scripts/dev/cron-self-pull-lib.sh` (`emit_cron_self_pull <pm_dir> <branch> <script> [data…]`) so the pattern is DRY in
source even though each emitted line is self-contained. It is **syntax-gated (H6)**: the candidate is streamed via
`git show` to a temp, `bash -n`'d, and only `mv`+`chmod 755`'d into place if it parses — so one bad commit can never
propagate fleet-wide and stop the cron; on any failure (offline / parse-fail) the last-good local copy runs. Three
machine crons self-pull: `slot-cron-ff-pull` (+ its `cron-branch-overrides.txt` data sibling), `slot-host-symmetry-verify`,
and `slot-git-status-report` (added 2026-06-12 — was bare). All installed/updated by `install-slot-cron-ff-pull.sh` (run
once per host from the ROOT clone, never a slot — the Phase-D guard refuses a `.tabs/` cwd). `refresh-manifest-dag` is
exempt (retired); the orphan-ping **Cloud Run Job** is exempt (it clones PM fresh each run — only the local Ikenna-machine
crontab copy would need the self-pull).

**Path-B per-slot ref refresh.** Under Path-B every slot is an independent `git clone --reference` with its OWN refs
(objects shared via `objects/info/alternates`, refs NOT shared). `slot-cron-ff-pull.sh` PHASE-1 prefetch updates only the
main-workspace clones' refs, so PHASE 2 MUST refresh each slot's `origin/<branch>` — a LOCAL ref-copy from the
`--reference` clone (objects already shared → no network), network-fetch fallback (`_refresh_independent_clone_ref`).
Without it a slot compares HEAD against a stale local ref and silently falls behind (observed up to +149 commits; fixed
2026-06-12). The legacy "linked tab worktrees share the main clone's refs" assumption (still phrased in the tag-clobber
row above) holds ONLY for `.git`-FILE linked worktrees, not Path-B clones.

### FF-pull starvation watchdog (codified 2026-06-01)

**Failure mode.** A slot worktree sits N commits behind `origin/<integration-branch>` with the remote configured
correctly, but `slot-cron-ff-pull.sh` silently no-ops every run because an **uncommitted local edit collides with an
incoming changed file**, so every `git pull --ff-only` aborts. Both crons (`slot-cron-ff-pull.sh`,
`slot-git-status-report.sh`) historically treated "couldn't FF" as a benign skip — nothing alerted, and the slot fell
further behind indefinitely (reference incident: slot-5 `unified-trading-pm` 963 behind, 2026-06-01).

**Actor vs detector.** `slot-cron-ff-pull.sh` stays the **actor** (it does the FF). `slot-git-status-report.sh` (which
already walks each repo's ahead/behind + dirty state for the dashboard, every 5 min) is the **detector/alerter**. It
shells out to `scripts/dev/ff-starvation-detect.sh` per repo and, on a positive detection, POSTs a `FF-PULL STARVATION`
ping to the slot's message inbox (`/api/slots/<N>/message`, `from_role: main`) the same way it POSTs git-status. The
watchdog does **not** auto-resolve the collision — that needs the stash-by-name + adjudicate judgment from the
Two-teammates HARD RULE.

**Detection rule** (per slot × per repo, each cron tick — see `ff-starvation-detect.sh`):

```
behind    = git rev-list --count HEAD..origin/<branch>
ff_clean  = (behind > 0) AND (merge-base HEAD origin/<branch> == HEAD)   # a true fast-forward is possible
dirty     = git status --porcelain is non-empty
collision = ff_clean AND dirty AND (incoming changed-file set ∩ dirty file set ≠ ∅)
STARVED   = collision AND (behind >= FF_STARVE_COMMIT_THRESHOLD
                           OR oldest colliding dirty file age > FF_STARVE_AGE_HOURS)
```

`collision` (not merely `dirty`) is the precise trigger: a dirty file that does **not** intersect the incoming change
set does not block `--ff-only`, so it is not a starvation cause and must not page. The behind/age gate avoids paging on
normal in-flight work (a slot 1–2 commits behind mid-edit is healthy). Diverged/ahead is a different failure mode
handled by the ff-pull cron's `[skip:diverged]`/`[skip:ahead]`.

**De-duplication.** One ping per (slot, repo) starvation **episode** — a marker under `.tabs/.ff-starve-state/` is set
on first ping and cleared the moment the repo is no longer starved, so a fresh episode re-pings.

**Tunables (env):** `FF_STARVE_WATCHDOG` (default `1`; set `0` to disable), `FF_STARVE_COMMIT_THRESHOLD` (default `25`),
`FF_STARVE_AGE_HOURS` (default `6`).

**Tests:** `tests/test_ff_starvation_detect.bats` — collision→signal, non-colliding-dirty→no-signal,
below-threshold→no-signal, clean/up-to-date→no-signal.

### Ikenna's provisioning evidence (2026-05-10/11)

Ikenna's machine provisioned 8 slots successfully via this recipe:

```
slot 1: branch=tab/ikennaigboaka/1 head=6a6ae73b
slot 2: branch=tab/ikennaigboaka/2 head=6a6ae73b
...
slot 8: branch=tab/ikennaigboaka/8 head=6a6ae73b
```

26 active repos × 8 slots = 208 worktrees provisioned. All 4 verification probes green. The same recipe applies to Harsh
— only `$USER` (or `--operator` override) and chosen slot count `N` differ.

## Slot is durable; theme is daily

The mapping of slot ↔ theme lives in **two** places, both daily-updated:

1. **The day's work-split plan** (`plans/active/work_split_<YYYY_MM_DD>_<operator>.md`) — authoritative for today.
2. **The operator's orchestrator LEDGER** (`<operator>_orchestrator/LEDGER.md`) "Today's slot assignments" section —
   forward index that fresh tab-agents read on bootstrap.

Example LEDGER slot↔theme table:

```markdown
## Today's slot assignments (2026-05-10)

| Slot | Theme                       | Plan-of-record                                                |
| ---- | --------------------------- | ------------------------------------------------------------- |
| 1    | main orchestrator + on-call | (this LEDGER)                                                 |
| 2    | cefi-master                 | plans/active/cefi_master.md                                   |
| 3    | writegate Wave 4 slice (b)  | plans/active/writegate_honest_coverage_endtoend_2026_05_06.md |
| 4    | defi paper-trade smoke      | plans/active/defi_master.md                                   |
| 5    | (idle)                      | —                                                             |
```

Three benefits of fixed slots over ephemeral spin-ups:

1. **Cursor extension state caches.** TS server warmup + indexing + watcher setup is 30-90s per repo × 6-8 repos × N
   slots. Ephemeral spin-ups burn 30+ min/day of bootstrap; persistent slots: one-time cost.
2. **Cross-day workstreams continue cleanly.** Writegate spans weeks; cefi-master spans months. Same slot the whole
   time.
3. **Slot↔theme is the operator's load-balancer**, not a worktree property. Decoupling lets the operator reshuffle
   themes daily without touching filesystem state.

## Slot-reset discipline (between themes)

When a slot's theme changes (typically morning, when the daily work-split reassigns):

```bash
# Step 1 — operator commits / pushes / discards any leftover WIP in the slot.
# Step 2 — reset the slot:
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot <N>
# → Verifies every repo's worktree clean (aborts with file list if dirty)
# → Fetches origin
# → Rebases tab/<operator>/<N> onto origin/live-defi-rollout
# → Truncates <side>_orchestrator/pings/slot_<N>.md to a fresh stub (commits with [reset-slot] tag)
# → Slot is ready for the new theme.
```

The script **aborts on dirty state** rather than silently rebasing over it. If aborted, the operator's choices are:
commit, stash, or `git checkout --` per-file (only for tracked runtime artifacts that regenerate naturally — never for
foreign agents' WIP per the CLAUDE.md "Two teammates" rule). Then re-run `--reset-slot`.

### Ping-doc reset on re-theme

The `--reset-slot` truncate step writes a stub like:

```text
# Slot N ping file — re-themed YYYY-MM-DD
[YYYY-MM-DD HH:MM UTC] [main → slot N] — RE-THEMED via --reset-slot.
Prior theme: TBD (main fills from yesterday's LEDGER + prior plan's DONE block on first read).
New theme: TBD (main fills from today's work-split + plan-of-record + spawn prompt).
```

Slot main fills the two `TBD` lines on first read. The prior content survives in git history + the prior plan's
`## DONE` block — nothing is lost. The `[reset-slot]` commit tag makes the truncate recognisable in cross-side acks.

**For same-theme continuations** (slot stays on the same plan across sessions), do NOT run `--reset-slot`. Use `/clear`
in the Claude Code session to clear conversation context; the ping file retains day-context. To prevent unbounded growth
within a multi-day same-theme run, call the read-time rollup helper at slot boot:

```bash
python3 unified-trading-pm/scripts/agents/rollup_resolved_pings.py \
    unified-trading-pm/<side>_orchestrator/pings/slot_<N>.md
```

This helper rolls up entries that are both (a) ✅ DONE / ✅ RESOLVED and (b) older than 24 hours into a
`## Prior context (rolled)` section at the bottom of the file. It is triggered at read-time (NOT by the script), to
avoid racing with concurrent append-writes from sub-agents.

Pinned to the daily work-split plan's "Daily reset" checklist. Operators should habituate to running `--reset-slot`
before assigning a slot to a different theme.

## Foot-gun mitigations vs. shared-tree model

The previous shared-working-tree model produced four documented foot-guns (#1 foreign bundling, #2 path-arg masking, #3
concurrent reset wipe, #4 prek auto-restore race). With per-slot worktrees:

| Foot-gun                            | Status under per-slot model                                                                                                           |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| #1 foreign work bundled in          | **Unrepresentable.** No other slot can touch your `.git/index`.                                                                       |
| #2 `--cached --stat <path>` masking | **Unrepresentable.** Only your hunks are in your index. (Discipline still good practice within-slot if sub-agents stage in parallel.) |
| #3 concurrent reset wipe            | **Unrepresentable.** No other slot can move your HEAD.                                                                                |
| #4 prek auto-restore race           | **Mitigated via `PREK_CACHE_DIR` per-slot** (auto-set in each slot's `.envrc`). prek patches stay slot-local; no cross-restore.       |

Within-slot collisions (sub-agents in the same slot writing to overlapping files) remain possible. Master agent
mitigations:

- Partition sub-agent fan-out by repo/dir at spawn time (sub-A → MTDS, sub-B → UTL, sub-C → PM plan section X — no
  overlap by design).
- For unavoidable PM repo overlap (every slot touches plans + codex), master pre-allocates plan sections to sub-agents
  so they don't `git add` the same file simultaneously.
- Standard pre-commit check still applies within a slot — `git status` + `git diff --cached --stat` (no path arg) before
  every commit.

## Path A vs Path B (mechanism)

Default is **Path A**: `git worktree add` on per-slot branch `tab/<operator>/<N>` rebased from `live-defi-rollout`. The
slot master pushes its slot branch to origin per shippable unit (`git push origin tab/<op>/<N>`) AND immediately
FF-pushes the slot branch tip into `live-defi-rollout` (`git push origin tab/<op>/<N>:live-defi-rollout` — server-side
FF; remote rejects if non-FF, signalling rebase-needed). The bundled cadence is the canonical Half 1 + Half 4 of the
[`Commit + Push + Flip Plan Checkboxes`](../../cursor-configs/CLAUDE.md) HARD RULE — codified 2026-05-11 after the slice
(b) ship-blindness incident where slot-branch commits sat hours private from downstream consumers.

**Path B fallback** (if Path A surprises): `git clone --reference` per slot. Each slot is an independent clone sharing
`.git/objects` with the operator's primary clone via `--reference`. Each clone is on `live-defi-rollout` directly.
Bootstrap script supports either; Phase 0 spike chose Path A (no surprises observed).

## Within-slot ergonomics

Every slot worktree's `.envrc` declares:

```bash
export UNIFIED_TRADING_WORKSPACE_ROOT="${WORKSPACE_ROOT}/.tabs/<N>"
export PREK_CACHE_DIR="${WORKSPACE_ROOT}/.tabs/<N>/.cache/prek"
export SLOT_NUMBER="<N>"
export SLOT_OPERATOR="<operator>"
```

direnv-style auto-load isolates the prek patch cache + tells scripts which workspace root applies. Sibling-path-deps
(`uv pip install -e ../<dep>`) resolve correctly because every active repo's worktree lives under the same slot dir.

## Reconciliation — plan-aware merge resolution

When the slot master pushes a shippable unit and finds incoming commits on origin (another slot landed first), it
rebases. The rebase may surface conflicts — especially in PM repo, the always-touched surface. **Plan-aware merge
resolution** (see [`plan-aware-merge-resolution.md`](plan-aware-merge-resolution.md)) gives the master agent a
structured protocol: classify conflict shape (append-section / checkbox-flip / paragraph-rewrite), auto-resolve trivial
ones, escalate semantic conflicts to the operator with plan-context reasoning.

### Align = the merged combination (rebase-onto-LDR), not "take one side" (codified 2026-06-03)

When a slot tab branch has **diverged** from LDR (your commits + N incoming; `origin/tab/<op>/N` is no longer an
ancestor of `origin/live-defi-rollout`, so the tab→LDR mirror jams), aligning is a **content merge, not a pointer
overwrite**:

1. `git rebase origin/live-defi-rollout` — replays YOUR commits onto current LDR, dropping patch-id duplicates.
2. **Resolve each conflict keeping BOTH sides' genuine work.** Additive plan/doc/code from both agents survives. Where
   two agents independently wrote the **same** rule/fix (a "two-similar" conflict), MERGE into the single best version
   (fold the weaker subset into the stronger superset — don't keep redundant duplicates). Incident 2026-06-03: a slot
   independently added a "never pipe a backgrounded command through `tail`/`head`" rule that a richer "Background-task
   honesty" rule subsumed → merged into one.
3. **VERIFY content survival before pushing** — grep your key additions AND the incoming ones in each rebased file. A
   wording / em-dash mismatch can read as "lost" when it survived; a genuine drop MUST be caught here, not after the
   push.
4. `git push --force-with-lease=tab/<op>/N:<old-tip-sha> origin HEAD:tab/<op>/N`.

**`--force-with-lease` is branch-tip safety, NOT content safety (HARD distinction).** The lease only refuses the push if
`origin/tab/<op>/N` moved since your fetch (catching a concurrent push to YOUR branch). It does **not** inspect files or
whether another agent had work on them. OTHER agents' work is protected by: (a) rebasing **onto** current LDR so their
commits are your BASE (never overwritten — LDR itself is untouched by the push); (b) the conflict-merge keeping both;
(c) the post-rebase verify. Safe ONLY because the tab branch is the slot's alone and you rebased onto (not discarded)
LDR. **NEVER `--force` / `--force-with-lease` a shared branch (`live-defi-rollout` / `main`).**

## Commit attribution — slot + host in the author NAME (codified 2026-06-03)

**Problem (two layers, both found in the 2026-06-03 slot-3 audit):**

1. The author **name** is bare `ikennaigboaka` everywhere → CI alerts + cross-agent triage cannot tell which slot / host
   produced a commit, and a foreign commit on a slot's tab branch is invisible by author.
2. The author **email is WRONG fleet-wide** — of 25 slot worktrees, ~14 carried the
   `semver-rollout[bot]@users.noreply.github.com` email (so **agent commits there masquerade as the semver bot** —
   risky, since semver-agent's own bot/author checks key off that email) and ~7 carried `agent@ci.local` (unattributed).
   Only `unified-trading-pm` was correct. Almost certainly leaked from a setup/semver step that wrote the bot identity
   into persistent per-worktree config. **Root-cause hunt + recurrence-guard is part of the implementation todo.**

**Mechanism (low-risk — local per-worktree config only affects that slot's commits):** STANDARDISE both name + email:

- `user.name = "ikennaigboaka [slot-<N>·<host>]"` — `<N>` from the `tab/<op>/<N>` branch; `<host>` = `laptop` (or the
  short hostname) on a workstation, the `vm-<id>` on a fleet VM.
- `user.email = "ikennaigboaka@gmail.com"` — the GitHub-attributed human account (NOT the bot, NOT `agent@ci.local`).
  GitHub commit attribution + semver-agent bot/author checks key off the EMAIL, so this both fixes attribution and stops
  the bot-masquerade, while making `git log --format=%an`, the GitHub author column, and CI `head_commit.author.name`
  correct + slot-aware.

**Per-operator (NOT hardcoded — codified 2026-06-05):** the email + name handle are **the operator's own GitHub
account**, which DIFFERS per laptop — Ikenna `ikennaigboaka <ikennaigboaka@gmail.com>`, Harsh
`harshkantariya <harshkantariya@odum-research.com>`. The three scripts that touch identity — the per-repo
`fix-commit-identity.sh` pre-commit hook, `setup-tab-worktrees.sh` (provision), and `verify-slot-host-symmetry.sh`
(assert) — all resolve it the SAME host-stable way (the earlier hardcoded `ikennaigboaka@gmail.com` constant made
`verify` step 9 unachievable on Harsh's laptop without the hook actively rewriting his commits to Ikenna's identity):

```
1. env override            SLOT_CANON_EMAIL / SLOT_CANON_NAME
2. per-machine git config   git config --global slotIdentity.email   /   slotIdentity.name
3. fleet default            ikennaigboaka@gmail.com / ikennaigboaka   (VMs + Ikenna's laptop, unconfigured)
```

A **non-Ikenna host declares itself ONCE** (readable by every git invocation incl. the per-repo hook, so no env-plumbing
or cwd-climbing needed):

```bash
git config --global slotIdentity.email "harshkantariya@odum-research.com"
git config --global slotIdentity.name  "harshkantariya"
```

VMs leave it unset → fall through to the Ikenna-owned fleet default (VMs commit under the Ikenna GitHub account by
design). The `tab-mirror-to-ldr.yml` CI bot keeps its own `tab-mirror[bot]` identity (not a per-operator slot identity).

**Set per-worktree — MECHANISM GOTCHA (codified 2026-06-03):** `.tabs/<N>/<repo>` are **git worktrees that SHARE the
main clone's `.git/config`**, so plain `git config user.name` is shared across ALL worktrees of a repo (last-writer-wins
— useless for per-slot identity; the 2026-06-03 naive loop made every slot read `[main·laptop]`). Per-slot identity
**requires git's per-worktree config**:

```bash
# once per repo (on the shared config):
git config extensions.worktreeConfig true
# then per worktree (writes .git/worktrees/<wt>/config.worktree, NOT the shared file):
git config --worktree user.name  "ikennaigboaka [slot-<N>·<host>]"
git config --worktree user.email "ikennaigboaka@gmail.com"
```

`setup-tab-worktrees.sh` runs this at `--init` / `--add-slot` / `--reset-slot` (it already writes a per-slot `.envrc`;
the same provisioning step enables `extensions.worktreeConfig` + sets `--worktree` identity). Sub-agents share the slot
worktree → inherit the `--worktree` tag automatically. Do NOT hand-edit `~/.gitconfig`.

**Consumers:** CI alert workflows attribute via `github.event.head_commit.author.name`; the slot-git-status-report +
orphan-ping crons can group by slot. A machine-parseable `Agent-Slot:` / `Agent-Host:` commit trailer (a
`prepare-commit-msg` hook) is the follow-up if the name string proves awkward to parse. Implementation (setup script +
CI parse) is tracked as a plan todo; until it lands, agents set the name manually per the CLAUDE.md Git-discipline
directive.

## Upstream tracking — a tab branch upstream STAYS `origin/live-defi-rollout` (HARD RULE codified 2026-06-04)

**The git upstream of every `tab/<op>/N` worktree MUST be `origin/live-defi-rollout`, NEVER `origin/tab/<op>/N`.**
`setup-tab-worktrees.sh` sets it correctly (`git worktree add --track -b tab/<op>/N … origin/live-defi-rollout` → the
`--track` makes the upstream LDR). The drift cause is a single command: **`git push -u origin HEAD:tab/<op>/N`** (or
`git branch --set-upstream-to=origin/tab/<op>/N`) re-points the upstream to the remote tab branch. Symptom: the git
client / IDE source-control panel then shows a **phantom "ahead N"** (e.g. "ahead 52/70") measured against the **stale
remote tab branch** — which is NOT real divergence (local is still exactly at LDR, `0/0` vs `origin/live-defi-rollout`).
The remote tab is just behind because the FF-push of a finished unit and the cron lag the integration tip.

**Rule for agents (local OR VM):**

- **NEVER `git push -u` a tab branch.** Push with the explicit refspec, no `-u`: `git push origin HEAD:tab/<op>/N` (this
  is already the per-shippable-unit form below; it does NOT touch the upstream). Never
  `git branch --set-upstream-to=origin/tab/...`.
- **Detect**: `git rev-parse --abbrev-ref --symbolic-full-name @{upstream}` MUST print `origin/live-defi-rollout`. If it
  prints `origin/tab/<op>/N`, the worktree has drifted.
- **Fix (idempotent, safe)**: `git branch --set-upstream-to=origin/live-defi-rollout tab/<op>/N`.
- **Why it's harmless functionally but still must be fixed**: `slot-cron-ff-pull.sh` pulls `live-defi-rollout`
  **explicitly** (`git pull --rebase origin live-defi-rollout`), not via `@{upstream}`, so the FF-pull is unaffected;
  and `push.default=simple` **refuses** a bare `git push` when the branch name (`tab/<op>/N`) ≠ the upstream name
  (`live-defi-rollout`), so a tab branch can NEVER accidentally push to LDR even with the upstream set to LDR. The only
  damage is that the ahead/behind **display lies** (phantom "ahead N"), which wastes triage time and masks the true
  position vs the integration axis. So keep all worktrees uniform on `origin/live-defi-rollout`.
- **Audit the whole slot host**:
  `for d in */; do (cd "$d" && echo "$d $(git rev-parse --abbrev-ref @{upstream} 2>/dev/null)"); done` — every line
  should end `origin/live-defi-rollout`. (2026-06-04 audit: 22/25 correct; mtds + UAC + UTL had drifted to `origin/tab`
  from a prior `git push -u` and were re-synced.) Candidate for `verify-slot-host-symmetry.sh` to assert per tick so
  drift self-heals fleet-wide.

## Per-shippable-unit FF-push into `live-defi-rollout` (HARD RULE codified 2026-05-11)

Every push to a slot branch MUST be followed immediately by a server-side fast-forward push of the slot tip into
`live-defi-rollout`. This is the Half 4 codification in [`cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) §
"Commit + Push + Flip Plan Checkboxes" — the visibility complement to Half 1's durability push.

**Canonical command** (bundles Half 1 + Half 4 in one bash window):

```bash
git push origin tab/<operator>/<N> --no-verify \
  && git push origin tab/<operator>/<N>:live-defi-rollout --no-verify
```

The `tab/<op>/<N>:live-defi-rollout` form is a server-side FF push — origin verifies it's a fast-forward and advances
`live-defi-rollout` to the slot tip. **Remote rejects non-FF**: if rejected, your slot branch is behind LDR; rebase onto
`origin/live-defi-rollout` (existing conditional-push protocol) and retry both pushes.

**Why not auto-merge in a script.** The conditional check `ahead=N, behind=0` is the natural FF guard. A script that
runs the bundled command on every commit would mostly work — but the rebase-on-failure branch needs human (or agent)
judgment per plan-aware-merge-resolution. The HARD RULE is the discipline; the bash bundling is the implementation.

**Reference incident 2026-05-11**: slot 2 shipped writegate slice (b) end-to-end across 5 repos but every commit sat on
`tab/ikennaigboaka/2` for hours while downstream agents had no way to import the new helpers. Operator had to explicitly
FF-merge slot branches into LDR to unblock the dep chain (`manifest_schema_final_gate` Phase 2 was waiting on the UTL
`manifest_completeness` helper; slice (c) per-service rollout owners were waiting on the MDPS POC as a copy-paste
template). The Half 4 rule codifies this away.

**Foot-gun #5 — durable but invisible**. A clean Half 1 push to a slot branch creates a false sense of "shipped": the
commit is on origin, the plan-flip checkbox is `[x]`, but `live-defi-rollout` doesn't have it yet. Downstream agents
reading the plan, attempting `git fetch origin live-defi-rollout && grep <new_symbol>`, find no match and treat the plan
flip as a false claim. The fix is Half 4 — make the work visible at the same moment it becomes durable.

## On-demand artifact pattern — venvs, node_modules, caches

**Slot worktrees are code-only.** No `.venv/`, no `node_modules/`, no `dist/`, no `.next/`. Build artifacts come into
existence only when a worker first spawns into a slot and needs them, and they live entirely inside the gitignored
surface — never tracked, never copied across slots.

| Artifact                                    | Build trigger                                              | Lives at                                                   | Survives slot reset?                   |
| ------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------- | -------------------------------------- |
| `.venv/` (per Python service repo)          | `uv sync` on first worker spawn or first manual invocation | `<repo>/.venv/` inside the slot worktree                   | No — `--reset-slot` wipes the slot dir |
| `.venv-workspace/`                          | Operator-driven once per workspace, not per-slot           | `${WORKSPACE_ROOT}/.venv-workspace/` (above all slot dirs) | Yes — outside `.tabs/`                 |
| `node_modules/` (per frontend repo)         | `npm install` on first frontend operation                  | `<repo>/node_modules/` inside the slot worktree            | No                                     |
| `dist/`, `build/`, `__pycache__/`, `.next/` | Build commands                                             | Inside per-repo worktree                                   | No                                     |
| `data/` caches                              | First read of upstream data                                | Per-repo gitignored data dir                               | No                                     |

**Why on-demand**: 12 slots × 27 repos × ~500 MB of venv each = ~160 GB of duplicated venvs if eagerly built per slot.
On-demand keeps `.tabs/` at ~3-4 GB code-only. Verified 2026-05-20 on the EC2 VM (`13.113.200.22`): 12 slots
bootstrapped, 0 `.venv` directories present anywhere under `.tabs/`. Every workspace repo with a Python service has
`.venv` listed in `.gitignore` so accidental commits are blocked.

**Excluded from on-demand purge** (credentials stay where they are, NOT in slot worktrees):

- `~/.aws/credentials`, `~/.aws/config`
- `~/.config/gcloud/`, `~/.config/gh/`
- `~/.claude/.credentials.json`

**Composes with**:

- Phase 2 pre-spawn dirty-state gate (`agent-orchestrator/server/worktree_clean_check.py`): `git status --porcelain`
  already excludes gitignored content so on-demand artifacts don't trigger false dirty-state alarms
- Phase 3 `.agent-claim` ownership file: claim lives at `.tabs/<N>/.agent-claim` (slot root, above repos), never
  conflicts with per-repo build dirs

**Open follow-ups** (tracked in
[plans/active/agent_reliability_mitigations_2026_05_20.md](../../plans/active/agent_reliability_mitigations_2026_05_20.md)
§ Phase 5):

1. Wire automatic `uv sync` in `agent-orchestrator/server/tmux_spawn.py::spawn()` when worker role is spawned into a
   slot whose primary repo is a Python service (background-launch + log to dashboard)
2. Prune cron: scrub `.venv` / `node_modules` from slot worktrees that haven't been spawned-into in N days
   (configurable, default 7d)
3. Coord with Harsh: confirm his local fleet topology (per his 2026-05-20 screenshot — slots 1-5 PM-only main, 21-30
   workers code-only) becomes the workspace SSOT so both Ikenna's Mac + the VM align

## Pre-spawn branch-state + liveness-gated dirty resolution (Phase 4, 2026-06-01)

The orchestrator's spawn paths (`server.py::spawn_slot`, `autospawn._do_spawn`,
`worker_liveness._maybe_auto_respawn_stuck_slot` + `_do_auth_fail_respawn`) run two structural gates before a worker
lands, so a halted slot restarts on a **good working tree on the right branch** — not on inherited garbage. SSOT:
`agent-orchestrator/server/worktree_clean_check.py` +
`plans/active/orchestrator_autonomy_audit_remediation_2026_06_01.md` Phase 4.

**Dirty-state resolution (`resolve_dirty_state`) — in order:**

1. **FM3 restore generated artifacts** — `git restore -- <allowlist>` (playwright-report/blob-report/test-results),
   NEVER `git restore .`; re-check.
2. **FM2 wiped-index guard** — detect the `staged-D` + same-path-`??`-on-disk signature; `git reset --mixed HEAD` first;
   `commit_and_push_dirty_repos` REFUSES a pure mass-deletion (>20 files) / wiped index → outcome `quarantined` (never
   pushes a destructive delete as orphan WIP).
3. **FM8 liveness gate (the slot-isolation invariant)** — dirty content in YOUR slot worktree is almost always a
   previous session of _you_ that is now gone → **inherit it** (commit+push as `chore(orphan-wip)`). The discriminator
   is **LIVENESS, not slot-id identity**: a dead/absent/expired claim, or a claim owned by the very session being
   respawned → inherit; a DIFFERENT live tmux session owning a fresh `.agent-claim` → **PROTECT** (never stomp). Third
   LIVE signal (FM8 addendum): a dirty file with mtime < 120 s → a live interactive editor (operator/Cursor, no claim,
   no tmux) → protect. **Quarantine is never terminal** — a dead maker's WIP is always eventually inherited.

**FM8b slot-tagged stashes** — linked worktrees share one `.git`, so `git stash list` exposes every slot's stashes.
`stash_dirty_repos` tags `slot-<N>-orphan-<ts>` and `find_slot_stash_ref` only ever pops the stash matching THIS slot's
tag — never assumes `stash@{0}` is ours.

**Branch-state gate (`check_slot_branch_state`) — FM1/FM5/FM6/FM7:** per repo assert `HEAD == tab/<op>/<N>` (FM7: STOP
on detached/wrong-branch), repair a stale upstream → `origin/<base>` (FM1), FF when behind+clean (FM4), quarantine on
divergence (FM5). **FM6 per-repo base: every repo — INCLUDING agent-orchestrator — integrates via `live-defi-rollout`.**
Do NOT special-case agent-orchestrator to `main`: slot worktrees track `origin/live-defi-rollout` (server code ships
from LDR; `main` is only the dashboard-SPA deploy branch + CI gate), so a `main` base reads every slot as diverged — a
`main` override was removed from `scripts/dev/cron-branch-overrides.txt` 2026-05-24 for exactly this. The recovery /
auth-fail boot prompts inline the same ff-only-when-behind + divergence-STOP block (FM4/5) so a recovered session
self-verifies, no weaker than a cold autospawn.

## Anti-patterns

- **Don't** create ephemeral per-theme worktrees. Slot is durable; theme rotates.
- **Don't** reuse a slot for a new theme without running `--reset-slot` first. Yesterday's WIP leaks into today's plan.
- **Don't** name branches after themes (e.g. `tab/ikenna/writegate`). Branch is the slot identity: `tab/ikenna/3`.
  Theme-naming undoes the slot-vs-theme decoupling.
- **Don't** use `git add -A` / `git add .` inside a slot worktree just because foot-guns #1/#2 are unrepresentable
  cross-slot. Within-slot, sub-agents share the index — pre-commit check still required.
- **Don't** pre-build venvs across all slots on `setup-tab-worktrees.sh --init`. Eager build = ~160 GB duplication per
  fleet; on-demand keeps it ~3-4 GB code-only.

## Composes with

- [`plan-aware-merge-resolution.md`](plan-aware-merge-resolution.md) — protocol the slot master uses at rebase time.
- `cursor-configs/CLAUDE.md` § "Daily Work-Split Process" — operator orchestrator + daily work-split plan format.
- `cursor-configs/CLAUDE.md` § "The mandatory pre-commit check" — within-slot discipline (the cross-slot half is trimmed
  because foot-guns #1-#3 are unrepresentable).
- `plans/PLAN_FORMAT.md` § "Daily Work-Split Process" — slot↔theme table requirement.

## References

- Plan: [`plans/active/per_agent_worktrees_2026_05_10.md`](../../plans/archive/per_agent_worktrees_2026_05_10.md)
- Bootstrap script: [`scripts/dev/setup-tab-worktrees.sh`](../../scripts/dev/setup-tab-worktrees.sh)
- Teardown script: [`scripts/dev/teardown-tab-worktrees.sh`](../../scripts/dev/teardown-tab-worktrees.sh)
- Audit:
  [`plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md`](../../plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md)
  Block D3
