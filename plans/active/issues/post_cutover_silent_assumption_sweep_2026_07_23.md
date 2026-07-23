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
asset_group: [cross-cutting]
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
  - staging_workflow_shutdown_2026_07_23.md
  - stale_staging_versions_manifest_2026_07_23.md
  - qg_sentinel_environment_blind_2026_07_23.md
  - github_actions_ci_cost_reduction_2026_07_15.md
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

## Docs (P2)

`codex/08-workflows/ci-cd-flow.md` carries a correct dormancy banner but the branch-model narrative below it is stale:
**L75-109** still shows `ldr-to-staging-promote` draining every service repo on a 15-min cron and labels direct-to-main
as "PM only"; **L763**, **L777-786**, **L1183** still describe `quickmerge → staging → main` as canonical.

**Gap that bites on re-entry:** nothing in `codex/` documents that the staging triggers were commented out 2026-07-23
and must be **uncommented** as part of re-entry — that fact lives only in inline YAML comments and
`staging_workflow_shutdown_2026_07_23.md` (a plan, which archives). Per CLAUDE.md's SSOT-direction rule this belongs in
codex, or a future staging re-entry gets a dead pipeline.

---

## Resolution checklist

- [ ] [OPERATOR] P0. **Rule on F1 (kill-switch).** Either implement the `halt-order-flow`/`resume-order-flow` listener
      in execution-service, or delete the kill-switch call path — but do not leave a safety mechanism that reports
      success while doing nothing. Needs a human call because it touches live trading behaviour.
- [ ] [INFRA] P1. **Fix F2**: make `reconcile_release_tags.py` read the version from the hatch-vcs source (or from the
      built dist / `hatch version`) instead of a static `version =` line. Then reconcile the ~4 weeks of missing tags.
      Verify by confirming new tags appear and `publish-package` runs again.
- [ ] [INFRA] P1. **Re-assess `stale_staging_versions_manifest_2026_07_23.md` in light of F2 before implementing its
      fix** — its premise is inverted (see the ⚠ box above). Do not action the two independently.
- [ ] [INFRA] P1. **Make dispatch delivery observable.** A 204 cannot distinguish "delivered" from "nobody subscribed",
      so runtime handling cannot fix this class. Add a STATIC check (CI or QG) that every dispatched `event_type` has a
      listener for that type in the resolved target repo — the same check that would have caught F1 and both escalation
      bugs. Fix the unconditional `&& echo "...dispatched"` success reporting at the sites in F3.
- [ ] [INFRA] P2. Disable or fix the F4 vacuous crons (`sit-debounce-trigger`, `freeze-deferred-build-replay`,
      `fix-approval-timeout`, `supersede-stale-dep-update-prs`); diagnose `digest-drift-sweep`'s non-convergence (it
      costs real money via `ubuntu-latest` fan-out); make `workspace-quickmerge-validation` fail when it logs a failure.
- [ ] [INFRA] P2. Fix the F5 readers so an empty input renders as **"unknown"/"not applicable", never GREEN** — starting
      with the `deployed_versions` shape mismatch and the `stuck_in_sit` / promotion-blocked panels. Correct the false
      comment at `ldr-to-main-promote-fleet.yml:422-434`.
- [ ] [INFRA] P2. Close the `sit_validated_workspace_digest` written-but-unread gap, or document why it is safe to drop.
- [ ] [DOC] P2. Update `codex/08-workflows/ci-cd-flow.md` (L75-109, L763, L777-786, L1183) to the current LDR→main
      model, and add the staging re-entry procedure INCLUDING "uncomment the disabled triggers" to codex.
- [ ] [REVIEW] P3. Guard the latent repeat: `agent-runner.yml:91` / `sit-gate.yml:357` self-dispatch is safe only by
      file placement. Either hardcode the PM target or add a rollout guard.
