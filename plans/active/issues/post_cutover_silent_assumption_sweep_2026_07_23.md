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
context_scope: [/codex/08-workflows/ci-cd-flow.md, scripts/deploy/trading-kill-switch.sh, scripts/cicd/reconcile_release_tags.py, /plans/archive/issues/stale_staging_versions_manifest_2026_07_23.md]
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

- [ ] [INFRA] P1. Implement conventional-commit bump computation + tag mint in `reconcile_release_tags.py`, reusing the
      proven rules. Gate behind an explicit `--mint` flag so the detector stays usable standalone.
- [ ] ⛔ [DOC] P1. **SUPERSEDED 2026-07-25 — moot, not an open operator question.** Option B (this whole sub-steps list)
      was never built; the per-repo `semver-agent` retarget shipped instead (see the ⛔ banner above this section + the
      Resolution checklist's F2 item). There is no reconciler-side message-only-vs-API-diff tradeoff to rule on since
      the reconciler itself does not exist and is not being built. Left unticked per the section banner's own "left
      unticked on purpose" note — not re-tagged `[OPERATOR]` because there is nothing left for an operator to decide
      here.
- [ ] [INFRA] P1. Port the bump-rate circuit breaker to the reconciler (tag-mints/hour), plus a low `--max-creates` for
      the first drain.
- [ ] [INFRA] P2. Batch the manifest write to ONE commit per run (the whole point of B) — verify by confirming a single
      `chore(manifest):` commit after a multi-repo mint.
- [ ] [INFRA] P2. First supervised drain: run with `--dry-run`, eyeball the 22 proposed versions, then mint.
- [ ] [DOC] P2. Update `/codex/08-workflows/ci-cd-flow.md` § "Release tag reconciler" once B ships — it currently
      documents B as _planned_.

## Docs (P2)

`/codex/08-workflows/ci-cd-flow.md` carries a correct dormancy banner but the branch-model narrative below it is stale:
**L75-109** still shows `ldr-to-staging-promote` draining every service repo on a 15-min cron and labels direct-to-main
as "PM only"; **L763**, **L777-786**, **L1183** still describe `quickmerge → staging → main` as canonical.

**Gap that bites on re-entry:** nothing in `codex/` documents that the staging triggers were commented out 2026-07-23
and must be **uncommented** as part of re-entry — that fact lives only in inline YAML comments and
`staging_workflow_shutdown_2026_07_23.md` (a plan, which archives). Per CLAUDE.md's SSOT-direction rule this belongs in
codex, or a future staging re-entry gets a dead pipeline.

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
- [ ] ⛔ [INFRA] P1. **SUPERSEDED 2026-07-25 — DO NOT IMPLEMENT AS WRITTEN.** ~~F2 — restore version minting via OPTION
      B (the PM reconciler), NOT the per-repo agent.~~ **F2's OUTCOME (version minting restored) IS ACHIEVED — by the
      opposite route.** On an operator directive 2026-07-25 the per-repo `semver-agent` was retargeted `staging` →
      `push:[main]` (`unified-trading-pm@0b128a725`, ancestor-verified), fleet-rolled to all 22 `ldr_main`+git-tag
      repos, and proven live (`unified-trading-library` v0.57.0 published to Artifact Registry, the first real publish
      since 2026-06-27). The PM-reconciler minter was **never built** and is architecturally incoherent for git-tag
      repos. See the ⛔ banner on § "Option B" below and
      [/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md](/plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md)
      § Phase 4. Left unticked because the item as _worded_ must not be executed; its retirement is parked for the
      operator.
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
      [/plans/active/issues/main_backmerge_to_ldr_silent_failure_2026_08_02.md](/plans/active/issues/main_backmerge_to_ldr_silent_failure_2026_08_02.md).
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
      instruments-service@7d005520. DONE via `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s "Confirm
      instruments-service's publish path can no longer emit 0.0.0.dev0" todo (full evidence there): the repo's installed
      `publish-package.yml` was stale pre-migration legacy content (no `fetch-depth: 0`, not even the AR-dispatch
      pattern) — replaced with the canonical `scripts/propagation/templates/publish-package.yml` (byte-identical to the
      working `unified-api-contracts`/`unified-trading-library` copies), which now dispatches to PM's
      already-fail-closed receiver. Bad wheel disposition recorded (still present, single 2026-07-03 occurrence, left in
      place per the operator-gated AR-delete rule).
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
      (`--baseline-write`) as each is fixed so the ratchet only ever shrinks.
- [ ] [INFRA] P2. Disable or fix the F4 vacuous crons (`sit-debounce-trigger`, `freeze-deferred-build-replay`,
      `fix-approval-timeout`, `supersede-stale-dep-update-prs`); diagnose `digest-drift-sweep`'s non-convergence (it
      costs real money via `ubuntu-latest` fan-out); make `workspace-quickmerge-validation` fail when it logs a failure.
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

- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
