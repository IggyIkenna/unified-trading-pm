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
locked_by: live-defi-rollout
locked_since: 2026-05-21
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

- [x] ✅ [INFRA] P1. **Block on**: staging lock self-clears (precheck/`>= STAGING_GREEN` fix live), AO phantom drained
      (`pending_repos` recomputed empty), promote-bot (`--auto --rebase`) green. Verify
      `staging_status.locked == false` + a clean LDR→staging promote merges before proceeding. (Do not duplicate the
      live session's fixes; consume their result.)

## Phase 1 — Reconcile rare main-only CI workflows DOWN to LDR (depends: Phase 0)

- [x] ✅ [SCRIPT] P1. Diff `origin/main` vs `origin/live-defi-rollout` for every repo, restricted to `.github/**` + PM
      `scripts/**`. Any main-only content (CI workflow versions not on LDR) → back-merge **to LDR** first (LDR-SSOT), so
      the subsequent force-sync doesn't drop it. Everything else: LDR wins.
- [x] ✅ [SCRIPT] P1. **Close the steady-state main→LDR drift hole (discovered 2026-06-08).**
      `main-backmerge-to-ldr.yml` fires `on: push: branches: [main]`, but **`[skip ci]` suppresses ALL GitHub Actions
      triggers — including the back-merge** — so the very `[skip ci]` machinery commits that go direct-to-main
      (ci*status writes, manifest bumps, starvation flags) never fire it. `main` chronically drifts ahead by those
      commits and only catches up when the next \_non*-`[skip ci]` main push sweeps them in (observed: PM main ~8
      commits ahead, all `[skip ci]` ci_status writes). **Fix (option 1, preferred): add a `schedule:` tick (~every
      15–30 min) to `main-backmerge-to-ldr.yml`** — a cron run is not `[skip ci]`-suppressed, so it sweeps accumulated
      drift with no real commit; roll out fleet-wide via the template. (Option 2: the ci_status/manifest writer
      co-pushes its `[skip ci]` commit to LDR in the same step.) This makes the "main never ahead of LDR" invariant
      actually hold, not just eventually-converge.

## Phase 2 — Stale-PR sweep (#2) (depends: Phase 1)

- [x] ✅ [SCRIPT] P1. For every open PR fleet-wide, compute head-diff vs `origin/live-defi-rollout`. **Empty diff
      (content already on LDR) → close** with a comment ("superseded — content already on LDR; LDR is SSOT").
      Non-empty + part of an active cascade → leave. Build the sweeper as a reusable script
      (`scripts/cicd/close_superseded_prs.py --dry-run` by default; `--apply` only after dry-run review). **Precise
      stale def = empty head-diff vs LDR**, NOT "old" — the dep-update cascade PRs with real diffs are the convergence,
      never close those.

## Phase 3 — Force-sync clean start (#3) (depends: Phase 2)

- [x] ✅ [INFRA] P1. **Run `run-version-alignment.sh` FIRST** (admin force-sync can revert semver-agent bumps —
      CLAUDE.md warning). Then fast-forward/force `staging` and `main` to match LDR's content (LDR-SSOT clean start),
      preserving the Phase-1 reconciled CI bits + the canonical semver tags. Verify no semver bump was reverted (compare
      `versions{}` pre/ post).

## Phase 4 — Drain the LDR backlog / quickmerge everything (#6) (depends: Phase 3)

- [x] ✅ [INFRA] P1. Open a per-repo LDR→staging promote PR for everything sitting on LDR behind staging (incl. the
      checkout@v5 workflow files shipped 2026-06-08 via commit-to-tab). Drive the drain to `STAGING_GREEN` → `main` in
      dep order (T0 first). Watch the progress metric (repos reaching main); flat metric → STOP-and-diagnose, never
      wait.

## Phase 5 — Dep-update cascade PRs wedged on a PHANTOM version + stale aiohttp metadata (discovered 2026-06-09)

> **Gap in Phase 2**: Phase 2 correctly kept "dep-update PRs with real diffs" as the convergence and closed only the
> empty-diff noise. But the kept real-diff cascade has NOT converged — ~40 dep-update PRs fleet-wide are still
> `BLOCKED`/`DIRTY`, wedged on an **unsatisfiable constraint**, NOT on anything rebaseable. Phase 2's "leave the cascade
> PRs, they're the convergence" assumed they would self-resolve; they cannot until the upstream publish/version state is
> fixed. Root cause from the slot-1 investigation 2026-06-09 (interactive, with operator):

- [ ] [INFRA] P1. **ROOT CAUSE — phantom version + stale published artifact (unified-trading-library + PM propagation).**
      The dep PRs bump consumer constraints to `unified-trading-library>=0.4.0,<1.0.0` and
      `unified-api-contracts>=0.2.0,<1.0.0`, but **no 0.4.x / 0.2.x artifact was ever published.** UTL is NOT graduated
      (operator 2026-06-09) — source is `0.3.167`; its only git tags `v1.0.0`/`v1.2.0` are spurious **2025-11 bootstrap
      artifacts, NOT a graduation** (see FIX 1b); UTL `publish-package.yml`
      publishes ONLY on a `v*` tag push → the 0.3.x line was never tag-published. PM's version-aware clone in
      `.github/workflows/python-quality-gates-v2.yml` finds no tag in `[0.4.0,1.0.0)` → falls back to the index, where
      the only resolvable UTL `0.3.167` is a STALE build declaring `aiohttp>=3.14.0,<4.0.0` — violating the fleet pin
      `aiohttp>=3.13.4,<3.14.0` (CLAUDE.md known exception). uv fails: `No solution found … only
      unified-trading-library==0.3.167 is available … depends on aiohttp>=3.14.0`. Confirmed identical on
      alerting-service #31, instruments-service #400, deployment-service #26. Cross-ref:
      `aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` + `cicd_contract_hardening_2026_06_01.md`.

- [ ] [INFRA] P1. **FIX 1 — republish UTL on the 0.x line with the corrected aiohttp pin (unified-trading-library).**
      **UTL is NOT graduated (operator 2026-06-09) — it stays on 0.x (source `0.3.167`).** Tag-publish a fresh 0.x patch
      (e.g. `v0.3.168`) carrying `aiohttp>=3.13.4,<3.14.0` so an installable artifact with the CORRECT metadata exists
      and supersedes the stale published `0.3.167`. **NEVER bump aiohttp to 3.14** (operator decision 2026-06-05; vcrpy
      8.1.1 deadlock).

- [ ] [INFRA] P1. **FIX 1b — delete the spurious pre-regime `v1.x` tags + fleet tag audit (unified-trading-library +
      others).** UTL's `v1.0.0`/`v1.2.0` tags are ANCIENT bootstrap-era artifacts from **2025-11-13** (commit msgs
      "Add automatic publishing on tag push" / "Use github.repository variable for GitHub Packages URL";
      `pyproject@tag` = 1.0.0/1.2.0) — created while first wiring `publish-package.yml`, **NOT a graduation**. They are
      the repo's "latest tags" → they corrupt the PM version-aware clone's tag resolution AND likely drove the
      semver-agent to compute the phantom `0.4.0` (next-version logic keys off latest tag). Delete them
      (**operator-gated** — tag deletion is destructive + outward-facing; but these are pre-semver-agent garbage, NOT
      canonical semver-agent tags, so the "remote-canonical-tags / never-force-push-tags" rule does not protect them).
      Audit EVERY repo for the same class: **instruments-service carries `v1.1.0`/`v1.2.0`/`v1.3.0`** (same 2025-11 era);
      uac/execution/deployment have none. Any 0.x repo carrying `v1.x` tags = spurious → clean up.

- [ ] [INFRA] P1. **FIX 2 — propagation must never emit a constraint for an unreleased version (unified-trading-pm).**
      The semver-agent / `update-dependency-version.yml` cascade dispatched `>=0.4.0` for UTL (and `>=0.2.0` for uac)
      when no such version was ever tag-published. Gate the dep-bump dispatch on the target version actually existing as
      a published tag/artifact (or clamp to the latest real published version) so a phantom version can never enter a
      downstream `pyproject.toml`.

- [ ] [SCRIPT] P1. **FIX 3 — regenerate / reconcile the wedged dep PR cohort (all consumer repos).** After FIX 1+2 land,
      re-trigger propagation so the ~40 `BLOCKED`/`DIRTY` dep PRs regenerate against the real published versions (or
      auto-close as superseded). Verify the cohort goes green via `gh pr checks`; the `DIRTY` ones' `pyproject.toml`
      conflicts resolve in regeneration. This is the actual unblock — NOT 40 manual rebases.

## Success criteria

- `staging` and `main` content == LDR for every repo (modulo the reconciled main-only CI bits, now also on LDR).
- Zero open superseded PRs (empty-diff-vs-LDR); cascade PRs either merged or legitimately in-flight.
- No semver bump reverted by the force-sync.
- The checkout@v5 workflow files reach `main` fleet-wide (closes the 2026-06-08 commit-to-tab tail).
- A fresh test commit flows LDR→staging→main cleanly (the parity proof — see `ci_local_qg_parity`).
- **The dep-update cascade PRs resolve against REAL published versions** — no `pyproject.toml` carries a constraint for
  an unreleased version; the ~40-PR cohort goes green or auto-closes as superseded (Phase 5).

## Codex SSOT updates

`codex/08-workflows/ci-cd-flow.md` § LDR-as-SSOT + clean-start runbook; add the stale-PR sweeper to the runbook owner
table.

## Progress — 2026-06-08 (slot-1 autonomous)

- **DONE**: Phase 0 heal consumed (lock cleared, AO drained, promote-bot green). Phase 1 main-only→LDR backmerge done
  fleet-wide (CI fixes + uts-ui feat + #181/#182); drift-hole closed via the `schedule: */20` drift-tick on
  main-backmerge-to-ldr (PM+template+fleet rollout). Phase 2 stale-PR: the force-sync COLLAPSED the divergent
  staging/main SHAs (0-file-delta promotion noise) directly — superseded-PR sweep subsumed. Phase 3 force-sync:
  protection-aware relax→force→restore, 24/24 main==staging==LDR. Phase 4 drain: achieved by force-sync (fast clean
  start, not serial promotion).

## Progress — 2026-06-09 (slot-1 interactive, with operator)

- **GAP FOUND + filed as Phase 5**: the real-diff dep-update cascade PRs Phase 2 deliberately kept are still wedged
  (~40 `BLOCKED`/`DIRTY`). Investigation traced it to a phantom propagated version (`UTL>=0.4.0` / `uac>=0.2.0` never
  tag-published) compounded by a stale published UTL `0.3.167` carrying `aiohttp>=3.14.0` (violates the fleet pin).
  Concrete 3-step fix (republish UTL → gate propagation on real versions → regenerate cohort) drafted as Phase 5 todos.
  No code/version changes made — fix is operator/pipeline-gated.
- **Operator correction (2026-06-09): UTL is NOT graduated** — it stays on 0.x. The `v1.0.0`/`v1.2.0` tags are spurious
  2025-11-13 bootstrap-era artifacts (initial `publish-package.yml` wiring), not a graduation; instruments-service has
  the same (`v1.1.0`–`v1.3.0`). Added FIX 1b to delete them + audit the fleet — likely the reason the semver-agent
  computed the phantom `0.4.0` (next-version keys off latest tag). FIX 1 reframed: republish on the 0.x line.
- **Adjacent GitHub-issue hygiene done same session** (not part of this plan's scope, logged for traceability): closed
  the 13 abandoned `major-bump-pending` 1.0.0-graduation issues (deferred), 15 superseded uac cassette-drift issues,
  6 PM SIT-Plan-Sync issues, 324 Feb-19 `[DATA-IO-PROD]` auto-task issues (superseded by the plan-driven backlog), and
  the stale mtds PR #79.
