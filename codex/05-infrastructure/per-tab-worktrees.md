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
slot master pushes its slot branch to origin per shippable unit; merge to `live-defi-rollout` happens as a separate
shippable-unit step (master runs `git checkout live-defi-rollout && git merge --ff-only tab/<op>/<N> && git push` OR
ships the merge via the slot branch directly — both work).

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
