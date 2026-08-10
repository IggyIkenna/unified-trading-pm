---
doc_type: issue
title:
  Post-cutover silent-assumption sweep — 5-surface audit finds a dead trading kill-switch, fleet-wide release tagging
  broken since 2026-06-27, and 4 more silently-vacuous mechanisms
summary: >-
  Deliberate audit of the hypothesis "what else assumed staging was live?", run across five surfaces after five bugs of
  that shape surfaced in two days. The hypothesis is CONFIRMED and the class is broader than staging: it is **mechanisms
  whose input set silently became empty/unmatchable, which then report success**. Two findings are operationally serious
  and were verified first-hand, not taken from agent reports. (1) **The trading kill-switch is a no-op** —
  `trading-kill-switch.sh` dispatches `halt-order-flow` to execution-service, which has exactly one repository_dispatch
  listener (`dependency-update`) and none for halt/resume; GitHub returns 204 for an unsubscribed dispatch and the
  script treats 204 as success, so order flow is never halted or drained before a trading-critical deploy. (2)
  **Fleet-wide release tagging has been dead since 2026-06-27** — `reconcile_release_tags.py:51`'s `_VERSION_RE`
  requires a literal `version = "X.Y.Z"`, but every repo moved to `dynamic = ["version"]` + `[tool.hatch.version] source
  = "vcs"`, so it matches nothing, creates 0 tags, and logs "24 repo(s) had no main version" as a successful run.
  Because versions now DERIVE from tags, the fleet's real package versions are frozen at 2026-06-27 while the manifest's
  `versions` key advances independently. Good news, verified with run logs: the cross-repo BREAKING-CHANGE gate is
  genuinely LIVE and fail-closed — the empty `breaking_pending` is only its redundant first layer.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    execution-service,
    unified-trading-library,
    unified-api-contracts,
    instruments-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: [ci-cd, audit, silent-failure, kill-switch, release-tags, repository-dispatch, post-cutover, safety]
related:
  - /plans/archive/issues/staging_workflow_shutdown_2026_07_23.md
  - /plans/archive/issues/stale_staging_versions_manifest_2026_07_23.md
  - /plans/active/issues/qg_sentinel_environment_blind_2026_07_23.md
  - /plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md
created: 2026-07-23
author: unknown
priority: P1
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
assigned_role: infra
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/issues/stale_staging_versions_manifest_2026_07_23.md,
    /plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    scripts/deploy/trading-kill-switch.sh,
    scripts/cicd/reconcile_release_tags.py,
  ]
resolved_by:
depends_on: []
source:
  - "operator ask 2026-07-23: audit the 'what else assumed staging was live' hypothesis; file an issue only if the gap
    is genuine"
  - "5 parallel read-only audits covering the dispatch graph, manifest readers, the breaking-change gate, cron premises,
    and rulesets plus docs"
  - "the two headline findings independently re-verified by the author before filing"
---

# Post-cutover silent-assumption sweep

## Why this was run

Five defects in two days shared a shape: machinery that was correct before the 2026-06-27 LDR→main cutover, quietly
stopped matching reality, and **never failed loudly** — two mis-targeted escalation dispatches (204 = "success"), a
frozen `staging_versions` still outranking live versions, an environment-blind QG sentinel, and ~6,900 runs/week of
no-op crons reporting `success`. Rather than keep finding these one incident at a time, five read-only audits were run
in parallel over: the repository_dispatch event graph · manifest staging-key readers · the SIT/breaking-change gate ·
scheduled-workflow premises · rulesets and codex drift.

**Verdict: hypothesis confirmed, and the real class is wider than staging.** The common failure mode is _an input set
that silently became empty or unmatchable, feeding a step that reports success on empty_. Staging dormancy caused
several instances; it is not the only cause (see F1/F2).

---

## F1 — The trading kill-switch never halts anything (SAFETY, P0-adjacent)

**Verified first-hand.** `scripts/deploy/trading-kill-switch.sh` dispatches `halt-order-flow` / `resume-order-flow` to a
hardcoded `IggyIkenna/execution-service` (invoked from `cloud-build-router.yml:430` before trading-critical deploys).

Measured: execution-service's workflows contain **exactly one** `repository_dispatch` listener —
`update-dependency-version.yml` → `types: [dependency-update]`. Fleet-wide grep for `halt-order-flow` /
`resume-order-flow` returns **one hit, and it is a comment**, not a listener.

The failure is masked twice over:

- The repo _exists_, so an unsubscribed dispatch returns **204**, not 404. `trading-kill-switch.sh:54` does
  `if [ "$HTTP_CODE" = "204" ]` → prints `Event 'halt-order-flow' dispatched successfully`.
- `cloud-build-router.yml:410`'s own comment predicts a **404** ("the cross-repo dispatch 404s; that soft-gates"). That
  prediction is wrong, so the intended soft-gate warning never fires and `kill_switch_halted=true` is set.

**Consequence:** order flow is never rejected and in-flight orders are never drained before a trading-critical deploy,
and the deploy pipeline records that it was. Whether this ever mattered depends on how often that path ran with live
order flow — that is exactly what nobody can currently tell, because the mechanism is indistinguishable from working.

**This one is not staging-related at all** — it was found only because the sweep looked at the whole dispatch graph.

## F2 — Fleet-wide release tagging dead since 2026-06-27 (P1)

> ### ⚠️ ROOT CAUSE CORRECTED 2026-07-23 — it is NOT the regex
>
> The regex below is real, but it is the **backstop**, not the cause. Tracing the tag minter found **two independent
> failures on the same date, each masking the other**:
>
> 1. **PRIMARY — `semver-agent.yml` was orphaned.** It is the only thing that mints `v*` tags, and it triggers on
>    `push: branches: [staging]`. The 2026-06-27 cutover made `staging` dormant fleet-wide, so it simply **stopped
>    firing**. Measured: its last runs were `unified-trading-library` 2026-06-28 and `unified-api-contracts` 2026-06-27
>    — exactly matching each repo's newest tag. Nothing broke; the trigger just pointed at a branch nobody pushes to any
>    more. This was the shelved **D13 "semver-retarget"** work item (`cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` —
>    _"Shelved (reversible; revisit if/when wanted)"_); the shelving was deliberate, its side effect on tagging was not
>    noticed.
> 2. **BACKSTOP — `reconcile_release_tags.py` could not catch it.** Its `_VERSION_RE` broke in the _same_ pyproject
>    migration, so the one mechanism that would have reported the outage reported `created 0 tag(s)` as success, 246
>    times.
>
> A third instance of the identical regex lived in `semver-agent`'s own `always_patch` policy branch (dormant — all 24
> repos are `agent`), and a fourth in `publish-package.yml`'s version check, which is what let a `0.0.0.dev0` wheel be
> published rather than rejected.
>
> **Status 2026-07-23: root cause CONFIRMED, retarget BUILT and PROVEN, then REVERTED by operator decision.** Reviving
> the per-repo agent costs ~$32/mo of `ubuntu-latest` time (the runner is unmovable) and restores ~24 PM manifest
> commits/day (peak 84). Minting moves to the PM reconciler instead — **see § "Option B" below**, which carries the
> measurements, the proof the bump logic is correct, and the implementation steps. Reverted at
> `unified-api-contracts@d9ff488b` · `unified-trading-library@df89ac54` · `unified-trading-api@6987074`.

**Verified first-hand.** `scripts/cicd/reconcile_release_tags.py:51`:

```python
_VERSION_RE = re.compile(r'^\s*version\s*=\s*["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', re.MULTILINE)
```

Every repo now declares `dynamic = ["version"]` with `[tool.hatch.version] source = "vcs"` — there is no static
`version = "X.Y.Z"` line to match. The reconciler therefore finds nothing, creates 0 tags, and exits `success`, logging
`created 0 tag(s); 24 repo(s) had no main version` (246 scheduled runs in 7 days; on 2026-06-20..25 the same line read
`2 repo(s)`, so the regression is dateable to the pyproject migration).

Measured tag state — the fleet's newest tags:

| repo                     | latest tag | date           | manifest `versions` | manifest `staging_versions` |
| ------------------------ | ---------- | -------------- | ------------------- | --------------------------- |
| unified-api-contracts    | v0.72.0    | **2026-06-27** | 0.71.0              | 0.72.0                      |
| instruments-service      | v0.90.0    | **2026-06-27** | 0.88.0              | 0.90.0                      |
| market-tick-data-service | v0.92.0    | **2026-06-27** | 0.91.0              | 0.92.0                      |
| unified-trading-library  | v0.43.0    | **2026-06-28** | 0.55.0              | 0.43.0                      |

**Because `source = "vcs"`, the tag IS the package version.** So the fleet's real, installable versions have been frozen
for ~4 weeks while `versions` in the manifest advances independently. `publish-package` has run 0 times in 7 days, which
is consistent.

### Measured blast radius (2026-07-23, corrects the "4-week-old code is deployed" reading)

Probed the actual artifact estate rather than inferring from the tag state. **Deploys are NOT running stale code — the
loss is IDENTITY, not freshness.** Both halves matter:

**a) Artifact Registry `unified-libraries` (PYTHON) — the two shared libraries are frozen at the break date:**

| package                   | newest version in AR | published  |
| ------------------------- | -------------------- | ---------- |
| `unified-api-contracts`   | 0.72.0               | 2026-06-27 |
| `unified-trading-library` | 0.55.0               | 2026-06-27 |

**b) But the Docker base image everyone builds FROM is rebuilt daily and re-tagged with the SAME frozen number.**
`asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-library/unified-trading-library` has builds from
`2026-07-23T14:42`, `14:27`, `14:05`, `12:55`… and today's carries tags **`0.55.0, latest`**. The service Dockerfile
(`market-data-processing-service/Dockerfile:26,64`) does `FROM …unified-trading-library@${BASE_IMAGE_DIGEST}` then
`uv pip install --system -e . --no-sources` — `--no-sources` disables the `[tool.uv.sources]` path overrides, so the
container takes UTL/UAC from the base image (fresh) or AR (frozen), never from the sibling checkout.

**Therefore: the tag `0.55.0` is MUTABLE and means a different tree every day.** "Roll back to 0.55.0" is undefined;
"which UAC is in prod" is unanswerable from the version string.

**c) Six services HAVE kept publishing — with hatch-vcs distance-from-tag versions**, which is the tagging gap made
literal (the `devN` is the commit count since the last tag):

| package                             | newest in AR (2026-07-23)  | commits past last tag |
| ----------------------------------- | -------------------------- | --------------------- |
| `features-service`                  | `0.66.1.dev191+g190a1c957` | **191**               |
| `market-data-processing-service`    | `0.22.1.dev163+g5692f742e` | **163**               |
| `ml-service`                        | `0.50.1.dev44+g055625238`  | 44                    |
| `greeks-service`                    | `0.18.18.dev34+ga980f5000` | 34                    |
| `batch-live-reconciliation-service` | `0.49.1.dev32+g6d542ab27`  | 32                    |
| `fund-administration-service`       | `0.9.33.dev32+gb598d8743`  | 32                    |

Ironically these `+g<sha>` versions are **more** traceable than the frozen `0.55.0` — they name their commit.

**d) Worst case — total identity loss:** `instruments-service` published **`0.0.0.dev0`** on 2026-07-03. That is
hatch-vcs's no-git-history fallback (shallow checkout / no tags reachable). It carries no version and no sha.

### ⚠ This CORRECTS `stale_staging_versions_manifest_2026_07_23.md`

That issue framed `staging_versions` as the stale, harmful key. **The inverse is closer to the truth**: in all four
repos above, `staging_versions` equals the last real git tag — i.e. the actual package version — while `versions` does
not. The two keys did not "drift because staging froze"; they diverged because **tagging broke**, and each key is
tracking a different thing. That issue's recommended fix (make the dep gate ignore `staging_versions` under dormancy)
should NOT be implemented until F2 is resolved, or the gate will start trusting the key that matches reality _less_.
Cross-linked; do not action them independently.

## F3 — Other orphan dispatches (P2)

Same 204-is-not-delivery class as F1, all from the dispatch-graph audit (reported, spot-checked, not each independently
re-verified — flagged where so):

| dispatch                                                    | target                   | what silently never happens                                              |
| ----------------------------------------------------------- | ------------------------ | ------------------------------------------------------------------------ |
| `cascade-qg-ordering.yml:229-236` → `quality-gate-run`      | each dependent repo      | Cascade QG never triggers a QG; it then polls pre-existing state         |
| 8 services' `cloudbuild.yaml` → `service-deployed`          | deployment-service       | post-deploy notification never lands (both sites end `\|\| true`)        |
| 24 repos' `semver-agent.yml:828` → `schema-changed`         | unified-trading-pm       | T0 schema-change notification never lands                                |
| `sit-gate.yml:236,240` → `game-day-sit`, `synthetic-smokes` | system-integration-tests | Tier-E game-day + synthetic smokes never run (self-admitted best-effort) |

**Dead listeners** (chain broken the other way): `publish-package.yml` (its only dispatcher was never rolled out —
compounds F2); `uac-registry-sync.yml` / `uic-openapi-sync.yml` in 3 repos (UAC→UI sync fully dead);
`reconcile-release-tags.yml` listener.

**Latent repeat of the known bug:** `agent-runner.yml:91` and `sit-gate.yml:357` still self-dispatch via
`${{ github.repository }}`. Correct _only_ because those files exist solely in PM — rolling either into another repo
reproduces the escalation bug verbatim.

## F4 — Vacuous crons still firing (P2, $0 but not free)

All on `[self-hosted, glue]`, so **no GitHub bill** — but ~873 runs/week occupying the glue pool and adding noise:

| workflow                         | cron     | runs/7d | evidence of no-op                                  |
| -------------------------------- | -------- | ------- | -------------------------------------------------- |
| `sit-debounce-trigger`           | `*/5`    | **271** | "Trigger SIT" step `skipped` in 40/40 sampled runs |
| `reconcile-release-tags`         | `*/30`   | **246** | `created 0 tag(s)` — this is F2, not mere waste    |
| `freeze-deferred-build-replay`   | hourly   | 174     | `No active PROD_DEPLOY freeze`                     |
| `fix-approval-timeout`           | `0 */2`  | 91      | `Found 0 open breaking-fix-pending issues` (6/6)   |
| `supersede-stale-dep-update-prs` | `23 */2` | 91      | `Superseded: 0 \| obsolete-closed: 0` (6/6)        |

Also **DEGRADED**: `digest-drift-sweep` never converges ("Dispatched 16 / Already fresh 0" on 3/3 runs; the target
digest changes every tick) and fans out to `ubuntu-latest` downstream — this one **does** cost money.
`workspace-quickmerge-validation` logs `❌ Dependency alignment FAILED` yet concludes `success`.

## F5 — Vacuous manifest readers (P2)

Readers whose input is permanently empty, which then read as GREEN rather than "not applicable":

- `ldr-to-main-promote-fleet.yml:422-434` — SIT gate **part 1** reads `staging_status.breaking_pending`, empty since
  2026-06-08; its only writer fires solely when `branch=="staging"`. Structurally unreachable. **The in-file comment
  claiming "BOTH stay live for ldr_main repos" is now false.** (Part 2 still gates — see the clean bill below.)
- `_repo_ci_stuck.py:148,155` — `stuck_in_sit` can never fire; the jam class the panel exists for is invisible.
- `ci_failure_watcher.py:761-763` — `promotion_quarantine` `{}` → repeated promotion failure never pages.
- `repo_ci.py:643-670` — "Promotion blocked" panel always renders GREEN, never "unknown".
- `_repo_ci_manifest.py:285-289` — reads `deployed_versions.get(repo)` but the writer (`cloud-build-router.yml:853`)
  writes `[env][repo]`; **shape mismatch**, column permanently blank.
- `generate_system_topology.py:104,215` — publishes a 2026-06-08 `staging_status` snapshot to consumers as current.

**Good pattern to copy** (these check dormancy correctly): `promotion_lag_monitor.py:190-199`,
`_repo_ci_manifest.py:251-258`, `deployment-ui/src/lib/repoCi.ts:214-218`.

## ✅ Clean bill of health — the breaking-change gate IS live

Worth stating plainly because it was the sweep's biggest fear. The cross-repo breaking-change gate **genuinely evaluates
and fails CLOSED**, evidenced from real run logs, not YAML reading:

- `29898858111` (07-22):
  `SIT GATE BLOCK market-tick-data-service: true-delta not SIT-validated on this tree … fail-CLOSED` + auto-dispatched
  `full-workspace-sit`
- `29902097405` (+52 min): same repo `SIT GATE PASS`; agent-orchestrator newly BLOCKED
- `30008639044` (today): 15 repos evaluated with per-repo verdicts

A block → re-validate → pass cycle is something a vacuous gate cannot produce. The empty `breaking_pending` (F5) is only
the redundant first layer; the load-bearing layer is the Firestore `sit_validated_tree` comparison, which is fed nightly
by `full-workspace-sit.yml`'s own `0 3 * * *` cron. **Fail-open points that remain** (ranked): UI repos have
`breaking_scan_dir: none` so TypeScript surface breaks are structurally invisible; three `ldr_main`-but-not-SIT-covered
repos take the `SIT GATE N/A` branch; and `sit_validated_workspace_digest` is still WRITTEN but never READ, so a repo
validated against UAC v1 can promote after UAC v2 lands.

## Option B — move version minting into the PM reconciler (OPERATOR DECISION 2026-07-23)

> ## ⛔ SUPERSEDED 2026-07-25 — OPTION B WAS NEVER BUILT; THE SEMVER-AGENT RETARGET SHIPPED INSTEAD
>
> _(Recorded 2026-07-26 by `/plan-reconcile ci`. `/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` §
> Phase 4 already logged that "the codex `ci-cd-flow.md` § 'Release tag reconciler' **+ the Option-B doc** are now
> stale/contradictory and need reconciliation" — the codex half landed 2026-07-25; this is the doc half.)_
>
> **Everything below this banner describes a decision that was reversed two days later.** Do not implement the
> sub-steps.
>
> **What actually happened**, on an explicit operator directive 2026-07-25 (_"we are NOT gonna use staging right now
> unless we flip the toggle, so under the ldr to main we need a full mechanism for that, all repos do it properly"_):
>
> - `semver-agent`'s trigger was retargeted `branches: [staging]` → **`push: branches: [main]`** in the fleet SSOT
>   template — `unified-trading-pm@0b128a725` (verified ancestor of `origin/live-defi-rollout` this session).
> - Rolled to **all 22** `ldr_main` + `version_source=git-tag` repos (per-repo shas in
>   `/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` § Phase 4). Verified independently here by
>   reading an installed copy: `unified-api-contracts/.github/workflows/semver-agent.yml` is `push: branches: [main]`.
> - **Proven live end-to-end**: semver-agent fired on `unified-api-contracts` main 2026-07-25T20:01:24Z, and
>   `unified-trading-library` **v0.57.0 was genuinely published to Artifact Registry** — the first real publish since
>   2026-06-27.
> - The centralized PM minter this section designs was found **DECIDED BUT NEVER BUILT and architecturally incoherent
>   for git-tag repos**: `scripts/cicd/reconcile_release_tags.py` has **no `--mint` implementation** (grepped this
>   session) and hard-refuses to mint for dynamic-versioned repos; its own STALL message names semver-agent as the
>   minter.
> - **Codex now rules the opposite of this section**: `/codex/08-workflows/ci-cd-flow.md:1004` § _"Release tag
>   reconciler — a STALL DETECTOR, not the minter (corrected 2026-07-25)"_.
>
> **Corroborating measurement**: this section's premise was "no tags are minted and `versions` is NOT advancing". Ran
> the gate command 2026-07-26 — `git log --grep='chore(manifest): update' -- workspace-manifest.json` shows **14 entries
> since 2026-07-23**, newest `936a2e31a` (2026-07-26T01:11Z). Minting is live again.
>
> **The 6 `- [ ]` sub-steps below are left unticked on purpose** (they were superseded, not completed). Their retirement
> — and whether the operator's original cost/noise objection to the retarget still stands — is parked as a planning
> call.

**Decision: adopt Option B. The per-repo `semver-agent` retarget is REVERTED and stays dead.**

### Why the obvious fix was rejected

Retargeting `semver-agent` to the promotion branch works — that is not in question, it was measured (below). It was
rejected on the two axes the operator actually cares about, both quantified rather than asserted:

| axis             | measured                                                                                                                                                           |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **GHA cost**     | `runs-on: ubuntu-latest`, ~~7.4 runs/day/repo × 24 repos ≈ **178 runs/day**; 15–25 s each but Linux bills a 1-min minimum ⇒ **~~$32/month**                        |
| **commit noise** | each bump dispatches `update-repo-version`, which commits to `workspace-manifest.json`: **733 commits in the 30 days before it died — ~24/day, peaking at 84/day** |

The runner cannot be moved: all 8 self-hosted runners are registered to `unified-trading-pm` **only**, and
`orgs/IggyIkenna/actions/runners` 404s (personal account, no org pool). A fleet template pointing at `[self-hosted]`
would hang forever in all 24 repos. So per-repo minting is billable by construction.

The manifest noise is the part the operator had noticed and welcomed the end of. Worth separating precisely, because the
two halves have different causes:

- **Gone for good** — the `chore(release): bump version to X` commits _inside each repo_. Under `version_source=git-tag`
  the agent mints a tag and makes **zero** commits. That really was the D13 migration.
- **Would come back** — the PM `chore(manifest): update <repo> to <version>` commits. Those stopped because
  **semver-agent died**, not because of the migration.

### Evidence the bump LOGIC is correct (reuse it, don't rewrite it)

Before the revert, the retarget ran for real — `unified-trading-api`, run `30020017387`, 2026-07-23T15:19Z, the first
semver-agent run on `main` since 2026-06-27, conclusion **success**:

```
Dynamic repo (version_source=git-tag): counted 0 v* tag mint(s) in the last hour   ← breaker live on the new path
Baseline versions version for unified-trading-api: 0.2.19                          ← read `versions`, NOT staging_versions
Scanning commits from 7c113d5 (version 0.2.19) to HEAD                             ← BOUNDED scan, not the widening one
Current version: 0.2.19
```

No tag was minted because every commit since `v0.2.19` was `ci:`/`chore:` — **correct behaviour, not a failure.** So the
conventional-commit classification, the baseline-key routing and the circuit breaker are all proven on the `main` path.
Option B relocates this logic; it does not need to reinvent it. The reverted template is recoverable from
`unified-api-contracts@17cc3acc` / `unified-trading-library@ef59d2a0` / `unified-trading-api@5bf6ff3`.

### The design

Move minting into `scripts/cicd/reconcile_release_tags.py`, already scheduled `*/30` in PM **on self-hosted runners
(\$0)**. For each tag-derived repo it would: read commits on `main` since the newest `v*` tag via the GitHub API,
classify them by conventional-commit prefix (the rules above), compute the next version, and mint the tag — then write
**one batched manifest commit per run** instead of one per bump.

|            | per-repo agent (rejected) | reconciler (option B)                 |
| ---------- | ------------------------- | ------------------------------------- |
| runner     | `ubuntu-latest`, billable | PM self-hosted, **$0**                |
| runs       | ~178/day                  | already-scheduled `*/30`, no new runs |
| PM commits | ~24/day, peaks 84         | **≤1 per run**, batched               |
| bump logic | proven (above)            | **same logic, relocated**             |

### Known risks to handle when implementing

1. **`--max-creates` matters more here.** One reconciler run could mint 22 tags at once and fire 22 `publish-package`
   runs. The existing cap exists for exactly this; keep it low on the first drain.
2. **API-diff breaking detection is lost.** The per-repo agent had the repo checked out and could run
   `detect_breaking_change.py`. The reconciler sees commit messages only, so it can classify `feat!:` but not an
   undeclared API break. Decide explicitly: accept message-only classification, or have the reconciler dispatch the diff
   check. **This is a real capability reduction and must not be glossed over.**
3. **The circuit breaker must be re-implemented reconciler-side**, or the runaway protection is lost — the 2026-06-10
   incident (0.3.0→0.30.0 at 1 bump/min) is what it exists for. Rate-limit by tag mints/hour as the git-tag path does.
4. **Do not backfill ~2,490 intermediate releases.** Those artifacts never existed; inventing them is fabrication. Each
   repo gets ONE tag capturing current `main`; the gap stays a gap.
5. **Shared GitHub rate limit** — the reconciler authenticates as the same user the CI dep-clone steps use. See the
   rate-limit caveat in `/codex/08-workflows/ci-cd-flow.md`.

### Sub-steps

- [x] ⛔ [INFRA] P1. **RETIRED 2026-08-08 (operator ruling: formally retire Option B now — see
      `/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` § Phase 4).** ~~Implement conventional-commit
      bump computation + tag mint in `reconcile_release_tags.py`, reusing the proven rules. Gate behind an explicit
      `--mint` flag so the detector stays usable standalone.~~ Moot -- the per-repo `semver-agent` retarget
      (`unified-trading-pm@0b128a725`, `push:[main]`, fleet-rolled to all 22 `ldr_main` repos) shipped instead and is
      proven live (see the ⛔ banner above this section). No `--mint` flag exists or will be built;
      `reconcile_release_tags.py` stays a STALL DETECTOR only (`/codex/08-workflows/ci-cd-flow.md:1004`).
- [x] ⛔ [DOC] P1. **SUPERSEDED 2026-07-25, formally retired 2026-08-08 (operator ruling — see
      `/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` § Phase 4).** Option B (this whole sub-steps
      list) was never built; the per-repo `semver-agent` retarget shipped instead (see the ⛔ banner above this
      section + the Resolution checklist's F2 item). There is no reconciler-side message-only-vs-API-diff tradeoff to
      rule on since the reconciler itself does not exist and is not being built.
- [x] ⛔ [INFRA] P1. **RETIRED 2026-08-08 (operator ruling — see
      `/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` § Phase 4).** ~~Port the bump-rate circuit
      breaker to the reconciler (tag-mints/hour), plus a low `--max-creates` for the first drain.~~ Moot -- the
      reconciler-side minter this circuit breaker would protect is not being built; the per-repo `semver-agent` retarget
      shipped instead and already carries its own proven circuit breaker (the 2026-06-10 incident's fix, unchanged by
      this retarget).
- [x] ⛔ [INFRA] P2. **RETIRED 2026-08-08 (operator ruling — see
      `/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` § Phase 4).** ~~Batch the manifest write to
      ONE commit per run (the whole point of B) — verify by confirming a single `chore(manifest):` commit after a
      multi-repo mint.~~ Moot -- Option B (the whole point of which was this batching) was never built; the per-repo
      semver-agent retarget shipped instead, with its own unbatched-but-now-restored per-repo manifest commits (F2's
      outcome achieved by the opposite route -- see the Resolution checklist item).
- [x] ⛔ [INFRA] P2. **RETIRED 2026-08-08 (operator ruling — see
      `/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` § Phase 4).** ~~First supervised drain: run
      with `--dry-run`, eyeball the 22 proposed versions, then mint.~~ Moot -- there is no reconciler-side mint path to
      drain; minting already happens per-repo via the live semver-agent retarget.
- [x] ⛔ [DOC] P2. **RETIRED 2026-08-08 (operator ruling) — already superseded in practice.** ~~Update
      `/codex/08-workflows/ci-cd-flow.md` § "Release tag reconciler" once B ships — it currently documents B as
      _planned_.~~ B will never ship; codex already reflects the actual shipped state
      (`/codex/08-workflows/ci-cd-flow.md:1004` § "Release tag reconciler — a STALL DETECTOR, not the minter (corrected
      2026-07-25)"), so there is nothing left to update for this specific item.

## Docs (P2)

**RESOLVED — DONE 2026-07-26 (`unified-trading-pm@97970974e`), this section is stale, corrected 2026-08-10
(plan_reconciler, ci tranche).** This prose was never struck after the matching `[DOC] P2` resolution-checklist item
below shipped — it described already-fixed content as still open. Both gaps this section named are independently
re-verified fixed as of this correction: `/codex/08-workflows/ci-cd-flow.md`'s branch-model narrative now correctly
describes the LDR→main model ("Exactly three things gate a repo's LDR→main promotion", not the old 15-min staging-cron
narrative), and a "Staging re-entry procedure" section (with explicit uncomment-the-disabled-triggers guidance) now
exists in codex. See the `[DOC] P2` item under Resolution checklist for the full citation.

---

## Resolution checklist

- [ ] [BACKEND] P0→**TIME-GATED (re-affirmed 2026-07-28, retagged away from `[OPERATOR]`)**. **F1 (kill-switch).** RULED
      2026-07-28 (2026-07-28 operator-decisions pass, applying the general theme): this stays correctly DEFERRED — not
      because it is still awaiting an operator authority decision, but because execution-service genuinely does not run
      live order flow yet, so there is nothing to implement/verify a halt against yet. Retagged away from `[OPERATOR]`
      because no further operator input is needed to keep this on track — it activates automatically as a normal
      engineering todo the moment its own gate condition (below) is met. **Standing 2026-07-23 ruling preserved
      verbatim**: KEEP TRACKED, DO NOT FIX YET. Rationale: not in production, and no execution-service is currently
      running — so the no-op kill-switch cannot presently mask a real halt failure. To be fixed **when execution-service
      work starts**. **Directional guidance for when the gate opens** (applying the operator's full-completion theme —
      "things should recover FULLY if they die or restart... prefer building the full automatic recovery, not just a
      manual runbook note" — to a live-trading safety mechanism): the default answer when this activates should be
      **IMPLEMENT the real `halt-order-flow`/`resume-order-flow` listener in execution-service**, not delete the
      kill-switch call path — a genuine trading-safety control should be built properly, not removed to avoid the work,
      unless whoever picks up execution-service work finds a concrete reason the mechanism itself is obsolete by then.
      ⚠️ **Re-entry gate unchanged: this item must be closed BEFORE execution-service handles live order flow** — the
      defect is invisible at runtime (204 reads as success), so it will not resurface on its own. Whoever picks up
      execution-service work owns this.
- [x] ⛔ [INFRA] P1. **SUPERSEDED 2026-07-25, formally retired 2026-08-08 (operator ruling: retire it formally now — see
      `/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` § Phase 4).** ~~F2 — restore version minting
      via OPTION B (the PM reconciler), NOT the per-repo agent.~~ **F2's OUTCOME (version minting restored) IS ACHIEVED
      — by the opposite route.** On an operator directive 2026-07-25 the per-repo `semver-agent` was retargeted
      `staging` → `push:[main]` (`unified-trading-pm@0b128a725`, ancestor-verified), fleet-rolled to all 22
      `ldr_main`+git-tag repos, and proven live (`unified-trading-library` v0.57.0 published to Artifact Registry, the
      first real publish since 2026-06-27). The PM-reconciler minter was **never built** and is architecturally
      incoherent for git-tag repos. See the ⛔ banner on § "Option B" below and
      [/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md](/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md)
      § Phase 4. The per-repo semver-agent retarget is what shipped and holds — Option B is closed, not just
      unimplemented.
- [x] ✅ [INFRA] P1. **Fix F2 — make the BACKSTOP able to report the outage.** `scripts/cicd/reconcile_release_tags.py`
      now splits two populations: tag-derived repos (all 23 today) are **N/A for tag creation** — minting a tag from a
      version is circular when the tag defines the version — and are instead checked for the real invariant, that `main`
      must not accumulate commits past the newest `v*` tag. Legacy static-version repos keep the original path. **Ran
      live (`--dry-run`, not read): 22 repos STALLED, 26–29 days, ~2,490 unreleased commits** — e.g.
      `instruments-service` 402, `market-tick-data-service` 354, `deployment-service` 257. `--fail-on-stall` opts a
      caller into a hard failure; the default is a `::warning::` so the `*/30` schedule does not fail 48×/day.
- [x] ✅ [INFRA] P1. **Fix the `0.0.0.dev0` publish** (`.github/workflows/publish-package.yml`). Root cause was a
      SHALLOW checkout: no `fetch-depth: 0` ⇒ no tags ⇒ hatch-vcs falls back to its no-history sentinel. Added
      `fetch-depth: 0`; replaced the version check (a fourth copy of the same broken static-`version =` grep, which
      resolved to `"unknown"` and only WARNed) with an assertion against the **built wheel's** actual version, failing
      closed on `0.0.0.dev0`; `published_packages` and the publish log now record the BUILT version, not the payload's.
- [x] ✅ [INFRA] P1. **Stop re-pointing the `:VERSION` Docker tag** (`unified-trading-library/cloudbuild.yaml`, the only
      repo with this pattern — verified fleet-wide). `VERSION` came from `git describe --abbrev=0` (the bare nearest
      tag), so every build between two tags re-tagged the same string. Now `:{version}-{sha12}` is always applied and
      never re-pointed, `:latest` stays the mutable alias, and the bare `:{version}` tag is applied **only when HEAD is
      exactly the release commit** — so a version tag names exactly one tree. Probe repointed to the unique tag.
- [ ] [INFRA] P2. **Reconcile the ~4 weeks of missing tags.** NOTE: this is deliberately NOT a backfill of ~2,490
      intermediate releases — those artifacts never existed and inventing them would be fabrication. Each repo's first
      post-fix promotion mints ONE tag capturing current `main`; the gap stays a gap, correctly. This todo is only to
      CONFIRM that happened for all 22, and to hand-mint for any repo whose promotion is idle. **2026-07-25 partial
      progress**: hand-minted + republished `unified-trading-library` and `unified-api-contracts` specifically (see the
      two new checked items below) — these were the two actively blocking real production Cloud Build failures
      (`instruments-service` and others could not resolve `unified-trading-library>=0.56.0`, a floor no published
      version satisfied since 2026-06-27). The other ~20 stalled repos in the table above are still open; this todo item
      itself stays unchecked. **na-eligibility-audit 2026-08-01: already tracked (not yet done) as an open todo in
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md` ("Fleet version/tag-state census (read-only, NO tag minting)"),
      which cites this exact checkbox as its Source — track completion there.** **2026-08-02 census complete**
      (`ci_satellite_ao_dispatch_batch1-020`, read-only, zero tags minted): 11 of the 22 have since minted a post-fix
      tag; 11 remain stalled today (`agent-orchestrator`, `batch-live-reconciliation-service`, `client-reporting-api`,
      `e2e-testing`, `fund-administration-service`, `greeks-service`, `ibkr-gateway-infra`,
      `market-data-processing-service`, `ml-service`, `system-integration-tests`, `trading-agent-service`). Also found:
      the manifest `versions{}` cache lags tags for 15 of 24 repos on `live-defi-rollout` specifically because
      `main-backmerge-to-ldr.yml` has failed on every run since 2026-07-29T15:48:27Z (~3 days, previously unreported) —
      the writer (`update-repo-version.yml`) is healthy and `main`'s cache is current. Full dated table + evidence:
      [/plans/archive/issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md](/plans/archive/issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md)
      § "Fleet version/tag-state census (2026-08-02)". New P1 filed for the backmerge outage:
      [/plans/archive/issues/main_backmerge_to_ldr_silent_failure_2026_08_02.md](/plans/archive/issues/main_backmerge_to_ldr_silent_failure_2026_08_02.md).
      This todo itself stays unchecked — the census is done, but the 11 still-stalled repos and the new backmerge P1 are
      open follow-up work, not this todo's own completion.
- [x] ✅ [INFRA] P1. **`publish-package.yml`'s per-repo DISPATCHER was never actually installed on the two frozen
      library repos (2026-07-25 finding, sharpens the "dead listener" framing above)** — not merely un-rolled-out in the
      abstract: `unified-trading-library/.github/workflows/publish-package.yml` was still the **pre-refactor "Publish to
      GitHub Packages" workflow** (triggers on `push: tags: v*`, builds a wheel, uploads it as a GitHub Actions build
      artifact — never touches Artifact Registry at all; a leftover from before this repo was renamed from
      `unified-cloud-services`), and `unified-api-contracts` had **no `publish-package.yml` file whatsoever**. So even
      with F2 fixed, neither repo would have dispatched anything. Separately, the CANONICAL propagation template itself
      (`scripts/propagation/templates/publish-package.yml`) still had the same dead static-`version =` grep as
      `reconcile_release_tags.py` — installing it as-is would have `exit 1`'d on every hatch-vcs repo. Fixed: the
      template now derives a best-effort `git describe`-based version hint (the receiver's own build-the-wheel step is
      the authoritative version regardless — this is only for the dispatch payload), installed on both repos.
- [x] ✅ [INFRA] P1. **`unified-trading-library/cloudbuild.yaml` REGRESSION from the 2026-07-23 `:VERSION` Docker-tag
      fix above — silently rejected every push-triggered build since** (2026-07-25 finding, separate from F2/F3). That
      same commit's new comments referenced the bare shell variable as `$VERSION` (single `$`) instead of the
      double-escaped `$$VERSION` every other reference in the file correctly uses. Cloud Build's substitution validator
      does a RAW TEXT scan of the whole resolved build config — including comments — for `$IDENTIFIER` tokens, so a bare
      `$VERSION` anywhere trips
      `invalid value for 'build.substitutions': key in the template     "VERSION" is not a valid built-in substitution`
      before a single build step runs (the `cloud-build-failure-watcher` "silent config-rejection" class — no repo/sha
      substitutions, GitHub shows nothing). Confirmed via `gcloud builds list --filter=status=FAILURE`: recurring
      roughly hourly since 2026-07-23T23:58, ~13+ instances. Fixed by escaping the 4 offending comment lines to
      `$$VERSION`.
- [x] ✅ [INFRA] P1. **Stop re-pointing a released Docker tag at new content** (found by the F2 blast-radius probe): the
      UTL base image is rebuilt daily and re-tagged `0.55.0`/`latest`, so `0.55.0` names a different tree every day and
      rollback-by-version is undefined. Once tagging is fixed, each rebuild must get its own immutable version tag;
      consider pinning service `FROM` lines by digest only. Verify by confirming two builds never share a version tag.
      **2026-08-02 verification (read-only AR probe, `ci_satellite_ao_dispatch_batch1-024`, no image tagged/deleted)**:
      `gcloud artifacts docker images list asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-library/unified-trading-library --include-tags`
      enumerated every tagged digest since the 2026-07-23 `cloudbuild.yaml` fix landed. Parsed 221 tagged rows spanning
      2026-07-23T09:12 → 2026-08-02T16:47 (10 days, 15 versions `0.55.0`→`0.70.0`, up to 41 rebuilds within one version
      e.g. `0.67.0`): **218 distinct `{version}-{sha12}` build tags, every one mapping to exactly 1 digest (0
      collisions)**; **15 bare `{version}` release tags (`0.55.0` … `0.70.0`), every one ALSO mapping to exactly 1
      digest (0 re-pointing events)** — e.g. `0.67.0` was minted once (`0.67.0-4ddbef1255ed`, 2026-07-30T07:30:31) while
      36 OTHER `0.67.0-<sha12>`-only builds that day never touched the bare `0.67.0` tag, confirming the "exact release
      commit only" gate holds. This is 15 independent version releases × up to two months of daily rebuilds each — far
      exceeding "two consecutive rebuilds." **Digest-pinning check**: already fleet-wide — every service Dockerfile
      (`grep -rn 'FROM.*unified-trading-library' --include=Dockerfile .`, 16 repos: market-data-processing-service,
      strategy-service, deployment-api, client-reporting-api, alerting-service, execution-service, features-service,
      agent-orchestrator, fund-administration-service, e2e-testing, trading-agent-service, deployment-service,
      market-tick-data-service, ml-service, batch-live-reconciliation-service, greeks-service) already pins
      `FROM …unified-trading-library@${BASE_IMAGE_DIGEST}` — a digest, never a mutable tag. No further digest-pinning
      work is needed; this was already correct going into the probe. **Verdict: F2 fix holds — no re-pointing observed
      across the full post-fix window; verification item CLOSED.** Read-only throughout (list only, no tag/image
      mutation). Evidence: `ci_satellite_ao_dispatch_batch1_2026_07_26.md` ("Verify the released Docker version tag is
      no longer re-pointed at new content") tracked completion here per its own citation.
- [x] ✅ [INFRA] P2. **Fix `instruments-service`'s `0.0.0.dev0` publish** (2026-07-03, AR `unified-libraries`) —
      instruments-service@79b7d5b4 (rewritten from the orphaned `7d005520` during the 2026-08-05 slot-5 diverged-branch
      reconciliation — content identical, confirmed ancestor of `origin/live-defi-rollout`; the original `7d005520` sha
      only survives on `origin/wip-preserve/slot-5-instruments-service-diverged-20260805T111826Z`, not LDR). DONE via
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s "Confirm instruments-service's publish path can no longer emit
      0.0.0.dev0" todo (full evidence there): the repo's installed `publish-package.yml` was stale pre-migration legacy
      content (no `fetch-depth: 0`, not even the AR-dispatch pattern) — replaced with the canonical
      `scripts/propagation/templates/publish-package.yml` (byte-identical to the working
      `unified-api-contracts`/`unified-trading-library` copies), which now dispatches to PM's already-fail-closed
      receiver. Bad wheel disposition recorded (still present, single 2026-07-03 occurrence, left in place per the
      operator-gated AR-delete rule).
- [x] ✅ [INFRA] P1. **Re-assess `stale_staging_versions_manifest_2026_07_23.md` in light of F2 before implementing its
      fix** — its premise is inverted (see the ⚠ box above). Do not action the two independently. — **DONE, closed via
      `autonomous_session_operator_decisions_2026_07_25.md` entry #33** (operator ruled option 1, the dormancy-aware
      gate), independently confirmed live in `scripts/quickmerge.sh` as of the `na-eligibility-audit 2026-08-01`
      re-assessment of that sibling doc (commit `b3abf1bd5`, 2026-07-30, verified ancestor of current HEAD).
- [x] ✅ [INFRA] P1. **DONE 2026-07-26 (slot-5, `infra`, `ci_satellite_ao_dispatch_batch1-002`) — the static checker
      itself.** Delivered `scripts/quality_gates/check_dispatch_listeners.py` (+ regression tests
      `tests/unit/test_check_dispatch_listeners.py`, 9 cases). Walks every repo for DISPATCH SITES
      (`.github/workflows/*.yml`, `cloudbuild*.yaml`, `buildspec*.yaml`, `scripts/**/*.sh`) and LISTENER SITES
      (`on: repository_dispatch: types: [...]`), resolving owner/repo/event_type through literal values, known
      single-fleet-owner aliases (`OWNER`/`ORG`/`GH_ORG`/`GITHUB_REPOSITORY_OWNER`/`REPO_OWNER` → `IggyIkenna`),
      file-scope shell variable assignments, and — for `trading-kill-switch.sh`'s exact shape — a shell-function wrapper
      pass that resolves each literal-argument call site of a fixed-target/variable-event_type dispatcher. **Reproduces
      F1 + F3 exactly on the live workspace** (run 2026-07-26,
      `python scripts/quality_gates/check_dispatch_listeners.py --show` from a clean checkout): - F1 confirmed:
      `trading-kill-switch.sh:75,96` → `halt-order-flow`/`resume-order-flow` → `execution-service`, no listener. - F3
      confirmed: `cascade-qg-ordering.yml:229` → `quality-gate-run` → dynamic target, **zero repos fleet-wide** listen
      (provably orphan regardless of which dependent repo the loop picks); `sit-gate.yml:235,239` →
      `game-day-sit`/`synthetic-smokes` → `system-integration-tests`, no listener (only `full-workspace-sit` is
      registered there); 12+ services' `cloudbuild.yaml`/`buildspec.aws.yaml` → `service-deployed` →
      `deployment-service`, no listener. - **New orphans the checker additionally found** (not previously enumerated in
      F3, same class): all 24 repos' `semver-agent.yml` → `schema-changed` → `unified-trading-pm`, no listener;
      `unified-api-contracts/cloudbuild.yaml` → `library-published` → `deployment-service`, no listener;
      `ci-status-update.yml` → `tier-ab-green` → `unified-trading-pm`, no listener;
      `sit-gate.yml`/`sit-unlock.yml`/`staging-to-main.yml` → `staging-locked`/`staging-unlocked` → dynamic target, zero
      listeners anywhere (the target's listener block is deliberately commented out per the 2026-07-23 staging-machinery
      shutdown — expected dormancy, not a fresh bug). - **Total: 63 orphan dispatch sites, 344 dispatch sites scanned,
      13 unresolved** (documented residual — 2 are genuinely-generic utility functions
      `dispatch_with_retry`/`stagger-dispatches.sh` with ZERO call sites anywhere in the fleet today, confirmed by a
      workspace-wide grep, so nothing to resolve). Baselined at 63 in
      `scripts/quality_gates/check_dispatch_listeners_baseline.yaml` (shrinking ratchet — any NEW orphan beyond 63
      fails; the 63 are today's tracked, known-broken set, this list). **Deliberately NOT wired into
      `scripts/quality-gates.sh` yet** (same-file contention with 2 sibling new checkers from this batch — the single
      registration commit is `ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`'s todo). Regression tests prove:
      reproduces an F1-shaped orphan, a matching-listener case is NOT flagged, a wildcard listener covers any type, the
      cloudbuild/buildspec escaped-JSON-quote shape parses, the dynamic-target-with-zero-listeners-anywhere case is
      flagged while a dynamic-target-with-SOME-listener case is correctly left unresolved (not asserted either way), the
      shell-wrapper per-call-site resolution works, and the baseline ratchet exits 0 at-baseline / 1 on a synthetic new
      orphan beyond it. Full PM `quality-gates.sh` green (1356 passed, 16 skipped, 77.95s). **Still open, NOT this
      todo's scope**: fixing the unconditional `&& echo "...dispatched"` success-reporting at the F3 sites themselves
      (that's a separate remediation once the checker exists to prevent regressions) — split into its own follow-up
      below so this todo stays scoped to "make it observable", per its own title.
- [ ] [INFRA] P2. **Fix the unconditional `&& echo "...dispatched"` success reporting at the F3 orphan-dispatch sites**
      (split out from the item above once the observability checker existed to prevent a regression while fixing):
      `cascade-qg-ordering.yml`, `sit-gate.yml` (`game-day-sit`/`synthetic-smokes` — already `::warning::`-guarded, so
      likely already correct; verify), the 12+ services' `cloudbuild.yaml`/`buildspec.aws.yaml` `service-deployed`
      dispatches, and the 24 repos' `semver-agent.yml` `schema-changed` dispatch. For each: either add the missing
      listener in the target repo, or stop claiming success when the dispatch has no subscriber. Use
      `check_dispatch_listeners.py --show` to enumerate the current live set before starting, and re-baseline
      (`--baseline-write`) as each is fixed so the ratchet only ever shrinks. -
      **`service-deployed → deployment-service` SLICE: DONE 2026-08-06** (operator-approved same-day fix, not just
      documented). Added `deployment-service/.github/workflows/service-deployed-listener.yml`
      (`on: repository_dispatch: types: [service-deployed]`) + `scripts/cicd/handle_service_deployed_dispatch.py` + an
      explicit-allowlist `deployment_service/auto_deploy_allowlist.py` (default-deny — operator ruling 2026-08-06,
      pre-live-cutover: only genuinely-live, pinned-tag, long-lived Cloud Run **Services** not already covered by their
      own dedicated `-main-deploy` trigger are eligible; today that's exactly `alerting-service` →
      `dp-alerting-subscriber`). Reuses deployment-api's existing `POST /api/deployments/{service}/deploy`
      (`deploy_build()`) via a new backward-compatible `cloud_run_service_name` override (added because
      alerting-service's image name and its live Cloud Run service name diverge — a real gap this work surfaced).
      `cascade-qg-ordering.yml`, `sit-gate.yml` (`game-day-sit`/`synthetic-smokes`), and the 24-repo `semver-agent.yml`
      `schema-changed` slice are **explicitly OUT of scope for this fix and remain open** — different event types/target
      repos/owners, not touched. Shipped `deployment-service@5599bda8`, `deployment-api@7110d2d`. Re-baselined
      `check_dispatch_listeners_baseline.yaml` 63→38 (the drop is larger than one event_type because ~11 services'
      `cloudbuild.yaml`+`buildspec.aws.yaml` all dispatched the same `service-deployed → deployment-service` pair, now
      resolved as one listener). Full verification (real Cloud Run revision timestamp change on
      `dp-alerting-subscriber`) + a separate flagged finding (`DISABLE_AUTH=true` currently live on prod
      `uts-shared-deployment-api`) are in the Progress Log below. **Citation added 2026-08-07 (na-eligibility-audit)**:
      the remaining open scope (`cascade-qg-ordering.yml`, `sit-gate.yml`) is tracked in
      `ci_satellite_ao_dispatch_batch5_2026_08_02.md` (~line 249, `status: active`, `assigned_vm: planning`), which
      explicitly cites this doc as Source — do not re-extract, batch5 already owns it. **`cascade-qg-ordering.yml` /
      `sit-gate.yml` SLICE: DONE 2026-08-07 (`ci_satellite_ao_dispatch_batch5_2026_08_02.md` todo 6) —
      `unified-trading-pm@ead69c37d`** (verified ancestor of `origin/live-defi-rollout`,
      `ci_satellite_ao_dispatch_batch6_finalize` todo 1). `cascade-qg-ordering.yml`'s `quality-gate-run` orphan was
      already fixed 2026-08-03 (switched to `workflow_dispatch` of `quality-gates-v2.yml`, which fails loudly on no
      target). `sit-gate.yml`'s `game-day-sit`/`synthetic-smokes` guards existed but were dead code (GitHub returns 204
      for `repository_dispatch` regardless of listener existence, so the success branch always fired) — fixed by
      changing the message to `::notice::Fired X (best-effort; GitHub 204 does not confirm listener)`, no longer
      implying a confirmed dispatch. **Only remaining open scope**: the 24 repos' `semver-agent.yml` `schema-changed`
      dispatch (D5-2 in batch5's Deferred table, conflict-gated on the `scripts/workflow-templates/` rollout mechanism —
      not claimed by batch6 either; still genuinely open).
- [ ] [INFRA] P2. Disable or fix the F4 vacuous crons (`sit-debounce-trigger`, `freeze-deferred-build-replay`,
      `fix-approval-timeout`, `supersede-stale-dep-update-prs`); diagnose `digest-drift-sweep`'s non-convergence (it
      costs real money via `ubuntu-latest` fan-out); ~~make `workspace-quickmerge-validation` fail when it logs a
      failure~~. **STALE (na-eligibility-audit 2026-08-03)** — the `workspace-quickmerge-validation` fix is DONE, closed
      via `plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md:229` (`unified-trading-pm@6f898f930`, removed the
      blanket `|| true`, `if: always()` on artifact-upload, fixed a `set -e` early-exit bug). The other sub-items (F4
      vacuous crons, `digest-drift-sweep` non-convergence) remain open — not closing this checkbox.
- [x] ✅ [INFRA] P2. Fix the F5 readers so an empty input renders as **"unknown"/"not applicable", never GREEN** —
      starting with the `deployed_versions` shape mismatch and the `stuck_in_sit` / promotion-blocked panels. Correct
      the false comment at `ldr-to-main-promote-fleet.yml:422-434`. — **3/4 sub-items DONE 2026-07-29 via
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (INFRA P2, citing this doc's § F5 as Source)**: the
      `deployed_versions` shape mismatch fixed, the `repo_ci.py` promotion-blocked panel confirmed already-fixed, the
      false `ldr-to-main-promote-fleet.yml` comment corrected. The 4th sub-item (`stuck_in_sit` tri-state) was
      deliberately forked into its own larger, properly-scoped doc: `issues/repo_ci_stuck_in_sit_tristate_2026_07_29.md`
      — track that item there, not here.
- [ ] [INFRA] P2. Close the `sit_validated_workspace_digest` written-but-unread gap, or document why it is safe to drop.
- [x] ✅ [DOC] P2. Update `/codex/08-workflows/ci-cd-flow.md` (L75-109, L763, L777-786, L1183) to the current LDR→main
      model, and add the staging re-entry procedure INCLUDING "uncomment the disabled triggers" to codex. — **DONE
      2026-07-26 (slot-5, `cicd`) — `unified-trading-pm@97970974e`**, via
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (citing this doc's `[DOC] P2` + § Docs as Source): fixed all four
      narrative sites, added the Staging re-entry procedure section, corrected the WARN-default line.
- [x] ✅ [REVIEW] P3. Guard the latent repeat: `agent-runner.yml:91` / `sit-gate.yml:357` self-dispatch is safe only by
      file placement. Either hardcode the PM target or add a rollout guard. — **DONE 2026-07-28 (slot-11, `infra`) —
      `unified-trading-pm@cb5e944f0`**, via `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (citing this doc's
      `[REVIEW] P3` as Source): hardcoded the PM target in both files.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — of 18 open items, 8 must NOT be
dispatched as written: the 6 Option-B sub-steps sit under a ⛔ SUPERSEDED banner that says they are "left unticked on
purpose" with their retirement "parked as a planning call"; the F2 resolution item is ⛔ "SUPERSEDED — DO NOT IMPLEMENT
AS WRITTEN" with retirement likewise parked; and F1 (kill-switch) is TIME-GATED on execution-service handling live order
flow per a dated 2026-07-28 ruling. The F4 vacuous-cron item is parked as ci batch2 Deferred **E10**. Flipping
`assigned_vm` in place would dispatch the superseded set, so this stays NA. **The ~10 genuinely bounded remaining items
(Docker version-tag repointing, the `0.0.0.dev0` publish, F3 success-reporting, F5 readers, the codex LDR→main narrative
update, the self-dispatch guard) are real carve-out candidates for a future `/ag-closeout-audit` ci batch — extraction,
not an in-place flip.**

**na-eligibility-audit 2026-08-01** (tranche `ci`, autonomous): KEEP-NA, stale-items — re-read all 18 open items
end-to-end. The superseded/time-gated/operator-gated set (8 items) is unchanged and correctly stays NA. Of the remaining
~10, found several were ALREADY closed elsewhere but never flipped here: closed 3 as KEEP-NA-STALE (reconcile-tags,
Docker re-pointing, `0.0.0.dev0` — each annotated with a citation to the still-open tracking todo in
`ci_satellite_ao_dispatch_batch1_2026_07_26.md`, not independently re-actioned), closed 1 as resolved-elsewhere
(`stale_staging_versions_manifest` re-assessment, via `autonomous_session_operator_decisions_2026_07_25.md` entry #33),
and flipped 3 to `[x]` DONE with commit citations that a prior audit pass missed (F5 readers 3/4 done + 1/4 forked to
`repo_ci_stuck_in_sit_tristate_2026_07_29.md`; the ci-cd-flow.md docs update; the agent-runner/sit-gate self-dispatch
guard — all three shipped via `ci_satellite_ao_dispatch_batch1_2026_07_26.md`, `unified-trading-pm@97970974e` /
`@cb5e944f0`). F3 success-reporting remains the one genuinely-uncovered bounded gap, still not yet extracted into any
active batch — flagged again as the standing carve-out candidate. Doc stays NA overall.

## Progress Log

- **context-scout 2026-08-03**: populated/refreshed context_scope (6 entries) — added
  `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md`, the active plan repeatedly cited throughout
  the Resolution checklist as the doc actually tracking completion of most of this doc's shipped/remaining sub-items.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — SUPERSEDED banners on 6 items, time-gated kill-switch, extraction
candidates exist

- **sub-agent 2026-08-06 — `service-deployed → deployment-service` slice shipped, live E2E verification IN PROGRESS (not
  yet closed)**: full build + ship summary is inline at the todo above; this entry tracks verification status. Shipped
  `deployment-service@5599bda8` (listener + allowlist + tests) → promoted to `main`, then found a REAL bug on the first
  live test fire (a manually-simulated `service-deployed` dispatch for `alerting-service` v0.60.0): the workflow's
  `pip install --quiet -e .` step failed in CI
  (`ERROR: Could not find a version that satisfies the requirement unified-api-contracts<1.0.0,>=0.96.0` — no
  GAR-authenticated Python index configured on a bare `ubuntu-latest` runner). Root cause:
  `from deployment_service.auto_deploy_allowlist import ...` forces execution of `deployment_service/__init__.py`, which
  pulls the package's full heavy dependency tree even though `auto_deploy_allowlist.py` itself has zero external
  imports. Fixed by loading the file directly via `sys.path` (importing it as a bare top-level module, never touching
  the package `__init__.py`) and dropping the now-unneeded pip-install step entirely — `deployment-service@4a69f9d0`.
  Re-ran `quality-gates.sh --no-fix` against this exact commit post-fix (coordinator-requested sentinel check) —
  confirmed `.qg_last_passed_sha` matches HEAD `4a69f9d0`, genuinely green, not just "looked fine." Also confirmed live
  (before firing any dispatch) that `uts-shared-deployment-api`'s own separate `_DEPLOY=true` main-deploy Cloud Build
  trigger had already redeployed my `deployment-api@d3ea7ac` (the `cloud_run_service_name`-override commit) to prod — so
  the deploy target the listener calls already carries the fix. **Still open**: the bugfixed
  `deployment-service@4a69f9d0` is on LDR, promotion to `main` is pending — blocked (not by anything in this fix) on the
  unrelated SIT-stamping bug documented in `issues/sit_stamp_skipped_on_detached_head_pinned_sha_2026_08_06.md` (now
  fixed live at `system-integration-tests@0dc3ff1`, per that doc). Once `4a69f9d0` reaches `main`, the remaining step
  is: re-fire
  `gh api repos/IggyIkenna/deployment-service/dispatches -f event_type=service-deployed -F 'client_payload[service_name]=alerting-service' -F 'client_payload[version]=0.60.0' -F 'client_payload[image]=asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/alerting-service:0.60.0'`
  and confirm `dp-alerting-subscriber`'s Cloud Run revision moves off `dp-alerting-subscriber-00015-lcn` (created
  `2026-07-28T06:17:13Z`, image `alerting-service:diag-62b850c`) to a fresh revision on `alerting-service:0.60.0`. A
  first fire attempt (pre-bugfix, run `31114870431`) correctly left `dp-alerting-subscriber` untouched on failure — no
  partial/bad state, confirmed live. This is a genuinely different scope than the todo's remaining sub-items
  (`cascade-qg-ordering.yml`, `sit-gate.yml`, the 24-repo `schema-changed` dispatch) — do not close those from this
  entry.

**na-eligibility-audit 2026-08-07** (tranche `ci`, autonomous, `agt-cbbd1f`): KEEP-NA, stale citation fixed — re-read
all 12 open items end-to-end. 11 remain genuinely operator-/design-gated (SUPERSEDED banners, time-gated kill-switch F1,
fleet-wide tag-minting judgment call, unruled F4 cron disposition, unresolved `sit_validated_workspace_digest` design
call). 1 (the F3 `cascade-qg-ordering.yml`/`sit-gate.yml` success-reporting remainder) was already extracted into
`ci_satellite_ao_dispatch_batch5_2026_08_02.md` (status: active) but this doc's own checkbox carried no back-citation —
added one. No `assigned_vm` change. **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid —
re-read all 5 remaining open items against today's 9 operator-Q&A precedents; none apply. F1 (kill-switch) stays
TIME-GATED on execution-service handling live order flow, unchanged. The "reconcile ~4 weeks of missing tags" item and
the F3 success-reporting remainder stay KEEP-NA-STALE (already-duplicated in
`ci_satellite_ao_dispatch_batch1_2026_07_26.md` / `batch5_2026_08_02.md` respectively, both cited in place). The F4
vacuous-crons item bundles a plausibly-bounded sub-part (disable 4 named no-op crons) with a genuinely open-ended
sub-part (`digest-drift-sweep`'s non-convergence, itself gated on the dormant- cascade investigation) — not split out or
reclassified here. The `sit_validated_workspace_digest` item ("close the gap, or document why safe to drop") is a
genuine design call, not a checkable fact. No `assigned_vm` change.

**round-9 combined RECLASSIFY + satellite-extraction sweep, 2026-08-09** (ci tranche): KEEP-NA, valid — re-read all 5
open items end-to-end, verdict unchanged from 2026-08-08. F1 (kill-switch) stays time-gated per its own re-affirmed
operator ruling; the ~4-weeks-of-missing-tags reconciliation is explicitly NOT a backfill by design (deliberately scoped
away from a bulk-write); the F3 success-reporting item's PM-owned half was already extracted
(`ci_satellite_ ao_dispatch_batch5_2026_08_02.md` todo 6, shipped) — the remaining scope is the non-PM-owned dispatch
sites, still genuinely open but not newly bounded; F4 stays the bundled bounded+open-ended pair described above; the
digest-gap item stays a design call. No new facts from today's round-9 cheat sheet (GSM secrets, Slack webhooks) apply
to this doc's content. No `assigned_vm` change.

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:2f1897ab7a615737]: KEEP-NA,
valid — Large audit doc, 5 open checkboxes (matches phase0=5 and my grep). Six prior na-eligibility-audit passes
(2026-07-30, 08-01, 08-06, 08-07, 08-08 round7, 08-09 round-9) all verdicted KEEP-NA valid; independently re-read all 5
items end-to-end rather than rubber-stamping: (1) F1 kill-switch (L439) -- TIME-GATED per an explicit dated 2026-07-28
operator ruling quoted verbatim in the doc ('Standing 2026-07-23 ruling preserved... KEEP TRACKED, DO NOT FIX YET'; gate
= execution-service handling live order flow, not yet true pre-live-trading) -- honored per the never-re-litigate rule;
citation verified real by reading it in place. Tag: DEPENDENCY_BLOCKED.
