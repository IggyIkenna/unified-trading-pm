---
doc_type: issue
title: >-
  Uncommitted, unexplained full revert of features-service@6b2282c5 (HYPERLIQUID derivative_ticker CEFI-bucket
  resolution fix) found staged in the features-service-clean-check worktree -- stashed, not applied; fix itself is now
  live-verified correct in production
summary: >-
  While working delta_one_candle_loader_no_pass_through_path_defi-003 (2026-08-03), found staged (not committed) changes
  in the `features-service-clean-check` worktree that mechanically DELETE
  `_DERIVATIVE_TICKER_CROSS_ASSET_GROUP_VENUES`/`_resolve_passthrough_source` from `_passthrough_loader.py` and all 8
  associated unit tests from `test_data_loader.py` -- a full revert of `features-service@6b2282c5` (the `[BACKEND] P1`
  fix in `defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`), with NO explanatory
  comment/commit message anywhere. Stashed it rather than committing or discarding (per the DONE-GATE's "unimportant WIP
  -> slot-tagged stash" path -- it was not part of my task and I could not determine its intent). Separately, this same
  session ran extensive REAL production verification of `6b2282c5` (not just unit tests):
  `features-delta-one-defi-20260803-055145` (`EXIT_STATUS=0`) wrote 454/455 real `captured` `funding_oi` manifest
  shards, independently corroborated by slot-10's concurrent `features-delta-one-defi-20260803-055219`. So the fix this
  stash reverts is now strongly evidenced correct in production -- either the revert was an accident/aborted experiment
  (most likely, given zero rationale anywhere in the corpus), or someone found a real problem with it that was never
  written down anywhere I could find. This doc exists so that question gets a real answer instead of silently
  evaporating with the stash.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [defi, features-service, delta-one, dangling-wip, stash, git-hygiene, data-correctness]
related:
  - /plans/archive/issues/defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md
  - /plans/archive/issues/delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md
created: "2026-08-03"
source: [backlog task delta_one_candle_loader_no_pass_through_path_defi-003, slot 8]
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/archive/issues/defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md,
    features-service/features_service/delta_one/app/core/_passthrough_loader.py,
  ]
locked_by:
resolved_by:
---

# What I found

While working `delta_one_candle_loader_no_pass_through_path_defi-003`, a `git status` in my slot's
`features-service-clean-check` worktree (a linked worktree of `features-service`) showed staged, uncommitted changes I
never made. The diff (`git stash show -p`, captured before stashing) mechanically deletes:

- `_DERIVATIVE_TICKER_CROSS_ASSET_GROUP_VENUES` (the `frozenset({"HYPERLIQUID"})` constant)
- `_resolve_passthrough_source()` (the bucket/asset_group resolver it gates)
- The `_log_empty_oi_enrichment()` helper + its two call sites
- All 8 associated unit tests in `TestLoadPassthroughDay`/`TestResolvePassthroughSource`
  (`test_hyperliquid_derivative_ticker_queries_cefi_bucket_and_prefix`,
  `test_hyperliquid_perp_funding_still_uses_own_asset_group_bucket`, `test_defaults_to_own_asset_group_bucket`,
  `test_non_hyperliquid_derivative_ticker_also_defaults`, `test_hyperliquid_derivative_ticker_overrides_to_cefi`,
  `test_venue_match_is_case_insensitive`, `test_real_bug_shape_blank_raw_symbol_wrong_bucket_end_to_end`,
  `test_logs_warning_when_derivative_ticker_load_returns_empty`,
  `test_logs_warning_when_derivative_ticker_rows_lack_timestamp`)

This is a byte-exact full revert of `features-service@6b2282c5` — slot-12's `[BACKEND] P1` fix in
`defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md` (HYPERLIQUID's `derivative_ticker` OI
capture writes exclusively to the CEFI bucket, not the run's own DEFI bucket — a real bucket/asset_group mismatch,
independently traced and verified live at the time). **No commit, no commit message, no comment anywhere in the diff
explains why.** The file's mtime (checked at discovery time) predates `6b2282c5`'s own commit timestamp, which is odd
for a revert of it — possibly a stale/abandoned WIP from an earlier, unrelated attempt rather than a fresh reaction to
`6b2282c5` specifically, but I could not determine provenance further without guessing.

## What I did

Did NOT commit it (not my task, no rationale I could verify) and did NOT discard it (per CLAUDE.md's git safety protocol
— investigate before deleting/overwriting uncommitted work). Stashed it:
`git stash push --include-untracked -m "orchestrator-slot-8-features_smoke_matrix_verification_findings-006"` in the
`features-service-clean-check` worktree, reported in that task's `/done` `stashed` field (per the DONE-GATE protocol —
this Slack-alerts the operator by design).

## Why it matters now (new evidence since the stash)

This same session ran extensive REAL production verification of `6b2282c5` — the exact thing this stash reverts:

- `features-delta-one-defi-20260803-055145` (`funding_oi`, DEFI, `15m`, `2023-05-12..2023-10-31`, `EXIT_STATUS=0`):
  manifest shows 454/455 shards `captured` across 147 distinct dates (only the window's first date is `attempted_failed`
  — an expected lookback-buffer warmup edge).
- Independently corroborated by slot-10's concurrent `features-delta-one-defi-20260803-055219` (same conclusion, found
  the identical bug class via a completely different route — a DP-VM escalation, not a dispatched todo).

Two independent real-infra verifications now support `6b2282c5` being CORRECT. This makes an unexplained full revert of
it either (a) an accident/aborted experiment that should simply be dropped, or (b) evidence someone found a DIFFERENT
problem with the fix that was never written down — which would be a genuine data-correctness concern given
`defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 checkbox has now been flipped citing `6b2282c5` as working.

# Recommended decision

- [ ] [OPERATOR] P2. Determine the stash's origin/intent: check `features-service-clean-check`'s recent history (was
      this worktree used by another slot/session around 2026-08-03T00:43Z, the stashed file's mtime?), ask around, or
      simply judge it abandoned given the strong corroborating evidence above. Done when: a decision is recorded — drop
      the stash (`git stash drop` on the `features-service-clean-check` worktree, human-only per this workspace's
      destructive-command guardrail) if judged accidental/abandoned, or escalate to a real `[BACKEND]` investigation if
      a genuine concern surfaces.
- [ ] [SCRIPT] P3. If judged accidental: audit whether `features-service-clean-check` (or any other `-clean-check`
      linked worktree in this workspace) should be routinely swept for stray staged/uncommitted state, since it is not
      part of the normal `/boot`-per-task worktree-cleanliness checks (those check the slot's PRIMARY repo clones, not
      secondary linked worktrees like this one).

# Progress Log

- 2026-08-03 (slot-4, `data_pipeline_failure` DP-VM-001 escalation, `agt-dd3c9e`): **third independent corroboration
  that `6b2282c5` is correct — found via a pre-fix failure, not a post-fix verification.** Dispatched to relaunch
  `features-delta-one-defi-20260803-031632` (started 2026-08-03T03:16:32Z — over 2h before this doc's `055145`/`055219`
  verification runs), which failed `exit_code=1`. Root-caused BEFORE considering any relaunch (run.log: "No pre-loaded
  candles for HYPERLIQUID:perpetual:" at every timeframe, on EVERY one of the 173 requested days 2023-05-12..2023-10-31
  — 100% reproducible, not transient) — this is `6b2282c5`'s exact pre-fix symptom: my VM ran BEFORE the fix landed on
  `live-defi-rollout`, so it hit the unpatched code path (no CEFI-bucket passthrough for HYPERLIQUID
  `derivative_ticker`/OI). Rather than blind-relaunch a deterministic failure, verified current state instead: (1)
  `6b2282c5` is on `live-defi-rollout`, ancestor of my slot's current features-service HEAD (`c092df50`), and
  `_DERIVATIVE_TICKER_CROSS_ASSET_GROUP_VENUES`/`_resolve_passthrough_source` are present in the checked-out tree (not
  reverted — this stash has NOT leaked into the primary worktree); (2) live GCS check on
  `gs://features-defi-prd-central-element-323112/delta_one/by_date/` confirms real, non-trivial funding_oi parquet
  shards for `HYPERLIQUID:perpetual:` across the sampled range (2023-07-15 15m = 341.65 KiB, 2023-10-31 15m = 737.9 KiB,
  written 05:57-05:59Z — matching the `055145` run's timing exactly). Conclusion: the scope my failed VM was dispatched
  for has already been completed by the later successful run: **did not relaunch** (would be redundant — the work is
  done, not missing) and did not file a new issue (this one already covers the exact root cause + risk). Net effect: my
  VM's failure is fully explained as a timing artifact (ran before the fix), not a regression or a second bug — no code
  changes needed on my end. This raises the corroboration count to three independent findings (`055145` exit 0,
  slot-10's `055219` DP-VM escalation, now this pre-fix-failure trace) all consistent with `6b2282c5` being correct and
  the dangling stash being safe to judge abandoned — still leaving that call to the `[OPERATOR]` todo above, not
  deciding it here.
