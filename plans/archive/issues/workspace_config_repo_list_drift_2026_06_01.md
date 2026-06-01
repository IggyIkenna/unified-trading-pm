---
title: Workspace .code-workspace repo-list drift + tab-worktree generator path-style bug
created: 2026-06-01
author: ikennaigboaka (slot 5, interactive)
source:
  - slot-5 interactive session 2026-06-01 (VS Code "risk-and-exposure-service does not appear to be a git repository"
    error)
  - .tabs/*/unified-trading-system-repos.code-workspace
  - unified-trading-pm/cursor-configs/unified-trading-system-repos.code-workspace
  - unified-trading-pm/scripts/dev/setup-tab-worktrees.sh
parent_epic: infrastructure_master
assigned_vm: planning-vm
priority: P2
status: resolved-archived
locked_by: live-defi-rollout
locked_since: 2026-06-01
resolved: 2026-06-01
---

> **✅ RESOLVED 2026-06-01 — acked into
> [`plans/active/workspace_config_drift_remediation_2026_06_01.md`](../../active/workspace_config_drift_remediation_2026_06_01.md).**
> All 5 "Recommended decision" items shipped/resolved:
>
> - Item 1 (commit canonical fix): `unified-trading-pm@73963a354`.
> - Item 2 (generator path-style fix): `unified-trading-pm@c6dab6afd`.
> - Item 3 (regression guard QG step + pytest): `unified-trading-pm@79263233d`.
> - Item 4 (features-service `ci_status` adjudication): investigated — `quality-gates-v2` GREEN on LDR HEAD; the slot-5
>   `FAILING` flip was stale; dropped slot-5 `stash@{0}` (operator-acked); slot-5 PM tree unblocked.
> - Item 5 (FF-pull starvation watchdog): spec delivered in the remediation plan (wiring is an optional P3 follow-up).
>
> Codex `codex/05-infrastructure/per-tab-worktrees.md` documents the canonical-vs-slot `.code-workspace` path-style
> contract + guard. Archived per the issue-doc lifecycle (acked ⇒ archive immediately).

> **Provenance**: Surfaced while cleaning slot-5 working trees on 2026-06-01. The operator saw VS Code report
> `risk-and-exposure-service does not appear to be a git repository`. Root-caused to stale multi-root workspace config.
> Slot 5 applied a **runtime fix to the deployed loose files** (all 11 tab `.code-workspace` files + the canonical, as a
> working-tree change). This issue captures the **systemic gaps** that remain so they can be fixed properly with a
> regression guard + the generator bug fixed + the canonical committed. **Do not treat the slot-5 runtime fix as the
> durable fix** — it patched the symptom on disk; the SSOT + tooling + guard are below.

## What I found

### Finding 1 — `.code-workspace` repo lists drifted from the actual repo set (the visible error)

The multi-root VS Code workspace files list repos as `folders[]` (and in `git.scanRepositories` /
`git.ignoredRepositories` settings). VS Code opens every listed path as a git repo; a listed-but-absent path throws
`<name> does not appear to be a git repository`. The deployed files had drifted in **both** directions:

- **Stale (deleted/consolidated) repos still listed** — caused the error: `risk-and-exposure-service` (consolidated into
  `strategy-service`), `ml-inference-service`, `ml-training-service` (→ `ml-service`), `pnl-attribution-service`,
  `position-balance-monitor-service`, `new-sports-batting-services`.
- **Real current repos missing** — never added after they landed: `agent-orchestrator`, `greeks-service`,
  `fund-administration-service`, `ml-service`.

Spread across surfaces:

- **11 tab files** `.tabs/{1..11}/unified-trading-system-repos.code-workspace` (loose, untracked) — drifted into **5
  different content versions** (md5-distinct); tabs 9/10/11 additionally carried 40 stale `git.ignoredRepositories` + 5
  stale `git.scanRepositories` entries each.
- **Canonical SSOT** `unified-trading-pm/cursor-configs/unified-trading-system-repos.code-workspace` (git-tracked) — was
  missing `fund-administration-service`; an in-progress uncommitted edit had just added `greeks-service`.
- **Root symlink** `unified-trading-system-repos.code-workspace` → `.cursor/workspace-configs/…` → canonical (so the
  "main worktree" view inherits whatever the canonical says).

**Slot-5 runtime fix already applied (symptom-level, on disk):** rebuilt every tab's `folders[]` **from the real
worktrees present on disk** (self-healing) → all 25 current repos + workspace-root; cleaned the stale
`scanRepositories`/`ignoredRepositories` entries; added `fund-administration-service` to the canonical and removed 6
stale `ignoredRepositories` entries there (preserving the in-progress `greeks-service` add). The canonical change is a
**working-tree modification in the ROOT worktree `/…/unified-trading-system-repos/unified-trading-pm`** — **NOT yet
committed** (it also contains the foreign `greeks-service` add, so slot-5 deliberately did not commit it).

### Finding 2 — `setup-tab-worktrees.sh` copies the canonical with the wrong path style (latent regression)

`copy_workspace_file()` (`unified-trading-pm/scripts/dev/setup-tab-worktrees.sh:218-233`) does a **plain `cp`** of the
canonical workspace file into each slot dir:

```sh
src="${WORKSPACE_ROOT}/unified-trading-system-repos.code-workspace"   # → canonical, uses ../../ paths
dst="${sd}/unified-trading-system-repos.code-workspace"
cp "${src}" "${dst}"
```

The canonical uses `../../<repo>` paths (correct for its real home 2 levels deep under `cursor-configs/`), but the
function's own comment says _"relative paths in the workspace file resolve against the slot dir"_. A freshly
`--add-slot N` / `--reset-slot N` slot therefore gets a workspace file whose `../../<repo>` paths resolve to the **main
worktree's** repos (`/repos/<repo>`), **not the slot's own** (`.tabs/N/<repo>`). It will not throw the "not a git
repository" error (those dirs exist), so it fails **silently** — the operator edits in slot N but the SCM panel /
multi-root tree points at the main checkout. The existing deployed tab files use **relative (bare-name)** paths,
confirming the intended style is relative — so the generator and the canonical disagree on path style.

### Finding 3 — No guard prevents either drift (the reason both happened)

Nothing fails when (a) a `.code-workspace` `folders[]` list diverges from the actual repo set / the
`workspace-manifest.json` active-repo set, or (b) the generator emits the wrong path style. Both Finding 1 and Finding 2
are silent until a human notices a broken SCM panel.

### Observation A — foreign uncommitted edit was blocking slot-5 PM's FF-pull (related, lower urgency)

Slot-5 `unified-trading-pm` was **963 commits behind** `origin/live-defi-rollout` with origin set **correctly**
(`origin/live-defi-rollout`, same as slot 3). The FF-pull cron had been silently blocked by an **uncommitted foreign
edit** in `workspace-manifest.json` marking **`features-service` `ci_status: LOCAL_PASS → FAILING`** (origin still says
`LOCAL_PASS`, so it is a real, non-redundant edit). The incoming commits also touch that file, so every `--ff-only`
aborted. Slot 5 preserved the edit in a labeled stash
(`stash@{0}: slot5-FOREIGN: features-service ci_status LOCAL_PASS->FAILING`) and fast-forwarded the slot to current. The
edit is **not lost** but **not committed** — someone marked features-service CI failing and never landed it.

## Why it matters

- **Dev ergonomics / correctness**: a broken multi-root SCM panel (wrong/absent repos) is how slots silently edit the
  wrong worktree (Finding 2) or see phantom errors (Finding 1). The slot-host-symmetry model assumes every slot's view
  is accurate.
- **Recurrence**: with no guard (Finding 3) this will drift again on the next repo add/consolidate — it already drifted
  into 5 different tab versions.
- **Silent FF-pull starvation** (Observation A): one stuck uncommitted file held a slot 963 commits behind for an
  unknown period without any alert. The same failure mode applies to any slot/repo where a dirty file collides with
  incoming commits — worth a watchdog signal.

## Recommended decision

1. **Commit the canonical fix** (ROOT worktree working-tree change) — add `fund-administration-service`, drop the 6
   stale `ignoredRepositories` entries, keep the `greeks-service` add. This is the SSOT; committing it makes the
   main-worktree view durable and feeds the generator. Verify it lists exactly the active repo set first.
2. **Fix the generator path style** (`setup-tab-worktrees.sh:copy_workspace_file`): either (a) rewrite `../../` →
   relative on copy (sed the `path` values), or (b) keep a **relative-path canonical template** dedicated to slot
   copies. Pick one; the existing deployed tab files use relative, so (a)/(b) should both land on relative in slots.
   Decide and document which file is canonical for which consumer (root symlink vs slot copies).
3. **Add a regression guard** (P2): a QG/test step (PM `quality-gates.sh` or a small pytest) asserting the canonical
   `.code-workspace` `folders[]` == the active (non-archived) repo set in `workspace-manifest.json`, and that no listed
   path is a known-deleted repo. Optionally validate `git.scanRepositories`/`ignoredRepositories` entries resolve to
   real dirs. This closes Finding 3.
4. **Adjudicate the features-service `ci_status` edit** (Observation A): is features-service CI actually FAILING (then
   commit the manifest flip + open/point at the remediation) or stale WIP (then drop `stash@{0}`)? Either way the slot
   tree should not carry a perpetually-dirty manifest that starves the FF-pull cron.
5. **Consider a "stuck dirty file starving FF-pull" watchdog signal** — a slot N commits behind origin with a clean FF
   available but a dirty-file collision should ping the orchestrator, not sit silent.

## What slot 5 already did (do not redo)

- Rebuilt all 11 tab `.code-workspace` `folders[]` from real worktrees + cleaned their stale settings arrays (loose
  files, no commit needed — done on disk).
- Applied the canonical add/cleanup as a ROOT-worktree working-tree change (item 1 above — **needs commit**).
- Fast-forwarded slot-5 `unified-trading-pm` to current; foreign features-service edit preserved in `stash@{0}`.
