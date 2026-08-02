---
doc_type: issue
title:
  features-service volatility family has a real, tested fix for the same PREDICTION MDPS-bucket bug already fixed 4x in
  delta_one — but the only copy is a commit slot 9's local clone discarded from its own branch, recoverable today only
  via that clone's reflog
summary: >-
  Slot 9's local `features-service` clone contains commit `272de118` ("fix(volatility): route MDPS market-data bucket
  resolution through shared PREDICTION-aware resolver", 2026-08-01 15:20:21 UTC) that is not on
  `origin/live-defi-rollout`, not patch-equivalent to anything on origin, and — beyond what was first flagged in chat —
  not reachable from any local branch tip either: the branch was reset back to `origin/live-defi-rollout` after the
  commit landed (reflog: `HEAD@{1}: branch: Reset to origin/live-defi-rollout`), orphaning it. It survives only in slot
  9's reflog (`HEAD@{2}`). The commit fixes the exact bug class already found + fixed 4x in `delta_one` across
  2026-07-27/28 (see the related issue doc) inside
  `features_service/volatility/core/{dependency_checker,data_loader}.py` — currently latent (volatility's
  `ASSET_GROUP_CHOICES` doesn't include PREDICTION yet) but would break the moment PREDICTION is added, identically to
  delta_one's history.
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [features-service, volatility, dependency-checker, bucket-naming, prediction, orphaned-commit, slot-9, git-reflog]
related:
  [
    /plans/active/issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-08-02
priority: P2
parent_epic: infrastructure_master
source: "review agent (slot 1, agt-e85468) + main agent (agt-cb1851), chat thread 2026-08-02 12:13-12:19Z"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# features-service volatility PREDICTION-bucket fix is orphaned in slot 9's local reflog

## What I found

Slot 9's local `features-service` clone (`.tabs/9/features-service`) contains a real, fully-formed commit — `272de118`
(`fix(volatility): route MDPS market-data bucket resolution through shared PREDICTION-aware resolver`, authored
`ikennaigboaka [slot-9·planning]`, 2026-08-01 15:20:21 UTC) — that:

- is **not on `origin/live-defi-rollout`** (`git merge-base --is-ancestor 272de118 origin/live-defi-rollout` fails),
- is **not reachable from the current local branch tip either** (`git branch --contains 272de118` returns nothing;
  `git merge-base --is-ancestor 272de118 HEAD` also fails),
- survives **only in that clone's reflog**: `git reflog` shows the commit at `HEAD@{2}`, immediately followed by
  `HEAD@{1}: branch: Reset to origin/live-defi-rollout` — the local `live-defi-rollout` branch was reset back to origin
  sometime after the commit landed, discarding it from the branch (current HEAD, `8d560b86`, is origin's tip — a routine
  `chore(promote): LDR → main` backmerge, unrelated). The reset mechanism itself wasn't root-caused here (out of scope
  for this doc — doesn't change the recovery/fallback disposition below either way).

Recovery today requires `git reflog` (not `git log`) inside that exact clone, and is time-limited: an unreachable reflog
entry is subject to eventual git gc (`gc.reflogExpireUnreachable` / `gc.pruneExpire` defaults) if left uncollected, and
would be gone immediately if slot 9's clone is ever reset or recreated again.

**What the commit does**: fixes the same bug class already found and fixed 4x in `delta_one`
(`/plans/active/issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md`) — a direct
`resolve_bucket_name(kind="market-data", asset_group=...)` call that doesn't know PREDICTION resolves via a dedicated
flat yaml kind (`market-data-tick-prediction`, abbreviated `pred`) rather than a per-asset_group `market-data` dict
entry. `features_service/volatility/core/{dependency_checker,data_loader}.py` each had this same raw call — currently
unreachable because volatility's CLI `ASSET_GROUP_CHOICES` only lists CEFI/TRADFI today, but would break the moment
PREDICTION is added, exactly as it broke delta_one (4 independent call sites, fixed across `features-service@bba7de58` /
`89e3ad3b` / `306bef65`). The orphaned commit resolves the last open todo in that related issue doc.

Diff shape (`git show --stat 272de118`, 3 files, 44 insertions(+), 5 deletions(-)):

```
features_service/common/__init__.py                          | 22 +++++++++++++++++++++-
features_service/volatility/core/data_loader.py               | 12 +++++++++++-
features_service/volatility/core/dependency_checker.py        | 15 ++++++++++++---
```

It adds `features_service.common.resolve_mdps_bucket()` (next to the existing `resolve_bucket`/`resolve_bucket_uri`
cross-family helpers) and routes both volatility call sites through it — mirroring the identical `_resolve_mdps_bucket`
pattern already shipped in `features_service/delta_one/app/core/dependency_checker.py`.

**Not a false-completion risk**: the related issue doc's last todo is still correctly `- [ ]` (unchecked) — nobody
marked it done based on this commit, since it never reached origin. No doc correction needed there.

## Why it matters

- A real, working fix (same pattern already proven 4x) currently exists nowhere durable — not on origin, not on any
  branch, only in one clone's reflog. If slot 9's clone is reset again, recreated, or the reflog entry ages out, the
  work is silently lost with no record it was ever attempted, and the latent bug quietly waits to bite the moment
  PREDICTION is added to volatility's asset groups (as it did, 4 separate times, for delta_one).
- Low urgency today — the bug path is genuinely unreachable (PREDICTION isn't in volatility's `ASSET_GROUP_CHOICES` yet)
  — but the fix is cheap to land now versus re-discovering + re-fixing it under time pressure later.
- Slot 9's clone is live (per-tab-worktrees liveness rules apply) and must not be touched by another slot or an
  interrupting task — recovery can only happen from inside that clone, and only while slot 9 chooses to run it.
- **Update (main + review, 2026-08-02 ~12:26Z)**: this session has seen heavy slot-churn (multiple killed-waves of 5-6
  slots at once). That makes the realistic loss vector NOT git's ~2-week gc window but slot 9's clone itself being reset
  or reassigned before anyone actions this todo — which takes the reflog with it immediately. That demotes
  cherry-pick-from-reflog to an opportunistic shortcut rather than the primary plan, and promotes re-implement-from-spec
  (below) to primary, since it's slot-independent and dispatches to any DATA worker via normal PlanRegenLoop. Bumped P3
  → P2 on that basis. No backlog `target_slot` affinity is being set for this reason too — pinning to slot 9 buys
  nothing once the primary path no longer depends on that specific clone, and staying off backlog.yaml keeps this clear
  of the hand-edit-backlog rule (RULES.md §4).

## Recommended decision

- [ ] [DATA] P2. **Primary path — re-implement from spec** (slot-independent; dispatches to any DATA worker via normal
      PlanRegenLoop): in `features-service`, add `features_service.common.resolve_mdps_bucket()` next to the existing
      `resolve_bucket`/`resolve_bucket_uri` helpers, and route both
      `features_service/volatility/core/dependency_checker.py` and `.../data_loader.py`'s direct
      `resolve_bucket_name(kind="market-data", asset_group=...)` calls through it — mirrors the identical,
      already-shipped `_resolve_mdps_bucket` pattern in `features_service/delta_one/app/core/dependency_checker.py` (see
      "What I found" above for the exact shape — 3 files: `common/__init__.py` +
      `volatility/core/{dependency_checker,data_loader}.py`, 44 insertions/5 deletions). Add/adapt a regression test
      mirroring delta_one's `TestResolveMdpsBucketPredictionAbbreviation` coverage. Ship via the normal Pass-1
      `bash scripts/quality-gates.sh` → Pass-2 `bash scripts/quickmerge.sh "<msg>" --agent --files '<paths>'` flow.
      **Opportunistic shortcut — cherry-pick from slot 9's reflog, IFF it still applies**: before re-implementing by
      hand, check `.tabs/9/features-service`'s `git reflog | grep 272de118` — if the commit is still there (i.e. slot
      9's clone hasn't been reset/reassigned since), `git cherry-pick 272de118` saves rewriting the diff; verify it
      applies cleanly and tests pass before shipping. This is opportunistic ONLY — do not wait on slot 9 or block on it
      being available; if the reflog entry is gone, just take the primary path above. No backlog affinity is set for
      this todo (deliberate, see "Why it matters").
