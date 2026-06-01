---
title: PM codex QG not enforced on live-defi-rollout pushes — ratchet drifted unnoticed
created: 2026-05-30
author: ikenna (slot 1)
source:
  - origin/live-defi-rollout @ ae2800938 (fix commit)
  - origin/live-defi-rollout @ ac85f82c1 (2026-05-29 ratchet that landed partial)
locked_by: live-defi-rollout
---

## What I found

The 2026-05-29 codex ratchet (`CODEX_MAX_VIOLATIONS` 12 → 2, commit `ac85f82c1`)
landed as a **5-file subset** of the agent's intended 7–8 file change. During a
messy `stash`/`rebase`/`pop` two fixes were silently dropped before push:

- `pyproject.toml` STEP 5.21 fix (`reportUnknown* = "none"` → `"error"`)
- `gcs_migration_bundle_2026_05_08.py` STEP 5.23 facade-import fix

So the tolerance was tightened to 2 while ~2 of the violations it cleared were
still present. The agent's local QG had passed (full tree) and written a green
sentinel, so quickmerge allowed the push — but the pushed commit was partial.

Worse: in the **~295 commits since**, full PM codex QG was effectively **never
re-run on `live-defi-rollout` pushes** (they were dominated by
`ci: ... [skip ci]` status bumps, `docs(plans):` fast-path, and `feat(scripts):`
pushes). New code drifted past the gate, accumulating **4 fresh codex
violations** plus a fail-fasting lint error:

| File | Check | Origin |
| --- | --- | --- |
| `migration/backfill_pipeline_mode.py` | STEP 5.23 deep UAC import | new file `9cf186cd8` |
| `orchestrator/prune_state_db_zombies.py` | bandit B608 + dead `# noqa: C901` (lint) | new file |
| `orchestrator/prune_state_db_zombies.py` | imports-inside-functions (`try/except ImportError` fallback) | new file |
| `dev/feature_parity_diff.py` | any-types false-positive (`[Any]` in a comment) | new file |

A fresh `bash scripts/quality-gates.sh` on the LDR tip therefore returned **RED**
(5 codex violations vs max 2, after a lint fail-fast) — i.e. the gate was broken
the whole time and nobody noticed because nothing re-ran it.

Fixed in `ae2800938` (QG now `ALL QUALITY GATES PASSED`, codex 1/2).

## Why it matters

This violates the **"Quality Gates Are A Merge Prerequisite" HARD RULE**: no code
change should merge to `live-defi-rollout` without `quality-gates.sh` exit 0 for
the touched repo. The current LDR push flow does not enforce this for PM itself:

- Direct `git push` to LDR has no remote CI (by design — enforced locally).
- The local enforcement (quickmerge sentinel) is bypassed when agents push
  directly, and the sentinel can go stale if a tree is mangled post-pass (exactly
  what happened to the ratchet commit).
- Fast-path (`docs`/`*.md` → main) and `[skip ci]` bumps never trigger PM codex QG.

Net effect: the codex ratchet is a **lagging** indicator that silently rots.
Fixing the 4 violations is whack-a-mole; they re-accumulate until enforcement is
real.

## Recommended decision

1. **Pre-push hook or CI on LDR for PM** that runs the codex-compliance subset
   (STEP 5.21/5.23 + imports-in-functions + any-types + bandit) on every push
   touching `*.py` / `pyproject.toml` / `scripts/quality-gates*.sh`, not just via
   quickmerge. Cheap subset (~seconds), no full pytest.
2. **Sentinel hardening**: invalidate `.qg_last_passed_sha` if the working tree
   changes between QG-pass and push (the dropped-fix root cause). Quickmerge
   should re-verify the committed tree, not trust a sentinel written against a
   since-mutated tree.
3. **Ratchet self-check**: a tiny QG step that fails if `CODEX_MAX_VIOLATIONS` is
   lower than the actual count — turning a partial-landing into an immediate red
   instead of a silent inconsistency.

Owner: slot 1 main / whoever owns `codex/06-coding-standards/quality-gates.md`.
