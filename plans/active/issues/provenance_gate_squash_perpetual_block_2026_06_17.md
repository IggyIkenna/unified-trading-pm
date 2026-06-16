---
title:
  Strict-quickmerge provenance gate PERPETUALLY re-flags a trailer-less LDR commit after a squash-promote — every
  LDR→staging drain re-blocks on the same commit (14b11e2) until manually admin-merged
created: 2026-06-17
author: slot-3·laptop
source:
  - "#ci-failures 2026-06-16/17: 'Provenance gate BLOCKED' on unified-trading-library #367/#368/#371/#372 — all the SAME
    commit 14b11e2; and features-service #567 (06a83fb6)"
  - scripts/cicd/check_strict_quickmerge.py
locked_by: live-defi-rollout
priority: P1
status: active
---

# Provenance gate perpetually re-flags a trailer-less LDR commit after a squash-promote

## What I found

`scripts/cicd/check_strict_quickmerge.py` enumerates the promote range with **`git rev-list <base>..<head>`** (`main()`
line ~79) and flags any commit that changed SOURCE without a `Quickmerge:` trailer (a real direct-push bypass). The
promote bots (`ldr-to-staging-promote`) run it over (effectively) `origin/staging..origin/live-defi-rollout` and **won't
arm auto-merge** when it flags a commit.

The bug: when a trailer-less commit (e.g. UTL `14b11e2` `fix(kill-switch): … bus.py`, direct-pushed by slot-6) drains to
staging via a **SQUASH** merge, staging gets a NEW squash commit — the original SHA never lands on staging, AND the
squash's combined patch-id ≠ the individual commit's patch-id. So:

- `git rev-list staging..LDR` → still contains `14b11e2` (its SHA isn't on staging) → **re-flagged**.
- `git cherry staging LDR` → ALSO shows `14b11e2` as `+` (its individual patch-id isn't on staging; the squash has a
  different combined patch-id) → cherry does NOT fix it either.
- the merge-base of staging+LDR is unchanged (a squash creates no parent link) → `merge-base..LDR` still includes it.

So a single trailer-less commit re-blocks **every** subsequent LDR→staging drain, forever, until each drain is manually
`gh pr merge --admin`'d (whack-a-mole: observed #367 → #368 → #371 → #372 all blocked on the identical `14b11e2`; the
operator/agents admin-merged #367/#368, and #371/#372 re-appeared). features-service #567 shows the same on `06a83fb6`.

## Why it matters

Every breaking-change cascade (which bumps deps fleet-wide → many drains) re-trips these on each drain, generating
recurring CRITICAL "Provenance gate BLOCKED" noise + stalling the LDR→staging drain auto-merge for repos that carry ANY
historical trailer-less commit. It is NOT catching a real new bypass — the content is valid and already on staging; the
gate just can't tell, because squash-merges destroy per-commit promotion tracking.

## Recommended decision (needs focused, fresh-context work — critical fleet gate)

- [ ] [CICD] P1. Make the promote-bot provenance range track the **last-promoted LDR point**, not raw `staging..LDR`.
      Options (pick one, verify it still catches a genuine new direct-push): 1. **Marker-based (preferred):** when
      `ldr-to-staging-promote` squashes LDR@`<sha>`→staging, record `<sha>` (a moved lightweight tag
      `last-promoted-to-staging` on LDR, or a field in the SIT/ci-status state). The provenance check then runs
      `last-promoted-to-staging..origin/live-defi-rollout` — only commits since the last drain, so an already-drained
      trailer-less commit drops out of range permanently. Genuine new direct-pushes (after the last promote) are still
      flagged. 2. **Content-diff fallback in the gate:** for a flagged commit, before reporting it, check whether the
      files it changed are already byte-identical on `origin/staging` (`git diff` of the commit's paths vs staging) → if
      so, it's already reconciled, skip. More expensive but bot-agnostic. 3. **Operator-gated clean-start force-sync**
      of the repo's `staging`(+`main`) to LDR collapses the divergence so the trailer-less commits become part of the
      staging base (no longer in `staging..LDR`). This is the canonical LDR-is-SSOT fix but is per-repo +
      operator-gated, not a durable systemic fix on its own.
- [ ] [CICD] P3. INTERIM (no code): the recurring drains are unblocked by `gh pr merge <n> --admin --squash` once the
      drain's `quality-gates-v2` is green (the content is valid). This is whack-a-mole — only the P1 above stops it.

## Composes with

`codex/08-workflows/ci-cd-flow.md` § strict-quickmerge + § "LDR is the SSOT". The strict-quickmerge HARD RULE itself is
correct (catch real bypasses); this is purely the RANGE computation being squash-blind.
