---
doc_type: issue
title: "ldr_main fleet promoter LABEL-CHECK falsely blocks every multi-commit service-repo LDR→main drain (EXPECTED=latest-commit vs COMPUTED=whole-range asymmetry) → fleet promotion stalled ~1–2.5 days"
created: 2026-06-29
source:
  - .github/workflows/ldr-to-main-promote-fleet.yml
assigned_vm: NA
status: active
priority: P1
summary: "The ldr_main fleet promoter's LABEL-CHECK gate derives EXPECTED from only the newest commit subject but COMPUTED from the max bump across the whole un-promoted range. On the LDR→main drain the unit is the entire accumulated range, so any range with an earlier feat: under a newer fix:/chore: yields EXPECTED=patch vs COMPUTED=minor → false 'mislabeled bump' BLOCK. It mis-fires for nearly every service repo, stalling LDR→main promotion (>60m promotion-lag alerts on 8 repos)."
nature: process
asset_group: cross-asset
stage: [meta]
repos:
  - unified-trading-pm
  - instruments-service
  - market-tick-data-service
  - market-data-processing-service
  - deployment-api
  - deployment-service
  - deployment-ui
  - agent-orchestrator
scope: [engineer, admin]
tags: [cicd, promotion, ldr-main, semver, label-check]
related: []
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-29
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

## Symptom

Slack `#ci-failures` (2026-06-29 11:11): **PROMOTION LAG > 60m — 9 branch-pairs across 8 repos un-propagated**
(`instruments-service LDR→main 92 commits, oldest 3689m`; `market-tick-data-service 53 commits, oldest 3668m`;
`deployment-service 61 commits, oldest 3733m`; `market-data-processing-service`, `deployment-api`, …). **PM is NOT in
the list.** A manual `workflow_dispatch` of `ldr-to-main-promote-fleet.yml` (2026-06-29 ~05:25 and again ~06:1x) reports
**`Promoted (0)`** — nothing drains.

Last time each service repo actually reached `main` (proves the lag is real, not just squash-count inflation):

| Repo | last LDR→main commit on `main` | lag |
|------|-------------------------------|-----|
| market-tick-data-service | 2026-06-27 23:46 | ~37h |
| instruments-service | 2026-06-28 21:36 (stuck `feat(catalogue)` is ~61h old) | ~14h |
| deployment-service | 2026-06-28 20:56 | ~14h |
| market-data-processing-service | 2026-06-28 22:02 | ~13h |
| deployment-api | 2026-06-29 05:24 (drained only by a manual dispatch) | — |

> Note: the branch-health monitor counts `compare ahead_by` (commits), which is **squash-inflated** — every prior
> squash-merge leaves its LDR commits counted forever. The headline commit counts overstate; the *last-main-commit*
> dates above and tree-equality are the honest measure. The content IS genuinely un-drained (trees differ).

## Verified root cause — LABEL-CHECK EXPECTED/COMPUTED asymmetry

`ldr-to-main-promote-fleet.yml` Tier-? LABEL-CHECK step (≈ lines 500–556). Under `ldr_main` the merge-PR head is the
LDR SHA, which never receives the semver-agent's `semver-agent/label-check` status (that fires on `push:[staging]`), so
the gate **re-derives the verdict on the LDR head**. Its two values are computed asymmetrically:

- **`COMPUTED`** (line ~516–534): max bump across **all** subjects in `RANGE_MSGS` (`breaking > minor > patch`),
  refined by the AST differ (`is_breaking → breaking`; else `new_export_count > old_export_count → minor`).
- **`EXPECTED`** (line ~536): bump from **only the latest subject** — `LATEST_SUBJECT=$(printf '%s\n' "$RANGE_MSGS" | head -1)`.

`RANGE_MSGS=git log origin/main..origin/live-defi-rollout --format='%s'` (line ~446) is **newest-first**, so `head -1`
is the single most-recent commit. The block fires when `EXPECTED != COMPUTED` (line ~545).

On the LDR→main drain the "unit of work" is the **entire accumulated range** (dozens of commits over days). Whenever
the newest commit's type is lower than the max type in the range — e.g. a `fix:`/`chore:` landed on top of earlier
`feat:`s — the gate produces `EXPECTED=patch` vs `COMPUTED=minor` and **falsely** declares a "mislabeled bump." Nothing
is actually mislabeled: the range legitimately contains features + a later fix, and the aggregate bump *is* minor.

### Concrete proof — deployment-api (2026-06-29)

- Newest LDR commit (→ `EXPECTED`): `fix(repo-ci): attribute manual tier3 builds via _SERVICE_NAME fallback` → **patch**.
- Un-promoted range contains **10 `feat:` commits** (→ `COMPUTED`): **minor**.
- `patch ≠ minor` → `⛔ LABEL-CHECK BLOCK deployment-api: commit label says 'patch' but the API diff resolves 'minor'`.

Same pattern confirmed for `instruments-service` (`feat(catalogue)…` in range, newer `fix(tradfi)…` on top),
`market-tick-data-service` (`feat:` drains + newer `fix(sports-manifest)…`), `deployment-service` (`feat(infra)/feat(dp-monitor)/feat(monitoring)` + newer `fix(dp-monitor)…`). The verdict even **flipped live**: in the 05:22 dry-run
`market-tick` had `expected=minor → PASS`; by 05:25 a new patch-type commit had landed and it became `expected=patch → BLOCK`. That flip is the asymmetry caught in the act.

Side effect: on a real (non-dry) run the gate **POSTs `state=failure` to `repos/<repo>/statuses/<LDR_HEAD_SHA>` with
context `semver-agent/label-check`** (line ~543) — so it actively stamps a red status on the LDR head.

## Compounding factor — fleet promoter is not on a schedule

`ldr-to-main-promote-fleet.yml` has **0 schedule-event runs ever**; it only runs on manual `workflow_dispatch`
(verified via `gh run list --workflow ldr-to-main-promote-fleet.yml`). PM's own `ldr-to-main-promote.yml` IS scheduled
`*/15` and is healthy (it drained PM PR #710 this morning) — which is why PM is absent from the lag alert. Because the
service promoter only runs sporadically, ranges grow large and mixed over days, which **guarantees** the LABEL-CHECK
asymmetry triggers. The two issues reinforce each other into a hard stall: not-scheduled → big mixed ranges →
label-check false-block → even a manual dispatch promotes 0 → permanent lag.

## Secondary blocks (not the main root cause)

- `deployment-ui`, `agent-orchestrator`: `SIT GATE BLOCK` — per-repo `sit_validated_tree` unset for the current LDR
  tree (fail-closed). Full-workspace SIT is green (2026-06-29 05:26), so once the exact LDR tree is SIT-stamped a tick
  promotes them — **but only if the promoter actually ticks** (see scheduling factor). `agent-orchestrator` has an
  active `fix/sit-exclude-agent-orchestrator-phantom` branch (known SIT phantom under work).
- Orphaned promote PRs `market-tick-data-service#467`, `deployment-service#318` (head `promote/<repo>`, opened
  2026-06-28 22:59) — old branch-naming; the active promoter manages `--head live-defi-rollout` only, so these are
  stale and never merge. Candidate for cleanup.

## NOT the cause (ruled out)

- No CI failure: every affected repo is `quality-gates-v2` green; live Firestore `ci_status` is `MAIN_GREEN`/`FEATURE_GREEN`.
- The earlier `deployment-api held behind unified-trading-library (tier-1)` cockpit alarm was a **stale `ci_status`**
  (UTL stuck `FAILING` in the manifest cache while live-green); the dep-order gate's Firestore overlay already handles
  it and the operator's manual UTL QG re-run (04:41 → MAIN_GREEN 04:48) cleared it. Resolved; not this issue.

## Proposed fix

Derive **`EXPECTED` the same way as `COMPUTED`** — the aggregate max bump across the **whole** `RANGE_MSGS`, not just
`head -1`. Then `EXPECTED` equals `COMPUTED`'s subject-derived part, and the gate only blocks a **genuine** mismatch:
subjects say patch but the AST differ found new exports (minor) or breaking — i.e. an actually-undeclared API bump,
which is the real thing this check exists to catch. This mirrors the aggregate-type derivation already shipped in
`ldr-to-staging-promote.yml::_squash_subject()` (the "derive the AGGREGATE conventional type from the collapsed
commits" fix) — port that semantics here so the two paths never diverge.

Concretely: replace `LATEST_SUBJECT=$(… | head -1)` + single-subject EXPECTED branch with a loop over all of
`RANGE_MSGS` taking the max (`breaking > minor > patch`), identical to the COMPUTED subject loop, *before* the AST
refinement — and compare that subject-aggregate against the AST-refined COMPUTED.

Also (lower priority): once correct, give the service fleet promoter a real `*/15` schedule (or a reliable
`repository_dispatch` source) so ranges don't accumulate for days — this is WS-L consolidated-plan territory
(`cicd_consolidated_remaining_2026_06_24.md`), do not action without operator sign-off.

## Immediate workaround (no code change)

The blocked PRs are `MERGEABLE` (required `quality-gates-v2` is green); only the non-required `semver-agent/label-check`
status is red. An operator can manually merge a specific repo's `live-defi-rollout → main` PR, or push a corrected
`feat:`-typed commit as the newest LDR commit so `EXPECTED` matches `COMPUTED` on the next dispatch.

## Evidence

- `gh run view <fleet-dispatch-run> --log` → `Promoted (0)`; `⛔ LABEL-CHECK BLOCK` for instruments-service /
  market-tick-data-service / deployment-api / deployment-service; `SIT GATE BLOCK` for deployment-ui / agent-orchestrator.
- deployment-api: newest LDR subject `fix(repo-ci): …` (EXPECTED=patch); 10 `feat:` in `compare/main...live-defi-rollout` (COMPUTED=minor).
- `ldr-to-main-promote-fleet.yml` lines ~446 (`RANGE_MSGS` newest-first), ~516–534 (COMPUTED loop), ~536 (EXPECTED `head -1`), ~545 (block on mismatch), ~543 (failure-status POST).
- Slack `#ci-failures` 2026-06-29 11:11 promotion-lag alert (8 repos; PM absent).

## Progress Log

- 2026-06-29: Root-caused and verified. Two manual fleet `workflow_dispatch` runs both returned `Promoted (0)`; the
  immediate `deployment-api`-held-behind-UTL alarm was cleared earlier (UTL re-greened, dep-order overlay). Issue filed.
  No code change made (LABEL-CHECK fix + scheduling are WS-L-adjacent; awaiting operator decision).
