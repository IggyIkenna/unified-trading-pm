---
title: "Full CI/CD + SIT target state — close the gaps that let staging drift ~1 month undetected"
created: 2026-05-24
source:
  - "staging staleness audit + UAC pilot PR #48 (2026-05-24)"
  - "plans/active/issues/staging_resync_post_cutover_2026_05_24.md"
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found (the structural gap)

The 2026-05-24 staging audit exposed that our CI/CD + SIT is **not actually continuous**. Staging drifted ~1 month
behind LDR across all 8 active repos (~5000 commits) and **nobody's pipeline caught it**, because of four compounding
structural holes:

1. **`live-defi-rollout` CI runs but is RED + UN-GATED** (corrected 2026-05-24 after verifying actual runs — earlier
   claim "LDR has no CI" was wrong). `workspace-qg` _does_ trigger on every LDR push (the template trigger is
   `[main, staging, live-defi-rollout]`). But LDR has **no branch protection**, so a RED run does not block the push —
   so failures accumulate and nobody fixes them (the runs have been failing for the whole sprint). The accumulated-red
   is the same per-repo cross-repo-SIT-misfire (#4) + whatever else slots didn't catch locally. **Fix = make LDR CI
   green + treated as a real signal**, not "add CI" (it exists). Confirmed: UAC LDR runs were failing on the
   cross-repo-SIT misfires; fixed @f7627f8e + @5b0707f0.
2. **The only real CI gate is the `staging` PR.** `quality-gates` (the SIT) runs when `quickmerge` opens a `→ staging`
   PR. So the _first_ time a month of LDR state meets CI is the staging PR — which then surfaces a month of accumulated
   failures at once (the worst possible time to discover them).
3. **No automated LDR→staging promotion.** It's manual `quickmerge` per repo. During the cutover sprint everyone
   (correctly) pushed direct to LDR and deferred quickmerge → staging froze. There is no cron/bot that catches staging
   up when LDR moves; the operator's mental model ("staging auto-syncs on QG pass") does not match reality.
4. **Cross-repo SIT tests misfire in per-repo CI.** `workspace-qg` renders `dep_repos=""` for foundation repos, so
   per-repo CI checks out only that repo. Tests that validate _cross-repo_ invariants (sibling service dirs in
   `test_feature_dag_ssot`, production cassette consumers in `test_cassette_orphan_checker`, MTDS connector coexistence)
   then fail or false-positive because the siblings/consumers aren't present. We patched these to skip-when-no-siblings
   (UAC@f7627f8e) — but skipping is a workaround: **the cross-repo invariants now run nowhere in CI**, only in local
   full-workspace QG.

Net: we have _per-repo_ CI (good for repo-local lint/type/test) but **no continuous cross-repo SIT and no continuous
integration of the actual integration branch (LDR)**.

## Why it matters

- "Staging is current" is load-bearing for: the disaster-recovery game-day (needs current alerting-service + DART on
  staging), promote-to-paper/live (deploys from staging→main artifacts), and any "test it on staging" request. A
  month-stale staging silently breaks all of these.
- Accumulated-debt-at-promotion is the most expensive failure mode: instead of one bad commit failing one PR, a month of
  commits fail one giant PR with interleaved causes → hard to bisect, high-pressure to bypass.
- Cross-repo contracts (UAC↔consumers, feature-DAG SSOT, cassette↔consumer linkage) are exactly the things that break
  silently across repos — and they're the ones with no continuous gate.

## Target state — full CI/CD with real SIT

### Tier A — per-repo CI on LDR: make it GREEN + a real signal (the trigger already exists)

- `workspace-qg` already triggers on `live-defi-rollout` — the gap is it's been RED + ignored (no LDR branch
  protection). **Fix the accumulated-red so LDR CI is trustworthy** (started: the cross-repo-SIT-misfire fix @f7627f8e +
  @5b0707f0 greens UAC; replicate per repo). Then decide whether to add LDR branch protection (blocks the rapid
  direct-push flow — likely keep LDR un-gated but **monitored**: a dashboard / ping when LDR CI goes red, so it's fixed
  in hours not weeks).
- Keep `dep_repos` = upstream deps only (build/resolve correctness).

### Tier B — full-workspace SIT job (NEW — the missing layer)

- A scheduled + on-promotion GHA (or Cloud Build) job that **checks out ALL active repos** (topologicalOrder from
  `workspace-manifest.json`) into a workspace layout and runs the **cross-repo invariant suite**: feature-DAG SSOT,
  cassette↔consumer linkage, schema-provenance across repos, IS→MTDS URL contract, batch=live parity,
  incident-gateway↔UAC contract, etc.
- This is where the tests we just guarded (skip-in-per-repo-CI) actually execute. Cadence: nightly + on every staging
  promotion. Owner + verifier + last_executed per the runbook-governance rule.
- Gate: a repo cannot promote to staging if the full-workspace SIT is RED for its layer.

### Tier C — continuous LDR→staging promotion (NEW automation)

- A bot/workflow that, when LDR is green (Tier A) + the full-workspace SIT is green (Tier B), **opens/advances the
  `live-defi-rollout → staging` PR per repo in dependency order** and auto-merges on green. Cadence: e.g. every 4–6h or
  on green-LDR-push, so staging never drifts more than hours.
- Must handle the dep-order cascade (UAC→UTL→instruments→services→APIs→deployment→UI→e2e) + the version-bump cascade
  (semver-agent + `update-dependency-version.yml`).
- Conflict policy: LDR is source-of-truth (staging is downstream); preserve only staging-only semver version bumps.

### Tier D — staging→main + deploy (mostly exists; harden)

- semver-agent staging→main promotion: keep. Audit that non-major auto-promotion is healthy.
- **Service deploy configs**: services that must serve HTTP on staging/prod (e.g. alerting-service safety-ops gateway —
  currently a subscriber with NO Cloud Run service) need a `gcloud run deploy` step + service-account/env/ingress
  config. Today the cloudbuild builds+pushes an image but deploys nothing for some services. Audit every service:
  subscriber-only vs HTTP-served, and add Cloud Run deploy for the HTTP ones.

### Tier E — SIT scenarios as CI (close the loop with the DR work)

- The disaster-recovery game-day scenarios (`e2e-testing/scripts/defi/scenarios/`) + synthetic smokes should run against
  the staging stack on a schedule as part of SIT, with the 7 per-scenario asserts. This makes "21/21 game-day" a
  continuous gate, not a manual operator session.

## Phased plan to get there

1. **Unblock now (tracked in `staging_resync_post_cutover_2026_05_24.md`)**: repair the cross-repo SIT misfires (done
   for UAC; replicate the skip-guard pattern per repo), then cascade the dep-order LDR→staging resync to make staging
   current once.
2. **Tier A**: add `live-defi-rollout` to the `workspace-qg` push trigger (edit PM template `workspace-qg.yml.tmpl` +
   `rollout-workflow-templates.sh`). Cost: more Action minutes on LDR; mitigate with the existing concurrency-cancel.
3. **Tier B**: build the full-workspace SIT job (new reusable workflow in PM that checks out the topologicalOrder set +
   runs the cross-repo suite). Move the guarded tests to require this context.
4. **Tier C**: build the auto-promotion bot (dep-order LDR→staging PRs on green).
5. **Tier D**: per-service deploy-config audit + add Cloud Run deploy for HTTP-served services.
6. **Tier E**: wire game-day + synthetic smokes into the staging SIT schedule.

## Recommended decision

This is an epic-sized infrastructure workstream (belongs under `observability_master` or a new `cicd_master` epic). It
is the structural fix that prevents the next month-of-drift. Sequence it **after** the one-time staging resync (which
makes staging current), so Tier C automation starts from a current baseline.

## Status

- [x] Gap + target state documented (root-cause #1 CORRECTED: LDR has CI; it's red+ungated, not absent)
- [x] Cross-repo-SIT-misfire fixed for UAC — both code paths: pytest guards (UAC@f7627f8e) + STEP 5.86 shell checker
      (UAC@5b0707f0). Tests/type/codex/STEP-5.86 now green in per-repo CI; validation preserved in full workspace.
- [x] **Tier A — UAC fully green**: cleared the remaining accumulated codex-red beyond the SIT misfire (UAC@36f43a90):
      13 imports-inside-functions (stdlib hoisted in data_source_continuity + scenario_overlay; registry sibling
      lazy-imports normalized to `# noqa: imports-inside-functions`), `pd.Series[Any]` in internal/testing/
      seed_validator (Any check now excludes `**/testing/**` — PM@00b5d945a), malformed `# qg-empty-fallback` markers
      (team_mapping_data, protocol_pause_windows), hardcoded project-id in a \_cefi.py comment. Full UAC QG exit 0 for
      per-repo CI; UAC remote workspace-qg re-running to confirm green.
- [~] Tier A: replicate to other repos. **Fleet status 2026-05-25**: alerting-service GREEN; deployment-service GREEN;
  UTL fixes pushed (UTL@b92f8518 — local QG exit 0; CI verifying); UAC bouncing on parallel credential/ledger commits;
  instruments / execution / strategy / MTDS still RED with their own accumulated-red.
  - **UTL red was 4 classes (~45 tests), not just SIT-misfire**: (1) model_registry cross-repo SSOT → hermetic
    `tests/fixtures/cloud-providers.yaml`; (2) UAC `DataFreshnessContract` added required `asset_group` → test
    constructions updated; (3) reason-classifier precedence test re-scoped; (4) **broken deps**: `starlette>=1.0.1` was
    unsatisfiable with `fastapi<1.0.0` → reverted + PYSEC-2026-161 tracked. Pattern for downstream repos: expect
    UAC-contract-drift + cross-repo-SSOT + per-repo accumulated codex-red, not just the SIT skip-guard.
- [ ] [AGENT] P0. Tier A: LDR-CI-red monitoring/ping (so red is fixed in hours, not weeks)
- [~] Tier B: full-workspace SIT job **BUILT** (system-integration-tests@f881579):
  `scripts/run_cross_repo_invariants.sh` (asserts full workspace assembled; runs the guarded invariants for real; fails
  on any failure OR skip) + `.github/workflows/full-workspace-sit.yml` (clones all 31 active repos from manifest
  topologicalOrder, nightly 03:00 UTC + workflow_dispatch + repository_dispatch[full-workspace-sit] for the Tier C
  on-promotion hook). Runner **validated locally**: feature-DAG SSOT + cassette↔consumer (pytest + STEP 5.86) PASS with
  siblings present (proving they no longer skip); data_type canonicalization correctly RED on the MTDS drift. Remaining:
  confirm the workflow on a live trigger; wire the promotion-gate (Tier C) to read its result. **Validated the premise
  locally (2026-05-24)**: with the full workspace assembled, the guarded cross-repo invariants run for real and already
  caught live drift — `tests/test_data_type_canonicalization.py[market-tick-data-service]` FAILS: MTDS
  `configs/venue_data_types.yaml` still uses banned legacy DeFi data_type aliases (`swaps`→`dex_swaps`,
  `liquidity`→`dex_pools`, `rate_indices`→`lending_indices`) across UNISWAP_V2/V3/V4-ETHEREUM, CURVE-ETHEREUM,
  AAVE_V3_ETH, MORPHO-ETHEREUM, FLUID-ETHEREUM. This drift is invisible to per-repo CI (UAC's test returns `[]` when the
  MTDS sibling is absent). Tracked below + needs config-vs-data-migration diagnosis before fix.
- [ ] [AGENT] P1. Tier C: auto LDR→staging promotion bot (dep-order)
- [ ] [AGENT] P1. Tier D: per-service Cloud Run deploy-config audit
- [ ] [AGENT] P2. Tier E: game-day + synthetic smokes as staging SIT
