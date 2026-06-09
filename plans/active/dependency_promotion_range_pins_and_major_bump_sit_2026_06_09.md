---
title: "Dependency promotion — range pins absorb minor/patch, only MAJOR forces rebuild (full SIT in dep order)"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
created: 2026-06-09
source:
  - operator design direction 2026-06-09 ("why are we locking to minor versions… ranges >0.0.1<1… only major bumps force
    uv lock changes… major bumps trigger full SIT in dep order else escalate to vm-planning")
  - plans/active/cicd_contract_hardening_2026_06_01.md § "CORRECTION + ADDENDUM 2026-06-09" (UAC 0.1.20-vs-0.2.1 split
    that surfaced this)
---

# Dependency promotion — range pins absorb minor/patch; only MAJOR forces a consumer rebuild

## The model (operator, 2026-06-09)

**`uv.lock` is already correct — do NOT "fix" it (operator clarification 2026-06-09).** Internal deps (UTL/UAC) are
recorded as `source = { editable = "../unified-api-contracts" }` (path/editable, NOT an exact version pin — the recorded
`version =` is just a snapshot; the install resolves from the source path regardless), while EXTERNAL deps lock exact
(correct lockfile behavior) and the `pyproject` constraint stays a range (`aiohttp>=3.13.4,<3.14.0`). So there is no
exact-pin bug in the lockfile. The substantive **"honor ranges" gap was the version-aware clone** — which version/branch
of an internal dep a consumer's CI clones — and that is **already closed by the loud-fail** preflight
(`setup-workspace-from-manifest.sh:139/305` hard-fails a required dep clone; quickmerge's dep-clone fallback
`clone -b staging → -b main`, `quickmerge.sh:1301`). The MTDS "version-alignment red" was that loud-fail correctly
firing on the UAC `main(0.1.20)`-vs-`staging(0.2.1)` SPLIT — healed by promoting UAC `staging→main` (PR #108), not by
any lockfile change.

**Target dependency-promotion contract:**

- **Declared pins are RANGES** `>=0.x,<1.0.0` (already true fleet-wide — `pyproject.toml` +
  `workspace-constraints.toml`).
- **minor/patch bumps are backward-compatible BY DESIGN** → absorbed by the range → **NO consumer rebuild, NO CI
  noise**. A consumer picks up the newer dep only when IT next goes through its own promote workflow (and passes QG at
  that point). Downside accepted: a consumer's build can lag the latest dep; upside: prod is stable + intermediate
  builds don't thrash CI. The operator asks for a promote when they want the newer dep — promotion is pull, not push.
- **MAJOR bumps are breaking** → they violate the consumer's `<1.0.0` range → the consumer MUST deliberately update its
  pin → **rebuild is forced**. A major bump **triggers a full SIT in dependency order** to verify every dependent still
  passes QG against the new major; if SIT passes → promote proceeds; if the staging workflow gets **stuck**, **escalate
  to vm-planning** (the orchestrator) to resolve.
- **What counts as MAJOR vs MINOR is decided by the breaking-change matrix** — the AST public-surface differ
  (`scripts/cicd/detect_breaking_change.py`) + a plan-documented schema/API-contract matrix, refined deliberately (not a
  version-phase heuristic). SSOT for "breaking = public-surface change": `codex/08-workflows/ci-cd-flow.md` § "Breaking
  = public-surface change, NOT version phase".

**How the range is honored (the part that IS still work):** with editable internal deps + range pins, a minor/patch
internal bump is absorbed silently — the consumer keeps building against whatever it cloned until IT next promotes
(pull, not push). A **MAJOR** bump crosses the consumer's `<1.0.0` ceiling → the editable source no longer satisfies the
constraint → the version-aware clone / resolution surfaces it. That MAJOR signal must **fire a cascade of quality gates
(full SIT in dependency order)** across dependents, and **vm-planning is escalated ONLY if that cascade FAILS** — if the
gates pass, the major promotes automatically with no human/vm-planning involvement. minor/patch never fire the cascade.

## What's already in place (verified 2026-06-09)

- ✅ Declared pins are ranges: MTDS `unified-api-contracts>=0.1.0,<1.0.0` +
  `[tool.uv.sources] path = "../unified-api-contracts"` editable; `workspace-constraints.toml` matches.
- ✅ `uv.lock` is CORRECT: internal deps `source = { editable = "../…" }` (no exact pin), external deps exact
  (reproducibility). **No lockfile fix needed** (operator clarification 2026-06-09 — earlier "range-aware lock gate"
  framing was a non-problem; do not implement it).
- ✅ External dep-alignment check ALREADY exempts internal packages (`check_external_dependency_alignment.py`: "internal
  packages — never in PyPI — skip them").
- ✅ The "honor ranges" gap (version-aware clone) is CLOSED by the loud-fail preflight
  (`setup-workspace-from-manifest.sh:139/305`; quickmerge fallback `clone -b staging → -b main`, `quickmerge.sh:1301`).
- ✅ Breaking-change differ exists (`detect_breaking_change.py`) + SIT/cascade-lock fire on real public-surface change.
- ✅ UAC `main(0.1.20)`-vs-`staging(0.2.1)` split healed by PR #108 (the actual cause of the MTDS loud-fail).
- ❌ No "MAJOR bump → cascade of quality gates (full SIT in dep order) → escalate to vm-planning ONLY IF the cascade
  fails" wiring. **This is the remaining work.**

## Phases

### Phase 1 — RESOLVED: nothing pins from `uv.lock` → relax `uv lock --check` to non-blocking (P1)

**Resolution (operator 2026-06-09, verified):** the range check we want already exists — **`uv pip install -e .`
resolves against the `pyproject.toml` ranges at install time**, so an in-range version installs and a MAJOR that crosses
`<1.0.0` fails to resolve (the signal, for free). And **nothing installs FROM `uv.lock`**: every path is `uv venv` +
`uv pip install -e .` — there is NO `uv sync` / `--frozen` / `--locked` anywhere in `base-service.sh` (220-225) /
`base-library.sh` (113-115) / Dockerfiles. So `uv.lock` pins nothing (internal deps editable; external deps also
range-resolved at install, not pinned from the lock) — it's a _record_, not an enforced pin.

Therefore the earlier "diff-exempt gate" (and the "does `uv lock --check` red on internal drift?" verification) is
**MOOT**: even if the check reds, it enforces nothing real. `uv lock --check` (`base-service.sh:215`,
`base-library.sh:105`) is a gratuitous _freshness_ gate that only adds churn on the cosmetic `version =` snapshot. The
clean fix is to relax it.

- [x] ✅ [SCRIPT] P1. DONE 2026-06-09 (PM@a89e234ee) — `uv lock --check` is now WARN-ONLY in `base-service.sh` +
      `base-library.sh` (collapsed the pinned-uv blocking branch to a single warn; rationale comment added).
      **Fleet-wide immediately, no rollout** — repos `source` the PM base scripts
      (`source …/unified-trading-pm/scripts/quality-gates-base/base-service.sh`), they are not copied per-repo. Also
      note the gate is local-only (guarded by `if [ -z GITHUB_ACTIONS ]`), so CI was never affected. The real contract —
      the pyproject range — is enforced by `uv pip install -e .` (out-of-range MAJOR fails to resolve).
- [ ] [DOCS] P2. (Forward-insurance) IF the fleet ever adopts `uv sync --frozen` (install FROM the lock for reproducible
      builds), re-introduce a lock-freshness gate — but as an **external-only** check (internal editable deps stay
      exempt), since the editable `version =` snapshot is always cosmetic. Until then, not needed.
- [x] [DOCS] P1. Docs already consistent — `CLAUDE.md` / `SUB_AGENT` / `ci-cd-flow.md` say "uv.lock is correct, no
      exact-pin fix needed," which this resolution confirms (the only delta is relaxing the gratuitous freshness gate).

### Phase 2 — MAJOR bump triggers a CASCADE of quality gates (full SIT in dependency order) — P1

- [x] 🟡 [SCRIPT] P1. WIRED 2026-06-09 — `update-repo-version.yml` now dispatches `cascade-qg-trigger` to
      `cascade-qg-ordering.yml` when `bump_type == major || is_breaking` (the cascade was orphaned before — nothing
      dispatched the trigger). `cascade-qg-ordering.yml` already runs QG across transitively-affected repos in
      **topological level order** (parallel within level, sequential across, fail-fast + invalidate downstream).
      **Pending live verification**: a real MAJOR bump must exercise it end-to-end (can't tick fully ✅ on smoke alone).
- [x] 🟡 [SCRIPT] P1. WIRED — the trigger's `if:` excludes minor/patch (`bump_type == major || is_breaking` only), so a
      non-breaking bump fires NO cascade/SIT fan-out (rides the consumer's range pin). Pending live verification.

### Phase 3 — Escalate to vm-planning ONLY IF the cascade FAILS (pass → auto-promote) — P1

- [x] 🟡 [SCRIPT] P1. WIRED 2026-06-09 — `cascade-qg-ordering.yml` gained an `escalate-on-failure` job
      (`if: always() && needs.cascade.result == 'failure'`) that dispatches `escalate-to-orchestrator`
      (`wall_type=sit_failure`, target = first failed dependent, context = failed repos + source major). A **GREEN**
      cascade skips this job → the major promotes automatically with NO vm-planning involvement (operator's refinement).
      Mechanical `[skip ci]`-bump-head deadlocks are still cleared first by `ci-failure-watcher --auto-recover`
      (workflow_dispatch re-fire); this fires only for a GENUINE QG failure. **Pending live verification** (a real
      failing cascade must confirm the escalation reaches vm-planning).

### Phase 4 — MAJOR/MINOR classification matrix refinement — P2

- [x] ✅ [SCRIPT+DOCS] P2. DONE 2026-06-09 (PM@<this commit>) — closed the highest-value schema-contract gap: the differ
      only captured **annotated** class attrs (`ast.AnnAssign`), so **Enum members** (plain `FOO = "foo"` assigns — the
      UAC StrEnum contracts) were invisible → removing/renaming a member or changing its serialized VALUE classified as
      NON-breaking. Added `_is_enum_base()` + enum-member capture into `fields` (keyed `Class.MEMBER`, value = the
      literal), so member removal AND value-change now trip the removed/changed-field breaking checks; a NEW member
      stays additive (non-breaking), and a non-Enum class constant is NOT tracked (no false trips). 4 regression tests
      added (`test_detect_breaking_change.py`, 12 pass). Matrix documented in `codex/08-workflows/ci-cd-flow.md` §
      "Breaking = public-surface change".
- [ ] [DOCS] P3. (Residual) Non-code contract surfaces still out of the differ's scope by design — **manifest
      `schema_version`** (data, handled by the manifest canonicalisation walk) and **GCS path/partition keys** — are
      governed by their own SSOTs, not semver. Cross-link them in the matrix doc so the boundary is explicit; no differ
      change (the differ is a CODE public-surface tool).

### Phase 5 — Version-resolution bug fixes (agent field reports, 2026-06-09)

A hands-on agent fixing the version-aware-clone loud-fail surfaced a class of silent-no-op bugs where `packaging` is
imported at a point in CI BEFORE `uv sync` runs (so `packaging` isn't installed yet → the import fails silently →
version comparison no-ops → the guard never fires). Captured here:

- [x] [SCRIPT] P0. **DONE (agent-fixed) — verify it shipped**: the version-aware-clone loud-fail's first version used
      `from packaging.version import Version`, which silently no-op'd in CI (clone step runs before `uv sync` →
      `packaging` absent) → the loud-fail stayed silent. Fixed to a **stdlib tuple-compare**. Confirm the fix is on
      `live-defi-rollout` + main and add a regression note so it isn't reintroduced.
- [x] ✅ [SCRIPT] P2. DONE 2026-06-09 (PM@<this commit>) — found + fixed the concrete defect: it is
      **`check_version_constraint()` in `setup-workspace-from-manifest.sh`** (the version-aware-clone PREFLIGHT version
      check — `get_version_tag` was the agent's shorthand; no function by that literal name exists in PM, and
      `clone_repo` only ever clones by BRANCH, never a tag, which is the "always branch-falls-back" the agent meant).
      Its `from packaging.version import Version` wrapped in `except Exception: sys.exit(0)` SILENTLY passed every
      constraint when `packaging` was absent at clone time → wrong versions went undetected. Replaced with a
      **stdlib-only PEP440- subset comparator** (no third-party import; no silent exit(0) on parse failure). Verified:
      in-range→0, MAJOR out-of-range→**1** (now detected at preflight), boundary→0, below→1, `any`→0, unparseable→**1**
      (was silently 0).
- [ ] [SCRIPT] P3. **Fleet sweep for the same packaging-no-op pattern in OTHER repos** —
      `rg "from packaging" $(setup     scripts)` across all 25 repos' `setup.sh` / clone-time scripts; any that import
      `packaging` BEFORE `uv sync` with an `except: pass/exit(0)` mask have the same latent silent-no-op.
      (`check-internal-advisories.sh` in PM imports `packaging` too but runs post-install — verify install-order before
      touching it.) Fix each to stdlib; deliberate per-repo (changes resolution behavior).

### Phase 6 — Reproducibility + dep-provenance: base-image digest pinning (5.79) + deployment BoM — P1 (PRIORITIZED)

**Why here (2026-06-09 design review):** the same operator question — "how do I reverse-engineer what code went into a
build / pin deps for safe rollback?" — has ONE answer, and it is NOT `uv.lock`. Cloud builds never read the lock
(service Dockerfiles do `uv pip install -e . --no-deps`; the UTL base image does `uv pip install` against ranges, not
`uv sync --frozen`). So reproducibility AND internal-dep provenance both ride the base **image**, via two levers with
two gaps:

- ✅ **Service-code provenance EXISTS today.** Every service image is tagged `:$SHORT_SHA` (+ optional `:$VERSION`;
  `cloudbuild.yaml:125,245`) and Cloud Run pins the digest at deploy → running service → image digest → `:$SHORT_SHA` →
  exact service commit. No work needed.
- ❌ **Internal-dep (UTL/UAC) provenance + rebuild determinism is BROKEN.** Service Dockerfiles use
  `FROM unified-trading-library:latest` (floating) → the service image never records WHICH UTL/UAC it baked; today you
  can only correlate by build-time vs Artifact Registry push history (indirect, ambiguous under concurrent pushes; UAC
  is one hop worse — baked editable into the UTL image).

The fix is already scoped as **QG STEP 5.79 (`dockerfile-base-pin`, `base-service.sh:2221`, currently
PENDING-RATCHET)**. Reframe + prioritize it: pinning `FROM …@sha256:<digest>` is simultaneously the
**reproducible-build** lever AND the **dep-provenance** lever — one change, both payoffs. Once landed: service commit →
its Dockerfile pins `unified-trading-library@sha256:…` → that digest = a specific UTL build = UTL version+commit → UAC
commit baked in = a deterministic single-SHA provenance chain, with zero `uv.lock` dependency.

- [ ] [INFRA] P1. **Complete the 5.79 FROM-digest ratchet** — drive every production Dockerfile's `FROM` from
      `:latest`/`:tag` → `@sha256:<digest>` and flip STEP 5.79 from PENDING-RATCHET to BLOCKING
      (`base-service.sh:2221-2264`). Resolve the digest at build time (cloudbuild reads the freshly-pushed base image's
      `RepoDigests` / Cloud Run revision digest, injects via `--build-arg BASE_IMAGE_DIGEST`). Done = rebuilding any
      service commit yields a byte-identical image (reproducibility) AND the Dockerfile records exactly which UTL/UAC
      went in (provenance). This is the operator's answer to both "reproducible cloud builds" and "reverse-engineer the
      code version in a build".
- [ ] [CODE] P1. **Deployment-registry bill-of-materials — record digest + commit + dep-versions** (deployment-service).
      TODAY the registry persists ONLY a mutable `image_tag` (`monitor.py:39` / `live_deployment.py:42,63` /
      `backends/base.py:135`); the `git_commit` field exists (`monitor.py:40`) but its writer
      `VersionRegistry.register_version` (`monitor.py:540`) has ZERO callers (dead/unwired), and NO image-digest /
      internal-dep-version is stored anywhere — so "what code is in prod right now" is NOT queryable. On the **live**
      deploy path (`DeploymentRegistryEntry`/heartbeat extras, `deployments_registry.py:146-169`, OR wire up the dead
      `VersionRegistry`): (a) resolve the deployed tag → immutable `@sha256:` digest (Cloud Run revision / Artifact
      Registry `RepoDigests`) into a new `image_digest` field; (b) stamp `git_commit` from `$SHORT_SHA`; (c) stamp
      `dep_versions: dict` (UTL/UAC + base-image digest). Store: GCS `gs://deployment-metadata-{pid}/versions/…` (the
      existing VersionRegistry target) / `gs://deployment-scripts-{pid}/deployments/…`; expose via deployment-api
      `GET /api/deployments`. Done = "what's deployed in prod + exactly what code is in it" is a single queryable BoM.

## Success criteria

- A UAC (or any internal lib) minor/patch bump reds ZERO consumer QGs and triggers ZERO consumer rebuilds.
- A MAJOR bump triggers a full SIT in dep order; on stuck staging it escalates to vm-planning (never silently jams).
- External-dep reproducibility unchanged (external drift still hard-fails `uv lock --check`).
- The major/minor boundary is matrix/contract-driven, not a version-phase heuristic.
- Every production Dockerfile `FROM` is `@sha256:<digest>` (5.79 BLOCKING) → rebuilding any service commit is
  byte-deterministic AND records its exact UTL/UAC provenance.
- "What code is deployed in prod" is a single queryable BoM (image digest + git commit + UTL/UAC dep versions) via
  deployment-api `GET /api/deployments`.

## Codex SSOT updates

`codex/08-workflows/ci-cd-flow.md` (dependency-promotion model + the lock-gate internal-exemption),
`codex/06-coding-standards/quality-gates.md` (uv.lock gate behavior + STEP 5.79 dockerfile-base-pin as the
reproducibility/provenance lever), CLAUDE.md § Dependencies+builds (range pins absorb minor/patch; only major forces
rebuild; base-image `@sha256` digest — not `uv.lock` — is the rollback/provenance pin),
`codex/05-infrastructure/vm-tarball-deployment.md` (deployment-registry BoM: image digest + git commit + dep versions).
