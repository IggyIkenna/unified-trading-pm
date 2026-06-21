---
title:
  staging→main promotion starves 20/23 repos — two upstream failure modes (manifest version-bump desync + Tier-C
  squash-fallback eating semver labels), not a missing promoter
created: 2026-06-19
source:
  - 2026-06-19 fleet audit (deployment-ui CI/CD Repos page; LDR→main delta column)
  - unified-trading-pm/.github/workflows/staging-to-main.yml (pending-set derivation)
  - unified-trading-pm/.github/workflows/ldr-to-staging-promote.yml (lines 306-315, rebase→squash fallback)
  - unified-trading-pm/scripts/workflow-templates/semver-agent.yml.tmpl (bump computation)
  - unified-trading-pm/workspace-manifest.json (staging_versions / staging_commits / versions)
  - gh api compare main...staging + per-repo pyproject versions across the fleet
  - unified-api-contracts PR #370 (stuck staging→main promote PR)
locked_by: live-defi-rollout
parent_epic: infrastructure_master
estimate_class: refactor
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 1.0
priority: P1
status: active
---

## What I found

The `LDR→main delta` column on the CI/CD Repos dashboard shows most repos days behind main (agent-orchestrator ~8d,
alerting ~4d, etc.). The dashboard "lag" = **age of the oldest un-promoted commit** in `git compare main...<branch>`
(per `scripts/cicd/promotion_lag_monitor.py` `_lag()`), NOT "how long main has been broken". Investigating why so much
content sits on `staging` without reaching `main` surfaced **two distinct upstream failures**. The staging→main promoter
itself (`staging-to-main.yml`, `*/15`) is working — it is just blind to these repos.

### Fleet audit (2026-06-19) — staging→main content divergence vs manifest membership

23 service repos (PM excluded — Option-B main-direct). **20 are starving** (real content on `staging`, never reaching
`main`):

| Bucket                                             | Repos                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Promoting normally (in `manifest.staging_commits`) | deployment-api, unified-trading-library, system-integration-tests                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| In sync (nothing pending)                          | ibkr-gateway-infra                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **STARVING** (content on staging, not promoting)   | agent-orchestrator (145 files/327 commits), instruments-service (89), execution-service (58), strategy-service (39), unified-trading-system-ui (39), unified-api-contracts (36), deployment-service (33), e2e-testing (32), features-service (25), market-tick-data-service (25), client-reporting-api (19), ml-service (18), trading-agent-service (11), alerting-service (10), deployment-ui (10), fund-administration-service (9), greeks-service (9), market-data-processing-service (8), unified-trading-api (7), batch-live-reconciliation-service (7) |

### How the promoter selects work (so we know why it skips these)

`staging-to-main.yml` derives its pending set from the **PM manifest**, not from git divergence:

- idempotency gate: `if not manifest.staging_commits: skip`.
- readiness / dep-order / merge gates: `promoting = [r for r,sv in staging_versions.items() if sv != versions[r]]`.

So a repo is promoted **only if `manifest.staging_versions[r] != manifest.versions[r]`** — i.e. only if the manifest
records a version delta. That makes the manifest's version maps the single source of truth for "what to promote". Both
failure modes below break that input.

### Mode A — repo bumped, but the manifest never recorded it (5 repos)

These repos' `pyproject.toml` version on `staging` is genuinely ahead of `main`, but `manifest.staging_versions` is
missing/stale, so the promoter cannot see the delta:

| repo                    | staging pyproject | main pyproject | manifest.staging_versions | manifest.versions |
| ----------------------- | ----------------- | -------------- | ------------------------- | ----------------- |
| unified-api-contracts   | 0.23.0            | 0.21.0         | (absent)                  | 0.22.0            |
| unified-trading-library | 0.16.0            | 0.15.0         | 0.15.0 (stale)            | 0.14.0            |
| instruments-service     | 0.11.0            | 0.10.0         | (absent)                  | 0.10.0            |
| execution-service       | 0.15.0            | 0.14.0         | (absent)                  | 0.14.0            |
| client-reporting-api    | 0.9.0             | 0.8.0          | (absent)                  | (absent)          |

The semver-agent bumped the repo's `pyproject.toml` but the bump never propagated to the manifest. The propagation path
is: repo `semver-agent` → `repository_dispatch: version-bump` → PM `update-repo-version.yml` → writes `staging_versions`
(branch=staging) / `versions` (branch=main). CLAUDE.md already documents this dispatch as a historical SPOF
(semver-agent carries a CRITICAL "version-bump dispatch FAILED … staging_versions baseline will NOT record" alert). The
symptom here is exactly that: bumps landed in repos, the manifest baseline did not record them.

### Mode B — version never moved (≈15 repos)

These repos have `staging` pyproject `==` `main` pyproject despite content divergence — semver-agent never bumped them.
Confirmed mechanism on strategy-service (frozen at 0.16.0):

- Its `live-defi-rollout` carries real `feat:` commits (e.g. `feat: CarryFundingDispersionEngine`,
  `feat(config): funding/basis ensemble config`) that should bump it.
- Its `staging` history is **only** squashed `chore(promote): LDR → staging (Tier C auto-drain)` commits, bodied
  `Tier C automated drain — squash fallback (LDR not rebaseable)`.

Root cause is `ldr-to-staging-promote.yml` lines 306-315:

```bash
# --rebase fails to ARM when LDR is merge-laden (backmerge bot) → fall back to --squash
gh pr merge "$PR_URL" --auto --rebase ... \
  || gh pr merge "$PR_URL" --auto --squash \
       --subject "chore(promote): LDR → staging (Tier C auto-drain)" ...
```

When `live-defi-rollout` contains merge commits (the `main-backmerge-to-ldr` bot creates them continuously), GitHub
refuses `--rebase` ("This branch can't be rebased") and the drain falls back to **squash**. The squash collapses every
underlying `feat:/fix:/feat!:` commit into one `chore(promote)` commit → semver-agent (reading the staging commit label)
sees `chore` → **no bump** → version frozen → version-driven promoter can never carry it. Mode-A repos only escaped this
because their public-surface differ caught the change independently of the (lost) commit label.

### Acute incident riding on top — UAC PR #370 (still OPEN as of 2026-06-19 ~15:00 UTC)

UAC additionally had a stuck `staging→main` promote PR #370. Timeline:

1. A wrong `DATASET_CBOE_CFE = "CFE"` value was direct-pushed to UAC `main` (`9fb2c338`, laptop, out of the carve-out
   set); the correct value is `"XCBF.PITCH"` (verified against Databento's catalog: `databento.com/datasets/XCBF.PITCH`;
   a bare `CFE` 400s). #370 (staging→main) went `CONFLICTING`.
2. Fixed via PR #371 (`main` ← `XCBF.PITCH`), merged green. #370 became `MERGEABLE` but `BLOCKED`.
3. #370's head (the 0.22.0 bump commit, pushed by Semver Agent) has no `pull_request`-context `quality-gates-v2` check →
   the required check is **missing** → permanently `BLOCKED` (the documented "v2-never-reported deadlock"). A
   `workflow_dispatch` v2 run went green but did **not** satisfy the PR (dispatch-event checks don't count for a PR's
   required context). The fix is close+reopen (what `ci-failure-watcher --auto-recover` does), which was permission-
   blocked for the investigating agent. Once Mode-A is fixed, the auto-drain would promote UAC and make #370 moot.

## Why it matters

- Fleet-wide: `main` (the release/projection branch + image source) is days-to-weeks stale for 20/23 repos. Anything
  keying off `main` (image builds, `versions` map, deploy provenance) is stale.
- Silent: each individual workflow reports green (`semver-agent` "success" = "no bump needed"; the drain "success" =
  squashed). Nothing fails, so the starvation only shows on the lag dashboard.
- Self-reinforcing: the more `main-backmerge` merge commits accrete on LDR, the more often the drain squash-fallback
  fires, so Mode B worsens over time.
- This is a workspace-SSOT-level CI/CD correctness gap (cross-repo, affects the promotion pipeline) → "big finding" per
  Findings-Triage.

## Recommended decision

Two upstream fixes (NOT a new/per-repo promoter — the promoter is central and fine):

1. **Mode B (systemic, the real freeze): preserve the semver signal through the squash fallback. ✅ FIXED 2026-06-21
   (PM@6acde3fe7).** Implemented the preferred option: `ldr-to-staging-promote.yml` now has `_squash_subject()` which
   derives the aggregate conventional type (`feat!` if any `!:`/`BREAKING CHANGE`, else `feat`, else `fix`, else
   `chore`) from the commits the squash collapses, and titles the squash subject `<type>: LDR → staging (Tier C
   auto-drain)` at ALL 3 squash sites (initial fallback + close-reopen recovery + idempotent re-arm). Fail-safe: `chore`
   only when no feat/fix/breaking is found; over-detection → a harmless monotonic bump, never a starve. **Effect:**
   future Tier-C squash drains carry the real type → semver-agent bumps → version delta → the version-driven promoter
   carries the repo. **Verify (not yet confirmed):** watch the next drains on a Mode-B repo (e.g. strategy-service) —
   squash subject now `feat:`/`fix:` + semver bumps + it promotes. **Caveat — does NOT retro-drain the ALREADY-frozen
   backlog:** repos already squash-drained to staging (content==staging, version frozen) have no new LDR-ahead content →
   no new drain → stay frozen until new content arrives OR a one-shot (Mode A); active repos self-heal on next drain.
   Alternatives kept as hardening if insufficient: (a) keep LDR rebaseable so `--rebase` arms; (b) semver-agent resolves
   the bump from the LDR commit _range_.

2. **Mode A (quick unblock for the 5 already-bumped repos): re-sync + harden the manifest dispatch.** Reconcile
   `manifest.staging_versions`/`staging_commits` to the repos' actual `pyproject` versions (one-shot reconcile), and
   harden/repair the `semver-agent → update-repo-version` dispatch so future bumps always record. This alone makes
   UAC/instruments/execution/client-reporting-api/UTL promote on the next `*/15` tick (and resolves UAC #370
   implicitly).

3. **UAC #370 now:** close+reopen to re-fire `pull_request` v2 (or let `ci-failure-watcher --auto-recover` do it).
   Tracked by the acute incident above; will be moot after Mode A.

## ⚠️ Paths to explore more (NOT yet verified — do not treat as settled)

- **WHY the Mode-A dispatch failed.** I confirmed the _symptom_ (repo bumped, manifest blind) but not the _cause_. Could
  be (a) the `version-bump` `repository_dispatch` genuinely failing/HTTP-erroring (check semver-agent run logs for the
  CRITICAL dispatch-failed alert), or (b) a manifest reconcile (`reconcile_manifest_backmerge.py` / a force-sync) having
  reset `staging_versions` to only the current 5 keys. Read the dispatch logs + manifest `lastUpdated`/history before
  patching the symptom.
- **Whether ALL ~15 Mode-B repos are squash-label-loss vs genuinely chore-only.** Confirmed for strategy-service. The
  others are inferred from "staging pyproject == main pyproject + content divergence". A repo whose staging delta is
  _genuinely_ only docs/chore SHOULD legitimately not bump — and then there is a SEPARATE open question (below).
  Per-repo: scan each LDR delta for real feat/fix.
- **Does content that legitimately never bumps (pure docs/chore PRs) ever reach `main`?** If the model is strictly
  version-driven, a repo receiving only non-bumping commits would never promote. Need an operator decision on whether
  that is acceptable (chore/docs stranded on staging) or whether the promoter should also carry
  content-divergent-but-non-bumping repos. (My initial hypothesis that this was THE bug was wrong — the dominant cause
  is squash-label-loss — but the edge case remains open.)
- **semver-agent behaviour on a `chore`-labelled squash that DOES change public surface.** The template says
  label-vs-API-diff MISMATCH posts a FAILING status (block), yet Mode-B runs report "success". Either the API diff also
  resolved no-bump, or the mismatch path isn't triggering. I could not capture the compute-step log (`gh run view --log`
  returned empty for the runs I tried) — re-pull a fresh semver-agent run log on a Mode-B repo and read the
  `Resolved from API diff` / `MISMATCH` lines.
- **agent-orchestrator specifics.** AO's branch-model migration completed 2026-06-19; its 327-commit / 8-day backlog is
  the worst case. Confirm the migration didn't independently break its dispatch/promotion before assuming Mode A/B fully
  explain it.
- **The other multi-day-lag repos on the dashboard** (alerting 4d, deployment-service 4d6h, etc.) are assumed to be the
  same two modes; spot-check 2-3 to confirm before a blanket fix.

## Related

- `plans/active/cicd_promotion_pipeline_2026_06_18.md` (LDR-trunk decoupling, Tier-C drain)
- `plans/active/cicd_quality_gates_2026_06_18.md`
- `codex/08-workflows/ci-cd-flow.md` (§ "LDR-trunk decoupling", § "[skip ci] and required checks")
- CLAUDE.md § "v2-never-reported deadlock", § semver-agent dispatch SPOF

## Progress Log

### 2026-06-21 — autonomous completion (operator `/autonomous`: finish, don't prompt, verified done-state)

**Decision (content-vs-version promoter question, made under autonomous authority + documented intent):** do NOT
rewrite the central 1449-line `staging-to-main.yml` to be content-delta-aware (high blast radius; the issue doc's own
stance is "the promoter is central and fine"). Instead: (1) keep the version-driven promoter as primary; (2) **Mode B
fix (PM@6acde3fe7) makes future bumping content flow normally**; (3) **drain the CURRENT frozen backlog via per-repo
LDR→main PRs + v2-gated auto-merge** (the proven 2026-06-17 reconcile mechanism — promotes content to main regardless of
version-delta, covers Mode A + Mode B uniformly, "LDR is the SSOT / main is a projection"); (4) residual pure-non-bumping
content (docs/chore that legitimately never bumps) staying on staging is LOW-HARM (main = deploy/image source; docs
don't affect deploys) and acceptable — not worth the promoter rewrite. This closes the doc's open design question.

- [x] **Backlog drain ARMED 2026-06-21** — 20 starving repos (real content off main) each got an `LDR→main` PR with
      v2-gated auto-merge: agent-orchestrator#350 (78f), e2e-testing#348 (50f), instruments-service#491 (44f),
      deployment-service#119 (41f), unified-trading-system-ui#285 (29f), deployment-api#146 (18f), deployment-ui#277
      (17f), execution-service#327 (16f), features-service#581 (12f), market-tick-data-service#265 (12f),
      batch-live-reconciliation-service#110 (10f), fund-administration-service#206/ml-service#132/trading-agent#225
      (8f), system-integration-tests#250/unified-trading-api#419 (4f), market-data-processing-service#319 (3f),
      alerting#110/greeks#225/ibkr-gateway-infra#235 (1f). Skipped 3 already-content-identical (strategy-service /
      unified-api-contracts / unified-trading-library / client-reporting-api — drained earlier). v2 gates each; reds
      stay open for the per-repo fix (none expected — all staging-green).
- [ ] **VERIFY (in progress):** watch main catch up to LDR per repo (content-delta → 0); diagnose any v2-red straggler.
- [ ] **Manifest hygiene (post-drain):** after main catches up, reconcile manifest `versions`/`staging_versions` to the
      drained pyproject versions if `assert_version_coherence.py` (warn-only) shows a split; the next semver/promote
      cycle also realigns it.
