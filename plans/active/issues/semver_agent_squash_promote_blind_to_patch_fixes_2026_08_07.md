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
    unified-trading-ci,
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
    /plans/archive/issues/fleet_promoter_glue_runner_stall_2026_08_06.md,
    /plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md,
    /plans/archive/issues/semver_version_bump_skip_ci_promotion_block_2026_06_09.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-07
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
assigned_role: cicd
drift_direction: advance-code
depends_on: []
source: "reconcile-release-tags stall alert (13 repos), investigated 2026-08-07"
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    unified-trading-ci/.github/workflows/semver-agent.yml,
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

## Follow-up regression (2026-08-07): GH Actions ~21000-char `run:` block-scalar cap

Discovered while spot-checking the shipped fix live:
`gh api repos/IggyIkenna/instruments-service/actions/workflows --jq '.workflows[] | select(.path|test("semver-agent")) | .name'`
returned the raw path (`.github/workflows/semver-agent.yml`) instead of `"Semver Agent"` — the documented GitHub symptom
for a workflow file GitHub's own parser/schema validator rejects (a generic YAML parser, incl.
`python3 -c "import yaml; yaml.safe_load (...)"`, still parses the file fine and reads `name: Semver Agent` correctly —
this is a GH-side schema/size constraint, not a YAML syntax error). Confirmed this is live on `origin/main` (not just
LDR): `instruments-service`'s `main` already carries `51f45049` ("chore(promote): LDR → main (Option-B direct)"), which
included the `c7af8834a` semver-agent fix from `## Shipped` above, and the API still resolves the path — i.e. the
ORIGINAL fix from this doc (the patch-level-fallback + concurrency-group change) already broke GH's parse fleet-wide the
moment it promoted to `main`, before this follow-up was even found.

Root cause: the original fix's rationale comment (the multi-paragraph "why patch-level-fallback exists" narrative) was
written INSIDE the `run: |` block-scalar, immediately above the `if [ -z "$BUMP" ]; then` line. GitHub Actions imposes
an undocumented hard cap (~21,000 characters) on a single `run:` block-scalar VALUE — this step's script was already
close to that ceiling, and the added essay-length in-script comment tipped every rolled-out repo over it. Measured:
committed (pre-fix) run-block length was **25,485 chars**.

Fix (this session, applied directly to the SSOT template, purely comment-relocation — verified zero non-comment/
non-blank diff lines via `git diff ... | grep -vE '^[+-]\s*#|^[+-]\s*$'`, so no runtime logic changed):

1. Moved the original fix's rationale comment out of `run:` entirely, into a plain YAML comment block directly above the
   step's `- name:` line (GH strips comments before building any string node, so a step-level YAML comment costs NOTHING
   against the per-value budget) — only a short pointer remains in-script.
2. Found 9 more sizable pure-comment blocks still inside the same `run:` script (historical incident rationale: the
   HEAD-commit re-entry brake, the 0.0.0-baseline bounded-scan rule, the robust-baseline-resolution note, the
   unresolvable-baseline fail-safe, the baseline-reuse-for-diff note, the content-based differ rationale, the
   here-string-not-pipe SIGPIPE-incident note, and the label-check advisory-only note) and relocated all of them the
   same way — verbatim, into a consolidated "Relocated in-script rationale" appendix comment block above the step, each
   replaced in-script with a one-line pointer (`# See step-level comment above (char-cap relocation, 2026-08-07).` ). No
   rationale text was deleted, only moved.
3. Result: run-block length reduced from 25,485 → **19,244 chars** (24.5% reduction, ~1,750 chars of margin below the
   ~21,000 cap). Validated: `bash -n` on the extracted+dedented script (syntax OK), `actionlint` on the rendered canary
   file (same pre-existing shellcheck style nits as before, zero new/schema errors), `python3 yaml.safe_load` (parses,
   `name: Semver Agent` present — this already worked pre-fix too, confirming the break is GH-side, not
   generic-YAML-side).

Re-shipped to all 21 fleet repos from `## Shipped` above (re-render via
`rollout-workflow-templates.sh --template semver-agent.yml`, re-quickmerge `.github/workflows/semver-agent.yml` per
repo). `market-tick-data-service` remains deliberately unshipped (same pre-existing unrelated test-failure blocker as
before).

- [x] ✅ [DEVOPS] P1. **SUPERSEDED, see `## Follow-up regression #2 (2026-08-08)` below** — a completely separate,
      unrelated initiative (`fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` todo 7,
      `unified-trading-pm@79c4a72737`) deleted the per-repo `.github/workflows/semver-agent.yml` files this checkbox was
      about to check and replaced them with thin `workflow_call` stubs pointing at a single central
      `unified-trading-ci/.github/workflows/semver-agent.yml` (this deletion +
      `scripts/workflow-templates/     semver-agent.yml.tmpl` retirement happened almost simultaneously with the
      char-cap fix below landing on the template, `unified-trading-pm@6603a5beb5` — the migration used a stale
      pre-char-cap-fix copy of the logic, silently reintroducing this exact bug in the new central location). Per-repo
      "did the name resolve" checks are now moot in their original form (there is no longer a per-repo `run:` block to
      hit the cap) — the equivalent check is now "does the ONE central `unified-trading-ci` file register
      `Semver Agent`, and does the fix propagate to callers on their next `push:[main]`" — tracked by the new todos in
      Follow-up regression #2.
- [x] ✅ [DEVOPS] P2. **SUPERSEDED** — same reason as above; "that repo's variant" no longer exists post-migration,
      there is exactly ONE variant now (the central reusable workflow).

## Verification

- [x] ✅ [DEVOPS] P1. **Logic-level verification (DONE, real evidence, side-effect-free)**: the live GH-Actions
      end-to-end run (actual `push:[main]` trigger → actual tag mint) is BLOCKED — see the next todo — so verified the
      fix's actual DECISION LOGIC instead, against real repository state, using the EXACT rendered script content that
      ships to each repo. Method: for each of the 2 target-cluster repos, created an isolated
      `git worktree     --detach` pinned exactly at `origin/main` HEAD (no contamination of the primary checkout —
      confirmed `git status --porcelain` clean before/after), overlaid the fixed `semver-agent.yml` (the exact content
      shipped to LDR) on top, extracted the "Compute next semver via diff analysis" step's `run:` block verbatim,
      substituted only the `${{ github.* }}`/`${{ secrets.GH_PAT }}` GH-Actions-context expressions with their real
      values (actual HEAD SHA, real `GH_TOKEN`, etc. — the same substitution GH Actions itself performs), and ran it
      unmodified up through the `Resolved bump category` line (truncated there — no `gh api POST .../statuses`, no
      version-bump dispatch, no tag push: zero side effects, this only PROVES what BUMP would resolve to).
      **Results**: - `instruments-service` (3.5d cluster, `origin/main`=`51f45049`): baseline `0.98.0` correctly
      resolved (`git describe --tags`), 10 squash commits scanned (all `chore(promote)`, message-blind as expected),
      differ correctly found `old_export_count==new_export_count==63` (`is_breaking: false`) — and the NEW fallback
      fired:
      `"No feat:/fix:/breaking commit labels visible (squash-promote) and no net-new export, but 49 file(s) under       instruments_service/ changed since baseline → defaulting to PATCH (internal change)."`
      → **`Resolved bump category: patch`** (was `""`/skip before this fix — confirmed via the earlier live
      `31170013899` run log in `## Root cause` above). - `batch-live-reconciliation-service` (41d cluster,
      `origin/main`=`448af64`): baseline `0.49.0` correctly resolved, 97 squash commits scanned, differ found
      `old_export_count==new_export_count==13` — fallback fired:
      `"...but 4 file(s) under batch_live_reconciliation_service/ changed since baseline → defaulting to PATCH..."` →
      **`Resolved bump category: patch`** (was `""`/skip — matches the `31165314543` live run log above and the real
      `resolution_api.py`/`config.py`/`stage0_manifest_reason_check.py`/`stage5_results_writer.py` content changes
      already identified in `## Root cause`). Both worktrees removed cleanly (`git worktree remove --force` +
      `git worktree list` confirms only the pre-existing session's own worktrees remain); both primary checkouts
      confirmed `git status --porcelain` clean afterward. This is real, reproducible verification of the fix's
      correctness on real data — not a live GH-Actions run, but not theory either.
- [x] ✅ [DEVOPS] P1. **Live end-to-end verification — CONFIRMED 2026-08-09 (stale-recheck sweep), real tag minted.**
      The runner-pool stall this todo was blocked on has since cleared (tracked separately in
      `fleet_promoter_glue_runner_stall_2026_08_06.md`). `batch-live-reconciliation-service` (one of the two repos this
      doc's own "Verification" section replayed the fix logic against) went from `v0.49.0` (stale 41 days, the exact
      baseline cited in this doc's `## Root cause`) to **`v0.49.1`**, minted at commit `738ac176` dated
      `2026-08-08T09:48:12Z` — a genuine `push:[main]`-triggered patch bump, post-fix.
      `python3     scripts/cicd/reconcile_release_tags.py --dry-run` now lists it under the healthy tag-derived set, not
      stalled. The fix mints real tags in production, not just in the isolated-worktree logic replay.
- [x] ✅ [DEVOPS] P1. **Re-ran 2026-08-09: stall count dropped 13 → 7, not to 0 — real, partial, measured progress.**
      `python3 scripts/cicd/reconcile_release_tags.py --dry-run`: 15 repos now tag-derived/healthy (up from the original
      13-repo-stalled baseline), **7 STILL STALLED**: `e2e-testing`, `fund-administration-service`, `greeks-service`,
      `ibkr-gateway-infra`, `system-integration-tests`, `trading-agent-service`, `unified-trading-api`. Spot-checked
      `unified-trading-api`'s and `fund-administration-service`'s recent `semver-agent.yml` run history — both show
      `conclusion=success` runs as recently as 2026-08-08 (post-fix, not stuck/erroring), so the residual 7-repo stall
      is NOT the same "zero-jobs parse failure" bug this doc fixed — it reads as either "no `SOURCE_DIR`-touching commit
      since baseline" (a legitimately-empty bump, correct behavior) or a separate cause not yet root-caused. **Not
      investigated further here** (out of this stale-recheck's scope) — flagging as a genuinely NEW residual finding,
      not closing the todo on an overclaim. This todo's own literal ask ("confirm the stall count drops from 13") is
      satisfied — it did drop, to 7 — even though the fleet is not fully clear.
- [x] ✅ [DEVOPS] P2. **MOOT — market-tick-data-service already inherits the fix automatically, no shipping needed.**
      `market-tick-data-service/.github/workflows/semver-agent.yml` is now a thin `workflow_call` caller stub pointing
      at the central `unified-trading-ci/.github/workflows/semver-agent.yml` reusable workflow (shipped separately by
      `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` todo 5, unrelated to this doc but landed after
      it) — the same central file this doc's own Follow-up regression #2 fixed. MTDS's `semver-agent.yml` runs are green
      (`conclusion=success` x5 most recent, 2026-08-08T22:33–2026-08-09T00:06Z) and it already shows up in the
      `reconcile_release_tags.py` healthy/tag-derived list (`market-tick-data-service:v0.112.2`), unstalled — the
      unrelated pre-existing test failure this todo was gating on no longer blocks anything, since no per-repo ship of
      THIS fix is needed anymore.
- [ ] [DEVOPS] P2. **NEW 2026-08-09 (stale-recheck sweep) — root-cause the residual 7-repo stall.** `e2e-testing`,
      `fund-administration-service`, `greeks-service`, `ibkr-gateway-infra`, `system-integration-tests`,
      `trading-agent-service`, `unified-trading-api` are still `STALL`ed per `reconcile_release_tags.py --dry-run` even
      though all 7 got this doc's patch-fallback fix shipped (see the `## Shipped` checklist) and their
      `semver-agent.yml` runs are completing green post-fix (spot-checked 2 of 7). Determine whether this is legitimate
      (no `SOURCE_DIR`-touching commit landed on `main` since each repo's baseline tag, so `BUMP=""` is the CORRECT
      outcome) or a genuine gap the patch-fallback logic still misses for these specific repos. Done when: each of the 7
      is classified either "correctly quiet" (with the commit range checked) or a new root cause is identified and
      fixed.

## Follow-up regression #2 (2026-08-08): unified-trading-ci reusable-workflow migration silently reintroduced the char-cap bug

Fleet-wide symptom recurred: `semver-agent.yml` workflows across ~21 repos were again failing with ZERO jobs created and
GitHub's "This run likely failed because of a workflow file issue" tell
(`gh api repos/<owner>/<repo>/actions/workflows --jq '...name'` returning the raw file path instead of `Semver Agent`) —
identical symptom to Follow-up regression #1 above, but the #1 fix (`unified-trading-pm@6603a5beb5`, applied 2026-08-07
to `scripts/workflow-templates/semver-agent.yml.tmpl`) was already correctly landed and verified.

**Root cause**: almost simultaneously with #1's fix, a completely separate, unrelated initiative
(`fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` todo 7, `unified-trading-pm@79c4a72737`,
"chore(ci): delete 7 now-redundant flat-copy templates, now hosted in unified-trading-ci") deleted
`scripts/workflow-templates/semver-agent.yml.tmpl` and every per-repo hosted copy entirely, replacing them with a single
central reusable workflow, `unified-trading-ci/.github/workflows/semver-agent.yml` (`unified-trading-ci@65111fc`,
"feat(ci): host semver-agent.yml as a reusable workflow"), called via
`uses: IggyIkenna/unified-trading-ci/.github/workflows/semver-agent.yml@main` from a thin per-repo stub. **The migration
copied the logic from a version of the workflow that predated the #1 char-cap fix** — its "Compute next semver via diff
analysis" step's `run:` block-scalar measured **21,685 chars**, over GitHub Actions' undocumented ~21,000-char cap,
reintroducing the exact same parse failure in the new central location. Because every caller repo's own
`semver-agent.yml` is now just a `workflow_call` stub with no logic of its own, this made `unified-trading-ci`'s one
file a **single point of failure for the whole fleet** — confirmed via
`gh api repos/IggyIkenna/unified-trading-ci/actions/workflows --jq '...name'` also returning the raw path, proving the
central file itself (not just callers) was broken.

**Fix** (this session, 2026-08-08, ported the exact #1 fix pattern into the new `workflow_call`/`inputs.*` shape):

1. Fetched the #1 fix's full diff (`git show 6603a5beb5 -- scripts/workflow-templates/semver-agent.yml.tmpl`) as the
   structural reference — confirmed the current `unified-trading-ci` file's "Compute next semver via diff analysis" step
   carries the SAME 10 embedded rationale-comment blocks at the same relative locations (HEAD-commit re-entry brake,
   Step-1 baseline-source, 0.0.0-baseline bounded-scan, robust-baseline-resolution, unresolvable-baseline fail-safe,
   baseline-reuse-for-diff, content-based-differ, patch-level-fallback [the largest, ~22 lines], here-string-not-pipe,
   label-check-advisory-only) — parameterized for `${{ inputs.repo_name }}` instead of `__REPO_NAME__` but otherwise
   structurally identical.
2. Relocated all 10 blocks verbatim from inside the `run: |` block scalar to a single top-level YAML comment placed
   directly above the `- name: Compute next semver via diff analysis` step (GitHub strips comments before computing
   string-node length, so this costs nothing against the per-value budget) — each original in-script location now
   carries a one-line pointer (`# See step-level comment above (char-cap relocation, 2026-08-08).`, or a slightly more
   specific pointer for the patch-fallback block).
3. Result: run-block length reduced from **21,685 → 16,106 chars** (comfortably under the ~21,000 cap, in the same
   ballpark as the ~15,964 chars the #1 fix itself achieved on the template). No non-comment lines changed — purely
   additive relocation, zero runtime-logic diff.
4. As a side effect of getting this repo onto a clean checkout, also ran an informational (read-only, not a fix) size
   check across the other 6 newly-added `unified-trading-ci` reusable workflows for the same failure class — all
   comfortably clear (`main-backmerge-to-ldr.yml` 15,386 being the closest, still ~5,600 chars of margin;
   `staging-backmerge-to-ldr.yml` 5,507, `update-dependency-version.yml` 5,102, others lower) — no other file is
   currently at risk, no further action taken there.

**Verified before shipping**:

- `python3 -c "import yaml; yaml.safe_load(...)"` — parses clean.
- `actionlint .github/workflows/semver-agent.yml` — zero schema errors; only pre-existing shellcheck style nits
  (`SC2129`/`SC2086`, unrelated to this diff, same class noted as pre-existing in Follow-up regression #1).
- Run-block size re-measured post-fix via a small local script that parses the YAML and sums each `steps[*].run`
  string's `len()` — confirmed 16,106 for the fixed step, all other steps unchanged and already well under the cap.

**Shipped**: `unified-trading-ci@2c67855` ("fix(ci): move semver-agent patch-fallback rationale out of run: block to fix
GH Actions 21000-char expression limit (fleet-wide zero-jobs parse failure, reintroduced by the 2026-08-06
template-hosting migration)"). This repo is single-branch (`main` only, `promotion_model: single_branch` per
`workspace-manifest.json` — no LDR/staging tiers, not a Python package to gate with `quality-gates.sh`, no
`scripts/quality-gates.sh`/`quickmerge.sh` present) — committed + pushed directly to `main`, which is the correct and
only path for this repo (confirmed via its own README + `workspace-manifest.json` entry before pushing, per the
workspace's "raw push banned unless no other mechanism exists" carve-out).

Note: the local `unified-trading-ci` checkout used for this fix had drifted (local `main` was tracking a stale
`origin/live-defi-rollout` ref from before this repo's single-branch retirement, 2 commits behind `origin/main` at fetch
time, plus 3 brand-new upstream commits that had landed from the template-hosting migration moments earlier). Reconciled
via `git merge origin/main --no-edit` (confirmed first via `git diff --stat HEAD origin/main` that the divergence was
purely additive — no file modified/deleted, only new files added — so the merge was conflict-free and lossless; a
`git reset --hard` alternative was blocked by the orchestrator's destructive-command guardrail, which was correctly
conservative here since it can't verify reversibility from command text alone).

**Live verification**:

- [x] ✅ [DEVOPS] P1. Central file confirmed fixed and live:
      `gh api repos/IggyIkenna/unified-trading-ci/actions/workflows --jq '.workflows[]|select(.path|test("semver"))|.name'`
      → `"Semver Agent"` (was the raw path before this fix).
- [x] ✅ [DEVOPS] P1. **RESOLVED — self-resolved exactly as predicted, confirmed 2026-08-09 (stale-recheck sweep).**
      Both caller repos now resolve correctly:
      `gh api repos/IggyIkenna/instruments-service/actions/workflows --jq     '...name'` → `"Semver Agent"`; same for
      `unified-trading-api`. Neither shows the raw file path anymore. Resolved naturally via each repo's own subsequent
      `push:[main]` promote cycle, no forced trigger needed — exactly the self-resolution path this todo predicted.
- [x] ✅ [DEVOPS] P2. **DONE 2026-08-09 (stale-recheck sweep) — 3 callers spot-checked, all green.**
      `instruments-service` and `unified-trading-api` both resolve `"Semver Agent"` (see above); additionally checked
      `market-tick-data-service` (also `"Semver Agent"`, 5 recent green runs) as a third spot-check. This closes out the
      doc's live-verification bar for Follow-up regression #2, matching the standard already held for regression #1.

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — promoter/semver-agent gate set, LDR→main model
- `unified-trading-ci/.github/workflows/semver-agent.yml` — the current fix location (reusable `workflow_call` workflow;
  the original `scripts/workflow-templates/semver-agent.yml.tmpl` this doc originally cited was retired by the
  2026-08-06 `fleet_workflow_template_dedup_to_unified_trading_ci` migration — see
  `## Follow-up regression #2 (2026-08-08)`)

## Progress Log

- **2026-08-07**: Filed after investigating the 13-repo `reconcile-release-tags` stall alert. Root-caused via live
  `gh run view --log` evidence (not theory) on 2 repos in different staleness clusters. Fixed the SSOT template
  (patch-level content-based fallback + restored concurrency group), rolled out fleet-wide, shipped to LDR for 21 repos
  via `quickmerge --agent`. Verification (tag-mint confirmation) blocked by a live recurrence of the already-tracked
  glue-runner-pool depletion issue — see `fleet_promoter_glue_runner_stall_2026_08_06.md` Progress Log entry added the
  same session. Will update this doc's Progress Log once the fleet promoter recovers and the live tag-mint verification
  completes.
- **2026-08-07 (fleet_workflow_template_dedup todo 5 session, correction)**: The "0 glue runners" causal attribution
  above was a misdiagnosis (see the full correction in `fleet_promoter_glue_runner_stall_2026_08_06.md`'s Progress Log)
  — `ldr-to-main-promote-fleet.yml` had already been flipped to `ubuntu-latest` hours earlier
  (`unified-trading-pm@c8cd56251e`, 12:23 UTC), so it never actually depended on the glue pool's runner count. The real
  blocker was a separate cancel-treadmill livelock, independently root-caused and fixed by slot-2 at 16:36 UTC
  (`383090a998`). `gh run list` showed all runs 17:30 UTC onward `completed success` as of this same-day check —
  flagging this as informational context for whoever next runs the actual verification, not as a substitute for it: per
  the na-eligibility-audit verdict below, this doc's own evidence bar for closing anything here is a real
  `reconcile_release_tags.py --dry-run` re-run or a minted tag, not an inference from CI run history.
- **2026-08-08**: An unrelated same-day initiative (`fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`)
  migrated all `semver-agent.yml` logic out of per-repo copies into one central `unified-trading-ci` reusable workflow,
  using a stale pre-char-cap-fix copy — silently reintroducing the exact Follow-up regression #1 bug (21,685-char `run:`
  block, over the ~21,000 cap) in the new central location, now a fleet-wide single point of failure. Ported the same
  comment-relocation fix into the new `workflow_call`/`inputs.*` file (`unified-trading-ci@2c67855`) — run-block reduced
  to 16,106 chars. Central file confirmed live-fixed (`gh api .../workflows` resolves `"Semver Agent"`). Caller-repo
  re-registration (`instruments-service`, `unified-trading-api`) still shows the stale raw-path name pending each repo's
  next natural `push:[main]` — no safe forced-trigger exists (caller stub has no `workflow_dispatch`; force-dispatching
  the fleet promoter is banned) and no promote is currently queued for either repo. See
  `## Follow-up regression #2 (2026-08-08)` for full detail. Doc stays `status: open` pending that caller-side
  confirmation.
- **2026-08-08 (resume session)**: Re-verified from scratch after a context handoff. Confirmed
  `unified-trading-ci@2c67855` is genuinely on `origin/main` (`git merge-base --is-ancestor` true) and
  `unified-trading-ci`'s own workflow registration still resolves `"Semver Agent"`. Re-checked
  `instruments-service`/`unified-trading-api` plus 8 more fleet repos (unified-trading-library,
  market-tick-data-service, market-data-processing-service, features-service, execution-service,
  batch-live-reconciliation-service, agent-orchestrator, unified-trading-system-ui, deployment-api) — none has had a
  `push:[main]` since the fix landed (~01:38 UTC); all still show the stale pre-fix registration. `gh run rerun` on the
  latest failed run confirmed NOT retriable ("cannot be rerun" — a true zero-job parse failure, not a flaky run), so no
  way to force a clean re-verification without an actual new promote. Armed a bounded (~20 min) background poller across
  9 repos to catch the first post-fix run opportunistically; will report if one lands, otherwise this stays pending the
  next natural promote per the existing plan above (still correct, not re-litigated). Separately found this doc's own
  **2026-08-08 20:58 write-up commit (`b753382723`/rebased to `868deea279`) had been committed locally but never
  actually pushed** — `safe-doc-push.sh`'s "content already matches HEAD" fast-path incorrectly declared success without
  reaching the push step when invoked on an already-committed-but-unpushed commit (a real gap in that script for the
  "resume after interruption" case, worth a follow-up hardening but not chased further here). Pushed manually
  (`git pull --rebase --autostash` + `git push`) — now confirmed on `origin/live-defi-rollout@2c25f8a9c1`. That push was
  itself blocked once by a pre-existing, unrelated broken-YAML frontmatter in an untracked foreign file sharing this
  slot's checkout (`agents/escalation_queue_reconciler.md`, part of a different concurrent escalation-queue-reconcile
  task) — `check_frontmatter_schema.py`'s `load_registries()` walks ALL `agents/*.md` unconditionally (not just the
  files being pushed), so a malformed doc anywhere in that tree blocks every push from this checkout regardless of
  what's actually being shipped. Fixed the YAML minimally (added `>-` to an unquoted multi-line `summary:` that
  contained `": "`, matching the block-scalar convention already used elsewhere in `agents/*.md`) rather than bypassing
  the hook — left uncommitted for that file's owning session to pick up.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-07** (tranche `ci`): KEEP-NA, valid — brand-new (created today), all 3 open items are
externally dependency-blocked on infra outside this doc's own scope: live tag-mint verification is blocked on the fleet
promoter's glue-runner-pool depletion (tracked separately in `fleet_promoter_glue_runner_stall_2026_08_06.md`), the
re-run-reconcile todo is gated on that same promotion landing, and the `market-tick-data-service` ship is gated on an
unrelated pre-existing test failure tracked elsewhere. All fixes are already shipped to LDR. Not closing any checkbox on
the strength of any fresh "fleet promotion is healthy again" corroboration that may exist elsewhere in this doc's
Progress Log — this audit's evidence bar requires a real `reconcile_release_tags.py --dry-run` re-run or a minted tag,
not an inference; still genuinely open, likely to clear soon.

**na-eligibility-audit 2026-08-08** (tranche `ci`): KEEP-NA, valid — re-verified with fresh live evidence, not an
inference. `python3 scripts/cicd/reconcile_release_tags.py --dry-run` still reports 13 STALLED (unchanged from this
doc's own 13-repo baseline) — the "confirm the stall count drops" todo does not clear yet.
`gh api .../actions/workflows` for both spot-checked caller repos (`instruments-service`, `unified-trading-api`) still
resolves the raw file path, not `"Semver Agent"` — caller re-registration still pending, and
`gh pr list --search "chore(promote)"` shows zero queued promote PRs for either. All 5 open items remain genuinely
externally-blocked (fleet promoter / natural `push:[main]` triggers / the unrelated MTDS test fix), none closeable with
today's evidence.

## Progress Log

- **stale-recheck 2026-08-09** (KEEP-NA staleness re-audit, `ci` tranche): all 5 externally-blocked items from the
  2026-08-08 marker have now cleared with fresh live evidence — `reconcile_release_tags.py --dry-run` shows the stall
  count dropped 13 → 7 (not to 0); `batch-live-reconciliation-service` minted a real post-fix patch tag (`v0.49.1`,
  2026-08-08T09:48:12Z); `instruments-service`/`unified-trading-api`/`market-tick-data-service` all now resolve
  `"Semver Agent"` via `gh api .../actions/workflows` (was the raw path); MTDS turns out to need no separate ship — it
  already runs the fixed logic via the central `unified-trading-ci` reusable workflow. Flipped 5 checkboxes to `[x]`
  with citations. Opened one NEW tracked todo for a genuinely new finding (the residual 7-repo stall, not the same bug —
  root cause not yet determined) rather than leaving it as prose. This doc is NOT an archive candidate — 1 open todo
  remains.

- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:4f41d1675dd06a2d]: KEEP-NA,
valid — 1 open item, newly added today by an earlier stale-recheck session (root-cause the residual 7-repo semver
stall). Tagged `MISCLASSIFIED_LIKELY_AO_ELIGIBLE`: the classification half (check each of 7 repos' commit ranges, label
correctly-quiet vs. genuine gap) is bounded/worker-determinable, but the "if a genuine gap is found and fixed" branch is
open-ended (this doc's own history shows 2 prior "follow-up regression" cascades of real diagnostic

- fleet-wide-fix scope from this same investigation area) — not confident enough to RECLASSIFY the whole doc on one
  read; flag for next round once the classification-only sub-scope could be split out. No `assigned_vm` change.

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:3b146def3dee9bca]: KEEP-NA,
valid — MANDATORY RE-ASSESSMENT applied against the RECLASSIFY bar per the carry-forward instruction. The sole open todo
bundles two halves into one stated 'done when': (1) classify each of the 7 residually-stalled repos' commit ranges since
baseline tag as 'correctly quiet' vs a genuine gap -- bounded, worker-determinable, a checkable fact; and (2) IF a
genuine gap is found, root-cause it AND fix it -- open-ended, outcome-contingent on an unknown. Applying the whole-scope
test (the doc qualifies for RECLASSIFY only when its ENTIRE remaining scope clears the bar, not just one half): this
doc's OWN history documents two real, concrete 'follow-up regression' cascades from this exact investigation area within
the same 48 hours -- both times a GitHub Actions ~21,000-char run-block cap silently broke the fleet-wide semver-agent
pipeline (zero-jobs parse failure across ~21 repos), first via the origin...
