---
doc_type: plan
title: CI satellite AO batch 2 — second AO-dispatch extraction for the ci tranche
summary: >-
  Second AO-dispatch batch for the `ci` topic tranche, produced by `/ag-closeout-audit ci` (autonomous mode, 2026-07-29)
  re-running against `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (still `status: active`, 14/30 todos done at audit
  time) per the skill's iterative-drain methodology. Phase 0: re-checked batch1's own conflict-gated Deferred items
  first (D2-D6) — three have cleared since 2026-07-26 (D5 operator-ruled TODAY 2026-07-29, D7/D3(1) and D18 already
  resolved per batch1's own 2026-07-28 gate-cleanup notes) and become todos here; D3's remaining quickmerge.sh claims
  and D2/D6 remain genuinely gated, carried forward. Phase 0.3 also caught a real script bug —
  `generate_ag_closeout_audit_candidates.py`'s `ao`/`ci`/`infra` membership branch silently returns zero candidates once
  the tranche's own consolidated-closeout doc is archived (which `ci`'s was, 2026-07-28) — worked around via a direct
  frontmatter sweep (`asset_group` containing `ci`) per the skill's now-documented 2026-07-27 schema-migration guidance
  (see
  `plans/archive/issues/generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md`
  for the bug report). Phase 1 read all 9 newly-surfaced candidate docs end-to-end (29 direct `asset_group:[ci]` docs
  minus batch1/finalize minus already-cited/self-dispatched, plus 1 already-known `asset_group:[meta]` fold-in) via a
  Workflow — all 9 confirmed genuinely orphaned (7 `orphaned_never_touched`, 2 `orphaned_partial_coverage`). Phase 3's
  conflict-check found `scripts/quality-gates-base/base-service.sh` claimed by 3 candidates and `base-library.sh` by 2 —
  rationed to one todo per file, same discipline as batch1. 14 conflict-cleared bounded todos below; the rest deferred
  by taxonomy (file-contention / operator-gated / duplicate-of-self-dispatched / too-large / role-mismatch).
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    unified-trading-library,
    market-tick-data-service,
    deployment-api,
    strategy-service,
    features-service,
    execution-service,
    instruments-service,
    greeks-service,
    e2e-testing,
    unified-api-contracts,
    system-integration-tests,
  ]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-2, satellite-docs, quickmerge, quality-gates, test-speed]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/active/ci_satellite_ao_dispatch_batch2_finalize_2026_07_29.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-07-29"
last_updated: "2026-07-30"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5.5
estimate_calibrated_ai_days: 4.4
assigned_role: cicd
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit ci` run 2026-07-29 (ag_closeout_auditor scheduled worker, slot 7), re-triaging
  `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s Deferred section + a fresh Phase 1 sweep of docs never touched by
  batch1 (9 new-since-2026-07-26 or previously-missed tranche members).
---

# CI satellite AO batch 2

> **🟢 STATUS: `active` — dispatched 2026-07-30** (`unified-trading-pm@5a6bbefc3`, "activate 9 fresh ag-closeout-audit
> dispatch batches (operator go-ahead)"). Drafted by a scheduled one-shot audit worker, then reviewed and activated by
> the operator alongside 8 sibling batches; AO dispatch is now live against the todos below.

> **Why this plan exists.** `ci_satellite_ao_dispatch_batch1_2026_07_26.md` is still active with 16/30 todos open — this
> is NOT a replacement for it. This is the tranche's SECOND extraction: items batch1 deliberately deferred (now
> conflict-cleared) plus docs that never existed or were never discovered as of batch1's 2026-07-26 snapshot.

## Same-file contention — read before editing this plan

Same-priority todos in one plan run **concurrently**, so they must touch disjoint files (CLAUDE.md § Plans). Three files
are contended this round:

- **`scripts/quality-gates-base/base-service.sh` — claimed by 3 candidates.** Only todo 1 touches it (folds in the
  `--durations=25` addition too, since it already owns the file this round).
  `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md`'s BATS-phase todo also wants this file — deferred to
  batch 3 (see `## Deferred`).
- **`scripts/quality-gates-base/base-library.sh` — claimed by 2 candidates.** Only todo 11 (the `${TMPDIR:-/tmp}` port)
  touches it. The `--durations=25` addition (same source as the base-service.sh contention above) also wanted this file
  — deferred to batch 3, do not add a second base-library.sh todo here.
- **`scripts/quickmerge.sh` — claimed by 4 candidates.** Only todo 1 touches it (the ENVIRONMENT-alignment piece).
  `stale_staging_versions_manifest_2026_07_23.md`'s STAGE 1.6 dormancy gate (D8, previously "reserved" for this batch —
  see note in `## Deferred`), `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md`'s redundant-hook
  deletion (D4), and `ldr_to_main_promote_churn_fix_verification_2026_07_27.md`'s Option-B removal (operator-gated
  anyway) are all deferred again.

Every audit/verification todo records its findings **in its own named source doc**, never in this plan's body, so
concurrent workers do not collide on this file.

## Todos

- [x] ✅ [INFRA] P1. **Bind configuration into the QG sentinel + align quickmerge/standalone `ENVIRONMENT` resolution +
      add the `--durations=25` visibility flag.** Three related `scripts/base-service.sh`/`scripts/quickmerge.sh`
      changes bundled into one todo (same file, avoids a same-priority collision with the other two candidates this
      round — see § Same-file contention): (a) mix `ENVIRONMENT` (and any other gate-affecting env var) into the QG
      sentinel hash so a sentinel produced under one configuration cannot satisfy a run under another, with a regression
      test proving a dev-written sentinel does NOT satisfy a prod-context quickmerge; (b) make quickmerge's and a
      standalone `quality-gates.sh --no-fix` run resolve the SAME explicit `ENVIRONMENT` for the same branch context —
      do NOT flip quickmerge itself to `production` (that trades this hazard for real prod-credential exposure on every
      slot's every commit); instead make the standalone entrypoint derive `ENVIRONMENT` from the same branch-conditional
      logic quickmerge uses, covering every repo's entrypoint, not just the 3-4 currently-affected repos, with a
      regression test asserting both paths resolve identically for the same branch; (c) add `--durations=25` to the
      shared pytest invocation in `base-service.sh` (visibility only, zero behavior change). **Done when**: (a) and (b)
      each have a passing regression test, `quality-gates.sh` is green in every repo touched, and (c)'s duration output
      is visible on a real PM run. Sources: `issues/qg_sentinel_environment_blind_2026_07_23.md` (Resolution checklist
      items 2 + 5, RULED 2026-07-28 — no longer operator-gated) ·
      `archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md` (`--durations=25` item). **(c) CONFIRMED
      ALREADY SHIPPED 2026-07-30 (this session's rulings-closeout pass)** — verified live: `base-service.sh`'s `PARGS`
      already carries `--durations=25` (`unified-trading-pm@3ed0fc99d`, 2026-07-29, "perf(ci): add pytest --durations,
      uv cache in the QG reusable, merge ruff dtz/tid251 rule-group scans into one invocation" — confirmed via
      `git show 3ed0fc99d -- scripts/quality-gates-base/base-service.sh`), sourced live by every consumer repo. **(a)
      and (b) confirmed still genuinely open** — re-read `_qg_content_hash()` in `base-service.sh` directly: it hashes
      HEAD sha + tracked/untracked diffs + the gate-logic script + ruff version, with NO `ENVIRONMENT`/ `DEPLOYMENT_ENV`
      dimension. Confirmed PM's own `scripts/quality-gates.sh` never exports `ENVIRONMENT` before sourcing
      `base-service.sh` either (standalone runs still fall through to the Python resolver's bare-unset→prod default).
      ~~**NOT attempted this session**: (a)/(b) require editing the shared, fleet-wide sentinel-hash function every
      repo's QG run depends on — assessed as too high-blast-radius to implement solo without a dedicated, reviewed
      session (a subtle bug here breaks `quickmerge --agent`'s fast-path for every repo, not just one), unlike the
      bounded, single-file fixes elsewhere in this batch. Left open and unclaimed rather than rushed.~~ **(a) and (b)
      SHIPPED 2026-07-30** (`unified-trading-pm@4545df4c6`) — the dedicated, reviewed pass the prior session held out
      for. New shared single-source-of-truth `scripts/quality-gates-base/qg-environment.sh` (`qg_resolve_environment()`)
      sourced from BOTH `qg-common.sh` (every base-\*.sh tier — service/library/ui/codex) and `quickmerge.sh`'s own
      ENVIRONMENT AUTO-DETECT block (no-ops in CI via `GITHUB_ACTIONS=true`, since the v2 gate's `QG_SLICE`-sliced runs
      never touch the sentinel anyway). `_qg_content_hash()` (base-service.sh + base-library.sh) now folds
      `ENVIRONMENT`/`DEPLOYMENT_ENV` into the content-sentinel hash. `.qg_last_passed_sha` (base-service.sh,
      base-library.sh, base-ui.sh) now appends `ENVIRONMENT=`/`DEPLOYMENT_ENV=` lines after the SHA (old bare-SHA
      sentinels still parse via `head -1`, backward compatible); `quickmerge.sh`'s `_qm_check_agent_sentinel()` now
      refuses a config mismatch before the SHA/content check. **(a)'s regression test**:
      `scripts/quality-gates-base/tests/test-qg-sentinel-environment-binding.sh` (content-hash differs across
      ENVIRONMENT/DEPLOYMENT_ENV, 5/5 assertions) +
      `scripts/quality-gates-base/tests/test-quickmerge-sentinel-environment-mismatch.sh` (the literal bar: a
      dev-written sentinel does NOT satisfy a prod-context quickmerge check, and vice-versa, 6/6 assertions incl. the
      old-bare-SHA-sentinel-fails-closed case). **(b)'s regression test**:
      `scripts/quality-gates-base/tests/test-qg-environment-resolution-parity.sh` (quickmerge's block and
      `qg_resolve_environment` resolve identically for main/non-main/arbitrary branches + explicit-override
      preservation, 6/6 assertions). **Verified live, not just in the extracted-function tests**: a full
      `bash scripts/quality-gates.sh` run in PM itself wrote `.qg_last_passed_sha` with `ENVIRONMENT=development`
      appended (branch=live-defi-rollout, matches quickmerge's own resolution); a SECOND full run in
      `unified-trading-library` (a genuinely different consumer repo/tier, clean worktree, pre-existing bare-SHA
      sentinel from 2026-07-28) independently reproduced the same correct write, and the real
      `_qm_check_agent_sentinel()` (extracted from the shipped `quickmerge.sh`) accepted that live sentinel under a
      matching `ENVIRONMENT=development` check and correctly refused it under `ENVIRONMENT=production` — the exact
      hazard this todo closes, reproduced and fixed end-to-end against real production code, not a synthetic fixture.
      Pre-existing-failure baseline confirmed via `git stash`: 3 of the base-tests dir's other `test-*.sh` files
      (`test-qg-governor-wait-time.sh`, `test-qg-mem-cap.sh`, `test-setup-sh-uv-bootstrap-fallback.sh`) fail identically
      with my changes stashed out — unrelated, pre-existing (host-timing/systemd-availability/uv-pin drift), not a
      regression. Full `quality-gates.sh` green in PM (both before and after the codex-doc pass below). **Post-phase
      codex audit** (this todo's own shared-contract change, per CLAUDE.md): updated `/codex/08-workflows/ci-cd-flow.md`
      § "Two-Pass Workflow Model" (the sentinel ASCII block was describing the bare-SHA pre-fix format),
      `/codex/06-coding-standards/quality-gates.md` § "Do-less-work levers" (the green- sentinel hash-input list), and
      `/codex/05-infrastructure/quickmerge-architecture.md` § "Environment Awareness" / "Sentinel integration" (also
      fixed a stale `quickmerge.sh` line-number citation while there). Also corrected the matching sentinel-format
      claims in `/codex/08-workflows/deployment-flow.md` — but that doc's OWN pipeline model (staging-mediated
      promotion) turned out to be much more broadly stale, pre-dating the LDR-direct MVP migration independent of this
      fix; filed `issues/deployment_flow_doc_stale_pre_ldr_direct_mvp_2026_07_30.md` rather than absorbing that larger,
      unrelated rewrite into this todo. **(c)** was already confirmed shipped in the 2026-07-30 rulings-closeout pass
      above; no change needed here.
- [x] ✅ [DOC] P2. **Correct the "re-run quality-gates.sh --no-fix then retry" recovery guidance** wherever it is taught
      — **verified 2026-07-31: already done, as a byproduct of todo 1's own shipped fix; no separate correction commit
      needed.** Full-corpus sweep (agents/_.md incl. every craft file, cursor-configs/_.md + all 24 repos' symlinked
      copies, codex/**/_.md, codex/15-runbooks/, scripts/quickmerge.sh, scripts/quality-gates-base/_.sh, every sibling
      repo's own docs) found **no file anywhere that currently teaches the unsafe pattern as live/positive instruction**
      — the only place the literal phrase appears is inside this todo's own source issue doc
      (`qg_sentinel_environment_blind_2026_07_23.md`), where it is quoted as the historical BUG DESCRIPTION being fixed,
      not instructional copy misleading a reader. The 3 canonical SSOT docs that DO describe the recovery flow were
      already updated as part of todo 1's landing (`unified-trading-pm@4545df4c6`, 2026-07-30) to describe the post-fix,
      genuinely-safe behavior: `codex/08-workflows/ci-cd-flow.md` (lines ~384-405, sentinel now appends
      `ENVIRONMENT=`/`DEPLOYMENT_ENV=` + `_qm_check_agent_sentinel()`-equivalent config-mismatch check),
      `codex/06-coding-standards/quality-gates.md` § "Do-less-work levers" (content-hash now folds resolved
      `ENVIRONMENT`/`DEPLOYMENT_ENV`), `codex/05-infrastructure/quickmerge-architecture.md` § "Environment Awareness" /
      "Sentinel integration" (shared `qg_resolve_environment()` single source of truth). `scripts/quickmerge.sh`'s
      `_qm_check_agent_sentinel()` (lines ~1484-1527) already emits the correct, safe framing on a config mismatch
      (`❌ Pass 1 sentinel config mismatch` + `Re-run: bash scripts/quality-gates.sh`), and its own regression test
      (`scripts/quality-gates-base/tests/test-quickmerge-sentinel-environment-mismatch.sh`) quotes the OLD bug purely as
      historical test-rationale context (correct, expected use — not stale guidance). `agents/worker.md:417`'s "commit
      it, re-run quality-gates.sh, quickmerge push" is the normal two-pass ship flow, not the environment-laundering
      pattern, and is accurate as written (now genuinely safe since the sentinel binds environment). **No corpus edit
      was required by this todo** — Sequenced after todo 1 (already `[x]` above). Source:
      `issues/qg_sentinel_environment_blind_2026_07_23.md` (Resolution checklist item 4, also flipped).
- [x] ✅ [INFRA] P2. **CONFIRMED ALREADY CLEAN (verified 2026-07-31) — no code change needed, the non-MTDS half of the
      2026-07-23 claim does not reproduce today.** Re-derived the exact mechanism first: since todo 1's (a)/(b) landed
      (`unified-trading-pm@4545df4c6`, 2026-07-30), `qg-environment.sh`'s `qg_resolve_environment()` is now sourced by
      BOTH quickmerge AND a standalone `quality-gates.sh` run — so the original divergence this todo worried about
      (quickmerge forces `development`, standalone left `ENVIRONMENT` unset and fell through to the bucket resolver's
      `prod` default) no longer exists: on `live-defi-rollout` (every slot's branch, not `main`), BOTH paths now resolve
      `ENVIRONMENT=development` identically. Reproduced directly against that now-single value: `deployment-api`'s full
      `tests/unit` suite (the exact scope `quality-gates.sh` collects, `RUN_INTEGRATION=false`) — 5052 passed/16 skipped
      under `ENVIRONMENT` unset AND under `ENVIRONMENT=development`, byte-identical pass/skip counts, `-p no:xdist`.
      `strategy-service`'s full `tests/` suite (its `PYTEST_UNIT_DIR="tests/"` — the per-family-layout scope the gate
      actually runs, excluding only `-k integration`) — 5003 passed/5 skipped/22 xfailed under both states, again
      identical. Grepped every `-prd-`/`resolve_bucket_name`/`get_bucket_name` test call site in both repos (the
      `test_manifest_source.py`/`test_data_query_service.py`/`test_unified_deps_functional.py` hits the original
      2026-07-23 grep would have found) — all pass literal strings directly to mocked functions or explicit config
      overrides, none resolve a bucket name through the ambient-`ENVIRONMENT`-dependent ambient resolver path the way
      MTDS's 2 named reproducer tests do. `git log --since=2026-07-23 -- tests/` in both repos shows no intervening fix
      commit either — this was not silently patched elsewhere; the original claim (unlike MTDS's 2 explicitly-named,
      explicitly-verified failing tests) appears to have over-generalized from the `-prd-` grep pattern without
      confirming a live ambient-`ENVIRONMENT` failure in these two repos specifically. **Final confirmation — the real
      gate, not just the scoped reproduction**: full `bash scripts/quality-gates.sh` (backgrounded per the cicd
      heartbeat rule) in both repos: `deployment-api` → `✅ ALL QUALITY GATES PASSED (112s)`, sentinel written, exit 0
      (the 2 `❌`-prefixed lines mid-run are pre-existing `imports-inside-functions`/`direct-cloud-SDK` debt absorbed
      within `CODEX_MAX_VIOLATIONS=5`'s aggregate-tolerance pool — "Codex compliance: 3 violations (within tolerance of
      5)", unrelated to this todo); `strategy-service` → `✅ ALL QUALITY GATES PASSED (122s)`, sentinel written,
      independently re-verified `EXIT=0` on a second fast-path run (the peripheral `e2e-testing/scripts/defi/`
      ruff/basedpyright warnings printed after the pass banner are that OTHER repo's own pre-existing peripheral-dir
      debt, non-blocking, out of scope here). **Explicitly excludes the two `market-tick-data-service` cases**, which
      stay genuinely gated — those are real, confirmed, still-failing reproducers (see `## Deferred` E7), unrelated to
      this finding. Source: `issues/qg_sentinel_environment_blind_2026_07_23.md` (Resolution checklist item 3, non-MTDS
      half — flipped accordingly there too).
- [x] ✅ [DEVOPS] P2. **DONE (verified 2026-07-30, this session's rulings-closeout pass) — all three parts already
      resolved, none by this session directly; closing out the citation.** (a) The `PROVENANCE-BLOCKED` reclassification
      is live in `scripts/cicd/promotion_lag_monitor.py` (`_provenance_blocked()` + the
      `⛔ BLOCKED by the provenance     gate...` inline finding in `main()`, distinct from the plain `PROMOTION LAG`
      line) — but had NO regression test exercising it against a synthetic blocked PR, which is the one genuine gap this
      session closed: `scripts/cicd/test_promotion_lag_monitor_provenance_blocked.py` (6 new tests mocking `_gh_json` —
      no-open-PRs, fail-closed-on-lookup-failure, PR-without-marker, PR-with-marker [the synthetic reproducer],
      non-promote-titled PR skipped, non-int PR-number skipped), shipped `unified-trading-pm@51b93ec0a` (direct push per
      the PM `scripts/**` carve-out — local `quality-gates.sh --no-fix` was red only on 8 pre-existing, unrelated
      failures, confirmed by reading each traceback:
      `test_capability_param_schema.py`/`test_capability_verdict_matrix.py` [known, strategy-service CARRY_STAKED_BASIS
      in-progress wiring], `test_check_repo_docs_ssot.py` [drift in an unrelated `deployment-service-sports-wt`
      worktree], `test_check_doc_body_links.py` [a 60s pytest-timeout from host contention against a second concurrent
      full QG run, not a real broken link] — the new test file itself:
      `.venv/bin     /python -m pytest scripts/cicd/test_promotion_lag_monitor_provenance_blocked.py -q` → 6 passed,
      ruff-clean). (b) The 2 SPECIFIC 2026-07-17 offenders named in this todo (`market-tick-data-service@d302f07a`,
      deployment-ui) are STALE — the source issue doc itself (see below) already recorded both its own todos `[x]` done
      2026-07-30, explaining those exact offenders were long superseded and the CURRENT (2026-07-30) blocks were cleared
      instead (`features-service` 4 commits, `market-tick-data-service` 38 commits, via `reprovenance_bypass.sh`).
      Live-reverified just now: `gh pr list --repo IggyIkenna/deployment-ui --state open --base main` → **empty** — no
      open promote PR, so there is no current block to clear for it. (c) `_backmerge` exemption reconfirmed live in
      `check_strict_quickmerge.py` (2-parent-merge unconditional exemption + `test_backmerge_merge_commit_is_exempt`).
      Source: `issues/promotion_lag_alert_hides_provenance_block_2026_07_17.md` (both its own todos already `[x]`,
      2026-07-30 — this batch2 todo's citation predates that resolution and had gone stale relative to it).
- [x] ✅ [SCRIPT] P2. **CONFIRMED ALREADY SHIPPED (verified 2026-07-30, this session's rulings-closeout pass) — no new
      work needed.** `unified-trading-pm@bbe9a9871` documents the third `Quickmerge: direct-carveout-dirty-deps` trailer
      value + the dirty-deps direct-push recipe in `/codex/08-workflows/ci-cd-flow.md` (confirmed live at lines 211/219
      of the current HEAD, == `origin/live-defi-rollout`); `check_strict_quickmerge.py`'s trailer check was already
      value-agnostic (presence-only), so no code change was needed there either. Source issue
      `plans/archive/issues/check_strict_quickmerge_blind_to_dirty_deps_carveout_2026_07_23.md` is itself already
      `status: resolved` + archived 2026-07-30 with this exact evidence — this batch2 todo's own citation was drafted
      2026-07-29, one day before that archival, and had simply gone stale.
- [x] ✅ [FIX] P1. **Close the `detect_breaking_change.py` registry-data-dict blind spot end to end.** — shipped
      `unified-trading-pm@7e0aab35f` + `unified-api-contracts@e34afc1d` + `system-integration-tests@67db4da`. (a)
      design: `# @contract-surface` marker convention (docstring + inline comments in `detect_breaking_change.py`),
      citing the manifest `schema_version` precedent explicitly. (b) implemented: tagged constant → literal snapshot
      (bare-`Name` keys/members resolved against earlier same-file string constants; unresolvable per-key values
      dropped, not fatal) → structural diff (removed top-level key / removed set-or-list member / removed inner dict-key
      = breaking; additive = not). Tagged all 3 constants in `unified-api-contracts` (`INSTRUMENT_TYPES_BY_VENUE`,
      `VENUES_BY_ASSET_GROUP`, `VENUE_DATA_TYPE_CAPABILITIES`). (c) 9 new regression tests in
      `test_detect_breaking_change.py`, including the exact `23fa3a99` (OKX, SPOT_PAIR)-shape fixture — all pass
      (`.venv/bin/python -m pytest tests/unit/test_detect_breaking_change.py -q` → 20 passed). (d) SIT gap closed:
      `unified-api-contracts/tests/test_cefi_registry_expected_universe_invariant.py` (3 tests, loads
      instruments-service's `build_expected('cefi')` by file path — not part of the installable package — runs it
      against the live registry, asserts `VENUE_DATA_TYPE_CAPABILITIES`⊆`VENUES_BY_ASSET_GROUP` and every
      `CEFI_VENUE_FOLD` target has expected tuples; wired into `run_cross_repo_invariants.sh` as invariant #22); the
      `strict=False` xfail on `test_venue_to_tardis_matches_inverted_venue_mapping` is RESOLVED for real (not just
      relaxed) — it surfaced 2 genuine pre-existing bugs (`_VENUE_TO_TARDIS['OKX']` pointed at the spot feed 'okex'
      instead of the perp aggregate's real feed 'okex-swap'; a stale bare-"COINBASE" expected-venue predating the
      2026-07-06 COINBASE-SPOT migration), both fixed. Also removed a stale `VENUE_DATA_TYPE_CAPABILITIES["POLYGON"]`
      entry (Polygon.io, retired as a tradfi source 2026-07-19, never cleaned up — caught live by the new (d)
      invariant). (e) reproduced end-to-end: in an isolated worktree, committed the marker on top of UAC's real
      pre-23fa3a99 base, then re-applied the exact SPOT_PAIR-removal shape on top — differ now returns
      `is_breaking:true` with export count unchanged 1204→1204 (matching the original false-negative signature); the new
      SIT invariant independently verified to go RED on a fold-target venue silently disappearing from the registry
      (proved via an in-memory monkeypatch — deleting bare `BYBIT` from `INSTRUMENT_TYPES_BY_VENUE` makes
      `test_cefi_venue_fold_targets_are_expected` fail as expected). (f) `ci-cd-flow.md`'s breaking-differ section
      updated (new bullet + closed-gap rewrite of the prior "residual coverage gap, still open" note). **Excluded per
      scope**: the source doc's [DESIGN] P2 consumer-QG-fanout item stays parked as Deferred **E8** /operator question 1
      in this plan — not required for this todo's done-when. Source:
      `issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md` (todos 1-4, 6-7 closed by this; todo 5
      = the parked E8 design fork).
- [ ] [SCRIPT] P2. **Fix real `sleep()`-based test waste — the non-MTDS fleet.** Mocking the clock instead of sleeping
      real wall-time, zero behavior risk, across 3 repos (excludes `market-tick-data-service`'s
      `test_sports_catalog_reader_timeout.py` — that file is ALREADY self-dispatched under
      `issues/mtds_sports_catalog_reader_timeout_test_flaky_under_contention_2026_07_27.md`, `assigned_vm: planning`; do
      not duplicate, but flag for whoever picks that task up that monkeypatching `_BLOB_TIMEOUT_SECS` down — this doc's
      proposed fix — would also resolve that doc's flakiness, since a near-zero timeout removes the wall-clock race
      entirely, not just widens the margin): (a) `unified-trading-library` —
      `test_manifest_freshness.py`/`test_agent_action.py`/`test_pipeline_heartbeat_timer.py` sleep-based waits
      (~11.65s/run); (b) `features-service` — `test_feature_cache.py` `sleep(1.1)`; (c) the smaller batch/low-value
      sleeps in `deployment-api`, `instruments-service`, `greeks-service`. **Done when**: every named test passes with
      the real sleep replaced by a mocked/monkeypatched clock and the per-repo `quality-gates.sh` stays green. Source:
      `archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md` (§ "Real sleep()-based test waste").
- [x] ✅ [SCRIPT] P3. **CONFIRMED ALREADY SHIPPED (verified 2026-07-30, this session's rulings-closeout pass) — no new
      work needed.** Both parts confirmed live in `unified-trading-pm@3ed0fc99d` (2026-07-29, same commit that shipped
      todo 1's `--durations=25` piece above): (a) `.github/workflows/python-quality-gates-v2.yml` carries
      `actions/cache@v4` for the `uv` package cache, sized first per the commit message (cold `uv sync` ~2m07s vs warm
      9.4s, a real ~118s/run win) before being added; (b) `scripts/quality_gates/check_ruff_rule_ratchet.py`'s
      `run_ruff_count_all()` merges the separate `dtz`/`tid251` full-tree ruff invocations into one pass (confirmed via
      `grep -n "run_ruff_count_all" scripts/quality_gates/check_ruff_rule_ratchet.py`). Source:
      `archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md` (§ tooling speed) — this batch2 todo's
      citation was drafted 2026-07-29, after the fix had already shipped, and had simply gone stale.
- [ ] [SCRIPT] P3. **Dead-code cleanup: 3 confirmed-stale deletions.** (a) `execution-service` — re-verify ~40
      files/~10,082 lines importing a pre-refactor module path are still genuinely dead, then delete; (b)
      `unified-trading-library` — delete the already-skip-marked dead test importing a moved `ConfigReloader` path; (c)
      `e2e-testing` — fix the stale `SERVICES` arrays in `run-full-pipeline.sh` referencing archived pre-merge
      `features-*-service` repos. **Done when**: (a)'s re-verification is recorded before deletion (per "delete
      deprecated code, no shims" — confirm dead first), all three repos' `quality-gates.sh` stay green post-delete, and
      (c)'s `SERVICES` array matches the live repo topology. Source:
      `archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md` (§ dead code).
- [x] ✅ [BACKEND] P1. **Widen MTDS's ungated test coverage — fix + widen `PYTEST_UNIT_DIR`.** —
      `market-tick-data-service@4849d4f6`. Real failure count had DRIFTED further since this doc's 2026-07-17 baseline
      (22 real failures) to 35 by 2026-07-30 (13 more days of ungated churn) — all 35 fixed against the CURRENT prod
      contract, not the stale 2026-07-17 snapshot: (a) the 8+ `tests/market_interface/unit/` failures
      (`test_defi_handlers.py` — 4 handlers' `assert_defi_catalog_fresh` preflight never mocked + a manifest-recorder
      API rename (`record_failed` → `record_catalog_unavailable`) + a bridge-events subgraph→on-chain-log rewrite + an
      aave-positions per-reserve schema change; `test_defi_adapters_boost_2.py` — ethena oracle_prices now
      on-chain-samples via `BlockResolver` + current_apy reaches real DefiLlama sockets unmocked;
      `test_barchart_and_yahoo_adapters.py` — Yahoo `fetch_instruments()` intentionally always `[]` per 2026-06-25
      ruling, test asserted the opposite); (b) the `tests/market_interface/adapters/**` canonical-output/write failures
      (7 databento canonical-id + 4 write-pipeline `file_symbol`-kwarg/chain-tail drift + 8 tradfi_canonical_writes
      pipeline_mode drift [6 stale FRED/ECB/OFR-override + Massive-retired assertions fixed; 2 IBKR ones are a REAL bug
      — IBKR has no `_VENUE_OVERRIDES` entry, xfailed + filed
      `issues/ibkr_pipeline_mode_missing_venue_override_2026_07_30.md` rather than papered over] + 1 tardis-options
      credential-gated test hardened against a conftest dummy-key false-positive + 1 tardis-adapter ns-vs-us timestamp
      fixture bug); (c) widened `PYTEST_UNIT_DIR` to the full `market_interface`
      unit/adapters/clients/schema_validation + `tests/cli` + 3 proven credential-free `tests/integration/*` files —
      full `bash scripts/quality-gates.sh` GREEN with the widened dir (rule 11a, exit 0); (d) the remaining 9
      `tests/integration/**` files stay OUT (all already `@pytest.mark.requires_credentials` + self-skip, real vendor
      creds unavailable in CI — decision + rationale recorded inline in `scripts/quality-gates.sh`'s `PYTEST_UNIT_DIR`
      comment block). Also found + fixed a look-alike (NOT the same) test-env issue in
      `test_bucket_resolution_uses_category_tradfi` (root-caused live: this repo's own `CLOUD_PROVIDER=local` test-suite
      default, not the tracked DEPLOYMENT_ENV race) — noted in
      `issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md` to avoid future confusion with that
      still-open, unrelated leak. Source: `issues/mtds_ungated_test_families_2026_07_17.md` (todos 1-4, all closed).
- [ ] [QG] P2. **Fleet sweep: a PM quality-gate check comparing every repo's `tests/*/unit/` dirs against its
      `PYTEST_UNIT_DIR`.** So no other repo silently ends up in MTDS's pre-todo-11 situation (a whole test family never
      collected by the gate). New standalone PM script, shrinking-ratchet baseline (do not fail the gate red on existing
      fleet debt this todo doesn't fix). **Done when**: the checker exists, correctly flags a synthetic
      new-uncollected-dir case, and the baseline is seeded at today's real fleet count. Source:
      `issues/mtds_ungated_test_families_2026_07_17.md` (todo 5).
- [ ] [INFRA] P2. **Port the `${TMPDIR:-/tmp}` hardcoded-path fix to `scripts/quality-gates-base/base-library.sh`.**
      Mirrors the already-shipped `base-service.sh` fix in the same source doc — grep for the ~10+ named hardcoded
      `/tmp/` checker-capture sites in `base-library.sh`, apply the identical substitution pattern, verify `bash -n`,
      re-run `quality-gates.sh` on a library-tier repo (e.g. `unified-api-contracts`). **Done when**: every named site
      uses `${TMPDIR:-/tmp}`, `bash -n` passes, and the named library-tier repo's `quality-gates.sh` is green on a full
      tmpfs. Source: `archive/issues/qg_hardcoded_tmp_paths_false_failures_on_full_tmpfs_2026_07_26.md` (sole open
      todo).
- [ ] [BACKEND] P2. **Root-cause and fix `plan-health-agent.yml`'s dead `schedule` trigger (1/200 firings since
      2026-03-07).** One combined todo (todo 2 is gated on todo 1's output, same source doc): (a) compare the workflow's
      trigger/concurrency/permissions blocks line-by-line against 2-3 reliably-firing sibling crons — the doc has
      already ruled out disabled-workflow-state, recently-added-trigger, and concurrency-group collision; the leading
      untested hypothesis is `pull_request`-trigger-volume deprioritization; escalate to GitHub support/status page only
      if no structural cause is found; (b) once root-caused, ship the fix (e.g. split the `pull_request`- triggered
      sweep into its own workflow file to remove shared-workflow contention, or adjust concurrency scoping) and verify
      via a real schedule-triggered run appearing within 48 hours of shipping. **Done when**: (a) records a root cause
      (or a documented, GH-support-escalated absence of one), and (b)'s fix is verified by an actual schedule-fired run
      post-ship. Source: `issues/plan_health_agent_dead_schedule_trigger_2026_07_27.md` (todos 1-2).
- [ ] [DOC] P2. **`monitoring_control_plane_master_2026_06_10.md` reconciliation + one bounded status check.** (a)
      Reconcile G3 (manifest-consolidator-health, still literally `- [ ]` since 2026-06-12) against what actually
      shipped: `unified_deployment_health_cockpit_2026_06_23` (status complete) delivered the underlying capability, and
      `consolidator_throughput_backlog_monitor_2026_07_09` (active, cross-cutting tranche batch2) extended it further —
      close G3 against these with an explicit cross-reference, or re-scope it to whatever residual gap remains once
      those two are read; (b) re-verify the Deferred-work row citing `cicd_contract_hardening_2026_06_01.md`'s (now
      ARCHIVED) "promote system-integration-tests LDR → main" todo — check whether the routine LDR→main drain has since
      promoted `system-integration-tests` to `main`, and if not, promote it. **Explicitly excludes** the Rollout-ratchet
      panels / G4 items (UI-touching, needs a `[UI]`-capable role + `pw:L2` gate, this batch's `assigned_role` is
      `cicd`) and the "Runtime-level deploy signal v2" P0 item (scope too open-ended for a bounded todo as currently
      written — see `## Escalated to the operator`) — both deferred. **Done when**: G3 is either closed-with-citation or
      re-scoped with a stated residual, and (b)'s promotion status is recorded (and acted on if still pending). Source:
      `monitoring_control_plane_master_2026_06_10.md` (G3 line 429, Deferred-work row line 622).

## Deferred

Tagged by WHY, per the `/ag-closeout-audit` non-batchable taxonomy.

### Conflict-gated (file-contention this round — re-triageable in batch 3+)

| id  | Item                                                                                                                                                                   | Competing claim it collided with                                                                                                                                                                                                                      |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E1  | `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md` — add BATS phase to `base-service.sh`                                                                     | Todo 1 owns `base-service.sh` this round                                                                                                                                                                                                              |
| E2  | `ci_test_content_and_tooling_speed_findings_2026_07_28.md`'s `--durations=25` addition to `base-library.sh`                                                            | Todo 11 owns `base-library.sh` this round (todo 1 already carries the `base-service.sh` half of this same item)                                                                                                                                       |
| E3  | `stale_staging_versions_manifest_2026_07_23.md` (D8) — STAGE 1.6 dormancy-aware dep gate in `quickmerge.sh`                                                            | Todo 1 owns `quickmerge.sh` this round. **Note**: this item was previously flagged "reserved for batch 2" in batch1's Deferred D8 — superseded this round by the higher-priority (P1 vs P2) sentinel-binding fix; genuinely next in line for batch 3. |
| E4  | `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` (D4) — delete redundant `pre-push-strict-quickmerge.sh` + repoint referrers in `quickmerge.sh` | Todo 1 owns `quickmerge.sh` this round; both referrer todos (batch1 todo 1, batch1 todo 18) are now done, so this is otherwise fully conflict-cleared — top of the batch-3 queue for this file.                                                       |
| E5  | `quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` steps 2-4 (D3(4)) — broaden the `live-defi-rollout` branch check                                 | Same file as todo 1; also has its own internal step-2 precondition not re-verified this round.                                                                                                                                                        |

### Operator-gated (needs a ruling, not a re-triage)

| id  | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E6  | `ldr_to_main_promote_churn_fix_verification_2026_07_27.md` — removing quickmerge.sh's PM-specific Option-B direct-PR-open step needs explicit operator sign-off first ("should PM's quickmerge stop opening its own promote PR and rely 100% on the bot") — genuine judgment call, not a re-triage. Todo 2 (the before/after churn measurement) is further gated on todo 1 landing.                                                                                                                                                                            |
| E7  | `mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md` — root-causing the 14+ confirmed DEPLOYMENT_ENV leak occurrences is explicitly NOT bounded as currently framed (5 independent investigation sessions have failed to pin the mechanism). This is the SAME underlying bug as `mtds_deployment_env_race_survives_single_worker_2026_07_23.md` (D3(3), already parked pending its own cascade-instrumentation step) — both docs explicitly say "read together, do not duplicate investigation." Stays parked on that single shared blocker. |
| E8  | `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`'s [DESIGN] P2 item — should a UAC registry-change promote additionally fan out and run consumer QG (e.g. instruments-service)? Genuine blast-radius design fork, parked rather than folded into todo 6 above.                                                                                                                                                                                                                                                                              |
| E9  | `digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md` / `post_cutover_silent_assumption_sweep_2026_07_23.md` § F4 — `digest-drift-sweep` non-convergence + `ubuntu-latest` fan-out cost. Re-verified this round: still open, unchanged since batch1's D2 (`post_cutover`'s F4 todo is still unchecked). Same file as batch1 todo 3 (done) — now technically file-available, but the non-convergence root cause itself is still unparked/unresolved, so no bounded fix exists to dispatch yet.                                                      |
| E10 | `post_cutover_silent_assumption_sweep_2026_07_23.md` § F4 — disable/fix the 4 vacuous crons (`sit-debounce-trigger`, `freeze-deferred-build-replay`, `fix-approval-timeout`, `supersede-stale-dep-update-prs`). Re-verified this round: still open, unchanged. Needs a per-cron disable-vs-fix ruling.                                                                                                                                                                                                                                                         |
| E11 | `check_strict_quickmerge_blind_to_dirty_deps_carveout_2026_07_23.md`'s Option 2 sibling docs (`mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md`, `sports_odds_ownership_registry_split_brain_...`, others) that reference the SAME dirty-deps carve-out class — out of scope for todo 5 above, which is scoped to the checker + recipe only.                                                                                                                                                                                                           |

### Role-mismatch (needs a `[UI]`-capable slot, not `cicd`)

| id  | Item                                                                                                                                                                                                                                                                                      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E12 | `ci_test_content_and_tooling_speed_findings_2026_07_28.md` — `unified-trading-system-ui` (Playwright `--project=chromium` scoping, browser-binary cache, ESLint ignore-list tightening) + `deployment-ui` (vitest jsdom→happy-dom, npm→pnpm migration). Same pattern as batch1's D20/D28. |
| E13 | `monitoring_control_plane_master_2026_06_10.md` — Rollout-ratchet panels (deployment-api reader + deployment-ui panel) + G4 (folds into the same panel work).                                                                                                                             |

### Too-large-or-risky / needs a design pass first

| id  | Item                                                                                                                                                                                                                                                                                                                                                                                                                  |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E14 | `monitoring_control_plane_master_2026_06_10.md` — "Runtime-level deploy signal v2" (P0, line 253): resolve what is actually RUNNING (Cloud Run revisions / deployment registry / VM heartbeats) vs `main` HEAD and surface the diff. Scope is open-ended as written (which signals, what "surface the diff" means concretely — new panel vs alert) — needs a scoping/design pass before it can become a bounded todo. |

### Low-priority / near-moot

| id  | Item                                                                                                                                                                                           |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E15 | `ci_test_content_and_tooling_speed_findings_2026_07_28.md` — resume/track the stalled 3-agent PM-cost-breakdown workflow angle. Doc's own note calls this "explicitly low-priority/near-moot." |

## Escalated to the operator (parked, not guessed)

Three questions, quotes/locations/options/recommendation, not resolved autonomously:

1. **E8** — should a UAC registry-change promote (breaking-change differ scope) additionally fan out and run consumer QG
   (e.g. instruments-service) beyond today's producer-repo-only gate? Recommendation: not required for todo 6's core fix
   to be complete; worth a follow-up once todo 6 lands and the blast-radius tradeoff can be evaluated against real
   fan-out cost data.
2. **E14** — does `monitoring_control_plane_master`'s "Runtime-level deploy signal v2" (P0) need a dedicated
   scoping/design session before it's AO-dispatchable, or is there a narrower done-when the operator already has in mind
   that would make it bounded? Recommendation: scoping session first — the current line-253 text names 3+ candidate
   signal sources with no stated priority among them.
3. **E6** — should quickmerge.sh's PM-specific Option-B direct-PR-open step be removed in favor of 100% bot-driven drain
   (matching every other repo), per `ldr_to_main_promote_churn_fix_verification_2026_07_27.md`'s measured churn finding?
   Recommendation: yes (removes a measured, real CI-run churn source with no stated benefit to keeping Option-B), but
   this changes the fleet's core shipping gatekeeper for one specific repo, so it needs explicit sign-off before any
   worker touches `quickmerge.sh` on this basis.

## Codex SSOTs (read before executing any todo)

- `/codex/08-workflows/ci-cd-flow.md` — pipeline / quickmerge / strict-quickmerge / gate set / release + wheel
- `/codex/06-coding-standards/quality-gates.md` — how gates run; never `pytest` directly; ratchet-baseline convention
- `/codex/04-architecture/ci-alerting.md` — `notify-slack.yml` carrier, `dedup_key` + cooldown, recovery-gated
  all-clears
- `/codex/06-coding-standards/ui-testing-layers.md` — why E12/E13 need a `[UI]`-capable role, not `cicd`
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `plans/active/task_template.md` §4 — finalize-plan-coverage rule

## Progress Log

- **2026-07-29** — Drafted by `/ag-closeout-audit ci` (autonomous mode, `ag_closeout_auditor` scheduled worker, slot 7).
  Phase 0: `ci_consolidated_closeout_2026_07_25.md` confirmed archived 2026-07-28 (its own single todo done); covering
  set re-derived as `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (active, 14/30 todos done) + its gated finalize
  (draft). Found + worked around a real bug in `scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py`: its
  `ao`/`ci`/`infra` membership branch derives candidates from the tranche's consolidated-closeout doc's own citations
  (`_closeout_paths()`, globs `plans/active/`), which silently returns zero once that doc is archived — stale relative
  to the skill's own documented 2026-07-27 schema migration (asset_group `ci` is now the primary membership signal for
  this tranche, not the old closeout-citation workaround). Filed
  `archive/issues/generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md`
  and worked around via a direct frontmatter sweep. Found 31 docs with `asset_group` containing `ci` (29 after excluding
  batch1+finalize); cross-referenced batch1's citations (basename AND truncated-prose-paraphrase matching, since batch1
  sometimes elides long filenames with `…`) plus self-dispatch status (`assigned_vm: planning` + `status: active/open`)
  to narrow to 9 genuinely never-touched candidates, PLUS folded in 1 already-known `asset_group: [meta]` doc
  (`mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`, identified via
  `ag_closeout_audit_scope_widening_triage_2026_07_26.md`'s completed corpus-wide meta-sweep — but classified
  `orphaned_partial_coverage`/not-bounded, see E7, not drafted here). Phase 1: all 9 read end-to-end via a `Workflow`
  (one agent per doc) — 7 `orphaned_never_touched`, 2 `orphaned_partial_coverage`. Also re-checked batch1's own
  conflict-gated Deferred items D2-D6 per the iterative-drain methodology: D5 (dirty-deps carve-out) was RULED by the
  operator TODAY (2026-07-29, same day as this audit — a genuine coincidence, not this audit's own doing); D7/D3(1)
  (sentinel ENVIRONMENT binding) and D18 (promotion-lag alert) were already resolved per batch1's own 2026-07-28
  gate-cleanup notes but never extracted into a todo until now; D2, D6, and D3's remaining sub-items remain genuinely
  gated (re-verified against their source docs' current state, unchanged). Phase 3: conflict-check found
  `scripts/quality-gates-base/base-service.sh` claimed by 3 candidates (todo 1, `pm_bats_tests`, the `--durations=25`
  half) and `base-library.sh` by 2 (todo 11, the `--durations=25` other half) — rationed one todo per file. Also caught
  a genuine near-duplicate: `ci_test_content_and_tooling_speed_findings_2026_07_28.md`'s proposed
  `test_sports_catalog_reader_timeout.py` fix is the SAME FILE as the already-self-dispatched
  `mtds_sports_catalog_reader_timeout_test_flaky_under_contention_2026_07_27.md` (`assigned_vm: planning`) — excluded
  from todo 7 to avoid dispatching a competing fix to already-claimed work; noted for that task's own worker instead. 14
  todos drafted, 15 items deferred (E1-E15), 3 escalated to the operator. Nothing shipped, nothing flipped to `active`.

- **2026-07-30 (rulings-closeout pass, still `status: draft` — not flipped active)**: operator asked for every recorded
  ruling across the plans corpus that implies concrete, unshipped work to actually be closed out. This plan is still a
  DRAFT AO-dispatch candidate batch (flipping to `active` remains the operator's own call, untouched here), but several
  of its todos turned out to already be fully shipped by other, more recent sessions whose citations simply predate this
  draft's own 2026-07-29 authoring — re-verified each directly against live code/repo state rather than trusting the
  todo text: **todo 1's part (c)** (`--durations=25`) and the separate **CI-cost-tooling todo** (uv cache + merged
  ruff-ratchet invocation) both landed in `unified-trading-pm@3ed0fc99d` (2026-07-29); **todo 4** (promotion-lag
  PROVENANCE-BLOCKED reclassification) was already implemented, its named 2026-07-17 offenders superseded by the source
  issue doc's own already-`[x]` 2026-07-30 resolution (different, current offenders cleared instead) — the one genuine
  gap (no regression test against a synthetic blocked PR) was closed this session:
  `scripts/cicd/test_promotion_lag_monitor_provenance_blocked.py` (6 tests), shipped `unified-trading-pm@51b93ec0a`;
  **todo 5** (Quickmerge trailer carve-out) was already shipped + archived (`unified-trading-pm@bbe9a9871`, source issue
  `status: resolved`). Flipped all four to `[x]` with the verification evidence inline. **Todo 1's parts (a)/(b)**
  (sentinel ENVIRONMENT-binding + quickmerge/standalone entrypoint alignment) were confirmed still genuinely open (read
  `_qg_content_hash()` and PM's own `quality-gates.sh` directly — neither binds/aligns `ENVIRONMENT` today) but were
  deliberately NOT attempted: this is a real, correctly-scoped gap, but implementing it safely means editing the shared
  `base-service.sh` sentinel-hash function every repo's QG run depends on — too high a blast radius for a solo,
  time-boxed pass without dedicated review, unlike every other bounded single-file fix touched this session. Todos 2, 3,
  6-14 were not re-verified (out of this pass's time budget) and are left exactly as drafted. No status flip attempted;
  this remains an operator-gated draft.

- **2026-07-30 (slot 3, `[INFRA]` dispatch)** — plan activated by the operator earlier the same day
  (`unified-trading-pm@5a6bbefc3`, alongside 8 sibling batches); this session picked up todo 1 as an AO-dispatched task.
  Shipped todo 1's parts (a) and (b) in full — the exact gap the 2026-07-30 rulings-closeout pass above deliberately
  left unclaimed pending a dedicated, reviewed session. See the todo's own inline evidence for the full design (new
  `qg-environment.sh` single source of truth, config-bound `.qg_content_sentinel` + `.qg_last_passed_sha`, 3 regression
  tests, 2 independent live end-to-end verifications) and
  `issues/deployment_flow_doc_stale_pre_ldr_direct_mvp_2026_07_30.md` for a broader, unrelated codex-staleness finding
  surfaced (and correctly NOT absorbed) along the way. Also corrected this plan's own stale draft-status banner and this
  Progress Log's prior "operator-gated draft" framing — the plan has been `status: active` since the operator's same-day
  activation, just never reflected in the body text until now.

- **2026-07-31 (slot 14, `[INFRA]` dispatch)** — picked up todo 3 (env-coupled `ENVIRONMENT`-ambient-default tests in
  `deployment-api`/`strategy-service`). Investigated by reproducing the exact 2026-07-23 mechanism against both repos'
  real `quality-gates.sh`-scoped test suites under `ENVIRONMENT` unset and `ENVIRONMENT=development` — found byte-
  identical pass/skip/xfail counts under both states in both repos (no divergence), then confirmed with a full real
  `bash scripts/quality-gates.sh` run in each (backgrounded per the cicd heartbeat rule) — both green, sentinels
  written. Root cause of why this is now moot: todo 1's already-shipped (a)/(b) fix made a standalone `quality-gates.sh`
  run resolve the SAME `ENVIRONMENT=development` a quickmerge run would on `live-defi-rollout`, closing the exact
  ambient-default divergence this todo worried about. No code change was needed in either repo — the original 2026-07-23
  claim (grep-derived, unverified for these 2 repos unlike MTDS's named/confirmed reproducers) does not reproduce today.
  Flipped todo 3 `[x]` with full evidence inline; also updated the source issue doc
  (`issues/qg_sentinel_environment_blind_2026_07_23.md` item 3) to record the same finding. MTDS's 2 cases remain
  untouched and genuinely gated (E7, unchanged).
