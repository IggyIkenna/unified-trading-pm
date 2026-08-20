---
doc_type: issue
title: Proposal — pin an explicit `LC_TARBALL_FRESHNESS` default for `mtds-live-*` VM relaunches
summary: >-
  Sports batch10 todo 3 asked for a proposal to default `mtds-live-*` VM relaunches to
  `LC_TARBALL_FRESHNESS=enforce`, filed 2026-08-04 when the shared launcher default was `warn` (never blocks a launch).
  Since then two independent fixes already closed the specific gap the original todo raised: the shared library default
  flipped `warn`→`auto` (deployment-service@c1e0481, 2026-08-06) and `auto` mode's own silent-skip bug (declaring
  success even when the republish it triggered was skipped on a dirty tree) was fixed (deployment-service@450b212,
  2026-08-07) so it now correctly blocks a launch if a repo is still stale after the auto-republish attempt. Given
  that, this doc recommends explicitly pinning `LC_TARBALL_FRESHNESS=auto` (not `enforce`) at the 4 `mtds-live-*`/
  perp-clob-live launcher call sites — `auto` already gives the same "never launch onto stale code" guarantee the
  original `enforce` ask wanted, but self-heals via an automatic rebuild instead of hard-aborting the relaunch, which
  matters for a long-running live producer someone is trying to get back onto just-shipped code. The explicit pin (vs.
  leaving it as an inherited default) makes the choice for this VM class self-documenting instead of silently
  inheriting whatever the shared default happens to be — which has already changed once.
status: open
nature: issue
asset_group: [infrastructure]
stage: [live]
repos: [deployment-service]
scope: [engineer]
tags: [vm-tarball-deployment, tarball-freshness, mtds-live, vm-launcher-runbook, proposal]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch10_2026_08_06.md,
    /plans/archive/issues/sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md,
    /plans/active/issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md,
    /plans/active/issues/lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
  ]
created: "2026-08-16"
author: slot-19 (data_engineering, dispatched on batch10 todo 3, adopted infra craft)
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
source: >-
  Extracted verbatim from `sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md`'s sole open todo
  into `sports_satellite_ao_dispatch_batch10_2026_08_06.md` todo 3 (assigned_vm: planning). This doc is that todo's
  deliverable.
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/scripts/vm/launch-mtds-live.sh,
    deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh,
    deployment-service/scripts/vm/launch-mtds-live-prediction-consolidated.sh,
    deployment-service/scripts/vm/launch-perp-clob-live.sh,
    /plans/active/issues/lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md,
  ]
---

# Proposal — explicit `LC_TARBALL_FRESHNESS` default for `mtds-live-*` VM relaunches

## Background — why this todo exists

`sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md` hit a real incident (2026-08-05): relaunching
`mtds-live-*` after a code fix silently ran the VM on a STALE `market-tick-data-service` tarball twice in a row, because
`lc_verify_tarball_freshness`'s default was `warn` — it prints a loud warning but never blocks. For a live producer
(runs for weeks, not a one-shot batch job), a stale relaunch is not self-correcting the way a batch VM's next run would
be. The todo asked for a proposal to default `mtds-live-*` relaunches to `LC_TARBALL_FRESHNESS=enforce` (hard block on
any staleness) to close that gap.

## What changed since 2026-08-04 (the load-bearing finding of this doc)

Two independent fixes already landed on the SHARED `lc_verify_tarball_freshness` mechanism (used by every launcher, not
just `mtds-live-*`), materially changing the landscape the original todo was written against:

1. **`deployment-service@c1e0481` (2026-08-06)** — flipped the library's own default from `warn` to `auto`
   (`launcher_common.sh:1009`, `${LC_TARBALL_FRESHNESS:-auto}`). None of the 4 `mtds-live-*`/perp-clob-live launchers
   set `LC_TARBALL_FRESHNESS` at their call site (confirmed by grep — see Change surface below), so they already
   inherit this new default today, not `warn`.
2. **`deployment-service@450b212` (2026-08-07)** — fixed `auto` mode's own silent-skip bug
   (`lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md`): previously, `auto` mode always returned
   success as long as the republish subprocess exited 0, even when `create-code-tarballs.sh` had SKIPPED the actual
   rebuild (e.g. because unrelated foreign dirty files sat in the shared checkout). Fixed so the post-republish
   re-verify now runs with `enforce` semantics internally and its result is actually propagated — `auto` mode now
   correctly returns non-zero (blocks the launch) if the repo is still stale after the auto-republish attempt.

**Also fixed as a same-turn finding while researching this proposal**: `launcher_common.sh`'s own header comment
(lines 970-971, 985) still documented `warn` as `(DEFAULT)` and `(default: warn)` — stale since the 2026-08-06 flip
above, and exactly the kind of misleading doc comment CLAUDE.md's "a doc/comment that misled you is a finding" rule
requires fixing in the same turn. Corrected in this doc's shipped commit (see Shipped below); no separate todo needed.

Given both fixes, the SPECIFIC failure mode the original todo raised — a live producer silently running provably-stale
code because staleness was only ever a warning — no longer exists for ANY launcher using the shared default, including
`mtds-live-*`. `auto` today gives the same "never launch onto stale code" outcome `enforce` would, but with one
material difference: `auto` attempts an automatic rebuild first and only blocks if that rebuild can't produce a fresh
tarball, while `enforce` blocks immediately on any staleness with no attempt to self-heal, requiring a human/agent to
manually run `create-code-tarballs.sh --include <repo>` before retrying.

## Recommendation

**Explicitly pin `LC_TARBALL_FRESHNESS=auto` (not `enforce`) at each of the 4 `mtds-live-*`/perp-clob-live launcher
call sites**, rather than leaving it as an inherited shared-library default.

Rationale for `auto` over `enforce` specifically for this VM class: the most common trigger for an `mtds-live-*`
relaunch is "I just shipped a fix and want the live producer back on it now" (the exact scenario in the source
incident). Under `auto`, that relaunch self-heals in one command — the launcher rebuilds the stale tarball and
proceeds once it's fresh. Under `enforce`, the SAME relaunch attempt would hard-abort and require a separate manual
rebuild step first, adding friction to the exact recovery path this todo cares about, for no additional safety (both
modes equally refuse to launch onto code that is provably still stale after the check).

Rationale for pinning explicitly rather than leaving it as the inherited default: the shared library default has
already changed once (`warn`→`auto`, 2026-08-06) for reasons unrelated to `mtds-live-*` specifically, and could change
again for a different launcher class's tradeoffs. `mtds-live-*` VMs are long-running live producers where staleness
risk is qualitatively worse than a batch/backfill VM (per the source incident's own framing) — that argues for this
VM class's freshness behavior being an explicit, self-documenting choice at the call site, not a value it happens to
inherit from whatever the shared default is set to at any given time.

**If the operator instead prefers a hard-block-no-auto-heal posture for `mtds-live-*` specifically** (e.g. a
deliberate policy that any stale-tarball relaunch of a live producer should force a human/agent to consciously
rebuild before proceeding, rather than silently auto-rebuilding), the alternative is to pin `LC_TARBALL_FRESHNESS=enforce`
at the same 4 call sites instead — the change surface below is identical either way, only the pinned value differs.

## Change surface

All 4 currently call `lc_verify_tarball_freshness "$CODE_BUCKET" ...` with no `LC_TARBALL_FRESHNESS` set at the call
site (confirmed via `grep -n LC_TARBALL_FRESHNESS`/`lc_verify_tarball_freshness` across `deployment-service/scripts/vm/`,
2026-08-16):

- `deployment-service/scripts/vm/launch-mtds-live.sh:240`
- `deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh:170`
- `deployment-service/scripts/vm/launch-mtds-live-prediction-consolidated.sh:127`
- `deployment-service/scripts/vm/launch-perp-clob-live.sh:199`

Proposed change (identical shape at each site): immediately before the `lc_verify_tarball_freshness` call, add
`export LC_TARBALL_FRESHNESS="${LC_TARBALL_FRESHNESS:-auto}"` (or `:-enforce` per the operator's choice above) — the
`${VAR:-default}` form preserves any operator override (e.g. `off` for a deliberate stale relaunch, or `warn` to
temporarily downgrade) while making the intended default for this launcher class explicit in the script itself
instead of implicit via the shared library.

## Shipped

- `deployment-service@8eae625c` — corrected `launcher_common.sh`'s stale `warn`-is-default doc comment (lines
  970-971, 985) to reflect the actual `auto` default, landed while researching this proposal (misleading-doc finding,
  fixed in the same turn per CLAUDE.md). Verified on origin/live-defi-rollout post-push (the SHA moved from the
  original local commit due to 2 rebases under heavy shared-host quickmerge churn while QG queued — confirmed via
  `git merge-base --is-ancestor`, per RULES.md's "never trust quickmerge's own Landed message alone").

## Todos

- [ ] [INFRA] P3. Implement the recommended pin (`LC_TARBALL_FRESHNESS=auto`, or `enforce` if the operator prefers the
      hard-block posture — see Recommendation above) at the 4 launcher call sites listed in Change surface, with a
      regression test per launcher asserting the exported default (mirroring the existing
      `TestTarballFreshnessGuard`-style tests in `deployment-service/tests/unit/test_vm_launcher_scripts.py`). (repo:
      deployment-service)

## Progress Log

- **slot-19 2026-08-16 (data_engineering, adopted `infra` craft for this task; batch10 todo 3)**: Filed this proposal
  per the todo's done-when. Investigated current state before writing the recommendation rather than restating the
  2026-08-04 incident's now-superseded premise: confirmed via `grep` that the shared `lc_verify_tarball_freshness`
  default is `auto` (not `warn`) as of `deployment-service@c1e0481` (2026-08-06), and that `auto` mode's own
  silent-skip gap was independently fixed by `deployment-service@450b212` (2026-08-07,
  `lc_verify_tarball_freshness_auto_mode_silent_dirty_skip_2026_08_06.md` todo 1) — together these already close the
  specific staleness-risk this todo was filed to prevent. Recommended `auto` (not the originally-proposed `enforce`)
  as the pin value for `mtds-live-*` specifically, with the reasoning above, while presenting `enforce` as the
  explicit alternative if the operator's actual intent is a hard-block posture rather than auto-heal. Fixed a stale
  doc-comment finding in `launcher_common.sh` hit along the way (see Shipped, `deployment-service@8eae625c`,
  verified on origin). Implementation left as a follow-up todo (`assigned_vm: NA` pending an operator read of the
  auto-vs-enforce tradeoff above) rather than folded into this session, since the todo's own done-when only required
  the proposal doc to exist.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-17** (infra tranche) [body-hash:0df0d853988b1b0d]: KEEP-NA, valid — doc's own author explicitly set assigned_vm: NA pending an operator read of an auto-vs-enforce policy tradeoff on live-trading-adjacent infra.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
