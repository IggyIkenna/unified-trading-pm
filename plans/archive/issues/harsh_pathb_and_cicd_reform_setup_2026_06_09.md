---
title: "Harsh host setup — align with the 2026-06-08/09 CI/CD reform + Path-B worktrees"
created: 2026-06-09
source:
  - plans/active/cicd_contract_hardening_2026_06_01.md (§ SESSION OUTCOME + ADDENDUM)
  - plans/active/worktree_ldr_unification_2026_06_08.md
locked_by: live-defi-rollout
priority: P1
status: resolved
resolved: 2026-06-12
---

> **🟢 RESOLVED 2026-06-12 (ACKED-INTO-CODE)** — Harsh's host (`hk`) is migrated to Path-B and aligned
> with the 2026-06-08/09 CI/CD reform. All slot worktrees are reference-clones on `live-defi-rollout`
> with per-slot identity reading `harshkantariya [slot-N·laptop]` (verified on slot-3). Setup task
> complete; archived per `codex/11-project-management/issue-doc-lifecycle.md`.

# Prompt for Harsh — finish setting up your host (Path-B worktrees + CI/CD reform)

> Hand this whole block to Harsh's agent/session. Run it on **Harsh's laptop** (handle `hk`,
> committer `harshkantariya <harshkantariya@odum-research.com>`). It's safe + idempotent and
> **preserves all uncommitted work** before changing anything.

## What changed on Ikenna's side (2026-06-08/09) that you need to align with

The CI/CD pipeline was healed + reformed and the worktree model was migrated to **Path-B**:

- **Worktree model → Path-B** (the `tab/<op>/N` tab-branch model is RETIRED). Each slot is now a
  per-slot `git clone --reference <main> <url> .tabs/<N>/<repo>` with its OWN `.git`, checked out
  directly on **`live-defi-rollout`**. No tab branch, no `tab-mirror-to-ldr.yml` (DISABLED
  fleet-wide), no upstream-self-heal, no diverged-tab recovery. Stay current with
  `git pull --ff-only origin live-defi-rollout`; ship via `quickmerge --agent --files`.
- **strict-quickmerge** is now a HARD RULE: CODE reaches the integration branch ONLY via
  `quickmerge --agent --files`. A direct `git push` of code is BANNED (carve-out: dirty-deps,
  FF-pull-in + PM `docs(plans)` flip, PM `scripts/`+`.github/` that must reach main). A pre-push
  hook + `scripts/cicd/check_strict_quickmerge.py` enforce it (WARN-default).
- **Content-based breaking-detection**: SIT/cascade-lock fire only on a real public-surface change
  (`scripts/cicd/detect_breaking_change.py`), not a 0.x-minor/docstring. QG-v2 still gates every PR.
- **LDR is the SSOT** + the **drift-tick** (`main-backmerge-to-ldr` `schedule: */20`) keeps main==LDR.
- **dep-content gate** (`scripts/cicd/check_dep_content_sync.py`) + `local_qg_sweep.py` oracle +
  `parity_watchdog.py`. All on `live-defi-rollout`.

Full record: `plans/active/cicd_contract_hardening_2026_06_01.md` §§ "SESSION OUTCOME" + "ADDENDUM".

## Run this on your host (in order)

```bash
cd <YOUR_WORKSPACE_ROOT>            # the dir that contains the per-repo main clones + .tabs/

# 0. Declare your identity ONCE (so commits attribute to you, not Ikenna):
git config --global slotIdentity.name  harshkantariya
git config --global slotIdentity.email harshkantariya@odum-research.com

# 1. Workflow-scoped GH token (carries workflow scope; the keyring gho_ token does NOT):
source unified-trading-pm/scripts/workspace/load-gh-token.sh

# 2. Get the new tooling + rules onto your MAIN clones (fast-forward; never force):
for r in */ ; do r="${r%/}"; [ -d "$r/.git" ] && git -C "$r" pull --ff-only origin live-defi-rollout 2>/dev/null; done
#   (PM now carries: setup-tab-worktrees.sh Path-B, migrate-slots-to-pathb.sh, slot_drift_check.py,
#    check_strict_quickmerge.py, the pre-push hook, and the updated CLAUDE.md + SUB_AGENT + codex.)

# 3. DRY-RUN the Path-B migration first (shows what it would preserve + reclone — touches nothing):
bash unified-trading-pm/scripts/dev/migrate-slots-to-pathb.sh --slots 1-<N> --dry-run
#   <N> = your highest slot number. If you are running this FROM inside a slot worktree, add:
#     --exclude <thatSlot>/unified-trading-pm     (you can't self-reclone the clone you're operating in)

# 4. Execute it. It PRESERVES every real uncommitted change to
#    origin/wip-preserve/harshkantariya-slot-<N> FIRST (junk excluded), then reference-clones each
#    slot onto live-defi-rollout, sets your identity, and installs the strict-quickmerge pre-push hook:
bash unified-trading-pm/scripts/dev/migrate-slots-to-pathb.sh --slots 1-<N>
#    (If you excluded your operating slot's PM, reclone it last from a different cwd, or just leave it
#     — it pushes via explicit `git push origin HEAD:live-defi-rollout` and is otherwise unaffected.)

# 5. Verify — every slot worktree must be a clone on live-defi-rollout, ancestor-or-equal of LDR:
python3 unified-trading-pm/scripts/cicd/slot_drift_check.py --tabs-root .tabs
#    Spot-check identity:  git -C .tabs/1/<repo> config user.name   # → "harshkantariya [slot-1·laptop]"
```

## Recover any preserved WIP (when you're ready to resume that work)

```bash
git -C <repo> fetch origin wip-preserve/harshkantariya-slot-<N>
git -C <repo> show origin/wip-preserve/harshkantariya-slot-<N>:<path>     # inspect
git -C <repo> cherry-pick origin/wip-preserve/harshkantariya-slot-<N>     # or apply, then QG + quickmerge
```

## After migrating — how you work under Path-B

- **Stay current**: `git -C .tabs/<N>/<repo> pull --ff-only origin live-defi-rollout` (your `slot-cron-ff-pull.sh`
  + `verify-slot-host-symmetry.sh` crons keep working unchanged — they key on the integration branch, not tab names).
- **Ship code**: `cd .tabs/<N>/<repo> && bash scripts/quality-gates.sh --no-fix && bash scripts/quickmerge.sh "..." --agent --files '<paths>'` — NEVER a raw `git push` of code (strict-quickmerge).
- **Docs/plans/scripts/.github**: the carve-out — a direct `git push origin HEAD:live-defi-rollout` is fine.
- Read `cursor-configs/CLAUDE.md` §§ "Per-slot worktrees — Path-B", "Strict quickmerge", "Breaking-detection is
  CONTENT-based", "LDR is the SSOT" + `SUB_AGENT_MANDATORY_RULES.md` for the full new contract.

## Status

- [x] ✅ [INFRA] P1. Harsh runs steps 0–5 on his host; `slot_drift_check.py` exits 0 + identity reads `harshkantariya [slot-N·…]`. Archive this doc when done. — done 2026-06-12; slot-3 identity = `harshkantariya [slot-3·laptop]`, all 25 repos reference-clones on `live-defi-rollout`.
