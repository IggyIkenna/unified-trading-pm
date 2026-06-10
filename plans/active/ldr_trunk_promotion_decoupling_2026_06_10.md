---
title: LDR-trunk promotion decoupling — quickmerge lands on LDR, tier-drain promotes, hotfix is the only break-glass
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
created: 2026-06-10
locked_by: live-defi-rollout
related_plans:
  - plans/active/cicd_contract_hardening_2026_06_01.md
source:
  - plans/active/cicd_contract_hardening_2026_06_01.md
---

# LDR-trunk promotion decoupling

> **Parent / umbrella:** this plan is a focused tranche OF
> [`cicd_contract_hardening_2026_06_01.md`](cicd_contract_hardening_2026_06_01.md). It finishes the "staging-first path
> unused / staging behind LDR" thread (that plan's item H / todo @2559) by making the Tier-C drain the **sole**
> LDR→staging path and removing the per-commit staging coupling from `quickmerge`. Read the conflict reconciliation (§4)
> before touching any shared surface.

## Why (the trigger)

Two live symptoms on 2026-06-10 share one root cause — **per-commit promotion couples shipping to staging state**:

1. **BLR `main` went RED** with `dependency unified-trading-library: resolved 0.4.0 < floor 0.5.0`. The
   `feat(docker): pin base image via ARG BASE_IMAGE_DIGEST` commit was **direct-pushed to `main`** (the FROM-digest
   Phase-6 rollout used the direct-to-main carve-out). A full QG on a `main` push resolves internal deps **against
   main-tier** (`BRANCH = github.ref_name`), where UTL is still 0.4.0 / only `v0.4.0` is tagged — even though UTL 0.5.0
   is live on staging+LDR. The **same change through LDR→staging** (`base_ref=staging`) resolves against staging-tier →
   finds 0.5.0 → passes. The red is an artifact of bypassing the orderly LDR→staging→main flow.
2. **Staging-lock serialization.** `quickmerge` STAGE 1.5 blocks **every** agent commit while staging is locked for a
   breaking-change SIT — even though `live-defi-rollout` is supposed to be the gateless integration trunk. "Commit a
   million things but each blocks the next" is this gate.

## The model (what changes)

`live-defi-rollout` becomes the **gateless trunk** in practice, not just in docs:

- **`quickmerge --agent --files` lands on LDR and stops there.** No per-unit LDR→staging PR for service repos. The
  commit-quality boundary (local `quality-gates.sh` sentinel) still binds — LDR isn't unguarded, it's
  _server-gate-deferred_.
- **Promotion is the existing tier-ordered batched drain.** `ldr-to-staging-promote.yml` (Tier C) is already
  tier-ordered (`topologicalOrder.levels[]`) and dep-order-gated (`tier_c_promotion_gate.py`). Its cadence moves **6h →
  30min** so "CI on LDR content" (the LDR→staging PR's `quality-gates-v2`, resolving deps against staging-tier) lands
  within ≤30 min. That PR **is** the authoritative server gate.
- **Hotfix is the only break-glass.** `--hotfix` still opens a staging PR and **still hits the staging lock** (correct:
  a queue-jumping change must reconcile with whatever is converging on staging). An exceptional `--hotfix-to-main` opens
  a main PR whose **only gate is `quality-gates-v2` on main** (no SIT, no staging hop). Both require an explicit
  operator signal + a commit-message marker; agents cannot self-authorize.
- **The promote bot promotes only quickmerge-provenanced content (operator direction 2026-06-10).** Two layers, in
  priority order: (1) **promote-PR provenance gate (the enforcement)** — the LDR→staging promote PR runs
  `check_strict_quickmerge.py` over its commit range; any **non-carve-out CODE commit lacking the `Quickmerge:`
  trailer** → the PR is **not merged** (this, not the push, is what stops un-QG'd code reaching staging). Carve-outs
  (`docs(plans):`, dirty-dep, `.github/**`) are legitimately trailer-less and pass. (2) **push tripwire (faster
  detection, optional)** — a non-blocking `push: live-defi-rollout` GHA running the same checker; a violation fires a
  `#ci-failures` alert so a bypass is caught at push, not ≤30 min later at the drain. **LDR itself never runs QG.**
  **Head-of-line is accepted by design:** the promote PR is the whole LDR→staging diff, so one un-promotable commit
  (bypass or red) freezes that repo's promotion until reverted/retro-QG'd — fail-safe, nothing jumps a bad commit.
- **Stale/superseded promote PRs auto-close (no manual cleanup).** A GHA closes any LDR→staging PR whose commits are
  already in `staging` — by **patch-id/content equivalence, NOT SHA** (the drain rebases/squashes → staging SHAs differ;
  a SHA-membership check never matches → never closes). Bundle into the existing `ci_failure_watcher` hygiene.

## Decisions recorded (so they aren't re-litigated)

- **D1 — drop `push:[staging]` QG; staging-green INHERITS from feature-green (operator decision 2026-06-10).** The QG
  that runs on the LDR→staging PR (`pull_request:[staging]`, head=LDR, base=staging) executes on the **exact tree** that
  lands on staging — re-running v2 on the `push:[staging]` event is redundant (same content, same staging-tier
  resolution). So **remove `staging` from the `push:` triggers** in `quality-gates-v2.yml.tmpl` (keep
  `pull_request:[main,staging]` + `push:[main]`). The `STAGING_GREEN` ci_status is **derived from the feature-green
  result** (the LDR→staging PR's pass = `FEATURE_GREEN`) at merge time, not from a staging-branch QG run.
  - **HARD ORDERING (do not reorder):** `STAGING_GREEN` today is written by `ci-status-update.yml` _on a QG pass on the
    staging branch_ — i.e. the `push:[staging]` run. The Tier-C dep-order gate (`tier_c_promotion_gate.py`) **reads**
    `STAGING_GREEN`. So removing `push:[staging]` **before** wiring the inheritance STARVES the dep-order gate → the
    drain jams fleet-wide. Sequence: (1) wire `FEATURE_GREEN→STAGING_GREEN` inheritance in `ci-status-update.yml`, (2)
    teach the @4950 zero-check-run detector that a staging head legitimately has no _push_ check (its gate is the merged
    PR's check), (3) THEN drop `staging` from `push:` in the template + `rollout-workflow-templates.sh`. See todos
    below.
  - We still do **NOT** add a `push: live-defi-rollout` trigger — a raw LDR-push QG has _no_ `base_ref=staging`
    fallback, so it would re-introduce the BLR failure (a dep on staging-but-not-LDR). The staging→main required check
    is unaffected (the `pull_request:[main]` trigger re-runs v2 on the staging head).
- **D2 — local dep-alignment stays main-aligned.** `version-alignment-gate.sh:99-108` deliberately compares local
  `versions{}` vs `origin/main` (not `staging_versions`) to avoid false-blocking the whole promotion window. The
  operator's "build off latest staging" intent is satisfied by **CI tiered resolution** (staging-tier on staging PRs),
  not by changing the local gate. No change to the local gate; instead see todo P1.5 (compose with hardening @4228,
  dep-clone ref-determinism).

## §4 — Conflict reconciliation with `cicd_contract_hardening_2026_06_01.md` remaining todos

Checked all ~50 open todos. **No hard conflicts.** Interactions:

| Hardening todo                                                    | Relationship                                     | Action here                                                                                                                                                                                                                                                                                       |
| ----------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| @2559 staging behind LDR / staging-first unused (P2)              | **This plan completes it**                       | Making the drain the sole path + 30min is the resolution.                                                                                                                                                                                                                                         |
| @4228 QG dep-clone ref-determinism (P2)                           | **Complement / prerequisite-soft**               | The model leans on deps resolving at the _same_ (staging) ref. Cross-link; not blocking — fail today is a mixed-ref edge, our model reduces its blast radius.                                                                                                                                     |
| @4941 sanitize Tier-C squash body `[skip ci]` (P1)                | **Now applies (drain gained a squash fallback)** | The drain now does `--auto --rebase \|\| --auto --squash` (PM@84fe257ae — rebase can't arm on a merge-laden LDR); the squash path re-touches @4941 and was **pre-sanitized** in the same fix (explicit subject/body). The separate `ldr-to-main`/`staging-to-main` squash paths still need @4941. |
| @4950 flag staging head w/ ZERO check runs (P2)                   | **Must adapt (was a blocker)**                   | Dropping `push:[staging]` (D1) makes a checkless staging head LEGITIMATE — the detector must flag only heads with no check AND no merged-PR check (else false-positive on every drain merge). Sequenced todo below.                                                                               |
| @4933 per-cone parallel staging locks (P3)                        | **Composes (future)**                            | 30min drain + per-cone locks compose; lock duration → longest cone. No change needed now.                                                                                                                                                                                                         |
| @4882 4 repos lack `quickmerge.sh` (P2)                           | **Coverage gap**                                 | ml-service et al. won't get the new behavior until they have the symlinked script. Out of scope; cross-link.                                                                                                                                                                                      |
| @4843-4849 sit-gate/cloud-build-router concurrency review (P2/P3) | **Adjacent**                                     | Unaffected; promotion ordering unchanged.                                                                                                                                                                                                                                                         |

## Todos

- [x] ✅ [SCRIPT] P0. **Drain cadence 6h → 30min.** `ldr-to-staging-promote.yml:26` cron `"17 */6 * * *"` →
      `"13,43 * * * *"` (off top/bottom-of-hour). PM-only workflow; must land on PM `main` to fire (scheduled workflows
      fire only from the default branch). — unified-trading-pm@ef76571 (PR #219 → main)
- [x] ✅ [SCRIPT] P0. **quickmerge: land-on-LDR, skip per-unit staging PR for service repos.** After the LDR push, for a
      commit that is NOT PM, NOT `[skip ci]`, NOT `--hotfix` → do **not** `gh pr create --base staging`; print "landed
      on LDR — Tier-C drain (≤30min) promotes to staging". PM→main and `[skip ci]`→main paths unchanged. File:
      `scripts/quickmerge.sh` (early-exit after PR_BASE block). FAIL-SAFE (worst case: promotion waits ≤30min). —
      unified-trading-pm@ef76571
- [x] ✅ [SCRIPT] P0. **quickmerge: decouple LDR commits from staging state.** STAGE 1.5 (staging-lock) and STAGE 1.7
      (dep-tier): guard changed `TO_STAGING=true` → `HOTFIX=true` so only a hotfix-to-staging respects the lock /
      dep-tier gate; normal LDR landings skip them (the drain re-gates dep-order). FAIL-SAFE. —
      unified-trading-pm@ef76571
- [x] ✅ [SCRIPT] P1. **quickmerge: STAGE 1.6 dep-version gate → WARN for non-hotfix, BLOCK for hotfix.** Building
      against a dep that is version-behind-staging is legitimate on the LDR trunk; the drain + SIT catch real
      incompatibilities. Keep the hard BLOCK on the `--hotfix` path (a hotfix must reconcile with staging). —
      unified-trading-pm@ef76571
- [x] ✅ [SCRIPT] P1. **quickmerge: harden `--hotfix` (marker) — DONE.** `--hotfix` now requires a `[hotfix]` marker in
      the commit message (else refuse), in the FLAG VALIDATION block. Keeps the staging-lock respect. —
      unified-trading-pm@305014936
  - [ ] **`--hotfix-to-main` — DEFERRED (design finding).** The naive "PR_BASE=main on the existing flow" is WRONG: the
        PR head is `live-defi-rollout`, so a LDR→main PR would promote the **whole trunk**, not just the hotfix. A
        correct `--hotfix-to-main` needs a **dedicated single-commit branch off `main`** (cherry-pick the fix → PR that
        branch → main, v2-on-main the only gate) + `[hotfix-main]` marker + operator env
        `QUICKMERGE_HOTFIX_TO_MAIN_OK=1` (agents cannot self-authorize). Until built, the operator uses the manual
        relax→push→re-enable path. **Does NOT script a protection bypass.**
- [x] ✅ [DOCS] P1. **codex SSOT update — codex DONE, CLAUDE.md deferred.** Added a "LDR-trunk decoupling" subsection to
      `codex/08-workflows/ci-cd-flow.md` § Two-Pass (land-on-LDR, hotfix-scoped gates, 30min drain, A1 inheritance, D1
      provenance gate, `[hotfix]` marker, `--hotfix-to-main` not-yet-shipped). — unified-trading-pm@305014936
  - [ ] **CLAUDE.md one-liner DEFERRED** until the model is complete (A3 dropped `push:[staging]` + `--hotfix-to-main`
        shipped) — a pointer to a half-built model in the most-loaded context file is premature.
- [ ] [SCRIPT] P1.5. **Compose with @4228 (dep-clone ref-determinism).** Confirm the LDR→staging PR resolves _all_
      internal deps at the staging ref consistently (no mixed staging-new/main-old set). Cross-linked,
      verify-on-first-green.
- [x] ✅ [SCRIPT] P1. **Drop `push:[staging]` QG — STEP 1 of 3 (inheritance FIRST).** Wire
      `FEATURE_GREEN → STAGING_GREEN` inheritance. **Implemented in `python-quality-gates-v2.yml` (the reusable v2
      workflow, pinned `@live-defi-rollout` → live fleet-wide) NOT `ci-status-update.yml`** — that's where the
      branch→status mapping lives: the "Record CI status" step now reads `github.base_ref` and a green PR _into_ staging
      maps to `STAGING_GREEN` (the promote PR's v2 IS the staging gate). Additive — `push:[staging]` still also sets it
      until STEP 3, so no regression. Only `staging` is inherited (not `main`). **MUST stay ahead of STEP 3.** —
      unified-trading-pm@e9938a425
- [x] ✅ [CODE] P2. **Drop `push:[staging]` QG — STEP 2 of 3 (detector) — recorded as a forward constraint.** The @4950
      zero-check-run detector **does not exist yet** (it's an open "should" in `cicd_contract_hardening` @4950, future
      `monitoring_control_plane_master_2026_06_10.md` dashboard work) — so there is nothing to _adapt_ today, and A3 is
      NOT currently blocked by a false-positive. **Constraint recorded** (here + the codex LDR-trunk section): when
      @4950 is built, a staging head with no _push_ check must be treated as LEGITIMATE when its merged promote PR
      carried the v2 check (flag only no-check AND no-merged-PR-check), else it false-positives on every drain merge
      post-A3.
- [ ] [CI] P1. **Drop `push:[staging]` QG — STEP 3 of 3 (template + rollout).** Remove `staging` from the `push:`
      branches in `scripts/workflow-templates/quality-gates-v2.yml.tmpl` (keep `pull_request:[main,staging]` +
      `push:[main]`), then `rollout-workflow-templates.sh --template quality-gates-v2` to all 24 repos + commit each
      per-repo copy (rollout is not done until `detect_template_drift.py --workflows` is clean and no repo's
      `.github/workflows/` is dirty). **Gated on STEP 1 being live.** Verify v2-on-staging count drops to zero while
      `STAGING_GREEN` still populates + the drain keeps promoting.
- [ ] [TEST] P2. **First-use watch.** After PM ships: confirm (a) a normal `quickmerge --agent` lands on LDR with no
      staging PR + a clean message, (b) the 30min drain opens the LDR→staging PR and it auto-merges on v2-green, (c)
      `--hotfix` still hits the lock when staging is locked. Record evidence here.
- [x] ✅ [CI] P0. **Tier-C drain auto-merge was SILENTLY DEAD — `--auto --rebase` cannot ARM on a merge-laden LDR**
      (GraphQL `This branch can't be rebased`; LDR carries merge commits from the backmerge-bot + resolved backmerges) →
      every promote PR opens but never auto-merges → the LDR→staging pile-up (the "treadmill"). The arm failure was
      swallowed (`2>/dev/null` / `|| true`). **FIX (PM@84fe257ae):** `--auto --rebase || --auto --squash` fallback
      (squash always arms) at BOTH merge sites (line 166 primary + line 220 close-reopen), with an explicit **sanitized
      subject/body** so no inherited `[skip ci]` poisons the staging push — pre-emptively closing @4941 for the drain's
      NEW squash path (the separate `ldr-to-main`/`staging-to-main` squash paths still need @4941). Validated:
      `--auto --squash` arms + merges (execution-service #254 merged via the probe). **VERIFY end-to-end** once it
      reaches PM `main` (Option-B) + the next :13/:43 tick auto-merges a promote via the squash fallback. Finding + fix:
      harsh slot, 2026-06-10.

### Track D — LDR integrity (promote-PR provenance + push tripwire + PR hygiene)

- [x] ✅ [CI] P1. **Promote-PR provenance gate (the enforcement) — staging drain DONE.** **Implementation pivot:**
      `check_strict_quickmerge.py` is NOT present in target-repo checkouts (only in PM), so it can't run in the per-repo
      v2 aggregation job. Implemented instead **in the Tier-C drain itself** (`ldr-to-staging-promote.yml`, which checks
      out PM and HAS the script) — exactly the "promote _bot_ gates" framing: before arming auto-merge for a repo, the
      drain shallow-fetches that repo's `staging`+`live-defi-rollout` into a temp repo and runs the SSOT checker over
      `origin/staging..origin/live-defi-rollout --block`. A **clear** violation → auto-merge NOT armed, PR left open +
      commented, counted BLOCKED. **FAIL-OPEN** on fetch/checker error (distinguishes a real violation — output contains
      `bypassed quickmerge` — from an internal error, so a checker bug never jams promotion). Reuses the checker's
      carve-out classification (PB1). **Note vs original spec:** this is a "don't-arm-auto-merge" gate (PR sits open),
      NOT a v2-RED hard-block — bad content can't auto-promote, but isn't admin-unmergeable. —
      unified-trading-pm@e9938a425
  - [x] ✅ **Mirror DONE:** the gate is now in `ldr-to-main-promote.yml` (PM's LDR→main; range
        `origin/main..origin/live-defi-rollout`, checked directly since PM is the checkout; gates both arm sites).
        PM-only so mostly carve-outs. — unified-trading-pm@3cae03cf5. (Optional stronger variant: a true v2-RED
        hard-block would need the checker fetched into the per-repo v2 job — deferred; the drain gate is sufficient for
        "bot promotes only provenanced content".)
- [ ] [CI] P2. **Push tripwire (faster detection — optional, build after P1).** Non-blocking `push: live-defi-rollout`
      GHA running the SAME `check_strict_quickmerge.py`; a violation fires a `#ci-failures` alert (+ optional QG) so a
      bypass is caught at push, not ≤30 min later at the drain. Latency-reduction only — the promote-PR gate (above) is
      the actual safety. **LDR never runs QG on a clean (trailered) push.**
- [ ] [SCRIPT] P2. **Auto-close stale/superseded promote PRs (no manual cleanup).** Extend `ci_failure_watcher.py`:
      close any LDR→staging (or →main) PR whose commits are already in the base by **`git patch-id`/`git cherry` content
      equivalence — NOT SHA membership** (the drain rebases/squashes → staging SHAs differ; SHA checks never match → PRs
      never close → the pile-up). Composes with the now-fixed `--squash` auto-merge arming (line 143 todo).
- [ ] [SCRIPT] P2. **Parallelize the drain + SIT within a tier.** `ldr-to-staging-promote.yml` reads
      `topologicalOrder.levels[]` (correct order) but iterates **serially** in a bash for-loop — repos in the same tier
      with no inter-dep (e.g. instruments-service ∥ MTDS) run one-after-another. Fan them out (background jobs + a
      `wait` barrier between tiers) so promotion wall-clock = longest dependency chain, not the sum. Same for the
      `full-workspace-sit` assembly. Composes with @4933 (per-cone locks).
- [ ] [SCRIPT] P3. **Stale-checkout / stale-PR host monitoring.** Extend the slot Slack monitoring to flag stale promote
      PRs + stale branch checkouts on any host (laptops ikenna/harsh · vm-0/vm-planning · epic VMs when up). Composes
      with `verify-slot-host-symmetry.sh`.

## Success criteria

- `quickmerge --agent --files` on a service repo: commit on `origin/live-defi-rollout`, **no** staging PR opened,
  exit 0.
- Staging-locked → a normal `quickmerge` still succeeds (lands on LDR); a `--hotfix` is blocked by the lock.
- `ldr-to-staging-promote` runs at :13/:43, drains in tier order, LDR→staging PR `quality-gates-v2` green (deps resolved
  against staging-tier).
- BLR-class failure (`resolved < floor` on a `main` push) cannot recur for changes that flow through LDR.
- `detect_template_drift.py` clean; no per-repo `.github/workflows` dirty; codex + CLAUDE.md aligned.
