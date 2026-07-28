---
doc_type: issue
title:
  Fleet-wide test-suite content/tooling-speed audit (24 findings) — orphaned tests, missing caching, redundant scans,
  real sleep()-based waste — none yet converted from chat findings into tracked work
summary: >-
  Parallel research workflow (9 of 12 planned agents completed; 3 hit a session usage cap covering the PM cost-breakdown
  angle, tracked separately) audited ~24 repos' test suites and shared CI tooling for speed opportunities distinct from
  the runner/infra-migration work covered by github_actions_operator_gated_followups_2026_07_17.md — this doc covers
  test CONTENT and TOOLING, not where/how often CI runs. Findings were reported to the operator in chat only and never
  landed as tracked todos until this doc (workspace hard rule: every discovery becomes a `- [ ]`, never prose-only chat
  output). Fleet-wide-leverage items (shared quality-gates-base scripts, consumed by ~22 repos) are prioritized first
  since a single fix cascades; per-repo findings are lower priority. Total identified: ~45s of trivially-fixable real
  sleep() waste per full-suite run, ~40 files/10k+ lines of confirmed-dead test code in execution-service, and one
  high-confidence fleet-wide Playwright misconfiguration (a debug/human project running in CI).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    deployment-ui,
    unified-trading-system-ui,
    execution-service,
    unified-trading-library,
    market-tick-data-service,
    features-service,
    deployment-api,
    instruments-service,
    greeks-service,
  ]
scope: [engineer]
tags: [ci-cd, test-speed, tooling, orphaned-code, caching]
related: [/plans/active/github_actions_operator_gated_followups_2026_07_17.md]
created: "2026-07-28"
priority: P2
parent_epic: deployment_and_user_management_master
source:
  "interactive session, 2026-07-28 — Workflow tool fan-out (9/12 agents completed), findings never previously tracked"
execution_scope: local-only
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
---

# Fleet-wide test-suite content/tooling-speed findings — untracked until now

Full raw findings (JSON) are in the session transcript only, not promoted anywhere durable — this doc captures every
finding as an actionable todo instead of leaving them as chat prose per the workspace hard rule. Todos are grouped by
leverage (fleet-wide-template fixes first — one change, ~22 repos benefit) then by repo.

## Fleet-wide-leverage todos (shared `quality-gates-base`, `python-quality-gates-v2.yml`, or template-driven repos)

- [ ] [SCRIPT] P2. Add `--durations=25` to the shared pytest invocation in
      `unified-trading-pm/scripts/quality-gates-base/base-service.sh:737` and `base-library.sh:367` (the `PARGS`
      string). Currently zero per-test timing visibility exists anywhere in the fleet's CI — engineers can see a repo's
      "tests" phase took 350-460s but not which test(s) drive it. Near-zero cost to add; unblocks every other test-speed
      fix below and any future one. Verify on 1 consumer repo before considering fleet-applied (rule 11).
- [ ] [SCRIPT] P3. Add an `actions/cache@v4` step for the `uv` package cache (`~/.cache/uv` or the custom `UV_CACHE_DIR`
      set in base-service.sh/base-library.sh) in `python-quality-gates-v2.yml` — currently `.venv` is rebuilt from
      scratch on every single run fleet-wide (confirmed: `actions/checkout@v4`'s default `clean: true` wipes any
      leftover `.venv` before `uv sync` runs, even on persistent self-hosted runners). Biggest payoff on any repo NOT
      yet on `self-hosted-qg-repos.txt` (still GitHub-hosted, no incidental host-persistence benefit). Size the actual
      savings first (compare a cold vs warm `uv sync` timing) before committing to the cache-key design — self-hosted
      host persistence may already be absorbing some of this for free.
- [ ] [SCRIPT] P3. `unified-trading-pm/scripts/quality_gates/check_ruff_rule_ratchet.py` (`run_ruff_count()`, lines
      ~208-227) runs a separate full-source-tree `ruff check --no-cache` invocation PER RULE GROUP (currently 2: dtz,
      tid251) in STEP 5.95, on top of the primary `[2/6] LINT` pass that already runs `ruff check` once with caching.
      Low absolute cost (ruff is fast) but a clean, mechanical fix: merge the rule groups into one `--select` invocation
      sharing one `--config`, and drop `--no-cache` unless there's a real correctness reason for it (check the script's
      own `--isolated` comment first — that flag is load-bearing, `--no-cache` may not be).

## `unified-trading-system-ui` (public repo — no GH billing impact, but real wall-clock/orchestrator-VM-contention impact)

- [ ] [UI] P2. **Highest-confidence finding in the whole audit.** Playwright E2E (`package.json:40` → `pnpm test:e2e` →
      `playwright test` with no `--project` filter) runs ALL THREE configured projects every CI run
      (`playwright.config.ts:42-84`) — including a `widgets` project and a THIRD project configured with
      `headless: false, slowMo: 700` (a human-debug project that should never run in CI). Scope the CI invocation to
      `--project=chromium` (the codex-sanctioned `pw:L2` command already does this) — roughly a 2-3x E2E-time cut.
- [ ] [UI] P3. No `actions/cache` for the Playwright browser-binary directory in the e2e job
      (`.github/workflows/ci.yml:66-67`, `pnpm exec playwright install --with-deps chromium` runs unconditionally).
      Currently low-impact since this repo's real CI is already self-hosted (persistent host likely caches browsers
      incidentally) — but add explicitly rather than relying on that, since it'd become a real multi-minute cost if ever
      moved to an ephemeral runner.
- [ ] [UI] P3. `eslint .` (`package.json:26`) scans ~2080 files vs. ~1587 in the actual `app+components+lib+hook` tree —
      `eslint.config.mjs`'s ignore list excludes `_reference/**` etc. but NOT `archive/**` (25 files, 652KB, name
      signals dead code) or `tooling-templates/**`. Add both to the ignore list; also add `--cache` to the lint script.

## `deployment-ui`

- [ ] [UI] P3. `vitest.config.ts:24` uses `environment: "jsdom"` instead of `happy-dom` — the repo's own comments
      (`scripts/quality-gates.sh:20-26`) already document raising `STEP_TIMEOUT_TEST` 120s→300s specifically citing "75+
      test files × jsdom env overhead," and `vitest.config.ts:51-60` separately raised test/hook timeouts citing CPU
      contention from jsdom + coverage + the `forks` pool. `happy-dom` is commonly 2-3x faster for DOM-heavy component
      tests. With 782 tests already near the 300s budget, this is a credible multi-minute win that would let the timeout
      budgets come back down instead of needing to ratchet up further.
- [ ] [UI] P3. Package manager is `npm` (`package-lock.json`) while the sibling UI repo already standardized on `pnpm`.
      Small absolute win (15 deps + 23 devDeps) but free consistency with the fleet pattern and a real per-run speedup
      on the one UI repo whose CI genuinely runs on ephemeral `ubuntu-latest`.

## Real `sleep()`-based test waste (all trivially fixable by mocking the clock instead — zero behavior risk)

- [ ] [SCRIPT] P2. `market-tick-data-service/tests/unit/engine/test_sports_catalog_reader_timeout.py:88` — imports the
      REAL production constant `_BLOB_TIMEOUT_SECS` (=30) and does a real `time.sleep(35)` inside a background thread.
      **The single largest item found: ~30s of unnecessary real wall time on every run of this one test.** Fix:
      monkeypatch `_BLOB_TIMEOUT_SECS` down to e.g. 0.05s for the test.
- [ ] [SCRIPT] P3. `unified-trading-library`: 4 tests in `tests/unit/test_manifest_freshness.py` each `sleep(1.1)`
      (~4.4s total, lines 324/468/515/570); `tests/unit/recovery/test_agent_action.py` sleeps 1.5s
      (`test_loop_detector_window_expires`); `tests/events/test_pipeline_heartbeat_timer.py` sums to ~5.75s across 7
      tests (one single test alone is 3.5s, line 180). All read the clock via a directly-patchable
      `time.monotonic()`/`import time` call — no production refactor needed, just `patch(...time.monotonic)` in each
      test. Combined ~11.65s/run in this one repo.
- [ ] [SCRIPT] P3. `features-service/tests/sports/unit/test_feature_cache.py` — 2 tests `sleep(1.1)` each (~2.2s total)
      waiting out a 1s TTL on `LiveFeatureCache`; this directory IS part of the QG-gated pytest run (dynamic glob picks
      up every `tests/*/unit/` dir), so this runs on every CI invocation.
- [ ] [SCRIPT] P3 (batch, low individual value — do together or skip). `deployment-api` (~0.5s across 2 files,
      `test_data_status_cache.py:89,276` and `test_route_deployments_inventory.py:2069` — the latter is a legitimate
      concurrency-proof pattern, probably not worth changing), `instruments-service`
      (`tests/unit/test_base_adapter_cache.py:83`, ~20ms), `greeks-service`
      (`tests/unit/inputs/test_instrument_reader.py:100`, ~10ms). Negligible individually; noted for completeness since
      they're the literal anti-pattern this todo group targets.

## Orphaned/dead test code (not a current CI-speed cost — these aren't gated — but real maintenance debt)

- [ ] [SCRIPT] P3. `execution-service`: ~40 files / ~10,082 lines across `tests/live/`, `tests/context7/`,
      `tests/validation/`, `tests/scripts/` import a pre-refactor module path (`execution_service.live.*` —
      oms/orchestrator/positions/risk/router/trading_node/factory/order_converter/config/persistence.*,
      `execution_service.venues.cefi`, `execution_service.catalog_manager`) that no longer exists. Confirmed not
      currently collected/gated (0 CI-minutes cost today) — but 10k+ lines of confirmed-dead code is real debt and a
      landmine for any future attempt to broaden test collection scope. Verify still-dead (grep for the import paths
      resolving to nothing) before deleting, since this audit is now hours old.
- [ ] [SCRIPT] P3. `unified-trading-library/tests/config_interface/unit/test_persistence.py:284` —
      `TestConfigReloaderReplayAt` imports `ConfigReloader` from `unified_trading_library.config_interface`, a path that
      no longer exports it (moved to top-level `unified_trading_library.ConfigReloader`, already correctly used
      elsewhere). Already `@pytest.mark.skip`-marked so zero current cost — trivial dead-code cleanup only.
- [ ] [SCRIPT] P3. `e2e-testing/scripts/{tradfi,cefi,sports,prediction}/run-full-pipeline.sh` — `SERVICES` arrays still
      list pre-merge repo/module name pairs for the archived `features-*-service` split repos (e.g.
      `"features-sports-service:features_sports_service:..."`). Not wired into CI (zero test-time cost) — a
      correctness/dead-reference cleanup in operator-run pipeline scripts, not a speed item.

## What did NOT surface a finding (say so explicitly — audited ~22 repos total for orphaned tests, only 2 hit)

Clean, per the audit's cluster reports: `agent-orchestrator`, `alerting-service`, `batch-live-reconciliation-service`,
`client-reporting-api`, `deployment-api` (orphaned-test angle only — see sleep() finding above), `deployment-service`,
`e2e-testing` (orphaned-test angle only — see dead-reference finding above), `ml-service`, `strategy-service`,
`system-integration-tests`, `trading-agent-service`, `unified-api-contracts`, `unified-trading-api`,
`fund-administration-service`, `ibkr-gateway-infra`, `market-data-processing-service`. The fleet's test suites are
meaningfully cleaner than the audit's working hypothesis assumed going in.

## Not covered by this pass (tracked so it isn't silently dropped)

- [ ] [REVIEW] P3. The PM cost-breakdown angle of the original audit (why `unified-trading-pm` specifically is 41% of
      measured fleet spend) hit a session usage cap mid-workflow. **Partially superseded**: the interactive session that
      followed did this manually via direct `gh api` calls (not the stalled workflow) and found the real answer — see
      `github_actions_operator_gated_followups_2026_07_17.md`'s 2026-07-28 evening Progress Log entry
      (`ci-health`/`branch-health` job-body slowness, not cron frequency). This todo is really just "resume the stalled
      3-agent workflow if a fuller per-workflow breakdown is ever wanted" — low priority, the practical question is
      already answered.
