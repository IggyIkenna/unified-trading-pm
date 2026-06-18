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
  fails" wiring. **This is the remaining work.** [STATUS CORRECTION 2026-06-10: the cascade IS wired —
  update-repo-version.yml:132-153+387-407 dispatches cascade-qg-trigger → cascade-qg-ordering.yml (per-consumer QG in
  manifest topologicalOrder levels, escalate-on-failure → orchestrator) since PM@cb44b85d4. Remaining: live verification
  on a real MAJOR bump + DEFECT-2 dependency-FIRST ordering (promote dep + tag before consumer pin fan-out).] [LIVE-RUN
  OBSERVED 2026-06-10 — PARTIAL: UTL 0.5.0 breaking-MINOR exercised the LOCK + fan-out legs but NOT the cascade-QG leg.
  Evidence: update-repo-version run 27264928435 success 08:54:04Z → manifest 843e3ebcc 08:54:38Z engaged lock ("Breaking
  MINOR bump cascade: unified-trading-library=0.5.0 (pre-1.0.0)"); consumer fan-out fired green at 08:54:47-48Z
  (update-dependency-version success in mtds + execution-service + features-service; no pin PRs expected — 0.5.0 stays
  in the `<1.0.0` range); cascade-qg-trigger dispatch DID fire (cascade-qg-ordering run 27264972415, repository_dispatch
  08:54:52Z) but was CANCELLED 4 s later (08:54:56Z) with ZERO jobs — displaced in the shared `manifest-update`
  concurrency group (the H2 fix; `cancel-in-progress: false` protects a RUNNING run but GitHub keeps only ONE pending
  run per group, so a newer queued manifest writer evicts a queued cascade). All 5 most-recent cascade-qg-ordering runs
  are cancelled/failure — the cascade has never completed a level live. The lock was cleared NOT by the cascade but by
  staging-to-main.yml run 27265597852 (workflow_dispatch, success 09:05:58Z) → 786c71d79 "chore(manifest): promote
  staging_versions → versions, clear staging lock" 09:06:40Z + staging-unlocked dispatch 09:06:58Z. UNPROVEN LEG:
  per-level dep-order QG execution + escalate-on-failure skip-on-green. breaking_pending residual
  `['unified-trading-library']` post-unlock is an EXPECTED transient — staging-to-main clears only the lock;
  sit-debounce-trigger.yml:156-163 prunes stale entries (breaking_pending − pending) on its next tick, and a stale entry
  is fail-safe meanwhile (worst case forces an extra SIT if the repo re-enters pending). Do NOT flip this item until a
  cascade run survives the concurrency group and runs its levels.]

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
- [x] 🟡 [DOCS] P1. RESOLVED 2026-06-12 (operator Harsh) — the fleet ADOPTS `uv sync --frozen` in CI (below), but the
      lock-freshness gate is **deliberately NOT re-introduced**: `--locked` / `uv lock --check` hard-fails on the
      semver-agent's CI-side `version =` bump (poison-pill — one bumped version with no lock regen reds every later PR),
      and speed > security per operator. The author-time "floor bump → regen + commit `uv.lock` in the same commit"
      discipline replaces it (a rule, not a CI gate).
- 🟡 [CI] **SUPERSEDED 2026-06-17 → now tracked as Phase 1.5b below; the flip is gated on the Phase-1.5a LDR-landing
  prerequisite (a bare flip re-arms the Tier-C runaways). Original 2026-06-12 draft kept for rationale.** DECIDED
  2026-06-12 (operator Harsh) — align CI to local via `uv sync --frozen`; speed > security. DRAFTED for Ikenna
  (CI/CD-pipeline surface), REVIEW-REQUESTED. The CORRECTION stands: CI's `python-quality-gates-v2.yml` runs `uv venv` +
  plain `uv sync` (line 459) which RE-RESOLVES against the lock and can pull surprise transitive deps (the CI-only
  `pip==26.0.1` PYSEC-2026-196 divergence — CI pip-audit red, local clean). **Decision: keep `pyproject.toml` as the
  edit-surface/contract, but make CI install the COMMITTED lock deterministically — `uv sync` → `uv sync --frozen`.**
  `--frozen` NOT `--locked`: `--frozen` installs the committed lock as-is, no re-resolution (no surprise deps, fastest)
  AND tolerates the semver-agent's CI-side `version =` bump; `--locked` asserts pyproject↔lock consistency and would
  HARD-FAIL on every version bump (poison-pill). Under `--frozen` the version bump is a no-op (root pkg is
  editable-installed from source). **Replaces the freshness gate with an author-time rule:** a dependency-FLOOR bump
  (NOT a version bump) regenerates + commits `uv.lock` in the SAME commit (`uv lock` /
  `uv lock --upgrade-package <name>` → commit `pyproject.toml` + `uv.lock` together); a CVE fix = bump the floor + regen
  (no transitive-CVE HARD block — pip-audit / internal-advisories on transitive pins WARN). **Ready diff handed to
  Ikenna in `_agent_pings.md` 2026-06-12:** one-line `python-quality-gates-v2.yml:459     uv sync` →
  `uv sync --frozen` + relax transitive-CVE block to WARN; trivially revertible (drop `--frozen`). Docs updated:
  `CLAUDE.md` Deps+builds + `ci-cd-flow.md` §Dependency promotion + `quality-gates.md`. Repo: unified-trading-pm.
- [x] [DOCS] P1. Docs already consistent — `CLAUDE.md` / `SUB_AGENT` / `ci-cd-flow.md` say "uv.lock is correct, no
      exact-pin fix needed," which this resolution confirms (the only delta is relaxing the gratuitous freshness gate).

### Phase 1.5 — Frozen-lock end-to-end + local/CI parity (DECISION 2026-06-17, operator-ratified)

> **Decision** (closes
> [`issues/uv_lock_frozen_model_contradiction_2026_06_15.md`](issues/uv_lock_frozen_model_contradiction_2026_06_15.md);
> finalizes + sequences the superseded line-120 item above): adopt the **frozen-lock model end-to-end** for genuine
> local↔CI parity. `uv.lock` is the SSOT, regenerated on `live-defi-rollout` and flowing LDR→staging→main as
> byte-identical projections (no cross-branch lockstep — staging/main never carry an independent lock). Internal
> `unified-*` editable deps are **EXEMPT** from regen (the lock resolves the on-disk sibling, so a minor floor bump
> needs none); the regen rule scopes to **EXTERNAL deps only**. **Sequencing is load-bearing:** the structural
> LDR-landing fix (1.5a) MUST land before the `--frozen` flip (1.5b), or the flip re-arms the Tier-C runaways. Why
> frozen and not the bare-`uv sync` status quo: bare `uv sync` cannot give true parity — local uses
> `uv pip install -e .` (range resolve), CI uses `uv sync` (lock-mediated); they diverge exactly when it matters (the
> fund-admin CVE case). Why the runaway is not a reason to reject frozen: the runaway is the dep-bump bot landing on
> `staging` only — a branch-targeting bug independent of the lock model (1.5a fixes it). This also earns its keep
> post-1.0 when internal deps become published packages and the floor re-pin + lock become load-bearing for the
> major-bump cascade.

### Current-flow map + REGRESSION CONTRACT (verified vs deployed workflows 2026-06-18 — do NOT regress)

**Ownership:** Harsh owns the CI/CD surface (Ikenna is on the data pipeline) — no cross-owner gate, but the promote-bot
machinery is jam-prone, so the safeguards below are MANDATORY before touching it.

**TWO distinct failure modes this work must prevent (verified mechanisms, with file:line):**

- **(A) tree-divergence runaway** — a floor edit landing on **`staging` only** (lock unchanged) makes `staging` tree-sha
  ≠ LDR tree-sha. The Tier-C drain's ONLY convergence signal is tree-sha equality (`ldr-to-staging-promote.yml:187`); a
  staging-exclusive commit can never be reproduced by the LDR-sourced drain, and `ahead_by` never returns to 0
  (squash-merges, `:172`) → the drain re-promotes every ~40s → runaway breaker (≥30 `chore(promote)` merges/6h, `:213`)
  trips + pages. `ci-status-update.yml:223-258` amplifies it (each `STAGING_GREEN` re-fires `tier-ab-green` → another
  promote; the `:233-244` loop-guard only stops the SAME-status self-loop). `staging-backmerge-to-ldr` can't rescue it —
  the divergent floor line CONFLICTS on the `--no-ff` merge → `merge --abort` + escalate-to-human PR, never auto-FFs.
- **(B) version mismatch** — pyproject floor ≠ `uv.lock` pin, and CI installs from the lock. Today CI does **bare
  `uv sync`** (`python-quality-gates-v2.yml:459`) which re-resolves to the floor and MASKS it; flipping to
  **`--frozen`** installs the committed (stale) lock EXACTLY → ships the wrong version (the fund-admin
  `python-multipart 0.0.29` CVE case).

**PREVENTION — the safety contract (all required, in this order):**

1. **Atomic regen** — floor bump + regenerated `uv.lock` in the SAME commit (kills B). **EXTERNAL deps ONLY** — internal
   `unified-*` editable deps resolve the on-disk sibling regardless of the lock's cosmetic version, so regenerating them
   just manufactures cross-branch lock churn → re-creates (A). Internal bumps: **NO regen**.
2. **Land on `live-defi-rollout`, not `staging`** — flows LDR→staging→main as byte-identical projections; trees converge
   after one drain promote (kills A). This is 1.5a.
3. **`uv lock --check` BLOCKING** (1.5b) — the guardrail: a floor-without-lock-regen HARD-FAILS the gate, so B is
   impossible to merge (not merely discouraged).
4. **Sequencing** — 1.5b (`--frozen`) is GATED on 1.5a. `--frozen` makes the lock authoritative; safe ONLY once 1.5a
   guarantees the lock is always fresh-on-LDR. Flip `--frozen` first → ship B on the next stale-lock repo.

**NEW regression vectors the 1.5a "land on LDR" change ITSELF introduces (handle, or we trade the old jam for a new
one):**

- ✅ **Provenance gate — VERIFIED ALREADY-HANDLED 2026-06-18 (no new code; was over-cautious framing)**. The Tier-C
  drain runs `check_strict_quickmerge.py --block` over the promote range (`ldr-to-staging-promote.yml:283`). Reading the
  checker (`scripts/cicd/check_strict_quickmerge.py`): `commit_violates` returns NOT-a-violation for **(a)** a
  `github-actions` / `[bot]` author (`:59`) **and** **(b)** a commit that changes **no** `.py`/`.ts`/`.tsx` source
  (`:65`). The dep-bump commit is authored `github-actions[bot]` (the workflow's `git config user.name`) and touches
  only `pyproject.toml`/`uv.lock`/Dockerfile — so it is **doubly exempt**. A `Quickmerge:` trailer would be a redundant
  FAKE signal (it never went through quickmerge) and is NOT added. **Guardrail for future edits:** do not change the bot
  identity on these commits — the bot-author exemption is load-bearing. (Header comment in the workflow records this.)
- **Breaking-dep path** — `update-dependency-version.yml:276-282` opens a `feat!` PR to **staging** today; must reroute
  to the LDR path or breaking bumps still diverge. (Non-breaking is already digest-only / range-absorbed — `:100-108`.)
- **Deferred firing** — a push to LDR fires ZERO immediate workflows (LDR has no `push:` triggers; LDR-named workflows
  are schedule/dispatch pollers). The change waits for the next drain tick (≤15min) instead of re-firing semver-agent
  instantly. Proper path, but a behavior change — verify the drain reliably carries it (it will: atomic floor+lock on
  LDR → one promote → `LDR_TREE == STG_TREE` → the `:187` gate collapses subsequent ticks).
- **`update-repo-version.yml` commits to `main`** (no `ref:` → default branch) — that's PM's OWN version self-bump (PM
  is Option-B main-direct); it back-merges to LDR via `main-backmerge-to-ldr.yml`. So 1.5a's reroute is about
  `update-dependency-version.yml` (the dependent-repo fan-out) + the manual author edit, NOT PM's self-bump.

**Phase 1.5a — remove the divergence source (PREREQUISITE, must land before the flip):**

- [x] ✅ [SCRIPT] P1. **DONE 2026-06-18 — template + 24-repo fleet rollout landed on LDR.** Make dependency-floor bumps
      land on **`live-defi-rollout`, not `staging`** — the automatic fan-out `update-dependency-version.yml`. Edited the
      SSOT template `scripts/workflow-templates/update-dependency-version.yml`: (1) checkout `ref: live-defi-rollout`
      (was `staging`); (2) non-breaking digest-refresh path pushes `HEAD:live-defi-rollout` (was
      `git push origin staging`), rebase-retry on a concurrent-push reject; (3) MAJOR/breaking path **retired the
      dedicated `feat!` staging PR** — now an atomic `chore(deps): re-pin …` commit (floor + regenerated `uv.lock`)
      pushed to LDR with rebase-retry (conflict → `exit 1` → `notify-failure` Slack, never silently dropped). **3
      regression vectors handled:** (i) **provenance gate** — VERIFIED already-exempt (bot-author + no-source double
      carve-out; see the ✅ note above), no code; (ii) **breaking-path reroute** — DONE, and SIT is NOT lost (the
      major-bump CASCADE `update-repo-version.yml`→`cascade-qg-ordering.yml` is payload-triggered, independent of this
      workflow's PR; the drain PR's `quality-gates-v2` gates the content); (iii) **deferred-firing** — accepted: an LDR
      push fires no immediate CI; the `*/15` Tier-C drain carries it (≤15min), trees converge after one promote (`:187`
      gate). YAML validated (`yaml.safe_load`), 0 residual `staging`-direct writes. **Manual external floor edit** needs
      no code — `quickmerge --files 'pyproject.toml uv.lock'` already lands on LDR (the 1.5b DOCS todo makes the regen
      rule explicit). **Rollout COMPLETE**: `rollout-workflow-templates.sh --template update-dependency-version.yml` →
      all 24 consumer copies committed + pushed to their LDRs (PM has no consumer copy — it is the dispatcher);
      `detect_template_drift.py --workflows` exits **0** (0 new drift; the rollout also CLEANED 46 previously-baselined
      drift entries) and 0 repo's `.github/workflows/` is dirty. Also deleted the dead duplicate
      `scripts/propagation/templates/update-dependency-version.yml` (no consumer; a stale staging-direct copy = a latent
      regression vector). Evidence: PM@`5549412ec` + 24× `ci(workflow-templates): … lands dep bumps on LDR` on each
      repo's `live-defi-rollout`. **Effective-on-main**: the workflow fires from each repo's DEFAULT branch
      (`repository_dispatch`), so the new behaviour activates per-repo as the copy promotes LDR→staging→main via the
      normal drain (fail-safe during transition — the old staging-direct copy on `main` keeps working until the new one
      lands). First organic internal-dep bump post-promotion validates it lands on LDR not staging. Repo:
      unified-trading-pm (template ✅) + 24 repo copies (rollout ✅).
- [ ] [CI] P2. **Finding (2026-06-18 flow audit): `major-bump-issue-handler.yml:183` is a second staging-direct writer**
      — the 1.0.0-graduation handler (`/approve`-gated) clones the target at `--branch staging` (`:155`), bumps the
      repo's own `version =` field, and `git push origin staging` (`:183`). Same divergence CLASS as 1.5a but a
      different axis (package **version**, not a dep **floor**) — lower-risk (rare human-gated event; a bare `version =`
      bump rarely conflicts so the hourly `staging-backmerge-to-ldr` usually rescues it cleanly). Reroute to
      `live-defi-rollout` (`--branch live-defi-rollout` + `git push origin HEAD:live-defi-rollout`) for consistency with
      the LDR-is-SSOT model. NOT folded into the 1.5a change to keep that blast radius scoped to the dep-floor fan-out.
      Repo: unified-trading-pm (template + roll out).
- [ ] [SCRIPT] P3. **Finding (2026-06-18): stale duplicate
      `scripts/propagation/templates/update-dependency-version.yml`** — a SECOND copy of the workflow with OLD line
      numbers (`ref: staging` `:49` / `push origin staging` `:213` / `--base staging` `:251`), separate from the rollout
      SSOT `scripts/workflow-templates/`. No consumer found in a `grep -rn 'propagation/templates' scripts/`, so it
      appears orphaned — but if a repo-bootstrap path reads it, it would re-introduce the staging-direct behavior on a
      new repo. Confirm it is dead and **delete it** (delete-deprecated-code rule), or if a bootstrap consumes it, point
      that consumer at the `workflow-templates/` SSOT. Repo: unified-trading-pm.
- [x] ✅ [SCRIPT] P2. ~~Close the mtds rollout gap (`staging-backmerge-to-ldr.yml`)~~ — **DONE / STALE: verified
      2026-06-18 `market-tick-data-service/.github/workflows/staging-backmerge-to-ldr.yml` is PRESENT** (rolled out
      since the 2026-06-17 finding). The gap is closed; back-merge is still FF-only by design (it can't rescue a
      divergent staging-direct floor edit — which is WHY 1.5a/land-on-LDR is the real fix, not the back-merge).
- [ ] [INFRA] P1. One-time clean-start reconcile: bring the current staging-only floor bumps (e2e-testing /
      features-service / greeks-direct) DOWN to `live-defi-rollout` and regen all affected locks **on LDR**, so
      LDR/staging/main locks are byte-identical before the flip (use the `staging_clean_start` force-sync pattern). Do
      NOT regen per-branch independently — that is the runaway-restart trap the issue documents.

**Phase 1.5b — flip to frozen + unify local with CI (the parity win — gated on 1.5a):**

> **DECISION + validation (2026-06-18, operator Harsh) — Option A: keep current WORKING external deps; do NOT
> mass-upgrade.** The fleet `uv lock --upgrade` validation (regen→QG, tier-ordered, 22 repos) proved the latest external
> set is NOT all safe: **16/22 passed QG on latest deps; 6 failed** — (a) **3 real dep breaks** (fastapi 0.137.2 /
> starlette 1.3.1 wrap included routers as `_IncludedRouter` (no `.path`) → break `[r.path for r in app.routes]`
> route-introspection in strategy-service / client-reporting-api / features-service); (b) **2 pre-existing
> version-alignment blocks** (deployment-api, system-integration-tests — QG pre-flight, NOT dep-related); (c) **1 to
> investigate** (alerting-service — `test_synthetic_false_does_not_log_suppressed_event`). So 1.5b ships the **current
> working locks** under `--frozen` (they pin the deps the repos run today), **caps fastapi/starlette** so a future
> `--upgrade` can't pull the breaking versions (DONE in `workspace-constraints.toml`: `fastapi<0.137` /
> `starlette>=1.1.0,<1.3.0`), and defers the one-by-one external-dep upgrades (incl. the fastapi/starlette
> `_IncludedRouter` fix) to `issues/cve_affected_pinned_deps_remediation_2026_06_18.md`. **Remaining steps (ordered):**
>
> 1. Revert the 22 `--upgrade` regens → current working locks (we ship current, not latest).
> 2. Roll the fastapi/starlette cap into the 14 declaring repos' pyproject + `canonical-dependency-manifest.json`; regen
>    those locks (pins the working version within the cap).
> 3. **Smoke `--frozen` install-semantics on ONE repo before templating** — `uv pip install -e .` → `uv sync --frozen`
>    changes venv/prune behaviour (siblings are editable sources in the lock; confirm `uv sync --frozen` installs them +
>    root + externals into the QG venv without pruning, else reorder). Get the exact working command FIRST.
> 4. Flip `--frozen` in the 3 templates (CI `:459`, `base-service.sh:331`, `base-library.sh:191`) per the smoke result.
> 5. **Mode-B validate** fleet-wide: current locks + caps + `--frozen` + QG (the actual end-state) — tier-ordered.
> 6. On green, commit + roll out; then the guardrail (floor-vs-pin, NOT `uv lock --check` — it treadmills on the semver
>    `version =` bumps) + the DOCS rule.

- [x] ✅ [CI] P1. **DONE — PM@PR#398 (merged main 2026-06-18).** CI `uv sync` → `uv sync --frozen`. **No 24-repo rollout
      needed:** the per-repo `.tmpl` workflows `uses:` the SINGLE reusable
      `unified-trading-pm/.github/workflows/python-quality-gates-v2.yml@live-defi-rollout`, so the flip in that one
      reusable workflow (line 461) covers the whole fleet's CI. `--frozen` NOT `--locked` (tolerates the semver `version =` bump).
- [x] ✅ [SCRIPT] P1. **DONE — PM@PR#397 (merged main 2026-06-18).** `base-service.sh` + `base-library.sh`
      `uv pip install -e .` → `uv sync --frozen`, placed BEFORE the editable-sibling loop (prune-immune; smoke-validated
      on greeks: siblings → workspace-root editable, externals → locked working pin, tooling kept). LOCAL == CI byte-for-byte.
- [x] ✅ [CI] P1. **REPLACED per operator Harsh 2026-06-18 — floor-vs-pin guardrail, NOT `uv lock --check`** (which
      treadmills on the semver CI-side `version =` bump). PM@PR#397 ships
      `scripts/quality_gates/check_lock_satisfies_pyproject.py` (BLOCKING in `base-*.sh`): every external lock pin must
      satisfy its pyproject range; skips editable/internal sources; validated (synthetic catch + 22-repo no-false-positive
      + exercised in-QG across Mode-B).
- [x] ✅ [DOCS] P1. **DONE — PM@PR#397.** `cursor-configs/CLAUDE.md`: "CI **and local `quality-gates.sh`** install via
      `uv sync --frozen` (1.5b local↔CI parity, the lock is the install SSOT)."
- [ ] [DOCS] P3. **Stale codex value (found in the 2026-06-18 flow audit):** `codex/08-workflows/ci-cd-flow.md:460`
      states the back-merge drift-tick is `schedule: */20`, but the **deployed** `main-backmerge-to-ldr.yml:42` (+
      template) is `cron "0 * * * *"` (hourly, relaxed 2026-06-11 to cut Actions spend). Root CLAUDE.md already matches
      hourly; fix the codex doc body line.

> **1.5b SHIPPED (2026-06-18, slot-3) — Mode-B green (16/22 pass, the rest pre-existing/remediated); PM-core PR#397 +
> CI-v2 PR#398 MERGED to `main`; **15/15 repo caps** + e2e/SIT stale-lock fixes on LDR. The features GCP unit-test bug
> was FIXED (mock the loader) so its cap shipped too → `check-dependency-alignment.py` is `aligned: true` (0 issues).**
> Option-A cap + frozen
> flip executed. (a) Capped fastapi `>=0.115.0,<0.137.0` + starlette `>=1.1.0,<1.3.0` in the **15 declaring repos'**
> `[project.dependencies]` (14 fastapi ∪ trading-agent-service for starlette — trading-agent was MISSING from the earlier
> 14-list; enumerated from the real dep arrays, not assumed), in `workspace-constraints.toml`, and regenerated
> `canonical-dependency-manifest.json` from the capped constraints (generator reads constraints). (b) `uv lock` (plain,
> keep-pins) on all 15 → every pin lands <0.137 / <1.3.0 (rc=0; UTL starlette 1.3.1→1.1.0, fastapi pins 0.134–0.136.3
> kept; incidental in-range type-stub/patch freshening on a few stale locks, benign + QG-gated). (c) Flipped
> `uv pip install -e .` → `uv sync --frozen` in `base-service.sh` + `base-library.sh` (sync BEFORE the editable-sibling
> loop — **prune-immune**: a typecheck-only sibling absent from the lock would otherwise be pruned right after install)
> and `python-quality-gates-v2.yml:459`. (d) Smoke-validated on greeks: `uv sync --frozen` synced the venv to the locked
> working pins (starlette 1.1.0 / fastapi 0.136.3 / pytest 9.0.3 — downgraded the upgraded leftovers), siblings stayed
> editable-local (dep-content gate intact), QG green 66 s. (e) Full tier-ordered Mode-B QG running across the fleet.

- [ ] [SCRIPT] P2. **FINDING (1.5b, 2026-06-18): `propagate-canonical-versions.py` silently SKIPS ceiling-first specs.**
      `_replace_dep_spec` (`scripts/propagation/propagate-canonical-versions.py:93-107`) loops separators
      `[">=","<=","!=","==",">","<","~="]` and **`return line` on the FIRST separator found with `idx>0`, even when the
      parsed pkg_name is wrong**. For a ceiling-first spec `"fastapi<1.0.0,>=0.115.0"` it finds `>=` first → pkg_name
      `fastapi<1.0.0,` → not in constraints → returns the line UNCHANGED, never trying `<` (which would correctly parse
      `fastapi`). Impact: propagation would NOT cap fastapi in the ~11 fleet repos that write it ceiling-first (dry-run
      flagged only 9 of 15 declarers). 1.5b used a scoped `sed` instead, so the cap is complete; this is a latent silent
      gap for any FUTURE canonical rollout. Fix: parse the package name at the EARLIEST operator position across all
      operators (`idx = min((i for s in seps if (i := spec.find(s)) > 0), default=-1)`), not iterate-and-return-on-first.
      Repo: unified-trading-pm.
- [ ] [INFRA] P2. **FINDING (1.5b, 2026-06-18): canonical-dependency alignment is ADVISORY + has pre-existing drift.**
      TWO canonical sources — `workspace-constraints.toml` (read by `propagate-canonical-versions.py`) and
      `canonical-dependency-manifest.json` (read by `check-dependency-alignment.py`, generated FROM constraints by
      `generate_canonical_dependency_manifest.py`) — silently drift if one is edited without regenerating the other (1.5b
      hit this: capped constraints, manifest stale until regenerated). `check-dependency-alignment.py` reports
      `aligned: false` with misalignments NOT caused by 1.5b: **pyarrow** `>=23.0.1,<24.0.0` in 5 repos (unified-api-contracts,
      execution-service, features-service, market-data-processing-service, ml-service), **python-multipart**
      `>=0.0.31,<1.0.0` in fund-administration-service (the failure-mode-B CVE case this very plan describes), + starlette
      floors (resolved by the 1.5b cap). The checker also reads TRANSITIVE starlette specifiers from `uv.lock` (`>=1.0.1`),
      not just `[project.dependencies]`, so some reports are noisy. PM is actively pushed with alignment red → the "never
      push PM unless aligned" rule is advisory, not hard-enforced today. A focused alignment-hygiene pass (cap-fix pyarrow
      + python-multipart, fix the propagation bug above, reconcile the two sources, decide if alignment should hard-block)
      is its own follow-up — OUT of 1.5b scope (scoped-change discipline: do not mass-sweep pyarrow under the uv banner).
      Repo: unified-trading-pm + the 5 pyarrow repos + fund-administration-service.
- [ ] [SCRIPT] P3. **FINDING (1.5b, 2026-06-18): the `--ignore-vuln` block is DUPLICATED across `base-service.sh` +
      `base-library.sh` and had DRIFTED.** `base-service.sh:1198` already carried the two starlette CVEs
      (CVE-2026-54283/-54282, added in the 2026-06-15 advisory batch) but `base-library.sh` did NOT — so when the 1.5b
      cap lowered the starlette floor 1.3.1→1.1.0 (re-exposing them), every LIBRARY repo with starlette went red in QG
      while service repos stayed green (incident: UTL Mode-B fail; UAC passed only because it declares no starlette).
      FIXED 2026-06-18 by syncing base-library.sh to base-service.sh (+ a comment). Root hazard remains: two hand-kept
      copies of a ~20-entry ignore list silently diverge. Extract the `--ignore-vuln` argument list to a SINGLE shared
      shell constant (e.g. `qg-common.sh` `PIP_AUDIT_IGNORE_VULNS`) sourced by both bases, so a CVE add/lift edits ONE
      place. Repo: unified-trading-pm (`scripts/quality-gates-base/`).
- [x] ✅ [TEST] **P1 DONE (2026-06-18) — FIXED + shipped → alignment GREEN (`aligned: true`, 0 issues, 15/15 capped).**
      The proper fix: the `orchestrator` fixture in `test_calendar_orchestrator_capture_status.py` now mocks
      `EconomicCalendarLoader` (`load_all_events()` → `{}`) so the unit test never builds a real GCP client — 5 tests pass
      under `--block-network`, full features QG green (378 s); the test-fix + cap were quickmerged to features LDR.
      **Original diagnosis retained:** features-service cap can't ship → fleet PM-quickmerge alignment block (1.5b, 2026-06-18).
      14/15 caps are on LDR + the manifest cap is MERGED (PR#397). features-service's cap (pyproject `fastapi<0.137.0`)
      is correct + ready in the slot tree but CANNOT quickmerge: its Pass-1 QG is red on a PRE-EXISTING bug —
      `tests/calendar/unit/test_calendar_orchestrator_capture_status.py` (a *unit* test) makes `CalendarOrchestrationService`
      init a real GCP client that authenticates to the GCP metadata server (`192.178.211.95`) under `--block-network`
      (the test mocks storage but NOT the GCP auth → ~27 `SocketConnectBlockedError` + a gRPC `_InactiveRpcError`). The
      cap FIXED features' starlette `_IncludedRouter` break; this GCP-auth debt is orthogonal (present in the
      `--upgrade`-era log too) and features-service has NO `requires_credentials` skip hook (so marking won't skip it).
      **CONSEQUENCE:** `check-dependency-alignment.py` (the PM-quickmerge `aligned:true` gate — no baseline) flags features
      fastapi (committed-uncapped vs merged-capped manifest) → **BLOCKS PM script/manifest quickmerges fleet-wide** until
      features' cap lands. **Resolution options:** (a) **proper** — mock the GCP client (or route it through the
      cloud-agnostic `get_storage_client`/`UnifiedCloudConfig` wrapper) in the test → quickmerge features' cap
      [features-service work]; (b) **interim** — direct-push features' cap (pyproject+lock) to LDR (provenance-exempt: no
      `.py`/`.ts` source change), re-aligning the gate; features' own staging CI stays red on the pre-existing bug, but
      features was already blocked; (c) operator/coordination call. The cap is re-derivable from the merged canonical
      regardless. Repo: features-service (test) + unified-trading-pm (alignment).

> **HOLD until 1.5a lands:** do NOT run a fleet-wide `uv sync` + commit-lock pass — it re-diverges LDR↔staging locks
> and restarts the runaways. Stop any active runaway the convergence-safe way (match pyproject to staging on LDR; do not
> touch the lock).

### Phase 2 — MAJOR bump triggers a CASCADE of quality gates (full SIT in dependency order) — P1

- [x] 🟡 [SCRIPT] P1. WIRED 2026-06-09 — `update-repo-version.yml` now dispatches `cascade-qg-trigger` to
      `cascade-qg-ordering.yml` when `bump_type == major || is_breaking` (the cascade was orphaned before — nothing
      dispatched the trigger). `cascade-qg-ordering.yml` already runs QG across transitively-affected repos in
      **topological level order** (parallel within level, sequential across, fail-fast + invalidate downstream).
      **Pending live verification**: a real MAJOR bump must exercise it end-to-end (can't tick fully ✅ on smoke alone).
- [x] 🟡 [SCRIPT] P1. WIRED — the trigger's `if:` excludes minor/patch (`bump_type == major || is_breaking` only), so a
      non-breaking bump fires NO cascade/SIT fan-out (rides the consumer's range pin). Pending live verification.
- [x] ✅ [RESOLVED-STALE: cascade-qg-ordering own concurrency group, fixed 2026-06-10] [SCRIPT] P1. **DEFECT (live-found
      2026-06-10): cascade-qg-ordering runs are evicted from the queue by the shared `manifest-update` concurrency group
      before any job starts** — UTL 0.5.0 dispatch fired (run 27264972415, 08:54:52Z) but was cancelled in 4 s with zero
      jobs; all 5 most-recent cascade runs are cancelled/failure, so the cascade has never executed a level live.
      `cancel-in-progress: false` only protects a RUNNING run — GitHub keeps a single PENDING slot per group, so any
      newer manifest writer (version-bump, ci_status) evicts a queued cascade. Fix: give the cascade its own concurrency
      group (manifest mutation can be made atomic via retry-with-rebase as staging-to-main already does) OR a
      queue-tolerant re-dispatch/retry so eviction is not silent loss. The H2 serialise-with-manifest-writers intent
      must not cost the cascade its execution. Repo: unified-trading-pm
      (`.github/workflows/cascade-qg-ordering.yml:32-36`).
- [x] ✅ [SCRIPT] P1. **DEFECT-2 (separated out 2026-06-10): dependency-FIRST ordering** — DONE 2026-06-10 —
      unified-trading-pm@c4e9f3c9c. Mechanism: `update-repo-version.yml` gained a **bounded resolvability gate**
      (`resolve-gate` step) between the digest-resolution steps and the consumer dispatch loop. It polls (10 × 30 s ≈ 5
      min — kept under 10 min because the run HOLDS the `manifest-update` concurrency group and a long hold risks the
      DEFECT-1 pending-slot eviction of sibling version-bump runs) until the bumped version is resolvable **the way
      consumers resolve it** (clone_repo() order: exact tag `v{VERSION}` via `git/ref/tags`, OR the dep's `{branch}`
      pyproject carrying `version = "{VERSION}"` via the contents API — NO workflow creates release tags today, so the
      branch pyproject is the canonical fresh-bump location). Success → fan-out + cascade dispatch proceed (both
      `if:`-gated on `resolve-gate.outputs.resolvable`). Timeout → NO blind dispatch: `::warning` + re-dispatch of the
      SAME `version-bump` event with `fanout_retry: N+1` (max 3, chain-depth loop-breaker idiom; `chain_depth`
      preserved; original `bump_type` rides the retry payload so the retry run doesn't recompute it as "patch" off the
      already-updated manifest — a `bump_override` hook in the manifest python honors it, and retry runs skip the PM
      self-bump so they never mint extra PM versions). Retries exhausted (or retry-dispatch HTTP failure) →
      `retries_exhausted=true` → new `notify-fanout-unresolvable` Slack job (CRITICAL, notify-slack.yml pattern).
      Cascade gating justified: its per-repo QGs clone the dep exactly like consumer QGs — firing it unresolvable
      guarantees a spurious red cascade + spurious escalation; on retry it fires with major/breaking routing intact.
      Verified: yaml.safe_load OK, actionlint exit 0, `bash -n` on all 3 modified run scripts, both python heredocs
      compile. Residual: a retry dispatch itself can be evicted by the `manifest-update` pending-slot race — that is the
      DEFECT-1 concurrency item above, not re-tracked here. Repo: unified-trading-pm (`update-repo-version.yml`).
      **[KNOWN TENSION 2026-06-10]**: the resolve-gate's <=5-min hold of the manifest-update concurrency group increases
      pending-slot eviction pressure on sibling manifest writers (one pending slot per group) — frequent ci-status
      writers can evict each other during the hold → stale ci_status → dep-order gate friction. Structural fix = the
      ci_status Firestore side-store (per-repo document partitioning,
      plans/active/ci_status_firestore_side_store_2026_06_10.md) — its dual-write sequencing guard is therefore doubly
      important. **[OBSERVED LIVE ~19:50Z same day — eviction is eating version-bump runs THEMSELVES]**:
      update-repo-version runs CANCELLED at 13:34(×4)/14:57/17:38 — so the digest fan-out for UTL's new image
      (`d41011e1…`, built 17:06) NEVER dispatched and consumers' pins stayed at the morning's `058d589f…` (a direct
      cause of the first digest-pinned build failures, alongside the unauthenticated-pull defect — the latter fixed in
      `cloudbuild-service-template.yaml`'s digest-aware pre-pull, which makes stale-but-existing pins build correctly
      and demotes this eviction class from build-breaking to staleness-lag). Raises the side-store's priority and/or a
      dedicated concurrency group for version-bump runs (mirror of the cascade's own-group fix).

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

- [x] ✅ [SCRIPT] P0. **RESOLVED 2026-06-09 — see "RESOLUTION LOG — 2026-06-09" below (DEFECT 1 FIXED,
      `unified-trading-pm@0cfac845e`, semver-agent.yml.tmpl pickaxe baseline-resolution + module→package-move regression
      test, rolled out 24/24); verified 2026-06-10 (commit + test + template all in-tree). DEFECT 1 — `is_breaking=true`
      was stamped for a bump the canonical differ calls NON-breaking → the cascade + fleet staging-lock fired
      SPURIOUSLY.** On 2026-06-09 13:48Z `update-repo-version.yml` locked staging with
      `locked_reason="Breaking MINOR bump cascade: unified-api-contracts=0.5.0 (pre-1.0.0)"`,
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
- [x] ✅ [SCRIPT] P0. **RESOLVED 2026-06-09 — see "RESOLUTION LOG" below (incident cleared: 18 spurious dep-update
      fan-out PRs CLOSED incl. execution-service#232, lock healed; the durable dependency-first-ordering fix tracked in
      Phase 6.x — see line ~320 FROM-digest ratchet + cascade-ordering items); verified 2026-06-10. DEFECT 2 — even IF
      it were breaking, the SIT could not converge: the consumer was pinned to a UAC version stranded on `staging`,
      unresolvable from where its CI clones.** The cascade auto-opened execution-service dep-update PR #232
      (`feat!: update unified-api-contracts to 0.5.0`, head `dep-update/unified-api-contracts-0.5.0` → `staging`) which
      is a PURE pin bump `unified-api-contracts>=0.3.0` → `>=0.5.0` (no code change). Its `quality-gates-v2` FAILS at
      the **dep-clone range gate BEFORE any test/typecheck**: `check_version_constraint()` clones UAC by branch-fallback
      (head-branch-name → manifest-tag v0.2.0 → **main=0.3.0**) and never tries the PR's BASE branch (`staging`, where
      0.5.0 actually lives) nor a v0.5.0 tag (none exists) → `assert_dep_in_range` fails `resolved 0.3.0 < floor 0.5.0`.
      This is the dependency-ORDER violation: the cascade pinned the CONSUMER (execution-service) to a UAC version that
      the DEPENDENCY (UAC) had not yet promoted to a resolvable location (main/tag). Per `cicd_contract_hardening` §
      ROOT FIX line ~122 ("UAC move together; non-clone repos follow; then re-trigger the stuck heads") the dependency
      must converge FIRST. UAC has a 3-way version split (main 0.3.0 / LDR 0.4.0 / staging 0.5.0) and NO open UAC
      `staging→main` PR. **Fix (when a breaking cascade IS genuine):** the version-aware clone must resolve the
      dependency from the consumer-PR's BASE branch (or the cascade must promote the dep dependency-first + tag) before
      pinning + re-triggering consumers. repo: unified-trading-pm
      (`setup-workspace-from-manifest.sh check_version_constraint` + cascade ordering).
- [x] ✅ [SCRIPT] P0. **DONE 2026-06-09 (operator chose "full fix: clear + durable" + authorized admin) — see
      "RESOLUTION LOG" below; verified 2026-06-10. RESOLUTION for THIS incident:** clear the spurious staging-lock
      (retry-exhausted + differ says non-breaking) exactly as the 2026-06-07 session-#3 precedent did, and close
      execution-service PR #232 (revert the unnecessary pin — the existing `>=0.3.0,<1.0.0` range already absorbs 0.5.0;
      promotion is PULL not PUSH for non-breaking minors). UAC then promotes LDR→staging→main normally via its range (PR
      #112 LDR→staging is open + MERGEABLE). Provenance: execution-service consumes NONE of the changed UAC symbols
      (`rg` verified — it imports the `unified_api_contracts.instruction` root facade, not the deleted
      `internal/validation/instruction` subtree; the Infura refs are local script/test strings, not the removed dict
      key).

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
- [x] ✅ [PLAN-HYGIENE] P3. DONE 2026-06-12 — `check_credential_ask_orphans.py` now counts ONLY OPEN `- [ ]`
      credential-ask todos (`CHECKBOX_ITEM_RE` tightened `\[[ xX]\]` → `\[ \]`): a COMPLETED `[x] ✅` ask is resolved,
      never an orphan. Orphan count dropped to 0 (the stale "baseline 11" was actually 2 with the `[x]`-inclusive
      regex); baseline ratcheted DOWN to 0 (`credential_ask_orphans_baseline.yaml`) so the gate now enforces
      zero-orphans. repo: unified-trading-pm (`check_credential_ask_orphans.py`).

### Phase 4 — MAJOR/MINOR classification matrix refinement — P2

- [x] ✅ [SCRIPT+DOCS] P2. DONE 2026-06-09 (PM@<this commit>) — closed the highest-value schema-contract gap: the differ
      only captured **annotated** class attrs (`ast.AnnAssign`), so **Enum members** (plain `FOO = "foo"` assigns — the
      UAC StrEnum contracts) were invisible → removing/renaming a member or changing its serialized VALUE classified as
      NON-breaking. Added `_is_enum_base()` + enum-member capture into `fields` (keyed `Class.MEMBER`, value = the
      literal), so member removal AND value-change now trip the removed/changed-field breaking checks; a NEW member
      stays additive (non-breaking), and a non-Enum class constant is NOT tracked (no false trips). 4 regression tests
      added (`test_detect_breaking_change.py`, 12 pass). Matrix documented in `codex/08-workflows/ci-cd-flow.md` §
      "Breaking = public-surface change".
- [x] ✅ [DOCS] P3. DONE 2026-06-12 — added a **Scope boundary** bullet to `codex/08-workflows/ci-cd-flow.md` §
      "Breaking = public-surface change" cross-linking the two non-code contract surfaces to their own SSOTs: manifest
      `schema_version` → `codex/02-data/availability-manifest-and-data-status.md`; GCS path/partition keys
      (`pipeline_mode=`/`asset_group=`/`feature_group_version=`) → `pipeline-mode-partition.md` +
      `feature-formula-versioning.md`. Boundary now explicit (these are real contract changes but do NOT trip the CODE
      differ — coordinate via the data-track SSOT + single-walk migration). No differ change.

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
- [x] ✅ **[DONE 2026-06-12 (swept, CLEAN — no fixes needed) — `rg 'from packaging|import packaging' -g '*.sh'` across
      all 25 repos: every per-repo `setup.sh` is clean (none import packaging); the only clone-time `.sh` importing
      packaging, `setup-workspace-from-manifest.sh`, is already the stdlib-only PEP440 comparator (the 2026-06-09 fix —
      the line-102 hit is a comment about the removed old code); `check-internal-advisories.sh` runs POST-install
      (operates on `get_installed_packages()`) so packaging is present and its `except ImportError→exit(0)` is a
      loud-warned guarded skip, not a pre-uv-sync silent no-op (verified install-order per this item's note → leave it).
      No latent silent-no-op instances remain.]** [SCRIPT] P3. **Fleet sweep for the same packaging-no-op pattern in
      OTHER repos** — `rg "from packaging" $(setup     scripts)` across all 25 repos' `setup.sh` / clone-time scripts;
      any that import `packaging` BEFORE `uv sync` with an `except: pass/exit(0)` mask have the same latent
      silent-no-op. (`check-internal-advisories.sh` in PM imports `packaging` too but runs post-install — verify
      install-order before touching it.) Fix each to stdlib; deliberate per-repo (changes resolution behavior).
- [x] ✅ **[DONE 2026-06-12 — system-integration-tests@341446c9: `instruments-service>=0.30.0` → `>=0.4.0` (matches the
      de-inflated true version); QG green 135s]** [SCRIPT] P2. **Lower SIT's phantom-era instruments-service floor** —
      `system-integration-tests/pyproject.toml` still pins `instruments-service>=0.30.0,<1.0.0`; the runaway-semver
      phantom was de-inflated to a coherent **0.4.0** (main=staging=LDR, tag `v0.4.0`), so this `>=0.30.0` floor is
      stale (true version 0.4.0). Non-blocking today (content-first clone resolves the editable path source) but should
      match the real version → set `>=0.4.0,<1.0.0`. **MIGRATED FROM:**
      `plans/archive/issues/instruments_service_version_phantom_2026_06_11.md` § Follow-up (archived 2026-06-12, the
      phantom itself RESOLVED 2026-06-11).

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

- [x] ✅ [INFRA] P1. **COMPLETE 2026-06-10 — the full FROM-digest ratchet, end to end.** Final state: 16/16 consumer
      Dockerfiles digest-pinned on LDR; cloudbuild fleet (18 repos) carries the digest-aware pre-pull (proof: mtds build
      `fc2d4b07` SUCCESS through `FROM @${BASE_IMAGE_DIGEST}`); **STEP 5.79 flipped to HARD-FAIL**
      (unified-trading-pm@52f33275f — legacy `${`-warn branch closed; blast radius verified zero pre-flip, incl.
      instruments' indirect `ARG BASE_IMAGE=` shape). Build-path incidents found+fixed en route: unauthenticated daemon
      digest-pulls (digest-aware pre-pull in `configs/cloudbuild-service-template.yaml`), GCB substitution grammar (×2
      silent rejections → `check_cloudbuild_substitutions.py` QG STEP 5.19 + render gate +
      `cloud-build-failure-watcher.yml`; see
      `issues/cloudbuild_silent_failures_no_alerting_no_validation_2026_06_10.md`). Remaining related-but-separate
      items: the registry-poller edge (P2 below) + deployment-api BoM surface (P2) + eviction-class fan-out reliability
      (KNOWN TENSION note). Original task text below: ~~Complete the 5.79 FROM-digest ratchet~~ — drive every production
      Dockerfile's `FROM` from `:latest`/`:tag` → `@sha256:<digest>` and flip STEP 5.79 from PENDING-RATCHET to BLOCKING
      (`base-service.sh:2221-2264`). Resolve the digest at build time (cloudbuild reads the freshly-pushed base image's
      `RepoDigests` / Cloud Run revision digest, injects via `--build-arg BASE_IMAGE_DIGEST`). Done = rebuilding any
      service commit yields a byte-identical image (reproducibility) AND the Dockerfile records exactly which UTL/UAC
      went in (provenance). This is the operator's answer to both "reproducible cloud builds" and "reverse-engineer the
      code version in a build". [DESIGN SHARPENED 2026-06-10: STEP 5.79 (base-service.sh:2361-2413) is currently
      TOOTHLESS against the canonical FROM lines — the line-2395 `${` exemption skips every FROM that uses
      `${PROJECT_ID}`. Sound mechanism: (1) each consumer Dockerfile carries a checked-in `ARG
      BASE_IMAGE_DIGEST=sha256:<digest>` default consumed in FROM; (2) digest freshness rides the existing
      dependency-update fan-out (update-repo-version.yml → per-repo update-dependency-version.yml PRs rewrite the ARG
      line on base-image publish); (3) THEN narrow 5.79: registry FROMs must carry @sha256 literally or via an ARG
      BASE_IMAGE_DIGEST default in the same Dockerfile — closing the blanket `${` skip. Sequencing hard requirement:
      Dockerfile ARG rollout lands fleet-wide BEFORE the 5.79 narrowing, else every repo QG reddens.] **[MACHINERY
      SHIPPED 2026-06-10 — remaining = per-repo conversion ships]** Landed in PM: (a)
      `scripts/propagation/add-dockerfile-digest-arg.py` (idempotent Dockerfile rewriter, handles direct-UTL +
      instruments `ARG BASE_IMAGE=` shapes; `--dry-run/--repo/--digest`); (b) `update-dependency-version.yml`
      template+propagation copy: digest-refresh step (validates optional `base_image_digest` payload, sed-rewrites the
      ARG, digest-only PRs); (c) `update-repo-version.yml`: on a unified-trading-library bump, WIF/SA-key auth → resolve
      `:latest` digest → attach `base_image_digest` to every dependency-update dispatch (non-fatal when unresolvable);
      (d) STEP 5.79 narrowed MONOTONICALLY (converted Dockerfile → strict @digest enforcement; unconverted → legacy
      skip + warn — no fleet redness); (e) PILOT converted: deployment-service/Dockerfile @ sha256:058d589f… (docker
      build --check green). Current digest resolved live via gcloud.
- [x] ✅ [INFRA] P1. **FROM-digest ships — 16/16 LANDED on LDR (completed 2026-06-10 ~19:35Z; pins content-verified on
      each repo's `origin/live-defi-rollout`).** alerting, blr, client-reporting, execution, features, fund-admin (×2
      FROMs), greeks, instruments, mtds, ml, trading-agent, strategy, mdps, agent-orchestrator (6343874 — incl. the
      QG-stub venv-on-PATH fix it surfaced), **deployment-service** (BoM + pilot — re-landed from
      `origin/wip-preserve/bom-deployment-service-2026-06-10` after a live-peer reset; the re-land itself shipped
      through and thereby PROVED the new quickmerge committed-ahead fall-through @331c7c183), and **deployment-api** (×2
      Dockerfiles — landed in the all-deps-clean window after the peer's UTL/strategy sweep finished; QG-green +
      quickmerge). Collision handling per liveness rules throughout: peer WIP protected, discarded work recovered via
      wip-preserve, three latent tooling defects the arc exposed all fixed same-day (committed-ahead stranding
      @331c7c183, checkout-blind dep-gate heal @1537b36dc, in-repo .qg_cache @4c6c5679d). **NEXT (the final ratchet)**:
      flip STEP 5.79's legacy `${`-skip to hard-fail — see the conflict-guard below. **[CONFLICT-GUARD 2026-06-10 —
      operator-ratified]**: the final 5.79 hard-fail flip is GATED on a REAL cloud build (Cloud Build / buildspec)
      proving the @${BASE_IMAGE_DIGEST} FROM path end-to-end — docker build --check is NOT sufficient; flipping first
      could block the fleet on an unproven build shape.
- [ ] [SCRIPT] P2. **Registry-poller for the rebuild-without-bump edge** — the digest fan-out hooks UTL VERSION bumps;
      an image rebuild with no version bump (infra-only rebuild) never refreshes consumer digests. Add a `*/6h` PM
      workflow: gcloud-resolve `:latest` digest → dispatch `dependency-update` with `base_image_digest` to UTL consumers
      (stateless — consumer sed is idempotent, unchanged digest → no PR). Reuse the WIF/SA-key auth pattern from
      `update-repo-version.yml`.
- [x] ✅ **[DONE 2026-06-12 — `deployment-service/deployment_service/bom.py` exists, `DeploymentRegistryEntry` carries
      the BoM fields, and `VersionRegistry.register_version` is now WIRED on the live-deploy path
      (`live_deployment.py`); shipped `deployment-service@f9c0920`. Code present on LDR. (Follow-up: surface in GET
      /api/deployments — still open below.)]** [CODE] P1. **Deployment-registry bill-of-materials — record digest +
      commit + dep-versions** (deployment-service). TODAY the registry persists ONLY a mutable `image_tag`
      (`monitor.py:39` / `live_deployment.py:42,63` / `backends/base.py:135`); the `git_commit` field exists
      (`monitor.py:40`) but its writer `VersionRegistry.register_version` (`monitor.py:540`) has ZERO callers
      (dead/unwired), and NO image-digest / internal-dep-version is stored anywhere — so "what code is in prod right
      now" is NOT queryable. On the **live** deploy path (`DeploymentRegistryEntry`/heartbeat extras,
      `deployments_registry.py:146-169`, OR wire up the dead `VersionRegistry`): (a) resolve the deployed tag →
      immutable `@sha256:` digest (Cloud Run revision / Artifact Registry `RepoDigests`) into a new `image_digest`
      field; (b) stamp `git_commit` from `$SHORT_SHA`; (c) stamp `dep_versions: dict` (UTL/UAC + base-image digest).
      Store: GCS `gs://deployment-metadata-{pid}/versions/…` (the existing VersionRegistry target) /
      `gs://deployment-scripts-{pid}/deployments/…`; expose via deployment-api `GET /api/deployments`. Done = "what's
      deployed in prod + exactly what code is in it" is a single queryable BoM. **[IMPLEMENTED 2026-06-10 — in
      deployment-service tree, ship parked on the UTL dep-order gate]**: `DeploymentRegistryEntry` +3 typed fields
      (legacy-safe loads); new `deployment_service/bom.py` (resolution SSOT: config passthrough
      `GIT_COMMIT`/`IMAGE_DIGEST`/`BASE_IMAGE_DIGEST` + importlib.metadata dep versions + digest-from-pinned-ref only —
      omits-not-fabricates); BoM stamped at both registry writers (`deployment_heartbeat.py cmd_register` +
      `heartbeat_cli.py` daemon, round-trips via HeartbeatEntry.metadata); dead `VersionRegistry.register_version` WIRED
      on the live deploy path (`LiveDeployer.deploy` → `_register_deployed_version()` post-health-gate, best-effort).
      33/33 new+touched tests, 239 adjacent green, 0 new basedpyright errors. Cloud Run live services: `run_v2` exposes
      no tag→digest resolve — provenance = FROM-digest ratchet + passthrough (documented in code).
- [x] ✅ **[DONE 2026-06-12 — deployment-api@33be49cba: added `image_digest`/`git_commit`/`dep_versions` to
      `VmDeploymentEntryModel` so the `asdict(entry)` keys stop being pydantic-dropped + reach the response; regression
      test `tests/unit/test_vm_deployment_bom.py` (3 cases: model declares, asdict-passthrough, honest-empty default);
      QG green 201s]** [CODE] P2. **BoM follow-up: surface the three fields in `GET /api/deployments`** —
      deployment-api's `VmDeploymentEntryModel` (`deployment_api/routes/vm_deployments.py:42`) builds from
      `asdict(entry)` and pydantic silently DROPS unknown keys, so BoM reaches the GCS rows but not the API response
      until the model adds `image_digest` / `git_commit` / `dep_versions` (3-line change). repo: deployment-api.

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
