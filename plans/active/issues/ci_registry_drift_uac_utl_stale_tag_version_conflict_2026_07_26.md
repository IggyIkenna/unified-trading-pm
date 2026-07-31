---
doc_type: issue
title:
  unified-trading-system-ui's registry-drift CI job has been silently broken since 2026-07-21 (UAC/UTL stale-tag pip
  conflict)
summary: >-
  unified-trading-system-ui's ci.yml `registry-drift` job (the only CI-level drift check for
  lib/registry/ui-reference-data.json) has failed on EVERY push to main since at least 2026-07-21 — the `pip install -e`
  of UAC+UTL default-branch checkouts hits a ResolutionImpossible: UAC's main HEAD resolves (via hatch-vcs git-describe)
  to a stale "0.71.1.devNNN" version because tag v0.72.0 is NOT an ancestor of UAC's current main branch, which fails
  UTL's `unified-api-contracts>=0.72.0` pip constraint. Found while scoping
  defi_wizard_batch2_018_residual_findings-004/-005 (extending this same job to also drift-check
  capability-manifest.json/capability-verdict-matrix.json) — a scratch PR reproduced the identical failure on completely
  unmodified code, proving it predates and is unrelated to that work. A partial fix (fetch-depth:0 on the UAC/UTL
  checkouts, fixing a separate shallow-clone/no-tags-at-all failure mode) is shipped, but the deeper stale-tag- ancestry
  issue remains open and needs a cicd/infra-scoped investigation.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-system-ui, unified-api-contracts, unified-trading-library]
scope: [engineer]
tags: [ci, registry-drift, hatch-vcs, dynamic-versioning, pip, cross-repo]
related:
  [
    /plans/archive/issues/defi_wizard_batch2_018_residual_findings_2026_07_26.md,
    /plans/archive/issues/hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-26
parent_epic: infrastructure_master
priority: P2
estimate_class: infra
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: [hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26]
gate_on_depends: true
source:
  [
    unified-trading-system-ui/.github/workflows/ci.yml,
    unified-api-contracts/pyproject.toml,
    unified-trading-library/pyproject.toml,
  ]
---

## What I found

While scoping `defi_wizard_batch2_018_residual_findings-004`/`-005` (extend the `registry-drift` CI job to also
drift-check `capability-manifest.json`/`capability-verdict-matrix.json`, mirroring the existing `ui-reference-data.json`
check), I pushed a scratch branch + draft PR (#354, then #356 after a partial fix, both closed without merging) to
verify the new steps against a real GitHub Actions run. The job failed before it ever reached my new steps — at the
PRE-EXISTING `Install generator deps (UAC + UTL — the generator imports both)` step
(`pip install -e _deps/unified-api-contracts -e _deps/unified-trading-library`), completely unmodified by my change.

**Confirmed pre-existing, not caused by my work**: `gh run list --workflow "CI - Test & Lint" --branch main --limit 10`
shows the `registry-drift` job has failed on the last 10 consecutive pushes to `main`, going back to **2026-07-21**.
`e2e` also fails consistently on the same runs (separate, not investigated here — `ci.yml` is not the required check,
`quality-gates-v2.yml` is, so this has gone unnoticed operationally).

**Root cause, in two layers:**

1. **Shallow-clone / no-tags-at-all (FIXED this session).** `actions/checkout@v5`'s default is a shallow clone with no
   tags. UAC and UTL both use `hatch-vcs` (git-describe-against-tags) dynamic versioning. With no reachable tags, the
   resolved version was a placeholder `0.1.dev1+g<sha>` — which trivially fails UTL's
   `unified-api-contracts<1.0.0,>=0.72.0` constraint (0.1 < 0.72). Fix: add `fetch-depth: 0` to the UAC/UTL checkout
   steps (`unified-trading-system-ui@8c2f3590`, shipped).

2. **Stale reachable tag (STILL OPEN, deeper).** After the fetch-depth fix, the version resolves correctly to a REAL
   git-describe value — but it's still wrong: `0.71.1.dev158+gb22f9fca2`. `gb22f9fca2` is UAC's actual current `main`
   HEAD (confirmed via `gh api repos/IggyIkenna/unified-api-contracts/commits/main`). Tag `v0.72.0` exists in the repo
   (confirmed via `gh api repos/IggyIkenna/unified-api-contracts/tags`) but
   `git merge-base --is-ancestor <v0.72.0-sha> b22f9fca2` returns **false** — v0.72.0 was tagged on a commit that is
   **not an ancestor of UAC's current main branch**. `git describe` therefore falls back to an older tag
   ("v0.71.1"-ish), and UTL's `>=0.72.0` constraint correctly (if unhelpfully) rejects it. This is NOT a shallow-clone
   artifact — `fetch-depth: 0` does not fix it, because the tag genuinely isn't reachable from main's actual history.

**Why this matters beyond CI noise**: `ci.yml`'s `registry-drift` job is the ONLY thing that would catch
`lib/registry/ui-reference-data.json` going stale vs UAC/UIC (per `unified-trading-pm/docs/ui-alignment-ssot.md` §1's
"next automation step" note). It has been unable to run successfully for 5+ days — meaning that drift check has been
silently non-functional this whole time, on top of the separate capability-manifest.json/capability-verdict-matrix.json
gap already documented in `docs/ui-alignment-ssot.md` §1a.

**Not investigated / not this doc's job**: WHY v0.72.0 isn't an ancestor of main (a release-tagging/branch-topology
question — possibly related to the semver-agent retarget off `staging` noted in workspace CLAUDE.md § "Git discipline",
though the dates don't line up cleanly enough to be certain) is a cicd/infra-scoped release-process question, not
something this UI-craft-scoped investigation should hand-fix by loosening a version constraint or minting a tag.

## Why it matters

A silently-broken, non-required CI job is exactly the kind of thing that stays broken indefinitely because nothing pages
on it — this one has already gone 5+ days unnoticed. It also fully blocks verifying
`defi_wizard_batch2_018_residual_findings-004`/`-005`'s CI-check design in real GitHub Actions (the design itself is
proven correct via local reproduction — see that issue doc — but never successfully executed end-to-end in CI).

## Recommended decision

- [x] ✅ [SCRIPT] P3. **DONE 2026-07-26 (slot 2), `unified-trading-system-ui@8c2f3590`.** Shipped the fetch-depth:0 fix
      (layer 1) — it's a genuine, real, independently valuable fix regardless of layer 2's resolution (correct version
      strings resolve now instead of a nonsense placeholder), full `quality-gates.sh` green.
- [x] ✅ [CICD] P2. **DONE 2026-07-26 (slot 6)** — root-caused in the sibling doc
      `/plans/archive/issues/hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md` § "Root cause
      diagnosed": `v0.72.0` was a MANUAL one-off D13-migration baseline tag placed on an LDR-side `_backmerge` merge
      commit (`4ac8be3f`), never on `main`'s own graph — not a semver-agent bug, not a stalled promotion (content was
      byte-identical on `main`'s own squash commit `b52aea5d`, ~2h later, which is what should have been tagged). `main`
      only advances via single-parent squash commits, so an LDR-side tag can never become a `main` ancestor no matter
      how many further promotions land — this will NOT resolve on its own via (a). Adjacent finding also logged there:
      `semver-agent` is correctly retargeted to `push:[main]` since 2026-07-25 and would self-heal this class going
      forward, but its bump-rate circuit breaker is currently tripped, so no new tag has actually landed yet. Fix
      direction (re-tag vs. wait-for-breaker-clear) is the sibling doc's still-open todo 2 — not duplicated here.
- [ ] [SCRIPT] P3. Once the above is resolved, re-verify `registry-drift` goes green on `main` for 3 consecutive pushes
      (not just once — confirm it's not still flaky), THEN pick up the already-designed
      capability-manifest.json/capability-verdict-matrix.json CI-check extension from
      `defi_wizard_batch2_018_residual_findings-004`/`-005` (the YAML is fully drafted and locally-verified — see that
      issue doc's evidence — just needs a clean real-CI run to merge with confidence). Repos: unified-trading-system-ui,
      unified-trading-pm.
- [ ] [CICD] P3. **Addendum (slot 4, 2026-07-26)**: independently re-derived the same layer-1/layer-2 diagnosis while
      picking up `defi_wizard_batch2_018_residual_findings-004` concurrently with slot 2 — see the sibling doc
      `hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md` for the concurrently-completed
      root-cause work (its own todo 1). Also hit a THIRD, separate symptom while re-verifying on scratch PRs
      #353/#357/#358/#359: a repo-wide `pull_request`-event Actions stall on `unified-trading-system-ui` — zero
      `pull_request`-triggered workflow runs fired for **20+ minutes** (confirmed via
      `gh api repos/.../actions/runs?event=pull_request`, checked repo-wide not just on my branch), while
      `push`-triggered runs on `main`/`live-defi-rollout` kept firing normally throughout the same window. Ruled out:
      not branch-specific (tested 3 different branches), not draft-PR-specific (`gh pr ready` didn't help), not an
      Actions-disabled/billing issue (`actions/permissions` shows enabled, GitHub status page green). Whoever picks up
      the P3 re-verify todo above should check whether this recurs — if `pull_request` events are still silently
      dropping intermittently, that's a SEPARATE Actions-delivery reliability issue worth its own investigation
      (possibly GitHub-side, possibly an org webhook config), not the tag-ancestry bug this doc tracks.

## 2026-07-26 premature-dispatch finding + `depends_on`/`gate_on_depends` fix (slot 10)

Dispatched todo 3 (`-002` in the backlog) fresh. `GET /api/backlog/.../blockers` returned `"ready (no blockers)"` even
though this doc's own todo 2 says explicitly "Fix direction... is the sibling doc's still-open todo 2 — not duplicated
here" — i.e. todo 3 here genuinely depends on
`hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md`'s todo 2 (`[DEVOPS] P2`, decide + ship the
fix direction), which is a DIFFERENT plan file. Re-verified live before touching anything:
`git fetch origin main --tags` + `git merge-base --is-ancestor v0.72.0 origin/main` on `unified-api-contracts` still
returns NOT an ancestor — the tag-ancestry gap is still open, so `registry-drift` would still fail identically on `main`
today. Confirmed the sibling doc's todo 2 is still `- [ ]` unchecked.

This is a genuinely different shape from the two premature-dispatch fixes already applied elsewhere today: not a
same-doc chain (→ `sequential: true`) and not an operator-only credential (→ `BLOCKED-CREDENTIALS`), but a real
CROSS-PLAN dependency on another doc's still-open, worker-dispatchable todo — exactly the case `depends_on` +
`gate_on_depends: true` exists for. Added both to this doc's frontmatter above, pointing at the sibling doc's slug. Note
(per the known `gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` issue): this wiring has a documented
history of not always taking effect on the same regen tick a plan is authored/edited — if `-002` (or its successor id)
gets re-dispatched again with `blockers` still reporting "ready," that issue doc's wiring-gap investigation is the next
place to look, not a fresh re-diagnosis here. Declining to run/verify the CI job or flip the checkbox against a fix that
hasn't landed; skipping this task (`reason_code: GATED`).

## 2026-07-27 tag-ancestry gap now closed — first re-verification (session-3)

The sibling doc's fix direction resolved: the operator directly force-moved `unified-api-contracts`' `v0.72.0` tag from
the LDR-only commit to the correct main-side squash-promote commit (`b52aea5d`, byte-identical tree) — see
`/plans/archive/issues/hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md` § "Resolution" for
the full command trail. Re-ran this doc's own P3 todo (`gh run rerun 30217824955 --failed` on
`unified-trading-system-ui`'s `registry-drift` job, the same run cited above as still-broken pre-fix):

- **`pip install -e` now SUCCEEDS** — log shows
  `Successfully installed ... unified-api-contracts-0.72.1.dev165+gb6b92922b unified-trading-library-0.58.1.dev6+g1ef0ffb53 ...`
  (full dependency tree resolved, no version-conflict error). This is the FIRST successful install since the regression
  window opened — the tag-ancestry root cause is confirmed fixed end-to-end, not just fixed-in-theory.
- **BUT the job still fails — two DIFFERENT, unrelated blockers now surface** (invisible before, because the job never
  got past `pip install` to reach them):
  1. `registry-drift` step itself:
     `##[error]lib/registry/ui-reference-data.json content is stale vs UAC. Regenerate it...` — plus a WARNING
     `Failed to extract MVP_CME_EXCHANGE_CODES: cannot import name 'MVP_CME_EXCHANGE_CODES' from 'unified_api_contracts.registry'`
     (a genuine UAC/UI content drift, unrelated to hatch-vcs/tags).
  2. Separate `e2e` job: `Error: ENOENT: no such file or directory, stat '.../unified-trading-system-ui/.gitleaks.toml'`
     — a missing config file, also unrelated to tags/versioning.
- **Verdict**: this doc's own scope (tag-ancestry-caused registry-drift breakage) is RESOLVED and confirmed via live CI
  evidence. The "3 consecutive green pushes" bar in the P3 todo above cannot be met as originally worded because TWO
  NEW, genuinely separate issues now block green — re-scoping that todo to "3 consecutive greens once the 2
  newly-exposed blockers are independently fixed" rather than re-diagnosing tags again. Not filing new issue docs for
  the 2 new blockers in this pass (out of this doc's scope, no further investigation done on either) — flagging here so
  the next picker-upper doesn't mistake them for a tag-fix regression.

## 2026-07-31 blocker 1 fixed (registry content regen); blocker 2 already fixed; a 3rd blocker found — NOT this doc's scope

Picked up this doc's own P3 todo 3 fresh. Fresh-pulled the fleet, re-checked `main`'s last 10+ `CI - Test & Lint` runs.

**Blocker 1 (registry-drift's own stale-content failure) — FIXED this session.** Set up `git worktree` checkouts of
UAC/UTL/PM at their actual `main` tips (the exact refs `registry-drift`'s job checks out — NOT `live-defi-rollout`,
which can differ), built a throwaway py3.13 venv, and ran the documented regen command CI-faithfully. Confirmed genuine,
large drift: `archetype_count` 23→53 (+30 archetypes accumulated on UAC main since the file was last regenerated —
TSMOM/DEFI_LP/PORTFOLIO_FACTOR_ALLOCATION/etc — 6197 lines of content-normalized diff, not a formatting artifact). No
`MVP_CME_EXCHANGE_CODES` import warning this time (38 codes extracted cleanly) — that part of the 07-27 finding is gone
(unrelated prior fix, not reinvestigated). Regenerated, ran `prettier --write` to match the committed style, and
confirmed the new committed file content-normalizes BYTE-IDENTICAL to a fresh generation (the exact check
`registry-drift`'s `Diff ui-reference-data.json` step runs). Shipped: `unified-trading-system-ui@dfbfff68`
(`fix(registry): regenerate ui-reference-data.json from UAC/UTL main`).

**Blocker 2 (e2e's `.gitleaks.toml` ENOENT) — already fixed by someone else, prior to this session.** `git log` shows
`1306658c fix(ci): replace dangling .gitleaks.toml symlink with real file copy`, already on both `main` and
`live-defi-rollout` (`git ls-tree` confirms `100644` regular blob, not a `120000` symlink, on both). Not this session's
work — noting it here so the "3 consecutive greens" bar isn't miscounted against a blocker that's already gone.

**Blocker 3, newly found — a flaky `test` job failure, NOT filing a new issue doc, cross-referencing instead.** 3 of the
last ~10 `main` CI runs (e.g. `30544453841`, `30543110912`, `30403417035`) show the `test` job itself failing on
`tests/unit/components/strategy-catalogue/admin-editor-wiring.test.tsx` ("surfaces the load error banner on GET failure"
— `TestingLibraryElementError: Unable to find an element by: [data-testid="admin-editor-load-error"]`), which skips
`registry-drift`/`e2e` entirely (both `needs: test`). Ran this exact test file in isolation locally 5/5 times — 100%
pass, 6-8s each — ruling out a real app/test bug. The failing CI runs show adjacent
`ECONNREFUSED 127.0.0.1:8030`/`socket hang up` noise from concurrent workers in the same log, and separately observed
`gh api .../actions/runners` showing exactly ONE `glue-ip-172-31-5-118-1` runner (shared, frequently `busy`) with 2-3
runs sitting `queued` for 1-2.5+ hours at time of writing. This matches, symptom-for-symptom, the ALREADY-TRACKED,
still-open multi-day incident `plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`
(host-contention-induced timeouts/hangs on the same shared `glue` runner fleet, `i-0c9b283b31d6b5ca7`) — that doc's own
entries repeatedly conclude "host contention, no code fix" for symptomatically-identical CI flakes. Not duplicating a
new issue doc for this; deliberately cross-referencing instead.

**Verdict / what's left**: this doc's registry-drift-specific scope is now fully unblocked in principle (both real
blockers fixed). The "3 consecutive green `main` pushes" bar itself is NOT yet observed — it requires the fix above to
actually run to completion on `main` via the LDR→main promotion cycle, competing for the same contended single runner
tracked by the day2 capacity doc, so wall-clock to observe 3 greens could span hours and depends on that separate
incident's trajectory, not on anything left to do in THIS doc. Leaving todo 3 unchecked pending that live observation —
whoever next has a natural CI-status check in flight (or the next `/check-agent-orchestrator`-adjacent session) should
glance at `gh run list --workflow "CI - Test & Lint" --branch main --repo IggyIkenna/unified-trading-system-ui` and, if
3 consecutive `registry-drift: success` are visible, flip the checkbox and move on to the
capability-manifest.json/capability-verdict-matrix.json CI-check extension the todo also names.

## Deferred work after 2026-07-31 (pre-compact checkpoint, slot 7)

| Item                                                                               | State / why deferred                                                                                                                                                                                  | Blocked on                                                                                                                                     |
| ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Todo 3: 3 consecutive `registry-drift: success` on `main`                          | Cannot be done yet — the fix (`unified-trading-system-ui@dfbfff68`) is shipped and its first verification run (`30635331302`) has been `queued` since 13:39:22Z (2h43m+ at last check, zero movement) | Elapsed real time on the contended shared `glue` runner (see `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`) — not work, waiting |
| Todo 4: capability-manifest.json/capability-verdict-matrix.json CI-check extension | Not started — explicitly gated behind todo 3 by the todo's own wording ("Once the above is resolved... THEN pick up...")                                                                              | Todo 3                                                                                                                                         |

**Recommended next item**: re-check
`gh run list --workflow "CI - Test & Lint" --branch main --repo IggyIkenna/unified-trading-system-ui --json databaseId,status,conclusion,createdAt --limit 10`
and, per-run,
`gh run view <id> --repo IggyIkenna/unified-trading-system-ui --json jobs -q '.jobs[] | select(.name=="registry-drift") | .conclusion'`
— once `30635331302` (or its successor push) resolves, count consecutive `registry-drift: success` results back from the
newest completed run. 3 in a row → flip todo 3's checkbox with the run IDs as evidence, then start todo 4 (the
capability-manifest/verdict-matrix CI-check YAML is already drafted per
`defi_wizard_batch2_018_residual_findings-004`/`-005`, cited above — it just needs a clean real-CI merge). A background
poller (5-min interval, self-heartbeating, `MAX_CYCLES=48` ≈ 4h cap) may still be running in slot 7's session scratchpad
watching exactly this — if so, its next completion notification carries the answer; if that session has since ended, the
check above reproduces it from scratch in under a minute.

**Lessons for whoever picks this up next**:

- The registry-drift job's own `main`-tip-vs-committed-file diff check is CI-faithful only if you regenerate against
  UAC/UTL/PM's actual `main` tips (via `git worktree add ... origin/main --detach`), NOT `live-defi-rollout` — the two
  can differ meaningfully (confirmed here: LDR-tip UAC differs from main-tip UAC often enough that this file drifts
  repeatedly, per the git history of `fix(registry): refresh/regenerate ...` commits on this same file).
- `busy: true` on `gh api .../actions/runners` does NOT mean YOUR run is progressing — cross-check
  `gh api .../actions/runs?status=in_progress` for the SAME repo; if that's empty while the runner is busy, the runner
  is busy on a DIFFERENT repo's job (the "glue" runner fleet is shared cross-repo by name, not per-repo-exclusive
  despite each repo having its own `/actions/runners` registration entry).
- A queued-but-not-failed CI run has NO retrigger remedy — the established "resolve via retrigger" posture in the
  capacity-crisis doc applies to runs that already failed/died from contention, not ones still waiting for the runner.
  Don't waste a retrigger on a run that's simply queued.
- Markdown pre-commit/prettier reformatting can mangle spacing around adjacent inline-code spans in long wrapped
  paragraphs (observed + fixed in this same doc, see the Blocker 3 paragraph above) — worth a visual re-read of any long
  backtick-dense paragraph after it round-trips through a commit, not just a diff-stat check.

## 2026-07-31 ~18:47Z re-check (slot 14) — still queued, still not this doc's work to do

Picked up todo 3 fresh via `/boot`. Re-ran the exact recommended check:
`gh run list --workflow "CI - Test & Lint" --branch main --repo IggyIkenna/unified-trading-system-ui --json databaseId,status,conclusion,createdAt,updatedAt --limit 15`.

All three runs the prior (slot 7 pre-compact) entry named as pending are **still `queued`, zero progress**:
`30635331302` (created 13:39:22Z, `updatedAt` unchanged at 13:39:22Z — 5h+ with no state transition at all),
`30627739825` (created 11:38:27Z, `updatedAt` 18:43:37Z — touched recently but still `queued`, not `in_progress`),
`30625075106` (created 10:53:00Z, `updatedAt` 18:18:16Z — same). `gh api .../actions/runners` shows the single
`glue-ip-172-31-5-118-1` runner still `busy: true`. Host `uptime` on this orchestrator VM: load average
11.02/14.40/14.11 on 16 vCPU — elevated again versus the prior entry's 18:08:44Z "eased" reading (6.00/6.85/7.17),
consistent with `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`'s own documented
"fluctuating-but-still-elevated," not resolved, pattern.

No consecutive-green count is observable yet — the last 3 runs before these are still `queued` are `failure`
(2026-07-30, pre-dating this doc's own fixes having had a chance to run). Per this doc's own established lesson ("a
queued-but-not-failed CI run has NO retrigger remedy... don't waste a retrigger on a run that's simply queued"), not
retriggering. This is the third session in a row (session-3 2026-07-27, slot-7 pre-compact 2026-07-31, this one) to find
the identical genuinely-external-wait state — nothing left to DO here until the shared runner fleet actually drains and
one of these runs transitions to `in_progress`/`completed`. Leaving todo 3 unchecked; self-skipping this task rather
than holding the slot idle-waiting (mirrors slot 10's 2026-07-26 `reason_code: GATED` skip earlier in this same doc) so
the slot can pick up other queued work instead of busy-polling a condition only external CI capacity can change.
