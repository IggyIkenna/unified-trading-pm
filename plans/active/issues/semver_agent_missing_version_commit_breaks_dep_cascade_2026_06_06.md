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
locked_by: live-defi-rollout
parent_epic: infrastructure_master
priority: P2
status: active
---

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

- [ ] [SCRIPT] P0. Promote the LDR `aiohttp <3.14` cap to **staging** fleet-wide (strategy-service,
      market-tick-data-service, execution-service, market-data-processing-service, unified-trading-library — staging
      lacks the cap; that is why dep-update branches inherit the bad constraint). Drive UTL LDR→staging→main (PR #243) +
      a UTL version bump > 0.3.167 so the published wheel caps aiohttp; then future dep-update branches need no manual
      cap.
- [ ] [SCRIPT] P0. **BLOCKED — canonical rollout tooling is broken; must repair BEFORE deploy (verified 2026-06-07,
      slot-1).** Deploy updated `semver-agent.yml` to all fleet repos (verify `contents: write` + the new "Apply version
      bump to staging" step landed on each repo's staging). PM #149 fixed the TEMPLATE(s); the per-repo live workflows
      still lack the version-commit step (verified: instruments/strategy/mtds/uac/utl/deployment-service LDR copies all
      have `version-commit=0`). **The 2026-06-07 "TOOL CORRECTION" naming
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
- [ ] [SCRIPT] P0. **Repair the canonical rollout path so the deploy above can run** (prereq for the deploy P0). Either
      (a) point `scripts/propagation/rollout-agent-workflows.sh`'s semver `TEMPLATES_DIR` at a fully-current
      `{{SERVICE_NAME}}` SSOT and first SYNC that SSOT to match `scripts/workflow-templates/semver-agent.yml.tmpl` (port
      the `quality-gates-v2` trigger + `pm-readiness` checkout into `scripts/propagation/templates/semver-agent.yml`),
      OR (b) make `scripts/propagation/rollout-semver-agent.sh` (which already reads the correct `.tmpl` + substitutes
      `__REPO_NAME__`/`__SOURCE_DIR__` correctly — the "cp-only/literal-placeholder" claim is FALSE, it does `sed`) the
      canonical tool by adding the per-repo commit/push it currently lacks. Then collapse to ONE SSOT + ONE script (see
      the P1 consolidation todo below) and delete the dead `scripts/templates/semver-agent.yml`. Roll out to the FULL
      set incl. uac/utl/deployment-service, not just the 14 service/api repos. repo: unified-trading-pm.
- [x] ✅ [SCRIPT] P1. `update-dependency-version.yml`: relock `uv.lock` after the constraint bump — DONE 2026-06-07
      (PM@<sha>). Added `Install uv` (astral-sh/setup-uv@v5) + a guarded `uv lock` after the constraint edit + staged
      `uv.lock` in both the direct-commit and breaking-PR paths, in
      `scripts/workflow-templates/update-dependency-version.yml` (the canonical rolled-out template) and de-drifted
      `scripts/propagation/templates/update-dependency-version.yml` to match it (the dead duplicate had no consumer —
      neither rollout script reads it). Also added the same relock to `.github/workflows/update-repo-version.yml` (PM's
      own pyproject patch-bump path). NB: SC2129 style warnings at the `$GITHUB_OUTPUT` redirect block are pre-existing
      (not from this change) + the template isn't under the PM actionlint gate (`.github/workflows/` only).
- [ ] [SCRIPT] P1. **Roll out the uv-lock `update-dependency-version.yml` template to the 24 fleet repos** (ratchet the
      drift baseline back down). The template change above made the rolled-out copy diverge from all 24 repos' live
      copies → the PM QG `detect_template_drift.py --workflows` ratchet was `--baseline-write`-grandfathered 2026-06-07
      (24 `update-dependency-version.yml` entries in `workflow_template_drift_baseline.json`) so the template fix could
      land. The deploy (`rollout-workflow-templates.sh --template update-dependency-version.yml` → per-repo commit) is
      cross-repo (sibling repos, fleet-drain loop); each rolled-out repo should be REMOVED from the baseline so the
      ratchet tightens. repo: unified-trading-pm template + 24 sibling repos.
- [ ] [SCRIPT] P1. Collapse the triple `semver-agent` template drift to ONE SSOT + ONE rollout script; delete the dead
      `scripts/templates/semver-agent.yml`.
- [ ] [SCRIPT] P2. `python-quality-gates-v2.yml` dep-clone: when `DEP_BRANCH` (the head dep-update branch) does not
      exist in a dep repo, fall back to that dep's CURRENT computed version/tag rather than silently to `main` — so the
      tested dep version is explicit.
- [x] ✅ [SCRIPT] P1. **PM's own `uv.lock` drifts on every PM version bump** — DONE 2026-06-07 (PM@<sha>). Added an
      `Install uv` step + a guarded `uv lock` immediately after the `sed` PM-version bump in
      `.github/workflows/update-repo-version.yml`, and staged `uv.lock` in the manifest commit, so PM's lock tracks the
      pyproject patch bump automatically. Observed a THIRD time this session (1.2.4→1.2.8 drift, relocked) — that was
      the live blocker this fix prevents recurring. (orig: same class as the dep-update relock gap —
      `update-repo-version.yml` bumped PM `pyproject.toml` but never relocked `uv.lock`, so `uv lock --check` failed the
      PM gate until a human relocked.)
