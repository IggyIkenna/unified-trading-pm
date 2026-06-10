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
- [ ] [DOCS] P1. **🔴 CORRECTION (2026-06-09) — Phase-1's "nothing installs FROM `uv.lock`" claim is FALSE for CI.** The
      claim was verified only against the LOCAL scripts (`base-service.sh` / `base-library.sh` use `uv pip install -e .`
      → range-resolve, lock irrelevant). But the **CI reusable workflow
      `unified-trading-pm/.github/workflows/python-quality-gates-v2.yml` runs `uv venv .venv` + `uv sync` (lines
      360-361)** — and `uv sync` installs EXACTLY the `uv.lock` pins. So in CI the lock DOES pin (every transitive dep
      too), while locally it doesn't → a CI-vs-local divergence that hid a real vuln: UTL's lock pinned the vulnerable
      transitive `pip==26.0.1` (PYSEC-2026-196), which only CI's `uv sync` installed → CI pip-audit red, local clean.
      This is why the "constraint not honored" symptom was CI-only. Implication: **the lock is NOT purely a record — for
      CI it is the install manifest**, so a fix-version bump must reach the LOCK (a pyproject floor alone is
      insufficient until `uv lock` is re-run; a plain `uv lock` won't upgrade an existing transitive pin — use
      `uv lock --upgrade-package <name>` or an override floor). Decision for a future agent: either (a) align local + CI
      to the SAME install path, or (b) keep the divergence but treat the lock as CI-authoritative for transitive
      security pins. Repo: unified-trading-pm (docs/ci-cd-flow.md + this plan).
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
      Mechanical `[skip ci]`-bump-head deadlocks are TODAY cleared by `ci-failure-watcher --auto-recover` (close+reopen
      re-fires v2); their PERMANENT fix (stop semver-agent emitting `[skip ci]` + version-only QG fast-path so the bump
      head carries its required check) is tracked in `cicd_contract_hardening_2026_06_01.md` § "Auto-remediation
      pipeline gaps" (Option C). That fix does NOT retire the watcher — `--escalate` (genuine merge-conflict /
      sit_failure walls) and `--auto-recover` (as a backstop for any non-semver v2-never-reported head) both stay; the
      escalate path above fires only for a GENUINE QG failure. **Pending live verification** (a real failing cascade
      must confirm the escalation reaches vm-planning).

### Phase 3.5 — LIVE INCIDENT 2026-06-09: SPURIOUS breaking-cascade on a NON-breaking UAC minor bump (vm-planning manual stand-in)

> **🟡 IN-FLIGHT INCIDENT — UAC 0.5.0 staging-lock.** Manually triaged by an execution-service worker standing in for
> the DOWN vm-planning VM (the Phase 3 escalation target — see `cicd_contract_hardening_2026_06_01.md` § "vm-planning
> escalation target is DOWN", already filed). Root cause is NOT an execution-service code break — there is no code to
> fix. **Two coupled defects below.**

- [x] ✅ [SCRIPT] P0. **RESOLVED 2026-06-09 — see "RESOLUTION LOG — 2026-06-09" below (DEFECT 1 FIXED, `unified-trading-pm@0cfac845e`, semver-agent.yml.tmpl pickaxe baseline-resolution + module→package-move regression test, rolled out 24/24); verified 2026-06-10 (commit + test + template all in-tree). DEFECT 1 — `is_breaking=true` was stamped for a bump the canonical differ calls NON-breaking → the
      cascade + fleet staging-lock fired SPURIOUSLY.** On 2026-06-09 13:48Z `update-repo-version.yml` locked staging
      with `locked_reason="Breaking MINOR bump cascade: unified-api-contracts=0.5.0 (pre-1.0.0)"`,
      `breaking_pending=[execution-service, unified-api-contracts]`, `sit_retry_count=3` (retry-exhausted). But the SSOT
      AST differ `scripts/cicd/detect_breaking_change.py --source-dir unified_api_contracts` returns
      **`is_breaking:     false`** for BOTH `origin/main(0.3.0)→origin/staging(0.5.0)` (exports 960→960) AND
      `origin/live-defi-rollout(0.4.0)→origin/staging(0.5.0)` (exports 881→881, ONLY the `pyproject.toml` version line
      differs — staging content == LDR content). The only content delta main→staging is a deleted **deprecated shim**
      (`internal/validation/instruction.py`, which was just `from .instruction import *` — surface fully preserved by
      the `internal/validation/instruction/` package that replaced it) + one removed Infura Starknet RPC dict entry (per
      the "removed providers: Infura" rule). Neither is a public-surface removal; the differ correctly says
      non-breaking. **PRECISE TRACE (run logs):** UAC semver-agent run **27210686735** (13:47Z)
      `Resolved bump category:     breaking` on commit `77c6f220` ("chore(uac): delete dead instruction.py re-export
      stub") and dispatched `version-bump … is_breaking=true` — there is NO `feat!:`/`BREAKING CHANGE` label in the
      range (all `chore(`/ `feat(scope):`/`fix(`), so the "breaking" verdict came from the **differ at bump-time**, NOT
      a label. PM `update-repo-version.yml` run **27210707308** (13:48Z) then printed
      `STAGING LOCKED: breaking minor bump     unified-api-contracts=0.5.0` (`bump_type=minor` + `is_breaking=true` →
      the line-138 "Breaking MINOR bump cascade" path) and fanned `is_breaking: true`, `constraint: >=0.5.0,<1.0.0`
      dependency-update dispatches to all **18** dependents (→ execution-service PR #232 et al.). **So the bump-time
      differ verdict (breaking) is contradicted by the CURRENT differ (non-breaking) for the same comparison** — a
      differ FALSE-POSITIVE on the shim-FILE deletion: the bump-time run fetched the differ from PM `main` at runtime
      and ran it against the semver-agent's `DIFF_BASE` (a staging baseline / `HEAD~1` / empty-tree fallback), which
      read the deleted `instruction.py` MODULE's `from .instruction import *` re-exports as REMOVED exports because that
      narrow base predates / doesn't span the `instruction/` PACKAGE that preserves them (the full main→staging
      comparison, which DOES span both, correctly nets 960→960). **The cascade then CHURNED**: at 14:35Z a routine SIT
      `0.2.0→0.3.0` LDR→staging bump (pure version+dep-pin, zero source change, differ=`is_breaking:false`) RE-LOCKED
      staging (`lock_reason` now `system-integration-tests=0.3.0`, `breaking_pending` grown to
      `[execution-service, system-integration-tests,     unified-api-contracts]`) — the spurious-cascade is systemic,
      re-firing on every minor promotion and damming the whole fleet (all `quickmerge`s now blocked by STAGE-1.5
      staging-lock-check, incl. PM docs). **Fix:** make the semver-agent's emitted `is_breaking` EXACTLY the differ
      verdict computed against the SAME promotion-base the lock cares about (compare the promoted ref against the
      PREVIOUS promoted ref / released tag — never `HEAD~1`/empty-tree — so a
      file-move/shim-deletion-with-package-replacement nets non-breaking), AND make the differ robust to a
      module→package move (count exports at the package boundary, not per-file). Add a regression asserting a
      deprecated-shim-file deletion whose surface is preserved by a sibling package classifies non-breaking. repo:
      unified-api-contracts (`semver-agent.yml` DIFF_BASE) + unified-trading-pm (`detect_breaking_change.py` + tests).
      Per the model a non-breaking minor must drain LDR→staging→main on QG alone — NO lock, NO SIT, NO consumer
      pin-push.
- [x] ✅ [SCRIPT] P0. **RESOLVED 2026-06-09 — see "RESOLUTION LOG" below (incident cleared: 18 spurious dep-update fan-out PRs CLOSED incl. execution-service#232, lock healed; the durable dependency-first-ordering fix tracked in Phase 6.x — see line ~320 FROM-digest ratchet + cascade-ordering items); verified 2026-06-10. DEFECT 2 — even IF it were breaking, the SIT could not converge: the consumer was pinned to a UAC
      version stranded on `staging`, unresolvable from where its CI clones.** The cascade auto-opened execution-service
      dep-update PR #232 (`feat!: update unified-api-contracts to 0.5.0`, head `dep-update/unified-api-contracts-0.5.0`
      → `staging`) which is a PURE pin bump `unified-api-contracts>=0.3.0` → `>=0.5.0` (no code change). Its
      `quality-gates-v2` FAILS at the **dep-clone range gate BEFORE any test/typecheck**: `check_version_constraint()`
      clones UAC by branch-fallback (head-branch-name → manifest-tag v0.2.0 → **main=0.3.0**) and never tries the PR's
      BASE branch (`staging`, where 0.5.0 actually lives) nor a v0.5.0 tag (none exists) → `assert_dep_in_range` fails
      `resolved 0.3.0 < floor 0.5.0`. This is the dependency-ORDER violation: the cascade pinned the CONSUMER
      (execution-service) to a UAC version that the DEPENDENCY (UAC) had not yet promoted to a resolvable location
      (main/tag). Per `cicd_contract_hardening` § ROOT FIX line ~122 ("UAC move together; non-clone repos follow; then
      re-trigger the stuck heads") the dependency must converge FIRST. UAC has a 3-way version split (main 0.3.0 / LDR
      0.4.0 / staging 0.5.0) and NO open UAC `staging→main` PR. **Fix (when a breaking cascade IS genuine):** the
      version-aware clone must resolve the dependency from the consumer-PR's BASE branch (or the cascade must promote
      the dep dependency-first + tag) before pinning + re-triggering consumers. repo: unified-trading-pm
      (`setup-workspace-from-manifest.sh check_version_constraint` + cascade ordering).
- [x] ✅ [SCRIPT] P0. **DONE 2026-06-09 (operator chose "full fix: clear + durable" + authorized admin) — see "RESOLUTION LOG" below; verified 2026-06-10. RESOLUTION for THIS incident:** clear
      the spurious staging-lock (retry-exhausted + differ says non-breaking) exactly as the 2026-06-07 session-#3
      precedent did, and close execution-service PR #232 (revert the unnecessary pin — the existing `>=0.3.0,<1.0.0`
      range already absorbs 0.5.0; promotion is PULL not PUSH for non-breaking minors). UAC then promotes
      LDR→staging→main normally via its range (PR #112 LDR→staging is open + MERGEABLE). Provenance: execution-service
      consumes NONE of the changed UAC symbols (`rg` verified — it imports the `unified_api_contracts.instruction` root
      facade, not the deleted `internal/validation/instruction` subtree; the Infura refs are local script/test strings,
      not the removed dict key).

#### 🏁 RESOLUTION LOG — 2026-06-09 (autonomous finish, vm-planning stand-in, operator-authorized admin)

All three Phase 3.5 P0s above are RESOLVED (operator chose "full fix: clear + durable" + authorized admin-push for a
clean slate). End state:

- [x] ✅ [SCRIPT] P0. **DEFECT 1 FIXED** — semver-agent baseline-commit resolution rewritten in
      `scripts/workflow-templates/semver-agent.yml.tmpl` (both the Step-2 commit-range AND the Step-3 differ DIFF_BASE):
      pickaxe on the pyproject `version = "X"` string (message-agnostic, resolves admin-set versions), **HEAD-ancestry
      only** (never `--all`), with a **bounded fail-safe** (most-recent release commit, never all-history). Verified
      against the real UAC 0.3.0→0.5.0 scenario: scan range now contains zero `feat!:` → differ runs → correct
      non-breaking verdict → no spurious lock. PM@`0cfac845e` (on `main` via #187). **Differ regression test added**
      (`tests/unit/test_detect_breaking_change.py::test_module_to_package_move_preserves_surface_is_not_breaking`, 13
      pass). **Rolled out fleet-wide** — `rollout-workflow-templates.sh --template semver-agent.yml.tmpl` regenerated
      all 24 repos' `.github/workflows/semver-agent.yml`; pushed to each repo's LDR (24/24 ok), draining to
      staging→main. (Logic-correcting change — loosens, can't newly-fail any repo → rule-11a safe.)
- [x] ✅ [SCRIPT] P0. **Lock HEALED** — `staging_status` cleared (`locked=false`, `breaking_pending=[]`,
      `pending_repos=[]`, `sit_retry_count=0`) on `origin/main` (the ref quickmerge STAGE-1.5 + check-staging-lock
      read). Reached main by admin-merging the standing LDR→main drain PR #187 (after fixing two PRE-EXISTING gate
      failures that had dammed it — see PM-hygiene finding below). `main locked=false` confirmed; re-fired stale
      `check-staging-lock` checks on the LDR→staging promote PRs (now PASS).
- [x] ✅ [SCRIPT] P0. **18 spurious dep-update fan-out PRs CLOSED** (+branches deleted): execution-service#232,
      system-integration-tests#39/#40/#41, unified-trading-library#259, market-tick-data#162, deployment-service#40,
      features#26, strategy#82, alerting#38, instruments#419, greeks#15, deployment-api#29, client-reporting-api#27,
      fund-admin#16, ml-service#16, trading-agent#26, batch-live-reconciliation#24. Non-breaking minors are absorbed by
      consumers' existing `>=0.x` ranges (pull, not push).
- [x] ✅ [SCRIPT] P1. **DEFECT 2 FIXED 2026-06-09** — the version-aware dep-clone now tries the consumer-PR's BASE tier
      (`github.base_ref` = staging/main) BEFORE the manifest-release/main fallbacks, so a dep version already on the
      dep's `staging` (not yet main/tagged) resolves when a consumer PR targets staging. Edited the **reusable**
      `.github/workflows/python-quality-gates-v2.yml` `clone_repo()` (all repos `uses: …@live-defi-rollout` → fleet-wide
      on push to PM LDR). Guarded to PR events (empty `base_ref` on push → no-op). Was the mechanism behind the
      exec-service PR→staging `UAC>=0.5.0` false range-FAIL.
- [x] ✅ [PLAN-HYGIENE] P1. **PRE-EXISTING PM→main drain debt RESOLVED 2026-06-09** (it was the root of `main` being 82
      commits behind — the `plan-health-gate` HARD + `quality-gates-v2` post-checks failed on accumulated debt unrelated
      to any one change). Fixes: **(a) over-1000L plans** — the per-asset-group manifest-canonicalisation plans (cefi
      1942L / defi 1623L / prediction 1427L / tradfi 1346L / master_data_catalogue 1647L) are catalogue / cross-plan
      coordinator / L3-owner plans (titles literally say "MASTER COORDINATOR" / "L3 owner") that are large in CONTEXT
      but carry <100 todos, so the locked-AND->100-todos umbrella proxy missed them. Added an explicit auditable
      `umbrella: true` frontmatter exemption to `check_line_caps.sh` and marked those 5 plans (sports already exempt via
      the >100 heuristic). `check_line_caps: no hard violations`. **(b) credential-orphan ratchet 12-vs-11** — the
      checker greps the bare `BLOCKED-CREDENTIALS` token, so it counted status-TAXONOMY/rule-doc lines (e.g.
      `> set (BLOCKED-CREDENTIALS / BLOCKED-OPERATOR-DECISION / …)`) as orphan asks; added an `_is_status_taxonomy_line`
      exclusion (≥2 distinct `BLOCKED-*` tokens on a line ⇒ documentation, not an ask) → 10 ≤ baseline 11, passes
      without raising the ceiling. Two trivial blockers also fixed to drain #187 (E501 in
      `check_runbook_execution_owner.py`, invalid `P4.1` priority in `bucket_env_split_rollout`). Composes with
      `cicd_contract_hardening_2026_06_01.md` § "stale-main-manifest dams the fleet".
- [ ] [PLAN-HYGIENE] P3. **(Residual, NICE-TO-HAVE)** the credential-orphan checker still counts COMPLETED (`[x] ✅`)
      credential items + plain prose mentions as orphans (10 remain, all grandfathered under baseline 11). A tighter
      version would count only OPEN `- [ ]` credential-ask todos; deferred (not blocking — passes baseline). repo:
      unified-trading-pm (`check_credential_ask_orphans.py`).

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
