---
title: Staging/main clean-start from LDR-SSOT + stale-PR hygiene + LDR backlog drain
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
created: 2026-06-08
orchestrated_by: plans/active/cicd_contract_hardening_2026_06_01.md
related_plans:
  - plans/active/cicd_contract_hardening_2026_06_01.md
  - plans/active/issues/sit_94_failures_masked_by_dangling_lock_2026_06_07.md
  - plans/active/ci_local_qg_parity_2026_06_08.md
source:
  - chat design session 2026-06-08 (operator + vm-planning)
---

# Staging/main clean-start from LDR + stale-PR hygiene + drain

> **Orchestrated by** `cicd_contract_hardening_2026_06_01.md` (its WAVE 0/3 own the live drain — this plan is the
> coordinated, sequenced view; the live slot-1 session owns execution of the heal). **GATED: every destructive op below
> waits on the cascade jam clearing** (lock-clear + promote-bot fixed). Do not execute while staging is locked.

## Principle — LDR is the SSOT

`live-defi-rollout` is the integration source of truth. Staging and main are downstream projections of LDR. **The open
dep-update PRs are largely irrelevant** — if a PR's content is already on LDR, it is noise to be closed, not work to be
merged. The **only** exception: `main` may carry CI-workflow versions not yet on LDR (rare) — those must be back-merged
**down to LDR** before any force-sync, never discarded.

## Phase 0 — Heal gate (depends: cicd_contract_hardening WAVE 0/1, owned by live session)

- [ ] [INFRA] P1. **Block on**: staging lock self-clears (precheck/`>= STAGING_GREEN` fix live), AO phantom drained
      (`pending_repos` recomputed empty), promote-bot (`--auto --rebase`) green. Verify
      `staging_status.locked == false` + a clean LDR→staging promote merges before proceeding. (Do not duplicate the
      live session's fixes; consume their result.)

## Phase 1 — Reconcile rare main-only CI workflows DOWN to LDR (depends: Phase 0)

- [ ] [SCRIPT] P1. Diff `origin/main` vs `origin/live-defi-rollout` for every repo, restricted to `.github/**` + PM
      `scripts/**`. Any main-only content (CI workflow versions not on LDR) → back-merge **to LDR** first (LDR-SSOT), so
      the subsequent force-sync doesn't drop it. Everything else: LDR wins.
- [ ] [SCRIPT] P1. **Close the steady-state main→LDR drift hole (discovered 2026-06-08).** `main-backmerge-to-ldr.yml`
      fires `on: push: branches: [main]`, but **`[skip ci]` suppresses ALL GitHub Actions triggers — including the
      back-merge** — so the very `[skip ci]` machinery commits that go direct-to-main (ci_status writes, manifest bumps,
      starvation flags) never fire it. `main` chronically drifts ahead by those commits and only catches up when the
      next _non_-`[skip ci]` main push sweeps them in (observed: PM main ~8 commits ahead, all `[skip ci]` ci_status
      writes). **Fix (option 1, preferred): add a `schedule:` tick (~every 15–30 min) to `main-backmerge-to-ldr.yml`** —
      a cron run is not `[skip ci]`-suppressed, so it sweeps accumulated drift with no real commit; roll out fleet-wide
      via the template. (Option 2: the ci_status/manifest writer co-pushes its `[skip ci]` commit to LDR in the same
      step.) This makes the "main never ahead of LDR" invariant actually hold, not just eventually-converge.

## Phase 2 — Stale-PR sweep (#2) (depends: Phase 1)

- [ ] [SCRIPT] P1. For every open PR fleet-wide, compute head-diff vs `origin/live-defi-rollout`. **Empty diff (content
      already on LDR) → close** with a comment ("superseded — content already on LDR; LDR is SSOT"). Non-empty + part of
      an active cascade → leave. Build the sweeper as a reusable script
      (`scripts/cicd/close_superseded_prs.py --dry-run` by default; `--apply` only after dry-run review). **Precise
      stale def = empty head-diff vs LDR**, NOT "old" — the dep-update cascade PRs with real diffs are the convergence,
      never close those.

## Phase 3 — Force-sync clean start (#3) (depends: Phase 2)

- [ ] [INFRA] P1. **Run `run-version-alignment.sh` FIRST** (admin force-sync can revert semver-agent bumps — CLAUDE.md
      warning). Then fast-forward/force `staging` and `main` to match LDR's content (LDR-SSOT clean start), preserving
      the Phase-1 reconciled CI bits + the canonical semver tags. Verify no semver bump was reverted (compare
      `versions{}` pre/ post).

## Phase 4 — Drain the LDR backlog / quickmerge everything (#6) (depends: Phase 3)

- [ ] [INFRA] P1. Open a per-repo LDR→staging promote PR for everything sitting on LDR behind staging (incl. the
      checkout@v5 workflow files shipped 2026-06-08 via commit-to-tab). Drive the drain to `STAGING_GREEN` → `main` in
      dep order (T0 first). Watch the progress metric (repos reaching main); flat metric → STOP-and-diagnose, never
      wait.

## Success criteria

- `staging` and `main` content == LDR for every repo (modulo the reconciled main-only CI bits, now also on LDR).
- Zero open superseded PRs (empty-diff-vs-LDR); cascade PRs either merged or legitimately in-flight.
- No semver bump reverted by the force-sync.
- The checkout@v5 workflow files reach `main` fleet-wide (closes the 2026-06-08 commit-to-tab tail).
- A fresh test commit flows LDR→staging→main cleanly (the parity proof — see `ci_local_qg_parity`).

## Codex SSOT updates

`codex/08-workflows/ci-cd-flow.md` § LDR-as-SSOT + clean-start runbook; add the stale-PR sweeper to the runbook owner
table.
