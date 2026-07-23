---
doc_type: plan
title: Fleet Hygiene — cryptography GHSA floor bump + MTDS QG baseline ratchet-down
summary:
  Bump the fleet's cryptography dependency off the GHSA-537c-gmf6-5ccf advisory line and drop the transient
  --ignore-vuln; ratchet MTDS's DTZ + fallback-import QG baselines down now that the underlying fix already landed.
status: complete # (was: active) 2026-07-15 plan-reconcile: all todos [x], evidence spot-checked, no open prose work
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, market-tick-data-service]
scope: [engineer]
tags: [dependency, security, quality-gates, hygiene, fleet-wide]
related: [/plans/active/v2_engine_venue_buildout_2026_06_15.md]
created: 2026-07-13
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-code
last_updated: 2026-06-27
locked_by:
locked_since:
depends_on:
supersedes:
superseded_by:
source: [v2_engine_venue_buildout_2026_06_15.md follow-up 2026-07-13]
sequential: false
---

# Fleet Hygiene — cryptography GHSA bump + MTDS baseline ratchet

> **Split out 2026-07-13** from [`v2_engine_venue_buildout_2026_06_15.md`](v2_engine_venue_buildout_2026_06_15.md)
> Follow-ups section — both items are mechanical, unblocked, and unrelated to the strategy-engine work in the parent
> plan; grouped here as one small hygiene sweep rather than two separate micro-plans.

## Ground truth (2026-07-13 verification — do not re-derive)

- The `GHSA-537c-gmf6-5ccf` ignore for `cryptography` 46.0.7 (statically-linked OpenSSL) is confirmed still present in
  `unified-trading-pm/scripts/quality-gates-base/base-service.sh:1307-1310` and `base-library.sh:946+`, both explicitly
  cross-referencing this plan's parent by name. It is a transient speed>security unblock, not the fix.
- MTDS is confirmed below both `ruff_rule_ratchet_baseline.yaml` (32) and `no_fallback_imports_baseline.yaml` (3) after
  the DTZ noqa fix already shipped — the ratchet-down just hasn't been run.

## Todos

- [x] ✅ [SCRIPT] P2. Bump the `cryptography` dependency floor fleet-wide (every repo declaring it, directly or
      transitively) to a version outside the `GHSA-537c-gmf6-5ccf` line; regenerate `uv.lock` per repo. Repo:
      fleet-wide. — DONE for 16/17 repos, 1 blocked (see below).
  - Bumped the canonical range in `workspace-constraints.toml` (`cryptography>=47.0.0,<50.0.0` — floor off the advisory
    line, ceiling widened to admit what the fleet already naturally resolves to: 47/48/49 seen pre-bump on repos without
    an explicit ceiling). Did NOT use `propagate-canonical-versions.py --apply` for the 13 directly-pinned repos — it
    bulk-realigns EVERY canonical package, not just the one changed (caught it silently downgrading MTDS's fastapi
    ceiling/uvicorn floor); reverted that and hand-patched just the `cryptography` line via a scoped regex across the 13
    files instead.
  - 13 repos with an explicit pin (unified-trading-library, unified-trading-pm, market-tick-data-service,
    unified-trading-api ×2 occurrences, batch-live-reconciliation-service, trading-agent-service, deployment-api,
    ibkr-gateway-infra, system-integration-tests, client-reporting-api, strategy-service,
    market-data-processing-service, execution-service): `pyproject.toml` line updated + `uv.lock` regenerated.
  - 4 purely-transitive repos with no explicit pin, stale locks (deployment-service, fund-administration-service,
    instruments-service, e2e-testing): `uv lock --upgrade-package cryptography` (no pyproject.toml change needed).
  - All 17 repos verified off the vulnerable line (`cryptography` now 47.0.0-49.0.0 everywhere) via a fleet-wide version
    sweep.
  - Two unrelated pre-existing findings hit + resolved in passing: `ibkr-gateway-infra`'s scm-version-gate was RED
    (cloudbuild.yaml missing a git-tag fetch step) — fixed via the existing sanctioned `patch_cloudbuild_fetch_tags.py`
    tool (small/clear/scripted). `fund-administration-service`'s pip-audit was RED on `click 8.3.2` (PYSEC-2026-2132,
    already tracked in `plans/active/issues/fund_administration_service_click_pysec_2026_2132_2026_07_13.md`) — fixed
    via the issue's own documented remedy (`uv lock --upgrade-package click`), bundled into the same `uv.lock` commit.
  - **16/17 repos SHIPPED**: `unified-trading-library@b65cf8d2`, `unified-trading-pm@03a90fb64`,
    `market-data-processing-service@807bc2a`, `unified-trading-api@7e1c506`,
    `batch-live-reconciliation-service@727e676`, `trading-agent-service@4225490`, `deployment-api@20fbd6d`,
    `execution-service@a37bac53`, `ibkr-gateway-infra@7ea590c` (+`d7ef684` scm-version-gate fix),
    `system-integration-tests@02010af`, `client-reporting-api@8e58b92`, `strategy-service@23e250c0`,
    `deployment-service@56c65fb`, `fund-administration-service@018e5a6`, `instruments-service@055ca3cc`,
    `e2e-testing@4b91e1a`.
  - **17/17 SHIPPED** (final): `market-tick-data-service@ee911510` — shipped by **slot-9**, who picked up the
    repo-blocker's green signal once slot-3 independently fixed the pre-existing file-size gate
    (`market-tick-data-service@e284ad63`) that had blocked this repo. My own locally-committed crypto-bump for this repo
    (`1317ba31`) was never pushed and turned out redundant with slot-9's shipped commit — abandoned in favor of theirs
    (verified identical target `cryptography>=47.0.0,<50.0.0` state) rather than duplicate/conflict. Full story in
    `plans/active/issues/mtds_migrate_sports_canonical_v9_filesize_2026_07_13.md`.
  - **Separate P1 safety finding**: an unidentified process force-reset 8 of this slot's worktrees mid-ship, silently
    discarding 6 committed-but-unpushed commits (all recovered via `git cherry-pick` from dangling reflog SHAs, all now
    confirmed pushed). Filed `plans/active/issues/slot6_git_reset_dataloss_2026_07_13.md` (P1) + alerted main/operator —
    contradicts `slot-cron-ff-pull.sh`'s documented never-destructive contract, root cause needs infra investigation I
    don't have session access for.
- [x] ✅ [SCRIPT] P2. Remove the `GHSA-537c-gmf6-5ccf` `--ignore-vuln` from both
      `unified-trading-pm/scripts/quality-gates-base/base-service.sh` and `base-library.sh` once the bump above is
      confirmed green across the fleet — do not remove the ignore before every dependent repo's QG has actually passed
      with the new floor. Repo: unified-trading-pm. — SHIPPED `unified-trading-pm@c5d4a72af` (PR #995, auto-merge).
      Removed the ignore + its explanatory comment from `base-service.sh`'s `QG_PIP_AUDIT_COMMON_IGNORES` list in
      `qg-common.sh` (single control point, item 252) now that all 17/17 repos are confirmed off the vulnerable
      cryptography line. `base-library.sh` never actually carried its own copy of the ignore — it sources
      `QG_PIP_AUDIT_COMMON_IGNORES` from `qg-common.sh` too, so removing it there covers both. Also bundled a small
      unrelated blocker-fix in the same shipping session (repo: unified-trading-pm@`5e39e6509`-family, folded into final
      SHA): extended `PER_REPO_EXTERNAL_EXCEPTIONS` for `unified-trading-api`'s `fastapi<0.138.0` (same
      already-established safe pattern as the other 7 exempted repos — verified locked resolution 0.135.1, below the
      confirmed-broken 0.137.x threshold) — this was independently blocking STAGE 1.5 dependency-alignment for every PM
      push and had to clear before this todo's own shipment could land. Also fixed (in passing, same session, own
      commits): a stale `canonical-dependency-manifest.json` (cryptography entry never regenerated after the fleet bump
      — superseded by another slot's identical fix during rebase, no separate SHA) and a click-floor canonical-lag for
      `features-service` (superseded by another slot's identical fix `10943bfd` during rebase). Shipping hit an extreme
      SHA-drift race — `unified-trading-pm`'s fleet-wide commit rate briefly outpaced a full QG run's duration,
      requiring ~16 QG-then-quickmerge cycles before landing cleanly; content was verified identical across every retry,
      never a real conflict. execution-service's own pillow floor-lag fix (a 3rd pre-existing STAGE 1.5 blocker found in
      passing) shipped separately: `execution-service@f481ba08`. strategy-service's equivalent pillow fix was
      independently shipped by another slot (`10943bfd`) — my local commit was redundant and correctly dropped during
      rebase.
- [x] ✅ [SCRIPT] P3. Ratchet DOWN `ruff_rule_ratchet_baseline.yaml` and `no_fallback_imports_baseline.yaml` for
      market-tick-data-service by re-running `--update-baseline` — baselines only go DOWN, never up, per the
      coding-standards HARD RULE. Repo: unified-trading-pm. — SHIPPED `unified-trading-pm@aa0428ea`. Ran both checkers
      scoped to `market-tick-data-service` first (dry-run, no `--update-baseline`) to see exactly what changed:
      `check_ruff_rule_ratchet.py` reported `dtz: 30 < baseline 32 — ratchet DOWN` (`tid251` unchanged at 38, already ==
      baseline); `check_no_fallback_imports.py` reported `count: 2 (== baseline)` — no ratchet room there, contrary to
      the plan's stated "(3)" (already correct at the current baseline, nothing to update). Ran
      `check_ruff_rule_ratchet.py --scope market-tick-data-service --update-baseline`, which dropped `dtz` 32→30 in
      `ruff_rule_ratchet_baseline.yaml` (`tid251` untouched, still 38 — no drift there). Did NOT touch
      `no_fallback_imports_baseline.yaml` since its live count already matched. Re-ran both checkers post-update to
      confirm `== baseline` on all four numbers. Full `quality-gates.sh` green (59s).

## Progress Log

(loop handoff lands here)
