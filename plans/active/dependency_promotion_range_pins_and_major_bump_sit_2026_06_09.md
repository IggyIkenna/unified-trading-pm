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

### Phase 1 — `uv lock --check` gate vs internal editable drift — RE-OPENED pending verification (P0)

**Status reconciliation (2026-06-09):** this was tombstoned after the operator clarified "`uv.lock` is already correct"
(editable internal / exact external — the lock FORMAT has no exact-pin bug). But a hands-on agent then re-reported that
the `uv lock --check` **gate** still reds on internal editable drift (the recorded `version =` snapshot, e.g. `0.1.20`,
goes stale vs the source). Those aren't contradictory — the lock FORMAT is correct AND the staleness CHECK can still
trip. So re-opened with a verification gate first (don't build on a false premise either way):

- [ ] [SCRIPT] P0. **VERIFY**: does `uv lock --check` actually exit non-zero on a pure internal editable version-field
      drift (source bumped, no external dep moved)? Reproduce in a sandbox consumer. If NO (uv treats editable version
      leniently) → re-tombstone, the version-aware-clone loud-fail is the only mechanism (already closed). If YES →
      implement the exempt-gate below.
- [ ] [SCRIPT] P0 (only if VERIFY=yes). Write `scripts/cicd/check_lock_internal_only_drift.py` (PM): on
      `uv lock --check` failure, regenerate to a temp lock + diff; **PASS** if the only changed `[[package]]` entries
      are internal editable deps (name in the workspace-manifest internal set AND `source={editable=…}`), **FAIL** if
      any EXTERNAL dep version moved (reproducibility preserved). NEVER recommit the lock (no fleet churn). Unit tests:
      internal-only → pass; external → fail; no drift → pass; mixed → fail.
- [ ] [SCRIPT] P0 (only if VERIFY=yes). Wire into `base-service.sh:215` + `base-library.sh:105` (replace the raw
      `uv lock --check … || exit 1`); keep the pinned-uv-only blocking behavior; roll out via `rollout-*.sh` (never
      hand-edit per-repo copies). Then reconcile `CLAUDE.md` / `SUB_AGENT` / `ci-cd-flow.md` (which currently state the
      gate is a non-problem) — update them to "FORMAT correct; the CHECK exempts internal editable drift".

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

- [ ] [DOCS] P2. Refine the plan-documented major-vs-minor matrix based on **schemas + API contracts** (UAC public
      surface, manifest schema_version, event contracts) — what is a breaking (major) change vs a backward-compatible
      (minor/patch) one — so `detect_breaking_change.py` + semver-agent classify correctly. SSOT:
      `codex/08-workflows/ci-cd-flow.md` § "Breaking = public-surface change".

### Phase 5 — Version-resolution bug fixes (agent field reports, 2026-06-09)

A hands-on agent fixing the version-aware-clone loud-fail surfaced a class of silent-no-op bugs where `packaging` is
imported at a point in CI BEFORE `uv sync` runs (so `packaging` isn't installed yet → the import fails silently →
version comparison no-ops → the guard never fires). Captured here:

- [x] [SCRIPT] P0. **DONE (agent-fixed) — verify it shipped**: the version-aware-clone loud-fail's first version used
      `from packaging.version import Version`, which silently no-op'd in CI (clone step runs before `uv sync` →
      `packaging` absent) → the loud-fail stayed silent. Fixed to a **stdlib tuple-compare**. Confirm the fix is on
      `live-defi-rollout` + main and add a regression note so it isn't reintroduced.
- [ ] [SCRIPT] P2. **`get_version_tag` has the SAME latent defect** — it imports `packaging` at the same pre-`uv sync`
      point, so it can **never resolve a release tag** and **always falls back to the branch**; this is why the phantom
      manifest row stayed silent. Fix it to a stdlib version compare too. **Deliberate rollout, NOT a drive-by** — it
      changes fleet dep-resolution behavior (tag-vs-branch clone selection), so: locate every consumer of
      `get_version_tag`, fix the import/compare, dry-run the resolution change across the fleet, then roll out. Find the
      definition + call sites first (`rg get_version_tag`), embed the consumer manifest in the todo before changing it.

## Success criteria

- A UAC (or any internal lib) minor/patch bump reds ZERO consumer QGs and triggers ZERO consumer rebuilds.
- A MAJOR bump triggers a full SIT in dep order; on stuck staging it escalates to vm-planning (never silently jams).
- External-dep reproducibility unchanged (external drift still hard-fails `uv lock --check`).
- The major/minor boundary is matrix/contract-driven, not a version-phase heuristic.

## Codex SSOT updates

`codex/08-workflows/ci-cd-flow.md` (dependency-promotion model + the lock-gate internal-exemption),
`codex/06-coding-standards/quality-gates.md` (uv.lock gate behavior), CLAUDE.md § Dependencies+builds (range pins absorb
minor/patch; only major forces rebuild).
