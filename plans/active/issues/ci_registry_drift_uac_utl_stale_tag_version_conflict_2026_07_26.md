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
context_scope:
  [
    /plans/archive/issues/hatch_vcs_main_tag_ancestry_gap_breaks_cross_repo_pip_install_2026_07_26.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
    /plans/archive/issues/defi_wizard_batch2_018_residual_findings_2026_07_26.md,
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

## 2026-07-31 ~19:36Z re-check (slot 15) — real partial movement this time, but still not resolved

Picked up todo 3 fresh. Unlike the prior 3 checks (zero state transitions), this session observed **genuine forward
progress**: run `30635331302`'s `test` job left `queued` for the first time in this doc's history, ran, and
**succeeded** (`19:03:08Z` → `19:11:12Z`, ~8 min). Watched via a bounded 30-min background poll (5-min interval) rather
than a single snapshot, specifically to distinguish "still stuck" from "about to move."

**But `registry-drift` itself (the job this todo actually gates on) never got a turn.** Once `test` passed, both
`registry-drift` and `e2e` immediately re-queued for the same single `glue-ip-172-31-5-118-1` runner and sat there for
25+ minutes with zero further state change (confirmed via 6 samples at `19:05/19:10/19:15/19:21/19:26/19:31Z`, then a
final fresh check at `19:36:40Z` — all identical: `registry-drift=queued`). `gh api .../actions/runners` still shows the
one runner `busy: true` — per this doc's own established lesson, that does not mean progress on THIS run, since the
runner is shared cross-repo.

**Verdict**: still not this doc's work to do — the blocker is 100% the same tracked external capacity incident
(`fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`), not a code or config issue. The new data point worth
keeping for the next picker-upper: `test` passing confirms the pip-install/tag-ancestry fix AND the registry-content
regen fix (both already shipped) are not themselves blocking anything — the entire remaining gap is queue depth on the
one shared runner. No consecutive-green count observable yet (0 of 3 target runs have reached `registry-drift`
completion). Leaving todo 3 unchecked; self-skipping this task (4th session in a row, `reason_code: GATED`) rather than
holding the slot — same posture as the three prior sessions.

## 2026-07-31 ~19:50Z re-check (slot 12) — same 3 runs, `e2e` now progressing, `registry-drift` still queued

Picked up todo 3 fresh via `/boot`. Re-ran the exact recommended check on the same 3 pending runs
(`30635331302`/`30627739825`/`30625075106`) plus per-job status:

- All 3 runs: `test` job = `success` (confirms slot 15's finding still holds).
- `30625075106`: `e2e` now `in_progress` (first movement on `e2e` observed across all sessions so far) —
  `registry-drift` still `queued`.
- `30635331302`, `30627739825`: both `e2e` AND `registry-drift` still `queued`.
- `gh api .../actions/runners` → single `glue-ip-172-31-5-118-1` runner, `busy: true`;
  `gh api .../actions/runs?status=in_progress` for this repo → **0** — confirms (per this doc's own established lesson)
  the runner is busy on a different repo's job, not making progress on any of these 3 runs' `registry-drift` step.

**Verdict**: identical externally-gated state as the last 2 sessions (slot 14 at 18:47Z, slot 15 at 19:36Z) — no new
code work available, 0 of 3 target runs have reached `registry-drift` completion, so the "3 consecutive green" bar
remains unobserved. This is purely the shared-runner capacity incident draining on its own schedule. Leaving todo 3
unchecked; self-skipping this task (5th session in a row, `reason_code: GATED`) — same posture as slots 10/14/15.

## 2026-07-31 ~20:xxZ re-check (slot 4) — IDENTICAL state to slot 12, zero movement in 10+ min — flagging redispatch churn

Picked up todo 3 fresh via `/boot` (`already_in_progress: true`, `dispatch_reason: "resume"`). Re-ran the exact same
check on the exact same 3 runs:

- All 3 runs: `test` = `success` (unchanged).
- `30625075106`: `e2e` = `in_progress` (unchanged from slot 12's reading).
- `30635331302`, `30627739825`: `e2e` = `queued` (unchanged).
- All 3: `registry-drift` = `queued` (unchanged — still 0 of 3 target runs reached completion).
- `gh api .../actions/runners` → single `glue-ip-172-31-5-118-1` runner, `busy: true`;
  `gh api .../actions/runs?status=in_progress` for this repo → **0** (unchanged).

**This is byte-for-byte the same observable state slot 12 recorded ~10-15 minutes ago** — no state transition occurred
between that check and this one. This is now the **6th consecutive session** (slots 10, 14, 15, 12, and this one, plus
the original slot-7 pre-compact entry) to `/boot` this exact todo, spend a check confirming nothing changed, and
self-skip. Per the workspace CLAUDE.md async-wait/poll-discipline HARD RULE ("a bare skip re-queues it to re-dispatch
every cycle with zero new information — a textbook async-wait/poll-discipline violation... gate it behind a condition so
it only re-dispatches once the fleet actually advances") — this doc's own todo 3 has now hit exactly that pattern.
Posting a `/blocked` (not a code question — a scheduling one: should this task be parked via `priority_override` + a
`registry-drift-observable` prerequisite condition, gated on the tracked capacity incident, so it stops burning a fresh
worker dispatch every cycle for identical zero-new-information reads) with `can_continue: true` and moving to other
queued work rather than holding this slot on a 7th identical poll. Leaving todo 3 unchecked; self-skipping
(`reason_code: GATED`) — same posture as the 5 prior sessions, but flagging the churn itself as the actionable finding
here.

## 2026-08-01 ~09:36-09:45Z re-check (slot 9) — todo 4's own ask (pull_request-stall recurrence), new queue-depth record, no code regression found

Dispatched todo 4 (this doc's own `[CICD] P3` addendum item — id `-003`), not todo 3. Its concrete ask is narrower than
todo 3's: "whoever picks up the P3 re-verify todo above should check whether [the `pull_request`-event stall] recurs."
Checked that directly rather than repeating todo 3's exhausted 3-run poll:

- **No open PRs currently exist on `unified-trading-system-ui`** (`gh pr list --state open` → `[]`), so there is no live
  case to reproduce the original 20+-minute `pull_request`-event-delivery stall against. The most recent
  `pull_request`-triggered runs are all from 2026-07-31T13:32Z (the `dfbfff68` promote PR) and fired normally — no gap
  observed between repo activity and run dispatch in the available data. **Inconclusive, not clean**: absence of a
  currently-open PR means this check cannot positively confirm the symptom is gone, only that it isn't observable right
  now. Whoever next has a live PR in flight on this repo should re-check
  `gh api repos/IggyIkenna/unified-trading-system-ui/actions/runs?event=pull_request` against that PR's actual open
  time.
- **Confirmed the tracked capacity incident (`fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`) is still open
  and was updated as recently as ~07:52Z today (2026-08-01)** — i.e., ~1h45m before this check, not a stale reference.
- **New queue-depth record**: run `30635331302` (the actual post-fix verification run per the 2026-07-31 "blocker 1
  fixed" entry — `dfbfff68` landed before this run was dispatched) has now been sitting `queued` since
  `2026-07-31T13:39:22Z` — **~20h as of this check**, its `registry-drift` job still `status: queued`, never started.
  This exceeds every previously-logged queue-depth figure in either doc (prior worst: ~3h+). `30627739825` similarly
  unchanged (`e2e`=`in_progress`, `registry-drift`=`queued`).
- **One of the 3 originally-tracked runs, `30625075106`, finally completed** (`conclusion: cancelled`, its
  `registry-drift` job `conclusion: failure`) — but this is **not a regression**: `30625075106` was created
  `2026-07-31T10:53:00Z`, which is BEFORE the `dfbfff68` registry-content-regen fix landed (the doc's own 07-31 entry
  identifies `30635331302`, created 13:39:22Z, as the FIRST run to test the fix). Pulled the actual job log
  (`gh run view --job 91235842697 --log`): the job ran end-to-end (checkout → pip install → regen → diff), reaching the
  `Fail on stale registry` step with `archetype_count: 23` (committed, stale pre-fix content) vs `53` (fresh regen) —
  the exact drift signature the doc's 07-31 entry already diagnosed and fixed. This confirms the diff mechanism works
  correctly and that no new drift/regression exists on the actual fix commit; it's simply a stale-queued pre-fix run
  finally getting a turn on the runner and correctly failing against content that was superseded 20+ hours ago.
  `e2e`=`cancelled` (superseded), consistent with GitHub's own supersede-check behavior on an outdated run.
- `gh api .../actions/runners` → single `glue-ip-172-31-5-118-1` runner, still `busy: true`;
  `gh api .../actions/runs?status=in_progress` for this repo → **0** (same signature as every prior entry — the runner
  is busy on a different repo's job).

**Verdict**: todo 4's own ask is inconclusive-by-absence (no open PR to test against) rather than resolved — recommend
whoever next opens a PR on this repo do the check with a live case. Todo 3's blocker is unchanged in kind (same tracked
external capacity incident) but WORSE in degree (new 20h queue-depth record) — still zero code work available on this
doc's own scope. No repo state changed by this check; no code or config touched. Leaving todo 3 and todo 4 unchecked;
self-skipping this task (`reason_code: GATED`) — 7th consecutive session to hit this doc's capacity blocker, same
posture as the 6 prior sessions. Did not re-post a duplicate `/blocked` (slot 4's scheduling question above already
covers the parking ask; a generic worker session doesn't have `data/config/backlog.yaml` write access to self-action it
per RULES.md §4's "main agent + operator" scoping — flagging for main/operator to action, not re-asking).

## 2026-08-01 ~10:10Z re-check (slot 15) — byte-identical to slot 9's check 30 min earlier; self-skip is auto-parking, no further manual action needed

Picked up todo 4 (`-003`) fresh via `/boot` (`already_in_progress: true`). Re-ran the same checks slot 9 ran ~30 min
prior: `gh pr list --state open` on `unified-trading-system-ui` → still `[]` (no live PR to test the
`pull_request`-stall question against — unchanged). The 2 still-pending runs (`30635331302`, `30627739825`) show
unchanged `updatedAt` timestamps vs slot 9's reading — zero state transition. `gh api .../actions/runners` → single
`glue-ip-172-31-5-118-1` runner, `busy: true`; `gh api .../actions/runs?status=in_progress` for this repo → **0** (same
signature). The sibling `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` doc is still `status: open`,
`last_updated: 2026-08-01`.

**Not re-deriving the same finding at length** — this is now the 8th consecutive session with zero new information on
this doc's capacity blocker. **Correction to prior sessions' stated limitation**: found that a generic worker session
does NOT actually need `data/config/backlog.yaml` write access to action the parking slot 4 asked about —
`agent-orchestrator/server/auto_park.py` already implements exactly that recipe automatically:
`POST /api/slots/<N>/skip-current-task` with `reason_code: "GATED"` is counted per-task, and once the count crosses
`tuning.dispatch_cooldown_auto_park_skip_threshold`, the server itself applies `priority: 999` +
`priority_override: true` + a synthetic `auto_unpark__<task_id>` prerequisite (idempotent — a task already parked is
left alone) — no hand-edit needed, no operator action needed to trigger it, and no duplicate `/blocked` needed. Calling
`/skip-current-task` with `reason_code: GATED` (as every prior session in this doc has already been doing) IS the
correct self-action; it was already accumulating toward auto-park with each skip. Doing the same now. Leaving todo 3 and
todo 4 unchecked; self-skipping (`reason_code: GATED`).

## 2026-08-01 ~10:2xZ re-check (slot 12) — byte-identical, 9th consecutive session, no new information

Picked up todo 4 (`-003`) fresh via `/boot` (`already_in_progress: true`, `dispatch_reason: "resume"`). Re-ran the same
checks: `gh pr list --state open` on `unified-trading-system-ui` → still `[]` (unchanged — no live PR to test the
`pull_request`-stall question against). `30635331302`/`30627739825` unchanged (`updatedAt` identical to slot 15's 10:10Z
reading). One new run appeared (`30695614270`, created 10:23:26Z) but is itself `queued`, adding to the backlog rather
than resolving it. `gh api .../actions/runners` → single `glue-ip-172-31-5-118-1` runner, still `busy: true`;
in-progress runs for this repo → **0** (same signature — runner busy on a different repo's job). No code or config work
available on this doc's own scope. Self-skipping (`reason_code: GATED`) per the now-confirmed auto-park mechanism —
leaving todo 3 and todo 4 unchecked.

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (3 entries).
