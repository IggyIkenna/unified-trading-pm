---
title: Staging/main clean-start from LDR-SSOT + stale-PR hygiene + LDR backlog drain
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: archived
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

> **🗄️ ARCHIVED 2026-06-18 — 0 open items; the model is live. Consolidation provenance:
> `plans/active/cicd_docs_and_consolidation_2026_06_18.md`.**

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
- [x] ✅ [INFRA] P1. **RESOLVED (2026-06-09) via FIX 4 — audited all repos for the manifest-vs-source split, found 12,
      reconciled all; `assert_version_coherence.py` (FIX 2) now guards it going forward.** **REOPENED — the "no semver
      bump reverted" verification MISSED unified-trading-library (found 2026-06-09).** The force-sync reverted UTL
      source `0.4.0`→`0.3.167` while the manifest stayed `0.4.0` (see Phase 5 FIX 1). Audit EVERY repo for the same
      manifest-vs-source split (`versions{}[repo]` ≠ source `pyproject.version`), not just UTL — the force-sync
      clobbered LDR-behind source for any repo whose semver bump hadn't reached LDR. This is the missing teeth on the
      Phase-3 verification.

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

- [x] ✅ [DONE 2026-06-11: get_version_tag ported to stdlib tuple-compare, PM@d293ddde — silent pre-uv-sync degradation
      removed; provably identical on X.Y.Z domain] [INFRA] P1. **ROOT CAUSE — phantom version + stale published artifact
      (unified-trading-library + PM propagation).** The dep PRs bump consumer constraints to
      `unified-trading-library>=0.4.0,<1.0.0` and `unified-api-contracts>=0.2.0,<1.0.0`, but **no 0.4.x / 0.2.x artifact
      was ever published.** UTL is NOT graduated (operator 2026-06-09) — source is `0.3.167`; its only git tags
      `v1.0.0`/`v1.2.0` are spurious **2025-11 bootstrap artifacts, NOT a graduation** (see FIX 1b); UTL
      `publish-package.yml` publishes ONLY on a `v*` tag push → the 0.3.x line was never tag-published. PM's
      version-aware clone in `.github/workflows/python-quality-gates-v2.yml` finds no tag in `[0.4.0,1.0.0)` → falls
      back to the index, where the only resolvable UTL `0.3.167` is a STALE build declaring `aiohttp>=3.14.0,<4.0.0` —
      violating the fleet pin `aiohttp>=3.13.4,<3.14.0` (CLAUDE.md known exception). uv fails:
      `No solution found … only     unified-trading-library==0.3.167 is available … depends on aiohttp>=3.14.0`.
      Confirmed identical on alerting-service #31, instruments-service #400, deployment-service #26. Cross-ref:
      `aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` + `cicd_contract_hardening_2026_06_01.md`.

- [x] ✅ [INFRA] P1. **FIX 1 DONE (2026-06-09) — UTL `0.4.0` published + tagged + source-coherent; systemic resolution
      blocker VERIFIED fixed.** Committed UTL source `0.3.167`→`0.4.0` to LDR (`fd8c37a6`), pushed tag `v0.4.0` →
      `publish-package.yml` run `27193522340` **succeeded** (publishes `0.4.0` with the correct `aiohttp<3.14.0` pin to
      GitHub Packages; the Nov-2025 publish failures were stale). **Verification**: re-ran QG on the previously-BLOCKED
      `deployment-service` #26 + `alerting-service` #31 — the "Install dependencies" step that used to die with
      `No solution found … only unified-trading-library==0.3.167 … aiohttp>=3.14.0` now **resolves cleanly**
      (`Resolved     207/277 packages`). UTL is now `source==tag==published==manifest==0.4.0`. **Remaining dep-PR
      failures are INDEPENDENT + pre-existing** (the dep-update branches are STALE — cut from old commits carrying e.g.
      `PipelineMode.BATCH_HYPERLIQUID_REST`, renamed to `BATCH_HYPERLIQUID` by the 2026-06-07 G0 standardisation and
      already fixed on LDR) — NOT the version cascade. **Note**: `unified-api-contracts` has the SAME phantom-tag gap
      (no `v0.2.x` tag; manifest `0.2.0` vs source `0.2.1`) but resolution falls back to its `main` clone OK, so it is
      not a hard blocker — fold its version-state reconcile into the fleet-split todo below. **Original task text
      below:** **FIX 1 — restore the force-sync-REVERTED UTL `0.4.0` forward (unified-trading-library).** **Sharper root
      cause (2026-06-09):** UTL legitimately reached `0.4.0` — PM `workspace-manifest.json` `versions{}` AND
      `staging_versions{}` both say `0.4.0`, the 40 downstream dep PRs all pin `>=0.4.0`, and UTL git history shows
      commit `5983adeb chore: align version to staging remote` setting `version="0.4.0"`. But **current UTL source is
      back at `0.3.167`** — the **2026-06-08 LDR-SSOT clean-start force-sync (Phase 3) reverted UTL's `0.4.0` source
      bump to LDR's `0.3.167`**, while the manifest kept `0.4.0` → a manifest/source split with no `v0.4.0` tag or
      installable `0.4.0` artifact anywhere. So the fix is **FORWARD** (match the manifest + the 40 PRs), not a fresh
      0.3.x: restore UTL source `pyproject` to `0.4.0` (current source ALREADY carries the correct
      `aiohttp>=3.13.4,<3.14.0` via revert `5f58be77`) → push `v0.4.0` → `publish-package.yml` publishes an installable
      `0.4.0` with correct metadata, superseding the stale `0.3.167`. **Tension to clear: "NEVER bump version manually —
      semver-agent handles all" (CLAUDE.md).** The bump already HAPPENED in the manifest; this is reconciling a
      force-sync clobber, not a fresh bump — but it still hand-produces the tag the semver-agent normally emits, so it
      needs explicit operator authorization OR a clean semver-agent re-emit. **NEVER bump aiohttp to 3.14.**

- [x] ✅ [INFRA] P1. **FIX 1b DONE (2026-06-09) — deleted 5 spurious pre-regime `v1.x` tags.** unified-trading-library
      `v1.0.0`+`v1.2.0`, instruments-service `v1.1.0`+`v1.2.0`+`v1.3.0` (all HTTP 204). Confirmed garbage by the
      manifest `_note`: "All versions reset to 0.x.x (2026-02-28); versions >=1.0.0 were aspirational." Fleet audit:
      only those two repos carried `v1.x`; all others clean. **Original task text below:** **FIX 1b — delete the
      spurious pre-regime `v1.x` tags + fleet tag audit (unified-trading-library + others).** UTL's `v1.0.0`/`v1.2.0`
      tags are ANCIENT bootstrap-era artifacts from **2025-11-13** (commit msgs "Add automatic publishing on tag push" /
      "Use github.repository variable for GitHub Packages URL"; `pyproject@tag` = 1.0.0/1.2.0) — created while first
      wiring `publish-package.yml`, **NOT a graduation**. They are the repo's "latest tags" → they corrupt the PM
      version-aware clone's tag resolution AND likely drove the semver-agent to compute the phantom `0.4.0`
      (next-version logic keys off latest tag). Delete them (**operator-gated** — tag deletion is destructive +
      outward-facing; but these are pre-semver-agent garbage, NOT canonical semver-agent tags, so the
      "remote-canonical-tags / never-force-push-tags" rule does not protect them). Audit EVERY repo for the same class:
      **instruments-service carries `v1.1.0`/`v1.2.0`/`v1.3.0`** (same 2025-11 era); uac/execution/deployment have none.
      Any 0.x repo carrying `v1.x` tags = spurious → clean up.

- [x] ✅ [INFRA] P1. **FIX 2 DONE (2026-06-09) — shipped `scripts/cicd/assert_version_coherence.py`** (read-only gate:
      asserts `versions{}`==`staging_versions{}`==source `pyproject.version` per repo; `--tags` also requires a matching
      published `vX` tag; exits 1 on any split). ruff+basedpyright clean. Run it AFTER any force-sync / clean-start —
      this is the teeth the Phase-3 "verify no semver bump reverted" check was missing. **Follow-ups DONE
      (2026-06-09):** (1) wired the gate into `admin-force-sync-all-to-main.sh` as a BLOCKING post-sync step (exits 1 +
      loud message on any split — catches a force-sync reverting a bump before it ships); (2) defense-in-depth
      `assert_dep_in_range()` added to the reusable `python-quality-gates-v2.yml` clone step — after cloning each dep it
      FAILS LOUD (`::error::` + exit 1) when the resolved version falls OUTSIDE the pinned RANGE (>=floor AND <upper,
      honoring the full range, not an exact tag) instead of silently surfacing a stale lower version, **with a dedicated
      #ci-failures Slack alert** (`SLACK_CI_WEBHOOK_URL`). YAML/bash/range-logic validated. **uv.lock finding (no action
      needed):** internal deps are already `source = { editable = "../<dep>" }` (path, NOT exact-pinned) + pyproject
      ranges; only external deps lock exact (correct reproducible-build behavior). So the "ranges not exact pins"
      concern was already satisfied for internal deps — the real gap was the clone honoring the range, now fixed.
      **Original task text below:** **FIX 2 — force-sync must NOT silently revert a published version below the manifest
      (unified-trading-pm).** Reframed 2026-06-09: the propagation was NOT wrong — it correctly emitted `UTL>=0.4.0`
      when `0.4.0` WAS the semver-agent value. The bug was the **clean-start force-sync (Phase 3) reverting source
      `version` fleet-wide to LDR's older value while the manifest kept the higher one** → a published-then-unpublished
      phantom. **Correct preventive**: add a coherence GATE to the force-sync / clean-start runbook (and a standalone
      check) that, AFTER any force-sync, asserts `versions{}[repo]` == source `pyproject.version` == latest published
      `vX` tag for EVERY repo, and BLOCKS / loud-flags any split (this is the teeth the Phase-3 "verify no semver bump
      reverted" check was missing). Cheap first step (read-only, ship now-safe): a
      `scripts/cicd/assert_version_coherence.py` that prints the fleet split table (the 13-repo audit under FIX 4).
      **Defense-in-depth** (secondary): the version-aware clone's index fallback should fail LOUD when a pinned version
      is unresolvable instead of silently surfacing a stale lower version's metadata.

- [x] ✅ [SCRIPT] P1. **FIX 3 DONE (2026-06-09) — closed all 43 stale dep-update PRs as superseded.** Rationale: the
      resolution blocker is fixed at source (UTL 0.4.0 published), the dependency-alignment gate is GREEN
      (`check-dependency-alignment.py --json` → `aligned:true`, 0 issues) so the floor bumps are NOT required, the
      branches are stale, and the service→service bumps would have created NEW phantom pins (pinning not-yet-published
      versions). Branches deleted on close; the pipeline re-propagates fresh bumps if a real version-bump fires.
      **Original task text below:** **FIX 3 — reconcile the dep cohort onto LDR (sharpened 2026-06-09; the resolution
      blocker is GONE).** Now that UTL `0.4.0` resolves, the cohort splits three ways, NOT "make 40 stale PRs green":
      (a) the constraint bumps (`UTL>=0.4.0`, `uac>=0.2.0`) are mostly **NOT on LDR yet** (deployment/alerting/execution
      LDR still pin `>=0.1.0`; instruments has `uac>=0.2.0` only) → they carry REAL diffs and must LAND on LDR
      (LDR-SSOT); (b) the existing dep-update PR **branches are STALE** (old code, pre-`BATCH_HYPERLIQUID` rename) →
      close as superseded once the bump is on LDR; (c) some repos will surface **independent pre-existing failures** on
      re-run (already-fixed on LDR) — out of scope for the cascade. **Cleanest path: re-trigger the propagation**
      (`update-repo-version.yml` version-bump for `unified-trading-library@0.4.0` + `unified-api-contracts@0.2.x`) so it
      re-emits fresh dependency-update events against CURRENT LDR (fresh PRs/commits, not the stale branches), then
      close the stale cohort. **STRATEGIC FORK (operator):** old PR-to-staging flow vs new LDR-SSOT direct-to-LDR — pick
      before mass-mutating ~20 consumer repos. Verify each via `gh pr checks` / QG; treat independent failures as
      separate findings.

- [x] ✅ [INFRA] P1. **FIX 4 DONE (2026-06-09) — reconciled all 12 manifest-vs-source version splits; coherence GREEN.**
      Source-behind (bumped source `pyproject.version` UP to manifest, direct LDR commit):
      deployment-api/deployment-service `0.1.1→0.2.0`, e2e-testing `0.1.0→0.2.0`, execution-service `0.1.1→0.2.0`,
      fund-admin/greeks/trading-agent `0.1.0→0.2.0`, instruments-service `0.1.22→0.2.0`, mtds `0.2.0→0.3.0`.
      Source-ahead (bumped manifest UP): uac `versions 0.2.0→0.2.1`, mtdseervice `versions+staging 0.4.0→0.4.1`, PM
      `staging_versions 1.2.45→1.2.48`. `assert_version_coherence.py` now reports ✅ all 24 repos coherent;
      `aligned:true` preserved. **Original task text below:** **FIX 4 — reconcile the FLEET-WIDE manifest-vs-source
      version split (13 repos; found 2026-06-09).** The 2026-06-08 clean-start force-sync reverted source
      `pyproject.version` fleet-wide while the manifest kept the semver-agent values → 13 repos split:
      deployment-api/deployment-service `0.2.0`vs`0.1.1`, execution `0.2.0`vs`0.1.1`, instruments `0.2.0`vs`0.1.22`,
      mtds `0.3.0`vs`0.2.0`, fund-admin/greeks/trading-agent/e2e `0.2.0`vs`0.1.0`, mtdseervice `0.4.0`vs`0.4.1` (source
      AHEAD), uac `0.2.0`vs`0.2.1` (source ahead), UTL fixed by FIX 1. Reconcile each FORWARD to the manifest (the SSOT)
      so `versions{}`==source==published tag per repo. `run-version-alignment.sh` handles dependency-constraint
      alignment only — NOT the repo's own `version` field — so this needs the version-bump/tag flow per repo (or the
      semver-agent re-run), not that script.

- [x] ✅ [SCRIPT] P2 (downgraded from P1 after the 2026-06-10 semantics diagnosis — do NOT blind-sync). **DONE
      2026-06-10 — extended `assert_version_coherence.py` with VESTIGIAL_SCALAR_DRIFT (repositories{}.version must ==
      versions{} when present; remedy: run-version-alignment.sh --fix or delete the field) + DEP_FLOOR_UNSATISFIABLE
      (packaging SpecifierSet: floor ≤ versions{}[dep] < ceiling, explicitly NOT floor==latest) + wired `--warn-only`
      into PM quality-gates.sh post-gates (non-blocking; blocking flip is a later ratchet) —
      unified-trading-pm@8605171b1 | verified 2026-06-10. Findings TODAY: 17 VESTIGIAL_SCALAR_DRIFT (incl. UAC 0.1.20 vs
      0.5.0, UTL 0.3.167 vs 0.4.0, PM 1.2.0 vs 1.2.69), 10 pre-existing VERSION_SPLITs (source ahead of versions{} —
      promotion lag class), 0 DEP_FLOOR_UNSATISFIABLE (all dep-edge floors satisfiable). Original task text below:**
      Workspace-manifest version-surface reconciliation, scoped by what each field MEANS: **(a) dep-edge floors
      (`repositories{}.dependencies[].version` `>=0.1.20,<1.0.0` style) are the INTENTIONAL range-pin floors — never
      "fix" them to latest** (that would defeat the pull-not-push promotion model and force consumer re-pins);
      `check-internal-version-constraints.py` already verifies satisfiability. **(b) `repositories{}.version` scalar is
      VESTIGIAL** — written only opportunistically by `run-version-alignment.sh --fix`, read only as a display fallback
      (`generate_workspace_dag.py:283`); either delete the field per-repo or extend `assert_version_coherence.py` to
      require it equals `versions{}[repo]` when present. **(c) `versions{}` vs source pyproject is the ONLY pair that
      must agree** — `assert_version_coherence.py:111` already flags it (UAC 0.5.0 vs 0.5.1 was live promotion lag,
      self-draining). Remaining concrete work: extend `assert_version_coherence.py` with (1) the
      `repositories{}.version`==`versions{}` check (or vestigial-field deletion), (2) fold in dep-edge floor
      SATISFIABILITY (floor ≤ versions{}[dep] < ceiling — explicitly NOT floor==latest), and (3) wire it `--warn-only`
      into PM QG post-gates (today it only runs inside `admin-force-sync-all-to-main.sh:750`).

- [x] ✅ [DONE 2026-06-11: get_version_tag stdlib port, PM@d293ddde — companion to L97] [INFRA] P2. **FINDING
      (2026-06-09) — `get_version_tag` in `python-quality-gates-v2.yml` is silently degraded: the Clone step runs BEFORE
      `uv sync`, so `from packaging.version import Version` fails → it returns "" → the "version-aware" clone ALWAYS
      falls back to a branch/main clone, never actually resolving to a published tag.** This is WHY the phantom could
      happen silently (no tag resolution + no range check). Discovered while fixing FIX-2's `assert_dep_in_range` (which
      now uses stdlib tuple-compare to avoid the same trap + loud-fails on out-of-range — validated green on
      alerting-service run 27199812587: `dep unified-trading-library: OK 0.3.167 satisfies     >=0.1.0,<1.0.0`). **Fix
      (deferred — behavior change, blast radius):** port `get_version_tag` to the same stdlib tuple-compare so it
      actually resolves the latest IN-RANGE published tag (floor AND upper), making the clone genuinely version-aware.
      Risk: repos would then test against the published tag instead of branch HEAD — needs a deliberate rollout, not a
      drive-by.

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

- **GAP FOUND + filed as Phase 5**: the real-diff dep-update cascade PRs Phase 2 deliberately kept are still wedged (~40
  `BLOCKED`/`DIRTY`). Investigation traced it to a phantom propagated version (`UTL>=0.4.0` / `uac>=0.2.0` never
  tag-published) compounded by a stale published UTL `0.3.167` carrying `aiohttp>=3.14.0` (violates the fleet pin).
  Concrete 3-step fix (republish UTL → gate propagation on real versions → regenerate cohort) drafted as Phase 5 todos.
  No code/version changes made — fix is operator/pipeline-gated.
- **EXECUTED 2026-06-09 (slot-1, operator-authorized full forward repair)**: FIX 1b ✅ (5 spurious `v1.x` tags deleted),
  FIX 1 ✅ (UTL `0.4.0` committed `fd8c37a6` + tag `v0.4.0` + `publish-package.yml` success → systemic resolution
  blocker VERIFIED gone: blocked PR re-runs now `Resolved 207/277 packages`, no `No solution found`). Remaining dep-PR
  failures are INDEPENDENT/pre-existing (stale branches carrying pre-`BATCH_HYPERLIQUID`-rename code, already fixed on
  LDR) — NOT the cascade. FIX 2 reframed (force-sync coherence gate, not propagation), FIX 3 sharpened (per-repo LDR
  reconciliation + strategic fork), FIX 4 added (fleet-wide 13-repo manifest/source split). 2/4 keystone items done; the
  rest are the larger reconciliation, scoped as todos.
- **ALL REMAINING FIXES EXECUTED 2026-06-09 (slot-1, operator-authorized)**: FIX 2 ✅ (`assert_version_coherence.py`
  shipped, ruff+basedpyright clean), FIX 3 ✅ (43 stale dep-update PRs closed as superseded — resolution fixed at source
  - alignment green make the floor bumps unneeded), FIX 4 ✅ (12 manifest/source version splits reconciled → coherence
    check GREEN, alignment still `aligned:true`). FIX 3 chose LDR-SSOT-direct over old PR-to-staging (workspace SSOT is
    LDR). Net: dep cascade fully unjammed, fleet version state coherent, recurrence guard in place. Residual follow-ups
    (non-blocking): wire the coherence gate into the force-sync runbook; loud-fail defense-in-depth in the version-aware
    clone.
- **Operator correction (2026-06-09): UTL is NOT graduated** — it stays on 0.x. The `v1.0.0`/`v1.2.0` tags are spurious
  2025-11-13 bootstrap-era artifacts (initial `publish-package.yml` wiring), not a graduation; instruments-service has
  the same (`v1.1.0`–`v1.3.0`). Added FIX 1b to delete them + audit the fleet — likely the reason the semver-agent
  computed the phantom `0.4.0` (next-version keys off latest tag). FIX 1 reframed: republish on the 0.x line.
- **Adjacent GitHub-issue hygiene done same session** (not part of this plan's scope, logged for traceability): closed
  the 13 abandoned `major-bump-pending` 1.0.0-graduation issues (deferred), 15 superseded uac cassette-drift issues, 6
  PM SIT-Plan-Sync issues, 324 Feb-19 `[DATA-IO-PROD]` auto-task issues (superseded by the plan-driven backlog), and the
  stale mtds PR #79.
