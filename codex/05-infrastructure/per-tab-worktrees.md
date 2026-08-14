---
doc_type: codex-ssot
title: Per-slot reference-clones — 3-tier isolation for parallel-agent flow
summary:
  "Path-B per-slot reference-clones (live since 2026-06-08; tab/<op>/N tab-branch model RETIRED): each slot is a `git
  clone --reference` with its OWN .git checked out on live-defi-rollout, objects shared via --reference. The one
  invariant — HEAD ancestor-or-equal of origin/live-defi-rollout. Covers bootstrap/setup recipe, FF-pull starvation
  watchdog, per-clone commit identity (slot+host in author NAME), merged-combination reconciliation on LDR push-reject,
  and liveness-gated dirty-WIP resolution."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, alerting-service, unified-trading-pm]
scope: [engineer]
tags: [infrastructure, quickmerge, scripts, orchestrator, reconciliation, self-healing]
related: [plans/active/worktree_ldr_unification_2026_06_08.md, plans/archive/per_agent_worktrees_2026_05_10.md]
created: 2026-05-10
authoritative_for: [per-slot reference-clone worktree model]
referenced_by:
  [
    /codex/05-infrastructure/claude-code-settings-symlink.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/plan-aware-merge-resolution.md,
    /codex/12-agent-workflow/harsh-laptop-migration-2026-05-20.md,
    /codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md,
    /codex/12-agent-workflow/orchestrator-safety-mechanisms.md,
  ]
owner: workspace-platform
last_reviewed: 2026-08-12
code_refs:
last_updated: 2026-08-12
related_codex: [/codex/05-infrastructure/plan-aware-merge-resolution.md, ../../cursor-configs/CLAUDE.md]
---

# Per-slot reference-clones — 3-tier isolation for parallel-agent flow

> **Model: Path-B reference-clones (live since 2026-06-08; the `tab/<op>/N` tab-branch model is RETIRED).** Each slot is
> a **`git clone --reference <workspace>/<repo> <url> .tabs/<N>/<repo>`** with its **OWN `.git`** (no shared refs/index,
> no ref races), shared object store via `--reference` (no disk blowup), each clone **independently checked out on
> `live-defi-rollout`**. Stay current with `git -C .tabs/<N>/<repo> pull --ff-only origin live-defi-rollout`; ship via
> `quickmerge --agent --files`. The ONE invariant to police: HEAD is ancestor-or-equal of `origin/live-defi-rollout`
> (`scripts/cicd/slot_drift_check.py`). Commit attribution is in the author NAME (`[slot-<N>·<host>]`), independent of
> branch. SSOT for the model: `plans/active/worktree_ldr_unification_2026_06_08.md`.
>
> **If you encounter `tab/<op>/N` branches, `tab-mirror`, upstream re-pointing, `--force-with-lease`-to-a-tab-branch, or
> `extensions.worktreeConfig` per-worktree identity anywhere (a doc, a script, a boot prompt), it is STALE** — Path-B
> has none of these. Report or fix it; do not act on it. (The filename stays `per-tab-worktrees.md` because many docs
> point to it by that path; the model it describes is per-slot clones.)

**TL;DR.** Each operator (Ikenna / Harsh) runs N parallel agent "slots." Each slot is its own clone at
`.tabs/<N>/<repo>/` checked out on `live-defi-rollout`. Cross-slot races on `.git/index` + working tree are
unrepresentable by construction (separate clones). Contention moves to **LDR push-time** (rebase-on-reject, handled by
quickmerge STAGE 0.4). Slot is the durable identity; theme (writegate / cefi-master / defi / etc.) is the daily
assignment via the orchestrator dashboard (LEDGER slot↔theme table is the offline fallback).

## Slot-number → role (main vs worker)

The slot number decides whether a slot runs a **main** agent or a **worker** — `1..MAIN_SLOT_MAX` (default 20) are
mains, `> MAIN_SLOT_MAX` are workers. That is the only meaning the number carries now: **there is no branch prefix**
(the old `tab/<main-prefix>/<N>` / `tab/<worker-prefix>/<N>` scheme is retired — every slot, main or worker, is a clone
on `live-defi-rollout`). `setup-tab-worktrees.sh` reads `MAIN_SLOT_MAX` only to label the slot's role in `--list`; the
working branch is always `live-defi-rollout`.

## The 3-tier hierarchy

```
Tier 1 — Operator (Ikenna ⊥ Harsh)
    Physical machine boundary. No shared local state.
    Reconciliation: fetch + push via origin/live-defi-rollout. Cross-side
    coordination via workspace-shared plans/active/_agent_pings.md.

Tier 2 — Slot (within one operator)              ←── THIS DOC'S SCOPE
    Per-slot `git clone --reference` at .tabs/<N>/<repo>/ checked out on
    live-defi-rollout (own .git, shared object store). Slot count is
    operator-declared at --init. Slot is durable identity; theme is daily.
    Reconciliation: push per shippable unit; on LDR push-reject, rebase
    onto origin/live-defi-rollout keeping the merged combination (below).

Tier 3 — Sub-agent (within one slot)
    Sub-agents SHARE the slot clone's working tree + index. Master agent
    partitions fan-out to non-overlapping repos/dirs so within-slot
    collisions are rare. Master is the in-session reconciler when they happen.
```

## Bootstrap

One-time per operator, runs on the operator's workstation (also used on every VM worker host):

```bash
# Provision 8 slots for this operator (typical; pick N for peak parallel count).
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --init --slots 8

# Add a 9th slot later if peak grows.
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --add-slot 9

# Between themes on the same slot — verify clean + fast-forward to origin/live-defi-rollout.
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot 3

# List configured slots + their current branch heads.
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --list

# Rare: shrink fleet (remove a slot — only when really retiring it).
bash unified-trading-pm/scripts/dev/teardown-tab-worktrees.sh --slot 9
```

After `--init`, every active repo in `workspace-manifest.json` has a reference-clone at `.tabs/<N>/<repo>/` for each
slot, checked out on `live-defi-rollout`. The operator opens Cursor at `.tabs/<N>/` and the slot is isolated.

## Operator setup recipe (paste-ready)

This section is the operator runbook — paste-ready commands + verification probes for each step. Works identically for
Ikenna and Harsh; the only operator-specific detail is the choice of slot count N (see step 1).

> **Precondition.** Workspace already bootstrapped via
> [`scripts/workspace/workspace-bootstrap.sh`](../../scripts/workspace/workspace-bootstrap.sh) — i.e. all active sibling
> repos are cloned under `$WORKSPACE_ROOT`, `.venv-workspace` exists, and `git status` is clean across every repo on
> `live-defi-rollout`. Confirm with:
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
> If anything's dirty, commit/push or stash before running `--init`. Each slot clone checks out
> `origin/live-defi-rollout`; uncommitted state in the main clone does NOT propagate into the new slots, but it's good
> hygiene to start clean.

### Step 1 — pick N (slot count)

Rule of thumb: **N = peak concurrent Cursor / Claude Code slots you expect to run**, +1-2 headroom for surge days.

| Operator | Recommended N | Rationale                                                             |
| -------- | ------------- | --------------------------------------------------------------------- |
| Ikenna   | 8             | Cross-cutting design + governance; typically 5-6 active slots daily.  |
| Harsh    | 6-8           | Implementation-from-spec; slot count varies by daily work-split size. |

You can grow later with `--add-slot <N>`. Don't undersize — an empty slot clone is cheap (objects are shared with the
main clone via `--reference`, so only refs + working tree cost disk). Oversizing costs little operationally.

### Step 2 — run `--init`

```bash
cd "$WORKSPACE_ROOT"
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --init --slots 8
```

`--operator <name>` / `--init` reads the operator handle for the **commit-identity NAME** (`[slot-<N>·<host>]`) and the
per-machine `.worktree-identity.conf`; it does NOT create any branch (every slot checks out `live-defi-rollout`).

**Expected output** (excerpt — one block per slot × active repos):

```
[setup-tab-worktrees] Initialising 8 slots for operator 'harsh' under /Users/harsh/Code/.../.tabs/
[setup-tab-worktrees] Provisioning slot 1 (clone on live-defi-rollout) ...
[setup-tab-worktrees]   ENV  slot 1 .envrc written (PREK_CACHE_DIR=.../prek)
[setup-tab-worktrees]   CLONE  alerting-service → /Users/.../.tabs/1/alerting-service (live-defi-rollout)
...
[setup-tab-worktrees]   SKIP user-management-ui (no sibling clone at ...)
[setup-tab-worktrees] Done. 8 slots ready. Next: assign themes via the daily work-split + orchestrator dashboard.
```

Runtime: a reference-clone is network-light (objects come from the sibling via `--reference`); a few minutes total for 8
slots × active repos.

### Step 3 — verification probes

After `--init` returns, run these in order:

```bash
# Probe 1 — all N slots provisioned with one clone per active repo on live-defi-rollout.
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --list
# Expected: "slot 1: branch=live-defi-rollout head=<sha>" through "slot N: ... head=<sha>"
# All HEADs should equal the current live-defi-rollout tip.

# Probe 2 — each slot repo is a SEPARATE clone (its .git is a directory, not a worktree gitfile).
for n in $(seq 1 8); do
  f=".tabs/$n/unified-trading-pm/.git"
  [ -d "$f" ] && echo "slot $n: separate clone ✓" || echo "slot $n: NOT a separate clone ✗ ($f)"
done

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

If any probe fails, re-run `--init` (idempotent) or `--reset-slot <N>` for the affected slot.

### Step 4 — assign themes (orchestrator dashboard; LEDGER fallback)

The agent-orchestrator dashboard is the authoritative slot↔theme surface. The offline fallback is the LEDGER
`## Today's slot assignments` table; the daily work-split plan (`plans/active/work_split_<YYYY_MM_DD>_<operator>.md`) is
the authoritative source the LEDGER mirrors.

```markdown
## Today's slot assignments

**Slot count:** 6 (grow with `--add-slot <N>` if peak parallel work exceeds).

| Slot | Theme                    | Plan-of-record / scope                                         |
| ---- | ------------------------ | -------------------------------------------------------------- |
| 1    | main orchestrator        | (this LEDGER) — direction-setting + Q&A dispatch + ping triage |
| 2    | mtds prediction smoke    | plans/active/predictions_master.md                             |
| 3    | features-onchain Phase 5 | plans/active/features_repo_consolidation_2026_05_08.md         |
```

### Step 5 — open Cursor at a slot

For each slot you want to spawn, two equivalent options — pick the one matching how you like the file tree rendered:

```bash
# Option A — Open as folder (single-root; flat file tree of all repos as subdirs).
code "$WORKSPACE_ROOT/.tabs/<N>"

# Option B — Open as multi-root workspace (named labels per repo, custom emojis, folder grouping).
# The .code-workspace file is auto-copied into each slot by --init / --add-slot.
code "$WORKSPACE_ROOT/.tabs/<N>/unified-trading-system-repos.code-workspace"

# OR for Claude Code CLI in a terminal:
cd "$WORKSPACE_ROOT/.tabs/<N>" && claude
```

Both options produce identical isolation — the window's CWD is rooted at the slot, all Git operations from any terminal
in that window hit the slot clone's `.git`. The slot's `.envrc` loads `PREK_CACHE_DIR` + `SLOT_NUMBER` if you have
direnv installed (otherwise source it manually).

**Verify CWD before pasting the spawn prompt.** In a Cursor terminal of the new window:

```bash
pwd                                                              # → .../.tabs/<N>
git -C unified-trading-pm rev-parse --abbrev-ref HEAD            # → live-defi-rollout
```

If `pwd` returns the main workspace root, you opened the wrong directory.

### `.code-workspace` path-style contract (canonical vs slot copies)

Two distinct consumers read the multi-root workspace file, and they need **different `folders[].path` styles** — this is
deliberate, not drift:

| Consumer                 | File                                                                                    | `folders[].path` style         | Why                                                                                                            |
| ------------------------ | --------------------------------------------------------------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| Main-clone view (root)   | repos-root symlink → `.cursor/workspace-configs/` (dir symlink → the tracked canonical) | `../../<repo>` + `../../` root | Canonical lives 2 levels deep under `unified-trading-pm/cursor-configs/`; `../../` resolves to the repos root. |
| Slot copies (`.tabs/N/`) | `.tabs/N/unified-trading-system-repos.code-workspace`                                   | bare `<repo>` + `.` root       | Slot file is 1 level deep; bare names resolve to the slot's own `.tabs/N/<repo>`.                              |

**Canonical SSOT** = `unified-trading-pm/cursor-configs/unified-trading-system-repos.code-workspace` (git-tracked). The
repos-root `unified-trading-system-repos.code-workspace` is a symlink whose chain resolves to it.

`copy_workspace_file()` (in `setup-tab-worktrees.sh`) does **not** plain-`cp` the canonical into a slot — that would
carry the `../../<repo>` paths verbatim, which from `.tabs/N/` resolve to the **main** clone (a silent footgun: the dirs
exist, so no error, but the slot's SCM panel points at the main checkout). Instead it rewrites paths to bare-relative on
copy (`../../<repo>` → `<repo>`, `../../` → `.`).

A blocking QG step (`scripts/quality_gates/check_workspace_code_workspace_drift.py`) asserts the canonical `folders[]`
(minus the workspace-root entry) == the active+scaffolded repo set in `workspace-manifest.json`, and that no listed path
is a known archived/consolidated repo. SSOT for the incident + remediation:
`plans/active/workspace_config_drift_remediation_2026_06_01.md`.

### Troubleshooting

| Symptom                                                                                                                                                                                                                                                                                                                | Likely cause                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Fix                                                                                                                                                                                                                                                                                                                                                                        |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--init` reports `SKIP <repo>` for an unexpected repo                                                                                                                                                                                                                                                                  | Repo not cloned as sibling under `$WORKSPACE_ROOT`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Re-run `bash scripts/workspace/workspace-bootstrap.sh --skip-fresh` to clone missing repos; then re-run `--init` (idempotent).                                                                                                                                                                                                                                             |
| `--reset-slot <N>` aborts with "dirty file(s)" + an unfamiliar file                                                                                                                                                                                                                                                    | Foreign-agent WIP OR runtime artifact (e.g. `.local-dev-cache/`, `catboost_info/`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Per CLAUDE.md "Two teammates" rule: do NOT `git checkout --` foreign WIP. For runtime artifacts: discard with `git checkout --`. For WIP: commit/stash.                                                                                                                                                                                                                    |
| prek auto-restore wipes your edits mid-session                                                                                                                                                                                                                                                                         | Per-slot `PREK_CACHE_DIR` not exported (direnv not loading `.envrc`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Manually: `source $WORKSPACE_ROOT/.tabs/<N>/.envrc` before any commit, OR install direnv + run `direnv allow`.                                                                                                                                                                                                                                                             |
| A slot clone silently falls dozens/hundreds of commits behind `origin/live-defi-rollout` even though the FF-pull cron runs                                                                                                                                                                                             | **FF-pull starvation**: an uncommitted local edit COLLIDES with an incoming changed file, so every `git pull --ff-only` aborts. Both crons treat "couldn't FF" as a benign skip, so nothing alerts.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | The **FF-pull starvation watchdog** pages on this (below): a `FF-PULL STARVATION — slot N / repo` message lands in the slot inbox naming the colliding files. Remediate: `git stash push -- <colliding paths> && git pull --ff-only && (commit-or-restore the stash)`. The colliding file is usually foreign WIP — **stash-by-name, do NOT discard**.                      |
| `git pull` / `git fetch --tags` rejected with `! [rejected] vX.Y.Z (would clobber existing tag)` (commonly after a 1.0.0 graduation)                                                                                                                                                                                   | **Stale local release tag**: a local tag points at a different object than the remote's same-named tag, re-created by **semver-agent** (the SSOT for version tags).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | **`git fetch origin --tags --force`** — a **local-only** ref update pointing the stale local tags at the canonical remote objects. No commits lost, nothing pushed. Then `git pull --ff-only`. **Never** force-push local tags to remote (can revert a semver bump). `slot-cron-ff-pull.sh` fetches `--tags --force`, so cron-driven hosts auto-heal between manual pulls. |
| A slot clone's `git fsck` FAILS with `invalid sha1 pointer` / `invalid reflog entry` for an object "missing" from the store (VM git-health guard alerts "genuine missing/broken objects")                                                                                                                              | **Reference-clone prune hazard** (below): the base clone's default auto-gc pruned an unreachable object that a slot's stale ref/reflog still points at. The base's gc has no knowledge of slot refs.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | **Prevent:** `git -C <base> config gc.pruneExpire never` on every base (asserted by `setup-tab-worktrees.sh` at clone time + `fleet-git-health-guard.sh` every 15 min). **Repair a broken slot:** reset the stale local ref off the missing object (`git update-ref refs/heads/<b> origin/<b>`) + `git reflog expire --stale-fix --all`, then re-fsck. See § below.        |
| A repo's test/QG run fails with `ImportError: cannot import name 'X'` (or similar) while importing/probing a **sibling** repo's code (e.g. unified-trading-pm's capability-schema tests reading strategy-service's live engine registry) — even though that sibling's own quality-gates is green on its current branch | **Stale sibling `.venv` on THIS slot**: each slot's sibling clones have fully independent `.venv`s (3-tier isolation above). A fleet-wide dependency bump landing in the sibling's `pyproject.toml`/`uv.lock` does **not** retroactively refresh any slot's already-built venv — only the NEXT `uv sync` in that specific clone does. Confirmed 2026-07-31: `strategy-service/.venv` on slot 2 had `fastapi==0.135.1` installed while its own `pyproject.toml`/`uv.lock` already required `0.140.7` (a fleet-wide CVE-remediation bump shipped 2026-07-28, `plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md`) — a cross-repo probe in unified-trading-pm's tests hit `ImportError: cannot import name 'iter_route_contexts' from 'fastapi.routing'` purely from the stale venv. | **Self-service first, don't escalate**: `cd <sibling-repo> && uv sync`, then verify — e.g. `.venv/bin/python -c "import <pkg>; print(<pkg>.__version__)"` should match the version pinned in that repo's own `uv.lock`. No code/pyproject change needed; this is a local environment refresh, not a dependency-resolution bug.                                             |

| Repeated `index.lock` contention, an edit needing recovery from an autostash TWICE, or a commit landing under the
WRONG operator's identity — even though Path-B's separate clones make CROSS-slot collisions unrepresentable |
**Interactive-session slot collision** — two live sessions sharing ONE slot's `.git` (see § below) | **Prevention**:
hold uncommitted work in a private `git worktree` via `scripts/dev/ship-from-worktree.sh setup`, not the shared checkout
(§ below). **Detection**: `SessionStart` collision hook (WARN-only) + `.agent-claim` heartbeat. |

### Interactive-session slot collision — a distinct failure mode Path-B's clones do NOT solve

AO-dispatched workers get programmatic slot allocation; an INTERACTIVE session (a human opening a terminal/IDE tab) has
none — the operator just `cd`s into whichever `.tabs/N` they have open, and nothing prevented a different live session
from already occupying it. Multiple `claude` processes (potentially different operators) then share ONE slot's single
`.git` — one index, one `HEAD`, one set of refs, and one `user.name`/`user.email` (§ "Commit attribution" below assumes
one live session per slot — this failure mode breaks that premise). Confirmed live 2026-08-01: up to 6 concurrent
`claude` processes on one slot, 3 collisions in ~15 min, one commit mis-attributed to the wrong operator despite correct
content. Full incident:
`plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md`.

**Detection (WARN, never hard-block — 2026-08-08 operator ruling): a live heartbeat on `.agent-claim`**
(`slot-git-status-report.sh`'s `refresh_agent_claim_heartbeat()`) distinguishes "claimed" from "claimed-and-alive"; a
`SessionStart` hook (`cursor-configs/hooks/session-start-collision-check.sh`) checks that heartbeat plus a live-process
cwd scan and warns (non-blocking) naming the live occupant.

**Signal 2's cwd scan was silently blind on macOS (fixed 2026-08-11).** It originally read ONLY `/proc/<pid>/cwd` +
`/proc/<pid>/status` — Linux-only paths. This operator's own laptop (Darwin — the host every measured instance of this
incident, including the 2026-08-11 recurrence below, actually happened on) has no `/proc` at all, so every read silently
failed and `foreign_count` stayed 0 regardless of how many peer sessions were actually live: the signal never once fired
on the platform it exists to protect, and nothing said so. Confirmed by direct reproduction: a simulated peer process
(cwd inside a fake slot dir, argv0 renamed to match `pgrep -f claude`) produced ZERO warning from the unpatched hook and
the correct warning after the fix, on the identical input. Fixed by adding a `ps`/`lsof` fallback (`_ppid_of` /
`_cwd_of` helpers) that only engages when `/proc` is absent — Linux behavior is unchanged. This is a
detection-completeness fix, not a severity change: still WARN-only, still never blocks. Regression coverage:
`tests/test_session_start_collision_check.bats` (10/10).

**2026-08-11 recurrence — the mitigation that actually worked was to stop sharing the checkout, not to detect harder.**
In slot 4, AFTER the quarantine-guard fix that closed the specific call-site bug behind the earlier losses
(`pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`), a peer session's own reconcile still reverted a
DIFFERENT session's tracked edits to HEAD twice in ~30 minutes — `git status` clean, content recoverable only from a
`pre-reconcile quarantine` stash by path. Neither detection signal above prevented it (WARN-only by design; the
`.agent-claim` heartbeat is best-effort and an interactive session commonly has none at all, per the header comment on
the hook itself). The only thing that reliably worked was to stop holding uncommitted work in the shared checkout at all
— a private linked `git worktree`, which by construction has its own working tree, index, and HEAD, so a peer session's
stash/reconcile machinery (which operates entirely within the SHARED `.git`'s index and working tree) cannot touch it.
See § "What worktree isolation does NOT cover" above for the two surfaces (`refs/stash`, `.git/COMMIT_EDITMSG`) a
worktree does NOT protect against — this mitigation is for the working-tree/index/HEAD class of loss specifically, which
is what both 2026-08-11 losses were.

**`scripts/dev/ship-from-worktree.sh` formalizes this as a real, tested tool** rather than a hand-derived emergency
manoeuvre every session re-invents. `setup` fetches, creates a detached linked worktree named after the CALLING repo
(never a hardcoded literal — resolved via `git rev-parse --show-toplevel`, so it tracks whatever the F7-adjacent P1
around quickmerge's own directory-name assumptions eventually settles on, rather than needing a matching fix here),
symlinks sibling repos in for a subsequent `quickmerge.sh`'s STAGE 1.5 dependency alignment, and optionally
(`--with- venv`) provisions a Python venv via the SAME shared per-repo cache (`QM_ISO_VENV_CACHE`, default
`$HOME/.cache/qm-iso-venv/<repo>`) that `quickmerge.sh`'s own isolated mode already uses — deliberately NEVER a symlink
to the caller's real `.venv`: both `scripts/quickmerge.sh`'s own header comment and this section's source issue doc's
"Lessons carried forward" record that doing so let `uv sync --frozen` PRUNE packages out of the operator's live
environment (measured 2026-08-10). `cleanup <dest>` removes the worktree via `git worktree remove --force` (git's own
removal, never a raw `rm -rf`, which a guardrail hook on this host blocks anyway) resolved against the ORIGIN repo (via
`git rev-parse --git-common-dir` from inside the worktree, so cleanup works regardless of where the caller currently
is), prunes worktree admin state, unlinks sibling symlinks by name, and `rmdir`s the parent — never forced, so anything
unexpectedly left behind fails loudly instead of being deleted. Ship from inside it exactly as from the shared checkout
— `safe-doc-push.sh` / `quickmerge.sh` both run fine from within a worktree (they build their OWN, shorter- lived
isolation worktree internally regardless of whether the caller is already in one). Tests:
`tests/test_ship_from_worktree.bats` (16/16, hermetic — builds its own scratch origin + slot clone, never touches a real
`.tabs/<N>`).

**Open question, not yet resolved: should detection escalate past WARN?** Two options were assessed (2026-08-11); no
change beyond the detection-completeness fix above has shipped, pending an operator decision:

- **Option A — keep SessionStart WARN-only; strengthen the message to name `ship-from-worktree.sh` as the concrete
  mitigation [RECOMMENDED as the immediate default].** A true hard block is not mechanically available at this hook
  event regardless of preference — `SessionStart` is documented as non-blocking in Claude Code REGARDLESS of exit code
  (see the hook's own header comment), so "harder than WARN" cannot mean "refuse the session" without moving to a
  different hook event entirely. The operator's 2026-08-08 ruling (WARN, never hard-block) was made for exactly the
  reason still true today: an operator may deliberately run two sessions in one slot for a review pass, and a session
  that refuses to start with no per-invocation override is a worse cost than the collision it prevents.
- **Option B — a narrower `PreToolUse` guard scoped to the actual risky commands** (`git commit` / `quickmerge.sh` /
  `safe-doc-push.sh`), re-checking the same two liveness signals at the MOMENT of the mutating call rather than only at
  session start, with a clean, cheap opt-out for anything invoked from inside a `ship-from-worktree.sh` worktree (which
  is safe by construction and must never be blocked). This targets the actual moment of loss more precisely than a
  session-start check — the 2026-08-11 recurrence happened well after both sessions had already started, when a PEER
  session's reconcile fired mid-session, not at either session's launch. What it would break if adopted carelessly: a
  second session doing purely read-only/planning work with no git-mutating intent would still hit friction on its first
  commit attempt; an AO-spawned tmux pane transiently visible during a worker handoff in the SAME slot could false-
  positive; and unlike a session-start warning (skippable by just continuing), a `PreToolUse` block genuinely stops the
  next action, so its false-positive cost is now paid mid-task rather than at a natural pause point.

Recorded here rather than decided unilaterally — a change to hook-blocking severity is a workflow-wide policy call, not
a same-turn code fix, per the escalation-to-operator convention (present options, mark a recommendation, let the
operator choose).

### Reference-clone prune hazard (codified 2026-07-13)

**Failure mode.** Every slot is a `git clone --reference <base>` sharing the base's object store via
`objects/info/alternates`. The base clone runs git's **default** auto-gc (`gc.auto` unset → fires at 6700 loose objects;
`gc.pruneExpire` unset → `2.weeks.ago`). Auto-gc prunes objects unreachable **from the base's own refs** — it has zero
knowledge of the N slot clones referencing its object store. So when the base prunes an object a slot's stale local
ref/reflog still points at (typically the vestigial `main` branch — slots work on `live-defi-rollout`), that slot's
`git fsck --connectivity-only` FAILS (`invalid sha1 pointer` on the ref / `invalid reflog entry`), which the VM
git-health guard reports as "genuine missing/broken objects". This is git's documented `--reference` hazard (see the
`git clone` man page). Reference incidents: instruments-service (2026-07-09→13) and deployment-api (2026-07-13), both on
`agent-orchestrator-vm-1`.

**The durable fix (three layers).** Never let a base that backs `--reference` clones DELETE objects:

1. **At clone time** — `setup-tab-worktrees.sh` sets `gc.pruneExpire=never` on the sibling base whenever it references
   it (idempotent, asserted every `--init` / `--add-slot`), so a newly-provisioned base is born protected.
2. **Continuously, every host (primary)** — `slot-cron-ff-pull.sh` asserts `gc.pruneExpire=never` on every main clone in
   its `prefetch_main_clones()` loop. This is the fleet-wide guarantee: the cron runs **every 5 min on every
   slot-hosting host** (operator laptops + every VM) and **self-pulls its own code from `origin/live-defi-rollout`**, so
   the protection reaches the whole fleet with no manual deploy and heals pre-existing bases + any config drift within
   one tick. It is asserted in the same loop that fetches (the fetch is what feeds the auto-gc trigger), so the disarm
   tracks the trigger exactly.
3. **Continuously, orchestrator VM (belt-and-suspenders)** — `fleet-git-health-guard.sh` also asserts it on every main
   clone it scans (every 15 min), and remains the DETECTOR/repair for any clone that corrupted before the protection
   landed.

`gc.pruneExpire=never` keeps auto-gc's repack (loose-object → pack, the performance win) and drops only the destructive
prune, so slots never lose a referenced object. To reclaim unreachable objects on a base, run `git gc --prune=now`
**only when no slots reference it** (e.g. during a full slot teardown).

**Repairing an already-corrupt slot** (the pruned object is gone — nothing to recover): reset the stale local ref off
the missing object and expire the dangling reflog entries, then re-fsck:

```bash
# for a slot whose refs/heads/<b> tip object is MISSING (skip the checked-out branch):
git -C <slot> update-ref refs/heads/<b> refs/remotes/origin/<b>   # or origin/live-defi-rollout
git -C <slot> reflog expire --stale-fix --all                     # drops reflog entries to broken objects
git -C <slot> fsck --connectivity-only --no-progress              # verify CLEAN
```

The working tree + the checked-out `live-defi-rollout` branch are untouched — only the vestigial ref/reflog is repaired.

### Cron self-pull + Path-B per-slot ref refresh (codified 2026-06-12)

**Self-pull (every machine-run PM cron).** Each cron's crontab LINE — the immutable anchor — refreshes its OWN script
from `origin/live-defi-rollout` before running it, so a stale/dirty root PM clone never starves the cron of current code
(the chicken-and-egg that froze clones hundreds of commits behind). The snippet is emitted by the shared helper
`scripts/dev/cron-self-pull-lib.sh` (`emit_cron_self_pull <pm_dir> <branch> <script> [data…]`). It is **syntax-gated
(H6)**: the candidate is streamed via `git show` to a temp, `bash -n`'d, and only `mv`+`chmod 755`'d into place if it
parses — so one bad commit can never propagate fleet-wide and stop the cron. Three machine crons self-pull:
`slot-cron-ff-pull` (+ its `cron-branch-overrides.txt` data sibling), `slot-host-symmetry-verify`, and
`slot-git-status-report`. All installed/updated by `install-slot-cron-ff-pull.sh` (run once per host from the ROOT
clone, never a slot — the Phase-D guard refuses a `.tabs/` cwd).

**Cmp-guarded writes + managed-file heal (codified 2026-07-14).** The original self-pull overwrote its files
UNCONDITIONALLY every tick, which on a behind root PM clone left them permanently dirty-vs-HEAD — and that dirt tripped
`ff_one()`'s own `[skip:dirty]`, starving the clone of the very FF that would have healed it (self-inflicted
chicken-and-egg; reference incident 2026-07-14: root PM clone 1138 commits behind with the self-pull artifact as the
only tracked dirt). Two-sided fix, both halves must stay: (1) `emit_cron_self_pull` writes ONLY when the working copy
differs from `origin/<branch>` content (`git show | cmp -s` guard), and data siblings are written via cmp-guarded
`git show`→temp→`mv` — **never `git checkout origin/<branch> -- <file>`, which also writes the INDEX and leaves STAGED
dirt**; (2) `ff_one()` carries the matching heal — a managed cron file that is dirty but **byte-identical to
`origin/<int_branch>`** is restored to HEAD (`git checkout HEAD -- <file>`, clearing index + worktree) so the FF
proceeds and brings HEAD forward to that same content. The heal ships inside `slot-cron-ff-pull.sh` itself, so it
reaches hosts still running an older unguarded crontab line without a reinstall; re-running
`install-slot-cron-ff-pull.sh` upgrades the crontab line to the guarded emission. Local edits to the four managed cron
files remain LDR-authoritative and are still overwritten by design — ship changes to them via PR→LDR, never by editing a
clone in place.

**Per-uid log paths — a root-owned log must never block the operator cron (codified 2026-06-23).** All three crons
redirect to `${XDG_RUNTIME_DIR:-/tmp}/<name>.$(id -u).log` (uid-suffixed), matching the already-per-uid lock
(`slot-cron-ff-pull.$(id -u).lock`). **Why:** the lock was per-uid but the LOG was a shared `/tmp/slot-cron-ff-pull.log`
— a one-off run as a DIFFERENT uid (e.g. a `sudo`/root invocation) created a root-owned log, after which the ubuntu
cron's `>>` redirect silently failed every tick and the FF-pull stopped firing (reference incident: a 6-day silent
outage to 2026-06-22 — clones drifted while the host looked healthy). Per-uid logs make the redirect collision
impossible, so a **freshly-bootstrapped VM gets a working cron straight away** (this is the install default, no manual
step). **Opt-in `--include-main-clones`:** the `--all-slots` sweep covers `.tabs/<N>/` clones; a host that does its work
in the ROOT/main clones (an interactive dispatch host, not a `.tabs/` worker) passes `--include-main-clones` at install
to also FF-pull the root clones on the standard `3,8,13,…` schedule. Standard data/paper/worker VMs work in `.tabs/` and
need nothing extra.

**Path-B per-slot ref refresh.** Under Path-B every slot is an independent `git clone --reference` with its OWN refs
(objects shared via `objects/info/alternates`, refs NOT shared). `slot-cron-ff-pull.sh` PHASE-1 prefetch updates only
the main-workspace clones' refs, so PHASE 2 MUST refresh each slot's `origin/<branch>` — a LOCAL ref-copy from the
`--reference` clone (objects already shared → no network), with a network-fetch fallback
(`_refresh_independent_clone_ref`). Without it a slot compares HEAD against a stale local ref and silently falls behind
(observed up to +149 commits; fixed 2026-06-12).

### FF-pull starvation watchdog (codified 2026-06-01)

**Failure mode.** A slot clone sits N commits behind `origin/live-defi-rollout` with the remote configured correctly,
but `slot-cron-ff-pull.sh` silently no-ops every run because an **uncommitted local edit collides with an incoming
changed file**, so every `git pull --ff-only` aborts. Both crons (`slot-cron-ff-pull.sh`, `slot-git-status-report.sh`)
historically treated "couldn't FF" as a benign skip — nothing alerted (reference incident: slot-5 `unified-trading-pm`
963 behind, 2026-06-01).

**Actor vs detector.** `slot-cron-ff-pull.sh` stays the **actor** (it does the FF). `slot-git-status-report.sh` (which
already walks each repo's ahead/behind + dirty state for the dashboard, every 5 min) is the **detector/alerter**. It
shells out to `scripts/dev/ff-starvation-detect.sh` per repo and, on a positive detection, POSTs a `FF-PULL STARVATION`
ping to the slot's message inbox (`/api/slots/<N>/message`, `from_role: main`). The watchdog does **not** auto-resolve
the collision — that needs the stash-by-name + adjudicate judgment from the Two-teammates HARD RULE.

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
set does not block `--ff-only`. **De-duplication:** one ping per (slot, repo) starvation **episode** — a marker under
`.tabs/.ff-starve-state/` is set on first ping and cleared the moment the repo is no longer starved.

**Tunables (env):** `FF_STARVE_WATCHDOG` (default `1`; set `0` to disable), `FF_STARVE_COMMIT_THRESHOLD` (default `25`),
`FF_STARVE_AGE_HOURS` (default `6`). **Tests:** `tests/test_ff_starvation_detect.bats`.

## Slot is durable; theme is daily

The mapping of slot ↔ theme is daily-updated and lives authoritatively on the **agent-orchestrator dashboard**, with the
operator LEDGER `## Today's slot assignments` table as the offline fallback (forward index that fresh slot agents read
on bootstrap), mirroring the day's work-split plan (`plans/active/work_split_<YYYY_MM_DD>_<operator>.md`).

Three benefits of fixed slots over ephemeral spin-ups:

1. **Cursor extension state caches.** TS server warmup + indexing + watcher setup is 30-90s per repo × repos × N slots.
   Ephemeral spin-ups burn 30+ min/day of bootstrap; persistent slots: one-time cost.
2. **Cross-day workstreams continue cleanly.** Writegate spans weeks; cefi-master spans months. Same slot the whole
   time.
3. **Slot↔theme is the operator's load-balancer**, not a clone property. Decoupling lets the operator reshuffle themes
   daily without touching filesystem state.

## Slot-reset discipline (between themes)

When a slot's theme changes (typically morning, when the daily work-split reassigns):

```bash
# Step 1 — operator commits / pushes / discards any leftover WIP in the slot.
# Step 2 — reset the slot:
bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot <N>
# → Verifies every repo's clone clean (aborts with file list if dirty)
# → Fetches origin + fast-forwards each clone to origin/live-defi-rollout
# → Truncates <side>_orchestrator/pings/slot_<N>.md to a fresh stub (commits with [reset-slot] tag)
# → Slot is ready for the new theme.
```

The script **aborts on dirty state** rather than silently resetting over it. If aborted: commit, stash, or
`git checkout --` per-file (only for tracked runtime artifacts that regenerate naturally — never for foreign agents' WIP
per the CLAUDE.md "Two teammates" rule). Then re-run `--reset-slot`.

**For same-theme continuations** (slot stays on the same plan across sessions), do NOT run `--reset-slot`. Use `/clear`
in the Claude Code session to clear conversation context; the ping file retains day-context. To bound growth within a
multi-day same-theme run, call the read-time rollup helper at slot boot:

```bash
python3 unified-trading-pm/scripts/agents/rollup_resolved_pings.py \
    unified-trading-pm/<side>_orchestrator/pings/slot_<N>.md
```

This rolls up entries that are both ✅ DONE/RESOLVED and older than 24h into a `## Prior context (rolled)` section. It
is triggered at read-time (NOT by the script), to avoid racing with concurrent append-writes from sub-agents.

## The model — Path-B reference-clones (mechanism)

Each slot is `git clone --reference <workspace>/<repo> <url> .tabs/<N>/<repo>`: an **independent clone** that shares
`.git/objects` with the operator's primary clone via `--reference` (objects deduplicated → no disk blowup) but has its
**own refs, index, and working tree** (no ref races, no shared-index collisions). Each clone is checked out on
`live-defi-rollout` directly. There is no per-slot branch, no `tab-mirror`, no upstream to re-point — the clone's
upstream is `origin/live-defi-rollout` by construction.

**Why Path-B (the tab-branch model was retired 2026-06-08):** the tab branch was never an architectural choice — only a
workaround for git's "can't check out the same branch in two worktrees of one clone" constraint. The real isolation is
worktree-level (separate index/working tree). Separate clones drop the entire **sync tax**: `tab-mirror-to-ldr.yml`
(deleted fleet-wide), the tab-rebase/upstream self-heal in `slot-cron-ff-pull.sh`, and the diverged-tab recovery class.
Contention moves to **LDR push-time** (rebase-on-reject), already handled by quickmerge STAGE 0.4.

### Ship scripts run isolated on a DETACHED HEAD and push a refspec (codified 2026-08-10)

That same "can't check out one branch in two worktrees of a clone" constraint governs the **ship scripts' own** isolated
mode, and it is not optional: an isolated worktree of a slot clone can never `git checkout live-defi-rollout`, because
the clone itself already holds it. Both `safe-doc-push.sh` and `quickmerge.sh` therefore:

1. create the throwaway worktree with **`git worktree add --detach`**, and **stay detached** — no branch checkout at any
   later stage; and
2. push an **explicit refspec** — `git push origin "HEAD:refs/heads/<branch>"`, never `git push -u origin <branch>`.

Step 2 is load-bearing, not stylistic. From a detached HEAD, `-u origin <branch>` pushes the **shared clone's**
`refs/heads/<branch>` — a stale ref that does not contain the commit just made — and can **exit 0 having shipped none of
your work**. A silent no-op ship is worse than a failure, so the refspec form is required.

`safe-doc-push.sh` was built this way; `quickmerge.sh` was not, and its isolated mode consequently died on
`fatal: '<branch>' is already used by worktree at '<main clone>'` for every ship until 2026-08-10
(`unified-trading-pm@dad266ff61`, regression tests in `/tests/test_quickmerge_isolated_branch_collision.bats`). The
practical cost was indirect: callers fell back to `--no-isolated`, which is precisely the shared-checkout mode where a
peer's pull/rebase cycle can revert your uncommitted work mid-ship.

**A corollary worth knowing before you add a stage:** anything reading `git rev-parse --abbrev-ref HEAD` gets the
literal string `HEAD` in isolation, not a branch name. Fall back to the ship branch explicitly.

**The isolated worktree must also be given a toolchain, or its gate is a lie.** Its `.venv` is a symlink to a per-repo
cache that nothing else creates, and `quality-gates.sh` gates its PATH export on `[ -d .venv/bin ]` — **false for a
dangling symlink**, so before 2026-08-10 the gate silently ran `pytest` on the _system_ interpreter and reported
failures for a tree whose tests pass. quickmerge now provisions it (`uv sync`), and the gate now **fails closed** rather
than degrading silently (`agent-orchestrator@8f1a08ad53`). Node deps are cached per repo and seeded by **copy, never a
symlink** — `uv sync` pruned a shared `.venv` once already, and a linked `node_modules` would let `npm ci` do the same
to the operator's real tree.

### What worktree isolation does NOT cover (codified 2026-07-30)

Worktree/clone isolation covers exactly three things: the **working tree**, the **index**, and **HEAD**. Two surfaces
that agents routinely assume are isolated are NOT, and both have caused real data loss:

**1. `refs/stash` is a SINGLE shared LIFO stack per `.git` directory — not per worktree.** Multiple `git worktree`s on
ONE clone (including the `Agent` tool's `isolation: "worktree"` scratch worktrees under `.claude/worktrees/<id>/`) all
push to and pop from the same stack. Worker A's `git stash push` followed by worker B's `git stash pop` pops **A's**
entry, not B's — silently, with no conflict and no warning. **Confirmed incident 2026-07-30**: a push/pop race between
two concurrent sharded tranche workers of `/na-eligibility-audit` swapped two workers' unrelated changesets. This is
distinct from (and additive to) the "never `git stash drop` foreign WIP" rule below — here nobody drops anything, the
stack just hands the wrong entry to the wrong worker.

- **HARD RULE**: never `git stash` while running as one of several concurrent workers on a shared clone. Need a
  pristine-tree comparison? Use a **throwaway second worktree at HEAD** — `git worktree add <scratch> HEAD`, read it,
  `git worktree remove <scratch>` — which IS properly isolated. The `--autostash` flavours drive the same stack, so
  prefer `git pull --ff-only` from an already-clean tree over `git pull --rebase --autostash` in that shape. (Per-SLOT
  clones are separate `.git` dirs and therefore separate stash stacks — the hazard is concurrency WITHIN one clone,
  which is the normal shape for sub-agents and for the sharded per-tranche audit workers.)
- Note the asymmetry with the neighbouring rules: separate slot CLONES made cross-slot index collisions unrepresentable,
  which is exactly why the remaining shared-state surfaces are easy to forget.

**2. A shared scratch/temp filesystem path is not isolated either.** If two agents resolve the same scratchpad or temp
directory (a shared `TMPDIR`, a hardcoded workspace-relative scratch dir, a per-session path that two sub-agents of the
same session both inherit), they will clobber each other's intermediate files with no git involvement at all. Scope
scratch artifacts by a unique per-agent token (agent id / PID / `mktemp -d`), never by a name two concurrent workers can
both derive.

**3. `.git/COMMIT_EDITMSG` is a single unlocked file per `.git` directory — `git commit` invocations racing in the same
clone can swap MESSAGES across each other while each keeps its OWN correct tree (root-caused 2026-07-30,
`/plans/archive/issues/shared_clone_concurrent_commit_message_swap_2026_07_28.md`).** Every `git commit`, including a
non-interactive `git commit -m "..."`, still writes its message to `.git/COMMIT_EDITMSG` early (right after the
`pre-commit` hook) and only reads it back — to actually build the commit object — after the `prepare-commit-msg` and
`commit-msg` hooks finish. Unlike the index (`index.lock`, exclusive) and `HEAD` (compare-and-swap; a losing writer gets
`fatal: cannot lock ref 'HEAD': is at ... but expected ...`), **that message file has no locking at all.** If a second
`git commit` in the same clone — including one that ultimately FAILS (a branch-drift rejection, a prettier/plan-hygiene
auto-fix forcing a re-stage) — writes to `COMMIT_EDITMSG` while a first, slower invocation is still inside its own hook
chain (prek's formatter/linter/checker set commonly runs hundreds of ms–seconds), the first invocation's final commit
object gets ITS OWN tree (built from the index it already staged) but the SECOND process's message. Confirmed by direct
reproduction (a scratch repo + an artificial slow `prepare-commit-msg` hook): a clean `index.lock`/ref-CAS failure rules
out the index and `HEAD` as the culprit, and prek's own patch-stash tempfiles are PID-namespaced (`<ts>-<pid>.patch` —
not shared), leaving `COMMIT_EDITMSG` as the confirmed, reproduced root cause.

- **HARD RULE — one `git commit` in flight at a time per clone.** Do not run two `git commit` invocations (yours + a
  sub-agent's, or two sub-agents sharing this slot's index per "Within-slot ergonomics" below) concurrently against the
  same `.git` directory. Serialize: finish (or cleanly abort) one commit before starting the next.
- **Detection, not prevention, already ships**: `scripts/quickmerge.sh`'s Commit+Push+Flip step compares
  `git log -1 --format=%s` against the subject line it intended to commit and prints a loud `WARN` (never silently) on a
  mismatch — it does not auto-`--amend` (a swapped-in message may belong to a process still relying on its own HEAD
  read). Treat any such WARN as license to re-verify the SHA before citing it as `- [x] ... — <repo>@<sha>` evidence.
- This is a distinct mechanism from item 2 in that issue doc's "Corroboration" section (`git commit` silently picking up
  a FOREIGN process's staged files into the tree) — that one is a real index-sharing hazard requiring
  `git diff --cached --stat` + `git restore --staged <foreign-file>` before every commit (see "Within-slot ergonomics"
  below); this one (message-only) can happen even when the tree is provably clean.

**4. prek's own stash/restore cycle around each hook run is also not race-safe in a shared checkout — a verified
data-loss class, not a theoretical one (confirmed 2026-08-08,
`/plans/archive/issues/prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md`).** Each prek run stashes
unstaged changes to a PID-namespaced patch (`~/.cache/prek/patches/<ts>-<pid>.patch`) at hook-batch start and restores
them at the end. If a second session edits the SAME file while a first session's hooks are still running, the first
session's restore reinstates its own STALE pre-edit snapshot over the second session's newer edit — silently: no error
to the victim session, no conflict marker, and (unlike item 1 above) no `refs/stash` entry at all, since prek uses its
own patch cache rather than a real git stash. The victim's `git status` reads clean immediately afterward, which
actively confirms the wrong conclusion rather than merely omitting the right one. Reproduced on demand via
`scripts/dev/repro-prek-stash-restore-race.sh`. Two code fixes now shrink the window (flock-serializing the `git commit`
call in `safe-doc-push.sh`/`quickmerge.sh`, plus a checksum-verify hard-stop on those same call sites — see the issue
doc's Progress Log) but do not close every path — a raw/manual `git commit` outside those two scripts can still hit it.

- **Complementary safety net — `check_orphaned_prek_patches()` (`scripts/dev/safe-doc-push.sh`), added 2026-08-09
  (`/plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`).** After a
  successful push, compares every `~/.cache/prek/patches/*.patch` file's mtime against the run's own start epoch; a
  patch created during THIS run that outlived the push means its restore never happened, and the script fails loudly
  (exit 9) instead of silently exiting 0. Genuinely complementary to `_prek_race_snapshot`/`_prek_race_check` above, not
  redundant: the checksum check is per-call and only covers files already unstaged-dirty at THIS script's own
  `locked_git_commit()` snapshot; the orphan scan checks the shared cache dir directly, once, for the whole run, so it
  also catches a patch left behind by a DIFFERENT process's `git commit` (a bare commit outside these scripts, or a peer
  session) or a file that only went dirty after this script's own snapshot.

- **HARD RULE — back up uncommitted WIP to the scratchpad BEFORE running any git-touching command in a shared checkout,
  and verify the backup before trusting it.** Copy the file(s) you're mid-editing to your scratchpad
  (`cp <file> <scratchpad>/<file>.bak` or equivalent) ahead of any `git commit` / `prek run` / `safe-doc-push.sh` /
  `quickmerge.sh` invocation that could race with a concurrent session's hooks on the same clone, THEN confirm the copy
  actually landed (`diff`/`ls -la` the backup — don't just trust the `cp` exit code). This is what recovered the
  original incident's lost work; without it the edit would have been gone with no trace in any commit, stash, or on
  disk.

**5. `gcloud config set account` mutates HOST-WIDE state, not per-slot or per-session state — confirmed live twice in
one session, 2026-08-04 (`plans/active/issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md`).**
`~/.config/gcloud/` is deliberately excluded from the per-slot on-demand-artifact purge (§ "On-demand artifact pattern"
above) so credential files aren't duplicated per slot — but that shared location also holds gcloud's mutable
ACTIVE-SELECTION property (`core/account` / the active named configuration), not just static credential files. Any
concurrent slot running `gcloud config set account <x>` (or any tool that mutates the active gcloud config) changes
which identity EVERY OTHER slot's bare `gcloud` invocations use, immediately and silently — no lock, no warning, no
per-process scoping. Confirmed live: a production VM-launching backfill's active account flipped between three different
service accounts at least 4 times across ~2 hours with zero action from the affected session, twice landing on an
identity that lacked `compute.instances.create` and aborting an in-progress launch mid-run.

- **HARD RULE — prefer a per-invocation identity override over the ambient active account whenever the tooling supports
  one.** Use `gcloud --account=<sa> ...` (per-command flag, does not mutate shared state) or
  `CLOUDSDK_CORE_ACCOUNT=<sa>` exported only within the invoking script's own subshell, instead of relying on
  `gcloud config set account` having "stuck." A per-slot NAMED configuration
  (`gcloud config configurations create slot-<N>` + `CLOUDSDK_ACTIVE_CONFIG_NAME=slot-<N>`) is a further isolation
  option where a per-invocation override isn't practical — it scopes the mutable active-selection pointer without
  duplicating the underlying credential files.
- **Any other concurrent slot may change the ambient identity at any time.** Never assume the account you last set (or
  observed via `gcloud config list`) is still active by the time your next `gcloud` call runs — a sibling slot's own
  legitimate `gcloud config set account` between your calls is enough to flip it out from under you, with no error or
  warning at the point of mutation.

## Within-slot ergonomics

Every slot clone's `.envrc` declares:

```bash
export UNIFIED_TRADING_WORKSPACE_ROOT="${WORKSPACE_ROOT}/.tabs/<N>"
export PREK_CACHE_DIR="${WORKSPACE_ROOT}/.tabs/<N>/.cache/prek"
export SLOT_NUMBER="<N>"
export SLOT_OPERATOR="<operator>"
```

direnv-style auto-load isolates the prek patch cache + tells scripts which workspace root applies. Sibling-path-deps
(`uv pip install -e ../<dep>`) resolve correctly because every active repo's clone lives under the same slot dir.

**Within-slot collisions** (sub-agents in the same slot writing overlapping files) remain possible — sub-agents SHARE
the slot clone's index. Master agent mitigations:

- Partition sub-agent fan-out by repo/dir at spawn time (sub-A → MTDS, sub-B → UTL, sub-C → PM plan section X — no
  overlap by design).
- For unavoidable PM repo overlap (every slot touches plans + codex), master pre-allocates plan sections to sub-agents
  so they don't `git add` the same file simultaneously.
- Standard pre-commit check still applies within a slot — `git status` + `git diff --cached --stat` (no path arg) before
  every commit, and stage by name (never `git add -A`).

## Reconciliation — merged combination on LDR push-reject (codified 2026-06-03)

A slot clone commits ON `live-defi-rollout` and pushes straight to it. If the push is **rejected as behind** (a peer
landed first), aligning is a **content merge, not a pointer overwrite**:

1. **Case-split by whether you already have a local commit ahead of origin (`ahead`-count) — that is the variable that
   decides fast-forward eligibility, not file-content overlap** (decided fix 2026-08-01,
   `autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md` — see the non-conflict hazard subsection below for
   the incident this closes):
   - **`ahead=0` (pre-commit — no local commit yet)**: `git pull --ff-only` only. quickmerge STAGE 0.4
     (`_qm_stage_0_4_not_behind_gate`) does this for you and, on ff-only failure at `ahead=0`, reports
     `PRECOMMIT_WORKING_TREE_CONFLICT` and **blocks instead of falling back to `--rebase --autostash`** — with no local
     commit for rebase to replay, an ff-only failure here can only be a working-tree content overlap (a dirty tracked
     file the incoming diff also touches), and autostashing anyway would stash-and-repop the WHOLE dirty tree — every
     OTHER foreign file in this shared checkout, not just the overlapping one — for zero reconciliation benefit.
   - **`ahead>0` (post-commit — you already have a local commit ahead of origin)**: this IS genuine commit-graph
     divergence — `git pull --rebase --autostash` (quickmerge STAGE 0.4 does this for you) replays YOUR commits onto
     current LDR, dropping patch-id duplicates. **Immediately after the pop, BEFORE your own `git add <files>`, run
     `git restore --staged .` unconditionally** — it only unstages (never touches working-tree content, so it can't
     destroy anything), guaranteeing your index holds only what you explicitly `git add` this round regardless of what
     the autostash pop restaged.
2. **Resolve each conflict keeping BOTH sides' genuine work.** Additive plan/doc/code from both agents survives. Where
   two agents independently wrote the **same** rule/fix (a "two-similar" conflict), MERGE into the single best version
   (fold the weaker subset into the stronger superset — don't keep redundant duplicates). Incident 2026-06-03: a slot
   independently added a "never pipe a backgrounded command through `tail`/`head`" rule that a richer "Background-task
   honesty" rule subsumed → merged into one.

   **Incident 2026-07-27 (genuine, non-fast-forward conflict on a large shared plan doc)**: two conflict blocks in the
   same file — one a pure-whitespace artifact (an unrelated HTML-comment padding diff) too large for reliable Edit-tool
   string matching, resolved by direct line-index read/write; one genuine content conflict where a concurrent session
   had independently retagged an adjacent `[OPERATOR]`→`[DOC]` item while this session flipped a neighboring todo done —
   resolved by keeping BOTH edits (never picking one side and discarding the other), verified via
   `assert lines[idx].startswith(...)` checks against the exact expected line ranges before writing back. When a plan
   doc's conflict is whitespace-heavy or spans a huge diff, plain-Python line-index surgery is a legitimate recovery
   tool alongside the Edit tool — the goal (both sides' legitimate intent survives) matters more than which mechanism
   gets there.

3. **VERIFY content survival before pushing** — grep your key additions AND the incoming ones in each rebased file. A
   wording / em-dash mismatch can read as "lost" when it survived; a genuine drop MUST be caught here, not after the
   push.
4. Push again to `live-defi-rollout`.

**NEVER force-push a shared branch (`live-defi-rollout` / `main`).** There is no force-push and no tab branch in the
Path-B ship path — you rebase onto LDR (so peers' commits are your BASE, never overwritten) and push normally.
Plan-aware conflict shapes (append-section / checkbox-flip / paragraph-rewrite) + auto-resolve protocol:
[`plan-aware-merge-resolution.md`](plan-aware-merge-resolution.md).

### FETCH_HEAD verification discipline — use the stable remote ref, not FETCH_HEAD

**Never verify your work against `FETCH_HEAD`** — under a concurrent session `FETCH_HEAD` is overwritten by every
`git fetch` call any other agent issues, so its value is unreliable as a reference point (it can point at a different
tip than the branch you think you are comparing against). Use the **stable remote-tracking ref** instead:

```bash
# Confirm a SHA has landed on the integration branch (don't use FETCH_HEAD):
git merge-base --is-ancestor <sha> origin/live-defi-rollout && echo "landed" || echo "NOT on LDR"

# Confirm a path exists at the remote tip:
git cat-file -e origin/live-defi-rollout:<path> && echo "exists" || echo "absent"
```

These commands read the locally-cached `origin/live-defi-rollout` ref, which is updated by any `git fetch` and is not
overwritten by concurrent session fetches (unlike `FETCH_HEAD`, which is a single file updated on every fetch).

### Non-conflict autostash-pop hazard — foreign WIP silently lands in your index (2026-07-17)

Distinct from the CONFLICT case in the next subsection. The stage-by-name rule ("`git add <your files>`, never
`git add .`/`-A`") assumes naming your own files is sufficient to keep a concurrent agent's uncommitted work out of your
commit. In a shared per-slot checkout it is NOT, on the happy (non-conflict) path.

`--autostash` = `git stash` + restore. The restore re-applies the stashed changes **and their index state** — foreign
files that were merely dirty in the working tree (not staged by you) come back **staged**. A subsequent `git commit`
commits the whole index, so it sweeps up every foreign file regardless of what you passed to `git add`. It is invisible
pre-commit: `git status` correctly reports the foreign files as "Changes not staged for commit" right up until the pull,
and the post-pull index is never re-inspected. **Measured 2026-07-17**: `unified-trading-pm@1a59516af` was meant to add
ONE new issue doc; it landed with 3 files — a foreign agent's 157-insertion/125-deletion in-progress plan edit and a
brand-new issue doc they had not yet committed, published under this slot's authorship. Not data loss (the content was
intact on origin), but mis-attribution and premature publication of WIP the owning agent hadn't chosen to ship yet.

**The fix splits on `ahead`-count, not content overlap** (decided 2026-08-01, full derivation in
`autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md`) — see step 1 of the Reconciliation list above:

- **Pre-commit (`ahead=0`)**: skip the autostash path entirely — ff-only-or-block (`PRECOMMIT_WORKING_TREE_CONFLICT`).
  Shipped 2026-08-01, `unified-trading-pm@72bdb200e`.
- **Post-commit (`ahead>0`)**: keep `--rebase --autostash` (genuine commit-graph divergence — rebase is what keeps
  `live-defi-rollout` linear instead of littering it with merge commits), but immediately after the pop, BEFORE your own
  `git add <files>`, run `git restore --staged .` unconditionally.

**Do NOT "fix" a sweep after the fact by reverting.** Once pushed, the foreign content is the other agent's only
committed copy of that work — a revert or force-push to "clean up" the attribution deletes their uncommitted work,
turning a cosmetic problem into real data loss (force-pushing a shared branch is independently banned regardless). The
correct response to a sweep that already happened: leave it, tell the operator, and let the owning agent carry on (their
tree simply shows those files as already-committed after their next pull).

### Failed-commit staging hazard — a rejected hook leaves files vulnerable to a peer session's bare commit (2026-08-06)

A different TRIGGER for the same underlying fact as the autostash-pop hazard above ("`git commit` takes the WHOLE index,
not just what you just staged") — no `--autostash` involved this time. A commit attempt that fails a pre-commit hook
(e.g. the Conventional Commits format check) aborts the commit but does NOT unstage the attempted files — they sit
staged indefinitely while you diagnose/fix the failure. If a DIFFERENT session shares this exact index — commit
attribution is path-derived (slot number + host), not session-derived, so two interactive Claude Code tabs/windows on
the same machine, both pointed at the same slot directory, resolve to the IDENTICAL git identity — that session's own
unrelated `git add <its files>` + bare `git commit` commits the whole index, silently absorbing your leftover staged
files into its commit.

**Measured 2026-08-06**: `agent-orchestrator@e430623`, committed as
`fix(infra): add PrivateTmp=yes to resource- history-sampler.service...` (9 real lines), silently carried 460 lines of
an unrelated wallet-reconciliation feature's frontend/test files that had been sitting staged from a prior commit
attempt that failed the Conventional Commits check two minutes earlier. Not data loss — both commits landed and
`git merge-base --is-ancestor` confirms both are ancestors of the eventual HEAD — but the same mis-attribution class the
autostash-pop hazard causes, via a completely different trigger.

**Mitigation**: the instant a commit attempt fails validation (hook rejection, format error),
`git restore --staged <the same file list>` before doing anything else — fixing the message, re-diagnosing, whatever
comes next. Don't let files sit staged while you work on the fix; only re-stage right before the retry. This is the SAME
discipline the reconciliation list's `ahead>0` step already applies before a pull's `--autostash` pop — this hazard is
the reminder that it applies equally after a failed commit, pull or no pull.

### Autostash conflict recovery on rebase

When `git pull --rebase --autostash` (or `git rebase`) reports `Applying autostash resulted in conflicts`, the autostash
pop has produced merge conflicts in the working tree. **Do not attempt to resolve them in place** — the autostash may
contain the ONLY copy of a foreign agent's uncommitted WIP:

1. **`git rebase --abort`** — this is safe: it unwinds the rebase, leaves your commits as they were, and preserves the
   autostash in the stash list (the conflicting hunks are still there, not discarded).
2. Inspect the stash (`git stash show -p stash@{0}`) to understand what is yours vs. foreign.
3. **Stash only YOUR files by name** — `git stash push -- <your-file-list>` — so the rebase replay starts from a
   minimal-dirty tree.
4. Re-run `git pull --rebase` (without `--autostash` this time, since your files are now explicitly stashed).
5. Resolve any remaining conflicts keeping BOTH sides' genuine work (see reconciliation rules above), then
   `git stash pop` to restore your named stash.

**NEVER do `git checkout HEAD -- <file>` then `git stash drop`**: `git checkout HEAD -- <file>` discards ALL uncommitted
content for that file — if the autostash held a foreign agent's only WIP copy for that path, it is permanently gone
(UNRECOVERABLE). The autostash drop follows silently and the WIP is lost with no warning.

### Stash-pile regrowth signal (2026-07-30, stash_pile_workspace_cleanup_2026_06_03.md Phase 5)

The autostash-conflict pattern above means `refs/stash` piles regrow silently between manual `audit-stash-pile.sh`
sweeps — nothing un-stashes on its own, and per the multi-agent-safety HARD RULE a foreign WIP stash is never
auto-dropped. `scripts/dev/slot-git-status-report.sh` (already running every 5 minutes per slot) now carries a
WARNING-only watchdog: `scripts/dev/stash-pile-detect.sh` measures each repo's stash `count` and the age (in days) of
its OLDEST entry, and the reporter pings the slot's inbox (deduped once per episode, same mechanism as the existing
FF-pull-starvation watchdog) when either threshold trips. **It never touches `git stash`** — no read of stash content,
no apply, no drop; remediation stays the existing `audit-stash-pile.sh` dry-run-then-`--apply` runbook.

**Thresholds — measured, not invented** (2026-07-30, one laptop, 4 populated slots + the main-workspace clone,
`unified-trading-pm`):

| Slot / clone   | count | oldest entry             |
| -------------- | ----- | ------------------------ |
| slot 1         | 45    | 9-10 days                |
| slot 2         | 10    | 10 days                  |
| slot 3         | 33    | ~5 weeks                 |
| slot 4         | 1     | (residual, post-cleanup) |
| main-workspace | 11    | ~8 weeks                 |
| slots 5-11     | 0     | —                        |

The split is clean: a "still normal churn" slot sits at ≤11 entries with a max age around 10 days; a genuinely regrown
pile sits at 33+ entries with entries running 5-8 weeks old. Chosen thresholds (env-overridable —
`STASH_WARN_COUNT`/`STASH_WARN_AGE_DAYS` on the reporter, `STASH_PILE_WATCHDOG=0` disables the whole check):

- **count > 15** — comfortably above the observed normal-churn ceiling (11), comfortably below the observed regrown-pile
  floor (33).
- **oldest entry > 14 days** — one confirmation-window's worth of buffer past the observed normal-churn max (10 days),
  short enough to catch a pile going stale well before it reaches the multi-week range.

Either condition alone trips the warning (an old-but-small pile, e.g. one long-forgotten stash, still deserves a nudge).

### Silent duplicate-file resurrection after a rebase/stash-pop (2026-07-25)

A DIFFERENT failure mode from the conflict case above: a `git pull --rebase --autostash` (or a manual `git stash push` /
`git stash pop` cycle) can **silently resurrect stale pre-move copies of renamed files** with NO conflict markers and NO
error — `git status` looks clean, the commit succeeds, and the diff even looks plausible. This happened during a large
corpus-wide archival sweep: after several rebase cycles on a very active shared checkout, 54 files that had been
`git mv`'d into `plans/archive/` reappeared at their OLD `plans/active/` paths, duplicated alongside their correct
archive-side twins — with no rebase/stash output ever flagging it.

**Why `git status` doesn't catch this**: a clean working tree matching the last commit is not proof the LAST COMMIT
itself is correct — it only proves you haven't drifted from what you already committed. If the corruption happened
INSIDE a commit (a stash-pop reintroduced stale content that then got committed), `git status` reads as perfectly clean.

**Detection — verify commit CONTENT, not just clean status, after any rebase-heavy sequence involving file moves:**

```bash
# Don't trust git status alone. Spot-check that a doc you moved is genuinely NOT duplicated:
git cat-file -e HEAD:plans/active/<old-name>.md && echo "STILL AT OLD PATH — corruption" || echo "clean"

# For a gate-backed invariant (e.g. an archival count), re-run the actual checker against HEAD content,
# not just the working tree, and compare to the expected number:
python3 scripts/plan-hygiene/check_terminal_status_archived.py --quiet
```

A live gate script that unexpectedly jumps back to a much-higher violation count right after a rebase — on a tree that
`git status` reports as clean — is the tell. Re-run the check; if it's real (not a transient read mid-write by another
session), diff each flagged pair before touching anything (the resurrected copy is usually byte-identical to the
pre-move version, confirming nothing unique was added), then remove the stale duplicates one at a time (`git rm` — bulk
multi-file `git rm` invocations can trip the destructive-command guardrail; single-file calls do not).

**Root cause, best understood**: the prek/prettier auto-stage hooks and a manual `git pull --rebase --autostash` both
perform their OWN internal stash-and-restore cycles. On a checkout this actively shared (many concurrent sessions
committing every few seconds), these can interleave — one process's autostash pop can restore an OLDER snapshot of a
file's content over top of a newer rename that landed in between. The practical mitigation is procedural, not
preventive: **after any commit that moved/renamed files across a rebase-heavy sequence, immediately verify via
`git show HEAD:<path> | wc -l` (or an equivalent content check) that the committed result matches intent** — don't just
trust that a clean `git status` + a plausible commit message means the commit contains what you think it does.

**A second, self-inflicted variant (2026-07-25): a pathspec-scoped `git commit -- <paths>` that omits the OLD half of a
`git mv` silently drops the deletion.** `git mv old new` stages BOTH the removal of `old` and the creation of `new` as
one paired rename in the index. A `git commit -m "..." -- <pathspec>` that names `new` (and unrelated referrer-fix
paths) but never names `old` only commits the changes for the paths it was given — `old`'s staged removal doesn't match
the pathspec, so it is silently left uncommitted, and the resulting commit's tree inherits `old` UNCHANGED from the
parent. The archived doc and its stale pre-archival twin both end up live in the same commit, with no error and no
unusual `git status` output at commit time. **Fix: a pathspec-scoped commit that includes a `git mv` MUST name both the
old and new paths** (or just commit the rename with no pathspec restriction at all, once you've verified via
`git diff --cached --stat` that nothing foreign is staged). Detected the same way as the rebase variant above —
`git cat-file -e HEAD:<old-path>` unexpectedly succeeding — and fixed the same way: verify the resurrected content is
byte-identical to the pre-move blob, then remove it with its own single-file `git rm` + commit naming that exact path.

### A third variant (2026-07-27): UNCOMMITTED edits vanish entirely, not just stale content resurrecting

Distinct from both variants above (which involve content that was already committed at least once). Editing several
files, then running `quickmerge.sh` — which performs its OWN multi-stage internal `git stash`/pull/rebase cycle around
the pre-commit hooks — while those edits are still UNCOMMITTED, silently dropped them entirely (not reverted to a
stale-but-real prior version; the edit simply never reappeared anywhere, in the working tree, a stash, or a patch file)
on a branch this actively shared. It happened **twice in one session** editing the same 9 files, each time only
discovered by grepping for the edit's own added text after the fact — `git status` looked clean, no error was printed,
and there was nothing to "resolve" because nothing conflicted.

**The fix that worked reliably, proven across the rest of that session's ~50+ subsequent file edits with zero further
loss**: commit each file (or small batch) IMMEDIATELY after editing it — within seconds, before running
`quality-gates.sh`, before `quickmerge.sh`, before anything else. A real `git commit` survives a rebase (git replays
it); long-lived UNCOMMITTED changes sitting in the working tree across multiple pull/rebase/quickmerge-internal-stash
cycles do not reliably survive on a branch this busy. Concretely: edit → grep-verify the edit is on disk →
`git add <exact files, by name>` → `git commit` → only then `git pull --rebase --autostash` (safe now, since it's
replaying a real commit, not popping a stash over dirty content) → re-grep to confirm survival before doing anything
else → push, retrying the pull-rebase-push cycle as many times as the branch's traffic requires (this branch routinely
needs 2-4 retries for a single push; that is normal, not a sign of a problem). Editing 9 files then running one slow
multi-stage pipeline over all of them uncommitted is exactly the failure shape; editing-and-committing one small unit at
a time is the fix.

Under Path-B each slot is an independent clone with its OWN `.git`, so two agents sharing the same slot's `.git` is
structurally impossible in the normal operating model. However, in rare edge cases — a sub-agent launched by a
concurrent interactive session, or a manual setup that accidentally reuses a single clone as two contexts — a second
agent may share the slot clone's index while you have staged or committed content.

In this case **do NOT commit from the shared tree**. Instead, promote via a **throwaway worktree off the integration
branch**:

```bash
# Create an isolated worktree at a temporary path:
git worktree add /tmp/slot-promote-wt live-defi-rollout

# Copy or cherry-pick your content into it, then commit + push from there:
cd /tmp/slot-promote-wt
git cherry-pick <your-commit-sha>   # or stage + commit the files directly
git push origin live-defi-rollout

# Clean up the throwaway worktree:
cd -
git worktree remove /tmp/slot-promote-wt
```

This keeps your promotion isolated without touching the shared clone's index or working tree, so the concurrent
session's in-flight state is unaffected. The throwaway worktree shares the same `.git` object store (no duplication) but
has its own index file, so staging/committing there is completely independent.

## Commit attribution — slot + host in the author NAME (codified 2026-06-03)

**Problem (found in the 2026-06-03 slot-3 audit):** the author **name** was bare `ikennaigboaka` everywhere → CI
alerts + cross-agent triage couldn't tell which slot / host produced a commit; and the author **email was WRONG
fleet-wide** — of 25 slot clones, ~14 carried `semver-rollout[bot]@users.noreply.github.com` (so **agent commits there
masquerade as the semver bot** — risky, since semver-agent's own bot/author checks key off that email) and ~7 carried
`agent@ci.local` (unattributed).

**Mechanism — STANDARDISE both name + email per clone:**

- `user.name = "<operator> [slot-<N>·<host>]"` — `<N>` = the slot number; `<host>` = `laptop` (or the short hostname) on
  a workstation, the `vm-<id>` on a fleet VM.
- `user.email` = the operator's GitHub-attributed human account (NOT the bot, NOT `agent@ci.local`). GitHub commit
  attribution + semver-agent bot/author checks key off the EMAIL, so this fixes attribution AND stops the
  bot-masquerade, while making `git log --format=%an`, the GitHub author column, and CI `head_commit.author.name`
  correct + slot-aware.

**Per-operator (NOT hardcoded — codified 2026-06-05):** the email + name handle are **the operator's own GitHub
account**, which DIFFERS per laptop — Ikenna `ikennaigboaka <ikennaigboaka@gmail.com>`, Harsh
`harshkantariya <harshkantariya@odum-research.com>`. The three scripts that touch identity — the per-repo
`fix-commit-identity.sh` pre-commit hook, `setup-tab-worktrees.sh` (provision), and `verify-slot-host-symmetry.sh`
(assert) — all resolve it the SAME host-stable way:

```
1. env override            SLOT_CANON_EMAIL / SLOT_CANON_NAME
2. per-machine git config   git config --global slotIdentity.email   /   slotIdentity.name
3. fleet default            ikennaigboaka@gmail.com / ikennaigboaka   (VMs + Ikenna's laptop, unconfigured)
```

A **non-Ikenna host declares itself ONCE** (readable by every git invocation incl. the per-repo hook):

```bash
git config --global slotIdentity.email "harshkantariya@odum-research.com"
git config --global slotIdentity.name  "harshkantariya"
```

VMs leave it unset → fall through to the Ikenna-owned fleet default (VMs commit under the Ikenna GitHub account by
design).

**Set per clone — MECHANISM (Path-B, 2026-06-08):** each slot `.tabs/<N>/<repo>` is its OWN `git clone --reference` with
its OWN `.git/config`, so **plain `git config user.name` / `user.email` in the clone IS per-slot** — no
`extensions.worktreeConfig`, no `--worktree` flag (those were the shared-`.git/config` worktree-era workaround, retired
with the tab-branch model):

```bash
git config user.name  "ikennaigboaka [slot-<N>·<host>]"
git config user.email "ikennaigboaka@gmail.com"
```

`setup-tab-worktrees.sh` sets this at `--init` / `--add-slot` / `--reset-slot` (clone time). Sub-agents share the slot
clone → inherit the identity automatically. Do NOT hand-edit `~/.gitconfig`. **Consumers:** CI alert workflows attribute
via `github.event.head_commit.author.name`; the slot-git-status-report cron can group by slot.

**Caveat — this premise assumes ONE live session per slot.** If two interactive sessions/operators share the same slot's
checkout (the "Interactive-session slot collision" row in § Troubleshooting above), `.git/config` is shared state too:
commits from EITHER session land under whichever identity is currently stamped there, regardless of actual author
(confirmed 2026-08-01 — a session's own content-correct commit landed under the other operator's identity). This is not
a gap in the per-clone mechanism itself; it is a consequence of the interactive-session-collision gap and is mitigated
the same way (WARN-only `.agent-claim` liveness + the `SessionStart` collision hook), not solved at the identity layer.

### Derivation SSOT + checker (rework 2026-07-09 — ao_task_lifecycle plan Phase D)

The expected-identity rule lives in ONE sourced lib — `scripts/hooks/slot-identity-lib.sh`
(`slot_identity_resolve <repo-toplevel>`) — shared by the `fix-commit-identity.sh` pre-commit hook (enforce) and
`scripts/dev/check-slot-commit-identity.sh` (audit/stamp), so enforcement and audit can never drift:

- **Label is PATH-derived**: `…/.tabs/<N>/<repo>` → `slot-N`; anything else → `main`. The pre-2026-07-09 BRANCH
  derivation (`tab/<op>/<N>` → slot-N) was retired with the tab-branch model — Path-B slots sit on `live-defi-rollout`,
  so it resolved `main` in EVERY slot and actively REWROTE correct stamped identities away (the fleet-wide
  missing-slot-number bug).
- **Canon is SANITIZED**: any " [label·host]" suffix is stripped from the resolved canon name. (Live incident: the
  planning VM's global `slotIdentity.name` had itself been polluted with a label, so every hook self-heal CONCATENATED —
  `ikennaigboaka [slot-0·human-planning] [main·laptop]`.)
- **Host resolution gains a machine-level source**: `ORCHESTRATOR_VM_ID` → `VM_NAME` →
  `git config --global slotIdentity.host` → `laptop`. Fleet processes carry the env; INTERACTIVE shells on a VM don't
  (they used to stamp `·laptop` on the planning VM) — a VM declares itself once:
  `git config --global slotIdentity.host planning`.
- **Checker**: `bash scripts/dev/check-slot-commit-identity.sh [--fix] [--slot N]` — audits the main workspace + every
  `.tabs/<N>/<repo>` on the host against the lib's expectation; `--fix` stamps (worktree-aware; plain-config fallback);
  exit non-zero on drift. `setup-tab-worktrees.sh` runs `--fix --slot <N>` as the FINAL provisioning step, which also
  stamps repos added to an existing slot later (idempotent re-run). First host sweep (planning VM 2026-07-09): 419
  repos, 117 drifted → 114 fixed + hand-repaired globals (`slotIdentity.name` de-polluted,
  `slotIdentity.host=planning`).
- **Orphan-WIP preserve commits carry the SLOT'S OWN identity**
  (`agent-orchestrator server/worktree_clean_check/_orphan.py`): the old distinct `agent-orchestrator (orphan-wip)`
  author was REJECTED by the fail-closed hook → permanent slot quarantine → dispatch starvation (7/17 slots,
  2026-07-09). Preserve commits now resolve/stamp the slot identity (same resolution order as the lib) and use
  `--no-verify` (a preservation commit to a `wip-preserve/` ref is not a QG boundary); they stay greppable via the
  `chore(orphan-wip):` subject + `Orphan-WIP: slot-<N>` trailer.

## Git hooks are per-clone and MUST both be installed (2026-07-06)

Each Path-B clone has its OWN `.git/hooks` — hooks are NOT inherited from the reference clone. Two hooks are
load-bearing:

- **`pre-commit` = prek** (`prek install` — writes `pre-commit` + `commit-msg` only): runs gitleaks, slot·host
  commit-identity enforcement, branch-drift, ruff, prettier, conventional-commit — plus the staged-plans frontmatter
  schema gate in PM. **Found 2026-07-06: 384 of 400 clones (25 repos × 16 clones, every one carrying a prek config) had
  NEVER had it installed** (setup only provisioned pre-push), so commit-time gates silently never ran fleet-wide —
  that's how a gate-red issue doc reached LDR despite the check existing. prek REFUSES on a set `core.hooksPath`; 10
  clones carried a stale absolute post-`/active`-migration path there (disabling ALL hooks) — clear with
  `git config --unset-all --local core.hooksPath` only when the target dir is provably gone.
- **`pre-push` = the strict-quickmerge guard** (`scripts/hooks/pre-push`, installed — **prek must NEVER manage
  pre-push**). 24 main-ws clones lacked it too (the slot setup script never covers main-ws).

**Provisioning is now three-layered**: `setup-tab-worktrees.sh` installs BOTH at clone time for every repo
(`install_strict_quickmerge_hook` + `install_prek_precommit_hook`); the 5-min `slot-cron-ff-pull.sh` self-heal loop
covers **ALL repos × ALL clones** every tick (installs whichever hook is missing, clears a provably-dead
`core.hooksPath`, never touches a live custom one); and the server-side QG (`quality-gates-v2` on the promote PR)
remains the backstop that no local bypass (`--no-verify`, uninstalled hook) can dodge. Local hooks are the floor, not
the wall. Other hosts need no manual sweep — their cron self-updates from origin each tick, then heals their own clones.

## Ship into `live-defi-rollout` — visibility = durability (HARD RULE)

Ship every finished unit via `quickmerge --agent --files '<paths>'` (Pass-1 QG sentinel → Pass-2 commit + push to LDR;
the LDR→staging promote drain takes it onward). A push that lands on LDR is **immediately visible** to every other
slot's next FF-pull — that is the point: do not let a finished unit sit uncommitted/local.

**Foot-gun — durable but invisible.** A commit that exists only in your local clone (committed but not pushed to LDR)
creates a false "shipped" sense: the plan-flip checkbox is `[x]`, but downstream agents doing
`git fetch origin live-defi-rollout && grep <new_symbol>` find no match and treat the plan flip as a false claim. Push
the moment the work is done (the Commit + Push + Flip rule), so durability and visibility coincide. **Reference incident
2026-05-11**: a slot shipped writegate slice (b) across 5 repos but every commit sat private for hours while downstream
agents had no way to import the new helpers — the push-now discipline codifies this away.

## On-demand artifact pattern — venvs, node_modules, caches

**Slot clones are code-only.** No `.venv/`, no `node_modules/`, no `dist/`, no `.next/`. Build artifacts come into
existence only when a worker first spawns into a slot and needs them, and they live entirely inside the gitignored
surface — never tracked, never copied across slots.

| Artifact                                    | Build trigger                                              | Lives at                                                   | Survives slot reset?                   |
| ------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------- | -------------------------------------- |
| `.venv/` (per Python service repo)          | `uv sync` on first worker spawn or first manual invocation | `<repo>/.venv/` inside the slot clone                      | No — `--reset-slot` wipes the slot dir |
| `.venv-workspace/`                          | Operator-driven once per workspace, not per-slot           | `${WORKSPACE_ROOT}/.venv-workspace/` (above all slot dirs) | Yes — outside `.tabs/`                 |
| `node_modules/` (per frontend repo)         | `npm install` on first frontend operation                  | `<repo>/node_modules/` inside the slot clone               | No                                     |
| `dist/`, `build/`, `__pycache__/`, `.next/` | Build commands                                             | Inside per-repo clone                                      | No                                     |
| `data/` caches                              | First read of upstream data                                | Per-repo gitignored data dir                               | No                                     |

**Why on-demand**: many slots × many repos × ~500 MB of venv each would be hundreds of GB of duplicated venvs if eagerly
built per slot. On-demand keeps `.tabs/` at ~3-4 GB code-only. Every workspace repo with a Python service has `.venv`
listed in `.gitignore` so accidental commits are blocked.

**Excluded from on-demand purge** (credentials stay where they are, NOT in slot clones): `~/.aws/credentials`,
`~/.aws/config`, `~/.config/gcloud/`, `~/.config/gh/`, `~/.claude-accounts/<id>.env` (setup-token auth).

**Composes with**: the Phase-4 pre-spawn dirty-state gate (`worktree_clean_check.py`) uses `git status --porcelain`
which already excludes gitignored content, so on-demand artifacts don't trigger false dirty-state alarms; the
`.agent-claim` ownership file lives at `.tabs/<N>/.agent-claim` (slot root, above repos), never conflicts with per-repo
build dirs.

## Shared uv cache — one per-host cache, hardlinked venvs (codified 2026-07-17; relocated INSIDE `.tabs/` 2026-08-09)

**Rule**: `UV_CACHE_DIR = <workspace-root>/.tabs/.uv-cache` + `UV_LINK_MODE=hardlink`, where `<workspace-root>` is the
directory holding all repo clones (parent of `unified-trading-pm`). Derived, never a hardcoded home path — the cache
MUST sit on the same filesystem as the venvs it links into, or hardlinks silently degrade to copies (failure mode B2 in
`plans/archive/issues/slot_venv_duplication_disk_pressure_2026_06_29.md`; the fleet-wide dedup fix shipped 2026-06-29,
measured proof: shared `.so` inodes at `links=81`, ~21 GB reclaimed).

**The cache dir must live INSIDE `.tabs/`, not as its sibling (RULED 2026-08-09,
`/plans/archive/2026_08/issues/tabs_mount_boundary_defeats_uv_cache_hardlink_dedup_2026_08_09.md`).** This host presents
`.tabs/` as its own mount/bind boundary — `stat -c %d` reports an identical device id for `.tabs/` and its siblings, but
the kernel's `link()` syscall still refuses to cross the real boundary between them (`EXDEV`, confirmed via a raw `ln`
probe; same mechanism independently found for pnpm's default store, `ci_satellite_ao_dispatch_batch6_2026_08_08.md` item
10). A cache dir placed as a sibling of `.tabs/` (the 2026-07-17-codified `<workspace-root>/.uv-cache`) silently
degraded every cache→venv install to a full copy — `UV_LINK_MODE=hardlink` being correctly set did NOT save it, because
the boundary was crossed regardless. Verified fix: a real `uv sync` against the relocated
`<workspace-root>/.tabs/.uv-cache` shows installed `.so` files at `nlink=2` (was `nlink=1` fleet-wide, 1,800/1,800
sampled, per the 2026-08-08 investigation this fix corrects).

Four layers export the same derivation and all respect a pre-set value (`${VAR:-...}`), so whichever layer runs first
wins consistently:

1. **QG runs** — `scripts/quality-gates-base/base-service.sh` (every `quality-gates.sh` invocation, all hosts).
2. **AO slot spawns** — `agent-orchestrator/server/tmux_spawn.py` (worker shells on the planning VM).
3. **Interactive shells** — `scripts/dev/install-uv-cache-shell-env.sh` writes a managed block into the operator's
   `~/.bashrc`/`~/.zshrc`. Run ONCE per host (installed 2026-07-17 on the planning VM + hk dev host); without it,
   hand-run `uv` falls back to `~/.cache/uv`, which on split-filesystem hosts is cross-fs → silent copies + a second
   cache on the wrong partition. Verify: interactive `uv cache dir` prints `<workspace-root>/.tabs/.uv-cache`.
4. **The prune cron** — `scripts/dev/prune-uv-cache.sh` / `install-prune-uv-cache-cron.sh` — must target the SAME
   relocated dir, or it silently prunes an empty/unused directory while the real cache grows unbounded.

**Growth is bounded by two crons on the planning VM** (`i-0c9b283b31d6b5ca7`): `vm-disk-guard.sh` (threshold 80%,
cadence `0 */2` since 2026-07-17 — 6h let the host climb +19 points blind between firings) and
`install-prune-uv-cache-cron.sh`'s `uv cache prune` job (`0 */6`; the prune script resolves `uv` by absolute path —
cron's PATH excludes `~/.local/bin`, a silent-failure bug fixed 2026-07-16, `pm@88310f87a`). Execution history + all
measurements: `plans/archive/2026_07/ao_host_disk_pressure_2026_07_16.md`.

## gcloud SDK PATH symlinks — non-interactive shells never source `.bashrc`

**Same bug class as the cron-PATH gap above, different trigger.** A host with the snap-packaged `gcloud` pre-installed
puts `/snap/bin` on `PATH` ahead of the real SDK, and `/snap/bin/gcloud` cannot even run inside this sandbox
(`snap-confine is packaged without necessary permissions ... cap_dac_override not found`). `~/.bashrc` already sources
`google-cloud-sdk/path.bash.inc`, which PREPENDS the real SDK's `bin/` — but that fix only fires in an INTERACTIVE login
shell. An agent's sandboxed Bash-tool invocation (and any other non-interactive shell — cron, `claude -p`, …) never
sources `.bashrc`, so it still resolves the broken snap `gcloud`/`gsutil` first; every
`deployment-service/scripts/vm/*.sh` launcher and `create-code-tarballs.sh` depends on a working `gcloud` CLI, so this
silently blocks any interactive-AO-slot VM launch or tarball rebuild. Root-caused + fixed 2026-07-25:
`plans/archive/issues/vm_tarball_upload_expired_wif_token_interactive_slot_2026_07_25.md`.

**Fix**: `scripts/dev/install-gcloud-sdk-path-symlinks.sh` symlinks the real SDK's `gcloud`/`gsutil`/`bq`/
`docker-credential-gcloud` into `~/.local/bin` — already FIRST on `PATH` in every shell type observed on this host
(interactive and non-interactive alike), so no shell-startup file needs to run for it to take effect. Idempotent,
host-level (not per-slot, since `~/.local/bin` is one shared user directory); self-skips cleanly on a host with no SDK
conflict (e.g. a backfill VM that installs `gcloud` via apt with no snap present — `bootstrap_vm.sh` STEP 1.6).
Provisioned automatically by `setup-tab-worktrees.sh --init` alongside the slot-host crons; re-run by hand on an
already-provisioned host with `bash scripts/dev/install-gcloud-sdk-path-symlinks.sh`.

## pkill/pgrep cross-slot-kill guard — mechanical shell-level enforcement (codified 2026-07-28/29)

**Rule**: a process kill during a worker session must target an exact PID/PGID captured at background-start time (`$!`,
or the child PID) — never a bare `pkill -f <script-basename>` / `pkill <name>`. Every slot invokes shared scripts (e.g.
`quality-gates.sh --no-fix`) with IDENTICAL argv, so a name-only pattern is host-wide, not slot-scoped, and can kill a
DIFFERENT slot's live QG run. Two same-day recurrences (2026-07-28, slots 13 and 5) proved a RULES.md prose addendum
alone does not prevent the mistake under time pressure — enforcement moved from documentation to a mechanical guard.

**Fix**: `scripts/hooks/pkill-guard.sh` defines `pkill()`/`pgrep()` shell functions that shadow the real binaries —
ALLOW an exact numeric `-g/-G/-P/-s/-U/-u/-T` target, or a pattern containing the caller's own `.tabs/<N>/` cwd
substring (derived from `$PWD`); REFUSE (one-line stderr explanation, exit 1) any bare name/pattern lacking both. This
is a footgun-guard, not a security boundary — `command pkill ...` / an absolute path deliberately bypasses it (same as
any bash wrapper function), and it cannot intercept a non-shell caller (e.g. a Python `subprocess.run(["pkill", ...])`).

**Install**: `scripts/dev/install-pkill-guard-shell-env.sh` writes a managed block into `~/.bashrc`/`~/.zshrc` (mirrors
the uv-cache / gcloud-SDK installers above). Slot-aware: safe to run from inside any `.tabs/<N>/unified-trading-pm`
clone — it strips the `.tabs/<N>/<repo>` suffix so the sourced guard-lib path always resolves against the CANONICAL root
clone, staying valid host-wide regardless of which slot ran the installer. Run ONCE per shared host; idempotent (safe to
re-run — a re-run just replaces the managed block in place). Verify in a NEW interactive shell:
`pkill -f quality-gates.sh` → `REFUSED: ...`; a `.tabs/<N>/`-scoped `-f` pattern or a numeric `-g` target passes through
to the real binary unchanged.

Full incident history (two recurrences + root cause + rollout verification):
`plans/archive/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md`.

## Dashboard e2e ports are slot-namespaced (fixed 2026-08-07)

Same failure CLASS as the pkill guard above, different surface:
`agent-orchestrator/dashboard/tests/e2e/run-e2e-backend*.sh`

- `dashboard/playwright.config.ts` boot local `ORCHESTRATOR_MODE=mock` backend/dashboard pairs on fixed ports. Before
  this fix every slot used the SAME absolute ports (8790-8794 backend, 5198-5202 dashboard) — two slots running the
  Playwright suite concurrently collided, and `reuseExistingServer: false`'s port-clear
  (`lsof -ti tcp:$PORT | xargs kill`) killed whichever process was ACTUALLY listening, with no ownership check —
  confirmed live: killed `.tabs/3`'s in-progress `switch-model.spec.ts`/`edit-agent-modal.spec.ts` run this way while a
  different slot debugged an unrelated port conflict. Incident + investigation:
  `plans/archive/issues/ao_local_mock_server_workflow_truncation_and_e2e_port_collision_2026_08_07.md`.

**Fix**: `playwright.config.ts` derives `SLOT_OFFSET = slot_number * 10` from its own file path (same
`…/.tabs/<N>/<repo>` regex as `scripts/hooks/slot-identity-lib.sh`, kept local rather than shelling out) and adds it to
every port; the un-tabbed main checkout resolves to offset 0 (original ports unchanged). Each slot's own
`run-e2e-backend*.sh` computes its `ORCHESTRATOR_CORS_ORIGINS` from a `PLAYWRIGHT_*_PORT` env var that the config now
explicitly passes through (previously unwired — worked only by coincidence when the vite port always matched the
script's hardcoded literal default; a slot-offset port broke that coincidence and failed every dashboard→backend fetch
on CORS until this was wired). `reuseExistingServer` deliberately stays `false` (unchanged) — several specs mutate their
backend's seeded state durably (dispatch/park, collision-fix, chat-send), so reusing a not-freshly-reseeded server
across local reruns produces false failures; SLOT_OFFSET alone already fully closes the cross-slot collision, so reuse
was not needed. Shipped `agent-orchestrator@5d2ed4b09`.

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
   `commit_and_push_dirty_repos` REFUSES a pure mass-deletion (>20 files) / wiped index → outcome `quarantined`.
3. **FM8 liveness gate (the slot-isolation invariant)** — dirty content in YOUR slot clone is almost always a previous
   session of _you_ that is now gone → **inherit it** (commit+push as `chore(orphan-wip)`). The discriminator is
   **LIVENESS, not slot-id identity**: a dead/absent/expired claim, or a claim owned by the very session being respawned
   → inherit; a DIFFERENT live tmux session owning a fresh `.agent-claim`, or a dirty file with mtime < 120 s (a live
   interactive editor) → **PROTECT** (never stomp). **Quarantine is never terminal** — a dead maker's WIP is always
   eventually inherited.

**Stashes are per-clone (Path-B).** Each slot is a separate clone with its own `.git`, so `git stash list` shows ONLY
this slot's stashes — no cross-slot leakage (the old "linked worktrees share one `.git` → stash list exposes every
slot's stashes" hazard is gone). `stash_dirty_repos` still tags `slot-<N>-orphan-<ts>` for auditability.

**Branch-state gate (`check_slot_branch_state`):** per repo assert `HEAD == live-defi-rollout` (STOP on detached/wrong
branch), FF when behind+clean, quarantine on divergence. **Every repo — INCLUDING agent-orchestrator — integrates via
`live-defi-rollout`.** Do NOT special-case agent-orchestrator to `main`: slot clones track `origin/live-defi-rollout`
(server code ships from LDR; `main` is only the dashboard-SPA deploy branch + CI gate), so a `main` base reads every
slot as diverged — that override was removed from `scripts/dev/cron-branch-overrides.txt` 2026-05-24. The recovery /
auth-fail boot prompts inline the same ff-only-when-behind + divergence-STOP block so a recovered session self-verifies.

## Anti-patterns

- **Don't** create ephemeral per-theme clones. Slot is durable; theme rotates.
- **Don't** reuse a slot for a new theme without running `--reset-slot` first. Yesterday's WIP leaks into today's plan.
- **Don't** re-introduce a `tab/<op>/N` branch, `tab-mirror`, `--force-with-lease`-to-a-tab-branch, upstream
  re-pointing, or `extensions.worktreeConfig` per-worktree identity — all RETIRED with the tab-branch model. A slot is a
  clone on `live-defi-rollout`.
- **Don't** use `git add -A` / `git add .` inside a slot clone. Cross-slot collisions are unrepresentable (separate
  clones), but within-slot sub-agents share the index — pre-commit check + stage-by-name still required.
- **Don't** force-push `live-defi-rollout` / `main`. On a push-reject, rebase onto LDR keeping the merged combination.
- **Don't** pre-build venvs across all slots on `--init`. Eager build = hundreds of GB duplication per fleet; on-demand
  keeps it ~3-4 GB code-only.

## Composes with

- [`plan-aware-merge-resolution.md`](plan-aware-merge-resolution.md) — protocol the slot master uses at rebase time.
- `cursor-configs/CLAUDE.md` § "Per-slot worktrees — Path-B reference-clones on LDR" — the model summary + drift
  invariant.
- `cursor-configs/CLAUDE.md` § "Daily Work-Split Process" — operator orchestrator + daily work-split plan format.
- `plans/PLAN_FORMAT.md` § "Daily Work-Split Process" — slot↔theme table requirement.

## References

- Model SSOT:
  [`plans/active/worktree_ldr_unification_2026_06_08.md`](../../plans/archive/2026_06/worktree_ldr_unification_2026_06_08.md)
- Original plan (archived):
  [`plans/archive/per_agent_worktrees_2026_05_10.md`](../../plans/archive/per_agent_worktrees_2026_05_10.md)
- Bootstrap script: [`scripts/dev/setup-tab-worktrees.sh`](../../scripts/dev/setup-tab-worktrees.sh)
- Teardown script: [`scripts/dev/teardown-tab-worktrees.sh`](../../scripts/dev/teardown-tab-worktrees.sh)
- Drift invariant: `scripts/cicd/slot_drift_check.py`

---

## Committing from a contended checkout — isolated-worktree mode (2026-08-10)

**Authoritative for**: how `safe-doc-push.sh` and `quickmerge.sh` behave under concurrency, what their exit codes mean,
and when isolation is on. Root-cause evidence:
[`/plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`](/plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md).

### The hazard, stated once

Two processes committing out of **one checkout** interleave prek's patch save/restore and git's autostash push/pop. The
loser's uncommitted edits are reverted to HEAD with **no error and nothing in `git status` to explain it**. This is not
rare: measured 2026-08-10, six concurrent doc pushes from one shared checkout, with a peer session dirtying unrelated
tracked files, landed **0 of 6** (every worker `rc=7`, prek stash/restore race). The same six from isolated worktrees
landed **6 of 6** with every caller's working tree intact.

It needs concurrent writers **in one checkout** — which is a laptop condition, not a fleet one. Two interactive Claude
sessions routinely share one `.tabs/N` checkout (this doc's own multi-agent section documents that as accepted). The
orchestrator's planning VM dispatches one task at a time per slot, and each slot is already its own clone, so there is
no second writer to race.

### What each script does for you now — you do not hand-roll any of this

| Behaviour                               | `safe-doc-push.sh` | `quickmerge.sh`                         |
| --------------------------------------- | ------------------ | --------------------------------------- |
| Isolated worktree for stage+commit      | ✅ always          | ✅ laptop only (see gating below)       |
| Retry loop w/ backoff (6 attempts)      | ✅                 | ✅                                      |
| Per-repo push mutex + host governor     | ✅                 | ✅                                      |
| Per-checkout `flock` around commit      | ✅                 | ✅                                      |
| Drift gate made advisory for its commit | ✅                 | ✅                                      |
| Detects your content being reverted     | ✅ exit 10         | ✅ loud warning + recovery instructions |
| Recursion backstop                      | ✅ exit 11         | ✅ exit 11                              |

**Do not** re-improvise fetch/reconcile/stage-by-name/retry logic in-context. Call the script.

### Which race isolation actually solves — and which it does not

Two separate hazards get conflated. Keep them apart when reasoning about a host:

- **Shared-index race.** Two processes in ONE checkout: prek's patch save/restore interleaves with git's autostash
  push/pop, and the loser's uncommitted edits are reverted with no error. Measured 0/6 landed vs 6/6 isolated.
  **Isolation solves ONLY this**, and it requires a shared index to exist at all — a laptop condition, since interactive
  sessions have no allocation mechanism and share a `.tabs/N` checkout. On the AO VM one task runs per slot and each
  slot is its own clone, so the hazard is structurally absent and isolation would cost a full ~7,155-file worktree
  checkout per commit for nothing.
- **Push contention on the shared branch.** Many slots and hosts, one `live-defi-rollout`. Every host has this, AO
  included. **Isolation does nothing for it either way.** It is handled by the per-repo+branch push mutex (K=1), the
  rebase-and-retry loop, the advisory drift gate (which removed the livelock where a commit could never pass while
  origin moved during the ~2min hook chain), and the exit-10 content-vanished guard — all host-independent, all active
  regardless of the isolation gate.

So turning isolation off on the VM removes overhead for a hazard it does not have, and removes none of the protection
for the hazard it does. Both scripts therefore share ONE host gate: laptop → on, named VM → off, explicit flag/env wins
either way.

### Rebase-invalidated evidence citations reconcile themselves

A worker commits (SHA X), records `<repo>@X` in a plan todo, and ships — but both shipping scripts rebase onto origin
before pushing, which REWRITES the commit, so what lands is SHA Y and the citation resolves nowhere. This is not
fabrication; the SHA aged out between `git commit` and `git push`. Live instance 2026-08-10:
`unified-trading-pm@0f9b8a65ca`, whose work had really landed as `034cb4e2ad`. A pre-commit check structurally cannot
catch it — at commit time the citation IS resolvable. `scripts/dev/reconcile-sha-citations.sh` therefore runs AFTER the
last rebase and BEFORE the push, deriving the old→new mapping from `ORIG_HEAD` plus preserved commit subjects (ambiguous
subjects are skipped, never guessed), rewriting citations in the named files and amending. Best-effort and non-blocking;
`SHA_CITATION_RECONCILE=0` disables it.

### quickmerge isolation gating

`--isolated` forces it on, `--no-isolated` forces it off, `QUICKMERGE_ISOLATED=force|off` sets it non-interactively.
Default is `auto`, which resolves by host label (`ORCHESTRATOR_VM_ID` / `VM_NAME` /
`git config --global slotIdentity.host`, falling back to `laptop` — the same signal `slot-identity-lib.sh` already
uses):

- **Laptop (Ikenna / Harsh) → isolation is OPT-IN via `--isolated`, NOT automatic** (corrected 2026-08-10, same day it
  shipped). It was briefly default-on and that was wrong: `quality-gates.sh` cannot resolve its dependencies inside a
  fresh worktree — the end-to-end dogfood died with `ModuleNotFoundError: No module named 'unified_api_contracts'` and
  `'pandas'`, because symlinking `.venv` is insufficient (editable/sibling installs resolve relative to the ORIGINAL
  checkout, and the tooling re-resolves the environment from the worktree's own project dir). Default-on turned every
  laptop quickmerge into a QG failure — strictly worse than the race it guarded against. Until the venv-resolution
  problem is solved, use `--no-isolated` semantics by default and reach for `--isolated` deliberately.
- **agent-orchestrator planning VM → isolation OFF.** One task per slot, each slot already its own clone. Isolation
  would add a full worktree checkout per commit for zero safety gain.

**Isolation forces a full QG re-gate in quickmerge, by design.** Your checkout's Pass-1 `quality-gates.sh` sentinel does
NOT transfer into the worktree, and carrying it over would be a lie — the sentinel attests _your_ tree, whereas the
worktree is your named files applied to `origin/HEAD`, a different tree. Re-gating is strictly stronger (it validates
exactly what is being committed, rather than a sentinel a concurrent session may have invalidated since), and it earned
its keep immediately: the first end-to-end run of this path caught a live P0 in F7's own `_pm_root` resolution that had
already reached `live-defi-rollout`. But it costs a full QG run per quickmerge — use `--no-isolated` when you want the
sentinel fast path and know no peer is writing your checkout.

Isolation symlinks `.venv` / `.venv-workspace` / `node_modules` from the caller's checkout into the worktree, because
`quality-gates.sh` resolves the repo's own `.venv` and a fresh worktree has none (gitignored). Without that symlink
isolation would silently turn every quickmerge into a QG failure.

**Isolation also gives each run its own `PREK_HOME` (2026-08-12, `unified-trading-pm@62d1a42613`) — a real hardening,
NOT a confirmed fix for any specific observed corruption.** prek's default cache (`~/.cache/prek`) is host-global, not
per-worktree — its `patches/` subdir is where an unstaged-change stash/restore cycle lives around each hook batch, and
two fully-separate isolated worktrees on the same host funnel through that ONE shared directory in principle. **A direct
repro (`scripts/dev/repro-prek-cross-worktree-race.sh`) tested this exact mechanism — two separate worktrees, racing,
with a shared vs. isolated `PREK_HOME` — and it came back clean BOTH ways: cross-worktree corruption via a shared
patches dir does not reproduce, isolated or not.** A same-file concurrency test against the real `safe-doc-push.sh`
(non-overlapping edits: both preserved via the existing rebase-retry; overlapping edits: loud abort, never silent loss)
was also clean. So this hardening is kept because host-global cache sharing across worktrees is bad isolation hygiene
regardless, and it's free (every repo gets it via the `quickmerge.sh` symlink) — but do NOT cite it as "the fix" for a
specific revert report; that connection was tested and falsified. See
`/plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md` for the full elimination trail
(7 mechanisms tested) and the still-open root cause. Both `quickmerge.sh` and `safe-doc-push.sh` export a per-run
`PREK_HOME` (`$TMPDIR/{qm,sdp}-iso-$$/prek-home`) into the isolated re-exec — `repos`/`hooks`/`tools`/`cache` (the
expensive hook-environment installs, not part of the race) are symlinked in from a shared per-repo cache
(`~/.cache/qm-iso-prek/<repo>`, mirroring the venv-cache pattern), while `patches`/`scratch` are left for prek to create
fresh, private to that one run.

**If a revert IS ever detected again**, both scripts now dump a forensic snapshot automatically
(`unified-trading-pm@340bae9f60`) — entry fingerprints, HEAD state, recent commits on the named files, `git status`,
stash list, prek patches listing, worktree list — to `~/.cache/{sdp,qm}-forensics/revert-<ts>-<pid>.log` the moment
detection fires. The 2026-08-12 investigation only had a hash-only summary to work from, which was not enough to
distinguish the real mechanism from 7 tested-and-cleared candidates; this closes that gap for next time.

### Exit codes worth recognising

- **`safe-doc-push` exit 10** — retries exhausted **and** your named files no longer match what you handed the script.
  Do NOT re-run: that would push whatever is on disk now. The script prints the recovering `git stash` ref. Prefer
  `git show 'stash@{0}:<path>' > <path>` over `git stash pop` — these autostashes often also hold a peer session's WIP.
- **`safe-doc-push` / `quickmerge` exit 11** — isolation recursion backstop. A defect in the script, not your
  invocation; report it rather than retrying.
- **`safe-doc-push` exit 5** — genuinely transient, and the script has verified your content is intact. Re-running is
  safe.
- **`safe-doc-push` exit 6** — deterministic content rejection. Fix the content; re-running cannot help. Note a hook
  merely AUTOFIXING files is no longer classified here — that is retried automatically.

### The working commit order — reconcile → format → commit (codified 2026-08-12)

The order **reconcile → format → commit** is what `safe-doc-push.sh` / `quickmerge.sh` already do internally, and it is
the recipe an agent should reach for by hand if working around a contended doc push
(`pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`, F3). The three links compose into a closed loop if
taken in any other order:

1. Behind origin → prettier's own drift guard declines to format (residue protection for a bare `git commit`, since a
   formatted-then-blocked commit would leave reflow debris in the tree).
2. Unformatted content gets committed anyway → the hygiene hook autofixes it on the way in.
3. That autofix trips prek's `files were modified by this hook` → without the F2 fix this used to report a false
   DETERMINISTIC failure and refuse to re-run — over a tree that was one retry away from succeeding.

Reconciling FIRST (so the drift guard is satisfied before formatting runs) breaks link 1; formatting BEFORE committing
means the hygiene hook has nothing left to autofix, which breaks link 3 even without the F2 fix. Both
`safe-doc-push.sh`/`quickmerge.sh` now also set `DRIFT_GATE_ADVISORY=1` around their own commit call
(`check-branch-drift.sh` WARNs instead of hard-blocking on drift, since the wrapper's post-commit rebase enforces the
same invariant a few seconds later) and `prettier-autostage.sh` honours the same flag, so the sanctioned scripts do not
need this sequence spelled out by hand — a bare, unwrapped `git commit` on a contended checkout still does.

**The exit-5 caveat this recipe exists to prevent an agent from ignoring**: `safe-doc-push`'s exit-5 wording ("Exhausted
N attempts … this is transient, not a defect. Re-run.") is safe ONLY because the script fingerprints your named files at
entry and checks that fingerprint before printing it — if it does NOT match, the script instead exits **10** and names
the recovering `git stash` ref (see "Exit codes worth recognising" above). An agent who sees the word "transient" and
reflexively re-runs without first checking which exit code it actually was can re-ship whatever is on disk NOW, which
may not be what they intended. Read the exit code, not just the word "transient".

### Verifying a change to any of this

`scripts/dev/test-safe-doc-push-concurrency.sh <repo> <n-workers> <branch> [isolated 0|1]` is the regression harness.
Acceptance is three-part per worker: content landed byte-identical, no exit-0-without-content, and the **caller's**
working-tree copy unchanged. Its peer-noise writer is load-bearing — against a CLEAN checkout legacy mode scores 5/6 and
proves nothing, because prek only does its patch save/restore when unstaged changes exist.

## When a ship eats work it was never asked to touch (2026-08-10)

**The guards built for shared-checkout safety are scoped to `--files`.** `quickmerge`'s `_QM_ENTRY_FINGERPRINT` iterates
`$FILES_ARG`; `safe-doc-push`'s `_sdp_fingerprint_named` says so in its name; the exit-10 content-vanished check fires
on named files. All of them watch **the work you are shipping**, and stop exactly where your attention already is.

Nothing watched the rest of the tree. So an uncommitted edit to a file you were _not_ shipping could be stashed by
`git pull --rebase --autostash`, resolved against an incoming version during the pop, and lost — with the run exiting 0
and printing `✅ Landed`, correctly by its own definition, because it committed and pushed exactly what it was asked to.
Measured live: an edit to `scripts/quickmerge.sh` collided with a peer's upstream change to the same file and vanished;
it was found minutes later by accident, while checking something unrelated.

On a shared checkout, unrelated WIP in the tree is the **normal** state — so the unguarded case is the common one, not
an edge.

### `scripts/dev/tree-wip-guard.sh`

Three functions, wired into the ship scripts:

- **`wip_guard_snapshot`** — hash every MODIFIED TRACKED file at entry (untracked excluded: autostash does not move
  them, and flagging scratch files buries the signal).
- **`wip_guard_report <snapshot> <named-files>`** — after the reconcile, report anything whose content moved and was
  **not** in `--files`. Advisory by design: a push that already succeeded must not be retroactively failed over a
  neighbouring file. It cannot prevent the collision — `--autostash` is doing what it was told — it converts a SILENT
  loss into a LOUD, recoverable one. The content was never destroyed, only detached from where anyone would look.
- **`wip_guard_park_notice <stash-ref> <paths>`** — the other half. The two functions above write to the SHIPPING run's
  stderr, which reaches the pusher; when your reconcile parks a **peer's** work, that peer is in another session and
  sees nothing. This drops `.parked-wip` (gitignored) into the affected checkout, which `slot-git-status-report.sh`
  surfaces on its 5-minute cycle.

### Recovering parked work — use `wip_guard_restore`, never a wholesale copy

`git show 'stash@{N}:path' > path` is the instinct and it is **wrong in precisely the case that caused the loss**: the
edit was parked BECAUSE someone else changed that file, so restoring the whole file reinstates your version and silently
deletes theirs. This was one keystroke from reverting a peer's shipped fix.

`wip_guard_restore <stash-ref> <path>` decides on content, not intent:

| Situation                                   | Behaviour                                               |
| ------------------------------------------- | ------------------------------------------------------- |
| current == the version the stash was cut at | nobody else touched it → plain restore (exit 0)         |
| current differs                             | 3-way merge, base = `<stash>^1` → their change survives |
| same region changed on both sides           | conflict markers written, hand-resolve (exit 1)         |
| base unresolvable                           | nothing written, refuses to guess (exit 2)              |

Verified: `git merge-file` conflicts on ADJACENT-line edits and merges cleanly when the regions are separated —
conservative, and correct. Coverage: `tests/test_tree_wip_guard.bats` (10 cases, including a peer's change surviving the
restore).
