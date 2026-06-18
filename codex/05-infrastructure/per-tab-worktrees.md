---
title: "Per-slot reference-clones — 3-tier isolation for parallel-agent flow"
scope: [engineer]
status: active
last_updated: 2026-06-18
last_reviewed: 2026-06-18
owner: workspace-platform
related_plans:
  - plans/active/worktree_ldr_unification_2026_06_08.md
  - plans/archive/per_agent_worktrees_2026_05_10.md
related_codex:
  - codex/05-infrastructure/plan-aware-merge-resolution.md
  - ../../cursor-configs/CLAUDE.md
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

| Symptom                                                                                                                              | Likely cause                                                                                                                                                                                        | Fix                                                                                                                                                                                                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--init` reports `SKIP <repo>` for an unexpected repo                                                                                | Repo not cloned as sibling under `$WORKSPACE_ROOT`                                                                                                                                                  | Re-run `bash scripts/workspace/workspace-bootstrap.sh --skip-fresh` to clone missing repos; then re-run `--init` (idempotent).                                                                                                                                                                                                                                             |
| `--reset-slot <N>` aborts with "dirty file(s)" + an unfamiliar file                                                                  | Foreign-agent WIP OR runtime artifact (e.g. `.local-dev-cache/`, `catboost_info/`)                                                                                                                  | Per CLAUDE.md "Two teammates" rule: do NOT `git checkout --` foreign WIP. For runtime artifacts: discard with `git checkout --`. For WIP: commit/stash.                                                                                                                                                                                                                    |
| prek auto-restore wipes your edits mid-session                                                                                       | Per-slot `PREK_CACHE_DIR` not exported (direnv not loading `.envrc`)                                                                                                                                | Manually: `source $WORKSPACE_ROOT/.tabs/<N>/.envrc` before any commit, OR install direnv + run `direnv allow`.                                                                                                                                                                                                                                                             |
| A slot clone silently falls dozens/hundreds of commits behind `origin/live-defi-rollout` even though the FF-pull cron runs           | **FF-pull starvation**: an uncommitted local edit COLLIDES with an incoming changed file, so every `git pull --ff-only` aborts. Both crons treat "couldn't FF" as a benign skip, so nothing alerts. | The **FF-pull starvation watchdog** pages on this (below): a `FF-PULL STARVATION — slot N / repo` message lands in the slot inbox naming the colliding files. Remediate: `git stash push -- <colliding paths> && git pull --ff-only && (commit-or-restore the stash)`. The colliding file is usually foreign WIP — **stash-by-name, do NOT discard**.                      |
| `git pull` / `git fetch --tags` rejected with `! [rejected] vX.Y.Z (would clobber existing tag)` (commonly after a 1.0.0 graduation) | **Stale local release tag**: a local tag points at a different object than the remote's same-named tag, re-created by **semver-agent** (the SSOT for version tags).                                 | **`git fetch origin --tags --force`** — a **local-only** ref update pointing the stale local tags at the canonical remote objects. No commits lost, nothing pushed. Then `git pull --ff-only`. **Never** force-push local tags to remote (can revert a semver bump). `slot-cron-ff-pull.sh` fetches `--tags --force`, so cron-driven hosts auto-heal between manual pulls. |

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

The mapping of slot ↔ theme is daily-updated and lives authoritatively on the **agent-orchestrator dashboard**, with
the operator LEDGER `## Today's slot assignments` table as the offline fallback (forward index that fresh slot agents
read on bootstrap), mirroring the day's work-split plan (`plans/active/work_split_<YYYY_MM_DD>_<operator>.md`).

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

1. `git pull --rebase --autostash` (quickmerge STAGE 0.4 does this for you) — replays YOUR commits onto current LDR,
   dropping patch-id duplicates.
2. **Resolve each conflict keeping BOTH sides' genuine work.** Additive plan/doc/code from both agents survives. Where
   two agents independently wrote the **same** rule/fix (a "two-similar" conflict), MERGE into the single best version
   (fold the weaker subset into the stronger superset — don't keep redundant duplicates). Incident 2026-06-03: a slot
   independently added a "never pipe a backgrounded command through `tail`/`head`" rule that a richer "Background-task
   honesty" rule subsumed → merged into one.
3. **VERIFY content survival before pushing** — grep your key additions AND the incoming ones in each rebased file. A
   wording / em-dash mismatch can read as "lost" when it survived; a genuine drop MUST be caught here, not after the
   push.
4. Push again to `live-defi-rollout`.

**NEVER force-push a shared branch (`live-defi-rollout` / `main`).** There is no force-push and no tab branch in the
Path-B ship path — you rebase onto LDR (so peers' commits are your BASE, never overwritten) and push normally.
Plan-aware conflict shapes (append-section / checkbox-flip / paragraph-rewrite) + auto-resolve protocol:
[`plan-aware-merge-resolution.md`](plan-aware-merge-resolution.md).

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
via `github.event.head_commit.author.name`; the slot-git-status-report + orphan-ping crons can group by slot.

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
  [`plans/active/worktree_ldr_unification_2026_06_08.md`](../../plans/active/worktree_ldr_unification_2026_06_08.md)
- Original plan (archived):
  [`plans/archive/per_agent_worktrees_2026_05_10.md`](../../plans/archive/per_agent_worktrees_2026_05_10.md)
- Bootstrap script: [`scripts/dev/setup-tab-worktrees.sh`](../../scripts/dev/setup-tab-worktrees.sh)
- Teardown script: [`scripts/dev/teardown-tab-worktrees.sh`](../../scripts/dev/teardown-tab-worktrees.sh)
- Drift invariant: `scripts/cicd/slot_drift_check.py`
