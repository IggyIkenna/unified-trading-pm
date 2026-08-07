---
doc_type: issue
title:
  "semver-agent silently mints ZERO tags fleet-wide when a promote cycle has no exported-API-changing commit — 13 repos
  stalled up to 41 days"
summary: >-
  Investigated the `reconcile-release-tags` stall alert (13 repos not advancing). semver-agent.yml IS running
  successfully on every push to main (not erroring) but resolves BUMP="" and skips almost every time, because (1) the
  LDR→main promote model SQUASHES every commit into one generic `chore(promote): LDR → main (Option-B direct)` message,
  making the message-based feat:/fix:/breaking scan structurally blind, and (2) the AST content differ only catches
  BREAKING surface changes and NET-NEW public exports — a `fix:`-shaped internal change that nets zero new exports is
  invisible to both signals. Root-cause-fixed via a content-based patch-level fallback in the SSOT template, restored a
  dropped `concurrency:` group, and shipped to 21 fleet repos.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    batch-live-reconciliation-service,
    client-reporting-api,
    e2e-testing,
    execution-service,
    fund-administration-service,
    greeks-service,
    ibkr-gateway-infra,
    instruments-service,
    ml-service,
    strategy-service,
    system-integration-tests,
    trading-agent-service,
    unified-trading-api,
    unified-api-contracts,
    unified-trading-library,
    alerting-service,
    deployment-api,
    deployment-service,
    features-service,
    market-data-processing-service,
    agent-orchestrator,
    market-tick-data-service,
  ]
scope: [engineer]
tags: [ci-cd, semver-agent, release-tags, squash-promote, fleet-template]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/fleet_promoter_glue_runner_stall_2026_08_06.md,
    /plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md,
    /plans/archive/issues/semver_version_bump_skip_ci_promotion_block_2026_06_09.md,
  ]
created: 2026-08-07
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
assigned_role: devops
drift_direction: advance-code
depends_on: []
source: "reconcile-release-tags stall alert (13 repos), investigated 2026-08-07"
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    scripts/workflow-templates/semver-agent.yml.tmpl,
    scripts/cicd/reconcile_release_tags.py,
    scripts/cicd/detect_breaking_change.py,
    scripts/cicd/promote_provenance_range.py,
  ]
---

# semver-agent silently no-ops on squash-only promote cycles — 13 repos stalled up to 41 days

## The alert

`reconcile-release-tags` (fires every 30 min) reported 13 repos with unreleased commits on `main` and stale newest tags:
`batch-live-reconciliation-service` (97 commits, 41.0d), `client-reporting-api` (97, 41.0d),
`fund-administration-service` (85, 41.0d), `greeks-service` (94, 41.3d), `trading-agent-service` (75, 12.5d — note:
alert text said 12.5d but the repo's own dry-run later showed 41.1d, i.e. the ORIGINAL alert had a partly-stale
snapshot; the numbers in `## Root cause` below are the live re-measured ones), `e2e-testing` (55, 12.5d),
`ibkr-gateway-infra` (22, 12.5d), `system-integration-tests` (43, 12.5d), `ml-service` (54, 11.9d), `strategy-service`
(19, 7.0d), `unified-trading-api` (14, 7.0d), `execution-service` (14, 6.0d), `instruments-service` (10, 3.5d).

## Root cause (confirmed via live run logs, not theory)

Pulled `gh run view --log` for the most recent `semver-agent.yml` run on `batch-live-reconciliation-service` (run
`31165314543`, `conclusion=success`) and `instruments-service` (run `31170013899`, `conclusion=success`). Both show the
SAME pattern:

1. **`Commits to analyze`** (the `BASELINE_SHA..HEAD` range on `main`) is a list of
   `chore(promote): LDR → main (Option-B direct)` commits — every single one, no exceptions (97/97 for
   batch-live-reconciliation-service, 10/10 for instruments-service). `git log -1 --format=%B` on these confirms they
   are genuine single-parent SQUASH commits ("LDR→main fleet bot — squash (LDR is the backmerge sink; not rebaseable)"),
   carrying a `Promoted-From-LDR: <sha>` trailer but NOT the original conventional-commit messages from LDR.
2. The message-based `feat:`/`fix:`/`breaking` regex scan (`grep -qE "^[a-f0-9]+ feat(...)?:"` etc.) therefore matches
   **zero** commits, every time, structurally — not a parsing bug, the signal genuinely isn't there anymore.
3. The AST content differ (`scripts/cicd/detect_breaking_change.py`) correctly ran the cumulative `DIFF_BASE..HEAD` diff
   (spanning the FULL window since the last release, not just one squash commit) and reported
   `old_export_count == new_export_count` for both repos (13→13 for batch-live-reconciliation-service, 63→63 for
   instruments-service) — `is_breaking: false`. This IS correct: neither window added or removed a public export.
4. With no message-based signal and no export-count delta, `BUMP` stays `""` → `skip=true` → "No feat:/fix:/breaking
   commits or API changes found. Skipping version bump." — **every single run, forever**, regardless of how much real
   work landed.
5. **This is not a false negative on inert commits.** Diffed batch-live-reconciliation-service's `v0.49.0..main` file
   list directly: `batch_live_reconciliation_service/api/resolution_api.py` (+102 lines), `.../config.py` (+39),
   `.../stages/stage0_manifest_reason_check.py`, `.../stages/stage5_results_writer.py` (brand new, +21), plus 190 new
   lines across `tests/unit/test_resolution_api.py` (new file) and `tests/unit/test_stages.py`. Real, substantial
   feature/fix work — silently trapped for 41 days.

The already-documented semver rules (see the template's own header) say `fix: / internal change → PATCH bump` — but that
rule has been **unreachable** since the LDR→main model went squash-only: there is no content-based signal that
implements it. The bug isn't in the differ or the message scanner individually — each does exactly what it's supposed to
— it's that **nothing implements the "patch" tier** under the squash-promote model.

## Timing cross-reference (why 4 different staleness numbers, one root cause)

- **41d cluster** (`batch-live-reconciliation-service`, `client-reporting-api`, `fund-administration-service`,
  `greeks-service`, `trading-agent-service`): `batch-live-reconciliation-service`'s `v0.49.0` tag points at `441cffb1` —
  the FIRST `chore(promote): LDR → main (Option-B direct)` squash commit ever created for this repo (2026-06-27). Per
  the semver-agent.yml.tmpl's own header comment, semver was triggered on `push:[staging]` until the staging drain
  stopped 2026-06-28, then went **completely dead fleet-wide** (zero triggers at all, not even a skip) until the
  retarget to `push:[main]` landed 2026-07-25 (`cicd_mvp_ldr_to_main_pipeline` Phase 4). So the 41d-cluster repos' LAST
  bump happened via the old pre-dormancy staging trigger one day before staging died; from 2026-06-28 to 2026-07-25
  there were literally no runs; from 2026-07-25 onward runs resumed but hit this bug on every single promote cycle.
- **12.5d / 7d / 6d / 3.5d clusters**: these repos' last bump landed AFTER the 2026-07-25 retarget (the retarget itself
  worked — main-triggered runs do fire and do run to completion), so their staleness reflects how long ago their most
  recent promote cycle happened to contain a commit that tripped the differ's breaking/net-new-export signal by chance,
  not a separate bug. Same root cause, different exposure timing.

## A separate, already-tracked, self-resolved anomaly (NOT this bug)

While spot-checking `instruments-service`, found its newest tag by CREATION DATE was `v0.1.0` (2026-08-05, lower than
the concurrent `v0.98.0`) and **not an ancestor of `origin/main`** — a spurious tag minted when a semver-agent run
computed `BASELINE=0.0.0` (i.e. `git describe --tags` found no reachable `v*` tag at all). Root cause: the
2026-08-05T11:24:53Z security-driven history rewrite disconnected `instruments-service`'s (and 4 other repos')
pre-rewrite tag history from post-rewrite `main` for a window, corrupting `promote_provenance_range.py`'s marker
resolution and causing a churn of closed/reopened promote PRs — already fully diagnosed, root-cause-fixed, and
live-verified in `/plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`
(instruments-service's own thread there is marked fully resolved, main tip `51f45049…`, matching what this repo's `main`
shows today). Not re-investigated or re-fixed here — cross-referenced only. The stray `v0.1.0` tag itself is still
sitting in the tag namespace (unreachable, harmless — `git describe` on the current, correct `main` resolves `v0.98.0`
fine and ignores it); left alone per the delete-safety protocol (not this task's mandate, and tag deletion needs its own
reversibility check).

## Fix

Edited the SSOT template `scripts/workflow-templates/semver-agent.yml.tmpl` (used by
`rollout-workflow-templates.sh --template semver-agent.yml`, the fleet-wide rollout mechanism):

1. **Patch-level fallback for squash-only promote commits** — when `BUMP` is still unset after the message scan AND the
   content differ (no breaking, no net-new export), check whether `CHANGED_FILES` (already computed for the differ,
   spanning the full `DIFF_BASE..HEAD` window) includes at least one file under `SOURCE_DIR/` (the repo's own package).
   If so, default to `patch` — directly implementing the already-documented "fix: / internal change → PATCH bump" rule
   via a content-based signal instead of the now-dead message-based one. Scoped to `SOURCE_DIR/` changes only, so a
   squash commit touching ONLY CI/workflow/docs/lockfile files correctly stays un-bumped (matching "chore:/docs: → no
   bump").
2. **Restored a dropped `concurrency:` group** (`group: ${{ github.workflow }}-${{ github.ref }}`,
   `cancel-in-progress: true`) — present in the pre-retarget staging-triggered version, silently dropped when the
   workflow was retargeted to `main` on 2026-07-25. Without it, the `*/5` LDR→main promote-fleet cadence can fire
   several `push:[main]` events in quick succession, and overlapping semver-agent runs can each read a stale
   `git describe --tags` baseline before a sibling run's tag push lands, racing the mint. Restoring it is a targeted
   hardening, independent of the patch-fallback fix.

Both changes are purely additive (no lines removed) — verified via `bash -n` on the extracted compute-step script and
`actionlint` (zero structural/schema errors, only 2 pre-existing shellcheck style nits unrelated to this diff).

## Shipped (2026-08-07)

Rendered via `bash scripts/workflow-templates/rollout-workflow-templates.sh --template semver-agent.yml`, then
`quality-gates.sh --no-fix` (all green) + `quickmerge.sh --agent --files .github/workflows/semver-agent.yml` per repo —
landed on `live-defi-rollout` (LDR), pending the fleet promoter to reach `main`:

- [x] ✅ [DEVOPS] P1. `unified-api-contracts@451a49758` (T0 dep, shipped first)
- [x] ✅ [DEVOPS] P1. `unified-trading-library@243847f38` (T0 dep, shipped second)
- [x] ✅ [DEVOPS] P1. `batch-live-reconciliation-service@ea30608d6` (41d cluster)
- [x] ✅ [DEVOPS] P1. `instruments-service@c7af8834a` (3.5d cluster)
- [x] ✅ [DEVOPS] P1. `execution-service@67ecc357d` (6d cluster)
- [x] ✅ [DEVOPS] P1. `client-reporting-api@f07231bc0`
- [x] ✅ [DEVOPS] P1. `fund-administration-service@adaf5e308`
- [x] ✅ [DEVOPS] P1. `greeks-service@036cea885`
- [x] ✅ [DEVOPS] P1. `ibkr-gateway-infra@4d8eccc3b`
- [x] ✅ [DEVOPS] P1. `ml-service@23f735621`
- [x] ✅ [DEVOPS] P1. `strategy-service@a26501a07`
- [x] ✅ [DEVOPS] P1. `trading-agent-service@65d85f3f9`
- [x] ✅ [DEVOPS] P1. `unified-trading-api@6e6c114d7`
- [x] ✅ [DEVOPS] P1. `e2e-testing@025805335`
- [x] ✅ [DEVOPS] P1. `system-integration-tests@0c72324ed` (needed alerting-service/deployment-api/deployment-service/
      market-data-processing-service/features-service shipped first — its own dep closure)
- [x] ✅ [DEVOPS] P2. `alerting-service@0057cfff2`
- [x] ✅ [DEVOPS] P2. `deployment-service@7e1aa270f`
- [x] ✅ [DEVOPS] P2. `deployment-api@3eb8e0ece`
- [x] ✅ [DEVOPS] P2. `market-data-processing-service@a1b52e513`
- [x] ✅ [DEVOPS] P2. `features-service@02f611c8f`
- [x] ✅ [DEVOPS] P2. `agent-orchestrator@de1408664` (staging-first promotion model, not ldr_main — different drain
      path, same fix content)

All 13 originally-alerted repos are covered. 8 additional fleet repos consuming the same template were shipped
proactively (transitive deps of the above, or repos that would hit the identical bug on their next squash-only promote
cycle).

**Not shipped (follow-ups below)**:

- `market-tick-data-service` — blocked by a PRE-EXISTING, unrelated failing test
  (`tests/unit/scripts/test_rewrite_tradfi_chain_bundle_content_id_2026_07_25.py::test_derive_future_id_from_raw_databento_symbol`)
  that fails `quality-gates.sh` and therefore blocks quickmerge for ANY file in this repo, not just mine. Already
  tracked (referenced from `tradfi_manifest_content_recovery_completion_2026_07_24.md` /
  `mtds_migrate_executor_progress_checkpoint_gap_2026_08_04.md`) — not re-investigated here, out of scope.
- `unified-trading-system-ui`, `deployment-ui` — lower priority (not in the original 13; `deployment-ui` has no
  `pyproject.toml` at all, so this Python-oriented template is a permanent no-op there anyway;
  `unified-trading-system-ui` has a `pyproject.toml` but no `v*` tags found, unclear if it uses this versioning path at
  all) — deferred, not investigated further.
- `unified-trading-ci` — the rollout script would CREATE a brand-new `semver-agent.yml` here (repo has no
  `pyproject.toml`, essentially just a README). Deliberately excluded — out of scope for this fix, a separate decision
  about whether this repo should have semver-agent at all.

## Verification — IN PROGRESS, blocked by an unrelated live incident

- [ ] [DEVOPS] P1. Confirm a NEW tag mints on `main` for at least 2 repos in different staleness clusters
      (batch-live-reconciliation-service=41d, instruments-service=3.5d) once the fix reaches `main`. **Blocked**: the
      LDR→main fleet promoter (`ldr-to-main-promote-fleet.yml`, the ONLY path code reaches `main` under the `ldr_main`
      promotion model) has 0 self-hosted `glue` runners registered as of this writing
      (`gh api repos/IggyIkenna/unified-trading-pm/actions/runners` → `{"total_count": 0}`), preceded by roughly an hour
      of consecutive `cancelled` promote-fleet runs. This is a recurrence of the ALREADY-TRACKED
      `/plans/active/issues/fleet_promoter_glue_runner_stall_2026_08_06.md` (noted there, not re-investigated here — out
      of scope for this task). All 21 repos' fixes are correctly landed on LDR and will promote automatically once the
      runner pool recovers (the doc's history shows this class of incident usually self-heals within minutes to hours).
- [ ] [DEVOPS] P1. Once promoted, re-run `python3 scripts/cicd/reconcile_release_tags.py --dry-run` and confirm the
      stall count drops from 13 (baseline re-measured 2026-08-07, matches the original alert almost exactly).
- [ ] [DEVOPS] P2. Ship the fix to `market-tick-data-service` once its unrelated pre-existing test failure is fixed
      (tracked in the docs cited above — this todo is just the reminder to circle back, not a duplicate of that fix).

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — promoter/semver-agent gate set, LDR→main model
- `scripts/workflow-templates/semver-agent.yml.tmpl` — the fix itself

## Progress Log

- **2026-08-07**: Filed after investigating the 13-repo `reconcile-release-tags` stall alert. Root-caused via live
  `gh run view --log` evidence (not theory) on 2 repos in different staleness clusters. Fixed the SSOT template
  (patch-level content-based fallback + restored concurrency group), rolled out fleet-wide, shipped to LDR for 21 repos
  via `quickmerge --agent`. Verification (tag-mint confirmation) blocked by a live recurrence of the already-tracked
  glue-runner-pool depletion issue — see `fleet_promoter_glue_runner_stall_2026_08_06.md` Progress Log entry added the
  same session. Will update this doc's Progress Log once the fleet promoter recovers and the live tag-mint verification
  completes.
