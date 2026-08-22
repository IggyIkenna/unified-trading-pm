---
doc_type: issue
title:
  deployment-service basedpyright ratchet (1259) broken fleet-wide, root cause UNKNOWN — 1261 measured, zero
  deployment-service source changed, dependency-backmerge theory FALSIFIED by isolated-worktree bisection
summary: >-
  Measured 2026-08-15 in slot 15: `basedpyright deployment_service/` reports 1261 errors, 2 over the checked-in
  `BASEDPYRIGHT_MAX_ERRORS=1259` ratchet in `deployment-service/scripts/quality-gates.sh:134`. This BLOCKS every
  quickmerge for deployment-service until fixed. `git diff` between the last confirmed-green commit
  (`deployment-service@bf69b2b289`) and current HEAD (`7939f176`) touches only a Dockerfile + 2 shell launcher
  scripts — zero Python — so the regression is NOT in deployment-service's own source. **The original "3-known-deps
  backmerge" theory below is FALSIFIED** (see "Update 2026-08-15" in the body): an isolated-worktree bisection pinned
  all 3 editable LOCAL_DEPS (`unified-api-contracts`, `unified-trading-library`, `deployment-api`) to their
  pre-backmerge commits simultaneously and the count stayed at 1261 unchanged. Root cause is genuinely UNKNOWN as of
  this correction (2026-08-19, plan-reconcile observability_master — this title/summary previously stated the
  falsified theory as settled fact, already flagged twice by prior `/plan-reconcile` passes and left unfixed; see
  `plan_reconciler_findings_cross_cutting_2026_08_16.md` + `..._08_18.md`) — needs a fresh bisection sweep beyond the
  3 known LOCAL_DEPS.
status: open
nature: issue
asset_group: [ci] # corrected 2026-08-19 (ag-closeout-audit cross-cutting, Phase 1 Workflow) -- was [cross-cutting]; a deployment-service CI/quality-gate ratchet break, own tags already say "ci", not data-pipeline scope
stage: [meta]
repos: [deployment-service, unified-api-contracts, unified-trading-library]
scope: [engineer]
tags: [basedpyright, type-check, ratchet, ci, dependency-drift, blocking]
related:
  [
    /plans/active/issues/dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md,
    /plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md,
  ]
created: 2026-08-15
last_updated: 2026-08-15T02:15Z
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Found while shipping Todo 2 of dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md (truncated-sweep
  detection) — quality-gates.sh failed on type-check with zero deployment-service files touched by my own diff.
context_scope:
  [
    deployment-service/scripts/quality-gates.sh,
    deployment-service/deployment_service/shard_builder.py,
    deployment-service/deployment_service/shard_calculator.py,
    deployment-service/deployment_service/smoke_test_framework.py,
    deployment-service/deployment_service/sports_latency_observation.py,
    /codex/06-coding-standards/quality-gates.md,
  ]
---

# deployment-service basedpyright ratchet broken by a dependency backmerge, not by deployment-service's own code

## What was measured (2026-08-15, slot 15)

1. `deployment-service`'s own `bash scripts/quality-gates.sh --no-fix` (task `bachblch7`, this session) passed fully —
   `✅ ALL QUALITY GATES PASSED (303s)` — on the tree that became `deployment-service@bf69b2b289`.
2. Minutes later, a background `slot-cron-ff-pull.sh`-style sync advanced this checkout's `deployment-service` HEAD to
   `7939f176` ("Merge remote-tracking branch 'origin/main' into _backmerge"). `git diff bf69b2b289..HEAD --stat` shows
   **only**: `Dockerfile` (1 line), `launch-backfill-defi-legacy-datatype-fold-vm.sh` (12 lines),
   `launch-sport-residue-blank-venue-purge-vm.sh` (new file, launcher script). **Zero `.py` files.**
3. A fresh `bash scripts/quality-gates.sh --no-fix` run on this new HEAD failed type-check:
   `❌ Type check FAILED — 1261 error(s) > BASEDPYRIGHT_MAX_ERRORS=1259`.
4. Reproduced standalone, deterministically, twice — including once against a brand-new empty `BASEDPYRIGHT_CACHE_DIR`
   (rules out cache-contention from a concurrent peer session in this same slot, per the slot-collision warning active
   this session): `.venv/bin/basedpyright deployment_service/` → **1261 errors, 0 warnings** both times. Every reported
   error is in `shard_builder.py`, `shard_calculator.py`, `smoke_test_framework.py`, or `sports_latency_observation.py`
   — files `git log -1 -- <those 4 paths>` shows were last touched by an unrelated, much older commit (`138c82d1`), not
   by anything in the `bf69b2b289..HEAD` range.

## Root cause — editable-installed local deps, not deployment-service source

`deployment-service`'s `LOCAL_DEPS` are path/editable installs of `unified-api-contracts` and `unified-trading-library`
(not pinned wheels) — so basedpyright's inference for any deployment-service call site into those packages depends on
THEIR current on-disk source, not a version pin deployment-service's own git history would show. Both moved HEAD in the
same window the backmerge landed:

- `unified-api-contracts` → `85caa70a` at `2026-08-15T01:20:55Z`. Candidate commits in that window: `53a5adc7`
  "feat(registry): LST token address SSOT — migrate 8 cited addresses..." and `bed96aa0` "fix(registry): drop eETH/rsETH
  from the LST address SSOT...".
- `unified-trading-library` → `bd587735` at `2026-08-15T01:23:34Z`. Candidate commit: `ff9cb5f8`
  "fix(pipeline-e2e-check): suffix GCS report blob with asset_group...".

**Update 2026-08-15 (same day, later pass) — all 5 candidates checked so far are RULED OUT.** Read the full diffs of the
original 3 candidates plus 2 more found by actually tracing the flagged files' import chains
(`shard_builder.py`/`shard_calculator.py` → `config_loader.py` → `unified_api_contracts.VenueMapping` +
`market_data_categories`; `smoke_test_framework.py`/`sports_latency_observation.py` →
`unified_trading_library.StorageClient`):

| Commit                             | Repo | What it actually changed                                                                                                   | Verdict                                                       |
| ---------------------------------- | ---- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| `unified-api-contracts@53a5adc7`   | UAC  | New file `registry/lst_token_addresses.py` (additive only, unrelated module)                                               | Ruled out — deployment-service never imports this module      |
| `unified-api-contracts@bed96aa0`   | UAC  | Same new file, 10-line data edit                                                                                           | Ruled out — same reason                                       |
| `unified-trading-library@ff9cb5f8` | UTL  | `pipeline_e2e_check/report.py` (unrelated module, not imported by the 4 files)                                             | Ruled out                                                     |
| `unified-trading-library@b12ceab9` | UTL  | `StorageClient.download_bytes_range()` gains a fully-typed optional `generation` kwarg                                     | Ruled out — fully annotated, predates the window (2026-08-10) |
| `unified-api-contracts@316002f1`   | UAC  | `VenueMapping`/`market_data_categories`: adds `"PACIFICA-SOLANA"` string literals to existing `list[str]`/`dict[str, str]` | Ruled out — pure data-literal additions, no signature change  |

None of these touch a return type, parameter type, or class attribute annotation. Basedpyright's Unknown cascade in the
4 flagged files traces to `ConfigLoader`'s `.get(...)` calls (shard_builder.py) and `StorageClient` methods
(smoke_test_framework.py/sports_latency_observation.py) — but the classes themselves (`ConfigLoader`, `VenueMapping`,
`StorageClient`) were NOT touched by any commit in the backmerge window. **The "single culprit commit in a known time
window" theory this doc started with is not panning out** — ad-hoc commit-message-driven guessing has now cost real time
across 2 passes without a hit.

**Recommended methodology for the next attempt — bisection, not more guessing, and NOT on this shared checkout.**
`unified-api-contracts`/`unified-trading-library` are editable/path-installed LOCAL_DEPS shared by every slot session
via this same checkout (per the workspace's multi-agent-safety rule) — checking out an old commit in either repo here
would silently change what every OTHER concurrent process reading them sees. Do this instead: clone (or
`git worktree add`) an ISOLATED copy of both dependency repos, point a throwaway venv's editable install at that
isolated copy, then bisect by checking out each dependency repo at successive commits in the
`2026-08-14T11:40Z..2026-08-15T01:24Z` window (arming commit through the backmerge) and re-running
`basedpyright deployment_service/` after each, until the count flips from <=1259 to 1261. That pins the exact commit
without disturbing this shared checkout.

**Update 2026-08-15 (isolated-worktree bisection executed — the "3-known-deps" theory is FALSIFIED.** Ran the
methodology above for real: `git worktree add` isolated copies of `unified-api-contracts`, `unified-trading-library`,
AND a third editable LOCAL_DEP this doc had never checked — `deployment-api`
(`deployment-service/scripts/quality-gates.sh:48: LOCAL_DEPS=(deployment-api)`) — plus an `rsync`'d copy of
`deployment-service/.venv` with its three `_editable_impl_*.pth` files repointed at the isolated worktrees (so nothing
in the shared checkout or its venv was ever touched). Confirmed the isolated setup reproduces the live result first
(1261, matching the shared checkout exactly), then pinned each dependency to its last commit **before the arming
window** (`2026-08-14T11:40Z`): `unified-api-contracts@acbd0882`, `unified-trading-library@dd193279`,
`deployment-api@7f8fb83`.

| Combination                                           | `basedpyright deployment_service/` result |
| ----------------------------------------------------- | ----------------------------------------- |
| All 3 at current (post-backmerge) HEAD                | 1261 errors                               |
| `unified-api-contracts` pre-window, other 2 current   | 1261 errors                               |
| `unified-trading-library` pre-window, other 2 current | 1261 errors                               |
| **All 3 pinned pre-window simultaneously**            | **1261 errors — unchanged**               |

Pinning all three known editable LOCAL_DEPS to before the arming window does NOT recover the 1259 ratchet ceiling.
`basedpyright` is pinned identical (`==1.38.2`, exact hash match, both at `bf69b2b289` and current — confirmed via
`uv.lock`), and `deployment-service`'s own diff `bf69b2b289..HEAD` is still empty for `.py`/config files (Dockerfile + 3
shell launcher scripts only). **This means the doc's original premise — a dependency backmerge in the `11:40Z..01:24Z`
window regressed the count — does not hold**: reverting every plausible culprit in that window, together, produces the
identical error count as leaving them all current. Two live leads for whoever picks this up next, not yet chased down
(ran out of turn budget after the elimination, and this is now squarely a design/measurement-methodology question rather
than a code hunt):

1. `.qg_last_passed_sha` / `.qg_content_sentinel` (gitignored, present in this checkout, timestamped `01:11` — _before_
   the 01:20-01:23 backmerge-completion commits) suggest `quality-gates.sh`'s content-sentinel cache was primed around
   that time. Worth checking whether the "ALL QUALITY GATES PASSED (303s)" run this doc's Root Cause section cites for
   `bf69b2b289` was a **live basedpyright execution** or a **sentinel cache HIT** reusing an earlier verified-good hash
   — `qg-common.sh`'s `_qg_editable_sibling_hash()` does fold in every editable sibling's live `git rev-parse HEAD` +
   `git diff HEAD` generically (all `*.dist-info/direct_url.json` with `"editable": true`, which covers `deployment-api`
   too, not just the 2 originally suspected), so a stale-hash explanation would need the sentinel mechanism itself to
   have a gap, not just an unhashed sibling.
2. Alternatively the true baseline may simply never have been a live-verified 1259 at exactly `bf69b2b289` — worth
   re-deriving it from the last commit where `.qg_last_passed_sha` demonstrably matched a genuine full basedpyright run,
   rather than trusting the doc's original claim.

## Why this matters

`BASEDPYRIGHT_MAX_ERRORS=1259` is a hard-fail gate in `deployment-service/scripts/quality-gates.sh` — every quickmerge
for deployment-service is blocked until this is back at or under 1259. This is a genuinely different failure class from
the usual "someone's source regressed the ratchet" case the mechanism is designed for: an EDITABLE-INSTALL dependency
changed shape without deployment-service's own diff recording anything, so `git bisect` inside deployment-service alone
cannot find it — the fix has to be sought in the two dependency repos.

## Todos

- [x] [CODE] P1. Isolated-worktree bisection executed 2026-08-15 (see Update in Root Cause section) — pinned all 3
      editable LOCAL_DEPS (`unified-api-contracts`, `unified-trading-library`, and previously-unchecked
      `deployment-api`) to pre-arming-window commits simultaneously, in an isolated `git worktree add` + `rsync`'d venv
      copy that never touched the shared checkout. Result: still 1261, unchanged. **This DoD ("bisect until the count
      flips 1259→1261") could not be met — the count never flips, because the dependency-backmerge premise itself
      appears to be wrong.** Closing this todo as "methodology executed, hypothesis falsified" rather than leaving it
      open against a premise the evidence no longer supports; the 2 follow-on leads (sentinel-cache-hit vs.
      never-truly-1259) are new open questions, tracked below as Todo 3, not a continuation of this bisection.
- [ ] [DIAG] P2. Run a deeper bisection beyond the 3 known editable LOCAL_DEPS (`unified-api-contracts`,
      `unified-trading-library`, `deployment-api`) to find the actual cause of the 1259→1261 basedpyright regression —
      do NOT raise `BASEDPYRIGHT_MAX_ERRORS` yet. Per D13 ruling (2026-08-22): ratchets-only-go-down is a HARD RULE and
      a cross-slot measurement (slot 5, same day) shows 1259 IS reachable on a current tree — raising the ratchet is a
      last resort only, not the next step. Two guessing passes (5 candidate commits) plus a rigorous isolated-worktree
      elimination (all 3 known editable deps pinned pre-window simultaneously) have failed to find the code-level
      culprit so far; the ratchet's last GENUINE full-run verification was commit `0aeb925f`, ~23 minutes before the
      disputed UAC/UTL backmerge-completion commits even landed — worth re-deriving from there.

      **CROSS-SLOT MEASUREMENT 2026-08-15 (slot 5) — READ BEFORE SPENDING THE OPERATOR DECISION.** In slot 5's
          checkout the count is **1259, not 1261** — at `deployment-service@657c897b`, `unified-api-contracts@e8a55ca8`,
          `unified-trading-library@624b2cf607`. Reproduced **twice against two separately-created empty
          `BASEDPYRIGHT_CACHE_DIR`s** (same cache-contention control this doc used to establish 1261), both
          `1259 errors, 0 warnings, 0 notes`. Enforcement is `[ "$ERROR_COUNT" -gt "$_max_bp_errors" ]`
          (`scripts/quality-gates-base/base-service.sh:1368`), so exactly-1259 takes the `elif` warn branch at :1372 and
          **PASSES** — deployment-service shipping is not blocked from this slot. This does NOT mean slot 15 now reads
          1259: the two slots are independent clones with independent venvs and independent dep HEADs, and the count is
          the thing under dispute, so it must be re-measured there rather than assumed. What it does establish is that
          **1259 is reachable on a real current tree**, which supports this doc's original editable-dep-inference root
          cause (the count tracks dep state, with zero deployment-service `.py` changed) even though Todo 1's bisection
          could not pin the specific commit — a pinning failure is not evidence the premise is wrong when the count is
          demonstrably dep-state-dependent in both directions. **Therefore option (a) (raise the ratchet to 1261) should
          not be actioned yet** — it would permanently relax a gate to accommodate a condition that is already absent on
          another current tree, and the ratchet-only-goes-down norm exists precisely to stop that. Cheaper next step for
          slot 15 before escalating: `git pull --ff-only` all three editable deps, then re-measure with a fresh cache dir.
          Provenance: measured while landing an unrelated deployment-service change from slot 5.

- [x] [CODE] P2. Determine whether the `bf69b2b289` "ALL QUALITY GATES PASSED" run that established the 1259 baseline
      was a live basedpyright execution or a `quality-gates.sh` content-sentinel cache HIT (`.qg_last_passed_sha` /
      `.qg_content_sentinel`, gitignored, present in this checkout timestamped `01:11` — before the backmerge-completion
      commits at 01:20-01:23). If it was a cache hit reusing an earlier genuinely-verified hash, re-derive the true
      last-live-verified baseline from history instead of trusting `bf69b2b289`'s claimed count. See the Root Cause
      section's Update for the 2 concrete leads. DoD: a stated determination (cache-hit vs. genuine) with evidence, and
      if cache-hit, the corrected true baseline commit + count. — ✅ **CACHE HIT, CONFIRMED** (2026-08-15, slot 15).
      `.qg_last_passed_sha` (read fresh, this pass) currently records `0aeb925fc371efd2aa63fc467c1f911749c13c3a` (commit
      date `2026-08-15T00:57:58Z`, "Merge remote-tracking branch 'origin/main' into \_backmerge") — **not** `bf69b2b289`
      (`2026-08-15T01:12:12Z`). Per `base-service.sh:4550-4557` (the "H5" comment), this file is deliberately NEVER
      refreshed on a content-sentinel HIT — only on a genuine full run — so its current content IS the last commit a
      live full run actually passed on. `git merge-base --is-ancestor 0aeb925f bf69b2b289` confirms ordinary same-branch
      ancestry (not a fluke/rewrite). This directly falsifies the doc's original premise that the verified-green run
      happened "on the tree that became `bf69b2b289`" — it happened one commit earlier, at `0aeb925f`. **Follow-on check
      — does this change the root cause?** `0aeb925f..bf69b2b289` is NOT `.py`-empty like `bf69b2b289..HEAD` is — it's
      exactly the revocation-release identity fix from `dp_revocation_release_never_resolves_identity_2026_08_15.md`
      (`meta_watchers.py` + `cli.py` + test file). Checked directly:
      `basedpyright deployment_service/data_pipeline_monitors/meta_watchers.py deployment_service/data_pipeline_monitors/cli.py`
      → 6 errors, **all** in `cli.py:399-411` (pre-existing `CloudSchedulerClient`/`reportAny` typing, nowhere near the
      diff's touched lines 639/699), **zero** in `meta_watchers.py`. The revocation-release fix is basedpyright-clean —
      it is not the source of the 1259→1261 gap. **Exact live-verified count at `0aeb925f` — not recoverable, noted as a
      genuine gap, not chased further**: the sentinel files store a content hash, not an error count, and there is no
      accessible CI log for that exact execution from this session. Attempted an isolated `git worktree add`
      re-measurement (mirroring Todo 1's sanctioned methodology) — produced 3569 errors, wildly inconsistent with
      1259/1261 and clearly an environment artifact (a bare worktree outside the venv's expected sibling layout breaks
      third-party/stub resolution, not a real count); discarded, worktree removed (`git worktree remove --force` +
      `prune`, confirmed clean via `git worktree list`). A trustworthy re-measurement would need a fully isolated venv
      provision at `0aeb925f`, out of scope for this todo's DoD (which only required cache-hit-vs-genuine + corrected
      baseline commit, both now answered).

**2026-08-15 (agt-d1be49, slot 18) — this now ALSO blocks a live DP-MANIFEST-001 root-cause fix.** Hit this same
`1261 > 1259` failure shipping `deployment-service/scripts/recovery/relaunch_consolidator.py` +
`data_pipeline_monitors/escalation.py` (the CONSOLIDATOR_DOWN actuator built the wrong Cloud Run job name —
`manifest-consolidator-{ag}` vs the real `uts-prod-manifest-consolidator-{kind}-{ag}` — every real relaunch 404'd since
inception). `git fetch origin live-defi-rollout` on `unified-api-contracts`/`unified-trading-library` showed ZERO
incoming commits (already current); `deployment-api` had 2 incoming (a consolidator staleness-budget bump + a Docker
digest pin, `3a5d3cc..f6c1d70`) — pulled it, re-ran `basedpyright deployment_service/` with a fresh
`BASEDPYRIGHT_CACHE_DIR` → still `1261 errors, 0 warnings, 0 notes`, unchanged. One more negative data point against a
findable single culprit commit. **Not escalating a duplicate — the operator-decision todo above already covers this**;
noting it here so the decision's cost (a P0 truncated-sweep fix AND this P1 alerting-actuator fix both sitting
unshippable) is visible. My own escalation's underlying incident is already resolved LIVE (manual
`relaunch_consolidator.py --asset-group tradfi --service-kind instruments` invocation confirmed the Cloud Run execution
SUCCEEDED, tradfi consolidator heartbeat should refresh next sweep) — only the code fix (so the NEXT CONSOLIDATOR_DOWN
finding auto-recovers instead of re-escalating) is blocked on this ratchet.

## Evidence

- `deployment-service@bf69b2b289..HEAD` diff: `Dockerfile | 2 +-`, 2 shell launcher scripts, 0 `.py` files.
- `.venv/bin/basedpyright deployment_service/` → `1261 errors, 0 warnings, 0 notes`, reproduced twice (default cache +
  fresh isolated cache dir), both from `deployment-service` HEAD `7939f176`.
- `unified-api-contracts` HEAD `85caa70a` (2026-08-15T01:20:55Z), `unified-trading-library` HEAD `bd587735`
  (2026-08-15T01:23:34Z) — both editable-installed LOCAL_DEPS of deployment-service.
- Isolated-worktree elimination (2026-08-15, this checkout untouched): `unified-api-contracts@acbd0882` +
  `unified-trading-library@dd193279` + `deployment-api@7f8fb83` (all 3 pre-arming-window) against `deployment-service`
  current HEAD → still `1261 errors, 0 warnings, 0 notes`. `basedpyright==1.38.2` pinned byte-identical (exact hash
  match) in `uv.lock` at both `bf69b2b289` and current HEAD.
- **Todo 3 (2026-08-15, slot 15)**: `.qg_last_passed_sha` head line = `0aeb925fc371efd2aa63fc467c1f911749c13c3a`
  (`2026-08-15T00:57:58Z`), read directly from the gitignored file in this checkout — not `bf69b2b289`
  (`2026-08-15T01:12:12Z`). `git merge-base --is-ancestor 0aeb925f bf69b2b289` → true.
  `git diff 0aeb925f..bf69b2b289 --stat` → `cli.py`, `meta_watchers.py`, `tests/unit/test_data_pipeline_monitors.py`
  (the revocation-release identity fix). `basedpyright deployment_service/data_pipeline_monitors/{meta_watchers,cli}.py`
  → 6 errors, all in `cli.py:399-411`, 0 in `meta_watchers.py`. Isolated-worktree re-measurement at `0aeb925f`
  (`git worktree add`) → 3569 errors, discarded as an environment artifact (bare worktree, no isolated venv provision)
  and removed (`git worktree remove --force` + `prune`).

## Deferred work after 2026-08-15

| Item                                                                                              | State / why deferred                                                                                                                                                                                                                                                                    | Blocked on                            |
| ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| Todo 2 of `dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md` (truncated-sweep signal) | **Code + tests WRITTEN, compile-checked, uncommitted** in `deployment-service` working tree (`exit_code_fleet_monitor.py` + `tests/unit/test_data_pipeline_monitors.py`) — cannot ship, quickmerge requires a green `quality-gates.sh` and this ratchet break is unrelated-but-blocking | This doc's Todo 2 (operator decision) |
| A trustworthy exact live error count at baseline commit `0aeb925f`                                | Would need a fully isolated venv provision (not a bare worktree) to reproduce faithfully — the quick worktree attempt gave an unreliable 3569; not pursued further since it wasn't required to close Todo 3's DoD                                                                       | Nobody — real work, low priority      |

**Recommended next item**: Todo 2 (operator decision) — it unblocks ALL deployment-service shipping immediately,
independent of whether Todo 3's cache-hit investigation ever resolves the "why."

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:0196a6655c035b95]: KEEP-NA, valid -- Sole remaining todo is explicitly tagged [OPERATOR] with a BLOCKED-OPERATOR-DECISION marker: whether to relax the BASEDPYRIGHT_MAX_ERRORS ratchet ceiling from 1259 to 1261 against the workspace's own 'ratchet-only-goes-down' norm, or hold all deployment-service quickmerges. Two guessing passes plus a rigorous isolated-worktree bisection all failed to find a code-level culprit, and a cross-slot measurement note narrows but does not resolve the decision (1259 is reachable on another current tree, arguing against relaxing the ratchet yet).
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **2026-08-22 — ruling D13 (Basedpyright ratchet 1259 vs 1261)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Deeper bisection first — ratchets-only-go-down is a HARD RULE and a
  cross-slot measurement shows 1259 is reachable on a current tree; raise only as last resort. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
