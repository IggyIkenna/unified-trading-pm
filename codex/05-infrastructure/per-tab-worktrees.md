---
title: "Per-tab worktrees — 3-tier isolation for parallel-agent flow"
scope: workspace
status: active
last_updated: 2026-05-10
owner: ikenna
related_plans:
  - plans/active/per_agent_worktrees_2026_05_10.md
related_codex:
  - codex/05-infrastructure/plan-aware-merge-resolution.md
  - ../../cursor-configs/CLAUDE.md
---

# Per-tab worktrees — 3-tier isolation for parallel-agent flow

**TL;DR.** Each operator (Ikenna / Harsh) runs N parallel agent "tabs." Each tab gets its own permanent worktree at
`.tabs/<N>/<repo>/` on a permanent branch `tab/<operator>/<N>`. Cross-tab races on `.git/index` + working tree become
unrepresentable by construction. Slot is the durable identity; theme (writegate / cefi-master / defi / etc.) is the
daily assignment via the operator's orchestrator LEDGER slot↔theme table.

## The 3-tier hierarchy

```
Tier 1 — Operator (Ikenna ⊥ Harsh)
    Physical machine boundary. No shared local state.
    Reconciliation: fetch + push via origin/live-defi-rollout. Cross-side
    coordination via workspace-shared plans/active/_agent_pings.md.

Tier 2 — Slot (within one operator)              ←── THIS DOC'S SCOPE
    Per-slot worktree at .tabs/<N>/<repo>/ on permanent branch
    tab/<operator>/<N>. Slot count is operator-declared at --init.
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
| 2    | mtds prediction smoke    | plans/active/predictions_master_2026_05_07.md                  |
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

| Symptom                                                               | Likely cause                                                                       | Fix                                                                                                                                                     |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--init` reports `SKIP <repo>` for an unexpected repo                 | Repo not cloned as sibling under `$WORKSPACE_ROOT`                                 | Re-run `bash scripts/workspace/workspace-bootstrap.sh --skip-fresh` to clone missing repos; then re-run `--init` (idempotent).                          |
| `--reset-slot <N>` aborts with "dirty file(s)" + an unfamiliar file   | Foreign-agent WIP OR runtime artifact (e.g. `.local-dev-cache/`, `catboost_info/`) | Per CLAUDE.md "Two teammates" rule: do NOT `git checkout --` foreign WIP. For runtime artifacts: discard with `git checkout --`. For WIP: commit/stash. |
| Cross-slot foot-gun-shaped behaviour (foreign work bundled)           | You're not in a slot worktree — main clone state leaked                            | `cd $WORKSPACE_ROOT/.tabs/<N>/` and start fresh. Confirm with `git rev-parse --show-toplevel` → should resolve to a path under `.tabs/<N>/`.            |
| prek auto-restore wipes your edits mid-session                        | Per-slot `PREK_CACHE_DIR` not exported (direnv not loading `.envrc`)               | Manually: `source $WORKSPACE_ROOT/.tabs/<N>/.envrc` before any commit, OR install direnv + run `direnv allow`.                                          |
| `git worktree add` fails with "already checked out at .../.tabs/<N>/" | Stale worktree entry after a manual `rm -rf .tabs/<N>/`                            | `git -C <repo> worktree prune` to clean the registry, then re-run `--add-slot <N>`.                                                                     |
| Branch `tab/<op>/<N>` already exists with diverged history            | Slot was previously used + branched off an older `live-defi-rollout`               | `setup-tab-worktrees.sh --reset-slot <N>` rebases onto current origin/live-defi-rollout (assuming clean state).                                         |
| `git rebase` produces conflicts during `--reset-slot`                 | The slot has commits not on `live-defi-rollout` (genuinely-divergent slot)         | Manual resolution: enter the slot, resolve conflicts, `git rebase --continue`, push the slot branch. Then re-run `--reset-slot` if needed.              |

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
| 2    | cefi-master                 | plans/active/cefi_master_2026_05_07.md                        |
| 3    | writegate Wave 4 slice (b)  | plans/active/writegate_honest_coverage_endtoend_2026_05_06.md |
| 4    | defi paper-trade smoke      | plans/active/defi_master_2026_05_07.md                        |
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
# → Slot is ready for the new theme.
```

The script **aborts on dirty state** rather than silently rebasing over it. If aborted, the operator's choices are:
commit, stash, or `git checkout --` per-file (only for tracked runtime artifacts that regenerate naturally — never for
foreign agents' WIP per the CLAUDE.md "Two teammates" rule). Then re-run `--reset-slot`.

Pinned to the daily work-split plan's "Daily reset" checklist. Operators should habituate to running it before assigning
a slot to a different theme.

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
[`Commit + Push + Flip Plan Checkboxes`](../../cursor-configs/CLAUDE.md) HARD RULE — codified 2026-05-11 after the
slice (b) ship-blindness incident where slot-branch commits sat hours private from downstream consumers.

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

## Per-shippable-unit FF-push into `live-defi-rollout` (HARD RULE codified 2026-05-11)

Every push to a slot branch MUST be followed immediately by a server-side fast-forward push of the slot tip into
`live-defi-rollout`. This is the Half 4 codification in
[`cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) § "Commit + Push + Flip Plan Checkboxes" — the
visibility complement to Half 1's durability push.

**Canonical command** (bundles Half 1 + Half 4 in one bash window):

```bash
git push origin tab/<operator>/<N> --no-verify \
  && git push origin tab/<operator>/<N>:live-defi-rollout --no-verify
```

The `tab/<op>/<N>:live-defi-rollout` form is a server-side FF push — origin verifies it's a fast-forward and advances
`live-defi-rollout` to the slot tip. **Remote rejects non-FF**: if rejected, your slot branch is behind LDR; rebase
onto `origin/live-defi-rollout` (existing conditional-push protocol) and retry both pushes.

**Why not auto-merge in a script.** The conditional check `ahead=N, behind=0` is the natural FF guard. A script that
runs the bundled command on every commit would mostly work — but the rebase-on-failure branch needs human (or agent)
judgment per plan-aware-merge-resolution. The HARD RULE is the discipline; the bash bundling is the implementation.

**Reference incident 2026-05-11**: slot 2 shipped writegate slice (b) end-to-end across 5 repos but every commit sat
on `tab/ikennaigboaka/2` for hours while downstream agents had no way to import the new helpers. Operator had to
explicitly FF-merge slot branches into LDR to unblock the dep chain (`manifest_schema_final_gate` Phase 2 was waiting
on the UTL `manifest_completeness` helper; slice (c) per-service rollout owners were waiting on the MDPS POC as a
copy-paste template). The Half 4 rule codifies this away.

**Foot-gun #5 — durable but invisible**. A clean Half 1 push to a slot branch creates a false sense of "shipped": the
commit is on origin, the plan-flip checkbox is `[x]`, but `live-defi-rollout` doesn't have it yet. Downstream agents
reading the plan, attempting `git fetch origin live-defi-rollout && grep <new_symbol>`, find no match and treat the
plan flip as a false claim. The fix is Half 4 — make the work visible at the same moment it becomes durable.

## Anti-patterns

- **Don't** create ephemeral per-theme worktrees. Slot is durable; theme rotates.
- **Don't** reuse a slot for a new theme without running `--reset-slot` first. Yesterday's WIP leaks into today's plan.
- **Don't** name branches after themes (e.g. `tab/ikenna/writegate`). Branch is the slot identity: `tab/ikenna/3`.
  Theme-naming undoes the slot-vs-theme decoupling.
- **Don't** use `git add -A` / `git add .` inside a slot worktree just because foot-guns #1/#2 are unrepresentable
  cross-slot. Within-slot, sub-agents share the index — pre-commit check still required.

## Composes with

- [`plan-aware-merge-resolution.md`](plan-aware-merge-resolution.md) — protocol the slot master uses at rebase time.
- `cursor-configs/CLAUDE.md` § "Daily Work-Split Process" — operator orchestrator + daily work-split plan format.
- `cursor-configs/CLAUDE.md` § "The mandatory pre-commit check" — within-slot discipline (the cross-slot half is trimmed
  because foot-guns #1-#3 are unrepresentable).
- `plans/PLAN_FORMAT.md` § "Daily Work-Split Process" — slot↔theme table requirement.

## References

- Plan: [`plans/active/per_agent_worktrees_2026_05_10.md`](../../plans/active/per_agent_worktrees_2026_05_10.md)
- Bootstrap script: [`scripts/dev/setup-tab-worktrees.sh`](../../scripts/dev/setup-tab-worktrees.sh)
- Teardown script: [`scripts/dev/teardown-tab-worktrees.sh`](../../scripts/dev/teardown-tab-worktrees.sh)
- Audit:
  [`plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md`](../../plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md)
  Block D3
