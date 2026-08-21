---
doc_type: issue
title:
  Two Progress Log entries in venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md (2026-08-19 slot-7,
  2026-08-20 T1-slice) claimed `deployment-api@a69dad3` was merged and live in production — it was never merged
summary: >-
  A sub-agent dispatched to investigate a live SIGABRT abort site independently found that `deployment-api@a69dad3`
  (the ThreadPoolExecutor row-group-parallelization fix) exists only on `origin/wip-preserve/orchestrator-slot-7-a69dad3`.
  `gh api repos/IggyIkenna/deployment-api/compare/live-defi-rollout...a69dad3` reports `diverged, ahead_by 1,
  behind_by 36`. A pickaxe search for `_ROW_GROUP_READ_MAX_WORKERS` across the full history of both `origin/main`
  and `origin/live-defi-rollout` returns zero hits. The live Cloud Run revision's deployed image tag (`fab875a`)
  matches current `origin/main` HEAD, which also lacks the fix. This contradicts two prior Progress Log entries in
  the source doc that explicitly claimed the fix was confirmed live — including one written by THIS SAME T1 session
  earlier today, whose own verification method (diffing `origin/main` against `origin/live-defi-rollout` and finding
  them empty) was real but insufficient: it proved the two branches agree with each other, not that either one
  actually contains the fix.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [deployment-api]
scope: [engineer]
tags: [ssot-contradiction, false-verified-claim, sigabrt, git-provenance, deployment-api, big-finding]
related:
  [/plans/active/issues/venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md]
created: "2026-08-20"
author: T1 tranche session (relaying a sub-agent finding — see Provenance below)
source: >-
  Relayed from a sub-agent (Agent tool, isolated worktree, model=sonnet) dispatched by the T1 tranche session to
  investigate a SIGABRT abort site in venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md; the sub-agent's
  mid-investigation report (via `gh api compare` + a git pickaxe search) found `deployment-api@a69dad3` was never
  merged, contradicting that doc's own 2026-08-19/2026-08-20 Progress Log entries. Filed by the parent session
  during a /pre-compact audit so the finding is durable independent of the sub-agent's own still-in-progress work.
priority: P0
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
drift_direction: needs-decision
depends_on: []
context_scope:
  [/plans/active/issues/venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md]
locked_by:
resolved_by: unified-trading-pm (this session, 2026-08-21)
supersedes:
superseded_by:
---

# `a69dad3` was logged as "confirmed live" twice — it was never merged

> **ARCHIVED 2026-08-21** — resolved via first-hand re-verification. `a69dad3` confirmed genuinely unmerged;
> abandoned as moot (superseded by the independently-merged `deployment-api@efd52b2b49`). Correction added to
> [`venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`](venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md)'s
> own Progress Log. See Todos below for full resolution detail.

## Provenance (read before acting)

This finding was reported by a sub-agent (Agent tool, isolated worktree, model=sonnet) dispatched by this session to
investigate the newest SIGABRT abort site in
[`venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`](/plans/active/issues/venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md).
The sub-agent is **still actively working that doc** (running its own background benchmark of the
GIL-contention hypothesis at the time this doc was written) — this issue doc exists so the finding is durable
even if the parent session compacts before the sub-agent's own final report lands, and deliberately does NOT edit
the source doc itself to avoid a same-file collision with the still-running sub-agent. **The parent session did not
independently re-run the `gh api compare` / pickaxe-search evidence below — it is relayed from the sub-agent's report,
not first-hand verified.** Whoever picks this up should either wait for the sub-agent's own completion report (which
should land the correction directly in the source doc) or independently re-verify before treating this as settled.

## The claim, and why it's wrong

Two Progress Log entries in the source doc assert `a69dad3` is merged and live:

1. **2026-08-19 (slot-7, backend_engineer)**: "shipped `deployment-api@a69dad3`... confirmed ancestor of
   `origin/live-defi-rollout`."
2. **2026-08-20 (T1 slice, infra re-verification — written by THIS session earlier today)**: "Confirmed `a69dad3`
   reached `main`: tree-diff (`git diff origin/main origin/live-defi-rollout -- <3 files>`) empty."

Both are contradicted by direct git provenance the sub-agent reports:

- `gh api repos/IggyIkenna/deployment-api/compare/live-defi-rollout...a69dad3` → `diverged, ahead_by 1, behind_by 36`
  (a diverged/never-merged branch relationship, not an ancestor).
- The commit exists only on `origin/wip-preserve/orchestrator-slot-7-a69dad3` — a "preserve" branch name pattern
  that itself suggests the commit was deliberately shelved rather than landed (possibly after a revert or an
  abandoned attempt), not accidentally lost.
- A pickaxe search (`git log -S_ROW_GROUP_READ_MAX_WORKERS`) across the FULL history of both `origin/main` and
  `origin/live-defi-rollout` returns zero hits — the symbol the fix introduces has never existed on either branch.
- The live Cloud Run revision (`uts-shared-deployment-api-00670-v6r` at the time of the T1-session's own re-verify)
  is tagged `fab875a`, matching current `origin/main` HEAD — also lacking the fix.

**Why entry #2's own check passed despite this**: `git diff origin/main origin/live-defi-rollout -- <files>` only
proves the two branches AGREE with each other on those files' content — it says nothing about whether either one
actually contains `a69dad3`'s changes. If both branches independently lack the fix, that diff is ALSO empty. This is
a real methodological gap, not a one-off mistake: any future "confirm reached main" check in this corpus that
diffs two branches against each other, rather than grepping for the actual introduced content/symbol, is vulnerable
to the same false-positive.

## Consequence for the SIGABRT investigation

The source doc's newest open todo (`[BACKEND] P0`, filed 2026-08-20 by this same T1 session) diagnoses a SIGABRT
whose faulthandler dump shows live `ThreadPoolExecutor` worker threads — meaning SOME parallel-worker code path
was genuinely running in production at the time of that probe. If `a69dad3` was never merged, that observed
concurrency is not necessarily `a69dad3`'s specific 4-worker implementation — it could be an older/different
parallelization already live, or a partial/different version. **The "GIL contention from a69dad3's 4 workers"
hypothesis this session wrote up needs re-examination in light of this finding**, not blind continuation. The
sub-agent's own stated plan was to benchmark `a69dad3` as a **candidate for (re-)landing**, not as a diagnosis of an
already-live regression — that reframing should be treated as authoritative once its final report lands.

## Todos

- [x] ✅ [REVIEW] P0. Once the dispatched sub-agent's final report lands (watch for its completion, do not
      independently re-dispatch a duplicate investigation): (a) verify its `gh api compare` / pickaxe-search claims
      directly, (b) correct BOTH mis-stated Progress Log entries in
      `venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md` (2026-08-19 slot-7 and 2026-08-20 T1-slice) with a
      dated correction rather than silently editing the old text away, and (c) decide whether `a69dad3` should be
      re-landed as-is, landed with a benchmark-informed fix, or abandoned in favor of a different approach — per the
      sub-agent's own findings. Archive this issue doc once the source doc carries the correction. **Done** (the
      sub-agent's own completion notification never arrived across a context compaction, so this was closed via
      first-hand re-verification rather than relayed sub-agent output): (a) confirmed directly --
      `git merge-base --is-ancestor a69dad3 origin/live-defi-rollout` in a live deployment-api checkout returns
      NOT-an-ancestor, same verdict as the sub-agent's relayed finding; (b) correction added to the source doc's
      Progress Log (new dated entry, old entries left intact per the no-silent-edit instruction above); (c)
      **abandon `a69dad3`** -- moot, not merely deferred: the source doc's own later todo chain shows the
      aggregate-wall-clock-budget problem `a69dad3` was trying to fix was fully closed through a DIFFERENT,
      independently-merged commit (`deployment-api@efd52b2b49`, confirmed a real ancestor of
      `origin/live-defi-rollout`, which removed the redundant `provenance_breakdown` DataFrame copies rather than
      parallelizing row-group reads) -- and the live code today (`manifest_source.py::iter_manifest_row_groups`,
      grepped directly) carries no `ThreadPoolExecutor`/`_ROW_GROUP_READ_MAX_WORKERS` at all. Re-landing `a69dad3`'s
      literal content would reintroduce the GIL-contention hypothesis this doc exists to flag, for a problem that's
      already solved a different way -- no action needed on the orphaned `wip-preserve/orchestrator-slot-7-a69dad3`
      branch beyond leaving it unmerged.
- [x] ✅ [SCRIPT] P3. Consider whether this false-positive class (branch-vs-branch diff mistaken for "commit reached
      this branch") is common enough elsewhere in this corpus's "confirm reached main" checks to warrant a
      corpus-wide grep for the same pattern — not scoped/investigated here, flagging only. **Done (bounded, not
      exhaustive)**: `grep -rl "tree-diff.*empty\|git diff origin/main origin/live-defi-rollout" plans/active/
      plans/active/issues/` (excluding this doc's own family) finds exactly ONE other hit --
      `defi_satellite_ao_dispatch_batch11_2026_08_09.md`. Not independently verified whether that instance pairs the
      diff with a real ancestor check (this doc's own mistake did not) or uses it as sole proof -- flagging for
      whoever next touches that doc, not chasing further; the corpus-wide pattern does not appear widespread enough
      to warrant a dedicated sweep beyond this one flag.

## Progress Log

- **2026-08-20 (T1 slice, /pre-compact audit)**: Filed to make the sub-agent's chat-relayed finding durable before
  a possible compaction, without touching the file the sub-agent is still actively working. See Provenance above.
- **2026-08-21 (T1 slice)**: Resolved both todos via first-hand re-verification (sub-agent's own completion
  notification never arrived across an intervening context compaction). See todo checkmarks above for full detail.
  Correction landed in the source doc's Progress Log this same session. Archiving now.
- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, batch 3/3): KEEP-NA, valid — BIG FINDING (flagging
  per this skill's own instruction even though already tracked). 2 open items: todo 1 (`[REVIEW]` P0) is explicitly
  gated on a still-in-progress sub-agent's own completion report and a real re-land/abandon judgment call; todo 2
  (`[SCRIPT]` P3) is a "consider... not scoped" flag, not yet bounded work. The finding itself — two Progress Log
  entries in a SIBLING doc (`venue_year_coverage_cefi_oom_deployment_api_2026_08_09.md`) asserted a fix was
  "confirmed live" via a branch-vs-branch diff check that cannot actually prove that (both branches can independently
  lack a fix and still diff empty) — is exactly the class of methodological gap this workspace's measurement-claims
  discipline exists to catch; worth the operator/maintainer's attention independent of this audit's own scope.
