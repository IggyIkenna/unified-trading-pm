---
title:
  Strict-quickmerge provenance gate PERPETUALLY re-flags a trailer-less LDR commit after a squash-promote — every
  LDR→staging drain re-blocks on the same commit (14b11e2) until manually admin-merged
created: 2026-06-17
source:
  - "#ci-failures 2026-06-16/17: 'Provenance gate BLOCKED' on unified-trading-library #367/#368/#371/#372 — all the SAME
    commit 14b11e2; and features-service #567 (06a83fb6)"
  - scripts/cicd/check_strict_quickmerge.py
priority: P1
status: resolved
resolved: 2026-06-18
---

# Provenance gate perpetually re-flags a trailer-less LDR commit after a squash-promote

> **✅ RESOLVED + ARCHIVED 2026-06-18** — marker-based promote-range fix shipped
> (`scripts/cicd/promote_provenance_range.py`, PM@b54da7855 + PR #389→main); verified in prod (UTL #374 recreated with
> auto-merge armed, `14b11e2` no longer flagged). Both items closed, no deferred work; codex
> `08-workflows/ci-cd-flow.md` §D1 already states the contract.

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

- [x] ✅ [CICD] P1. Make the promote-bot provenance range track the **last-promoted LDR point**, not raw `staging..LDR`.
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
  - **RESOLVED 2026-06-17 (option 1, marker-based — no new state).** New `scripts/cicd/promote_provenance_range.py`
    resolves the marker = `headRefOid` of the **last MERGED LDR→target drain PR**
    (`gh pr list --base <staging|main> --head live-defi-rollout --state merged --limit 1 --json headRefOid`). For a
    merged PR the head SHA is frozen at merge time = exactly the last-promoted LDR SHA, so this needs **no moved tag /
    no state file / no write race** — strictly simpler than option 1's tag variant, same semantics. The bots emit
    `<marker>..origin/live-defi-rollout`. **Fail-safe**: no merged drain yet / empty / unreachable-marker → raw
    `<base>..LDR` fallback (WIDEN, never narrow); fail-OPEN on a checker error preserved. Both bots wired
    (`ldr-to-staging-promote.yml` temp-clone path with `--fetch-remote`; `ldr-to-main-promote.yml` PM-checkout path).
    HARD RULE + carve-out set unchanged — only the range computation. **Verified end-to-end**: UTL `14b11e2` (≤ marker
    `b859a153`) NO LONGER flagged under the new range, the OLD raw `staging..LDR` still flagged it; a fresh trailer-less
    `.py` after the marker IS still flagged. **Verified in prod**: dispatched `ldr-to-staging-promote`
    (only_repo=unified-trading-library) after closing the bug-blocked #373 →
    `mode=marker marker=b859a153 reachable=True` → `✅ provenance: promote-range is quickmerge-clean` → recreated PR
    #374 with auto-merge ARMED + 0 provenance-block comments (was the perpetually-blocked repo across #367–#373). Unit
    tests: `tests/unit/test_promote_provenance_range.py` + `tests/unit/test_check_strict_quickmerge.py`. Shipped:
    unified-trading-pm@b54da7855 (LDR) + PR #389 → main. SSOT: `codex/08-workflows/ci-cd-flow.md` § D1 (already states
    the contract).
- [x] ✅ [CICD] P3. ~~INTERIM (no code): the recurring drains are unblocked by `gh pr merge <n> --admin --squash`~~ —
      **MOOT, superseded by P1 (2026-06-17)**: the squash-blind perpetual block is fixed at the source, so no more
      whack-a-mole admin merges are needed. (#373 was closed; the fixed bot recreated #374 with auto-merge armed.)

## Composes with

`codex/08-workflows/ci-cd-flow.md` § strict-quickmerge + § "LDR is the SSOT". The strict-quickmerge HARD RULE itself is
correct (catch real bypasses); this is purely the RANGE computation being squash-blind.
