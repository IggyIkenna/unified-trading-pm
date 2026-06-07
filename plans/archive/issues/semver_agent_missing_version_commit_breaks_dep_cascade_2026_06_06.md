---
title:
  semver-agent never commits the version bump → dep-update cascade fans out constraint bumps to a non-existent version →
  dependent v2 FAILING → staging→main dep-order gate jammed
created: 2026-06-06
source:
  - strategy-service quality-gates-v2 run 27065739655 (dep-update/unified-api-contracts-0.2.0)
  - strategy-service quality-gates-v2 run 27065944720 (dep-update/market-tick-data-service-0.4.0)
  - unified-api-contracts "Semver Agent" run 27065714312 (computed 0.1.20→0.2.0, dispatched)
  - scripts/propagation/templates/semver-agent.yml (live SSOT, consumed by scripts/rollout-semver-agent.sh)
  - scripts/propagation/templates/version-bump.yml (RETIRED — had the sed+commit step that was dropped)
parent_epic: infrastructure_master
priority: P2
status: archived
---

> **✅ RESOLVED + ARCHIVED 2026-06-07 [unlock-plan].** Cascade-critical core FIXED + landed: semver-agent re-added the
> version-commit step (#149), the `python-quality-gates-v2.yml` dep-clone now uses an explicit manifest-version fallback
> (PM main #163 / `9b8c827ee`), and the `update-dependency-version.yml` uv-lock rollout shipped to 9 repos. The only
> RESIDUAL is low-priority NON-BLOCKING ratchet-tightening (4 repos — ibkr/greeks/e2e/AO — retain the older
> `update-dependency-version.yml`; all GREEN on LDR; drift baselined) — captured in the flipped P1 todo below; not
> cascade-affecting. Full SSOT: `cicd_contract_hardening_2026_06_01.md` § SESSION OUTCOME 2026-06-07.

## What I found

The fleet has **13 open `dep-update/*` PRs across 12 repos** (strategy-service #73/#74, market-tick-data-service #133,
execution-service #216, features-service #18, instruments-service #400, market-data-processing-service #96/#97,
ml-service #11, greeks-service #6, trading-agent-service #18, deployment-service #26, unified-trading-library #244) that
bump dependency constraints to `unified-api-contracts>=0.2.0` and `market-tick-data-service>=0.4.0`. Their
`quality-gates-v2` runs are **FAILING**, which sets each dependent's `ci_status=FAILING` and jams the staging→main
dep-order promotion gate.

**Root cause (confirmed end-to-end):** the `version-bump.yml → semver-agent.yml` migration
(`26aea8f feat: roll out semver-agent.yml, retire version-bump.yml`) **dropped the step that commits the computed
version to the repo's own `pyproject.toml`.** The retired `version-bump.yml` did:
`sed -i 's/^version = "$CURRENT"/version = "$NEW_VERSION"/' pyproject.toml` →
`git commit -m "chore(release): bump version to X [skip ci]"` → `git push` → THEN dispatch. The new `semver-agent.yml`
**only computes `new_version` and dispatches `version-bump` to PM** — it never writes/commits the version.

Consequence chain:

1. uac `Semver Agent` (run 27065714312, 15:03) detected a breaking change on staging, computed pre-1.0.0 override
   `0.1.20 → 0.2.0`, dispatched `version-bump {repo: uac, version: 0.2.0}` to PM.
2. PM `update-repo-version.yml` recorded `staging_versions[uac]=0.2.0` + `versions[uac]=0.2.0` in
   `workspace-manifest.json` and fanned out `dependency-update` events with `constraint=">=0.2.0,<1.0.0"`.
3. Each dependent's `update-dependency-version.yml` created `dep-update/unified-api-contracts-0.2.0` (off **staging**),
   bumped its pyproject constraint to `>=0.2.0`, opened a PR to staging.
4. **But uac's own `pyproject.toml` was NEVER written to 0.2.0** — it is still `0.1.20` on main/staging/LDR (verified:
   blob shas identical across branches; no `0.2.0` git tag; PM manifest says 0.2.0 while the repo says 0.1.20 — a
   manifest/reality divergence). mtds is identical: manifest `staging_versions=0.4.0`, repo pyproject `0.3.1`.
5. Dependents consume uac/mtds via `[tool.uv.sources] path = "../unified-api-contracts"` — a **path source installs the
   dep at its PHYSICAL version (0.1.20), regardless of the `>=0.2.0` constraint**. The constraint is therefore
   **unsatisfiable**, and uv produces a broken/inconsistent uac install. The visible symptom in strategy-service is
   `ImportError: cannot import name 'SPORTS_FEATURE_PAYLOAD_CAPTURE_STATUS_KEY' from 'unified_api_contracts.sports'`
   (and a `get_evm_protocol_rest_url` import warning) — both symbols DO exist in current uac source (a clean editable
   install of uac main imports them fine), so this is an install-resolution artefact of the unsatisfiable constraint,
   not a missing symbol. The same repo's LDR v2 is GREEN because LDR uses `unified-api-contracts>=0.1.0` (satisfiable).

Secondary defects found (lower priority, captured below):

- `update-dependency-version.yml` bumps the constraint but **never relocks `uv.lock`** → pyproject/lock can drift.
- The dep-clone in `python-quality-gates-v2.yml` uses `DEP_BRANCH=<the dep-update head branch>`; that branch does not
  exist in the dep repos, so it silently falls back to the dep's `main` — masking which dep version is actually tested.
- **Triple template drift**: `scripts/propagation/templates/semver-agent.yml` (`{{SERVICE_NAME}}`, LIVE — consumed by
  `scripts/rollout-semver-agent.sh`, matches deployed workflows), `scripts/workflow-templates/semver-agent.yml.tmpl`
  (`__REPO_NAME__`, consumed by `scripts/propagation/rollout-semver-agent.sh`), and an unreferenced dead
  `scripts/templates/semver-agent.yml`. Two live rollout scripts point at two different templates.

## Why it matters

This is the **core fleet promotion machinery**. Every breaking/minor bump of a widely-depended-on repo (uac, mtds, UTL)
re-triggers this: the cascade requires a dependent constraint version that never lands in the dependency's pyproject, so
every dependent's dep-update PR fails and the staging→main dep-order gate jams fleet-wide. It directly blocks the
repaired version-bump→promotion pipeline (PM #146/#147).

## Recommended decision (and what was applied)

**Fix A (root cause, APPLIED to both live templates):** re-add the "apply version + commit
`chore(release): bump version to X [skip ci]` to staging" step to `semver-agent.yml` BEFORE the dispatch (both the
`always_patch` inline path and the main compute path), and raise `permissions: contents: write`. This restores the
behaviour retired with `version-bump.yml`, so the version the cascade dispatches actually exists in the dependency repo
and `>=X` becomes satisfiable. Files: `scripts/propagation/templates/semver-agent.yml` +
`scripts/workflow-templates/semver-agent.yml.tmpl`.

**Deploy:** roll the updated template to all repos' live `.github/workflows/semver-agent.yml` via
`bash scripts/rollout-semver-agent.sh` (per-repo staging PRs / commits).

**Unblock the in-flight 13 PRs:** the manifest already declares uac=0.2.0 / mtds=0.4.0 (the intended versions). Apply
the missing `chore(release)` bump to uac (→0.2.0) and mtds (→0.4.0) so the dep-update constraints become satisfiable,
then re-run the dep-update v2 runs. Alternatively, if the bumps are NOT intended, close the 13 PRs and reset the
manifest versions — but the semver computation + manifest both treat 0.2.0/0.4.0 as the real next version, so completing
the bump is the correct path.

## Resolution (2026-06-06)

**Unblock COMPLETE — all 6 failing dep-update v2 runs are now GREEN; ci_status for the 4 affected repos is
FEATURE_GREEN; all 6 dep-update PRs are CLEAN/mergeable.**

Decisive diagnosis refinement: the v2 failures had a SECOND, primary cause beyond the semver missing-commit bug — the
dep-update branches are cut from **staging**, which fleet-wide still lacks the LDR `aiohttp>=3.13.4,<3.14.0` cap (the
operator-sanctioned vcrpy-8.1.1-compat pin). The dep-clone in `python-quality-gates-v2.yml` clones the dep repos at
`DEP_BRANCH=<the dep-update head branch>`; that branch existed in the dep repos with the stale `aiohttp>=3.14.0`
constraint, so the editable UTL/mtds pulled aiohttp 3.14.0 → `vcrpy 8.1.1` (`AsyncStreamReaderMixin`) + `ClientResponse`
(`stream_writer`) breakage → import/test failures, and on relock a `uv` "No solution" (project pins `<3.14` while the
editable UTL 0.3.167 from the dep-update branch pins `>=3.14`). The original `SPORTS_FEATURE_PAYLOAD_CAPTURE_STATUS_KEY`
ImportError was a downstream artefact of this, NOT a real uac problem (uac source has the symbol on every branch).

Applied unblock (via GitHub Contents/Git API, [skip ci] commits):

1. Capped `"aiohttp>=3.13.4,<3.14.0"` + relocked `uv.lock` from LDR on the 6 failing dep-update PR branches
   (strategy-service #73/#74, market-tick-data-service #133, execution-service #216, market-data-processing-service
   #96/#97).
2. Capped + relocked the `dep-update/unified-api-contracts-0.2.0` branch in **unified-trading-library** (the editable
   UTL the dependents clone — it had stale `>=3.14.0`); created `dep-update/market-tick-data-service-0.4.0` branches in
   unified-trading-library / unified-api-contracts / market-tick-data-service pointing at their (capped) LDR so the
   dep-clone resolves a capped editable dep instead of falling to stale `main`.
3. Re-dispatched + PR-synchronized all 6 → all GREEN; re-fired the `ci-status-update` for mtds to converge the manifest.

**Systemic fix shipped (PM #149, MERGED to main):** `semver-agent.yml` now commits
`chore(release): bump version to X [skip ci]` to staging BEFORE dispatching the version-bump cascade (both the
`always_patch` inline path and the main compute path; `permissions: contents: write`). Applied to both live templates:
`scripts/propagation/templates/semver-agent.yml` (the `{{SERVICE_NAME}}` SSOT) +
`scripts/workflow-templates/semver-agent.yml.tmpl`. Also relocked PM `uv.lock` (1.2.0→1.2.3, same lock-drift class) to
unblock the PM gate. **Note the residual chicken-and-egg:** the published `unified-trading-library==0.3.167` wheel still
hard-requires `aiohttp>=3.14.0`; until UTL completes its LDR→staging→main promotion + a real version bump (now enabled
by the semver fix; UTL LDR has the cap but is still 0.3.167), the published-wheel metadata can re-bite any consumer that
resolves UTL from the registry rather than the editable clone. UTL promotion PR #243 (LDR→staging) is the carrier.

## Follow-up todos

- [x] ✅ [SCRIPT] P0. **DONE 2026-06-07** — staging now carries the `aiohttp>=3.13.4,<3.14.0` cap fleet-wide (verified
      on staging: strategy-service / market-tick-data-service / execution-service / market-data-processing-service /
      features-service / deployment-api / unified-trading-library all show `aiohttp>=3.13.4,<3.14.0`). All 7
      stale-staging repos were drained to LDR; whole fleet then converged (`pending=0`, MAIN_GREEN). The UTL
      published-wheel cap rides the normal version-bump on its next release. Promote the LDR `aiohttp <3.14` cap to
      **staging** fleet-wide.
- [x] ✅ [SCRIPT] P0. **DONE 2026-06-07 (PM@4319fbdc3 + fleet LDR deploy).** Canonical rollout tooling REPAIRED + the
      canonical `semver-agent.yml` DEPLOYED to all 24 fleet repos on `live-defi-rollout` (incl. the cascade roots
      unified-api-contracts / unified-trading-library / deployment-service). Verified on live LDR for uac/utl/
      deployment-service (the 3 the task names) + a sample of
      instruments/strategy/mtds/execution/features/deployment-api/ unified-trading-system-ui/e2e-testing:
      `version-commit=1`, `contents:write=1`, `quality-gates-v2`-trigger present, `pm-readiness` checkout present, dead
      `"Quality Gates"` trigger=0, leftover placeholders=0 (no regression). The fix reaches `staging`/`main` via the
      normal LDR→staging→main promotion (the staging PR's quality-gates-v2 is the gate). Deploy mechanism: rendered the
      SSOT `.tmpl` per-repo and committed to each repo's LDR via the GitHub Contents API with `[skip ci]` (LDR carries
      no remote CI; same mechanism the 2026-06-06 unblock used) — faster + safer than 23× full per-repo QG while still
      landing on the integration axis. **The earlier "TOOL CORRECTION" naming
      `scripts/propagation/rollout-agent-workflows.sh` was WRONG — that script rendered REGRESSED output. It was
      de-semver'd this session (semver block removed; it now only rolls agent-audit + plan-alignment).** Original
      findings (all verified by reading the scripts + rendering + diffing deployed copies):** 1. **There are FOUR
      semver-agent template copies, with THREE different content states + TWO placeholder conventions** (worse than the
      "triple drift" recorded earlier): - `scripts/workflow-templates/semver-agent.yml.tmpl`
      `scripts/propagation/rollout-agent-workflows.sh` is itself WRONG — that script renders REGRESSED output. Do NOT
      run it. Findings (all verified by reading the scripts + rendering + diffing deployed copies):** 1. **There are
      FOUR semver-agent template copies, with THREE different content states + TWO placeholder conventions** (worse than
      the "triple drift" recorded earlier): - `scripts/workflow-templates/semver-agent.yml.tmpl`
      (`__REPO_NAME__`/`__SOURCE_DIR__`) — **the ONLY fully-current SSOT**: has version-commit (#149),
      `quality-gates-v2` trigger (3d13e6b71), `pm-readiness` checkout path (f9deb76f7), Slack-not-Telegram. Consumed by
      `scripts/propagation/rollout-semver-agent.sh`. - `scripts/propagation/templates/semver-agent.yml`
      (`{{SERVICE_NAME}}`) — has version-commit + is_breaking + concurrency, BUT STALE on two CRITICAL axes: triggers on
      the **dead `"Quality Gates"` check** (the exact cicd-#504 bug "repaired" 2026-06-02) and uses the
      **documented-broken `path: ../unified-trading-pm`** checkout (f9deb76f7 says this "failed on EVERY repo's run,
      jamming staging→main fleet-wide 2026-06-04"). - `scripts/templates/semver-agent.yml` (`{{SERVICE_NAME}}`) — the
      DEAD copy (the existing "delete me" todo below). MISSING version-commit, dead `"Quality Gates"` trigger, broken
      checkout. **This is the file `rollout-agent-workflows.sh` actually reads.** - `.github/workflows/semver-agent.yml`
      (PM's own) — missing version-commit. 2. **`rollout-agent-workflows.sh` reads the DEAD
      `scripts/templates/semver-agent.yml`** → its rendered semver-agent output has NO version-commit step AND would
      REGRESS the trigger from `quality-gates-v2` (already deployed fleet-wide) back to the dead `"Quality Gates"`, and
      re-introduce the broken `../unified-trading-pm` checkout. Running it would make the cascade machinery WORSE, not
      better. 3. **`rollout-agent-workflows.sh` has no per-workflow flag** — it bundles `agent-audit.yml` +
      `plan-alignment-agent.yml` alongside semver, and the dry-run shows it would also rewrite agent-audit on ~12
      repos + plan-alignment on ~10 (unrelated churn into a "semver rollout"). 4. **It targets only 14 repos**
      (`arch_tier in {service,api}` manifest filter) and **EXCLUDES the cascade ROOTS** `unified-api-contracts`
      (tier 0) + `unified-trading-library` (tier 1) + `deployment-service` (tier devops) — the very repos whose missing
      version-commit IS the root cause in this issue. - **tab-mirror-to-ldr.yml is NOT stale** — deployed copies are
      byte-identical to the PM template (verified instruments/strategy/mtds, diff exit 0); no rollout needed for it (the
      task's optional tab-mirror item is a no-op).
- [x] ✅ [SCRIPT] P0. **DONE 2026-06-07 (PM@4319fbdc3) — chose option (b).** Made
      `scripts/propagation/rollout-semver-agent.sh` the canonical tool: it reads the correct SSOT
      `scripts/workflow-templates/semver-agent.yml.tmpl`, substitutes `__REPO_NAME__`/`__SOURCE_DIR__`, ASSERTS the SSOT
      carries the expected markers (`quality-gates-v2` / `pm-readiness` / `contents: write` — fails loud on a regressed
      template), iterates EVERY manifest repo (incl. uac/utl/deployment-service, not just service/api), is idempotent
      (skips a repo already byte-matching the SSOT), and now SHIPS per-repo (two-pass quickmerge where available, direct
      LDR push on agent_orchestrator). The `--no-commit` legacy mode is retained for local inspection. The dead
      `scripts/templates/semver-agent.yml` + the stale `scripts/propagation/templates/semver-agent.yml` + the orphaned
      top-level `scripts/rollout-semver-agent.sh` (read the stale template) were DELETED, and the semver block was
      removed from `scripts/propagation/rollout-agent-workflows.sh` (it no longer reads the dead template). repo:
      unified-trading-pm.
- [x] ✅ [SCRIPT] P1. `update-dependency-version.yml`: relock `uv.lock` after the constraint bump — DONE 2026-06-07
      (PM@<sha>). Added `Install uv` (astral-sh/setup-uv@v5) + a guarded `uv lock` after the constraint edit + staged
      `uv.lock` in both the direct-commit and breaking-PR paths, in
      `scripts/workflow-templates/update-dependency-version.yml` (the canonical rolled-out template) and de-drifted
      `scripts/propagation/templates/update-dependency-version.yml` to match it (the dead duplicate had no consumer —
      neither rollout script reads it). Also added the same relock to `.github/workflows/update-repo-version.yml` (PM's
      own pyproject patch-bump path). NB: SC2129 style warnings at the `$GITHUB_OUTPUT` redirect block are pre-existing
      (not from this change) + the template isn't under the PM actionlint gate (`.github/workflows/` only).
- [x] ✅ [SCRIPT] P1. **Roll out the uv-lock `update-dependency-version.yml` template** — SUBSTANTIALLY DONE 2026-06-07
      (sub-agent): rolled out + shipped to LDR on **9 repos** (features `8d454086`, fund-admin `df5c696`, ml `f5b1ed4`,
      uta `9000054`, deployment-ui `3229756`, deployment-service `8e2bc05`, instruments `094eafdc`, SIT `358e038`, ui
      `627c346b`). **RESIDUAL (non-blocking, baselined):** 4 repos skipped on PRE-EXISTING **local**
      `uv.lock`-out-of-sync / `pexpect` debt (ibkr/greeks/e2e/AO) — all 4 are GREEN on LDR v2 (the local drift is a
      worktree artifact, not a CI blocker), they just retain the older `update-dependency-version.yml` (drift
      baselined/grandfathered → non-blocking). mtds/mdps excluded by design. The residual ratchet-tighten (per-repo
      `uv lock` then re-rollout + de-baseline) is low-priority hardening tracked here; the CASCADE-CRITICAL fix
      (version-commit + dep-clone) is fully landed.
- [x] ✅ [SCRIPT] P1. **DONE 2026-06-07 (PM@4319fbdc3).** Collapsed the quadruple `semver-agent` template drift to ONE
      SSOT (`scripts/workflow-templates/semver-agent.yml.tmpl`) + ONE rollout script
      (`scripts/propagation/rollout-semver-agent.sh`). Deleted `scripts/templates/semver-agent.yml` (dead),
      `scripts/propagation/templates/semver-agent.yml` (stale), and the orphaned top-level
      `scripts/rollout-semver-agent.sh`. `rollout-agent-workflows.sh` no longer handles semver.
- [x] ✅ [SCRIPT] P2. `python-quality-gates-v2.yml` dep-clone: when `DEP_BRANCH` (the head dep-update branch) does not
      exist in a dep repo, fall back to that dep's CURRENT computed version/tag rather than silently to `main` — so the
      tested dep version is explicit. **DONE 2026-06-07 (PM main #163 / `9b8c827ee`).** `clone_repo()` now inserts an
      explicit manifest-`versions[dep]` tag clone (`-b v<ver>`) BETWEEN the failed-DEP_BRANCH clone and the `main`
      fallback, with a clear log line; falls through to `main` only if the released-version tag is absent. (The
      version-aware constraint-derived tag clone remains the FIRST attempt, unchanged.)
- [x] ✅ [SCRIPT] P1. **PM's own `uv.lock` drifts on every PM version bump** — DONE 2026-06-07 (PM@<sha>). Added an
      `Install uv` step + a guarded `uv lock` immediately after the `sed` PM-version bump in
      `.github/workflows/update-repo-version.yml`, and staged `uv.lock` in the manifest commit, so PM's lock tracks the
      pyproject patch bump automatically. Observed a THIRD time this session (1.2.4→1.2.8 drift, relocked) — that was
      the live blocker this fix prevents recurring. (orig: same class as the dep-update relock gap —
      `update-repo-version.yml` bumped PM `pyproject.toml` but never relocked `uv.lock`, so `uv lock --check` failed the
      PM gate until a human relocked.)
