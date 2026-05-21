---
type: operator-broadcast
status: active
created: 2026-05-19 15:00 UTC
expires_after_ack: true
sender: slot-1-main (Ikenna)
recipients: ALL slots (Ikenna 2-11 + Harsh 2-11)
---

# 🔴 OPERATOR DIRECTIVE — commit + push dirty work to slot branch + FF to LDR

**Why**: many slots have dirty state across multiple repos; operator wants visibility into the latest state. Before
starting any new work (especially before Ikenna slots 3-9 boot into the repo consolidation push), each slot must
commit + push its in-flight work to its slot branch + ensure it's reachable from LDR.

**This is a one-shot sweep, not a recurring task.** After your tab is clean, normal Half-1+Half-2 commit cadence resumes
per CLAUDE.md "Commit + Push + Flip Plan Checkboxes As You Ship Each Item" HARD RULE.

---

## Per-slot procedure

Execute in EACH repo under your tab worktree `.tabs/<N>/<repo>/`:

### Step 1 — Inventory dirty state

```bash
cd ${WORKSPACE_ROOT}
for repo in .tabs/<N>/*/ ; do
  cd "${WORKSPACE_ROOT}/${repo}"
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "=== ${repo} DIRTY ==="
    git status -s
  fi
  cd "${WORKSPACE_ROOT}"
done
```

### Step 2 — Per dirty repo: stage YOUR files explicitly

🔴 **NEVER `git add -A` / `git add .`** — stage explicitly by name per CLAUDE.md "Stage explicitly by name; never git
add -A". Today's slot-1 commit (`518a0010d`) caught a pre-loaded foreign-staged 156-file index — explicit reset +
per-file stage prevented bundling foreign work. Same risk applies to your tab.

```bash
cd ${WORKSPACE_ROOT}/.tabs/<N>/<repo>
git status -s                                       # Inspect — confirm only your files appear
git reset HEAD -- . > /dev/null 2>&1                # Defensive: unstage anything pre-loaded
git add path/to/your/file1 path/to/your/file2       # Explicit names only
git diff --cached --stat                            # Verify: nothing foreign staged
```

### Step 3 — Commit with conventional prefix

```bash
git commit -m "<type>(<scope>): <summary>"
```

Conventional-commit prefixes (prek rejects others):

| Prefix     | When to use                                          |
| ---------- | ---------------------------------------------------- |
| `feat`     | new feature or scope                                 |
| `fix`      | bug fix                                              |
| `refactor` | code change without functional behaviour change      |
| `docs`     | documentation (incl. `docs(plans):`, `docs(codex):`) |
| `test`     | test-only changes                                    |
| `chore`    | tooling, deps, build                                 |
| `perf`     | performance improvement                              |

If prek auto-restore symptoms observed in commit output (look for "Restored working tree changes from
.../prek/patches/"): use `--no-verify` per CLAUDE.md foot-gun #4 authorization. Bundle Edit→stage→commit→push into ONE
Bash call when this is observed.

### Step 4 — Push to slot branch

```bash
git push origin HEAD:tab/<operator>/<N>
```

Replace `<operator>` with `ikennaigboaka` or `harshharish` (or your actual handle) and `<N>` with your slot number.

### Step 5 — FF to LDR

```bash
git fetch origin live-defi-rollout
git log --oneline HEAD..origin/live-defi-rollout    # Incoming-commit check

# If 0 incoming: push freely
git push origin HEAD:live-defi-rollout

# If incoming commits exist: rebase first
git rebase origin/live-defi-rollout
git push origin HEAD:live-defi-rollout
```

### Step 6 — Verify clean state

```bash
git status -s                                        # Should be empty (or only foreign edits)
git log --oneline origin/live-defi-rollout..HEAD     # Should be empty (your work is on LDR)
```

---

## Critical rules

- 🔴 **NEVER `git add -A` / `git add .`** — stage explicitly by name.
- 🔴 **NEVER force-push** (`--force` / `--force-with-lease`) without operator approval. Branch protection on
  `live-defi-rollout` will reject force-push; on slot branches it would rewrite parallel sessions' work.
- 🔴 **If you see merge conflicts on rebase**: STOP. Ping operator via your per-slot ping file or
  `ikenna_orchestrator/_agent_pings.md`. Do NOT auto-resolve foreign conflicts (CLAUDE.md "Two teammates × multiple
  parallel agents" HARD RULE).
- 🔴 **Untracked files in dep repos = NOT YOURS**. Leave them. Stage only what you wrote in your tab worktree this
  session.
- 🔴 **Foreign-file handling**: if `git status` shows foreign edits you don't recognise, leave them in the working tree.
  They belong to someone else's parallel slot. The auto-restore stash (`stash@{0}` per CLAUDE.md foot-gun #4) may
  preserve them; do NOT pop without understanding what's there.

---

## What "your" files means

A file is "yours" if:

1. You created it this session (untracked → now staged).
2. You modified it this session via Edit/Write tool (verify by reading your transcript).
3. The plan or task you were dispatched to owns it (e.g. slot 3 owns `strategy-service/pyproject.toml` for Phase 0.5).

A file is NOT yours if:

1. It was already dirty when you booted (foreign-edit from another slot).
2. Untracked in a dep repo you didn't explicitly modify.
3. You don't remember touching it and `git log` shows a different agent's last commit.

---

## Report back

Ack in your per-slot ping file (`ikenna_orchestrator/pings/slot_<N>.md` or `harsh_orchestrator/pings/slot_<N>.md`) with:

```
[<timestamp>] [ack] slot <N> commit-sweep complete:
  - <repo>@<sha> (<one-line summary>)
  - <repo>@<sha> (<one-line summary>)
```

If you cannot ship something (operator-gated, blocked, conflict), ack with:

```
[<timestamp>] [blocked] slot <N> commit-sweep: <repo> — <reason>
```

Examples:

- `[blocked] slot 4: instruments-service — rebase conflict with origin/live-defi-rollout, need operator review`
- `[blocked] slot 8: deployment-service — Terraform plan pending operator approval, code committed locally not pushed`
- `[ack] slot 6 commit-sweep complete: features-service@a1b2c3d (feat(metrics): add cardinality guard), pm@d4e5f6a (docs(plans): flip Phase 4D item)`

---

## Cross-references

- This broadcast: `plans/active/_operator_broadcast_2026_05_19_commit_dirty_work.md`
- CLAUDE.md HARD RULE: "Commit + Push + Flip Plan Checkboxes As You Ship Each Item" (Half-1 + Half-2)
- CLAUDE.md HARD RULE: "Two teammates × multiple parallel agents" (foreign-file etiquette)
- Today's work-split (Ikenna): `plans/active/work_split_2026_05_19_ikenna.md`
- Today's work-split (Harsh): `plans/active/work_split_2026_05_19_harsh.md`
