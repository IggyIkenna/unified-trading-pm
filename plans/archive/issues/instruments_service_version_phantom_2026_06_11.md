---
title: "instruments-service version phantom — RESOLVED (de-inflated runaway semver to coherent 0.4.0)"
created: 2026-06-11
resolved: 2026-06-11
status: resolved
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# instruments-service version phantom — RESOLVED

> **RESOLVED 2026-06-11**: de-inflated the runaway semver and reconciled all version surfaces to a coherent **0.4.0**.

## What it was

`instruments-service` versions were incoherent: `workspace-manifest.json versions{}` = **0.30.0**,
`repositories{}.version` = 0.1.22, source `pyproject.version` = 0.31.0, staging = 0.32.0, latest git **tag** =
**v0.2.1**.

## Root cause (diagnosed)

A **runaway semver-agent loop on 2026-06-10 07:09–07:33 UTC** bumped the version `0.3.0 → 0.30.0` — **27 minor bumps in
24 minutes**, one per minute, all empty `chore(release): bump version to X` commits with **no real feature commits**
between them. The real released version was `v0.2.1` (the tag); everything ≥0.4.0 was inflation garbage, leaving
instruments-service wildly out of line with the fleet (others 0.3–0.8). (The bump-rate circuit breaker — ≥3 bumps/hr —
was added AFTER this incident; it would catch a recurrence.)

## Resolution (what shipped)

1. Lowered source `pyproject.version` 0.31.0 → 0.3.0 on `live-defi-rollout` (instruments-service@ea3495a9).
2. Force-synced `staging` tree to LDR (discarded the divergent 0.32.0 inflation bump) → cleared conflict-wall PR #437.
3. Promoted `staging → main` (#430, clean FF; main⊆LDR). During promotion semver-agent fired off the PR's v2
   (head=staging) and bumped to **0.4.0** — the legitimate promoted version, now coherent across **main = staging = LDR
   = 0.4.0**.
4. Created release **tag `v0.4.0`** at main HEAD (deleted the mislabeled interim v0.3.0); `v0.2.1` retained in history.
5. Reconciled PM `workspace-manifest.json`: `versions{}` = 0.4.0, `repositories{}.version` = 0.4.0, `staging_versions` =
   0.4.0; cleared stale `breaking_pending` / `pending_repos` / `promotion_failures` /
   `staging_commits[instruments-service]`.

## Verification

- `git show origin/main:pyproject.toml` → `0.4.0`; `git ls-remote --tags origin v0.4.0` → present; main-v2 = success.
- All three coherence surfaces agree at 0.4.0.

## Deferred work — migrated to:

- The one remaining follow-up (lower SIT's `instruments-service>=0.30.0` floor → `>=0.4.0`) is **migrated to**
  `plans/active/dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md` § Phase 5 (2026-06-12). Archived here.

## Follow-up (small) — MIGRATED, see above

- [x] ➡️ [SCRIPT] P2. Lower `system-integration-tests/pyproject.toml` `instruments-service>=0.30.0,<1.0.0` → `>=0.4.0`
      (the only remaining stale phantom-era floor; non-blocking today via content-first clone, but should match the true
      version). **MIGRATED 2026-06-12** to dependency_promotion plan § Phase 5.
