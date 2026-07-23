---
doc_type: issue
title:
  workspace-manifest `staging_versions` is frozen at 2026-06-27 and disagrees with `versions` for 12 repos — spurious
  quickmerge STAGE 1.6 warnings, and a real BLOCK under --hotfix
summary: >-
  `staging_versions` in workspace-manifest.json has not been updated since 2026-06-27 (staging went dormant), but
  quickmerge's STAGE 1.6 dependency gate PREFERS it over `versions` (`r = rstag.get(dep,'') or rmain.get(dep,'')`,
  scripts/quickmerge.sh:998). 12 repos now disagree between the two keys; for 4 of them `staging_versions` is AHEAD of
  the real version (unified-api-contracts 0.71.0 vs 0.72.0, instruments-service 0.88.0 vs 0.90.0,
  market-tick-data-service 0.91.0 vs 0.92.0, ibkr-gateway-infra 0.0.74 vs 0.0.75), so any repo depending on those four
  gets a permanent "dependency BEHIND staging/main" report that no amount of pulling can clear — the auto-heal fires a
  main-backmerge that cannot possibly fix it, because the staleness lives in `staging_versions`, whose only writer
  (reconcile-staging-versions.yml) reads frozen staging pyprojects. For a NORMAL landing this is a WARN (noise + a
  wasted workflow dispatch per occurrence); under `--hotfix` it is a hard BLOCK. Found while auditing what still runs
  against the retired staging branch.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, quickmerge, workspace-manifest, staging, versions, dependency-gate]
related:
  - github_actions_ci_cost_reduction_2026_07_15.md
  - ../cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
created: 2026-07-23
priority: P2
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
assigned_role: infra
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
locked_by:
resolved_by:
depends_on: []
source:
  - "fleet staging-machinery audit 2026-07-23 (operator ask: what still runs for staging, can we stop it)"
  - "verified live: workspace-manifest.json staging_versions vs versions; scripts/quickmerge.sh:985-1060"
---

# `staging_versions` is a frozen mirror that still outranks `versions` in the quickmerge dep gate

> ## ⚠️ PREMISE CORRECTED 2026-07-23 — DO NOT IMPLEMENT THE FIX BELOW YET
>
> The post-cutover sweep (`post_cutover_silent_assumption_sweep_2026_07_23.md`, finding **F2**) found that this issue's
> framing is **inverted**. Every repo uses `dynamic = ["version"]` + `[tool.hatch.version] source = "vcs"`, so **the git
> tag IS the package version** — and in all four "stale-AHEAD" repos, `staging_versions` **equals the last real tag**
> while `versions` does not:
>
> | repo                     | last git tag    | `versions` | `staging_versions` |
> | ------------------------ | --------------- | ---------- | ------------------ |
> | unified-api-contracts    | v0.72.0 (06-27) | 0.71.0     | **0.72.0** ✔       |
> | instruments-service      | v0.90.0 (06-27) | 0.88.0     | **0.90.0** ✔       |
> | market-tick-data-service | v0.92.0 (06-27) | 0.91.0     | **0.92.0** ✔       |
> | unified-trading-library  | v0.43.0 (06-28) | 0.55.0     | **0.43.0** ✔       |
>
> The two keys did **not** drift "because staging froze". They diverged because **release tagging broke fleet-wide on
> 2026-06-27** (`reconcile_release_tags.py:51`'s regex cannot match a `dynamic` version), so each key now tracks a
> different thing — and `staging_versions` is the one still tracking reality.
>
> **Consequence for the recommendation below:** option 1 ("make the gate ignore `staging_versions` under dormancy")
> would make the dep gate trust the key that matches the real installed version **less**. Resolve F2 first, then
> re-derive the right fix. The measured drift and the WARN-vs-`--hotfix`-BLOCK impact analysis below remain accurate —
> only the causal story and the recommended fix are superseded.

> ## ⏸️ STILL BLOCKED 2026-07-23 (later the same day) — root cause found, fix deferred to Option B
>
> F2's real root cause is now known and is **not** the regex: `semver-agent` (the only tag minter) was orphaned on the
> dormant `staging` branch. A retarget was built and **proven working**, then **REVERTED on operator decision** for cost
> (~$32/mo of `ubuntu-latest`) and commit noise (~24 PM manifest commits/day, peak 84). Minting will instead move into
> the PM reconciler — **Option B**, see `post_cutover_silent_assumption_sweep_2026_07_23.md` § "Option B".
>
> **What that means for THIS issue: nothing has changed yet, so do NOT implement option 1.** Until Option B ships, no
> tags are minted and `versions` is NOT advancing — so `staging_versions` still happens to be the key that matches the
> last real tag, exactly as the ⚠️ box above describes. The inversion is not resolved; it is deferred.
>
> **What Option B will change, and the precondition to re-check:** minting will record into **`versions`** (the stable
> key), making it live again and demoting `staging_versions` to a frozen historical record. At that point — and only
> then — option 1 (dormancy-aware gate) becomes correct.
>
> **Gate before implementing option 1:** confirm `versions` is demonstrably advancing —
> `git log --grep='chore(manifest): update' -- workspace-manifest.json` must show entries newer than 2026-07-23. As of
> this writing the newest such entry is **2026-06-30**.

## What's wrong

`scripts/quickmerge.sh:998` (STAGE 1.6 dependency version gate):

```python
lv = lm.get('versions', {}); rstag = rm.get('staging_versions', {}); rmain = rm.get('versions', {})
for dep in deps:
    l = lv.get(dep, ''); r = rstag.get(dep, '') or rmain.get(dep, '')
    ...
    if pl < pr:
        print(f'  {dep}: local={l} < staging/main={r}')
```

`staging_versions` is consulted **first** and only falls back to `versions` when the key is absent. That was correct
when staging was the promotion path — `staging_versions` meant "the SIT-tested version that already landed on staging",
which is legitimately ahead of `versions`.

Since **2026-06-27** staging is dormant fleet-wide (`staging_dormant_mode: true`, 24/25 repos
`promotion_model: ldr_main`). Its only writer, `reconcile-staging-versions.yml`, derives values from the **frozen**
staging-branch pyprojects, so it has produced no change since commit `c2d6b1e7b` (2026-06-27) — it runs hourly and
rewrites the same values forever. Meanwhile `versions` keeps advancing on the live LDR→main path. The two keys have
drifted apart.

## Measured drift (2026-07-23)

12 of the repos in `versions` disagree with `staging_versions`. Four are **staging-AHEAD**, which is the harmful
direction (the gate compares `local < staging`):

| repo                       | `versions` (real) | `staging_versions` (stale) |
| -------------------------- | ----------------- | -------------------------- |
| `unified-api-contracts`    | 0.71.0            | **0.72.0**                 |
| `instruments-service`      | 0.88.0            | **0.90.0**                 |
| `market-tick-data-service` | 0.91.0            | **0.92.0**                 |
| `ibkr-gateway-infra`       | 0.0.74            | **0.0.75**                 |

The other eight (`agent-orchestrator` 0.97.0 vs 0.20.0, `unified-trading-library` 0.55.0 vs 0.43.0, `deployment-service`
0.105.0 vs 0.83.0, `deployment-api` 0.51.0 vs 0.8.0, `greeks-service` 0.18.13 vs 0.17.2, `execution-service` 0.38.1 vs
0.38.0, `unified-trading-pm` 1.2.596 vs 1.2.509) are stale in the BEHIND direction and are harmless to the gate (it only
fires on `local < remote`), but they make the key actively misleading to read.

`unified-api-contracts` and `unified-trading-library` are dependencies of nearly every service, so the UAC entry alone
puts a spurious warning in front of most of the fleet's ships.

## Impact — and the correction to the initial report

An earlier pass on this described it as a false **BLOCK**. Reading `scripts/quickmerge.sh:1052-1060` shows that is only
true in one mode:

- **Normal landing** (the 99% case, incl. every `--agent` ship): **WARN, not a block** — "LDR-trunk landing allowed".
  Cost is noise in every affected ship's output, plus a **wasted `gh workflow run main-backmerge-to-ldr.yml` dispatch
  each time** (the auto-heal at `:1046` fires a backmerge that structurally cannot resolve a `staging_versions`
  staleness) — a small self-inflicted addition to the CI bill.
- **`--hotfix` landing**: **hard BLOCK** — "❌ BLOCKED (--hotfix): dependency version(s) still behind staging/main after
  PM pull". A hotfix touching anything that depends on UAC / instruments-service / MTDS / ibkr-gateway-infra would be
  blocked today by a version that does not exist anywhere, with a remedy message that cannot work. This is the real
  risk: it bites exactly when someone is in a hurry.

## Options (operator call)

1. **Make the gate dormancy-aware (recommended, smallest).** In `_dep_versions_behind`, ignore `staging_versions` when
   the manifest says `staging_dormant_mode: true` — i.e.
   `r = ('' if dormant else rstag.get(dep,'')) or rmain.get(dep,'')`. Self-correcting: the moment staging is re-entered
   the old precedence returns. One-line change, no data migration.
2. **Re-sync the key once** (`staging_versions := versions`) and let it re-freeze. Clears today's drift but the two keys
   will silently diverge again the moment `versions` advances, so it is a patch, not a fix.
3. **Retire `staging_versions` as a gate input** and keep it as a pure historical record. Cleanest long-term, but it
   also feeds `semver-agent.yml:262` and `assert_version_coherence.py:193` (warn-only), so it needs those checked first.

Option 1 pairs naturally with the staging-machinery shutdown in `github_actions_ci_cost_reduction_2026_07_15.md` §
"Phase 6" — if `reconcile-staging-versions.yml`'s hourly cron is stopped, this key is provably frozen and the gate
should stop trusting it.

## Resolution checklist

- [ ] [OPERATOR] P2. Pick option 1 / 2 / 3 above (recommendation: **1**, dormancy-aware gate).
- [ ] [INFRA] P2. Implement the chosen option in `scripts/quickmerge.sh` STAGE 1.6; verify by running a quickmerge in a
      repo that depends on `unified-api-contracts` and confirming the spurious "local=0.71.0 < staging/main=0.72.0" line
      is gone.
- [ ] [INFRA] P3. Confirm the wasted auto-heal dispatch (`gh workflow run main-backmerge-to-ldr.yml` at
      `scripts/quickmerge.sh:1046`) no longer fires for this cause — it is a real, if small, CI cost line.
