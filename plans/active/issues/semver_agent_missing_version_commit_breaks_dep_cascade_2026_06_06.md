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
- [ ] [SCRIPT] P0. Deploy updated `semver-agent.yml` to all fleet repos via `scripts/rollout-semver-agent.sh` (verify
      `contents: write` + the new "Apply version bump to staging" step landed on each repo's staging). PM #149 fixed the
      TEMPLATE; the per-repo live workflows still lack the step until rolled out.
- [ ] [SCRIPT] P1. `update-dependency-version.yml`: relock `uv.lock` after the constraint bump (or document why the
      path-source makes it unnecessary). Target: `scripts/workflow-templates/update-dependency-version.yml` +
      `scripts/propagation/templates/update-dependency-version.yml` (de-drift the two copies in the same change).
- [ ] [SCRIPT] P1. Collapse the triple `semver-agent` template drift to ONE SSOT + ONE rollout script; delete the dead
      `scripts/templates/semver-agent.yml`.
- [ ] [SCRIPT] P2. `python-quality-gates-v2.yml` dep-clone: when `DEP_BRANCH` (the head dep-update branch) does not
      exist in a dep repo, fall back to that dep's CURRENT computed version/tag rather than silently to `main` — so the
      tested dep version is explicit.
- [ ] [SCRIPT] P1. **PM's own `uv.lock` drifts on every PM version bump** (same class as the dep-update relock gap):
      `update-repo-version.yml` bumps PM `pyproject.toml` (e.g. 1.2.0→1.2.3→1.2.4 on #149 merge) but never relocks
      `uv.lock`, so `uv lock --check` fails the PM gate fleet-wide until a human relocks. Observed twice this session
      (relocked 1.2.0→1.2.3, then 1.2.3→1.2.4). Add a `uv lock` + commit step to `update-repo-version.yml` after the
      `sed` PM version bump.
